#!/usr/bin/env python3
"""memory.py — the one memory entry point any agent runs per step.

Covers the properties that decide whether memory helps or hurts: a fresh install is asked nothing,
the user's words are kept verbatim in any language, nothing sensitive is stored, recurrence (not one
remark) is what proposes a standing preference, and nothing that binds future decks is written
without the consent tier it needs.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
MEM = SCRIPTS / "memory.py"
sys.path.insert(0, str(SCRIPTS))

fails: list[str] = []
passed = 0


def check(cond, msg):
    global passed
    if cond:
        passed += 1
    else:
        fails.append(msg)


class Box:
    """One fresh registry + ledger per scenario."""

    def __init__(self):
        self.td = Path(tempfile.mkdtemp(prefix="mem-test-"))
        self.reg = self.td / "registry"
        self.reg.mkdir()
        self.ledger = self.td / "ledger.json"
        self.today = "2026-11-25"

    def env(self):
        e = dict(os.environ)
        e["SLIDE_MAKER_REGISTRY"] = str(self.reg)
        e["SLIDE_MAKER_TASTE_LEDGER"] = str(self.ledger)
        e["SLIDE_MAKER_TODAY"] = self.today
        return e

    def run(self, *args):
        r = subprocess.run([sys.executable, str(MEM), *args], capture_output=True, text=True,
                           env=self.env())
        return r.returncode, r.stdout, r.stderr

    def obs(self):
        p = self.reg / "observations.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    def taste(self):
        p = self.reg / "taste.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""


def note(b, *extra, deck="deck-a", kind="requirement", key="colour", quote="太素了，颜色放在数据上",
         direction="more"):
    args = ["note", "--kind", kind, "--key", key, "--quote", quote, "--deck", deck]
    if direction:
        args += ["--direction", direction]
    return b.run(*args, *extra)


# ── Task 1: store, vocabulary, privacy, note ─────────────────────────────────────────────────────
r = subprocess.run([sys.executable, str(MEM), "--selftest"], capture_output=True, text=True)
check(r.returncode == 0, "memory.py --selftest failed:\n" + r.stdout + r.stderr)

b = Box()
code, out, err = note(b)
check(code == 0, "a valid Chinese note was refused: " + out + err)
o = b.obs()
check(len(o) == 1 and o[0]["quote"] == "太素了，颜色放在数据上" and o[0]["date"] == "2026-11-25",
      "the note was not stored verbatim with today's date: {}".format(o))

code, out, err = note(b, key="sparkle")
check(code == 1 and "colour" in (out + err), "an unknown key was not refused with the vocabulary")
code, out, err = note(b, direction=None)
check(code == 1, "a requirement without --direction was accepted")
code, out, err = note(b, direction="bigger")
check(code == 1, "a direction outside more/less/require/avoid was accepted")
code, out, err = note(b, kind="profile-fact", key="role", direction=None, quote="我是做MRI重建的")
check(code == 1, "a profile-fact without --value was accepted")
code, out, err = note(b, "--value", "MRI reconstruction researcher", kind="profile-fact",
                      key="role", direction=None, quote="我是做MRI重建的")
check(code == 0, "a valid profile-fact was refused: " + out + err)
code, out, err = note(b, kind="profile-fact", key="colour", direction=None, quote="x y z w",
                      )
check(code == 1, "a profile-fact on a non-profile key was accepted")
code, out, err = b.run("note", "--kind", "applied-record", "--key", "colour", "--quote", "abcd",
                       "--deck", "d")
check(code == 1, "applied-record was writable from the CLI (only `close` may write it)")

n_before = len(b.obs())
for bad in ("mail me at a@b.nl", "call +31 6 1234 5678", "card 4111 1111 1111 1111",
            "see https://u:p@x.org/a", "https://x.org/?token=abc123", "I live at 12 Baker Street",
            "postcode 2333 ZA"):
    code, out, err = note(b, quote=bad)
    check(code == 1, "PII was accepted: {!r}".format(bad))
check(len(b.obs()) == n_before, "a refused note still wrote something")
for ok in ("ISMRM 2027 talk wants more colour", "deadline 2026-11-25, more colour"):
    code, out, err = note(b, quote=ok)
    check(code == 0, "a date/venue year tripped the PII rule: {!r} {}".format(ok, out + err))

for bad in ("I have diabetes", "我的签证状态是", "salary band 5"):
    code, out, err = note(b, "--value", bad, kind="profile-fact", key="habits", direction=None,
                          quote=bad)
    check(code == 1, "a sensitive profile fact was accepted: {!r}".format(bad))
code, out, err = note(b, quote="the disease figure needs more colour")
check(code == 0, "a design quote about a medical deck was topic-filtered: " + out + err)

code, out, err = note(b, "--standing", quote="Altijd meer kleur graag")
check(code == 0 and b.obs()[-1].get("standing") is True, "--standing was not stored")
code, out, err = note(b, quote="以后都要用这个配色")
check(b.obs()[-1].get("standing") is True, "a Chinese standing word did not mark standing")

p = b.reg / "observations.jsonl"
with p.open("a", encoding="utf-8") as fh:
    fh.write("{not json\n")
code, out, err = b.run("keys")
check(code == 0 and "colour" in out and "role" in out, "`keys` did not print the vocabulary")
code, out, err = note(b)
check(code == 0 and "skipp" in err.lower(), "a corrupt log line was not skipped with a warning")

b2 = Box()
for i in range(305):
    note(b2, deck="d{}".format(i))
check(len(b2.obs()) == 300, "the log was not pruned to 300 lines: {}".format(len(b2.obs())))


# ── report ───────────────────────────────────────────────────────────────────────────────────────
for f in fails:
    print("FAIL: " + f)
print("{} passed, {} failed".format(passed, len(fails)))
sys.exit(1 if fails else 0)
