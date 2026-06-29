# Form selection — content shape → the candidate FORMS (generate a set, then pick)

The single content-indexed map for "what visual form should this slide take?" — used by the
**content-planner** (designs to it), the **builder** (SKILL.md step 4), and the **critic** (judges form
fit) so all three resolve to one surface. Each row is a **candidate SET + a tie-breaker**, never a
single answer.

> **Design is choosing, not matching.** NEVER record the first matching form. For each content slide,
> generate the **2–3 forms the content could take**, then pick with the tie-breaker and record *why the
> winner beat the runner-up* (the planner's Form ledger). The reflex form — a rounded-card / panel grid
> — is the right answer for **parallel, unordered, equal-weight** items only; the moment the content has
> **order, magnitude, a relationship, time, or two axes**, a non-card form almost always says it better.

## By communicative intent

| The content is… | Candidate forms (deckkit, in rough preference order) | Tie-breaker |
|---|---|---|
| **A comparison** (A vs B; before→after) | `table`(highlight row) · `dumbbell` · `slope` · `before_after` · `change_stat` · `quadrant` | table for >2 dimensions; **dumbbell** for one before→after gap *per item*; slope for a 2-point rank change; change_stat for a single baseline→after; quadrant when **two axes** carry the point |
| **A process / sequence / steps** | `step_list` · `flow_chain` · `timeline` · `node`+`connector` · `repeat_row`(if N identical stages) | timeline if the steps are **dated**; flow_chain if there are **arrows/branches** (+ stroke & shape semantics, elbow for loops); step_list if linear & numbered |
| **Parts of a whole / composition** | `native_donut` · `segmented_bar` · `stat_row` · `leaderboard` | donut for 2–4 shares; **segmented_bar** for cumulative 100%; leaderboard for a *ranked* breakdown |
| **A relationship / structure / architecture** | `hub_spoke` · `node`+`connector` · `concentric_rings` · `quadrant` | hub_spoke for one centre + spokes; concentric_rings for **nested** layers; node+connector for a general graph (one `hub`) |
| **A trend over time** | `native_chart`(line) · `slope` · `native_dual_axis` · `native_pareto` | line for many points; **slope** for two points; dual-axis for two scales (A↑ vs B↓) |
| **A few standout numbers / KPIs** | `scorecard`(3–6 tiles) · `stat_row` · `big_numeral`(one hero) · `change_stat` · `meter_bar` | big_numeral when **one** number is the whole point; scorecard for 3–6; meter_bar for a single share/percentile |
| **A set of distinct attributes / features** | **first ask:** is there magnitude (`stat_row`) or two axes (`quadrant`) or a comparison (`table`)? → use those. Only if the items are **truly parallel, unordered, equal-weight** → `icon_card` row / `columns` cards | cards are the *considered* choice for parallel-equal items, **not** the default for anything list-shaped |
| **One idea / a claim / a quote** | `pull_quote` · `big_numeral`+caption · a whole figure + assertion title · `insight_banner` | pull_quote for a verbatim line; big_numeral for a single statistic; figure when the artifact *is* the point |
| **Dense reference / many fields** | `table` · `spec_card` · `wireframe_grid`+`spec_list` | table for rows×cols; spec_card for a mono key→value placard; wireframe for a UI/layout spec |
| **A concept that needs the real thing** | a **computed/generated domain artifact** (image-generation.md) · a **whole source figure** | compute/extract the real artifact (FFT, a real plot, a patch) — never a box-and-dot cartoon |
| **A principle / mechanism / how-it-works** (physics, math, a process you're *explaining*) | a **labelled schematic diagram BESIDE the statement** (forces · signal path · geometry · cause→effect) · a generated domain artifact · `node`+`connector` · an annotated whole figure | **default to a diagram, not text-alone** — a stated principle wants a picture of the mechanism next to it; schematic when it's spatial/causal, a real/generated artifact when it must look real, an equation (mathfont) when the law *is* the relation. Text-only for a principle a diagram could show is a miss. |
| **An algorithm / method / training-or-optimization procedure** (ANY field — ML, but also a derivation, optimizer, lab/comp protocol) | `algorithm_block` (numbered pseudocode — Input/Output, for/if, indentation) · `flow_chain` / `node`+`connector` (the data-flow/architecture) · `step_list` | **`algorithm_block`** when the *exact steps, loops, Input→Output* matter (a training loop, an optimizer, a derivation); a **flow/architecture diagram** when the *data path between modules* is the point; **often BOTH** — the block for precision + a small diagram for intuition. Don't bury a precise procedure in prose. |

**Cross-links:** pick the **chart type** in `data-viz.md` (editable-native vs raster); reach for the
exact **component** in `design-gallery.md`; place safely with the `deckkit` helpers in SKILL.md step 4.

## How the planner uses this (the Form ledger)
For every **content** slide, the plan records one Form-ledger row — `slide | visual protagonist |
format-family (card / chart / diagram / quote / big-number / timeline / table / photo) | build?` — plus,
in the per-slide Layout cell, the winner **and** the alternative it beat: e.g. *"dumbbell — beats
bar+table because the per-item before→after gap IS the point; a bar hides the pairing."* The **diversity
gate** then runs against the ledger: if any one format-family exceeds **~40–50%** of the content slides,
the plan is **not ready** — rework the weakest into the form its content actually wants. (Taste, not a
quota: a genuinely card-shaped run is allowed *with a one-clause justification in the ledger* — the gate
is auditable, never silent.)
