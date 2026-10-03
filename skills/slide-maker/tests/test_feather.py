#!/usr/bin/env python3
"""image_fx.feather: an illustration's edges fade into the paper ground (storybook); colour and existing alpha kept."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import image_fx
from PIL import Image
with tempfile.TemporaryDirectory() as td:
    src = Path(td) / "ill.png"
    Image.new("RGB", (400, 300), (200, 120, 80)).save(src)
    out = image_fx.feather(str(src))
    im = Image.open(out).convert("RGBA")
    check(out.endswith(".feather.png"), "default name")
    check(im.getpixel((0, 0))[3] < 20 and im.getpixel((399, 299))[3] < 20, "corners fade out")
    check(im.getpixel((200, 150))[3] == 255, "the centre stays opaque")
    check(im.getpixel((200, 150))[:3] == (200, 120, 80), "colour untouched")
    rgba = Path(td) / "a.png"
    Image.new("RGBA", (300, 300), (10, 20, 30, 128)).save(rgba)
    a2 = Image.open(image_fx.feather(str(rgba))).convert("RGBA")
    check(a2.getpixel((150, 150))[3] == 128, "existing alpha is multiplied, not replaced")
    for bad in (0, 0.5, -1):
        try:
            image_fx.feather(str(src), radius=bad)
            fails.append("radius {} accepted".format(bad))
        except ValueError:
            pass

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_feather] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
