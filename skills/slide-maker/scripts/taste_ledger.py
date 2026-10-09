#!/usr/bin/env python3
"""The TASTE LEDGER — what this user has already taught, so the next deck does not relearn it.

🔴 WHY THIS EXISTS. Every deck starts from zero. The skill has 39 references and 60-odd tests, and
none of them remember a single thing the user actually said. Measured, from one user's own history,
the SAME correction arriving on deck after deck:

    "为什么这个slide没有icon"                     — icons missing, found by the user at hand-off
    "设计能力变弱了"                                — a deck of grey blocks
    "尺子这个确实有些太impressive了,可以用block之类的"  — a motif that overpowered its content
    "对于实验室或者会议场景,ppt的默认字体应该是…"      — a type default, corrected by hand

Each cost a delivery to discover. Each was then forgotten. This is the difference between a skill
that is *configured* and a skill that *learns*: without it, the user is the memory, and paying that
tax is what "从零开始" actually feels like from their side.

🔴 WHY IT IS SELF-LIMITING, AND WHY THAT MATTERS MOST. A ledger that only grows becomes noise, and
noise is indistinguishable from having no ledger. So an entry that earns a DETERMINISTIC GATE is
retired and points at it:

    add → the rule binds by being read at the step it applies to   (soft, costs attention)
    retire --gate CODE → the rule binds by being checked            (hard, costs nothing)

That is this skill's own enforcement invariant ("every 🔴 MUST must be wired into a gate artifact")
applied to taste: **the ledger is the holding pen for user-taught rules that do not have a gate
yet.** Entries leave by being promoted, not by being forgotten.

🔴 WHAT KEEPS IT FROM BECOMING VIBES. Three required fields, each blocking:
  - `quote`        — the user's own words. Not your summary of them. A rule with no quote is
                     something you decided and attributed to them.
  - `learned_from` — which deck, and when. A rule with no origin cannot be re-examined when it
                     stops being true, and taste does change.
  - `binds_at`     — the pipeline step that must read it. A rule that binds nowhere is a note.

STORAGE. The DATA is per-user and lives outside the repo (default `~/.slide-maker/taste-ledger.json`,
override with `$SLIDE_MAKER_TASTE_LEDGER`); the MECHANISM ships in the repo. A user's verbatim
feedback is theirs and does not belong in a public git history.

    python3 scripts/taste_ledger.py add --id icons-are-default --quote "…" --rule "…" \
            --binds-at design --deck melbourne-first-trip --date 2026-09-03
    python3 scripts/taste_ledger.py list [--binds-at design] [--format prompt]
    python3 scripts/taste_ledger.py retire icons-are-default --gate ICON_FAMILY_UNSEEN
    python3 scripts/taste_ledger.py check <deck-dir>
    python3 scripts/taste_ledger.py --selftest

Exit 0 clean · 1 problems · 2 could not run.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

GATES = ".deck-gates.json"
BINDS = ("content", "design", "build", "critic")
MIN_QUOTE = 4
MIN_RULE = 12
ID_RX = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}$")


def _w(text) -> int:
    """Width, not codepoints — the same bar in Chinese as in English.

    🔴 `len()` counts CODEPOINTS, so a CJK reason clears a floor at half the information an
    English one needs: an 11-codepoint Chinese brief is and was rejected by a floor of
    12, while a 12-letter English phrase carrying a third as much passed. Measured on a real
    Chinese deck built with this skill. ONE definition, imported — see written_reason.py.
    """
    from written_reason import reason_width
    return reason_width(text)


def ledger_path() -> Path:
    env = os.environ.get("SLIDE_MAKER_TASTE_LEDGER")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".slide-maker" / "taste-ledger.json"


def load(path: Path | None = None) -> list[dict]:
    """The ledger, or an empty one. A fresh install has no ledger and that is not an error —
    the gate below must therefore never REQUIRE entries, only require that existing ones were
    read."""
    p = path or ledger_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                     # noqa: BLE001 - report, never guess
        raise SystemExit("[taste] cannot read {}: {}".format(p, e))
    entries = data.get("entries") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise SystemExit("[taste] {} does not hold a list of entries.".format(p))
    return [e for e in entries if isinstance(e, dict)]


def save(entries: list[dict], path: Path | None = None) -> Path:
    p = path or ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    return p


def active(entries, binds_at=None) -> list[dict]:
    """Entries still binding by attention. A retired entry is enforced by a gate and must NOT be
    re-listed — that is the whole self-limiting property."""
    out = [e for e in entries if not str(e.get("retired_by") or "").strip()]
    if binds_at:
        out = [e for e in out if str(e.get("binds_at") or "").strip().lower() == binds_at]
    return out


def entry_faults(e) -> list[str]:
    """What makes an entry a rule rather than a feeling."""
    out: list[str] = []
    if not isinstance(e, dict):
        return ["must be an object."]
    eid = str(e.get("id") or "").strip()
    if not ID_RX.match(eid):
        out.append("`id` must be a short kebab-case slug, got {!r}.".format(eid))
    if _w(e.get("quote")) < MIN_QUOTE:
        out.append("{}: `quote` must carry the user's OWN words. A rule with no quote is something "
                   "you decided and attributed to them.".format(eid or "?"))
    if _w(e.get("rule")) < MIN_RULE:
        out.append("{}: `rule` must say what to DO about it, not restate the complaint."
                   .format(eid or "?"))
    if str(e.get("binds_at") or "").strip().lower() not in BINDS:
        out.append("{}: `binds_at` must be one of {} — the step that has to read it. A rule that "
                   "binds nowhere is a note.".format(eid or "?", " | ".join(BINDS)))
    lf = e.get("learned_from")
    if not isinstance(lf, dict) or not str(lf.get("deck") or "").strip():
        out.append("{}: `learned_from.deck` must name the deck this was learned on, so it can be "
                   "re-examined when it stops being true.".format(eid or "?"))
    return out


# ── the gate contract ────────────────────────────────────────────────────────────────────────────
def design_of(record) -> dict:
    """The design block, from EITHER schema — ONE owner, imported, never re-spelled here.

    🔴 `blind_read.design_of` knows that the shared record calls it `design_plan` and the Codex
    record calls it `design`. This module's first version reached for `design_plan` on the Codex
    path, where that key has never existed, which made this gate permanently unsatisfiable there —
    the same `png`/`path` drift `material_probe.file_value` was written to end, third occurrence.
    A second copy of the key list here would be the fourth.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from blind_read import design_of as _shared
    return _shared(record)


def faults(design_plan, entries) -> list[str]:
    """Did the design step READ the ledger? Empty ledger → nothing to check, always.

    This does not check that the rules were OBEYED — a rule can be right to break, and a gate that
    forbids deviation would be worse than the rules it enforces. It checks that each active rule was
    CONSIDERED and that a skip was reasoned. That is the same contract the icon rule already uses."""
    live = active(entries, None)
    if not live:
        return []
    if not isinstance(design_plan, dict):
        return [MISSING.format(n=len(live))]
    seen = design_plan.get("taste_applied")
    if not isinstance(seen, list):
        return [MISSING.format(n=len(live))]
    by_id = {str(r.get("id") or "").strip(): r for r in seen if isinstance(r, dict)}
    out: list[str] = []
    for e in live:
        eid = str(e.get("id") or "").strip()
        row = by_id.get(eid)
        if row is None:
            out.append("`design_plan.taste_applied` never mentions `{}` — {} (learned on {}). "
                       "Apply it, or record why it does not bind on this deck."
                       .format(eid, str(e.get("rule"))[:80],
                               (e.get("learned_from") or {}).get("deck")))
            continue
        if row.get("applied") is True:
            continue
        if _w(row.get("why_not")) < MIN_RULE:
            out.append("`taste_applied[{}]` is not applied and gives no reason. A rule the user "
                       "taught is skipped in WRITING or not at all.".format(eid))
    return out


# the command carries this file's ABSOLUTE path (braces doubled for .format): `python3 scripts/taste_ledger.py`, printed by
# `deck_gates.py check`, ran only from the skill folder (non-Claude audit, 2026-10-09)
_SELF_CMD = ("python3 " + __import__("shlex").quote(str(Path(__file__).resolve()))).replace("{", "{{").replace("}", "}}")
MISSING = ("`design_plan.taste_applied` is missing, and the taste ledger has {n} active entry(ies) "
           "— things this user has already corrected by hand. Read them "
           "(`" + _SELF_CMD + " list --binds-at design --format prompt`) and record "
           "one row each:\n"
           '    "taste_applied": [{{"id": "<entry id>", "applied": true}},\n'
           '                      {{"id": "<entry id>", "applied": false, '
           '"why_not": "<why it does not bind here>"}}]')


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────
def _cmd_add(a) -> int:
    entries = load()
    if any(str(e.get("id") or "") == a.id for e in entries):
        print("[taste] `{}` already exists — edit it in {} or pick another id."
              .format(a.id, ledger_path()), file=sys.stderr)
        return 1
    e = {"id": a.id, "quote": a.quote, "rule": a.rule, "binds_at": a.binds_at,
         "learned_from": {"deck": a.deck, "date": a.date or ""}, "retired_by": ""}
    bad = entry_faults(e)
    if bad:
        for b in bad:
            print("[taste] " + b, file=sys.stderr)
        return 1
    entries.append(e)
    print("[taste] added `{}` (binds at {}) → {}".format(a.id, a.binds_at, save(entries)))
    return 0


def _cmd_list(a) -> int:
    entries = load()
    live = active(entries, a.binds_at)
    if a.format == "prompt":
        if not live:
            print("(no taste-ledger entries bind here)")
            return 0
        print("THINGS THIS USER HAS ALREADY CORRECTED — apply each, or record why it does not bind:")
        for e in live:
            lf = e.get("learned_from") or {}
            print('  - [{}] {}\n      they said: "{}"  ({}{})'.format(
                e.get("id"), e.get("rule"), e.get("quote"), lf.get("deck") or "?",
                ", " + lf["date"] if lf.get("date") else ""))
        return 0
    retired = [e for e in entries if str(e.get("retired_by") or "").strip()]
    for e in live:
        print("{:<28} {:<8} {}".format(str(e.get("id")), str(e.get("binds_at")),
                                       str(e.get("rule"))[:80]))
    for e in retired:
        print("{:<28} {:<8} RETIRED → gate {}".format(str(e.get("id")), str(e.get("binds_at")),
                                                      e.get("retired_by")))
    print("\n[taste] {} active, {} retired into gates  ({})"
          .format(len(live), len(retired), ledger_path()))
    return 0


def _cmd_retire(a) -> int:
    entries = load()
    for e in entries:
        if str(e.get("id") or "") == a.id:
            e["retired_by"] = a.gate
            print("[taste] `{}` retired — it is now enforced by {}, so it stops costing attention. "
                  "{}".format(a.id, a.gate, save(entries)))
            return 0
    print("[taste] no entry `{}`.".format(a.id), file=sys.stderr)
    return 1


def _cmd_check(a) -> int:
    deck = Path(a.deck).expanduser().resolve()
    p = deck / GATES
    if not p.exists():
        print("[taste] no {} in {}".format(GATES, deck), file=sys.stderr)
        return 2
    gates = json.loads(p.read_text(encoding="utf-8"))
    bad = faults(gates.get("design_plan"), load())
    for b in bad:
        print("[taste] " + b)
    print("[taste] {}".format("{} problem(s)".format(len(bad)) if bad else "ok"))
    return 1 if bad else 0


def _selftest() -> int:
    import tempfile
    fails = []
    E = {"id": "icons-are-default", "quote": "为什么这个slide没有icon",
         "rule": "categorical content gets icons by default; skipping needs a category reason",
         "binds_at": "design", "learned_from": {"deck": "melbourne-first-trip",
                                                "date": "2026-09-03"}, "retired_by": ""}
    if entry_faults(E):
        fails.append("a well-formed entry failed: {}".format(entry_faults(E)))
    for missing in ("quote", "rule", "binds_at"):
        bad = dict(E)
        bad[missing] = ""
        if not entry_faults(bad):
            fails.append("an entry with no `{}` passed".format(missing))
    if not entry_faults({**E, "learned_from": {}}):
        fails.append("an entry with no origin deck passed")
    if not entry_faults({**E, "id": "Not A Slug"}):
        fails.append("a non-slug id passed")
    if not entry_faults({**E, "binds_at": "whenever"}):
        fails.append("an invented binds_at passed")

    # an EMPTY ledger must never demand anything — the fresh-install case
    if faults(None, []) or faults({}, []):
        fails.append("an empty ledger demanded a field")
    # a live ledger must be read
    if not faults({}, [E]):
        fails.append("a live entry was not required to be read")
    if not faults({"taste_applied": []}, [E]):
        fails.append("an empty taste_applied passed against a live entry")
    if faults({"taste_applied": [{"id": "icons-are-default", "applied": True}]}, [E]):
        fails.append("an applied entry failed")
    if not faults({"taste_applied": [{"id": "icons-are-default", "applied": False}]}, [E]):
        fails.append("a skip with no reason passed")
    if faults({"taste_applied": [{"id": "icons-are-default", "applied": False,
                                  "why_not": "this deck has no categorical content at all"}]}, [E]):
        fails.append("a reasoned skip failed")
    # 🔴 the self-limiting property: a RETIRED entry must stop costing attention
    if faults({}, [{**E, "retired_by": "READ_PLAN_UNSEEN"}]):
        fails.append("a retired entry was still demanded — the ledger would grow without bound")
    if active([{**E, "retired_by": "X"}]):
        fails.append("active() returned a retired entry")
    if len(active([E, {**E, "id": "other", "binds_at": "critic"}], "design")) != 1:
        fails.append("binds_at filter is wrong")

    # round-trip through a real file
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "l.json"
        save([E], p)
        got = load(p)
        if len(got) != 1 or got[0]["quote"] != E["quote"]:
            fails.append("round-trip lost the quote (encoding?)")
    if load(Path(td) / "gone.json"):
        fails.append("a missing ledger did not read as empty")

    for f in fails:
        print("FAIL " + f)
    print("[taste_ledger selftest] {}".format("FAILED: {}".format(len(fails)) if fails else "ok"))
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    a1 = sub.add_parser("add")
    a1.add_argument("--id", required=True)
    a1.add_argument("--quote", required=True, help="the user's OWN words")
    a1.add_argument("--rule", required=True, help="what to DO about it")
    a1.add_argument("--binds-at", required=True, choices=BINDS)
    a1.add_argument("--deck", required=True, help="the deck it was learned on")
    a1.add_argument("--date", default="")
    a2 = sub.add_parser("list")
    a2.add_argument("--binds-at", choices=BINDS)
    a2.add_argument("--format", choices=("table", "prompt"), default="table")
    a3 = sub.add_parser("retire")
    a3.add_argument("id")
    a3.add_argument("--gate", required=True, help="the lint code / gate that now enforces it")
    a4 = sub.add_parser("check")
    a4.add_argument("deck")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    return {"add": _cmd_add, "list": _cmd_list, "retire": _cmd_retire,
            "check": _cmd_check}.get(a.cmd, lambda _a: (ap.print_help() or 2))(a)


if __name__ == "__main__":
    sys.exit(main())
