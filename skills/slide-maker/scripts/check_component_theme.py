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


TIER1 = ("agenda bento consort_flow dot_strip dumbbell_board eval_matrix funnel gantt heat_matrix iso_bars iso_prism "
         "iso_stack leaderboard meter_bar native_chart org_tree position_map pyramid sankey scorecard segmented_bar "
         "small_multiples stat_row step_list table tier_stack timeline unit_grid venn source_note tint draw_axis").split()


def main():
    deckkit = Path(__file__).resolve().parent / "deckkit.py"
    found = [x for x in scan(str(deckkit), TIER1) if (x[0], x[2]) not in ALLOW]
    for fn, line, lit in found:
        print("  FAIL deckkit.py:{} {}(): literal colour {} — use _th(role, legacy) or a palette constant".format(line, fn, lit))
    print("[component-theme] {} literal colour(s) outside the theme".format(len(found)))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
