#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A connector docked on a box's CENTRE — the arrow crossing the box interior — was invisible to
the very check written to catch it.

`CONNECTOR_IN_BOX` reads a connector's begin/end points and flags one that lands in a block's
central zone while drawn above it. But it only ever iterated `info`, and `info` is built by
skipping any shape whose `_bbox_in` is None — and `_bbox_in` returns None for a zero-area shape.
A VERTICAL or HORIZONTAL connector has zero width or height, so every axis-aligned connector was
dropped before the check ran. That is the common case: flow arrows, feedback loops, and every
`elbow_connector` segment are axis-aligned. The check fired only on the rare diagonal connector.

Measured on a real deck: a feedback loop built with `elbow_connector(loop_path(x, x, y_centre, …))`
emanated from the CENTRE of two boxes and crossed both interiors. Build-time `lint_layout` reported
clean and the deck shipped; a human caught it in the render. The fix captures every connector's
ENDPOINTS regardless of bbox, so the check sees axis-aligned + elbow connectors too.

🔴 The load-bearing half is what it must stay SILENT on: an edge-docked connector
(`connect_boxes`/`edge_point`/`hub_spokes`), a connector drawn BELOW the block it touches (the
node paints over the seam — the covered pattern), and this library's own `hub_spoke`/`flow_chain`
figures. A check that fires on correct diagrams is worse than no check.

Run:  python3 tests/test_connector_in_box.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import deckkit as dk                                                  # noqa: E402
from deckkit import RGBColor                                          # noqa: E402

PASS, FAIL = [], []
INK = RGBColor(0x1E, 0x21, 0x27)
BLUE = RGBColor(0x3B, 0x6F, 0xB0)
RED = RGBColor(0xE4, 0x48, 0x3D)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def cib(prs):
    return [f for f in dk.lint_layout(prs, verbose=False) if f[2] == "CONNECTOR_IN_BOX"]


def deck():
    prs = dk.blank_deck()
    return prs, dk.add_slide(prs)


def box_node(s, rect):
    dk.node(s, *rect, "N", shape="roundrect", fill=WHITE, line=BLUE, tcolor=INK)


def ctr(r):
    return (r[0] + r[2] / 2.0, r[1] + r[3] / 2.0)


def main():
    print("connector-in-box contract")
    A = (1.2, 2.55, 1.6, 0.9)
    B = (6.0, 2.55, 1.6, 0.9)

    # ---- the measured defect: axis-aligned + elbow connectors from a box CENTRE ----------
    prs, s = deck()
    box_node(s, A)
    ca = ctr(A)
    dk.connector(s, (ca[0], ca[1]), (ca[0], ca[1] + 1.4), color=RED)   # VERTICAL, begins at centre
    check("a VERTICAL connector docked on a box centre is caught (was invisible)", len(cib(prs)) >= 1)

    prs, s = deck()
    box_node(s, A)
    dk.connector(s, (ca[0], ca[1]), (ca[0] + 1.4, ca[1]), color=RED)   # HORIZONTAL from centre
    check("a HORIZONTAL connector docked on a box centre is caught", len(cib(prs)) >= 1)

    prs, s = deck()
    box_node(s, A)
    box_node(s, B)
    cb = ctr(B)
    # the exact deck-7 bug: an elbow feedback loop whose terminal docks are the two box CENTRES
    dk.elbow_connector(s, dk.loop_path(ca[0], cb[0], ca[1], ca[1] + 0.8), style="dotted", color=RED)
    check("an ELBOW loop docked on two box centres is caught (one per box)", len(cib(prs)) == 2)

    # ---- and it is a CRITICAL, so strict=True must refuse to save -------------------------
    prs, s = deck()
    box_node(s, A)
    dk.connector(s, (ca[0], ca[1]), (ca[0], ca[1] + 1.4), color=RED)
    raised = False
    try:
        dk.lint_layout(prs, verbose=False, strict=True)
    except RuntimeError:
        raised = True
    check("it is a CRITICAL — strict=True refuses to save a centre-docked connector", raised)

    # ---- the load-bearing half: correct diagrams must stay SILENT ------------------------
    prs, s = deck()
    box_node(s, A)
    box_node(s, B)
    dk.connect_boxes(s, A, B, color=BLUE)                    # edge-docked — the right way
    check("connect_boxes (edge-docked) is silent", cib(prs) == [])

    prs, s = deck()
    box_node(s, A)
    box_node(s, B)
    y_edge = A[1] + A[3]                                     # the boxes' BOTTOM edge (the fix)
    dk.elbow_connector(s, dk.loop_path(ca[0], cb[0], y_edge, y_edge + 0.8), style="dotted", color=RED)
    check("an elbow loop docked on the box BOTTOM EDGE is silent", cib(prs) == [])

    prs, s = deck()
    # covered pattern: the connector is added BEFORE the node, so the node paints over the seam
    dk.connector(s, (ca[0], ca[1]), (ca[0], ca[1] + 1.4), color=RED)
    box_node(s, A)
    check("a centre-docked connector added BEFORE its node (covered) is silent", cib(prs) == [])

    prs, s = deck()
    dk.hub_spoke(s, 5.0, 2.9, 2.1, "Core", ["A", "B", "C", "D", "E"])
    check("hub_spoke (this library's own radial figure) is silent", cib(prs) == [])

    prs, s = deck()
    dk.flow_chain(s, 0.7, 2.5, 8.5, 1.0, ["In", "Mid", "Out"])
    check("flow_chain (edge-docked internally) is silent", cib(prs) == [])

    # loop_between: the rect-aware, edge-docked-by-construction loop — the ergonomic fix that makes
    # the SAFE feedback-loop the easy one (vs. loop_path + a raw box centre).
    prs, s = deck()
    box_node(s, A)
    box_node(s, B)
    segs = dk.loop_between(s, A, B, side="bottom", label="revise", color=RED)
    check("loop_between (edge-docked U loop) is silent", cib(prs) == [])
    dock_y = segs[0].begin_y / 914400.0
    check("loop_between docks on the box EDGE, not its centre",
          abs(dock_y - (A[1] + A[3])) < 0.01, (dock_y, A[1] + A[3]))

    prs, s = deck()
    box_node(s, A)
    box_node(s, B)
    dk.loop_between(s, A, B, side="top", color=RED)
    check("loop_between side='top' is silent", cib(prs) == [])

    prs, s = deck()
    box_node(s, A)
    box_node(s, B)
    raised = False
    try:
        dk.loop_between(s, A, B, side="sideways")
    except ValueError:
        raised = True
    check("loop_between rejects an unknown side", raised)

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
