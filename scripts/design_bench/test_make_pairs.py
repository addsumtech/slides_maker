#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_pairs.py — blind side-by-side sheets for judging two decks built from the same material.

Run:  python3 scripts/design_bench/test_make_pairs.py
"""
import json
import pathlib
import sys
import tempfile

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_pairs as MP  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  %s" % (detail,)))


TMP = pathlib.Path(tempfile.mkdtemp(prefix="make-pairs-"))


def render_dir(name, n, rgb, size=(320, 180)):
    d = TMP / name / "render"
    d.mkdir(parents=True)
    for i in range(1, n + 1):
        Image.new("RGB", size, rgb).save(d / ("slide%02d.png" % i))
    Image.new("RGB", (50, 50), (0, 0, 0)).save(d / "contact_01.png")      # ignored: sheets are rebuilt
    return str(d)


entries = []
for brief in ("quarterly-review", "chengdu"):
    entries.append({"brief": brief, "arm": "baseline", "render": render_dir(brief + "-b", 14, (200, 0, 0))})
    entries.append({"brief": brief, "arm": "v420", "render": render_dir(brief + "-v", 10, (0, 200, 0))})
    entries.append({"brief": brief, "arm": "current", "render": render_dir(brief + "-c", 9, (0, 0, 200))})
entries.append({"brief": "chengdu", "arm": "current-extra", "render": render_dir("x", 3, (9, 9, 9))})

out = TMP / "pairs"
pairs = MP.make_pairs(entries, str(out), seed=7)
files = sorted(p.name for p in out.glob("pair_*.png"))
key = json.loads((out / "key.json").read_text(encoding="utf-8"))

print("── pairs")
check("2 briefs -> 8 sheets (2 comparisons x 2 orders each)", len(files) == 8 and len(pairs) == 8, files)
check("unknown arms are ignored", all(p["left"]["arm"] != "current-extra" and p["right"]["arm"] != "current-extra"
                                       for p in pairs))
check("file names leak nothing", not any(w in f for f in files
                                        for w in ("baseline", "v420", "current", "quarterly", "chengdu")), files)
check("key.json maps every sheet to its left/right source", set(key) == set(files) and
      all({"left", "right", "brief", "comparison"} <= set(v) for v in key.values()), key)
by = {}
for f, v in key.items():
    by.setdefault((v["brief"], v["comparison"]), []).append((v["left"], v["right"]))
check("each comparison is shown in both orders",
      all(len(v) == 2 and v[0] == v[1][::-1] for v in by.values()), by)
check("the comparisons are v420-vs-current and current-vs-baseline",
      {c for _, c in by} == {"v420-vs-current", "current-vs-baseline"}, by.keys())

print("── the sheet")
im = Image.open(out / files[0])
y = MP.HEADER + 10                                   # inside the first thumbnail of each half
px = [im.getpixel((MP.PAD + 10, y)), im.getpixel((im.width // 2 + MP.GAP // 2 + MP.PAD + 10, y))]
check("left half and right half show different decks", px[0] != px[1], px)
check("the sheet is built from slide PNGs, not the lint contact sheet", (0, 0, 0) not in px)
again = MP.make_pairs(entries, str(TMP / "pairs2"), seed=7)
check("same seed, same pairing", [(p["left"], p["right"]) for p in again] == [(p["left"], p["right"]) for p in pairs])

custom = MP.make_pairs(entries, str(TMP / "pairs3"), seed=7, comparisons=(("v420", "baseline"),))
check("custom comparisons: only the requested pair, both orders", len(custom) == 4 and
      {p["comparison"] for p in custom} == {"v420-vs-baseline"}, [p["comparison"] for p in custom])

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
