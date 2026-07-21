#!/usr/bin/env python3
"""Mechanical DIVERGENCE check for direction-gate candidates — the anti-theater gate.

The direction gate asks for "3 *differentiated* directions", and the same agent that wrote them
then judges whether they differ. That is one mind checking itself, and it fails in a specific,
repeatable way: three token sets that are three colourways of one layout, presented as a choice.
This script measures divergence DETERMINISTICALLY from the token sets, per pair, on four axes:

  mode         light/dark, from the background's relative luminance (a mode flip is strong divergence)
  palette      euclidean distance between backgrounds + between accents (the loudest single signal)
  type         the display/body font PAIRING as a class (serif/sans/mono/slab) + whether the deck
               sets a display face apart from its body face at all
  composition  the cover archetype and the content skeleton — WHERE the ink sits. Added because a
               measured real deck showed 8/12 pages sharing one composition signature while its
               FORMS varied correctly: composition was never being chosen, only defaulted.

A pair is TOO SIMILAR when it matches on >=3 of the 4 axes. The response is never an auto-kill:
REDIVERGE the pair, or keep it WITH A NAMED JUSTIFICATION recorded on the `direction gate:` line
(a brand-locked accent is a legitimate reason for a palette match — the shared hue is a mandate,
and divergence then has to move onto the other three axes).

CLI:  python directions_diversity.py directions.json [--json]
Exit: 0 = every pair diverges · 2 = >=1 too-similar pair (printed) · 1 = unreadable input.
"""
import argparse
import itertools
import json
import re
import sys

PALETTE_T = 90.0        # combined bg+accent distance under which two palettes read "one family"

_SERIF = ("georgia", "times", "garamond", "baskerville", "palatino", "cambria", "book antiqua",
          "constantia", "hoefler", "songti", "mincho", "serif")
_MONO = ("menlo", "consolas", "monaco", "courier", "sf mono", "monospace")
_SLAB = ("rockwell", "roboto slab", "zilla", "museo slab")


def _rgb(h):
    h = (h or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h or ""):
        raise ValueError("not a hex colour: {!r}".format(h))
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _face_class(stack):
    """Classify a CSS font stack by its FIRST family — that is what actually renders."""
    first = (stack or "").split(",")[0].strip().strip("'\"").lower()
    # "sans-serif" CONTAINS "serif" — check the sans generics before any substring test, or a bare
    # generic stack scores as a serif deck and two directions look more different than they are.
    if first in ("sans-serif", "system-ui", "-apple-system", "ui-sans-serif") or "sans" in first:
        return "sans"
    for names, cls in ((_MONO, "mono"), (_SLAB, "slab"), (_SERIF, "serif")):
        if any(n in first for n in names):
            return cls
    return "sans"


# Kept in lockstep with archetypes_html.py's vocabulary ON PURPOSE: a typo used to pass HERE
# (counting as a divergent composition) and only fail later in the renderer, so a collapsed set
# could earn a divergence credit from a value that does not exist.
_COVERS = ("centred", "low-left", "split-vertical", "full-bleed-type")
_SKELETONS = ("statement", "split", "island", "band", "rail")


def _checked(d, key, allowed):
    v = d.get(key, allowed[0])
    if v not in allowed:
        raise ValueError("direction {!r}: {} must be one of {}, got {!r}".format(
            d.get("name", "?"), key, allowed, v))
    return v


def _features(d):
    bg, accent = _rgb(d.get("bg", "#FFFFFF")), _rgb(d.get("accent", "#B0451F"))
    disp, body = d.get("font_display", ""), d.get("font_body", "")
    return {
        "name": d.get("name", "?"),
        "mode": "dark" if _lum(bg) < 110 else "light",
        "bg": bg, "accent": accent,
        # the PAIRING, not just the display face: serif-display-over-sans-body and an all-sans deck
        # are different type attitudes even when the display class alone matches.
        "type": (_face_class(disp), _face_class(body), _face_class(disp) == _face_class(body)),
        "density": str(d.get("density", "minimal")).strip().lower(),
        "comp": (_checked(d, "cover", _COVERS), _checked(d, "skeleton", _SKELETONS)),
    }


def _pair(a, b):
    pal = (sum((a["bg"][i] - b["bg"][i]) ** 2 for i in range(3)) ** 0.5
           + sum((a["accent"][i] - b["accent"][i]) ** 2 for i in range(3)) ** 0.5)
    # ONE axis list, identical to the prose rule in SKILL.md/collaborative-mode.md:
    # {palette mood · type attitude · density/scale · composition}. Mode is folded INTO the
    # palette axis (a light/dark flip IS a palette-mood divergence; scoring it separately
    # double-counted one perceptual difference), and density is measured because it is in the
    # token — an unmeasured axis lets the prose rule and the script reach opposite verdicts
    # on the same pair.
    axes = {
        "palette": a["mode"] == b["mode"] and pal < PALETTE_T,
        "type": a["type"] == b["type"],
        "density": a["density"] == b["density"],
        "composition": a["comp"] == b["comp"],
    }
    matched = [k for k, v in axes.items() if v]
    return {"a": a["name"], "b": b["name"], "palette_distance": round(pal, 1),
            "same_mode": a["mode"] == b["mode"],
            "matched_axes": matched, "too_similar": len(matched) >= 3,
            "a_comp": "/".join(a["comp"]), "b_comp": "/".join(b["comp"])}


def check(directions):
    feats = [_features(d) for d in directions]
    pairs = [_pair(x, y) for x, y in itertools.combinations(feats, 2)]
    return {"pairs": pairs, "flagged": [p for p in pairs if p["too_similar"]],
            "modes": {f["name"]: f["mode"] for f in feats},
            "compositions": {f["name"]: "/".join(f["comp"]) for f in feats}}


def main():
    ap = argparse.ArgumentParser(description="mechanical direction-candidate diversity check")
    ap.add_argument("directions", help="the same directions.json passed to archetypes_html.py")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()
    try:
        with open(a.directions, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or len(data) < 2:
            raise ValueError("expected a JSON list of 2+ direction objects")
        r = check(data)
    except Exception as e:                                        # noqa: BLE001
        print("[diversity] could not read directions: {}".format(e))
        sys.exit(1)
    if a.as_json:
        print(json.dumps(r, indent=1))
        sys.exit(2 if r["flagged"] else 0)
    for p in r["pairs"]:
        mark = "x TOO SIMILAR" if p["too_similar"] else "v"
        print("  {}  {} vs {}: palette {} · comp {} vs {} · matched: {}".format(
            mark, p["a"], p["b"], p["palette_distance"], p["a_comp"], p["b_comp"],
            ", ".join(p["matched_axes"]) or "none"))
    if r["flagged"]:
        involved = sorted({n for p in r["flagged"] for n in (p["a"], p["b"])})
        print("[diversity] {} pair(s) read as skins of one idea (involving: {}).".format(
            len(r["flagged"]), ", ".join(involved)))
        print("            REDIVERGE them, or keep the pair and record the reason on the")
        print("            `direction gate:` line (e.g. 'brand-locked accent — divergence moved")
        print("            to composition + type'). Never ship an unexplained collapse.")
    sys.exit(2 if r["flagged"] else 0)


if __name__ == "__main__":
    main()
