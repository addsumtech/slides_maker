#!/usr/bin/env python3
"""Preflight: verify the slide-maker toolchain. Run once on a new machine:

    python check_env.py            # Windows / anywhere
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
    for label, d in cands:
        if not os.path.isdir(d):
            continue
        try:
            fd, probe = tempfile.mkstemp(prefix=".slide-maker-probe-", dir=d)
            os.close(fd)
            os.unlink(probe)
            usable.append(label)
        except Exception as e:
            print("  [blocked] {:<12} not writable ({}) — do not offer it as a save location"
                  .format(label, type(e).__name__))
    if usable:
        print("  [ok]  writable save locations: {}".format(", ".join(usable)))
    else:
        print("  [MISSING]  no writable save location among {} — ask the user for a path you CAN "
              "write, before building".format(", ".join(l for l, _ in cands)))


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
    rasterizer = None
    try:
        import cairosvg  # noqa: F401
        rasterizer = "cairosvg"
    except Exception:
        pass
    if not rasterizer:
        import shutil as _sh
        if _sh.which("rsvg-convert"):
            rasterizer = "rsvg-convert"
    if not rasterizer:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            from icons import _find_chrome
            if _find_chrome():
                rasterizer = "headless Chrome/Edge"
        except Exception:
            pass
    if rasterizer:
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


if __name__ == "__main__":
    main()
