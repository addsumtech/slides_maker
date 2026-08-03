#!/usr/bin/env python3
"""check_versions — every version marker in this repo must say the same thing.

There are FOUR, and they are easy to bump unevenly:

    .claude-plugin/plugin.json        version                  (plugin manifest)
    .claude-plugin/marketplace.json   metadata.version         (marketplace listing)
    CHANGELOG.md                      first `## [x.y.z]`       (the release note)
    skills/slide-maker/VERSION        the whole file           (SHIPS WITH THE SKILL)

The fourth is the one worth explaining. `npx skills add` copies ONLY
`skills/slide-maker/`, so a copied install has none of the other three on disk — it used
to have nothing at all saying which version it was, which is why
`scripts/check_version.py` could not tell an npx user that an update existed. VERSION is
that marker, and it only works if it is bumped with the rest.

Why this is a CI gate and not a note in a release checklist: the update notice is SILENT
when current. If VERSION goes stale, every user is told they are up to date forever, and
nothing anywhere reports it — the failure is invisible by construction. A rule with no
gate is a suggestion, and this repo's own history says suggestions get missed.

    python3 scripts/check_versions.py          # exit 1 on any mismatch
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def read_markers() -> dict[str, tuple[str, str]]:
    """Return {label: (value, where)}. A marker that cannot be read is reported, not skipped —
    a silently absent marker is the same failure this gate exists to catch."""
    out: dict[str, tuple[str, str]] = {}

    p = ROOT / ".claude-plugin/plugin.json"
    out["plugin.json"] = (json.loads(p.read_text())["version"], str(p.relative_to(ROOT)))

    m = ROOT / ".claude-plugin/marketplace.json"
    out["marketplace.json"] = (json.loads(m.read_text())["metadata"]["version"],
                               str(m.relative_to(ROOT)))

    c = ROOT / "CHANGELOG.md"
    hit = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", c.read_text(encoding="utf-8"), re.M)
    out["CHANGELOG.md"] = (hit.group(1) if hit else "<no versioned heading>",
                           str(c.relative_to(ROOT)))

    v = ROOT / "skills/slide-maker/VERSION"
    out["skills/slide-maker/VERSION"] = (
        v.read_text(encoding="utf-8").strip() if v.is_file() else "<missing>",
        str(v.relative_to(ROOT)))

    return out


def main() -> int:
    try:
        markers = read_markers()
    except Exception as e:
        print(f"VERSION CHECK FAILED: could not read a marker — {e}")
        return 1

    width = max(len(k) for k in markers)
    for label, (value, _) in markers.items():
        print(f"  {label:<{width}}  {value}")

    values = {v for v, _ in markers.values()}
    if len(values) != 1:
        print("\nVERSION MISMATCH — these must be bumped together.")
        print("  The one that silently breaks users is skills/slide-maker/VERSION: it is the")
        print("  only marker an `npx skills add` install has on disk, so if it goes stale the")
        print("  update notice tells every copied install it is current, forever.")
        return 1

    only = values.pop()
    if not SEMVER.match(only):
        print(f"\nNOT SEMVER: {only!r} — expected x.y.z")
        return 1

    print(f"\nall four markers agree: {only}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
