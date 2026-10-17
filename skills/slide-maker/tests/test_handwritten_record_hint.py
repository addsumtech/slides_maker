#!/usr/bin/env python3
"""A hand-typed record gets the FIELD NAMES wrong, and the gate can see that it was hand-typed.

🔴 MEASURED, twice in one session. A run wrote the `.deck-gates.json` composition block by hand
and used `name` where the contract says `label` — one round-trip. It then wrote the `why` clause
with abbreviations ("A / B / C") and the gate rejected it for not naming what was compared —
another round-trip. Both were shaped correctly in the template `deck_gates.py init` writes, and
the skill has said "write the record with deck_gates.py, not by hand" in prose the whole time.

Prose is not a check. This one prints beside the findings, at the moment the mistake surfaces, and
never blocks — the record may legitimately drop a block (a no-source deck writes no open ledger),
so it fires on a COUNT of absent `init`-always-writes blocks rather than on any single key.

Note what this file does NOT claim: the shared scaffold was audited the same way as the Codex one
(fill it, run the real gate, look for fields it demands that the template never showed) and came
back COMPLETE — `label`, `picked` and `why` are all in it, with the "name the versions you
compared" instruction included. The defect was never a missing field; it was that nothing stopped
an author from bypassing the template.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deck_gates as dg  # noqa: E402

fails: list[str] = []
HINT = "does not look like it came from"


def check(cond, msg):
    if not cond:
        fails.append(msg)


def run_check(d: Path) -> str:
    r = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "check", str(d)],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


with tempfile.TemporaryDirectory() as _td:
    td = Path(_td)

    # ── 🔴 a hand-typed record is recognised ─────────────────────────────────────────────────────
    hand = td / "hand"
    hand.mkdir()
    (hand / ".deck-gates.json").write_text(json.dumps(
        {"content": {"slides": [{"slide": 1, "role": "cover", "takeaway": "x"}]},
         "design_plan": {"boldness": "balanced+"}}), encoding="utf-8")
    out = run_check(hand)
    check(HINT in out,
          "a record missing every block `init` always writes drew no hint — the failure mode this "
          "exists for is exactly an author who never ran init")
    check("label" in out, "the hint does not name the measured mistake (`name` for `label`), so it "
                          "teaches nothing")

    # ── 🔴 and an init-produced record is NOT nagged ─────────────────────────────────────────────
    made = td / "made"
    made.mkdir()
    r = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "init", str(made),
                        "--slides", "6"], capture_output=True, text=True)
    check((made / ".deck-gates.json").exists(),
          "deck_gates.py init did not write a record: {}{}".format(r.stdout, r.stderr))
    out2 = run_check(made)
    check(HINT not in out2,
          "the template's OWN output was accused of being hand-written — a hint that fires on the "
          "correct workflow is noise, and noise is what teaches people to skim gates")

    # ── interview --set first, init second: init KEEPS the answers (iPhone 18 explainer, 2026-10-17) ───
    # `interview --set` on a fresh folder writes a record holding only the interview; `init` then refused
    # ("already exists"), and the way out it named — --force — DISCARDS the answers just recorded.
    early = td / "early"
    early.mkdir()
    subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "interview", str(early),
                    "--set", "language=en", "--set", "density=balanced", "--set", "length=9 slides",
                    "--set", "goal=inform"], capture_output=True, text=True)
    r = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "init", str(early), "--slides", "9"],
                       capture_output=True, text=True)
    rec = json.loads((early / ".deck-gates.json").read_text(encoding="utf-8"))
    iv = rec.get("interview") or {}
    check(r.returncode == 0 and "content" in rec and "design_plan" in rec,
          "init after `interview --set` wrote the full skeleton (exit {}: {})".format(r.returncode, r.stderr.strip()[:120]))
    check(iv.get("language") == "en" and iv.get("length") == "9 slides" and iv.get("goal") == "inform",
          "init after `interview --set` kept the recorded answers ({})".format(
              {k: iv.get(k) for k in ("language", "density", "length", "goal")}))
    r2 = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "init", str(early)],
                        capture_output=True, text=True)
    check(r2.returncode == 2, "a FULL record is still protected: a second init without --force is refused")

    # ── a record that drops ONE block is not accused either ──────────────────────────────────────
    rec = json.loads((made / ".deck-gates.json").read_text(encoding="utf-8"))
    rec.get("content", {}).pop("open_ledger", None)          # legitimate on a no-source deck
    one = td / "one"
    one.mkdir()
    (one / ".deck-gates.json").write_text(json.dumps(rec), encoding="utf-8")
    check(HINT not in run_check(one),
          "dropping a single legitimate block triggered the hint; it must fire on a COUNT, so a "
          "deck with a real exception is not nagged")

# ── the predicate itself, both directions ───────────────────────────────────────────────────────
check(not dg._looks_hand_written({}), "an empty/unreadable record must not be accused")
check(not dg._looks_hand_written(None), "a None record must not raise or be accused")
full = {t: {k: 1} for t, k in dg._INIT_MARKERS}
merged: dict = {}
for t, k in dg._INIT_MARKERS:
    merged.setdefault(t, {})[k] = 1
check(not dg._looks_hand_written(merged),
      "a record carrying every marker was called hand-written")
check(dg._looks_hand_written({"design_plan": {}, "content": {}}),
      "a record carrying NO marker was not recognised — the predicate is inert")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_handwritten_record_hint] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
