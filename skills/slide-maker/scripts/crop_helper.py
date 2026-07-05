#!/usr/bin/env python3
"""crop_helper — crop a figure out of a larger image *by looking*, not by guessing.

The skill's figure rule is "use the source's own figure, whole" — but often the figure
you want is a *region* of a bigger image: one panel of a multi-panel figure, a few columns
of a comparison grid, a plot lifted off a page you already rasterised with extract_pdf.py.
The failure mode is cropping **blind** — eyeballing fraction coordinates, getting them
wrong, and shipping a crop that clips a column or includes a neighbour. This tool removes
the guessing: overlay a labelled ruler, *read* the box off it, crop, then *re-view* the
crop to confirm. You look at pixels at every step instead of trusting a number you made up.

Works on ANY image (a PNG you already have, or a page from extract_pdf.py `page`) — it is
not PDF-specific. For a figure still inside a PDF, run extract_pdf.py first to get a PNG,
then crop here.

THE LOOP (do this, don't skip the verify):
  1. python crop_helper.py grid figure.png _grid.png          # ruler overlay
  2. Read _grid.png — read the crop box off the labelled lines (fractions or pixels).
  3. python crop_helper.py crop figure.png out.png 0.05 0.1 0.62 0.95 --frac
  4. Read out.png — does it contain exactly the region you wanted, nothing clipped? If
     not, adjust the box and redo step 3. One or two iterations beats one blind guess.

COMPARISON / PANEL GRIDS (the hard case — e.g. a paper's N-method × M-modality figure):
A dense grid (many columns of methods, a few rows of examples) is unreadable shrunk onto a
slide. Don't crop one ragged rectangle — keep only the columns/rows that make your point
and reassemble them into a compact figure, preserving the header row and the row-label
column. `panel` does this on a *regularly* spaced grid:
  # First overlay the cell indices and CHECK the lines land on real cell boundaries:
  python crop_helper.py panel fig.png _idx.png --grid 5x10 --xpad 0.06 --ypad 0.05
  # Then reassemble keeping the label col + header row + chosen content cols/rows:
  python crop_helper.py panel fig.png out.png --grid 5x10 --xpad 0.06 --ypad 0.05 \
         --keep-cols 0,1,3,9 --keep-rows 0,2,3
  --grid RxC      content area is R rows x C columns of equal cells (excl. the margins below)
  --xpad f        width fraction of the left ROW-LABEL margin (0 if none); always kept
  --ypad f        height fraction of the top COLUMN-HEADER margin (0 if none); always kept
  --keep-cols     0-based content column indices to keep, in output order (omit = overlay only)
  --keep-rows     0-based content row indices to keep (omit = keep all rows)
Tune --xpad/--ypad until the overlaid grid lines sit exactly on the gaps between cells
(that's why you view _idx.png first) — then the reassembly slices cleanly.

Importable: from crop_helper import crop, draw_grid, panel_pick.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

try:
    import numpy as np
except Exception:
    np = None


def _font(px):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except Exception:
                pass
    return ImageFont.load_default()


def info(path):
    w, h = Image.open(path).size
    print(f"{path}: {w} x {h} px  (aspect {w/h:.3f})")
    return w, h


def trim(path, out=None, margin=0.01, thresh=25):
    """Snap a crop to its real content — remove the uniform background border so the figure
    is tight, WITHOUT ever clipping the figure's own parts. This is background-subtraction,
    not PIL.getbbox() (which assumes a pure-black bg and trips on JPEG noise). Works for
    light- AND dark-background figures: the bg colour is estimated from the corners, so a
    plot on white and a vessel image on black both trim correctly.

    margin: fraction of the larger side added back on every side (default 1%), so anti-aliased
    edges, axis ticks, colour bars and legends are never shaved. thresh: per-pixel distance
    from bg (0-255) to count as content; raise for JPEG-noisy inputs.

    Returns the cropped box (left, upper, right, lower) in pixels, or None if the image is
    blank / trimming would be degenerate (then the original is left as-is)."""
    im = Image.open(path).convert("RGB")
    W, H = im.size
    if np is None:                      # numpy missing — safe no-op, keep the image
        if out and out != path: im.save(out)
        print("numpy unavailable — trim skipped"); return None
    a = np.asarray(im).astype(np.int16)
    # estimate background from the four corner patches (median is robust to a stray tick)
    k = max(4, min(W, H) // 50)
    corners = np.concatenate([a[:k, :k].reshape(-1, 3), a[:k, -k:].reshape(-1, 3),
                              a[-k:, :k].reshape(-1, 3), a[-k:, -k:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    dist = np.abs(a - bg).max(axis=2)               # per-pixel distance from bg
    mask = dist > thresh
    if not mask.any():
        if out and out != path: im.save(out)
        print(f"{path}: no content above threshold — left as-is"); return None
    ys, xs = np.where(mask.any(axis=1))[0], np.where(mask.any(axis=0))[0]
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    # guard: a near-full box means the bg estimate/threshold failed — don't risk a bad trim
    if (y1 - y0) * (x1 - x0) > 0.985 * W * H:
        if out and out != path: im.save(out)
        print(f"{path}: already tight (content fills frame) — left as-is"); return None
    m = max(4, int(margin * max(W, H)))
    box = (max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m))
    im.crop(box).save(out or path)
    print(f"wrote {out or path}  ({box[2]-box[0]}x{box[3]-box[1]}px, trimmed from {W}x{H}) "
          f"— content fully retained, only background removed.")
    return box


def draw_grid(path, out, step=0.1):
    """Overlay a labelled ruler: lines every `step` fraction, tagged with both the
    fraction (0..1) and the pixel coordinate, so you can read a crop box straight off it."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    d = ImageDraw.Draw(im, "RGBA")
    f = _font(max(11, w // 90))
    red, grid = (220, 30, 30, 255), (0, 150, 255, 110)
    n = int(round(1 / step))
    for i in range(n + 1):
        fx = i * step
        x = min(int(fx * w), w - 1)
        d.line([(x, 0), (x, h)], fill=grid, width=1)
        d.text((x + 2, 2), f"{fx:.2f}", fill=red, font=f)
        d.text((x + 2, h - f.size - 2), f"{x}px", fill=red, font=f)
        y = min(int(fx * h), h - 1)
        d.line([(0, y), (w, y)], fill=grid, width=1)
        d.text((2, y + 1), f"{fx:.2f}", fill=red, font=f)
        d.text((w - 5 * f.size, y + 1), f"{y}px", fill=red, font=f)
    im.save(out)
    print(f"wrote {out}  ({w}x{h}px) — read the crop box off the red labels, then `crop`.")
    return out


def crop(path, out, x0, y0, x1, y1, frac=False):
    """Crop a box (pixels, or fractions 0..1 with frac=True) and report the result so you
    can immediately view it and confirm nothing's clipped."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if frac:
        x0, y0, x1, y1 = x0 * w, y0 * h, x1 * w, y1 * h
    box = (int(x0), int(y0), int(x1), int(y1))
    c = im.crop(box)
    c.save(out)
    print(f"wrote {out}  ({c.size[0]}x{c.size[1]}px from box {box}) — VIEW it to verify.")
    return out


def panel_pick(path, out, rows, cols, xpad=0.0, ypad=0.0, keep_cols=None, keep_rows=None):
    """Regular-grid panel tool. With no keep_cols: overlay numbered cell indices so you can
    confirm the grid lines fall on real cell boundaries. With keep_cols: reassemble a
    compact figure = [label margin] + chosen content columns, [header margin] + chosen
    content rows."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    x_off, y_off = int(xpad * w), int(ypad * h)
    cw = (w - x_off) / cols
    ch = (h - y_off) / rows

    if not keep_cols:                      # overlay mode — verify the grid first
        d = ImageDraw.Draw(im, "RGBA")
        f = _font(max(13, w // 70))
        for c in range(cols + 1):
            x = int(x_off + c * cw)
            d.line([(x, 0), (x, h)], fill=(255, 0, 0, 180), width=2)
        for r in range(rows + 1):
            y = int(y_off + r * ch)
            d.line([(0, y), (w, y)], fill=(255, 0, 0, 180), width=2)
        if x_off:
            d.line([(x_off, 0), (x_off, h)], fill=(0, 200, 0, 220), width=3)
        if y_off:
            d.line([(0, y_off), (w, y_off)], fill=(0, 200, 0, 220), width=3)
        for r in range(rows):
            for c in range(cols):
                cx, cy = int(x_off + c * cw + 4), int(y_off + r * ch + 4)
                d.text((cx, cy), f"r{r}c{c}", fill=(255, 230, 0, 255), font=f)
        im.save(out)
        print(f"wrote {out} — green = label/header margins, red = cell grid. Check the "
              f"lines sit on the gaps between cells; adjust --xpad/--ypad/--grid if not, "
              f"then add --keep-cols.")
        return out

    keep_cols = [int(c) for c in keep_cols]
    keep_rows = [int(r) for r in keep_rows] if keep_rows else list(range(rows))
    label = im.crop((0, 0, x_off, h)) if x_off else None
    header = im.crop((0, 0, w, y_off)) if y_off else None

    def col_box(c):
        return (int(x_off + c * cw), int(x_off + (c + 1) * cw))
    def row_box(r):
        return (int(y_off + r * ch), int(y_off + (r + 1) * ch))

    # build output width/height from kept columns/rows (+ margins)
    out_w = x_off + sum(col_box(c)[1] - col_box(c)[0] for c in keep_cols)
    out_h = y_off + sum(row_box(r)[1] - row_box(r)[0] for r in keep_rows)
    canvas = Image.new("RGB", (out_w, out_h), (255, 255, 255))

    # paste header strip (sliced to kept columns) and label strip (sliced to kept rows)
    if header is not None:
        x = x_off
        for c in keep_cols:
            a, b = col_box(c)
            canvas.paste(header.crop((a, 0, b, y_off)), (x, 0)); x += b - a
    if label is not None:
        y = y_off
        for r in keep_rows:
            a, b = row_box(r)
            canvas.paste(label.crop((0, a, x_off, b)), (0, y)); y += b - a
    # paste the content cells
    y = y_off
    for r in keep_rows:
        ra, rb = row_box(r)
        x = x_off
        for c in keep_cols:
            ca, cb = col_box(c)
            canvas.paste(im.crop((ca, ra, cb, rb)), (x, y)); x += cb - ca
        y += rb - ra
    canvas.save(out)
    print(f"wrote {out}  ({out_w}x{out_h}px; kept cols {keep_cols}, rows {keep_rows}) "
          f"— VIEW it to verify the headers/labels still line up with their columns/rows.")
    return out


def _main(argv):
    if len(argv) < 2:
        print(__doc__); return 1
    cmd, a = argv[1], argv[2:]
    flags, pos = {}, []
    i = 0
    while i < len(a):
        t = a[i]
        if t == "--frac": flags["frac"] = True; i += 1
        elif t == "--snap": flags["snap"] = True; i += 1
        elif t == "--step": flags["step"] = float(a[i+1]); i += 2
        elif t == "--margin": flags["margin"] = float(a[i+1]); i += 2
        elif t == "--thresh": flags["thresh"] = float(a[i+1]); i += 2
        elif t == "--grid": flags["grid"] = a[i+1]; i += 2
        elif t == "--xpad": flags["xpad"] = float(a[i+1]); i += 2
        elif t == "--ypad": flags["ypad"] = float(a[i+1]); i += 2
        elif t == "--keep-cols": flags["keep_cols"] = a[i+1].split(","); i += 2
        elif t == "--keep-rows": flags["keep_rows"] = a[i+1].split(","); i += 2
        else: pos.append(t); i += 1
    if cmd == "info":
        info(pos[0])
    elif cmd == "grid":
        draw_grid(pos[0], pos[1], step=flags.get("step", 0.1))
    elif cmd == "trim":
        trim(pos[0], pos[1] if len(pos) > 1 else None,
             margin=flags.get("margin", 0.01), thresh=flags.get("thresh", 25))
    elif cmd == "crop":
        crop(pos[0], pos[1], *map(float, pos[2:6]), frac=flags.get("frac", False))
        if flags.get("snap"):
            trim(pos[1], pos[1], margin=flags.get("margin", 0.01),
                 thresh=flags.get("thresh", 25))
    elif cmd == "panel":
        r, c = (int(x) for x in flags["grid"].lower().split("x"))
        panel_pick(pos[0], pos[1], r, c, xpad=flags.get("xpad", 0.0),
                   ypad=flags.get("ypad", 0.0), keep_cols=flags.get("keep_cols"),
                   keep_rows=flags.get("keep_rows"))
    else:
        print(__doc__); return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
