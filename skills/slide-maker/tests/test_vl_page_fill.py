#!/usr/bin/env python3
"""Two compositions the user found weak in the gallery (2026-10-04):
- a data page with no picture set the figure, label and note at their usual sizes in the top-left quarter of a wide
  column: now the figure is set big, and on a landscape canvas the label and note sit BESIDE it;
- storybook contained a PORTRAIT illustration in a frame drawn for a landscape one (the quote page: a sliver, ~4% of
  the slide): a portrait picture now takes the page's *_tall frame, chosen from the picture's own aspect.
Every language, both canvases, short and long numbers, a CJK label."""
from __future__ import annotations
import contextlib, io, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk
import visual_languages as vl

# 1. the data page with no picture (the native four: tests/test_native_languages.py)
for name in vl.IMAGE_LED:
    for W, H in ((13.333, 7.5), (7.5, 10.0)):
        for num, lab in (("1", "evening a month"), ("120", "repairs a year"), ("1,250,000", "每月一个晚上的修理次数")):
            prs = dk.blank_deck(W, H)
            with contextlib.redirect_stdout(io.StringIO()):
                k = vl.use(name, prs)
            s = k.new_slide()
            try:
                r = k.data(s, number=num, label=lab, note="Short enough to fit around work.")
            except Exception as e:
                fails.append("{} {}x{} {!r}: {}: {}".format(name, W, H, num, type(e).__name__, e))
                continue
            rn, rl = r["rects"]["number"], r["rects"]["label"]
            tag = "{} {}x{} {!r}".format(name, W, H, num)
            if W > H:
                check(rl[0] >= rn[0] + rn[2] - 1e-6, "{}: the label sits BESIDE the figure (label x {:.2f}, figure ends {:.2f})"
                      .format(tag, rl[0], rn[0] + rn[2]))
                check(rl[1] < rn[1] + rn[3] and rl[1] + rl[3] > rn[1], "{}: ...and level with it".format(tag))
            sizes = [r_.font.size.pt for sh in s.shapes if getattr(sh, "has_text_frame", False)
                     and sh.text_frame.text.strip() == num for p_ in sh.text_frame.paragraphs for r_ in p_.runs if r_.font.size]
            base = vl.TYPE[name]["number"][0] * min(W, H) / 7.5
            if len(num) <= 3 and sizes:
                # big = 1.2x the language's size, OR as wide as the figure may be (half the column landscape, 86%
                # portrait) — a wide face hits that cap first (Linux CI's substitute for Impact: "120" at 1.18x)
                fw = dk._natural_width_in([(num, bool(vl.TYPE[name]["number"][2]))], max(sizes), k.face("numeral"))
                colw = vl.LAYOUTS[name]["data"]["land" if W > H else "port"]["col_noimg"][2] * W
                capped = fw >= 0.9 * (0.50 if W > H else 0.86) * colw
                check(max(sizes) >= 1.2 * base or capped, "{}: the figure is set big ({:.0f}pt vs the language's {:.0f}pt, "
                      "{:.2f}in wide of a {:.2f}in column)".format(tag, max(sizes), base, fw, colw))

# 2. storybook: a portrait illustration takes the tall frame
port = str(ROOT / "assets" / "vl" / "watercolour" / "balcony-watering.jpg")
pages = (("cover", dict(kicker="A small city garden", title="A balcony can grow a season of vegetables")),
         ("section", dict(number="02", kicker="Tools", title="You need very few tools")),
         ("image_text", dict(kicker="Tools", title="You need very few tools", body="A trowel and twine.")),
         ("quote", dict(quote="Half an hour of watering a day is enough.", attribution="A balcony gardener")),
         ("data", dict(number="1", label="pot is enough to begin", note="A window sill will do.")),
         ("closing", dict(title="A balcony can grow a season of vegetables", line="A window sill will do.")))
for W, H, floor in ((13.333, 7.5, 0.20), (7.5, 10.0, 0.11)):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("storybook", prs)
    for page, kw in pages:
        s = k.new_slide()
        getattr(k, page)(s, image=port, **kw)
        pics = [sh for sh in s.shapes if sh.shape_type == 13]
        share = max((sh.width * sh.height for sh in pics), default=0) / (W * H * 914400.0 ** 2)
        check(share >= floor, "storybook {}x{} {}: a portrait illustration fills {:.0%} of the slide (floor {:.0%})"
              .format(W, H, page, share, floor))
    bad = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
    check(not bad, "storybook {}x{}: the tall frames raise no layout criticals: {}".format(W, H, [(f[0], f[2]) for f in bad][:4]))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_vl_page_fill] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
