# Designed plots — pick the chart per argument, don't default to bars

A weak data deck reaches for the same bar chart (or a number table) every slide. A strong one
**chooses the chart TYPE that fits each argument**, themes it to the deck, **highlights the one
thing that matters**, and pairs it with a one-line "so-what". This file is the repertoire + the
rules. (For raw data with an *obvious* single comparison, a plain bar/line is still right — this
is for when the relationship is richer.)

## Table of contents
- Pick by argument
- Chart anti-patterns (each one has shipped an ugly or misleading chart — check by name)
- The four rules every designed plot follows
- IBCS notation — business/status/finance decks
- Colour-blind safety
- Editable native charts vs matplotlib rasters — pick by need
- Native data furniture (deckkit)
- Example
- When NOT to use this

## Pick by argument
| The point you're making | Chart | Helper (`scripts/designed_charts.py`) |
|---|---|---|
| Part-to-whole + one headline number | **donut + centre KPI** | `donut_kpi(...)` |
| Before→after / a gap per category | **dumbbell** | `dumbbell(rows, ...)` |
| Rank/level change between **two** dates | **slope / bump** | `slope(series, ...)` |
| Two trends on different scales (A↑ while B↓) | **dual-axis line** | `dual_axis(x, left, right, ...)` |
| x vs y with a 3rd (size) dimension + fair value | **bubble + trend line** | `bubble_trend(points, ...)` (raster) · **`deckkit.native_bubble`** (editable-native — prefer it for a non-Latin deck or when the user will edit) |
| The "vital few" that drive a total | **Pareto** (bars + cumulative %) | `pareto(items, ...)` |
| Current state in numbers (3-6 metrics) | **KPI scorecards** (native) | `deckkit.scorecard(...)` ×N |
| Ranked / part list keyed to a chart | **leaderboard** (native) | `deckkit.leaderboard(rows)` |
| One hub, many dependents | **hub-and-spoke** | native (`box`+connectors); radial layout |
| **How a total builds start→end / a variance walk** | **waterfall / bridge** | `waterfall(out, items, ...)` — floating rise/fall/total bars + connector steps; the one **semantic up/down colour** exception (not the single-highlight rule) |
| **A multivariate profile across 3–8 axes** (compare shapes, ≤3 series) | **radar / spider** | `radar(out, axes_labels, series, ...)` — enforces the limits that keep the form honest: ≤3 overlaid polygons, 3–8 axes, every spoke **zero-anchored** (per-axis min–max stretching is the usual radar cheat), and it prints the range it used. Note radar always *overstates* a lead (area grows as the square) and the spoke ORDER changes the shape — so prefer `small_multiples` or a per-metric `dot_strip`/`dumbbell` for "who wins on each metric", and use radar only when the profile SHAPE (balanced vs spiky) is itself the point. For 4+ series it raises. |
| **Spread / uncertainty in SAMPLE data** (a value that is a mean of measurements — per-subject Dice, per-run latency, per-rater score) | **box plot · mean ± error · every point** | **`distribution(out, groups, ...)`** — the ONE case where a bar chart is a defect, not a preference: the bar hides n, the shape and the outliers (Nature Methods, *Kick the bar chart habit*; PLOS Biology, *Beyond Bar and Line Graphs*). `kind="auto"` applies that literature's rule in code — n≥5 → box (median/IQR/Tukey whiskers), n=3–4 → mean ± error, n<3 → **refuses** (two values have no distribution; use `dot_strip` and state n). `err="sd"/"se"/"ci95"` is **printed on the figure**, because the same drawn height means three different things. Counts still belong in a bar chart. |
| **Size AND share together** (market share by segment, share of wallet, portfolio mix) | **marimekko / mekko** | `marimekko(out, columns, categories, ...)` — column WIDTH = segment size, height = the split inside it, so **cell area = the absolute quantity**. That is exactly what a 100% stacked bar throws away (it draws every segment as equally important). Widths are strictly proportional and a non-positive size raises. On a stacked form `highlight` keeps the accent but gives the others a *distinguishable* neutral each — flattening them to one grey would destroy the mix. |
| A simple single comparison / one trend | **bar / line** | `matplotlib` (the existing path) |

The recipes render a themed PNG → place with `deckkit.picture(out, ..., fit="contain")`.

**Recipe patterns (no dedicated helper — compose in matplotlib / deckkit):**
- **Small multiples / trellis** — the same metric across many comparable slices (regions, products, cohorts): build with **`deckkit.small_multiples`**, which produces identical mini charts pinned to ONE shared value axis (so shapes compare) + **one highlighted** slice. Do NOT hand-compose `native_chart` per panel — that silently loses the shared scale that IS the form. Better than one spaghetti chart of N series.
- **Sparkline** — a tiny axis-less word-scale trend inside a KPI tile / table cell / sentence: a matplotlib line with axes/ticks/frame off, saved small and placed inline via `picture`, or a native mini `native_chart` stripped of chrome. Pairs with `big_numeral`/`stat_row` to show "the number AND its trend".
- **Chart annotation layer** — data-anchored overlays ON a designed chart: a **CAGR growth arrow** across columns, a **delta bracket** between two bars, a **reference/target line** (`ax.axhline`), a **convergence/target band** (`ax.axhspan`), or a labeled callout on the key point. The annotation carries the "so-what" *inside* the plot; keep it to the ONE thing that matters.
- **Football field / range bars** — a value RANGE per category (valuation, estimate, min–max) → **`deckkit.range_bars`** (floating horizontal bars on a shared `axis_scale`, one row per category, optional base-case tick) — a `dot_strip` cousin for ranges instead of points.
- **Composition over time** — a total AND its component mix across periods → **`deckkit.native_chart(kind='column_stacked' | '…_stacked_100' | 'area_stacked')`** (real editable charts; `…_100` when the SHARE is the story). Clustered bars hide the mix.
- **Actual vs target dashboard** — KPIs each with a plan line and good/ok/poor context → **`deckkit.bullet_graph`** (per-row scale, so mixed units are fine; `higher_better=False` for churn/latency). `scorecard`/`meter_bar` carry a value but no target or thresholds.
- **Choropleth (value per region)** — one value PER COUNTRY / PER PROVINCE shaded on a real map → **`deckkit.choropleth(slide, x, y, w, h, data, mapname)`** where `mapname` = `'europe'` · `'world'` · `'china'` (provinces). Built on public-domain geometry (Natural Earth countries · DataV China provinces) via `scripts/maps.py`, projected (Albers for a region, equirectangular for the world), light→`accent` ramp with a neutral no-data fill. Key `data` by ISO-3166 alpha-2/alpha-3 or English name (countries) or province name/adcode (china); unmatched keys are reported. Title + gradient legend are NATIVE deckkit text (CJK-safe), so the map PNG stays language-agnostic. Geometry is fetched once and cached like icons (needs matplotlib — already a dep — and network on first use). Use it instead of a `dot_strip` when the geography itself carries meaning; keep `dot_strip` when a handful of named values on a common scale say it more simply.

## Chart anti-patterns (each one has shipped an ugly or misleading chart — check by name)
- **Dual-axis abuse** — two unrelated series forced onto twin axes to fake correlation; use it only
  for one genuinely paired ↑/↓ story, and colour-key each axis to its series.
- **Too many series** — >4 lines/bars per chart turns evidence into spaghetti; split, or grey all
  but the ONE series the takeaway is about (single-highlight rule). *Carve-out: single-highlight is
  for CLUSTERED/line charts — a **stacked/area composition** chart keeps every series its own colour
  so the mix reads (omit `highlight`); the cap there is ~4–5 genuine parts-of-a-whole.*
- **Composition without meaning** — a donut/stacked bar for parts that don't sum to a meaningful
  whole; if the audience won't ask "share of what?", use a bar.
- **Stacked chart that misleads** — three traps on `native_chart(kind='…_stacked…')`: (1) a
  **100%-stacked** whose SHARE grows while the absolute TOTAL is collapsing — the mix looks healthy as
  the business shrinks; keep the total visible (pair with a plain stacked bar, or annotate it). (2)
  **NEGATIVE segments** — a stack's height only reads as a sum when parts are same-sign; a negative
  segment crosses zero and the total is misrepresented (deckkit prints a notice) — use a clustered or
  diverging form for signed data. (3) **too many / non-parts series** — a stack reads cleanly to ~4–5
  genuine parts-of-one-whole; beyond that segments reuse colours and blur, so group the tail into
  "Other" or split. (Corollary: **clustered bars where composition-over-time wants a stack** — 8
  quarters × 4 lines as 32 clustered bars buries the very mix-shift that is the story.)
- **Cropped-axis drama** — a bar chart whose y-axis starts above 0 inflates a small delta; bars
  start at 0 (lines may zoom, but then say so on the axis). This bites hardest on **clustered-high
  data** (scores 85/88/92, revenue 210/220/230): the renderer *auto-crops* the axis to ~200 and a
  bar reading ~3× taller is only 1.09× larger. `deckkit.native_chart`/`native_pareto` now force a
  zero baseline for column/bar with non-negative data (`zero_base=True` default) — don't pass
  `zero_base=False` unless a zoomed magnitude axis is deliberate *and* labelled; a **matplotlib /
  hand-rolled** bar chart has no such guard, so set `ax.set_ylim(bottom=0)` yourself.
- **Inflating floor on a proportional encoding** — a min-visible-size clamp that lifts small values
  to a fixed floor so a `10`-out-of-`200` tier is DRAWN at 20% width while its label reads 5%: the
  geometry now contradicts its own number, and the floor fires exactly where a funnel's story lives
  (the deep drop-off). A proportional encoding (funnel/pyramid band width, bubble area, bar length)
  must track `value/max` with at most a *hairline* floor; when a band gets too thin to hold its
  label, route the label OUT to a side leader — never widen the band. `deckkit.tier_stack` does this
  now; a hand-rolled proportional shape must too.
- **Off-zero neutral on a signed scale** — a diverging blue↔red (or +/−) encoding whose neutral is
  anchored at the DATA midpoint, not the value 0, so a true `0` renders blue ("negative") and
  all-positive deltas straddle neutral — the sign reading is simply wrong. Anchor neutral at the
  semantic zero. `deckkit.heat_matrix(scale='div')` **and `deckkit.choropleth(scale='div')`** zero-centre
  by default (both pass explicit symmetric `vmin`/`vmax` only for a deliberate asymmetric range); a
  hand-rolled matplotlib diverging map needs `TwoSlopeNorm(vcenter=0)` (or a symmetric `vmin=-M, vmax=+M`).
- **Choropleth that maps COUNTS, not rates** — the #1 map lie: shading a raw TOTAL (sales, users, cases)
  so big/populous regions always go dark and the map just re-draws population/area. Shade a **rate / share /
  per-capita / index / density** so region size doesn't dominate; a raw total belongs on a ranked bar or
  `dot_strip`, or normalise by population/area first. Related traps: (a) a map for only a **handful of
  regions** where a ranked bar reads better (use `choropleth` when *where* is the story, not just because the
  categories are places); (b) **sequential ramp on signed data** (or `div` on one-directional magnitude) —
  `seq` for magnitude, `div` for signed/around-a-reference; (c) a **blank region reads as zero** when it's
  actually NO DATA — `deckkit.choropleth` fills unmatched regions a distinct neutral and prints the
  unmatched keys, so verify that notice and fix any typo/ISO before shipping.
- **Axis that misses a bar** — a baseline / value axis drawn to a hand-picked width that stops short of
  the last bar reads as a rendering bug; derive its extent from the data (`last_bar_x_end − axis_x`).
- **Waterfall that double-counts** — showing increments AND their sum as peer bars ("+8 / +8.3 / +16.3"
  where 16.3 = 8+8.3), or stacking two *different* quantity kinds into one total (take-home extras +
  employer pension = a "135%" bar). Show increments *or* the running total, use `designed_charts.waterfall`
  (correct running-total + connectors), and keep distinct quantities in separate stacks / a side note.
- **Hand-rolled where a component exists** — building `waterfall`/`gantt`/`dumbbell_board`/a chart from
  raw boxes re-introduces the geometry & grammar bugs the component already fixed; reach for the
  component, hand-roll only a form the library genuinely lacks.
- **Chart with no takeaway** — a plot dropped on the slide with no assertion title / takeaway rail
  is data, not an argument; every chart answers a named question.
- **Rainbow categorical palette** — hues with no semantic binding read as decoration; bind each hue
  (semantic-color-contract.md) or stay monochrome + one accent.

## The four rules every designed plot follows
1. **Single highlight (one-accent discipline).** Recolor only the ONE series/wedge/row/bar that
   carries the point in the accent; drop everything else to a neutral grey. The recipes take a
   `highlight` index and do this; for a multi-series categorical chart where every series matters,
   skip the highlight. Never let a chart use >2 saturated hues unless it's genuinely categorical.
   (On a **single-series** native bar/column chart, `highlight` selects a whole series and so can't
   pick one bar — use `native_chart(..., emphasize=<category index>)` to foreground ONE bar.)
2. **Theme it to the deck.** Pass the deck's palette (`palette=ACCENTS`, or pull from a generated
   template with `palette_from_image`) and `dark=True` for a dark deck, so the chart looks built-in,
   not pasted. Charts render on a transparent background, so they sit on any slide fill. **On a CJK
   (Chinese/Japanese/Korean) deck, pass `font="<your deckkit.EAFONT>"`** so chart labels render real
   glyphs, not tofu (matplotlib uses its first resolvable font for *all* text, so the CJK face must
   lead — the recipes handle this when you pass `font`). If no CJK font is installed, keep chart text
   Latin/numeric and label the categories with `deckkit.text()` around the chart (the `equation_png`
   fallback). This applies to **any-language** deck, not just English.
3. **Carry a "so-what".** Split the slide ~**65% chart / ~35% narrative rail** and add a
   `deckkit.takeaway_rail(label, hero_stat, body)` — a small caps label, the one restated number,
   and a 2-3 line interpretation. A chart without a stated conclusion makes the audience guess.
4. **Label directly, don't rely on colour alone.** End-of-line value labels, a legend keyed by
   the SAME colours as a paired `leaderboard`, markers as well as hue — so it survives a projector
   and colour-blind viewers (the deck-wide accessibility rule).
5. **It must LOOK right — render it and check.** Applies to **every plot you generate with code**
   (matplotlib, a designed_charts recipe, any domain plot), not one chart type. Two recurring failures:
   **(a) undersampled curves** — a continuous/high-frequency function plotted at coarse or integer `x`
   *aliases* into jagged zigzags (the "sine looks weird" bug); sample with a dense `np.linspace` (a few
   hundred points, ≥~10× the highest frequency) so smooth functions look smooth — plot the curve on a
   fine grid even if the *data/markers* sit on integers. **(b) A legend (or annotation) sitting ON the
   data** — when the plot is full, put the legend **outside the axes** or in the truly empty corner;
   `loc='best'` is not enough on a busy plot. The general pattern:
   ```python
   xs = np.linspace(x0, x1, 600)            # dense grid — NOT np.arange(0, 50) for a smooth curve
   for k in series: ax.plot(xs, f(xs, k), label=...)
   ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)  # legend OUTSIDE the axes
   fig.savefig(out, bbox_inches="tight")    # so the outside legend isn't clipped
   ```
   For a **dual-axis / twin-axis** plot, never draw two separate `legend()`s (they collide with each
   other and the twin-axis ticks) — collect both handle lists and draw **one combined legend above** the
   axes: `lns = l1 + l2; ax.legend(lns, [h.get_label() for h in lns], loc="lower center",
   bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)`. Overlap can't always be perfectly avoided on a
   dense plot — when there's no empty region, going **outside** (right or above) is the answer; never ship
   a legend sitting on the data. (In a very small plot cell an outside legend can shrink the axes too far —
   then omit the in-figure legend and label the series in the native slide caption instead.)
   Always **view the rendered PNG** and fix aliasing / an occluding legend / clipped labels before
   placing it — a wrong-*looking* plot misleads even when the numbers are right.

## IBCS notation — business/status/finance decks
**Scope:** consulting/status/finance readouts (variance walks, plan-vs-actual, forecast bridges) —
where the audience reads AC/PY/PL/FC daily. Academic/creative decks are exempt; this is reporting
notation, not a universal style. A bar's **fill** says which data world it shows:

| Scenario | Fill | `designed_charts` |
|---|---|---|
| **AC** — actual | solid dark ink | `scenario="actual"` |
| **PY** — prior year/period | solid light grey | `scenario="prior"` |
| **PL** — plan/budget | hollow: white face, dark edge | `scenario="plan"` |
| **FC** — forecast | hatched `//` | `scenario="forecast"` |

- `pareto(..., scenario=...)` and `waterfall(..., scenario=...)` take one scenario for the whole
  chart **or a per-bar list** (the classic bridge: actual months solid, forecast months hatched);
  in `waterfall` the treatment keeps each bar's semantic colour as its ink, so an FC variance bar
  renders as a green/red `//` hatch. `scenario=None` (default) keeps the non-IBCS accent look.
- **Variance semantics: green = favorable, red = unfavorable** (`favorable_color=` /
  `unfavorable_color=` on `waterfall` and `dumbbell`; pass them swapped when *down* is good, e.g. a
  cost bridge). **Never hue alone** — pair the colour with a **sign (+/−), a label, or position**
  (the helpers do: signed waterfall labels, dumbbell dot position) so the reading survives
  grayscale, a projector, and colour-blind viewers.
- **Same measure + same unit → ONE value scale** across the charts on a slide/spread; if a shared
  scale is impossible, carry an **explicit scaling indicator** (a `×10` note / axis-break marker) —
  silently different scales fake comparability.
- **Data titles state measure · unit · period** — "Revenue, m€, FY25 vs FY24" — never a vague
  "Performance overview".

## Colour-blind safety
- 🔴 **Check the palette, don't just intend it**: `python3 scripts/palette_audit.py --inks …` simulates deuteranopia, protanopia and tritanopia and names any pair that stops being two colours for the ~8% of men with a red-green deficiency. It matters only where two hues carry MEANING (a series, a status, a legend); where they do, separate them by LIGHTNESS or by shape/label as well as hue.
- `dk.OKABE_ITO` is the colour-blind-safe **categorical fallback** palette — reach for it whenever
  a chart genuinely needs 3+ categorical hues and the deck palette isn't verified safe.
- **Hue-only ban:** multi-series lines must differ by more than hue — vary linestyle/marker or add
  direct end-of-line labels; status semantics (green/red, RAG) always pair the colour with an
  icon/label/shape (rule 4 above; semantic-color-contract.md).

## Editable native charts vs matplotlib rasters — pick by need
Three ways to put a chart on a slide; choose by what the deck needs:
- **Editable native PowerPoint chart — `deckkit.native_chart` / `deckkit.native_dual_axis`.** A *real*
  chart object: the user can **click to edit data/labels** in PowerPoint, and **any non-Latin labels —
  CJK (中文/日本語/한국어), Cyrillic, Greek, … — render via PowerPoint's own fonts, no tofu** (matplotlib
  often can't find the script's font for a rotated axis title and renders □). **Prefer this whenever
  (a) the deck is in ANY non-Latin language, or (b) the user wants to edit the chart.** Pass `font=`
  your deck's text font for the script (your `EAFONT` for CJK; a Cyrillic/Greek deck's `FONT` already
  covers those). **Covers nearly the whole roster:** `native_chart` (`line`/`line_markers`/`column`/
  `bar` + the **composition** kinds `column_stacked`/`…_stacked_100`/`bar_stacked`/`…_stacked_100`/
  `area`/`area_stacked`/`…_stacked_100`, and **slope** = a 2-point line), `native_dual_axis` (two-scale 'A↑ vs B↓', e.g. 占比% vs
  成本指数), `native_donut` (part-to-whole + a KPI in the hole), `native_pareto` (columns + cumulative-%
  line on a secondary axis), `native_bubble` (x·y·size). Themed (`palette`, `dark`, `font`,
  `highlight`). **Data from a spreadsheet?** `deckkit.series_from_csv(path, x_col, y_cols)` → `(categories,
  series)` feeds `native_chart`/`native_dual_axis` directly (stdlib csv — no pandas; auto-sniffs the
  delimiter; strips thousands-commas / `%` / a currency symbol; non-numeric → 0). *(RTL scripts —
  Arabic/Hebrew — remain a known layout limitation, see `multilingual.md`.)*
- **`designed_charts` (matplotlib raster).** Use only when (a) you specifically want the matplotlib
  styling, or (b) for the **dumbbell** (before→after gap), which has no native chart type — otherwise
  prefer the native editable equivalents above. A transparent PNG; **not editable**, and on a
  non-Latin deck you must pass `font="<the script's font>"` — still raster.
- **Freeform native (`deckkit` shapes)** for diagram-like "charts" (hub-and-spoke, a flow/Sankey, an
  annotated timeline) that are really layout — and for an editable **dumbbell** (rows of dot——dot).
  Keep them measure-then-place inside a `content_band`.

Rule of thumb: **default to the native editable charts** (`native_chart` / `native_dual_axis` /
`native_donut` / `native_pareto` / `native_bubble` — pass the script's `font=`); reach for
`designed_charts` (raster) only for dumbbell or a deliberate matplotlib look; a diagram → freeform.
- Either way: **whole chart, legible at the deck's read distance, one message, one highlight, a
  takeaway.** ("From the back of the room" is the floor for a *presented* deck; for a **read-alone /
  reference** chart, size to arm's-length reading and it's fine to keep more series labelled — there's
  no narrator to point at the rest. Direct labels + colour-blind safety are universal regardless.)

## Native data furniture (deckkit)
- `scorecard(slide, x,y,w,h, label, value, delta=, caption=, good_up=, glass_tint=)` — a KPI tile
  (big value + auto-coloured ▲/▼ delta). Lay out 3-6 with `columns()`/a 2×2 grid; pass
  `glass_tint=` on a dark deck to make them glass.
- `leaderboard(slide, x,y,w, rows=[(color,name,value[,sub])])` — ranked rows with a colour swatch
  that **keys back to a paired chart** (use the chart's colour list so legend ↔ chart stay in sync).
- `takeaway_rail(slide, x,y,w, label, hero, body)` — the narrative rail beside a chart.

## Example
```python
import designed_charts as dc, deckkit as dk
band = dk.content_band(s)                       # the safe region
dc.dumbbell("assets/gap.png", rows, palette=ACCENTS, highlight=1, a_label="2024", b_label="2026")
dk.picture(s, "assets/gap.png", band[0], band[1], band[2]*0.62, band[3], fit="contain")
dk.takeaway_rail(s, band[0]+band[2]*0.66, band[1]+0.3, band[2]*0.34,
                 "Key shift", "+5 dB", "Model B closes most of the gap by 2026 — the one to back.")
```

## When NOT to use this
Short status updates, qualitative talks, or a slide with a single obvious number (use a hero stat /
`scorecard`, not a chart). Reserve the richer roster for data/report/market/strategy decks that have
many distinct quantitative relationships to show.
