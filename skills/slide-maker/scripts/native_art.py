#!/usr/bin/env python3
"""native_art — the drawn surfaces of the four NATIVE visual languages (ink, poster, cutpaper, blueprint):
native, editable shapes, deterministic for a seed, and ON THE PAGE by construction.

Two rules every function keeps, both found on the 2026-10-05 look-dev deck, which LibreOffice rendered and
PowerPoint did not open cleanly:
  · nothing is drawn past the slide edge. PowerPoint's editing view shows geometry beyond the slide, so a
    bleed is computed up to the edge (clip_to_page, band) — never left for the renderer to clip;
  · every angle written is in range. A negative outerShdw `dir` made PowerPoint repair the file (angle()).

    import native_art as na
    na.ink_ridges(s, color="1D1C1A", layers=na.INK_LAYERS["land"], keep_clear=[(9.6, 0.7, 1.2, 4.9)])
"""
from __future__ import annotations

import math
import random
import tempfile
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

import deckkit as dk
import ornaments as orn

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
U = 100000

# ridge layers, far to near: (crest base / H, peak height / H, top alpha, depth / H)
INK_LAYERS = {
    "land": ((0.57, 0.25, 0.34, 0.32), (0.67, 0.20, 0.46, 0.30), (0.77, 0.15, 0.62, 0.25), (0.89, 0.09, 0.80, 0.21)),
    "port": ((0.66, 0.12, 0.34, 0.20), (0.73, 0.10, 0.46, 0.18), (0.81, 0.08, 0.62, 0.15), (0.90, 0.05, 0.80, 0.11)),
    "faint": ((0.86, 0.10, 0.18, 0.16), (0.93, 0.06, 0.30, 0.10)),
}


def page_size(slide):
    pres = slide.part.package.presentation_part.presentation
    return pres.slide_width / 914400.0, pres.slide_height / 914400.0


def hexstr(c):
    if isinstance(c, str):
        return c.lstrip("#").upper()
    return "{:02X}{:02X}{:02X}".format(*c)


def _pct(v):
    return int(round(min(max(float(v), 0.0), 1.0) * 100000))


def angle(deg):
    """An OOXML angle (60000ths of a degree), always in 0..21599999 — PowerPoint repairs a negative one."""
    return int(round((float(deg) % 360.0) * 60000)) % 21600000


def clip_to_page(pts, W, H):
    """Sutherland-Hodgman: the polygon `pts` (inches) cut to the page rectangle [0, W] x [0, H]."""
    def clip(poly, inside, cross):
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))

    def at_y(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / (b[1] - a[1]), yv)

    pts = [tuple(p) for p in pts]
    for inside, cross in ((lambda p: p[0] >= 0.0, at_x(0.0)), (lambda p: p[0] <= W, at_x(W)),
                          (lambda p: p[1] >= 0.0, at_y(0.0)), (lambda p: p[1] <= H, at_y(H))):
        if not pts:
            break
        pts = clip(pts, inside, cross)
    return pts


def _custom(slide, x, y, w, h, path_xml, *, fill=None, alpha=None, line=None, line_w=1.0):
    return orn._shape(slide, x, y, w, h, path_xml, fill=fill, alpha=alpha, line=line, line_w=line_w)


def poly(slide, pts, *, fill=None, alpha=None, line=None, line_w=0.75):
    """A straight-edged polygon, clipped to the page; None when nothing of it is on the page."""
    W, H = page_size(slide)
    pts = clip_to_page(pts, W, H)
    if len(pts) < 3:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    w, h = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
    u = [((px - x0) / w * U, (py - y0) / h * U) for px, py in pts]
    path = '<a:path w="{u}" h="{u}"{f}>{d}</a:path>'.format(u=U, d=orn._ring(u),
                                                            f="" if fill is not None else ' fill="none"')
    return _custom(slide, x0, y0, w, h, path, fill=None if fill is None else hexstr(fill), alpha=alpha,
                   line=line, line_w=line_w)


def band(slide, top_pts, bottom_y, *, fill, alpha=None):
    """A band whose top edge is a smooth curve through `top_pts` and whose foot is flat — x clamped to the page,
    the foot to the page bottom, so a bleed reaches the edge and stops there."""
    W, H = page_size(slide)
    pts = [(min(max(px, 0.0), W), py) for px, py in top_pts]
    bottom_y = min(bottom_y, H)
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0 = max(0.0, min(min(p[1] for p in pts), bottom_y - 0.02))
    w, h = max(x1 - x0, 0.01), max(bottom_y - y0, 0.01)
    u = [((px - x0) / w * U, (max(py, y0) - y0) / h * U) for px, py in pts]
    d = "<a:moveTo>{}</a:moveTo>{}<a:lnTo>{}</a:lnTo><a:lnTo>{}</a:lnTo><a:close/>".format(
        orn._pt(*u[0]), orn._smooth(u), orn._pt(U, U), orn._pt(0, U))
    return _custom(slide, x0, y0, w, h, '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=U, d=d),
                   fill=hexstr(fill), alpha=alpha)


def fade(shape, color, top, mid=None, stop=55):
    """Swap a solid fill for a vertical transparency gradient: `top` alpha at the crest, mist at the foot."""
    sp = shape._element.spPr
    sf = sp.find(qn("a:solidFill"))
    if sf is None:
        raise ValueError("fade(): the shape has no solid fill to fade")
    mid = top * 0.35 if mid is None else mid
    g = etree.fromstring(
        '<a:gradFill xmlns:a="{a}" rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:srgbClr val="{c}"><a:alpha val="{t}"/></a:srgbClr></a:gs>'
        '<a:gs pos="{p}"><a:srgbClr val="{c}"><a:alpha val="{m}"/></a:srgbClr></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="{c}"><a:alpha val="0"/></a:srgbClr></a:gs></a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/></a:gradFill>'.format(
            a=A_NS, c=hexstr(color), t=_pct(top), m=_pct(mid), p=int(min(max(stop, 1), 99)) * 1000))
    sf.addprevious(g)
    sp.remove(sf)
    return shape


def soft_shadow(shape, *, blur=0.10, dist=0.04, alpha=0.25, color="2A1E10", direction=90.0):
    """A soft paper shadow (a real outerShdw), its angle normalised into range, placed in schema order."""
    sp = shape._element.spPr
    for e in sp.findall(qn("a:effectLst")):
        sp.remove(e)
    eff = etree.fromstring(
        '<a:effectLst xmlns:a="{a}"><a:outerShdw blurRad="{b}" dist="{d}" dir="{r}" algn="t" rotWithShape="0">'
        '<a:srgbClr val="{c}"><a:alpha val="{al}"/></a:srgbClr></a:outerShdw></a:effectLst>'.format(
            a=A_NS, b=int(abs(blur) * 914400), d=int(abs(dist) * 914400), r=angle(direction), c=hexstr(color),
            al=_pct(alpha)))
    ln = sp.find(qn("a:ln"))
    if ln is not None:
        ln.addnext(eff)
    else:
        sp.append(eff)
    return shape


def disc(slide, cx, cy, d, fill, *, shadow=False):
    b = dk.box(slide, cx - d / 2.0, cy - d / 2.0, d, d, fill=hexstr(fill))
    b._element.spPr.find(qn("a:prstGeom")).set("prst", "ellipse")
    return soft_shadow(b, blur=0.12, dist=0.05, alpha=0.24) if shadow else b


def seg(slide, x0, y0, x1, y1, color, *, w=0.75, dash=False, alpha=None):
    W, H = page_size(slide)
    cl = lambda v, hi: min(max(v, 0.0), hi)            # noqa: E731
    c = dk._connector(slide, cl(x0, W), cl(y0, H), cl(x1, W), cl(y1, H), dk._as_rgb(hexstr(color)), w=w, dash=dash)
    if alpha is not None:
        clr = c._element.spPr.find(qn("a:ln")).find(qn("a:solidFill"))[0]
        clr.append(clr.makeelement(qn("a:alpha"), {"val": str(_pct(alpha))}))
    return c


def no_autofit(tb):
    """A measured box keeps its size: PowerPoint re-runs spAutoFit on vertical text differently from LibreOffice."""
    bp = tb.text_frame._txBody.find(qn("a:bodyPr"))
    for e in list(bp):
        if e.tag in (qn("a:spAutoFit"), qn("a:normAutofit"), qn("a:noAutofit")):
            bp.remove(e)
    bp.insert(0, bp.makeelement(qn("a:noAutofit"), {}))
    return tb


def vertical(tb):
    """CJK set upright, top to bottom, columns right to left."""
    tb.text_frame._txBody.find(qn("a:bodyPr")).set("vert", "eaVert")
    return no_autofit(tb)


def _bg(slide, fill_xml):
    csld = slide._element.find(qn("p:cSld"))
    for old in csld.findall(qn("p:bg")):
        csld.remove(old)
    csld.insert(0, etree.fromstring('<p:bg xmlns:p="{p}" xmlns:a="{a}" xmlns:r="{r}"><p:bgPr>{f}<a:effectLst/>'
                                    '</p:bgPr></p:bg>'.format(p=P_NS, a=A_NS, r=R_NS, f=fill_xml)))


def solid_background(slide, color):
    _bg(slide, '<a:solidFill><a:srgbClr val="{}"/></a:solidFill>'.format(hexstr(color)))


def grid_background(slide, *, base, ink, step=0.25, major=4, dpi=150):
    """A drafting grid as the slide background — one picture per canvas and colour, cached, never a shape."""
    from PIL import Image, ImageDraw
    W, H = page_size(slide)
    path = Path(tempfile.gettempdir()) / "slide-maker-native-art" / "grid_{}_{}_{:.3f}x{:.3f}.png".format(
        hexstr(base), hexstr(ink), W, H)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pw, ph = int(W * dpi), int(H * dpi)
        b = tuple(int(hexstr(base)[i:i + 2], 16) for i in (0, 2, 4))
        k = tuple(int(hexstr(ink)[i:i + 2], 16) for i in (0, 2, 4))
        mix = lambda a: tuple(int(b[i] * (1 - a) + k[i] * a) for i in range(3))  # noqa: E731
        im = Image.new("RGB", (pw, ph), b)
        dr = ImageDraw.Draw(im)
        px = dpi * step
        for i in range(int(pw / px) + 1):
            dr.line([(int(i * px), 0), (int(i * px), ph)], fill=mix(0.13 if i % major == 0 else 0.055), width=1)
        for j in range(int(ph / px) + 1):
            dr.line([(0, int(j * px)), (pw, int(j * px))], fill=mix(0.13 if j % major == 0 else 0.055), width=1)
        im.save(str(path))
    _part, rid = slide.part.get_or_add_image_part(str(path))
    _bg(slide, '<a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{}"/><a:srcRect/><a:stretch><a:fillRect/>'
               '</a:stretch></a:blipFill>'.format(rid))
    return str(path)


SHOULDER = 1.6      # how steeply (in/in) a ridge falls away beside kept-clear text: a hillside, not a cut


def ridge_points(W, H, layer, i, seed, peak_span, keep_clear):
    """The crest of ridge layer `i` as 41 (x, y) points. Over a keep_clear rect the crest sits below the rect's
    foot; beside it the crest is held down by a SHOULDER that relaxes with distance — measured 2026-10-05, a flat
    clamp left a vertical cut in the ridge at the rect's edge."""
    bf, af, _top_alpha, _df = layer
    rnd = random.Random(seed * 31 + i)
    base, amp = bf * H, af * H
    lo, hi = peak_span[0] * W, peak_span[1] * W
    centers = [(rnd.uniform(lo, hi), rnd.uniform(0.45, 1.0) * amp, rnd.uniform(0.06, 0.16) * W) for _ in range(4)]
    pts = []
    for j in range(41):
        x = W * j / 40.0
        hgt = 0.12 * amp * (1 + math.sin(x / W * 12.0 + seed + i)) / 2.0
        for cx, a, sp in centers:
            hgt = max(hgt, a * math.exp(-((x - cx) / sp) ** 2 * 2.2) * (1 + 0.08 * math.sin(x * 9 + seed)))
        y = base - hgt
        for kx, ky, kw, kh in keep_clear:
            d = max(kx - 0.25 - x, 0.0, x - (kx + kw + 0.25))      # how far outside the kept span
            y = max(y, ky + kh + 0.15 - SHOULDER * d)
        pts.append((x, y))
    return pts


def ink_ridges(slide, *, color, layers, seed=0, peak_span=(0.0, 0.62), keep_clear=()):
    """Ink-wash ridges, far to near, each fading from its crest into mist. Peaks rise only inside `peak_span`
    (fractions of W); over every `keep_clear` rect the crest stays below the rect's foot — text never sits on
    the wash. Declared decorative: the language's ground, like paper grain."""
    W, H = page_size(slide)
    out = []
    for i, layer in enumerate(layers):
        bf, _af, top_alpha, df = layer
        pts = ridge_points(W, H, layer, i, seed, peak_span, keep_clear)
        sh = band(slide, pts, bf * H + df * H, fill=color)
        fade(sh, color, top_alpha)
        dk.decorative(sh, "an ink-wash ridge: the language's ground, like paper grain")
        out.append(sh)
    return out


def seal(slide, x, y, size, chars, *, fill, ink, face):
    """A carved seal carrying ONE or TWO characters of the caller's own text (never invented)."""
    chars = (chars or "").strip()
    if not 1 <= len(chars) <= 2:
        raise ValueError("seal(): one or two characters from the caller's own text, got {!r}".format(chars))
    rnd = random.Random(sum(map(ord, chars)))
    j = lambda: rnd.uniform(-0.035, 0.035) * size     # noqa: E731 — a carved stone's edge is never straight
    pts = [(x + j(), y + j()), (x + size / 2, y + j() * 0.6), (x + size + j(), y + j()),
           (x + size + j(), y + size / 2), (x + size + j(), y + size + j()), (x + size / 2, y + size + j() * 0.6),
           (x + j(), y + size + j()), (x + j() * 0.6, y + size / 2)]
    body = poly(slide, pts, fill=fill, alpha=0.94)
    pt = size * 72 * (0.40 if len(chars) == 2 else 0.60)
    tb = dk.text(slide, x, y, size, size, [[(chars, pt, dk._as_rgb(hexstr(ink)), True, False, face, face)]],
                 align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    (vertical if len(chars) == 2 else no_autofit)(tb)
    dk.overlap_intent(tb, "the seal's characters are carved into the seal")
    return [body, tb]


def enso(slide, cx, cy, R, width, *, color, seed=3, gap=38.0, start=110.0, alpha=0.9):
    """An open ensō brush circle: thick where the brush lands, dry and thin where it lifts."""
    rnd = random.Random(seed)
    n, sweep = 120, 360.0 - gap
    outer, inner = [], []
    for i in range(n + 1):
        t = i / float(n)
        a = math.radians(start + sweep * t)
        wob = 0.012 * R * math.sin(t * 23 + seed) + 0.01 * R * (rnd.random() - 0.5)
        w = width * (0.25 + 0.75 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6) * (1 - 0.55 * t ** 3)
        outer.append((cx + (R + wob) * math.cos(a), cy + (R + wob) * math.sin(a)))
        inner.append((cx + (R + wob - w) * math.cos(a), cy + (R + wob - w) * math.sin(a)))
    sh = poly(slide, outer + inner[::-1], fill=color, alpha=alpha)
    dk.decorative(sh, "an ensō brush circle around the figure; ornament")
    return sh


def hill_points(W, base, amp, seed, waves):
    ph = random.Random(seed).uniform(0.0, 6.28)
    return [(W * i / 16.0, base - amp * (0.55 + 0.45 * math.sin(ph + waves * 6.28318 * i / 16.0))) for i in range(17)]


def paper_hill(slide, pts, bottom_y, *, fill, shadow=True):
    sh = band(slide, pts, bottom_y, fill=fill)
    if shadow:
        soft_shadow(sh, blur=0.14, dist=0.05, alpha=0.22, direction=270.0)
    dk.decorative(sh, "a cut-paper hill: the language's ground")
    return sh


def paper_card(slide, x, y, w, h, *, fill="FFFFFF", r=0.22, rotation=0.0):
    c = dk.box(slide, x, y, w, h, fill=hexstr(fill), round=True, r=r)
    if rotation:
        c.rotation = float(rotation)
    return soft_shadow(c, blur=0.16, dist=0.06, alpha=0.24)


def cloud(slide, cx, cy, w, *, fill="FFFFFF"):
    pts = []
    for i in range(14):
        a = 6.28318 * i / 14
        r = 1 + 0.18 * math.sin(a * 3) + 0.08 * math.sin(a * 5)
        pts.append((cx + math.cos(a) * w / 2 * r, cy + math.sin(a) * w / 5.5 * r))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0, ww, hh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    u = [((px - x0) / ww * U, (py - y0) / hh * U) for px, py in pts]
    d = "<a:moveTo>{}</a:moveTo>{}<a:close/>".format(orn._pt(*u[0]), orn._smooth(u, closed=True))
    sh = _custom(slide, x0, y0, ww, hh, '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=U, d=d), fill=hexstr(fill))
    soft_shadow(sh, blur=0.08, dist=0.04, alpha=0.18)
    dk.decorative(sh, "a paper cloud: the cut-paper ground")
    return sh


def paper_sun(slide, cx, cy, diameters, colors):
    out = []
    for d, col in zip(diameters, colors):
        sh = disc(slide, cx, cy, d, col, shadow=True)
        dk.decorative(sh, "a layered paper sun")
        out.append(sh)
    return out


def drawing_sheet(slide, *, ink, mute, accent, number, project, face):
    """A drawing sheet's furniture: double border, zone marks, and a title block holding only the sheet number
    and the caller's own project words. Returns (content rect, title-block rect)."""
    W, H = page_size(slide)
    s = min(W, H) / 7.5
    m1, m2 = 0.32 * s, 0.42 * s
    rgb = lambda c: dk._as_rgb(hexstr(c))              # noqa: E731
    dk.box(slide, m1, m1, W - 2 * m1, H - 2 * m1, line=rgb(ink), line_w=1.0)
    dk.box(slide, m2, m2, W - 2 * m2, H - 2 * m2, line=rgb(ink), line_w=0.5)
    zpt = max(8.0, 8.0 * s)
    nx, ny = max(2, int(round(W / 2.2))), max(2, int(round(H / 1.9)))
    for i in range(nx):
        dk.text(slide, m2 + (W - 2 * m2) * (i + 0.5) / nx - 0.15, 0.03 * s, 0.3, m1 - 0.04 * s,
                [[(str(i + 1), zpt, rgb(mute), False, False, face)]], align=dk.PP_ALIGN.CENTER,
                anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    for j in range(min(ny, 8)):
        dk.text(slide, 0.02 * s, m2 + (H - 2 * m2) * (j + 0.5) / ny - 0.12, m1 - 0.04 * s, 0.24,
                [[("ABCDEFGH"[j], zpt, rgb(mute), False, False, face)]], align=dk.PP_ALIGN.CENTER,
                anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    bw, bh = min(3.9 * s, W * 0.36), 0.9 * s
    bx, by = W - m2 - 0.12 * s - bw, H - m2 - 0.12 * s - bh
    dk.box(slide, bx, by, bw, bh, line=rgb(ink), line_w=0.75)
    split = bx + bw * 0.66
    seg(slide, split, by, split, by + bh, ink, w=0.5)
    lab = max(8.0, 8.0 * s)
    if project:
        title_block_project(slide, (bx, by, bw, bh), project, ink=ink, mute=mute, face=face)
    dk.text(slide, split + 0.08 * s, by + 0.06 * s, bx + bw - split - 0.14 * s, bh - 0.12 * s,
            [[("SHEET", lab, rgb(mute), False, False, face)],
             [("{:02d}".format(number), max(14.0, 16.0 * s), rgb(accent), True, False, face)]], space_after=0)
    return (0.9 * s, 0.78 * s, W - 1.8 * s, H - 1.56 * s), (bx, by, bw, bh)


def title_block_project(slide, block, project, *, ink, mute, face):
    """The caller's project words in a drawing sheet's title block (left field), measured: 10pt shrinking to 7pt.
    Returns False and draws NOTHING when they do not fit even then — the caller decides (refuse the caller's own
    project=, or leave a remembered title out: the sheet number alone)."""
    W, H = page_size(slide)
    s = min(W, H) / 7.5
    bx, by, bw, bh = block
    split = bx + bw * 0.66
    fw, fh = split - bx - 0.14 * s, bh - 0.12 * s
    rgb = lambda c: dk._as_rgb(hexstr(c))              # noqa: E731
    lab = max(8.0, 8.0 * s)
    lab_h = dk.measure_text([("PROJECT", False)], fw, lab, font=face, line_h_factor=dk._LINT_LINE_H)   # lint's model
    sz = max(9.0, 10.0 * s)
    while True:
        need = lab_h + dk.measure_text([(str(project), True)], fw, sz, font=face, line_h_factor=dk._LINT_LINE_H)
        if need <= fh or sz <= 7.0:
            break
        sz = max(7.0, sz - 0.5)
    if need > fh + 1e-6:
        return False
    dk.text(slide, bx + 0.08 * s, by + 0.06 * s, fw, fh,
            [[("PROJECT", lab, rgb(mute), False, False, face)],
             [(str(project), sz, rgb(ink), True, False, face, face)]], space_after=0)
    return True


def _iso(cx, cy, a, b):
    return (cx + (a - b) * 0.866, cy + (a + b) * 0.5)


def iso_stack(slide, cx, cy, size, gap, n, *, ink, accent=None, accent_layer=None, thick=0.18):
    """`n` isometric layers (one per point of the page — never a generic diagram), top layer first; the layer at
    `accent_layer` is filled with `accent`. Returns each layer's top rhombus corners (top, right, bottom, left)."""
    tops = []
    for k_ in range(n):
        y = cy + k_ * gap
        p = [_iso(cx, y, 0, 0), _iso(cx, y, size, 0), _iso(cx, y, size, size), _iso(cx, y, 0, size)]
        if accent is not None and accent_layer == k_:
            poly(slide, p, fill=accent, alpha=0.9)
        poly(slide, p, line=dk._as_rgb(hexstr(ink)), line_w=1.0)
        poly(slide, [p[3], p[2], (p[2][0], p[2][1] + thick), (p[3][0], p[3][1] + thick)], line=dk._as_rgb(hexstr(ink)), line_w=1.0)
        poly(slide, [p[2], p[1], (p[1][0], p[1][1] + thick), (p[2][0], p[2][1] + thick)], line=dk._as_rgb(hexstr(ink)), line_w=1.0)
        tops.append(p)
    if n > 1:
        for corner in (0, 1, 3):
            x, y = tops[0][corner]
            seg(slide, x, y, x, tops[-1][corner][1], ink, w=0.5, dash=True, alpha=0.7)
    return tops


def dimension_line(slide, x, y0, y1, *, ink):
    out = [seg(slide, x, y0, x, y1, ink, w=0.6)]
    for y in (y0, y1):
        out.append(seg(slide, x - 0.09, y + 0.09, x + 0.09, y - 0.09, ink, w=0.9))
        out.append(seg(slide, x - 0.16, y, x + 0.16, y, ink, w=0.4))
    return out


def balloon(slide, x, y, d, label, *, ink, accent, face, fill):
    b = dk.box(slide, x, y, d, d, fill=hexstr(fill), line=dk._as_rgb(hexstr(ink)), line_w=0.9)
    b._element.spPr.find(qn("a:prstGeom")).set("prst", "ellipse")
    tb = dk.text(slide, x, y, d, d, [[(str(label), max(10.0, d * 72 * 0.40), dk._as_rgb(hexstr(accent)), True, False, face)]],
                 align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    no_autofit(tb)
    dk.overlap_intent(tb, "a numbered balloon: the number sits inside its circle")
    return [b, tb]


def clipped_block(slide, x, y, w, h, deg, *, fill):
    """A rotated colour block drawn as its polygon cut to the page (a rotated rectangle would hang off it)."""
    cx, cy, a = x + w / 2.0, y + h / 2.0, math.radians(deg)
    corners = [(cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))
               for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    sh = poly(slide, corners, fill=fill)
    if sh is not None:
        dk.decorative(sh, "a poster colour block: the language's ground")
    return sh
