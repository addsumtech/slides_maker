#!/usr/bin/env python3
"""display_type: stacked headlines fill one measure, two-tone splits named words, outlined marks are pictures (LibreOffice draws a native hollow run filled)."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk, display_type as dt
prs = dk.blank_deck(13.333, 7.5)
dk.set_ground("F4EFE6")
s = dk.add_slide(prs)
box, bottom = dt.stacked(s, 0.8, 0.6, 4.0, ["BRING IT", "BROKEN"], color=dk.DEEP, face="Impact", max_size=200)
# ONE headline: one textbox, one paragraph per line (lint and PowerPoint both read it as one block)
paras = box.text_frame.paragraphs
check(len(paras) == 2 and bottom > 0.6, "two stacked lines in one box")
sizes = [p.runs[0].font.size.pt for p in paras]
check(sizes[1] > sizes[0], "the shorter word gets the larger size (both fill the width)")
# each line's REAL glyph width (the font file's advances) fits the box's inner width — measure_text only
# breaks at spaces, so it called a too-wide single word "one line" while LibreOffice broke it mid-word
# ("BRO / KEN" over the next block, 2026-10-03)
from PIL import ImageFont  # noqa: E402
for p, sz in zip(paras, sizes):
    fnt = ImageFont.truetype(str(dk._font_file("Impact")), int(sz * 10))
    width = fnt.getlength(p.runs[0].text) / 10.0 / 72.0
    check(width <= 4.0 - 0.056, "{!r} at {}pt is {:.2f}in wide — wider than the box".format(p.runs[0].text, sz, width))
check(abs((box.top + box.height) / 914400.0 - bottom) < 0.02, "bottom is the box's measured end")
zs, zbottom = dt.stacked(s, 8.2, 0.6, 4.4, ["城市", "小菜园"], color=dk.DEEP, ea="Songti SC", max_size=72)
check(len(zs.text_frame.paragraphs) == 2, "CJK stacked")
try:
    dt.stacked(s, 0.8, 5, 1.0, ["AN EXTREMELY LONG HEADLINE LINE"], color=dk.DEEP, face="Impact", min_size=40)
    fails.append("a line that cannot fit at min_size was accepted")
except ValueError as e:
    check("min_size" in str(e), str(e))
tb = dt.two_tone(s, 0.8, bottom + 0.15, 7.0, 0.9, "Bring it broken.", ["broken."], size=32, color=dk.DEEP,
                 accent=dk.RGBColor(0xB2, 0x3A, 0x28), face="Georgia")
runs = tb.text_frame.paragraphs[0].runs
check([r.text for r in runs] == ["Bring it ", "broken."], "split at the accent word")
check(str(runs[1].font.color.rgb) == "B23A28", "accent colour on the accent word")
zt = dt.two_tone(s, 0.8, bottom + 1.1, 7.0, 0.8, "楼顶也能种菜", ["种菜"], size=28, color=dk.DEEP,
                 accent=dk.RGBColor(0xB2, 0x3A, 0x28), ea="Songti SC")
check([r.text for r in zt.text_frame.paragraphs[0].runs] == ["楼顶也能", "种菜"], "CJK split")
if dk._font_substituted("Arial Black"):          # the ubuntu CI runner: outlined() must REFUSE a stand-in face
    print("  skip outlined('07') picture: Arial Black is not installed here — checking the refusal instead")
    try:
        dt.outlined(s, 9.2, zbottom + 0.2, 3.0, 1.6, "07", color="B23A28")
        fails.append("outlined drew with a stand-in for a face that is not installed")
    except ValueError as e:
        check("installed" in str(e), str(e))
else:
    pic = dt.outlined(s, 9.2, zbottom + 0.2, 3.0, 1.6, "07", color="B23A28")
    check(pic.shape_type == 13 and pic._element.find(".//" + dk.qn("p:cNvPr")).get("descr") == "07", "a picture with alt text")
try:                                              # a face that cannot draw the text refuses (it would draw boxes)
    dt.outlined(s, 1, 1, 1, 1, "三成", color="B23A28", face="Impact")
    fails.append("outlined accepted '三成' in Impact, which has no CJK glyphs")
except ValueError:
    pass
for bad in ("TOO LONG!", ""):
    try:
        dt.outlined(s, 1, 1, 1, 1, bad, color="B23A28")
        fails.append("outlined accepted {!r}".format(bad))
    except ValueError:
        pass
try:
    dt.outlined(s, 1, 1, 1, 1, "07", color="B23A28", face="No Such Face 123")
    fails.append("outlined accepted a face that is not installed")
except ValueError as e:
    check("installed" in str(e), str(e))
crit = [f for f in dk.lint_layout(prs, strict=True, verbose=False) if f[1] == "CRITICAL"]
check(not crit and all(f[1] != "WARN" or f[2] != "TEXT_OVERLAP" for f in dk.lint_layout(prs, verbose=False)), "lint: no critical, no overlap")

# _glyph_width measures the FACE the run renders in. macOS ships whole families as ONE .ttc collection, and the
# collection's face 0 was measured for every style: a bold "45" in Rockwell (2.444in at 150pt, the regular width; bold
# is 2.625) was planned on one line of a timer dial and rendered on two (recipe, 2026-10-22); Chalkboard SE bold "CHAPTER
# TWO" read 1.615in for 1.673 (comic); Avenir Next's face 0 is its BOLD, so its regular read 3.7% wide. The faces below
# are the ones LibreOffice drew for these runs (PDF font names, rendered 2026-10-22); the oracle reads each face by its
# PostScript name straight from the collection — never through the code under test. Italic: the family's real italic
# face (8-11% narrower in Baskerville / Hoefler Text / Didot); a family with no italic face is SLANTED by the renderer,
# which keeps the upright advances (Chalkboard SE: origins identical, measured); a bold italic the family lacks (Didot)
# is measured at the wider of its italic and its bold, because LibreOffice drew Didot's as the slanted Bold.
from fontTools.ttLib import TTCollection  # noqa: E402
from PIL import ImageFont  # noqa: E402


def _ps_width(face, ps, text, size):
    path = dk._font_file(face)
    if dk._font_substituted(face) or not path or not str(path).lower().endswith((".ttc", ".otc")):
        return None
    names = [f_["name"].getDebugName(6) for f_ in TTCollection(str(path), lazy=True).fonts]
    if ps not in names:
        return None
    fnt = ImageFont.truetype(str(path), int(size * 10), index=names.index(ps), layout_engine=ImageFont.Layout.BASIC)
    return fnt.getlength(text) / 10.0 / 72.0


TTC_CASES = [("Rockwell", True, False, "Rockwell-Bold"), ("Chalkboard SE", True, False, "ChalkboardSE-Bold"),
             ("Chalkboard SE", False, False, "ChalkboardSE-Regular"), ("Chalkboard SE", False, True, "ChalkboardSE-Regular"),
             ("Avenir Next", False, False, "AvenirNext-Regular"), ("Avenir Next", True, False, "AvenirNext-Bold"),
             ("Avenir Next", False, True, "AvenirNext-Italic"), ("Avenir Next", True, True, "AvenirNext-BoldItalic"),
             ("Helvetica Neue", True, False, "HelveticaNeue-Bold"), ("Helvetica Neue", False, True, "HelveticaNeue-Italic"),
             ("Baskerville", False, True, "Baskerville-Italic"), ("Hoefler Text", False, True, "HoeflerText-Italic"),
             ("Didot", True, False, "Didot-Bold"), ("Didot", True, True, "Didot-Bold")]
_ran = 0
for _face, _b, _i, _ps in TTC_CASES:
    for _t, _sz in (("45", 150), ("CHAPTER TWO", 17), ("Hamburgefonstiv 1,250", 40)):
        want = _ps_width(_face, _ps, _t, _sz)
        if want is None:
            continue
        _ran += 1
        got = dt._glyph_width(_t, _sz, _face, _b, _i)
        check(got is not None and abs(got - want) <= 0.002 * want + 1e-4,
              "{} {}{} {!r} at {}pt is measured in {} ({:.3f}in), got {}".format(
                  _face, "bold" if _b else "regular", " italic" if _i else "", _t, _sz, _ps, want,
                  None if got is None else round(got, 3)))
print("  ({} collection-face width checks ran here{})".format(
    _ran, "" if _ran else " — none: this machine has none of these .ttc families"))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_display_type] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
