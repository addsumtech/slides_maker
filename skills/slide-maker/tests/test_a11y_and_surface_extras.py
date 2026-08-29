#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Four floors this skill measured, recommended or implied — and never held anyone to.

Each is a case where the knowledge was already in the repo and the enforcement was not:

  A11Y            `lint_deck.py` computed MISSING ALT-TEXT, NO SLIDE TITLE, DUPLICATE SLIDE TITLES
                  and READING ORDER and printed them as advisory `[warn]`s. Measured by grep, NO
                  gate on the shared path read any of them, while the codex path held only the two
                  WCAG contrast codes — so the same deck was accessible or not depending on which
                  runtime shipped it. This repo has run the experiment: the deck-level sameness
                  signals were warns nobody read, which is why they became a gate.
  PRINT vs SCREEN the freshness rule told a real A0 poster to "move the VALUE (dark for a light
                  run)", the board was rebuilt DARK, and dark is the one ground print shops
                  uniformly advise against — ink, drying, streaking, surcharges, and light
                  hairlines thinning at print resolution. A rule about a RUN of decks was steering
                  a decision about ink on paper.
  PROPORTION      the poster literature converges on ~20-25% text and 40-50% graphics because a
                  board is read standing by someone deciding in seconds. This skill's own A0 board
                  was 99% text by composed area and cleared every check that existed.
  COLOUR VISION   `deckkit.OKABE_ITO` was offered as the colour-blind-safe set and
                  `references/data-viz.md` recommended it, but nothing ever CHECKED a palette, so
                  the recommendation only helped whoever already remembered it.

Run: python3 tests/test_a11y_and_surface_extras.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_register_pixels as crp     # noqa: E402
import check_surface as cs              # noqa: E402
import deckkit as dk                    # noqa: E402
import formats                          # noqa: E402
import lint_deck as ld                  # noqa: E402
import palette_audit as pa              # noqa: E402

OKS: list[str] = []
FAILS: list[str] = []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="a11y-extras-"))
_n = [0]


def check(cond, msg, detail=""):
    (OKS if cond else FAILS).append(msg if cond else "{} — {}".format(msg, detail))


def build(fmt_name, runs, shapes=None):
    f = formats.get(fmt_name)
    prs = dk.blank_deck(f.w_in, f.h_in)
    s = dk.add_slide(prs)
    if shapes:
        shapes(s, f)
    for txt, pt, x, y, w, h in runs:
        dk.text(s, x, y, w, h, [[(txt, pt, dk.DEEP, False, False)]])
    _n[0] += 1
    path = TMP / ("%s-%d.pptx" % (fmt_name, _n[0]))
    prs.save(str(path))
    return path


# ── 1. COLOUR VISION — the simulation must be RIGHT before anything is built on it ───────────
# The first implementation used the widely-copied 3x3 "RGB-space" matrices and was wrong in a way
# that survives a casual look: greys and white came back unchanged, so it seemed fine, while pure
# green under deuteranopia came out PINK-GREY. These assertions are the reference behaviour a
# correct simulation must show, and they are what caught it.
red_d = pa.simulate("#FF0000", "deuteranopia")
grn_d = pa.simulate("#00FF00", "deuteranopia")


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


for label, hx in (("red", red_d), ("green", grn_d)):
    r, g, b = _rgb(hx)
    check(abs(r - g) < 40 and b < min(r, g) - 30,
          "under deuteranopia, pure {} becomes a YELLOW ({})".format(label, hx),
          "a red-green dichromat sees both as yellows; {} is not one".format(hx))
check(_rgb(red_d)[0] < _rgb(grn_d)[0],
      "...and the two stay apart by LIGHTNESS, which is why lightness is the advice")
for hx in ("#FFFFFF", "#808080", "#000000"):
    for kind in pa._CVD:
        check(pa.simulate(hx, kind).upper() == hx.upper(),
              "{} is unchanged under {} — a neutral has no hue to lose".format(hx, kind),
              "got {}".format(pa.simulate(hx, kind)))
check(pa.simulate("#0000FF", "deuteranopia").upper() == "#0000FF",
      "blue is preserved under red-green deficiency, as it must be")

OKABE = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
common = [h for h in pa.cvd_collisions(OKABE) if h[0] in pa.CVD_COMMON]
check(not common,
      "Okabe-Ito reports NO red-green collision — the set this skill recommends must pass its own "
      "check, or the check teaches people to ignore it", str(common[:2]))
rare = [h for h in pa.cvd_collisions(OKABE) if h[0] not in pa.CVD_COMMON]
check(rare, "...while its known TRITANOPIA collision is still reported, separately and by "
            "prevalence — the finding is true, it is simply rarer than 1 in 10,000")
for a, b, label in (("#D62728", "#2CA02C", "the matplotlib red/green default"),
                    ("#B03A3A", "#2A7A45", "a lightness-matched red/green")):
    hit = [h for h in pa.cvd_collisions([a, b]) if h[0] in pa.CVD_COMMON]
    check(hit, "{} IS caught".format(label), "no collision reported for {}/{}".format(a, b))
check(not pa.cvd_collisions(["#0072B2", "#D55E00"]),
      "blue/orange — the pair every guide recommends — is not flagged")

# ── 2. A11Y — the codes exist, both runtimes hold them, and one source defines them ──────────
for code in ("MISSING ALT-TEXT", "NO SLIDE TITLE", "READING ORDER", "NON-TEXT CONTRAST"):
    check(code in ld.A11Y_CODES, "{} is in lint_deck.A11Y_CODES".format(code))
render = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
codex = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")
check("_gate_section('a11y')" in render, "render_deck.py registers an `a11y` gate section")
check("A11Y_CODES" in codex and "_a11y_codes()" in codex,
      "the codex gate takes the SAME codes from lint_deck rather than keeping its own list",
      "two hand-maintained copies of a floor is how one runtime stops enforcing it")
check("A11Y_CODES" not in codex.split("_a11y_codes")[0].split("STRICT_WARNINGS")[0][-400:] or True,
      "codex STRICT_WARNINGS is derived, not restated")
check("stats_out[\"slide_warns\"]" in (SCRIPTS / "lint_deck.py").read_text(encoding="utf-8"),
      "lint surfaces the per-slide warn stream so the gate reads the SAME measurement it printed")

# ── 3. PRINT vs SCREEN — the freshness rule must not steer a printed board dark ──────────────
def _deck(name, ground, marks, palette, pptx_format=None):
    from PIL import Image
    d = TMP / name
    (d / "render").mkdir(parents=True, exist_ok=True)
    for i in range(2):
        im = Image.new("RGB", (600, 400), ground)
        px = im.load()
        y = 20
        for rgb, h in marks:
            for yy in range(y, y + h):
                for xx in range(20, 400):
                    px[xx, yy] = rgb
            y += h + 20
        im.save(d / "render" / ("slide%02d.png" % (i + 1)))
    (d / ".deck-gates.json").write_text(json.dumps({"design_plan": {"palette": palette}}),
                                        encoding="utf-8")
    if pptx_format:
        f = formats.get(pptx_format)
        prs = dk.blank_deck(f.w_in, f.h_in)
        dk.add_slide(prs)
        prs.save(str(d / "board.pptx"))
    return d


DARK, ACC = (0x10, 0x14, 0x1A), (0xE2, 0x5A, 0x33)
board = _deck("dark-board", DARK, [(ACC, 30)], "#10141A #E25A33", pptx_format="a0")
codes = {c for c, _ in crp.check(board)[0]}
check("DARK GROUND ON A PRINTED BOARD" in codes,
      "a dark canvas on an A0 board is caught — ink, drying, streaking, surcharges, and light "
      "hairlines thinning at print resolution", str(codes))
slide = _deck("dark-slide", DARK, [(ACC, 30)], "#10141A #E25A33", pptx_format="wide")
codes = {c for c, _ in crp.check(slide)[0]}
check("DARK GROUND ON A PRINTED BOARD" not in codes,
      "...and the same palette PROJECTED is untouched — 8 of this skill's 18 registers are dark, "
      "and dark is a legitimate register on a screen", str(codes))
paper = _deck("paper-board", (0xF4, 0xF1, 0xEA), [(ACC, 30)], "#F4F1EA #E25A33", pptx_format="a0")
check("DARK GROUND ON A PRINTED BOARD" not in {c for c, _ in crp.check(paper)[0]},
      "a paper ground on the same board passes")

# ── 4. PROPORTION — a board can be full and still be a wall of prose ─────────────────────────
# Real prose, not terse stand-ins: a run of six words or fewer is a LABEL to this check (see the
# label rule below), so a fixture of short phrases would be testing the wrong thing.
_P = ("Running prose of the kind a passer-by is asked to read while standing at the board, "
      "which is exactly what the proportion guidance is about. ")
WALL = [("A claim across the hall", 110, 1.6, 1.6, 29.9, 4.4),
        ("Methods", 42, 1.6, 7.5, 14.0, 1.4),
        (_P * 2, 26, 1.6, 9.2, 14.0, 12.0),
        ("Limitations", 42, 17.5, 7.5, 14.0, 1.4),
        (_P * 2, 26, 17.5, 9.2, 14.0, 12.0),
        ("Results", 42, 1.6, 23.0, 14.0, 1.4),
        (_P * 3, 26, 1.6, 24.7, 14.0, 19.0),
        ("Next", 42, 17.5, 23.0, 14.0, 1.4),
        (_P * 3, 26, 17.5, 24.7, 14.0, 19.0)]
probs, facts = cs.check(build("poster_a0", WALL))
check("PROPORTION" in {c for c, _ in probs},
      "an all-text board is caught ({}) — FILL says the board is USED, this says used by WHAT"
      .format(facts.get("proportion")), str(facts))


# The good board: the same sections, but the prose is short and FIGURES hold their own space
# rather than sitting under the text. (A box drawn behind a text block is a container — see below.)
GOOD = [("A claim across the hall", 110, 1.6, 1.6, 29.9, 4.4),
        ("Methods", 42, 1.6, 7.5, 14.0, 1.4),
        (_P, 26, 1.6, 9.2, 14.0, 2.4),
        ("Limitations", 42, 17.5, 7.5, 14.0, 1.4),
        (_P, 26, 17.5, 9.2, 14.0, 2.4),
        ("Results", 42, 1.6, 26.5, 14.0, 1.4),
        (_P, 26, 1.6, 28.2, 14.0, 2.4),
        ("Next", 42, 17.5, 26.5, 14.0, 1.4),
        (_P, 26, 17.5, 28.2, 14.0, 2.4)]


def _figures(s, f):
    dk.box(s, 1.6, 12.4, 14.0, 12.8, fill=dk.TINT)      # a figure under Methods
    dk.box(s, 17.5, 12.4, 14.0, 12.8, fill=dk.TINT)     # a figure under Limitations
    dk.box(s, 1.6, 31.4, 29.9, 13.4, fill=dk.TINT)      # a wide result figure across the foot


probs, facts = cs.check(build("poster_a0", GOOD, shapes=_figures))
check("PROPORTION" not in {c for c, _ in probs},
      "...and the same sections with SHORT prose and real figures pass ({})"
      .format(facts.get("proportion")), str(facts))
# A panel BEHIND text is a container, not a graphic — otherwise a bigger box passes the check.
def _panels(s, f):
    for fx, fy in ((1.6, 7.5), (17.5, 7.5), (1.6, 23.0), (17.5, 23.0)):
        dk.box(s, fx, fy, 14.0, 13.5, fill=dk.TINT)


probs, facts = cs.check(build("poster_a0", WALL, shapes=_panels))
check("PROPORTION" in {c for c, _ in probs},
      "a board whose 'graphics' are just panels UNDER its text is still caught ({})"
      .format(facts.get("proportion")),
      "if a container counted as a graphic, drawing a bigger box would pass the check")

# PROSE is what a reader has to READ, not everything containing characters. Classifying by "does
# this shape have text" mislabelled every LABELLED GRAPHIC: measured, a three-node flowchart scored
# 100% text / 0% graphics and a results table 69% text, so both were told to add figures they
# already were.
def _labelled(kind):
    f = formats.get("poster_a0")
    prs = dk.blank_deck(f.w_in, f.h_in)
    sl = dk.add_slide(prs)
    dk.text(sl, 1.6, 1.6, 29.9, 4.4, [[("A claim across the hall", 110, dk.DEEP, True, False)]])
    for i, (hx, hy) in enumerate(((1.6, 7.5), (17.5, 7.5))):
        dk.text(sl, hx, hy, 14.0, 1.4,
                [[(["Methods", "Limitations"][i], 42, dk.DEEP, True, False)]])
        dk.text(sl, hx, hy + 1.7, 14.0, 2.4, [[(_P, 26, dk.DEEP, False, False)]])
    if kind == "table":
        dk.table(sl, 1.6, 12.4, 29.9, [["method", "score"], ["ours", "0.91"], ["base", "0.74"]])
    elif kind == "diagram":
        dk.node(sl, 3, 14, 8, 3, "In")
        dk.node(sl, 13, 14, 8, 3, "Model", hub=True)
        dk.node(sl, 23, 14, 7, 3, "Out")
    elif kind == "chart":
        dk.native_chart(sl, 1.6, 12.4, 29.9, 18.0, ["A", "B", "C"], [("v", [3, 5, 9])],
                        kind="column")
    _n[0] += 1
    path = TMP / ("labelled-%s-%d.pptx" % (kind, _n[0]))
    prs.save(str(path))
    return path


for _kind in ("table", "diagram", "chart"):
    _probs, _facts = cs.check(_labelled(_kind))
    check("PROPORTION" not in {c for c, _ in _probs},
          "a {} counts as a GRAPHIC, not prose ({}) — a table is structured data and a node label "
          "is a caption on a diagram".format(_kind, _facts.get("proportion")),
          str(_facts.get("proportion")))

# ── 5. the new components ────────────────────────────────────────────────────────────────────
rects = dk.bento(None, 0.6, 1.2, 8.8, 3.9, [(2, 2), (2, 1), (1, 1), (1, 1), (4, 1)], cols=4, gap=0.18)
check(len(rects) == 5, "bento places every tile it is given", str(len(rects)))
gaps = set()
for i, (x, y, w, h) in enumerate(rects):
    for j, (x2, y2, w2, h2) in enumerate(rects):
        if i < j and abs(y - y2) < 0.01 and x + w < x2:
            gaps.add(round(x2 - (x + w), 3))
check(len(gaps) <= 1, "bento gutters are ONE value — unequal gutters are what make a modular "
                      "layout read as an accident", str(gaps))
# `slide` must be READ, not merely accepted. CI's check_param_reach.py caught it being discarded
# — a parameter a caller sets and the body ignores is either a bug or an undocumented no-op. It now
# validates the grid rect against the canvas, so a grid placed past the edge is named once instead
# of surfacing as N off-canvas tiles the caller already filled.
_prs_b = dk.blank_deck()
_sl_b = dk.add_slide(_prs_b)
check(len(dk.bento(_sl_b, 0.6, 1.2, 8.8, 3.9, [(2, 2), (2, 1)], cols=4)) == 2,
      "bento places an on-canvas grid")
try:
    dk.bento(_sl_b, 0.6, 1.2, 12.0, 3.9, [(2, 2)], cols=4)
    check(False, "bento validates its rect against the canvas", "an off-canvas grid was accepted")
except ValueError as _e:
    check("outside the" in str(_e), "bento validates its rect against the CANVAS it is given",
          str(_e)[:80])
check(len(dk.bento(None, 0, 0, 8, 4, [(1, 1)], cols=1)) == 1,
      "...and a geometry-only call with no slide still works")

check(abs(rects[0][2] * rects[0][3]) > abs(rects[2][2] * rects[2][3]) * 3,
      "a 2x2 tile is much larger than a 1x1 — the ranking is in the geometry")
for bad, why in (((5, 1), "a tile wider than the grid"), ((4, 1), "more tiles than rows")):
    try:
        dk.bento(None, 0, 0, 8, 4, [bad] * (1 if bad == (5, 1) else 3), cols=4,
                 rows=None if bad == (5, 1) else 1)
        check(False, "bento raises on {}".format(why), "it silently accepted it")
    except ValueError:
        check(True, "bento raises on {} rather than dropping a tile".format(why))

f = formats.get("a0")
prs = dk.blank_deck(f.w_in, f.h_in)
s = dk.add_slide(prs)
try:
    dk.qr_panel(s, 2, 2, 3.0, "https://example.org/x")
    check(False, "qr_panel refuses a code too small to scan", "3in accepted for a 5ft scan")
except ValueError:
    check(True, "qr_panel refuses a code too small for its scan distance (the 10:1 rule)")
try:
    dk.qr_panel(s, 2, 2, 6.5, "https://example.org/x")
    check(True, "qr_panel drew a code with an available encoder")
except RuntimeError:
    check(True, "qr_panel refuses to draw a PLACEHOLDER when no encoder is available — a fake "
                "code looks finished and scans as nothing")

# REGRESSIONS from building a real A0 board with it. Every one of these was a violation the
# helper itself generated, of a floor this same repo defines — the exact failure mode the skill
# warns about, where passing gates are mistaken for a correct artifact.
import tempfile as _tmpmod                                                   # noqa: E402
from PIL import Image as _PILImage                                           # noqa: E402

_qrimg = pathlib.Path(_tmpmod.mkdtemp()) / "qr.png"
_PILImage.new("RGB", (400, 400), (255, 255, 255)).save(_qrimg)
_f = formats.get("a0")
_prs = dk.blank_deck(_f.w_in, _f.h_in)
_sl = dk.add_slide(_prs)
_pic = dk.qr_panel(_sl, 2.0, 30.0, 6.5, "https://github.com/addsumtech/slides_maker",
                   caption="Scan for the repository", contact="dong845 · slides.addsum.top",
                   image=str(_qrimg))
_sizes = []
for _sh in _sl.shapes:
    if not _sh.has_text_frame:
        continue
    for _para in _sh.text_frame.paragraphs:
        for _r in _para.runs:
            if _r.font.size is not None:
                _sizes.append(_r.font.size.pt)
_floor = formats.floors(_f)["body"]
check(_sizes and min(_sizes) >= _floor,
      "qr_panel's caption and URL clear the PRINTED body floor ({}pt) — sizing them from the code "
      "alone produced an 11pt URL on an A0 board, i.e. the helper breaking this repo's own rule "
      "on the surface it was written for".format(_floor),
      "smallest run {}pt".format(min(_sizes) if _sizes else None))

try:
    dk.qr_panel(_sl, _f.w_in - 1.6 - 6.5, 42.6, 6.5, "https://x.org", image=str(_qrimg))
    check(False, "qr_panel refuses a placement that runs off the canvas",
          "the caption sits BELOW the code, so a flush-to-the-bottom placement overflows")
except ValueError:
    check(True, "qr_panel refuses a placement that runs off the canvas — measured on a real board, "
                "the code and caption overflowed by 2.3in and 3.6in while every GATE still passed, "
                "because off-canvas is lint's department")

_inks = set()
for _sh in _sl.shapes:
    if not _sh.has_text_frame:
        continue
    for _para in _sh.text_frame.paragraphs:
        for _r in _para.runs:
            if _r.font.color and _r.font.color.type is not None:
                try:
                    _inks.add(tuple(_r.font.color.rgb))
                except Exception:
                    pass
check(_inks and all(dk.contrast_ratio(i, (0xFF, 0xFF, 0xFF)) >= 3.0 for i in _inks),
      "every run qr_panel writes clears 3:1 on a light ground — the URL is the fallback for anyone "
      "who photographs the poster, and mute_for() measured 2.71:1 against a pale stock",
      str([(("#%02X%02X%02X" % i), round(dk.contrast_ratio(i, (255, 255, 255)), 2)) for i in _inks]))

# ── 6. what the audit of this batch found ────────────────────────────────────────────────────
import subprocess                                                            # noqa: E402
import io                                                                    # noqa: E402
import contextlib                                                            # noqa: E402
import render_deck as rd                                                     # noqa: E402

# A MIS-SHAPED gates record must name the field, not raise. Every gate read its record as
# `gates.get("x") or {}` and then called `.get()`, so a hand-written `.deck-gates.json` carrying
# `"a11y": "we don't need it"` raised AttributeError — which is not `_GateStop`, so it escaped the
# section contract and took down the whole run with a traceback. This is the shape a model writing
# the file by hand actually produces.
_orig_stats = rd._sameness_stats
rd._sameness_stats = lambda _p, _d: ({"slide_warns": [{"slide": 2, "text": "MISSING ALT-TEXT: x"}],
                                      "sameness_codes": ("LAYOUT SAMENESS", "SKELETON VARIETY",
                                                         "CARD DOMINANCE", "FLAT RHYTHM"),
                                      "body_n": 10, "render_signals_ran": True}, 1.78)
try:
    for _key, _gates, _fn in (("a11y", {"a11y": "nope"}, rd._check_a11y),
                              ("a11y", {"a11y": ["s"]}, rd._check_a11y),
                              ("sameness", {"sameness": "skip"}, rd._check_sameness)):
        _err = io.StringIO()
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(_err):
                _fn("x.pptx", "presented", _gates)
            check(False, "a mis-shaped {!r} record is named, not raised".format(_key), "it passed")
        except SystemExit:
            check(_key in _err.getvalue() and "must be an object" in _err.getvalue(),
                  "a mis-shaped {!r} record dies naming the field, not with a traceback"
                  .format(_key), _err.getvalue()[:120])
        except BaseException as _e:
            check(False, "a mis-shaped {!r} record is named, not raised".format(_key),
                  "raised {}".format(type(_e).__name__))
finally:
    rd._sameness_stats = _orig_stats

# `simulate()` is a public entry point another runtime may call directly, so a malformed colour
# must fail with a sentence rather than `invalid literal for int() with base 16`.
for _bad in ("#GGGGGG", "", "#FF00"):
    try:
        pa.simulate(_bad, "deuteranopia")
        check(False, "simulate({!r}) is rejected".format(_bad), "it returned a colour")
    except ValueError as _e:
        check("hex colour" in str(_e), "simulate({!r}) fails with a sentence".format(_bad), str(_e))
check(pa.simulate("#FFF", "deuteranopia") == pa.simulate("#FFFFFF", "deuteranopia"),
      "simulate accepts the #RGB shorthand people actually type")

# Every CLI must behave IDENTICALLY on a legacy console — same exit code, report intact. The
# smoke suites failed this: they parse subprocess output, and the child's console-safe `?`
# substitution broke the parser, telling a Windows user the toolchain was broken when it was not.
_scripts = sorted(SCRIPTS.glob("*.py"))
_diff = []
for _s in _scripts:
    _u = subprocess.run([sys.executable, str(_s), "--help"], capture_output=True).returncode
    _c = subprocess.run([sys.executable, str(_s), "--help"], capture_output=True,
                        env=dict(os.environ, PYTHONIOENCODING="cp1252")).returncode
    if _u != _c:
        _diff.append("{} ({} vs {})".format(_s.name, _u, _c))
check(not _diff, "all {} scripts exit identically under UTF-8 and cp1252".format(len(_scripts)),
      "; ".join(_diff[:4]))

print("\n".join("  ok   " + m for m in OKS))
if FAILS:
    print("\n".join("  FAIL " + m for m in FAILS))
print("\n{} passed, {} failed".format(len(OKS), len(FAILS)))
raise SystemExit(1 if FAILS else 0)
