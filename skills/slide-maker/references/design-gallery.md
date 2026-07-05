# Design gallery — styles & components mined from professional decks

A reference vocabulary distilled from a close page-by-page study of 21 professionally-designed
sample decks (280 slides). Use it to (a) pick a coherent *style* fast, and (b) reach for the right
*component* instead of reinventing it. Everything here maps to a `presets.py` preset or a `deckkit`
helper. The craft rules in `design-principles.md` still govern; this is the catalogue.

## The style presets (one switch = palette + fonts + surface)
| preset | register | signature moves |
|---|---|---|
| `swiss` | minimal / typographic | strict grid, one red, huge type-scale ratio, ghost numerals |
| `editorial_paper` | light luxury magazine | warm paper, Georgia serif, gold, big photography |
| `editorial_report` | FT/Bloomberg **dark** data | near-black, one red + amber, micro-charts, serif headers |
| `glassmorphism` | premium SaaS / launch | frosted glass cards on a dark gradient, glow |
| `memphis` | playful / festival | cream + vivid geometry, terrazzo, Arial Black |
| `risograph` | zine / DIY | 2-ink halftone, mis-registration `offset_shadow`, hand-cut type |
| `brutalist` | newspaper / annual report | black/white/red, Arial Black, mono, **heavy rules**, dense grid |
| `blueprint` | engineering schematic | deep navy, cyan line-art nodes, mono eyebrow, one coral focal |
| `dark_tech` | AI/infra/eng (dark) | near-black, multi **semantic** accents, **white `diagram_island`s**, mono brand, gradient header |
| `consulting` | MBB strategy / board | white, **action titles** + `insight_banner`, navy→emerald `gradient_rule`, 5-colour semantic |
| `ink_wash` | Chinese ink (藏拙) | warm paper, ink, one `seal`, KaiTi, `cjk_numeral`, 留白 |
| `eastern_traditional` | 传统色 heritage | warm paper, ochre+sage, KaiTi, colour-as-content |
| `luxury_dark` | dark fashion/luxury | near-black, ONE champagne accent, photography supplies colour |
| `museum_memorial` | midnight memorial / exhibition | navy + brass gold, archival `duotone`, `year_badge`, serif gravitas |

Pick the preset to the purpose+mood, then **vary it** — these are starting languages, not locks.

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
  along an edge as a signature. Gradient ONLY the hero element, never body text.

## The component catalogue (reach for these, don't reinvent)
- **Diagrams (general):** `node` + `connector` (+ `flow_chain`) — rebuild ANY architecture/flowchart
  from rounded-rect/pill/circle nodes joined by connectors with **stroke semantics** (solid=required ·
  dashed=optional · dotted=feedback/inferred); promote exactly ONE node to `hub=True`. On a dark deck
  host the diagram in a bright `diagram_island` ("Figure N"). `concentric_rings` for nested frameworks
  (CMT 色彩·材质·纹理); `hub_spoke`/`quadrant`/`timeline` for those specific shapes.
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
