# User taste — the portable profile (`taste.md`), the dial ledger, and the write-back

One lifecycle, three parts. **`taste.md` is the durable store** (what this user has proven to
want across decks) · the **dial ledger is the per-deck observation stream** (WHY each iteration
round happened, in the user's own words) · **Step-6 write-back is the only bridge between them**
(durable dials promoted conservatively; consented looks mined into the registry). It exists so a
returning user never re-teaches a preference at the cost of a render-review round — and so a
one-deck guess never hardens into a standing rule.

## Table of contents
- Where it lives — and the empty-file rule
- Precedence — the profile seeds, it never decides
- The schema — fixed sections, HARD CAPS (whole file ≤ ~500 tokens)
- READ protocol
- WRITE protocol — conservative by construction (Step 6 only)
- Why this shape

## Where it lives — and the empty-file rule
`taste.md` sits at the **active template-registry ROOT** — `~/.claude/slide-templates/taste.md`
(Claude Code) · `~/.codex/slide-templates/taste.md` (Codex); if only one root exists, use it —
NOT inside this skill, because it is the user's personal footprint: portable across hosts,
theirs to edit or delete line-by-line. **A missing or empty `taste.md` is silently skipped** —
a brand-new user has NO footprint (the same rule as the empty registry), so never manufacture a
profile; create the file only when the first durable signal is written at a Step-6 close.

## Precedence — the profile seeds, it never decides
🔴 **MUST: `current request > this interview's answers > taste.md`.** The profile seeds
defaults, delegated picks, and the *substance* of the two-stage rolled-up options — it **never
overrides an explicit interview answer or a checkpoint decision**, because a memory that
outranks the user's live words is a cage, not a convenience. Host assistant memory is auxiliary
corroboration only and never overrides either. *(Gate: the Design plan's required
`taste profile:` line — a Step-2 design-gate precondition — records exactly what was applied,
so an override would be visible, not silent.)*

## The schema — fixed sections, HARD CAPS (whole file ≤ ~500 tokens)
An unbounded profile stops being readable at interview speed, so **prune at append**:

```markdown
# taste.md — <user>'s slide taste (portable · edit or delete freely)

## DIALS  (≤10 rows)
| dimension | position | evidence (deck · date · the user's verbatim words) |
|---|---|---|
| colour | vivid content, quiet chrome | cine-mri · 2026-06-14 · "太素了 — colour on the data, not the frame" |
| boldness | balanced+ (stable base + one signature move) | <deck · date · verbatim> |

*(`boldness` is a first-class dial — conservative | balanced+ | bold | experimental. It seeds the
design plan's `boldness:` line under an auto directive, per the same recurrence gate as any dial; an
explicit per-deck request still overrides it. The row above is illustrative — promote it only on real
evidence, like any other dial.)*

## NO-GOs  (≤5 lines)
- No white-card-block dominance ("looks like a template, not a design") — cine-mri · 2026-06-14

## LOOK HISTORY  (most recent 10 lines only — prune the oldest at append)
| date | deck | preset/look | canvas value | signature motif |
|---|---|---|---|---|
| 2026-06-14 | cine-mri | dark_tech | dark navy | k-space spiral |
```

- **DIALS (≤10 rows)** — durable design preferences, one row per dimension, each carrying its
  **evidence: deck · date · the user's verbatim words** — an unevidenced dial is an invention,
  and the quote is what keeps the profile auditable. Later conflicting feedback **UPDATES the
  existing row** (move the dial, `handoff-and-iteration.md`), never appends a contradiction —
  two rows arguing about one dimension is the diverging-sources-of-truth failure.
- **NO-GOs (≤5 lines)** — hard user vetoes, evidenced the same way.
- **LOOK HISTORY (10 lines)** — one line per delivered deck; the freshness input
  (`agents/slide-design.md` §1 varies at least one foundation against the LAST line).
- 🔴 **MUST — SCOPE EXCLUSION: design dials, NO-GOs, and look history ONLY; never
  workflow/mode directives** (the per-deck auto waiver, checkpoint skips) — SKILL.md settles
  those per-deck, and recording one here would silently carry an approval waiver across decks.
  *(Gate: the schema has no field that could hold one.)*

## READ protocol
- **Interview (Step 0).** Read `taste.md` alongside the registry. It surfaces **exclusively as
  the substance of the already-sanctioned two-stage rolled-up history options** (Q1 "one of
  your saved templates"; Q4 "like one of my previous decks", expanding to LOOK-HISTORY lines —
  praised looks first — on pick). It never auto-locks a choice and never adds new option
  shapes, so personalization still cannot crowd the general paths. Under a **per-deck auto
  directive**, the DIALS + NO-GOs seed the *delegated* picks — evidenced past preference is
  exactly what "derive, don't default" wants — and the first-FYI pick block names the dials
  applied, so a stale dial costs one glance to veto, not a build.
- **Design (Step 2).** The coordinator passes the **taste lines** — DIALS + NO-GOs + the LAST
  look-history line ("none on file" for a brand-new user) — into the slide-design dispatch.
  They feed §1 Freshness (something real to vary against) and the chrome-budget default;
  the interview's explicit answers and the LOCKED-look carve always outrank them. A dial
  **nudges craft choices** (colour placement, density, motion) — it never fixes a house
  palette (the vary-the-look rule still applies: sameness across decks is the failure to
  avoid) and never overrides purpose-driven restraint (`design-by-purpose.md` grants stated
  preferences their say, subordinate to per-purpose appropriateness).
  *(Gate — required field: the Design language section carries one line,
  `taste profile: <n dials applied / none on file> · freshness: varied <foundation> vs <last
  look-history line>`, or the alternate arm `look LOCKED (registered/provided template) —
  carve applies`; design self-verify (j) checks against it.)*

## WRITE protocol — conservative by construction (Step 6 only)
Writes happen **only at the Step-6 close**, only from recorded evidence, and **always with
user visibility**: every write is announced in **one FYI line** — *"recorded to your taste
profile: <the line> — say the word and I'll drop it"* — and the veto stays cheap because the
file is the user's own (edit or delete any line, any time). *(Gate: the Step-6 close checklist
in SKILL.md names write + FYI as ONE item — a silent write didn't happen.)*

**1) The dial ledger — the per-deck observation stream.** On each Step-6 user-feedback round,
the round record gains one `user-dials:` line per criticised dimension —
`dimension → direction, layer — "verbatim user words"` (e.g. `colour: +vivid, content layer —
"太素了"`). Zero cost when no iteration happens. It is also the evidence the pendulum-overshoot
check cites (`review-rubrics.md` §9) — the user's words fix which dial moved and how far.
Mechanics: `handoff-and-iteration.md` "Move the dial" + "The taste write-back".

**2) The promotion gate — dial ledger → DIALS row.** 🔴 **MUST — promote a dial into
`taste.md` ONLY on a durable, cross-deck signal:**
- **(a)** the user's own words mark it standing — "always", "一直", "in general", "for all my
  decks"; **or**
- **(b)** the **same dimension + direction appears in the round records of ≥2 distinct decks**
  — once is a deck-scoped correction, twice is a preference.
Everything else stays deck-scoped in that deck's record: a one-off content choice or a
purpose-driven correction promoted into a standing rule silently steers every future build —
the exact overfit the vary-the-look rule exists to prevent. *(Gate: a DIALS row without its
verbatim quote + deck + date is invalid by schema — nothing can be promoted without evidence.)*

**3) Look history.** Append **ONE line** for the delivered deck (`date | deck | preset/look |
canvas value | signature motif`), pruning to the 10 most recent — a named Step-6 hand-off
action, so next deck's freshness rule has a real record to vary against.

**4) Consented-look mining — registry parity.** When the deck's look was **freshly designed**
(Q1 branch (c), either sub-path — the one branch that invents a look and never saved it) and
isn't yet registered, **offer once at hand-off**: *"save this look to your registry as
<name>?"* On an **explicit yes** — never otherwise, and **skip the offer entirely under a
per-deck auto directive** (no un-consented registry writes) — copy the deck's `style.py` into
a new registry subfolder and write a `profile.md` per the existing conventions
(palette · fonts · build helpers · Origin), **distilling the final round's critic `strengths`
and any cross-round recurring finding dimensions into the existing Notes field** — hand-off
(after the critic loop) is the right moment because only then does the profile know what the
vetted deck *proved*. This is the same single persist that collaborative mode's Gate A 7(b)
names — one save, one owner, re-timed to hand-off. A look the user **explicitly praised**
("I love this one") additionally gets a `— praised` annotation on its LOOK-HISTORY line —
those lines lead when Q4's "like one of my previous decks" expands.

## Why this shape
The store is small and evidenced, so it stays trustworthy; the ledger is per-deck, so
observation is free; the bridge is gated on recurrence + explicit standing words, so the
profile converges on what the user *keeps* saying — memory without fossilization.
