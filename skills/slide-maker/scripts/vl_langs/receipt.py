"""receipt — the Shop receipt language (购物小票): its ground painter, its card and its seven pages.

A thermal till slip on a counter: torn zigzag edges, monospaced type, dashed separators, a barcode at the foot. The
points read as line items (01 RENT AND BILLS, its note under it), the key figure as the total, set to the right. On
the cover and the last page an older slip lies askew behind. Every page PLANS its words first (vl_native2.flow,
measured, never under a floor) block by block down the slip, cuts the slip to them, then draws the slip and sets the
words. The only words it writes itself are the line numbers (the manifest's derived words)."""
from __future__ import annotations

import hashlib
import math

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "receipt"


def _caps(t):
    return _v2.caps(t)


# ─────────────────────────────────────────── the slip ───────────────────────────────────────────
def _slip_pts(x, y, w, h, s):
    """The slip's outline: torn zigzag top and bottom, straight sides."""
    a, p = 0.07 * s, 0.17 * s
    n = max(4, int(round(w / p)))
    top = [(x + w * i / n, y + (0.0 if i % 2 == 0 else a)) for i in range(n + 1)]
    bot = [(x + w * i / n, y + h - (0.0 if i % 2 == 0 else a)) for i in range(n, -1, -1)]
    return top + bot


def _rot(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (px - cx) * ca - (py - cy) * sa, cy + (px - cx) * sa + (py - cy) * ca) for px, py in pts]


def _slip(k, slide, rect, *, fill=None, deg=0.0, shadow=True):
    W, H, s, o = ctx(k)
    x, y, w, h = rect
    pts = _slip_pts(x, y, w, h, s)
    if deg:
        pts = _rot(pts, x + w / 2.0, y + h / 2.0, deg)
    sh = na.poly(slide, pts, fill=fill or k.P["slip"])
    if sh is not None:
        dk.decorative(sh, "the till slip the words are printed on; the words carry the meaning")
        dk.overlap_intent(sh, "a till slip lies over the print or the older slip on the counter: layered by design")
        if shadow:
            na.soft_shadow(sh, blur=0.12, dist=0.05, alpha=0.26)
    return sh


def _dashes(k, slide, x0, x1, y):
    sh = na.strokes(slide, [((x0, y), (x1, y))], k.P["ink"], w=0.9, dash=True, alpha=0.7)
    if sh is not None:
        dk.decorative(sh, "the dashed separator printed across the slip; it only divides the blocks")


def _barcode(k, slide, x, y, w, h, seed):
    """Bars of a till slip's barcode, from a hash of the slip's words: furniture, it encodes nothing."""
    hsh = hashlib.sha256(seed.encode("utf-8")).digest()
    units = [1 + (b % 3) for b in hsh] * 2
    total = sum(units[:60])
    u = w / total
    bars, cx = [], x
    for i, n in enumerate(units[:60]):
        if i % 2 == 0:
            bars.append([(cx, y), (cx + n * u, y), (cx + n * u, y + h), (cx, y + h)])
        cx += n * u
    sh = na.multipoly(slide, bars, k.P["barcode"])
    if sh is not None:
        dk.decorative(sh, "barcode-like bars at the foot of the slip: a receipt's furniture, they encode nothing")


def _seq(k, slide, page, x, w, y, y_max, blocks):
    """PLAN blocks down a slip column: blocks = [(items, align, dash_after, start)] (an empty block skipped). Every block
    is first sized TOGETHER (as vl_native2.stack does: planned one by one, a long title took the whole slip and left
    the subtitle none), then planned in turn in what is left; a dashed separator sits in the gap after a block that
    asks for one. When a later block still cannot fit, the joint sizing is re-run in a smaller budget (the estimate
    reads repeated fields as one entry of lines) — refused only when even that fails. Returns (rects, draws, dash_ys,
    foot)."""
    W, H, s, o = ctx(k)
    blocks = [b for b in blocks if b[0]]
    gaps = sum((0.40 if d else 0.12) * s for _i, _a, d, _st in blocks[:-1])
    gaps += sum(max(0, len(b[0]) - 1) for b in blocks) * vl.GAP * s      # each block's own gaps between its fields
    joint = {}
    for _i, _a, _d, st in blocks:
        joint.update(st or {})
    merged = {}                       # a field repeated across blocks (each line item's head) is ONE entry of lines
    for b in blocks:
        for f_, t_ in b[0]:
            merged[f_] = (merged[f_] + "\n" + t_) if f_ in merged else t_
    last = None
    for attempt in range(6):
        budget = max(0.1, (y_max - y - gaps) * (1.0 - 0.08 * attempt))
        _r0, d0 = _v2.flow(k, slide, page, (x, y, w, budget), list(merged.items()), anchor="top",
                           **({"start": joint} if joint else {}))
        sized = dict(getattr(d0, "sizes", {}))
        try:
            return _seq_place(k, slide, page, x, w, y, y_max, blocks, sized)
        except vl.VLTextOverflow as e:
            last = e
    raise last


def _seq_place(k, slide, page, x, w, y, y_max, blocks, sized):
    W, H, s, o = ctx(k)
    rects, draws, dash_ys = {}, [], []
    for i, (items, align, dash, start) in enumerate(blocks):
        kw = {"anchor": "top", "align": align}
        st = dict(start or {}, **{f_: sized[f_] for f_, _t in items if f_ in sized})
        if st:
            kw["start"] = st
        r, d = _v2.flow(k, slide, page, (x, y, w, max(0.1, y_max - y)), items, **kw)
        rects.update(r)
        draws.append(d)
        foot = max((v[1] + v[3] for v in r.values()), default=y)
        if i < len(blocks) - 1:
            if dash:
                dash_ys.append(foot + 0.20 * s)
                y = foot + 0.40 * s
            else:
                y = foot + 0.12 * s
        else:
            y = foot
    return rects, draws, dash_ys, y


def _receipt(k, slide, page, x, w, blocks, *, y_lo, y_hi, barcode=None, center=True, back=False):
    """A whole slip: its blocks planned down it, a dashed rule and the barcode at its foot when `barcode` (its seed
    words) is given, the slip cut to them and centred in [y_lo, y_hi]. Draws it all; returns (rects, slip_rect)."""
    W, H, s, o = ctx(k)
    pad, tooth = 0.40 * s, 0.10 * s
    bar_h = 0.55 * s if barcode else 0.0
    tail = (0.40 * s + bar_h) if barcode else 0.0

    def plan(y0):
        return _seq(k, slide, page, x + pad, w - 2 * pad, y0 + pad + tooth, y_hi - pad - tooth - tail, blocks)
    rects, draws, dashes, foot = plan(y_lo)
    h = foot - y_lo + tail + pad + tooth
    if center:
        y0 = y_lo + max(0.0, (y_hi - y_lo - h) * 0.45)
        rects, draws, dashes, foot = plan(y0)
    else:
        y0 = y_lo
    slip = (x, y0, w, foot - y0 + tail + pad + tooth)
    if back:
        _slip(k, slide, (x + 0.45 * s, y0 - 0.15 * s, w, slip[3] * 0.92), fill=k.P["slip_back"], deg=5.0)
    _slip(k, slide, slip)
    for yd in dashes:
        _dashes(k, slide, x + pad * 0.6, x + w - pad * 0.6, yd)
    if barcode:
        _dashes(k, slide, x + pad * 0.6, x + w - pad * 0.6, foot + 0.20 * s)
        bw = min(w - 2 * pad, 3.2 * s)
        _barcode(k, slide, x + (w - bw) / 2.0, foot + 0.40 * s, bw, bar_h, barcode)
    _run_all(draws)
    return rects, slip


def _seed(f):
    return " ".join(str(v) for v in f.values() if isinstance(v, str)) or "receipt"


def _cols(k, frac_land, frac_port):
    W, H, s, o = ctx(k)
    w = (frac_land if o == "land" else frac_port) * W
    return (W - w) / 2.0, w


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=2)
def _rc_cover(k, slide, f, image):
    """The slip itself: the kicker printed as the shop's header, a dashed rule, the title in bold, the subtitle, the
    barcode; an older slip askew behind it."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    x, w = _cols(k, (0.42, 0.50)[alt()], (0.78, 0.86)[alt()])
    blocks = [(_v2.fields(f, ("kicker",), ("kicker",)), "c", True, None),
              (_v2.fields(f, ("title",)), "c", bool(text_of(f, "subtitle")), None),
              (_v2.fields(f, ("subtitle",)), "c", False, None)]
    r, _slip_r = _receipt(k, slide, "cover", x, w, blocks, y_lo=m, y_hi=H - m, barcode=_seed(f), back=True)
    return r


@register(NAME, "section", alts=2)
def _rc_section(k, slide, f, image):
    """A slip with the section number printed large between two dashed rules; the kicker above, the title below."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    x, w = _cols(k, (0.38, 0.48)[alt()], (0.74, 0.84)[alt()])
    num = text_of(f, "number")
    blocks = [(_v2.fields(f, ("kicker",), ("kicker",)), "c", True, None),
              ([("number", num)] if num else [], "c", True, {"number": (110 if alt() == 0 else 80) * s}),
              (_v2.fields(f, ("title",)), "c", False, None)]
    r, _s = _receipt(k, slide, "section", x, w, blocks, y_lo=m, y_hi=H - m)
    return r


@register(NAME, "image_text", alts=3)
def _rc_image_text(k, slide, f, image):
    """The caller's picture lying on the counter as a print with a white border, the caption under it; a slip laid
    over its right edge carrying the kicker, title and body (under the picture on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    cap = text_of(f, "caption")
    b = 0.12 * s
    if o == "land":
        img = (m + 0.3 * s, 0.14 * H, (0.50, 0.44, 0.38)[alt()] * W, (0.62 if cap else 0.70) * H)
    else:
        img = (0.10 * W, m + 0.15 * s, 0.80 * W, (0.34, 0.27, 0.20)[alt()] * H)
    r = {}
    frame = dk.box(slide, img[0] - b, img[1] - b, img[2] + 2 * b, img[3] + 2 * b, fill=k.P["slip"])
    dk.decorative(frame, "the print's white border; the picture itself carries the meaning")
    na.soft_shadow(frame, blur=0.10, dist=0.05, alpha=0.24)
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    foot = img[1] + img[3] + b
    if cap:
        cw = img[2] - (0.75 * s if o == "land" else 0.0)     # ends before the slip laid over the print's right edge
        cr, cd = _v2.flow(k, slide, "image_text", (img[0], foot + 0.18 * s, cw, 0.8 * s), [("caption", cap)])
        cd()
        r.update(cr)
        foot = max(v[1] + v[3] for v in cr.values())
    rules = alt() < 2                              # the last layout gives the dashed rules' room to the words
    blocks = [(_v2.fields(f, ("kicker",), ("kicker",)), "l", rules, None),
              (_v2.fields(f, ("title",)), "l", rules and bool(text_of(f, "body")), None),
              (_v2.fields(f, ("body",)), "l", False, None)]
    if o == "land":
        x = img[0] + img[2] - 0.35 * s
        w = W - m - x
        rr, sl = _receipt(k, slide, "image_text", x, w, blocks, y_lo=0.10 * H, y_hi=H - m)
    else:
        sw = (0.76, 0.82, 0.88)[alt()] * W
        rr, sl = _receipt(k, slide, "image_text", (W - sw) / 2.0, sw, blocks, y_lo=foot + 0.25 * s, y_hi=H - m)
    r.update(rr)
    return r


@register(NAME, "points", alts=3)
def _rc_points(k, slide, f, image):
    """An itemised slip: the kicker as the header, the title in bold, a dashed rule, then each point as a line item —
    01 and its head in capitals, its line under it — a dashed rule and the barcode at the foot. Long copy: a wider
    slip, then two slips side by side (landscape) or no barcode."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    pts = points_of(f.get("items"))
    n = len(pts)
    two = o == "land" and alt() == 2 and n >= 3
    head = [(_v2.fields(f, ("kicker",), ("kicker",)), "c", True, None), (_v2.fields(f, ("title",)), "c", True, None)]
    lines = [([("item_head", "{:02d}  {}".format(i + 1, _caps(hd)))] + ([("item_line", ln)] if ln else []),
              "l", False, None) for i, (hd, ln) in enumerate(pts)]
    barcode = _seed(f) if alt() < 2 else None
    if not two:
        x, w = _cols(k, (0.46, 0.58, 0.66)[alt()], (0.80, 0.86, 0.88)[alt()])
        blocks = head + [(it, al, i < n - 1 and False, st) for i, (it, al, _d, st) in enumerate(lines)]
        r, _s = _receipt(k, slide, "points", x, w, blocks, y_lo=m, y_hi=H - m, barcode=barcode)
        return r
    a = -(-n // 2)
    gap = 0.45 * s
    w = (0.86 * W - gap) / 2.0
    x0 = (W - 2 * w - gap) / 2.0
    r1, s1 = _receipt(k, slide, "points", x0, w, head + lines[:a], y_lo=m, y_hi=H - m, center=False)
    r2, s2 = _receipt(k, slide, "points", x0 + w + gap, w, lines[a:], y_lo=m + 0.5 * s, y_hi=H - m, center=False)
    r1.update(r2)
    return r1


@register(NAME, "quote", alts=2)
def _rc_quote(k, slide, f, image):
    """A slip with the quote printed across it, the attribution under a dashed rule, the barcode at the foot."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    x, w = _cols(k, (0.48, 0.62)[alt()], (0.80, 0.88)[alt()])
    blocks = [(_v2.fields(f, ("mark", "quote")), "c", bool(text_of(f, "attribution")), None),
              (_v2.fields(f, ("attribution",)), "c", False, None)]
    r, _s = _receipt(k, slide, "quote", x, w, blocks, y_lo=m, y_hi=H - m, barcode=_seed(f) if alt() == 0 else None)
    return r


@register(NAME, "data", alts=2)
def _rc_data(k, slide, f, image):
    """A slip read like its total: the label in bold, a dashed rule, the number printed large and set to the right, the
    note under a second rule, the barcode at the foot."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    x, w = _cols(k, (0.46, 0.58)[alt()], (0.80, 0.88)[alt()])
    num = text_of(f, "number")
    blocks = [(_v2.fields(f, ("label",)), "l", True, None),
              ([("number", num)] if num else [], "r", bool(text_of(f, "note")), None),
              (_v2.fields(f, ("note",)), "l", False, None)]
    r, _s = _receipt(k, slide, "data", x, w, blocks, y_lo=m, y_hi=H - m, barcode=_seed(f) if alt() == 0 else None)
    return r


@register(NAME, "closing", alts=2)
def _rc_closing(k, slide, f, image):
    """The end of the slip: the title in bold and its line, the barcode; an older slip askew behind."""
    W, H, s, o = ctx(k)
    m = 0.55 * s
    x, w = _cols(k, (0.42, 0.56)[alt()], (0.76, 0.86)[alt()])
    blocks = [(_v2.fields(f, ("title",)), "c", bool(text_of(f, "line")), None),
              (_v2.fields(f, ("line",)), "c", False, None)]
    r, _s = _receipt(k, slide, "closing", x, w, blocks, y_lo=m, y_hi=H - m, barcode=_seed(f), back=True)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_receipt(slide, role, index):
    """An ordinary page (a chart, an agenda) on the counter: the counter is the page's ground; the content rect in
    REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


_card_receipt = vl._card_for(NAME)
