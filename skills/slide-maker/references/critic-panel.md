# Critic panel

## The CONTRACT CARD — full field list

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

## Handling a returned review — strengths, probes, and ceilings

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

## Review effort tiers — what the user's one word actually dispatches

The stakes-derived composition below is the **default**. Step 0 collects a one-word `review:` tier
(`fast` | `standard` | `thorough`, derived from purpose per `references/interview-protocol.md`)
that may move it. The tier scales the **weight** of the loop; it can never scale away its
**existence** — see the floors at the end of this section.

| | `fast` | `standard` | `thorough` |
|---|---|---|---|
| critics per round | **1 generalist**, carrying BOTH lenses | **2 focused**, one lens each | exactly what "Panel composition by stakes" below already prescribes for high-stakes, including its light-vs-full sub-scaling by length and scope |
| arbitration | none | **none** — identical to today's low-stakes | per that same section: skipped at the light end, full cross-validation on a long/career-defining deck |
| round cap | **1** | 2 | 3 |
| round-2 scope | n/a | a **full fresh** whole-deck re-review | a **full fresh** whole-deck re-review |
| consent | the critic's own | the critic's own | corroborated, wherever that section already requires it |
| provenance sample | top ~5 load-bearing claims | top ~10 | fan-out over all of them |
| measured order of magnitude | ~6 subagents · ~250k tok | ~12 · ~600k | ~32 · ~2M |

**`standard` and `thorough` are pure ALIASES for today's low-stakes and high-stakes — every cell
above either restates that section or defers to it.** That is the whole safety property of this
dial: it renames two behaviours the skill already had so a user can *reach* them by word, and adds
exactly ONE genuinely new band, `fast`. Nothing about a deck whose user says nothing changes.
🔴 **`fast` is therefore OPT-IN ONLY and is never DERIVED** — no purpose, however small the ask,
defaults to it. A user has to ask for it, which is what makes the recall drop below a consented
trade rather than a silent downgrade.
*(An earlier draft also had `standard` narrow round-2 to the changed slides and gain a "triggered"
arbiter pass. Both were dropped: the first is rejected by the review-validation gate, whose
`slides_opened` scope buckets are whole-deck and per-section only, so a scoped round 2 bounces and
costs an extra round instead of saving one; the second contradicts four surviving statements that
low-stakes dispatches no arbiter at all, including `agents/arbiter.md`'s own brief. Either could
return later as its own change that edits every one of those files — neither belongs in a dial
whose value is that it changes nothing by default.)*

**When no tier was collected — treat it as `standard`, and say so.** Three paths reach Step 5
without Step 0's purpose question ever running: a redesign (whose R0 keep-or-restyle answers
REPLACE the template question), a critique of an existing deck with no rebuild, and any external
deck with no Step-1 plan. On all three the tier is `standard` and the hand-off records
`review: standard (no tier collected — <which path>)`. A tier that is silently undefined is how a
default becomes whatever the run happened to feel like.

**🔴 Two shapes no tier may alter, because they are not weight.** (1) On a **large/sectioned
deck**, the per-section critics plus the one whole-deck coherence critic run at EVERY tier
(`references/large-deck-orchestration.md`) — the tier moves rounds and the provenance sample, never
the sectioned panel shape; a 40-slide deck reviewed as one document is not a cheaper review, it is
a different and worse one. (2) **Corroborated consent stays required wherever the stakes section
requires it.** A user word may buy fewer rounds; it may not buy consent that nobody checked on the
deck class where that check gates shipping.

**Report the bill.** A dial the user sets but never sees the cost of builds no intuition, so the
Step-6 hand-off carries a `cost:` line (subagents · tokens · wall-clock) beside the `review:`
line — `references/handoff-checklist.md` owns both.

## Panel composition by stakes, and arbiter cross-validation

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

## High-stakes — verify the fixes and corroborate consent

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
