#!/usr/bin/env python3
"""picture() can mask, rotate and aim its crop — and the mask is real in the RENDER.

Editorial decks put photos in circles, arches, chamfered and notched cards and organic blobs; the
library could only round corners (`_round_pic_geom`), so every such page was a rectangle. The XML
is asserted, and then the render is sampled: a geometry that LibreOffice ignored would pass every
XML assertion and still ship a rectangle.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deckkit as dk  # noqa: E402
import render_deck as rd  # noqa: E402
from PIL import Image  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def geom(pic):
    x = pic._element.xml
    if "<a:custGeom" in x:
        return "custGeom"
    m = re.search(r'<a:prstGeom[^>]*prst="([a-zA-Z0-9]+)"', x)
    return m.group(1) if m else None


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    red = td / "red.png"
    # 2:1, red throughout but NOT one flat colour — a flat plate is (rightly) ASSET NOT USABLE
    im0 = Image.new("RGB", (800, 400))
    im0.putdata([(200 + (x * 35) // 800, 25 + (y * 20) // 400, 30) for y in range(400) for x in range(800)])
    im0.save(red)
    prs = dk.blank_deck(13.333, 7.5)
    s = dk.add_slide(prs)
    dk.slide_background(s, dk.WHITE)
    want = {"ellipse": "ellipse", "arch": "round2SameRect", "snip": "snip2DiagRect",
            "notch": "custGeom", "blob": "custGeom"}
    for i, (shape, g) in enumerate(want.items()):
        p = dk.picture(s, str(red), 0.5 + i * 2.5, 1.0, 2.2, 2.2, fit="cover", shape=shape, alt="")
        check(geom(p) == g, "shape={} gave geometry {}".format(shape, geom(p)))
        # cover keeps the aspect: a 2:1 image in a square frame crops HALF the width, evenly
        check(abs(p.crop_left - 0.25) < 1e-6 and abs(p.crop_right - 0.25) < 1e-6,
              "shape={} cover crop not even: {} {}".format(shape, p.crop_left, p.crop_right))
        check(p._element.spPr.find(dk.qn("a:prstGeom")) is None or g != "custGeom",
              "shape={} left a prstGeom beside its custGeom".format(shape))
    # focus=(0, .5): keep the LEFT edge — the whole crop comes off the right
    p = dk.picture(s, str(red), 0.5, 4.0, 2.2, 2.2, fit="cover", shape="ellipse",
                   focus=(0.0, 0.5), alt="")
    check(abs(p.crop_left) < 1e-9 and abs(p.crop_right - 0.5) < 1e-6,
          "focus x=0 must crop only the right ({} {})".format(p.crop_left, p.crop_right))
    # rotation is stored and read back in [0,360)
    p = dk.picture(s, str(red), 3.2, 4.0, 2.0, 2.4, fit="cover", rotation=-6, alt="")
    check(abs(p.rotation - 354.0) < 1e-6, "rotation=-6 should read back 354, got {}".format(p.rotation))
    # tall frames keep their geometry (a 9:16 page's arch / blob / notch)
    for shape in ("arch", "blob", "notch"):
        q = dk.picture(s, str(red), 6.0, 3.6, 1.2, 3.6, fit="cover", shape=shape, alt="")
        check(geom(q) == want[shape], "tall {} lost its geometry".format(shape))
        if shape == "blob":
            nums = [int(v) for v in re.findall(r'<a:pt x="(-?\d+)" y="(-?\d+)"', q._element.xml)
                    for v in v]
            path = re.search(r'<a:path w="(\d+)" h="(\d+)"', q._element.xml)
            W, H = int(path.group(1)), int(path.group(2))
            check(all(0 <= v <= max(W, H) for v in nums), "tall blob escapes its frame")
    # contain + shape masks the PLACED (letterboxed) picture, not the frame
    c = dk.picture(s, str(red), 9.0, 4.0, 2.0, 2.0, fit="contain", shape="ellipse", alt="")
    check(abs(c.height / 914400.0 - 1.0) < 1e-3 and geom(c) == "ellipse",
          "contain+ellipse should mask the 2.0x1.0 placed image")
    # refusals
    for bad, kw in (("unknown shape", {"shape": "star"}),
                    ("shape+round", {"shape": "ellipse", "round": True}),
                    ("focus out of range", {"focus": (1.4, 0.5)})):
        try:
            dk.picture(s, str(red), 0.5, 0.5, 1, 1, fit="cover", alt="", **kw)
            fails.append("picture() accepted {}".format(bad))
        except ValueError:
            pass
    deck = td / "pics.pptx"
    prs.save(str(deck))
    crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
    check(not crit, "a deck of masked pictures has CRITICAL layout findings: {}".format(crit))

    # ── the RENDER clips: sample corners (white) and centres (red) of each masked picture ──────
    soffice = rd.find_soffice()
    if not soffice:
        fails.append("LibreOffice not found — the render half of this test did not run")
    else:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(td), str(deck)],
                       check=True, capture_output=True, timeout=180)
        import fitz
        page = fitz.open(str(td / "pics.pdf"))[0]
        pix = page.get_pixmap(dpi=40)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        k = pix.width / 13.333

        def px(xi, yi):
            return im.getpixel((int(xi * k), int(yi * k)))

        def is_red(c):
            return c[0] > 170 and c[1] < 90 and c[2] < 90

        corner = {"ellipse": (0.12, 0.12), "arch": (0.08, 0.08), "snip": (2.15, 0.05),
                  "notch": (2.12, 0.08), "blob": (0.06, 0.06)}
        for i, shape in enumerate(want):
            x0 = 0.5 + i * 2.5
            check(is_red(px(x0 + 1.1, 1.0 + 1.1)), "{}: centre is not red in the render".format(shape))
            cx, cy = corner[shape]
            check(not is_red(px(x0 + cx, 1.0 + cy)),
                  "{}: frame corner is still painted — the mask did not clip".format(shape))

# ── generalisation probe (2026-10-03): inputs the first tests never tried ──────────────────────

with tempfile.TemporaryDirectory() as td2:
    _p = Path(td2) / "g.png"
    _g = Image.new("RGB", (300, 200))
    _g.putdata([(x % 256, y % 256, 90) for y in range(200) for x in range(300)])
    _g.save(_p)
    _d = dk.blank_deck(13.333, 7.5)
    _s = dk.add_slide(_d)
    for bad in ("center", (0.5,), (0.5, "top")):
        try:
            dk.picture(_s, str(_p), 1, 1, 2, 2, fit="cover", focus=bad, alt="")
            fails.append("picture() accepted focus={!r}".format(bad))
        except ValueError as e:
            check("focus" in str(e), "picture()'s refusal should name focus: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_picture_shapes] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
