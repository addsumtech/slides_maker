# Visual-language system: contract, component skins, optimisation, any-agent use — design

Date: 2026-10-15 · Skill: `skills/slide-maker` · Status: approved in conversation, awaiting written review

## 1. Goal

slide-maker ships fifteen visual languages (four image-led, eleven drawn). This work makes them a **system**:

1. every language satisfies one machine-checked **contract**, so a sixteenth language is added by following rules
   and running checks, not by remembering ~25 touch points;
2. the general design capabilities and **components** (charts, timeline, process, comparison, KPI, org chart …)
   work inside every language and **wear its look** (colours, type, cards, rules, markers), readable on every ground;
3. the fifteen languages are **optimised** where an audit, verified by measurement, finds them weak;
4. an agent that is not Claude (Codex as the acceptance runtime) can use the languages from the docs and the
   scripts' printed output alone.

Success = all four phases delivered with their checks in CI; the component × language × ground matrix lint-clean;
a docs-only Sonnet run and one limited Codex run complete a deck without reading source.

## 2. Decisions taken with the user (2026-10-15)

| Question | Decision |
|---|---|
| How far must components "work" in a language | **Wear the language**: colours, type, card, rule and marker style follow it; readable and lint-clean. No per-component × per-language redraws. |
| Acceptance runtime for non-Claude use | **Codex real run, limited** (the user's Codex quota is small: one short run at the end) + docs-only Sonnet subagent runs while iterating. |
| Approach | **A — contract first**: per-language manifest + one conformance suite + skin vocabulary + authoring kit. |
| Order | Phase 1 contract → Phase 2 components → Phase 3 language optimisation → Phase 4 authoring kit + any-agent acceptance. Each phase gets its own plan and ships on its own. |
| Contract form | **One manifest file per language**; the data moves out of the central tables; sample fingerprints must stay byte-identical through the move. |
| Component coverage | Tier 1 = every general component; Tier 2 (full skin) = the ~15 most used. |
| Language optimisation | Verify every audit finding before fixing; recurring patterns become contract checks; the user approves before/after sheets before samples are committed. |
| Shared-gate frictions | Fixed in Phase 4 (they block non-Claude agents). |

## 3. Audit evidence (2026-10-15, read-only)

**A. Components inside languages** — every general component's runnable example (`sigs.py --example`, 38
components) drawn on an ordinary page (`k.new_slide()` + `rs.ground`) of every language × both grounds: 30 decks,
linted, the default-ground decks rendered.
- Dark grounds fail wholesale: the 11 dark grounds (editorial-ink, collage-slate, cutpaper-night, ink-night,
  drafting-cyanotype, starlit ×2, tally-night, chalkboard ×2, interface-dark) carry 102–116 hard findings each;
  light grounds 10–26. By class: LOW CONTRAST 583, INVISIBLE TEXT 470 (components draw fixed dark inks such as
  `#1B1B1B` / `#5A5A55`).
- Components do not wear the language at all: timeline dots, chart bars and table type are the same green and the
  same serif in all fifteen languages (only `poster` differs); type is small at deck scale; examples are placed by
  absolute coordinates, over the language's furniture (interface window, broadsheet masthead).
- Root causes in `deckkit.py`: `set_palette()` rewrites only the constants it knows; 79 literal `RGBColor(...)` and
  14 hex literals; font defaults captured at definition time; no component knows the ground is dark.
- Pre-existing, also on a plain deck with no language (baseline run): `leaderboard` example raises IndexError;
  `sankey` OVERLAP; `bento` UNEVEN CARD HEIGHTS; `agenda` / `card` examples add their own slides (an empty page
  is left behind); `native_chart` reads as an empty slide to the lint.

**B. The languages' own design** — a Sonnet art-director pass over the 30 bundled sample sheets (4 pages each)
produced about fifty per-language candidate issues and eight cross-language patterns. They are **candidates**: sizes were estimated from thumbnails and must be measured
(Phase 3). Cross-language patterns it reported:
1. the smallest tier (kicker, attribution, chip, running head) too small and faint — 13 languages;
2. quote pages under-scaled, 50–70% of the page empty, attribution crammed — 10 languages;
3. image-led data pages weak (number ~20% of page height beside an unrelated photo) — 4 languages;
4. contrast grounds that are recolours (white prints/cards/slabs at full brightness on dark): collage-slate,
   cutpaper-night, chalkboard-slate, journal-green, soft-dusk, storybook-meadow (art fades to cream, not the ground);
5. look-alike dark grounds (tally-night ≈ interface-dark; several navy grounds);
6. lists that end half-way down while rules/columns run on into emptiness — 6 languages;
7. under-scaled titles on quiet languages (storybook, starlit, cutpaper cover, interface cover);
8. decorative furniture that encodes nothing (poster's rotated blocks, chalkboard smudges and tray bar, …).
HIGH candidates: collage-slate prints, storybook-meadow haze, broadsheet points rules running past the text.

**C. The rule system today** — per-language data lives in ~14 tables in `visual_languages.py` (`LANGS`, `VARIANTS`,
`TYPE`, `NATIVE`, `NATIVE_IMAGE_PAGES`, `IMAGE_LED`, `NATIVE_EXTRAS`, `EXTRA_PAGES`, `SAMPLE_IMAGES`, sample copy,
display names, rationale, `_ground_<n>`, `_card_<n>`) plus compositions in `vl_native*.py`, the offer list in
`directions_diversity.py`, `sigs.py` scaffolds and prose lists/counts in ~8 docs; adding `wayfinding` touched ~25
files. Declarations are inconsistent: palettes carry 6–17 keys with no shared role set, TYPE 14–23 roles; the
`light` ground key of `starlit` / `chalkboard` is a dark ground; extras share names across languages (`tags`,
`total`, `ordered`) with nothing guaranteeing one meaning. Each batch (P3/P4/P5) wrote its own test file; a prose
count ("the nine DRAWN languages") drifted and was caught only by review.

**D. Any-agent use** — the docs-only runs of 2026-10-09/10 hit shared-gate frictions: the visual-language doc
promises "8" owed gates while `--gate-check` prints 12; `--gate-check` reports blind_read answered and then
"answers is missing"; GROUND REPEAT holds a deck whose ground the user named; rendering a second deck into the same
folder overwrites `render/`; `sigs.py --example` preamble builds a 13.333in canvas while the docs teach
`formats.blank_deck("16:9")` (10in).

## 4. Phase 1 — the visual-language contract

### 4.1 Manifest (one file per language)

`scripts/vl_specs/<name>.py` defines `SPEC` (a plain dict validated by `scripts/vl_contract.py`). Required:

- **identity** — `name`; `display` `{en, zh}`; `kind` `image-led | drawn`; `rationale` (one line);
  `offer` = topics `{en: [...], zh: [...]}` — the single source for every "which topic → which language" sentence.
- **grounds** — ordered map `ground_id → {label: {en, zh}, dark: bool, palette: {...}}`; `default` and
  `contrast` named explicitly (the `light` key no longer has to mean light: the ids stay as callers use them, the
  `dark` flag carries the meaning).
- **palette roles** (every ground, all required): `ground`, `ink`, `mute`, `card`, `card_ink`, `rule`,
  `accent[≥1]`, `on_accent`, `series[≥4]`, `highlight`; language-private colours live under `extra`. The validator
  computes and enforces: ink/ground and card_ink/card ≥ 4.5:1, mute ≥ 4.5:1 on ground, on_accent/accent ≥ 4.5:1
  (≥ 3:1 when only large text sits there), every series colour ≥ 3:1 against ground and card and
  pairwise distinguishable.
- **type roles** — the shared core every page and component may ask for (`kicker`, `title`, `subtitle`, `body`,
  `quote`, `attribution`, `number`, `label`, `note`, `caption`, `line`, `item_head`, `item_line`, `item_no`) with
  size / role / weight / colour role / italic / floor; private roles allowed; fonts per platform.
- **pages** — the seven page functions (`cover`, `section`, `image_text`, `points`, `quote`, `data`, `closing`)
  must be registered for the language (checked against the compositions registry); `image_pages`.
- **extras** — `name → {pages, remembered: bool, takes: <validator id>, absent: "<what is drawn without it>"}`;
  one extra name means one thing across languages (the validator compares shared names).
- **derived words** — every word a page may write that the caller did not give (page/point numbers, structural
  labels per script, way-out sign, initials rule …), with its localisations.
- **ordinary page** — `ground(slide, role, index) -> rect` and `card(...)` painters.
- **skin** (consumed in Phase 2, declared here) — see §5.3.
- **samples** — sample copy (en + one CJK script) and sample images.

`visual_languages.py` builds `LANGS`, `VARIANTS`, `TYPE`, `NATIVE`, `NATIVE_EXTRAS`, `EXTRA_PAGES` … from the
manifests, so existing importers keep working.

### 4.2 Migration

All fifteen languages move into manifests in one phase; behaviour does not change. Guard: every bundled sample's
fingerprint (`assets/vl/samples/manifest.json`) stays byte-identical, and the existing suites (P3/P4/P5, audit,
generality corpus) stay green. Roles a language lacks today are added (e.g. `series`, `on_accent`) without changing
any colour already drawn.

### 4.3 Conformance suite

`tests/test_vl_contract.py` iterates the registry; a language added to it is tested with no new test code:

1. manifest validates (schema + contrast + shared-extra meaning);
2. every page × canvas {16:9, 4:3, portrait 3:4, square} × ground × script {en, zh} with ordinary and long sample
   copy → builds, or refuses with a `VLTextOverflow` that names the field;
3. a deck of the language's own pages has no hard `lint_deck` finding;
4. **never invent**: every text run on a built page is the caller's text (allowing the documented re-casing and
   clause breaks) or a declared derived word;
5. every extra is refused by name on a page outside its `pages`;
6. the docs mention the language where the generated blocks say they must, `sigs.py --example vl_<name>` runs,
   the bundled samples exist and are current.

`scripts/check_vl_contract.py <name>` runs the same checks for one language (fast author feedback).

### 4.4 Docs that cannot drift

Lists, counts and offer guidance in `SKILL.md`, `references/visual-languages.md`, `interview-protocol.md`,
`codex-runtime.md`, `file-inventory.md`, `README.md`, `README_CN.md` and the `directions_diversity` message live
between `<!-- vl:… -->` markers and are written by `scripts/vl_docs.py --write` from the registry;
`vl_docs.py --check` runs in CI. SKILL.md edits keep `check_skill_lossless.py` green (allowlist with reasons).

## 5. Phase 2 — components wear the language

### 5.1 Theme read at call time

`deckkit` gains one theme object (`dk.THEME`) holding the contract's palette roles, type faces and skin; `vl.use()`
fills it, presets keep filling today's values. Components read colours and faces from it **when they draw**.
For a deck with no visual language the theme's defaults equal today's constants: a corpus of every component
example built without a language must produce byte-identical slide XML before and after, except where a change is a
listed fix.

### 5.2 Rules every component follows

- no literal colour inside a component body — `scripts/check_component_theme.py` (AST scan, CI) refuses
  `RGBColor(…)` / hex literals in component functions; a justified exception is allowlisted with its reason;
- text ink is chosen by contrast against the surface it actually sits on (card, band, ground);
- on a dark ground, cards, tracks and rules use the dark ground's roles — no full-white slab;
- type scales with the canvas and never drops below the language's floor for that role;
- matplotlib charts (`designed_charts`) take series colours, ink, face and a transparent background from the theme.

### 5.3 Skin vocabulary

Each manifest picks one value per drawing role; Tier-2 components route those roles through the skin:

| role | values |
|---|---|
| card | `filled`, `outlined`, `hairline`, `window`, `sign`, `chalk`, `paper` |
| rule | `solid`, `hairline`, `dashed`, `chalk` |
| marker | `dot`, `disc-number`, `roundel`, `circled`, `badge` |
| number | the face, weight and figure style used for numerals |
| series | the palette's `series` |

A value is implemented once (e.g. `chalk` card = the chalkboard box primitive) and reused by every language that
picks it; a new language mostly picks from the vocabulary and adds a value only when none fits.

### 5.4 Placement

In a visual-language deck a component lives in the content rect `rs.ground()` returns.
`sigs.py --example <component> --in <language>` prints a scaffold that places it there and runs as printed.

### 5.5 Coverage

- **Tier 1 — every general component** (the 38 probed): theme colours and faces, readable on every ground; the
  component × language × ground matrix is part of the conformance suite and has no hard lint finding.
- **Tier 2 — full skin**: `card`/`bento`, `step_list`, `timeline`, `table`, `native_chart`, `stat_row`, `org_tree`,
  `funnel`, `pyramid`, `venn`, `heat_matrix`, `gantt`, `tier_stack`, `meter_bar`, `agenda`.
- The docs list each component's tier.

### 5.6 Fixed in this phase

`leaderboard` example IndexError; `sankey` overlap; `bento` uneven heights; `agenda` / `card` examples leaving an
empty page; `native_chart` read as an empty slide.

## 6. Phase 3 — optimise the languages

1. **Verify first.** Each audit candidate (§3.B) is measured (sizes, contrast, extents) or checked on a full-size
   render; unconfirmed candidates are dropped and listed as such.
2. **Recurring patterns become contract checks** (thresholds calibrated on the current languages and on the
   confirmed defects, not guessed):
   - smallest-tier floor: kicker / attribution / chip / label / running head ≥ a canvas-scaled minimum size and
     ≥ 4.5:1;
   - no rule, column line or margin line extends past the content it serves by more than a set margin;
   - designed contrast grounds: on a `dark` ground a large near-white filled shape is flagged unless declared;
   - distinctiveness: each language's (ground, accent, display face) differs from every other's beyond a set
     distance, per ground.
3. **Fix the confirmed HIGH and MEDIUM items** per language (candidates include the collage-slate prints,
   storybook-meadow feathering, broadsheet rules, cutpaper-night cards, journal-green chart slab, soft-dusk disc,
   interface data-page label order and quote bubble, wayfinding quote page, quote-page scale, image-led data pages).
4. **The user's gate.** Before/after sheets per changed language go to the user; samples are committed only for the
   approved ones; a rejected change is reverted.

## 7. Phase 4 — authoring kit and any-agent use

- `references/visual-language-authoring.md`: the contract field by field; the design rules learned so far (never
  invent; a route or arrow only when the caller says ordered; measure with headroom and set the measured lines;
  alternative layouts before refusing; declared overlaps; the derived-words list; floors; designed contrast ground;
  distinctiveness; CJK rules — clause breaks, no spaces between CJK and Latin, Latin words never split); the steps
  from look-dev to shipped samples; a review checklist.
- `scripts/new_visual_language.py <name>`: writes the manifest skeleton and composition stubs; an unfilled field
  fails the conformance suite with a message naming it.
- `visual_languages.py --describe <name>`: pages, grounds, extras (pages, remembered, values), derived words, offer
  topics and a runnable example, printed from the manifest; the docs and the Codex runbook point to it.
- Shared-gate frictions of §3.D fixed.
- Acceptance: two docs-only Sonnet runs (one English, one Chinese; one of them uses general components inside a
  language) with every friction fixed; then one **limited Codex run** — the user runs one command given to them:
  one language, about five pages, executing only commands the scripts print.

## 8. Constraints (all phases)

- Never invent words, numbers or names on a page; derived words are declared.
- Commit locally; push, release or rsync the installed copy only when the user says so; after a push wait for the
  GitHub CI conclusion, then `rsync` to `~/.agents/skills/slide-maker` (dry run first).
- Before any push: the full local CI (`cisteps.py`, chunks under 10 minutes) and the Linux font simulation.
- Codex usage: the single limited run of Phase 4 only.
- CHANGELOG English-only; SKILL.md changes keep `check_skill_lossless.py` green.
- Fixtures are self-built; the user's own decks are never used as test input.

## 9. Not in scope (tracked)

- `fonts="mac"` measuring bold Helvetica Neue ~9% narrow (`display_type._glyph_width` opens a `.ttc` without the
  face index) — a measurement change across every language that needs its own corpus diff.
- Per-component × per-language native redraws (declined: Tier 2 skin instead).

## 10. Risks

- **Migration drift** — mitigated by byte-identical sample fingerprints and the existing suites per language.
- **Theme refactor changing ordinary decks** — mitigated by the byte-identical component corpus with no language.
- **Thresholds that cry wolf** (Phase 3 checks) — calibrated on confirmed defects and the current languages; a
  check that flags a page the user approved is re-examined, not silenced.
- **Phase size** — each phase ships alone with its checks; later phases build on earlier ones only through the
  manifest and the theme object.
