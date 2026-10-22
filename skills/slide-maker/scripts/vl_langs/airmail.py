"""airmail — the Air mail language (航空邮件): its ground painter, its card and its seven pages.

An air-mail envelope: the red-and-blue striped border round every page, a perforated stamp (a paper plane on the cover;
the key number as its denomination elsewhere), a round postmark with wavy cancel lines, address-label cards, and on the
last page the envelope's back — its flap and a wax seal. Every page PLANS its words first (vl_native2.flow / stack:
measured, never under a floor), draws its art clear of them, then sets them. The only words it writes itself are the
point numbers on the points page's small stamps (the manifest's derived words)."""
from __future__ import annotations

import math

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "airmail"


# ─────────────────────────────────────────── drawing helpers ───────────────────────────────────────────
def _multipoly(slide, polys, fill, *, alpha=None, reason):
    """native_art.multipoly, declared decorative with `reason`."""
    sh = na.multipoly(slide, polys, fill, alpha=alpha)
    if sh is not None:
        dk.decorative(sh, reason)
    return sh


def _clip(pts, lo, hi, axis):
    """Sutherland–Hodgman clip of a polygon to lo <= coordinate[axis] <= hi."""
    def cut(poly, keep, edge):
        out = []
        for i, p in enumerate(poly):
            q = poly[i - 1]
            pin, qin = keep(p), keep(q)
            if pin != qin:
                t = (edge - q[axis]) / ((p[axis] - q[axis]) or 1e-9)
                out.append((q[0] + t * (p[0] - q[0]), q[1] + t * (p[1] - q[1])))
            if pin:
                out.append(p)
        return out
    pts = cut(pts, lambda p: p[axis] >= lo, lo)
    return cut(pts, lambda p: p[axis] <= hi, hi) if pts else pts


def _stripes(k, slide, rect, horizontal, L, gap):
    """The air-mail chevrons inside `rect` — red, gap, blue, gap — as two shapes (one per colour)."""
    x, y, w, h = rect
    reds, blues = [], []
    period, i = 2 * (L + gap), 0
    if horizontal:
        pos = x - h - period
        while pos < x + w + h:
            for off, bucket in ((0.0, reds), (L + gap, blues)):
                a = pos + off
                poly = [(a, y), (a + L, y), (a + L - h, y + h), (a - h, y + h)]
                poly = _clip(poly, x, x + w, 0)
                if len(poly) >= 3:
                    bucket.append(poly)
            pos += period
            i += 1
    else:
        pos = y - w - period
        while pos < y + h + w:
            for off, bucket in ((0.0, reds), (L + gap, blues)):
                a = pos + off
                poly = [(x, a), (x, a + L), (x + w, a + L - w), (x + w, a - w)]
                poly = _clip(poly, y, y + h, 1)
                if len(poly) >= 3:
                    bucket.append(poly)
            pos += period
    _multipoly(slide, reds, k.P["stripe_a"], reason="the air-mail border's red chevrons; the envelope's edge, not a sign")
    _multipoly(slide, blues, k.P["stripe_b"], reason="the air-mail border's second chevrons; the envelope's edge, not a sign")


def _border(k, slide):
    """Every page: the striped air-mail border round the envelope's edge."""
    W, H, s, o = ctx(k)
    bi, bh = 0.16 * s, 0.20 * s
    L, gap = 0.42 * s, 0.22 * s
    _stripes(k, slide, (bi, bi, W - 2 * bi, bh), True, L, gap)
    _stripes(k, slide, (bi, H - bi - bh, W - 2 * bi, bh), True, L, gap)
    _stripes(k, slide, (bi, bi + bh, bh, H - 2 * bi - 2 * bh), False, L, gap)
    _stripes(k, slide, (W - bi - bh, bi + bh, bh, H - 2 * bi - 2 * bh), False, L, gap)


vn.GROUNDS[NAME] = _border


def _circle(cx, cy, r, n=40):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _stamp(k, slide, x, y, w, h):
    """A perforated stamp at (x, y, w, h): its paper, the perforation bites round its edge, an inner frame. Returns the
    inner frame's rect (where its picture or its number goes)."""
    W, H, s, o = ctx(k)
    paper = dk.box(slide, x, y, w, h, fill=k.P["stamp"])
    dk.decorative(paper, "the stamp's paper; the number or the picture printed on it carries the meaning")
    na.soft_shadow(paper, blur=0.06, dist=0.03, alpha=0.22)
    d = 0.10 * s
    step = d * 2.1
    bites = []
    for side in range(4):
        length = w if side % 2 == 0 else h
        n = max(2, int(length / step))
        for i in range(n + 1):
            t = i / n
            cx = (x + t * w) if side % 2 == 0 else (x if side == 1 else x + w)
            cy = (y if side == 0 else y + h) if side % 2 == 0 else (y + t * h)
            bites.append(_circle(cx, cy, d / 2.0, 12))
    _multipoly(slide, bites, k.P["ground"], reason="the perforation round the stamp's edge, cut in the envelope's colour")
    m = 0.15 * s
    frame = dk.box(slide, x + m, y + m, w - 2 * m, h - 2 * m, fill=None, line=dk._as_rgb(k.P["stamp_frame"]), line_w=1.0)
    dk.decorative(frame, "the printed frame inside the stamp; it only borders what the stamp shows")
    return (x + m, y + m, w - 2 * m, h - 2 * m)


def _plane(k, slide, rect):
    """A paper plane and its dashed flight path inside `rect` — the stamp's picture on the cover."""
    x, y, w, h = rect
    P = lambda u, v: (x + u * w, y + v * h)          # noqa: E731
    path = na.polyline(slide, [P(0.06, 0.88), P(0.20, 0.80), P(0.32, 0.70), P(0.40, 0.62)], k.P["plane"], w=1.0)
    from pptx.enum.dml import MSO_LINE_DASH_STYLE
    path.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    dk.decorative(path, "the paper plane's flight path; part of the stamp's picture")
    _multipoly(slide, [[P(0.30, 0.48), P(0.94, 0.16), P(0.50, 0.58)]], k.P["plane"],
               reason="the paper plane drawn on the stamp: air mail's emblem")
    _multipoly(slide, [[P(0.50, 0.58), P(0.94, 0.16), P(0.60, 0.80)]], k.P["stripe_a"],
               reason="the paper plane's lower wing: air mail's emblem")
    _multipoly(slide, [[P(0.50, 0.58), P(0.60, 0.80), P(0.48, 0.70)]], k.P["stamp_frame"],
               reason="the paper plane's keel: air mail's emblem")


def _postmark(k, slide, cx, cy, d, *, waves=0.0, side=-1):
    """A round postmark at (cx, cy): two rings, the empty date slug across it, and `waves` inches of wavy cancel lines
    running off to one side (-1 left, +1 right)."""
    W, H, s, o = ctx(k)
    c = k.P["postmark"]
    out = []
    for r, w in ((d / 2.0, 1.6), (d * 0.39, 0.8)):
        pts = _circle(cx, cy, r, 48)
        out.append(na.polyline(slide, pts + pts[:1], c, w=w, alpha=0.82))
    out.append(na.strokes(slide, [((cx - d * 0.30, cy + dy), (cx + d * 0.30, cy + dy)) for dy in (-0.07 * s, 0.07 * s)],
                          c, w=0.8, alpha=0.82))          # pen strokes, not connectors: they dock to nothing
    if waves > 0:
        x0 = cx + side * (d / 2.0 + 0.08 * s)
        for j in range(5):
            yy = cy + (j - 2) * 0.13 * s
            pts = [(x0 + side * waves * i / 60.0, yy + 0.06 * s * math.sin(2 * math.pi * (waves * i / 60.0) / (0.62 * s)))
                   for i in range(61)]
            out.append(na.polyline(slide, pts, c, w=1.1, alpha=0.78))
    for sh in out:
        if sh is not None:
            dk.decorative(sh, "the postmark and its cancel lines: an envelope's furniture, nothing to read in it")
            dk.overlap_intent(sh, "a postmark is struck across the stamp it cancels: layered by design")


def _label_band(k, slide, x, y, w):
    """The striped band along the top of an address label."""
    W, H, s, o = ctx(k)
    _stripes(k, slide, (x, y, w, 0.12 * s), True, 0.26 * s, 0.13 * s)


def _seal(k, slide, cx, cy, d):
    """A wax seal: a disc with a pressed, uneven edge, an inner ring and a small star pressed into it."""
    W, H, s, o = ctx(k)
    R = d / 2.0
    edge = [(cx + R * (1 + 0.05 * math.sin(9 * a) + 0.03 * math.sin(5 * a + 1.0)) * math.cos(a),
             cy + R * (1 + 0.05 * math.sin(9 * a) + 0.03 * math.sin(5 * a + 1.0)) * math.sin(a))
            for a in [2 * math.pi * i / 72 for i in range(72)]]
    disc = na.poly(slide, edge, fill=k.P["seal"])
    dk.decorative(disc, "the wax seal on the envelope's flap: ornament, nothing to read in it")
    na.soft_shadow(disc, blur=0.08, dist=0.04, alpha=0.3)
    ring = _circle(cx, cy, R * 0.66, 48)
    dk.decorative(na.polyline(slide, ring + ring[:1], k.P["seal_dark"], w=1.6), "the ring pressed into the wax seal")
    star = [(cx + (R * 0.30 if i % 2 == 0 else R * 0.12) * math.cos(-math.pi / 2 + math.pi * i / 5),
             cy + (R * 0.30 if i % 2 == 0 else R * 0.12) * math.sin(-math.pi / 2 + math.pi * i / 5)) for i in range(10)]
    _multipoly(slide, [star], k.P["seal_dark"], reason="the star pressed into the wax seal; ornament only")


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
M = 0.62          # the margin inside the border, in units of s (landscape; a portrait or square page takes less)


def _m(k):
    W, H, s, o = ctx(k)
    return (M if o == "land" else 0.40) * s + 0.36 * s


@register(NAME, "cover", alts=2)
def _am_cover(k, slide, f, image):
    """An envelope's front: the kicker where the sender writes, a stamp with a paper plane at the top right, struck by
    a postmark whose cancel lines run across the top; the title and subtitle where the address goes."""
    W, H, s, o = ctx(k)
    m = _m(k)
    land = o == "land"
    sw, sh = (1.55 * s, 1.85 * s) if land else (1.30 * s, 1.55 * s)
    sx, sy = W - m - sw, m - 0.05 * s
    r, ds = {}, []
    kick = text_of(f, "kicker")
    if kick:
        kr, kd = _v2.flow(k, slide, "cover", (m, m, min(0.42 * W, sx - m - 2.9 * s if land else sx - m - 0.4 * s),
                                              1.0 * s), [("kicker", _v2.caps(kick))])
        r.update(kr)
        ds.append(kd)
    if land:
        ax = (0.34 if alt() == 0 else 0.16) * W
        ay0 = max(0.40 * H, sy + sh + 0.35 * s)
    else:
        ax = 0.10 * W
        ay0 = max(0.40 * H, sy + sh + 0.45 * s)
    tr, tds = _v2.stack(k, slide, "cover", ax, W - m - ax, ay0, H - m, [(_v2.fields(f, ("title",)), 0.22 * s),
                                                                      (_v2.fields(f, ("subtitle",)), 0.0)],
                        anchor="middle")
    r.update(tr)
    ds += tds
    inner = _stamp(k, slide, sx, sy, sw, sh)
    _plane(k, slide, inner)
    _postmark(k, slide, sx + 0.10 * s, sy + sh * 0.80, (1.30 if land else 1.10) * s,
              waves=(2.6 if land else 1.6) * s, side=-1)
    _run_all(ds)
    return r


def _number_stamp(k, slide, page, box, num, *, start=None):
    """PLAN the number as a stamp's denomination: the stamp cut to the number, centred in `box`. Returns (rects, draw,
    stamp_rect); draw() draws the stamp and then the number."""
    W, H, s, o = ctx(k)
    x, y, w, h = box
    m = 0.15 * s
    pad = 0.30 * s
    kw = {"anchor": "middle", "align": "c"}
    if start:
        kw["start"] = start
    nr, nd = _v2.flow(k, slide, page, (x + m + pad, y + m + pad, w - 2 * (m + pad), h - 2 * (m + pad)),
                      [("number", num)], **kw)
    size = getattr(nd, "sizes", {}).get("number", vl.TYPE[NAME]["number"][0] * s)
    iw = min(w - 2 * (m + pad), _v2.ink_w(k, "number", num, size))
    nx, ny, nw, nh = nr["number"]
    sw = min(w, iw + 2 * (m + pad))
    sh_ = min(h, max(nh + 2 * (m + 0.18 * s), sw * 1.12))
    sx = nx + nw / 2.0 - sw / 2.0
    sy = ny + nh / 2.0 - sh_ / 2.0

    def draw():
        _stamp(k, slide, sx, sy, sw, sh_)
        nd()
    return nr, draw, (sx, sy, sw, sh_)


@register(NAME, "section", alts=2)
def _am_section(k, slide, f, image):
    """A stamp carrying the section number as its denomination, struck by a postmark; the kicker and title beside it
    (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    r, ds = {}, []
    if o == "land":
        box = (m + 0.2 * s, 0.20 * H, (0.32 if alt() == 0 else 0.26) * W, 0.62 * H)
        col = (box[0] + box[2] + 0.8 * s, 0.18 * H, W - m - box[0] - box[2] - 0.8 * s, 0.66 * H)
    else:
        box = (0.22 * W, m + 0.2 * s, 0.56 * W, (0.34 if alt() == 0 else 0.26) * H)
        col = (0.10 * W, box[1] + box[3] + 0.5 * s, 0.80 * W, H - m - box[1] - box[3] - 0.5 * s)
    stamp = None
    if num:
        nr, nd, stamp = _number_stamp(k, slide, "section", box, num, start={"number": 120 * s})
        r.update(nr)
        ds.append(nd)
    tr, tds = _v2.stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3],
                        [(_v2.fields(f, ("kicker",), ("kicker",)), 0.15 * s), (_v2.fields(f, ("title",)), 0.0)],
                        anchor="middle", align="l" if o == "land" else "c")
    r.update(tr)
    ds = ds + tds
    _run_all(ds)
    if stamp:
        sx, sy, sw, sh_ = stamp
        _postmark(k, slide, sx + sw, sy + sh_ * 0.15, 1.15 * s, waves=0.0)
    return r


@register(NAME, "image_text", alts=3)
def _am_image_text(k, slide, f, image):
    """The caller's picture as a postcard — a white border, a soft shadow, a postmark struck across its corner; the
    caption under it, the kicker, title and body beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    cap = text_of(f, "caption")
    if o == "land":
        img = (m + 0.15 * s, 0.17 * H, (0.46, 0.40, 0.34)[alt()] * W, (0.58 if cap else 0.66) * H)
    else:
        img = (0.12 * W, m + 0.1 * s, 0.76 * W, (0.34, 0.26, 0.19)[alt()] * H)
    r, ds = {}, []
    foot = img[1] + img[3]
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (img[0], foot + 0.28 * s, img[2], 0.9 * s), [("caption", cap)])
        r.update(cr)
        ds.append(cd)
        foot = max(v[1] + v[3] for v in cr.values())
    if o == "land":
        col = (img[0] + img[2] + 0.75 * s, 0.15 * H, W - m - img[0] - img[2] - 0.75 * s, 0.72 * H)
    else:
        col = (0.10 * W, foot + 0.40 * s, 0.80 * W, H - m - foot - 0.40 * s)
    tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                        [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
                         (_v2.fields(f, ("body",)), 0.0)], anchor="middle")
    r.update(tr)
    ds = tds + ds
    b = 0.13 * s
    card = dk.box(slide, img[0] - b, img[1] - b, img[2] + 2 * b, img[3] + 2 * b, fill=k.P["stamp"])
    dk.decorative(card, "the postcard's white border round the picture; the picture carries the meaning")
    na.soft_shadow(card, blur=0.10, dist=0.05, alpha=0.24)
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _postmark(k, slide, img[0] + img[2] - 0.15 * s, img[1] + 0.15 * s, 1.05 * s, waves=min(2.0 * s, img[2] * 0.45),
              side=-1)
    _run_all(ds)
    return r


@register(NAME, "points", alts=4)
def _am_points(k, slide, f, image):
    """Address labels: each point a label with the striped air-mail band along its top and a small stamp in its corner
    numbered 1 2 3 — the point's head and line under the band. Columns across a landscape page; rows on a portrait or
    square page; long copy gives the title less room, then two columns of rows."""
    W, H, s, o = ctx(k)
    m = _m(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    x0, w0 = m, W - 2 * m
    # the roomier layouts start the title smaller: set at the largest size its room allows, a long title took the
    # height the labels needed (a 30-character Chinese title on a square page, 2026-10-22)
    r, ds = _v2.stack(k, slide, "points", x0, w0, m, m + (0.22 if alt() == 0 else 0.30) * H,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", start=None if alt() < 2 else {"title": 34 * s})
    top = max((v[1] + v[3] for v in r.values()), default=m) + (0.40 if alt() < 2 else 0.28) * s
    bottom = H - m
    st_w, st_h = 0.62 * s, 0.74 * s
    pad = (0.20 if alt() < 3 else 0.14) * s
    band = 0.12 * s
    stamps = alt() < 3                            # the last layout sets the number as type on the label instead
    if o == "land" and alt() < 2:
        cols, rows = n, 1
    elif alt() >= 2 and n >= 3:
        cols, rows = 2, -(-n // 2)
    else:
        cols, rows = 1, n
    gap = (0.35 if alt() < 3 else 0.24) * s
    cw = (w0 - (cols - 1) * gap) / cols
    rh = (bottom - top - (rows - 1) * gap) / rows
    side = rows > 1                               # rows (or a grid): the stamp at the left, the words beside it
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    if not stamps:
        items = [[("item_no", str(i + 1))] + it for i, it in enumerate(items)]
        rects = [(pad, band + pad, cw - 2 * pad, rh - band - 2 * pad) for _ in pts]
    elif side:
        rects = [(st_w + 2 * pad, band + pad, cw - st_w - 3 * pad, rh - band - 2 * pad) for _ in pts]
    else:
        rects = [(pad, band + pad + st_h + 0.10 * s, cw - 2 * pad, rh - band - 2 * pad - st_h - 0.10 * s) for _ in pts]
    probe = _v2.plan_together(k, slide, "points", [((0, 0, w_, h_), it, {"anchor": "top"})
                                                   for (dx, dy, w_, h_), it in zip(rects, items)])
    need = [max((v[1] + v[3] for v in pr.values()), default=0.0) + rects[i][1] + pad for i, (pr, _d) in enumerate(probe)]
    if side and stamps:
        need = [max(h_, st_h + band + 2 * pad) for h_ in need]
    row_h = [max(need[i] for i in range(rw * cols, min(n, rw * cols + cols))) for rw in range(rows)]
    block = sum(row_h) + gap * (rows - 1)
    if block > bottom - top + 1e-6:
        raise vl.VLTextOverflow("airmail.points(): the labels need {:.2f}in, the page has {:.2f}in".format(
            block, bottom - top))
    y = top + (bottom - top - block) * 0.40
    ys = []
    for rw in range(rows):
        ys.append(y)
        y += row_h[rw] + gap
    # set at the sizes the probe measured: flowed afresh, a label breaks its clauses at the design size and can need
    # a line more than the probe found at the shared size (a Chinese label on a square page, 2026-10-22)
    sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
    planned = _v2.plan_together(k, slide, "points", [((x0 + (i % cols) * (cw + gap) + dx, ys[i // cols] + dy, w_,
                                                      row_h[i // cols] - dy - pad), it, {"anchor": "top", "start": sizes})
                                                     for i, ((dx, dy, w_, h_), it) in enumerate(zip(rects, items))])
    art = []
    for i, (pr, pd) in enumerate(planned):
        cx, cy, ch = x0 + (i % cols) * (cw + gap), ys[i // cols], row_h[i // cols]
        r.update(pr)
        if stamps:
            sx, sy = (cx + pad, cy + band + pad) if side else (cx + cw - pad - st_w, cy + band + pad)
            nr, nd, _st = _small_stamp(k, slide, sx, sy, st_w, st_h, str(i + 1))
            r.update(nr)
        else:
            nd = (lambda: None)

        def card(cx=cx, cy=cy, ch=ch, nd=nd):
            b = dk.box(slide, cx, cy, cw, ch, fill=k.P["panel"])
            dk.decorative(b, "the address label the words are written on; the words carry the meaning")
            na.soft_shadow(b, blur=0.06, dist=0.03, alpha=0.18)
            _label_band(k, slide, cx, cy, cw)
            nd()
        art.append(card)
        ds.append(pd)
    _run_all(art + ds)
    return r


def _small_stamp(k, slide, x, y, w, h, num):
    """PLAN a small stamp carrying `num`; returns (rects, draw, rect)."""
    W, H, s, o = ctx(k)
    m = 0.10 * s
    nr, nd = _v2.flow(k, slide, "points", (x + m, y + m, w - 2 * m, h - 2 * m), [("item_no", num)], anchor="middle",
                      align="c")

    def draw():
        _stamp_small(k, slide, x, y, w, h)
        nd()
    return nr, draw, (x, y, w, h)


def _stamp_small(k, slide, x, y, w, h):
    W, H, s, o = ctx(k)
    paper = dk.box(slide, x, y, w, h, fill=k.P["stamp"])
    dk.decorative(paper, "the small stamp's paper; the number printed on it carries the meaning")
    d = 0.07 * s
    bites = []
    for side in range(4):
        length = w if side % 2 == 0 else h
        n = max(2, int(length / (d * 2.2)))
        for i in range(n + 1):
            t = i / n
            cx = (x + t * w) if side % 2 == 0 else (x if side == 1 else x + w)
            cy = (y if side == 0 else y + h) if side % 2 == 0 else (y + t * h)
            bites.append(_circle(cx, cy, d / 2.0, 10))
    _multipoly(slide, bites, k.P["panel"], reason="the perforation round the small stamp, cut in the label's colour")
    fr = dk.box(slide, x + 0.08 * s, y + 0.08 * s, w - 0.16 * s, h - 0.16 * s, fill=None,
                line=dk._as_rgb(k.P["stamp_frame"]), line_w=0.75)
    dk.decorative(fr, "the printed frame inside the small stamp; it only borders the number")


@register(NAME, "quote", alts=2)
def _am_quote(k, slide, f, image):
    """A line from a letter: the quote in an italic letter face, the attribution under it; a postmark at the top right
    with its cancel lines running in from the right."""
    W, H, s, o = ctx(k)
    m = _m(k)
    if o == "land":
        x, w, y0 = m + 0.3 * s, (0.62 if alt() == 0 else 0.74) * W, 0.30 * H
    else:
        x, w, y0 = 0.10 * W, 0.80 * W, (0.30 if alt() == 0 else 0.22) * H
    r, ds = _v2.stack(k, slide, "quote", x, w, y0, H - m,
                      [(_v2.fields(f, ("mark", "quote")), 0.30 * s), (_v2.fields(f, ("attribution",)), 0.0)],
                      anchor="middle")
    pm_d = (1.25 if o == "land" else 1.0) * s
    cx, cy = W - m - pm_d / 2.0 - 0.1 * s, m + pm_d / 2.0
    _run_all(ds)
    _postmark(k, slide, cx, cy, pm_d, waves=min(2.4 * s, cx - pm_d / 2.0 - x - 0.3 * s), side=-1)
    return r


@register(NAME, "data", alts=2)
def _am_data(k, slide, f, image):
    """The number as a stamp's denomination, struck by a postmark; the label and note beside it (under it on a
    portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    r, ds = {}, []
    if o == "land":
        box = (m + 0.2 * s, 0.18 * H, (0.38 if alt() == 0 else 0.32) * W, 0.64 * H)
        col = (box[0] + box[2] + 0.8 * s, 0.16 * H, W - m - box[0] - box[2] - 0.8 * s, 0.68 * H)
    else:
        box = (0.14 * W, m + 0.1 * s, 0.72 * W, (0.36 if alt() == 0 else 0.28) * H)
        col = (0.10 * W, box[1] + box[3] + 0.5 * s, 0.80 * W, H - m - box[1] - box[3] - 0.5 * s)
    stamp = None
    if num:
        nr, nd, stamp = _number_stamp(k, slide, "data", box, num)
        r.update(nr)
        ds.append(nd)
    tr, td = _v2.flow(k, slide, "data", col, _v2.fields(f, ("label", "note")), anchor="middle")
    r.update(tr)
    ds.append(td)
    _run_all(ds)
    if stamp:
        sx, sy, sw, sh_ = stamp
        _postmark(k, slide, sx + sw - 0.05 * s, sy + 0.10 * s, 1.15 * s, waves=0.0)
    return r


@register(NAME, "closing", alts=2)
def _am_closing(k, slide, f, image):
    """The envelope's back: its flap folded down to a wax seal; the title and its line under the seal."""
    W, H, s, o = ctx(k)
    m = _m(k)
    inner = 0.42 * s
    vy = (0.42 if o == "land" else 0.34) * H
    if alt() == 1:
        vy -= 0.06 * H
    seal_d = (1.15 if o == "land" else 1.0) * s
    dk.decorative(na.polyline(slide, [(inner, inner), (W / 2.0, vy), (W - inner, inner)], k.P["ink"], w=1.0, alpha=0.30),
                  "the fold of the envelope's flap: the back of the envelope, nothing to read")
    x, w = (0.14 if alt() == 0 else 0.09) * W, (0.72 if alt() == 0 else 0.82) * W
    r, ds = _v2.stack(k, slide, "closing", x, w, vy + seal_d / 2.0 + 0.45 * s, H - m,
                      [(_v2.fields(f, ("title",)), 0.22 * s), (_v2.fields(f, ("line",)), 0.0)], anchor="middle",
                      align="c")
    _seal(k, slide, W / 2.0, vy, seal_d)
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_airmail(slide, role, index):
    """An ordinary page (a chart, an agenda) inside the envelope: the border is the page's ground (new_slide paints
    it); the content rect inside it, in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.75, 0.70, W - 1.5, H - 1.4)


_card_airmail = vl._card_for(NAME)
