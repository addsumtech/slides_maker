#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_pairs — blind side-by-side sheets for judging two decks built from the same material.

For each brief it pairs v420 with current, and current with baseline, each in BOTH left/right orders,
so a judge's position bias cancels out. Every deck is drawn the same way — its slide PNGs in a 4-column
grid — never the renderer's own contact sheet, whose layout differs with slide count. File names are
random; the mapping back to the sources is only in key.json.

    python3 scripts/design_bench/make_pairs.py entries.json --out DIR [--seed N]
    (entries.json: [{"brief": id, "arm": "baseline|v420|current", "render": "<dir of slideNN.png>"}])
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

COMPARISONS = (("v420", "current"), ("current", "baseline"))
COLS, THUMB_W, PAD, GAP, HEADER = 4, 360, 16, 48, 72


def _slides(render_dir):
    fs = sorted(glob.glob(os.path.join(render_dir, "slide[0-9]*.png")))
    if not fs:
        raise SystemExit("[make_pairs] no slideNN.png in {}".format(render_dir))
    return fs


def _panel(render_dir, label, height=None):
    fs = _slides(render_dir)
    thumbs = []
    for f in fs:
        im = Image.open(f).convert("RGB")
        im = im.resize((THUMB_W, max(1, round(im.height * THUMB_W / im.width))))
        thumbs.append(im)
    th = max(t.height for t in thumbs)
    rows = (len(thumbs) + COLS - 1) // COLS
    w = PAD * 2 + COLS * THUMB_W + (COLS - 1) * PAD
    h = height or HEADER + rows * (th + PAD) + PAD
    panel = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(panel)
    try:
        font = ImageFont.load_default(size=40)
    except TypeError:                                        # Pillow < 10.1
        font = ImageFont.load_default()
    d.text((PAD, 14), label, fill=(0, 0, 0), font=font)
    for i, t in enumerate(thumbs):
        panel.paste(t, (PAD + (i % COLS) * (THUMB_W + PAD), HEADER + (i // COLS) * (th + PAD)))
    return panel


def _sheet(left_dir, right_dir, path):
    a, b = _panel(left_dir, "A"), _panel(right_dir, "B")
    h = max(a.height, b.height)
    a, b = _panel(left_dir, "A", h), _panel(right_dir, "B", h)
    sheet = Image.new("RGB", (a.width + GAP + b.width, h), (200, 200, 200))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width + GAP, 0))
    sheet.save(path)


def make_pairs(entries: list[dict], out_dir: str, seed: int, comparisons=COMPARISONS) -> list[dict]:
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(seed)
    by = {}
    for e in entries:
        by.setdefault(e["brief"], {})[e["arm"]] = e
    pairs, key = [], {}
    for brief in sorted(by):
        arms = by[brief]
        for x, y in comparisons:
            if x not in arms or y not in arms:
                continue
            for left, right in ((arms[x], arms[y]), (arms[y], arms[x])):
                name = "pair_%08x.png" % rng.getrandbits(32)
                _sheet(left["render"], right["render"], os.path.join(out_dir, name))
                p = {"file": name, "brief": brief, "comparison": "%s-vs-%s" % (x, y),
                     "left": {"arm": left["arm"], "render": left["render"]},
                     "right": {"arm": right["arm"], "render": right["render"]}}
                pairs.append(p)
                key[name] = {"brief": brief, "comparison": p["comparison"],
                             "left": left["arm"], "right": right["arm"]}
    with open(os.path.join(out_dir, "key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)
    return pairs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("entries")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--compare", nargs="+", metavar="X:Y",
                    help="arm pairs to compare (default v420:current current:baseline)")
    a = ap.parse_args(argv)
    with open(a.entries, encoding="utf-8") as f:
        comps = tuple(tuple(c.split(":", 1)) for c in a.compare) if a.compare else COMPARISONS
        pairs = make_pairs(json.load(f), a.out, a.seed, comps)
    print("{} sheet(s) in {}".format(len(pairs), a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
