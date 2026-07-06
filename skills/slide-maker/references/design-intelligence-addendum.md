# Design-intelligence addendum — the OPERATIONAL gates the art-director enforces

This is the operational layer the **`slide-design` agent** (`agents/slide-design.md`) points to so the
agent prompt stays concise. `slide-design.md` states the *philosophy* (art-director, content-first, the
five bottlenecks, form-first); **this file makes that philosophy testable** — explicit output fields, an
anti-card-grid audit, the single authoritative concept→visualization dictionary, and deck-level gates a
plan must pass before the DESIGN checkpoint.

It is **general, reusable design intelligence** — it applies equally to a research/method deck, a product
launch, a teaching lecture, a project status readout, a conference talk, or a pitch. Any worked example
below is *illustrative only* and deliberately drawn from different domains; none of these gates are
specific to any one deck genre.

**Cross-reference, don't relearn.** This addendum sits *on top of* the craft files — it adds enforceable
gates, it does not restate their mechanics:
- **C.R.A.P., the squint test, base whitespace/rhythm rules, the AI-slop tells** → `design-principles.md`
  (`The C.R.A.P. framework`, `Deck-level rhythm — vary the protagonist`, `The squint test`,
  `Avoid the AI-slop tells`). This file references those; it does not repeat them.
- **Content-shape → candidate-forms map + tie-breaker + the Form-ledger diversity gate** →
  `form-selection.md`. The dictionary in §3 here is the *concept-level* first move that feeds that map.
- **Component catalogue / presets** → `design-gallery.md`; **charts** → `data-viz.md`; **schematics** →
  `schematic-diagrams.md`.
- **Icons** → `icons.md`; **animation / builds** → `animation.md`; **semantic-colour mechanics**
  (declare-once, propagate, teach-the-legend, contrast) → `semantic-color-contract.md`. §6 here adds the
  *ledger table* as an enforceable output on top of those mechanics.

## Contents
1. **The five bottlenecks, made operational** — the per-slide output fields that turn philosophy into a
   trace: Layout Intelligence, Rhythm Design, Space Intelligence, Visual Surprise, Visual Reasoning.
2. **Block Dependency Audit** — the stricter anti-card-grid gate the format-family diversity gate can't catch.
3. **Concept → Visualization decision table** — the single authoritative dictionary (use / avoid / failure mode).
4. **Reference-vs-Generated Gap Heuristic** — is this plan art-directed, or just clean template output?
5. **Evenness Penalty** — the "something must win" check.
6. **Semantic Colour Ledger** — colour as bound meaning, as an enforceable output.
7. **Minimum Deck-level Variation Requirements** — deck-level floors; hard gates at ~8+ content slides, strong guidance below.
8. **Slide Archetype Alternatives** — escape hatches from the default page-type reflex.

---

## 1 — The five bottlenecks, made operational

`slide-design.md` names the five bottlenecks the art-director exists to beat. Naming them isn't enough —
a deck can pass every per-slide check and still read as template output. Each bottleneck below gets a
**required output field or table**: a visible reasoning trace the plan must carry so the decision is
auditable, not implicit. Fill these for the slides where the choice is non-obvious; a title/divider/
single-idea slide can carry a one-clause version.

Together these fields extend the Design-plan's per-slide row into a diagnostic one. The columns worth
surfacing explicitly are **Narrative job · Content shape · Rejected default · Density/whitespace** — they
prevent the four hidden template decisions (slide-type→template mapping, no visual reasoning, card-grid
reflex, overpacking). Keep the fields in the plan; keep them out of the agent prompt.

### 1.1 Layout Intelligence — narrative job *before* layout

The failure mode: a template is chosen too early, so the layout becomes a **container** for content
instead of a **visual explanation** of the idea.

> **Rule.** Every slide must first identify its *narrative job* before choosing a layout. **A layout is
> invalid if it is only a container for content rather than a visual explanation of the idea.**

Required fields (per non-obvious slide):

```markdown
Narrative job: diagnosis / proof / contrast / mechanism / transition / decision / action
Visual logic:  evidence tree / flow / loop / timeline / split-screen / map / dashboard / hero number
Rejected default: card grid / bullet list / generic columns, because …
```

The *narrative job* is the verb the slide performs in the argument; the *visual logic* is the structure
that performs it; the *rejected default* forces you to name — and beat — the reflex form.

**The job is assigned upstream, not invented here.** The Content plan's per-slide **role · question ·
beat** column (role vocabulary: hook / problem / diagnosis / framework / method / evidence / case study /
comparison / roadmap / conclusion / call-to-action) already names each slide's job — the art director
*translates* the role into visual logic rather than re-deriving it at design time. Each role gravitates
to its own layout style, so adjacent slides with different roles should rarely share a template, and the
same role recurring is exactly where execution must consciously vary. If a slide arrives with no
nameable role or question, that is a **content** gap — raise it to the content-planner, don't paper over
it with layout.

### 1.2 Rhythm Design — a slide-by-slide rhythm map

The failure mode: every slide passes on its own, but the deck feels **evenly paced** end to end — same
density, same colour mode, same protagonist type, same emotional temperature.

> **Rule.** The design plan must include a **rhythm map** showing slide-to-slide variation in density,
> colour mode, visual protagonist, and emotional register. (This is the enforceable form of the
> `Deck-level rhythm` section in `design-principles.md` — read it down the whole column, since only the
> art-director sees every slide at once.)

Required table (one row per content slide):

| # | Skeleton | Density | Background mode | Protagonist | Emotional register | Role in rhythm |
|---|----------|---------|-----------------|-------------|--------------------|----------------|
| 1 | statement | light  | white           | hero symbol | aspirational       | opener         |
| 2 | split     | medium | warm accent     | risk / gap  | pressure           | conflict       |
| 3 | island    | light  | white           | funnel      | diagnostic         | explanation    |
| 4 | dashboard | medium | cool system     | flywheel    | constructive       | solution       |

**The Density cell carries the §1.3 whitespace estimate** — write it as `light ~65%` / `medium ~55%` /
`dense ~45% (split?)`, so the 50–70% target is *planned* per slide here rather than remembered
mid-build (the render-time lint then measures the real ink coverage and warns `CROWDED` when the
estimate was optimistic).

**The SKELETON column is the page's bone structure — one level above the protagonist.** A deck can
rotate protagonists (chart → diagram → number) and still feel templated because every page shares the
same skeleton: title top-left, one content zone, footer. Rotate the *canvas architecture* itself, from
this vocabulary (extend it freely):
- **statement** — one oversized sentence / number, centred or golden-ratio placed, nothing else
- **split** — two vertical fields (50/50 or 1/3–2/3), often text ↔ visual
- **island** — one diagram/figure dominating the middle, annotations orbiting
- **dashboard** — a measured grid of tiles with ONE hero tile breaking the grid
- **band** — a full-width horizontal axis (timeline / flow / spectrum) with content hanging off it
- **full-bleed** — the visual IS the page (image/diagram edge-to-edge), text overlaid on a scrim/plate
- **rail** — a narrow side rail (nav / context / stat stack) + a wide main field
- **gallery** — 2–4 exhibits with captions, curated not gridded
A deck of 8+ content slides should use **≥4 distinct skeletons**, and **no 3 consecutive slides share
one skeleton** (the render-time lint fingerprints this — `LAYOUT SAMENESS`). Adjacent rows must still
differ on more than one axis overall.

The example rows are cross-domain scaffolding, not a prescription — a teaching deck's registers might run
*curiosity → tension → aha → consolidation*; a status deck's might run *steady → concern → plan →
commitment*. What matters is that **adjacent rows differ** on more than one axis.

The *Emotional register* column is **executed, not invented**: the Content plan's narrative arc carries a
planned **emotional curve** (each slide tagged with its beat), and this map's job is to make that curve
*visible* — density, colour temperature, and scale rising and falling with it. A flat emotional
temperature end-to-end is precisely the failure this table exists to catch; deviating from a planned beat
needs a stated reason, and a missing curve is a content-plan gap to raise upstream.

### 1.3 Space Intelligence — whitespace is active; subtract, don't add

The failure mode: AI treats empty space as unused capacity and fills it — usually with one more card row.

> **Rule.** Whitespace is an **active** design element. If a slide feels thin, **strengthen the hero or
> reduce secondary elements — do not add more cards to fill space.** The urge to add a plate/card-row to
> a plain slide is the AI-slop signal (`design-principles.md`, `Avoid the AI-slop tells`): subtract.

Required fields (per slide that feels dense or thin):

```markdown
Whitespace estimate: ~55% / ~65% / ~70%
Density decision: keep airy because … / split because … / compress only if …
```

Target band is ~50–70% whitespace (the operational figure here for `design-principles.md`'s *generous whitespace*). "Compress" is the last resort and must be
justified; the first two moves are **strengthen the hero** and **split the slide** (never shrink to
illegible).

### 1.4 Visual Surprise — name *why* the WOW is memorable

The failure mode: the deck schedules a WOW slide every ~6–8 slides but makes it merely a *large element*,
not a *memorable* one, and doesn't check that it actually contrasts with its neighbours.

> **Rule.** A WOW slide is not merely a large element. It must create a **deliberate contrast against the
> surrounding slides** and be **memorable after the deck is closed.**

Required fields (per WOW/hero beat):

```markdown
WOW candidate: slide X
Why memorable: bold number / iconic diagram / dramatic sentence / extreme contrast / unusual metaphor
Surrounding contrast: differs from slides X-1 and X+1 by layout + density + colour mode
```

If the "surrounding contrast" line can't be filled — because X-1 and X+1 look the same — the WOW isn't a
WOW yet; it's just another slide that happens to be bigger.

### 1.5 Visual Reasoning — reason from content *logic*, not page *type*

The failure mode: even with a dictionary, the agent maps a page *type* to a layout ("this is a problem
slide → three cards") instead of reasoning from the content's underlying *logic*.

> **Rule.** Do **not** map "problem slide → three cards." Map the *logic*: "this problem is caused by
> three **interacting** failure points → evidence tree / causal chain / leak diagram." The relationship
> between the units — not their count — chooses the form.

Required reasoning chain (per non-obvious slide):

```markdown
Content says:   <the raw content units on this slide>
Underlying idea: <the one thing they collectively mean>
Visual metaphor candidates: <2–4 forms that could express it>
Chosen: <winner>, because it expresses <the relationship> better than <the rejected default>.
```

Cross-domain worked examples (illustrative only):

- *Research method:* "Content says: preprocessing loses signal, the model overfits, evaluation leaks. →
  Underlying idea: the pipeline degrades at three coupled stages. → Candidates: leaking pipeline, causal
  chain, evidence tree, failure dashboard. → Chosen: leaking pipeline, because it shows the loss
  *compounding through* stages, which three independent cards would hide."
- *Teaching:* "Content says: three properties of the operator. → Underlying idea: they build on each
  other. → Candidates: layered stack, staircase, three cards. → Chosen: staircase, because each property
  *presupposes* the one below — order is the point."
- *Product status:* "Content says: sign-ups up, activation flat, retention down. → Underlying idea: the
  growth loop isn't closing. → Candidates: flywheel with a broken segment, funnel, three KPI cards. →
  Chosen: broken flywheel, because the metrics *feed each other* and the story is the loop, not the tiles."

---

## 2 — Block Dependency Audit

The single most common weakness in generated decks is not that block/card layouts are *wrong* — it's that
blocks quietly become the **default visual language** for everything. The Form-ledger **diversity gate**
in `form-selection.md` counts by *format-family*, so it can be gamed accidentally: a "dashboard," a
"metric matrix," and "three action cards" count as three different forms, yet all three read as the **same
block-grid** on the wall. This audit catches the visual sameness the family count misses.

> **The block rule.** A block / card / panel layout is allowed **only if** the content units are all of:
> **parallel · unordered · equal-weight · independent** — **and** the content is **not better expressed as
> time, flow, hierarchy, comparison, system, or magnitude.** The moment the units have order, a
> relationship, two axes, a sequence, or differing weight, a non-block form says it better (see the
> dictionary in §3 and the tie-breaker in `form-selection.md`).

> **The consecutive-slides rule.** **No more than two consecutive slides may use block/card/panel logic.**
> If two or more in a row do, at least one must be redesigned into the form its content actually wants —
> unless there is a stated, strong content reason.

Required audit table (one row per slide that uses cards / blocks / panels):

| # | Uses blocks? | Why allowed? (name the parallel/unordered/equal-weight/independent test it passes) | Better non-block alternative considered? (name it) | Keep or redesign? |
|---|--------------|------------------------------------------------------------------------------------|----------------------------------------------------|-------------------|

The "better alternative considered" column is the point: it forces the agent to *reach for* the flow /
timeline / hierarchy / comparison / system form and consciously reject it, rather than defaulting to
blocks because blocks are easy to place. A block layout that survives this audit is a **considered**
choice; one that can't fill the "why allowed?" cell is the reflex, and must be redesigned.

**Relation to the diversity gate:** the diversity gate (`form-selection.md`) is a *quantitative* ceiling
per family (~40–50%); the block dependency audit is a *qualitative* gate on the underlying visual
language. A plan can pass the gate and still fail the audit — run both.

---

## 3 — Concept → Visualization decision table (the authoritative dictionary)

**This table is the single authoritative concept→visualization dictionary for the whole skill.** The
short "first move" concept list in `slide-design.md` step 2 and the compact concept table at the top of
`form-selection.md` are *pointers into this table* — when a concept needs its full use/avoid/failure-mode
detail, resolve it here, then pick the concrete form/component in `form-selection.md` and `design-gallery.md`.

Read the content's *underlying shape* (what the units collectively mean and how they relate), match a row,
then choose among its **strong visual languages** using the **Use when / Avoid when** columns. The **Common
AI failure** column names the specific slop this concept degrades into — that's the thing to *not* ship.
Every row is domain-neutral: "Flow" is as true of a lab protocol as of a delivery pipeline; "Growth" fits
a learning curve, an adoption chart, or a compounding argument.

| Concept / content logic | Strong visual languages | Use when | Avoid when | Common AI failure |
|---|---|---|---|---|
| **Flow** | pipeline, river, conveyor, swimlane | Steps happen in sequence | Items are unordered | Four cards with arrows |
| **Journey** | timeline, road, metro map, path | Time or stages matter | No chronological order | Generic timeline with too much text |
| **Growth** | curve, mountain, compounding loop, rocket, staircase | Progress or acceleration is central | Change is qualitative only | Random upward arrow |
| **Loop** | flywheel, orbit, cycle, feedback loop | Output feeds back as input | Sequence has a clear endpoint | Circular diagram with no feedback logic |
| **Comparison** | split screen, mirror layout, before/after, scale | Two states or options must be contrasted | More than 3 alternatives | Table when visual contrast is needed |
| **Hierarchy** | pyramid, layers, nested boxes, org tree | Levels or dependencies matter | Items are equal-weight | Flat card grid |
| **Strategy** | compass, map, north-star, choice tree | Direction and tradeoffs matter | Pure execution details | Decorative compass icon |
| **Ecosystem** | network, galaxy, hub-spoke, stakeholder map | Many actors interact | Simple sequence | Random nodes with no meaning |
| **System** | circuit, operating system, layered architecture, control loop | Components interact repeatedly | One-time process | Boxes connected by meaningless lines |
| **Transformation** | morphing, bridge, before/after, migration path | Old state becomes new state | Only listing features | Two columns with no transformation logic |
| **Decision** | decision tree, fork, option matrix, criteria ladder | Choice rules matter | No decision criteria | Bullet list of options |
| **Process** | assembly line, flow chain, swimlane, Gantt | Operational sequence matters | The point is outcome only | Too many equal cards |
| **Relationship** | network, matrix, Venn, causal map | Connections are the insight | Independent items | Decorative network |
| **Dependency** | Sankey, dependency graph, stacked layers | Inputs feed outputs | No volume or dependency | Arrows without weights/logic |
| **Scale** | staircase, zoom levels, nested frames, logarithmic axis | Magnitude / level changes matter | All values are close | Giant number without context |
| **Prioritization** | 2×2, ranked ladder, bullseye, impact-effort map | Choice / order matters | There is no ranking | Random quadrant with weak axes |
| **Evolution** | timeline, version ladder, maturity curve | Change over time matters | Static concept | Timeline used as decoration |
| **Risk** | heatmap, warning dashboard, red-flag map, failure chain | Severity / likelihood matters | Risks are only examples | Red colour everywhere |
| **Performance** | dashboard, scorecard, leaderboard, delta cards | KPIs are central | Story is causal / mechanistic | KPI wall with no hierarchy |
| **Progress** | progress bar, milestone road, completion ring | Completion status matters | Open-ended exploration | Decorative progress bars |
| **Bottleneck** | narrow pipe, hourglass, blocked flow, queue | One constraint slows the system | Multiple unrelated problems | Three problem cards |
| **Tradeoff** | balance scale, tension diagram, frontier curve | Two objectives conflict | Only one objective | Two columns without tension |
| **Causality** | evidence tree, causal chain, fishbone, domino path | Cause-effect is central | Items are merely descriptive | Flat bullets / cards |
| **Flywheel / compounding** | flywheel, orbit, self-reinforcing loop | Each step strengthens the next | Steps do not feed back | Pretty circle with no compounding |
| **Leakage / churn** | leaking bucket, broken funnel, pipeline leak | Loss occurs across stages | Only one metric is bad | Three warning cards |
| **Operating model** | system map, RACI grid, layered model, swimlane | Roles / process / metrics interact | Pure narrative | Org chart as decoration |
| **Roadmap** | quarterly timeline, release train, milestone path | Future sequencing matters | No time order | Three cards labelled Q1/Q2/H2 only |
| **Case study** | journey + proof metrics, story arc, expansion path | A person / entity changes over time | Pure metric summary | Timeline with no protagonist |
| **Insight / conclusion** | editorial quote, big sentence, black band, hero claim | One message should land emotionally | Detail-heavy slide | Small conclusion hidden at bottom |

After a row is chosen here, hand off to `form-selection.md` for the concrete candidate SET + tie-breaker
(e.g. Comparison → `dumbbell` vs `slope` vs `before_after`) and to `design-gallery.md`/`data-viz.md` for
the exact component or chart. This table chooses the *language*; those files choose the *artifact*.

---

## 4 — Reference-vs-Generated Gap Heuristic

A useful general test of whether a plan is **art-directed** or merely **clean template output**. The
difference between a strong human deck and a weak generated one is rarely colour quality — it's whether
each slide uses a **content-specific visual mechanism** or reuses one generic one.

**Weak generated-deck pattern** (if the plan looks like this, it isn't ready):
- many slides share the same shallow background,
- many slides use card grids as the main visual language,
- all cards have similar weight,
- colour follows the template instead of semantic meaning,
- dense slides are "solved" by smaller text rather than hierarchy,
- the deck has few true visual events.

**Strong art-directed pattern** (the target):
- each slide has a **different visual protagonist**,
- colours **shift semantically** across the argument's beats (setup, tension, mechanism, evidence, action),
- one slide is a diagram, one a dashboard, one a timeline, one a hero claim,
- dense information is **ranked**, not evenly packed,
- **every few slides** carries a memorable visual event.

> **The heuristic.** If the design plan resembles the weak pattern, **it is not ready even if each
> individual slide looks clean.** Clean-but-even is the exact failure this whole addendum exists to catch.

The narrative beats above are deliberately generic — for a paper they might be *background → gap → method
→ results → implication*; for a pitch, *status quo → problem → solution → traction → ask*; for a lecture,
*motivation → concept → worked example → takeaway*. The test is the same across all of them: does the
visual mechanism change with the beat, or is it one language repeated?

---

## 5 — Evenness Penalty

Many generated slides look clean but **too even**: every card has similar visual weight, every section
has similar spacing, every slide sits at medium density. Even is not the same as balanced — even is the
absence of a decision about what wins.

> **The penalty.** A slide is weak if all elements have similar visual weight. The plan must **decide what
> wins.** (This is the enforceable form of the `squint test` and "invest unevenly (one element at ~120%)"
> rules in `design-principles.md` — a slide should blur to 3–4 hierarchy levels, not one even grey field.)

Per-slide check:
- Is there a clear **first-read** element (what the eye lands on immediately)?
- Is there a clear **second-read** layer (what it goes to next)?
- Are supporting details **visibly quieter** (smaller / lighter / lower-contrast)?
- Is **at least one thing** deliberately **oversized, isolated, darkened, framed, or placed centrally**?

> If everything is equally polite, the slide **fails the squint test** — send it back and let one element win.

---

## 6 — Semantic Colour Ledger

`semantic-color-contract.md` owns the *mechanics* — bind one hue per concept, declare it once, propagate
it to every element that expresses the concept (headings, icons, badges, cells, chart series, keyword
highlights), teach the legend early, and clear ≥4.5:1 contrast. This addendum adds the **ledger as an
enforceable output**: the plan must state, up front, what each colour *means* and what it must *not* touch.

> **Rule.** The design plan must include a **semantic colour ledger** — an explicit map of role → token →
> where it's used → where it must never appear.

| Semantic role | Colour / token | Used for | Must **not** be used for |
|---|---|---|---|
| **Structure** | navy / graphite | systems, labels, axes, frames | warnings |
| **Growth / positive** | green / teal | improved metrics, expansion, "good" | neutral decoration |
| **Risk / problem** | amber / red | bad metrics, bottlenecks, loss | ordinary emphasis |
| **Neutral support** | grey / warm grey | cards, grid, background | the main hero |
| **Decision / action** | deep blue / purple | roadmap, commitment, "what we'll do" | historical evidence |

The roles and vocabulary above are **illustrative and cross-domain**, not a fixed palette — a teaching
deck might bind *known / new / misconception*, a scientific deck *signal / noise / artifact*; carry the
same declare-once discipline onto whatever concepts your content actually names.

Rules:
- **No accent colour without semantic meaning.** If a hue appears, it must *mean* something the audience
  can name.
- **Problem slides are allowed to feel different from results slides.** Semantic colour is *supposed* to
  shift the temperature across the argument's beats — a warning slide reading amber-warm while a results
  slide reads green-cool is the contract working, not an inconsistency.
- **If the whole deck uses one accent hue for everything, the plan is not ready.** One hue for everything
  means colour is decoration, not meaning.

Keep it to ≤5 bound concepts (beyond that colour stops reading as meaning), and never encode meaning by
colour alone — pair it with a label / icon / shape (`semantic-color-contract.md`).

---

## 7 — Minimum Deck-level Variation Requirements

The Form-ledger diversity gate sets a *ceiling* per format-family; these are the *floors*. **Consider all
of these on every deck** — the consideration is never optional; what scales with size is how hard the
numbers bind. For any deck with **~8+ content slides** they are hard gates: the plan is not ready unless
each holds *or* carries a one-clause reason why this deck's content genuinely wants otherwise. At **6–7
content slides** treat them as **strong guidance**, not a hard fail; under 6, as lighter guidance still (a
4-slide deck may legitimately carry fewer protagonists).

- **≥ 4 distinct visual protagonists** across the deck, **of which ≥ 3 are non-card forms** (diagram /
  chart / timeline / hero number / quote / table — not panels) — or a one-clause reason why this deck's
  content genuinely wants otherwise.
- **No more than 2 consecutive slides** using card / panel logic (this is the §2 consecutive-slides rule,
  surfaced as a deck-level floor) — or a stated, strong content reason (as in §2).
- **≥ 1 hero / WOW slide** (with its §1.4 fields filled) — or a one-clause reason why this deck's content
  genuinely wants otherwise.
- **≥ 1 diagrammatic slide** if the content contains **any process, system, mechanism, or framework.**
- **≥ 1 contrast slide** if the content contains **before/after, old/new, problem/solution, or
  baseline/proposed.**
- **≥ 1 time / roadmap slide** if the content contains **sequence, phases, evolution, or a future plan.**

The last three are *content-triggered*: they only bind when that content is present — but when it is,
skipping the corresponding form is a miss, not a stylistic choice (unless a one-clause content reason
says otherwise).

---

## 8 — Slide Archetype Alternatives

The reflex is to reach for the same page type for the same *kind* of content — every "problem" slide
becomes three cards, every "results" slide becomes a KPI wall. For each common archetype below, the plan
should have **considered at least one alternative** and named why it did or didn't fit. These are menus,
not mandates — a genuinely list-shaped run of items may still be cards, *with a stated reason*.

**Problem slide** →
- warning dashboard · leaking funnel · broken pipeline · evidence tree · heatmap · single dramatic hero number

**Root-cause slide** →
- causal chain · fishbone · system-loop failure · bottleneck map · responsibility swimlane

**Framework / model slide** →
- flywheel · operating-system layers · hub-spoke model · lifecycle loop · compass / north-star map

**Results slide** →
- dashboard with one hero metric · before/after scoreboard · slope chart · KPI wall *with hierarchy* · proof stack

**Case-study slide** →
- journey timeline · expansion path · lifecycle of the subject · story arc · metric progression

**Action-plan slide** →
- roadmap · milestone ladder · operating cadence · decision tree · commitment board

For each, resolve the concept through the dictionary in §3, then pick the concrete artifact via
`form-selection.md` / `design-gallery.md`. The archetype names above are cross-domain: a "results" slide
is as real in a thesis defense or a lecture recap as in a status readout; a "framework/model" slide fits a
methods section, a teaching concept, or a product architecture equally.
