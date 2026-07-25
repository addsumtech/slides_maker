# Asset production — evidence manifest, figure crops, equations, generated & sourced imagery (Step 2–4)

## Evidence manifest — probing asset geometry before design

With the **Content plan approved**, first build the **Evidence manifest** — so the art director
plans geometry with its eyes open, not blind to a 2400×700px figure destined for a half-column.
When the approved plan's *Visual source* column names assets that exist or are locatable, emit
one READ-ONLY line per named asset: `asset | locator | WxH (px/pt) | aspect class (wide >~1.6 /
squarish / tall <~0.65) | table RxC | value range (optional)` — probed via PIL/`sips` for image
files, `extract_pdf.py figures` bboxes for in-PDF figures (note in the manifest that the
auto-bbox is the plot-panel extent, so the AR is an estimate), and header/row counts for CSVs.
Probing NEVER materializes crops/equations/plates — asset-prep still runs only AFTER the design
plan is approved (`agents/asset-prep.md`, unchanged); an unlocatable or to-be-generated asset is
listed "dims unknown", and a no-asset deck skips the manifest entirely.

## Per-slide content-image opt-in — the three guardrails and the REFERENT RULE

**The per-slide content-image opt-in is a CROSS-CUTTING choice, available on EVERY deck** — it is
*not* tied to the template choice and is *separate from* Q1's "generate a template with an image
tool" path (which makes the visual identity). Offer the opt-in whenever an image tool OR web access
for sourced photos is available — generation rows need the tool; sourced rows need only the
Commons/Openverse/press-kit search — regardless of how the deck was templated: a **registered**, **provided**, **clean**, or
**generated** template can all carry generated *content* images. Three guardrails the art director
enforces and the checkpoint shows: **(a) each proposed plate is *content-related* — it depicts THAT
slide's actual subject, never generic "fancy" filler** (`image-generation.md`); **(b) it is
SMART about where — plates only for the few slides that genuinely earn one, NEVER every slide, even
when the user has opted into image generation** (the dose rule holds on photo-friendly topics too —
only the PRESSURE inverts: a travel/city deck's temptation is wall-to-wall photos); and **(c) the
REFERENT RULE picks the source for content images** (`references/image-generation.md` "Sourced real
imagery" — the owning section: token grammar, scope carves for generated-template identity plates
and cover mood, tie-breaks, and the `searched, none found → …` fallback rungs): a real-and-specific
subject (a named place, real product, real person) gets a REAL license-clear sourced photo —
generation *claiming photographic reality* of a real thing is a fidelity bug, while a declared
stylized illustration is a nameable deviation; a generic-concrete subject may be generated; an
abstract subject gets native forms, not photos. Every image row carries its source token per that
grammar. The user then approves which (if any) are
generated or sourced. Fold in the user's design edits, then set up the canvas (Step 3).

## Figures — cropping, PDF extraction, and panel-grid reassembly

  - **Never clip the figure's OWN parts. Crop the complete SEMANTIC object, not an arbitrary
    rectangle.** The legend, colour bar, axis titles/labels/ticks, units, **error bars / CIs &
    significance markers (`*`, p-values)**, **panel-strip headers**, **panel labels `(a) (b) (c)`**,
    a sub-plot's own x-axis labels, and the outermost rows/columns are all *part of the figure* —
    losing them is worse than showing the figure a touch smaller. **If one part is needed to read
    another** (a colour key, a shared legend/axis, a side-input to a diagram), keep them together.
    After every crop **and** after placing/scaling a figure on a slide, **re-view the result** and
    confirm nothing of the figure is cut off (a half-cut legend at the top edge is the classic miss).
    **A small margin, not blank padding:** keep just enough margin that nothing sits *flush* (a tick
    label *touching* the boundary is already too tight) — but no *fat* blank border either, since the
    figure is placed with `picture(fit="contain")` and a wide white margin makes it float small on the
    slide. Crop **close to the figure's real content**: a small even margin, which is *not* the same as
    cropping flush (flush is still a bug). When tick labels are **rotated** or a legend/colour-bar sits
    *outside* the plot, extend the crop to **include those elements fully** — that extra room is to
    *fit* them, not to pad with whitespace.
    - **🔴 The auto-detector's bbox captures only the PLOT PANEL — expand beyond it.** A plotting
      library (ggplot / matplotlib / seaborn) places the **axis titles, tick labels, panel-strip
      headers, and legend OUTSIDE** that panel rectangle, so cropping to the detected box (or an
      eyeballed fraction near it) **silently drops them** — the recurring "figure has no x-axis
      labels" / "axis title sliced in half" bug. Treat the detected bbox as the *inner* extent and
      **grow the crop outward** (down for the x-axis title + tick rows, left for the y-axis title,
      right/bottom for the legend) until every peripheral part is inside **with a small margin**.
    - **🔴 Zoom EACH of the four edges after every crop — a margin, not flush.** Don't just glance
      at the whole crop; inspect each edge close-up and confirm each element (axis title, outermost
      tick label, legend entry, panel border) is **fully present AND has clearance from the edge**.
      An element *flush to* the image edge reads as clipped once the figure sits on a coloured slide
      (its baseline/descenders butt the boundary) — treat flush the same as cut and re-crop.
    - **🔴 A legend you add ON the slide does NOT substitute for the figure's own axis labels.**
      Adding a colour legend beside a figure is fine, but it must not *mask* an over-crop that shaved
      the figure's own x-axis category labels off the bottom: the placed figure must be **self-
      contained** (its own axes readable) first; a slide-legend is an optional aid on top, not a
      replacement for the axis the crop dropped.
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

## Charts from raw data, GIFs, and computed domain visuals

- **Animated results (GIF / looping animations) → insert the GIF itself with `deckkit.gif()`**,
  never reduce it to a single frame. **No GIF provided but the content IS inherently motion (a process /
  algorithm / optimisation, a reconstruction or simulation converging, a transformation, cine/4D, a
  rotating 3D)? You MAY generate one — `deckkit.make_gif` from frames you compute in the asset step —
  but SPARINGLY:** only when motion conveys what a static frame can't (the "When a GIF earns its place"
  rubric in `animation.md`; the slide-design agent makes the call), a deck carries **zero-to-a-few**
  purposeful GIFs (never one per slide — keep concepts/tables/equations/charts static), and a generated
  GIF must animate a **real computable change, never fabricated motion**. It embeds the real animated GIF (every frame preserved;
  PowerPoint and Keynote **loop it in slideshow**), places it **whole and undistorted** (`contain` —
  a square cine clip is never stretched), sets alt-text, and **warns on a heavy file** (a big cine GIF
  bloats the `.pptx` and stutters live) or a single-frame still. For time-resolved / 4D / cine /
  training-run results — in **any deck** (a product/UI demo in a pitch, an interaction in teaching, a
  data-viz loop, a simulation or time-resolved result in a research/status deck) — a frozen frame
  throws away the point. Integrate it like a figure: often the slide's **hero** (assertion
  title + a one-line *"what to watch"* caption), or beside its quant panel in a `columns(2)` split;
  two GIFs for before/after. **The first frame matters:** the render, the static critic, a **PDF/print
  export**, and edit view all show frame 0 (a GIF has no separate poster) — so verify it's
  representative with `deckkit.gif_poster(path, "first.png", frame="first")` and, if it's a blank /
  black / loading frame, get a GIF that *starts* on a meaningful frame; `frame="auto"` extracts a
  representative still to hand the critic. Don't misrepresent the dynamics (no meaning-changing frame
  drops/speed-ups). Tell the user at hand-off that it animates in **slideshow** (still in edit/print).
- **Data but no figure yet → make the chart, don't dump numbers.** If the source gives
  raw data (a CSV, a metrics table, logged numbers) but no plot, turn it into the chart
  that makes the comparison obvious rather than typing a wall of figures — generate it
  with matplotlib or another available figure-making workflow — then place the result
  *whole*, with a legend + takeaway, like any other figure. A bare number table is the
  weakest way to show a trend. **Pick the chart TYPE that fits the argument, not always a
  bar** — `references/data-viz.md` has a roster + ready recipes. **For a deck in ANY non-Latin language
  (CJK · Cyrillic · Greek · …), or when the user will edit the chart, use an EDITABLE native chart** —
  `deckkit.native_chart` (line/column/bar + stacked/area composition kinds) / `deckkit.native_dual_axis` (two-scale A↑ vs B↓): a real
  PowerPoint chart that renders non-Latin labels via PowerPoint's fonts (**no tofu**) and is
  click-editable (pass `font=` the script's font). For the richer raster types
  (`scripts/designed_charts.py`: donut+KPI, dumbbell, slope, bubble+trend, Pareto) pass your palette /
  `dark=True` (and `font=<the script's font>` on a non-Latin deck). Either way: a **single highlight** on the one series
  that matters + a `deckkit.takeaway_rail` "so-what". For 3-6 headline metrics use
  `deckkit.scorecard` tiles; key a ranked list to a chart with `deckkit.leaderboard`.
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
  - **Make the plot actually look CORRECT (then view it).** A computed plot is only faithful if it
    *renders* right: **(a) sample continuous curves finely** — a smooth function must look smooth, so
    use a dense `np.linspace` (a few hundred points / ≥~10× the highest frequency), never the integer
    index steps; plotting a high-frequency sine at integer `x` *aliases* it into jagged zigzags (the
    classic "sin curve looks weird" bug). **(b) The legend must NOT overlap the data — treat this as a
    rule, not a nicety.** `loc='best'` and any in-axes corner routinely land the legend ON a curve on a
    full/busy plot. The reliable fix is to put the legend **OUTSIDE the axes**: to the right
    (`loc='center left', bbox_to_anchor=(1.02, 0.5)`) or **above** (`loc='lower center',
    bbox_to_anchor=(0.5, 1.0), ncol=…`); use an in-axes corner ONLY when that corner is provably empty.
    For a **dual-axis / twin-axis** plot don't draw two separate legends (they collide with each other and
    the twin ticks) — collect both handle sets and draw **one combined legend above** (`h1+h2`,
    `loc='lower center', bbox_to_anchor=(0.5,1.0), ncol=2`). It can't *always* be perfect on a dense plot
    — when no empty region exists, going outside is the answer, never overlapping the data. *(In a tiny plot cell where an outside legend would shrink the axes too far, drop the legend and name the series in the native slide caption, or keep it inside a provably-empty corner.)* **(c) Always
    view the rendered PNG** and fix anything off (aliasing, clipped labels, an **occluding legend**, a
    squished aspect) — a wrong-looking plot misleads even when the math is right.

## Brand logo / wordmark, and the SVG icon family

- **Brand logo on every page when the deck is ABOUT one company / institution / product.** A pitch,
  product/launch, company or stakeholder readout, or a single institution's report reads as more
  credible when that entity's **real logo is present on every slide** in a **consistent position** —
  the way real corporate decks keep a mark in a fixed corner (top-right is the usual default; move it
  to whichever corner the title/figures/motifs leave free, but keep it the same everywhere so it never
  jumps). Use `deckkit.logo(slide, path, corner=..., h=...)` per slide on clean/generated decks; on a
  **provided/registered template** the branding usually already lives on the layouts (don't double it).
  Source the mark in order, stopping at the first you can get: the **real** logo (an image asset the
  content-planner found or the user gave) → else a clean designed typographic **WORDMARK** in the deck's
  own type — build it with `deckkit.wordmark(text, out_path, …)` then place it with `logo(slide, out_path,
  …)` (**the sanctioned default** when no real logo was found, per `references/image-generation.md`
  "Logo / brand mark") → and if even the wordmark doesn't fit the design, **ask the user for the
  asset — never ship placeholder text on a slide** ("logo here" IS the meta-annotation PRE-FLIGHT 8
  and the critic treat as a blocker). Never a
  faked/recolored replica of a real entity's official mark. This does **not** apply to multi-organisation decks (surveys, landscapes) or
  neutral academic talks — there, name entities inline. Full rule + the no-apply cases in
  `references/image-generation.md` ("Real brand / product assets come first").
- **SVG icons — ONE coherent open-licensed family, recolored, used with restraint (full rules — the
  jobs icons do, the rule-of-thumb, + five quality marks — in `references/icons.md`).** An icon must
  **reduce cognitive load, not decorate**: use one only where it does a real job (label a section /
  category, mark a repeated entity, guide reading order, anchor a sparse slide, flag status) and it
  passes the **rule-of-thumb** — answers *what is this / what does it do / why pay attention* before the
  words; else cut it. **Don't hand-draw a set** (inconsistent = amateur) and don't sprinkle them as decoration. **Fetch from
  one family** (Tabler/Lucide/Phosphor MIT-ISC; `simple:` CC0 for brand/tech logos) via
  `scripts/icons.py` `icon_png(spec, out, color=ACCENT)` — it fetches, **recolors to the deck palette**,
  and rasterizes to a transparent PNG (python-pptx can't embed SVG reliably; rasterizing renders the
  same everywhere). **Don't default to a flat monochrome drop — vary the *treatment* to fit the deck**
  (full gallery in `icons.md` "Treatments"): render it **duotone** (`phosphor-duotone:`) or
  **gradient-filled** (`icon_png(..., gradient=(c0,c1))`), and place it in a styled container —
  `deckkit.icon_tile()` (circle/squircle/square × solid/gradient/glass tile, optional sheen),
  `icon_badge()` (ring badge), `icon_ghost()` (oversized faint watermark), `icon()` (bare or tinted
  tile), or `icon_card()` (upper-left feature card). A duotone glyph on a gradient/glass disc, colour-
  coded per category, is how polished decks look "designed" rather than clip-arty — but keep **one
  treatment across siblings** (vary only the hue to colour-code). The
  five quality marks (`icons.md`): **semantic fit** (the metaphor matches what it labels), **colour-coded
  per category** (in a multi-category layout each category its own hue from `palette(n)`, carried by the
  icon + label + tint — not one global accent), **contrast** (bright on dark / saturated on light, a
  `disc=` tile if needed), **consistent** family/size/position across siblings (size **≤ the title**,
  ≈0.32–0.5 in), and **style matching the deck** (outline vs filled). **Always pair an icon with a text
  label.** Cache in `~/Downloads/<deck>/assets/icons/`. **Icons fit any topic** — the libraries are
  diverse enough to match any register, so **match the style/weight and use fewer**, rather than ship a
  mismatched zoo or one-per-bullet clutter (the flaw is wrong-style/decoration, not icons by subject).

## Equations and inline math

- **Equations — 🔴 default to EDITABLE native math (`equation_native()`); raster (`equation_png()`)
  is the fallback for 2-D layout only.** A formula the audience reads should default to
  **`deckkit.equation_native(slide, x, y, w, h, latex)`** — it renders a LaTeX-subset as **real,
  click-editable TEXT runs** (italic variables · upright operators · true sub/superscripts · Greek &
  math glyphs) in a math font, so it stays **editable** AND renders the same in PowerPoint / Keynote /
  LibreOffice / PDF — *as long as the math font is present* (see below). This is the editability users
  expect — a raster formula is a *frozen image they cannot fix*, so don't ship one where native math
  works. Reach for **`equation_png()`** (rasterised LaTeX) for math `equation_native` can't render: it
  supports a **common LaTeX subset (linear math)** and **raises `NotImplementedError`, naming the
  construct, on anything else** — both **2-D layout** (`\frac`, matrices/`\begin`, `\sqrt`, `\overline`,
  `\binom`, over/under-braces) **and any unmapped command** (`\mathscr`, `\overrightarrow`, `\stackrel`,
  `\models`, …). It does NOT silently mangle — but a *display-style* stacked sum/integral with bounds
  (`\sum_{i=1}^{N}`) still renders *inline* (bounds beside, not stacked), so use `equation_png` when the
  stacked 2-D look matters. **Always view each native equation in the render** and switch that one
  formula to `equation_png` if a glyph is missing. *(A true PowerPoint OMML equation OBJECT is editable
  in PowerPoint but **invisible in the LibreOffice render & PDF export** — so it is NOT the default;
  native runs are verifiable in the loop.)* **Never** paste Unicode super/subscripts (ᴴ ᵀ ᵣ) — tofu.
  **Math font (a real dependency):** `equation_native` needs a math font for ℒ Σ ‖ … (`deckkit.EQ_MATHFONT`
  = `'STIX Two Math'`; set `'Cambria Math'` for Office portability). **STIX ships on neither stock macOS
  nor Windows, and Cambria Math needs MS Office** — so on a machine with NEITHER, the math glyphs **tofu**
  in the render/PDF: install the math font, or **fall back to `equation_png` (font-independent)** for that
  deck. **Flag this dependency at hand-off.** For `equation_png` pick its `mathfont` (`'cm'` formal ·
  `'stixsans'` crisp).
  - **Size the formula to the CONTENT text, not to fill the slide.** A formula's glyph
    height should read like the deck's **body/content** size — *never* blown up to span
    the slide width (which oversizes every glyph and breaks the title→content hierarchy),
    never shrunk illegible. On the 10×5.625 canvas, set `equation_png`'s placed **height**
    so a single-line equation lands ≈ **0.22–0.32 in** (≈ body text); scale *height* (not
    width-to-fit) and keep the *same* target height across every equation in the deck so
    they're visually consistent. The formula may be larger **only when it IS the slide's
    hero** (a method slide whose one point is the equation) — otherwise it sits at content
    size. Always confirm in the render that the formula glyphs aren't bigger than the slide
    title's letters.
  - **Even a single variable or symbol uses math format — and stays editable.** Any
    variable/symbol that appears in running text or a bullet (e.g. *x*, *λ*, *σ*, `Aᵀ`,
    *R*(*x*)) must be set in **proper math style** — italic variable + real sub/superscript
    — not typed as plain upright body letters and never as Unicode super/subscripts. For one
    or two inline symbols use **`eq_par()`/native runs** so the symbol stays **click-editable**
    and inherits the surrounding body size; reach for **`equation_native()`** for a full expression
    (still editable), and `equation_png` only for 2-D math. Keep the LaTeX source in the build script
    either way — it's the reproducible source of truth (for a raster it's the *only* way to "edit"; for
    native math it's what you re-parse).
- **Formulas → TYPESET math (editable `equation_native`; `equation_png` for 2-D), never a cropped
  image.** Unlike a figure or table (cropped *whole* from the PDF with `extract_pdf.py`), a needed
  equation is **re-typeset**: write it as LaTeX and render with **`equation_native()`** (editable native
  runs) — or `equation_png()` for 2-D math. A cropped formula bitmap is low-res, carries the source's
  font/background, can't be restyled to the deck, and clips — a typeset one is crisp at any zoom and
  on-brand.
  - **From a paper → transcribe** the formula precisely (don't alter symbols/indices).
  - **From code/other material → derive** the formula the code implements (a loss, update rule,
    metric, transform, a pricing/unit-economics calc) when the content-planner judges it shows the
    idea more directly than prose — useful for **any code-sourced technical deck** (lab meeting,
    defense, conference method talk, teaching, an eng status readout). It must be a *correct*
    expression of what the code computes (verify against the code), not invented or wrongly-simplified.
  - Either way the **fidelity rule applies** — verify the rendered math against the source.
  `extract_pdf.py` is for figures/tables; formulas go through `equation_native` (editable) / `equation_png` (2-D).
