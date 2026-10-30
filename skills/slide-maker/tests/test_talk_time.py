#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The interview asks for the time budget; until `check_talk_time.py` nothing compared the deck to it.

Ending on time is the one thing every audience notices, and for a conference talk it is enforced by
a chair with a microphone. The budget was collected in the interview ("for a talk, give me the time
budget and I will confirm the slide count") and, measured by grep before this suite, no file in the
repo mentioned words per minute, a per-slide minute budget, or a duration of any kind. This is the
repo's recurring shape: a rule that lives in prose and is measured nowhere.

What is pinned here is the JUDGEMENT, not the arithmetic alone:
  * the estimate is a BAND, because delivery pace is someone else's and a single number is a lie;
  * only the SPEAKER NOTES count — on-slide text is not spoken by a presenter doing it right, and
    counting both would punish the decks that follow this skill's own rule;
  * a missing budget and a deck with notes on a third of its slides are NOT CHECKED, out loud —
    an estimate of part of a talk wearing the clothes of a whole one is worse than no estimate.

Run: python3 tests/test_talk_time.py
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import pathlib
import sys
import tempfile
import warnings

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))
warnings.simplefilter("ignore")

import check_talk_time as ctt                                             # noqa: E402
import deckkit as dk                                                      # noqa: E402
from pptx.dml.color import RGBColor                                       # noqa: E402

OK, BAD = [], []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="talktime-"))
INK = RGBColor(0x22, 0x22, 0x22)
_VOCAB = ("pipeline acquisition regulariser comparison reconstruction clinical reader numbers "
          "baseline cohort").split()


def ck(cond, msg, detail=""):
    (OK if cond else BAD).append(msg)
    print(("  ok   " if cond else "  ✗    ") + msg + (("  — %s" % (detail,)) if detail and not cond else ""))


def words(n):
    return " ".join(_VOCAB[i % len(_VOCAB)] for i in range(n))


def deck(name, notes, *, on_slide=""):
    """A deck whose slide i carries `notes[i]` as its spoken thread."""
    prs = dk.blank_deck()
    for i, note in enumerate(notes, 1):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        dk.text(s, 0.6, 0.8, 8.8, 3.5, [[(on_slide or "Slide %d" % i, 14, INK, False, False, dk.FONT)]])
        if note:
            dk.speaker_notes(s, note)
    path = TMP / name
    prs.save(str(path))
    return str(path)


print("— the rate bands, and where they come from")
ck(0 < ctt.LATIN_WPM[0] < ctt.LATIN_WPM[1] and 0 < ctt.CJK_CPM[0] < ctt.CJK_CPM[1],
   "both rates are ORDERED bands, not single numbers — a talk's pace belongs to the speaker, and "
   "one figure would be false precision about it")
_doc = ctt.__doc__ or ""
ck("130-150" in _doc and "180-220" in _doc and "words per minute" in _doc,
   "...and the module states the numbers it uses, so a reader can disagree with the rate rather "
   "than with an unexplained verdict")

print("\n— the arithmetic, on numbers that can be checked by hand")
lo, hi = ctt.minutes_band(1500, 0)
ck(abs(lo - 10.0) < 0.05 and abs(hi - 11.54) < 0.05,
   "1500 English words = 10.0-11.5 min (1500/150 and 1500/130)", (lo, hi))
lo, hi = ctt.minutes_band(0, 2200)
ck(abs(lo - 10.0) < 0.05 and abs(hi - 12.22) < 0.05,
   "2200 CJK characters = 10.0-12.2 min (2200/220 and 2200/180)", (lo, hi))
lat, cjk = ctt.spoken_load("Our 8x accelerated 重建 runs in 12 秒")
ck((lat, cjk) == (6, 3),
   "a mixed sentence splits by script — 6 Latin tokens, 3 CJK characters — so a bilingual talk is "
   "not timed on the wrong scale", (lat, cjk))

print("\n— the budget is read from what the interview actually records")
for text, want in (("12 pages / 10 min", 10), ("20 分钟", 20), ("a 45m slot", 45), ("1 hour", 60),
                   ("10 min + 5 Q&A", 10), ("20 分钟 + 5 分钟提问", 20),
                   ("30-minute committee meeting", 30), ("9-15 slides", None), ("", None)):
    got = ctt.parse_minutes(text)
    ck(got == want, "parse %r -> %r" % (text, want), got)
ck(ctt.recorded_minutes({"content": {"talk_minutes": 8},
                         "interview": {"length": "a 20 min talk"}}) == 8,
   "an explicit content.talk_minutes wins over the prose answer — the field exists to correct it")

print("\n— 🔴 scripts other than English and Chinese")
for label, sample in (("Russian", "это русский текст доклада " * 20),
                      ("Arabic", "هذا نص عربي للاختبار " * 20),
                      ("Greek", "αυτό είναι ελληνικό κείμενο " * 20),
                      ("Hindi", "यह हिंदी पाठ है " * 20)):
    w, c = ctt.spoken_load(sample)
    ck(w > 20 and c == 0,
       "%s counts as WORDS — `[A-Za-z0-9]` scored it ZERO, and a slide with no scored load reads "
       "as a slide with no notes, so a fully-noted deck was refused with 'only 0 of N slides carry "
       "speaker notes'" % label, (w, c))
ck(ctt.unsegmented_script("นี่คือข้อความภาษาไทยสำหรับการทดสอบ" * 4) == "Thai"
   and ctt.unsegmented_script("the quick brown fox " * 10) is None,
   "🔴 Thai/Lao/Khmer are NAMED and refused: they have no word spaces and are not CJK, this module "
   "has a sourced rate for neither, and the token count would come from where the combining marks "
   "fall — an estimate that looks like one and is not")
_thai = deck("thai.pptx", ["นี่คือข้อความภาษาไทยสำหรับการทดสอบ" * 4] * 6)
try:
    ctt.check(_thai, 10)
    ck(False, "a Thai deck is NOT CHECKED rather than given a number", "it returned a verdict")
except RuntimeError as exc:
    ck("Thai" in str(exc), "a Thai deck is NOT CHECKED, and the refusal names the script", exc)

print("\n— a PER-SLIDE budget is not the talk's budget")
for text in ("12 slides, 10 minutes each", "10 minutes per slide", "每页 2 分钟", "每张幻灯片 3 分钟"):
    ck(ctt.parse_minutes(text) is None,
       "🔴 %r reads as NOTHING, not as the talk length — taken as the budget it makes a correctly "
       "sized deck look twelve times too long, and refusing is the one reading that cannot "
       "mislead" % text, ctt.parse_minutes(text))
ck(ctt.parse_minutes("20 分钟") == 20 and ctt.parse_minutes("第 20 分钟开始") == 20,
   "...while an ordinary Chinese duration still parses — the guard is the per-unit marker, not the "
   "character")

print("\n— what the estimate is built from: the SPOKEN thread, never the slide")
wall = deck("wall.pptx", [words(40)] * 8, on_slide=words(120))
bare = deck("bare.pptx", [words(40)] * 8)          # same notes, no wall of on-slide words
_f, facts = ctt.check(wall, 6)
_fb, facts_b = ctt.check(bare, 6)
ck(facts["estimate"] == facts_b["estimate"] and not [f for f in _f if f[0] == "block"],
   "🔴 a deck with a WALL of on-slide text and short notes is not called long — on-slide words are "
   "not spoken by a presenter following this skill's own rule, and counting both would punish the "
   "decks that follow it", (facts["estimate"], facts_b["estimate"]))

print("\n— the verdicts")
over = deck("over.pptx", [words(150)] * 10)             # 1500 words -> 10.0-11.5 min
finds, facts = ctt.check(over, 6)
blocks = [f for f in finds if f[0] == "block"]
ck(len(blocks) == 1 and blocks[0][1] == "OVER THE SLOT",
   "1500 words in a 6-minute slot BLOCKS — over even at the fast end of the band", finds)
ck("Cut about" in blocks[0][2],
   "...and the message says how much to cut, not just that it is too long", blocks[0][2][:80])
_f2, _ = ctt.check(over, 11)
ck([f for f in _f2 if f[0] == "block"] == [] and any(f[1] == "TIGHT" for f in _f2),
   "the same deck in an 11-minute slot is TIGHT, not a block: it fits if delivery stays fast", _f2)
thin = deck("thin.pptx", [words(30)] * 6)               # 180 words -> 1.2-1.4 min
_f3, _ = ctt.check(thin, 12)
ck(any(f[1] == "UNDER THE SLOT" for f in _f3),
   "a deck that fills a fifth of its slot is reported too — a 12-minute speaker with four minutes "
   "of material has a problem the gate can see", _f3)
heavy = deck("heavy.pptx", [words(60)] * 3 + [words(700)] + [words(60)] * 6)
_f4, _ = ctt.check(heavy, 12)
ck(any(f[1] == "ONE SLIDE EATS THE TALK" and " 4" in f[2] for f in _f4),
   "one slide carrying five minutes of speech is named, with its number — the classic methods "
   "slide nobody can leave", _f4)

print("\n— what it refuses to answer")
for args, why in (((over, None), "no budget recorded — a deck that will be READ is never late"),
                  ((deck("sparse.pptx", [words(80)] * 3 + [""] * 7), 12),
                   "notes on 3 of 10 slides — an estimate of a third of the talk is worse than none")):
    try:
        ctt.check(*args)
        ck(False, "NOT CHECKED: %s" % why, "it returned a verdict instead")
    except RuntimeError as exc:
        ck(True, "NOT CHECKED: %s" % why)
        _msg = str(exc)
        ck(len(_msg) > 60 and any(w in _msg for w in ("talk_minutes", "interview", "speaker notes")),
           "...and the refusal names the field or artifact that would let it answer — an author "
           "can act on that, where a bare NOT CHECKED sends them reading", _msg[:80])
_fw, factsw = ctt.check(over, 6, waive="the chair moved us to the 12-minute slot after the programme changed")
ck(factsw.get("waived") and [f for f in _fw if f[0] == "block"],
   "a written waiver does not delete the finding — it is recorded beside it, the way every other "
   "floor in this skill is waived")

print("\n— both runtimes run it, and the record carries the budget across")
import check_gate_parity as gp                                            # noqa: E402
ck("talk_time" in gp.RECORD_FED,
   "talk_time is declared RECORD-FED, so parity demands tests/test_schema_reach.py prove both "
   "runtimes' records can be READ — being called on both paths is not the same thing")
_shared = (SKILL / "scripts" / "render_deck.py").read_text(encoding="utf-8")
_codex = (SKILL / "scripts" / "codex_delivery_gate.py").read_text(encoding="utf-8")
ck("_gate_section('talk_time')" in _shared and "def check_talk_time" in _codex,
   "the gate is wired on the shared path and the Codex path")
for name, src in (("shared", _shared), ("codex", _codex)):
    ck("talk_minutes" in src and '"talk_time"' in src or "'talk_time'" in src,
       "%s: its message names the budget field and the waiver, so the fix shape travels with the "
       "finding" % name)
_init = (SKILL / "scripts" / "deck_gates.py").read_text(encoding="utf-8")
ck('"talk_minutes"' in _init and '"talk_minutes"' in _codex,
   "both --init scaffolds SHOW the field — a field the scaffold omits is one nobody fills, which "
   "is what tests/test_scaffold_teaches.py exists to say")

print()
print("%d passed, %d failed" % (len(OK), len(BAD)))
raise SystemExit(1 if BAD else 0)
