#!/usr/bin/env python3
"""ASSET NOT USABLE — a picture that arrived but cannot carry anything.

Every asset gate here asks whether a planned asset was USED. None asked whether the file that got
used is any good, and existence is not success: a failed generation writes a truncated download or
a flat placeholder plate, a bad crop writes a fully transparent frame. All three embed without
complaint, render as a blank rectangle, and pass every geometric, contrast and density check —
the picture DOES occupy its box, so the page does not even read as underfilled.

The negatives matter more than the positives, and one especially: an icon is mostly transparent by
construction, so a rule about emptiness that is written carelessly fires on every icon in the
library.
"""
import io, pathlib, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

ok, bad = [], []
for _m in ("pptx", "PIL"):
    try:
        __import__(_m)
    except ImportError:
        print(f"skip: {_m} not installed")
        raise SystemExit(0)

import deckkit as dk                                        # noqa: E402
from PIL import Image                                       # noqa: E402

dk.FONT = "Helvetica Neue"
TMP = pathlib.Path(tempfile.mkdtemp(prefix="asset-"))
W, H = 10.0, 5.625


def _save(im, name):
    p = TMP / name
    im.save(p)
    return str(p)


def _page():
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    dk.slide_background(s, "F5F1E6")
    return prs, s


def _hits(prs):
    return [f for f in dk.lint_layout(prs, verbose=False) if f[2] == "ASSET NOT USABLE"]


def _photo(w=300, h=200):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = ((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256)
    return im


def _icon(cov=0.30):
    im = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    px = im.load()
    for i in range(int(192 * 192 * cov)):
        px[i % 192, i // 192] = (0x1F, 0x3B, 0x2F, 255)
    return im


# ---------------------------------------------------------------- negatives: real assets are fine
prs, s = _page()
dk.picture(s, _save(_photo(), "photo.png"), 1, 1, 4, 2.6)
if not _hits(prs):
    ok.append("an ordinary photograph is silent")
else:
    bad.append("a valid photograph was reported unusable")

prs, s = _page()
dk.icon(s, _save(_icon(), "ic.png"), 1, 1, 0.8, alt="a category icon")
if not _hits(prs):
    ok.append("a monochrome icon is silent — it is ~70% transparent by construction, which a "
              "carelessly written emptiness rule would fire on for every icon in the library")
else:
    bad.append("an ordinary icon was reported unusable")

prs, s = _page()
dk.icon(s, _save(_icon(cov=0.03), "sparse.png"), 1, 1, 0.8, alt="a hairline icon")
if not _hits(prs):
    ok.append("a very sparse (3% ink) hairline icon is still silent")
else:
    bad.append("a sparse icon was mistaken for an empty frame")

grad = Image.new("RGB", (200, 200))
gp = grad.load()
for y in range(200):
    for x in range(200):
        gp[x, y] = (30 + x // 4, 40 + y // 5, 90)
prs, s = _page()
dk.picture(s, _save(grad, "grad.png"), 1, 1, 3, 3)
if not _hits(prs):
    ok.append("a smooth gradient plate is silent — it is not one flat colour")
else:
    bad.append("a gradient was treated as a flat placeholder")

# ---------------------------------------------------------------- positives: the three failures
prs, s = _page()
dk.picture(s, _save(Image.new("RGB", (300, 200), (140, 140, 140)), "flat.png"), 1, 1, 4, 2.6)
h = _hits(prs)
if len(h) == 1 and h[0][1] == "CRITICAL" and "flat colour" in h[0][3]:
    ok.append("a FLAT PLACEHOLDER plate is CRITICAL — the shape of a failed generation")
else:
    bad.append(f"a flat placeholder passed: {h}")

prs, s = _page()
dk.picture(s, _save(Image.new("RGBA", (300, 200), (0, 0, 0, 0)), "empty.png"), 1, 1, 4, 2.6)
h = _hits(prs)
if len(h) == 1 and "fully transparent" in h[0][3]:
    ok.append("a FULLY TRANSPARENT frame is CRITICAL — a hole in the layout with a caption under it")
else:
    bad.append(f"an empty frame passed: {h}")

src = TMP / "src.png"
_photo().save(src)
trunc = TMP / "trunc.png"
trunc.write_bytes(src.read_bytes()[:400])
prs, s = _page()
try:
    dk.picture(s, str(trunc), 1, 1, 4, 2.6)
    h = _hits(prs)
    if len(h) == 1 and "does not decode" in h[0][3]:
        ok.append("a TRUNCATED download is CRITICAL — the file exists, so every path that only "
                  "checks existence passed it")
    else:
        bad.append(f"a truncated image passed: {h}")
except Exception:
    ok.append("a truncated download fails even earlier, at picture() — also acceptable")

# ---------------------------------------------------------------- it names the shape
prs, s = _page()
shp = dk.picture(s, _save(Image.new("RGB", (200, 200), (9, 9, 9)), "black.png"), 1, 1, 3, 3)
try:
    shp.name = "hero-illustration"
except Exception:
    pass
h = _hits(prs)
if h and "hero-illustration" in h[0][3]:
    ok.append("the finding names the offending picture, so the fix does not need a hunt")
else:
    bad.append(f"the finding does not identify which picture failed: {h}")

# ---------------------------------------------------------------- several bad assets, several findings
prs, s = _page()
dk.picture(s, _save(Image.new("RGB", (200, 200), (140, 140, 140)), "f1.png"), 0.5, 1, 2, 2)
dk.picture(s, _save(Image.new("RGBA", (200, 200), (0, 0, 0, 0)), "e1.png"), 3.0, 1, 2, 2)
dk.picture(s, _save(_photo(), "good.png"), 5.5, 1, 2, 2)
if len(_hits(prs)) == 2:
    ok.append("two unusable assets beside one good one produce exactly two findings")
else:
    bad.append(f"expected 2 findings on a mixed slide, got {len(_hits(prs))}")

# ---------------------------------------------------------------- grouped + vector assets
prs, s = _page()
dk.picture(s, _save(Image.new("RGB", (200, 200), (140, 140, 140)), "gflat.png"), 1, 1, 2, 2)
dk.box(s, 4, 1, 1, 1, fill="1F3B2F")
s.shapes.add_group_shape([x for x in list(s.shapes)][-2:])
if len(_hits(prs)) == 1:
    ok.append("a flat placeholder INSIDE a group is still caught")
else:
    bad.append("grouping a bad picture hid it from the check")


class _FakeImg(object):
    def __init__(self, ext):
        self.ext, self.blob = ext, b"not-decodable-by-pillow"


class _FakePic(object):
    shape_type = "PICTURE (13)"
    name = "vector-logo"
    rotation = 0.0

    def __init__(self, ext):
        self.image = _FakeImg(ext)


class _FakeSlide(object):
    def __init__(self, shapes):
        self.shapes = shapes


class _FakePrs(object):
    def __init__(self, slides):
        self.slides = slides


for ext in ("emf", "wmf", "svg"):
    f = dk._asset_faults(_FakePrs([_FakeSlide([_FakePic(ext)])]))
    if not f:
        ok.append(f".{ext} is skipped, not reported — Pillow cannot open a metafile, and saying "
                  f"'does not decode' about one would be a confident wrong finding on somebody "
                  f"else's template (the redesign route lints decks this skill did not build)")
    else:
        bad.append(f".{ext} was reported as undecodable: {f}")

f = dk._asset_faults(_FakePrs([_FakeSlide([_FakePic("png")])]))
if f and "does not decode" in f[0][3]:
    ok.append("a .png that genuinely does not decode IS still reported (the extension carve is "
              "narrow, not an escape hatch)")
else:
    bad.append("the vector carve swallowed a real undecodable bitmap")

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print(f"\n{len(ok)} passed, {len(bad)} failed")
raise SystemExit(1 if bad else 0)
