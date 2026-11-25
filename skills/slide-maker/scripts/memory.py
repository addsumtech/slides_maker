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


# ── taste.md sections ────────────────────────────────────────────────────────────────────────────
# Edited line by line: the file is the user's own, often hand-edited, so every byte outside the one
# targeted line survives. Section order when a section has to be created: PROFILE · DIALS · NO-GOs ·
# LOOK HISTORY (LOOK HISTORY is appended by the Step-6 close as before; this script never writes it).
SECTIONS = ("PROFILE", "DIALS", "NO-GOs", "LOOK HISTORY")
TABLE = {"DIALS": "| dimension | position | evidence (deck · date · the user's verbatim words) |\n"
                  "|---|---|---|",
         "LOOK HISTORY": "| date | deck | preset/look | canvas value | signature motif |\n"
                         "|---|---|---|---|---|"}
HEADING = {"PROFILE": "## PROFILE  (≤8 lines · facts that shape decks · say \"drop it\" to remove any line)",
           "DIALS": "## DIALS  (≤10 rows)", "NO-GOs": "## NO-GOs  (≤5 lines)",
           "LOOK HISTORY": "## LOOK HISTORY  (most recent 10 lines only — prune the oldest at append)"}
CAPS = {"PROFILE": 8, "DIALS": 10, "NO-GOs": 5}
SKELETON = "# taste.md — slide taste (portable · edit or delete freely)\n"


class CapFull(Exception):
    pass


def _section_of(line: str):
    if not line.startswith("## "):
        return None
    head = line[3:].strip()
    for s in SECTIONS:
        if head.startswith(s):
            return s
    return "?"


def _spans(lines: list[str]) -> dict:
    """section → (heading index, end index exclusive)."""
    out, cur, start = {}, None, 0
    for i, l in enumerate(lines):
        s = _section_of(l)
        if s is not None:
            if cur and cur != "?":
                out.setdefault(cur, (start, i))
            cur, start = s, i
    if cur and cur != "?":
        out.setdefault(cur, (start, len(lines)))
    return out


def _content_idx(lines, section, span) -> list[int]:
    h, e = span
    idx = []
    if section in TABLE:
        rows = [i for i in range(h + 1, e) if lines[i].lstrip().startswith("|")]
        idx = [i for i in rows[1:] if not re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i])]
    else:
        idx = [i for i in range(h + 1, e) if lines[i].lstrip().startswith("- ")]
    return idx


def _line_key(section, line) -> str:
    s = line.strip()
    if section in TABLE:
        cells = re.split(r"(?<!\\)\|", s.strip("|"))
        return cells[0].strip().lower() if cells else ""
    body = s[2:] if s.startswith("- ") else s
    return body.split(":", 1)[0].strip().lower() if ":" in body else body.strip().lower()


def read_sections(text: str) -> dict:
    lines = (text or "").splitlines()
    spans = _spans(lines)
    return {s: [lines[i] for i in _content_idx(lines, s, spans[s])] if s in spans else []
            for s in SECTIONS}


def upsert_line(text: str, section: str, match_key, new_line: str, cap=None) -> str:
    """Replace the first line in `section` whose key is `match_key`, else append. Creates the
    section (and the file skeleton) when missing. Raises CapFull when an append would exceed cap."""
    text = text or ""
    lines = text.splitlines()
    trailing = text.endswith("\n") or not text
    if not lines:
        lines = SKELETON.rstrip("\n").splitlines()
    spans = _spans(lines)
    if section not in spans:
        block = ["", HEADING[section]] + (TABLE[section].splitlines() if section in TABLE else [])
        after = SECTIONS[SECTIONS.index(section) + 1:]
        nxt = min((spans[s][0] for s in after if s in spans), default=None)
        if nxt is None:
            lines = lines + block
        else:
            # insert before the next known section, keeping one blank line between blocks
            lines = lines[:nxt] + block[1:] + [""] + lines[nxt:]
        spans = _spans(lines)
    idx = _content_idx(lines, section, spans[section])
    if match_key is not None:
        for i in idx:
            if _line_key(section, lines[i]) == str(match_key).lower():
                lines[i] = new_line
                return "\n".join(lines) + ("\n" if trailing else "")
    if cap is not None and len(idx) >= cap:
        raise CapFull("{} is full ({} lines) — drop one first (`{} forget …`)"
                      .format(section, cap, SELF))
    h, e = spans[section]
    if idx:
        at = idx[-1] + 1
    elif section in TABLE:
        rows = [i for i in range(h + 1, e) if lines[i].lstrip().startswith("|")]
        at = (rows[-1] + 1) if rows else h + 1
    else:
        at = h + 1
    lines.insert(at, new_line)
    return "\n".join(lines) + ("\n" if trailing else "")


def remove_line(text: str, section: str, match_key):
    """Remove the line in `section` whose key matches (or the N-th line for a 1-based int)."""
    lines = (text or "").splitlines()
    spans = _spans(lines)
    if section not in spans:
        return text, None
    idx = _content_idx(lines, section, spans[section])
    target = None
    if isinstance(match_key, int):
        if 1 <= match_key <= len(idx):
            target = idx[match_key - 1]
    else:
        target = next((i for i in idx if _line_key(section, lines[i]) == str(match_key).lower()),
                      None)
    if target is None:
        return text, None
    gone = lines.pop(target)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), gone


def read_taste() -> str:
    p = taste_path()
    try:
        return p.read_text(encoding="utf-8") if p.exists() else ""
    except OSError as exc:
        print("memory: cannot read {} ({}) — treating it as absent".format(p, exc), file=sys.stderr)
        return ""


def write_taste(text: str) -> Path:
    p = taste_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(p)
    return p


# ── recall ───────────────────────────────────────────────────────────────────────────────────────
RECALL_CAP = 50
CLIP = 160
RULES_AT = {"interview": None, "content": "content", "design": "*", "build": "build",
            "critic": "critic", "handoff": None}
TASTE_AT = {"interview": ("PROFILE", "DIALS", "NO-GOs", "LAST"),
            "content": ("PROFILE",), "design": ("PROFILE", "DIALS", "NO-GOs", "LAST"),
            "build": ("DIALS", "NO-GOs"), "critic": ("DIALS", "NO-GOs"), "handoff": ()}
NOTE_NEXT = ("NEXT: when the user states a requirement, correction or a fact about themselves → "
             "{s} note --kind requirement|correction|praise|veto|profile-fact --key <key> "
             "--quote \"<their words>\" --deck <deck-folder> [--direction more|less|require|avoid] "
             "[--value <fact>] [--standing]   (keys: {s} keys)").format(s=SELF)


def _clip(text: str, width=CLIP) -> str:
    from written_reason import reason_width
    t = " ".join(str(text).split())
    if reason_width(t) <= width:
        return t
    out, w = "", 0
    for ch in t:
        cw = reason_width(ch) or 1
        if w + cw > width - 1:
            break
        out, w = out + ch, w + cw
    return out + "…"


def _row_text(line: str) -> str:
    s = line.strip()
    if s.startswith("|"):
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", s.strip("|"))]
        return " — ".join(c.replace("\\|", "|") for c in cells if c)
    return s[2:] if s.startswith("- ") else s


def _rules(step: str) -> list[dict]:
    import taste_ledger as tl
    want = RULES_AT[step]
    if want is None:
        return []
    return tl.active(tl.load(), None if want == "*" else want)


def recall(step: str, venue=None) -> dict:
    secs = read_sections(read_taste())
    show = TASTE_AT[step]
    d = {"step": step, "root": str(memory_root()),
         "profile": [_row_text(l) for l in secs["PROFILE"]] if "PROFILE" in show else [],
         "dials": [_row_text(l) for l in secs["DIALS"]] if "DIALS" in show else [],
         "nogos": [_row_text(l) for l in secs["NO-GOs"]] if "NO-GOs" in show else [],
         "last_look": (_row_text(secs["LOOK HISTORY"][-1])
                       if "LAST" in show and secs["LOOK HISTORY"] else ""),
         "rules": [{"id": e.get("id"), "rule": e.get("rule"), "quote": e.get("quote"),
                    "deck": (e.get("learned_from") or {}).get("deck"),
                    "date": (e.get("learned_from") or {}).get("date")} for e in _rules(step)],
         "refs": [], "research": [], "proposals": 0, "next": []}
    if step in ("interview", "handoff"):
        d["proposals"] = len(proposals())
    nxt = [NOTE_NEXT]
    if step == "design" and d["rules"]:
        nxt.append('NEXT: record design_plan.taste_applied — one row per TAUGHT RULE above: '
                   '{"id": "<id>", "applied": true} or {"id": "<id>", "applied": false, '
                   '"why_not": "<why it does not bind here>"}')
    if d["proposals"]:
        nxt.append("NEXT: {} pending proposal(s) — {} proposals".format(d["proposals"], SELF))
    if step == "handoff":
        nxt.append("NEXT: at the Step-6 close → {} close <deck-dir>".format(SELF))
    d["next"] = nxt
    return d


def _empty(d) -> bool:
    return not any(d[k] for k in ("profile", "dials", "nogos", "last_look", "rules", "refs",
                                  "research", "proposals"))


def render_prompt(d: dict) -> str:
    if _empty(d):
        return "\n".join(["memory: none on file"] + d["next"])
    out = ["MEMORY · step {} · {}  (current request > interview answers > this memory)"
           .format(d["step"], d["root"])]
    for title, items in (("PROFILE (who the user is)", d["profile"]),
                         ("DIALS (standing design preferences)", d["dials"]),
                         ("NO-GOs (hard vetoes)", d["nogos"])):
        if items:
            out.append(title + ":")
            out += ["  " + _clip(x) for x in items]
    if d["last_look"]:
        out.append("LAST LOOK (vary at least one foundation against it): " + _clip(d["last_look"]))
    if d["rules"]:
        out.append("TAUGHT RULES (apply each, or record why it does not bind):")
        out += ['  [{}] {} — they said "{}" ({}{})'.format(
            r["id"], _clip(r["rule"], 90), _clip(r["quote"], 50), r["deck"] or "?",
            ", " + r["date"] if r["date"] else "") for r in d["rules"]]
    tail = []
    if d["refs"]:
        tail.append("REFERENCES (cached external facts):")
        tail += ["  " + _clip(x) for x in d["refs"]]
    tail += d["research"]
    room = RECALL_CAP - len(out) - len(d["next"])
    out += tail[:max(room, 0)]
    return "\n".join(out + d["next"])


def _cmd_recall(a) -> int:
    d = recall(a.step, a.venue)
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print(render_prompt(d))
    return 0


def proposals(now=None) -> list[dict]:
    return []


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
    r = sub.add_parser("recall", help="the memory THIS step should use")
    r.add_argument("--step", required=True, choices=STEPS)
    r.add_argument("--venue", help="the deck's venue, to match cached references")
    r.add_argument("--format", choices=("prompt", "json"), default="prompt")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    try:
        if a.cmd == "note":
            return _cmd_note(a)
        if a.cmd == "keys":
            return _cmd_keys(a)
        if a.cmd == "recall":
            return _cmd_recall(a)
    except OSError as exc:
        print("memory: could not run — {}".format(exc), file=sys.stderr)
        return 2
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
