#!/usr/bin/env python3
"""Auto mode: what the skill decided FOR the user must be recorded, sourced and floored.

The module's `--selftest` covers the contract. This file covers what that cannot: that the check
binds on exactly the decks it should and NO others, that the floor encoding the measured
angle-invention failure cannot be walked around, that every gate path enforces it identically, and
that the reference stating the rule finally has a backstop.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import delegated_picks as dp  # noqa: E402

os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/nonexistent/taste-ledger-for-tests.json"

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


r = subprocess.run([sys.executable, str(SCRIPTS / "delegated_picks.py"), "--selftest"],
                   capture_output=True, text=True)
check(r.returncode == 0, "delegated_picks.py --selftest failed:\n{}{}".format(r.stdout, r.stderr))

BASIS = "the request names a three-day trip and no venue at all"
ALT = "a conference room was plausible; the request says 'send it to me'"


def record(**over):
    picks = []
    for a in dp.AXES:
        if a == "angle":
            picks.append({"axis": a, "source": "genre-default",
                          "value": "the city introduction people actually give"})
        elif a in dp.ALTERNATIVE_REQUIRED:
            picks.append({"axis": a, "source": "delegated", "value": "a real chosen value",
                          "basis": BASIS, "alternative": ALT})
        else:
            picks.append({"axis": a, "source": "delegated", "value": "a real chosen value",
                          "basis": BASIS})
    out = {"picks": picks}
    out.update(over)
    return out


# ── 🔴 SCOPE: it binds where the risk is, and nowhere else ───────────────────────────────────────
# A supervised deck's Step-0 answers were the USER's. Asking it to justify them would be friction
# with no risk behind it — and this skill already carries 69 required fields.
check(not dp.faults(None, auto=False), "a supervised deck was asked for delegated picks")
check(not dp.faults({"language": "English"}, auto=False),
      "a supervised deck with a normal interview block was rejected")
check(dp.faults(None, auto=True), "an auto deck with no picks passed")

# and `auto` is read from the record the gates ALREADY require, so nothing new must be declared
check(dp.is_auto({"content": {"checkpoint": {"mode": "auto"}}}),
      "is_auto missed the shared spelling")
check(dp.is_auto({"design": {"checkpoint": {"mode": "auto"}}}),
      "is_auto missed the CODEX spelling `design.checkpoint` — the runtime this exists for")
check(dp.is_auto({"design_plan": {"checkpoint": {"mode": "auto"}}}),
      "is_auto missed design_plan.checkpoint")
check(not dp.is_auto({"content": {"checkpoint": {"mode": "approved"}}}),
      "is_auto fired on an approved deck — every supervised run would pay for this")
for junk in (None, 7, "str", {}, {"content": 5}, {"content": {"checkpoint": "x"}}):
    check(not dp.is_auto(junk), "is_auto fired on {!r}".format(junk))

# ── 🔴 THE FLOOR — the measured failure, encoded ─────────────────────────────────────────────────
# "decide everything yourself" was read as licence to pick the ANGLE, and the deck answered a
# question nobody asked while passing every gate.
bad = record()
bad["picks"][0] = {"axis": "angle", "source": "delegated", "value": "an 1837 land survey",
                   "basis": BASIS, "alternative": ALT}
f = dp.faults(bad, auto=True)
check(any("may not be" in x for x in f),
      "an INVENTED angle passed — that is the whole reason this file exists")
check(any("genre-default" in x for x in f),
      "...and the message does not name the legitimate alternative, so it teaches nothing")
ok = record()
check(not dp.faults(ok, auto=True), "a genre-default angle was rejected: {}"
                                    .format(dp.faults(ok, auto=True)[:1]))
st = record()
st["picks"][0] = {"axis": "angle", "source": "stated", "value": "what the user asked for"}
check(not dp.faults(st, auto=True), "a STATED angle was rejected")

# ── judgement levers, not just fields ────────────────────────────────────────────────────────────
nob = record()
nob["picks"][dp.AXES.index("density")] = {"axis": "density", "source": "delegated", "value": "x y"}
check(any("basis" in x for x in dp.faults(nob, auto=True)),
      "a pick decided FOR the user with no basis passed — `I judged it` is what this replaces")
for axis in dp.ALTERNATIVE_REQUIRED:
    noa = record()
    noa["picks"][dp.AXES.index(axis)] = {"axis": axis, "source": "delegated",
                                         "value": "a real chosen value", "basis": BASIS}
    check(any("alternative" in x for x in dp.faults(noa, auto=True)),
          "`{}` is one of the three that decide everything downstream and passed with no named "
          "runner-up".format(axis))
# …and an axis outside those three is not taxed for one
light = record()
light["picks"][dp.AXES.index("length")] = {"axis": "length", "source": "delegated",
                                           "value": "12-15 slides", "basis": BASIS}
check(not dp.faults(light, auto=True),
      "an axis outside ALTERNATIVE_REQUIRED was charged for an alternative — the cost must scale "
      "with the risk, not with the field count")

# ── 🔴 language-independent: the same bar in Chinese as in English ───────────────────────────────
cn = record()
cn["picks"][dp.AXES.index("audience")] = {
    "axis": "audience", "source": "delegated", "value": "打算去旅行的人",
    "basis": "请求里写明是准备去旅行的人，没有提到任何会议场合",
    "alternative": "也可能是本地居民，但请求说的是「打算去旅行」"}
check(not dp.faults(cn, auto=True),
      "a real CJK basis/alternative was rejected — `len()` instead of reason_width does exactly "
      "this, and this repo has shipped that bug before: {}".format(dp.faults(cn, auto=True)[:1]))

# ── coverage: every axis is answered by SOMEONE ──────────────────────────────────────────────────
short = record()
short["picks"] = short["picks"][:3]
check(any("no pick recorded" in x for x in dp.faults(short, auto=True)),
      "a record covering 3 of {} axes passed — the unanswered ones are exactly the ones nobody "
      "thought about".format(len(dp.AXES)))
na = record()
na["picks"][dp.AXES.index("style")] = {"axis": "style", "source": "not-applicable", "value": "-"}
check(not dp.faults(na, auto=True), "`not-applicable` was rejected — an axis that genuinely does "
                                    "not apply must have a way to say so")

# ── robustness ───────────────────────────────────────────────────────────────────────────────────
for junk in (None, 7, "str", [1], {"picks": "not a list"}, {"picks": [7]}, {"picks": []}):
    try:
        out = dp.faults(junk, auto=True)
    except Exception as e:                                             # noqa: BLE001
        fails.append("faults raised on {!r}: {}".format(junk, e))
        continue
    check(out != [], "faults({!r}) passed as a complete record".format(junk))
check(dp.faults({"picks": [dict(record()["picks"][1], axis="made-up")]}, auto=True),
      "an invented axis passed")
check(dp.faults({"picks": [dict(record()["picks"][1], source="made-up")]}, auto=True),
      "an invented source passed")

# ── 🔴 THE LADDER SERVES THE USER'S INTENT, NOT THE FIELD COUNT ─────────────────────────────────
# The point of the source ladder is reading ORDER at hand-off: a pick nothing in the request
# pointed at is the likeliest to be wrong and the cheapest to veto, so it must come first.
check(dp.SOURCES.index("stated") < dp.SOURCES.index("inferred-from-request")
      < dp.SOURCES.index("delegated"),
      "the ladder is not ordered by distance from what the user actually said")
mixed = {"picks": [
    {"axis": "language", "source": "stated", "value": "English"},
    {"axis": "density", "source": "delegated", "value": "balanced", "basis": BASIS},
    {"axis": "goal", "source": "inferred-from-request", "value": "inform", "basis": BASIS},
]}
order = [p["source"] for p in dp.delegated(mixed)]
check(order and order[0] == "delegated",
      "the hand-off order does not put the furthest-from-stated pick first: {}".format(order))
check("stated" not in order, "a pick the USER made was listed as something decided for them")
check(len(order) == 2, "an `inferred-from-request` pick was dropped from the hand-off — it still "
                       "was not the user's own words")
# an inferred pick CLAIMS the request points at it, so it owes the pointer
noptr = record()
noptr["picks"][dp.AXES.index("goal")] = {"axis": "goal", "source": "inferred-from-request",
                                         "value": "inform"}
check(any("basis" in x for x in dp.faults(noptr, auto=True)),
      "`inferred-from-request` passed with no basis — that claim IS the difference from `delegated`")

# ── 🔴 WIRED INTO EVERY GATE PATH — and the Codex one especially ─────────────────────────────────
# Measured before this change: 16 of the 17 shared gate sections were mirrored on the Codex path
# and `checkpoints` was the exception — the one record that says whether a human approved anything,
# missing on the runtime most likely to compress the pipeline into one pass.
for name in ("render_deck.py", "deck_gates.py", "codex_delivery_gate.py"):
    src = (SCRIPTS / name).read_text(encoding="utf-8")
    check("delegated_picks" in src,
          "{} does not consume the delegated-picks contract".format(name))
    check("NEVER_DELEGATED" not in src,
          "{} hard-codes the floor instead of importing it".format(name))

# ── the reference that states the rule now HAS a backstop ────────────────────────────────────────
ref = (ROOT / "references" / "checkpoint-convention.md").read_text(encoding="utf-8")
check("delegated" in ref.lower(), "checkpoint-convention.md no longer describes delegated picks")
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
check("delegated_picks.py" in skill,
      "SKILL.md never names the script, so a run that skips the reference meets nothing")

# ── recording picks and merging a plan's gate fragment have a COMMAND (audit 2026-10-29) ──────────
# Operators hand-edited .deck-gates.json to add interview.picks rows and to paste a plan's gate block in —
# the one record the hand-off gates all read, edited as free JSON with nothing validating a row until the
# gate ran at the end.
import json as _json  # noqa: E402
import tempfile as _tf  # noqa: E402

_DG = [sys.executable, str(SCRIPTS / "deck_gates.py")]


def _dg(*args):
    p = subprocess.run(_DG + [str(a) for a in args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


_deck = Path(_tf.mkdtemp(prefix="dg-picks-"))
_gf = _deck / ".deck-gates.json"
_gf.write_text(_json.dumps({"content": {"checkpoint": {"mode": "auto"}}}), encoding="utf-8")
_rc, _out = _dg("picks", _deck, "--set", "audience=neighbours who might volunteer", "--source", "delegated",
                "--basis", BASIS, "--alternative", ALT)
_rec = _json.loads(_gf.read_text(encoding="utf-8"))
_rows = (_rec.get("interview") or {}).get("picks") or []
check(_rc in (0, 1) and any(r.get("axis") == "audience" and r.get("source") == "delegated"
                            and r.get("basis") == BASIS and r.get("alternative") == ALT for r in _rows),
      "`deck_gates.py picks --set audience=…` records a validated row (rc {}): {}".format(_rc, _out[-300:]))
check("still to record" in _out and "angle" in _out,
      "…and says which axes are still unrecorded: {}".format(_out[-300:]))
_rc, _out = _dg("picks", _deck, "--set", "angle=whatever I like", "--source", "delegated", "--basis", BASIS)
_rec = _json.loads(_gf.read_text(encoding="utf-8"))
check(_rc == 2 and "may not be" in _out and not any(r.get("axis") == "angle" for r in _rec["interview"]["picks"]),
      "a DELEGATED angle is refused by the same floor and NOT written (rc {}): {}".format(_rc, _out[-300:]))
_rc, _out = _dg("picks", _deck, "--set", "purpose=a lab meeting", "--source", "delegated", "--basis", BASIS)
check(_rc == 2 and "alternative" in _out, "a delegated purpose with no alternative is refused (rc {}): {}"
      .format(_rc, _out[-200:]))
_rc, _out = _dg("picks", _deck, "--set", "audience=the city council", "--source", "stated")
_rec = _json.loads(_gf.read_text(encoding="utf-8"))
_aud = [r for r in _rec["interview"]["picks"] if r.get("axis") == "audience"]
check(len(_aud) == 1 and _aud[0]["source"] == "stated" and "basis" not in _aud[0],
      "re-recording an axis REPLACES its row rather than adding a second: {}".format(_aud))
for _a in dp.AXES:
    if _a == "audience":
        continue
    _dg("picks", _deck, "--set", "{}=a value".format(_a), "--source", "stated")
_rc, _out = _dg("picks", _deck)
check(_rc == 0 and "all" in _out.lower(), "with every axis recorded, `picks` reports clean (rc {}): {}"
      .format(_rc, _out[-200:]))

# merge: a plan's gate fragment lands in the record, deep, without clobbering what is already there
_frag = _deck / "design-fragment.json"
_frag.write_text(_json.dumps({"design_plan": {"boldness": "bold", "type_scale": {"body": 18}}}), encoding="utf-8")
_rec = _json.loads(_gf.read_text(encoding="utf-8"))
_rec["design_plan"] = {"palette": "kept: ink on paper with one red", "type_scale": {"title": 40}}
_gf.write_text(_json.dumps(_rec), encoding="utf-8")
_rc, _out = _dg("merge", _deck, _frag)
_rec = _json.loads(_gf.read_text(encoding="utf-8"))
check(_rc == 0 and _rec["design_plan"].get("boldness") == "bold"
      and _rec["design_plan"]["type_scale"] == {"title": 40, "body": 18}
      and _rec["design_plan"]["palette"].startswith("kept") and _rec["interview"]["picks"],
      "`deck_gates.py merge` deep-merges a fragment and keeps every field it does not name (rc {}): {}"
      .format(_rc, _out[-300:]))
check("design_plan.boldness" in _out, "…and lists what it set: {}".format(_out[-300:]))
_bad = _deck / "bad.json"
_bad.write_text("[1, 2]", encoding="utf-8")
_before = _gf.read_text(encoding="utf-8")
_rc, _out = _dg("merge", _deck, _bad)
check(_rc == 2 and _gf.read_text(encoding="utf-8") == _before,
      "a fragment that is not a JSON object is refused and the record is untouched (rc {})".format(_rc))
_bad.write_text(_json.dumps({"desgin_plan": {"boldness": "bold"}}), encoding="utf-8")
_rc, _out = _dg("merge", _deck, _bad)
check(_rc == 2 and "desgin_plan" in _out and _gf.read_text(encoding="utf-8") == _before,
      "a misspelt top-level section is refused by name, not written as a new block (rc {}): {}"
      .format(_rc, _out[-200:]))

# the docs that tell an operator how to record picks name the command
for _doc in ("SKILL.md", "references/checkpoint-convention.md"):
    check("deck_gates.py\" picks" in (ROOT / _doc).read_text(encoding="utf-8")
          or "deck_gates.py picks" in (ROOT / _doc).read_text(encoding="utf-8"),
          "{} tells the operator to record picks with `deck_gates.py picks`".format(_doc))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_delegated_picks] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
