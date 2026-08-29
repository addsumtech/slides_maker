#!/usr/bin/env python3
"""Resolve a deck's palette into FILL-only vs TEXT-safe tokens — once, before the build.

WHY THIS EXISTS. SKILL.md already states the rule: "a hue used as TEXT must itself clear >=4.5:1
on its background", so keep two tokens per accent — a bright fill and a darker text-safe twin.
The rule is correct and it is still easy to break, because the check is per-PAIR and a build
touches dozens of pairs. Measured on one real deck, the author declared the two-token rule in
the design plan and then violated it four separate times — a vivid ochre set as a tier label on
its own pale slab (2.34:1), coral emphasis text on a coral tint (4.19:1), a table's highlight
colour (4.19:1), and a muted grey used for real content on cream (4.26:1). None were reckless;
each was a pair the author simply was not thinking about while computing contrast ad-hoc for a
different pair. Every one surfaced at render time or in review, each costing a round.

A matrix is the fix. Computing all N x M pairs once costs nothing and turns "I remembered to
darken the coral" into a table you read. Print it at Step 2/3, paste the FILL/TEXT split into
the design plan, and build from the tokens it hands back.

    # explicit tokens
    python3 scripts/palette_audit.py --inks E2543A,D18A2E,1F5F63,20304A \\
                                     --grounds FAF3E4,FBE3DC,F7E7CE,FFFFFF

    # or pull every colour constant out of a deck's style module
    python3 scripts/palette_audit.py --from-style ~/Downloads/mydeck/style.py

Thresholds are WCAG: 4.5 body text · 3.0 large text (>=18pt, or >=14pt bold) · 3.0 non-text
marks (icon glyph on its tile, a symbol on a chip, an arrowhead on a band — WCAG 1.4.11).

Exit 0 when every pair the deck actually needs is resolvable, 1 when a token has no safe use.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

BODY, LARGE, MARK = 4.5, 3.0, 3.0


def _srgb(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _lum(hexs: str) -> float:
    h = hexs.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def ratio(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def darken_to(ink: str, ground: str, target: float) -> str | None:
    """The nearest darker twin of `ink` that clears `target` on `ground`, hue preserved."""
    h = ink.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    for step in range(100, 14, -1):
        f = step / 100.0
        cand = "%02X%02X%02X" % (int(r * f), int(g * f), int(b * f))
        if ratio(cand, ground) >= target:
            return cand
    return None


def _norm(s: str) -> str | None:
    s = s.strip().lstrip("#").upper()
    return s if re.fullmatch(r"[0-9A-F]{6}", s) else None


def from_style(path: Path) -> tuple[list[str], list[str]]:
    """Every 6-hex colour constant in a style module, in declaration order.

    Grounds are guessed as the lightest third (a canvas/tint is what text sits ON) and inks as
    everything else — a guess the printed table makes obvious enough to correct by hand.
    """
    spec = importlib.util.spec_from_file_location("_style_probe", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_style_probe"] = mod
    spec.loader.exec_module(mod)

    seen: dict[str, str] = {}
    for name in dir(mod):
        if name.startswith("_"):
            continue
        val = getattr(mod, name)
        for cand in ([val] if isinstance(val, str) else
                     list(val) if isinstance(val, (list, tuple)) else []):
            if isinstance(cand, str) and (hx := _norm(cand)):
                seen.setdefault(hx, name)
        if val.__class__.__name__ == "RGBColor":
            if hx := _norm(str(val)):
                seen.setdefault(hx, name)
    hexes = list(seen)
    if not hexes:
        raise RuntimeError(f"no colour constants found in {path}")
    light = sorted(hexes, key=_lum, reverse=True)
    n_ground = max(1, len(light) // 3)
    return [h for h in hexes if h not in light[:n_ground]], light[:n_ground]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inks", help="comma-separated hex colours used as TEXT or as MARKS")
    ap.add_argument("--grounds", help="comma-separated hex colours text SITS ON")
    ap.add_argument("--from-style", dest="style", help="a deck style.py to read tokens from")
    a = ap.parse_args()

    if a.style:
        try:
            inks, grounds = from_style(Path(a.style).expanduser())
        except Exception as e:
            print(f"NOT CHECKED — {e}", file=sys.stderr)
            return 2
        print(f"tokens read from {a.style}\n")
    elif a.inks and a.grounds:
        inks = [h for t in a.inks.split(",") if (h := _norm(t))]
        grounds = [h for t in a.grounds.split(",") if (h := _norm(t))]
    else:
        ap.error("give --inks and --grounds, or --from-style")

    w = max(len(g) for g in grounds) + 2
    print("contrast matrix — ink (rows) on ground (columns)")
    print("  " + " " * 10 + "".join(f"{g:>{w}}" for g in grounds))
    for ink in inks:
        cells = []
        for g in grounds:
            r = ratio(ink, g)
            flag = " " if r >= BODY else ("*" if r >= LARGE else "!")
            cells.append(f"{r:>{w - 1}.2f}{flag}")
        print(f"  {ink:<10}" + "".join(cells))
    print("\n  blank = clears 4.5 (body text) · * = 3.0-4.5 (large/bold or a MARK only)"
          "\n  !     = under 3.0 — unusable as text or as a mark on that ground")

    print("\nresolved tokens — use the FILL value for shapes, the TEXT value for any run")
    unusable = 0
    for ink in inks:
        worst_g = min(grounds, key=lambda g: ratio(ink, g))
        r = ratio(ink, worst_g)
        if r >= BODY:
            print(f"  {ink}  FILL + TEXT anywhere        (worst pair {r:.2f} on {worst_g})")
            continue
        fixes = []
        for g in grounds:
            if ratio(ink, g) < BODY:
                tw = darken_to(ink, g, BODY)
                fixes.append(f"on {g} -> {tw} ({ratio(tw, g):.2f})" if tw else f"on {g} -> none")
        ok_as_mark = all(ratio(ink, g) >= MARK for g in grounds)
        role = "FILL only" + ("" if ok_as_mark else "; NOT even a mark on every ground")
        if not ok_as_mark:
            unusable += 1
        print(f"  {ink}  {role}")
        for f in fixes:
            print(f"      TEXT twin {f}")
    # The colour-vision report runs BEFORE any early return. A palette with a contrast problem is
    # exactly the palette about to be reworked, which is the moment its CVD behaviour is cheapest
    # to fix — reporting one and swallowing the other would send the author back twice.
    hits = cvd_collisions([c.upper() if c.startswith("#") else "#" + c.upper()
                           for c in dict.fromkeys(inks)])
    common = [h for h in hits if h[0] in CVD_COMMON]
    rare = [h for h in hits if h[0] not in CVD_COMMON]
    if common:
        print("\nCOLOUR VISION — {} pair(s) distinct to you that lose their distinction for a "
              "red-green colour vision deficiency (~8% of men, ~0.5% of women):".format(len(common)))
        for kind, a, b, _d, share in common[:8]:
            print("  {:<13} {} vs {}  ->  {} vs {}   ({:.0%} of the separation left)".format(
                kind, a, b, simulate(a, kind), simulate(b, kind), share))
        print("  This matters only where the two carry MEANING — a series, a status, a legend. "
              "Where they do, separate them by LIGHTNESS or by shape/label as well as hue, or "
              "take the categorical set from deckkit.OKABE_ITO, which is built for this.")
    else:
        print("\nCOLOUR VISION: every pair keeps its distinction under deuteranopia and "
              "protanopia (~8% of men).")
    if rare:
        print("  [--] {} pair(s) also collapse under TRITANOPIA, which is rarer than 1 in 10,000 "
              "and not sex-linked: {}. Worth knowing, not usually worth redesigning for — "
              "Okabe-Ito itself collides here.".format(
                  len(rare), ", ".join("{}/{}".format(a, b) for _k, a, b, _d, _s in rare[:4])))
    if unusable:
        print(f"\n{unusable} token(s) fall under 3.0 somewhere they are used — pick a different "
              f"ground for them, or a different hue.")
        return 1
    print("\nevery token has a stated role. Paste the FILL/TEXT split into the design plan.")
    return 0


# ── COLOUR VISION: the palette that separates for you and collapses for 1 reader in 12 ────────
# `deckkit.OKABE_ITO` has been offered as "the colour-blind-safe categorical fallback" since it was
# added, and `references/data-viz.md` recommends it — but nothing ever CHECKED a palette, so the
# recommendation only helped the author who already remembered it. Contrast and CVD are different
# questions and a palette can pass one while failing the other: two hues at very different
# lightness always clear a contrast ratio and can still be the same colour to a deuteranope.
#
# Roughly 8% of men and 0.5% of women have some colour vision deficiency, so on a room of forty
# this is not an edge case — it is most rooms. The simulation is Brettel/Viénot-style: convert to
# linear RGB, project onto the dichromat's plane, convert back.
# The simulation is Viénot–Brettel–Mollon (1999): sRGB -> linear -> LMS cone response -> project
# onto the plane the missing cone leaves -> back. Doing it in LMS is not pedantry. The first
# version of this used the widely-copied 3x3 "RGB-space" matrices instead, and it was WRONG in a
# way that passes a casual look: greys and white came back unchanged, so it seemed fine, while pure
# green under deuteranopia came out PINK-GREY (#A59595) when a deuteranope in fact sees it as
# yellow. A wrong simulation is worse than none — it would have cleared palettes that collapse and
# flagged palettes that do not.
_RGB2LMS = ((17.8824, 43.5161, 4.11935),
            (3.45565, 27.1554, 3.86714),
            (0.0299566, 0.184309, 1.46709))
_LMS2RGB = ((0.0809444479, -0.130504409, 0.116721066),
            (-0.0102485335, 0.0540193266, -0.113614708),
            (-0.000365296938, -0.00412161469, 0.693511405))
# Each dichromacy replaces the missing cone's response with a linear function of the other two.
_CVD = {
    "deuteranopia": ("M", (0.494207, 0.0, 1.24827)),     # ~6% of men — the common one
    "protanopia":   ("L", (0.0, 2.02344, -2.52581)),     # ~2% of men
    "tritanopia":   ("S", (-0.395913, 0.801109, 0.0)),   # rare, and not sex-linked
}


def _mul(m, v):
    return [sum(m[r][i] * v[i] for i in range(3)) for r in range(3)]


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    c = max(0.0, min(1.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return int(round(max(0.0, min(1.0, v)) * 255))


def simulate(hexstr, kind):
    """`hexstr` as a viewer with `kind` sees it, returned as #RRGGBB."""
    h = hexstr.lstrip("#")
    lin = [_srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4)]
    lms = _mul(_RGB2LMS, lin)
    missing, coef = _CVD[kind]
    idx = {"L": 0, "M": 1, "S": 2}[missing]
    lms[idx] = sum(coef[i] * lms[i] for i in range(3))
    return "#%02X%02X%02X" % tuple(_linear_to_srgb(v) for v in _mul(_LMS2RGB, lms))


def _dist(a, b):
    """Redmean distance — the same approximation check_register_pixels uses, for one answer."""
    ra = [int(a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    rb = [int(b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    rm = (ra[0] + rb[0]) / 2.0
    dr, dg, db = ra[0] - rb[0], ra[1] - rb[1], ra[2] - rb[2]
    return ((2 + rm / 256.0) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256.0) * db * db) ** 0.5


# The bar is ABSOLUTE distance after simulation — "how different are these two to that viewer" —
# not how much the pair CHANGED. The first version used the change ratio and it could not do the
# job: Okabe-Ito's worst common-CVD pair keeps 22% of its separation and the classic red/green
# mistake keeps 16%, so any ratio cut sits in a 6-point gap and would flag the palette this skill
# recommends. Measured in absolute terms the two populations are properly apart, because a pair can
# change a great deal and still be perfectly distinct:
#
#     Okabe-Ito, worst pair under deuteranopia/protanopia   68   (#0072B2 vs #CC79A7)
#     matplotlib red/green                                  56
#     lightness-matched red/green                           34
#
# 60 sits in that gap. A palette BUILT for colour-universal design has to pass, or the check
# teaches people to ignore it.
CVD_MIN = 60.0         # below this, the pair has stopped being two colours for that viewer
CVD_SAME = 26.0        # a pair already this close to everyone is the author's decision, not a finding
# Prevalence, because a finding should be weighted by how many people it reaches. Red-green
# deficiency is ~8% of men and ~0.5% of women; tritanopia is rarer than 1 in 10,000 and not
# sex-linked. They are reported separately rather than summed: Okabe-Ito — built for
# colour-universal design — DOES collide under tritanopia (its vermillion and reddish-purple both
# land near #A8A800), and a check that called that palette unsafe would be training people to
# dismiss it.
CVD_COMMON = ("deuteranopia", "protanopia")


def cvd_collisions(colours, floor=CVD_MIN, same=CVD_SAME):
    """[(kind, a, b, distance, share_kept)] for pairs that stop being two colours under a CVD.

    Only pairs DISTINCT to a trichromat are considered — two colours already alike are the author's
    decision, not an accessibility finding.
    """
    out = []
    for kind in _CVD:
        for i, a in enumerate(colours):
            for b in colours[i + 1:]:
                base = _dist(a, b)
                if base <= same:
                    continue
                d = _dist(simulate(a, kind), simulate(b, kind))
                if d < floor:
                    out.append((kind, a, b, d, d / base if base else 1.0))
    return sorted(out, key=lambda r: r[3])


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
