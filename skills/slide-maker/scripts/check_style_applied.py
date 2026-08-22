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


# A look that is NOT applied by presets.apply(): the Q1(d) image-generated identity, a bespoke
# register, a provided/registered template, a mimic. Each of these derives its own `style.py`, so
# naming a preset in the pick describes the ART DIRECTION, not a call the build makes.
NON_PRESET = re.compile(
    r"\b(bespoke|generated|generate-a-template|image[- ]tool|hero[- ]generated|"
    r"template|mimic|locked)\b")
LOOK_SOURCE_KEY = "look_source"
_PRESET_SOURCES = {"preset"}
_NON_PRESET_SOURCES = {"generated", "bespoke", "template", "mimic", "locked", "provided"}


def declared_preset(style_pick: str, names, look_source=None):
    """-> (preset_name | None, confidence).

    `confidence` is "sure" when the look is known to be preset-based, "unsure" when the pick
    names a preset but also carries a non-preset qualifier. Only "sure" may hard-block.

    WHY THE THREE-WAY ANSWER. The first version answered yes/no from the prose alone and produced
    a FALSE POSITIVE on the Q1(d) generate-a-template branch. `references/codex-runtime.md` says
    the topic contest "runs on the GENERATE-A-TEMPLATE branch too" and governs the generated
    HERO's art-direction, so a legitimate generated-branch pick reads

        "editorial_paper for a poetry course - beat ink_wash - generated hero art-directed by it"

    and the build never calls presets.apply() because the look came out of an image tool. Blocking
    that is worse than the gap it closes: a gate that refuses correct work teaches people to waive
    it, and a waived gate stops guarding the case it was built for. Nothing anywhere records which
    Q1 branch a deck took, so `design_plan.look_source` settles it when present and the prose is
    read conservatively when it is not.
    """
    if isinstance(look_source, str) and look_source.strip():
        ls = look_source.strip().lower()
        if ls in _NON_PRESET_SOURCES:
            return None, "sure"
        if ls not in _PRESET_SOURCES:
            return None, "unsure"
    if not isinstance(style_pick, str) or not style_pick.strip():
        return None, "sure"
    s = style_pick.strip().lower()
    # An explicitly non-preset pick, declared where the format says to declare it. Checked BEFORE
    # name matching, because such a pick legitimately names the preset it beat or was directed by.
    if re.match(r"^\s*(bespoke|generated|n/?a\b)", s):
        return None, "sure"
    # The FIRST preset name that appears is the pick; anything after "beat"/"rival"/"over" is the
    # loser, and crediting a deck for applying the register it rejected would be worse than not
    # checking at all.
    head = re.split(r"\bbeat\b|\brival\b|\bover\b|·|—|--", s)[0]
    hits = [(head.find(n), n) for n in names if n in head]
    if not hits:
        return None, "sure"
    name = min(hits)[1]
    # A preset name AND a non-preset qualifier somewhere in the sentence: cannot tell, do not block.
    if NON_PRESET.search(s) and look_source is None:
        return name, "unsure"
    return name, "sure"


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


def evaluate(style_pick, build_src, names, waiver=None, look_source=None):
    """-> (exit_code, message). Pure, so the selftest can drive it without files."""
    want, confidence = declared_preset(style_pick, names, look_source)
    if want is None:
        return 0, ("style_pick is not preset-based (bespoke / generated / template / locked "
                   "look) — nothing to apply, nothing to check")
    try:
        got = applied_presets(build_src)
    except SyntaxError as exc:
        return 2, f"NOT CHECKED — the build script does not parse: {exc}"
    if want in got:
        return 0, f"style_pick declares '{want}' and the build calls presets.apply('{want}')"
    if isinstance(waiver, str) and len(waiver.strip()) >= _MIN_WAIVER:
        return 0, f"'{want}' not applied — WAIVED: {waiver.strip()[:120]}"
    if confidence == "unsure":
        # Never block a look this gate cannot classify. NOT CHECKED is loud and is not clean.
        return 2, (
            f"NOT CHECKED — style_pick names '{want}' but also reads as a generated / bespoke / "
            f"template look, and the build does not call presets.apply('{want}'). Those are BOTH "
            f"legitimate (the topic contest runs on the generate-a-template branch too and "
            f"art-directs the hero from a preset), so this is not a finding — it is an unverified "
            f'field. Record `"{LOOK_SOURCE_KEY}": "preset"|"generated"|"bespoke"|"template"` in '
            f"the design block and it becomes checkable either way.")
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
    # (style_pick, build source, waiver, expected_exit, why) — look_source appended where used
    # --- the Q1(d) GENERATE-A-TEMPLATE branch, which the first version false-positived on ------
    ("generated register for a poetry course · beat ink_wash", '', None, 0,
     "generated branch, declared in the leading token"),
    ("editorial_paper for a poetry course · beat ink_wash — generated hero art-directed by it",
     'dk.set_palette(deep=X)', None, 2,
     "generated branch leading with the PRESET that art-directed the hero — NOT CHECKED, "
     "never a block: codex-runtime.md runs the topic contest on this branch too"),
    ("editorial_paper for a poetry course — the generated hero follows it", 'x = 1', None, 2,
     "same, with no palette call at all"),
    ("swiss for a status update · beat consulting", 'x = 1', None, 1,
     "a plain preset pick with no generated/bespoke qualifier still HARD blocks"),
    ("n/a — locked: the user's registered template", '', None, 0, "template branch"),
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
    # --- look_source settles what the prose cannot ------------------------------------------
    ("editorial_paper for a poetry course — generated hero", 'x = 1', None, 0,
     "look_source says generated: skipped outright, no NOT CHECKED", "generated"),
    ("editorial_paper for a report", 'x = 1', None, 1,
     "look_source says preset: the qualifier-free pick still blocks", "preset"),
    ("editorial_paper for a poetry course — generated hero", 'presets.apply("editorial_paper")',
     None, 0, "look_source preset AND applied", "preset"),
]


def selftest(names) -> int:
    bad = 0
    for case in SELFTEST:
        pick, src, waiver, want, why = case[:5]
        ls = case[5] if len(case) > 5 else None
        got, msg = evaluate(pick, src, names, waiver, ls)
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
