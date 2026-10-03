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
    check(o.size == im.size, "the outline must not change the canvas size")
    check(o.getpixel((200, 250))[:3] == (30, 80, 200), "the subject must stay on top, unchanged")
    check(o.getpixel((200, 92))[3] == 255 and o.getpixel((200, 92))[:3] == (255, 255, 255),
          "a white border must appear just outside the subject")
    check(o.getpixel((5, 5))[3] == 0, "far outside the silhouette must stay transparent")
    # the border FOLLOWS the silhouette: beside the ellipse's waist it is white, at the frame's
    # corner region (outside the ellipse + border) it is still transparent
    check(o.getpixel((95, 250))[3] == 255, "the border must hug the side of the silhouette")
    check(o.getpixel((110, 110))[3] == 0, "the border must not square off the silhouette's corner")
    # default output path, and a colour given as a tuple
    out2 = image_fx.sticker_outline(str(src), color=(250, 220, 40))
    check(out2.endswith(".sticker.png") and Path(out2).exists(), "default out path")
    check(Image.open(out2).convert("RGBA").getpixel((200, 92))[:3] == (250, 220, 40), "tuple colour")
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

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_sticker_outline] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
