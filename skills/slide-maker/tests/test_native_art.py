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
# ── P4: the five new languages' motifs ──
import zipfile, re as _re
from PIL import Image
def p4_page(W, H, seed):
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=seed, keep_clear=[(1.0, 1.0, 3.0, 1.0)])
    na.radial_glow(s, W * 0.5, H * 0.4, min(W, H) * 0.5, "F1D9A6")
    na.radial_glow(s, 0.1, 0.1, 3.0, "F1D9A6")                       # near a corner: shrinks to stay whole
    na.horizon_glow(s, H * 0.84, "F1D9A6", "D9B36C")
    na.crescent(s, W - 0.2, 0.2, 0.9, "D9B36C", "0B1430")           # asked for off the corner: moved on
    na.ring(s, W * 0.3, H * 0.5, 1.4, "D9B36C")
    na.polyline(s, [(-1, 1), (W + 1, 2), (W * 0.5, H + 1)], "F3F1EA", w=1.5)
    na.chalk_box(s, 0.5, 0.5, 3.0, 1.6, "F2D16B", seed=seed)
    na.chalk_ellipse(s, W * 0.7, H * 0.5, 1.0, 0.8, "F2A9B8", seed=seed)
    na.chalk_underline(s, 0.5, H * 0.8, 3.0, "F2D16B", seed=seed)
    na.chalk_arrow(s, 4.0, 2.0, 5.0, 2.0, "F3F1EA", seed=seed)
    inner = na.board_frame(s, "7A4F2A", "E8E2D2")
    r1 = na.chip(s, 1.0, 3.0, "MEMBERS", size=12, fill="C6F432", ink="0E0E10", face="Arial")
    r2 = na.chip(s, 1.0, 3.6, "会员", size=12, fill="C6F432", ink="0E0E10", face="Arial", ea_face="Hiragino Sans GB")
    na.share_bar(s, 0.5, H - 1.0, W - 1.0, 0.3, track="E7EAF1", fill="2438F0")
    p = td / "p4_{}x{}_{}.pptx".format(W, H, seed)
    prs.save(str(p))
    return p, prs, s, inner, (r1, r2)

for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333), (7.5, 7.5)):
    p, prs, s, inner, chips = p4_page(W, H, 3)
    check(ox.xml_findings(str(p)) == [], "P4 art {}x{}: PowerPoint-safe: {}".format(W, H, ox.xml_findings(str(p))[:2]))
    check(ox.beyond_page(prs) == [], "P4 art {}x{}: nothing past the page: {}".format(W, H, ox.beyond_page(prs)[:2]))
    check(0 < inner[0] < 0.5 and inner[0] + inner[2] < W and inner[1] + inner[3] < H,
          "P4 art {}x{}: board_frame returns the rect inside its frame {}".format(W, H, inner))
# the glow is clear by 68% of its path: with path="circle" the 100% stop is the bbox CORNER (a rim showed at ~71%)
_p, _prs, _s, _i, _c = p4_page(13.333, 7.5, 3)
gls = [g for sh in _s.shapes for g in sh._element.iter("{%s}gradFill" % na.A_NS) if g.find("{%s}path" % na.A_NS) is not None]
check(gls, "radial glows are radial gradients")
for g in gls:
    stops = {int(gs.get("pos")): int(gs.find(".//{%s}alpha" % na.A_NS).get("val")) for gs in g.iter("{%s}gs" % na.A_NS)}
    check(all(a == 0 for pos, a in stops.items() if pos >= 68000), "a glow is clear from 68% outwards: {}".format(stops))
# the sky is one background PICTURE, deterministic, and clear where words go
pa = na.starfield_png(dk.add_slide(dk.blank_deck(13.333, 7.5)), base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=5,
                      keep_clear=[(2.0, 2.0, 4.0, 2.0)])
pb = na.starfield_png(dk.add_slide(dk.blank_deck(13.333, 7.5)), base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=5,
                      keep_clear=[(2.0, 2.0, 4.0, 2.0)])
check(pa == pb and Path(pa).read_bytes() == Path(pb).read_bytes(), "the same sky is the same picture (cached, deterministic)")
im = Image.open(pa).convert("RGB")
dpi = im.size[0] / 13.333
inside = {im.getpixel((int(x * dpi), int(y * dpi))) for x in (2.2, 3.5, 5.8) for y in (2.2, 3.0, 3.8)}
check(inside == {(0x0B, 0x14, 0x30)}, "no star inside the keep-clear rect: {}".format(inside))
# repainting the background drops the old picture (a starlit page is painted at new_slide, then with its words clear)
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=1)
na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=1, keep_clear=[(1, 1, 2, 2)])
imgs = [r for r in s.part.rels.values() if r.reltype.endswith("/image")]
check(len(imgs) == 1, "a repainted sky leaves one picture on the slide, not an orphan ({})".format(len(imgs)))
na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=1, keep_clear=[(1, 1, 2, 2)])
imgs = [r for r in s.part.rels.values() if r.reltype.endswith("/image")]
check(len(imgs) == 1 and s._element.find(".//" + "{%s}blip" % na.A_NS) is not None,
      "repainting with the SAME picture keeps it (the old and new share one relationship)")
# chips are as wide as their words, one line, and a CJK chip is at least an em a character
w_en, w_long = na.chip_width("TAGS", 12, "Arial"), na.chip_width("TAGS AND MORE TAGS", 12, "Arial")
check(w_long > w_en > 0.4, "a chip grows with its words ({:.2f} < {:.2f})".format(w_en, w_long))
check(na.chip_width("会员资格", 12, "Arial") >= 4 * 12 / 72.0, "a CJK chip is at least an em per character")
_tbs = [sh for sh in _s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text in ("MEMBERS", "会员")]
check(len(_tbs) == 2 and all(t.text_frame.word_wrap is False for t in _tbs), "chip text never wraps")
# the share bar draws its fraction of the track, clamped
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
na.share_bar(s, 1.0, 6.0, 10.0, 0.3, track="E7EAF1", fill="2438F0")
na.share_bar(s, 1.0, 6.5, 10.0, 1.7, track="E7EAF1", fill="2438F0")
ws = sorted(round(sh.width / 914400.0, 2) for sh in s.shapes)
check(ws == [3.0, 10.0, 10.0, 10.0], "share bars: 30% of the track, and a fraction over 1 clamps to the track ({})".format(ws))
# chalk is deterministic for a seed
def chalk_xml(seed):
    prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
    na.chalk_box(s, 1, 1, 3, 2, "F2D16B", seed=seed)
    return "".join(sh._element.xml for sh in s.shapes)
check(chalk_xml(4) == chalk_xml(4) and chalk_xml(4) != chalk_xml(5), "chalk strokes are deterministic for a seed")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
