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

Direction previews are an **HTML comparison page** — *one self-contained link* holding all
2–3 directions, which the user opens in a browser to review side-by-side and pick from. It's
fast (no LibreOffice round-trip) and shareable. The one risk of HTML is a *fidelity gap* to the
real pptx; close it two ways so "approve == ship" still holds: **(1)** drive the HTML and the
chosen `style.py` from the **same design tokens** (palette hexes, portable font families, motif)
so they can't drift, and **(2)** after the user picks, render **one real slide in the chosen
style** with deckkit / `render_deck` and confirm before the full build. The gate decides *taste/
direction*; the single real render confirms *fidelity*.

## The four gates (each cheap to change; expensive work deferred)

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
2. Capture each direction as a small **design-token object** (`name`, `rationale`, the
   palette hexes `bg/ink/grey/mute/line/light/accent` + an `accents` list, `font_display`,
   `font_body`, `density`) — and keep the **fonts portable** (Georgia, Arial/Helvetica,
   'Times New Roman', Consolas, Verdana — present on macOS+Windows) so the preview and the
   eventual pptx agree. This same token set seeds the chosen direction's `style.py` later, so
   there's **one source of truth** and no HTML→pptx drift. Write the 2–3 directions to a
   `directions.json` in a disposable `_directions/` subfolder of the deck folder.
3. Build the **one comparison link** with `python scripts/archetypes_html.py
   directions.json _directions/directions.html "Deck Title"`. It renders the **same four
   archetype slides per direction** — cover, bullets+callout, diagram pipeline, data/figure
   — into a single self-contained HTML page: same content, only the style differs, so the
   comparison is apples-to-apples and shows how the user's *real* slide types will look, not
   just a pretty cover. (The page already bakes in the instructions and the "describe your
   own — D" prompt.)
4. **Give the user the link** — the `file://…/directions.html` path to copy into a browser.
   Each direction has a **"Pick this one"** button (and a "D — describe your own" textarea); the
   page copies a short **paste-back line** to the clipboard — `I pick direction B — Keynote`, or
   `I pick D (my own): <text>` — which the user pastes back into chat (the page can't message the
   session). Parse that line for the choice. Also collect **knobs** — density
   (minimal/moderate/dense), accent colour, font pairing, light/dark.
   - **Always include a final "D — describe your own" option.** The shown directions are only
     your *opening proposals*; the author may have a look in their head you didn't guess. If
     they pick D, they **type their intention** — a reference deck/site, a brand, a mood, a
     colour, a constraint ("like our website", "warmer", "a serif on dark") — and you
     **synthesize a new direction token-set from that description**, regenerate the HTML link,
     and bring it back (step 5 loop). A blend ("B's palette with A's serif") is a valid D too.
     Never force one of your three.
   - *(Optional, when a host browser tool or headless Chrome is available, you may screenshot
     the page to show inline too — but the link is the deliverable the user reviews.)*
5. Apply knobs — or a "D" free-text intention — by editing the **token-set** and re-running
   `archetypes_html.py` (a tweak = change a constant + regenerate the page — cheap, instant,
   no LibreOffice) until the user consents.
6. On consent: **(a)** turn the chosen token-set into the deck's `style.py` (the standard
   style-module interface), then **render ONE real slide in it** (deckkit + `render_deck`) and
   confirm it matches what they picked — this closes the HTML→pptx fidelity gap before the
   costly build; **(b)** optionally persist it to the active template registry (profile.md +
   the style module) so it's a reusable registered template next time — collaborative mode
   *grows the registry*; then **(c) delete the throwaway preview artifacts** — the whole
   `_directions/` folder (`directions.json` + `directions.html`) and the *rejected* directions'
   token-sets — keeping only the chosen `style.py` (and the registry copy, if persisted). The
   previews were scaffolding for the choice; don't leave demo files littering the user's
   Downloads. Then continue to Gates B–D and build the **full** deck in the chosen style.

### Gate B — Content plan (the Step 1 CONTENT checkpoint)
This gate **is the content checkpoint surfaced as a gate** — present the **content-planner's**
work only: the deck's **arc** and the **per-slide takeaways** (the story, not the styling — no
thinner "outline"). Approve before any design or build work — this catches structural /
content-direction errors while they are cheapest to fix. Confirm scope here too ("9 slides —
this arc, proceed?").

### Gate C — Design plan (the Step 2 DESIGN checkpoint)
This gate **is the design checkpoint surfaced as a gate** — present the **slide-design** agent's
work: the **Design language** (the direction fixed at Gate A, now expanded into a full spec), the
**form ledger** + **rhythm**, the **per-slide design**, and the **image opt-in list**. Approve
before building all slides — this catches form / layout / motion direction errors before the
costly build. Confirm any scope shift here too ("9 slides in *Editorial* — proceed?").

### Gate D — Draft (the build + critic loop, Steps 4–5)
Build the **full** deck in the approved content + design plan — single-author by default, or
**section fan-out** for large decks (`large-deck-orchestration.md`) — then run the
**critic panel** and show the user. Iterate on their feedback as normal.

## Principles that keep it cheap and robust
- **Truthful previews via one source of truth:** the HTML link and the chosen `style.py`
  are driven by the **same design tokens** (palette/fonts/motif), and the chosen direction is
  **confirmed with one real pptx render** before the full build — so approve ≈ ship with the
  fidelity gap closed, not hand-waved.
- **Previews are disposable:** once the user picks, delete the `_directions/` folder
  (`directions.json` + `directions.html`) and the rejected token-sets — only the chosen
  `style.py` and the real deck survive. Clean up after the choice; never hand back a folder
  full of demo files alongside the deliverable.
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
