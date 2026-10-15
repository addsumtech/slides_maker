#!/usr/bin/env python3
"""Every script, agent and reference must appear in `references/file-inventory.md`.

🔴 WHY. SKILL.md routes agents to that file by name — "Full inventory … is in
`references/file-inventory.md`. Read it whenever you need a capability the *Where things live* table
doesn't already route." A capability missing from it is one an agent cannot find, and the cost falls
hardest on the runtimes that have nothing else to consult: a Claude session can grep `scripts/`, a
Codex or GPT agent following the documented route cannot see what the route never mentions.

MEASURED AT INTRODUCTION, 2026-09-12: **11 of 77 scripts and 11 of 39 references were absent**,
including `deck_cycle.py` (the loop-breaker every build iteration goes through), `run_eval.py` (the
only thing that scores a produced deck), `interview-protocol.md` (all of Step 0) and
`security-and-capabilities.md` (what the skill does to your machine). Nothing reported it, because a
missing entry and a complete file read exactly the same.

This is the same shape as `check_tests_wired.py`: adding the twenty-two fixes today, and the guard
fixes the twenty-third — written by someone who does not know the rule.

A file may be deliberately unlisted — a private helper, a fixture, an experiment. That is a
DECISION someone writes down in ALLOWLIST, not a file quietly sitting outside the index.

    python3 scripts/check_inventory.py           # from the skill directory
    python3 scripts/check_inventory.py --list    # what is indexed and what is not

Exit 0 clean · 1 unlisted files · 2 could not run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
INVENTORY = SKILL / "references" / "file-inventory.md"

# What counts as a documented capability. `tests/` is deliberately absent: `check_tests_wired.py`
# owns that one, and it checks something stronger (that CI RUNS them, not that a file names them).
GROUPS = (("scripts", "*.py"), ("scripts/vl_specs", "*.py"), ("agents", "*"), ("references", "*.md"))

# Deliberately unlisted, each with the reason. An empty reason is the thing this script prevents.
ALLOWLIST: dict[str, str] = {
    # Empty on purpose. The first run of this guard found both of its own draft entries to be
    # wrong — one named a file that does not exist, the other a file the inventory already lists.
    # Add an entry only when a real file is deliberately undocumented, and say why.
}


def indexed_text() -> str:
    return INVENTORY.read_text(encoding="utf-8")


def survey():
    """[(group, filename, listed)] for every file this inventory claims to cover."""
    text = indexed_text()
    rows = []
    for group, pat in GROUPS:
        d = SKILL / group
        if not d.is_dir():
            continue
        for f in sorted(d.glob(pat)):
            if not f.is_file() or f.name.startswith("."):
                continue
            rows.append((group, f.name, f.name in text))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print every file and whether it is indexed")
    a = ap.parse_args(argv)

    if not INVENTORY.exists():
        print("[inventory] missing {} — the file SKILL.md routes agents to.".format(INVENTORY),
              file=sys.stderr)
        return 2
    rows = survey()
    if not rows:
        print("[inventory] found nothing to check under {} — that is itself wrong."
              .format(SKILL), file=sys.stderr)
        return 2

    if a.list:
        for group, name, listed in rows:
            mark = "in  " if listed else ("skip" if name in ALLOWLIST else "MISSING")
            print("{:<8} {:<12} {}".format(mark, group, name))
        return 0

    missing = [(g, n) for g, n, listed in rows if not listed and n not in ALLOWLIST]
    have = {n for _, n, _ in rows}
    stale = [n for n in ALLOWLIST if n not in have]

    for group, name in missing:
        print("[inventory] {}/{} is not named anywhere in references/file-inventory.md. Add an "
              "entry describing what it DOES — read the file first; a guessed description is worse "
              "than none — or add it to ALLOWLIST here with a reason.".format(group, name))
    for name in stale:
        print("[inventory] ALLOWLIST names {}, which no longer exists — stale permission."
              .format(name))

    bad = len(missing) + len(stale)
    print("[inventory] {} file(s) across {}: {} indexed, {} allowlisted, {} problem(s)."
          .format(len(rows), " + ".join(g for g, _ in GROUPS),
                  sum(1 for _, n, l in rows if l), len(ALLOWLIST) - len(stale), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
