# slide-maker user memory — design

Date: 2026-11-25 · Status: draft for approval · Approach: **A (extend the existing stores, add one entry point)**

## Intent — why
Past interactions carry hints the next deck should use: requirements the user keeps repeating,
facts about who they are (role, field, audiences, venues, languages, brand) that shape every deck.
Today the skill remembers *design* taste only, learns it slowly (written once, at the Step-6 close,
promoted only after it recurs in ≥2 decks' round records), and reaches it through prose spread over
SKILL.md + `references/user-taste.md`. A non-Claude agent that skips those references loses all of
it (project memory `reference-only-rules-unread`: runs never opened a reference the prose pointed at).

Goal in one line: **any agent runs one command per step and gets back exactly the memory that step
should use; every requirement the user voices is captured as it happens; recurring ones are
proposed for promotion; stale ones are surfaced; external facts tied to the user's profile are
researched once, cached with source + date, and re-checked when they expire.**

## What exists today (unchanged by this design)
| store | location | holds | read by |
|---|---|---|---|
| `taste.md` | registry root (`scripts/registry.py` resolves: `~/.claude/slide-templates` · `~/.codex/slide-templates` · `~/.slide-maker/slide-templates` · `$SLIDE_MAKER_REGISTRY`) | DIALS ≤10 · NO-GOs ≤5 · LOOK HISTORY 10 | interview, design dispatch, `check_register_pixels.py` (LOOK HISTORY hex) |
| `taste-ledger.json` | `$SLIDE_MAKER_TASTE_LEDGER` → `$SLIDE_MAKER_REGISTRY/…` → `~/.slide-maker/taste-ledger.json` | user-taught rules (quote · rule · binds_at · deck), retired when gated | Step 2 + gate (`design_plan.taste_applied`) |
| `registers.md`, template subfolders | registry root | invented registers, saved templates | interview Q1, design |

All three keep their schema, location and gates. Precedence stays **current request > this
interview's answers > memory** (user-taste.md §Precedence); memory seeds, it never decides.

## Goals
1. **Profile layer** — a `## PROFILE` section in `taste.md` for facts about the user that affect decks.
2. **Continuous capture** — an observation log written whenever the user states a requirement or
   correction (any step, not only Step 6), verbatim.
3. **One entry point** — `scripts/memory.py recall --step <step>` prints the bounded memory block for
   that step, merged from all stores. This is the generality mechanism for non-Claude agents.
4. **Self-evolution** — (a) recurrence → promotion *proposals*; (b) staleness → review prompts;
   (c) external enrichment cached with source/date/TTL.
5. **Privacy by construction** — field allowlist + value deny-patterns enforced by the script.

## Non-goals
- No migration or merge of the existing stores (approach B was rejected: every gate reading
  `taste.md`/ledger would have to change; this repo has recorded the two-schema drift bug twice).
- No use of host-specific memory (Claude memory, AGENTS.md) — not portable (approach C, rejected).
- No new required gate field in `.deck-gates.json` / Codex evidence (gate paperwork is a measured
  regression cause). Memory use is checked by the existing `taste_applied` gate only.
- No network access inside scripts. Agents research with their own web tool; scripts only store,
  validate and expire what they record.
- No onboarding questionnaire. The profile fills from what the user already says.

## Anti-goals (failure even if it "works")
- Memory that overrides the user's live words, or fossilizes one deck's look into a house style
  (the vary-the-look rule still holds).
- A write the user never saw (every write keeps the one-line FYI + easy veto).
- Storing anything sensitive, or any user data inside the repo.
- A recall block so long agents skim it — the block is capped.
- SKILL.md growing by more than ~20 lines.

## Design

### 1. PROFILE section in `taste.md`
```markdown
## PROFILE  (≤8 lines · facts that shape decks · say "drop it" to remove any line)
- role: MRI reconstruction researcher (PhD) — "我是做 MRI 重建的" · cine-mri · 2026-06-14
- audiences: lab meeting · conference (ISMRM) · job interview — <deck · date>
- languages: zh conversation, en slides — <evidence>
- organization: LUMC (brand: registry template lkeb-lumc) — <evidence>
```
- **Allowed keys (closed set):** `role`, `field`, `organization`, `audiences`, `venues`,
  `languages`, `brand`, `habits` (recurring non-design deck habits, e.g. "always adds speaker notes").
- Each line carries evidence (verbatim words or "stated in interview" · deck · date), same rule as DIALS.
- `user-taste.md`'s SCOPE EXCLUSION is amended: PROFILE facts are allowed; **workflow/mode
  directives (auto waivers, checkpoint skips) remain forbidden** — the schema still has no field for them.
- File cap raised from ~500 to ~650 tokens.

### 2. Observation log — `<registry root>/observations.jsonl`
One JSON object per line:
`{"date","deck","step","kind","key","direction","value","standing","quote"}`
- `direction` (requirement/correction/praise/veto): one of `more` | `less` | `require` | `avoid`. A closed
  set so recurrence is counted without fuzzy matching; `more`↔`less` and `require`↔`avoid` are opposites.
- `value`: required for `profile-fact` (the fact itself); `standing: true` when the user marked it as
  standing in ANY language (the agent sets `--standing`; the EN/ZH word list is only a fallback).
- `kind`: `requirement` | `correction` | `praise` | `profile-fact` | `veto` | `applied-record` (written only by `close`)
- `key`: from a fixed vocabulary the script ships (the DIALS dimensions — colour, density, boldness,
  icons, type, numerals, motion, imagery, layout/architecture, background — plus content/process keys:
  length, language, citations, speaker-notes, structure, tone, delivery-format — plus the PROFILE keys).
  Unknown key → rejected with the list printed (keeps recurrence counting honest).
- `quote` is required and must be the user's words (same rule as the ledger).
- Written by `memory.py note …` at the moment the user says it. Step 6's existing `user-dials:` round
  lines are logged through the same command, so there is one stream.
- Capped at the most recent 300 lines (prune oldest on append); it is evidence, not the store.

### 3. `scripts/memory.py` — the only new script
```
memory.py recall --step interview|content|design|build|critic|handoff [--format prompt|json]
memory.py note --kind K --key K --quote "…" --deck D [--direction "…"] [--step S]
memory.py close <deck-dir>               # Step-6: snapshot this deck's taste_applied into the log, then print proposals
memory.py proposals                      # promotion + staleness candidates, nothing written
memory.py accept <proposal-id>           # writes the target row, prints the FYI line to show the user
memory.py reject <proposal-id>           # remembered, not re-proposed for the same evidence
memory.py ref add --key org:LUMC --url U --facts "…" [--ttl-days 180]
memory.py ref list [--expired]
memory.py forget <key|line-id>           # user-requested deletion, any store
memory.py --selftest
```
- **recall** merges: PROFILE (all steps) · DIALS + NO-GOs + last LOOK HISTORY line (design/build/critic)
  · active ledger entries — **all** of them at `--step design` (the existing gate,
  `taste_ledger.faults()` → `active(entries, None)`, requires a `taste_applied` row for every active
  entry whatever its `binds_at`), only the matching `binds_at` at other steps · cached refs whose key matches a PROFILE
  organization/venue or the current deck's venue · open proposals (interview + handoff only).
  Output ≤ 50 lines, every item one line; taught rules and NO-GOs are never truncated (the gate needs
  them in full), refs and proposals are trimmed first; ends with `NEXT:` lines naming the commands the step should run
  (house style: every script prints its next step). Empty stores → one line `memory: none on file`.
- **Root resolution** reuses `registry.py`; ledger path reuses `taste_ledger.ledger_path()`. No new
  locations, no new env vars.
- Exit codes follow the repo: 0 ok · 1 problems · 2 could not run.

### 4. Self-evolution
- **(a) Recurrence → proposal.** Same `key`+`direction` in ≥2 distinct decks, or a quote containing
  standing words ("always", "every deck", "in general", "一直", "每次", "所有") → a proposal naming
  its target: design preference → DIALS row; veto → NO-GO; profile-fact → PROFILE line;
  content/build/critic rule → ledger entry (`binds_at` from `step`). Conflicting direction on an
  existing DIALS row → proposal to UPDATE that row. **Nothing is promoted without `accept`.**
  **Consent tiers (decided by the user):**
  - observation log (`note`, `close`) — written silently; it is evidence and steers no deck. The
    hand-off FYI carries one summary line ("logged N observations this deck").
  - DIALS / NO-GO / LOOK HISTORY — today's rule: write at Step-6, announce in the FYI line, easy veto.
  - PROFILE lines and new ledger entries — **explicit user yes before `accept`** (a ledger entry adds a
    `taste_applied` obligation to every future deck). `accept` for these targets requires `--confirmed`;
    without it the script refuses and prints the question to ask.
  This replaces "promote at Step 6 by reading round records" with a computed list; the promotion
  criteria themselves are unchanged.
- **(b) Staleness.** `memory.py close <deck-dir>` (Step-6 close) reads that deck's
  `design_plan.taste_applied` from `.deck-gates.json` (or the Codex evidence file) and appends one
  `kind: applied-record` line `{deck, date, applied: [ids], skipped: [ids]}` to the log — no gate code
  changes. From those records: a ledger entry recorded
  `applied: false` in 3 consecutive decks → review proposal ("still want this?"). A DIALS/PROFILE
  line whose evidence is > 12 months old and was never re-confirmed → review proposal. Review never
  deletes; the user decides.
- **(c) External enrichment.** When PROFILE names an organization or venue, or a deck names a venue,
  and no unexpired ref exists, recall's `NEXT:` asks the agent to research it with its own web tool
  (official brand guidelines; venue slot length, aspect ratio, template, poster size) and record it
  via `ref add` with the source URL and date. TTL default 180 days for brands, 365 for a dated venue
  edition. No web tool or nothing found → record `facts: "unknown"` and ask the user; never guess.
  Stored in `<registry root>/references.jsonl`. This caches what interview-protocol's venue research
  already does, so it is done once, not per deck.

### 5. Privacy
- Closed key allowlist (PROFILE keys + observation vocabulary).
- `note` and `ref add` reject values matching PII deny-patterns: email, phone/ID/card-length digit
  runs (≥9 digits), street-address shapes, URLs with credentials/tokens.
- PROFILE facts (`profile-fact` notes and PROFILE accepts) additionally reject sensitive-category
  words about the USER — health, finances, religion, politics, sexuality, immigration/visa status
  (EN + ZH lists). Deck-content quotes are not topic-filtered: "the disease figure needs more colour"
  is a design note about a medical deck, not a fact about the user. Rejection prints
  why and stores nothing.
- All data under the registry root in the user's home; tests pin `$SLIDE_MAKER_REGISTRY` to a temp
  dir (repo precedent: every test pins `SLIDE_MAKER_TASTE_LEDGER`).
- `forget` removes a line from any store on request.

### 6. SKILL.md + references wiring (target ≤ +20 lines in SKILL.md)
- Step 0: one line — run `memory.py recall --step interview` before the first question; PROFILE
  pre-fills options (two-stage rule unchanged).
- Step 1 / 2 / 5: the Step-2 block's `taste_ledger.py list …` command becomes
  `memory.py recall --step design` (the block still requires `taste_applied`); Step 1 and Step 5 get
  one line each with their `--step`.
- Any step: one rule — when the user states a requirement or correction, `memory.py note` it.
- Step-6 close checklist: add `memory.py close <deck-dir>` → show its proposals per the consent tiers
  (§4a) → `accept`/`reject`.
- `references/user-taste.md`: PROFILE schema, observation log, proposals, refs, privacy (moved here,
  not into SKILL.md). `references/codex-runtime.md`: one line naming `memory.py recall` as the
  memory entry point. `references/file-inventory.md`: entry for `memory.py` (enforced by
  `check_inventory.py`).

### 7. Acceptance
1. `tests/test_memory.py` + a CI step in `.github/workflows/ci.yml` (same completion-grep pattern as
   `test_taste_ledger`). Covers: empty stores; neutral root (no Claude/Codex dir); `$SLIDE_MAKER_REGISTRY`
   override; CJK quotes and Chinese standing words; recurrence across 2 decks vs 2 notes in 1 deck
   (must NOT propose); conflicting direction → update proposal; staleness from `taste_applied`;
   expired ref; every deny-pattern rejected; recall output ≤ 50 lines with a full store and every taught rule present; reject is
   remembered.
2. Existing gates untouched: full local CI (`sm-ci`) GREEN before and after; `check_versions.py`,
   `check_inventory.py`, `check_skill_lossless.py` pass.
3. **Non-Claude run, as printed:** in a clean temp HOME with only the neutral root, follow ONLY what
   `memory.py` prints (`NEXT:` lines) through note → proposals → accept → recall, and confirm the
   accepted row appears in the next recall (project memory `next-step-commands-run-as-printed`).
4. Read the real output: recall blocks for each step on a seeded fixture store, read by eye.
No user decks are used as input; fixtures only.

## Approaches considered
- **A — extend + one entry point (chosen by the user).** Keeps every gate and schema; adds a PROFILE
  section, an observation log, a refs cache and `memory.py`. Cost: three stores remain, unified only
  at read time.
- **B — merge into one new store, `taste.md` generated.** Cleanest model; rejected because every
  reader/gate changes and the repo has hit schema-drift bugs twice.
- **C — host memory.** Not portable across agents; rejected.

## Decided by the user
- Approach A. External enrichment is in scope now.
- SKILL.md may grow a little, as long as an agent can still read it whole.
- Sensitive personal information is never stored; low-stakes, deck-relevant facts may be.

- Consent tiers: silent log · write-then-FYI for design dials/no-gos/looks · explicit yes for PROFILE
  lines and new ledger entries.

## Builder's calls (marked so the user can check them)
- `recall --step design` lists all active ledger entries (matches the existing gate; no gate change).
- Staleness data comes from `memory.py close <deck-dir>` snapshots, not from a deck index or gate hook.
- Fixed key vocabulary (rejecting unknown keys) rather than free-text keys — chosen so recurrence
  counting works without fuzzy matching.
- Closed direction set (more/less/require/avoid) + `--standing` flag; recall cap 50 lines with rules
  never truncated; sensitive-topic filter applies to profile facts only.
- Thresholds: ≥2 decks (unchanged from today), 3 consecutive skips, 12 months, TTL 180/365 days,
  log cap 300, PROFILE cap 8 lines.
- `memory.py` is the only new script; it imports `registry.py` and `taste_ledger.py`, does not copy them.
- Work happens on a new branch off `origin/main`; the installed copy is rsynced only after it lands.
