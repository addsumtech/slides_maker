#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 1 must decide WHO this is for and what they have to decide, before it gathers anything.

WHY. The pipeline gates the comprehension of a SOURCE thoroughly — fixed fields, a traced claim
ledger, an open ledger, a competed arc — and the FRAME not at all. On a deck with no source there
is nothing to comprehend, so the brief silently becomes a summary of the SUBJECT.

Measured on a delivered deck: the interview recorded `audience = people planning a trip` and
`goal = they leave able to plan one`. Step 1 wrote a brief about Melbourne. All three arc
candidates were then generated inside that frame, and the winner was picked because "it is the
only candidate whose organising idea also does the organising work … nothing is easier to remember
a week later" — a deck-quality test, with the recorded goal never used to score. The practical
candidate was rejected for becoming "the same list every travel site gives me", which for someone
planning a trip is the deliverable. What shipped was a thesis on an 1837 land survey.

The frame also aimed the RESEARCH: chain lengths, allotment widths and inscription years were
verified; daily cost, distances, a rainy-day alternative and what to skip were never asked for.
Every gate passed, twice, including a full render self-check.

🔴 AND THE RULE ALREADY EXISTED. `checkpoint-convention.md` carries the same lesson from a Paris
deck — refuse the obvious PICTURE, never the obvious SUBJECT — but scoped to the auto-waiver's
delegated Step-0 picks. That build ran a full interview and was never inside its scope. A correct
rule in the wrong scope is not a gate, which is why this one is a required field.

Run:  python3 tests/test_audience_brief.py
"""
import ast
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audience_brief as ab                      # noqa: E402
import arc_divergence as ad                      # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


GOOD = {"who": "the three people who sign the migration off, deciding whether to fund phase 2",
        "decisions": [{"decision": "fund phase 2 or stop", "needs": "phase 1's real cost"},
                      {"decision": "who owns the rollout", "needs": "where the work landed before"},
                      {"decision": "what to tell the board", "needs": "one repeatable number"}]}

check(ab.faults(GOOD) == [], "a filled brief passes")
check(ab.faults(None) and "is missing" in ab.faults(None)[0],
      "🔴 a MISSING brief is caught — the whole point, since the failure is silent: a subject "
      "brief looks like a brief and every later gate agrees with it")
check(any("decisions" in f for f in ab.faults({"who": GOOD["who"], "decisions": GOOD["decisions"][:2]})),
      "🔴 two decisions is not a brief — fewer than three is a persona, and a persona does not "
      "aim a search")
_no_needs = {"who": GOOD["who"],
             "decisions": [{"decision": d["decision"], "needs": ""} for d in GOOD["decisions"]]}
check(len(ab.faults(_no_needs)) == 3 and all("needs" in f for f in ab.faults(_no_needs)),
      "🔴 every decision needs its `needs` — that half is what aims the research, and it is the "
      "half the failing deck never had: it verified chain lengths and never asked what a day costs")
check(any("who" in f for f in ab.faults({"decisions": GOOD["decisions"]})),
      "...and `who` must say who is in the room, not be left to the interview record")

check(ab.is_waived({"waived": "a reference appendix nobody decides from"}),
      "a carve is claimable — a deck whose audience decides nothing is not forced to invent a list")
check(any("waived_category" in f for f in ab.waiver_faults({"waived": "x" * 40})),
      "...but the carve must be CLASSIFIED")
check(any("hard" in f for f in ab.waiver_faults({"waived": "x" * 40, "waived_category": "difficult"})),
      "🔴 ...and 'the deck was hard to think about' is not one of the carves — the message says so "
      "by name, because that is the waiver this field would otherwise attract")

# ── the arc competition is scored on the GOAL, not on elegance ───────────────────────────────
BASE = {"shape": "evidence-build", "roles": ["problem", "evidence", "conclusion"],
        "audience_question": "q", "objection": "o", "closing_ask": "a", "evidence": ["C1"]}
try:
    ad.check([dict(BASE, name="A"), dict(BASE, name="B")])
    _raised = False
except Exception as e:                                            # noqa: BLE001
    _raised = "serves_goal" in str(e)
check(_raised,
      "🔴 a candidate with no `serves_goal` is refused — the axis this competition kept being "
      "decided on was elegance, and the recorded goal sat unused in the same file")

SAME = [dict(BASE, name="A", serves_goal="it gets the room able to plan a trip"),
        dict(BASE, name="B", serves_goal="it gets the room able to plan a trip",
             audience_question="q2", objection="o2", closing_ask="a2",
             shape="recommendation-first", roles=["conclusion", "evidence", "roadmap"])]
r = ad.check(SAME)
check(r["same_goal"] and r["same_goal"][0]["overlap"] >= 0.6,
      "🔴 candidates that serve the goal in the SAME words are reported — one sentence copied "
      "across the set is the field being satisfied, not the competition being run")
DIFF = json.loads(json.dumps(SAME))
DIFF[1]["serves_goal"] = "it hands over a booked itinerary and the three costs, in order"
check(not ad.check(DIFF)["same_goal"],
      "...and two genuinely different routes to the same goal pass")

# ── every gate path reads ONE contract ──────────────────────────────────────────────────────
print("== one contract, three gates ==")
for name in ("deck_gates.py", "render_deck.py", "codex_delivery_gate.py"):
    tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"))
    imported = any(
        (isinstance(n, ast.Import) and any(a.name == "audience_brief" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "audience_brief")
        for n in ast.walk(tree))
    check(imported, "%s imports the shared audience_brief contract rather than restating it" % name)

_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
check("AUDIENCE BRIEF" in _skill and "content.audience_brief" in _skill,
      "🔴 SKILL.md Step 1 carries the rule in LAYER 1 — the Paris version of it lives in "
      "checkpoint-convention.md scoped to the AUTO-WAIVER, so a deck built from a full interview "
      "was never inside it. A correct rule in the wrong scope is not a gate")
check("takeaway spine" in _skill and "true statements ABOUT the subject" in _skill,
      "...and it carries the test for the case where you cannot tell which brief you wrote")
_spec = (ROOT / "references" / "content-plan-spec.md").read_text(encoding="utf-8")
check("Audience brief" in _spec and _spec.index("Audience brief") < _spec.index("Comprehension brief"),
      "...and the field spec puts it BEFORE the comprehension brief, which is the order it has to "
      "be written in")
_cp = (ROOT / "references" / "checkpoint-convention.md").read_text(encoding="utf-8")
check("`audience:` line" in _cp,
      "...and the Step-1 checkpoint carries an `audience:` line, so a subject-framed deck is one "
      "glance from a veto instead of surfacing at delivery")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
