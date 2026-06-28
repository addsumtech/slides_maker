# Icons — one coherent family, recolored to the deck, used with restraint

Icons can lift a deck (label categories, mark sections, give a card a focal point) — but used
badly they make it look *worse* (a mismatched zoo, decorative clutter, the same junk as emoji
in titles). The whole value is **consistency**: a coherent icon family is an *identity system*
(CRAP "Repetition"), and a single icon gives a block a focal point (CRAP "Contrast"). Get those
two right and icons read as "designed"; get them wrong and they read as AI-slop.
**But whether to use an icon family at all is scenario-dependent.** The 7 jobs below are
*content-driven*; the *dosage* is gated by **register, delivery, and preset** (see "Scenario fit").
Some decks should use **no icon family at all** — they have a native device instead.

## Design them yourself, or fetch them? — FETCH, from one open-licensed family
**Do not hand-draw an icon set.** Hand-/AI-drawn icons come out inconsistent — varying stroke
weight, optical size, corner radius, metaphor — which is exactly the inconsistency that looks
amateur. A curated library is a *system*: hundreds of icons on one grid, one stroke weight, one
visual language. That coherence is the point. (The only acceptable "self-drawn" mark is a trivial
geometric primitive deckkit already draws — a dot, arrow, plus, check — or a case where literally
no library icon fits; even then match the deck's stroke language.)

**Pick ONE family per deck**, to the deck's mood (all permissive licenses — no attribution needed):

| family (`spec` prefix) | look | license | best for |
|---|---|---|---|
| `tabler:` (+ `tabler-filled:`) | crisp, minimal line | MIT | default; corporate / product / clean |
| `lucide:` | clean, neutral line | ISC | minimal / editorial |
| `phosphor:` (+ `phosphor-bold:`) | friendly, rounded line | MIT | approachable / teaching / playful |
| `feather:` | spare, thin line | MIT | very minimal |
| `heroicons:` (+ `-solid`) | corporate line/solid | MIT | enterprise / stakeholder |
| `simple:` | **brand / tech logos** (GitHub, Python, AWS…) | CC0 | representing actual products/tech |

**Some presets take NO icon family** (see *Scenario fit* below) — pick a family only after
confirming the preset is icon-native, not as a reflex on every deck.

Mixing two *content* families on one deck is a consistency tell — don't. (Exception: a `simple:`
brand logo can sit alongside your one content family, since logos are their own category.)
Use `simple:` to **name** a tech/tool inline (it is monochrome and recolored to the deck accent) —
**never as a credibility / proof / partner logo**: on a logo wall or any proof-of-traction slide
use the **real full-colour brand asset** (design-by-purpose "Real assets first") or omit it; never
recolor a customer/partner logo to the deck accent (a wrong-colour look-alike is a fidelity issue).
**SVG Repo** has **mixed per-icon licenses** — prefer the curated sets above; if you must use it,
check that icon's license and attribute when the license requires it.

## Mechanism — fetch → recolor → rasterize → place
python-pptx can't reliably embed SVG, so rasterize to a **transparent high-DPI PNG** (renders
identically in PowerPoint / Keynote / the LibreOffice render / the critic) and recolor to the deck
palette first. `scripts/icons.py` does it; `deckkit.icon()` / `icon_card()` place it.

```python
from icons import icon_png            # scripts/icons.py
import deckkit as dk
ACC = "#1F5FA8"                        # the deck accent
p = icon_png("tabler:chart-bar", "assets/icons/chart.png", color=ACC, px=160)  # fetch+recolor+raster
dk.icon(s, p, x, y, 0.42, disc="#E8F0FA")        # a single icon (optional tinted tile behind it)
dk.icon_card(s, *col, p, "Analytics", "Track what matters", accent=dk.ACCENT, disc="#E8F0FA")
```
- Keep recolored PNGs in `~/Downloads/<deck>/assets/icons/` (reproducible from the build).
- **Rasterizer:** `icons.py` tries cairosvg → rsvg-convert → headless Chrome (the last is usually
  present). If none exists it errors clearly — `pip install cairosvg`, or install Chrome/Chromium.
- **Offline / exact-name unknown:** pass a **local `.svg` path** to `icon_png()` instead of a spec
  (the user can drop an SVG in), or check the library's site for the exact kebab-case name.

## Scenario fit — dosage by register, delivery & preset (decide BEFORE you pick a family)
The 7 jobs are **content-driven**; the **dosage** is **scenario-driven**. Two gates run first.

**Gate 1 — register & delivery (purpose).** The DEFAULT on sober / figure-dominated decks is *no icons*.

| register / context | icon dosage | what carries it instead |
|---|---|---|
| Thesis / committee defense | **none** (default) | numbered contributions (`big_numeral`), typographic hierarchy, whole figures/tables; status via a sober chip / bold text — not an alert/star icon |
| Conference talk · lab meeting · job-talk **deep-result** slides | **none–sparingly**; only structural #1 (long arc) / #3 (inside a diagram) / #4 (diagram entity) | a larger hero figure + whitespace; ghost/numeral wayfinding; an annotation box/arrow on the figure for "look here" |
| Job talk — **program-map & dividers** | **moderate**, concentrated here (#1 + #3 on the program colour) | on deep-result slides the annotated figure carries it — no icon; let program colour do the wayfinding |
| Research **poster** | **sparingly** — small region-header marks (Method/Results) + diagram-entity marks; **always text-labelled** (no speaker); never competing with the focal result | large typographic region headers; enlarge the focal figure (a poster has no "sparse area" to anchor) |
| Company / stakeholder / **exec readout** | **strong but restrained** — #1 dividers, #3 ≤5 category cards, #7 status | **stat furniture** (`scorecard`/`change_stat`/status chips) on KPI tiles — **not** an icon per tile. A status icon + status hue + label encodes state **colour-blind-safely** (a sanctioned use) |
| Product / **sales pitch** | **strong** — #2 ≤5 benefit cards, #1 dividers | the **real full-colour logo** on a proof/partner slide — never a recolored `simple:` look-alike |
| **Investor** pitch | **sparingly** — #1 arc dividers only; NOT #2/#3 on stat slides | `stat_row`/`big_numeral`/`scorecard`/`leaderboard`; real headshots; a quadrant for competition |
| **Webinar** / online | **moderate** — #1 agenda spine; use a heavier weight + `disc=` and stay in the central safe area so it reads when shrunk in a video window | a larger text label where an icon would be sub-legible |
| **Teaching** / lecture | **strong** — #1 per concept-stage, #3 per-concept hue, #2 ≤5 distinct, #5 distinct-action steps | **split** a long list across slides (≤5 cards each) or a numbered `step_list`; subtract for sparse slides — don't anchor every one |
| **General** (no strong purpose) | **content-driven** — scan per slide; `tabler` default, `phosphor` for a teaching register | fix by subtraction where no job is present |

Hard carve-out (any purpose): **no icon on an evidence slide** — a slide whose hero is a source
figure, results table, or typeset equation. The icon competes with the thing the audience came to
read; icons live on structural / navigation / framework slides, not on the result.

**Gate 2 — preset (style).** Before picking a family, check the active preset. If it is an AVOID
preset, do **not** staple on an icon family — reach for the device named.

- **FIT — icon-native:** `dark_tech`, `consulting`, `glassmorphism`, `blueprint` (**line only** —
  filled clashes with the schematic), `swiss` (**sparingly, mono or the one red**, not colour-coded-per-category).
- **CONSTRAINED:** `memphis` / `risograph` — only **bold/filled marks flattened to the 2-ink / accent
  palette**, and prefer the preset's native motifs; `editorial_report` — at most **one restrained
  monochrome wayfinding mark on dividers**, no icon-card grids.
- **AVOID — use the native device:**
  - `ink_wash` · `eastern_traditional` → `deckkit.seal` + `cjk_numeral` (a Tabler/Lucide card grid is
    the same machine-translated-template tell as emoji, in vector form).
  - `editorial_paper` · `luxury_dark` → full-bleed photography + serif/italic numerals + hairlines +
    restraint ("icons feel cheap" here — they multiply an accent the preset keeps to one).
  - `museum_memorial` → `year_badge` chronology + archival `duotone` + `catalogue_frame`.
  - `brutalist` → heavy rules + blocky/filled marks at the rule weight + big raw numerals
    (quality-mark 5's "filled for bold" does NOT mean reach for the icon library here).

Cross-cutting: any **photography-and-restraint** preset (light or dark luxury, museum,
editorial_report) treats decorative chrome as *cheapening* — reach for photography, serif/italic
numerals, hairlines, duotone, not an icon family.

## The jobs an icon does — when to reach for one (the "why", + the rule-of-thumb)
**Core principle: an icon must REDUCE cognitive load, not decorate.** Reach for one only when it does
a real *job* — a recognition shortcut the audience reads **before** the words. The recurring jobs (scan
each slide for these; most decks use two or three, not all):

1. **Label a section / wayfinding** — a per-section mark reused on each divider so the audience always
   knows where they are (method = `tabler:settings`, results = `chart-line`, conclusion = `flag`). One
   icon per section, repeated deck-wide — this is the strongest, lowest-risk use. **But where the
   deck already carries numeral/typographic wayfinding (swiss ghost numerals, `big_numeral`,
   `cjk_numeral`) an icon section-mark is redundant — pick ONE wayfinding system; on minimal/academic
   decks prefer the numeral and skip the icon.**
2. **Turn a SHORT list of DISTINCT attributes into scannable cards** — when each item is its *own*
   concept (Fast · Accurate · Easy → `bolt` · `target` · `thumb-up`), a category icon per card speeds
   the scan (`icon_card`). **⚠ This is NOT "an icon on every bullet":** it applies to a *few* (≤~5)
   genuinely distinct categories, each a different idea — a long or homogeneous bullet list gets noise,
   not help (see Hurt). The test: would each item still need its *own* picture if you removed the text?
   The **≤5 count is per card-group, not per deck**: a long list is a candidate for *neither* treatment —
   **split** it across slides (one idea per slide, ≤5 distinct cards each; `content-planner.md`) or, if
   it is a sequence, use a numbered `step_list` (#5) with the numbers as the cue, not an icon per row.
3. **Separate categories / build hierarchy** — in a multi-category layout (Input · Training · Eval ·
   Output) an icon per category, **colour-coded** (quality mark 2), makes the grouping legible at a
   glance; colour + icon together encode "which group".
4. **Stand in for a repeated entity** — a recurring concrete noun (dataset, database, user, cloud,
   model, GPU) gets ONE consistent icon reused everywhere it appears (esp. in diagram nodes), instead of
   re-typing the word; the icon becomes the deck's shorthand for that thing.
5. **Guide reading order** — icons paired with numbers/arrows in a sequence (Analyze → Process →
   Result) cue the path (`step_list`, or `flow_chain` with an icon per node). In a sequence the
   **number is the primary cue**; add a per-step icon only when each step is a **distinct action with
   its own metaphor** (mix → measure → observe) — a same-kind step list stays numbers-only.
6. **Anchor a sparse slide** — ONE large, on-topic icon (or a simple illustration / a thin divider)
   balances an empty slide better than enlarging the text. This is the *sanctioned* way to fill space —
   it composes with the "don't inflate a block / don't oversize body text to fake fullness" rule: a
   single focal icon is legit; a blown-up paragraph is not. **Never** anchor a slide whose hero is a
   real figure / results table / equation (enlarge the figure or add whitespace instead), and anchor
   sparse framing/divider slides **selectively** — a generic mark repeated across many
   objectives/recap/transition slides becomes wallpaper (see Hurt); prefer the section's own wayfinding
   mark, and on an academic deck a numeral or thin rule is often better.
7. **Flag status / importance** — a meaning-bearing mark for warning / key idea / contribution /
   recommendation (`alert-triangle` · `bulb` · `star` · `circle-check`), used **sparingly** so it stays
   a signal, not wallpaper. In a **status readout**, a status icon + the status hue + a text label
   together encode state **colour-blind-safely** (satisfies the no-colour-alone rule) — a sanctioned,
   not decorative, use; still keep it to the status cells, not every row.

**The rule-of-thumb — apply to EVERY icon before it ships.** It must answer at least one of:
**(1) What is this? · (2) What does it do? · (3) Why should I pay attention?** — *before* the audience
reads the text. If an icon answers **none** of the three, it is decoration, not communication → **cut
it.** (This is the single test that separates a designed icon system from AI-slop sprinkle.)

## When icons HELP vs HURT
**Help** (use): a **row of feature/category/section cards** each marked by an icon; a **section
divider** or wayfinding mark reused per section; a **brand/tech logo** (`simple:`) to name a real
product; a single focal icon in a callout/stat tile. The test: the icon **aids recognition or
labels a category** the audience scans.

**Hurt** (cut): an icon on **every bullet** (clutter, not information); a **decorative** icon that
labels nothing; **mismatched families** on one deck; an **oversized** icon competing with the title;
an icon **carrying meaning with no text label** (fails accessibility + ambiguous); a literal/cheesy
metaphor (a lightbulb for "idea" on every slide). Also HURT: an icon on **every KPI / scorecard /
stat tile** (a number is the focal point — the icon beside it is decoration); an icon on an
**evidence slide** (figure / results table / equation hero — it competes with the result); **every
slide the same icon-card grid** (the deck-rhythm "one template repeated" flaw — vary the protagonist:
chart / diagram / photo / plain breath); and **register-wrong** icons — well-crafted, colour-coded
icons used decoratively on a **sober, figure-dominated academic deck** (defense, conference/results,
lab meeting, job-talk deep results) or on an **AVOID preset** (see Scenario fit), where the fix is to
remove them and let the figure / numbered structure / native device carry the slide.
Icons are seasoning — a few, consistent, purposeful.
**Never** substitute emoji or ✅/🚀/🔥 for real icons (that's an AI-slop tell, see design-principles).

## What makes icons look GOOD — five qualities (from real well-iconned decks)
A good icon slide gets ALL of these right; getting one wrong is what makes icons look tacked-on.

1. **Semantic fit — the metaphor matches the content it labels.** Pick the icon whose meaning *is*
   the thing: an **eye** for "perception", a **brain** for "reasoning", a **bolt** for "action", a
   **database** for "memory"; a **magnifier** for "parse", a **target** for "select", a **plug** for
   "execute", a **check** for "validate", a **retry/refresh** for "recover", **layers** for "deliver".
   A generic or mismatched icon (a gear on every card) is worse than none — it mislabels.
2. **Colour-coded by category — each category its OWN hue, and the icon carries it.** In a multi-
   category layout (layers, sections, steps, problem areas) give each category a distinct accent and
   make the **icon, its label, its card tint, and any pill/number all share that one hue** — so colour
   itself encodes "which group". Derive the N hues from `deckkit.palette(n)` (distinct, contrast-
   checked) and apply one per category, consistently. (This is the single biggest "looks designed"
   move — NOT one global accent on every icon when the layout has real categories.)
3. **Contrast against the background.** On a **dark deck**, icons are **bright/saturated** accent
   colours, often in a **disc/tile** that lifts them off the card (a deep-tinted disc on a dark card
   with a bright icon, or a dark disc on a colour-banded header with a light icon). On a **light deck**,
   a saturated accent icon (never pale-grey, never pure black). Aim ≥3:1 icon-vs-its-immediate-
   background so the shape reads. The `disc=` tile is the easy way to guarantee contrast.
4. **Consistent position & size across siblings.** Pick ONE placement and repeat it: **upper-left of
   the card** (`icon_card`, the default) or **centred at the top** of a step/pipeline card — every
   sibling the **same family, size, colour-treatment, and position**. Size small, to ~heading scale
   (**≈0.32–0.5 in**), and **never larger than the title** (font-hierarchy). One odd icon breaks it.
5. **Design style matches the deck — or use none.** Outline icons for a clean/minimal/technical deck
   (the dark "glowing line" look pairs thin line icons); filled/solid only for a bold **corporate**
   deck (`consulting`, `glassmorphism`). For a bold **print/zine** register (`brutalist`, `risograph`,
   `memphis`) the bold comes from heavy rules, halftone duotone and motif sets — **not** the icon
   library; use icons there only if flattened to the print palette. And some presets take **no** icon
   family at all (see *Scenario fit* — Gate 2). The icon weight should echo the deck's type/stroke;
   don't mix outline and filled across siblings.

## Placement patterns + the craft
- **Upper-left corner of a card** (`icon_card`) — default and strongest: icon top-left (bare or in a
  `disc=` tile), title under it, body below; the eye lands on the icon then reads down.
- **Centred at the top of a step card** — for a pipeline/numbered sequence (often a number circle
  above + icon + label + an output line + a bottom pill), the icon centred, recolored to that step's
  hue; consider highlighting the terminal/success step.
- **In a colour-banded header** — icon in a circular disc inside a per-card accent band, with the
  category label beside it (good for a 3-up problem/feature panel).
- **Other:** above a centred big-number/stat; inline just before a chip/section label (vertically
  centred with the text); a light icon inside a solid accent bar.
  Whatever you pick, apply it the **same way everywhere**.
- **Accessibility:** an icon is *support* — the **text label always carries the meaning**, never an
  icon alone. Set `alt=` when informative; keep the icon legible against its background.

## Build checklist
One family · **semantic fit** (metaphor matches the content) · **colour-coded per category** (each
category its own hue from `palette(n)`, carried by the icon + label + tint) · **contrast** against the
background (bright on dark / saturated on light, disc if needed) · small (≤ title) · **consistent
size/position/treatment** across siblings · style matches the deck (outline vs filled) · **does a job**
(passes the rule-of-thumb — answers *what is this / what does it do / why pay attention*; else cut) ·
text always present · assets cached in the deck folder.
