#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A label running into the bar beside it was invisible to every gate.

`TEXT_OVERLAP` measures text against TEXT. A bar, a chip, a node, a swatch is geometry, so a
caption grazing one produces no finding anywhere — the same structural blindness
`TEXT_OVER_MOTIF` was written for, except that check only sees shapes the author remembered to
TAG, and nobody tags a bar.

Measured on a delivered 12-page deck: a right-aligned row label ran 0.015in² into the negative
bar beside it. Build-time `lint_layout` reported clean; render-time `lint_deck.py` reported
clean; it was found by a human looking at the PNG — twice, because the first repair shortened
the string and the label still grazed. That second miss is the useful part: the fix has to move
the label COLUMN'S EDGE, derived from how far the mark can actually reach, and shortening text
only moves the collision somewhere else. The message says so.

🔴 The hard half of this check is what it must stay SILENT on. A value printed inside its own
bar is text over a filled shape too, and it is correct design — this library's own components do
it, and the deck that produced the defect does it on three slides. So the discriminator is
CONTAINMENT, not overlap: ink mostly inside the shape is a label ON it; ink mostly outside with
a corner dipping in is a collision. Both directions are asserted below, and the silent half is
the load-bearing one: a check that fires on good decks is worse than no check.

Run:  python3 tests/test_graze_contract.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import deckkit as dk                                                  # noqa: E402
from deckkit import RGBColor                                          # noqa: E402

PASS, FAIL = [], []
PAPER = RGBColor(0xF5, 0xF1, 0xE6)
BAR = RGBColor(0xB4, 0x46, 0x2A)


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def grazes(prs):
    return [f for f in dk.lint_layout(prs, verbose=False) if f[2] == "TEXT_GRAZES_SHAPE"]


def deck():
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.box(s, 0, 0, 10, 5.625, fill=PAPER)
    return prs, s


def label(s, x, y, w, txt, *, align=None):
    return dk.text(s, x, y, w, 0.28,
                   [[(txt, 12.5, dk.DEEP, False, False, "Helvetica Neue")]],
                   space_after=0, wrap=False,
                   align=align or dk.PP_ALIGN.RIGHT)


def main():
    print("graze contract")
    dk.FONT, dk.EAFONT = "Helvetica Neue", "Hiragino Sans GB"

    # ---- the measured defect --------------------------------------------------------
    prs, s = deck()
    dk.box(s, 3.33, 2.0, 0.28, 0.34, fill=BAR)     # a negative bar reaching left of the axis
    label(s, 0.62, 2.03, 2.80, "建筑物 structures")  # right edge 3.42 > the bar's 3.33
    g = grazes(prs)
    check("a row label running into the bar beside it is reported", len(g) == 1, g)
    check("...and the message names the real fix (the column edge, not the string)",
          g and "column's edge" in g[0][3] and "shortening the string" in g[0][3])

    # the first repair in the real deck: shorten the text. It still grazed — assert that.
    prs, s = deck()
    dk.box(s, 3.33, 2.0, 0.28, 0.34, fill=BAR)
    label(s, 0.62, 2.03, 2.80, "建筑物")
    check("shortening the string does NOT silence it (the box still reaches)",
          len(grazes(prs)) == 1)

    # the real fix: derive the column edge from how far the mark can reach
    prs, s = deck()
    dk.box(s, 3.33, 2.0, 0.28, 0.34, fill=BAR)
    label(s, 0.62, 2.03, 3.33 - 0.14 - 0.62, "建筑物 structures")
    check("deriving the column edge from the data DOES silence it", grazes(prs) == [])

    # ---- the silent half, which is the load-bearing one ------------------------------
    prs, s = deck()
    dk.box(s, 3.0, 1.6, 1.28, 1.9, fill=dk.DEEP)
    dk.text(s, 3.0, 1.6, 1.28, 1.9, [[("3.2%", 22, PAPER, True, False, "Helvetica Neue")]],
            space_after=0, wrap=False, align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE)
    check("a value printed INSIDE its own bar is silent (this library does it everywhere)",
          grazes(prs) == [])

    prs, s = deck()
    dk.box(s, 3.0, 2.0, 1.4, 0.34, fill=dk.DEEP)
    dk.text(s, 3.02, 2.0, 1.36, 0.34, [[("Input", 11, PAPER, True, False, "Helvetica Neue")]],
            space_after=0, wrap=False, align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE)
    check("a centred chip label overhanging its snug chip by a hair is silent",
          grazes(prs) == [])

    prs, s = deck()
    dk.box(s, 3.60, 2.0, 1.0, 0.34, fill=BAR)
    label(s, 0.62, 2.03, 2.80, "设备投资")           # ends 3.42, bar starts 3.60 — a real gap
    check("a label with a real gap to the mark is silent", grazes(prs) == [])

    prs, s = deck()
    dk.box(s, 0, 0, 10, 5.625, fill=dk.DEEP)        # a full-bleed ground, painted over
    dk.text(s, 0.8, 2.0, 6.0, 0.4, [[("A title on a dark cover", 24, PAPER,
                                      True, False, "Helvetica Neue")]], space_after=0, wrap=False)
    check("text on a full-bleed ground is silent (a ground is not something to graze)",
          grazes(prs) == [])

    prs, s = deck()
    dk.box(s, 0.6, 1.4, 8.8, 3.0, fill=RGBColor(0xEE, 0xEA, 0xDE))   # a half-canvas panel
    dk.text(s, 0.9, 1.7, 6.0, 0.4, [[("Text on a big panel", 16, dk.DEEP,
                                      False, False, "Helvetica Neue")]], space_after=0, wrap=False)
    check("text on a half-canvas panel is silent (that is a ground too)", grazes(prs) == [])

    prs, s = deck()
    dk.box(s, 3.33, 2.0, 0.28, 0.34, fill=BAR)
    t = label(s, 0.62, 2.03, 2.80, "建筑物 structures")
    dk.overlap_intent(t, "标签压在柱上是这一页刻意的构图，不是碰撞")
    check("a DECLARED overlap is silent", grazes(prs) == [])

    prs, s = deck()
    dk.register_mark(s, "arcs", corner=(3.0, 1.6), size=2.0)
    dk.text(s, 3.2, 2.4, 3.0, 0.4, [[("crossing the motif", 16, dk.DEEP,
                                      False, False, "Helvetica Neue")]], space_after=0, wrap=False)
    codes = {f[2] for f in dk.lint_layout(prs, verbose=False)}
    check("a motif keeps its OWN message (TEXT_OVER_MOTIF), not this one",
          "TEXT_OVER_MOTIF" in codes and "TEXT_GRAZES_SHAPE" not in codes, codes)

    prs, s = deck()
    dk.box(s, 3.33, 2.0, 0.28, 0.34, fill=None,
           line=RGBColor(0x88, 0x88, 0x88), line_w=1.0)   # outline only, no fill
    label(s, 0.62, 2.03, 2.80, "建筑物 structures")
    check("an UNFILLED outline is not a mark to graze (no ink to collide with)",
          grazes(prs) == [])

    # ---- it may never block a build ---------------------------------------------------
    prs, s = deck()
    dk.box(s, 3.33, 2.0, 0.28, 0.34, fill=BAR)
    label(s, 0.62, 2.03, 2.80, "建筑物 structures")
    try:
        dk.lint_layout(prs, verbose=False, strict=True)
        check("it is a WARN — strict=True still saves", True)
    except RuntimeError as exc:
        check("it is a WARN — strict=True still saves", False, str(exc)[:70])

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
