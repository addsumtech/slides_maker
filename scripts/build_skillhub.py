#!/usr/bin/env python3
"""build_skillhub — build the SkillHub upload package of skills/slide-maker, and refuse a bad one.

SkillHub takes at most 200 files per skill and no image files. The repo's skill folder holds ~445
(bundled sample images, the test suite, evals, CI-only checks), so the package is a TRIMMED copy, and
trimming by hand drifted: the 6.0.1 package was 202 files and the recipe lived in a memory note. This
script is the recipe:

  1. `git archive <ref> skills/slide-maker` — committed files only, never a stray local file;
  2. drop what a user's agent never runs while building a deck: assets/ (images — SkillHub refuses
     them; every path that reads them degrades), tests/, evals/, LICENSE, the lossless allowlist, the
     CI-only checks, and the maintainer-only tools and docs (adding a NEW visual language, exporting
     the site's library, installing from a checkout, the maintenance boundaries);
  3. annotate every `backticked` mention of a dropped file in the package's .md files as living in the
     source repository, so no instruction points at a file that is not there;
  4. VERIFY: no image files; at most --limit files; every scripts/ module imports in the package exactly
     when it imports in the full tree (a module that only fails here lost something it needs);
  5. write <out>/slide-maker-<VERSION>-skillhub.zip and the unzipped folder beside it — named
     <VERSION>+<commit> unless <ref> is that release's tag, and never over an existing file
     without --force.

    python3 scripts/build_skillhub.py                     # HEAD → ~/Downloads
    python3 scripts/build_skillhub.py --ref v6.1.0 --out ~/Desktop
    python3 scripts/build_skillhub.py --selftest          # build into a temp dir and check; CI runs this

Exit 0 built (or selftest passed) · 1 refused (over the limit, an image, a broken import) · 2 bad input.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_REL = "skills/slide-maker"
SOURCE_URL = "https://github.com/addsumtech/slides_maker"
LIMIT = 200

DROP_DIRS = ("assets", "tests", "evals")
DROP_FILES = ("LICENSE", ".skill-lossless-allow.json")
# CI / maintainer checks: run against the repository, never by an agent building a deck.
CI_ONLY = ("check_component_theme", "check_design_contracts", "check_gate_parity", "check_inventory",
           "check_reason_width", "check_tests_wired", "check_param_reach", "check_reference_code",
           "check_skill_lossless", "smoke_directions", "run_eval", "roundtrip_report")
# Maintainer tools: adding a NEW visual language, exporting the site library, installing from a checkout.
# None is imported by the deck-building path (each is named only in strings, comments and docs).
MAINTAINER = ("new_visual_language", "check_vl_contract", "vl_conformance", "vl_library_export",
              "install_skill")
MAINTAINER_DOCS = ("maintenance-boundaries.md", "visual-language-authoring.md")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".ico", ".svg"}
NOTE = " (in the source repository, {}, not in this package)".format(SOURCE_URL)


def _archive(ref: str, dest: Path) -> Path:
    try:
        blob = subprocess.run(["git", "-C", str(REPO), "archive", ref, SKILL_REL],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError as exc:
        raise SystemExit("git archive {} failed: {}".format(ref, exc.stderr.decode(errors="replace").strip()))
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        if hasattr(tarfile, "data_filter"):                           # 3.12+: refuse odd members
            tar.extractall(dest, filter="data")
        else:                                                           # 3.9–3.11: our own git archive
            tar.extractall(dest)                                        # noqa: S202
    return dest / SKILL_REL


def dropped(skill: Path) -> list[str]:
    """Paths (relative to the skill folder) the package leaves out."""
    out = []
    for d in DROP_DIRS:
        if (skill / d).is_dir():
            out.extend(str(p.relative_to(skill)) for p in sorted((skill / d).rglob("*")) if p.is_file())
    for f in DROP_FILES:
        if (skill / f).is_file():
            out.append(f)
    for n in CI_ONLY + MAINTAINER:
        if (skill / "scripts" / (n + ".py")).is_file():
            out.append("scripts/{}.py".format(n))
    for n in MAINTAINER_DOCS:
        if (skill / "references" / n).is_file():
            out.append("references/" + n)
    return out


def trim(skill: Path) -> list[str]:
    gone = dropped(skill)
    for rel in gone:
        (skill / rel).unlink()
    for d in DROP_DIRS:
        shutil.rmtree(skill / d, ignore_errors=True)
    for junk in list(skill.rglob("__pycache__")) + list(skill.rglob(".DS_Store")):
        shutil.rmtree(junk, ignore_errors=True) if junk.is_dir() else junk.unlink()
    return gone


_MARKED = ("scripts/", "references/", "evals/", "tests/")       # dropped files a doc may point at


def annotate(skill: Path, gone: list[str]) -> int:
    """Mark every `backticked` mention of a dropped script/doc as living in the source repository."""
    names = sorted({Path(g).name for g in gone if g.startswith(_MARKED)}, key=len, reverse=True)
    if not names:
        return 0
    # a backticked span may wrap onto the next line (`scripts/run_eval.py --score <deck-dir>\n--eval <id>`)
    alt = "|".join(re.escape(n) for n in names)
    rx = re.compile(r"`[^`]{0,240}?(?<![\w-])(?:" + alt + r")(?![\w.-])[^`]{0,240}?`")
    count = 0
    for md in sorted(skill.rglob("*.md")):
        text = md.read_text(encoding="utf-8")

        def _mark(m):
            nonlocal count
            count += 1
            return m.group(0) + NOTE
        new = rx.sub(lambda m: m.group(0) if text[m.end():m.end() + len(NOTE)] == NOTE else _mark(m), text)
        if new != text:
            md.write_text(new, encoding="utf-8")
    return count


def _env() -> dict[str, str]:
    return dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                SLIDE_MAKER_REGISTRY=tempfile.mkdtemp(prefix="skillhub-reg-"),
                SLIDE_MAKER_TASTE_LEDGER=os.path.join(tempfile.mkdtemp(), "ledger.json"))


def _imports(scripts: Path, mods: list[str] | None = None) -> dict[str, str | None]:
    """{module: None if it imports, else "<Exception>: <message>"} — all in ONE process (fast)."""
    code = ("import importlib, json, sys\nres = {}\nfor m in sys.argv[1:]:\n"
            "    try:\n        importlib.import_module(m); res[m] = None\n"
            "    except BaseException as e:\n        res[m] = '%s: %s' % (type(e).__name__, str(e)[:200])\n"
            "print(json.dumps(res))")
    mods = mods or sorted(p.stem for p in scripts.glob("*.py") if p.stem != "__init__")
    r = subprocess.run([sys.executable, "-c", code] + mods, cwd=str(scripts), capture_output=True, text=True,
                       env=_env(), timeout=900)
    import json
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise SystemExit("could not run the import check in {}:\n{}".format(scripts, r.stderr[-800:]))


def _import_alone(scripts: Path, mod: str) -> str | None:
    """The same import in a FRESH process: an in-process failure can come from a module imported before it
    (a CI run flagged `anim`, which imports nothing but python-pptx)."""
    return _imports(scripts, [mod])[mod]


def verify(pkg: Path, full: Path, limit: int) -> list[str]:
    problems = []
    files = [p for p in pkg.rglob("*") if p.is_file()]
    if len(files) > limit:
        problems.append("{} files — over SkillHub's limit of {}. Drop more maintainer-only files here, or "
                        "merge one language's spec + painter (see the package recipe).".format(len(files), limit))
    imgs = [str(p.relative_to(pkg)) for p in files if p.suffix.lower() in IMAGE_EXT]
    if imgs:
        problems.append("image files in the package (SkillHub refuses them): " + ", ".join(imgs[:8]))
    have, base = _imports(pkg / "scripts"), _imports(full / "scripts")
    suspects = sorted(m for m, err in have.items() if err and base.get(m) is None)
    broke = []
    for m in suspects:                       # confirm each one alone, in both trees, before refusing
        err = _import_alone(pkg / "scripts", m)
        if err and _import_alone(full / "scripts", m) is None:
            broke.append("{} ({})".format(m, err))
        else:
            print("note: {} failed only when imported after the others in one process ({}) — not a "
                  "missing file; it imports alone".format(m, have[m]))
    if broke:
        problems.append("modules that import in the full tree but NOT in the package (they need a dropped "
                        "file): " + "; ".join(broke))
    left = []
    for md in pkg.rglob("*.md"):
        for n in [Path(g).name for g in dropped(full) if g.startswith(_MARKED)]:
            for m in re.finditer(re.escape(n), md.read_text(encoding="utf-8")):
                tail = md.read_text(encoding="utf-8")[m.end():m.end() + 200]
                if NOTE.strip() not in tail:
                    left.append("{}: {}".format(md.relative_to(pkg), n))
                    break
    if left:
        print("note: {} un-backticked mention(s) of a dropped file remain (prose, left as is): {}".format(
            len(left), "; ".join(sorted(set(left))[:6])))
    return problems


def _label(ref: str, version: str) -> str:
    """`6.1.0` when <ref> IS that release's tag; otherwise `6.1.0+<commit>` — a package of unreleased
    work named like the release is how two different packages end up with one file name."""
    def _git(*a):
        r = subprocess.run(["git", "-C", str(REPO)] + list(a), capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    commit = _git("rev-parse", "--short", ref + "^{commit}")
    tag_commit = _git("rev-parse", "--short", "v{}^{{commit}}".format(version))
    return version if commit and commit == tag_commit else "{}+{}".format(version, commit or "unknown")


def build(ref: str, out: Path, limit: int = LIMIT, keep: bool = True,
          force: bool = False) -> tuple[int, Path | None]:
    work = Path(tempfile.mkdtemp(prefix="skillhub-build-"))
    full = _archive(ref, work / "full")
    pkg = _archive(ref, work / "pkg")
    gone = trim(pkg)
    marked = annotate(pkg, gone)
    problems = verify(pkg, full, limit)
    n = sum(1 for p in pkg.rglob("*") if p.is_file())
    version = (pkg / "VERSION").read_text(encoding="utf-8").strip() if (pkg / "VERSION").is_file() else "dev"
    print("package: {} files ({} dropped, {} doc mention(s) marked as source-repository only)".format(
        n, len(gone), marked))
    if problems:
        for p in problems:
            print("REFUSED: " + p)
        return 1, None
    if not keep:
        return 0, pkg
    label = _label(ref, version)
    out.mkdir(parents=True, exist_ok=True)
    folder = out / "slide-maker-{}-skillhub".format(label)
    zpath = out / "slide-maker-{}-skillhub.zip".format(label)
    taken = [str(p) for p in (folder, zpath) if p.exists()]
    if taken and not force:
        print("REFUSED: {} already exist(s) — it may be a package you uploaded. Move it, pick another "
              "--out, or pass --force to replace it.".format(", ".join(taken)))
        return 1, None
    if folder.exists():
        shutil.rmtree(folder)
    shutil.copytree(pkg, folder / "slide-maker")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(pkg.rglob("*")):
            if p.is_file():
                z.write(p, Path("slide-maker") / p.relative_to(pkg))
    print("wrote {} ({:.1f} MB) and the folder {}".format(zpath, zpath.stat().st_size / 1e6, folder))
    return 0, zpath


def _selftest() -> int:
    code, _ = build("HEAD", Path(tempfile.mkdtemp()), keep=False)
    print("[build_skillhub selftest] {}".format("ok" if code == 0 else "FAILED"))
    return code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", default="HEAD", help="git ref to package (default HEAD)")
    ap.add_argument("--out", default=str(Path.home() / "Downloads"), help="output folder (default ~/Downloads)")
    ap.add_argument("--limit", type=int, default=LIMIT, help="file limit (default 200, SkillHub's)")
    ap.add_argument("--force", action="store_true", help="replace an existing package of the same name")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    code, _ = build(a.ref, Path(os.path.expanduser(a.out)), a.limit, force=a.force)
    return code


if __name__ == "__main__":
    sys.exit(main())
