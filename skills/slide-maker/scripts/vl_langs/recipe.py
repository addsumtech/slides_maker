"""recipe — the Recipe card language (食谱卡): its ground painter, its card and its seven pages.

A home cook's index card on a kitchen table: a gingham tablecloth (two translucent band shapes, one per direction — the
crossings darken like woven checks), a cream card with a red header rule and blue ruled lines, washi tape. The cover is
the card with a whisk and a wooden spoon printed on it in line; a section is a recipe-box divider standing in its tin,
the number on its tab; the photo is a snapshot paper-clipped to a card; points are a checklist (or numbered steps) on the
ruled lines; a quote is a yellow note card; the key figure sits on a kitchen timer's dial; the last card is signed with
a heart. The butcher-paper ground lays the same cards on kraft paper, a blue-gingham napkin under one corner (ordinary
pages get the plain paper). Every page PLANS its words first (vl_native2.stack / flow / plan_together:
measured, never under a floor), draws the card and its art from the planned rects, then sets the words — always on a
card, never on the checks. The only words it writes itself are the step numbers 1 2 3 on the points page, and only when
the caller says the points happen in order (ordered=True); otherwise the points get empty tick boxes."""
from __future__ import annotations

import math

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "recipe"

PADX, PADT, PADB = 0.42, 0.34, 0.30      # the card's inner margins, in units of s
RED_DY = 0.07                             # the red header rule under the header's last line
RED_GAP = 0.38                            # header foot -> the first ruled line's words
RULE_DY = 0.03                            # a blue rule under a line of words
BODY_GAP = 0.22                           # a block's foot -> the next block's words (its rule sits in between)
PITCH = 0.40                              # the blank ruled lines' pitch


# ─────────────────────────────────────────── geometry ───────────────────────────────────────────
def _deco(sh, reason, overlap=None):
    if sh is not None:
        dk.decorative(sh, reason)
        if overlap:
            dk.overlap_intent(sh, overlap)
    return sh


def _rot(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (px - cx) * ca - (py - cy) * sa, cy + (px - cx) * sa + (py - cy) * ca) for px, py in pts]


def _clip_axis(pts, lo, hi, axis):
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


def _clip_rect(pts, x0, y0, x1, y1):
    pts = _clip_axis(pts, x0, x1, 0)
    return _clip_axis(pts, y0, y1, 1) if len(pts) >= 3 else []


def _arc(cx, cy, r, a0, a1, n=16):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _fillet(pts, corners, r, n=8):
    """The polygon `pts` with the vertices at the indexes in `corners` rounded to radius r (an arc tangent to both
    edges, the radius cut down where an edge is too short to hold it)."""
    out = []
    for i, p in enumerate(pts):
        if i not in corners:
            out.append(p)
            continue
        a, b = pts[i - 1], pts[(i + 1) % len(pts)]
        u = (a[0] - p[0], a[1] - p[1])
        v = (b[0] - p[0], b[1] - p[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        u, v = (u[0] / lu, u[1] / lu), (v[0] / lv, v[1] / lv)
        ang = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))
        rr = min(r, 0.45 * min(lu, lv) * math.tan(ang / 2.0))
        d = rr / math.tan(ang / 2.0)
        t1, t2 = (p[0] + u[0] * d, p[1] + u[1] * d), (p[0] + v[0] * d, p[1] + v[1] * d)
        bis = (u[0] + v[0], u[1] + v[1])
        lb = math.hypot(*bis) or 1.0
        c = (p[0] + bis[0] / lb * rr / math.sin(ang / 2.0), p[1] + bis[1] / lb * rr / math.sin(ang / 2.0))
        a0, a1 = math.atan2(t1[1] - c[1], t1[0] - c[0]), math.atan2(t2[1] - c[1], t2[0] - c[0])
        while a1 - a0 > math.pi:
            a1 -= 2 * math.pi
        while a0 - a1 > math.pi:
            a1 += 2 * math.pi
        out += _arc(c[0], c[1], rr, a0, a1, n)
    return out


# ─────────────────────────────────────────── the table ───────────────────────────────────────────
def _bands(x0, y0, x1, y1, c, horizontal, origin):
    """The bands of one direction of a gingham: c wide, every 2c, one starting at `origin`, cut to the rect."""
    out = []
    lo, hi = (y0, y1) if horizontal else (x0, x1)
    v = origin - math.ceil((origin - lo) / (2 * c)) * 2 * c
    while v < hi:
        a, b = max(v, lo), min(v + c, hi)
        if b - a > 1e-3:
            out.append([(x0, a), (x1, a), (x1, b), (x0, b)] if horizontal else [(a, y0), (b, y0), (b, y1), (a, y1)])
        v += 2 * c
    return out


def _tablecloth(k, slide):
    """The light ground: a red gingham tablecloth over the whole page — the horizontal bands as one translucent shape,
    the vertical bands as another, so the crossings print darker like woven checks."""
    W, H, s, o = ctx(k)
    c = 0.30 * s
    for horiz, why in ((True, "the gingham tablecloth's horizontal bands"), (False, "the gingham tablecloth's vertical bands")):
        polys = _bands(0.0, 0.0, W, H, c, horiz, (H if horiz else W) / 2.0 - c / 2.0)
        _deco(na.multipoly(slide, polys, k.P["check"], alpha=0.34), why + "; the cloth the card lies on, nothing to read",
              "the tablecloth lies under every card on the page: layered by design")


def _napkin(k, slide):
    """The butcher-paper ground: a blue gingham napkin folded under the bottom-left corner, running off the page."""
    W, H, s, o = ctx(k)
    S = 0.66 * min(W, H)
    cx, cy, deg = 0.10 * S, H - 0.06 * S, 14.0
    sq = [(cx - S / 2, cy - S / 2), (cx + S / 2, cy - S / 2), (cx + S / 2, cy + S / 2), (cx - S / 2, cy + S / 2)]
    base = na.poly(slide, _rot(sq, cx, cy, deg), fill=k.P["napkin"])
    if base is not None:
        _deco(base, "a gingham napkin under the card: the table's furniture, nothing to read",
              "the napkin lies under the cards on the page: layered by design")
        na.soft_shadow(base, blur=0.10, dist=0.03, alpha=0.18)
    c = 0.26 * s
    for horiz, why in ((True, "the napkin's horizontal gingham bands"), (False, "the napkin's vertical gingham bands")):
        polys = [_clip_rect(_rot(p, cx, cy, deg), 0.0, 0.0, W, H)
                 for p in _bands(cx - S / 2, cy - S / 2, cx + S / 2, cy + S / 2, c, horiz, cy if horiz else cx)]
        _deco(na.multipoly(slide, [p for p in polys if len(p) >= 3], k.P["napkin_check"], alpha=0.40),
              why + "; the table's furniture, nothing to read", "the napkin lies under the cards on the page: layered by design")


def _page_card(k):
    """The large card every page on the tablecloth starts with (an ordinary page's chart or table sits on it)."""
    W, H, s, o = ctx(k)
    return (0.45 * s, 0.40 * s, W - 0.90 * s, H - 0.80 * s)


def _ground(k, slide):
    """Every page. On the light ground: the tablecloth, and on it a large card — words are never set on the checks, so
    a chart or a table placed on an ordinary page lands on the card (the composed pages lift it and lay their own cards,
    _table). Butcher paper is the plain kraft itself: a chart reads on it as it is."""
    if k.ground != "kraft":
        _tablecloth(k, slide)
        _card(k, slide, _page_card(k), what="the page's card")


vn.GROUNDS[NAME] = _ground


def _table(k, slide):
    """What a composed page does to the table before it lays its own cards: lifts the page's card off the tablecloth
    (undone if the layout is) — or, on butcher paper, lays the napkin."""
    if k.ground == "kraft":
        _napkin(k, slide)
        return
    x, y, w, h = _page_card(k)
    for sh in list(slide.shapes):
        if (sh.shape_type == 1 and abs(sh.left / 914400.0 - x) < 0.01 and abs(sh.top / 914400.0 - y) < 0.01
                and abs(sh.width / 914400.0 - w) < 0.01 and abs(sh.height / 914400.0 - h) < 0.01):
            vn.remove_tracked(sh._element)
            return


# ─────────────────────────────────────────── paper ───────────────────────────────────────────
def _card(k, slide, rect, fill="panel", *, shadow=True, what="the index card"):
    x, y, w, h = rect
    W, H, s, o = ctx(k)
    b = dk.box(slide, x, y, w, h, fill=k.P[fill], round=True, r=0.05 * s)
    _deco(b, what + " the words are written on; the words carry the meaning",
          "a card lies on the table and over the paper under it: layered by design")
    if shadow:
        na.soft_shadow(b, blur=0.14, dist=0.05, alpha=0.30)
    return b


def _back_card(k, slide, rect, deg, fill="card_back", top=None):
    """An older card under the one in front, turned a little; `top` moves it so its turned outline starts there (kept
    clear of the front card's top edge: two cards starting level read as an uneven row to the delivery lint)."""
    x, y, w, h = rect
    pts = _rot([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], x + w / 2.0, y + h / 2.0, deg)
    if top is not None:
        dy = top - min(p[1] for p in pts)
        pts = [(px, py + dy) for px, py in pts]
    sh = na.poly(slide, pts, fill=k.P[fill])
    if sh is not None:
        _deco(sh, "an older recipe card under the one in front; nothing to read on it",
              "the card in front lies over this one: a stack of cards, layered by design")
        na.soft_shadow(sh, blur=0.12, dist=0.04, alpha=0.22)
    return sh


def _tape(k, slide, cx, cy, L, h, deg, color=None):
    """A strip of washi tape centred on (cx, cy), `deg` from the horizontal, its ends torn in small teeth."""
    W, H, s, o = ctx(k)
    n, t = 5, 0.045 * s
    right = [(L / 2.0 - (t if i % 2 else 0.0), -h / 2.0 + h * i / (n - 1)) for i in range(n)]
    left = [(-L / 2.0 + (t if i % 2 else 0.0), h / 2.0 - h * i / (n - 1)) for i in range(n)]
    pts = _rot([(cx + px, cy + py) for px, py in right + left], cx, cy, deg)
    sh = na.poly(slide, pts, fill=color or k.P["tape"], alpha=0.80)
    return _deco(sh, "washi tape holding the card to the table; nothing to read in it",
                 "tape is laid across the card's edge and the table it holds it to: layered by design")


def _rules(k, slide, x0, x1, ys, *, key="blue_rule", w=0.75, blockers=(), one=False):
    """Printed ruled lines across x0..x1 at each y, broken around `blockers` (a drawing, a photo). One shape per line,
    or one for all of them (`one`, for the blank lines under the last words)."""
    W, H, s, o = ctx(k)
    segs = []
    pad = 0.12 * s
    for y in ys:
        pieces = [(x0, x1)]
        for bx, by, bw, bh in blockers:
            if by - pad <= y <= by + bh + pad:
                nxt = []
                for a, b in pieces:
                    if b <= bx - pad or a >= bx + bw + pad:
                        nxt.append((a, b))
                        continue
                    if a < bx - pad:
                        nxt.append((a, bx - pad))
                    if b > bx + bw + pad:
                        nxt.append((bx + bw + pad, b))
                pieces = nxt
        segs += [((a, y), (b, y)) for a, b in pieces if b - a > 0.30 * s]
    why = ("the card's printed red header rule; it only underlines the heading" if key == "red_rule"
           else "the card's printed ruled lines; they only guide the writing")
    over = "the card's printed lines run under its drawings and pictures: layered by design"
    if one and not blockers:             # broken lines stay one shape per piece: one shape's box would span the gap
        _deco(na.strokes(slide, segs, k.P[key], w=w), why, over)
        return
    for sg in segs:
        _deco(na.strokes(slide, [sg], k.P[key], w=w), why, over)


def _clip(k, slide, cx, top, L, deg=0.0):
    """A paper clip, `L` long, its upper end at `top`, straddling whatever edge it clips (a Gem clip in wire)."""
    W, H, s, o = ctx(k)
    u = L / 3.0
    def P(x, y):
        return (cx + (x - 0.5) * u, top + y * u)
    path = ([P(0.30, 2.05), P(0.30, 0.58)] + [P(0.52 + 0.22 * math.cos(a), 0.58 + 0.22 * math.sin(a))
                                                for a in [math.pi + math.pi * i / 12 for i in range(13)]]
            + [P(0.74, 2.62)] + [P(0.44 + 0.30 * math.cos(a), 2.62 + 0.30 * math.sin(a)) for a in [math.pi * i / 14 for i in range(15)]]
            + [P(0.14, 0.48)] + [P(0.50 + 0.36 * math.cos(a), 0.48 + 0.36 * math.sin(a))
                                 for a in [math.pi + math.pi * i / 14 for i in range(15)]]
            + [P(0.86, 2.30)])
    if deg:
        path = _rot(path, cx, top + L / 2.0, deg)
    for col, wd, al in ((k.P["clip"], 2.6 * s, 1.0), ("FFFFFF", 0.9 * s, 0.55)):
        _deco(na.polyline(slide, path, col, w=wd, alpha=al if al < 1 else None),
              "a paper clip holding the snapshot to the card; nothing to read in it",
              "the clip is clipped over the photo's edge and the card: layered by design")


# ─────────────────────────────────────────── line drawings ───────────────────────────────────────────
def _whisk_lines(base, ang, L):
    """A balloon whisk in line, from the end of its handle `base` along `ang` (radians, y down), `L` long: its wire
    loops, its handle (a closed outline) and the ring it hangs by, as point lists."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (base[0] + ca * u - sa * v, base[1] + sa * u + ca * v)
    Lh, hw, B = 0.40 * L, 0.040 * L, 0.20 * L
    wires = []
    for c in (1.0, 0.62, 0.26):
        side = [(Lh + t * (L - Lh), B * c * math.sin(math.pi * t ** 1.3) ** 0.85) for t in [i / 24.0 for i in range(25)]]
        wires.append([P(u, v) for u, v in side] + [P(u, -v) for u, v in side[::-1]])
    wires.append([P(Lh, 0.0), P(L * 0.985, 0.0)])
    end = [P(0.9 * hw * math.cos(a), 0.9 * hw * math.sin(a)) for a in [-math.pi / 2 - math.pi * i / 10 for i in range(11)]]
    handle = [P(Lh + 0.02 * L, -hw)] + end + [P(Lh + 0.02 * L, hw)]
    ferrule = [P(Lh - 0.06 * L, -hw * 1.04), P(Lh - 0.06 * L, hw * 1.04)]
    ring = [P(-0.07 * L + 0.035 * L * math.cos(a), 0.035 * L * math.sin(a)) for a in [2 * math.pi * i / 20 for i in range(21)]]
    return {"wires": wires, "handle": handle, "lines": [ferrule, ring]}


def _spoon_lines(base, ang, L):
    """A wooden spoon in line, from the end of its handle `base` along `ang`, `L` long: its handle and bowl (closed
    outlines), the hollow of the bowl and the hanging hole, as point lists."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (base[0] + ca * u - sa * v, base[1] + sa * u + ca * v)
    a, b = 0.17 * L, 0.095 * L
    bc = L - a
    neck = bc - a * 0.80
    h0, h1 = 0.032 * L, 0.020 * L
    handle = ([P(neck, -h1), P(0.0, -h0)] + [P(-h0 * math.sin(t), -h0 * math.cos(t)) for t in [math.pi * i / 10 for i in range(11)]]
              + [P(0.0, h0), P(neck, h1)])
    bowl = [P(bc + a * math.cos(t), b * math.sin(t)) for t in [2 * math.pi * i / 40 for i in range(40)]]
    hollow = [P(bc + 0.12 * a + 0.62 * a * math.cos(t), 0.58 * b * math.sin(t))
              for t in [-0.35 * math.pi + 0.7 * math.pi * i / 16 for i in range(17)]]
    hole = [P(0.07 * L + 0.012 * L * math.cos(t), 0.012 * L * math.sin(t)) for t in [2 * math.pi * i / 16 for i in range(17)]]
    return {"shapes": [handle, bowl], "lines": [hollow, hole]}


def _heart_pts(cx, cy, size):
    """A heart `size` tall centred on (cx, cy)."""
    pts = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * size / 32.0, cy + (y + 2.5) * size / 32.0))
    return pts


def _fit_to(parts, box):
    """Scale and move point lists (a nested dict/list of them) so that together they sit centred in box (x, y, w, h)."""
    flat = []

    def walk(v):
        if isinstance(v, dict):
            for x_ in v.values():
                walk(x_)
        elif v and isinstance(v[0], tuple):
            flat.extend(v)
        else:
            for x_ in v:
                walk(x_)
    walk(parts)
    xs, ys = [p[0] for p in flat], [p[1] for p in flat]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    x, y, w, h = box
    sc = min(w / max(1e-6, x1 - x0), h / max(1e-6, y1 - y0))
    ox, oy = x + (w - (x1 - x0) * sc) / 2.0, y + (h - (y1 - y0) * sc) / 2.0

    def tf(v):
        if isinstance(v, dict):
            return {k_: tf(x_) for k_, x_ in v.items()}
        if v and isinstance(v[0], tuple):
            return [(ox + (px - x0) * sc, oy + (py - y0) * sc) for px, py in v]
        return [tf(x_) for x_ in v]
    return tf(parts), sc


def _utensils(k, slide, box):
    """A whisk and a wooden spoon crossed, printed in line in the card's own red, fitted inside `box` (x, y, w, h):
    the spoon lies over the whisk (its outline filled with the card, so the wires behind it do not show through)."""
    W, H, s, o = ctx(k)
    x, y, w, h = box
    tilt = math.radians(36 if w > 1.15 * h else 52)
    L = 10.0
    whisk = _whisk_lines((math.cos(tilt) * L / 2, math.sin(tilt) * L / 2), math.pi + tilt, L)
    spoon = _spoon_lines((-math.cos(tilt) * L / 2, math.sin(tilt) * L / 2), -tilt, L)
    (whisk, spoon), _sc = _fit_to([whisk, spoon], box)
    col = k.P["drawn"]
    lw = max(1.0, 1.5 * s)
    why = "a whisk and a wooden spoon drawn in line on the card: they say this is a kitchen, nothing to read in them"
    over = "the spoon is drawn over the whisk it crosses, on the card's printed lines: layered by design"

    def segs(lines, closed=False):
        out = []
        for ln in lines:
            pts = ln + ln[:1] if closed else ln
            out += [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        return out
    # three shapes, not a dozen: the wires, then the card-coloured fill that hides the wires where the spoon crosses,
    # then every outline (separate small filled parts read as a row of uneven cards to the delivery lint)
    _deco(na.strokes(slide, segs(whisk["wires"] + whisk["lines"]), col, w=lw), why, over)
    _deco(na.multipoly(slide, [whisk["handle"]] + spoon["shapes"], k.P["panel"]), why, over)
    _deco(na.strokes(slide, segs([whisk["handle"]] + spoon["shapes"], closed=True) + segs(spoon["lines"]), col, w=lw),
          why, over)


# ─────────────────────────────────────────── planning on a card ───────────────────────────────────────────
def _plan_card(k, slide, page, card, head, body, *, align="l", start=None, col=None, lead=0.0):
    """PLAN the words on an index card: the `head` fields above the red header rule, then each `body` group on its own
    ruled line. card = (x, y, w, h); col = (x, w) of the text column (default: the card less its margins); `lead`
    inches kept clear above the words (for a drawn mark). Returns (rects, draws, geo): geo["red"] the header rule's y
    (None without a head), geo["rules"] the ys of the rules under the body blocks, geo["foot"] the last words' foot."""
    W, H, s, o = ctx(k)
    x, y, w, h = card
    tx, tw = col or (x + PADX * s, w - 2 * PADX * s)
    head = [it for it in head if it]
    body = [it for it in body if it]
    groups = [(it, RED_GAP * s if i == len(head) - 1 else 0.10 * s) for i, it in enumerate(head)]
    groups += [(it, BODY_GAP * s) for it in body]
    kw = {"start": start} if start else {}
    r, ds = _v2.stack(k, slide, page, tx, tw, y + PADT * s + lead, y + h - PADB * s, groups, anchor="top", align=align,
                      **kw)
    foots = [max(r[f_][1] + r[f_][3] for f_, _t in it if f_ in r) for it, _g in groups]
    red = (foots[len(head) - 1] + RED_DY * s) if head else None
    rules = [foots[i] + RULE_DY * s for i in range(len(head), len(groups))]
    return r, ds, {"red": red, "rules": rules, "foot": max(foots) if foots else y + PADT * s + lead}


def _blank_from(k, card, geo):
    """Where a card's blank ruled lines begin: a pitch under the last rule its words sit on."""
    W, H, s, o = ctx(k)
    last = geo["rules"][-1] if geo["rules"] else geo["red"] if geo["red"] is not None else geo["foot"]
    return last + PITCH * s


def _sizes(ds):
    out = {}
    for d in ds:
        out.update(getattr(d, "sizes", {}))
    return out


def _cut(k, slide, page, card, head, body, *, blank=2, extra=0.0, cy=None, **kw):
    """Plan the words on `card`, then cut the card to them — the words, `blank` empty ruled lines and `extra` inches
    under them — centred on cy (the given card's centre by default) within the room the card was given. Returns
    (card, rects, draws, geo)."""
    W, H, s, o = ctx(k)
    x, y, w, h = card
    r, ds, geo = _plan_card(k, slide, page, card, head, body, **kw)
    need = _blank_from(k, card, geo) + (blank - 1) * PITCH * s + 0.30 * s + extra - y
    if need >= h - 1e-6:
        return card, r, ds, geo
    c = (y + h / 2.0) if cy is None else cy
    ny = min(max(y, c - need / 2.0), y + h - need)
    kw = dict(kw, start=dict(kw.get("start") or {}, **_sizes(ds)))
    r, ds, geo = _plan_card(k, slide, page, (x, ny, w, need), head, body, **kw)
    return (x, ny, w, need), r, ds, geo


def _ruling(k, slide, card, geo, *, blockers=(), red=True, x0=None, x1=None):
    """Draw a card's printing: the red header rule, a rule under every block of words, then blank ruled lines at an even
    pitch down to the card's foot. Returns the y where the blank lines start."""
    W, H, s, o = ctx(k)
    x, y, w, h = card
    a, b = (x if x0 is None else x0), (x + w if x1 is None else x1)
    if red:
        ry = geo["red"] if geo["red"] is not None else y + 0.85 * s
        _rules(k, slide, a, b, [ry], key="red_rule", w=1.6 * max(0.7, s), blockers=blockers)
    if geo["rules"]:
        _rules(k, slide, a, b, geo["rules"], blockers=blockers)
    start = _blank_from(k, card, geo)
    ys, v = [], start
    while v <= y + h - 0.22 * s:
        ys.append(v)
        v += PITCH * s
    _rules(k, slide, a, b, ys, blockers=blockers, one=True)
    return start


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
def _centred(k, wf, hf):
    W, H, s, o = ctx(k)
    w, h = wf * W, hf * H
    return ((W - w) / 2.0, (H - h) / 2.0, w, h)


def _title_start(k, a, design=None, text=None, width=None):
    """The title's starting size: the page's own (`design`) on the designed layout, near its floor on the last one. A
    short Chinese or Japanese title with no clause mark that is a little too wide for one line starts a little smaller
    (down to 70%), on one line — wrapped, "我们街上的树" broke as "我们街 / 上的树"."""
    W, H, s, o = ctx(k)
    if a >= 2:
        return {"title": 30 * s}
    z = (design if design and a == 0 else vl.TYPE[NAME]["title"][0]) * s
    if text and width and dk._has_cjk(text) and len(text) <= 16 and not any(c in text for c in vn._CLAUSE_MARKS):
        room = width * vl.HEADROOM - dk.TEXT_INSET_LR
        nat = _v2._cjk_width(k, "title", text, z)
        if nat > room and nat * 0.70 <= room:
            return {"title": z * room / nat * 0.98}
    return {"title": z} if design and a == 0 else None


@register(NAME, "cover", alts=3)
def _rc_cover(k, slide, f, image):
    """The recipe card itself, taped to the table over an older one: the kicker typed in red and the title written
    above the red header rule, the subtitle on the first ruled line, blank lines below — and a whisk and a wooden spoon
    printed crossed in the card's corner."""
    W, H, s, o = ctx(k)
    a = alt()
    land = o == "land"
    if land:
        card = _centred(k, (0.74, 0.84, 0.90)[a], (0.80, 0.84, 0.88)[a])
    else:
        card = _centred(k, (0.84, 0.88, 0.90)[a], (0.80, 0.86, 0.90)[a])
    head = [_v2.fields(f, ("kicker",), ("kicker",)), _v2.fields(f, ("title",))]
    body = [_v2.fields(f, ("subtitle",))]
    title = text_of(f, "title") or ""
    big = len(title) <= (40 if land else 26) or dk._has_cjk(title) and len(title) <= 16   # a short title set large
    r, ds, geo = _plan_card(k, slide, "cover", card, head, body,
                            start=_title_start(k, a, (60 if land else 64) if big else None, title or None,
                                               card[2] - 2 * PADX * s))
    x, y, w, h = card
    # the utensils: in the blank lines under the words — at the card's right on a landscape card, centred in the free
    # lines of a tall one
    free_top = geo["foot"] + 0.40 * s
    free_h = y + h - 0.32 * s - free_top
    vign = None
    if free_h >= 1.0 * s:
        if land:
            vh = min(free_h, 2.7 * s)
            vw = min(w * 0.40, vh * 1.45)
            vign = (x + w - PADX * s - vw, y + h - 0.32 * s - vh, vw, vh)
        else:
            vh = min(free_h * 0.80, 3.4 * s)
            vw = min(w - 2 * PADX * s, vh * 1.30)
            vign = (x + (w - vw) / 2.0, free_top + (free_h - vh) * 0.55, vw, vh)
    _table(k, slide)
    _back_card(k, slide, (x + 0.30 * s, y - 0.10 * s, w, h), 3.2)
    _card(k, slide, card)
    blk = ()
    if vign:
        bx0 = vign[0] - 0.05 * s if land else x
        blk = [(bx0, vign[1], x + w - bx0, vign[3])]
    _ruling(k, slide, card, geo, blockers=blk)
    if vign:
        _utensils(k, slide, vign)
    _tape(k, slide, x + 0.30 * s, y + 0.06 * s, 1.15 * s, 0.30 * s, -38)
    _tape(k, slide, x + w - 0.30 * s, y + 0.06 * s, 1.15 * s, 0.30 * s, 38)
    _run_all(ds)
    return r


def _divider_pts(x, y, w, h, tx, tw, th, r):
    """A recipe-box divider: the card (x, y, w, h) with a tab rising `th` from its top edge between tx and tx + tw, its
    sides a little slanted, its top corners rounded and its feet eased into the card's edge."""
    sl = min(0.10 * th, 0.12 * tw)
    pts = [(x, y + h), (x, y), (tx, y), (tx + sl, y - th), (tx + tw - sl, y - th), (tx + tw, y), (x + w, y), (x + w, y + h)]
    return _fillet(pts, (1, 2, 3, 4, 5, 6), r)


@register(NAME, "section", alts=3)
def _rc_section(k, slide, f, image):
    """A recipe-box divider standing in its tin: the section number large on the divider's tab, the kicker and the title
    on the divider above the tin's front, an older card standing behind it. The divider is cut to its words (never
    shorter than a card) and the whole box is centred on the page."""
    W, H, s, o = ctx(k)
    a = alt()
    num = text_of(f, "number")
    land = o == "land"
    dx, dw = ((0.12, 0.76) if land else (0.08, 0.84)) if a == 0 else ((0.07, 0.86) if land else (0.06, 0.88))
    dx, dw = dx * W, dw * W
    tin_h = (0.17 if land else 0.11) * H
    pad = 0.34 * s
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.14 * s), (_v2.fields(f, ("title",)), 0.0)]

    def plan(top, text_top, text_bottom, anchor, size=None, tstart=None):
        r, ds, tab = {}, [], None
        if num:
            room_w = min(0.55 * dw, 5.0 * s)
            room_h = (0.30 if land else 0.18) * H
            if size is None:
                size0 = (120, 96, 80)[a] * s
                _nr, nd0 = _v2.flow(k, slide, "section", (dx, top, room_w, room_h), [("number", num)], anchor="top",
                                    align="c", start={"number": size0})
                size = getattr(nd0, "sizes", {}).get("number", size0)
            bw = min(room_w, _v2.ink_w(k, "number", num, size) * 1.06 + 0.14 * s)
            tx = dx + 0.50 * s
            nr, nd = _v2.flow(k, slide, "section", (tx + pad, top + 0.12 * s, bw, room_h), [("number", num)],
                              anchor="top", align="c", start={"number": size})
            nx, ny, nw, nh = nr["number"]
            size = getattr(nd, "sizes", {}).get("number", size)
            body_y = ny + nh + 0.02 * s + 0.05 * size / 72.0
            tab = (tx, nw + 2 * pad, body_y - top)
            r.update(nr)
            ds.append(nd)
        else:
            body_y = top + 0.9 * s
        t0 = body_y + 0.45 * s if text_top is None else text_top
        tr, tds = _v2.stack(k, slide, "section", dx + PADX * s, dw - 2 * PADX * s, t0, text_bottom, groups,
                            anchor=anchor, start=tstart if tstart else _title_start(k, a, None, text_of(f, "title"),
                                                                                    dw - 2 * PADX * s))
        r.update(tr)
        ds += tds
        foot = max((v[1] + v[3] for v in tr.values()), default=t0)
        return r, ds, tab, body_y, foot, size

    # measured from the top of the page, the words as low as the tin allows; then the box cut and centred
    top0 = 0.06 * H
    r, ds, tab, body_y, foot, size = plan(top0, None, H - 0.03 * H - tin_h - 0.30 * s, "top")
    tin_y = max(foot + 0.50 * s, body_y + (2.5 if land else 2.1) * s)
    used = tin_y + tin_h - top0
    shift = max(0.0, (H - used) / 2.0 - top0)
    tsizes = _sizes(ds)
    tin_y += shift
    r, ds, tab, body_y, foot, size = plan(top0 + shift, None, tin_y - 0.30 * s, "middle", size=size,
                                         tstart={f_: z for f_, z in tsizes.items() if f_ != "number"})
    body_h = tin_y + 0.5 * tin_h - body_y
    if tab:
        pts = _divider_pts(dx, body_y, dw, body_h, tab[0], tab[1], tab[2], 0.14 * s)
        off = tab[0] + tab[1] - dx
    else:
        pts = [(dx, body_y + body_h), (dx, body_y), (dx + dw, body_y), (dx + dw, body_y + body_h)]
        off = 0.0
    _table(k, slide)
    if dw - off - 0.50 * s >= 0.8 * s:          # the card behind shows only where the tab leaves room for it
        _back_card(k, slide, (dx + off + 0.35 * s, body_y - 0.34 * s, dw - off - 0.50 * s, body_h), 0.0)
    div = na.poly(slide, pts, fill=k.P["divider"])
    _deco(div, "the recipe-box divider the section's words are written on; the words carry the meaning",
          "the divider stands in the tin, in front of the card behind it: layered by design")
    na.soft_shadow(div, blur=0.12, dist=0.04, alpha=0.26)
    _rules(k, slide, dx, dx + dw, [body_y + 0.20 * s], key="red_rule", w=1.6 * max(0.7, s))
    _tin(k, slide, tin_y, tin_y + tin_h)
    _run_all(ds)
    return r


def _tin(k, slide, y, yb):
    """The front of the recipe tin from y to yb: its enamel, a rolled lip, a highlight and an empty label holder."""
    W, H, s, o = ctx(k)
    x0, x1 = 0.04 * W, 0.96 * W
    b = dk.box(slide, x0, y, x1 - x0, yb - y, fill=k.P["timer"], round=True, r=0.10 * s)
    _deco(b, "the front of the recipe tin the divider stands in; nothing to read on it",
          "the tin's front hides the foot of the divider standing in it: layered by design")
    na.soft_shadow(b, blur=0.14, dist=0.05, alpha=0.30)
    lip = dk.box(slide, x0, y, x1 - x0, 0.11 * s, fill=k.P["timer_dark"], round=True, r=0.05 * s)
    _deco(lip, "the rolled lip of the recipe tin; nothing to read in it",
          "the lip is the top of the tin's front: layered by design")
    gl = na.strokes(slide, [((x0 + 0.35 * s, y + 0.24 * s), (x1 - 0.35 * s, y + 0.24 * s))], "FFFFFF", w=1.6 * s, alpha=0.45)
    _deco(gl, "a highlight along the tin's enamel; nothing to read in it",
          "the highlight lies on the tin's front: layered by design")
    hw, hh = min(2.2 * s, 0.30 * (x1 - x0)), min(0.55 * s, (yb - y) * 0.42)
    hy = y + 0.11 * s + (yb - y - 0.11 * s - hh) / 2.0
    holder = dk.box(slide, (W - hw) / 2.0, hy, hw, hh, fill=None, line=dk._as_rgb(k.P["timer_dark"]), line_w=1.4,
                    round=True, r=0.06 * s)
    _deco(holder, "the tin's empty label holder; nothing is written in it", "the holder is fixed on the tin's front")


@register(NAME, "image_text", alts=3)
def _rc_image_text(k, slide, f, image):
    """The caller's photo clipped to the card as a snapshot — a white border, a paper clip over its top edge, the caption
    typed under it; the kicker and title above the red header rule beside it, the body on the ruled lines (all under the
    photo on a portrait or square page)."""
    W, H, s, o = ctx(k)
    a = alt()
    cap = text_of(f, "caption")
    land = o == "land"
    card = _centred(k, 0.90, 0.86 if land else 0.92)
    x, y, w, h = card
    b = 0.09 * s
    r, ds = {}, []
    head = [_v2.fields(f, ("kicker",), ("kicker",)), _v2.fields(f, ("title",))]
    body = [_v2.fields(f, ("body",))]
    if land:
        pw = (0.44, 0.38, 0.32)[a] * W
        px, py = x + 0.42 * s, y + 0.55 * s
        foot = y + h - PADB * s
        if cap:
            cr, cd = _v2.flow(k, slide, "image_text", (px, foot - 1.2 * s, pw, 1.2 * s), [("caption", cap)],
                              anchor="bottom")
            r.update(cr)
            ds.append(cd)
            foot = min(v[1] for v in cr.values()) - 0.20 * s
        img = (px, py, pw, foot - py)
        cx0 = px + pw + 0.60 * s
        tr, tds, geo = _plan_card(k, slide, "image_text", card, head, body, col=(cx0, x + w - PADX * s - cx0),
                                  start=_title_start(k, a, None, text_of(f, "title"), x + w - PADX * s - cx0))
    else:
        ph = (0.32, 0.26, 0.20)[a] * H
        px, py = x + PADX * s, y + 0.55 * s
        img = (px, py, w - 2 * PADX * s, ph)
        foot = py + ph + b
        if cap:
            cr, cd = _v2.flow(k, slide, "image_text", (px, foot + 0.14 * s, img[2], 1.0 * s), [("caption", cap)])
            r.update(cr)
            ds.append(cd)
            foot = max(v[1] + v[3] for v in cr.values())
        sub = (x, foot + 0.05 * s, w, y + h - foot - 0.05 * s)
        tr, tds, geo = _plan_card(k, slide, "image_text", sub, head, body,
                                  start=_title_start(k, a, None, text_of(f, "title"), w - 2 * PADX * s))
    if img[3] < 1.0 * s:
        raise vl.VLTextOverflow("recipe.image_text(): the caption leaves the photo {:.2f}in".format(img[3]))
    r.update(tr)
    ds = tds + ds
    _table(k, slide)
    _card(k, slide, card)
    # beside the snapshot the card's lines start right of it: the photo and its typed caption keep a clear column
    _ruling(k, slide, card, geo, blockers=[(x, y, img[0] + img[2] + b + 0.10 * s - x, h)] if land else ())
    frame = dk.box(slide, img[0] - b, img[1] - b, img[2] + 2 * b, img[3] + 2 * b, fill="FFFFFF")
    _deco(frame, "the snapshot's white border; the picture itself carries the meaning",
          "the snapshot is clipped over the card's printed lines: layered by design")
    na.soft_shadow(frame, blur=0.10, dist=0.04, alpha=0.26)
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _clip(k, slide, img[0] + 0.22 * img[2], img[1] - b - 0.42 * s, 1.05 * s)
    _run_all(ds)
    return r


def _tickbox(k, slide, x, y, d):
    """An empty tick box at (x, y), d wide."""
    W, H, s, o = ctx(k)
    bx = dk.box(slide, x, y, d, d, fill=None, line=dk._as_rgb(k.P["drawn"]), line_w=1.4 * max(0.75, s))
    _deco(bx, "an empty tick box beside a point, as on a recipe's ingredient list; it holds no mark")


@register(NAME, "points", alts=4)
def _rc_points(k, slide, f, image):
    """The card's list: the kicker and title above the red header rule, each point on its own ruled line — an empty tick
    box beside its head (a step number in a ring when the caller says the points happen in order), its line under it in
    the lighter ink; the card cut to its list and two blank lines. Long copy: a larger card, the title nearer its floor,
    then two columns of points."""
    W, H, s, o = ctx(k)
    a = alt()
    pts = points_of(f.get("items"))
    ordered = f.get("ordered", False)
    if not isinstance(ordered, bool):
        raise TypeError("recipe.points(): ordered= is True or False, got {!r}".format(ordered))
    land = o == "land"
    if land:
        room = _centred(k, (0.72, 0.84, 0.90, 0.92)[a], (0.88, 0.90, 0.92, 0.92)[a])
    else:
        room = _centred(k, (0.86, 0.90, 0.92, 0.92)[a], (0.88, 0.90, 0.92, 0.92)[a])
    plan = _points_plan(k, slide, f, pts, room, room[3], a)
    need = plan["last"] + 2 * PITCH * s + 0.30 * s - room[1]
    if need < room[3] - 1e-6:
        card = (room[0], room[1] + (room[3] - need) * 0.45, room[2], need)
        plan = _points_plan(k, slide, f, pts, card, room[3], a, sizes=plan["sizes"])
    else:
        card = room
    x, y, w, h = card
    marks = []
    for i, (ncx, first, d) in enumerate(plan["marks"]):
        if ordered:
            dd = 0.40 * s
            nr, nd = _v2.flow(k, slide, "points", (ncx - dd / 2.0, first - dd / 2.0, dd, dd), [("item_no", str(i + 1))],
                              anchor="middle", align="c")
            plan["rects"].update(nr)
            marks.append(lambda ncx=ncx, first=first, dd=dd: _deco(
                na.ring(slide, ncx, first, dd, k.P["drawn"], w=1.3 * max(0.75, s)),
                "the ring round a step number, as a cook numbers a method; the number carries the meaning"))
            marks.append(nd)
        else:
            marks.append(lambda ncx=ncx, first=first, d=d: _tickbox(k, slide, ncx - d / 2.0, first - d / 2.0, d))
    _table(k, slide)
    _card(k, slide, card)
    _rules(k, slide, x, x + w, [plan["red"]], key="red_rule", w=1.6 * max(0.7, s))
    for a0, a1, yy in plan["rules"]:
        _rules(k, slide, a0, a1, [yy])
    ys, v = [], plan["last"] + PITCH * s
    while v <= y + h - 0.22 * s:
        ys.append(v)
        v += PITCH * s
    _rules(k, slide, x, x + w, ys, one=True)
    _tape(k, slide, x + w / 2.0, y + 0.02 * s, 1.30 * s, 0.32 * s, -4)
    _run_all(marks + plan["draws"])
    return plan["rects"]


def _points_plan(k, slide, f, pts, card, room_h, a, sizes=None):
    """PLAN the points page on `card`: the header in its share of `room_h`, then the points down one column (two on the
    last layout), measured together at one size per field and shrunk together until they fit. Nothing is drawn."""
    W, H, s, o = ctx(k)
    x, y, w, h = card
    n = len(pts)
    cols = 2 if (a == 3 and n >= 3) else 1
    head = [_v2.fields(f, ("kicker",), ("kicker",)), _v2.fields(f, ("title",))]
    hr, hds, hgeo = _plan_card(k, slide, "points", (x, y, w, (0.36 if a < 2 else 0.42) * room_h), head, [],
                               start=_title_start(k, a, None, text_of(f, "title"), w - 2 * PADX * s))
    top = (hgeo["foot"] + RED_GAP * s) if hr else y + 1.0 * s
    bottom = y + h - PADB * s
    gut = 0.52 * s
    tx, tw = x + PADX * s, w - 2 * PADX * s
    cgap = 0.50 * s
    cw = (tw - (cols - 1) * cgap) / cols
    per = -(-n // cols)
    hl = 0.04 * s                                 # a point's head -> its line
    lined = [i for i, (_hd, ln) in enumerate(pts) if ln]
    T = vl.TYPE[NAME]
    need = None
    for scale in ((None,) if sizes else (1.0, 0.92, 0.85, 0.78, 0.72, 0.66, 0.60, 0.55)):
        st = sizes or {f_: max(T[f_][5] * s, T[f_][0] * s * scale) for f_ in ("item_head", "item_line")}
        ph = _v2.plan_together(k, slide, "points", [((0, 0, cw - gut, bottom - top), [("item_head", hd)],
                                                     {"anchor": "top", "start": st}) for hd, _ln in pts])
        pl = _v2.plan_together(k, slide, "points", [((0, 0, cw - gut, bottom - top), [("item_line", pts[i][1])],
                                                     {"anchor": "top", "start": st}) for i in lined]) if lined else []
        hh = [pr["item_head"][3] for pr, _d in ph]
        lh = {i: pr["item_line"][3] for i, (pr, _d) in zip(lined, pl)}
        st = dict(st, **_sizes([d_ for _p, d_ in ph + pl]))
        rows = [hh[i] + (hl + lh[i] if i in lh else 0.0) for i in range(n)]
        need = max(sum(rows[c * per:(c + 1) * per]) + BODY_GAP * s * (len(rows[c * per:(c + 1) * per]) - 1)
                   for c in range(cols))
        if need <= bottom - top + 1e-6:
            break
    else:
        raise vl.VLTextOverflow("recipe.points(): the points need {:.2f}in, the card has {:.2f}in".format(
            need, bottom - top))
    r = dict(hr)
    ds = list(hds)
    marks, rules = [], []
    for i, (hd, ln) in enumerate(pts):
        c, j = i // per, i % per
        cx0 = tx + c * (cw + cgap)
        yy = top + sum(rows[c * per:c * per + j]) + BODY_GAP * s * j
        hr_, hd_ = _v2.flow(k, slide, "points", (cx0 + gut, yy, cw - gut, hh[i] + 0.05 * s), [("item_head", hd)],
                            anchor="top", start=st)
        r.update(hr_)
        ds.append(hd_)
        foot = max(v[1] + v[3] for v in hr_.values())
        if ln:
            lr_, ld_ = _v2.flow(k, slide, "points", (cx0 + gut, foot + hl, cw - gut, lh[i] + 0.05 * s),
                                [("item_line", ln)], anchor="top", start=st)
            r.update(lr_)
            ds.append(ld_)
            foot = max(v[1] + v[3] for v in lr_.values())
        a0 = cx0 - (PADX * s if c == 0 else 0.20 * s)
        a1 = cx0 + cw + (PADX * s if c == cols - 1 else 0.20 * s)
        rules.append((a0, a1, foot + RULE_DY * s))
        hy = hr_["item_head"][1]
        hsize = getattr(hd_, "sizes", {}).get("item_head", st["item_head"])
        first = hy + 0.028 + hsize / 72.0 * dk._LINT_LINE_H * (dk.CJK_LS if dk._has_cjk(hd) else 1.0) / 2.0
        d = min(0.24 * s, hsize / 72.0 * 0.62)
        marks.append((cx0 + (gut - 0.10 * s) / 2.0, first, d))
    red = hgeo["foot"] + RED_DY * s if hr else y + 0.85 * s
    return {"rects": r, "draws": ds, "marks": marks, "rules": rules, "red": red,
            "last": max(yy for _a, _b, yy in rules), "sizes": st}


def _quote_mark(k, slide, x, y, hgt):
    """An opening quotation mark drawn as two red teardrops, `hgt` tall, its top-left corner at (x, y)."""
    W, H, s, o = ctx(k)
    one = ([(math.cos(t), math.sin(t)) for t in [-math.pi / 2 + math.pi * 1.5 * i / 20 for i in range(21)]]
           + [(-1.02, -0.70), (-0.80, -1.55), (-0.25, -2.25), (0.55, -2.62), (0.62, -2.42), (0.05, -1.95), (-0.18, -1.35)])
    u = hgt / 3.65
    out = []
    for dx in (0.0, 2.55):
        out.append([(x + (px + 1.05 + dx) * u, y + (py + 2.62) * u) for px, py in one])
    _deco(na.multipoly(slide, out, k.P["red_rule"]), "an opening quotation mark printed in red: it says these are "
          "someone's words, nothing to read in it")
    return (x, y, 4.7 * u, hgt)


@register(NAME, "quote", alts=3)
def _rc_quote(k, slide, f, image):
    """A yellow note card taped over a recipe card: a red quotation mark at its head, the quote written in italic on its
    ruled lines, the attribution typed on the next line."""
    W, H, s, o = ctx(k)
    a = alt()
    land = o == "land"
    room = _centred(k, ((0.64 if W / H > 1.6 else 0.72), 0.80, 0.88)[a] if land else (0.84, 0.88, 0.92)[a],
                    (0.84, 0.88, 0.92)[a] if land else (0.76, 0.84, 0.92)[a])
    lead = 0.62 * s
    body = [_v2.fields(f, ("quote",)), _v2.fields(f, ("attribution",))]
    card, r, ds, geo = _cut(k, slide, "quote", room, [], body, blank=2, lead=lead)
    x, y, w, h = card
    _table(k, slide)
    _back_card(k, slide, (x - 0.35 * s, y + 0.25 * s, w, h), -3.0, fill="panel", top=y + 0.30 * s)
    _card(k, slide, card, fill="note", what="the note card")
    _ruling(k, slide, card, geo, red=False)
    _quote_mark(k, slide, x + PADX * s, y + PADT * s - 0.02 * s, 0.50 * s)
    _tape(k, slide, x + 0.25 * s, y + 0.10 * s, 1.15 * s, 0.30 * s, -36)
    _run_all(ds)
    return r


def _timer(k, slide, cx, cy, D):
    """A kitchen timer: its enamel body and ridged twist knob, a cream dial with sixty ticks, the index mark at the
    top."""
    W, H, s, o = ctx(k)
    kw, kh = 0.26 * D, 0.15 * D
    knob = dk.box(slide, cx - kw / 2.0, cy - D / 2.0 - 0.075 * D, kw, kh, fill=k.P["timer_dark"], round=True, r=0.035 * D)
    _deco(knob, "the timer's twist knob; nothing to read in it", "the knob sits behind the timer's body: layered by design")
    ridges = [((cx - kw / 2.0 + kw * (i + 1) / 7.0, cy - D / 2.0 - 0.055 * D), (cx - kw / 2.0 + kw * (i + 1) / 7.0,
                                                                            cy - D / 2.0 + 0.01 * D)) for i in range(6)]
    _deco(na.strokes(slide, ridges, "FFFFFF", w=1.0 * max(0.75, s), alpha=0.35), "the ridges of the timer's knob",
          "the ridges are pressed into the knob: layered by design")
    body = na.disc(slide, cx, cy, D, k.P["timer"], shadow=True)
    _deco(body, "the kitchen timer's enamel body; the figure on its dial carries the meaning",
          "the timer stands on the table: layered by design")
    gloss = _arc(cx, cy, 0.455 * D, math.radians(198), math.radians(252), 14)
    _deco(na.polyline(slide, gloss, "FFFFFF", w=2.2 * s, alpha=0.55), "a highlight on the enamel; nothing to read in it",
          "the highlight lies on the timer's body: layered by design")
    face = na.disc(slide, cx, cy, 0.80 * D, k.P["panel"])
    _deco(face, "the timer's dial face the figure is printed on; the figure carries the meaning",
          "the dial face is set into the timer's body: layered by design")
    rim = na.ring(slide, cx, cy, 0.80 * D, k.P["timer_dark"], w=1.5 * s)
    _deco(rim, "the rim of the timer's dial; nothing to read in it", "the rim edges the dial face: layered by design")
    minor, major = [], []
    for i in range(60):
        t = -math.pi / 2 + 2 * math.pi * i / 60
        r0 = 0.40 * D - 0.03 * D
        r1 = r0 - (0.055 * D if i % 5 == 0 else 0.025 * D)
        (major if i % 5 == 0 else minor).append(((cx + r0 * math.cos(t), cy + r0 * math.sin(t)),
                                                  (cx + r1 * math.cos(t), cy + r1 * math.sin(t))))
    for segs, wd in ((minor, 0.7), (major, 1.6)):
        _deco(na.strokes(slide, segs, k.P["ink"], w=wd * max(0.75, s), alpha=0.75),
              "the timer's minute ticks; a dial's furniture, they mark no value",
              "the ticks are printed on the dial face: layered by design")
    tri = [(cx, cy - 0.405 * D), (cx - 0.035 * D, cy - 0.475 * D), (cx + 0.035 * D, cy - 0.475 * D)]
    _deco(na.poly(slide, tri, fill=k.P["panel"]), "the timer's fixed index mark; it marks no value",
          "the index mark is set on the timer's body: layered by design")


def _dial_fits(k, num, D):
    """The largest size (pt) at which `num` sits on one line inside the ticks of a D-inch timer dial, or None when not
    even its floor size does."""
    W, H, s, o = ctx(k)
    base, _role, _b, _c, _i, floor = vl.TYPE[NAME]["number"]
    R = 0.305 * D
    z = min(base * s, 1.05 * R / 0.72 * 72.0)            # its cap height inside the dial
    lo = max(9.0, floor * s)
    while z >= lo - 1e-6:
        hw = math.sqrt(max(0.0, R * R - (0.40 * z / 72.0) ** 2))
        if _v2.ink_w(k, "number", num, z) / vl.HEADROOM + dk.TEXT_INSET_LR + 0.04 <= 2.0 * hw * 0.98:
            return z
        z *= 0.96
    return None


def _grow_dial(k, num, D, D_max, target):
    """The designed dial `D`, grown only as far as the figure needs to sit inside its ticks at `target` pt (never past
    D_max; at D_max it sits as large as it can there): the least growth leaves the card beside or under it the most
    room."""
    def ok(d):
        z = _dial_fits(k, num, d)
        return z is not None and z >= target - 1e-6
    if not num or ok(D) or D >= D_max:
        return D
    if not ok(D_max):
        return D_max                    # as large as the page allows (or the page refuses it and tries the next)
    lo, hi = D, D_max
    for _i in range(14):
        mid = (lo + hi) / 2.0
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


def _dial_number(k, slide, num, cx, cy, D):
    """PLAN the figure on a D-inch timer dial centred on (cx, cy), as large as fits inside its ticks: (rects, draw), or
    None when it does not fit even at its floor size."""
    z = _dial_fits(k, num, D)
    if z is None:
        return None
    R = 0.305 * D
    hw = math.sqrt(max(0.0, R * R - (0.40 * z / 72.0) ** 2))
    bh = z / 72.0 * 1.35 + 0.10
    return _v2.flow(k, slide, "data", (cx - hw, cy - bh / 2.0, 2.0 * hw, bh), [("number", num)], anchor="middle",
                    align="c", start={"number": z})


@register(NAME, "data", alts=3)
def _rc_data(k, slide, f, image):
    """The figure on a kitchen timer's dial; the label written above the red rule of a card beside it (under it on a
    portrait or square page), the note on its ruled line; the card cut to its words and three blank lines."""
    W, H, s, o = ctx(k)
    a = alt()
    num = text_of(f, "number")
    land = o == "land"
    head, body = [_v2.fields(f, ("label",))], [_v2.fields(f, ("note",))]
    r, ds = {}, []
    # a long figure grows the dial toward this size (a smaller one on each roomier layout, down to the floor)
    target = max(vl.TYPE[NAME]["number"][5], (64, 48, 0)[a]) * s
    if land:
        wide = W / H > 1.6
        D = _grow_dial(k, num, min((0.68, 0.74, 0.78)[a] * H, ((0.40, 0.42, 0.44) if wide else (0.36, 0.38, 0.40))[a] * W),
                       min(0.84 * H, 0.50 * W, 0.51 * W - 0.55 * s), target)   # the card keeps >= 36% of the width
        cx, cy = 0.07 * W + D / 2.0, H / 2.0 + 0.04 * D
        cxl = cx + D / 2.0 + 0.55 * s
        room = (cxl, 0.10 * H, W - 0.06 * W - cxl, 0.80 * H)
        card, tr, tds, geo = _cut(k, slide, "data", room, head, body, blank=3, cy=cy)
    else:
        D = _grow_dial(k, num, min(((0.46, 0.40, 0.34) if W / H > 0.9 else (0.40, 0.36, 0.32))[a] * H, 0.66 * W),
                       min(0.60 * H, 0.84 * W), target)
        lift = 0.08 * D                                     # the knob above the body
        top_room = 0.05 * H + lift + D + 0.40 * s
        room = (0.08 * W, top_room, 0.84 * W, H - 0.05 * H - top_room)
        card, tr, tds, geo = _cut(k, slide, "data", room, head, body, blank=3, cy=room[1])
        total = lift + D + 0.40 * s + card[3]                # the timer and its card, centred as one
        dy = max(0.0, (H - total) / 2.0 - 0.05 * H)
        cx, cy = W / 2.0, 0.05 * H + dy + lift + D / 2.0
        card = (card[0], card[1] + dy, card[2], card[3])
        tr, tds, geo = _plan_card(k, slide, "data", card, head, body, start=_sizes(tds))
    if num:
        dial = _dial_number(k, slide, num, cx, cy, D)
        if dial is None:
            raise vl.VLTextOverflow("recipe.data(): the figure {!r} does not fit a {:.2f}in timer dial at its floor size "
                                    "— trying a roomier layout".format(num, D))
        r.update(dial[0])
        ds.append(dial[1])
    r.update(tr)
    ds += tds
    _table(k, slide)
    _timer(k, slide, cx, cy, D)
    _card(k, slide, card)
    _ruling(k, slide, card, geo)
    _tape(k, slide, card[0] + card[2] - 0.30 * s, card[1] + 0.06 * s, 1.05 * s, 0.28 * s, 36)
    _run_all(ds)
    return r


@register(NAME, "closing", alts=3)
def _rc_closing(k, slide, f, image):
    """The last card: the title written above the red rule, its line on the ruled line under it, all centred, and a
    small red heart printed in the blank lines — the cook's sign-off."""
    W, H, s, o = ctx(k)
    a = alt()
    land = o == "land"
    room = _centred(k, (0.64, 0.76, 0.88)[a] if land else (0.84, 0.88, 0.92)[a],
                    (0.84, 0.88, 0.92)[a] if land else (0.76, 0.84, 0.92)[a])
    head = [_v2.fields(f, ("title",))]
    body = [_v2.fields(f, ("line",))]
    card, r, ds, geo = _cut(k, slide, "closing", room, head, body, blank=3, align="c",
                            start=_title_start(k, a, 56, text_of(f, "title"), room[2] - 2 * PADX * s))
    x, y, w, h = card
    b0 = _blank_from(k, card, geo)
    hs = min(0.50 * s, (y + h - 0.30 * s - b0) * 0.9)
    heart = None
    if hs >= 0.26 * s:
        hy = b0 + (y + h - 0.30 * s - b0) / 2.0 - PITCH * s * 0.5
        heart = (x + w / 2.0 - hs * 0.6, hy - hs * 0.5, hs * 1.2, hs)
    _table(k, slide)
    _back_card(k, slide, (x + 0.30 * s, y - 0.12 * s, w, h), 3.0)
    _card(k, slide, card)
    _ruling(k, slide, card, geo, blockers=[heart] if heart else ())
    if heart:
        hx, hy_, hw_, hh_ = heart
        _deco(na.poly(slide, _heart_pts(hx + hw_ / 2.0, hy_ + hh_ / 2.0, hh_), fill=k.P["red_rule"]),
              "a small heart printed at the foot of the last card: the cook's sign-off, nothing to read in it")
    _tape(k, slide, x + w / 2.0, y + 0.02 * s, 1.30 * s, 0.32 * s, 3)
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_recipe(slide, role, index):
    """An ordinary page (a chart, an agenda): on the tablecloth, the content rect inside the page's card (new_slide laid
    it); on butcher paper, the plain paper. In REFERENCE inches."""
    K = vl.rs._K[0]
    k = _v2.kit_for(NAME, slide)
    W, H, s, o = ctx(k)
    if k.ground == "kraft":
        rw, rh = vl.rs._canvas(slide)
        return (0.75, 0.62, rw - 1.5, rh - 1.24)
    x, y, w, h = _page_card(k)
    return ((x + 0.35 * s) / K, (y + 0.30 * s) / K, (w - 0.70 * s) / K, (h - 0.60 * s) / K)


_card_recipe = vl._card_for(NAME)
