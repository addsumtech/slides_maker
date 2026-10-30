#!/usr/bin/env python3
"""The cover axis must read where the GLYPHS are, not where the text BOX is.

🔴 MEASURED. `check_direction_applied` scored the title block as `sh.left + sh.width/2`. A
full-width, left-aligned title box centres at exactly 50% of the canvas while every glyph hugs the
left margin — so a textbook LOW-LEFT cover was flagged as "centred" on a real deck (0.90in left,
11.53in wide, `job-hunt` flush left → 50.0%). The same line fails the OTHER way too: a genuinely
CENTRED cover whose narrow box sits off to one side scores off-centre and passes. One arithmetic
slip, a false positive and a false negative.

This file pins BOTH directions, because a fix verified only on the case that motivated it is how
the mirror-image bug survives. `deckkit._ink_rect` is the measurement — it accounts for the
frame's margins, measured wraps, the vertical anchor and the paragraph alignment.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                    # noqa: E402
import check_direction_applied as cda   # noqa: E402

fails: list[str] = []
skipped: list[str] = []
W, H = 13.333, 7.5
INK = dk.RGBColor.from_string("111111")
EA = "Songti SC"
# 🔴 A width in inches is only true where the glyphs exist. On a Linux runner with no CJK face,
# `Songti SC` substitutes to DejaVu and a CJK width comes back at Latin metrics — so asserting the
# INCHES there tests the runner's font list, not this fix. The repo already had this convention
# (`test_cjk_measurement.HAVE_CJK_FONT`); this file shipped without it and turned CI red three
# times while passing on the author's Mac. What is font-INDEPENDENT — that the run carries <a:ea>
# at all, and that a left-aligned CJK title reads left — is still asserted everywhere.
HAVE_CJK_FONT = not dk._font_substituted(EA)


def check(cond, msg):
    if not cond:
        fails.append(msg)


def check_metric(cond, msg):
    """A check whose truth needs a real CJK font present — skipped loudly, never silently."""
    if not HAVE_CJK_FONT:
        skipped.append(msg)
        return
    check(cond, msg)


def centre_of(left, width, align=None, text="job-hunt"):
    """Build one cover title and return where the check thinks its block sits, 0..1."""
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    kw = {"align": align} if align is not None else {}
    dk.text(s, left, 3.55, width, 1.35, [[(text, 60, INK, True, False)]], **kw)
    sh = next(x for x in s.shapes if x.has_text_frame and x.text_frame.text.strip())
    cb = cda._block_rect(60.0, sh)
    return (cb["left"] + cb["w"] / 2.0) / W, cb


# ── 🔴 THE MEASURED FAILURE: a full-width LEFT-ALIGNED title is NOT centred ──────────────────────
c, cb = centre_of(0.9, W - 1.8)
check(cb["from_ink"], "the ink was not measurable on a plain title — the check silently fell back "
                      "to the box, which is the bug it is meant to fix")
check(c < 0.40, "a full-width LEFT-ALIGNED title scored {:.0%} — the box-centre reading (50%) is "
                "back, and every low-left cover is flagged as centred".format(c))

# ── 🔴 THE MIRROR: a genuinely CENTRED title in an OFF-CENTRE box IS centred ─────────────────────
# Box spans 0.9..7.9 (box centre 33%), text centred inside it. Reading the box passes this deck as
# "not centred"; reading the ink must see it sitting at the box's own middle.
c2, cb2 = centre_of(0.9, 7.0, align=dk.PP_ALIGN.CENTER)
check(cb2["from_ink"], "ink not measured on the centred case")
check(abs(c2 - (0.9 + 3.5) / W) < 0.06,
      "a CENTRED paragraph in an off-centre box scored {:.0%}; the ink sits at {:.0%} and the "
      "alignment is the whole signal".format(c2, (0.9 + 3.5) / W))
check(c2 > c, "the centred-in-box title did not score further right than the flush-left one — the "
              "measure is not responding to alignment at all")

# ── RIGHT alignment moves the ink the other way ─────────────────────────────────────────────────
c3, _ = centre_of(0.9, W - 1.8, align=dk.PP_ALIGN.RIGHT)
check(c3 > 0.60, "a full-width RIGHT-ALIGNED title scored {:.0%} — ink should sit near the right "
                 "margin".format(c3))

# ── CJK: the same reading in Chinese ─────────────────────────────────────────────────────────────
# `_ink_rect` measures through <a:ea>, so a Chinese deck must have set `EAFONT` — which every real
# one has, because `CJK_NO_EA` is a build-time CRITICAL and a deck without it cannot be produced.
# MEASURED with EAFONT unset: six CJK glyphs came back 3.00in, NARROWER than six latin letters at
# 3.18in, against a true 5.00in — a 40% under-report that would drag a left-aligned CJK title even
# further left and pass this test for the wrong reason. So the order is asserted against a latin
# string of the same glyph count, under the same setup a real deck has.
dk.EAFONT = EA
c_cn, cb_cn = centre_of(0.9, W - 1.8, text="求职工具介绍")
c_lat, _ = centre_of(0.9, W - 1.8, text="abcdef")
check(cb_cn["from_ink"], "ink not measured on a CJK title")
check(c_cn < 0.40, "a left-aligned CJK title scored {:.0%}".format(c_cn))
# font-INDEPENDENT: the run must carry an <a:ea> face at all. Without it the measuring face falls
# back to <a:latin> on EVERY machine, CJK font or not — which is the actual defect class.
prs_cn = dk.blank_deck(W, H)
s_cn = dk.add_slide(prs_cn)
dk.text(s_cn, 0.9, 3.55, W - 1.8, 1.35, [[("求职工具介绍", 60, INK, True, False)]])
xml_cn = "".join(sh._element.xml for sh in s_cn.shapes)
check("<a:ea " in xml_cn or "<a:ea/>" in xml_cn,
      "a CJK run carries no <a:ea> face, so `_ink_rect` measures it in the latin face on every "
      "machine — the width is then short by about half and no font can fix it")
check_metric(c_cn > c_lat,
             "six CJK glyphs measured no wider than six latin ones — the measuring face is "
             "falling back to <a:latin> and every CJK width is short by about half")

# ── the fallback is VISIBLE, never disguised as a measurement ────────────────────────────────────
class _Dud:
    left = width = top = 0
    has_text_frame = False

    @property
    def text_frame(self):
        raise RuntimeError("no frame")


cbf = cda._block_rect(60.0, _Dud())
check(cbf.get("from_ink") is False,
      "an unmeasurable shape came back without `from_ink: False` — 'measured the ink' and 'guessed "
      "from the box' must not look identical downstream")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
if skipped:
    print("  ({} width check(s) skipped: {!r} is not installed here, so a CJK width would be "
          "DejaVu's — the face-routing check above is the font-independent half and it ran)"
          .format(len(skipped), EA))
print("[test_cover_ink_not_box] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
