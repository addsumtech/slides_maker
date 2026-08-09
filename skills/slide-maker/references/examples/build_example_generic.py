#!/usr/bin/env python3
"""Generic worked example — a short, brand-free deck built FROM SCRATCH (no template),
showing BOTH the deckkit helpers and the per-slide-function SCAFFOLD every single-author
build should copy: a STYLE block at the top → one function per slide whose DOCSTRING is
that slide's design-plan row + motion-manifest line → an ordered SLIDES registry →
main() builds ALL slides, runs the build-time geometry gate, and saves.

Why the scaffold: each docstring carries `role=… | form=… | build:…/static:… |
takeaway='…'`, so PRE-FLIGHT #3 becomes a mechanical diff (design-plan rows vs these
docstrings) plus a spot-check that each `build:` docstring has matching Build.step calls
in its function body — and the motion manifest the Step-5 critic reads IS these
docstrings, not a comment block that drifts.

🔴 TWO RULES THIS FILE DEMONSTRATES RATHER THAN STATES, because a scaffold teaches by example
and this one used to teach the opposite of both:

  1. NEVER hand-pick a y for a block that can grow. Measure it (`measure_bullets`/`measure_callout`
     /`measure_text`) or anchor it (`vstack(..., bottom=)`, `content_band()`, `bottom_callout()`).
     Measured on a real 14-page build: the author hand-computed nearly every y, spent many rounds
     moving coordinates by 0.02in, and only reached for `vstack` after pages had already started
     overlapping — at which point its first error, "blocks need 3.68in but the band is only
     2.88in", was the single most useful sentence of the build. It says the page is OVER-FULL,
     which no amount of nudging can fix. That error arriving on round one instead of round twelve
     is the whole difference.

  2. TAG the deck's signature device. `register_mark()` draws the common register shapes correct
     by construction and tags them; anything you draw yourself gets `tag_motif(shape, loud=…)`.
     Untagged, a motif is invisible to `TEXT_OVER_MOTIF` and to the <=3-loud-appearance budget —
     measured on that same build, 383 shapes carried ZERO tags, so the check written for its own
     cover defect reported nothing on it.

If the user has a template, build on it instead (deckkit.open_template + the template's
profile in the active template registry). This file is just a how-to for the kit.

Run:  python build_example_generic.py   →  <tempdir>/slide_maker_demo.pptx
Then: bash ../../scripts/render_deck.sh <that path>   (or, on native Windows,
      python ..\\..\\scripts\\render_deck.py <that path>)  and inspect the PNGs.
"""
import sys, os, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from deckkit import (  # noqa: E402
    blank_deck, add_slide, title_bar, footer,
    box, text, bullet, callout, bottom_callout, arrow, chip, modbox, equation_native,
    equation_png,
    columns, rows, vstack, content_band, measure_bullets, measure_callout,
    register_mark, tag_motif, picture, lint_layout, declare_delivery,
    set_font, Inches, PP_ALIGN, MSO_ANCHOR,
    DEEP, BLUE, TEAL, MAGENTA, SLATE, MUTE, TINT, LIGHT, WHITE,
    GOLD, STEEL, VIOLET, ACCENTS,
)

# ─── STYLE — the deck's design language, stated ONCE (palette/fonts come from deckkit's
#     constants here; a real deck sets them from the approved Design plan / preset) ───
OUT = os.path.join(tempfile.gettempdir(), "slide_maker_demo.pptx")
TAG = "demo deck"


def slide_cover(prs):
    """role=cover | form=full-bleed statement | static: nothing to pace |
    takeaway='Project Title — the one line this deck argues'"""
    s = add_slide(prs)
    box(s, 0, 0, 10, 5.625, fill=DEEP)
    box(s, 0, 0, 0.18, 5.625, fill=MAGENTA)
    # The register signature, drawn by the helper so it is correct AND tagged. `loud=True` marks a
    # hero appearance (budgeted at <=3); interior pages use the same call without it.
    register_mark(s, "arcs", corner="br", color=TEAL, size=2.2, loud=True)
    text(s, 0.7, 2.0, 8.6, 1.4, [[("Project Title", 40, WHITE, True, False)],
         [("a one-line subtitle", 20, TEAL, False, False)]], space_after=4, line_spacing=1.0)
    text(s, 0.7, 4.4, 8.6, 0.4, [[("Presenter · Affiliation", 13, WHITE, False, False)]], space_after=0)


def slide_one_idea(prs):
    """role=framework | form=terse bullets + takeaway callout | static: scan-at-once list |
    takeaway='A slide is a visual aid, not a document'"""
    s = add_slide(prs)
    title_bar(s, "One idea per slide", kicker="section")
    footer(s, TAG, page=2)
    register_mark(s, "arcs", corner="tr", color=TINT, size=1.2)   # the quiet echo, every page
    # 🔴 MEASURED, not hand-picked. `callout(s, 0.6, 4.3, ...)` is the bug this scaffold used to
    # teach: the moment the bullets gain a line, that 4.3 is inside them. vstack takes each block's
    # measured height, keeps the gaps equal by construction, and RAISES at build time if the two
    # no longer fit the band — which is the message you want, because it means "this page is too
    # full", not "move something 0.02in".
    items = [("Few words ", "per point"),
             ("Diagrams ", "over text"),
             ("Every figure ", "gets a takeaway")]
    band = content_band(s)                        # the safe rect: below the title, above the footer
    h_bul = measure_bullets(items, 5.5, size=17, gap=0.3)
    h_cal = measure_callout("TAKEAWAY", "A slide is a visual aid, not a document.", 5.5)
    # anchor: "top" keeps the two blocks together as one unit under the title, which is right HERE
    # because the page reserves its right column (w=5.5 of an 8.8in band) for a figure — the empty
    # area is composed, not left over. "justify" spreads the slack as equal gaps, but with exactly
    # TWO blocks that means maximum separation: the bullets pin to the title, the takeaway pins to
    # the footer, and the slack collects as one hole in the MIDDLE of the page, which reads far
    # worse than the same slack at the edge. Reach for "justify" at three or more blocks.
    vstack(s, 0.6, band[1], 5.5,
           [(h_bul, lambda x, y, w: bullet(s, x, y, w, items, size=17, gap=0.3)),
            (h_cal, lambda x, y, w: callout(s, x, y, w, h_cal, "TAKEAWAY",
                                            "A slide is a visual aid, not a document."))],
           gap=0.35, bottom=band[1] + band[3])


def slide_pipeline(prs):
    """role=method | form=pipeline chips (colours rotate via ACCENTS) | static: scaffold —
    wire anim.Build here, stage-by-stage-with-its-arrow, in a real deck | takeaway='Four stages, one flow'"""
    s = add_slide(prs)
    title_bar(s, "A pipeline diagram", kicker="method")
    footer(s, TAG, page=3)
    stages = ["Input", "Process", "Model", "Output"]
    cw, g, x0, y0, ch = 1.9, 0.3, 0.7, 2.0, 1.2
    for i, name in enumerate(stages):
        x = x0 + i * (cw + g)
        chip(s, x, y0, cw, ch, name, "one line\nof detail", ACCENTS[i % len(ACCENTS)])
        if i < len(stages) - 1:
            arrow(s, x + cw + 0.02, y0 + ch / 2 - 0.12, g - 0.04, 0.24)


def slide_equation(prs):
    """role=method(why) | form=native typeset math + WHY callout | static: one relation, read
    whole | takeaway='Typeset math reads as formal — and stays editable'"""
    s = add_slide(prs)
    title_bar(s, "Typeset math reads as formal", kicker="equations")
    footer(s, TAG, page=4)
    # bottom_callout, NOT callout at a hand-picked y. `callout` auto-grows DOWN, so a long body
    # placed at an eyeballed y=4.3 grew straight into the footer band — this file shipped that way,
    # and it is the exact defect SKILL.md calls "the #1 recurring layout bug", demonstrated in the
    # example it tells you to copy. Measured on the built deck: FOOTER collision · FOOTER-ZONE
    # intrusion · TEXT PADDING past the card bottom, all three on this slide.
    # bottom_callout anchors to the footer band and grows UP, so it cannot collide by construction.
    #
    # 🔴 It is built FIRST because it RETURNS ITS OWN TOP y — that return value is what the block
    # above is sized against. Building it last and discarding the return (which this file also used
    # to do) leaves the equation at a hand-picked y=2.2 that knows nothing about how tall the
    # callout grew: the two are independent guesses that happen to clear today and collide the
    # first time the body text gains a line.
    top = bottom_callout(s, 0.6, 8.8, "WHY",
                         "equation_native typesets real math as EDITABLE text runs (italic variables, "
                         "true sub/superscripts) — click-editable and renders everywhere; reach for "
                         "equation_png only for 2-D math (fractions/matrices), eq_par for one inline "
                         "symbol.")
    # equation_native renders a LaTeX subset as real, click-EDITABLE text runs (italic
    # variables, upright operators, true sub/superscripts) in a math font — the DEFAULT;
    # reach for equation_png only for 2-D math (fractions/matrices), eq_par for one inline symbol.
    band = content_band(s)                        # (x, y, w, h) — below the title, above the footer
    eq_h, gap = 0.7, 0.30
    equation_native(s, 0.8, band[1] + (top - gap - band[1] - eq_h) / 2.0, 8.4, eq_h,
                    r"\hat{x} = \arg\min_x \|A x - y\|_2^2 + \lambda R(x)",
                    size=20, align=PP_ALIGN.CENTER)


def slide_split(prs):
    """role=evidence | form=columns(2) split — bullets left, figure/chips right | static:
    comparison read side-by-side | takeaway='Equal panels + symmetric margins, by construction'"""
    # The most common lopsided-slide tell is a left and right panel of different widths, or
    # unequal white margins. columns(n) derives every panel from one grid so they come out
    # equal by construction — and columns(2, weights=(1, 2)) is the measured form of an
    # INTENTIONAL 1/3–2/3 split (rail + main), still with symmetric outer margins.
    s = add_slide(prs)
    title_bar(s, "Equal split panels, by construction", kicker="layout")
    footer(s, TAG, page=5)
    L, R = columns(2, slide=s, bottom=1.3)   # two equal halves; left/right margins identical
    bullet(s, L[0], L[1], L[2], [
        ("columns(2) ", "returns equal-width rects"),
        ("Outer margins ", "stay symmetric"),
        ("No eyeballing ", "x / w per panel"),
    ], size=16, gap=0.3)
    # right half: chips occupy the SAME width as the left panel (a real figure would use
    # picture(s, fig, *R, fit="contain") here — same rect, edges preserved)
    rx, ry, rw, _rh = R
    for i, (name, detail) in enumerate([("Left rail", "text / bullets"), ("Right panel", "figure or chips")]):
        chip(s, rx, ry + i * (1.2 + 0.3), rw, 1.2, name, detail, ACCENTS[i % len(ACCENTS)])
    callout(s, L[0], 4.45, R[0] + R[2] - L[0], 0.6, "WHY",
            "Both panels come from one grid, so left/right widths and flanking margins match.")


# The ordered registry IS the deck. It may be TEMPORARILY sliced (e.g. SLIDES[2:3]) for the
# render-failure isolation workflow or a mid-round self-check render into render_check/ (never
# render/) — the fence: every critic round reviews a full fresh render, and the deliverable is
# always this full, zero-arg default build.
SLIDES = [slide_cover, slide_one_idea, slide_pipeline, slide_equation, slide_split]


def main():
    prs = blank_deck()                      # fresh 16:9 deck, no template
    for build_slide in SLIDES:
        build_slide(prs)
    # build-time geometry gate: catch overflow / overlap / off-canvas / footer faults BEFORE
    # rendering (in-process, milliseconds). strict=True RAISES on any CRITICAL so a broken
    # deck can't be saved by accident — fix the geometry and re-run (or pass strict=False for
    # a rare, deliberate off-canvas bleed). Then render + run the critic.
    lint_layout(prs, strict=True)
    prs.save(OUT)
    # 🔴 Record WHAT KIND of deck this is, next to the save, while it is still known. Both
    # `lint_deck.py` and `render_deck.py --gate-check` read this key, so the budgets they enforce
    # stop depending on someone remembering `--selfread` on every run. Measured on a delivered
    # self-read deck: 20 advisory lines with no flag, 10 with the right one — half the output was
    # the presented budget applied to a deck nobody speaks, and noise is what teaches people to
    # skim gates. One of: presented · textheavy · selfread · surface.
    declare_delivery(OUT, "presented")
    print("saved ->", OUT, "| slides:", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
