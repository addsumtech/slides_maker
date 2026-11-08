#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_plan_record.py density rules — a density waiver is the USER's text-heavy choice, never the author's escape.

Measured 2026-11-07/08: twelve real runs of the current skill shipped presented decks at a median of
83–168 words a slide by writing `"density": {"waived": …}` in their own words, while the older skill's
runs sat at 54–66 and won a blind design comparison. Dense pages force small type and leave no room
for a hero, which is what the reviewers faulted. What this suite holds the rule to:

  · a waiver counts only when the recorded density is text-heavy AND the user chose it (a picks row
    marked `delegated` is the author's choice, not the user's);
  · balanced / diagram-heavy decks get no free-text waiver;
  · a very sparse deck gets a note, never a block.

Run:  python3 tests/test_density_choice.py
"""
import _hermetic  # noqa: F401,E402
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import design_plan_record as _DPR  # noqa: E402


class DC:                                   # the density rules, formerly density_choice.py
    waiver_allowed = staticmethod(_DPR.density_waiver_allowed)
    sparse_note = staticmethod(_DPR.density_sparse_note)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  %s" % (detail,)))


def g(density, source=None):
    iv = {"density": density}
    if source:
        iv["picks"] = [{"axis": "density", "source": source, "value": density}]
    return {"interview": iv}


print("── who chose the density")
check("text-heavy stated by the user: waiver counts", DC.waiver_allowed(g("text-heavy", "stated"))[0])
check("text-heavy with no picks row (supervised run): waiver counts", DC.waiver_allowed(g("Text-heavy"))[0])
check("Chinese 文字为主 stated: waiver counts", DC.waiver_allowed(g("文字为主", "stated"))[0])
ok, why = DC.waiver_allowed(g("text-heavy", "delegated"))
check("text-heavy DELEGATED: waiver refused, and says it was the author's pick", not ok and "delegated" in why, why)
ok, why = DC.waiver_allowed(g("balanced", "stated"))
check("balanced: waiver refused, and says to cut to notes or split", not ok and "notes" in why, why)
check("diagram-heavy: waiver refused", not DC.waiver_allowed(g("diagram-heavy"))[0])
check("no density recorded: waiver refused", not DC.waiver_allowed({})[0])
check("图文均衡: waiver refused", not DC.waiver_allowed(g("图文均衡", "stated"))[0])

print("── too sparse is a note")
check("median 3 words over 8 slides: a note", "sparse" in (DC.sparse_note(3, 8) or ""))
check("median 25 words: no note", DC.sparse_note(25, 8) is None)
check("a 2-slide deck is never called sparse", DC.sparse_note(2, 2) is None)

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
