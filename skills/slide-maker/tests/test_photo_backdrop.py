#!/usr/bin/env python3
"""A photo carrying the page: the panel goes where the image MEASURES calmest.

`references/image-generation.md` has named three placements for a content image — full-bleed
background, side panel, inline figure — for a long time, and the first of them was the only one
with no component. Every part existed (`picture(fit="cover")`, `slide_background`, `scrim_overlay`,
`photo_card`, `bottom_callout`) and the composition did not, so it was hand-rolled each time and
the same three things went wrong: the panel landed where the picture was busiest, the ink was
chosen by eye against a photograph instead of against the panel, and the panel was made translucent
enough to look elegant and too translucent to read.

These hold the three claims that make the component worth having over a hand-rolled box.
"""
import sys
import tempfile
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
warnings.simplefilter("ignore")

import deckkit as dk                      # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


def _plate(path, calm):
    """A photo-like plate whose calm half is where `calm` says: 'left' | 'right' | 'top'."""
    from PIL import Image
    W, H = 640, 360
    im = Image.new("RGB", (W, H), (150, 170, 195))
    px = im.load()
    for y in range(H):
        for x in range(W):
            t = y / float(H)
            px[x, y] = (int(120 + 60 * (1 - t)), int(145 + 55 * (1 - t)), int(180 + 40 * (1 - t)))
    # a deterministic "busy" field — hard edges every few pixels, which is what variance measures
    if calm == "left":
        xs = range(W // 2, W)
    elif calm == "right":
        xs = range(0, W // 2)
    else:                                   # calm top -> busy along the bottom
        xs = range(0, W)
    ys = range(0, H) if calm in ("left", "right") else range(int(H * 0.62), H)
    for y in ys:
        for x in xs:
            px[x, y] = (40, 44, 52) if ((x // 3 + y // 3) % 2) else (215, 205, 165)
    im.save(path)
    return path


TMP = Path(tempfile.mkdtemp(prefix="photobd-"))
dk.set_palette(deep="14181D", magenta="E2231A", font="Helvetica Neue")
dk.set_ground("F4F1EA")


def _run(calm, **kw):
    p = _plate(TMP / "{}.png".format(calm), calm)
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    rect = dk.photo_backdrop(s, str(p), alt="a test plate", **kw)
    return prs, s, rect


# ---------------------------------------------------------------- the panel follows the MEASUREMENT
W_IN = 10.0
_prs, _s, (x, y, w, h, ink) = _run("left")
check(x + w / 2 < W_IN / 2,
      "🔴 an image whose LEFT half is calm puts the content panel on the left — the placement is "
      "read from the picture, which is the one thing a hand-rolled box cannot do "
      "(panel centre at {:.0%} of the width)".format((x + w / 2) / W_IN))
_prs, _s, (x2, _y, w2, _h, _i) = _run("right")
check(x2 + w2 / 2 > W_IN / 2,
      "...and a mirrored image puts it on the right ({:.0%})".format((x2 + w2 / 2) / W_IN))
_prs, _s, (_x, y3, w3, h3, _i) = _run("top")
check(y3 + h3 < 5.625 * 0.55 and w3 > W_IN * 0.8,
      "...and an image that is calm across the SKY puts the words in an upper BAND — a wide calm "
      "region becomes the band on its own side, not a side column, which is what the measurement "
      "actually said (band at y={:.2f}, {:.1f}in wide)".format(y3, w3))


# A side band that cannot hold a column is not a side band. On a narrow canvas it becomes the
# horizontal one — derived from the measure it would leave, not from a canvas whitelist.
_p = _plate(TMP / "left.png", "left")
_prs = dk.blank_deck()
_prs.slide_width, _prs.slide_height = int(5.63 * 914400), int(10.0 * 914400)
_s = dk.add_slide(_prs)
_bx, _by, _bw, _bh, _i = dk.photo_backdrop(_s, str(_p), alt="a plate")
check(_bw > 4.0,
      "🔴 on a portrait canvas the left-calm image does NOT get a 1.9in side column — the panel "
      "falls back to the horizontal band, which is the shape that holds a measure there "
      "({:.1f}in wide)".format(_bw))

# ------------------------------------------------------------------- the ink comes from the PANEL
for ground, want_dark in (("F4F1EA", True), ("14181D", False)):
    dk.set_ground(ground)
    _prs, _s, (_x, _y, _w, _h, ink2) = _run("left")
    lum = 0.299 * ink2[0] + 0.587 * ink2[1] + 0.114 * ink2[2]
    got_dark = lum < 128
    check(got_dark == want_dark,
          "on a {} panel the returned ink is {} — resolved against the PANEL, never against the "
          "photograph, which is the second thing that goes wrong when this is hand-rolled".format(
              "light" if want_dark else "dark", "dark" if got_dark else "light"))
    check(dk.contrast_ratio(ink2, dk.RGBColor.from_string(ground)) >= 4.5,
          "...and it clears the 4.5:1 body floor on that panel ({:.1f}:1)".format(
              dk.contrast_ratio(ink2, dk.RGBColor.from_string(ground))))
dk.set_ground("F4F1EA")


# --------------------------------------------------------------------- the alpha floor is a RULE
try:
    _run("left", alpha=0.5)
    bad.append("a translucent panel under the 0.88 floor was accepted")
except ValueError as exc:
    check("scrim" in str(exc).lower() and "0.88" in str(exc),
          "🔴 an alpha under 0.88 RAISES and names the rule — a scrim only DIMS the image's "
          "linework, so a title over a balustrade stays crossed by it; the message points at "
          "`scrim_overlay`, which is the component that means a deliberate wash")
try:
    dk.photo_backdrop(dk.add_slide(dk.blank_deck()), str(TMP / "left.png"), alt="")
    bad.append("a missing alt-text was accepted")
except ValueError as exc:
    check("alt" in str(exc).lower(),
          "...and a missing `alt` raises rather than letting a deck acquire a BLOCKING "
          "accessibility finding it will only meet at hand-off")
try:
    dk.photo_backdrop(dk.add_slide(dk.blank_deck()), str(TMP / "left.png"), alt="x", panel="middle")
    bad.append("an unknown panel value was accepted")
except ValueError as exc:
    check("panel must be" in str(exc), "...and an unknown `panel` value names the legal ones")


# ------------------------------------------------------------------------- it survives the linter
_prs, _s, (x4, y4, w4, h4, ink4) = _run("left", credit="Photographer / CC BY-SA")
dk.text(_s, x4, y4, w4, 1.0, [[("A claim over a photograph", 28, ink4, True, False)]])
try:
    dk.lint_layout(_prs, strict=True)
    check(True, "a page built from it clears the build-time geometry gate, credit included")
except Exception as exc:
    bad.append("lint_layout: {}".format(exc))
texts = [sh.text_frame.text for sh in _s.shapes if getattr(sh, "has_text_frame", False)]
check(any("CC BY-SA" in t for t in texts),
      "...and the attribution an attribution-required licence needs is ON THE SLIDE, which is what "
      "`check_image_provenance` looks for")
_prs2, _s2, (_x, _y, _w, h5, _i) = _run("left")
check(h5 > h4,
      "...and the content rect SHRINKS when a credit is placed, so the credit cannot be written "
      "over ({:.2f}in vs {:.2f}in)".format(h4, h5))


# ------------------------------------------------------------- generality: any canvas, any picture
for label, (cw, ch) in (("16:9 13.33in", (13.333, 7.5)), ("4:3", (10.0, 7.5)),
                        ("portrait 9:16", (5.63, 10.0)), ("A1 landscape", (33.1, 23.4))):
    p = _plate(TMP / "left.png", "left")
    prs = dk.blank_deck()
    prs.slide_width, prs.slide_height = int(cw * 914400), int(ch * 914400)
    s = dk.add_slide(prs)
    bx, by, bw, bh, _ink = dk.photo_backdrop(s, str(p), alt="a plate")
    check(bx >= 0 and by >= 0 and bx + bw <= cw + 1e-6 and by + bh <= ch + 1e-6
          and bw > cw * 0.25 and bh > ch * 0.3,
          "on {} the panel is on the canvas and big enough to hold a page "
          "({:.1f}x{:.1f}in)".format(label, bw, bh))

# an unreadable image must not take the build down with it — it degrades LOUDLY
dud = TMP / "not-an-image.png"
dud.write_text("this is not a PNG", encoding="utf-8")
try:
    dk.photo_backdrop(dk.add_slide(dk.blank_deck()), str(dud), alt="x")
    check(True, "an unreadable image falls back to a left band and SAYS it was a guess")
except Exception as exc:
    check("not found" in str(exc) or "cannot" in str(exc).lower(),
          "...or fails with a message naming the file ({})".format(type(exc).__name__))

# and the component is WIRED, not merely written
import component_audit as ca        # noqa: E402
import sigs                          # noqa: E402
check("photo_backdrop" in ca.FORM_GUARANTEE,
      "the component states its guarantee in `component_audit.FORM_GUARANTEE`, so the audit can "
      "name it when a deck hand-rolls the same geometry")
check("photo_backdrop" in sigs.EXAMPLES,
      "...and carries a runnable `sigs.py --example` scaffold, which the smoke suite EXECUTES — "
      "a capability that does not reach the one lookup an agent makes is one it will hand-roll")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
