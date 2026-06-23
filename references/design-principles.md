# Design principles — why these slides look the way they do

These rules are tuned to the **default deck — a visual aid backing a live speaker**, where the
recurring failure is treating a slide like a page of notes (long run-on sentences, vague phrasing,
figures dropped in with no explanation): the audience can't read a paragraph and listen at once, so
the slide competes with the speaker instead of supporting them. For that deck, everything below
follows from one idea: **a slide is a visual aid, not a document** — optimize for "understood in a
few seconds." But first know the *delivery mode*, because the density rules flex with it.

## Delivery mode — scope the density rules to how the deck is consumed
**Before applying the rules below, know how the deck will be consumed** (the interview captures it):
- **Presented (spoken)** — a speaker narrates; the slide shows the *phrase*, the speaker says the
  *sentence*. **The default.** One-idea-per-slide, few-words, big "read-from-the-back" type, "more
  slides not denser," and "spoken prose lives in speaker notes" all apply *here*.
- **Read-alone** (leave-behind, pre-read, emailed status, reference / appendix deck) — **no speaker**,
  so each slide must carry the sentence a speaker would otherwise say: **self-contained, complete
  lines and legitimately denser slides are the deliverable, not a flaw**; size type to arm's-length
  reading (not a projector); structure for scanning/jumping over a single linear narrative.
- **Fixed surface** (poster, single-slide infographic, one-pager) — one canvas, the **count can't
  grow**: organise density into clear regions/columns with strong hierarchy (you can't "add a
  slide"); read distance is poster-near or on-screen, not back-of-room.

So where a rule below says "one idea," "few words," "from the back," or "more slides," read it as the
**presented default** and flex it for read-alone / fixed-surface decks per the above. What **never**
flexes (every mode): contrast, no overlap, fidelity to the source, clear hierarchy, no tofu, one
consistent visual system.

## Tell a story — especially the opening
A deck should pull the audience along, not list facts. The motivation/opening is
where you win or lose them: build it **step by step** toward the problem, don't dump
it. A reliable shape — *what matters → what's hard about it → the gap nobody has
filled → (next slide) our idea.* Use a short visual progression (a few chips with
arrows, a numbered build) so the audience feels the logic, and end the setup on a
crisp **hook** — the open question your work answers. Name the concrete problems you
aim to solve; that's what makes a method feel necessary rather than arbitrary. Every
later slide should answer a question the previous one raised. *(This is for a **linearly-delivered**
deck — a talk, pitch, or readout. A **reference/leave-behind** deck is consulted non-linearly: make
each slide stand alone and be findable — clear titles, navigable structure — over a single arc.)*

## One idea per slide
Decide the single takeaway before writing anything. Title states the point;
the body supports it. If a slide needs two takeaways, it's two slides. *(Presented default — a
read-alone **reference** deck, a **poster** panel, or a single-slide **infographic** may legitimately
carry several related points; there the unit of "one idea" is the clearly-delineated **region**, not
the whole surface.)*

## Few words per point
Points should be phrases, not sentences — often 2–5 words. Good:
- "Latency dropped 40%"
- "Cache = single source of truth"
- "Retry only on timeout"

Bad (what to fix):
- "We tried several configurations on the staging dataset, running the full pipeline
  with retries enabled (the queue is the bottleneck); 1. pick the first batch ..."

The speaker says the sentence; the slide shows the phrase. **This assumes a speaker** — for a
**read-alone** deck (leave-behind, pre-read, reference, poster) there is no one to say the sentence,
so the slide must carry it: write complete, self-sufficient lines, not telegraphic 2–5-word fragments
the reader can't reconstruct. Terseness is a *presented*-deck target, not a universal one.

## Diagrams over text
A relationship is clearer drawn than described. For structure you are creating from
scratch (a pipeline, a state machine, a module map with no source figure), prefer native
shapes (boxes + arrows via deckkit) over bullet lists. But see the next rule first.

## Build native, editable objects — never a flattened slide
Every slide is **real PowerPoint objects** — live text boxes, shapes, tables — that the user can
select and edit one by one. This is a core advantage of building with python-pptx; protect it:
- **Never deliver a content slide as one whole-page image** (a screenshot/render pasted as the
  slide), and never ship "the deck" as code-only or HTML — the recipient must be able to fix a typo,
  restyle a box, or move a shape in PowerPoint/Keynote without you.
- **Generated/source images stay in their lane:** a figure, a chart, a *text-free* background plate,
  or a cover/divider illustration **with a native title on top** — never the slide's text/data baked
  into a raster. Text, numbers, labels, and titles are always native runs (so they're editable,
  searchable, and crisp at any zoom), never pixels.
- Keep the file clean: the planned slides and nothing else (no orphan/blank pages, no template
  residue) — a tidy, fully-editable `.pptx` is part of the deliverable's quality.

## Use the source's own figures — whole
*(True for any deck, not just academic ones.)* If the source — a paper, report,
doc, an existing slide, or a chart/plot already produced from the code/data — has a
figure for something (an architecture, results, a dashboard, a graph), **use that
figure** rather than redrawing it. Redrawing by hand is slow and risks dropping or
mis-stating detail — getting it subtly *wrong* in front of the audience (an expert
panel *or* your boss) is far worse than showing the original correct figure. And show the figure **whole**: a partial crop hides context and invites
"what about the rest?". Annotate the whole figure with native callouts/arrows to
guide the eye; don't chop it. For a **dense** whole figure (e.g. a paper
architecture), enlarge it and overlay **big native labels the audience reads
instead of the paper's tiny ones** — numbered markers (✪ on the 3–4 parts you name
aloud) + a large legend strip, or endpoint labels over the columns that matter. **Extract it
precisely**: prefer `extract_pdf.py figures`/`figure` (it caption-anchors, detects the page's
caption convention, snaps to the figure's true extent, and excludes page chrome) over eyeballed
fractional crops, then **re-view the PNG and confirm BOTH ways** — nothing of the figure is
clipped (legend, colour bar, axis labels/ticks, title, units, outer rows/cols, a sub-plot's
x-axis labels) AND no page text bled in (the figure's caption, a neighbour figure's caption
fragment, a running head/author line, a page number). A clean crop is tight to the figure's own
content and contains none of the page's prose. Trim only the page header, the figure's caption,
and dead outer whitespace — never the figure's content. Crop to a sub-region *only*
when a figure is genuinely too dense to read at all, and say so.

## Every figure gets a legend + a takeaway
A bare image grid means nothing to the audience. State what the rows/columns are
(write your own caption — don't rely on tiny in-figure text), and add a one-line
TAKEAWAY of what to notice. Without the takeaway, the audience guesses.

## Designed plots — pick the chart per argument
When *you* make the chart (data, no source figure), don't default to a bar every time: choose the
chart **type that fits the argument** (part-to-whole → donut; before→after gap → dumbbell; two-point
rank change → slope; A↑/B↓ tradeoff → dual-axis; vital few → Pareto), **theme it to the deck**,
**highlight the one series that matters** (everything else neutral grey), and give it a "so-what"
rail. Full roster + ready recipes in `references/data-viz.md` (`scripts/designed_charts.py`); KPI
tiles via `deckkit.scorecard`. For a single obvious number use a hero stat, not a chart.

## Layout patterns — reach for the right one (apply dynamically, not always)
Beyond columns/rows, `deckkit` has purpose-fit patterns; use the one that fits the *content*, and
don't force any of them:
- **Hero stats** — `scorecard` tiles (big number + ▲/▼ delta) for a status/KPI readout; `stat_row`
  for 2-4 standout editorial figures with no trend to plot.
- **Relationships** — `quadrant` when items classify on two real axes (effort×impact); `hub_spoke`
  for one centre + peers (platform+modules); `timeline` for chronology/roadmaps (one highlight node).
- **Wayfinding** — `big_numeral` (ghost watermark / marker) for enumerated content; reuse the SAME
  numeral+accent on the TOC, the section divider, and the recap so sections are navigable; bookend
  the deck (cover ↔ closing mirror, `corner_frame` for a sparse closer).
- **Publication bookend** — for editorial/report/zine decks, open with `cover` (issue label + big
  display title) and close with a mirrored `colophon` (payoff tagline + credits); `backdrop_motif`
  (a faint full-bleed grid/texture + accent disc) on *both* frames the deck as one object. For a
  research deck, `sources_page` renders references as a credible mono colophon.
- **Editorial register** — `editorial_header` (caps eyebrow + title + accent hairline) and a serif
  display face for showcase/brand/report decks; a per-slide source line for reports. **3-font roles:**
  a display face for titles/numbers, ONE monospace **chrome** face for all eyebrows/footers/page
  markers (`part_eyebrow`/`page_marker`), and a neutral body face — the mono-chrome trick is a quiet
  signature even in an otherwise plain deck. `specimen_card` (rule + giant glyph) compares fonts/brands.
- **Self-demonstration** (niche) — for a deck *about* layout/design/systems, render its own grid as
  the diagram (`wireframe_grid` + `spec_list`'s `derived = base × n` math) — showing the scaffolding
  adds authority. Don't force it on general business content.
- **Photography** — full-bleed photo under a graduated `scrim_overlay` (aim it at the text zone, not
  a flat overlay); `before_after` pairs, `photo_triptych`, `image_tab` corner labels for photo decks.
- **One-accent discipline** — for a focal-item-per-slide deck, colour ONLY the one element that
  matters and drop the rest to a neutral grey (`accent_one`); never exceed ~2 saturated hues unless
  the content is genuinely categorical. Restraint reads as confidence.

## Tables and equations
- **A table exists to make one comparison obvious.** Decide what it should compare
  (it follows from the source's message), and make *that* the salient axis — don't
  introduce a second, distracting comparison. If the point is "X helps", foreground
  *baseline vs +X*; don't lay it out so the eye instead compares two unrelated rows.
  Use real **rules** (`deckkit.hrule`) — a header rule, a separator under the
  baseline — so it reads as a table, not floating numbers. Include uncertainty
  (± std / error bars) when the source reports it. Distil — never paste a giant
  paper table; show the rows that carry the message.
- **Formal math.** When equations should look polished, render them with
  `deckkit.equation_png` (matplotlib mathtext: true italics, ⊙, fractions, proper
  sub/superscripts) and place the image. Keep `eq_par` for quick, editable inline
  math. Either way the notation must match the source's.
- **Formulas are TYPESET, never cropped — and may be derived from code.** Figures and tables you take
  *whole* from the PDF — but a formula you **re-typeset** with `equation_png` (or `eq_par`): a cropped
  equation bitmap is low-res, drags in the source's font/background, can't be recoloured/resized to
  the deck, and clips; a typeset one is crisp at any zoom and on-brand. **From a paper:** transcribe
  it precisely. **From code/other material:** *derive* the formula the code implements (loss, update
  rule, metric, transform) and typeset it, when it shows the idea more directly than prose — a strong
  move for a lab meeting. Either way it must be **faithful** to the source (same symbols/indices; for
  code, a correct expression of what it actually computes) and verified against it — fidelity rules.

## Layout: give every element room
The overall layout of a slide — margins, alignment, balance, whitespace — matters
as much as the words on it. Design is not optional polish; it is half the job.

**The governing rule is *suitable space* — the right degree.** Every element should leave a
comfortable margin on **all four sides**: never crowd an edge (top / bottom / left / right) and
never strand a large dead gap either. Too tight reads as cramped; too loose reads as
unfinished. The degree matters and is best judged in the render — so after building, look and
ask of each element "is there suitable, balanced space around it, or is it crowding/floating?"
- **Gutters.** Leave a consistent ~0.4 in (`deckkit.GUTTER`) between a figure and
  any adjacent text, callout, or slide edge. Text butted against a figure looks
  amateur.
- **Balanced split layouts — equal panels, equal flanking margins.** When a slide is split
  into left/right regions (text + figure, two-up comparison, image + caption), the two
  regions *and the white margins on either side of them* should be the **same width** unless
  you deliberately intend otherwise. A left panel and a right panel of unequal width — or a
  wider strip of white on one side than the other — is a lopsided-slide tell that reads as
  careless even when nothing overflows. Don't eyeball each panel's `x`/`w`; derive them all
  from one grid (`deckkit.columns(n)` returns `n` equal-width rects with symmetric outer
  margins and equal gutters). An *intentional* asymmetric split (e.g. a 1/3 text rail beside
  a 2/3 figure) is fine, but keep the outer left and right margins equal, and **check the
  render** — the two sides should look balanced, not accidentally uneven.
- **Don't strand a narrow element in a too-wide panel.** When one column's content is
  *naturally* much narrower than its half — a vertical timeline, a tall thin chart, a short
  list beside a paragraph — a 50/50 split leaves a big dead-white gap on that side. Fix it
  by **either** giving that column a *narrower, intentional* width (asymmetric split, equal
  outer margins) so its content **fills** the region, **or** centring the narrow element in
  its panel so the leftover white is symmetric. A large lopsided white band on one side is
  the tell to catch in the render.
- **Figure beside text — anchor the figure, gutter the text (don't centre + far-strand).** A
  very common imbalance: a figure left in a wide half-panel gets **centred** by `contain`,
  stranding white on its outer edge, *while* the side text is pushed to the far edge — leaving a
  big dead gap between figure and text. Fix both: **align the figure to its margin** (set the
  `picture` box to the figure's own aspect so `contain` doesn't centre-pad it) and place the
  text **one normal gutter away**, not against the opposite edge. Result: figure at the left
  margin, a ~`GUTTER` gap, then the text — balanced, with no stranded band.
- **Blocks hug their text — modest, *balanced* internal padding.** Inside a chip / card /
  callout the text should sit with a **modest** top-and-bottom margin: snug to the text, not
  floating in a tall box, and not cramped against the edges. Size the box to its content (the
  auto-growing `callout`; chips/cards sized ≈ text + a small pad) and **middle-anchor** the text
  so the padding is symmetric — a short card must not leave a big white strip at the bottom, and
  a one-line callout must not swim in a deep bar.
- **Bottom margin — measure or anchor, never hand-pick a y.** Keep content clear of the
  footer. The recurring failure is a bottom callout placed at an eyeballed low `y` that grows
  *down* into the footer when its text wraps. Don't guess a coordinate: use
  `deckkit.bottom_callout()` (anchors to the footer band and grows **up**, so it can't collide),
  ask `deckkit.content_band()` for the safe region, and pack content-height blocks with
  `deckkit.vstack(..., bottom=…)` (equal gaps + no overlap by construction; it errors at build
  time if the content can't fit). A hand-picked y for any auto-growing block is a bug.
- **Text must fit its box — and its CARD.** Never let text spill outside its callout/box, and never
  let an auto-growing text box extend **past the card/container drawn behind it** (the classic tell:
  a card sized for one line of body, but the body wraps to two — the second line hangs below the
  card). **Measure-then-place: size the card to the *measured* text** (count the wrapped lines at the
  real width — `deckkit.measure_lines`/`columns` + a height that fits), or shorten the text; don't
  hard-code a card height and hope. `scripts/lint_deck.py` now flags text that overruns its card —
  run it, and *check the render*, because overflow is invisible in the build code.
- **No widow — never strand one word (or a lone CJK glyph) on the last line.** A final line holding a
  single word/character reads as a mistake. Fix it by nudging the box **width** (a little wider or
  narrower so the last line gains company) or lightly rewording, so the wrap fills toward the end of
  the last line. Check it in the render — most common on 2–3 line bodies and titles.
- **Interior padding.** Text should never crowd a block's edge — keep a comfortable
  inset between a label/title/body and the boundary of its chip, callout, card, or
  box (the deckkit `chip`/`callout` helpers bake this in; for boxes you draw yourself,
  inset text ~0.15 in from the edges, more at the top of a titled card). Cramped text
  touching a rounded corner reads as unfinished even when nothing overflows.
- **No large empty region — fill the slide, balanced.** A slide that's mostly blank (content
  huddled in one corner or the top third, a wide empty band down a side or across the bottom) reads
  as unfinished — don't ship it. Fix it: **enlarge the figure/content to use the space, add the
  supporting element the point actually needs, or redistribute the blocks** so the content occupies
  the slide evenly. If a slide genuinely has too little to fill it, **merge or cut it** (a presented
  deck that's over-full wants *more* slides, never emptier ones). Whitespace is a *deliberate*
  breathing tool around content — not a large leftover void. *(On a **fixed surface** — poster,
  single-slide infographic, one-pager — you can't "add a slide": organise the density into clear
  regions/columns with strong hierarchy instead; the no-large-void rule still holds within the canvas.)*
- **Mind the gaps between blocks — even and intentional.** Equal gaps between repeated/adjacent
  blocks (cards, chips, rows, list items) — derive them from `columns`/`rows`/`vstack`, never
  eyeball; one gap visibly larger than its neighbours reads as careless. Adjacent blocks always need
  a **visible, consistent** gap — never touching, never wildly uneven.
- **Cards in a row share ONE height.** Sibling cards on the same row must be the **same height** —
  when their text differs in length, **size the whole row to the tallest card's content** and apply
  that height to all (don't grow each card independently — that yields a ragged row, the tell to
  avoid). If one card's text is much longer, either tighten its wording, widen the body so it wraps to
  the same line-count as its siblings, or accept the taller uniform row — but keep the heights equal.
  And leave a **clear gap below the row before the next line/element** (a caption or summary line
  directly under a card looks cramped) — `scripts/lint_deck.py` flags uneven row heights.
- **Read the whole slide as one composition (the overview test).** After building, step back from
  the render and take the slide in as a whole: is it balanced top-to-bottom and left-to-right, is
  attention led to one focal point, do the blocks line up on a clean grid, is the space used well?
  A slide can pass every *local* check and still look **off** as a gestalt — a lopsided mass, a
  drifting focal point, an empty quadrant. Fix the overall impression, not only the parts.
- **The squint test (hierarchy at a glance).** Blur your eyes — or just downscale the render to a
  thumbnail — and look again: the **3–4 levels of hierarchy** (the one focal element, the title, the
  supporting blocks, the fine print) must *still* be distinguishable when you can't read the words. If
  everything blurs into one even-grey field, the slide has no visual hierarchy — enlarge the
  protagonist, add contrast, or cut. A cheap, tool-free check that catches "flat" slides the
  word-level reading misses.
- **Invest unevenly — one element at 120%, the rest at 80%.** A slide (and a deck) reads as *authored*
  when one hero — the key figure, the headline number, the one diagram — is pushed and everything else
  stays cleanly competent, not when every element is maxed equally. Pick the one thing this slide is
  *for* and let it dominate; keep the supporting cast quiet.
- **Deck-level rhythm — vary the protagonist across slides.** A long deck reads as one template
  repeated if every slide has the same shape. Orchestrate **rhythm** deliberately: a *colour* rhythm
  (mostly light, with the occasional full-bleed dark divider or accent slide as a beat), a *density*
  rhythm (dense data slide → airy one-idea slide → a quote/whitespace breath), and a rotating *visual
  protagonist* (a chart slide, then a diagram slide, then a photo slide, then a big-number slide). Not
  random variety for its own sake — a paced sequence so the audience feels movement. (Section dividers
  are the natural beat markers.)
- **Avoid the AI-slop tells.** A handful of choices instantly read as machine-generated filler — name
  and avoid them: full-screen rainbow / mesh / purple-to-blue gradients; emoji in titles or as bullet
  markers; ✅/🚀/🔥 decoration; the rounded-card-with-a-left-border-accent everywhere; three-near-identical
  "feature cards"; over-exposed default fonts used without intent; and **fabricated specifics** (made-up
  stats, fake quotes, invented logos). Meta-heuristic: **when you feel the urge to *add* something to
  make a plain slide "look nicer," that urge is usually the slop signal — subtract instead** (more
  whitespace, one stronger element) and fix the layout, don't decorate it.
- **Don't crowd the title's accent rule.** `title_bar` draws a short accent underline below
  the title. When you add a subtitle / definition line under it, leave a clear gap *below the
  rule* before the subline (and start the body a step below that) — a sub-line jammed against
  the accent rule reads as cramped. If a slide needs a subtitle, budget vertical space for it
  (push the content region down) rather than tucking it under the rule.
- **The kicker/eyebrow adds a category — it must not echo the title.** The small label above
  the title (`title_bar(..., kicker=...)`) is a section/eyebrow; it should carry information
  the title *doesn't* — the section name, a step number, a phase. A kicker that repeats a word
  the title already leads with (kicker "Origin" over a title "Origin: founded in 2002") is
  pure duplication and looks careless. Fix it by **stripping the repeated word from the
  title** (let the kicker carry the section, the title state the specific point — "founded in
  2002, nearly bankrupt") **or dropping the kicker**. Same idea across slides: kickers should
  read as a consistent set of *section labels*, not restate each title.
- **Centre a single glyph or icon in its box.** A lone character or icon (a "?", a number, a
  mark) inside a box must be *optically centred*: give the textbox the **same x/y/w/h as the
  box**, `anchor=MIDDLE`, `align=CENTER` — and then **check the render**, since a single glyph
  off-centre is obvious. Don't offset the textbox or rely on default top-left placement.
  **Gotcha — full-width CJK punctuation won't centre as a standalone glyph.** A full-width
  mark (`？！。：`) renders left-of-centre *within its own advance*, so even with `align=CENTER`
  it looks pushed left. For a lone large mark use the **ASCII** form (`?`, `!`) so it centres;
  full-width punctuation is correct only *inside running CJK text*, not as a centred single glyph.
- **Even bullet rhythm needs a consistent line count.** A list looks evenly spaced only
  when every item occupies the *same* number of lines. The moment one item wraps to two
  lines, it claims an extra line-height of vertical space, so the gap before the *next* item
  looks bigger than the others — the "uneven last gap" tell. This is a line-count mismatch,
  never a `gap` value to nudge. `deckkit.bullet` now *measures* line counts from real glyph
  metrics (so the marker advance matches the render — no phantom or missing lines), but the
  authoring rule stands: keep list items to a consistent length — ideally each comfortably on
  one line (well under the column width). If an item genuinely must wrap, let *all* peers wrap
  (uniform rhythm) or give it its own element. Still *check the PNG*: if one gap is larger,
  shorten the item above it until the rhythm is even.
- **Diagram shapes stay inside their container.** When you draw a native diagram into a
  card/panel (e.g. nodes in a box, icons around a hub, items flanking a centre), every
  shape must sit *inside* that frame with a margin — a block escaping the card edge (or an
  asymmetric, off-centre cluster) is the "out of lock" tell. Compute positions from the
  container's centre and keep them symmetric; after rendering, check no shape pokes outside
  its frame.
- **Match corner rounding between a card and anything overlaid on it.** A *rounded* card
  with a **square** colored header band (or a square accent bar) on top is a classic tell —
  the band's right-angle corners poke past the card's curve. Fix it one of two ways: give
  the band rounded *top* corners that match the card's radius (`deckkit.box(corners='top',
  r=<card radius>)`), or **inset** a thin accent strip/bar by the corner radius so its
  square ends land on the card's *straight* edge, not over the rounded corner (deckkit's
  `callout` insets its accent bar this way). Never lay a square block over a rounded one.
- **Corner rounding is a deck-wide language — keep it consistent, especially for images.** A
  **square-cornered image** sitting in a rounded frame, or beside rounded cards/panels, is a
  visible inconsistency (the photo reads as pasted-in). If the deck's blocks are rounded, **round
  the images to match** — `deckkit.picture(..., round=True)` or `r=<inches>`; for an image inside a
  rounded frame use a radius ≈ the frame's radius **minus the border** so the curves stay
  concentric. Conversely, on a hard-edged/Swiss deck keep images square. One radius family across
  cards, panels, chips, and images — don't mix squared and rounded corners on the same slide.
- **Connector labels: centred and tight.** A word over an arrow (a verb or transform name —
  e.g. "encode", "train", "merge") should be *centred on the arrow* and sit just above it
  with a small gap — not drifting to one side or floating far above. `deckkit.arrow_label`
  does this for you (places the label at the arrow's centre x, a hair above its top), so
  every connector label stays consistent.
- **Connectors point the way the flow actually moves.** An arrow between two blocks must run
  *along the flow*. Side-by-side blocks → a left/right arrow; **vertically stacked** blocks
  (problem→solution, before→after read top-to-bottom) → a **down/up** arrow
  (`deckkit.arrow(..., direction="down")`). A sideways arrow squeezed between two
  stacked boxes is a classic wrong-direction tell — match every connector's orientation to
  the layout, and check it in the render.
- **Equal spacing for repeated elements.** A row or column of blocks joined by connectors
  must have **equal gaps and equal connector lengths** — hand-placing each block's `x`/`y` and
  each arrow produces visibly unequal spacing (one arrow longer than the next), which reads
  as careless. Derive the blocks from one grid: **`deckkit.columns(n, gap=...)` for a
  horizontal row**, **`deckkit.rows(n, gap=...)` for a vertical stack** (both return equal
  cells with equal gaps; pass `slide=s`). Then drop each connector **centred in the equal
  gap** rather than eyeballing positions. And **adjacent blocks always need a visible gap
  between them — never let two boxes touch** (a stacked pair whose bottom edge meets the next
  box's top edge reads as one merged block); leave a clear `gap` (the `rows`/`columns` helpers
  enforce one). A zero-gap seam between blocks is a common hand-placed-coordinate bug.
- **Image `fit`: never crop the subject out.** `fit="cover"` fills a frame by cropping the
  overflow — fine for edge-tolerant texture, atmosphere, or backgrounds, but it will happily
  slice off the very thing the image is *about* (the subject cut down to a sliver; a key
  object left out of frame). Use **`fit="contain"` whenever the image's subject — or all its
  parts — must stay fully visible**: a figure, a whole object, a product shot, a multi-element
  scene (several items that must each show), anything whose meaning needs the whole. If
  `contain` letterboxes too much,
  **shrink/zoom the placement or regenerate at the frame's aspect ratio** — never switch to
  `cover` and crop the subject away. **After placing *any* image (generated or source),
  re-view the slide and confirm the key subject isn't cut off** — the same look-after-you-place
  rule used for cropped figures, applied to every `picture()`. A full-bleed `cover` plate is
  only safe when its subject sits well inside the central safe area.
- **Align labels under the image feature they describe.** When captions/labels annotate parts
  of an image (items in a row, regions of a diagram, stages of a process, parts of a product),
  put each label *directly under (or beside) the thing it names* — a label far from the part it
  points to reads as disconnected. Measure the feature's position in the placed image and centre
  the label on it.
- **Generated images of real things must be factually right.** A generated plate of known
  subjects that gets relative **size/proportion, count, colour, or arrangement** wrong (two
  objects drawn equal when one is much bigger; the wrong number or colour) reads as broken to
  anyone who knows the subject — even on a "decorative" plate. State the facts in the prompt and
  re-view the result; when the factual relationship *is* the point, a prompted-and-verified plate
  is fine, or **draw it natively** (deckkit shapes / a chart) for guaranteed control. (See
  `references/image-generation.md`.)
  If the features are **bunched** so labels would collide, **spread them** — place (or
  regenerate) the image wider/at the band's aspect so each feature has room for its label —
  rather than cramming labels under a clump.
- **Let the hero breathe.** When a figure *is* the point of the slide (results, an
  ablation, an architecture), give it the slide — enlarge it and reduce competing
  text to one caption + one takeaway, rather than shrinking it to make room for
  bullets. And prefer the figure's **own** legend/labels over re-creating them
  natively (re-created legends drift out of sync and add clutter).
- Align elements to a shared grid; don't let things float at random offsets.

## Colour: vary within the brand
Don't paint every block the same accent — a diagram where every box is the one blue
reads as monotone and unconsidered. Rotate through the theme's accents
(`deckkit.ACCENTS` = blue · teal · gold · steel · violet · green; the first few are
the template's own secondary accents, so they stay on-brand) so colour signals
*structure*, and reserve one colour (magenta) for emphasis/warnings. Pull the base
palette from the template; these are accents on top of it.

**A sequence of blocks must read as a *thought-through* set of colours.** For a row/stack of
chips, cards, or pipeline stages, give each block a **distinct, deliberately-chosen hue** —
and use `deckkit.palette(n, ACCENTS)` to get them: it returns `n` distinct fills and *warns at
build time* if any two **adjacent** blocks aren't visibly different. Two rules it enforces:
(1) **no two adjacent blocks share a hue** (the "first two blocks are the same colour" tell);
(2) **never drop a neutral gray into a colour sequence as if it were a category** — gray reads
as disabled / secondary, so a vivid block beside a gray one looks half-finished, not designed
(reserve gray for genuinely de-emphasised items). Pick hues that *contrast* (cyan↔amber,
violet↔rose — not two cool near-neighbours), and let `chip`/`modbox` auto-pick the text colour
for ≥4.5:1 on each fill. If a meaningful order exists, map it (e.g. the primary accent on the
key step, a warm/warning hue on the failure state).

**Never let colour be the *only* signal.** If a chart's series, a status, or a
"before/after" is distinguished by hue alone, it collapses under a projector's washed-out
colours and disappears for colour-blind viewers. Back colour with a second cue — a direct
label, a shape/marker, a pattern, or a position — so the meaning survives without it.

## Accessibility
A few cheap habits make a deck usable by everyone, and most are things you should do
anyway:
- **Contrast ≥ 4.5:1** for normal text (≥ 3:1 for large/bold ≥ ~18pt). Check a colour
  against its fill with `deckkit.contrast_ratio()` *before* committing — light-grey
  captions on white and white text on a light accent are the usual failures. (`chip`/
  `modbox` now auto-pick a readable text colour; the `deckkit` palette defaults clear
  4.5:1 on their intended backgrounds.)
- **Don't encode meaning by colour alone** (see above) — pair hue with a label/shape.
- **Alt-text on every informative figure.** Call `deckkit.alt_text(shape, "…")` after
  `add_picture()` (and on diagrams) with a one-line factual description ("ROC curve:
  proposed method above baseline"). It doesn't render — it's screen-reader metadata in
  the .pptx — so it's invisible to the pixel critic; set it at build time as a habit.
  Decorative-only shapes can be left without alt-text.
- **Logical reading order & real text.** Keep titles in the title placeholder, use real
  text (not text baked into an image), and order content top-to-bottom / left-to-right so
  assistive tech follows the intended flow.
- **Legible type sizes — set the floor by the medium.** For a **projected talk**, body large enough
  to read from the back (~18pt+; titles ~28pt+). For a **webinar** size up (the slide is shrunk in a
  video window); for a **read-alone** deck read at arm's length, or a **poster/infographic**,
  secondary type can run smaller and denser — the floor is "comfortably legible at *this* deck's read
  distance," not "back of a hall." Whatever the floor, contrast (≥4.5:1) never relaxes.

## Visual hierarchy
- High-contrast titles (white on a colored band, or dark on white) — readable at a
  glance, consistent across slides. Keep text-vs-background contrast high (≈4.5:1 or
  better); light-grey body on white or pale labels on a tint fail from the back row.
- Body 16–18 pt; don't shrink text to fit — cut text instead.
- **Mind the canvas scale when judging sizes.** The deck is built on a 10 × 5.625 in
  canvas (75% of the standard 13.33 in), so every point size is ~¾ of its
  standard-deck equivalent: 16 pt here ≈ 21 pt on a normal deck, and a 12.5 pt callout
  ≈ 17 pt, an 8–9 pt caption ≈ 11–12 pt. That means **callouts/captions/figure labels
  are the things that go illegible first** — keep callout body ≥12 pt and anything the
  audience actually needs to read ≥14 pt here. When in doubt, the render tells you:
  if you have to squint at the PNG, the back row can't read it.
- Accent colours for emphasis, used with intent (see Colour above); a thin colored
  rule or a small marker is enough.
- **Mixed-size text on one line — vertically centre it, don't baseline-mix.** When a single line
  pairs a small part with a much larger emphasised one (a `before → after` change stat, a label +
  hero number, a unit beside a big figure), runs in one box **share a baseline** — so the small
  part/arrow sinks to the bottom, dropped below the big value's centre (e.g. "<10% → **≈40%**" with
  the arrow low). Fix by **vertically centring** the parts: keep them in one box and **baseline-shift
  the small run up** to the big value's centre — which preserves natural, equal spacing
  (`deckkit.change_stat` does this) — or use separate middle-anchored boxes; or keep the sizes close.
- **Equal spacing around an operator/symbol.** An inline `=`, `≈`, `→`, `+`, `×`, `:` (etc.) must
  have the **same gap on both sides** — `A = B`, never `A  =B`. Two traps to catch in the render:
  (1) a layout that puts a wide fixed gap on one side and a tight text space on the other — size both
  gaps equal; (2) on a CJK deck, a **full-width space (`　`, ~1 em) on one side and an ASCII
  space on the other** (a common mistake) — use the *same* space character, same width, on both sides.
- Name the closing slide for its purpose — an academic talk ends on **"Conclusion"**,
  not "Take home"; a status update might end on "Next steps".
- Generous whitespace. A slightly empty slide reads as confident; a packed one
  reads as a data dump.

## Callouts carry the message
A short labelled callout (THE GAP, PAYOFF, TAKEAWAY, NOTE) is where the
"so what" goes. Keep it to one line.

## Render and look — always
python-pptx places text blind: it never complains about overflow, a callout on the
footer, low contrast, or a missing glyph. The only way to know a slide is right is
to render it to an image and look. This caught every layout bug in practice; it is
not optional polish, it is part of building.
