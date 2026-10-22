"""vinyl — the Vinyl record language (黑胶唱片): its ground painter, its card and its seven pages.

A record and its sleeve: the cover is an album front (the title printed on a coloured sleeve, the record sliding out
of it); the section number and the key figure sit on the record's centre label; the points are a track list (A1 A2 …
B1 B2) beside a half record rising from the page's edge; a tonearm rests on the record on the data page. Every page
PLANS its words first (vl_native2.flow / stack: measured, never under a floor), draws its art clear of them, then sets
them. The only words it writes itself are the track numbers (the manifest's derived words)."""
from __future__ import annotations

import math

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "vinyl"
_BLEED = "the record runs off the page's edge on purpose: a record sliding out of view, a cropped album photograph"


def _off(slide, x, y, w, h):
    W, H = na.page_size(slide)
    return x < -0.001 or y < -0.001 or x + w > W + 0.001 or y + h > H + 0.001


def _decl(slide, sh, reason, box):
    if sh is None:
        return None
    dk.decorative(sh, reason)
    dk.overlap_intent(sh, "a record's disc, grooves, sheen and label are layered on each other (and the record lies "
                          "behind its sleeve or photograph) by design")
    if _off(slide, *box):
        dk.bleed_intent(sh, _BLEED)
    return sh


def _rings(slide, cx, cy, radii, color, w, alpha=None, reason="the record's grooves; texture, nothing to read"):
    """Concentric circles as ONE outline shape."""
    radii = [r for r in radii if r > 0.01]
    if not radii:
        return None
    R = max(radii)
    U = na.U
    d = ""
    for r in radii:
        pts = [((cx + r * math.cos(2 * math.pi * i / 72) - (cx - R)) / (2 * R) * U,
                (cy + r * math.sin(2 * math.pi * i / 72) - (cy - R)) / (2 * R) * U) for i in range(72)]
        d += "<a:moveTo>{}</a:moveTo>".format(na.orn._pt(*pts[0])) + \
             "".join("<a:lnTo>{}</a:lnTo>".format(na.orn._pt(*p)) for p in pts[1:]) + "<a:close/>"
    sh = na._custom(slide, cx - R, cy - R, 2 * R, 2 * R, '<a:path w="{u}" h="{u}" fill="none">{d}</a:path>'.format(
        u=U, d=d), line=na.hexstr(color), line_w=w)
    if alpha is not None:
        from pptx.oxml.ns import qn
        clr = sh._element.spPr.find(qn("a:ln")).find(qn("a:solidFill"))[0]
        clr.append(clr.makeelement(qn("a:alpha"), {"val": str(int(alpha * 100000))}))
    return _decl(slide, sh, reason, (cx - R, cy - R, 2 * R, 2 * R))


def _disc(slide, cx, cy, d, fill, reason):
    return _decl(slide, na.disc(slide, cx, cy, d, fill), reason, (cx - d / 2, cy - d / 2, d, d))


def _record(k, slide, cx, cy, d, *, label_frac=0.34, label=None, hole=True):
    """A record at (cx, cy): the black disc, its grooves (finer rings and the brighter bands between tracks), two soft
    sheens, the centre label and the spindle hole. Returns the label's radius."""
    W, H, s, o = ctx(k)
    R = d / 2.0
    lr = R * label_frac
    _disc(slide, cx, cy, d, k.P["record"], "the record's black disc: the record is the picture, nothing to read")
    step = 0.05 * s
    radii, r = [], R * 0.975
    while r > lr * 1.12:
        radii.append(r)
        r -= step
    _rings(slide, cx, cy, radii, k.P["groove"], 0.35)
    _rings(slide, cx, cy, [R * f for f in (0.93, 0.80, 0.66, 0.53) if R * f > lr * 1.2], k.P["groove_gap"], 1.1,
           reason="the brighter bands between the record's tracks; texture, nothing to read")
    for a0 in (0.55, 0.55 + math.pi):
        pts = [(cx + lr * 1.15 * math.cos(a0 + t), cy + lr * 1.15 * math.sin(a0 + t)) for t in (0.0, 0.32)] + \
              [(cx + R * 0.96 * math.cos(a0 + 0.38 - t * 0.38 / 8), cy + R * 0.96 * math.sin(a0 + 0.38 - t * 0.38 / 8))
               for t in range(9)]
        sh = na.poly(slide, pts, fill="FFFFFF", alpha=0.07)
        _decl(slide, sh, "light catching the record's grooves; texture, nothing to read", (0, 0, 0.1, 0.1))
    _disc(slide, cx, cy, 2 * lr, label or k.P["label"], "the record's centre label; what is printed on it carries the meaning")
    _rings(slide, cx, cy, [lr * 0.86], k.P["label_ink"], 0.6, alpha=0.35,
           reason="the printed ring on the record's label; ornament, nothing to read")
    if hole:                          # a label carrying a number gives its centre to the number
        _disc(slide, cx, cy, max(0.10 * s, d * 0.022), k.P["ground"], "the record's spindle hole")
    return lr


def _sleeve(k, slide, x, y, S):
    b = dk.box(slide, x, y, S, S, fill=k.P["sleeve"])
    dk.decorative(b, "the album sleeve the title is printed on; the title carries the meaning")
    na.soft_shadow(b, blur=0.14, dist=0.06, alpha=0.35)
    return b


def _tonearm(k, slide, cx, cy, R):
    """A tonearm resting on the record: its pivot beyond the record's top right, the arm, the headshell on a groove."""
    W, H, s, o = ctx(k)
    px = min(W - 0.55 * s, cx + R * 1.02)
    py = max(0.55 * s, cy - R * 0.92)
    _disc(slide, px, py, 0.62 * s, k.P["arm_dark"], "the tonearm's pivot base; part of the record player, nothing to read")
    _disc(slide, px, py, 0.32 * s, k.P["arm"], "the tonearm's pivot; part of the record player, nothing to read")
    ex, ey = px - 0.10 * R, py + 0.95 * R
    hx, hy = cx + R * 0.45, cy + R * 0.45
    arm = na.polyline(slide, [(px, py), (ex, ey), (hx, hy)], k.P["arm"], w=4.5 * s)
    dk.decorative(arm, "the tonearm; part of the record player, nothing to read")
    a = math.atan2(hy - ey, hx - ex)
    ca, sa = math.cos(a), math.sin(a)
    L, Wd = 0.42 * s, 0.22 * s
    pts = [(hx + ca * dx - sa * dy, hy + sa * dx + ca * dy) for dx, dy in ((-0.05 * s, -Wd / 2), (L, -Wd / 2), (L, Wd / 2),
                                                                      (-0.05 * s, Wd / 2))]
    head = na.poly(slide, pts, fill=k.P["arm_dark"])
    dk.decorative(head, "the tonearm's headshell; part of the record player, nothing to read")


def _m(k):
    W, H, s, o = ctx(k)
    return 0.62 * s


def _number_on_label(k, slide, page, cx, cy, lr, num, start=None):
    """PLAN the number inside the label (in the label's ink)."""
    W, H, s, o = ctx(k)
    side = lr * 1.30
    kw = {"anchor": "middle", "align": "c", "ink": k.P["label_ink"]}
    if start:
        kw["start"] = start
    return _v2.flow(k, slide, page, (cx - side / 2.0, cy - side / 2.0, side, side), [("number", num)], **kw)


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=2)
def _vy_cover(k, slide, f, image):
    """An album front: the kicker, the title and the subtitle printed on a coloured sleeve; the record sliding out of
    it to the right (out of its foot on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    if o == "land":
        S = min((0.78 if alt() == 0 else 0.86) * H, (0.46 if alt() == 0 else 0.56) * W)
        peek = 0.46 if alt() == 0 else 0.36
        sx, sy = (W - S * (1 + peek)) / 2.0, (H - S) / 2.0
        rc = (sx + S * (0.52 + peek), sy + S / 2.0)
    else:
        peek = 0.42 if alt() == 0 else 0.30
        S = min(0.84 * W, (H - 2 * m) / (1 + peek))
        sx, sy = (W - S) / 2.0, (H - S * (1 + peek)) / 2.0
        rc = (sx + S / 2.0, sy + S * (0.52 + peek))
    pad = 0.42 * s
    ink = dict(ink=k.P["sleeve_ink"], accent=k.P["sleeve_ink"], mute=k.P["sleeve_ink"])
    r, ds = {}, []
    kick = text_of(f, "kicker")
    top = sy + pad
    if kick:
        kr, kd = _v2.flow(k, slide, "cover", (sx + pad, sy + pad, S - 2 * pad, 0.9 * s), [("kicker", _v2.caps(kick))],
                          **ink)
        r.update(kr)
        ds.append(kd)
        top = max(v[1] + v[3] for v in kr.values()) + 0.3 * s
    tr, tds = _v2.stack(k, slide, "cover", sx + pad, S - 2 * pad, max(top, sy + S * (0.22 if alt() == 0 else 0.0)),
                        sy + S - pad,
                        [(_v2.fields(f, ("title",)), 0.20 * s), (_v2.fields(f, ("subtitle",)), 0.0)], anchor="middle",
                        **ink)
    r.update(tr)
    ds += tds
    _record(k, slide, rc[0], rc[1], S * 0.94)
    _sleeve(k, slide, sx, sy, S)
    _run_all(ds)
    return r


@register(NAME, "section", alts=2)
def _vy_section(k, slide, f, image):
    """A record seen close, running off the left edge: the section number on its centre label; the kicker and title
    beside it (under it, the record running off the top, on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    if o == "land":
        d = (1.05 if alt() == 0 else 0.90) * H
        cx, cy = 0.20 * W - (0.0 if alt() == 0 else 0.03 * W), H / 2.0
        col = (cx + d / 2.0 + 0.6 * s, 0.16 * H, W - m - cx - d / 2.0 - 0.6 * s, 0.68 * H)
    else:
        d = min((0.95 if alt() == 0 else 0.80) * W, (0.62 if alt() == 0 else 0.52) * H)
        cx, cy = W / 2.0, d * 0.40
        col = (0.10 * W, cy + d / 2.0 + 0.5 * s, 0.80 * W, H - m - cy - d / 2.0 - 0.5 * s)
    lr = _record(k, slide, cx, cy, d, label_frac=0.40, hole=not num)
    r, ds = {}, []
    if num:
        nr, nd = _number_on_label(k, slide, "section", cx, cy, lr, num, start={"number": 120 * s})
        r.update(nr)
        ds.append(nd)
    tr, tds = _v2.stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3],
                        [(_v2.fields(f, ("kicker",), ("kicker",)), 0.15 * s), (_v2.fields(f, ("title",)), 0.0)],
                        anchor="middle", align="l" if o == "land" else "c")
    r.update(tr)
    _run_all(ds + tds)
    return r


@register(NAME, "image_text", alts=3)
def _vy_image_text(k, slide, f, image):
    """The caller's picture as a square album photograph, its record sliding out behind it; the caption under it, the
    kicker, title and body beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    cap = text_of(f, "caption")
    if o == "land":
        S = min((0.66, 0.58, 0.50)[alt()] * H, 0.38 * W)
        sx, sy = m + 0.2 * s, (H - S) / 2.0 - (0.35 * s if cap else 0.0)
    else:
        S = min((0.62, 0.52, 0.40)[alt()] * W, (W - 2 * m) / 1.40, (0.36, 0.30, 0.24)[alt()] * H)
        sx, sy = m + 0.1 * s, m + 0.1 * s
    rd = S * 0.92
    rc = (sx + S * 0.88, sy + S - rd / 2.0 + 0.04 * S)  # its foot just past the photograph's: a credit on the picture
                                                         # sits inside the record's outline, never across its edge
    r, ds = {}, []
    foot = sy + S
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (sx, sy + S + 0.22 * s, S, 0.9 * s), [("caption", cap)])
        r.update(cr)
        ds.append(cd)
        foot = max(v[1] + v[3] for v in cr.values())
    if o == "land":
        x0 = rc[0] + rd / 2.0 + 0.5 * s
        col = (x0, 0.14 * H, W - m - x0, 0.72 * H)
    else:
        col = (0.10 * W, foot + 0.40 * s, 0.80 * W, H - m - foot - 0.40 * s)
    tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                        [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
                         (_v2.fields(f, ("body",)), 0.0)], anchor="middle")
    r.update(tr)
    _record(k, slide, rc[0], rc[1], rd)
    vl._place_image(k, slide, image, (sx, sy, S, S), vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(tds + ds)
    return r


def _track_nos(n):
    a = -(-n // 2)
    return ["A{}".format(i + 1) for i in range(a)] + ["B{}".format(i + 1) for i in range(n - a)]


@register(NAME, "points", alts=3)
def _vy_points(k, slide, f, image):
    """A track list: A1 A2 … B1 B2 — the first half of the points on side A, the rest on side B — each track its head
    and its line, a rule between tracks, a wider gap between the sides; a half record rising from the page's left
    edge (its top on a portrait or square page). Long copy: a smaller record, then no record."""
    W, H, s, o = ctx(k)
    m = _m(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    nos = _track_nos(n)
    rec = alt() < 2
    if o == "land":
        d = (0.96 if alt() == 0 else 0.78) * H
        cx, cy = 0.02 * W, H / 2.0
        x0 = (cx + d / 2.0 + 0.6 * s) if rec else m + 0.3 * s
        y0, y1 = m, H - m
    else:
        d = (0.92 if alt() == 0 else 0.74) * W
        cx, cy = W / 2.0, 0.02 * H
        x0 = m + 0.2 * s
        y0, y1 = ((cy + d / 2.0 + 0.4 * s) if rec else m), H - m
    w0 = W - m - x0
    r, ds = _v2.stack(k, slide, "points", x0, w0, y0, y0 + 0.30 * H,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", start=None if alt() == 0 else {"title": 46 * s})
    top = max((v[1] + v[3] for v in r.values()), default=y0) + (0.35 if alt() == 0 else 0.25) * s
    nw = 0.80 * s
    gap, side_gap = 0.20 * s, 0.42 * s
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    a = -(-n // 2)
    cgap = 0.5 * s

    def _plan(two):
        """The track list in one column, or (two) side A and side B side by side: (sides, column width, extra gap,
        heights, block height)."""
        sides = [list(range(a)), list(range(a, n))] if two else [list(range(n))]
        cw = (w0 - cgap) / 2.0 if two else w0
        extra = (side_gap - gap) if (not two and n > a) else 0.0     # one column: the wider gap between the sides
        share = min((y1 - top - gap * (len(g) - 1) - extra) / len(g) for g in sides if g) - 0.05 * s
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - nw, share), it, {"anchor": "top"}) for it in items])
        hs = [max((v[1] + v[3] for v in pr.values()), default=0.0) + 0.05 * s for pr, _d in probe]
        return sides, cw, extra, hs, max(sum(hs[i] for i in g) + gap * (len(g) - 1) + extra for g in sides if g)

    # with no record the sleeve's two columns are tried when one column does not fit: side A left, side B right
    two_ok = not rec and n >= 2 and (w0 - cgap) / 2.0 - nw >= 1.4 * s
    try:
        sides, cw, extra, hs, block = _plan(False)
    except vl.VLTextOverflow:
        if not two_ok:
            raise
        block = float("inf")
    if block > y1 - top + 1e-6 and two_ok:
        sides, cw, extra, hs, block = _plan(True)
    two = len(sides) == 2
    if block > y1 - top + 1e-6:
        raise vl.VLTextOverflow("vinyl.points(): the track list needs {:.2f}in, the page has {:.2f}in".format(
            block, y1 - top))
    xs, ys = [x0] * n, [0.0] * n
    for gi, g in enumerate(sides):
        y = top + (y1 - top - block) * 0.35                             # the two sides start level
        for i in g:
            xs[i], ys[i] = x0 + gi * (cw + cgap), y
            y += hs[i] + (side_gap if (not two and i == a - 1) else gap)
    planned = _v2.plan_together(k, slide, "points", [((xs[i] + nw, ys[i], cw - nw, hs[i] + 0.1 * s), it,
                                                      {"anchor": "top"}) for i, it in enumerate(items)])
    numbers = [_v2.flow(k, slide, "points", (xs[i], ys[i] + 0.04 * s, nw - 0.1 * s, 0.5 * s), [("item_no", nos[i])],
                        anchor="top") for i in range(n)]
    art = []
    if rec:
        art.append(lambda: _record(k, slide, cx, cy, d))
    for g in sides:
        for i in g[1:]:
            strong = not two and i == a
            yl = ys[i] - (side_gap if strong else gap) / 2.0
            art.append(lambda yl=yl, xl=xs[i], strong=strong: dk.decorative(
                na.strokes(slide, [((xl, yl), (xl + cw, yl))], k.P["ink"], w=1.2 if strong else 0.5,
                           alpha=0.55 if strong else 0.25),
                "the rule between two tracks (the stronger one between side A and side B)"))
    for (pr, pd), (nr, nd) in zip(planned, numbers):
        r.update(pr)
        r.update(nr)
        ds += [pd, nd]
    _run_all(art + ds)
    return r


@register(NAME, "quote", alts=2)
def _vy_quote(k, slide, f, image):
    """Liner notes: the quote in an italic display serif and its attribution; a record turning in from the page's
    bottom right corner."""
    W, H, s, o = ctx(k)
    m = _m(k)
    d = (0.95 * H if o == "land" else 0.95 * W) * (1.0 if alt() == 0 else 0.8)
    R = d / 2.0
    if o == "land":
        x, w, y0, y1 = m + 0.3 * s, min(0.62 * W, W - R - m - 0.6 * s), 0.14 * H, H - m
    else:
        x, w, y0, y1 = 0.10 * W, 0.80 * W, 0.12 * H, H - R - 0.4 * s
    r, ds = _v2.stack(k, slide, "quote", x, w, y0, y1,
                      [(_v2.fields(f, ("mark", "quote")), 0.30 * s), (_v2.fields(f, ("attribution",)), 0.0)],
                      anchor="middle")
    _record(k, slide, W, H, d)
    _run_all(ds)
    return r


@register(NAME, "data", alts=3)
def _vy_data(k, slide, f, image):
    """The number printed on the record's centre label, the tonearm resting on the record; the label and the note
    beside it (under it on a portrait or square page). A figure too wide for the label (1,250,000): the label stays
    plain and the figure is set at the head of the column instead."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    on_label = alt() < 2
    if o == "land":
        d = (0.84 if alt() == 0 else 0.74 if alt() == 1 else 0.66) * H
        cx, cy = m + d / 2.0, H / 2.0
        col = (cx + d / 2.0 + 1.1 * s, 0.16 * H, W - m - cx - d / 2.0 - 1.1 * s, 0.68 * H)
    else:
        d = (0.80 if alt() == 0 else 0.66 if alt() == 1 else 0.50) * W
        cx, cy = W / 2.0 - 0.3 * s, m + d / 2.0
        col = (0.10 * W, cy + d / 2.0 + 0.5 * s, 0.80 * W, H - m - cy - d / 2.0 - 0.5 * s)
    lr = _record(k, slide, cx, cy, d, label_frac=0.50, hole=not (num and on_label))
    _tonearm(k, slide, cx, cy, d / 2.0)
    r, ds = {}, []
    if num and on_label:
        nr, nd = _number_on_label(k, slide, "data", cx, cy, lr, num)
        r.update(nr)
        ds.append(nd)
    tr, td = _v2.flow(k, slide, "data", col, _v2.fields(f, ("label", "note") if on_label else ("number", "label", "note")),
                      anchor="middle")
    r.update(tr)
    _run_all(ds + [td])
    return r


@register(NAME, "closing", alts=2)
def _vy_closing(k, slide, f, image):
    """The run-out: a record rising from the page's foot like a sun; the title and its line above it."""
    W, H, s, o = ctx(k)
    m = _m(k)
    d = (0.95 * H if o == "land" else 0.95 * W) * (1.0 if alt() == 0 else 0.82)
    R = d / 2.0
    cy = H + 0.05 * R
    x, w = (0.14 if alt() == 0 else 0.09) * W, (0.72 if alt() == 0 else 0.82) * W
    r, ds = _v2.stack(k, slide, "closing", x, w, m, cy - R - 0.35 * s,
                      [(_v2.fields(f, ("title",)), 0.22 * s), (_v2.fields(f, ("line",)), 0.0)], anchor="middle",
                      align="c")
    _record(k, slide, W / 2.0, cy, d)
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_vinyl(slide, role, index):
    """An ordinary page (a chart, an agenda): the sleeve's plain ground; the content rect in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


_card_vinyl = vl._card_for(NAME)
