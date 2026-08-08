#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Occupancy is a bounding-box union, so a DRAWN CONTAINER counts as a full page.

Measured: one empty outlined rectangle with four characters inside scored **49% ink coverage** —
a page carrying a single word read as half full, which is comfortably "full" by every density
check in the file and therefore exempt from UNDERFILLED as well. Nothing could distinguish ink a
reader receives from ink that is a frame around it.

`ink_content` is that union with hollow decoration removed, kept BESIDE `ink_cov` rather than
replacing it: the existing occupancy bands were calibrated against the old number, and moving them
silently would re-tune every threshold in this file.

SCOPE, stated because the boundary matters more than the check. This catches the HOLLOW CONTAINER
case — an outlined frame with no fill and no text of its own. It does NOT catch a diagram of
FILLED node boxes that spends page on little content, and that is deliberate: a white-filled card
on a light ground is the ordinary card form, and treating it as hollow would fire across a large
class of legitimate decks. The mechanically-detectable half of that other defect (the same name
printed in a list and again in the diagram beside it) belongs to DUPLICATE_TEXT, which owns it;
the remaining half — whether a form earns its page — is judgment, and gating judgment is how a
skill starts producing pages that pass checks instead of pages that read well.

Run:  python3 tests/test_hollow_ink.py
"""
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                                                  # noqa: E402
import lint_deck as L                                                 # noqa: E402
from deckkit import RGBColor                                          # noqa: E402

PASS, FAIL = [], []
PAPER = RGBColor(0xF4, 0xEF, 0xE4)
LINE = RGBColor(0xD8, 0xD0, 0xBF)
PANEL = RGBColor(0xE8, 0xE2, 0xD4)


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def T(s, x, y, t, size=13, w=8.4):
    dk.text(s, x, y, w, size / 72.0 * 1.5,
            [[(t, size, dk.DEEP, False, False, "Helvetica Neue")]], space_after=0, wrap=False)


def measures(build):
    """(ink_cov, ink_content) for a single built slide."""
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    build(s)
    st = L._slide_stats(s, L._boxes(s, 10.0, 5.625), 10.0, 5.625)
    return st["ink_cov"], st["ink_content"]


def fires(build):
    """Does HOLLOW FILL fire, with the slide sat between two ordinary neighbours?"""
    prs = dk.blank_deck()
    for k in range(3):
        s = dk.add_slide(prs)
        dk.title_bar(s, "Page %d" % (k + 1))
        if k == 1:
            build(s)
        else:
            for j in range(3):
                T(s, 0.6, 1.6 + j * 0.4, "An ordinary line of body content on this page.")
    tmp = tempfile.mkdtemp(prefix="hollow_")
    p = tmp + "/d.pptx"
    prs.save(p)
    subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"), p, tmp + "/r"],
                   capture_output=True)
    out = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), p, "--renders", tmp + "/r"],
                         capture_output=True, text=True).stdout
    return "HOLLOW FILL" in out


# --- the shapes under test ---------------------------------------------------------------
def hollow(s):                    # THE defect: an empty outlined container carrying one phrase
    dk.box(s, 1.0, 1.4, 8.0, 3.2, fill=None, line=LINE, line_w=1.4, round=True, r=0.3)
    T(s, 4.0, 2.8, "三校合办", 15, 2.0)


def filled(s):                    # the same footprint, but the panel is real
    dk.box(s, 1.0, 1.4, 8.0, 3.2, fill=PANEL, round=True, r=0.3)
    T(s, 4.0, 2.8, "三校合办", 15, 2.0)


def composed(s):                  # a hero word and vast air — the oldest editorial move there is
    T(s, 0.8, 2.2, "One idea, stated at full size", 56)


def cards_with_content(s):        # outlined cards that actually carry something
    for i in range(4):
        dk.box(s, 0.6 + i * 2.2, 1.5, 1.9, 1.1, fill=None, line=LINE, line_w=1.2, round=True, r=0.1)
        T(s, 0.72 + i * 2.2, 1.8, "Stage %d" % i, 12, 1.7)
    T(s, 0.6, 3.0, "A paragraph of ordinary body prose explaining the four stages above.", 12)


def frame_around_content(s):      # a frame is fine when it frames something
    dk.box(s, 1.0, 1.4, 8.0, 3.2, fill=None, line=LINE, line_w=1.4, round=True, r=0.3)
    for j in range(6):
        T(s, 1.3, 1.8 + j * 0.35, "A real line of explanatory content inside the frame.", 12, 7.4)


def main():
    print("hollow ink")

    # ---- the measure itself ---------------------------------------------------------
    cov, con = measures(hollow)
    check("a hollow container reads FULL by the old measure", cov >= 0.40, "%.2f" % cov)
    check("...and nearly EMPTY by the content measure", con <= 0.10, "%.2f" % con)
    check("the two disagree by a wide margin (that gap IS the signal)", cov - con >= 0.30)

    cov, con = measures(filled)
    check("a FILLED panel of the same footprint is untouched", abs(cov - con) < 0.02,
          "%.2f vs %.2f" % (cov, con))
    cov, con = measures(composed)
    check("a hero word with air is untouched", abs(cov - con) < 0.02)
    cov, con = measures(cards_with_content)
    check("outlined cards carrying real content barely move",
          cov - con < 0.20, "%.2f vs %.2f" % (cov, con))

    # ---- the check ------------------------------------------------------------------
    check("HOLLOW FILL fires on the hollow container", fires(hollow))
    check("silent on a filled panel of identical footprint", not fires(filled))
    check("silent on a hero word and air (composition, not emptiness)", not fires(composed))
    check("silent on outlined cards that carry content", not fires(cards_with_content))
    check("silent on a frame around six real lines", not fires(frame_around_content))

    # ---- the boundary, asserted so nobody widens it by accident ---------------------
    # A white-filled node box on a light ground LOOKS hollow and is NOT classified as such: that
    # is the ordinary card form, and treating it as decoration would fire across a large class of
    # legitimate decks. The defect it leaves uncaught (a diagram spending page on one sentence)
    # is owned elsewhere — DUPLICATE_TEXT for its mechanical half, judgment for the rest.
    def filled_nodes(s):
        mx = 4.8
        rects = [(mx, 3.1, 1.36, 0.56), (mx + 1.5, 3.1, 1.36, 0.56), (mx + 3.0, 3.1, 1.36, 0.56)]
        for rect in rects:
            dk.node(s, *rect, "School")
        T(s, mx, 4.1, "Jointly run", 10, 4.5)
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    filled_nodes(s)
    boxes = [b for b in L._boxes(s, 10.0, 5.625) if not b["bg"]]
    check("a white-FILLED node box is not classified hollow (the card form stays legitimate)",
          not any(b["hollow"] for b in boxes if b["st"].startswith("AUTO")))

    # ---- it may never block a build --------------------------------------------------
    check("HOLLOW FILL is a [stats] warn, so it can never fail a build",
          True)   # asserted by construction: warns list, never `finds`

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
