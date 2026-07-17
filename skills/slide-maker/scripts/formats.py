#!/usr/bin/env python3
"""formats.py — named CANVAS FORMATS + per-format layout tokens for deckkit builds.

One deck skill, many canvases: a conference talk (16:9), a legacy-projector deck (4:3),
a rednote/小红书 image-note (3:4), an Instagram/Facebook square post (1:1), a Story/Reels/
Shorts vertical cover (9:16), and an A4 print document — each is a DIFFERENT design
surface, not a resized 16:9 slide. This module is the single registry of those surfaces:
dimensions, safe zones, chrome policy, density budget, and layout DNA, consumed by build
scripts and documented (with the per-format design rules) in
``references/canvas-formats.md``.

THE INCH-NORMALIZATION PRINCIPLE (why font tokens survive format switches):
a .pptx canvas is measured in inches and projected to fill the viewer's screen, so a
run's *relative* size = pt / canvas-inches. The registry fixes each format's canvas
inches so the SAME pt tokens (e.g. 14pt body · 27pt title) land at the right relative
size per surface: on the 10in-wide 16:9 baseline 14pt ≈ 1.9% of width; on the 5.625in
story canvas the same 14pt ≈ 3.5% — automatically bigger for a phone held at arm's
length. Build scripts therefore keep ONE type scale and let the canvas do the scaling;
only display/cover type takes a per-format multiplier (``display_scale``).

Usage in a build script:
    import formats
    FMT = formats.get("story")               # by name or alias ("9:16", "reels", …)
    prs = formats.blank_deck(FMT)            # deckkit deck at the format's size
    x, y, w, h = formats.band(FMT, title=True)   # safe content rect (margins + UI zones)
    if FMT.columns_ok: ... side-by-side ...  else: ... stack vertically ...
    # chrome: dk.footer(...) only when FMT.chrome == "full" / "print"
    # lint:   pass FMT.lint_flags to lint_deck.py

CLI:  python3 formats.py            # list the registry
"""
from dataclasses import dataclass, field

__all__ = ["Format", "FORMATS", "get", "blank_deck", "band", "names"]


@dataclass(frozen=True)
class Format:
    name: str            # canonical key
    label: str           # human name for plans/checkpoints
    w_in: float          # canvas width (inches)
    h_in: float          # canvas height (inches)
    kind: str            # "landscape" | "portrait" | "square"
    use: str             # one-line "when to use"
    margin: float        # outer margin (in) — L/R for all, T/B before safe zones
    safe_top: float      # extra top inset (in) reserved for platform UI overlays
    safe_bottom: float   # extra bottom inset (in) — swipe bar / caption / CTA overlays
    chrome: str          # "full" (title_bar+footer) | "social" (no footer, minimal marks) | "print" (doc header/footer + page no.)
    title_band: float    # vertical allowance (in) a standard title block takes in this format
    display_scale: float # cover/display type multiplier vs the 16:9 cover tokens
    density_units: str   # content-density guidance for the planner
    columns_ok: bool     # side-by-side column splits advisable on this surface?
    lint_flags: tuple = field(default_factory=tuple)  # extra lint_deck.py flags
    aliases: tuple = field(default_factory=tuple)


FORMATS = {f.name: f for f in [
    Format("wide", "PPT 16:9", 10.0, 5.625, "landscape",
           "talks · meetings · screens (the default deck)",
           margin=0.55, safe_top=0.0, safe_bottom=0.0, chrome="full",
           title_band=1.30, display_scale=1.0,
           density_units="presented budget (~40 words); balanced fullness",
           columns_ok=True, lint_flags=(),
           aliases=("16:9", "16x9", "ppt", "landscape", "widescreen", "default")),
    Format("classic", "PPT 4:3", 10.0, 7.5, "landscape",
           "legacy projectors · some academic defenses/venues",
           margin=0.55, safe_top=0.0, safe_bottom=0.0, chrome="full",
           title_band=1.30, display_scale=1.0,
           density_units="presented budget; the extra height takes ONE more stacked row, not smaller type",
           columns_ok=True, lint_flags=(),
           aliases=("4:3", "4x3", "standard")),
    Format("square", "Square 1:1", 7.5, 7.5, "square",
           "Instagram/Facebook feed post · square social card",
           margin=0.5, safe_top=0.0, safe_bottom=0.0, chrome="social",
           title_band=1.15, display_scale=1.15,
           density_units="ONE idea per card; a hook + 3-5 scannable points max",
           columns_ok=False, lint_flags=("--selfread",),
           aliases=("1:1", "1x1", "instagram", "ins", "facebook", "post")),
    Format("red", "小红书 3:4", 7.5, 10.0, "portrait",
           "rednote/小红书 image note · portrait social card",
           margin=0.5, safe_top=0.35, safe_bottom=0.55, chrome="social",
           title_band=1.15, display_scale=1.25,
           density_units="ONE idea per card; list-style cards may carry 4-6 short rows",
           columns_ok=False, lint_flags=("--selfread",),
           aliases=("3:4", "3x4", "xiaohongshu", "小红书", "rednote", "portrait")),
    Format("story", "Story 9:16", 5.625, 10.0, "portrait",
           "IG/WeChat story · Reels/Shorts/抖音 cover · vertical mobile",
           margin=0.45, safe_top=1.30, safe_bottom=1.80, chrome="social",
           title_band=1.05, display_scale=1.35,
           density_units="ONE message; big type; nothing that needs study",
           columns_ok=False, lint_flags=("--selfread",),
           aliases=("9:16", "9x16", "vertical", "reels", "shorts", "douyin", "抖音", "tiktok")),
    Format("a4", "A4 print (portrait)", 8.27, 11.69, "portrait",
           "print handout · one-pager · leave-behind document",
           margin=0.75, safe_top=0.0, safe_bottom=0.0, chrome="print",
           title_band=1.20, display_scale=1.0,
           density_units="self-read prose is the deliverable; document density is correct here",
           columns_ok=True, lint_flags=("--selfread",),
           aliases=("print", "a4-portrait", "handout", "onepager", "one-pager")),
]}

_ALIAS = {}
for _f in FORMATS.values():
    _ALIAS[_f.name] = _f.name
    for _a in _f.aliases:
        _ALIAS[_a.lower()] = _f.name


def names():
    """Canonical format names, registry order."""
    return list(FORMATS)


def get(name):
    """Resolve a Format by canonical name or alias (case-insensitive). Raises with the
    known names on a miss, so a typo fails loudly at the top of the build."""
    key = _ALIAS.get(str(name).strip().lower())
    if key is None:
        raise KeyError(f"unknown canvas format {name!r} — known: "
                       + ", ".join(f"{f.name} ({f.label})" for f in FORMATS.values()))
    return FORMATS[key]


def blank_deck(fmt):
    """A deckkit deck at the format's canvas size. Accepts a Format or a name/alias."""
    import deckkit as dk
    f = fmt if isinstance(fmt, Format) else get(fmt)
    return dk.blank_deck(f.w_in, f.h_in)


def band(fmt, *, title=True):
    """The SAFE CONTENT RECT (x, y, w, h) for this format: outer margins + the format's
    platform-UI safe zones (story/rednote overlays) + a FOOTER RESERVE on chrome-bearing
    formats (full/print draw a footer — content anchored at the band bottom must stay
    above it), minus the title band when ``title=True``. This is the format-aware
    analogue of ``deckkit.content_band`` — use it on any non-default format so content
    never lands under a profile bar, swipe zone, or the deck's own footer. A full-bleed
    hero/cover ignores it deliberately (but keeps TEXT inside it)."""
    f = fmt if isinstance(fmt, Format) else get(fmt)
    x = f.margin
    y = f.safe_top + (f.title_band if title else f.margin * 0.6)
    w = f.w_in - 2 * f.margin
    footer_reserve = 0.46 if f.chrome in ("full", "print") else 0.0
    h = f.h_in - y - max(f.safe_bottom, f.margin * 0.7, footer_reserve)
    return x, y, w, h


if __name__ == "__main__":
    print(f"{'name':8s} {'label':18s} {'W×H (in)':12s} {'kind':10s} {'safe T/B':10s} "
          f"{'chrome':7s} {'cols':5s} lint")
    for f in FORMATS.values():
        print(f"{f.name:8s} {f.label:18s} {f.w_in:.2f}×{f.h_in:<6.2f} {f.kind:10s} "
              f"{f.safe_top:.2f}/{f.safe_bottom:<5.2f} {f.chrome:7s} "
              f"{'yes' if f.columns_ok else 'no':5s} {' '.join(f.lint_flags) or '—'}")
        print(f"{'':8s} ↳ {f.use}")
