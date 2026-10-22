"""pixel — the Pixel game language (像素游戏): its ground painter, its card and its seven pages.

An 8-bit game screen. Everything is drawn square by square on ONE pixel grid (the screen's: its origin the frame's
outer corner, its pixel 0.06in at a 7.5in short side): a stepped pixel frame round every page and a HUD strip inside
its top edge — three hearts, and a coin beside the page's own number. The cover is a title screen (the title over a
brick floor, the hero before a hill, a run of coins and a floating block row, clouds); the section a level card (the
number large, the hero beside it); the picture sits in a pixel window frame (on the handheld ground shown in its four
greens, dithered); the points are a level map (1-1 1-2 … tiles on a path when the caller says the points are ordered,
separate stages when not); the quote an RPG dialogue box (the speaker standing over it, or a pixel portrait in it,
the speaker's name on a tab, the ▼ prompt); the key figure a score counter beside a coin, with an HP bar when the
caller gives total=; the last page an end screen (the goal flag raised, fireworks). A sprite is ONE shape per colour
(native_art.multipoly of merged pixel runs). Every page PLANS its words first (vl_native2.flow / stack /
plan_together: measured, never under a floor), draws its art clear of them, then sets them. The only words it writes
itself are the page numbers in the HUD and the level numbers on the points page (the manifest's derived words)."""
from __future__ import annotations

import math

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "pixel"
_OVER = "a sprite's colour layers interlock pixel by pixel: one picture drawn in several colours, layered by design"

# ─────────────────────────────────────────── the sprites ───────────────────────────────────────────
# one character per pixel; "." is empty. Each sprite names the palette key of every character it uses.
SPRITES = {
    "heart": ([".RR.RR.",
               "RWRRRRR",
               "RRRRRRR",
               ".RRRRR.",
               "..RRR..",
               "...R..."], {"R": "heart", "W": "heart_hi"}),
    "coin": ([".DDDD.",
              "DYYYYD",
              "DWYDYD",
              "DWYDYD",
              "DWYDYD",
              "DWYDYD",
              "DYYYYD",
              ".DDDD."], {"D": "coin_dk", "Y": "coin", "W": "coin_hi"}),
    "hud_coin": ([".DDDD.",
                  "DWYYYD",
                  "DWYDYD",
                  "DWYDYD",
                  "DYYYYD",
                  ".DDDD."], {"D": "coin_dk", "Y": "coin", "W": "coin_hi"}),
    "block": ([".DDDDDD.",
               "DWWWWWWD",
               "DWDQQDQD",
               "DWQQQQQD",
               "DWQQQQQD",
               "DWDQQDQD",
               "DWQQQQQD",
               ".DDDDDD."], {"D": "block_dk", "Q": "block", "W": "block_hi"}),
    # the hero: a round-headed kid with a tuft of hair and a scarf blowing out behind, facing right — an original
    # character (no cap, no moustache), two-pixel eyes so it still reads at one pixel to a square
    "hero": (["......H.....",
              ".....HHHH...",
              "....HHHHHH..",
              "...HHHHHHHH.",
              "...HSSSSSSH.",
              "...SSSOSOSS.",
              "...SSSOSOSS.",
              "....SSSMSS..",
              ".FFFFFFFFF..",
              "FF..CCCCCC..",
              "...SCCCCCCS.",
              "....PP..PP..",
              "....BBB.BBB."], {"H": "hero_hair", "S": "hero_skin", "O": "line", "M": "heart", "F": "hero_scarf",
                                "C": "hero_shirt", "P": "hero_pants", "B": "hero_hair"}),
    "cloud": (["....WWWW......",
               "..WWWWWWWW.WW.",
               ".WWWWWWWWWWWWW",
               "WWWWWWWWWWWWWW",
               "WWWWWWWWWWWWWW",
               ".WWWWWWWWWWWW."], {"W": "cloud"}),
    "hill": (["......GGGG......",
              "....GGGGGGGG....",
              "...GGgGGGGgGG...",
              "..GGGGGGGGGGGG..",
              ".GGGGgGGGGGgGGG.",
              "GGGGGGGGGGGGGGGG"], {"G": "hill", "g": "hill_dk"}),
    "spark": (["...S...",
               "...S...",
               "..STS..",
               "SSTTTSS",
               "..STS..",
               "...S...",
               "...S..."], {"S": "spark", "T": "spark_hi"}),
    "burst": (["....S....",
               ".S..S..S.",
               "..S...S..",
               "....T....",
               "SS.TTT.SS",
               "....T....",
               "..S...S..",
               ".S..S..S.",
               "....S...."], {"S": "spark", "T": "spark_hi"}),
    "prompt": (["AAAAAAA",
                ".AAAAA.",
                "..AAA..",
                "...A..."], {"A": "path"}),
    # the same kid face on, for the dialogue box's portrait: the tuft, two-pixel eyes, the scarf knotted at the neck
    "face": ([".....H......",
              "...HHHHHH...",
              "..HHHHHHHH..",
              ".HHHHHHHHHH.",
              ".HSSSSSSSSH.",
              ".SSOSSSSOSS.",
              ".SSOSSSSOSS.",
              ".SSSSMMSSSS.",
              "..SSSSSSSS..",
              "..FFFFFFFF..",
              ".CFFCCCCCCC.",
              "CCFFCCCCCCCC"], {"H": "hero_hair", "S": "hero_skin", "O": "line", "M": "heart", "F": "hero_scarf",
                                "C": "hero_shirt"}),
    "flag": (["FFFFFFF",
              ".FFFFFF",
              "..FFFFF",
              "...FFFF",
              "....FFF",
              ".....FF"], {"F": "flag"}),
}
BRICK = ["HHHMHHHH",
         "BBBMBBBB",
         "BBBMBBBB",
         "MMMMMMMM",
         "HHHHHHHM",
         "BBBBBBBM",
         "BBBBBBBM",
         "MMMMMMMM"]
BRICK_MAP = {"B": "brick", "M": "brick_dk", "H": "brick_hi"}


def _size(name):
    rows = SPRITES[name][0]
    return max(len(r) for r in rows), len(rows)


def _layers(rows):
    """{char: [[col, row, w, h]]}: each colour's pixels merged into rectangles — runs along a row, stacked down a
    column while the run below has the same span — so a sprite is a few rectangles per colour, not a pixel each."""
    runs = {}
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch in ". ":
                c += 1
                continue
            c0 = c
            while c < len(row) and row[c] == ch:
                c += 1
            runs.setdefault(ch, []).append([c0, r, c - c0, 1])
    out = {}
    for ch, lst in runs.items():
        merged, live = [], {}
        for rc in lst:
            prev = live.get((rc[0], rc[2]))
            if prev is not None and prev[1] + prev[3] == rc[1]:
                prev[3] += 1
            else:
                merged.append(rc)
                live[(rc[0], rc[2])] = rc
        out[ch] = merged
    return out


def _paint(k, slide, rows, cmap, x, y, px, reason, *, alpha=None):
    """Draw pixel rows at (x, y), each pixel px inches: ONE multipoly per colour. Every layer spans the whole sprite's
    box (a zero-area sliver from corner to corner): its colours are one picture, and layers of different extents
    starting on one row read to the delivery lint as a row of uneven cards (a hero's skin and outline layers,
    2026-10-22). Returns the drawn box."""
    bw, bh = max(len(r_) for r_ in rows) * px, len(rows) * px
    for ch, rects in _layers(rows).items():
        polys = [[(x + c * px, y + r * px), (x + (c + w) * px, y + r * px), (x + (c + w) * px, y + (r + h) * px),
                  (x + c * px, y + (r + h) * px)] for c, r, w, h in rects]
        polys.append([(x, y), (x + bw, y + bh), (x, y)])
        sh = na.multipoly(slide, polys, k.P[cmap[ch]], alpha=alpha)
        if sh is not None:
            dk.decorative(sh, reason)
            dk.overlap_intent(sh, _OVER)
    return (x, y, max(len(r_) for r_ in rows) * px, len(rows) * px)


NPC = {"H": "npc_hair", "C": "npc_shirt", "F": "npc_scarf"}   # the quote's speaker: the hero, palette-swapped
SPARK2 = {"S": "spark2", "T": "spark2_hi"}       # a second firework colour


def _sprite(k, slide, name, x, y, px, reason, *, flip=False, swap=None):
    rows, cmap = SPRITES[name]
    if swap:
        cmap = dict(cmap, **swap)
    if flip:
        w = max(len(r_) for r_ in rows)
        rows = [r_.ljust(w, ".")[::-1] for r_ in rows]
    return _paint(k, slide, rows, cmap, x, y, px, reason)


# ─────────────────────────────────────────── the screen's grid ───────────────────────────────────────────
def _grid(k):
    """(X0, Y0, N, M, P): the screen's pixel grid — the frame's outer corner, its size in pixels, the pixel."""
    W, H, s, o = ctx(k)
    P = 0.06 * s
    inset = 0.14 * s
    N, M = int((W - 2 * inset) / P), int((H - 2 * inset) / P)
    return (W - N * P) / 2.0, (H - M * P) / 2.0, N, M, P


def _gx(k, x):
    """x snapped to the screen's pixel grid (the nearest pixel edge)."""
    X0, _Y0, _N, _M, P = _grid(k)
    return X0 + round((x - X0) / P) * P


def _gy(k, y):
    _X0, Y0, _N, _M, P = _grid(k)
    return Y0 + round((y - Y0) / P) * P


def _top(k):
    """The first y the page's words may use: under the HUD strip."""
    _X0, Y0, _N, _M, P = _grid(k)
    return Y0 + 14 * P


def _m(k):
    """The side margin: inside the frame, clear of it."""
    W, H, s, o = ctx(k)
    X0, _Y0, _N, _M, P = _grid(k)
    return X0 + 8 * P


def _bottom(k):
    W, H, s, o = ctx(k)
    _X0, Y0, _N, M, P = _grid(k)
    return Y0 + (M - 5) * P


def _rect_poly(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _ring(k, slide, x, y, w, h, px, color, reason, *, notch=True):
    """A one-pixel ring round (x, y, w, h) — its outer edge on that rect — drawn as FOUR strips (one shape each, so no
    shape's box spans what it frames); `notch` steps the corners in by a pixel, the way a pixel window is rounded."""
    top = [_rect_poly(x + (2 * px if notch else 0), y, w - (4 * px if notch else 0), px)]
    bot = [_rect_poly(x + (2 * px if notch else 0), y + h - px, w - (4 * px if notch else 0), px)]
    left = [_rect_poly(x, y + (2 * px if notch else px), px, h - (4 * px if notch else 2 * px))]
    right = [_rect_poly(x + w - px, y + (2 * px if notch else px), px, h - (4 * px if notch else 2 * px))]
    if notch:
        left += [_rect_poly(x + px, y + px, px, px), _rect_poly(x + px, y + h - 2 * px, px, px)]
        right += [_rect_poly(x + w - 2 * px, y + px, px, px), _rect_poly(x + w - 2 * px, y + h - 2 * px, px, px)]
    out = []
    for polys in (top, bot, left, right):
        sh = na.multipoly(slide, polys, color)
        if sh is not None:
            dk.decorative(sh, reason)
            dk.overlap_intent(sh, "a pixel frame's strips meet at its stepped corners and lie round what they frame")
            out.append(sh)
    return out


def _window(k, slide, x, y, w, h, *, fill=None):
    """A game window: the panel, a light outer ring with stepped corners and a darker inner ring — the box a game
    sets its text in. (x, y, w, h) on the pixel grid."""
    X0, Y0, N, M, P = _grid(k)
    pts = [(x + 2 * P, y), (x + w - 2 * P, y), (x + w - 2 * P, y + P), (x + w - P, y + P), (x + w - P, y + 2 * P),
           (x + w, y + 2 * P), (x + w, y + h - 2 * P), (x + w - P, y + h - 2 * P), (x + w - P, y + h - P),
           (x + w - 2 * P, y + h - P), (x + w - 2 * P, y + h), (x + 2 * P, y + h), (x + 2 * P, y + h - P),
           (x + P, y + h - P), (x + P, y + h - 2 * P), (x, y + h - 2 * P), (x, y + 2 * P), (x + P, y + 2 * P),
           (x + P, y + P), (x + 2 * P, y + P)]
    sh = na.poly(slide, pts, fill=fill or k.P["panel"])
    if sh is not None:
        dk.decorative(sh, "the game window's panel: the words set on it carry the meaning")
    _ring(k, slide, x, y, w, h, P, k.P["edge"], "the game window's outer pixel border, stepped at the corners")
    _ring(k, slide, x + 2 * P, y + 2 * P, w - 4 * P, h - 4 * P, P, k.P["rim"],
          "the game window's inner pixel border", notch=False)
    return sh


# ─────────────────────────────────────────── every page: the screen ───────────────────────────────────────────
def _screen(k, slide):
    """Every page: the screen's stepped pixel frame, and the HUD inside its top edge — three hearts at the left, a
    coin and the page's own number at the right."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    _ring(k, slide, X0, Y0, N * P, M * P, P, k.P["frame"], "the game screen's stepped pixel frame round the page")
    hy = Y0 + 4 * P
    for i in range(3):
        _sprite(k, slide, "heart", X0 + (5 + 9 * i) * P, hy, P, "a heart in the game screen's HUD: the language's "
                                                                  "furniture, it counts nothing")
    num = "{:02d}".format(_v2.page_no(slide))
    size = vl.TYPE[NAME]["hud"][0] * s
    tw = _v2.ink_w(k, "hud", num, size) + 0.16 * s
    th = 6 * P
    tx = X0 + (N - 5) * P - tw
    tb = dk.text(slide, tx, hy - 0.02 * s, tw, th + 0.04 * s,
                 [k.runs(num, size, k.color("ink"), True, "body")], align=dk.PP_ALIGN.RIGHT,
                 anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    dk.decorative(tb, "the page's own number beside the HUD coin, as a game counts its stages")
    cw, _ch = _size("hud_coin")
    _sprite(k, slide, "hud_coin", _gx(k, tx - (cw + 2) * P), hy, P, "the coin in the game screen's HUD beside the "
                                                                    "page number")


vn.GROUNDS[NAME] = _screen


def _floor(k, slide, rows, *, c0=None, c1=None):
    """A brick floor `rows` pixels tall along the foot of the screen, inside its frame. Returns its top y."""
    X0, Y0, N, M, P = _grid(k)
    c0 = 1 if c0 is None else c0
    c1 = N - 1 if c1 is None else c1
    r0 = M - 1 - rows
    sc = max(1, rows // 8)
    grid = []
    for r in range(r0, M - 1):
        line = []
        for c in range(0, N):
            if c < c0 or c >= c1 or (r == M - 2 and c in (1, N - 2)):
                line.append(".")
            else:
                line.append(BRICK[((r - r0) // sc) % 8][((c - c0) // sc) % 8])
        grid.append("".join(line))
    _paint(k, slide, grid, BRICK_MAP, X0, Y0 + r0 * P, P, "the brick floor of the game screen; ground, nothing to read")
    return Y0 + r0 * P


def _floor_room(k, need, top, bottom):
    """The brick floor a page can afford under a block `need` tall that starts at `top`: (rows, the block's new
    bottom) — 16 rows, else 8, else none (0, bottom)."""
    X0, Y0, N, M, P = _grid(k)
    for rows in (16, 8):
        fb = Y0 + (M - 1 - rows) * P - 5 * P
        if fb - top >= need + 0.15 * ctx(k)[2]:
            return rows, min(bottom, fb)
    return 0, bottom


def _clear(rect, rects, pad=0.0):
    return not any(_v2.meet(rect, r, pad) for r in rects)


def _inside(k, rect):
    """Whether rect lies inside the screen's frame (clear of the frame's line and its HUD band is the caller's job)."""
    X0, Y0, N, M, P = _grid(k)
    x, y, w, h = rect
    return x >= X0 + 2 * P - 1e-6 and y >= Y0 + 2 * P - 1e-6 and x + w <= X0 + (N - 2) * P + 1e-6 and \
        y + h <= Y0 + (M - 2) * P + 1e-6


def _scatter(k, slide, items, keep, pad):
    """Draw each (name, x, y, px, reason, flip) whose box is clear of `keep` (text rects) and inside the frame; the
    drawn boxes join `keep` (sprites do not stack on each other). Returns the drawn boxes."""
    drawn = []
    for name, x, y, px, reason, flip in items:
        w, h = _size(name)
        box = (_gx(k, x), _gy(k, y), w * px, h * px)
        if _inside(k, box) and _clear(box, keep, pad):
            _sprite(k, slide, name, box[0], box[1], px, reason, flip=flip)
            keep = keep + [box]
            drawn.append(box)
    return drawn


def _foot(rects, default):
    return max((v[1] + v[3] for v in rects.values()), default=default)


def _stack(k, slide, page, x, w, y0, y1, groups, **kw):
    """vl_native2.stack centred in [y0, y1]. Its own centring pass plans each group in what the JOINT plan's later
    groups need — and when the joint plan set a title taller than the title planned alone (57.7pt in three lines vs
    49.4pt in two, a 3:4 cover), the shift it computed from the shorter real foot left the first group no room and the
    page was refused (core: vl_native2.stack, anchor="middle"). So when the centred stack refuses: plan from the top,
    then plan the same window again moved down by half the room left — the same plan, lower (kept from the top when
    the moved window would set the words any smaller)."""
    try:
        return _v2.stack(k, slide, page, x, w, y0, y1, groups, anchor="middle", **kw)
    except vl.VLTextOverflow:
        pass
    r, ds = _v2.stack(k, slide, page, x, w, y0, y1, groups, anchor="top", **kw)
    if not r:
        return r, ds
    shift = (y1 - _foot(r, y1)) / 2.0
    if shift > 0.01:
        try:
            r2, ds2 = _v2.stack(k, slide, page, x, w, y0 + shift, y1 + shift, groups, anchor="top", **kw)
        except vl.VLTextOverflow:
            return r, ds
        same = [getattr(d, "sizes", {}) for d in ds] == [getattr(d, "sizes", {}) for d in ds2]
        if same and _foot(r2, y1) <= y1 + 1e-6:
            return r2, ds2
    return r, ds


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=3)
def _px_cover(k, slide, f, image):
    """A title screen: the kicker, the title and the subtitle centred in the sky; a brick floor along the foot; the hero
    standing on it at the left in front of a hill, a row of coins floating ahead of him at head height and a row of
    blocks beyond them (as many as the width holds); clouds where the words leave the sky free. Long copy: a smaller
    scene, then the floor alone."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    sc = 2 if alt() == 0 else 1
    rows = 16 if alt() < 2 else 8
    floor_y = Y0 + (M - 1 - rows) * P
    hw, hh = _size("hero")
    band = (hh + 4) * sc * P if alt() < 2 else 3 * P
    x, w = ((0.10, 0.08, 0.07)[alt()] * W, (0.80, 0.84, 0.86)[alt()] * W) if o == "land" else (0.08 * W, 0.84 * W)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.14 * s), (_v2.fields(f, ("title",)), 0.24 * s),
              (_v2.fields(f, ("subtitle",)), 0.0)]
    # a tall page sets the words a little lower: centred in all of its sky they floated near the top, far from the scene
    y0 = _top(k) + (0.12 * (floor_y - band - _top(k)) if H > 1.2 * W else 0.0)
    r, ds = _stack(k, slide, "cover", x, w, y0, floor_y - band, groups, align="c",
                   start={"title": (64, 50, 34)[alt()] * s, "kicker": (18, 16, 15)[alt()] * s})
    keep = list(r.values())
    if alt() < 2:
        P2 = sc * P
        cl_w, cl_h = _size("cloud")
        low = floor_y - band - (cl_h + 4) * P2          # just over the scene, where the words end above it
        sky = [(X0 + 8 * P, _top(k), False), (X0 + (N - 8) * P - cl_w * P2, _top(k) + 5 * P, True),
               (X0 + (N - 12) * P - cl_w * P2, low, False), (X0 + 14 * P, (low + _top(k)) / 2.0, True)]
        _scatter(k, slide, [("cloud", cx_, cy_, P2, "a cloud in the title screen's sky", fl_) for cx_, cy_, fl_ in sky],
                 keep, 0.14 * s)
    _floor(k, slide, rows)
    if alt() < 2:
        hx = _gx(k, X0 + 3 * P + 10 * P2)               # room at his left for the hill he stands in front of
        hy = floor_y - hh * P2
        hill_w, hill_h = _size("hill")
        _sprite(k, slide, "hill", _gx(k, hx - 9 * P2), floor_y - hill_h * P2, P2, "a hill behind the hero: the title "
                                                                                   "screen's scenery")
        _sprite(k, slide, "hero", hx, hy, P2, "the hero standing on the floor: the title screen's player")
        keep.append((hx, hy, hw * P2, hh * P2))
        right = X0 + (N - 6) * P
        cw, ch = _size("coin")
        bw, bh = _size("block")
        cy, by = floor_y - (hh + 1) * P2, _gy(k, floor_y - (hh + 2) * P2)

        def run(n, nb):
            """n coins ahead of the hero, then a row of nb blocks: (fits, coins, blocks)."""
            x0 = hx + (hw + 6) * P2
            coins = [(_gx(k, x0 + i * (cw + 4) * P2), _gy(k, cy), cw * P2, ch * P2) for i in range(n)]
            end = coins[-1][0] + coins[-1][2] if coins else hx + hw * P2
            row = [(_gx(k, end + 8 * P2) + i * bw * P2, by, bw * P2, bh * P2) for i in range(nb)]
            return all(b[0] + b[2] <= right and _clear(b, keep, 0.12 * s) for b in coins + row), coins, row
        # the fullest run the width holds: coins and a block row of three, then fewer, then one block, then coins alone
        coins, row = [], []
        for n, nb in ((4, 3), (3, 3), (2, 3), (3, 1), (2, 1), (3, 0), (2, 0), (1, 0)):
            ok, c_, r_ = run(n, nb)
            if ok:
                coins, row = c_, r_
                break
        for b in coins:
            _sprite(k, slide, "coin", b[0], b[1], P2, "a coin floating ahead of the hero: a run to collect")
        for i, b in enumerate(row):
            if i == 1 or len(row) == 1:
                _sprite(k, slide, "block", b[0], b[1], P2, "the item block in the floating row")
            else:
                _paint(k, slide, BRICK, BRICK_MAP, b[0], b[1], P2, "a brick in the floating block row")
        keep += coins + row
        _scatter(k, slide, [("hill", X0 + (N - 4) * P - hill_w * P2, floor_y - hill_h * P2, P2,
                             "a second hill on the floor at the far end: the title screen's scenery", True)],
                 keep, 0.10 * s)
    _run_all(ds)
    return r


def _sprite_scale(k, size, rows, frac=1.0):
    """The pixel scale (1-4) at which a sprite `rows` tall stands about `frac` of a figure's cap height at `size`."""
    P = _grid(k)[4]
    return max(1, min(4, int(round(0.72 * size / 72.0 * frac / (rows * P)))))


def _number_start(k, num, w, start, sprite, frac, gap):
    """The number's starting size, kept small enough that the number AND the sprite standing beside it fit a column
    `w` wide: a 150pt figure filled a square page's column and left its coin no room (it was dropped)."""
    P = _grid(k)[4]
    sw, sh = _size(sprite)
    floor = vl.TYPE[NAME]["number"][5] * ctx(k)[2]
    size = start
    for _i in range(10):
        lead = (sw * _sprite_scale(k, size, sh, frac) + gap) * P
        room = (w - lead) * vl.HEADROOM - dk.TEXT_INSET_LR
        iw = _v2.ink_w(k, "number", num, size)
        if iw <= room or size <= floor:
            break
        size = max(floor, size * room / iw * 0.98)
    return size


def _number_beside(k, slide, page, r, ds, num, sprite, frac, gap, reason):
    """Stand `sprite` beside the planned number, on its baseline, the pair centred together: the number is re-set (at
    the size it was planned at) in its column narrowed by the sprite's room, so it moves right by half of it. The
    sprite is drawn only when it stays inside the frame and clear of the other words. Returns the number's rect."""
    X0, Y0, N, M, P = _grid(k)
    s = ctx(k)[2]
    nx, ny, nw, nh = r["number"]
    di = next(i for i, d in enumerate(ds) if "number" in getattr(d, "sizes", {}))
    size = ds[di].sizes["number"]
    sw, sh = _size(sprite)
    sc = _sprite_scale(k, size, sh, frac)
    lead = (sw * sc + gap) * P
    nr, nd = _v2.flow(k, slide, page, (nx + lead, ny, nw - lead, nh + 0.05 * s), [("number", num)], anchor="top",
                      align="c", start={"number": size})
    if abs(nd.sizes.get("number", 0.0) - size) < 0.05:
        r["number"], ds[di] = nr["number"], nd
        nx, nw = nx + lead, nw - lead
    iw = min(nw, _v2.ink_w(k, "number", num, size))
    # the figure's baseline as the renderer sets it (vl_native2.first_baseline models LibreOffice's 1.2em line with the
    # baseline 1.0em below its top, face metrics aside): the sprite stands on it
    base = ny + _v2.first_baseline(k, "number", num, size)
    box = (_gx(k, nx + nw / 2.0 - iw / 2.0 - lead), _gy(k, base - sh * sc * P), sw * sc * P, sh * sc * P)
    others = [v for f_, v in r.items() if f_ != "number"]
    if _inside(k, box) and _clear(box, others, 0.10 * s) and box[0] > X0 + 4 * P:
        _sprite(k, slide, sprite, box[0], box[1], sc * P, reason)
    return r["number"]


@register(NAME, "section", alts=2)
def _px_section(k, slide, f, image):
    """A level card: the kicker, then the section's number large with the hero standing beside it on its baseline (the
    pair centred together), then the title — centred on a plain screen over a brick floor."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    num = text_of(f, "number")
    rows = 16 if alt() == 0 else 8
    floor_y = Y0 + (M - 1 - rows) * P
    x, w = ((0.14 if alt() == 0 else 0.08) * W, (0.72 if alt() == 0 else 0.84) * W)
    hero = bool(num) and not dk._has_cjk(num)
    start = {"number": (140 if alt() == 0 else 110) * s}
    if hero:
        start["number"] = _number_start(k, num, w, start["number"], "hero", 1.0, 5)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.18 * s), ([("number", num)] if num else [], 0.20 * s),
              (_v2.fields(f, ("title",)), 0.0)]
    r, ds = _stack(k, slide, "section", x, w, _top(k), floor_y - 4 * P, groups, align="c",
                      start=start)
    _floor(k, slide, rows)
    if hero and "number" in r:
        _number_beside(k, slide, "section", r, ds, num, "hero", 1.0, 5, "the hero beside the level number, about to "
                                                                       "start the level")
    _run_all(ds)
    return r


@register(NAME, "image_text", alts=3)
def _px_image_text(k, slide, f, image):
    """The caller's picture in a pixel window frame — three one-pixel rings, stepped at the outer corners — the caption
    under it; the kicker, title and body beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    cap = text_of(f, "caption")
    m = _m(k)
    span = lambda v: round(v / P) * P                     # noqa: E731 — a length in whole pixels
    if o == "land":
        img = (_gx(k, m + 0.1 * s), _gy(k, _top(k) + 0.25 * s), span((0.46, 0.40, 0.34)[alt()] * W),
               span((0.58 if cap else 0.68) * H))
    else:
        img = (_gx(k, 0.12 * W), _gy(k, _top(k) + 0.15 * s), span(0.76 * W), span((0.34, 0.27, 0.20)[alt()] * H))
    r, ds = {}, []
    foot = img[1] + img[3] + 3 * P
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (img[0] - 3 * P, foot + 0.18 * s, img[2] + 6 * P, 0.9 * s),
                          [("caption", cap)])
        r.update(cr)
        ds.append(cd)
        foot = _foot(cr, foot)
    if o == "land":
        cx = img[0] + img[2] + 3 * P + 0.6 * s
        col = (cx, _top(k), W - m - cx, _bottom(k) - _top(k))
    else:
        col = (0.10 * W, foot + 0.35 * s, 0.80 * W, _bottom(k) - foot - 0.35 * s)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.20 * s),
              (_v2.fields(f, ("body",)), 0.0)]
    if o == "land":
        tr, tds = _stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3], groups)
    else:
        tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3], groups, anchor="top")
    r.update(tr)
    x, y, w, h = img
    _ring(k, slide, x - 3 * P, y - 3 * P, w + 6 * P, h + 6 * P, P, k.P["edge"],
          "the picture's pixel window frame, stepped at the corners")
    _ring(k, slide, x - 2 * P, y - 2 * P, w + 4 * P, h + 4 * P, P, k.P["rim"], "the picture frame's middle pixel ring",
          notch=False)
    _ring(k, slide, x - P, y - P, w + 2 * P, h + 2 * P, P, k.P["frame"], "the picture frame's inner pixel ring",
          notch=False)
    vl._place_image(k, slide, _lcd(k, image, img), img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(tds + ds)
    return r


def _lcd(k, image, rect):
    """On a ground whose palette names the screen's four tones (lcd0 darkest … lcd3 lightest — the handheld), the
    caller's picture as that screen shows it: its own grey levels set in the four greens, dithered on a fine pixel grid
    (a third of the screen's pixel), upright and whole (the frame crops it, as any picture). A COPY in a cache folder,
    keyed by the source's path, size and mtime, the grid and the tones; named after the source so its alt text is the
    caller's. A colour ground (and an image-series slot, whose provenance travels with its own file) gets the picture
    as given."""
    import hashlib
    import os
    import tempfile
    from pathlib import Path
    tones = [k.P.get("lcd{}".format(i)) for i in range(4)]
    if not all(tones) or not isinstance(image, (str, os.PathLike)):
        return image
    image = str(image)
    from PIL import Image, ImageOps
    path, _alt, slot = vl._resolve(k, image)
    if slot:
        return image
    W, H, s, o = ctx(k)
    px = _grid(k)[4] / 3.0
    with Image.open(path) as src:
        im = ImageOps.exif_transpose(src).convert("L")
    iw, ih = im.size
    # the WHOLE picture, upright and in its own proportions (the frame crops it, as it crops any picture): sized so
    # that, cover-fitted to the frame, one dithered pixel is `px` across
    f = max(rect[2] / iw, rect[3] / ih) / px
    nx, ny = max(8, int(round(iw * f))), max(8, int(round(ih * f)))
    st = Path(path).stat()
    key = hashlib.sha1("{}|{}|{}|{}x{}|{}".format(Path(path).resolve(), st.st_size, st.st_mtime_ns, nx, ny,
                                                  tones).encode()).hexdigest()[:16]
    d = Path(tempfile.gettempdir()) / "slide-maker-pixel" / key
    out = d / (Path(str(image)).stem + ".png")
    if vl._cached_ok(out):
        return str(out)
    d.mkdir(parents=True, exist_ok=True)
    im = ImageOps.autocontrast(im.resize((nx, ny), Image.LANCZOS), cutoff=1)
    pal = Image.new("P", (1, 1))
    pal.putpalette([0, 0, 0, 85, 85, 85, 170, 170, 170, 255, 255, 255] + [0, 0, 0] * 252)
    q = im.convert("RGB").quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG)
    q.putpalette([int(t[i:i + 2], 16) for t in tones for i in (0, 2, 4)] + [0, 0, 0] * 252)
    up = max(1, int(1600 / max(nx, ny)) + 1)                              # sharp pixels in any renderer
    vl._atomic_save(q.convert("RGB").resize((nx * up, ny * up), Image.NEAREST), out, format="PNG")
    return str(out)



def _level_no(i):
    return "1-{}".format(i + 1)


def _tile(k, slide, x, y, w, h):
    """A level tile on the map: a stepped window carrying the level number."""
    _window(k, slide, x, y, w, h, fill=k.P["tile"])


def _path(k, slide, pts, P):
    """A dotted pixel path through the points (x, y) — straight runs, a pixel every other pixel — ONE shape."""
    dots = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(round(max(abs(x1 - x0), abs(y1 - y0)) / P))
        for i in range(0, n + 1, 2):
            t = i / float(max(1, n))
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            dots.append(_rect_poly(cx - P / 2.0, cy - P / 2.0, P, P))
    sh = na.multipoly(slide, dots, k.P["path"])
    if sh is not None:
        dk.decorative(sh, "the dotted path between the level tiles: the order the caller gave the points in")
        dk.overlap_intent(sh, "the level map's path runs up to the tiles it joins")
    return sh


@register(NAME, "points", alts=5)
def _px_points(k, slide, f, image):
    """A level map: each point a level tile (1-1, 1-2 …) with its head and line under it — a row of stages across a
    landscape page, a column down a portrait or square one, the block at the page's optical centre. When the caller
    says the points are ordered (ordered=True) a dotted path joins the tiles, and on the row the hero stands on the
    first tile and a goal flag flies over the last; otherwise the stages stand apart (no route is claimed). Long copy:
    smaller tiles, then the column, then two columns (each tile over its words, then beside them)."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    ordered = f.get("ordered", False)
    if not isinstance(ordered, bool):
        raise TypeError("pixel.points(): ordered= is True or False, got {!r}".format(ordered))
    m = _m(k)
    x0, w0 = m, W - 2 * m
    row_map = o == "land" and alt() < 2
    r, ds = _v2.stack(k, slide, "points", x0, w0, _top(k), _top(k) + (0.26 if alt() == 0 else 0.32) * H,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", start=None if alt() < 2 else {"title": 30 * s})
    top = _gy(k, _foot(r, _top(k)) + 0.30 * s)
    bottom = _bottom(k)
    nos = [_level_no(i) for i in range(n)]
    nsize = (22, 18, 18, 16, 15)[alt()] * s
    th = (16, 13, 13, 11, 11)[alt()] * P
    # the tile's panel (inside its two rings, 3 pixels a side) holds the level number with room to spare
    tw = max(th, _gx(k, X0 + max(_v2.ink_w(k, "item_no", t, nsize) for t in nos) / vl.HEADROOM + 10 * P
                     + dk.TEXT_INSET_LR) - X0)
    hw, hh = _size("hero")
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    art, nums = [], []
    if row_map:
        gap = 0.45 * s
        cw = (w0 - (n - 1) * gap) / n
        lift = (hh + 1) * P if ordered else 0.0
        tgap = 0.22 * s
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw, max(0.1, bottom - top - lift - th - tgap)), it,
                                                        {"anchor": "top", "align": "c"}) for it in items])
        need = max(_foot(pr, 0.0) for pr, _d in probe)
        total = lift + th + tgap + need
        if total > bottom - top + 1e-6:
            raise vl.VLTextOverflow("pixel.points(): the stages need {:.2f}in, the page has {:.2f}in".format(
                total, bottom - top))
        rows_f, bottom = _floor_room(k, total, top, bottom)
        if rows_f:
            art.append(lambda: _floor(k, slide, rows_f))
        ty = _gy(k, top + (bottom - top - total) * 0.42 + lift)
        ttop = ty + th + tgap
        sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
        cols = [x0 + i * (cw + gap) for i in range(n)]
        planned = _v2.plan_together(k, slide, "points", [((cols[i], ttop, cw, need + 0.1 * s), it,
                                                          {"anchor": "top", "align": "c", "start": sizes})
                                                         for i, it in enumerate(items)])
        tiles = [(_gx(k, cols[i] + (cw - tw) / 2.0), ty, tw, th) for i in range(n)]
        if ordered:
            mid = _gy(k, ty + th / 2.0)
            for a_, b_ in zip(tiles, tiles[1:]):
                art.append(lambda a_=a_, b_=b_: _path(k, slide, [(a_[0] + tw + 2 * P, mid), (b_[0] - 2 * P, mid)], P))
            hx = _gx(k, tiles[0][0] + (tw - hw * P) / 2.0)
            art.append(lambda: _sprite(k, slide, "hero", hx, ty - hh * P, P, "the hero standing on the first level "
                                                                            "tile: where the route starts"))
            art.append(lambda: _goal(k, slide, _gx(k, tiles[-1][0] + tw / 2.0), ty, (hh + 1) * P, P))
    else:
        cols = 2 if (alt() >= 3 and n >= 3) else 1
        stacked = cols == 2 and alt() == 3   # two columns: each tile over its words, which keep the cell's width
        cgap = 0.45 * s
        cw = (w0 - (cols - 1) * cgap) / cols
        rows = -(-n // cols)
        off = 0.0 if stacked else tw + 0.30 * s
        drop = th + 0.14 * s if stacked else 0.0
        gap = (0.30 if alt() < 3 else 0.24) * s
        share = (bottom - top - (rows - 1) * gap) / rows - drop
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - off, max(0.1, share)), it, {"anchor": "top"})
                                                       for it in items])
        hs = [_foot(pr, 0.0) for pr, _d in probe]
        row_h = [max([th] + [drop + hs[i] for i in range(rw * cols, min(n, rw * cols + cols))]) for rw in range(rows)]
        block = sum(row_h) + gap * (rows - 1)
        if block > bottom - top + 1e-6:
            raise vl.VLTextOverflow("pixel.points(): the stages need {:.2f}in, the page has {:.2f}in".format(
                block, bottom - top))
        rows_f, bottom = _floor_room(k, block, top, bottom)
        if rows_f:
            art.append(lambda: _floor(k, slide, rows_f))
        if rows > 1:                  # a tall page spreads its stages down the map (a long path), within reason
            spread = min((bottom - top - block) * 0.5 / (rows - 1), 0.9 * s)
            gap += spread
            block += spread * (rows - 1)
        y = _gy(k, top + (bottom - top - block) * 0.40)
        ys = []
        for rw in range(rows):
            ys.append(y)
            y = _gy(k, y + row_h[rw] + gap)
        sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
        xs = [_gx(k, x0 + (i % cols) * (cw + cgap)) for i in range(n)]
        # beside its tile, a stage whose words are shorter than the tile sits level with the tile's middle
        planned = _v2.plan_together(k, slide, "points", [((xs[i] + off, ys[i // cols] + drop
                                                           + (0.0 if stacked else max(0.0, (th - hs[i]) / 2.0)),
                                                           cw - off, row_h[i // cols] - drop + 0.1 * s), it,
                                                          {"anchor": "top", "start": sizes})
                                                         for i, it in enumerate(items)])
        tiles = [(xs[i], ys[i // cols], tw, th) for i in range(n)]
        if ordered:
            # the route follows the reading order: down the column, or along each row of the two columns (a row's
            # turn to the next row would cross the words, so it is left to the numbers)
            # (two columns with each tile beside its words: any route would cross the words — none is drawn)
            pairs = [] if cols == 2 and not stacked else \
                [(tiles[i], tiles[i + 1]) for i in range(n - 1) if not stacked or i % 2 == 0]
            for a_, b_ in pairs:
                if stacked:
                    my = _gy(k, a_[1] + th / 2.0)
                    pts_ = [(a_[0] + tw + 2 * P, my), (b_[0] - 2 * P, my)]
                else:
                    cx = _gx(k, a_[0] + tw / 2.0)
                    pts_ = [(cx, a_[1] + th + 2 * P), (cx, b_[1] - 2 * P)]
                art.append(lambda pts_=pts_: _path(k, slide, pts_, P))
    for i, (tx_, ty_, tw_, th_) in enumerate(tiles):
        art.append(lambda tx_=tx_, ty_=ty_: _tile(k, slide, tx_, ty_, tw, th))
        nr, nd = _v2.flow(k, slide, "points", (tx_ + 3 * P, ty_ + 3 * P, tw - 6 * P, th - 6 * P), [("item_no", nos[i])],
                          anchor="middle", align="c", ink=k.P["tile_ink"], start={"item_no": nsize})
        nums.append(nd)
        r.update(nr)
    for pr, pd in planned:
        r.update(pr)
        ds.append(pd)
    _run_all(art + nums + ds)
    return r


def _goal(k, slide, x, y_base, h, q):
    """A goal flag: a pole `h` tall with its left edge at x (on the grid) and its foot at y_base, a round knob on its
    top, the flag flying to the left of it; q is the flag's pixel (the pole is one of them wide)."""
    pole = na.multipoly(slide, [_rect_poly(x, y_base - h + 3 * q, q, h - 3 * q)], k.P["pole"])
    if pole is not None:
        dk.decorative(pole, "the goal flag's pole: the end of the level")
        dk.overlap_intent(pole, "the goal flag's pole stands on the ground or the last tile under it")
    _paint(k, slide, [".B.", "BBB", ".B."], {"B": "coin"}, x - q, y_base - h, q, "the knob on top of the goal flag's "
                                                                                 "pole")
    fw, _fh = _size("flag")
    _sprite(k, slide, "flag", x - fw * q, y_base - h + 4 * q, q, "the goal flag flying from its pole")
    return (x - fw * q, y_base - h, (fw + 2) * q, h)


@register(NAME, "quote", alts=3)
def _px_quote(k, slide, f, image):
    """An RPG dialogue box: a game window holding the quote, the ▼ prompt in its lower right corner, the speaker's name
    (the attribution) on a tab above its left end. The speaker — the hero's sprite in another palette, as a game
    swaps colours for a new character — stands large above the box when the page has the room; otherwise a pixel
    portrait of them sits in the box beside the words, and for the longest copy the words take the whole box."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    a = text_of(f, "attribution")
    q = text_of(f, "quote")
    if not q:
        raise ValueError("pixel.quote(): needs quote= — the dialogue box holds the speaker's words; a name alone "
                         "(attribution=) says nothing")
    hw, hh = _size("hero")
    fw_, _fh = _size("face")
    pad = 4 * P
    big, side = alt() == 0, alt() == 1
    bw = _gx(k, X0 + ((0.80, 0.86, 0.90) if o == "land" else (0.86, 0.88, 0.90))[alt()] * W) - X0
    bx = _gx(k, (W - bw) / 2.0)
    pf = (fw_ + 4) * P                        # the portrait's frame: the face and a two-pixel margin
    top, bottom = _top(k), _bottom(k)
    tab_h, tdr = 0.0, None
    if a:
        _tr, tdr = _v2.flow(k, slide, "quote", (bx, top, bw * 0.6, 1.2 * s), [("attribution", a)], anchor="top")
        a_h = _foot(_tr, top) - top
        tab_h = math.ceil((a_h + 6 * P + 0.06 * s) / P) * P      # the name, and three pixels of window round it
    qx = bx + pad + 2 * P + (pf + 3 * P if side else 0.0)
    qw = bx + bw - pad - 2 * P - qx
    above = (2 * hh + 6) * P if big else 0.0  # the least room the standing speaker needs
    room = bottom - top - tab_h - P - pad - 12 * P - above
    _qr, qd = _v2.flow(k, slide, "quote", (qx, top, qw, max(0.1, room)), [("quote", q)], anchor="top")
    # the box is cut to the words it holds (a short quote set in two balanced lines left half a wide box empty) —
    # never narrower than half the page (most of a portrait one) or than its name tab needs
    used = _qr["quote"][2]
    lo = (0.50 if o == "land" else 0.80) * W
    if a:
        lo = max(lo, (_v2.ink_w(k, "attribution", a, tdr.sizes.get("attribution", 16 * s)) / vl.HEADROOM
                      + 2 * pad + 4 * P + dk.TEXT_INSET_LR) / 0.7 + 4 * P)
    nb = _gx(k, X0 + max(lo, (qx - bx) + used + pad + 2 * P)) - X0
    if nb < bw - P / 2.0:
        qx, bw = qx - bx, nb
        bx = _gx(k, (W - bw) / 2.0)
        qx += bx
        qw = bx + bw - pad - 2 * P - qx
        _qr, qd = _v2.flow(k, slide, "quote", (qx, top, qw, max(0.1, room)), [("quote", q)], anchor="top",
                           start=qd.sizes)
    q_h = _foot(_qr, top) - top
    inner = max(q_h, pf if side else 0.0)
    # the words, then a row of their own for the ▼ prompt (4 pixels) under the last line, inside the inner ring
    bh = _gy(k, Y0 + inner + pad + 11 * P) - Y0
    if big:
        by = _gy(k, bottom - bh)
    else:
        by = _gy(k, top + tab_h + P + max(0.0, (bottom - top - tab_h - P - bh) * 0.5))
    tab_top = by - tab_h - P
    r, ds = {}, []
    if big:
        space = tab_top - 3 * P - top
        sc = min(4, int(space / (hh * P)), int(0.34 * H / (hh * P)))
        if sc < 2:
            raise vl.VLTextOverflow("pixel.quote(): no room for the speaker over the box — trying the portrait")
    qy = by + pad + 2 * P + (max(0.0, pf - q_h) / 2.0 if side else 0.0)
    qr, qd = _v2.flow(k, slide, "quote", (qx, qy, qw, q_h + 0.1 * s), [("quote", q)], anchor="top",
                      start=getattr(qd, "sizes", None))
    r.update(qr)
    ds.append(qd)
    if big:
        sx = _gx(k, W / 2.0 - hw * sc * P / 2.0)
        sy = _gy(k, tab_top - 3 * P - hh * sc * P)
        shadow = na.multipoly(slide, [_rect_poly(sx - sc * P, sy + hh * sc * P, (hw + 2) * sc * P, sc * P)],
                              k.P["cloud"])
        if shadow is not None:
            dk.decorative(shadow, "the speaker's shadow on the ground")
        _sprite(k, slide, "hero", sx, sy, sc * P, "the speaker of the quote, standing over the dialogue box",
                swap=NPC)
    _window(k, slide, bx, by, bw, bh)
    if side:
        px_, py_ = bx + pad, by + pad
        _ring(k, slide, px_, py_, pf, pf, P, k.P["rim"], "the portrait's pixel frame in the dialogue box", notch=False)
        _sprite(k, slide, "face", px_ + 2 * P, py_ + 2 * P, P, "the speaker's pixel portrait in the dialogue box",
                swap=NPC)
    aw, ah = _size("prompt")
    _sprite(k, slide, "prompt", bx + bw - pad - (aw + 1) * P, by + bh - 4 * P - ah * P, P,
            "the dialogue box's prompt: the speaker has more to say")
    if a:
        tw = min(bw * 0.7, _v2.ink_w(k, "attribution", a, tdr.sizes.get("attribution", 16 * s)) / vl.HEADROOM
                 + 2 * pad + 4 * P + dk.TEXT_INSET_LR)
        tab = (bx + 2 * P, tab_top, math.ceil(tw / P) * P, tab_h)
        tr, tdr = _v2.flow(k, slide, "quote", (tab[0] + pad, tab[1] + (tab_h - a_h) / 2.0, tab[2] - 2 * pad,
                                               a_h + 0.02 * s), [("attribution", a)], anchor="top",
                           start=tdr.sizes)
        _window(k, slide, *tab)
        r.update(tr)
        ds.append(tdr)
    _run_all(ds)
    return r


def _hp_bar(k, slide, x, y, w, share, P):
    """An HP bar: a heart, then a pixel-framed bar filled to `share` (snapped to the pixel), a light pixel row along
    the top of the fill. (x, y) its top-left; w its whole width. Returns its height."""
    hw, hh = _size("heart")
    _sprite(k, slide, "heart", x, y + P, P, "the heart at the head of the HP bar")
    bx = x + (hw + 2) * P
    bw = _gx(k, bx + w - (hw + 2) * P) - bx
    bh = 8 * P
    inner_w = bw - 4 * P
    fill_w = round(share * inner_w / P) * P
    _ring(k, slide, bx, y, bw, bh, P, k.P["edge"], "the HP bar's pixel frame")
    empty = na.multipoly(slide, [_rect_poly(bx + 2 * P + fill_w, y + 2 * P, inner_w - fill_w, bh - 4 * P)],
                         k.P["bar_empty"]) if inner_w - fill_w > 0 else None
    if empty is not None:
        dk.decorative(empty, "the empty part of the HP bar: the rest of the total")
        dk.overlap_intent(empty, "the HP bar's fill and its empty part lie inside its frame")
    if fill_w > 0:
        full = na.multipoly(slide, [_rect_poly(bx + 2 * P, y + 2 * P, fill_w, bh - 4 * P)], k.P["bar"])
        dk.overlap_intent(full, "the HP bar's fill lies inside its frame")
        hi = na.multipoly(slide, [_rect_poly(bx + 2 * P, y + 2 * P, fill_w, P)], k.P["heart_hi"])
        dk.decorative(hi, "the light row along the top of the HP bar's fill")
        dk.overlap_intent(hi, "the light row lies on the HP bar's fill")
    return bh


@register(NAME, "data", alts=3)
def _px_data(k, slide, f, image):
    """A score counter: the number large with a coin standing beside it on its baseline (the pair centred); with
    total= an HP bar under it — a heart and a pixel bar filled to the number's share of the total; the label and the
    note under that, all centred."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    num = text_of(f, "number")
    total = text_of(f, "total")
    if total and not num:
        raise ValueError("pixel.data(): total= draws a share bar of the number — pass number= too")
    share = _v2.share_of("pixel", num, total) if total else None
    x, w = ((0.12, 0.08, 0.07)[alt()] * W, (0.76, 0.84, 0.86)[alt()] * W)
    bar_h = 8 * P
    start = {"number": (150, 120, 96)[alt()] * s}
    if num:
        start["number"] = _number_start(k, num, w, start["number"], "coin", 0.8, 4)
    groups = [([("number", num)] if num else [], (bar_h + 0.55 * s) if share is not None else 0.25 * s),
              (_v2.fields(f, ("label", "note")), 0.0)]
    r, ds = _stack(k, slide, "data", x, w, _top(k), _bottom(k), groups, align="c", start=start)
    if num and "number" in r:
        nx, ny, nw, nh = _number_beside(k, slide, "data", r, ds, num, "coin", 0.8, 4,
                                        "the coin beside the score: the number is the score")
        if share is not None:
            bwid = _gx(k, X0 + min(w, max(0.42 * W, 4.0 * s))) - X0
            _hp_bar(k, slide, _gx(k, x + (w - bwid) / 2.0), _gy(k, ny + nh + 0.22 * s), bwid, share, P)
    _run_all(ds)
    return r


@register(NAME, "closing", alts=3)
def _px_closing(k, slide, f, image):
    """The end screen: the level's goal reached — a brick floor along the foot, the goal flag raised on a tall pole at
    the right and the hero standing below it; the title and its line beside them (above them on a portrait or square
    page); fireworks bursting where the words leave the sky free."""
    W, H, s, o = ctx(k)
    X0, Y0, N, M, P = _grid(k)
    rows = 16 if alt() < 2 else 8
    floor_y = Y0 + (M - 1 - rows) * P
    hw, hh = _size("hero")
    sc = 2 if alt() == 0 else 1
    q = sc * P
    land = o == "land"
    pole_x = _gx(k, X0 + (N - 18) * P) if land else _gx(k, X0 + (N - 16) * P)
    if land:
        x, w = _m(k) + 0.2 * s, (0.58, 0.64, 0.70)[alt()] * W
        r, ds = _stack(k, slide, "closing", x, w, _top(k), floor_y - 4 * P,
                       [(_v2.fields(f, ("title",)), 0.25 * s), (_v2.fields(f, ("line",)), 0.0)],
                       align="l", start={"title": (60, 46, 34)[alt()] * s})
    else:
        x, w = (0.09 * W, 0.82 * W)
        r, ds = _stack(k, slide, "closing", x, w, _top(k), floor_y - (hh * sc + 8) * P,
                       [(_v2.fields(f, ("title",)), 0.25 * s), (_v2.fields(f, ("line",)), 0.0)],
                       align="c", start={"title": (54, 44, 34)[alt()] * s})
    keep = list(r.values())
    _floor(k, slide, rows)
    tall = floor_y - (_top(k) + 2 * P)
    while tall > (hh * sc + 8) * P and not _clear((pole_x - 8 * q, floor_y - tall, 10 * q, tall), keep, 0.12 * s):
        tall -= P
    if _clear((pole_x - 8 * q, floor_y - tall, 10 * q, tall), keep, 0.12 * s):
        keep.append(_goal(k, slide, pole_x, floor_y, _gy(k, Y0 + tall) - Y0, q))
    hx = _gx(k, pole_x - (hw + 6) * q)
    hbox = (hx, floor_y - hh * q, hw * q, hh * q)
    if _clear(hbox, keep[:len(r)], 0.10 * s):
        _sprite(k, slide, "hero", hx, hbox[1], q, "the hero at the goal: the level is complete")
        keep.append(hbox)
    bw_, bh_ = _size("burst")
    tx0, tx1 = x, x + w                                   # the words' column
    sky = []
    if land:                                              # a lane between the words and the flag, then the corners
        lx0, lx1 = tx1 + 0.15 * s, pole_x - 8 * q - 0.15 * s
        if lx1 - lx0 >= bw_ * q:
            cx = (lx0 + lx1) / 2.0
            sky += [("burst", cx - bw_ * q / 2.0, _top(k) + 2 * P, q, None),
                    ("spark", cx - 3.5 * q + 3 * q, _top(k) + 2 * P + (bh_ + 6) * q, q, SPARK2),
                    ("burst", cx - bw_ * q / 2.0 - 4 * q, _top(k) + 2 * P + (2 * bh_ + 4) * q, q, SPARK2)]
    sky += [("burst", X0 + 10 * P, _top(k) + 2 * P, q, SPARK2),
            ("burst", tx0 + (tx1 - tx0) / 2.0 - bw_ * q / 2.0, _top(k) + 2 * P, q, None),
            ("spark", X0 + 12 * P, floor_y - (bh_ + 10) * q, q, None)]
    # each firework is tried at the scene's scale and then, on the same centre, at one pixel to a square (a 4:3 page's
    # sky over a two-line title holds a small burst, not a big one)
    sky = [c for nm, sx, sy, px_, sw in sky for c in ((nm, sx, sy, px_, sw),) + (
        ((nm, sx + _size(nm)[0] * (px_ - P) / 2.0, sy + _size(nm)[1] * (px_ - P) / 2.0, P, sw),) if px_ > P else ())]
    fired = 0
    for name, sx, sy, px_, swap in sky:
        bw0, bh0 = _size(name)
        box = (_gx(k, sx), _gy(k, sy), bw0 * px_, bh0 * px_)
        if fired < 4 and _inside(k, box) and box[1] + box[3] < floor_y - 2 * P and _clear(box, keep, 0.14 * s):
            _sprite(k, slide, name, box[0], box[1], px_, "a firework over the end screen: the level is won",
                    swap=swap)
            keep.append(box)
            fired += 1
    _run_all(ds)
    return r



# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_pixel(slide, role, index):
    """An ordinary page (a chart, an agenda) on the game screen: the frame and the HUD are its ground (new_slide paints
    them); the content rect inside the frame, under the HUD, in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.62, 0.95, W - 1.24, H - 1.55)


_card_pixel = vl._card_for(NAME)
