#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The hand-off gate reports EVERY failure in one run, and reports them no more softly.

WHY. `check_handoff_gates` used to stop at the first problem: 45 `die()` sites across ~15
independent stop classes, one per run. A thin `.deck-gates.json` therefore cost one
fail → fix → re-run round-trip PER FIELD, at the most expensive moment of the session (hand-off,
full context). `codex_delivery_gate.py` already accumulated its `errors` list, and
`validate_review.py`'s docstring already named "the ping-pong of one-error-at-a-time retries" as
the anti-pattern; this path was the holdout.

The batching is only worth having if it did not weaken anything, so both directions are asserted:

  BATCHES   — a record with N independent problems names all N in ONE run.
  STILL BLOCKS — nonzero exit, no pass line, and every message that fired before still fires.
  NO MASKING — within one section the FIRST stop still wins (its later checks read values the
               failed one was supposed to establish, so continuing would invent follow-on faults),
               and across sections nothing is suppressed.
  CLEAN IS CLEAN — a complete record still passes silently. A batching bug that reported phantom
               problems on a good deck would be worse than the ping-pong it replaced.

Run:  python3 tests/test_gate_batching.py
"""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
RENDER = SKILL / "scripts" / "render_deck.py"

sys.path.insert(0, str(HERE))
from test_critic_waiver_gate import (  # noqa: E402
    fit_content,  # noqa: E402  (the fixtures are deliberately shared)
    ARC_OK, DESIGN_OK, GOOD_REASON, PROV_OK, build_deck, write_proof,
)

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}\n       {detail}")


def gate(deck, gates, *flags):
    gates = fit_content(gates, deck)
    if "interview" not in gates:                 # the four recorded answers are now required;
        gates = dict(gates, interview={          # no fixture below is ABOUT the interview, so
            "language": "English", "density": "balanced",     # filling it here keeps each test
            "length": "medium 9-15", "goal": "inform"})       # about the thing it checks
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates), encoding="utf-8")
    p = subprocess.run([sys.executable, str(RENDER), str(deck), "--gate-check", "--static", *flags],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def full_record():
    return {"critic": {"verdict": "consent", "rounds": 2},
            "design_plan": copy.deepcopy(DESIGN_OK),
            "content": copy.deepcopy(ARC_OK),
            "provenance": copy.deepcopy(PROV_OK)}


def main():
    with tempfile.TemporaryDirectory() as td:
        deck_dir = pathlib.Path(td)
        deck = build_deck(deck_dir)
        write_proof(deck_dir)

        print("== a complete record still passes, and says nothing extra ==")
        rc, out = gate(deck, full_record())
        check("clean record exits 0", rc == 0, out)
        check("...and reports no phantom failures", "gate(s) failed" not in out, out)

        print("== four INDEPENDENT problems are all named in ONE run ==")
        # One per section: critic, design_plan, content.arc, provenance. Each of these blocked on
        # its own before; the point is that one run now names all four.
        rec = full_record()
        rec["critic"] = {"waived": GOOD_REASON}                    # a real reason, no category
        rec["design_plan"].pop("carried_by")                       # a required design field
        # IN PLACE: `content` now carries three independent artifacts (arc · slides · checkpoint)
        # and replacing the whole dict would break three sections, not the one this case is about.
        rec["content"]["arc"]["chosen"] = ""                       # empty winner
        rec["provenance"] = {"claims": {"not": "a list"}}          # tally-shaped, not per-claim
        rc, out = gate(deck, rec)
        check("still blocks", rc != 0, out)
        check("report says how many", "4 hand-off gate(s) failed" in out, out)
        for label in ("critic", "design_plan", "content.arc", "provenance"):
            check(f"names the {label} section", f"] {label}\n" in out, out)
        check("critic message survives verbatim", "waived_category" in out, out)
        check("design message survives verbatim", "carried_by" in out, out)
        check("arc message survives verbatim", "name the arc that won" in out, out)
        check("provenance message survives verbatim", "per-claim `claims` list" in out, out)
        check("tells the reader to fix them in one pass", "ONE pass" in out, out)

        print("== each failing section is still independently fatal on its own ==")
        for label, mutate, needle in (
            ("critic", lambda r: r.update(critic={"waived": GOOD_REASON}), "waived_category"),
            ("design_plan", lambda r: r["design_plan"].pop("carried_by"), "carried_by"),
            ("content.arc", lambda r: r["content"]["arc"].update(chosen=""), "name the arc"),
            # The arc verdict is RECOMPUTED at the gate, so removing the candidates removes the
            # only evidence the competition happened — a pasted verdict no longer stands in.
            ("content.arc", lambda r: r["content"]["arc"].pop("candidates"),
             "must carry the 2-3 candidate arcs"),
            # The content checkpoint's own table, and the record of how each checkpoint was
            # delivered: the two artifacts codex_delivery_gate always required and this path did not.
            ("content.slides", lambda r: r["content"].pop("slides"), "one row per slide"),
            ("checkpoints", lambda r: r["content"].pop("checkpoint"),
             "delegation changes WHO approves"),
            ("provenance", lambda r: r.update(provenance={"claims": {}}), "per-claim"),
        ):
            rec = full_record()
            mutate(rec)
            rc, out = gate(deck, rec)
            check(f"{label} alone still blocks", rc != 0 and needle in out, out)
            check(f"...and reports as a single failure", "1 hand-off gate failed" in out, out)

        print("== no masking WITHIN a section: the first stop wins, no invented follow-ons ==")
        # boldness is validated before the field sweep; with BOTH broken, only the first is
        # reported, because everything after it reads a dial the gate could not resolve.
        rec = full_record()
        rec["design_plan"]["boldness"] = "spicy"
        rec["design_plan"].pop("type_scale")
        rc, out = gate(deck, rec)
        check("one design_plan stop, not two", out.count("] design_plan\n") == 1, out)
        check("...and it is the one that ran first", "not a dial" in out, out)

        print("== a structural failure is reported alone and still blocks ==")
        (deck_dir / ".deck-gates.json").unlink()
        p = subprocess.run([sys.executable, str(RENDER), str(deck), "--gate-check", "--static"],
                           capture_output=True, text=True)
        out = p.stdout + p.stderr
        check("missing .deck-gates.json blocks", p.returncode != 0, out)
        check("...and names the file", ".deck-gates.json" in out, out)

        rc, out = gate(deck, {"critic": {"verdict": "consent"}, "delivery": "billboard"})
        check("an unknown recorded delivery blocks", rc != 0, out)
        check("...alone — later gates read the delivery it could not resolve",
              "1 hand-off gate failed" in out, out)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
