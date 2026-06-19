# Collaborative mode — opt-in, checkpoint-gated building

**Default is auto** (interview → build → critic loop → show). Collaborative mode is
**opt-in**: run it when the user asks to "see options/directions first", "let me check
before you build it all", wants to be involved, or for a brand-defining deck where the
*direction* is theirs to choose. Auto mode may **offer** it in one line
("want me to show you 2–3 directions first?") — but don't force it.

Why it's worth having: the critic loop optimizes toward *objectively good*, but it
can't read **preference**. Fixing direction at a cheap gate costs ~100× less than
after a finished deck. So collaborative mode front-loads the *subjective* calls behind
cheap approvals, then hands the bulk to the same engine as auto mode.

Previews use the **real `pptx → PNG` renderer** (not HTML): what the user approves is
exactly what ships, and the chosen direction's style module *becomes* the deck's
`style.py`. (HTML mockups look slick but introduce a fidelity gap to the pptx — only
use them as a throwaway mood sketch, then confirm with a real rendered slide.)

## The three gates (each cheap to change; expensive work deferred)

### Gate A — Direction + archetypes
1. From the interview (purpose/audience/style) generate **differentiated directions** —
   distinct design *languages*, not three shades of one idea: vary the big axes
   (light/dark, warm/cool, serif/sans, restrained/bold) so the choice is real. Each is
   grounded in `design-by-purpose.md` and named with a one-line rationale (e.g.
   *Editorial* — serif, airy, gravitas; *Keynote* — dark, high-contrast, energetic;
   *Corporate* — light, crisp, institutional). Each direction is a **style module** with
   the standard interface (see `references/examples/style_example.py`).
   - **How many:** when this gate fires because the user chose **"design a clean one" /
     no template** (its recommended-default home), use **3** — the look is fully yours to
     invent, so a fuller spread earns the pick. For the lighter "unsure / brand-defining"
     opt-in offer, **2–3** is fine. Present the pick through the host's natural UI:
     structured choices when available, or a short direct question in plain chat.
2. For each, build the **same archetype slides** with `scripts/archetypes.py`
   (`build_archetypes(prs, S)` / `preview_direction(style_path, out)`): cover, a
   bullets+callout slide, a diagram slide, and a data/figure slide. Same content,
   only the style differs → an honest, apples-to-apples comparison that shows how the
   user's *real* slide types will look, not just a pretty cover.
   - **Render previews into a disposable location** — a `_directions/` subfolder of the
     deck folder (or a temp dir), each direction's style module + preview deck + render
     PNGs together — so the whole set can be removed in one step once the user picks (step 6).
3. **Run a quick critic on each preview first** (don't spend the user's attention on
   issues a critic would catch — show decent options).
4. Render all directions, present them (a contact sheet / the PNGs), and collect
   **structured feedback**: pick a direction, plus **knobs** —
   density (minimal/moderate/dense), accent colour, font pairing, light/dark.
   - **Always include a final "D — describe your own" option** beyond the rendered
     directions. The rendered options are only your *opening proposals*; the author may
     have a look in their head you didn't guess. If they pick D, they **type their
     intention** — a reference deck/site, a brand, a mood, a colour, a constraint ("like
     our website", "warmer", "a serif on dark") — and you **synthesize a new style module
     from that description**, render the same archetypes, and bring it back (step 5 loop).
     A blend ("B's palette with A's serif") is a valid D too. Never force one of your three.
5. Apply knobs — or a "D" free-text intention — by editing/creating the **style module**
   (a tweak = change a constant + re-render the archetypes — cheap) until the user consents.
6. On consent: **(a)** the chosen module becomes the deck's `style.py`; **(b)** optionally
   persist it to the active template registry (profile.md + the style module) so it's
   a reusable registered template next time — collaborative mode *grows the registry*; then
   **(c) delete the throwaway preview artifacts** — the whole `_directions/` preview folder
   (every direction's preview deck + render PNGs) and the *rejected* directions' style
   modules — keeping only the chosen `style.py` (and the registry copy, if persisted). The
   previews were scaffolding for the choice; don't leave demo decks littering the user's
   Downloads. Then continue to Gate B/C and build the **full** deck in the chosen style.

### Gate B — Outline
Present the slide-by-slide **takeaways / arc** (cheap text, from step 3 of the main
flow). Approve before building all slides — this catches structural/content-direction
errors before the costly build. Confirm scope here too ("9 slides in *Editorial* —
proceed?").

### Gate C — Draft (the existing step 6)
Build the **full** deck in the approved direction — single-author by default, or
**section fan-out** for large decks (`large-deck-orchestration.md`) — then run the
**critic panel** and show the user. Iterate on their feedback as normal.

## Principles that keep it cheap and robust
- **Truthful previews:** pptx-render, so approve == ship; the chosen style IS the
  build style. No translation step.
- **Previews are disposable:** once the user picks, delete the preview decks and the
  rejected modules — only the chosen `style.py` and the real deck survive. Clean up after
  the choice; never hand back a folder full of demo options alongside the deliverable.
- **Diff-based iteration:** freeze what the user approved; change only what they
  flagged; show before/after. Don't re-litigate settled gates.
- **Knobs over rebuilds:** parameterize the style module so visual tweaks re-render a
  few archetype slides, not the whole deck.
- **Critic at the gate:** previews shown to the user should already pass a quick
  critic — the human resolves *taste*, not bugs.
- **Async fallback:** if the user goes quiet, proceed in auto mode with best judgment
  and **flag every assumption** for later review — a gate should never hard-block.
- **Compose, don't fork:** collaborative mode reuses everything — the interview,
  `design-by-purpose.md`, the style-module + section machinery, the critic panel,
  `anim.py`. It only adds *approval gates*; the building engine is the same as auto.
