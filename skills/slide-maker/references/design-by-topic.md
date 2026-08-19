# Design by TOPIC — pick a preset/register that fits the SUBJECT, not the reflex

`design-by-purpose.md` keys the look on **what kind of talk** it is (research meeting · status update ·
pitch · lecture). This file keys it on the other axis — **what the subject IS** (finance · engineering ·
medicine · luxury · gaming · crime · climate …). Both matter: purpose sets the *register's formality*,
domain sets the *register's family*. Read this when you are choosing the look ("design a clean one" or a
generated identity); it is the thing that makes a template **topic-adapted** rather than a reflex.

*(Ported from `slides-to-video/references/visual-styles.md`'s topic-domain contest, adapted to
slide-maker's 18 presets — `scripts/presets.py`. On the design-a-clean-one branch it feeds the direction
gate's preset slots; on a generated-template branch it feeds the style shortlist.)*

🔴 **This file governs the IMAGE-GEN branch too, not only presets.** When Q1 = "generate a template with
an image tool", run this same contest to shortlist the 3 generated styles (`generated-template.md`), and
— just as important — **the ANTI-PICK and the CLICHÉ GUARD apply to the generated HERO's art-direction**:
a domain map row's anti-pick names the *image cliché* to avoid (AI/ML → anti `synthwave`/`dark_tech`
**= no neon/HUD sci-fi hero**; climate → anti `terminal`/`dark_tech` **= no cold green-globe render**;
Chinese-culture → **not ink-wash-by-reflex on every topic**). The domain is chosen once; whether it is
realised as a preset, a bespoke register, or a generated plate, the register family and its anti-pick
are the same, and the pick is recorded as `design_plan.style_pick` on every branch. The image cliché is
owned in full by `references/image-generation.md` (CLICHÉ GUARD); this file supplies the per-domain
anti-pick it reasons from.

## How to use it — a ranked contest, not a lookup

1. **Read the subject's DOMAIN** off the approved content (its thesis, its objects, its audience) — not
   the umbrella word. "A company that makes AI cars" is *automotive/hardware + AI*, not "tech."
2. **Shortlist 2–3 apt presets** from the domain map, then **drop any that trip a VETO** (below).
3. **Score the survivors on four axes** — DOMAIN fit (cultural association) · CONTENT-SHAPE fit
   (data-dense wants a high-legibility spine; narrative wants an expressive register) · FORMALITY fit
   (exec/clinical → restrained; youth/creative → expressive) · TEMPERATURE fit (aspirational vs
   diagnostic vs somber vs playful). **Crown one, and name the nearest REJECTED rival + the one clause
   that separates them** — a contest, never a strawman.
4. **Record the pick** as the design plan's required **`style pick:`** line (slide-design §1;
   `checkpoint-convention.md`): `style pick: <preset|bespoke> for <domain> · beat <nearest rival> because
   <clause> · anti-pick avoided: <the cliché the domain tempts>`. On a locked look (provided/registered
   template or a Mode-A mimic) the look is not domain-picked — write `style pick: n/a — <locked: template
   / mimic / provided>`.

**The pick is an OFFER, not a cage.** A bespoke register invented for the subject (direction-gate rule)
routinely beats every preset here — the map raises the floor, the bespoke beats it. And a deliberate,
*named* deviation ("consulting for a fintech, but dark like the product") is design; an unexplained one is
the reflex this file exists to interrupt.

## Topic-domain → apt presets → ANTI-PICK

The ANTI-PICK is the register whose emotional temperature or legibility profile **collides** with the
subject — a hard veto above the four scoring axes. It always fails on ONE of two axes: **temperature**
(a playful/ironic register over a somber or authority-demanding subject) or **legibility** (a
low-contrast / high-texture spine under a data-dense deck).

| Topic domain | Apt presets | ANTI-PICK (why it fights the domain) |
|---|---|---|
| Finance / enterprise / consulting | `consulting` · `swiss` · `editorial_report` | `synthwave` / `memphis` — unserious, breaks trust |
| Engineering / hardware / architecture | `blueprint` · `bauhaus` · `swiss` | `luxury_dark` / `ink_wash` — ornament & softness fight schematic precision |
| Software / dev-tooling / infra | `terminal` · `swiss` · `dark_tech` | `synthwave` — retro-neon cliché; and DON'T reflex `dark_tech` for every "tech" deck |
| **AI / ML / technical research** | `editorial_report` · `blueprint` · `swiss` | 🔴 `dark_tech` / `synthwave` — the electric-blue-on-near-black **sci-fi cliché faking "futuristic"** over real method (the CLICHÉ GUARD; see below) |
| Medicine / biotech / clinical | `editorial_paper` · `blueprint` · `swiss` | `memphis` / `synthwave` — trivializes (somber veto) |
| History / museums / culture / heritage | `museum_memorial` · `editorial_paper` · `eastern_traditional` (CJK) | `glassmorphism` / `synthwave` — screen-glossy, anachronistic |
| Luxury / fashion / hospitality / spirits | `luxury_dark` · `editorial_paper` | `brutalist` / `terminal` — cold, cheap-looking, off-brand |
| Gaming / esports / entertainment / youth | `synthwave` · `memphis` | `swiss` / `consulting` — austere, kills the energy |
| Consumer app / lifestyle / wellness / D2C | `glassmorphism` · `editorial_paper` · `midcentury` | `brutalist` — harsh, off-brand |
| Startup pitch / product launch / hype | `glassmorphism` · bold `editorial_paper` · `memphis` | `blueprint` — reads like a lab report, not a launch |
| Climate / nature / sustainability / travel | `editorial_paper` · `risograph` · `midcentury` | `terminal` / `dark_tech` — cold, screen-bound, off-topic |
| Music / arts / indie / creative | `risograph` · `memphis` · `synthwave` | `blueprint` / `consulting` — clinical, kills expressiveness |
| Crime / security / investigative / defense | `luxury_dark` (noir) · `brutalist` | `memphis` / `midcentury` — playful, undercuts gravity |
| Kids education / general-public explainer | `risograph` · `memphis` · `midcentury` · `bauhaus` | `brutalist` / `terminal` — cold / scary |
| Geography / geopolitics / logistics / supply-chain | `swiss` · `blueprint` | `risograph` — grain/imprecision fights spatial data |
| Space / physics / deep-tech futures | `blueprint` (star-chart) · `editorial_report` | `synthwave` — glossy retro-future faking hard science (unless genuinely retro-future) |
| Data / analytics / observability | `terminal` · `swiss` · `editorial_report` | `synthwave` / `glassmorphism` — low-contrast under charts (data-density veto) |
| Legal / policy / government | `editorial_report` · `swiss` · `consulting` | `synthwave` / `memphis` — undermines authority |
| Chinese cultural / literary / heritage | `ink_wash` · `eastern_traditional` · `museum_memorial` | `dark_tech` / `glassmorphism` — screen-glossy, off the register 留白 wants |

## Guardrail VETOES (a style must never fight the content)

- **SOMBER / SENSITIVE** — death, disease, disaster, layoffs, war, safety-critical medicine forbid
  playful/ironic/retro registers (`memphis`, `synthwave`); default `editorial_*` / `swiss` / `blueprint`.
- **ENTERPRISE / TRUST** — finance, enterprise, legal, gov, healthcare-B2B forbid `synthwave`, loud
  `memphis`, `brutalist`-for-clients.
- **DATA-DENSITY** — a chart/benchmark deck forbids a busy/low-contrast SPINE (`synthwave` grids,
  heavy `risograph` grain, glass blur *under* a chart); such treatments live only as quiet backgrounds.
- **KIDS / PLAYFUL** — welcomes `risograph`, `memphis`, `midcentury`; forbids `brutalist` / `terminal`.
- 🔴 **CLICHÉ GUARD** — never reflex `dark_tech` / `synthwave` for "AI/tech", `terminal` for every dev
  deck, or `glassmorphism` for every SaaS. Reason from the SPECIFIC subject, not the umbrella domain.
  *(Measured on this skill's own Tesla deck: `dark_tech` "Signal" — dark canvas + electric cyan — was
  the reflex first pick for an EV/AI company; the user chose `editorial_report`, which is exactly this
  table's #1 for AI/ML. The cliché guard is here so the shortlist surfaces editorial FIRST.)*
- **3-SECOND-READ SUPREMACY** — if a style hurts legibility, the style YIELDS (atmosphere/background)
  and the content spine stays legible. `deckkit.contrast_ratio` floors are the automatic backstop.

## Per-preset — beats its rival · avoid the cliché

The compact discipline each preset needs at pick time (the `when` field lives in `scripts/presets.py`;
this adds the **rival** it beats and the **cliché** to avoid — the two things that make the pick
deliberate). Use it to write the `style pick:` line's `beat <rival> because …` clause.

| Preset | Beats its rival when… | Avoid the cliché |
|---|---|---|
| `swiss` | the deck is a systematic data-grid, not a quote-driven narrative (beats `editorial_paper`) | not a Helvetica poster of random rectangles — the grid must ORGANIZE real content; red is emphasis, not confetti |
| `editorial_paper` | the content is warm long-form narrative, not a data-grid (beats `swiss`) | no chunky serif over a beige gradient with a fake "MAGAZINE" kicker + smiling stock photo |
| `editorial_report` | it's a dark data/analysis readout with gravitas, not a light magazine (beats `editorial_paper`) | serif headlines need LINING figures for numbers — never let old-style digits bob (route numerals through a lining face; the `OLDSTYLE_FIGURES` lint backstops hand-set runs) |
| `consulting` | it's an exec/board decision deck needing MBB restraint (beats `swiss` when warmth+structure both matter) | not a wall of identical blue bullet cards — one hero per slide, action titles |
| `blueprint` | the subject IS engineering/method and precision reads as trust (beats `dark_tech`) | the grid must be schematic, not decorative graph-paper wallpaper; don't fake dimension callouts |
| `dark_tech` | genuinely an infra/AI product whose own UI is dark — and only when NOT the AI cliché | 🔴 the electric-blue-on-#0d1117 slop — reason from the specific system, not "it's AI" |
| `terminal` | it's CLI/code/observability where mono IS the subject (beats `swiss` for dev density) | fake readable code in images; keep code real HTML, mono for data only |
| `glassmorphism` | it's a premium launch/product surface where depth sells (beats `editorial_paper`) | full-screen rainbow mesh; frosted cards must sit over TOPICAL imagery, not generic orbs |
| `synthwave` | genuinely retro-future / gaming / music culture (beats `memphis` for neon energy) | not "AI/tech = neon grid"; a hard cliché-guard target |
| `memphis` | an event/launch/culture deck that rewards playful energy (beats `risograph`) | no emoji-in-titles; shapes must organize, not confetti |
| `risograph` | indie/craft/culture/kids where print texture is the voice (beats `memphis`) | grain must not sit under a chart (data-density veto) |
| `brutalist` | a manifesto / data-journalism-with-attitude (beats `swiss` for a bold statement) | raw ≠ broken; still one hero, still legible |
| `bauhaus` | modernist/geometric design/education (beats `swiss` for warmth + primary blocks) | primary shapes must encode, not decorate |
| `midcentury` | a warm retro/lifestyle/optimistic register (beats `editorial_paper` for warmth) | not a Mad-Men pastiche; the warmth serves the content |
| `luxury_dark` | fashion/luxury/premium OR a noir crime/investigation register (beats `editorial_report` for tone) | dark ≠ low-contrast; mute the HUE, keep the VALUE distance (`design-principles.md` "Muted register ≠ low contrast") |
| `museum_memorial` | history/heritage/memorial/exhibition where gravity is the register (beats `editorial_paper`) | reverent, not funereal; let the artifact lead |
| `ink_wash` | a Chinese cultural/literary/humanities deck (beats `eastern_traditional` for 留白 restraint) | 留白 is the design — don't fill it; one seal is the accent |
| `eastern_traditional` | traditional-culture/heritage where 传统色 + material matter (beats `ink_wash` for colour/material) | 传统色 must be sourced, not a red-and-gold pastiche |

## The registry link

When the subject has a visual world of its own, a **bespoke register** invented for it beats every preset
above — and a good one is worth keeping. See `references/bespoke-registers.md`: a growing, open-ended
library of verified bespoke registers to ADAPT (never transplant), plus the process for registering a new
one when a deck's invented register works. The domain map is the floor; the bespoke library is where the
ceiling gets recorded.
