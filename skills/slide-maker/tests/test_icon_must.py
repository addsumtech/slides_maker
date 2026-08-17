#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Icons are the DEFAULT on categorical content; skipping the family is a HIGH-bar, CLASSIFIED choice.

WHY (user directive, 2026-08). Icons aid the 1-second read and reinforce the visual system on any
deck with categorical / multi-item / conceptual content, and the old `icon_family: none` waiver was
too easy to reach — naming the slides you'd "checked" cleared it, so a casual "not category-rich"
sentence shipped a categorical deck with zero icons. This raises the bar on the WAIVER (not on the
icons themselves): a `none` decision must now ALSO classify WHY from four reasons where an icon
family would genuinely HURT — motif-dominant · editorial-register · tiny-deck · template-locked —
symmetric with the critic waiver's `waived_category`. The default is icons; skipping names its class.

It is NOT "an icon on every slide": icons must ENCODE, not decorate (design-must-be-meaningful), so
the family lands on the categorical/conceptual slides, and the category explains the rest.

Both gate paths hold the same bar (they have drifted on icons before): render_deck._icon_none_waived
and codex_delivery_gate._icon_waiver_ok share the ICON_NONE_CATEGORIES set.

Run:  python3 tests/test_icon_must.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(HERE))

import render_deck as RD  # noqa: E402
from test_critic_waiver_gate import (  # noqa: E402
    ARC_OK, DESIGN_OK, PROV_OK, build_samey, run_gate, write_proof,
)

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}\n       {str(detail)[:340]}")


def base(**dp_over):
    dp = dict(DESIGN_OK)
    dp.update(dp_over)
    return {"critic": {"waived": "No subagent dispatch on this host; both lenses ran inline.",
                       "waived_category": "no-dispatch-on-host", "inline_ran": True},
            "design_plan": dp, "provenance": PROV_OK, "content": ARC_OK}


def main():
    import tempfile
    print("== the helper: named slides are no longer enough; the reason must classify ==")
    check("named slides alone do NOT waive (the raised bar)",
          not RD._icon_none_waived({"design_plan": {"icon_none_checked": ["slide 2"]}}))
    check("named slides + a valid category DO waive",
          RD._icon_none_waived({"design_plan": {"icon_none_checked": ["slide 2"],
                                                "icon_none_category": "motif-dominant"}}))
    check("a category with no named slides does NOT waive",
          not RD._icon_none_waived({"design_plan": {"icon_none_category": "motif-dominant"}}))
    check("an UNRECOGNISED category does not waive (no bare 'not category-rich')",
          not RD._icon_none_waived({"design_plan": {"icon_none_checked": ["slide 2"],
                                                    "icon_none_category": "not-category-rich"}}))
    check("all four high-bar categories are recognised",
          all(RD._icon_none_waived({"design_plan": {"icon_none_checked": ["s"],
                                                    "icon_none_category": c}})
              for c in RD._ICON_NONE_CATEGORIES))

    print("== on a categorical deck that ships zero icons, the gate now BLOCKS a bare `none` ==")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "cat"
        d.mkdir()
        deck = build_samey(d, n=12)   # parallel label rows, no pictures — the categorical shape
        write_proof(d)

        # NB build_samey also trips the SAMENESS composite (a separate gate), so key these on the
        # ICON gate's own die message ("CLASSIFIED reason") rather than the overall exit code.
        _, out = run_gate(deck, base(icon_none_checked=["slide 2", "slide 3"]))
        check("named slides WITHOUT a category no longer clear the ICON gate",
              "CLASSIFIED reason" in out and "motif-dominant" in out, out[-500:])

        _, out = run_gate(deck, base(icon_none_checked=["slide 2", "slide 3"],
                                     icon_none_category="editorial-register"))
        check("named slides + a valid high-bar category clear the ICON gate (no icon die)",
              "CLASSIFIED reason" not in out, out[-500:])

        _, out = run_gate(deck, base(icon_none_checked=["slide 2", "slide 3"],
                                     icon_none_category="不想加"))
        check("an invalid category is refused by the ICON gate, not waved through",
              "CLASSIFIED reason" in out, out[-500:])

    print("== the two gate paths share the category set (they have drifted on icons before) ==")
    src_codex = (SKILL / "scripts" / "codex_delivery_gate.py").read_text(encoding="utf-8")
    check("codex_delivery_gate defines the same ICON_NONE_CATEGORIES",
          "ICON_NONE_CATEGORIES" in src_codex
          and all(c in src_codex for c in RD._ICON_NONE_CATEGORIES))
    check("codex path requires a classified icon waiver (_icon_waiver_ok)",
          "_icon_waiver_ok" in src_codex)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
