#!/usr/bin/env python3
"""Build a register's SURFACE, not just its palette — the half `presets.apply()` never had.

WHY. `apply()` calls exactly four things: `set_palette`, `set_geometry`, `set_ground` and the font
setters. That is a colourway and a corner radius. Measured, and rendered: one identical page taken
through all 18 presets produced 18 pages differing only in ground colour, ink colour, accent, one
font swap and a line weight. memphis had none of its colour bands or scattered marks, bauhaus none
of its oversized primitives, glassmorphism no glass, risograph no overprint, terminal no scanlines.
Every preset's `surface` field describes those things correctly — in prose, for an author to read
and build by hand, which in practice meant they were never built.

WHAT A KIT IS. Three things, because a register lives in all three and a background alone is a
wallpaper:

    ground(slide, register, role=...)   paints the register's own furniture and RETURNS the content
                                        rect that is left — like `title_bar()` returning its
                                        content top. Marks stay in the margins; nothing is painted
                                        into the band it hands back.
    card(slide, register, x, y, w, h)   the register's CARD FORM. Same call, different object: a
                                        memphis banded card, a bauhaus hard square, a riso sticker
                                        with a crisp offset, a glass panel, a terminal output block.
                                        This is what stops the eighteen pages being one page.
    marks                               the public primitives the grounds are built from
                                        (`halftone`, `starburst`, `boomerang`, `zigzag`, `tri`,
                                        `scanlines`, `color_band`) — reusable in a bespoke register.

DETERMINISM. Placement varies per page so a deck does not repeat one arrangement 12 times, but it
varies by INDEX, never by a random number: the same deck built twice is byte-identical, which the
render-parallel test and every diff-based check depend on.

IT OBEYS ITS OWN REGISTER. `check_register_guard` reads the same `presets.FORBIDS` these builders
are written against — bauhaus gets exactly ONE oversized primitive (never a confetti), risograph's
halftone is discrete dots rather than a gradient, terminal stays monospace, and every shape here
goes through deckkit's `_flat` + `shadow.inherit = False` so nothing arrives with a theme shadow.
The selftest runs the guard over every kit's own output, so a builder that violates the register it
claims to build fails here rather than in a delivered deck.

    python3 scripts/register_surface.py --selftest
    python3 scripts/register_surface.py --sample <out.pptx>   # one page per kit, to LOOK at
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pptx.enum.shapes import MSO_SHAPE            # noqa: E402
from pptx.util import Inches, Pt                  # noqa: E402

import deckkit as dk                              # noqa: E402

MARGIN = 0.45                  # marks live outside the content band, never on top of it
LOUD_MAX = 3                   # the motif budget this skill already states, applied to the ground


# ---------------------------------------------------------------------------- deterministic spread

def _h(index, salt=0):
    """A stable small integer from a page index — placement must not need a random number.

    `Math.random`-style variation makes two builds of one deck differ, which breaks the byte-identity
    the parallel-render check proves and makes every visual diff untrustworthy. Varying by index
    gives the same spread every time and still stops twelve pages sharing one arrangement.
    """
    v = (int(index) + 1) * 2654435761 + salt * 40503
    return (v ^ (v >> 13)) & 0xFFFF


def _pick(seq, index, salt=0):
    return seq[_h(index, salt) % len(seq)]


def _frac(index, salt=0):
    return (_h(index, salt) % 1000) / 1000.0


_MARKS = []                    # rects painted by the CURRENT ground() call, minus textures


def _record(x, y, w, h, texture):
    """A LOUD mark is one that must clear the content band; a texture may lie under it.

    The difference is not decorative bookkeeping. Scanlines, glows and a faint screen are grounds:
    type sits on them and the contrast checks judge the result. A triangle, a disc, a burst, an
    oversized primitive are objects: type landing on one is the collision a reader sees first, and
    this module's own docstring promised it could not happen — while the first render put a memphis
    triangle through a card corner and a bauhaus disc through a third card. A promise with nothing
    measuring it is how that ships.
    """
    if not texture:
        _MARKS.append((x, y, x + w, y + h))


def _blend(a, b, t):
    """`t` of the way from colour `a` to colour `b` — how a texture is made faint on any ground."""
    A, B = dk._as_rgb(a), dk._as_rgb(b)          # RGBColor is a bytes-like triple; the API only
    return dk.RGBColor(*[int(round(A[i] + (B[i] - A[i]) * t))   # accepts RGBColor back, not a tuple
                         for i in range(3)])


def _shape(slide, kind, x, y, w, h, fill=None, line=None, line_w=1.0, rot=None, texture=False):
    """One primitive, flattened the way every deckkit helper flattens: no theme style, no shadow."""
    _record(x, y, w, h, texture)
    s = dk._flat(slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h)))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = dk._as_rgb(fill)
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = dk._as_rgb(line)
        s.line.width = Pt(line_w * getattr(dk, "RULE_W_SCALE", 1.0))
    s.shadow.inherit = False
    if rot:
        s.rotation = rot
    return s


# ------------------------------------------------------------------------------------------ marks

def color_band(slide, y, h, color, *, x=0.0, w=None):
    """A full-bleed band of colour. memphis's header bands, riso's ink bar, a section rule."""
    W, _H_ = dk._slide_size(slide)
    return _shape(slide, MSO_SHAPE.RECTANGLE, x, y, (W - x) if w is None else w, h, fill=color)


def tri(slide, x, y, w, h, color, *, direction="up", line=None, line_w=1.0):
    """An isosceles triangle — bauhaus's third primitive, memphis's scatter, midcentury's wedge."""
    rot = {"up": 0, "right": 90, "down": 180, "left": 270}.get(direction, 0)
    return _shape(slide, MSO_SHAPE.ISOSCELES_TRIANGLE, x, y, w, h,
                  fill=color, line=line, line_w=line_w, rot=rot)


def zigzag(slide, x, y, w, h, color, *, teeth=5, line_w=2.5, texture=False):
    """A memphis squiggle, drawn as a real polyline of hairlines rather than a picture."""
    _record(x, y, w, h, texture)
    out = []
    step = w / max(1, teeth)
    for i in range(teeth):
        x0 = x + i * step
        y0 = y + (0 if i % 2 == 0 else h)
        y1 = y + (h if i % 2 == 0 else 0)
        c = dk._flat(slide.shapes.add_connector(
            1, Inches(x0), Inches(y0), Inches(x0 + step), Inches(y1)))
        c.line.color.rgb = dk._as_rgb(color)
        c.line.width = Pt(line_w * getattr(dk, "RULE_W_SCALE", 1.0))
        c.shadow.inherit = False
        out.append(c)
    return out


def halftone(slide, x, y, w, h, color, *, cols=14, rows=8, r_max=0.11, r_min=0.02, index=0,
             texture=False):
    """A riso/print DOT FIELD that ramps across the rect — discrete dots, never a gradient.

    risograph's own guard forbids gradients (its fills are flat and its shadows hard), so the
    obvious way to fake a tonal ramp is exactly the thing the register prohibits. Real riso tone is
    a screen: the dots stay the same colour and change SIZE, which is what this draws.
    """
    _record(x, y, w, h, texture)
    out = []
    dx, dy = w / cols, h / rows
    for cx in range(cols):
        t = cx / max(1, cols - 1)
        r = r_max - (r_max - r_min) * t
        for cy in range(rows):
            if r <= 0.005:
                continue
            out.append(_shape(slide, MSO_SHAPE.OVAL,
                              x + cx * dx + (dx - r) / 2, y + cy * dy + (dy - r) / 2,
                              r, r, fill=color, texture=True))   # the FIELD was recorded, not each dot
    return out


def starburst(slide, cx, cy, r, color, *, rays=12, line_w=1.2, index=0, texture=False):
    """The midcentury atomic burst: hairlines radiating from a point, alternating length."""
    import math
    _record(cx - r, cy - r, 2 * r, 2 * r, texture)
    out = []
    for i in range(rays):
        a = (2 * math.pi * i / rays) + (_frac(index, 7) * 0.4)
        rr = r * (1.0 if i % 2 == 0 else 0.62)
        c = dk._flat(slide.shapes.add_connector(
            1, Inches(cx), Inches(cy), Inches(cx + rr * math.cos(a)), Inches(cy + rr * math.sin(a))))
        c.line.color.rgb = dk._as_rgb(color)
        c.line.width = Pt(line_w * getattr(dk, "RULE_W_SCALE", 1.0))
        c.shadow.inherit = False
        out.append(c)
    return out


def boomerang(slide, x, y, w, h, color, *, line_w=None, index=0):
    """The other midcentury mark: an open arc, drawn as a thick-stroked ARC primitive.

    Stroked rather than filled, because a filled crescent at this scale reads as a blob and the
    midcentury mark is a GESTURE — the eye should follow it, not weigh it.
    """
    s = _shape(slide, MSO_SHAPE.ARC, x, y, w, h, fill=None,
               line=color, line_w=line_w if line_w is not None else 3.0,
               rot=_pick((0, 30, 200, 250), index, 11))
    return s


def scanlines(slide, color, *, spacing=0.09, line_w=0.75, top=0.0, bottom=None):
    """terminal's phosphor texture: faint horizontal hairlines over the whole surface.

    Kept to a hairline at the register's MUTE colour — a scanline that competes with body type is
    a screen effect, and the point is a screen you can still read.
    """
    W, H = dk._slide_size(slide)
    bottom = H if bottom is None else bottom
    out, yy = [], top          # a texture by definition: type sits ON it, contrast judges it
    while yy < bottom:
        c = dk._flat(slide.shapes.add_connector(1, Inches(0), Inches(yy), Inches(W), Inches(yy)))
        c.line.color.rgb = dk._as_rgb(color)
        c.line.width = Pt(line_w)
        c.shadow.inherit = False
        out.append(c)
        yy += spacing
    return out


# ------------------------------------------------------------------------------------- the grounds

def _band_below(slide, y_top, *, side_margin=0.6, footer_gap=0.55):
    W, H = dk._slide_size(slide)
    return (side_margin, y_top, W - 2 * side_margin, H - y_top - footer_gap)


def _memphis(slide, role, index):
    """cream ground · a colour band that TITLES the page · 2–3 scattered marks in the margins."""
    W, H = dk._slide_size(slide)
    accent = _pick((dk.MAGENTA, dk.BLUE, dk.TEAL), index, 1)
    band_h = 0.85 if role in ("cover", "section") else 0.5
    color_band(slide, 0, band_h, accent)
    if role in ("cover", "section"):
        color_band(slide, band_h, 0.14, dk.DEEP)
    # Marks live OUTSIDE the band this returns — memphis scatters in the margin, it does not
    # scribble over the text. Three at most: the motif budget, applied to the furniture.
    top = band_h + 0.46
    foot = 0.62                                  # the bottom margin the marks live in
    marks = [
        lambda: zigzag(slide, W - 1.7, H - 0.5, 1.1, 0.26, dk.DEEP, teeth=4),
        lambda: tri(slide, 0.2, H - 0.56, 0.42, 0.42, dk.TEAL, line=dk.DEEP, line_w=1.5),
        lambda: _shape(slide, MSO_SHAPE.OVAL, W - 0.62, band_h + 0.06, 0.32, 0.32, fill=dk.MAGENTA),
        lambda: _shape(slide, MSO_SHAPE.PIE, 0.2, band_h + 0.04, 0.36, 0.36, fill=dk.BLUE),
    ]
    seen = set()
    for k in range(LOUD_MAX):                    # LOUD_MAX distinct marks, never the same one twice
        j = _h(index, 20 + k) % len(marks)
        while j in seen:
            j = (j + 1) % len(marks)
        seen.add(j)
        marks[j]()
    return _band_below(slide, top, side_margin=0.7, footer_gap=foot)


def _bauhaus(slide, role, index):
    """ONE oversized primitive, bleeding off an edge, in a primary — never a confetti of shapes."""
    W, H = dk._slide_size(slide)
    color = _pick((dk.MAGENTA, dk.BLUE, dk.TEAL), index, 2)
    size = 4.6 if role in ("cover", "section") else 3.4
    corner = _pick(("tr", "br", "bl"), index, 3)
    x = W - size * 0.55 if corner in ("tr", "br") else -size * 0.45
    y = -size * 0.35 if corner == "tr" else H - size * 0.6
    kind = _pick((MSO_SHAPE.OVAL, MSO_SHAPE.RECTANGLE, MSO_SHAPE.ISOSCELES_TRIANGLE), index, 4)
    _shape(slide, kind, x, y, size, size, fill=color,
           rot=(_pick((0, 180), index, 5) if kind == MSO_SHAPE.ISOSCELES_TRIANGLE else None))
    # The hairline datum bauhaus composes against. One rule, full bleed, the register's ink.
    color_band(slide, H - 0.42, 0.03, dk.DEEP)
    # Derived from where the primitive ACTUALLY landed, not from a guess at where it lands: the
    # guessed version left a 0.23in overlap that put the hero disc through the third card.
    pad = 0.3
    if corner in ("tr", "br"):
        left, right = 0.7, x - pad
    else:
        left, right = x + size + pad, W - 0.7
    top = 0.85
    bottom = (H - 0.62) if corner == "tr" else min(H - 0.62, y - pad)
    return (left, top, max(3.2, right - left), max(1.6, bottom - top))


def _risograph(slide, role, index):
    """Two flat inks, deliberately out of register, plus a screen — the whole look is the misfit."""
    W, H = dk._slide_size(slide)
    a = _pick((dk.MAGENTA, dk.BLUE), index, 6)
    b = dk.TEAL if a is not dk.TEAL else dk.MAGENTA
    bar_y = 0.0 if role in ("cover", "section") else H - 0.72
    bar_h = 1.05 if role in ("cover", "section") else 0.4
    color_band(slide, bar_y, bar_h, a)
    color_band(slide, bar_y + 0.055, bar_h, b, x=0.075, w=W - 0.15)   # the OFFSET plate
    if bar_y == 0:                                # cover: bar on top, screen in the bottom margin
        top, bottom = bar_h + 0.4, H - 0.95
        halftone(slide, W - 2.6, H - 0.82, 2.4, 0.66, a, rows=4, r_max=0.09, index=index)
    else:                                         # content: bar at the foot, screen in the top one
        top, bottom = 0.95, bar_y - 0.28
        halftone(slide, W - 2.6, 0.14, 2.4, 0.62, a, rows=4, r_max=0.09, index=index)
    return (0.65, top, W - 1.3, bottom - top)


def _terminal(slide, role, index):
    """A screen: scanlines, a prompt line for chrome, a block cursor. Everything monospace."""
    W, H = dk._slide_size(slide)
    # Faint and wide: at MUTE on 0.11in this rendered as ruled notebook paper with the body type
    # sitting on the rules. A phosphor screen is a texture you stop seeing; blend it most of the
    # way back to the ground and give it room.
    scanlines(slide, _blend(dk.GROUND, dk.MUTE, 0.3), spacing=0.2, line_w=0.6)
    dk.text(slide, 0.55, 0.3, W - 1.1, 0.3,
            [[("user@deck", 11, dk.MUTE, False, False, dk.MONO),
              (":~$ ", 11, dk.MUTE, False, False, dk.MONO),
              (("cover" if role == "cover" else "slide --{}".format(role)),
               11, dk.MAGENTA, True, False, dk.MONO)]])
    _shape(slide, MSO_SHAPE.RECTANGLE, W - 0.72, H - 0.55, 0.16, 0.26, fill=dk.MAGENTA)
    return _band_below(slide, 0.82, side_margin=0.55, footer_gap=0.8)


def _midcentury(slide, role, index):
    """Atomic-age marks on warm paper: a burst, a boomerang, one hairline datum."""
    W, H = dk._slide_size(slide)
    side = _pick(("l", "r"), index, 9)
    cx = (W - 0.95) if side == "r" else 0.95
    starburst(slide, cx, H - 0.5, 0.42, _pick((dk.MAGENTA, dk.TEAL), index, 10),
              rays=_pick((10, 12, 14), index, 12), index=index)
    boomerang(slide, (0.4 if side == "r" else W - 1.9), 0.1, 1.4, 0.62, dk.BLUE, index=index)
    color_band(slide, H - 0.98, 0.02, dk.DEEP)
    return _band_below(slide, 0.86, side_margin=0.75, footer_gap=1.05)


def _glassmorphism(slide, role, index):
    """A lit dark ground — glass only reads as glass on something with light behind it."""
    W, H = dk._slide_size(slide)
    dk.glow(slide, _frac(index, 13) * (W - 4.0) + 2.0, 1.2, 6.0, 4.4,
            _pick((dk.MAGENTA, dk.BLUE), index, 14))
    dk.glow(slide, _frac(index, 15) * (W - 3.0) + 1.5, H - 1.0, 5.0, 3.6, dk.TEAL, alpha=0.4)
    return _band_below(slide, 0.9, side_margin=0.7, footer_gap=0.7)


GROUNDS = {
    "memphis": _memphis,
    "bauhaus": _bauhaus,
    "risograph": _risograph,
    "terminal": _terminal,
    "midcentury": _midcentury,
    "glassmorphism": _glassmorphism,
}


# --------------------------------------------------------------------------------------- the cards

def _card_memphis(slide, x, y, w, h, label=None):
    body = dk.box(slide, x, y, w, h, fill=dk.TINT, line=dk.DEEP, line_w=1.6, round=True, r=0.12)
    head = dk.box(slide, x, y, w, 0.42, fill=dk.MAGENTA, corners="top", r=0.12)
    if label:
        dk.text(slide, x + 0.18, y + 0.05, w - 0.36, 0.32,
                [[(label, 12, dk.on(dk.MAGENTA), True, False)]])   # auto-contrast on the band
    return body, head


def _card_bauhaus(slide, x, y, w, h, label=None):
    return dk.box(slide, x, y, w, h, fill=dk.TINT, line=dk.DEEP, line_w=2.2), None


def _card_risograph(slide, x, y, w, h, label=None):
    return dk.offset_shadow(slide, x, y, w, h, dk.TINT, shadow=dk.MAGENTA,
                            line=dk.DEEP, line_w=1.6, round=False), None


def _card_terminal(slide, x, y, w, h, label=None):
    return dk.box(slide, x, y, w, h, fill=None, line=dk.MUTE, line_w=1.0), None


def _card_midcentury(slide, x, y, w, h, label=None):
    return dk.box(slide, x, y, w, h, fill=dk.TINT, line=dk.DEEP, line_w=1.0, round=True, r=0.06), None


def _card_glass(slide, x, y, w, h, label=None):
    return dk.glass_card(slide, x, y, w, h, dk.BLUE), None


CARDS = {
    "memphis": _card_memphis,
    "bauhaus": _card_bauhaus,
    "risograph": _card_risograph,
    "terminal": _card_terminal,
    "midcentury": _card_midcentury,
    "glassmorphism": _card_glass,
}


# ------------------------------------------------------------------------------------ the public API

def has(register):
    """Is there a surface kit for this register yet? Six of eighteen — the rest say so out loud."""
    return str(register or "").strip().lower() in GROUNDS


def ground(slide, register, *, role="content", index=0):
    """Paint the register's own surface and RETURN the content rect `(x, y, w, h)` left over.

    Call it as the FIRST thing on a slide, before any content: everything it draws is furniture,
    and furniture goes behind. The rect it returns is where content may go — nothing this function
    painted overlaps it, which is the contract that lets a builder stay hands-off about placement.

    `role` is the page's job (`cover` / `section` / `content` / `closer`): a cover gets the loud
    version of the register, a content page the quiet one, because a register applied at full
    volume on every page is the "flashy but unreadable" failure this skill keeps naming.
    """
    reg = str(register or "").strip().lower()
    if reg not in GROUNDS:
        raise KeyError(
            "no surface kit for register {!r} — kits exist for {}. Do NOT silently fall back to a "
            "plain page: a caller that asked for a register's surface and got a blank one would "
            "ship the colourway-only deck this module was written to end.".format(
                register, ", ".join(sorted(GROUNDS))))
    del _MARKS[:]
    band = GROUNDS[reg](slide, str(role or "content").lower(), int(index))
    bx, by, bw, bh = band
    clash = [m for m in _MARKS
             if min(bx + bw, m[2]) - max(bx, m[0]) > 0.02
             and min(by + bh, m[3]) - max(by, m[1]) > 0.02]
    if clash:
        raise AssertionError(
            "{}'s ground painted {} loud mark(s) INTO the content rect it returned "
            "({}) — a caller that trusts the rect would set type on top of them. Marks belong in "
            "the margins; a full-bleed ground passes texture=True. Offenders: {}".format(
                reg, len(clash), tuple(round(v, 2) for v in band),
                [tuple(round(v, 2) for v in c) for c in clash]))
    return band


def card(slide, register, x, y, w, h, *, label=None):
    """The register's CARD FORM at this rect. Same call on every register, a different object.

    This is the half that makes the pages differ in FORM rather than in colour: a memphis banded
    card, a bauhaus hard square with a heavy keyline, a riso sticker with a crisp offset plate, a
    frosted glass panel, a terminal output block with no fill at all. Returns `(body, header)`;
    `header` is None for the registers whose card has no band.
    """
    reg = str(register or "").strip().lower()
    if reg not in CARDS:
        raise KeyError("no card form for register {!r} — kits exist for {}".format(
            register, ", ".join(sorted(CARDS))))
    return CARDS[reg](slide, x, y, w, h, label)


def registers():
    """The registers that have a kit, sorted — for a gallery, a doc, or a coverage report."""
    return sorted(GROUNDS)


# ------------------------------------------------------------------------------------------ sample

def sample(out_path):
    """One page per kit, same content, so the difference is the REGISTER and nothing else."""
    import presets
    prs = None
    for i, reg in enumerate(registers()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            presets.apply(reg)
        if prs is None:
            prs = dk.blank_deck()
        s = dk.add_slide(prs)
        role = "cover" if i == 0 else "content"
        bx, by, bw, bh = ground(s, reg, role=role, index=i)
        dk.text(s, bx, by, bw, 0.7,
                [[(reg.replace("_", " ").upper(), 30, dk.DEEP, True, False)]])
        cw = (bw - 0.6) / 3.0
        for c in range(3):
            cx = bx + c * (cw + 0.3)
            card(s, reg, cx, by + 0.95, cw, bh - 1.15, label="CARD {}".format(c + 1))
            dk.text(s, cx + 0.22, by + 1.55, cw - 0.44, bh - 1.9,
                    [[("The same three cards, the same three sentences, on every one of these "
                       "pages.", 12, dk.DEEP, False, False)]])
    prs.save(str(out_path))
    return out_path


def _selftest():
    import presets
    import check_register_guard as guard
    import tempfile
    ok, bad = [], []
    tmp = Path(tempfile.mkdtemp(prefix="regsurf-"))

    snap = {k: getattr(dk, k) for k in dir(dk) if k.isupper()}
    try:
        for reg in registers():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                presets.apply(reg)
            prs = dk.blank_deck()
            for i, role in enumerate(("cover", "content", "section")):
                s = dk.add_slide(prs)
                bx, by, bw, bh = ground(s, reg, role=role, index=i)
                W, H = dk._slide_size(s)
                if not (bx >= 0 and by >= 0 and bw > 3.0 and bh > 1.5
                        and bx + bw <= W + 1e-6 and by + bh <= H + 1e-6):
                    bad.append("{} {}: content rect {} is off-canvas or too small".format(
                        reg, role, (bx, by, bw, bh)))
                cw, ch = min(3.2, bw), min(2.0, bh - 0.9)
                card(s, reg, bx, by + 0.8, cw, ch, label="X")
                dk.text(s, bx + 0.2, by + 1.35, cw - 0.4, ch - 0.75,
                        [[("a card carries content", 12, dk.DEEP, False, False)]])
            p = tmp / "{}.pptx".format(reg)
            prs.save(str(p))
            viol, _facts = guard.check(p, register=reg)
            (ok if not viol else bad).append(
                "`{}`'s own surface kit obeys `{}`'s prohibitions".format(reg, reg)
                if not viol else "{} violates its own register: {}".format(
                    reg, [c for c, _m in viol]))
    finally:
        for k, v in snap.items():
            setattr(dk, k, v)

    # Determinism: the same index must give the same page, or every diff-based check is noise.
    def _fingerprint():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            presets.apply("memphis")
        prs = dk.blank_deck()
        s = dk.add_slide(prs)
        ground(s, "memphis", role="content", index=7)
        return [(sh.shape_type, sh.left, sh.top, sh.width, sh.height) for sh in s.shapes]
    snap2 = {k: getattr(dk, k) for k in dir(dk) if k.isupper()}
    try:
        a, b = _fingerprint(), _fingerprint()
    finally:
        for k, v in snap2.items():
            setattr(dk, k, v)
    (ok if a == b else bad).append(
        "the same page index builds the same page twice — placement varies by INDEX, never by a "
        "random number, so a deck built twice stays byte-identical"
        if a == b else "non-deterministic ground")

    try:
        ground(dk.add_slide(dk.blank_deck()), "swiss")
        bad.append("a register with no kit was silently given a blank surface")
    except KeyError:
        ok.append("a register with NO kit yet raises instead of quietly returning a plain page — "
                  "the silent fallback would ship exactly the colourway-only deck this ends")

    for line in ok:
        print("  ok   " + line)
    for line in bad:
        print("  FAIL " + line)
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    from _console import safe_stdio
    safe_stdio()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sample", metavar="OUT.pptx")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.list:
        import presets
        for r in registers():
            print("  {:16s} {}".format(r, str(presets.PRESETS[r].get("surface"))[:88]))
        missing = [r for r in sorted(presets.PRESETS) if r not in GROUNDS]
        print("\n  {} of {} registers have a surface kit; still prose-only: {}".format(
            len(GROUNDS), len(presets.PRESETS), ", ".join(missing)))
        return 0
    if a.sample:
        print("wrote", sample(a.sample))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
