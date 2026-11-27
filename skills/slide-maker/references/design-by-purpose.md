# Design by purpose — give "design a clean one" a purpose-fit look

`deckkit`'s default palette is a safe neutral blue. Safe is not the same as *right*:
a thesis defense, a startup-style exec readout, and an undergrad lecture should not
look identical. When the user picked **"design a clean one"** (no template) — or when
you're free to set the look — tailor the visual system to the **purpose + audience**
chosen in step 0. The goal isn't decoration; it's that the deck *reads as the right
kind of document* the moment it's on screen, which earns trust before a word is said.

## Table of contents
- Shortcut: design-language presets
- Reach for the new modules — by purpose (every purpose benefits, not just design-forward ones)
- How to use this file
- Research meeting with a supervisor / lab group
- Work status update to a manager / team
- Academic conference talk
- Academic job talk / faculty interview
- Company / stakeholder / investor readout
- Product description / pitch
- Thesis defense
- Teaching / lecture
- Webinar / online presentation
- Preset fit by purpose — a fast sanity map (fit is a default, avoid is a flag, both overridable with a stated reason)

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

**Typed modules for reference surfaces** (read-alone leave-behind / cheat-sheet / fixed-surface
one-pager — **NEVER** a presented-live slide): compose the multi-region hierarchy from *named*
module types, each carrying **specific data points, not generic descriptions** — SUCH AS a **selection
array** (4–8 items, best choice highlighted) · a **spec scale** (3–5 levels with exact increments) ·
a **scenario comparison** (3–6 scenarios, one recommendation each) · a **pitfalls zone** (3–5
pitfalls WITH consequences + 1–2 correct moves, high visual contrast) · a **quick-reference
table / decision flow**. The list is open — extend per domain: a formula block, a parameter/constant
table, protocol steps, a decision flow, an error zone. Dense is correct on these surfaces — but
typed and organized, never freeform cramming.

**Delivery mode flexes density** (`design-principles.md` "Delivery mode"): a **read-alone /
reference / poster** deck is read without a speaker, so it legitimately carries **more text per
surface** than a spoken deck — don't thin it to talk-density.
**Surface effects gate by medium, not purpose:** `glass_card`/`glow`/`scrim_overlay` need a
dark/photographic base (product/tech/launch) — skip them on a light research, readout, or webinar
deck. And the universal craft holds for every purpose: charts single-highlight + a takeaway, role-based fonts,
consistent corners/colours, no orphaned punctuation, no large blank.

## How to use this file
1. Find the purpose below and adopt its **design language** as your starting point —
   set the palette with **`deckkit.set_palette(deep=…, blue=…, magenta=…, accents=[…], mono=…)`**
   (one call after import; it also re-themes the components' built-in colour defaults, which a bare
   `deckkit.DEEP = …` reassignment does NOT) and a **role-based font pairing** (a `DISPLAY` title
   face + `FONT` body + `MONO`; for a CJK deck also `EADISPLAY` + `EAFONT`) to match — don't ship
   the whole deck in one font (see `font-guidance.md` "Type pairing") — and apply its layout/chrome
   guidance in steps 3–4.
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
>
> **The mood dial, quantified:** *subtle / balanced / bold* are a TRANSFORM over the chosen preset,
> not a new preset — so "make it punchier/calmer" is a parameter change, not a redesign. **subtle** =
> desaturate the accents ~20–30%, keep only 1–2 saturated hues in play, hairline rules/strokes, low
> `tint()` fractions; **balanced** = the preset as shipped; **bold** = +20–30% saturation/contrast on
> the accents, 3–4 hues, heavier rules/stroke weights, stronger tints. The dial's stroke moves land
> on *content* elements (diagram edges, chart emphasis) — chrome weight stays per the chrome budget
> at every setting, and subtle's "hairline rules" likewise refers to content strokes. The floors
> still bind at every
> setting: contrast ≥ 4.5:1, the legibility floors for the venue, statement/full-bleed hero
> skeletons don't take bold chrome, and the transform never reassigns the semantic colour
> contract's hue assignments — identity is preserved, only intensity moves. **The preset's `guard`
> binds at every dial setting** — bold on a one-accent register raises weight, scale, rule
> thickness on CONTENT elements and tint of the ONE accent, never the hue count; on a named-palette
> register (传统色) bold never re-saturates the named hues. And on a §0 **LOCKED** look
> (`agents/slide-design.md`) the dial moves only the unlocked dials — imagery strength, stroke/rule
> weights, density, tint fractions within the locked palette; a saturation transform of a locked
> palette is a re-litigation and goes back to the user.

**Type by register (the academic default).** For a **lab meeting, group progress update,
conference talk, job talk or thesis defense**, the expected face is a conference face — **Times New
Roman** (serif, and the right answer whenever the deck carries equations, because prose and math
then share one face), or **Calibri / Arial** for a sans register — with **Courier New** for mono. A
characterful designer sans reads as marketing in that room. 🔴 And check that the face is installed
SYSTEM-WIDE, not just inside an app bundle: Office's Calibri/Cambria on macOS are invisible to the
render loop and to the width measurement, so a deck set in them is laid out and "verified" against
a substitute (`font-guidance.md` → the app-bundle section). Override with a stated clause.

**Non-Latin decks:** the font names below are Latin. For Chinese/Japanese/Korean, pick
the script-appropriate equivalent and set `deckkit.EAFONT` — sans (modern/corporate/
talks) → Hiragino Sans GB / PingFang SC / Heiti SC (macOS) / Noto Sans CJK; serif
(formal/defense) → Songti SC /
Noto Serif CJK; brush → Kaiti SC. See `references/multilingual.md`.

---

## Research meeting with a supervisor / lab group
Working session, expert audience, frequent. Optimize for *fast technical read*, not
polish. Calm, low-chrome, content-forward.
- **Type:** the academic default — Times New Roman (or Calibri/Arial for a sans register),
  Courier New for mono; equations in the SAME face as the body. See the Type-by-register note
  above; a designer sans is the wrong signal in this room.
- 🔴 **Structure — when the update reports a CHANGE OF APPROACH, three things move.** Use the
  `method-pivot` arc (`content-planner.md` §3). (a) **The prior work's RESULTS go BEFORE the
  pivot**, grouped, in the order the steps produced them — a room asked to accept a direction
  change before seeing what the old direction showed has no basis to accept it. (b) **Every step
  of the retired method carries WHAT IT WAS FOR**, not only what it did; the purposes are what the
  pivot later contradicts, and a recap without them is a list rather than an argument. (c) **The
  deck ENDS ON STATUS** — what is established and what is not — because the new method's slide is
  not evidence, and a deck that stops there implies a result it does not have. Each of these three
  was a correction on a real delivered deck, twice by the user.
- 🔴 **Every step you enumerate owes a result, or an explicit "no result yet".** If the method
  recap numbers four steps and the deck shows outcomes for three, the room notices the gap — and a
  later slide that rests on the missing one (a measurement, a benchmark) is arguing from something
  it never showed. Say the outcome inline where it is used, or mark the step as not-yet-reported.
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
- 🔴 **Declares (checked): what changed · open questions.** Both come from the Signature line
  above; a working session with neither is a report, and nobody called a meeting for a report.
- 🔴 **Fidelity:** this is the one audience where rounding a shaky number up costs you directly —
  they will build advice on it.

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
- 🔴 **Declares (checked): outcome · the ask.**
- 🔴 **Fidelity:** a status update with no ask is a report the reader did not need. If nothing is
  wanted from them, say so explicitly rather than leaving them to guess.

## Academic conference talk
A *spoken* talk to a room, often dim. Big, legible, one message per slide; built to
be followed at the back of the hall. **Venue conventions dominate** — if step 0 found
an official template or venue norms, those override this section.
- **Type:** the academic default — Times New Roman, or the venue template's own face when step 0
  found one (venue conventions dominate here). Size for the back of the hall before anything else.
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
- 🔴 **Declares (checked): contribution · evidence · limitations.**
- 🔴 **Fidelity:** the room cannot check you while you are in it, which is exactly why the
  limitation slide matters. State the regime where the method does NOT hold.

## Academic job talk / faculty interview
A *spoken* talk to a whole department — like a conference talk in legibility, but
longer, more personal, and selling a research *program*, not one paper. It must read
as "a confident future colleague," authoritative yet warm, and accessible at the back
of a room holding people far from your subfield.
- **Type:** the academic default — Times New Roman for an equation-heavy talk, Calibri/Arial for a
  slide-native one. Consistency across every slide matters more than the choice.
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
- 🔴 **Declares (checked): track record · research plan · fit.**
- 🔴 **Fidelity:** the plan is judged on feasibility, not ambition. A five-year programme with
  no named first project reads as a wish — say what starts in month one.

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
- 🔴 **Declares (checked): the ask · the number · the risk.**
- 🔴 **Fidelity:** a readout that names no downside reads as a sales pitch, and the first
  question will be the one you left out. Name the assumption the number rests on.

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
- 🔴 **Declares (checked): positioning · benefits.** Both from the Signature line above.
- 🔴 **Fidelity:** a benefit is a CLAIM. Every number on a pitch slide is one a customer may hold
  you to; an unverifiable one is not persuasion, it is an unpaid debt.

## Thesis defense
Formal, rigorous, complete; an expert committee that will probe. Serious and
authoritative, but still legible as a talk.
- **Type:** the academic default — Times New Roman throughout, equations included, so the formulas
  read as part of the argument rather than pasted into it.
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
- 🔴 **Declares (checked): contributions · limitations · future work.**
- 🔴 **Fidelity:** own the limitations before the committee finds them. One you raised is
  evidence of judgement; the same one raised from the floor is a gap.

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
- 🔴 **Declares (checked): objectives · worked example · recap.** All three are already in the
  Layout and Signature lines above — this only makes them checkable.
- 🔴 **Fidelity:** a novice cannot tell a simplification from a claim. Say when you are
  simplifying, or the simplification is what they carry away as fact.

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
- 🔴 **NO section list, and the reason is not 'too unconventional'.** A webinar is a delivery
  MODE, not a genre: the same session can be a lecture, a product pitch or an exec readout, and
  those need different content — so a list attached to "webinar" would be a guess about which,
  firing on two decks in three. What it genuinely constrains is the MEDIUM, and that already
  lives in the lint's type floors and `formats.py`'s safe zones. Record the GENRE as the
  purpose ("a teaching webinar", "an investor webinar") — `check_purpose` recognises the
  medium words and asks you for the genre rather than silently checking nothing.

## Grant proposal / funding pitch
ERC · NWO · NIH · Horizon. The highest-stakes deck an academic makes, and the one with the most
rigid conventions — reviewers score against *named* criteria, so a missing section is a lost point
rather than a stylistic choice. Not a product pitch: the register is sober, and enthusiasm reads as
a substitute for evidence.
- **Type:** the academic default; equations only where the method genuinely turns on one.
- **Palette:** institutional or sober; nothing that looks like a startup deck.
- **Density:** high but structured — a reviewer is reading against a checklist, not being toured.
- **Layout/chrome:** the scored sections visible as sections. Numbered aims.
- **Signature:** the aims page is the deck. One sentence per aim, each falsifiable.
- 🔴 **Declares (checked): aims · feasibility · risk.** Feasibility means *why this team, why now* —
  pilot data, track record, access. Risk means named risks with named mitigations; "no significant
  risks" is read as not having thought about it.
- 🔴 **Fidelity:** preliminary data is the section most often overstated. A pilot is a pilot — say n,
  say it is preliminary. A reviewer who catches one inflated claim discounts the rest.

## Progress / guidance committee meeting
A PhD guidance committee, a thesis advisory board, a stage-gate review. It differs from a lab
meeting in exactly one way, and it is the way that matters: **the room has to decide something** —
is this on track, does the thesis hold together, what should be scoped down. A committee deck with
no ask has silently become a status update, and the meeting's most valuable output is lost.
- **Type/palette:** the lab or institution's own template, unchanged. Nobody is being impressed.
- **Density:** moderate-to-high; the deck is also the record of the year, read as well as presented.
- **Layout/chrome:** status legible at a glance — what is done, what is out for review, what is
  still on your desk. Bind one hue to each state and keep it deck-wide.
- **Signature:** the closing slide names the decisions you want them to weigh in on.
- 🔴 **Declares (checked): progress · plan · ask.**
- 🔴 **Fidelity:** what is not done must READ as not done. A committee exists to advise on open
  work, and a hypothesis promoted to a result removes the thing they are there to help with
  (`content.open_ledger` is the artifact).

## Journal club / presenting someone else's paper
You are presenting work you did not do. Extremely common, and it carries a fidelity risk the
universal never-invent rule does not reach: not fabrication but **misattribution** — stating their
result more strongly than they did, or blurring their claims with your critique until the audience
cannot tell which is which.
- **Type/palette:** reuse the paper's own figures; let its visual language show through.
- **Density:** moderate — the method matters, but the room has (in principle) read it.
- **Layout/chrome:** a visible separation between *their claim* and *your reading*. A rail, a
  colour, a consistent slot — anything, as long as it is the same on every slide.
- **Signature:** your assessment, owned as yours.
- 🔴 **Declares (checked): attribution · critique.**
- 🔴 **Fidelity:** attribute on the slide that carries the result, not only on the title slide. An
  audience that cannot tell which is which will remember your critique as the paper's conclusion.

## Clinical case presentation / tumour board / M&M
A fixed clinical narrative. The structure is not a style choice: colleagues are being asked to judge
a decision, and they cannot do that without the information that was available when it was made.
- **Type/palette:** the institution's template; sober. Never playful — somber veto.
- **Density:** high on the facts, minimal on chrome. Imaging large.
- **Layout/chrome:** one section per stage, in order; imaging shown at a size a clinician can read.
- **Signature:** the learning point, stated plainly.
- 🔴 **Declares (checked): presentation · investigations · management · outcome.**
- 🔴 **Fidelity — DE-IDENTIFICATION IS LOAD-BEARING.** This is the genre PRE-FLIGHT 5's burned-in
  identifier check exists for: name, MRN, accession, date of birth, study date, institution, read on
  all four edges and in every overlay strip. Get a de-identified export — never crop or blur and
  ship. Unlike everything else on this page, it is irreversible once the deck is sent.

> 🔴 **These four are CHECKED, not just described.** `scripts/purposes.py` declares the sections each
> genre is not finished without and `scripts/check_purpose.py` looks for them in the built deck, on
> both gate paths — the same mechanism `formats.py`/`check_surface.py` already applies to surfaces.
> The check asks whether the deck NAMES the section, not whether it does it well; judging the latter
> is the critic's job. Terms are multilingual; extend them with `design_plan.purpose_section_terms`
> rather than waiving, and waive in writing when a deck genuinely has none.
>
> **SEVENTEEN of the eighteen entries on this page are now checked.** The eighteenth, **webinar**, has no
> section list on purpose: it is a delivery MODE, not a genre, and `check_purpose` says so rather
> than checking nothing (see its entry above).
>
> 🔴 **Every section list here was DERIVED FROM THIS PAGE'S OWN PROSE, not invented.** Teaching's
> objectives/example/recap were already in its Layout and Signature lines; the lab meeting's "what
> changed" and "open questions" and the pitch's "positioning" and "benefits" are its Signature line
> verbatim. That is the whole move — the conventions were already written down and simply could not
> be checked. Where a genre's prose does NOT name a required section, none was added: inventing one
> would fire on good decks, and a check that fires on good decks is how people learn to ignore
> checks.

## The everyday genres — their playbooks live in `purposes.py`
Five genres that make up most of the decks people build outside a lab, each with a full playbook — arc,
content rules, design conventions, failure modes, sources — printed by `python3 scripts/purposes.py --brief
"<their words>"` (and on `deck_gates.py picks --set purpose=…`). The design conventions there sit INSIDE the
direction you pick; they never replace the preset, the visual language, the signature move or the icons.
- **student presentation** (课堂汇报 · group project) — sections: introduction · conclusion · references. Graded
  on a rubric: one central message, sourced evidence, a structure the room can follow, the time limit.
- **client proposal** (bid · RFP · 投标) — sections: their goals · scope · timeline · investment. Scope names
  what is OUT; price comes as options.
- **investor pitch** (pitch deck · 融资路演) — sections: problem · market · business model · team · the ask.
  About ten slides, legible from the back, a dated metric behind every traction claim.
- **training** (onboarding · e-learning · 培训) — sections: objectives · practice · knowledge check · recap.
  Modules end in a check (`deckkit.check_question`); self-paced decks stand alone.
- **all hands** (town hall · keynote · 年会) — sections: agenda · updates · recognition · q&a. Picture-led,
  one engineered moment, honest about the hard news.
The upgraded genres gained sections the same way: **teaching** adds *check for understanding* (a
`check_question` / `prompt_card`, not "Questions?"), **work status** adds *risks*, **product pitch** adds
*proof* and *next step*.

## Preset fit by purpose — a fast sanity map (fit is a default, avoid is a flag, both overridable with a stated reason)
| Purpose | Natural fits | Flag before using |
|---|---|---|
| Thesis defense · committee | `swiss` · `editorial_paper` · clean custom | `memphis` · `risograph` · `luxury_dark` (playful/fashion registers read unserious to a committee) |
| Exec / board readout | `consulting` · `editorial_report` (dark data) · `swiss` | `risograph` · `blueprint` (zine/schematic registers undercut authority) |
| Conference talk | `swiss` · `editorial_paper` · `dark_tech` (AI/systems) | heavy `glassmorphism` (projector contrast risk) |
| Product pitch / launch | `glassmorphism` · `dark_tech` · `memphis` (consumer/playful) | `brutalist` · `museum_memorial` |
| Teaching / lecture | `editorial_paper` · `swiss` · warm custom | `luxury_dark` · `consulting` (cold for a classroom) |
| Teaching — K-12 | visual languages `cutpaper` · `bricks` · `chalkboard` · preset `memphis` | `consulting` · `luxury_dark` · `terminal` (adult registers lose a young room) |
| Work status update | `editorial_report` · `swiss` · `consulting` | `synthwave` · `memphis` (a status board must read neutral) |
| Student class presentation | `swiss` · `editorial_paper` · `bauhaus` / `memphis` (creative courses) | `luxury_dark` (projector contrast) · template-heavy chrome |
| Client proposal / bid | `consulting` · `editorial_report` · `swiss` · client co-brand | `synthwave` · `memphis` (unless the client is a creative brand) |
| Investor pitch | `dark_tech` · `glassmorphism` · `swiss` | `editorial_paper` (reads as a report) · `museum_memorial` |
| Training / onboarding | `swiss` · `bauhaus` · `midcentury` · visual languages `wayfinding` · `boardgame` · `chalkboard` | `luxury_dark` · `brutalist` (hostile to a learner) |
| All-hands / keynote / 年会 | brand custom · `glassmorphism` · `dark_tech` · `synthwave` (celebration) | `editorial_paper` · `consulting` (too quiet for a stage) |
| Culture / heritage / CN-brand | `ink_wash` · `eastern_traditional` · `museum_memorial` | `dark_tech` (register clash) — and the reverse: don't reach for ink/seal on a technical/clinical deck without a content reason (`east-asian-aesthetic.md`) |
