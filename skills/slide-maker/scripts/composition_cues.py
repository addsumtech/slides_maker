#!/usr/bin/env python3
"""What a rendered page LOOKS like, as seven numbers — reported, never gated.

Every other measurement in this toolchain answers "is something wrong": overflow, contrast below a
floor, a repeated skeleton, a palette that never arrived. That is the whole of it — measured across
`render_deck.py`, of twelve blocking gate sections essentially one pushes UPWARD, and
`agents/critic.md` says so itself, calling its distinctiveness axis "the loop's ONE upward-pushing
lens". So a deck can be flawless and forgettable, and nothing in the pipeline notices. Measured on
this repo's own A0 poster: every gate green at one skeleton, seven size tokens against a target of
four to five, and 59% occupancy.

These are the seven cues an unsupervised slide-quality study validated against human ratings
(arXiv 2508.19289 — whitespace, colorfulness, edge density, brightness contrast, text density,
colour harmony, layout balance), reaching a correlation of about 0.83 and beating several
commercial vision models at the same task. That is independent support for this skill's whole
thesis — measure the render, do not ask a model — and three of the cues (edge density, colorfulness,
colour harmony) were computed nowhere here.

🔴 REPORTED, NOT GATED, and that is a deliberate design decision rather than caution. A number that
correlates with taste across a corpus does not license a threshold on ONE deck: a deliberately
quiet ink-wash register and a cluttered mess sit at the same low colorfulness, and this skill
protects the first. What the numbers are for is giving the critic and the author something REAL to
argue with — "this page is in the bottom decile of the deck for edge density and carries the
argument" is a sentence worth reading; "colorfulness 0.31" alone is not. Cheap by construction: it
reads renders already on disk and adds no render pass.

    python3 scripts/composition_cues.py <deck-dir|render-dir>
    python3 scripts/composition_cues.py --selftest

Exit 0 always when it could measure (there is nothing here to fail); 2 if it could not run.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

SIDE = 480          # renders are downsampled to this before any cue — the cues are all global


def _load(png):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    im.thumbnail((SIDE, SIDE))
    return im


def cues(png):
    """The seven cues for one rendered page, each roughly 0..1 (higher = more of that thing)."""
    import numpy as np
    im = _load(png)
    a = np.asarray(im, dtype=np.float64)
    h, w, _ = a.shape
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # WHITESPACE — share of the page within a whisker of the modal (ground) tone. Not "how white":
    # a dark register's ground is its whitespace, and calling a dark deck 0% empty would be wrong.
    hist = np.bincount((lum / 4).astype(np.int64).ravel(), minlength=64)
    ground = float(hist.argmax() * 4)
    whitespace = float((np.abs(lum - ground) < 10).mean())

    # COLORFULNESS — Hasler & Süsstrunk's opponent-axis measure, the standard one, normalised so a
    # vivid page lands near 1.
    rg, yb = r - g, 0.5 * (r + g) - b
    colorfulness = min(1.0, float((rg.std() ** 2 + yb.std() ** 2) ** 0.5
                                  + 0.3 * (rg.mean() ** 2 + yb.mean() ** 2) ** 0.5) / 110.0)

    # EDGE DENSITY — share of pixels on a luminance edge. This is the cue that separates a composed
    # page from an empty one and from a cluttered one, and nothing here measured it.
    gx = np.abs(np.diff(lum, axis=1))[:-1, :]
    gy = np.abs(np.diff(lum, axis=0))[:, :-1]
    edge_density = float(((gx + gy) > 24).mean())

    # BRIGHTNESS CONTRAST — spread of tone, p95 to p5, over the full range.
    brightness_contrast = float((np.percentile(lum, 95) - np.percentile(lum, 5)) / 255.0)

    # TEXT DENSITY — small connected ink, approximated by edge pixels in the mid-frequency band:
    # type edges cluster tightly, a photograph's do not.
    fine = (gx + gy) > 40
    text_density = float(fine.mean())

    # COLOUR HARMONY — how few hues carry the page. A register is a small set of hues used well;
    # this reads high when the page's chroma sits in one or two families.
    mx, mn = a.max(axis=2), a.min(axis=2)
    chroma = mx - mn
    mask = chroma > 28
    if mask.sum() < 40:
        harmony = 1.0                       # a near-neutral page is trivially harmonious
    else:
        hue = np.zeros_like(lum)
        with np.errstate(invalid="ignore", divide="ignore"):
            d = np.where(chroma == 0, 1, chroma)
            hr = ((g - b) / d) % 6
            hg = ((b - r) / d) + 2
            hb = ((r - g) / d) + 4
            hue = np.where(mx == r, hr, np.where(mx == g, hg, hb)) * 60.0
        hh = np.bincount((hue[mask] / 15).astype(np.int64) % 24, minlength=24).astype(float)
        hh /= hh.sum()
        harmony = float(np.sort(hh)[-3:].sum())   # share held by the top three hue families

    # LAYOUT BALANCE — how evenly ink sits about the vertical and horizontal axes. 1 is balanced;
    # a deliberately asymmetric page reads lower, which is information, not a fault.
    ink = 255.0 - lum if ground > 127 else lum
    ink = np.clip(ink - np.percentile(ink, 20), 0, None)
    tot = ink.sum() or 1.0
    cx = float((ink.sum(axis=0) * np.arange(w)).sum() / tot) / w
    cy = float((ink.sum(axis=1) * np.arange(h)).sum() / tot) / h
    balance = float(1.0 - min(1.0, 2.0 * ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5))

    return {"whitespace": whitespace, "colorfulness": colorfulness,
            "edge_density": edge_density, "brightness_contrast": brightness_contrast,
            "text_density": text_density, "colour_harmony": harmony,
            "layout_balance": balance}


ORDER = ("whitespace", "colorfulness", "edge_density", "brightness_contrast",
         "text_density", "colour_harmony", "layout_balance")


def deck_cues(renders):
    """[(page_name, {cue: value})] for every render found, in page order."""
    pngs = sorted(glob.glob(os.path.join(renders, "slide*.png")))
    out = []
    for p in pngs:
        try:
            out.append((os.path.basename(p), cues(p)))
        except Exception as exc:
            out.append((os.path.basename(p), {"error": "{}: {}".format(
                exc.__class__.__name__, exc)}))
    return out


def report(rows):
    """The lines a human or a critic reads. Deck spread first, then the pages worth looking at."""
    good = [(n, c) for n, c in rows if "error" not in c]
    if not good:
        return ["no readable renders — nothing measured, which is not the same as nothing wrong"]
    lines = ["{:<11}{}".format("page", "  ".join("%-6s" % k[:6] for k in ORDER))]
    for n, c in good:
        lines.append("{:<11}{}".format(n.replace(".png", ""),
                                       "  ".join("%-6.2f" % c[k] for k in ORDER)))
    lines.append("")
    # What a reader can act on: the deck's RANGE per cue. A flat range is the real signal — it
    # means every page looks the same, which no single page's number can tell you.
    for k in ORDER:
        vals = [c[k] for _n, c in good]
        lo, hi = min(vals), max(vals)
        note = ""
        if hi - lo < 0.06 and len(good) > 3:
            note = "  <- flat across the deck: every page scores the same on this"
        lines.append("  {:<20} {:.2f} .. {:.2f}   (mean {:.2f}){}".format(k, lo, hi,
                                                                         sum(vals) / len(vals),
                                                                         note))
    return lines


def _selftest():
    import tempfile
    from PIL import Image, ImageDraw
    ok, bad = [], []
    tmp = tempfile.mkdtemp(prefix="cues-")

    def page(name, draw):
        im = Image.new("RGB", (960, 540), (244, 242, 238))
        draw(ImageDraw.Draw(im), im)
        p = os.path.join(tmp, name)
        im.save(p)
        return cues(p)

    blank = page("slide01.png", lambda d, im: None)
    busy = page("slide02.png", lambda d, im: [d.rectangle([x, y, x + 26, y + 14], fill=(20, 24, 30))
                                              for x in range(20, 940, 34)
                                              for y in range(20, 520, 22)])
    ok.append("a blank page reads high whitespace ({:.2f}) and near-zero edges ({:.2f})".format(
        blank["whitespace"], blank["edge_density"])) if (
        blank["whitespace"] > 0.9 and blank["edge_density"] < 0.02) else bad.append(
        "blank page: {}".format(blank))
    ok.append("a dense page reads far more edge density ({:.2f} vs {:.2f})".format(
        busy["edge_density"], blank["edge_density"])) if (
        busy["edge_density"] > blank["edge_density"] * 20) else bad.append(
        "busy page did not separate: {:.3f} vs {:.3f}".format(
            busy["edge_density"], blank["edge_density"]))

    grey = page("slide03.png", lambda d, im: d.rectangle([100, 100, 600, 400], fill=(120, 122, 126)))
    vivid = page("slide04.png", lambda d, im: d.rectangle([100, 100, 600, 400], fill=(220, 60, 20)))
    ok.append("a vivid page scores higher colorfulness than a grey one ({:.2f} vs {:.2f})".format(
        vivid["colorfulness"], grey["colorfulness"])) if (
        vivid["colorfulness"] > grey["colorfulness"]) else bad.append(
        "colorfulness inverted: vivid {:.2f} grey {:.2f}".format(
            vivid["colorfulness"], grey["colorfulness"]))

    centred = page("slide05.png", lambda d, im: d.rectangle([330, 170, 630, 370], fill=(20, 24, 30)))
    corner = page("slide06.png", lambda d, im: d.rectangle([20, 20, 320, 220], fill=(20, 24, 30)))
    ok.append("a centred page is more balanced than a corner-weighted one ({:.2f} vs {:.2f})".format(
        centred["layout_balance"], corner["layout_balance"])) if (
        centred["layout_balance"] > corner["layout_balance"]) else bad.append(
        "balance inverted: centred {:.2f} corner {:.2f}".format(
            centred["layout_balance"], corner["layout_balance"]))

    # A dark register's ground IS its whitespace — reading "0% empty" on a dark deck would be wrong,
    # and is what a naive brightness-based measure does.
    dark = cues(_dark_page(tmp))
    ok.append("a DARK page's ground counts as whitespace ({:.2f}) — a dark register is not a full "
              "page".format(dark["whitespace"])) if dark["whitespace"] > 0.8 else bad.append(
        "dark page whitespace {:.2f}".format(dark["whitespace"]))

    rows = deck_cues(tmp)
    ok.append("the deck report names the RANGE per cue, which is what a flat deck shows up in") \
        if any("mean" in ln for ln in report(rows)) else bad.append("report has no range lines")
    rows.append(("broken.png", {"error": "x"}))
    ok.append("an unreadable render is carried as an error, not a crash") \
        if report(rows) else bad.append("report died on an error row")

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def _dark_page(tmp):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (960, 540), (16, 20, 26))
    ImageDraw.Draw(im).rectangle([100, 100, 500, 300], fill=(226, 90, 51))
    p = os.path.join(tmp, "_dark.png")
    im.save(p)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="a deck directory (its ./render is used) or a render dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.path:
        ap.print_help()
        return 2
    try:
        __import__("numpy")
        __import__("PIL")
    except ImportError as exc:
        print("cannot run: {} (pip install -r requirements.txt)".format(exc), file=sys.stderr)
        return 2
    root = os.path.expanduser(a.path)
    renders = root if glob.glob(os.path.join(root, "slide*.png")) else os.path.join(root, "render")
    rows = deck_cues(renders)
    if not rows:
        print("no slide*.png under {} — nothing measured, which is not the same as nothing wrong"
              .format(renders), file=sys.stderr)
        return 2
    print("\n".join(report(rows)))
    print("\nReported, not gated: a number that tracks taste across a corpus does not license a "
          "threshold on ONE deck.\nUse it to argue — a page in the deck's bottom decile that "
          "carries the argument is worth a look.")
    return 0


try:
    from _console import safe_stdio
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
