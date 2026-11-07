# Research budget and the primary-source gate

Read this BEFORE any web research or research fan-out, and before handing off a research-sourced deck. Moved verbatim from SKILL.md (2026-11-07).


## Search budget, primary-source gate, ordering

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
