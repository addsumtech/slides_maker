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
import memory as _m  # noqa: E402
_saved = {k: os.environ.get(k) for k in ("SLIDE_MAKER_REGISTRY", "SLIDE_MAKER_TASTE_LEDGER")}
os.environ.update({"SLIDE_MAKER_REGISTRY": str(b2.reg), "SLIDE_MAKER_TASTE_LEDGER": str(b2.ledger)})
for i in range(305):
    _m.append_obs({"date": "2026-11-25", "deck": "d{}".format(i), "kind": "requirement",
                   "key": "colour", "direction": "more", "quote": "more colour"})
os.environ.update({k: v for k, v in _saved.items() if v is not None})
check(len(b2.obs()) == 300 and b2.obs()[0]["deck"] == "d5",
      "the log was not pruned to the newest 300 lines: {}".format(len(b2.obs())))


# ── Task 2: taste.md sections + recall ───────────────────────────────────────────────────────────
import memory as M  # noqa: E402

FULL_TASTE = """# taste.md — Tester's slide taste (portable · edit or delete freely)

Some prose the user wrote by hand. Keep me.

## PROFILE  (≤8 lines)
- role: MRI reconstruction researcher — "我是做 MRI 重建的" · cine-mri · 2026-06-14
- field: medical imaging — stated in interview · cine-mri · 2026-06-14
- organization: LUMC — stated in interview · cine-mri · 2026-06-14
- audiences: lab meeting, conference — stated · cine-mri · 2026-06-14
- venues: ISMRM — stated · cine-mri · 2026-06-14
- languages: zh conversation, en slides — stated · cine-mri · 2026-06-14
- brand: registry template lkeb-lumc — stated · cine-mri · 2026-06-14
- habits: always speaker notes — stated · cine-mri · 2026-06-14

## DIALS  (≤10 rows)
| dimension | position | evidence (deck · date · the user's verbatim words) |
|---|---|---|
| colour | vivid content, quiet chrome | cine-mri · 2026-06-14 · "太素了" |
| density | balanced \\| never empty | a · 2026-06-15 · "too empty" |
| boldness | balanced+ | b · 2026-06-16 · "bolder" |
| icons | SVG family on categories | c · 2026-07-11 · "svg icon should appear" |
| numerals | lining figures always | d · 2026-07-12 · "忽上忽下" |
| type | sans body | e · 2026-07-13 · "font" |
| motion | appear builds only | f · 2026-07-14 · "no flying" |
| imagery | real domain photos | g · 2026-07-15 · "real images" |
| architecture | rotate layouts | h · 2026-07-16 · "each page same" |
| background | one canvas system | i · 2026-07-17 · "lone slide" |

*(an italic note the user kept)*

## NO-GOs  (≤5 lines)
- No card grids — a · 2026-06-29
- No bottom strip on every page — b · 2026-07-11
- No Georgia digits — c · 2026-07-12
- No stock blue — d · 2026-07-13
- No lone background — e · 2026-07-14

## LOOK HISTORY  (most recent 10 lines only)
| date | deck | preset/look | canvas value | signature motif |
|---|---|---|---|---|
| 2026-10-09 | muse-pitch | approval trail | #FBFAF7 | progress rail |
| 2026-10-22 | caselip | journal | #FBFAF6 | ledger rule |
"""


def ledger_entry(i, binds):
    return {"id": "rule-{}".format(i), "quote": "the user said {}".format(i),
            "rule": "do the thing number {} on every deck".format(i), "binds_at": binds,
            "learned_from": {"deck": "deck-{}".format(i), "date": "2026-09-0{}".format(i)},
            "retired_by": ""}


b = Box()
code, out, err = b.run("recall", "--step", "interview")
lines = out.strip().splitlines()
check(code == 0 and lines[0] == "memory: none on file" and len(lines) == 2
      and lines[1].startswith("NEXT:") and " note " in lines[1],
      "an empty store did not recall as exactly `none on file` + the note line:\n" + out + err)

b = Box()
(b.reg / "taste.md").write_text(FULL_TASTE, encoding="utf-8")
binds = ["design", "design", "design", "content", "content", "build"]
b.ledger.write_text(json.dumps([ledger_entry(i + 1, x) for i, x in enumerate(binds)]),
                    encoding="utf-8")
code, out, err = b.run("recall", "--step", "design")
check(code == 0, "design recall failed: " + err)
check(len(out.strip().splitlines()) <= 50,
      "design recall over 50 lines: {}".format(len(out.splitlines())))
check(all("rule-{}".format(i) in out for i in range(1, 7)),
      "design recall did not list EVERY active rule (the gate requires all):\n" + out)
check("taste_applied" in out, "design recall did not say to record taste_applied")
check("lining figures always" in out and "No stock blue" in out and "caselip" in out
      and "MRI reconstruction researcher" in out, "design recall dropped a taste section:\n" + out)
check("balanced | never empty" in out, "an escaped \\| leaked into the recall display")
check("muse-pitch" not in out, "design recall printed more than the LAST look-history line")
code, out, err = b.run("recall", "--step", "content")
check("rule-4" in out and "rule-5" in out and "rule-1" not in out and "rule-6" not in out,
      "content recall did not filter rules by binds_at:\n" + out)
check("lining figures always" not in out, "content recall printed design dials")
code, out, err = b.run("recall", "--step", "build", "--format", "json")
try:
    d = json.loads(out)
    check([r["id"] for r in d["rules"]] == ["rule-6"] and isinstance(d["next"], list),
          "build recall json has the wrong rules: {}".format(d.get("rules")))
except json.JSONDecodeError:
    check(False, "recall --format json did not print JSON:\n" + out)
code, out, err = b.run("recall", "--step", "handoff")
check(" close " in out, "handoff recall did not name the close command:\n" + out)

# edit_preserves_other_bytes
new = M.upsert_line(FULL_TASTE, "PROFILE", "role", "- role: PhD researcher — x · y · 2026-11-25",
                    cap=8)
a_lines, b_lines = FULL_TASTE.splitlines(), new.splitlines()
diff = [i for i, (x, y) in enumerate(zip(a_lines, b_lines)) if x != y]
check(len(a_lines) == len(b_lines) and len(diff) == 1 and "PhD researcher" in b_lines[diff[0]],
      "replacing one PROFILE line changed {} lines".format(len(diff)))
new = M.upsert_line(FULL_TASTE, "DIALS", "density", "| density | airy | z · 2026-11-25 · \"q\" |",
                    cap=10)
check(new.count("airy") == 1 and "never empty" not in new and new.count("| density |") == 1,
      "a DIALS update did not replace the row in place")
try:
    M.upsert_line(FULL_TASTE, "PROFILE", "extra", "- extra: x", cap=8)
    check(False, "a 9th PROFILE line was accepted")
except M.CapFull:
    check(True, "")
no_profile = FULL_TASTE.split("## PROFILE")[0] + "## DIALS" + FULL_TASTE.split("## DIALS")[1]
new = M.upsert_line(no_profile, "PROFILE", "role", "- role: tester — q · d · 2026-11-25", cap=8)
check(new.index("## PROFILE") < new.index("## DIALS") and "Keep me." in new
      and all(l in new.splitlines() for l in no_profile.splitlines()),
      "creating PROFILE did not insert it above DIALS while keeping every other line")
created = M.upsert_line("", "NO-GOs", None, "- No x — d · 2026-11-25", cap=5)
check(created.startswith("# taste.md") and "## NO-GOs" in created and "- No x" in created,
      "a first write did not create a taste.md skeleton")
txt, gone = M.remove_line(FULL_TASTE, "PROFILE", "venues")
check(gone and "venues:" not in txt and len(txt.splitlines()) == len(a_lines) - 1,
      "remove_line did not remove exactly one line")
check(M.read_sections(FULL_TASTE)["DIALS"][1].startswith("| density"),
      "read_sections kept the header/separator rows")


# ── report ───────────────────────────────────────────────────────────────────────────────────────
for f in fails:
    print("FAIL: " + f)
print("{} passed, {} failed".format(passed, len(fails)))
sys.exit(1 if fails else 0)
