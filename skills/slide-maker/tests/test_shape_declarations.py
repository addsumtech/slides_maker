#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three declarations share one field, and none of them may erase the others.

`tag_motif`, `bleed_intent` and `overlap_intent` all record a decision in `shape.name`, because a
name survives `prs.save()` where a side table keyed on object identity does not. Each of them used
to ASSIGN it outright, so whichever ran last won.

🔴 MEASURED. A delivered deck whose entire design is a hand-drawn motif had a surface kit that
called `tag_motif(sh, loud=False)` and then `overlap_intent(sh, …)` on every piece of furniture —
the grid, the little-street rules, the slot. The saved file contained ZERO tagged motif shapes.
Consequences, none of which reported themselves:

  · MOTIF_BUDGET counted no appearances, so the <=3 loud budget was unenforceable
  · TEXT_OVER_MOTIF and MOTIF_UNEXPLAINED could not see the device at all
  · `icon_family: "none"` with category `motif-dominant` claims icons would dilute a strong motif —
    and the gate that verifies that category against the built file found no motif to verify it
    against, on a deck that is nothing but motif

An erased declaration reads exactly like one that was never made. That is why this class of bug is
silent, and why the fix is a shared composer rather than three careful call sites: the next
declaration someone adds to this field would have re-introduced it.

🔴 CALL ORDER MUST NOT MATTER. Nothing in any signature hints that it would, so a rule that only
holds for one order is a trap rather than a contract.

Run:  python3 tests/test_shape_declarations.py
"""
import itertools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deckkit as dk                                                  # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


prs = dk.blank_deck()
slide = dk.add_slide(prs)
BLEED_WHY = "the ray fan's origin sits off the page on purpose"
OVER_WHY = "the display word is the ground the caption rides"


def fresh():
    return dk.box(slide, 1, 1, 1, 1, fill="888888")


OPS = {"motif": lambda sh: dk.tag_motif(sh, loud=True),
       "bleed": lambda sh: dk.bleed_intent(sh, BLEED_WHY),
       "overlap": lambda sh: dk.overlap_intent(sh, OVER_WHY),
       # 🔴 the FOURTH member, found by asking whether the other tag families collide too:
       # `mark_datum` and `tag_motif` erased each other in BOTH directions, and the datum-first
       # order produced `deckkit-motif-loud:bars:12.0` — a name that parses as a motif whose
       # "reason" is the lost datum record. A motif page drawn AS bars uses both.
       "datum": lambda sh: dk.mark_datum(sh, 12.0, group="bars"),
       # the FIFTH (2026-10-03): `decorative` — pure ornament, exempt from NON-TEXT CONTRAST. A
       # washi tape is a motif that holds its print (overlap) and is decoration, all at once.
       "decor": lambda sh: dk.decorative(sh, "washi tape is ornament; no meaning rides on it")}

lost = []
for order in itertools.permutations(OPS):
    sh = fresh()
    for k in order:
        OPS[k](sh)
    if not (dk._is_motif(sh) and dk._is_motif(sh, loud=True)
            and dk._declared_overlap(sh) and "+bleed" in sh.name and "+datum" in sh.name
            and "+decor" in sh.name):
        lost.append("->".join(order) + " => " + sh.name)
check(not lost,
      "🔴 all 120 orders of tag_motif / bleed_intent / overlap_intent / mark_datum / decorative keep every "
      "declaration — "
      "the composer parses the name back to a SET and re-renders it, so order cannot matter "
      "(lost: %s)" % (lost or "none"))

# the SIXTH: a generated picture's provenance (image_series.slot_picture) — a flag in the name HEAD, so it
# never takes the one reason slot the others share. Composes with motif / bleed / overlap / decor.
GEN_OPS = {k: v for k, v in OPS.items() if k != "datum"}          # a generated picture is never a datum bar
GEN_OPS["gen"] = lambda sh: dk._compose_tag(sh, gen="s03-kettle")
lost_g = []
for order in itertools.permutations(GEN_OPS):
    sh = fresh()
    for k in order:
        GEN_OPS[k](sh)
    if not (dk.generated_slot(sh) == "s03-kettle" and dk._is_motif(sh) and dk._declared_overlap(sh)
            and "+bleed" in sh.name and "+decor" in sh.name):
        lost_g.append("->".join(order) + " => " + sh.name)
check(not lost_g, "all 120 orders keep the generated-slot tag beside the other four (lost: %s)" % (lost_g or "none"))
sh = fresh()
dk._compose_tag(sh, gen="hero")
check(sh.name == "deckkit-gen.hero" and dk.generated_slot(sh) == "hero", "gen alone: " + sh.name)
check(dk.generated_slot(fresh()) is None, "an untagged shape has no generated slot")

VL_OPS = dict(GEN_OPS)
VL_OPS["vl"] = lambda sh: dk._compose_tag(sh, vl="collage")
lost_v = []
for order in itertools.permutations(["motif", "overlap", "gen", "vl", "decor"]):
    sh = fresh()
    for k in order:
        VL_OPS[k](sh)
    if not (dk.vl_name(sh) == "collage" and dk.generated_slot(sh) == "s03-kettle" and dk._is_motif(sh)
            and dk._declared_overlap(sh) and "+decor" in sh.name):
        lost_v.append("->".join(order) + " => " + sh.name)
check(not lost_v, "all orders keep the visual-language tag beside the others (lost: %s)" % (lost_v or "none"))
sh = fresh()
dk._compose_tag(sh, vl="editorial")
check(sh.name == "deckkit-vl.editorial" and dk.vl_name(sh) == "editorial", "vl alone: " + sh.name)
check(dk.vl_name(fresh()) is None, "an untagged shape has no language")

# The single-declaration paths are the common case and must stay exactly as they were.
for label, fn, want in (
        ("bleed alone", lambda sh: dk.bleed_intent(sh, BLEED_WHY), "deckkit-bleed:"),
        ("overlap alone", lambda sh: dk.overlap_intent(sh, OVER_WHY), "deckkit-overlap:"),
        ("quiet motif alone", lambda sh: dk.tag_motif(sh, loud=False), "deckkit-motif-quiet"),
        ("loud motif alone", lambda sh: dk.tag_motif(sh, loud=True), "deckkit-motif-loud"),
        ("datum alone", lambda sh: dk.mark_datum(sh, 12.0, group="bars"), "deckkit-datum:"),
        ("decorative alone", lambda sh: dk.decorative(sh, "washi tape is ornament; no meaning rides on it"),
         "deckkit-decor:")):
    sh = fresh()
    fn(sh)
    check(sh.name.startswith(want) and "+bleed+bleed" not in sh.name
          and "+overlap+overlap" not in sh.name,
          "%s is unchanged and un-duplicated (%s)" % (label, sh.name[:44]))

sh = fresh()
dk.bleed_intent(sh, BLEED_WHY)
dk.overlap_intent(sh, OVER_WHY)
check(("+bleed" in sh.name or sh.name.startswith("deckkit-bleed")) and dk._declared_overlap(sh)
      and not dk._is_motif(sh),
      "two declarations WITHOUT a motif compose into `deckkit-bleed+overlap:` and do not "
      "accidentally become a motif")

sh = fresh()
dk.tag_motif(sh, loud=True)
dk.tag_motif(sh, loud=False)
check(dk._is_motif(sh, loud=False) and not dk._is_motif(sh, loud=True),
      "re-tagging changes the TIER rather than appending one — the tier is authoritative, so a "
      "quiet echo of a loud mark is expressible")

sh = fresh()
dk.tag_motif(sh, loud=True)
dk.overlap_intent(sh, OVER_WHY)
check(OVER_WHY.split()[0] in sh.name,
      "🔴 the REASON survives the compose — an overlap declaration whose why-clause was dropped "
      "would satisfy the check while losing the sentence the check exists to demand")

# The reason floor is a real gate and composing must not open a way around it.
try:
    dk.overlap_intent(fresh(), "too short")
    _floor = False
except ValueError:
    _floor = True
check(_floor,
      "...and the >=16-character reason floor still raises — the composer is not a way in "
      "without one")

src = (ROOT / "scripts" / "deckkit.py").read_text(encoding="utf-8")
_family = ("def tag_motif", "def bleed_intent", "def overlap_intent", "def mark_datum",
           "def decorative")
_bare = []
for _d in _family:
    _i = src.index(_d)
    _body = src[_i:src.index("\ndef ", _i + 10)]
    if "shape.name = " in _body and "_compose_tag" not in _body:
        _bare.append(_d.split()[1])
check(not _bare,
      "🔴 every member of this tag family writes the name through ONE composer — the fix has to "
      "be the shared function, because four careful call sites is exactly what was there when it "
      "broke, and the next declaration someone adds would re-introduce it (%s still assigns "
      "directly)" % (_bare or "none"))

sh = fresh()
dk.mark_datum(sh, 12.0, group="bars")
dk.tag_motif(sh, loud=True)
check(dk._is_motif(sh, loud=True) and sh.name.endswith("bars:12.0"),
      "🔴 datum-then-motif keeps BOTH — this order used to produce `deckkit-motif-loud:bars:12.0`, "
      "which parses as a motif whose reason is the datum record it destroyed")

# 🔴 MEASURED 2026-10-04: a visual-language kit stamps `+vl.<name>` on every shape it draws, so an
# overlap declaration on a collage print is saved as `deckkit-overlap+vl.collage:<why>` — a THIRD
# spelling. The reader knew only `deckkit-overlap:` and `+overlap`, so the render-time lint refused
# twelve declared overlaps on a three-print collage cover that the build-time gate had passed.
for extra in ({"vl": "collage"}, {"gen": "s01-cover"}, {"vl": "collage", "gen": "s01-cover"}):
    sh = fresh()
    dk.overlap_intent(sh, OVER_WHY)
    dk._compose_tag(sh, **extra)
    check(dk._declared_overlap(sh),
          "overlap declaration survives a later %s tag (name %r)" % ("+".join(extra), sh.name))

# 🔴 The same composed spelling reaches EVERY reader of a `<base>:` tag, not just the render-time
# overlap one fixed above — found by listing all of them (2026-10-05). Two more were blind to it:
#   · build-time TEXT_OVERLAP read `deckkit-overlap:` only, so a kit-stamped text box carrying a
#     declared overlap was refused as a collision — the declaration the render gate now honours;
#   · DATUM SCALE read `deckkit-datum:` only, so a bar declared decorative or stamped by a kit
#     (`deckkit-datum+decor:g:2.0`) dropped out of the truth check while its group still printed.
def _lint_codes(p):
    with __import__("contextlib").redirect_stdout(__import__("io").StringIO()):
        return {(n, code) for n, _sev, code, *_ in dk.lint_layout(p, verbose=False)}


for extra in ({}, {"vl": "collage"}, {"gen": "s01-cover", "vl": "collage"}):
    p2 = dk.blank_deck()
    s2 = dk.add_slide(p2)
    big = dk.text(s2, 0.5, 1.0, 6.0, 1.4, [[("GIANT", 80, dk.DEEP, True, False)]])
    dk.overlap_intent(big, OVER_WHY)
    if extra:
        dk._compose_tag(big, **extra)
    dk.text(s2, 1.0, 1.4, 4.0, 0.5, [[("a caption riding it", 14, dk.DEEP, False, False)]])
    check((1, "TEXT_OVERLAP") not in _lint_codes(p2),
          "build-time TEXT_OVERLAP honours a declaration with {} composed onto it (name {!r})"
          .format("+".join(extra) or "nothing", big.name))
p3 = dk.blank_deck()
s3 = dk.add_slide(p3)
dk.text(s3, 0.5, 1.0, 6.0, 1.4, [[("GIANT", 80, dk.DEEP, True, False)]])
dk.text(s3, 1.0, 1.4, 4.0, 0.5, [[("a caption riding it", 14, dk.DEEP, False, False)]])
check((1, "TEXT_OVERLAP") in _lint_codes(p3), "control: an UNDECLARED text collision is still TEXT_OVERLAP")

for extra in ({}, {"flag": "+decor", "reason": None}, {"vl": "collage"}):
    p4 = dk.blank_deck()
    s4 = dk.add_slide(p4)
    # values 1 and 2 drawn 2.0in and 3.0in long: the lengths say 1 : 1.5, the data says 1 : 2
    for i, (v, ln) in enumerate(((1.0, 2.0), (2.0, 3.0))):
        bar = dk.box(s4, 1.0, 1.0 + i * 0.6, ln, 0.3, fill="2F5BEA")
        dk.mark_datum(bar, v, group="probe")
        if extra:
            kw = dict(extra)
            if kw.get("reason", 1) is None:
                kw.pop("reason")
            dk._compose_tag(bar, **kw)
    names = [sh.name for sh in s4.shapes]
    check(any(code == "DATUM SCALE" for _n, _sev, code, *_ in dk._datum_faults(p4)),
          "DATUM SCALE still reads a datum with {} composed onto it ({})"
          .format("+".join(k.strip("+") for k in extra) or "nothing", names[0]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
