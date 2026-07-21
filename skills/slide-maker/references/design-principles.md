# Design principles — why these slides look the way they do

These rules are tuned to the **default deck — a visual aid backing a live speaker**, where the
recurring failure is treating a slide like a page of notes (long run-on sentences, vague phrasing,
figures dropped in with no explanation): the audience can't read a paragraph and listen at once, so
the slide competes with the speaker instead of supporting them. For that deck, everything below
follows from one idea: **a slide is a visual aid, not a document** — optimize for "understood in a
few seconds." But first know the *delivery mode*, because the density rules flex with it.

## Table of contents
- Delivery mode — scope the density rules to how the deck is consumed
- Tell a story — especially the opening
- One idea per slide
- Few words per point
- Diagrams over text
- Build native, editable objects — never a flattened slide
- Use the source's own figures — whole
- Every figure gets a legend + a takeaway
- A placed figure's OWN text must stay LEGIBLE at the displayed size
- Designed plots — pick the chart per argument
- Big numbers — the hero numeral must read clean
- Layout patterns — reach for the right one (apply dynamically, not always)
- Tables and equations
- Layout: give every element room
- Colour: vary within the brand
- Accessibility
- Visual hierarchy
- Callouts carry the message
- Render and look — always

## Delivery mode — scope the density rules to how the deck is consumed
**Before applying the rules below, know how the deck will be consumed** (the interview captures it):
- **Presented (spoken)** — a speaker narrates (a live room OR a screen-shared meeting/webinar both
  count as presented); the slide shows the *phrase*, the speaker says the
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
Points should be phrases, not sentences — often 2–5 words (in any domain). Good:
- "Latency dropped 40%" · "Churn down 12%" · "Saves 4 hours a week"
- "Cache = single source of truth" · "One owner per metric"
- "Retry only on timeout" · "Photosynthesis needs light"

Bad (what to fix):
- "We tried several configurations on the staging dataset, running the full pipeline
  with retries enabled (the queue is the bottleneck); 1. pick the first batch ..."

The speaker says the sentence; the slide shows the phrase. **This assumes a speaker** — for a
**read-alone** deck (leave-behind, pre-read, reference, poster) there is no one to say the sentence,
so the slide must carry it: write complete, self-sufficient lines, not telegraphic 2–5-word fragments
the reader can't reconstruct. Terseness is a *presented*-deck target, not a universal one.

## Diagrams over text
A relationship is clearer drawn than described. For structure you are creating from
scratch — a pipeline or state machine, but equally a process/workflow, an org or market map, a
concept taxonomy, a timeline — prefer native shapes (boxes + arrows via deckkit) over bullet lists.
But see the next rule first.

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
- **Slide text is for the AUDIENCE — never a build/meta annotation about how the slide was made.**
  Properties of how you built it (a chart is editable-native, an image is AI-generated, a block is a
  placeholder, the deck is a draft) are **never captions on the slide**. Concretely, *never* let any
  of these reach a rendered slide: "（可点击编辑的原生图表）" / "(editable native chart)",
  "(AI-generated)" / "AI 生成", "(placeholder)" / "占位", "(draft)" / "草稿", "(sample/示例)",
  "generated by …", TODO / FIXME / dev notes, or any parenthetical describing the *method/tool* rather
  than the *content*. A caption names the **data or subject** ("一年内的变化", "Fig 3: 重建对比"), not the
  technique. Such notes belong in build-script comments or the step-6 hand-off — **leaking one onto a
  slide is an embarrassing, ships-broken mistake.** (Editability is a *feature you deliver*, not
  something you announce on the slide.)

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

## A placed figure's OWN text must stay LEGIBLE at the displayed size
Sizing a figure is not just "make it fit the slot" — **its internal text (axis labels, tick numbers,
legend, in-plot annotations) has to be READABLE at the size it's actually shown.** The recurring
failure is shrinking a figure to fit a small cell until its labels are an illegible blur — the figure
then proves nothing. When the internal text won't read at the placed size, fix it in this order:
**(1)** give the figure more room — fewer figures per slide, a bigger cell, or its own slide (and for a
**SOURCE** figure whose own labels won't read, more room *plus* big NATIVE labels overlaid so the audience
reads those instead of the original's tiny ones — you can't regenerate a source figure; see "Use the
source's own figures — whole"); **(2)** for a figure *YOU* generate (never a source figure — don't redraw
those), **regenerate the plot bigger-but-simpler** — larger fonts, thicker lines, fewer series/ticks/words,
so it stays legible when small (author a thumbnail-destined chart at thumbnail scale, not a dense full-size
plot crammed down); **(3)** only if neither is possible, drop the in-figure text and carry it in a native
caption (per "Every figure gets a legend"). **Check it in the render**: zoom each figure and confirm a back-of-room
viewer could read its labels — if you can't read them on screen, neither can they.

## Designed plots — pick the chart per argument
When *you* make the chart (data, no source figure), don't default to a bar every time: choose the
chart **type that fits the argument** (part-to-whole → donut; before→after gap → dumbbell; two-point
rank change → slope; A↑/B↓ tradeoff → dual-axis; vital few → Pareto), **theme it to the deck**,
**highlight the one series that matters** (everything else neutral grey), and give it a "so-what"
rail. Full roster + ready recipes in `references/data-viz.md` (`scripts/designed_charts.py`); KPI
tiles via `deckkit.scorecard`. For a single obvious number use a hero stat, not a chart.
- **The axis / baseline must span EVERY element it measures.** A bar/waterfall/dot chart's baseline
  or value axis has to run under (or across) *all* its bars — a baseline that stops short of the last
  bar reads as a rendering bug. Derive its length from the bars (`last_bar_x_end − axis_x`), never a
  hand-picked width that happens to miss the final element.
- **A cumulative / waterfall must not DOUBLE-COUNT.** Show the increments as floating bars *or* their
  running total as a full bar — never both an increment set AND its sum as peer bars (a "+8 / +8.3 /
  +16.3" trio reads as three additions when 16.3 = 8 + 8.3). Use dashed connectors to carry the running
  total between floats, end on ONE total/subtotal bar, and keep *different kinds* of quantity apart
  (e.g. employee take-home extras vs employer-paid pension are two stacks, not one 135% total — show
  the second as a separate labelled note, not stacked into the first). `designed_charts.waterfall` /
  `designed_charts` render this correctly; prefer them over hand-rolling floating boxes.
- **The geometry must MATCH the number — three ways an encoding silently lies.** A picture that
  misrepresents its own data is worse than a broken layout; before shipping any value-driven chart,
  read one bar/cell's *geometry* against its *printed value*. (1) **Zero baseline for magnitude** —
  a column/bar's length must encode the value, so the axis starts at 0; on clustered-high data
  (85/88/92) an auto-cropped axis makes a 1.09× gap look ~3×. (2) **Proportional means proportional**
  — a funnel band / bubble area / any size-encoding must track `value/max` with at most a hairline
  floor; a min-size clamp that widens a 5%-of-max tier to 20% makes the shape contradict its label
  (route a too-thin label to a side leader instead of inflating the shape). (3) **Signed scales
  anchor neutral at 0** — a diverging blue↔red must put its neutral at the *value* 0, not the data
  midpoint, or a true 0 reads as negative. deckkit's components now default to all three (zero-base
  column/bar, hairline funnel sliver, zero-centred `div` heat); a matplotlib or hand-rolled chart
  gets none for free — set `ylim(bottom=0)`, keep sizes proportional, use `TwoSlopeNorm(vcenter=0)`.

## Big numbers — the hero numeral must read clean
- **An integral number never wraps.** A hero/ghost numeral or a single figure ("2026", "€15亿",
  "+16.3%") must stay on **one line** — never break into "202" / "6". Size it to fit its box, or pass
  **`deckkit.text(..., wrap=False)`** (a ghost may then bleed off-canvas, which is fine; the build-time
  lint still catches a real overflow).
- **Numerals need LINING figures.** Set big numbers in a **lining-figure** face (uniform-height,
  baseline-aligned digits) — Helvetica Neue / Arial / Verdana, or Cambria / Times New Roman for serif.
  A big number in an **old-style-figure** face (Georgia, Constantia, Hoefler Text — verified from the installed font, not assumed) shows
  digits at different heights ("some smaller / higher / lower") and misaligns with adjacent CJK/Latin
  on the line. Full rule + face list in `references/font-guidance.md`. Verify digit alignment in the
  render — beside CJK (`中文 15亿`) and on pure-Latin lines.
- **A numeral STACK is measured, never hand-guessed.** The classic broken slide is a display numeral
  (40–80pt) whose label above and caption below were placed by eye — the numeral's real ink height
  (~1.35× its point size) swallows the caption and the render shows the digits struck through the
  text. Stack label → numeral → caption with `deckkit.vstack()`, or seat each element off the
  previous one's MEASURED bottom (`measure_text`); and after ANY size change to the numeral,
  re-seat everything below it — a size tweak silently invalidates every hand-placed offset under it.

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
- **Image-text composition patterns — reach past the default 50/50 split.** A richer vocabulary for
  pairing an image with text (pick by *what the image is for*, then keep it consistent):
  - **Side panel + bleed** — image on one side **bleeding off the slide edge** (no margin on the outer
    edge), text in a flush column on the other; dynamic, gives the image presence without shrinking it.
  - **Full-bleed + floating text** — image fills the slide, text sits in a calm zone over a
    `scrim_overlay` aimed at it (a corner, a band) — for an atmospheric opener or section divider.
  - **Faded large title over imagery** — a low-contrast/large display title overlapping a soft
    background image (an ink wash, a texture) — editorial, literary; keep the image quiet so type wins.
  - **Colour-block quadrant** — 2×2 (or 1×N) of solid colour panels, each a category with a short
    label + figure/icon; bold, scannable (use `palette(n)`, one hue per block — never gray filler).
  - **Inset / framed image** — a smaller image in a `corner_frame` or `photo_card` with a caption rail
    beside it, for a figure that supports rather than dominates.
  - **Image grid / contact sheet** — N small images on a strict grid (one gutter, equal cells) for a
    montage/montage-of-examples; label each consistently.
  Whichever you pick, keep the subject **whole** (`picture(fit="contain")` unless edge-tolerant), the
  text one gutter clear, and the same pattern across sibling slides.
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
- **Formal math.** Default to **`deckkit.equation_native`** (a LaTeX-subset rendered as real,
  click-**editable** text runs — italic variables, true sub/superscripts, math glyphs — that stays
  editable and renders the same in PowerPoint/Keynote/LibreOffice/PDF *where the math font is present*).
  Reach for `deckkit.equation_png` (matplotlib mathtext raster) only for **2-D math it can't lay out**
  (fractions, matrices, stacked limits) **or when the math font can't be guaranteed**; `eq_par` for a
  single inline symbol. Either way the notation must match the source's.
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

### The C.R.A.P. framework — the four principles every layout obeys
Robin Williams' four foundational design principles (Contrast, Repetition, Alignment, Proximity)
are the organizing lens for *all* the layout rules below — use them as a named checklist when you
design a slide and when you critique one. Each maps onto rules this skill already enforces:
- **Contrast — make the important element pop; lead the eye.** Create a *visible* difference between
  levels so the slide isn't an even grey field: **size** (title clearly larger than body — see "Visual
  hierarchy"; ~1.4–1.8× steps), **weight/colour** (one accent for emphasis, ≥4.5:1 contrast), **font**
  (a display face distinct from the body face — **≤2 *text* families**, often serif + sans but two
  well-paired sans is fine; a **mono for code** and a **CJK face on a CJK deck** are functional, not
  extra style fonts; emphasise with
  bold/italic, **never underline**, which clutters), and **shape** (a chip/card/band to set one thing
  apart). Contrast is *intentional and balanced* — too much reads as chaos, too little blends together.
  This is the **squint test** and "invest unevenly (one element at 120%)" rules below.
- **Repetition — repeat identity markers so the deck reads as ONE designed thing.** Reuse the same
  *system* on every slide: title chrome, accent palette, font pairing, bullet/marker style, footer,
  section-divider treatment, and any signature motif or numeral system. Repetition is what "brands" a
  deck and makes a long one feel unified rather than templated-at-random — it is largely a **deck-level**
  (planner) responsibility, since only a whole-deck view can keep the system consistent. (See
  "Deck-level rhythm" — repetition of the *system*, deliberate variation of the *protagonist*.)
  **What repeats is the QUIET system, never the loudest ornament**: unity comes from palette, type,
  spacing, and chrome *geometry* — a signature motif or decorative device stamped identically on every
  page stops branding and starts shouting. Dose the motif (cover · dividers · closer, ~2–3 appearances)
  and keep per-slide chrome (title furniture, rules, footers) in ink/grey with at most one thin accent;
  saturated colour belongs on the elements that carry meaning — data, diagram nodes, icons, the hero
  number — not on the scaffolding around them.
- **Alignment — every element sits on a shared grid, intentionally; nothing is placed by eye.** A clear
  alignment makes a slide read as organized; a single off-grid element reads as messy. Derive positions
  from `columns`/`rows`/`vstack`/`content_band` so edges line up — never hand-pick a coordinate. (See
  "Balanced split layouts", "measure or anchor, never hand-pick a y".)
  - **Hub / converge / fan-out nodes sit on the CENTRE of the set they link — computed, not eyeballed.**
    In a many→one (inputs converging into one node), one→many (one node fanning to several), or
    hub-and-spoke diagram, the **shared node must be centred on the geometric span of its members**
    (midway between the topmost member's top and the bottommost member's bottom), and **every connector
    anchors at each member's centre**, not its top. Eyeballing the hub to one member's level (the classic
    "the middle block isn't on the middle line of the two it joins") reads as broken. Compute it:
    `hub_y = span_center([(y1,h1),(y2,h2),…], hub_h)` and anchor connectors with `mid(y, y+h)` — the
    converge/fan analogue of `spaced_centers` for evenly-spaced rows. (deckkit, SKILL §4.)
  - **A two-part layout shares ONE centre line.** When a slide splits into two regions — left↔right
    (a table + a side panel, a figure + its text, before↔after) or top↕bottom — the two parts are
    **centred on the same axis**, not corner-pinned. Equal-height parts share top & bottom edges;
    **unequal-height parts are centred so their mid-lines coincide** — a free-floating shorter block is
    centred to the taller one's midline rather than top-pinned (which would leave the taller one hanging
    below). The classic tell: a short table top-aligned with a taller side card. Fix by centring the
    shorter part on the taller's midline (`y_short = y_tall + (h_tall − h_short)/2`), or size both from
    `columns`/`content_band` so their centres coincide by construction. **Guard — top-align (NOT
    midline-centre) when the two parts are parallel top-down *reading* content** (two text columns, two
    bulleted lists, or two panels both starting under a shared header): the eye scans each from the top,
    so they share a TOP edge; centring would strand the shorter one with dead space above it. Mid-line
    centring is for self-contained *blocks* whose vertical position is free — a table, figure, card,
    stat, or image — set against a taller neighbour.
  - **Text inside a box sits in its true (geometric) middle — anchor, don't y-nudge.** A badge / chip /
    pill / selected-marker / button / callout label must be **vertically centred** in its box: give the
    textbox the box's FULL `(x, y, w, h)` and `anchor=MSO_ANCHOR.MIDDLE` (deckkit `chip`/`meter_bar`/
    `scorecard` do this), **never a hand-picked `y + small offset` with a shorter height** — that y-nudge
    is exactly what makes a label read "a bit high / a bit low" in its block. Re-check every badge/pill in
    the render: the text block's centre must match the box's centre. (The one exception is a run that must
    share a BASELINE with a separate sibling box — a number beside its unit — anchored BOTTOM per the next
    bullet, not MIDDLE; never a licence to top-pin or y-nudge a self-contained label.)
  - **Mixed font sizes on ONE line must read as one line — share a baseline, or deliberately centre.** A
    big + a small size on the same visual line must sit on **one horizon**, not float. Which is right
    depends on *what the small part is*: a **unit / suffix** (dB · % · × · ms) correctly sits on the
    **shared baseline** — put both as runs in **ONE `text()` box** and PowerPoint baseline-aligns them
    (this is exactly what `stat_row` does; **don't centre a unit**). A **comparison prefix / arrow / small
    operand beside a hero number** (a `before → after`, "<10% → ≈40%") instead reads better **vertically
    centred** on the big value — shift the small run with `deckkit._set_baseline(run, pct)` (this is what
    `change_stat` does). The tells to fix: a comparison prefix/arrow **sunk low** below the big value's
    optical centre, or mixed sizes that **don't share a consistent line** — most often from top-aligning
    **separate boxes** (never top-align different sizes; if they must be separate, anchor both `BOTTOM`
    so the baselines meet).
- **Proximity — group related items; separate unrelated ones with space.** What belongs together sits
  together; the gap *between* groups is clearly larger than the gap *within* one, so the eye parses the
  structure without lines or boxes. (See "Group by proximity — inter-group gap ≥ ~1.5–2× intra-group".)
  Operationally this is a **SPACING SCALE** — ~4 gap tokens on a ~1.6× ladder, *line < element < group <
  section* (≈ `0.06 · 0.12–0.2 · 0.3 · 0.5in` on the default 10×5.625in canvas; scale to the canvas),
  declared once in the design language and reused everywhere. Identical gaps everywhere is the tell of an
  undesigned page: when every distance is the same, proximity carries no structure and the eye must read
  boxes and rules instead. Whitespace earns its place by *job* — separation, emphasis, framing, or
  guiding the eye — and heavy elements (a big dark block, a full-bleed image) are balanced by air or
  lighter elements across the composition: balance visual **weight**, not object count.
A slide that satisfies all four — one element pops (C), it uses the deck's repeated system (R),
everything aligns to a grid (A), and related things are grouped (P) — is almost always well-laid-out;
a slide that feels "off" usually violates one of them, so name *which* when diagnosing.

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
  a 2/3 figure) is fine, but keep the outer left and right margins equal — build it as
  `dk.columns(2, slide=s, weights=(1, 2))`, which proportions the panels while keeping the
  margins symmetric by construction — and **check the
  render** — the two sides should look balanced, not accidentally uneven.
- **Don't strand a narrow element in a too-wide panel.** When one column's content is
  *naturally* much narrower than its half — a vertical timeline, a tall thin chart, a short
  list beside a paragraph — a 50/50 split leaves a big dead-white gap on that side. Fix it
  by **either** giving that column a *narrower, intentional* width (asymmetric split, equal
  outer margins — `dk.columns(2, slide=s, weights=(1, 2))` is the measured form of exactly this
  fix) so its content **fills** the region, **or** centring the narrow element in
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
- **The footer band is RESERVED — content stays above it (a `≈0.6in` bottom strip is deck chrome).**
  Keep *every* content block — a card, a dark stat band, a callout, a figure — clear of the bottom
  footer/page-number zone. A content band whose bottom dips over the footer is the recurring collision
  (it still "looks placed" in code but overlaps the footer in the render). `scripts/lint_deck.py` now
  flags this as a **FOOTER collision / FOOTER-ZONE intrusion** with no "text-on-a-card" escape (the
  footer is chrome, never something a block may sit on).
- **Bottom margin — measure or anchor, never hand-pick a y.** Keep content clear of the
  footer. The recurring failure is a bottom callout placed at an eyeballed low `y` that grows
  *down* into the footer when its text wraps. Don't guess a coordinate: use
  `deckkit.bottom_callout()` (anchors to the footer band and grows **up**, so it can't collide),
  ask `deckkit.content_band()` for the safe region, and pack content-height blocks with
  `deckkit.vstack(..., bottom=…)` (equal gaps + no overlap by construction; it errors at build
  time if the content can't fit). A hand-picked y for any auto-growing block is a bug.
- **Avoid overlap by *construction*, then catch by lint — not by eyeballing.** The reliable way to
  "no overlaps, perfect layout" is to derive every position from the measured layout helpers
  (`content_band` for the safe rect, `columns`/`rows` for splits, `vstack(bottom=…)` for stacks,
  `bottom_callout` for the bottom) so blocks *can't* collide, then run the **two nets in order**:
  `deckkit.lint_layout(prs)` at BUILD time (in-process, before any render — off-canvas · overflow ·
  text-on-text · card-escape · footer · off-centre) and `scripts/lint_deck.py` AFTER render (re-checks
  geometry on the final file + the render-only faults: CJK kinsoku/widow · missing EA font ·
  whole-page-image · uneven rows). Hand-placed coordinates are where overlaps creep in; measured
  placement + the build-time gate + the render lint is how they stay gone.
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
- **Interior padding — keep a real margin on ALL sides (≥ ~0.12 in), measured against the *wrapped*
  text.** Text must never crowd a block's edge — keep a comfortable inset between a label/title/body and
  the boundary of its chip, callout, card, or box (deckkit `chip`/`callout` bake it in; for boxes you
  draw yourself, inset ~0.15 in, more at a titled card's top). Cramped text touching an edge/corner reads
  as unfinished **even when nothing overflows** — `lint_deck.py` flags the highest-frequency case (**TEXT
  PADDING**: text cramped against / past the card's BOTTOM, against the rendered text) plus the two
  sub-cases below; **left/right/top insets you eyeball in the render** (the lint stays bottom-only to avoid
  false positives on centred labels). Two recurring sub-cases the lint also catches and you must design against:
  - **Size a chip / pill / label to its text — never the reverse.** A label wider or taller than its
    pill (e.g. "Boston Dynamics" in a 0.8-in chip) wrap-crams against the edges. Size the chip to the
    longest label (or use fewer/shorter labels, or a plain `· `-separated line instead of pills). (**CHIP/LABEL TOO SMALL**.)
  - **Stack value + label + sub-label with enough gap that a 2-line WRAP won't collide.** A big stat
    numeral or a label that wraps to two lines overruns whatever sits below it — give each its own room
    (or shrink the numeral / shorten the label so it stays one line). Two boxes whose *declared* rects
    don't overlap still collide once the upper one's text wraps. (**TEXT COLLISION**.)
- **A node/block must NOT sit ON a connector line — route links in the GAPS between nodes.** A line that
  passes under or through a box (or a node dropped onto a bar) reads as a mistake and muddles the diagram.
  Draw each connector **edge-to-edge in the gap** between nodes (or draw the nodes ON TOP of the mesh so
  no line shows through), and give a node a clear margin from any line it doesn't connect to. If a
  representation is hard to read (a row of chips on a bar), **rethink it** — a labelled container/mesh, a
  clear left→right flow, or a stack usually says it better than dots on a line.
- **Show an AGGREGATE separate from its constituents — never buried among them.** When a diagram shows a
  *derived/summary* quantity (a net or resultant vector, a total, a mean/centroid, a combined output)
  alongside the individual elements that produce it, the aggregate must read as the **outcome**, not as
  one more item in the crowd. Drawing the net arrow *inside* the cluster of component arrows (overlapping
  them) makes it look like just another component — the exact failure to avoid. Instead: **(1) separate it
  spatially** — give it its own zone beside/below the group, not on top of it; **(2) make the relationship
  literal** with an explicit operator or connector (`⇒` / `Σ` / `=`, an arrow, a brace) so "these combine
  into this" is unmistakable; **(3) distinguish it** by weight/size/colour (the focal accent, a heavier
  stroke). The same pattern applies anywhere parts make a whole: a resultant among component vectors, a
  total beside its bars, an average among samples, a centroid among points, the merged result after a
  fan-out. *(Special case of Contrast + Proximity: the summary element earns its own visual level and its
  own region.)*
- **A textured / line / grid BACKGROUND must not compete with line-heavy CONTENT.** A faint grid, hatch,
  blueprint frame, or line motif is good chrome *behind ordinary content* — but when a slide's content is
  **itself dense line-work** (a pulse-sequence timing diagram, a k-space line stack, a wave/axis plot, a
  many-line schematic, a ruled table), the background lines **blend into and muddle the figure** (same
  hue, same orientation → the eye can't separate signal from texture). On such slides: **(a) suppress the
  background motif** — a grid-free variant of the same template (keep the frame/footer so the chrome stays
  consistent); **or (b) seat the figure on a solid/frosted panel** that masks the motif behind it; **and/or
  (c) strengthen the figure's line weight / contrast** so it clearly dominates the texture. The motif's job
  is atmosphere *behind* content — when the content is the same visual language as the motif, the motif has
  to yield. (Generalises to any motif-vs-content clash: dots behind a scatter, hatch behind hatched bars.)
- **Block fill must FIT the background — on a rich/image background use SEMI-TRANSPARENT (frosted) blocks,
  not flat opaque panels.** A solid opaque card is right on a *plain/flat* background. But on a **textured,
  photographic, 3D, or generated-plate** background a fully opaque block reads as "pasted on" and
  disconnected from the scene. Give content blocks a **slight transparency** so the background shows
  through (~30–45%) and they read as part of it — a **frosted-glass** treatment: a low-alpha tint of the
  block colour + a subtle lighter **rim**, via `deckkit.glass_card` or `box(grad=[(0,tint,α),(1,tint,α)])`
  with **α ≈ 0.55–0.72**. **Contrast stays non-negotiable:** the tint must still carry the text at ≥4.5:1
  — if the background has a bright/busy patch under a block, raise the block's α (more opaque) or
  darken/strengthen the tint where the text sits (and keep the deck's gentle background scrim). Use **ONE
  block treatment deck-wide** so every card reads as the same material — and design the **block colour +
  rim to harmonise with the palette** (a dark deck → a dark glass tint + a faint light/accent rim; a
  light deck → a white glass tint), never a colour that fights the background.
- **TWO background ZONES on one slide must HARMONISE — don't stitch a dark panel to a light one.**
  When a single slide carries two background fills (a split-colour canvas, a coloured side rail beside
  the body, a header band over the content), the two zones should be **tonally cooperative** — the same
  hue family at two values, analogous neighbours, or one a soft tint of the other — so the slide reads
  as ONE surface. A hard **dark-panel-beside-light-panel** (high value contrast between two big
  background areas) looks like two slides stitched together and reads harsh, even when each half is fine
  alone. Prefer two *similar / well-cooperating* colours; if you truly need a dark zone against a light
  one, bridge them (a shared accent hairline, a gradient seam, or narrow the dark zone to a rail so it
  reads as an accent, not a half). *(Different from a deliberate full-slide colour FLOOD — one
  background across the whole slide as a WOW beat — which is fine; the rule is about two zones **fighting
  within** one slide.)*
- **Vary the canvas VALUE across the deck for beauty — with NATIVE means, no image tool needed.** A
  flat fill on *every* interior slide is safe but can feel monotone; a deck that never changes its
  background value reads flat (the `FLAT RHYTHM` lint measures exactly this). Give a few beats a
  different feeling using code alone: a **tonal-shifted section divider** (a deeper/richer fill on the
  divider pages), a **subtle vertical gradient** on a hero slide, a **duotone photo/texture band**
  (`image_fx.duotone` on a license-clear or computed image), or a **deliberate accent-flood WOW**
  (`box(0,0,W,H,fill=…)` behind light type). **Dose it like the WOW — a few tasteful beats, not every
  slide different** (and keep each such slide's zones harmonised, per the rule above; a varied deck is
  not a clashing one). This is *canvas* variation, not loud chrome — the frame/footer stay quiet.
  **And a value event must RECUR or bookend — never appear exactly once mid-deck.** One lone slide
  in a different canvas value reads as a mistake, not rhythm (the `ONE-OFF CANVAS FLIP` lint catches
  it): tie every flip to a repeating family (all dividers dark, dark cover+closer bookends). On a
  generated-identity deck the rule is stricter still — see generated-template.md: rhythm comes from
  imagery strength, never from abandoning the plate on one page.
- **No large empty region — fill the slide, balanced.** A slide that's mostly blank (content
  huddled in one corner or the top third, a wide empty band down a side or across the bottom) reads
  as unfinished — don't ship it. **Default fix: ENRICH the content** — add the supporting detail,
  example, sub-point, caption, mini-diagram, or data the point actually deserves so the slide earns
  its space with *substance*. Then, secondarily, **enlarge the figure/hero element** or **redistribute
  the blocks** so the content occupies the slide evenly. Only if a slide genuinely has too little to
  say — even after enriching — **merge or cut it** (a presented deck that's over-full wants *more*
  slides, never emptier ones). Whitespace is a *deliberate* breathing tool around content — not a
  large leftover void. *(On a **fixed surface** — poster, single-slide infographic, one-pager — you
  can't "add a slide": organise the density into clear regions/columns with strong hierarchy instead;
  the no-large-void rule still holds within the canvas.)*
- **Never inflate an oversized block to *fake* a full slide.** Filling space means more *content*,
  not a bigger empty *container*. The anti-pattern: a huge card/callout/panel holding a single short
  line of small text, stretched tall or wide just to cover a gap — it reads as a placeholder, not a
  finished block (small font swimming in a big box is the dead giveaway). Two correct fixes, never the
  inflate: **(a)** if the point deserves more, *add real content* to the block (a second line, a
  figure, a sub-list) so the box is genuinely full; **(b)** if it's a one-liner, **shrink the box to
  hug the text** (per "Blocks hug their text") and use the freed space for another element or a
  balanced margin. A block's size must be *earned by its content* — never a one-line label in a block
  sized for a paragraph.
- **Depict multiplicity, don't DUPLICATE it — show the pattern, not N copies of the same content.**
  When a slide has many units that are **identical except for an index/label**, do **not** render all
  N as full blocks. Repeating the same words N times adds **zero information**, eats the whole canvas,
  and *buries the actual message* — the audience re-reads the same label N times instead of grasping
  the structure. This pattern shows up in *any* domain: parallel compute/model units (N attention
  heads, N stacked layers, K service replicas, an M-model ensemble), repeated infrastructure (12
  identical microservices, a rack of identical nodes), repeated process/org units (N regional teams
  running the same playbook, N identical pipeline stages), or a long set of same-shaped items. Smart
  depiction:
  - **Representatives + ellipsis + count.** Show 2–3 representative units, then `…`, then the last one,
    and state the total — e.g. `unit 1 · unit 2 · … · unit N` with a **`× N`** badge — so "there are N
    of these in parallel" is read at a glance. (A single card with a stacked-shadow "deck of cards"
    look, or a `×N` multiplier, works too.)
  - **Say the shared detail ONCE.** The content common to every unit (whatever each one *does*) belongs
    in **one** caption under the group, or on the *representative* only — never copied into every block.
  - **Spend the saved space on what actually differs / what matters** — almost always the *structure or
    flow* the multiplicity feeds into (how the parallel units fan out and then combine/aggregate), not
    the enumeration of clones. Make that flow the slide's hero.
  - **When to show all N instead:** only when each unit has **genuinely distinct content** (different
    labels, values, or roles), or N is small (≲4) *and* showing every one is the point. Identical-
    except-index + large N ⇒ abstract it. This is also the *right* fix for a too-empty row — fill it
    with the real flow/structure, **never** by cloning a block to occupy space (that compounds both the
    filler and the duplication faults). Plan this with `deckkit.repeat_row()` (representatives + `…` +
    `×N` + one shared caption).
- **Overlap vs layering — the one distinction, so "no overlap" and "layer glass on a glow" never
  conflict.** Two definitions, applied everywhere (rules, lint, critic):
  - **Collision = two SEPARATE blocks intersecting, neither contained in the other** (a card over a
    table, a callout over the footer, text crossing out of its box, a diagram node poking past its
    panel). **This is UNACCEPTABLE — always a flaw, never "close enough."** Separate blocks need a
    visible gap; they never touch or overlap.
  - **Layering = a child fully INSIDE its parent** (a label on its card, a scrim over a photo, a glow
    *under* a glass card, a header band on its card, an icon in its tile). This is **intentional and
    correct — not overlap.** The "no-overlap" rule forbids *collisions*, not containment.
  So the test for any two intersecting shapes: *does one fully contain the other?* Contained →
  intentional layering, fine. Not contained → collision, fix it (re-anchor via `content_band`/`vstack`/
  `bottom_callout`, resize, or add a gap). `lint_deck.py` encodes exactly this (containment excluded;
  the footer zone has no containment escape).
- **Mind the gaps between blocks — even and intentional.** Equal gaps between repeated/adjacent
  blocks (cards, chips, rows, list items) — derive them from `columns`/`rows`/`vstack`, never
  eyeball; one gap visibly larger than its neighbours reads as careless. Adjacent blocks always need
  a **visible, consistent** gap — never touching *and never a near-zero sliver*: make it read clearly
  (**≥ ~0.12in, ~⅓ `GUTTER`**), never wildly uneven. A gap far smaller than the slide's own margins
  reads as cramped even when nothing technically overlaps — the classic cause is a stacked pitch
  hand-picked just above the block height (panels at pitch 1.04, height 1.02 → a ~0.02in seam).
  **Derive the stack pitch from the region** (`rows(n)` / `vstack(..., bottom=…)`), never `block_h`
  plus a tiny nudge. (The floor stays ~0.12–0.13in; the build-time lint warns `SLIVER_GAP` only
  clearly below it — a 0.005–0.10in seam — so a rule-compliant gap never warns.)
- **Group by proximity — the gap BETWEEN groups must be clearly larger than the gaps WITHIN a group.**
  When you stack labelled groups (a stat's label + big value + caption, then the next stat; or stacked
  cards), the space *separating the groups* has to beat the space *inside* a group — otherwise one
  group's caption crowds the next group's label and the eye can't tell where one ends. Rule of thumb:
  **inter-group gap ≥ ~1.5–2× the intra-group line spacing.** The classic tell (seen on stacked
  stat cards): the `≈40% / 改造前…` block sits almost flush against the `获客成本 / −22%` block below —
  add a clear divider of whitespace between the two stats. Build stacked groups with `vstack`/`rows`
  so the between-group gap is set deliberately, not left to wrap.
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
  are the natural beat markers.) Vary the
  **component FORMAT too, not only the protagonist** — the rounded-card / panel grid is the reflex that
  makes a deck read as one template, so don't default every content slide to it; rotate in a timeline, a
  big-numeral / stat row, a pull-quote, a chart, a diagram island, a 2×2 / quadrant, a step-list, a
  before/after, or a comparison table as the content invites. If more than ~40–50% of the content slides
  are the same block type, that's over-reliance — rework the weakest into the form their content wants
  (taste, not a quota).
- **Avoid the AI-slop tells (VISUAL).** A handful of choices instantly read as machine-generated filler — name
  and avoid them: full-screen rainbow / mesh / purple-to-blue gradients; emoji in titles or as bullet
  markers; ✅/🚀/🔥 decoration; the rounded-card-with-a-left-border-accent everywhere; three-near-identical
  "feature cards"; **a multi-colour decorative strip / spine / rainbow rule stamped on every slide**
  (palette-as-ornament — the palette shows through the content, not through a swatch bar);
  **a full-width takeaway strip parked at the bottom of nearly every page** (rotate the slot —
  architecture-rotation rule); **every element panelled on an already-calm canvas** (free at least
  a third of the protagonists); **chips/rosters/pillars naming tools or categories with NO icon
  family** (self-verify (g));
  over-exposed default fonts used without intent; and **fabricated specifics** (made-up
  stats, fake quotes, invented logos). *(An invented **fake of a real entity's official logo** is the tell; a clearly-flagged designed **wordmark** stand-in — used only when no real logo exists or could be found — is sanctioned, see `review-rubrics.md` / `image-generation.md` "Logo / brand mark".)* Meta-heuristic: **when you feel the urge to *add* something to
  make a plain slide "look nicer," that urge is usually the slop signal — subtract instead** (more
  whitespace, one stronger element) and fix the layout, don't decorate it.
- **Write like a human presenter (VOICE) — the WORDS betray AI as fast as the visuals.** Write each line
  the way a sharp person in the field would *say* it to the room, not the way an LLM defaults. Cut the
  inflated / promotional vocabulary that clusters in AI text — *leverage · unlock · empower · robust ·
  seamless · cutting-edge · game-changer · pivotal · crucial · underscore · landscape · delve · "a
  testament to" · "marks a pivotal moment" · "in today's fast-paced world" · "it's worth noting"* — and
  replace each with the **concrete specific it's dodging** (not "leveraging synergies to drive impact"
  but "auto-routing cut support tickets 30%"). **Don't force the rule of three** — not every slide is 3
  bullets / 3 columns; use the count the content actually has (2, 4, 5). **Don't reach for formulaic
  section names** ("Key Takeaways", "Challenges & Future Prospects", "Deep Dive", "Overview") — name the
  slide for its real point. Give the deck a **point of view** (an assertion, a recommendation), not
  sterile both-sides neutrality. **The test: read each line aloud — would a real expert actually say this?**
  If it sounds like a press release or a textbook abstract, rewrite. *(Em-dashes in **moderation** are fine
  — it's **over-reliance** on them and on reflexive parallel triads that reads as machine. Language-specific
  tells, incl. 中文 translationese (的-chains, 进行/实现-nominalisation, 破折号成瘾), live in `multilingual.md`
  "Write like a human"; the critic enforces this via `review-rubrics.md` §3.)*
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
  every connector label stays consistent. Keep the label in the OPEN GAP beside the line, never wrapped in
  an opaque chip that stands out over it — only a subtle translucent backing if it must cross a busy area
  (a background-colour knockout on a plain slide is fine). Mirrors the SKILL §5 render self-check.
- **Connectors point the way the flow actually moves.** An arrow between two blocks must run
  *along the flow*. Side-by-side blocks → a left/right arrow; **vertically stacked** blocks
  (problem→solution, before→after read top-to-bottom) → a **down/up** arrow
  (`deckkit.arrow(..., direction="down")`). A sideways arrow squeezed between two
  stacked boxes is a classic wrong-direction tell — match every connector's orientation to
  the layout, and check it in the render.- **Connector SHAPE carries meaning — straight for adjacent flow, elbow/U for everything else.**
  A **straight** arrow means *direct flow between two adjacent nodes*. A **feedback/repeat loop, a
  return path, or any link between NON-adjacent nodes** is an **elbow / U-shaped** connector — build it
  with `deckkit.elbow_connector(pts=…)` (orthogonal segments) or `deckkit.loop_path(x_from, x_to,
  y_row, y_drop)` (the U that drops under a row for a "repeat" arrow), never a straight line shoved
  diagonally across the boxes in between. The classic miss is drawing a *repeat/feedback* edge as a
  straight arrow: it reads as forward flow and crosses other shapes. So **stroke** encodes the link's
  *kind* (solid=required · dashed=optional · dotted=feedback) and **shape** encodes its *path*
  (straight=adjacent · elbow/U=loop / return / non-adjacent).
- **Equal spacing for repeated elements.** A row or column of blocks joined by connectors
  must have **equal gaps and equal connector lengths** — hand-placing each block's `x`/`y` and
  each arrow produces visibly unequal spacing (one arrow longer than the next), which reads
  as careless. Derive the blocks from one grid: **`deckkit.columns(n, gap=...)` for a
  horizontal row**, **`deckkit.rows(n, gap=...)` for a vertical stack** (both return equal
  cells with equal gaps; pass `slide=s`). Then drop each connector **centred in the equal
  gap** rather than eyeballing positions. And **adjacent blocks always need a visible gap
  between them — never let two boxes touch** (a stacked pair whose bottom edge meets the next
  box's top edge reads as one merged block); leave a clear `gap` (the `rows`/`columns` helpers
  enforce one). A zero- *or near-zero* (e.g. ~0.02in) gap seam between blocks is a common hand-placed-coordinate
  bug — derive the pitch from `rows`/`vstack` rather than picking a pitch (1.04) that barely clears
  the block height (1.02).
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
- **Muted register ≠ low contrast — mute the HUE, not the VALUE.** The most seductive contrast
  failure is systematic, not accidental: an elegant tonal palette (warm greys on cream, dusty
  gold on paper, tone-on-tone teal) where *every* kicker, caption and pagination lands at
  2.4–3.3:1 — harmonious up close, invisible from the back of a room. Desaturate toward the
  canvas's hue family but keep the VALUE distance: a muted warm grey can be `#6E6557` on cream
  (4.6:1) instead of `#9A927F` (2.7:1) and read just as calm. Compute the ratio for every planned
  ink×canvas pair at design time; when a whole chrome family sits below floor, darken the family,
  don't grant it an exemption for elegance.
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
- **Content text must be visibly SMALLER than the slide title — never equal, never larger.**
  The size order is fixed: slide **title** > section/sub-heading > **body/content** > caption/fine
  print. A body or callout set as large as (or larger than) the title flattens the hierarchy and
  reads as amateur — the eye can't tell the headline from the supporting text. Keep a clear step
  between levels (e.g. title ~24–30 pt, body ~16–18 pt on this canvas — a ~1.4–1.8× ratio), and that
  includes **equations, big numerals, and chip/card labels**: an equation or a stat value may be the
  slide's hero and so *can* exceed body size, but a *supporting* formula or label sits at content size,
  still below the title. Check it in the render: if any body/formula/label glyph is as tall as the
  title's letters, shrink it.
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
  not "Take home"; a status update might end on "Next steps". Use the label **in the deck's
  language** (a Chinese deck closes on **结论 / 总结 / 下一步**, not the English word) — the rule is
  register-appropriate naming, not the English string.
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
