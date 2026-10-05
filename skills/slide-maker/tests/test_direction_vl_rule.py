#!/usr/bin/env python3
"""A deck that HAS pictures — the user's photos or illustrations — offers at least one visual language among its
directions (the user's rule, 2026-10-04). The docs said a visual language MAY be a direction and nothing ever asked
for one, so the four image-led looks rarely reached the person they were built for. The direction-gate record now
states `images: photos | illustrations | none`; one checker (directions_diversity.images_fault) holds the rule on
both runtimes, and the gate's named `waived` remains the escape."""
from __future__ import annotations
import contextlib, io, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import directions_diversity as dd
import render_deck as rd
import codex_delivery_gate as cdg
import visual_languages as vl

td = Path(tempfile.mkdtemp())
plain = [{"name": n, "bg": bg, "ink": ink, "accent": ac, "font_display": fd, "font_body": "Arial",
          "cover": cv, "skeleton": sk}
         for n, bg, ink, ac, fd, cv, sk in (("A", "#FFFFFF", "#111111", "#0055AA", "Georgia", "centred", "statement"),
                                            ("B", "#101820", "#F2F2F2", "#E8A33D", "Arial Black", "low-left", "split"),
                                            ("C", "#F4EFE6", "#2A2A2A", "#B23A2B", "Didot", "split-vertical", "island"),
                                            ("D", "#E9F1EC", "#1D2B22", "#2E8B57", "Trebuchet MS", "full-bleed-type", "band"))]
with_vl = plain[:3] + [vl.direction("soft")]
with_story = plain[:3] + [vl.direction("storybook")]

# 1. the rule, in the one shared checker
check(dd.images_fault("photos", plain) and "visual language" in dd.images_fault("photos", plain),
      "photos + no visual language among the directions is a fault: {!r}".format(dd.images_fault("photos", plain)))
check(dd.images_fault("photos", with_vl) is None, "photos + a visual language passes")
check(dd.images_fault("none", plain) is None, "a deck with no pictures needs no visual language")
f_ = dd.images_fault(None, plain)
check(f_ and "photos" in f_ and "illustrations" in f_ and "none" in f_, "a missing `images` names its values: {!r}".format(f_))
check(dd.images_fault("pictures", plain) and "photos" in dd.images_fault("pictures", plain), "an unknown value is refused")
check(dd.images_fault("illustrations", plain) and "storybook" in dd.images_fault("illustrations", plain),
      "illustrations without a visual language points at storybook: {!r}".format(dd.images_fault("illustrations", plain)))
check(dd.images_fault("illustrations", with_story) is None, "illustrations + storybook passes")


# 2. the Claude runtime (render_deck --gate-check's direction gate)
def rd_msg(dg):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(io.StringIO()):
            rd._direction_gate({"direction_gate": dg}, str(td))
        return ""
    except SystemExit:
        return buf.getvalue()


m = rd_msg({"candidates": plain, "picked": "A", "images": "photos"})
check("visual language" in m, "render_deck holds a photo deck whose directions offer no visual language: {}".format(m[-300:]))
m = rd_msg({"candidates": with_vl, "picked": "A", "images": "photos"})
check("visual language" not in m, "render_deck: a visual language among them clears the rule: {}".format(m[-300:]))
m = rd_msg({"candidates": plain, "picked": "A"})
check("images" in m and "photos | illustrations | none" in m, "render_deck asks for `images` when it is missing: {}".format(m[-300:]))
m = rd_msg({"candidates": plain, "picked": "A", "images": "photos", "waived": "the client's brand book forbids photo-led layouts"})
check(m == "" or "visual language" not in m, "the named waiver still clears it: {}".format(m[-300:]))
check(rd_msg("n/a - user supplied the look") == "", "the n/a carve is untouched")


# 3. the Codex runtime
def cdg_errs(dg):
    errs: list[str] = []
    try:
        cdg.check_design({"design": {"direction_gate": dg}}, td, {1}, "0" * 64, errs)
    except Exception as e:
        errs.append("raised " + repr(e))
    return [e for e in errs if e.startswith("design.direction_gate") or e.startswith("raised")]


e = cdg_errs({"candidates": plain, "picked": "A", "images": "photos"})
check(any("visual language" in x for x in e), "codex gate holds the same deck: {}".format(e))
e = cdg_errs({"candidates": with_vl, "picked": "A", "images": "photos"})
check(not any("visual language" in x for x in e), "codex gate: a visual language clears it: {}".format(e))
e = cdg_errs({"candidates": plain, "picked": "A"})
check(any("images" in x for x in e), "codex gate asks for `images` when it is missing: {}".format(e))

# 4. pictures you GENERATE or FETCH count too (the user's rule, 2026-10-05). An end-to-end run had no material, a
#    paid image tool, and a ten-picture generated series — and the record could only say `none` (no rule) or
#    `photos` (as if the user had sent them). The deck's own image records are checked against the gate's `images`.
GEN = ["slide 3 | gadgets on a table | generated — openai gpt-image-2"]
FETCHED = ["slide 6 | Dartmouth hall | sourced — Wikimedia Commons (CC BY-SA 4.0)"]
FALLBACK = ["slide 9 | 1890 factory | searched (Commons, Openverse), none found → generated, flagged illustrative"]
PROVIDED = ["slide 4 | Fig 3 of the paper | provided — user (own material)"]
f_ = dd.images_fault("none", plain, image_sources=GEN)
check(f_ and "generated" in f_ and "visual language" in f_,
      "images: none while the plan GENERATES pictures is a fault: {!r}".format(f_))
f_ = dd.images_fault("none", plain, image_sources=FETCHED)
check(f_ and "fetched" in f_, "images: none while the plan FETCHES pictures is a fault: {!r}".format(f_))
check(dd.images_fault("none", plain, image_sources=FALLBACK),
      "a search that fell back to a generated picture counts as generated")
check(dd.images_fault("none", plain, imagery="series"),
      "images: none on a deck built on a generated image SERIES is a fault")
check(dd.images_fault("none", plain, image_sources=PROVIDED) is None,
      "the user's own figures do not force a visual language (a paper's plots are not a photo deck)")
check(dd.images_fault("none", plain, image_sources="n/a — a text-only briefing") is None,
      "an n/a image record forces nothing")
check(dd.images_fault("photos", with_vl, image_sources=GEN, imagery="series") is None,
      "generated photos + a visual language offered passes")
m = rd_msg_dp = None
buf = io.StringIO()
try:
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(io.StringIO()):
        rd._direction_gate({"direction_gate": {"candidates": plain, "picked": "A", "images": "none"},
                            "image_sources": GEN}, str(td))
    m = ""
except SystemExit:
    m = buf.getvalue()
check("generated" in m and "visual language" in m,
      "render_deck reads the deck's image records against `images: none`: {}".format(m[-300:]))
errs: list[str] = []
cdg.check_design({"design": {"direction_gate": {"candidates": plain, "picked": "A", "images": "none"},
                             "imagery": "series"}}, td, {1}, "0" * 64, errs)
check(any(x.startswith("design.direction_gate") and "generated" in x for x in errs),
      "codex gate reads the same records: {}".format([x for x in errs if x.startswith("design.direction_gate")]))

# 5. a deck with NO pictures offers a native language — the one that fits the topic, with the reason recorded
ink_dir = vl.direction("ink")
check(tuple(dd.NATIVE_LANGS) == tuple(vl.NATIVE), "directions_diversity knows the same native languages")
f_ = dd.native_fault("none", plain)
check(f_ and "native" in f_ and "drafting" in f_, "no pictures + no native language among the directions is a fault: {!r}".format(f_))
f_ = dd.native_fault("none", plain[:3] + [ink_dir])
check(f_ and "native_fit" in f_, "a native language offered without its reason asks for native_fit: {!r}".format(f_))
check(dd.native_fault("none", plain[:3] + [ink_dir], {"language": "ink", "why": "a talk on tea and craft"}) is None,
      "a native language with its reason passes")
check(dd.native_fault("none", plain[:3] + [ink_dir], {"language": "poster", "why": "a manifesto"}) is not None,
      "native_fit must name a language that was offered")
check(dd.native_fault("photos", plain) is None, "with pictures the native rule does not apply")
m = rd_msg({"candidates": plain, "picked": "A", "images": "none"})
check("native" in m, "render_deck holds a picture-less deck with no native language: {}".format(m[-300:]))
m = rd_msg({"candidates": plain[:3] + [ink_dir], "picked": "A", "images": "none",
            "native_fit": {"language": "ink", "why": "a talk on tea and craft"}})
check("native" not in m, "render_deck: a native language with its reason clears it: {}".format(m[-300:]))
e = cdg_errs({"candidates": plain, "picked": "A", "images": "none"})
check(any("native" in x for x in e), "codex gate holds the same deck: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_direction_vl_rule] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
