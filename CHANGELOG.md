# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each
section is a distilled summary — the full notes live on the
[GitHub releases page](https://github.com/addsumtech/slides_maker/releases).

## [Unreleased]

### Added — free-win deliverables & speed (multi-platform: identical on Claude Code / Codex / Windows)
- **PDF as a first-class deliverable** — the render pipeline already produces a PDF as its first
  step; `render_deck.py` now parks it beside the `.pptx` (`<deck>.pdf`) instead of burying it in
  `render/` — submission/email/print-ready at zero extra cost.
- **`render/viewer.html`** — a self-contained, zero-dependency flip-through preview generated on
  every render: one `file://` link, any browser, any OS (arrow keys / click / thumbnail rail /
  fullscreen). The fastest way to eyeball a deck without opening PowerPoint.
- **Persistent host-agnostic icon cache** — icon SVGs now cache in the platform cache dir
  (macOS `~/Library/Caches/slide-maker/icons` · Linux `$XDG_CACHE_HOME` · Windows `%LOCALAPPDATA%`,
  override `SLIDE_MAKER_CACHE`) instead of `/tmp` — shared across Claude Code AND Codex on the same
  machine, fetched once ever, and warm builds work offline. Hardened by an adversarial audit:
  atomic cache writes + self-healing torn entries, unwritable-cache fallback to tmp, and
  `check_env.py` now prints the active cache path.
- **`render_deck` out-dir safety** — the pre-existing `rmtree(out)` could wipe a user directory
  (passing `.` as out deleted the pptx itself); now the dir is only removed when it holds nothing
  but this deck's own render products (OS junk tolerated, `.git`/foreign PDFs route to a safe
  per-file clean). Special-character deck names (spaces/中文/&) verified; viewer title HTML-escaped;
  preview link is a proper `file:///` URI via `Path.as_uri()`. Docs synced (handoff-and-iteration's
  stale "PDF on request", FAQ §5 pipeline products, large-deck section-PDF cleanup, icons.md cache note).

### Fixed — ZH/EN system consistency (from a 2-round bilingual audit incl. a live CJK build test)
- **`presets.py` KaiTi platform bug** — `ink_wash`/`eastern_traditional` hardcoded `"KaiTi"`, a family
  name that does not exist on macOS (it's `"Kaiti SC"`); the ink presets' calligraphic titles rode an
  uncontrolled font substitution. Now resolved per platform via `_KAITI`; `east-asian-aesthetic.md`
  corrected (it claimed the reverse of `multilingual.md`'s correct table) and its PingFang body
  recommendation now carries the render-loop-trap caveat. Also repaired a docstring line that had
  split `from presets import preset` in half.
- **`wordmark()` CJK tofu** — a Chinese entity name resolved to a Latin face with no CJK cmap and the
  deck's sanctioned logo stand-in shipped as tofu chrome (verified). Now CJK-aware:
  font → EADISPLAY → EAFONT → a CJK-capable system face; documented in `multilingual.md` +
  `image-generation.md`.
- **`native_chart` CJK labels uncontrolled** — python-pptx writes font names into `<a:latin>` only,
  so chart category/series labels (一月/营收) fell back to the theme's EA default. `_theme_chart` now
  writes `<a:ea>` into every chartSpace `defRPr` (verified in the XML).
- **New build-time gate `CJK_NO_EA`** — CJK runs with no `<a:ea>` font now fail `lint_layout`
  (CRITICAL) at build time instead of only after the render round-trip; `lint_deck` stays as the
  backstop. FAQ §4 row added; SKILL.md's lint classifications updated.
- **`extract_pdf._load` aligned byte-for-byte with `lint_deck._text_load`** — CJK punctuation
  handling, ASCII-punctuation splits and rounding had drifted (~19% heavier on Chinese prose), so
  Chinese PDFs crossed long-source thresholds earlier than equivalent English ones (verified equal
  on mixed samples now).
- Checkpoint-table headers: documented that they follow the conversation language (the 中文 column
  names in SKILL.md are not fixed for English decks). FAQ: added the `PINGFANG ON MACOS` row and
  named `CJK TIGHT LEADING` in its row. README EN/CN micro-drifts aligned (fraction/matrix fallback
  wording, 独立复核, structured analysis, interview tab labels).

## [3.4.0] - 2026-07-19

### Added — multi-format source ingestion (Word · Excel · image · audio · video · cloud)
- The content-planner (`agents/content-planner.md` §1 "Input formats") now has an explicit ingest
  route + fidelity floor per source type: **Word `.docx`** (`ingest.py doctext` exact text+tables;
  long docs → `office`→PDF for long-source triage); **`.pptx`** → `extract_deck.py` (native);
  **Excel `.xlsx`** → `ingest.py sheet` (exact CSV rows; office→PDF drops data); **images** (place the
  pixels as a figure freely, but a number/quote *typed* off one is `verified? = N` until confirmed —
  no OCR); **video** (supplied transcript = precise spoken content; else `frames` samples the visual
  track and the narration is a flagged GAP — never invented); **audio-only** and **cloud docs
  (Google/Notion/URL)** get honest "supply a transcript / export the file" guidance.
- `scripts/ingest.py` — `probe` (detect + route), `doctext` (python-docx), `sheet` (openpyxl → CSV),
  `office` (LibreOffice → PDF; isolated temp profile, no litter), `frames` (ffmpeg keyframes, **capped
  at 60**, refuses audio-only files, honest "no STT" warning); clean errors + exit codes on every bad
  input; arg parsing hardened.
- **Fidelity mirror (both sides wired):** the planner routes pixel/audio-sourced claims through the
  claim ledger as `verified? = N` (with image/frame/transcript `source` tokens), AND the critic now
  enforces it — `references/review-rubrics.md` item 10 + `agents/critic.md` flag a number typed off an
  unverifiable image (blocker → show as a trend) and a video's reconstructed narration dressed as fact
  (major). Re-reading the same pixels is not confirmation.
- Wiring: Step-0 source question lists the formats + dedicated routes (uncrossed); nav-table + Files
  inventory list `ingest.py`.

### Changed / Fixed — holistic integration hardening (from a whole-delta 4-lens audit)
- **The CONTRACT CARD now carries the new artifacts** in all three enumerations (SKILL.md assembly ·
  critic.md · arbiter.md): the `source size:` line + the approved Source-coverage map on a long-source
  deck (critics judge completeness against its built-around/summarised set, never the whole book) and
  the transcript status on a video-sourced deck — closing the gap where the rubric told the critic to
  judge against an artifact it was never given.
- **Two-phase planner dispatch for over-threshold sources** — phase 1 (classify+map+triage) returns the
  draft coverage map, the coordinator posts the selection FYI and confirms the slice, phase 2 runs the
  verbatim deep-read; recorded as a `selection FYI:` plan line the checkpoint checks (a one-shot
  dispatch silently made the "early" FYI post-hoc).
- **`source size:` is now required for EVERY file-sourced deck** (not just self-declared long ones) —
  the bounded-vs-long classification is a recorded measurement; its absence blocks the plan (the gate
  was self-referential before: only sources already judged "long" ever got measured).
- **Arbiter wired into the fidelity mirror** — a pixel/audio-sourced ledger row cannot be confirmed by
  re-reading the pixels; absent an underlying-data/transcript locator the critic's finding is real
  (an arbiter following the old text could overturn a correct blocker).
- **Video gate** — a video-sourced plan must carry the transcript-status line (supplied locator or the
  visual-only GAP line), checked at the §1 self-verify + checkpoint + digest; supplied-transcript rows
  verify like text (they were wrongly pinned to `verified? = N`); pixel rows become shippable by
  appending the underlying-data locator and flipping to Y.
- **Stale re-key fixed** — the CONTENT-checkpoint precondition still gated "every `map` TOC chapter"
  (vacuous on a no-TOC book); now "every skeleton section" like everywhere else. CJK caveat on the
  `wc -w` fallback (undercounts ~6–30×); mixed-format multi-file sets convert non-PDF members to PDF;
  page-scoped figure locators on long sources (never whole-book `autofig`).
- **Tooling** — `ingest.py doctext` now extracts textboxes + headers/footers and warns on
  footnotes/endnotes (was silently dropping them while claiming "exact"); `sheet` warns when formula
  cells have no cached value (blank ≠ absent) and emits pure dates; `office` converts into a fresh
  temp dir + checks the exit code (a stale same-name PDF could masquerade as a fresh conversion);
  `extract_pdf.py headings` falls back to bold/ALL-CAPS candidates when a book has no font-size
  outliers; `map`'s no-TOC hint points at `headings`; EPUB no longer warned against (it's a
  documented route).
- **troubleshooting-faq.md §11** — symptom → cause → fix for every new ingestion/long-source error
  surface (the FAQ's "any failure" promise held again); `requirements.txt` lists the optional
  ingestion deps (python-docx · openpyxl · ffmpeg).

## [3.3.0] - 2026-07-18

### Added
- **Long-source mode** — the content-planner (`agents/content-planner.md` §1) now handles a **book
  or very long PDF** without faking a linear read (which either overflows context or, worse, fits
  and goes shallow, then fabricates plausible-but-absent points). The method: anchor on the deck's
  purpose first (importance is purpose-relative) → **map** the structure → read chapter-by-chapter
  into page-tagged notes (map-reduce; fan out the *reading*, synthesise as one mind) → **deep-read
  verbatim only the load-bearing ~20%** for slide-bound claims → trace every claim to a real page (a
  chapter note is corroboration, not a source). The plan gains a required **Source-coverage map**
  (each chapter → built-around / summarised / cut) so the SELECTION is explicit — the coverage gate
  at book scale — and it is confirmed at the CONTENT checkpoint (surfaced even under the auto-waiver,
  since the wrong-slice risk is the biggest one on a book). Honest limits are named: a scanned /
  image-only or DRM-locked PDF yields no text → ask for a text version / OCR / specific chapters.
- `scripts/extract_pdf.py` gains two long-source commands: **`map`** (structural skeleton — page/word/
  token estimate + the embedded TOC/bookmarks + a binned word-density strip, no body text) and
  **`text`** (dump a 1-indexed inclusive page range with PAGE markers, for chunked reading).
- SKILL.md wiring: a long-source case in Step 1, the Source-coverage/SELECTION gate on the CONTENT
  checkpoint, and nav-table + Files rows pointing at the mode and its tooling.

### Robustness — non-PDF · multi-file · no-TOC · CJK · graceful tooling (hardened from a 4-lens adversarial audit)
- **Non-PDF & multi-file sources** — the mode no longer assumes a single PDF. Step 0 classifies by
  type: PDF/EPUB via `extract_pdf.py map`; `.docx`/`.md`/Google-Doc/web → convert or a `wc`-style
  count; a code repo → size the file tree; **multi-file/multi-volume → sum pages/tokens across
  files**, with per-file coverage rows and `<file>:p.NNN` provenance cites.
- **No-TOC books genuinely gated** — the Source-coverage gate is re-keyed from "every `map` TOC
  chapter" to "every **skeleton** section (TOC *or* a recorded reconstructed skeleton)", so a no-TOC
  book can't pass vacuously; new `extract_pdf.py headings` reconstructs the skeleton by font-size
  outlier (no whole-book read).
- **CJK sizing fixed** — `map`/`text` used `.split()`, undercounting Chinese/Japanese/Korean 10-30×
  so a dense CJK book evaded the token trigger; now a CJK-aware load (`latin words + CJK chars / 2`).
- **Reading budgeted** — only `built-around`/`summarised` chapters are read; `cut` chapters are
  dispositioned from the skeleton unread; verbatim stays ~20% with a total ceiling; figures extracted
  per page from the plan's locators, never `autofig` over the whole book.
- **`extract_pdf.py` fails gracefully** — `_open` catches missing/corrupt/unopenable files (clean
  message + exit 1, no traceback) and flags a non-PDF; `map` warns on scanned PDFs; `text` counts
  body-only (excludes PAGE markers), rejects bad ranges, writes UTF-8; arg parsing prints usage, not
  tracebacks.
- **Critic rubric mirrors the planner** — `review-rubrics.md` item 10 widened: PROVENANCE covers
  book-page claims (a chapter-note-only "fact" = unverified), COVERAGE judged against the approved
  Source-coverage map's built-around/summarised set.

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
