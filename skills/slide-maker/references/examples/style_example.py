"""style.py — the SINGLE source of truth for a multi-section deck.

Copy this into your deck's working dir as `style.py` and tune it to the purpose
(see references/design-by-purpose.md). EVERY section module imports THIS, so sections
authored in parallel by different subagents cannot drift: one palette, one font, one
title/footer treatment, one set of layout constants. Coherence lives here and nowhere
else — sections never redefine colours or chrome, they call these helpers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import deckkit
from deckkit import add_slide, box, text, RGBColor, PP_ALIGN  # noqa: F401 (re-exported)

# ---- one palette for the whole deck (tune to the chosen purpose) ----
INK    = RGBColor(0x14, 0x1C, 0x2B)   # titles / strong text
ACCENT = RGBColor(0x2D, 0x5B, 0xE3)   # primary accent
GREY   = RGBColor(0x55, 0x61, 0x70)   # body
MUTE   = RGBColor(0x96, 0xA2, 0xB4)   # captions / footer
LINE   = RGBColor(0xDD, 0xE3, 0xEA)   # hairlines
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Calibri"          # set once for the whole deck
deckkit.FONT = FONT        # deckkit resolves FONT at call time, so every section inherits

W, H = 10.0, 5.625         # 16:9

def base_deck():
    """The base every section is appended to (assemble.build_deck makes its own, but
    use this for local previews so previews match the final deck)."""
    return deckkit.blank_deck(W, H)

def title_bar(s, title, kicker=""):
    """One title treatment for every content slide across every section."""
    if kicker:
        text(s, 0.6, 0.34, W - 1.2, 0.3, [[(kicker.upper(), 11, ACCENT, True, False)]], space_after=0)
        ty = 0.6
    else:
        ty = 0.45
    text(s, 0.6, ty, W - 1.2, 0.7, [[(title, 26, INK, True, False)]], space_after=0)
    box(s, 0.62, ty + 0.66, 1.0, 0.045, fill=ACCENT)

def footer(s, page, tag=""):
    """One footer treatment; the orchestrator assigns each section its page numbers."""
    if tag:
        text(s, 0.6, H - 0.4, 6.0, 0.3, [[(tag, 8.5, MUTE, False, False)]], space_after=0)
    text(s, W - 1.0, H - 0.4, 0.6, 0.3, [[(str(page), 9, MUTE, True, False)]],
         align=PP_ALIGN.RIGHT, space_after=0)


# ─── the two things sections must NOT each decide for themselves ────────────────────────
# Both live here for the same reason the palette does: sections are authored in PARALLEL by
# separate agents, so anything a section computes locally drifts silently between sections.

def band(s, kicker=True):
    """The safe content rect (x, y, w, h) for THIS deck's chrome — below the title rule,
    above the footer band.

    `deckkit.content_band` defaults to `top=1.15`, which is deckkit's OWN title_bar. This deck
    has its own title treatment, so the top edge is derived from it here, once: the rule sits at
    ``ty + 0.66`` and is 0.045 tall, plus breathing room. A section that calls the bare
    `content_band(s)` gets deckkit's number, not this deck's, and lands its first block ~0.4in
    too high — the kind of drift that is invisible per-section and obvious once assembled.
    """
    return deckkit.content_band(s, top=(0.6 if kicker else 0.45) + 0.66 + 0.045 + 0.24)


def register(s, loud=False):
    """This deck's register signature — ONE tagged device, shared by every section.

    Hand-rolling the mark per section is how a deck ends up with three slightly different
    versions of its own signature, and — because a hand-rolled mark carries no tag — how
    `TEXT_OVER_MOTIF` and the <=3-loud-appearance budget end up watching a deck they cannot see.
    Measured on a real 14-page build: 383 shapes, ZERO motif tags. Pass ``loud=True`` only on a
    hero page (cover / section opener).
    """
    return deckkit.register_mark(s, "arcs", corner="tr", color=ACCENT,
                                 size=(2.0 if loud else 1.1), loud=loud)
