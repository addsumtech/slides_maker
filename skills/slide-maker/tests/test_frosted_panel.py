#!/usr/bin/env python3
"""frosted_panel(): glass made from the picture region that is ACTUALLY under the panel.

`glass_card` fakes frost with an alpha gradient and needs a dark ground to read. Real frosted glass
is a blur of what is behind it. A blurred crop of the WRONG region was tried (2026-10-03) and read
as a grey slab with illegible white text — so the region is computed from the backdrop's placement
and crop, and the ink is chosen against the panel's own pixels or the call is refused.
"""
from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deckkit as dk  # noqa: E402
from PIL import Image  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def pictures(slide):
    return [sh for sh in slide.shapes if "PICTURE" in str(getattr(sh, "shape_type", ""))]


def glass_lum(slide):
    """Luminance at the centre of the glass plate — the shape frosted_panel draws just before its
    tint wash. A blurred NON-flat region is a picture; a flat one is drawn as a box (a flat picture
    is ASSET NOT USABLE), so read whichever it is."""
    plate = list(slide.shapes)[-2]
    if "PICTURE" in str(plate.shape_type):
        g = Image.open(io.BytesIO(plate.image.blob)).convert("L")
        return g.getpixel((g.width // 2, g.height // 2)), "picture"
    c = plate.fill.fore_color.rgb
    return int(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]), "box"


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # left half black, right half white — so WHICH region was blurred is visible in the result
    src = td / "half.png"
    im = Image.new("RGB", (1600, 900), (255, 255, 255))
    im.paste((0, 0, 0), (0, 0, 800, 900))
    im.save(src)
    prs = dk.blank_deck(13.333, 7.5)
    s = dk.add_slide(prs)
    bd = dk.picture(s, str(src), 0, 0, 13.333, 7.5, fit="cover", alt="a two-tone test plate")
    x, y, w, h, ink = dk.frosted_panel(s, bd, 1.0, 2.0, 4.0, 2.0)       # wholly over the BLACK half
    lum, kind = glass_lum(s)
    check(lum < 60, "the glass over the black half is not dark — the wrong region was blurred")
    check(kind == "box", "a blur of a flat region must be drawn as a box, got a " + kind)
    check(str(ink) == str(dk.WHITE), "ink over dark glass must be white, got {}".format(ink))
    check(x > 1.0 and y > 2.0 and x + w < 5.0 and y + h < 4.0, "content rect must be inset")
    # over the WHITE half the ink flips to dark
    *_r, ink2 = dk.frosted_panel(s, bd, 8.0, 2.0, 4.0, 2.0)
    check(dk.contrast_ratio(ink2, dk.WHITE) >= 4.5, "ink over light glass must be dark")
    # a COVER-cropped backdrop: a 2:1 image in a 16:9 frame loses its sides; the region math must
    # follow the crop. Left 40% black on the source -> after the even crop the black band ends at
    # x = (0.40 - crop_left) / (1 - 2*crop_left) of the frame
    src2 = td / "band.png"
    im2 = Image.new("RGB", (2000, 1000), (255, 255, 255))
    im2.paste((0, 0, 0), (0, 0, 800, 1000))
    im2.save(src2)
    s3 = dk.add_slide(prs)
    bd3 = dk.picture(s3, str(src2), 0, 0, 13.333, 7.5, fit="cover", alt="a banded test plate")
    edge = (0.40 - bd3.crop_left) / (1 - bd3.crop_left - bd3.crop_right) * 13.333
    dk.frosted_panel(s3, bd3, max(0.2, edge - 2.6), 2.0, 2.2, 2.0, alpha=0.30)   # just left of it
    check(glass_lum(s3)[0] < 60, "with a cover crop, the glass left of the black/white edge must be dark")
    # a NON-flat region stays a blurred PICTURE: a dark-to-mid gradient, glass over its dark end
    src4 = td / "ramp.png"
    im4 = Image.new("RGB", (1600, 900))
    im4.putdata([(x * 120 // 1600, x * 120 // 1600, 40 + y * 60 // 900) for y in range(900) for x in range(1600)])
    im4.save(src4)
    s4 = dk.add_slide(prs)
    bd4 = dk.picture(s4, str(src4), 0, 0, 13.333, 7.5, fit="cover", alt="a dark gradient plate")
    *_r4, ink4 = dk.frosted_panel(s4, bd4, 0.6, 1.0, 5.0, 3.0)
    lum4, kind4 = glass_lum(s4)
    check(kind4 == "picture" and lum4 < 90, "glass over a real gradient must be a dark blurred "
          "picture, got {} at {}".format(kind4, lum4))
    # a mid-tone photo region (plate 40-90, so a 30% white wash spans ~104-139 — black fails the
    # dark end, white the light end): no ink clears 4.5:1 at a 30% wash, so the
    # DEFAULT (alpha=None) must pick the smallest wash that does — and report it — while an
    # explicit alpha that cannot work is still refused
    src5 = td / "mid.png"
    im5 = Image.new("RGB", (1600, 900))
    im5.putdata([(40 + (x * 50) // 1600,) * 3 for y in range(900) for x in range(1600)])
    im5.save(src5)
    s5 = dk.add_slide(prs)
    bd5 = dk.picture(s5, str(src5), 0, 0, 13.333, 7.5, fit="cover", alt="a mid-tone plate")
    try:
        dk.frosted_panel(s5, bd5, 0.3, 1.0, 12.7, 2.0, alpha=0.30)   # spans the whole ramp
        fails.append("an explicit alpha=0.30 on mid-tone glass was accepted (no ink clears 4.5:1)")
    except ValueError:
        pass
    s6 = dk.add_slide(prs)
    bd6 = dk.picture(s6, str(src5), 0, 0, 13.333, 7.5, fit="cover", alt="a mid-tone plate")
    try:
        *_r6, ink6 = dk.frosted_panel(s6, bd6, 0.3, 1.0, 12.7, 2.0)
        # measured on the ARTIFACT: the blurred plate in the file, blended with the wash alpha the
        # file declares, judged at its 10th/90th percentile — the ink must clear 4.5:1 on both.
        # (The lightest passing wash may be BELOW the refused 0.30: contrast is not monotonic in
        # the wash — a light wash keeps white ink legible, a mid wash fails both inks.)
        plate, wash = list(s6.shapes)[-2], list(s6.shapes)[-1]
        a_used = int(wash._element.xml.split('<a:alpha val="')[1].split('"')[0]) / 100000.0
        g6 = Image.open(io.BytesIO(plate.image.blob)).convert("RGB")
        comp = Image.blend(g6, Image.new("RGB", g6.size, (255, 255, 255)), a_used).convert("L")
        lum6 = sorted(comp.getdata())
        ends = [lum6[int(q * (len(lum6) - 1))] for q in (0.10, 0.90)]
        worst6 = min(dk.contrast_ratio(ink6, dk.RGBColor(v, v, v)) for v in ends)
        check(worst6 >= 4.45, "auto-wash ink clears only {:.2f}:1 on the glass it drew (alpha {})"
              .format(worst6, a_used))
        check(a_used != 0.30, "the default reproduced the refused wash")
    except ValueError as e:
        fails.append("the default alpha refused a mid-tone photo it could have washed: " + str(e))
    # straddling the seam: the composite has a dark and a light side; ink must clear BOTH or refuse
    try:
        dk.frosted_panel(s, bd, 5.5, 2.0, 2.4, 2.0, alpha=0.05)
        fails.append("a panel straddling black/white with almost no tint was accepted")
    except ValueError as e:
        check("alpha" in str(e), "the refusal should tell the caller to raise alpha: " + str(e))
    # a contain-fit backdrop in a NARROWER frame is letterboxed top and bottom (a 16:9 image in an
    # 8 x 7.5 frame is placed 8 x 4.5 at y = 1.5); a panel starting at y = 1.0 sits partly over
    # the letterbox, which is not image
    s2 = dk.add_slide(prs)
    bd2 = dk.picture(s2, str(src), 0, 0, 8.0, 7.5, fit="contain", alt="a two-tone test plate")
    check(abs(bd2.top / 914400.0 - 1.5) < 0.01,
          "contain placement assumption broken: top={}".format(bd2.top / 914400.0))
    try:
        dk.frosted_panel(s2, bd2, 0.5, 1.0, 3.0, 1.5)
        fails.append("a panel over the letterbox (outside the image) was accepted")
    except ValueError as e:
        check("outside" in str(e), "the refusal should say the panel is outside the image: " + str(e))
    # refusals: rotated / masked backdrop
    rot = dk.picture(s2, str(src), 1, 1, 4, 3, fit="cover", rotation=5, alt="")
    msk = dk.picture(s2, str(src), 6, 1, 4, 3, fit="cover", shape="ellipse", alt="")
    for name, b in (("rotated", rot), ("masked", msk)):
        try:
            dk.frosted_panel(s2, b, 1.5, 1.5, 1.0, 1.0)
            fails.append("frosted_panel accepted a {} backdrop".format(name))
        except ValueError:
            pass
    # the deck still lints with no CRITICAL on the glass pages
    crit = [f for f in dk.lint_layout(prs, verbose=False)
            if f[1] == "CRITICAL" and f[0] in (1, 2, 3, 4)]
    check(not crit, "frosted panels produced CRITICAL layout findings: {}".format(crit))


# ── deferred from the final review: say which wash was used; the scaffold lints clean ──────────
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    src7 = td / "mid7.png"
    im7 = Image.new("RGB", (1600, 900))
    im7.putdata([(40 + (x * 50) // 1600,) * 3 for y in range(900) for x in range(1600)])
    im7.save(src7)
    p7 = dk.blank_deck(13.333, 7.5)
    s7 = dk.add_slide(p7)
    bd7 = dk.picture(s7, str(src7), 0, 0, 13.333, 7.5, fit="cover", alt="a mid-tone plate")
    res = dk.frosted_panel(s7, bd7, 0.3, 1.0, 12.7, 2.0)
    x7, y7, w7, h7, ink7 = res                                   # still unpacks to five
    xml_a = int(list(s7.shapes)[-1]._element.xml.split('<a:alpha val="')[1].split('"')[0]) / 100000.0
    check(abs(getattr(res, "alpha", -1) - xml_a) < 1e-6,
          "frosted_panel must report the wash it used (.alpha), got {!r}".format(getattr(res, "alpha", None)))
    # the documented scaffold (sigs) must not teach a layout the gate warns about
    import sigs  # noqa: E402
    Image.new("RGB", (1600, 900), (90, 120, 160)).save(td / "skyline.png")
    _im8 = Image.open(td / "skyline.png")
    _im8.putdata([(70 + (x * 60) // 1600, 100 + (y * 40) // 900, 150) for y in range(900) for x in range(1600)])
    _im8.save(td / "skyline.png")
    p8 = dk.blank_deck(10, 5.625)
    s8 = p8.slides.add_slide(p8.slide_layouts[6])
    import os as _os  # noqa: E402
    _cwd = _os.getcwd()
    _os.chdir(td)
    try:
        exec(compile(sigs.EXAMPLES["frosted_panel"], "<scaffold>", "exec"), {"dk": dk, "s": s8, "prs": p8})
    finally:
        _os.chdir(_cwd)
    off = [f for f in dk.lint_layout(p8, verbose=False) if f[2] == "OFFCENTER"]
    check(not off, "the frosted_panel scaffold teaches an OFFCENTER layout: {}".format(off))

# ── generalisation probe (2026-10-03): inputs the first tests never tried ──────────────────────

_dg = dk.blank_deck(13.333, 7.5)
_sgf = dk.add_slide(_dg)
try:
    dk.frosted_panel(_sgf, dk.box(_sgf, 0, 0, 3, 3, fill="888888"), 0.5, 0.5, 1, 1)
    fails.append("frosted_panel accepted a box as its backdrop")
except TypeError as e:
    check("picture" in str(e), "frosted_panel's refusal should say it needs a picture: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_frosted_panel] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
