#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 1 and Step 2 must leave ARTIFACTS, not a report about themselves.

WHY. Measured across one session, from the transcript rather than from memory:

  deck              interview?   arc_divergence.py runs   content checkpoint table posted
  DeepSeek Harness  yes          3                        1
  Paris v1          delegated    0                        0
  Paris travel      delegated    0                        0

Both delegated decks passed every hand-off gate. Both are the decks whose design was judged flat
and whose direction was judged wrong. The one with a real interview is the one that ran the
pipeline. The trigger is the per-deck AUTO WAIVER: it converts the two 🔴 stops into FYIs, and an
FYI is prose with no backstop — the class this skill's own enforcement invariant ranks last.

Three holes are closed here, and the first is the sharpest:

  ARC RECOMPUTED   `content.arc.divergence` was a STRING the run wrote about itself. A delivered
                   deck passed with the two characters "ok" while `arc_divergence.py` had never
                   been invoked for it. The gate now takes `candidates` and runs `check()` itself,
                   so passing costs the work rather than the sentence.
  CONTENT.SLIDES   the content checkpoint's own table (`# | 角色 | 记忆句 | 承载证据 | units`)
                   reaches the gate file. NOT a new field: codex_delivery_gate has required
                   `content.slides` all along — the asymmetry was that the CODEX path demanded the
                   artifact and the shared path did not.
  CHECKPOINT MODE  `content.checkpoint` / `design.checkpoint`, mode `approved` | `auto` — also
                   codex's existing spelling. Delegation must change WHO approves, not WHETHER the
                   step happened, and the hand-off must say which one it got.

Run:  python3 tests/test_step1_artifacts.py
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
CODEX = SKILL / "scripts" / "codex_delivery_gate.py"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(HERE))

import arc_divergence  # noqa: E402
import render_deck as RD  # noqa: E402
from test_critic_waiver_gate import (  # noqa: E402
    ARC_CANDIDATES, DESIGN_OK, GOOD_REASON, PROV_OK, build_deck, content_ok, selfcheck_ok,
    write_proof,
)

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}\n       {str(detail)[:400]}")


def gate(deck, gates):
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates, ensure_ascii=False),
                                                  encoding="utf-8")
    p = subprocess.run([sys.executable, str(RENDER), str(deck), "--gate-check", "--static"],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def record(n=3, **content):
    c = content_ok(n)
    c.update(content)
    return {"critic": {"waived": GOOD_REASON, "waived_category": "no-dispatch-on-host",
                       "inline_ran": True},
            "design_plan": copy.deepcopy(DESIGN_OK), "content": c,
            "render_selfcheck": selfcheck_ok(n),
            "provenance": copy.deepcopy(PROV_OK)}


def main():
    print("== the record that shipped: `divergence: ok` with no competition behind it ==")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        deck = build_deck(d)
        write_proof(d)

        # THE REGRESSION CASE, verbatim from the delivered deck's .deck-gates.json.
        shipped = record()
        shipped["content"]["arc"] = {
            "chosen": "到了之后会问的顺序（problem-turn-evidence）",
            "rejected": [{"name": "景点排行榜", "why_lost": "读完仍不知道怎么安排一天"},
                         {"name": "按历史时间线", "why_lost": "读者要的是怎么玩不是编年史"}],
            "divergence": "ok"}
        rc, out = gate(deck, shipped)
        check("the exact shipped record is now REFUSED", rc != 0, out)
        check("...and the message says the candidates themselves are the evidence",
              "must carry the 2-3 candidate arcs" in out, out)
        check("...and points at the template that produces them",
              "--template" in out, out)

        print("== the raw --template skeleton, pasted unedited, is REFUSED (adversary-found) ==")
        # An adversarial verify pass defeated the first cut: `arc_divergence.py --template` prints a
        # fillable skeleton whose fields are `<label-A>` etc., and the die() messages here print more
        # of them. The unedited skeleton passed — every floor measured WIDTH and a placeholder is
        # wide — so "faking it costs the work" was false: the cost was one shell command and a paste.
        tmpl = json.loads(subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "arc_divergence.py"), "--template"],
            capture_output=True, text=True).stdout)
        rec = record()
        rec["content"]["arc"] = {"chosen": "<label-A>", "candidates": tmpl,
                                 "rejected": [{"name": "<label-B>", "why_lost": "<one clause>"}]}
        rc, out = gate(deck, rec)
        check("the unedited arc --template output is refused", rc != 0, out)
        check("...naming the placeholder fields, not a width complaint",
              "raw `--template` placeholder" in out and "candidates[0]" in out, out)

        # ...and the same blindness in the OTHER two artifacts: the die() messages' own example text.
        rec = record()
        rec["content"]["slides"][1]["takeaway"] = "<the one sentence this slide leaves behind>"
        rc, out = gate(deck, rec)
        check("a placeholder takeaway is refused (not just a stub token)", rc != 0, out)
        rec = record()
        rec["content"]["slides"][1]["evidence"] = ["<SOURCE TRACE — a locator, not a label>"]
        rc, out = gate(deck, rec)
        check("a placeholder evidence trace is refused", rc != 0, out)
        rec = record()
        rec["content"]["checkpoint"]["record"] = "<what the checkpoint recorded>"
        rc, out = gate(deck, rec)
        check("a placeholder checkpoint record is refused", rc != 0, out)

        # The guard must NOT fire on real prose that merely contains an angle bracket — a rule that
        # blocks legitimate work only teaches authors which value gets them through.
        rec = record()
        rec["content"]["slides"][1]["takeaway"] = "增长 <5% 时不必调价，这是一条真实的经验阈值"
        rec["content"]["slides"][1]["evidence"] = ["运营手册 p.4：阈值 <5%"]
        rc, out = gate(deck, rec)
        check("a real '<5%' string is NOT mistaken for a placeholder", rc == 0, out)

        print("== a real competition passes, and the gate says it scored it ITSELF ==")
        rc, out = gate(deck, record())
        check("2 diverging candidates + every loser named passes", rc == 0, out)
        check("...and the line says the scoring happened here",
              "scored HERE" in out, out)

        print("== faking it now costs the work: the candidates are actually scored ==")
        # Two candidates that are one arc in two wordings: same shape, same opening, same ask.
        twins = copy.deepcopy(ARC_CANDIDATES)
        twins[1]["shape"] = twins[0]["shape"]
        twins[1]["roles"] = list(twins[0]["roles"])
        twins[1]["closing_ask"] = twins[0]["closing_ask"]
        twins[1]["audience_question"] = twins[0]["audience_question"]
        twins[1]["objection"] = twins[0]["objection"]
        rec = record()
        rec["content"]["arc"]["candidates"] = twins
        rc, out = gate(deck, rec)
        check("a set that only LOOKS like a competition is caught", rc != 0, out)
        check("...by the recomputation, not by a field being absent",
              "RECOMPUTED here" in out and "tell the same story" in out, out)
        check("...and the fix offered is rediverge-or-justify, never an auto-kill",
              "divergence_justified" in out, out)

        rec["content"]["arc"]["divergence_justified"] = \
            "这两条确实同形，但保留是因为要给听众看同一材料的两种收尾差别"
        rc, out = gate(deck, rec)
        check("a justified flag passes, and prints the finding beside the justification",
              rc == 0 and "flagged" in out and "justified:" in out, out)

        # A strawman: same divergence, but one candidate nobody developed.
        thin = copy.deepcopy(ARC_CANDIDATES)
        thin[0]["evidence"] = ["c1", "c2", "c3", "c4", "c5", "c6"]
        thin[1]["evidence"] = ["c1"]
        rec = record()
        rec["content"]["arc"]["candidates"] = thin
        rc, out = gate(deck, rec)
        check("a strawman candidate is caught even when the set diverges",
              rc != 0 and "strawman" in out, out)

        print("== the winner has to be IN the field, and every loser on the record ==")
        rec = record()
        rec["content"]["arc"]["chosen"] = "an arc that never competed"
        rc, out = gate(deck, rec)
        check("a winner from outside the candidate set is refused",
              rc != 0 and "not one of the candidates" in out, out)

        rec = record()
        rec["content"]["arc"]["candidates"] = copy.deepcopy(ARC_CANDIDATES) + [
            {"name": "chronological", "shape": "chronological",
             "roles": ["hook", "case-study", "roadmap"],
             "audience_question": "how did the project actually unfold over the year",
             "objection": "a story is not a result",
             "closing_ask": "keep the team funded through the next milestone",
             "evidence": ["c2", "c4"]}]
        rc, out = gate(deck, rec)
        check("a third candidate that lost but is not on the rejected list is refused",
              rc != 0 and "skips" in out and "chronological" in out, out)
        check("...with the reason spelled out, not just the field name",
              "flattering half" in out, out)

        rec = record()
        rec["content"]["arc"]["rejected"].append(
            {"name": "a name nobody entered", "why_lost": "it lost a race it was not in"})
        rc, out = gate(deck, rec)
        check("a loser that never competed is refused",
              rc != 0 and "never competed" in out, out)

        print("== the content checkpoint's TABLE is now an artifact ==")
        rec = record()
        rec["content"].pop("slides")
        rc, out = gate(deck, rec)
        check("no per-slide plan blocks the hand-off", rc != 0, out)
        check("...and the message names the convention it comes from",
              "checkpoint-convention.md" in out, out)
        check("...and says the auto waiver removes the stop, never the record",
              "never the record" in out, out)

        rec = record()
        rec["content"]["slides"] = rec["content"]["slides"][:2]
        rc, out = gate(deck, rec)
        check("a plan that stops short of the deck is refused",
              rc != 0 and "every final slide exactly once" in out, out)

        rec = record()
        rec["content"]["slides"][1]["takeaway"] = "背景"
        rc, out = gate(deck, rec)
        check("a TOPIC in the takeaway column is refused",
              rc != 0 and "not what it SAYS" in out, out)

        rec = record()
        rec["content"]["slides"][1]["evidence"] = ["见来源"]
        rc, out = gate(deck, rec)
        check("a stub in the 承载证据 column is refused",
              rc != 0 and "SOURCE TRACE" in out, out)

        rec = record()
        rec["content"]["slides"][1]["takeaway"] = rec["content"]["slides"][2]["takeaway"]
        rc, out = gate(deck, rec)
        check("two content slides with ONE memory sentence is refused",
              rc != 0 and "SAME takeaway" in out, out)

        rec = record()
        rec["content"]["slides"][0]["role"] = "cover"
        rec["content"]["slides"][0]["takeaway"] = rec["content"]["slides"][2]["takeaway"]
        rc, out = gate(deck, rec)
        check("...but a COVER may restate the deck's one sentence", rc == 0, out)

        rec = record()
        rec["content"]["slides"][1]["units"] = 9
        rec["content"]["slides"][1]["role"] = "evidence"
        rc, out = gate(deck, rec)
        check("a dense row is REPORTED, never fatal", rc == 0 and "units>=6" in out, out)

        rec = record()
        rec["content"]["slides_waived"] = "三页 CI 夹具，没有可分页的论证"
        rec["content"].pop("slides")
        rec["content"]["checkpoint"]["mode"] = "auto"
        rc, out = gate(deck, rec)
        check("a written waiver is honoured", rc == 0 and "WAIVED" in out, out)
        rec["content"]["slides_waived"] = "无"
        rc, out = gate(deck, rec)
        check("...but a token is not a waiver", rc != 0, out)

        print("== delegation is visible at delivery ==")
        rec = record()
        rec["content"].pop("checkpoint")
        rc, out = gate(deck, rec)
        check("a missing checkpoint record blocks", rc != 0, out)
        check("...and the message refuses to offer a third value",
              "no third one" in out and "WHO approves" in out, out)

        rec = record()
        rec["content"]["checkpoint"] = {"mode": "skipped", "record": "never posted it"}
        rc, out = gate(deck, rec)
        check("`skipped` is not a mode a run may claim", rc != 0, out)

        rec = record()
        rec["content"]["checkpoint"] = {"mode": "auto", "record": "x"}
        rc, out = gate(deck, rec)
        check("a mode with no record is not a record", rc != 0, out)

        rec = record()
        rec["content"]["checkpoint"]["mode"] = "auto"
        rec["design_plan"]["checkpoint"]["mode"] = "auto"
        rc, out = gate(deck, rec)
        check("both FYIs pass under the auto waiver", rc == 0, out)
        check("...and the ledger prints WHICH mode each was",
              "checkpoint ledger" in out and "content: auto" in out
              and "design: auto" in out, out)
        check("...next to whether the artifact is actually there",
              "slides x3" in out and "design_plan" in out, out)

        rec = record()
        rec["content"]["slides_waived"] = "三页 CI 夹具，没有可分页的论证"
        # `approved` over a waived table is ODD, not wrong: the checkpoint carries more than the
        # table, so the user may have approved the rest of it. Noted on the ledger, never blocking.
        rec["content"].pop("slides")
        rc, out = gate(deck, rec)
        check("`approved` over a WAIVED artifact is NOTED, not blocked",
              rc == 0 and "over a WAIVED artifact" in out, out)

    print("== the two gates hold the same bar (they have drifted twice before) ==")
    src_render = (SKILL / "scripts" / "render_deck.py").read_text(encoding="utf-8")
    src_codex = CODEX.read_text(encoding="utf-8")
    for field in ("content.arc.candidates", "divergence_justified"):
        check(f"both gates name {field}", field in src_render and field in src_codex)
    check("both recompute with arc_divergence rather than reading a verdict",
          "arc_divergence" in src_render and "load_arc_checker" in src_codex)
    check("neither still requires the old free-text `divergence` string",
          'require_string(arc.get("divergence")' not in src_codex)
    check("both exempt the same structural roles from the takeaway-uniqueness rule",
          "STRUCTURAL_ROLES" in src_codex and "_STRUCTURAL_ROLES" in src_render)
    check("the structural vocabularies are identical",
          sorted(RD._STRUCTURAL_ROLES) == sorted(_codex_structural(src_codex)))

    print("== the recomputation is the SAME code the CLI runs ==")
    v = RD._arc_verdict(copy.deepcopy(ARC_CANDIDATES))
    check("gate-time check() returns arc_divergence's own verdict shape",
          set(v) >= {"pairs", "flagged", "sketches", "no_ledger"})
    check("...and agrees with calling the module directly",
          v == arc_divergence.check(copy.deepcopy(ARC_CANDIDATES)))

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


def _codex_structural(src):
    """Read the codex gate's STRUCTURAL_ROLES literal out of its source.

    Imported by AST rather than by running the module, because codex_delivery_gate.py is a CLI
    whose import surface is heavier than this one comparison needs.
    """
    import ast
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "STRUCTURAL_ROLES" for t in node.targets):
            return list(ast.literal_eval(node.value.args[0]))
    return []


if __name__ == "__main__":
    raise SystemExit(main())
