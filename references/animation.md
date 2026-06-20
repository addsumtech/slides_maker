# Animation — purposeful builds that guide the audience

Animation is a tool for **controlling attention and pace**, not decoration. In a
live talk the audience reads the whole slide the instant it appears — often racing
ahead of the speaker. A *build* (revealing one piece at a time on click) keeps them
with you: each click introduces the next idea exactly when you say it, and leaves the
previous pieces on screen as the picture accumulates. That's the legitimate use.
Flying, spinning, bouncing text is the opposite — it pulls attention to the motion
instead of the meaning. The bar: **if an animation doesn't help the audience
understand or follow, cut it.**

`scripts/anim.py` makes this real (python-pptx has no animation API; it injects the
slide's `<p:timing>` XML). The model: draw your static base, then wrap each
reveal-on-click chunk in a build step.

## When a build genuinely helps
- **Step-by-step diagrams / pipelines.** Reveal each stage (and its arrow) on a
  click so you can narrate the flow one box at a time, instead of dumping the whole
  diagram at once.
- **Progressive reasoning / multi-part points.** A slide making a 3-part argument:
  reveal each part as you reach it, so the audience isn't reading point 3 while you
  explain point 1.
- **Before → after / problem → solution.** Show the problem, let it land, then
  reveal the fix (or overlay the "after") on click.
- **Build to a punchline / takeaway.** Show the evidence first; reveal the takeaway
  callout last, after the setup is on screen.
- **Layered data.** Show a baseline, then reveal the comparison/annotation on top.

## Consider it on every slide — but animate few; static is the default
What's a standard step for all purposes (research/lab meeting, status update, conference,
defense, exec, pitch, teaching) is the **consideration**: on every deck, scan each slide and
ask "would a purposeful build help here?" That is *not* a mandate to animate — for most
slides the honest answer is no, and they stay static. **Considering motion ≠ applying
motion.** What you scale across decks is whether you bother to *check*; what you do *not*
scale up is the number of slides that actually move. A deck where only two or three slides
build is a well-judged deck, not an under-animated one. Skipping the check on an "internal"
deck is the under-side failure; putting a build on every slide is the over-side failure —
and the over-side is the more common and more damaging one, because needless motion pulls
attention off the meaning.

## Default to static — animate only the clear cases
**Most individual slides have nothing to pace and should stay static — that is the expected,
correct outcome of the per-slide check, not a gap to fix.** Leave these static:
- Title, section, and simple one-idea slides.
- Dense reference / leave-behind decks meant to be read, not presented.
- Any slide where everything should be seen at once (e.g. a side-by-side comparison the
  audience scans together).
- Any slide where you cannot name *what understanding* a build would aid.

Only animate when a slide is one of the clear build cases above (pipeline, multi-part
argument, before→after, build-to-takeaway). **The test before you animate any slide: name
the specific comprehension aid the build provides. If you can't, drop it.** Never animate
for flourish, for "consistency" with other built slides, or to fill a slide that feels
plain — fix the layout instead.

## Animated GIFs / looping results — insert the GIF, don't freeze it
When a result is a GIF (a looping animation, a time-resolved/4D sequence, a training run),
**embed the GIF itself** — never extract one frame and show that. `add_picture` embeds the
real animated GIF (verified: GIF89a + all frames preserved, content-type image/gif), and
**PowerPoint and Keynote loop it automatically in slideshow**. For time-resolved /
dynamic results the *motion is the result* (e.g. a physics simulation over time, a
rotating 3D model, a before/after loop) — a static frame discards what you're showing.
```python
s.shapes.add_picture("results/demo_loop.gif", Inches(x), Inches(y), height=Inches(h))
```
- Size and place it like any figure (whole, with a legible deck-font label + takeaway).
- The render (LibreOffice → PNG) and the static critic see only the **first frame** — that
  is expected; the GIF still loops in the delivered `.pptx`. Tell the user in the hand-off
  that the animation plays in PowerPoint/Keynote.
- Two GIFs side by side (e.g. before vs after, baseline vs improved) makes a strong before/after that
  *moves* — both loop together.
- Keep file size sane: prefer the source GIF; if you generate one, palette-optimize it.

## The calm deck-wide transition is a separate, low-distraction choice
Separate from click-builds, a subtle **slide-to-slide transition** applied across the
whole deck (`slide_transition(s, "fade")` on each slide, ~0.4–0.5s) adds polish and
continuity without anyone noticing it. **This is *not* the "animation" that makes a deck
feel over-animated** — that's the per-slide builds above; a uniform fade is the one motion
that's fine to apply broadly. So it's a reasonable **default-on** choice — but applying it
deck-wide *or* omitting it for a static/print feel are both legitimate; just decide
deliberately and record the choice in the motion manifest. It's independent of builds:
use it on a deck whose individual slides are otherwise static, and combine it with
click-builds on the few slides that warrant them. Keep it calm (fade/none); avoid
theatrical transitions (cube, push, morph-everywhere).

## Record a motion manifest (so the critic can judge what it can't see)
A static render — and the critic reviewing it — can't watch a reveal sequence. So as you
build, jot a one-line-per-slide **motion manifest**: `build: <what reveals, in order>` or
`static: <why nothing to pace>`, plus whether the deck-wide transition is on. Hand it to the
critic with the renders. This is what makes "consider motion on every slide" *enforceable*:
the critic checks that a pacing decision was made (and flags a deck with no motion and
obvious build-candidates), rather than rubber-stamping a deck that simply never got the pass.
A comment block at the top of `build_<deck>.py` is a perfectly good place to keep it.

## Craft rules
- **Default to a subtle fade**, ~0.4–0.6s. Avoid flashy entrances (fly/spin/bounce);
  they distract. `appear` (instant) is fine for simple stepping.
- **One idea per click.** Group the shapes that belong to a single beat into one
  step (e.g. a box *and* its arrow), so a click reveals a complete thought.
- **Keep the static scaffold visible.** Titles, axes, frames, the always-true
  context are drawn outside steps — only the *new* information animates in.
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
