#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The safe band was unsafe against the deck's own default chrome.

SKILL.md's cure for hand-picked y-coordinates is `content_band()`: ask for the safe rect instead
of guessing a number. That helper returned a CONSTANT top of 1.15in — which is `title_bar()`'s
bottom edge (1.100) plus a 0.05in gap, and correct only for a title with NO kicker. Add a kicker
and the title box ends at 1.240 while the band still starts at 1.150, so the first content block
lands 0.09in INSIDE the title rule.

That was shipping in this skill's own worked example — the file SKILL.md tells every single-author
build to copy — and no gate saw it: `TEXT_OVERLAP` measures text against TEXT, and a title rule is
geometry. It was found by rendering the example and looking at the PNG.

The fix measures the tagged title chrome instead of assuming it. What this suite pins:

  · the no-kicker case still returns EXACTLY 1.15 — the fix reproduces the constant in the case
    the constant was tuned for, so it is a precision fix and not a silent re-layout of every deck;
  · the kicker case clears its chrome;
  · a corner `register_mark` is chrome-height geometry in the title zone and must NOT push the
    band down — which is why only TAGGED title chrome is measured, not "whatever is near the top";
  · an explicit `top=` still wins (a deck with its own `style.py` title treatment), and a slide
    with no chrome yet still falls back to the documented constant.

Run:  python3 tests/test_content_band.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                                                  # noqa: E402

E = 914400.0
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def slide(**kw):
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    if kw.get("title", True):
        dk.title_bar(s, kw.get("text", "One idea per slide"), kicker=kw.get("kicker", ""))
    return prs, s


def chrome_bottom(s):
    return max((sh.top + sh.height) / E for sh in s.shapes)


def main():
    print("content band")

    # ---- the regression itself: the band must clear the chrome it sits under ----------
    for kicker in ("section", "method", ""):
        _, s = slide(kicker=kicker)
        top = dk.content_band(s)[1]
        bot = chrome_bottom(s)
        check("kicker=%-8r band top %.3f clears chrome bottom %.3f" % (kicker, top, bot),
              top >= bot - 1e-9, "overlaps by %.3fin" % (bot - top))

    # ...and it must clear a title that WRAPS to two lines, which moves the rule down.
    _, s = slide(kicker="section",
                 text="A sentence-length assertion title that is long enough to wrap onto a "
                      "second line in the title band")
    check("a two-line title still clears", dk.content_band(s)[1] >= chrome_bottom(s) - 1e-9,
          (dk.content_band(s)[1], chrome_bottom(s)))

    # ---- byte-identical in the case the old constant was tuned for --------------------
    _, s = slide(kicker="")
    check("no-kicker title still returns EXACTLY the historical 1.15",
          abs(dk.content_band(s)[1] - 1.15) < 1e-9, dk.content_band(s)[1])

    # ---- only TAGGED chrome is measured ------------------------------------------------
    _, s = slide(kicker="")
    dk.register_mark(s, "arcs", corner="tr", size=2.0)      # tall, top-right, NOT a title
    check("a corner register mark does not push the band down",
          abs(dk.content_band(s)[1] - 1.15) < 1e-9, dk.content_band(s)[1])

    _, s = slide(kicker="")
    dk.box(s, 0, 0, 10, 5.625, fill=dk.DEEP)                # a full-bleed ground
    check("a full-bleed background does not push the band down",
          abs(dk.content_band(s)[1] - 1.15) < 1e-9, dk.content_band(s)[1])

    # ---- the escapes still work --------------------------------------------------------
    _, s = slide(title=False)
    check("a slide with no chrome falls back to the documented constant",
          abs(dk.content_band(s)[1] - dk.TITLE_BAND_DEFAULT) < 1e-9, dk.content_band(s)[1])

    _, s = slide(kicker="section")
    check("an explicit top= still wins (a deck with its own title treatment)",
          abs(dk.content_band(s, top=2.0)[1] - 2.0) < 1e-9)

    # ---- the rest of the rect is untouched ---------------------------------------------
    _, s = slide(kicker="section")
    x, y, w, h = dk.content_band(s)
    w_in, h_in = dk._slide_size(s)
    check("x/width still come from the real deck size",
          abs(x - dk.GUTTER) < 1e-9 and abs(w - (w_in - 2 * dk.GUTTER)) < 1e-9, (x, w))
    check("the bottom edge still clears the footer band",
          abs((y + h) - (h_in - dk.FOOTER_BAND - 0.15)) < 1e-9, y + h)
    check("footer_gap= is still honoured",
          abs(sum(dk.content_band(s, footer_gap=0.5)[1::2]) - (h_in - dk.FOOTER_BAND - 0.5)) < 1e-9)

    # ---- and the whole point: a block placed at the band top must not overlap the title -
    _, s = slide(kicker="section")
    band = dk.content_band(s)
    dk.bullet(s, band[0], band[1], 5.5, [("Few words ", "per point"),
                                         ("Diagrams ", "over text")], size=17)
    prs = s.part.package.presentation_part.presentation
    bad = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
    check("a bullet block at the band top passes the build-time gate", bad == [], bad)

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
