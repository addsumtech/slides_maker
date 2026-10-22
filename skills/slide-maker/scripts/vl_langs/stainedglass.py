"""stainedglass — the Stained glass language (彩绘玻璃): its ground painter, its card and its seven pages.

Stained-glass windows set in pale stone: jewel-tone glass cut into pieces and held by thick dark lead, a rose window
built from radial segments (stone tracery over the glass), pointed lancet windows with a border of small pieces round
a field of diamond quarries, medallions along their axis. The words never sit on busy glass — they sit on the plain
stone, inside a plastered niche, or on a clear pane at a window's centre (the section's number, the key figure, each
point's number). Every page PLANS its words first (vl_native2.flow / stack: measured, never under a floor), draws its
glass clear of them, then sets them. The only words it writes itself are the point numbers on each lancet's pane (the
manifest's derived words)."""
from __future__ import annotations

import math

from pptx.oxml.ns import qn

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2   # names looked up at call time: vl_native2 may still be importing when this module loads

NAME = "stainedglass"
TAU = 2.0 * math.pi
_LAYERED = "the glass, its lead and the stone that holds it are one window, layered on each other by design"


# ─────────────────────────────────────────── drawing primitives ───────────────────────────────────────────
def _dark(k):
    return bool(vl.REGISTRY[NAME]["grounds"][k.ground]["dark"])


def _decl(sh, reason):
    if sh is not None:
        dk.decorative(sh, reason)
        dk.overlap_intent(sh, _LAYERED)
    return sh


def _outline(slide, rings, color, w, *, closed=True, alpha=None):
    """Many polylines (closed rings by default) as ONE outline-only shape with round joins and caps — a window's whole
    leading is one object."""
    rings = [r for r in rings if len(r) >= 2]
    if not rings:
        return None
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    x0, y0 = min(xs), min(ys)
    bw, bh = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
    U = na.U
    d = []
    for r in rings:
        u = [((px - x0) / bw * U, (py - y0) / bh * U) for px, py in r]
        d.append("<a:moveTo>{}</a:moveTo>".format(na.orn._pt(*u[0]))
                 + "".join("<a:lnTo>{}</a:lnTo>".format(na.orn._pt(*q)) for q in u[1:])
                 + ("<a:close/>" if closed else ""))
    sh = na._custom(slide, x0, y0, bw, bh, '<a:path w="{u}" h="{u}" fill="none">{d}</a:path>'.format(u=U, d="".join(d)),
                    line=na.hexstr(color), line_w=w)
    ln = sh._element.spPr.find(qn("a:ln"))
    if ln is not None:
        if alpha is not None:
            clr = ln.find(qn("a:solidFill"))[0]
            clr.append(clr.makeelement(qn("a:alpha"), {"val": str(int(round(alpha * 100000)))}))
        ln.append(ln.makeelement(qn("a:round"), {}))
    return sh


def _circle(cx, cy, r, n=48, a0=0.0):
    return [(cx + r * math.cos(a0 + TAU * i / n), cy + r * math.sin(a0 + TAU * i / n)) for i in range(n)]


def _sector(cx, cy, r0, r1, a0, a1, n=6):
    """An annular sector (a wedge when r0 is 0), angles in radians, y down."""
    angs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    outer = [(cx + r1 * math.cos(a), cy + r1 * math.sin(a)) for a in angs]
    if r0 <= 1e-6:
        return [(cx, cy)] + outer
    return outer + [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)) for a in reversed(angs)]


def _area(p):
    return sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p))) / 2.0


def _clip(subject, clip):
    """Sutherland–Hodgman: the polygon `subject` cut to the CONVEX polygon `clip` (either winding)."""
    sgn = 1.0 if _area(clip) > 0 else -1.0
    out = list(subject)
    for i in range(len(clip)):
        a, b = clip[i - 1], clip[i]
        if not out:
            break
        if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
            continue
        inp, out = out, []

        def side(p, a=a, b=b):
            return sgn * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]))
        for j in range(len(inp)):
            cur, prev = inp[j], inp[j - 1]
            sc, sp = side(cur), side(prev)
            if sc >= 0:
                if sp < 0:
                    t = sp / (sp - sc)
                    out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
                out.append(cur)
            elif sp >= 0:
                t = sp / (sp - sc)
                out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
    return out


# ─────────────────────────────────────────── arches ───────────────────────────────────────────
def _apex_h(w, rho, d=0.0):
    """How far a pointed arch of width w (radius rho*w; 0.5 is a round arch) rises above its springing line, its
    outline offset outward by d."""
    R = rho * w
    Rd = R + d
    ta = math.acos(max(-1.0, min(1.0, (w / 2.0 - R) / Rd)))
    return Rd * math.sin(ta)


def _arch(x, w, ys, yb, rho=1.0, d=0.0, n=16, nj=1, ns=1):
    """The closed outline (inches, y down) of a window: straight jambs from the sill `yb` up to the springing line
    `ys`, then two arcs of radius rho*w meeting at the apex (rho 0.5: a round arch; 1.0: an equilateral Gothic arch);
    offset outward by d (inward when negative). The same number of points for every d — `nj` per jamb, `ns` along the
    sill, `n` per half arch — so two offsets pair point for point (a border band cut into pieces)."""
    R = rho * w
    Rd = R + d
    cl = x + R
    mid = x + w / 2.0
    ta = math.acos(max(-1.0, min(1.0, (mid - cl) / Rd)))
    left = []
    for i in range(n + 1):
        a = math.pi + (ta - math.pi) * i / n
        left.append((cl + Rd * math.cos(a), ys - Rd * math.sin(a)))
    left[-1] = (mid, left[-1][1])
    right = [(2 * mid - px, py) for px, py in reversed(left[:-1])]
    xl, xr, yf = x - d, x + w + d, yb + d
    up = [(xl, yf + (ys - yf) * j / nj) for j in range(nj)]
    down = [(xr, ys + (yf - ys) * j / nj) for j in range(1, nj + 1)]
    sill = [(xr - (xr - xl) * j / ns, yf) for j in range(1, ns)]
    return up + left + right + down + sill


def _tudor_r2(w, hh, a, al):
    """The radius of a four-centred arch's upper arcs that makes its head `hh` high (bisection; clamped)."""
    def head(R2):
        c2x = a + (R2 - a) * math.cos(al)
        c2y = (R2 - a) * math.sin(al)              # below the springing line (y down)
        dx = w / 2.0 - c2x
        if abs(dx) > R2:
            return None
        return math.sqrt(R2 * R2 - dx * dx) - c2y
    lo = a + (w / 2.0 - a) / math.cos(al)          # the arc's top just at the centre line: the lowest pointed head
    hi = 40.0 * w
    if hh <= (head(lo) or 0.0):
        return lo
    for _ in range(60):
        mid = (lo + hi) / 2.0
        h = head(mid)
        if h is None or h > hh:
            hi = mid
        else:
            lo = mid
    return lo


def _tudor(x, w, ys, yb, hh, d=0.0, n=16, a_frac=0.20, al=math.radians(52)):
    """A four-centred (Tudor) arch — a low pointed head for a wide opening: a small arc of radius a at each springing
    turning `al`, then a large arc to the apex; head `hh` high; offset outward by d. Returns (outline, apex_y)."""
    a = a_frac * w
    R2 = _tudor_r2(w, hh, a, al)
    mid = x + w / 2.0
    c1x, c1y = x + a, ys
    c2x, c2y = x + a + (R2 - a) * math.cos(al), ys + (R2 - a) * math.sin(al)
    left = []
    for i in range(n // 3 + 1):
        t = math.pi - al * i / max(1, n // 3)
        left.append((c1x + (a + d) * math.cos(t), c1y - (a + d) * math.sin(t)))
    tap = math.acos(max(-1.0, min(1.0, (mid - c2x) / (R2 + d))))
    m2 = n - n // 3
    for i in range(1, m2 + 1):
        t = (math.pi - al) + (tap - (math.pi - al)) * i / m2
        left.append((c2x + (R2 + d) * math.cos(t), c2y - (R2 + d) * math.sin(t)))
    left[-1] = (mid, left[-1][1])
    right = [(2 * mid - px, py) for px, py in reversed(left[:-1])]
    out = [(x - d, yb + d)] + left + right + [(x + w + d, yb + d)]
    return out, left[-1][1]


def _tudor_half_at(x, w, ys, hh, y, d=0.0):
    """Half the inside width of a Tudor arch outline at height y (from its own outline)."""
    if y >= ys:
        return w / 2.0 + d
    pts, apex = _tudor(x, w, ys, ys + 1.0, hh, d, n=48)
    if y <= apex:
        return 0.0
    mid = x + w / 2.0
    left = [p for p in pts[1:] if p[0] <= mid + 1e-9]
    for (x1, y1), (x2, y2) in zip(left, left[1:]):
        if (y1 - y) * (y2 - y) <= 0 and abs(y2 - y1) > 1e-12:
            px = x1 + (x2 - x1) * (y - y1) / (y2 - y1)
            return max(0.0, mid - px)
    return 0.0


# ─────────────────────────────────────────── glazing ───────────────────────────────────────────
class _Glazing:
    """The glass of one drawing, collected before anything is drawn: pieces by layer and colour (one shape per colour
    per layer — a window is a handful of objects, not hundreds), each layer's lead drawn over its own glass, so a
    medallion laid over the quarries hides their leading."""

    def __init__(self, k, slide, lead_w):
        self.k, self.slide, self.lead_w = k, slide, lead_w
        self.glass = {}
        self.lead = {}

    def piece(self, poly, colour, layer=0, lead=True, w=None):
        if len(poly) < 3 or abs(_area(poly)) < 1e-5:
            return
        self.glass.setdefault(layer, {}).setdefault(colour, []).append(poly)
        if lead:
            self.lead.setdefault(layer, {}).setdefault((w or self.lead_w, True), []).append(poly)

    def line(self, ring, layer, w=None, closed=True):
        self.lead.setdefault(layer, {}).setdefault((w or self.lead_w, closed), []).append(ring)

    def draw(self):
        for layer in sorted(set(self.glass) | set(self.lead)):
            for colour, polys in self.glass.get(layer, {}).items():
                _decl(na.multipoly(self.slide, polys, self.k.P[colour]),
                      "pieces of coloured glass in a window: ornament, nothing to read in them")
            for (w, closed), rings in self.lead.get(layer, {}).items():
                _decl(_outline(self.slide, rings, self.k.P["lead"], w, closed=closed),
                      "the lead came that holds the pieces of glass: ornament, nothing to read")

    def pieces(self):
        """Every glass piece as (colour, poly), the lead-coloured backing left out."""
        return [(c, p) for layer in sorted(self.glass) for c, ps in self.glass[layer].items() if c != "lead"
                for p in ps]


def _petal(cx, cy, r0, r1, ang, hw, n=8):
    """A pointed petal from radius r0 to r1 along `ang`, `hw` at its widest."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    right, left = [], []
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * t
        h = hw * math.sin(math.pi * t) ** 0.85
        px, py = cx + r * ux, cy + r * uy
        right.append((px + nx * h, py + ny * h))
        left.append((px - nx * h, py - ny * h))
    return right + left[::-1][1:-1]


def _rosette(G, cx, cy, r, layer, *, disc, petals, centre, m=8):
    """A small flower of glass: a disc, m petals on it in two alternating colours, a round centre."""
    G.piece(_circle(cx, cy, r, 40), disc, layer)
    rc = r * 0.26
    for i in range(m):
        a = -math.pi / 2 + TAU * i / m
        G.piece(_petal(cx, cy, rc * 0.7, r * 0.90, a, r * 0.95 * math.sin(math.pi / m)), petals[i % 2], layer + 1)
    G.piece(_circle(cx, cy, rc, 24), centre, layer + 2)


def _ring_pieces(G, cx, cy, r0, r1, m, colours, layer, a0=-math.pi / 2):
    for i in range(m):
        G.piece(_sector(cx, cy, r0, r1, a0 + TAU * i / m, a0 + TAU * (i + 1) / m, 4), colours[i % len(colours)], layer)


# ─────────────────────────────────────────── the rose window ───────────────────────────────────────────
SCHEMES = {
    # the outer field (two cuts), the petals (two cuts: one each side of the petal's lead), the oculus in each petal,
    # the middle ring (two cuts), its bosses, the rim of small pieces inside the stone, the hub's ring, the hub's
    # rosette (disc, petals, centre). Three hues lead each window; the others are small touches, as in a real rose.
    "cover": dict(field=("sapphire", "sapphire2"), petal=("ruby", "ruby2"), oculus="amber2",
                  mid=("violet", "sapphire2"), boss="emerald2", rim=("amber", "ruby2"), hub_ring=("amber", "amber2"),
                  rosette=("ruby2", ("amber", "amber2"), "emerald")),
    "section": dict(field=("ruby", "ruby2"), petal=("sapphire", "sapphire2"), oculus="amber2", mid=("amber", "amber2"),
                    boss="emerald2", rim=("sapphire2", "amber"), hub_ring=("sapphire", "sapphire2"),
                    rosette=("sapphire", ("amber", "amber2"), "ruby")),
    "data": dict(field=("sapphire", "sapphire2"), petal=("violet", "violet2"), oculus="amber2", mid=("ruby", "ruby2"),
                 boss="amber2", rim=("amber", "ruby2"), hub_ring=("amber", "amber2"),
                 rosette=("ruby2", ("amber", "amber2"), "emerald")),
    "oculus": dict(field=("sapphire", "sapphire2"), petal=("ruby", "ruby2"), oculus="amber2",
                   mid=("emerald", "emerald2"), boss="amber2", rim=("amber", "ruby2"), hub_ring=("amber", "amber2"),
                   rosette=("ruby2", ("amber", "amber2"), "emerald")),
}


def _tone(pair, i, j, band):
    """One of a colour's two cuts for the piece in sector i, half j, band `band`: one piece in three in the second
    cut, on a period that repeats round the whole ring — streaky, never a checkerboard, and every cut reaches all the
    way round (a cut that landed only in the top half drew a shape whose box ended mid-window, and the lint read it as
    a card the centre number overran)."""
    return pair[1] if (2 * i + j + band) % 3 == 0 else pair[0]


def _glow(k, sh, size):
    """On the night ground, glass is lit: a soft halo of its light on the wall round the window."""
    if sh is not None and _dark(k):
        na.soft_shadow(sh, blur=size, dist=0.0, alpha=0.55, color=k.P["light"])


def _rose(k, slide, cx, cy, R, *, n=12, hub=0.32, hub_kind="rosette", scheme="cover"):
    """A rose window centred at (cx, cy), radius R: a stone ring; inside it glass in three zones — an outer ring of
    n pointed petals (each with a small round oculus) on a two-cut field, a middle ring of wedges with a boss at every
    spoke, and the hub — a glass rosette, or a clear pane (hub_kind "pane") that a number is set on. Stone tracery (n
    spokes and three rings) is laid over the glass. Returns the pane's radius (0 for a rosette)."""
    W, H, s, o = ctx(k)
    S = SCHEMES[scheme]
    Rg = R * 0.87
    rh = Rg * hub
    r2 = rh + (Rg - rh) * 0.40
    lead = max(0.6, min(1.8, 0.55 * R / max(s, 0.3)))
    stone = na.disc(slide, cx, cy, 2 * R, k.P["stone"])
    _decl(stone, "the stone ring of a rose window: ornament, nothing to read in it")
    _glow(k, stone, 0.30 * R)
    if not _dark(k):
        na.soft_shadow(stone, blur=0.10 * s, dist=0.04 * s, alpha=0.22)
    _decl(_outline(slide, [_circle(cx, cy, R, 96), _circle(cx, cy, R * 0.955, 96)], k.P["stone_edge"], 0.75),
          "the mouldings of the rose window's stone ring")
    G = _Glazing(k, slide, lead)
    G.piece(_circle(cx, cy, Rg, 96), "lead", 0, lead=False)
    step = TAU / n
    Rb = Rg - max(0.045 * s, min(0.12 * s, 0.055 * Rg))          # the rim of small pieces inside the stone
    _ring_pieces(G, cx, cy, Rb, Rg, 3 * n, S["rim"], 1, a0=-math.pi / 2 - step / 2)
    rf = r2 + 0.52 * (Rb - r2)
    for i in range(n):
        a0 = -math.pi / 2 - step / 2 + step * i
        a1, am = a0 + step, a0 + step / 2
        for j, (b0, b1) in enumerate(((a0, am), (am, a1))):
            G.piece(_sector(cx, cy, r2, rf, b0, b1, 4), _tone(S["field"], i, j, 1), 1)
            G.piece(_sector(cx, cy, rf, Rb, b0, b1, 4), _tone(S["field"], i, j, 2), 1)
            G.piece(_sector(cx, cy, rh, r2, b0, b1, 4), S["mid"][j], 1)
        # the petal: a lancet head pointing outward, its foot on the middle ring, cut in two down its axis
        hw = min((r2 + 0.10 * (Rb - r2)) * math.sin(step / 2) * 0.80, (Rb - r2) * 0.36)
        rb, rt = r2 + 0.05 * (Rb - r2), Rb - 0.07 * (Rb - r2)
        ah = _apex_h(2 * hw, 1.0)
        rs = max(rb + 0.2 * (rt - rb), rt - ah)
        loc = _arch(-hw, 2 * hw, -rs, -rb, 1.0, 0.0, n=8)
        ux, uy, tx, ty = math.cos(am), math.sin(am), -math.sin(am), math.cos(am)
        glob = [(cx + (-ly) * ux + lx * tx, cy + (-ly) * uy + lx * ty) for lx, ly in loc]
        foot = (cx + rb * ux, cy + rb * uy)
        G.piece([foot] + glob[:10], S["petal"][0], 2)              # loc: the jamb foot, 9 arc points to the apex …
        G.piece(glob[9:] + [foot], S["petal"][1], 2)               # … then the other half from the apex down
        ro = rb + (rs - rb) * 0.55
        G.piece(_circle(cx + ro * ux, cy + ro * uy, hw * 0.42, 20), S["oculus"], 3)
        rbm = (rh + r2) / 2.0
        G.piece(_circle(cx + rbm * math.cos(a0), cy + rbm * math.sin(a0),
                        min((r2 - rh) * 0.20, rbm * math.sin(step / 2) * 0.50), 18), S["boss"], 2)
    rp = 0.0
    if hub_kind == "pane":
        rp = rh * 0.84
        _ring_pieces(G, cx, cy, rp, rh, max(8, n), S["hub_ring"], 4)
        G.piece(_circle(cx, cy, rp, 72), "pane", 5, w=lead * 1.6)
    else:
        _rosette(G, cx, cy, rh, 4, disc=S["rosette"][0], petals=S["rosette"][1], centre=S["rosette"][2],
                 m=8 if n % 8 == 0 else max(6, n // 2 if n > 12 else n))
    G.draw()
    tw = max(1.2, min(6.0, 2.0 * R / max(s, 0.3)))
    angs = [-math.pi / 2 - step / 2 + step * i for i in range(n)]
    spokes = [((cx + rh * math.cos(a), cy + rh * math.sin(a)), (cx + Rb * math.cos(a), cy + Rb * math.sin(a)))
              for a in angs]
    rings = [_circle(cx, cy, r, 96) for r in (rh, r2, Rb)]
    for col, w in ((k.P["lead"], tw + 1.4), (k.P["stone"], tw)):
        _decl(na.strokes(slide, spokes, col, w=w), "the stone tracery of the rose window: ornament, nothing to read")
        _decl(_outline(slide, rings, col, w), "the stone tracery rings of the rose window: ornament, nothing to read")
    return rp


# ─────────────────────────────────────────── the lancet window ───────────────────────────────────────────
_POINT_GLASS = (("sapphire", "sapphire2"), ("ruby", "ruby2"), ("emerald", "emerald2"), ("violet", "violet2"))
_POINT_TRIM = (("amber", "ruby"), ("amber", "sapphire"), ("amber2", "ruby2"), ("amber", "emerald"))


def _band_pieces(G, outer, inner, bounds, colours, layer):
    """The band between two paired outlines (outer, inner), cut at the point indices `bounds`."""
    N = len(outer)
    for j, (b0, b1) in enumerate(zip(bounds, bounds[1:] + [bounds[0] + N])):
        idx = [i % N for i in range(b0, b1 + 1)]
        G.piece([outer[i] for i in idx] + [inner[i] for i in reversed(idx)], colours[j % len(colours)], layer)


def _arch_bounds(nj, n, ns, pp):
    """Where a border band round an _arch outline is cut: every jamb and sill point, every pp-th arc point."""
    b = list(range(0, nj)) + [nj + i for i in range(0, 2 * n + 1, pp)]
    if b[-1] != nj + 2 * n:
        b.append(nj + 2 * n)
    b += [nj + 2 * n + j for j in range(1, nj + 1)] + [2 * nj + 2 * n + j for j in range(1, ns)]
    return sorted(set(b))


def _lancet(k, slide, x, w, top, yb, *, rho=1.0, glass=("sapphire", "sapphire2"), trim=("amber", "ruby"),
            medals=(), sill=True):
    """A lancet window, its glass from `top` (the apex) to `yb` (the sill), `w` wide: a stone surround and sill; a
    border band of small pieces in the two `trim` colours; a field of diamond quarries in the two `glass` cuts; and
    medallions along the axis — medals = [(cy, r, kind)], kind "pane" (a clear pane for a number) or "rosette".
    Returns (glazing, springing y)."""
    W, H, s, o = ctx(k)
    ah = _apex_h(w, rho)
    ys = top + ah
    b = max(0.045 * s, min(0.15 * s, 0.10 * w))
    fs = max(0.05 * s, min(0.16 * s, 0.10 * w))
    lead = max(0.6, min(2.0, 0.45 + 0.85 * w / max(s, 0.3)))
    sur = na.poly(slide, _arch(x, w, ys, yb, rho, fs, n=24), fill=k.P["stone"], line=k.P["stone_edge"], line_w=0.6)
    _decl(sur, "the stone surround of a lancet window: ornament, nothing to read in it")
    _glow(k, sur, 0.22 * w + 0.10 * s)
    if sill:
        sb = dk.box(slide, x - fs - 0.06 * s, yb + fs - 0.01 * s, w + 2 * fs + 0.12 * s, 0.09 * s, fill=k.P["stone"],
                    line=dk._as_rgb(k.P["stone_edge"]), line_w=0.6)
        _decl(sb, "the stone sill under a lancet window: ornament, nothing to read in it")
    G = _Glazing(k, slide, lead)
    L = max(0.16 * s, 2.2 * b)
    arc_len = (rho * w) * (math.pi - math.acos(max(-1.0, min(1.0, (w / 2.0 - rho * w) / (rho * w)))))
    npieces = max(2, int(round(arc_len / L)))
    pp = 3
    narc = npieces * pp
    nj = max(1, int(round((yb - ys) / L)))
    ns = max(1, int(round(w / L)))
    edge = _arch(x, w, ys, yb, rho, 0.0, n=narc, nj=nj, ns=ns)
    _band_pieces(G, edge, _arch(x, w, ys, yb, rho, -b, n=narc, nj=nj, ns=ns), _arch_bounds(nj, narc, ns, pp), trim, 1)
    G.piece(edge, "lead", 0, lead=False)
    field = _arch(x, w, ys, yb, rho, -b, n=24)
    iw = w - 2 * b
    across = 2 if iw < 0.9 * s else 3 if iw < 1.9 * s else 4
    qa = iw / (2.0 * across)
    qb = qa * 1.45
    j, y = 0, top - qb
    while y <= yb + qb:
        off = qa if j % 2 else 0.0
        xq = x + b - 2 * qa + off
        i = 0
        while xq <= x + w + 2 * qa:
            d = [(xq, y - qb), (xq + qa, y), (xq, y + qb), (xq - qa, y)]
            p = _clip(d, field)
            if len(p) >= 3:
                pu = (round((xq - x) / qa) + round((y - top) / qb)) // 2
                pv = (round((xq - x) / qa) - round((y - top) / qb)) // 2
                G.piece(p, glass[1] if (pu % 2 == 0 and pv % 2 == 0) else glass[0], 1)
            xq += 2 * qa
            i += 1
        y += qb
        j += 1
    G.line(field, 1, w=lead)
    for (my, mr, kind) in medals:
        mx = x + w / 2.0
        _ring_pieces(G, mx, my, mr * 0.80, mr, 10, trim, 2)
        if kind == "pane":
            G.piece(_circle(mx, my, mr * 0.80, 56), "pane", 3, w=lead * 1.5)
        else:
            other = "ruby" if glass[0] != "ruby" else "sapphire"
            centre = "emerald" if glass[0] != "emerald" else "amber"
            _rosette(G, mx, my, mr * 0.80, 3, disc=other, petals=("amber2", glass[1]), centre=centre, m=8)
    G.line(edge, 4, w=lead * 1.6)
    G.draw()
    return G, ys


# ─────────────────────────────────────────── layout helpers ───────────────────────────────────────────
def _m(k):
    W, H, s, o = ctx(k)
    return (0.55 if o == "land" else 0.48) * s


def _foot(rects, default):
    return max((v[1] + v[3] for v in rects.values()), default=default)


def _number_in(k, slide, page, cx, cy, rp, num, field="number", start=None):
    """PLAN `num` on a round clear pane of radius rp at (cx, cy): a tall box and a wide box, both inside the circle, are
    planned and the one that sets the number larger is kept ("02" stands tall, "1,240" lies wide). Refuses
    (VLTextOverflow) when neither holds it at its floor."""
    best, last = None, None
    for bwf, bhf in ((1.30, 1.50), (1.66, 1.06)):
        bw, bh = rp * bwf, rp * bhf
        kw = {"anchor": "middle", "align": "c"}
        if start:
            kw["start"] = start
        try:
            rects, d = _v2.flow(k, slide, page, (cx - bw / 2.0, cy - bh / 2.0, bw, bh), [(field, num)], **kw)
        except vl.VLTextOverflow as e:
            last = e
            continue
        z = getattr(d, "sizes", {}).get(field, 0.0)
        if best is None or z > best[0] + 1e-6:
            best = (z, rects, d)
    if best is None:
        raise last
    return best[1], best[2]


def _sizes(ds):
    return {f_: z for d in ds for f_, z in getattr(d, "sizes", {}).items()}


def _nlines(k, rects, ds, field):
    """How many lines a planned field takes (its box height over its line height)."""
    if field not in rects:
        return 0
    z = _sizes(ds).get(field)
    if not z:
        return 1
    return int(round(rects[field][3] / (z / 72.0 * 1.2)))


def _one_line_heads(k, heads, w):
    """A start size for the point heads under narrow windows: when a Latin head is a little too wide for its column,
    every head is set a little smaller (never under 85%, never under the floor) so it holds ONE line — wrapped, "Plane
    trees lead by far" left "far" alone under the window (16:9, four points). None when every head fits, or one would
    need more than that (it wraps anyway; the flow balances it)."""
    base, _role, _b, _c, _i, floor = vl.TYPE[NAME]["item_head"]
    W, H, s, o = ctx(k)
    z = base * s
    room = w * vl.HEADROOM - dk.TEXT_INSET_LR - 0.02
    need = max((_v2.ink_w(k, "item_head", t, z) for t in heads if t and not dk._has_cjk(t)), default=0.0)
    if need <= room:
        return None
    fit = z * room / need * 0.98
    return fit if fit >= max(0.85 * z, floor * s) else None


def _below(k, slide, page, top, art_h, gap, groups, *, align="c", start=None):
    """Portrait and square pages: the art (art_h tall, from `top`) and the words under it as ONE block — planned at the
    top, then moved down by a share of what is left, so the page holds no empty band between the window and its
    words. Returns (dy, rects, draws): the art moves down by dy too."""
    W, H, s, o = ctx(k)
    m = _m(k)
    x, w = m + 0.15 * s, W - 2 * m - 0.30 * s

    def plan(dy):
        return _v2.stack(k, slide, page, x, w, top + dy + art_h + gap, H - m, groups, anchor="top", align=align,
                         start=start)
    r, ds = plan(0.0)
    if not r:
        return 0.0, r, ds
    dy = max(0.0, ((H - m) - _foot(r, H - m)) * 0.42)
    if dy > 0.04 * s:
        r, ds = plan(dy)
    return dy, r, ds


# ─────────────────────────────────────────── the pages ───────────────────────────────────────────
@register(NAME, "cover", alts=3)
def _sg_cover(k, slide, f, image):
    """A rose window beside the title: the kicker, title and subtitle on the plain stone at the left, the rose window
    at the right (above them, centred, on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.22 * s), (_v2.fields(f, ("title",)), 0.24 * s),
              (_v2.fields(f, ("subtitle",)), 0.0)]
    start = None if a < 2 else {"title": 32 * s}
    if o == "land":
        R = min((0.42, 0.37, 0.31)[a] * H, (0.20, 0.18, 0.16)[a] * W)
        cx, cy = W - m - R, H / 2.0
        tx = m + 0.30 * s
        r, ds = _v2.stack(k, slide, "cover", tx, cx - R - 0.70 * s - tx, m, H - m, groups, anchor="middle", start=start)
        if a == 0 and _nlines(k, r, ds, "title") > 4:
            # a title stacked five lines deep beside the window reads as a column of words: give it the room first
            raise vl.VLTextOverflow("stainedglass.cover(): the title takes more than four lines beside the window")
    else:
        R = min((0.38, 0.33, 0.27)[a] * W, (0.205, 0.175, 0.145)[a] * H)
        dy, r, ds = _below(k, slide, "cover", m, 2 * R, 0.40 * s, groups, start=start)
        cx, cy = W / 2.0, m + R + dy
    _rose(k, slide, cx, cy, R, n=12, hub=0.30, hub_kind="rosette", scheme="cover")
    _run_all(ds)
    return r


@register(NAME, "section", alts=3)
def _sg_section(k, slide, f, image):
    """The section's number on the clear pane at the centre of a rose window; the kicker and title on the stone beside
    it (under it on a portrait or square page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    num = text_of(f, "number")
    on_pane = bool(num) and a < 2
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.18 * s), (_v2.fields(f, ("title",)), 0.0)]
    if num and not on_pane:              # the last layout: the number heads the column, the window keeps its rosette
        groups = [([("number", num)], 0.10 * s)] + groups
    tstart = None if a < 2 else {"title": 30 * s, "number": 72 * s}
    if o == "land":
        R = min((0.40, 0.35, 0.30)[a] * H, (0.21, 0.19, 0.17)[a] * W)
        cx, cy = m + 0.15 * s + R, H / 2.0
        x0 = cx + R + 0.75 * s
        tr, tds = _v2.stack(k, slide, "section", x0, W - m - 0.2 * s - x0, m, H - m, groups, anchor="middle",
                            align="l", start=tstart)
    else:
        R = min((0.36, 0.31, 0.24)[a] * W, (0.22, 0.18, 0.14)[a] * H)
        dy, tr, tds = _below(k, slide, "section", m + 0.05 * s, 2 * R, 0.45 * s, groups, start=tstart)
        cx, cy = W / 2.0, m + R + 0.05 * s + dy
    hub = 0.46
    r, ds = {}, []
    if on_pane:
        # the pane grows (the glass round it gives way) until the number stands on it at its floor or larger
        last = None
        for hub in (0.46, 0.54, 0.62):
            rp = R * 0.87 * hub * 0.84
            try:
                nr, nd = _number_in(k, slide, "section", cx, cy, rp, num,
                                    start={"number": min(110 * s, rp * 72 * 1.25)})
                break
            except vl.VLTextOverflow as e:
                last = e
        else:
            raise last
        r.update(nr)
        ds.append(nd)
    r.update(tr)
    _rose(k, slide, cx, cy, R, n=8, hub=hub if on_pane else 0.40, hub_kind="pane" if on_pane else "rosette",
          scheme="section")
    _run_all(ds + tds)
    return r


@register(NAME, "data", alts=3)
def _sg_data(k, slide, f, image):
    """The key figure on the large clear pane at the heart of a rose window; the label and note on the stone beside it
    (under it on a portrait or square page). A figure too wide for the pane is set at the head of the column instead,
    the window keeping its glass rosette."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    num = text_of(f, "number")
    on_pane = bool(num) and a < 2
    names = ("label", "note") if on_pane or not num else ("number", "label", "note")
    groups = [(_v2.fields(f, names), 0.0)]
    if o == "land":
        R = min((0.43, 0.38, 0.36)[a] * H, (0.23, 0.21, 0.20)[a] * W)
        cx, cy = W - m - 0.10 * s - R, H / 2.0
        x0 = m + 0.30 * s
        tr, tds = _v2.stack(k, slide, "data", x0, cx - R - 0.80 * s - x0, m, H - m, groups, anchor="middle", align="l")
    else:
        R = min((0.38, 0.36, 0.30)[a] * W, (0.25, 0.21, 0.16)[a] * H)
        dy, tr, tds = _below(k, slide, "data", m + 0.05 * s, 2 * R, 0.45 * s, groups)
        cx, cy = W / 2.0, m + R + 0.05 * s + dy
    r, ds = {}, []
    hub = 0.32
    if on_pane:
        # the pane grows (the glass round it gives way) until the figure stands on it at its floor or larger
        last = None
        for hub in (0.50, 0.58, 0.66):
            rp = R * 0.87 * hub * 0.84
            try:
                nr, nd = _number_in(k, slide, "data", cx, cy, rp, num, start={"number": min(140 * s, rp * 72 * 1.1)})
                break
            except vl.VLTextOverflow as e:
                last = e
        else:
            raise last
        r.update(nr)
        ds.append(nd)
    r.update(tr)
    _rose(k, slide, cx, cy, R, n=16, hub=hub, hub_kind="pane" if on_pane else "rosette", scheme="data")
    _run_all(ds + tds)
    return r


@register(NAME, "points", alts=5)
def _sg_points(k, slide, f, image):
    """An arcade of lancet windows, one per point, each in its own glass, its number on the clear pane of its
    medallion, the point's head and line on the stone under the sill. Long copy or a narrow page: rows — a slim
    lancet beside each point — then two columns of rows, then a small round pane in place of the window."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    pts = points_of(f.get("items"))
    n = len(pts)
    tall = H / W > 1.2
    if o == "land":
        layout = ("cols", "cols", "rows", "rows2", "roundels")[a]
    else:                                 # a portrait or square page: an arcade of three, or two over two
        layout = ("cols" if n <= 3 else "grid", "grid" if (tall and n >= 3) else "rows", "rows", "rows2", "roundels")[a]
    x0, w0 = m + 0.10 * s, W - 2 * m - 0.20 * s
    r, ds = _v2.stack(k, slide, "points", x0, w0, m, m + (0.24 if a == 0 else 0.30) * H,
                      [(_v2.fields(f, ("kicker",), ("kicker",)), 0.10 * s), (_v2.fields(f, ("title",)), 0.0)],
                      anchor="top", align="l", start=None if a < 2 else {"title": 30 * s})
    top = _foot(r, m) + (0.40 if a < 2 else 0.30) * s
    bottom = H - m
    nos = [str(i + 1) for i in range(n)]
    items = [[("item_head", hd)] + ([("item_line", ln)] if ln else []) for hd, ln in pts]
    art = []
    if layout in ("cols", "grid"):
        # an arcade: each point a lancet standing on a stone string course, its head and line on the stone under it;
        # one row across ("cols"), or two over two ("grid") on a portrait page
        ncol = n if layout == "cols" else min(n, 2)
        nrow = -(-n // ncol)
        gap, rgap = 0.45 * s, 0.50 * s
        cw = (w0 - (ncol - 1) * gap) / ncol
        cell_h = (bottom - top - (nrow - 1) * rgap) / nrow
        min_win = (2.1 if (a == 0 and nrow == 1) else 1.45) * s
        room = cell_h - min_win - 0.45 * s
        if room < 0.5 * s:
            raise vl.VLTextOverflow("stainedglass.points(): no room for the labels under the windows")
        hz = _one_line_heads(k, [hd for hd, _ln in pts], cw)
        kw0 = {"anchor": "top", "align": "c"}
        if hz:
            kw0["start"] = {"item_head": hz}
        probe = _v2.plan_together(k, slide, "points", [((0, 0, cw, room), it, dict(kw0)) for it in items])
        need = max(_foot(pr, 0.0) for pr, _d in probe) + 0.05 * s
        avail = cell_h - need - 0.40 * s
        if avail < min_win:
            raise vl.VLTextOverflow("stainedglass.points(): the labels leave the windows {:.2f}in".format(avail))
        ww = min(cw * 0.58, avail / 2.5, 1.75 * s)
        wh = min(avail, ww * 3.4)
        lift = (cell_h - (wh + 0.40 * s + need)) * (0.5 if nrow > 1 else 0.85 if o == "land" else 0.55)
        sizes = _sizes([d_ for _pr, d_ in probe])
        cells = []
        for i in range(n):
            row, col = divmod(i, ncol)
            in_row = min(ncol, n - row * ncol)
            cx0 = x0 + col * (cw + gap) + (ncol - in_row) * (cw + gap) / 2.0
            sill_y = top + row * (cell_h + rgap) + lift + wh
            cells.append((cx0, sill_y))
        planned = _v2.plan_together(k, slide, "points", [((cx0, sy + 0.40 * s, cw, need + 0.05 * s), it,
                                                          {"anchor": "top", "align": "c", "start": sizes})
                                                         for (cx0, sy), it in zip(cells, items)])
        pr_ = ww * 0.38
        nplans = []
        for i, (cx0, sy) in enumerate(cells):
            wtop = sy - wh
            ys = wtop + _apex_h(ww, 1.0)
            my = ys + max(pr_ + 0.12 * s, (sy - ys) * 0.38)
            nplans.append(_number_in(k, slide, "points", cx0 + cw / 2.0, my, pr_ * 0.80, nos[i], field="item_no"))
            art.append(lambda i=i, cx0=cx0, sy=sy, wtop=wtop, my=my: _lancet(
                k, slide, cx0 + cw / 2.0 - ww / 2.0, ww, wtop, sy, glass=_POINT_GLASS[i % 4], trim=_POINT_TRIM[i % 4],
                medals=[(my, pr_, "pane")], sill=False))
        for sy in sorted({sy for _cx, sy in cells}):
            band = dk.box(slide, x0 - 0.05 * s, sy + 0.06 * s, w0 + 0.10 * s, 0.10 * s, fill=k.P["stone"],
                          line=dk._as_rgb(k.P["stone_edge"]), line_w=0.6)
            _decl(band, "the stone string course the arcade's windows stand on: ornament, nothing to read")
        for (pr, pd), (nr, nd) in zip(planned, nplans):
            r.update(pr)
            r.update(nr)
            ds += [pd, nd]
        _run_all(art + ds)
        return r
    # rows: a slim lancet (or a small round pane) beside each point's head and line
    cols = 2 if (layout in ("rows2", "roundels2") or (layout == "roundels" and o == "land")) and n >= 3 else 1
    rows = -(-n // cols)
    cgap, gap = 0.45 * s, (0.24 if layout.startswith("rows") else 0.20) * s
    cw = (w0 - (cols - 1) * cgap) / cols
    lw = (0.85 if layout.startswith("rows") else 0.70) * s
    tx = lw + 0.30 * s
    share = (bottom - top - (rows - 1) * gap) / rows
    probe = _v2.plan_together(k, slide, "points", [((0, 0, cw - tx, share), it, {"anchor": "top"}) for it in items])
    floor_h = (1.25 if layout.startswith("rows") else 0.72) * s
    hs = [max(_foot(pr, 0.0) + 0.05 * s, floor_h) for pr, _d in probe]
    row_h = [max(hs[i] for i in range(rw * cols, min(n, rw * cols + cols))) for rw in range(rows)]
    block = sum(row_h) + gap * (rows - 1)
    if block > bottom - top + 1e-6:
        raise vl.VLTextOverflow("stainedglass.points(): the rows need {:.2f}in, the page has {:.2f}in".format(
            block, bottom - top))
    y = top + (bottom - top - block) * 0.40
    ys_ = []
    for rw in range(rows):
        ys_.append(y)
        y += row_h[rw] + gap
    sizes = {f_: z for _pr, d_ in probe for f_, z in getattr(d_, "sizes", {}).items()}
    boxes = [(x0 + (i % cols) * (cw + cgap), ys_[i // cols], row_h[i // cols]) for i in range(n)]
    planned = _v2.plan_together(k, slide, "points", [((bx + tx, by, cw - tx, bh), it,
                                                      {"anchor": "middle", "start": sizes})
                                                     for i, ((bx, by, bh), it) in enumerate(zip(boxes, items))])
    for i, ((bx, by, bh), (pr, pd)) in enumerate(zip(boxes, planned)):
        r.update(pr)
        ds.append(pd)
        if layout.startswith("rows"):
            ww = lw * 0.80
            fs = max(0.05 * s, min(0.16 * s, 0.10 * ww))
            wtop, wb = by + fs + 0.02 * s, by + bh - fs - 0.10 * s
            ys = wtop + _apex_h(ww, 1.0)
            pr_ = ww * 0.38
            my = ys + max(pr_ + 0.04 * s, (wb - ys) * 0.45)
            if my + pr_ > wb - 0.04 * s:
                my = (ys + wb) / 2.0
            nr, nd = _number_in(k, slide, "points", bx + lw / 2.0, my, pr_ * 0.80, nos[i], field="item_no")
            art.append(lambda i=i, bx=bx, ww=ww, wtop=wtop, wb=wb, my=my, pr_=pr_: _lancet(
                k, slide, bx + (lw - ww) / 2.0, ww, wtop, wb, glass=_POINT_GLASS[i % 4], trim=_POINT_TRIM[i % 4],
                medals=[(my, pr_, "pane")], sill=False))
        else:
            rr = min(lw / 2.0, bh / 2.0)
            cy = by + bh / 2.0
            nr, nd = _number_in(k, slide, "points", bx + lw / 2.0, cy, rr * 0.62, nos[i], field="item_no")
            art.append(lambda i=i, bx=bx, cy=cy, rr=rr: _roundel(k, slide, bx + lw / 2.0, cy, rr, i))
        r.update(nr)
        ds.append(nd)
    _run_all(art + ds)
    return r


def _roundel(k, slide, cx, cy, r, i):
    """A small round window: a ring of glass pieces in the point's colours round a clear pane, in a stone rim."""
    W, H, s, o = ctx(k)
    stone = na.disc(slide, cx, cy, 2 * r, k.P["stone"])
    _decl(stone, "the stone rim of a small round window: ornament, nothing to read")
    _glow(k, stone, 0.15 * r + 0.05 * s)
    G = _Glazing(k, slide, max(0.6, min(1.4, 1.6 * r / max(s, 0.3))))
    rg = r * 0.86
    G.piece(_circle(cx, cy, rg, 48), "lead", 0, lead=False)
    _ring_pieces(G, cx, cy, rg * 0.72, rg, 12, (_POINT_GLASS[i % 4][0], _POINT_TRIM[i % 4][0]), 1)
    G.piece(_circle(cx, cy, rg * 0.72, 48), "pane", 2, w=G.lead_w * 1.5)
    G.line(_circle(cx, cy, rg, 48), 3, w=G.lead_w * 1.6)
    G.draw()


@register(NAME, "quote", alts=3)
def _sg_quote(k, slide, f, image):
    """The quote under a stone arch: a plastered niche with a low four-centred head, a small rose window in the head,
    the quote and its attribution on the plaster under it."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    if o == "land":
        nw = min((0.64, 0.74, 0.84)[a] * W, W - 2 * m - 0.4 * s)
    else:
        nw = min((0.84, 0.88, 0.92)[a] * W, W - 2 * m)
    nx = (W - nw) / 2.0
    hh = min(0.31 * nw, 0.34 * H)
    apex = m
    ys = apex + hh
    yb = H - m
    pad = (0.55 if a < 2 else 0.40) * s
    oc = a < 2
    ro = min(0.40 * hh, (1.05 if a == 0 else 0.72) * s, 0.13 * nw) if oc else 0.0
    oy = apex + ro + 0.12 * s

    def clear_of_head(cy_):              # the little rose sits whole inside the arch's head, a hand's width from it
        return all(_tudor_half_at(nx, nw, ys, hh, cy_ - ro * t) >= ro * math.sqrt(max(0.0, 1 - t * t)) + 0.14 * s
                   for t in (1.0, 0.85, 0.7, 0.5, 0.25, 0.0))
    while oc and not clear_of_head(oy) and oy < ys:
        oy += 0.03 * s
    cw = nw - 2 * pad
    ytop = ys - hh * 0.55
    while ytop < ys and _tudor_half_at(nx, nw, ys, hh, ytop) < cw / 2.0 + 0.15 * s:
        ytop += 0.02 * s
    if oc:
        ytop = max(ytop, oy + ro + 0.30 * s)
    groups = [(_v2.fields(f, ("quote",)), 0.30 * s), (_v2.fields(f, ("attribution",), ("attribution",)), 0.0)]
    if o == "land":
        r, ds = _v2.stack(k, slide, "quote", nx + pad, cw, ytop, yb - 0.35 * s, groups, anchor="middle", align="c")
    else:
        # a tall page: the niche keeps a doorway's proportion (a page-high niche left half of itself empty under a
        # short quote) and grows only for longer words; the whole arch stands a little above the page's centre
        r, ds = _v2.stack(k, slide, "quote", nx + pad, cw, ytop, yb - 0.35 * s, groups, anchor="top", align="c")
        yb2 = min(yb, max(ys + 0.8 * s, _foot(r, ytop) + 0.75 * s, apex + 1.15 * nw))
        dy = max(0.0, (H - m - yb2) * 0.42)
        apex, ys, yb, oy, ytop = apex + dy, ys + dy, yb2 + dy, oy + dy, ytop + dy
        r, ds = _v2.stack(k, slide, "quote", nx + pad, cw, ytop, yb - 0.35 * s, groups, anchor="middle", align="c")
    outline, _ap = _tudor(nx, nw, ys, yb, hh, 0.0, n=36)
    niche = na.poly(slide, outline, fill=k.P["niche"])
    _decl(niche, "the plastered niche under the arch: the quote is set on it, the niche itself says nothing")
    band = 0.16 * s
    ph = 0.34 * s                         # the jambs stand on stone bases; the moulding ends on top of them

    def on_bases(pts):
        return [(px, min(py, yb - ph)) for px, py in pts]
    path = on_bases(_tudor(nx, nw, ys, yb, hh, band / 2.0, n=36)[0])
    edges = [on_bases(_tudor(nx, nw, ys, yb, hh, dd, n=36)[0]) for dd in (0.0, band)]
    _decl(na.polyline(slide, path, k.P["stone"], w=band * 72.0), "the stone moulding of the arch: ornament only")
    _decl(_outline(slide, edges, k.P["stone_edge"], 0.75, closed=False), "the edges of the arch's stone moulding")
    th = dk.box(slide, nx - band - 0.08 * s, yb - 0.09 * s, nw + 2 * band + 0.16 * s, 0.09 * s, fill=k.P["stone"],
                line=dk._as_rgb(k.P["stone_edge"]), line_w=0.6)
    _decl(th, "the stone threshold the arch stands on: ornament only")
    for side in (-1, 1):
        bx = nx - band - 0.08 * s if side < 0 else nx + nw - 0.08 * s
        pl = dk.box(slide, bx, yb - ph, band + 0.16 * s, ph, fill=k.P["stone"], line=dk._as_rgb(k.P["stone_edge"]),
                    line_w=0.6)
        _decl(pl, "the stone base of the arch's jamb: ornament only")
    if oc:
        _rose(k, slide, W / 2.0, oy, ro, n=8, hub=0.34, hub_kind="rosette", scheme="oculus")
    _run_all(ds)
    return r


@register(NAME, "image_text", alts=3)
def _sg_image_text(k, slide, f, image):
    """The caller's picture glazed into an arched window: a border of jewel-coloured pieces round it, held in stone;
    the caption on the stone under the window, the kicker, title and body beside it (under it on a portrait or square
    page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    cap = text_of(f, "caption")
    rho = 0.62
    bw, fs = 0.14 * s, 0.14 * s
    edge = bw + fs
    if o == "land":
        ih = (0.80, 0.70, 0.60)[a] * H - 2 * m - (0.55 * s if cap else 0.0)
        iw = min(ih * 0.78, (0.36, 0.31, 0.26)[a] * W)
        ix, iy = m + edge + 0.15 * s, m + edge
    else:
        ih = (0.40, 0.32, 0.25)[a] * H
        iw = min(0.66 * W, ih * 0.92)
        ix, iy = (W - iw) / 2.0, m + edge
    groups = [(_v2.fields(f, ("kicker",), ("kicker",)), 0.12 * s), (_v2.fields(f, ("title",)), 0.18 * s),
              (_v2.fields(f, ("body",)), 0.0)]

    def plan(iy):
        r, ds = {}, []
        foot = iy + ih + edge
        if cap:
            cr, cd = _v2.flow(k, slide, "image_text", (ix - edge, foot + 0.22 * s, iw + 2 * edge, 1.0 * s),
                              [("caption", cap)], align="c")
            r.update(cr)
            ds.append(cd)
            foot = _foot(cr, foot)
        if o == "land":
            cx0 = ix + iw + edge + 0.70 * s
            tr, tds = _v2.stack(k, slide, "image_text", cx0, W - m - 0.10 * s - cx0, m, H - m, groups, anchor="middle")
        else:
            tr, tds = _v2.stack(k, slide, "image_text", m + 0.15 * s, W - 2 * m - 0.30 * s, foot + 0.35 * s, H - m,
                                groups, anchor="top", align="c")
        r.update(tr)
        return r, ds, tds
    r, ds, tds = plan(iy)
    if o != "land":                      # the window, its caption and the words as one block, its slack shared
        dy = max(0.0, ((H - m) - _foot(r, H - m)) * 0.42)
        if dy > 0.04 * s:
            iy += dy
            r, ds, tds = plan(iy)
    ys = iy + _apex_h(iw, rho)
    yb = iy + ih
    sur = na.poly(slide, _arch(ix, iw, ys, yb, rho, edge, n=30), fill=k.P["stone"], line=k.P["stone_edge"], line_w=0.6)
    _decl(sur, "the stone surround of the window the picture is glazed into: ornament, nothing to read")
    _glow(k, sur, 0.20 * s)
    if not _dark(k):
        na.soft_shadow(sur, blur=0.10 * s, dist=0.04 * s, alpha=0.20)
    G = _Glazing(k, slide, max(0.8, min(1.8, 1.2 * s)))
    L = 0.30 * s
    arc_len = rho * iw * 2.0
    pp = 3
    narc = max(2, int(round(arc_len / L))) * pp
    nj = max(1, int(round((yb - ys) / L)))
    ns = max(1, int(round(iw / L)))
    outer = _arch(ix, iw, ys, yb, rho, bw, n=narc, nj=nj, ns=ns)
    inner = _arch(ix, iw, ys, yb, rho, 0.0, n=narc, nj=nj, ns=ns)
    _band_pieces(G, outer, inner, _arch_bounds(nj, narc, ns, pp), ("ruby", "amber", "sapphire", "amber"), 1)
    G.draw()
    n0 = len(slide.shapes)
    vl._place_image(k, slide, image, (ix, iy, iw, ih), vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    for sh in list(slide.shapes)[n0:]:
        if sh.shape_type == 13:
            _mask_arch(sh, ix, iy, iw, ih, rho)
    rim = _outline(slide, [_arch(ix, iw, ys, yb, rho, 0.0, n=30)], k.P["lead"], max(1.2, 1.6 * s))
    _decl(rim, "the lead came round the picture's edge, where the glazed picture meets the border glass")
    _run_all(tds + ds)
    return r


def _mask_arch(pic, x, y, w, h, rho):
    """Clip a placed picture to the window's arch (a custom geometry on the picture itself)."""
    ys = y + _apex_h(w, rho)
    pts = _arch(x, w, ys, y + h, rho, 0.0, n=30)
    U = na.U
    u = [((px - x) / w * U, (py - y) / h * U) for px, py in pts]
    u = [(min(max(a, 0.0), U), min(max(b, 0.0), U)) for a, b in u]
    path = '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=U, d=na.orn._ring(u))
    spPr = pic._element.spPr
    old = spPr.find(qn("a:prstGeom"))
    if old is None:
        old = spPr.find(qn("a:custGeom"))
    g = dk.parse_xml('<a:custGeom xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:avLst/><a:gdLst/>'
                     '<a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/><a:pathLst>{}</a:pathLst></a:custGeom>'
                     .format(path))
    if old is not None:
        old.addprevious(g)
        spPr.remove(old)


@register(NAME, "closing", alts=3)
def _sg_closing(k, slide, f, image):
    """A single tall lancet with light falling through it: its glass pooled in colour on the floor below; the title
    and its line on the stone beside it (under it on a portrait page)."""
    W, H, s, o = ctx(k)
    m = _m(k)
    a = alt()
    side = o == "land" or H / W < 1.15
    groups = [(_v2.fields(f, ("title",)), 0.24 * s), (_v2.fields(f, ("line",)), 0.0)]
    start = None if a < 2 else {"title": 32 * s}
    if side:
        ww = min((0.155, 0.135, 0.12)[a] * W, (0.27, 0.24, 0.21)[a] * H)
        cxw = m + 0.30 * s + ww * 0.95
        wtop = m + 0.05 * s
        yb = H * 0.64
        x0 = cxw + ww * 0.5 + max(1.0 * s, ww * 0.95)
        r, ds = _v2.stack(k, slide, "closing", x0, W - m - 0.15 * s - x0, m, H - m, groups, anchor="middle",
                          align="l", start=start)
        pool = (yb + 0.30 * s, H - m)
    else:
        ww = min((0.26, 0.22, 0.19)[a] * W, 0.16 * H)
        cxw = W / 2.0
        yb = (0.44, 0.40, 0.36)[a] * H
        ph_ = min(0.13 * H, 1.4 * s)
        dy, r, ds = _below(k, slide, "closing", m + 0.05 * s, yb - m - 0.05 * s + 0.30 * s + ph_, 0.40 * s, groups,
                           start=start)
        wtop, yb = m + 0.05 * s + dy, yb + dy
        pool = (yb + 0.30 * s, yb + 0.30 * s + ph_)
    ys = wtop + _apex_h(ww, 1.0)
    straight = yb - ys
    nmed = max(1, min(3, int(straight / (ww * 1.15))))
    mr = ww * 0.34
    medals = [(ys + straight * (j + 0.5) / nmed, mr, "rosette") for j in range(nmed)]
    # the light: the window's own glass laid on the floor below it — foreshortened, sheared the way the light falls,
    # its apex farthest from the wall — soft-edged and pale on the stone, glowing on the night ground; a shaft of light
    # fading from the sill down to it
    gh = yb - wtop
    ph = min(pool[1] - pool[0], (1.35 if side else 1.4) * s)
    shear = 0.45 if side else 0.22
    spread = 1.22 if side else 1.45

    def to_floor(px, py):
        v = (yb - py) / gh
        return (cxw + (px - cxw) * spread + v * ph * shear, pool[0] + v * ph)
    dark = _dark(k)
    sh = na.poly(slide, [(cxw - ww * 0.50, yb + 0.14 * s), (cxw + ww * 0.50, yb + 0.14 * s)]
                 + [to_floor(cxw + ww / 2.0, wtop), to_floor(cxw - ww / 2.0, wtop)], fill=k.P["light"])
    _vgrad(sh, k.P["light"], 0.30 if dark else 0.34, 0.0)
    _decl(sh, "the shaft of light falling from the window to the floor: ornament, nothing to read")
    G, _ys = _lancet(k, slide, cxw - ww / 2.0, ww, wtop, yb, glass=("sapphire", "sapphire2"), trim=("amber", "ruby"),
                     medals=medals)
    pieces = {}
    for colour, poly in G.pieces():
        pieces.setdefault(colour, []).append([to_floor(px, py) for px, py in poly])
    for colour, polys in pieces.items():
        tint = k.P[colour] if dark else _mix(k.P[colour], "FFFFFF", 0.35)
        pool_sh = na.multipoly(slide, polys, tint, alpha=0.50 if dark else 0.62)
        _soft(pool_sh, 0.03 * s)
        _decl(pool_sh, "the window's colours pooled on the floor where its light falls: ornament, nothing to read")
    _run_all(ds)
    return r


def _mix(a, b, t):
    """`a` moved a share t of the way to `b` (hex colours)."""
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join("{:02X}".format(int(round(x + (y - x) * t))) for x, y in zip(ca, cb))


def _soft(sh, rad):
    """Soften a shape's edges by `rad` inches (a real softEdge effect): light on stone has no hard edge."""
    if sh is None:
        return
    sp = sh._element.spPr
    for e in sp.findall(qn("a:effectLst")):
        sp.remove(e)
    eff = dk.parse_xml('<a:effectLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                       '<a:softEdge rad="{}"/></a:effectLst>'.format(int(rad * 914400)))
    ln = sp.find(qn("a:ln"))
    if ln is not None:
        ln.addnext(eff)
    else:
        sp.append(eff)


def _vgrad(sh, color, a_top, a_bot):
    """Swap a shape's solid fill for a top-to-bottom fade of `color` from alpha a_top to a_bot."""
    if sh is None:
        return
    sp = sh._element.spPr
    sf = sp.find(qn("a:solidFill"))
    if sf is None:
        return
    c, a0, a1 = na.hexstr(color), int(a_top * 100000), int(a_bot * 100000)
    sf.addprevious(dk.parse_xml(
        '<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:srgbClr val="{c}"><a:alpha val="{a0}"/></a:srgbClr></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="{c}"><a:alpha val="{a1}"/></a:srgbClr></a:gs></a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/></a:gradFill>'.format(c=c, a0=a0, a1=a1)))
    sp.remove(sf)


# ─────────────────────────────────────────── ordinary pages ───────────────────────────────────────────
def _ground_stainedglass(slide, role, index):
    """An ordinary page (a chart, an agenda) on the plain stone: the content rect in REFERENCE inches."""
    W, H = vl.rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


_card_stainedglass = vl._card_for(NAME)
