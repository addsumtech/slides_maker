"""periodic — the Periodic table language (元素周期表): its ground painter, its card and its seven pages.

The periodic table of the elements as a design system. Every element is a square TILE: a small number at its top
left, a large central mark, a name line under it, its fill and rule in its FAMILY's colour. The cover is a wall chart —
the whole table in family colours, the title set where a chart sets its own, in the bay above the transition metals;
the closing is the same table as an empty outline with its last element lit. A section or the data page is ONE large
solid tile carrying the caller's number; the points are element tiles, one each; the picture is mounted in a tile; the
quote is the table's legend tile, its “ hung in the slot where a tile carries its number.

A number decides a colour the way the table does: section 2 is lit in the colour of element 2's family (a noble gas),
point 1 in hydrogen's, point 3 in lithium's — and a section's small table lights that element's place. A percentage on
the data page lights that share of the table's tiles. Nothing else is coloured at random.

Never inventing a word: a chemical symbol or an element name is an invented word unless it is the caller's, so the
large mark on a tile is always the caller's own (the number, the point's head) and the only words the language writes
itself are the manifest's derived ones — the point numbers 1 2 3 at the tiles' top left and the opening “ on the legend
tile. Every page PLANS its words first (vl_native2.flow / stack / plan_together: measured, never under a floor), draws
its tiles clear of them, then sets them."""
from __future__ import annotations

import re

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "periodic"


# ─────────────────────────────────────────── colour ───────────────────────────────────────────
def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    """`t` of colour a over colour b (hex), as hex."""
    ra, rb = _rgb(a), _rgb(b)
    return "".join("{:02X}".format(int(round(x * t + y * (1.0 - t)))) for x, y in zip(ra, rb))


def _dark(k):
    return vl._lum(k.P["ink"]) > vl._lum(k.P["ground"])


def _fam(k, i):
    return k.P["fam{}".format(i % 10)]


def _tint(k, i, mosaic=False):
    """A tile's fill in family i: the family colour laid thin over the ground — deeper on the cover's wordless table
    (`mosaic`), paler under words; on the dark ground thin either way, the family colour being the tile's glowing
    rule instead."""
    if _dark(k):
        return _mix(_fam(k, i), k.P["ground"], 0.14 if mosaic else 0.15)
    return _mix(_fam(k, i), k.P["ground"], 0.42 if mosaic else 0.20)


def _shade(k, base, on, need=4.6):
    """`base` moved toward the ground's ink until it reads at `need`:1 on `on` — a family colour that carries words."""
    for i in range(0, 41):
        c = _mix(k.P["ink"], base, i / 40.0)
        if vl._contrast(c, on) >= need:
            return c
    return k.P["ink"]


_CLOSE = "，。、；：！？）」』》】,.;:!?)”’"
_OPEN = "（「『《【(“‘"


def _balanced(k, field, text, size, width):
    """A `text` that wraps to two lines at `size` in `width`, broken where the longer of the two lines is shortest — a
    centred tile head reads "Shade is / very uneven", never "Shade is very / uneven", one word alone under a full line;
    a Chinese quote "螺丝刀握在 / 来访者手里。", never a closing 。 alone on a line of its own (the renderer and the
    lint disagreed where an unbalanced line ended). Latin breaks between words; CJK between characters — never before
    a closing mark, after an opening one or inside a Latin word — and at a clause mark when that is as even. Anything
    else (one line, three) is returned as it is."""
    if not text or "\n" in text:
        return text
    room = width * vl.HEADROOM
    if len(vl._break_lines(k, field, text, size, room)) != 2:
        return text
    if dk._has_cjk(text):
        cuts = []
        for i in range(1, len(text)):
            p, c = text[i - 1], text[i]
            if c in _CLOSE or p in _OPEN or (p.isascii() and p.isalnum() and c.isascii() and c.isalnum()):
                continue
            cuts.append((text[:i].rstrip(), text[i:].lstrip(), p in _CLOSE))
        if any(c_ for _a, _b, c_ in cuts):
            # Chinese with a clause mark inside breaks only at one: when no clause break fits, the text is left to the
            # kit's own clause packing, which sets it smaller rather than break a clause
            cuts = [ct for ct in cuts if ct[2]]
    else:
        words = text.split()
        cuts = [(" ".join(words[:i]), " ".join(words[i:]), words[i - 1][-1] in ",;:.!?") for i in range(1, len(words))]
    best = None
    for a, b, clause in cuts:
        if not a or not b:
            continue
        wa, wb = _v2.ink_w(k, field, a, size), _v2.ink_w(k, field, b, size)
        # a break at a clause mark beats any break inside a clause ("规划街道之前，/ 先数一数…", never "…之前，先 /
        # 数一数…" though that is a character more even); among breaks of one kind, the most even wins
        score = (0 if clause else 1, max(wa, wb))
        if max(wa, wb) <= room * 0.97 and (best is None or score < best[0]):
            best = (score, a + "\n" + b)
    return best[1] if best else text


def _on(k, fill):
    """The ink for words set on a solid `fill`: the ground's ink or its ground colour, whichever reads better."""
    a, b = k.P["ink"], k.P["ground"]
    return a if vl._contrast(a, fill) >= vl._contrast(b, fill) else b


def _solid(k, i, need=4.6):
    """A solid tile's fill in family i: the family colour, eased toward the ground until the ground's ink reads on it
    at `need`:1 (light halogen violet held the kicker at 4.2:1)."""
    base = _fam(k, i)
    for j in range(0, 21):
        c = _mix(k.P["ground"], base, j / 40.0)
        if vl._contrast(_on(k, c), c) >= need:
            return c
    return base


# ─────────────────────────────────────────── the table ───────────────────────────────────────────
ALK, AE, TR, PT, MD, NM, HA, NG, LA, AC = range(10)      # the ten families, in the manifest's fam0 … fam9 order
_P_BLOCK = {1: (MD, NM, NM, NM), 2: (PT, MD, NM, NM), 3: (PT, MD, MD, NM), 4: (PT, PT, MD, MD),
            5: (PT, PT, PT, PT), 6: (PT, PT, PT, PT)}     # groups 13-16 by period: boron … livermorium


def _family(r, c):
    """The family of the element at (period row r, group column c) in the 18-column table; rows 7 and 8 are the
    lanthanides and actinides, set under the table."""
    if r == 7:
        return LA
    if r == 8:
        return AC
    if r == 0:
        return NM if c == 0 else NG
    if c == 0:
        return ALK
    if c == 1:
        return AE
    if c == 17:
        return NG
    if c == 16:
        return HA
    if c == 2 and r in (5, 6):
        return LA if r == 5 else AC
    if c <= 11:
        return TR
    return _P_BLOCK[r][c - 12]


CELLS = ([(0, 0), (0, 17)] + [(r, c) for r in (1, 2) for c in (0, 1, 12, 13, 14, 15, 16, 17)]
         + [(r, c) for r in range(3, 7) for c in range(18)] + [(r, c) for r in (7, 8) for c in range(2, 17)])
# element Z sits at ZCELL[Z - 1]: in order of atomic number (57-71 and 89-103 in the two rows under the table)
ZCELL = ([(0, 0), (0, 17), (1, 0), (1, 1)] + [(1, c) for c in range(12, 18)] + [(2, 0), (2, 1)]
         + [(2, c) for c in range(12, 18)] + [(3, c) for c in range(18)] + [(4, c) for c in range(18)]
         + [(5, 0), (5, 1)] + [(7, c) for c in range(2, 17)] + [(5, c) for c in range(3, 18)]
         + [(6, 0), (6, 1)] + [(8, c) for c in range(2, 17)] + [(6, c) for c in range(3, 18)])
# every tile, row by row as a page is read — the two f-block placeholders too: left out, a lit share had a hole in it
READING = list(CELLS)
LAST = ZCELL[117]          # oganesson, element 118: the table's last tile


def _z(t):
    """The element a caller's number names: a whole number 1-118 written as digits ("02", "12"), else None."""
    if t and re.fullmatch(r"\s*0*(\d{1,3})\s*", t):
        z = int(t)
        return z if 1 <= z <= 118 else None
    return None


def _z_family(z, default):
    return _family(*ZCELL[z - 1]) if z else default


def _share(t):
    """A percentage as a share 0-1 ("98%", "12.5 %", "45％"), else None."""
    mt = re.fullmatch(r"\s*(\d{1,3}(?:\.\d+)?)\s*[%％]\s*", t or "")
    if not mt:
        return None
    v = float(mt.group(1))
    return v / 100.0 if 0 <= v <= 100 else None


def _table(rect, fblock=True):
    """Fit the 18-column table in `rect` (x, y, w, h): (left, top, pitch). The f-block hangs half a row under it."""
    x, y, w, h = rect
    rows = 9.5 if fblock else 7.0
    p = min(w / 18.0, h / rows)
    return x + (w - 18 * p) / 2.0, y + (h - rows * p) / 2.0, p


def _cell(tx, ty, p, r, c):
    g = p * 0.10
    yy = ty + (r + (0.5 if r >= 7 else 0.0)) * p
    return (tx + c * p + g / 2.0, yy + g / 2.0, p - g, p - g)


def _draw_table(k, slide, tx, ty, p, *, mode, lit=(), lit_fill=None, fblock=True):
    """The table's tiles. `mode` "colour": each tile tinted in its family with a rule in the family colour (the
    cover); "ghost": each an empty outline (the closing, the small tables). `lit`: tiles filled solid — in their own
    family's colour, or `lit_fill`. fblock=False leaves out the two rows under the table."""
    lit = set(lit)
    cells = [rc for rc in CELLS if fblock or rc[0] < 7]
    if mode == "ghost":
        segs = []
        for r, c in cells:
            if (r, c) in lit:
                continue
            x, y, w, h = _cell(tx, ty, p, r, c)
            segs += [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)),
                     ((x, y + h), (x, y))]
        sh = na.strokes(slide, segs, k.P["ghost"], w=0.75 if p > 0.3 else 0.5)
        if sh is not None:
            dk.decorative(sh, "the outline of the periodic table, every element an empty tile: the deck's ground")
    else:
        dark = _dark(k)
        for r, c in cells:
            if (r, c) in lit:
                continue
            fam = _family(r, c)
            x, y, w, h = _cell(tx, ty, p, r, c)
            b = dk.box(slide, x, y, w, h, fill=_tint(k, fam, mosaic=True), line=dk._as_rgb(_fam(k, fam)),
                       line_w=1.0 if dark else 0.75)
            dk.decorative(b, "an element tile of the periodic table, coloured by its family; no words on it")
    for r, c in sorted(lit):
        x, y, w, h = _cell(tx, ty, p, r, c)
        b = dk.box(slide, x, y, w, h, fill=lit_fill or _fam(k, _family(r, c)))
        dk.decorative(b, "a lit element tile of the periodic table: the place the page's number names")


# ─────────────────────────────────────────── tiles ───────────────────────────────────────────
def _tile_box(k, slide, rect, fam, solid=False):
    """A tile at `rect`: a family tint with a rule in the family colour, or (solid) filled with the colour."""
    x, y, w, h = rect
    if solid:
        b = dk.box(slide, x, y, w, h, fill=_solid(k, fam))
    else:
        b = dk.box(slide, x, y, w, h, fill=_tint(k, fam), line=dk._as_rgb(_fam(k, fam)), line_w=1.25)
    dk.decorative(b, "the element tile is the ground its words sit on; the words carry the meaning")
    return b


def _m(k):
    W, H, s, o = ctx(k)
    return (0.62 if o == "land" else 0.50) * s


def _bottom(k):
    """The lowest a page's words may reach: the margin, and never into the kit's reserved footer band."""
    W, H, s, o = ctx(k)
    return H - max(_m(k), vl._FOOT + 0.02)


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
def _sizes(draws):
    """The sizes planned draws were decided at — to plan the same words again, moved, at the same sizes."""
    return {f_: z for d in draws for f_, z in getattr(d, "sizes", {}).items()}


def _over(k, slide, page, groups, th, align):
    """A portrait or square cover or closing: the table across the page (at most `th` tall) over the words, the two
    as one group centred on the page. Returns (tx, ty, p, rects, draws)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    if W >= 0.85 * H:                  # a square page: the table may take more of the height it has to spare
        th *= 1.3
    tx, _ty, p = _table((m, m, W - 2 * m, th))
    tab_h, gap, bottom = 9.5 * p, 0.55 * s, _bottom(k)
    r, ds = _v2.stack(k, slide, page, m, W - 2 * m, m + tab_h + gap, bottom, groups, anchor="top", align=align)
    words_h = max((v[1] + v[3] for v in r.values()), default=m + tab_h + gap) - (m + tab_h + gap)
    ty = m + max(0.0, (bottom - m - (tab_h + gap + words_h)) * 0.45)
    if r and ty > m + 0.01:
        r, ds = _v2.stack(k, slide, page, m, W - 2 * m, ty + tab_h + gap, bottom, groups, anchor="top", align=align,
                          start=_sizes(ds))
    return tx, ty, p, r, ds


@register(NAME, "cover", alts=3)
def _pt_cover(k, slide, f, image):
    """A wall chart: the whole table in its family colours, the kicker, title and subtitle in its bay above the
    transition metals — where a chart sets its own title. Long copy, or a page too narrow for the bay: the table at
    the side (landscape) or above (portrait), the words beside or under it."""
    W, H, s, o = ctx(k)
    m = _m(k)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.22 * s),
              (_v2.fields(f, ("subtitle",)), 0.0)]
    fblock = True
    if o == "land" and alt() == 0:
        # the main table (its two placeholder tiles stand for the f-block) on the page's foot; its bay — groups 3-12,
        # open up to the page's top margin — holds the words: at least 3in (at a 7.5in short side) above the
        # transition metals
        fblock = False
        mt = 0.70 * m
        p = min((W - 2 * mt) / 18.0, (H - 2 * mt - 3.0 * s) / 4.0)
        tx, ty = (W - 18 * p) / 2.0, H - mt - 7.0 * p
        g = 0.10 * p
        bx0, bx1 = tx + 2 * p + g / 2.0 + 0.04 * s, tx + 12 * p - g / 2.0 - 0.10 * s
        r, ds = _v2.stack(k, slide, "cover", bx0, bx1 - bx0, mt + 0.10 * s, ty + 3 * p - 0.32 * s, groups,
                          anchor="middle")
    elif o == "land":
        tw = (0.44 if alt() == 1 else 0.36) * W
        tx, ty, p = _table((W - m - tw, m, tw, H - 2 * m))
        r, ds = _v2.stack(k, slide, "cover", m, tx - 0.55 * s - m, m, _bottom(k), groups, anchor="middle")
    else:
        tx, ty, p, r, ds = _over(k, slide, "cover", groups, (0.30, 0.24, 0.18)[alt()] * H, "l")
    _draw_table(k, slide, tx, ty, p, mode="colour", fblock=fblock)
    _run_all(ds)
    return r


_TAB_H = 9.5 / 18.0         # a table with its f-block: its height per inch of width


def _tile_w(k, tiled, side, maxw):
    """The large tile's width: square, unless its number would fall under 62% of its size in the square (or under
    its floor) — then wide enough to hold it there ("1,250,000"), up to `maxw`."""
    W, H, s, o = ctx(k)
    num = dict(tiled).get("number")
    if not num:
        return side
    pad = 0.09 * side
    target = 0.44 * side * 72
    zz = max(0.62 * target, vl.TYPE[NAME]["number"][5] * s * 1.02)
    need = _v2.ink_w(k, "number", num, zz) / vl.HEADROOM + 2 * pad + 0.06 * s
    return side if need <= side else min(maxw, need)


def _hero(k, slide, page, f, mark, fam, words, lit, *, start_words=None):
    """The section and data pages: one large SOLID tile carrying `mark` (the caller's number; the section's kicker on
    its name line), the caller's `words` beside it and, when `lit` names tiles, a small table with those tiles lit in
    the tile's colour — on a landscape page the words top-aligned and the table bottom-aligned on the large tile's
    edges; on a portrait or square page tile, words and table stacked as one group, centred on the page. Roomier
    layouts: a smaller tile, then no small table. No number: no tile, the words alone, centred."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    fill = _solid(k, fam)
    loc = bool(lit) and a < 2
    tiled = [it for it in mark if it[1]]
    bottom = _bottom(k)
    r, ds = {}, []
    wkw = {"start": start_words} if start_words else {}
    loc_rect = None
    if not tiled:
        tr, tds = _v2.stack(k, slide, page, m, W - 2 * m, m, bottom, [(words, 0.0)], anchor="middle", align="c", **wkw)
        _run_all(tds)
        return tr
    if o == "land":
        side = min((0.62, 0.54, 0.48)[a] * H, 0.38 * W)
        tw = _tile_w(k, tiled, side, 0.56 * W - m)
        tile = (m + 0.15 * s, (H - side) / 2.0, tw, side)
        cx0 = tile[0] + tw + 0.80 * s
        colw = W - m - cx0
        lw = min(colw, 5.4 * s, 0.50 * side / _TAB_H) if loc else 0.0
        loc_rect = (cx0, tile[1] + side - lw * _TAB_H, lw, lw * _TAB_H) if loc else None
        y1 = (loc_rect[1] - 0.40 * s) if loc else tile[1] + side
        if words:
            tr, tds = _v2.stack(k, slide, page, cx0, colw, tile[1] - 0.04 * s, y1, [(words, 0.0)],
                                anchor="top" if loc else "middle", align="l", **wkw)
            r.update(tr)
            ds += tds
    else:
        side = min((0.30, 0.25, 0.21)[a] * H, 0.62 * W)
        lw = min(W - 2 * m, 5.0 * s, 0.17 * H / _TAB_H) if loc else 0.0
        loc_h = lw * _TAB_H + 0.40 * s if loc else 0.0
        gap = 0.45 * s
        tr, tds = {}, []
        if words:
            tr, tds = _v2.stack(k, slide, page, m, W - 2 * m, m + side + gap, bottom - loc_h, [(words, 0.0)],
                                anchor="top", align="c", **wkw)
        words_h = max((v[1] + v[3] for v in tr.values()), default=m + side) - (m + side + (gap if tr else 0.0))
        total = side + (gap + words_h if tr else 0.0) + loc_h
        y_top = m + max(0.0, (bottom - m - total) * 0.45)
        if tr and y_top > m + 0.01:
            tr, tds = _v2.stack(k, slide, page, m, W - 2 * m, y_top + side + gap, bottom - loc_h, [(words, 0.0)],
                                anchor="top", align="c", start=_sizes(tds))
        r.update(tr)
        ds += tds
        tw = _tile_w(k, tiled, side, W - 2 * m)
        tile = ((W - tw) / 2.0, y_top, tw, side)
        if loc:
            foot = max((v[1] + v[3] for v in tr.values()), default=y_top + side)
            loc_rect = ((W - lw) / 2.0, foot + 0.40 * s, lw, lw * _TAB_H)
    x, y, w, h = tile
    pad = 0.09 * side
    ink = _on(k, fill)
    # the number starts where its ink takes at most 90% of the tile's measure: held to the full measure, "1,250" at
    # 108pt filled its 3.81in box to the last hundredth and the renderer broke it "1,25 / 0" (a sheet, 2026-10-22)
    nz = 0.44 * side * 72
    num = dict(tiled).get("number")
    if num:
        iw = _v2.ink_w(k, "number", num, nz)
        if iw > 0.90 * (w - 2 * pad):
            nz = max(nz * 0.90 * (w - 2 * pad) / iw, vl.TYPE[NAME]["number"][5] * s)
    kick = dict(tiled).get("kicker")
    kz = (17 if num else 28) * s                    # no number: the kicker is the tile's only mark
    if kick:                                        # the name line on ONE line when it fits at >= the kicker's floor
        kink = _v2.ink_w(k, "kicker", kick, kz)
        if kink > 0.94 * (w - 2 * pad):
            kz = max(kz * 0.94 * (w - 2 * pad) / kink, vl.TYPE[NAME]["kicker"][5] * s)
    st = {"number": nz, "kicker": kz}
    tr, td = _v2.flow(k, slide, page, (x + pad, y + pad, w - 2 * pad, h - 2 * pad), tiled, anchor="middle",
                      align="c", ink=ink, accent=ink, mute=ink, start=st)
    r.update(tr)
    ds.append(td)
    _tile_box(k, slide, tile, fam, solid=True)
    if loc:
        tx, ty, p = _table(loc_rect)
        _draw_table(k, slide, tx, ty, p, mode="ghost", lit=lit, lit_fill=fill)
    _run_all(ds)
    return r


@register(NAME, "section", alts=3)
def _pt_section(k, slide, f, image):
    """One large tile carrying the caller's number, in the colour of the family of the element that number names
    (section 2: a noble gas), the kicker on its name line; the title beside it, and a small table with that element's
    place lit. A number that names no element (a letter, a numeral past 118) is set in the accent family, with no
    small table."""
    num, kick = text_of(f, "number"), text_of(f, "kicker")
    z = _z(num)
    return _hero(k, slide, "section", f, [("number", num), ("kicker", _v2.caps(kick) if kick else None)],
                 _z_family(z, MD), _v2.fields(f, ("title",)), [ZCELL[z - 1]] if z else [])


@register(NAME, "image_text", alts=3)
def _pt_image_text(k, slide, f, image):
    """The caller's picture mounted in an element tile — a tint of its family round it, the caption on the tile's name
    line under it; the kicker, title and body beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    cap = text_of(f, "caption")
    fam = NM
    b = 0.12 * s                                       # the tile's margin round the picture
    cap_room = (1.0 if o == "land" else 0.85) * s if cap else 0.0
    if o == "land":
        side = min((0.62, 0.54, 0.46)[alt()] * H, 0.42 * W)
        x, y = m + 0.10 * s, 0.0
    else:
        side = min((0.34, 0.27, 0.21)[alt()] * H, 0.80 * W)
        x, y = (W - side) / 2.0, m + 0.10 * s
    img_w = side - 2 * b
    r, ds = {}, []
    cap_h = 0.0
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (0.0, 0.0, img_w, cap_room), [("caption", cap)], anchor="top",
                          align="c")
        cap_h = max(v[1] + v[3] for v in cr.values()) + 0.10 * s
    else:                       # no caption: the tile keeps a foot (its empty name line), so a credit set on the
        cap_h = 0.22 * s        # picture's corner is not pressed on the tile's edge (TEXT PADDING, a 2-line credit)
    th = side + cap_h
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.10 * s), (_v2.fields(f, ("title",)), 0.20 * s),
              (_v2.fields(f, ("body",)), 0.0)]
    bottom = _bottom(k)
    if o == "land":
        y = (H - th) / 2.0
        cx0 = x + side + 0.80 * s
        tr, tds = _v2.stack(k, slide, "image_text", cx0, W - m - cx0, 0.12 * H, bottom, groups, anchor="middle")
    else:                                              # the tile over the words, one group centred on the page
        gap = 0.45 * s
        tr, tds = _v2.stack(k, slide, "image_text", m, W - 2 * m, y + th + gap, bottom, groups, anchor="top")
        words_h = max((v[1] + v[3] for v in tr.values()), default=y + th + gap) - (y + th + gap)
        y2 = m + max(0.0, (bottom - m - (th + gap + words_h)) * 0.45)
        if tr and y2 > y + 0.01:
            y = y2
            tr, tds = _v2.stack(k, slide, "image_text", m, W - 2 * m, y + th + gap, bottom, groups, anchor="top",
                                start=_sizes(tds))
    r.update(tr)
    tile = (x, y, side, th)
    img = (x + b, y + b, img_w, side - 2 * b)
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (x + b, y + side - 0.04 * s, img_w, cap_h), [("caption", cap)],
                          anchor="top", align="c")
        r.update(cr)
        ds.append(cd)
    mount = _tile_box(k, slide, tile, fam)
    dk.overlap_intent(mount, "the picture is mounted inside its element tile: layered by design")
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(tds + ds)
    return r


@register(NAME, "points", alts=4)
def _pt_points(k, slide, f, image):
    """Element tiles, one per point: its number at the top left (where a tile carries its atomic number) and the tile
    in the colour of that element's family (1 hydrogen's, 2 helium's …); the point's head as the large central mark, its
    line as the name line at the tile's foot. A row of near-square tiles on a landscape page; a 2 x 2 block, or rows of
    wide tiles (the number at the left, the head over the line), when the words need it or the page is portrait or
    square. On a portrait page the title and the tiles are one group, centred on the page."""
    W, H, s, o = ctx(k)
    m = _m(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    a = alt()
    # a row of tiles where it fits (landscape; two points; three on a square page), a 2 x 2 block for four on a page
    # that is not landscape; then rows of wide tiles
    row_ok = o == "land" or n == 2 or (n == 3 and W >= 0.85 * H)
    if a == 0 and not (n == 4 and o != "land") and row_ok:
        cols, rows = n, 1
    elif a <= 1 and n == 4:
        cols, rows = 2, 2
    elif a == 1 and row_ok:
        cols, rows = n, 1
    else:
        cols, rows = 1, n
    wide = cols == 1
    gap = (0.30 if not wide else 0.20) * s
    cw = (W - 2 * m - (cols - 1) * gap) / cols
    if not wide:                                    # an element tile stays a tile: two points are not two banners
        cw = min(cw, 3.9 * s)
    w0 = cols * cw + (cols - 1) * gap
    x0 = gx0 = (W - w0) / 2.0                       # the tiles and the title over them: one block, centred
    head = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)]
    hkw = {"anchor": "top", "start": None if a < 3 else {"title": 30 * s}}
    t_room = (0.26 if a < 2 else 0.32) * H
    r, ds = _v2.stack(k, slide, "points", x0, w0, m, m + t_room, head, **hkw)
    title_h = max((v[1] + v[3] for v in r.values()), default=m) - m
    hgap = 0.45 * s if r else 0.0
    top = m + title_h + hgap
    bottom = _bottom(k)
    room = (bottom - top - (rows - 1) * gap) / rows
    pad = (0.20 if not wide else 0.14) * s
    no_w = 0.62 * s if wide else 0.0                  # wide: the number in a column of its own at the left
    no_h = 0.0 if wide else 0.42 * s                  # square: the number's line at the top
    inner_w = cw - 2 * pad - no_w
    # the head is the tile's large mark: as large as the room allows, and on ONE line when every head fits one at
    # >= 24pt (a centred "Plane trees / lead" left a word alone under a big two-word line)
    # …else on two (a narrow tile set "Stumps are / not / replaced" at the full size, a word a line)
    big = (34 if not wide else 26) * s
    one = min(big * inner_w * 0.94 / max(0.01, _v2.ink_w(k, "item_head", hd, big)) for hd, _ln in pts)
    two = min(big * 2 * inner_w * 0.80 / max(0.01, _v2.ink_w(k, "item_head", hd, big)) for hd, _ln in pts)
    hstart = {"item_head": min(big, one) if one >= 24 * s else min(big, max(two, 20 * s))}
    lines_ = [ln for _hd, ln in pts if ln]
    if lines_:                                      # a name line that nearly fits one line is set on one
        lz = vl.TYPE[NAME]["item_line"][0] * s
        lone = min(lz * inner_w * 0.94 / max(0.01, _v2.ink_w(k, "item_line", ln, lz)) for ln in lines_)
        if 0.86 * lz <= lone < lz:
            hstart["item_line"] = lone
    al = "l" if wide else "c"

    def bottom_of(pr):
        return max((v[1] + v[3] for v in pr.values()), default=0.0)
    if wide:                                        # head over line, beside the number
        items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
        probe = _v2.plan_together(k, slide, "points", [((0, 0, inner_w, room - 2 * pad), it,
                                                        {"anchor": "top", "align": al, "start": hstart})
                                                       for it in items])
        line_h, lgap = 0.0, 0.0
        need = max(bottom_of(pr) for pr, _d in probe) + 2 * pad
        sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
    else:                                           # the head in the tile's middle, the line on its foot
        # the sizes are decided with head and line TOGETHER in the tile's room (each alone, the lines took the room
        # first and left a square page's heads none); then each is measured at its size, apart
        lgap = 0.18 * s if any(ln for _hd, ln in pts) else 0.0
        joint = _v2.plan_together(k, slide, "points", [((0, 0, inner_w, room - 2 * pad - no_h - lgap),
                                                        [("item_head", hd)] + ([("item_line", ln)] if ln else []),
                                                        {"anchor": "top", "align": al, "start": hstart})
                                                       for hd, ln in pts])
        sizes = _sizes([d_ for _pr, d_ in joint])
        lprobe = _v2.plan_together(k, slide, "points", [((0, 0, inner_w, room), [("item_line", ln)] if ln else [],
                                                         {"anchor": "top", "align": al, "start": sizes})
                                                        for _hd, ln in pts])
        hprobe = _v2.plan_together(k, slide, "points", [((0, 0, inner_w, room), [("item_head", hd)],
                                                         {"anchor": "top", "align": al, "start": sizes})
                                                        for hd, _ln in pts])
        line_h = max(bottom_of(pr) for pr, _d in lprobe)
        need = max(bottom_of(pr) for pr, _d in hprobe) + 2 * pad + no_h + line_h + lgap
        sizes = dict(sizes, **_sizes([d_ for _pr, d_ in hprobe + lprobe]))
    if wide:
        th = max(need, 0.95 * s)
    else:
        th = max(need, min(cw, room) * (0.92 if rows == 1 else 0.84))      # near-square while the page allows
        th = min(th, max(need, room))
    block = rows * th + (rows - 1) * gap
    if block > bottom - top + 1e-6:
        raise vl.VLTextOverflow("periodic.points(): the tiles need {:.2f}in, the page has {:.2f}in".format(
            block, bottom - top))
    if o == "land":
        y = top + (bottom - top - block) * 0.42
    else:                                           # portrait: title and tiles as one group, centred
        y0 = m + max(0.0, (bottom - m - (title_h + hgap + block)) * 0.45)
        if r:
            r, ds = _v2.stack(k, slide, "points", x0, w0, y0, y0 + t_room, head, anchor="top",
                              start=_sizes(ds))
        y = y0 + title_h + hgap
    specs, boxes = [], []
    for i in range(n):
        cx = gx0 + (i % cols) * (cw + gap)
        cy = y + (i // cols) * (th + gap)
        boxes.append((cx, cy))
        if wide:
            specs.append(((cx + pad + no_w, cy + pad, inner_w, th - 2 * pad),
                          [("item_head", pts[i][0])] + ([("item_line", pts[i][1])] if pts[i][1] else []),
                          {"anchor": "middle", "align": al, "start": sizes}))
        else:
            hd = _balanced(k, "item_head", pts[i][0], sizes.get("item_head", big), inner_w)
            specs.append(((cx + pad, cy + pad + no_h, inner_w, th - 2 * pad - no_h - line_h - lgap),
                          [("item_head", hd)], {"anchor": "middle", "align": al, "start": sizes}))
            if pts[i][1]:
                specs.append(((cx + pad, cy + th - pad - line_h, inner_w, line_h + 0.02 * s),
                              [("item_line", _balanced(k, "item_line", pts[i][1], sizes.get("item_line", 16 * s),
                                                       inner_w))], {"anchor": "top", "align": al, "start": sizes}))
    planned = _v2.plan_together(k, slide, "points", specs)
    nums = []
    for i in range(n):
        cx, cy = boxes[i]
        fam = _z_family(i + 1, MD)
        _tile_box(k, slide, (cx, cy, cw, th), fam)
        num_c = _shade(k, _fam(k, fam), _tint(k, fam))
        nrect = ((cx + 0.13 * s, cy + 0.10 * s, no_w - 0.13 * s, 0.45 * s) if wide
                 else (cx + 0.14 * s, cy + 0.10 * s, 0.9 * s, 0.45 * s))
        nr, nd = _v2.flow(k, slide, "points", nrect, [("item_no", str(i + 1))], anchor="top", accent=num_c)
        r.update({"item_no_{}".format(i + 1): nr["item_no"]})
        nums.append(nd)
    for pr, pd in planned:
        r.update(pr)
        ds.append(pd)
    _run_all(nums + ds)
    return r


@register(NAME, "quote", alts=2)
def _pt_quote(k, slide, f, image):
    """The table's legend tile: the opening “ hung in the tile's top-left slot (where a tile carries its number), the
    quote in the serif beside it, the attribution on the name line under it; the tile cut to the words' measure (never
    narrower than half a landscape page) and centred on the page."""
    W, H, s, o = ctx(k)
    m = _m(k)
    q = text_of(f, "quote")
    fam = MD
    if o == "land":
        x0, w0 = (0.12 if alt() == 0 else 0.07) * W, (0.76 if alt() == 0 else 0.86) * W
        wmin = 0.50 * W
    else:
        x0, w0 = m, W - 2 * m
        wmin = w0
    y0, y1 = m, _bottom(k)
    pad = 0.45 * s
    msize = vl.TYPE[NAME]["mark"][0] * s
    gut = (0.80 if o == "land" else 0.66) * s if q else 0.0      # the mark's slot: the words start beside it
    groups = [(_v2.fields(f, ("quote",)), 0.30 * s), (_v2.fields(f, ("attribution",)), 0.0)]

    def plan(x, w, cw=None, **kw):
        cw = w - 2 * pad - gut if cw is None else cw
        dx = (w - 2 * pad - gut - cw) / 2.0              # a narrower measure sits in the middle of the tile
        return _v2.stack(k, slide, "quote", x + pad + dx + gut, cw, y0 + pad, y1 - pad, groups, anchor="middle", **kw)
    qkw = {}
    if q and dk._has_cjk(q):
        # a Chinese quote a hair too wide for one line is set a little smaller ON one line: at full size its closing
        # 。 hung past the margin in the plan and fell to a line of its own in the render (4:3, 2026-10-22)
        qz = vl.TYPE[NAME]["quote"][0] * s * vl.QUOTE_GROW
        cw0 = (w0 - 2 * pad - gut) * vl.HEADROOM - qz / 72.0
        iw = _v2.ink_w(k, "quote", q, qz)
        if cw0 < iw <= 1.25 * cw0:
            qkw = {"start": {"quote": qz * cw0 / iw}}
    r, ds = plan(x0, w0, **qkw)
    sz = _sizes(ds)
    qb = _balanced(k, "quote", q, sz["quote"], w0 - 2 * pad - gut) if q else q
    if qb != q:                                         # two lines: broken where they are most even
        groups = [([("quote", qb)], 0.30 * s), (_v2.fields(f, ("attribution",)), 0.0)]
    widest = 0.0
    for f_, t in [it for g_, _gap in groups for it in g_]:
        for para in t.split("\n"):
            for ln in vl._break_lines(k, f_, para, sz[f_], (w0 - 2 * pad - gut) * vl.HEADROOM):
                widest = max(widest, _v2.ink_w(k, f_, ln, sz[f_]))
    measure = widest / vl.HEADROOM + 0.25 * s           # the words' own measure (CJK: an em more, so a closing
    if q and dk._has_cjk(q):                            # mark is never pushed onto a line of its own)
        measure += sz.get("quote", 0.0) / 72.0
    tw = min(w0, max(wmin, measure + 2 * pad + gut))
    if measure < w0 - 2 * pad - gut - 0.05 or qb != q:  # cut to the measure: set again in the narrower column, the
        x0, w0 = (W - tw) / 2.0, tw                     # tile cut to it too (never under its minimum width)
        r, ds = plan(x0, w0, cw=min(measure, w0 - 2 * pad - gut), start=sz)
    top = min(v[1] for v in r.values()) - pad
    foot = max(v[1] + v[3] for v in r.values()) + pad
    tint = _tint(k, fam)
    if q:
        qy = r["quote"][1]
        mh = msize * 1.2 / 72.0
        # the mark's ink lines up with the cap height of the quote's first line
        my = qy + 0.20 * (sz.get("quote", msize) - msize) / 72.0
        top = min(top, my - 0.25 * s)
        foot = max(foot, my + mh + 0.10 * s)
        mx1 = r["quote"][0] - 0.10 * s               # hung against the words: set to the right of its slot
        mx = max(x0 + pad * 0.45, mx1 - gut)
        mr, md = _v2.flow(k, slide, "quote", (mx, my, mx1 - mx, mh + 0.02 * s), [("mark", "“")],
                          anchor="top", align="r", accent=_shade(k, _fam(k, fam), tint), start={"mark": msize})
        r.update(mr)
        ds = [md] + ds
    _tile_box(k, slide, (x0, top, w0, foot - top), fam)
    _run_all(ds)
    return r


@register(NAME, "data", alts=3)
def _pt_data(k, slide, f, image):
    """The caller's number in one giant tile; the label and note beside it (under it on a portrait or square page). A
    percentage also lights that share of a small table's tiles, read row by row."""
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    sh_ = _share(num)
    lit = READING[:int(round(sh_ * len(READING)))] if sh_ else []
    start = {"label": vl.TYPE[NAME]["label"][0] * s * (1.35 if o == "land" else 1.15),
             "note": vl.TYPE[NAME]["note"][0] * s * 1.1}
    return _hero(k, slide, "data", f, [("number", num)], ALK, _v2.fields(f, ("label", "note")), lit,
                 start_words=start)


@register(NAME, "closing", alts=3)
def _pt_closing(k, slide, f, image):
    """The table again as an empty outline, its last element lit; the title and its line in the bay."""
    W, H, s, o = ctx(k)
    m = _m(k)
    groups = [(_v2.fields(f, ("title",)), 0.22 * s), (_v2.fields(f, ("line",)), 0.0)]
    if o == "land" and alt() == 0:
        mt = 0.70 * m
        p = min((W - 2 * mt) / 18.0, (H - 2 * mt - 2.4 * s) / 6.5)
        tx, ty = (W - 18 * p) / 2.0, H - mt - 9.5 * p
        g = 0.10 * p
        bx0, bx1 = tx + 2 * p + g / 2.0 + 0.10 * s, tx + 12 * p - g / 2.0 - 0.10 * s
        r, ds = _v2.stack(k, slide, "closing", bx0, bx1 - bx0, mt + 0.15 * s, ty + 3 * p - 0.30 * s, groups,
                          anchor="middle", align="c")
        tz = _sizes(ds).get("title")
        if tz and tz < 0.72 * vl.TYPE[NAME]["title"][0] * s:
            # a closing title squeezed into the bay at under 72% of its size reads as a caption: the words beside the
            # table instead (a 9-word title set at 24pt in the bay, 2026-10-22)
            raise vl.VLTextOverflow("periodic.closing(): the title would be set at {:.0f}pt in the bay — trying the "
                                    "table at the side".format(tz))
    elif o == "land":
        tw = (0.44 if alt() == 1 else 0.36) * W
        tx, ty, p = _table((W - m - tw, m, tw, H - 2 * m))
        r, ds = _v2.stack(k, slide, "closing", m, tx - 0.55 * s - m, m, _bottom(k), groups, anchor="middle")
    else:
        tx, ty, p, r, ds = _over(k, slide, "closing", groups, (0.30, 0.24, 0.18)[alt()] * H, "c")
    _draw_table(k, slide, tx, ty, p, mode="ghost", lit=[LAST])
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_periodic(slide, role, index):
    """An ordinary page (a chart, an agenda) on the lab ground: nothing drawn; the content rect, in REFERENCE
    inches."""
    W, H = vl.rs._canvas(slide)
    return (0.62, 0.62, W - 1.24, H - 1.24)


_card_periodic = vl._card_for(NAME)
