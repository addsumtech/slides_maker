<!-- Extracted from SKILL.md Step 4 figure rules (L1278-1350) -->
<!-- This file is loaded on-demand when the corresponding Step runs. -->
<!-- SKILL.md retains a skeleton summary + pointer to this file. -->

# Figure Handling Rules

> Integral-figure default, crop rules, PDF figure extraction, the see-it crop loop, and dense panel grid reassembly.

---

- **Use the source's own figures, WHOLE — integral is the default.** For *any* deck
  (research, work, exec, teaching): if the source — paper, report, doc, existing slide, or a
  chart already produced from the code/data — has a figure (architecture, results, a plot),
  use *that*; don't redraw it (slow, risks wrong detail) and don't chop it into pieces. Many users
  *prefer* the whole figure even when it's dense (it's the artifact they know and trust), so
  when a figure feels too busy, your *first* move is to give it a whole slide — large, with an
  **assertion title + a one-line caption** pointing attention to the part that matters (e.g.
  "the orange line is this quarter", or "rightmost column is ours") — not to crop it down. Reach for cropping only to (a) **trim**
  surrounding page header / caption / whitespace (leaving a small margin, never flush), or (b) lift
  **one cleanly-separable sub-figure** that genuinely stands alone. Chopping a multi-panel figure into a few columns
  *loses context and changes what the authors showed* — do it only when the whole is truly
  unusable on a slide, and prefer to **confirm with the user** before discarding panels.
  Build native diagrams only for structure with no source figure.
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
