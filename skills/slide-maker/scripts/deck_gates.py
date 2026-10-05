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

# ONE module owns the carve vocabulary — see material_probe.py for why a per-gate copy is exactly
# the drift `anchor_proof.py` was created to stop.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audience_brief as ab  # noqa: E402
import blind_read as brd  # noqa: E402
import composition_probe as cpx  # noqa: E402
import delegated_picks as dpk  # noqa: E402
import taste_ledger as tl  # noqa: E402
from material_probe import (CARVES as MATERIAL_PROBE_CARVES,  # noqa: E402
                            file_value as _mp_file, waiver_faults as _mp_faults)

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
        # 🔴 `picks` matters ONLY on a deck whose checkpoints were delivered as `auto` — it records
        # WHO answered each Step-0 question, because a value the user gave and one the skill
        # invented are otherwise byte-identical. A supervised run drops it. `angle` may never be
        # `delegated`. See delegated_picks.py.
        "interview": dict(
            {k: "<{}>".format(INTERVIEW_HINT[k]) for k in INTERVIEW_AXES},
            picks=[{"axis": "angle", "source": "genre-default | stated",
                    "value": "<the deck the request already implies>"},
                   {"axis": "audience", "source": "delegated",
                    "value": "<who is in the room>",
                    "basis": "<what in the request or the material points at them>",
                    "alternative": "<who else it could have been for, and why not>"},
                   # 🔴 the template row is what check_template_profile BINDS on: a designed
                   # registry template ships no .pptx and so has no layout fingerprint, and a deck
                   # that declared one and then built in stock colours binds to nothing without it
                   {"axis": "template", "source": "stated",
                    "value": "<registered name | none>"},
                   "<one row per axis: " + " · ".join(dpk.AXES) + ">"]),
        "delivery": delivery,
        "content": {
            "slides": [{"slide": i + 1, "role": "<cover|hook|evidence|framework|…>",
                        "takeaway": "<the sentence a reader should leave with>",
                        "evidence": ["<a locator: fig / p.4 ¶2 / a verbatim span>"], "units": 3}
                       for i in range(n)] or
                      [{"slide": 1, "role": "<role>", "takeaway": "<takeaway>",
                        "evidence": ["<locator>"], "units": 3}],
            # the interview asks for it on a talk ("give me the time budget and I will confirm the
            # slide count"); check_talk_time compares the built deck against it. Leave it null for a
            # deck that will be READ — a deck nobody presents is never late.
            "talk_minutes": None,
            # the questions you expect from THIS room, each with the backup slide that answers
            # it; check_qa_backup verifies that slide can be jumped to (dk.link) and left
            # (dk.back_link). Empty when you prepared no backup slides.
            "qa": [],
            # the bibliography this deck cites + the keys IN CITED ORDER; check_citations
            # derives every marker and reference line from those entries, so a retyped year
            # cannot drift. null for a deck that cites nothing.
            # {"bib": "refs.bib", "style": "numeric", "keys": ["lustig2007", ...]}
            "citations": None,
            "checkpoint": {"mode": "<approved|auto>", "record": "<how it was delivered>"},
            # WHAT THE AUDIENCE HAS TO DECIDE, in the order they face it — written BEFORE the
            # information is gathered, because the frame is what aims the gathering. On a
            # no-source deck this replaces the comprehension brief: there is no source to
            # comprehend, and a brief about the SUBJECT ships a deck about the subject.
            "audience_brief": {
                "who": "<who is in the room, and what they are about to do>",
                "decisions": [{"decision": "<what they must decide>",
                               "needs": "<what they need in hand to decide it>"}]},
            # Every claim the SOURCE ITSELF marks as not yet established — future work, an open
            # gate, "cannot establish", a roadmap item, a TODO. The deck may reference these, but
            # never in the established voice. `[]` is a legitimate value and means the question was
            # asked; the gate blocks the missing KEY, never the count.
            "open_ledger": [{"claim": "<what the source marks as NOT yet shown>",
                             "source": "<where it says so>",
                             "in_deck": "<absent | stated as open on slide N>"}],
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
            # image-led decks only (references/image-generation.md, the SERIES exception): "series"
            # + the path of its series.json; any other deck keeps "selective" (today's rule).
            "imagery": "selective",
            "image_series": None,
            # a curated visual language (references/visual-languages.md): name + "both" | "mac" fonts + the
            # ground it was built on ("light" or its contrast ground — visual_languages.py --gates prints all)
            "visual_language": None,
            "vl_fonts": "both",
            "vl_ground": None,
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
            # THE SIGNATURE PAGE, COMPETED. Never hand-written: `composition_probe.py compare
            # <probe>.pptx --slides 1,2,3` measures each variant and the gate re-checks that they
            # really are different compositions rather than one layout restyled.
            "composition": {
                "variants": [{"label": "A", "signature": "<composition_probe.py measured this>"},
                             {"label": "B", "signature": "<... and this>"}],
                "picked": "<A | B | …>",
                "why": "<what you SAW that decided it — name the versions you compared>"},
            "direction_gate": {"verdict": "<the directions_diversity.py verdict>",
                               "picked": "<the direction the user chose>",
                               "candidates": "<path to directions.json>",
                               "images": "<photos | illustrations | none — the pictures this deck will carry: the user's, generated or fetched; with none, also add native_fit: {language, why}>"},
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
        # Filled by `blind_read.py compare --write`, never by hand: the answers come from a reader
        # that was not shown this record, and the findings are computed from the two.
        "blind_read": {"answers": "<blind_read.py packet … → an independent reader → its JSON>",
                       "findings": "<blind_read.py compare … --write fills this>"},
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

    content = gates.get("content")
    if isinstance(content, dict):
        brief = content.get("audience_brief")
        if ab.is_waived(brief):
            for f in ab.waiver_faults(brief):
                problems.append("`content.audience_brief.waived` " + f)
        elif brief is None:
            problems.append("`content.audience_brief` " + ab.MISSING.split("\n")[0])
        else:
            for f in ab.faults(brief):
                problems.append("`content.audience_brief`: " + f)
        if "open_ledger" not in content:
            problems.append(
                "`content.open_ledger` is missing. It records every claim the SOURCE ITSELF marks "
                "as NOT yet established (future work, an open gate, 'cannot establish', a TODO) so "
                "that none of them reaches a slide in the established voice. Measured: a deck "
                "asserted that extra respiratory bins helped the reconstruction, while the source "
                "listed exactly that as an untested gate — the fact was IN the source, promoted to "
                "the wrong modality, which the never-invent rule does not catch. `[]` is a valid "
                "value and means the question was asked.")
        else:
            rows = content.get("open_ledger")
            if not isinstance(rows, list):
                problems.append("`content.open_ledger` must be a LIST of rows (use [] when the "
                                "source marks nothing as unresolved).")
            else:
                for i, r in enumerate(rows):
                    if not isinstance(r, dict) or not r.get("claim") or _ph(r.get("claim")):
                        problems.append("`content.open_ledger[{}]` needs a `claim`.".format(i))
                    elif not r.get("source") or _ph(r.get("source")):
                        problems.append("`content.open_ledger[{}]` needs a `source` — where the "
                                        "source says it is unresolved. Without the locator the row "
                                        "is an opinion about the material.".format(i))

    probe = _need(gates, "design_plan.material_probe", problems, dict,
                  why="Step 2 opens by BUILDING one real slide and looking at it.")
    # Step 2's documented carve — a registered/provided template, a Mode-A mimic, a 1-2 slide ask —
    # is now expressible. It had no waiver arm at all, so a deck on a registered template had to
    # invent an artifact and note that the gate and the prose disagreed. `conservative` is
    # deliberately not a carve: SKILL.md says restraint is a material decision too.
    if isinstance(probe, dict) and probe.get("waived"):
        for _f in _mp_faults(probe):
            problems.append("`design_plan.material_probe.waived` " + _f)
    elif isinstance(probe, dict):
        _pv = _mp_file(probe)          # `png` or `path`; the Codex evidence records use `path`
        if not _pv or _ph(_pv):
            problems.append("`design_plan.material_probe.png` is empty or a placeholder.")
        if not probe.get("safe_version") or _ph(probe.get("safe_version")):
            problems.append("`design_plan.material_probe.safe_version` is empty or a placeholder.")

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

    # The blind read. `render_selfcheck` above proves a look happened; this proves what was SEEN,
    # by someone who was not shown the record. Same shape pre-flight as everything else here.
    br = gates.get("blind_read")
    if brd.is_waived(br):
        for f in brd.waiver_faults(br):
            problems.append("`blind_read.waived` " + f)
    elif br is None:
        problems.append("`blind_read` " + brd.MISSING.split("\n")[0])
    else:
        for f in brd.faults(br, len(gates.get("content", {}).get("slides") or []) or None):
            problems.append("`blind_read`: " + f)
        for f in brd.recompute_faults(br, record=gates, slide_count=len(gates.get("content", {}).get("slides") or []) or None):
            problems.append("`blind_read`: " + f)

    # The signature page must have been COMPETED, not composed once. Shape pre-flight only —
    # `render_deck --gate-check` remains the authority, and the carve lives there too.
    _dp = tl.design_of(gates)
    _cmp = _dp.get("composition") if isinstance(_dp, dict) else None
    _cons = str((_dp or {}).get("boldness") or "").lower().startswith("conserv")
    if _cmp is not None or not _cons:
        for f in cpx.competition_faults(_cmp):
            problems.append("`design_plan.composition` " + (f if f is not cpx.MISSING else f))

    # What the skill decided FOR the user — only on a deck that waived the stops.
    if dpk.is_auto(gates):
        for f in dpk.faults(gates.get("interview"), auto=True):
            problems.append("`interview.picks` " + f)

    # What this user has already corrected by hand, on earlier decks. An empty ledger asks nothing.
    for f in tl.faults(tl.design_of(gates), tl.load()):
        problems.append(f)
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
    # 🔴 The count goes on EVERY line and again at the END, not only in a header.
    # MEASURED: this gate reported all 9 problems in one pass and said so on its first line — and
    # the run that motivated this read the output through `tail -8`, cut the header off, fixed the
    # three rows it could see, and paid three more round-trips discovering the rest. `tail` is the
    # habit of every agent that wants a verdict without a wall of text, so a report whose total
    # lives only at the top is a report that will be read truncated. `[4/9]` survives any window.
    n = len(probs)
    print("{} shape problem(s) — ALL of them, so one pass fixes the lot:\n".format(n))
    # 🔴 A HAND-WRITTEN record gets the FIELD NAMES wrong, and the gate can tell: the template
    # this same tool writes carries every key, and a record that came from it cannot be missing
    # one. MEASURED, twice in one session: a run typed the composition block by hand and used
    # `name` where the contract says `label`, then wrote the `why` clause with abbreviations the
    # gate rejects for not naming what was compared — two extra round-trips at the most expensive
    # moment, for a record `init` would have shaped correctly. The skill has said "write the
    # record with deck_gates.py, not by hand" in prose the whole time; prose is not a check, so
    # this says it where the mistake surfaces.
    if _looks_hand_written(_load(a.deck_dir)):
        print("🔴 This record does not look like it came from `deck_gates.py init` — several keys\n"
              "   the template always writes are absent. A hand-typed record gets the field NAMES\n"
              "   wrong (measured: `name` for `label`), which costs a round-trip per key. Either\n"
              "   run `python3 scripts/deck_gates.py init <deck-dir> --slides N` into a scratch\n"
              "   path and copy the shapes across, or check each block against it.\n")
    for i, m in enumerate(probs, 1):
        print("  [{}/{}] {}\n".format(i, n, m))
    print("{} shape problem(s) above — fix them in ONE pass, then re-run.".format(n))
    return 1


def _selftest():
    # 🔴 HERMETIC: point the taste ledger at a path that does not exist. It is USER-LEVEL data,
    # so a test that reads the real one passes or fails by whatever the developer happens to
    # have taught the skill — the same "passes by luck" class as a hash-salted fixture.
    os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/nonexistent/taste-ledger-for-tests.json"
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
    # Two genuinely different placeholder compositions — ink on the left vs ink on the right.
    # 🔴 The skeleton must PASS its own gate: a template whose own values are rejected teaches the
    # shape by failing, which this repo has shipped once already.
    _cv = [{"label": "A", "signature": {"cols": 2, "rows": 1, "grid": [[0.30, 0.02]], "blocks": 3,
                                        "dominance": 0.25, "centroid": [0.28, 0.5], "axis": 0.4,
                                        "ink": 0.32}},
           {"label": "B", "signature": {"cols": 2, "rows": 1, "grid": [[0.02, 0.30]], "blocks": 2,
                                        "dominance": 0.70, "centroid": [0.74, 0.5], "axis": -0.3,
                                        "ink": 0.32}}]
    d["composition"] = {"variants": _cv, "picked": "B",
                        "why": "B carries its claim in one beat; A buried it under the list"}
    d["checkpoint"] = {"mode": "approved", "record": "posted in chat"}
    g["content"]["audience_brief"] = {
        "who": "the three people who sign off the migration, deciding whether to fund phase 2",
        "decisions": [{"decision": "fund phase 2 or stop here",
                       "needs": "what phase 1 actually cost against its estimate"},
                      {"decision": "which team owns the rollout",
                       "needs": "where the work landed last time and what it displaced"},
                      {"decision": "what to tell the board in March",
                       "needs": "one number they can repeat without a caveat"}]}
    g["content"]["open_ledger"] = []          # swept; the source marks nothing as unresolved
    g["critic"] = {"waived": "user declined with the deck visible", "waived_category": "user-waived"}
    g["render_selfcheck"] = {"slides": [{"n": i + 1, "verdict": "ok"} for i in range(3)]}
    # A blind read whose findings are COMPUTED from its own answers and then answered. Typing the
    # findings by hand is precisely what `recompute_faults` catches, so a hand-typed fixture would
    # be testing the wrong thing.
    _bq = {k: ([] if k in ("legible_text", "unreadable", "problems") else "a real observation")
           for k, _ in brd.QUESTIONS}
    _bans = [dict(_bq, n=i + 1,
                  elements=dict({k: 0 for k in brd.ELEMENT_KEYS}, text_blocks=2, photos=1),
                  legible_text=["a real line of words that carries this page"])
             for i in range(3)]
    g["blind_read"] = {
        "answers": _bans,
        "findings": [dict(f, resolution="re-read the page at full size and acted on it",
                          **({"fixed": "rebuilt that page with measured layout"}
                             if f["severity"] == "hard" else {}))
                     for f in brd.compare(_bans, total=3, record=g)]}
    probs = check(g)
    if not probs:
        ok.append("a fully-filled record passes")
    else:
        bad.append("a filled record still fails: {}".format(probs))

    # 🔴 THE SPELLING, both ways. This gate's skeleton says `png`; every Codex evidence record
    # spells a file `path`. That exact split — `path` in one gate, `png` in the other — is what
    # made a bridged run write what its own gate demanded and the other reject it, and it is why
    # anchor_proof.py exists. material_probe.file_value() reads either, so neither runtime can be
    # blocked for using its own word.
    g_path = json.loads(json.dumps(g))
    g_path["design_plan"]["material_probe"] = {"path": "render/slide04.png",
                                               "safe_version": "two captioned pictures"}
    if check(g_path):
        bad.append("a probe spelled the CODEX way (`path`) was rejected by this gate: {}"
                   .format(check(g_path)))
    else:
        ok.append("a probe spelled `path` (the Codex records' key) passes here too")
    g_none = json.loads(json.dumps(g))
    g_none["design_plan"]["material_probe"] = {"safe_version": "two captioned pictures"}
    if any("material_probe" in p for p in check(g_none)):
        ok.append("...and a probe naming NO file under either key is still caught")
    else:
        bad.append("a probe with no file at all passed — reading two keys must not mean "
                   "accepting neither")

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


# The interview's questions, carried as DATA so a runtime with no choice UI has something to print
# rather than something to remember. Written in both languages because SKILL.md says "ask in the
# USER's language" and then shows only English — an instruction whose example contradicts it is one
# a hurried reader follows in English.
INTERVIEW_QUESTIONS = {
    "en": [
        ("language", "Which language should the slides be in — English, 中文, or bilingual EN+中文?"),
        ("density", "How much text per point — diagram-heavy (a phrase, a figure carries it), "
                    "balanced (one sentence + a visual), or text-heavy (2-3 sentences, reads "
                    "without a speaker)?"),
        ("length", "How many slides — short ~5-8, medium ~9-15, long 16+? (For a talk, give me the "
                   "time budget instead and I'll confirm the count.)"),
        ("goal", "What should this deck DO — inform, support a decision, or inspire action?"),
    ],
    "zh": [
        ("language", "幻灯片用哪种语言 —— 中文、English,还是中英双语?"),
        ("density", "每个要点多少字 —— 图为主(一个短语,图承载)、均衡(一句话配一张图),还是"
                    "文字为主(2-3 句,没有讲者也读得懂)?"),
        ("length", "要多少页 —— 短 5-8 / 中 9-15 / 长 16+?(如果是要讲的,给我时间预算,我来确认页数。)"),
        ("goal", "这份 deck 要做成什么 —— 告知、支持一个决策,还是推动行动?"),
    ],
}


def _cmd_interview(a):
    """Ask the four unartifacted axes, or record them — one command, for a runtime with no widgets.

    These four are singled out because nothing else downstream demands them, which is exactly why
    they are the ones that go unasked: measured on a real delivered deck, `delivery`, `builds` and
    `content.slides` were recorded and language, density, length and goal were not. A host with a
    choice UI has the axes carried FOR it by the widget; a plain-chat host has nothing carrying
    them, so it gets this.
    """
    g = _load(a.deck_dir) if _path(a.deck_dir).exists() else {}
    iv = g.get("interview") if isinstance(g.get("interview"), dict) else {}
    if a.set:
        bad = [kv for kv in a.set if "=" not in kv]
        if bad:
            print("each --set takes axis=answer, got: {}".format(" ".join(bad)), file=sys.stderr)
            return 2
        for kv in a.set:
            k, _, v = kv.partition("=")
            k = k.strip().lower()
            if k not in INTERVIEW_AXES:
                print("{!r} is not an interview axis — expected one of {}".format(
                    k, ", ".join(INTERVIEW_AXES)), file=sys.stderr)
                return 2
            iv[k] = v.strip()
        g["interview"] = iv
        _save(a.deck_dir, g)
        print("recorded: " + " · ".join("{} {}".format(k, iv[k]) for k in INTERVIEW_AXES if iv.get(k)))
    missing = [k for k in INTERVIEW_AXES if not str(iv.get(k) or "").strip()
               or str(iv.get(k)).strip().startswith("<")]
    if a.ask or (missing and not a.set):
        lang = a.lang or "en"
        print("\nAsk the user these, in ONE turn, in THEIR language "
              "(--lang {}):\n".format("/".join(sorted(INTERVIEW_QUESTIONS))))
        for i, (axis, q) in enumerate(INTERVIEW_QUESTIONS.get(lang, INTERVIEW_QUESTIONS["en"]), 1):
            mark = " " if axis in missing else "✓"
            print("  {} {}. {}".format(mark, i, q))
        print("\nThen record them:\n  python3 scripts/deck_gates.py interview {} \\\n"
              "      --set language=… --set density=… --set length=… --set goal=…"
              .format(a.deck_dir))
    if missing:
        print("\nstill unanswered: {}".format(", ".join(missing)))
        return 1
    print("all four axes answered")
    return 0


# Keys `init` ALWAYS writes. A record missing several of them was not produced by it.
_INIT_MARKERS = (("design_plan", "composition"), ("design_plan", "material_probe"),
                 ("design_plan", "signature_proof"), ("content", "audience_brief"),
                 ("content", "open_ledger"), ("content", "arc"))


def _looks_hand_written(rec) -> bool:
    """True when several blocks `init` always writes are absent.

    Deliberately a COUNT, not a single missing key: a deck may legitimately delete one block (a
    no-source deck writes no open ledger), and firing on that would make this an obstacle rather
    than a hint. It is a hint either way — it prints beside the findings and never blocks.
    """
    if not rec:
        return False
    missing = 0
    for top, key in _INIT_MARKERS:
        blk = rec.get(top)
        if not isinstance(blk, dict) or key not in blk:
            missing += 1
    return missing >= 3


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

    p = sub.add_parser("interview", help="ask / record the four axes nothing else demands.")
    p.add_argument("deck_dir")
    p.add_argument("--set", action="append", default=[], metavar="AXIS=ANSWER")
    p.add_argument("--ask", action="store_true", help="print the questions even if all are answered")
    p.add_argument("--lang", choices=sorted(INTERVIEW_QUESTIONS), help="the USER's language")
    p.set_defaults(fn=_cmd_interview)

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
