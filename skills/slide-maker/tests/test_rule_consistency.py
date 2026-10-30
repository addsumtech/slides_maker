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

# ─────────────────────────────────────────────── A2 · one fan-out threshold, owned by the reference
ldo = read("references/large-deck-orchestration.md")
_rule = "\n".join(l for l in ldo.split("## ")[0].splitlines() if not l.startswith(">"))   # the rule, not its history
check("~9" not in _rule and "9+" not in _rule,
      "large-deck-orchestration.md no longer states the stale ~9-slide build threshold")
check("~6 content slides" in _rule and "owns the build fan-out threshold" in _rule,
      "large-deck-orchestration.md states — and owns — the current ~6-content-slide threshold")
check(">= 7" in read("scripts/render_deck.py") and "len(expected_slides) >= 7" in read("scripts/codex_delivery_gate.py"),
      "both gates still fire at 7+ slides (6 content slides + the cover) — the number the reference documents")
check("7+" in ldo.split("## ")[0], "the reference says what the gates count (7+ slides including the cover)")
_scale = SK[SK.find("**Scaling up — section fan-out.**"):][:1500]
check("large-deck-orchestration.md" in _scale,
      "SKILL.md 'Scaling up' points at the reference that owns the number")
check("from ~9 slides the BUILD fans out" not in read("references/critic-panel.md"),
      "critic-panel.md does not restate the stale ~9 build threshold")

# ─────────────────────────────────────────────── A6 · documented build scripts end with the STRICT lint
import sigs  # noqa: E402

check("lint_layout(prs, strict=True)" in sigs.PREAMBLE,
      "sigs.py's printed scaffold preamble tells a build script to end with dk.lint_layout(prs, strict=True)")
vld = read("references/visual-languages.md")
blocks = re.findall(r"```python\n(.*?)```", vld, re.S)
_saving = [b for b in blocks if "prs.save(" in b]
check(_saving, "visual-languages.md carries build examples that save a deck")
for b in _saving:
    lint_at = b.find("lint_layout(prs, strict=True)")
    check(0 <= lint_at < b.find("prs.save("),
          "visual-languages.md example calls dk.lint_layout(prs, strict=True) BEFORE prs.save: {!r}"
          .format(b.strip().splitlines()[-1][:60]))
check("`dk.lint_layout(prs)` at the end of" not in SK,
      "SKILL.md Step 5 does not describe the build-time gate as the non-blocking lint_layout(prs)")
check("`deckkit.lint_layout(prs)` at BUILD time" not in read("references/design-principles.md"),
      "design-principles.md names the strict build-time gate, not the non-blocking call")
# …and the editorial example still BUILDS under strict mode (a documented example that raises would teach
# the reader to switch strict off — the exact thing this fixes).
_ed = next((b for b in _saving if "repair-cafe.pptx" in b), None)
if _ed is not None:
    td = Path(tempfile.mkdtemp(prefix="vl-strict-"))
    script = td / "build_repair-cafe.py"
    script.write_text("\n".join(l[3:] if l.startswith("   ") else l for l in _ed.splitlines()), encoding="utf-8")
    env = dict(os.environ, SKILL=str(SKILL))
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=str(td), env=env)
    check(r.returncode == 0 and (td / "repair-cafe.pptx").exists(),
          "the editorial worked example builds and saves under lint_layout(strict=True) (exit {}; {})"
          .format(r.returncode, (r.stderr or r.stdout).strip()[-300:]))
else:
    check(False, "the editorial repair-cafe example is in visual-languages.md")


for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
if bad:
    print("[test_rule_consistency] FAILED: {} problem(s)".format(len(bad)))
    sys.exit(1)
print("[test_rule_consistency] ok")
