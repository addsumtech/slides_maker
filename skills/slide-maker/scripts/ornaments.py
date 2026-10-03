#!/usr/bin/env python3
"""ornaments — the hand-made marks of editorial decks, as native editable geometry.

squiggle · scribble · brush_stroke · tape · scallop. Each is ONE shape with a custom geometry
(curves where the mark is curved), flattened (no inherited theme shadow), and TAGGED as the deck's
motif — quiet by default, `loud=True` for a hero appearance — so MOTIF_BUDGET counts it and
TEXT_OVER_MOTIF sees a caption laid across it. They are borrowed marks, not a register: use one or
two per deck where they MEAN something (a squiggle under the claim, tape holding a print), never as
confetti — the motif budget will say so.

Measured 2026-10-03: hand-made marks were present on most of the 33 image-led editorial decks
surveyed and absent from all 72 sampled pages this skill had built; the library had starbursts and
zigzags (register_surface) and nothing hand-drawn.

    import ornaments as orn
    orn.squiggle(s, 0.8, 2.1, 4.0, 0.35, "E5483B")     # under the claim
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import deckkit as dk  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_U = 10000                                   # path units per frame side


def _need(**dims):
    for k, v in dims.items():
        if not v or v <= 0:
            raise ValueError("ornaments: {} must be > 0 (got {!r})".format(k, v))


def _count(**counts):
    """Counts (waves, loops, bumps) are whole numbers >= 1 — a float used to die inside range()."""
    for k, v in counts.items():
        if isinstance(v, bool) or not isinstance(v, int) or v < 1:
            raise ValueError("ornaments: {} must be a whole number >= 1 (got {!r})".format(k, v))


def _shape(slide, x, y, w, h, path_xml, *, fill=None, line=None, line_w=2.0, alpha=None,
           loud=False, rotation=0.0):
    """One flattened shape whose geometry is `path_xml` (inside <a:pathLst>), motif-tagged."""
    sh = dk._flat(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, dk.Inches(x), dk.Inches(y),
                                         dk.Inches(w), dk.Inches(h)))
    spPr = sh._element.spPr
    old = spPr.find(dk.qn("a:prstGeom"))
    g = dk.parse_xml('<a:custGeom xmlns:a="{}"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
                     '<a:rect l="0" t="0" r="r" b="b"/><a:pathLst>{}</a:pathLst></a:custGeom>'
                     .format(_A, path_xml))
    old.addprevious(g)
    spPr.remove(old)
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = dk._as_rgb(fill)
        if alpha is not None:
            clr = spPr.find(dk.qn("a:solidFill"))[0]
            clr.append(clr.makeelement(dk.qn("a:alpha"), {"val": str(int(round(alpha * 100000)))}))
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = dk._as_rgb(line)
        sh.line.width = dk.Pt(line_w)
        ln = spPr.find(dk.qn("a:ln"))
        if ln is not None:
            ln.set("cap", "rnd")                 # a pen mark has round ends
    if rotation:
        sh.rotation = float(rotation)
    return dk.tag_motif(sh, loud=loud)


def _pt(x, y):
    return '<a:pt x="{}" y="{}"/>'.format(int(round(x)), int(round(y)))


def _smooth(points, closed=False):
    """Catmull-Rom through `points` (path units) as cubic Beziers."""
    n = len(points)
    out = []
    for i in (range(n) if closed else range(n - 1)):
        p0 = points[(i - 1) % n] if closed else points[max(i - 1, 0)]
        p1, p2 = points[i], points[(i + 1) % n]
        p3 = points[(i + 2) % n] if closed else points[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        out.append("<a:cubicBezTo>{}{}{}</a:cubicBezTo>".format(_pt(*c1), _pt(*c2), _pt(*p2)))
    return "".join(out)


def _ring(points):
    """A closed straight-edged path through `points`."""
    return ("<a:moveTo>{}</a:moveTo>".format(_pt(*points[0]))
            + "".join("<a:lnTo>{}</a:lnTo>".format(_pt(*p)) for p in points[1:]) + "<a:close/>")


def squiggle(slide, x, y, w, h, color, *, waves=4, line_w=3.0, loud=False):
    """Ornament — A hand-drawn WAVE line — under a claim, between sections. `waves` full periods across `w`."""
    _need(w=w, h=h)
    _count(waves=waves)
    seg = _U / (2 * waves)
    d = ["<a:moveTo>{}</a:moveTo>".format(_pt(0, _U / 2))]
    for i in range(2 * waves):
        x0, x1 = i * seg, (i + 1) * seg
        yy = 0 if i % 2 == 0 else _U
        d.append("<a:cubicBezTo>{}{}{}</a:cubicBezTo>".format(
            _pt(x0 + seg / 3, yy), _pt(x1 - seg / 3, yy), _pt(x1, _U / 2)))
    path = '<a:path w="{u}" h="{u}" fill="none">{d}</a:path>'.format(u=_U, d="".join(d))
    return _shape(slide, x, y, w, h, path, line=color, line_w=line_w, loud=loud)


def scribble(slide, x, y, w, h, color, *, loops=3, line_w=2.0, seed=0, loud=False):
    """Ornament — A looping pen COIL travelling across `w` — `loops` overlapping loops, a little uneven."""
    _need(w=w, h=h)
    _count(loops=loops)
    rnd = random.Random(seed)
    pts = []
    steps = loops * 8
    for i in range(steps + 1):
        t = i / steps
        a = 2 * math.pi * loops * t
        jit = 1.0 + 0.08 * (rnd.random() - 0.5)
        px = _U * (0.10 + 0.80 * t) + _U * 0.10 * math.cos(a + math.pi) * jit
        py = _U * 0.5 + _U * 0.42 * math.sin(a) * jit
        pts.append((min(max(px, 0), _U), min(max(py, 0), _U)))
    path = '<a:path w="{u}" h="{u}" fill="none"><a:moveTo>{m}</a:moveTo>{c}</a:path>'.format(
        u=_U, m=_pt(*pts[0]), c=_smooth(pts))
    return _shape(slide, x, y, w, h, path, line=color, line_w=line_w, loud=loud)


def brush_stroke(slide, x, y, w, h, color, *, seed=0, rotation=0.0, loud=False):
    """Ornament — A dry-brush SWASH: a filled band with ragged edges and tapered ends — behind a word, under
    a number. Deterministic for a given `seed`."""
    _need(w=w, h=h)
    rnd = random.Random(seed)
    n = 18
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        half = _U * 0.5 * math.sin(math.pi * t) ** 0.6
        top.append((_U * t, _U * 0.5 - half * (0.86 + 0.14 * rnd.random())))
        bot.append((_U * t, _U * 0.5 + half * (0.86 + 0.14 * rnd.random())))
    path = '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=_U, d=_ring(top + bot[::-1]))
    return _shape(slide, x, y, w, h, path, fill=color, loud=loud, rotation=rotation)


def tape(slide, x, y, w, h, color, *, rotation=-4.0, alpha=0.75, seed=0, loud=False, holds=None):
    """Ornament — A strip of translucent TAPE with torn (zig-zag) short ends — holding a print to the page.

    `holds=<the picture or card it is stuck to>` declares that overlap — holding the print IS the
    overlap — after checking the tape really touches it (a `holds=` it does not touch RAISES).
    Without `holds=` nothing is declared, so tape laid across any other solid shape is still an
    OVERLAP: a helper that declared for itself on every call was a standing waiver against ANY
    shape (final review, 2026-10-03). 🔴 Where it sits on the PAGE
    ground it is a small mark under WCAG 1.4.11: a pale washi tone on a light page (e.g. F2D16B on
    F4EEE3, 1.29:1) is a NON-TEXT CONTRAST finding, which the hand-off gate holds the deck on —
    pick a tape colour at >= 3:1 against the page, keep it over the picture, or, when it is pure
    ornament, say so: `dk.decorative(tape_shape, "<why nothing rides on it>")`."""
    _need(w=w, h=h)
    if not 0.0 < alpha <= 1.0:
        raise ValueError("tape(): alpha must be within (0, 1]")
    rnd = random.Random(seed)
    teeth = 6
    # a simple ring: down the torn RIGHT end (top -> bottom), then up the torn LEFT end
    # (bottom -> top); closing it draws the straight top edge, the jump between the two ends the
    # straight bottom edge. Alternating in/out makes the zig-zag; the jitter makes it torn.
    right = [(_U - _U * (0.05 * (i % 2) + 0.02 * rnd.random()), _U * i / teeth)
             for i in range(teeth + 1)]
    left = [(_U * (0.05 * (i % 2) + 0.02 * rnd.random()), _U * (teeth - i) / teeth)
            for i in range(teeth + 1)]
    path = '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=_U, d=_ring(right + left))
    sh = _shape(slide, x, y, w, h, path, fill=color, alpha=alpha, loud=loud, rotation=rotation)
    if holds is None:
        return sh
    # The declaration composes with the motif tag and waives the solid-vs-solid GEOMETRY only —
    # OCCLUSION, contrast and TEXT_OVER_MOTIF still apply (tape laid over text is still caught).
    if dk._overlap_area(dk._placed_box(sh), dk._placed_box(holds)) <= 0.0:
        raise ValueError("tape(holds=…): the tape does not touch the shape it claims to hold — "
                         "move it onto the print's edge")
    return dk.overlap_intent(sh, "tape holds the print it is stuck to")


def scallop(slide, x, y, d, color, *, bumps=12, depth=0.10, loud=False):
    """Ornament — A SCALLOPED disc of diameter `d` — the badge behind a number or a 'new' stamp.

    A badge smaller than ~3% of the canvas is a DEVICE to the motif checks, so a number set on it
    is reported as TEXT_OVER_MOTIF (WARN) — the rule is right in general (a caption laid across a
    ring is a defect). When the number IS the badge's job, declare it on the TEXT — the check
    reads the declaration from the text shape, not from the motif:
        orn.scallop(s, x, y, 1.6, "2F5BEA")
        n = dk.text(s, x, y, 1.6, 1.6, [[("12", 40, dk.WHITE, True, False)]],
                    align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE)
        dk.overlap_intent(n, "the count sits on its badge")
    """
    _need(d=d)
    _count(bumps=bumps)
    if not 0.0 < depth < 0.5:
        raise ValueError("scallop(): depth must be within (0, 0.5)")
    n = bumps * 4
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 0.5 * (1.0 - depth + depth * abs(math.cos(bumps * a / 2.0)))
        pts.append((_U * (0.5 + r * math.cos(a)), _U * (0.5 + r * math.sin(a))))
    path = '<a:path w="{u}" h="{u}"><a:moveTo>{m}</a:moveTo>{c}<a:close/></a:path>'.format(
        u=_U, m=_pt(*pts[0]), c=_smooth(pts, closed=True))
    return _shape(slide, x, y, d, d, path, fill=color, loud=loud)
