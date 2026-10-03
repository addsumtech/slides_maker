#!/usr/bin/env python3
"""chroma_cutout: key a generated subject off its flat background — or refuse, loudly.

The series pipeline asks for cut-out subjects "on a perfectly flat #00B140 background" and keys the
background away with Pillow (no new dependency: the user's choice). A key that half-works is worse than
none — a green fringe or a bitten subject looks like a working sticker — so a background that is not
flat, a subject that touches the frame edge, or a key that leaves almost nothing is REFUSED.
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


def scene(bg, fg, box=(60, 50, 240, 250), size=(300, 300), noise=0):
    import random
    im = Image.new("RGB", size, bg)
    if noise:
        rnd = random.Random(1)
        px = im.load()
        for x in range(size[0]):
            for y in range(size[1]):
                n = rnd.randint(-noise, noise)
                px[x, y] = tuple(max(0, min(255, c + n)) for c in bg)
    ImageDraw.Draw(im).ellipse(box, fill=fg)
    return im


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # clean green key → subject kept opaque, background transparent, no green fringe on the subject
    p = td / "kettle.png"
    scene((0, 177, 64), (150, 92, 60)).save(p)
    out = image_fx.chroma_cutout(str(p))
    o = Image.open(out).convert("RGBA")
    check(out.endswith(".cut.png"), "default out path is <src>.cut.png")
    check(o.getpixel((5, 5))[3] == 0, "the background must be transparent")
    check(o.getpixel((150, 150))[3] == 255 and o.getpixel((150, 150))[:3] == (150, 92, 60),
          "the subject must stay opaque and unchanged")
    # Review Focus 3: a GREEN subject on a MAGENTA key survives
    g = td / "leaf.png"
    scene((255, 0, 255), (46, 125, 50)).save(g)
    go = Image.open(image_fx.chroma_cutout(str(g))).convert("RGBA")
    check(go.getpixel((150, 150))[3] == 255, "a green subject on a magenta key must survive")
    # a SOFT edge (every real generation has one): the mixed subject/key pixels just inside the edge
    # are far enough from the key to stay OPAQUE, and they carry the key's green — a visible fringe
    # unless the despill reaches them. Measured 2026-10-03: the first version left a green outline.
    from PIL import ImageFilter
    sb = td / "soft.png"
    scene((0, 177, 64), (196, 140, 92), size=(600, 600), box=(120, 100, 480, 520)).filter(
        ImageFilter.GaussianBlur(1.5)).save(sb)
    so = Image.open(image_fx.chroma_cutout(str(sb))).convert("RGBA")
    greenish = [p for p in so.getdata() if p[3] > 0 and p[1] > max(p[0], p[2]) + 8]
    check(not greenish, "a soft edge keeps {} green-fringed pixel(s), e.g. {}".format(len(greenish), greenish[:3]))
    # ...while a green SUBJECT on a magenta key keeps its own green inside (the despill is an edge band)
    check(go.getpixel((150, 150))[:3] == (46, 125, 50), "a magenta-key despill must not touch the green interior: {}"
          .format(go.getpixel((150, 150))))
    # refusals
    n = td / "noisy.png"
    scene((0, 177, 64), (150, 92, 60), noise=70).save(n)
    e = td / "edge.png"
    scene((0, 177, 64), (150, 92, 60), box=(-20, 40, 200, 260)).save(e)
    t = td / "tiny.png"
    scene((0, 177, 64), (150, 92, 60), box=(140, 140, 146, 146)).save(t)
    for f, word in ((n, "flat"), (e, "edge"), (t, "subject")):
        try:
            image_fx.chroma_cutout(str(f))
            fails.append("chroma_cutout accepted {}".format(f.name))
        except ValueError as ex:
            check(word in str(ex), "{}: refusal should mention {!r}: {}".format(f.name, word, ex))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_chroma_cutout] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
