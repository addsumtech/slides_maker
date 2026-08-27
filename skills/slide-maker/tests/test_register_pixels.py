#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A declared register must reach the RENDERED PIXELS, and must not be the last deck's.

WHY. SKILL.md names two rules that "survive no matter what" — *never ship deckkit's default blue,
and never reuse the last deck's scheme* — and both were prose with nothing scoring them. The
nearest gate, `check_style_applied.py`, checks the SOURCE: that `presets.apply("brutalist")`
appears in the build script. Two real cases walk straight past it:

  * a build that calls `presets.apply()` and then hand-sets the tokens back to stock, and
  * a **bespoke** register — the kind this skill actively encourages — which has no preset call to
    grep for and is skipped by definition. Measured on the deck built in this repo's own session:
    its entire terminal register was set by hand, and nothing verified any of it landed.

`tests/test_register_expression.py` (the sibling of this file) closes the GEOMETRY half at the
OOXML level — rule widths, radii, backgrounds. This file closes the COLOUR half at the level the
geometry one cannot reach: the raster, where a register either arrived or did not.

Two of these cases are regressions against measurements taken on real renders, and they pull in
opposite directions — which is why both are here:

  * a register's accent usually lives in TYPE. On a real 15-page deck the signature green covered
    0.65% of its best page; ranking colours by area put it nowhere near the top and the first
    version of the checker declared the deck's own palette "absent".
  * two colours also meet by ACCIDENT. Where a white ground abuts a pale panel, antialiasing
    produces every blend between them, and a cream in neither one scored 0.093% of a page on a
    deck rendered entirely in deckkit's stock white-and-blue.

Run: python3 tests/test_register_pixels.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_register_pixels as crp        # noqa: E402

FAILS: list[str] = []
OKS: list[str] = []


def ok(msg):
    OKS.append(msg)


def bad(msg):
    FAILS.append(msg)


def check(cond, msg, detail=""):
    (ok if cond else bad)(msg if cond else "{} — {}".format(msg, detail))


def _deck(root, name, ground, marks, declared, history=None):
    """A deck directory with real PNGs. `marks` are (rgb, height_px) drawn as bands of ink."""
    from PIL import Image
    d = pathlib.Path(root) / name
    (d / "render").mkdir(parents=True, exist_ok=True)
    for i in range(3):
        im = Image.new("RGB", (960, 540), ground)
        px = im.load()
        y = 40
        for rgb, h in marks:
            for yy in range(y, y + h):
                for xx in range(40, 520):
                    px[xx, yy] = rgb
            y += h + 30
        im.save(d / "render" / ("slide%02d.png" % (i + 1)))
    (d / ".deck-gates.json").write_text(json.dumps(
        {"design_plan": {"palette": " ".join("#%02X%02X%02X" % c for c in declared)}}),
        encoding="utf-8")
    taste = None
    if history is not None:
        taste = d / "taste.md"
        rows = "\n".join(
            "| 2026-01-%02d | %s | look | %s | motif |" % (i + 1, nm, " ".join("#%02X%02X%02X" % c for c in cols))
            for i, (nm, cols) in enumerate(history))
        taste.write_text("## LOOK HISTORY\n| date | deck | look | canvas | motif |\n|---|---|---|---|---|\n"
                         + rows + "\n", encoding="utf-8")
    return d, (str(taste) if taste else None)


def codes(*a, **kw):
    return {c for c, _ in crp.check(*a, **kw)[0]}


# ── 1. the checker's own contract, on real rasters ───────────────────────────────────────────
tmp = tempfile.mkdtemp(prefix="regpix-test-")

# REGRESSION: an accent that exists only as TYPE. 3 bands x 12px over 960x540 is ~0.83% of a
# page — the order of magnitude a real deck's signature colour actually occupies. Ranking by
# AREA declares this absent; that was the first version's bug, caught on a real deck.
d, _ = _deck(tmp, "type-accent", (0x0A, 0x0F, 0x0A),
             [((0x33, 0xFF, 0x66), 12), ((0xC8, 0xF0, 0xC8), 12)],
             [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66), (0xC8, 0xF0, 0xC8)])
got = codes(d)
check("DECLARED PALETTE ABSENT" not in got,
      "an accent that lives only in TYPE counts as having reached the pixels",
      "flagged {}".format(got))

# REGRESSION: a near-white that is NOT in the deck must not count as present just because
# antialiasing between a white ground and a pale panel produces every blend between them.
d, _ = _deck(tmp, "blend", (0xFF, 0xFF, 0xFF),
             [((0xEA, 0xF3, 0xFA), 200), ((0x00, 0x7C, 0xC2), 60), ((0x00, 0x3C, 0x66), 60)],
             [(0xF2, 0xED, 0xE3), (0x11, 0x11, 0x11), (0xC8, 0x10, 0x2E)])
got = codes(d)
check("STOCK REGISTER SHIPPED" in got,
      "deckkit's stock identity under a plan declaring another register is caught",
      "got {}".format(got))

# The bespoke case check_style_applied.py is skipped on by definition.
d, _ = _deck(tmp, "bespoke-missing", (0x20, 0x20, 0x20), [((0x80, 0x80, 0x80), 40)],
             [(0xC4, 0x2E, 0x1C), (0x2F, 0x5D, 0x50), (0xF2, 0xED, 0xE3)])
check("DECLARED PALETTE ABSENT" in codes(d),
      "a bespoke register that never reached the build is caught — no preset call exists to grep",
      "got {}".format(codes(d)))

# Freshness, in the shape the REAL registry has: rows carrying only the canvas value.
d, tp = _deck(tmp, "ground-repeat", (0xF3, 0xF2, 0xED), [((0xC4, 0x2E, 0x1C), 40)],
              [(0xF3, 0xF2, 0xED), (0xC4, 0x2E, 0x1C)],
              history=[("previous-deck", [(0xF3, 0xF2, 0xED)])])
check("GROUND REPEAT" in codes(d, taste=tp),
      "a repeated canvas VALUE is caught from a one-hex history row",
      "got {}".format(codes(d, taste=tp)))

d, tp = _deck(tmp, "ground-fresh", (0x0A, 0x0F, 0x0A), [((0x33, 0xFF, 0x66), 40)],
              [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)],
              history=[("previous-deck", [(0xF3, 0xF2, 0xED)])])
probs, facts = crp.check(d, taste=tp)
check("GROUND REPEAT" not in {c for c, _ in probs} and facts.get("band"),
      "a different value band passes, and the band streak is REPORTED either way",
      "{} / band={}".format({c for c, _ in probs}, facts.get("band")))

# A pixel check with no pixels must never report clean.
d, _ = _deck(tmp, "norender", (0, 0, 0), [], [(0x11, 0x22, 0x33)])
for f in (d / "render").glob("*.png"):
    f.unlink()
check("NO RENDERS" in codes(d), "no renders is reported, not passed", "got {}".format(codes(d)))

# A palette with no hex (a locked corporate template, a mimic) is UNCHECKED, not clean.
d, _ = _deck(tmp, "nohex", (0x11, 0x22, 0x33), [((0x44, 0x55, 0x66), 40)], [])
probs, facts = crp.check(d)
check(not probs and facts.get("note"),
      "a palette naming no hex is reported as not-checked rather than silently passed",
      "{} / note={!r}".format(probs, facts.get("note")))

# The written waiver, on both key spellings the gates accept.
d, _ = _deck(tmp, "waived", (0x20, 0x20, 0x20), [((0x80, 0x80, 0x80), 40)],
             [(0xC4, 0x2E, 0x1C)])
(d / ".deck-gates.json").write_text(json.dumps(
    {"design_plan": {"palette": "#C42E1C", "register_pixels_waived": "one-colour print run"}}),
    encoding="utf-8")
probs, facts = crp.check(d)
check(not probs and facts.get("waived"),
      "a written waiver stands the check down and SAYS it stood down",
      "{} {}".format(probs, facts))

# REGRESSION: a deck rendered in GREYSCALE while the plan declares a hue. The count-based rule
# cannot see this on its own — a two-colour plan whose near-black ground still matches scores
# 1 of 2 and clears "fewer than half" — so the hue rule is separate on purpose.
from PIL import Image                                                        # noqa: E402
d, _ = _deck(tmp, "greyscale", (0x0A, 0x0F, 0x0A), [((0x33, 0xFF, 0x66), 12)],
             [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)])
for f in (d / "render").glob("*.png"):
    Image.open(f).convert("L").save(f)
check("DECLARED HUES ABSENT" in codes(d),
      "a deck rendered in greyscale under a plan declaring a hue is caught",
      "got {}".format(codes(d)))

# REGRESSION: one unreadable PNG must not switch the check off for the whole deck. Both callers
# wrap this module in try/except, so anything it RAISES becomes "NOT CHECKED" for every page.
d, _ = _deck(tmp, "corrupt", (0x0A, 0x0F, 0x0A), [((0x33, 0xFF, 0x66), 12)],
             [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)])
(d / "render" / "slide02.png").write_bytes(b"not a png")
probs, facts = crp.check(d)
check("UNREADABLE RENDER" in {c for c, _ in probs} and facts.get("pages") == 2,
      "a corrupt render is REPORTED and the readable pages are still measured",
      "{} / pages={}".format({c for c, _ in probs}, facts.get("pages")))

# Renders arrive in whatever mode the rasteriser produced; none of them may crash or mislead.
for mode in ("L", "P", "RGBA"):
    d, _ = _deck(tmp, "mode" + mode, (0x0A, 0x0F, 0x0A), [((0x33, 0xFF, 0x66), 12)],
                 [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)])
    for f in (d / "render").glob("*.png"):
        Image.open(f).convert(mode).save(f)
    got = codes(d)
    want = "DECLARED HUES ABSENT" in got if mode == "L" else not got
    check(want, "a {} -mode render is read correctly".format(mode), "got {}".format(got))

# The numpy-free fallback must give the SAME verdict — a minimal runtime is not a wrong runtime.
import builtins                                                              # noqa: E402
d, _ = _deck(tmp, "nonumpy", (0x0A, 0x0F, 0x0A),
             [((0x33, 0xFF, 0x66), 12), ((0xFF, 0x5A, 0x5A), 12)],
             [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66), (0xFF, 0x5A, 0x5A)])
with_np = crp.check(d)[1]
_real_import = builtins.__import__


def _no_numpy(name, *a, **k):
    if name == "numpy" or name.startswith("numpy."):
        raise ImportError("numpy unavailable")
    return _real_import(name, *a, **k)


builtins.__import__ = _no_numpy
try:
    without_np = crp.check(d)[1]
finally:
    builtins.__import__ = _real_import
check(with_np["present"] == without_np["present"] and with_np["field"] == without_np["field"],
      "the numpy-free path reaches the same verdict as the numpy path",
      "{} vs {}".format(with_np["present"], without_np["present"]))

# ── 2. the wiring: both delivery paths must ask the SAME code ────────────────────────────────
render = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
codex = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")

check("_gate_section('register_pixels')" in render,
      "render_deck.py registers a `register_pixels` gate section",
      "no section found — the checker would exist and never run")
check("import check_register_pixels" in render,
      "render_deck.py delegates to the checker module rather than restating the rule")
check("check_register_pixels.py" in codex and "check_register_pixels(evidence" in codex,
      "the codex delivery gate runs the same checker",
      "a rule enforced on one runtime only is how the two paths drift")

# The selftest must be runnable and green — it is what a non-Claude runtime runs to trust this.
r = subprocess.run([sys.executable, str(SCRIPTS / "check_register_pixels.py"), "--selftest"],
                   capture_output=True, text=True)
check(r.returncode == 0, "check_register_pixels.py --selftest passes",
      (r.stdout + r.stderr)[-400:])

print("\n".join("  ok   " + m for m in OKS))
if FAILS:
    print("\n".join("  FAIL " + m for m in FAILS))
print("\n{} passed, {} failed".format(len(OKS), len(FAILS)))
raise SystemExit(1 if FAILS else 0)
