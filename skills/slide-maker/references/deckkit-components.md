# deckkit components — the form catalogue to build from, not hand-roll (Step 4)

## Deckkit helper catalogue — every component, by job

The helper set, by job:
- **Chrome:** `title_bar`/`content_slide`, `footer`, `editorial_header` (caps eyebrow + title +
  hairline), `part_eyebrow`/`page_marker` (mono eyebrow + page marker), `logo` (persistent
  brand/institution/product mark in a fixed corner on every page — see the brand-logo rule below).
- **Safe layout — measure or anchor, never hand-pick a y:** `columns`/`rows` (equal **or
  `weights=`-proportioned** split panels — a measured 1/3–2/3 or rail+main split — symmetric outer
  margins either way), `content_band` (the SAFE rect below title / above footer), **`bottom_callout`**
  (footer-safe bottom takeaway — anchors to the band, grows UP, can't collide), **`vstack(…, bottom=)`**
  (measured stack: equal gaps + no overlap by construction, errors at build time on overflow) with the
  `measure_callout/measure_bullets/measure_text` helpers, **`spaced_centers`** (evenly-spaced marker
  centers for a timeline / tick row / numbered steps, **inset at the ends so a centered caption stays
  co-centered with its end marker** — use it instead of hand-rolling a row of dots+captions, which
  desyncs the first/last caption from its dot near a slide edge; `timeline` already uses it),
  `picture` (`fit="contain"` keeps edges /
  `"cover"` crops), `make_gif` (GENERATE a looping GIF from computed frames) + `gif` (embed the animated
  GIF, undistorted + size/still warnings) + `gif_poster` (extract the first/representative frame to
  verify what the render & PDF export show) — generate → embed → review, `icon`/`icon_tile`/
  `icon_badge`/`icon_ghost`/`icon_card` (place an open-licensed SVG icon — recolored + rasterized via
  `scripts/icons.py`, which also does **duotone** weights + **gradient-fill**; `icon_tile` is the
  versatile container — circle/squircle/square × solid/gradient/glass tile, `icon_badge` a ring badge,
  `icon_ghost` an oversized faint watermark, `icon_card` the upper-left feature-card pattern; vary the
  treatment to fit the deck — see `references/icons.md` "Treatments"). *(These exist so you never
  hardcode a low `y` — the recurring overlap/footer bug.)*
- **Text & blocks:** `bullet`, `callout` (auto-grows), `chip`, `modbox` (a labelled MODULE box —
  reach for it as the node when mapping architecture modules / code files / system parts joined by
  `connector`, where a plain `node` is too bare; role word + optional filename/tag), `arrow`, `table` (highlight
  the key row), `code_block`, `hrule`.
- **Colour:** `palette(n, ACCENTS)` (n distinct, contrast-checked fills — warns on adjacent same-hue;
  never a gray filler), `palette_from_image` (match a generated template's palette), `accent_one`
  (one-accent discipline), `contrast_ratio` (verify ≥~4.5:1 before committing).
- **Data furniture & charts:** `scorecard`/`leaderboard`/`takeaway_rail`, `change_stat` (baseline-
  centred before→after), `stat_row`, `big_numeral`; **editable native charts** `native_chart` /
  `native_dual_axis` / `native_donut` / `native_pareto` / `native_bubble` (feed them straight from a
  spreadsheet with **`series_from_csv(path, x_col, y_cols)`** → `(categories, series)`, stdlib, no pandas),
  plus the raster recipes in `scripts/designed_charts.py` (incl. **`waterfall`** — a total's rise/fall/
  total walk, semantic up/down colour) — pick per `references/data-viz.md`.
- **Walkthrough / hierarchy / comparison-grid:** **`annotated_figure`** (a real figure + numbered
  markers + a numbered caption rail + optional magnified inset — the guided figure walkthrough the
  integral-figure rule kept demanding by hand) · **`small_multiples`** (identical mini native charts
  with a SHARED value axis — the documented recipe left each panel auto-scaling, so a small bump and
  a huge bump looked identical) · **`position_map`** (N LABELLED items on two continuous axes — the
  within-cell position quadrant() throws away) · **`org_tree`** (tidy hierarchy: centroid parents,
  horizontal bus; raises when it can't fit legibly).
- **2.5D isometric (native — no generated image):** **`iso_bars`** (a FAITHFUL 2.5D bar chart —
  extrusion height is linear in the value and zero-based, so the depth never distorts the data) ·
  **`iso_stack`** (a layered architecture / disclosure ladder / decision stack — floating isometric
  slabs with labels aligned beside each one) · **`iso_prism`** (one extruded block as a hero).
  Fixed projection (true 30° isometric, parallel not perspective) and one-light-source face shading,
  so every 2.5D element in a deck reads as one system. **Dose like generated imagery** — a stack, a
  hierarchy, or ONE hero chart, never every slide; text cannot be sheared onto a face, so labels sit
  beside the geometry. When the 2.5D wants to be a rich atmospheric *scene* (not data), that is the
  generated-image branch, not these.
- **Placement by measurement:** `image_fx.quiet_region(path)` → the image's calmest ONE-INK region
  + its mean luminance (choose dark vs light ink from data, not eyeballing) · `deckkit.pic_alpha`
  (native picture opacity — a faint plate that keeps its own hues, no scrim shape) ·
  `deckkit.design_intent(slide, envelope=…, rhyme=…)` (declare a deliberate quiet/baseline/bleed
  register so the render-time lint audits intent instead of guessing it).
- **Decision / plan / grid:** **`eval_matrix`** (options×criteria scoring grid — `harvey_ball` fifths-fill
  glyphs or ✓/◐/✕ marks, `recommend=` tints the winner) · **`heat_matrix`** (category×category grid coloured
  by value, `scale="seq"|"div"|"risk"`) · **`tier_stack`** (one taper: `mode="funnel"` drop-off /
  `mode="pyramid"` layers, + `funnel()`/`pyramid()` wrappers) · **`gantt`** (dated task bars on a shared
  `axis_scale`, `lanes=` swimlanes, `today=` marker — durations & overlap, where `timeline` shows only points).
- **Diagrams / patterns:** `quadrant`, `hub_spoke`, `timeline`, `before_after`/`image_tab`/
  `photo_triptych`, **`device_frame`** (a real screenshot in a `chrome="browser"`/`"phone"` bezel),
  `wireframe_grid`+`spec_list`, `corner_frame`, `photo_card`, `backdrop_motif`,
  `repeat_row` (N identical-except-index units as representatives + `…` + `×N`, shared detail said
  once — never N duplicate blocks).
- **Surface (dark / glass / print):** `glass_card`/`glow`/`scrim_overlay` (gradient+alpha fill),
  `offset_shadow` (hard letterpress/riso shadow).
- **Publication & math:** `cover`/`colophon` (bookend the deck), `sources_page`, `specimen_card`;
  **`equation_native`** (EDITABLE LaTeX-subset math — real text runs, renders everywhere; the default) /
  `equation_png` (rasterised LaTeX, for 2-D math: fractions/matrices) / `eq_par` (inline runs).
- **East-Asian (CJK) accents:** `seal` (vermilion chop/印章 stamp — the one red accent on an ink deck),
  `cjk_numeral` (壹·贰·叁 section markers vs Latin "01"). See `references/east-asian-aesthetic.md`.
- **Diagram kit (general flowcharts):** `node` + `connector` / `flow_chain` (straight links between adjacent nodes) + `elbow_connector` /
  `loop_path` (elbow / U-shaped paths for a feedback/repeat loop, a return, or a link between NON-adjacent
  nodes) — any architecture from rounded-rect/pill/circle nodes (+ diamond/parallelogram/cylinder when
  formal flowchart notation applies — see the Standard-notation crib in `design-gallery.md`) with
  **stroke semantics** (solid=required
  · dashed=optional · dotted=feedback) and **shape semantics** (straight=adjacent flow · elbow/U=loop /
  return / non-adjacent), exactly one `hub` (hub optional in the system-architecture recipe — the
  focal path can carry emphasis instead)  *(NB two similarly-named helpers: **`hub_spoke`** draws the
  whole radial FIGURE — one centre + labelled spoke nodes on a ring; **`hub_spokes`** only draws the
  CONNECTORS from an existing hub to existing nodes. Reach for `hub_spoke` to build the diagram,
  `hub_spokes` to wire one you laid out yourself.)* the
  focal path can carry emphasis instead); `diagram_island` (bright figure panel on a dark slide);
  `concentric_rings` (nested framework); `step_list` (numbered process, vertical/horizontal).
  - **This kit draws conceptual BOX-FLOW only — not physical science schematics.** For a
    **labelled science schematic** explaining a principle / mechanism / experiment / definition (a
    **free-body / force diagram, optics ray path, electric circuit, chemistry apparatus + reaction,
    vector / coordinate geometry, wave / field** — physics · chemistry · biology · engineering · any
    subject), NOT the node/connector kit. Two faithful build paths (pick by precision-vs-polish):
    **matplotlib / a domain library** → transparent PNG (the safe default when the exact geometry/labels
    ARE the meaning — deterministic, correct-by-construction), OR — for a **complex / fancy / generated-
    template-matched** schematic whose geometry isn't load-bearing — the **OpenAI image tool for a
    text-free styled visual with the labels overlaid as native editable text**. **Never bake labels or
    unverifiable geometry into a generated image** (garbled text + wrong physics). Recipes, the
    image-tool workflow, and the **domain-accuracy fidelity gate** are in
    `references/schematic-diagrams.md` — build it correct (a wrong schematic misleads worse than none).
- **Editorial / consulting furniture:** `insight_banner` (so-what bar), `bilingual_lockup` (CJK+tracked
  Latin headline), `highlight` (inline `<k>keyword</k>` recolour), `ghost_numeral` (faint watermark
  ordinal), `concept_equation` (ZINE=MAGAZINE word-equation), `pull_quote`/`standfirst`, `cta_button`/
  `cta_pair`, `status_stamp`/`corner_tab`, `spec_card`, `year_badge`, `gradient_rule` (2-stop brand rule),
  `catalogue_frame` (double-line specimen frame — museum/eastern presets).
- **Micro-viz:** `dot_meter` (●●○), `tradeoff_list` (+/−), `segmented_bar` (cumulative 100%), `meter_bar`
  (a single percentile/share/progress row — track + accent fill + a value label **vertically centered on
  the bar**; use this instead of hand-building "track box + fill box + number", which is how value labels
  end up floating off the bar's centerline; canvas-safe by construction — an overflowing value
  auto-shortens the bar instead of leaving the slide).
- **Photo on-brand (`scripts/image_fx.py`):** `duotone` / `grayscale` so a colour photo doesn't fight
  the accent (riso/brutalist/ink/luxury/museum), then `picture(fit="cover")`.
