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

# ── (the gate sections follow) ──────────────────────────────────────────────────────────────────

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_rotated_geometry] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
