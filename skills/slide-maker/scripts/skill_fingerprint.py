#!/usr/bin/env python3
"""One hash over the whole skill tree — so a COPIED install can tell it is not on main.

🔴 THE DEFECT THIS EXISTS FOR, measured. `check_version.py` on a copy install compares
`skills/slide-maker/VERSION` against the one on GitHub. `VERSION` only moves on a RELEASE, so
every commit between releases is invisible to it — which is precisely the development case. Tested
directly: a copy whose `SKILL.md` had been truncated to 2,000 bytes (of 278,400 — 99.3% of the
skill gone) passed `check_version.py --force` **silently, exit 0**, because its VERSION still read
`5.2.0`. Real consequence in one session: the installed copy was three commits behind, the check
said nothing, and a whole deck was built by a skill that did not contain the rules the repo had
already fixed and pushed.

A version STRING cannot answer "am I running what main has". A content fingerprint can, and it
needs no hook into an installer we do not own: `SKILL.sha256` is committed beside the skill and
says what main's tree hashes to, so a copy compares its OWN computed hash against that file
fetched from GitHub. Different hash, different tree — whichever direction.

    python3 scripts/skill_fingerprint.py            # print the fingerprint of this tree
    python3 scripts/skill_fingerprint.py --write     # regenerate SKILL.sha256
    python3 scripts/skill_fingerprint.py --check     # exit 1 if SKILL.sha256 is stale (CI)

Volatile paths are excluded because they differ between two identical installs and would make the
fingerprint report a difference that is not one: caches, OS turds, and the fingerprint file itself
(including it would be self-referential).
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
FINGERPRINT_FILE = SKILL_ROOT / "SKILL.sha256"

# Directory NAMES pruned anywhere in the tree, and file names/suffixes skipped.
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", ".mypy_cache", "node_modules"}
SKIP_NAMES = {".DS_Store", "SKILL.sha256", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".swp", ".orig", ".rej"}


def _files(root: Path):
    """Every tracked-looking file under `root`, sorted, with volatile paths pruned."""
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.name in SKIP_NAMES or p.suffix in SKIP_SUFFIXES:
            continue
        out.append(p)
    return out


def fingerprint(root: Path = SKILL_ROOT) -> str:
    """sha256 over `relative/path\\0<sha256 of contents>\\n` for every file, path-sorted.

    Paths are included, not just contents: a file RENAMED or DELETED must move the hash, and a
    contents-only digest would miss both. POSIX separators so a Windows checkout agrees with a
    macOS one.
    """
    h = hashlib.sha256()
    for p in _files(root):
        rel = p.relative_to(root).as_posix()
        fh = hashlib.sha256()
        with p.open("rb") as fp:
            for chunk in iter(lambda: fp.read(1 << 20), b""):
                fh.update(chunk)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(fh.hexdigest().encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def read_recorded() -> str | None:
    try:
        return FINGERPRINT_FILE.read_text(encoding="utf-8").split()[0].strip() or None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Fingerprint the skill tree.")
    ap.add_argument("--write", action="store_true", help="regenerate SKILL.sha256")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when SKILL.sha256 does not match the tree (CI)")
    a = ap.parse_args()

    actual = fingerprint()
    if a.write:
        FINGERPRINT_FILE.write_text(actual + "\n", encoding="utf-8")
        print("wrote {} = {}".format(FINGERPRINT_FILE.name, actual))
        return 0
    if a.check:
        recorded = read_recorded()
        if recorded == actual:
            print("SKILL.sha256 is current ({})".format(actual[:16]))
            return 0
        # Loud and actionable: a stale fingerprint silently disables the staleness check for
        # every copied install, which is the whole failure this file exists to end.
        print("SKILL.sha256 is STALE — recorded {} but the tree hashes to {}.\n"
              "  Run: python3 scripts/skill_fingerprint.py --write\n"
              "  It is committed beside the skill so a COPIED install can tell it is not on "
              "main; left stale, every such install silently believes it is current."
              .format((recorded or "<missing>")[:16], actual[:16]), file=sys.stderr)
        return 1
    print(actual)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
