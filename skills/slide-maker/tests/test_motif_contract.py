#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The signature motif had no machine-readable existence, so its two contracts were unmeasurable.

The skill asks for an unusually thoughtful motif system: a NAMED device with a stated meaning, a
STRANGER TEST it must pass at first appearance, a budget of <=3 LOUD appearances (a device stamped
on every page is a template tell, not a signature), a quiet register signature that MAY repeat on
every page, and a `carried_by` clause naming slides where the idea does structural work. All of it
lived in prose. Measured on a real 14-page build:

  · the quiet register signature was hand-rolled in eight lines, offset each ring in x but NOT in
    y, and therefore drew three INTERLOCKING circles — a Venn diagram — in the corner of twelve
    pages. No gate knows what a motif should look like; a human found it by opening a PNG.
  · a subtitle was laid straight across the cover motif. `TEXT_OVERLAP` measures text against TEXT
    and a motif is geometry, so the build-time lint reported ZERO findings. The defect was caught
    by eye once, written down as a build rule, and recurred on the next page — the signature of a
    rule with no gate.
  · nothing could say whether the deck's motif appeared 3 times or 11, because nothing could say
    which shapes WERE the motif.

`tag_motif` / `register_mark` give the device an identity; `TEXT_OVER_MOTIF` and `MOTIF_BUDGET`
are what that identity makes possible. Both are WARN, never CRITICAL — text ON a device is
ordinary editorial design, so the gate reports the collision and lets the author declare it.

Both directions are asserted throughout, and the silent cases are the load-bearing half: a deck
that never uses this vocabulary must never be punished for it.

Run:  python3 tests/test_motif_contract.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                                                  # noqa: E402
from deckkit import RGBColor                                          # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def codes(prs, code):
    return [f for f in dk.lint_layout(prs, verbose=False) if f[2] == code]


def txt(s, x, y, t, size=16):
    dk.text(s, x, y, 8.4, size / 72.0 * 1.5,
            [[(t, size, dk.DEEP, False, False, "Helvetica Neue")]], space_after=0, wrap=False)


def main():
    print("motif contract")

    # ---- register_mark draws what it claims -------------------------------------------
    for kind, kw in (("arcs", {}), ("rule", {}), ("ticks", {}),
                     ("ordinal", {"text": "03"}), ("grid", {})):
        for corner in ("tl", "tr", "bl", "br"):
            prs = dk.blank_deck()
            s = dk.add_slide(prs)
            out = dk.register_mark(s, kind, corner=corner, **kw)
            off = [x for x in out if x.left < 0 or x.top < 0
                   or (x.left + x.width) / 914400.0 > 10.001
                   or (x.top + x.height) / 914400.0 > 5.626]
            check("%s/%s builds, tagged, on canvas" % (kind, corner),
                  out and all(dk._is_motif(x) for x in out) and not off, off)

    # THE bug this helper exists to make unrepresentable: rings that are not concentric.
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    out = dk.register_mark(s, "arcs", rings=4)
    centres = {"%.3f,%.3f" % ((x.left + x.width / 2.0) / 914400.0,
                              (x.top + x.height / 2.0) / 914400.0) for x in out}
    check("arcs share ONE centre (the interlocking-circles bug is unrepresentable)",
          len(centres) == 1, centres)

    for bad, why in ((lambda: dk.register_mark(s, "swoosh"), "unknown kind"),
                     (lambda: dk.register_mark(s, "arcs", corner="middle"), "unknown corner"),
                     (lambda: dk.register_mark(s, "ordinal"), "ordinal with no text")):
        try:
            bad()
            check("%s raises rather than drawing something else" % why, False)
        except ValueError:
            check("%s raises rather than drawing something else" % why, True)

    # ---- TEXT_OVER_MOTIF ---------------------------------------------------------------
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.register_mark(s, "arcs", corner=(3.0, 1.0), size=4.0, loud=True)
    txt(s, 0.8, 2.6, "A subtitle running straight across the ring")
    found = codes(prs, "TEXT_OVER_MOTIF")
    check("a caption crossing the motif is reported", len(found) == 1, found)
    check("the report says how to declare it deliberate",
          found and "overlap_intent" in found[0][3])

    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.register_mark(s, "arcs", corner="tr")
    txt(s, 0.8, 2.6, "A subtitle nowhere near the corner mark")
    check("text that does NOT cross the motif is silent", codes(prs, "TEXT_OVER_MOTIF") == [])

    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.register_mark(s, "arcs", corner=(3.0, 1.0), size=4.0)
    dk.text(s, 0.8, 2.6, 8.4, 0.4,
            [[("A display word riding the device", 16, dk.DEEP, False, False, "Helvetica Neue")]],
            space_after=0, wrap=False)
    dk.overlap_intent(list(s.shapes)[-1], "the ring is the ground the caption rides")
    check("a DECLARED overlap is silent (the author said it is the composition)",
          codes(prs, "TEXT_OVER_MOTIF") == [])

    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.tag_motif(dk.box(s, 0, 0, 10, 5.625, fill=None, line=RGBColor(0xEE, 0xEE, 0xEE), line_w=1.0))
    txt(s, 0.8, 2.6, "A subtitle over a full-bleed plate")
    check("a FULL-BLEED motif is a ground, not an object — silent",
          codes(prs, "TEXT_OVER_MOTIF") == [])

    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.box(s, 3.0, 1.0, 4.0, 4.0, fill=None, line=RGBColor(0xD8, 0xD0, 0xBF),
           line_w=1.2, round=True, r=2.0)
    txt(s, 0.8, 2.6, "A subtitle across an UNTAGGED ring")
    check("a deck that never uses the vocabulary is never punished for it",
          codes(prs, "TEXT_OVER_MOTIF") == [])

    # a watermark numeral is decorative by its own tag and must not read as crossed text
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.register_mark(s, "arcs", corner=(3.0, 1.0), size=4.0)
    dk.ghost_numeral(s, 3.2, 1.2, 3.6, 3.6, "01")
    check("a ghost numeral over the motif is not a text collision",
          codes(prs, "TEXT_OVER_MOTIF") == [])

    # ---- MOTIF_BUDGET ------------------------------------------------------------------
    for n, should in ((3, False), (4, True), (7, True)):
        prs = dk.blank_deck()
        for _ in range(n):
            sl = dk.add_slide(prs)
            dk.register_mark(sl, "arcs", corner="tr", loud=True)
        got = codes(prs, "MOTIF_BUDGET")
        check("loud motif on %d slides -> %s" % (n, "reported" if should else "silent"),
              bool(got) == should, got)

    prs = dk.blank_deck()
    for _ in range(9):
        sl = dk.add_slide(prs)
        dk.register_mark(sl, "arcs", corner="tr")            # quiet
    check("the QUIET register signature may repeat on every page — never budgeted",
          codes(prs, "MOTIF_BUDGET") == [])

    # ---- neither may ever block a build -------------------------------------------------
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.register_mark(s, "arcs", corner=(3.0, 1.0), size=4.0, loud=True)
    txt(s, 0.8, 2.6, "A subtitle running straight across the ring")
    try:
        dk.lint_layout(prs, verbose=False, strict=True)
        check("both are WARN — strict=True still saves", True)
    except RuntimeError as exc:
        check("both are WARN — strict=True still saves", False, str(exc)[:70])

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
