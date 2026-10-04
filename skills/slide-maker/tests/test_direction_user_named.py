#!/usr/bin/env python3
"""Codex gate: a look the USER named (a visual language, by name) is recorded as design.direction branch "user-named" — the
look and the user's own words — instead of staging four preview directions nobody asked for. direction_gate already had
the carve ("n/a - user supplied the look"); design.direction had none, so a docs-only agent whose user said "editorial"
stayed BLOCKED on "clean design direction needs four named preview directions" (restricted run, 2026-10-04)."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import codex_delivery_gate as cdg

root = Path(tempfile.mkdtemp())


def direction_errors(design):
    errs: list[str] = []
    try:
        cdg.check_design({"design": design}, root, {1}, "0" * 64, errs)
    except Exception as e:                         # the rest of a minimal design may be incomplete; that is not this test
        errs.append("raised " + repr(e))
    return [e for e in errs if e.startswith("design.direction") or "preview directions" in e or "direction preview" in e
            or "user-named" in e or "user_words" in e or e.startswith("raised")]


ok = {"visual_language": "editorial", "direction_gate": "n/a - user supplied the look (editorial, by name)",
      "direction": {"branch": "user-named", "look": "visual language: editorial",
                    "user_words": "用 editorial 那种杂志风，底色按我最近的 deck 自动选"}}
e = direction_errors(ok)
check(not e, "a user-named visual language passes design.direction without four directions or a preview: {}".format(e))

bad = {**ok, "direction": {"branch": "user-named", "look": "visual language: editorial"}}
e = direction_errors(bad)
check(any("user_words" in x for x in e), "user-named without the user's own words is refused, naming user_words: {}".format(e))

bad = {**ok, "direction": {"branch": "user-named", "look": "visual language: editorial", "user_words": "ok"}}
e = direction_errors(bad)
check(any("user_words" in x for x in e), "a two-letter 'ok' is not the user's words: {}".format(e))

bad = {**ok, "direction_gate": {"candidates": "directions.json", "picked": "A"}}
e = direction_errors(bad)
check(any("user-named" in x and "direction_gate" in x for x in e),
      "user-named while direction_gate claims a competition is a contradiction: {}".format(e))

bad = {**ok, "direction": {**ok["direction"], "look": "a bold swiss grid"}}
e = direction_errors(bad)
check(any("user-named" in x and "editorial" in x for x in e),
      "a user-named look that does not name the recorded visual language is refused: {}".format(e))

e = direction_errors({**ok, "direction": {"branch": "made-up"}})
check(any("branch is invalid" in x for x in e), "an unknown branch is still refused: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_direction_user_named] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
