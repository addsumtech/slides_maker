#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The CEILING side of the toolchain: architecture, rhythm, and what a page looks like.

WHY. Measured across `render_deck.py`, of twelve blocking gate sections essentially one pushes
UPWARD — and `agents/critic.md` says so itself, calling its distinctiveness axis "the loop's ONE
upward-pushing lens", deliberately non-blocking. Everything else subtracts faults. So the skill got
very good at preventing bad decks and had almost nothing for making distinctive ones, and the
evidence was in its own output: a deliberately DEAD deck — one skeleton, three type sizes, no idea —
linted clean at `0 layout findings`, and this repo's own A0 poster passed every gate at one
skeleton, seven size tokens against a four-to-five target, and 59% occupancy.

Three concrete gaps, each verified before it was closed:

  ARCHITECTURE   `lint_deck` demands >=4 distinct page skeletons (SKELETON VARIETY) from a named
                 set of eight, and the toolkit had NO helper and NO scaffold for any of them — 190
                 helpers for what goes ON a page, none for how a page is COMPOSED. A required rule
                 with no tool to meet it is the asymmetry SKILL.md's own enforcement invariant
                 warns about.
  RHYTHM         SKELETON VARIETY and LAYOUT SAMENESS both fire AFTER the build, when varying the
                 architecture means re-laying written pages. So it got decided one page at a time,
                 in the order the content arrived.
  LOOK           nothing measured what a page LOOKS like — only what is wrong with it.

Run: python3 tests/test_design_capability.py
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import composition_cues as cc        # noqa: E402
import deckkit as dk                 # noqa: E402
import lint_deck as ld               # noqa: E402
import plan_rhythm as pr             # noqa: E402

OKS: list[str] = []
FAILS: list[str] = []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="design-cap-"))


def check(cond, msg, detail=""):
    (OKS if cond else FAILS).append(msg if cond else "{} — {}".format(msg, detail))


# ── 1. the eight architectures exist, and are REALLY different ───────────────────────────────
check(len(dk.SKELETONS) == 8, "deckkit names eight page architectures", str(dk.SKELETONS))
_prs = dk.blank_deck()
_sl = dk.add_slide(_prs)
for _k in dk.SKELETONS:
    _r = dk.skeleton(_sl, _k)
    check(isinstance(_r, dict) and _r, "skeleton({!r}) returns named rects".format(_k), str(_r))
    for _name, _v in _r.items():
        rects = _v if isinstance(_v, list) else [_v]
        check(all(len(t) == 4 and t[2] > 0 and t[3] > 0 for t in rects),
              "skeleton({!r})[{!r}] is a positive rect".format(_k, _name), str(_v))
try:
    dk.skeleton(_sl, "nosuch")
    check(False, "an unknown skeleton kind raises", "it returned a default")
except ValueError:
    check(True, "an unknown kind raises rather than silently returning a default — a typo that "
                "returns one architecture under eight names is the failure this prevents")

# The claim the whole feature rests on: lint must SEE these as distinct skeletons. Its fingerprint
# is (shape-class, left, top, width) in half-inch buckets, so architectures that differ only in
# name would score as one and the helper would be decoration.
def _showcase():
    import io
    import contextlib
    prs = dk.blank_deck()
    for k in dk.SKELETONS:
        s = dk.add_slide(prs)
        dk.box(s, 0, 0, 10, 5.625, fill=dk.TINT)
        r = dk.skeleton(s, k)
        for _n, v in r.items():
            for rc in (v if isinstance(v, list) else [v]):
                dk.box(s, rc[0], rc[1], rc[2], rc[3], fill=dk.DEEP)
    p = TMP / "showcase.pptx"
    prs.save(str(p))
    stats = {}
    with contextlib.redirect_stdout(io.StringIO()):
        ld.lint(str(p), mode="presented", renders_dir=None, static_ok=True, stats_out=stats)
    return stats


_st = _showcase()
check(_st.get("distinct_skeletons", 0) >= 8,
      "all eight architectures register as DISTINCT skeletons to lint ({}) — the fingerprint is "
      "geometric, so a set that differed only in name would score as one"
      .format(_st.get("distinct_skeletons")), str(_st.get("distinct_skeletons")))

# ── 2. the planner clears the floors it is written against ──────────────────────────────────
_rows = pr.plan(["cover", "context", "problem", "method", "method", "result", "result",
                 "compare", "evidence", "takeaway", "next", "close"], carry=(6, 9))
check(not pr.check(_rows), "a planned 12-slide argument clears SKELETON VARIETY and LAYOUT SAMENESS",
      str(pr.check(_rows)))
check(len({k for _i, _r, k, _w in _rows}) >= 4,
      "...with at least lint's 4-skeleton floor ({} distinct)"
      .format(len({k for _i, _r, k, _w in _rows})))
check(not pr.check(pr.plan(["result"] * 12)),
      "twelve IDENTICAL roles still clear both floors — the rotation carries a deck whose content "
      "gives the planner nothing to work with")
check({k for i, _r, k, _w in pr.plan(["context"] * 10, carry=(4, 7)) if i in (4, 7)}
      & {"full_bleed", "island", "statement"},
      "a carry slide gets an architecture that can hold a signature move")
check(pr.plan([]) == [], "an empty deck plans nothing rather than raising")
check({k for _i, _r, k, _w in pr.plan(list(pr.ROLE_FIT) + ["unknown"] * 4)} <= set(dk.SKELETONS),
      "every architecture the planner proposes is one deckkit can actually build — the planner and "
      "the builder cannot drift apart")

# ── 3. planning beats improvising, on the same content ──────────────────────────────────────
def _deck(kinds):
    import io
    import contextlib
    prs = dk.blank_deck()
    for i, k in enumerate(kinds):
        s = dk.add_slide(prs)
        dk.box(s, 0, 0, 10, 5.625, fill=dk.TINT)
        dk.text(s, 0.6, 0.35, 8.8, 0.6, [[("Heading %d" % (i + 1), 24, dk.DEEP, True, False)]])
        r = dk.skeleton(s, k, flip=(i % 4 == 3))
        for _n, v in r.items():
            for rc in (v if isinstance(v, list) else [v]):
                dk.box(s, rc[0], rc[1], rc[2], rc[3], fill=dk.WHITE)
    p = TMP / ("d%d.pptx" % len(kinds))
    prs.save(str(p))
    stats = {}
    with contextlib.redirect_stdout(io.StringIO()):
        ld.lint(str(p), mode="presented", renders_dir=None, static_ok=True, stats_out=stats)
    return stats.get("distinct_skeletons", 0)


_improvised = _deck(["split"] * 12)
_planned = _deck([k for _i, _r, k, _w in _rows])
check(_planned > _improvised * 2,
      "the same content planned scores far more distinct architectures than improvised "
      "({} vs {})".format(_planned, _improvised), "{} vs {}".format(_planned, _improvised))

# ── 4. the look cues separate a dead deck from a varied one ─────────────────────────────────
from PIL import Image, ImageDraw          # noqa: E402


def _pages(name, drawer, n=6):
    d = TMP / name
    d.mkdir(exist_ok=True)
    for i in range(n):
        im = Image.new("RGB", (960, 540), (244, 242, 238))
        drawer(ImageDraw.Draw(im), i)
        im.save(d / ("slide%02d.png" % (i + 1)))
    return d


_flat = _pages("flat", lambda dr, i: dr.rectangle([60, 60, 900, 300], fill=(230, 227, 220)))
_varied = _pages("varied", lambda dr, i: (
    dr.rectangle([0, 0, 960, 540], fill=(20, 24, 30)) if i % 3 == 0 else
    dr.rectangle([60, 60, 460, 480], fill=(176, 74, 42)) if i % 3 == 1 else
    dr.rectangle([300, 180, 660, 360], fill=(230, 227, 220))))
_flat_n = sum(1 for ln in cc.report(cc.deck_cues(str(_flat))) if "flat across" in ln)
_var_n = sum(1 for ln in cc.report(cc.deck_cues(str(_varied))) if "flat across" in ln)
check(_flat_n > _var_n,
      "the look cues report more FLAT cues on a deck of identical pages than on a varied one "
      "({} vs {}) — the signal no fault check produces".format(_flat_n, _var_n),
      "{} vs {}".format(_flat_n, _var_n))
_c = cc.cues(str(next(_varied.glob("slide01.png"))))
check(set(_c) == set(cc.ORDER), "every one of the seven cues is computed", str(sorted(_c)))
check(all(0.0 <= v <= 1.0 for v in _c.values()), "every cue is normalised to 0..1", str(_c))

# A dark register's ground IS its whitespace. A naive brightness measure calls a dark deck 100%
# full, which would penalise 8 of this skill's 18 registers.
_dark = _pages("dark", lambda dr, i: dr.rectangle([0, 0, 960, 540], fill=(16, 20, 26)), n=2)
check(cc.cues(str(next(_dark.glob("slide01.png"))))["whitespace"] > 0.8,
      "a DARK page reads as mostly whitespace — 8 of the 18 registers are dark and none of them "
      "is a full page")

print("\n".join("  ok   " + m for m in OKS))
if FAILS:
    print("\n".join("  FAIL " + m for m in FAILS))
print("\n{} passed, {} failed".format(len(OKS), len(FAILS)))
raise SystemExit(1 if FAILS else 0)
