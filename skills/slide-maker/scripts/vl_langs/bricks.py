"""bricks — the Toy bricks language (积木): its ground painter, its card and its seven pages.

Glossy toy building bricks seen front-on in 2.5D — a lighter top face with round studs, a darker side for depth — on a
studded baseplate (pale grey, or deep blue). The cover is a build going up beside the title (its last brick still
hovering, about to click in); the section number sits on one big brick; the picture is a printed tile with bricks
locked over its corner; each point is a brick of its own (a course of bricks across a wide page, a staggered stack on a
tall one); the quote is printed on a smooth flat tile with a brick carrying its opening mark; the key figure stands on
a short tower of bricks (a pedestal, not a chart: it is the same three bricks whatever the number); the last page is
the cover's build finished. Every page PLANS its words first (vl_native2.flow / stack: measured, never under a floor),
builds its bricks round them, then sets them. It writes no word of its own."""
from __future__ import annotations

import hashlib
import math
import tempfile
from pathlib import Path

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "bricks"
_LAYERED = "toy bricks sit on, beside and over each other and over the baseplate: layered by design"

# the brick's geometry, in units of its stud pitch p: the 2.5D depth (the top face rises DY and runs DX to the right),
# the front face of one standard brick, the studs (diameter, height) and how flat their round tops read from the front
DX, DY = 0.34, 0.40
BRICK_H = 1.20
STUD_D, STUD_H, STUD_FLAT = 0.60, 0.20, 0.42


# ─────────────────────────────────────────── colour ───────────────────────────────────────────
def _mix(a, b, t):
    a, b = na._rgb3(a), na._rgb3(b)
    return "{:02X}{:02X}{:02X}".format(*(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)))


def _ink_on(k, fill):
    """The words' colour on a brick of `fill`: the brick inks' light or dark one, whichever reads better — and it must
    read (4.5:1), or the palette is wrong and the page says so instead of setting grey on red."""
    lt, dkc = k.P["brick_light_ink"], k.P["brick_dark_ink"]
    a, b = dk.contrast_ratio(lt, fill), dk.contrast_ratio(dkc, fill)
    c, r = (lt, a) if a >= b else (dkc, b)
    if r < 4.5:
        raise ValueError("bricks: no brick ink reads on #{} ({:.2f}:1) — fix the palette".format(fill, r))
    return c


_CYCLE = ("brick_red", "brick_blue", "brick_yellow", "brick_green")


def _colour(k, i):
    return k.P[_CYCLE[i % len(_CYCLE)]]


def _num_colour(k, num):
    """The section brick's colour, from the caller's number: 1 red, 2 blue, 3 yellow, 4 green, then round again — so
    the sections of one deck come in order, each its own colour. A number with no digits takes a colour by its text."""
    digits = "".join(ch for ch in (num or "") if ch.isdigit())
    if digits:
        return _colour(k, (int(digits[-6:]) - 1) % len(_CYCLE))
    h = hashlib.sha1((num or "").encode("utf-8")).digest()[0]
    return _colour(k, h)


# ─────────────────────────────────────────── the baseplate ───────────────────────────────────────────
def _redmean(a, b):
    a, b = na._rgb3(a), na._rgb3(b)
    rm = (a[0] + b[0]) / 2.0
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return math.sqrt((2 + rm / 256.0) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256.0) * db * db)


def _near(base, toward, d=18.0):
    """The colour furthest from `base` toward `toward` that stays within redmean `d` of it: the lint reads a
    background picture as one colour only while 95% of its pixels sit within 20 of their median — a stud pattern
    drawn in these stays the ground's colour to every check, and still reads as a baseplate."""
    best = na.hexstr(base)
    for i in range(1, 201):
        c = _mix(base, toward, i / 200.0)
        if _redmean(c, base) > d:
            break
        best = c
    return best


def _plate(k, slide):
    """Every page: the baseplate — a grid of studs standing out of the ground, each a round top a shade lighter than
    the plate with a shade below it, so faint the words read on it as on the plain ground. One cached picture as the
    slide's background, never hundreds of shapes."""
    from PIL import Image, ImageDraw
    W, H, s, o = ctx(k)
    g = 0.30 * s
    base = k.P["ground"]
    hi, lo = _near(base, "FFFFFF"), _near(base, "000000")
    dpi = min(150.0, math.sqrt(4.0e6 / (W * H)))
    sig = repr((na.hexstr(base), hi, lo, round(W, 3), round(H, 3), round(g, 4), round(dpi, 2), 3))
    path = Path(tempfile.gettempdir()) / "slide-maker-native-art" / "bricks_plate_{}.png".format(
        hashlib.sha1(sig.encode("utf-8")).hexdigest()[:16])
    if not na._cached_ok(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        ss = 3                                         # drawn large and scaled down: smooth round studs
        px = dpi * ss
        im = Image.new("RGB", (max(1, int(W * px)), max(1, int(H * px))), na._rgb3(base))
        dr = ImageDraw.Draw(im)
        nx, ny = max(1, int(W / g)), max(1, int(H / g))
        ox, oy = (W - nx * g) / 2.0, (H - ny * g) / 2.0
        r = 0.27 * g

        def disc(cx, cy, rr, c):
            dr.ellipse([(cx - rr) * px, (cy - rr) * px, (cx + rr) * px, (cy + rr) * px], fill=na._rgb3(c))
        for i in range(nx):
            for j in range(ny):
                cx, cy = ox + (i + 0.5) * g, oy + (j + 0.5) * g
                disc(cx + 0.045 * g, cy + 0.06 * g, r, lo)
                disc(cx, cy, r, hi)
        im = im.resize((max(1, int(W * dpi)), max(1, int(H * dpi))), Image.LANCZOS)
        na._atomic_save(im, path, optimize=True)
    _part, rid = slide.part.get_or_add_image_part(str(path))
    na._bg(slide, '<a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{}"/><a:srcRect/><a:stretch><a:fillRect/>'
                  '</a:stretch></a:blipFill>'.format(rid))


vn.GROUNDS[NAME] = _plate


# ─────────────────────────────────────────── a brick ───────────────────────────────────────────
def _decl(sh, reason):
    if sh is not None:
        dk.decorative(sh, reason)
        dk.overlap_intent(sh, _LAYERED)
    return sh


def _ellipse(cx, cy, rx, ry, n=28, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-9 else 1))]


def _top(p, studs=True):
    """How far a brick's top face and studs rise above its front face, for stud pitch p."""
    return DY * p + (STUD_H * p if studs else 0.0)


def _brick(k, slide, x, y, w, h, color, *, p, studs=True, n=None, shadow=True, gloss=True,
           reason="a toy brick; the words printed on it carry the meaning"):
    """One brick: its front face at (x, y, w, h), the top face rising DY*p behind it and running DX*p right, the side
    face down its right, `n` studs on top (w / p of them by default) and a glossy rim along the front's top edge. The
    silhouette carries the side's colour and the brick's shadow, the faces are laid over it."""
    W, H, s, o = ctx(k)
    dx, dy = DX * p, DY * p
    top_c, side_c = _mix(color, "FFFFFF", 0.26), _mix(color, "000000", 0.30)
    sil = na.poly(slide, [(x, y + h), (x, y), (x + dx, y - dy), (x + w + dx, y - dy), (x + w + dx, y + h - dy),
                          (x + w, y + h)], fill=side_c)
    _decl(sil, reason)
    if sil is not None and shadow:
        na.soft_shadow(sil, blur=0.10 * s, dist=0.05 * s, alpha=0.26, color=k.P["shadow"], direction=60.0)
    _decl(na.poly(slide, [(x, y), (x + w, y), (x + w + dx, y - dy), (x + dx, y - dy)], fill=top_c),
          "the brick's top face; the brick is the picture, nothing to read in it")
    _decl(na.poly(slide, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill=color), reason)
    if gloss:
        g = min(0.07 * p, 0.05 * h)
        _decl(na.poly(slide, [(x + 0.10 * p, y + 0.06 * p), (x + w - 0.10 * p, y + 0.06 * p),
                              (x + w - 0.10 * p, y + 0.06 * p + g), (x + 0.10 * p, y + 0.06 * p + g)],
                      fill="FFFFFF", alpha=0.30),
              "light catching the brick's glossy rim; texture, nothing to read")
    if studs:
        _studs(k, slide, x, y, w, color, p=p, n=n)
    return (x, y, w, h)


def _studs(k, slide, x, y, w, color, *, p, n=None):
    """The studs along a brick's top face: each a short cylinder (its side in the brick's colour) under a round top
    seen from the front, with a speck of light on it."""
    n = n or max(1, int(round(w / p)))
    q = w / n
    dx, dy = DX * p, DY * p
    rx = STUD_D * min(q, p) / 2.0
    ry = rx * STUD_FLAT
    sh = STUD_H * p
    sides, tops, shines = [], [], []
    for i in range(n):
        cx, cy = x + (i + 0.5) * q + dx / 2.0, y - dy / 2.0
        sides.append([(cx - rx, cy - sh)] + _ellipse(cx, cy, rx, ry, 14, 0.0, math.pi)[::-1] + [(cx + rx, cy - sh)])
        tops.append(_ellipse(cx, cy - sh, rx, ry, 28))
        shines.append(_ellipse(cx - 0.38 * rx, cy - sh - 0.15 * ry, 0.30 * rx, 0.34 * ry, 14))
    _decl(na.multipoly(slide, sides, _mix(color, "000000", 0.12)), "the studs on the brick's top; nothing to read")
    _decl(na.multipoly(slide, tops, _mix(color, "FFFFFF", 0.36)), "the round tops of the brick's studs; nothing to read")
    _decl(na.multipoly(slide, shines, "FFFFFF", alpha=0.55), "light on the studs' glossy tops; nothing to read")


def _tile(k, slide, x, y, w, h, color, *, p, reason):
    """A smooth flat tile: a brick with no studs and a thinner top (a tile is the piece with nothing on top)."""
    return _brick(k, slide, x, y, w, h, color, p=p, studs=False, gloss=True, reason=reason)


def _hover_shadow(k, slide, x, y, w, p):
    """The soft shadow a hovering brick drops on the brick under it: an oval on that brick's top face."""
    sh = na.poly(slide, _ellipse(x + w / 2.0 + DX * p / 2.0, y - DY * p / 2.0, w * 0.46, DY * p * 0.42, 36),
                 fill=k.P["shadow"], alpha=0.14)
    _decl(sh, "the shadow the hovering brick casts on the build; nothing to read")


# ─────────────────────────────────────────── a build ───────────────────────────────────────────
# a small build, in studs: (row from the bottom, first stud, studs wide, colour) — a staggered ziggurat eight studs
# wide, four bricks high. The cover shows it going up (its last brick hovering); the closing shows it finished.
BUILD = ((0, 0, 4, "brick_blue"), (0, 4, 4, "brick_red"),
         (1, 1, 4, "brick_yellow"), (1, 5, 2, "brick_green"),
         (2, 2, 4, "brick_neutral"),
         (3, 3, 2, "brick_red"))
BUILD_W, BUILD_ROWS = 8, 4
HOVER = 0.70          # how far the last brick hovers on the cover, in brick heights


PLATE_H = 0.40        # a plate's front, in stud pitches: a third of a brick


def _build_size(p, done):
    """(width, height) of the build at stud pitch p: the bricks, the side face, the top face and studs; the hover on
    the cover, the plate it stands on (a stud wider each side) once it is finished."""
    if done:
        return (BUILD_W + 2 + DX) * p, (BUILD_ROWS * BRICK_H + PLATE_H) * p + _top(p)
    return (BUILD_W + DX) * p, (BUILD_ROWS * BRICK_H + HOVER * BRICK_H) * p + _top(p)


def _build(k, slide, box, *, done, align="c", valign="b", p_max=None):
    """The build fitted into `box` (x, y, w, h): its stud pitch as large as the box allows (up to p_max), set at the
    box's foot (valign 'b') or middle ('m'), centred across it ('c') or at its left ('l'). Returns its rect."""
    W, H, s, o = ctx(k)
    bx, by, bw, bh = box
    w1, h1 = _build_size(1.0, done)
    p = min(bw / w1, bh / h1, p_max or 0.62 * s)
    if p < 0.14 * s:
        raise vl.VLTextOverflow("bricks: the build needs {:.2f}in x {:.2f}in, the page leaves {:.2f}in x {:.2f}in".format(
            w1 * 0.14 * s, h1 * 0.14 * s, bw, bh))
    w, h = w1 * p, h1 * p
    x0 = bx + ((bw - w) / 2.0 if align == "c" else 0.0)
    y0 = by + (bh - h if valign == "b" else (bh - h) / 2.0)
    floor = y0 + h                     # the foot of the bottom row's front face
    bhp = BRICK_H * p
    last = len(BUILD) - 1
    if done:                           # finished: the build stands on a plate, its studs showing either side
        _brick(k, slide, x0, floor - PLATE_H * p, (BUILD_W + 2) * p, PLATE_H * p, k.P["brick_green"], p=p,
               n=BUILD_W + 2, gloss=False,
               reason="the plate the finished build stands on: the deck's picture of a finished build, nothing to read")
    sx = x0 + (p if done else 0.0)
    floor -= PLATE_H * p if done else 0.0
    for i, (row, st, n, ck) in enumerate(BUILD):
        x = sx + st * p
        y = floor - (row + 1) * bhp
        if i == last and not done:
            _hover_shadow(k, slide, x, y + bhp, n * p, p)
            y -= HOVER * bhp
        _brick(k, slide, x, y, n * p, bhp, k.P[ck], p=p, n=n,
               reason="a brick of the build: the deck's picture of putting pieces together, nothing to read")
    return (x0, y0, w, h)


# ─────────────────────────────────────────── text on a brick ───────────────────────────────────────────
def _m(k):
    W, H, s, o = ctx(k)
    return 0.55 * s


def _foot(rects, default):
    return max((v[1] + v[3] for v in rects.values()), default=default)


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=3)
def _bk_cover(k, slide, f, image):
    """The title block, and beside it (under it on a portrait or square page) a build going up — its last brick still
    hovering over the others, about to click in."""
    W, H, s, o = ctx(k)
    m = _m(k)
    heads = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.16 * s), (_v2.fields(f, ("title",)), 0.24 * s),
             (_v2.fields(f, ("subtitle",)), 0.0)]
    start = None if alt() < 2 else {"title": 32 * s}
    if o == "land":
        cw = (0.54, 0.60, 0.64)[alt()] * W
        r, ds = _v2.stack(k, slide, "cover", m + 0.1 * s, cw, m, H - m, heads, anchor="middle", start=start)
        ax = m + 0.1 * s + cw + 0.5 * s
        art = (ax, m + 0.3 * s, W - m - ax, H - 2 * m - 0.5 * s)
        _build(k, slide, art, done=False, valign="m")
    else:
        # the words, then the build under them, centred down the page as one group
        gap = 0.70 * s

        def words(y0):
            return _v2.stack(k, slide, "cover", m + 0.1 * s, W - 2 * m - 0.2 * s, y0,
                             y0 + (0.58, 0.64, 0.70)[alt()] * H - m, heads, anchor="top", start=start)
        r, ds = words(m)
        foot = _foot(r, m)
        w1, h1 = _build_size(1.0, False)
        p = min((W - 2 * m) / w1, (H - m - foot - gap) / h1, 0.70 * s)
        if p < 0.14 * s:
            raise vl.VLTextOverflow("bricks.cover(): the words leave the build {:.2f}in".format(H - m - foot - gap))
        dy = max(0.0, (H - m - foot - gap - h1 * p) / 2.0)
        if dy > 0.02 * s:
            r, ds = words(m + dy)
            foot = _foot(r, m + dy)
        _build(k, slide, (m, foot + gap, W - 2 * m, h1 * p + 0.01 * s), done=False, valign="b", p_max=p)
    _run_all(ds)
    return r


def _number_brick(k, slide, page, box, num, colour, *, start=None, studs=4):
    """PLAN the number on one big brick, centred in `box`: the brick cut to the number (never narrower than it is
    tall), `studs` studs on top. Returns (rects, draw, brick_rect); draw() draws the brick, then the number."""
    W, H, s, o = ctx(k)
    x, y, w, h = box
    ink = _ink_on(k, colour)
    padx, pady = 0.40 * s, 0.22 * s
    room = (x + padx, y + pady, w - 2 * padx, h - 2 * pady)
    kw = {"anchor": "middle", "align": "c", "ink": ink, "accent": ink, "mute": ink}
    nr, nd = _v2.flow(k, slide, page, room, [("number", num)], **dict(kw, **({"start": start} if start else {})))
    size = getattr(nd, "sizes", {}).get("number", vl.TYPE[NAME]["number"][0] * s)
    iw = _v2.ink_w(k, "number", num, size)
    nx, ny, nw, nh = nr["number"]
    tw = min(room[2], iw / vl.HEADROOM + 0.12 * s)
    bw = min(w, max(tw + 2 * padx, (nh + 2 * pady) * 1.05))
    bh_ = min(h, nh + 2 * pady)
    p = bw / studs
    bx, by = x + (w - bw - DX * p) / 2.0, ny + nh / 2.0 - bh_ / 2.0
    nr, nd = _v2.flow(k, slide, page, (bx + (bw - tw) / 2.0, by + pady, tw, bh_ - 2 * pady), [("number", num)],
                      **dict(kw, start={"number": size}))

    def draw():
        _brick(k, slide, bx, by, bw, bh_, colour, p=p, n=studs,
               reason="the big brick the section's number is printed on; the number carries the meaning")
        nd()
    return nr, draw, (bx, by, bw, bh_), p


@register(NAME, "section", alts=2)
def _bk_section(k, slide, f, image):
    """One big brick carrying the section number (its colour from the number: 1 red, 2 blue, 3 yellow, 4 green); the
    kicker and title beside it (under it on a portrait or square page, the brick and the words centred down the
    page together)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    colour = _num_colour(k, num)
    heads = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.15 * s), (_v2.fields(f, ("title",)), 0.0)]

    def plan(dy):
        r, ds = {}, []
        if o == "land":
            bw_ = (0.36 if alt() == 0 else 0.30) * W
            box = (m + 0.2 * s, 0.20 * H, bw_, 0.62 * H)
            col = (box[0] + box[2] + 0.7 * s, 0.14 * H, W - m - box[0] - box[2] - 0.7 * s, 0.72 * H)
        else:
            box = (0.14 * W, m + 0.5 * s + dy, 0.72 * W, (0.34 if alt() == 0 else 0.26) * H)
            col = (m + 0.1 * s, box[1] + box[3] + 0.4 * s, W - 2 * m - 0.2 * s, H - m - box[1] - box[3] - 0.4 * s)
        head = box[1]
        if num:
            nr, nd, brick, p = _number_brick(k, slide, "section", box, num, colour, start={"number": 150 * s})
            r.update(nr)
            ds.append(nd)
            head = brick[1] - _top(p)
            if o != "land":             # the words start under the brick as it was cut, not under its box
                top = brick[1] + brick[3] + 0.55 * s
                col = (col[0], top, col[2], H - m - top)
        else:                           # no number, no brick: the words alone, centred on the page
            col = (m + 0.2 * s, m, W - 2 * m - 0.4 * s, H - 2 * m)
        tr, tds = _v2.stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3], heads,
                            anchor="middle" if o == "land" or not num else "top",
                            align="l" if o == "land" and num else "c")
        r.update(tr)
        return r, ds + tds, head
    r, ds, head = plan(0.0)
    if o != "land" and num:
        dy = ((H - m) - _foot(r, head) - (head - m)) / 2.0
        if dy > 0.02 * s:
            r, ds, head = plan(dy)
    _run_all(ds)
    return r


@register(NAME, "image_text", alts=3)
def _bk_image_text(k, slide, f, image):
    """The caller's picture printed on a flat tile, two bricks locked over its top-left corner (one across the tile's
    top, one down its side); the caption under it, the kicker, title and body beside it (under it on a portrait or
    square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    cap = text_of(f, "caption")
    p = 0.40 * s
    bhp = BRICK_H * p
    b = 0.10 * s                                   # the tile's printed border round the picture
    tp = 0.30 * s                                  # the tile's own (thinner) depth
    lift = bhp + _top(p) + b                       # the corner brick on the tile's top
    left = p + b                                   # the bricks down the tile's left side
    if o == "land":
        ix = m + left + 0.1 * s
        iw = (0.44, 0.38, 0.32)[alt()] * W
        ih = (H - 2 * m - lift - b - (0.95 * s if cap else 0.0)) * (0.96, 0.88, 0.80)[alt()]
    else:
        ix = m + left + 0.1 * s
        iw = W - ix - m - b - DX * tp
        ih = (0.32, 0.26, 0.20)[alt()] * H

    def caption(iy):
        if not cap:
            return {}, None, iy + ih + b
        cr, cd = _v2.flow(k, slide, "image_text", (ix - b, iy + ih + b + 0.20 * s, iw + 2 * b, 0.9 * s),
                          [("caption", cap)])
        return cr, cd, _foot(cr, iy + ih + b)
    heads = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
             (_v2.fields(f, ("body",)), 0.0)]

    def words(foot):
        if o == "land":
            cx0 = ix + iw + b + DX * tp + 0.7 * s
            return _v2.stack(k, slide, "image_text", cx0, W - m - cx0, 0.14 * H, 0.86 * H, heads, anchor="middle")
        return _v2.stack(k, slide, "image_text", m + 0.1 * s, W - 2 * m - 0.2 * s, foot + 0.40 * s, H - m, heads,
                         anchor="top")
    # the corner brick, the tile, its caption (and on a portrait or square page the words under them) centred down
    # the page as one group
    iy = m + lift
    _cr, _cd, foot = caption(iy)
    end = foot if o == "land" else _foot(words(foot)[0], foot)
    if H - m - end > 0.02 * s:
        iy += (H - m - end) * 0.5
    cr, cd, foot = caption(iy)
    r, ds = dict(cr), [cd] if cd else []
    img = (ix, iy, iw, ih)
    tile = (ix - b, iy - b, iw + 2 * b, ih + 2 * b)
    tr, tds = words(foot)
    r.update(tr)
    tx, ty, tw, th = tile
    # the corner: two bricks down the tile's left side, locked under a 1x4 brick lying across the tile's top-left
    # corner — the picture held into the build
    for j, ck in ((1, "brick_blue"), (0, "brick_yellow")):
        _brick(k, slide, tx - p, ty + j * bhp, p, bhp, k.P[ck], p=p, n=1, studs=False,
               reason="a brick locked under the corner brick, framing the picture's corner; nothing to read")
    _tile(k, slide, tx, ty, tw, th, k.P["print"], p=tp,
          reason="the flat tile the picture is printed on; the picture carries the meaning")
    _brick(k, slide, tx - p, ty - bhp, 4 * p, bhp, k.P["brick_red"], p=p, n=4,
           reason="a brick locked over the picture's corner, holding the tile to the build; nothing to read")
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(tds + ds)
    return r


def _balance(k, field, text, size, w):
    """Words whose last line would hold one word, one or two CJK characters, or a short scrap, set in balanced lines
    instead — the narrowest measure that keeps the same number of lines, its lines given as the words' own line
    breaks ("Two in five trees on the main / road" reads "Two in five trees / on the main road"; "主干道上五棵里有两 /
    棵" reads "主干道上五 / 棵里有两棵"). Copy the kit already breaks at its clause marks, and anything whose words the
    lines would not tile, is left as it was."""
    if not text or "\n" in text:
        return text
    cjk = dk._has_cjk(text)
    if cjk and any(ch in "，。、；：！？" for ch in text):
        return text
    wm = w * vl.HEADROOM
    lines = vl._break_lines(k, field, text, size, wm)
    if len(lines) < 2:
        return text
    last = lines[-1].strip()
    longest = max(len(ln.strip()) for ln in lines)
    if cjk:
        if len(last) > 2 and len(last) >= 0.45 * longest:
            return text
    elif len(last.split()) > 1 and len(last) >= 0.45 * longest:
        return text
    lo, hi = 0.40 * wm, wm
    for _i in range(16):
        mid = (lo + hi) / 2.0
        if len(vl._break_lines(k, field, text, size, mid)) <= len(lines):
            hi = mid
        else:
            lo = mid
    best = [ln.strip() for ln in vl._break_lines(k, field, text, size, hi)]
    same = ("".join(best) == "".join(text.split())) if cjk else (" ".join(best).split() == text.split())
    lone = min(len(b) for b in best) <= 2 if cjk else min(len(b.split()) for b in best) < 2
    if len(best) != len(lines) or not same or lone:      # "Plane / trees lead" is no better than "Plane trees / lead"
        return text
    return "\n".join(best)


def _head_on_one_line(k, heads, size, w):
    """The size every point's head is set at so that each stands on ONE line of its brick, when that takes no more
    than 15% off (and keeps the floor): "Plane trees lead" a little smaller on one line beats "Plane trees / lead".
    None when every head already fits, or one would need more."""
    if not heads:
        return None
    _b, role, bold, *_r = vl.TYPE[NAME]["item_head"]
    floor = vl.TYPE[NAME]["item_head"][5] * ctx(k)[2]
    room = w * vl.HEADROOM - dk.TEXT_INSET_LR
    need = max(_v2.ink_w(k, "item_head", h, size) for h in heads)
    if need <= room:
        return None
    z = size * room / need * 0.98
    return z if z >= max(0.85 * size, floor) else None


@register(NAME, "points", alts=5)
def _bk_points(k, slide, f, image):
    """Each point on a brick of its own — its head and its line printed on the brick's face, the bricks in four
    colours. A course of bricks side by side across a landscape page; a staggered stack on a portrait or square page
    (point 1 on top). When a course would set the words small (four points on a 4:3 page) or long copy needs the
    room, the bricks go two to a course, the next course staggered on the first (three points: a pyramid, point 1 on
    top); the title starts smaller in the roomier layouts."""
    W, H, s, o = ctx(k)
    m = _m(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    a = alt()
    land = o == "land"
    title_start = (None, 36, 36, 28, 26)[a] if land else (None, 36, 34, 28, 26)[a]
    # the title's room: up to 0.30 of the page (the roomier layouts start it smaller, so it takes less of that room;
    # a room cut smaller would only shrink a long title to its floor and refuse the page)
    def heads_at(y):
        return _v2.stack(k, slide, "points", m + 0.1 * s, W - 2 * m - 0.2 * s, y, y + (0.30, 0.30, 0.30, 0.30, 0.34)[a] * H,
                         [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)],
                         anchor="top", start={"title": title_start * s} if title_start else None)
    r, ds = heads_at(m)
    pt = (0.62, 0.62, 0.62, 0.50, 0.42)[a] * s           # the stud pitch aimed at
    dx = DX * pt
    top = _foot(r, m) + 0.36 * s + _top(pt)
    bottom = H - m
    x0, w0 = m + 0.1 * s, W - 2 * m - 0.2 * s - dx
    if land:
        cols = n if a == 0 or n < 3 else 2
    else:
        cols = 2 if a >= 2 and n >= 3 else 1
    compact = a >= 3
    rows = -(-n // cols)
    # a course set one stud along from the one under it (the last layout gives that stud to the words)
    stagger = 0.0 if rows == 1 or a == 4 else pt
    gap = 0.18 * s if cols > 1 else 0.0
    bw = (w0 - stagger - (cols - 1) * gap) / cols
    if rows == 1 and bw > 4.6 * s:                       # two points across a wide page: bricks, not slabs — the
        bw = 4.6 * s                                      # course centred
        x0 += (w0 - (cols * bw + (cols - 1) * gap)) / 2.0
    studs = max(2, int(round(bw / pt)))
    p = bw / studs
    padx, pady = max(0.26 * s, 0.30 * p), (0.24 if cols > 1 or rows == 1 else 0.18) * s
    if compact:
        padx, pady = padx * (0.75 if a == 3 else 0.62), pady * (0.75 if a == 3 else 0.55)
    inner = bw - 2 * padx
    if inner < (2.0 if land and cols == n and n >= 3 and a == 0 else 1.2) * s:
        # a course of bricks too narrow to hold a head on a line or two (four points across a 4:3 page): the next
        # layout stacks two courses
        raise vl.VLTextOverflow("bricks.points(): {} bricks to a course leave {:.2f}in for the words".format(cols, inner))
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    inks = [_ink_on(k, _colour(k, i)) for i in range(n)]
    # the words are planned at their own sizes while a roomier layout is left to try (a smaller title, two courses);
    # the compact layouts plan them in the room one brick gets, shrinking toward their floors before refusing
    room = max(0.3 * s, (bottom - top) / rows - 2 * pady) if compact else bottom - top
    z1 = _head_on_one_line(k, [hd for hd, _ln in pts if not dk._has_cjk(hd)], vl.TYPE[NAME]["item_head"][0] * s, inner)
    first = {"anchor": "top", "start": {"item_head": z1}} if z1 else {"anchor": "top"}
    probe = _v2.plan_together(k, slide, "points", [((0, 0, inner, room), it, first) for it in items])
    sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
    if land and cols == n and n >= 3 and a == 0:
        # a course of narrow bricks may set the words well under their size: the next layout stacks two courses
        small = sorted(f_ for f_, z in sizes.items() if z < 0.84 * vl.TYPE[NAME][f_][0] * s)
        if small:
            raise vl.VLTextOverflow("bricks.points(): a course of {} bricks sets {} under 85% of its size".format(
                n, " and ".join(small)))
    items = [[(f_, _balance(k, f_, t, sizes.get(f_, vl.TYPE[NAME][f_][0] * s), inner)) for f_, t in it] for it in items]
    probe = _v2.plan_together(k, slide, "points", [((0, 0, inner, room), it, {"anchor": "top", "start": sizes})
                                                    for it in items])
    sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
    need = max(_foot(pr, 0.0) for pr, _d in probe)
    avail = bottom - top
    least = max(need + 2 * pady, BRICK_H * p)
    if rows * least > avail + 1e-6:
        raise vl.VLTextOverflow("bricks.points(): the bricks need {:.2f}in, the page has {:.2f}in".format(
            rows * least, avail))
    # a brick's proportions: as tall as its words need and no squatter than a toy brick — a course across a wide page
    # about 0.58 of its width tall, two courses 0.40, a staggered stack's bricks about 1.5 standard bricks
    want = min(0.58 * bw, 2.4 * s) if rows == 1 else (min(0.40 * bw, 2.0 * s) if cols > 1 else 1.5 * BRICK_H * p)
    bh_ = max(least, min(want, avail / rows))
    lift_ = (bh_ - least) / 2.0                           # the tallest point's words centred on its brick, every
    block = rows * bh_                                    # head on one line across the course
    if land:
        y0 = top + (bottom - top - block) * 0.42
    else:                                                 # a tall page: the title and its bricks centred as a group
        dy = (bottom - top - block) / 2.0
        y0 = top + dy
        if dy > 0.02 * s and r:
            r, ds = heads_at(m + dy)
    # course 0 is the TOP course, drawn last so it sits on the courses under it; a short course (three points two to a
    # course) is the top one, centred over the joint of the two under it — a pyramid, never an overhang
    per = [n - cols * (rows - 1)] + [cols] * (rows - 1)
    rects = []
    for row, cnt in enumerate(per):
        off = stagger if (rows - 1 - row) % 2 == 1 else 0.0
        if cnt < cols:
            off = (w0 - (cnt * bw + (cnt - 1) * gap)) / 2.0
        for c in range(cnt):
            rects.append((x0 + off + c * (bw + gap), y0 + row * bh_, bw, bh_))
    planned = _v2.plan_together(k, slide, "points", [
        ((bx + padx, by + pady + lift_, inner, bh_ - 2 * pady - lift_), it,
         {"anchor": "top", "start": sizes, "ink": inks[i], "mute": inks[i], "accent": inks[i]})
        for i, ((bx, by, _w, _h), it) in enumerate(zip(rects, items))])
    for i in sorted(range(n), key=lambda i: (-rects[i][1], rects[i][0])):     # bottom course first, left to right
        bx, by, bw_i, bh_i = rects[i]
        _brick(k, slide, bx, by, bw_i, bh_i, _colour(k, i), p=p, n=studs,
               reason="the brick this point is printed on; the point's words carry the meaning")
    for pr, pd in planned:
        r.update(pr)
        ds.append(pd)
    _run_all(ds)
    return r


# the opening quote mark printed on the quote's brick, drawn from Arial Black's own outline (its quoteleft, in font
# units, y up; TrueType quadratic curves with their implied on-curve points) — a drawn mark sits centred on the brick's
# face at any scale, where a text glyph rides high in its line box and its box runs past the brick
_QUOTELEFT = ((505, 675), (70, 675), (70, 1010), ("q", (70, 1195), (147, 1302)), ("q", (224, 1409), (411, 1491)),
              (505, 1313), ("q", (390, 1259), (346, 1205.5)), ("q", (302, 1152), (297, 1079)), (505, 1079))
_QUOTE_OFFSETS = (-15, 492)                       # the two quotelefts of U+201C, as the font composes them
_QUOTE_BOX = (55.0, 675.0, 997.0, 1491.0)         # their ink box


def _quote_mark(k, slide, cx, cy, hgt, color):
    """The opening quote mark, its ink `hgt` tall, centred on (cx, cy)."""
    x0, y0, x1, y1 = _QUOTE_BOX
    sc = hgt / (y1 - y0)
    polys = []
    for off in _QUOTE_OFFSETS:
        pts, cur = [], None
        for seg in _QUOTELEFT:
            if seg[0] == "q":
                (qx, qy), (ex, ey) = seg[1], seg[2]
                for i in range(1, 9):
                    t = i / 8.0
                    pts.append(((1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * qx + t * t * ex,
                                (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * qy + t * t * ey))
                cur = (ex, ey)
            else:
                pts.append(seg)
                cur = seg
        polys.append([(cx + (px + off - (x0 + x1) / 2.0) * sc, cy - (py - (y0 + y1) / 2.0) * sc) for px, py in pts])
    sh = na.multipoly(slide, polys, color)
    if sh is not None:
        dk.decorative(sh, "the opening quote mark printed on the brick: it marks the words on the tile as a quote")
        dk.overlap_intent(sh, "the quote mark is printed on the brick it sits on: layered by design")


@register(NAME, "quote", alts=3)
def _bk_quote(k, slide, f, image):
    """The quote printed on a wide, smooth flat tile; a brick sits on the tile's top-left carrying the opening quote
    mark; the attribution under the quote, on the tile."""
    W, H, s, o = ctx(k)
    m = _m(k)
    q = text_of(f, "quote") or ""
    tp = 0.36 * s                                 # the tile's depth
    tile_c = k.P["brick_yellow"]
    ink = _ink_on(k, tile_c)
    mark_c = k.P["brick_red"]
    mark_ink = _ink_on(k, mark_c)
    padx, pady = (0.55 if alt() < 2 else 0.40) * s, (0.45 if alt() < 2 else 0.32) * s
    # the tile as wide as the quote asks: a short line on a long yellow slab is mostly slab
    units = sum(2 if dk._has_cjk(ch) else 1 for ch in q)
    frac = 0.62 if units <= 50 else 0.76 if units <= 110 else 0.90
    if dk._has_cjk(q):                            # CJK display type runs wide at a quote's size: a roomier tile
        frac = max(frac, 0.76)
    if W < 1.6 * H:                               # a 4:3 page is narrower for the same quote
        frac = min(1.0, frac + 0.12)
    if o != "land":
        frac = 1.0
    frac = (frac, max(frac, 0.90), 1.0)[alt()]
    full = W - 2 * m - 0.2 * s - DX * tp
    tw = full * frac
    tx = (W - tw - DX * tp) / 2.0
    p = 0.55 * s                                  # the mark's brick: two studs wide
    ab, ah = 2 * p, BRICK_H * p * 1.35
    lift = ah + _top(p)
    kw = {"ink": ink, "mute": ink, "accent": ink}
    groups = [(_v2.fields(f, ("quote",)), 0.26 * s), (_v2.fields(f, ("attribution",)), 0.0)]

    def plan(ty, x, iw):
        return _v2.stack(k, slide, "quote", x + padx, iw, ty + pady, H - m - pady, groups, anchor="top", **kw)

    def sizes_of(ds_):
        return {f_: round(z, 2) for d in ds_ for f_, z in getattr(d, "sizes", {}).items()}
    iw = tw - 2 * padx
    r, ds = plan(m + lift, tx, iw)
    foot0, z0 = _foot(r, m + lift), sizes_of(ds)
    if o == "land":
        # the tile cut in to the words: the narrowest measure that sets them at the same sizes in the same height —
        # with a little slack, so no line is set to the hair (a CJK line's hung 。 read as one more line by the lint)
        for cut in (0.70, 0.80, 0.90):
            iw2 = min(iw, iw * cut + 0.35 * s)
            if iw2 + 2 * padx < max(0.36 * W, ab + 1.2 * s) or iw2 >= iw:
                continue
            try:
                r1, d1 = plan(m + lift, tx, iw2)
            except vl.VLTextOverflow:
                continue
            if _foot(r1, m + lift) <= foot0 + 1e-3 and sizes_of(d1) == z0:
                iw = iw2
                break
        tw = iw + 2 * padx
        tx = (W - tw - DX * tp) / 2.0
        r, ds = plan(m + lift, tx, iw)
    th = _foot(r, m + lift) - (m + lift) + pady
    ty = m + lift + max(0.0, (H - m - (m + lift) - th) * 0.45)
    r, ds = plan(ty, tx, iw)
    th = _foot(r, ty) - ty + pady
    _tile(k, slide, tx, ty, tw, th, tile_c, p=tp,
          reason="the smooth flat tile the quote is printed on; the quote carries the meaning")
    mx = tx + 0.45 * s
    _brick(k, slide, mx, ty - ah, ab, ah, mark_c, p=p, n=2,
           reason="the brick on the tile carrying the opening quote mark; ornament")
    _quote_mark(k, slide, mx + ab / 2.0, ty - ah / 2.0, ah * 0.46, mark_ink)
    _run_all(ds)
    return r


@register(NAME, "data", alts=3)
def _bk_data(k, slide, f, image):
    """The number standing on a short tower of three bricks (the same three whatever the number: a pedestal, not a
    bar); the label and the note beside it (under it on a portrait or square page, the whole group centred)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    land = o == "land"
    if land:
        zone = (m + 0.1 * s, m, (0.46, 0.42, 0.38)[alt()] * W, H - 2 * m)
    else:
        zone = (m + 0.1 * s, m, W - 2 * m - 0.2 * s, (0.62, 0.54, 0.46)[alt()] * H - m)
    zx, zy, zw, zh = zone
    if not num:                                    # no figure, nothing to stand on the tower: the words alone
        r, d = _v2.flow(k, slide, "data", (m + 0.2 * s, m, W - 2 * m - 0.4 * s, H - 2 * m),
                        _v2.fields(f, ("label", "note")), anchor="middle", align="c")
        d()
        return r
    per_h = 3 * BRICK_H + DY + STUD_H              # the tower's height for a stud pitch of 1
    hmax = zh * 0.42 / per_h                       # the tower takes at most 42% of the zone's height
    nr, nd = _v2.flow(k, slide, "data", (zx, zy, zw, zh - per_h * min(hmax, 0.40 * s)), [("number", num)],
                      anchor="top", align="c")
    nh = nr["number"][3]
    em = getattr(nd, "sizes", {}).get("number", vl.TYPE[NAME]["number"][0] * s) / 72.0
    iw = _v2.ink_w(k, "number", num, em * 72.0)
    # the tower: three bricks of four studs stacked straight, as wide as the figure standing on it (within reason)
    p = min(max(iw / 4.0 * 0.92, 0.36 * s), 0.70 * s, hmax, (zw - 0.2 * s) / (4 + DX))
    tower_h = per_h * p
    # the figure stands ON the studs: its line box runs 0.22 em under its digits' baseline (measured in Arial Black)
    sink = 0.22 * em - 0.03 * s
    group = nh - sink + tower_h
    words = _v2.fields(f, ("label", "note"))

    def place(gy):
        floor = gy + group
        nr, nd = _v2.flow(k, slide, "data", (zx, gy, zw, nh), [("number", num)], anchor="top", align="c",
                          start={"number": em * 72.0})
        r, ds = dict(nr), [nd]
        if land:
            cx0 = zx + zw + 0.6 * s
            tr, td = _v2.flow(k, slide, "data", (cx0, 0.14 * H, W - m - cx0, 0.72 * H), words, anchor="middle")
        else:
            top = floor + 0.45 * s
            tr, td = _v2.flow(k, slide, "data", (m + 0.1 * s, top, W - 2 * m - 0.2 * s, H - m - top), words,
                              anchor="top", align="c")
        r.update(tr)
        ds.append(td)
        return r, ds, floor
    if land:
        gy = zy + (zh - group) / 2.0
    else:                                          # the figure, its tower and its words centred down the page
        r0, _d0, floor0 = place(zy)
        gy = zy + max(0.0, ((H - m) - _foot(r0, floor0)) / 2.0)
    r, ds, floor = place(gy)
    tx = zx + (zw - 4 * p) / 2.0
    bhp = BRICK_H * p
    for row, ck in ((0, "brick_blue"), (1, "brick_red"), (2, "brick_yellow")):
        _brick(k, slide, tx, floor - (row + 1) * bhp, 4 * p, bhp, k.P[ck], p=p, n=4,
               reason="a brick of the tower the number stands on; the same three bricks whatever the number")
    _run_all(ds)
    return r


@register(NAME, "closing", alts=3)
def _bk_closing(k, slide, f, image):
    """The cover's build, finished — every brick in place; the title and its line above it."""
    W, H, s, o = ctx(k)
    m = _m(k)
    groups = [(_v2.fields(f, ("title",)), 0.22 * s), (_v2.fields(f, ("line",)), 0.0)]
    start = None if alt() == 0 else {"title": (36 if alt() == 1 else 28) * s}
    x, w = m + 0.2 * s, W - 2 * m - 0.4 * s
    lim = (0.52, 0.58, 0.64)[alt()] * H
    r, ds = _v2.stack(k, slide, "closing", x, w, m, lim, groups, anchor="top", align="c", start=start)
    th = _foot(r, m) - m
    min_b = (1.9 if o == "land" else 1.6) * s
    room = H - 2 * m - th - 0.5 * s
    if room < min_b:
        raise vl.VLTextOverflow("bricks.closing(): the build needs {:.2f}in under the words, the page leaves {:.2f}in"
                                .format(min_b, room))
    w1, h1 = _build_size(1.0, True)
    p = min(room / h1, (0.62 if o == "land" else 0.70) * s, (W - 2 * m) / w1)
    bh_ = h1 * p
    y0 = m + max(0.0, (H - 2 * m - th - 0.5 * s - bh_) * 0.5)
    r, ds = _v2.stack(k, slide, "closing", x, w, y0, y0 + th + 0.05 * s, groups, anchor="top", align="c",
                      start=dict(start or {}, **{f_: z for d in ds for f_, z in getattr(d, "sizes", {}).items()}))
    _build(k, slide, (m, _foot(r, y0) + 0.5 * s, W - 2 * m, bh_ + 0.01 * s), done=True, valign="b", p_max=p)
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_bricks(slide, role, index):
    """An ordinary page (a chart, an agenda) on the baseplate: the plate is the page's ground (new_slide paints it);
    the content rect in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


_card_bricks = vl._card_for(NAME)
