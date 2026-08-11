#!/usr/bin/env python3
"""archetypes — build a small set of *representative* slides for the DIRECTION GATE
of collaborative mode (references/collaborative-mode.md).

To let a user choose a visual direction, you show 2–3 *differentiated* directions. The
trap is showing only a pretty cover — the user then approves a look that falls apart on
real content. So show the same **archetype slides** in every direction: a cover, a
bullets+callout slide, a diagram slide, and a data/figure slide. Only the *style*
differs between directions, so the comparison is apples-to-apples and honest about how
the user's real content will look.

Each "direction" is just a style module (same interface as
references/examples/style_example.py): it must expose
    INK, ACCENT, GREY, MUTE, LINE, WHITE, W, H,
    title_bar(slide, title, kicker=""), footer(slide, page, tag="")
and optionally ACCENTS (a list, for diagram variety) and ACCENT2.

Previews render with the real pptx -> PNG pipeline (render_deck.sh), so WHAT THE USER
APPROVES IS WHAT SHIPS — the chosen direction's style module becomes the deck's style.py.

NOTE: the direction gate now shows directions as ONE HTML link via `archetypes_html.py`
(faster, shareable, no LibreOffice). This pptx variant remains useful for the **post-pick
fidelity confirmation** — after the user picks a direction in the HTML page, render the chosen
style's archetypes (or one real slide) here to confirm the pptx matches before the full build.
"""
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _load_style(path):
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("dirstyle_" + os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    d = os.path.dirname(path)
    if d not in sys.path:
        sys.path.insert(0, d)
    spec.loader.exec_module(mod)
    return mod


def build_archetypes(prs, S, name=""):
    """Append the 4 standard preview slides, styled by direction module S."""
    from deckkit import (add_slide, box, text, bullet, callout, bottom_callout, chip, arrow,
                         chrome_band, vstack, measure_bullets, slide_background, WHITE as _W)
    accents = list(getattr(S, "ACCENTS", [S.ACCENT, getattr(S, "ACCENT2", S.ACCENT)]))
    W, H = S.W, S.H

    # 1 — cover
    s = add_slide(prs)
    slide_background(s, S.INK)                   # the real <p:bg>, not a selectable full-canvas rect
    box(s, 0, 0, 0.16, H, fill=S.ACCENT)
    text(s, 0.7, H/2 - 0.7, W - 1.4, 1.0, [[("Deck Title", 38, S.WHITE, True, False)]], space_after=2)
    text(s, 0.72, H/2 + 0.05, W - 1.4, 0.5, [[("a one-line subtitle in this direction", 17, S.ACCENT, False, False)]], space_after=0)
    if name:
        text(s, 0.7, H - 0.6, W - 1.4, 0.3, [[(f"Direction: {name}", 11, S.MUTE, False, True)]], space_after=0)

    # 2 — bullets + callout (how text content reads)
    s = add_slide(prs)
    S.title_bar(s, "How content slides read", kicker="archetype")
    # 🔴 MEASURED, and here it is not a nicety. `S` is an ARBITRARY direction module: its title
    # treatment is unknown by construction, which is the entire point of a direction gate. This
    # opened at a hand-picked y=1.55 for every direction, so a direction with a taller title, a
    # larger kicker, or a title that wraps collided with its own first bullet — on the preview
    # slide the user approves the whole deck from. chrome_band() is called right after the chrome
    # is drawn and before any content, when every shape on the slide IS chrome.
    band = chrome_band(s)
    items = [("Terse points ", "a few words each"),
             ("Emphasis ", "where it matters"),
             ("Consistent ", "spacing and rhythm")]
    top = bottom_callout(s, 0.6, W - 1.2, "TAKEAWAY",
                         "One idea per slide, carried by the layout.",
                         label_c=S.WHITE, fill=S.ACCENT, body_c=S.WHITE)
    vstack(s, 0.6, band[1], W - 1.7,
           [(measure_bullets(items, W - 1.7, size=16),
             lambda x, y, w: bullet(s, x, y, w, items, size=16, marker=S.ACCENT,
                                    lead_c=S.INK, body_c=S.GREY))],
           bottom=top - 0.3)
    S.footer(s, 2, tag="direction preview")

    # 3 — diagram (how a pipeline/structure reads)
    s = add_slide(prs)
    S.title_bar(s, "How a diagram reads", kicker="archetype")
    stages = ["Input", "Process", "Model", "Output"]
    # y0 was 2.2 — a literal, so the AST scan that found the other three missed it, which is a
    # fair warning about that scan: it catches `f(s, 0.6, 1.55, ...)` and not a constant bound to
    # a name one line earlier. Same defect either way. Centre the row in the measured band.
    band = chrome_band(s)
    cw, g, x0, ch = (W - 1.2 - 3 * 0.3) / 4, 0.3, 0.6, 1.2
    y0 = band[1] + (band[3] - ch) / 2.0
    for i, nm in enumerate(stages):
        x = x0 + i * (cw + g)
        chip(s, x, y0, cw, ch, nm, "one line", accents[i % len(accents)])
        if i < len(stages) - 1:
            arrow(s, x + cw + 0.02, y0 + ch / 2 - 0.12, g - 0.04, 0.24, color=S.ACCENT)
    S.footer(s, 3, tag="direction preview")

    # 4 — data / figure (how a results slide reads)
    s = add_slide(prs)
    S.title_bar(s, "How a results slide reads", kicker="archetype")
    band = chrome_band(s)                     # again: measured, for an unknown title treatment
    fy, fh = band[1], band[3]
    box(s, 0.6, fy, 5.4, fh, fill=getattr(S, "LIGHT", S.LINE), line=S.LINE, line_w=1.0)
    text(s, 0.6, fy + fh / 2 - 0.2, 5.4, 0.4,
         [[("[ your figure / chart, shown whole ]", 12, S.MUTE, False, True)]],
         align=None, space_after=0)
    legend = [("Series A ", "baseline"), ("Series B ", "proposed")]
    note = bottom_callout(s, 6.25, W - 6.85, "WHAT TO NOTICE",
                          "The one comparison the figure makes.",
                          label_c=S.WHITE, fill=S.ACCENT, body_c=S.WHITE)
    vstack(s, 6.25, fy, W - 6.85,
           [(0.3, lambda x, y, w: text(s, x, y, w, 0.3,
                                       [[("LEGEND", 11, S.ACCENT, True, False)]], space_after=0)),
            (measure_bullets(legend, W - 6.9, size=13, gap=0.28),
             lambda x, y, w: bullet(s, x + 0.05, y, w - 0.05, legend, size=13, gap=0.28,
                                    marker=S.ACCENT, lead_c=S.INK, body_c=S.GREY))],
           gap=0.12, bottom=note - 0.3)
    S.footer(s, 4, tag="direction preview")


def preview_direction(style_path, out_path, name=""):
    """Render one direction's archetype slides to its own deck for the gate."""
    from deckkit import blank_deck
    S = _load_style(style_path)
    prs = blank_deck(S.W, S.H)
    build_archetypes(prs, S, name=name or os.path.splitext(os.path.basename(style_path))[0])
    prs.save(out_path)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python archetypes.py STYLE.py OUT.pptx [name]")
        raise SystemExit(2)
    style_path, out = sys.argv[1], sys.argv[2]
    nm = sys.argv[3] if len(sys.argv) > 3 else ""
    print("direction preview ->", preview_direction(style_path, out, nm))
