#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEMPLATE-BOUND: the composition-boldness counterweight.

Every deck-level signal in lint_deck punishes TOO MUCH or TOO SAME; the timidity composite catches
a deck that is flat (no type hero, no colour, all-text). None of them catch the case this skill's
own build-record deck hit: boldness=bold, 11 distinct skeletons, and yet EVERY content page is a
variation of one safe rectangle — the daring all in the concept and the chrome, none in where the
ink sits. SKELETON VARIETY misses it because it scores skeletons "different" when their BODIES
differ. So TEMPLATE-BOUND measures the one thing that is a NECESSARY condition for timid
composition: not one interior page departs the default frame with a committed move (full-bleed,
statement-with-void, or a dominant typographic hero).

The load-bearing half is what it must stay SILENT on:
  - it is scoped to decks whose OWN design_plan.boldness is bold/experimental — sound restraint
    (conservative or undeclared) is legitimate and is never nudged;
  - one committed breakout page silences it — whether that breakout is genuinely INNOVATIVE is the
    critic's distinctiveness call, deliberately NOT a deterministic one, so this stays advisory and
    out of the blocking sameness/timidity composites;
  - it needs enough interior pages to be a pattern (≥8).

Run:  python3 tests/test_composition_boldness.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                                                  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def lint(pptx):
    r = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(pptx), "--static"],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


def build(dirpath, boldness, *, breakout=False, n=11):
    """A deck of `n` slides: a cover, n-2 interior pages, a closer. Every interior is a plain
    title + bullets in the safe rectangle (no breakout) UNLESS `breakout` — then slide 3 is a
    dominant typographic hero (a committed, distinctive composition)."""
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.box(s, 0, 0, 10, 5.625, fill=dk.DEEP)
    dk.text(s, 0.7, 2.2, 8.6, 1.0, [[("Cover", 40, dk.WHITE, True, False)]])
    for i in range(1, n - 1):
        s = dk.add_slide(prs)
        if breakout and i == 3:
            dk.text(s, 0.7, 1.6, 8.6, 2.2, [[("42", 90, dk.MAGENTA, True, False)]])
            dk.text(s, 0.7, 4.2, 8.6, 0.4,
                    [[("the one number that matters", 16, dk.DEEP, False, False)]])
        else:
            dk.title_bar(s, "A perfectly safe slide %d" % i, kicker="section")
            dk.bullet(s, 0.7, 1.7, 8.6, [("Point one", "some detail"),
                                         ("Point two", "more detail"),
                                         ("Point three", "and more")], size=17)
            dk.footer(s, "demo", page=i + 1)
    s = dk.add_slide(prs)
    dk.box(s, 0, 0, 10, 5.625, fill=dk.DEEP)
    dk.text(s, 0.7, 2.2, 8.6, 1.0, [[("Thanks", 40, dk.WHITE, True, False)]])
    out = os.path.join(dirpath, "deck.pptx")
    prs.save(out)
    dk.declare_delivery(out, "presented")            # writes .deck-gates.json in dirpath
    gp = os.path.join(dirpath, ".deck-gates.json")
    blob = json.load(open(gp)) if os.path.exists(gp) else {}
    blob.setdefault("design_plan", {})["boldness"] = boldness
    json.dump(blob, open(gp, "w"))
    return out


def fires(dirpath, **kw):
    return "TEMPLATE-BOUND" in lint(build(dirpath, **kw))


def main():
    print("composition-boldness (TEMPLATE-BOUND)")
    with tempfile.TemporaryDirectory() as td:
        # the measured defect: a bold-declared deck whose every interior sits in the safe rectangle
        d = os.path.join(td, "a"); os.makedirs(d)
        check("a bold-declared deck with no interior breakout is caught",
              fires(d, boldness="bold"))

        # one committed breakout page (a dominant hero) silences it
        d = os.path.join(td, "b"); os.makedirs(d)
        check("one decisive breakout composition silences it",
              not fires(d, boldness="bold", breakout=True))

        # sound restraint is never nudged — scoped to a bold declaration
        d = os.path.join(td, "c"); os.makedirs(d)
        check("a conservative-declared deck is never nudged (restraint is legitimate)",
              not fires(d, boldness="conservative"))

        # experimental counts as daring too
        d = os.path.join(td, "e"); os.makedirs(d)
        check("boldness=experimental is in scope",
              fires(d, boldness="experimental"))

        # needs enough interior pages to be a pattern
        d = os.path.join(td, "s"); os.makedirs(d)
        check("a short bold deck (<8 interior pages) is not nudged",
              not fires(d, boldness="bold", n=7))

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
