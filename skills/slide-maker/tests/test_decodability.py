#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A viewer must be able to DECODE what is on the page — and that must be measured, not claimed.

WHY. Three pieces of feedback from the first human reader of a deck this repo built, all of which
every automated gate had passed:

  「icon 应该是一个必须包含的东西但是这个却没有」   the icon gate was cleared by a prose waiver
  「1/5/10/12 的设计我没有看懂」                    the signature move's stranger test was asserted
  「第一页的那些横线是什么意思」                     nine repeated marks nobody had named

One root cause under all three: **the skill could SAY a visual element was readable, and nothing
checked whether the sentence was true.** Each fix below turns a rule the skill had already written
in prose into a measurement over the built file.

  MOTIF_UNEXPLAINED_AT_FIRST_USE  SKILL.md says, in as many words, that "a reading that defers to
                                  a later slide is a FAILED test written as a passing sentence" —
                                  and the check tested the opposite, clearing on a legend ANYWHERE.
                                  Measured: a loud motif debuted on the cover with nothing to read
                                  it by, the legend arrived later, the deck passed, and the first
                                  reader asked what it meant.
  UNNAMED_REPEATED_MARK           a set of identical marks with no text near it was invisible to
                                  every check: not text, not tagged as a motif, and trivially
                                  clearing contrast and overlap. Nine unlabelled rules on a cover
                                  shipped, and the reader's question was "什么意思".
  icon waiver categories          `motif-dominant` / `tiny-deck` / `template-locked` were compared
                                  against a list of strings. Any of the four words cleared the
                                  gate, so the WORD did the work and not the fact.

Run: python3 tests/test_decodability.py
"""
from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk            # noqa: E402
import render_deck as rd        # noqa: E402

OKS: list[str] = []
FAILS: list[str] = []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="decodability-"))


def check(cond, msg, detail=""):
    (OKS if cond else FAILS).append(msg if cond else "{} — {}".format(msg, detail))


def codes(prs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        dk.lint_layout(prs)
    out = buf.getvalue()
    return {w for w in ("MOTIF_UNEXPLAINED_AT_FIRST_USE", "MOTIF_UNEXPLAINED",
                        "UNNAMED_REPEATED_MARK", "MOTIF_BUDGET") if w in out}


# ── 1. the stranger test is about FIRST appearance ───────────────────────────────────────────
prs = dk.blank_deck()
s1 = dk.add_slide(prs)
dk.tag_motif(dk.box(s1, 0.7, 2.0, 8.6, 0.02, fill=dk.MAGENTA), loud=True)
dk.text(s1, 0.7, 2.6, 8.6, 0.6, [[("A cover", 28, dk.DEEP, True, False)]])
s2 = dk.add_slide(prs)
dk.tag_motif(dk.box(s2, 0.7, 2.0, 8.6, 0.02, fill=dk.MAGENTA), loud=True)
dk.motif_legend(s2, "the rule marks a boundary", x=0.7, y=2.3)
check("MOTIF_UNEXPLAINED_AT_FIRST_USE" in codes(prs),
      "a loud motif that debuts unexplained and is keyed LATER is caught — deferring the reading "
      "to a later slide is the exact failure SKILL.md names, and the old check cleared it",
      str(codes(prs)))

prs = dk.blank_deck()
s1 = dk.add_slide(prs)
dk.tag_motif(dk.box(s1, 0.7, 2.0, 8.6, 0.02, fill=dk.MAGENTA), loud=True)
dk.motif_legend(s1, "the rule marks a boundary", x=0.7, y=2.3)
s2 = dk.add_slide(prs)
dk.tag_motif(dk.box(s2, 0.7, 2.0, 8.6, 0.02, fill=dk.MAGENTA), loud=True)
check("MOTIF_UNEXPLAINED_AT_FIRST_USE" not in codes(prs),
      "...and keying it AT its debut passes — the rule is about where the reader meets the device",
      str(codes(prs)))

prs = dk.blank_deck()
for _ in range(2):
    s = dk.add_slide(prs)
    dk.tag_motif(dk.box(s, 0.7, 2.0, 8.6, 0.02, fill=dk.MAGENTA), loud=True)
check("MOTIF_UNEXPLAINED" in codes(prs),
      "a loud motif with NO legend anywhere is still caught (the pre-existing check is intact)")

# ── 2. repetition nobody named ───────────────────────────────────────────────────────────────
def _marks(named):
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    for i in range(9):
        dk.box(s, 3.0, 1.5 + i * 0.13, 6.0, 0.01, fill=dk.DEEP)
    if named:
        dk.text(s, 1.2, 2.0, 1.5, 0.4, [[("TWELVE FLOORS", 11, dk.DEEP, True, False)]])
    dk.text(s, 0.7, 4.6, 8.6, 0.6, [[("A cover", 28, dk.DEEP, True, False)]])
    return prs


check("UNNAMED_REPEATED_MARK" in codes(_marks(False)),
      "nine identical rules with no text near them are caught — not text, not tagged, and they "
      "clear contrast and overlap trivially, so every other check was blind to them",
      str(codes(_marks(False))))
check("UNNAMED_REPEATED_MARK" not in codes(_marks(True)),
      "...and the SAME nine rules pass once a word sits beside them. The fix a reader needs is a "
      "label, and that is exactly what clears it",
      str(codes(_marks(True))))

# A LABEL, not merely text that happens to be nearby. The first version asked "is there text
# within reach", and on the real cover this check was written for, a 28pt HEADLINE sat 0.22in below
# the nine rules and cleared them — a page title does not name your diagram. A label is small and
# close; a headline is large and is titling the page.
def _cover(named):
    prs = dk.blank_deck()
    sl = dk.add_slide(prs)
    for i in range(9):
        dk.box(sl, 2.55 if named else 0.72, 3.30 + i * 0.132,
               6.73 if named else 8.56, 0.010, fill=dk.DEEP)
    if named:
        dk.text(sl, 0.72, 3.30 + 4 * 0.132 - 0.30, 1.40, 0.30,
                [[("TWELVE", 11, dk.DEEP, True, False)]])
        dk.text(sl, 0.72, 3.30 + 4 * 0.132 - 0.04, 1.40, 0.30,
                [[("FLOORS", 11, dk.DEEP, True, False)]])
    dk.text(sl, 0.72, 4.58, 8.0, 0.46, [[("Every check was green.", 28, dk.DEEP, True, False)]])
    return prs


check("UNNAMED_REPEATED_MARK" in codes(_cover(False)),
      "a 28pt HEADLINE 0.22in below the marks does not count as naming them — this is the real "
      "cover the check was written for, and 'text is nearby' cleared it",
      str(codes(_cover(False))))
check("UNNAMED_REPEATED_MARK" not in codes(_cover(True)),
      "...and an 11pt label beside the group does count. Small and close is a label; large is a "
      "page title", str(codes(_cover(True))))

prs = dk.blank_deck()
s = dk.add_slide(prs)
for i in range(3):
    dk.box(s, 1.0 + i * 3.0, 2.0, 2.4, 1.2, fill=dk.TINT)
check("UNNAMED_REPEATED_MARK" not in codes(prs),
      "three cards are not reported — the floor is 4, so an ordinary card row is untouched")

# ── 3. the icon waiver's category must be TRUE of the built file ─────────────────────────────
def _deck(n_slides, loud=False):
    prs = dk.blank_deck()
    for _ in range(n_slides):
        s = dk.add_slide(prs)
        if loud:
            dk.tag_motif(dk.box(s, 0.7, 2.0, 8.6, 0.02, fill=dk.MAGENTA), loud=True)
    p = TMP / ("d%d%s.pptx" % (n_slides, "m" if loud else ""))
    prs.save(str(p))
    return p


ok, why = rd._icon_none_category_holds("motif-dominant", _deck(12), [2, 3])
check(not ok and "loud motif" in why,
      "`motif-dominant` on a deck with NO loud motif is rejected — the strongest word on the list "
      "was clearing the gate on decks that had no motif to dilute", why[:90])
ok, _ = rd._icon_none_category_holds("motif-dominant", _deck(4, loud=True), [2])
check(ok, "...and it holds on a deck that really carries one")
ok, why = rd._icon_none_category_holds("tiny-deck", _deck(12), [2])
check(not ok and "tiny-deck" in why, "`tiny-deck` on twelve slides is rejected", why[:80])
ok, _ = rd._icon_none_category_holds("tiny-deck", _deck(2), [2])
check(ok, "...and holds on a 2-slide ask")
ok, why = rd._icon_none_category_holds("template-locked", _deck(6), [2])
check(not ok and "stock layouts" in why,
      "`template-locked` on a blank deck is rejected — python-pptx ships eleven named layouts, so "
      "'has layout names' proved nothing and this cleared on the first try", why[:90])
ok, _ = rd._icon_none_category_holds("editorial-register", _deck(12), [2])
check(ok, "`editorial-register` is left as declared — it is a taste claim about a look, and "
          "inventing a measurement for it would be worse than admitting there is none")

# ── 4. the waiver must name EVERY flagged slide ──────────────────────────────────────────────
src = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
check("_icon_none_category_holds" in src and "icon waiver REJECTED" in src,
      "the gate calls the category check and says REJECTED out loud when it fails")
check("not re-decided" in src,
      "...and REPORTS the flagged slides a waiver did not name. Deliberately a report and not a "
      "hold: as a hold it rejected a lawful `editorial-register` waiver that had named two of a "
      "dozen pages, and the defect this batch actually had — a category FALSE of the built file — "
      "is caught precisely by the check above. A blunt second rule that fires on lawful use is how "
      "a gate earns the reflex to waive it.")

print("\n".join("  ok   " + m for m in OKS))
if FAILS:
    print("\n".join("  FAIL " + m for m in FAILS))
print("\n{} passed, {} failed".format(len(OKS), len(FAILS)))
raise SystemExit(1 if FAILS else 0)
