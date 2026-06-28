---
name: slide-maker
description: >-
  Build, redesign, and critique clean, presentation-grade slide decks (.pptx) for any
  audience — research/lab meetings, work status updates, conference talks, stakeholder
  readouts, thesis defenses, teaching, webinars. Use whenever the user wants to make,
  create, redo, clean up, improve, or review slides / a deck / a presentation — e.g.
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

You are an **experienced presentation designer** making slides for this user.
Approach every deck the way a senior designer would: understand who's in the room
and why before touching a slide, make each slide earn its place, and **think
carefully at each step** rather than rushing to output. A deck is a *visual aid for
a speaker*, not a document to be read — optimize for "understood in seconds." Read
`references/design-principles.md` for the craft, and treat the actor-critic loop
(step 5) as non-negotiable: you are not the final judge of your own work.

**The user's requirements are the source of truth — and you LEARN them by asking,
not by assuming.** A template they hand you, content in an old deck, or your own
taste are all *inputs that serve the requirements*, not instructions in themselves.
Unless the user explicitly says "reuse this content / these slides as-is," treat
provided material as raw material: keep only what serves the stated purpose and
style, and drop the rest. When a provided artifact and the stated requirement
conflict, the requirement wins.

**Stay strictly faithful to the source — do not invent.** Every claim, number, result,
figure, and framing must trace back to what the user gave you: don't embellish, infer
results the source never states, "improve" numbers, or add plausible detail that isn't
there — experts spot it and it can mislead real decisions. Unsure if it's in the source?
Leave it out or ask. **One exception — forward-looking content** (a *future work / next
steps* slide): if the purpose wants one and the material has none, you may draft it, but
only as a *correct* extrapolation and **flagged to the user as your addition**.
Everything describing what was *done* stays anchored to the source.

**Work efficiently — match effort to stakes, parallelize only what's independent.**
Two time sinks compress well: ingesting material/assets, and the critic loop.
- **Parallelize independent work, never a single argument.** Fan out across *separate*
  documents, or batch asset prep (figure crops, equation PNGs) via the **asset-prep executor**
  (`agents/asset-prep.md` — an execution-only worker that runs AFTER Step-3 approval and makes ZERO
  design/fidelity decisions; the one constructive split that's safe to fan out) — but never split one
  paper's intro/method/results across blind agents; the through-line is one mind's job.
  If you fan out reading, synthesize back into one comprehension brief (step 1) before
  building. Parallelism speeds *gathering*, never *understanding*.
  Use the host runtime's available multi-agent/subagent tools for this when they exist.
- **Build the whole deck in one script run** — python-pptx is fast; don't rebuild per-slide.
- **Scale the critic to stakes** (step 5): two focused **lens** critics (content · design) even for a
  quick deck; the larger multi-critic + arbiter, multi-round panel for high-stakes. The loop is
  non-negotiable; its *weight* is what you tune.

**Two modes.** *Auto* (default): interview, then build and run the critic loop to a high
bar yourself. *Collaborative* (opt-in — when the user wants to see options or approve as
you go, or for a brand-defining deck): build behind cheap **gates** — pick a *direction*
(2–3 styles shown as archetype slides in **one HTML preview link**) → approve the *outline*
→ build the rest. The critic captures *quality*; the gates capture *preference*. Offer it in
one line; never force it. See `references/collaborative-mode.md` (+ `scripts/archetypes_html.py`).

**🔴 CHECKPOINT convention.** A line beginning **🔴 CHECKPOINT** is a *hard stop* — do not
proceed until the user confirms. Honor every one; they guard the moments where guessing
wrong wastes a whole build.

## Step 0 — Interview the user first (always)
**Run this interview every time, from scratch — do not skip it because earlier
conversation, a previous deck, or context "obviously" implies an answer.** A terse
request like *"make slides for MICCAI"* specifies only one thing (the venue);
the content, source material, style, and template are all still unknown and must be
**collected, not assumed**. The biggest failure mode is silently carrying over
assumptions from a prior deck in the same session (its topic, its content, its
style, its template) — every deck starts fresh with these questions.

Collect all four answers in **one cheap interview turn**. Match the host UI:
- **If the runtime provides a structured choice UI** (for example Claude Code's
  `AskUserQuestion`), ask the four questions in one batched call with concise options.
- **If the runtime does not provide that UI** (for example plain Codex chat), ask one
  compact direct question and let the user answer in free text. Do not fabricate a fake
  multiple-choice form; give short examples only where they reduce ambiguity.

Direct-question fallback:
```text
Before I build, please give me:
1. Template/brand: existing template, new template, design a clean one, or generate one with an image tool?
2. Purpose/audience/time: who is this for, how long — and is it presented live, screen-shared, or sent to self-read? Main goal: inform, support a decision, or inspire action?
3. Source material: paper, deck, doc, figures, repo, or none?
4. Style/language: density (diagram-heavy ↔ balanced ↔ text-heavy?), tone (minimal/corporate/academic/playful), and language (中文/English/etc.)?
```

This batching is deliberate: the interview is non-negotiable, so it has to be *cheap*.
Only drop a question if the user already answered *that* one in their current request;
when in doubt, keep it. Never assume the **topic/content**, the **style**, or **which
template** — confirm each.

**Personalize options only from THIS user's own footprint — never a hardcoded or guessed
domain.** Any *suggestions* you pre-fill into a question — candidate topics, example
subjects, registered templates — must come from what this user has actually given you:
materials they provided (now or in a past session) or their saved registry / profile /
memory. In Codex, prefer the registry root `~/.codex/slide-templates/`; in Claude Code,
prefer `~/.claude/slide-templates/`. If only one exists, use it. A **brand-new user has no footprint**, so do NOT seed a specific domain (e.g.
don't offer "MRI reconstruction" or any field as a topic just because some *past* deck
used it) or a prior user's branding — ask the subject **openly** (a genuinely open-ended
topic is the one place free text beats options) and offer only the generic template/look
choices: "provide a template", "design a clean one", and, when a more vivid custom identity
would fit, "generate a template with an image tool". Personalizing from a *returning* user's
own materials is good and encouraged; assuming a domain for someone who gave you nothing is
the failure to avoid.

**Scale the interview to the ask:** a full deck needs
all four; a genuinely tiny ask (a single slide, a quick infographic) still needs purpose
and content confirmed, but you may collapse template/style to a sensible default *stated
in one line* ("I'll do a clean minimal look — say if you have a template") rather than a
full prompt. Scaling ≠ skipping — never infer purpose or content. Some answers trigger a quick follow-up *after* the
batch: *a conference talk* → ask which venue, then research it; *a new template* → they
hand over the file; *"design a clean one" (no template)* → offer the **direction gate**
(see Q1's design-one branch) — recommend showing **3** rendered style directions to pick
from before the full build; *"generate a template with an image tool"* → run the
mini-interview + generation + feedback loop in `references/generated-template.md`, then **skip
the direction gate** (the look is already decided). The four:

1. **Template / brand.** First **list this user's registered templates** — check the
   host-appropriate registry (`~/.codex/slide-templates/` in Codex, `~/.claude/slide-templates/`
   in Claude Code; if only one exists, use it). Each subfolder is one template they've used before,
   with a `profile.md`).
   **⚠️ The template question MUST present ALL FOUR standard choices every time — do not silently drop
   one (especially the image-tool option, which is easy to forget):**
   **(a)** each *registered template* · **(b)** *"a new template (I'll provide one)"* · **(c)** *"design
   a clean one"* · **(d)** *"generate a template with an image tool"* (a bespoke generated visual
   identity). If you're using a structured-choice UI and run out of option slots, keep (c) and (d) and
   fold the registered/provide-your-own into one "use/provide a template" option — never omit the
   generate-with-image-tool path. Then:
   - *A registered template* → build on it using its saved `profile.md` (step 2).
   - *A new template* → they give a `.pptx`/brand; build on it, AND after profiling it
     (step 2) **save a new subfolder to the active template registry** (its
     `profile.md`) so it becomes a remembered choice next time. The registry **grows
     through conversation.**
   - *Design a clean one* → build from preferences (brand colour/logo? formality?),
     and **shape the look to the chosen purpose** (step 2 / `references/design-by-purpose.md`)
     rather than always shipping the same default blue — a defense, an exec readout,
     and a lecture should not look alike.
     **Because the look is entirely yours to invent here, default to offering the
     direction gate** — this is the one branch where preference, not just quality, is
     unresolved, so let the user *choose* the look rather than guessing one for them.
     After the interview, ask in the host's natural style — structured choices when
     available, otherwise a direct text question — between **"see 3 style directions first
     (recommended)"** and **"just design one and go."**
     - *Picks the 3 directions* → run **Gate A** of `references/collaborative-mode.md`
       with **3 *differentiated* directions** (distinct light/dark, warm/cool, serif/sans —
       not three shades of one idea), each captured as a **design-token set** (palette +
       portable fonts + motif) and rendered by `scripts/archetypes_html.py` into **ONE
       self-contained HTML page** showing all three in the **same** representative slides
       (cover / points+callout / diagram / data). **Hand the user the single `file://…
       directions.html` link** to open in a browser, review side-by-side, and pick from — no
       local pptx samples. Collect the pick + knobs. Present the pick as **A / B / C plus a
       fourth "D — describe your own" option**: if the user picks D, they *type the look they
       have in mind* (a reference, a brand, a mood, a constraint) and you **synthesize a fourth
       direction from that description** — regenerate the HTML link and show it alongside
       (iterate until they consent), rather than forcing one of your three guesses. The three
       are only your opening proposals; the author's own intention always outranks them. On the
       pick, the chosen token-set becomes the deck's `style.py` — then **render ONE real slide
       in it to confirm fidelity** before building. **Once they pick, delete the throwaway
       `_directions/` preview files + rejected token-sets** (keep only the chosen style), then
       build the full deck in it — don't leave demo files littering Downloads.
     - *Picks design-one* → build a single look shaped to purpose, as above.
     This offer is **skippable, never forced** — a brand-new from-scratch deck is exactly
     when showing options pays off, but a user in a hurry can decline in one click.
   - *Generate a template with an image tool* → **a bespoke visual identity** — a styled, **text-free**
     hero/divider illustration, then reproduced natively so every content block fits it — for a vivid,
     designed deck (launch, event, brand, playful pitch) where a clean default isn't enough. **Follow
     `references/generated-template.md`**: a mini-interview *now* (scenario + brand colours; **seed from
     its Style library**, offering the 3–4 best-fit as options + "describe your own" + "a reference" +
     **"let the image tool pick the style"** — the auto path where you don't choose a named style and
     instead let the model/image tool decide the best-fit look from the scenario) →
     generate the text-free hero with a calm title zone (**no key** — native imagegen in Codex, else
     `generate_images_codex.py`; see `image-generation.md`) → **derive a matching `style.py`** (palette
     via `deckkit.palette_from_image`, motif + component helpers, so native blocks match) → render the
     cover + one real content slide and gate it:
     > **🔴 CHECKPOINT** — show the hero + a sample content slide; iterate until the user confirms.
     Then **the look is decided — SKIP the 3-direction gate**, finish the interview normally, and build
     (image cover/dividers with native title on top; content built natively in `style.py`); save the
     confirmed template to the registry.

   **Never hardcode or assume a specific institution's template.** This skill ships
   to anyone: a brand-new user has an *empty* registry, so they see only generic choices
   ("provide one", "design a clean one", and optionally "generate a template with an image
   tool") — no prior user's branding is ever offered to them.

2. **Purpose & audience.** "What's this deck for, and who's the audience?" Offer the
   common cases since the bar differs sharply between them:
   *research meeting with a supervisor* · *work status update to a manager/boss* ·
   *academic conference talk* · *academic job talk / faculty interview* ·
   *company/stakeholder readout* · *product description / pitch* · *thesis defense* ·
   *teaching* · *webinar / online presentation*. Get the **time budget**. This selects
   the critic's rubric (`references/review-rubrics.md`).
   - **Also capture two axes that the purpose alone doesn't pin down — ASK, don't infer them**
     (both change foundational design decisions *before* you build):
     - **Delivery context — presented live to a room · shared/screen-shared in a meeting · sent
       digitally / self-read.** This is the **single most design-determining answer**: it sets the
       deck's **delivery mode** (`design-principles.md` "Delivery mode"). A *presented* deck wants few
       words per slide + larger type + speaker notes; a *self-read* deck must be self-sufficient and can
       carry more text per surface. The same purpose can go either way (a status update presented vs
       emailed), so **don't infer it from the purpose or the density choice — ask it.** For self-read,
       there's no talking-time, so also get the **deck length** directly (short ~5–8 / medium ~9–15 /
       long 16+) instead of deriving it from minutes.
     - **Deck length is ALWAYS the user's choice — surface it, never silently derive it.** Make it an
       explicit interview option: a **self-read** deck → ask **short ~5–8 / medium ~9–15 / long 16+**; a
       **spoken** deck → the **time budget** sets the working count (~1 slide/min), but still **confirm the
       resulting slide count** with the user at the Step-3 plan checkpoint before building. Don't ship a
       length the user never saw (e.g. quietly building 14 slides because the content "felt like 14").
     - **Primary goal / intent — inform & educate · support a decision · inspire / motivate action.**
       This sets the **rhetorical arc**: *inform* builds to the evidence; *decide* leads with the
       recommendation and the ask; *inspire* opens on stakes and closes on a call to action. Purpose
       hints at it but doesn't fix it (a conference talk can inform *or* persuade) — so confirm it.
   - *(Structure emphasis — data/trends vs narrative-insights vs sector/section breakdown — and the
     fine-grained slide count are best steered at the **Step-3 plan checkpoint**, where the user
     approves the arc, rather than front-loaded here — keep this interview cheap.)*
   - **Webinar / online presentation** = a talk delivered over video, watched in a shrunk
     window on mixed-size screens. Build it like a conference talk but for a shared screen:
     larger type, light background, content in the central safe area, more/lighter slides
     to hold a remote audience, and "ask in the chat" prompts (see `design-by-purpose.md`).
   - **Academic job talk / faculty interview** = a candidate selling their research
     *program* + vision + fit to a hiring department (not one paper to peers). Unlike a
     conference talk it's longer (~45 min), personal, and must connect past work into one
     through-line and a concrete future agenda — so don't model it as a long conference talk.
   - **Product description / pitch** = presenting or selling a *product* to
     prospects, customers, or users (launch deck, sales pitch, product overview) —
     distinct from a *stakeholder readout* (which reports business status/decisions).
     Lead with the value proposition, sell benefits over features, show the real
     product, and end on a call to action. If it targets a named market/event or has
     a brand, treat that like a venue/template and research/honor it. **Confirm the
     audience: an *investor* pitch (raising capital) is a distinct variant** — it sells
     the company/opportunity (market, traction, business model, team, the ask), not just
     the product, so ask "investors, customers/users, or internal stakeholders?" and judge
     it against the investor overlay in `references/review-rubrics.md`.
   - **Conference talk → ALWAYS identify and research the specific venue.** First
     ask *which* conference and (if relevant) which track/format — oral, spotlight,
     poster (e.g. MICCAI, ISMRM, NeurIPS, RSNA, CVPR). **This is required, not
     optional: never build a "generic conference" deck.** Then **web-search the
     named venue** even if you think you know it (guidelines change yearly) to learn:
     talk length & slot, slide aspect ratio, file/format rules, whether an
     **official template** exists (fetch & use it if so), the **audience**
     composition (specialists vs. broad), and what a *strong talk at this venue*
     looks like (single-message expectations, how technical, clinical vs. ML
     framing, Q&A norms, any companion poster). Venue norms vary widely — a clinical
     society ≠ an ML conference — so ground every choice in what you find, cite it
     back to the user, and fold it into the plan, the build, and the critic's rubric.
     - *Poster, not a talk?* A conference **poster** is a different artifact — one large
       single-canvas layout, not a sequence of slides — so the deck arc and the per-slide
       rubric don't apply directly. `deckkit` can build a single large-canvas "slide"
       (`blank_deck(w_in, h_in)` at the poster's real size, e.g. 33×47 in / A0), and the
       craft rules still hold (whole figures, hierarchy, contrast, one clear story), but
       say plainly that this skill is tuned for *talks* — confirm size/orientation and
       the venue's poster spec before building.

3. **Source material.** "Do you have content for me to work from — code, a paper, a
   doc, existing slides, figures/images?"
   - *Yes* → **dig in deeply** (step 1, content branch): read it properly and build
     from the real material. (But per "requirements first" above — if they didn't
     ask you to reuse a provided deck's *content/wording* as-is, mine it for facts
     and figures, don't inherit its structure or text.)
   - *No* → **build the content yourself** from your knowledge, and **web-search to
     ground it** (correct facts, current numbers, credible framing) rather than
     inventing. Confirm the intended scope/outline with the user before building.
   - **Their own deck, to *improve*** (e.g. "redesign this", "my slides are too
     dense", "make my deck better") → this is a redesign, not a build-from-scratch, and
     it rewards a different front end. **Follow `references/redesign-existing-deck.md`**:
     ask two extra answers in the same interview turn — *keep your
     design/branding, or redesign the look?* and *how deep — light cleanup keeping your
     structure, or full re-author?* — and **diagnose their deck first** (render it,
     extract its content/figures with `scripts/extract_deck.py`, run the critic on it),
     then show the weakness list and confirm scope **before** rebuilding. Optimizing
     someone's existing deck rewards a diagnosis-led, scope-confirmed approach over a
     silent ground-up replacement.
     > **🔴 CHECKPOINT** — show the diagnosis + proposed scope and get the user's OK before rebuilding their deck.

4. **Style.** "How do you want it to look and feel?" Offer these (applies to *every*
   purpose):
   - *Minimal / diagram-heavy* (**recommended default**) — a few words per point, a
     diagram/figure carrying each idea; what lets an audience follow a *speaker*.
   - *Moderate text* · *dense / detailed* — for any **read-without-a-speaker** artifact: a
     leave-behind, an emailed/reference/appendix deck, a board pre-read, a **poster**, or a
     single-slide **infographic**. There fuller, self-contained text is the deliverable, not a flaw
     (this sets the deck's **delivery mode** — see `references/design-principles.md` "Delivery mode").
   - **Density (text-heavy ↔ diagram-heavy) is ALWAYS a SURFACED choice — ask it, never silently derive
     it.** This is the question you remember as "text-heavy or diagram-heavy"; it lives here in Style and
     composes with the **delivery context** (Q2): for a **presented** deck offer **diagram-heavy
     (recommended) ↔ balanced** (a *text-heavy presented* deck is a wall of text — steer away from it);
     for a **self-read / poster / leave-behind** deck offer **balanced ↔ dense/detailed** (fuller
     self-contained text is the deliverable). Put it in the interview as an explicit option (like the
     deck length) — don't quietly decide "diagram-driven" or "dense" from the purpose/delivery alone.
   - **"Mimic an example I'll provide"** — the user hands over a deck (or slides /
     PDF / screenshots) whose **visual style they want imitated**. Different from a
     *template* (Q1): you do NOT build on it or inherit its logos — you reproduce its
     *look and feel* in your own build. **Understand the style fully before building**
     — a glance won't do; the style lives in the *system* (what repeats across slides)
     and the *details* (its decorations). View **every** slide and write a structured
     **style brief** covering the overall structure/rhythm, grid & layout, exact
     colour system, typography, **decorations & motifs** (bands, rules, shapes,
     corners, icons, signature touches), and how each recurring element (titles,
     callouts, figures, tables, equations, diagrams) is styled. Follow the full
     checklist in **`references/style-analysis.md`**, then build to the brief —
     overriding deckkit's defaults to match — while keeping the user's content,
     purpose, and the craft rules. A style example composes with everything (e.g.
     build on the user's template for branding yet mimic an example's density/motifs).
   - Plus any tone (academic, corporate, playful).
   Honor their choice over your own habits; nudge toward concise + visual when
   unsure; carry the choice into the plan (step 3) and the build (step 4).
   - **Direction gate (when to show rendered options first).** Two cases call for it:
     (a) **"design a clean one" / no template** → it's the *recommended default* there —
     offer 3 directions as described in Q1's design-one branch above; (b) any other case
     where the user is **unsure on style** or it's a **brand-defining / high-stakes** deck →
     offer **2–3 directions** as a lighter opt-in. Either way it's the same machinery
     (collaborative mode Gate A, `references/collaborative-mode.md` + `scripts/archetypes_html.py`):
     **one HTML link** showing the archetype slides per direction, which the user opens and picks
     from before the full build. **Skippable,
     never forced.** A *provided* template **or a generated template** (Q1's image-tool branch)
     means the look is already decided — **don't offer the gate** in those cases.

**Language (decide it, then hold it).** A deck is written in **one language
throughout** — default to the language the *user* writes in. **When the source
material is in a different language than the user** (e.g. an English-speaking user with
a Chinese codebase/paper), or it's otherwise ambiguous, **ask which language the slides
should be in** — don't assume the source's. **When you ask the language, also offer
bilingual as an option** (e.g. "English only, 中文 only, or bilingual EN+中文?") so a user
who'd benefit doesn't have to volunteer it. Then translate the content into that language
and keep every slide consistent. Established technical terms, proper nouns, acronyms,
units, and code may stay in their original form (that's not "mixing"). Build a
**mixed/bilingual** deck only if the user asks (or picks it) — and then do it
systematically (same pairing on every slide). See `references/multilingual.md`.

## Step 1 — Understand the material & plan the deck (use the content-planner)
**Use `agents/content-planner.md` for this step and Step 3 as one deep pass** — dispatch
it through an available multi-agent/subagent tool when the host exposes one (in Codex,
discover multi-agent tools with `tool_search` if needed), otherwise run the same planner
brief inline yourself. It is the
constructive counterpart to the critic/arbiter judges. Give it the interview answers
(purpose/audience/time, **delivery context** & **primary goal**, style/language, template
decision, venue if any), the source material (or "none"), and the craft references
(`design-principles.md`, `design-by-purpose.md`, `animation.md`, `image-generation.md`,
`review-rubrics.md`, `multilingual.md`). It returns a **deck plan**: a comprehension brief
+ the narrative arc + a build-ready per-slide spec (takeaway · content · visual source ·
layout · motion · proposed image), plus an image opt-in list, flagged forward-looking
content, and open questions. You then take that plan into the **Step 3 checkpoint** (show
it, get the user's OK), set up the canvas (Step 2), and build it (Step 4). The planner is
*one mind* — it may fan out *reading* across multiple documents, but it synthesises the
understanding, arc, and design itself; never split one paper across blind agents. For a
quick, low-stakes deck you may do this pass inline yourself rather than dispatching — but
the deep-understanding and planning standard below is the same either way.

The rest of this step and Step 3 are the **specification the planner works to** (and what
you check its plan against). The bar — understand it deeply, don't skim:

A deck is only as good as your grasp of the material — a superficial read produces a
deck that *looks* right but misrepresents the work, which an expert audience spots
instantly. Read **all of it**, not the abstract: run the code's README, read the
paper end-to-end (intro → method → **every results table/figure** → conclusion).

Then **write a comprehension brief — a REQUIRED, fixed-field, source-traced artifact** (the
planner's `agents/content-planner.md` §1 is the spec); every field must trace to a locatable
source span, not memory:
- The **one-sentence message** + the verbatim source sentence it derives from (+ where).
- The **contributions**, in their words, each with its source location.
- The **method essence** at talk-altitude (+ the one key equation), and where it appears.
- **One row per figure AND table:** `id | what it is FOR (the ONE comparison) | which exact
  element carries it (row/column/curve/panel) | what it emphasises | the WRONG reading to avoid`.
  A table exists to make one comparison obvious — foreground *that* (e.g. baseline vs +X), and
  name the carrying element (it drives which row the build highlights + the assertion title).
  A figure whose carrying element you cannot name is one you haven't understood.
- Any **nuance/limitation** the authors stress, quoted.
- A **claim ledger** (per `content-planner.md` §2): every number/date/name/citation/superlative/
  dated-event as a row with source + verbatim value + verified?(Y/N) + as-of date; an unverifiable
  claim is cut or marked open, never shipped.

**This is a hard gate, not a sanity check.** Self-verify the brief against the source; if any
field is empty, hedged, or untraced — or the emphasis test fails (your one-sentence message
would surprise the authors) — you have NOT understood it: re-read or log an open question.
**An incomplete or untraced brief blocks the build.** Every slide must be faithful to the
authors' actual emphasis, not a plausible-sounding paraphrase. Reuse their figures
(relabel for the slide).

**Having a source is rarely the whole story — use the web for the gaps, even with one.**
Most decks are *partial*: a paper that needs related-work-since-publication or current
framing, a code repo with no writeup, figures with no prose, a doc that omits the venue. So
the web step below is **not only for the "No content" case** — run it whenever a source
leaves a gap, and in particular **re-verify the source's own falsifiable / time-bound claims
at *today's* date**: a paper's "state-of-the-art", an adoption number, a "first/largest/
latest" superlative may be stale by presentation day. Re-verifying a source claim is not
inventing — it's fidelity to what's *true now*.

- **No content:** draft an outline from your own expertise, then **ground *and verify*
  it** with the host's available web search/fetch tools (Codex: use `web.run`) — treat this as a **fact-check, not just framing**.
  List the deck's specific *falsifiable* claims (numbers, dates, names, citations, and
  every "first/largest/state-of-the-art" assertion) and confirm each against a credible
  source before it lands on a slide; fix or cut anything you can't verify, and never
  present an unverifiable claim as established fact. This matters because a no-source deck
  has **no paper to anchor it** — *you* are the only check on whether a confident-sounding
  statement is actually true, and an expert audience spots a wrong "fact" instantly (the
  failure mode here is being *wrong*, not just vague).
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
  Carry the verified outline + source log into the **Step 3 deck plan**, where the user
  approves it — a no-source deck still produces one full plan, gated once at the Step 3
  checkpoint, not twice here.

## Step 2 — Set up the canvas
**First, decide where the deck lands.** Deliver each deck as one self-contained
folder in the user's Downloads — `~/Downloads/<deck-name>/`, holding the
`<deck-name>.pptx` and a `render/` subfolder of slide PNGs — so the user gets a
tidy, findable bundle rather than a stray file in `/tmp`. Point your build script's
output path and `render_deck.sh`'s out-dir there from the start (no need to copy
files around at the end). **Before the first save, confirm `~/Downloads` exists; if
it doesn't, ask the user where they'd like outputs** and use that location instead —
don't silently dump into `/tmp`. You'll remind them to open it in step 6.
> **🔴 CHECKPOINT** — if `~/Downloads` is missing, ask where to save before writing any file.

**Keep the per-deck build script (`build_<deck>.py`) in that same folder, beside the
`.pptx`.** The build script — not the rendered file — is the *source of truth* for the
deck, so it should travel with the artifact: this makes every later iteration
reproducible (re-run it, get the same deck) and is what lets you fold the user's
later change requests back into the build rather than hand-patching the binary. See
`references/handoff-and-iteration.md` for why this matters at hand-off and how to
iterate without clobbering the user's manual edits. In that script, resolve deck assets
relative to the script file (for example `ROOT = Path(__file__).resolve().parent`) rather
than the current working directory, so `python /path/to/build_<deck>.py` works from anywhere.

- **Template branch:** run `scripts/inspect_template.py <file.pptx>` to learn the
  layout indices, placeholder ids, and where logos/brand live (they sit on the
  layouts, so new slides inherit them). Then `deckkit.open_template()` loads the
  deck and wipes old slides while keeping masters/layouts. Pull the brand colors
  from the template and set `deckkit` palette/`FONT` to match. Save what you learn as
  a `profile.md` under the active template registry so it's reusable next time
  (a registered template's `profile.md` is a fully worked example of this).
  - **Conference template:** if step 0 turned up an official conference template,
    download it with the host's web fetch/download tool or `curl` and treat it exactly like a user template —
    inspect it, then build on it so the talk matches the venue's required look and
    aspect ratio.

- **No-template branch:** `deckkit.blank_deck()` + `deckkit.add_slide()`, and give
  it consistent chrome with `deckkit.title_bar()` / `deckkit.footer()`. **Don't just
  accept deckkit's default blue — design the look to fit the purpose.** Read
  `references/design-by-purpose.md` for a per-purpose design language (palette mood,
  density, layout, chrome) and set the `deckkit` palette constants + a **role-based font
  pairing** (`DISPLAY` title face + `FONT` body + `MONO`; add `EADISPLAY`+`EAFONT` for CJK) to
  match — or adopt a one-switch **`scripts/presets.py`** `preset(name)` (glassmorphism / swiss /
  editorial_paper / editorial_report / risograph / memphis: palette + fonts + surface + image-prompt)
  and tune it — then do a quick web-search for current, well-regarded examples of *this kind* of
  deck and adapt concrete ideas. A status update should read as crisp and corporate,
  a defense as sober and formal, a lecture as warm and clear — the design should
  signal the right kind of document before a word is read.
  - **Vary the look deliberately — don't default to one house style.** When *you* define
    the style, treat each deck as a fresh visual identity: choose a palette, type pairing,
    layout grid, and a signature motif that fit *this* purpose/audience/mood — and do NOT
    reuse the last deck's scheme out of habit (not the deckkit default blue, not whatever
    you built last time). Range widely across decks — warm vs cool, **light vs dark**,
    serif vs sans, minimal vs bold, restrained vs vivid; `design-by-purpose.md` gives a
    starting mood per purpose, but pick a *distinct, concrete* look within it. Unsure or
    brand-defining? Show 2–3 direction archetypes in **one HTML preview link** and let the user
    pick (collaborative mode, `scripts/archetypes_html.py`). Sameness across decks is the failure to
    avoid; the only constant is the craft (contrast, hierarchy, one idea per slide).

**Fonts for non-Latin languages (Chinese / Japanese / Korean)** — applies to both
branches. The defaults are Latin-only, so set a script-appropriate font before
building: `deckkit.EAFONT = "PingFang SC"` (or Heiti SC / Microsoft YaHei / Noto Sans
CJK SC), keeping `FONT` for Latin/numbers. This tags every run with a CJK `<a:ea>` font
so it renders correctly *and portably* (not an uncontrolled fallback), and mixed
中文+English stays right. Pick the CJK font to the purpose, emphasize with weight/colour
not italic (CJK has no true italic), and flag the font dependency at hand-off. Full
guidance + RTL limits in `references/multilingual.md`.

**Font portability (any deck).** A `.pptx` stores font *names*, not the fonts — pick fonts
present on every machine that will open it (a missing font substitutes, shifting metrics
or, for non-Latin, producing tofu). Default to cross-platform-safe fonts (Arial/Calibri,
Georgia, Consolas), set `deckkit.FONT/MONO/EQFONT` accordingly, and flag any brand-font
dependency at hand-off. Equations via `equation_png` are font-independent (rasterised).
Full list, fallbacks, and tofu recovery in `references/font-guidance.md`.

## Step 3 — Pace-check the plan, then get approval
The content-planner's plan (Step 1) already carries the arc and the per-slide spec; this
step locks it. The standard it must meet: **one idea per slide** *(for a presented deck — a
read-alone / reference / poster deck legitimately packs more per surface; see `design-principles.md`
"Delivery mode")*, in an arc that fits the purpose (a conference talk and a status update are ordered
differently — let the rubric guide you). **For a spoken deck, scale the slide count to the time
budget** — ~1 slide per talking-minute as a loose anchor: short talk/status ~6–9 slides,
lecture/thesis defense/job talk ~10–20+; a longer spoken deck means *more* slides, never a denser
one. *(A **read-alone / fixed-surface** deck has no talking-minute budget — its scope is set by
content completeness, and deliberate density is fine, not a defect to split away.)* At **~15+
slides**, consider the section fan-out (step 4). Each slide's **takeaway** comes first; bullets support it.

Each slide's **visual source** is set in the plan — source figure, chart, native diagram,
generated plate, or **none**. Both **generated images and motion are a matter of taste and
purpose, never a quota** (full rules: `references/image-generation.md`, `references/animation.md`):
generated plates are opt-in, styled to the deck's purpose + topic, and never carry evidence. For
**motion**, actively check each (presented) slide's *layout* for a build-friendly shape — a flow of
blocks joined by arrows, a multi-part/numbered build, before→after, evidence→takeaway, a
quadrant/timeline/step-cards — and plan a step-reveal there; none across the deck is fine, but don't
*miss* a pipeline that clearly wants one (build it with `scripts/anim.py`).

**Sanity-check pace against the clock.** After planning, compute `slide_count ÷
time_minutes`: well over ~1/min for a *spoken* talk means you'll overrun — cut slides or
get more time, and flag it to the user. Count an **animated/build slide once** (a 4-click
pipeline is one slide for pacing, not four). Read-alone decks (no speaker) aren't bound by
this.

**Show the plan and get approval before building — always.** The deck plan (from the
content-planner in Step 1) is the cheapest place to course-correct, so present it to the
user every time: the **comprehension brief + claim ledger** (shown FIRST, so the user can spot
a misread before any build), then the narrative arc + the per-slide spec (takeaway, content,
visual source, layout, motion) + the **image opt-in list** (which slides you'd propose a
generated plate for, in what style — the user chooses whether any are generated) + any flagged
forward-looking content + open questions. Fold in their edits, then build.
**The per-slide content-image opt-in is a CROSS-CUTTING choice, available on EVERY deck** — it is
*not* tied to a template choice and is *separate from* Q1's "generate a template with an image tool"
path (which makes the visual identity). Whenever an image tool is available, offer it regardless of how
the deck was templated — a **registered** template, a **provided** template, a **clean** design, or a
**generated** template can all carry generated *content* images. Two guardrails the planner enforces and
the checkpoint shows: **(a) each proposed plate is *content-related* — it depicts THAT slide's actual
subject, never generic "fancy" filler** (`image-generation.md`); and **(b) the planner is SMART about
where — it proposes plates only for the few slides that genuinely earn one, NEVER every slide, even when
the user has opted into image generation.** The user then approves which (if any) are generated.
**Precondition — the comprehension AND design gates:** before showing the plan, confirm it carries a
*complete* comprehension brief (every field filled + traced) and claim ledger (no shipped
`verified?=N` rows) — AND that the **design side passes too**: a concrete **Design language** (a *named*
signature motif + a deliberately-chosen palette/type, not a defaulted light/minimal/blue), and a **Form
ledger** whose diversity gate passes (no one format-family on >~40–50% of content slides — the
card-overuse guard). A plan that is empty/hedged/untraced **or** that defaults its look / over-relies on
one format is **not ready** — send it back to the planner rather than building on a shallow or monotone plan.
> **🔴 CHECKPOINT** — show the deck plan (brief + claim ledger + **Design language + Form ledger**) and get the user's OK (including the image opt-in) before building.

## Step 4 — Build with deckkit
Write a small per-deck build script that imports `scripts/deckkit.py` (don't re-derive primitives;
full signatures + behaviour are in its docstrings). The helper set, by job:
- **Chrome:** `title_bar`/`content_slide`, `footer`, `editorial_header` (caps eyebrow + title +
  hairline), `part_eyebrow`/`page_marker` (mono eyebrow + page marker).
- **Safe layout — measure or anchor, never hand-pick a y:** `columns`/`rows` (equal split panels with
  symmetric margins), `content_band` (the SAFE rect below title / above footer), **`bottom_callout`**
  (footer-safe bottom takeaway — anchors to the band, grows UP, can't collide), **`vstack(…, bottom=)`**
  (measured stack: equal gaps + no overlap by construction, errors at build time on overflow) with the
  `measure_callout/measure_bullets/measure_text` helpers, **`spaced_centers`** (evenly-spaced marker
  centers for a timeline / tick row / numbered steps, **inset at the ends so a centered caption stays
  co-centered with its end marker** — use it instead of hand-rolling a row of dots+captions, which
  desyncs the first/last caption from its dot near a slide edge; `timeline` already uses it),
  `picture` (`fit="contain"` keeps edges /
  `"cover"` crops), `gif` (animated GIF, undistorted + size/still warnings) + `gif_poster` (extract the
  first/representative frame to verify what the render & PDF export show), `icon`/`icon_card` (place an
  open-licensed SVG icon — recolored + rasterized via `scripts/icons.py`; `icon_card` is the
  upper-left-corner feature-card pattern). *(These exist so you never
  hardcode a low `y` — the recurring overlap/footer bug.)*
- **Text & blocks:** `bullet`, `callout` (auto-grows), `chip`, `modbox`, `arrow`, `table` (highlight
  the key row), `code_block`, `hrule`.
- **Colour:** `palette(n, ACCENTS)` (n distinct, contrast-checked fills — warns on adjacent same-hue;
  never a gray filler), `palette_from_image` (match a generated template's palette), `accent_one`
  (one-accent discipline), `contrast_ratio` (verify ≥~4.5:1 before committing).
- **Data furniture & charts:** `scorecard`/`leaderboard`/`takeaway_rail`, `change_stat` (baseline-
  centred before→after), `stat_row`, `big_numeral`; **editable native charts** `native_chart` /
  `native_dual_axis` / `native_donut` / `native_pareto` / `native_bubble`, plus the raster recipes in
  `scripts/designed_charts.py` — pick per `references/data-viz.md`.
- **Diagrams / patterns:** `quadrant`, `hub_spoke`, `timeline`, `before_after`/`image_tab`/
  `photo_triptych`, `wireframe_grid`+`spec_list`, `corner_frame`, `photo_card`, `backdrop_motif`,
  `repeat_row` (N identical-except-index units as representatives + `…` + `×N`, shared detail said
  once — never N duplicate blocks).
- **Surface (dark / glass / print):** `glass_card`/`glow`/`scrim_overlay` (gradient+alpha fill),
  `offset_shadow` (hard letterpress/riso shadow).
- **Publication & math:** `cover`/`colophon` (bookend the deck), `sources_page`, `specimen_card`;
  `equation_png` (LaTeX-style math) / `eq_par` (inline).
- **East-Asian (CJK) accents:** `seal` (vermilion chop/印章 stamp — the one red accent on an ink deck),
  `cjk_numeral` (壹·贰·叁 section markers vs Latin "01"). See `references/east-asian-aesthetic.md`.
- **Diagram kit (general flowcharts):** `node` + `connector` / `flow_chain` (straight links between adjacent nodes) + `elbow_connector` /
  `loop_path` (elbow / U-shaped paths for a feedback/repeat loop, a return, or a link between NON-adjacent
  nodes) — any architecture from rounded-rect/pill/circle nodes with **stroke semantics** (solid=required
  · dashed=optional · dotted=feedback) and **shape semantics** (straight=adjacent flow · elbow/U=loop /
  return / non-adjacent), exactly one `hub`; `diagram_island` (bright figure panel on a dark slide);
  `concentric_rings` (nested framework); `step_list` (numbered process, vertical/horizontal).
- **Editorial / consulting furniture:** `insight_banner` (so-what bar), `bilingual_lockup` (CJK+tracked
  Latin headline), `highlight` (inline `<k>keyword</k>` recolour), `ghost_numeral` (faint watermark
  ordinal), `concept_equation` (ZINE=MAGAZINE word-equation), `pull_quote`/`standfirst`, `cta_button`/
  `cta_pair`, `status_stamp`/`corner_tab`, `spec_card`, `year_badge`, `gradient_rule` (2-stop brand rule),
  `catalogue_frame` (double-line specimen frame — museum/eastern presets).
- **Micro-viz:** `dot_meter` (●●○), `tradeoff_list` (+/−), `segmented_bar` (cumulative 100%), `meter_bar`
  (a single percentile/share/progress row — track + accent fill + a value label **vertically centered on
  the bar**; use this instead of hand-building "track box + fill box + number", which is how value labels
  end up floating off the bar's centerline).
- **Photo on-brand (`scripts/image_fx.py`):** `duotone` / `grayscale` so a colour photo doesn't fight
  the accent (riso/brutalist/ink/luxury/museum), then `picture(fit="cover")`.

If the user gave a **style example** (Q4),
build to your **style brief** of it — match its palette/accents, density, title
treatment, and figure/table/equation motifs (override the deckkit defaults to suit).
A few rules that matter (see `references/design-principles.md`):
- **Use the source's own figures, WHOLE — integral is the default.** For *any* deck
  (research, work, exec, teaching): if the source — paper, report, doc, existing slide, or a
  chart already produced from the code/data — has a figure (architecture, results, a plot),
  use *that*; don't redraw it (slow, risks wrong detail) and don't chop it into pieces. Many users
  *prefer* the whole figure even when it's dense (it's the artifact they know and trust), so
  when a figure feels too busy, your *first* move is to give it a whole slide — large, with an
  **assertion title + a one-line caption** pointing attention to the part that matters (e.g.
  "the orange line is this quarter", or "rightmost column is ours") — not to crop it down. Reach for cropping only to (a) **trim**
  surrounding page header / caption / whitespace, or (b) lift **one cleanly-separable
  sub-figure** that genuinely stands alone. Chopping a multi-panel figure into a few columns
  *loses context and changes what the authors showed* — do it only when the whole is truly
  unusable on a slide, and prefer to **confirm with the user** before discarding panels.
  Build native diagrams only for structure with no source figure.
  - **Never clip the figure's OWN parts.** Whether you place a figure whole or crop it, the
    legend, colour bar, axis labels/ticks, title, units, and the outermost rows/columns are
    *part of the figure* — losing them is worse than showing the figure a touch smaller. After
    every crop **and** after placing/scaling a figure on a slide, **re-view the result** and
    confirm nothing of the figure is cut off (a half-cut legend at the top edge is the classic
    miss). If a crop box starts at the very edge of a legend/axis, give it a margin.
  - **Figure trapped in a PDF (paper/report)? Crop it FROM the paper — don't ask the user
    for an original** (you may *offer* to use one if they have it, but you can get a clean,
    precise crop yourself). The primary tool is `scripts/extract_pdf.py`'s auto-detection,
    which anchors on captions and snaps to the figure's real extent:
    `python extract_pdf.py figures paper.pdf` lists every detected figure (with `cov=`/`bodyov=`
    checks and a `⚠ CHECK` flag on suspect ones); `extract_pdf.py figure paper.pdf <idx> out.png`
    renders one (auto-trimmed); `autofig paper.pdf figs/` dumps them all. **Always view a
    rendered crop before using it**, and for a `⚠`-flagged one (dense multi-figure pages can
    mis-localise) fall back to the manual loop: `page` rasterises a whole page to high-DPI PNG
    (composites vector+text+raster exactly as printed), then `crop_helper.py grid`→`crop` to
    cut precisely. (`crop` by point/fraction box and `images` for embedded bitmaps still exist.)
    Then place the PNG *whole*, like any other source figure.
  - **When you DO crop, do it by looking, never by guessing.** The failure mode is cropping
    **blind** — inventing fraction coordinates, clipping a column or a legend, and not
    noticing. `scripts/crop_helper.py` removes the guessing with a **see-it loop**: `grid
    img _g.png` overlays a labelled ruler → *view it* and read the box off the labels →
    `crop img out.png x0 y0 x1 y1 --frac` → **view the crop and confirm** nothing's clipped
    (adjust and redo if so). One or two looked-at iterations beat a single blind guess.
  - **Dense comparison / panel grid (N methods × M examples)?** First consider showing it
    **whole** on its own slide (the integral default above) — that is often what the user
    wants. Only if you and the user agree the full grid is unusable, keep the columns/rows
    that make the point and **reassemble** them, preserving the header row and row-label
    column: `crop_helper.py panel fig.png _idx.png --grid RxC --xpad <left-label>
    --ypad <top-header>` overlays numbered cells (*view it*, tune `--xpad/--ypad` until the
    lines sit on the cell gaps), then add `--keep-cols 0,1,3,9 --keep-rows 0,2,3` to emit a
    compact figure. View the result to confirm the kept headers still line up — this is also
    a fidelity check (you can read each cell's numbers and confirm they're faithful). When the
    user provides the *original* source images/PDFs, prefer working from those.
- **Animated results (GIF / looping animations) → insert the GIF itself with `deckkit.gif()`**,
  never reduce it to a single frame. It embeds the real animated GIF (every frame preserved;
  PowerPoint and Keynote **loop it in slideshow**), places it **whole and undistorted** (`contain` —
  a square cine clip is never stretched), sets alt-text, and **warns on a heavy file** (a big cine GIF
  bloats the `.pptx` and stutters live) or a single-frame still. For time-resolved / 4D / cine /
  training-run results — in **any deck** (a product/UI demo in a pitch, an interaction in teaching, a
  data-viz loop, a simulation or time-resolved result in a research/status deck) — a frozen frame
  throws away the point. Integrate it like a figure: often the slide's **hero** (assertion
  title + a one-line *"what to watch"* caption), or beside its quant panel in a `columns(2)` split;
  two GIFs for before/after. **The first frame matters:** the render, the static critic, a **PDF/print
  export**, and edit view all show frame 0 (a GIF has no separate poster) — so verify it's
  representative with `deckkit.gif_poster(path, "first.png", frame="first")` and, if it's a blank /
  black / loading frame, get a GIF that *starts* on a meaningful frame; `frame="auto"` extracts a
  representative still to hand the critic. Don't misrepresent the dynamics (no meaning-changing frame
  drops/speed-ups). Tell the user at hand-off that it animates in **slideshow** (still in edit/print).
- **Data but no figure yet → make the chart, don't dump numbers.** If the source gives
  raw data (a CSV, a metrics table, logged numbers) but no plot, turn it into the chart
  that makes the comparison obvious rather than typing a wall of figures — generate it
  with matplotlib or another available figure-making workflow — then place the result
  *whole*, with a legend + takeaway, like any other figure. A bare number table is the
  weakest way to show a trend. **Pick the chart TYPE that fits the argument, not always a
  bar** — `references/data-viz.md` has a roster + ready recipes. **For a deck in ANY non-Latin language
  (CJK · Cyrillic · Greek · …), or when the user will edit the chart, use an EDITABLE native chart** —
  `deckkit.native_chart` (line/column/bar) / `deckkit.native_dual_axis` (two-scale A↑ vs B↓): a real
  PowerPoint chart that renders non-Latin labels via PowerPoint's fonts (**no tofu**) and is
  click-editable (pass `font=` the script's font). For the richer raster types
  (`scripts/designed_charts.py`: donut+KPI, dumbbell, slope, bubble+trend, Pareto) pass your palette /
  `dark=True` (and `font=<the script's font>` on a non-Latin deck). Either way: a **single highlight** on the one series
  that matters + a `deckkit.takeaway_rail` "so-what". For 3-6 headline metrics use
  `deckkit.scorecard` tiles; key a ranked list to a chart with `deckkit.leaderboard`.
- **Concept needs a domain image → show the real thing, not an abstract icon.** When an
  idea has a concrete visual — a real data sample, a signal/waveform, a chart of the
  actual numbers, a map, a microscopy/medical-image patch, a sample UI, or a *transformed*
  version of any of these — **generate it with tools** (numpy / scipy / matplotlib /
  scikit-image, or the domain's own libraries) or fetch a **license-clear** example,
  rather than drawing a box-and-dot cartoon. Compute the **real** artifact so it's
  faithful: actually run the operation the slide describes on a real input — e.g. FFT an
  image to show its true frequency content, filter or downsample a signal to show the real
  artifact, plot the real distribution from the data — so what you show is what genuinely
  occurs, not a plausible-looking stand-in. Keep generated assets in the deck folder and
  reproducible from the build.
  - **Make the plot actually look CORRECT (then view it).** A computed plot is only faithful if it
    *renders* right: **(a) sample continuous curves finely** — a smooth function must look smooth, so
    use a dense `np.linspace` (a few hundred points / ≥~10× the highest frequency), never the integer
    index steps; plotting a high-frequency sine at integer `x` *aliases* it into jagged zigzags (the
    classic "sin curve looks weird" bug). **(b) Place the legend so it never covers the data** — when
    the plot area is full (oscillations spanning the range), put the legend **outside the axes**
    (`bbox_to_anchor` right/below, `loc='center left'`) or in the genuinely empty corner; `loc='best'`
    is not enough on a busy plot. **(c) Always view the rendered PNG** and fix anything that looks off
    (aliasing, clipped labels, an occluding legend, a squished aspect) — a wrong-looking plot misleads
    even when the math is right.
- **Generated visual plates (atmosphere / conceptual) — by taste & purpose, opt-in; full mechanics in
  `references/image-generation.md`.** Generate where it genuinely helps (no quota), styled to the deck;
  **never bake words/numbers/labels/charts/logos into a plate** (those stay editable objects / real
  assets). **Each plate must be *highly topical* — depict THIS slide's actual subject, not a generic
  "fancy" image that could sit on any slide** (name what it shows, else cut). **Place plates
  consistently — never a one-off generated *header* on a single body slide** (title chrome is
  `title_bar`'s; a content plate goes full-bleed / side-panel / inline, one role + art-direction across
  the plated slides). Generate with **no key** (auto-detect: native imagegen → `generate_images_codex.py`
  → OpenAI fallback; build the manifest with `image_prompts.py`), keep assets in
  `~/Downloads/<deck>/assets/generated/`, place with `deckkit.picture(fit="contain"|"cover")`, and
  render-check (calm space behind text, no pseudo-text/fake charts, subject whole, real things right).
- **SVG icons — ONE coherent open-licensed family, recolored, used with restraint (full rules — the
  jobs icons do, the rule-of-thumb, + five quality marks — in `references/icons.md`).** An icon must
  **reduce cognitive load, not decorate**: use one only where it does a real job (label a section /
  category, mark a repeated entity, guide reading order, anchor a sparse slide, flag status) and it
  passes the **rule-of-thumb** — answers *what is this / what does it do / why pay attention* before the
  words; else cut it. **Don't hand-draw a set** (inconsistent = amateur) and don't sprinkle them as decoration. **Fetch from
  one family** (Tabler/Lucide/Phosphor MIT-ISC; `simple:` CC0 for brand/tech logos) via
  `scripts/icons.py` `icon_png(spec, out, color=ACCENT)` — it fetches, **recolors to the deck palette**,
  and rasterizes to a transparent PNG (python-pptx can't embed SVG reliably; rasterizing renders the
  same everywhere). Place with `deckkit.icon()` or the **`icon_card()`** upper-left-corner pattern. The
  five quality marks (`icons.md`): **semantic fit** (the metaphor matches what it labels), **colour-coded
  per category** (in a multi-category layout each category its own hue from `palette(n)`, carried by the
  icon + label + tint — not one global accent), **contrast** (bright on dark / saturated on light, a
  `disc=` tile if needed), **consistent** family/size/position across siblings (size **≤ the title**,
  ≈0.32–0.5 in), and **style matching the deck** (outline vs filled). **Always pair an icon with a text
  label.** Cache in `~/Downloads/<deck>/assets/icons/`. **Icons fit any topic** — the libraries are
  diverse enough to match any register, so **match the style/weight and use fewer**, rather than ship a
  mismatched zoo or one-per-bullet clutter (the flaw is wrong-style/decoration, not icons by subject).
- **Speaker notes — for a PRESENTED deck, put the spoken script in the notes, not on the slide.**
  For any deck the user will *present* (especially a conference talk, defense, or lecture), move the
  full sentences off the slide into speaker notes with `deckkit.speaker_notes(slide, "…")`.
  The slide shows the phrase; the notes hold what the presenter says. Notes don't render
  (the critic won't see them) but they show in Presenter View and on printed Notes Pages —
  so the user can rehearse without the slide becoming a wall of text. Offer this at
  hand-off; it directly serves the "few words per point" rule. **For a read-alone deck there is no
  presenter** — the explanatory prose belongs **on the slide** (a reader won't open the notes), so
  keep the sentences visible there rather than hiding them in notes.
- **Layout & diagrams — full rules in `references/design-principles.md`; the essentials:**
  keep a `deckkit.GUTTER` (~0.4 in) between elements and clear of the footer; build **balanced
  split panels** and **equal-gap stacks** from one grid — `columns(n)` (horizontal) / `rows(n)`
  (vertical), with symmetric outer margins (an intentional asymmetric split still keeps equal
  outer margins, and don't strand a narrow element in a too-wide column); point
  `arrow(direction=…)` the way the flow moves (down/up between stacked boxes), keep repeated
  connectors evenly spaced and adjacent blocks **gapped with a clearly visible gap (≥ ~⅓ `GUTTER`, never near-touching)** — derive the stack pitch from `rows`/`vstack`, not a pitch that barely clears the block height — and centre a lone
  glyph in its box; place figures/plates with **`picture(..., fit="contain")`** so the subject
  is never cropped (`cover` only for edge-tolerant texture).
- **Never hand-pick a y for an auto-growing block — measure or anchor.** A bottom callout
  placed at an eyeballed low `y` grows *down* into the footer when its text wraps (the #1
  recurring layout bug). Use **`bottom_callout()`** (anchors to the footer band, grows up),
  get the safe region from **`content_band()`**, and pack content-height blocks with
  **`vstack(..., bottom=…)`** (equal gaps + no overlap by construction, errors at build time on
  overflow). Use `measure_callout/measure_bullets/measure_text` when you must position manually.
  Then run the Step-5 render self-check.
  - **Reserve the bottom callout's space BEFORE sizing content above it — don't add it last.**
    `bottom_callout()` returns its TOP y; the recurring mistake is to hardcode tall panels/cards
    (e.g. `y=1.7, h=2.5`) and *then* drop a callout on top, so the bar overlaps the cards' bottom
    edge. Call the callout FIRST, then size content to end **a full `GUTTER` above** its returned
    top: `top = dk.bottom_callout(s, 0.6, W-1.2, "要点", "…"); card_h = top - GUTTER - card_y`. A
    *near-zero* overlap is not harmless — the bar draws on top and **clips the cards' rounded
    corners** — so require a visible gap, not just non-collision. (The Step-5 self-check + lint now
    flag a wide bar grazing the content above it, but reserving the space avoids it by construction.)
- **Colour.** Rotate `deckkit.ACCENTS` so diagrams aren't monotone; reserve magenta
  for emphasis. For a **sequence of blocks** (chips / cards / pipeline stages) give each a
  **distinct, deliberately-contrasted hue** via `deckkit.palette(n, ACCENTS)` — it returns `n`
  distinct fills and **warns if any two adjacent blocks aren't visibly different**; never reuse a
  hue for adjacent blocks and **never use a neutral gray as a category colour** (gray reads as
  disabled, not a category — it makes a coloured row look half-finished). Name the closing slide
  for its purpose, in the deck's language ("Conclusion" for an English talk; 结论/总结 on a Chinese deck).
- **Accessibility.** Keep text ≥4.5:1 on its fill (`contrast_ratio`; `chip`/`modbox`
  auto-pick a readable text colour) and never encode meaning by colour alone. Set
  **alt-text** on every informative figure — `deckkit.alt_text(shape, "one-line
  description")` after `add_picture()` — for screen readers; it doesn't render (invisible
  to the critic) so make it a build habit. More in `references/design-principles.md`.
- **Equations:** prefer **`equation_png()`** for any formula the audience reads — it
  typesets real LaTeX-style math (italic variables, true sub/superscripts, fractions,
  Greek) and looks markedly better than ASCII. Pick its `mathfont` (`'cm'` for a
  formal/academic feel; a sans set like `'stixsans'` to match a crisp corporate deck),
  set `color` to contrast the slide, and place the PNG scaled to a target *height* so
  glyph size stays consistent across slides. Use **`eq_par()`** (`N()/SUP()/SUB()`)
  only for trivial inline math or when matplotlib is unavailable. **Never** paste
  Unicode super/subscripts (ᴴ ᵀ ᵣ) — the display font may lack them and render tofu.
  - **Size the formula to the CONTENT text, not to fill the slide.** A formula's glyph
    height should read like the deck's **body/content** size — *never* blown up to span
    the slide width (which oversizes every glyph and breaks the title→content hierarchy),
    never shrunk illegible. On the 10×5.625 canvas, set `equation_png`'s placed **height**
    so a single-line equation lands ≈ **0.22–0.32 in** (≈ body text); scale *height* (not
    width-to-fit) and keep the *same* target height across every equation in the deck so
    they're visually consistent. The formula may be larger **only when it IS the slide's
    hero** (a method slide whose one point is the equation) — otherwise it sits at content
    size. Always confirm in the render that the formula glyphs aren't bigger than the slide
    title's letters.
  - **Even a single variable or symbol uses math format — and stays editable.** Any
    variable/symbol that appears in running text or a bullet (e.g. *x*, *λ*, *σ*, `Aᵀ`,
    *R*(*x*)) must be set in **proper math style** — italic variable + real sub/superscript
    — not typed as plain upright body letters and never as Unicode super/subscripts. For one
    or two inline symbols use **`eq_par()`/native runs** so the symbol stays **click-editable**
    and inherits the surrounding body size; reach for `equation_png` for a full expression.
    Keep the LaTeX source for every `equation_png` in the build script (it's a raster, so
    "editing" means re-rendering from the script) — that is what keeps formulas reproducible
    and adjustable on a later iteration.
- **Formulas → TYPESET math (`equation_png`), never a cropped image.** Unlike a figure or table
  (cropped *whole* from the PDF with `extract_pdf.py`), a needed equation is **re-typeset**: write it
  as LaTeX and render with `equation_png()` (or `eq_par()` for simple inline). A cropped formula
  bitmap is low-res, carries the source's font/background, can't be restyled to the deck, and clips —
  a typeset one is crisp at any zoom and on-brand.
  - **From a paper → transcribe** the formula precisely (don't alter symbols/indices).
  - **From code/other material → derive** the formula the code implements (a loss, update rule,
    metric, transform, a pricing/unit-economics calc) when the content-planner judges it shows the
    idea more directly than prose — useful for **any code-sourced technical deck** (lab meeting,
    defense, conference method talk, teaching, an eng status readout). It must be a *correct*
    expression of what the code computes (verify against the code), not invented or wrongly-simplified.
  - Either way the **fidelity rule applies** — verify the rendered math against the source.
  `extract_pdf.py` is for figures/tables; formulas go through `equation_png`.
- **One language.** Keep the whole deck in the chosen target language — don't drift
  (no stray English on a Chinese deck, no English headings over translated bullets).
  Technical terms / proper nouns / acronyms / units / code may stay original; only
  build mixed/bilingual decks when the user asked (`references/multilingual.md`).

Copy `references/examples/build_example_generic.py` (brand-free) — or a registered
template's own `build_example.py` — for how the helpers compose.

**Scaling up — section fan-out for large decks (optional).** For a normal deck
(~6–14 slides), one author writing one build script is both faster and more coherent —
**that's the default** (and stays the single-author default up to ~14 slides). Only fan
out when it genuinely pays: **large decks (15+ slides)** or **independently-sourced sections**
(different papers/datasets/areas). The
rule that keeps quality high: **centralize coherence, parallelize only the independent
work.** The coordinator (you) keeps the comprehension brief, the arc, and a single
shared `style.py` (palette/font/chrome — copy `references/examples/style_example.py`);
then dispatch **one subagent per *section* (not per slide)** in parallel, each
importing that `style` and exposing `build_section(prs)` (copy
`references/examples/section_example.py`), each self-rendering its own section to
optimize it; finally `scripts/assemble.py` runs them in order into **one** deck (no
fragile .pptx merging). Don't do one-agent-per-slide-with-neighbour-chat — it drifts,
fights the single-file artifact, and doesn't speed up the parts that actually cost
time. Full workflow (incl. the critic panel + finding-routing) in
`references/large-deck-orchestration.md`.

**Motion & builds — the animation that matters is in-slide "appear" builds, NOT slide transitions.**
🔴 **Do not "animate" a deck by putting a fade transition on every slide — that adds nothing and is the
lazy mistake to avoid.** What "add animation" means here is **revealing bullets / blocks one at a time
on click** (an *appear* build) so the audience follows the speaker instead of reading ahead. The two
layers are **not** equal:
- **(1) In-slide appear builds — THE real work; default to considering one on every multi-point content
  slide.** Reveal each **bullet, card, pipeline stage, quadrant cell, or the final takeaway callout**
  one per click. Reach for it wherever stepping the reveal will *emphasize*, *engage*, or *guide* — a
  multi-point list, a **pipeline / multi-stage diagram** (stage at a time), a **multi-part argument**,
  **before→after**, **evidence→takeaway**. Leave title / divider / single-image / scan-all-at-once
  slides plain. By taste, not a quota (consecutive builds fine, a plain stretch fine) — the failure is
  *thoughtlessness*: either no build where one would clearly help, or motion for flourish.
- **(2) Slide-to-slide transition — optional, secondary, off the critical path.** A calm deck-wide
  `slide_transition(s, "fade")` is *allowed* but never the point; a deck with **no** transition and good
  appear-builds beats one with a fade on every slide and no builds. Decide it once; **don't count
  "added transitions" as having animated the deck.**

Use `scripts/anim.py`: draw the static scaffold, wrap **each reveal-on-click chunk** in a `Build.step()`
(one bullet/block per step → they appear one by one), then `apply(effect="appear")` (instant) or
`"fade"` (soft). Recipe in `references/animation.md` ("bread-and-butter build"). A slide must still read
correctly **fully-built** (for print/PDF) — builds layer on a correct static slide, never fix a
cluttered one.

**Record a one-line motion manifest** as you go — for each slide, `build: <what reveals,
in order>` or `static: <why nothing to pace>`, plus whether the deck-wide transition is on.
You'll hand this to the critic in step 5 (it can't *see* motion in a static render, so it
judges your motion *design* from this manifest plus the build-candidates it spots in the
pixels). Keep it next to the build (a comment block in `build_<deck>.py` is fine).

## Step 5 — Render, verify, then run the actor–critic loop
First **render and look** (`bash scripts/render_deck.sh <deck.pptx>` → one PNG per
slide). python-pptx writes blind — overflow, low contrast, a callout on the footer,
or a missing glyph only show up in the image. Fix mechanical issues and re-render.
(First time on a machine, or a render errors? `bash scripts/check_env.sh` verifies
LibreOffice + the python deps and prints the fix for anything missing.)
**Codex sandbox note:** LibreOffice may abort or produce no PDF when launched inside a managed
sandbox even though `check_env.py` passes; in that case rerun only the render command with elevated /
unsandboxed execution, then continue the normal render -> lint -> critic loop. This is an environment
permission issue, not evidence that the deck is malformed.

**Then run the layout lint** — `python scripts/lint_deck.py <deck.pptx>` — a cheap, deterministic
check that flags **off-slide overflow, text overflowing the card behind it, uneven card heights in a
row, two solid blocks/images overlapping (neither contained), footer collisions, orphaned punctuation
/ widow (a lone 。/，or single glyph on the last line — 避头尾), CJK text with no EA font (the kinsoku
root cause), whole-page-image (editability), and orphan/empty slides**: exactly the failures the eye
misses (a callout tucked under a panel; a 2-line body hanging below a card; a 。 stranded on its own row). Fix every finding, re-render, and re-lint
to clean before handing to the critic. It's a safety net for the no-overlap / fits-its-box rules, **not** a
replacement for looking (it can't judge crop, balance, legibility, or fidelity).

**Render self-check — scan EVERY slide for these before handing to the critic** (they're
invisible in the build code and only appear in the pixels; catching them yourself saves a
critic round — full rationale in `references/design-principles.md`):
- **Overflow / contrast / footer / glyphs** — no clipped or spilling text, ≥4.5:1 contrast,
  nothing jammed on the footer, no tofu/missing glyphs, and **no orphaned punctuation** (a lone 。/，
  or single glyph stranded on its own row — set `deckkit.EAFONT` so PowerPoint's kinsoku keeps it
  attached, and widen/reword if needed).
- **No build/meta annotation visible** — scan for any text that describes *how the slide was made*
  rather than its content: "（可点击编辑的原生图表）"/"(editable native chart)", "(AI-generated)", "(placeholder)",
  "(draft/草稿)", "generated by…", TODO/FIXME. It must NOT be on a slide — delete it (it belongs in code
  comments or the hand-off). A leaked meta-label ships broken.
- **Stacked groups read as separate** — for stacked labelled groups (stat label+value+caption, stacked
  cards), the gap *between* groups is clearly larger than the gaps *within* one (proximity); no caption
  crowding the next group's label.
- **Balance & suitable space** — every element has a comfortable margin on **all four sides**:
  nothing crowds an edge, nothing strands a big dead gap (the right *degree* — not too tight,
  not too loose). Split panels + flanking margins equal; no large dead-white band beside a
  narrow element; a **figure beside text is anchored to its margin (not centred-and-far-
  stranded)** with the text one gutter away; repeated blocks/connectors evenly spaced; grid-
  aligned, nothing lopsided. **A column/stack inside a card fills the space below its header** — a
  ladder, a list, stacked chips should **distribute evenly** to fill the available height; don't
  bottom-/top-anchor and strand a visible gap between the header and the first item (compute the gap
  from the region — `(region_h − n·item_h)/(n−1)` — or use `vstack`/`rows`, never a hand-picked offset).
- **Block padding & no inflated filler** — text inside a chip/card/callout hugs the box with a
  **modest, balanced** top/bottom margin (middle-anchored; not floating in a tall box, not cramped).
  A short card must not leave a white strip at the bottom. **No oversized block faking a full slide:**
  a single short line of small font swimming in a big box is a placeholder tell — either *add real
  content* to fill it or *shrink the box to hug the text* and use the freed space; never inflate a
  container to cover a gap.
- **Font hierarchy (content < title)** — body/content/callout/label text is **visibly smaller** than
  the slide title (clear step between levels, ~1.4–1.8×); no body, formula, or chip label set as large
  as (or larger than) the title. The only thing that may exceed body size is a deliberate **hero**
  element (the one big numeral or the slide-defining equation) — and even it stays below the title.
- **Formula sized to content** — every equation's glyphs read at ≈ **body size** (not blown up to fill
  the slide width, not illegibly shrunk), and **consistent across slides** (same placed height); any
  inline variable/symbol is in **math format** (italic, real sub/superscript), never plain body letters
  or Unicode super/subscripts.
- **Footer collision / overlap** — no block crosses into the footer band and no two stacked
  blocks overlap. If one does, the cause is almost always a hand-picked `y` for an auto-growing
  callout/stack — fix it by switching to `bottom_callout()` / `vstack()` / `content_band()`, not
  a one-off coordinate nudge (that just recurs when the text changes). **Look specifically at the
  seam where content meets a bottom callout/bar:** a *wide* bar grazing the cards above it by even
  a sliver clips their rounded corners — there must be a visible gap, so size content to the
  callout's returned top minus a `GUTTER` (reserve its space before sizing content, don't add it last).
- **Adjacent / stacked blocks — a VISIBLE gap, not a sliver** — between any two same-axis blocks
  (stacked panels, side-by-side cards, pipeline nodes) the gap must read clearly: **≥ ~0.12in
  (~⅓ `GUTTER`)**. A ~0.02in seam (three panels at pitch 1.04 with height 1.02) reads as touching —
  a gap far smaller than the slide's own margins looks cramped even though nothing overlaps. Cause:
  a hand-picked pitch that nearly equals the block height. Fix: **derive the pitch from the region** —
  `rows(n)` / `vstack(..., bottom=…)` — so the gap is set by construction, never `block_h + 0.02`.
- **Bar labels sit ON the bar** — for any track+fill row (percentile / share / progress / "want vs
  have"), the value/percent label is **vertically centered on the bar's centerline**, not floating
  above or below it, and doesn't overlap the track. Use `meter_bar()` (which centers the value by
  construction) rather than hand-placing a number at a guessed `y`.
- **Marker captions sit UNDER their marker** — on a timeline / tick row / numbered-step row, each
  caption (date · title · sub) is **horizontally co-centered with its dot/marker**, *including the
  first and last*. The classic bug: an end marker sits near the slide edge and its centered caption
  gets clamped inward, so the caption drifts off to the side of its dot. Use `timeline()` or
  `spaced_centers()` (which **inset the end markers** so every caption stays co-centered) — never
  hand-roll a dots+captions row with a per-caption edge clamp.
- **Diagrams** — arrows point the way the flow moves (down/up between stacked boxes); adjacent
  blocks have a visible gap (never touching); a lone glyph/icon optically centred (ASCII, not
  full-width, for a centred mark on a CJK deck).
- **Block colours** — in a sequence of chips/cards/stages, every block is a **distinct,
  deliberately-contrasted hue**: no two adjacent blocks share a colour, and **no neutral gray
  sits in the sequence as if it were a category** (use `palette()` — it warns on both). A vivid
  block beside a gray one reads as half-finished.
- **Titles** — a subtitle/definition line has a clear gap below the title's accent rule; the
  kicker/eyebrow adds a section label, it doesn't echo a word the title already leads with.
- **Images** — the key **subject is whole, not cropped** (`contain` vs `cover`); a generated
  image of real things is **factually right** (relative size/proportion, count, colour); any
  **labels sit under the feature** they name.
- **PDF figures cropped precisely** — for every figure pulled from a paper, zoom each edge and
  confirm BOTH: nothing of the figure is clipped (legend, colour bar, axis labels/ticks, outer
  rows/cols, a sub-plot's x-axis labels) AND no page text bled in (its caption, a neighbour's
  caption fragment, a running head, a page number). Prefer `extract_pdf.py figure` over eyeballed
  fractional crops; a clipped *or* text-contaminated crop is a real flaw, not a nitpick.
- **Motion & images by taste** — what's there earns its place (emphasises/engages/guides),
  nothing thoughtless; what's plain is fine.
**On native Windows (PowerShell / cmd) there is no bash — call the Python entry points
directly: `python scripts\render_deck.py <deck.pptx>` and `python scripts\check_env.py`.**
The `.sh` files are just shims that forward to those `.py` scripts, so macOS / Linux /
Git Bash / WSL keep working unchanged; everything else in the toolchain is already
cross-platform Python.

**If a render fails *after* `check_env.sh` passes** (a build/LibreOffice error mid-loop),
isolate it rather than thrash: the **build script is the source of truth and re-runnable**,
so comment out the suspect slide (or the shape you last added), rebuild + re-render to
confirm the rest is fine, then fix that one slide and restore it. A frequent culprit is a
bad asset path (a figure/GIF/equation PNG that doesn't exist) or a malformed `equation_png`
string — the Python traceback names it. Don't ship a partially-rendered deck silently; if
one slide can't render, tell the user which and why.

**If you used animation/builds:** the render (and the critic) see only the **final
built state** — they can't play the sequence (the anim.py timing is verified to
round-trip through real PowerPoint as native builds; LibreOffice just can't *play* it).
So verify the fully-built PNG reads correctly on its own (run the loop as normal), and
in step 6 **describe the click order** to the user. Builds are a layer on a correct
static slide, never a fix for a cluttered one.

Then run the **actor-critic loop** — this is the quality engine, and the critic is a
*demanding* judge (see `agents/critic.md`), not a rubber stamp:
1. **Critique.** Dispatch an independent critic subagent through the host's available
   multi-agent/subagent tool, pointed at `agents/critic.md`, giving it the rendered PNGs, the deck's **purpose + audience**,
   `references/review-rubrics.md`, the **motion manifest** from step 4 (so it can judge the
   motion *design* it can't see in a static render), **and the source material** (so it can
   verify claims/figures/numbers, not just style). A *separate* agent matters: it judges the
   pixels, not your intentions. It returns structured JSON — `verdict`
   ("consent"/"revise"), per-slide `findings` (severity + concrete fix), strengths.
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
       each judging only the rendered pixels + source: is the finding **real** (re-derive
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
   as-is) — not merely when the last round's issues are fixed. Cap the rounds by
   stakes so the loop converges fast: **low-stakes ≈ up to 2 rounds, high-stakes up
   to 3.** If the first render is already clean and the critic consents, you're done
   in one round — don't manufacture extra rounds. Otherwise apply the blocker+major
   fixes, rebuild, re-render.
3. **Repeat.** The critic **re-reviews the whole deck fresh** (fixes introduce new
   issues). Converge; keep a short record of what changed each round so improvement is
   visible, not just churn.

**High-stakes only — verify the fixes and corroborate consent.** On re-render, the
arbiters cheaply re-check each promoted finding against the actor's **change manifest**
(what changed + which slides were touched): did the fix actually land *in the pixels*,
and did it regress a neighbour? A fix that didn't land **stays open** instead of
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

## Step 6 — Show the user, then iterate on feedback
Present the rendered slides (or a contact sheet) plus a short note: slides count,
purpose it was built for, and the font/portability caveat if relevant. **Tell the
user the exact output folder path (`~/Downloads/<deck-name>/`, or wherever they
chose) and ask them to open it and check the `.pptx`** — the rendered PNGs verify
layout, but they should confirm the editable deck itself opens cleanly on their
machine. If you added any forward-looking content (per the fidelity rule), call that
out explicitly here so they can confirm it.

**Keep the hand-off minimal — caveats + next steps, not a recap.** The note should carry only what
the user *acts on*: the folder path, the open-the-pptx check, the font/portability caveat, any
forward-looking content you added, and open questions (e.g. a missing real brand asset to supply). Do
**not** narrate the deck slide-by-slide, restate what they can see in the render, or self-praise the
result — a tight hand-off respects their time and reads as senior.

**For a long deck (~15+ slides), show work at ~50%, not only at 100%.** When a build is large enough
that a wrong direction is expensive to unwind, render the first few finished slides (cover + a couple
of content archetypes) and check in **before** completing the rest — "here's the look and the first 3
slides; continuing in this direction unless you'd change something." Cheaper than discovering a
palette/density/structure mismatch after all 20 are built. (Short decks: just build and run the critic.)

**If the deck has speaker notes, tell them how to use the notes.** They render nowhere on
the slide, so the user may not know they exist: "the spoken script is in the notes — open
**Presenter View** (PowerPoint: Slide Show → Presenter View; Keynote: Play with a second
display / rehearse mode) to see it while presenting." Offer to **export the notes** as a
plain-text rehearsal script with `scripts/export_notes.py deck.pptx` if they'd rather
rehearse away from the slides.

**Tell them the deck is fully editable — and how to change it without losing work.**
The `.pptx` is native (real text/shapes/images), so they can edit anything in
PowerPoint/Keynote and save. But the build script *regenerates the file from scratch*,
so a later rebuild would overwrite anything they hand-edited — the two don't merge. So
give them the two non-conflicting lanes in one line: **(a)** take it from here in
PowerPoint themselves (you won't rebuild over their file), or **(b)** tell you the
changes and you edit the build script (reproducible, survives future iterations). Note
the font/portability caveat if relevant. Full guidance — and the rule for iterating
safely — is in `references/handoff-and-iteration.md`.

Then **fold in the user's feedback** — treat their corrections as the highest-priority
signal, re-run the build → render → critic loop, and keep going until **the user is
satisfied**. **One safety rule when iterating after delivery:** before you re-run the
build, check whether the user has hand-edited the delivered file (ask, or compare its
mtime to your last build); if they have, **don't regenerate over it** — reconcile first
(fold their edits back into the script via `scripts/extract_deck.py`, or edit their file
in place). Never silently clobber edits you didn't make. Each round should make the deck
more specifically theirs (their emphasis, their wording, their priorities), not just
generically "better".

## Anti-patterns — never do this
A checkable red-flag list; if a draft does any of these, stop and fix it before shipping:
- **Never invent** numbers, results, citations, or figures the source doesn't state (the
  one allowed exception is *flagged* forward-looking content).
- **Never skip the interview**, and **never assume** the topic/content, template, style,
  or — for a brand-new user with no footprint — a domain (ask the subject openly).
- **Never present last year's data as current** on a deck dated this year — ground to today.
- **Never leave a build/meta annotation on a slide** — "（可点击编辑的原生图表）"/"(editable native chart)",
  "(AI-generated)", "(placeholder)", "(draft)", "generated by…", TODO/FIXME. Slide text is the
  audience's content, never a note about how it was made; that goes in code comments or the hand-off.
- **Never let stacked groups blur together** — the gap between groups must beat the gap within a group.
- **Never leave a slide awkwardly empty, and never fake fullness with an oversized block** — fill space
  by **enriching the content** (add the detail/example/figure the point deserves) or enlarging the hero;
  never inflate a card/callout around a single short line of small font to cover a gap (shrink the box
  to hug its text instead).
- **Never set content text as large as (or larger than) the slide title** — body/callout/formula/label
  must be visibly smaller than the title; only a deliberate hero numeral/equation may exceed body size,
  and it still stays below the title.
- **Never oversize a formula or leave a variable in plain text** — size every equation to ≈ body text
  (consistent across slides, not blown up to fill the slide width), and set even a lone inline variable
  in math format (italic + real sub/superscript), keeping the LaTeX in the build script so it stays
  reproducible/editable.
- **Never act as your own final critic** — an independent critic must consent; **never ship
  a partially-rendered or contested-blocker deck silently** (surface the disagreement).
- **Never clobber the user's hand-edits** — reconcile before regenerating over their file.
- **Never** ship a wall-of-text slide, a redrawn source figure where a real one exists, a
  cine GIF reduced to one frame, meaning carried by colour alone, or text below ~4.5:1 contrast.
- **Never** put real slide text, labels, numbers, logos, citations, source figures, or
  evidence-bearing charts inside an AI-generated image; generated images are text-free
  visual support unless the user explicitly requested a raster mockup.
- **Never** clip a figure's own parts (legend, colour bar, axis labels/ticks, outer
  row/column) with a crop or a too-large placement, and **never** chop a multi-panel figure
  into context-losing pieces when the whole figure would serve — default to the integral
  figure; **re-view every figure after cropping/placing** to confirm nothing is cut off.
- **Never** leave text in a callout / chip / takeaway bar visibly off-centre (sitting low or
  edge-hugging) — centred boxes need the textbox to span the box's true extent.
- **Never** paste Unicode super/subscripts (ᴴ ᵀ ᵣ); **never** build a "generic conference"
  deck (research the venue); **never** let the deck drift between languages.

## Files
**Scripts** (`scripts/`):
- `deckkit.py` — the build helpers (template & blank decks), **incl. the editable native charts**
  (`native_chart`/`native_dual_axis`/`native_donut`/`native_pareto`/`native_bubble` — click-to-edit,
  any-language-safe); the build's source of truth. Full signatures in its docstrings.
- `render_deck.py` — pptx → one PNG per slide (verify + critic loop); finds LibreOffice cross-platform
  or set `SOFFICE` (`.sh` is a shim). `check_env.py` — preflight if a render fails. `inspect_template.py`
  — a template's layouts/placeholders/logos. `requirements.txt` / `install_skill.py` — deps / installer.
- `lint_deck.py` — deterministic layout lint (off-slide overflow · block/image collision [containment
  excluded] · footer-zone intrusion · text-past-card · uneven rows); run after render, before critic;
  non-zero on findings. `smoke_deckkit.py` — regression guard for the helpers.
- `anim.py` — PowerPoint click-builds/transitions (pair `references/animation.md`).
- `designed_charts.py` — raster matplotlib chart recipes (use only for dumbbell or a deliberate
  look — prefer deckkit's native charts; `references/data-viz.md`). `presets.py` — named
  design-language presets (glassmorphism · swiss · editorial_paper · editorial_report · risograph ·
  memphis · brutalist · blueprint · ink_wash · eastern_traditional · **consulting** (MBB action-title) ·
  **dark_tech** (engineering dark + diagram-island) · **luxury_dark** · **museum_memorial**; ink_wash/
  eastern_traditional → `references/east-asian-aesthetic.md`; the full style+component catalogue →
  `references/design-gallery.md`).
- `image_prompts.py` (build the prompt manifest) → `generate_images_codex.py` (no-key, Codex CLI) /
  `generate_images_openai.py` (API fallback). `archetypes_html.py` (direction-gate previews as
  **one HTML link**; `archetypes.py` is the older pptx-render variant + the post-pick one-slide
  fidelity confirm) · `assemble.py` (assemble a sectioned deck) · `export_notes.py` (notes →
  rehearsal script).
- `icons.py` — fetch an open-licensed SVG icon (Tabler/Lucide/Phosphor/Simple…), recolor to the deck
  palette, rasterize to a transparent PNG (`icon_png(spec, out, color, px)`); pair with
  `deckkit.icon`/`icon_card`. See `references/icons.md`.
- `image_fx.py` — `duotone(img, ink_a, ink_b)` / `grayscale(img)` — preprocess a colour photo to the
  deck's ink so it doesn't fight the accent (riso/brutalist/ink/luxury/museum). See `design-gallery.md`.
- `extract_pdf.py` (crop a figure from a PDF — `figures`/`figure`/`autofig` auto-detect, `page`/`crop`
  manual) · `crop_helper.py` (crop/trim/panel **by looking, not guessing**) · `extract_deck.py` (pull
  content out of an existing deck — the redesign path).
**Agents** (`agents/`): `content-planner.md` (Step-1 deep-understand + the build-ready per-slide plan incl. the Form ledger; the Step-3 checkpoint) · `critic.md` (independent critic brief — the two review lenses + JSON schema) · `arbiter.md` (high-stakes finding cross-validation + fix-verification; no-op low-stakes) · `asset-prep.md` (execution-only asset materializer — crops/equations/plates/icons after Step-3 approval; zero design decisions) · `openai.yaml` (Codex display metadata).

**References** (`references/`, loaded on demand): `design-principles.md` (the craft / the "why"; incl. the **C.R.A.P. framework** — Contrast · Repetition · Alignment · Proximity) · `design-gallery.md` (style+component catalogue mined from 21 pro decks — pick a preset, reach for the right component) · `semantic-color-contract.md` (bind a hue to a concept deck-wide) · `review-rubrics.md` (universal + per-purpose review criteria) · `design-by-purpose.md` (per-purpose look for "design a clean one") · `form-selection.md` (**content-shape → candidate FORMS** — the single design-decision map; generate a set, pick deliberately) · `data-viz.md` (pick the chart type; editable-native vs raster) · `image-generation.md` (when/how; topical, text-free, consistently placed) · `icons.md` (one coherent open-licensed icon family, recolored, restrained) · `generated-template.md` (Q1's image-tool template branch) · `style-analysis.md` (mimic a style example, Q4) · `font-guidance.md` (portable fonts, tofu recovery) · `multilingual.md` (non-Latin / CJK / RTL) · `east-asian-aesthetic.md` (Chinese ink / traditional looks — paper · seal · CJK numerals · `ink_wash`/`eastern_traditional`) · `animation.md` (when/why + `anim.py`) · `large-deck-orchestration.md` (section fan-out; default is single-author) · `collaborative-mode.md` (direction→outline→draft gates) · `redesign-existing-deck.md` (diagnose-then-rebuild) · `handoff-and-iteration.md` (delivery + iterate without clobbering edits) · `examples/` (`build_example_generic.py`, `style_example.py`, `section_example.py`).

**Registry** (NOT part of the skill): `~/.codex/slide-templates/` (Codex) · `~/.claude/slide-templates/` (Claude Code) — the user's saved templates; read for choices, write new `profile.md`s to the active host. Empty for a new user.
