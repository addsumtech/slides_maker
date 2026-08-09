#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The one defect class where the file does not open at all, and nothing here could see it.

Every other check in this toolkit is geometric, pixel-based or semantic. None of them asks
whether the produced part is well-formed against ECMA-376 — and this library writes OOXML by
hand (`parse_xml` in ~11 places in deckkit, plus `anim.py` composing `<p:timing>` as a string).

Measured: two `Build(s)` on ONE slide, each calling `apply()`, produced

    ['cSld', 'clrMapOvr', 'timing', 'timing']

CT_Slide allows exactly one `<p:timing>`. `prs.save()` raised nothing. LibreOffice rendered it.
`lint_layout` reported clean. `preflight_check.py` — which asks only whether the string
`p:timing` occurs — read the DUPLICATE as *more* compliant, so the deck got a tick for the very
thing that broke it. The first human signal would have been PowerPoint offering to repair the
file, i.e. the user.

Two layers, and the split is the point:
  · `anim.apply()` now REFUSES a second call on one slide. A second Build's steps were never in
    the first's sequence, so silently keeping either tree ships a click order the author never
    wrote — that is a build error, not something to merge.
  · `OOXML_SHAPE` is the net under it, because the next hand-written element will not have its
    own guard.

🔴 It is deliberately NOT a schema validator. Shipping ECMA-376's XSD set means carrying the
schemas, filtering the noise a real template already contains, and maintaining an auto-repair
path — cost out of proportion to what it catches here. It asserts the cardinality and order of
the elements THIS toolkit writes, which is exactly where its own bugs land. The day it starts
missing something it does not model is the day to reconsider the full validator, not before.

Run:  python3 tests/test_ooxml_shape.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import deckkit as dk                                                  # noqa: E402
from anim import Build, slide_transition                              # noqa: E402
from pptx.oxml import parse_xml                                       # noqa: E402
from pptx.oxml.ns import nsdecls                                      # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def codes(prs):
    return [f[2] for f in dk.lint_layout(prs, verbose=False)]


def kids(slide):
    return [e.tag.split("}")[-1] for e in slide._element]


def one(**kw):
    prs = dk.blank_deck()
    return prs, dk.add_slide(prs)


def main():
    print("ooxml shape")
    dk.FONT, dk.EAFONT = "Helvetica Neue", "Hiragino Sans GB"

    # ---- the measured defect: a second Build.apply() on one slide ---------------------
    prs, s = one()
    b1 = Build(s)
    with b1.step():
        dk.box(s, 1, 1, 2, 1, fill=dk.DEEP)
    b1.apply(effect="appear")
    check("one Build produces exactly one <p:timing>", kids(s).count("timing") == 1, kids(s))

    b2 = Build(s)
    with b2.step():
        dk.box(s, 1, 2.4, 2, 1, fill=dk.DEEP)
    try:
        b2.apply(effect="appear")
        check("a SECOND apply() on the same slide is refused", False, kids(s))
    except ValueError as exc:
        check("a SECOND apply() on the same slide is refused", True)
        check("...and the message says why silence was the danger",
              "schema-invalid" in str(exc) and "PowerPoint" in str(exc), str(exc)[:80])

    # ---- the net under it: the same corruption reached any other way ------------------
    prs, s = one()
    for _ in range(2):
        s._element.append(parse_xml("<p:timing %s/>" % nsdecls("p")))
    check("a duplicate <p:timing> built by any other route is CRITICAL",
          "OOXML_SHAPE" in codes(prs), codes(prs))
    sev = [f[1] for f in dk.lint_layout(prs, verbose=False) if f[2] == "OOXML_SHAPE"]
    check("...at CRITICAL, because the file will not open at all", sev == ["CRITICAL"], sev)
    try:
        dk.lint_layout(prs, verbose=False, strict=True)
        check("...and strict=True refuses to save it", False)
    except RuntimeError:
        check("...and strict=True refuses to save it", True)

    # ---- order, not just count -------------------------------------------------------
    prs, s = one()
    s._element.append(parse_xml("<p:extLst %s/>" % nsdecls("p")))
    s._element.append(parse_xml("<p:timing %s/>" % nsdecls("p")))
    check("timing appended AFTER extLst is reported (order, not just cardinality)",
          "OOXML_SHAPE" in codes(prs), kids(s))

    # ...and apply() places it correctly when an extLst is already there
    prs, s = one()
    s._element.append(parse_xml("<p:extLst %s/>" % nsdecls("p")))
    b = Build(s)
    with b.step():
        dk.box(s, 1, 1, 2, 1, fill=dk.DEEP)
    b.apply(effect="appear")
    check("apply() inserts timing BEFORE an existing extLst",
          kids(s) == ["cSld", "clrMapOvr", "timing", "extLst"], kids(s))
    check("...so the deck it just built is clean", "OOXML_SHAPE" not in codes(prs))

    # ---- the silent half: every ordinary deck shape must pass -------------------------
    prs, s = one()
    dk.box(s, 0, 0, 10, 5.625, fill=dk.RGBColor(0xF5, 0xF1, 0xE6))
    dk.title_bar(s, "An ordinary page", kicker="test")
    dk.footer(s, "tag", page=1)
    check("a plain slide is silent", "OOXML_SHAPE" not in codes(prs), kids(s))

    prs, s = one()
    slide_transition(s, "fade")
    check("a slide with a transition is silent",
          "OOXML_SHAPE" not in codes(prs), kids(s))

    prs, s = one()
    slide_transition(s, "fade")
    b = Build(s)
    with b.step():
        dk.box(s, 1, 1, 2, 1, fill=dk.DEEP)
    b.apply(effect="appear")
    check("transition + build together keep schema order",
          kids(s) == ["cSld", "clrMapOvr", "transition", "timing"], kids(s))
    check("...and are silent", "OOXML_SHAPE" not in codes(prs))

    prs = dk.blank_deck()
    for i in range(4):
        sl = dk.add_slide(prs)
        dk.box(sl, 0, 0, 10, 5.625, fill=dk.RGBColor(0xF5, 0xF1, 0xE6))
        bb = Build(sl)
        with bb.step():
            dk.box(sl, 1, 1, 2, 1, fill=dk.DEEP)
        bb.apply(effect="appear")
    check("one Build per slide across a multi-slide deck is silent",
          "OOXML_SHAPE" not in codes(prs))

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
