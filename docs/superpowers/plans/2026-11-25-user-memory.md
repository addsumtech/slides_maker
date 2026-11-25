# slide-maker user memory — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** one CLI, `scripts/memory.py`, that any agent runs per step to recall, capture, promote, age and enrich the user's slide memory, on top of the existing `taste.md` + taste ledger.

**Architecture:** a single stdlib-only script next to `taste_ledger.py` and `registry.py`, importing both (no copies). Data lives at the registry root that holds `taste.md` (`registry.taste_file().parent`, else `registry.root_for_write()[1]`): `taste.md` (gains `## PROFILE`), `observations.jsonl`, `references.jsonl`, `memory-state.json`. The ledger stays where `taste_ledger.ledger_path()` puts it.

**Tech Stack:** Python 3 stdlib; tests in the repo's plain-script style (`check(cond,msg)`, final `N passed, 0 failed`), run with `python tests/test_memory.py`.

**Spec:** `docs/superpowers/specs/2026-11-25-user-memory-design.md`

## Global Constraints
- No new required field in `.deck-gates.json` / `.codex-deck-evidence.json`; no gate code changes.
- No network calls in scripts. No user data in the repo; tests import `_hermetic` first.
- Precedence unchanged: current request > interview answers > memory.
- Caps: PROFILE ≤ 8 lines · DIALS ≤ 10 · NO-GOs ≤ 5 · observations ≤ 300 lines · recall ≤ 50 lines (taught rules + NO-GOs never truncated).
- Thresholds: recurrence ≥ 2 distinct decks · stale ledger = skipped in 3 consecutive applied-records · stale evidence > 365 days · ref TTL default 180 (org) / 365 (venue).
- Consent tiers: observations silent · DIALS/NO-GO write-then-FYI · PROFILE + ledger need `--confirmed`.
- SKILL.md grows ≤ 20 lines; every SKILL.md line removed must be allowlisted by `check_skill_lossless.py`.
- Exit codes: 0 ok · 1 problems/refused · 2 could not run. Every command ends by printing `NEXT:` lines where a next step exists.

## Review Focus
1. Non-Latin quotes and values (Chinese, Japanese, Dutch) — stored and recalled verbatim; standing marked via `--standing` in any language. → Task 1 + Task 3 tests.
2. A `taste.md` hand-edited by the user (extra prose, missing sections, `|` inside cells) — accept/forget must change only the targeted line and leave every other byte. → Task 2 test `edit_preserves_other_bytes`.
3. Corrupt/half-written `observations.jsonl` line — skipped with a stderr warning, never a crash. → Task 1 test.
4. Neutral root only (no `~/.claude`, no `~/.codex`) and `$SLIDE_MAKER_REGISTRY` override — writes land in that root and the next recall reads them. → Task 5 as-printed run.
5. Date-like strings and venue years ("ISMRM 2027", "2026-11-25") must NOT trip the ≥9-digit PII rule. → Task 1 test.

---

### Task 1: store, vocabulary, privacy, `note`, `keys`

**Files:** Create `skills/slide-maker/scripts/memory.py`, `skills/slide-maker/tests/test_memory.py`

**Interfaces — Produces:**
- `memory_root() -> Path` · `obs_path() / refs_path() / state_path() -> Path`
- `DESIGN_KEYS = ("colour","density","boldness","icons","type","numerals","motion","imagery","architecture","background","motif")`
- `CONTENT_KEYS = {"length":"content","language":"content","citations":"content","structure":"content","tone":"content","speaker-notes":"build","delivery-format":"build"}` (key → ledger `binds_at`)
- `PROFILE_KEYS = ("role","field","organization","audiences","venues","languages","brand","habits")`
- `DIRECTIONS = ("more","less","require","avoid")`; `OPPOSITE = {"more":"less","less":"more","require":"avoid","avoid":"require"}`
- `KINDS = ("requirement","correction","praise","profile-fact","veto","applied-record")`
- `pii_faults(text) -> list[str]` · `sensitive_faults(text) -> list[str]`
- `load_obs() -> list[dict]` (skips bad lines, warns on stderr) · `append_obs(rec: dict) -> Path` (prunes to 300)
- `standing_words(text) -> bool` (EN: always, every deck, all my decks, in general, from now on; ZH: 一直, 每次, 所有, 以后都, 总是, 永远)

- [ ] **Step 1: failing tests** — `note` round-trip of a Chinese quote; unknown key → exit 1 and the vocabulary printed; requirement without `--direction` → exit 1; profile-fact without `--value` → exit 1; each PII sample rejected (`a@b.nl`, `+31 6 1234 5678`, `4111 1111 1111 1111`, `https://u:p@x.org`, `https://x.org/?token=abc`, `Main Street 12`… use `12 Baker Street`, NL `2333 ZA`); `"ISMRM 2027"` and `"2026-11-25"` accepted; profile-fact `"I have diabetes"` / `"签证状态"` rejected, design quote `"the disease figure needs more colour"` accepted; a garbage line in the jsonl is skipped; 305 appends leave 300 lines; `--standing` stored; standing word `"以后都要"` sets `standing` even without the flag.
- [ ] **Step 2:** run `python skills/slide-maker/tests/test_memory.py` → FAIL (no module).
- [ ] **Step 3:** implement the Interfaces above + CLI `note --kind --key --quote --deck [--direction] [--value] [--step] [--standing]` and `keys`. `note` stores `date` = today ISO; `applied-record` is refused from the CLI (only `close` writes it). Dates for tests via `$SLIDE_MAKER_TODAY` (YYYY-MM-DD) override.
- [ ] **Step 4:** test → PASS. Also `--selftest` (a minimal in-temp round-trip) exits 0.
- [ ] **Step 5:** commit `memory.py: observation log, closed vocabulary, privacy filter`.

### Task 2: `taste.md` sections + `recall`

**Files:** Modify `memory.py`, `test_memory.py`

**Interfaces — Consumes:** Task 1. `registry.taste_file()`, `taste_ledger.load()/active()`.
**Produces:**
- `read_sections(text) -> dict[str, list[str]]` (keys `PROFILE`,`DIALS`,`NO-GOs`,`LOOK HISTORY`; content lines, table header/rule rows excluded)
- `upsert_line(text, section, match_key: str|None, new_line, cap) -> str` (replace the first line whose key matches, else append; create section — PROFILE above DIALS; raises `CapFull`)
- `remove_line(text, section, match_key) -> tuple[str, str|None]`
- `recall(step: str, venue: str|None=None) -> dict` with keys `profile, dials, nogos, last_look, rules, refs, proposals, next`; `render_prompt(d) -> str`
- CLI `recall --step interview|content|design|build|critic|handoff [--venue V] [--format prompt|json]`

Sections per step: interview = all taste sections + proposals count; content = profile + rules(binds_at content) + refs; design = profile + dials + nogos + last_look + **all** active rules + refs; build = dials + nogos + rules(build); critic = dials + nogos + rules(critic); handoff = proposals + `NEXT: memory.py close <deck-dir>`. Every step's NEXT includes the `note` command line; design adds the `taste_applied` instruction when rules exist.

- [ ] **Step 1: failing tests** — empty root → exactly `memory: none on file` + the note NEXT line; fixture `taste.md` (this repo's schema example + PROFILE 8 lines, DIALS 10, NO-GOs 5) + 6 ledger entries (mixed binds_at) → design recall ≤ 50 lines and all 6 rule ids present; content recall has only content rules; `--format json` parses; `upsert_line` on a hand-edited file with extra prose and a `\|` cell changes exactly one line (`edit_preserves_other_bytes`); CapFull raised at the 9th PROFILE line.
- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3:** implement. One line per item, truncated to 160 display columns (`written_reason.reason_width`); trim refs then proposals to fit 50.
- [ ] **Step 4:** run → PASS.
- [ ] **Step 5:** commit `memory.py recall: one bounded memory block per step`.

### Task 3: `close`, `proposals`, `accept`, `reject`, `forget`

**Files:** Modify `memory.py`, `test_memory.py`

**Interfaces — Consumes:** Tasks 1–2, `taste_ledger.design_of/entry_faults/load/save`.
**Produces:**
- `proposals(today: date) -> list[dict]` — each `{id, target: "dial"|"nogo"|"profile"|"rule"|"review", key, direction, decks:[...], quotes:[...], reason, needs_confirm: bool}`; `id = "p-" + sha1(target|key|direction)[:8]`
- CLI `close <deck-dir>` · `proposals` · `accept <id> [--position P] [--text T] [--rule R] [--rule-id ID] [--confirmed]` · `reject <id>` · `forget <profile:KEY|dial:DIM|nogo:N|rule:ID|obs:KEY|ref:KEY>`

Rules:
- promotion: group requirement/correction/praise by `(key, direction)`; propose when distinct decks ≥ 2 or any record `standing`. `veto` → nogo; design key → dial; content key → rule (binds_at from `CONTENT_KEYS`); `profile-fact` → profile on first sight (one record is enough — it is a fact).
- conflict: newest group's direction opposite to an older accepted one on the same key → a dial proposal whose reason says it UPDATES the row.
- review: ledger id in `skipped` of the last 3 applied-records consecutively; DIALS/PROFILE row whose newest date (evidence cell, or newest obs on that key) is > 365 days old.
- `memory-state.json` = `{"accepted": {id: date}, "rejected": {id: n_decks_at_reject}}`; accepted never re-proposed; rejected re-proposed only when distinct-deck count grows.
- `accept` dial needs `--position`, nogo needs `--text`, rule needs `--rule` (id defaults to `<key>-<direction>`), profile/rule need `--confirmed` else exit 1 printing the question to ask the user. Evidence written as `deck · date · "quote"` (newest record). Dial/nogo accept prints the FYI line: `recorded to your taste profile: <line> — say the word and I'll drop it`.
- `close`: reads `.deck-gates.json` else `.codex-deck-evidence.json`, `design_of` → `taste_applied`; appends `applied-record {deck: dirname, applied, skipped}`; prints `logged N observations this deck`, then proposals grouped by tier with the exact accept command.

- [ ] **Step 1: failing tests** — two notes in ONE deck → no proposal; same key+direction in two decks → dial proposal; standing note in one deck → proposal; profile-fact → profile proposal with `needs_confirm`; accept profile without `--confirmed` → exit 1 and taste.md unchanged; accept dial writes row + FYI line; opposite direction later → update proposal, accept replaces the row (one row for that dimension); reject → not re-proposed until a third deck; rule accept goes through `entry_faults` and lands in the ledger; `close` on a fixture deck with `design_plan.taste_applied` and on a Codex `design` record both log the record; three consecutive skips → review proposal; `forget profile:role` removes only that line.
- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** run → PASS.
- [ ] **Step 5:** commit `memory.py: recurrence proposals, consent tiers, staleness review`.

### Task 4: external references

**Files:** Modify `memory.py`, `test_memory.py`

**Produces:** CLI `ref add --key org:NAME|venue:NAME --url URL --facts TEXT [--ttl-days N]` · `ref list [--expired]`; `refs_for(names: list[str], today) -> (fresh: list, expired: list)`.

- `--url` must be `http(s)://` unless `--facts unknown` (then `--url none` allowed); credential/token URLs refused (Task 1 `pii_faults`). Newer ref with the same key replaces the older.
- recall: names = PROFILE `organization` + `venues` values (split on `,`/`·`/`、`/`;`, parentheses dropped) + `--venue`. Fresh refs print as `ref <key>: <facts> (source, fetched)`; missing or expired → `NEXT: research "<name>" with your own web tool (official brand guide / venue slot, aspect ratio, template), then memory.py ref add --key … --url … --facts …; nothing found → --facts unknown --url none and ask the user`. At most 2 research lines.

- [ ] **Step 1: failing tests** — ref add/list; expired after TTL (via `$SLIDE_MAKER_TODAY`); recall with PROFILE `organization: LUMC` and no ref → research NEXT; with fresh ref → the facts line; `--venue ISMRM-2027` matched; token URL refused; `unknown` accepted.
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5:** commit `memory.py ref: cached external facts with source, date and expiry`.

### Task 5: wiring, docs, CI, acceptance

**Files:** Modify `skills/slide-maker/SKILL.md` (Step 0 personalization line, Step 2 ledger block command, Steps 1/5 one line each, a one-line "any step" note rule, Step-6 close checklist item 4), `references/user-taste.md` (PROFILE schema + scope amendment + cap ~650 tokens, observation log, proposals + consent tiers, refs, privacy), `references/interview-protocol.md` (run recall before Q1), `references/codex-runtime.md` (one line), `references/handoff-checklist.md` (FYI line includes observation count + proposals), `references/file-inventory.md` (`memory.py` entry), `.github/workflows/ci.yml` (step after "Taste ledger", same grep pattern), lossless allowlist if a SKILL.md line changed.

- [ ] **Step 1:** edits. Verify `wc -l SKILL.md` delta ≤ 20.
- [ ] **Step 2:** `python3 scripts/check_inventory.py`, `python3 scripts/check_tests_wired.py`, `python3 scripts/check_skill_lossless.py --baseline origin/main:skills/slide-maker/SKILL.md`, `python3 scripts/check_versions.py` → all exit 0.
- [ ] **Step 3:** full `sm-ci` on the worktree (background) → `RESULT = GREEN`; compare with the baseline run on `../slides_maker-base`.
- [ ] **Step 4: as-printed non-Claude run** — `HOME=$(mktemp -d)` with no `.claude`/`.codex`, `SLIDE_MAKER_REGISTRY` unset; start from `memory.py recall --step interview`, then follow ONLY printed `NEXT:` commands (filling placeholders with fixture values) through note ×2 decks → close → accept → recall; confirm the accepted row appears under `~/.slide-maker/slide-templates/taste.md` and in the next recall.
- [ ] **Step 5:** read every step's recall output on the fixture store by eye.
- [ ] **Step 6:** commit `wire memory.py into the pipeline; docs + CI`.
- [ ] **Step 7:** whole-branch review by a fresh reviewer; fix confirmed findings; re-run CI.

### Task 6: seed memory for existing users (spec Addendum)
**Files:** Modify `memory.py`, `test_memory.py`, `references/user-taste.md`, `references/file-inventory.md`
**Produces:** `legacy_footprint() -> bool` · `seed(dirs: list[Path]) -> dict` · CLI `seed [--scan DIR…] [--skip]`; kind `recorded` (written by seed only); state key `seeded`.
- [ ] Step 1: failing tests — fixture HOME with two shared records (language 中文, density diagram-heavy, taste_applied), one Codex record, one placeholder record, one delegated-language record, one unreadable folder; seed → 3 applied-records, a confirm-first languages proposal and a confirm-first density proposal, the unreadable folder named; second seed → no duplicates; `--skip` marks; recall prompts only for a legacy, unseeded user; a new user's first note marks fresh and no prompt follows.
- [ ] Step 2–4: FAIL → implement → PASS. Step 5: commit.
