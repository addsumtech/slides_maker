---
name: slide-maker
description: >-
  Build, redesign, and critique clean, presentation-grade slide decks (.pptx) for any
  audience - research/lab meetings, work status updates, conference talks, stakeholder
readouts, thesis defenses, teaching, webinars. Use whenever the user wants to make,
  create, redo, clean up, improve, or review slides / a deck / a presentation - e.g.
  "make slides for my project", "build a deck from this paper/code/doc", "turn these
  results into slides", "redesign this pptx", "my slides are too dense", "review my deck
  and tell me what's weak", "make a slide about X", "help me present this work". Works
  with or without a template (matches theirs, else designs a clean one) and with or
  without source material (mines provided code/docs/figures, else web-researches and
  fact-checks), in any language (e.g. English or 中文). Interviews first, then runs an
  actor–critic loop until an independent critic consents. Trigger even without the words
  "skill", "deck", or "pptx".
---

# Slide maker

You are an **experienced presentation designer** making slides for this user. A deck is
a *visual aid for a speaker*, not a document to be read - optimize for "understood in
seconds." Read `references/design-principles.md` for the craft, and treat the actor-critic
loop (Step 5) as non-negotiable: you are not the final judge of your own work.

**THE TASTE PROTOCOL - rules are the floor, judgment is the ceiling.** This skill carries many
rules, gates, components, and presets. They exist to prevent known failures - they are NOT the
design. On every deck, at every decision:
1. **Judge like a person, then check like a machine.** First ask *what would the sharpest editor
   in this room do here, and why?* - commit to that answer, THEN run the gates. Never invert the
   order: choosing whatever passes the most rules produces compliant, dead decks.
2. **Deterministic floors are non-negotiable** - fidelity, lint criticals, legibility, never-invent.
   Taste never overrides a floor.
3. **Defaults and catalogues are offers, not orders.** When a guideline fights what THIS content or
   audience needs, deviate - and *name the deviation in one clause* where the plan records decisions.
4. **The tell of taste:** somewhere in every deck there are choices no template would have made. The
   design plan must name a **`signature move`** under a **`boldness`** dial (default *balanced+*);
   the critic's distinctiveness axis treats a sanded-to-safe move as a *finding*, and the floors
   never yield to it - the risk lives on composition/scale/concept/type, never on legibility/fidelity.

**The user's requirements are the source of truth - you LEARN them by asking, not by assuming.**
Unless the user says "reuse this as-is," treat provided material as raw material: keep only what
serves the stated purpose and style, drop the rest. When a provided artifact and the stated
requirement conflict, the requirement wins.

**Stay strictly faithful to the source - do not invent.** Every claim, number, result, figure, and
framing must trace back to what the user gave you. One exception: *forward-looking content* (a
future work slide) may be drafted as a *correct* extrapolation, **flagged to the user as your
addition**.

**Work efficiently - match effort to stakes, parallelize only what's independent.**
- **Parallelize independent work, never a single argument.** Fan out across *separate* documents,
  or batch asset prep via the **asset-prep executor** (`agents/asset-prep.md` - execution-only, runs
  after the DESIGN plan is approved, makes ZERO design decisions) - but never split one paper's
  intro/method/results across blind agents. Use host multi-agent/subagent tools when available.
- **Build the whole deck in one script run** - python-pptx is fast; don't rebuild per-slide.
- **Scale the critic to stakes** (Step 5): two focused lens critics for a quick deck; the multi-critic
  + arbiter panel for high-stakes. The loop is non-negotiable; its *weight* is what you tune.

**Two modes.** *Standard* (default): interview -> 🔴 checkpoints -> build -> critic loop. *Collaborative*
(opt-in - when the user wants options or approval as you go): build behind cheap gates (direction ->
outline -> build). Offer it in one line; never force it. See `references/collaborative-mode.md`.

**🔴 CHECKPOINT convention.** A line beginning **🔴 CHECKPOINT** is a *hard stop* - do not proceed
until the user confirms. Honor every one. The **per-deck AUTO WAIVER** (distinct from Standard
mode): a "decide everything yourself / just show me the result" directive waives the checkpoint
*stops* for THAT deck only (a redo/new deck resets to default). The checkpoints stay **visible -
posted in chat as compact terminal-friendly markdown tables** (FYI under the waiver). The waiver
covers preference/approval stops only; 🔴 stops requesting information you cannot supply (e.g.
missing `~/Downloads`) follow their own auto rule. A veto/correction posted against any FYI while
the build is running is a **HARD INTERRUPT** - stop, revise, post revised FYI, then resume.
**Full format spec (content/design checkpoint fields, auto-waiver delegation, FYI contract, gate
lines):** 详见 `references/checkpoint-format.md`.

## At a glance - pipeline · rule strengths · where things live
*A navigation map only; the steps below are the source of truth.*

**Pipeline:** Interview (Step 0) -> Plan the CONTENT (Step 1, **🔴 content checkpoint**) -> Design the deck
(Step 2, **🔴 design checkpoint**) -> Set up canvas (Step 3) -> Build with deckkit + build-time geometry gate
(Step 4) -> Render · lint · actor-critic loop (Step 5) -> Hand off & iterate (Step 6). Every **🔴 CHECKPOINT**
is a hard stop.

**Rule-strength vocabulary:**

| Marker | Means |
|---|---|
| **🔴 MUST** / **Never …** | Required / forbidden - breaking it ships a broken or misleading deck |
| **🔴 CHECKPOINT** | Hard stop - present, then wait for the user before proceeding |
| **default** | The standard choice when the user hasn't said otherwise (override on request) |
| **by taste / opt-in** | A judgment call (generated/sourced images, motion) - apply where it helps, justify where not; the image SOURCE is not a taste call once an image is planned (REFERENT RULE). Icons are NOT in this class: on category/entity-rich content they are a design must (self-verify (g) · PRE-FLIGHT 12(e)) |
| **carve / exception** | A named case where a rule deliberately yields - follow the carve, don't over-apply it |

> **Enforcement invariant:** every 🔴 MUST must be *wired into a gate artifact* - an interview question,
> a required plan field/column, a self-verify item, the PRE-FLIGHT checklist, a deterministic lint check,
> or a named critic-rubric item. A MUST that lives only in reference prose is advisory in practice. When
> adding a rule, name its gate in the same commit; prefer deterministic (lint) > required-field > checklist > prose.

**Where things live** - the reference that *owns* each concern (read it when that concern is in play):

| Concern | Owner |
|---|---|
| The craft / the "why" (contrast · hierarchy · C.R.A.P. · layout safety) | `references/design-principles.md` |
| Per-purpose look (defense vs exec vs lecture …) | `references/design-by-purpose.md` |
| Content - deep read + per-slide message (Step 1) | `agents/content-planner.md` |
| Input formats - Word/Office · image · video | `agents/content-planner.md` §1 · `scripts/ingest.py` |
| Long source (book / very long PDF / repo) - map -> triage -> deep-read | `agents/content-planner.md` §1 · `scripts/extract_pdf.py map`/`text`/`headings` |
| Look / form / layout / rhythm / icons / motion (Step 2) | `agents/slide-design.md` |
| Independent review + JSON schema | `agents/critic.md` · `agents/arbiter.md` · `references/review-rubrics.md` |
| Which visual FORM a slide takes (avoid the card-grid default) | `references/form-selection.md` |
| Colour-means-one-thing (bind a hue to a concept deck-wide) | `references/semantic-color-contract.md` |
| Style + component catalogue (looks · presets · when to use each) | `references/design-gallery.md` |
| Charts (which type · editable-native vs raster) | `references/data-viz.md` |
| Choropleth map (value per country / province) | `deckkit.choropleth()` · `scripts/maps.py` · `references/data-viz.md` |
| Science schematics (force / ray / circuit / apparatus …) | `references/schematic-diagrams.md` |
| Generated + sourced imagery (when/how · text-free · topical · REFERENT RULE) | `references/image-generation.md` |
| Generated-template branch (hero + shallow bg + frosted blocks) | `references/generated-template.md` |
| Icons (one family · recolored · treatments) | `references/icons.md` |
| Mimic a provided style example | `references/style-analysis.md` |
| Fonts / portability / tofu · non-Latin & CJK | `references/font-guidance.md` · `references/multilingual.md` |
| Animation / appear-builds | `references/animation.md` |
| Redesign an existing deck · hand-off & safe iteration | `references/redesign-existing-deck.md` · `references/handoff-and-iteration.md` |
| Cross-deck user taste - registry-root `taste.md` schema · read/write · dial promotion | `references/user-taste.md` |
| Large / sectioned decks · collaborative gates | `references/large-deck-orchestration.md` · `references/collaborative-mode.md` |
| East-Asian / ink looks | `references/east-asian-aesthetic.md` |
| Canvas formats (16:9 default · 4:3 · 1:1 · 小红书 3:4 · story 9:16 · A4) | `scripts/formats.py` · `references/canvas-formats.md` |
| The build helpers (source of truth) | `scripts/deckkit.py` (docstrings) · `references/build-helpers.md` |
| Geometry lint - build-time · render-time | `deckkit.lint_layout(prs, strict=True)` (Step 4) · `scripts/lint_deck.py` (Step 5) |
| ANY error / lint finding / env failure - symptom -> cause -> fix | `references/troubleshooting-faq.md` (open it BEFORE improvising a fix) |
| Deck-level design gates - rhythm · block-dependency · semantic-colour · variation | `references/design-intelligence-addendum.md` |
| **Step-0 interview Q1-Q4 full branch logic + direction gate + carves** | `references/interview-protocol.md` |
| **Checkpoint artifact format spec + AUTO WAIVER full rules** | `references/checkpoint-format.md` |
| **deckkit component catalogue (helpers by job)** | `references/build-helpers.md` |
| **Figure handling rules (integral/crop/legend/axis)** | `references/figure-handling.md` |
| **PRE-FLIGHT 12 items (full criteria)** | `references/pre-flight-checklist.md` |
| **Contract Card + critic dispatch + arbiter panel** | `references/critic-dispatch.md` |

## Step 0 - Interview the user first (always)
**Run this interview every time, from scratch - do not skip it because earlier conversation, a previous
deck, or context "obviously" implies an answer.** Collect all four answers in **one cheap interview
turn** (match the host UI: structured-choice if available, else one compact direct question). The
interview is non-negotiable, so it has to be *cheap* - only drop a question if the user already answered
*that* one, or the deck runs under a full per-deck auto directive (you answer preference questions by
delegation, post picks as first FYI; the topic/source-material floor still gets asked).

> **Scope guard:** fires for DECK-BUILDING asks only (make/redesign/improve a deck). An audit/review/extract/
> question is NOT a build - do it directly. When in doubt, one clarifying line beats a wrong assumption.

**🔴 MUST: never assume the topic/content, the style, or which template - confirm each.** Never
hardcode or assume a specific institution's template (a brand-new user has an empty registry). **Precedence
(🔴 MUST): current request > this interview's answers > `taste.md`** - the profile seeds defaults and
options only and never overrides an explicit answer or checkpoint decision. Personalize options only from
THIS user's own footprint - never a hardcoded or guessed domain. Scale the interview to the ask (a tiny
ask still needs purpose + content confirmed).

The four questions (full branch logic, carves, direction gate, follow-ups): 详见 `references/interview-protocol.md`.
**Language (decide it, then hold it):** default to the user's language; when source material differs, ask
which language the slides should be in (offer bilingual as an option). See `references/multilingual.md`.
**完成条件:** four answers collected (or delegated picks posted as first FYI under auto-waiver); language decided.

## Step 1 - Understand & plan the CONTENT (use the content-planner)
**Use `agents/content-planner.md` for this step - the CONTENT only.** Dispatch it through an available
multi-agent/subagent tool when the host exposes one, otherwise run the same planner brief inline. It returns
a **Content plan** - message only, no design: a comprehension brief + a claim ledger + the authors'-emphasis
check + the narrative arc (incl. the planned emotional curve) + a per-slide CONTENT spec (takeaway that
passes the memory test · role · question · beat · content units · visual source). You take that plan into the
**Step-1 CONTENT checkpoint** before any design begins.

**The bar - understand it deeply, don't skim.** Read **all of it**, not the abstract. Then write a
**comprehension brief** (REQUIRED, fixed-field, source-traced) + a **claim ledger** (every
number/date/name/citation/superlative as a row with source + verbatim value + verified?(Y/N) + as-of date;
an unverifiable claim is cut or marked open, never shipped).

**This is a hard gate, not a sanity check.** Self-verify the brief against the source; if any field is
empty, hedged, or untraced - or the emphasis test fails - you have NOT understood it. **An incomplete or
untraced brief blocks the build.** Every slide must be faithful to the authors' actual emphasis.

**Having a source is rarely the whole story - use the web for the gaps, even with one.** Re-verify the
source's own falsifiable / time-bound claims at *today's* date (a "state-of-the-art" or "first/largest" may
be stale by presentation day). For a **no-source deck**: draft an outline, then **ground *and verify* it**
with web search/fetch - treat this as a **fact-check, not just framing**. 🔴 **Never present an unverifiable
claim as established fact.** If NO web tool is available, mark each claim *open/unverified*, soften it, and
**ask the user to confirm** - never ship an unchecked "fact." Ground to *today* and re-verify time-bound
claims on every build. For a **long source** (book / very long PDF): run **long-source mode** (map -> triage
-> deep-read the load-bearing ~20% + a Source-coverage map); see `agents/content-planner.md` §1.

**Precondition - the comprehension gate:** before showing the plan, confirm it carries a *complete*
comprehension brief (every field filled + traced), a claim ledger (no shipped `verified? = N` rows), a
Takeaway spine that reads as one argument, a `scripts/plan_wordcount.py` pass over the per-slide table,
a `source size:` line on any file-sourced deck, and for an over-threshold long source a complete
Source-coverage map. An empty/hedged/untraced brief is **not ready** - send it back to the planner.

**The pace / slide-count check happens HERE.** For a *spoken* deck scale to the time budget (~1
slide/min); **confirm the resulting slide count** with the user (never ship a length they never saw).
A *read-alone / poster* deck has no talking-minute budget - its scope is set by content completeness.
> **🔴 CHECKPOINT - CONTENT:** show the comprehension brief + claim ledger + narrative arc + the
> per-slide takeaways/content, and confirm the pace/slide-count, before any design work begins - rendered
> as the compact ≤~25-line checkpoint artifact (详见 `references/checkpoint-format.md`). **For a long
> source, the artifact also carries a DIGEST of the Source-coverage map and the SELECTION is confirmed here.**

## Step 2 - Design the deck (use the slide-design agent)
With the **Content plan approved**, first build the **Evidence manifest** - one READ-ONLY line per named
asset: `asset | locator | WxH (px/pt) | aspect class | table RxC | value range (optional)`. Probing NEVER
materializes crops/equations/plates - asset-prep still runs only AFTER the design plan is approved. Then
dispatch `agents/slide-design.md` - the deck's **art director** - to design the look on top of the locked
message. It consumes the approved content (it does **not** reopen it) and returns a **Design plan**: the
deck's **Design language** (a *named* signature motif + a deliberately-chosen palette/type + the polish
moves), the **deck rhythm**, a **per-slide design table**, the **Form ledger + diversity gate**, the
**design self-verify checks**, the **10-item design-critic checklist**, and the **image opt-in list**. The
art director is *one mind* over the whole deck.

**This design intelligence runs on EVERY deck** - it's how the art director designs, never opt-in per deck
- and scales down gracefully to small decks; only the deck-level numeric floors are size-gated.

**Precondition - the design gate:** the plan is **not ready** unless it has:
- A concrete **Design language** (a *named* signature motif + a deliberately-chosen palette/type, not a
  defaulted light/minimal/blue).
- A one-line **`taste profile:` field** (or the `look LOCKED` carve for a registered/provided template).
- **`boldness:` line** (conservative | balanced+ | bold | experimental - default balanced+) **AND a real
  `signature move:` line** - the ONE deliberate aesthetic RISK, scoped to where it lands + adapting a named
  bold reference, **plus a `carried_by:` clause** naming 2–3 slides where the idea does STRUCTURAL work.
  A `signature move` that reduces to "a big number / a nice gradient / a full-bleed photo" is the safe
  catalogue, **not** a signature move - makes the plan incomplete (send it back). Only `boldness: conservative`
  softens the field to a "deliberately restrained" clause. The risk lives on composition/scale/concept/type
  and **never** overrides a floor.
- **`AR a.b -> <zone>`** annotation in the Layout cell of every slide placing a manifest-listed figure/table.
- A **Form ledger** whose diversity gate passes (no one format-family on >~40–50% of content slides - the
  card-overuse guard), plus the addendum's **deck-level design gates** (rhythm map · semantic-colour ledger ·
  block-dependency audit · minimum deck-level variation).
- For a **company/product/single-entity deck**: a **`logo plan:` line WITH EVIDENCE** (`official asset -
  <source>` / `searched, none found -> designed wordmark (flagged)` / `n/a - <reason>`). A bare "wordmark"
  with no recorded search, or a missing line on a single-entity deck, makes the plan **incomplete**.
- The **THREE DESIGN MUSTS** addressed: **(1)** appear-builds - ONLY if the user opted in (if IN, a motion
  manifest places builds where they help and each built slide is staged FULLY; if OUT, every slide is
  `static: user opted out` - complete, not a gap). **(2)** a style-matched SVG icon family on any
  category/entity-rich deck - every branch, incl. generated-template. **(3)** diverse formats (not a card
  grid repeated). Musts 2–3 are *applied where they help or justified where not*.

**The per-slide content-image opt-in is a CROSS-CUTTING choice, available on EVERY deck** - not tied to
the template choice. Three guardrails: **(a)** each plate is *content-related* (depicts THAT slide's actual
subject, never generic filler); **(b)** SMART about where (only the few slides that genuinely earn one,
NEVER every slide); **(c)** the **REFERENT RULE** picks the source (a real-and-specific subject gets a REAL
license-clear sourced photo; a declared stylized illustration is a nameable deviation). Every image row
carries its source token per `references/image-generation.md`.

> **🔴 CHECKPOINT - DESIGN:** show the Design language + Form ledger + the 3 design musts + the
> **`boldness:` line + the `signature move:` line** + the image opt-in list (each row with its source token)
> + (for a single-entity deck) the **`logo plan:` line WITH evidence token** + the **motif line** (device +
> meaning + legibility mode - the STRANGER TEST) - presented as the compact checkpoint artifact (详见
> `references/checkpoint-format.md`, same fields incl. rhythm-map table and `direction gate:`/`style gate:`
> line) - and get the user's OK before building.

## Step 3 - Set up the canvas
**First, decide where the deck lands.** Deliver each deck as one self-contained folder in the user's
Downloads - `~/Downloads/<deck-name>/`, holding the `<deck-name>.pptx` and a `render/` subfolder of slide
PNGs - so the user gets a tidy, findable bundle rather than a stray file in `/tmp`.

**🔴 The `.pdf` and `viewer.html` are NOT produced during the build.** They are **reserved deliverables**:
generated at hand-off (Step 6) once the user confirms the deck is final, with `render_deck … --deliverables`.
Point your build script's output path and `render_deck.sh`'s out-dir there from the start.

> **🔴 CHECKPOINT** - if `~/Downloads` is missing, ask where to save before writing any file.
> *(Per-deck auto: this checkpoint is a question, so it has no FYI form - do not stop. Default:
> `mkdir -p ~/Downloads` when home is writable; only if home is unwritable, use `./<deck-name>/`. Never
> `/tmp`. State the chosen location in chat the moment you decide it.)*

**Canvas format (only when the interview picked a non-default surface).** Default is 16:9 via
`deckkit.blank_deck()`. For a different surface (4:3, 小红书 3:4, square 1:1, story 9:16, A4), start from
`scripts/formats.py` and follow `references/canvas-formats.md` (per-surface layout DNA + repurpose pattern).

**Keep the per-deck build script (`build_<deck>.py`) in that same folder, beside the `.pptx`.** The build
script - not the rendered file - is the *source of truth* for the deck, so it should travel with the
artifact. Resolve deck assets relative to the script file (`ROOT = Path(__file__).resolve().parent`).

- **Template branch:** run `scripts/inspect_template.py <file.pptx>` to learn layout indices,
  placeholder ids, logo locations. Then `deckkit.open_template()` loads the deck and wipes old slides
  while keeping masters/layouts. Pull brand colors and set deckkit palette/`FONT` to match. Save a
  `profile.md` to the active template registry.
- **No-template branch:** `deckkit.blank_deck()` + `deckkit.add_slide()`, consistent chrome with
  `deckkit.title_bar()` / `deckkit.footer()`. **Don't just accept deckkit's default blue - design the look
  to fit the purpose.** Set palette via **`deckkit.set_palette(...)`** (call ONCE right after import) + a
  role-based font pairing, or adopt a `scripts/presets.py` `preset(name)` and tune it. **Vary the look
  deliberately across decks - sameness is the failure to avoid.**

**Fonts for non-Latin languages (CJK):** set `deckkit.EAFONT = "Hiragino Sans GB"` (or Microsoft YaHei /
Noto Sans CJK SC), keeping `FONT` for Latin/numbers. **Font portability:** pick fonts present on every
machine that will open the deck. Full guidance: `references/font-guidance.md` · `references/multilingual.md`.

**完成条件:** output folder resolved + announced; build script (`build_<deck>.py`) started; canvas format
set; fonts configured.

## Step 4 - Build with deckkit

> ### 🔴 Step 4 opens with the SIGNATURE PROOF - one slide, rendered, BEFORE the other slides exist
> The `boldness:` / `signature move:` contract is approved as **prose**. Put the evidence where the decision is:
> 1. Author the **signature slide first** (the one the `signature move:` line names) + its `carried_by:` partner.
> 2. Build, then render just that page: `python3 scripts/render_deck.py <deck>.pptx <out> --slides N` (~5s).
> 3. **Post the PNG** with one line: *"this is what `<signature move>` actually looks like."* A 🔴 stop in
>    the default flow; under AUTO WAIVER, a posted FYI - the waiver removes the wait, never the artifact.
> 4. Then author the rest. If the proof is wrong you have re-authored ONE slide, not twenty.
> 5. **Record it** - the run carries a `signature proof:` token to Step 5 on the critic contract card:
>    `signature proof: slide N -> <png path>` or `skipped: <the named carve>`.
> **Skip only when:** `boldness: conservative` with its "deliberately restrained" clause recorded, or a 1–2
> slide tiny-ask. A registered/provided template does NOT skip it.

Write a small per-deck build script that imports `scripts/deckkit.py` (don't re-derive primitives). **Build
the approved Design plan** as the source of truth - the slide-design agent already chose each slide's visual
FORM and the user approved it, so **don't re-derive an approved form.** *Fallback only where the plan left
something open:* pick that slide's form deliberately - generate 2-3 candidate forms and choose with the
tie-breaker in `references/form-selection.md`; **don't default every multi-item slide to a card grid.**

> **🔴 When a COMPONENT exists for the form, BUILD that component - do NOT hand-roll a substitute from
> raw `box`/`connector` primitives.** Reaching for a plotted form (`waterfall`, `gantt`, `dumbbell_board`,
> `dot_strip`, `tier_stack`, `native_chart`, `eval_matrix`, `heat_matrix`, `meter_bar`, `timeline` …) and
> then hand-drawing it with boxes **re-introduces the exact geometry & grammar bugs the component already
> fixed.** This is the #1 source of "the chart looks messy / wrong" defects. Adapt a component's params or
> compose from primitives ONLY for a form the library genuinely lacks - and *then* derive every axis /
> baseline / track extent from the data. Full component catalogue: 详见 `references/build-helpers.md`.

**A few rules that matter** (see `references/design-principles.md` + the owning references):
- **Use the source's own figures, WHOLE - integral is the default.** Never redraw, never chop into pieces.
  Full figure handling rules (integral/crop/legend/axis/PDF extraction): 详见 `references/figure-handling.md`.
- **🔴 Never clip the figure's OWN parts.** Crop the complete SEMANTIC object, not an arbitrary rectangle.
  The legend, colour bar, axis titles/labels/ticks, error bars, panel labels are all *part of the figure*.
  Re-view every crop after placing/scaling - confirm nothing is cut off or flush.
- **Animated results (GIF) -> insert the GIF itself with `deckkit.gif()`**, never reduce to a single frame.
- **Data but no figure yet -> make the chart, don't dump numbers.** For non-Latin languages or when the user
  will edit, use an EDITABLE native chart (`deckkit.native_chart`). Pick the chart TYPE that fits the argument.
- **Concept needs a domain image -> show the real thing, not an abstract icon.** Compute the real artifact.
  Make the plot actually look CORRECT (finely sample curves; legend OUTSIDE the data; always view the PNG).
- **Generated visual plates - by taste & purpose, opt-in** (详见 `references/image-generation.md`). 🔴 **Never
  bake words/numbers/labels/charts/logos into a plate.** Each plate must be *highly topical*. The OpenAI-API
  path is **metered and gated** (🔴 BILLING GATE - ask first).
- **Brand logo on every page when the deck is ABOUT one company/institution/product.** Use `deckkit.logo()`
  per slide on clean/generated decks; on a provided/registered template the branding usually lives on the
  layouts (don't double it). Source in order: real logo -> clean designed **WORDMARK** (`deckkit.wordmark`)
  -> ask the user. **Never ship placeholder text on a slide.**
- **SVG icons - ONE coherent open-licensed family, recolored, used with restraint** (详见 `references/icons.md`).
  Fetch via `scripts/icons.py`; vary the *treatment* to fit the deck. **Always pair an icon with a text label.**
- **Speaker notes - for a PRESENTED deck, put the spoken script in the notes, not on the slide.** Pipe from
  the content plan's Spoken thread, don't re-draft. For a read-alone deck, prose belongs ON the slides.
- **🔴 Gate the geometry at BUILD time - end the build script with `dk.lint_layout(prs, strict=True)` before
  `prs.save()`.** `strict=True` makes it a *real* gate: an unresolved CRITICAL **raises and the deck is
  never saved**. It hard-fails on: content off-canvas, text overflowing a visible box, text-on-text overlap,
  a connector routed through a block, a decorative RULE drawn through a text block, CJK runs with no `<a:ea>`
  font. *(Each code's plain-language meaning + first fix: `references/troubleshooting-faq.md` §4.)* It is a
  **net, not a substitute for looking** (the critic's job).
- **Layout essentials:** stay in the safe area (`content_band()`); give text padding; no text-on-text;
  `fit_text_size()` if it doesn't fit; vertically centre text in self-contained blocks; grid/stack over
  hand-picked y with a real gap (~`GUTTER`); for a diagram, compute all bounding boxes first, then draw.
- **🔴 Never hand-pick a y for an auto-growing block - measure or anchor.** Use `bottom_callout()` (anchors
  to footer, grows up), `content_band()`, `vstack(..., bottom=...)`. Reserve the bottom callout's space
  BEFORE sizing content above it - don't add it last.
- **Colour.** Rotate `deckkit.ACCENTS`; reserve magenta for emphasis. `deckkit.palette(n, ACCENTS)` returns
  `n` distinct fills and warns on adjacent same-hue. **Never use a neutral gray as a category colour.** **Bind
  each hue to ONE concept deck-wide** (详见 `references/semantic-color-contract.md`). **🔴 A hue used as TEXT
  must itself clear ≥4.5:1 on its background** - keep TWO tokens per accent when needed (bright fill-only +
  darker text-safe). The same split covers a MARK ON A FILLED GROUND (~3:1).
- **Equations - 🔴 default to EDITABLE native math (`equation_native()`); raster (`equation_png()`) is the
  fallback for 2-D layout only.** Never paste Unicode super/subscripts (ᴴ ᵀ ᵣ) - tofu. Size the formula to
  ≈ body text (consistent across slides), never blown up to fill the slide width. Math font is a real
  dependency - flag it at hand-off. Full guidance: `references/font-guidance.md`.
- **One language** throughout - don't drift. Technical terms / proper nouns / acronyms / units / code may
  stay original; only build mixed/bilingual decks when the user asked (`references/multilingual.md`).

**Scaling up - section fan-out for large decks (optional).** Default is single-author up to ~14 slides. For
15+ slides or independently-sourced sections: centralize coherence (shared `style.py`), dispatch one
subagent per *section* (not per slide), assemble with `scripts/assemble.py`. Full workflow:
`references/large-deck-orchestration.md`.

**Motion & builds - the animation that matters is in-slide "appear" builds, NOT slide transitions.** 🔴 **Do
not "animate" a deck by putting a fade transition on every slide.** Builds are the USER's opt-in choice. If
IN, YOU decide WHERE, and a slide that gets a build is staged FULLY (every content element in a step, nothing
pre-shown but the title/frame). If OUT, the deck is static. Use `scripts/anim.py`; recipe in
`references/animation.md`. Record a one-line motion manifest per slide (`build: <what reveals>` or
`static: <why>`).

### 🔴 PRE-FLIGHT - tick these 12 before the first render, EVERY deck, no exceptions
**Emit it as twelve literal ✓/✗ lines** - writing the ticks is what forces the checks to actually run.
The 12 items (speaker notes, builds, plan↔code correspondence, charts native, evidence real, colour keyed,
register carries all pages, claims current, language & hygiene, eye path, hand-off ready, titles bound to
takeaways + form diversity & frame fill tally): 详见 `references/pre-flight-checklist.md`.
**`component_audit.py` is ADVISORY BY DESIGN and must never be treated as a blocker.**

**Gates never collapse.** A quick / low-stakes / inline run scales the *size* of each artifact, never the
*existence* of the gates: interview -> content plan -> design plan (with self-verify) -> pre-flight -> lint+stats
-> critic. Every rule-miss this skill has shipped happened when a step was run "in my head" instead of emitted.

## Step 5 - Render, verify, then run the actor–critic loop
**You should already have run the build-time geometry gate** (`dk.lint_layout(prs)` at Step 4) and cleared
its CRITICALs in-process, so the render loop starts mostly geometry-clean.

First **render and look** (`bash scripts/render_deck.sh <deck.pptx>` -> one PNG per slide). python-pptx
writes blind - overflow, low contrast, a callout on the footer, or a missing glyph only show up in the
image. Fix mechanical issues and re-render. **When anything fails or flags** - open
`references/troubleshooting-faq.md` FIRST: it maps every error surface to symptom -> cause -> first fix.
When surfacing a finding to the user, say it in plain language, never as a raw lint code.

**Iterating on a deck you already rendered? Add `--fast`.** `render_deck … --fast` fingerprints every slide
and re-renders only the changed ones (~4.7s for a one-slide edit vs ~12s full; byte-identical output).

**Then run the layout lint** - `python scripts/lint_deck.py <deck.pptx>` (add `--json out.json` for a
structured copy to hand to critics). It re-checks geometry on the FINAL file and adds the render/parse-only
faults (invisible/low-contrast text, off-slide overflow, uneven card heights, overlapping blocks, footer
collisions, orphaned punctuation, CJK with no EA font, whole-page-image, orphan slides). It also prints soft
`[warn]`s (missing alt-text, math-font tofu risk, LOW/BODY CONTRAST bands, accessibility set, TEXT ON IMAGE).

**READ the DECK STATS block - don't skim past it.** Its `[stats]` warnings name the rule they measure:
`TEXT WALL`, `CROWDED`, `LAYOUT SAMENESS`, `FLAT TYPE`, `SMALL TYPE`, `SIZE SPRAWL`, `NO BUILDS`,
`SKELETON VARIETY`, `TIMID COVER`, `FLAT RHYTHM`, `CJK TIGHT LEADING`, `CJK-LATIN SPACING`. Treat each as the
NAMED design rule having failed measurably: fix it or write one clause of why this deck is the exception.
**Paste the stats block into the critic's input** so the judges score numbers, not impressions.

**Render self-check - scan EVERY slide for these before handing to the critic** (invisible in build code,
only in pixels): overflow / contrast / footer / glyphs (no orphaned punctuation); no build/meta annotation
visible; stacked groups read as separate; balance & suitable space; block padding & no inflated filler; font
hierarchy (content < title); hero numerals read clean; chart axis spans every bar / no double-count;
geometry matches the number; formula sized to content; no rule/divider crossing text; footer collision /
overlap; adjacent blocks have a VISIBLE gap (≥ ~⅓ `GUTTER`); bar labels sit ON the bar; marker captions sit
UNDER their marker; diagrams (arrows point the right way, connector labels sit in the open gap); block colours
distinct; mark-on-fill contrast (~3:1); titles rotate 2–3 chrome treatments (no `TITLE-RULE MONOCULTURE`);
images subject whole & factually right; text over an image legible (no linework crossing glyphs, ≥4.5:1,
clear title↔subtitle gap); PDF figures cropped precisely (zoom each edge).

**On native Windows (no bash):** call the Python entry points directly - `python scripts\render_deck.py
<deck.pptx>` and `python scripts\check_env.py`. The `.sh` files are just shims that forward to the `.py`
scripts.

Then run the **actor-critic loop** - the quality engine, and the critic is a *demanding* judge
(`agents/critic.md`), not a rubber stamp. **Full Contract Card assembly + critic dispatch + panel scaling +
arbiter cross-validation + promote/discard rules:** 详见 `references/critic-dispatch.md`.

1. **Critique.** Dispatch an independent critic subagent pointed at `agents/critic.md`, giving it the
   rendered PNGs, the deck's purpose + audience (+ delivery mode + density), `references/review-rubrics.md`,
   the motion manifest, **the CONTRACT CARD**, and the source material (so it can verify claims/figures).
   **Validate the review BEFORE acting on it:** run `python3 scripts/validate_review.py critic <json>`; a
   review failing conformance/coverage is **rejected and re-dispatched once** - never acted on.
2. **Decide.** Stop as soon as `verdict == "consent"` - not merely when the last round's issues are fixed.
   Cap rounds by stakes: **low-stakes ≈ up to 2, high-stakes up to 3.**
   > 🔴 **One exception to "surface it and ship": a surviving `timid` / `sanded-to-safe` distinctiveness
   > finding on a deck whose `boldness:` is `bold` or `experimental`.** There the deck does **not** ship on
   > your say-so - after one improvement attempt, put the choice to the USER: *(a) one more round - naming
   > the concrete change; (b) ship as-is, recorded as a knowing accept.* Either answer ships it; what changes
   > is **who waives**. At `balanced+`/`conservative`: one attempt, then ship with the note. **Record the
   > outcome in the Step-6 hand-off note** - `distinctiveness: user waived (bold)` or `resolved in round N`.
3. **Repeat.** The critic **re-reviews the whole deck fresh** (fixes introduce new issues). Converge.

**🔴 PRIMARY-SOURCE GATE - research-sourced decks only, before hand-off.** When the deck's load-bearing
claims came from **web research** (every no-source deck, and any sourced deck where research supplied
slide-level numbers/quotes), run one **adversarial primary-source spot-check**: independent verifier agent(s)
with live web access take the deck's load-bearing claims and try to **REFUTE** each against its **primary
source** (the original paper / org's own post / official docs - never an aggregator). **WRONG and
PARTLY-WRONG are fixed before ship; UNVERIFIABLE is hedged as unverified or cut - never shipped as established
fact.** Scale to stakes (quick deck: one verifier over top ~10 claims; high-stakes: fan-out over all). **Never
skip it entirely on a research-sourced deck.** The Step-6 hand-off carries one `provenance:` line - `N claims
checked · N confirmed · N fixed · N cut/hedged` - a research-sourced hand-off without that line means the
gate did not run. Decks built purely from the user's own material skip this gate.

**High-stakes only - verify the fixes and corroborate consent.** Arbiters re-check each promoted finding
against the actor's change manifest; a fix that didn't land stays open. Accept final consent only when
`verdict == "consent"` **and** a confirmation pass sees no surviving blocker/major. **Fail loudly at the cap:**
if rounds are exhausted and a *contested* blocker remains, don't silently ship - hand the user that one
disagreement in Step 6 as an honest question.

## Step 6 - Show the user, then iterate on feedback
Present the rendered slides (or a contact sheet) plus a short note: slides count, purpose it was built for,
and the font/portability caveat if relevant. **Tell the user the exact output folder path** and ask them to
open and check the `.pptx` - the rendered PNGs verify layout, but they should confirm the editable deck opens
cleanly on their machine. **Then OFFER the two reserved deliverables** - a **`.pdf`** (submission / email /
print) and a **`viewer.html`** flip-through preview (one `file://` link, any browser, no PowerPoint needed).
Ask in one line; on a yes - or once the user confirms final - run `render_deck … --deliverables`.
**Re-run it after any later change** so the pair never lags the deck. If you added forward-looking content,
call that out explicitly.

**Keep the hand-off minimal - caveats + next steps, not a recap.** The note carries only what the user *acts
on*: folder path, open-the-pptx check, font/portability caveat, forward-looking content, open questions -
**plus these REQUIRED-by-their-owning-rule lines when they apply (this is the ONE authoritative hand-off
checklist):** the `provenance:` line (research-sourced decks), per-slide **click order** (appear-builds),
**image licenses/credits** (sourced photos), the **GIF plays-in-slideshow** note, **accepted advisories** one
plain-language line each, the **`distinctiveness:` line** whenever Step 5's bold/experimental escalation fired,
and on an auto-waiver deck the **delegated-picks recap** - and, optional (exactly one sentence), the critic's
`ceiling` verbatim as an *"if you want to push it further:"* line. Two taste-ecosystem lines when they apply:
**(a)** the save-this-look offer (for a freshly-designed look not yet registered - skip under per-deck auto
directive); **(b)** the taste write-back FYI. Do **not** narrate slide-by-slide, restate what they can see,
or self-praise - a tight hand-off respects their time and reads as senior.

**For a long deck (~15+ slides), show work at ~50%, not only at 100%.** Render the first few finished slides
and check in before completing the rest. (A soft check-in, not a 🔴 stop: under auto-waiver, post as FYI and
continue.)

**Tell them the deck is fully editable - and how to change it without losing work.** Two lanes: **(a)** take
it from here in PowerPoint themselves (you won't rebuild over their file), or **(b)** tell you the changes
and you edit the build script (reproducible, survives future iterations). Full guidance:
`references/handoff-and-iteration.md`.

Then **fold in the user's feedback** - treat corrections as the highest-priority signal, re-run the build ->
render -> critic loop, keep going until **the user is satisfied**. **One safety rule when iterating after
delivery:** before re-running the build, check whether the user hand-edited the delivered file; if they have,
**don't regenerate over it** - reconcile first. **Never silently clobber edits you didn't make.** On each
user-feedback round, add one **`user-dials:`** line - `dimension -> direction, layer - "verbatim user words"`.

**Step-6 close - the taste write-back** (named checklist; full protocol in `references/user-taste.md`):
1. **Append ONE look-history line** for the delivered deck to `taste.md` at the registry root.
2. **Promote a dial into `taste.md` ONLY on the recurrence gate (🔴 MUST):** the user's own words mark it
   standing ("always", "一直", "in general"), **or** the same dimension+direction appears in ≥2 distinct
   decks' round records. One-off or purpose-driven corrections stay deck-scoped. Every promoted row carries
   its verbatim quote + deck + date; conflicting later feedback UPDATES the existing row, never appends a
   contradiction.
3. **Announce every write in the hand-off FYI line with the easy veto** - a silent write didn't happen.
A brand-new user with nothing durable gets no writes and no FYI.

## Anti-patterns - never do this
A checkable red-flag list; if a draft does any of these, stop and fix it before shipping:
- **Never invent** numbers, results, citations, or figures the source doesn't state (the one allowed
  exception is *flagged* forward-looking content).
- **Never skip the interview**, and **never assume** the topic/content, template, style, or - for a
  brand-new user with no footprint - a domain (ask the subject openly).
- **Never present last year's data as current** on a deck dated this year - ground to today.
- **Never leave a build/meta annotation on a slide** - "(editable native chart)", "(AI-generated)",
  "(placeholder)", "(draft)", "generated by…", TODO/FIXME. That goes in code comments or the hand-off.
- **Never let stacked groups blur together** - the gap between groups must beat the gap within a group.
- **Never leave a slide awkwardly empty, and never fake fullness with an oversized block** - enrich the
  content or enlarge the hero; never inflate a card/callout around a single short line to cover a gap.
- **Never set content text as large as (or larger than) the slide title** - only a deliberate hero
  numeral/equation may exceed body size, and it still stays below the title.
- **Never oversize a formula or leave a variable in plain text** - size every equation to ≈ body text
  (consistent across slides); set even a lone inline variable in math format.
- **Never act as your own final critic** - an independent critic must consent; **never ship a
  partially-rendered or contested-blocker deck silently** (surface the disagreement).
- **Never clobber the user's hand-edits** - reconcile before regenerating over their file.
- **Never** ship a wall-of-text slide the user didn't explicitly choose (Q4), a redrawn source figure
  where a real one exists, a cine GIF reduced to one frame, meaning carried by colour alone, or text below
  ~4.5:1 contrast.
- **Never** put real slide text, labels, numbers, logos, citations, source figures, or evidence-bearing
  charts inside an AI-generated image; generated images are text-free visual support unless explicitly
  requested.
- **Never** clip a figure's own parts (legend, colour bar, axis labels/ticks, outer row/column) with a crop
  or too-large placement, and **never** chop a multi-panel figure into context-losing pieces when the whole
  would serve - default to the integral figure; **re-view every figure after cropping/placing**.
- **Never** leave text in a callout / chip / takeaway bar visibly off-centre.
- **Never** paste Unicode super/subscripts (ᴴ ᵀ ᵣ); **never** build a "generic conference" deck (research
  the venue); **never** let the deck drift between languages.

## Files
**Scripts** (`scripts/`):
- `deckkit.py` - the build helpers (template & blank decks), **incl. the editable native charts**
  (`native_chart`/`native_dual_axis`/`native_donut`/`native_pareto`/`native_bubble`) **and the build-time
  geometry gate** (`lint_layout(prs, strict=True)`). Full component catalogue: `references/build-helpers.md`.
- `component_audit.py` - advisory tool: did this deck hand-roll a form the library already implements?
  **Advisory, never a blocker.** Run at PRE-FLIGHT 12.
- `directions_diversity.py` - mechanical divergence check for direction-gate candidates (4 axes). Run before
  posting the preview link.
- `render_deck.py` - pptx -> one PNG per slide. `--slides N` renders ONLY named pages (SIGNATURE PROOF /
  re-render loop). `--fast` re-renders only changed slides (cached fingerprint). `--deliverables` also parks
  PDF + `viewer.html` at hand-off. `check_env.py` - preflight if a render fails.
- `lint_deck.py` - deterministic **render-time** layout lint (complement to deckkit's build-time
  `lint_layout`). Run after render, before critic.
- `plan_wordcount.py` - advisory per-slide word-budget pass (Step-1 comprehension-gate check).
- `validate_review.py` - stdlib schema validator for critic/arbiter JSON (Step 5 runs it before acting).
- `anim.py` - PowerPoint click-builds/transitions. `formats.py` - named canvas-format registry.
- `designed_charts.py` - raster matplotlib chart recipes (waterfall, dumbbell, slope, etc.). `maps.py` -
  choropleth base maps. `presets.py` - 18 named design-language presets.
- `image_prompts.py` -> `generate_images_codex.py` (no-key) / `generate_images_openai.py` (**metered**,
  gated). `archetypes_html.py` (direction-gate previews as one HTML link). `assemble.py` (sectioned deck).
  `export_notes.py` (notes -> rehearsal script).
- `icons.py` - fetch/recolor/rasterize open-licensed SVG icons. `image_fx.py` - duotone/grayscale photo
  preprocessing. `extract_pdf.py` (figure crop + long-source trio `map`/`text`/`headings`).
  `crop_helper.py` (crop by looking, not guessing). `extract_deck.py` (pull content from existing deck).
  `ingest.py` (ingest non-PDF source). `inspect_template.py` (template layouts/placeholders).

**Agents** (`agents/`): `content-planner.md` (Step-1 CONTENT deep-understand + claim ledger) ·
`slide-design.md` (Step-2 art director - design language + per-slide form/layout/rhythm + icons +
appear-animation + Form ledger) · `critic.md` (independent critic - two review lenses + JSON schema) ·
`arbiter.md` (high-stakes finding cross-validation + fix-verification) · `asset-prep.md` (execution-only
asset materializer - crops/equations/plates/icons after design plan approved; zero design decisions) ·
`openai.yaml` (Codex display metadata).

**References** (`references/`, loaded on demand): `canvas-formats.md` · `design-principles.md` ·
`design-gallery.md` · `semantic-color-contract.md` · `review-rubrics.md` · `design-by-purpose.md` ·
`form-selection.md` · `schematic-diagrams.md` · `data-viz.md` · `image-generation.md` · `icons.md` ·
`generated-template.md` · `style-analysis.md` · `font-guidance.md` · `multilingual.md` ·
`east-asian-aesthetic.md` · `animation.md` · `large-deck-orchestration.md` · `collaborative-mode.md` ·
`redesign-existing-deck.md` · `handoff-and-iteration.md` · `design-intelligence-addendum.md` ·
`user-taste.md` · `troubleshooting-faq.md` · **`interview-protocol.md`** (Step-0 Q1-Q4 full branch logic) ·
**`checkpoint-format.md`** (CHECKPOINT convention + AUTO WAIVER format spec) · **`build-helpers.md`**
(deckkit component catalogue) · **`figure-handling.md`** (integral/crop/legend/axis rules) ·
**`pre-flight-checklist.md`** (PRE-FLIGHT 12 items) · **`critic-dispatch.md`** (Contract Card + critic
panel + arbiter).

**Registry** (NOT part of the skill): `~/.codex/slide-templates/` (Codex) · `~/.claude/slide-templates/`
(Claude Code) - the user's saved templates, **plus `taste.md` at the root** (schema + read/write protocol
in `references/user-taste.md`). Empty for a new user (no templates, no `taste.md` - silently skipped).
