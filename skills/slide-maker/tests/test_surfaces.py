#!/usr/bin/env python3
"""surfaces.grain_background: a tiled grain/paper ground in <p:bg> — deterministic, capped amplitude, lint-clean."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk, surfaces
from pptx.oxml.ns import qn
from PIL import Image
prs = dk.blank_deck(13.333, 7.5)
dk.set_ground("F3EBDD")
s = dk.add_slide(prs)
p1 = surfaces.grain_background(s, "F3EBDD", strength=6, seed=1)
p2 = surfaces.grain_background(s, "F3EBDD", strength=6, seed=1)
check(p1 == p2 and Path(p1).read_bytes() == Path(p2).read_bytes(), "deterministic tile")
cs = s._element.find(qn("p:cSld"))
check(cs[0].tag == qn("p:bg") and len(cs.findall(qn("p:bg"))) == 1, "one <p:bg>, first in cSld")
check(cs[0].find(".//" + qn("a:tile")) is not None and cs[0].find(".//" + qn("a:blip")) is not None, "a tiled picture fill")
im = Image.open(p1).convert("L")
lum = list(im.getdata())
base = Image.new("RGB", (1, 1), (0xF3, 0xEB, 0xDD)).convert("L").getpixel((0, 0))
check(max(abs(v - base) for v in lum) <= 6, "noise within ±strength")
check(len(set(lum)) > 4, "it is not flat")
dk.text(s, 1, 1, 8, 1, [[("Body text on grain", 20, dk.DEEP, False, False)]])
check(dk.lint_layout(prs, strict=True) == [], "lint_layout clean (no OOXML_SHAPE, no asset finding)")
for bad in (0, 11, -3):
    try:
        surfaces.grain_background(s, "F3EBDD", strength=bad)
        fails.append("strength {} accepted".format(bad))
    except ValueError:
        pass
try:
    surfaces.grain_background(s, "nothex")
    fails.append("a bad colour accepted")
except ValueError:
    pass

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_surfaces] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
