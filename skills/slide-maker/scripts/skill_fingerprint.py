#!/usr/bin/env python3
"""Can this COPY tell it is not running what main has? Compare git blob SHAs, commit nothing.

🔴 THE DEFECT THIS EXISTS FOR, measured. `check_version.py` on a copy install compares
`skills/slide-maker/VERSION` against the one on GitHub. `VERSION` only moves on a RELEASE, so every
commit between releases is invisible — which is precisely the development case. Tested directly: a
copy whose `SKILL.md` had been truncated to 2,000 bytes of 278,400 (99.3% of the skill gone) passed
`check_version.py --force` **silently, exit 0**, because its VERSION still read `5.2.0`. Real
consequence in one session: the installed copy was three commits behind, the check said nothing, and
a whole deck was built by a skill that did not contain rules the repo had already fixed and pushed.

A version STRING cannot answer "am I running what main has". File CONTENT can, and GitHub already
stores the answer: every blob in the tree carries its git SHA, which is
`sha1("blob <len>\\0" + bytes)` — computable locally with no git installed and no artifact committed
to the repo. One API call gets the whole subtree.

🔴 **The comparison is deliberately ONE-DIRECTIONAL: does everything I HAVE match main?** An
installer chooses what to copy (`npx skills add` lands ~55 files where the tree has ~193), so
demanding an exact set would report "differs" on every correct install forever. The honest limit of
that choice is stated where it matters: a copy that is merely MISSING a file added after it was
installed will not be caught — every file it does have being current is what this can prove.

    python3 scripts/skill_fingerprint.py            # compare this tree against main
    python3 scripts/skill_fingerprint.py --local    # just list what we would compare
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO = "addsumtech/slides_maker"
TREE_URL = (f"https://api.github.com/repos/{REPO}/git/trees/"
            "main:skills%2Fslide-maker?recursive=1")
NET_TIMEOUT = 4

# Pruned anywhere in the tree: these differ between two identical installs, so comparing them
# would report a difference that is not one.
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", ".mypy_cache", "node_modules"}
SKIP_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".swp", ".orig", ".rej"}


def blob_sha(path: Path) -> str:
    """The file's git blob SHA — identical to `git hash-object <path>`, without needing git."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def local_blobs(root: Path = SKILL_ROOT) -> dict[str, str]:
    """`{posix relative path: blob sha}` for every comparable file under `root`."""
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in SKIP_NAMES or p.suffix in SKIP_SUFFIXES:
            continue
        try:
            out[rel.as_posix()] = blob_sha(p)
        except OSError:
            continue
    return out


def remote_blobs() -> dict[str, str] | None:
    """`{path: blob sha}` from main's tree, or None when the answer is unavailable.

    Unavailable is not "current": every caller treats None as "could not tell" and says nothing,
    because this must never be the reason a deck did not get built.
    """
    try:
        req = urllib.request.Request(
            TREE_URL, headers={"User-Agent": "slide-maker-version-check",
                               "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None
    if data.get("truncated"):
        # GitHub truncates very large trees. A partial answer would produce false "differs" rows,
        # so refuse it rather than report a difference we cannot stand behind.
        return None
    tree = data.get("tree")
    if not isinstance(tree, list):
        return None
    return {e["path"]: e["sha"] for e in tree
            if isinstance(e, dict) and e.get("type") == "blob" and e.get("path") and e.get("sha")}


def compare(root: Path = SKILL_ROOT) -> tuple[bool | None, list[str]]:
    """(matches, differing_paths). `matches` is None when the comparison could not be made.

    A local file absent from main is skipped, not reported: an installer's subset is legitimate and
    so is a user's own file dropped into the folder.
    """
    remote = remote_blobs()
    if not remote:
        return None, []
    local = local_blobs(root)
    if not local:
        return None, []
    differing = sorted(rel for rel, sha in local.items()
                       if rel in remote and remote[rel] != sha)
    return (not differing), differing


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare this skill tree against main.")
    ap.add_argument("--local", action="store_true", help="list local blob SHAs and stop")
    a = ap.parse_args()
    if a.local:
        for rel, sha in sorted(local_blobs().items()):
            print("{}  {}".format(sha, rel))
        return 0
    matches, differing = compare()
    if matches is None:
        print("could not compare (offline, rate-limited, or the tree was truncated)")
        return 0
    if matches:
        print("this tree matches {}@main for every file it has".format(REPO))
        return 0
    print("DIFFERS from {}@main in {} file(s):".format(REPO, len(differing)), file=sys.stderr)
    for rel in differing[:20]:
        print("  {}".format(rel), file=sys.stderr)
    if len(differing) > 20:
        print("  … and {} more".format(len(differing) - 20), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
