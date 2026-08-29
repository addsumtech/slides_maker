#!/usr/bin/env python3
"""The surface kits: do they build the REGISTER, obey it, and stay out of the content's way.

The measurement that motivated the module: one identical page through all 18 presets rendered as
18 colourways of one page. These tests hold the three properties that stop the kits from being
the same thing with more code — the pages must actually DIFFER, each must obey its own register's
prohibitions, and the content rect a kit hands back must be usable (nothing loud painted into it).
That last one is not theoretical: the first render put a memphis triangle through a card corner and
a bauhaus disc through the third card, under a docstring promising it could not happen.
"""
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

warnings.simplefilter("ignore")

import deckkit as dk                      # noqa: E402
import presets                            # noqa: E402
import register_surface as rs             # noqa: E402
import check_register_guard as guard      # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


def _snapshot():
    return {k: getattr(dk, k) for k in dir(dk) if k.isupper()}


def _restore(snap):
    for k, v in snap.items():
        setattr(dk, k, v)


def _page(register, role="content", index=0):
    presets.apply(register)
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    band = rs.ground(s, register, role=role, index=index)
    return prs, s, band


# ---------------------------------------------------------------- every kit names a real register
check(set(rs.registers()) <= set(presets.PRESETS),
      "every kit names a register that actually exists in the preset gallery")
check(sorted(rs.registers()) == sorted(presets.PRESETS),
      "every one of the {} presets has a surface kit — a register with none would silently be "
      "back to a colourway".format(len(presets.PRESETS)))
check(sorted(rs.CARDS) == sorted(rs.GROUNDS),
      "every kit has BOTH halves: a ground and a card form. A ground alone is wallpaper — the card is what makes the pages differ in shape rather than colour")
check(not rs.has("no_such_register") and not rs.has(None) and not rs.has(""),
      "has() answers False for a name that is not a register, rather than raising")

# ------------------------------------------------------------ the content rect is usable and clear
snap = _snapshot()
try:
    for reg in rs.registers():
        for role in ("cover", "content", "section", "closer"):
            _prs, slide, (bx, by, bw, bh) = _page(reg, role=role, index=3)
            W, H = dk._slide_size(slide)
            check(bx >= 0 and by >= 0 and bx + bw <= W + 1e-6 and by + bh <= H + 1e-6,
                  "{}/{}: the content rect is on the canvas".format(reg, role))
            check(bw >= 3.5 and bh >= 1.5,
                  "{}/{}: the content rect is big enough to hold a page ({:.1f}x{:.1f}in)".format(
                      reg, role, bw, bh))
finally:
    _restore(snap)

# The invariant with teeth: a LOUD mark inside the returned rect raises rather than shipping.
snap = _snapshot()
try:
    presets.apply("memphis")
    prs = dk.blank_deck()
    slide = dk.add_slide(prs)
    del rs._MARKS[:]
    original = rs.GROUNDS["memphis"]
    try:
        rs.GROUNDS["memphis"] = lambda sl, role, i: (
            rs._shape(sl, rs.MSO_SHAPE.OVAL, 4.0, 3.0, 1.0, 1.0, fill=dk.MAGENTA),
            (2.0, 2.0, 8.0, 3.0))[1]
        try:
            rs.ground(slide, "memphis")
            bad.append("a mark painted INTO the returned content rect was not caught")
        except AssertionError as exc:
            check("loud mark" in str(exc),
                  "a kit that paints a loud mark into the rect it hands back RAISES — the promise "
                  "is measured on every call, not asserted in a docstring")
    finally:
        rs.GROUNDS["memphis"] = original
finally:
    _restore(snap)

# ------------------------------------------------------------------- each kit obeys its own guard
snap = _snapshot()
try:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="regsurf-test-"))
    for reg in rs.registers():
        presets.apply(reg)
        prs = dk.blank_deck()
        for i, role in enumerate(("cover", "content")):
            s = dk.add_slide(prs)
            bx, by, bw, bh = rs.ground(s, reg, role=role, index=i)
            cw = min(3.0, bw / 2)
            ch = max(0.8, bh - 0.7)          # derived from what is LEFT, never hand-picked
            rs.card(s, reg, bx, by + 0.6, cw, ch, label="L")
            dk.text(s, bx + 0.2, by + 0.85, max(0.5, cw - 0.4), max(0.3, ch - 0.4),
                    [[("content on the card", 12, dk.DEEP, False, False)]])
        p = tmp / "{}.pptx".format(reg)
        prs.save(str(p))
        viol, _facts = guard.check(p, register=reg)
        check(not viol, "`{}`'s kit obeys `{}`'s own prohibitions — the builders are written "
                        "against the same FORBIDS the guard reads".format(reg, reg))
finally:
    _restore(snap)

# ---------------------------------------------------------- the pages actually differ from each other
snap = _snapshot()
try:
    shapes = {}
    for reg in rs.registers():
        _prs, s, _band = _page(reg, role="content", index=1)
        shapes[reg] = sorted((str(sh.shape_type), round((sh.width or 0) / 914400, 2),
                              round((sh.height or 0) / 914400, 2)) for sh in s.shapes)
    pairs = [(a, b) for i, a in enumerate(rs.registers()) for b in rs.registers()[i + 1:]]
    same = [(a, b) for a, b in pairs if shapes[a] == shapes[b]]
    check(not same,
          "no two kits build the same set of shapes — the whole point is that the pages stop being "
          "one page in eighteen colourways ({} pairs compared)".format(len(pairs)))
    check(all(len(v) >= 2 for v in shapes.values()),
          "every kit actually paints something")
finally:
    _restore(snap)

# ----------------------------------------------------------------------------------- determinism
snap = _snapshot()
try:
    def fp(reg, index):
        _prs, s, _b = _page(reg, index=index)
        return [(str(sh.shape_type), sh.left, sh.top, sh.width, sh.height) for sh in s.shapes]
    check(fp("midcentury", 5) == fp("midcentury", 5),
          "the same index builds the same page — placement varies by index, never by a random "
          "number, so two builds of one deck stay byte-identical")
    check(fp("memphis", 2) != fp("memphis", 3),
          "...and different indices vary, so twelve pages do not repeat one arrangement")
finally:
    _restore(snap)

# ------------------------------------------------------- the marks are usable outside a kit as well
snap = _snapshot()
try:
    presets.apply("memphis")
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    before = len(s.shapes._spTree)
    rs.halftone(s, 1, 1, 2, 1, dk.MAGENTA, cols=6, rows=4)
    rs.starburst(s, 3, 3, 0.5, dk.BLUE, rays=8)
    rs.zigzag(s, 1, 5, 1, 0.3, dk.DEEP, teeth=3)
    rs.tri(s, 6, 1, 0.5, 0.5, dk.TEAL)
    rs.color_band(s, 6.5, 0.2, dk.DEEP)
    rs.boomerang(s, 8, 1, 1, 0.6, dk.BLUE)
    rs.scanlines(s, dk.MUTE, spacing=1.0)
    check(len(s.shapes._spTree) > before + 20,
          "every mark is callable on its own, so a BESPOKE register can borrow a halftone or a "
          "starburst without a kit")
finally:
    _restore(snap)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
