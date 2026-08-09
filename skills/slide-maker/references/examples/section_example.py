"""section_NN_<name>.py — ONE independently-authored section of a larger deck.

It exposes `build_section(prs)`, which APPENDS this section's slides to the shared
deck. It imports the shared `style` module, so it matches every other section by
construction. The orchestrator:
  - gives this section its role/content (from the one comprehension brief + plan) and
    its START_PAGE (so page numbers are continuous across sections),
  - dispatches a subagent to author + optimize this file in parallel with the others,
  - then calls build_section during assembly (scripts/assemble.py).

While authoring, the subagent self-checks by rendering JUST this section:
    python section_NN_<name>.py        # writes <tempdir>/section_preview.pptx
    bash scripts/render_deck.sh <that path>   # look at the PNGs
    # native Windows: python scripts\render_deck.py <that path>
Because the preview uses the same style/base, what you see is what you'll get after
assembly. Iterate here, then return the finalized module.
"""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))               # find style.py
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))      # deckkit, assemble
# In the real workflow the shared module is named style.py; this example ships it as
# style_example.py, so fall back to that if you run this file before renaming/copying it.
try:
    import style
except ModuleNotFoundError:
    import style_example as style
from deckkit import add_slide, bullet, bottom_callout, vstack, measure_bullets

START_PAGE = 2   # orchestrator sets this so page numbers stay continuous

def build_section(prs):
    # 🔴 Every y below is MEASURED or ANCHORED, never hand-picked — and in a parallel-authored
    # deck that rule is stricter than usual, because no single mind sees all the sections. A
    # hand-picked 4.4 that clears the footer in THIS section, with THIS much text, silently stops
    # clearing it in the next one; `style.band()` and `bottom_callout` cannot drift, and `vstack`
    # RAISES at build time when the page is genuinely over-full instead of overlapping quietly.

    # slide 1 of this section
    s = add_slide(prs)
    style.title_bar(s, "What this section owns", kicker="section 1")
    style.register(s)                       # the shared, TAGGED signature — never hand-rolled here
    items = [
        ("Shared style ", "— palette, font, chrome all come from style.py"),
        ("No drift ", "— every section looks like one deck"),
        ("Parallel-authored ", "— built by its own subagent, assembled in order"),
    ]
    top = bottom_callout(s, 0.6, 8.7, "WHY",
                         "Coherence is centralized; only the content fans out.",
                         label_c=style.WHITE, fill=style.ACCENT, body_c=style.WHITE)
    bx, by, _, _ = style.band(s)
    vstack(s, bx, by, 8.7,
           [(measure_bullets(items, 8.7, size=16),
             lambda x, y, w: bullet(s, x, y, w, items, size=16, marker=style.ACCENT,
                                    lead_c=style.INK, body_c=style.GREY))],
           bottom=top - 0.3)
    style.footer(s, START_PAGE, tag="example deck")

    # slide 2 of this section — same helpers; the page number advances by one
    s = add_slide(prs)
    style.title_bar(s, "One idea per slide", kicker="section 1")
    style.register(s)
    items = [
        ("Advance the page ", "— pass START_PAGE + 1 to the footer (+2 for the next, ...)"),
        ("Reuse the shared helpers ", "— add_slide / bullet / callout, all styled by style.py"),
    ]
    top = bottom_callout(s, 0.6, 8.7, "NOTE",
                         "Add as many slides as the section needs — keep one idea each.",
                         label_c=style.WHITE, fill=style.ACCENT, body_c=style.WHITE)
    bx, by, _, _ = style.band(s)
    vstack(s, bx, by, 8.7,
           [(measure_bullets(items, 8.7, size=16),
             lambda x, y, w: bullet(s, x, y, w, items, size=16, marker=style.ACCENT,
                                    lead_c=style.INK, body_c=style.GREY))],
           bottom=top - 0.3)
    style.footer(s, START_PAGE + 1, tag="example deck")

    # ...add the section's further slides the same way (START_PAGE + 2, +3, ...)

if __name__ == "__main__":
    from assemble import preview_section
    out = os.path.join(tempfile.gettempdir(), "section_preview.pptx")
    preview_section(__file__, out)
    print("section preview ->", out)
