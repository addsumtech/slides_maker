#!/usr/bin/env python3
"""ornaments: the hand-made marks of editorial decks, native and countable.

Squiggles, scribbled loops, brush swashes, tape and scalloped badges carry the workshop / zine /
cut-paper registers (measured 2026-10-03: present on most of the 33 image-led skillry decks, absent
from all 72 sampled slide-maker pages). Each is drawn as editable geometry, never a picture, and
each is TAGGED as motif — so MOTIF_BUDGET counts it and TEXT_OVER_MOTIF sees text laid across it.
An untagged ornament is a loose shape every overlap rule would fight, or ignore.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deckkit as dk  # noqa: E402
import ornaments as orn  # noqa: E402
import render_deck as rd  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


RED = dk.RGBColor.from_string("E5483B")
prs = dk.blank_deck(13.333, 7.5)
s = dk.add_slide(prs)
dk.slide_background(s, dk.WHITE)
made = {
    "squiggle": orn.squiggle(s, 0.6, 0.6, 4.0, 0.5, RED),
    "scribble": orn.scribble(s, 0.6, 1.6, 4.0, 1.2, RED, seed=3),
    "brush_stroke": orn.brush_stroke(s, 0.6, 3.2, 4.5, 0.7, RED, seed=2),
    "tape": orn.tape(s, 6.0, 0.8, 1.6, 0.45, RED),
    "scallop": orn.scallop(s, 6.0, 2.2, 1.8, RED),
}
for name, sh in made.items():
    x = sh._element.xml
    check(dk._is_motif(sh), "{} is not motif-tagged".format(name))
    check(not dk._is_motif(sh, loud=True), "{} should default to QUIET".format(name))
    check("<p:style>" not in x, "{} carries the theme shadow (<p:style>)".format(name))
    check("custGeom" in x and "prstGeom" not in x, "{} is not (only) native custom geometry".format(name))
check("cubicBezTo" in made["squiggle"]._element.xml, "squiggle must be curves, not a polyline")
check("cubicBezTo" in made["scallop"]._element.xml, "scallop bumps must be curves")
check(abs(made["tape"].rotation - 356.0) < 1e-6, "tape default rotation -4 not applied")
check("<a:alpha" in made["tape"]._element.xml, "tape must be translucent")
loud = orn.squiggle(s, 6.0, 4.6, 3.0, 0.4, RED, loud=True)
check(dk._is_motif(loud, loud=True), "loud=True must tag LOUD")
# deterministic: same seed, same outline
a = orn.brush_stroke(s, 0.6, 5.0, 4.0, 0.6, RED, seed=7)._element.xml
b = orn.brush_stroke(s, 0.6, 5.8, 4.0, 0.6, RED, seed=7)._element.xml


def strip(x):
    return x[x.index("<a:pathLst"):x.index("</a:pathLst>")]


check(strip(a) == strip(b), "brush_stroke is not deterministic for a fixed seed")
for fn, args in ((orn.squiggle, (s, 0, 0, 0, 1, RED)), (orn.scallop, (s, 0, 0, -1, RED)),
                 (orn.tape, (s, 0, 0, 1, 0, RED))):
    try:
        fn(*args)
        fails.append("{} accepted a non-positive size".format(fn.__name__))
    except ValueError:
        pass
crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
check(not crit, "an ornament page has CRITICAL layout findings: {}".format(crit))

with tempfile.TemporaryDirectory() as td:
    deck = Path(td) / "orn.pptx"
    prs.save(str(deck))
    soffice = rd.find_soffice()
    if not soffice:
        fails.append("LibreOffice not found — the render half of this test did not run")
    else:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", td, str(deck)],
                       check=True, capture_output=True, timeout=180)
        import fitz
        from PIL import Image
        pix = fitz.open(str(Path(td) / "orn.pdf"))[0].get_pixmap(dpi=40)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        k = pix.width / 13.333

        def red_in(x, y, w, h):
            n = 0
            for xi in range(int(x * k), int((x + w) * k)):
                for yi in range(int(y * k), int((y + h) * k)):
                    c = im.getpixel((xi, yi))
                    n += (c[0] > 170 and c[1] < 120 and c[2] < 120)
            return n

        for name, (x, y, w, h) in {"squiggle": (0.6, 0.6, 4.0, 0.5), "scribble": (0.6, 1.6, 4.0, 1.2),
                                   "brush_stroke": (0.6, 3.2, 4.5, 0.7),
                                   "scallop": (6.0, 2.2, 1.8, 1.8)}.items():
            check(red_in(x, y, w, h) > 15, "{} drew nothing visible in the render".format(name))

# ── tape is MEANT to overlap the print it holds; both gates must honour that ──────────────────
# Measured on the end-to-end sample (2026-10-03): tape on a tilted print was a HARD render-time
# OVERLAP. Two causes: lint_deck read an overlap declaration only from a name STARTING with
# `deckkit-overlap`, so a motif that also declares one (`deckkit-motif-quiet+overlap:<why>`) was
# refused at render time though lint_layout honoured it; and tape() declared nothing.
import contextlib  # noqa: E402
import io  # noqa: E402

import lint_deck  # noqa: E402
from PIL import Image as _Im  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    ph = Path(td) / "ph.png"
    _im = _Im.new("RGB", (400, 300))
    _im.putdata([(60 + x // 8, 40 + y // 8, 30) for y in range(300) for x in range(400)])
    _im.save(ph)
    p2 = dk.blank_deck(13.333, 7.5)

    def _page(title):
        sl = dk.add_slide(p2)
        dk.slide_background(sl, dk.WHITE)
        dk.text(sl, 0.6, 0.4, 8, 0.8, [[(title, 28, dk.DEEP, True, False)]])
        return sl

    sl = _page("Tape on a print")
    dk.picture(sl, str(ph), 4.0, 1.6, 4.0, 3.0, fit="cover", rotation=-4, alt="a test print")
    orn.tape(sl, 5.2, 1.4, 1.6, 0.42, "C9A227")
    # a hand-made motif that ALSO declares an overlap, crossing a picture — the composed name
    sl = _page("Declared motif on a picture")
    dk.picture(sl, str(ph), 4.0, 1.6, 4.0, 3.0, fit="cover", alt="a test print")
    m = dk.box(sl, 7.4, 2.0, 1.4, 0.6, fill=dk.RGBColor.from_string("2F5BEA"))
    dk.tag_motif(m)
    dk.overlap_intent(m, "the badge is pinned to the corner of the print")
    check("+overlap" in m.name and m.name.startswith("deckkit-motif"), "composed name: " + m.name)
    # the control: the SAME motif with no declaration must still be an OVERLAP
    sl = _page("Undeclared motif on a picture")
    dk.picture(sl, str(ph), 4.0, 1.6, 4.0, 3.0, fit="cover", alt="a test print")
    m2 = dk.box(sl, 7.4, 2.0, 1.4, 0.6, fill=dk.RGBColor.from_string("2F5BEA"))
    dk.tag_motif(m2)
    deck2 = Path(td) / "tape.pptx"
    p2.save(str(deck2))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_deck.lint(str(deck2))
    lines = buf.getvalue().splitlines()
    ov = lambda n: [ln for ln in lines if ln.strip().startswith("slide {}: OVERLAP".format(n))]  # noqa: E731
    check(not ov(1), "lint_deck: tape holding a print is an OVERLAP: {}".format(ov(1)))
    check(not ov(2), "lint_deck: a motif's composed overlap declaration was ignored: {}".format(ov(2)))
    check(ov(3), "lint_deck: the undeclared control must still be an OVERLAP")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_ornaments] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
