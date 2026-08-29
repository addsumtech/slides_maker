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

# The HOME BASE the workflow requires. `agents/slide-design.md`: when the direction gate chose a
# skeleton token, that skeleton "is the map's PLURALITY: the most-used home base, visibly the deck's
# default", because the user picked a composition from RENDERED options. A planner that rotated
# evenly would silently override the pick they actually looked at.
from collections import Counter                                              # noqa: E402

for _home in ("split", "island", "dashboard", "rail"):
    _r = pr.plan(["cover", "context", "method", "result", "result", "compare", "evidence",
                  "takeaway", "next", "close"], home=_home)
    _top = Counter(k for _i, _ro, k, _w in _r).most_common(1)[0][0]
    check(_top == _home and not pr.check(_r, home=_home),
          "home base {!r} becomes the plurality AND still clears both floors".format(_home),
          "plurality {} / {}".format(_top, pr.check(_r, home=_home)))
try:
    pr.plan(["a"] * 8, home="nosuch")
    check(False, "a typo'd home base is refused", "it reached the plan")
except ValueError:
    check(True, "a typo'd home base is refused — the planner may never propose an architecture "
                "deckkit cannot build")

# Found by planning a REAL deck: the two tools in this pipeline disagreed about what a role IS.
# `arc_divergence.py` prints a documented role vocabulary in its own template; 18 of those roles
# were unknown here, so an arc written in that vocabulary hit "no role given; rotating" on most of
# its pages and the role→architecture intelligence — the whole value of the file — silently did not
# fire. No error, no warning, and a plan no better than a rotation.
_ARC_ROLES = set("hook problem diagnosis framework idea framework-idea method evidence case-study "
                 "comparison roadmap conclusion call-to-action objective prerequisite concept "
                 "worked-example misconception counterexample practice check recap".split())
_unknown = sorted(_ARC_ROLES - set(pr.ROLE_FIT))
check(not _unknown,
      "every role arc_divergence documents is one plan_rhythm knows — two tools in one pipeline "
      "must not disagree about what a role is", "unknown: {}".format(_unknown))

# ...and the planner must never emit a plan its OWN checker rejects. Measured on that same deck: a
# cover plus three carry slides all reached for the boldest architecture and TIED the declared home.
_real = pr.plan(["cover", "problem", "diagnosis", "diagnosis", "framework", "method", "method",
                 "evidence", "method", "evidence", "diagnosis", "conclusion"],
                carry=(5, 10, 12), home="band")
check(not pr.check(_real, home="band"),
      "a real 12-slide plan with a home base clears its own checker — a planner that emits a plan "
      "its checker rejects is broken", str(pr.check(_real, home="band")))
check(all("no role given" not in w for _i, _r, _k, w in _real),
      "...and every row was matched on its ROLE, not filled by the rotation",
      str([w for _i, _r, _k, w in _real if "no role given" in w]))
check(pr.STRUCTURAL and "cover" in pr.STRUCTURAL,
      "structural pages are excluded from the plurality — a cover is not part of the body rhythm, "
      "which is the same convention arc_divergence states for its order axis")

# skeleton() must FAIL LOUDLY on a division that cannot fit, like its sibling bento(). Before this,
# n=99 cells / a gap wider than the band / weight at 0 or 1 returned NEGATIVE widths, which
# python-pptx accepts and renders as garbage far from the cause.
_p2 = dk.blank_deck()
_s2 = dk.add_slide(_p2)
for _label, _kw in (("99 cells", dict(n=99)), ("a gap wider than the band", dict(gap=9.0)),
                    ("a negative gap", dict(gap=-1.0)),
                    ("a source band of nothing", dict(band=(0, 0, 0.5, 0.4)))):
    try:
        dk.skeleton(_s2, "dashboard", **_kw)
        check(False, "skeleton refuses {}".format(_label), "it returned rects")
    except ValueError:
        check(True, "skeleton refuses {} rather than returning a negative rect".format(_label))
for _w in (0.0, 1.0):
    try:
        dk.skeleton(_s2, "split", weight=_w)
        check(False, "skeleton('split') refuses weight={}".format(_w), "it returned rects")
    except ValueError:
        check(True, "skeleton('split') refuses weight={} — one column would have no width"
              .format(_w))
# and every legitimate combination on every registered canvas still builds
import formats                                                               # noqa: E402
_broken = []
for _name in ("wide", "classic", "square", "red", "story", "a4", "a0", "a1", "a0-landscape"):
    _f = formats.get(_name)
    _p3 = dk.blank_deck(_f.w_in, _f.h_in)
    _s3 = dk.add_slide(_p3)
    for _k in dk.SKELETONS:
        for _fl in (False, True):
            try:
                _R = dk.skeleton(_s3, _k, flip=_fl)
                for _v in _R.values():
                    for _rc in (_v if isinstance(_v, list) else [_v]):
                        if _rc[2] <= 0 or _rc[3] <= 0:
                            _broken.append("{}/{}".format(_name, _k))
            except Exception as _e:
                _broken.append("{}/{}: {}".format(_name, _k, type(_e).__name__))
check(not _broken,
      "all eight architectures build on all nine registered canvases, both flips — 16:9 is where "
      "they were designed, not where they have to work", str(_broken[:3]))

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

# ── 5. WIRED, not orphaned ───────────────────────────────────────────────────────────────────
# The failure this audit actually found: all three tools shipped with a mention in SKILL.md and
# nothing else — 0 in the design agent that builds the rhythm map, 0 in the codex runbook a
# non-Claude runtime reads, 0 in the example scaffold. A capability nothing points at is the same
# as a capability that was never added, and this repo has recorded that lesson before.
ROOT = HERE.parent
_design = (ROOT / "agents" / "slide-design.md").read_text(encoding="utf-8")
_critic = (ROOT / "agents" / "critic.md").read_text(encoding="utf-8")
_codex = (ROOT / "references" / "codex-runtime.md").read_text(encoding="utf-8")
_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
_example = (ROOT / "references" / "examples" / "build_example_generic.py").read_text(encoding="utf-8")

check("plan_rhythm" in _design,
      "the DESIGN agent names plan_rhythm where it builds the rhythm map — the skeleton column is "
      "arithmetic it was previously asked to do by hand")
check("--home" in _design,
      "...and tells it to pass --home when a direction gate picked a composition, so the user's "
      "pick stays the deck's default")
check("skeleton(" in _design, "the design agent names the builder for what the plan proposes")
check("composition_cues" in _critic,
      "the CRITIC is told to read the composition cues on its distinctiveness axis")
check("NOT GATED" in _critic or "not gated" in _critic.lower(),
      "...and told they are reported, never a threshold")
check("plan_rhythm" in _codex and "composition_cues" in _codex,
      "the CODEX runbook names both — a non-Claude runtime never reads agents/, so a tool absent "
      "here does not exist for it")
check("deckkit.skeleton" in _codex, "...and the builder, with a runnable-example pointer")
check("plan_rhythm" in _skill and "composition_cues" in _skill,
      "SKILL.md names both (composition_cues had ZERO mentions when it shipped)")
check("skeleton(" in _example and "plan_rhythm" in _example,
      "the EXAMPLE scaffold demonstrates a real skeleton page — the specific failure this repo has "
      "on record: a new capability that never enters the scaffolding is the same as not adding it")

import sigs                                                                  # noqa: E402
check("skeleton" in sigs.EXAMPLES,
      "`sigs.py --example skeleton` hands back a runnable call, like every other form component")

print("\n".join("  ok   " + m for m in OKS))
if FAILS:
    print("\n".join("  FAIL " + m for m in FAILS))
print("\n{} passed, {} failed".format(len(OKS), len(FAILS)))
raise SystemExit(1 if FAILS else 0)
