#!/usr/bin/env python3
"""Runtime drift must be impossible to introduce silently.

The two gate paths have drifted apart three times — `png`/`path`, `design_plan`/`design`, and
`checkpoints` — each time invisibly, because a gate that never runs and a gate that passes look
identical from outside. This suite attacks the guard rather than running it: a guard that only ever
prints green is the same failure one level up.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
GUARD = SCRIPTS / "check_gate_parity.py"
sys.path.insert(0, str(SCRIPTS))
import check_gate_parity as gp  # noqa: E402

os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/nonexistent/taste-ledger-for-tests.json"
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def run():
    p = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


rc, out = run()
check(rc == 0, "the two gate paths are OUT OF PARITY right now:\n{}".format(out))
check("0 problem(s)" in out, "the guard did not report a clean count: {}".format(out[-200:]))

# 🔴 it must DETECT, and with the right exit code — a CI step reads the code, so a guard that
# complains and returns 0 is green in CI.
codex = SCRIPTS / "codex_delivery_gate.py"
backup = codex.read_text(encoding="utf-8")
try:
    codex.write_text(backup.replace("blind_read", "zz_gone"), encoding="utf-8")
    rc, out = run()
    check(rc == 1, "a gate section removed from the Codex path did not make the guard EXIT 1 "
                   "(got {})".format(rc))
    check("blind_read" in out, "the complaint does not name the section that went missing")
finally:
    codex.write_text(backup, encoding="utf-8")
rc, _ = run()
check(rc == 0, "the guard stayed red after the file was restored — it is not reading live")

# a shared CONTRACT dropped from one side is the png/path class and must fire too
try:
    codex.write_text(backup.replace("taste_ledger", "zz_gone_contract"), encoding="utf-8")
    rc, out = run()
    check(rc == 1 and "taste_ledger" in out,
          "a shared contract module missing from one runtime was not reported (rc={})".format(rc))
finally:
    codex.write_text(backup, encoding="utf-8")

# a stale allowlist entry is permission nobody reviewed
real = dict(gp.ALLOWLIST)
try:
    gp.ALLOWLIST.clear()
    gp.ALLOWLIST["zz_not_a_section"] = "a reason for a gate that does not exist"
    check(gp.main([]) == 1, "a stale ALLOWLIST entry passed")
finally:
    gp.ALLOWLIST.clear()
    gp.ALLOWLIST.update(real)

for name, why in gp.ALLOWLIST.items():
    check(len(str(why).strip()) >= 20,
          "ALLOWLIST[{!r}] has no real reason — an unexplained one-sided gate is exactly what this "
          "guard exists to surface".format(name))

# it must not be able to match nothing and call that clean
check(len(gp.sections()) >= 10,
      "the guard found {} gate sections — if the pattern it reads ever changes it would report "
      "clean forever".format(len(gp.sections())))
check(set(gp.CONTRACTS) >= {"anchor_proof", "material_probe", "blind_read", "delegated_picks"},
      "the contract list lost a module that exists BECAUSE the two paths disagreed about it")

ci = ROOT.parent.parent / ".github" / "workflows" / "ci.yml"
if ci.exists():
    check("check_gate_parity.py" in ci.read_text(encoding="utf-8"),
          "check_gate_parity.py is not run by CI — an unrun guard guards nothing")
else:
    check(True, "no CI workflow on this checkout — skipped, not faked")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_gate_parity] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
