#!/usr/bin/env python3
"""Every component that MEASURES its own text measures the width the renderer sets it in: the text frame minus text()'s
2pt left/right insets. A word that fits the frame but not its inner width breaks mid-word in the render; measured at
the frame width it counts one line short and the component is built too small (a node's ink leaked 0.11in above and
below under DejaVu, CI simulation 2026-10-04). Each case is built from the CURRENT font's metrics, so it holds on any
machine: the word is set wider than the inner width and narrower than the frame."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk

WORD = "Extraordinarily"


def frame_for(size, bold, font=None):
    """A frame width (in) the word fits but its inner width (frame - insets) does not."""
    wpt = dk._pil_font(font or dk.FONT, size, bold).getlength(WORD) / dk._MEAS_PREC
    return wpt / 72.0 + dk.TEXT_INSET_LR / 2.0


def ink_inside(slide, label):
    """(ok, detail): every text frame's measured ink stays inside the slide's tallest filled shape around it."""
    texts = [sh for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    boxes = [sh for sh in slide.shapes if not (sh.has_text_frame and sh.text_frame.text.strip())]
    bad = []
    for t in texts:
        r = dk._ink_rect(t, dk._bbox_in(t))
        if not r:
            continue
        (ix, iy, iw, ih) = r[0]
        hosts = [b for b in boxes if b.left / 914400 <= ix + 1e-3 and (b.left + b.width) / 914400 >= ix + iw - 1e-3]
        if not hosts:
            continue
        host = max(hosts, key=lambda b: b.height)
        top, bot = host.top / 914400, (host.top + host.height) / 914400
        if iy < top - 0.03 or iy + ih > bot + 0.03:
            bad.append((t.text_frame.text[:24], round(iy, 3), round(iy + ih, 3), round(top, 3), round(bot, 3)))
    return not bad, bad


# node: frame = w - 0.12, label 13pt bold
fw = frame_for(13, True)
prs = dk.blank_deck(); s = dk.add_slide(prs)
dk.node(s, 1.0, 1.0, fw + 0.12, 0.35, WORD)
ok, bad = ink_inside(s, "node")
check(ok, "node: the label's ink stays inside the node: {}".format(bad))

# chip: frame = w - 0.26, title 14pt bold
fw = frame_for(14, True)
prs = dk.blank_deck(); s = dk.add_slide(prs)
dk.chip(s, 1.0, 1.0, fw + 0.26, 0.4, WORD, "", dk.TINT)
ok, bad = ink_inside(s, "chip")
check(ok, "chip: the title's ink stays inside the chip: {}".format(bad))

# modbox: role frame = w - 0.1, 16pt bold
fw = frame_for(16, True)
prs = dk.blank_deck(); s = dk.add_slide(prs)
dk.modbox(s, 1.0, 1.0, fw + 0.1, 0.6, WORD, "m.py", dk.TINT)
ok, bad = ink_inside(s, "modbox")
check(ok, "modbox: the role's ink stays inside the box: {}".format(bad))

# callout: frame = w - 0.44, label 11pt bold + body 12.5pt — one word body at 12.5pt
fw = frame_for(12.5, False)
lab_w = dk._pil_font(dk.FONT, 11, True).getlength("A  ") / dk._MEAS_PREC / 72.0
prs = dk.blank_deck(); s = dk.add_slide(prs)
h = dk.measure_callout("A", WORD, fw + lab_w + 0.44)
dk.callout(s, 1.0, 1.0, fw + lab_w + 0.44, 0.3, "A", WORD)
ok, bad = ink_inside(s, "callout")
check(ok, "callout: the text's ink stays inside the callout: {}".format(bad))

# measure_text / fit_text_size already subtract it (Task 6) — the same contract, stated once more
fw = frame_for(24, False)
check(dk.measure_text([(WORD, False)], fw, 24) > dk.measure_text([(WORD[:3], False)], fw, 24),
      "measure_text counts the word that fits the frame but not its inner width as wrapping")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_inset_contract] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
