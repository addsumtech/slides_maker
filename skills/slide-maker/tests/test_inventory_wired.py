#!/usr/bin/env python3
"""The file inventory must stay complete, and the guard must be a DETECTOR.

`references/file-inventory.md` is the lookup SKILL.md routes agents to by name. A capability
missing from it is one an agent cannot find — and the cost falls hardest on runtimes with nothing
else to consult, which is exactly the "non-Claude agents can use this" case.

This suite exists because of a defect measured in `check_inventory.py`'s own docstring: 11 of 77
scripts and 11 of 39 references were absent, and nothing reported it. A guard that only ever prints
green is the same failure one level up, so most of what follows is an attack on the guard itself.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
GUARD = SCRIPTS / "check_inventory.py"
INVENTORY = ROOT / "references" / "file-inventory.md"

sys.path.insert(0, str(SCRIPTS))
import check_inventory as ci  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def run(*args):
    p = subprocess.run([sys.executable, str(GUARD), *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


# ── the repo is currently complete ───────────────────────────────────────────────────────────────
rc, out = run()
check(rc == 0, "the inventory is INCOMPLETE right now:\n{}".format(out))
check("0 problem(s)" in out, "the guard did not report a clean count: {}".format(out.strip()[-200:]))

# ── 🔴 it must be a DETECTOR, not a decoration ───────────────────────────────────────────────────
# The repo has shipped a check that reported 0 on the very deck that motivated it. Prove this one
# fires, on each group it claims to cover, with the right EXIT CODE — a CI step reads the code.
for group, name in (("scripts", "zz_guard_probe.py"),
                    ("references", "zz_guard_probe.md"),
                    ("agents", "zz_guard_probe.md")):
    probe = ROOT / group / name
    probe.write_text("# a throwaway file, to prove the guard sees it\n", encoding="utf-8")
    try:
        rc, out = run()
        check(rc == 1, "an unlisted {}/{} did not make the guard EXIT 1 (got {}) — the CI step "
                       "reads the exit code, so a guard that prints a complaint and returns 0 is "
                       "green in CI".format(group, name, rc))
        check(name in out, "the complaint does not name the unlisted file: {}".format(out[-160:]))
    finally:
        probe.unlink()

rc, out = run()
check(rc == 0, "the guard stayed red after the probe files were removed — it is not reading the "
               "tree live")

# ── a stale ALLOWLIST entry is itself a fault ────────────────────────────────────────────────────
# Permission to skip a file that no longer exists is permission nobody reviewed. Found on the
# guard's own first run, in its own draft allowlist.
real = dict(ci.ALLOWLIST)
try:
    ci.ALLOWLIST.clear()
    ci.ALLOWLIST["zz_does_not_exist.py"] = "a reason for a file that is not there"
    rc = ci.main([])
    check(rc == 1, "a stale ALLOWLIST entry passed — nobody would ever notice the permission "
                   "outliving its file")
finally:
    ci.ALLOWLIST.clear()
    ci.ALLOWLIST.update(real)

# ── every allowlist entry carries a written reason ───────────────────────────────────────────────
for name, why in ci.ALLOWLIST.items():
    check(len(str(why).strip()) >= 12,
          "ALLOWLIST[{!r}] has no real reason — an unexplained skip is the thing this guard "
          "prevents, one level up".format(name))

# ── it cannot mistake a missing inventory for a clean one ────────────────────────────────────────
backup = INVENTORY.read_text(encoding="utf-8")
try:
    INVENTORY.unlink()
    rc, out = run()
    check(rc == 2, "a MISSING inventory returned {} — 'cannot run' must never look like 'clean'"
                   .format(rc))
finally:
    INVENTORY.write_text(backup, encoding="utf-8")

# ── the guard is itself wired into CI, and indexed ───────────────────────────────────────────────
ciyml = (ROOT.parent.parent / ".github" / "workflows" / "ci.yml")
if ciyml.exists():
    text = ciyml.read_text(encoding="utf-8")
    check("check_inventory.py" in text,
          "check_inventory.py is not run by CI — an unrun guard guards nothing")
    check("check_tests_wired.py" in text, "check_tests_wired.py is not run by CI")
else:
    check(True, "no CI workflow on this checkout — the wiring assertion is skipped, not faked")
check("check_inventory.py" in backup,
      "the guard is missing from the inventory it guards")

# ── the two guards must not overlap: tests/ belongs to check_tests_wired ─────────────────────────
check("tests" not in [g for g, _ in ci.GROUPS],
      "check_inventory claims tests/ too — check_tests_wired owns that, and it asserts something "
      "STRONGER (that CI runs them, not that a doc names them)")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_inventory_wired] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
