#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contact_sheet.py — every slide on ONE image, so a critic can survey a deck in one look.

Why this exists: a critic's dominant cost is not thinking, it is LOOKING. Opening twelve
renders as twelve separate images was ~44 tool calls and ~20 minutes per lens, and a
second review round paid that bill again from scratch. Measured on a 12-slide deck:
one contact sheet + selective full-size opens cut a lens from ~12 image reads to ~4-6.

What it deliberately does NOT do is narrow the SCOPE. A fresh reviewer that is told
"only look at slides 3, 6 and 8" cannot catch the regression you introduced on slide 10,
and the whole point of a second round is that the first round's fixes are themselves
unreviewed changes. So the sheet shows ALL slides — full coverage stays intact — and the
reviewer decides for itself which pages to open at full resolution. Coverage is preserved;
only the cost per page of coverage falls.

    python3 scripts/contact_sheet.py <render-dir> [-o sheet.png] [--cols 4] [--width 2400]

Prints the sheet path and the slide->cell map, so a reviewer can name what it wants to
open next. Exit 0 = written · 2 = nothing to montage.
"""
import argparse
import os
import re
import sys

_SLIDE = re.compile(r"^slide(\d{2,})\.png$")


def slide_pngs(d):
    out = []
    for name in sorted(os.listdir(d)):
        m = _SLIDE.match(name)
        if m:
            out.append((int(m.group(1)), os.path.join(d, name)))
    return sorted(out)


def build(render_dir, out_path, cols=4, sheet_w=2400, pad=14, label_h=30):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("error: Pillow is required (pip install pillow)", file=sys.stderr)
        return 2
    pngs = slide_pngs(render_dir)
    if not pngs:
        print("error: no slideNN.png in %s" % render_dir, file=sys.stderr)
        return 2

    cols = max(1, min(cols, len(pngs)))
    cell_w = (sheet_w - pad * (cols + 1)) // cols
    with Image.open(pngs[0][1]) as im0:
        ar = im0.width / float(im0.height)
    cell_h = int(round(cell_w / ar))
    rows = (len(pngs) + cols - 1) // cols
    sheet_h = pad + rows * (cell_h + label_h + pad)

    sheet = Image.new("RGB", (sheet_w, sheet_h), (238, 238, 238))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    mapping = []
    for i, (num, path) in enumerate(pngs):
        r, c = divmod(i, cols)
        x = pad + c * (cell_w + pad)
        y = pad + r * (cell_h + label_h + pad)
        with Image.open(path) as im:
            sheet.paste(im.convert("RGB").resize((cell_w, cell_h), Image.LANCZOS), (x, y))
        # a hairline so a white-ground slide does not bleed into the sheet's ground
        draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(170, 170, 170))
        draw.text((x + 2, y + cell_h + 5), "slide %02d" % num, fill=(40, 40, 40), font=font)
        mapping.append((num, r + 1, c + 1, os.path.basename(path)))

    sheet.save(out_path)
    print("contact sheet: %s  (%d slides, %dx%d grid, %dx%d px)"
          % (out_path, len(pngs), rows, cols, sheet.width, sheet.height))
    print("open it ONCE to survey the whole deck, then open individual slides at full size "
          "only where something looks wrong:")
    for num, r, c, base in mapping:
        print("  slide %02d  row %d col %d  ->  %s/%s" % (num, r, c, render_dir, base))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("render_dir")
    ap.add_argument("-o", "--out", default=None, help="default: <render-dir>/_contact_sheet.png")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--width", type=int, default=2400, help="sheet width in px (default 2400)")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.render_dir):
        print("error: not a directory: %s" % a.render_dir, file=sys.stderr)
        return 2
    out = a.out or os.path.join(a.render_dir, "_contact_sheet.png")
    return build(a.render_dir, out, cols=a.cols, sheet_w=a.width)


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
