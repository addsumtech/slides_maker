# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each
section is a distilled summary — the full notes live on the
[GitHub releases page](https://github.com/addsumtech/slides_maker/releases).

## [Unreleased]

## [3.7.0] — 2026-07-21

### Added — design components the form catalogue kept prescribing and could not draw
- **`deckkit.small_multiples`** — a grid of identical mini native charts on ONE SHARED value axis,
  with an optional hero panel. The cheapest correctness win in the set: `data-viz.md` and
  `form-selection.md` both prescribe shared scales, but composing `native_chart` per panel by hand
  let PowerPoint auto-scale each one, so **a small bump and a huge bump rendered identically** — a
  silent misreading no geometry lint could see. The regression asserts the axis contract itself.
- **`deckkit.position_map`** — N labelled items on two continuous axes, with greedy label
  anti-collision and a `ValueError` naming any pair it cannot separate. `quadrant()` returns four
  cells and discards the within-cell position that is usually the whole argument; `native_bubble`
  drops the labels.
- **`deckkit.annotated_figure`** — a real figure + numbered fractional-coordinate markers + a
  numbered caption rail + an optional magnified inset (via `Picture.crop_*`, no image processing).
  The inset picks the first corner that covers no marker. This is the form the skill's own
  integral-figure philosophy most insists on and least supported.
- **`deckkit.org_tree`** — tidy hierarchy layout: post-order centroid placement (the part that stops
  being hand-placeable at depth 3), horizontal bus connectors, and a hard `ValueError` when it cannot
  fit legibly rather than silently squeezing.
- **`image_fx.quiet_region(path)`** — grid luminance-variance scan returning the image's calmest
  **single-ink** region plus its mean luminance, so title placement and ink colour are measured
  rather than eyeballed. Two fixes found by running it on real photographs: the growth threshold
  anchors on the image's own variance distribution (one flat cell otherwise made every gradient
  neighbour look "busy"), and growth requires luminance coherence — a full-height column spanning
  dark sky and light ground averages to a mid-luminance where *neither* ink is safe.
- **`deckkit.design_intent(slide, envelope=, rhyme=, reason=)`** — the declared-register channel that
  three lint messages already promised ("record the quiet-register exception") with nowhere to record
  it. Stored as an invisible zero-ink tag shape, so intent travels **inside the .pptx** to the
  render-time lint with no side-channel file. Abuse is audited (`INTENT INFLATION`).
- **`deckkit.pic_alpha(picture, pct)`** — native picture opacity via `a:alphaModFix`. Against the
  scrim-overlay approach the A/B is unambiguous: the image keeps its own hues instead of being tinted
  toward the scrim colour, and there is no second full-bleed shape.

### Added — `--fast` incremental render
- **`render_deck.py --fast` re-renders only the slides that changed.** Profiling an 18-slide deck:
  build 1.8s, LibreOffice→PDF 9.1s, rasterize 24.4s cold. Rasterization, not the PDF export, is the
  larger cost. Measured: **12.3s → 4.7s** for a one-slide change, **0.07s** when nothing changed;
  outputs byte-identical to a full render.
- Each slide is fingerprinted (its XML + rels + the bytes of the media it references) and mixed with
  a **deck-global digest** (presentation.xml, theme, masters, layouts). That digest closes a hole
  found by testing: flipping the canvas 16:9→4:3 changes no slide XML, so `--fast` previously
  reported "no slide changed" and left every PNG at the wrong aspect ratio.
- **Correctness over speed throughout** — a stale PNG is worse than a slow render, because the lint
  and the visual critic both trust `render/*.png` to BE the deck. Full-render fallbacks (each with a
  printed reason) for: changed slide count, hidden slides, auto slide-number fields, or no cache.
  Cache writes are atomic and **delete the cache on failure**.
- Hardened against an adversarial audit (27 candidates → 5 must-fix, all reproduced): hidden slides
  broke the page↔slide mapping on the pre-existing full path too; an unresolvable part hashed to a
  constant so real edits stopped registering; the subset PDF collided between concurrent runs;
  `--fast --deliverables` exited 0 having produced no PDF (now rejected at parse time); and media
  owned by a layout/master/theme was invisible to the digest.

### Added — deck-level design gates (the second design-capability tranche)
- **`ENVELOPE MONOCULTURE`** — fires when >60% of interior slides end their content at the same
  height. A deck can vary every form and still read as one template because every page fills the
  same rectangle; this is judged as a *distribution*, not per slide.
- **`REGISTRATION DRIFT`** — consecutive title tops drifting 0.02–0.12in. Identical is calm and a
  deliberate jump is a decision; a sub-visible wobble is neither, and reads as a twitch when
  advancing.
- **`INHERITED_EFFECT`** — warns when a shape bypasses the theme-shadow strip (below).
- **`DEAD BOTTOM`**'s per-slide floor drops 0.62 → 0.45, so only the genuine accident fires; the
  0.45–0.62 band is a legitimate upper envelope and is now judged by the distribution check instead.

### Changed — `OLDSTYLE_FIGURES` is a WARN; the defect is prevented in the components
- **v3.6.0 shipped this as a hard build blocker. It is now a WARN**, and the defect is prevented at
  the source instead: `numeral_run_face()` resolves a lining face inside every component that emits a
  figure, so correct output is the default rather than a rule authors must satisfy.
- **Why the architecture changed rather than the threshold:** a fourth audit round found *more*
  defects than the third (12 non-minor vs 5), three self-inflicted by the previous fix round. As a
  blocker the rule has an unbounded false-positive surface — every component × every font × every
  string shape — while being structurally blind to where numbers most often live: tables and native
  charts report `has_text_frame=False`, so their numeric cells and tick labels were never checked at
  all. `"7"` (a single digit, which cannot bob), `"10x"` and `"H1 2026"` were blocked; a cover whose
  title IS a year had no fix available to its author.
- A project that wants it fatal asserts over its own finished file — which is what a build script can
  now do in three lines.

### Changed — numeral faces resolve from the deck's design (visible change)
- **`big_numeral`'s default face changed.** It was hard-coded `serif="Georgia"`; it now resolves
  through `deckkit.numeral_face()`, which keeps a lining SERIF (Times New Roman) by default. The
  register is preserved — an oversized italic serif figure, as before — but the digits no longer
  sit at mixed heights. **A deck rebuilt from an older build script will render its marker numerals
  in a different face.** `serif=` still overrides, except that an old-style face is substituted
  (lint_layout would reject it).
- `stat_row`, `scorecard`, `kpi_card` and `change_stat` route their FIGURE runs through the same
  resolver, keeping each component's own default (body font) while guaranteeing lining digits.
  Previously these inherited a body/display face and could hard-fail their own output on a deck
  whose font is Georgia.
- Which faces count as old-style is **measured from the installed font** rather than read off a
  list; the curated set is only a fallback for fonts the machine does not have.

### Changed — the PDF and viewer.html are reserved hand-off deliverables
- They were produced on **every** render and parked at the deck root. A deck is rebuilt each critic
  round and then usually hand-edited in PowerPoint, so both went stale the moment the .pptx changed —
  and **a stale PDF is worse than an absent one**, because someone opens it and reviews the wrong deck.
- `render_deck.py` now takes **`--deliverables`** (alias `--final`), off by default. The PDF still
  exists as a render intermediate inside `render/`; the flag is what promotes it to the deck root and
  writes the viewer. The default run prints a one-line reminder of how to produce them at hand-off.
  `--fast` and `--deliverables` are mutually exclusive, enforced at flag-parse time.

### Security — the metered image rung asks before it bills
- The generated-template branch had three rungs (native imagegen → codex CLI → `OPENAI_API_KEY`)
  governed by one rule: *never block on a choice when a working path is present*. Right for the two
  subscription rungs, **wrong for the third** — it treats a present API key as authorisation. On a
  machine with no codex CLI but an exported key, the skill would have started billing per image
  without asking.
- **BILLING GATE:** rung 3 is metered, an available key is NOT consent, ask before the first paid
  call — a red stop **explicitly not waived** by a per-deck auto directive (delegation covers
  preferences, never the user's money) — and on a decline fall back to a native look rather than
  spending. `agents/asset-prep.md` (a subagent brief, which could have spent money with no way to
  ask) and `generate_images_codex.py`'s own failure message are corrected to match.
- **Claude Code's real cost is now documented:** CC has no native image tool, so the codex CLI IS the
  path there — free on the subscription, one `codex login`. Q1 probes for a free path *before*
  offering the branch, so a user cannot pick a look nothing can generate.

### Fixed — the inherited theme shadow under every generated shape
- python-pptx stamps `<p:style><a:effectRef idx="2">` on every autoshape, connector and freeform,
  resolving to the theme's soft drop shadow. `shadow.inherit = False` writes an empty `<a:effectLst/>`
  into `spPr` — **PowerPoint honours that, LibreOffice does not**, and LibreOffice is what the render
  loop and the visual critic look at.
- Measured under a plain box: a ~10px grey gradient (185,185,185 → white) under every card, chip,
  callout, tile, node and device frame **in every deck this skill has ever produced**. It is the
  single artifact that most separates "2010 SmartArt" from flat editorial, and no author could have
  seen it — the XML says there is no shadow. (It also explains an earlier round spent warming a
  frosted tint because panels "read cool grey": the grey was largely this.)
- `_flat()` removes the element at all 20 shape-creation sites. Deliberate shadows are unaffected
  (`offset_shadow`, `glass_card`).

### Fixed — a failed render reported as SUCCESS, and four lint false positives
- **CRITICAL:** `_render_pdf` returned the *expected* path and `main` only checked
  `os.path.isfile()`, never `returncode`. With `out` == the deck folder (where a `--deliverables` PDF
  legitimately lives) a **stale file satisfied that check**: the run printed "rendered N slides",
  exited 0, left the old PNGs, and wrote fresh fingerprints — so the next `--fast` said "no slide
  changed" and the stale render became permanent. Conversion now always targets a private empty temp
  dir, a non-zero exit is fatal, and the out-dir cleanup runs only after the PDF is verified readable.
- **The old-style font blacklist was factually wrong.** Measured from the installed fonts: Palatino
  digit top-spread 2/100pt, Baskerville 2 — both *lining*, both wrongly blocked. Replaced the list
  with measurement. (The list had been copied from the skill's own prose without checking it.)
- **The gate inverted on CJK:** `_digit_share` divided by raw character count, so `"2026 Roadmap"`
  scored 0.36 (warn) while `"2026 年路线图"` scored 0.50 (build failure) — Chinese decks did not get
  the carve-out SKILL.md promises. Now weighted by visual width, with the threshold re-measured into
  the empty gap between word-bearing headings (≤0.40) and real display numerals (≥0.67).
- **`_font_file` shadowing:** the numeral resolver was overridden by matplotlib's same-named helper
  later in the module, so "measured" detection actually measured DejaVu for every uninstalled face —
  on a host without Georgia the rule was silently dead.
- Four lint checks were firing on correct design, all reproduced before and after: `FOOTER-ZONE`
  judged the declared frame instead of the rendered ink; `CROWDED` counted a hero photograph's area
  as reading density; `INVERTED TYPE` fired on every interior statement slide (a ≤12-word largest run
  is the hero line, not a broken hierarchy); and `OVERLAP` flagged small textless markers riding a
  line or ring — composition, not collision, and 13 of one deck's 24 standing findings.
- **`position_map` hero labels are bound to their dot** — the hero claims its slot before the greedy
  anti-collision pass, and its label takes the dot's own hue. Found by building a real deck: the hero
  point's label had been nudged next to a *different* dot and read as that dot's subtitle. Bold alone
  says "important"; it does not say "belongs to THAT one".
- `_slide_fingerprints` re-hashed shared media once per referencing slide (40-slide deck sharing one
  plate: **318ms → 35ms** via part memoization); the subset temp dir leaked on every failure path.

## [3.6.0] — 2026-07-20

### Added — `OLDSTYLE_FIGURES`: a documented rule becomes a deterministic gate
- **`deckkit.lint_layout` now hard-fails on display numerals set in an OLD-STYLE (text) figure
  face** — Georgia, Palatino, Baskerville, Book Antiqua, Constantia, Hoefler Text, Calluna, Candara.
  Those faces set 0/1/2 at x-height, push 6/8 up and drop 3/4/5/7/9 below the baseline, so a hero
  number visibly bobs and misaligns with adjacent CJK/Latin. The check names the face, the offending
  run and its size, and points at the lining-figure fix.
- **Threshold-aware, so it is right rather than merely strict:** fires at **≥20pt** only. Old-style
  figures inside running prose are a legitimate typographic choice and stay quiet; the gate targets
  display numerals, where the wobble is a defect.
- **Why this shipped as code and not more prose:** the rule was already written in *five* places —
  `SKILL.md`, `design-principles.md`, `font-guidance.md`, `multilingual.md` and `critic.md` — and was
  still missed on a real deck, twice, across two skills. That is precisely the failure mode SKILL.md's
  own enforcement invariant warns about: *a MUST that lives only in reference prose is advisory in
  practice*. Geometry linters cannot see it (it is a font property, not a layout fault) and render
  thumbnails are too small to reveal it, so nothing downstream caught it either.
- Wired end-to-end: the CRITICAL in `lint_layout`, a plain-language row in `troubleshooting-faq.md` §4,
  the hard-fail list in `SKILL.md` updated from four items to five, and a **four-case regression test**
  in `smoke_deckkit.py` covering both directions (Georgia/Palatino display numerals fail; Georgia body
  prose and a lining-face numeral pass) — so the gate itself is verified to fire, not merely present.


### Added — composition / target / range components (native, editable)
- **`native_chart` stacked & area kinds** — `column_stacked` · `column_stacked_100` · `bar_stacked` ·
  `bar_stacked_100` · `area` · `area_stacked` · `area_stacked_100`: real editable PowerPoint charts for
  **composition over time** (a total AND its component mix — the most common exec chart the roster
  couldn't draw). Series-fill themed, `zero_base` extended to stacked column/bar, CJK `<a:ea>` labels
  intact; a printed notice fires on negative segments (a stack's height only reads as a sum for
  same-sign parts).
- **`deckkit.bullet_graph`** — Stephen Few's 'actual vs TARGET, in context' KPI bar (poor/ok/good bands +
  a target tick), one row per metric. Each row scales to its OWN max, so a **mixed-unit dashboard** reads
  right; `higher_better=False` reverses the bands for churn/latency. The dashboard bar `scorecard`/
  `meter_bar` can't give.
- **`deckkit.range_bars`** — a 'football field' (floating min–max ranges per row on a shared `axis_scale`
  + optional base-case tick); closes form-selection's recipe-only note.
- Wired end-to-end from a 4-lane self-check (integration · decision-taste · **agent-workflow cooperation**
  · correctness): a Composition + Range row in the Concept→Visualization dictionary (§3), a
  'stacked chart that misleads' anti-pattern (100%-hides-collapsing-total · negative segments · spaghetti)
  in `data-viz.md` + critic hooks in `review-rubrics.md`/`critic.md`, a single-highlight **carve-out** so a
  correct stacked chart isn't flagged, and roster/catalogue entries (`form-selection.md`, `data-viz.md`,
  `design-gallery.md`, `SKILL.md`). Correctness fixes: range_bars includes base-case points in its axis;
  bullet_graph sorts bands; smoke test added.

### Added — choropleth map (value per country / province)
- **`deckkit.choropleth(slide, x, y, w, h, data, mapname)`** + **`scripts/maps.py`** — the high-payoff
  form the skill was missing: shade a real map by a value per region. `mapname` = `europe` · `world` ·
  `china` (provinces). Built on **public-domain geometry** (Natural Earth 110m countries · DataV China
  provinces — nothing fabricated), rendered with matplotlib (no geopandas): Albers equal-area conic for a
  region, equirectangular for the world; light→`accent` ramp (or `scale='div'`); neutral no-data fill;
  thin borders. Key `data` by ISO-3166 alpha-2/alpha-3 or English name (countries), or province name/adcode
  (china); the Natural Earth `ISO_A2 = -99` quirk is patched (France/Norway…) and unmatched keys are
  reported, not dropped.
- The map PNG is **language-agnostic**; the title + gradient legend are **native deckkit text**, so units
  and titles render in any language (CJK included) instead of matplotlib tofu. Geometry is fetched once and
  cached like icons (network only on first use; `SLIDE_MAKER_CACHE` override).
- Hardened by a 3-lane self-check (code-alignment · decision-taste · adversarial correctness): `scale='div'`
  is **zero-centred** (neutral == 0, distinct poles via `accent2`) and the native legend now renders the
  diverging ramp with a 0 tick so **legend and map agree**; NaN/None values are treated as no-data (no
  crash); the unmatched-key notice reports the **actual** bad keys; China's **nine-dash line** renders as a
  visible dashed element. Decision-taste wired everywhere the model looks: a **Geography/"where"** row in the
  Concept→Visualization dictionary (`design-intelligence-addendum.md` §3 + `form-selection.md`), a
  **counts-not-rates** anti-pattern in `data-viz.md` + a named critic check in `review-rubrics.md`, and the
  "shade a rate, blank = no data" guidance in the docstring. Smoke covers projection, region matching
  (incl. the -99 patch), NaN, div, and a real render.

### Security — hardening pass (public-skill audit)
- **SVG icon rasterizer no longer executes untrusted content (was the one real vuln).** `icon_png()`
  accepts a local `.svg`, and when `cairosvg`/`rsvg-convert` are absent the headless-Chrome fallback
  used to render it with JS + `file://` access — an attacker-supplied icon could read local files
  (exfiltrated into the deck) or run JS/SSRF. Fixed with `sanitize_svg()` (a backend-agnostic control
  run before every rasterizer): strips `<script>`/`<foreignObject>`/`<iframe>`/`<image>`/`<audio>`/
  `<video>`/`<set>`/`<animate>` (incl. namespaced forms), `on*` handlers, any non-internal
  `href`/`xlink:href`/`src`, and external `url(...)` — while preserving paths, `<use href="#..">`, and
  the gradient refs recolor injects. Chrome also runs `--disable-remote-fonts`. Comments are stripped
  first (no comment-split reassembly), and the input is size/complexity-bounded (>100KB or >600 elements
  is refused in ~1ms) so the sanitizer itself can't be turned into a quadratic-time DoS. Verified across
  all 13 icon libraries: real icons (flat + gradient + duotone) still render; a 16-payload adversarial
  battery is fully neutralized; a ReDoS regression test guards the bound (`smoke_deckkit.py`).
- **Icon `name` is validated** (`fetch_svg`) as a strict slug (`[A-Za-z0-9._-]`, no `..`), closing a
  path-traversal into the icon cache and a CDN-URL traversal to arbitrary jsDelivr/npm packages.
- **LibreOffice render is now time-bounded** (`render_deck.py`, `timeout=300`) so a malformed/hostile
  `.pptx` can't hang the pipeline — matching the timeouts every other soffice/ffmpeg call already had.

## [3.5.0] - 2026-07-20

### Added — connectors dock on block edges (arrows never emerge from a block's centre)
- **`edge_point(rect, toward)`** — the point where a line aimed at `toward` crosses a block's
  boundary; the primitive behind edge-docked arrows (optional `inset` for a standoff).
- **`connect_boxes(a, b)` / `hub_spokes(hub, spokes)`** — connectors that dock on the facing EDGES
  of two block rects, so BOTH ends land on a boundary and nothing crosses a block's own label. The
  ergonomic replacement for hand-computing a centre point (the `hub_spokes` fan is exactly the
  "one Gateway, everything connects to it" topology shape).
- **`CONNECTOR_IN_BOX` build-time lint** — flags an arrow/line endpoint sitting in a block's central
  zone AND drawn above that block (so the stroke shows crossing the interior). Central-zone + z-order
  test keeps it false-positive-free: edge-docked ends, chart grid/axis lines, and the covered pattern
  (connector added before the node) never trip it. New `smoke_deckkit.py` case
  ("lint_layout CONNECTOR_IN_BOX") locks in the behaviour. Wired into `slide-design.md` (diagram
  self-verify), `design-gallery.md` (diagram crib), and `troubleshooting-faq.md` (§4).

### Added — overflow-proof components (by construction, not by lint)
- **`meter_bar`** measures the value label's real width, clamps the value box to it, and shortens
  the BAR when the footprint would leave the canvas (printed note; impossible fits raise) — the
  recurring right-edge `OFF_CANVAS` bug is now unrepresentable.
- **`scorecard`** measures the caption's wrapped height (instead of assuming 0.40in) and adapts —
  value shrinks first, then the caption steps down to an 8.5pt floor — so captions no longer run
  past the card bottom.
- **`insight_banner`** measures its body: a too-long body drops one size step, then the bar GROWS
  to hold it — text never escapes the shape.
- **`stat_row`** never wraps a figure mid-number (over-wide figures scale down, floor 15pt),
  measures caption heights, and returns the real bottom y.
- All four are **byte-identical on fitting calls** — only an overflowing call is adjusted; the four
  real-world failure shapes from this week's decks are now a permanent smoke-test case
  (`smoke_deckkit.py` "overflow-proof components"), verified clean at build-time AND render-time lint.

### Added — free-win deliverables & speed (multi-platform: identical on Claude Code / Codex / Windows)
- **PDF as a first-class deliverable** — the render pipeline already produces a PDF as its first
  step; `render_deck.py` now parks it beside the `.pptx` (`<deck>.pdf`) instead of burying it in
  `render/` — submission/email/print-ready at zero extra cost.
- **`viewer.html`** — a self-contained, zero-dependency flip-through preview generated on every
  render and **parked at the deck root beside the `.pptx`/`.pdf`** (not buried in `render/`; it
  references the PNGs through the `render/` subdir): one `file://` link, any browser, any OS (arrow
  keys / click / thumbnail rail / fullscreen). The fastest way to eyeball a deck without opening PowerPoint.
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
