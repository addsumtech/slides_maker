#!/usr/bin/env python3
"""check_style_applied — the register a deck DECLARES must be the register it APPLIES.

THE GAP THIS CLOSES
-------------------
Both delivery gates already require the declaration. `codex_delivery_gate.py` demands
`design.style_pick` ("<preset|bespoke> for <domain> - beat <rival> - anti-pick avoided:
<cliche>") and `render_deck.py --gate-check` requires the same field in `.deck-gates.json`.
Neither verified it. Measured by grep across all three gate scripts: `presets.apply`,
`set_geometry` and `set_ground` appear in NONE of them. So a deck recording

    "style_pick": "brutalist for engineering - beat blueprint - anti-pick avoided: dark_tech"

built with deckkit's stock defaults passed every gate, on BOTH runtimes. The competition was
run, the winner was written down, and nothing carried it into the build.

That is the same declared-vs-applied shape as the defects inside deckkit itself: `presets.apply`
returned a `bg` nothing painted, and `set_geometry`'s tokens were read by 1 of 181 functions.
Those are fixed and `tests/test_register_expression.py` proves the call now reaches the pixels.
This file connects the other end - that the call happens at all - so the chain runs
declaration -> call -> pixels with no unwatched link.

WHAT IT CHECKS, AND WHAT IT HONESTLY DOES NOT
---------------------------------------------
It parses the build script and asserts `presets.apply("<name>")` is called for the preset the
deck declared. It checks the CALL, not the rendered geometry - a build could call apply() and
then override every token by hand. That residue is deliberate: measuring the pixels invites
false positives on legitimate local departures (one page deliberately rounder than the
register), and the pixel half is already covered by test_register_expression.py, which proves
apply() reaches the geometry. A cheap check that is right beats an expensive one that cries
wolf, because a gate everyone learns to waive is worse than no gate.

Only PRESET picks are checked. `bespoke ...`, `generated ...` and `n/a - <locked look>` are
skipped by definition: they are not preset-based, and forcing them through a preset-shaped
check would turn the waiver into a rubber stamp.

USAGE
    python3 scripts/check_style_applied.py --build build_deck.py --gates .deck-gates.json
    python3 scripts/check_style_applied.py --build build_deck.py --style-pick "swiss for ..."
    python3 scripts/check_style_applied.py --selftest

Exit 0 applied (or not applicable) - 1 declared-but-not-applied - 2 could not run.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WAIVER_KEY = "style_pick_waived"
_MIN_WAIVER = 24


def preset_names() -> list[str]:
    sys.path.insert(0, str(HERE))
    import presets  # noqa: E402
    return list(presets.names())


def declared_preset(style_pick: str, names) -> str | None:
    """The preset `style_pick` names, or None when the pick is not preset-based.

    `style_pick` is prose by design - it carries the rival it beat and the cliche it avoided -
    so this reads the preset out of it rather than demanding a machine field the authors would
    then have to keep in sync with the sentence.
    """
    if not isinstance(style_pick, str) or not style_pick.strip():
        return None
    s = style_pick.strip().lower()
    # An explicitly non-preset pick. Checked BEFORE name matching, because a bespoke register's
    # prose legitimately names the preset it beat ("bespoke ... beat swiss").
    if re.match(r"^\s*(bespoke|generated|n/?a\b)", s):
        return None
    # The FIRST preset name that appears is the pick; anything after "beat"/"rival"/"over" is the
    # loser, and crediting a deck for applying the register it rejected would be worse than not
    # checking at all.
    head = re.split(r"\bbeat\b|\brival\b|\bover\b|·|—|--", s)[0]
    hits = [(head.find(n), n) for n in names if n in head]
    if not hits:
        return None
    return min(hits)[1]


def applied_presets(build_src: str) -> set[str]:
    """Every literal name passed to presets.apply()/apply() in the build script."""
    tree = ast.parse(build_src)
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = None
        if isinstance(fn, ast.Attribute) and fn.attr == "apply":
            name = "apply"
        elif isinstance(fn, ast.Name) and fn.id == "apply":
            name = "apply"
        if name and node.args and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str):
            out.add(node.args[0].value.strip().lower())
    return out


def evaluate(style_pick, build_src, names, waiver=None):
    """-> (exit_code, message). Pure, so the selftest can drive it without files."""
    want = declared_preset(style_pick, names)
    if want is None:
        return 0, ("style_pick is not preset-based (bespoke / generated / locked look) — "
                   "nothing to apply, nothing to check")
    try:
        got = applied_presets(build_src)
    except SyntaxError as exc:
        return 2, f"NOT CHECKED — the build script does not parse: {exc}"
    if want in got:
        return 0, f"style_pick declares '{want}' and the build calls presets.apply('{want}')"
    if isinstance(waiver, str) and len(waiver.strip()) >= _MIN_WAIVER:
        return 0, f"'{want}' not applied — WAIVED: {waiver.strip()[:120]}"
    applied = ", ".join(sorted(got)) if got else "nothing"
    return 1, (
        f"DECLARED BUT NOT APPLIED — style_pick names '{want}', the build applies {applied}.\n"
        f"  Both delivery gates already require this declaration and neither verified it, so a "
        f"deck could record a register it never used and pass.\n"
        f"  Fix: `p = presets.apply(\"{want}\")` before building — one call carries the palette, "
        f"the geometry (radius/rule_w) and the ground.\n"
        f"  A deliberate departure is a named waiver: \"{WAIVER_KEY}\": \"<why, >={_MIN_WAIVER} "
        f"chars>\" in the design block."
    )


SELFTEST = [
    # (style_pick, build source, waiver, expected_exit, why)
    ("brutalist for engineering · beat blueprint", 'presets.apply("brutalist")', None, 0,
     "declared and applied"),
    ("brutalist for engineering · beat blueprint", 'presets.apply("swiss")', None, 1,
     "applied a DIFFERENT register"),
    ("brutalist for engineering · beat blueprint", 'dk.set_palette(deep=X)', None, 1,
     "hand-set palette, no apply at all — the measured failure"),
    ("bespoke seismograph register · beat swiss", 'dk.set_palette(deep=X)', None, 0,
     "bespoke is not preset-based"),
    ("generated visual identity for the brand", '', None, 0, "generated branch"),
    ("n/a — locked: the user's template", '', None, 0, "locked look"),
    ("swiss for a policy brief · beat consulting", 'p = presets.apply("swiss")\nx = 1', None, 0,
     "assignment form"),
    ("ink_wash for a poetry course · beat editorial_paper", 'from presets import apply\napply("ink_wash")',
     None, 0, "bare imported apply()"),
    ("brutalist for engineering", 'dk.set_palette(deep=X)',
     "the client brand book fixes the border weight at 1pt, which brutalist would triple", 0,
     "a real waiver clears it"),
    ("brutalist for engineering", 'dk.set_palette(deep=X)', "ok", 1,
     "a bare 'ok' is not a waiver"),
    # The loser must never be credited: 'swiss' appears only as the rival.
    ("brutalist for engineering · beat swiss", 'presets.apply("swiss")', None, 1,
     "applying the REJECTED rival is not applying the pick"),
]


def selftest(names) -> int:
    bad = 0
    for pick, src, waiver, want, why in SELFTEST:
        got, msg = evaluate(pick, src, names, waiver)
        if got != want:
            bad += 1
            print(f"  FAIL want={want} got={got}  ({why})\n      {msg.splitlines()[0]}")
    if bad:
        print(f"\ncheck_style_applied selftest: {bad} disagreement(s) — the check no longer "
              f"means what this file says it means.")
        return 1
    blocks = sum(1 for c in SELFTEST if c[3] == 1)
    print(f"selftest ok — {blocks} declared-but-not-applied case(s) blocked, "
          f"{len(SELFTEST) - blocks} legitimate case(s) passed through")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="the declared register must be the applied one")
    ap.add_argument("--build", help="the deck's build script")
    ap.add_argument("--gates", help=".deck-gates.json or .codex-deck-evidence.json")
    ap.add_argument("--style-pick", help="the style_pick string, instead of --gates")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    try:
        names = preset_names()
    except Exception as exc:
        print(f"check_style_applied: NOT CHECKED — cannot import presets ({exc})")
        return 2
    if a.selftest:
        return selftest(names)
    if not a.build:
        ap.error("--build is required (or --selftest)")

    pick, waiver = a.style_pick, None
    if a.gates:
        try:
            rec = json.loads(Path(a.gates).read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"check_style_applied: NOT CHECKED — cannot read {a.gates} ({exc})")
            return 2
        # `.deck-gates.json` keys it under design_plan, the Codex evidence record under design.
        block = rec.get("design_plan") or rec.get("design") or {}
        pick = pick or block.get("style_pick")
        waiver = block.get(WAIVER_KEY)
    if not pick:
        print("check_style_applied: NOT CHECKED — no style_pick found (both delivery gates "
              "require it, so an absent one is already their finding, not this one's)")
        return 2
    try:
        src = Path(a.build).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"check_style_applied: NOT CHECKED — cannot read {a.build} ({exc})")
        return 2

    code, msg = evaluate(pick, src, names, waiver)
    print(("check_style_applied: " if code == 0 else "check_style_applied FAILED: ") + msg)
    return code


if __name__ == "__main__":
    sys.exit(main())
