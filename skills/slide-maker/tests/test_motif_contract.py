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

    # ── the LOUD tier: motif_page, and the STRANGER TEST made countable ───────────────────────
    print("\nthe loud tier")
    prs = dk.blank_deck(10.0, 5.625)
    s1 = dk.add_slide(prs)
    dk.slide_background(s1, "FFFFFF")
    shapes = dk.motif_page(s1, "seam")
    check("motif_page draws the page whose GEOMETRY is the motif", len(shapes) >= 4)
    check("...and every shape it draws is tagged LOUD, so the <=3 budget can see the page",
          all(dk._is_motif(sh, loud=True) for sh in shapes))
    check("an unexplained loud motif is REPORTED — the stranger test, countable at last",
          len(codes(prs, "MOTIF_UNEXPLAINED")) == 1)

    prs2 = dk.blank_deck(10.0, 5.625)
    s2 = dk.add_slide(prs2)
    dk.slide_background(s2, "FFFFFF")
    dk.motif_page(s2, "conduit", legend="CROSSING — today to the bet")
    check("...and legend='…' on the device's first appearance clears it",
          codes(prs2, "MOTIF_UNEXPLAINED") == [])
    check("the legend does NOT spend the loud budget (a key is not the device)",
          not any(dk._is_motif(sh) for sh in s2.shapes
                  if str(getattr(sh, "name", "")) == dk.MOTIF_LEGEND))

    prs3 = dk.blank_deck(10.0, 5.625)
    s3 = dk.add_slide(prs3)
    dk.slide_background(s3, "FFFFFF")
    dk.text(s3, 0.7, 0.6, 6.0, 0.5, [[("a plain page", 20, dk.DEEP, True, False, "Helvetica Neue")]])
    check("a deck with NO motif is never asked to explain one (the check cannot punish a deck for "
          "not using this vocabulary)", codes(prs3, "MOTIF_UNEXPLAINED") == [])

    prs4 = dk.blank_deck(10.0, 5.625)
    s4 = dk.add_slide(prs4)
    dk.register_mark(s4, "seal", corner="tr")
    check("a QUIET register signature alone raises nothing — it is chrome, not a claim",
          codes(prs4, "MOTIF_UNEXPLAINED") == [])

    bad = None
    try:
        dk.motif_page(dk.add_slide(dk.blank_deck(10.0, 5.625)), "swoosh")
    except ValueError as exc:
        bad = str(exc)
    check("an unknown motif_page kind RAISES rather than drawing something else", bool(bad),
          "no exception")
    check("...and the error names the alternatives", bool(bad and "seam" in bad and "orbit" in bad))

    for k in dk._REGISTER_KINDS:
        sN = dk.add_slide(prs4)
        try:
            dk.register_mark(sN, k, corner="tl", text="7")
            drew = True
        except Exception as exc:                                          # noqa: BLE001
            drew = False
            detail = "{}: {}".format(type(exc).__name__, exc)
        check("register_mark kind {!r} draws".format(k), drew, locals().get("detail", ""))
    check("the register vocabulary reaches past the graphic-neutral five into subject worlds",
          {"seal", "stitch", "trace", "contour", "caliper", "hatch"} <= set(dk._REGISTER_KINDS))

    for k in sorted(dk._MOTIF_PAGE_KINDS):
        pk = dk.blank_deck(10.0, 5.625)
        sk = dk.add_slide(pk)
        try:
            got = dk.motif_page(sk, k, legend="{} — meaning".format(k))
            okk = len(got) >= 2
        except Exception as exc:                                          # noqa: BLE001
            okk, got = False, exc
        check("motif_page kind {!r} draws a page".format(k), okk, str(got)[:70])

    # ── grounds vs devices: the carve that makes the loud tier USABLE ─────────────────────────
    print("\ngrounds vs devices")
    prs5 = dk.blank_deck(10.0, 5.625)
    s5 = dk.add_slide(prs5)
    dk.motif_page(s5, "seam", legend="THE SEAM — old hands over to new")
    txt(s5, 0.7, 2.0, "Before")
    txt(s5, 5.6, 2.0, "After")
    check("text ON a motif's painted colour FIELD is not a crossing — a field is a canvas, and "
          "without this carve every word on a loud motif page was reported",
          codes(prs5, "TEXT_OVER_MOTIF") == [],
          [f[3][:60] for f in codes(prs5, "TEXT_OVER_MOTIF")])

    prs6 = dk.blank_deck(10.0, 5.625)
    s6 = dk.add_slide(prs6)
    ring = dk.box(s6, 3.4, 1.4, 3.2, 3.2, fill=None, line=dk.MAGENTA, line_w=2.0, round=True, r=1.6)
    dk.tag_motif(ring, loud=True)
    txt(s6, 3.0, 2.6, "a subtitle laid across the ring")
    check("...while text across an outline DEVICE still fires — the defect the check was written "
          "for (a subtitle through a hand-rolled register) is untouched",
          len(codes(prs6, "TEXT_OVER_MOTIF")) == 1)

    band = dk.blank_deck(10.0, 5.625)
    sb = dk.add_slide(band)
    spine = dk.box(sb, 0.0, 2.8, 10.0, 0.04, fill=dk.MAGENTA)
    dk.tag_motif(spine, loud=True)
    txt(sb, 0.7, 2.68, "a caption straight through the spine")
    check("...and a full-width RULE is a device, not a ground — thickness, not span, is what "
          "separates the two", len(codes(band, "TEXT_OVER_MOTIF")) == 1)

    # ── the legend places itself against the deck's own safe band ────────────────────────────
    prs7 = dk.blank_deck(10.0, 5.625)
    s7 = dk.add_slide(prs7)
    dk.motif_page(s7, "seam", legend="A key long enough to wrap onto a second line, which is "
                                     "exactly the case that used to land inside the footer band")
    leg = [sh for sh in s7.shapes if str(getattr(sh, "name", "")) == dk.MOTIF_LEGEND][0]
    bottom = (leg.top + leg.height) / 914400.0
    _bx, _by, _bw, _bh = dk.content_band(s7)
    check("a two-line legend places itself INSIDE the safe band (measured, never a fixed y)",
          bottom <= _by + _bh + 0.02, "legend bottom {:.2f} vs band {:.2f}".format(bottom, _by + _bh))
    right = (leg.left + leg.width) / 914400.0
    check("...and it fits the colour field it sits on rather than straddling the seam",
          right <= 10.0 * 0.5 + 0.02, "legend right edge {:.2f} vs the seam at 5.0".format(right))

    prs8 = dk.blank_deck(10.0, 5.625)
    s8 = dk.add_slide(prs8)
    dk.motif_page(s8, "seam", color=RGBColor(0x00, 0x2A, 0x40), legend="dark ground")
    leg8 = [sh for sh in s8.shapes if str(getattr(sh, "name", "")) == dk.MOTIF_LEGEND][0]
    ink8 = leg8.text_frame.paragraphs[0].runs[0].font.color.rgb
    check("a legend on a DARK register takes a light ink — it reads its ground, it does not "
          "assume one", str(ink8) == str(dk.WHITE), str(ink8))

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
