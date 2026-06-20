# Review rubrics — judge a deck against its PURPOSE

A deck is only "good" relative to why it exists and who's in the room. The same
slide that's perfect for a Monday lab meeting is wrong for a conference keynote.
So the critic always reviews against (a) the **universal rubric** below and then
(b) the **purpose overlay** that matches the deck's context.

These criteria are grounded in established presentation research, not invented:
- **Assertion–Evidence** (Michael Alley, Penn State): the title is a full-sentence
  *assertion* (the slide's one message); the body is *visual evidence*, not a
  bullet list. Empirically improves comprehension, recall, and lowers cognitive load.
- **Mayer's multimedia principles**: coherence (cut anything that doesn't serve the
  point), signaling (highlight what matters), redundancy (don't make them read text
  that duplicates narration), spatial contiguity (labels next to what they label).
- **Conference-talk consensus**: one take-home message, big legible visuals over
  words, time discipline, forecast → tell → summarize.

## Table of contents
- [Universal rubric](#universal-rubric) — always applied
- [Severity scale](#severity-scale)
- Purpose overlays:
  - [Research meeting with supervisor / advisor](#progress--lab-meeting)
  - [Work status update to a manager / boss](#work-status-update)
  - [Academic conference talk](#academic-conference-talk)
  - [Academic job talk / faculty interview](#academic-job-talk--faculty-interview)
  - [Company / stakeholder / exec presentation](#company--stakeholder-presentation)
  - [Product description / pitch](#product-description--pitch)
  - [Thesis / committee defense](#thesis--committee-defense)
  - [Teaching / instructional](#teaching--instructional)

---

## Universal rubric
Score each dimension; cite specific slides.

1. **One idea per slide.** Does each slide carry a single, identifiable point? Two
   messages on one slide = split it. Title should state that point (ideally an
   assertion, e.g. "Only the warp needs to be 3D", not a topic like "Method").
2. **Results legibility.** This is the one people get wrong most. Can the audience
   *actually see* the evidence from a normal viewing distance — figures large
   enough, key differences pointed at, in-figure labels readable? A results slide
   whose claim can't be verified from the image is a blocker.
3. **Cognitive load / text.** Few words per point; no paragraph the audience must
   read while the speaker talks. No text that merely duplicates what's said.
4. **Figures labeled & intact.** Every figure has a legend (what rows/cols/axes are) and
   a one-line takeaway (what to notice). Unlabeled figure = major issue. Also check the
   figure is **intact**: none of its own parts — legend, colour bar, axis labels/ticks,
   title, units, outer rows/columns — is clipped by a crop or by the slide placement (a
   half-cut legend is the classic miss), and the figure isn't **chopped into pieces that lose
   the authors' context** (prefer the whole, integral figure; a narrowed crop that changes
   what was shown is a real finding).
5. **Signaling.** Is the eye guided to what matters (arrow, box, color, bold), or
   is everything the same weight?
6. **Narrative flow.** Do the slides form an arc (problem → idea → method →
   evidence → so-what)? Are there gaps or non-sequiturs between slides?
7. **Visual quality.** Contrast (text vs. background — aim for ≥4.5:1, so light-grey
   text on white or low-contrast figure labels are flags), consistency (fonts, colors,
   alignment), whitespace (not crammed, not awkwardly empty), no overflow/clipping. Is
   any meaning carried by **colour alone** (a plot legend or status distinguished only
   by hue)? Pair it with a label/shape/marker so it survives projection and colour-blind
   viewers.
8. **Framing.** Does an unprepared audience member know, early, *what this is about
   and why it matters*? Or does it start mid-method?
9. **Layout, figures & colour** *(applies to every purpose — a lab-meeting or exec
   deck is judged on this just like a conference talk).* When the source already has
   a figure (architecture, results, a chart), is it shown **whole** rather than
   partial-cropped or hand-redrawn (redraws risk dropping/mis-stating detail)? Is
   there breathing room — a consistent gutter between figures and text, nothing
   crammed, **and no two elements overlapping** (a figure encroaching on a table/text)?
   On **split layouts** (text + figure, two-up, image + caption), are the left and right
   regions — *and the white margins flanking them* — the **same width** (or a clearly
   intentional asymmetric split with equal outer margins)? Unequal panels or a lopsided
   left-vs-right white margin is a real finding, not a nitpick.
   Is text inside filled boxes (callouts, chips, takeaway bars, cells) **optically
   centred**, not hugging an edge or sitting a touch low? Does colour vary with intent,
   or is everything one monotone accent? Is the closing slide named for its purpose
   ("Conclusion" for a talk, "Next steps" for a status update — not a generic "Take home")?
10. **Factual fidelity** *(when source material exists — the check every system fails).*
   Does every number, label, and headline claim trace back to the source? Does the deck
   represent the source's *actual emphasis* (e.g. a comparison table foregrounds the
   authors' comparison — baseline vs. the proposed thing — not a distracting one)? A
   caption that disagrees with its figure, a wrong number, or an over-claimed trend is a
   **blocker/major**, not a nitpick: it misleads the audience and exposes a shallow grasp
   of the material. **Allowed exception — forward-looking content:** a *future work /
   next steps / the ask* slide may carry content not in the source, **if** it is clearly
   flagged as proposed and follows correctly from the material. Don't flag a
   properly-flagged forward-looking slide; *do* flag forward-looking claims dressed as
   established fact, or fabricated traction/market numbers presented as real.
11. **Design fits the purpose.** Does the look match the deck's purpose and audience —
   crisp/corporate for a status update, sober/formal for a defense, bold/on-brand for a
   product pitch, warm/clear for teaching (see `references/design-by-purpose.md`)? A
   purpose-mismatched look (or a generic default palette shipped for a high-polish
   pitch/exec deck) is a real finding. Judge against this purpose, not a generic ideal.
12. **Motion & pacing** *(applies to every purpose, not just talks).* Was the pacing
   decision *made deliberately* — animating only the slides a build genuinely helps, and no
   more? Two failure modes count: under-design (shipped static because nobody looked) and the
   more common over-application (a build on every slide, or motion added for polish). Two
   checks, read against the
   **motion manifest** (the static render can't show a reveal sequence, so judge the design,
   not the playback): (a) a calm **deck-wide transition** is the default — its absence with no
   stated reason is a minor finding; (b) any slide that is clearly a **pipeline / multi-stage
   diagram, a multi-part argument, or an evidence→takeaway** shown all at once, where a
   step-by-step build would help the audience follow — left static with no reason — is a real
   finding (typically major for a *presented* talk, minor for a read-alone deck). Calibrate:
   title/section/one-idea slides and side-by-side comparisons *should* be static; most
   individual slides stay static; "static, because X" is a valid answer. You're enforcing
   that the pacing decision was *made*, never that everything animates — **over-animation is
   equally a finding**: a build on a slide that gains nothing from one, motion added for
   polish/consistency, or builds on most slides reads as needless and is a real flaw (flag
   it and say which slides should revert to static). A cluttered
   *final built* state is still a layout finding, not a motion one — animation never excuses it.
12a. **Generated-image restraint** *(when the deck uses AI-generated plates).* Generated
   images should be *sparse and purposeful*, not one-per-slide. Flag **over-use** — a
   decorative plate on most/every slide, a generated image where a source figure / real
   computed artifact / chart / plain whitespace would serve better, or imagery that competes
   with the slide's text. (Fidelity violations — readable text, fake charts/labels/logos, or
   a generated image standing in for evidence — are blockers under item 10, not this one.)

## Severity scale
- **blocker** — undermines the deck's purpose (e.g. results illegible at a
  conference; buried recommendation for an exec). Must fix before sharing.
- **major** — clearly hurts comprehension/impact (unlabeled key figure, two ideas
  on a slide, wall of text).
- **minor** — polish (uneven spacing, a slightly long title, ellipsis ambiguity).
Consent to ship when there are **no blockers and no majors** (minors are optional).

## Finding-level cross-validation (high-stakes only)
For high-stakes decks the panel's merged findings are **adjudicated by independent
arbiters** (`agents/arbiter.md`) before the actor fixes anything — and the promote/discard
rule lives *here* so SKILL.md and the arbiter point at one place and never re-specify it.
The costs are **asymmetric** — acting on a phantom flaw wastes a round and can damage a
correct slide, but shipping a real blocker is worse — so this is **not** a flat majority:
- **Promote** a finding the arbiters call **real and not-hurts**.
- A finding that is **real but whose fix hurts** is promoted with the arbiters'
  *substituted better fix* — the problem is real, only the prescription was wrong.
- A **blocker survives unless arbiters actively refute it** — don't drop a wrong number
  because two agents shrugged "unsure".
- A **lone finding on its home turf** is trusted at raise-count 1 — the content critic
  owns numbers/claims/emphasis, the design critic owns layout/contrast/legibility/
  overflow, the audience critic owns back-of-room readability/jargon — so a real flaw only
  one critic caught isn't drowned by de-dup. (*Narrative/arc/flow* is a shared deck-level
  lens, not any one critic's turf — a lone narrative finding falls under the general
  majority rule, not raise-count-1 trust.)
- A **minor** is **not sent to the arbiters** (not worth an agent); the coordinator
  promotes it only when a clear majority of the *critics* raised it.
- **All-unsure on a major → keep, flagged "unverified"** (skepticism is the default).
- **Discard** only `false_positive` / `hurts` findings — each with the arbiters' reason
  kept in the round log, never silently.

After fixing, each promoted finding is **verified in the re-rendered pixels** (resolved +
no regression). Final consent requires a **second independent pass** to agree there's no
surviving blocker/major; a *contested* blocker that survives the round cap is **surfaced
to the user, not silently shipped**. This whole layer is a **no-op for low-stakes** decks
(one critic, one consent).

**Language consistency.** The deck should be in one language throughout; flag accidental
mixing (a stray heading/label/bullet in another language, or drift between slides) unless
the user asked for a bilingual/mixed deck. Technical terms, proper nouns, acronyms, units,
and code left in their original form are fine — not violations.

**Direction previews (collaborative mode).** When you're reviewing *archetype preview
slides* for a direction gate (not a full deck), only the design dimensions apply —
2 results-legibility, 5 signaling, 7 visual-quality, 9 layout/figures/colour, and
11 design-fits-purpose, plus consistency across the archetypes. **Skip** narrative/
framing/fidelity and content-completeness — it's a style sample, not the deck;
`consent` = "strong and on-purpose enough to show the user."

**Animation / builds.** Judge the *final built state* shown in the render (static PNGs
can't play a sequence). Never treat the absence of animation as a flaw, and don't demand
it — most slides should stay static. Two kinds of animation finding exist: (a) a
**cluttered final state** — a slide that would only look clean mid-build is relying on
animation to hide crowding (fix the layout, not the timeline); and (b) **over-application**
— a build on a slide that gains nothing, motion added for polish/consistency, or builds on
most slides; flag it and name the slides that should revert to static (see item 12).

---

## Progress / lab meeting
*(Research meeting with supervisor / advisor.)*
*Audience:* supervisor/advisor + labmates who know the project. *Time:* short (5–10
min). *They want:* what's new since last time, whether it works, what's blocked,
what's next. Honesty over polish.
- **Weight heavily:** clear "what I did / what I found / what's next"; honest
  results including negatives; blockers stated; correct technical depth (don't
  over-explain known background).
- **Relax:** high visual polish, broad-audience framing, motivation slides — they
  know the context.
- **Red flags:** vague status ("rerunning, sth wrong"); no explicit next step; results shown without saying whether they're good; burying the one new result among old recap.

## Work status update
*(Daily/weekly update to a manager or boss at work — not a research advisor.)*
*Audience:* a manager who cares about deliverables, timelines, and risks more than
method internals. *Time:* very short. *They want:* are we on track, what shipped,
what's at risk, what you need.
- **Weight heavily:** outcome/status first (done / on-track / at-risk, ideally
  colour-coded); progress against the goal or timeline; risks/blockers with the ask
  ("need X from you"); impact in business terms; tight, scannable.
- **Relax:** method depth, derivations, research nuance — a manager rarely needs them.
- **Red flags:** activity dump with no status verdict; no risks/asks surfaced;
  technical detail with no "why it matters for the goal"; no clear next milestone.

## Academic conference talk
*Audience:* peers in the field but NOT in your subfield. *Time:* strict (often
12–15 min). *They want:* one memorable message, why it matters, convincing evidence.
**First, know the venue:** different conferences impose different talk lengths,
slide aspect ratios, and norms — research the specific conference (step 0) and
judge against its actual guidelines and official template if one exists.
- **Weight heavily:** conformance to the venue's rules (time, aspect ratio, any
  required template/format); a single take-home message, stated early and repeated;
  motivation/significance accessible to adjacent fields; method at the right
  altitude (intuition + one key equation, not every detail); **big, legible,
  annotated results**; limitations; notation defined before use; realistic time
  budget (~1 slide/min); a clear closing "what to remember".
- **Relax:** exhaustive implementation detail (push to backup slides).
- **Red flags:** ignoring the venue's format/time rules; no single message; dense
  derivations; tiny unreadable result figures; jargon undefined; too many slides
  for the time; ending on "Thanks" with no recap of the contribution.
- **Webinar / online variant:** judge with this same overlay, but for a *shared-screen*
  medium — additionally weight larger type, a light background, key content in the central
  safe area (edges/bottom get cropped by meeting UI), more/lighter slides to hold a remote
  audience, and chat-interaction prompts; every slide must also read as a recorded still
  (see `references/design-by-purpose.md` → Webinar).

## Academic job talk / faculty interview
*(A candidate presenting their research **program** + vision + fit to a hiring
department — not one paper to peers, but "hire me for the next decade." Longer and
more personal than a conference talk.)*
*Audience:* the **whole department** — the search committee plus faculty from far-off
subfields, postdocs, and grad students; most are *not* in your niche and some control
your tenure case. *Time:* long — typically a ~45-min talk in a 60-min slot, with real
Q&A reserved. *They want:* to answer three questions — *is this a first-rate researcher
with a vision?*, *can they teach/communicate to a broad room?*, and *do they fit and
strengthen us?*
- **Weight heavily:** a **unifying thesis / research-program narrative** — one through-line
  that connects past work to a future agenda, not a chronological tour of papers; a
  **personal opening** that establishes who you are as a scholar (your grand aim, your
  approach), with the first ~10-15 min **broadly accessible** to the whole department
  (the arc starts broad, descends to one deep result, ascends back); **2-3 best results
  built up properly** (depth over breadth — for each: why it's hard, what was known, your
  move, the result, the implication), *not* a complete survey; an explicit **future-program
  slide** with **concrete, fundable directions spanning the pre-tenure 5-7 years** (named
  projects, not "I will explore…"); evidence of **independence** (this is *your* agenda,
  distinct from your advisor's); **fit** signalled through framing pitched to *this*
  department; calm, listening **Q&A** that shows the depth survives probing.
- **Relax:** covering every project you've done; exhaustive method detail on the non-headline
  results (gesture and move on); venue-template conformance (there usually isn't one — but a
  hard time limit still binds); a hard sell / call-to-action (this is credibility, not a pitch).
- **Red flags:** a chronological "and then I did…" with **no through-line or vision**;
  opening straight into narrow method so half the room is lost in the first 5 minutes;
  **no future-research slide**, or one that's vague hand-waving instead of concrete projects;
  future work that reads as the advisor's lab agenda (no independence); cramming 6 projects
  shallowly instead of 2-3 deeply; results legible only to your subfield; over-running so
  Q&A is cut; ending on "Thanks" with no return to the big picture and the program ahead;
  zero signal of fit or what you'd bring to *them*.

## Company / stakeholder presentation
*Audience:* managers/clients, mixed/low technical depth. *Time:* short, decision-
oriented. *They want:* impact, value, and what you're asking of them.
- **Weight heavily:** lead with the outcome/recommendation (not the method);
  business/clinical framing of "so what"; minimal jargon (or defined plainly); high
  polish and consistency; every slide answers "why do I care?"; a clear ask/next step.
- **Relax:** algorithmic detail, equations (cut or move to appendix).
- **Red flags:** method-first ordering; unexplained acronyms; raw technical plots
  with no business interpretation; no recommendation/ask.

## Product description / pitch
*(Presenting or selling a product to prospects, customers, or users — a launch deck,
sales pitch, or product overview. Distinct from a stakeholder readout: the goal is to
make the audience **want the product and act**, not to report status.)*
*Audience:* potential users/buyers, often mixed or non-technical; they don't yet
care about you — they care about their problem. *Time:* short, momentum-driven.
*They want:* what is it, what problem it solves for *them*, why it's better, and what
to do next.
- **Weight heavily:** a clear value proposition stated **early and plainly** ("what
  it is + who it's for + the one core benefit"); **benefit-led, not a feature dump**
  (every feature tied to a "so you can…"); the **real product shown** (screenshots,
  photos, a demo frame — not abstract clip-art); clear **differentiation** ("vs. the
  status quo / alternatives"); **proof** (metrics, results, testimonials, logos) to
  back claims; one memorable positioning line; a strong, specific **call to action**
  at the end (try it / buy / sign up / contact). High polish and on-brand consistency
  matter — this deck represents the product.
- **Relax:** internal implementation/algorithm depth, roadmap minutiae, internal
  status/timeline (unless the audience is technical buyers who ask for it).
- **Red flags:** feature dump with no benefit or value framing; no clear "what is
  this" in the first slide or two; jargon/acronyms aimed at insiders; claims with no
  proof; no differentiation from alternatives; **no call to action**; the product
  itself never actually shown.
- **Investor pitch (raising capital) is a distinct variant — confirm the audience.** A
  pitch *to investors* sells the **company/opportunity**, not just the product, so it
  additionally wants: a big **market** (TAM/SAM/SOM), a credible **business model** and
  unit economics, **traction** (real growth/revenue/usage — never fabricated), the
  **team** and why they win, **competition** positioning, and a clear **ask** (amount +
  use of funds), typically on the canonical ~10-slide arc (problem → solution → market →
  product → traction → business model → competition → team → financials → ask). Judge an
  investor deck against *these*; judge a customer/user pitch against the value-prop/benefit
  criteria above. Fabricated metrics or market numbers are a **blocker** either way.

## Thesis / committee defense
*Audience:* expert committee. *Time:* long, scrutiny-heavy. *They want:* rigor,
validation, and your explicit contribution.
- **Weight heavily:** explicit contributions; validation/ablation; limitations and
  threats to validity; reproducibility; positioning vs. prior work; depth that
  survives hard questions; backup slides for anticipated questions.
- **Red flags:** claims without validation; no limitations; unclear what's novel.

## Teaching / instructional
*Audience:* learners new to the material. *Time:* flexible. *They want:* to
understand and remember.
- **Weight heavily:** stated learning objectives; progressive build (one new idea
  at a time); worked examples; recap/checkpoints; analogies for hard concepts;
  consistent notation.
- **Red flags:** too much at once; no examples; assuming prerequisites not given.

---

## Sources
- Alley, *Assertion–Evidence approach* — assertionevidence.com; Penn State
  (writing.engr.psu.edu) — sentence-assertion titles + visual evidence improve
  comprehension and recall.
- Mayer, *Cognitive Theory of Multimedia Learning* — coherence, signaling,
  redundancy, spatial-contiguity principles.
- Reynolds, *Presentation Zen* / Duarte, *Resonate* — simplicity, story, audience focus.
- Conference-talk guidance (e.g. UW-Madison "Oral Presentation Advice", LSE Impact
  blog) — one message, legible visuals, time discipline, forecast/summary.
- Job-talk convention — Maleckar et al., "Ten simple rules for giving an effective
  academic job talk" (PLOS Comput. Biol.); MIT EECS Communication Lab "Faculty Job
  Talk"; "Dr. Karen's Rules of the Job Talk" (theprofessorisin.com); Mordecai Lab
  "How to give a great (job) talk" — unifying research-program narrative, ~45-min
  talk in 60-min slot, first 10-15 min broadly accessible, 2-3 results at depth not
  breadth, a concrete 5-7-year future agenda, independence and departmental fit.
