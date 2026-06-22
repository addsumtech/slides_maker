<p align="center">
  <img src="assets/cover.png" alt="slide-maker — design, redesign &amp; critique presentation-grade decks" width="100%">
</p>

<p align="center">
  <b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <a href="README.es.md">Español</a>
</p>

# slide-maker

> **Build, redesign, and critique presentation-grade `.pptx` decks** — for any audience, in any language, with or without a template or source material.

Most AI tools make slides the way they make text: in one shot, from a guess, without ever *looking* at what they produced. **slide-maker works like a senior presentation designer instead.** It asks what you actually need, stays strictly faithful to your source, and refuses to call a deck "done" until an *independent critic* has reviewed the rendered slides. What you get back is a real, editable PowerPoint file you own — not a screenshot, not a web app you're locked into.

One belief drives every decision: **a slide is a visual aid for a speaker, not a document to be read** — so everything optimizes for *understood in seconds*.

---

## Why it's different

Three quiet disciplines separate it from the usual ways of making slides:

- **It interviews before it builds.** Purpose, audience, source, style, language — gathered up front, never assumed. No more decks that confidently answer the wrong question.
- **It can't fabricate your work.** Every number, claim, and figure must trace back to your source; the single exception — forward-looking content — is flagged as the model's own addition. An expert audience spots an invented result instantly, so it doesn't invent them.
- **It checks its own pixels — with a second set of eyes.** `python-pptx` writes blind: overflow, contrast, and glyph bugs only appear once rendered. So every deck is rendered to images and an **independent critic subagent must consent** before hand-off. The builder doesn't get to mark its own homework.

### slide-maker vs. the usual ways to make slides

<sub>✓ yes&nbsp;&nbsp;·&nbsp;&nbsp;~ partial / depends&nbsp;&nbsp;·&nbsp;&nbsp;✗ no</sub>

| What you get | One-shot AI prompt | Web slide tools | By hand (PPT / `python-pptx`) | **slide-maker** |
|---|:--:|:--:|:--:|:--:|
| Asks your goal & audience *before* building | ✗ | ~ | ✓ | **✓** |
| Stays faithful to your source — no invented numbers | ~ | ~ | ✓ | **✓** |
| Uses your source's own figures & tables — auto-cropped from the PDF, not redrawn | ✗ | ✗ | ~ | **✓** |
| Optional generated visual plates for polish, kept text-free and non-evidentiary | ~ | ✓ | ~ | **✓** |
| Independent critic checks the **rendered** slides | ✗ | ✗ | ✗ | **✓** |
| Design tuned to the *purpose* (defense ≠ pitch ≠ lecture) | ~ | ~ | ✓ | **✓** |
| Real, editable `.pptx` you own — no lock-in | ~ | ~ | ✓ | **✓** |
| Any language — incl. CJK & real equation typography | ~ | ~ | ✓ | **✓** |
| Reproducible build + safe re-editing | ✗ | ~ | ✓ | **✓** |
| Fast to a *polished* deck | ~ | ✓ | ✗ | **✓** |

The others can all make slides. slide-maker is the one that **asks, stays faithful, and checks the result** — while still handing you a file you completely own.

---

## How it works — one disciplined loop

> **Interview → Understand → Build → Render &amp; critique ⟲ → Hand off**

Every deck flows through seven steps (`SKILL.md` is the authoritative spec):

| Step | What happens | Why it exists |
|---|---|---|
| **0 — Interview** | One compact interview turn: template, purpose & audience, source material, style. Structured choices when the host supports them; direct free-text prompts in plain Codex chat. | The user's requirements are the source of truth; you *learn* them, never inherit them from a prior deck. |
| **1 — Understand & plan** | A dispatched **content-planner agent** reads all source deeply (or web-researches + fact-checks when there's none), writes a **comprehension brief**, then designs the deck — this step plus Step 3 as one deep pass by one mind. | A deck that looks right but misreads the work fools no expert. Faithfulness starts here. |
| **2 — Canvas** | Decide output folder (`~/Downloads/<deck>/`), load template *or* design a purpose-fit look; set palette/fonts (incl. CJK `EAFONT`). | Branding lives on layouts; design should signal the right *kind* of document before a word is read. |
| **3 — Plan** | Per-slide spec (takeaway-first, content, visual source, layout, motion + image opt-in), one idea each, slide count ~1/min, arc shaped to the purpose; ~15+ → section fan-out. **The plan is shown for approval before building.** | Cheap to fix a plan; expensive to fix a finished deck. |
| **4 — Build** | One build script using `deckkit` helpers. Whole source figures, equal split panels (`columns`), optional text-free generated visual plates, gutters, rotating accents, real equations, one language, builds/animation and images by **taste & purpose** (emphasize / engage / guide — no quota), speaker notes. | python-pptx is fast; one script run, one coherent author. |
| **5 — Render + critic loop** | Render to PNGs and *look*; then an **independent critic subagent** returns JSON (consent / revise + per-slide fixes). Loop until consent. | python-pptx writes blind — overflow/contrast/glyph bugs only show in pixels. You are not the judge of your own work. |
| **6 — Hand off + iterate** | Show the user, give the folder path, explain editability + the two change-lanes, fold in feedback. | The deck is theirs to own and keep tweaking — safely. |

**The actor–critic loop is the quality engine.** Its *weight* scales to the stakes — one critic for a lab meeting, a 2–3-critic panel with different lenses for a conference, defense, or pitch — but the loop itself is never skipped. For **high-stakes** decks an independent **arbiter** pass then cross-validates the panel's findings before any fix (acting on a phantom flaw is as costly as missing a real one) and re-verifies them after the rebuild; low-stakes decks stay one critic, no arbiter.

### Two modes

- **Auto (default):** interview → build → critic loop to a high bar → show. The critic captures *quality*.
- **Collaborative (opt-in):** adds cheap **approval gates** — pick a *direction* from real rendered options → approve the *outline* → build the rest. The gates capture *preference* (taste), which a critic can't read. Designing from scratch, it shows you **3 distinct directions** — plus a *"describe your own"* — to choose from before it commits.

---

## What it can do

- **Build from anything — or nothing.** A paper, codebase, doc, or existing slides → a deck. No material? It drafts from expertise and **web-searches to ground and fact-check** every claim.
- **Uses your real figures and tables, precisely.** It pulls the source's own figures *and tables* **straight from the paper/PDF** — auto-detected by caption (handling figures-captioned-below and tables-captioned-above, even on one page) and cropped to the true extent (legend, axes, all columns intact; no caption or page-header bleed), shown *whole* rather than redrawn or chopped. A **post-render pixel self-check** catches a clipped edge or bled-in caption and auto-corrects it before the crop ships; dense comparison grids can be reassembled to just the columns that matter.
- **Can add generated visuals where they help.** For slides that need atmosphere, hero imagery, or conceptual polish rather than evidence, it can plan text-free image-generation prompts and place the selected assets reproducibly in the deck. In Codex it can use native imagegen; outside Codex it can use an optional OpenAI API helper with `OPENAI_API_KEY`. Real figures, charts, labels, and source evidence stay real and editable.
- **Redesign your existing deck.** It diagnoses first, confirms scope, then rebuilds reusing your content and figures — never a silent ground-up replacement.
- **Match a look you like.** Hand it an example and it reproduces the *style* — grid, palette, typography, motifs — in its own build.
- **Or generate a bespoke template with an image tool.** For a vivid, designed deck (a launch, an event, a brand deck), it generates a styled text-free hero/divider illustration, derives a matching palette + motif + component system from it, and **builds every content block natively to fit** — so the inserted cards, bullets, and badges read as part of the generated look, not pasted on.
- **Speak your audience's language.** Any language, held consistently throughout, with proper **CJK typography** and real **LaTeX-quality equations**.
- **Respect the venue.** For a conference talk it identifies and researches the venue — format, aspect ratio, official template, audience — before building.
- **Scale to big decks.** 15+ slides → optional section fan-out with a shared style, parallel authoring, and a critic panel.
- **Hand off cleanly.** A self-contained folder, speaker notes, purposeful animation, and a reproducible build script so you can keep editing safely.

---

## Try it

slide-maker is an **Agent Skill** — it runs in Claude Code and other Agent-Skills-compatible runtimes. You don't run commands to use it; you just **ask**, and the skill takes over (starting with the interview).

```bash
# 1. From this repo, install/import into both terminal runtimes
python scripts/install_skill.py --target both

# 2. One-time toolchain check (python-pptx, LibreOffice, matplotlib, …)
python ~/.codex/skills/slide-maker/scripts/check_env.py
python ~/.claude/skills/slide-maker/scripts/check_env.py

# 3. If Python packages are missing, install them for the same interpreter
python -m pip install -r ~/.codex/skills/slide-maker/requirements.txt
```

Then just ask your agent:

> *"Use $slide-maker to create one slide explaining our new architecture."*
> *"Make a 12-minute conference talk from paper.pdf."*
> *"My deck is too dense — redesign it."*
> *"A lecture on diffusion models, in 中文 — clean and diagram-heavy."*
> *"Turn this repo into an investor pitch."*

Your finished deck lands in `~/Downloads/<deck-name>/` — the `.pptx`, a `render/` of slide PNGs, and the build script that made it.

---

## Which path your request takes

The interview (step 0, Q3 especially) routes the request:

| The user wants… | Path |
|---|---|
| A deck from their code/paper/doc | Build path (steps 1–6), content branch |
| A deck with no material | Build path; draft from expertise + web-search to ground, confirm outline |
| To **improve their own** deck | **Redesign path** — diagnose first, confirm scope, rebuild reusing their content/figures (`references/redesign-existing-deck.md`) |
| A deck **looking like an example** | Style-mimic — write a style brief, reproduce the look (`references/style-analysis.md`) |
| A **generated, bespoke template** | Image-tool template — mini-interview → generate a styled hero/divider, derive a matching palette + components, build content natively to fit it (`references/generated-template.md`) |
| A **conference** talk | Identify + web-research the venue (rules, template, audience), then build to it |
| A **poster** | Scoped: single large canvas; craft rules hold but the skill is talk-tuned — confirm spec first |
| A **non-English / CJK** deck | Set `EAFONT`, one-language discipline, CJK typography (`references/multilingual.md`) |
| A **big** deck (15+ slides) | Optional section fan-out: shared `style.py`, parallel section authors, `assemble.py`, critic panel (`references/large-deck-orchestration.md`) |
| To **see options first** | Collaborative mode gates |
| **Changes after delivery** | Iterate safely — never clobber hand-edits (`references/handoff-and-iteration.md`) |

---

## Design principles baked into the skill

1. **Requirements over artifacts.** A template, an old deck, or the model's taste are *inputs*, not instructions. When they conflict with the stated requirement, the requirement wins.
2. **Strict fidelity.** Every claim/number/figure traces to the source. The one exception is clearly-flagged forward-looking content.
3. **Independent critique.** A separate agent judges the rendered pixels — its independence is what makes "consent" mean something.
4. **Parallelize gathering, never understanding.** Fan out reading/asset-prep; one mind holds the through-line.
5. **Purpose-fit design.** A defense, an exec readout, and a lecture should not look alike.
6. **One language, held throughout.**
7. **The script is the source of truth; the `.pptx` is an artifact.** Reproducible, and safe to iterate without losing the user's edits.

---

## Toolchain

`python-pptx`, `pymupdf` (render + figure extraction), `matplotlib` + `Pillow` (equations/charts/figure cropping), and LibreOffice (`soffice`) for rendering. Run `bash scripts/check_env.sh` once on a new machine; it prints the exact fix for anything missing.

<details>
<summary><b>Repository map</b> (for contributors)</summary>

**Spine**
- `SKILL.md` — the operating instructions the model follows (steps 0–6, the rules).

**Engine (`scripts/`)**
- `deckkit.py` — the build kit: text/shape/component helpers (`bullet`, `callout`, `chip`, `arrow`, `modbox`, `hrule`), layout helpers (`columns`/`rows` for equal split panels & stacks, plus **measure-then-place** primitives — `content_band`, `bottom_callout` (footer-safe, grows up), `vstack` (equal gaps, no overlap, errors on overflow), and the `measure_*` helpers — so collisions surface at build time, not in the render), `picture`, `palette` (distinct, contrast-checked category fills — no gray-as-category), equations (`eq_par`, `equation_png`), `speaker_notes`, contrast check, brand colours/fonts (incl. CJK `EAFONT`), template reuse (`open_template`, `content_slide`) and the no-template chrome (`blank_deck`, `title_bar`, `footer`). Also: **gradient+alpha fills** powering `glass_card`/`glow`/`scrim_overlay`/`offset_shadow` (glassmorphism, soft glows, graduated photo scrims, hard riso shadows); **data furniture** (`scorecard`, `leaderboard`, `takeaway_rail`); **layout patterns** (`editorial_header`, `big_numeral`, `stat_row`, `quadrant`, `hub_spoke`, `timeline`, `before_after`/`image_tab`/`photo_triptych`, `corner_frame`, `accent_one`); and **publication templates/chrome** (`cover`/`colophon`/`sources_page`, `part_eyebrow`/`page_marker`, `specimen_card`, `wireframe_grid`/`spec_list`, `photo_card`, `backdrop_motif`) — each applied dynamically by purpose. Import it; don't re-derive primitives.
- `install_skill.py` — terminal installer/import helper for Codex and Claude Code skill directories.
- `requirements.txt` — Python package dependencies for terminal use.
- `render_deck.sh` — `.pptx` → one PNG per slide (LibreOffice → PDF → PNG). Cross-platform; uses a private LibreOffice profile so parallel/coexisting renders don't collide.
- `lint_deck.py` — deterministic layout lint on a built `.pptx`: flags off-slide overflow, **text overflowing its card** (text taller than the card behind it), solid block/image overlaps (ignoring intentional layering), footer collisions, whole-page-image/editability, and orphan slides. Run after rendering, before the critic.
- `check_env.sh` — one-time preflight for the toolchain.
- `anim.py` — injects PowerPoint build/animation timing XML python-pptx can't write.
- `designed_charts.py` — the "designed plots" roster (donut+KPI, dumbbell, slope, dual-axis, bubble+trend, Pareto): themed, single-highlight matplotlib recipes beyond default bars; pair with `references/data-viz.md`.
- `presets.py` — named **design-language presets** (`glassmorphism`/`swiss`/`editorial_paper`/`editorial_report`/`risograph`/`memphis`): one switch returns a coherent palette + fonts + surface + image-prompt style.
- `assemble.py` — combine parallel-authored section modules into one deck (no fragile merge).
- `archetypes.py` — build the same preview slides per direction for the collaborative gate.
- `image_prompts.py` — create prompt manifests and expected filenames for optional text-free generated visual plates.
- `generate_images_openai.py` — optional OpenAI Images API path: reads `image_prompt_manifest.json` and writes `slide-XX.png` files when `OPENAI_API_KEY` is set.
- `generate_images_codex.py` — **no-API-key** image generation (the default outside a native-imagegen host): shells out to `codex exec` (hosted `image_generation` tool), decodes the image from the Codex session rollout, and writes the same manifest's files. Auto-detected when `codex` is installed; the OpenAI API path is only a fallback.
- `inspect_template.py` — print a template's layouts/placeholders/logos.
- `extract_pdf.py` — pull a **figure or table** *out* of a source PDF: `figures`/`figure`/`autofig` **auto-detect and crop them precisely from the paper** (per-kind caption convention so figures-below and tables-above both localise; snap-to-content; page chrome — running heads/folios — excluded; a borderless-table text-bbox fallback; and a **post-render pixel self-check** that flags / auto-corrects a clipped edge or bled-in caption), plus manual page/region/embedded-image extraction.
- `crop_helper.py` — operate on an image *by looking, not guessing*: `grid` (ruler overlay), `crop`/`--snap`, `trim` (snap-to-content; removes background without clipping a legend/axis, light or dark bg), `panel` (reassemble chosen columns/rows of a dense comparison grid).
- `extract_deck.py` — pull text/tables/figures *out* of an existing deck (redesign + reconcile).
- `export_notes.py` — export a deck's speaker notes to a plain-text rehearsal script.

**Judgement**
- `agents/content-planner.md` — the constructive planner's brief: understand the material deeply (or web-research), then design the narrative arc + per-slide plan (content, layout, motion, purpose-styled images).
- `agents/critic.md` — the independent critic's brief + JSON schema.
- `agents/arbiter.md` — the independent finding-arbiter's brief: high-stakes cross-validation of critic findings before the actor acts, plus fix-verification on re-render. A no-op for low-stakes decks.
- `references/review-rubrics.md` — universal rubric + per-purpose overlays (research-grounded).
- `references/design-principles.md` — the craft and the "why."

**Per-scenario references**
- `design-by-purpose.md` · `data-viz.md` (designed plots — pick the chart per argument) · `image-generation.md` · `generated-template.md` (image-tool template branch) · `animation.md` · `multilingual.md` · `font-guidance.md` · `style-analysis.md` · `redesign-existing-deck.md` · `collaborative-mode.md` · `large-deck-orchestration.md` · `handoff-and-iteration.md`
- `examples/` — worked build script, the shared-style + section-module convention.

**External (not part of the skill)**
- `~/.codex/slide-templates/` / `~/.claude/slide-templates/` — the user's personal template registry for Codex / Claude Code; read for choices, write new profiles to the active host's registry. Empty for a new user.

</details>
