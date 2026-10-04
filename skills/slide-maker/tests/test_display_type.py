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

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_display_type] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
