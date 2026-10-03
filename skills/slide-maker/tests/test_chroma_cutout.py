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
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

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
    # a MAGENTA key's despill must not turn the edge green: capping red and blue AT green did exactly that
    # to a real watercolour pot (an orange rim went pale green). Subtract only the key's EXCESS.
    so2 = td / "soft_mg.png"
    scene((255, 0, 255), (214, 128, 70), size=(600, 600), box=(120, 100, 480, 520)).filter(
        ImageFilter.GaussianBlur(1.5)).save(so2)
    o2 = list(Image.open(image_fx.chroma_cutout(str(so2), key="FF00FF")).convert("RGBA").getdata())
    raw2 = list(Image.open(so2).convert("RGB").getdata())
    # the property: a visible pixel that carries NO key excess (for magenta: min(R, B) <= G) is the
    # subject's own colour and must come through UNCHANGED — the cap turned real orange (191,164,95) olive
    moved = [(r_, c_) for r_, c_ in zip(raw2, o2) if c_[3] > 0 and min(r_[0], r_[2]) <= r_[1] and c_[:3] != r_]
    check(not moved, "despill altered {} spill-free subject px, e.g. raw->cut {}".format(len(moved), moved[:3]))
    leftover = [c_ for c_ in o2 if c_[3] > 0 and min(c_[0], c_[2]) > c_[1] + 8]
    check(not leftover, "magenta spill left on {} visible px, e.g. {}".format(len(leftover), leftover[:3]))
    # ...while a green SUBJECT on a magenta key keeps its own green inside (the despill is an edge band)
    check(go.getpixel((150, 150))[:3] == (46, 125, 50), "a magenta-key despill must not touch the green interior: {}"
          .format(go.getpixel((150, 150))))
    # the background must be the key colour ASKED for: measured 2026-10-03, a watercolour series' style
    # reference won over the prompt and a cut-out came back on cream PAPER; keyed anyway, the subject's
    # own cream highlights went with it (holes in a pot rim, specks through the soil) and nothing said so
    cream = td / "cream.png"
    scene((252, 243, 224), (196, 120, 70)).save(cream)
    try:
        image_fx.chroma_cutout(str(cream), key="FF00FF")
        fails.append("chroma_cutout keyed a cream background when FF00FF was asked for")
    except ValueError as ex:
        check("key" in str(ex) and "FF00FF" in str(ex), "the refusal should name the asked-for key: {}".format(ex))
    mg = td / "mg.png"
    scene((255, 0, 255), (46, 125, 50)).save(mg)
    check(image_fx.chroma_cutout(str(mg), key="#ff00ff").endswith(".cut.png"), "the right key passes, any case/#")
    # the key must not EAT part of the subject: green leaves on the green key came back fully transparent
    # while the pot kept the subject share up — "OK" with the leaves gone (final review, 2026-10-03)
    for leaf in ((20, 165, 60), (40, 150, 60)):
        im = Image.new("RGB", (400, 400), (0, 177, 64))
        dr = ImageDraw.Draw(im)
        dr.rectangle((150, 230, 250, 340), fill=(170, 100, 60))                     # the pot
        for box in ((90, 60, 190, 150), (210, 60, 310, 150), (150, 120, 250, 220)):  # three big leaves
            dr.ellipse(box, fill=leaf)
        lp = td / "leafy.png"
        im.save(lp)
        try:
            image_fx.chroma_cutout(str(lp))
            fails.append("chroma_cutout keyed away {} leaves on the green key without refusing".format(leaf))
        except ValueError as ex:
            check("FF00FF" in str(ex), "the refusal should name the other key: {}".format(ex))
    # ...but a hole that IS the background (a kettle handle's loop) is not an eaten subject
    loop = Image.new("RGB", (400, 400), (0, 177, 64))
    dl = ImageDraw.Draw(loop)
    dl.rectangle((120, 180, 280, 340), fill=(230, 220, 190))
    dl.ellipse((130, 60, 270, 200), fill=(40, 40, 40))
    dl.ellipse((160, 90, 240, 170), fill=(0, 177, 64))                             # the loop shows the key
    lo = td / "loop.png"
    loop.save(lo)
    check(image_fx.chroma_cutout(str(lo)).endswith(".cut.png"), "a background-coloured hole must pass")
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

# the masks are grown with an O(n) dilation: PIL's MaxFilter(37) took ~20 s per call on a 4000x3000
# image (66 s per cut-out, generality probe 2026-10-03). It must equal MaxFilter exactly.
import numpy as np  # noqa: E402
import random  # noqa: E402
_r = random.Random(7)
for _ in range(25):
    h, w, k = _r.randint(5, 60), _r.randint(5, 60), _r.randint(1, 6)
    m = np.array([[_r.random() < 0.05 for _x in range(w)] for _y in range(h)])
    ref = np.asarray(Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(2 * k + 1))) > 0
    got = image_fx._dilate(m, k)
    check(got.shape == m.shape and (got == ref).all(), "_dilate differs from MaxFilter at h={} w={} k={}".format(h, w, k))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_chroma_cutout] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
