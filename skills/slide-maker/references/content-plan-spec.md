# Content plan spec

## Audience brief — write this FIRST, and aim the gathering at it

🔴 **Before the comprehension brief, before any search: what do the people in the room have to
DECIDE, in the order they will face it, and what do they need in hand to decide each one?** That
list is the frame, and the frame is what aims the information gathering — so a wrong frame gathers
the wrong facts and every later gate passes.

    "audience_brief": {
      "who": "<who is in the room, and what they are about to do>",
      "decisions": [{"decision": "<what they must decide>",
                     "needs": "<what they need in hand to decide it>"}, …]
    }

At least three decisions, each with its `needs` — the `needs` half is what does the aiming; a
decision with no stated need gathers nothing. Contract, carves and messages:
`scripts/audience_brief.py`, imported by `deck_gates.py`, `render_deck.py --gate-check` and
`codex_delivery_gate.py`.

🔴 **On a NO-SOURCE deck this REPLACES the comprehension brief below.** There is no source to
comprehend; a brief written anyway becomes a summary of the SUBJECT, and that is the failure this
field exists for. Measured: a deck built from `audience = people planning a trip` and `goal = they
leave able to plan one` shipped a thesis on an 1837 land survey, because Step 1 described the city,
the arc candidates were all generated inside that frame, and the winner was scored on elegance
rather than on the recorded goal. The research followed the frame — chain lengths and inscription
years verified, daily cost and distances never asked for.

**The test when you cannot tell which you have written:** read the takeaway spine top to bottom. If
it reads as true statements ABOUT the subject rather than as answers to what this room must decide,
the frame is wrong. Patching the missing topic onto it fixes the symptom and keeps the frame.

### …and the questions those decisions will be asked as

A room that has to decide something asks about it. So the audience brief is also where the
anticipated questions come from: for each decision, what will they push on that the deck does not
already answer on a slide? Those are the **backup slides** — built, parked after the close, and
LINKED, because a prepared answer you can only reach by arrowing past everything in between is one
that goes unused. Record them beside the plan and the built deck is checked against them:

    "qa": [{"question": "Why not compressed sensing as the baseline?", "slide": 14}, …]

`references/navigation-and-qa.md` owns the components (`dk.link` · `dk.agenda(targets=)` ·
`dk.back_link`) and the gate. Optional by design — a deck nobody interrupts needs none — but on a
defense, a committee, a grant panel or a board readout, the decision list has already told you what
the questions are.

**If the deck cites published work**, the same step records the bibliography rather than retyping
from it: `"citations": {"bib": "refs.bib", "style": "numeric", "keys": [...]}` in cited order, with
`references/citations-and-bibliography.md` for the craft. The marker on the slide and the line on
the references page are then derived from the same .bib entry, which is the only way a year cannot
drift between them.

## Comprehension brief — the required fields and the claim-ledger columns

- The **one-sentence message** + the verbatim source sentence it derives from (+ where).
- The **contributions**, in their words, each with its source location.
- The **method essence** at talk-altitude (+ the one key equation), and where it appears.
- **One row per figure AND table:** `id | what it is FOR (the ONE comparison) | which exact
  element carries it (row/column/curve/panel) | what it emphasises | the WRONG reading to avoid`.
  A table exists to make one comparison obvious — foreground *that* (e.g. baseline vs +X), and
  name the carrying element (it drives which row the build highlights + the assertion title).
  A figure whose carrying element you cannot name is one you haven't understood.
- Any **nuance/limitation** the authors stress, quoted.
- 🔴 **The OPEN ledger — every claim the SOURCE ITSELF marks as NOT yet established**, one row:
  `claim | where the source says so | absent from the deck, or stated AS OPEN on slide N`.
  Sweep for the source's own hedges: *future work · next steps · a roadmap · a gate · "cannot
  establish" · "not yet" · "to be tested" · TODO · an untested flag*. **A row here may never appear
  on a slide in the established voice.** This is a DIFFERENT failure from inventing: the fact is
  really in the source, promoted from hypothesis to result — which the never-invent rule and the
  claim ledger both wave through, because the claim *is* traceable. Measured on a delivered
  research deck: a slide asserted that extra respiratory bins helped the reconstruction while the
  source listed *"tests whether each bin helps"* as an open gate; an expert room catches that
  instantly and it costs the whole deck's credibility. `[]` is a legitimate value — it records that
  the sweep happened. Recorded as `content.open_ledger`; `deck_gates.py check` blocks the missing
  KEY, never the count.
- A **claim ledger** (per `content-planner.md` §2): every number/date/name/citation/superlative/
  dated-event as a row with source + verbatim value + verified?(Y/N) + as-of date; an unverifiable
  claim is cut or marked open, never shipped.

## Web verification & no-source decks (incl. grounding to today)

- **No content:** draft an outline from your own expertise, then **ground *and verify*
  it** with the host's available web search/fetch tools (Codex: use `web.run`) — treat this as a **fact-check, not just framing**.
  List the deck's specific *falsifiable* claims (numbers, dates, names, citations, and
  every "first/largest/state-of-the-art" assertion) and confirm each against its **primary**
  source (the planner's PROVENANCE CONTRACT, `agents/content-planner.md` §2 — an aggregator
  or news rewrite is not confirmation) before it lands on a slide; fix or cut anything you
  can't verify, and never
  present an unverifiable claim as established fact. This matters because a no-source deck
  has **no paper to anchor it** — *you* are the only check on whether a confident-sounding
  statement is actually true, and an expert audience spots a wrong "fact" instantly (the
  failure mode here is being *wrong*, not just vague). **If the host exposes NO web tool** (no
  search/fetch available), do not present falsifiable claims as established: mark each such claim
  *open/unverified*, soften it to what you can defend, and **ask the user to confirm the numbers or
  supply a source** — never ship an unchecked "fact" just because you couldn't check it.
  - **Ground to *today* — the current day, not just the year — and re-verify on every build.**
    You know today's date; use it: run **recency-bounded** searches (this month / the last few
    weeks for fast-moving topics) and fold in material recent events. Re-check anything
    **time-bound** *every* build (including a regeneration) — never reuse cached research for it
    (cached is fine for *stable* facts): prices, counts, rankings, role-holders, versions,
    status; "current / latest / upcoming" claims; "first / largest / record" superlatives; and
    any **scheduled / dated event** (launch, release, ruling, earnings, election, deadline). For
    a dated event, check whether it has **already happened as of today** and write the correct
    status/tense — a "planned / upcoming" item whose date has passed is **completed**; a
    "leading / latest" thing may since have been superseded. Date the deck **"as of \<day month
    year\>"**; if the newest *full-year* metric is last year's, label it and add the current
    year-to-date figure rather than presenting old data as current.
  Carry the verified outline + source log into the **Content plan**, where the user
  approves it — a no-source deck is gated the same as any other: once at the CONTENT
  checkpoint (Step 1), then again at the DESIGN checkpoint (Step 2).

## Long-source mode — classify, map, triage, deep-read the load-bearing 20%

- **A long source (a book / very long PDF / large corpus / multi-volume set)** — one you can't read
  faithfully in a single pass — is NOT read front-to-back: a faked linear read either overflows or,
  worse, *fits* and goes shallow, then invents plausible-but-absent points. Run the planner's
  **Long-source mode** (`agents/content-planner.md` §1): (1) **classify size deterministically** —
  PDF/EPUB → `python3 scripts/extract_pdf.py map <src>` (CJK-correct load + token estimate); `.docx`/
  `.md`/Google-Doc/web → convert to PDF first or use a `wc`-style count (**never raw `wc -w` on CJK
  text — it undercounts ~6–30×; count CJK chars ÷ 2 + Latin words, or convert to PDF and let `map`
  do it**); a code repo → size the file
  tree; **multi-file → sum across files** (once the set is over-threshold, convert every non-PDF
  member `office`→PDF so pages/provenance exist uniformly) — recorded as the brief's `source size:`
  field; over
  ~40–50 pp (or a token estimate that won't fit one pass) FORCES the mode, (2) anchor on purpose FIRST,
  (3) **map the structure** — TOC/bookmarks + density; **no TOC? `extract_pdf.py headings <src>`**
  reconstructs a skeleton by font-size outlier (recorded in the plan), (4) read **only the chapters
  you'll build-around/summarise** into page-tagged notes (`extract_pdf.py text <src> <start> <end>`;
  fan out the *reading*, synthesise as one mind; `cut` chapters are dispositioned from the skeleton,
  unread), (5) **deep-read *verbatim* only the load-bearing ~20%**, tracing every slide-bound claim
  to a real page (`<file>:p.NNN`; a chapter note is corroboration, not a source), extracting figures
  **per page** from the plan's locators (never `autofig` the whole book). The plan then carries a
  **Source-coverage map** (every skeleton section → built-around / summarised / cut) so the SELECTION
  is explicit — on a book the biggest risk is building around the *wrong slice*, not misreading one
  figure. **Dispatch mechanics — the selection FYI must land BEFORE the deep-read, so an
  over-threshold source makes the planner dispatch TWO-PHASE:** phase 1 (steps 0–3) returns the
  `source size:` + skeleton + draft coverage map, the coordinator posts the selection FYI in chat
  (a stop normally, an FYI under the auto-waiver) and gets the slice confirmed/adjusted, THEN phase 2
  (steps 4–6) runs the verbatim deep-read on the confirmed slice — a one-shot dispatch has no user
  channel mid-run, so a single-phase dispatch silently converts the "early" FYI into a post-hoc one
  (the plan records `selection FYI: posted <when> · slice confirmed/adjusted`, which the checkpoint
  precondition checks). An inline-run planner just posts the FYI directly at the same point.
  A **scanned / image-only or DRM-locked** PDF yields no extractable text (`map`/`text` print
  a `⚠ NO extractable text` warning) — say so and ask for a text version, OCR, or the specific
  chapters, never hallucinate the contents.

## Research budget and the primary-source gate (moved here from research-budget.md)

Read this BEFORE any web research or research fan-out, and before handing off a research-sourced deck. Moved verbatim from SKILL.md (2026-11-07).


### Search budget, primary-source gate, ordering

**🔴 THE SEARCH BUDGET IS A SHARED, SESSION-SCOPED, NON-RENEWABLE RESOURCE — spend it like one.**
Web search is capped per SESSION (Claude Code: `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`,
default 200), the cap is shared with every subagent you dispatch, and **it does not reset between
decks in the same conversation.** Measured: one research fan-out — 12 research agents plus 7
verifiers, each searching freely because nothing told them otherwise — consumed the entire 200.
Nothing metered it and nothing warned; the exhaustion surfaced hours later, on a different task,
when a single lookup for a company's official logo could not run. The deck that needed that logo
shipped without it and said so on its own limitations page. That is the shape of the failure:
**the cheap, late, small lookups starve, because the big early fan-out took everything.**

Three rules, in order of how much they buy:

1. **Do the SMALL, NAMED lookups FIRST — before any research fan-out.** The logo, the brand
   colours, a licensed photo, one specific clearance number: these are a handful of searches, they
   are the ones that get starved, and they are needed by Step 2 anyway. Front-loading them costs
   nothing and removes the failure entirely.
2. **Budget the fan-out explicitly and say the number in each dispatch.** An agent with no stated
   cap searches until satisfied, and N of them do it in parallel. Write it into the prompt —
   *"you have at most 6 searches; spend them on the claims you cannot resolve any other way"* —
   and size the round so the whole fan-out stays under roughly **half of what REMAINS — not half of
   the original cap**. Half, not all: verification, mid-build fact-checks, and asset sourcing all
   still have to happen. *(Remains, not original, because the cap is SESSION-scoped and does not
   reset between decks: on the second deck of a conversation "half the cap" can be more than
   everything left. Step 1's dispatch rule says the same thing in the same words — they are one
   rule stated at the two moments it binds, so change one, change both.)*
3. **Record what you planned and what you spent**, so exhaustion is a number someone chose rather
   than a wall someone hit. When the budget IS gone, say so in the deck's limitations and in the
   hand-off — never let a missing fact read as an absent fact.

**🔴 PRIMARY-SOURCE GATE — research-sourced decks only, before hand-off.** When the deck's
load-bearing claims came from **web research** (every no-source deck, and any sourced deck where
research supplied slide-level numbers/quotes), the content critic verifying slides *against the
ledger* is not enough — a hallucinated or secondhand ledger row passes that check by construction.
So before hand-off, run one **adversarial primary-source spot-check**: independent verifier
agent(s) with live web access take the deck's load-bearing claims (every headline number, date,
direct quote, ranking, attribution) and try to **REFUTE** each against its **primary source** (the
original paper / the org's own post / official docs — never an aggregator), returning per claim
`CONFIRMED (URL) / WRONG / PARTLY-WRONG / UNVERIFIABLE`. **WRONG and PARTLY-WRONG are fixed before
ship; UNVERIFIABLE is hedged as unverified or cut — never shipped as established fact.** While
there, verifiers also flag the planner's PROVENANCE CONTRACT breaks (spliced figures, quote-mark
abuse — `agents/content-planner.md` §2, rubric item 10). Scale it to stakes like the critic itself
(a quick deck: one verifier over the top ~10 claims; high-stakes: a fan-out over all of them) —
**and the user's `review:` tier is the handle on that same scale** — `fast` = the top ~5 load-bearing
claims, `standard` = the top ~10, `thorough` = all of them. The tier narrows the SAMPLE and never the
gate; on a research-sourced deck the gate runs at every tier that RUNS —
this is the gate between "the slides match the ledger" and "the ledger matches reality."
**The one exception is `none` at the post-build question:** the user declined the whole review
loop with the deck visible, and this gate rides on it. That is the single most consequential thing
`none` gives up — a wrong number is the one defect the user's own eyes cannot catch — which is why
`none`'s option text on a research-sourced deck must SAY it skips this, and the hand-off's
`provenance:` line must read `skipped — user declined post-build review` rather than a tally.
**Ordering:** run the
verifier pass in parallel with (or immediately before) the FINAL critic round; any WRONG /
PARTLY-WRONG fix re-enters the normal rebuild → re-render → re-lint path, and a fix landing after
critic consent gets a cheap confirmation look (the touched slides, not a fresh full round) — gate
fixes never count against the critic round caps. **The gate's artifact (required, per the enforcement
invariant):** the Step-6 hand-off carries one `provenance:` line — `N claims checked · N confirmed
· N fixed · N cut/hedged` — plus the per-claim verdict list on request; a research-sourced hand-off
without that line means the gate did not run (Step 6's checklist lists it). Decks built purely from the user's own material skip
this gate — there, fidelity is to the provided source, and item 10 already owns it — **but** a
source claim that §2(b) re-verification *updated or replaced* with a web-found current value counts
as research-supplied, and pulls the gate in for those rows. **When a `provenance` record carries rows
confirmed against the user's own material** (a mixed deck, or one that records them anyway), such a
row cites that file instead of a URL — `{"claim": "…", "verdict": "CONFIRMED", "source": "<path to the
user's file, relative to the deck folder>"}` — and the gate checks the file exists; a web-researched
claim still needs its primary-source `url`. **A deck built from the user's material skips the web
spot-check but NOT the number trace:** `content.sources` + `source_check.py` (Step 1) hold every slide
number to those files at the gate, on both runtimes, and the hand-off's `provenance:` line carries its
tally (`N numbers traced · N rounded · N derived · N from images (not machine-checked) · N material
findings resolved`).

