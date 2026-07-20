# Design gallery — styles & components mined from professional decks

A reference vocabulary distilled from a close page-by-page study of 21 professionally-designed
sample decks (280 slides). Use it to (a) pick a coherent *style* fast, and (b) reach for the right
*component* instead of reinventing it. Everything here maps to a `presets.py` preset or a `deckkit`
helper. The craft rules in `design-principles.md` still govern; this is the catalogue.

## Table of contents
- The style presets (one switch = palette + fonts + surface)
- Cross-cutting techniques every strong deck uses (the "instantly professional" moves)
- The component catalogue (reach for these, don't reinvent)
- Reproduction notes

## The style presets (one switch = palette + fonts + surface)
| preset | register | signature moves |
|---|---|---|
| `swiss` | minimal / typographic | strict grid, one red, huge type-scale ratio, ghost numerals |
| `editorial_paper` | light luxury magazine | warm paper, Georgia serif, gold, big photography |
| `editorial_report` | FT/Bloomberg **dark** data | near-black, one red + amber, micro-charts, serif headers |
| `glassmorphism` | premium SaaS / launch | frosted glass cards on a dark gradient, glow |
| `memphis` | playful / festival | cream + vivid geometry, terrazzo, Arial Black |
| `risograph` | zine / DIY | halftone in 2 inks + the navy neutral, mis-registration `offset_shadow`, hand-cut type |
| `brutalist` | newspaper / annual report | black/white/red, Arial Black, mono, **heavy rules**, dense grid |
| `blueprint` | engineering schematic | deep navy, cyan line-art nodes, mono eyebrow, one coral focal |
| `dark_tech` | AI/infra/eng (dark) | near-black, multi **semantic** accents, **white `diagram_island`s**, mono brand, gradient header |
| `consulting` | MBB strategy / board | white, **action titles** + `insight_banner`, navy→emerald `gradient_rule`, 5-colour semantic |
| `ink_wash` | Chinese ink (藏拙) | warm paper, ink, one `seal`, KaiTi, `cjk_numeral`, 留白 |
| `eastern_traditional` | 传统色 heritage | warm paper, ochre+sage, KaiTi, colour-as-content |
| `luxury_dark` | dark fashion/luxury | near-black, ONE champagne accent, photography supplies colour |
| `museum_memorial` | midnight memorial / exhibition | navy + brass gold, archival `duotone`, `year_badge`, serif gravitas |

Pick the preset to the purpose+mood, then **vary it** — these are starting languages, not locks.
The one exception: each preset carries a **`guard`** string (its 1–3 register-defining constraints,
e.g. swiss "ONE red only", luxury_dark "ONE champagne accent") — the designer/builder honor
`p["guard"]` literally and the critic flags any violation as a register break; guards survive the
"vary it" rule. **Precedence:** a guard is a register floor for the SKILL'S OWN choices only — an
explicit user request or a recorded named deviation (the plan line naming the guard it overrides)
lifts it, and the critic treats a recorded guard deviation like the stylized-illustration
deviation: a taste call, not a register break. A guard binds only when its preset is the deck's
**declared register**; a component borrowed into another register (Mode-B mimic, glass variants on
an image-backed page) obeys the HOST register's guard (and the component's own physical
legibility rules).

## Cross-cutting techniques every strong deck uses (the "instantly professional" moves)
- **Semantic colour contract** — bind ONE hue to each concept (navy=structure, green=good/safe,
  red=risk, amber=brand) and propagate it to icons, headings, badges, table columns AND chart series.
  Teach the legend on slide 2, reuse deck-wide. See `semantic-color-contract.md`; build with
  `palette()` / `accent_one` and pass the same hue everywhere.
- **Action titles** (consulting) — make each slide title a *complete-sentence conclusion* ("Only 19%
  of customers return — a critical retention gap"), then restate the implication in an `insight_banner`.
- **Inline keyword highlight** — recolour exactly ONE phrase in a headline (and a few per body line)
  with `highlight("…<k>the phrase</k>…", size, ink, accent)` — a scannable second reading layer.
- **Bilingual lockup** — pair a heavy CJK/serif headline with a wide-tracked ALL-CAPS Latin/pinyin
  strap (`bilingual_lockup`). The single most universal "designed" device for CN/EN decks.
- **Ghost numeral** — a giant 8–18% faint ordinal/year behind a card/section as silent wayfinding +
  texture (`ghost_numeral`, the bg-aware version that works on **dark** decks too — `big_numeral(mode=
  'ghost')` is light-only). Use `big_numeral`/`stat_row` for a *foreground* hero figure.
- **Light/dark pacing + section dividers** — punctuate quiet light content pages with the occasional
  **full-bleed dark divider** carrying a giant numeral + bilingual chapter title; dividers silently
  absorb numbering gaps. Two-mode rhythm structures most long editorial decks.
- **Gradient brand rule** — a thin two-stop `gradient_rule` (navy→emerald, amber→blue) under titles /
  along an edge as a signature. Gradient ONLY the hero element, never body text (where the preset
  guard permits — swiss/riso ban it).

## The component catalogue (reach for these, don't reinvent)
- **Diagrams (general):** `node` + `connector` (+ `flow_chain`) — rebuild ANY architecture/flowchart
  from rounded-rect/pill/circle nodes (+ diamond/parallelogram/cylinder when formal flowchart
  notation applies — see the Standard-notation crib) joined by connectors with **stroke semantics**
  (solid=required · dashed=optional · dotted=feedback/inferred); promote exactly ONE node to `hub=True`.
  **Connectors dock on EDGES, both ends** — pass block rects to `connect_boxes(a, b)` /
  `hub_spokes(hub, spokes)` (or `edge_point(rect, toward)` for one end) so no arrow ever emerges from
  a block's centre across its own label; the `CONNECTOR_IN_BOX` lint enforces it. On a dark deck
  host the diagram in a bright `diagram_island` ("Figure N"). `concentric_rings` for nested frameworks
  (CMT 色彩·材质·纹理); `hub_spoke`/`quadrant`/`timeline` for those specific shapes.
- **Layered-card vocabulary (modern-SaaS polish):** `kpi_card` (hairline card = tinted `icon_chip`
  + label + DELTA pill top-right + big value + muted sub + optional `conclusion_strip`) ·
  `icon_chip` (accent-tinted squircle, accent icon) · `conclusion_strip` (the accent-tinted so-what
  bar that closes a card) · `tint(color, frac)` (the pastel surface mixer behind all of these — pass `base=` to mix toward a
  dark canvas instead of white). On an image-backed or dark page use the glass variants —
  `kpi_card(fill="glass")` / seat on `glass_card` — the opaque white defaults are for light flat canvases.
  These add the micro-design layering that makes cards read *product-designed* — use them WITH the
  chrome budget (tints are content-surface, not chrome) and never as a same-height card wall.
  **Old-vs-new procedure:** `flow_compare` — parallel stage rows, highlighted bottleneck, result
  chips, transition marker. **Exec/board cover pattern:** a compact 3-KPI strip (value + one-word
  label ×3) above the fold gives a readout cover its hook — build from `kpi_card`-lite or `stat_row`.
- **Cycle / loop / flywheel:** `cycle_diagram` — 3–6 nodes on an ellipse with collision-free labels
  (diagonal `start_deg=-45` is the safest 4-node layout), optional icons, hub label, and a dashed
  reinforcing-loop arrow routed over the top. **Before→after scoreboard:** `dumbbell_board` — one
  dumbbell row per metric on its own honest scale, single-line name+sub, hero-row accent, optional
  threshold tick (the "crosses 100%" moment). Both encode geometry that previously needed
  per-deck debugging — reach for the component before hand-composing.
- **Process / steps:** `step_list` (vertical numbered spine OR horizontal connected pills with an
  accented terminal step), numeral_style arabic/pad2(01)/cjk.
- **Consulting furniture:** `insight_banner` (so-what bar), `cta_button`/`cta_pair`, `status_stamp`
  (CONFIDENTIAL / SOLD OUT), `corner_tab` (RECOMMENDED), `spec_card` (mono key→value placard).
- **Editorial furniture:** `pull_quote` (italic-serif + big quote-mark + attribution), `standfirst`
  (italic dekker under a headline), `year_badge` (chronology pill), `concept_equation` (ZINE =
  MAGAZINE word-equation headline).
- **Micro-viz (cheap, legible):** `dot_meter` (●●○), `tradeoff_list` (green + / red −), `segmented_bar`
  (cumulative 100%). For KPIs use `scorecard`/`stat_row`/`change_stat`; for ranked-to-chart use
  `leaderboard`; for the so-what use `takeaway_rail`.
- **Decision & strategy furniture:** `eval_matrix` (options×criteria grid — `harvey_ball` fifths-fill
  glyphs or semantic ✓/◐/✕ marks, `recommend=` tints the winning column + a RECOMMENDED tab; the
  qualitative scoring `table` can't give) · `heat_matrix` (category×category grid coloured by value,
  `scale="seq"|"div"|"risk"`, contrast-aware cell text — the designed risk/prioritization matrix) ·
  `tier_stack` (one taper core: `mode="funnel"` conversion drop-off / `mode="pyramid"` proportional
  tiers, semantic ramp + optional `values`; `funnel()`/`pyramid()` wrappers).
- **Plan / time:** `gantt` (task bars on a shared `axis_scale` — `lanes=` swimlanes, `today=` marker,
  `ticks/tick_labels=` a quarter grid; durations & overlap, where `timeline` shows only dated points) ·
  `waterfall` (raster recipe — a total's rise/fall/total walk).
- **Product / UI:** `device_frame` — a real screenshot clipped into a `chrome="browser"` (window +
  traffic-lights + URL pill) or `chrome="phone"` (bezel + notch) bezel, so the shot reads as the
  product, not a floating rectangle. For a pitch/product/teaching deck showing an actual app/site.
- **Compose-from-primitives recipes (no dedicated helper):** **team roster** — circular
  `picture(fit="cover", round=…)` headshots on a `columns(n)` grid + name/role/bio, one avatar
  diameter/accent/alignment across all cards. **Org / issue / driver tree** — `node` + `elbow_connector`
  as a branch bus (parent drop → horizontal bus → even child drops), left-to-right for a driver tree —
  and default a tree of **5+ levels** to horizontal left-to-right (depth reads better as width)
  unless the canvas is portrait/width-starved — name the deviation.
  **System architecture** (the multi-layer system diagram) — (1) classify components into role LAYERS
  (clients · gateway · services · data · infra); (2) one layer per **column** (left-to-right for data
  pipelines / request flows — users left, stores right) or per **row** (top-to-bottom for layered
  stacks — clients top, infra bottom); (3) stack a layer's components with even gaps; (4) dashed `box()`
  region boundaries around groups sharing infrastructure; (5) arrange the layers so that **most**
  edges join adjacent layers — a genuine skip edge is kept, routed as a demoted elbow around the
  layer stack, never deleted or re-terminated to satisfy the layout. Shared middleware = ONE
  horizontal bus bar (its own semantic colour) with short vertical
  taps — never N-to-N arrows. Colours bind via the semantic colour contract. On a one-accent
  preset (blueprint/swiss) encode layers by outline weight/dash + region boundaries, not extra
  hues; the bus bar takes the base line colour.
  **Decision flowchart** — the happy path runs straight along ONE spine; at each decision the success
  branch continues on the spine and the other branch exits to ONE consistent side; branches rejoin via
  `elbow_connector`; loop-backs route around the far edge via `loop_path`. Outcome labels sit ON the
  exit arrows near the decision, coloured by the semantic contract (good=proceed · risk=reject);
  error/exception paths dashed in the risk colour; spine connectors full-strength, branch connectors
  blended/demoted so the main story reads first.
  **Venn** — 2–3 translucent `glass_card`/`box` circles with labeled overlaps. **Agenda / section
  tracker** — a quiet nav rail of sections with the current one accented (or `step_list(active_idx=…)`
  on an agenda page). **Geographic map** — a license-clear/computed base map as `picture` + native
  markers/labels on top (never bake labels into a generated map). (Recipes routed from `form-selection.md`.)
- **Standard notation (technical audiences read these literally — draw them correctly):**
  *Flowchart:* rounded rect = start/end · rect = process · `node(shape="diamond")` = decision ·
  `node(shape="parallelogram")` = input/output · `node(shape="cylinder")` = data store.
  *Sequence:* vertical lifelines; solid arrow = sync call · open head (`connector(head="open")`) =
  async · dashed + open head = return.
  *State machine:* filled dot = initial · bullseye = final · transitions labelled `event [guard] / action`.
  *UML / ER (compressed):* solid line + empty triangle = inheritance · filled diamond at the owner
  end = composition · dashed + open head = dependency · crow's foot = cardinality.
  This notation binds for **formal flowcharts drawn for technical audiences**; free shapes
  (rounded-rect/pill/circle) are fine for conceptual box-flow. Stroke semantics are
  **per-diagram-type** — the solid/dashed/dotted house contract governs box-flow; the
  sequence/decision recipes override it locally; never mix the two registers in one diagram; note
  which register the slide uses in the design plan.
  Caveat: if the source already HAS the UML/ER figure, extract it whole (`design-principles.md`) —
  don't redraw it.
- **Photography on-brand:** `image_fx.duotone(img, ink_a, ink_b)` / `grayscale(img)` so a colour photo
  doesn't fight the accent (riso/brutalist/ink/luxury/museum), then `picture(fit="cover")`.
- **East-Asian:** `seal` (vermilion chop), `cjk_numeral` (壹贰叁), `bilingual_lockup` — see
  `east-asian-aesthetic.md`.
- **Math:** `equation_native` (editable LaTeX-subset) for *math* — `equation_png` for 2-D; `concept_equation` for a *word*-equation headline.
- **Algorithms / pseudocode (CS·AI):** `algorithm_block` — a LaTeX-`algorithm`-environment-style block
  (booktabs rules or `boxed=True`, numbered indented lines, auto-bolded keywords Input/Output/for/if/
  while/return/end…) for a *training loop, optimizer, or method procedure*. Use a `MONO` font; pair the
  exact steps with one prose line of intuition. The right form for "describe the method as exact steps."
- **Explaining a principle/mechanism:** don't state it as text alone — put a **labelled schematic
  diagram beside it** (`node`+`connector` for box-flow; a **science schematic** — force/ray/circuit/
  apparatus/vector — via **matplotlib/domain-lib** for precise ones or the **image tool** for stylized/
  template-matched ones, per `references/schematic-diagrams.md`; an annotated whole figure; or an
  `equation_png` when the law *is* the relation), so the reader *sees* the
  forces/signal-path/geometry/cause→effect. Build it **domain-accurate** — a wrong schematic is worse
  than none.

## Reproduction notes
- python-pptx can't embed SVG → rasterise (icons via `icons.py`, figures from PDFs via `extract_pdf.py`).
- Gradients: `gradient_rule` (real 2-stop gradient fill) works; gradient *text* isn't portable — keep
  hero numerals flat, spend the gradient on the rule.
- Always set `EAFONT`/`EADISPLAY` on any CJK deck (the lint flags CJK-without-EA-font → tofu).
