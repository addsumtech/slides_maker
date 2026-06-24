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
  documents, or batch asset prep (figure crops, equation PNGs) — but never split one
  paper's intro/method/results across blind agents; the through-line is one mind's job.
  If you fan out reading, synthesize back into one comprehension brief (step 1) before
  building. Parallelism speeds *gathering*, never *understanding*.
  Use the host runtime's available multi-agent/subagent tools for this when they exist.
- **Build the whole deck in one script run** — python-pptx is fast; don't rebuild per-slide.
- **Scale the critic to stakes** (step 5): one critic for a quick internal deck; the
  multi-critic, multi-round panel only for high-stakes. The loop is non-negotiable;
  its *weight* is what you tune.

**Two modes.** *Auto* (default): interview, then build and run the critic loop to a high
bar yourself. *Collaborative* (opt-in — when the user wants to see options or approve as
you go, or for a brand-defining deck): build behind cheap **gates** — pick a *direction*
(2–3 styles shown as real rendered archetypes) → approve the *outline* → build the rest.
The critic captures *quality*; the gates capture *preference*. Offer it in one line;
never force it. See `references/collaborative-mode.md` (+ `scripts/archetypes.py`).

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
1. Template/brand: existing template, new template, or design a clean one?
2. Purpose/audience/time: who is this for and how long?
3. Source material: paper, deck, doc, figures, repo, or none?
4. Style/language: minimal, corporate, academic, playful, 中文/English/etc.?
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
   with a `profile.md`). Offer those as choices, **plus** "a new template (I'll
   provide one)", "design a clean one", and **"generate a template with an image tool"**. Then:
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
       not three shades of one idea), each a style module rendered by
       `scripts/archetypes.py` into the **same** representative slides (cover / points+
       callout / diagram / data), quick-critic each, then collect the pick + knobs. Present
       the pick as **A / B / C plus a fourth "D — describe your own" option**: if the user
       picks D, they *type the look they have in mind* (a reference, a brand, a mood, a
       constraint) and you **synthesize a fourth direction from that description** — build it
       as a style module, render the same archetypes, and show it alongside (iterate until
       they consent), rather than forcing one of your three guesses. The three are only your
       opening proposals; the author's own intention always outranks them. The
       chosen/synthesized module becomes the deck's `style.py`. **Once they pick, delete the
       throwaway preview decks + rejected modules** (keep only the chosen style), then build
       the full deck in it — don't leave demo options littering Downloads.
     - *Picks design-one* → build a single look shaped to purpose, as above.
     This offer is **skippable, never forced** — a brand-new from-scratch deck is exactly
     when showing options pays off, but a user in a hurry can decline in one click.
   - *Generate a template with an image tool* → **a bespoke visual identity created with the
     image tool** (a styled hero/divider illustration) and then reproduced natively so every
     content block fits it — for a vivid, designed deck (a launch, a festival/event, a brand
     deck, a playful pitch) where a clean default look isn't enough. **Follow
     `references/generated-template.md`** — the short version:
     1. **Gather what the look needs** (one extra mini-interview *now*, before generating): the
        **scenario/topic** and any **brand colours**; **seed the look from the Style library** in
        `generated-template.md` (proven styles — Memphis (the sample's), Swiss, Art Deco,
        Vaporwave, Editorial, Risograph, …) by offering the **3–4 best-fit as options** (+
        "describe your own" / "I'll provide a reference"); and invite the user to **drop in
        reference images / a logo / mood material**. Then **tailor the chosen style** to the
        scenario + brand before generating (the preset is a starting language, not a straitjacket).
     2. **Generate the template** — a **text-free** full-bleed hero/divider illustration in that
        style with a calm zone for the title (**no API key needed** — in Codex, use the native
        imagegen tool call directly and save/copy the selected bitmap into the deck folder; outside a
        native-imagegen host, fall back to the **Codex CLI** `scripts/generate_images_codex.py` if `codex` is installed →
        OpenAI `scripts/generate_images_openai.py` only as a fallback; see
        `references/image-generation.md`), then **derive a matching `style.py`**: pull the
        palette straight from the image with `deckkit.palette_from_image(...)` and define the
        template's motif + component helpers, so **native content reuses the same colours,
        decorations, and card/heading treatments** (this is what makes inserted blocks fit).
     3. **Render a sample** (the cover + one real content slide) and **ask for feedback**:
        > **🔴 CHECKPOINT** — show the generated template (hero + a sample content slide) and get the user's OK; iterate (regenerate the image / tune the palette/motifs) until they confirm.
     4. After confirm, **the look is decided — so SKIP the 3-direction gate** (and any style
        step); continue the rest of the interview (purpose, audience, source, language) normally.
     5. Build to it: **dividers/cover use the generated image(s)** (native title on top),
        **content slides are built natively in the derived `style.py`** so blocks/bullets/cards
        match the template. Save the confirmed template to the registry so it's reusable.

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
     (collaborative mode Gate A, `references/collaborative-mode.md` + `scripts/archetypes.py`):
     real rendered archetype slides the user picks from before the full build. **Skippable,
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
(purpose/audience/time, style/language, template
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
    brand-defining? Show 2–3 rendered direction archetypes and let the user pick
    (collaborative mode, `scripts/archetypes.py`). Sameness across decks is the failure to
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
**Precondition — the comprehension gate:** before showing the plan, confirm it carries a
*complete* comprehension brief (every field filled + traced) and claim ledger (no shipped
`verified?=N` rows); a plan whose brief is empty/hedged/untraced is **not ready** — send it
back to the planner rather than building on a shallow read.
> **🔴 CHECKPOINT** — show the deck plan (brief + ledger first) and get the user's OK (including the image opt-in) before building.

## Step 4 — Build with deckkit
Write a small per-deck build script that imports `scripts/deckkit.py` rather than
re-deriving primitives. Helpers: `content_slide`/`title_bar` (a clear title),
`columns` (equal-width split panels with symmetric margins — use it for *any* left/right
or N-up layout so the two sides and their flanking white space come out the same width),
`picture` (place a figure/plate without distorting it — `fit="contain"` keeps edges,
`fit="cover"` crops to fill), `bullet`, `callout` (auto-grows to fit), `arrow`,
`chip` (pipelines), `modbox`,
`content_band(slide)` (the SAFE rect below the title and above the footer — ask for it
instead of hardcoding "above the footer" y-values), `bottom_callout(slide, x, w, label, body)`
(a footer-SAFE bottom takeaway — measures itself, anchors to the bottom band, grows UP, so it
can never collide with the footer; **use this for every bottom callout** instead of a
hand-picked low `y`), `vstack(slide, x, y, w, blocks, bottom=…)` (measured vertical packer —
**equal gaps + no overlap guaranteed by construction**, raises at build time if content
overflows the band; pass `(measure_callout(...)/measure_bullets(...)/measure_text(...), draw)`
blocks), and the `measure_*` helpers to know a block's true height BEFORE placing it,
`palette(n, ACCENTS)` (n **distinct, contrast-checked** category fills for a chip/card/stage
sequence — warns if adjacent blocks aren't visibly different; never a gray filler),
`palette_from_image(path, n)` (extract a **generated template's** palette from its image so
native content matches it — the bridge for the image-tool template branch),
`scorecard` / `leaderboard` / `takeaway_rail` (KPI tiles · ranked rows keyed to a chart · the
"so-what" rail beside a chart — the data-furniture; pair with the chart roster in
`references/data-viz.md` + `scripts/designed_charts.py`),
`change_stat` (a `before → after` change stat with the AFTER value emphasized large and **vertically
centred** with the small before+arrow — avoids the baseline-mix where a small arrow/prefix sinks
below a big number),
`glass_card` / `glow` / `scrim_overlay` (frosted-glass card · soft radial glow · graduated photo
scrim — for dark/glassmorphism decks and text-over-photo legibility; built on `box`'s new
gradient+alpha fill) and `offset_shadow` (hard letterpress/riso shadow),
`editorial_header` (caps eyebrow + title + hairline), `big_numeral` (oversized index figure,
marker/ghost — never wraps), `stat_row` (editorial figure+unit+caption row), `quadrant` (2×2 with
meaningful axes), `hub_spoke` (radial one-core-many-peers), `timeline` (native h/v with one
highlight), `before_after`/`image_tab`/`photo_triptych` (editorial photo kit), `corner_frame`
(L-brackets for a sparse closing), and `accent_one` (one-accent discipline — colour only the focal item),
`cover` / `colophon` (a publication-style cover + a mirrored closing colophon — bookend the deck;
stronger than a plain title/"Thanks"), `sources_page` (mono numbered references — a research deck's
colophon), `part_eyebrow` / `page_marker` (tracked-caps mono eyebrow + tiny page marker — route
chrome through one mono font for a quiet signature), `specimen_card` (rule-on-top card with a giant
glyph/number specimen — comparing fonts/brands/metrics), `wireframe_grid` + `spec_list` (a
self-demonstrating annotated grid + mono spec math — for decks ABOUT layout/design/systems),
`photo_card` (translucent tinted card to hold text on a photo), `backdrop_motif` (faint full-bleed
grid/texture + accent disc to bookend cover ↔ closer),
`table` (booktabs data tables — highlight the key row to foreground the authors'
comparison), `code_block` (monospace code panels with line-highlight),
`hrule` (table rules), `equation_png` (formal LaTeX-style math via matplotlib) /
`eq_par` (quick editable inline math), `contrast_ratio` (check a text colour against
its fill clears ~4.5:1 before you commit to it). If the user gave a **style example** (Q4),
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
- **Animated results (GIF / looping animations) → insert the GIF itself**, never reduce
  it to a single frame. `s.shapes.add_picture(path_to.gif, ...)` embeds the real animated
  GIF; PowerPoint and Keynote **loop it in slideshow**. For time-resolved / 4D / dynamic
  results that motion *is* the result — a frozen frame throws away the point. Size it like any
  figure; the render and critic see only the first frame (expected — note it for the
  user), and it plays in the delivered deck. (For *built* GIFs you generate, optimize
  the palette/size so the file stays reasonable.)
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
- **Generated visual plates (atmosphere / conceptual) — by taste & purpose; full rules in
  `references/image-generation.md`.** Generate where your design sense says a plate helps (no
  quota), styled to the deck's purpose+topic, **opt-in only**; never bake words/numbers/labels/
  charts/logos into a plate (those stay editable objects or real assets). **Each plate must be
  *highly topical* — depict THIS slide's actual subject, not a generic "fancy" image that could sit on
  any slide** (name what it shows; if you can't, cut it). **And place plates consistently — never a
  one-off generated *header* on a single body slide** (title chrome is `title_bar`'s; a content plate
  goes full-bleed / side-panel / inline, with one role+art-direction across the plated slides). Build prompts with
  `scripts/image_prompts.py` (a sub-outline of *only* the plated slides), then generate by the
  **auto-detected** source — **no API key needed**: native imagegen (Codex tool call, then save/copy
  the bitmap into the deck folder) → else the **Codex CLI**
  `generate_images_codex.py` if `codex` is installed (no key) → OpenAI `generate_images_openai.py`
  (+`OPENAI_API_KEY`) only as a fallback if neither exists. Use what's present and say so; ask only if
  none is available (see `image-generation.md`); keep
  assets in `~/Downloads/<deck>/assets/generated/` and place with `deckkit.picture(...)` —
  `fit="contain"` when a subject/edges must stay whole, `fit="cover"` only for edge-tolerant
  texture. Render-check: calm space behind text, no pseudo-text/fake charts, subject not cropped,
  real things factually right.
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
  connectors evenly spaced and adjacent blocks **gapped (never touching)**, and centre a lone
  glyph in its box; place figures/plates with **`picture(..., fit="contain")`** so the subject
  is never cropped (`cover` only for edge-tolerant texture).
- **Never hand-pick a y for an auto-growing block — measure or anchor.** A bottom callout
  placed at an eyeballed low `y` grows *down* into the footer when its text wraps (the #1
  recurring layout bug). Use **`bottom_callout()`** (anchors to the footer band, grows up),
  get the safe region from **`content_band()`**, and pack content-height blocks with
  **`vstack(..., bottom=…)`** (equal gaps + no overlap by construction, errors at build time on
  overflow). Use `measure_callout/measure_bullets/measure_text` when you must position manually.
  Then run the Step-5 render self-check.
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

**Motion & builds — by taste and purpose, not a quota.**
Add a build where your design sense says stepping the reveal will *emphasize*, *engage*, or
*guide* — and leave it off where it wouldn't (consecutive builds are fine, a long plain stretch
is fine; the only thing to avoid is *thoughtless* motion added for flourish). Two layers,
decided separately: **(1)** a calm deck-wide `slide_transition(s, "fade")` is a sensible
low-distraction default (or omit for a static/print feel — decide deliberately); **(2)
click-builds** per slide for the clear cases — a **pipeline / multi-stage diagram** revealed a
stage at a time, a **multi-part argument**, **before→after**, or **evidence→takeaway** — while
title / divider / single-image slides simply stay plain.

Use `scripts/anim.py` (it injects the PowerPoint timing XML python-pptx can't): draw the
static scaffold, wrap each reveal-on-click chunk in a `Build.step()`, then
`apply(effect="fade")` — subtle fade, one idea per click, scaffold always visible. A slide
must still read correctly fully-built (for print/PDF) — builds layer on a correct static
slide, never fix a cluttered one. See `references/animation.md` for craft rules and usage.

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
row, two solid blocks/images overlapping (neither contained), footer collisions, whole-page-image
(editability), and orphan/empty slides**: exactly the failures the eye misses (a callout tucked under
a panel; a 2-line body hanging below a card sized for one). Fix every finding, re-render, and re-lint
to clean before handing to the critic. It's a safety net for the no-overlap / fits-its-box rules, **not** a
replacement for looking (it can't judge crop, balance, legibility, or fidelity).

**Render self-check — scan EVERY slide for these before handing to the critic** (they're
invisible in the build code and only appear in the pixels; catching them yourself saves a
critic round — full rationale in `references/design-principles.md`):
- **Overflow / contrast / footer / glyphs** — no clipped or spilling text, ≥4.5:1 contrast,
  nothing jammed on the footer, no tofu/missing glyphs.
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
  aligned, nothing lopsided.
- **Block padding** — text inside a chip/card/callout hugs the box with a **modest, balanced**
  top/bottom margin (middle-anchored; not floating in a tall box, not cramped). A short card
  must not leave a white strip at the bottom.
- **Footer collision / overlap** — no block crosses into the footer band and no two stacked
  blocks overlap. If one does, the cause is almost always a hand-picked `y` for an auto-growing
  callout/stack — fix it by switching to `bottom_callout()` / `vstack()` / `content_band()`, not
  a one-off coordinate nudge (that just recurs when the text changes).
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
     - *Low-stakes* (research/lab meeting, work status update, teaching) → **one
       critic** is enough.
     - *High-stakes* (conference, academic job talk / faculty interview, thesis
       defense, exec/stakeholder/pitch) → dispatch a
       **panel of 2–3 critics in parallel with different lenses** (content/accuracy,
       design/layout, back-of-room audience), then **merge and de-dup** their findings —
       independent reviewers catch far more than one, in parallel at no extra
       wall-clock. **Scale the panel *within* high-stakes by length & scope, not just
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
       skips all of this** — one critic, one consent, unchanged.
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
- `scripts/deckkit.py` — import this; build helpers for both template & blank decks.
- `scripts/inspect_template.py` — print a template's layouts/placeholders/logos.
- `scripts/render_deck.py` — pptx → one PNG per slide for the verify + critic loop. The
  real, cross-platform implementation (macOS / Linux / WSL / native Windows): finds
  LibreOffice on PATH or in OS-specific install locations (incl. `C:\Program Files\…`),
  or set `SOFFICE`. `render_deck.sh` is a thin bash shim that forwards to it.
- `scripts/lint_deck.py` — deterministic layout lint on a built `.pptx`: flags off-slide
  overflow, solid block/image overlaps (neither contained — ignores intentional layering), and
  footer collisions. Run after rendering, before the critic; exits non-zero on findings.
- `scripts/check_env.py` — one-time preflight; verifies LibreOffice + python deps and
  prints the exact fix for anything missing. Run it if a render ever fails. `check_env.sh`
  is a thin bash shim that forwards to it. On native Windows run the `.py` directly.
- `scripts/install_skill.py` — terminal installer/import helper; copies this skill into
  `~/.codex/skills/slide-maker`, `~/.claude/skills/slide-maker`, or both.
- `requirements.txt` — Python package dependencies for terminal use; install with
  `python -m pip install -r requirements.txt` if `check_env.py` reports missing modules.
- `scripts/anim.py` — inject purposeful PowerPoint builds/animations (click-reveal,
  fade) that python-pptx can't; pair with `references/animation.md`.
- `scripts/designed_charts.py` — the "designed plots" roster (donut+KPI, dumbbell, slope,
  dual-axis, bubble+trend, Pareto) — themed, single-highlight matplotlib recipes beyond default
  bars (raster PNGs; pass `font=` for CJK); pair with `references/data-viz.md`.
- `deckkit.native_chart` / `native_dual_axis` / `native_donut` / `native_pareto` / `native_bubble` —
  **editable** native PowerPoint charts (line/column/bar, two-scale dual-axis, doughnut+KPI, Pareto,
  bubble; slope = a 2-point line): click-to-edit, **any-language-safe (no tofu)**. Prefer over the
  raster `designed_charts` for non-Latin decks or when the user will edit the chart — `designed_charts`
  is then only for dumbbell or a deliberate matplotlib look (`references/data-viz.md`).
- `scripts/presets.py` — named **design-language presets** (`preset("glassmorphism"|"swiss"|
  "editorial_paper"|"editorial_report"|"risograph"|"memphis")`): one switch returns a coherent
  palette + fonts + surface treatment + image-prompt style. Starting languages, not straitjackets.
- `scripts/assemble.py` — assemble a large deck from parallel-authored section modules
  into one file (robust, no .pptx merge); pair with `references/large-deck-orchestration.md`.
- `scripts/archetypes.py` — build the same representative slides (cover/bullets/diagram/
  data) for each candidate direction, for collaborative mode's direction gate.
- `scripts/image_prompts.py` — create text-free image generation prompt manifests and
  expected filenames for optional slide visual plates.
- `scripts/generate_images_codex.py` — **no-API-key** image generation (the default outside a
  native-imagegen host; inside Codex, prefer the native imagegen tool call): shells out to `codex exec` (the hosted `image_generation` tool), decodes the
  image from the Codex session rollout, and writes the manifest's `slide-XX.png` files. Auto-detected
  when `codex` is installed/logged-in; prompts are passed verbatim. **No key, no per-image cost.**
- `scripts/generate_images_openai.py` — **fallback** OpenAI Images API path (only when neither native
  imagegen nor `codex` is available): reads `image_prompt_manifest.json` and writes `slide-XX.png`
  when `OPENAI_API_KEY` is set. Same manifest + flags as the Codex script.
- `scripts/extract_deck.py` — pull text/tables/figures OUT of an existing deck (the
  redesign path), so a rebuild reuses the user's real content and figures.
- `scripts/extract_pdf.py` — pull a figure OUT of a source PDF/paper as a clean PNG.
  **`figures`/`figure`/`autofig` auto-detect and crop figures precisely from the paper**
  (caption-anchored + snap-to-content, with `⚠ CHECK` flags) — the primary "crop from the
  paper" path; `page`/`crop`/`images` are the manual fallback.
- `scripts/crop_helper.py` — work on an image *by looking, not guessing*: `grid` overlays a
  labelled ruler to read a crop box off, `crop` (`--snap`) cuts it, `trim` snaps any image to
  its content (removes background, never clips a legend/axis — light or dark bg), and `panel`
  reassembles chosen columns/rows out of a dense comparison grid (keeping headers + labels).
- `scripts/export_notes.py` — export a deck's speaker notes to a plain-text rehearsal
  script (`python scripts/export_notes.py deck.pptx`); offer it at hand-off.
- `agents/content-planner.md` — the constructive planner's brief: understand the material
  deeply (or web-research when there's none), then design the narrative arc + a build-ready
  per-slide plan (takeaway, content, visual source, layout, motion, proposed image with a
  purpose-derived style). Dispatched in Step 1; its plan is the Step 3 checkpoint.
- `agents/critic.md` — the independent critic's brief + output JSON schema.
- `agents/arbiter.md` — the independent finding-arbiter's brief + per-finding verdict
  JSON; high-stakes cross-validation of critic findings before the actor acts, plus
  fix-verification on re-render. A no-op for low-stakes decks.
- `agents/openai.yaml` — Codex-facing display metadata and default prompt for installed
  skill lists/chips.
- `references/design-principles.md` — the craft / the "why".
- `references/review-rubrics.md` — universal + per-purpose review criteria.
- `references/style-analysis.md` — how to study & reproduce a style example (Q4).
- `references/design-by-purpose.md` — per-purpose design language for the
  "design a clean one" branch (palette/density/layout/chrome tuned to the purpose).
- `references/image-generation.md` — when and how to use native imagegen for optional
  text-free visual plates without compromising source fidelity or editability.
- `references/data-viz.md` — designed plots: pick the chart TYPE per argument (donut+KPI,
  dumbbell, slope, dual-axis, bubble+trend, Pareto), themed + single-highlight + a "so-what"
  rail; the `designed_charts.py` recipes + the `scorecard`/`leaderboard`/`takeaway_rail` furniture.
- `references/generated-template.md` — Q1's **"generate a template with an image tool"** branch:
  mini-interview → generate a text-free hero/divider illustration → derive a matching `style.py`
  (palette via `palette_from_image`, motif + component helpers) → feedback gate → skip the
  direction gate → build content natively so blocks fit the generated look; save to the registry.
- `references/font-guidance.md` — pick portable fonts, avoid tofu, recover from missing
  fonts; brand-font and CJK pointers.
- `references/animation.md` — when/why to animate, craft rules, and how to add
  purposeful click-builds with `scripts/anim.py`.
- `references/large-deck-orchestration.md` — when/how to parallelize a big deck by
  section (shared style module + assembly + critic panel); the default is single-author.
- `references/collaborative-mode.md` — the opt-in, checkpoint-gated mode (direction →
  outline → draft); pair with `scripts/archetypes.py`.
- `references/multilingual.md` — non-Latin decks (CJK fonts via `deckkit.EAFONT`,
  CJK typography, portability, RTL limits).
- `references/examples/style_example.py`, `section_example.py` — the shared-style +
  section-module convention for the fan-out path.
- `references/redesign-existing-deck.md` — the redesign path: diagnose the user's own
  deck first, confirm scope, then rebuild reusing their content/figures.
- `references/handoff-and-iteration.md` — what to tell the user at delivery (the deck is
  editable; the build script is the source of truth) and how to iterate after delivery
  WITHOUT overwriting their manual edits.
- `references/examples/build_example_generic.py` — a brand-free worked build script.
- `~/.codex/slide-templates/` / `~/.claude/slide-templates/` — the **user's** personal
  template registry for Codex / Claude Code respectively (NOT part of this skill); read it
  for template choices, write new profiles to the active host's registry. Empty for a new user.
