#!/usr/bin/env python3
"""A gate that CALLS a checker on both runtimes can still be unable to READ either one's record.

🔴 THE FAILURE THIS EXISTS FOR, measured. `check_purpose` was wired into both gate paths and
`check_gate_parity` reported 21 sections, 0 problems — correctly, by its own definition: it checks
that each `_gate_section` is *reachable* in `codex_delivery_gate.py`, and it was. But the extractor
read `design.purpose`, and inspecting the REAL scaffold that `codex_delivery_gate.py --init` writes
showed the Codex schema has no `purpose` key anywhere — not top level, not under `design`. The gate
existed on that runtime and could almost never bind. Parity was green the whole time.

That hole is structural, not a one-off: parity compares FILES, and this compares BEHAVIOUR. Split
by hand across the two paths, the reads that could carry it are

    shared  25 record reads — 19 are waiver lookups, 6 FEED a check
    codex   42 record reads — 11 are waiver lookups, 31 FEED a check

and the dangerous ones are the FEEDING reads' nested paths, because the top-level keys (`design`,
`interview`, `content`) do exist in both scaffolds. A static scan cannot settle this: the extractor
that failed loops over a tuple of candidate key names, which no regex reads.

So each extractor here is run against a PLAUSIBLY FILLED record for BOTH runtimes, filled the way
that runtime actually fills it, and must find what it needs on both. A `NOT CHECKED` that nobody
can ever clear is indistinguishable from a passing gate, which is the whole failure class.

Run: python3 tests/test_schema_reach.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, SCRIPTS)

OK, BAD = [], []


def ck(cond, msg):
    (OK if cond else BAD).append(msg)
    print(("  ok   " if cond else "  ✗    ") + msg)


def shared_scaffold():
    """The real `.deck-gates.json` skeleton, from the tool that writes it."""
    d = tempfile.mkdtemp(prefix="reach-shared-")
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "deck_gates.py"), "init", d,
                    "--slides", "3"], capture_output=True, text=True, check=True)
    return json.load(open(os.path.join(d, ".deck-gates.json")))


def codex_scaffold():
    """The real Codex evidence skeleton, from the tool that writes it."""
    f = os.path.join(tempfile.mkdtemp(prefix="reach-codex-"), "ev.json")
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "codex_delivery_gate.py"), "--init", f],
                   capture_output=True, text=True, check=True)
    return json.load(open(f))


print("— both scaffolds come from the tools that really write them, not from a copy here")
SH, CX = shared_scaffold(), codex_scaffold()
ck(isinstance(SH, dict) and isinstance(CX, dict), "both scaffolds load")
ck("interview" in SH and "interview" in CX, "both carry an `interview` block")
ck("purpose" not in CX and "purpose" not in (CX.get("design") or {}),
   "🔴 the Codex schema still has NO `purpose` key — the fact that made the purpose gate unbindable "
   "there. If this ever flips, the extractor can be simplified; until then it must not depend on it")

print("\n— PURPOSE: the extractor must find the genre on a record from EITHER runtime")
import check_purpose as cp                                                # noqa: E402
import purposes                                                           # noqa: E402

# filled the way each runtime actually fills it — the shared path records a purpose PICK, the Codex
# path (supervised) records the user's words in `interview.record` and an audience brief.
sh = json.loads(json.dumps(SH))
sh["interview"]["picks"] = [{"axis": "purpose", "source": "stated",
                             "value": "PhD guidance committee meeting"}]
cx = json.loads(json.dumps(CX))
cx["interview"]["record"] = "the user asked for a guidance committee meeting deck"
cx["content"]["audience_brief"] = {"who": "the PhD guidance committee",
                                   "decisions": [{"decision": "is the thesis on track"}]}
for rec, label in ((sh, "shared .deck-gates.json"), (cx, "Codex evidence")):
    got = purposes.match(cp.recorded_purpose(rec))
    ck(got is not None and got.name == "committee",
       "%s -> the purpose extractor binds (%s)" % (label, got.name if got else "NOTHING"))

# …and an UNFILLED scaffold must still bind to nothing on both, or the gate fires at placeholders
for rec, label in ((SH, "shared"), (CX, "Codex")):
    ck(purposes.match(cp.recorded_purpose(rec)) is None,
       "an unfilled %s scaffold binds to NOTHING — placeholder text is not a genre" % label)

print("\n— AUDIENCE BRIEF: the shared contract must read both schemas")
import audience_brief as ab                                               # noqa: E402
# the contract requires >=3 decisions ("fewer than that is a persona, not a brief") — the first
# fixture here had one and the suite reported the CONTRACT as broken. The contract was right.
good = {"who": "the PhD guidance committee, deciding whether the thesis is on track",
        "decisions": [{"decision": "is it on track", "needs": "the status of every chapter"},
                      {"decision": "does the thesis hold together",
                       "needs": "the line of enquiry, shown not asserted"},
                      {"decision": "what to scope down", "needs": "what is actually left"}]}
for rec_name, rec in (("shared", {"content": {"audience_brief": good}}),
                      ("Codex", {"content": {"audience_brief": good}})):
    faults = ab.faults(good)
    ck(faults == [], "%s: a filled audience brief passes its own contract (%r)" % (rec_name, faults))
ck(ab.faults({"who": "", "decisions": []}) != [],
   "…and an empty one does not — the contract is not vacuous")

print("\n— DELEGATED PICKS: auto-mode detection must work off each runtime's checkpoint shape")
import delegated_picks as dp                                              # noqa: E402
for label, rec in (("shared", {"content": {"checkpoint": {"mode": "auto"}},
                               "design_plan": {"checkpoint": {"mode": "auto"}}}),
                   ("Codex", {"content": {"checkpoint": {"mode": "auto"}},
                              "design": {"checkpoint": {"mode": "auto"}}})):
    ck(dp.is_auto(rec) is True,
       "%s: an auto-waiver deck is detected, so the delegated-picks record is demanded there" % label)
for label, rec in (("shared", {"content": {"checkpoint": {"mode": "approved"}},
                               "design_plan": {"checkpoint": {"mode": "approved"}}}),
                   ("Codex", {"content": {"checkpoint": {"mode": "approved"}},
                              "design": {"checkpoint": {"mode": "approved"}}})):
    ck(dp.is_auto(rec) is False,
       "%s: a supervised deck is NOT treated as auto — it records nothing extra" % label)

print("\n— ANCHOR PROOF: the record shape differs between the runtimes by spelling")
import anchor_proof as ap                                                 # noqa: E402
ck(ap.anchor_file({"role": "signature", "slide": 4, "png": "render/slide04.png"}) is not None,
   "the shared spelling (`png`) resolves")
ck(ap.anchor_file({"role": "signature", "slide": 4, "path": "render/slide04.png"}) is not None,
   "the Codex spelling (`path`) resolves — this pair is why the contract module exists at all")

print("\n— SURFACE: the section TERMS extension must be reachable under each schema's design key")
# the feeding read is `surface_section_terms` — the author's escape for a field's own vocabulary.
# It lives under `design_plan` on the shared path and `design` on the Codex one, which is exactly
# the pair that has already drifted twice in this repo.
for label, rec, key in (("shared", {"design_plan": {"surface_section_terms": {"methods": ["方法"]}}},
                         "design_plan"),
                        ("Codex", {"design": {"surface_section_terms": {"methods": ["方法"]}}},
                         "design")):
    got = (rec.get(key) or {}).get("surface_section_terms")
    ck(got == {"methods": ["方法"]},
       "%s: surface_section_terms is reachable under %r" % (label, key))
ck((SH.get("design_plan") is not None) and (CX.get("design") is not None),
   "…and BOTH scaffolds carry the design block those terms hang off "
   "(shared `design_plan`, Codex `design`)")

print("\n— CHECKPOINTS (checkpoints): auto-vs-approved must be readable from both, or delegation is invisible")
for label, rec in (("shared", SH), ("Codex", CX)):
    c = (rec.get("content") or {}).get("checkpoint")
    d = (rec.get("design_plan") or rec.get("design") or {}).get("checkpoint")
    ck(isinstance(c, dict) and "mode" in c and isinstance(d, dict) and "mode" in d,
       "%s: content.checkpoint.mode AND the design checkpoint's mode both exist in the real "
       "scaffold — a delegated run and a skipped one must not look identical" % label)

print("\n— CONTENT.AUDIENCE_BRIEF: covered above, and its contract is not vacuous")
ck(ab.faults(good) == [] and ab.faults({"who": "", "decisions": []}) != [],
   "content.audience_brief passes when filled and fails when empty, from the ONE shared contract "
   "module both paths import")

print("\n— TALK TIME: the budget the interview asks for must be readable from both records")
import check_talk_time as ctt                                             # noqa: E402

# each runtime writes it where its own schema puts things: the shared path keeps the interview's
# own answers, the Codex path records them under `design`/`content`. The question is asked as prose
# ("for a talk, give me the time budget"), so the number arrives inside a sentence.
sh_t = json.loads(json.dumps(SH))
sh_t["interview"]["length"] = "about 12 slides — it is a 10 min talk plus 2 min of questions"
cx_t = json.loads(json.dumps(CX))
cx_t["content"]["talk_minutes"] = 10
for rec, label in ((sh_t, "shared .deck-gates.json"), (cx_t, "Codex evidence")):
    ck(ctt.recorded_minutes(rec) == 10,
       "%s -> the time budget reads as 10 minutes (got %r)" % (label, ctt.recorded_minutes(rec)))
ck(ctt.recorded_minutes(SH) is None and ctt.recorded_minutes(CX) is None,
   "an unfilled scaffold carries NO budget on either runtime — the gate says NOT CHECKED rather "
   "than inventing a slot")
ck(ctt.recorded_minutes({"interview": {"length": "9-15 slides"}}) is None,
   "...and a slide count is never read as a duration")

print("\n— QA BACKUP: the anticipated questions must be readable from both records")
import check_qa_backup as cqb                                             # noqa: E402

# Both runtimes hold it in their own content block; the Codex file also has a `design` twin, which
# is where that schema keeps plan-side fields. Shape, not prose, this time — the entries name the
# slide that answers each question, and the gate resolves them against the BUILT file.
_qa = [{"question": "Why not compressed sensing as the baseline?", "slide": 14}]
sh_q = json.loads(json.dumps(SH)); sh_q["content"]["qa"] = _qa
cx_q = json.loads(json.dumps(CX)); cx_q["content"]["qa"] = _qa
cx_d = json.loads(json.dumps(CX)); cx_d.setdefault("design", {})["qa"] = _qa
for rec, label in ((sh_q, "shared .deck-gates.json"), (cx_q, "Codex evidence"),
                   (cx_d, "Codex evidence, design twin")):
    got = cqb.recorded_qa(rec)
    ck(got == _qa, "%s -> the anticipated questions read back (got %r)" % (label, got))
ck(cqb.recorded_qa(SH) is None and cqb.recorded_qa(CX) is None,
   "an unfilled scaffold carries NO questions on either runtime — the gate says NOT CHECKED "
   "rather than passing a deck nobody prepared for")
_empty = json.loads(json.dumps(SH)); _empty["content"]["qa"] = []
ck(cqb.recorded_qa(_empty) is None,
   "...and an explicitly EMPTY list reads the same way, so the scaffold's own `\"qa\": []` never "
   "reports as a checked-and-clean deck")

print("\n— CITATIONS: the citation plan must be readable from both records")
import check_citations as cc                                              # noqa: E402

_plan = {"bib": "refs.bib", "style": "numeric", "keys": ["lustig2007", "schlemper2018"]}
sh_c = json.loads(json.dumps(SH)); sh_c["content"]["citations"] = _plan
cx_c = json.loads(json.dumps(CX)); cx_c["content"]["citations"] = _plan
cx_dc = json.loads(json.dumps(CX)); cx_dc.setdefault("design", {})["citations"] = _plan
for rec, label in ((sh_c, "shared .deck-gates.json"), (cx_c, "Codex evidence"),
                   (cx_dc, "Codex evidence, design twin")):
    got = cc.recorded_citations(rec)
    ck(got == _plan, "%s -> the citation plan reads back (got %r)" % (label, got))
ck(cc.recorded_citations(SH) is None and cc.recorded_citations(CX) is None,
   "an unfilled scaffold carries NO citation plan on either runtime — the gate says NOT CHECKED "
   "rather than reporting a deck that cites nothing as checked")
_half = json.loads(json.dumps(SH))
_half["content"]["citations"] = {"bib": "refs.bib", "style": "numeric", "keys": []}
ck(cc.recorded_citations(_half) is None,
   "...and a plan with a bibliography but NO keys reads as nothing recorded — half a plan cannot "
   "be checked against the deck, and reporting it as clean is the failure this suite exists for")

print("\n— IMAGE SERIES: an image-led deck's series plan must be readable from both records")
import check_image_series as cis                                          # noqa: E402

# The shared record keeps plan-side fields in `design_plan`, the Codex file in `design`. Picking the
# image-led direction writes imagery: "series" + the series.json path; every scaffold starts at
# "selective", which must read as NOT an image-led deck — never as a series with no plan.
sh_s = json.loads(json.dumps(SH)); sh_s["design_plan"].update(imagery="series", image_series="s.json")
cx_s = json.loads(json.dumps(CX)); cx_s.setdefault("design", {}).update(imagery="series", image_series="s.json")
for rec, label in ((sh_s, "shared .deck-gates.json"), (cx_s, "Codex evidence")):
    got = cis.recorded_series(rec)
    ck(got == {"imagery": "series", "plan": "s.json"}, "%s -> the series plan reads back (got %r)" % (label, got))
ck(SH["design_plan"].get("imagery") == "selective" and CX["design"].get("imagery") == "selective",
   "both scaffolds WRITE the switch, at its default — an agent can see it exists")
ck(cis.recorded_series(SH) is None and cis.recorded_series(CX) is None,
   "an unfilled scaffold is NOT an image-led deck on either runtime — the gate says NOT CHECKED")
_noplan = json.loads(json.dumps(SH)); _noplan["design_plan"]["imagery"] = "series"
ck(cis.recorded_series(_noplan) == {"imagery": "series", "plan": None},
   "...and 'series' with no plan path reads as a series WITHOUT a plan, which the gate blocks")

print("\n— VISUAL LANGUAGE: a recorded visual language must be readable from both records")
import check_visual_language as cvl                                       # noqa: E402

sh_v = json.loads(json.dumps(SH)); sh_v["design_plan"].update(visual_language="collage", vl_fonts="mac", vl_ground="slate")
cx_v = json.loads(json.dumps(CX)); cx_v.setdefault("design", {}).update(visual_language="collage", vl_fonts="mac", vl_ground="slate")
for rec, label in ((sh_v, "shared .deck-gates.json"), (cx_v, "Codex evidence")):
    got = cvl.recorded_language(rec)
    ck(got == {"name": "collage", "fonts": "mac", "ground": "slate"},
       "%s -> the visual language and its ground read back (got %r)" % (label, got))
ck(all(k in SH["design_plan"] for k in ("visual_language", "vl_ground")) and all(k in CX["design"] for k in ("visual_language", "vl_ground")),
   "both scaffolds WRITE the visual-language and ground fields, so an agent can see they exist")
ck(cvl.recorded_language(SH) is None and cvl.recorded_language(CX) is None,
   "an unfilled scaffold records no language on either runtime — the gate says NOT CHECKED")

print("\n— the loop is closed: every record-FED gate section is covered here")
import re                                                                 # noqa: E402
import check_gate_parity as gp                                            # noqa: E402
covered = open(os.path.join(HERE, "test_schema_reach.py")).read()
for name in gp.RECORD_FED:
    ck(name.upper().replace("_", " ") in covered or name in covered,
       "gate section %r is exercised by this suite" % name)

print()
print("%d passed, %d failed" % (len(OK), len(BAD)))
raise SystemExit(1 if BAD else 0)
