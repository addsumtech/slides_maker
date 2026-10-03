#!/usr/bin/env python3
"""rotgeom — where a ROTATED shape actually paints, for both geometry gates.

OOXML stores a rotated shape as its UNROTATED frame (`a:off`/`a:ext`) plus `rot`, applied
CLOCKWISE about the frame's centre. Both gates measured the frame. Measured on a two-slide probe,
2026-10-03: a 5.0 x 0.5in vertical margin label rotated 90deg and sitting inside the canvas was a
CRITICAL `OFF_CANVAS` at build time (so `strict=True` refused to save a correct deck) and a hard
`OVERFLOW [right+1.87]` after the render; the same label laid straight through a paragraph of body
copy produced ZERO findings in either gate. Wrong in both directions, from one cause.

One definition, imported by `lint_deck.py` and `deckkit.lint_layout`, so the two gates cannot
disagree about where a rotated shape is:

  · a multiple of 90deg -> `placed()` is EXACT (the sides swap about the centre);
  · any other angle     -> `placed()` is the axis-aligned box of the rotated corners (it can only
                           over-state), and `overlap()` is the EXACT intersection of two rotated
                           rectangles, for the checks that ask how much two shapes cover each other.

Pure geometry: no pptx import, inches in, inches out, y grows DOWN (screen space).
"""
from __future__ import annotations

import math

_EPS_DEG = 0.01


def norm(rot):
    """Degrees in [0, 360). Within 0.01deg of a full turn is 0. Anything non-numeric is 0."""
    try:
        r = float(rot or 0.0) % 360.0
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if (r < _EPS_DEG or r > 360.0 - _EPS_DEG) else r


def is_rotated(rot):
    return norm(rot) != 0.0


def is_axis(rot):
    """True for 0 / 90 / 180 / 270 (within 0.01deg) — the angles whose placed box is exact."""
    r = norm(rot)
    return abs(r - 90.0 * round(r / 90.0)) < _EPS_DEG


def rotate(points, cx, cy, rot):
    """Rotate points CLOCKWISE on a y-down screen by `rot` degrees about (cx, cy)."""
    a = math.radians(norm(rot))
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca)
            for (x, y) in points]


def rect_poly(l, t, w, h):
    """The four corners of an axis-aligned rect: TL, TR, BR, BL."""
    return [(l, t), (l + w, t), (l + w, t + h), (l, t + h)]


def corners(l, t, w, h, rot):
    """The four PAINTED corners of frame (l, t, w, h) rotated by `rot` about its own centre."""
    return rotate(rect_poly(l, t, w, h), l + w / 2.0, t + h / 2.0, rot)


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def placed(l, t, w, h, rot):
    """(l, t, w, h) of what the rotated frame paints. Unrotated -> the input, untouched."""
    r = norm(rot)
    if r == 0.0:
        return (l, t, w, h)
    if is_axis(r):
        if round(r / 90.0) % 2:                      # 90 / 270: the sides swap about the centre
            cx, cy = l + w / 2.0, t + h / 2.0
            return (cx - h / 2.0, cy - w / 2.0, h, w)
        return (l, t, w, h)                          # 180: same footprint
    return bbox(corners(l, t, w, h, r))


def _signed_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def area(poly):
    return abs(_signed_area(poly)) if len(poly) >= 3 else 0.0


def _clip(subject, clipper):
    """Sutherland-Hodgman: `subject` clipped to the CONVEX polygon `clipper`."""
    orient = 1.0 if _signed_area(clipper) >= 0 else -1.0

    def inside(p, a, b):
        return orient * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= -1e-12

    def cross(p1, p2, a, b):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = a
        x4, y4 = b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-15:
            return p2
        u = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + u * (x2 - x1), y1 + u * (y2 - y1))

    out = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(cross(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(cross(s, e, a, b))
            s = e
    return out


def overlap(pa, pb):
    """(area, (l, t, w, h) of the intersection) of two CONVEX polygons; (0.0, None) if disjoint."""
    poly = _clip(pa, pb)
    if len(poly) < 3:
        return 0.0, None
    a = area(poly)
    if a <= 1e-12:
        return 0.0, None
    return a, bbox(poly)


def contains_point(poly, pt):
    """Point inside a CONVEX polygon; the boundary counts as inside."""
    orient = 1.0 if _signed_area(poly) >= 0 else -1.0
    x, y = pt
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if orient * ((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) < -1e-12:
            return False
    return True


def centreline(poly, w, h):
    """The long axis of a rotated frame as a segment ((x0, y0), (x1, y1)). `poly` is its four
    painted corners in frame order (TL, TR, BR, BL); `w`/`h` the frame size — the long axis runs
    along whichever is larger. This is what a thin tilted RULE draws."""
    tl, tr, br, bl = poly
    if w >= h:
        return (((tl[0] + bl[0]) / 2.0, (tl[1] + bl[1]) / 2.0),
                ((tr[0] + br[0]) / 2.0, (tr[1] + br[1]) / 2.0))
    return (((tl[0] + tr[0]) / 2.0, (tl[1] + tr[1]) / 2.0),
            ((bl[0] + br[0]) / 2.0, (bl[1] + br[1]) / 2.0))


def seg_in_rect(p, q, rect):
    """Length of segment p-q inside the axis-aligned rect (l, t, w, h) — Liang-Barsky clipping.
    0.0 when the segment misses the rect or the rect is empty."""
    l, t, w, h = rect
    if w <= 0 or h <= 0:
        return 0.0
    x0, y0 = p
    dx, dy = q[0] - x0, q[1] - y0
    u0, u1 = 0.0, 1.0
    for pk, qk in ((-dx, x0 - l), (dx, l + w - x0), (-dy, y0 - t), (dy, t + h - y0)):
        if pk == 0:
            if qk < 0:
                return 0.0
            continue
        r = qk / pk
        if pk < 0:
            u0 = max(u0, r)
        else:
            u1 = min(u1, r)
        if u0 > u1:
            return 0.0
    return (u1 - u0) * math.hypot(dx, dy)
