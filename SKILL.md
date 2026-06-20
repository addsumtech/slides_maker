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
  (`superpowers:dispatching-parallel-agents`.)
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
topic is the one place free text beats options) and offer only "provide a template" /
"design a clean one". Personalizing from a *returning* user's own materials is good and
encouraged; assuming a domain for someone who gave you nothing is the failure to avoid.

**Scale the interview to the ask:** a full deck needs
all four; a genuinely tiny ask (a single slide, a quick infographic) still needs purpose
and content confirmed, but you may collapse template/style to a sensible default *stated
in one line* ("I'll do a clean minimal look — say if you have a template") rather than a
full prompt. Scaling ≠ skipping — never infer purpose or content. Three answers trigger a quick follow-up *after* the
batch: *a conference talk* → ask which venue, then research it; *a new template* → they
hand over the file; *"design a clean one" (no template)* → offer the **direction gate**
(see Q1's design-one branch) — recommend showing **3** rendered style directions to pick
from before the full build. The four:

1. **Template / brand.** First **list this user's registered templates** — check the
   host-appropriate registry (`~/.codex/slide-templates/` in Codex, `~/.claude/slide-templates/`
   in Claude Code; if only one exists, use it). Each subfolder is one template they've used before,
   with a `profile.md`). Offer those as choices, **plus** "a new template (I'll
   provide one)" and "design a clean one." Then:
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

   **Never hardcode or assume a specific institution's template.** This skill ships
   to anyone: a brand-new user has an *empty* registry, so they see only "provide one"
   or "design a clean one" — no prior user's branding is ever offered to them.

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
   - *Moderate text* · *dense / detailed* (only for a read-alone leave-behind).
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
     never forced.** A *provided* template means the look is already decided — don't offer it.

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

## Step 1 — Get the content right (understand it deeply, don't skim)
A deck is only as good as your grasp of the material — a superficial read produces a
deck that *looks* right but misrepresents the work, which an expert audience spots
instantly. Read **all of it**, not the abstract: run the code's README, read the
paper end-to-end (intro → method → **every results table/figure** → conclusion).

Then **write down, before building, a comprehension brief** and sanity-check it:
- The **one-sentence message** (what the authors most want remembered).
- The **contributions**, in their words.
- The **method essence** at talk-altitude (+ the one key equation).
- For **each figure and table: what is it FOR?** What comparison does it make, and
  what does it *emphasize*? A table exists to make one comparison obvious — represent
  *that* comparison, not a different axis. (E.g. if a paper's point is "feature X
  helps", the table must foreground *baseline vs +X*, not invite an unrelated A-vs-B
  comparison — getting this wrong reveals you didn't understand the paper.)
- Any **nuance/limitation** the authors stress.

If you can't fill this in confidently, you haven't understood it yet — re-read or ask
the user. Build only once the brief is right; every slide must be faithful to the
authors' actual emphasis, not a plausible-sounding paraphrase. Reuse their figures
(relabel for the slide).

- **No content:** draft an outline from your own expertise, then **ground *and verify*
  it** with `WebSearch`/`WebFetch` — treat this as a **fact-check, not just framing**.
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
  Then confirm the outline with the user before building the full deck (cheaper to correct an
  outline than a finished deck).
  > **🔴 CHECKPOINT** — get the user's OK on the outline before building the full deck.

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
iterate without clobbering the user's manual edits.

- **Template branch:** run `scripts/inspect_template.py <file.pptx>` to learn the
  layout indices, placeholder ids, and where logos/brand live (they sit on the
  layouts, so new slides inherit them). Then `deckkit.open_template()` loads the
  deck and wipes old slides while keeping masters/layouts. Pull the brand colors
  from the template and set `deckkit` palette/`FONT` to match. Save what you learn as
  a `profile.md` under the active template registry so it's reusable next time
  (a registered template's `profile.md` is a fully worked example of this).
  - **Conference template:** if step 0 turned up an official conference template,
    download it (`WebFetch`/`curl`) and treat it exactly like a user template —
    inspect it, then build on it so the talk matches the venue's required look and
    aspect ratio.

- **No-template branch:** `deckkit.blank_deck()` + `deckkit.add_slide()`, and give
  it consistent chrome with `deckkit.title_bar()` / `deckkit.footer()`. **Don't just
  accept deckkit's default blue — design the look to fit the purpose.** Read
  `references/design-by-purpose.md` for a per-purpose design language (palette mood,
  density, layout, chrome) and set the `deckkit` palette constants + `FONT` to match,
  then do a quick web-search for current, well-regarded examples of *this kind* of
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

## Step 3 — Plan the deck (terse, purpose-shaped)
One idea per slide, in an arc that fits the purpose (a conference talk and a status
update are ordered differently — let the rubric guide you). **Scale the slide count to
the time budget** — roughly one slide per talking-minute as a loose anchor: a short talk
or status update runs ~6–9 slides; a longer lecture, thesis defense, or job talk ~10–20+.
Keep **one idea per slide** regardless — a longer deck means *more* slides, never a
denser one. At **~15+ slides**, consider the section fan-out (step 4) to keep a big deck
coherent. Write each slide's **takeaway** first; bullets are support, not the message.

Plan each slide's visual source before building: source figure, deterministic chart,
native diagram, generated visual plate, or **no image** (a clean, well-typeset slide
needs none). Generated plates are optional style support, not evidence.
**Use generated images with judgment, not by default — most decks need zero, and a plate
on *every* slide is the failure to avoid.** Decide per slide whether one earns its place:
add a generated plate only when a *specific* slide would otherwise feel visually thin and a
text-free, decorative/conceptual image genuinely helps — never reflexively, never one-per-
slide, and never when a source figure, a real generated artifact, a chart, or simply more
whitespace would serve better. When in doubt, leave the slide image-free. When they do earn
their place, use them for text-free hero imagery, atmosphere, side panels, textures,
conceptual scenes, and decorative motifs; do **not** use them for source figures, data
charts, medical/scientific evidence, screenshots, logos, or anything whose content must be
traceable. For generated plates, read `references/image-generation.md`
and create a prompt manifest with `scripts/image_prompts.py` so the selected images live
inside the deck folder and the build stays reproducible. In Codex, prefer the native
imagegen tool when available. Outside Codex, use `scripts/generate_images_openai.py` with
`OPENAI_API_KEY` as an optional API fallback, or ask the user to provide externally
generated images with the manifest filenames.

**Sanity-check pace against the clock.** After planning, compute `slide_count ÷
time_minutes`: well over ~1/min for a *spoken* talk means you'll overrun — cut slides or
get more time, and flag it to the user. Count an **animated/build slide once** (a 4-click
pipeline is one slide for pacing, not four). Read-alone decks (no speaker) aren't bound by
this.

## Step 4 — Build with deckkit
Write a small per-deck build script that imports `scripts/deckkit.py` rather than
re-deriving primitives. Helpers: `content_slide`/`title_bar` (a clear title),
`columns` (equal-width split panels with symmetric margins — use it for *any* left/right
or N-up layout so the two sides and their flanking white space come out the same width),
`picture` (place a figure/plate without distorting it — `fit="contain"` keeps edges,
`fit="cover"` crops to fill), `bullet`, `callout` (auto-grows to fit), `arrow`,
`chip` (pipelines), `modbox`,
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
  "rightmost column is Ours") — not to crop it down. Reach for cropping only to (a) **trim**
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
  with matplotlib, or for a publication-grade plot/table hand it to the **`paper-figures`**
  sibling skill — then place the result *whole*, with a legend + takeaway, like any other
  figure. A bare number table is the weakest way to show a trend.
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
- **Need atmosphere or a conceptual visual → use image generation deliberately, and
  sparingly.** This is a *per-slide judgment call, not a per-deck habit* — the same
  restraint as animation. Most slides (and many whole decks) need **no** generated image;
  reach for one only when a *specific* slide would otherwise feel visually thin **and** a
  decorative or conceptual image genuinely helps it — not to fill space, not on every slide,
  and not when a source figure, a real computed artifact, a chart, or plain whitespace would
  serve better. If you can't name what a plate adds to *that* slide, don't generate it. When
  one does earn its place and the missing image is decorative or
  conceptual rather than evidentiary, use the agent's image generation skill to create a
  **text-free visual plate**. Keep all slide words, numbers, labels, charts, equations,
  citations, UI copy, and logos as editable PowerPoint objects or real source assets. Run
  `scripts/image_prompts.py` from the deck outline to make prompts + expected filenames,
  generate/select the images with the native imagegen tool when available, or run
  `scripts/generate_images_openai.py <manifest>` when the user has configured
  `OPENAI_API_KEY`. Copy/keep the final assets in `~/Downloads/<deck>/assets/generated/`,
  and place them with `deckkit.picture(..., fit="cover", alt="")` for decorative plates or
  `fit="contain"` when edges must be preserved. Always render-check that generated imagery
  leaves calm space behind text and contains no accidental pseudo-text/fake charts. Full
  rules: `references/image-generation.md`.
- **Speaker notes — put the spoken script in the notes, not on the slide.** For any deck
  the user will *present* (especially a conference talk, defense, or lecture), move the
  full sentences off the slide into speaker notes with `deckkit.speaker_notes(slide, "…")`.
  The slide shows the phrase; the notes hold what the presenter says. Notes don't render
  (the critic won't see them) but they show in Presenter View and on printed Notes Pages —
  so the user can rehearse without the slide becoming a wall of text. Offer this at
  hand-off; it directly serves the "few words per point" rule.
- **Spacing.** Leave a `deckkit.GUTTER` (~0.4 in) gap between a figure and any text,
  callout, or edge — crowding looks amateur. Mind each page's overall layout.
- **Balanced split layouts — equal panels, equal margins.** When a slide is divided into
  left/right regions (text + figure, two-up comparison, image + caption) the two regions —
  *and the white margins flanking them* — should be the **same width** unless you have a
  deliberate reason otherwise. A left panel and right panel of different widths, or a wider
  white margin on one side than the other, is a lopsided-slide tell that reads as careless.
  Don't eyeball each panel's `x`/`w`; derive them from one grid with **`deckkit.columns(n)`**
  (it returns `n` equal-width rects with symmetric outer margins and equal gutters), then
  drop content into those rects. If you *intend* an asymmetric split (e.g. a 1/3 text rail
  beside a 2/3 figure), make it clearly intentional and keep the *outer* margins equal —
  and **re-view the render** to confirm the two sides look balanced, not accidentally uneven.
- **Colour.** Rotate `deckkit.ACCENTS` so diagrams aren't monotone; reserve magenta
  for emphasis. Name the closing slide for its purpose ("Conclusion" for a talk).
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

**Motion & builds — CONSIDER on every slide, ANIMATE only where it earns its place.**
What's required is the *consideration pass* (so a deck that obviously needed a step-by-step
build doesn't ship static because nobody looked) — **not** motion on every slide. The
default outcome of that pass is the opposite: **most slides stay static**, and a click-build
is the *exception* you add only when you can name the specific thing it helps the audience
follow. Animating reflexively — a build on every slide, motion for polish — is exactly the
failure to avoid; it pulls attention to the motion instead of the meaning. Two distinct
layers, decided separately:
- **The calm deck-wide transition** is a sensible, low-distraction default: a subtle
  `slide_transition(s, "fade")` (~0.4–0.5s) applied uniformly across the deck adds
  continuity without anyone noticing it. Apply it as the default *for the deck* (it is the
  one motion that's fine to apply broadly), or omit it for a static/print feel — either is a
  legitimate choice; just decide deliberately and record it. This is *not* the "animation"
  that makes a deck feel over-animated — that's the per-slide builds below.
- **Click-builds are per-slide, and the bar is high — static is the default.** Walk each
  slide and ask "would revealing this step by step genuinely help the audience *follow*?"
  For most slides the honest answer is no, and they stay static — **that is the expected,
  correct outcome, not a gap.** Add a build *only* for the clear cases: **pipelines /
  multi-stage diagrams** (one stage + its arrow per click), **multi-part arguments** (reveal
  each part as you reach it), **before→after / problem→solution**, and **build-to-takeaway**
  (evidence first, the takeaway callout last). Title / section / single-idea slides and
  side-by-side comparisons the audience scans together **should stay static**. The test
  before animating any slide: *name the comprehension aid the build provides* — if you can't,
  leave it static. The discipline is that you *considered* every slide, then animated *few*.

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
1. **Critique.** Dispatch an independent critic subagent (Agent tool) pointed at
   `agents/critic.md`, giving it the rendered PNGs, the deck's **purpose + audience**,
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
- `scripts/check_env.py` — one-time preflight; verifies LibreOffice + python deps and
  prints the exact fix for anything missing. Run it if a render ever fails. `check_env.sh`
  is a thin bash shim that forwards to it. On native Windows run the `.py` directly.
- `scripts/install_skill.py` — terminal installer/import helper; copies this skill into
  `~/.codex/skills/slide-maker`, `~/.claude/skills/slide-maker`, or both.
- `requirements.txt` — Python package dependencies for terminal use; install with
  `python -m pip install -r requirements.txt` if `check_env.py` reports missing modules.
- `scripts/anim.py` — inject purposeful PowerPoint builds/animations (click-reveal,
  fade) that python-pptx can't; pair with `references/animation.md`.
- `scripts/assemble.py` — assemble a large deck from parallel-authored section modules
  into one file (robust, no .pptx merge); pair with `references/large-deck-orchestration.md`.
- `scripts/archetypes.py` — build the same representative slides (cover/bullets/diagram/
  data) for each candidate direction, for collaborative mode's direction gate.
- `scripts/image_prompts.py` — create text-free image generation prompt manifests and
  expected filenames for optional slide visual plates.
- `scripts/generate_images_openai.py` — optional OpenAI Images API fallback that reads
  `image_prompt_manifest.json` and writes the selected `slide-XX.png` files when
  `OPENAI_API_KEY` is configured; native Codex imagegen remains preferred in Codex.
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
