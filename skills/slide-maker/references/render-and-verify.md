# Render & verify — fast re-renders, render failures, the stats table, and the per-slide self-check (Step 5)

## Re-rendering fast (`--fast`)

**Iterating on a deck you already rendered? Add `--fast`.** `render_deck … --fast` fingerprints
every slide (its XML + rels + the bytes of the media it references, mixed with a deck-global digest
covering the theme/master/layouts/canvas size) against the previous run, then re-renders **only the
slides that changed** — it subsets the pptx to those slides, converts that, and overwrites just their
PNGs. Measured on an 18-slide deck: a full render is ~12s, a one-slide change is **~4.7s**, and a run
where nothing changed is **0.07s**. Output is byte-identical to a full render (verified), so the
critic and the render-time lint see exactly what they would have seen anyway. It falls back to a full
render — and says why — whenever the mapping could be wrong: slide count changed, every slide changed,
no cache, or the deck contains **auto slide-number fields** or **hidden slides** (LibreOffice drops
hidden slides from the PDF, so page N stops being slide N — a full render now warns loudly and
refuses to cache when the page count and slide count disagree). **Use it for the actor-critic fix rounds
and for post-delivery tweaks** ("change slide 7 to a chart"); use a plain full render for the first
render of a deck and whenever you pass `--deliverables`.

## Codex sandbox aborts — LibreOffice produces no PDF

**Codex sandbox note:** LibreOffice may abort or produce no PDF when launched inside a managed
sandbox even though `check_env.py` passes; in that case rerun only the render command with elevated /
unsandboxed execution, then continue the normal render -> lint -> critic loop. This is an environment
permission issue, not evidence that the deck is malformed.

## The DECK STATS block and its `[stats]` warnings

**It then prints a DECK STATS block — the measured form of the design targets. READ it, don't skim
past it** (pass `--selfread` for a read-alone deck — it raises the TEXT WALL budget (~40→~90 words)
and drops the presented-only SMALL TYPE / NO BUILDS warns; the other warns are mode-independent —
`--surface` for a poster/single-canvas artifact, `--textheavy` when the user explicitly chose
text-heavy density for a presented deck, or `--static` on a presented deck when the user opted OUT of
appear-builds (silences NO BUILDS — a static presented deck was their choice, not an omission), so the
budgets fit the delivery mode). Per slide it measures:
reading **load** (latin words + CJK chars/2) vs the ~40-word presented budget · **text% / ink%
coverage** vs the ~50–70% whitespace target · **max font pt** · shape/picture/chart counts ·
**build** presence · **sim↑** (layout-skeleton similarity vs the previous slide); deck-wide it
prints the **font histogram + type-drama ratio** and **builds/transitions n/N**. Its `[stats]`
warnings name the rule they measure — **`TEXT WALL`** (word budget blown → cut copy to notes or
split), **`CROWDED`** (occupancy past ~70% — role bands: cover 25–35 · exec 45–60 · technical 55–70 →
subtract or split, don't shrink), **`LAYOUT SAMENESS`**
(3 consecutive slides share one skeleton → the §1.2 skeleton-rotation rule failed), **`FLAT TYPE`**
(no typographic hero → the type-scale drama rule failed), **`SMALL TYPE`** (body-median under the
canvas-relative ≈18pt-equivalent floor → fewer words, bigger type), **`SIZE SPRAWL`** (>3–4 font sizes
on one slide → use the declared type-scale tokens), **`NO BUILDS`** (presented deck with no
appear-builds → the motion manifest failed *unless the user opted out of builds* — then pass
`--static`), **`SKELETON VARIETY`** (<4 distinct layout skeletons
across an 8+-slide deck → the canvas architecture barely rotates), **`TIMID COVER`** (slide 1's
largest run under 2× body → the cover lacks poster scale), **`FLAT RHYTHM`** (when render PNGs are
present via `--renders`/`./render`: no light/dark or colour-temperature event across the deck → the
rhythm map's Background-mode column is single-note), and on CJK decks **`CJK TIGHT LEADING`** (multi-line
CJK at ≤ single spacing → use the script-aware default) and **`CJK-LATIN SPACING`** (both 盘古之白
conventions mixed → pick one deck-wide). Treat each `[stats]` warning as the NAMED design rule
having failed measurably: fix it or write one clause of why this deck is the exception, and **paste
the stats block into the critic's input** so the judges score numbers, not impressions. It's a safety
net for the no-overlap / fits-its-box / density / rhythm rules, **not** a
replacement for looking (it can't judge crop, balance, legibility, or fidelity).

## Render self-check — the per-slide pixel scan

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
- **Hero numerals read clean** — an **integral number stays on ONE line** (no "2026" broken into
  "202"/"6" — use `wrap=False` or a wide-enough box); digits are **uniform-height & baseline-aligned**
  (a lining-figure face — Helvetica Neue / Arial / Cambria — NOT an old-style-figure face like Georgia,
  whose digits sit at different heights); and a numeral run **aligns** with adjacent CJK/Latin on its
  line (`design-principles.md` "Big numbers", `font-guidance.md`).
- **Chart axis spans every bar; a cumulative doesn't double-count** — a bar/waterfall/dot chart's
  baseline/value-axis runs under **all** its bars (not stopping short of the last one), and a
  cumulative/waterfall shows increments *or* their total, never both as peer bars (a "+8 / +8.3 /
  +16.3" trio is a double-count); keep different quantity kinds in separate stacks. Prefer
  `designed_charts.waterfall` over hand-rolled floating boxes (`design-principles.md` "Designed plots").
- **Geometry matches the number** — read one bar/band/cell's *size or colour* against its *printed
  value*: a magnitude column/bar starts at **0** (a cropped axis makes 210/220/230 read as a ~3×
  cliff); a proportional shape (funnel band, bubble) is sized to `value/max`, not clamped up by a
  min-size floor that contradicts its label; a diverging/signed scale reads its **sign** (a true 0
  is neutral, not blue). deckkit defaults handle all three — flag any hand-rolled/matplotlib chart
  that doesn't (`data-viz.md` "Chart anti-patterns", `design-principles.md` "Designed plots").
- **Formula sized to content** — every equation's glyphs read at ≈ **body size** (not blown up to fill
  the slide width, not illegibly shrunk), and **consistent across slides** (same placed height); any
  inline variable/symbol is in **math format** (italic, real sub/superscript), never plain body letters
  or Unicode super/subscripts.
- **No rule/divider crossing text** — every hairline, divider and accent bar passes BETWEEN blocks,
  never through one. The build-time `RULE_THROUGH_TEXT` gate catches this deterministically now; if you
  see one in a render it means the rule was drawn at a hand-picked `y` computed from how long the text
  happened to be at the time. Fix the *derivation*, not the coordinate.
- **Footer collision / overlap** — no block crosses into the footer band and no two stacked
  blocks overlap. If one does, the cause is almost always a hand-picked `y` for an auto-growing
  callout/stack — fix it by switching to `bottom_callout()` / `vstack()` / `content_band()`, not
  a one-off coordinate nudge (that just recurs when the text changes). **Look specifically at the
  seam where content meets a bottom callout/bar:** a *wide* bar grazing the cards above it by even
  a sliver clips their rounded corners — there must be a visible gap, so size content to the
  callout's returned top minus a `GUTTER` (reserve its space before sizing content, don't add it last).
- **Adjacent / stacked blocks — a VISIBLE gap, not a sliver** — between any two same-axis blocks
  (stacked panels, side-by-side cards, pipeline nodes) the gap must read clearly: **≥ ~0.13in
  (~⅓ `GUTTER`)**. A ~0.02in seam (three panels at pitch 1.04 with height 1.02) reads as touching —
  a gap far smaller than the slide's own margins looks cramped even though nothing overlaps. Cause:
  a hand-picked pitch that nearly equals the block height. Fix: **derive the pitch from the region** —
  `rows(n)` / `vstack(..., bottom=…)` — so the gap is set by construction, never `block_h + 0.02`.
  (The build-time lint's `SLIVER_GAP` warn catches this class deterministically — an unaddressed
  one at render time means the build-time report was skipped.)
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
  full-width, for a centred mark on a CJK deck). **A connector / loop label (e.g. a feedback-loop's
  「修订」/「retry」) sits in the OPEN GAP next to the line — offset above a horizontal segment, or beside a
  vertical one, with clearance — NOT inside an opaque chip that STANDS OUT over the line.** A chip that
  contrasts with the slide reads as a band-aid; route the label into clear space so the line and text
  simply don't collide. (On a PLAIN background a label that knocks the line OUT in the background colour —
  the line breaking cleanly for the text — is fine; the band-aid is a *visible* chip, e.g. a white block on
  a coloured/textured slide. Add a subtle *translucent* backing only if the label must cross a busy area.
  See `references/design-principles.md` → "Connector labels".)
- **Block colours** — in a sequence of chips/cards/stages, every block is a **distinct,
  deliberately-contrasted hue**: no two adjacent blocks share a colour, and **no neutral gray
  sits in the sequence as if it were a category** (use `palette()` — it warns on both). A vivid
  block beside a gray one reads as half-finished.
- **Mark-on-fill contrast — an icon glyph on its tile, a symbol/number on a coloured chip** — the
  mark must stand out from the ground it sits ON (~3:1), not just from the slide. Zoom each icon tile:
  a **same-hue pair** (teal glyph on aqua tile) or a **dark-on-dark pair** (coloured glyph on
  near-black tile) is invisible — the exact bug a mid-tone tile hides. `icon_tile` auto-guards this
  (white/near-white glyph on a deep tile, or deep glyph on a pale tile); a hand-placed icon-on-`box`
  does not, so check it here.
- **Titles** — a subtitle/definition line has a clear gap below the title's accent rule; the
  kicker/eyebrow adds a section label, it doesn't echo a word the title already leads with. **The
  title CHROME itself is not one fixed template repeated on every slide** — an identical
  eyebrow + rule-under-the-title on all ~12 content slides is a template tell (creativity is a design
  metric, not just correctness). **`lint_deck.py` now backstops the most common case deterministically —
  `TITLE-RULE MONOCULTURE` fires when the same thin rule sits under the title at the same height on
  >60% of content slides** (a `head()`-style helper that stamps one treatment deck-wide is exactly how
  this regresses); the other treatments (tab/rail/ordinal) it can't measure stay on this self-check.
  Rotate **2–3 title treatments** across the deck (e.g. a classic
  accent-rule · an eyebrow in a filled tab/pill · a left vertical accent bar · a section ordinal ·
  a motif mark) so no two adjacent slides share the exact chrome and no single treatment dominates —
  the eyebrow-ornament analogue of the skeleton-rotation floor (`references/design-intelligence-addendum.md`).
  This does **not** fight the Repetition principle: the visual SYSTEM stays constant (same palette,
  type pairing, signature motif on every slide) — you rotate the *chrome treatment*, not the identity.
  That IS "repeat the system, vary the protagonist" (`references/design-principles.md` C.R.A.P.), not a
  license to make each title look unrelated.
- **Images** — the key **subject is whole, not cropped** (`contain` vs `cover`); a generated
  image of real things is **factually right** (relative size/proportion, count, colour); any
  **labels sit under the feature** they name. A **sourced photo is aesthetically usable**, not just
  subject-correct: reject an ugly / under-construction (cranes, scaffolding) / blurry / badly-lit /
  cluttered / unrepresentative shot — re-source, or generate a **declared-stylized illustration**
  instead (a beautiful accurate illustration beats an ugly real photo; `references/image-generation.md`
  aesthetic gate + the `searched, found but low-quality → generated, flagged illustrative` rung).
- **Text over an image (hero / photo / plate)** — read the title against the pixels behind it: **(a)**
  no image **line / edge / motif / frame-ornament crosses the glyphs** (a scrim only *dims* a bright
  Deco line — it stays visible; when the image carries linework where the title lands, cover it with a
  **near-opaque panel** α ≥ 0.88, a lower-third band or corner card filled to the canvas edge, never
  bleeding off-canvas); **(b)** every run — including a gold/tint **eyebrow** — clears ≥4.5:1 against
  what's actually behind it; **(c)** an **unmistakable gap** separates the big title from its
  subtitle/rule (a subtitle hugging the title's baseline reads as an error). Fix by strengthening the
  backing, moving the text to an empty region, or re-spacing — treat a title fighting the image as a
  real defect, like an overflow.
- **PDF figures cropped precisely** — for every figure pulled from a paper, zoom **each of the four
  edges** close-up (not a glance at the whole) and confirm: (a) none of the figure's own parts is
  clipped **or flush** (flush = cut); (b) no page text bled in (its caption, a neighbour's caption
  fragment, a running head, a page number, a stray body-text line); (c) the figure is
  **self-contained — its own x/y axis labels are present**, not silently replaced by a legend you
  added on the slide. The full element list + the plot-panel-bbox pitfall (the auto-detector's box
  excludes the axis titles/ticks/legend, so an eyeballed crop near it drops them) are under **“Never
  clip the figure's OWN parts”** in Step 4. A clipped, flush, or axis-label-missing crop is a real flaw, not a nitpick.
- **Motion & images by taste** — what's there earns its place (emphasises/engages/guides),
  nothing thoughtless; what's plain is fine.

## Native Windows entry points, and isolating one bad slide

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
one slide can't render, tell the user which and why. (Symptom → cause → fix tables:
`references/troubleshooting-faq.md` §5 for render failures, §3 for build tracebacks.)

## If the deck uses animation/builds

**If you used animation/builds:** the render (and the critic) see only the **final
built state** — they can't play the sequence (the anim.py timing is verified to
round-trip through real PowerPoint as native builds; LibreOffice just can't *play* it).
So verify the fully-built PNG reads correctly on its own (run the loop as normal), and
in step 6 **describe the click order** to the user. Builds are a layer on a correct
static slide, never a fix for a cluttered one.
