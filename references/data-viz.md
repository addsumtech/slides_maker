# Designed plots — pick the chart per argument, don't default to bars

A weak data deck reaches for the same bar chart (or a number table) every slide. A strong one
**chooses the chart TYPE that fits each argument**, themes it to the deck, **highlights the one
thing that matters**, and pairs it with a one-line "so-what". This file is the repertoire + the
rules. (For raw data with an *obvious* single comparison, a plain bar/line is still right — this
is for when the relationship is richer.)

## Pick by argument
| The point you're making | Chart | Helper (`scripts/designed_charts.py`) |
|---|---|---|
| Part-to-whole + one headline number | **donut + centre KPI** | `donut_kpi(...)` |
| Before→after / a gap per category | **dumbbell** | `dumbbell(rows, ...)` |
| Rank/level change between **two** dates | **slope / bump** | `slope(series, ...)` |
| Two trends on different scales (A↑ while B↓) | **dual-axis line** | `dual_axis(x, left, right, ...)` |
| x vs y with a 3rd (size) dimension + fair value | **bubble + trend line** | `bubble_trend(points, ...)` |
| The "vital few" that drive a total | **Pareto** (bars + cumulative %) | `pareto(items, ...)` |
| Current state in numbers (3-6 metrics) | **KPI scorecards** (native) | `deckkit.scorecard(...)` ×N |
| Ranked / part list keyed to a chart | **leaderboard** (native) | `deckkit.leaderboard(rows)` |
| One hub, many dependents | **hub-and-spoke** | native (`box`+connectors); radial layout |
| A simple single comparison / one trend | **bar / line** | `matplotlib` (the existing path) |

The recipes render a themed PNG → place with `deckkit.picture(out, ..., fit="contain")`.

## The four rules every designed plot follows
1. **Single highlight (one-accent discipline).** Recolor only the ONE series/wedge/row that
   carries the point in the accent; drop everything else to a neutral grey. The recipes take a
   `highlight` index and do this; for a multi-series categorical chart where every series matters,
   skip the highlight. Never let a chart use >2 saturated hues unless it's genuinely categorical.
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
   Always **view the rendered PNG** and fix aliasing / an occluding legend / clipped labels before
   placing it — a wrong-*looking* plot misleads even when the numbers are right.

## Editable native charts vs matplotlib rasters — pick by need
Three ways to put a chart on a slide; choose by what the deck needs:
- **Editable native PowerPoint chart — `deckkit.native_chart` / `deckkit.native_dual_axis`.** A *real*
  chart object: the user can **click to edit data/labels** in PowerPoint, and **any non-Latin labels —
  CJK (中文/日本語/한국어), Cyrillic, Greek, … — render via PowerPoint's own fonts, no tofu** (matplotlib
  often can't find the script's font for a rotated axis title and renders □). **Prefer this whenever
  (a) the deck is in ANY non-Latin language, or (b) the user wants to edit the chart.** Pass `font=`
  your deck's text font for the script (your `EAFONT` for CJK; a Cyrillic/Greek deck's `FONT` already
  covers those). **Covers nearly the whole roster:** `native_chart` (`line`/`line_markers`/`column`/
  `bar`, and **slope** = a 2-point line), `native_dual_axis` (two-scale 'A↑ vs B↓', e.g. 占比% vs
  成本指数), `native_donut` (part-to-whole + a KPI in the hole), `native_pareto` (columns + cumulative-%
  line on a secondary axis), `native_bubble` (x·y·size). Themed (`palette`, `dark`, `font`,
  `highlight`). *(RTL scripts — Arabic/Hebrew — remain a known layout limitation, see `multilingual.md`.)*
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
