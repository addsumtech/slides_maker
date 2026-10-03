#!/usr/bin/env python3
"""image_fx — on-brand photo preprocessing so a dropped-in photo never fights the deck's palette.

A single saturated accent only reads as THE accent if the photography doesn't compete. So for the
risograph / brutalist / ink_wash / editorial-dark / museum presets, run stray colour photos through
`duotone()` (two-ink) or `grayscale()` first, then place with `deckkit.picture()`. Pillow-only.

    from image_fx import duotone, grayscale
    p = duotone("photo.jpg", "#111111", "#C8102E", out="photo_duo.png")     # ink + red (brutalist)
    p = grayscale("photo.jpg")                                              # forced B/W
    deckkit.picture(s, p, x, y, w, h, fit="cover")
"""
import os
from PIL import Image, ImageOps


def _hex(c):
    if isinstance(c, (tuple, list)):
        return tuple(c)
    s = str(c).lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def grayscale(src, out=None):
    """Forced grayscale (so colour photos don't compete with the deck's accent). Returns out path."""
    out = out or os.path.splitext(src)[0] + ".gray.png"
    Image.open(src).convert("L").convert("RGB").save(out)
    return out


def duotone(src, ink_shadow, ink_highlight, out=None, *, autocontrast=True, halftone=False, mid=None):
    """Two-ink DUOTONE: map shadows->`ink_shadow`, highlights->`ink_highlight` (hex strings or RGB
    tuples). The signature look of risograph / brutalist / newsprint / archival-museum photography —
    a single brand pair instead of full colour. `mid` adds a 3-stop midtone; `halftone=True` adds a
    1-bit dither screen (a coarse newsprint feel). Returns out path."""
    out = out or os.path.splitext(src)[0] + ".duo.png"
    g = Image.open(src).convert("L")
    if autocontrast:
        g = ImageOps.autocontrast(g, cutoff=1)
    if halftone:
        g = g.convert("1").convert("L")  # ordered dither -> 1-bit -> back to L
    kw = {"black": _hex(ink_shadow), "white": _hex(ink_highlight)}
    if mid is not None:
        kw.update(mid=_hex(mid), midpoint=128)
    ImageOps.colorize(g, **kw).convert("RGB").save(out)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Duotone / grayscale a photo to match the deck palette.")
    ap.add_argument("src")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--gray", action="store_true", help="forced grayscale")
    ap.add_argument("--shadow", default="#111111", help="duotone shadow hex")
    ap.add_argument("--highlight", default="#FFFFFF", help="duotone highlight hex")
    ap.add_argument("--halftone", action="store_true")
    a = ap.parse_args()
    p = grayscale(a.src, a.out) if a.gray else duotone(a.src, a.shadow, a.highlight, a.out, halftone=a.halftone)
    print("wrote", p)


def quiet_region(path, *, grid=4):
    """Find the CALMEST region of an image — where title text can sit without fighting linework.

    Splits the image into a grid x grid gride, scores each cell by local luminance variance
    (busy-ness), and greedily grows the best-scoring rectangle of cells. Returns
    (fx, fy, fw, fh, mean_lum) — fractional rect + 0-255 mean luminance, so the caller both
    PLACES the text and picks its ink (mean_lum > 150 -> dark ink, else light ink).

    This replaces eyeballing "the sky looks empty" with a measurement — the Tokyo cover's calm
    wedge was measured by hand-sampling bands; this is that probe, generalised. Since the skill
    GENERATES its imagery, the found region can also be fed back into the prompt ("keep the
    upper-left third calm").
    """
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L")
    W, H = im.size
    cw, ch = W // grid, H // grid
    scores = {}
    for gy in range(grid):
        for gx in range(grid):
            cell = im.crop((gx * cw, gy * ch, (gx + 1) * cw, (gy + 1) * ch))
            st = ImageStat.Stat(cell)
            scores[(gx, gy)] = (st.stddev[0], st.mean[0])
    # best single cell, then greedily absorb the calmer neighbour row/col while variance stays low
    best = min(scores, key=lambda k: scores[k][0])
    x0 = x1 = best[0]; y0 = y1 = best[1]
    # threshold: the best cell can be near-zero variance (flat cream), which made even a
    # smooth gradient sky fail the *2+6 bar and the region never grew. Anchor on the image's
    # own variance distribution instead: grow while a cell stays under the 40th percentile.
    ordered = sorted(v[0] for v in scores.values())
    thresh = max(scores[best][0] * 3.0 + 10.0, ordered[max(0, int(len(ordered) * 0.4) - 1)])
    grown = True
    while grown:
        grown = False
        for nx0, ny0, nx1, ny1 in ((x0 - 1, y0, x1, y1), (x0, y0, x1 + 1, y1),
                                   (x0, y0 - 1, x1, y1), (x0, y0, x1, y1 + 1)):
            if nx0 < 0 or ny0 < 0 or nx1 >= grid or ny1 >= grid or (nx0, ny0, nx1, ny1) == (x0, y0, x1, y1):
                continue
            cells = [(gx, gy) for gx in range(nx0, nx1 + 1) for gy in range(ny0, ny1 + 1)]
            # calm is not enough — the region must be ONE ink zone. A full-height column that
            # spans dark sky and cream ground averages to lum≈146, where NEITHER ink is safe.
            if (max(scores[c][0] for c in cells) <= thresh
                    and max(abs(scores[c][1] - scores[best][1]) for c in cells) <= 55):
                x0, y0, x1, y1 = nx0, ny0, nx1, ny1
                grown = True
                break
    cells = [(gx, gy) for gx in range(x0, x1 + 1) for gy in range(y0, y1 + 1)]
    lum = sum(scores[c][1] for c in cells) / len(cells)
    return (x0 / grid, y0 / grid, (x1 - x0 + 1) / grid, (y1 - y0 + 1) / grid, lum)


def sticker_outline(src, out=None, *, border=0.035, color="FFFFFF"):
    """A die-cut STICKER border around a transparent cut-out (cutout): the subject's own silhouette, grown by
    `border` (fraction of the shorter side) and filled with `color`, under the unchanged subject.
    Returns the out path (default `<src>.sticker.png`). Place it with `deckkit.picture(...,
    fit="contain")` — the transparency is the shape, so no mask is needed.

    The canvas GROWS by the border on every side (every original pixel moves by the same offset):
    background-removal tools crop tight to the subject, and on a same-size canvas a subject
    touching the edge got no border exactly at its head and feet (final review, 2026-10-03).

    The cut-paper / doodle registers put people and objects on the page as stickers; the border
    has to follow the silhouette, so it is built from the alpha channel (a blur-and-threshold
    dilation, which grows ROUND — a max-filter grows square and would square off every corner).

    RAISES ValueError for an image with no transparency — there is no silhouette to follow, and a
    white-bordered RECTANGLE would look like a working sticker. Cut the subject out first."""
    from PIL import ImageFilter
    im = Image.open(src)
    if im.mode not in ("RGBA", "LA", "PA") and "transparency" not in im.info:
        raise ValueError("sticker_outline(): {} has no alpha channel — nothing to outline; cut the "
                         "subject out first".format(src))
    im = im.convert("RGBA")
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] == 255:
        raise ValueError("sticker_outline(): {} is fully opaque — cut the subject out first"
                         .format(src))
    if sum(alpha.histogram()[25:]) == 0:
        raise ValueError("sticker_outline(): {} has no subject — every pixel is transparent, so "
                         "there is nothing to outline".format(src))
    # a SPECK of transparency (one stray pixel, a rounded-corner export) is still a rectangle;
    # a cut-out has a background removed — require a real share of transparent pixels
    _hist = alpha.histogram()
    _clear = sum(_hist[:25]) / float(im.size[0] * im.size[1])
    if _clear < 0.05:
        raise ValueError("sticker_outline(): only {:.1%} of {} is transparent — that is a photo "
                         "with a speck of transparency, not a cut-out; remove the background "
                         "first".format(_clear, src))
    px = max(1, int(round(border * min(im.size))))
    pad = px + 2                                     # room for the border wherever the subject is
    grown_im = Image.new("RGBA", (im.size[0] + 2 * pad, im.size[1] + 2 * pad), (0, 0, 0, 0))
    grown_im.paste(im, (pad, pad))
    im = grown_im
    alpha = im.getchannel("A")
    solid = alpha.point(lambda v: 255 if v > 24 else 0)
    grown = solid.filter(ImageFilter.GaussianBlur(px / 2.0)).point(lambda v: 255 if v > 6 else 0)
    rgb = _hex(color)
    base = Image.new("RGBA", im.size, tuple(rgb) + (0,))
    base.putalpha(grown)
    base.alpha_composite(im)
    out = out or os.path.splitext(src)[0] + ".sticker.png"
    base.save(out)
    return out


def _dilate(mask, k):
    """A boolean mask grown by a (2k+1)-square window — exactly PIL's MaxFilter(2k+1), in O(n) with
    running sums (MaxFilter(37) took ~20 s on a 4000x3000 image: 66 s per cut-out)."""
    import numpy as np
    m = np.asarray(mask, dtype=bool).astype(np.int32)
    c = np.cumsum(np.pad(m, ((0, 0), (k + 1, k))), axis=1)
    r = (c[:, 2 * k + 1:] - c[:, :-(2 * k + 1)]) > 0
    c = np.cumsum(np.pad(r.astype(np.int32), ((k + 1, k), (0, 0))), axis=0)
    return (c[2 * k + 1:, :] - c[:-(2 * k + 1), :]) > 0


def chroma_cutout(src, out=None, *, key=None, tol=60, min_subject=0.05):
    """Key a generated subject off a FLAT background colour (the series pipeline prompts for one).

    The background colour is estimated from the frame's outer ring; pixels within `tol/2` of it become
    transparent, a soft ramp to `tol` keeps the edge smooth, and the key colour's spill is pulled out of
    the edge pixels. Returns the out path (default `<src>.cut.png`).

    RAISES ValueError — never hands back a half-keyed image that looks like a working sticker — when the
    background is not FLAT (regenerate on a flatter background), when the subject touches the frame EDGE
    (regenerate with margin), or when less than `min_subject` of the frame is subject."""
    import numpy as np
    from PIL import ImageFilter
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    # Classify the border on a MEDIAN-FILTERED copy: grain/noise vanishes there, a subject crossing
    # the edge does not — that is what tells "not flat" from "touches the edge".
    sm = np.asarray(im.filter(ImageFilter.MedianFilter(5))).astype(np.float32)
    sides_sm = [sm[:2].reshape(-1, 3), sm[-2:].reshape(-1, 3), sm[:, :2].reshape(-1, 3), sm[:, -2:].reshape(-1, 3)]
    sides_raw = [a[:2].reshape(-1, 3), a[-2:].reshape(-1, 3), a[:, :2].reshape(-1, 3), a[:, -2:].reshape(-1, 3)]
    bg = np.median(np.concatenate(sides_sm), axis=0)
    if key:
        kh = str(key).lstrip("#").upper()
        kc = np.array([int(kh[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
        if float(np.linalg.norm(bg - kc)) > tol:
            raise ValueError("chroma_cutout(): the background of {} is #{:02X}{:02X}{:02X}, not the key colour #{} "
                             "asked for — regenerate it on the key. Keying another ground also removes the "
                             "subject's own matching colours (measured: a cut-out returned on cream paper lost "
                             "its cream highlights).".format(src, *(int(round(c)) for c in bg), kh))
    hit = [float((np.linalg.norm(sd - bg, axis=1) > tol * 0.5).mean()) > 0.02 for sd in sides_sm]
    if sum(hit) >= 3:
        raise ValueError("chroma_cutout(): the background of {} is not flat (a gradient or a subject that fills "
                         "the frame) — regenerate it on a flatter, uniform background with margin".format(src))
    clear = [sd for sd, h_ in zip(sides_raw, hit) if not h_]
    spread = float(np.percentile(np.linalg.norm(np.concatenate(clear) - bg, axis=1), 90))
    if spread > tol * 0.5:
        raise ValueError("chroma_cutout(): the background of {} is not flat (border spread {:.0f} > {:.0f}: "
                         "texture or noise) — regenerate it on a flatter, uniform background".format(
                             src, spread, tol * 0.5))
    if any(hit):
        raise ValueError("chroma_cutout(): the subject of {} touches the frame edge — regenerate it with "
                         "margin on every side".format(src))
    d = np.linalg.norm(a - bg, axis=2)
    alpha = np.clip((d - tol * 0.5) / (tol * 0.5), 0.0, 1.0)
    share = float((alpha > 0.5).mean())
    if share < min_subject:
        raise ValueError("chroma_cutout(): only {:.1%} of {} is subject after keying — no usable subject; "
                         "regenerate it larger".format(share, src))
    # The key must not EAT part of the subject. Measured (final review, 2026-10-03): green leaves on the
    # green key came back fully transparent while the pot kept the subject share up — "OK", leaves gone.
    # An eaten pixel is made (partly) transparent although its colour is clearly NOT the background
    # (farther from it than the background's own noise) and it lies away from the subject's soft edge.
    # A hole that IS the background (a handle's loop) is the key colour itself, so it does not count.
    # Two ways: (a) a clearly non-background pixel keyed fully away, off the subject's soft edge; (b) a
    # half-transparent pixel deep INSIDE the subject, far from the true background (pale-green leaves
    # came back at alpha 0.61 — visible, but see-through).
    kk = max(2, int(round(min(a.shape[:2]) * 0.006)))
    def _grow(mask):
        return _dilate(mask, kk)
    near_subject = _grow(alpha >= 0.5)
    near_clear = _grow(alpha < 0.02)
    gone = (alpha < 0.5) & (d >= max(15.0, spread + 8.0)) & ~near_subject
    see_through = (alpha > 0.02) & (alpha < 0.98) & ~near_clear
    eaten = gone | see_through
    subject_px = float((alpha >= 0.5).sum())
    if eaten.sum() > max(200, 0.02 * subject_px):
        other = "FF00FF" if int(np.argmax(bg)) == 1 else "00B140"
        raise ValueError("chroma_cutout(): keying {} also removed part of the SUBJECT ({:.0%} of it — colours "
                         "close to the key, e.g. green leaves on a green key). Regenerate it on the other key: "
                         "set the plan's \"chroma\" to {}.".format(src, eaten.sum() / subject_px, other))
    # despill: in an EDGE BAND, remove only the key's EXCESS — how far the weakest KEY channel (green; red
    # and blue for magenta) rises above the strongest other one — from every key channel. The band is
    # every visible pixel within a few px of the keyed-out region, not only the partly transparent ones:
    # the mixed subject/key pixels just inside a soft edge stay OPAQUE and still carry the key (measured:
    # a green outline on the first version). A pixel with no excess is the subject's own colour and is
    # left exactly as it is — capping each key channel AT the others instead turned a real orange pot rim
    # olive (191,164,95 -> 164,164,95). The interior is untouched either way.
    keys = [c for c in range(3) if bg[c] > 128] or [int(np.argmax(bg))]
    rest = [c for c in range(3) if c not in keys]
    k = max(2, int(round(min(a.shape[:2]) * 0.006)))
    edge_px = (alpha > 0) & _dilate(alpha < 1, k)
    if rest:
        excess = np.clip(a[..., keys].min(axis=2) - a[..., rest].max(axis=2), 0, None)
        excess = np.where(edge_px, excess, 0)
        for c in keys:
            a[..., c] = a[..., c] - excess
    rgba = np.dstack([a, alpha * 255.0]).clip(0, 255).astype(np.uint8)
    out = out or os.path.splitext(src)[0] + ".cut.png"
    Image.fromarray(rgba, "RGBA").save(out)
    return out


def feather(src, out=None, *, radius=0.08):
    """Fade an image's EDGES to transparent so an illustration melts into the paper ground (the
    storybook language). `radius` is a fraction of the short side. Existing alpha is multiplied, so a
    cut-out stays cut out. Returns the out path (default `<stem>.feather.png`)."""
    from PIL import ImageChops, ImageDraw, ImageFilter
    if not (0 < radius < 0.5):
        raise ValueError("feather(): radius must be in (0, 0.5) — a fraction of the short side, got {!r}".format(radius))
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    r = max(1, int(round(min(w, h) * radius)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((r, r, w - 1 - r, h - 1 - r), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(r * 0.6))
    im.putalpha(ImageChops.multiply(im.getchannel("A"), mask))
    out = out or os.path.splitext(src)[0] + ".feather.png"
    im.save(out)
    return out
