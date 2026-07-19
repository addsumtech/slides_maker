# Icons — one coherent family, recolored to the deck, used with restraint

Icons can lift a deck (label categories, mark sections, give a card a focal point) — but used
badly they make it look *worse* (a mismatched zoo, decorative clutter, the same junk as emoji
in titles). The whole value is **consistency**: a coherent icon family is an *identity system*
(CRAP "Repetition"), and a single icon gives a block a focal point (CRAP "Contrast"). Get those
two right and icons read as "designed"; get them wrong and they read as AI-slop.
**Icons fit ANY topic — never excluded by subject or preset; what's scenario-dependent is the STYLE
and the AMOUNT.** The 7 jobs below are *content-driven*; the *style* (family/weight/treatment) and
*dosage* are tuned to the **register, delivery, and preset** (see "Scenario fit"). Even a deck with a
strong native device (a seal, photography) can carry a **style-matched** icon alongside it — the choice
is *which style and how many*, not *whether*.

## Table of contents
- Design them yourself, or fetch them? — FETCH, from one open-licensed family
- Mechanism — fetch → recolor → rasterize → place
- Treatments — VARY how the icon is shown (don't default to a flat monochrome drop)
- Scenario fit — MATCH the style & dose to the register (icons fit ANY topic)
- The jobs an icon does — when to reach for one (the "why", + the rule-of-thumb)
- When icons HELP vs HURT
- What makes icons look GOOD — five qualities (from real well-iconned decks)
- Placement patterns + the craft
- Build checklist

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
| `phosphor:` (+ `-bold` / `-fill` / `-duotone` / `-light` / `-thin`) | friendly rounded; 6 weights incl. **duotone** | MIT | approachable / teaching / playful; duotone for depth |
| `feather:` | spare, thin line | MIT | very minimal |
| `heroicons:` (+ `-solid`) | corporate line/solid | MIT | enterprise / stakeholder |
| `simple:` | **brand / tech logos** (GitHub, Python, AWS…) | CC0 | representing actual products/tech |

**There's a fitting icon style for ANY deck** — the families above span line / thin / rounded / sharp /
filled / duotone (Phosphor alone has 6 weights), so icons are never excluded by topic: you **match the
style and dose** to the register (see *Scenario fit* below), you don't decide *whether* icons are allowed.

Mixing two *content* families on one deck is a consistency tell — don't. (Exception: a `simple:`
brand logo can sit alongside your one content family, since logos are their own category.)
Use `simple:` to **name** a tech/tool inline (it is monochrome and recolored to the deck accent) —
**never as a credibility / proof / partner logo**: on a logo wall or any proof-of-traction slide
use the **real full-colour brand asset** (design-by-purpose "Real assets first") or omit it; never
recolor a customer/partner logo to the deck accent (a wrong-colour look-alike is a fidelity issue).
**SVG Repo** has **mixed per-icon licenses** — prefer the curated sets above; if you must use it,
check that icon's license and attribute when the license requires it.

**Icons are not diagrams.** When the content is a *domain mechanism* (a model architecture, a
k-space trajectory, a force diagram, a data path), a generic library icon is a downgrade, not a
visual: draw the schematic (`schematic-diagrams.md`). Icons mark categories, wayfinding, and
repeated entities — they never *stand in for* the mechanism the slide exists to explain.

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
dk.icon_card(s, *col, p, "Analytics", "Track what matters", accent=ACC, disc="#E8F0FA")
```
- Keep recolored PNGs in `~/Downloads/<deck>/assets/icons/` (reproducible from the build).
- **Rasterizer:** `icons.py` tries cairosvg → rsvg-convert → headless Chrome (the last is usually
  present). If none exists it errors clearly — `pip install cairosvg`, or install Chrome/Chromium.
- **Offline / exact-name unknown:** pass a **local `.svg` path** to `icon_png()` instead of a spec
  (the user can drop an SVG in), or check the library's site for the exact kebab-case name.

## Treatments — VARY how the icon is shown (don't default to a flat monochrome drop)
A bare recolored glyph is the *baseline*, not the only option — the same icon reads very differently
by **rendering** (how the glyph is filled) and by **container** (what sits behind it). Polished decks
(e.g. the glassmorphism reference) get their richness here: **duotone glyphs on translucent gradient
discs, colour-coded per category** — not flat icons scattered on a slide. Pick a treatment that fits
the deck and **apply it identically across siblings** (same shape/size/treatment; vary only the *hue*
to colour-code categories). The two layers, with the helpers that produce them:

**Rendering (icons.py — how the glyph itself looks):**
- **Outline** — `tabler:` / `lucide:` / `phosphor:` (the clean default).
- **Filled / solid** — `tabler-filled:` / `phosphor-fill:` / `heroicons-solid:` (heavier, more
  presence on a busy or dark slide).
- **Two-tone (duotone)** — `phosphor-duotone:` → a built-in light+solid look in ONE accent colour;
  the depth-y treatment the reference uses. The cheapest big upgrade from "flat".
- **Weight** — Phosphor spans `thin` / `light` / regular / `bold` (match the deck's stroke language;
  thin for archival/luxury, bold for punchy).
- **Gradient-filled** — `icon_png(spec, out, gradient=("#5B8DEF", "#A26BFA"))` fills the glyph with a
  two-stop gradient instead of one flat colour. Reserve for hero/feature icons (not dense rows).

**Container (deckkit — what sits behind/around it):**
- `icon(s, p, x, y, size, disc="#E8F0FA")` — bare, or on a simple tinted tile (the existing default).
- `icon_tile(s, x, y, size, p, shape=…, fill=… | grad=(c0,c1) | glass=True, sheen=…)` — the versatile
  tile: **circle / squircle / square**, **solid / gradient / frosted-glass**, optional top **sheen**.
  A gradient disc with a duotone glyph is the reference's signature lockup; `glass=True` (+ `glow()`)
  is the glassmorphism card; colour-code per category by changing only the tile hue.
- `icon_badge(s, x, y, size, p, ring=ACC)` — icon inside a thin accent **ring** (light, outlined;
  good on a light deck where a solid tile feels heavy).
- `icon_ghost(s, p_pale, x, y, big_size)` — an **oversized faint** icon as a watermark behind a
  card's content (recolor the PNG to a pale tint first); adds texture without clutter.
- `icon_card(s, …, disc=…)` — the upper-left feature-card pattern (icon + title + body).

**Pair treatment to surface:** flat/outline or a light `disc` on a clean light deck; **duotone or
gradient glyphs on gradient/glass tiles** on a dark/glassy deck; ring badges for an airy editorial
look; a ghost glyph to enrich an otherwise sparse card. Whatever you pick, keep it **one system** —
mixing tile shapes or rendering styles across sibling icons is the same consistency tell as mixing
families. Colour-coding categories (each its own hue, carried by tile + glyph + label) is encouraged;
random per-icon restyling is not.

## Scenario fit — MATCH the style & dose to the register (icons fit ANY topic)
**Icons are available on *every* deck — never excluded by topic or preset.** The libraries are vast and
stylistically diverse (outline · thin/light · rounded · sharp · filled · duotone · hand/brush, plus
brand logos — Phosphor alone ships 6 weights; Tabler/Lucide/Heroicons/Iconoir/Feather add more), so a
*fitting* icon style exists for any register, from a brutalist annual report to a delicate ink-wash
deck. The discipline is **choosing the right STYLE and the right amount** — NOT deciding *whether* icons
are allowed. The real failure modes are a **mismatched style** (a chunky SaaS line-icon grid stapled
onto a delicate ink/luxury deck) or **decoration** (an icon that does no job) — never icons per se.
Two questions, in order:

**A) Dosage — by register & delivery.** Match the AMOUNT and the JOBS to the register (always within
the rule-of-thumb + ≤5-per-card-group + the no-evidence-slide carve-out):

| register / context | dosage |
|---|---|
| Product / sales pitch · teaching · webinar · general | **strong** — category/benefit/step cards, section & wayfinding marks, status flags |
| Company / stakeholder / **exec readout** | **strong but restrained** — dividers, ≤5 category cards, status; NOT one icon per KPI tile (let `scorecard`/`change_stat` carry the number) |
| Conference · lab meeting · job talk · **thesis defense** | **minimal & structural** — wayfinding on a long arc, a category / diagram-entity mark inside a figure; keep icons OFF the deep-result/evidence slides and don't dress a contributions slide with them (a sober room reads a *cute* icon as padding — but a clean structural mark is fine, not forbidden) |
| Research **poster** | **sparingly**, always text-labelled, never competing with the focal result |

Hard carve-out (any register): **no icon on an evidence slide** — a slide whose hero is a source
figure, results table, or typeset equation (it competes with the result). And keep the **`simple:`
brand-logo rule:** the real full-colour logo on a proof/partner slide, never a recolored look-alike.
**On an icon-native, category-rich deck, shipping ZERO icons is a MISS, not restraint** — the
consistency device is exactly what the register is reaching for.

**B) Style — match the family/weight/treatment to the preset.** Every preset *can* carry icons; pick a
style that belongs (the wrong **weight** is the flaw, not the icon):
- `dark_tech` / `consulting` / `glassmorphism` / `blueprint` → crisp **line / sharp** icons — the
  obvious fit; **actively use them** on category-rich content (`blueprint`: line, not filled).
- `swiss` → minimal, **mono or the one accent**, sparing.
- `memphis` / `risograph` → **bold / filled** marks flattened to the 2-ink / accent palette.
- `editorial_report` → restrained **monochrome** marks.
- `editorial_paper` / `luxury_dark` → a **fine hairline / thin** icon in the one accent, used sparingly
  — photography still leads; a *heavy* icon feels cheap here, a *delicate* one is on-brand.
- `museum_memorial` → a fine, **archival-weight** mark alongside `year_badge` / `duotone`.
- `ink_wash` / `eastern_traditional` → the **`seal` + `cjk_numeral` stay the signature**; a generic SaaS
  line-icon *grid* still clashes (the machine-translated-template tell), but a **thin / brush-like mark
  recolored to ink**, used sparingly, composes fine — match the brush aesthetic, don't staple a Tabler grid.

The native devices above (seal, photography, `year_badge`) **lead and compose with** a style-matched
icon — they are never a reason to ship *zero* icons. When in doubt, pick the lightest/cleanest weight
that still reads, and use fewer.

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
chart / diagram / photo / plain breath); **style-MISMATCHED** icons — the wrong *weight/treatment* for
the register (a chunky generic SaaS grid on a delicate `editorial_paper`/`luxury_dark`/`ink_wash` deck;
a filled icon on `blueprint`) — where the fix is **restyle / use fewer / let the native device lead**,
NOT remove icons by topic; and **decorative** icons on a sober, figure-dominated slide (defense /
results / lab meeting) where a clean *structural* mark would be fine but dressing-up is not.
Icons are seasoning — a few, consistent, purposeful — but available on **any** deck in the right style.
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
5. **Design style MATCHES the deck — match the weight/treatment, never exclude by topic or preset.**
   Outline icons for a clean/minimal/technical deck (the dark "glowing line" look pairs thin line icons);
   filled/solid for a bold **corporate** deck (`consulting`, `glassmorphism`). For a bold **print/zine**
   register (`brutalist`, `risograph`, `memphis`) the bold comes from heavy rules, halftone duotone and
   motif sets — so flatten icons to the print palette and keep them structural. **No preset is icon-free
   by rule** — every preset *can* carry icons; pick the family's weight/treatment to fit the register (a
   heavy icon feels cheap on a delicate deck; see *Scenario fit — B) Style*). The icon weight should echo
   the deck's type/stroke; don't mix outline and filled across siblings.

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
category its own hue from `palette(n)`, carried by the icon + label + tint) · **contrast** — the glyph
must clear ~3:1 against **whatever it sits ON**: against the slide for a bare icon (bright on dark /
saturated on light), and against **its TILE** for a tiled icon. The two invisible traps are the
**same-hue pair** (a teal glyph on an aqua tile) and the **dark-on-dark pair** (a coloured glyph on a
near-black tile). Use `icon_tile`, which guarantees it by construction — it reads the glyph's ink from
the PNG (or takes `glyph=<colour>`) and auto-nudges the tile to ≥3:1; a clean pairing is a **white/
near-white glyph on a deep tile**, or a **deep glyph on a pale tile** (never a mid glyph on a mid
tile of the same hue). · small (≤ title) · **consistent
size/position/treatment** across siblings · style matches the deck (outline vs filled) · **does a job**
(passes the rule-of-thumb — answers *what is this / what does it do / why pay attention*; else cut) ·
text always present · assets cached in the deck folder.

**Cache.** Fetched SVGs persist in the platform cache dir — macOS `~/Library/Caches/slide-maker/icons` · Linux `$XDG_CACHE_HOME`/`~/.cache/slide-maker/icons` · Windows `%LOCALAPPDATA%\slide-maker\icons` (override with `SLIDE_MAKER_CACHE`) — shared across Claude Code AND Codex, so an icon is fetched once ever and warm builds work offline. Delete a file there to force a refetch (a torn entry also self-heals on next read).
