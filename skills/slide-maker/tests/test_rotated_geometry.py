#!/usr/bin/env python3
"""Rotated shapes are measured where they PAINT, by both geometry gates.

🔴 MEASURED 2026-10-03 on a two-slide probe. A 5.0 x 0.5in vertical margin label rotated 90deg,
inside the canvas, was a CRITICAL OFF_CANVAS at build time (strict=True refused to save a correct
deck) and a hard `OVERFLOW [right+1.87]` after the render; the same label laid through a paragraph
of body copy produced ZERO findings in either gate. Both gates read the unrotated frame
(off/ext) and ignored `rot`. Both directions are asserted below, plus the unrotated control.
"""
from __future__ import annotations

import contextlib
import io
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import rotgeom as rg  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def near(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


# ── unit: normalisation (hand-written angles outside [0,360)) ──────────────────────────────────
check(rg.norm(-6) == 354.0, "norm(-6) should be 354, got {}".format(rg.norm(-6)))
check(rg.norm(370) == 10.0, "norm(370) should be 10")
check(rg.norm(359.995) == 0.0 and rg.norm(0.004) == 0.0, "angles within 0.01deg of a turn are 0")
check(rg.norm(None) == 0.0 and rg.norm("x") == 0.0, "non-numbers normalise to 0")
check(rg.is_axis(90) and rg.is_axis(270.004) and rg.is_axis(-90) and not rg.is_axis(8),
      "is_axis classifies right angles only")
check(rg.is_rotated(354) and not rg.is_rotated(360.0), "is_rotated")

# ── unit: the probe label, exactly ──────────────────────────────────────────────────────────────
check(near(rg.placed(10.2, 3.5, 5.0, 0.5, 90), (12.45, 1.25, 0.5, 5.0)),
      "90deg label placed box wrong: {}".format(rg.placed(10.2, 3.5, 5.0, 0.5, 90)))
check(rg.placed(1, 2, 3, 4, 0) == (1, 2, 3, 4), "unrotated must return the input untouched")
check(near(rg.placed(1, 2, 3, 4, 180), (1, 2, 3, 4)), "180deg keeps the box")
# clockwise on screen: a point to the RIGHT of centre moves BELOW it at +90
p = rg.rotate([(1.0, 0.0)], 0.0, 0.0, 90)[0]
check(near(p, (0.0, 1.0)), "rotation must be clockwise on a y-down screen, got {}".format(p))
# a tilted frame's placed box is the box of its corners
check(near(rg.placed(0, 0, 2, 3, 8), rg.bbox(rg.corners(0, 0, 2, 3, 8))), "tilted placed box")

# ── unit: exact intersection ────────────────────────────────────────────────────────────────────
a = rg.rect_poly(0, 0, 2, 2)
b = rg.rect_poly(1, 1, 2, 2)
A, bb = rg.overlap(a, b)
check(abs(A - 1.0) < 1e-9 and near(bb, (1, 1, 1, 1)), "axis overlap should be the 1x1 corner")
sq = rg.rect_poly(-0.5, -0.5, 1, 1)
dia = rg.corners(-0.5, -0.5, 1, 1, 45)
A, _ = rg.overlap(sq, dia)
check(abs(A - 2 * (math.sqrt(2) - 1)) < 1e-9,
      "unit square vs its 45deg self = 2(sqrt2-1), got {}".format(A))
A, bb = rg.overlap(rg.rect_poly(0, 0, 1, 1), rg.rect_poly(2, 2, 1, 1))
check(A == 0.0 and bb is None, "disjoint rects overlap nothing")
check(rg.contains_point(dia, (0.0, 0.0)) and not rg.contains_point(dia, (0.49, 0.49)),
      "point-in-rotated-rect")

# ── gate: lint_deck (render-time) ────────────────────────────────────────────────────────────────
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

import lint_deck  # noqa: E402


def _tb(shapes, x, y, w, h, text, size=20, rot=0, face="Arial"):
    t = shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    t.text_frame.word_wrap = True
    r = t.text_frame.paragraphs[0].add_run()
    r.text, r.font.size, r.font.name = text, Pt(size), face
    r.font.color.rgb = RGBColor(20, 20, 20)
    if any(ord(c) > 0x2E80 for c in text):              # CJK renders from <a:ea>, not <a:latin>
        from pptx.oxml.ns import qn
        from lxml import etree
        ea = etree.SubElement(r._r.get_or_add_rPr(), qn("a:ea"))
        ea.set("typeface", face)
    t.rotation = rot
    return t


def _card(shapes, x, y, w, h, rot):
    from pptx.enum.shapes import MSO_SHAPE
    c = shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid()
    c.fill.fore_color.rgb = RGBColor(0xE8, 0x5D, 0x3F)
    c.line.fill.background()
    c.rotation = rot
    return c


def probe_deck(path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    # 1 — CORRECT: vertical labels in both margins (Latin at 90, CJK at 270)
    s = prs.slides.add_slide(blank)
    _tb(s.shapes, 0.8, 0.8, 8, 1.0, "A correct page with vertical margin labels", 28)
    _tb(s.shapes, 10.2, 3.5, 5.0, 0.5, "EVERY PAGE OPENS A POSSIBILITY", 16, rot=90)
    _tb(s.shapes, -1.9, 3.5, 5.0, 0.5, "每一页都打开一种可能", 16, rot=270, face="PingFang SC")
    # 2 — BROKEN: the rotated label runs through a paragraph
    s = prs.slides.add_slide(blank)
    _tb(s.shapes, 0.8, 0.5, 8, 0.6, "A broken page", 28)
    _tb(s.shapes, 4.2, 3.5, 5.0, 0.5, "EVERY PAGE OPENS A POSSIBILITY", 16, rot=90)
    _tb(s.shapes, 5.6, 2.0, 2.6, 0.9, "Body copy the vertical label slices through.", 18)
    # 3 — CORRECT: two parallel 8deg cards whose AXIS boxes overlap but whose shapes do not
    s = prs.slides.add_slide(blank)
    _tb(s.shapes, 0.8, 0.5, 8, 0.6, "Tilted, apart", 28)
    _card(s.shapes, 1.0, 2.0, 2.0, 3.0, 8)
    _card(s.shapes, 3.15, 2.0, 2.0, 3.0, 8)
    # 4 — BROKEN: the same pair, really overlapping
    s = prs.slides.add_slide(blank)
    _tb(s.shapes, 0.8, 0.5, 8, 0.6, "Tilted, colliding", 28)
    _card(s.shapes, 1.0, 2.0, 2.0, 3.0, 8)
    _card(s.shapes, 2.90, 2.0, 2.0, 3.0, 8)
    # 5 — CORRECT: a vertical label inside an UNROTATED group
    s = prs.slides.add_slide(blank)
    _tb(s.shapes, 0.8, 0.5, 8, 0.6, "Grouped label", 28)
    g = s.shapes.add_group_shape()
    _tb(g.shapes, 10.2, 3.5, 5.0, 0.5, "EVERY PAGE OPENS A POSSIBILITY", 16, rot=90)
    prs.save(str(path))


def deck_findings(path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_deck.lint(str(path))
    by = {}
    for line in buf.getvalue().splitlines():
        line = line.strip()
        if line.startswith("slide ") and ":" in line:
            try:
                n = int(line.split(":", 1)[0].split()[1])
            except ValueError:
                continue
            by.setdefault(n, []).append(line)
    return by


with tempfile.TemporaryDirectory() as td:
    deck = Path(td) / "rot.pptx"
    probe_deck(deck)
    f = deck_findings(deck)
    s1 = [x for x in f.get(1, []) if "EVERY PAGE" in x or "每一页" in x]
    check(not s1, "lint_deck: correct vertical labels flagged: {}".format(s1))
    s2 = [x for x in f.get(2, []) if "EVERY PAGE" in x or "Body copy" in x]
    check(s2, "lint_deck: a rotated label through body copy produced no finding on slide 2")
    s3 = [x for x in f.get(3, []) if "OVERLAP" in x]
    check(not s3, "lint_deck: tilted cards that do not touch were called overlapping: {}".format(s3))
    s4 = [x for x in f.get(4, []) if "OVERLAP" in x]
    check(s4, "lint_deck: two tilted cards really overlapping produced no OVERLAP")
    s5 = [x for x in f.get(5, []) if "OVERFLOW" in x]
    check(not s5, "lint_deck: a grouped vertical label was called off-canvas: {}".format(s5))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_rotated_geometry] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
