#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_plan_record.py — the art director's Design plan is a FILE the gate re-reads, not a summary.

Measured 2026-11-07: in eight real runs of the current skill not one opened agents/slide-design.md —
the agents typed the design_plan fields themselves — while three of four runs of the older skill read
it, and the older skill won a blind design comparison on three or four of four briefs. The gate
already required the fields; nothing required the art director. What this suite holds the script to:

  · a plan carrying slide-design.md's Output sections (English or Chinese headings) and its
    self-verify checks validates; one missing a section or most of the checks does not, by name;
  · `record` writes design_plan.plan_file (path · sha256 · dispatched) and keeps every other field;
  · the gate finds nothing wrong with a recorded, dispatched plan, and names the fault when the
    record is missing, the file changed after recording, or a self-authored plan has no allowed
    waiver category.

Run:  python3 tests/test_design_plan_record.py
"""
import _hermetic  # noqa: F401,E402
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import design_plan_record as DPR  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  %s" % (detail,)))


CHECKS = "\n".join("- **(%s)** passes — reason" % c for c in "abcdefghijklmnopqrs")
PLAN_EN = ("# Design plan\n\n### Design language\nconcept: a ledger\n\n### Deck rhythm\nquiet-loud-quiet\n\n"
           "### Per-slide design\n| 1 | cover |\n\n### Form ledger + diversity gate\ncards: 2\n\n"
           "### Design self-verify\n" + CHECKS + "\n")
PLAN_ZH = ("# 设计方案\n\n## 设计语言\n概念：账本\n\n## 整体节奏\n静-响-静\n\n## 逐页设计\n| 1 | 封面 |\n\n"
           "## 形式台账\n卡片 2\n\n## 设计自检\n" + CHECKS + "\n")

print("── validate")
check("an English plan with every Output section validates", DPR.validate(PLAN_EN) == [], DPR.validate(PLAN_EN))
check("a Chinese plan with every Output section validates", DPR.validate(PLAN_ZH) == [], DPR.validate(PLAN_ZH))
no_rhythm = PLAN_EN.replace("### Deck rhythm\nquiet-loud-quiet\n\n", "")
check("a missing section is named", any("deck rhythm" in f.lower() for f in DPR.validate(no_rhythm)),
      DPR.validate(no_rhythm))
few = PLAN_EN.replace(CHECKS, "\n".join("- (%s) ok" % c for c in "abcde"))
check("a plan carrying 5 of the 19 self-verify checks is refused",
      any("self-verify" in f.lower() for f in DPR.validate(few)), DPR.validate(few))
check("an empty file is refused", DPR.validate("") != [])

print("── record + gate")
TMP = pathlib.Path(tempfile.mkdtemp(prefix="dpr-"))
deck = TMP / "deck"
deck.mkdir()
(deck / ".deck-gates.json").write_text(json.dumps({"design_plan": {"boldness": "bold", "palette": "p"}}),
                                       encoding="utf-8")
plan = TMP / "design-plan.md"
plan.write_text(PLAN_EN, encoding="utf-8")
r = subprocess.run([sys.executable, str(SCRIPTS / "design_plan_record.py"), str(plan), "--deck", str(deck),
                    "--dispatched"], capture_output=True, text=True)
g = json.loads((deck / ".deck-gates.json").read_text(encoding="utf-8"))
pf = (g.get("design_plan") or {}).get("plan_file") or {}
check("record exits 0", r.returncode == 0, r.stdout + r.stderr)
check("record writes path, sha256 and dispatched", pf.get("dispatched") is True and len(pf.get("sha256", "")) == 64
      and pf.get("path"), pf)
check("record keeps the other design_plan fields", g["design_plan"].get("boldness") == "bold")
check("gate: a recorded, dispatched plan has no fault", DPR.gate_faults(g["design_plan"], str(deck)) == [],
      DPR.gate_faults(g["design_plan"], str(deck)))
check("gate: no plan_file is a fault that says how to record one",
      any("design_plan_record.py" in f for f in DPR.gate_faults({"boldness": "x"}, str(deck))))
plan.write_text(PLAN_EN + "\nedited later\n", encoding="utf-8")
check("gate: a plan edited after recording is a fault",
      any("changed" in f for f in DPR.gate_faults(g["design_plan"], str(deck))))
plan.write_text(PLAN_EN, encoding="utf-8")
self_auth = dict(g["design_plan"], plan_file=dict(pf, dispatched=False))
check("gate: a self-authored plan without an allowed waiver is a fault",
      any("no-dispatch-on-host" in f for f in DPR.gate_faults(self_auth, str(deck))))
ok_waiver = dict(g["design_plan"], plan_file=dict(pf, dispatched=False, waived="host has no subagent tool",
                                                   waived_category="no-dispatch-on-host"))
check("gate: a self-authored plan with no-dispatch-on-host + a reason passes",
      DPR.gate_faults(ok_waiver, str(deck)) == [], DPR.gate_faults(ok_waiver, str(deck)))
bad = subprocess.run([sys.executable, str(SCRIPTS / "design_plan_record.py"), str(TMP / "nope.md"), "--deck",
                      str(deck), "--dispatched"], capture_output=True, text=True)
check("record on a missing file is a clear error, not a traceback",
      bad.returncode != 0 and "Traceback" not in bad.stderr, bad.stderr[-300:])

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
