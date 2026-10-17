#!/usr/bin/env python3
"""Three checks that came out of verifying a review's claims against the deck.

The parent exercise matters more than any one check here. Six claims from a real design review
were re-measured by hand; three were factually wrong, all three among the ones quoting precise
figures. Two of those three nearly became lint checks in this repository — built to enforce a
defect that did not exist. Everything below either survived that verification or came out of it:

  · SPLIT PAGE — one interior slide cut in half by a band of nothing (independently measured at
    0.985in against <=0.555in on every other content slide, and reached by the review too).
  · carried_by rule consistency — three slides declared to carry ONE device drawing it in three
    colours, three spans and three weights.
THREE proposed checks are deliberately ABSENT, and their absence is part of the finding:

  · a same-colour adjacency check — the review claimed a bar and a rule merged because both were
    INK. The bar is GOLD (192,138,46); the rule is INK; the bar meeting the rule IS the page's
    argument. There was no defect to catch.
  · a label-to-object distance check — the "distant" labels are a legitimate column alignment, and
    this repo's own RAGGED LEFT EDGE already exempts the opposite convention.
  · an automated re-measurer for a review's quoted figures. It was built, and abandoned after it
    kept trading one failure mode for another: associating "which object does this coordinate
    describe" cannot be done reliably by regex over prose. It confirmed a false span using a row
    cited two sentences away, then contradicted a correct claim whose first cited row falls
    between glyph strokes. `maintenance-boundaries.md` says a check that cannot reach acceptable
    precision should not ship; that applies to checks written here too.

What replaces it is knowledge, not code: a review's quoted measurements are not evidence. Half of
the ones examined were wrong. Re-measure before acting on a number in a finding.
"""
import io, json, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

ok, bad = [], []
for _m in ("pptx", "PIL"):
    try:
        __import__(_m)
    except ImportError:
        print(f"skip: {_m} not installed")
        raise SystemExit(0)

from PIL import Image, ImageDraw                            # noqa: E402
import lint_deck as L                                       # noqa: E402

TMP = pathlib.Path(tempfile.mkdtemp(prefix="grounding-"))
W, H = 1440, 811
PAPER, INK = (245, 241, 230), (31, 59, 47)


def _page(bands):
    """A slide with ink on the given (y0, y1) row ranges."""
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for y0, y1 in bands:
        d.rectangle([120, y0, 900, y1], fill=INK)
    return im


# ---------------------------------------------------------------- SPLIT PAGE
# The measurement, against the same page the review reached independently.
dense = _page([(120, 300), (320, 420), (440, 560), (580, 630)])
split = _page([(120, 300), (320, 440), (586, 630)])          # a ~1in hole from y=440 to 586
b_dense = L._render_void_band(dense)
b_split = L._render_void_band(split)
if b_split > b_dense * 1.5 and b_split >= 0.85:
    ok.append(f"_render_void_band separates a split page ({b_split:.2f}in) from a dense one "
              f"({b_dense:.2f}in)")
else:
    bad.append(f"the void-band measure does not separate split from dense: {b_split} vs {b_dense}")

dark = Image.new("RGB", (W, H), (14, 27, 42))
dd = ImageDraw.Draw(dark)
dd.rectangle([120, 120, 900, 300], fill=(240, 240, 240))
dd.rectangle([120, 586, 900, 630], fill=(240, 240, 240))
if L._render_void_band(dark) >= 0.85:
    ok.append("a DARK page is measured against its own ground, not against white")
else:
    bad.append("the void band is blind on a dark canvas — it compares to the wrong ground")

spine = Image.new("RGB", (W, H), PAPER)
sp = ImageDraw.Draw(spine)
sp.rectangle([0, 0, 30, H], fill=(212, 113, 78))            # an ochre spine down the left edge
sp.rectangle([120, 120, 900, 300], fill=INK)
sp.rectangle([120, 586, 900, 630], fill=INK)
if L._render_void_band(spine) >= 0.85:
    ok.append("a page with an edge SPINE is still measured against its dominant colour — a corner "
              "sample would have returned the spine and reported no void at all")
else:
    bad.append("an edge spine became the background and the void band vanished")


# ---------------------------------------------------------------- carried_by rule consistency
# The declaration says N slides carry ONE device. The existing check asks whether each named slide
# differs from the deck's default page — three slides can each be unusual in three unrelated ways
# and pass it. Measured on a delivered deck declaring carried_by=[5,10,11] as "the same line
# grammar": #1F3B2F at 41% of the canvas and 3.2px · #8A8377 at 50% and 2.9px · #B4462A at 34%,
# 2.3px, at a different y entirely.
import subprocess as _sp                                     # noqa: E402

import deckkit as dk                                         # noqa: E402
from pptx.dml.color import RGBColor as C                     # noqa: E402

dk.FONT = "Helvetica Neue"


def _deck(rules, name):
    prs = dk.blank_deck()
    for i, r in enumerate(rules):
        s = dk.add_slide(prs)
        dk.slide_background(s, "F5F1E6")
        dk.text(s, 0.6, 0.5, 8.8, 0.7,
                [[("Section %d" % (i + 1), 26, C.from_string("1F3B2F"), True, False)]])
        if r:
            fill, frac, th = r
            dk.box(s, 0.6, 2.0, 10.0 * frac, th, fill=fill)
        dk.text(s, 0.6, 3.0, 8.0, 0.6,
                [[("body copy", 14, C.from_string("1F3B2F"), False, False)]])
    out = TMP / name
    out.mkdir(exist_ok=True)
    pth = out / "d.pptx"
    prs.save(str(pth))
    return pth


def _gate(pptx, cb):
    import importlib
    sys.path.insert(0, str(SCRIPTS))
    rd = importlib.import_module("render_deck")
    buf = io.StringIO()
    import contextlib
    with contextlib.redirect_stdout(buf):
        rd._report_carried_by(str(pptx), cb)
    return buf.getvalue()


mixed = _deck([("1F3B2F", 0.41, 0.022), ("8A8377", 0.50, 0.020), ("B4462A", 0.34, 0.016)], "mixed")
out = _gate(mixed, [1, 2, 3])
if "THREE different ways" in out and "1F3B2F" in out and "8A8377" in out:
    ok.append("three slides declared to carry one device, drawn three ways, are named with their "
              "three colours/spans/weights")
else:
    bad.append(f"an inconsistent carried_by device was not reported:\n{out[:300]}")

same = _deck([("1F3B2F", 0.41, 0.022)] * 3, "same")
out = _gate(same, [1, 2, 3])
if "THREE different ways" not in out and "consistent" in out:
    ok.append("the SAME rule on all three is reported consistent, not flagged")
else:
    bad.append(f"a consistent device was reported as inconsistent:\n{out[:300]}")

none = _deck([None, None, None], "none")
out = _gate(none, [1, 2, 3])
if "THREE different ways" not in out:
    ok.append("slides with no rule at all say nothing — the device may live on colour, type or "
              "concept, and dying on that would push authors toward layout stunts")
else:
    bad.append("a deck whose signature is not a rule was judged on rules it never drew")

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print(f"\n{len(ok)} passed, {len(bad)} failed")
raise SystemExit(1 if bad else 0)
