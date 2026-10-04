#!/usr/bin/env python3
"""The soft language's colour shape behind a number HOLDS the number, centred on it. It was a circle one line-height
across, drawn from the text box's LEFT edge: a "1" sat 16% of the circle left of centre and the "2" of "02" stood
outside it (the user, looking at the gallery, 2026-10-04). A single figure gets a circle; a wider number a pill of the
same height, so the line the flow reserved does not change. Ink width = the run's measured advance."""
from __future__ import annotations
import io, contextlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk
import visual_languages as vl

E = 914400.0


def number_and_shape(slide, num):
    box = next(sh for sh in slide.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() == num
               and not str(sh.name).startswith(dk.A11Y_TITLE_TAG))
    run = box.text_frame.paragraphs[0].runs[0]
    size, bold, face = run.font.size.pt, bool(run.font.bold), run.font.name
    adv = dk._natural_width_in([(num, bold)], size, face)
    bl, bw = box.left / E, box.width / E
    al = box.text_frame.paragraphs[0].alignment
    inset = dk.TEXT_INSET_LR / 2.0
    left = bl + (bw - adv) / 2.0 if al == dk.PP_ALIGN.CENTER else bl + inset
    shapes = [sh for sh in slide.shapes if "disc" in str(sh.name) or "pill" in str(sh.name)
              or "colour disc" in str(sh.name)]
    shp = shapes[0] if shapes else None
    return (left, left + adv, box.top / E, box.height / E), shp


cases = ["1", "02", "120", "3.5x", "40%"]
for ground in ("light", "dusk"):
    for W, H in ((13.333, 7.5), (7.5, 10.0)):
        for num in cases:
            for page in ("section", "data"):
                prs = dk.blank_deck(W, H)
                with contextlib.redirect_stdout(io.StringIO()):
                    k = vl.use("soft", prs, ground=ground)
                s = k.new_slide()
                if page == "section":
                    k.section(s, number=num, kicker="How it works", title="We fix it with you")
                else:
                    k.data(s, number=num, label="evening a month", note="Short enough.")
                (il, ir, bt, bh), shp = number_and_shape(s, num)
                tag = "{} {}x{} {} {!r}".format(ground, W, H, page, num)
                if shp is None:
                    fails.append("{}: no shape behind the number".format(tag))
                    continue
                sl, sw = shp.left / E, shp.width / E
                sh_h = shp.height / E
                pad = 0.06 * sh_h
                check(sl <= il - pad and sl + sw >= ir + pad,
                      "{}: the shape {:.2f}-{:.2f}in holds the number's ink {:.2f}-{:.2f}in".format(tag, sl, sl + sw, il, ir))
                check(abs((sl + sw / 2.0) - (il + ir) / 2.0) <= 0.05 * sh_h,
                      "{}: the shape is centred on the number (off by {:.2f}in)".format(tag, (sl + sw / 2.0) - (il + ir) / 2.0))
                if len(num) == 1:
                    check(abs(sw - sh_h) < 1e-3, "{}: a single figure sits in a circle ({:.2f} x {:.2f})".format(tag, sw, sh_h))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_vl_number_disc] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
