#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""""The tests all pass" has never meant "the skill got better", and now something says which.

Every one of the 20 suites here asks whether the CODE works. None asks whether 2109 lines of
SKILL.md, 35 references and 5 agents make the DECK better — so every claim that a change improved
the skill has been an impression. CLAUDE.md states the failure exactly: a lossless refactor can
score 2298/2298 and still degrade the skill, because the regression is in WHEN content reaches
context, not whether it survives. It has bitten twice for real — a refactor whose next live run
read 3 of 10 reference files and shipped zero icons while every gate passed, and an opt-in check
that reported 0 findings on the deck whose defect motivated it.

`run_eval.py` is the instrument. THIS suite tests the instrument, because an eval harness that
scores wrong is worse than none: it launders a bad build into a number.

The split under test is the design: `--score` reads an already-built deck and decides in ~1s with
no model and no network, which is why it can live in CI at all; producing the deck is the other
half and never runs here. Assertions are only things a program can be wrong about in one
direction — no taste, no LLM judge, no aesthetic composite (both were examined against the
published benchmarks and rejected: similarity scoring rewards imitation, closed-form beauty scores
fight this skill's own diversity rules).

🔴 The load-bearing case is `skip is not pass`. `reference_reached` — the one assertion that
answers "was that file actually READ", the exact hole that burned this repo twice — cannot be
decided without a transcript, and a harness that quietly counted it as passing would re-create the
blindness it exists to remove.

Run:  python3 tests/test_run_eval.py
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                                                  # noqa: E402
import run_eval                                                       # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def known_kinds():
    """Every assertion kind `run_eval.check()` actually implements, read out of its source.

    Collects the string on the right of every `kind == "..."` test inside check(). Deriving it
    means a kind can never be "known" to this suite without a branch existing that decides it.
    """
    import ast
    tree = ast.parse((SCRIPTS / "run_eval.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "check")
    out = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name):
            continue
        if node.left.id != "kind" or not isinstance(node.ops[0], ast.Eq):
            continue
        rhs = node.comparators[0]
        if isinstance(rhs, ast.Constant) and isinstance(rhs.value, str):
            out.add(rhs.value)
    return out


def make_deck(d, *, slides=3, numbers=("2.1", "0.94"), notes=True, gates=None,
              residue=None, broken=False):
    """A minimal but REAL deck: built by deckkit, saved, scoreable like any other."""
    dk.FONT, dk.EAFONT = "Helvetica Neue", "Hiragino Sans GB"
    prs = dk.blank_deck()
    for i in range(slides):
        s = dk.add_slide(prs)
        dk.box(s, 0, 0, 10, 5.625, fill=dk.RGBColor(0xFF, 0xFF, 0xFF))
        body = "PSNR +%s dB and SSIM %s" % numbers if i == 0 else "A supporting point."
        if residue and i == 1:
            body = residue
        dk.text(s, 0.6, 1.4, 8.8, 0.5,
                [[(body, 14, dk.DEEP, False, False, "Helvetica Neue")]], space_after=0)
        if broken and i == 0:
            # text ink far off the canvas — a hard finding the lint must report
            dk.text(s, 9.4, 1.0, 4.0, 0.4,
                    [[("this runs off the right edge of the slide", 14, dk.DEEP,
                       False, False, "Helvetica Neue")]], space_after=0, wrap=False)
        if notes:
            dk.speaker_notes(s, "A spoken paragraph long enough to count as real narration here.")
    out = os.path.join(d, "deck.pptx")
    prs.save(out)
    if gates is not None:
        with open(os.path.join(d, ".deck-gates.json"), "w", encoding="utf-8") as fh:
            json.dump(gates, fh)
    return out


def rows_of(deck_dir, assertions, transcript=None):
    ev = {"id": "t", "assertions": assertions}
    return {r["kind"]: r for r in run_eval.score(deck_dir, ev, transcript)}


def main():
    print("run_eval")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ev_"))
    try:
        # ---- the shipped evals file must itself be usable ---------------------------------
        evals = run_eval.load_evals()
        check("evals.json parses and is non-empty", bool(evals), evals)
        ids = [e["id"] for e in evals]
        check("every eval has a unique id", len(ids) == len(set(ids)), ids)
        check("every eval carries at least one assertion",
              all(e.get("assertions") for e in evals))
        # DERIVED from run_eval.check() by AST, not retyped here. It was a hand-kept literal set,
        # which is the same drift this repo has already paid for elsewhere (a gate's own printed
        # template listed six of the eight fields it enforced). A hand-kept mirror of a function's
        # branches fails in the direction that hurts: a NEW assertion kind reads as "the scorer
        # cannot decide this" and the obvious fix is to append a string to the list — at which
        # point the check is asserting that a name appears in two places, not that the scorer
        # implements it.
        known = known_kinds()
        check("the decidable-kind set is derived from check(), not a hand-kept list",
              len(known) >= 9, sorted(known))
        unknown = sorted({a["kind"] for e in evals for a in e["assertions"]} - known)
        check("no eval names an assertion the scorer cannot decide", not unknown, unknown)

        # ---- a good deck ------------------------------------------------------------------
        good = tmp / "good"
        good.mkdir()
        make_deck(str(good), gates={"critic": {"verdict": "consent"}, "design_plan": {},
                                    "delivery": "presented"})
        r = rows_of(str(good), [
            {"kind": "pptx_exists"},
            {"kind": "slides_between", "lo": 2, "hi": 6},
            {"kind": "lint_hard_clean"},
            {"kind": "gates_present", "keys": ["critic", "design_plan"]},
            {"kind": "text_contains", "values": ["2.1", "0.94"]},
            {"kind": "text_absent", "values": ["placeholder", "TODO"]},
            {"kind": "notes_coverage", "min_share": 0.8},
        ])
        for k in r:
            check("a sound deck passes %s" % k, r[k]["ok"] is True, r[k]["detail"])

        # ---- and each assertion FAILS on the thing it is for -------------------------------
        empty = tmp / "empty"
        empty.mkdir()
        r = rows_of(str(empty), [{"kind": "pptx_exists"}])
        check("no .pptx fails pptx_exists", r["pptx_exists"]["ok"] is False)

        r = rows_of(str(good), [{"kind": "slides_between", "lo": 8, "hi": 12}])
        check("a deck outside the slide range fails", r["slides_between"]["ok"] is False)

        nog = tmp / "nogates"
        nog.mkdir()
        make_deck(str(nog))
        r = rows_of(str(nog), [{"kind": "gates_present", "keys": ["critic"]}])
        check("a missing .deck-gates.json fails gates_present", r["gates_present"]["ok"] is False)
        check("...and says the evidence file was never written",
              "never written" in r["gates_present"]["detail"], r["gates_present"]["detail"])

        partial = tmp / "partial"
        partial.mkdir()
        make_deck(str(partial), gates={"delivery": "presented"})
        r = rows_of(str(partial), [{"kind": "gates_present", "keys": ["critic", "design_plan"]}])
        check("a gates file missing BLOCKS fails, and names them",
              r["gates_present"]["ok"] is False
              and "critic" in r["gates_present"]["detail"], r["gates_present"]["detail"])

        r = rows_of(str(good), [{"kind": "text_contains", "values": ["3.7"]}])
        check("a number the deck never printed fails text_contains",
              r["text_contains"]["ok"] is False)

        res = tmp / "residue"
        res.mkdir()
        make_deck(str(res), residue="TODO: fill this in")
        r = rows_of(str(res), [{"kind": "text_absent", "values": ["TODO"]}])
        check("build residue on a slide fails text_absent", r["text_absent"]["ok"] is False)

        nonotes = tmp / "nonotes"
        nonotes.mkdir()
        make_deck(str(nonotes), notes=False)
        r = rows_of(str(nonotes), [{"kind": "notes_coverage", "min_share": 0.8}])
        check("a presented deck with empty notes fails notes_coverage",
              r["notes_coverage"]["ok"] is False)

        bad = tmp / "broken"
        bad.mkdir()
        make_deck(str(bad), broken=True)
        r = rows_of(str(bad), [{"kind": "lint_hard_clean"}])
        check("a deck with a hard lint finding fails lint_hard_clean",
              r["lint_hard_clean"]["ok"] is False, r["lint_hard_clean"]["detail"])

        # ---- the fidelity assertion: an invented number is the whole point -----------------
        r = rows_of(str(good), [{"kind": "no_unsourced_numbers", "allow": ["2.1", "0.94"]}])
        check("a deck printing only the supplied numbers passes no_unsourced_numbers",
              r["no_unsourced_numbers"]["ok"] is True, r["no_unsourced_numbers"]["detail"])
        r = rows_of(str(good), [{"kind": "no_unsourced_numbers", "allow": ["2.1"]}])
        check("...and a figure outside the allowlist fails it",
              r["no_unsourced_numbers"]["ok"] is False, r["no_unsourced_numbers"]["detail"])

        # ---- 🔴 skip is not pass ------------------------------------------------------------
        r = rows_of(str(good), [{"kind": "reference_reached",
                                 "paths": ["references/design-principles.md"]}])
        check("reference_reached with NO transcript is skipped, never passed",
              r["reference_reached"]["ok"] is None, r["reference_reached"]["ok"])
        check("...and says only a transcript can answer it",
              "transcript" in r["reference_reached"]["detail"])

        tr = tmp / "run.jsonl"
        tr.write_text("opened references/design-principles.md and read it\n", encoding="utf-8")
        r = rows_of(str(good), [{"kind": "reference_reached",
                                 "paths": ["references/design-principles.md"]}], str(tr))
        check("a transcript that shows the read passes", r["reference_reached"]["ok"] is True)
        r = rows_of(str(good), [{"kind": "reference_reached",
                                 "paths": ["references/icons.md"]}], str(tr))
        check("a transcript that does NOT show the read fails — the twice-burned hole",
              r["reference_reached"]["ok"] is False, r["reference_reached"]["detail"])

        # ---- an assertion that crashes is a FAIL, never a silent pass ----------------------
        r = rows_of(str(good), [{"kind": "slides_between"}])          # missing lo/hi
        check("a malformed assertion FAILS rather than passing quietly",
              r["slides_between"]["ok"] is False, r["slides_between"]["detail"])

        # ---- the three BLIND-SPOT assertions ------------------------------------------------
        # Each was added with a scenario that targets a defect class this repo has shipped and
        # every existing gate passed clean. An assertion with no test of its own is the exact
        # trap that has already bitten twice here: the check runs, decides nothing, and the suite
        # stays green. Both directions are pinned for all three.

        # canvas_is — nothing before this ever read the slide size, so a pipeline that silently
        # builds 16:9 and calls it a portrait card passed every eval in the file.
        port = tmp / "portrait"
        port.mkdir()
        dk.FONT, dk.EAFONT = "Helvetica Neue", "Hiragino Sans GB"
        prs = dk.blank_deck(7.5, 10.0)
        s = dk.add_slide(prs)
        dk.text(s, 0.5, 1.0, 6.5, 0.6,
                [[("为什么要加速采集", 24, dk.DEEP, True, False, "Hiragino Sans GB")]],
                space_after=0)
        prs.save(str(port / "deck.pptx"))
        r = rows_of(str(port), [{"kind": "canvas_is", "w_in": 7.5, "h_in": 10.0}])
        check("canvas_is passes on the portrait canvas it names",
              r["canvas_is"]["ok"] is True, r["canvas_is"]["detail"])
        r = rows_of(str(port), [{"kind": "canvas_is", "w_in": 10.0, "h_in": 5.625}])
        check("canvas_is FAILS when the deck is not the canvas the scenario asked for",
              r["canvas_is"]["ok"] is False, r["canvas_is"]["detail"])

        # cjk_runs_have_ea_face — the deck above set EAFONT, so it is the passing case.
        r = rows_of(str(port), [{"kind": "cjk_runs_have_ea_face"}])
        check("cjk_runs_have_ea_face passes when CJK runs declare an <a:ea> face",
              r["cjk_runs_have_ea_face"]["ok"] is True, r["cjk_runs_have_ea_face"]["detail"])

        noea = tmp / "noea"
        noea.mkdir()
        dk.EAFONT = None                      # the real failure: only <a:latin> reaches the run
        prs = dk.blank_deck()
        s = dk.add_slide(prs)
        dk.text(s, 0.6, 1.0, 8.8, 0.6,
                [[("心脏磁共振加速采集", 24, dk.DEEP, True, False, "Helvetica Neue")]],
                space_after=0)
        prs.save(str(noea / "deck.pptx"))
        dk.EAFONT = "Hiragino Sans GB"
        r = rows_of(str(noea), [{"kind": "cjk_runs_have_ea_face"}])
        check("cjk_runs_have_ea_face FAILS when Chinese text carries only a Latin face — the "
              "asymmetry that already cost this repo a 46%-wrong width measurement",
              r["cjk_runs_have_ea_face"]["ok"] is False, r["cjk_runs_have_ea_face"]["detail"])
        r = rows_of(str(good), [{"kind": "cjk_runs_have_ea_face"}])
        check("…and a deck with no CJK at all passes rather than being punished for it",
              r["cjk_runs_have_ea_face"]["ok"] is True, r["cjk_runs_have_ea_face"]["detail"])

        # no_signed_native_bars — the defect class with no gate anywhere in this repo.
        def chart_deck(dest, values, kind="column"):
            dest.mkdir()
            prs = dk.blank_deck()
            s = dk.add_slide(prs)
            dk.native_chart(s, 0.8, 1.0, 8.0, 3.6, ["Cloud", "Services", "Hardware"],
                            [("YoY %", values)], kind=kind)
            prs.save(str(dest / "deck.pptx"))
            return dest

        neg = chart_deck(tmp / "negbar", [18.2, 4.6, -11.9])
        r = rows_of(str(neg), [{"kind": "no_signed_native_bars"}])
        check("no_signed_native_bars FAILS on a native column chart carrying a negative value — "
              "LibreOffice draws it at absolute height, so the .pptx is right and the render "
              "silently points the wrong way",
              r["no_signed_native_bars"]["ok"] is False, r["no_signed_native_bars"]["detail"])

        pos = chart_deck(tmp / "posbar", [18.2, 4.6, 11.9])
        r = rows_of(str(pos), [{"kind": "no_signed_native_bars"}])
        check("…and passes on the same chart with no negative value",
              r["no_signed_native_bars"]["ok"] is True, r["no_signed_native_bars"]["detail"])

        line = chart_deck(tmp / "negline", [18.2, 4.6, -11.9], kind="line")
        r = rows_of(str(line), [{"kind": "no_signed_native_bars"}])
        check("…and a LINE chart with the same negative value passes — line and scatter render "
              "signed data correctly, and flagging them would route working charts through a "
              "workaround they do not need",
              r["no_signed_native_bars"]["ok"] is True, r["no_signed_native_bars"]["detail"])

        r = rows_of(str(good), [{"kind": "no_signed_native_bars"}])
        check("…and a deck with no native chart at all passes",
              r["no_signed_native_bars"]["ok"] is True, r["no_signed_native_bars"]["detail"])

        # ---- exit codes: the only thing CI reads -------------------------------------------
        def run(deck, ev_id):
            return subprocess.run([sys.executable, str(SCRIPTS / "run_eval.py"),
                                   "--score", deck, "--eval", ev_id],
                                  capture_output=True, text=True).returncode
        check("--list exits 0",
              subprocess.run([sys.executable, str(SCRIPTS / "run_eval.py"), "--list"],
                             capture_output=True, text=True).returncode == 0)
        check("an unknown --eval exits 2 (could-not-run, never 'clean')",
              run(str(good), "no-such-eval") == 2)
        check("a deck missing its pptx exits 1", run(str(empty), evals[0]["id"]) == 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
