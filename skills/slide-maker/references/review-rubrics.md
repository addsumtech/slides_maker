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
  - [Conference / research poster](#conference--research-poster-single-large-canvas-not-a-slide-sequence)

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
   assertion, not a topic label — e.g. "Churn dropped 12% after the redesign" (status),
   "Switching saves you 4 hours a week" (pitch), or "Only the warp needs to be 3D" (research) — not
   a bare topic like "Results" or "Method"). This applies to every purpose, not just research.
2. **Results legibility.** This is the one people get wrong most. Can the audience
   *actually see* the evidence from a normal viewing distance — figures large
   enough, key differences pointed at, in-figure labels readable? A results slide
   whose claim can't be verified from the image is a blocker.
3. **Cognitive load / text.** Few words per point; no paragraph the audience must
   read while the speaker talks. No text that merely duplicates what's said. **Voice — reads human, not
   AI-generated:** concrete fact over hype-filler (强大/高效/赋能 · "leverage/seamless"), varied rhythm, no
   machine parallelism — **most acute in 中文** (translationese: 的-chains, 进行/实现-nominalization, 破折号成瘾).
   *Would a sharp person in this field say this line aloud?* (See `multilingual.md` "Write like a human".)
4. **Figures labeled, intact & cleanly cropped.** Every figure has a legend (what rows/cols/axes
   are) and a one-line takeaway (what to notice). Unlabeled figure = major issue. A PDF-sourced
   figure must be **precisely cropped** — zoom in **close-up on each of the four edges** (not a
   glance at the whole) and check three failure modes:
   (a) **intact & not flush** — none of its own parts (legend, colour bar, axis **titles** & tick
   labels, panel-strip headers, units, **error bars / confidence intervals & significance markers
   (`*`, p-values)**, **panel labels `(a) (b) (c)`**, outer rows/columns, a sub-plot's x-axis labels)
   is clipped **or sitting flush against the image edge** — a *flush* element (its baseline/descenders
   butting the boundary) reads as clipped once the figure sits on a coloured slide, so treat flush =
   cut; a half-cut axis title or x-labels shaved off the bottom is the classic miss;
   (b) **no page text bled in** — the crop contains none of the page's prose: not the figure's own
   caption ("Fig. N." / "Table N."), a neighbouring figure's caption fragment, a running head/author
   line, a page number, or a stray body-text line at an edge; and
   (c) **self-contained — its OWN axis labels are present**, NOT silently replaced by a legend added
   on the slide. A tidy slide-legend must not *mask* an over-crop that dropped the figure's own
   x-axis category labels; the placed figure's axes must be readable on their own (a legend on top
   is an optional aid, never a substitute). A clean crop is tight to the figure's own content and
   nothing else; any of the three is a real finding (the crop box was imprecise — often because it
   was snapped to the plot-panel bbox, which excludes the axis titles/ticks/legend the library draws
   outside it), not a nitpick. Also flag a figure **chopped into pieces that lose the authors'
   context** (prefer the whole, integral figure; a narrowed crop that changes what was shown is a
   real finding).
5. **Signaling.** Is the eye guided to what matters (arrow, box, color, bold), or
   is everything the same weight?
6. **Narrative flow.** Do the slides form an arc (problem → idea → method →
   evidence → so-what)? Are there gaps or non-sequiturs between slides? Three sharper probes:
   **(question chain)** every slide should answer a nameable question — ideally one the *previous*
   slide raised (question → answer → evidence, per the content plan's role · question · beat
   column when provided); a slide whose question nobody asked, or whose title is a bare topic
   answering nothing, is filler — cite it. **(memory test)** After the full pass, close the deck
   and write the ONE sentence you remember plus the deck's message as you understood it; if it
   isn't close to the planned deck message, or no slide takeaway survived, the deck optimised for
   looking right over being remembered — a real finding, citing the forgettable beats (the goal is
   a presentation people *remember*, not merely beautiful slides). **(emotional flatness)** a deck
   holding one emotional temperature end-to-end — check against the content plan's emotional curve
   when provided — reads as a document, not a talk; pair this with the design lens's rhythm checks
   (the rhythm map's emotional-register column is where the curve should be visible).
7. **Visual quality.** Contrast (text vs. background — aim for ≥4.5:1, so light-grey
   text on white or low-contrast figure labels are flags), consistency (fonts, colors,
   alignment), whitespace (not crammed, not awkwardly empty), no overflow/clipping.
   **Font hierarchy:** is the **content/body text visibly smaller than the slide title**
   (a clear step, ~1.4–1.8×)? Body, callout, formula, or chip-label text set as large as or
   larger than the title is a real finding (only a deliberate *hero* numeral/equation may exceed
   body size, and it still stays below the title). **Awkwardly-empty slide:** is a large region
   left blank (content in one corner/the top third, a wide dead band)? The fix the critic should
   call for is **enrich the content** (add the detail/example/sub-point/figure the point deserves)
   or enlarge the hero — *not* shipping it sparse, and **not** inflating an oversized block around a
   single short line to fake fullness (a small-font one-liner swimming in a big box is a placeholder
   tell — flag it). Is
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
   crammed, **and no two elements overlapping**? A **collision** — two separate blocks intersecting
   with neither containing the other (a figure encroaching on a table/text, a band over the footer,
   text crossing out of its box) — is **unacceptable** (major; a covered footer / unreadable overlap is
   a blocker). *Intentional layering* — a child fully inside its parent (label on a card, scrim on a
   photo, glow under a glass card) — is **not** overlap and is fine. Also check **interior padding** (no
   text crammed against a card edge), **chips sized to their text** (no label overrunning its pill), and no
   **wrapped value/label colliding** with the line below — `lint_deck.py` flags these against the rendered
   text. *(Visual-only, not lint-backed)* **no node sitting ON a connector line** — links route in the gaps.
   On a **rich / image / 3D / generated-plate** background, are content **blocks semi-transparent (frosted)**
   (~30–45% show-through, one treatment deck-wide) rather than flat opaque, and does **every interior slide
   carry the shallow background** (not a flat single colour) — and on a deck built via the **image-tool
   template** path, is that shallow background a **generated plate** (not just a native gradient), except a
   deliberately minimal/flat style or an explicit clean-interiors request? — text still ≥4.5:1? (Opaque is
   fine on a plain/flat-by-design background.)
   On **split layouts** (text + figure, two-up, image + caption), are the left and right
   regions — *and the white margins flanking them* — the **same width** (or a clearly
   intentional asymmetric split with equal outer margins)? Unequal panels, a lopsided
   left-vs-right white margin, or a **large dead-white band** beside a narrow element stranded
   in a too-wide column is a real finding, not a nitpick. Does the **kicker/eyebrow add a
   section label rather than echo a word the title already leads with**? In **diagrams**, do
   arrows point the way the flow moves (a *sideways* arrow between vertically-stacked boxes is
   wrong), are repeated blocks/connectors **evenly spaced**, and do **adjacent blocks have a
   visible gap** (never touching — *and not a near-zero sliver*, which reads as cramped even when
   nothing technically overlaps)? Is a **hub / converge / fan-out node centred on the set it links**
   (a many→one or hub-and-spoke node on the geometric centre of its members, with symmetric connectors)
   — not eyeballed to one member's level (`span_center`/`mid`)? When a line mixes **font sizes**, do they read
   as one line — a **unit/suffix on the shared baseline** (one `text()` box; correct, as `stat_row`), a
   **comparison prefix/arrow vertically centred** on the hero number (`_set_baseline`/`change_stat`) —
   with the flaw being a *sunk* prefix or a small run *floating* from top-aligned separate boxes? Is each **feedback / repeat / return or non-adjacent link an
   elbow / U-shape** (`elbow_connector` / `loop_path`), not a **straight** arrow (straight = direct
   adjacent flow only; a straight "repeat" edge reads as forward flow and crosses other shapes)?
   Does **every shape of a native diagram sit inside its
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
   Diagnose layout with the **C.R.A.P. lens** (Contrast · Repetition · Alignment · Proximity — the
   shared vocabulary the planner designs to and the critic names). **Semantic colour contract:** if the
   deck binds a hue to a concept (`semantic-color-contract.md`), the same concept keeps **one hue
   deck-wide** and no hue carries two meanings — a drifting or double-booked binding is a real finding.
   **N-identical units:** many units identical except an index (replicas / layers / ensemble / team
   members) shown as *N duplicate blocks* is a flaw — expect the **pattern** (2–3 representatives + `…`
   + a `×N` badge, shared detail said once; `repeat_row`). **Icons:** when the deck uses SVG icons,
   judge the five quality marks (`icons.md`) — semantic fit, one coherent family, per-category
   colour-coding, contrast, and consistent size/position; a mismatched zoo, one-per-bullet clutter, or a
   decorative icon that does no job (fails the rule-of-thumb — *what is this / does / why pay attention*)
   is a finding. **Also judge STYLE-fit (Scenario fit, `icons.md`):** icons fit *any* topic — judge the
   *style match*, not their presence. An icon whose **weight/treatment fights the preset** (a chunky,
   generic line-icon grid on a delicate `editorial_paper`/`luxury_dark`/`ink_wash`/`museum_memorial`
   deck; a filled icon on `blueprint`) — or an icon used **decoratively** on a sober, figure-dominated
   deck — is a finding even if the five marks pass (item 11); the fix is **restyle / fewer**, with the
   native device (seal/`cjk_numeral`, photography, `year_badge`/duotone) leading and *composing with* a
   matched icon, not forbidding one.
   **Conversely** — on an **icon-FIT preset** (`dark_tech` / `consulting` / `glassmorphism` / `blueprint`)
   whose content is category/step-rich (named patterns, pipeline stages, tools/memory/protocols,
   production/feature layers) — **shipping ZERO icons is itself a finding** (a miss, not restraint:
   `icons.md` "actively plan an icon family"). **Corner-rounding** (rounded vs hard-edged) is a deck-wide language — a square-cornered
   image inside rounded cards (or vice-versa) is a consistency finding.
   **Deck-level rhythm (scan all slides together):** across a *long* deck, does the visual
   protagonist and density vary (a paced sequence — chart / diagram / photo / big-number / quote,
   dense slides spaced by airy ones), or does it read as **one template repeated**? A long deck where
   nearly every slide has the same shape is a deck-level finding (structural variety, not a per-slide
   quota — a short or deliberately-uniform deck is fine). **Also flag over-reliance on ONE component
   format** (most often the rounded-card / panel grid) on **>~40–50% of content slides** — even
   *mid-deck*, not only when literally every slide matches; the fix is to rework the weakest into the
   format their content wants (a timeline, big-numeral, quote, chart, 2×2, step-list, table). For **any algorithmic procedure** (a training loop, optimizer, derivation, or protocol-as-computation — any field), is it shown as an `algorithm_block` (numbered pseudocode) rather than
   buried in prose; and for a **principle/mechanism/experiment**, is there a labelled schematic diagram
   *beside* the statement rather than text alone, **with labels legible at slide scale** (and, on an
   image-tool schematic, present as **native** text)? When a slide **explains a method**, does its form
   match the question it answers — the **what/how/why triad**: *what* it is → schematic; *how* it works →
   `algorithm_block`/data-path diagram; *why* it works → typeset equation (don't pile *how*/*why* onto the
   *what* overview slide). (See `references/form-selection.md` + `references/schematic-diagrams.md`.)
   **The design lens's 10-item design-critic checklist** *(this IS the design lens — the squint-level
   pass the design/layout critic runs over the whole deck; kept WORD-FOR-CONCEPT identical to the
   checklist the planner designs to in `agents/slide-design.md` so the art director plans against the
   exact checks applied here):* ☐ main message readable in 3 seconds ☐ one clear visual focal point
   ☐ this page differs structurally from the previous ☐ colours semantic not decorative (incl.
   chrome: no multi-hue ornament stamped per-slide) ☐ any
   block-list that could be a diagram, is ☐ enough whitespace ☐ information hierarchy obvious ☐ at
   least one WOW slide ☐ the deck has visual rhythm ☐ opening and ending slides are memorable.
   **Anti-template deck-level checks — the critic applying the addendum's Reference-vs-Generated Gap
   Heuristic + Evenness Penalty** *(`references/design-intelligence-addendum.md` §2, §4–7 — the same gates
   the art director planned against, so the design lens scores what the planner gated).* Beyond the
   per-slide checklist, judge whether the deck is **art-directed** or merely **clean template output**
   (the "clean-but-even" failure this layer exists to catch), and flag, as deck-level design findings:
   **block-grid overuse** — the deck's main visual language is card / panel blocks, or **more than two
   consecutive slides** run block/card/panel logic (stricter than the ~40–50% one-format count above,
   which a "dashboard + metric-matrix + action-cards" run passes while all three read as the same grid);
   **loud / stamped chrome** — decorative furniture (a colour spine, a multi-hue strip or rainbow rule,
   a heavy title badge) repeated identically on every slide and competing with content for attention:
   the chrome budget (`agents/slide-design.md` §1) puts saturated colour on content elements and holds
   the signature motif to ~2–3 appearances, so palette-as-ornament stamped per-slide is a finding even
   when each instance is individually tidy; **pendulum overshoot** *(iteration rounds only)* — a fix
   for named feedback that swung to the opposite extreme (muted → rainbow chrome, dense → bare, static
   → everything animated) instead of moving the criticised dial one deliberate step in the content
   layer (`references/handoff-and-iteration.md` "Move the dial");
   **evenness** — a slide where every element shares one visual weight with no clear first-read **fails
   the squint test**, because nothing was chosen to win ("balanced" is not "even"); **missing
   semantic-colour ledger** — one accent hue used for everything, or colour that is decorative rather
   than *bound* to a nameable meaning that shifts across the argument's beats; **weak rhythm / variation**
   — few true visual events, or **fewer than 4 distinct visual protagonists** on a deck of 6+ content
   slides (adjacent slides not differing on density / colour mode / protagonist); and a **WOW that isn't
   memorable** — a hero beat that is merely a *large* element, not one that contrasts with its neighbours
   and stays memorable after the deck is closed. (General and cross-purpose — a short or
   deliberately-uniform deck relaxes the counts.)
   **Two evidence sources for this deck-level pass:** *(1) the THUMBNAIL pass* — view all slides at
   thumbnail scale in one grid and ask, per slide, "what does this slide say?": if the answer requires
   reading body text, the form isn't carrying the message (the slide is *decorated text*, not a
   *directed visual*); thumbnails also expose sameness and a flat type scale instantly. *(2) the DECK
   STATS block* from `scripts/lint_deck.py` (the builder pastes it into your input; ask for it if
   missing) — measured reading load, text/ink coverage, font histogram + type-drama ratio, build
   presence, and skeleton-similarity per slide. Score the numbers, not impressions: a `TEXT WALL` /
   `CROWDED` / `LAYOUT SAMENESS` / `FLAT TYPE` / `NO BUILDS` stats warning left unaddressed (no
   one-clause exception recorded) is a finding with the measurement as its evidence.
10. **Factual fidelity** *(when source material exists — the check every system fails).*
   Does every number, label, and headline claim trace back to the source? Does the deck
   represent the source's *actual emphasis* (e.g. a comparison table foregrounds the
   authors' comparison — baseline vs. the proposed thing — not a distracting one)? A
   caption that disagrees with its figure, a wrong number, or an over-claimed trend is a
   **blocker/major**, not a nitpick: it misleads the audience and exposes a shallow grasp
   of the material. **A science schematic is held to the same fidelity bar:** it must be
   *domain-accurate* (correct directions/topology/ray-rules/polarity, a balanced reaction,
   faithful to the source) and carry **no baked-in text** inside a generated image (labels
   must be native) — a pretty-but-wrong schematic is a fidelity **blocker**
   (`references/schematic-diagrams.md` §5). **An `algorithm_block` is held to it too:** the pseudocode
   must faithfully match the source's actual procedure — steps, **order**, loops/conditions, Input→Output
   — verified against the paper's algorithm or the code it derives from; an invented, reordered, or
   mis-simplified procedure is a fidelity **blocker**, and the block must stay **legible** at slide scale
   (trim to the contribution-carrying steps, not a wall). **Allowed exception — forward-looking content:** a *future work /
   next steps / the ask* slide may carry content not in the source, **if** it is clearly
   flagged as proposed and follows correctly from the material. Don't flag a
   properly-flagged forward-looking slide; *do* flag forward-looking claims dressed as
   established fact, or fabricated traction/market numbers presented as real. **Faked real
   assets count too:** on a slide about a real brand/product/UI, a generated look-alike, an
   invented logo, or a default-blue box standing in for the real asset (rather than the real
   logo/screenshot or an honest placeholder) is a fidelity blocker — use the real asset or ask the user.
   **Persistent brand chrome (the authoritative logo check — design *and* fidelity):** a **single-entity**
   deck (pitch / product / company readout / institution report — and equally a research / teaching / status
   deck whose subject IS one named tool / app / vendor) should carry a logo in a **fixed corner on every
   content slide** (consistent position + size). Two findings live here: **(design lens)** a single-entity
   deck shipping with **no brand chrome at all** — neither the real logo **nor a designed wordmark
   stand-in** — is flagged, as is a mark that **jumps corner / size**; and **(fidelity)** a **fabricated
   fake of a real entity's official logo** (an invented mark passed off as the real one) is a **blocker**.
   What *satisfies* the check: the **real logo** (from search), or — when it wasn't found — a **clean
   designed typographic wordmark clearly flagged as a non-official stand-in** (the sanctioned default; do
   **not** flag that as 'fake' — designing a mark is correct for the user's own / a new product). (Not for
   multi-org / neutral-academic decks; don't double a template's own branding; see `image-generation.md`
   "Logo / brand mark".)
   **Currency:** if the deck makes time-bound / falsifiable claims (a "latest / current", a count, a
   ranking, a dated event), confirm it carries an **as-of date** (as the planner requires) and that
   nothing dated has silently gone stale (last year's figure presented as this year's is a finding).
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
   for "consistency"; and (b) a **missed beat** — a slide where revealing the points/blocks
   **one by one (an appear build)** would clearly have helped the audience follow, left plain for
   no reason. Scale the severity to how much the build helps: a **pipeline / multi-stage diagram, a
   multi-part argument building to a conclusion, or an evidence→takeaway** dumped all at once is
   typically *major* for a presented talk (the all-at-once version genuinely confuses); a plain
   **multi-point bullet list** that would merely read better stepped is at most *minor* (plain lists
   are often perfectly fine — don't force a build on every list). Minor-to-none for read-alone decks
   (no one clicks them). Also flag the **inverse**: a ❌ content type (a simple title, a large
   paragraph, a reference list) that's been appear-animated — see the content-type matrix in
   `animation.md`. From the manifest, also flag a build that **doesn't start from an empty content
   area** — its first beat pre-shown so only the later items animate; a build should open showing only
   the scaffold (title/frame) and reveal **from the first item**, accumulating click-by-click. **The motion that counts is the in-slide appear build — NOT the
   slide-to-slide transition.** A deck-wide fade is at most optional secondary polish, never the
   point: **flag the lazy pattern** of a fade transition on every slide standing in for real
   animation (especially with build-candidate slides left un-built) — that's "motion done" theatre,
   a finding, not a pass. (Conversely, *absence* of a transition is **not** a finding.) **Do not** flag a slide for being plain, or a deck for having "too few" or
   even several *consecutive* built slides — that's a legitimate design choice; "plain,
   because nothing to pace here" is a valid answer, and so is "built, because this beat needed
   guiding." A cluttered *final built* state is a layout finding, not a motion one — animation
   never excuses it. **Embedded animated GIF (a result that IS motion):** the render / print / edit
   view all show **frame 0**, so its first frame must be representative (not blank / black / loading),
   placed whole and undistorted (`contain`); a frozen-frame stand-in for a time-resolved / cine / demo
   result throws away the point — a real finding.
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
   **formulas typeset** (`equation_native` editable, or `equation_png` for 2-D), **never cropped bitmaps** — transcribed from a paper or
   *derived faithfully from code* (a code-derived formula must express what the code computes)? Are
   formulas **sized to the body text** (glyphs ≈ content size and consistent across slides — not blown
   up to span the slide width, which oversizes the glyphs past the title, nor shrunk illegible), and is
   **every variable/symbol in math format** (italic, real sub/superscript) — *including a lone inline
   variable* — never plain body letters or Unicode super/subscripts? And do
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
  **Prefer a full-sentence *action title*** (a conclusion, not a topic label) + a one-line
  implication bar (`insight_banner`) over a noun-phrase heading — for an exec/board readout a
  topic-label title that buries the so-what is a real finding.
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

## Conference / research poster *(single large canvas, not a slide sequence)*
*Audience:* people walking the hall, scanning many posters. *They want:* to grasp the one result in
seconds, then read deeper if hooked. Judge the **whole canvas as one composition**, not per-slide.
- **Weight heavily:** a clear **reading path** through regions (title → takeaway → method → results →
  conclusion); **one focal result** sized to dominate; **self-contained completeness** (no speaker to
  narrate); readability at **arm's-length / print** (generous type, high contrast); the title states
  the finding, not the topic.
- **Red flags:** a wall of uniform body text; no visual hierarchy between regions; a buried headline;
  type sized for a screen, not a printed A0; the per-slide arc rules applied as if it were a deck.
  (Density relaxes per the fixed-surface mode; results legibility never does.)

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
