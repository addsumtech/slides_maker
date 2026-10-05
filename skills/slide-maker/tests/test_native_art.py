#!/usr/bin/env python3
"""native_art: every primitive draws ON the page, in range, deterministically, on any canvas."""
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk
import native_art as na
import ooxml_safety as ox

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

td = Path(tempfile.mkdtemp())
check(na.angle(-90) == 16200000 and na.angle(450) == 5400000 and na.angle(0) == 0, "angles normalise into range")
check(na.clip_to_page([(-1, -1), (2, -1), (2, 2), (-1, 2)], 1.0, 1.0) and
      all(0 <= x <= 1 and 0 <= y <= 1 for x, y in na.clip_to_page([(-1, -1), (2, -1), (2, 2), (-1, 2)], 1.0, 1.0)),
      "clip_to_page keeps a polygon inside the page")
check(na.clip_to_page([(5, 5), (6, 5), (6, 6)], 1.0, 1.0) == [], "a polygon wholly off the page clips to nothing")

def build(W, H, seed):
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    na.ink_ridges(s, color="1D1C1A", layers=na.INK_LAYERS["land" if W > H else "port"], seed=seed,
                  keep_clear=[(W * 0.78, 0.5, 1.0, H * 0.6)])
    na.seal(s, 1.0, 1.0, 0.6, "茶事", fill="B0362A", ink="F6EEE6", face="Songti SC")
    na.enso(s, W * 0.3, H * 0.5, min(W, H) * 0.3, 0.4, color="1D1C1A")
    na.paper_hill(s, na.hill_points(W, H * 0.7, H * 0.12, seed, 1.8), H + 1.0, fill="5AA38A")
    na.paper_card(s, 0.5, 0.5, 3.0, 2.0)
    na.cloud(s, W * 0.5, H * 0.2, 1.6)
    na.paper_sun(s, W * 0.7, H * 0.3, (2.0, 1.4), ("F7D38A", "F2B33D"))
    na.clipped_block(s, W - 2.0, H - 2.0, 4.0, 4.0, -9, fill="D7FF3B")
    tops = na.iso_stack(s, W * 0.5, H * 0.3, min(W, H) * 0.25, 0.8, 3, ink="1E3A5F", accent="E2552C", accent_layer=1)
    na.dimension_line(s, W * 0.9, H * 0.2, H * 0.7, ink="1E3A5F")
    na.balloon(s, 1.0, H - 1.5, 0.42, "2", ink="1E3A5F", accent="B8401A", face="Courier New", fill="F1EFE8")
    p = td / "art_{}x{}_{}.pptx".format(W, H, seed)
    prs.save(str(p))
    return p, prs, tops

for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333)):
    p, prs, tops = build(W, H, 3)
    check(len(tops) == 3 and all(len(t) == 4 for t in tops), "iso_stack returns one rhombus per layer ({}x{})".format(W, H))
    check(ox.xml_findings(str(p)) == [], "no PowerPoint-repaired value ({}x{}): {}".format(W, H, ox.xml_findings(str(p))[:2]))
    check(ox.beyond_page(prs) == [], "nothing past the page ({}x{}): {}".format(W, H, ox.beyond_page(prs)[:2]))
a = (td / "art_13.333x7.5_3.pptx").read_bytes()
p2, _, _ = build(13.333, 7.5, 3)
import zipfile
x1 = zipfile.ZipFile(str(td / "art_13.333x7.5_3.pptx")).read("ppt/slides/slide1.xml")
x2 = zipfile.ZipFile(str(p2)).read("ppt/slides/slide1.xml")
check(x1 == x2, "deterministic for a seed")
try:
    prs = dk.blank_deck(13.333, 7.5); na.seal(dk.add_slide(prs), 1, 1, 0.6, "三个字", fill="B0362A", ink="FFFFFF", face="Songti SC")
    check(False, "a three-character seal is refused")
except ValueError:
    check(True, "a three-character seal is refused")
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
na.grid_background(s, base="F1EFE8", ink="1E3A5F")
na.solid_background(dk.add_slide(prs), "1F3BFF")
p = td / "bg.pptx"; prs.save(str(p))
check(ox.xml_findings(str(p)) == [], "backgrounds are valid OOXML")

# keep_clear lowers the crest under text with a SHOULDER, never a cliff (a vertical cut read as a broken ridge)
keep = (9.6, 0.6, 1.0, 4.4)
for i_, layer in enumerate(na.INK_LAYERS["land"]):
    pts = na.ridge_points(13.333, 7.5, layer, i_, 1, (0.0, 1.0), [keep])
    foot = keep[1] + keep[3]
    check(all(y >= foot for x, y in pts if keep[0] <= x <= keep[0] + keep[2]), "layer {}: the crest stays under the text".format(i_))
    steep = max(abs(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(pts, pts[1:]))
    check(steep <= 2.2, "layer {}: no cliff beside the kept-clear text (steepest slope {:.1f})".format(i_, steep))
for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
