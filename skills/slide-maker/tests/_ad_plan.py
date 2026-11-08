# -*- coding: utf-8 -*-
"""Test helper: give a gate fixture the art director's Design plan FILE the gate now re-reads.

`render_deck.py --gate-check` blocks without `design_plan.plan_file` (scripts/design_plan_record.py).
Fixtures that are not ABOUT that artifact call `with_ad_plan(gates, deck_dir)` before writing the
record, the same way they fill in the interview answers — each test stays about the thing it checks.
The plan is written OUTSIDE the deck folder, because plan files never ship beside the deck.
"""
import hashlib
from pathlib import Path

AD_PLAN = ("### Design language\nfixture\n### Deck rhythm\nfixture\ngrounds: single — template-locked: CI fixture\n### Per-slide design\nfixture\n"
           "### Form ledger\nfixture\n### Design self-verify\n"
           + "\n".join("- (%s) ok" % c for c in "abcdefghijklmnopqrs") + "\n")


def with_ad_plan(gates: dict, deck_dir) -> dict:
    d = gates.get("design_plan")
    if not isinstance(d, dict) or d.get("waived") or "plan_file" in d:
        return gates
    scratch = Path(deck_dir).parent / (Path(deck_dir).name + "-scratch")
    scratch.mkdir(exist_ok=True)
    p = scratch / "design-plan.md"
    p.write_text(AD_PLAN, encoding="utf-8")
    pf = {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "dispatched": True,
          "grounds": {"single": "template-locked", "why": "CI fixture"}}
    return dict(gates, design_plan=dict(d, plan_file=pf))
