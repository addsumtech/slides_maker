# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each
section is a distilled summary — the full notes live on the
[GitHub releases page](https://github.com/addsumtech/slides_maker/releases).

## [Unreleased]

## [3.2.0] - 2026-07-18

### Added
- **Boldness dial + signature-move distinctiveness axis** — the design plan now carries a
  two-line aesthetic-risk contract. `boldness: <conservative | balanced+ | bold | experimental>`
  sets how many beats may carry risk and how far the deck's ONE required `signature move` pushes
  (precedence: explicit user request > `taste.md`'s promoted dial > purpose-derived default;
  `balanced+` = exactly one genuine signature move). A pre-commit web pass for 2–3 genuinely
  distinctive references raises the ceiling before the move is fixed. Wired through
  `agents/slide-design.md` (contract + reference pass), `agents/critic.md` and
  `references/review-rubrics.md` (a distinctiveness lens that flags template-competent-but-timid
  work), `agents/arbiter.md`, `references/user-taste.md` (the dial is a promotable taste
  dimension), `references/large-deck-orchestration.md`, and SKILL.md.
- `scripts/smoke_deckkit.py` — a stdlib-only smoke test covering gradient-stop normalization
  (both shorthand and full-stop forms; the RGBColor-is-tuple parse guard) and the icon_tile
  contrast guard.
- Install channels: **SkillHub** and **Coze** added to `README.md` / `README_CN.md` alongside
  the existing `npx skills add` / marketplace paths.

### Changed
- The 3:4 social format is named **rednote** (小红书's English name) across `scripts/formats.py`
  and `references/canvas-formats.md`.

### Fixed
- `deckkit.icon_tile` guarantees glyph↔tile contrast **by construction**: when the glyph's ink
  is known (declared, or inferred from the PNG via `_png_dominant_ink`), the tile fill is
  auto-nudged to keep the pair ≥3:1 — a low-contrast icon-on-tile is now impossible rather than
  merely flagged after render.
- `deckkit._norm_stops` parses `(c0, c1)` shorthand, `(pos, colour)` pairs, and full
  `(pos, colour, alpha)` stop-lists uniformly, closing an RGBColor-looks-like-a-tuple ambiguity
  in gradient fills.

## [3.1.0] - 2026-07-17

### Added
- **Canvas formats** — `scripts/formats.py`, a named canvas-format registry (16:9 default ·
  4:3 · square 1:1 · 小红书 3:4 · story 9:16 · A4 print) with per-format dimensions,
  platform-UI safe zones, chrome policy, density guidance, lint flags, and a `band()`
  safe-content-rect helper (safe zones + footer reserve). Opt-in: the 16:9 default path
  never touches it, and all deckkit components carry over unchanged.
- `references/canvas-formats.md` — per-surface layout DNA, the inch-normalization sizing
  principle, the repurpose/batch pattern (one content plan → several surfaces), and three
  **verified layout patterns** (band-driven pitch distribution · closing element anchored
  at the band bottom · MIDDLE-anchored clusters) proven by a 6-format visual-verification
  pass (2 judge rounds per format, all-pass).
- SKILL.md wiring: the interview confirms the canvas format only for non-talk deliverables
  (social card / print); Step 3 documents the `formats.py` build path.
- `CHANGELOG.md` (this file), backfilled from the GitHub releases.
- `scripts/validate_review.py` — stdlib-only validator for the critic/arbiter review-JSON
  contracts (`python3 validate_review.py critic|arbiter <file|->`), with a `--selftest`.
- CI: a step asserting `plugin.json` and `marketplace.json` versions match, and a
  `validate_review.py --selftest` step.

### Changed
- Hardened gates from live-deck feedback: sourced-photo **aesthetic vetting** (+ a
  `searched, found but low-quality → generated, flagged illustrative` rung), title-over-hero
  legibility (a scrim only dims a bright frame-line — cover linework with a near-opaque
  panel; clear title↔subtitle gap), semantic-colour **text vs fill** two-token contrast rule
  (text ≥4.5:1), block text centered by construction, and rotating title-chrome treatments
  (2–3 per deck) so the title band never reads as one fixed template.

### Fixed
- `deckkit.part_eyebrow` default width (6.0in) now clamps to the real canvas, so eyebrows
  never overflow narrow (story/portrait) decks — found by the canvas-format verification;
  byte-identical on standard 16:9 calls.
- `.claude-plugin/plugin.json` version aligned to the marketplace manifest (3.0.0 → 3.0.1).

## [3.0.1] - 2026-07-15

### Added
- `references/troubleshooting-faq.md` — ten sections, every entry the same shape: the
  exact message you see → plain-language cause → first fix (error surfaces, env/install,
  build-time exceptions, both lint code dictionaries, render failures, `[stats]`
  guidance, image generation/sourcing, CJK, FAQ one-liners).

### Changed
- Error messages carry their fix inline: `OFF_CANVAS` / `OVERLAP` / canvas-`OVERFLOW`
  gained "→ how to fix" tails; failing lint runs print a pointer to the FAQ's matching
  section. `--json` output and exit codes stay byte-compatible.
- SKILL.md wiring: consult the FAQ before improvising a fix; report findings to the user
  in plain language, never as raw lint codes; both READMEs link the page.

### Fixed
- Five blockers from a 3-auditor adversarial pass fixed pre-ship (FAQ render section
  rewritten against the real `render_deck.py` pipeline; canvas-size and CJK line-spacing
  corrections).
- `lint_deck.py` no longer crashes on a 0-slide deck with an empty auto-discovered
  render dir.

## [3.0.0] - 2026-07-12

### Added
- **Identity-propagation contract**: a generated visual identity now propagates through
  all three layers of the deck — a type register derived from the image's character
  (8-family mapping with install-safe fallbacks), component geometry read off the image
  (outline weight · corner language · shadow/depth · fill flatness), and a four-line
  contract (palette · type · geometry · surface) recorded in the plan, shown at the hero
  checkpoint, and enforced by a new "identity-propagation break" critic finding.
- **Provenance contract** (planner MUST): a web-sourced load-bearing claim needs a
  primary source in the claim ledger; spliced figures and quote-mark abuse are named and
  banned.
- **Primary-source gate** before hand-off: independent verifiers with live web access
  try to refute every headline claim; the hand-off carries a `provenance:` tally line.
- Critic/rubric wiring: primary-source provenance (blocker), spliced figures (major),
  quote-mark abuse (major).
- deckkit: `sources_page` gains a `rule` param to suppress the accent hairline.

## [2.8.0] - 2026-07-12

### Added
- Design intelligence mined from JimLiu/baoyu-skills: 60 candidates audited, 12 adopted
  and hardened by a 3-auditor verification round.
- **Preset guards** — 1–3 countable register rules per preset, enforced plan → contract
  card → critic "REGISTER BREAK" → PRE-FLIGHT; an explicit user request lifts them as a
  named deviation.
- Diagram craft: layer-first system-architecture and happy-path flowchart recipes,
  complexity-escalation thresholds, z-order assembly guidance.
- deckkit: `diamond`/`parallelogram`/`cylinder` node shapes + connector `head` styles
  (defaults byte-identical).
- Quantified mood dial (subtle/balanced/bold), metaphor→concept rule, CJK ~1.7–2× width
  contract + new CJK pairing rows, typed dense-modules for read-alone surfaces.

## [2.7.0] - 2026-07-12

### Added
- **REFERENT RULE**: a real-and-specific subject gets a license-clear sourced photo —
  generation claiming photographic reality of a real referent is a fidelity bug on every
  template branch; a declared stylized register is the sanctioned illustration escape.
- Sourced-photo pipeline: sanctioned origins → subject verification → license + credit →
  palette treatment → per-row evidence tokens; ownership chain wired through
  slide-design, the main loop, and asset-prep, gated at self-verify / PRE-FLIGHT /
  checkpoint / critic.
- **Watermark gate**: a watermarked file is rejected and replaced, never
  cropped/blurred/inpainted to hide the mark.

### Changed
- 21-finding alignment sweep bringing `critic.md` fully to v2.6/v2.7 terms.
- Design hardening from a real fix-pass: "mute the HUE, not the VALUE", measured numeral
  stacks, and a 7-rule surgical fix-pass protocol for copy-in-place edits on foreign
  decks.

## [2.6.0] - 2026-07-12

### Added
- **STRANGER TEST for motifs**: a signature device must be legible to a first-time
  viewer — labeled at first appearance, figurative, or paired with an on-canvas legend;
  the checkpoint motif line states device + meaning + legibility mode.
- **LOGO PRINCIPLE** as a situation table with mandatory evidence tokens on the
  `logo plan:` line (`official asset — <source>` / `searched, none found → wordmark
  (flagged)` / `n/a — <reason>`).
- Enforcement wiring for both: design self-verify (n)/(o), PRE-FLIGHT 3(c), and new
  "opaque motif" and "logo missing or unevidenced" critic findings.

## [2.5.0] - 2026-07-11

### Added
- Icons are no longer optional on category/entity-rich content — enforced at
  self-verify (g), PRE-FLIGHT 12(e), the critic rubric, and the generated-template
  checklist.
- **Architecture rotation**: repeat the SYSTEM (palette/type/chrome), vary the
  ARCHITECTURE (takeaway slot ≤ ~half the deck per slot; ≥1/3 of protagonists
  direct-on-canvas).
- New lints: `BOTTOM-STRIP MONOCULTURE`, `STRETCHED THIN`, `DEAD BOTTOM`,
  `ONE-OFF CANVAS FLIP`; per-slide JSON exports `n_pic_fg` / `content_bottom` /
  `col_void`.
- Content-planner DISTRIBUTE pass + a `units` column on the content checkpoint table.

### Fixed
- `UNDERFILLED` no longer disabled by a full-bleed background plate — only substantial
  foreground imagery earns whitespace.

## [2.4.0] - 2026-07-10

### Added
- **Anti-greedy design gates**: divergent form choice (each slide names a runner-up from
  a different form family), a literal PRE-FLIGHT form-family tally, new `CARD DOMINANCE`
  and `UNDERFILLED` lint warns, and a content-planner frame-fill/merge check.
- **Style-first generated-template gate**: three deliberately diverse visual languages
  shown as real generated candidate images in one HTML gallery; the winner's image is
  reused as the deck's hero.
- Style library broadened to ~40 styles across 8 families, grounded in a web sweep of
  current design taxonomies.
- Topical whole-deck backgrounds: every main-content slide's generated background must
  carry the deck's own subject motifs — never generic texture.

## [2.3.0] - 2026-07-10

### Fixed
- Robustness audit: 34 issues fixed from a two-arm audit (5 real decks built + a static
  audit), all render-verified. Headline fix: wrapping titles are no longer struck
  through by the accent rule (`title_bar`/`cover`/`colophon`/`editorial_header` measure
  the wrapped title).
- Theming propagation: `deckkit` fonts/palette now resolve at call time; new
  `deckkit.set_palette(...)` re-themes the whole component set in one call.
- Provable ≥4.5:1 contrast on seven components; auto-fit/overflow fixes on `scorecard`,
  `segmented_bar`, `pull_quote`, `table`.
- Data honesty & i18n: `_numlabel` kills scientific notation, `dumbbell_board(regress=)`
  recolours regressions to risk red, ASCII minus in `waterfall`, i18n label params on
  `eval_matrix`/`colophon`, `hub_spoke` collision guard.

### Added
- New lints: `META-ANNOTATION LEAK`, `INVERTED TYPE HIERARCHY`, `LOPSIDED`, and
  grey-on-white contrast.

## [2.2.1] - 2026-07-08

### Fixed
- Value-encoding fidelity patch — the geometry now matches the number:
  `native_chart`/`native_pareto` columns pin the value axis to 0 by default;
  `tier_stack`/`funnel` widths track `value/max` with only a hairline floor (side leader
  for too-thin bands); `heat_matrix(scale='div')` zero-centres its neutral.

### Changed
- The root cause generalized into `data-viz.md`, `design-principles.md`, a critic
  value-encoding spot-check, and the SKILL render self-check ("Geometry matches the
  number"); every other value-encoding component audited faithful.

## [2.2.0] - 2026-07-08

### Added
- Appear-builds are the user's opt-in, and once a slide animates the reveal is fully
  staged — nothing pre-shown but the title/frame (fixes the half-animated-slide bug).
- Six new components: `tier_stack`, `gantt`, `waterfall`, `eval_matrix` +
  `harvey_ball`, `heat_matrix`, `device_frame`; ten Tier-2 compose-from-primitives
  recipes.
- Background & cover taste rules: harmonised background zones, topical covers even on
  flat templates, varied canvas value dosed like the WOW.

### Changed
- Complete scenario → component routing audited against the full inventory.
- "You decide" derives, it doesn't default; README repositioned around the real moat.

## [2.1.0] - 2026-07-07

### Added
- **Contract card** handed to critic/arbiter (deck message, takeaway/role/question/beat
  table, claim ledger, carrying elements, declared design contracts); the critic emits a
  `plan_audit`.
- **Spoken thread**: the planner authors the per-slide talk track, piped verbatim into
  speaker notes; lint counts it (NO NOTES warn).
- Money slide, takeaway spine test, plan-time word-budget check, assertion-title
  binding, evidence manifest, recorded fresh-eyes probes, do-not-harm strengths ledger,
  and a one-line ceiling on every consent.
- **Portable taste profile** (`taste.md`): durable cross-deck preferences you own —
  seeds defaults, never overrides the current deck.
- deckkit `axis_scale` / `dot_strip` / `pangu()`; new advisory lints `SKELETON VARIETY`,
  `TIMID COVER`, `FLAT RHYTHM` + bookend thumbnails for the poster test.

## [2.0.0] - 2026-07-06

### Added
- **The taste layer**: TASTE PROTOCOL (judge like a person, then check like a machine),
  editor's stance + COVERAGE GATE in the content-planner, art director's stance
  (blank-canvas sketch first, catalogue second).
- New components: `kpi_card`, `flow_compare`, `cycle_diagram`, `dumbbell_board`,
  `icon_chip`, `conclusion_strip`, `tint()`.
- lint: `--json` structured output, `--surface`, `--textheavy`; critic findings ordered
  by leverage; arbiter escalation escape hatch.

### Changed
- Interview & pipeline hardening from a 5-slice adversarial audit (11 verified
  conflicts/gaps fixed); standard mode vs per-deck AUTO WAIVER separated; returning-user
  history rolls up to one option; checkpoints are compact in-chat tables.
- READMEs (EN+CN) realigned to the full agent roster and two-checkpoint flow.

## [1.0.0] - 2026-07-05

### Added
- Initial public release: a paper, repo, doc, or topic becomes a native, editable
  PowerPoint — real text boxes, native charts, editable formulas, speaker notes, and
  click-build reveals — planned, built, and independently reviewed by a team of agents
  (content-planner, critic, arbiter, asset-prep).
- One-line install straight from `main`: `npx skills add addsumtech/slides_maker`; the
  demo site + template gallery moved to `slides_maker-site` (slides.addsum.top).
- Deterministic layout lint catches invisible / low-contrast dark-on-dark text;
  bilingual README + 8-direction template gallery.

[Unreleased]: https://github.com/addsumtech/slides_maker/compare/v3.0.1...HEAD
[3.0.1]: https://github.com/addsumtech/slides_maker/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/addsumtech/slides_maker/compare/v2.8.0...v3.0.0
[2.8.0]: https://github.com/addsumtech/slides_maker/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/addsumtech/slides_maker/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/addsumtech/slides_maker/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/addsumtech/slides_maker/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/addsumtech/slides_maker/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/addsumtech/slides_maker/compare/v2.2.1...v2.3.0
[2.2.1]: https://github.com/addsumtech/slides_maker/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/addsumtech/slides_maker/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/addsumtech/slides_maker/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/addsumtech/slides_maker/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/addsumtech/slides_maker/releases/tag/v1.0.0
