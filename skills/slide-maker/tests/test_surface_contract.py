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


def build(fmt_name, runs):
    f = formats.get(fmt_name)
    prs = dk.blank_deck(f.w_in, f.h_in)
    s = dk.add_slide(prs)
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
        ("Measured over every deck the skill built.", 26, 1.6, 9.2, 14.0, 12.0),
        ("Results", 42, 17.5, 7.5, 14.0, 1.4),
        ("Two prose rules now fail loudly.", 26, 17.5, 9.2, 14.0, 12.0),
        ("Limitations", 42, 1.6, 23.0, 14.0, 1.4),
        ("One site, one operator, no held-out cohort.", 26, 1.6, 24.7, 14.0, 19.0),
        ("Next", 42, 17.5, 23.0, 14.0, 1.4),
        ("Record accent hexes in the look history.", 26, 17.5, 24.7, 14.0, 19.0)]
probs, facts = cs.check(build("poster_a0", FULL))
check(not probs, "a well-set A0 poster passes clean", "{} ({})".format(probs, facts))

# REGRESSION: a 27pt body must not be mistaken for a section head and judged against 36pt.
body27 = [r if r[1] != 26 else (r[0], 27, r[2], r[3], r[4], r[5]) for r in FULL]
check("TYPE FLOOR" not in codes(build("poster_a0", body27)),
      "a 27pt body clears the 24pt body floor and is NOT judged against the 36pt section floor",
      "the first version guessed the role from the size, then judged the size against that role")

# The trap the format exists for: a poster typeset like a slide.
slideish = build("poster_a0", [("A result worth crossing a hall for", 46, 1.6, 1.6, 29.9, 4.0),
                               ("Methods", 20, 1.6, 8.0, 29.9, 16.0),
                               ("Limitations: one site only.", 14, 1.6, 25.0, 29.9, 18.0)])
msgs = [m for c, m in cs.check(slideish)[0] if c == "TYPE FLOOR"]
check(len(msgs) >= 2, "a poster typeset at SLIDE sizes fails the body AND the display floor",
      "{} TYPE FLOOR finding(s)".format(len(msgs)))

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
                         ("Wij hebben elk gebouwd deck gemeten.", 26, 1.6, 9.2, 14.0, 12.0),
                         ("Resultaten", 42, 17.5, 7.5, 14.0, 1.4),
                         ("Twee regels falen nu luid.", 26, 17.5, 9.2, 14.0, 12.0),
                         ("Beperkingen", 42, 1.6, 23.0, 14.0, 1.4),
                         ("Een locatie, een operator.", 26, 1.6, 24.7, 14.0, 19.0),
                         ("Vervolg", 42, 17.5, 23.0, 14.0, 1.4),
                         ("Leg accentkleuren vast.", 26, 17.5, 24.7, 14.0, 19.0)])
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
