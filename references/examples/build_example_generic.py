#!/usr/bin/env python3
"""Generic worked example — a short, brand-free deck built FROM SCRATCH (no template)
so it shows the deckkit helpers without any institution's branding.

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
    box, text, bullet, callout, arrow, chip, modbox, equation_png,
    columns, picture,
    set_font, Inches, PP_ALIGN, MSO_ANCHOR,
    DEEP, BLUE, TEAL, MAGENTA, SLATE, MUTE, TINT, LIGHT, WHITE,
    GOLD, STEEL, VIOLET, ACCENTS,
)

OUT = os.path.join(tempfile.gettempdir(), "slide_maker_demo.pptx")
prs = blank_deck()                      # fresh 16:9 deck, no template

# --- title slide ---
s = add_slide(prs)
box(s, 0, 0, 10, 5.625, fill=DEEP)
box(s, 0, 0, 0.18, 5.625, fill=MAGENTA)
text(s, 0.7, 2.0, 8.6, 1.4, [[("Project Title", 40, WHITE, True, False)],
     [("a one-line subtitle", 20, TEAL, False, False)]], space_after=4, line_spacing=1.0)
text(s, 0.7, 4.4, 8.6, 0.4, [[("Presenter · Affiliation", 13, WHITE, False, False)]], space_after=0)

# --- a content slide: title bar + terse bullets + a callout ---
s = add_slide(prs)
title_bar(s, "One idea per slide", kicker="section")
footer(s, "demo deck", page=2)
bullet(s, 0.6, 1.45, 5.5, [
    ("Few words ", "per point"),
    ("Diagrams ", "over text"),
    ("Every figure ", "gets a takeaway"),
], size=17, gap=0.3)
callout(s, 0.6, 4.3, 5.5, 0.6, "TAKEAWAY", "A slide is a visual aid, not a document.")

# --- a diagram slide: pipeline chips (colours rotate via ACCENTS) ---
s = add_slide(prs)
title_bar(s, "A pipeline diagram", kicker="method")
footer(s, "demo deck", page=3)
stages = ["Input", "Process", "Model", "Output"]
cw, g, x0, y0, ch = 1.9, 0.3, 0.7, 2.0, 1.2
for i, name in enumerate(stages):
    x = x0 + i*(cw+g)
    chip(s, x, y0, cw, ch, name, "one line\nof detail", ACCENTS[i % len(ACCENTS)])
    if i < len(stages)-1:
        arrow(s, x+cw+0.02, y0+ch/2-0.12, g-0.04, 0.24)

# --- an equation slide: PREFER equation_png (real typeset math) over ASCII eq_par ---
s = add_slide(prs)
title_bar(s, "Typeset math reads as formal", kicker="equations")
footer(s, "demo deck", page=4)
# render a LaTeX-style line to a PNG (Computer Modern), then place scaled to a target height
# so glyph size is consistent across slides; color is RRGGBB hex without '#'.
_eqp = os.path.join(tempfile.gettempdir(), "slide_maker_demo_eq.png")
_wpx, _hpx = equation_png([r"\hat{x} = \mathrm{arg\,min}_{x}\,\|Ax-y\|_{2}^{2} + \lambda R(x)"],
                          _eqp, color="003C66", fontsize=30, dpi=300, mathfont="cm")
_th = 0.7; _tw = _th * _wpx / _hpx
s.shapes.add_picture(_eqp, Inches((10 - _tw) / 2), Inches(2.2), width=Inches(_tw), height=Inches(_th))
callout(s, 0.6, 4.3, 8.8, 0.6, "WHY",
        "equation_png typesets real math (italic variables, true sub/superscripts) — much "
        "cleaner than ASCII; keep eq_par only for trivial inline math.")

# --- a balanced split layout: columns() gives equal panels + symmetric margins ---
# The most common lopsided-slide tell is a left panel and right panel of different widths,
# or unequal white margins. columns(n) derives every panel from one grid so they come out
# equal by construction — reach for it on ANY text+figure / two-up / image+caption slide.
s = add_slide(prs)
title_bar(s, "Equal split panels, by construction", kicker="layout")
footer(s, "demo deck", page=5)
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

prs.save(OUT)
print("saved ->", OUT, "| slides:", len(prs.slides._sldIdLst))
