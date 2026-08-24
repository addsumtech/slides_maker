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
    if unusable:
        print(f"\n{unusable} token(s) fall under 3.0 somewhere they are used — pick a different "
              f"ground for them, or a different hue.")
        return 1
    print("\nevery token has a stated role. Paste the FILL/TEXT split into the design plan.")
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
