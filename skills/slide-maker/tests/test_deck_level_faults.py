#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Two defect classes that a per-slide check structurally cannot see.

Both were found by a human eye on a delivered 14-page deck, after the build-time lint had
reported clean and the render-time lint had reported clean. Neither is exotic; both are what
happens when a rule about the WHOLE DECK is written as prose and left to per-page discipline.

  DUPLICATE TEXT — two separate shapes on one slide rendering the same string. Three measured
    causes, all from one build: a build script patched repeatedly left an ORPHANED copy of an
    earlier layout drawing over the new one (so the page ran two layouts at once and its
    coordinates would not move however the source was edited — four consecutive edits looked like
    they did nothing); a component's own auto-label printed beside a hand-written one, so a single
    quantity appeared twice at two different roundings on a deck whose whole proposition was
    traceability; a programme named in a list and then again as the hub of a diagram below it.

  CHROME SLOT DRIFT — a repeated chrome line that does not sit where the rest of the deck puts
    it. Measured: 11 source lines, 8 pinned and 3 placed wherever their page's last block ended.
    One of those rendered 「as of 2026-08-08」 inside a diagram box, reading as part of the
    diagram. The rule existed — as a constant each page applied by hand. It held 8 times of 11.

Both directions are asserted. A check that fires on legitimate work is worse than no check: a
deck may repeat a short shared token (a table's 是/否, an axis tick) and may re-anchor chrome on
a divider, so the thresholds exist and are tested, not assumed.

Run:  python3 tests/test_deck_level_faults.py
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


def deck(n=1):
    prs = dk.blank_deck()
    return prs, [dk.add_slide(prs) for _ in range(n)]


def txt(s, x, y, t, size=12):
    dk.text(s, x, y, 4.0, size / 72.0 * 1.4, [[(t, size, dk.DEEP, False, False, dk.FONT)]],
            space_after=0, wrap=False)


def main():
    print("deck-level faults")

    # ---- DUPLICATE TEXT ------------------------------------------------------------------
    prs, (s,) = deck()
    txt(s, 0.6, 1.2, "Klinische Technologie")
    txt(s, 5.9, 3.0, "Klinische Technologie")        # the real defect: list + diagram hub
    found = codes(prs, "DUPLICATE_TEXT")
    check("the same long string in two shapes is reported", len(found) == 1, found)
    check("the report names the string", found and "Klinische" in found[0][3])

    prs, (s,) = deck()
    txt(s, 0.6, 1.2, "四维重建流水线的一次迭代")
    txt(s, 5.0, 1.2, "四维重建流水线的一次迭代")
    check("CJK duplicates are caught too (a length rule tuned for Latin would miss them)",
          len(codes(prs, "DUPLICATE_TEXT")) == 1)

    # ...and the both-directions half: short shared tokens are NOT a defect.
    prs, (s,) = deck()
    for i, x in enumerate((0.6, 2.0, 3.4, 4.8)):
        txt(s, x, 1.2, "是", 11)
        txt(s, x, 1.8, "N/A", 11)
    check("a repeated SHORT token (是 / N/A) is not reported",
          codes(prs, "DUPLICATE_TEXT") == [], codes(prs, "DUPLICATE_TEXT"))

    prs, (s,) = deck()
    txt(s, 0.6, 1.2, "Geneeskunde")
    txt(s, 0.6, 1.8, "Biomedische Wetenschappen")
    txt(s, 0.6, 2.4, "Klinische Technologie")
    check("a list of DIFFERENT long strings is not reported",
          codes(prs, "DUPLICATE_TEXT") == [])

    prs, (a, b) = deck(2)
    txt(a, 0.6, 1.2, "Leiden Bio Science Park")
    txt(b, 0.6, 1.2, "Leiden Bio Science Park")       # same string, DIFFERENT slides
    check("the same string on two different slides is not reported (that is a motif, not a bug)",
          codes(prs, "DUPLICATE_TEXT") == [])

    # ---- CHROME SLOT DRIFT ---------------------------------------------------------------
    prs = dk.blank_deck()
    for y in (4.80, 4.80, 3.92, 4.80, 4.15):          # the measured shape: 2 strays of 5
        s = dk.add_slide(prs)
        txt(s, 0.6, 1.2, "some ordinary content on the page")
        dk.source_note(s, ["LUMC Jaarverslag 2025"], as_of="2026-08-08", label="来源",
                       size=8.5, ink=RGBColor(0x73, 0x6B, 0x5D), x=0.62, y=y, w=8.76)
    found = codes(prs, "CHROME_SLOT_DRIFT")
    check("source lines that drift off the deck's slot are reported", len(found) == 2, found)
    check("the report names both the stray y and the slot",
          found and "3.92" in found[0][3] and "4.80" in found[0][3], found)

    prs = dk.blank_deck()
    for _ in range(5):
        s = dk.add_slide(prs)
        txt(s, 0.6, 1.2, "some ordinary content on the page")
        dk.source_note(s, ["LUMC Jaarverslag 2025"], as_of="2026-08-08", label="来源",
                       size=8.5, ink=RGBColor(0x73, 0x6B, 0x5D), x=0.62, y=4.80, w=8.76)
    check("a deck that pins every source line is silent", codes(prs, "CHROME_SLOT_DRIFT") == [])

    # Below three source lines there is no slot to establish, so nothing may be asserted.
    prs = dk.blank_deck()
    for y in (4.80, 3.10):
        s = dk.add_slide(prs)
        dk.source_note(s, ["X"], as_of="2026-08-08", label="来源", size=8.5,
                       ink=RGBColor(0x73, 0x6B, 0x5D), x=0.62, y=y, w=8.76)
    check("two source lines do not establish a slot, so nothing is reported",
          codes(prs, "CHROME_SLOT_DRIFT") == [])

    # ---- neither check may ever block a build --------------------------------------------
    prs, (s,) = deck()
    txt(s, 0.6, 1.2, "Klinische Technologie")
    txt(s, 5.9, 3.0, "Klinische Technologie")
    try:
        dk.lint_layout(prs, verbose=False, strict=True)
        check("a duplicate is a WARN — strict=True still saves", True)
    except RuntimeError as exc:
        check("a duplicate is a WARN — strict=True still saves", False, str(exc)[:70])

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
