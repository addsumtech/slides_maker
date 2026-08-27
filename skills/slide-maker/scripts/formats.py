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
    # ABSOLUTE pt floors, ((role, pt), …), roles: display · section · body. Empty = the canvas is
    # projected and the inch-normalization above governs, so lint's canvas-RELATIVE floor is the
    # right one. Non-empty = the surface is PRINTED AT ACTUAL SIZE and read from a fixed distance,
    # where relative size means nothing and only the printed point size does. A poster is the case
    # this exists for: on a 33in-wide A0 canvas the relative rule would demand ~45pt body (absurd
    # for a printed page read at 1m) while deckkit's own cover cap of 46pt would print a TITLE
    # that fails to read at 5m. Both errors, in opposite directions, from one missing distinction.
    type_floors: tuple = field(default_factory=tuple)
    # (min, max) share of the canvas that content shapes may cover. Empty = not checked. A poster
    # is the case: the whole board is the deliverable, read once, standing — so an under-filled one
    # wastes the only space it gets and an over-filled one is the wall everybody walks past. A
    # projected deck has neither problem (whitespace across a SEQUENCE is rhythm, not waste), which
    # is why this is per-format and not a global rule.
    fill_range: tuple = field(default_factory=tuple)
    # Content a surface is not finished without, ((label, (keyword, …)), …). Prose everywhere else;
    # here it can be checked. See check_surface.py.
    required_sections: tuple = field(default_factory=tuple)


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
    # ── PRINTED AT ACTUAL SIZE ────────────────────────────────────────────────────────────────
    # A conference poster is not a big slide. It is read at THREE distances by a moving audience:
    # the title pulls someone in from across the hall (~5m), the section heads let them decide
    # whether to stop (~2m), and the body is read standing at it (~1m). That is why the type
    # floors below are ABSOLUTE points rather than a share of the canvas, and why they are three
    # numbers rather than one.
    #
    # `required_sections` encodes the other finding: a poster in the "billboard" style (one big
    # result, little text) tests better than a dense one, but readers of billboard posters
    # consistently ask for MORE method and MORE limitation than the style tends to include — the
    # two things a passer-by cannot reconstruct and cannot fairly judge the claim without. Both are
    # therefore required content, not density-dependent extras. A poster that genuinely has neither
    # (a purely descriptive display) waives them in writing.
    Format("poster_a0", "Poster A0 (portrait)", 33.11, 46.81, "portrait",
           "conference poster · printed A0 · read at 5m / 2m / 1m",
           margin=1.6, safe_top=0.0, safe_bottom=0.0, chrome="print",
           title_band=5.2, display_scale=2.2,
           density_units="THREE reading distances: one headline claim, 4-6 sections, "
                         "every body block short enough to read standing",
           columns_ok=True, lint_flags=("--surface",),
           aliases=("a0", "poster", "a0-portrait", "conference-poster", "海报"),
           type_floors=(("display", 90), ("section", 36), ("body", 24)),
           fill_range=(0.55, 0.90),
           required_sections=(("methods", ("method", "methods", "approach", "materials",
                                           "procedure", "protocol", "pipeline", "方法")),
                              ("limitations", ("limitation", "limitations", "caveat", "caveats",
                                               "threats to validity", "weakness", "局限",
                                               "不足")))),
    Format("poster_a1", "Poster A1 (portrait)", 23.39, 33.11, "portrait",
           "conference poster · printed A1 · smaller board, same reading distances",
           margin=1.2, safe_top=0.0, safe_bottom=0.0, chrome="print",
           title_band=3.8, display_scale=1.65,
           density_units="as A0 with LESS content, not smaller type — the floors do not scale "
                         "with the board",
           columns_ok=True, lint_flags=("--surface",),
           aliases=("a1", "a1-portrait", "poster-a1"),
           type_floors=(("display", 72), ("section", 32), ("body", 20)),
           fill_range=(0.55, 0.90),
           required_sections=(("methods", ("method", "methods", "approach", "materials",
                                           "procedure", "protocol", "pipeline", "方法")),
                              ("limitations", ("limitation", "limitations", "caveat", "caveats",
                                               "threats to validity", "weakness", "局限",
                                               "不足")))),
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


def match(w_in, h_in, tol=0.35):
    """The registered Format whose canvas these dimensions are, or None.

    A built PPTX carries only its size, so every check that wants to apply a format's contract
    has to recover the format from the canvas. Without this the registry is advisory by
    construction: build scripts opt into it and nothing downstream can tell whether they did.
    Tolerance is generous on purpose — A0 rounded to 33.1x46.8 is the same surface as 33.11x46.81.
    """
    best, best_d = None, None
    for f in FORMATS.values():
        d = abs(f.w_in - w_in) + abs(f.h_in - h_in)
        if d <= tol and (best_d is None or d < best_d):
            best, best_d = f, d
    return best


def floors(fmt):
    """{role: pt} absolute type floors, or {} when the canvas is projected rather than printed."""
    f = fmt if isinstance(fmt, Format) else get(fmt)
    return {role: pt for role, pt in f.type_floors}


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
    print(f"{'name':10s} {'label':20s} {'W×H (in)':14s} {'kind':10s} {'safe T/B':10s} "
          f"{'chrome':7s} {'cols':5s} {'type floors (pt)':22s} lint")
    for f in FORMATS.values():
        fl = " ".join(f"{r} {pt}" for r, pt in f.type_floors) or "canvas-relative"
        print(f"{f.name:10s} {f.label:20s} {f.w_in:.2f}×{f.h_in:<7.2f} {f.kind:10s} "
              f"{f.safe_top:.2f}/{f.safe_bottom:<5.2f} {f.chrome:7s} "
              f"{'yes' if f.columns_ok else 'no':5s} {fl:22s} {' '.join(f.lint_flags) or '—'}")
        print(f"{'':10s} ↳ {f.use}")
