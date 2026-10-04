#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UNEVEN CARD HEIGHTS compares SIBLINGS — a shape nested inside another is not one.

🔴 MEASURED 2026-10-04, on a collage deck: two taped prints side by side (a white border, and the
photo inset 0.08in inside it) were reported as "a row of 4 cards has heights [2.59, 2.59, 2.75,
2.75]". The check buckets shapes into rows by their top edge rounded to 0.1in and only de-duplicated
shapes sharing the SAME rounded top-left, so whether a print's photo joined its own border's row
depended on rounding: at one y it was a sibling, 0.03in lower it was not. A finding that comes and
goes with the third decimal of a coordinate trains authors to nudge numbers until it stops, which is
exactly the habit the loop breaker exists to refuse.

The two controls keep the check honest: genuinely uneven siblings, and genuinely uneven PRINTS
(nested photos and all), are still reported.

Run:  python3 tests/test_uneven_cards_nested.py
"""
import contextlib
import io
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deckkit as dk                                                  # noqa: E402
import lint_deck                                                      # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


BORDER = dk.RGBColor.from_string("FFFFFF")
PHOTO = dk.RGBColor.from_string("8A6A4A")
CARD = dk.RGBColor.from_string("DDE6F5")


def prints(sl, top, sizes, inset=0.08):
    """Side-by-side 'prints': a border box with a photo box nested inside it."""
    x = 0.8
    for size in sizes:
        dk.box(sl, x, top, size, size, fill=BORDER)
        dk.box(sl, x + inset, top + inset, size - 2 * inset, size - 2 * inset, fill=PHOTO)
        x += size + 0.5


with tempfile.TemporaryDirectory() as td:
    prs = dk.blank_deck(13.333, 7.5)
    # 1: equal prints — the border tops round to the same 0.1in bucket as their own photos
    for top in (2.56, 2.61, 2.64):
        prints(dk.add_slide(prs), top, (2.75, 2.75))
    # 4: control — two sibling cards of different heights in one row
    sl = dk.add_slide(prs)
    dk.box(sl, 0.8, 2.0, 3.0, 2.0, fill=CARD)
    dk.box(sl, 4.3, 2.0, 3.0, 2.6, fill=CARD)
    # 5: control — prints whose BORDERS differ (photos nested inside each)
    prints(dk.add_slide(prs), 2.56, (2.75, 2.75, 2.75))
    sl5 = prs.slides[4]
    # make the third print visibly shorter: replace with a 2.75 x 2.2 border + nested photo
    x3 = 0.8 + 2 * (2.75 + 0.5) + 3.3
    dk.box(sl5, x3, 2.56, 2.75, 2.2, fill=BORDER)
    dk.box(sl5, x3 + 0.08, 2.64, 2.59, 2.04, fill=PHOTO)
    path = pathlib.Path(td) / "cards.pptx"
    prs.save(str(path))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_deck.lint(str(path))
    lines = buf.getvalue().splitlines()


def uneven(n):
    return [ln for ln in lines if ln.strip().startswith("slide {}: UNEVEN CARD HEIGHTS".format(n))]


for n in (1, 2, 3):
    check(not uneven(n), "equal prints at slide {} are not uneven cards (a nested photo is not a "
                         "sibling): {}".format(n, uneven(n)))
check(uneven(4), "control: two sibling cards of different heights are still UNEVEN CARD HEIGHTS")
check(uneven(5), "control: prints whose borders differ in height are still UNEVEN CARD HEIGHTS")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
