#!/usr/bin/env python3
"""USER MEMORY — one command per pipeline step gives any agent the memory that step should use.

🔴 WHY THIS EXISTS. The skill already keeps the user's design taste (`taste.md` at the registry
root) and what they corrected by hand (`taste_ledger.py`). Both are reached through prose spread
over SKILL.md and its references, so an agent that skips a reference — measured: runs never opened
one the prose pointed at — loses every past hint. And a requirement the user voiced mid-build was
only ever kept if someone remembered it at the Step-6 close. This script is the single entry point:

    recall  --step S      what THIS step should use: profile · dials · no-gos · taught rules · refs
    note                  capture a requirement / correction / fact, verbatim, the moment it is said
    close <deck-dir>      Step-6: log which taught rules this deck applied, then list proposals
    proposals             recurring requirements → standing preferences; stale lines → review
    accept / reject       act on a proposal, under its consent tier
    ref add / ref list    external facts (brand guide, venue spec) with source, date and expiry
    forget                remove a line from any store
    keys                  the closed vocabulary

It stores nothing new about design that `taste.md` and the ledger did not already hold: it adds a
`## PROFILE` section (facts about the user that shape decks), an observation log (evidence), a
references cache and a small decisions file — all at the registry root `registry.py` resolves, so
the same commands work on Claude Code, Codex, or any other runtime (host-neutral fallback root).

🔴 WHAT KEEPS IT HONEST.
  - Quotes are the user's own words; a rule with no quote is something the agent decided.
  - Recurrence, not one remark, proposes a standing preference (≥2 distinct decks, or the user
    marked it standing). Proposals are never written without `accept`.
  - Consent tiers: the observation log is evidence and steers nothing → silent. DIALS / NO-GOs →
    written at the Step-6 close and announced with an easy veto (today's rule). PROFILE lines and
    new ledger rules bind every future deck → `--confirmed` (the user said yes) or refused.
  - Privacy: a closed key set; PII shapes are refused everywhere; sensitive categories about the
    USER (health, money, religion, politics, sexuality, immigration) are refused in profile facts.
  - No network. An agent researches with its own web tool and records what it found, with a URL.

Exit 0 ok · 1 problems / refused · 2 could not run.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import registry  # noqa: E402

SELF = "python3 " + str(Path(__file__).resolve())

DESIGN_KEYS = ("colour", "density", "boldness", "icons", "type", "numerals", "motion", "imagery",
               "architecture", "background", "motif")
CONTENT_KEYS = {"length": "content", "language": "content", "citations": "content",
                "structure": "content", "tone": "content", "speaker-notes": "build",
                "delivery-format": "build"}
PROFILE_KEYS = ("role", "field", "organization", "audiences", "venues", "languages", "brand",
                "habits")
DIRECTIONS = ("more", "less", "require", "avoid")
OPPOSITE = {"more": "less", "less": "more", "require": "avoid", "avoid": "require"}
KINDS = ("requirement", "correction", "praise", "profile-fact", "veto", "applied-record")
STEPS = ("interview", "content", "design", "build", "critic", "handoff")
OBS_CAP = 300
MIN_QUOTE = 4

STANDING_WORDS = ("always", "every deck", "all my decks", "in general", "from now on",
                  "一直", "每次", "所有", "以后都", "总是", "永远")

# ── privacy ──────────────────────────────────────────────────────────────────────────────────────
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_DIGITS = re.compile(r"\+?\d[\d \-().]{6,}\d")
_URL_CRED = re.compile(r"https?://[^\s/@]+:[^\s/@]+@")
_URL_TOKEN = re.compile(r"[?&](token|key|sig|signature|secret|password|access_token|api_key|"
                        r"apikey|auth)=", re.I)
_STREET = re.compile(r"\b\d{1,5}\s+(?:[A-Za-z][\w'-]*\s+){0,3}(?:street|st\.|road|rd\.|avenue|"
                     r"ave\.|lane|boulevard|blvd|drive|way)\b", re.I)
_STREET_NL = re.compile(r"\b\w+(?:straat|laan|weg|plein|gracht|kade)\s+\d+", re.I)
_POSTCODE_NL = re.compile(r"\b\d{4}\s?[A-Z]{2}\b")
_STREET_ZH = re.compile(r"[路街道巷弄]\s*\d+\s*号")
SENSITIVE = ("health", "diagnos", "disease", "illness", "medication", "therapy", "pregnan",
             "disabilit", "diabetes", "cancer", "depression", "salary", "income", "debt",
             "mortgage", "bank account", "religio", "church", "mosque", "political", "party member",
             "sexual", "gay", "lesbian", "visa", "immigration", "residence permit", "asylum",
             "病", "诊断", "药", "怀孕", "残疾", "工资", "薪", "收入", "负债", "贷款", "宗教", "信仰",
             "政治", "党员", "性取向", "签证", "移民", "居留", "庇护", "抑郁", "癌")


def pii_faults(text) -> list[str]:
    """Shapes of personal identifiers. Refused in every stored string."""
    t = str(text or "")
    out = []
    if _EMAIL.search(t):
        out.append("an email address")
    for m in _DIGITS.finditer(t):
        if sum(ch.isdigit() for ch in m.group()) >= 9:
            out.append("a phone / ID / card-length number")
            break
    if _URL_CRED.search(t) or _URL_TOKEN.search(t):
        out.append("a URL carrying credentials or a token")
    if _STREET.search(t) or _STREET_NL.search(t) or _POSTCODE_NL.search(t) or _STREET_ZH.search(t):
        out.append("a street address or postcode")
    return out


def sensitive_faults(text) -> list[str]:
    """Sensitive categories about the USER. Applied to profile facts only — a design note about a
    medical deck ("the disease figure needs more colour") is not a fact about the user."""
    t = str(text or "").lower()
    hits = sorted({w for w in SENSITIVE if w in t})
    return ["a sensitive personal category ({})".format(", ".join(hits))] if hits else []


def standing_words(text) -> bool:
    t = str(text or "").lower()
    return any(w in t for w in STANDING_WORDS)


# ── paths and io ─────────────────────────────────────────────────────────────────────────────────
def today() -> _dt.date:
    v = os.environ.get("SLIDE_MAKER_TODAY", "").strip()
    return _dt.date.fromisoformat(v) if v else _dt.date.today()


def memory_root() -> Path:
    """The registry root that holds (or will hold) `taste.md` — memory lives beside it."""
    f = registry.taste_file()
    return f.parent if f else registry.root_for_write()[1]


def taste_path() -> Path:
    return memory_root() / "taste.md"


def obs_path() -> Path:
    return memory_root() / "observations.jsonl"


def refs_path() -> Path:
    return memory_root() / "references.jsonl"


def state_path() -> Path:
    return memory_root() / "memory-state.json"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out, bad = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(rec, dict):
            out.append(rec)
        else:
            bad += 1
    if bad:
        print("memory: skipped {} unreadable line(s) in {}".format(bad, path), file=sys.stderr)
    return out


def _write_jsonl(path: Path, recs: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
                   encoding="utf-8")
    tmp.replace(path)
    return path


def load_obs() -> list[dict]:
    return _read_jsonl(obs_path())


def append_obs(rec: dict) -> Path:
    recs = load_obs() + [rec]
    return _write_jsonl(obs_path(), recs[-OBS_CAP:])


def load_state() -> dict:
    p = state_path()
    try:
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except json.JSONDecodeError:
        print("memory: {} is unreadable — treating it as empty".format(p), file=sys.stderr)
        d = {}
    d.setdefault("accepted", {})
    d.setdefault("rejected", {})
    return d


def save_state(d: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def all_keys() -> tuple[str, ...]:
    return DESIGN_KEYS + tuple(CONTENT_KEYS) + PROFILE_KEYS


def _refuse(msg: str) -> int:
    print("memory: REFUSED — " + msg, file=sys.stderr)
    return 1


# ── note ─────────────────────────────────────────────────────────────────────────────────────────
def note_faults(kind, key, quote, deck, direction, value) -> list[str]:
    out = []
    if kind not in KINDS or kind == "applied-record":
        out.append("--kind must be one of {} (applied-record is written by `close` only)"
                   .format(" | ".join(k for k in KINDS if k != "applied-record")))
    if key not in all_keys():
        out.append("--key {!r} is not in the vocabulary. Design: {}. Content/process: {}. "
                   "Profile: {}.".format(key, ", ".join(DESIGN_KEYS), ", ".join(CONTENT_KEYS),
                                         ", ".join(PROFILE_KEYS)))
    if not str(deck or "").strip():
        out.append("--deck must name the deck (its folder name)")
    from written_reason import reason_width
    if reason_width(quote) < MIN_QUOTE:
        out.append("--quote must carry the user's OWN words")
    if kind == "profile-fact":
        if key not in PROFILE_KEYS:
            out.append("a profile-fact needs a profile key: " + ", ".join(PROFILE_KEYS))
        if not str(value or "").strip():
            out.append("a profile-fact needs --value (the fact itself, in a few words)")
        out += sensitive_faults(value) + sensitive_faults(quote)
    elif kind in ("requirement", "correction", "praise") and direction not in DIRECTIONS:
        out.append("--direction must be one of " + " | ".join(DIRECTIONS))
    elif kind == "veto" and direction not in (None, "avoid"):
        out.append("a veto's direction is `avoid`")
    for field, v in (("quote", quote), ("value", value)):
        for f in pii_faults(v):
            out.append("--{} contains {} — not stored".format(field, f))
    return out


def _cmd_note(a) -> int:
    direction = a.direction or ("avoid" if a.kind == "veto" else None)
    bad = note_faults(a.kind, a.key, a.quote, a.deck, direction, a.value)
    if bad:
        return _refuse("; ".join(bad))
    rec = {"date": today().isoformat(), "deck": a.deck.strip(), "step": a.step or "",
           "kind": a.kind, "key": a.key, "direction": direction or "",
           "value": (a.value or "").strip(), "standing": bool(a.standing or standing_words(a.quote)),
           "quote": a.quote.strip()}
    path = append_obs(rec)
    print("memory: noted {} {} {}{} → {}".format(a.kind, a.key, direction or rec["value"],
                                                 " (standing)" if rec["standing"] else "", path))
    return 0


def _cmd_keys(_a) -> int:
    print("design keys (→ taste.md DIALS):  " + ", ".join(DESIGN_KEYS))
    print("content/process keys (→ ledger): " + ", ".join(
        "{} [{}]".format(k, v) for k, v in CONTENT_KEYS.items()))
    print("profile keys (→ taste.md PROFILE): " + ", ".join(PROFILE_KEYS))
    print("directions: " + " | ".join(DIRECTIONS) + "   kinds: " +
          " | ".join(k for k in KINDS if k != "applied-record"))
    return 0


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _selftest() -> int:
    fails = []
    if pii_faults("ISMRM 2027, 2026-11-25") or not pii_faults("a@b.nl"):
        fails.append("pii_faults mis-scored a date or an email")
    if sensitive_faults("MRI reconstruction researcher") or not sensitive_faults("签证"):
        fails.append("sensitive_faults mis-scored")
    if note_faults("requirement", "colour", "太素了", "d", "more", None):
        fails.append("a valid note was faulted: {}".format(
            note_faults("requirement", "colour", "太素了", "d", "more", None)))
    if not note_faults("requirement", "nope", "太素了", "d", "more", None):
        fails.append("an unknown key passed")
    for f in fails:
        print("selftest FAIL: " + f)
    print("memory selftest: " + ("ok" if not fails else "{} failure(s)".format(len(fails))))
    return 1 if fails else 0


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    n = sub.add_parser("note", help="capture what the user just said, verbatim")
    n.add_argument("--kind", required=True)
    n.add_argument("--key", required=True)
    n.add_argument("--quote", required=True)
    n.add_argument("--deck", required=True)
    n.add_argument("--direction")
    n.add_argument("--value")
    n.add_argument("--step", choices=STEPS)
    n.add_argument("--standing", action="store_true",
                   help="the user marked it as standing (any language)")
    sub.add_parser("keys", help="print the closed vocabulary")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    try:
        if a.cmd == "note":
            return _cmd_note(a)
        if a.cmd == "keys":
            return _cmd_keys(a)
    except OSError as exc:
        print("memory: could not run — {}".format(exc), file=sys.stderr)
        return 2
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
