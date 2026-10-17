#!/usr/bin/env python3
"""No literal colour inside a component body — every surface, line and ink comes from the theme (dk._th) or a palette
constant, so a component follows the active visual language. usage: check_component_theme.py  (scans the Tier-1
components in deckkit.py). An exception is allowlisted below WITH ITS REASON."""
import ast
import re
import sys
from pathlib import Path

_HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")
# (function, literal) -> why the literal stays. A semantic colour (good/bad, a diverging map's ends) is not a theme
# role; its text is contrast-picked at the call site.
ALLOW = {
    ("heat_matrix", "2C6FBB"): "diverging map, cold end — semantic; cell labels contrast-picked",
    ("heat_matrix", "C63A33"): "diverging map, hot end and risk high — semantic",
    ("heat_matrix", "2E8B57"): "risk ramp, low — semantic",
    ("heat_matrix", "E0A32E"): "risk ramp, mid — semantic",
    ("scorecard", "CFD7E6"): "the opt-in glass_tint path: a caption on the glass card's own dark tint, not on the page",
    ("_heat_color", "2C6FBB"): "heat_matrix's diverging map, cold end — semantic (its helper)",
    ("_heat_color", "C63A33"): "heat_matrix's diverging map, hot end and risk high — semantic (its helper)",
    ("_heat_color", "2E8B57"): "heat_matrix's risk ramp, low — semantic (its helper)",
    ("_heat_color", "E0A32E"): "heat_matrix's risk ramp, mid — semantic (its helper)",
    ("glass_card", "FFFFFF"): "scorecard's opt-in glass sheen: a white highlight gradient ON the glass, not a page colour",
}


def _literal(node):
    if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "RGBColor":
        try:
            return "".join("%02X" % ast.literal_eval(a) for a in node.args)
        except Exception:
            return None                    # computed channels (a blend, a tint) are not a literal colour
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and _HEX.match(node.value):
        return node.value.lstrip("#").upper()
    return None


def unknown(path, functions):
    """Listed names that are not top-level functions of `path` — a nested or renamed one would be skipped in silence."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    top = {fn.name for fn in tree.body if isinstance(fn, ast.FunctionDef)}
    return sorted(set(functions) - top)


def with_helpers(path, functions):
    """`functions` plus every top-level function they call, transitively: a colour drawn by a helper (_eval_mark, the
    heat map's _heat_color) lands on the component's slide all the same."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    top = {fn.name: fn for fn in tree.body if isinstance(fn, ast.FunctionDef)}
    seen, todo = set(f for f in functions if f in top), [f for f in functions if f in top]
    while todo:
        for node in ast.walk(top[todo.pop()]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in top \
                    and node.func.id not in seen:
                seen.add(node.func.id); todo.append(node.func.id)
    return sorted(seen)


def scan(path, functions):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    out = []
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name in functions:
            for node in ast.walk(fn):
                if node is fn:
                    continue
                lit = _literal(node)
                if lit:
                    # a legacy argument of _th(role, legacy) is the sanctioned place for the old literal
                    out.append((fn.name, getattr(node, "lineno", fn.lineno), lit))
    return _drop_th_legacy(tree, out, functions)


def _drop_th_legacy(tree, found, functions):
    keep = []
    legacy_lines = set()
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name in functions:
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_th" and len(node.args) >= 2:
                    for sub in ast.walk(node.args[1]):
                        if hasattr(sub, "lineno"):
                            legacy_lines.add((fn.name, sub.lineno, _literal(sub)))
    for x in found:
        if (x[0], x[1], x[2]) not in legacy_lines:
            keep.append(x)
    return keep


import vl_contract as _ct                                     # noqa: E402  plain data
# the Tier-1 components deckkit draws (the designed_charts recipes are matplotlib: designed_charts._theme colours them),
# plus the shared tint and axis helpers they draw through
TIER1 = tuple(n for n in _ct.TIER1 if n not in ("distribution", "forest_plot", "km_curve", "marimekko", "radar",
                                                "roc_curve", "waterfall", "bland_altman")) + ("tint", "axis_scale")


def main():
    deckkit = Path(__file__).resolve().parent / "deckkit.py"
    missing = unknown(str(deckkit), TIER1)
    for name in missing:
        print("  FAIL {}: listed but not a top-level function of deckkit.py — it would never be scanned".format(name))
    names = with_helpers(str(deckkit), TIER1)
    found = [x for x in scan(str(deckkit), names) if (x[0], x[2]) not in ALLOW]
    for fn, line, lit in found:
        print("  FAIL deckkit.py:{} {}(): literal colour {} — use _th(role, legacy) or a palette constant".format(line, fn, lit))
    print("[component-theme] {} literal colour(s) outside the theme across {} functions (the components and the helpers "
          "they call); {} unknown name(s)".format(len(found), len(names), len(missing)))
    return 1 if found or missing else 0


if __name__ == "__main__":
    sys.exit(main())
