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


# ── Task 3: close · proposals · accept · reject · forget ─────────────────────────────────────────
def props(b):
    code, out, err = b.run("proposals", "--format", "json")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        fails.append("proposals --format json did not print JSON: " + out + err)
        return []


code, out, err = Box().run("note", "--kind", "requirement", "--key", "habits", "--quote",
                           "always notes", "--deck", "a", "--direction", "require")
check(code == 1, "a requirement on a PROFILE key was accepted (profile keys take profile-fact)")

b = Box()
note(b, deck="deck-a")
note(b, deck="deck-a", quote="还是太素")
check(props(b) == [], "two notes in ONE deck proposed a standing preference")
note(b, deck="deck-b", quote="颜色再多一点")
p = props(b)
dial = [x for x in p if x["target"] == "dial" and x["key"] == "colour"]
check(len(dial) == 1 and sorted(dial[0]["decks"]) == ["deck-a", "deck-b"]
      and dial[0]["needs_confirm"] is False,
      "the same key+direction in two decks did not propose one dial: {}".format(p))

b = Box()
note(b, "--standing", deck="deck-a", key="numerals", direction="require",
     quote="digits must always line up")
p = props(b)
check(any(x["target"] == "dial" and x["key"] == "numerals" for x in p),
      "a standing note in one deck did not propose")
pid = [x for x in p if x["key"] == "numerals"][0]["id"]
code, out, err = b.run("accept", pid)
check(code == 1 and b.taste() == "", "a dial accept without --position wrote something")
code, out, err = b.run("accept", pid, "--position", "lining figures always")
check(code == 0 and "| numerals | lining figures always |" in b.taste()
      and "digits must always line up" in b.taste()
      and "recorded to your taste profile: numerals — lining figures always" in out,
      "a dial accept did not write the evidenced row + FYI line:\n" + out + err + b.taste())
check(not any(x["id"] == pid for x in props(b)), "an accepted proposal was proposed again")
note(b, "--standing", deck="deck-c", key="numerals", direction="avoid",
     quote="actually old-style digits are fine always")
p = [x for x in props(b) if x["key"] == "numerals"]
check(len(p) == 1 and p[0]["direction"] == "avoid" and "UPDATE" in p[0]["reason"],
      "an opposite later direction did not propose an UPDATE: {}".format(p))
b.run("accept", p[0]["id"], "--position", "old-style allowed")
check(b.taste().count("| numerals |") == 1 and "old-style allowed" in b.taste(),
      "the update did not replace the row (two rows argue about one dimension)")

b = Box()
code, out, err = note(b, "--value", "MRI reconstruction researcher", kind="profile-fact",
                      key="role", direction=None, quote="我是做MRI重建的")
p = props(b)
check(len(p) == 1 and p[0]["target"] == "profile" and p[0]["needs_confirm"] is True,
      "a profile fact did not propose a confirm-first PROFILE line: {}".format(p))
code, out, err = b.run("accept", p[0]["id"])
check(code == 1 and b.taste() == "" and "ask the user" in (out + err).lower(),
      "a PROFILE accept without --confirmed was not refused with the question to ask")
code, out, err = b.run("accept", p[0]["id"], "--confirmed")
check(code == 0 and "- role: MRI reconstruction researcher" in b.taste()
      and b.taste().index("## PROFILE") >= 0, "a confirmed PROFILE accept did not write the line")
code, out, err = b.run("forget", "profile:role")
check(code == 0 and "role:" not in b.taste(), "forget profile:role did not remove the line")

b = Box()
for d in ("deck-a", "deck-b"):
    note(b, deck=d, key="length", direction="less", quote="太长了，压缩一点")
p = [x for x in props(b) if x["target"] == "rule"]
check(len(p) == 1 and p[0]["needs_confirm"], "a recurring content requirement did not propose a "
      "confirm-first ledger rule: {}".format(p))
code, out, err = b.run("accept", p[0]["id"], "--confirmed")
check(code == 1, "a rule accept without --rule was accepted")
code, out, err = b.run("accept", p[0]["id"], "--confirmed", "--rule",
                       "keep decks short: cut to the core claims before adding slides")
led = json.loads(b.ledger.read_text())["entries"] if b.ledger.exists() else []
check(code == 0 and len(led) == 1 and led[0]["id"] == "length-less"
      and led[0]["binds_at"] == "content" and led[0]["quote"] == "太长了，压缩一点",
      "a confirmed rule accept did not land in the ledger: {} {}".format(led, out + err))

b = Box()
for d in ("deck-a", "deck-b"):
    note(b, deck=d, key="motion", direction="less", quote="no flying text")
pid = props(b)[0]["id"]
b.run("reject", pid)
check(props(b) == [], "a rejected proposal came straight back")
note(b, deck="deck-c", key="motion", direction="less", quote="still too much motion")
check(any(x["id"] == pid for x in props(b)), "a rejected proposal did not return on a NEW deck")


def deck_dir(b, name, applied, skipped, codex=False):
    d = b.td / name
    d.mkdir()
    rows = [{"id": i, "applied": True} for i in applied] + [
        {"id": i, "applied": False, "why_not": "does not bind on this deck at all"} for i in skipped]
    rec = {"design": {"taste_applied": rows}} if codex else {"design_plan": {"taste_applied": rows}}
    (d / (".codex-deck-evidence.json" if codex else ".deck-gates.json")).write_text(json.dumps(rec))
    return d


b = Box()
b.ledger.write_text(json.dumps([ledger_entry(1, "design"), ledger_entry(2, "design")]))
note(b, deck="deck-1")
code, out, err = b.run("close", str(deck_dir(b, "deck-1", ["rule-1"], ["rule-2"])))
rec = [o for o in b.obs() if o["kind"] == "applied-record"]
check(code == 0 and len(rec) == 1 and rec[0]["skipped"] == ["rule-2"]
      and "1 observation" in out, "close did not snapshot taste_applied + report the count:\n" + out)
b.run("close", str(b.td / "deck-1"))
check(len([o for o in b.obs() if o["kind"] == "applied-record"]) == 1,
      "closing the same deck twice logged two records (would fake 'consecutive' skips)")
code, out, err = b.run("close", str(deck_dir(b, "deck-2", [], ["rule-2"], codex=True)))
check(code == 0 and [o for o in b.obs() if o["kind"] == "applied-record"][-1]["skipped"] == ["rule-2"],
      "close did not read the Codex `design` record")
check(not any(x["target"] == "review" for x in props(b)), "two skips already proposed a review")
b.run("close", str(deck_dir(b, "deck-3", ["rule-1"], ["rule-2"])))
rv = [x for x in props(b) if x["target"] == "review"]
check(len(rv) == 1 and rv[0]["key"] == "rule:rule-2",
      "three consecutive skips did not propose a review of that rule: {}".format(rv))

b = Box()
(b.reg / "taste.md").write_text(FULL_TASTE, encoding="utf-8")
b.today = "2027-09-01"
rv = [x["key"] for x in props(b) if x["target"] == "review"]
check("dial:colour" in rv and "profile:role" in rv,
      "lines with evidence older than 365 days were not proposed for review: {}".format(rv))
note(b, deck="deck-z", key="colour", direction="more", quote="colour still matters")
rv = [x["key"] for x in props(b) if x["target"] == "review"]
check("dial:colour" not in rv, "a fresh observation on that key did not re-confirm the dial")
pid = [x for x in props(b) if x["key"] == "profile:role"][0]["id"]
b.run("reject", pid)
check(not any(x["id"] == pid for x in props(b)), "a kept (rejected) stale review came straight back")
b.today = "2028-09-02"
check(any(x["id"] == pid for x in props(b)), "a kept stale review never came back a year later")


# ── Task 4: external references ──────────────────────────────────────────────────────────────────
b = Box()
(b.reg / "taste.md").write_text("# taste.md\n\n## PROFILE\n"
                                "- organization: LUMC (Leiden) — stated · a · 2026-11-01\n"
                                "- venues: ISMRM, ESMRMB · RSNA — stated · a · 2026-11-01\n",
                                encoding="utf-8")
code, out, err = b.run("recall", "--step", "content")
research = [l for l in out.splitlines() if l.startswith("NEXT: research")]
check(len(research) == 2 and '"LUMC"' in research[0],
      "missing refs did not ask for research (≤2 lines, org first):\n" + out)
code, out, err = b.run("ref", "add", "--key", "org:LUMC", "--url",
                       "https://www.lumc.nl/huisstijl", "--facts", "primary blue #001158; Frutiger")
check(code == 0, "a valid ref was refused: " + out + err)
code, out, err = b.run("recall", "--step", "design")
check("#001158" in out and "lumc.nl" in out and '"LUMC"' not in out,
      "a fresh ref did not replace the research line with its facts:\n" + out)
code, out, err = b.run("ref", "add", "--key", "venue:ISMRM-2027", "--url", "https://ismrm.org/27",
                       "--facts", "power pitch 3 min, 16:9")
code, out, err = b.run("recall", "--step", "content", "--venue", "ISMRM-2027")
check("power pitch 3 min" in out, "--venue did not match its cached ref:\n" + out)
code, out, err = b.run("ref", "add", "--key", "org:LUMC", "--url", "https://www.lumc.nl/v2",
                       "--facts", "primary blue #001E5A")
code, out, err = b.run("ref", "list")
check(out.count("org:LUMC") == 1 and "#001E5A" in out and "#001158" not in out,
      "a newer ref for the same key did not replace the older:\n" + out)
b.today = "2027-06-30"
code, out, err = b.run("ref", "list", "--expired")
check("org:LUMC" in out and "ISMRM-2027" not in out,
      "TTL expiry wrong (org 180 days, venue 365):\n" + out)
code, out, err = b.run("recall", "--step", "content")
check('research "LUMC"' in out, "an expired ref did not ask for re-research:\n" + out)
for bad in (["--url", "https://x.org/?token=abc", "--facts", "x"],
            ["--url", "ftp://x.org/a", "--facts", "x"],
            ["--url", "none", "--facts", "x"]):
    code, out, err = b.run("ref", "add", "--key", "org:X", *bad)
    check(code == 1, "a bad ref was accepted: {}".format(bad))
code, out, err = b.run("ref", "add", "--key", "org:Y", "--url", "none", "--facts", "unknown")
check(code == 0, "an honest `unknown` ref was refused: " + err)
code, out, err = b.run("ref", "add", "--key", "LUMC", "--url", "https://a.b", "--facts", "x")
check(code == 1, "a ref key without org:/venue: was accepted")


# ── report ───────────────────────────────────────────────────────────────────────────────────────
for f in fails:
    print("FAIL: " + f)
print("{} passed, {} failed".format(passed, len(fails)))
sys.exit(1 if fails else 0)
