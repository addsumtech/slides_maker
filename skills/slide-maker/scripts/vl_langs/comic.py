"""comic — the Comic panels language (漫画分镜): its ground painter, its card and its seven pages.

A printed comic-book page: heavy panel borders with gutters of bare paper between them, Ben-Day halftone dots in the
printed primaries, yellow caption boxes, speech balloons with tails, focus lines and a jagged burst. The cover is a
comic's front (a masthead band, the title in a caption block on a burst, focus lines); a section is a splash panel with
its number in a burst; the picture is a panel of its own; the points are one panel each; the quote is one big balloon
whose tail points at the speaker; the key number bursts out of its panel; the last page is a final wide panel. Every
page PLANS its words first (vl_native2.flow: measured, never under a floor), cuts its boxes and balloons to them,
draws the art clear of them, then sets them. It writes no word of its own."""
from __future__ import annotations

import math
import random

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "comic"


def _caps(t):
    return _v2.caps(t)


# ─────────────────────────────────────────── geometry ───────────────────────────────────────────
def _m(k):
    """The page margin round the panel grid."""
    return 0.34 * ctx(k)[2]


def _g(k):
    """The gutter between two panels."""
    return 0.17 * ctx(k)[2]


def _lw(k):
    """A panel border's weight (pt)."""
    return 2.6 * ctx(k)[2]


def _ow(k):
    """The outline of a caption box, a balloon or a burst (pt)."""
    return 1.7 * ctx(k)[2]


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _inset(rect, d):
    x, y, w, h = rect
    return (x + d, y + d, w - 2 * d, h - 2 * d)


def _grow(rect, d):
    return _inset(rect, -d)


def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def _union(rects):
    xs = [r[0] for r in rects] + [r[0] + r[2] for r in rects]
    ys = [r[1] for r in rects] + [r[1] + r[3] for r in rects]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def _orient(clip):
    a = sum(clip[i - 1][0] * clip[i][1] - clip[i][0] * clip[i - 1][1] for i in range(len(clip)))
    return 1.0 if a > 0 else -1.0


def _side(a, b, p, sg):
    return sg * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]))


def _clip(pts, clip):
    """Sutherland–Hodgman: the polygon `pts` cut to the CONVEX polygon `clip` (either winding)."""
    sg = _orient(clip)
    out = list(pts)
    for i in range(len(clip)):
        a, b = clip[i - 1], clip[i]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            sp, sq = _side(a, b, p, sg), _side(a, b, q, sg)
            if sq >= 0:
                if sp < 0:
                    t = sp / (sp - sq)
                    out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
                out.append(q)
            elif sp >= 0:
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _inside(clip, pts):
    sg = _orient(clip)
    return all(_side(clip[i - 1], clip[i], p, sg) >= 0 for i in range(len(clip)) for p in pts)


def _hits(cx, cy, r, rect):
    x, y, w, h = rect
    nx, ny = min(max(cx, x), x + w), min(max(cy, y), y + h)
    return (cx - nx) ** 2 + (cy - ny) ** 2 < r * r


def _dist(p, rect):
    x, y, w, h = rect
    return math.hypot(p[0] - min(max(p[0], x), x + w), p[1] - min(max(p[1], y), y + h))


def _ray_rect(fx, fy, c, s_, rect):
    """The interval (t_in, t_out) along the ray (fx, fy) + t(c, s_) inside `rect`, or None."""
    x, y, w, h = rect
    lo, hi = -1e9, 1e9
    for p, d, a, b in ((fx, c, x, x + w), (fy, s_, y, y + h)):
        if abs(d) < 1e-12:
            if p < a or p > b:
                return None
            continue
        t1, t2 = (a - p) / d, (b - p) / d
        lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
    return (lo, hi) if lo < hi else None


# ─────────────────────────────────────────── drawing ───────────────────────────────────────────
def _poly(slide, pts, fill, reason, *, line=None, lw=0.75, alpha=None, overlap=None):
    sh = na.poly(slide, pts, fill=fill, line=line, line_w=lw, alpha=alpha)
    if sh is not None:
        dk.decorative(sh, reason)
        if overlap:
            dk.overlap_intent(sh, overlap)
    return sh


def _multi(slide, polys, fill, reason, *, alpha=None):
    sh = na.multipoly(slide, polys, fill, alpha=alpha)
    if sh is not None:
        dk.decorative(sh, reason)
    return sh


def _panel_fill(k, slide, pts, fill):
    return _poly(slide, pts, fill, "the inside of a comic panel; the words and drawing in it carry the meaning")


def _panel_line(k, slide, pts):
    return _poly(slide, pts, None, "a comic panel's heavy border: it frames the panel, nothing to read in it",
                 line=k.P["line"], lw=_lw(k))


def _box(k, slide, rect, fill, *, overlap=None):
    """A caption box: a flat colour block with a black (on noir: paper) outline."""
    return _poly(slide, _rect(*rect), fill, "a caption box: the ground its words sit on; the words carry the meaning",
                 line=k.P["line"], lw=_ow(k), overlap=overlap)


def _dots(k, slide, clip, color, src, reach, *, axis=None, pitch=None, rmax=None, keep=(), pad=None, alpha=None,
          gamma=1.0):
    """Ben-Day dots inside the convex polygon `clip`, on a 45-degree screen: largest at `src` and shrinking to nothing
    `reach` inches from it — round it, or along the unit vector `axis` (a straight tone ramp) — every dot whole inside
    `clip` and clear of the `keep` rects. With reach=None, `src` is a list of (src, reach): ONE screen, each dot as
    large as its nearest source makes it — one shape, as a printed tone is one plate (two separate fields of a size
    side by side were read by the lint as a row of uneven cards)."""
    W, H, s, o = ctx(k)
    sources = [(src, reach)] if reach is not None else list(src)
    sources = [(p_, r_) for p_, r_ in sources if r_ > 0.2 * s]
    if not sources:
        return None
    pitch = pitch or 0.20 * s
    rmax = min(rmax or 0.34 * pitch, 0.36 * pitch)
    pad = 0.07 * s if pad is None else pad
    x0, y0, w, h = _bbox(clip)
    polys, j, y = [], 0, y0 + pitch * 0.25
    while y < y0 + h:
        x = x0 + pitch * 0.25 + (j % 2) * pitch / 2.0
        while x < x0 + w:
            f = 0.0
            for (sx_, sy_), rc in sources:
                if axis:
                    d = max(0.0, (x - sx_) * axis[0] + (y - sy_) * axis[1])
                else:
                    d = math.hypot(x - sx_, y - sy_)
                f = max(f, 1.0 - d / rc)
            r = rmax * f ** gamma if f > 0 else 0.0
            if r >= 0.011 * s and _inside(clip, [(x - r, y), (x + r, y), (x, y - r), (x, y + r)]) \
                    and not any(_hits(x, y, r + pad, kr) for kr in keep):
                n = 8 if r < 0.05 * s else 12
                polys.append([(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n))
                              for i in range(n)])
            x += pitch
        y += pitch / 2.0
        j += 1
    return _multi(slide, polys, color, "Ben-Day halftone dots, the printed tone of a comic panel; texture, nothing to "
                                       "read in them", alpha=alpha)


def _reach(src, rects, cap, gap):
    """How far a dot field from `src` may reach and still fade out `gap` short of every rect (words set on the bare
    panel): the tone dies away before the words, never cut off by them."""
    return min([cap] + [_dist(src, r) - gap for r in rects])


def _focus(k, slide, area, focus, clear, color, *, n=56, seed=1, keep=(), w0=None, alpha=None, reach=(1.0, 1.55)):
    """Focus lines: thin wedges from the edges of `area` (x, y, w, h) toward `focus`, stopping round the ellipse
    `clear` (rx, ry) about it — a little further out each, as an inker draws them — and short of every `keep` rect."""
    W, H, s, o = ctx(k)
    x, y, w, h = area
    fx, fy = focus
    rx, ry = clear
    rnd = random.Random(seed)
    w0 = 0.05 * s if w0 is None else w0
    box = _rect(*area)
    polys = []
    for i in range(n):
        th = 2 * math.pi * (i + rnd.uniform(-0.38, 0.38)) / n
        c, sn = math.cos(th), math.sin(th)
        iv = _ray_rect(fx, fy, c, sn, area)
        if iv is None or iv[1] <= 0:
            continue
        tb = iv[1]
        ts = rnd.uniform(*reach) / math.sqrt((c / max(rx, 1e-3)) ** 2 + (sn / max(ry, 1e-3)) ** 2)
        skip = False
        for _pass in range(4):
            moved = False
            for kr in keep:
                kv = _ray_rect(fx, fy, c, sn, kr)
                if kv is None or kv[1] <= ts or kv[0] >= tb:
                    continue
                if kv[1] >= tb - 0.05 * s:
                    skip = True
                    break
                ts, moved = kv[1], True
            if skip or not moved:
                break
        if skip or tb - ts < 0.30 * s:
            continue
        hw = w0 * rnd.uniform(0.40, 1.0)
        bx, by = fx + c * tb, fy + sn * tb
        tip = (fx + c * ts, fy + sn * ts)
        wedge = _clip([(bx - sn * hw, by + c * hw), (bx + sn * hw, by - c * hw), tip], box)
        if len(wedge) >= 3:
            polys.append(wedge)
    return _multi(slide, polys, color, "focus lines drawn toward the panel's subject: a comic's emphasis, nothing to "
                                       "read in them", alpha=alpha)


def _burst_pts(cx, cy, rx, ry, *, n, spike, seed, rot=0.0):
    """A jagged burst: `n` spikes reaching `spike` (x 0.55–1.0) past the ellipse (rx, ry), its valleys ON the ellipse —
    so whatever the ellipse holds, the burst holds."""
    rnd = random.Random(seed)
    pts = []
    for i in range(2 * n):
        a = rot + math.pi * i / n + rnd.uniform(-0.20, 0.20) * math.pi / n
        if i % 2 == 0:
            e = spike * rnd.uniform(0.55, 1.0)
            pts.append((cx + (rx + e) * math.cos(a), cy + (ry + e) * math.sin(a)))
        else:
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _burst_fit(iw, ih, n):
    """The ellipse (rx, ry) whose burst valleys (n of them, jittered) hold an iw x ih rect, with a little air."""
    c = math.cos(1.2 * math.pi / n) / 1.07          # the valleys' polygon holds the ellipse scaled by cos(gap / 2)
    q = min(1.0, max(0.58, 1.5 * ih / max(iw, 1e-6)))   # a wide figure gets a wide burst, never flatter than 0.58
    rx = math.sqrt((iw / 2.0) ** 2 + (ih / 2.0 / q) ** 2) / c   # the ellipse through the rect's corners, aspect q
    return rx, q * rx


def _burst(k, slide, cx, cy, rx, ry, *, n, spike, seed, fill, clip=None, rot=0.0):
    pts = _burst_pts(cx, cy, rx, ry, n=n, spike=spike, seed=seed, rot=rot)
    if clip:
        pts = _clip(pts, clip)
    return _poly(slide, pts, fill, "a jagged comic burst: it shouts what is set on it; those words carry the meaning",
                 line=k.P["line"], lw=_ow(k))


_EX = 2.5          # the balloon's superellipse exponent: rounder than a card, squarer than an oval


def _super(cx, cy, a, b, N=120):
    out = []
    for i in range(N):
        t = 2 * math.pi * i / N
        c, s_ = math.cos(t), math.sin(t)
        out.append((cx + a * math.copysign(abs(c) ** (2.0 / _EX), c),
                    cy + b * math.copysign(abs(s_) ** (2.0 / _EX), s_)))
    return out


def _qbez(p0, c, p1, n=10):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]


def _balloon_pts(cx, cy, a, b, tip=None, base=0.5, bend=0.16):
    """A speech balloon: a superellipse about (cx, cy), and — toward `tip` — a curved tail `base` wide where it leaves
    the balloon."""
    pts = _super(cx, cy, a, b)
    if tip is None:
        return pts
    N = len(pts)
    th = math.atan2(tip[1] - cy, tip[0] - cx)

    def off(i):
        d = math.atan2(pts[i][1] - cy, pts[i][0] - cx) - th
        return abs(math.atan2(math.sin(d), math.cos(d)))
    i0 = min(range(N), key=off)
    step = sum(math.dist(pts[i - 1], pts[i]) for i in range(N)) / N
    j = max(2, int(round(base / 2.0 / step)))
    pa, pb = pts[(i0 - j) % N], pts[(i0 + j) % N]
    ring = [pts[(i0 + j + q) % N] for q in range(N - 2 * j + 1)]         # from pb round to pa
    mid = ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0)
    L = math.dist(mid, tip) or 1.0
    ux, uy = (tip[0] - mid[0]) / L, (tip[1] - mid[1]) / L
    px, py = -uy * bend * L, ux * bend * L                               # the tail bows to one side
    c1 = ((pa[0] + tip[0]) / 2.0 + px, (pa[1] + tip[1]) / 2.0 + py)
    c2 = ((pb[0] + tip[0]) / 2.0 + px * 0.6, (pb[1] + tip[1]) / 2.0 + py * 0.6)
    return ring + _qbez(pa, c1, tip)[1:] + _qbez(tip, c2, pb)[1:-1]


def _draw_balloon(k, slide, geo, tip=None):
    W, H, s, o = ctx(k)
    cx, cy, a, b = geo
    base = min(0.62 * s, 0.55 * min(a, b))
    return _poly(slide, _balloon_pts(cx, cy, a, b, tip, base=base), k.P["balloon"],
                 "a speech balloon: the words in it carry the meaning", line=k.P["line"], lw=_ow(k))


# ─────────────────────────────────────────── planning words ───────────────────────────────────────────
def _sizes(d):
    return dict(getattr(d, "exact", None) or getattr(d, "sizes", {}))


def _foot(r, default):
    return max((v[1] + v[3] for v in r.values()), default=default)


def _widest(k, items, sizes, colw, rects):
    """The column width (in) the items' lines need at `sizes`, as flow set them in a column `colw` wide (a balanced
    display field at the narrower measure flow chose for it)."""
    dw = colw * (1.0 - vl.HEADROOM)
    need = 0.0
    for f_, t in items:
        sz = sizes.get(f_)
        if sz is None or f_ not in rects:
            return colw
        wm = min(colw * vl.HEADROOM, rects[f_][2] - dw)
        t2, z = _v2._clause_break(k, f_, t, colw * vl.HEADROOM, {f_: sz})
        sz = z or sz
        for para in t2.split("\n"):
            for ln in vl._break_lines(k, f_, para.strip(), sz, wm):
                # a closing mark the measure lets hang past the line is one more em to the lint, which wraps it alone
                # onto a line of its own ('手里 / 。'): a snug CJK column keeps that em
                hang = sz / 72.0 if dk._has_cjk(ln) and ln.rstrip()[-1:] in dk._CJK_HANG else 0.0
                need = max(need, vl._line_width(k, f_, ln, sz) + hang)
    return (need + vl._INSET + 0.03) / vl.HEADROOM


_CLOSERS = set("。．，、！？：；）》】」』〕〗｝….,!?:;)]}")


def _lint_tail(k, field, para, size, width):
    """(lines, last line) of one paragraph as the delivery lint wraps it: character by character, every CJK glyph one
    em (a closing mark too — it hangs nothing), in the box's full width."""
    import display_type as dt
    role = vl.TYPE[NAME][field][1]
    bold = vl._weight(k, field, para)
    face = k.face(role)
    n, line, w = 1, "", 0.0
    for ch in para:
        cw = size / 72.0 if ord(ch) > 0x2E80 else (dt._glyph_width(ch, size, face, bold) or 0.55 * size / 72.0)
        if w + cw > width and w > 0:
            n, line, w = n + 1, ch, cw
        else:
            line, w = line + ch, w + cw
    return n, line.strip()


def _tail_bad(k, items, rects, sizes, colw):
    """The CJK fields whose last line the lint would read as a lone closing mark or a lone glyph (ORPHANED
    PUNCTUATION / WIDOW): flow lets the mark hang past a full line, the lint wraps it alone ('手里 / 。')."""
    bad = []
    dw = colw * (1.0 - vl.HEADROOM)
    for f_, t in items:
        z = sizes.get(f_)
        if f_ not in rects or not z or not dk._has_cjk(t):
            continue
        t2, z2 = _v2._clause_break(k, f_, t, colw * vl.HEADROOM, {f_: z})
        last = t2.split("\n")[-1].strip()
        ls = vl._break_lines(k, f_, last, z2 or z, rects[f_][2] - dw)
        if f_ in vl._NO_WIDOW and len(ls) > 1 and vl._lines_hold(k, f_, last, ls, z2 or z, rects[f_][2] - dw):
            last = ls[-1].strip()                      # a display field is set in its measured lines (paragraphs)
        n, tail = _lint_tail(k, f_, last, z2 or z, rects[f_][2])
        if n > 1 and tail and (all(c in _CLOSERS for c in tail) or (len(tail) == 1 and ord(tail) > 0x2E80)):
            bad.append(f_)
    return bad


def _flow3(k, slide, page, col, items, **kw):
    """vl_native2.flow, kept clear of the lint's lone-mark reading: a CJK field whose last line the lint would read as
    '。' alone is set again an em narrower (twice more at most), at the same size. Returns (rects, draw, width)."""
    x, y, w, h = col
    r, d = _v2.flow(k, slide, page, col, items, **kw)
    al = kw.get("align", "l")
    for i in (1, 2, 3):
        bad = _tail_bad(k, items, r, _sizes(d), w)
        if not bad:
            break
        w2 = w - i * max(_sizes(d).get(f_, 12.0) for f_ in bad) / 72.0
        if w2 < 0.55 * w:
            break
        x2 = x + (w - w2) / 2.0 if al == "c" else (x + w - w2 if al == "r" else x)
        try:
            r2, d2 = _v2.flow(k, slide, page, (x2, y, w2, h), items,
                              **dict(kw, start=dict(kw.get("start") or {}, **_sizes(d))))
        except vl.VLTextOverflow:
            break
        if not _tail_bad(k, items, r2, _sizes(d2), w2):
            return r2, d2, w2
    return r, d, w


def _flow(k, slide, page, col, items, **kw):
    r, d, _w = _flow3(k, slide, page, col, items, **kw)
    return r, d


def _snug(k, slide, page, col, items, kw):
    """flow() in `col`, then again in the narrowest column that keeps the same lines (the box hugs its words).
    Returns (rects, draw, column width)."""
    W, H, s, o = ctx(k)
    x, y, w, h = col
    r, d, w0 = _flow3(k, slide, page, col, items, **kw)
    sizes = _sizes(d)
    need = _widest(k, items, sizes, w0, r)
    # the narrowest column that keeps the lines; a little wider when the lint's line model (deckkit) reads the
    # snug one a line longer than the glyph measure did
    for grow in (1.0, 1.04, 1.09, 1.16):
        cw = need * grow
        if cw >= w0 - 0.04 * s:
            break
        try:
            r2, d2, cw2 = _flow3(k, slide, page, (x, y, cw, h), items,
                                 **dict(kw, start=dict(kw.get("start") or {}, **sizes)))
        except vl.VLTextOverflow:
            continue
        if _foot(r2, y) <= _foot(r, y) + 0.01 and not _tail_bad(k, items, r2, _sizes(d2), cw2) \
                and _renders_alike(k, items, _sizes(d2), cw2):
            return r2, d2, cw2
    return r, d, w0


def _renders_alike(k, items, sizes, colw):
    """True when every Latin field that is not set in its measured lines (body, captions, kickers) breaks the same in
    the 97% flow measures and in the full box a renderer fills — else a snug box could take a word up a line and
    strand the last one."""
    for f_, t in items:
        z = sizes.get(f_)
        if not z or f_ in vl._NO_WIDOW or dk._has_cjk(t):
            continue
        if vl._break_lines(k, f_, t, z, colw * vl.HEADROOM) != vl._break_lines(k, f_, t, z, colw):
            return False
    return True


def _pads(k, items, start=None):
    W, H, s, o = ctx(k)
    px, py = 0.17 * s, 0.11 * s
    big = max((start or {}).get(f_, vl.TYPE[NAME][f_][0] * s) for f_, _t in items)
    return px, py, py + 0.035 * s + (0.05 * big / 72.0 if big > 28 * s else 0.0)


def _plan_box(k, slide, page, x, y, wmax, hmax, items, *, ink, align="l", fit=True, start=None):
    """PLAN `items` in a box at (x, y), at most wmax x hmax, the box cut to its words — narrower when its lines are
    shorter than the room (a comic caption hugs its lettering). Returns (rects, draw_words, box, sizes)."""
    px, py, pb = _pads(k, items, start)
    kw = dict(anchor="top", align=align, ink=ink, accent=ink, mute=ink)
    if start:
        kw["start"] = start
    col = (x + px, y + py, wmax - 2 * px, hmax - py - pb)
    if fit:
        r, d, cw = _snug(k, slide, page, col, items, kw)
    else:
        r, d, _cw = _flow3(k, slide, page, col, items, **kw)
        cw = _cw
    sizes = _sizes(d)
    px, py, pb = _pads(k, items, sizes)
    foot = max(_foot(r, y + py) + pb, _lint_foot(k, r, items, sizes) + 0.12)     # the lint's pad is 0.09in, absolute
    return r, d, (x, y, cw + 2 * px, foot - y), sizes


def _lint_foot(k, rects, items, sizes):
    """Where the delivery lint reckons the words END: its line model sets a line at 1.25 em (1.4 em for CJK) from
    0.04in under the box's top, a little deeper than flow's 1.2 em — a box cut to flow's measure read as cramped
    (TEXT PADDING) under a three-line 54pt title. The box keeps the lint's 0.09in under that foot."""
    out = 0.0
    for f_, t in items:
        if f_ not in rects or f_ not in sizes:
            continue
        x, y, w, h = rects[f_]
        z = sizes[f_] / 72.0
        cjk = dk._has_cjk(t)
        n = max(1, int(round((h - 0.06) / (z * dk._LINT_LINE_H * (dk.CJK_LS if cjk else 1.0)))))
        out = max(out, y + 0.04 + n * z * (1.4 if cjk else 1.25))
    return out


def _caption(k, slide, page, x, y, wmax, hmax, items, *, fill=None, ink=None, align="l", fit=True, start=None,
             overlap=None, right=False):
    """PLAN a caption box at (x, y) — or, `right`, with its right edge at x; returns (rects, draw, box): draw() draws
    the box, then its words."""
    fill = fill or k.P["caption"]
    ink = ink or k.P["caption_ink"]
    if right:
        _r, _d, b0, sz = _plan_box(k, slide, page, 0.0, 0.0, wmax, hmax, items, ink=ink, align=align, fit=fit,
                                   start=start)
        x, wmax, fit, start = x - b0[2], b0[2] + 0.002, False, dict(start or {}, **sz)
    r, d, box, _sz = _plan_box(k, slide, page, x, y, wmax, hmax, items, ink=ink, align=align, fit=fit, start=start)

    def draw():
        _box(k, slide, box, fill, overlap=overlap)
        d()
    return r, draw, box


def _stack_boxes(k, slide, page, specs, y0, y1, *, gap=None, anchor="middle", centre=None, right=None):
    """PLAN boxes one under another between y0 and y1: specs = [(x, wmax, items, fill, ink, align), …] (empty items
    skipped). Every box is first sized TOGETHER (as vl_native2.stack does), then each planned at those sizes, cut to
    its words; the stack is centred when anchor is middle, and each box on the axis x = `centre` when given.
    Returns (rects, draws, boxes) — boxes = [(rect, fill)]."""
    W, H, s, o = ctx(k)
    gap = 0.14 * s if gap is None else gap
    specs = [sp for sp in specs if sp[2]]
    if not specs:
        return {}, [], []
    pads = sum(sum(_pads(k, sp[2])[1:]) + 0.02 * s for sp in specs) + gap * (len(specs) - 1)
    wmin = min(sp[1] for sp in specs) - 2 * 0.17 * s
    _r0, d0 = _v2.flow(k, slide, page, (0.0, 0.0, wmin, max(0.2, y1 - y0 - pads)),
                       [it for sp in specs for it in sp[2]], anchor="top")
    joint = _sizes(d0)
    hs = []
    for sp in specs:
        rs = [_r0[f_] for f_, _t in sp[2] if f_ in _r0]
        hs.append(_foot(dict(enumerate(rs)), 0.0) - min(v[1] for v in rs) + sum(_pads(k, sp[2])[1:]) if rs else 0.0)

    def plan(top):
        rects, draws, boxes, yy = {}, [], [], top
        for i, (x, wmax, items, fill, ink, align) in enumerate(specs):
            rest = sum(hs[i + 1:]) + gap * (len(specs) - 1 - i)
            st = {f_: joint[f_] for f_, _t in items if f_ in joint}
            r, d, box, sz = _plan_box(k, slide, page, x, yy, wmax, max(0.3, y1 - yy - rest), items, ink=ink,
                                      align=align, start=st)
            if centre is not None or right is not None:
                nx = (centre - box[2] / 2.0) if centre is not None else right - box[2]
                r, d, box, _sz = _plan_box(k, slide, page, nx, yy, box[2] + 0.002, box[3] + 0.3 * s,
                                           items, ink=ink, align=align, fit=False, start=sz)
            rects.update(r)
            boxes.append((box, fill))
            draws.append(d)
            yy = box[1] + box[3] + gap
        return rects, draws, boxes, yy - gap
    rects, draws, boxes, foot = plan(y0)
    if foot > y1 + 1e-6:
        raise vl.VLTextOverflow("comic.{}(): the boxes need {:.2f}in, the panel has {:.2f}in".format(
            page, foot - y0, y1 - y0))
    if anchor == "middle":
        rects, draws, boxes, foot = plan(y0 + max(0.0, (y1 - foot) / 2.0))
    return rects, draws, boxes


def _draw_boxes(k, slide, boxes, draws):
    for (box, fill), d in zip(boxes, draws):
        _box(k, slide, box, fill)
        d()


_KA = (1.10, 1.16, 1.24, 1.36)


def _balloon_plan(k, slide, page, region, items, *, start=None):
    """PLAN `items` (centred) in a speech balloon inside `region` (x, y, w, h). The balloon is a superellipse whose
    corners just clear the words' box; of a few shapes (wider and flatter … rounder) the one setting the words largest
    is kept. Returns a dict: rects, draw, geo (cx, cy, a, b), sizes, text (w, h) — the balloon centred in `region`."""
    W, H, s, o = ctx(k)
    x, y, w, h = region
    px, py = 0.12 * s, 0.07 * s
    ink = k.P["balloon_ink"]
    kw = dict(anchor="top", align="c", ink=ink, accent=ink, mute=ink)
    best, last = None, None
    for ka in _KA:
        kb = (1.0 - ka ** -_EX) ** (-1.0 / _EX)
        tw, th = w / ka - 2 * px, h / kb - 2 * py
        if tw < 0.9 * s or th < 0.3 * s:
            continue
        try:
            r, d = _v2.flow(k, slide, page, (0.0, 0.0, tw, th), items,
                            **dict(kw, **({"start": start} if start else {})))
        except vl.VLTextOverflow as e:
            last = e
            continue
        main = _sizes(d).get(items[0][0], 0.0)
        if best is None or main > best[0] + 0.3:
            best = (main, ka, kb, tw, th, _sizes(d))
    if best is None:
        raise last or vl.VLTextOverflow("comic.{}(): the balloon has no room ({:.2f} x {:.2f}in)".format(page, w, h))
    _main, ka, kb, tw, th, sizes = best
    st = dict(start or {}, **sizes)
    r0, _d0, cw = _snug(k, slide, page, (0.0, 0.0, tw, th), items, dict(kw, start=st))
    t_h = _foot(r0, 0.0)
    plan = {"ka": ka, "kb": kb, "cw": cw, "th": t_h, "sizes": st, "items": items, "page": page,
            "a": ka * (cw / 2.0 + px), "b": kb * (t_h / 2.0 + py)}
    return _balloon_at(k, slide, plan, x + w / 2.0, y + h / 2.0)


def _balloon_at(k, slide, plan, cx, cy):
    """The planned balloon's words set about the centre (cx, cy)."""
    ink = k.P["balloon_ink"]
    cw, t_h = plan["cw"], plan["th"]
    r, d = _v2.flow(k, slide, plan["page"], (cx - cw / 2.0, cy - t_h / 2.0, cw, t_h + 0.02), plan["items"],
                    anchor="top", align="c", ink=ink, accent=ink, mute=ink, start=plan["sizes"])
    out = dict(plan)
    out.update(rects=r, draw=d, geo=(cx, cy, plan["a"], plan["b"]))
    return out


def _number_plan(k, slide, page, region, num, starts, *, n=13):
    """PLAN the number in a burst inside `region` (x, y, w, h): at the first size in `starts` whose burst (spikes and
    all) fits the region. Returns (rects, draw_number, (cx, cy, rx, ry, spike))."""
    W, H, s, o = ctx(k)
    x, y, w, h = region
    ink = k.P["burst_ink"]
    last = None
    for st in starts:
        try:
            r, d = _v2.flow(k, slide, page, (x, y, w, h), [("number", num)], anchor="middle", align="c",
                            start={"number": st}, ink=ink)
        except vl.VLTextOverflow as e:
            last = e
            continue
        size = _sizes(d).get("number", st)
        nx, ny, nw, nh = r["number"]
        iw = min(nw, _v2.ink_w(k, "number", num, size))
        ih = size / 72.0 * (0.80 if not dk._has_cjk(num) else 0.95)
        rx, ry = _burst_fit(iw, ih, n)
        spike = 0.42 * min(rx, ry) + 0.12 * s
        # the burst is the figure's card to the delivery lint, which sets its line 1.25 em deep: a narrow figure ("7")
        # in a round burst ran past the burst's foot by that measure (TEXT PADDING), so the burst is at least that tall
        z = size / 72.0
        ry_min = (0.65 * z + 0.10) / 0.97 - 0.30 * spike
        if ry < ry_min:
            ry = ry_min
            rx = max(rx, 0.85 * ry)
            spike = 0.42 * min(rx, ry) + 0.12 * s
        if 2 * (rx + spike * 0.8) > w or 2 * (ry + spike * 0.8) > h:
            last = vl.VLTextOverflow("comic.{}(): the number {!r} needs a {:.2f} x {:.2f}in burst, the panel has "
                                     "{:.2f} x {:.2f}in".format(page, num, 2 * (rx + spike), 2 * (ry + spike), w, h))
            continue
        cx = x + w / 2.0
        # the figure's box is the burst's width, never the column's: a box wider than the burst reads to the lint as
        # dark ink on the page's ground (noir)
        bw = min(w, max(iw / vl.HEADROOM + vl._INSET + 0.06 * s, 2 * rx * 0.86))
        r2, d2 = _v2.flow(k, slide, page, (cx - bw / 2.0, y, bw, h), [("number", num)], anchor="middle", align="c",
                          start={"number": size}, ink=ink)
        cy = r2["number"][1] + r2["number"][3] * 0.50
        return r2, d2, (cx, cy, rx, ry, spike)
    raise last or vl.VLTextOverflow("comic.{}(): no room for the number".format(page))


def _inner(k, rect, extra=0.02):
    """The drawable inside of a panel: inside its border's ink."""
    return _inset(rect, _lw(k) / 72.0 / 2.0 + extra * ctx(k)[2])


def _head(k, slide, page, x, w, y, y1, f, *, title_start=None):
    """PLAN a page's head: the kicker on a yellow caption box, the title (comic capitals) under it. Returns (rects,
    draws, foot)."""
    W, H, s, o = ctx(k)
    kick, title = text_of(f, "kicker"), text_of(f, "title")
    r, ds, yy = {}, [], y
    if kick:
        kr, kd, kb = _caption(k, slide, page, x, y, min(w, 7.0 * s), min(1.4 * s, y1 - y), [("kicker", _caps(kick))])
        r.update(kr)
        ds.append(kd)
        yy = kb[1] + kb[3] + 0.20 * s
    if title:
        tr, td = _flow(k, slide, page, (x, yy, w, max(0.2, y1 - yy)), [("title", _caps(title))], anchor="top",
                          **({"start": {"title": title_start}} if title_start else {}))
        r.update(tr)
        ds.append(td)
        yy = _foot(tr, yy)
    return r, ds, yy


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=3)
def _cm_cover(k, slide, f, image):
    """A comic's front: the kicker on a masthead band across the top; under it the cover panel — the title in a caption
    block on a jagged burst, the subtitle on a caption under it, focus lines driving in from the panel's edges and
    halftone dots in two corners."""
    W, H, s, o = ctx(k)
    m, g = _m(k), _g(k)
    land = o == "land"
    kick = text_of(f, "kicker")
    r, ds = {}, []
    top = m
    band = None
    if kick:
        ink = k.P["mast_ink"]
        kr, kd, _kw = _snug(k, slide, "cover", (m + 0.30 * s, m + 0.14 * s, W - 2 * m - 0.60 * s, 1.5 * s),
                            [("kicker", _caps(kick))], dict(anchor="top", start={"kicker": (24 if land else 19) * s},
                                                            ink=ink, accent=ink, mute=ink))
        band = (m, m, W - 2 * m, _foot(kr, m) + 0.16 * s - m)
        r.update(kr)
        ds.append(kd)
        top = band[1] + band[3] + g
    P = (m, top, W - 2 * m, H - m - top)
    A = _inner(k, P)
    tw = ((0.62, 0.74, 0.86) if land else (0.84, 0.88, 0.90))[alt()] * A[2]
    tx = A[0] + (0.07 * A[2] if land else (A[2] - tw) / 2.0)
    sx = tx + (0.55 * s if land else 0.35 * s)
    title = text_of(f, "title")
    specs = [(tx, tw, [("title", _caps(title))] if title else [], k.P["caption"], k.P["caption_ink"], "l"),
             (sx, tw - (sx - tx), _v2.fields(f, ("subtitle",)), k.P["balloon"], k.P["balloon_ink"], "l")]
    vpad = (0.60 if alt() == 0 else 0.42) * s
    tr, tds, boxes = _stack_boxes(k, slide, "cover", specs, A[1] + vpad, A[1] + A[3] - vpad, gap=0.16 * s)
    r.update(tr)
    clip = _rect(*A)
    _panel_fill(k, slide, _rect(*P), k.P["tint_b"])
    if band:
        _box(k, slide, band, k.P["mast"])
        bi = _inset(band, _ow(k) / 72.0 + 0.04 * s)
        src = (bi[0] + bi[2], bi[1] + bi[3] / 2.0)
        _dots(k, slide, _rect(*bi), k.P["mast_ink"], src, _reach(src, [_grow(_union(list(kr.values())), 0.0)],
                                                                   0.30 * bi[2], 0.45 * s),
              axis=(-1.0, 0.0), pitch=0.15 * s, alpha=0.30)
    # the burst goes off behind the title's block (behind the subtitle's when there is no title; with neither, the
    # focus lines alone drive at the panel's centre and nothing bursts)
    tb = boxes[0][0] if boxes else (A[0] + A[2] / 2.0 - 0.5 * s, A[1] + A[3] / 2.0 - 0.3 * s, 1.0 * s, 0.6 * s)
    bcx, bcy = tb[0] + tb[2] / 2.0, tb[1] + tb[3] / 2.0
    brx, bry = tb[2] / 2.0 * 1.06 + 0.25 * s, tb[3] / 2.0 * 1.45 + 0.30 * s
    spike = min(0.75 * s, 0.30 * min(brx, bry) + 0.30 * s)
    _dots(k, slide, clip, k.P["dot_b"], [((A[0] + A[2], A[1] + A[3]), 0.62 * max(A[2], A[3])),
                                         ((A[0], A[1]), 0.30 * max(A[2], A[3]))], None, pitch=0.22 * s, gamma=1.1)
    _focus(k, slide, A, (bcx, bcy), (brx + spike * 0.6, bry + spike * 0.6), k.P["speed"], n=64, seed=7,
           keep=[_grow(b, 0.10 * s) for b, _f in boxes], w0=0.055 * s)
    if boxes:
        _burst(k, slide, bcx, bcy, brx, bry, n=15, spike=spike, seed=3, fill=k.P["burst_out"], clip=clip)
    _panel_line(k, slide, _rect(*P))
    _run_all(ds)
    _draw_boxes(k, slide, boxes, tds)
    return r


@register(NAME, "section", alts=3)
def _cm_section(k, slide, f, image):
    """A splash panel: the section number in a two-layer burst with focus lines driving at it; the kicker on a caption
    box in the panel's corner; the title on a caption beside the burst (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    land = o == "land"
    P = (m, m, W - 2 * m, H - 2 * m)
    A = _inner(k, P)
    E = _inner(k, P, 0.0)
    num, kick, title = text_of(f, "number"), text_of(f, "kicker"), text_of(f, "title")
    r, ds, kboxes = {}, [], []
    ktop = A[1]
    if kick:
        kr, kd, kbox = _caption(k, slide, "section", E[0], E[1], (0.46 if land else 0.80) * A[2], 1.5 * s,
                                [("kicker", _caps(kick))], start={"kicker": 17 * s})
        r.update(kr)
        ds.append(kd)
        kboxes.append(kbox)
        ktop = kbox[1] + kbox[3]
    starts = [z * s for z in ((150, 120, 96, 76, 60) if alt() == 0 else (110, 88, 70, 56) if alt() == 1
                              else (80, 64, 54, 48))]
    tspec = lambda x_, w_: [(x_, w_, [("title", _caps(title))] if title else [], k.P["balloon"],  # noqa: E731
                             k.P["balloon_ink"], "l")]
    geo, tboxes, tds = None, [], []
    if land:
        nreg = (A[0] + 0.03 * A[2], ktop + 0.15 * s, (0.44 if alt() < 2 else 0.36) * A[2],
                A[1] + A[3] - ktop - 0.30 * s)
        cx0 = (nreg[0] + nreg[2] + 0.35 * s) if num else A[0] + 0.12 * A[2]
        cw = A[0] + A[2] - cx0 - (0.40 * s if num else 0.12 * A[2])
        if title:
            tr, tds, tboxes = _stack_boxes(k, slide, "section", tspec(cx0, cw), ktop + 0.30 * s,
                                           A[1] + A[3] - 0.30 * s)
            r.update(tr)
    else:
        tx, tw = A[0] + 0.07 * A[2], 0.86 * A[2]
        th_need = 0.0
        if title and num:
            _r, _d, tb0, _sz = _plan_box(k, slide, "section", 0.0, 0.0, tw, 0.45 * A[3], [("title", _caps(title))],
                                         ink=k.P["balloon_ink"])
            th_need = tb0[3]
        nreg = (A[0] + 0.05 * A[2], ktop + 0.15 * s, 0.90 * A[2],
                A[1] + A[3] - ktop - 0.15 * s - (th_need + 0.55 * s if title else 0.30 * s))
        if title:
            y0 = (nreg[1] + nreg[3] + 0.15 * s) if num else ktop + 0.3 * s
            # the title's caption at the panel's foot, right: the kicker's corner, the burst and the title read
            # down the page's diagonal
            tr, tds, tboxes = _stack_boxes(k, slide, "section", tspec(tx, tw), y0, A[1] + A[3] - 0.30 * s,
                                           right=tx + tw)
            r.update(tr)
    if num:
        nr, nd, geo = _number_plan(k, slide, "section", nreg, num, starts)
        r.update(nr)
        ds.append(nd)
    clip = _rect(*A)
    _panel_fill(k, slide, _rect(*P), k.P["tint_c"])
    _dots(k, slide, clip, k.P["dot_a"], (A[0] + A[2], A[1] + A[3]), 0.55 * max(A[2], A[3]), pitch=0.22 * s)
    keep = [_grow(b, 0.10 * s) for b in kboxes + [b for b, _f in tboxes]]
    if geo:
        cx, cy, rx, ry, spike = geo
        _focus(k, slide, A, (cx, cy), (rx + spike * 1.1, ry + spike * 1.1), k.P["speed"], n=72, seed=11, keep=keep,
               w0=0.06 * s)
        _burst(k, slide, cx, cy, rx + spike * 0.55, ry + spike * 0.55, n=11, spike=spike * 0.9, seed=5,
               fill=k.P["burst_out"], clip=clip, rot=0.15)
        _burst(k, slide, cx, cy, rx, ry, n=13, spike=spike * 0.55, seed=6, fill=k.P["burst"], clip=clip)
    elif tboxes:
        b = tboxes[0][0]
        _focus(k, slide, A, (b[0] + b[2] / 2, b[1] + b[3] / 2), (b[2] / 2 + 0.3 * s, b[3] / 2 + 0.3 * s),
               k.P["speed"], n=72, seed=11, keep=keep, w0=0.06 * s)
    _panel_line(k, slide, _rect(*P))
    _run_all(ds)
    _draw_boxes(k, slide, tboxes, tds)
    return r


@register(NAME, "image_text", alts=3)
def _cm_image_text(k, slide, f, image):
    """The caller's picture is a panel of its own — its heavy border, the caption on a yellow caption box set into its
    top-left corner; beside it (under it on a portrait or square page) the kicker on a caption box, the title, and the
    body in a speech balloon whose tail points at the picture."""
    W, H, s, o = ctx(k)
    m = _m(k)
    land = o == "land"
    cap, body = text_of(f, "caption"), text_of(f, "body")
    if not land:
        return _image_text_port(k, slide, f, image)
    img = (m, m, (0.50, 0.44, 0.38)[alt()] * W, H - 2 * m)
    r, ds = _photo_caption(k, slide, img, cap)
    col = (img[0] + img[2] + 0.55 * s, m + 0.10 * s, W - m - img[0] - img[2] - 0.55 * s, H - 2 * m - 0.20 * s)
    gap = 0.35 * s
    bal = None
    if body:
        # the head and the balloon share the column: of a few splits, the one whose smaller of the two (title and body,
        # each against its own size) is largest — a long title planned first left a long body 11pt in a corner
        best, last = None, None
        for frac in (0.30, 0.42, 0.55, 0.68):
            need_b = max((1.5 if alt() < 2 else 1.1) * s, frac * col[3])
            try:
                hr_, hds_, hfoot_ = _head(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3] - need_b, f)
                reg = (col[0] + (0.35 * s if land else 0.0), hfoot_ + gap, col[2] - (0.35 * s if land else 0.0),
                       col[1] + col[3] - hfoot_ - gap)
                bal_ = _balloon_plan(k, slide, "image_text", reg, [("body", _caps(body))])
            except vl.VLTextOverflow as e:
                last = e
                continue
            tz = {f_: z for d_ in hds_ for f_, z in _sizes(d_).items()}.get("title")
            bz = bal_["sizes"]["body"] / (vl.TYPE[NAME]["body"][0] * s)
            tz = (tz / (vl.TYPE[NAME]["title"][0] * s)) if tz else 9.0
            score = min(bz, tz) + 0.3 * bz
            if bz >= 0.88 and tz >= 0.5:              # the first split that letters the balloon near its size
                best = (99.0, hr_, hds_, hfoot_, bal_)
                break
            if best is None or score > best[0] + 0.02:
                best = (score, hr_, hds_, hfoot_, bal_)
        if best is None:
            raise last
        _sc, hr, hds, hfoot, bal = best
    else:
        hr, hds, hfoot = _head(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3], f)
    # the head and the balloon as ONE group, centred in the column
    used = (hfoot - col[1]) + ((gap + 2 * bal["b"]) if bal else 0.0)
    dy = max(0.0, (col[3] - used) / 2.0)
    if dy > 0.01:
        sizes = {f_: z for d_ in hds for f_, z in _sizes(d_).items()}
        hr, hds, hfoot = _head(k, slide, "image_text", col[0], col[2], col[1] + dy, col[1] + col[3], f,
                               title_start=sizes.get("title"))
    r.update(hr)
    ds += hds
    if bal:
        a, b = bal["a"], bal["b"]
        bal = _balloon_at(k, slide, bal, min(col[0] + 0.35 * s + a, col[0] + col[2] - a), hfoot + gap + b)
        r.update(bal["rects"])
        ds.append(bal["draw"])
    _photo(k, slide, image, img)
    if bal:
        cx, cy, a, b = bal["geo"]
        tip = (img[0] + img[2] + 0.10 * s, min(max(cy + 0.25 * b, img[1] + 0.5 * s), img[1] + img[3] - 0.6 * s))
        _draw_balloon(k, slide, bal["geo"], tip)
    _run_all(ds)
    return r


def _photo_caption(k, slide, img, cap):
    """PLAN the caption on a yellow box set into the picture panel's top-left corner."""
    W, H, s, o = ctx(k)
    r, ds = {}, []
    if cap:
        E = _inner(k, img, 0.0)
        # lettered a size over the manifest's 12pt caption: that one also sets the core's credit chip, whose wrapped
        # Chinese credit read as cramped to the lint above 12pt (visual_languages._place_credit)
        cr, cd, _cb = _caption(k, slide, "image_text", E[0], E[1], min(0.82 * E[2], 5.0 * s), 0.45 * E[3],
                               [("caption", cap)], start={"caption": 14 * s},
                               overlap="a comic caption box is set into its panel's corner, over the picture")
        r.update(cr)
        ds.append(cd)
    return r, ds


def _photo(k, slide, image, img):
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _panel_line(k, slide, _rect(*img))


def _image_text_port(k, slide, f, image):
    """A portrait or square page reads down: the kicker and the title, the picture panel, and the body's balloon under
    it, its tail reaching up to the picture (a tail running up past the title crossed its words)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    cap, body = text_of(f, "caption"), text_of(f, "body")
    hr, hds, hfoot = _head(k, slide, "image_text", m + 0.10 * s, W - 2 * m - 0.20 * s, m,
                           m + (0.24, 0.28, 0.32)[alt()] * H, f)
    r, ds = dict(hr), list(hds)
    ytop = (hfoot + 0.32 * s) if (text_of(f, "kicker") or text_of(f, "title")) else m
    rest = H - m - ytop
    tail = 0.45 * s
    bal, bh_ = None, 0.0
    if body:
        reg = (m + 0.15 * s, 0.0, W - 2 * m - 0.30 * s, (0.40, 0.48, 0.56)[alt()] * rest - tail)
        bal = _balloon_plan(k, slide, "image_text", reg, [("body", _caps(body))])
        bh_ = 2 * bal["b"] + tail
    img = (m, ytop, W - 2 * m, rest - bh_)
    if img[3] < max(1.3 * s, 0.18 * H):
        raise vl.VLTextOverflow("comic.image_text(): the words leave the picture {:.2f}in".format(img[3]))
    cr, cds = _photo_caption(k, slide, img, cap)
    r.update(cr)
    ds += cds
    if bal:
        bal = _balloon_at(k, slide, bal, W / 2.0, img[1] + img[3] + tail + bal["b"])
        r.update(bal["rects"])
        ds.append(bal["draw"])
    _photo(k, slide, image, img)
    if bal:
        cx, cy, a, b = bal["geo"]
        _draw_balloon(k, slide, bal["geo"], (cx - 0.35 * a, img[1] + img[3] + 0.08 * s))
    _run_all(ds)
    return r


_DOTS = ("dot_a", "dot_b", "dot_c", "dot_b")
_TINTS = ("tint_a", "tint_b", "tint_c", "tint_a")


def _unwidow(k, field, text, size, w):
    """The column (in) for a line of body text that ends on two words or more AS RENDERED: flow measures in 97% of a
    column and draws the box at its full width, so a renderer can take one more word up and leave the last alone
    ('…most of them / old' — measured '…most of / them old'). The column is narrowed (text-wrap: balance) until the
    measure and the full box break alike and the last line has company; else w."""
    # Latin only: a balanced Chinese measure can rely on a closing mark hanging past the line, which the lint's line
    # model wraps alone ('东西 / 。'); flow already breaks Chinese at its clause marks
    if dk._has_cjk(text):
        return w

    def ok(wc):
        lm = vl._break_lines(k, field, text, size, wc * vl.HEADROOM)
        return (lm == vl._break_lines(k, field, text, size, wc)
                and not vl._widowed(k, field, text, size, wc * vl.HEADROOM))
    if ok(w):
        return w
    wb = vl._balanced_width(k, field, text, size, w * vl.HEADROOM) or w * 0.6
    wc = wb / vl.HEADROOM + 0.01
    n0 = len(vl._break_lines(k, field, text, size, w * vl.HEADROOM))
    while wc < w:
        if ok(wc) and len(vl._break_lines(k, field, text, size, wc * vl.HEADROOM)) <= n0:
            return wc
        wc *= 1.03
    return w


@register(NAME, "points", alts=4)
def _cm_points(k, slide, f, image):
    """A strip of panels, one point each, in reading order: the head on a yellow caption box at the panel's top, the
    line under it, and the panel's own colour of halftone tone rising from its foot (fading out before the words). A
    row with slanted gutters across a landscape page; a column of wide panels on a portrait or square one; long copy
    takes a two-by-two grid, then a plainer one."""
    W, H, s, o = ctx(k)
    m, g = _m(k), _g(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    land = o == "land"
    x0, w0 = m, W - 2 * m
    hr, ds, hfoot = _head(k, slide, "points", x0 + 0.04 * s, w0 - 0.08 * s, m, m + (0.26 if alt() < 2 else 0.32) * H, f,
                          title_start=None if alt() < 2 else 30 * s)
    r = dict(hr)
    top = hfoot + (0.30 if alt() < 3 else 0.22) * s
    bottom = H - m
    if land:
        layout = ("row", "row" if n <= 3 else "grid", "grid", "grid")[alt()]
    else:
        layout = ("col", "grid" if n >= 3 else "col", "grid" if n >= 3 else "col", "grid" if n >= 3 else "col")[alt()]
    cols, rows = {"row": (n, 1), "col": (1, n), "grid": (2, -(-n // 2))}[layout]
    gx = g if cols > 1 else 0.0
    cw = (w0 - (cols - 1) * gx) / cols
    rh = (bottom - top - (rows - 1) * g) / rows
    slant = 0.20 * s if (layout == "row" and alt() == 0 and n > 1) else 0.0
    pad = (0.22 if alt() < 3 else 0.15) * s
    edge = _lw(k) / 72.0 / 2.0
    heads = [[("item_head", _caps(hd))] for hd, _ln in pts]
    lines = [[("item_line", ln)] if ln else [] for _hd, ln in pts]
    tx_w = cw - 2 * pad - 2 * slant - 2 * edge
    if tx_w < 1.0 * s or rh < 0.8 * s:
        raise vl.VLTextOverflow("comic.points(): {} panels leave each {:.2f} x {:.2f}in".format(n, tx_w, rh))
    # the heads at ONE size, each on its caption box; the lines at one size in what the tallest box leaves
    # a head is lettered on ONE line when that costs at most a fifth of its size (a caption box of one word a line
    # read as a list, not a caption)
    hw = tx_w - 2 * 0.17 * s
    base = vl.TYPE[NAME]["item_head"][0] * s
    one = min(base * (hw * vl.HEADROOM - vl._INSET) / max(1e-6, vl._line_width(k, "item_head", hd[0][1], base))
              for hd in heads)
    # …and a roomy panel letters its words a size up (short heads in tall panels read as stamps, not captions)
    hstart = {"item_head": min(1.3 * base, one)} if one >= 0.80 * base else {}
    hstart["item_line"] = 1.18 * vl.TYPE[NAME]["item_line"][0] * s
    # the head and the line sized TOGETHER in what a panel holds (its box's padding and the gap taken out first): a
    # short panel shrinks both, not the line alone to nothing
    _px, _py, _pb = _pads(k, heads[0])
    jh = rh - 2 * edge - pad - _py - _pb - 0.18 * s + vl.GAP * s
    jprobe = _v2.plan_together(k, slide, "points", [((0, 0, hw, jh), hd + ln, {"anchor": "top", "start": hstart})
                                                    for hd, ln in zip(heads, lines)])
    hsz, lsz0 = {}, {}
    for _pr, d_ in jprobe:
        for f_, z in _sizes(d_).items():
            dd = hsz if f_ == "item_head" else lsz0
            dd[f_] = min(dd.get(f_, z), z)
    nlines = max(len(vl._break_lines(k, "item_head", hd[0][1], hsz.get("item_head", base), hw * vl.HEADROOM))
                 for hd in heads)
    if layout == "row" and nlines > 2:
        raise vl.VLTextOverflow("comic.points(): a head takes {} lines in a row of {} panels — trying a grid".format(
            nlines, n))
    # a strip whose panels hold the words only at a much smaller size gives way to the grid, which holds them larger
    # (a square page's three short rows set the heads at 60% of their size)
    lz = min(lsz0.values(), default=None)
    if layout != "grid" and alt() < 3 and (hsz.get("item_head", base) < 0.78 * base or
                                           (lz is not None and lz < 0.85 * vl.TYPE[NAME]["item_line"][0] * s)):
        raise vl.VLTextOverflow("comic.points(): the {} sets its words small ({:.0f}pt heads) — trying a grid".format(
            layout, hsz.get("item_head", base)))
    capb = [_plan_box(k, slide, "points", 0.0, 0.0, tx_w, rh * 0.6, hd, ink=k.P["caption_ink"], start=hsz)
            for hd in heads]
    cap_h = max(c[2][3] for c in capb)
    room = rh - cap_h - 0.18 * s - pad - 2 * edge          # the head's box sits in the panel's corner
    if any(lines) and room < 0.2 * s:
        raise vl.VLTextOverflow("comic.points(): the heads leave the lines {:.2f}in".format(room))
    lprobe = _v2.plan_together(k, slide, "points", [((0, 0, tx_w, room), ln, {"anchor": "top", "start": lsz0})
                                                    for ln in lines if ln])
    lsz = {}
    for _pr, d_ in lprobe:
        for f_, z in _sizes(d_).items():
            lsz[f_] = min(lsz.get(f_, z), z)
    panels, words, keeps = [], [], []
    for i, (head, line) in enumerate(zip(heads, lines)):
        ci, ri = i % cols, i // cols
        px0 = x0 + ci * (cw + gx)
        py0 = top + ri * (rh + g)
        pw = w0 if (layout == "grid" and n % 2 and i == n - 1) else cw     # an odd grid's last panel runs across
        tl, bl, tr_, br_ = px0, px0, px0 + pw, px0 + pw
        if slant:
            if ci > 0:
                tl, bl = px0 + slant, px0 - slant
            if ci < cols - 1:
                tr_, br_ = px0 + pw + slant, px0 + pw - slant
        panels.append([(tl, py0), (tr_, py0), (br_, py0 + rh), (bl, py0 + rh)])
        bx_ = max(tl, bl) + edge
        ix = bx_ + pad
        iw_ = min(tr_, br_) - edge - pad - ix
        cr_, cd_, cbox, _sz = _plan_box(k, slide, "points", bx_, py0 + edge, iw_ + pad, cap_h + 0.3 * s, head,
                                        ink=k.P["caption_ink"], start=hsz)
        r.update(cr_)
        words.append((cbox, cd_))
        kp = [cbox]
        if line:
            ly = cbox[1] + cbox[3] + 0.18 * s
            lw_ = _unwidow(k, "item_line", line[0][1], lsz.get("item_line", 12.0), iw_)
            lr_, ld_ = _flow(k, slide, "points", (ix, ly, lw_, py0 + rh - edge - pad - ly), line, anchor="top",
                                start=lsz)
            r.update(lr_)
            words.append((None, ld_))
            lx, ly_, lw2, lh = _union(list(lr_.values()))
            kp.append((lx, ly_, min(lw2, _widest(k, line, _sizes(ld_), lw2, lr_)), lh))   # its ink, not its column
        keeps.append(kp)
    for i, poly in enumerate(panels):
        _panel_fill(k, slide, poly, k.P[_TINTS[i % 4]])
        bx, by, bw, bh = _bbox(poly)
        ins = _clip(poly, _rect(*_inset((bx, by, bw, bh), edge + 0.03 * s)))
        # the tone rises from the panel's foot and dies out before its words. (Brought in from the far side of a wide
        # panel, the field shared its top with the head's caption box and the lint read the two as a row of uneven
        # cards; rising from the foot it is as wide as its panel.)
        src, axis = (bx, by + bh), (0.0, -1.0)
        reach = min(by + bh - (_union(keeps[i])[1] + _union(keeps[i])[3]) - 0.35 * s, 0.80 * bh)
        _dots(k, slide, ins, k.P[_DOTS[i % 4]], src, reach, axis=axis, keep=[_grow(kr, 0.04 * s) for kr in keeps[i]],
              pitch=0.19 * s, gamma=0.8)
    for poly in panels:
        _panel_line(k, slide, poly)
    for box, d in words:
        if box:
            _box(k, slide, box, k.P["caption"])
        d()
    _run_all(ds)
    return r


@register(NAME, "quote", alts=3)
def _cm_quote(k, slide, f, image):
    """One big speech balloon holding the quote, its tail pointing down at the speaker — the attribution on a caption
    box at the foot of the panel; halftone dots rise from the panel's far corner."""
    W, H, s, o = ctx(k)
    m = _m(k)
    land = o == "land"
    P = (m, m, W - 2 * m, H - 2 * m)
    A = _inner(k, P)
    q, a = text_of(f, "quote"), text_of(f, "attribution")
    r, ds = {}, []
    abox = None
    if a:
        items = [("attribution", _caps(a))]
        # the speaker's box at the panel's foot, right: measured first, then set where it goes
        _r, _d, b0, asz = _plan_box(k, slide, "quote", 0.0, 0.0, (0.55 if land else 0.80) * A[2], 0.30 * A[3], items,
                                    ink=k.P["caption_ink"])
        ar, ad, abox = _caption(k, slide, "quote", A[0] + A[2] - 0.06 * A[2] - b0[2], A[1] + A[3] - 0.30 * s - b0[3],
                                b0[2] + 0.002, b0[3] + 0.2 * s, items, fit=False, start=asz)
        r.update(ar)
        ds.append(ad)
    bal = None
    if q:
        bot = (abox[1] - (0.60 + 0.20 * alt()) * s) if abox else A[1] + A[3] - 0.9 * s
        reg = (A[0] + (0.05 if alt() < 2 else 0.03) * A[2], A[1] + 0.30 * s, (0.90 if alt() < 2 else 0.94) * A[2],
               bot - A[1] - 0.30 * s)
        bal = _balloon_plan(k, slide, "quote", reg, [("quote", _caps(q))])
        r.update(bal["rects"])
        ds.append(bal["draw"])
    _panel_fill(k, slide, _rect(*P), k.P["tint_a"])
    _dots(k, slide, _rect(*A), k.P["dot_a"], [((A[0], A[1] + A[3]), 0.70 * max(A[2], A[3])),
                                              ((A[0] + A[2], A[1]), 0.32 * max(A[2], A[3]))], None, pitch=0.22 * s,
          gamma=1.15)
    _panel_line(k, slide, _rect(*P))
    if bal:
        cx, cy, ga, gb = bal["geo"]
        if abox:
            tip = (abox[0] + min(0.30 * abox[2], 0.8 * s), abox[1] - 0.10 * s)
        else:
            tip = (cx - 0.45 * ga, cy + gb + 0.55 * s)
        _draw_balloon(k, slide, bal["geo"], tip)
    _run_all(ds)
    return r


@register(NAME, "data", alts=3)
def _cm_data(k, slide, f, image):
    """The key number bursts out of its panel — a two-layer burst, focus lines driving at it, halftone dots in the
    corner; the label and the note in the panel beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m, g = _m(k), _g(k)
    land = o == "land"
    num = text_of(f, "number")
    rest = _v2.fields(f, ("label", "note"), ("label",))
    side = land and alt() < 2               # a landscape page's last layout stacks them: room for a long figure
    if side:
        split = (0.60, 0.52)[alt()] if rest else 1.0
        P1 = (m, m, (W - 2 * m - (g if rest else 0.0)) * split, H - 2 * m)
        P2 = (P1[0] + P1[2] + g, m, W - m - P1[0] - P1[2] - g, H - 2 * m) if rest else None
    else:
        split = ((0.56, 0.48, 0.40) if not land else (0.58, 0.58, 0.58))[alt()] if rest else 1.0
        P1 = (m, m, W - 2 * m, (H - 2 * m - (g if rest else 0.0)) * split)
        P2 = (m, P1[1] + P1[3] + g, W - 2 * m, H - m - P1[1] - P1[3] - g) if rest else None
    A1 = _inner(k, P1)
    r, ds = {}, []
    geo = None
    if num:
        reg = _inset(A1, 0.20 * s)
        nr, nd, geo = _number_plan(k, slide, "data", reg, num, [z * s for z in (170, 140, 115, 95, 78, 64, 54, 48)])
        r.update(nr)
        ds.append(nd)
    if P2:
        A2 = _inset(_inner(k, P2), 0.32 * s)
        # the label a size up when the panel is wide enough to keep it to three lines (a narrow panel stacked a long
        # label one word a line)
        lab = text_of(f, "label")
        big = vl.TYPE[NAME]["label"][0] * s * 1.35
        up = bool(lab) and len(vl._break_lines(k, "label", _caps(lab), big, A2[2] * vl.HEADROOM)) <= 3
        st = {"label": big if up else vl.TYPE[NAME]["label"][0] * s, "note": vl.TYPE[NAME]["note"][0] * s * 1.15}
        tr, td = _flow(k, slide, "data", A2, rest, anchor="middle", start=st)
        r.update(tr)
        ds.append(td)
    clip = _rect(*A1)
    _panel_fill(k, slide, _rect(*P1), k.P["tint_b"])
    _dots(k, slide, clip, k.P["dot_b"], (A1[0], A1[1] + A1[3]), 0.62 * max(A1[2], A1[3]), pitch=0.21 * s)
    if geo:
        cx, cy, rx, ry, spike = geo
        _focus(k, slide, A1, (cx, cy), (rx + spike * 1.1, ry + spike * 1.1), k.P["speed"], n=68, seed=21, w0=0.06 * s)
        _burst(k, slide, cx, cy, rx + spike * 0.55, ry + spike * 0.55, n=11, spike=spike * 0.9, seed=8,
               fill=k.P["burst_out"], clip=clip, rot=0.2)
        _burst(k, slide, cx, cy, rx, ry, n=13, spike=spike * 0.55, seed=9, fill=k.P["burst"], clip=clip)
    _panel_line(k, slide, _rect(*P1))
    if P2:
        _panel_fill(k, slide, _rect(*P2), k.P["panel"])
        B2 = _inner(k, P2, 0.03)
        words = [_union(list(tr.values()))]
        src = (B2[0] + B2[2], B2[1] + B2[3])
        _dots(k, slide, _rect(*B2), k.P["dot_a"], src, _reach(src, words, 0.75 * max(B2[2], B2[3]), 0.30 * s),
              keep=[_grow(w_, 0.04 * s) for w_ in words], pitch=0.19 * s, gamma=1.1)
        _panel_line(k, slide, _rect(*P2))
    _run_all(ds)
    return r


@register(NAME, "closing", alts=3)
def _cm_closing(k, slide, f, image):
    """The last panel: a wide panel across the page, sun rays fanning up from its foot and halftone dots glowing round
    their source; the title on a caption block in the middle, the line on a caption under it."""
    W, H, s, o = ctx(k)
    m = _m(k)
    land = o == "land"
    ph = ((0.70, 0.80, 1.0) if land else (0.64, 0.76, 1.0))[alt()] * (H - 2 * m)
    P = (m, (H - ph) / 2.0, W - 2 * m, ph)
    A = _inner(k, P)
    tw = ((0.66, 0.78, 0.88) if land else (0.84, 0.88, 0.90))[alt()] * A[2]
    tx = A[0] + (A[2] - tw) / 2.0
    title, line = text_of(f, "title"), text_of(f, "line")
    specs = [(tx, tw, [("title", _caps(title))] if title else [], k.P["caption"], k.P["caption_ink"], "c"),
             (tx, tw, [("line", line)] if line else [], k.P["balloon"], k.P["balloon_ink"], "c")]
    r, tds, boxes = _stack_boxes(k, slide, "closing", specs, A[1] + 0.35 * s, A[1] + A[3] - 0.35 * s, gap=0.16 * s,
                                 centre=W / 2.0)
    _panel_fill(k, slide, _rect(*P), k.P["tint_c"])
    clip = _rect(*A)
    src = (W / 2.0, A[1] + A[3] + 0.6 * s)
    rays, nr, R = [], 22, 3 * max(W, H)
    for i in range(0, nr, 2):
        a0, a1 = math.pi + math.pi * i / nr, math.pi + math.pi * (i + 1) / nr
        c = _clip([src, (src[0] + R * math.cos(a0), src[1] + R * math.sin(a0)),
                   (src[0] + R * math.cos(a1), src[1] + R * math.sin(a1))], clip)
        if len(c) >= 3:
            rays.append(c)
    _multi(slide, rays, k.P["dot_c"], "sun rays fanning up from the last panel's horizon: the ending's light, nothing "
                                      "to read in them", alpha=0.35)
    _dots(k, slide, clip, k.P["dot_a"], (W / 2.0, A[1] + A[3]), 0.42 * max(A[2], A[3]), pitch=0.20 * s)
    _panel_line(k, slide, _rect(*P))
    _draw_boxes(k, slide, boxes, tds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_comic(slide, role, index):
    """An ordinary page (a chart, an agenda) is one panel: its heavy border inside the page margin; the content rect
    inside it, in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    k = _v2.kit_for(NAME, slide)
    Wr, Hr, s, o = ctx(k)
    m = _m(k)
    _panel_line(k, slide, _rect(m, m, Wr - 2 * m, Hr - 2 * m))
    return (0.75, 0.70, W - 1.5, H - 1.4)


_card_comic = vl._card_for(NAME)
