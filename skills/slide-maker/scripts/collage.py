#!/usr/bin/env python3
"""collage — 1-4 images as tilted, white-bordered prints held by tape, overlapping a little, inside a
region, never entering a rect kept clear for text. Deterministic for a seed.

The geometry is decided FIRST and drawn after: each print's painted polygon must stay out of
`keep_clear`, and two prints may cover at most MAX_COVER of the smaller one — a photo hidden under its
neighbour says nothing (measured, 2026-10-03: a portrait 3-print stack hid 54% of the first photo while
every test passed). Every print is declared `overlap_intent` so the overlap gates read it as designed.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import deckkit as dk  # noqa: E402
import rotgeom  # noqa: E402

MAX_COVER = 0.25      # the most of the smaller print another print may cover
GROW = 1.12           # a print is ~12% larger than its cell, so neighbours overlap a little
MIN_SIDE = 0.9        # inches — below this a print is a thumbnail, not a print


def _cells(region, n):
    """Cells for n prints. Wide-ish regions: a row of 2, or 2 over 1 centred, or 2x2. Tall regions:
    a column of 2, or a zig-zag of 3 rows (left, right, left), or 2x2."""
    x, y, w, h = region
    tall = h > w * 1.25
    if n == 1:
        return [region]
    if n == 2:
        return ([(x, y, w, h / 2.0), (x, y + h / 2.0, w, h / 2.0)] if tall else
                [(x, y, w / 2.0, h), (x + w / 2.0, y, w / 2.0, h)])
    if n == 3:
        if tall:
            cw, ch = w * 0.72, h / 3.0
            return [(x, y, cw, ch), (x + w - cw, y + ch, cw, ch), (x, y + 2 * ch, cw, ch)]
        cw, ch = w / 2.0, h / 2.0
        return [(x, y, cw, ch), (x + cw, y, cw, ch), (x + (w - cw) / 2.0, y + ch, cw, ch)]
    cw, ch = w / 2.0, h / 2.0
    return [(x + c * cw, y + r * ch, cw, ch) for r in range(2) for c in range(2)]


def _geometry(region, n, rnd, keep_clear, max_tilt):
    cells = _cells(region, n)
    rots = [round(rnd.uniform(-max_tilt, max_tilt), 1) for _ in range(n)]
    scale = GROW
    for _attempt in range(12):
        boxes = []
        for (cx, cy, cw, ch) in cells:
            pw, ph = min(cw * scale, region[2]), min(ch * scale, region[3])
            px = min(max(cx + (cw - pw) / 2.0, region[0]), region[0] + region[2] - pw)
            py = min(max(cy + (ch - ph) / 2.0, region[1]), region[1] + region[3] - ph)
            boxes.append((px, py, pw, ph))
        if min(min(b[2], b[3]) for b in boxes) < MIN_SIDE:
            raise ValueError("collage(): region {} is too small for {} prints (a print side < {}in)"
                             .format(tuple(round(v, 2) for v in region), n, MIN_SIDE))
        polys = [rotgeom.corners(*b, r) for b, r in zip(boxes, rots)]
        clear_ok = keep_clear is None or all(
            rotgeom.overlap(p, rotgeom.rect_poly(*keep_clear))[0] < 1e-6 for p in polys)
        cover_ok = all(rotgeom.overlap(polys[a], polys[b])[0]
                       <= MAX_COVER * min(rotgeom.area(polys[a]), rotgeom.area(polys[b])) + 1e-9
                       for a in range(n) for b in range(a + 1, n))
        if clear_ok and cover_ok:
            return boxes, rots
        scale *= 0.94                                   # shrink toward the cells' centres and retry
    raise ValueError("collage(): cannot place {} prints in {} without covering a print by more than {:.0%} or "
                     "entering keep_clear {} — enlarge the region or use fewer images"
                     .format(n, tuple(round(v, 2) for v in region), MAX_COVER, keep_clear))


def collage(slide, region, items, *, seed=0, keep_clear=None, tape=True, border=0.07, max_tilt=6.0):
    """Place 1-4 images as prints in `region` (x, y, w, h). Each item is a path, or a dict with "path"
    and "alt", or a dict with "slot", "plan" and "image_dir" (placed through image_series.slot_picture,
    so the image-series tag is kept). Returns the picture shapes."""
    import ornaments
    if not (1 <= len(items) <= 4):
        raise ValueError("collage(): 1-4 items, got {}".format(len(items)))
    rnd = random.Random(seed)
    boxes, rots = _geometry(region, len(items), rnd, keep_clear, max_tilt)
    out = []
    for i, (it, (px, py, pw, ph), rot) in enumerate(zip(items, boxes, rots)):
        it = {"path": it} if isinstance(it, str) else dict(it)
        frame = dk.box(slide, px, py, pw, ph, fill="FFFFFF")
        frame.rotation = rot
        dk.overlap_intent(frame, "a print's white border under its own photo")
        b = border * min(pw, ph)
        if it.get("slot"):
            import image_series as ims
            pic = ims.slot_picture(slide, it["plan"], it["slot"], px + b, py + b, pw - 2 * b, ph - 2 * b,
                                   image_dir=it["image_dir"])
        else:
            pic = dk.picture(slide, it["path"], px + b, py + b, pw - 2 * b, ph - 2 * b, fit="cover",
                             alt=it.get("alt") or "photograph")
        pic.rotation = rot
        dk.overlap_intent(pic, "a collage print overlapping its neighbour by design")
        if tape and i % 2 == 0:                     # a strip across the print's top edge, held by the print
            tw, th = pw * 0.34, min(0.32, ph * 0.16)
            t_ = ornaments.tape(slide, px + (pw - tw) / 2.0, py - th * 0.45, tw, th, "EDE3C8",
                                rotation=rot - 3.0, seed=seed + i, holds=frame)
            # a pale washi strip on the white border is 1.28:1 — NON-TEXT CONTRAST, which holds the hand-off;
            # it carries nothing, so say so (the print it holds is the content)
            dk.decorative(t_, "washi tape holding a print; ornament, nothing rides on seeing it")
        out.append(pic)
    return out
