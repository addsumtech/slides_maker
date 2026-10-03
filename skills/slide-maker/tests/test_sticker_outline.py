#!/usr/bin/env python3
"""sticker_outline: a die-cut border around a transparent cut-out, and a loud refusal otherwise.

The cut-paper and doodle registers put people and objects on the page as STICKERS: the subject,
its own outline in white, no rectangle. The border has to follow the subject's silhouette, so it is
made from the alpha channel. A photo with no transparency has no silhouette — outlining its frame
would hand back a white-bordered rectangle that looks like a working sticker, so it is refused.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import image_fx  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    src = td / "cut.png"
    im = Image.new("RGBA", (400, 500), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((100, 100, 300, 400), fill=(30, 80, 200, 255))
    im.save(src)
    out = image_fx.sticker_outline(str(src), str(td / "st.png"), border=0.05)
    o = Image.open(out).convert("RGBA")
    # the canvas grows by the border on every side (so a subject at an edge keeps its border);
    # every original pixel sits at (+d, +d)
    d = (o.size[0] - im.size[0]) // 2
    check(d > 0 and o.size == (im.size[0] + 2 * d, im.size[1] + 2 * d), "canvas must grow evenly")
    check(o.getpixel((200 + d, 250 + d))[:3] == (30, 80, 200), "the subject must stay on top, unchanged")
    check(o.getpixel((200 + d, 92 + d))[3] == 255 and o.getpixel((200 + d, 92 + d))[:3] == (255, 255, 255),
          "a white border must appear just outside the subject")
    check(o.getpixel((5, 5))[3] == 0, "far outside the silhouette must stay transparent")
    # the border FOLLOWS the silhouette: beside the ellipse's waist it is white, at the frame's
    # corner region (outside the ellipse + border) it is still transparent
    check(o.getpixel((95 + d, 250 + d))[3] == 255, "the border must hug the side of the silhouette")
    check(o.getpixel((110 + d, 110 + d))[3] == 0, "the border must not square off the silhouette's corner")
    # default output path, and a colour given as a tuple
    out2 = image_fx.sticker_outline(str(src), color=(250, 220, 40))
    check(out2.endswith(".sticker.png") and Path(out2).exists(), "default out path")
    o2 = Image.open(out2).convert("RGBA")
    d2 = (o2.size[0] - im.size[0]) // 2
    check(o2.getpixel((200 + d2, 92 + d2))[:3] == (250, 220, 40), "tuple colour")
    # a TIGHT cut-out (background-removal tools crop to the subject): the subject touches every
    # edge, so a same-size canvas has no room for the border. The canvas grows by the border.
    tight = td / "tight.png"
    ti = Image.new("RGBA", (300, 400), (0, 0, 0, 0))
    ImageDraw.Draw(ti).ellipse((0, 0, 299, 399), fill=(30, 80, 200, 255))
    ti.save(tight)
    to = Image.open(image_fx.sticker_outline(str(tight), str(td / "tight_st.png"), border=0.05)).convert("RGBA")
    pad_px = to.size[0] - 300
    check(pad_px > 0 and to.size == (300 + pad_px, 400 + pad_px),
          "a tight cut-out must get a canvas grown by the border on every side, got {}".format(to.size))
    check(to.getpixel((to.size[0] // 2, pad_px // 2 - 1))[3] == 255,
          "no border above a subject that touched the top edge")
    for bad in ("opaque.jpg", "opaque.png"):
        Image.new("RGB", (50, 50), (200, 10, 10)).save(td / bad)
        try:
            image_fx.sticker_outline(str(td / bad))
            fails.append("sticker_outline accepted an image with no cut-out: " + bad)
        except ValueError:
            pass
    full = td / "fullalpha.png"
    Image.new("RGBA", (50, 50), (10, 10, 10, 255)).save(full)
    try:
        image_fx.sticker_outline(str(full))
        fails.append("sticker_outline accepted an RGBA image that is fully opaque")
    except ValueError:
        pass


# ── deferred from the final review: a SPECK of transparency is not a cut-out ───────────────────
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    speck = Image.new("RGBA", (200, 200), (120, 140, 160, 255))
    speck.putpixel((0, 0), (0, 0, 0, 0))
    speck.save(td / "speck.png")
    rounded = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(rounded).rounded_rectangle((0, 0, 199, 199), radius=16, fill=(120, 140, 160, 255))
    rounded.save(td / "rounded.png")
    for nm in ("speck.png", "rounded.png"):
        try:
            image_fx.sticker_outline(str(td / nm))
            fails.append("sticker_outline accepted a photo that is essentially opaque: " + nm)
        except ValueError:
            pass

# ── generalisation probe (2026-10-03): inputs the first tests never tried ──────────────────────

with tempfile.TemporaryDirectory() as td:
    empty = Path(td) / "empty.png"
    Image.new("RGBA", (120, 120), (0, 0, 0, 0)).save(empty)
    try:
        image_fx.sticker_outline(str(empty))
        fails.append("sticker_outline accepted a fully transparent image (no subject to outline)")
    except ValueError as e:
        check("subject" in str(e), "the refusal should say there is no subject: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_sticker_outline] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
