# Collaborative mode — opt-in, checkpoint-gated building

**Default is the standard checkpoint flow** (interview → 🔴 checkpoints → build → critic loop →
show). Collaborative mode is
**opt-in**: run it when the user asks to "see options/directions first", "let me check
before you build it all", wants to be involved, or for a brand-defining deck where the
*direction* is theirs to choose. Standard mode may **offer** it in one line
("want me to show you 2–3 directions first?") — but don't force it.

Why it's worth having: the critic loop optimizes toward *objectively good*, but it
can't read **preference**. Fixing direction at a cheap gate costs ~100× less than
after a finished deck. So collaborative mode front-loads the *subjective* calls behind
cheap approvals, then hands the bulk to the same engine as standard mode.

Direction previews are an **HTML comparison page** — *one self-contained link* holding all
2–4 directions, which the user opens in a browser to review side-by-side and pick from. It's
fast (no LibreOffice round-trip) and shareable. The one risk of HTML is a *fidelity gap* to the
real pptx; close it two ways so "approve == ship" still holds: **(1)** drive the HTML and the
chosen `style.py` from the **same design tokens** (palette hexes, portable font families, motif)
so they can't drift, and **(2)** after the user picks, render **one real slide in the chosen
style** with deckkit / `render_deck` and confirm before the full build. The gate decides *taste/
direction*; the single real render confirms *fidelity*.

## Table of contents
- The four gates (each cheap to change; expensive work deferred)
  - Gate A — Direction + archetypes
  - Gate B — Content plan (the Step 1 CONTENT checkpoint)
  - Gate C — Design plan (the Step 2 DESIGN checkpoint)
  - Gate D — Draft (the build + critic loop, Steps 4–5)
- Principles that keep it cheap and robust

## The four gates (each cheap to change; expensive work deferred)

### Gate A — Direction + archetypes
> **Note:** Gate A is no longer collaborative-mode-only — on the Q1(c) *design-a-clean-one*
> branch it runs BY DEFAULT (SKILL.md Q1(c); named carves there), because that is the one
> branch where the look is invented from nothing and the user has seen no options.
1. From the interview (purpose/audience/style) offer **differentiated directions** — distinct design
   *languages* (a named preset **or** a bespoke register invented for THIS content), never three shades
   of one idea. **Default: >=1 BESPOKE register invented for this topic, plus the best-fit REAL
   DESIGN LANGUAGES** for it — best-fit
   presets from the 18-preset library (read each preset's `when` field in `scripts/presets.py`) **and/or
   a bespoke register you invent when the content has a look of its own** — built into direction tokens
   with **`archetypes_html.preset_directions([names])`** (a bespoke direction is a **dict** in that list,
   carrying its OWN motif so it too renders real DNA, not just palette). "REAL STYLE" means *a language
   with its own motif* — a preset **or** a bespoke register both qualify; the thing being ruled out is
   three colourways of one layout, NOT synthesis itself.
   - **Presets are the FLOOR you beat, not the menu you satisfy.** The library exists so a rushed deck
     never looks defaulted — but whenever this content has a register the library doesn't quite reach
     (a subject with its own visual world — deep-sea sonar, a manuscript archive, a specific brand
     universe), **synthesising a bespoke direction is a first-class peer of preset-selection, weighed on
     every deck — not a fallback only for "a topic no preset fits".** A bespoke register that carries a
     named motif + palette + type + its own **guard** (register floor) + runs through all pages (item
     (q)) is as legitimate as any preset, and is often the stronger, more daring answer. The "describe
     your own" slot is the *user*-initiated path; this is the *agent*-initiated one — reach for it when
     the content earns it.
   - **The DNA runs through EVERY preview slide, not just the cover.** `preset_directions` marks each
     token with its `dna`; the cover shows the loud hero motif (`_dna_cover`) and every interior
     archetype slide carries a quiet **ambient register signature** (`_dna_ambient` — a corner mark,
     an edge rule, a faint grid/scanline). This is deliberate: a user reported a style that "只有
     首尾页" (lived only on the first/last page). The gate must SHOW the register carrying the whole
     deck, and the built `style.py` must do the same — see step 7 and `agents/slide-design.md`
     (register-signature self-verify).
   🔴 **The rule is PAIRWISE and checkable: any two directions must differ on ≥2 of
   {palette mood · type attitude · density/scale · COMPOSITION ENVELOPE}.** Light-vs-dark and
   warm-vs-cool are *knobs on one design*; the composition envelope — WHERE the ink sits — is the
   axis that makes two previews read as different decks before a word is read. When an axis is
   LOCKED (a brand accent, a mimic target), it leaves the divergence set and the ≥2 rule applies to
   what remains — a constraint relocates variance, it never licenses convergence. Each is
   grounded in `design-by-purpose.md` and named with a one-line rationale (e.g.
   *Editorial* — serif, airy, gravitas; *Keynote* — dark, high-contrast, energetic;
   *Corporate* — light, crisp, institutional). Each direction is a **style module** with
   the standard interface (see `references/examples/style_example.py`).
   - **How many — the count rule is set by whether an image tool is in play:**
     - *"design a clean one" / no image tool* (this gate's recommended-default home) → **4**
       rendered directions: **>=1 bespoke register + best-fit DNA presets** + **1 pure colour-scheme direction**
       (a tasteful palette+type combo for the topic, NO motif — the classic clean look, itself a
       legitimate style the user asked to keep on the menu). Build all four in one call —
       `preset_directions(["p1","p2","p3", {colour_token}])`, where the 4th arg is a **dict**
       passed through verbatim as a no-`dna` direction. Rendered as A/B/C/D; **describe-your-own is
       the next slot (E)** — the own-letter is dynamic in `build_directions_html`, so a 4th rendered
       direction never collides with it.
     - *"generate a template with an image tool"* → the look runs through Q1(d)'s **style gate**
       (generated-template.md), which shows **3** best-fit image-backed styles, not this HTML gate.
     - The lighter "unsure / brand-defining" opt-in offer → **2–3** is fine.
     Present the pick through the host's natural UI: structured choices when available, or a short
     direct question in plain chat.
2. Capture each direction as a small **design-token object** (`name`, `rationale`, the
   palette hexes `bg/ink/grey/mute/line/light/accent` + an `accents` list, `font_display`,
   `font_body`, `density`, **`cover`** (`centred | low-left | split-vertical | full-bleed-type`)
   and **`skeleton`** (the 8 canonical `statement | split | island | band | rail | dashboard |
   full-bleed | gallery` — five render faithfully, the other three map to a nearest representative
   FOR THE PREVIEW while the real token passes through unchanged) — the last two are the composition
   axis, and an unknown value is a hard error rather than a silent fallback, so the gate can never
   claim a composition it did not render. When a token comes from `preset_directions` it also carries
   a **`dna`** marker (the preset name) that drives the cover hero motif + the ambient register on
   every interior slide. Two dict cases matter for INVENTED directions: a **pure colour-scheme
   direction** simply omits any motif field (its consistency is palette+type); a **BESPOKE REGISTER**
   invented for the content supplies its OWN motif — **`cover_motif`** (raw, inline-styled HTML for the
   loud hero motif on the cover) and **`ambient_motif`** (the quiet register signature echoed on every
   interior slide) — so it renders real DNA and is a first-class peer of a preset, not a motif-less
   colourway. This is the mechanism that makes agent-invented bespoke a genuine gate option, not just a
   palette. Keep the **fonts portable** (Georgia, Arial/Helvetica, 'Times New Roman', Consolas, Verdana — present on
   macOS+Windows) so the preview and the eventual pptx agree. This same token set seeds the chosen
   direction's `style.py` later, so there's **one source of truth** and no HTML→pptx drift. Write the
   2–4 directions to a `directions.json` in a disposable `_directions/` subfolder of the deck folder.
3. 🔴 **Check the divergence mechanically BEFORE building the link:**
   `python3 scripts/directions_diversity.py directions.json`. Exit 2 means EITHER a pair matched on
   ≥3 of the four axes, OR the set contains no bespoke direction (at least one candidate must be a
   register invented for THIS topic, carrying its own `cover_motif`/`ambient_motif` — see
   `references/interview-protocol.md` Q1(c)). Read the output; `--json` separates `flagged` from
   `no_bespoke`. Either way: fix it, or keep it and record the reason on the checkpoint's
   `direction gate:` line. This is not distrust of the pick; it is that the agent writing the three
   directions and the agent judging their difference are the same mind, and that mind's failure
   mode is confident, well-argued sameness.
4. Build the **one comparison link** with `python3 scripts/archetypes_html.py
   directions.json _directions/directions.html "Deck Title"`. It renders the **same four
   archetype slides per direction** — cover, bullets+callout, diagram pipeline, data/figure
   — into a single self-contained HTML page: same content, only the style differs, so the
   comparison is apples-to-apples and shows how the user's *real* slide types will look, not
   just a pretty cover. (The page already bakes in the instructions and the "describe your
   own" prompt, which is auto-lettered to the slot AFTER the rendered directions — **D** on a 3-up
   gate, **E** on the 4-up no-image-tool gate.)
5. **Give the user the link** — the `file://…/directions.html` path to copy into a browser.
   Each direction has a **"Pick this one"** button (and a describe-your-own textarea); the
   page copies a short **paste-back line** to the clipboard — `I pick direction B — Keynote`, or
   `I pick <own-letter> (my own): <text>` — which the user pastes back into chat (the page can't
   message the session). Parse that line for the choice. Also collect **knobs** — density
   (minimal/moderate/dense), accent colour, font pairing, light/dark.
   - **Always include a final "describe your own" option** (the last, auto-lettered slot). The shown
     directions are only your *opening proposals*; the author may have a look in their head you
     didn't guess. If they pick it, they **type their intention** — a reference deck/site, a brand, a
     mood, a colour, a constraint ("like our website", "warmer", "a serif on dark") — and you
     **synthesize a new direction token-set from that description**, regenerate the HTML link, and
     bring it back (step 5 loop). A blend ("B's palette with A's serif") is a valid describe-your-own
     too.
     Never force one of your rendered directions.
   - *(Optional, when a host browser tool or headless Chrome is available, you may screenshot
     the page to show inline too — but the link is the deliverable the user reviews.)*
6. Apply knobs — or a describe-your-own free-text intention (the own-letter slot: **E** on the 4-up
   no-image-tool gate, D on a 3-up) — by editing the **token-set** and re-running
   `archetypes_html.py` (a tweak = change a constant + regenerate the page — cheap, instant,
   no LibreOffice) until the user consents.
7. On consent: **the pick fixes the REGISTER (palette · type · composition · the interior register
   signature), not the DARING — it is a launchpad, not a finished design.** The gate chose a
   *language*; the deck still has to say something in it. So the slide-design boldness/signature-move
   gate runs in full on the picked direction (`agents/slide-design.md` §1 + self-verify (h)/(k)): the
   deck still owes a `boldness` dial and one **`signature move` this preset would not have made** — a
   choice no template (or preset) would have. "Picked a preset → rendered the preset" does **not**
   discharge the design step; a deck that is a faithful preset with no bespoke move is a
   template-with-extra-steps and the critic's distinctiveness axis treats it as a finding. Then:
   **(a)** turn the chosen token-set into the deck's `style.py` (the standard
   style-module interface) — **including its COMPOSITION: the `cover` token is implemented as the
   style's cover composition** (the deck has ONE cover and the user chose its shape; a style.py
   that carries the palette but builds a default-centred cover has quietly discarded half the
   pick), **and the `skeleton` token is recorded at the top of `style.py` as
   `# composition: skeleton=<value> (rhythm-map plurality)` for the slide-design agent** — it
   becomes the rhythm map's PLURALITY skeleton (the most-used home base; the ≥4-distinct-skeletons
   rotation still holds — a direction's skeleton is its default, never a uniform). Then **render
   ONE real slide in it** (deckkit + `render_deck`) and
   confirm it matches what they picked — this closes the HTML→pptx fidelity gap before the
   costly build; **(b)** optionally persist it to the active template registry (profile.md +
   the style module) so it's a reusable registered template next time — collaborative mode
   *grows the registry* — **best done at hand-off (Step 6), after the critic loop, so the
   profile's Notes can carry what the vetted deck proved** (the Step-6 "save this look?"
   offer IS this persist — one save, one owner, on an explicit yes; the chosen `style.py`
   survives the (c) cleanup, so nothing is lost by deferring; `references/user-taste.md`
   §"Consented-look mining"); then **(c) delete the throwaway preview artifacts** — the whole
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
**form ledger** + **rhythm**, the **per-slide design**, and the **image opt-in list** (each row
carrying its source token per the REFERENT RULE, `references/image-generation.md`), plus the
**motif line** (device + meaning + how a stranger reads it), the **`boldness:` +
`signature move:` lines with the `carried_by:` slides** (the declared risk and where it does
structural work — the fields the critic's distinctiveness axis will later hold the deck to), the
branch's **gate line** (`direction gate:` with its `diversity:` verdict / `style gate:`) and — on any deck
that names a real entity, including a roster slide — the
**`logo plan:` line WITH its evidence token** (plus a roster slide's **`entity marks:`** line); Gate C shows the same fields as SKILL.md's
🔴 CHECKPOINT — DESIGN spec. Approve
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
- **Async fallback — split by how Gate A was triggered:** in *opt-in collaborative mode*, Gate A
  never hard-blocks — if the user goes quiet, pick the best-fit direction yourself and **flag it**
  (post the directions link + your pick, so they can veto later). But when Gate A runs as the
  *default direction gate on the Q1(c) design-clean branch* (SKILL.md), it is checkpoint-grade:
  silence does not waive it — post the link, state what you're waiting on, and stop (only the
  explicit per-deck AUTO WAIVER converts it to auto-pick + FYI). Gates B and C ARE the Step-1/Step-2 🔴
  checkpoints: silence does not waive a 🔴 stop (only an explicit per-deck "decide everything
  yourself" directive does — SKILL.md, "The per-deck AUTO WAIVER"). At B/C, post the compact
  checkpoint table (per the 🔴 CHECKPOINT convention), state in one line exactly what
  confirmation you're waiting on, and stop — do all still-possible non-committal prep (asset
  gathering) but build no slides past the gate.
- **Compose, don't fork:** collaborative mode reuses everything — the interview,
  `design-by-purpose.md`, the style-module + section machinery, the critic panel,
  `anim.py`. It only adds *approval gates*; the building engine is the same as standard mode.
