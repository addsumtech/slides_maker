#!/usr/bin/env python3
"""Measure what a program CAN measure about a candidate photo — and make LOOKING cheap.

`references/image-generation.md` step 2 tells the model to vet a sourced photo before placing it:
watermark-free, subject-correct, and *aesthetically usable* (no scaffolding, no ugly snapshot, no
wrong preparation). That instruction is right and stays with the model — none of it is decidable
by a program, and this file does not pretend otherwise.

What IS decidable was never checked anywhere:

  * **EXIF rotation.** MEASURED here, end to end: a JPEG carrying `Orientation=6` was embedded with
    `deckkit.picture(fit="contain")` and rendered through this skill's own LibreOffice loop — it
    came out UNROTATED, and the contain-fit was computed from the stored 600x300 rather than the
    displayed 300x600. So a phone/Commons photo lands sideways in a box sized for the other
    aspect, and every existing gate is green: the picture decodes, it fills its box, nothing
    overflows. `--fix` bakes the rotation into the pixels, which is the only reliable fix.
  * **Resolution against the box it is planned for.** 1024px is fine in a thumbnail and mush at
    13.3in wide. The cost of finding out is a whole render + review round.
  * **Crop loss.** A 2:3 portrait in a 16:9 full-bleed slot loses ~62% of its frame; the subject
    usually goes with it.
  * **Softness, flat plates, letterbox bars, near-duplicates.** Each ships silently: `ASSET NOT
    USABLE` (lint_deck) only sees a picture that fails to decode or is blank.

`--contact-sheet` writes ONE labelled PNG of every candidate with its licence and flags, and
prints its sha256, because "look at each file" is a step that gets skipped and "open this one
image" is not. The sha256 is what a critic's consent can name (`review-looks-as-artifacts`).

    python3 scripts/image_qc.py <dir-or-file> [--at 13.33x7.5] [--box 16:9] [--contact-sheet]
    python3 scripts/image_qc.py assets/sourced --at 6.2x4.0 --fix
    python3 scripts/image_qc.py --selftest

Exit 0 clean · 1 findings · 2 could not run (never silently "clean").
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")

# ---- thresholds. Each is a JUDGEMENT with a reason, and each is overridable, because a wrong
# threshold that cannot be moved turns a real check into noise everybody learns to ignore.
MIN_DPI = 96.0          # a 16:9 slide projected at 1920px wide is ~144dpi at 13.3in; 96 is the
                        # floor where softness starts being visible on a projector, not a screen.
SOFT_VAR = 60.0         # Laplacian variance on the 512px-normalised luma. Below this, a photo
                        # reads soft at full-bleed size; scanned/older Commons files sit here.
FLAT_STD = 12.0         # luma std — a failed generation or a placeholder plate is nearly uniform.
LETTERBOX_FRAC = 0.035  # a uniform band ≥3.5% of the edge is a bar, not a sky.
DUP_HAMMING = 8         # dHash distance; ≤8 of 64 bits is "the same photo again".


def _need(mod):
    try:
        return __import__(mod)
    except ImportError:
        print("cannot run: {} is required (pip install -r requirements.txt)".format(mod),
              file=sys.stderr)
        raise SystemExit(2)


# --------------------------------------------------------------------------- measurement

def _load(path):
    from PIL import Image, ImageOps
    im = Image.open(path)
    im.load()
    orient = 1
    try:
        orient = int(im.getexif().get(274, 1) or 1)
    except Exception:
        orient = 1
    # Every measurement below is taken on the ORIENTED image, because that is what a viewer that
    # honours EXIF shows — while the flag itself is reported separately, because this skill's own
    # renderer does not honour it.
    return ImageOps.exif_transpose(im), orient


def _gray_array(im, side=512):
    np = _need("numpy")
    g = im.convert("L")
    w, h = g.size
    if max(w, h) > side:
        s = side / float(max(w, h))
        g = g.resize((max(1, int(w * s)), max(1, int(h * s))))
    return np.asarray(g, dtype="float32")


def _laplacian_var(a):
    np = _need("numpy")
    # 4-neighbour Laplacian, interior only — no scipy dependency for one convolution.
    lap = (-4.0 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:])
    return float(np.var(lap))


def _saturation(im, side=128):
    """Mean chroma, 0-1. Cheap, and enough to tell a monochrome photo from a colour one."""
    np = _need("numpy")
    rgb = im.convert("RGB")
    w, h = rgb.size
    if max(w, h) > side:
        sc = side / float(max(w, h))
        rgb = rgb.resize((max(1, int(w * sc)), max(1, int(h * sc))))
    a = np.asarray(rgb, dtype="float32") / 255.0
    mx, mn = a.max(axis=2), a.min(axis=2)
    return float(np.mean(np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)))


def _dhash(im, size=8):
    """Perceptual hash. Returns (bits, has_structure).

    `has_structure` is load-bearing, found by the self-test: fine-grained texture (noise, foliage,
    a crowd, a gravel road) averages to a nearly UNIFORM thumbnail, so every such photo hashes
    alike and a whole candidate set reports as duplicates of each other. A hash with nothing to
    compare must abstain, not answer — a false NEAR DUPLICATE would push a run to delete a photo
    that is nothing like the other one."""
    g = im.convert("L").resize((size + 1, size))
    px = list(g.getdata())
    lo, hi = min(px), max(px)
    bits = 0
    for r in range(size):
        row = px[r * (size + 1):(r + 1) * (size + 1)]
        for c in range(size):
            bits = (bits << 1) | (1 if row[c] < row[c + 1] else 0)
    return bits, (hi - lo) >= 12


def _hamming(a, b):
    return bin(a ^ b).count("1")


def _edge_bars(a):
    """Fraction of the frame taken by uniform bands at top/bottom and left/right."""
    np = _need("numpy")
    h, w = a.shape

    def scan(lines):
        n = 0
        for i in lines:
            if float(np.std(a[i] if a.ndim == 2 and len(a[i].shape) == 1 else a[i])) < 3.0:
                n += 1
            else:
                break
        return n

    top = scan(range(h))
    bot = scan(range(h - 1, -1, -1))
    left = scan(list(a.T)) if False else 0
    at = a.T
    left = 0
    for i in range(at.shape[0]):
        if float(np.std(at[i])) < 3.0:
            left += 1
        else:
            break
    right = 0
    for i in range(at.shape[0] - 1, -1, -1):
        if float(np.std(at[i])) < 3.0:
            right += 1
        else:
            break
    # A fully uniform image is a FLAT PLATE, not a letterbox — scanning would claim 100% bars.
    if top >= h or left >= at.shape[0]:
        return 0.0, 0.0
    return (top + bot) / float(h), (left + right) / float(at.shape[0])


def _corner_energy(a):
    """Ratio of high-frequency energy in the outer band to the centre.

    A HEURISTIC for watermarks/stock overlays, and deliberately reported as `possible`: a photo
    with a busy border and a plain sky centre scores the same way. It exists to make a human LOOK
    at a specific file, never to clear or condemn one on its own."""
    np = _need("numpy")
    h, w = a.shape
    if h < 32 or w < 32:
        return 0.0
    lap = abs(-4.0 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:])
    hh, ww = lap.shape
    by, bx = max(1, hh // 8), max(1, ww // 8)
    centre = lap[by * 2:hh - by * 2, bx * 2:ww - bx * 2]
    band = float(np.mean(lap[:by, :]) + np.mean(lap[-by:, :]) +
                 np.mean(lap[:, :bx]) + np.mean(lap[:, -bx:])) / 4.0
    c = float(np.mean(centre)) if centre.size else 0.0
    return band / c if c > 1e-6 else 0.0


def _aspect_loss(src_wh, box_wh):
    """Fraction of the SOURCE frame lost when filling `box_wh` (cover-fit)."""
    sw, sh = src_wh
    bw, bh = box_wh
    if not (sw and sh and bw and bh):
        return 0.0
    src_ar, box_ar = sw / float(sh), bw / float(bh)
    if abs(src_ar - box_ar) < 1e-6:
        return 0.0
    if src_ar > box_ar:                      # too wide: crop the sides
        return 1.0 - (box_ar / src_ar)
    return 1.0 - (src_ar / box_ar)           # too tall: crop top/bottom


def _parse_box(at, box):
    """--at WxH in inches (the planned box) or --box W:H (aspect only, full-bleed)."""
    if at:
        w, h = (float(x) for x in at.lower().replace("in", "").split("x"))
        return w, h
    if box:
        a, b = (float(x) for x in box.replace("/", ":").split(":"))
        return a, b
    return None


def inspect(path, *, box=None, dpi_floor=MIN_DPI, soft_var=SOFT_VAR):
    """Return a findings dict for ONE file. Never raises on a bad file — reports it."""
    rec = {"file": os.path.basename(str(path)), "path": str(path), "flags": [], "notes": {}}
    try:
        im, orient = _load(path)
    except Exception as exc:
        rec["flags"].append(("UNREADABLE", "{}: {}".format(type(exc).__name__, exc)))
        return rec
    w, h = im.size
    rec["notes"].update({"w": w, "h": h, "mode": im.mode, "exif_orientation": orient})
    try:
        rec["notes"]["sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        pass

    if orient not in (0, 1):
        rec["flags"].append((
            "EXIF ROTATION",
            "the file says Orientation={} but this skill's render loop ignores it (measured) — the "
            "photo will appear sideways and `fit=` will size it from the WRONG aspect. Re-save it "
            "with the rotation baked in: image_qc.py <file> --fix".format(orient)))

    if box:
        bw, bh = box
        loss = _aspect_loss((w, h), (bw, bh))
        rec["notes"]["crop_loss"] = round(loss, 3)
        if loss > 0.45:
            rec["flags"].append((
                "CROP LOSS",
                "{:.0f}% of the frame is cut to fill a {:.2f}x{:.2f} box — the subject usually goes "
                "with it. Choose a candidate nearer that aspect, or place it in a box that fits the "
                "photo.".format(loss * 100, bw, bh)))
        if bw > 3.0:                       # inches -> a real placement box, so DPI is meaningful
            dpi = min(w / bw, h / bh)
            rec["notes"]["dpi_at_box"] = round(dpi, 1)
            if dpi < dpi_floor:
                rec["flags"].append((
                    "TOO SMALL",
                    "{:.0f} dpi in a {:.2f}x{:.2f}in box (floor {:.0f}) — it will read soft on a "
                    "projector. Source a larger file or shrink the box.".format(dpi, bw, bh, dpi_floor)))

    a = _gray_array(im)
    np = _need("numpy")
    var = _laplacian_var(a)
    std = float(np.std(a))
    rec["notes"].update({"laplacian_var": round(var, 1), "luma_std": round(std, 1)})
    if std < FLAT_STD:
        rec["flags"].append((
            "FLAT PLATE",
            "almost no tonal variation (luma std {:.1f}) — the signature of a failed generation, a "
            "placeholder, or a solid colour saved as a photo.".format(std)))
    elif var < soft_var:
        rec["flags"].append((
            "SOFT",
            "low detail energy (Laplacian variance {:.0f} < {:.0f}) — blurred, upscaled, or a "
            "compressed re-upload. It will not survive a full-bleed placement.".format(var, soft_var)))

    v_bars, h_bars = _edge_bars(a)
    rec["notes"]["bars"] = (round(v_bars, 3), round(h_bars, 3))
    if max(v_bars, h_bars) > LETTERBOX_FRAC:
        rec["flags"].append((
            "LETTERBOX",
            "uniform bands on {} ({:.0f}% of the frame) — a screenshot or a padded export, not a "
            "photograph. Crop the bars (crop_helper.py trim) before placing.".format(
                "top/bottom" if v_bars >= h_bars else "left/right", max(v_bars, h_bars) * 100)))

    ce = _corner_energy(a)
    rec["notes"]["edge_energy_ratio"] = round(ce, 2)
    if ce > 2.2:
        rec["flags"].append((
            "POSSIBLE WATERMARK",
            "the outer band carries {:.1f}x the detail of the centre — often a stock overlay, a "
            "photographer stamp or a site logo. LOOK at it: a watermark means REJECT the file, "
            "never crop or blur the mark out (that is licence circumvention).".format(ce)))
    return rec


def inspect_dir(target, *, box=None, dpi_floor=MIN_DPI, soft_var=SOFT_VAR):
    p = Path(target)
    files = ([p] if p.is_file() else
             sorted(f for f in p.iterdir()
                    if f.suffix.lower() in EXTS and not f.name.startswith("_"))) if p.exists() else []
    # Leading underscore = this pipeline's OWN output, not a candidate: the contact sheet, and the
    # `_ref-` files generate_images_codex stages. Caught on the first real run, where the sheet
    # QC'd itself and reported LETTERBOX on its own margins — and worse, would have counted itself
    # in the set-level MIXED TREATMENT and near-duplicate passes.
    if not files:
        print("nothing to check at {} (looked for {})".format(target, ", ".join(EXTS)),
              file=sys.stderr)
        raise SystemExit(2)
    recs = [inspect(f, box=box, dpi_floor=dpi_floor, soft_var=soft_var) for f in files]

    hashes = {}
    for r in recs:
        try:
            im, _ = _load(r["path"])
            bits, structured = _dhash(im)
            if structured:
                hashes[r["file"]] = bits
            else:
                r["notes"]["dup_check"] = "skipped — too little structure to compare"
        except Exception:
            continue
    # MIXED TREATMENT — a set-level fault no per-file check can see. `image-generation.md` step 4
    # asks that mixed sources be treated to ONE register so the deck reads as one thing; a
    # monochrome Commons photo sitting between two colour ones is the commonest way that breaks,
    # and it is obvious the moment you see the contact sheet and invisible before then.
    sats = {}
    for r in recs:
        if any(f[0] == "UNREADABLE" for f in r["flags"]):
            continue
        try:
            im, _ = _load(r["path"])
            sats[r["file"]] = _saturation(im)
            r["notes"]["saturation"] = round(sats[r["file"]], 3)
        except Exception:
            continue
    mono = [f for f, v in sats.items() if v < 0.06]
    colour = [f for f, v in sats.items() if v > 0.18]
    if mono and colour:
        for r in recs:
            if r["file"] in mono:
                r["flags"].append((
                    "MIXED TREATMENT",
                    "monochrome, in a set that also holds {} colour photo(s) — mixed sources have "
                    "to read as ONE deck. Treat them all to the palette (image_fx.py duotone/gray), "
                    "or drop the odd one out.".format(len(colour))))

    names = list(hashes)
    for i, n1 in enumerate(names):
        for n2 in names[i + 1:]:
            d = _hamming(hashes[n1], hashes[n2])
            if d <= DUP_HAMMING:
                for r in recs:
                    if r["file"] == n2:
                        r["flags"].append((
                            "NEAR DUPLICATE",
                            "visually the same photo as {} (dHash distance {}) — two of the same "
                            "shot in one deck reads as padding.".format(n1, d)))
    return recs


# --------------------------------------------------------------------------- fix

def fix_orientation(path):
    """Bake EXIF rotation into the pixels. Returns True when the file was rewritten."""
    from PIL import Image, ImageOps
    im = Image.open(path)
    im.load()
    orient = int(im.getexif().get(274, 1) or 1)
    if orient in (0, 1):
        return False
    out = ImageOps.exif_transpose(im)
    exif = out.getexif()
    exif[274] = 1                            # the pixels now match; leaving the flag re-rotates
    params = {}
    if str(path).lower().endswith((".jpg", ".jpeg")):
        # `subsampling="keep"` is not available here: exif_transpose returns a NEW image that is
        # no longer a JpegImageFile, so PIL refuses. 4:4:4 at q95 is the safe re-encode — this
        # runs once, on a file that was going to be re-saved anyway.
        params = {"quality": 95, "subsampling": 0}
    out.save(path, exif=exif.tobytes(), **params)
    return True


# --------------------------------------------------------------------------- contact sheet

def _label_font(px, sample=""):
    """A face that can draw the label — including a CJK filename, which the PIL default cannot."""
    from PIL import ImageFont
    cands = []
    if any("⺀" <= c <= "鿿" or "぀" <= c <= "ヿ" for c in sample):
        cands = ["/System/Library/Fonts/PingFang.ttc",
                 "/System/Library/Fonts/Hiragino Sans GB.ttc",
                 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                 "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]
    cands += ["/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, px)
            except Exception:
                continue
    return ImageFont.load_default()


def contact_sheet(recs, out_path, *, cols=3, cell=460, ledger=None):
    """ONE labelled PNG of every candidate. Looking must cost a single Read, or it does not happen."""
    from PIL import Image, ImageDraw
    lic = {}
    if ledger:
        for e in ledger.get("entries", []):
            lic[e.get("file")] = "{} · {}".format(e.get("license", "?"), e.get("source", "?"))
    pad, label_h = 14, 74
    rows = (len(recs) + cols - 1) // cols
    W = cols * (cell + pad) + pad
    H = rows * (cell + label_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (245, 245, 247))
    d = ImageDraw.Draw(sheet)
    for i, r in enumerate(recs):
        cx = pad + (i % cols) * (cell + pad)
        cy = pad + (i // cols) * (cell + label_h + pad)
        d.rectangle([cx, cy, cx + cell, cy + cell], fill=(225, 225, 230))
        try:
            im, _ = _load(r["path"])
            im.thumbnail((cell, cell))
            sheet.paste(im.convert("RGB"), (cx + (cell - im.size[0]) // 2,
                                            cy + (cell - im.size[1]) // 2))
        except Exception:
            d.text((cx + 12, cy + 12), "UNREADABLE", fill=(180, 30, 30), font=_label_font(18))
        n = r["notes"]
        line1 = "[{}] {}".format(i + 1, r["file"][:44])
        line2 = "{}x{}  {}".format(n.get("w", "?"), n.get("h", "?"), lic.get(r["file"], ""))[:64]
        flags = ", ".join(f[0] for f in r["flags"])
        d.text((cx + 2, cy + cell + 6), line1, fill=(20, 20, 24), font=_label_font(15, line1))
        d.text((cx + 2, cy + cell + 26), line2, fill=(90, 90, 100), font=_label_font(13, line2))
        if flags:
            d.text((cx + 2, cy + cell + 46), flags[:70], fill=(190, 40, 40), font=_label_font(13))
        else:
            d.text((cx + 2, cy + cell + 46), "no measurable defect — your EYES decide the rest",
                   fill=(60, 130, 80), font=_label_font(13))
    out_path = Path(out_path)
    sheet.save(out_path)
    return out_path, hashlib.sha256(out_path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- selftest

def _selftest():
    import tempfile
    from PIL import Image
    _need("numpy")
    ok, bad = [], []
    tmp = Path(tempfile.mkdtemp(prefix="imgqc-"))

    import random
    from PIL import ImageDraw

    def textured(w, h, seed, blocks=90):
        """A detailed, STRUCTURED image — the ordinary photo case. Pure noise would be detailed
        but structureless, which is a different (and separately tested) thing."""
        rnd = random.Random(seed)
        im = Image.new("RGB", (w, h), (255, 255, 255))
        d = ImageDraw.Draw(im)
        for _ in range(blocks):
            x0, y0 = rnd.randrange(w), rnd.randrange(h)
            d.rectangle([x0, y0, x0 + rnd.randrange(20, w // 3), y0 + rnd.randrange(20, h // 3)],
                        fill=(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
        px = im.load()
        for y in range(0, h, 2):                       # fine grain on top of the big shapes
            for x in range(0, w, 2):
                v = rnd.randrange(-24, 25)
                r, g, b = px[x, y]
                px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)),
                            max(0, min(255, b + v)))
        return im

    noisy = textured(2400, 1600, 7)
    p_ok = tmp / "sharp.png"
    noisy.save(p_ok)

    flat = Image.new("RGB", (2400, 1600), (200, 200, 205))
    p_flat = tmp / "flat.png"
    flat.save(p_flat)

    bars = textured(2400, 1600, 11)
    for y in list(range(0, 200)) + list(range(1400, 1600)):
        for x in range(0, 2400, 3):
            bars.putpixel((x, y), (0, 0, 0))
            bars.putpixel((x + 1, y), (0, 0, 0))
            bars.putpixel((x + 2, y), (0, 0, 0))
    p_bars = tmp / "letterbox.png"
    bars.save(p_bars)

    rot = Image.new("RGB", (900, 600), "white")
    ex = rot.getexif()
    ex[274] = 6
    p_rot = tmp / "rotated.jpg"
    rot.save(p_rot, exif=ex.tobytes())

    small = textured(700, 460, 23, blocks=40)
    p_small = tmp / "small.png"
    small.save(p_small)

    def flags(rec):
        return {f[0] for f in rec["flags"]}

    r = inspect(p_ok, box=(13.33, 7.5))
    if not flags(r):
        ok.append("a large, detailed photo in a matching box is CLEAN — the checks do not fire on "
                  "the ordinary case (a check that always fires is noise)")
    else:
        bad.append("clean photo flagged: {}".format(flags(r)))

    if "FLAT PLATE" in flags(inspect(p_flat)):
        ok.append("a uniform plate is caught (failed generation / placeholder)")
    else:
        bad.append("flat plate not caught")

    if "LETTERBOX" in flags(inspect(p_bars)):
        ok.append("uniform edge bands are caught (screenshot / padded export)")
    else:
        bad.append("letterbox not caught")

    fr = inspect(p_rot)
    if "EXIF ROTATION" in flags(fr):
        ok.append("EXIF Orientation!=1 is caught BEFORE placement — measured to render sideways "
                  "and mis-fit in this skill's own render loop")
    else:
        bad.append("EXIF rotation not caught")
    if fix_orientation(p_rot) and int(Image.open(p_rot).getexif().get(274, 1)) == 1 \
            and Image.open(p_rot).size == (600, 900):
        ok.append("--fix bakes the rotation into the pixels AND clears the flag (leaving the flag "
                  "would re-rotate it in a viewer that honours EXIF)")
    else:
        bad.append("fix_orientation did not rewrite correctly")

    if "TOO SMALL" in flags(inspect(p_small, box=(13.33, 7.5))):
        ok.append("resolution is judged against the PLANNED box, not in the abstract")
    else:
        bad.append("small file not caught at full-bleed size")
    if "TOO SMALL" not in flags(inspect(p_small, box=(2.2, 1.5))):
        ok.append("...and the same file passes in a small box — the box is the question")
    else:
        bad.append("small file wrongly flagged in a small box")

    tall = textured(1200, 2600, 31)
    p_tall = tmp / "tall.png"
    tall.save(p_tall)
    if "CROP LOSS" in flags(inspect(p_tall, box=(13.33, 7.5))):
        ok.append("a portrait candidate for a 16:9 full-bleed slot is caught before it is cropped "
                  "to nothing")
    else:
        bad.append("crop loss not caught")

    dupe = tmp / "sharp-copy.png"
    dupe.write_bytes(p_ok.read_bytes())
    recs = inspect_dir(tmp)
    dup_hits = [r for r in recs if "NEAR DUPLICATE" in flags(r)]
    if dup_hits:
        ok.append("two copies of one shot in a candidate set are reported once, on the second")
    else:
        bad.append("near-duplicate not caught")
    if len(dup_hits) == 1:
        ok.append("...exactly once — the ORIGINAL is not also condemned")
    else:
        bad.append("duplicate reported {} times".format(len(dup_hits)))

    sheet, sha = contact_sheet(recs, tmp / "sheet.png")
    if sheet.exists() and len(sha) == 64:
        ok.append("the contact sheet is one artifact with a sha256 a review can name")
    else:
        bad.append("contact sheet not produced")

    broken = tmp / "broken.png"
    broken.write_bytes(b"not an image at all")
    if "UNREADABLE" in flags(inspect(broken)):
        ok.append("an undecodable file is REPORTED, not crashed on — the run must not die on one "
                  "bad download")
    else:
        bad.append("undecodable file not reported")

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


# --------------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="Image file or directory of candidates.")
    ap.add_argument("--at", help="The PLANNED box in inches, WxH (e.g. 6.2x4.0) — resolution and "
                                 "crop loss are meaningless without it.")
    ap.add_argument("--box", help="Aspect only, W:H (e.g. 16:9) when the plate is full-bleed.")
    ap.add_argument("--dpi-floor", type=float, default=MIN_DPI)
    ap.add_argument("--soft-var", type=float, default=SOFT_VAR)
    ap.add_argument("--fix", action="store_true", help="Bake EXIF rotation into flagged files.")
    ap.add_argument("--contact-sheet", nargs="?", const="_contact_sheet.png",
                    help="Write ONE labelled sheet of every candidate (default _contact_sheet.png "
                         "in the target directory) and print its sha256.")
    ap.add_argument("--json", help="Write the findings as JSON.")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return _selftest()
    if not a.target:
        ap.print_help()
        return 2
    _need("PIL")
    try:
        box = _parse_box(a.at, a.box)
    except ValueError:
        print("cannot parse --at/--box: use --at 6.2x4.0 (inches) or --box 16:9", file=sys.stderr)
        return 2

    recs = inspect_dir(a.target, box=box, dpi_floor=a.dpi_floor, soft_var=a.soft_var)

    if a.fix:
        for r in recs:
            if any(f[0] == "EXIF ROTATION" for f in r["flags"]):
                if fix_orientation(r["path"]):
                    print("  fixed orientation: {}".format(r["file"]))
        recs = inspect_dir(a.target, box=box, dpi_floor=a.dpi_floor, soft_var=a.soft_var)

    n_flag = sum(1 for r in recs if r["flags"])
    for r in recs:
        head = "  {}  {}x{}".format(r["file"], r["notes"].get("w", "?"), r["notes"].get("h", "?"))
        if box and "dpi_at_box" in r["notes"]:
            head += "  {}dpi@box".format(r["notes"]["dpi_at_box"])
        print(head)
        for code, msg in r["flags"]:
            print("    {}: {}".format(code, msg))

    if a.contact_sheet:
        led = None
        d = Path(a.target)
        d = d if d.is_dir() else d.parent
        lp = d / "sources.json"
        if lp.exists():
            try:
                led = json.loads(lp.read_text(encoding="utf-8"))
            except ValueError:
                led = None
        out = Path(a.contact_sheet)
        if not out.is_absolute() and out.name == a.contact_sheet:
            out = d / out
        sheet, sha = contact_sheet(recs, out, ledger=led)
        print("\ncontact sheet: {}\n  sha256 {}".format(sheet, sha))
        print("  OPEN IT. The remaining checks are not a program's to make: is this the claimed "
              "subject, is it watermarked, is it under scaffolding, is it simply ugly?")

    if a.json:
        Path(a.json).write_text(json.dumps(recs, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n{} file(s), {} with findings.".format(len(recs), n_flag))
    return 1 if n_flag else 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
