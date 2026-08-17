#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Two looks made into artifacts: the actor's render self-check (#1) and the critic record (#2).

WHY (user directive). The gate set measures whether the design WORK happened; the two remaining
"look at it" steps were prose with no backstop:

  #1 RENDER SELF-CHECK — Step 5 tells the coordinator to read every slide PNG and record a one-line
     verdict per slide ("a slide with no line was not checked"). The cheap actor-side look that
     catches an overflow / wrong number BEFORE a critic round is spent had no trace, so it was the
     easiest step to skip silently. Now: `render_selfcheck.slides`, one verdict per slide.

  #2 CRITIC RECORD — a consent used to pass as a bare `{"verdict":"consent","rounds":N}`, labelled
     SELF-REPORTED. That is the last self-cert hole: a skipped loop writes the identical JSON to a
     real one. Consent now REQUIRES the recorded review artifact (path + sha256, coverage bound to
     the deck). The escape is the honest WAIVER (no-dispatch-on-host), not a weaker consent.

Both hold on BOTH gate paths (render_deck + codex_delivery_gate) — they have drifted before. These
tests write .deck-gates.json DIRECTLY (not through fit_content, which auto-supplies both) so the
FAILURE paths are actually exercised.

Run:  python3 tests/test_review_integrity.py
"""
import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
RENDER = SKILL / "scripts" / "render_deck.py"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(HERE))

from test_critic_waiver_gate import (  # noqa: E402
    ARC_OK, DESIGN_OK, GOOD_REASON, PROV_OK, build_deck, content_ok, selfcheck_ok, write_proof,
)

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}\n       {str(detail)[:360]}")


def gate(deck, gates):
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates, ensure_ascii=False),
                                                  encoding="utf-8")
    p = subprocess.run([sys.executable, str(RENDER), str(deck), "--gate-check", "--static"],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def base(n, deck, **over):
    """A clean gates dict for an n-slide deck, with BOTH new artifacts present."""
    g = {"critic": {"waived": GOOD_REASON, "waived_category": "no-dispatch-on-host",
                    "inline_ran": True},
         "design_plan": copy.deepcopy(DESIGN_OK), "content": content_ok(n),
         "render_selfcheck": selfcheck_ok(n), "provenance": copy.deepcopy(PROV_OK)}
    g.update(over)
    return g


def record_review(deck, n, verdict="consent", findings=None, opened=None):
    """Write a real review file next to the deck and return the {source, sha256} critic block."""
    review = {"verdict": verdict, "findings": findings or [],
              "coverage": {"slides_opened": opened if opened is not None else list(range(1, n + 1))}}
    rp = deck.parent / "review.json"
    rp.write_text(json.dumps(review), encoding="utf-8")
    return {"verdict": verdict, "rounds": 2, "source": str(rp),
            "sha256": hashlib.sha256(rp.read_bytes()).hexdigest()}


def main():
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        n = 3
        deck = build_deck(d, n)
        write_proof(d)

        print("== #1  the render self-check is now a required trace ==")
        g = base(n, deck)
        g.pop("render_selfcheck")
        rc, out = gate(deck, g)
        check("a deck with no render_selfcheck is refused", rc != 0 and "render_selfcheck" in out, out)
        check("...and the message says one line per slide", "one line per slide" in out, out)

        rc, out = gate(deck, base(n, deck))
        check("one verdict per slide passes", rc == 0, out)

        g = base(n, deck, render_selfcheck={"slides": selfcheck_ok(n)["slides"][:2]})
        rc, out = gate(deck, g)
        check("fewer verdicts than slides is refused", rc != 0 and "every slide" in out.lower(), out)

        g = base(n, deck, render_selfcheck={"slides": [{"n": i, "verdict": "<what you saw>"}
                                                       for i in range(1, n + 1)]})
        rc, out = gate(deck, g)
        check("a placeholder verdict is refused", rc != 0, out)

        g = base(n, deck, render_selfcheck={"waived": "静态 fixture，无渲染稿可看"})
        rc, out = gate(deck, g)
        check("a written waiver is honoured", rc == 0 and "render self-check WAIVED" in out, out)

        print("== #2  a consent now needs the recorded review artifact, not a bare claim ==")
        g = base(n, deck, critic={"verdict": "consent", "rounds": 2})
        rc, out = gate(deck, g)
        check("a bare consent (no source) is REFUSED", rc != 0 and "no `source`" in out, out)
        check("...and it points at validate_review --record",
              "validate_review.py" in out and "--record" in out, out)
        check("...and it names the honest waiver escape", "no-dispatch-on-host" in out, out)

        g = base(n, deck, critic=record_review(deck, n))
        rc, out = gate(deck, g)
        check("a recorded review (source + sha256 + full coverage) passes",
              rc == 0 and "verified against" in out, out)

        # sha256 must bind the file: tamper it after recording -> refused
        cb = record_review(deck, n)
        (deck.parent / "review.json").write_text(json.dumps(
            {"verdict": "consent", "findings": [], "coverage": {"slides_opened": [1, 2, 3]},
             "x": "tampered"}), encoding="utf-8")
        rc, out = gate(deck, base(n, deck, critic=cb))
        check("a review edited after recording fails the sha256 bind", rc != 0 and "sha256" in out, out)

        # a consent recorded over a blocker finding is refused (contract: any blocker -> revise)
        g = base(n, deck, critic=record_review(deck, n, findings=[
            {"severity": "blocker", "issue": "x"}]))
        rc, out = gate(deck, g)
        check("consent while carrying a blocker finding is refused",
              rc != 0 and "blocker" in out.lower(), out)

        # the honest waiver still passes (labelled not independent)
        rc, out = gate(deck, base(n, deck))   # base uses the no-dispatch waiver
        check("the no-dispatch waiver still passes (honest, not a consent)",
              rc == 0 and "NOT INDEPENDENTLY REVIEWED" in out, out)

    print("== both gate paths carry the render_selfcheck check ==")
    src_codex = (SKILL / "scripts" / "codex_delivery_gate.py").read_text(encoding="utf-8")
    src_render = (SKILL / "scripts" / "render_deck.py").read_text(encoding="utf-8")
    check("render_deck has the render_selfcheck gate section",
          "_gate_section('render_selfcheck')" in src_render)
    check("codex_delivery_gate has check_render_selfcheck", "check_render_selfcheck" in src_codex)
    check("render_deck refuses a source-less consent (die, not SELF-REPORTED print)",
          'no `source`' in src_render and "SELF-REPORTED (no review" not in src_render)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
