#!/usr/bin/env python3
"""surfaces — grounds that are not flat colour.

`grain_background` sets a deterministic, tiled grain/paper tile as the slide's REAL background
(`<p:bg>` picture fill). Verified 2026-10-03: LibreOffice renders the tile; `lint_layout` walks shapes
only, so the background is never an "asset" finding — a subtle grain placed as a picture SHAPE would
be a CRITICAL ASSET NOT USABLE (flat bucket). Amplitude is capped (≤ ±10 levels) so text contrast holds.
"""
from __future__ import annotations

import hashlib
import random
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")
TILE = 256


def _tile(color, strength, seed):
    from PIL import Image
    c = color.lstrip("#").upper()
    key = hashlib.sha1("{}-{}-{}".format(c, strength, seed).encode()).hexdigest()[:16]
    d = Path(tempfile.gettempdir()) / "slide-maker-grain"
    d.mkdir(parents=True, exist_ok=True)
    out = d / "grain-{}.png".format(key)
    if not out.exists():
        rnd = random.Random("{}:{}:{}".format(c, strength, seed))
        base = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        px = []
        for _ in range(TILE * TILE):
            n = rnd.randint(-strength, strength)
            px.append(tuple(max(0, min(255, v + n)) for v in base))
        im = Image.new("RGB", (TILE, TILE))
        im.putdata(px)
        im.save(out)
    return str(out)


def grain_background(slide, color, *, strength=5, seed=0):
    """Set a tiled grain of `color` as the slide's background (replacing any `<p:bg>`)."""
    from lxml import etree
    from pptx.oxml.ns import qn
    if not (isinstance(color, str) and _HEX.match(color)):
        raise ValueError("grain_background(): color must be 'RRGGBB', got {!r}".format(color))
    if not (isinstance(strength, int) and 1 <= strength <= 10):
        raise ValueError("grain_background(): strength must be an int 1..10 (± levels), got {!r}".format(strength))
    path = _tile(color, strength, seed)
    _part, rid = slide.part.get_or_add_image_part(path)
    csld = slide._element.find(qn("p:cSld"))
    for old in csld.findall(qn("p:bg")):
        csld.remove(old)
    bg = etree.Element(qn("p:bg"))
    pr = etree.SubElement(bg, qn("p:bgPr"))
    bf = etree.SubElement(pr, qn("a:blipFill"), {"dpi": "0", "rotWithShape": "1"})
    etree.SubElement(bf, qn("a:blip"), {qn("r:embed"): rid})
    etree.SubElement(bf, qn("a:srcRect"))
    etree.SubElement(bf, qn("a:tile"), {"tx": "0", "ty": "0", "sx": "100000", "sy": "100000",
                                        "flip": "none", "algn": "tl"})
    etree.SubElement(pr, qn("a:effectLst"))
    csld.insert(0, bg)
    return path
