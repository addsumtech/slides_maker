#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A canvas format's contract must bind the BUILT deck, not just describe it.

WHY. `formats.py` is the registry of design surfaces — margins, platform-UI safe zones, whether
columns work, whether the surface carries deck chrome, how dense it may be — and
`references/canvas-formats.md` states a per-format rule for each. Measured by grep before this
suite existed: `import formats` appeared in exactly TWO files, `formats.py` itself and
`extract_pdf.py`. Both are producers. Nothing downstream ever read the registry, so a build script
opted into it voluntarily and no check afterwards could tell whether it had.

That made every per-surface rule advisory on precisely the surfaces where the mistake is least
recoverable. A caption placed under the swipe bar of a 9:16 story looks correct to whoever built it
on a desktop and is covered in the app. A poster is wrong only after it has been printed a metre
wide — and the poster case did not exist at all: the registry had no A0/A1 canvas, so a conference
board was built as an oversized slide, where deckkit's own 46pt cover cap prints a title that
cannot be read across a hall and lint's canvas-RELATIVE type floor would have demanded a nonsense
~45pt body. Printed surfaces are read at a FIXED distance; their point sizes are absolute.

Three of these cases are regressions against real measurements:
  * a 27pt body on an A0 board was flagged for failing a 36pt SECTION floor, because the first
    version guessed a run's role from its size and then judged the size against that role;
  * a real A0 render covered 43% of the board — visibly half empty — and passed every gate that
    existed, because lint's surface mode switches the density budgets OFF;
  * a normal 16:9 deck must stay untouched by all of it.

Run: python3 tests/test_surface_contract.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_surface as cs        # noqa: E402
import deckkit as dk              # noqa: E402
import formats                    # noqa: E402

OKS: list[str] = []
FAILS: list[str] = []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="surface-contract-"))
_n = [0]


def check(cond, msg, detail=""):
    (OKS if cond else FAILS).append(msg if cond else "{} — {}".format(msg, detail))


def build(fmt_name, runs, figures=()):
    """`figures` are stand-in graphic blocks — a board that is all prose fails PROPORTION, which is
    the point of that check, so every fixture that must PASS carries real figures like a real board."""
    f = formats.get(fmt_name)
    prs = dk.blank_deck(f.w_in, f.h_in)
    s = dk.add_slide(prs)
    for fx, fy, fw, fh in figures:
        dk.box(s, fx, fy, fw, fh, fill=dk.TINT)
    for txt, pt, x, y, w, h in runs:
        dk.text(s, x, y, w, h, [[(txt, pt, dk.DEEP, False, False)]])
    _n[0] += 1
    path = TMP / ("%s-%d.pptx" % (fmt_name, _n[0]))
    prs.save(str(path))
    return path


def codes(path, **kw):
    return {c for c, _ in cs.check(path, **kw)[0]}


# ── 1. the registry now describes a printed board at all ─────────────────────────────────────
for name, w, h in (("a0", 33.11, 46.81), ("a1", 23.39, 33.11)):
    f = formats.get(name)
    check(abs(f.w_in - w) < 0.02 and abs(f.h_in - h) < 0.02,
          "{} resolves to a true {} canvas".format(name, name.upper()),
          "{}x{}".format(f.w_in, f.h_in))
    fl = formats.floors(f)
    check(set(fl) == {"display", "section", "body"} and fl["display"] > fl["section"] > fl["body"],
          "{} declares three ABSOLUTE reading-distance floors".format(name), str(fl))
    check(formats.match(f.w_in, f.h_in) is f,
          "a built {} canvas can be matched back to its format".format(name),
          "a check that cannot recover the format cannot apply the contract")

check(not formats.get("wide").type_floors,
      "a PROJECTED canvas declares no absolute floors — the inch-normalization rule governs there, "
      "and applying a printed floor to a slide would be noise")

# ── 2. the poster contract, on real built decks ──────────────────────────────────────────────
FULL = [("A result worth crossing a hall for", 110, 1.6, 1.6, 29.9, 4.4),
        ("Methods", 42, 1.6, 7.5, 14.0, 1.4),
        ("Measured over every deck the skill built.", 26, 1.6, 9.2, 14.0, 2.4),
        ("Results", 42, 17.5, 7.5, 14.0, 1.4),
        ("Two prose rules now fail loudly.", 26, 17.5, 9.2, 14.0, 2.4),
        ("Limitations", 42, 1.6, 26.5, 14.0, 1.4),
        ("One site, one operator, no held-out cohort.", 26, 1.6, 28.2, 14.0, 2.4),
        ("Next", 42, 17.5, 26.5, 14.0, 1.4),
        ("Record accent hexes in the look history.", 26, 17.5, 28.2, 14.0, 2.4)]
FIGS = [(1.6, 12.4, 14.0, 12.8), (17.5, 12.4, 14.0, 12.8), (1.6, 31.4, 29.9, 13.4)]
probs, facts = cs.check(build("poster_a0", FULL, FIGS))
check(not probs, "a well-set A0 poster passes clean", "{} ({})".format(probs, facts))

# REGRESSION: a 27pt body must not be mistaken for a section head and judged against 36pt.
body27 = [r if r[1] != 26 else (r[0], 27, r[2], r[3], r[4], r[5]) for r in FULL]
check("TYPE FLOOR" not in codes(build("poster_a0", body27, FIGS)),
      "a 27pt body clears the 24pt body floor and is NOT judged against the 36pt section floor",
      "the first version guessed the role from the size, then judged the size against that role")

# The trap the format exists for: a poster typeset like a slide.
slideish = build("poster_a0", [("A result worth crossing a hall for", 46, 1.6, 1.6, 29.9, 4.0),
                               ("Methods", 20, 1.6, 8.0, 29.9, 16.0),
                               ("Limitations: one site only.", 14, 1.6, 25.0, 29.9, 18.0)])
msgs = [m for c, m in cs.check(slideish)[0] if c == "TYPE FLOOR"]
check(len(msgs) >= 2, "a poster typeset at SLIDE sizes fails the body AND the display floor",
      "{} TYPE FLOOR finding(s)".format(len(msgs)))

# PROPORTION: a board can be FULL and still be a wall of prose, and the title must not be counted
# as prose — a poster title is a required element and is supposed to be enormous. Measured: a
# landscape A0 with a correct 110pt title scored 46% text and failed while its body was four short
# lines, which penalised exactly the boards that size their title right.
check("PROPORTION" in codes(build("poster_a0", FULL)),
      "the same board with NO figures fails PROPORTION — FILL says the board is used, PROPORTION "
      "says used by what", "got {}".format(codes(build("poster_a0", FULL))))
_p, _f = cs.check(build("poster_a0", FULL, FIGS))
check("PROPORTION" not in {c for c, _ in _p},
      "...and with figures it passes ({})".format(_f.get("proportion")), str(_f))
_huge_title = [(t, 200 if pt == 110 else pt, x, y, w, h) for t, pt, x, y, w, h in FULL]
_p, _f = cs.check(build("poster_a0", _huge_title, FIGS))
check("PROPORTION" not in {c for c, _ in _p},
      "a BIGGER title does not push a board over the prose cap — headlines are navigation, "
      "not text to read ({})".format(_f.get("proportion")), str(_f))
_wordy = [(t if pt != 26 else (t + " ") * 12, pt, x, y, w, h) for t, pt, x, y, w, h in FULL]
check("TEXT BLOCK" in codes(build("poster_a0", _wordy, FIGS)),
      "a block past ~50 words is caught — nobody reads a paragraph standing at a poster",
      "got {}".format(codes(build("poster_a0", _wordy, FIGS))))

# REGRESSION: a half-empty board. Measured at 43% on a real A0 render that passed every gate.
sparse = build("poster_a0", [("A result worth crossing a hall for", 110, 1.6, 1.6, 29.9, 4.4),
                             ("Methods", 42, 1.6, 8.0, 14.0, 1.4),
                             ("Short.", 26, 1.6, 9.7, 14.0, 2.0),
                             ("Limitations", 42, 17.5, 8.0, 14.0, 1.4),
                             ("Also short.", 26, 17.5, 9.7, 14.0, 2.0)])
probs, facts = cs.check(sparse)
check("FILL" in {c for c, _ in probs},
      "a half-empty board is caught — lint's surface mode switches the density budgets OFF, so "
      "nothing measured this before ({})".format(facts.get("fill")),
      str(facts))

# Required content: the billboard style drops exactly what a passer-by cannot reconstruct.
bill = build("poster_a0", [("Ours wins", 140, 1.6, 1.6, 29.9, 12.0),
                           ("One number, very large.", 30, 1.6, 15.0, 29.9, 28.0)])
missing = [m for c, m in cs.check(bill)[0] if c == "MISSING SECTION"]
check(len(missing) == 2, "methods AND limitations are each required, and each reported",
      "{} finding(s)".format(len(missing)))
check("MISSING SECTION" not in codes(bill, waive_sections="a purely descriptive display board"),
      "a written waiver stands that requirement down")

# A poster not written in English or Chinese must be teachable, not waived away. Measured: the
# Dutch heading "Beperkingen" matches none of the built-in limitation words (while "Methode"
# happens to contain "method"), so without an extension point the check would tell a correct
# poster it has no limitations section — and the only escape would switch the check OFF.
nl = build("poster_a0", [("Een resultaat dat de zaal doorkruist", 110, 1.6, 1.6, 29.9, 4.4),
                         ("Methode", 42, 1.6, 7.5, 14.0, 1.4),
                         ("Wij hebben elk gebouwd deck gemeten.", 26, 1.6, 9.2, 14.0, 2.4),
                         ("Resultaten", 42, 17.5, 7.5, 14.0, 1.4),
                         ("Twee regels falen nu luid.", 26, 17.5, 9.2, 14.0, 2.4),
                         ("Beperkingen", 42, 1.6, 26.5, 14.0, 1.4),
                         ("Een locatie, een operator.", 26, 1.6, 28.2, 14.0, 2.4),
                         ("Vervolg", 42, 17.5, 26.5, 14.0, 1.4),
                         ("Leg accentkleuren vast.", 26, 17.5, 28.2, 14.0, 2.4)], FIGS)
check("MISSING SECTION" in codes(nl),
      "a Dutch poster trips MISSING SECTION on the built-in English/Chinese word lists",
      "if it did not, the extension point below would be untested")
check(not codes(nl, extra_terms={"limitations": ["beperking", "beperkingen"]}),
      "...and `surface_section_terms` TEACHES the check that language instead of waiving it off",
      str(codes(nl, extra_terms={"limitations": ["beperking", "beperkingen"]})))

# ── 3. the rules that were prose for the social surfaces ─────────────────────────────────────
story = build("story", [("Swipe up for the rest", 18, 0.5, 9.3, 4.6, 0.5),
                        ("left column", 16, 0.45, 4.0, 2.2, 1.2),
                        ("right column", 16, 2.9, 4.0, 2.2, 1.2)])
got = codes(story)
check("SAFE ZONE" in got, "text inside a 9:16 platform-UI zone is caught", str(got))
check("COLUMNS" in got, "a side-by-side split on a columns_ok=False surface is caught", str(got))

# REGRESSION: the rednote layout DNA `references/canvas-formats.md` PRESCRIBES — "payoff/handle
# bottom" — must not read as deck chrome, and a real `deckkit.footer()` / `page_marker()` must.
# The first version tested GEOMETRY (a wide strip low on the card) and got both backwards: it fired
# on the prescribed payoff line and missed a real footer, whose tag and page number are two NARROW
# shapes at opposite ends.
fr = formats.get("red")
BX, BY, BW, _BH = formats.band(fr)
payoff = build("red", [("A hook that fits the card", 30, BX, BY, BW, 1.4),
                       ("One idea, stacked.", 18, BX, BY + 2.0, BW, 2.0),
                       ("@handle · 收藏起来", 14, BX, 8.6, BW, 0.4)])
check("DECK CHROME" not in codes(payoff),
      "the prescribed rednote payoff/handle line is NOT read as deck chrome",
      "got {} — the skill's own layout DNA must pass its own gate".format(codes(payoff)))


def _with(fn):
    f = formats.get("red")
    prs = dk.blank_deck(f.w_in, f.h_in)
    sl = dk.add_slide(prs)
    dk.text(sl, BX, BY, BW, 1.4, [[("A hook", 30, dk.DEEP, False, False)]])
    fn(sl)
    _n[0] += 1
    path = TMP / ("red-chrome-%d.pptx" % _n[0])
    prs.save(str(path))
    return path


check("DECK CHROME" in codes(_with(lambda sl: dk.footer(sl, tag="deck name", page=3))),
      "a real deckkit.footer() on a social surface IS caught")
check("DECK CHROME" in codes(_with(lambda sl: dk.page_marker(sl, 3, 14))),
      "so is a page marker — furniture is identified by what it says, not where it sits")

# REGRESSION: COLUMNS must mean a split of running COPY. A stat pair, a chip row and two icon
# captions all sit side by side on a portrait card and none of them halves anyone's measure.
stats = build("red", [("Two numbers", 30, BX, BY, BW, 1.2),
                      ("62%", 26, BX, BY + 1.6, 2.8, 0.5),
                      ("3.1x", 26, BX + 3.4, BY + 1.6, 2.8, 0.5)])
check("COLUMNS" not in codes(stats), "a two-up stat pair is a legitimate portrait form",
      "got {}".format(codes(stats)))
split = build("red", [("Two columns of copy", 30, BX, BY, BW, 1.2),
                      ("Left column of running body copy that halves the measure.",
                       16, BX, BY + 1.6, 3.0, 2.4),
                      ("Right column of running body copy beside it.",
                       16, BX + 3.3, BY + 1.6, 3.0, 2.4)])
check("COLUMNS" in codes(split), "...and a real two-column body split still is",
      "got {}".format(codes(split)))

# Landscape boards are as standard as portrait ones. An unregistered canvas reports NOT CHECKED,
# so omitting them would have switched the whole contract off for half the posters printed.
for name, w, h in (("a0-landscape", 46.81, 33.11), ("a1-landscape", 33.11, 23.39)):
    f = formats.get(name)
    check(abs(f.w_in - w) < 0.02 and abs(f.h_in - h) < 0.02 and f.kind == "landscape"
          and formats.floors(f) == formats.floors(formats.get(name.split("-")[0]))
          and f.required_sections and f.fill_range,
          "{} is registered, landscape, and carries the same printed contract".format(name),
          "{}x{} {} {}".format(f.w_in, f.h_in, f.kind, formats.floors(f)))
land = build("poster_a0_land",
             [("A claim across the hall", 110, 1.6, 1.6, 43.0, 4.4),
              ("Methods", 42, 1.6, 7.5, 20.0, 1.4),
              ("Measured on every built deck.", 26, 1.6, 9.2, 20.0, 2.2),
              ("Results", 42, 24.0, 7.5, 20.0, 1.4),
              ("Two rules now fail loudly.", 26, 24.0, 9.2, 20.0, 2.2),
              ("Limitations", 42, 1.6, 22.5, 20.0, 1.4),
              ("One site, one operator.", 26, 1.6, 24.2, 20.0, 2.2),
              ("Next", 42, 24.0, 22.5, 20.0, 1.4),
              ("Record accent hexes.", 26, 24.0, 24.2, 20.0, 2.2)],
             [(1.6, 12.0, 20.0, 9.0), (24.0, 12.0, 20.0, 9.0), (1.6, 27.0, 42.4, 4.5)])
probs, facts = cs.check(land)
check(not probs and facts.get("format", "").startswith("poster_a0_land"),
      "a well-set LANDSCAPE A0 board resolves and passes", "{} {}".format(probs, facts))
bad_land = build("poster_a0_land", [("Slide-sized title", 46, 2.0, 2.0, 42.0, 3.0),
                                    ("Methods and limitations, at 14pt.", 14, 2.0, 8.0, 42.0, 20.0)])
check("TYPE FLOOR" in codes(bad_land), "...and a landscape board typeset like a slide is caught",
      "got {}".format(codes(bad_land)))

# FILL measures the area COMMITTED to content blocks, which is all a PPTX can answer — it cannot
# tell a full panel from an empty one. Measured on a real A0 board: 82% committed, 17% inked. The
# gap is REPORTED rather than thresholded, because two poster renders is not a calibration set,
# and lint_deck's calibrated HOLLOW FILL is switched off in --surface mode so nobody was reporting
# either number on a board.
import tempfile as _tf                                                    # noqa: E402
from PIL import Image as _Im                                              # noqa: E402
_rd = pathlib.Path(_tf.mkdtemp()) / "render"
_rd.mkdir(parents=True)
_im = _Im.new("RGB", (400, 560), (0x18, 0x1E, 0x26))
for _y in range(20, 60):                       # a thin band of ink on a big ground
    for _x in range(20, 300):
        _im.putpixel((_x, _y), (0xE2, 0x5A, 0x33))
_im.save(_rd / "slide01.png")
_probs, _facts = cs.check(build("poster_a0", FULL, FIGS), renders=str(_rd))
check("committed" in (_facts.get("fill") or "") and _facts.get("ink"),
      "FILL says COMMITTED, and the render's real ink share is reported beside it",
      "{} / {}".format(_facts.get("fill"), _facts.get("ink")))
check("large gap" in (_facts.get("ink") or ""),
      "...and a wide gap between the two is named, so 82%% committed is never read as 82%% full",
      str(_facts.get("ink")))
_probs, _facts = cs.check(build("poster_a0", FULL, FIGS))
check(_facts.get("fill") and not _facts.get("ink"),
      "with no renders the check still runs and simply says nothing about ink",
      "{} / {}".format(_facts.get("fill"), _facts.get("ink")))

# A deck with no slides must be NOT CHECKED, never a pile of findings about content it cannot have.
prs = dk.blank_deck(formats.get("a0").w_in, formats.get("a0").h_in)
blank = TMP / "blank-a0.pptx"
prs.save(str(blank))
probs, facts = cs.check(blank)
check(not probs and facts.get("note"), "a deck with no slides is reported, not judged", str(facts))

wide = build("wide", [("A normal projected slide", 24, 0.6, 0.6, 8.8, 1.0),
                      ("Body copy at a normal projected size.", 14, 0.6, 2.0, 4.0, 1.0),
                      ("A second column, which 16:9 allows.", 14, 5.2, 2.0, 4.0, 1.0)])
check(not codes(wide), "a normal 16:9 deck is untouched by every one of these rules",
      str(codes(wide)))

# An unregistered canvas must report NOT CHECKED, never clean.
prs = dk.blank_deck(12.34, 3.21)
dk.add_slide(prs)
odd = TMP / "odd.pptx"
prs.save(str(odd))
probs, facts = cs.check(odd)
check(not probs and facts.get("note"),
      "an unregistered canvas is reported as unchecked rather than passed", str(facts))

# ── 4. the wiring: the registry is no longer producer-only ───────────────────────────────────
render = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
codex = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")
check("_gate_section('surface')" in render, "render_deck.py registers a `surface` gate section")
check("import check_surface" in render, "render_deck.py delegates to the checker module")
check("check_surface.py" in codex and "check_surface_contract(evidence" in codex,
      "the codex delivery gate runs the same checker — a rule enforced on one runtime only drifts")

r = subprocess.run([sys.executable, str(SCRIPTS / "check_surface.py"), "--selftest"],
                   capture_output=True, text=True)
check(r.returncode == 0, "check_surface.py --selftest passes", (r.stdout + r.stderr)[-400:])

print("\n".join("  ok   " + m for m in OKS))
if FAILS:
    print("\n".join("  FAIL " + m for m in FAILS))
print("\n{} passed, {} failed".format(len(OKS), len(FAILS)))
raise SystemExit(1 if FAILS else 0)
