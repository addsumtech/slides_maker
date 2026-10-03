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
    # a paragraph, not a two-word caption: under a SUBSTITUTED face (CI's Linux runner) the
    # build-time gate deflates multi-line ink by the fallback's slack, by design, so a crossing
    # that is only just over TEXT_OVERLAP's 22% bar on the real face falls under it (measured
    # 2026-10-03). The render-time 6f check catches the short case either way.
    _tb(s.shapes, 5.6, 2.0, 2.6, 1.6, "Body copy the vertical label slices straight through, "
        "line after line, down the whole paragraph.", 18)
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

# ── gate: deckkit.lint_layout (build-time) ───────────────────────────────────────────────────────
import deckkit as dk  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    deck = Path(td) / "rot.pptx"
    probe_deck(deck)
    prs = Presentation(str(deck))
    fl = dk.lint_layout(prs, verbose=False)

    def crit(n):
        return [c for (s_, sev, c, m) in fl if s_ == n and sev == "CRITICAL"]

    check("OFF_CANVAS" not in crit(1), "lint_layout: correct vertical labels are OFF_CANVAS "
          "({})".format(crit(1)))
    check("TEXT_OVERLAP" in crit(2), "lint_layout: rotated label through body copy not caught "
          "(got {})".format(crit(2)))
    check("OFF_CANVAS" not in crit(3) and "OFF_CANVAS" not in crit(4), "tilted cards are in-canvas")
    # strict=True must SAVE the correct slide: rebuild a deck with slide 1 only
    one = Presentation()
    one.slide_width, one.slide_height = Inches(13.333), Inches(7.5)
    s = one.slides.add_slide(one.slide_layouts[6])
    _tb(s.shapes, 0.8, 0.8, 8, 1.0, "A correct page with vertical margin labels", 28)
    _tb(s.shapes, 10.2, 3.5, 5.0, 0.5, "EVERY PAGE OPENS A POSSIBILITY", 16, rot=90)
    _tb(s.shapes, -1.9, 3.5, 5.0, 0.5, "每一页都打开一种可能", 16, rot=270, face="PingFang SC")
    try:
        dk.lint_layout(one, verbose=False, strict=True)
    except Exception as exc:                                              # noqa: BLE001
        fails.append("lint_layout(strict=True) refused a correct rotated label: {}".format(exc))
    # a filled 90deg label whose text fits its frame must not read as OVERFLOW of a visible box
    s = one.slides.add_slide(one.slide_layouts[6])
    lab = _tb(s.shapes, 6.0, 3.0, 4.0, 0.6, "SECTION ONE", 16, rot=90)
    lab.fill.solid()
    lab.fill.fore_color.rgb = RGBColor(0xF2, 0xE6, 0x4B)
    fl2 = dk.lint_layout(one, verbose=False)
    check(not [m for (s_, sev, c, m) in fl2 if s_ == 2 and c == "OVERFLOW"],
          "lint_layout: a filled 90deg label whose text fits was called OVERFLOW")
    # the placed-geometry helpers: exact at 90deg, poly-bearing when tilted
    pb = dk._placed((10.2, 3.5, 5.0, 0.5), 90)
    check(near(pb, (12.45, 1.25, 0.5, 5.0)) and getattr(pb, "poly", None) is None, "_placed at 90")
    pt = dk._placed((1.0, 2.0, 2.0, 3.0), 8)
    check(getattr(pt, "poly", None) is not None, "_placed at 8deg carries its polygon")
    check(abs(dk._overlap_area(dk._placed((1.0, 2.0, 2.0, 3.0), 8),
                               dk._placed((3.15, 2.0, 2.0, 3.0), 8))) < 1e-9,
          "_overlap_area: parallel tilted cards 0.17in apart do not overlap")


# ── the other build-time passes: TEXT_OVER_MOTIF and TEXT_GRAZES_SHAPE place rotated shapes ─────
def _codes(prs_, n):
    return [c for (s_, sev, c, m) in dk.lint_layout(prs_, verbose=False) if s_ == n]


mp = Presentation()
mp.slide_width, mp.slide_height = Inches(13.333), Inches(7.5)
# 1: a motif BAR whose frame (x 5-11, y 3.0-3.3) misses the title, rotated 90deg so it PAINTS
#    x 7.85-8.15, y 0.15-6.15 — straight through the title's ink
s = mp.slides.add_slide(mp.slide_layouts[6])
_tb(s.shapes, 0.8, 0.8, 9.5, 1.0, "A correct page with vertical margin labels", 28)
bar = _card(s.shapes, 5.0, 3.0, 6.0, 0.3, 90)
dk.tag_motif(bar)
# 2: a filled BAR (not a motif) and a vertical label whose frame (x 4.2-9.2, y 3.5-4.0) misses the
#    bar but whose placed ink (x ~6.6-6.9, y ~1.25-4.4) dips into it from above — a graze
s = mp.slides.add_slide(mp.slide_layouts[6])
_tb(s.shapes, 0.8, 0.4, 6.0, 0.6, "Graze", 28)
_card(s.shapes, 6.2, 3.9, 3.0, 1.2, 0)
_tb(s.shapes, 4.2, 3.5, 5.0, 0.5, "EVERY PAGE OPENS A POSSIBILITY", 16, rot=90)
check("TEXT_OVER_MOTIF" in _codes(mp, 1),
      "TEXT_OVER_MOTIF: a rotated motif bar painted through the title was not seen "
      "(got {})".format(_codes(mp, 1)))
check("TEXT_GRAZES_SHAPE" in _codes(mp, 2) or "TEXT_OVERLAP" in _codes(mp, 2),
      "TEXT_GRAZES_SHAPE: a rotated label dipping into a filled bar was not seen "
      "(got {})".format(_codes(mp, 2)))

# ── TILTED (non-axis) shapes: position from the painted polygon, CLASSIFICATION from the frame ──
# Final review, 2026-10-03, every case confirmed BASE-vs-HEAD by probe: using the tilted shape's
# axis box where the polygon or the frame was needed produced false hard findings (a tilted kicker
# near body copy; a thin tilted rail read as a "card") AND silenced real ones (a tilted motif bar
# read as a "ground", a 2deg strike rule no longer "thin", a vertical label stealing the headline).
INK = dk.RGBColor.from_string("141414")
tp = dk.blank_deck(13.333, 7.5)


def _slide(title):
    sl = dk.add_slide(tp)
    dk.slide_background(sl, dk.WHITE)
    dk.text(sl, 0.8, 0.4, 11, 0.8, [[(title, 32, INK, True, False)]])
    return sl


def _kicker(sl):
    lab = dk.text(sl, 3.0, 3.0, 6.0, 0.6, [[("A TILTED KICKER LABEL ACROSS", 24, INK, True, False)]])
    lab.rotation = -10
    return lab


# find a body position whose ink is CLEAR of the tilted kicker's ink polygon but inside its axis box
_probe = dk.blank_deck(13.333, 7.5)
_ps = dk.add_slide(_probe)
_lab = _kicker(_ps)
_lb = dk._bbox_in(_lab)
_li = dk._placed_ink(_lab, _lb, dk._ink_rect(_lab, _lb)[0])
apart = None
for _by in [v / 20 for v in range(40, 80)]:
    for _bx in (2.4, 3.0, 6.0, 7.2, 8.0):
        _b = dk.text(_ps, _bx, _by, 2.4, 0.5, [[("Body copy", 20, INK, False, False)]])
        _bb = dk._bbox_in(_b)
        _bi = dk._ink_rect(_b, _bb)[0]
        _ax = max(0, min(_li[0] + _li[2], _bi[0] + _bi[2]) - max(_li[0], _bi[0])) * \
            max(0, min(_li[1] + _li[3], _bi[1] + _bi[3]) - max(_li[1], _bi[1]))
        # past TEXT_OVERLAP's own bar (> 0.05in2 and > 22% of the smaller ink) on the AXIS box
        if apart is None and _ax > max(0.06, 0.30 * _bi[2] * _bi[3]) \
                and dk._overlap_area(_li, _bi) == 0.0:
            apart = (_bx, _by)
check(apart is not None, "fixture: no position clear of the tilted kicker inside its axis box")
apart = apart or (8.0, 3.95)

s1 = _slide("Tilted kicker, body clear")                     # 1  correct
_kicker(s1)
dk.text(s1, apart[0], apart[1], 2.4, 0.5, [[("Body copy", 20, INK, False, False)]])
s2 = _slide("Tilted kicker, body crossed")                   # 2  broken
_kicker(s2)
dk.text(s2, 4.6, 3.05, 2.4, 0.5, [[("Body copy", 20, INK, False, False)]])
s3 = _slide("Thin tilted rail above a label")                # 3  correct (no card)
rail = dk.box(s3, 1.0, 1.4, 5.45, 0.28, fill=dk.RGBColor.from_string("2F5BEA"))
rail.rotation = 9
dk.text(s3, 1.2, 1.78, 4.4, 0.36, [[("DOMESTIC LEARNER VOLUME", 14, INK, True, False)]])
s4 = _slide("Tilted motif bar under a caption")              # 4  broken (text over motif)
bar = dk.box(s4, 2.0, 3.5, 6.0, 0.3, fill=dk.RGBColor.from_string("E5483B"))
bar.rotation = 10
dk.tag_motif(bar)
dk.text(s4, 3.5, 3.3, 3.0, 0.7, [[("Caption across", 24, INK, False, False)]])
s5 = _slide("Strike")                                        # 5  broken (rule through text)
dk.text(s5, 1.0, 2.0, 6.0, 0.8, [[("The old plan we abandoned", 28, INK, False, False)]])
rule = dk.box(s5, 1.0, 2.38, 5.6, 0.03, fill=dk.RGBColor.from_string("E5483B"))
rule.rotation = 2
s6 = dk.add_slide(tp)                                        # 6  broken (headline crowded)
dk.slide_background(s6, dk.WHITE)
dk.text(s6, 1.4, 0.5, 10, 0.8, [[("A headline that sits on top", 36, INK, True, False)]])
dk.text(s6, 1.4, 1.12, 9, 1.0, [[("Body copy placed right under the headline with no gap.", 20, INK, False, False)]])
vl = dk.text(s6, -1.9, 3.5, 5.0, 0.5, [[("SECTION ONE · THE SETUP", 16, INK, False, False)]],
             align=dk.PP_ALIGN.RIGHT)
vl.rotation = 270

tl = dk.lint_layout(tp, verbose=False)


def _has(n, code, sev=None):
    return any(s_ == n and c == code and (sev is None or sv == sev) for (s_, sv, c, m) in tl)


check(not _has(1, "TEXT_OVERLAP"), "C1 build: body CLEAR of a tilted kicker is a TEXT_OVERLAP")
check(_has(2, "TEXT_OVERLAP", "CRITICAL"), "C1 build: body crossed by a tilted kicker not caught")
check(_has(4, "TEXT_OVER_MOTIF"), "I1a: a caption across a TILTED motif bar went silent")
check(_has(5, "RULE_THROUGH_TEXT", "CRITICAL"), "I1b build: a 2deg strike rule through text went silent")
check(_has(6, "HEADLINE_CROWDED"), "I1c: a vertical label stole the headline; HEADLINE_CROWDED silent")

with tempfile.TemporaryDirectory() as td:
    dp = Path(td) / "tilt.pptx"
    tp.save(str(dp))
    tf_ = deck_findings(dp)
    c1 = [x for x in tf_.get(1, []) if "TEXT COLLISION" in x]
    check(not c1, "C1 render: body CLEAR of a tilted kicker is a TEXT COLLISION: {}".format(c1))
    c2 = [x for x in tf_.get(2, []) if "TEXT COLLISION" in x]
    check(c2, "C1 render: body crossed by a tilted kicker not caught")
    pad = [x for x in tf_.get(3, []) if "TEXT PADDING" in x]
    check(not pad, "C2: a thin tilted rail was read as a card: {}".format(pad))
    rt = [x for x in tf_.get(5, []) if "RULE THROUGH TEXT" in x]
    check(rt, "I1b render: a 2deg strike rule through text went silent")
    # a big print tilted 4deg is still CONTENT, not the page background
    bp = Presentation()
    bp.slide_width, bp.slide_height = Inches(13.333), Inches(7.5)
    from PIL import Image as _Im
    _ph = Path(td) / "ph.png"
    _im = _Im.new("RGB", (600, 350))
    _im.putdata([(80 + x // 6, 60 + y // 6, 40) for y in range(350) for x in range(600)])
    _im.save(_ph)
    bs = bp.slides.add_slide(bp.slide_layouts[6])
    pic = bs.shapes.add_picture(str(_ph), Inches(0.66), Inches(0.25), Inches(12.0), Inches(7.0))
    pic.rotation = 4
    rec = [r for r in lint_deck._boxes(bs, 13.333, 7.5) if r.get("pic")][0]
    check(not rec["bg"], "I1: a 12x7 print tilted 4deg was classified as the page background")

# ── found re-running real decks after the fix pass (2026-10-03) ─────────────────────────────────
# TEXT PADDING is a question about text in a card of the SAME orientation: a 270deg label whose
# painted top reaches into an unrotated picture is not "running past the picture's bottom" (a real
# deck's "Fourier" arrow label), while rotated text overflowing its own rotated chip IS — measured
# in the shared frame, as the base code did. And 6f must not fire on two vertical labels set at an
# ordinary line pitch: its floor is TEXT_OVERLAP's absolute 0.05in2, not the ink estimate's noise.
rp = dk.blank_deck(13.333, 7.5)


def _rslide():
    sl = dk.add_slide(rp)
    dk.slide_background(sl, dk.WHITE)
    return sl


sa = _rslide()                                               # 1  correct: different orientations
dk.box(sa, 5.0, 1.0, 2.0, 1.0, fill=dk.RGBColor.from_string("DDE6F5"))
fo = dk.text(sa, 5.5, 2.0, 0.94, 0.4, [[("Fourier", 16, INK, False, False)]])
fo.rotation = 270
sb = _rslide()                                               # 2  broken: overflows its own chip
chip = dk.box(sb, 4.0, 3.0, 3.0, 0.5, fill=dk.RGBColor.from_string("DDE6F5"))
chip.rotation = 90
ov_t = dk.text(sb, 4.0, 3.0, 3.0, 0.5, [[("A label far too long to fit inside its little rotated chip at all", 16, INK, False, False)]])
ov_t.rotation = 90
sc = _rslide()                                               # 3  correct: ordinary 0.18in pitch
for i, w_ in enumerate(("4 chamber", "2 chamber")):
    v = dk.text(sc, 4.0 + 0.18 * i, 3.0, 1.3, 0.32, [[(w_, 13, INK, False, False)]])
    v.rotation = 270
sd = _rslide()                                               # 4  broken: 0.10in pitch, glyphs collide
for i, w_ in enumerate(("4 chamber", "2 chamber")):
    v = dk.text(sd, 4.0 + 0.10 * i, 3.0, 1.3, 0.32, [[(w_, 13, INK, False, False)]])
    v.rotation = 270
with tempfile.TemporaryDirectory() as td:
    dp = Path(td) / "rp.pptx"
    rp.save(str(dp))
    rf = deck_findings(dp)
    check(not [x for x in rf.get(1, []) if "TEXT PADDING" in x],
          "a 270deg label reaching into an unrotated picture was judged for padding: {}".format(rf.get(1)))
    check([x for x in rf.get(2, []) if "TEXT PADDING" in x or "CHIP/LABEL" in x],
          "rotated text overflowing its own rotated chip went silent: {}".format(rf.get(2)))
    check(not [x for x in rf.get(3, []) if "TEXT COLLISION" in x],
          "two vertical labels at an ordinary 0.18in pitch were a TEXT COLLISION: {}".format(rf.get(3)))
    check([x for x in rf.get(4, []) if "TEXT COLLISION" in x],
          "two vertical labels at a 0.10in pitch (glyphs collide) were not caught")


# ── deferred from the final review: 6f reports a crossing PAIR once, not once from each side ───
dp_ = dk.blank_deck(13.333, 7.5)
sx = dk.add_slide(dp_)
dk.slide_background(sx, dk.WHITE)
for ang in (90, 270):
    v = dk.text(sx, 4.0, 3.0, 4.0, 0.4, [[("CROSSING LABELS HERE", 16, INK, True, False)]])
    v.rotation = ang
with tempfile.TemporaryDirectory() as td:
    dpp = Path(td) / "pair.pptx"
    dp_.save(str(dpp))
    pf = [x for x in deck_findings(dpp).get(1, []) if "TEXT COLLISION: rotated" in x]
    check(len(pf) == 1, "6f should report the crossing pair once, got {}".format(len(pf)))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_rotated_geometry] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
