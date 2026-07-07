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
    box, text, bullet, callout, arrow, chip, modbox, equation_native, equation_png,
    columns, picture, lint_layout,
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
    text(s, 0.7, 2.0, 8.6, 1.4, [[("Project Title", 40, WHITE, True, False)],
         [("a one-line subtitle", 20, TEAL, False, False)]], space_after=4, line_spacing=1.0)
    text(s, 0.7, 4.4, 8.6, 0.4, [[("Presenter · Affiliation", 13, WHITE, False, False)]], space_after=0)


def slide_one_idea(prs):
    """role=framework | form=terse bullets + takeaway callout | static: scan-at-once list |
    takeaway='A slide is a visual aid, not a document'"""
    s = add_slide(prs)
    title_bar(s, "One idea per slide", kicker="section")
    footer(s, TAG, page=2)
    bullet(s, 0.6, 1.45, 5.5, [
        ("Few words ", "per point"),
        ("Diagrams ", "over text"),
        ("Every figure ", "gets a takeaway"),
    ], size=17, gap=0.3)
    callout(s, 0.6, 4.3, 5.5, 0.6, "TAKEAWAY", "A slide is a visual aid, not a document.")


def slide_pipeline(prs):
    """role=method | form=pipeline chips (colours rotate via ACCENTS) | build: stage-by-stage
    with its arrow (wire with anim.Build in a real deck) | takeaway='Four stages, one flow'"""
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
    # equation_native renders a LaTeX subset as real, click-EDITABLE text runs (italic
    # variables, upright operators, true sub/superscripts) in a math font — the DEFAULT;
    # reach for equation_png only for 2-D math (fractions/matrices), eq_par for one inline symbol.
    equation_native(s, 0.8, 2.2, 8.4, 0.7,
                    r"\hat{x} = \arg\min_x \|A x - y\|_2^2 + \lambda R(x)",
                    size=20, align=PP_ALIGN.CENTER)
    callout(s, 0.6, 4.3, 8.8, 0.6, "WHY",
            "equation_native typesets real math as EDITABLE text runs (italic variables, true "
            "sub/superscripts) — click-editable and renders everywhere; reach for equation_png only for "
            "2-D math (fractions/matrices), and eq_par for one inline symbol.")


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
    print("saved ->", OUT, "| slides:", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
