# File inventory

## Files — scripts · agents · references · registry

**Tests** (`tests/`, script-style — `main()` + explicit exit, so `pytest` collects NOTHING from
them; CI invokes each directly and asserts it RAN rather than merely exited 0):
`test_lint_regressions.py` (two-sided: lint catches real defects AND leaves declared craft alone) ·
`test_codex_delivery_gate.py` · `test_codex_visual_contract.py` (Codex gate behaviour) ·
`test_critic_waiver_gate.py` (the shared-path critic waiver must be CLASSIFIED — a free-text
waiver once carried a whole deck through `all hand-off gates pass` with no independent critic) ·
`lint_fixture.py` (shared fixture, not a suite).

**Scripts** (`scripts/`):
- `deckkit.py` — the build helpers (template & blank decks), **incl. the editable native charts**
  (`native_chart`/`native_dual_axis`/`native_donut`/`native_pareto`/`native_bubble` — click-to-edit,
  any-language-safe) **and the build-time geometry gate** (`lint_layout(prs, strict=True)` — run before `prs.save()`;
  the in-process pre-render net for overflow/off-canvas/text-overlap/card-escape/footer/off-centre — plus
  `fit_text_size`); the build's source of truth. Full signatures in its docstrings.
- `component_audit.py` — did this deck hand-roll a form the library already implements? Reads the
  build script (every import form: `dk.x()`, an alias, or `from deckkit import x`) + the finished
  pptx (geometry signatures: bar rows, abutting 100% bands, tile rows, marker rows) and names the
  component whose guarantee the hand-roll gave up. **Advisory, never a blocker** — a bespoke
  composition is the signature move; what the tool states as fact is the usage ratio and the specific
  match. Reporting is suppressed when the deck draws with a FORM component that emits the same
  geometry (a component's own output must never be reported as a hand-roll); that set is **derived
  from deckkit's source and intersected with the form catalogue** — it has been wrong twice as a
  hand-kept list, and a primitive in it would silence the tool forever. Exits 1 and prints
  `NOT CHECKED` rather than reporting clean when the deck could not be opened. ~50ms. Run it at
  PRE-FLIGHT 12.
- `check_param_reach.py` — AST pass asserting every keyword parameter a public helper ACCEPTS is
  READ by its own body. Found ten, seven of them unknown: `node(fill=)` drew white whatever you
  passed, `backdrop_motif(kind=)` always drew the grid its docstring said was one of two modes,
  `native_bubble(xlabel=/ylabel=)` dropped documented axis titles, `slide_transition(kind=)`
  turned every transition into a fade. Deliberate no-ops go in `EXPECTED_UNREAD` with a reason.
- `check_reference_code.py` — resolves every `deckkit.*` call TAUGHT IN THE SKILL'S PROSE against
  the real module: unknown helper, bad keyword, dead `references/*.md` pointer, and the silent
  `.fore_color.alpha = ...` no-op (python-pptx solid fills cannot carry alpha, so that assignment
  raises nothing and renders a 100% OPAQUE shape). Exists because four wrong API facts shipped at
  once in the shared references and nothing reported any of them — the build crashes at the
  reader's desk, not in CI. Exit 0 clean / 1 findings / 2 could not run. Runs in CI.
- `check_design_contracts.py` — the DESIGN stack's index guard: every self-verify cross-reference in
  the tree resolves to a real item, the `### Design self-verify (a–r)` header covers every item the
  list actually defines (and its spelled-out count matches), the shared design thresholds agree
  across every file that states them (the ~40–50% form-family band, the two-consecutive-card rule),
  `references/checkpoint-convention.md` carries every line SKILL.md says it OWNS, and every
  `DESIGN_FIELDS` entry the hand-off gate requires is named in SKILL.md. Exists because an audit
  found the design pipeline's rules sound and its *indexes* rotted: the header said "(a–q)" while
  the list ran to (r) — and (r) is the density line, the one self-verify item with a hard gate
  behind it. These are agreements BETWEEN files, invisible to reading and decidable by a program.
  `--selftest` proves each check can still fail. Exit 0 clean / 1 drift / 2 could not run. Runs in CI.
- `codex_delivery_gate.py` — **Codex-only** post-lint evidence gate. It verifies a v2 evidence chain:
  final PPTX/build hashes, source and claim ledger, direction/signature artifacts, per-slide component
  and icon provenance, plus two schema-valid focused critic reviews. It does **not** alter Claude Code's
  pipeline or `component_audit.py`'s advisory classification. With `--receipt`, it writes a
  final-PPTX-bound PASS receipt only after the full gate succeeds.
- `codex_handoff_guard.py` — **Codex-only** final hand-off check. It re-hashes the PPTX against the
  PASS receipt from `codex_delivery_gate.py`; a missing, invalid, or stale receipt blocks a
  Codex-verified file hand-off.
- `codex_visual_contract.py` — **Codex-only** per-slide visual contract: local overlap and
  icon-semantic drift, checked against the evidence record. Paired with `codex_delivery_gate.py`;
  neither runs on the shared (Claude Code / Kimi) path.
- `directions_diversity.py` — mechanical divergence check for direction-gate candidates
  (mode · palette distance · type pairing · composition), flagging any pair that matches on ≥3 of 4
  axes. Exit 0 all diverge / 2 flagged / 1 unreadable. Never auto-kills: a flag means REDIVERGE **or**
  record a named justification on the `direction gate:` line. Run it before posting the preview link.
- `preflight_check.py` — decides the MECHANICAL half of PRE-FLIGHT (items 1, 2, 3b, 4, 7, 8, 10)
  and prints 5/6/6b/9/11 as still-yours rather than implying it covered them. Items 2, 7 and 10
  are advisory, not failures: they depend on facts the file does not carry. Catches the defect
  class nothing else does: `placeholder`/`TODO`/`(editable native chart)`/unfilled `<slot>` text
  shipped on a slide. `--build <script>` adds the `build:`-docstring vs `Build.step` diff.
  Exit 0 clean / 1 findings / 2 `NOT CHECKED`. Run it at the top of PRE-FLIGHT.
- `render_deck.py` — pptx → one PNG per slide (verify + critic loop). **`--slides N[,M]` renders ONLY
  the named 1-indexed pages** — the Step-4 SIGNATURE PROOF and any "re-render just the page I edited"
  loop; byte-identical to those pages from a full render, and it deliberately leaves NO cache (a cache
  would claim every page is current). Mutually exclusive with `--fast` (which chooses the set for you)
  and with `--deliverables` (which needs the whole deck). **`--fast` re-renders only the
  slides whose content changed since the last run** (per-slide fingerprint + deck-global digest,
  cached in `render/.render-cache.json`; subsets the pptx, output byte-identical to a full render,
  auto-falls-back to full whenever the page mapping could be wrong) — on an 18-slide deck, ~2.8s →
  ~2.3s for a one-slide edit (both start LibreOffice once, and that ~2.5s start is the floor), and
  0.07s when nothing changed, which is the real win because it starts LibreOffice not at all.
  **`--deliverables` (alias
  `--final`) additionally parks the PDF beside the pptx and writes `viewer.html`, a zero-dependency
  flip-through preview** — off by default, so an in-progress deck never accumulates stale copies;
  run it at hand-off once the user confirms the deck is final (PNGs always stay in `render/`); finds LibreOffice cross-platform
  or set `SOFFICE` (`.sh` is a shim). `check_env.py` — preflight if a render fails. `inspect_template.py`
  — a template's layouts/placeholders/logos. `requirements.txt` / `install_skill.py` — deps / installer.
- **`sigs.py`** — one lookup, many helpers: exact signature + docstring head for every named deckkit/designed_charts helper, plus the run-tuple and RGBColor call-shape contracts. `--search TERM` to find one, `--list` for all, `--full` for whole docstrings. Use it BEFORE writing a build script; reading deckkit.py one function at a time costs a round-trip per question.
- `lint_deck.py` — deterministic **render-time** layout lint and complement to deckkit's build-time
  `lint_layout`: re-checks geometry on the final file (off-slide overflow · block/image collision
  [containment excluded] · footer-zone intrusion · text-past-card · uneven rows) AND adds the
  render/parse-only faults (CJK kinsoku/widow · whole-page-image · orphan slides — plus missing EA font as the render-time BACKSTOP; `lint_layout` now catches it at build time as `CJK_NO_EA`, whose fix is `deckkit.retrofit_ea(prs)` on the line above the lint — setting `EAFONT` fixes the next build, not this one);
  run after render, before critic; non-zero on findings. `smoke_deckkit.py` — regression guard for the helpers.
- **Delivery-mode flags — the same word does NOT reach every tool.** SKILL.md names each flag at the
  step that uses it; this is the complete map of which tool actually accepts which, because the
  tools diverge and getting it wrong is quiet, not loud. Verified against the parsers, not the prose:
  - `lint_deck.py` — `--selfread` · `--briefing` · `--textheavy` · `--surface` · `--static`
    (each also spelled `--mode=NAME`), plus `--renders <dir>` · `--gates <.deck-gates.json>` ·
    `--json <out>`. This is the only tool that implements **all five** modes.
  - `render_deck.py` — `--slides N[,M]` · `--fast` · `--deliverables`/`--final` · `--gate-check` ·
    `--selfread` · `--textheavy` · `--surface`. The output dir is **positional**, not `--outdir`
    (`--headless`/`--convert-to`/`--outdir` in this file are the LibreOffice command line it emits,
    not options it takes). 🔴 **It has no `briefing` floor** — `_KNOWN_DELIVERY` is
    `presented|textheavy|selfread|surface` — so a briefing deck's hand-off gate runs at the
    `presented` word budget unless `.deck-gates.json` records a `delivery` it recognises; passing
    `--briefing` now exits with that explanation instead of silently absorbing it. `--static` is
    accepted and deliberately **inert**: this tool already lints with `static_ok=True`, so NO BUILDS
    cannot fire from it — it is consumed only so callers can pass it by symmetry with the lint.
    Any flag this tool does not take used to resolve to the OUTPUT DIRECTORY and run the gate at the
    `presented` floor in silence; it now exits with the accepted list.
  - `preflight_check.py` — `--build <script>` · `--selfread` · `--static` only. No `--briefing`,
    `--textheavy` or `--surface`.
  - `validate_review.py` — `--record` (Step 5 writes the reviewed run to the record with it) ·
    `--selftest` (the CI contract check).
- `plan_wordcount.py` — advisory per-slide word-budget pass over the Content plan's table (the Step-1
  comprehension-gate check; write the table to a scratch path, never the deliverable folder).
  `validate_review.py` — stdlib schema validator for critic/arbiter JSON (`critic|arbiter <file|->`;
  Step 5 runs it before acting on any review).
- `slide_index.py` — `slide N -> file:line function` + each slide's plan-row docstring, for one
  build script or a set of section modules. Run it at the top of the Step-5 fix loop on any
  fanned-out deck: section fan-out means the coordinator did NOT write the code, so a finding on
  slide 7 otherwise begins with grepping modules it has never read (measured: 33 round-trips /
  ~30,000 output tokens / ~9 min on one build, re-deriving a map the authors already had). Prefers
  an explicit `SLIDES` registry, falls back to source order; names any module it could not import
  instead of failing the run, because a partial map still beats grepping.
- `dispatch_brief.py` — write the deck brief ONCE, point every dispatch at it. `init --deck <dir>`
  creates the skeleton (in a scratch path, never the deck folder); `check --brief <p>` gates that
  every required section is filled; `prompt --brief <p> --role critic|section|planner|design
  [--lens A|B] [--round N] [--section N --slides a-b]` prints the dispatch prompt. Exists because
  nine dispatches on one measured build cost 41,203 output tokens (~12.5 min) at ~4,600 each, and
  almost all of it was the same interview answers, paths, cap and CONTRACT CARD retyped nine times;
  the generated prompt is ~220 tokens. Second reason: it makes the contract card ONE artifact
  instead of nine reconstructions. Refuses to emit a prompt while the brief has unfilled sections.
- `roundtrip_budget.py` — measures the build's actual cost from the session transcript: round-trips,
  the batching ratio (tool calls per round-trip), median context re-sent, and whether the render
  self-check read the slide PNGs in one message or one at a time. Step 6 runs it to fill the
  hand-off `cost:` line with a measured number (`--slides <N>`, `--json` for machine use). It is the
  backstop for the batching rules in the preamble and Step 5, which are otherwise prose that fails
  silently — a run can cost 4x its budget while every lint passes and the critic consents. Reports
  only; it never fails a build.
- `anim.py` — PowerPoint click-builds/transitions (pair `references/animation.md`).
- `formats.py` — named canvas-format registry (16:9 default · 4:3 · square 1:1 · 小红书 3:4 · story
  9:16 · A4 print): dimensions, platform safe zones, chrome policy, density + lint flags, and the
  `band()` safe-rect helper; opt-in — the 16:9 default never touches it (pair `references/canvas-formats.md`).
- `designed_charts.py` — raster matplotlib chart recipes (dumbbell, slope, dual_axis, bubble_trend,
  pareto, donut_kpi, **waterfall** — for a chart type with no native equivalent or a deliberate look;
  prefer deckkit's native charts; `references/data-viz.md`). `maps.py` — **choropleth base maps**
  (europe · world · china provinces) from public-domain geometry, value-shaded → PNG placed by
  `deckkit.choropleth()` (which adds the native title + legend); `references/data-viz.md`. `presets.py` — named
  design-language presets (glassmorphism · swiss · editorial_paper · editorial_report · risograph ·
  memphis · brutalist · blueprint · ink_wash · eastern_traditional · **consulting** (MBB action-title) ·
  **dark_tech** (engineering dark + diagram-island) · **luxury_dark** · **museum_memorial** ·
  **bauhaus** · **midcentury** · **terminal** · **synthwave** — **18 total**; ink_wash/
  eastern_traditional → `references/east-asian-aesthetic.md`; the full style+component catalogue →
  `references/design-gallery.md`).
- `image_prompts.py` (build the prompt manifest) → `generate_images_codex.py` (no-key, Codex CLI) /
  `generate_images_openai.py` (**metered** API path — gated, see the BILLING GATE). `archetypes_html.py` (direction-gate previews as
  **one HTML link** — `preset_directions([names])` turns best-fit preset names into direction tokens
  carrying each preset's real DNA, so the options are STYLES not colour schemes (accepts a **dict** in
  the list for the no-image-tool gate's 4th pure colour-scheme direction); `_dna_cover` renders each
  preset's signature hero motif and `_dna_ambient` runs the quiet register signature on EVERY interior
  preview slide so the style carries all pages, not just the cover; `archetypes.py` is the older
  pptx-render variant + the post-pick one-slide fidelity confirm) · `assemble.py` (assemble a sectioned deck) · `export_notes.py` (notes →
  rehearsal script).
- `icons.py` — fetch an open-licensed SVG icon (Tabler/Lucide/Phosphor incl. **6 weights + duotone**/
  Simple…), recolor OR **gradient-fill** to the deck palette, rasterize to a transparent PNG
  (`icon_png(spec, out, color=…, gradient=(c0,c1), px)`); pair with the deckkit container helpers
  `icon` / `icon_tile` (solid/gradient/glass tile) / `icon_badge` (ring) / `icon_ghost` (watermark) /
  `icon_card`. See `references/icons.md` ("Treatments").
- `image_fx.py` — `duotone(img, ink_a, ink_b)` / `grayscale(img)` — preprocess a colour photo to the
  deck's ink so it doesn't fight the accent (riso/brutalist/ink/luxury/museum). See `design-gallery.md`.
- `palette_audit.py` — resolve a palette into FILL-only vs TEXT-safe tokens ONCE, before the build,
  with the darkened twin per ground (`--inks`/`--grounds`, or `--from-style <deck>/style.py`). The
  two-token rule already exists in SKILL.md and is still easy to break because the check is
  per-PAIR and a build touches dozens; `render_deck.py --gate-check` therefore requires the
  resolved split as `design_plan.palette`.
- `trace_composed.py` — split a built deck's shipped lines into SOURCE-QUOTED vs AUTHOR-COMPOSED
  against the source files (`--source a.md,b.md`), so a content review aims at the composed set
  instead of re-reading every page. Deliberately NOT a fabrication detector (that version was
  measured at ~8% precision and dropped); Latin identifiers and numbers get an exact test instead,
  which is precise. Run it before dispatching the content critic and hand it the composed list.
- `extract_pdf.py` (crop a figure from a PDF — `figures`/`figure`/`autofig` auto-detect, `tables`
  for structured table data with an explicit shortfall report, `page`/`crop`
  manual; **plus the long-source trio `map` (TOC + CJK-aware word-density skeleton), `text` (page-range
  dump for chunked reading), and `headings` (reconstruct a skeleton for a no-TOC book)** — the tooling
  for the content-planner's long-source mode) · `crop_helper.py`
  (crop/trim/panel **by looking, not guessing**) · `extract_deck.py` (pull content out of an existing
  deck — the redesign path) · `ingest.py` (ingest a NON-PDF source — `doctext`/`office` for Word/Office,
  `frames` for a video's visual track, `probe` to route — with the vision/audio fidelity floor).
**Agents** (`agents/`): `content-planner.md` (Step-1 CONTENT deep-understand + claim ledger + per-slide message; the content checkpoint) · `slide-design.md` (the art director — Step-2 design language + per-slide form/layout/rhythm + icons + appear-animation + the Form ledger; the design checkpoint) · `critic.md` (independent critic brief — the two review lenses + JSON schema) · `arbiter.md` (high-stakes finding cross-validation + fix-verification; no-op low-stakes) · `asset-prep.md` (execution-only asset materializer — crops/equations/plates/icons after the design plan is approved; zero design decisions) · `openai.yaml` (Codex display metadata).

**References** (`references/`, loaded on demand): `auto-delegation-quality-gates.md` (**auto mode rigor enforcement** — "decide yourself" means "you choose", not "skip steps"; checkpoint protocol, image legibility floors, component discipline, critic requirement) · `canvas-formats.md` (per-surface layout DNA for the non-16:9 formats — square/rednote/story/A4 — + the repurpose/batch pattern; pairs `scripts/formats.py`) · `design-principles.md` (the craft / the "why"; incl. the **C.R.A.P. framework** — Contrast · Repetition · Alignment · Proximity) · `design-gallery.md` (style+component catalogue mined from 21 pro decks — pick a preset, reach for the right component) · `semantic-color-contract.md` (bind a hue to a concept deck-wide) · `review-rubrics.md` (universal + per-purpose review criteria) · `design-by-purpose.md` (per-purpose look for "design a clean one") · `form-selection.md` (**content-shape → candidate FORMS** — the single design-decision map; generate a set, pick deliberately) · `schematic-diagrams.md` (**HOW to draw a labelled SCIENCE schematic** — force/ray/circuit/apparatus/vector/wave; matplotlib/domain-lib recipes for precise/label-critical ones, OR the image tool for complex/stylized/template-matched ones with labels overlaid native; + the domain-accuracy fidelity gate) · `data-viz.md` (pick the chart type; editable-native vs raster) · `image-generation.md` (when/how; topical, text-free, consistently placed; **TEXT LEGIBILITY floor — scrim required for all text-over-image**) · `icons.md` (one coherent open-licensed icon family, recolored, restrained) · `generated-template.md` (Q1's image-tool template branch) · `style-analysis.md` (mimic a style example, Q4) · `font-guidance.md` (portable fonts, tofu recovery) · `multilingual.md` (non-Latin / CJK / RTL) · `east-asian-aesthetic.md` (Chinese ink / traditional looks — paper · seal · CJK numerals · `ink_wash`/`eastern_traditional`) · `animation.md` (when/why + `anim.py`) · `large-deck-orchestration.md` (section fan-out; default is single-author) · `collaborative-mode.md` (direction→outline→draft gates) · `redesign-existing-deck.md` (diagnose-then-rebuild) · `handoff-and-iteration.md` (delivery + iterate without clobbering edits) · `design-intelligence-addendum.md` (the deck-level design gates Step 2 measures against — rhythm map · block-dependency audit · Concept→Visualization table · semantic-colour ledger · variation floors) · `troubleshooting-faq.md` (**symptom → cause → fix for every error surface** — env · build exceptions · both lints · render · images · CJK — plus the FAQ; consult on any failure, and report findings to the user in its plain-language form) · `user-taste.md` (the registry-root `taste.md` — schema · read protocol · dial-ledger promotion + consented-look write-back) · `examples/` (`build_example_generic.py`, `style_example.py`, `section_example.py`).

`codex-runtime.md` is the **Codex-only** execution adapter: visible design proof, typography/icon/component evidence, and a focused critic-pair gate. It never changes Claude Code's workflow.

**Registry** (NOT part of the skill): `~/.codex/slide-templates/` (Codex) · `~/.claude/slide-templates/` (Claude Code) — the user's saved templates, **plus `taste.md` at the root** (the portable taste profile — schema + read/write protocol in `references/user-taste.md`); read for choices, write new `profile.md`s to the active host — a freshly-designed look saved at hand-off carries the vetted critic `strengths` distilled into its profile's Notes. Empty for a new user (no templates, no `taste.md` — silently skipped; no write until the first durable signal).
| `scripts/contact_sheet.py` | Montage every `slideNN.png` onto ONE image so a critic can survey a whole deck in a single look, then open individual slides at full size only where needed. Narrows the COST of a review round, never its scope. |
