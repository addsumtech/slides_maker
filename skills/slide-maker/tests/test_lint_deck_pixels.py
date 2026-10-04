#!/usr/bin/env python3
"""Render-time lint corner cases: paragraph spacing is not a hidden line (a covered line still is), a highlighted run is judged on its highlight, a crossing pair of rotated labels is one collision."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)



import subprocess
import deckkit as dk
from PIL import Image
td = Path(tempfile.mkdtemp())
items = ["1. Why a repair café works", "2. What people bring along", "3. How an evening runs", "4. How to join next month"]
prs = dk.blank_deck(13.333, 7.5)
# s1: four paragraphs with 14pt space after — rendered healthy, was "line 2 of 5 renders as a flat field" (a docs-only
# run's Korean agenda on an editorial card, 2026-10-04); Latin and Korean both
ko = ["1. 도구 소개와 안전 안내", "2. 가져온 물건 접수", "3. 자원봉사자와 함께 수리", "4. 다 고친 물건은 바로 가져가기"]
s = dk.add_slide(prs)
dk.box(s, 0.8, 0.8, 11.5, 5.6, fill="EAE3D6")
dk.text(s, 1, 1, 8, 4, [[(t, 18, dk.DEEP, False, False, "Arial", "Apple SD Gothic Neo")] for t in ko], space_after=14)
dk.text(s, 7.5, 4.5, 4.5, 1.8, [[(t, 14, dk.DEEP, False, False)] for t in items[:3]], space_after=14)
# s2: the same list with a box painted over its second line — the check must still catch a hidden line
s = dk.add_slide(prs)
dk.text(s, 1, 1, 8, 4, [[(t, 20, dk.DEEP, False, False)] for t in items], space_after=14)
dk.box(s, 0.9, 1.56, 8.2, 0.40, fill="FFFFFF")         # line 2's whole band (rendered 1.62-1.92in), not line 3
# s3: one highlighted run over a light photo, the other plain dark ink — the highlight is what sits behind its
# glyphs, so only the plain run is judged against the photo
img = td / "light.png"
im = Image.new("RGB", (800, 450))
im.putdata([(215 + (x * 3 + y) % 30, 210 + (x + y * 2) % 30, 205 + (y * 3) % 30) for y in range(450) for x in range(800)])
im.save(img)
s = dk.add_slide(prs)
dk.picture(s, str(img), 0, 0, 13.333, 7.5, alt="a light photograph")
hl = dk.mark(("NEW TONIGHT", 28, dk.RGBColor(0xFF, 0xFF, 0xFF), True, False), "1F2A44")
dk.text(s, 1, 1, 9, 1, [[hl, ("  bring a broken lamp along", 28, dk.RGBColor(0x11, 0x11, 0x11), False, False)]])
# s4: two rotated labels crossing — ONE collision, not one per side
s = dk.add_slide(prs)
a = dk.text(s, 3, 1, 4, 0.6, [[("A vertical label that runs", 18, dk.DEEP, False, False)]]); a.rotation = 90
b = dk.text(s, 3.1, 1.1, 4, 0.6, [[("Another vertical label here", 18, dk.DEEP, False, False)]]); b.rotation = 90
deck = td / "deck.pptx"
prs.save(str(deck))
subprocess.run([sys.executable, str(ROOT / "scripts" / "render_deck.py"), str(deck), str(td / "render")], capture_output=True, text=True)
r = subprocess.run([sys.executable, str(ROOT / "scripts" / "lint_deck.py"), str(deck), "--renders", str(td / "render")],
                   capture_output=True, text=True)
out = r.stdout + r.stderr
lines = [l_ for l_ in out.splitlines() if "slide" in l_]
def on(n, code):
    return [l_ for l_ in lines if ("slide {}:".format(n) in l_ or "slide  {}".format(n) in l_ or "slide {} ".format(n) in l_) and code in l_]
check(not on(1, "TEXT NOT VISIBLE"), "paragraph spacing is not a hidden line: {}".format(on(1, "TEXT NOT VISIBLE")))
check(on(2, "TEXT NOT VISIBLE"), "a box over line 2 of a spaced list is still caught: {}".format(lines[:6]))
check(not on(3, "TEXT-ON-IMAGE CONTRAST") and not on(3, "TEXT ON IMAGE"), "a highlighted run is judged on its highlight, not the photo: {}".format(on(3, "IMAGE")))
check(len(on(4, "TEXT COLLISION")) == 1, "a crossing pair of rotated labels is reported once: {}".format(on(4, "TEXT COLLISION")))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_lint_deck_pixels] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
