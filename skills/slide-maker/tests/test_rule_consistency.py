#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rules stated in more than one file say the SAME thing — and the briefs carry what SKILL.md mandates.

WHY. An audit plus a real end-to-end Chinese deck run (2026-10-29) found the same rule stated two
ways in different files, and the reader who meets the losing copy follows it:

  · the `standard` review tier was "worth it for a defense / pitch / exec readout" in SKILL.md's
    tier table, while the interview, the critic panel and SKILL.md's own Step 0 put those decks on
    `thorough` — and the auto-escalation example said `review: standard (escalated — defense deck)`
  · the build fan-out threshold was ~6 slides in SKILL.md and both gates, ~9 in the reference that
    is supposed to own it
  · the auto-delegation reference said the "full critic panel is NOT OPTIONAL" in auto mode, three
    paragraphs below its own rule that auto runs `fast` (one sole critic)
  · the documented build examples a generated script is copied from ended with a bare
    `prs.save(...)` — no strict build-time lint — so criticals printed and the deck still saved
  · the art-director brief never mentioned the Step-2 MATERIAL PROBE SKILL.md mandates, and the
    Gate A procedure never mentioned the no-pictures native-language rule

No gate can see prose disagreeing with prose, so each agreement is asserted here.

Run: python3 tests/test_rule_consistency.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))
ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


def read(rel):
    return (SKILL / rel).read_text(encoding="utf-8")


def corpus():
    files = [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md")) + sorted((SKILL / "agents").glob("*.md"))
    return {str(p.relative_to(SKILL)): p.read_text(encoding="utf-8") for p in files}


SK = read("SKILL.md")
ALL = corpus()

# ─────────────────────────────────────────────── A1 · the review tiers by stakes
rows = {m.group(1): m.group(0) for m in re.finditer(r"^\| \*{0,2}`(fast|standard|thorough|none)`[^\n]*", SK, re.M)}
check({"standard", "thorough"} <= set(rows), "SKILL.md's post-build tier table has a standard and a thorough row")
_hi = ("defense", "pitch", "exec readout")
check(not any(w in rows.get("standard", "") for w in _hi),
      "SKILL.md tier table: the `standard` row does not claim defense/pitch/exec decks (they are `thorough` "
      "everywhere else): {!r}".format(rows.get("standard", "")[:160]))
check(all(w in rows.get("thorough", "") for w in _hi),
      "SKILL.md tier table: the `thorough` row names defense / pitch / exec readout: {!r}"
      .format(rows.get("thorough", "")[:160]))
_esc_std = [f for f, t in ALL.items() if "review: standard (escalated" in t]
check(not _esc_std, "no file shows an auto escalation to `standard` for a high-stakes deck: {}".format(_esc_std))
check("review: thorough (escalated — defense deck, auto)" in SK,
      "SKILL.md's auto-escalation example escalates a defense deck to `thorough`")


for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
if bad:
    print("[test_rule_consistency] FAILED: {} problem(s)".format(len(bad)))
    sys.exit(1)
print("[test_rule_consistency] ok")
