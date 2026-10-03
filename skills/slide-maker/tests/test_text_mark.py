#!/usr/bin/env python3
"""mark(): a highlighter behind chosen words — native, follows the text, and gated for contrast.

Editorial decks set one or two words of a headline on a block of colour. Drawn as a separate shape
the block has to be positioned by guesswork and drifts off the word (measured 2026-10-03: the
guessed block covered half of "NEED ROOM"); `<a:highlight>` is a run property, so it follows the
glyphs wherever they wrap, in any script. The contrast gate must read the highlight as that run's
backing — otherwise dark ink on a dark highlight would sail through 1b, which compares the ink with
the SHAPE's fill.
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deckkit as dk  # noqa: E402
import lint_deck  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


LIME = dk.RGBColor.from_string("D4FF3A")
INK = dk.RGBColor.from_string("141414")
NAVY = dk.RGBColor.from_string("1A2B45")

prs = dk.blank_deck(13.333, 7.5)
s = dk.add_slide(prs)
dk.slide_background(s, dk.WHITE)
tb = dk.text(s, 0.6, 0.6, 12, 2.2, [[("BUILD THE SMALLEST ", 54, INK, True, False, "Arial"),
                                     dk.mark(("OBJECT", 54, INK, True, False, "Arial"), LIME),
                                     (" THAT ASKS A QUESTION", 54, INK, True, False, "Arial")]])
x = tb._element.xml
check(x.count("<a:highlight>") == 1 and "D4FF3A" in x, "exactly one run carries the highlight")
# a marked run still unpacks like the run it wraps (every run-tuple reader keeps working)
m = dk.mark(("WORD", 20, INK, True, False), LIME)
txt, size, color, bold, italic = m
check((txt, size, bold) == ("WORD", 20, True) and m.highlight == LIME, "a mark unpacks like its run")
# CJK, with the seventh (EA face) slot and CJK_SPACING on — the pangu pass must keep the mark
dk.CJK_SPACING = "spaced"
try:
    t2 = dk.text(s, 0.6, 3.2, 12, 1.4, [[("小团队", 40, INK, True, False, "Arial", "PingFang SC"),
                                         dk.mark(("学得快", 40, INK, True, False, "Arial", "PingFang SC"),
                                                 "FFD400")]])
finally:
    dk.CJK_SPACING = None
check("<a:highlight>" in t2._element.xml, "the CJK pangu pass dropped the highlight")
# schema order: highlight precedes latin/ea inside rPr
for rpr in re.findall(r"<a:rPr[^>]*>.*?</a:rPr>", t2._element.xml + x, re.S):
    if "<a:highlight>" in rpr and "<a:latin" in rpr:
        check(rpr.index("<a:highlight>") < rpr.index("<a:latin"), "highlight must precede latin")
# refusal: navy ink on a navy-ish highlight is under the floor
try:
    dk.mark(("LOW", 20, NAVY, False, False), "22334F")
    fails.append("mark() accepted 1.2:1 ink on its highlight")
except ValueError:
    pass
try:
    dk.mark("not a run", LIME)
    fails.append("mark() accepted a non-run")
except TypeError:
    pass

# ── the contrast gate reads the highlight as the backing ───────────────────────────────────────
s2 = dk.add_slide(prs)
dk.slide_background(s2, dk.WHITE)
bad = dk.text(s2, 0.6, 0.6, 12, 1.4, [[("READABLE ", 40, INK, True, False)]])
# write a failing pair past mark()'s own refusal, straight into the XML — the gate is the backstop
# for decks not built through mark()
r = bad.text_frame.paragraphs[0].add_run()
r.text = "HIDDEN"
r.font.size = dk.Pt(40)
r.font.color.rgb = NAVY
dk._set_highlight(r, dk.RGBColor.from_string("22334F"))
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "m.pptx"
    prs.save(str(p))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_deck.lint(str(p))
    out = buf.getvalue()
check("HIDDEN" in out and ("INVISIBLE TEXT" in out or "LOW CONTRAST" in out),
      "lint_deck did not read the highlight as the run's backing:\n" + out[-800:])
check(not any("OBJECT" in ln and ("INVISIBLE" in ln or "CONTRAST" in ln) for ln in out.splitlines()),
      "a legible marked word was reported as low contrast")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_text_mark] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
