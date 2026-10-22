"""herbarium — the Herbarium plate language (标本图鉴): its ground painter, its card and its seven pages.

An archival specimen sheet: a hairline double frame, pressed sprigs drawn as native shapes and held to the sheet by
paper tape, typewritten label cards, a numbered plate. Every page PLANS its words first (vl_native2.flow / stack:
measured, never under a floor), draws its art clear of them, then sets them. The only words it writes itself are the
manifest's derived words: the plate number (PL. 4 / 图版 4) and the point labels (No. 1 / 第 1 号)."""
from __future__ import annotations

import math
import random

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "herbarium"
def _lang(k, f, *texts):
    words = [t for t in texts if t] or [v for v in (f or {}).values() if isinstance(v, str)]
    return _v2.lang_of(*words, k=k, f=f)


# ─────────────────────────────────────────── the sheet ───────────────────────────────────────────
def _frame(k, slide):
    """Every page: the plate's hairline double frame."""
    W, H, s, o = ctx(k)
    for inset, w in ((0.26 * s, 0.9), (0.33 * s, 0.45)):
        b = dk.box(slide, inset, inset, W - 2 * inset, H - 2 * inset, fill=None, line=dk._as_rgb(k.P["frame"]),
                   line_w=w)
        dk.decorative(b, "the plate's hairline double frame — the border of the specimen sheet")


vn.GROUNDS[NAME] = _frame


def _plate(k, slide, f, *texts):
    """The plate number at the top right, inside the frame: PL. 4 (图版 4 / 図版 4) — the page's own number."""
    W, H, s, o = ctx(k)
    n = _v2.page_no(slide)
    lang = _lang(k, f, *texts)
    txt = {"zh": "图版 {}", "ja": "図版 {}"}.get(lang, "PL. {}").format(n)
    size = vl.TYPE[NAME]["plate"][0] * s
    w, h = 2.2 * s, 0.34 * s
    x, y = W - 0.33 * s - 0.20 * s - w, 0.33 * s + 0.08 * s
    tb = dk.text(slide, x, y, w, h, [k.runs(txt, size, k.color("mute"), False, "type")], align=dk.PP_ALIGN.RIGHT)
    dk.decorative(tb, "the plate number: this page's own number, as a specimen plate is numbered")
    return (x, y, w, h)


# ─────────────────────────────────────────── the specimen ───────────────────────────────────────────
_PROFILE = {        # half-width along the midrib, t = 0 at the base, 1 at the tip
    "ovate": lambda t: math.sin(math.pi * t) ** 0.80 * (1.0 - 0.22 * t),
    "lance": lambda t: math.sin(math.pi * t) ** 1.15 * (1.0 - 0.30 * t),
    "round": lambda t: math.sin(math.pi * t) ** 0.55 * (1.0 - 0.10 * t),
}
_WIDTH = {"ovate": 0.50, "lance": 0.26, "round": 0.78}


def _blade(bx, by, ang, L, shape):
    """The outline of a leaf's blade from its base along `ang` (radians, screen y down)."""
    ca, sa = math.cos(ang), math.sin(ang)
    prof, wd = _PROFILE[shape], L * _WIDTH[shape]
    right, left = [], []
    for i in range(17):
        t = i / 16.0
        d, hw = L * t, wd / 2.0 * prof(t)
        px, py = bx + ca * d, by + sa * d
        right.append((px - sa * hw, py + ca * hw))
        left.append((px + sa * hw, py - ca * hw))
    return right + left[::-1]


def _leaf(k, slide, bx, by, ang, L, shape, fill):
    """One pressed leaf from its base along `ang` (radians, screen y down): its blade, then its midrib and veins."""
    ca, sa = math.cos(ang), math.sin(ang)
    prof, wd = _PROFILE[shape], L * _WIDTH[shape]
    blade = na.poly(slide, _blade(bx, by, ang, L, shape), fill=fill)
    if blade is not None:
        dk.decorative(blade, "a pressed leaf of the specimen — ornament, nothing to read")
    if L < 0.35:
        return
    segs = [((bx, by), (bx + ca * L * 0.94, by + sa * L * 0.94))]
    for t in (0.30, 0.50, 0.68):
        mx, my = bx + ca * L * t, by + sa * L * t
        reach = L * (t + 0.13)
        hw = wd / 2.0 * prof(min(0.99, t + 0.13)) * 0.82
        for side in (1, -1):
            ex = bx + ca * reach - side * sa * hw
            ey = by + sa * reach + side * ca * hw
            segs.append(((mx, my), (ex, ey)))
    vein = na.strokes(slide, segs, k.P["leaf_dark"] if fill != k.P["leaf_dark"] else k.P["stem"], w=0.5, alpha=0.6)
    if vein is not None:
        dk.decorative(vein, "the midrib and veins of a drawn leaf; ornament, nothing to read in them")


def _bezier(p0, c, p1, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def _tangent(p0, c, p1, t):
    dx = 2 * (1 - t) * (c[0] - p0[0]) + 2 * t * (p1[0] - c[0])
    dy = 2 * (1 - t) * (c[1] - p0[1]) + 2 * t * (p1[1] - c[1])
    return math.atan2(dy, dx)


def _sprig_plan(base, tip, bend, leaves, shape, seed, leaf_scale):
    """Where a sprig's parts go, before anything is drawn: (control point, stem length, the leaves as
    (x, y, angle, length, shape, fill index), the random stream left for the tapes). The same numbers every call."""
    rnd = random.Random(seed)
    (x0, y0), (x1, y1) = base, tip
    L = max(0.1, math.hypot(x1 - x0, y1 - y0))
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    c = ((x0 + x1) / 2.0 + nx * bend * L, (y0 + y1) / 2.0 + ny * bend * L)
    out = []
    if shape == "fern":                       # a fern frond: many narrow pinnae, longest near the base
        for j in range(11):
            t = 0.10 + 0.86 * j / 10.0
            px, py = _bezier(base, c, tip, t)
            ta = _tangent(base, c, tip, t)
            for side in (1, -1):
                out.append((px, py, ta + side * 1.05, None, "lance", 0 if (j + (side > 0)) % 3 else 1, t))
        return c, L, out, rnd
    for j in range(leaves):
        t = 0.14 + 0.74 * j / max(1, leaves - 1)
        px, py = _bezier(base, c, tip, t)
        side = 1 if j % 2 == 0 else -1
        a = _tangent(base, c, tip, t) + side * rnd.uniform(0.62, 0.92)
        ll = L * 0.30 * (1.0 - 0.45 * t) * leaf_scale * rnd.uniform(0.9, 1.08)
        out.append((px, py, a, ll, shape, (j + seed) % 4, t))
    out.append((tip[0], tip[1], _tangent(base, c, tip, 1.0), L * 0.17 * leaf_scale, shape, -1, 1.0))
    return c, L, out, rnd


def _sprig_extent(k, base, tip, bend, leaves, shape, seed, leaf_scale):
    """The box (x0, y0, x1, y1) a sprig's stem and blades cover."""
    W, H, s, o = ctx(k)
    c, L, parts, _r = _sprig_plan(base, tip, bend, leaves, shape, seed, leaf_scale)
    pts = [_bezier(base, c, tip, i / 24.0) for i in range(25)]
    for px, py, a, ll, sh, _fi, t in parts:
        pts += _blade(px, py, a, ll if ll is not None else L * 0.26 * (1.0 - 0.75 * t) + 0.08 * s, sh)
    xs, ys = [p_[0] for p_ in pts], [p_[1] for p_ in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _sprig(k, slide, base, tip, *, bend=0.12, leaves=7, shape="ovate", seed=1, leaf_scale=1.0, tapes=(0.18,)):
    """A pressed sprig: a gently curved stem from `base` to `tip`, leaves alternating up it (smaller toward the tip),
    a terminal leaf, and paper tape across the stem at each fraction in `tapes`. Deterministic for a seed.
    A specimen is mounted INSIDE the plate's frame: a sprig whose leaves would cross it is drawn shorter, toward its
    base, until it fits (a leaf past the frame was a hard OVERLAP in the delivery lint, 2026-10-22)."""
    W, H, s, o = ctx(k)
    lo = 0.33 * s + 0.10 * s
    for _i in range(40):
        ex0, ey0, ex1, ey1 = _sprig_extent(k, base, tip, bend, leaves, shape, seed, leaf_scale)
        if ex0 >= lo and ey0 >= lo and ex1 <= W - lo and ey1 <= H - lo:
            break
        tip = (base[0] + (tip[0] - base[0]) * 0.95, base[1] + (tip[1] - base[1]) * 0.95)
    c, L, parts, rnd = _sprig_plan(base, tip, bend, leaves, shape, seed, leaf_scale)
    stem = na.polyline(slide, [_bezier(base, c, tip, i / 24.0) for i in range(25)], k.P["stem"],
                       w=(1.2 if shape == "fern" else 1.5) * s)
    dk.decorative(stem, "the rachis of a drawn fern frond; ornament, nothing to read in it" if shape == "fern"
                  else "the stem of a drawn pressed sprig; ornament, nothing to read in it")
    if shape == "fern":
        for px, py, a, _ll, sh, fi, t in parts:
            _leaf(k, slide, px, py, a, L * 0.26 * (1.0 - 0.75 * t) + 0.08 * s, sh, (k.P["leaf"], k.P["leaf_dark"])[fi])
    else:
        fills = [k.P["leaf"], k.P["leaf_dark"], k.P["leaf"], k.P["leaf_dry"]]
        for px, py, a, ll, sh, fi, t in parts:
            _leaf(k, slide, px, py, a, ll, sh, k.P["leaf"] if fi < 0 else fills[fi])
    for t in tapes:
        px, py = _bezier(base, c, tip, t)
        _tape(k, slide, px, py, 0.70 * s, 0.20 * s, _tangent(base, c, tip, t) + math.pi / 2
              + rnd.uniform(*((-0.2, 0.2) if shape == "fern" else (-0.25, 0.25))))


def _tape(k, slide, cx, cy, w, h, ang):
    """A strip of paper tape centred on (cx, cy), its long side across `ang`."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(cx + ca * dx - sa * dy, cy + sa * dx + ca * dy) for dx, dy in
           ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    t = na.poly(slide, pts, fill=k.P["tape"], alpha=0.86, line=k.P["tape_edge"], line_w=0.4)
    if t is not None:
        dk.decorative(t, "paper tape holding the specimen to the sheet")
        dk.overlap_intent(t, "paper tape laid over the specimen it holds down: layered by design")


def _clear(rect, rects, pad=0.0):
    return not any(_v2.meet(rect, r, pad) for r in rects)


# ─────────────────────────────────────────── labels and tags ───────────────────────────────────────────
def _card(k, slide, page, rect, items, *, align="l", start=None):
    """PLAN a typewritten label card holding `items` in `rect` (x, y, w, max h); the card is cut to the words.
    Returns (rects, draw, card_rect)."""
    W, H, s, o = ctx(k)
    x, y, w, h = rect
    pad = 0.16 * s
    kw = {"anchor": "top", "align": align}
    if start:
        kw["start"] = start
    r, d = _v2.flow(k, slide, page, (x + pad, y + pad + 0.10 * s, w - 2 * pad, h - 2 * pad - 0.10 * s), items, **kw)
    foot = max((v[1] + v[3] for v in r.values()), default=y + pad) + pad
    card = (x, y, w, foot - y)

    def draw():
        b = dk.box(slide, x, y, w, foot - y, fill=k.P["panel"], line=dk._as_rgb(k.P["frame"]), line_w=0.6)
        dk.decorative(b, "the label card is the ground the typed words sit on; the words carry the meaning")
        for dy in (0.10 * s, 0.14 * s):
            dk.decorative(na.seg(slide, x + pad * 0.6, y + dy, x + w - pad * 0.6, y + dy, k.P["frame"], w=0.4),
                          "the printed rules at the head of a label card")
        d()
    return r, draw, card


def _tag(k, slide, x, y, w, h, notch):
    """A specimen tag at (x, y, w, h): a pentagon pointing left, an eyelet at its point, its string running off
    up-left. Returns the tag's rect."""
    W, H, s, o = ctx(k)
    pts = [(x + notch, y), (x + w, y), (x + w, y + h), (x + notch, y + h), (x, y + h / 2.0)]
    t = na.poly(slide, pts, fill=k.P["panel"], line=k.P["frame"], line_w=0.8)
    dk.decorative(t, "the tag shape only frames the number set on it; the number carries the meaning")
    ex, ey = x + notch * 0.55, y + h / 2.0
    na.ring(slide, ex, ey, 0.16 * s, k.P["frame"], w=0.8)
    string = na.polyline(slide, [(ex, ey), (ex - 0.35 * s, ey - 0.5 * s), (ex - 0.45 * s, max(0.45 * s, ey - 1.4 * s))],
                         k.P["stem"], w=0.9)
    dk.decorative(string, "the string a specimen tag hangs by; ornament, nothing to read in it")
    return (x, y, w, h)


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=2)
def _hb_cover(k, slide, f, image):
    """A specimen sheet's front: the title and subtitle at the left; a tall pressed sprig at the right, taped down; the
    kicker typewritten on the label card under it (where a sheet carries its collection label)."""
    W, H, s, o = ctx(k)
    kick = text_of(f, "kicker")
    _plate(k, slide, f)
    groups = [(_v2.fields(f, ("title",)), 0.28 * s), (_v2.fields(f, ("subtitle",)), 0.0)]
    if o == "land":
        tx, tw = 0.09 * W, (0.50 if alt() == 0 else 0.58) * W
        r, ds = _v2.stack(k, slide, "cover", tx, tw, 0.16 * H, H - 0.8 * s, groups, anchor="middle")
        sx0 = tx + tw + 0.5 * s
        card = None
        if kick:
            cw = min(0.30 * W, W - 0.33 * s - 0.5 * s - sx0)
            cr, cd, card = _card(k, slide, "cover", (W - 0.33 * s - 0.45 * s - cw, 0.66 * H, cw, 0.26 * H),
                                 [("kicker", kick)])
            r.update(cr)
            ds.append(cd)
        top, bot = 0.12 * H, (card[1] - 0.30 * s) if card else H - 0.8 * s
        mid = (sx0 + W - 0.33 * s) / 2.0
        span = min(1.1 * s, (W - 0.33 * s - sx0) * 0.35)
        _sprig(k, slide, (mid + 0.1 * s, bot), (mid + span, top + 0.5 * s), bend=-0.08, leaves=9, shape="fern",
               seed=4, tapes=())
        _sprig(k, slide, (mid + 0.3 * s, bot), (mid - 0.5 * span, top), bend=0.10, leaves=9, shape="ovate", seed=3,
               leaf_scale=1.2, tapes=(0.10, 0.58))
    else:
        top = 0.11 * H
        art_h = 0.36 * H
        kick_r = None
        r = {}
        ds = []
        if kick:
            cr, cd, kick_r = _card(k, slide, "cover", (0.09 * W, top, 0.40 * W, 0.22 * H), [("kicker", kick)])
            r.update(cr)
            ds.append(cd)
        tr, tds = _v2.stack(k, slide, "cover", 0.09 * W, 0.82 * W, top + art_h + 0.3 * s, H - 0.8 * s, groups,
                            anchor="middle")
        r.update(tr)
        ds += tds
        sx = (0.60 if kick else 0.50) * W
        _sprig(k, slide, (sx + 0.6 * s, top + art_h), (sx - 0.2 * s, top + 0.1 * s), bend=0.12, leaves=7,
               shape="ovate", seed=3, leaf_scale=0.95, tapes=(0.15,))
    _run_all(ds)
    return r


@register(NAME, "section", alts=2)
def _hb_section(k, slide, f, image):
    """A divider plate: the kicker, the number and the title centred, the number flanked by two small sprigs."""
    W, H, s, o = ctx(k)
    _plate(k, slide, f)
    num = text_of(f, "number")
    groups = [(_v2.fields(f, ("kicker",)), 0.15 * s),
              ([("number", num)] if num else [], 0.25 * s),
              (_v2.fields(f, ("title",)), 0.0)]
    x, w = (0.16 if alt() == 0 else 0.10) * W, (0.68 if alt() == 0 else 0.80) * W
    start = {"number": (120 if alt() == 0 else 90) * s}
    r, ds = _v2.stack(k, slide, "section", x, w, 0.14 * H, H - 0.8 * s, groups, anchor="middle", align="c", start=start)
    if num and "number" in r:
        nx, ny, nw, nh = r["number"]
        size = next((d.sizes["number"] for d in ds if "number" in getattr(d, "sizes", {})), start["number"])
        iw = min(nw, _v2.ink_w(k, "number", num, size))
        cx, cy = nx + nw / 2.0, ny + nh * 0.55
        reach = min(2.3 * s, (W - iw) / 2.0 - 0.33 * s - 0.9 * s)
        if reach > 0.9 * s:
            for side in (-1, 1):
                b = (cx + side * (iw / 2.0 + 0.35 * s), cy + 0.25 * s)
                t = (cx + side * (iw / 2.0 + 0.35 * s + reach), cy - 0.35 * s)
                _sprig(k, slide, b, t, bend=0.10 * side, leaves=5, shape="lance", seed=5 + side, leaf_scale=0.9,
                       tapes=())
    _run_all(ds)
    return r


@register(NAME, "image_text", alts=3)
def _hb_image_text(k, slide, f, image):
    """The caller's picture mounted on the sheet like a specimen — a card mount, paper tape at its four corners, the
    caption on a label card under it; the kicker, title and body beside it (under the caption on a portrait or square
    page)."""
    W, H, s, o = ctx(k)
    _plate(k, slide, f)
    cap = text_of(f, "caption")
    if o == "land":
        img = (0.10 * W, 0.17 * H, (0.44, 0.38, 0.32)[alt()] * W, (0.56 if cap else 0.64) * H)
    else:
        img = (0.10 * W, 0.12 * H, 0.80 * W, (0.34, 0.26, 0.19)[alt()] * H)
    r, ds = {}, []
    foot = img[1] + img[3]
    if cap:
        cw = min(img[2], 4.2 * s)
        cr, cd, card = _card(k, slide, "image_text", (img[0], img[1] + img[3] + 0.30 * s, cw, 1.2 * s),
                             [("caption", cap)])
        r.update(cr)
        ds.append(cd)
        foot = card[1] + card[3]
    if o == "land":
        col = (img[0] + img[2] + 0.6 * s, 0.14 * H, 0.91 * W - img[0] - img[2] - 0.6 * s, H - 0.8 * s - 0.14 * H)
    else:
        cy0 = foot + 0.40 * s                        # under the caption card as it measured, not a fixed offset
        col = (0.10 * W, cy0, 0.80 * W, H - 0.8 * s - cy0)
    tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                        [(_v2.fields(f, ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
                         (_v2.fields(f, ("body",)), 0.0)], anchor="middle")
    r.update(tr)
    ds = tds + ds
    m = 0.12 * s
    mount = dk.box(slide, img[0] - m, img[1] - m, img[2] + 2 * m, img[3] + 2 * m, fill=k.P["panel"],
                   line=dk._as_rgb(k.P["frame"]), line_w=0.5)
    dk.decorative(mount, "the card mount around the picture; the picture itself carries the meaning")
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    for (px, py), a in (((img[0], img[1]), -0.75), ((img[0] + img[2], img[1]), 0.75),
                        ((img[0], img[1] + img[3]), 0.75), ((img[0] + img[2], img[1] + img[3]), -0.75)):
        _tape(k, slide, px, py, 0.75 * s, 0.22 * s, a)
    _run_all(ds)
    return r


_KINDS = ("ovate", "lance", "round", "fern")


def _no_label(k, f, i, texts):
    return ("第 {} 号" if _lang(k, f, *texts) in ("zh", "ja") else "No. {}").format(i + 1)


@register(NAME, "points", alts=3)
def _hb_points(k, slide, f, image):
    """A plate of specimens: each point a pressed specimen (a different leaf each) taped above its own label card, the
    card typed No. 1 …, the point's head and line. The cards are planned first at their own sizes and set along the
    foot of the plate; the specimens take the height left. Too little height: smaller specimens, then (and on a
    portrait or square page) rows — a small specimen and its number beside a card holding the head and the line."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    _plate(k, slide, f)
    texts = [t_ for p_ in pts for t_ in p_ if t_]
    x0, w0 = 0.09 * W, 0.82 * W
    # the last layout (no specimens) gives a long title a little more room and starts it near its floor: set as
    # large as its room allows, a 30-character Chinese title took three lines and the cards' height (2026-10-22)
    r, ds = _v2.stack(k, slide, "points", x0, w0, 0.11 * H, (0.30 if alt() == 0 else 0.34 if alt() == 1 else 0.37) * H,
                      [(_v2.fields(f, ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)], anchor="top",
                      start=None if alt() < 2 else {"title": 28 * s})
    top = max((v[1] + v[3] for v in r.values()), default=0.11 * H) + 0.30 * s
    bottom = H - 0.8 * s
    nos = [_no_label(k, f, i, texts) for i in range(n)]
    art = []
    pad = (0.16 if alt() < 2 else 0.12) * s
    if o == "land" and alt() < 2:
        gap = 0.40 * s
        cw = (w0 - (n - 1) * gap) / n
        items = [[("item_no", nos[i]), ("item_head", hd)] + ([("item_line", ln)] if ln else [])
                 for i, (hd, ln) in enumerate(pts)]
        min_leaf = (1.5 if alt() == 0 else 0.95) * s
        room = bottom - top - min_leaf - 0.25 * s
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - 2 * pad, room - 2 * pad - 0.10 * s), it,
                                                       {"anchor": "top"}) for it in items])
        need = max(max((v[1] + v[3] for v in pr.values()), default=0.0) for pr, _d in probe) + 2 * pad + 0.10 * s
        cy = bottom - need
        leaf_top = top + 0.05 * s
        if cy - 0.25 * s - leaf_top < min_leaf:
            raise vl.VLTextOverflow("herbarium.points(): the labels leave the specimens {:.2f}in — trying a roomier "
                                    "layout".format(cy - 0.25 * s - leaf_top))
        sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}   # as measured (airmail)
        planned = _v2.plan_together(k, slide, "points", [((x0 + i * (cw + gap) + pad, cy + pad + 0.10 * s,
                                                          cw - 2 * pad, need - 2 * pad - 0.10 * s), it,
                                                          {"anchor": "top", "start": sizes})
                                                         for i, it in enumerate(items)])
        for i, (pr, pd) in enumerate(planned):
            cx = x0 + i * (cw + gap)
            r.update(pr)
            art.append(lambda cx=cx: _card_box(k, slide, (cx, cy, cw, need)))
            ds.append(pd)
            mid = cx + cw / 2.0
            kind = _KINDS[i % len(_KINDS)]
            hgt = cy - 0.10 * s - leaf_top
            lean = (0.18 if i % 2 == 0 else -0.18) * min(hgt, cw)
            art.append(lambda mid=mid, kind=kind, i=i, hgt=hgt, lean=lean: _sprig(
                k, slide, (mid + lean * 0.3, cy - 0.14 * s), (mid - lean, leaf_top), bend=0.07 * (1 if i % 2 else -1),
                leaves=6 if kind != "round" else 5, shape=kind, seed=11 + i,
                leaf_scale=min(1.15, 0.55 + 0.35 * hgt / s / 1.5), tapes=(0.16,)))
    else:
        rows, cols = (n, 1) if not (alt() == 2 and n >= 3) else (-(-n // 2), 2)
        gap, cgap = 0.28 * s, 0.35 * s
        lw = 0.0 if alt() == 2 else min(1.25 * s, 0.20 * w0)
        cw = (w0 - (cols - 1) * cgap) / cols
        rh = (bottom - top - (rows - 1) * gap) / rows
        items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
        if not lw:                                     # no specimen column: the number goes on the card
            items = [[("item_no", nos[i])] + it for i, it in enumerate(items)]
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - lw - 2 * pad, rh - 2 * pad - 0.08 * s), it,
                                                       {"anchor": "top"}) for it in items])
        hs = [max(max((v[1] + v[3] for v in pr.values()), default=0.0) + 2 * pad + 0.08 * s, 1.05 * s if lw else 0.0)
              for pr, _d in probe]
        row_h = [max(hs[i] for i in range(rw * cols, min(n, rw * cols + cols))) for rw in range(rows)]
        block = sum(row_h) + gap * (rows - 1)
        y = top + max(0.0, (bottom - top - block) * 0.40)        # the rows as one group, at the optical centre
        ys = []
        for rw in range(rows):
            ys.append(y)
            y += row_h[rw] + gap
        boxes = [(x0 + (i % cols) * (cw + cgap), ys[i // cols], row_h[i // cols]) for i in range(n)]
        sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}   # as measured (airmail)
        planned = _v2.plan_together(k, slide, "points", [((bx + lw + pad, by + pad + 0.08 * s, cw - lw - 2 * pad,
                                                          bh - 2 * pad - 0.08 * s), it, {"anchor": "top", "start": sizes})
                                                         for (bx, by, bh), it in zip(boxes, items)])
        for i, ((bx, by, bh), (pr, pd)) in enumerate(zip(boxes, planned)):
            r.update(pr)
            art.append(lambda bx=bx, by=by, bh=bh: _card_box(k, slide, (bx + lw, by, cw - lw, bh)))
            ds.append(pd)
            if lw:
                nr, nd = _v2.flow(k, slide, "points", (bx, by + bh - 0.40 * s, lw - 0.15 * s, 0.40 * s),
                                  [("item_no", nos[i])], anchor="top", align="c")
                r.update(nr)
                ds.append(nd)
                kind = ("ovate", "lance", "round", "lance")[i % 4]
                ll = max(0.45 * s, bh - 0.55 * s)
                lx = bx + (lw - 0.15 * s) / 2.0
                art.append(lambda lx=lx, by=by, ll=ll, kind=kind, i=i: _single_leaf(
                    k, slide, lx, by + 0.08 * s + ll, ll, kind, i))
    _run_all(art + ds)
    return r


def _single_leaf(k, slide, x, y, L, shape, i):
    """One pressed leaf standing on its stalk at (x, y), leaning a little, taped across the stalk."""
    W, H, s, o = ctx(k)
    lean = (-0.18 if i % 2 else 0.18)
    ang = -math.pi / 2 + lean
    stalk = 0.16 * L
    sx, sy = x - math.cos(ang) * 0.0, y
    tip_x, tip_y = sx + math.cos(ang) * stalk, sy + math.sin(ang) * stalk
    st = na.polyline(slide, [(sx, sy), (tip_x, tip_y)], k.P["stem"], w=1.2 * s)
    dk.decorative(st, "the stalk of a drawn pressed leaf; ornament, nothing to read in it")
    fill = (k.P["leaf"], k.P["leaf_dark"], k.P["leaf_dry"], k.P["leaf"])[i % 4]
    _leaf(k, slide, tip_x, tip_y, ang, L * 0.84, shape, fill)
    _tape(k, slide, sx + math.cos(ang) * stalk * 0.5, sy + math.sin(ang) * stalk * 0.5, 0.55 * s, 0.16 * s, ang + math.pi / 2)


def _card_box(k, slide, rect):
    W, H, s, o = ctx(k)
    x, y, w, h = rect
    b = dk.box(slide, x, y, w, h, fill=k.P["panel"], line=dk._as_rgb(k.P["frame"]), line_w=0.6)
    dk.decorative(b, "the label card is the ground the typed words sit on; the words carry the meaning")
    for dy in (0.10 * s, 0.14 * s):
        dk.decorative(na.seg(slide, x + 0.10 * s, y + dy, x + w - 0.10 * s, y + dy, k.P["frame"], w=0.4),
                      "the printed rules at the head of a label card")


@register(NAME, "quote", alts=2)
def _hb_quote(k, slide, f, image):
    """The quote in italic serif, the attribution typed on a label card under it; a long sprig laid along the right
    edge of the sheet (along the top on a portrait or square page)."""
    W, H, s, o = ctx(k)
    _plate(k, slide, f)
    a = text_of(f, "attribution")
    if o == "land":
        x, w, y0, y1 = 0.10 * W, (0.62 if alt() == 0 else 0.74) * W, 0.16 * H, H - 0.8 * s
    else:
        x, w, y0, y1 = 0.10 * W, 0.80 * W, (0.34 if alt() == 0 else 0.20) * H, H - 0.8 * s
    reserve = 1.35 * s if a else 0.0
    r, ds = _v2.stack(k, slide, "quote", x, w, y0, y1 - reserve, [(_v2.fields(f, ("mark", "quote")), 0.0)],
                      anchor="middle")
    if a:
        qb = max((v[1] + v[3] for v in r.values()), default=y0) + 0.35 * s
        cw = min(w * 0.62, 4.6 * s)
        cr, cd, _c = _card(k, slide, "quote", (x, qb, cw, y1 - qb), [("attribution", a)])
        r.update(cr)
        ds.append(cd)
    if o == "land" and alt() == 0:
        _sprig(k, slide, (0.88 * W, 0.84 * H), (0.82 * W, 0.16 * H), bend=-0.10, leaves=8, shape="lance", seed=7,
               tapes=(0.18, 0.70))
    elif o != "land":
        _sprig(k, slide, (0.14 * W, 0.24 * H), (0.84 * W, 0.12 * H) if alt() == 0 else (0.84 * W, 0.11 * H),
               bend=0.08, leaves=8, shape="lance", seed=7, leaf_scale=0.7, tapes=(0.30,))
    _run_all(ds)
    return r


@register(NAME, "data", alts=2)
def _hb_data(k, slide, f, image):
    """The number on a specimen tag (its eyelet and string), the label and the note beside it (under it on a portrait
    or square page)."""
    W, H, s, o = ctx(k)
    _plate(k, slide, f)
    num = text_of(f, "number")
    if o == "land":
        tag_box = (0.10 * W, 0.24 * H, (0.44 if alt() == 0 else 0.38) * W, 0.44 * H)
        col = (tag_box[0] + tag_box[2] + 0.7 * s, 0.16 * H, 0.91 * W - tag_box[0] - tag_box[2] - 0.7 * s,
               H - 0.8 * s - 0.16 * H)
    else:
        tag_box = (0.12 * W, 0.15 * H, 0.76 * W, (0.30 if alt() == 0 else 0.22) * H)
        cy0 = tag_box[1] + tag_box[3] + 0.45 * s
        col = (0.10 * W, cy0, 0.80 * W, H - 0.8 * s - cy0)
    rects, draws = {}, []
    if num:
        notch = min(0.55 * s, tag_box[3] * 0.40)
        pad_l, pad_r = notch + 0.25 * s, 0.40 * s          # the eyelet end, and the plain end
        inner = (tag_box[0] + pad_l, tag_box[1] + 0.15 * s, tag_box[2] - pad_l - pad_r, tag_box[3] - 0.30 * s)
        nr, nd = _v2.flow(k, slide, "data", inner, [("number", num)], anchor="middle", align="c")
        size = getattr(nd, "sizes", {}).get("number", vl.TYPE[NAME]["number"][0] * s)
        iw = min(inner[2], _v2.ink_w(k, "number", num, size))
        nx, ny, nw, nh = nr["number"]
        tx = nx + nw / 2.0 - iw / 2.0 - pad_l               # the tag cut to the number, the number centred on it
        # the foot of a big figure's line box renders lower than its measured box (a renderer gives the line ~1.25x
        # the size): pad the tag's foot by the size too, or the number sits on the tag's edge (TEXT PADDING, 4:3)
        pad_b = 0.15 * s + 0.06 * size / 72.0
        th = nh + 0.15 * s + pad_b
        _tag(k, slide, tx, ny - 0.15 * s, iw + pad_l + pad_r, th, notch)
        rects.update(nr)
        draws.append(nd)
    r, d = _v2.flow(k, slide, "data", col, _v2.fields(f, ("label", "note")), anchor="middle")
    rects.update(r)
    draws.append(d)
    _run_all(draws)
    return rects


@register(NAME, "closing", alts=2)
def _hb_closing(k, slide, f, image):
    """The last plate: two sprigs crossed at their stems and taped where they cross, the title and its line centred
    under them."""
    W, H, s, o = ctx(k)
    _plate(k, slide, f)
    cx = W / 2.0
    art_top = (0.14 if alt() == 0 else 0.10) * H
    art_h = (1.9 if alt() == 0 else 1.3) * s
    x, w = (0.14 if alt() == 0 else 0.09) * W, (0.72 if alt() == 0 else 0.82) * W
    r, ds = _v2.stack(k, slide, "closing", x, w, art_top + art_h + 0.45 * s, H - 0.8 * s,
                      [(_v2.fields(f, ("title",)), 0.25 * s), (_v2.fields(f, ("line",)), 0.0)], anchor="middle",
                      align="c")
    base = (cx, art_top + art_h)
    span = min(1.9 * s, 0.30 * W)
    _sprig(k, slide, base, (cx - span, art_top), bend=0.12, leaves=7, shape="ovate", seed=31, leaf_scale=1.05, tapes=())
    _sprig(k, slide, base, (cx + span, art_top), bend=-0.12, leaves=7, shape="lance", seed=32, leaf_scale=1.05, tapes=())
    _tape(k, slide, cx, base[1] - 0.12 * s, 0.75 * s, 0.22 * s, 0.0)
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_herbarium(slide, role, index):
    """An ordinary page (a chart, an agenda) on the sheet: the frame is the page's ground (new_slide paints it); the
    plate number at the top right; the content rect inside the frame, under the plate number, in REFERENCE inches."""
    K = vl.rs._K[0]
    W, H = vl.rs._canvas(slide)
    k = _v2.kit_for(NAME, slide)
    _plate(k, slide, {})
    return (0.62, 0.85, W - 1.24, H - 1.5)


_card_herbarium = vl._card_for(NAME)
