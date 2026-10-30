#!/usr/bin/env python3
"""Every test file must be RUN by CI — a test nobody runs is not a test.

🔴 THE MEASURED DEFECT. `tests/` held 68 files and `.github/workflows/ci.yml` named 49 of them.
**Sixteen test files had never run in CI**, including two written in the same change as the feature
they protect (`test_audience_brief.py`, `test_shape_declarations.py`) and one that was ALREADY RED:
`test_review_integrity.py` had four failing assertions and nothing anywhere reported it.

This is the same shape as the local-runner defect that preceded it — a harness that reports on a
subset looks exactly like a harness that reports on everything, because a skipped check and a
passing check both produce no output. Adding the sixteen files fixes today; this fixes tomorrow,
because the seventeenth is written by someone who does not know the rule.

A test may be deliberately excluded — it needs a network, it is a slow soak, it is a helper module
imported by another suite — but that is a DECISION someone makes in writing, not a file quietly
sitting outside the run.

    python3 scripts/check_tests_wired.py            # from the skill directory
    python3 scripts/check_tests_wired.py --list     # what CI currently runs

Exit 0 clean · 1 unwired tests · 2 could not run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent
CI = REPO / ".github" / "workflows" / "ci.yml"

# Files that are deliberately not invoked as their own CI step. Each needs a written reason; an
# empty reason is the thing this script exists to prevent.
ALLOWLIST = {
    "test_critic_waiver_gate.py":
        "a helper module — `test_review_integrity.py` imports its fixtures and runs them in CI",
}


def test_files() -> list[Path]:
    return sorted((SKILL / "tests").glob("test_*.py"))


def wired(ci_text: str) -> set[str]:
    return set(re.findall(r"tests/(test_[a-z0-9_]+\.py)", ci_text))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print what CI runs and exit")
    a = ap.parse_args(argv)

    if not CI.exists():
        print("[tests-wired] no CI workflow at {} — cannot check.".format(CI), file=sys.stderr)
        return 2
    text = CI.read_text(encoding="utf-8")
    run = wired(text)
    files = test_files()
    if not files:
        print("[tests-wired] no test files found under {} — that is itself wrong."
              .format(SKILL / "tests"), file=sys.stderr)
        return 2

    if a.list:
        for f in files:
            mark = "run " if f.name in run else ("skip" if f.name in ALLOWLIST else "UNWIRED")
            print("{:<8} {}".format(mark, f.name))
        return 0

    missing = [f.name for f in files if f.name not in run and f.name not in ALLOWLIST]
    # …and every test runs HERMETIC: it imports tests/_hermetic.py before anything else, so a run on
    # a developer's machine never reads that person's taste.md / taste ledger (the gates read both),
    # and a result cannot depend on what they have taught the skill.
    leaky = [f.name for f in files
             if not re.search(r"^import _hermetic\b", f.read_text(encoding="utf-8"), re.M)]
    # …and the mirror: an allowlist entry for a file that no longer exists is stale permission.
    have = {f.name for f in files}
    stale = [n for n in ALLOWLIST if n not in have]
    ghosts = sorted(n for n in run if n not in have)

    for n in missing:
        print("[tests-wired] tests/{} is never run by CI. Add a step for it in "
              ".github/workflows/ci.yml, or add it to ALLOWLIST here WITH A REASON.".format(n))
    for n in leaky:
        print("[tests-wired] tests/{} does not `import _hermetic` (first import, after any "
              "`from __future__`) — it may read the user's own taste.md / taste ledger.".format(n))
    for n in stale:
        print("[tests-wired] ALLOWLIST names tests/{}, which no longer exists — stale permission."
              .format(n))
    for n in ghosts:
        print("[tests-wired] CI runs tests/{}, which does not exist — that step is failing or "
              "silently doing nothing.".format(n))

    bad = len(missing) + len(stale) + len(ghosts) + len(leaky)
    print("[tests-wired] {} test file(s): {} wired, {} allowlisted, {} problem(s)."
          .format(len(files), len(run & have), len(ALLOWLIST) - len(stale), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
