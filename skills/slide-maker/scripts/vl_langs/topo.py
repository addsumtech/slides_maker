"""topo — the Topographic map language (等高线地形图): its ground painter, its card and its seven pages.

A topographic survey sheet: a neatline with a graduated border round every page; smooth contour lines traced from a
height field (marching squares, then smoothed), every fifth an index contour drawn heavier; summit markers, survey
crosses, a north arrow and a scale bar; a dashed trail between waypoints when the caller says the points happen in
order. Every page PLANS its words first (vl_native2.flow / stack: measured, never under a floor), raises the terrain
around them, and breaks every contour where a word sits — as a printed map breaks its contours for a label — so no
line ever runs through the text. The only words it writes itself are the waypoint numbers (the manifest's derived
words); there are no elevation figures, scale numbers or compass letters."""
from __future__ import annotations

import math
import random

import deckkit as dk
import native_art as na
import ornaments as orn
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "topo"
_A, _B = 0.21, 0.262         # the neatline's outer and inner rules, in units of s


def _lw(k, w):
    """A line weight that grows with a large canvas (a poster) and never thins below its design on a small one."""
    return w * max(1.0, ctx(k)[2])


# ─────────────────────────────────────────── the sheet ───────────────────────────────────────────
def _sheet(k, slide):
    """Every page: the map's neatline — two rules with the graduated border between them (alternate cells filled, the
    corners solid), as the edge of a printed survey sheet is graduated."""
    W, H, s, o = ctx(k)
    a, b = _A * s, _B * s
    c = k.P["frame"]
    for inset, lw in ((a, 0.9), (b, 0.5)):
        bx = dk.box(slide, inset, inset, W - 2 * inset, H - 2 * inset, fill=None, line=dk._as_rgb(c), line_w=_lw(k, lw))
        dk.decorative(bx, "the map's neatline — the printed edge of the survey sheet, nothing to read in it")
    t = b - a
    cell = 0.50 * s
    sides = {"top": [], "bottom": [], "left": [], "right": []}
    for side, (x0, x1) in (("top", (b, W - b)), ("bottom", (b, W - b))):
        n = max(3, int(round((x1 - x0) / cell)))
        cw = (x1 - x0) / n
        y = a if side == "top" else H - b
        for i in range(0, n, 2):
            u, v = x0 + i * cw, x0 + (i + 1) * cw
            sides[side].append([(u, y), (v, y), (v, y + t), (u, y + t)])
        for cx in (a, W - b):                               # the solid corner squares
            sides[side].append([(cx, y), (cx + t, y), (cx + t, y + t), (cx, y + t)])
    for side, (y0, y1) in (("left", (b, H - b)), ("right", (b, H - b))):
        n = max(3, int(round((y1 - y0) / cell)))
        ch = (y1 - y0) / n
        x = a if side == "left" else W - b
        for i in range(1, n, 2):
            u, v = y0 + i * ch, y0 + (i + 1) * ch
            sides[side].append([(x, u), (x + t, u), (x + t, v), (x, v)])
    # the two side bands are ONE shape: either alone is a thin vertical line the conformance check reads as a column
    # rule running far past its text (vl_conformance.rules_past_content)
    sides = {"top": sides["top"], "bottom": sides["bottom"], "sides": sides["left"] + sides["right"]}
    for side, polys in sides.items():
        sh = na.multipoly(slide, polys, c)
        if sh is not None:
            dk.decorative(sh, "the graduated border of the map sheet: alternate cells along the neatline, a map's edge")


vn.GROUNDS[NAME] = _sheet


def _region(k):
    """The map's face inside the neatline (x0, y0, x1, y1): where terrain is drawn."""
    W, H, s, o = ctx(k)
    e = (_B + 0.06) * s
    return (e, e, W - e, H - e)


def _m(k):
    """The words' margin from the page edge."""
    W, H, s, o = ctx(k)
    return (0.82 if o == "land" else 0.64) * s


# ─────────────────────────────────────────── terrain ───────────────────────────────────────────
def _profile(d):
    """A hill's height at normalised distance d from its summit: a pointed crest, concave flanks, a smooth foot."""
    return (1.0 - d) * (1.0 - d) * (1.0 + d) if d < 1.0 else 0.0


class _Terrain:
    """A height field: hills (summit x, y, height, radii along and across, rotation) on a gently warped plane, so the
    contours wander like ground does. Deterministic for a seed."""

    def __init__(self, k, seed, warp=1.0):
        W, H, s, o = ctx(k)
        self.s = s
        self.hills = []
        self.troughs = []
        rnd = random.Random(seed)
        self.terms = []
        for lam, amp in ((4.2, 0.22), (2.3, 0.11), (1.25, 0.05)):
            f = 2.0 * math.pi / (lam * s)
            self.terms.append((f * rnd.uniform(0.8, 1.2), f * rnd.uniform(0.8, 1.2), rnd.uniform(0, 6.283),
                               rnd.uniform(0, 6.283), amp * s * warp))

    def hill(self, cx, cy, h, ax, ay=None, rot=0.0):
        ay = ax if ay is None else ay
        self.hills.append((cx, cy, h, 1.0 / max(ax, 1e-3), 1.0 / max(ay, 1e-3), math.cos(rot), math.sin(rot),
                           max(ax, ay) * 1.15, 0.0, 0.0))
        return self

    def plateau(self, cx, cy, h, hx, hy, R):
        """A hill with a flat top: the rect of half-sizes (hx, hy) round (cx, cy) at full height, the ground falling
        away over R all round it — its contours are even offsets of the top, however wide (a long figure set on a
        summit kept even rings; a stretched round hill packed them tight above and below)."""
        self.hills.append((cx, cy, h, 1.0 / max(R, 1e-3), 1.0 / max(R, 1e-3), 1.0, 0.0, max(hx, hy) + R * 1.15,
                           hx, hy))
        return self

    def _warp(self, x, y):
        dx = dy = 0.0
        for fx, fy, p1, p2, a in self.terms:
            dx += a * math.sin(fy * y + 0.37 * fx * x + p1)
            dy += a * math.sin(fx * x - 0.41 * fy * y + p2)
        return x + dx, y + dy

    def trough(self, pts, depth, width):
        """Carve a stream's bed along `pts` (source first): the ground dips across it, so the contours bend upstream
        in a V where they cross it, as they do on a map — shallow at the spring, full depth a little way down."""
        cum = [0.0]
        for p, q in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        m = 3.0 * width
        self.troughs.append((pts, cum, (min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m), depth, width))

    def _dip(self, x, y):
        v = 0.0
        for pts, cum, bb, depth, w in self.troughs:
            if not (bb[0] < x < bb[2] and bb[1] < y < bb[3]):
                continue
            best, along = 1e9, 0.0
            for i, (p, q) in enumerate(zip(pts, pts[1:])):
                dx, dy = q[0] - p[0], q[1] - p[1]
                L2 = dx * dx + dy * dy or 1e-9
                u = max(0.0, min(1.0, ((x - p[0]) * dx + (y - p[1]) * dy) / L2))
                ex, ey = p[0] + u * dx - x, p[1] + u * dy - y
                d2 = ex * ex + ey * ey
                if d2 < best:
                    best, along = d2, cum[i] + u * math.sqrt(L2)
            if best < 9.0 * w * w:
                v += depth * min(1.0, along / (0.8 * self.s)) * math.exp(-best / (w * w))
        return v

    def hills_at(self, x, y):
        """How many hills' slopes reach (x, y) — two or more is a valley or a saddle between them."""
        x, y = self._warp(x, y)
        n = 0
        for cx, cy, h, iax, iay, c, sn, reach, hx, hy in self.hills:
            dx, dy = x - cx, y - cy
            n += self._d2(dx, dy, iax, iay, c, sn, hx, hy) < 1.0
        return n

    @staticmethod
    def _d2(dx, dy, iax, iay, c, sn, hx, hy):
        """The squared normalised distance from a hill's top: from its summit point (an ellipse), or from the edge of
        a plateau's top — a rect with well-rounded corners, so its rings are even, round-cornered offsets."""
        u = dx * c + dy * sn
        w = -dx * sn + dy * c
        if not (hx or hy):
            u, w = u * iax, w * iay
            return u * u + w * w
        r = 0.75 * min(hx, hy)
        du, dv = max(abs(u) - (hx - r), 0.0), max(abs(w) - (hy - r), 0.0)
        d = max(0.0, math.sqrt(du * du + dv * dv) - r) * iax
        return d * d

    def at(self, x, y, only=None):
        ox, oy = x, y
        x, y = self._warp(x, y)
        v = -self._dip(ox, oy) if self.troughs and only is None else 0.0
        for cx, cy, h, iax, iay, c, sn, reach, hx, hy in (self.hills if only is None else self.hills[:only]):
            dx, dy = x - cx, y - cy
            if abs(dx) > reach or abs(dy) > reach:
                continue
            d2 = self._d2(dx, dy, iax, iay, c, sn, hx, hy)
            if d2 < 1.0:
                v += h * _profile(math.sqrt(d2))
        return v

    def summit(self, cx, cy, r):
        """Where the ground is highest within r of (cx, cy) — the warp moves a hill's crest a little."""
        best, bx, by = -1.0, cx, cy
        n = 10
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x, y = cx + r * i / n, cy + r * j / n
                v = self.at(x, y)
                if v > best:
                    best, bx, by = v, x, y
        return bx, by


def _contours(t, region, step, levels):
    """Marching squares over `region` (x0, y0, x1, y1) at grid `step` for each level:
    [(level index, points, closed)]."""
    x0, y0, x1, y1 = region
    nx = max(2, int((x1 - x0) / step))
    ny = max(2, int((y1 - y0) / step))
    gx = (x1 - x0) / nx
    gy = (y1 - y0) / ny
    V = [[t.at(x0 + i * gx, y0 + j * gy) for i in range(nx + 1)] for j in range(ny + 1)]
    lv = list(levels)
    segs = {i: [] for i in range(len(lv))}
    import bisect
    for j in range(ny):
        row, nrow = V[j], V[j + 1]
        for i in range(nx):
            a, b, c, d = row[i], row[i + 1], nrow[i + 1], nrow[i]
            lo = min(a, b, c, d)
            hi = max(a, b, c, d)
            if hi <= lv[0] or lo > lv[-1]:
                continue
            q0 = bisect.bisect_left(lv, lo)
            q1 = bisect.bisect_left(lv, hi)
            for q in range(q0, q1):
                L = lv[q]
                if not (lo <= L < hi):
                    continue
                case = (8 if a > L else 0) | (4 if b > L else 0) | (2 if c > L else 0) | (1 if d > L else 0)
                if case in (0, 15):
                    continue
                xa, ya = x0 + i * gx, y0 + j * gy

                def e(edge):
                    if edge == "t":
                        return ("h", i, j), (xa + gx * (L - a) / (b - a), ya)
                    if edge == "b":
                        return ("h", i, j + 1), (xa + gx * (L - d) / (c - d), ya + gy)
                    if edge == "l":
                        return ("v", i, j), (xa, ya + gy * (L - a) / (d - a))
                    return ("v", i + 1, j), (xa + gx, ya + gy * (L - b) / (c - b))
                if case in (5, 10):
                    centre = (a + b + c + d) / 4.0 > L
                    if (case == 5) == centre:
                        pairs = (("l", "t"), ("b", "r"))
                    else:
                        pairs = (("t", "r"), ("l", "b"))
                else:
                    pairs = (_MS[case],)
                for e1, e2 in pairs:
                    k1, p1 = e(e1)
                    k2, p2 = e(e2)
                    segs[q].append((k1, p1, k2, p2))
    out = []
    for q, ss in segs.items():
        for pts, closed in _chain(ss):
            out.append((q, pts, closed))
    return out


_MS = {1: ("l", "b"), 2: ("b", "r"), 3: ("l", "r"), 4: ("t", "r"), 6: ("t", "b"), 7: ("l", "t"), 8: ("l", "t"),
       9: ("t", "b"), 11: ("t", "r"), 12: ("l", "r"), 13: ("b", "r"), 14: ("l", "b")}


def _chain(segs):
    """Join marching-squares segments (keyed by the grid edge each end lies on) into polylines."""
    adj, pt = {}, {}
    for i, (k1, p1, k2, p2) in enumerate(segs):
        adj.setdefault(k1, []).append(i)
        adj.setdefault(k2, []).append(i)
        pt[k1], pt[k2] = p1, p2
    used = [False] * len(segs)
    out = []

    def walk(key, i):
        keys = [key]
        cur = key
        while i is not None:
            used[i] = True
            k1, _p1, k2, _p2 = segs[i]
            cur = k2 if k1 == cur else k1
            keys.append(cur)
            i = next((j for j in adj[cur] if not used[j]), None)
        return keys
    for key, ids in adj.items():
        if len(ids) == 1 and not used[ids[0]]:
            ks = walk(key, ids[0])
            out.append(([pt[q] for q in ks], False))
    for i in range(len(segs)):
        if not used[i]:
            ks = walk(segs[i][0], i)
            out.append(([pt[q] for q in ks], ks[0] == ks[-1] and len(ks) > 3))
    return out


def _resample(pts, closed, step):
    """Even spacing along a polyline (a closed one keeps its closing point), then one pass of neighbour averaging —
    the grid's small kinks go, the shape stays."""
    if len(pts) < 2:
        return pts
    seg = [math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:])]
    total = sum(seg)
    if total < 1e-6:
        return pts
    n = max(3 if closed else 2, int(round(total / step)))
    out, acc, si = [], 0.0, 0
    for k_ in range(n + 1):
        target = total * k_ / n
        while si < len(seg) - 1 and acc + seg[si] < target:
            acc += seg[si]
            si += 1
        f = 0.0 if seg[si] < 1e-9 else min(1.0, max(0.0, (target - acc) / seg[si]))
        p, q = pts[si], pts[si + 1]
        out.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f))
    if closed:
        ring = out[:-1]
        m = len(ring)
        sm = [((ring[i - 1][0] + 2 * ring[i][0] + ring[(i + 1) % m][0]) / 4.0,
               (ring[i - 1][1] + 2 * ring[i][1] + ring[(i + 1) % m][1]) / 4.0) for i in range(m)]
        return sm + sm[:1]
    mid = [((out[i - 1][0] + 2 * out[i][0] + out[i + 1][0]) / 4.0,
            (out[i - 1][1] + 2 * out[i][1] + out[i + 1][1]) / 4.0) for i in range(1, len(out) - 1)]
    return [out[0]] + mid + [out[-1]]


def _inside_t(p, q, r):
    """Liang–Barsky: the parameter interval of segment p→q inside rect r (x0, y0, x1, y1), or None."""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pp, qq in ((-dx, p[0] - r[0]), (dx, r[2] - p[0]), (-dy, p[1] - r[1]), (dy, r[3] - p[1])):
        if abs(pp) < 1e-12:
            if qq < 0:
                return None
        else:
            t = qq / pp
            if pp < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return (t0, t1) if t0 < t1 else None


def _knock(pts, closed, holes, box, min_len):
    """The parts of a polyline inside `box` and outside every hole — a map breaks its contours where a word sits.
    Returns [(points, closed)]: a ring that nothing cut stays closed."""
    runs, cur, cut = [], None, False
    first_from_start = None
    for si, (p, q) in enumerate(zip(pts, pts[1:])):
        iv = _inside_t(p, q, box)
        ivs = [iv] if iv else []
        if not iv or iv[0] > 1e-9 or iv[1] < 1 - 1e-9:
            cut = True
        for h in holes:
            hv = _inside_t(p, q, h)
            if not hv:
                continue
            nxt = []
            for a, b in ivs:
                if hv[1] <= a or hv[0] >= b:
                    nxt.append((a, b))
                    continue
                cut = True
                if a < hv[0]:
                    nxt.append((a, hv[0]))
                if hv[1] < b:
                    nxt.append((hv[1], b))
            ivs = nxt
        for a, b in ivs:
            pa = (p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a)
            pb = (p[0] + (q[0] - p[0]) * b, p[1] + (q[1] - p[1]) * b)
            if cur is not None and a <= 1e-9:
                cur.append(pb)
            else:
                if cur is not None:
                    runs.append(cur)
                cur = [pa, pb]
                if first_from_start is None:
                    first_from_start = si == 0 and a <= 1e-9
        if not ivs or ivs[-1][1] < 1 - 1e-9:
            if cur is not None:
                runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    if closed and not cut and len(runs) == 1:
        return [(runs[0], True)]
    if closed and len(runs) >= 2 and first_from_start and runs[-1][-1] == pts[-1]:
        runs[0] = runs[-1] + runs[0][1:]
        runs.pop()
    out = []
    for r in runs:
        ln = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(r, r[1:]))
        if ln >= min_len:
            out.append((r, False))
    return out


def _length(pts):
    return sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:]))


def _path(slide, runs, color, w, *, alpha=None, dash=None, fill=None):
    """Smooth runs [(points, closed)] as ONE editable outline shape (Catmull-Rom curves through the points)."""
    runs = [(p, c) for p, c in runs if len(p) >= 2]
    if not runs:
        return None
    xs = [x for p, _c in runs for x, _y in p]
    ys = [y for p, _c in runs for _x, y in p]
    x0, y0 = min(xs), min(ys)
    bw, bh = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
    U = na.U
    d = []
    for pts, closed in runs:
        u = [((x - x0) / bw * U, (y - y0) / bh * U) for x, y in pts]
        if closed:
            u = u[:-1] if u[0] == u[-1] else u
            d.append("<a:moveTo>{}</a:moveTo>{}<a:close/>".format(orn._pt(*u[0]), orn._smooth(u, closed=True)))
        else:
            d.append("<a:moveTo>{}</a:moveTo>{}".format(orn._pt(*u[0]), orn._smooth(u)))
    sh = na._custom(slide, x0, y0, bw, bh, '<a:path w="{u}" h="{u}"{f}>{d}</a:path>'.format(
        u=U, d="".join(d), f="" if fill else ' fill="none"'), fill=fill, line=na.hexstr(color), line_w=w)
    ln = sh._element.spPr.find(dk.qn("a:ln"))
    if ln is not None:
        sf = ln.find(dk.qn("a:solidFill"))
        if alpha is not None and sf is not None:
            sf[0].append(sf[0].makeelement(dk.qn("a:alpha"), {"val": str(int(round(alpha * 100000)))}))
        if dash and sf is not None:
            sf.addnext(ln.makeelement(dk.qn("a:prstDash"), {"val": dash}))
    return sh


def _box(r, pad=0.0):
    """(x, y, w, h) -> (x0, y0, x1, y1), padded."""
    x, y, w, h = r
    return (x - pad, y - pad, x + w + pad, y + h + pad)


def _relief(k, slide, t, holes, *, top=None, step=None, n=None, index=5, region=None):
    """Draw the terrain's contours: `n` levels from the foot up (or every `step` up to `top`), every `index`-th an
    index contour; each broken where it meets a hole (x0, y0, x1, y1) — the words, the panels, the marks."""
    W, H, s, o = ctx(k)
    region = region or _region(k)
    if top is None:
        top = max((h for _x, _y, h, *_r in t.hills), default=1.0) * 0.96
    if step is None:
        step = top / max(1, n or 14)
    levels = []
    L = step
    while L <= top + 1e-9:
        levels.append(L)
        L += step
    if not levels:
        return
    lines = _contours(t, region, 0.075 * s, levels)
    thin, thick = [], []
    for q, pts, closed in lines:
        pts = _resample(pts, closed, 0.085 * s)
        # a short cut-off piece reads as hatching, not ground, and a tiny ring at a crest as a smudge: an open run
        # under ~0.4in and a closed ring under ~0.45in are left out
        for run in _knock(pts, closed, holes, region, 0.12 * s):
            if _length(run[0]) < (0.45 if run[1] else 0.42) * s:
                continue
            (thick if (q + 1) % index == 0 else thin).append(run)
    dark = k.ground != "light"
    for runs, key, w, a, why in ((thin, "contour", 0.55, 0.55 if not dark else 0.46,
                                  "contour lines of the terrain: the map's ground, broken wherever words sit"),
                                 (thick, "index", 1.05, 0.85 if not dark else 0.72,
                                  "index contours, every fifth line drawn heavier as on a survey map")):
        sh = _path(slide, runs, k.P[key], _lw(k, w), alpha=a)
        if sh is not None:
            dk.decorative(sh, why)
            dk.overlap_intent(sh, "the contours run round the map's panels and marks, broken clear of them as a map is")


def _crosses(k, slide, holes, *, every=1.5, region=None):
    """Survey crosses on the map's grid, none on a word or a mark."""
    W, H, s, o = ctx(k)
    x0, y0, x1, y1 = region or _region(k)
    g = every * s
    arm = 0.07 * s
    nx, ny = int((x1 - x0) / g), int((y1 - y0) / g)
    ox = (W - nx * g) / 2.0
    oy = (H - ny * g) / 2.0
    segs = []
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = ox + i * g, oy + j * g
            if not (x0 + 0.2 * s < x < x1 - 0.2 * s and y0 + 0.2 * s < y < y1 - 0.2 * s):
                continue
            if any(h[0] - arm < x < h[2] + arm and h[1] - arm < y < h[3] + arm for h in holes):
                continue
            segs += [((x - arm, y), (x + arm, y)), ((x, y - arm), (x, y + arm))]
    sh = na.strokes(slide, segs, k.P["cross"], w=_lw(k, 0.55), alpha=0.55)
    if sh is not None:
        dk.decorative(sh, "survey crosses on the map grid: the sheet's graticule, nothing to read in them")
        dk.overlap_intent(sh, "the survey grid lies across the whole map face, under its panels")


def _rect_dist(x, y, r):
    dx = max(r[0] - x, 0.0, x - r[2])
    dy = max(r[1] - y, 0.0, y - r[3])
    return math.hypot(dx, dy)


def _voids(k, holes, avoid=(), n=2, min_r=0.9):
    """The largest empty rooms the words and marks leave on the map's face: [(radius, x, y)], each the centre of the
    widest circle clear of every hole and of the hills already raised (`avoid`: (x, y, r)). The terrain is raised
    there, so a page is a map wherever its words are not, on any canvas and with any length of copy."""
    W, H, s, o = ctx(k)
    x0, y0, x1, y1 = _region(k)
    g = 0.24 * s
    taken = list(avoid)
    out = []
    xs = [x0 + g * (i + 0.5) for i in range(int((x1 - x0) / g))]
    ys = [y0 + g * (j + 0.5) for j in range(int((y1 - y0) / g))]
    for _i in range(n):
        best = None
        for y in ys:
            for x in xs:
                dm = min([_rect_dist(x, y, h) for h in holes]
                         + [math.hypot(x - cx, y - cy) - cr for cx, cy, cr in taken]
                         + [min(x - x0, x1 - x, y - y0, y1 - y) + 1.0 * s])
                if best is None or dm > best[0]:
                    best = (dm, x, y)
        if best is None or best[0] < min_r * s:
            break
        out.append(best)
        taken.append((best[1], best[2], best[0] * 1.3))
    return out


def _fill(k, t, holes, avoid=(), n=2, h=0.5, seed=0):
    """Raise lower hills in the rooms the words leave (see _voids)."""
    W, H, s, o = ctx(k)
    rnd = random.Random(seed)
    for r_, x, y in _voids(k, holes, avoid, n=n):
        rr = min(r_, 2.6 * s)
        t.hill(x, y, h * rnd.uniform(0.85, 1.1), rr * 1.45, rr * rnd.uniform(1.0, 1.3), rnd.uniform(-0.8, 0.8))


def _climb(k, t, start, goal, lane, holes, *, grade=1.10, max_leg=None, seed=0):
    """A footpath from `start` up to `goal` as a walker takes it: across the slope at an easy grade (`grade` radians off
    straight uphill), turning back in a hairpin at the edge of its lane (x0, x1, and the left edge holds only below y2,
    where the words are) or before a hole, straight up for the last stretch. Each hairpin turns a little short of the
    lane's edge, by a different amount, so the legs differ as a real path's do. Returns its points; a walk that does
    not arrive falls back to a direct line."""
    W, H, s, o = ctx(k)
    step = 0.05 * s
    eps = 0.04 * s
    max_leg = max_leg or 2.2 * s
    rnd = random.Random(seed)
    span = max(0.0, lane[1] - lane[0])
    inset = (0.0, rnd.uniform(0.0, 0.30) * span)
    x, y = start
    pts = [(x, y)]
    side = 1 if goal[0] >= x else -1
    leg = 0.0
    for _i in range(900):
        gx_, gy_ = goal[0] - x, goal[1] - y
        dg = math.hypot(gx_, gy_)
        if dg < 0.30 * s:
            pts.append(goal)
            return pts
        # the slope of the hill being climbed only: a lower hill on the way would hold the walker on its own top
        tx, ty = (t.at(x + eps, y, 1) - t.at(x - eps, y, 1)), (t.at(x, y + eps, 1) - t.at(x, y - eps, 1))
        tn = math.hypot(tx, ty)
        ux, uy = gx_ / dg, gy_ / dg
        if tn > 1e-6 and tx * ux + ty * uy > 0:
            ux, uy = 0.55 * tx / tn + 0.45 * ux, 0.55 * ty / tn + 0.45 * uy
            un = math.hypot(ux, uy) or 1.0
            ux, uy = ux / un, uy / un
        th = grade if dg > 1.1 * s else grade * max(0.0, (dg - 0.35 * s) / (0.75 * s))
        for _try in range(2):
            px, py = -uy * side, ux * side
            dx, dy = math.cos(th) * ux + math.sin(th) * px, math.cos(th) * uy + math.sin(th) * py
            nx, ny = x + dx * step, y + dy * step
            bad = (((nx < lane[0] + inset[0] and ny > lane[2]) or nx > lane[1] - inset[1]) or leg > max_leg
                   or any(h[0] < nx < h[2] and h[1] < ny < h[3] for h in holes))
            if not bad:
                break
            side, leg = -side, 0.0
            inset = (rnd.uniform(0.0, 0.35) * span, rnd.uniform(0.0, 0.35) * span)
        x, y = nx, ny
        leg += step
        pts.append((x, y))
    return [start, goal]


def _stream_path(k, t, holes, marks=()):
    """A stream's course: it rises at a spring on the highest hill's flank and runs downhill, steepest way first, to
    the sheet's edge, clear of every word and mark — the longest such course among a ring of springs. None when no
    spring reaches the edge clear (then the map has no stream)."""
    W, H, s, o = ctx(k)
    if not t.hills:
        return None
    x0, y0, x1, y1 = _region(k)
    cx, cy, h = t.hills[0][:3]
    eps, step = 0.04 * s, 0.05 * s
    pad = 0.30 * s
    block = list(holes) + list(marks)

    def blocked(x, y):
        return any(b_[0] - pad < x < b_[2] + pad and b_[1] - pad < y < b_[3] + pad for b_ in block)
    best = None
    for i in range(16):
        ang = 2.0 * math.pi * i / 16.0
        ca, sa = math.cos(ang), math.sin(ang)
        r = 0.3 * s
        while r < 5.0 * s and t.at(cx + ca * r, cy + sa * r) > 0.55 * h:
            r += 0.05 * s
        x, y = cx + ca * r, cy + sa * r
        if blocked(x, y) or not (x0 < x < x1 and y0 < y < y1):
            continue
        dx, dy = ca, sa
        pts, ok, flat, valley = [(x, y)], False, 0, False
        for _j in range(400):
            gx = t.at(x + eps, y) - t.at(x - eps, y)
            gy = t.at(x, y + eps) - t.at(x, y - eps)
            gn = math.hypot(gx, gy)
            if gn > 1e-5:
                ndx, ndy = 0.6 * dx - 0.4 * gx / gn, 0.6 * dy - 0.4 * gy / gn
                nn = math.hypot(ndx, ndy) or 1.0
                dx, dy = ndx / nn, ndy / nn
            x, y = x + dx * step, y + dy * step
            if not (x0 < x < x1 and y0 < y < y1):
                pts.append((min(max(x, x0), x1), min(max(y, y0), y1)))
                ok = True
                break
            if blocked(x, y):
                break
            flat += 1 if t.at(x, y) < 0.06 * h else 0
            valley = valley or t.hills_at(x, y) >= 2
            pts.append((x, y))
        # a stream ruled straight down one hill's flank, or across the empty plain, reads as a stray line: it must run
        # down a valley between two hills
        if flat * step > 1.0 * s or not valley:
            continue
        n_ = len(pts) * step
        if ok and 1.6 * s < n_ < 7.0 * s and (best is None or n_ > best[0]):
            best = (n_, pts)
    if best is None:
        return None
    return _resample(_resample(best[1], False, 0.12 * s), False, 0.08 * s)


def _stream(k, slide, pts):
    """Draw a stream along `pts` (source first) in water blue, finer near its spring."""
    W, H, s, o = ctx(k)
    if not pts:
        return
    cut = max(2, len(pts) * 2 // 5)
    for part, w in ((pts[:cut + 1], 0.9), (pts[cut:], 1.6)):
        sh = _path(slide, [(part, False)], k.P["water"], _lw(k, w))
        if sh is not None:
            dk.decorative(sh, "a stream running from its spring down to the sheet's edge: the map's water")
            dk.overlap_intent(sh, "the stream crosses the contour lines as water crosses ground")


def _summit(k, slide, cx, cy, size):
    """A summit marker: a solid triangle with a pale dot — the trig point of a survey map. Returns its rect."""
    hgt = size * 0.87
    pts = [(cx, cy - hgt * 0.62), (cx + size / 2.0, cy + hgt * 0.38), (cx - size / 2.0, cy + hgt * 0.38)]
    tri = na.poly(slide, pts, fill=k.P["marker"])
    if tri is not None:
        dk.decorative(tri, "the summit marker: a survey triangle on the hill's highest point")
    dot = na.disc(slide, cx, cy + hgt * 0.05, size * 0.22, k.P["ground"])
    dk.decorative(dot, "the dot inside the summit triangle, as a trig point is drawn")
    dk.overlap_intent(dot, "the dot sits inside the summit triangle by construction")
    return (cx - size / 2.0, cy - hgt * 0.62, size, hgt)


def _north(k, slide, cx, cy, h):
    """A north arrow: a compass needle on its pivot — the north half split solid and open, the south half a light
    outline — drawn, with no letter."""
    W, H, s, o = ctx(k)
    hw = h * 0.13
    top, foot = cy - h / 2.0, cy + h / 2.0
    ink, paper = k.P["marker"], k.P["ground"]
    lw = _lw(k, 0.7)
    south = na.poly(slide, [(cx - hw, cy), (cx, foot), (cx + hw, cy)], fill=paper, line=ink, line_w=_lw(k, 0.5))
    left = na.poly(slide, [(cx, top), (cx, cy), (cx - hw, cy)], fill=ink, line=ink, line_w=lw)
    right = na.poly(slide, [(cx, top), (cx + hw, cy), (cx, cy)], fill=paper, line=ink, line_w=lw)
    pivot = na.disc(slide, cx, cy, h * 0.11, paper)
    pivot.line.color.rgb = dk._as_rgb(ink)
    pivot.line.width = dk.Pt(lw)
    for sh in (south, left, right, pivot):
        if sh is not None:
            dk.decorative(sh, "the north arrow: the map's orientation mark, drawn without a letter")
            dk.overlap_intent(sh, "the north arrow's parts are one drawn mark")
    return (cx - hw, top, 2 * hw, h)


def _scale(k, slide, x, y, w):
    """A scale bar without figures: four alternate cells on a thin bar and ticks at its ends — a map's measure."""
    W, H, s, o = ctx(k)
    bh = 0.075 * s
    n = 4
    cw = w / n
    cells = [[(x + i * cw, y), (x + (i + 1) * cw, y), (x + (i + 1) * cw, y + bh), (x + i * cw, y + bh)]
             for i in range(0, n, 2)]
    fill = na.multipoly(slide, cells, k.P["marker"])
    outline = dk.box(slide, x, y, w, bh, fill=None, line=dk._as_rgb(k.P["marker"]), line_w=_lw(k, 0.6))
    ticks = na.strokes(slide, [((x + i * cw, y), (x + i * cw, y - 0.07 * s)) for i in (0, 2, 4)], k.P["marker"],
                       w=_lw(k, 0.6))
    for sh in (fill, outline, ticks):
        if sh is not None:
            dk.decorative(sh, "the scale bar: alternate cells as on a map's measure, no figures on it")
            dk.overlap_intent(sh, "the scale bar's cells, outline and ticks are one drawn mark")
    return (x, y - 0.07 * s, w, bh + 0.07 * s)


def _trail(k, slide, pts, holes, dense=False):
    """A dashed footpath through `pts` (a few waypoints, or a walked path when `dense`), smooth, broken where it meets
    a hole."""
    W, H, s, o = ctx(k)
    if dense:                                  # a walked path: its hairpins rounded as feet round them
        dense = _resample(_resample(_resample(pts, False, 0.08 * s), False, 0.08 * s), False, 0.06 * s)
    else:
        dense = _catmull(pts, 0.05 * s)
    runs = _knock(dense, False, holes, _region(k), 0.08 * s)
    sh = _path(slide, runs, k.P["trail"], _lw(k, 1.7), dash="dash")
    if sh is not None:
        dk.decorative(sh, "the dashed footpath across the contours, from point to point")
        dk.overlap_intent(sh, "the footpath runs under the waypoint markers it joins")


def _catmull(pts, step):
    """Points along a Catmull-Rom curve through `pts`, about `step` apart."""
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, n - 1)]
        ln = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        m = max(2, int(ln / step))
        for j in range(m):
            t = j / float(m)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t
                                    + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def _flag(k, slide, x, y, h):
    """A small pennant planted at (x, y): its pole and its flag — the top is reached."""
    W, H, s, o = ctx(k)
    pole = na.polyline(slide, [(x, y), (x, y - h)], k.P["marker"], w=_lw(k, 1.1))
    flag = na.poly(slide, [(x, y - h), (x + h * 0.55, y - h * 0.80), (x, y - h * 0.60)], fill=k.P["trail"])
    for sh in (pole, flag):
        if sh is not None:
            dk.decorative(sh, "a pennant planted on the summit: the end of the trail")
            dk.overlap_intent(sh, "the pennant's pole and flag are one drawn mark")
    return (x - 0.05 * s, y - h, h * 0.6, h)


# ─────────────────────────────────────────── words ───────────────────────────────────────────
def _figure_ink(top, z):
    """Where a figure's digits are inked inside its text box (top, bottom in inches), the box's top at `top` and the
    size `z` pt. Measured on the render (LibreOffice, Trebuchet MS at 168pt): the digits run from 0.29 to 1.01 of the
    size below the box's top; taken a little wider, so another face's metrics stay inside."""
    return top + 0.26 * z / 72.0, top + 1.05 * z / 72.0


def _sizes(ds):
    out = {}
    for d in ds if isinstance(ds, (list, tuple)) else [ds]:
        out.update(getattr(d, "sizes", {}) or {})
    return out


def _ink(k, rects, texts, sizes, align="l", pad=0.0):
    """Holes for the planned words: each field's box cut to the width its line(s) take (a short title does not knock
    out its whole column), padded."""
    W, H, s, o = ctx(k)
    out = []
    for f_, (x, y, w, h) in rects.items():
        t = texts.get(f_)
        iw = w
        z = sizes.get(f_, vl.TYPE[NAME][f_][0] * s) if f_ in vl.TYPE[NAME] else 16.0 * s
        p = max(pad, 0.42 * z / 72.0)        # a halo that grows with the type: a headline keeps the lines further off
        if t and f_ in vl.TYPE[NAME]:
            try:
                lines = [ln for ln in t.split("\n") if ln.strip()]
                if len(lines) == 1:
                    one = _v2.ink_w(k, f_, lines[0], z)
                    if one <= w * vl.HEADROOM:
                        lines = [lines[0]]
                    else:
                        lines = vl._break_lines(k, f_, lines[0], z, w * vl.HEADROOM)
                iw = min(w, max(_v2.ink_w(k, f_, ln, z) for ln in lines) + 0.06 * s)
            except Exception:                       # a measure that cannot run keeps the whole column clear
                iw = w
        if align == "c":
            x = x + (w - iw) / 2.0
        elif align == "r":
            x = x + w - iw
        out.append((x - p, y - p * 0.6, x + iw + p, y + h + p * 0.6))
    return out


def _texts(f, extra=None):
    out = {k_: v for k_, v in ((n, text_of(f, n)) for n in ("kicker", "title", "subtitle", "body", "caption", "quote",
                                                            "attribution", "number", "label", "note", "line")) if v}
    if extra:
        out.update(extra)
    return out


def _seed(slide, page):
    return 7 + 31 * _v2.page_no(slide) + sum(ord(c) for c in page)


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=3)
def _tp_cover(k, slide, f, image):
    """The sheet's front: the kicker, title and subtitle in the lowland at the left; a summit's contour rings beside
    them (above them on a portrait or square page) with its survey triangle and a stream down a valley; a north arrow,
    a scale bar under the words."""
    W, H, s, o = ctx(k)
    m = _m(k)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.20 * s), (_v2.fields(f, ("title",)), 0.26 * s),
              (_v2.fields(f, ("subtitle",)), 0.0)]
    rx0, ry0, rx1, ry1 = _region(k)
    if o == "land":
        tw = (0.50, 0.57, 0.66)[alt()] * W
        r, ds = _v2.stack(k, slide, "cover", m, tw, 0.15 * H, H - 1.0 * s, groups, anchor="middle")
        right = m + tw
        cx, cy = right + (rx1 - right) * 0.52, 0.47 * H
        ax, ay = max(1.6 * s, (rx1 - right) * 0.78), 0.50 * H
        t = _Terrain(k, _seed(slide, "cover")).hill(cx, cy, 1.0, ax, ay, -0.35)
        t.hill(rx1 - 0.4 * s, ry1 - 0.2 * s, 0.50, 1.7 * s, 1.3 * s, 0.4)
        arrow = (rx1 - 0.55 * s, ry0 + 0.70 * s, 0.95 * s)
    else:
        top_h = (0.44, 0.38, 0.32)[alt()] * H
        r, ds = _v2.stack(k, slide, "cover", 0.09 * W, 0.82 * W, ry0 + top_h + 0.25 * s, H - 1.0 * s, groups,
                          anchor="middle")
        cx, cy = 0.56 * W, ry0 + top_h * 0.50
        ax, ay = 0.46 * W, top_h * 0.64
        t = _Terrain(k, _seed(slide, "cover")).hill(cx, cy, 1.0, ax, ay, -0.25)
        arrow = (rx1 - 0.45 * s, ry0 + 0.62 * s, 0.80 * s)
    texts = _texts(f, {"kicker": _v2.caps(text_of(f, "kicker") or "")})
    holes = _ink(k, r, texts, _sizes(ds), pad=0.16 * s)
    sx, sy = t.summit(cx, cy, 0.35 * min(ax, ay))
    tri = 0.30 * s
    marks = [_box((sx - tri, sy - tri, 2 * tri, 2 * tri), 0.10 * s)]
    ax_, ay_, ah = arrow
    marks.append(_box((ax_ - 0.25 * ah, ay_ - 0.55 * ah, 0.5 * ah, 1.1 * ah), 0.10 * s))
    foot = max((v[1] + v[3] for v in r.values()), default=0.0)
    bar = None
    bw = min(1.8 * s, 0.30 * W)
    by = ry1 - 0.38 * s
    if foot < by - 0.45 * s:
        bar = (m if o == "land" else 0.09 * W, by, bw)
        marks.append(_box((bar[0], by - 0.07 * s, bw, 0.15 * s), 0.12 * s))
    _fill(k, t, holes + marks, [(cx, cy, 0.8 * min(ax, ay))], n=2, h=0.45, seed=_seed(slide, "cover"))
    water = _stream_path(k, t, holes, marks)
    if water:
        t.trough(water, 0.14, 0.20 * s)
    _relief(k, slide, t, holes + marks, n=15)
    _crosses(k, slide, holes + marks)
    _stream(k, slide, water)
    _summit(k, slide, sx, sy, tri)
    _north(k, slide, ax_, ay_, ah)
    if bar:
        _scale(k, slide, *bar)
    _run_all(ds)
    return r


@register(NAME, "section", alts=2)
def _tp_section(k, slide, f, image):
    """A divider: the caller's number set at a peak — the hill's contour rings close round it as round a summit; the
    kicker and title beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    num = text_of(f, "number")
    rx0, ry0, rx1, ry1 = _region(k)
    r, ds = {}, []
    start = {"number": (150 if alt() == 0 else 112) * s}
    if o == "land":
        nb = (m, 0.18 * H, (0.40 if alt() == 0 else 0.34) * W, 0.64 * H)
        col = (nb[0] + nb[2] + 0.7 * s, 0.14 * H, W - m - nb[0] - nb[2] - 0.7 * s, 0.72 * H)
        align = "l"
    else:
        nb = (0.12 * W, ry0 + 0.45 * s, 0.76 * W, (0.36 if alt() == 0 else 0.28) * H)
        col = (0.09 * W, nb[1] + nb[3] + 0.5 * s, 0.82 * W, H - 0.95 * s - nb[1] - nb[3] - 0.5 * s)
        align = "c"
    if num:
        nr, nd = _v2.flow(k, slide, "section", nb, [("number", num)], anchor="middle", align="c", start=start)
        r.update(nr)
        ds.append(nd)
    tr, tds = _v2.stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3],
                        [(_v2.fields(f, ("kicker",), ("kicker",)), 0.16 * s), (_v2.fields(f, ("title",)), 0.0)],
                        anchor="middle", align=align)
    r.update(tr)
    ds += tds
    sizes = _sizes(ds)
    texts = _texts(f, {"kicker": _v2.caps(text_of(f, "kicker") or "")})
    holes = _ink(k, {f_: v for f_, v in r.items() if f_ != "number"}, texts, sizes, align=align, pad=0.16 * s)
    t = _Terrain(k, _seed(slide, "section"), warp=0.8)
    if num and "number" in r:
        nx, ny, nw, nh = r["number"]
        z = sizes.get("number", start["number"])
        iw = min(nw, _v2.ink_w(k, "number", num, z))
        top_, bot_ = _figure_ink(ny, z)
        ih = bot_ - top_
        cx, cy = nx + nw / 2.0, (top_ + bot_) / 2.0
        ax = ay = 2.8 * s                      # the number set on the summit's flat top, the rings even round it
        t.plateau(cx, cy, 1.0, iw / 2.0 + 0.24 * s, ih / 2.0 + 0.22 * s, ax)
        holes.append((cx - iw / 2.0 - 0.14 * s, top_ - 0.16 * s, cx + iw / 2.0 + 0.14 * s, bot_ + 0.18 * s))
        top = _profile(0.07) * 0.99
    else:
        cx, cy = (nb[0] + nb[2] / 2.0, nb[1] + nb[3] / 2.0)
        ax, ay = nb[2] * 0.8, nb[3] * 0.8
        t.hill(cx, cy, 1.0, ax, ay)
        top = 0.9
    _fill(k, t, holes, [(cx, cy, 0.75 * min(ax, ay))], n=2, h=0.42, seed=_seed(slide, "section"))
    _relief(k, slide, t, holes, top=top, n=11)
    _crosses(k, slide, holes, every=1.7)
    _run_all(ds)
    return r


@register(NAME, "image_text", alts=3)
def _tp_image_text(k, slide, f, image):
    """The caller's picture as an inset map panel — a pale mount with its own neatline, laid on the sheet, the contours
    running round it; the caption under it, the kicker, title and body beside it (under it on a portrait or square
    page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    cap = text_of(f, "caption")
    rx0, ry0, rx1, ry1 = _region(k)
    if o == "land":
        wide = W / H >= 1.5
        frac = ((0.46, 0.40, 0.34) if wide else (0.40, 0.35, 0.30))[alt()]
        img = (m, 0.17 * H, frac * W, (0.56 if cap else 0.64) * H)
    else:
        img = (0.12 * W, ry0 + 0.40 * s, 0.76 * W, (0.34, 0.27, 0.20)[alt()] * H)
    r, ds = {}, []
    b = 0.11 * s
    foot = img[1] + img[3] + b
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (img[0] - b, foot + 0.22 * s, img[2] + 2 * b, 1.0 * s),
                          [("caption", cap)])
        r.update(cr)
        ds.append(cd)
        foot = max(v[1] + v[3] for v in cr.values())
    if o == "land":
        cx0 = img[0] + img[2] + b + 0.75 * s
        col = (cx0, 0.14 * H, W - m - cx0, 0.74 * H)
    else:
        col = (0.09 * W, foot + 0.38 * s, 0.82 * W, H - 0.95 * s - foot - 0.38 * s)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
              (_v2.fields(f, ("body",)), 0.0)]
    if o == "land":
        tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3], groups, anchor="middle")
    else:                  # under the picture: the story stays near its picture, the map takes the room below it
        tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3], groups, anchor="top")
        room = col[1] + col[3] - max((v[1] + v[3] for v in tr.values()), default=col[1])
        if room > 0.05 * s:
            y_ = col[1] + room * 0.22
            tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], y_, col[1] + col[3], groups, anchor="top",
                                start=_sizes(tds))
    r.update(tr)
    ds = tds + ds
    texts = _texts(f, {"kicker": _v2.caps(text_of(f, "kicker") or "")})
    holes = _ink(k, r, texts, _sizes(ds), pad=0.15 * s)
    mount = (img[0] - b, img[1] - b, img[2] + 2 * b, img[3] + 2 * b)
    holes.append(_box(mount, 0.16 * s))
    t = _Terrain(k, _seed(slide, "image_text"))
    # the inset lies ON the map: a hill runs on under it, its outer contours showing all round the panel's edge
    hx, hy = img[0] + img[2] * 0.55, img[1] + img[3] * 0.45
    t.hill(hx, hy, 1.0, img[2] * 0.62 + 1.3 * s, img[3] * 0.62 + 1.3 * s, 0.2)
    _fill(k, t, holes, [(hx, hy, 0.5 * min(img[2], img[3]) + 0.6 * s)], n=2, h=0.5, seed=_seed(slide, "image_text"))
    _relief(k, slide, t, holes, n=13)
    _crosses(k, slide, holes, every=1.6)
    mt = dk.box(slide, *mount, fill=k.P["panel"], line=dk._as_rgb(k.P["frame"]), line_w=_lw(k, 0.9))
    dk.decorative(mt, "the inset panel's mount and neatline: it frames the picture, the picture carries the meaning")
    na.soft_shadow(mt, blur=0.06, dist=0.025, alpha=0.16)
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    tick = 0.16 * s
    segs = []
    for (px, py), (sx_, sy_) in (((mount[0], mount[1]), (-1, -1)), ((mount[0] + mount[2], mount[1]), (1, -1)),
                                 ((mount[0], mount[1] + mount[3]), (-1, 1)),
                                 ((mount[0] + mount[2], mount[1] + mount[3]), (1, 1))):
        segs += [((px + sx_ * 0.05 * s, py), (px + sx_ * (0.05 * s + tick), py)),
                 ((px, py + sy_ * 0.05 * s), (px, py + sy_ * (0.05 * s + tick)))]
    tk = na.strokes(slide, segs, k.P["frame"], w=_lw(k, 0.7))
    if tk is not None:
        dk.decorative(tk, "corner ticks registering the inset panel on the sheet")
        dk.overlap_intent(tk, "the corner ticks meet the inset's corners by construction")
    _run_all(ds)
    return r


def _ordered(f):
    v = f.get("ordered")
    if v not in (None, True, False):
        raise ValueError("topo.points(): ordered= takes True or False, got {!r}".format(v))
    return bool(v)


def _waypoint(k, slide, page, cx, cy, d, num):
    """PLAN a waypoint marker: a pale disc ringed in the trail's colour carrying its number. Returns (rects, draw)."""
    W, H, s, o = ctx(k)
    inner = d * 0.70
    nr, nd = _v2.flow(k, slide, page, (cx - inner / 2.0, cy - inner / 2.0, inner, inner), [("item_no", num)],
                      anchor="middle", align="c", ink=k.P["trail"])

    def draw():
        disc = na.disc(slide, cx, cy, d, k.P["panel"])
        disc.line.color.rgb = dk._as_rgb(k.P["trail"])
        disc.line.width = dk.Pt(_lw(k, 1.6))
        dk.decorative(disc, "the waypoint marker: the number on it carries the meaning")
        nd()
    return nr, draw


@register(NAME, "points", alts=3)
def _tp_points(k, slide, f, image):
    """Waypoints: each point a numbered marker on the map with its head and line under it. With ordered=True the
    markers climb and a dashed trail crosses the contours through them in order, to the summit at the last; without it
    each marker stands on a rise of its own and nothing joins them. Columns across a landscape page, rows on a portrait
    or square one; long copy gives the title less room, then sets the points in two columns of rows."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    ordered = _ordered(f)
    m = _m(k)
    rx0, ry0, rx1, ry1 = _region(k)
    x0, w0 = m, W - 2 * m
    head_top = ry0 + 0.45 * s
    r, ds = _v2.stack(k, slide, "points", x0, w0, head_top, (0.30 if alt() == 0 else 0.34 if alt() == 1 else 0.37) * H,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", start=None if alt() < 2 else {"title": 28 * s})
    top = max((v[1] + v[3] for v in r.values()), default=head_top) + 0.40 * s
    bottom = H - 0.90 * s
    d = (0.58 if alt() < 2 else 0.50) * s
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    nos = [str(i + 1) for i in range(n)]
    art, marks, centres = [], [], []
    columns = o == "land" and alt() < 2
    cols = n if columns else (2 if (alt() == 2 and n >= 3) else 1)
    if columns:
        gap = (0.50 if alt() == 0 else 0.38) * s
        cw = (w0 - (n - 1) * gap) / n
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw, bottom - top - d - 0.2 * s), it, {"anchor": "top"})
                                                       for it in items])
        need = [max((v[1] + v[3] for v in pr.values()), default=0.0) for pr, _d in probe]
        lift = d / 2.0 + 0.18 * s                  # marker centre to the words under it
        F = [bottom - need[i] - lift for i in range(n)]
        rise = (0.50 * s if ordered else 0.0)
        while True:
            yb = min(F[i] + i * rise for i in range(n))
            if yb - (n - 1) * rise >= top + d / 2.0 or rise <= 1e-6:
                break
            rise = max(0.0, rise - 0.05 * s)
        if yb - (n - 1) * rise < top + d / 2.0 - 1e-6:
            raise vl.VLTextOverflow("topo.points(): the points need {:.2f}in under the title, the page has {:.2f}in"
                                    .format(max(need) + lift + d / 2.0, bottom - top))
        free = (yb - (n - 1) * rise) - (top + d / 2.0)
        yb -= free * 0.42                         # the group at the optical centre of the room left
        sizes = _sizes([dd for _pr, dd in probe])
        specs = []
        for i in range(n):
            cx = x0 + i * (cw + gap) + d / 2.0
            cy = yb - i * rise
            centres.append((cx, cy))
            specs.append(((x0 + i * (cw + gap), cy + lift, cw, bottom - cy - lift + 0.01), items[i],
                          {"anchor": "top", "start": sizes}))
        planned = _v2.plan_together(k, slide, "points", specs)
    else:
        rows = -(-n // cols)
        gap, cgap = (0.34 if alt() < 2 else 0.24) * s, 0.40 * s
        cw = (w0 - (cols - 1) * cgap) / cols
        tx = d + 0.28 * s                          # the words start right of the marker
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - tx, (bottom - top - (rows - 1) * gap) / rows), it,
                                                        {"anchor": "top"}) for it in items])
        hs = [max(max((v[1] + v[3] for v in pr.values()), default=0.0), d) for pr, _d in probe]
        row_h = [max(hs[i] for i in range(rw * cols, min(n, rw * cols + cols))) for rw in range(rows)]
        block = sum(row_h) + gap * (rows - 1)
        if block > bottom - top + 1e-6:
            raise vl.VLTextOverflow("topo.points(): the points need {:.2f}in, the page has {:.2f}in".format(
                block, bottom - top))
        y = top + (bottom - top - block) * 0.20
        ys = []
        for rw in range(rows):
            ys.append(y)
            y += row_h[rw] + gap
        sizes = _sizes([dd for _pr, dd in probe])
        specs = []
        for i in range(n):
            bx, by = x0 + (i % cols) * (cw + cgap), ys[i // cols]
            centres.append((bx + d / 2.0, by + d / 2.0))
            specs.append(((bx + tx, by, cw - tx, row_h[i // cols] + 0.01), items[i], {"anchor": "top", "start": sizes}))
        planned = _v2.plan_together(k, slide, "points", specs)
    for i, (pr, pd) in enumerate(planned):
        r.update({"{}_{}".format(f_, i): v for f_, v in pr.items()})
        ds.append(pd)
    texts = _texts(f, {"kicker": _v2.caps(text_of(f, "kicker") or "")})
    holes = _ink(k, {f_: v for f_, v in r.items() if f_ in ("kicker", "title")}, texts, _sizes(ds), pad=0.15 * s)
    for i, (pr, pd) in enumerate(planned):
        tx_ = dict(zip(("item_head", "item_line"), pts[i]))
        holes += _ink(k, pr, {f_: v for f_, v in tx_.items() if v}, _sizes([pd]), pad=0.18 * s)
    for (cx, cy) in centres:
        e = d / 2.0 + 0.16 * s
        marks.append((cx - e, cy - e, cx + e, cy + e))
    t = _Terrain(k, _seed(slide, "points"))
    raised = []
    if ordered and columns:                    # the climb: the last waypoint stands on the summit
        sx, sy = centres[-1]
        fx, fy = centres[0]
        reach = max(math.hypot(sx - fx, sy - fy) * 1.2, 2.4 * s)
        t.hill(sx, sy, 1.0, reach, reach * 0.70, -0.3)
        raised.append((sx, sy, 0.6 * reach))
        _fill(k, t, holes + marks, raised, n=2, h=0.48, seed=_seed(slide, "points"))
    elif columns:                              # a broad rise under the waypoints, its crest between them: no climb
        my = sum(c[1] for c in centres) / n
        t.hill(x0 + w0 * 0.58, my - 0.2 * s, 1.0, 0.44 * W, 0.42 * H, 0.15)
        raised.append((x0 + w0 * 0.58, my, 0.30 * W))
        _fill(k, t, holes + marks, raised, n=2, h=0.48, seed=_seed(slide, "points"))
    else:                                      # the ground rises in the room the words leave
        _fill(k, t, holes + marks, raised, n=1, h=1.0, seed=_seed(slide, "points"))
        if t.hills:
            raised.append((t.hills[0][0], t.hills[0][1], 1.6 * s))
        _fill(k, t, holes + marks, raised, n=2, h=0.5, seed=_seed(slide, "points") + 1)
    _relief(k, slide, t, holes + marks, n=13)
    _crosses(k, slide, holes + marks, every=1.6)
    if ordered and (columns or cols == 1):
        way = []
        fx, fy = centres[0]
        if columns:
            way.append((rx0 + 0.02 * s, fy + 0.30 * s))
            for i, (cx, cy) in enumerate(centres):
                way.append((cx, cy))
                if i < n - 1:
                    nx_, ny_ = centres[i + 1]
                    way.append(((cx + nx_) / 2.0, (cy + ny_) / 2.0 - 0.20 * s))
        else:
            way.append((rx0 + 0.02 * s, fy - 0.25 * s))
            for i, (cx, cy) in enumerate(centres):
                way.append((cx, cy))
                if i < n - 1:
                    nx_, ny_ = centres[i + 1]
                    way.append((cx - min(0.22 * s, cx - rx0 - 0.08 * s), (cy + ny_) / 2.0))
        _trail(k, slide, way, holes)
    for i, (cx, cy) in enumerate(centres):
        nr, nd = _waypoint(k, slide, "points", cx, cy, d, nos[i])
        r.update({"item_no_{}".format(i): v for v in nr.values()})
        art.append(nd)
    _run_all(art + ds)
    return r


@register(NAME, "quote", alts=2)
def _tp_quote(k, slide, f, image):
    """The quote in a map legend box — a pale panel in a double rule, the quote in italic serif, a hairline, and the
    attribution set as a legend entry beside a summit triangle; the terrain all round the box."""
    W, H, s, o = ctx(k)
    rx0, ry0, rx1, ry1 = _region(k)
    a = text_of(f, "attribution")
    if o == "land":
        bx, bw = _m(k), (0.60 if alt() == 0 else 0.74) * W
        y0, y1 = ry0 + 0.55 * s, ry1 - 0.55 * s
    else:
        bx, bw = 0.08 * W, 0.84 * W
        y0, y1 = (0.36 if alt() == 0 else 0.22) * H, ry1 - 0.50 * s
    pad = 0.42 * s
    sym = 0.26 * s
    ix, iw = bx + pad, bw - 2 * pad
    ah, ar, ad = 0.0, None, None
    if a:
        ar, ad = _v2.flow(k, slide, "quote", (ix + sym + 0.22 * s, 0, iw - sym - 0.22 * s, y1 - y0),
                          [("attribution", a)], anchor="top")
        ah = max(v[1] + v[3] for v in ar.values()) + 0.40 * s
    qr, qds = _v2.stack(k, slide, "quote", ix, iw, y0 + pad, y1 - pad - ah, [(_v2.fields(f, ("quote",)), 0.0)],
                        anchor="top")
    # planned again at the size it came to: flowed afresh at the design size, a Chinese quote broke its clauses one
    # line taller than it is set at that size, and the legend box kept a blank line under it (4:3, 2026-10-22)
    qr, qds = _v2.stack(k, slide, "quote", ix, iw, y0 + pad, y1 - pad - ah, [(_v2.fields(f, ("quote",)), 0.0)],
                        anchor="top", start=_sizes(qds))
    qfoot = max((v[1] + v[3] for v in qr.values()), default=y0 + pad)
    box_h = (qfoot - y0) + ah + pad
    by = y0 + max(0.0, (y1 - y0 - box_h) * 0.45)
    dy = by - y0
    qr, qds = _v2.stack(k, slide, "quote", ix, iw, y0 + pad + dy, y1 - pad - ah, [(_v2.fields(f, ("quote",)), 0.0)],
                        anchor="top", start=_sizes(qds))
    r = dict(qr)
    ds = list(qds)
    rule_y = None
    if a:
        rule_y = qfoot + dy + 0.20 * s
        ar, ad = _v2.flow(k, slide, "quote", (ix + sym + 0.22 * s, rule_y + 0.20 * s, iw - sym - 0.22 * s,
                                              y1 - rule_y), [("attribution", a)], anchor="top", start=_sizes([ad]))
        r.update(ar)
        ds.append(ad)
    box = (bx, by, bw, box_h)
    t = _Terrain(k, _seed(slide, "quote"))
    if o == "land":
        hx, hy = bx + bw + (rx1 - bx - bw) * 0.55, 0.44 * H
        hr = max(1.8 * s, (rx1 - bx - bw) * 0.95)
        t.hill(hx, hy, 1.0, hr, 0.52 * H, 0.4)
    else:
        hx, hy = 0.55 * W, ry0 + (by - ry0) * 0.48
        hr = 0.48 * W
        t.hill(hx, hy, 1.0, hr, max(1.2 * s, (by - ry0) * 0.75), -0.3)
    holes = [_box(box, 0.18 * s)]
    _fill(k, t, holes, [(hx, hy, 0.7 * hr)], n=2, h=0.45, seed=_seed(slide, "quote"))
    _relief(k, slide, t, holes, n=13)
    _crosses(k, slide, holes, every=1.6)
    pan = dk.box(slide, *box, fill=k.P["panel"], line=dk._as_rgb(k.P["frame"]), line_w=_lw(k, 1.0))
    dk.decorative(pan, "the map legend's box: the ground the quote is set on, the words carry the meaning")
    e = 0.07 * s
    inner = dk.box(slide, bx + e, by + e, bw - 2 * e, box_h - 2 * e, fill=None, line=dk._as_rgb(k.P["frame"]),
                   line_w=_lw(k, 0.4))
    dk.decorative(inner, "the legend box's inner rule, the double frame of a map legend")
    if a:
        hl = na.strokes(slide, [((ix, rule_y), (ix + iw, rule_y))], k.P["frame"], w=_lw(k, 0.5), alpha=0.7)
        dk.decorative(hl, "the hairline between the legend's quote and its entry")
        ax_, ay_, aw_, ah_ = ar["attribution"]
        first = 0.5 * vl.TYPE[NAME]["attribution"][0] * s * 1.2 / 72.0
        _summit(k, slide, ix + sym / 2.0, ay_ + first + 0.02 * s, sym)
    _run_all(ds)
    return r


@register(NAME, "data", alts=2)
def _tp_data(k, slide, f, image):
    """The number as the summit's spot height: a survey triangle on the hill's top and the number set under it, the
    contour rings round the summit; the label and the note beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    rx0, ry0, rx1, ry1 = _region(k)
    num = text_of(f, "number")
    tri = 0.42 * s
    lift = tri + 0.30 * s
    if o == "land":
        nb = (m, 0.16 * H + lift, (0.46 if alt() == 0 else 0.40) * W, 0.66 * H - lift)
        col = (nb[0] + nb[2] + 0.7 * s, 0.16 * H, W - m - nb[0] - nb[2] - 0.7 * s, 0.68 * H)
    else:
        nb = (0.10 * W, ry0 + 0.40 * s + lift, 0.80 * W, (0.30 if alt() == 0 else 0.22) * H)
        cy0 = nb[1] + nb[3] + 0.45 * s
        col = (0.09 * W, cy0, 0.82 * W, H - 0.95 * s - cy0)
    r, ds = {}, []
    t = _Terrain(k, _seed(slide, "data"), warp=0.85)
    holes = []
    if num:
        nr, nd = _v2.flow(k, slide, "data", nb, [("number", num)], anchor="middle", align="c")
        r.update(nr)
        ds.append(nd)
        z = _sizes([nd]).get("number", vl.TYPE[NAME]["number"][0] * s)
        nx, ny, nw, nh = nr["number"]
        iw = min(nw, _v2.ink_w(k, "number", num, z))
        ink_top, ink_bot = _figure_ink(ny, z)
        cx = nx + nw / 2.0
        sy = ink_top - 0.24 * s - tri * 0.4
        holes.append((cx - iw / 2.0 - 0.14 * s, ink_top - 0.14 * s, cx + iw / 2.0 + 0.14 * s, ink_bot + 0.18 * s))
        # the summit's highest contour closes round the marker AND its figure, as a spot height is written inside the
        # top ring: a ring passing under the figure read as an underline (portrait, 2026-10-22)
        b_top = sy - tri * 0.62
        hw, hh = iw / 2.0 + 0.22 * s, (ink_bot - b_top) / 2.0 + 0.20 * s
        hr = 2.6 * s
        t.plateau(cx, (b_top + ink_bot) / 2.0, 1.0, hw, hh, hr)
        top = _profile(0.07) * 0.99                 # the top ring just outside the plateau the marker and figure share
    else:
        cx, sy = nb[0] + nb[2] / 2.0, nb[1]
        hr = 2.4 * s
        t.hill(cx, sy, 1.0, hr, 2.0 * s)
        top = None
    if o == "land":
        lr, ld = _v2.flow(k, slide, "data", col, _v2.fields(f, ("label", "note")), anchor="middle")
    else:                  # the label close under its number, the map below
        lr, ld = _v2.flow(k, slide, "data", col, _v2.fields(f, ("label", "note")), anchor="top")
        room = col[1] + col[3] - max((v[1] + v[3] for v in lr.values()), default=col[1])
        if room > 0.05 * s:
            c2 = (col[0], col[1] + room * 0.22, col[2], col[3] - room * 0.22)
            lr, ld = _v2.flow(k, slide, "data", c2, _v2.fields(f, ("label", "note")), anchor="top", start=_sizes([ld]))
    r.update(lr)
    ds.append(ld)
    holes += _ink(k, lr, _texts(f), _sizes([ld]), pad=0.16 * s)
    g = 0.12 * s
    mark = (cx - tri / 2.0 - g, sy - tri * 0.62 - g, cx + tri / 2.0 + g, sy + tri * 0.38 + g)
    _fill(k, t, holes + [mark], [(cx, sy, 0.7 * hr)], n=2, h=0.45, seed=_seed(slide, "data"))
    _relief(k, slide, t, holes + [mark], top=top, n=12)
    _crosses(k, slide, holes + [mark], every=1.6)
    _summit(k, slide, cx, sy, tri)
    _run_all(ds)
    return r


@register(NAME, "closing", alts=2)
def _tp_closing(k, slide, f, image):
    """The trail reaches the top: a dashed footpath climbs the contours in switchbacks to a summit with a pennant; the
    title and its line in the lowland beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    rx0, ry0, rx1, ry1 = _region(k)
    groups = [(_v2.fields(f, ("title",)), 0.24 * s), (_v2.fields(f, ("line",)), 0.0)]
    if o == "land":
        tw = (0.50 if alt() == 0 else 0.58) * W
        r, ds = _v2.stack(k, slide, "closing", m, tw, 0.36 * H, H - 1.0 * s, groups, anchor="middle")
        texts = _texts(f)
        holes = _ink(k, r, texts, _sizes(ds), pad=0.16 * s)
        right = max([h[2] for h in holes] + [m + 0.5 * tw])
        lane = (right + 0.30 * s, rx1 - 0.30 * s)
        sx, sy = lane[0] + (lane[1] - lane[0]) * 0.55, 0.30 * H
        hr = max(1.8 * s, (rx1 - right) * 0.85)
        t = _Terrain(k, _seed(slide, "closing")).hill(sx, sy, 1.0, hr, 0.46 * H, 0.3)
    else:
        art_h = (0.40 if alt() == 0 else 0.32) * H
        r, ds = _v2.stack(k, slide, "closing", 0.09 * W, 0.62 * W, ry0 + art_h + 0.20 * s, H - 0.95 * s, groups,
                          anchor="middle")
        texts = _texts(f)
        holes = _ink(k, r, texts, _sizes(ds), pad=0.16 * s)
        right = max([h[2] for h in holes] + [0.40 * W])
        lane = (min(right + 0.30 * s, rx1 - 1.2 * s), rx1 - 0.25 * s)
        sx, sy = 0.62 * W, ry0 + art_h * 0.42
        hr = 0.44 * W
        t = _Terrain(k, _seed(slide, "closing")).hill(sx, sy, 1.0, hr, art_h * 0.70, -0.2)
    sx, sy = t.summit(sx, sy, 0.3 * s)
    fh = 0.62 * s
    flag = _box((sx - 0.08 * s, sy - fh, fh * 0.65, fh), 0.10 * s)
    start = (lane[0] + (lane[1] - lane[0]) * 0.70, ry1)
    corridor = [(start[0] + (sx - start[0]) * i / 4.0, start[1] + (sy - start[1]) * i / 4.0, 0.9 * s) for i in range(4)]
    _fill(k, t, holes + [flag], [(sx, sy, 0.7 * hr)] + corridor, n=2, h=0.45, seed=_seed(slide, "closing"))
    # the trail: from the sheet's foot up the slope in switchbacks to the summit, inside its lane, clear of the words
    words_top = min([h[1] for h in holes] + [ry1]) - 0.25 * s
    lw_ = lane[1] - lane[0]
    # a narrow lane climbs more steeply: across it at an easy grade the path folded into a spring of hairpins
    grade = 1.10 if lw_ > 2.6 * s else 0.85 if lw_ > 1.9 * s else 0.62 if lw_ > 1.4 * s else 0.40
    walk = [start] + _climb(k, t, (start[0] - 0.05 * s, ry1 - 0.35 * s), (sx, sy),
                            (lane[0], max(lane[1], sx + 0.3 * s), words_top), holes, grade=grade,
                            seed=_seed(slide, "trail"))
    _relief(k, slide, t, holes + [flag], n=14)
    _crosses(k, slide, holes + [flag], every=1.6)
    _trail(k, slide, walk, holes, dense=True)
    _flag(k, slide, sx, sy, fh)
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_topo(slide, role, index):
    """An ordinary page (a chart, an agenda) on the sheet: the neatline is the page's ground (new_slide paints it); the
    content rect inside it, in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.70, 0.62, W - 1.40, H - 1.24)


_card_topo = vl._card_for(NAME)
