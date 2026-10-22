"""calendar — the Tear-off calendar language (撕页日历): its ground painter, its card and its seven pages.

A desk tear-off calendar block: a bound header with two metal rings, torn stubs of the pages already gone under it, the
current page, and the leaves still to come showing as a stack of page edges at its foot. The stack THINS as the deck
goes on (fewer leaves, more stubs) and the last page is nearly the last leaf. The section number and the key figure are
the giant date numeral in Sunday red; the points are a week strip of day cells; a picture sits on the page like a
picture calendar's photograph; the closing page lies among the pages torn off. Every page PLANS its words first
(vl_native2.flow / stack: measured, never under a floor), draws the block around them, then sets them. The only words
it writes itself are the day numerals of the points page's cells (1 2 3 4, the manifest's derived words)."""
from __future__ import annotations

import math
import random

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "calendar"
_LAYER = "the calendar block's paper layers sit on each other (a leaf under the page, a stub over it, the header " \
         "over the pad) by design"


def _art(sh, why, *, layered=True):
    """Declare a drawn piece of the calendar: decorative (it carries no words), layered on purpose."""
    if sh is None:
        return None
    dk.decorative(sh, why)
    if layered:
        dk.overlap_intent(sh, _LAYER)
    return sh


# ─────────────────────────────────────────── the block ───────────────────────────────────────────
def _leaves(slide, page):
    """How many leaves still show under the current page: eight on the first pages, one fewer every two pages, never
    under two — and one on the closing page, the last of the pad."""
    if page == "closing":
        return 1
    return max(2, 8 - (_v2.page_no(slide) - 1) // 2)


def _stub_count(slide, page):
    """How many torn stubs hang under the header: one on the cover, more as the pages go, four on the closing page."""
    if page == "cover":
        return 1
    if page == "closing":
        return 4
    return max(1, min(4, 1 + (_v2.page_no(slide) - 1) // 3))


def _geom(k, rect, *, leaves, stubs, top_pad=None, bot_pad=0.38):
    """Where the parts of a block at `rect` (x, y, w, h — the header's top to the deepest leaf's foot) go, before
    anything is drawn: the header's height, the current page, the leaf step and the writable rect inside the page
    (`bot_pad` × s of paper kept under the words)."""
    W, H, s, o = ctx(k)
    x, y, w, h = rect
    hh = max(0.40 * s, min(0.58 * s, 0.09 * h))
    over = 0.07 * s                                    # the header board is a little wider than the pad
    dy = 0.032 * s                                     # one leaf's edge under the next
    px, pw = x + over, w - 2 * over
    py = y + hh - 0.03 * s                             # the pad is glued just under the header's lip
    ph = h - hh - leaves * dy + 0.03 * s
    sd = 0.30 * s if stubs else 0.0                    # the deepest a torn stub reaches
    mx = 0.42 * s
    tp = (sd + 0.24 * s) if top_pad is None else top_pad
    top = py + 0.03 * s + tp
    bot = py + ph - bot_pad * s
    return {"rect": rect, "hh": hh, "dy": dy, "leaves": leaves, "stubs": stubs, "sd": sd,
            "page": (px, py, pw, ph), "inner": (px + mx, top, pw - 2 * mx, bot - top)}


def _torn_edge(rnd, x0, x1, y_left, y_right, s, *, amp=0.022, step=0.055):
    """The points of a ripped paper edge from x1 back to x0: a slant from y_left to y_right, a slow wander and a fine
    jag of fibres."""
    n = max(8, int((x1 - x0) / (step * s)))
    ph1, ph2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
    f1 = rnd.uniform(1.2, 2.4)
    pts = []
    for i in range(n + 1):
        t = 1.0 - i / n
        xx = x0 + (x1 - x0) * t
        if 0 < i < n:
            xx += rnd.uniform(-0.25, 0.25) * step * s
        yy = y_left + (y_right - y_left) * t
        yy += 0.035 * s * math.sin(ph1 + t * f1 * 6.28) + 0.015 * s * math.sin(ph2 + t * 13.0)
        yy += rnd.uniform(-amp, amp) * s
        pts.append((xx, yy))
    return pts


def _stubs(k, slide, g, seed):
    """The torn stubs of the pages already gone, hanging from the header over the current page; the oldest (deepest
    tear) behind, the most recent in front."""
    W, H, s, o = ctx(k)
    px, py, pw, ph = g["page"]
    rnd = random.Random(seed)
    top = py + 0.02 * s
    depths = []
    for i in range(g["stubs"]):
        a = rnd.uniform(0.12, 0.27) * s
        b = rnd.uniform(0.10, 0.25) * s
        depths.append((max(a, b), a, b))
    depths.sort(reverse=True)
    for i, (_m, a, b) in enumerate(depths):
        pts = [(px, top), (px + pw, top)] + _torn_edge(rnd, px, px + pw, top + a, top + b, s)
        sh = na.poly(slide, pts, fill=k.P["stub"], line=k.P["stub_line"], line_w=0.5)
        if sh is not None:
            _art(sh, "a torn stub of a page already torn off the calendar: a day gone by, nothing to read")
            na.soft_shadow(sh, blur=0.035, dist=0.014, alpha=0.22, color=k.P["shadow"])


def _rings(k, slide, g):
    """Two metal binder rings: each a punched slot in the header and a loop of wire rising over its top edge, drawn as
    its dark edge, its body and a line of light."""
    W, H, s, o = ctx(k)
    x, y, w, h = g["rect"]
    hh = g["hh"]
    hole_y = y + hh * 0.50
    rise = 0.24 * s
    r = 0.072 * s
    holes, loops = [], []
    for f in (0.24, 0.76):
        cx = x + w * f
        holes.append([(cx + 0.135 * s * math.cos(2 * math.pi * i / 24),
                       hole_y + 0.072 * s * math.sin(2 * math.pi * i / 24)) for i in range(24)])
        top = y - rise + r
        arc = [(cx + r * math.cos(math.pi + math.pi * i / 12), top + r * math.sin(math.pi + math.pi * i / 12))
               for i in range(13)]
        loops.append(([(cx - r, hole_y)] + arc + [(cx + r, hole_y)], cx, top))
    _art(na.multipoly(slide, holes, k.P["hole"]), "the punched slots the calendar's rings pass through")
    for lp, cx, top in loops:
        _art(na.polyline(slide, lp, k.P["ring_dark"], w=4.4 * s), "the shaded edge of a metal binder ring")
        _art(na.polyline(slide, lp, k.P["ring"], w=2.9 * s), "a metal binder ring holding the calendar pad")
        hi = [(cx - r - 0.006 * s, hole_y - 0.04 * s), (cx - r - 0.006 * s, top)] + \
             [(cx + (r + 0.006 * s) * math.cos(math.pi + math.pi * i / 12 * 0.55),
               top + (r + 0.006 * s) * math.sin(math.pi + math.pi * i / 12 * 0.55)) for i in range(1, 13)]
        _art(na.polyline(slide, hi, k.P["ring_hi"], w=0.9 * s, alpha=0.85), "light along a metal binder ring")


def _desk(k, slide):
    """Every page: the desk the calendar stands on — the long, faint grain of its wood, lines that run, cluster and
    fade; at night the warm pool of a desk lamp over it."""
    W, H, s, o = ctx(k)
    if vl.REGISTRY[NAME]["grounds"][k.ground]["dark"]:
        lamp = dk.box(slide, 0, 0, W, H, grad=[(0.0, k.P["lamp"], 0.12), (0.55, k.P["lamp"], 0.04),
                                               (1.0, k.P["lamp"], 0.0)], grad_radial=True)
        _art(lamp, "the warm pool of a desk lamp on the desk at night; light, nothing to read")
    rnd = random.Random(11)
    thin, bold = [], []
    y = rnd.uniform(0.10, 0.30) * s
    while y < H - 0.08 * s:
        amp, ph, fr = rnd.uniform(0.02, 0.08) * s, rnd.uniform(0, 6.28), rnd.uniform(0.30, 0.85)
        x0 = max(0.0, rnd.uniform(-0.6, 0.45) * W)
        x1 = min(W, x0 + rnd.uniform(0.40, 1.3) * W)
        n = max(4, int((x1 - x0) / (0.35 * s)))
        prev = None
        out = bold if rnd.random() < 0.28 else thin
        for i in range(n + 1):
            px = x0 + (x1 - x0) * i / n
            py = min(H - 0.03 * s, max(0.03 * s, y + amp * math.sin(ph + fr * px / s)
                                       + 0.25 * amp * math.sin(2.7 * ph + 3.1 * px / s)))
            if prev:
                out.append((prev, (px, py)))
            prev = (px, py)
        y += rnd.choice((0.06, 0.09, 0.12, 0.30, 0.45, 0.62)) * s
    _art(na.strokes(slide, thin, k.P["grain_line"], w=0.6, alpha=0.55),
         "the fine grain of the wooden desk under the calendar; texture, nothing to read")
    _art(na.strokes(slide, bold, k.P["grain_line"], w=1.3, alpha=0.45),
         "the darker grain lines of the wooden desk; texture, nothing to read")


vn.GROUNDS[NAME] = _desk


def _draw_block(k, slide, g, seed):
    """Draw the block at g: the leaves to come (deepest first), the current page, the torn stubs, the header and its
    rings."""
    W, H, s, o = ctx(k)
    x, y, w, h = g["rect"]
    px, py, pw, ph = g["page"]
    dy = g["dy"]
    for i in range(g["leaves"], 0, -1):
        b = dk.box(slide, px, py, pw, ph + i * dy, fill=k.P["leaf_a" if i % 2 else "leaf_b"],
                   line=dk._as_rgb(k.P["leaf_line"]), line_w=0.4)
        _art(b, "a leaf of the pad under the current page: its edge counts the pages still to come")
        if i == g["leaves"]:
            na.soft_shadow(b, blur=0.16, dist=0.06, alpha=0.30, color=k.P["shadow"])
    pg = dk.box(slide, px, py, pw, ph, fill=k.P["page"], line=dk._as_rgb(k.P["leaf_line"]), line_w=0.4)
    _art(pg, "the calendar's current page: the words printed on it carry the meaning")
    na.soft_shadow(pg, blur=0.03, dist=0.012, alpha=0.16, color=k.P["shadow"])
    if g["sd"] and g["inner"][1] - (py + 0.03 * s + g["sd"]) >= 0.14 * s:
        # the current page's own perforation, just under the stubs: where it will be torn off in its turn
        yp, d, step = py + 0.03 * s + g["sd"] + 0.03 * s, 0.022 * s, 0.080 * s
        n = int((pw - 0.24 * s) / step)
        x0 = px + (pw - n * step) / 2.0
        dots = [[(x0 + i * step + d * math.cos(2 * math.pi * j / 8), yp + d * math.sin(2 * math.pi * j / 8))
                 for j in range(8)] for i in range(n + 1)]
        _art(na.multipoly(slide, dots, k.P["leaf_line"], alpha=0.75),
             "the perforation across the top of the current page, where it tears off", layered=False)
    if g["stubs"]:
        _stubs(k, slide, g, seed)
    hh = g["hh"]
    hd = dk.box(slide, x, y, w, hh, fill=k.P["head"], round=True, corners="top", r=0.10 * s)
    _art(hd, "the calendar's header board the pad is bound to")
    na.soft_shadow(hd, blur=0.10, dist=0.035, alpha=0.30, color=k.P["shadow"])
    lip = dk.box(slide, x, y + hh - 0.075 * s, w, 0.075 * s, fill=k.P["head_lip"])
    _art(lip, "the binding strip along the header's lower edge")
    _art(na.strokes(slide, [((x + 0.12 * s, y + 0.06 * s), (x + w - 0.12 * s, y + 0.06 * s))], k.P["head_hi"], w=0.9),
         "light along the header board's top edge")
    _rings(k, slide, g)


def _rule(k, slide, x0, x1, y, *, color=None, w=1.1):
    _art(na.strokes(slide, [((x0, y), (x1, y))], color or k.P["date"], w=w),
         "a printed rule on the calendar page; it only divides the words", layered=False)


def _block_rect(k, land, port, *, top=0.42, foot=0.36):
    """The block's rect, centred: `land` / `port` = (fraction of W, least width in s) for a landscape / portrait or
    square canvas. The rings rise above the top; the desk shows round it."""
    W, H, s, o = ctx(k)
    fw, fs = land if o == "land" else port
    w = min(W - 0.9 * s, max(fw * W, fs * s))
    y = top * s
    return ((W - w) / 2.0, y, w, H - y - foot * s)


def _title_start(k, text, w, big):
    """The size a page's title starts at: `big` (pt, already scaled) when it sets in three lines or fewer across `w`,
    else the language's own title size — a long title at the big size broke into six ragged one-word lines on a
    portrait page."""
    W, H, s, o = ctx(k)
    base = vl.TYPE[NAME]["title"][0] * s
    if not text or big <= base:
        return big
    return big if len(vl._break_lines(k, "title", text, big, w * vl.HEADROOM - 0.06)) <= 3 else base


def _num_start(k, num, want, w):
    """The size the date numeral starts at: `want`, or less so that its ink is at most 86% of the column `w` — sized
    only by the word-fit loop, a figure as wide as the column was measured a line taller than it renders ("1,250" sat
    at the top of a box twice its height)."""
    W, H, s, o = ctx(k)
    if not num:
        return want
    iw = _v2.ink_w(k, "number", num, want)
    z = want * min(1.0, 0.86 * w / iw) if iw > 0 else want
    return max(vl.TYPE[NAME]["number"][5] * s, z)


def _mixcol(f, names, x, w, *, center=False):
    """The column (x, w) for words that mix Chinese/Japanese with Latin letters or digits ("用 GPT-5 做 3 件事"): 8%
    narrower (and re-centred). Measured to fit one line in a 3.96in column (3.67in of 3.79in), the section title
    rendered its last character alone on a second line (10in 16:9 sample, 2026-10-22) — the core's line width
    reads such a run narrower than the renderer sets it. Pure Latin or pure CJK copy keeps the full column."""
    import re as _re
    if any(dk._has_cjk(t) and _re.search(r"[A-Za-z0-9]", t) for t in (text_of(f, n) for n in names) if t):
        return (x + 0.04 * w if center else x), 0.92 * w
    return x, w


def _seed(slide, f):
    return "{}|{}".format(_v2.page_no(slide), "|".join(str(v) for v in f.values() if isinstance(v, str)))


def _kicker_top(k, slide, page, f, inner, *, align="c"):
    """PLAN the kicker at the top of the page, printed where a calendar prints its month, a short red rule under it.
    Returns (rects, draws, the y the rest starts at, a draw for the rule)."""
    W, H, s, o = ctx(k)
    ix, iy, iw, ih = inner
    kick = text_of(f, "kicker")
    if not kick:
        return {}, [], iy, (lambda: None)
    kr, kd = _v2.flow(k, slide, page, (ix, iy, iw, max(0.4 * s, ih * 0.34)), [("kicker", _v2.caps(kick))],
                      anchor="top", align=align, accent=k.P["date"])
    kx, ky, kw, khh = kr["kicker"]
    ry = ky + khh + 0.16 * s
    half = min(0.45 * s, iw / 4.0)
    cx = ix + iw / 2.0 if align == "c" else ix + half
    x0 = cx - half if align == "c" else ix

    def rule():
        _rule(k, slide, x0, x0 + 2 * half, ry)
    return kr, [kd], ry + 0.30 * s, rule


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=2)
def _cal_cover(k, slide, f, image):
    """The calendar block on the desk, a fresh pad (one torn stub): the kicker printed where the month goes, the title
    in the middle of the current page, the subtitle under it."""
    W, H, s, o = ctx(k)
    rect = _block_rect(k, ((0.47, 6.2), (0.62, 7.8))[alt()], ((0.84, 0), (0.92, 0))[alt()])
    g = _geom(k, rect, leaves=_leaves(slide, "cover"), stubs=_stub_count(slide, "cover"))
    ix, iy, iw, ih = g["inner"]
    r, ds, y0, rule = _kicker_top(k, slide, "cover", f, g["inner"])
    cx_, cw_ = _mixcol(f, ("title", "subtitle"), ix, iw, center=True)
    tr, tds = _v2.stack(k, slide, "cover", cx_, cw_, y0, iy + ih,
                        [(_v2.fields(f, ("title",)), 0.22 * s), (_v2.fields(f, ("subtitle",)), 0.0)],
                        anchor="middle", align="c",
                        start={"title": _title_start(k, text_of(f, "title"), cw_, (60 if alt() == 0 else 40) * s)})
    r.update(tr)
    _draw_block(k, slide, g, _seed(slide, f))
    rule()
    _run_all(ds + tds)
    return r


@register(NAME, "section", alts=2)
def _cal_section(k, slide, f, image):
    """A fresh page: the section number printed as the giant date numeral in Sunday red, the kicker where the month
    goes, the title under the numeral where a calendar prints the day's name."""
    W, H, s, o = ctx(k)
    rect = _block_rect(k, ((0.47, 6.2), (0.62, 7.8))[alt()], ((0.84, 0), (0.92, 0))[alt()])
    g = _geom(k, rect, leaves=_leaves(slide, "section"), stubs=_stub_count(slide, "section"))
    ix, iy, iw, ih = g["inner"]
    r, ds, y0, rule = _kicker_top(k, slide, "section", f, g["inner"])
    num = text_of(f, "number")
    cx_, cw_ = _mixcol(f, ("title",), ix, iw, center=True)
    tr, tds = _v2.stack(k, slide, "section", cx_, cw_, y0, iy + ih,
                        [([("number", num)] if num else [], 0.10 * s), (_v2.fields(f, ("title",)), 0.0)],
                        anchor="middle", align="c", accent=k.P["date"],
                        start={"number": _num_start(k, num, (300 if alt() == 0 else 220) * s, iw), "title": 42 * s})
    r.update(tr)
    _draw_block(k, slide, g, _seed(slide, f))
    rule()
    _run_all(ds + tds)
    return r


@register(NAME, "image_text", alts=3)
def _cal_image_text(k, slide, f, image):
    """A picture calendar's page: on a portrait or square page the caller's photograph printed across the top with the
    paper's margin round it, the caption under it, then the kicker, the title and the body; on a landscape page (a desk
    calendar laid on its side) the photograph down the page's left half, its caption under it, the words beside it."""
    W, H, s, o = ctx(k)
    side = o == "land"
    rect = _block_rect(k, ((0.78, 9.4), (0.86, 10.4), (0.92, 11.0))[alt()], ((0.86, 0), (0.90, 0), (0.92, 0))[alt()])
    g = _geom(k, rect, leaves=_leaves(slide, "image_text"), stubs=_stub_count(slide, "image_text"))
    ix, iy, iw, ih = g["inner"]
    cap = text_of(f, "caption")
    r, ds = {}, []
    if side:
        pw_ = iw * (0.50, 0.44, 0.38)[alt()]
        ch = 0.0
        if cap:
            cr, cd = _v2.flow(k, slide, "image_text", (ix, iy, pw_, 0.9 * s), [("caption", cap)], anchor="top")
            ch = cr["caption"][3] + 0.10 * s
        img = (ix, iy, pw_, ih - ch)
        if cap:
            cr, cd = _v2.flow(k, slide, "image_text", (ix, iy + ih - ch + 0.10 * s, pw_, ch), [("caption", cap)],
                              anchor="top")
            r.update(cr)
            ds.append(cd)
        tx = ix + pw_ + 0.50 * s
        col = (tx, iy, ix + iw - tx)
    else:
        frac = ((0.50, 0.42, 0.34) if o == "land" else (0.46, 0.38, 0.30))[alt()]
        img = (ix, iy, iw, ih * frac)
        foot = img[1] + img[3]
        if cap:
            cr, cd = _v2.flow(k, slide, "image_text", (ix, foot + 0.10 * s, iw, 0.9 * s), [("caption", cap)],
                              anchor="top")
            r.update(cr)
            ds.append(cd)
            foot = cr["caption"][1] + cr["caption"][3]
        col = (ix, foot + 0.28 * s, iw)
    cx_, cw_ = _mixcol(f, ("kicker", "title", "body"), col[0], col[2])
    tr, tds = _v2.stack(k, slide, "image_text", cx_, cw_, col[1], iy + ih,
                        [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.14 * s),
                         (_v2.fields(f, ("body",)), 0.0)], anchor="middle", accent=k.P["date"],
                        start=None if alt() < 2 else {"title": 28 * s})
    r.update(tr)
    _draw_block(k, slide, g, _seed(slide, f))
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(ds + tds)
    return r


def _points_head(k, slide, f, g, frac):
    """PLAN the kicker and the title at the head of the planner's page, in the top `frac` of the writable rect; the
    roomier layouts start the title near its floor so the cells keep their height."""
    W, H, s, o = ctx(k)
    ix, iy, iw, ih = g["inner"]
    cx_, cw_ = _mixcol(f, ("kicker", "title"), ix, iw)
    r, ds = _v2.stack(k, slide, "points", cx_, cw_, iy, iy + ih * frac,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.06 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", accent=k.P["date"],
                      start=None if alt() == 0 else {"title": (32, 24)[alt() > 1] * s})
    return r, ds, max((v[1] + v[3] for v in r.values()), default=iy)


def _cells_land(k, slide, f, g, pts):
    """The week strip: one day cell per point side by side under the title, each its day numeral (1 2 3 4) in red
    under a rule, then the head and the line; hairlines between the cells end at the longest cell's words. The strip is
    set at the optical centre of the room the title leaves."""
    W, H, s, o = ctx(k)
    ix, iy, iw, ih = g["inner"]
    n = len(pts)
    r, ds, foot = _points_head(k, slide, f, g, 0.34 if alt() == 0 else 0.40)
    top = foot + 0.34 * s
    bottom = iy + ih
    gap = 0.34 * s
    cw = (iw - (n - 1) * gap) / n
    items = [[("item_no", str(i + 1)), ("item_head", hd)] + ([("item_line", ln)] if ln else [])
             for i, (hd, ln) in enumerate(pts)]
    room = bottom - top - 0.16 * s
    if room < 1.0 * s:
        raise vl.VLTextOverflow("calendar.points(): the title leaves the day cells {:.2f}in — trying a roomier "
                                "layout".format(room))
    kw = {"anchor": "top", "accent": k.P["date"]}
    st = {"item_no": (78 if alt() == 0 else 64) * s}
    probe = _v2.plan_together(k, slide, "points", [((0, 0, cw, room), it, dict(kw, start=st)) for it in items])
    sizes = dict(st, **{f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()})
    used = max(max(v[1] + v[3] for v in pr.values()) for pr, _d in probe) + 0.16 * s
    top += max(0.0, (bottom - top - used) * 0.38)
    planned = _v2.plan_together(k, slide, "points", [((ix + i * (cw + gap), top + 0.16 * s, cw, room), it,
                                                      dict(kw, start=sizes)) for i, it in enumerate(items)])
    low = top
    for i, (pr, pd) in enumerate(planned):
        low = max(low, max(v[1] + v[3] for v in pr.values()))
        ds.append(pd)
        for f_, v in pr.items():
            r["{}_{}".format(f_, i + 1)] = v

    def art():
        for i in range(n):
            cx = ix + i * (cw + gap)
            _rule(k, slide, cx, cx + cw, top, color=k.P["ink"], w=1.2)
        if n > 1:
            segs = [((ix + i * (cw + gap) - gap / 2.0, top + 0.16 * s), (ix + i * (cw + gap) - gap / 2.0, low))
                    for i in range(1, n)]
            for sg in segs:            # one shape each: a shape spanning them all read as a card round the cells
                _art(na.strokes(slide, [sg], k.P["leaf_line"], w=0.6),
                     "a hairline between two day cells of the week strip", layered=False)
    return r, ds, art


def _cells_port(k, slide, f, g, pts):
    """The week strip stood on end (a portrait or square page, or long copy): one equal row per point down the page,
    its day numeral in red at the left, the head and the line beside it, a hairline above each row."""
    W, H, s, o = ctx(k)
    ix, iy, iw, ih = g["inner"]
    n = len(pts)
    r, ds, foot = _points_head(k, slide, f, g, (0.36, 0.34, 0.46)[alt()])
    top = foot + (0.30 if alt() < 2 else 0.16) * s
    bottom = iy + ih
    gap = (0.20 if alt() < 2 else 0.10) * s
    lw = min((1.05 if alt() < 2 else 0.72) * s, 0.22 * iw)
    avail = bottom - top - (n - 1) * gap
    eq = avail / n
    if eq < 0.42 * s:
        raise vl.VLTextOverflow("calendar.points(): the title leaves each day row {:.2f}in — trying a roomier "
                                "layout".format(eq))
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    tall = eq >= 1.6 * s                          # a tall page's rows: the heads and lines set a size up
    kw0 = {"anchor": "top", "start": {"item_head": 25 * s, "item_line": 17 * s}} if tall else {"anchor": "top"}
    pad_t = (0.04 if alt() < 2 else 0.02) * s     # paper between a row's hairline and its words
    probe = _v2.plan_together(k, slide, "points", [((0, 0, iw - lw, eq - pad_t - (0.08 * s if alt() < 2 else 0.0)),
                                                    it, kw0) for it in items])
    sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
    natural = max(max(v[1] + v[3] for v in pr.values()) for pr, _d in probe)
    no_size = max(vl.TYPE[NAME]["item_no"][5] * s,
                  min(1.7 * vl.TYPE[NAME]["item_no"][0] * s, (min(eq, 1.9 * s) - 0.12 * s) * 72 / 1.25,
                      (lw - 0.22 * s) * 72 / 0.55))
    # the head drops so its cap line meets the numeral's: a big figure's digits start lower in their line than a
    # small head's capitals (TNR / Didot ascent minus digit height, about 0.23 em) — never more than the row can give
    off = max(0.0, 0.23 * (no_size - sizes.get("item_head", no_size)) / 72.0)
    off = max(0.0, min(off, eq - natural - pad_t - 0.02 * s))
    # equal day rows down the page, as a planner rules them: each as tall as the room allows, up to 2.4in a row
    rh = min(eq, max(natural + off + pad_t + 0.02 * s, no_size / 72.0 * 1.25 + 0.12 * s, min(eq, 2.4 * s)))
    block = n * rh + (n - 1) * gap
    y = top + max(0.0, (bottom - top - block) * 0.40)
    ys = [y + i * (rh + gap) for i in range(n)]
    planned = _v2.plan_together(k, slide, "points", [((ix + lw, yy + pad_t + off, iw - lw, rh - pad_t - off),
                                                      it, {"anchor": "top", "start": sizes})
                                                     for yy, it in zip(ys, items)])
    for i, ((pr, pd), yy) in enumerate(zip(planned, ys)):
        for f_, v in pr.items():
            r["{}_{}".format(f_, i + 1)] = v
        ds.append(pd)
        nr, nd = _v2.flow(k, slide, "points", (ix, yy + pad_t, lw - 0.10 * s, rh - pad_t),
                          [("item_no", str(i + 1))], anchor="top", align="l", accent=k.P["date"],
                          start={"item_no": no_size})
        r["item_no_{}".format(i + 1)] = nr["item_no"]
        ds.append(nd)

    def art():
        foot = [ys[-1] + rh] if rh - pad_t - off - natural >= 0.14 * s else []   # a closing rule only with air above
        for yy in ys + foot:            # one shape each: a shape spanning them all read as a card round the rows
            _art(na.strokes(slide, [((ix, yy), (ix + iw, yy))], k.P["leaf_line"], w=0.7),
                 "a hairline ruling the day rows", layered=False)
    return r, ds, art


@register(NAME, "points", alts=3)
def _cal_points(k, slide, f, image):
    """A week planner's page: the kicker and the title at its head, then one day cell per point — its day numeral
    (1 2 3 4) in red, the head and the line — side by side on a landscape page, one row each on a portrait or square
    page (and on the last landscape layout, for long copy)."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    wide = o == "land" and alt() < 2
    last = alt() == 2              # the last layout gives the rows the block's spare paper above and below them
    rect = _block_rect(k, ((0.86, 9.6), (0.92, 10.0), (0.90, 9.6))[alt()], ((0.88, 0), (0.92, 0), (0.94, 0))[alt()],
                       **({"top": 0.38, "foot": 0.26} if last else {}))
    g = _geom(k, rect, leaves=_leaves(slide, "points"), stubs=_stub_count(slide, "points"),
              top_pad=0.30 * s + 0.10 * s if last else None, bot_pad=0.24 if last else 0.38)
    r, ds, art = (_cells_land if wide else _cells_port)(k, slide, f, g, pts)
    _draw_block(k, slide, g, _seed(slide, f))
    art()
    _run_all(ds)
    return r


@register(NAME, "quote", alts=2)
def _cal_quote(k, slide, f, image):
    """A quote-a-day page: a large red quote mark, the quote in italic serif, a short red rule and the attribution."""
    W, H, s, o = ctx(k)
    rect = _block_rect(k, ((0.56, 7.2), (0.68, 8.6))[alt()], ((0.86, 0), (0.92, 0))[alt()])
    g = _geom(k, rect, leaves=_leaves(slide, "quote"), stubs=_stub_count(slide, "quote"))
    ix, iy, iw, ih = g["inner"]
    a = text_of(f, "attribution")
    groups = [([("mark", "“")] + _v2.fields(f, ("quote",)), 0.42 * s if a else 0.0),
              (_v2.fields(f, ("attribution",)), 0.0)]
    cx_, cw_ = _mixcol(f, ("quote", "attribution"), ix, iw)
    r, ds = _v2.stack(k, slide, "quote", cx_, cw_, iy, iy + ih, groups, anchor="middle", accent=k.P["date"])
    _draw_block(k, slide, g, _seed(slide, f))
    if a and "attribution" in r:
        ax, ay, aw, ah = r["attribution"]
        _rule(k, slide, ix + 0.04 * s, ix + 0.04 * s + min(0.9 * s, iw / 4.0), ay - 0.21 * s)
    _run_all(ds)
    return r


@register(NAME, "data", alts=2)
def _cal_data(k, slide, f, image):
    """A day planner's page: the caller's number as the giant red date at the left, a hairline, its label and note at
    the right (on a portrait or square page: the number above, the label and the note under a rule)."""
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    words = _v2.fields(f, ("label", "note"))
    rect = _block_rect(k, ((0.70, 8.6), (0.80, 9.6))[alt()], ((0.86, 0), (0.92, 0))[alt()])
    g = _geom(k, rect, leaves=_leaves(slide, "data"), stubs=_stub_count(slide, "data"))
    ix, iy, iw, ih = g["inner"]
    rects, draws = {}, []
    if o == "land":
        # the date's column: half the page, a little more for a long figure ("1,250,000"), less on the roomier layout
        lw = iw * ((0.56 if num and len(num) >= 5 else 0.50) - (0.06 if alt() else 0.0)) if words else iw
        gap = 0.70 * s
        if num:
            nr, nd = _v2.flow(k, slide, "data", (ix, iy, lw, ih), [("number", num)], anchor="middle", align="c",
                              accent=k.P["date"],
                              start={"number": _num_start(k, num, (300 if alt() == 0 else 240) * s, lw)})
            rects.update(nr)
            draws.append(nd)
        rr = {}
        if words:
            rx = ix + lw + gap if num else ix
            rw = ix + iw - rx
            rx, rw = _mixcol(f, ("label", "note"), rx, rw)
            rr, rd = _v2.flow(k, slide, "data", (rx, iy, rw, ih), words, anchor="middle")
            rects.update(rr)
            draws.append(rd)

        def art():
            if num and words:
                lo = min(v[1] for v in rr.values())
                hi = max(v[1] + v[3] for v in rr.values())
                xm = ix + lw + gap / 2.0
                _art(na.strokes(slide, [((xm, lo), (xm, hi))], k.P["leaf_line"], w=0.8),
                     "the hairline between the date and its words", layered=False)
    else:
        groups = [([("number", num)] if num else [], 0.36 * s if words else 0.0), (words, 0.0)]
        cx_, cw_ = _mixcol(f, ("label", "note"), ix, iw, center=True)
        rects, draws = _v2.stack(k, slide, "data", cx_, cw_, iy, iy + ih, groups, anchor="middle", align="c",
                                 accent=k.P["date"],
                                 start={"number": _num_start(k, num, (300 if alt() == 0 else 220) * s, cw_)})

        def art():
            if num and words and "number" in rects:
                nx, ny, nw, nh = rects["number"]
                first = min(rects[f_][1] for f_, _t in words if f_ in rects)
                yr = first - 0.18 * s
                half = min(0.55 * s, iw / 4.0)
                _rule(k, slide, ix + iw / 2.0 - half, ix + iw / 2.0 + half, yr)
    _draw_block(k, slide, g, _seed(slide, f))
    art()
    _run_all(draws)
    return rects


def _torn_sheet(k, slide, cx, cy, w, h, deg, seed):
    """A page torn off the pad lying on the desk: its torn top edge, face down (a day gone by)."""
    W, H, s, o = ctx(k)
    rnd = random.Random(seed)
    x0, y0 = -w / 2.0, -h / 2.0
    pts = [(x0, y0 + h), (x0 + w, y0 + h)] + _torn_edge(rnd, x0, x0 + w, y0 + 0.05 * s, y0 + 0.02 * s, s)
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in pts]
    sh = na.poly(slide, pts, fill=k.P["leaf_a"], line=k.P["leaf_line"], line_w=0.5)
    if sh is not None:
        _art(sh, "a page torn off the calendar lying on the desk: the days already gone")
        na.soft_shadow(sh, blur=0.08, dist=0.03, alpha=0.24, color=k.P["shadow"])
    return pts


@register(NAME, "closing", alts=2)
def _cal_closing(k, slide, f, image):
    """The last page of the pad: the stack thinned to one leaf, the stubs of the pages gone under the header, the
    title and its line on the page; on a landscape page the torn-off pages lie on the desk at either side."""
    W, H, s, o = ctx(k)
    rect = _block_rect(k, ((0.47, 6.2), (0.62, 7.8))[alt()], ((0.84, 0), (0.92, 0))[alt()])
    g = _geom(k, rect, leaves=_leaves(slide, "closing"), stubs=_stub_count(slide, "closing"))
    ix, iy, iw, ih = g["inner"]
    cx_, cw_ = _mixcol(f, ("title", "line"), ix, iw, center=True)
    r, ds = _v2.stack(k, slide, "closing", cx_, cw_, iy, iy + ih,
                      [(_v2.fields(f, ("title",)), 0.26 * s), (_v2.fields(f, ("line",)), 0.0)], anchor="middle",
                      align="c",
                      start={"title": _title_start(k, text_of(f, "title"), cw_, (58 if alt() == 0 else 34) * s)})
    x, y, w, h = rect
    if o == "land" and x > 2.4 * s:
        px, py, pw, ph = g["page"]
        m = 0.14 * s
        # two pages already torn off, face down on the desk, tucked under the block at either side — one larger and
        # lower at the left, one smaller at the right; each kept whole on the page
        for (fw, fh, fx, fy, deg, sd) in ((0.62, 0.50, -0.30, 0.68, -11.0, 1), (0.48, 0.42, 0.24, 0.80, 6.5, 2)):
            sw, sh_ = min(pw * fw, x * 1.5), min(ph * fh, x * 1.5 * fh / fw)
            cx = (x + fx * sw) if fx < 0 else (x + w + fx * sw)
            half = 0.5 * math.hypot(sw, sh_)
            cx = min(max(cx, m + half), W - m - half)
            cy = min(max(y + h * fy, m + half), H - m - half)
            _torn_sheet(k, slide, cx, cy, sw, sh_, deg, "{}-{}".format(_seed(slide, f), sd))
    _draw_block(k, slide, g, _seed(slide, f))
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_calendar(slide, role, index):
    """An ordinary page (a chart, an agenda) printed on the calendar's current page: the block drawn over the slide, the
    content rect inside the page, in REFERENCE inches."""
    k = _v2.kit_for(NAME, slide)
    W, H, s, o = ctx(k)
    rect = (0.42 * s, 0.40 * s, W - 0.84 * s, H - 0.40 * s - 0.34 * s)
    g = _geom(k, rect, leaves=3, stubs=1, top_pad=0.30 * s + 0.18 * s)
    _draw_block(k, slide, g, "ordinary-{}".format(index))
    return vl._as_reference(g["inner"])


_card_calendar = vl._card_for(NAME)
