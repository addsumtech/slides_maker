<!-- Extracted from SKILL.md Step 4 PRE-FLIGHT (L1697-1748) -->
<!-- This file is loaded on-demand when the corresponding Step runs. -->
<!-- SKILL.md retains a skeleton summary + pointer to this file. -->

# PRE-FLIGHT Checklist (12 items)

> The 12-item PRE-FLIGHT boarding-pass checklist run before the first whole-deck render, with detailed criteria for each item.

---

### 🔴 PRE-FLIGHT — tick these 12 before the first render, EVERY deck, no exceptions
*(The Step-4 SIGNATURE PROOF is not "the first render" in this sense — it is a one-slide probe of a
deck that does not exist yet, so most of these 12 have nothing to check. Run the ones that apply to
that single slide (legibility, no placeholder text, lining figures), and run the full 12 before the
first WHOLE-deck render as always.)*
This is the fixed boarding-pass between build and render. **Emit it as twelve literal ✓/✗ lines** (in
your working notes or the build script's tail comment) — writing the ticks is what forces the checks
to actually run; a deck with un-ticked pre-flight items is not ready to render. It exists because
these are the rules that history shows get *silently* skipped when they live only as prose — they are
judgment calls the render-time lint cannot measure (lint already covers: word load, ink coverage,
font drama, build presence, layout sameness, CJK ea-font, contrast, footer, overlaps — don't re-tick
those here; read its report instead).
1. **Speaker notes**: presented deck (screen-shared = presented) → every slide's notes = the plan's **Spoken thread, verbatim**, via `dk.speaker_notes` (deviations — e.g. a split/merged slide — noted in one clause); self-read → prose is ON the slides instead.
2. **Builds — opted-in? then FULLY staged**: builds appear only if the user opted in; every animated slide reveals ALL its content beats in order (nothing content-bearing pre-shown but the title/frame — no half-animated slide), starting from an empty content area (first beat included), with no spoiling summary/legend in the base.
3. **Plan↔code correspondence**: (a) mechanical — diff the design plan's per-slide rows against the slide-function docstrings (icon family included; the classic inline-mode miss); (b) spot-check — each `build:` docstring has matching `Build.step` calls in its function body; (c) **cover carries its promises** — the built cover shows the self-verify-(l) device, the motif's label/legend where the plan said the STRANGER TEST is satisfied by labeling, and the `logo plan:` asset placed as planned (official file untouched; on a single-entity deck a cover with no logo and no recorded `n/a` reason is a ✗).
4. **Charts native**: every chart is editable-native unless a matplotlib look was deliberately chosen; legends sit off the data. Same bar for math: every 1-D equation is `equation_native`; raster `equation_png` only for genuinely 2-D layout (fractions/matrices), named as such.
5. **Evidence real**: every domain image/figure is the real computed/source artifact — no plausible stand-in; PDF crops checked on all four edges; every SOURCED photo comes from a sanctioned origin (Commons / Openverse / press kit / user file), its subject verified against caption/geotag/category, it is **watermark-free** (a watermark is an unlicensed-preview tell → reject the file; never crop/blur/inpaint the mark away), its license recorded (credit placed where required), it is **aesthetically vetted** (an ugly / under-construction / blurry / unrepresentative shot is rejected even when the subject is correct → re-source, or generate a declared-stylized illustration via the `searched, found but low-quality → generated, flagged illustrative` rung), and it is palette-treated so mixed sources read as one deck; no generated CONTENT image claims photographic reality for a real-and-specific subject (REFERENT RULE, `references/image-generation.md` — generated-template identity plates and declared stylized illustrations are exempt; a real subject with no findable photo uses a recorded `searched, none found → …` rung). Any **text over a hero/photo/plate** is verified legible against the pixels — no image linework crosses the glyphs (a scrim only dims a bright line; cover it with a near-opaque panel), eyebrow/kicker included, with a clear title↔subtitle gap (render self-check "Text over an image").
6. **Colour keyed**: the semantic-colour ledger's meanings are taught on-slide (key at first use) and no accent appears outside its bound meaning; chrome stays quiet — the **loud** signature motif ≤3 appearances (a *quiet register signature* — faint grid/scanline, corner numeral, edge rule, small seal — MAY repeat on every slide; that is SYSTEM, not stamping) — AND the chosen preset's `guard` constraints hold on every slide (quote the guard line in the tick).
6b. **Register carries all pages (的风格要走所有页)**: the quiet register signature reaches ordinary interior slides, not just the cover/dividers — the `interior register:` contract cue is present on interiors, or a `none (flat by register — <reason>)` carve is recorded. A style dressed only on the bookends fails.
7. **Claims current**: every time-bound ledger row re-verified with as-of = TODAY; the deck carries its "as of" date.
8. **Language & hygiene**: one language throughout; zero meta-annotations ("placeholder"/"TODO"/"AI-generated"); voice pass done on every line.
9. **Eye path**: squint each slide — first look lands on the named hero, 3–4 hierarchy levels survive the blur.
10. **Hand-off ready**: font/portability deps + per-slide click order noted for the hand-off; open questions carried, not dropped; output dir resolved + announced (`~/Downloads/<deck>/` or the user's stated choice); image licenses/credits noted (sourced photos).
11. **Titles bound to takeaways**: every content slide's title IS the plan's takeaway or a compression keeping its subject + verb + claim; **list the slide numbers** of compressions and of noted exceptions (bare topic labels are fine on cover/divider/agenda/closing; a named exception covers: Mode A "match its title treatment", a registered user template with a fixed title register, or a slide whose planned takeaway demonstrably lands as its named hero / `insight_banner` / `takeaway_rail` — note which element carries it). Emitting the slide numbers, not just a ✓, is what forces the per-slide comparison.
12. **Form diversity & frame fill — EMIT THE TALLY**: **first run
    `python scripts/component_audit.py build_<deck>.py <deck>.pptx` and paste its two summary lines
    into the tick** (it takes ~50ms and reads the finished file, so it costs nothing and cannot be
    guessed). It states one fact — how many of the form components it can name a guarantee for this
    deck actually called (deckkit's wider form catalogue is ~59) — and points at clusters whose
    geometry matches a component the deck never used. **If it prints `NOT CHECKED`, the tick is not
    done**: a wrong path or an unreadable deck exits 1 and says so, rather than reporting clean.
    **It is ADVISORY BY DESIGN and must never be treated as a blocker:** geometry cannot tell a lazy
    hand-roll from a deliberate bespoke composition, and the deliberate one is the *signature move*.
    So for each cluster, either reach for the component, or write the one clause that makes the
    hand-roll a decision ("the track is the deck's motif — a meter_bar would centre the value and
    kill the gap"). *(Why this tick exists, measured: across three delivered decks the build scripts
    called 3 of 59 form components. Every other form was composed from raw box+text, re-inheriting
    the geometry bugs — a baseline short of the last bar, a value label off the bar's centreline —
    that the components were written to fix. SKILL.md had said "when a COMPONENT exists, BUILD that
    component" as prose for a long time; it was violated dozens of times and detected zero times.)*
    Then write the deck's form-family tally as one literal line (`cards/panels: N · diagram: N · chart/proportional: N · big-type/editorial: N · timeline/roadmap: N · hero-image: N …`) and check six things against it: (a) **no family >~40% of content slides** — a first draft's greedy default is the card/panel, and per-slide checks can't see deck-level sameness, so this tally is the one place the crutch becomes visible; (b) every slide whose content is a RATIO / FLIP / DIVISION / PROCESS uses the form that *shows* it (a proportional bar, a topology diagram, a split, a roadmap), not a box that states it; (c) each interior slide **fills its frame** — a slide whose content ends in the top half either gets enriched, merged with its neighbour, or names its deliberate quiet register in one clause; (d) **one canvas system** — no background value/colour flip landing on exactly one interior slide (a flip must recur as a divider family or bookend; on the generated-template branch the plate stays on every content page and rhythm comes from imagery strength — `ONE-OFF CANVAS FLIP` lint is the render-time backstop); (e) **icons where content is categorical** — list the slides whose content names tools/entities/roles/pillars/categories; each such slide carries the planned icon family (one family, palette-recolored) or a one-clause waiver — "opt-in" never waives this silently (self-verify (g)); (f) **architecture rotation** — emit a second one-line tally of each content slide's TAKEAWAY SLOT (bottom-strip / side-rail / inline / headline / none) and CONTAINMENT (panelled / direct-on-canvas): no single takeaway slot on more than ~half the content slides (a bottom strip on every page is a template tell — `BOTTOM-STRIP MONOCULTURE` lint backstops it), and on a calm canvas at least ~1/3 of content slides put their protagonist directly on the canvas, un-panelled. Emitting the tallies + the (b)/(c)/(d)/(e)/(f) slide numbers, not just a ✓, is what forces the deck-level look a slide-by-slide build never takes.

**Gates never collapse.** A quick / low-stakes / inline run scales the *size* of each artifact
(a 5-line content plan, a 10-line design plan), never the *existence* of the gates: interview →
content plan → design plan (with self-verify) → pre-flight → lint+stats → critic. Every rule-miss
this skill has shipped happened when a step was run "in my head" instead of emitted — if it isn't
written down, it didn't happen. **The auto-waiver/inline path is where this bites hardest:** with
no checkpoint audience, the build slides into a single greedy pass that reaches for the same
handy component on every slide and stops at "nothing's broken" — every gate above is a floor, and
only the emitted form-candidates (per-slide runner-up from a different family) + the PRE-FLIGHT 12
tally push toward the ceiling. A delegated deck emits them for itself, not for the user.

