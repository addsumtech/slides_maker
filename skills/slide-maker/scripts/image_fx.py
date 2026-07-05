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
