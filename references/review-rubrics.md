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

> **Scope the density dimensions by DELIVERY MODE first.** Items 1 (one-idea), 3 (cognitive-load /
> few-words), and "from a normal viewing distance" assume a **presented** deck where a speaker
> narrates. For a **read-alone** deck (leave-behind, pre-read, reference / appendix) or a **fixed
> surface** (poster, single-slide infographic), denser self-contained slides with fuller prose are
> *correct, not a flaw* — judge density against the deck's **stated density mode / purpose**, never
> the talk default; do **not** flag legitimate read-alone density as "wall of text." Set the
> legibility floor by the **medium** (back-of-room for a talk, screen for a webinar, arm's-length /
> print for a read-alone or poster). What never relaxes in any mode: results legibility (≥4.5:1, no
> clipped figures), source fidelity, no overlap.

1. **One idea per slide** *(presented default)*. Does each slide carry a single, identifiable point? Two
   messages on one slide = split it. Title should state that point (ideally an
   assertion, e.g. "Only the warp needs to be 3D", not a topic like "Method").
2. **Results legibility.** This is the one people get wrong most. Can the audience
   *actually see* the evidence from a normal viewing distance — figures large
   enough, key differences pointed at, in-figure labels readable? A results slide
   whose claim can't be verified from the image is a blocker.
3. **Cognitive load / text.** Few words per point; no paragraph the audience must
   read while the speaker talks. No text that merely duplicates what's said.
4. **Figures labeled, intact & cleanly cropped.** Every figure has a legend (what rows/cols/axes
   are) and a one-line takeaway (what to notice). Unlabeled figure = major issue. A PDF-sourced
   figure must be **precisely cropped** — zoom in on all four edges and check both failure modes:
   (a) **intact** — none of its own parts (legend, colour bar, axis labels/ticks, title, units,
   outer rows/columns, a sub-plot's x-axis labels) is clipped by the crop or the slide placement
   (a half-cut legend, or x-labels shaved off the bottom, is the classic miss); and (b) **no page
   text bled in** — the crop contains none of the page's prose: not the figure's own caption
   ("Fig. N." / "Table N."), a neighbouring figure's caption fragment, a running head/author line,
   a page number, or a stray body-text line at an edge. A clean crop is tight to the figure's own
   content and nothing else; either failure is a real finding (the crop box was imprecise), not a
   nitpick. Also flag a figure **chopped into pieces that lose the authors' context** (prefer the
   whole, integral figure; a narrowed crop that changes what was shown is a real finding).
5. **Signaling.** Is the eye guided to what matters (arrow, box, color, bold), or
   is everything the same weight?
6. **Narrative flow.** Do the slides form an arc (problem → idea → method →
   evidence → so-what)? Are there gaps or non-sequiturs between slides?
7. **Visual quality.** Contrast (text vs. background — aim for ≥4.5:1, so light-grey
   text on white or low-contrast figure labels are flags), consistency (fonts, colors,
   alignment), whitespace (not crammed, not awkwardly empty), no overflow/clipping. Is
   any meaning carried by **colour alone** (a plot legend or status distinguished only
   by hue)? Pair it with a label/shape/marker so it survives projection and colour-blind
   viewers. And **none of the named AI-slop tells** (full-screen gradient wash, emoji titles,
   rounded-left-border cards on every slide, three identical feature cards) — see the named list in
   `agents/critic.md` / `references/design-principles.md`.
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
   intentional asymmetric split with equal outer margins)? Unequal panels, a lopsided
   left-vs-right white margin, or a **large dead-white band** beside a narrow element stranded
   in a too-wide column is a real finding, not a nitpick. Does the **kicker/eyebrow add a
   section label rather than echo a word the title already leads with**? In **diagrams**, do
   arrows point the way the flow moves (a *sideways* arrow between vertically-stacked boxes is
   wrong), are repeated blocks/connectors **evenly spaced**, and do **adjacent blocks have a
   visible gap** (never touching)? Does **every shape of a native diagram sit inside its
   card/panel** with a margin (a box/icon/node poking outside its frame, or an asymmetric
   off-centre cluster, is a real finding)? On **image slides**, is the key subject **whole and
   uncropped** — not sliced by the
   frame (a figure, product, person, or object cut off so only part of it shows)?
   A `cover`-fit plate that loses its subject is a real finding (fix: `contain`/shrink/regenerate).
   And is a **generated image of real things factually right** — correct **relative
   sizes/proportions** (real objects drawn to scale relative to each other), count, colour,
   and arrangement —
   with any **labels aligned under the feature** they name? A visibly wrong fact in a
   generated plate is a real finding even when it's "decorative" (fix: prompt the fact or draw
   it natively).
   Is text inside filled boxes (callouts, chips, takeaway bars, cells) **optically
   centred**, not hugging an edge or sitting a touch low — **including a lone glyph or icon**
   (a "?", a number, a mark), which must sit dead-centre in its box, not top-left or low? (On a
   CJK deck an off-centre large mark is usually full-width punctuation — the fix is the ASCII form.)
   Does a **subtitle / definition line under the title** leave a clear gap below the accent
   rule rather than jamming against it? Does colour vary with intent,
   or is everything one monotone accent? Is the closing slide named for its purpose
   ("Conclusion" for a talk, "Next steps" for a status update — not a generic "Take home")?
   **Deck-level rhythm (scan all slides together):** across a *long* deck, does the visual
   protagonist and density vary (a paced sequence — chart / diagram / photo / big-number / quote,
   dense slides spaced by airy ones), or does it read as **one template repeated**? A long deck where
   nearly every slide has the same shape is a deck-level finding (structural variety, not a per-slide
   quota — a short or deliberately-uniform deck is fine).
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
   established fact, or fabricated traction/market numbers presented as real. **Faked real
   assets count too:** on a slide about a real brand/product/UI, a generated look-alike, an
   invented logo, or a default-blue box standing in for the real asset (rather than the real
   logo/screenshot or an honest placeholder) is a fidelity blocker — use the real asset or ask the user.
11. **Design fits the purpose.** Does the look match the deck's purpose and audience —
   crisp/corporate for a status update, sober/formal for a defense, bold/on-brand for a
   product pitch, warm/clear for teaching (see `references/design-by-purpose.md`)? A
   purpose-mismatched look (or a generic default palette shipped for a high-polish
   pitch/exec deck) is a real finding. Judge against this purpose, not a generic ideal.
12. **Motion & pacing** *(applies to every purpose, not just talks).* Judge motion by
   **taste and purpose, not by a count** — there is no right number of builds and no quota in
   either direction. Read against the **motion manifest** (the static render can't show a
   reveal sequence, so judge the *design*, not the playback). The two failures to flag are
   both about *thoughtlessness*: (a) **thoughtless motion** — a build (or flashy entrance)
   that doesn't emphasize, engage, or guide, that distracts, or that is added for flourish or
   for "consistency"; and (b) a **missed beat** — a slide that is clearly a pipeline /
   multi-stage diagram, a multi-part argument, or an evidence→takeaway shown all at once,
   where a step-by-step build would clearly have helped the audience follow, left plain for no
   reason (typically major for a *presented* talk, minor for read-alone). Also: a calm
   **deck-wide transition** is a sensible default — its absence with no stated reason is a
   minor finding. **Do not** flag a slide for being plain, or a deck for having "too few" or
   even several *consecutive* built slides — that's a legitimate design choice; "plain,
   because nothing to pace here" is a valid answer, and so is "built, because this beat needed
   guiding." A cluttered *final built* state is a layout finding, not a motion one — animation
   never excuses it.
12a. **Generated images — taste & purpose** *(when the deck uses AI-generated plates).*
   Judge them the same way as motion: by design intent, not by count. Flag **thoughtless**
   use — a plate added for flourish, to fill space, or that competes with the slide's text;
   and a plate where a source figure / real computed artifact / chart / plain whitespace
   would serve better; and **style incoherence** — plates that don't share one art-direction
   fitting the deck's purpose and topic. **Do not** flag a deck merely for having several or
   *consecutive* plates, or for using none — frequency is a design choice. (Fidelity
   violations — readable text, fake charts/labels/logos, or a generated image standing in for
   evidence — are blockers under item 10, not this one.)
12b. **Designed charts, data furniture & typeset math** *(when the deck builds its own charts or uses
   the data-viz / publication helpers).* Is the chart **type chosen to fit the argument** (not a bar
   where a part-to-whole wants a donut, nor a grouped bar where a trend wants a slope/dual-axis), with
   a **single highlight** on the one series that matters and a stated **so-what** (`takeaway_rail`),
   placed **whole** and legible at the deck's read distance? Do `scorecard`/`change_stat` **▲/▼ deltas
   / before→after** carry the **right polarity** (green for the genuinely-good direction)? Are
   **formulas typeset** (`equation_png`), **never cropped bitmaps** — transcribed from a paper or
   *derived faithfully from code* (a code-derived formula must express what the code computes)? And do
   the surface/furniture patterns hold — **glass only on a dark base**, **cards in a row one height**,
   **type pairing** (a DISPLAY title face vs FONT body; for CJK, EADISPLAY title vs EAFONT body — not
   one font everywhere), no text spilling past a card? Most of these are also caught deterministically
   by `scripts/lint_deck.py`.

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
- **Three high-recurrence classes are re-derived from first principles, not voted on** — PDF
  **crop** (zoom every figure edge against the source page: nothing clipped *and* no page text
  bled in), **layout** (re-measure footer-collision / overlap / symmetry / centring in the
  pixels), and **material-understanding / fidelity** (recompute each number against its source
  location *and* claim-ledger row; check each figure/table's emphasis against the brief's
  carrying element). These slip to a later round most often, so they get the hardest
  cross-validation; a clip, a text-bleed, a footer collision, or a mis-emphasis confirmed in the
  pixels is promoted at raise-count 1.

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
can't play a sequence), and judge motion by taste and purpose — never by count. Never treat
a plain slide, or several/consecutive built slides, as a flaw in itself. Two kinds of
animation finding exist: (a) a **cluttered final state** — a slide that would only look
clean mid-build is relying on animation to hide crowding (fix the layout, not the timeline);
and (b) **thoughtless motion** — a build (or flashy entrance) that doesn't emphasize,
engage, or guide, that distracts, or that's added for flourish or "consistency" (see
item 12, which also covers the opposite: a clear beat left plain that a build would have
helped).

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
