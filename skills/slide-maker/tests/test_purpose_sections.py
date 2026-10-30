#!/usr/bin/env python3
"""A deck's GENRE declares content it is not finished without — and that is now checked.

`design-by-purpose.md` carried nine purpose recipes and nothing consumed them: measured by grep,
every per-purpose rule there was advisory by construction. Four genres with the most rigid
conventions were absent from the list entirely, and three of those are among the most common decks
an academic makes.

The mechanism is `formats.py` / `check_surface.py` generalised from SURFACES to GENRES. This suite
pins the three properties that make it worth having rather than noise:

  1. it fires on the MISSING section and only on that one
  2. it does not fire in a language it was not written in (a monolingual term list would report
     every CJK deck as missing every section)
  3. it binds ONLY on a recorded purpose it recognises — a genre outside the registry is NOT
     CHECKED, never a guessed section list

Run: python3 tests/test_purpose_sections.py
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import check_purpose as cp                                                # noqa: E402
import deckkit as dk                                                      # noqa: E402
import purposes                                                           # noqa: E402

OK, BAD = [], []
TMP = tempfile.mkdtemp(prefix="purpose-")


def ck(cond, msg):
    (OK if cond else BAD).append(msg)
    print(("  ok   " if cond else "  ✗    ") + msg)


def deck(name, lines, notes=None):
    prs = dk.blank_deck()
    for i, t in enumerate(lines):
        s = dk.add_slide(prs)
        dk.text(s, 0.6, 1.0, 8.8, 1.0, [[(t, 20, dk.DEEP, True, False)]])
        if notes and i < len(notes) and notes[i]:
            dk.speaker_notes(s, notes[i])
    path = os.path.join(TMP, name)
    prs.save(path)
    return path


def missing(path, purpose, **kw):
    probs, facts = cp.check(path, purpose, **kw)
    return facts["missing"]


print("— it fires on the MISSING section, and only that one")
full = deck("c_full.pptx", ["Progress since last year", "Plan for next year",
                            "Where I want your advice"])
ck(missing(full, "PhD guidance committee") == [],
   "a committee deck naming progress, plan and the ask is clean")
noask = deck("c_noask.pptx", ["Progress since last year", "Plan for next year", "Summary"])
ck(missing(noask, "PhD guidance committee") == ["ask"],
   "…and one without the ask reports exactly `ask` — the section whose absence turns a committee "
   "meeting into a status update")
thin = deck("g_thin.pptx", ["Specific aims", "Approach", "Timeline"])
ck(sorted(missing(thin, "ERC Starting Grant")) == ["feasibility", "risk"],
   "a grant deck with aims but no feasibility or risk reports exactly those two")

print("\n— speaker notes COUNT: the deck carries the section, not necessarily at 28pt")
innotes = deck("c_notes.pptx", ["Progress since last year", "Plan for next year", "Summary"],
               notes=[None, None, "I would like the committee's advice on scoping chapter 5."])
ck(missing(innotes, "PhD guidance committee") == [],
   "an ask that lives in the speaker notes satisfies the section — excluding notes would fire on "
   "exactly the decks that moved their sentences where this skill tells them to")

print("\n— it does not fire in a language it was not written in")
zh = deck("c_zh.pptx", ["去年的进展", "下一步计划", "想请教委员会的三个问题"])
ck(missing(zh, "年度考核进展汇报") == [],
   "a 中文 committee deck is clean via the 中文 terms")
for p in purposes.PURPOSES:
    for lbl, terms in p.required_sections:
        ck(any(any(ord(c) > 0x2E80 for c in t) for t in terms),
           "%s/%s carries a non-Latin synonym" % (p.name, lbl))

print("\n— it binds only where it recognises the genre")
for text, want in (("PhD guidance committee meeting", "committee"),
                   ("ERC Starting Grant proposal", "grant"),
                   ("journal club on a MICCAI paper", "journal_club"),
                   ("组会读论文", "journal_club"),
                   ("tumour board case presentation", "clinical_case"),
                   ("a product pitch to investors", "product_pitch"),   # was None until
                   ("teaching a first-year lecture", "teaching"),        # these two registered
                   ("an ethics committee submission", None),
                   ("", None)):
    got = purposes.match(text)
    ck((got.name if got else None) == want,
       "%r binds to %s" % (text[:34] or "<empty>", (got.name if got else "NOTHING (not checked)")))
# 🔴 NEGATIVE bindings, kept permanently. The first draft bound on a bare "committee" and a bare
# "proposal" — which would have pulled an INVESTMENT committee, an ETHICS committee and a business
# proposal into academic section lists, firing three or four times at the wrong deck. And because
# `recorded_purpose` also reads the AUDIENCE BRIEF, a loose term reaches far more decks than a
# purpose row alone. A check that fires on the wrong genre is how people learn to ignore checks.
# 🔴 "steering committee update" MOVED to the positive list when `exec_readout` was registered.
# It was correctly negative while the registry held only academic genres; a steering-committee
# update really is an exec readout, and ask/number/risk is exactly its shape. Recording the move
# rather than deleting the case: a negative assertion that becomes wrong is information about the
# registry growing, not a reason to loosen the guard. "ethics committee submission" stays negative
# — that genre has its own required content and this registry does not carry it.
_ec = purposes.match("steering committee update")
ck(_ec is not None and _ec.name == "exec_readout",
   "'steering committee update' now binds to exec_readout — it was negative until that genre was "
   "registered, and the ask/number/risk shape is genuinely its own")
# 🔴 Two more cases MOVED to positive when `product_pitch` and `teaching` were registered, the
# same way "steering committee update" did when `exec_readout` was. Recording each move instead of
# deleting the case: a negative assertion that becomes wrong is the registry growing correctly.
for text, want in (("a product pitch to investors", "product_pitch"),
                   ("teaching a first-year lecture", "teaching")):
    got = purposes.match(text)
    ck(got is not None and got.name == want,
       "%r now binds to %s — it was negative until that genre was registered" % (text[:34], want))
for text in ("investment committee readout", "ethics committee submission",
             "a business proposal for a client", "project proposal review",
             "an IRB submission", "a press release"):
    ck(purposes.match(text) is None,
       "%r binds to NOTHING — it is not one of these genres" % text[:40])

try:
    cp.check(full, "an ethics committee submission")
    ck(False, "an unbound genre must RAISE rather than check nothing silently")
except RuntimeError as exc:
    ck("binds to the recorded purpose" in str(exc),
       "an unbound genre raises and says so — a guessed section list would fire four times at the "
       "wrong deck and teach the author to ignore it")

print("\n— both record schemas, because a floor read from one runtime stops applying to the other")
shared = {"interview": {"picks": [{"axis": "purpose", "value": "annual guidance committee"}]}}
codex = {"design": {"purpose": "tumour board case presentation"}}
brief = {"content": {"audience_brief": {"who": "the PhD guidance committee, meeting to advise"}}}
# 🔴 The Codex schema has NO `purpose` key — checked against the real scaffold, not assumed — and
# `delegated_picks` records a purpose axis ONLY on an auto-waiver run. So on a supervised Codex
# deck `interview.record` (literally "the user's answers") and the audience brief's DECISIONS are
# often the only places the genre is written down. Without them the gate would be present on that
# runtime and unable to ever bind: a parity hole check_gate_parity structurally cannot see, because
# both paths really do call the checker.
cx_record = {"interview": {"mode": "answered",
                           "record": "The user asked for an ERC Starting Grant pitch"}}
cx_decision = {"content": {"audience_brief": {
    "who": "the review panel", "decisions": [{"decision": "whether to fund this grant proposal"}]}}}
for rec, want, why in ((shared, "committee", "shared .deck-gates.json interview.picks"),
                       (codex, "clinical_case", "Codex evidence design.purpose"),
                       (brief, "committee", "the audience brief, when no purpose row was filled"),
                       (cx_record, "grant", "Codex interview.record — the user's own answers"),
                       (cx_decision, "grant", "the audience brief's DECISIONS, when `who` is vague")):
    got = purposes.match(cp.recorded_purpose(rec))
    ck((got.name if got else None) == want, "%s is read (-> %s)" % (why, want))
# …and broadening the read surface must NOT broaden the BINDING
vague = {"content": {"audience_brief": {"who": "the review panel",
                                        "decisions": [{"decision": "fund it or not"}]}}}
ck(purposes.match(cp.recorded_purpose(vague)) is None,
   "a vague audience brief with no genre word still binds to NOTHING — reading more fields must "
   "not turn into guessing more genres")
scaffold_like = {"interview": {"picks": [{"axis": "angle", "value": "<which deck this is>"}]},
                 "content": {"audience_brief": {"who": "<who is in the room>"}}}
ck(purposes.match(cp.recorded_purpose(scaffold_like)) is None,
   "an UNFILLED scaffold binds to nothing rather than to whatever its placeholder text resembles")

print("\n— the escapes are real")
probs, facts = cp.check(noask, "PhD guidance committee", waive="this meeting is information-only")
ck(probs == [] and facts.get("waived"),
   "a written waiver clears it and is carried in the facts, not swallowed")
ck(missing(noask, "PhD guidance committee",
           extra_terms={"ask": ["punten ter bespreking"]}) == ["ask"],
   "an extension term that is NOT in the deck still reports missing")
nl = deck("c_nl.pptx", ["Voortgang", "Planning", "Punten ter bespreking"])
ck(missing(nl, "PhD guidance committee",
           extra_terms={"progress": ["voortgang"], "plan": ["planning"],
                        "ask": ["punten ter bespreking"]}) == [],
   "…and a deck in a language the registry does not carry is cleared by extending the TERMS, "
   "which keeps the check alive, rather than by waiving it away")

print("\n— the four genres added from this page's OWN prose bind, in both languages")
for text, want in (("lab meeting with my supervisor", "research_meeting"), ("组会", "research_meeting"),
                   ("weekly status update", "work_status"), ("周报", "work_status"),
                   ("product pitch to customers", "product_pitch"), ("产品介绍", "product_pitch"),
                   ("a first-year lecture", "teaching"), ("教学课程", "teaching")):
    got = purposes.match(text)
    ck((got.name if got else None) == want, "%r -> %s" % (text[:30], got.name if got else "NOTHING"))
# 组会 (lab meeting) vs 组会读论文 (journal club) — longest term wins, or the more specific genre loses
ck(purposes.match("组会读论文").name == "journal_club",
   "组会读论文 still binds to journal_club, not to the shorter 组会 — the longest matching term wins, "
   "which is what keeps a specific genre from being swallowed by a general one")

print("\n— WEBINAR is not a genre, and saying so beats checking nothing")
for text in ("a webinar for our users", "线上分享", "an online presentation"):
    ck(purposes.match(text) is None, "%r binds to no genre" % text)
    ck(purposes.not_a_genre(text) is not None,
       "…and %r is recognised as a delivery MODE, so the reader is asked for the genre" % text[:24])
ck(purposes.match("a teaching webinar") is not None
   and purposes.match("a teaching webinar").name == "teaching",
   "…while 'a teaching webinar' DOES bind — it names a genre, and the medium is beside the point")
ck(purposes.not_a_genre("PhD guidance committee") is None,
   "a real genre is never mistaken for a medium")

print("\n— the lists were DERIVED from design-by-purpose.md, not invented")
dbp = open(os.path.join(SKILL, "references/design-by-purpose.md")).read()
for genre, phrase in (("teaching", "objectives slide up front and a recap"),
                      ("research_meeting", "what changed since last time"),
                      ("product_pitch", "crisp one-line positioning"),
                      ("work_status", "decision or ask")):
    ck(phrase.lower() in dbp.lower(),
       "%s's sections trace to prose already on that page (%r)" % (genre, phrase[:34]))

print("\n— every registered purpose is reachable and actually checks something")
for p in purposes.PURPOSES:
    ck(bool(p.required_sections), "%s declares at least one section" % p.name)
    ck(bool(p.binds_on), "%s has binding terms, so it can be reached" % p.name)
    ck(bool(p.fidelity), "%s carries its own fidelity rule beyond never-invent" % p.name)

print("\n— MATCHING IS WORD-START, not naive substring — three checks were VACUOUS without it")
# a deck with none of the content, containing only words that happen to CONTAIN the terms
nc = deck("nocontent.pptx", ["Our action plan for the project",
                             "The benefit of this approach", "This is a summary"])
ck("investigations" in missing(nc, "tumour board case presentation"),
   "clinical investigations is NOT satisfied by 'ct' inside a-CT-ion / proje-CT")
ck("fit" in missing(nc, "faculty interview job talk"),
   "job-talk fit is NOT satisfied by 'fit' inside bene-FIT")
ck("positioning" in missing(nc, "product pitch to customers"),
   "product positioning is NOT satisfied by 'is a' — which is English, not a positioning phrase, "
   "and made this whole section report nothing missing on ANY deck")

print("\n— …and the boundary is on the START only, because several terms are PREFIXES")
pre = deck("prefix.pptx", ["Specific aims", "Feasibility and our track record",
                           "Risk and mitigation"])
ck(missing(pre, "ERC grant") == [],
   "'feasib' still matches FEASIBility — a trailing boundary would have broken it silently")
pre2 = deck("prefix2.pptx", ["Learning objectives", "A live demonstration", "Recap of key points"])
ck(missing(pre2, "a lecture") == [],
   "'demo' still matches DEMOnstration")
ck(cp._names("%", "we grew 50% this year"),
   "a term with no letters or digits ('%') falls back to substring — it has no boundary to anchor")

print("\n— every section carries its OWN NAME as a term")
# five shipped without it, and job_talk/track record reported MISSING on a slide reading
# "My track record" — a synonym list forgets the word it is a synonym OF.
for p_ in purposes.PURPOSES:
    for lbl, terms in p_.required_sections:
        ck(any(lbl.lower() in t.lower() or t.lower() in lbl.lower() for t in terms),
           "%s/%s includes its own name" % (p_.name, lbl))
own = deck("ownname.pptx", ["My track record", "Research plan for five years", "Why I fit here"])
ck(missing(own, "faculty job talk") == [],
   "…so a deck whose slide literally says 'My track record' is not reported as missing it")

print("\n— routing: layer 1 carries the trigger, which is what a non-Claude runtime reads")
skill = open(os.path.join(SKILL, "SKILL.md")).read()
ck("check_purpose.py" in skill, "SKILL.md names the checker")
ck("purposes.py" in skill, "…and the registry")
dbp = open(os.path.join(SKILL, "references/design-by-purpose.md")).read()
for genre in ("Grant proposal", "guidance committee", "Journal club", "Clinical case"):
    ck(genre in dbp, "design-by-purpose.md carries the %r recipe" % genre)
ck("TWELVE of the thirteen" in dbp and "delivery MODE, not a genre" in dbp,
   "…and states the coverage exactly (12 of 13) plus WHY the thirteenth has no list — a delivery "
   "mode is not a genre — rather than implying full coverage or vague under-coverage")

print("\n— the Codex RUNBOOK is a hand-copy of the registry, and the drift guard must not be vacuous")
# 🔴 WHY THIS BLOCK EXISTS. `references/codex-runtime.md` lists the genres in prose because a Codex
# agent reads it as its runbook. Writing that list out by hand got 1 of 12 wrong within minutes: it
# said "lab meeting" (a trigger word) where every gate message prints `research_meeting`, so an
# agent grepping the runbook for the name in its own error would have found nothing. A guard now
# lives in `check_purpose --selftest`. A guard nobody has seen FAIL is indistinguishable from one
# that checks nothing, so each arm is mutated here and must report.
import contextlib, dataclasses, io                                          # noqa: E402
import check_purpose as _cp                                                 # noqa: E402
import purposes as _pu                                                      # noqa: E402

_BASE = _pu.PURPOSES
_teach = [x for x in _BASE if x.name == "teaching"][0]


def _selftest_faults(registry):
    """Run the real selftest against a mutated registry; return the ✗ lines it printed."""
    _pu.PURPOSES = registry
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _cp._selftest()
        return [ln.strip()[2:].strip() for ln in buf.getvalue().splitlines()
                if ln.strip().startswith("\u2717")]
    finally:
        _pu.PURPOSES = _BASE


ck(_selftest_faults(_BASE) == [],
   "control: the UNMUTATED registry and the shipped runbook agree — the guard is not stuck red")

_renamed = tuple(x for x in _BASE if x.name != "teaching") + (
    dataclasses.replace(_teach, name="lecture_hall"),)
ck(any("lecture_hall" in f for f in _selftest_faults(_renamed)),
   "renaming a genre without touching the runbook is REPORTED — this is the exact defect found "
   "this round (runbook said 'lab meeting', gates say 'research_meeting')")

_extra_section = tuple(x for x in _BASE if x.name != "teaching") + (
    dataclasses.replace(_teach,
                        required_sections=_teach.required_sections + (("assessment", ("quiz", "测验")),)),)
ck(any("assessment" in f for f in _selftest_faults(_extra_section)),
   "adding a required section without documenting it is REPORTED — a runbook that understates a "
   "genre's content is worse than one that omits the genre, because it reads as complete")

# a duplicate of an ALREADY-DOCUMENTED genre leaves every name and section present, so only the
# stated total can catch it — proving the count arm is reachable on its own, not dead code.
_counts = tuple(_selftest_faults(_BASE + (dataclasses.replace(_teach),)))
ck(any("stated count has gone stale" in f for f in _counts),
   "growing the registry by a genre the runbook already names is caught by the STATED COUNT alone "
   "— that arm is independently reachable")
ck(not any("never names" in f for f in _counts),
   "…and nothing else fired on it, so that really was the count arm and not a name check in disguise")

print("\n— a NOUN in the material is not the deck's genre (real run, 2026-10-29)")
# 🔴 MEASURED. An annual-review deck whose material listed 社区基金会 (a community foundation) as an
# income source was bound to "Grant proposal / funding pitch" by the bare term 基金, and the purpose
# gate demanded feasibility and risk sections from a year-in-review. `recorded_purpose` reads the
# audience brief and `interview.record` — under auto mode a carved summary of the MATERIAL — so a
# bare noun that merely appears in the content binds the deck. Each pair below: a mention that must
# NOT bind, and the genre itself, which still must.
for text, want in (
        ("社区服务中心2025年度工作回顾：收入来源包括政府购买服务和社区基金会资助", None),
        ("申请国家自然科学基金面上项目", "grant"),
        ("国家自然科学基金申请书答辩", "grant"),
        ("实验室年度总结：本年度获国家自然科学基金资助3项", None),   # a grant RECEIVED is content
        ("国自然申请的预答辩", "grant"),
        ("年度回顾：本年度获得市慈善基金会和企业捐赠的支持", None),
        ("We received a grant from the community foundation; this is our year in review", None),
        ("funding came from individual donors and the city — our year in review", None),
        ("a grant pitch to the Wellcome Trust", "grant"),
        ("applying for funding from the national science foundation", "grant"),
        ("an immigrant support charity's annual report", None),
        ("of course, the annual report to our members", None),
        ("we ran 12 workshops this year — annual report", None),
        ("teaching a course on MRI physics", "teaching"),
        ("医院年度总结：全年收治病例3000例，多学科合作开展义诊", None),
        ("疑难病例讨论", "clinical_case"),
        ("多学科会诊病例汇报", "clinical_case"),
        ("hospital annual report: mortality rates fell", None),
        ("morbidity and mortality conference", "clinical_case")):
    got = purposes.match(text)
    ck((got.name if got else None) == want,
       "%r -> %s (want %s)" % (text[:40], got.name if got else "NOTHING", want or "NOTHING"))

print()
print("%d passed, %d failed" % (len(OK), len(BAD)))
raise SystemExit(1 if BAD else 0)
