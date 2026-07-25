<!-- Extracted from SKILL.md Step 5 critic loop (L2003-2204) -->
<!-- This file is loaded on-demand when the corresponding Step runs. -->
<!-- SKILL.md retains a skeleton summary + pointer to this file. -->

# Critic Dispatch & Contract Card

> The actor-critic loop dispatch, Contract Card assembly specification, panel scaling rules, arbiter cross-validation, and primary-source gate.

---

Then run the **actor-critic loop** — this is the quality engine, and the critic is a
*demanding* judge (see `agents/critic.md`), not a rubber stamp:
1. **Critique.** Dispatch an independent critic subagent through the host's available
   multi-agent/subagent tool, pointed at `agents/critic.md`, giving it the rendered PNGs, the deck's **purpose + audience**
   (plus the interview's recorded **delivery mode + density choice**, so the rubric's density carves can apply),
   `references/review-rubrics.md`, the **motion manifest** from step 4 (so it can judge the
   motion *design* it can't see in a static render), **the CONTRACT CARD** (below), **and the
   source material** (so it can
   verify claims/figures/numbers, not just style). A *separate* agent matters: it judges the
   pixels, not your intentions. It returns structured JSON — `verdict`
   ("consent"/"revise"), per-slide `findings` (severity + concrete fix), strengths, the
   `plan_audit` + `probes` blocks, and (on a full-deck consent) a one-line `ceiling`.
   **Validate the review BEFORE acting on it (the anti-skim gate's consumer side):** run
   `python3 scripts/validate_review.py critic <json>` (schema conformance), then check
   `coverage.slides_opened` lists every slide in the critic's ASSIGNED scope (whole deck for a
   sole critic; its section's range for a per-section critic), `passes` covers both lenses on a
   sole critic, `stats_block_seen: true`, and `contract_card_seen` is not false when a card was
   sent. A review failing any of these is **rejected and re-dispatched once** with the gap named —
   never acted on. Arbiter outputs validate the same way (`validate_review.py arbiter`); an
   arbiter's `escalated_unreviewed` entries are handed to the next round's fresh critic as
   candidate findings (or, at the round cap, surfaced to the user with the other open questions).
   - **The CONTRACT CARD — assemble it at dispatch, from the approved plans (declarations only,
     never rationale).** A compact artifact the coordinator builds for every pipeline-built deck:
     the **deck memory sentence + emotional-curve line** (peak marked), the **per-slide
     takeaway / role / question / beat table**, the **claim ledger**, the **per-figure
     carrying-element rows**, **on a long-source deck the `source size:` line + the approved
     Source-coverage map** (the per-section disposition rows + the verbatim-vs-skimmed line — the
     critics judge completeness against its built-around/summarised set, NOT the whole book, and
     read a `cut` row as a conscious cut), **on a video-sourced deck the transcript status**
     (supplied-transcript locator, or the "video read visual-only — spoken content is a GAP" line),
     and the Design plan's **declared contracts** — the skeleton rhythm
     map, the WOW slide(s), the money slide (the slide the deck exists for), **the `boldness:` dial +
     the `signature move:` line INCLUDING its `carried_by:` slides** (so the distinctiveness lens can
     judge whether the declared risk actually landed in the pixels or got sanded back to safe — and,
     on the named carry slides specifically, whether the idea does structural work there or was
     merely stamped), **the branch's gate line** (`direction gate:` / `style gate:`, so a look that
     was never chosen from alternatives is visible as such) **with the picked composition tokens**
     (`cover <token> · home skeleton <token>` — the design lens checks the BUILT cover against the
     archetype the user picked, and the rhythm map's plurality against the picked skeleton), the semantic-colour
     ledger, the type tokens, the **`interior register:` cue** (the quiet register signature that
     repeats on interior slides, or `none (flat by register — <reason>)` — the critic's
     `register_interiors` check reads it), the motion manifest, the **chosen preset name + its `guard` string
     verbatim** (or `custom look — no preset guards`) (on the generated-template branch, plus the four identity-propagation contract lines — palette · type register · component geometry · surface), the **`signature proof:` token**
     (`slide N → <png>` or `skipped: <carve>` — so the critic compares the SHIPPED signature slide
     against the frame that was approved before the rest of the deck existed, and a silent skip is
     visible), the **`logo plan:` line with its evidence
     token**, the **checkpoint motif line** (device + meaning + legibility mode), the **approved
     image opt-in rows with their per-row source tokens** (+ license/credit notes and any declared
     stylized deviation), and — **when a Q4 style example is in play** —
     the **chosen mimic mode (A/B) + style-brief pointer** (so the design lens judges style against
     the right bar: a Mode-B restyle's deliberately-different palette is correct, not a fidelity
     miss). Like the motion manifest it extends, the
     card carries **intent the pixels can't show**: the judges verify the RENDER honors what the
     deck DECLARES — they never re-litigate the approved declarations themselves, and pixels
     always win over a kept-but-bad promise. Fidelity stays **source-first**: a ledger row is
     corroboration for a number, never a substitute for its source location.
     **On any post-first round driven by user feedback**, also fold in that round's **`user-dials:`
     line(s)** — a neutral record of *dimension → direction, layer — "the user's verbatim words"*
     (NOT prior-critic output, so the fresh-critic-unanchored rule below is untouched); it is the
     evidence the pendulum-overshoot check cites (`review-rubrics.md` §9), so the critic judges an
     overshoot against the user's actual words, not a reconstruction. For an external
     deck under review/redesign or a direction preview (no Step-1 plan exists), state
     "none-declared" explicitly in the dispatch instead.
   - **Consume the previous round's `strengths` as a do-not-harm ledger.** On every fix round,
     pass the prior critic's `strengths` array to the ACTOR alongside the promoted fixes,
     labeled: *"protected — do not degrade these while fixing; if a fix forces a trade-off
     against a named strength, declare it in the change manifest rather than trading silently."*
     Do NOT hand strengths to the next round's fresh critic — the whole-deck re-pass stays
     unanchored.
   - **Diff the critic's recorded probes against the plan (cheap, coordinator-side).** The
     critic returns per-slide `{first_read, takeaway_guess}` thumbnails probes and a
     `memory_sentence`. Flag a slide ONLY when its `takeaway_guess` is a bare topic label
     carrying no message, or lands on a different message/emphasis than the plan's recorded
     takeaway — a coarser-but-aligned guess passes; flag `memory_sentence` only when it "isn't
     close to" the planned deck message (the rubric's own bar). Anti-fabrication tell: per-slide
     guesses that echo the plan's takeaway phrasing verbatim/near-verbatim invalidate the probe,
     the same way a `slides_opened` gap invalidates the review. Disposition — never auto-revise,
     never a user stop: low-stakes → hand the mismatch back to the same critic in the same round
     to reconcile (raise the finding, or state in one clause why the probe passes); high-stakes →
     it enters the arbiter pass as a candidate finding like any other.
   - **Ceilings are contained.** On a panel, keep the single strongest `ceiling` and discard the
     rest (reason unrecorded — it is not a finding); ceilings are never sent to arbiters, never
     enter the fix list, and never trigger or extend a round — their only consumer is the Step-6
     hand-off line.
   - **Scale the critic to the stakes — and run it as a panel** (this is the main
     speed lever):
     - *Low-stakes* (research/lab meeting, work status update, teaching) → **two FOCUSED lens
       critics in parallel** — one **Lens A (content · fidelity · narrative)** and one **Lens B
       (design · layout · legibility)** per `agents/critic.md` §2, each applying **only its lens**
       (plus the shared high-recurrence box). Two focused agents catch far more than one generalist
       wading through all ~30 checks, at the same wall-clock; **skip the arbiter pass** for low-stakes.
     - *High-stakes* (conference, academic job talk / faculty interview, thesis
       defense, exec/stakeholder/pitch) → dispatch a
       **panel of 2–3 critics in parallel, each assigned ONE lens** from `critic.md` §2 (Lens A
       content/fidelity, Lens B design/layout, + optionally a back-of-room/audience pass), then **merge
       and de-dup** their findings — independent, *focused* reviewers catch far more than one, in
       parallel at no extra wall-clock. **Each critic reads `critic.md` but applies only its assigned
       lens, so no single agent carries the whole ~30-check brief** (the load split that prevents
       missed checks). **Scale the panel *within* high-stakes by length & scope, not just
       purpose:** a short single-paper talk (e.g. a ~10-min conference oral) takes the
       **light** end — 2 critics, and **skip the arbiter pass** below; a long, career-
       defining deck (a 45-min job talk, thesis defense, or investor pitch) earns the
       **full** 2–3-critic panel **plus** that arbiter cross-validation. For a **large/sectioned deck**, add **per-section critics plus one
       whole-deck critic for coherence/arc/seams**, then — after the arbiter pass below —
       **route only the *promoted* findings** back to the section that owns each slide
       (see `references/large-deck-orchestration.md`). Keep
       every critic **independent** — it judges the rendered pixels, it doesn't
       co-design; that independence is what makes consent mean something.
     - **Then cross-validate the findings before acting on them (full-panel decks above).** A
       merged panel is still a *union* of opinions: a critic can flag a number as wrong
       when it's right, or demand a change that would crowd a slide already at its
       legibility floor — and merging alone acts on that blindly. So add **one parallel
       pass of independent arbiters** (`agents/arbiter.md`) over the candidate findings,
       each judging only the rendered pixels + source — **handed the CONTRACT CARD too**
       (the fidelity re-derivation in `arbiter.md` is defined against the claim ledger and
       carrying-element rows it carries; the source stays ground truth): is the finding **real** (re-derive
       it — recompute the number, look at the actual pixels), and would its fix **help or
       hurt**? Promote to the fix list only what survives; **discard the rest with the
       reason recorded, never silently.** Because the costs are asymmetric, a **blocker
       survives unless arbiters actively refute it** (don't ship a wrong number because
       two agents shrugged "unsure"), and a **lone finding on a critic's home turf** —
       the content critic on a number, the design critic on overflow — is trusted even if
       only one critic raised it, so a real flaw isn't drowned by de-dup; a *minor* is **not sent
       to the arbiters** and the coordinator promotes it only when a clear majority of the
       *critics* independently raised it; a finding that is **real but whose fix
       hurts** is promoted with the arbiters' *better* fix, not dropped. The exact
       promote/discard rule lives in `references/review-rubrics.md` so it stays
       consistent. Net effect: the actor fixes real flaws, not phantoms. **Low-stakes
       skips the arbiter/confirmation machinery** — just the two focused lens critics, merge, one consent.
2. **Decide.** Stop as soon as `verdict == "consent"` (the critic would present it
   as-is) — not merely when the last round's issues are fixed.
   **At ANY stakes, reaching the cap with a surviving blocker/major is never a silent ship:**
   surface the unresolved finding(s) in the Step-6 note as an honest open question — the
   low-stakes analogue of high-stakes' "fail loudly at the cap" below. Cap the rounds by
   stakes so the loop converges fast: **low-stakes ≈ up to 2 rounds, high-stakes up
   to 3.**
   > 🔴 **One exception to "surface it and ship": a surviving `timid` / `sanded-to-safe`
   > distinctiveness finding on a deck whose `boldness:` is `bold` or `experimental`.** There the
   > deck does **not** ship on your say-so — after the one improvement attempt, put the choice to the
   > USER in two lines: *(a) one more round — naming the concrete change you would make; (b) ship
   > as-is, recorded as a knowing accept.* Either answer ships it; what changes is **who waives**.
   > A deck the user asked to be bold and received forgettable did not deliver what was asked, and
   > you are the party with an interest in calling your own output good enough. **This is the only
   > taste finding that can hold a deck, it needs the user's own dial set to `bold`/`experimental`
   > to fire, and it is never a floor** (a bold idea that broke legibility is a floor finding first).
   > At `balanced+`/`conservative`, unchanged: one attempt, then ship with the note.
   > **Record the outcome in the Step-6 hand-off note** — `distinctiveness: user waived (bold)` or
   > `distinctiveness: resolved in round N`. Without it, "they accepted it" and "I never asked" are
   > indistinguishable afterwards, which is exactly the hole the gate lines were added to close.
   > *(Owned by `agents/critic.md` distinctiveness axis + `references/review-rubrics.md`; all three
   > must say the same thing — this rule has a history of drifting apart across files.)* If the first render is already clean and the critic consents, you're done
   in one round — don't manufacture extra rounds. Otherwise apply the blocker+major
   fixes, rebuild, re-render.
3. **Repeat.** The critic **re-reviews the whole deck fresh** (fixes introduce new
   issues). Converge; keep a short record of what changed each round so improvement is
   visible, not just churn.

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
but never skip it entirely on a research-sourced deck: this is the gate between "the slides match
the ledger" and "the ledger matches reality." **Ordering:** run the
verifier pass in parallel with (or immediately before) the FINAL critic round; any WRONG /
PARTLY-WRONG fix re-enters the normal rebuild → re-render → re-lint path, and a fix landing after
critic consent gets a cheap confirmation look (the touched slides, not a fresh full round) — gate
fixes never count against the critic round caps. **The gate's artifact (required, per the enforcement
invariant):** the Step-6 hand-off carries one `provenance:` line — `N claims checked · N confirmed
· N fixed · N cut/hedged` — plus the per-claim verdict list on request; a research-sourced hand-off
without that line means the gate did not run (Step 6's checklist lists it). Decks built purely from the user's own material skip
this gate — there, fidelity is to the provided source, and item 10 already owns it — **but** a
source claim that §2(b) re-verification *updated or replaced* with a web-found current value counts
as research-supplied, and pulls the gate in for those rows.

**High-stakes only — verify the fixes and corroborate consent.** On re-render, the
arbiters cheaply re-check each promoted finding against the actor's **change manifest**
(what changed + which slides were touched): did the fix actually land *in the pixels*,
and did it regress a neighbour? **Hand this pass the previous critic's `strengths` list +
the manifest's declared trade-offs too — its Job-2 JSON carries a required `dulled` flag**
(did the fix buy its resolution by subtracting declared drama — a named strength degraded,
the hero/WOW demoted, a build removed?); `dulled: true` re-opens the finding with a
`better_fix`, exactly like `resolved: false`. A fix that didn't land **stays open** instead of
vanishing. And accept final consent only when the critic's `verdict == "consent"` **and**
a confirmation pass — a panel member who didn't author this round's edits, or one fresh
arbiter if the panel agreed in lockstep — sees no surviving blocker/major; consent should
be *corroborated*, not one agent's say-so. **Fail loudly at the cap:** if rounds are
exhausted and a *contested* blocker remains (the raiser calls it a blocker, the arbiters
can't refute it, or the confirmation pass splits), don't silently ship — hand the user
that one disagreement in step 6 as an honest question ("two reviewers disagree on whether
the Table 2 number matches the source — please confirm"). Arbitration is parallel breadth
*within* a round; it never adds rounds, and the caps above are unchanged. (Because it
removes phantom fixes and slide-thrash, expected rounds-to-consent often *drops*.)

