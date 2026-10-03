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
    pr = dk.picture(sl, str(ph), 4.0, 1.6, 4.0, 3.0, fit="cover", rotation=-4, alt="a test print")
    orn.tape(sl, 5.2, 1.4, 1.6, 0.42, "C9A227", holds=pr)
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
    # 4: tape NOT told what it holds, laid across a solid data card — that is still an OVERLAP
    #    (final review: a blanket self-declaration waived tape against ANY solid shape)
    sl = _page("Stray tape on a card")
    dk.box(sl, 4.0, 1.6, 4.0, 2.4, fill=dk.RGBColor.from_string("DDE6F5"))
    orn.tape(sl, 7.2, 1.4, 1.6, 0.42, "C9A227")
    # holds= a shape the tape does not touch is refused, not declared
    far = dk.picture(sl, str(ph), 0.4, 5.0, 1.5, 1.2, fit="cover", alt="a far print")
    try:
        orn.tape(sl, 10.0, 1.0, 1.2, 0.4, "C9A227", holds=far)
        fails.append("tape(holds=) accepted a print it does not touch")
    except ValueError:
        pass
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
    check(ov(4), "lint_deck: tape with no holds= across a solid card must be an OVERLAP")


# ── a pale tape on the page ground: NON-TEXT CONTRAST unless DECLARED decorative, per shape ─────
# Decided by the user (2026-10-03): WCAG 1.4.11 exempts pure decoration, but the check cannot tell
# decoration from a mark someone must read — so the author says so, per shape, with a reason the
# lint prints. Undeclared, it is still held.
with tempfile.TemporaryDirectory() as td:
    pd = dk.blank_deck(13.333, 7.5)
    PAPER = dk.RGBColor.from_string("F4EEE3")
    for declare in (False, True):
        sl = dk.add_slide(pd)
        dk.slide_background(sl, PAPER)
        dk.text(sl, 0.6, 0.4, 8, 0.8, [[("Decor", 28, dk.DEEP, True, False)]])
        tp_ = orn.tape(sl, 6.0, 3.0, 1.6, 0.42, "F2D16B")          # on the page ground, pale
        if declare:
            dk.decorative(tp_, "washi tape is ornament; no meaning rides on seeing it")
            check(dk._is_motif(tp_), "decorative() erased the motif tag: " + tp_.name)
            check("+decor" in tp_.name, "decorative() did not record itself in the name: " + tp_.name)
    dpath = Path(td) / "decor.pptx"
    pd.save(str(dpath))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_deck.lint(str(dpath))
    outd = buf.getvalue()
    lns = outd.splitlines()
    ntc = lambda n: [ln for ln in lns if ln.strip().startswith("slide {}:".format(n)) and "NON-TEXT CONTRAST" in ln]  # noqa: E731
    check(ntc(1), "an UNDECLARED pale tape on the page must still be NON-TEXT CONTRAST")
    check(not ntc(2), "a tape DECLARED decorative was still held: {}".format(ntc(2)))
    check("washi tape is ornament" in outd, "the decorative declaration and its reason are not printed")
    # the reason floor is the language-fair one: 8 CJK characters say as much as 16 Latin
    sl = dk.add_slide(pd)
    t_short = orn.tape(sl, 1.0, 1.0, 1.2, 0.4, "F2D16B")
    try:
        dk.decorative(t_short, "pretty")
        fails.append("decorative() accepted a reason that says nothing")
    except ValueError:
        pass
    dk.decorative(orn.tape(sl, 3.0, 1.0, 1.2, 0.4, "F2D16B"), "胶带只是装饰，不承载信息")
    # the LINE branch of the same check (connectors) honours the same declaration
    pl = dk.blank_deck(13.333, 7.5)
    for declare in (False, True):
        sl = dk.add_slide(pl)
        dk.slide_background(sl, PAPER)
        dk.text(sl, 0.6, 0.4, 8, 0.8, [[("Lines", 28, dk.DEEP, True, False)]])
        ln_ = dk._flat(sl.shapes.add_connector(1, dk.Inches(1.0), dk.Inches(3.0), dk.Inches(6.0), dk.Inches(3.0)))
        ln_.line.color.rgb = dk.RGBColor.from_string("EADFC9")
        ln_.line.width = dk.Pt(2)
        if declare:
            dk.decorative(ln_, "a hairline flourish under the fold; it carries nothing")
    lpath = Path(td) / "lines.pptx"
    pl.save(str(lpath))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_deck.lint(str(lpath))
    ll_ = buf.getvalue().splitlines()
    nl = lambda n: [x for x in ll_ if x.strip().startswith("slide {}:".format(n)) and "NON-TEXT CONTRAST: line" in x]  # noqa: E731
    check(nl(1), "an undeclared pale connector must still be NON-TEXT CONTRAST")
    check(not nl(2), "a connector DECLARED decorative was still held: {}".format(nl(2)))

# ── generalisation probe (2026-10-03): inputs the first tests never tried ──────────────────────

_sg = dk.add_slide(prs)
for fn, kw, word in ((orn.squiggle, {"waves": 2.5}, "waves"), (orn.scribble, {"loops": 1.5}, "loops")):
    try:
        fn(_sg, 1, 1, 3, 0.6, RED, **kw)
        fails.append("{} accepted a non-integer {}".format(fn.__name__, word))
    except (TypeError, ValueError) as e:
        check(word in str(e), "{}'s refusal should name {}: {}".format(fn.__name__, word, e))
try:
    orn.scallop(_sg, 1, 1, 1.5, RED, bumps=7.5)
    fails.append("scallop accepted a non-integer bumps")
except (TypeError, ValueError) as e:
    check("bumps" in str(e), "scallop's refusal should name bumps: {}".format(e))
try:
    orn.squiggle(_sg, 1, 1, 3, 0.4, "red")
    fails.append("an ornament accepted the colour 'red'")
except ValueError as e:
    check("colour" in str(e).lower() or "color" in str(e).lower(),
          "a bad ornament colour should say so: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_ornaments] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
