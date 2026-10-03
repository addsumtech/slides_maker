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
    """A die-cut STICKER border around a transparent cut-out: the subject's own silhouette, grown by
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
