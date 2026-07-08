# Animation — purposeful builds that guide the audience

**🔴 Builds are the USER's opt-in choice — whether to animate at all is theirs, not the skill's
default.** The interview asks it on presented decks (Step 0); a self-read / poster deck is static by
design (no one clicks it), so it is never asked and never animated. This file is about how to build
WELL *once the user has opted in* — and where to place builds within an opted-in deck (that WHERE is
the skill's call). If the user opted out, the deck is static and correct; don't manufacture builds.

Animation is a tool for **controlling attention and pace**, not decoration. In a
live talk the audience reads the whole slide the instant it appears — often racing
ahead of the speaker. A *build* (revealing one piece at a time on click) keeps them
with you: each click introduces the next idea exactly when you say it, and leaves the
previous pieces on screen as the picture accumulates. That's the legitimate use.
Flying, spinning, bouncing text is the opposite — it pulls attention to the motion
instead of the meaning. The bar: **if an animation doesn't help the audience
understand or follow, cut it.**

> **🔴 FULL STAGED REVEAL — an animated slide reveals ALL its content, one beat at a time, in order.**
> The single most common build defect (the user has called it out): a slide where *some* blocks animate
> in while the *rest sit on screen from click 0* — a jarring half-animated slide. The rule: once a slide
> gets a build, **every content element on it is assigned to a step**, revealed in a deliberate reading
> order; the only things visible at click 0 are the **persistent scaffold** — the title/header + any
> frame, axes, or always-true context the beats land on. If a block isn't worth its own step, it still
> joins a neighbouring step (group one thought's shapes together) — it does NOT get left pre-shown.
> "Animate this slide" therefore means "stage this whole slide," never "animate a couple of its pieces."

`scripts/anim.py` makes this real (python-pptx has no animation API; it injects the
slide's `<p:timing>` XML). The model: draw your static base, then wrap each
reveal-on-click chunk in a build step.

**The bread-and-butter build = reveal bullets / blocks ONE BY ONE ("appear").** This is the
animation to reach for by default on a content slide with several points or blocks: each click brings
in the next bullet/card/stage as you talk to it, so the audience isn't reading point 4 while you're on
point 1. It's done by putting **each item in its own `step()`** (deckkit draws each bullet as its own
shapes, so one `bullet()` call per item works):
```python
from anim import Build
b = Build(s)
title_bar(s, "...")                       # static base — always visible
yb = 1.6
with b.step(): yb = bullet(s, 0.6, yb, 8.8, [("First point", "…")])   # click 1
with b.step(): yb = bullet(s, 0.6, yb, 8.8, [("Second point", "…")])  # click 2
with b.step(): yb = bullet(s, 0.6, yb, 8.8, [("Third point", "…")])   # click 3
with b.step(): bottom_callout(s, 0.6, 8.8, "TAKEAWAY", "…")           # click 4 — the punchline last
b.apply(effect="appear")                  # or "fade" for a soft one-by-one
```
`effect="appear"` (instant) or `"fade"` (soft) — both reveal one item per click; pick by taste. The
same pattern reveals **cards, pipeline stages, quadrant cells, or a final callout** one at a time. This
in-slide reveal — **not** a slide-to-slide transition — is what "add animation" means.

> **🔴 The static base must NOT pre-spoil what the build reveals.** Anything that **names, lists, or
> summarizes the to-be-revealed items** — a "four steps: A → B → C → D" caption, a recap line, a legend
> for blocks that appear one by one — must itself be **inside the build**, not in the always-visible base.
> The classic bug: drawing a summary line *after* `b.apply()` (or before the loop) so it's static — it
> then shows the whole answer at click 0 while the cards reveal one at a time, defeating the build. Two
> correct fixes: **(a) sync it** — break the summary so each fragment reveals *with* its block; or **(b)
> reveal it LAST** — wrap the summary in a final `b.step()` so it lands as the synthesis after every block
> is shown. Audit the **initial (pre-click) state**: it should give away *nothing* that a later click
> reveals. (Same logic as "build to a punchline" — the punchline can't already be on screen.)

## When a build genuinely helps
**Actively scan each (presented) slide's layout against this list** — animate the ones whose shape
fits, leave the rest plain. The recurring build-friendly layouts:
- **Step-by-step diagrams / pipelines (blocks joined by arrows).** Reveal each stage **and its
  arrow** on a click so you narrate the flow one box at a time, instead of dumping the whole diagram
  at once. *(A multi-block-with-arrows slide is the canonical signal to animate.)*
- **Progressive reasoning / multi-part points / a numbered list.** A slide making a 3-part argument:
  reveal each part as you reach it, so the audience isn't reading point 3 while you
  explain point 1.
- **Before → after / problem → solution.** Show the problem, let it land, then
  reveal the fix (or overlay the "after") on click.
- **Build to a punchline / takeaway.** Show the evidence first; reveal the takeaway
  callout last, after the setup is on screen.
- **Layered data.** Show a baseline, then reveal the comparison/annotation on top.
- **Quadrant / matrix · timeline · step-cards.** Reveal the cells, the nodes left-to-right, or the
  steps in order, so the structure assembles as you talk through it.

## Appear-by-content-type — the quick decision matrix
For a **presented** deck, map each slide's dominant content to this table, then build (or don't).
*(A **self-read / read-alone** deck has no presenter to click — it shows everything at once, so
ignore this table and leave such decks static; see SKILL.md "delivery mode".)*

| Content | Use appear? | Why |
|---|---|---|
| Bullet points | ✅ excellent | reveal one point as you discuss it |
| Step-by-step processes | ✅ excellent | keeps the audience on the current step |
| Flowcharts / pipelines | ✅ excellent | introduce components progressively (stage **+ its arrow** per click) |
| Equations | ✅ excellent | build a complex equation **term by term** |
| Diagrams | ✅ excellent | highlight one region / component at a time |
| Comparisons | ✅ good | reveal one side, then the other, for an easier compare |
| Tables | ⚠️ sometimes | only if you walk rows/columns **sequentially**; else show whole |
| Images | ⚠️ sometimes | only when pointing out **multiple regions** in turn |
| Large paragraphs | ❌ usually no | hard to read while text keeps appearing — show it at once |
| Simple titles | ❌ no | must be visible immediately |
| Reference / source lists | ❌ no | nothing to pace; the audience scans them |

The ✅ rows are the default build-candidates; the ❌ rows must appear **all at once** (animating a
title or a paragraph in is a *flaw*, not polish); the ⚠️ rows build **only** when you genuinely narrate
them piece-by-piece. Still **taste, not a quota** (next section) — the matrix says *what's eligible*,
your judgement says *whether this particular slide and moment need it*.

## Decide WHERE by taste and purpose — not by a rule or a quota
*(WHETHER the deck animates at all is the user's opt-in, above — this section is about where builds
fall **within a deck the user opted to animate**.)* Which slides build is a **design call**, the same for every purpose (research/lab
meeting, status update, conference, defense, exec, pitch, teaching): reach for a build where
your design sense says it will **emphasize** a point, make a slide **more engaging**, or
**guide the audience step by step** — and leave it off where it wouldn't. There is **no
count to hit in either direction.** It's completely fine for two or several *consecutive*
slides to build when the story wants that momentum, and equally fine for a long stretch to
be plain. Don't think in terms of "animate few" or "keep most static" — think in terms of
*what this slide and this moment need*. The failure to avoid is **thoughtlessness** in
either direction: reflexively animating every slide out of habit (motion that pulls the eye
off the meaning), and reflexively suppressing a build that would genuinely have helped.

## Where a build helps — and where a slide is simply plain
A build shines when stepping the reveal *emphasizes* or *guides*:
- **Pipelines / multi-stage diagrams** — reveal each stage (and its arrow) on a click.
- **Multi-part arguments** — reveal each part as you reach it.
- **Before → after / problem → solution** — let the problem land, then reveal the fix.
- **Build to a takeaway** — show the evidence, then reveal the takeaway last.
- **Layered data** — baseline first, then the comparison/annotation on top.

And some slides simply have nothing to pace, so they're plain — a title, a section divider,
a single one-idea slide, a side-by-side comparison the audience should scan all at once, a
dense leave-behind meant to be read. Leave those static not because of a rule, but because a
build there would add nothing. Never animate for flourish, for "consistency" with other
built slides, or to fill a slide that feels plain — fix the layout instead.

## Animated GIFs / looping results — insert the GIF, don't freeze it

### When a GIF earns its place — the decision (use it SPARINGLY)
**Core principle: a GIF only when *motion, progression, or interaction conveys information a static
image cannot.* Animation should REVEAL information, not decorate.** Most slides are static — a GIF is an
occasional, high-value exception (a deck usually has **zero or a few**, never one per slide; if every
other slide wants motion, you're decorating, not revealing). Run the checklist before planning one:
*does something actually change over time · is that change the point · would a single frame lose it ·
does the motion simplify rather than distract?* If any answer is no, use a static figure.
- **Strong fits** (motion is the content): **temporal/physical phenomena** (fluid flow, weather, a
  biological process, cine/4D/time-resolved), a **step-by-step process / algorithm / optimisation run**,
  a **progressive transformation** (reconstruction, image enhancement, deformation, a simulation
  converging), a **rotating 3D / spatial** structure (molecule, CAD, anatomy), a **UI / software / app
  demo loop**, a **cause-and-effect** sim (physics, circuit, mechanism), a **hidden internal mechanism**
  (packet flow, scheduling). Before/after and progressive data-viz (cluster/graph build-up) are weaker
  fits — a GIF helps only if the *transition itself* matters; else a static two-panel or final frame wins.
- **Keep STATIC** (a GIF adds nothing or distracts): concepts, relationships, **architecture / org
  diagrams**, **tables, equations**, **simple charts**, definitions, bullet lists, long text. Rule of
  thumb — static for *concepts / relationships / structure / data values*; GIF for *motion / process /
  interaction / temporal evolution / transformation / cause-and-effect / spatial exploration*.

When the result IS motion, **embed the GIF itself** — never extract one frame and show that. When the
*motion is the result*, a static frame discards what you're showing. This comes up across **every
kind of deck**: a product/UI demo loop or app walkthrough (pitch / product), an interaction or
worked animation (teaching), a looping data viz, a 4D / time-resolved / cine sequence, an
optimisation or training-run trajectory, a simulation, segmentation-over-time, or a rotating 3D
model (research / status / conference). Whenever the user hands you a GIF, treat it as live content,
not a still.

**Use `deckkit.gif()`** — a GIF-aware wrapper over `picture()`. It places the GIF **whole and
undistorted** (`fit="contain"` — a square cine clip is never stretched to 16:9; the original bytes are
embedded so every frame survives and **PowerPoint / Keynote loop it in slideshow**), sets alt-text,
**warns on a heavy file** (a big cine GIF bloats the `.pptx` and stutters live — palette-optimise /
downsample), and **warns if it's a single still** (use `picture()` then). Size and place it like any
figure — whole, on a grid, with a legible deck-font label.
```python
import deckkit as dk
L, R = dk.columns(2, slide=s)                 # GIF beside its quant panel — a balanced split
dk.gif(s, "results/cine_recon.gif", *R, alt="4D cine reconstruction, one cardiac cycle")
```

**No GIF yet, but the result is COMPUTABLE? Generate one with `deckkit.make_gif(frames, out, fps=…,
max_px=…)`** — the build-step companion that completes the loop **generate → embed (`gif()`) → review
(`gif_poster()`)**. Compute the frames in the deck's asset step exactly like the static figures (a
matplotlib animation, a simulation, a k-space fill, a denoising / training trajectory, a chart that
builds up) as PIL images / NumPy arrays / frame PNGs; `make_gif` stitches them into an optimised looping
GIF (shared palette; `max_px` caps the longest side to help keep the file under `gif()`'s `max_mb`).
**Time:** the encode is a second or two for a short clip — the real cost is computing the frames, so a
GIF slide fits the same compute-in-the-asset-step rhythm as a static figure, not a separate time sink.
Keep it modest (a few-second loop, ~10–15 fps, longest side ~720–960px). *(This is for one looping clip
embedded IN a slide; to narrate the WHOLE deck as a video, that's the separate `slides-to-video` skill.)*
```python
frames = [render_frame(t) for t in range(24)]      # your computed frames (PIL / ndarray / PNG path)
dk.make_gif(frames, "results/kspace_fill.gif", fps=12, max_px=900)
dk.gif(s, "results/kspace_fill.gif", *R, alt="k-space filling line by line")
```

### Make the FIRST frame representative — it's what everything-but-slideshow shows
A `.gif` loops only in **slideshow**. In the editor, in a **PDF/print export**, in the LibreOffice
render, and to the static critic, the GIF shows its **first frame** — and a GIF has no separate
poster frame (the first frame *is* the poster). A cine / 4D / training-run GIF that **starts on a
blank, black, or "loading" frame** therefore looks *broken* everywhere except live playback. So:
- **Check it:** `deckkit.gif_poster(path, "first.png", frame="first")` writes frame 0 — *view it*. If
  it's blank/unrepresentative, ask the user for (or regenerate) a GIF that **starts on a meaningful
  frame** (e.g. end-diastole for a cardiac loop, the trained state for a training run).
- **Give the critic a real still:** `gif_poster(path, "rep.png", frame="auto")` picks the
  highest-content frame — hand that to the critic / use it as a static fallback for a print export, so
  legibility is judged on a frame that actually shows the result, not the blank lead-in.
- **Fidelity (time-resolved data):** don't misrepresent the dynamics — don't drop frames that change
  the result's meaning or speed it up so a transient reads wrong. The loop must show what truly happens.

### Integrate it as content (not a floating clip) — CRAP still applies
- **GIF-as-hero:** when the loop is the slide's result, make it the **hero** (Contrast) — large, with
  an **assertion title** and a one-line **"what to watch"** caption pointing attention ("watch the
  artifact resolve", "ours = right panel"), exactly like a figure caption.
- **Beside its evidence:** pair the GIF with a static quant panel — a metrics table, a `scorecard`, a
  legend, or bullets — in a `columns(2)` split so the motion and the numbers read together.
- **Before/after & small multiples:** two GIFs side by side (baseline vs improved, two variants) loop
  together and make a moving comparison; a small grid of related loops (multiple views, runs, or cases)
  reads well for any audience — keep each whole and watch total file size.
- **Hand-off note:** tell the user the animation **plays in slideshow** (PowerPoint: Slide Show;
  Keynote: Play) and shows a still in edit/print — and that the first frame is what a PDF export uses.

## The slide-to-slide transition is SECONDARY — never a substitute for builds
> ⚠️ **The #1 animation mistake: slapping `slide_transition(s, "fade")` on every slide and calling it
> "animated."** A deck-wide fade is invisible polish at best — it does **nothing** to control attention
> or pace, it does **not** make bullets or blocks appear one at a time, and applying it reflexively to
> all slides is the *lazy* default to avoid. **It is NOT the animation that matters.** The animation that
> matters is the in-slide **appear/build** (the section above): revealing bullets/blocks **one by one**
> on click so the audience follows you. **Put your animation effort there, not into transitions.**

The slide-to-slide transition is a genuinely separate, *optional* choice — a subtle fade
(`slide_transition(s, "fade")`, ~0.4–0.5s) can add quiet continuity, but it is **off the critical
path**: a deck with **no** transition and good per-slide builds is far better than a deck with a fade
on every slide and no builds. So: decide it once, deliberately, and **don't treat "added fade
transitions" as having animated the deck** — that box is ticked by the appear-builds. If you do use a
transition keep it calm (fade/none, never cube/push/morph-everywhere), and record it in the motion
manifest as one line (`transition: fade` / `transition: none`) — distinct from the per-slide
`build:`/`static:` lines that carry the real work.

## Record a motion manifest (so the critic can judge what it can't see)
A static render — and the critic reviewing it — can't watch a reveal sequence. So as you
build, jot a one-line-per-slide **motion manifest**: `build: <what reveals, in order>` or
`static: <why this slide is plain>`, plus whether the deck-wide transition is on. Hand it to
the critic with the renders. It lets the critic judge the motion *design* it can't watch:
whether each build genuinely *emphasizes/guides* (and isn't thoughtless flourish), and
whether a slide that would clearly have been stronger with a build was left plain. It's a
record of your design choices, not a checklist quota. A comment block at the top of
`build_<deck>.py` is a perfectly good place to keep it.

## Craft rules
- **Default to a subtle fade**, ~0.4–0.6s. Avoid flashy entrances (fly/spin/bounce);
  they distract. `appear` (instant) is fine for simple stepping.
- **One idea per click.** Group the shapes that belong to a single beat into one
  step (e.g. a box *and* its arrow), so a click reveals a complete thought.
- **Keep the static scaffold visible.** Titles, axes, frames, the always-true
  context are drawn outside steps — only the *new* information animates in.
- **Start from an EMPTY content area — reveal from the *first* item.** Put **every** content beat inside
  a `step()`, the first one included, so the slide opens showing only the persistent scaffold and then
  fills in click by click. **"Empty" means the MAIN CONTENT region only — the page title / header (and
  any frame, axes, or always-true context) STAYS VISIBLE from the start and is never animated in.**
  Animating a title/header is itself a flaw — it must be readable the instant the slide appears; the
  reveal starts from the first *content* beat, not the title. The anti-pattern to avoid: drawing the
  first bullet / stage / card **outside** a step so it is already on screen when the slide appears — then
  the *content* doesn't *start empty*, it starts half-shown and only the later items animate. (Keep the
  always-true scaffold — title + minimal frame — visible; everything that is *content to be paced* begins
  hidden and accumulates under it.)
- **Builds add up, they don't replace.** Prefer entrance builds that accumulate the
  full picture; avoid exit animations that make earlier content vanish unless you
  have a strong reason.
- **A slide must survive without animation.** If it's printed, exported to PDF, or
  rendered statically, the fully-built state has to read correctly on its own. Never
  rely on motion to fix a cluttered slide — fix the layout.

## How to build it (with deckkit)
```python
from anim import Build, slide_transition

s = add_slide(prs)
title_bar(s, "From your question to a board that argues")  # static — always visible
footer(s, "...", page=4)

b = Build(s)
for i, (n, t, sub) in enumerate(steps):
    with b.step():                      # each click reveals one stage + its arrow
        chip(s, x, y, cw, ch, t, sub, ACCENTS[i % len(ACCENTS)])
        if i < len(steps) - 1:
            arrow(s, x + cw, y + ch/2, gap, 0.2)
with b.step():                          # final click: the takeaway
    callout(s, 0.7, 4.3, 8.6, 0.6, "TAKEAWAY", "...")

slide_transition(s, "fade")             # optional: a calm slide-to-slide transition
b.apply(effect="fade", duration=0.5)    # 'fade' (default) | 'appear' | 'wipe'
```
`Build.step()` records whatever deckkit shapes are drawn inside it (deckkit appends
shapes to the slide, so the recorder captures them automatically). `apply()` writes
the timing so each step appears on its own click, in order. Anything drawn *outside*
a step stays visible from the start.

## Verifying animation (important caveat)
`render_deck.sh` (LibreOffice → PNG) and the static-PNG critic show only the **final
built state** — they cannot play the sequence. So:
1. Make sure the fully-built PNG reads correctly on its own (run the normal render +
   critic loop on it as usual).
2. In your hand-off note to the user, **describe the build order** ("slide 4 builds
   the 4 stages on click, then the takeaway") so they can picture the sequence.
3. The anim.py timing itself is **verified**: real PowerPoint opens these decks and
   round-trips them into its *native* fade-on-click builds (a 5-click / 14-target test
   was preserved exactly), so the plumbing works — what you confirm per-deck is the
   *design* (does this build aid the talk), not whether the mechanism runs. LibreOffice
   simply can't *play* it (it ignores `<p:timing>`), which is why the render is
   final-state only.
The animation is an enhancement layer on top of an already-correct static slide —
never a substitute for getting the static slide right.
