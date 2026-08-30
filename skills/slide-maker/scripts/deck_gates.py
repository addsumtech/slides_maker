#!/usr/bin/env python3
"""Write and shape-check `.deck-gates.json` — the record every hand-off gate reads.

Every other expensive artifact in this pipeline has an emitter: the critic brief has
`dispatch_brief.py init`, the review contract has `validate_review.py --schema`, the consent
record has `--record`. The design plan block did not, so it was hand-typed JSON whose field
SHAPES were discoverable only by failing the gate — and the gate stops at the first problem in a
section, by a deliberate and tested contract ("its later checks read values the earlier one
validated"). Measured on one real build: **six consecutive `--gate-check` runs**, each naming
exactly one field — `boldness` in the wrong dial format, then `signature_proof`, then
`material_probe`, then `concept` in the wrong shape, then `type_scale.body` under the floor, then
`form_reach`. Six full context re-sends to learn six facts that were knowable up front.

This does not change the gate. It puts the shapes where they can be read BEFORE the run:

    python3 scripts/deck_gates.py init  <deck-dir> [--slides N] [--delivery presented]
    python3 scripts/deck_gates.py check <deck-dir>          # ALL shape problems at once
    python3 scripts/deck_gates.py set   <deck-dir> design_plan.boldness bold
    python3 scripts/deck_gates.py set   <deck-dir> design_plan.carried_by '[4, 6, 13]'
    python3 scripts/deck_gates.py --selftest

🔴 It writes the SHARED record, `.deck-gates.json` — the one `render_deck.py --gate-check` and
`lint_deck.py` read on every runtime. The Codex delivery path ALSO keeps `.codex-deck-evidence.json`,
a different schema owned by `codex_delivery_gate.py`; this tool neither writes nor validates that
one, and running it does not excuse producing it (`references/codex-runtime.md` step 3a).

🔴 `check` is a SHAPE pre-flight, not the gate. It never opens the .pptx, so it cannot know
whether the anchor PNGs render, whether the register was applied, whether the credits reached a
slide, or whether the deck is too same. `render_deck.py --gate-check` remains the authority and
must still be run — this only stops you from spending round-trips on typos and wrong shapes.

Exit 0 clean · 1 problems · 2 could not run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

GATES = ".deck-gates.json"

DIALS = ("conservative", "balanced+", "bold", "experimental")
DELIVERIES = ("presented", "textheavy", "selfread", "surface")

# The interview axes that must be RECORDED, and the reason they are a list rather than prose.
# Measured on a real delivered deck: `.deck-gates.json` carried `delivery`, `builds` and
# `content.slides` and none of these four. The three that survived are exactly the three something
# downstream demanded (declare_delivery, the motion manifest, the content gate); the ones that
# evaporated are the ones nothing asked for. LANGUAGE went unasked on that build and no artifact,
# lint or gate noticed. There is a mechanical half as well: the interview is five questions and a
# choice UI takes FOUR per call, so "ask them in one batched call" silently truncates the fifth —
# which is the line language lives on. `length` was already required on the codex path for exactly
# this reason, one axis at a time; this is that lesson applied to the rest of them.
# ONE definition, read by `render_deck --gate-check` and by `codex_delivery_gate` — a second copy is
# how the two gates have already drifted apart twice.
INTERVIEW_AXES = ("language", "density", "length", "goal")
INTERVIEW_HINT = {
    "language": "中文 / English / bilingual EN+中文",
    "density": "diagram-heavy / balanced / text-heavy",
    "length": "the slide count or range the USER saw",
    "goal": "inform / support a decision / inspire action",
}
ANCHOR_ROLES = ("signature", "complex", "data")
# The body floors render_deck.py enforces, restated here ONLY to warn early. The gate owns them.
BODY_FLOORS = {"presented": 13.5, "textheavy": 12.0, "selfread": 12.0}


def template(slides=None, delivery="presented"):
    """A fully-SHAPED skeleton. Every value is a placeholder that `check` will reject, so an
    unfilled template can never be mistaken for a filled one."""
    n = slides or 0
    return {
        # The interview's answers, scaffolded so they cannot be forgotten: a capability that does
        # not enter the skeleton is one the next deck rediscovers by failing a gate.
        "interview": {k: "<{}>".format(INTERVIEW_HINT[k]) for k in INTERVIEW_AXES},
        "delivery": delivery,
        "content": {
            "slides": [{"slide": i + 1, "role": "<cover|hook|evidence|framework|…>",
                        "takeaway": "<the sentence a reader should leave with>",
                        "evidence": ["<a locator: fig / p.4 ¶2 / a verbatim span>"], "units": 3}
                       for i in range(n)] or
                      [{"slide": 1, "role": "<role>", "takeaway": "<takeaway>",
                        "evidence": ["<locator>"], "units": 3}],
            "checkpoint": {"mode": "<approved|auto>", "record": "<how it was delivered>"},
            "arc": {
                "candidates": [{"name": "<arc name>", "shape": "<evidence-build|…>",
                                "opening_roles": ["<role>", "<role>", "<role>"],
                                "audience_question": "<what the room is asking>",
                                "objection": "<what it pre-empts>", "ask": "<the closing ask>",
                                "evidence": ["<ledger id>"]}],
                "chosen": "<the winner>",
                "rejected": [{"name": "<loser>", "why_lost": "<one clause>"}],
                "divergence": "<ok|flagged … → rediverged|justified: …>"},
        },
        "design_plan": {
            "concept": {"chosen": "<what this deck is a PICTURE of — via <core concepts> → "
                                  "<visual language>>",
                        "rejected": [{"concept": "<the runner-up>", "why_lost": "<one clause>"},
                                     {"concept": "<the other>", "why_lost": "<one clause>"}]},
            "boldness": "<%s>" % "|".join(DIALS),
            "boldness_derivation": "<explicit request | taste.md dial | purpose>",
            "signature_move": "<the ONE scoped aesthetic risk, and where it lands>",
            "carried_by": ["<slide n>", "<slide m>"],
            "form_ledger": "<per-family tally + the largest family's share>",
            "icon_family": "<family, recoloured — or 'none' + the classified reason>",
            "palette": "<the FILL-only vs TEXT-safe split, per palette_audit.py>",
            "type_scale": {"display": 40, "title": 22, "body": 14},
            "style_pick": "<preset|bespoke> for <domain> · beat <rival> because <clause> · "
                          "anti-pick avoided: <the domain cliché>",
            "motif_generates": {"background": "<what the motif makes the canvas do>",
                                "markers": "<the numeral/icon/bullet system it implies>",
                                "page": "<the slide whose GEOMETRY is the motif | none — reason>"},
            "image_sources": ["slide <n> | <subject> | sourced — <origin> (<licence>)",
                              "slide <n> | <subject> | generated — <tool>"],
            "material_probe": {"png": "render/slideNN.png",
                               "safe_version": "<what the DEFAULT version of this page would have "
                                               "been — if it is about the same thing, the register "
                                               "is a look, not a move>"},
            "signature_proof": [{"role": r, "slide": 0, "png": "render/slideNN.png"}
                                for r in ANCHOR_ROLES],
            "direction_gate": {"verdict": "<the directions_diversity.py verdict>",
                               "picked": "<the direction the user chose>",
                               "candidates": "<path to directions.json>"},
            "build_shape": "<fanout — <n> sections | solo — <reason>>",
            "checkpoint": {"mode": "<approved|auto>", "record": "<how it was delivered>"},
        },
        "critic": {"verdict": "<consent|revise>", "rounds": 1,
                   "source": "<path to the recorded review>", "sha256": "<its hash>"},
        "provenance": {"claims": [{"claim": "<the claim>", "verdict": "<CONFIRMED|WRONG|…>",
                                   "source": "<primary URL>"}]},
        "render_selfcheck": {"slides": [{"n": i + 1, "verdict": "<ok — … | … fixed>"}
                                        for i in range(n)] or
                                       [{"n": 1, "verdict": "<ok — …>"}]},
    }


# --------------------------------------------------------------------------- shape checking

def _ph(v):
    """Is this still a placeholder? Placeholders are the template's own <…> markers."""
    return isinstance(v, str) and v.strip().startswith("<") and v.strip().endswith(">")


def _need(d, path, problems, kind=None, why=""):
    cur, walked = d, []
    for part in path.split("."):
        walked.append(part)
        if not isinstance(cur, dict) or part not in cur:
            problems.append("`{}` is missing.{}".format(".".join(walked), why and " " + why))
            return None
        cur = cur[part]
    if _ph(cur):
        problems.append("`{}` is still the template placeholder {!r} — fill it.".format(path, cur))
        return None
    if kind is not None and not isinstance(cur, kind):
        problems.append("`{}` must be {}, got {}.".format(
            path, getattr(kind, "__name__", kind), type(cur).__name__))
        return None
    return cur


def check(gates):
    """EVERY shape problem, in one pass. Deliberately independent checks — this is the half the
    render gate cannot batch, because there each later check reads what an earlier one validated."""
    problems = []
    d = gates.get("design_plan")
    if not isinstance(d, dict):
        return ["`design_plan` is missing — run `deck_gates.py init <deck-dir>` first."]
    if d.get("waived"):
        return []

    dial = _need(gates, "design_plan.boldness", problems, str)
    if dial is not None and dial not in DIALS:
        problems.append("`design_plan.boldness` is {!r}, which is not a dial. One of: {}. (Put the "
                        "REASON in `boldness_derivation` — the gate tests this field for equality, "
                        "so 'bold — because …' reads as not-a-dial.)".format(dial, " | ".join(DIALS)))

    concept = _need(gates, "design_plan.concept", problems)
    if isinstance(concept, str):
        problems.append("`design_plan.concept` is a string; the gate wants the COMPETITION: "
                        '{"chosen": "…", "rejected": [{"concept": "…", "why_lost": "…"}, {…}]}.')
    elif isinstance(concept, dict):
        if not concept.get("chosen") or _ph(concept.get("chosen")):
            problems.append("`design_plan.concept.chosen` is empty or a placeholder.")
        rej = concept.get("rejected") or []
        if len(rej) < 2:
            problems.append("`design_plan.concept.rejected` needs TWO beaten pictures — one "
                            "alternative is not a choice.")
        for i, r in enumerate(rej):
            if not isinstance(r, dict) or not r.get("why_lost") or _ph(r.get("why_lost")):
                problems.append("`design_plan.concept.rejected[{}]` needs a `why_lost` clause."
                                .format(i))

    probe = _need(gates, "design_plan.material_probe", problems, dict,
                  why="Step 2 opens by BUILDING one real slide and looking at it.")
    if isinstance(probe, dict):
        for k in ("png", "safe_version"):
            if not probe.get(k) or _ph(probe.get(k)):
                problems.append("`design_plan.material_probe.{}` is empty or a placeholder."
                                .format(k))

    proof = _need(gates, "design_plan.signature_proof", problems, list)
    if isinstance(proof, list):
        roles = [p.get("role") for p in proof if isinstance(p, dict)]
        for r in ANCHOR_ROLES:
            if r not in roles:
                problems.append("`design_plan.signature_proof` has no {!r} anchor — the three are "
                                "{}.".format(r, ", ".join(ANCHOR_ROLES)))
        for i, p in enumerate(proof):
            if not isinstance(p, dict) or not p.get("png") or _ph(p.get("png")) \
                    or not isinstance(p.get("slide"), int) or p.get("slide", 0) < 1:
                problems.append("`design_plan.signature_proof[{}]` needs {{role, slide (int>=1), "
                                "png}}.".format(i))

    scale = _need(gates, "design_plan.type_scale", problems, dict)
    if isinstance(scale, dict):
        if not all(isinstance(scale.get(k), (int, float)) for k in ("display", "title", "body")):
            problems.append("`design_plan.type_scale` must resolve display/title/body as NUMBERS.")
        else:
            if not (scale["display"] > scale["title"] > scale["body"]):
                problems.append("`design_plan.type_scale` is not a scale: display {} > title {} > "
                                "body {} must hold.".format(scale["display"], scale["title"],
                                                            scale["body"]))
            mode = str(gates.get("delivery") or "presented")
            floor = BODY_FLOORS.get("selfread" if mode == "surface" else mode, 13.5)
            if scale["body"] < floor:
                problems.append("`design_plan.type_scale.body` is {}pt, under the {}pt floor for a "
                                "{} deck — a legibility floor, not a style choice."
                                .format(scale["body"], floor, mode))

    carried = _need(gates, "design_plan.carried_by", problems, list)
    if isinstance(carried, list) and len(carried) < 2:
        problems.append("`design_plan.carried_by` must name at least 2 slides — one brave slide "
                        "among nineteen safe ones is a tonal break, not a position.")

    for f in ("signature_move", "form_ledger", "icon_family", "palette", "style_pick",
              "build_shape", "image_sources", "motif_generates"):
        _need(gates, "design_plan." + f, problems)

    cp = _need(gates, "design_plan.checkpoint", problems, dict)
    if isinstance(cp, dict) and cp.get("mode") not in ("approved", "auto"):
        problems.append("`design_plan.checkpoint.mode` must be 'approved' or 'auto'.")

    if "critic" not in gates:
        problems.append("`critic` is missing — either the recorded consent (written by "
                        "`validate_review.py … --record`) or a CLASSIFIED waiver.")
    elif gates["critic"].get("waived") and not gates["critic"].get("waived_category"):
        problems.append("`critic.waived` needs a `waived_category` — an unclassified waiver is "
                        "indistinguishable from never having run the loop.")

    sc = gates.get("render_selfcheck", {}).get("slides")
    if not sc and not gates.get("render_selfcheck", {}).get("waived"):
        problems.append("`render_selfcheck.slides` is missing — one verdict per slide; a slide "
                        "with no line was not looked at.")
    return problems


# --------------------------------------------------------------------------- CLI

def _path(deck_dir):
    return Path(os.path.expanduser(deck_dir)) / GATES


def _load(deck_dir):
    p = _path(deck_dir)
    if not p.exists():
        print("no {} at {} — run `deck_gates.py init {}` first".format(GATES, p.parent, deck_dir),
              file=sys.stderr)
        raise SystemExit(2)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        print("{} is not valid JSON: {}".format(p, exc), file=sys.stderr)
        raise SystemExit(2)


def _save(deck_dir, g):
    p = _path(deck_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(g, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def _cmd_init(a):
    p = _path(a.deck_dir)
    if p.exists() and not a.force:
        print("{} already exists — pass --force to overwrite (this DISCARDS what is recorded)"
              .format(p), file=sys.stderr)
        return 2
    g = template(a.slides, a.delivery)
    _save(a.deck_dir, g)
    print("wrote {}".format(p))
    print("every value is a placeholder; `deck_gates.py check {}` lists what is still unfilled."
          .format(a.deck_dir))
    return 0


def _cmd_set(a):
    g = _load(a.deck_dir)
    try:
        val = json.loads(a.value)
    except ValueError:
        val = a.value
    cur = g
    parts = a.path.split(".")
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            print("cannot descend into {!r}: it is not an object".format(part), file=sys.stderr)
            return 2
    cur[parts[-1]] = val
    _save(a.deck_dir, g)
    print("set {} = {}".format(a.path, json.dumps(val, ensure_ascii=False)[:90]))
    return 0


def _cmd_check(a):
    probs = check(_load(a.deck_dir))
    if not probs:
        print("shape clean — {} carries every field the design gate reads, in the right shape."
              .format(GATES))
        print("🔴 NOT the gate: run `render_deck.py <deck>.pptx --gate-check` for the checks that "
              "need the built deck (anchors render, register applied, credits on a slide, "
              "sameness, density).")
        return 0
    print("{} shape problem(s) — ALL of them, so one pass fixes the lot:\n".format(len(probs)))
    for i, m in enumerate(probs, 1):
        print("  [{}] {}\n".format(i, m))
    return 1


def _selftest():
    ok, bad = [], []
    t = template(3)
    probs = check(t)
    if probs:
        ok.append("a FRESH template fails its own check ({} problems) — an unfilled skeleton can "
                  "never be mistaken for a filled one".format(len(probs)))
    else:
        bad.append("the template passed check() — placeholders are not being detected")

    g = template(3)
    d = g["design_plan"]
    d["boldness"] = "bold"
    d["concept"] = {"chosen": "a red line that gets crossed",
                    "rejected": [{"concept": "a deepfake face", "why_lost": "spectacle, not decision"},
                                 {"concept": "a magnifier", "why_lost": "the stock image of verifying"}]}
    d["signature_move"] = "the best plate is filed on the wrong side of the deck's own line"
    d["carried_by"] = [4, 6, 13]
    d["form_ledger"] = "seam 2 · editorial 3 · ledger 1 — largest 23%"
    d["icon_family"] = "tabler, recoloured"
    d["palette"] = "FILL #33FF66 / TEXT #C8F0C8"
    d["style_pick"] = "terminal for a CLI subject · beat swiss · anti-pick avoided: neon"
    d["build_shape"] = "solo — one tightly-coupled argument"
    d["image_sources"] = ["slide 3 | the reference | sourced — Commons (CC BY-SA 4.0)"]
    d["motif_generates"] = {"background": "a step rail", "markers": "+ / x / ?", "page": "slide 13"}
    d["material_probe"] = {"png": "render/slide04.png", "safe_version": "two captioned pictures"}
    d["signature_proof"] = [{"role": r, "slide": i + 4, "png": "render/slide%02d.png" % (i + 4)}
                            for i, r in enumerate(ANCHOR_ROLES)]
    d["checkpoint"] = {"mode": "approved", "record": "posted in chat"}
    g["critic"] = {"waived": "user declined with the deck visible", "waived_category": "user-waived"}
    g["render_selfcheck"] = {"slides": [{"n": i + 1, "verdict": "ok"} for i in range(3)]}
    probs = check(g)
    if not probs:
        ok.append("a fully-filled record passes")
    else:
        bad.append("a filled record still fails: {}".format(probs))

    g2 = json.loads(json.dumps(g))
    g2["design_plan"]["boldness"] = "bold — because it is a launch"
    g2["design_plan"].pop("material_probe")
    g2["design_plan"]["concept"] = "a red line"
    g2["design_plan"]["type_scale"]["body"] = 12
    probs = check(g2)
    kinds = {("boldness" in p, "material_probe" in p, "concept" in p, "type_scale" in p)
             for p in probs}
    hit = {"boldness": any("boldness" in p for p in probs),
           "material_probe": any("material_probe" in p for p in probs),
           "concept": any("concept" in p for p in probs),
           "type_scale": any("type_scale.body" in p for p in probs)}
    if all(hit.values()):
        ok.append("FOUR independent field faults are reported in ONE pass — the exact six-round-"
                  "trip sequence this file exists to collapse ({} problems)".format(len(probs)))
    else:
        bad.append("independent faults not batched: {}".format(hit))

    g3 = json.loads(json.dumps(g))
    g3["design_plan"]["waived"] = "a 2-slide tiny ask"
    if check(g3) == []:
        ok.append("a WAIVED design plan is not second-guessed — the waiver is the decision")
    else:
        bad.append("a waived plan still reported problems")

    g4 = json.loads(json.dumps(g))
    g4["critic"] = {"waived": "no reason category"}
    if any("waived_category" in p for p in check(g4)):
        ok.append("an unclassified critic waiver is caught here, not at hand-off")
    else:
        bad.append("unclassified critic waiver passed")

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("init", help="write a fully-SHAPED skeleton (all placeholders).")
    p.add_argument("deck_dir")
    p.add_argument("--slides", type=int, help="pre-fill this many content/self-check rows.")
    p.add_argument("--delivery", default="presented", choices=DELIVERIES)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=_cmd_init)

    p = sub.add_parser("set", help="set one field by dotted path (value parsed as JSON if it is).")
    p.add_argument("deck_dir")
    p.add_argument("path")
    p.add_argument("value")
    p.set_defaults(fn=_cmd_set)

    p = sub.add_parser("check", help="report EVERY shape problem at once (never opens the pptx).")
    p.add_argument("deck_dir")
    p.set_defaults(fn=_cmd_check)

    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not getattr(a, "fn", None):
        ap.print_help()
        return 2
    return a.fn(a)


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
