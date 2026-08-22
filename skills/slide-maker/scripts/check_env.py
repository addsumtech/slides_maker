#!/usr/bin/env python3
"""Preflight: verify the slide-maker toolchain. Run once on a new machine:

    python3 check_env.py           # mac / Linux / WSL — and anywhere with a python3 on PATH
    # python3-sweep-exempt: native Windows ships the `python` launcher and often no `python3`.
    python check_env.py            # native Windows (PowerShell / cmd) ONLY
    bash scripts/check_env.sh      # mac / Linux (delegates here)

Reports what's installed and the exact command to fix anything missing.
Cross-platform: macOS, Linux, WSL, and native Windows (PowerShell / cmd).
"""
import os
import sys
import tempfile

# Reuse the one LibreOffice finder so check + render agree on what counts as "found".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_deck import find_soffice  # noqa: E402

# Copy-pasteable pip commands for THIS interpreter (handles python vs python3 vs py).
PIP = '"{}" -m pip install'.format(sys.executable)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = os.path.join(ROOT, "requirements.txt")
PIP_REQ = '{} -r "{}"'.format(PIP, REQ)


def ensure_mpl_config_dir():
    """Avoid noisy matplotlib warnings when the home cache dir is not writable."""
    if os.environ.get("MPLCONFIGDIR"):
        return
    default = os.path.join(os.path.expanduser("~"), ".matplotlib")
    if os.path.isdir(default) and os.access(default, os.W_OK):
        return
    path = os.path.join(tempfile.gettempdir(), "slide-maker-matplotlib")
    os.makedirs(path, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = path


# The pip deps the build path IMPORTS — every script fails without these. Kept as (import-name,
# pip-name) because the two differ (fitz→pymupdf, PIL→Pillow). This is the manifest `--ensure`
# installs; the optional/system deps below it reports but never auto-installs.
REQUIRED_PIP = [
    ("pptx", "python-pptx"),
    ("fitz", "pymupdf"),
    ("PIL", "Pillow"),
    ("matplotlib", "matplotlib"),
    ("numpy", "numpy"),
]


def _missing_required():
    miss = []
    for mod, pkg in REQUIRED_PIP:
        try:
            if mod == "matplotlib":
                ensure_mpl_config_dir()
            __import__(mod)
        except ImportError:
            miss.append(pkg)
    return miss


def _find_rasterizer():
    """The SVG rasterizer icons.py will actually use: 'cairosvg' | 'rsvg-convert' |
    'headless Chrome/Edge' | None. Resolved the way icons.py resolves it (a check that answers
    differently from the code under test is worse than no check). Shared by main() and ensure()
    so the human report and the Step-0 preflight never disagree about whether icons can render."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from icons import _cairosvg
        if _cairosvg() is not None:
            return "cairosvg"
    except Exception:
        pass
    import shutil as _sh
    if _sh.which("rsvg-convert"):
        return "rsvg-convert"
    try:
        from icons import _find_chrome
        if _find_chrome():
            return "headless Chrome/Edge"
    except Exception:
        pass
    return None


def ensure():
    """Step-0 preflight: auto-install missing REQUIRED pip deps, report system deps that cannot be.

    WHY it runs at Step 0, right after the version check. On a fresh machine a missing library does
    not surface until the step that imports it — and the most expensive one is the RENDER (Step 5),
    the gate the critic loop waits on: a missing LibreOffice or PyMuPDF there costs a diagnosis
    round-trip and a re-run, exactly when tokens are most expensive. Detecting it BEFORE the
    interview turns a mid-critic failure into one fast install up front. Silent-and-instant when the
    toolchain is warm (the common case), so it never taxes a repeat run. Opt out with
    SLIDE_MAKER_NO_ENV_CHECK=1.

    It auto-installs ONLY the pip deps, and ONLY into THIS interpreter (sys.executable). System
    installs — LibreOffice, an SVG rasterizer — are heavier, need sudo / a package manager / a GUI
    download, and are the user's call: it prints the one command and returns a distinct code.

    Exit contract for the caller (SKILL.md Step 0.0):
      0  everything required present (or just installed) AND LibreOffice found — proceed silently
      3  pip deps ok, LibreOffice MISSING — render will fail; surface the one install command
      1  a required pip dep could not be installed — surface the manual command
    """
    import subprocess
    if os.environ.get("SLIDE_MAKER_NO_ENV_CHECK"):
        return 0
    miss = _missing_required()
    installed = []
    if miss:
        # `pip install`, then `--user` on an externally-managed env (PEP 668). Never add
        # --break-system-packages automatically — overriding the OS package manager is the user's
        # decision, so on a hard block we fall through to printing the manual command.
        for extra in ([], ["--user"]):
            try:
                r = subprocess.run([sys.executable, "-m", "pip", "install", *extra, *miss],
                                   capture_output=True, text=True, timeout=600)
            except Exception:                                    # noqa: BLE001
                continue
            if r.returncode == 0:
                installed = list(miss)
                break
        still = _missing_required()
        if still:
            print("[env] could not auto-install {}. Install by hand, then re-run:\n"
                  "        {} {}".format(", ".join(still), PIP, " ".join(still)))
            return 1
    if installed:
        print("[env] installed missing python deps: {} (into {})".format(
            ", ".join(installed), sys.executable))
    if not _find_rasterizer():
        # icons are a DEFAULT on categorical decks, but the rasterizer is a system-lib dep
        # (cairosvg installs cleanly yet dies without libcairo — a blind pip is a false 'fixed'),
        # so it is REPORTED here like LibreOffice, not auto-installed. Surfacing it at Step 0 stops
        # a fresh machine from passing --ensure and then failing at the first icon.
        print("[env] no SVG rasterizer — deckkit ICONS (a default on categorical decks) will fail. "
              "Install one once:  macOS: brew install librsvg · Ubuntu: sudo apt install "
              "librsvg2-bin · any OS: pip install cairosvg (needs a working libcairo) · or a "
              "headless Chrome/Edge.")
    if not find_soffice():
        print("[env] LibreOffice not found — the PNG render loop (Step 5, before the critic) needs "
              "it. Ask the user to install it once:\n"
              "        macOS: brew install --cask libreoffice · Ubuntu: sudo apt install "
              "libreoffice · Windows: winget install TheDocumentFoundation.LibreOffice")
        return 3
    return 0


def check_module(mod, label, fix_pkg, optional=False, note=""):
    try:
        if mod == "matplotlib":
            ensure_mpl_config_dir()
        m = __import__(mod)
        ver = getattr(m, "__version__", "")
        print("  [ok]  {} {}".format(label, ver).rstrip())
    except ImportError:
        tag = "[optional]" if optional else "[MISSING] "
        line = "  {} {:<12} ->  {} {}".format(tag, label, PIP, fix_pkg)
        if note:
            line += "   ({})".format(note)
        print(line)


def check_save_locations():
    """Can we actually WRITE a deck where the user will want it?

    macOS TCC grants a process access per-directory, and it can revoke mid-session: ~/Downloads
    stays listable while open() raises PermissionError. Measured on one build, that cost six
    round-trips of diagnosis in the middle of authoring — the deck was written, the save failed,
    and the failure looked like a bug in the build rather than a sandbox boundary.

    So probe by actually creating and deleting a file, not by reading permission bits: os.access()
    consults the mode bits, which is exactly the thing TCC does not express.
    """
    import tempfile
    home = os.path.expanduser("~")
    cands = [("~/Downloads", os.path.join(home, "Downloads")),
             ("~/Desktop", os.path.join(home, "Desktop")),
             ("~/Documents", os.path.join(home, "Documents")),
             ("cwd", os.getcwd())]
    usable = []
    seen = set()
    for label, d in cands:
        if not os.path.isdir(d):
            continue
        try:                              # cwd is frequently one of the named dirs; listing the same
            key = os.path.realpath(d)     # place twice reads as two options when there is one
        except OSError:
            key = d
        if key in seen:
            continue
        seen.add(key)
        probe = None
        try:
            fd, probe = tempfile.mkstemp(prefix=".slide-maker-probe-", dir=d)
            os.close(fd)
            usable.append(label)          # the CREATE is the test; cleanup is not part of the verdict
        except Exception as e:
            print("  [blocked] {:<12} not writable ({}) — do not offer it as a save location"
                  .format(label, type(e).__name__))
        finally:
            # best-effort, and deliberately outside the verdict: a cleanup failure would otherwise
            # report a perfectly writable directory as blocked AND strand the probe file there.
            if probe:
                try:
                    os.unlink(probe)
                except OSError:
                    pass
    if usable:
        print("  [ok]  writable save locations: {}".format(", ".join(usable)))
    else:
        print("  [MISSING]  no writable save location among {} — ask the user for a path you CAN "
              "write, before building".format(", ".join(l for l, _ in cands)))


def check_registry():
    """Report the resolved template/taste registry root.

    Never a failure — an empty registry is the correct state for a new user, and inventing one
    would break `user-taste.md`'s empty-file rule. It is here to be SEEN: the root used to be
    prose naming two hosts, so on any third runtime it resolved to nothing and Q1(a) silently
    lost the saved-templates option with no gate anywhere reporting it. One printed line at
    Step 0 is the cheapest place for that to stop being invisible.
    """
    try:
        import registry  # same directory as this script
    except Exception as exc:                                    # never fail the env check on it
        print(f"  [--]  template registry: unresolved ({exc.__class__.__name__})")
        return
    name, root = registry.root_for_write()
    n = len(registry.list_templates())
    taste = "taste.md" if registry.taste_file() else "no taste.md yet"
    state = "ok" if root.is_dir() else "--"
    print(f"  [{state}]  template registry ({name}): {root} — {n} template(s), {taste}")


def main():
    print("slide-maker environment check:")
    print("  install python deps: {}".format(PIP_REQ))
    check_module("pptx", "python-pptx", "python-pptx")
    check_module("fitz", "pymupdf", "pymupdf")
    check_module("PIL", "Pillow", "Pillow")
    check_module("matplotlib", "matplotlib", "matplotlib",
                 optional=True, note="only for equation_png")

    # SVG rasterizer — icons.py needs ONE of: cairosvg (working libcairo), rsvg-convert, or a
    # Chromium-family browser. cairosvg importing cleanly is NOT enough: it dies at call time
    # when libcairo is missing, so probe the native lib too.
    # Resolve it the way icons.py does (via the shared _find_rasterizer), not a bare import:
    # icons._cairosvg() also teaches cairocffi where a Homebrew/MacPorts libcairo lives, and a
    # check that answers differently from the code under test is worse than no check.
    rasterizer = _find_rasterizer()
    if rasterizer == "headless Chrome/Edge":
        # Green, but it is the SLOWEST backend by two orders of magnitude — measured on a real
        # 5-icon run: 5.05s per icon through Chrome vs 0.016s through cairosvg, identical output
        # (ink coverage within 0.0002). A deck with a dozen icons pays a full minute for nothing,
        # and the old check reported this as plain [ok] with no way to know.
        print("  [ok]  SVG rasterizer (headless Chrome/Edge)  ->  WORKS, but ~300x slower than "
              "cairosvg (~5s vs ~0.02s per icon). For faster builds: "
              "macOS: brew install cairo | Ubuntu: sudo apt install libcairo2 | "
              "then pip install cairosvg")
    elif rasterizer:
        print("  [ok]  SVG rasterizer ({})".format(rasterizer))
    else:
        print("  [MISSING]  SVG rasterizer (icons will FAIL)  ->  "
              "macOS: brew install librsvg | "
              "Ubuntu: sudo apt install librsvg2-bin | "
              "Windows: install Google Chrome or Edge (used headless) | "
              "any OS: pip install cairosvg (needs a working libcairo)")
    try:
        import icons as _icons
        print("  [--]  icon cache: {}{}".format(
            _icons._CACHE,
            "  (SLIDE_MAKER_CACHE override)" if os.environ.get("SLIDE_MAKER_CACHE") else ""))
    except Exception:
        pass

    soffice = find_soffice()
    if soffice:
        print("  [ok]  LibreOffice ({})".format(soffice))
    else:
        print("  [MISSING]  LibreOffice  ->  "
              "macOS: brew install --cask libreoffice | "
              "Ubuntu: sudo apt install libreoffice | "
              "Windows: winget install TheDocumentFoundation.LibreOffice | "
              "else https://www.libreoffice.org/download")

    check_save_locations()
    check_registry()


if __name__ == "__main__":
    # `--ensure` is the Step-0 auto-fix path (install missing pip deps, report system deps + exit
    # code); no flag is the full human-readable report. Kept as one script so the check and the
    # ensure never drift about what "required" means.
    if "--ensure" in sys.argv[1:]:
        raise SystemExit(ensure())
    main()
