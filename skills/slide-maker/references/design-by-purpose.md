# Design by purpose — give "design a clean one" a purpose-fit look

`deckkit`'s default palette is a safe neutral blue. Safe is not the same as *right*:
a thesis defense, a startup-style exec readout, and an undergrad lecture should not
look identical. When the user picked **"design a clean one"** (no template) — or when
you're free to set the look — tailor the visual system to the **purpose + audience**
chosen in step 0. The goal isn't decoration; it's that the deck *reads as the right
kind of document* the moment it's on screen, which earns trust before a word is said.

## Shortcut: design-language presets
For a strong, coherent *look* in one switch, `scripts/presets.py` has named design languages —
`preset("glassmorphism" | "swiss" | "editorial_paper" | "editorial_report" | "risograph" |
"memphis")` returns a matched palette + fonts + surface treatment + image-prompt style (and a
`when` note). Adopt one as the starting language, then **tune it to the purpose + brand below**
(the preset is not a straitjacket; the user's brand/reference always wins). E.g. a data report →
`editorial_report` + the `data-viz.md` charts; a launch/portfolio → `glassmorphism` or
`editorial_paper`; an event → `memphis`/`risograph`. These pair with the generated-template Style
library (`references/generated-template.md`).

## Reach for the new modules — by purpose (every purpose benefits, not just design-forward ones)
The recently-added kit — designed charts (`data-viz.md`), KPI/stat furniture, layout patterns,
publication chrome, surface effects, `presets.py` — serves **all** purposes; match it like this.
None are mandatory: pick what the *content* needs, and keep it **restrained for sober purposes**.

| Purpose | Preset to start | Modules that fit |
|---|---|---|
| Research meeting · thesis defense | `swiss` (minimal, one-accent) | designed charts with **single-highlight** + `takeaway_rail` for results; `big_numeral` for numbered contributions; `sources_page` for refs; `accent_one` restraint |
| Work status · stakeholder / investor readout | `editorial_report` | `scorecard` KPI tiles (value + ▲/▼ delta) & `stat_row` hero numbers; `leaderboard`; designed charts (the one comparison that matters); `timeline` roadmap; section dividers |
| Conference talk · job talk · webinar | projection/screen-grade (no heavy preset) | designed **plots** over tables; `timeline`/`hub_spoke` for way-finding & the program map; `big_numeral` section nav; `cover`/dividers |
| Product / pitch · launch | `glassmorphism` or `editorial_paper` | `scorecard`/`stat_row` hero metrics; `before_after`; photo kit (`photo_triptych`/`image_tab`); `cover` ↔ `colophon` bookend; bold CTA |
| Teaching / lecture | warm, light scheme | `quadrant`/`hub_spoke`/`timeline` concept diagrams; `before_after`; `accent_one` to encode one idea |
| Event · culture · marketing | `memphis` / `risograph` | `offset_shadow` stickers, bold motifs, designed plots |
| Editorial / brand / portfolio / report | `editorial_paper` / `editorial_report` | `editorial_header`, `big_numeral`, `photo_triptych`, `cover`/`colophon`, `sources_page` |
| **Read-alone** leave-behind / reference / pre-read *(no speaker)* | match the host purpose's look | **fuller, self-contained text** (NOT few-words), `sources_page` + appendix, `table` for dense reference, scannable headings/titles; judge by **completeness**, not slide count |
| **Fixed surface** — poster / single-slide infographic | `swiss`/`editorial` (or bold for an event) | one canvas → **multi-region hierarchy** (`columns`/`rows`/`quadrant`), larger headline, designed plots; build at the real size with `blank_deck(w_in, h_in)`. *Icons:* at most small region-header marks to guide the reading path + diagram-entity marks, never competing with the focal result, always text-labelled (no speaker) |

**Delivery mode flexes density** (`design-principles.md` "Delivery mode"): a **read-alone /
reference / poster** deck is read without a speaker, so it legitimately carries **more text per
surface** than a spoken deck — don't thin it to talk-density.
**Surface effects gate by medium, not purpose:** `glass_card`/`glow`/`scrim_overlay` need a
dark/photographic base (product/tech/launch) — skip them on a light research, readout, or webinar
deck. And the universal craft holds for every purpose: charts single-highlight + a takeaway, role-based fonts,
consistent corners/colours, no orphaned punctuation, no large blank.

## How to use this file
1. Find the purpose below and adopt its **design language** as your starting point —
   set the `deckkit` palette constants (`DEEP/BLUE/ACCENTS/...`) and a **role-based font
   pairing** (a `DISPLAY` title face + `FONT` body + `MONO`; for a CJK deck also `EADISPLAY`
   + `EAFONT`) to match — don't ship the whole deck in one font (see `font-guidance.md`
   "Type pairing") — and apply its layout/chrome guidance in steps 3–4.
2. **Then ground it in current inspiration.** Tastes and conventions shift, and a
   stock blue deck looks dated. Do a quick search/fetch with the host's available web tools (e.g. "modern
   conference talk slide design 2026", "clean investor readout deck examples",
   "minimal academic defense slides") and look at 3–5 real, well-regarded examples
   for *this* purpose. Pull concrete ideas — a colour pairing, a title treatment, a
   way of laying out a results figure — and adapt them. Cite back to the user what
   you drew from so the choice is legible, not arbitrary.
3. Keep the craft rules from `design-principles.md` regardless — purpose changes the
   *style*, not the discipline (one idea per slide, figures whole, contrast ≥ 4.5:1).

Adopt these as **tasteful defaults, not rules** — if the user states a brand colour,
tone, or preference, that always wins. And **vary within them**: each entry is a *mood*,
not a fixed palette — pick a distinct, concrete look each time (warm/cool, light/dark,
serif/sans, restrained/vivid) rather than shipping one identical house style across decks.
Don't reuse the previous deck's scheme out of habit.

> **Name the bias, then beat it.** Before settling a look, name the default pull (the safe,
> light/minimal/blue-ish reflex) and deliberately consider the **temperature span** — a *bold*
> direction (saturated, high-contrast, expressive type), a *neutral* one, and a *quiet* one — then
> choose what the purpose actually wants, not the reflex middle. **Anchor the choice to a concrete,
> named exemplar** — a *kind* of look (a clean product-doc look, an editorial-newspaper look, a
> Swiss-poster look) or a specific brand/reference — rather than vague adjectives, so "distinct" is
> real and checkable. (The web-search step in the build is where you ground it.)

**Non-Latin decks:** the font names below are Latin. For Chinese/Japanese/Korean, pick
the script-appropriate equivalent and set `deckkit.EAFONT` — sans (modern/corporate/
talks) → Heiti SC / PingFang SC / Noto Sans CJK; serif (formal/defense) → Songti SC /
Noto Serif CJK; brush → Kaiti SC. See `references/multilingual.md`.

---

## Research meeting with a supervisor / lab group
Working session, expert audience, frequent. Optimize for *fast technical read*, not
polish. Calm, low-chrome, content-forward.
- **Palette:** restrained — one cool primary (slate/navy or deep teal), grey body,
  a single saturated accent reserved for "look here / the new result". Avoid busy
  multi-colour.
- **Density:** moderate is fine here — this audience tolerates a labelled plot and a
  short equation. Show the *actual* figures/tables from your work, annotated.
- **Layout/chrome:** minimal footer, small section kicker, generous whitespace. No
  title slide theatrics. Date/iteration tag helps (it's a progress checkpoint).
- **Icons:** **minimal & structural** (low-chrome working deck) — a repeated-entity mark inside the
  recurring diagram or a category mark; keep them off the result slides; a status chip often beats a
  status icon. A style-matched family still fits — just sparing (see `icons.md` Scenario fit).
- **Signature:** "what changed since last time" framing; open questions slide.

## Work status update to a manager / team
Decision- and outcome-oriented; the reader is busy. Lead with results, make status
scannable.
- **Palette:** clean corporate neutral — a confident single brand-ish hue + grey,
  plus a small green/amber/red status vocabulary used *consistently* (on-track / at
  risk / blocked).
- **Density:** low. One headline per slide stating the outcome; supporting detail
  small. Tables/timelines over prose.
- **Layout/chrome:** consistent header with the status, tidy footer with date/owner.
  Use chips/badges for status. Predictable grid > clever layout.
- **Signature:** a takeaway line per slide phrased as the *decision or ask*.

## Academic conference talk
A *spoken* talk to a room, often dim. Big, legible, one message per slide; built to
be followed at the back of the hall. **Venue conventions dominate** — if step 0 found
an official template or venue norms, those override this section.
- **Palette:** higher contrast for projection; a strong dark or strong light base
  (not mid-grey), one vivid accent. Avoid thin light-grey text — it disappears on a
  projector.
- **Density:** minimal / diagram-heavy. Few words; the figure or diagram carries it.
  Every results figure gets a legend + a one-line takeaway.
- **Layout/chrome:** large type (titles ~28pt+, body ~18pt+), big figures, lots of
  air. Respect the venue's aspect ratio (16:9 vs 4:3) and any title-slide format.
- **Icons:** **minimal & structural** — diagram-entity shorthand or one consistent wayfinding mark on a
  long arc (skip it if numeral wayfinding already does the job); never on a results/figure slide. A
  style-matched, sparing family is fine — not off by rule.
- **Signature:** a clear arc (problem → method → result → so-what); a memorable
  closing message slide named "Conclusion".

## Academic job talk / faculty interview
A *spoken* talk to a whole department — like a conference talk in legibility, but
longer, more personal, and selling a research *program*, not one paper. It must read
as "a confident future colleague," authoritative yet warm, and accessible at the back
of a room holding people far from your subfield.
- **Palette:** projection-grade contrast like a conference talk — a strong base + one
  vivid accent — but a touch warmer and more personal than a sterile corporate scheme.
  One consistent **program colour** running through the arc (the through-line you keep
  returning to) is a powerful structural signal. Institution colours are *not* expected
  (you're not theirs yet); a clean personal scheme reads more confident.
- **Density:** minimal/diagram-heavy on the deep-result slides (figures carry it,
  big legible annotated results), but plan for a few **map slides** that show the whole
  program at a glance — a research-agenda overview and a future-directions roadmap — which
  carry a little more structure than a single conference take-home.
- **Layout/chrome:** large type and big figures (conference-grade). Add light **way-finding**
  so a broad audience never gets lost across a 45-min arc — a recurring agenda spine,
  section dividers that re-show the through-line, a "you are here" on the program map.
  A personal title slide (name, the program's one-line thesis, current affiliation). Keep
  backup slides for Q&A.
- **Icons:** restrained — concentrate a wayfinding mark on the agenda spine / dividers and per-theme
  colour-coded marks on the program-map; **none** on the deep-result slides (the figure carries those).
- **Signature:** open by establishing *who you are as a scholar* and the program's unifying
  thesis; descend into 2-3 deep results; **close on a concrete future-program roadmap** (named
  5-7-year projects) and return to the opening big picture — never end on "Thanks".

## Company / stakeholder / investor readout
Persuasive and credible to a mixed, partly non-technical audience. Polished, on-brand,
confident.
- **Palette:** brand-led if a brand exists; else a modern, slightly bolder scheme
  (deep base + one energetic accent). Cohesive, not playful.
- **Density:** low; narrative-driven. Big numbers as hero stats. Charts simplified to
  the single comparison that matters.
- **Layout/chrome:** strong title slide and section dividers, consistent premium
  spacing, hero-number layouts, clean icons used sparingly.
- **Signature:** a clear story spine and an explicit ask/next-steps close.

## Product description / pitch
Selling a product to prospects/customers/users. The most *designed* deck of the set —
it represents the product, so polish and brand are part of the message. Confident,
modern, visual; the product itself is the hero.
- **Palette:** brand-led above all (use the product's real colours/logo if it has
  them). If none, pick a bold, contemporary scheme — a strong primary + one
  energetic accent for CTAs/highlights — and commit to it consistently. Can be the
  most vivid of any purpose, but stay legible (contrast ≥ 4.5:1).
- **Density:** low and punchy. One value statement per slide; hero numbers and short
  benefit lines over paragraphs. Let visuals breathe.
- **Layout/chrome:** strong title/cover and section dividers; **hero product
  visuals** (screenshots, product photos, a demo frame shown large and clean); benefit
  blocks with sparing icons; consistent premium spacing. Map the arc to the pitch:
  hook/problem → what it is → key benefits → how it works → proof (metrics /
  testimonials / logos) → call to action.
- **Signature:** a crisp one-line positioning ("X for Y who want Z"); benefits phrased
  as outcomes for the user; a bold, specific **CTA slide** to close (try / buy / sign
  up / contact) — never end on a flat "Thanks".
- **Real assets first:** the **real logo / product render / UI screenshot** is the credibility
  anchor — show it, never a generated look-alike or a generic box. If a needed brand/product asset is
  missing, **ask for it** rather than fake it (recognizability hierarchy in `image-generation.md`).
  Same for any competitor/customer logos: real or omit — **never** a recolored monochrome `simple:`
  glyph on a proof/partner slide (the icon mechanism recolors it to the deck accent → a wrong-colour
  look-alike); `simple:` is for naming a tool inline, not for a credibility logo (`icons.md`).

## Thesis defense
Formal, rigorous, complete; an expert committee that will probe. Serious and
authoritative, but still legible as a talk.
- **Palette:** sober and classic — deep navy/charcoal/maroon base, restrained accent,
  excellent contrast. Nothing trendy or playful.
- **Density:** moderate; completeness matters more than minimalism, but never a wall
  of text. Plan for backup/appendix slides for Q&A.
- **Layout/chrome:** clear numbered structure, consistent section dividers, visible
  contribution framing. Institution colours if the user has them.
- **Icons:** **minimal & structural** — a clean wayfinding/section mark or a neutral entity mark in a
  diagram node is fine; keep DECORATIVE icons off contributions/method/results (an expert reads a *cute*
  icon there as padding — a credibility hit). Carry the core structure with numbered contributions
  (`big_numeral`) + typographic hierarchy; restrained matched icons, not zero by rule.
- **Signature:** contributions slide stated plainly; limitations + future work owned
  honestly; an appendix of defensible detail.

## Teaching / lecture
Goal is *understanding and retention*, mixed/novice audience. Friendly, clear,
progressive; a little warmth is welcome.
- **Palette:** approachable — a warmer or brighter (still legible, high-contrast)
  scheme; colour can encode concepts consistently (e.g. each concept a colour).
- **Density:** low per slide, but build ideas step by step; worked examples and simple
  diagrams beat dense definitions.
- **Layout/chrome:** clear learning-objective framing, consistent "concept → example →
  check" rhythm, generous figures, summary/recap slide.
- **Icons:** a strong fit here — reuse one mark per section / concept-stage (concept → example →
  check) and give each distinct concept its own colour-coded category icon; but never an icon on every
  bullet, and **split** a long list across slides rather than carding it (`icons.md` jobs 1–3 + the ≤5
  short-list guard).
- **Signature:** an objectives slide up front and a recap at the end; questions to the
  audience built in.

## Webinar / online presentation
A talk delivered over video (Zoom/Teams/streamed), watched on screens of varying size,
often with the speaker in a small inset and attention competing with the viewer's other
tabs. Like a conference talk but built for a *shared-screen* medium, not a projector.
- **Palette:** high-contrast and screen-grade; favour a **light** background (renders
  more reliably across compression/streaming than large dark fills, and is kinder if a
  viewer screenshots). One clear accent.
- **Density:** low; **larger** type than a conference deck (content is shrunk inside a
  video window and may be watched on a laptop or phone) — assume the slide occupies far
  less of the viewer's screen than a hall projector.
- **Layout/chrome:** keep key content in the central "safe area" (edges can be cropped by
  meeting UI/inset cameras); avoid bottom-edge content where a control bar or captions
  sit. Simple, frequent slide changes hold attention better than one dense slide.
- **Icons:** if used, favour a slightly **heavier** weight + a `disc=` tile so they read when the
  slide is shrunk in a video window, and keep them inside the central safe area (not near cropped
  edges/bottom); a wayfinding/agenda mark helps late joiners — per-card decoration competes for pixels.
- **Signature:** more, lighter slides to keep momentum; build/animate where step-by-step
  pacing genuinely helps a remote audience you can't read (by design sense, not a quota — see
  `references/animation.md`); explicit "ask in the chat" prompts; a visible agenda so late
  joiners orient. If it's recorded, ensure every slide reads as a still frame.
