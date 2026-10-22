"""circuit — the Circuit board language (电路板): its ground painter, its card and its seven pages.

A printed circuit board: the page is the board (plated mounting holes in its corners, two fiducials), copper traces
routed in buses at 45 and 90 degrees, gold pads and vias, chips with rows of gull-wing leads, white silkscreen. Every
page PLANS its words first (vl_native2.flow / stack: measured, never under a floor); the words become keep-outs, and
the traces are ROUTED round them — a trace that would cross a word, a chip or another bus stops short in a via, the
way a board drops a route to an inner layer. Then the copper is drawn, then the parts, then the words. The only words
it writes itself are the chips' designators on the points page (U1 U2 …, the manifest's derived words)."""
from __future__ import annotations

import math

import deckkit as dk
import native_art as na
import visual_languages as vl
import vl_native as vn
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "circuit"
FAR = 400.0                # "to the board's edge": a leg long enough to leave any page, clipped where it does


# ─────────────────────────────────────────── geometry ───────────────────────────────────────────
def _unit(v):
    n = math.hypot(v[0], v[1]) or 1e-9
    return (v[0] / n, v[1] / n)


def _walk(p, legs):
    """A polyline from `p` along `legs` [(direction, length)] (directions need not be unit vectors)."""
    pts = [p]
    for d, L in legs:
        if L <= 1e-6:
            continue
        ux, uy = _unit(d)
        x, y = pts[-1]
        pts.append((x + ux * L, y + uy * L))
    return pts


def _offset(pts, d):
    """The polyline offset by `d` to the LEFT of travel (normal (-dy, dx)), mitred at every joint: a bus is one centre
    line and its traces are its offsets, so the spacing holds through every 45-degree bend."""
    nrm = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        ux, uy = _unit((x1 - x0, y1 - y0))
        nrm.append((-uy, ux))
    out = []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            nx, ny = nrm[0]
        elif i == len(pts) - 1:
            nx, ny = nrm[-1]
        else:
            a, b = nrm[i - 1], nrm[i]
            dot = a[0] * b[0] + a[1] * b[1]
            nx, ny = (a[0] + b[0]) / (1.0 + dot), (a[1] + b[1]) / (1.0 + dot)
        out.append((x + d * nx, y + d * ny))
    return out


def _length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _inflate(r, d):
    return (r[0] - d, r[1] - d, r[2] + 2 * d, r[3] + 2 * d)


def _enter_t(p, q, r):
    """Where segment p→q first enters rect r, as a fraction of its length (Liang–Barsky); None when it misses."""
    x0, y0, w, h = r
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x0 + w - p[0]), (-dy, p[1] - y0), (dy, y0 + h - p[1])):
        if abs(pp) < 1e-12:
            if qq < 0:
                return None
            continue
        t = qq / pp
        if pp < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return t0


def _exit_t(p, q, W, H):
    """Where segment p→q (p on the page) leaves the page, as a fraction; None when it stays on."""
    t = 1.0
    hit = False
    for v, dv, lo, hi in ((p[0], q[0] - p[0], 0.0, W), (p[1], q[1] - p[1], 0.0, H)):
        if dv > 1e-12 and v + dv > hi:
            t, hit = min(t, (hi - v) / dv), True
        elif dv < -1e-12 and v + dv < lo:
            t, hit = min(t, (lo - v) / dv), True
    return max(0.0, t) if hit else None


def _pt_seg(px, py, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _approach_t(p, q, a, b, clr):
    """The first fraction of p→q at which it comes within `clr` of segment a–b; None when it never does. Distance
    from a point moving on a line to a segment is convex, so: find its minimum, then search back to the crossing."""
    if (max(p[0], q[0]) + clr < min(a[0], b[0]) or min(p[0], q[0]) - clr > max(a[0], b[0])
            or max(p[1], q[1]) + clr < min(a[1], b[1]) or min(p[1], q[1]) - clr > max(a[1], b[1])):
        return None
    f = lambda t: _pt_seg(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, a, b)   # noqa: E731
    if f(0.0) < clr:
        return 0.0
    lo, hi = 0.0, 1.0
    for _i in range(40):
        m1, m2 = lo + (hi - lo) / 3.0, hi - (hi - lo) / 3.0
        if f(m1) < f(m2):
            hi = m2
        else:
            lo = m1
    tm = (lo + hi) / 2.0
    if f(tm) >= clr:
        return None
    lo, hi = 0.0, tm
    for _i in range(30):
        mid = (lo + hi) / 2.0
        if f(mid) < clr:
            hi = mid
        else:
            lo = mid
    return lo


def _circle(cx, cy, r, n=20):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _rect_pts(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


_LAYERED = ("one layer of the board spread across the whole page — copper, pads, drills, leads or silkscreen — "
            "running under and round the parts and the picture's module, never across the words")


def _frame(slide, pts_lists, layer):
    """The frame a shape is drawn in: the whole page for a LAYER of the board (its copper, its gold, its drills, its
    silkscreen — one object spanning the board, as a layer does), else the extent of its own points."""
    W, H = na.page_size(slide)
    if layer:
        return 0.0, 0.0, W, H
    xs = [x for l_ in pts_lists for x, _y in l_]
    ys = [y for l_ in pts_lists for _x, y in l_]
    return min(xs), min(ys), max(max(xs) - min(xs), 0.01), max(max(ys) - min(ys), 0.01)


def _paths(slide, lines, color, w, *, alpha=None, reason, layer=True):
    """Open polylines as ONE outline shape, round ends and round joins."""
    lines = [l_ for l_ in lines if len(l_) >= 2 and _length(l_) > 1e-4]
    if not lines:
        return None
    W, H = na.page_size(slide)
    lines = [[(min(max(x, 0.0), W), min(max(y, 0.0), H)) for x, y in l_] for l_ in lines]
    x0, y0, bw, bh = _frame(slide, lines, layer)
    U = na.U
    u = lambda p: ((p[0] - x0) / bw * U, (p[1] - y0) / bh * U)          # noqa: E731
    d = "".join("<a:moveTo>{}</a:moveTo>".format(na.orn._pt(*u(l_[0])))
                + "".join("<a:lnTo>{}</a:lnTo>".format(na.orn._pt(*u(p))) for p in l_[1:]) for l_ in lines)
    sh = na._custom(slide, x0, y0, bw, bh, '<a:path w="{u}" h="{u}" fill="none">{d}</a:path>'.format(u=U, d=d),
                    line=na.hexstr(color), line_w=w)
    from pptx.oxml.ns import qn
    ln = sh._element.spPr.find(qn("a:ln"))
    if alpha is not None:
        clr = ln.find(qn("a:solidFill"))[0]
        clr.append(clr.makeelement(qn("a:alpha"), {"val": str(int(alpha * 100000))}))
    ln.find(qn("a:solidFill")).addnext(ln.makeelement(qn("a:round"), {}))
    dk.decorative(sh, reason)
    dk.overlap_intent(sh, _LAYERED if layer else "a mark moulded into a part, lying on its body by design")
    return sh


def _fill(slide, polys, color, *, alpha=None, reason, layer=True):
    """Closed polygons as ONE filled shape, each polygon cut to the page (a pad or a via never reaches past the
    board)."""
    W, H = na.page_size(slide)
    polys = [na.clip_to_page(p, W, H) for p in polys]
    polys = [p for p in polys if len(p) >= 3]
    if not polys:
        return None
    x0, y0, bw, bh = _frame(slide, polys, layer)
    U = na.U
    d = "".join(na.orn._ring([((x - x0) / bw * U, (y - y0) / bh * U) for x, y in p]) for p in polys)
    sh = na._custom(slide, x0, y0, bw, bh, '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=U, d=d),
                    fill=na.hexstr(color), alpha=alpha)
    dk.decorative(sh, reason)
    dk.overlap_intent(sh, _LAYERED if layer else "a small part soldered on the board, over its own pads by design")
    return sh


# ─────────────────────────────────────────── the board ───────────────────────────────────────────
def _holes(k):
    """The plated mounting holes at the four corners and the two fiducials beside them: (cx, cy) each."""
    W, H, s, o = ctx(k)
    c = 0.36 * s
    return [(c, c), (W - c, c), (c, H - c), (W - c, H - c)], [(W - c - 0.44 * s, c), (c + 0.44 * s, H - c)]


def _ground(k, slide):
    """Every page: the page IS the board — a plated mounting hole in each corner (gold ring, drilled centre, its
    silkscreen keep-out ring) and two fiducials (a bare gold dot in a clearing of the mask)."""
    W, H, s, o = ctx(k)
    holes, fids = _holes(k)
    _fill(slide, [_circle(x, y, 0.105 * s, 28) for x, y in fids], k.P["offboard"],
          reason="the clearing in the solder mask round each fiducial: the board's furniture")
    _fill(slide, [_circle(x, y, 0.17 * s, 36) for x, y in holes] + [_circle(x, y, 0.035 * s, 16) for x, y in fids],
          k.P["pad"], reason="the plated rings of the mounting holes and the fiducial dots: the board's furniture")
    _fill(slide, [_circle(x, y, 0.10 * s, 28) for x, y in holes], k.P["hole"],
          reason="the drilled centres of the mounting holes: the board's furniture, nothing to read")
    rings = [(_circle(x, y, 0.235 * s, 40) + [_circle(x, y, 0.235 * s, 40)[0]]) for x, y in holes]
    _paths(slide, rings, k.P["silk"], 0.6 * s, alpha=0.55,
           reason="the silkscreen keep-out ring round each mounting hole: the board's furniture")


vn.GROUNDS[NAME] = _ground


class _Board:
    """One page's copper: keep-outs (the planned words, the parts), the traces routed so far, the pads and vias. Plan
    everything, then draw() it in layers: copper, gold, drills, parts, silkscreen."""

    def __init__(self, k, slide):
        W, H, s, o = ctx(k)
        self.k, self.slide, self.W, self.H, self.s = k, slide, W, H, s
        self.pitch = 0.115 * s
        self.tw = 2.3 * s                  # a trace's width in pt
        self.clr = 0.13 * s                # a trace's centre line from a keep-out
        self.clr2 = 0.10 * s               # …from another bus's trace
        self.via_r = 0.042 * s
        self.edge = 0.40 * s               # no trace runs along the board's edge closer than this
        self.keep = []                     # (rect, owner)
        self.segs = []                     # ((a, b), bus)
        self.traces = []                   # (polyline, width factor)
        self.rails = []                    # bare gold rails (a shared bus left unmasked)
        self.vias = []
        self.gold = []                     # pad polygons
        self.leads = []
        self.parts = []                    # callables: chip bodies and small parts, drawn over the copper
        self.silk = []                     # silkscreen polylines
        self.silk_fill = []
        self.n_bus = 0
        holes, fids = _holes(k)
        for x, y in holes:
            self.keep.append(((x - 0.30 * s, y - 0.30 * s, 0.60 * s, 0.60 * s), "hole"))
        for x, y in fids:
            self.keep.append(((x - 0.14 * s, y - 0.14 * s, 0.28 * s, 0.28 * s), "hole"))

    # ── keep-outs ──
    def block(self, rect, owner="text", pad=0.0):
        self.keep.append((_inflate(rect, pad), owner))

    def free(self, rect, owner=None):
        """Is `rect` clear of every keep-out and every trace drawn so far?"""
        for r, own in self.keep:
            if own != owner and _v2.meet(rect, r):
                return False
        for (a, b), _bid in self.segs:
            if _enter_t(a, b, _inflate(rect, self.tw / 144.0 + 0.02 * self.s)) is not None:
                return False
        x, y, w, h = rect
        return x >= 0 and y >= 0 and x + w <= self.W and y + h <= self.H

    # ── routing ──
    def _clip(self, pts, owner, bus):
        """The part of the polyline that is clear: it stops at the page's edge ('edge'), or a clearance short of the
        first keep-out or other bus it meets ('via'). Returns (points, end)."""
        x0, y0 = pts[0]
        pts = [(min(max(x0, 0.0), self.W), min(max(y0, 0.0), self.H))] + list(pts[1:])
        out = [pts[0]]
        e = self.edge
        for p, q in zip(pts, pts[1:]):
            t_hit, end = None, None
            t = _exit_t(p, q, self.W, self.H)
            if t is not None:
                t_hit, end = t, "edge"
            # a run ALONG the board's edge (inside its margin) is no route: it stops where the run would begin
            if (abs(q[1] - p[1]) < 1e-9 and (p[1] < e or p[1] > self.H - e)) or \
                    (abs(q[0] - p[0]) < 1e-9 and (p[0] < e or p[0] > self.W - e)):
                t_hit, end = 0.0, "via"
            for r, own in self.keep:
                if own == owner or own.split("~")[0] == owner:
                    continue
                t = _enter_t(p, q, _inflate(r, self.clr))
                if t is not None and (t_hit is None or t < t_hit):
                    t_hit, end = t, "via"
            for (a, b), bid in self.segs:
                if bid == bus:
                    continue
                t = _approach_t(p, q, a, b, self.clr2)
                if t is not None and (t_hit is None or t < t_hit):
                    t_hit, end = t, "via"
            if t_hit is not None:
                out.append((p[0] + (q[0] - p[0]) * t_hit, p[1] + (q[1] - p[1]) * t_hit))
                return out, end
            out.append(q)
        x1, y1 = out[-1]
        at_edge = min(x1, y1, self.W - x1, self.H - y1) < 1e-3
        return out, ("edge" if at_edge else "via")

    def plan(self, lines, owner, bus, min_len):
        """[(kept points, end)] for each polyline (None for one too short to draw), nothing committed."""
        out = []
        for l_ in lines:
            kept, end = self._clip(l_, owner, bus)
            out.append((kept, end) if _length(kept) >= min_len else None)
        return out

    def commit(self, planned, bus, *, wf=1.0, vias=True, kind="trace"):
        for it in planned:
            if it is None:
                continue
            kept, end = it
            if kind == "rail":
                self.rails.append(kept)
            else:
                self.traces.append((kept, wf))
            self.segs += [((a, b), bus) for a, b in zip(kept, kept[1:])]
            vx, vy = kept[-1]
            room = self.via_r + 0.03 * self.s     # a via whose ring would leave the board is no via: the trace runs off
            if end == "via" and vias and room <= vx <= self.W - room and room <= vy <= self.H - room:
                self.vias.append(kept[-1])

    def new_bus(self):
        self.n_bus += 1
        return self.n_bus

    def route(self, lines, owner, *, bus=None, min_len=None, wf=1.0, vias=True):
        bus = bus or self.new_bus()
        p = self.plan(lines, owner, bus, self.s * 0.10 if min_len is None else min_len)
        self.commit(p, bus, wf=wf, vias=vias)
        return p

    def bus_lines(self, tips, D, legs):
        """The traces of a bus that leaves `tips` (in a row across direction D) along the centre line `legs`."""
        n = (-D[1], D[0])
        cx = sum(p[0] for p in tips) / len(tips)
        cy = sum(p[1] for p in tips) / len(tips)
        centre = _walk((cx, cy), legs)
        return [_offset(centre, (p[0] - cx) * n[0] + (p[1] - cy) * n[1]) for p in tips]

    def escape(self, tips, D, owner, *, group=5, a0=None, spread=None, turn=None, dogbones=True, order=None,
               turns=None):
        """Route a chip side's pins out: contiguous groups of `group` pins become buses that fan out (the outer
        groups jog sideways at 45 degrees, then run on to the board's edge), or — when that is blocked — turn 90
        degrees and run along; the best-routed candidate wins (a route reaching the board's edge beats one ending in
        vias). `turns` ({group index: direction}) asks a group to turn toward a direction — tried at a few heights.
        A group with nowhere to go becomes a fan-out of short stubs to staggered vias. The pin between two groups gets
        a dogbone: a short 45-degree stub to a via. Everything stops short of the words."""
        s = self.s
        D = _unit(D)
        n = (-D[1], D[0])
        tips = sorted(tips, key=lambda p: p[0] * n[0] + p[1] * n[1])
        groups, singles, i = [], [], 0
        while i < len(tips):
            g = tips[i:i + group]
            if len(g) >= 2:
                groups.append(g)
            else:
                singles += g
            i += group
            if i < len(tips):
                singles.append(tips[i])
                i += 1
        m = len(groups)
        a0 = 0.30 * s if a0 is None else a0
        spread = (group + 1) * self.pitch * 0.9 if spread is None else spread
        idx = list(range(m))
        if order == "outer":
            idx.sort(key=lambda j: -abs(j - (m - 1) / 2.0))
        for j in idx:
            g = groups[j]
            kpos = j - (m - 1) / 2.0
            sig = 0 if abs(kpos) < 0.26 else (1 if kpos > 0 else -1)
            half = (len(g) - 1) * self.pitch / 2.0
            cands = []
            want = (turns or {}).get(j)
            if want is not None:                       # this group is asked to turn toward an absolute direction:
                sg = 1 if (want[0] * n[0] + want[1] * n[1]) > 0 else -1     # the turn tried at a few heights, the
                lat = (n[0] * sg, n[1] * sg)                                # best-routed one kept
                diag = (D[0] + lat[0], D[1] + lat[1])
                r0 = a0 + half * 0.6
                for rr in (r0, r0 + 0.35 * s, r0 + 0.70 * s, r0 + 1.10 * s):
                    cands.append([(D, rr), (diag, half * 2.0 * math.sqrt(2) + 0.12 * s), (lat, FAR)])
            n_pref = max(1, len(cands))
            if sig:
                lat = (n[0] * sig, n[1] * sig)
                diag = (D[0] + lat[0], D[1] + lat[1])
                cands.append([(D, a0 + half * 0.5), (diag, abs(kpos) * spread * math.sqrt(2)), (D, FAR)])
            else:
                cands.append([(D, FAR)])
            for sg in ((sig,) if sig else (1, -1)) if turn is None else (turn,):
                lat = (n[0] * sg, n[1] * sg)
                diag = (D[0] + lat[0], D[1] + lat[1])
                reach = a0 + half * 1.2 + (abs(kpos) if sg == sig else (m - 1) / 2.0 - kpos * sg + 1) * spread * 0.8
                cands.append([(D, reach), (diag, half * 2.0 * math.sqrt(2) + 0.12 * s), (lat, FAR)])
            best, best_sc = None, -1.0
            bus = self.new_bus()
            for ci, legs in enumerate(cands):
                p = self.plan(self.bus_lines(g, D, legs), owner, bus, 0.10 * s)
                # a route that reaches the board's edge beats one that stops in vias beside the words
                sc = sum(_length(it[0]) * (1.0 if it[1] == "edge" else 0.5) for it in p if it) * (1.2 if ci < n_pref else 1.0)
                if sc > best_sc:
                    best, best_sc = p, sc
            if best_sc < len(g) * 0.45 * s:
                # nowhere to go: a fan-out — each pin a short stub to its own via, staggered as a board staggers them
                best = self.plan([_walk(t_, [(D, (0.10 + 0.13 * (q_ % 2)) * s)]) for q_, t_ in enumerate(g)],
                                 owner, bus, 0.08 * s)
                best = [(it[0], "via") if it else None for it in best]
            self.commit(best, bus)
        if dogbones:
            for t_ in singles:
                sg = 1 if (t_[0] * n[0] + t_[1] * n[1]) >= 0 else -1
                diag = (D[0] + n[0] * sg * 0.6, D[1] + n[1] * sg * 0.6)
                self.route([_walk(t_, [(D, 0.08 * s), (diag, 0.16 * s)])], owner, min_len=0.20 * s)

    # ── parts ──
    def chip(self, x, y, w, h, *, sides="tblr", owner, body="poly", inset=None, marks=True):
        """A chip whose BODY is (x, y, w, h): gull-wing leads on `sides` landing on gold pads, a pin-1 dimple, silkscreen
        corner marks and a pin-1 dot. Registers it as a keep-out; returns {side: [pad tips]} (where traces start)."""
        s = self.s
        p = self.pitch
        lead_l, lead_w = 0.075 * s, 0.040 * s
        pad_l, pad_w = 0.15 * s, 0.062 * s
        tips = {}
        for side in sides:
            L = w if side in "tb" else h
            ins = max(0.14 * s, 0.09 * L) if inset is None else inset
            cnt = int((L - 2 * ins) / p + 1e-6) + 1
            if cnt < 2:
                continue
            st = (L - (cnt - 1) * p) / 2.0
            row = []
            for i in range(cnt):
                t = st + i * p
                if side == "t":
                    bx, by, D = x + t, y, (0.0, -1.0)
                elif side == "b":
                    bx, by, D = x + t, y + h, (0.0, 1.0)
                elif side == "l":
                    bx, by, D = x, y + t, (-1.0, 0.0)
                else:
                    bx, by, D = x + w, y + t, (1.0, 0.0)
                nx, ny = -D[1], D[0]
                self.gold.append([(bx + D[0] * 0.01 * s + nx * pad_w / 2, by + D[1] * 0.01 * s + ny * pad_w / 2),
                                  (bx + D[0] * pad_l + nx * pad_w / 2, by + D[1] * pad_l + ny * pad_w / 2),
                                  (bx + D[0] * pad_l - nx * pad_w / 2, by + D[1] * pad_l - ny * pad_w / 2),
                                  (bx + D[0] * 0.01 * s - nx * pad_w / 2, by + D[1] * 0.01 * s - ny * pad_w / 2)])
                self.leads.append([(bx + nx * lead_w / 2, by + ny * lead_w / 2),
                                   (bx + D[0] * lead_l + nx * lead_w / 2, by + D[1] * lead_l + ny * lead_w / 2),
                                   (bx + D[0] * lead_l - nx * lead_w / 2, by + D[1] * lead_l - ny * lead_w / 2),
                                   (bx - nx * lead_w / 2, by - ny * lead_w / 2)])
                row.append((bx + D[0] * pad_l, by + D[1] * pad_l))
            tips[side] = row
        ex = {sd: (pad_l if sd in sides else 0.0) for sd in "tblr"}
        outer = (x - ex["l"], y - ex["t"], w + ex["l"] + ex["r"], h + ex["t"] + ex["b"])
        self.keep.append((_inflate(outer, 0.03 * s), owner))
        if marks:                                       # silkscreen: an L at each corner of the footprint, a pin-1 dot
            g = 0.09 * s
            cx0, cy0, cw, ch = _inflate(outer, g)
            arm = min(0.30 * s, 0.25 * min(cw, ch))
            for (px, py), (sx, sy) in (((cx0, cy0), (1, 1)), ((cx0 + cw, cy0), (-1, 1)),
                                       ((cx0, cy0 + ch), (1, -1)), ((cx0 + cw, cy0 + ch), (-1, -1))):
                self.silk.append([(px + sx * arm, py), (px, py), (px, py + sy * arm)])
            self.silk_fill.append(_circle(cx0 - 0.07 * s, cy0 - 0.07 * s, 0.038 * s, 14))
            self.keep.append((_inflate((cx0, cy0, cw, ch), 0.06 * s), owner + "~silk"))
        k = self.k

        def draw_body():
            if body == "poly":
                c = min(0.16 * s, 0.12 * min(w, h))            # the chamfered pin-1 corner of a QFP
                sh = na.poly(self.slide, [(x + c, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y + c)],
                             fill=k.P["chip"])
                dk.decorative(sh, "a chip's moulded body: the board's picture, nothing to read on it")
                na.soft_shadow(sh, blur=0.05, dist=0.025, alpha=0.35, color="000000")
                i_ = 0.07 * s
                top = na.poly(self.slide, [(x + i_ + c * 0.7, y + i_), (x + w - i_, y + i_), (x + w - i_, y + h - i_),
                                           (x + i_, y + h - i_), (x + i_, y + i_ + c * 0.7)], fill=k.P["chip_top"])
                dk.decorative(top, "the flat top face of the chip's body, a shade lighter than its bevel")
                er = min(0.14 * s, 0.07 * min(w, h))             # the mould's ejector-pin mark, opposite pin 1
                ring = _circle(x + w - 2.2 * er, y + h - 2.2 * er, er, 32)
                _paths(self.slide, [ring + ring[:1]], k.P["chip_edge"], 0.9 * s, layer=False,
                       reason="the ejector-pin mark moulded into the chip's body; ornament, nothing to read")
            else:
                sh = dk.box(self.slide, x, y, w, h, fill=dk._as_rgb(k.P["chip"]), line=dk._as_rgb(k.P["chip_edge"]),
                            line_w=1.0)
                dk.decorative(sh, "the chip's body is the ground its words sit on; the words carry the meaning")
                na.soft_shadow(sh, blur=0.05, dist=0.025, alpha=0.35, color="000000")
            dimple = min(0.085 * s, 0.10 * min(w, h))
            off = 0.13 * s if body == "poly" else 0.10 * s
            _fill(self.slide, [_circle(x + off + dimple / 2, y + off + dimple / 2, dimple / 2, 18)], k.P["chip_edge"], layer=False,
                  reason="the pin-1 dimple moulded into the chip's body; ornament, nothing to read")
        self.parts.append(draw_body)
        return tips

    def smd(self, cx, cy, horizontal, kind, owner="part"):
        """A small two-terminal part (an 0603 resistor or capacitor): two gold pads, its body between them."""
        s = self.s
        L, Wd = 0.24 * s, 0.11 * s
        w, h = (L, Wd) if horizontal else (Wd, L)
        r = (cx - w / 2, cy - h / 2, w, h)
        if not self.free(_inflate(r, 0.04 * s)):
            return False
        self.keep.append((_inflate(r, 0.04 * s), owner))
        e = 0.07 * s
        if horizontal:
            self.gold += [_rect_pts(r[0], r[1], e, h), _rect_pts(r[0] + w - e, r[1], e, h)]
            bodyr = (r[0] + e * 0.8, r[1] + 0.012 * s, w - 1.6 * e, h - 0.024 * s)
        else:
            self.gold += [_rect_pts(r[0], r[1], w, e), _rect_pts(r[0], r[1] + h - e, w, e)]
            bodyr = (r[0] + 0.012 * s, r[1] + e * 0.8, w - 0.024 * s, h - 1.6 * e)
        col = self.k.P["part_a"] if kind == "c" else self.k.P["part_b"]
        self.parts.append(lambda: _fill(self.slide, [_rect_pts(*bodyr)], col, layer=False,
                                        reason="the body of a small resistor or capacitor on the board; ornament"))
        return True

    def draw(self):
        k, sl, s = self.k, self.slide, self.s
        for wf in sorted({wf for _l, wf in self.traces}):
            lines = [l_ for l_, f_ in self.traces if f_ == wf]
            _paths(sl, lines, k.P["trace"], self.tw * wf,
                   reason="copper traces routed round the words: the board's wiring, nothing to read in it")
            _paths(sl, lines, k.P["trace_hi"], self.tw * wf * 0.32, alpha=0.75,
                   reason="the light catching the top of each copper trace; ornament, nothing to read")
        if self.rails:
            _paths(sl, self.rails, k.P["pad_dark"], self.tw * 3.0,
                   reason="the shared bus: a heavy rail of bare copper every chip taps; ornament, nothing to read")
            _paths(sl, self.rails, k.P["pad"], self.tw * 1.9,
                   reason="the lit face of the shared bus's bare copper rail; ornament, nothing to read")
        _fill(sl, self.gold + [_circle(x, y, self.via_r, 14) for x, y in self.vias], k.P["pad"],
              reason="gold pads and vias: where parts are soldered and traces change layer")
        _fill(sl, [_circle(x, y, self.via_r * 0.45, 10) for x, y in self.vias], k.P["hole"],
              reason="the drilled centres of the vias; ornament, nothing to read")
        _fill(sl, self.leads, k.P["lead"], reason="the chips' tinned gull-wing leads, soldered to their pads")
        for d in self.parts:
            d()
        _paths(sl, self.silk, k.P["silk"], 1.1 * s,
               reason="silkscreen corner marks round each chip's footprint: the board's printing, nothing to read")
        _fill(sl, self.silk_fill, k.P["silk"], reason="the silkscreen pin-1 dot beside each chip")


# ─────────────────────────────────────────── shared page parts ───────────────────────────────────────────
def _m(k):
    W, H, s, o = ctx(k)
    return (0.74 if o == "land" else 0.64) * s


def _sizes(draws):
    out = {}
    for d in draws:
        out.update(getattr(d, "sizes", {}) or {})
    return out


def _ink(k, field, text, rect, size, align="l"):
    """The rect the words take: the planned box cut to its longest line (measured), kept at the box's side."""
    x, y, w, h = rect
    try:
        lines = []
        for part in str(text).split("\n"):
            lines += vl._break_lines(k, field, part, size, w * vl.HEADROOM) or [part]
        iw = min(w, max(_v2.ink_w(k, field, l_, size) for l_ in lines) * 1.04 + 0.08)
    except Exception:
        return rect
    if align == "c":
        return (x + (w - iw) / 2.0, y, iw, h)
    if align == "r":
        return (x + w - iw, y, iw, h)
    return (x, y, iw, h)


def _block_words(B, k, f, rects, draws, align="l", fields=None, pad=0.20):
    """Make the planned words keep-outs, each cut to its measured lines."""
    sz = _sizes(draws)
    for fld, r in rects.items():
        t = (fields or {}).get(fld) or text_of(f, fld)
        if fld == "kicker" and t:
            t = _v2.caps(t)
        rr = _ink(k, fld, t, r, sz[fld], align) if (t and fld in sz) else r
        B.block(rr, "text", pad * B.s)


def _tall(k):
    W, H, s, o = ctx(k)
    return o == "port" and H >= 1.25 * W


def _low(plan, y0, y1):
    """Words set LOW in [y0, y1] — planned at the top, then moved down to end at y1 — on a tall portrait board, where
    the part above sends its buses down to them (centred, they left the board's lower half bare). `plan(y)` plans
    the words from y down to y1, anchored at the top, and returns (rects, draws)."""
    r, ds = plan(y0)
    if not r:
        return r, ds
    shift = y1 - max(v[1] + v[3] for v in r.values()) - 0.02
    if shift > 0.05:
        r, ds = plan(y0 + shift)
    return r, ds


def _parts_near(B, spots):
    """Small parts at the first free spots of a list [(x, y, horizontal, kind)] — decoupling capacitors and resistors
    near a chip, placed after the routing where they find room."""
    for x, y, hz, kind in spots:
        B.smd(x, y, hz, kind)


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=2)
def _cc_cover(k, slide, f, image):
    """A board's heart: the title (and kicker, subtitle) at the left; a large chip beside it with every bus on the
    board converging on it from the edges; small parts round it (on a portrait or square page the chip is above the
    words)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    B = _Board(k, slide)
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.14 * s), (_v2.fields(f, ("title",)), 0.22 * s),
              (_v2.fields(f, ("subtitle",)), 0.0)]
    pad_out = 0.15 * s
    if o == "land":
        cs = min(0.40 * H, 0.25 * W) if alt() == 0 else min(0.32 * H, 0.20 * W)
        cx, cy = W - m - 0.55 * s - cs / 2.0, H / 2.0
        tx = m + 0.15 * s
        tw = cx - cs / 2.0 - pad_out - 0.95 * s - tx
        r, ds = _v2.stack(k, slide, "cover", tx, tw, m + 0.2 * s, H - m - 0.2 * s, groups, anchor="middle")
        align = "l"
    else:
        cs = min(0.40 * W, 0.24 * H) if alt() == 0 else min(0.30 * W, 0.16 * H)
        cx = W / 2.0
        cy = max(m + 0.60 * s + pad_out + cs / 2.0, 0.24 * H)
        y0 = cy + cs / 2.0 + pad_out + 0.65 * s
        if _tall(k):
            r, ds = _low(lambda y: _v2.stack(k, slide, "cover", 0.10 * W, 0.80 * W, y, H - m, groups, anchor="top"),
                         y0, H - m)
        else:
            r, ds = _v2.stack(k, slide, "cover", 0.10 * W, 0.80 * W, y0, H - m, groups, anchor="middle")
        align = "l"
    _block_words(B, k, f, r, ds, align)
    x0, y0 = cx - cs / 2.0, cy - cs / 2.0
    tips = B.chip(x0, y0, cs, cs, sides="tblr", owner="core")
    for side, D in (("t", (0, -1)), ("b", (0, 1)), ("r", (1, 0)), ("l", (-1, 0))):
        B.escape(tips[side], D, "core", group=5 if cs > 1.6 * s else 4, order="outer")
    e = cs / 2.0 + pad_out + 0.32 * s
    _parts_near(B, [(cx + e, cy - e, True, "c"), (cx - e, cy + e, True, "c"), (cx + e, cy + e, False, "r"),
                    (cx - e, cy - e, False, "r")])
    B.draw()
    _run_all(ds)
    return r


def _number_chip(k, slide, page, B, box, num, sides, owner, *, start=None):
    """PLAN the number on a chip: the number measured in `box` (less the pads round it), the chip's body cut to the
    number. Returns (rects, draw, body rect, tips); draw() sets the number (the chip is drawn with the board)."""
    W, H, s, o = ctx(k)
    x, y, w, h = box
    pad_l = 0.15 * s + 0.06 * s
    padx, pady = 0.42 * s, 0.22 * s
    ix = x + (pad_l if "l" in sides else 0.0) + padx
    iy = y + (pad_l if "t" in sides else 0.0) + pady
    iw = w - (pad_l if "l" in sides else 0.0) - (pad_l if "r" in sides else 0.0) - 2 * padx
    ih = h - (pad_l if "t" in sides else 0.0) - (pad_l if "b" in sides else 0.0) - 2 * pady
    kw = {"anchor": "middle", "align": "c", "ink": k.P["chip_ink"]}
    if start:
        kw["start"] = start
    nr, nd = _v2.flow(k, slide, page, (ix, iy, iw, ih), [("number", num)], **kw)
    size = getattr(nd, "sizes", {}).get("number", vl.TYPE[NAME]["number"][0] * s)
    inkw = min(iw, _v2.ink_w(k, "number", num, size))
    nx, ny, nw, nh = nr["number"]
    pad_b = pady + 0.06 * size / 72.0
    bw = inkw + 2 * padx
    bh = nh + pady + pad_b
    if "l" in sides and "r" in sides:
        bw = min(max(bw, bh * 0.92), iw + 2 * padx)          # a QFP is near square, inside its box
    bx = nx + nw / 2.0 - bw / 2.0
    by = ny - pady
    tips = B.chip(bx, by, bw, bh, sides=sides, owner=owner, body="box")
    return nr, nd, (bx, by, bw, bh), tips


@register(NAME, "section", alts=2)
def _cc_section(k, slide, f, image):
    """A part of the board: the section number on a chip (leads along its top and its foot, buses running off to the
    board's edges); the kicker and the title beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    B = _Board(k, slide)
    num = text_of(f, "number")
    if o == "land":
        box = (m + 0.15 * s, 0.20 * H, (0.34 if alt() == 0 else 0.28) * W, 0.60 * H)
        col = (box[0] + box[2] + 0.75 * s, 0.16 * H, W - m - box[0] - box[2] - 0.75 * s - 0.1 * s, 0.68 * H)
        align = "l"
    else:
        box = (0.20 * W, m + 0.45 * s, 0.60 * W, (0.30 if alt() == 0 else 0.22) * H)
        col = (0.10 * W, box[1] + box[3] + 0.55 * s, 0.80 * W, H - m - box[1] - box[3] - 0.55 * s)
        align = "c"
    r, ds = {}, []
    tips = None
    if num:
        nr, nd, body, tips = _number_chip(k, slide, "section", B, box, num, "tb", "num",
                                          start={"number": (120 if alt() == 0 else 96) * s})
        r.update(nr)
        ds.append(nd)
    sgroups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.15 * s), (_v2.fields(f, ("title",)), 0.0)]
    if _tall(k):
        tr, tds = _low(lambda y: _v2.stack(k, slide, "section", col[0], col[2], y, col[1] + col[3], sgroups,
                                           anchor="top", align=align), col[1], col[1] + col[3])
    else:
        tr, tds = _v2.stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3], sgroups, anchor="middle",
                            align=align)
    r.update(tr)
    ds += tds
    _block_words(B, k, f, tr, tds, align)
    if tips:
        B.escape(tips["t"], (0, -1), "num", group=5, order="outer")
        B.escape(tips["b"], (0, 1), "num", group=5, order="outer")
        bx, by, bw, bh = body
        e = 0.48 * s
        _parts_near(B, [(bx - e, by + bh / 2.0, False, "c"), (bx + bw + e, by + bh / 2.0, False, "c"),
                        (bx - e, by + bh / 2.0 + 0.45 * s, False, "r")])
    B.draw()
    _run_all(ds)
    return r


def _header(B, mod, side, frac0, count, *, straddle=True):
    """A row of `count` gold header pads on one edge of the module (`frac0` along it), straddling the edge (or just
    outside it). Returns (pad tips, outward direction)."""
    s = B.s
    x, y, w, h = mod
    pad_w, pad_l = 0.07 * s, 0.20 * s
    L = w if side in "tb" else h
    count = max(2, min(count, int((L - 0.5 * s) / B.pitch) + 1))
    span = (count - 1) * B.pitch
    st = max(0.25 * s, min(L - 0.25 * s - span, frac0 * L))
    D = {"t": (0.0, -1.0), "b": (0.0, 1.0), "l": (-1.0, 0.0), "r": (1.0, 0.0)}[side]
    nx, ny = -D[1], D[0]
    a = -0.05 * s if straddle else 0.03 * s
    b = a + pad_l
    tips = []
    for i in range(count):
        t = st + i * B.pitch
        px, py = {"t": (x + t, y), "b": (x + t, y + h), "l": (x, y + t), "r": (x + w, y + t)}[side]
        B.gold.append([(px + D[0] * a + nx * pad_w / 2, py + D[1] * a + ny * pad_w / 2),
                       (px + D[0] * b + nx * pad_w / 2, py + D[1] * b + ny * pad_w / 2),
                       (px + D[0] * b - nx * pad_w / 2, py + D[1] * b - ny * pad_w / 2),
                       (px + D[0] * a - nx * pad_w / 2, py + D[1] * a - ny * pad_w / 2)])
        tips.append((px + D[0] * b, py + D[1] * b))
    return tips, D


@register(NAME, "image_text", alts=3)
def _cc_image_text(k, slide, f, image):
    """The caller's picture as a display module soldered to the board: a dark bezel round it, the caption printed on
    the module's chin, rows of gold header pads on its edges with traces leading to them; the kicker, title and body
    beside it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    B = _Board(k, slide)
    cap = text_of(f, "caption")
    bz = 0.11 * s
    if o == "land":
        share = (0.42, 0.36, 0.30) if W >= 1.6 * H else (0.36, 0.31, 0.26)    # 4:3 leaves the words more room
        img = (m + 0.55 * s, 0.22 * H, share[alt()] * W, (0.50 if cap else 0.56) * H)
    else:
        img = (0.10 * W + 0.30 * s, m + 0.62 * s, 0.80 * W - 0.6 * s, (0.30, 0.24, 0.18)[alt()] * H)
    r, ds = {}, []
    chin = bz
    if cap:
        cr, cd = _v2.flow(k, slide, "image_text", (img[0], img[1] + img[3] + 0.12 * s, img[2], 1.1 * s),
                          [("caption", cap)], ink=k.P["chip_ink"], mute=k.P["chip_mute"])
        r.update(cr)
        ds.append(cd)
        chin = max(v[1] + v[3] for v in cr.values()) - (img[1] + img[3]) + 0.10 * s
    mod = (img[0] - bz, img[1] - bz, img[2] + 2 * bz, img[3] + bz + chin)
    foot = mod[1] + mod[3]
    if o == "land":
        col = (mod[0] + mod[2] + 0.8 * s, 0.14 * H, W - m - mod[0] - mod[2] - 0.8 * s, 0.72 * H)
    else:
        col = (0.10 * W, foot + 0.55 * s, 0.80 * W, H - m - foot - 0.55 * s)
    igroups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
               (_v2.fields(f, ("body",)), 0.0)]
    if _tall(k):
        tr, tds = _low(lambda y: _v2.stack(k, slide, "image_text", col[0], col[2], y, col[1] + col[3], igroups,
                                           anchor="top"), col[1], col[1] + col[3])
    else:
        tr, tds = _v2.stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3], igroups,
                            anchor="middle")
    r.update(tr)
    _block_words(B, k, f, tr, tds)
    B.block(mod, "module", 0.02 * s)
    # (side, where along it, pads, straddling the edge, groups asked to turn toward a direction)
    heads = ((("t", 0.10, 11, True, {1: (1, 0)}), ("l", 0.12, 7, True, None), ("b", 0.55, 11, False, {0: (1, 0)}))
             if o == "land" else
             (("t", 0.18, 11, True, None), ("l", 0.20, 7, True, None), ("r", 0.45, 7, True, None),
              ("b", 0.40, 11, False, None)))
    for side, fr, cnt, st, turns in heads:
        tips, D = _header(B, mod, side, fr, cnt, straddle=st)
        B.escape(tips, D, "module", group=5, a0=0.20 * s, order="outer", turns=turns)

    def bezel():
        sh = dk.box(slide, *mod, fill=dk._as_rgb(k.P["bezel"]), line=dk._as_rgb(k.P["chip_edge"]), line_w=0.8)
        dk.decorative(sh, "the display module's bezel round the picture; the picture carries the meaning")
        dk.overlap_intent(sh, "the module's bezel lies under the picture and its credit, and under its header pads")
        na.soft_shadow(sh, blur=0.08, dist=0.04, alpha=0.40, color="000000")
    B.parts.insert(0, bezel)
    B.draw()
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(tds + ds)
    return r


def _designators(k, f, n, texts):
    return ["U{}".format(i + 1) for i in range(n)]


@register(NAME, "points", alts=4)
def _cc_points(k, slide, f, image):
    """Chips on one bus: each point a chip (its head and its line printed on the body), its designator U1 U2 …
    silkscreened above its pin-1 corner, every chip tapping ONE shared gold bus with three of its leads — the bus
    under the row on a landscape page, beside a column of chips on a portrait or square page, between two columns
    when the copy is long."""
    W, H, s, o = ctx(k)
    m = _m(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    B = _Board(k, slide)
    x0, w0 = m + 0.1 * s, W - 2 * m - 0.2 * s
    r, ds = _v2.stack(k, slide, "points", x0, w0, m, m + (0.24 if alt() in (0, 2) else 0.30) * H,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.08 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", start=None if alt() in (0, 2) else {"title": 30 * s})
    _block_words(B, k, f, r, ds)
    top = max((v[1] + v[3] for v in r.values()), default=m) + 0.32 * s
    nos = _designators(k, f, n, None)
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    ink = {"ink": k.P["chip_ink"], "mute": k.P["chip_mute"], "accent": k.P["chip_ink"]}
    padx, pady = 0.26 * s, 0.22 * s
    pad_l = 0.15 * s
    des_h = 0.26 * s
    silk = 0.09 * s + 0.03 * s                    # the silkscreen corner marks outside the pads
    row = o == "land" and alt() < 2
    if row:
        gap = 0.55 * s
        cw = (w0 - (n - 1) * gap) / n
        if cw < 2.2 * s:                          # four chips on a 4:3 page: their words would stand in a column
            raise vl.VLTextOverflow("circuit.points(): {} chips in a row are {:.2f}in wide — trying the columns".format(
                n, cw))
        head = des_h + 0.04 * s + silk + pad_l
        tail = pad_l + 0.55 * s + 0.12 * s + 3 * B.pitch    # pads under the body, the taps, the bus and its lines
        room = H - m - tail - head - top
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - 2 * padx, max(0.3, room - 2 * pady)), it,
                                                       dict(anchor="top", **ink)) for it in items])
        need = max(max((v[1] + v[3] for v in pr.values()), default=0.0) for pr, _d in probe) + 2 * pady
        if need > room + 1e-6:
            raise vl.VLTextOverflow("circuit.points(): the chips need {:.2f}in, the page has {:.2f}in".format(need, room))
        bh = max(need, min(room, 0.30 * H))       # a chip with presence when the page has the room
        y_top = top + max(0.0, (H - m - top - head - bh - tail) * 0.45)
        body_top = y_top + head
        sizes = _sizes([d for _p, d in probe])
        planned = _v2.plan_together(k, slide, "points", [((x0 + i * (cw + gap) + padx, body_top + pady, cw - 2 * padx,
                                                          bh - 2 * pady), it, dict(anchor="middle", start=sizes, **ink))
                                                         for i, it in enumerate(items)])
        bodies = [(x0 + i * (cw + gap), body_top, cw, bh) for i in range(n)]
        sides = "tb"
        bus_y = body_top + bh + pad_l + 0.55 * s
    else:
        cols = 2 if (alt() >= 2 and n >= 3) else 1
        lane = 0.85 * s
        if cols == 1:
            fws = [(x0 + lane, w0 - lane)]
            bus_x = x0 + 0.22 * s
        else:
            fw = (w0 - lane) / 2.0
            fws = [(x0, fw), (x0 + fw + lane, fw)]
            bus_x = x0 + fw + lane / 2.0
        cw = fws[0][1] - 2 * pad_l
        # the chips go down the columns — the first column takes the extra one — and each column is centred on the
        # same middle: three points read as two chips facing one across the bus, never a grid with a hole in it
        per = [list(range(-(-n // cols)))] if cols == 1 else [list(range(-(-n // 2))), list(range(-(-n // 2), n))]
        rows = len(per[0])
        gap = 0.12 * s
        pady = 0.17 * s
        head = 0.24 * s + 0.04 * s + silk
        room_h = (H - m - top - rows * head - (rows - 1) * gap) / rows
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - 2 * padx, max(0.3, room_h - 2 * pady)), it,
                                                       dict(anchor="top", **ink)) for it in items])
        hs = [max((v[1] + v[3] for v in pr.values()), default=0.0) + 2 * pady for pr, _d in probe]
        if max(hs) > room_h + 1e-6:
            raise vl.VLTextOverflow("circuit.points(): a chip needs {:.2f}in, a row has {:.2f}in".format(
                max(hs), room_h))
        ch = max(max(hs), min(room_h, (1.45 if _tall(k) else 1.10) * s))          # one height for every chip
        blocks = [len(c_) * (head + ch) + (len(c_) - 1) * gap for c_ in per]
        mid = top + max(blocks) / 2.0 + max(0.0, (H - m - top - max(blocks)) * 0.45)
        bodies = [None] * n
        for c, idx in enumerate(per):
            y = mid - blocks[c] / 2.0
            for i in idx:
                y += head
                bodies[i] = (fws[c][0] + pad_l, y, cw, ch)
                y += ch + gap
        sizes = _sizes([d for _p, d in probe])
        planned = _v2.plan_together(k, slide, "points", [((bx + padx, by + pady, bw - 2 * padx, bh - 2 * pady), it,
                                                          dict(anchor="middle", start=sizes, **ink))
                                                         for (bx, by, bw, bh), it in zip(bodies, items)])
        sides = "lr"
    # the designators: U1 … silkscreened above each chip's pin-1 corner, clear of its corner marks
    des = []
    for i, (bx, by, bw, bh) in enumerate(bodies):
        fx = bx - (pad_l if sides == "lr" else 0.0) - 0.09 * s
        fy = by - (pad_l if sides == "tb" else 0.0) - 0.09 * s
        dr, dd = _v2.flow(k, slide, "points", (fx + 0.04 * s, fy - 0.04 * s - des_h, min(bw, 1.2 * s), des_h),
                          [("item_no", nos[i])], anchor="top")
        r.update(dr)
        des.append(dd)
        B.block(_ink(k, "item_no", nos[i], dr["item_no"], _sizes([dd]).get("item_no", 13 * s)), "text", 0.04 * s)
    tips = [B.chip(bx, by, bw, bh, sides=sides, owner="u{}".format(i), body="box", inset=0.20 * s)
            for i, (bx, by, bw, bh) in enumerate(bodies)]
    # ONE shared bus — a heavy gold rail from edge to edge — and every chip tapping it with three of its leads
    bus = B.new_bus()
    if row:
        rail = [(0.0, bus_y), (W, bus_y)]
    else:
        y_lo = min(b_[1] for b_ in bodies) - 0.10 * s
        rail = [(bus_x, y_lo), (bus_x, H)]
    B.commit([it for it in B.plan([rail], "bus", bus, 0.5 * s) if it], bus, kind="rail")
    # the bus's other lines run beside the rail, on its far side from the chips, so no tap crosses them
    if row or cols == 1:
        off = [(0.0, (j + 1) * B.pitch) if row else (-(j + 1) * B.pitch, 0.0) for j in range(3)]
        B.route([[(a + dx, b + dy) for a, b in rail] for dx, dy in off], "bus", bus=bus, min_len=0.5 * s)
    for i, ((bx, by, bw, bh), t) in enumerate(zip(bodies, tips)):
        own = "u{}".format(i)
        if row:
            side, out = "b", "t"
        else:
            side = "l" if bus_x < bx else "r"
            out = "r" if side == "l" else "l"
        pins = t.get(side, [])
        mid = len(pins) // 2
        for (px, py) in pins[max(0, mid - 1):mid + 2]:
            end = (px, bus_y) if row else (bus_x, py)
            B.commit([([(px, py), end], "tap")], bus)
        # the far side: a few dogbones to vias
        far = t.get(out, [])
        Do = {"t": (0.0, -1.0), "b": (0.0, 1.0), "l": (-1.0, 0.0), "r": (1.0, 0.0)}[out]
        picks = far[-5::3] if row else far[1::4]
        for (px, py) in picks:
            lat = (1.0, 0.0) if Do[0] == 0 else (0.0, 1.0)
            B.route([_walk((px, py), [(Do, 0.06 * s), ((Do[0] + lat[0], Do[1] + lat[1]), 0.15 * s)])], own,
                    min_len=0.17 * s)
    # a decoupling capacitor beside each chip, as every chip on a board has one
    if row:
        _parts_near(B, [(bx + bw + 0.275 * s, by + 0.35 * s, False, "c") for bx, by, bw, bh in bodies[:-1]])
    B.draw()
    for pr, _d in planned:
        r.update(pr)
    _run_all([d for _p, d in planned] + des + ds)
    return r


@register(NAME, "quote", alts=2)
def _cc_quote(k, slide, f, image):
    """The quote inside a silkscreen keep-out — a fine outline, heavy corner marks, an orientation triangle — and two
    buses that cross the board and PART round it, one over the words and one under, jogging at 45 degrees."""
    W, H, s, o = ctx(k)
    m = _m(k)
    B = _Board(k, slide)
    padq = 0.42 * s
    nb = 4
    bw = (nb - 1) * B.pitch
    g = 0.34 * s + bw / 2.0                      # a bus's centre line from the area
    aw = ((0.62 if alt() == 0 else 0.76) if o == "land" else (0.80 if alt() == 0 else 0.86)) * W
    ax = (W - aw) / 2.0
    y0, y1 = m + 0.20 * s + g, H - m - 0.20 * s - g
    groups = [(_v2.fields(f, ("mark", "quote")), 0.30 * s), (_v2.fields(f, ("attribution",)), 0.0)]
    r, ds = _v2.stack(k, slide, "quote", ax + padq, aw - 2 * padq, y0 + padq, y1 - padq, groups, anchor="middle")
    # the outline hugs the words: re-planned at the measured width when they are narrower than the column
    sz = _sizes(ds)
    iw = max(_ink(k, f_, text_of(f, f_), v, sz.get(f_, 12 * s))[2] for f_, v in r.items() if text_of(f, f_))
    if iw < aw - 2 * padq - 0.4 * s:
        w2 = iw + 0.30 * s
        r2, ds2 = _v2.stack(k, slide, "quote", (W - w2) / 2.0, w2, y0 + padq, y1 - padq, groups, anchor="middle")
        hgt = lambda rr: max(v[1] + v[3] for v in rr.values()) - min(v[1] for v in rr.values())   # noqa: E731
        if hgt(r2) <= hgt(r) + 0.02 * s:
            r, ds, aw = r2, ds2, w2 + 2 * padq
            ax = (W - aw) / 2.0
    top = min(v[1] for v in r.values()) - padq
    bot = max(v[1] + v[3] for v in r.values()) + padq
    x, y, w, h = ax, top, aw, bot - top
    B.block((x, y, w, h), "area", 0.06 * s)
    B.silk.append(_rect_pts(x, y, w, h) + [(x, y)])
    arm = min(0.45 * s, 0.2 * min(w, h))
    heavy = [[(px + sx * arm, py), (px, py), (px, py + sy * arm)]
             for (px, py), (sx, sy) in (((x, y), (1, 1)), ((x + w, y), (-1, 1)), ((x, y + h), (1, -1)),
                                        ((x + w, y + h), (-1, -1)))]
    B.silk_fill.append([(x - 0.10 * s, y - 0.10 * s), (x + 0.12 * s, y - 0.10 * s), (x - 0.10 * s, y + 0.12 * s)])
    # the two buses: in from the left edge level with the words, jogging over (under) the area, out at the right
    side = x - g - 0.30 * s                       # the room beside the area for a jog
    jog = max(0.0, min(0.30 * h + g, side))
    if jog < 0.30 * s:
        jog = 0.0
    while jog and (h + 2 * g - 2 * jog) < bw + 0.40 * s:
        jog = max(0.0, jog - 0.1 * s)
    yt, yb = y - g, y + h + g
    ring = bw + 0.42 * s                          # one more bus, outside the last, where the board has the room
    for yl, sg in ((yt, 1), (yb, -1)):
        ye = yl + sg * jog
        centre = [(0.0, ye), (x - g - jog, ye), (x - g, yl), (x + w + g, yl), (x + w + g + jog, ye), (W, ye)]
        centre = [p_ for i_, p_ in enumerate(centre) if i_ == 0 or math.hypot(p_[0] - centre[i_ - 1][0],
                                                                                p_[1] - centre[i_ - 1][1]) > 1e-6]
        room = (yl - bw / 2.0) if sg > 0 else (H - yl - bw / 2.0)
        rings = 1 + max(0, min(2, int((room - 0.55 * s - m) / ring)))
        for j in range(rings):                    # the centre line runs left to right: its left is DOWN the page
            out = -sg * j * ring
            B.route([_offset(centre, out + (i - (nb - 1) / 2.0) * B.pitch) for i in range(nb)], "quote",
                    min_len=0.3 * s)
    B.draw()
    _paths(slide, heavy, k.P["silk"], 2.2 * s,
           reason="the heavy corner marks of the silkscreen keep-out round the quote")
    _run_all(ds)
    return r


@register(NAME, "data", alts=3)
def _cc_data(k, slide, f, image):
    """The number printed on a large chip with leads on all four sides, buses fanning out from it to the board's
    edges; the label and the note beside it (under it on a portrait or square page). A figure too wide for any chip
    (1,250,000) is set at the head of the column instead, the chip kept blank beside it."""
    W, H, s, o = ctx(k)
    m = _m(k)
    B = _Board(k, slide)
    num = text_of(f, "number")
    on_chip = alt() < 2
    if o == "land":
        box = (m + 0.25 * s, 0.17 * H, (0.44 if alt() == 0 else 0.36 if alt() == 1 else 0.28) * W, 0.66 * H)
        col = (box[0] + box[2] + 0.8 * s, 0.16 * H, W - m - box[0] - box[2] - 0.8 * s - 0.1 * s, 0.68 * H)
    else:
        box = (0.12 * W, m + 0.40 * s, 0.76 * W, (0.36 if alt() == 0 else 0.28 if alt() == 1 else 0.22) * H)
        col = (0.10 * W, box[1] + box[3] + 0.5 * s, 0.80 * W, H - m - box[1] - box[3] - 0.5 * s)
    r, ds = {}, []
    if num and on_chip:
        nr, nd, body, tips = _number_chip(k, slide, "data", B, box, num, "tblr", "num")
        r.update(nr)
        ds.append(nd)
    else:
        side = max(0.8 * s, min(box[2], box[3]) - 0.6 * s)
        bx, by = box[0] + (box[2] - side) / 2.0, box[1] + (box[3] - side) / 2.0
        body = (bx, by, side, side)
        tips = B.chip(bx, by, side, side, sides="tblr", owner="num")
    dfields = _v2.fields(f, ("label", "note") if on_chip else ("number", "label", "note"))
    if _tall(k):
        tr, td = _low(lambda y: _v2.flow(k, slide, "data", (col[0], y, col[2], col[1] + col[3] - y), dfields,
                                         anchor="top"), col[1], col[1] + col[3])
    else:
        tr, td = _v2.flow(k, slide, "data", col, dfields, anchor="middle")
    r.update(tr)
    ds.append(td)
    _block_words(B, k, f, tr, [td])
    for side, D in (("t", (0, -1)), ("b", (0, 1)), ("l", (-1, 0)), ("r", (1, 0))):
        if side in tips:
            B.escape(tips[side], D, "num", group=5, order="outer")
    bx, by, bw, bh = body
    e = 0.45 * s
    _parts_near(B, [(bx + bw + e, by - e, True, "c"), (bx - e, by + bh + e, True, "c"), (bx - e, by - e, False, "r")])
    B.draw()
    _run_all(ds)
    return r


@register(NAME, "closing", alts=2)
def _cc_closing(k, slide, f, image):
    """The board's edge connector: gold fingers along the foot of the page, a key notch between them. The traces from
    the fingers rise, part left and right under the words and — in the designed layout — climb the board's sides
    to its top, holding the title and its line between them; the roomier layout lets them run out to the sides."""
    W, H, s, o = ctx(k)
    m = _m(k)
    B = _Board(k, slide)
    land = o == "land"
    pitch = (0.15 if land else 0.13) * s
    B.pitch = pitch
    nf = 8 if land else 5                                       # fingers on each side of the key
    fh, key = 0.52 * s, 0.22 * s
    fw = 0.62 * pitch
    bw = (nf - 1) * pitch                                       # one bus's width
    corner = 0.5 * bw + 0.24 * s                                # a 90-degree corner's diagonal, long enough that the
    rise = 0.22 * s + 0.42 * bw                                 # inner trace keeps a leg of its own
    yf = H - fh
    y_run = yf - rise - corner / math.sqrt(2)
    wrap = alt() == 0
    if wrap:
        side_x = max(m + bw / 2.0 + 0.22 * s, (W - (0.60 * W)) / 2.0 - bw / 2.0 - 0.42 * s)
        tx = side_x + bw / 2.0 + 0.42 * s
    else:
        tx = 0.10 * W
    tw_ = W - 2 * tx
    r, ds = _v2.stack(k, slide, "closing", tx, tw_, m + 0.2 * s, y_run - bw / 2.0 - 0.40 * s,
                      [(_v2.fields(f, ("title",)), 0.22 * s), (_v2.fields(f, ("line",)), 0.0)], anchor="middle",
                      align="c")
    _block_words(B, k, f, r, ds, "c")
    fingers = []
    for sg in (-1, 1):
        xs = [W / 2.0 + sg * (key / 2.0 + 0.10 * s + i * pitch) for i in range(nf)]
        fingers += [_rect_pts(xc - fw / 2.0, yf, fw, fh) for xc in xs]
        cx_ = sum(xs) / nf
        legs = [((0, -1), rise), ((sg, -1), corner)]
        if wrap:
            sx = W / 2.0 + sg * (W / 2.0 - side_x)
            legs += [((sg, 0), abs(sx - cx_) - 2 * corner / math.sqrt(2)), ((sg, -1), corner), ((0, -1), FAR)]
        else:
            legs += [((sg, 0), FAR)]
        B.route(B.bus_lines([(xc, yf) for xc in xs], (0, -1), legs), "edge", min_len=0.3 * s)
    B.block((W / 2.0 - bw - key - 0.2 * s, yf - 0.05 * s, 2 * bw + 2 * key + 0.4 * s, fh), "edge")
    B.gold += fingers
    notch = _rect_pts(W / 2.0 - key / 2.0, H - fh * 0.62, key, fh * 0.62)
    B.parts.append(lambda: _fill(slide, [notch], k.P["offboard"], layer=False,
                                 reason="the key notch cut into the board's edge connector"))
    B.draw()
    _run_all(ds)
    return r


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_circuit(slide, role, index):
    """An ordinary page (a chart, an agenda) on the board: the mounting holes are the page's ground (new_slide paints
    them); the content rect clear of them, in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.75, 0.70, W - 1.5, H - 1.4)


_card_circuit = vl._card_for(NAME)
