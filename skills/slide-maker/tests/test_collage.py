#!/usr/bin/env python3
"""collage: 1-4 tilted, taped prints with bounded overlap that never enter the text-safe rect; deterministic for a seed; every canvas."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk, collage, rotgeom
from PIL import Image
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    paths = []
    for i, col in enumerate([(180, 90, 60), (60, 120, 160), (200, 180, 90), (90, 150, 90)]):
        p = td / "p{}.png".format(i)
        im = Image.new("RGB", (400, 300), col)
        im.putdata([tuple(min(255, c + (x * 7 + y * 5) % 60) for c in col) for y in range(300) for x in range(400)])
        im.save(p)
        paths.append(str(p))
    for W, H in ((13.333, 7.5), (10.0, 5.625), (5.625, 10.0), (7.5, 7.5)):
        prs = dk.blank_deck(W, H)
        dk.set_ground("EFE6D2")
        s = dk.add_slide(prs)
        region = (W * 0.42, H * 0.08, W * 0.52, H * 0.84) if W > H else (W * 0.06, H * 0.40, W * 0.88, H * 0.55)
        keep = (W * 0.05, H * 0.08, W * 0.34, H * 0.5) if W > H else (W * 0.06, H * 0.05, W * 0.88, H * 0.30)
        for n in (1, 2, 3, 4):
            s2 = dk.add_slide(prs)
            pics = collage.collage(s2, region, [{"path": p, "alt": "photo {}".format(i)} for i, p in enumerate(paths[:n])],
                                   seed=n, keep_clear=keep)
            check(len(pics) == n, "{}x{} n={}: {} prints".format(W, H, n, len(pics)))
            for pic in pics:
                E = 914400.0
                poly = rotgeom.corners(pic.left / E, pic.top / E, pic.width / E, pic.height / E, pic.rotation)
                area, _bb = rotgeom.overlap(poly, rotgeom.rect_poly(*keep))
                check(area < 1e-6, "{}x{} n={}: a print entered keep_clear ({:.3f} in2)".format(W, H, n, area))
                check(dk._declared_overlap(pic), "prints are declared overlap")
            # prints overlap a little, never by more than 25% of the smaller one (a covered photo
            # says nothing — measured: a portrait 3-print stack hid most of the first photo)
            polys = [rotgeom.corners(p_.left / E, p_.top / E, p_.width / E, p_.height / E, p_.rotation) for p_ in pics]
            for a in range(len(polys)):
                for b in range(a + 1, len(polys)):
                    ov, _ = rotgeom.overlap(polys[a], polys[b])
                    small = min(rotgeom.area(polys[a]), rotgeom.area(polys[b]))
                    check(ov <= 0.25 * small + 1e-6, "{}x{} n={}: prints {} and {} overlap {:.0%} of the smaller".format(W, H, n, a, b, ov / small))
            # the stack uses its region: its painted extent spans at least 70% of the region's width and height
            xs = [pt[0] for poly in polys for pt in poly]
            ys = [pt[1] for poly in polys for pt in poly]
            if n > 1:
                check((max(xs) - min(xs)) >= 0.7 * region[2] and (max(ys) - min(ys)) >= 0.7 * region[3],
                      "{}x{} n={}: the prints leave most of the region empty".format(W, H, n))
        prs.save(str(td / "c{}x{}.pptx".format(W, H)))
        crit = [f for f in dk.lint_layout(prs, strict=True, verbose=False) if f[1] == "CRITICAL"]
        check(not crit, "lint: no critical at {}x{}".format(W, H))
    prs = dk.blank_deck(13.333, 7.5)
    s = dk.add_slide(prs)
    a = [sh.rotation for sh in collage.collage(s, (6, 0.6, 6.6, 6.2), paths[:3], seed=7)]
    s = dk.add_slide(prs)
    b = [sh.rotation for sh in collage.collage(s, (6, 0.6, 6.6, 6.2), paths[:3], seed=7)]
    check(a == b, "deterministic for a seed")
    for bad in ([], paths + paths[:1]):
        try:
            collage.collage(s, (6, 0.6, 6.6, 6.2), bad)
            fails.append("collage accepted {} items".format(len(bad)))
        except ValueError:
            pass
    try:
        collage.collage(s, (0.5, 0.5, 1.2, 1.0), paths[:3])
        fails.append("collage accepted a region too small for 3 prints")
    except ValueError:
        pass

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_collage] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
