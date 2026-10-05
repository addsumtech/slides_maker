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
  (motif: `register_mark` 11 quiet kinds · `motif_page` 8 loud relations · `motif_legend` the key ·
  `tag_motif` / `bleed_intent` the two declarations)
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
- `check_style_applied.py` — the register a deck DECLARES must be the one it APPLIES. Both
  delivery gates required `style_pick` as a string and verified it in neither: measured by
  grep, `presets.apply` / `set_geometry` / `set_ground` appeared in no gate script at all, so a
  deck recording `"brutalist for engineering - beat blueprint"` and built with deckkit's stock
  defaults passed on BOTH runtimes. AST-checks the build script for `presets.apply("<the
  declared preset>")`; `bespoke` / `generated` / `n/a — <locked look>` are skipped by
  definition, a deliberate departure is `style_pick_waived` (>=24 chars). Imported by
  `render_deck.py --gate-check` and `codex_delivery_gate.py` — never copied, so the two paths
  cannot grow two answers. `--selftest` proves it both ways. It checks the CALL, not the
  pixels; `tests/test_register_expression.py` covers the other half.
- `palette_audit.py` — also SIMULATES colour vision deficiency (Viénot–Brettel–Mollon, in LMS)
  and names any pair that stops being two colours. `dk.OKABE_ITO` had been recommended for years
  with nothing checking a palette, so the advice only helped whoever already remembered it. The
  bar is ABSOLUTE distance after simulation, not how much the pair changed: Okabe-Ito's worst
  red-green pair lands at 68 and the classic matplotlib red/green at 56, and any *ratio* cut sits
  in a 6-point gap that would flag the set this skill recommends. Deuteranopia/protanopia (~8% of
  men) and tritanopia (rarer than 1 in 10,000) are reported separately — Okabe-Ito itself collides
  under tritanopia, and a check that called it unsafe would train people to dismiss it. The
  simulation runs in LMS on purpose: the first version used the widely-copied RGB-space matrices
  and turned pure green PINK-GREY under deuteranopia while leaving greys correct, which looks fine
  until you check it against a reference.
- `lint_deck.A11Y_CODES` / `A11Y_BLOCKING` — the accessibility codes this file already computed
  and printed as advisory `[warn]`s. Measured by grep before the split existed, no gate on the
  shared path read any of them and the codex path held only the two WCAG contrast codes, so the
  same deck was accessible or not depending on which runtime shipped it. `A11Y_BLOCKING` is what a
  gate may hold a deck on and deliberately EXCLUDES `NO SLIDE TITLE`: lint's own message for it
  calls an off-canvas title "a sanctioned trick for statement slides", and on an ordinary
  well-built 11-slide deck it fired once, on the closing slide. Both `render_deck.py --gate-check`
  (`a11y` section) and `codex_delivery_gate.py` (`STRICT_WARNINGS`) derive from these constants
  rather than restating them.
- `deckkit._motif_faults` — the DECODABILITY checks, all three added after a first human reader
  asked three questions about a deck that had passed every gate. `MOTIF_UNEXPLAINED_AT_FIRST_USE`:
  the stranger test is about FIRST appearance, and the old check cleared on a legend ANYWHERE —
  which is precisely the deferred reading SKILL.md calls "a FAILED test written as a passing
  sentence". `UNNAMED_REPEATED_MARK`: >=4 near-identical marks on one page with no text within
  reach of the group; such a set was invisible to every other check (not text, so the text checks
  skip it; not tagged, so the motif checks skip it; trivially clears contrast and overlap), and
  nine unlabelled rules shipped on a cover. Both are WARN, like their siblings — the figurative
  answer is legitimate — but they now READ, and `tests/test_decodability.py` locks both directions.
- `render_deck._icon_none_category_holds` — the icon waiver's CATEGORY, verified against the built
  file. The four classes were compared to a list of strings, so any of the four words cleared the
  gate: measured, `motif-dominant` was accepted on a deck carrying no loud motif, and the first
  reader's first note was that icons should be there. Now `motif-dominant` requires a real loud
  motif, `tiny-deck` a deck of 1-2 slides, `template-locked` a real template (python-pptx ships
  eleven named layouts, so "has layout names" proved nothing), and `editorial-register` stays
  declared because it is a taste claim about a look and inventing a measurement would be worse.
  The waiver must also name EVERY flagged slide — naming a subset let the re-decision cover the
  page the author had already thought about and skip the ones they had not.
- `plan_rhythm.py` — composes the deck's ARCHITECTURE as a sequence before any page is built.
  `lint_deck` demands >=4 distinct skeletons and reports 3 adjacent slides sharing 75% of their
  structure, but both fire AFTER the build, when varying the architecture means re-laying written
  pages — so it got decided one page at a time, in the order the content arrived. Maps each slide's
  ROLE to the architectures that suit it (a result is a thing to look at, a comparison is a set to
  scan, a process is stages in order), rotates when a role's picks are already in the last two
  pages, and pushes `carried_by` slides toward architectures that can hold a signature move.
  Deterministic arithmetic — ~40ms, no model call, no round-trip. Measured: the same content
  planned scored 8 distinct skeletons against 2 improvised. `--selftest`; a PROPOSAL, not a verdict.
- `composition_cues.py` — what a rendered page LOOKS like, as the seven cues an unsupervised
  slide-quality study validated against human ratings (arXiv 2508.19289: whitespace, colorfulness,
  edge density, brightness contrast, text density, colour harmony, layout balance; r ~= 0.83,
  beating several commercial vision models). Three of them were computed nowhere here. 🔴 REPORTED,
  NEVER GATED, deliberately: a number that tracks taste across a corpus does not license a threshold
  on ONE deck — a quiet ink-wash register and a cluttered mess share a low colorfulness, and this
  skill protects the first. Its real output is the deck-wide RANGE per cue, because a FLAT range is
  the signal a single page's number cannot give: measured, a deliberately dead deck that linted
  clean reported 6 of 7 cues flat. Reads renders already on disk — no extra render pass, ~0.6s for
  14 pages. Whitespace is measured against the MODAL tone, so a dark register reads as mostly empty
  rather than 100% full.
- `check_direction_applied.py` — the direction the user PICKED must be the deck that shipped.
  Four directions are rendered, one is clicked, and the choice was recorded as a sentence and
  compared to nothing. Measured on a delivered deck: the chosen direction declared a Georgia
  display face and a centred cover, and the deck shipped Helvetica Neue titles and a low-left
  cover, because `style.py` set `display=` and every title passed `dk.FONT` — the DISPLAY slot was
  never read. The author noticed; no gate did, while `check_register_pixels` and
  `check_style_applied` already existed for the identical class. It compares only what a file can
  settle — ground, accent presence, display and body faces, and `centred` vs `low-left` — and names
  skeleton and motif as NOT checked rather than guessing. A deviation is legitimate and recorded
  per axis in `design_plan.direction_deviations`; an unrecorded one is the version the user cannot
  see. Run by both gate paths from one module.
- `register_surface.py` — the half `presets.apply()` never had. apply() calls four things
  (`set_palette`, `set_geometry`, `set_ground`, the font setters), so one identical page through all
  18 presets RENDERED as 18 colourways of one page: no memphis bands, no bauhaus primitive, no
  glass, no overprint, no scanlines. Each preset's `surface` field described all of that correctly,
  in prose, for an author to build by hand — which is why it was never built. A kit is three things:
  `ground()` paints the register's furniture and RETURNS the content rect left over, `card()` gives
  its card FORM (the half that makes the pages differ in shape rather than colour), and the marks
  (`halftone` · `starburst` · `boomerang` · `zigzag` · `tri` · `scanlines` · `color_band`) are
  public so a bespoke register can borrow one. The rect it returns is a CONTRACT with teeth: a kit
  that paints a loud mark inside it raises — the first render put a memphis triangle through a card
  corner and a bauhaus disc through a third card while the docstring promised it could not happen.
  Placement varies by page INDEX, never by a random number, so two builds of a deck stay identical.
  All 18 registers have a kit; an unknown name raises rather than quietly returning a plain page,
  and so does painting a surface before `presets.apply()` has set the palette (it used to die on a
  blend deep inside a builder, with a TypeError that named nothing the caller could fix). Both gates NOTE a deck that declared a kitted register and used
  none of it.
- `register_surface.load_kits(dir)` — imports a deck's own `surface_*.py` kits so its INVENTED
  registers exist in THIS process. Registration happens at import time and the gates run in a fresh
  process after the build, so without it a bespoke register's declared prohibitions were enforced
  in-process and nowhere else: measured with a scaffolded kit forbidding gradients and a deck
  drawing one, the real gate reported "a bespoke look has no FORBIDS to check". Never raises — a
  kit that fails to import becomes a gate NOTE naming it, because "unregistered" and "clean" are
  different facts.
- `bespoke_kits.py` — the four registers in `references/bespoke-registers.md`, as runnable kits.
  The library taught how to invent a register in five prose fields and contained zero lines of code,
  so every deck that reached for one re-derived the contracts by hand and got a different subset
  right. Registered through `register_surface.register()`, they arrive with everything a preset's
  kit has. A motif that NEEDS distinct hues derives them rather than reusing the base palette's one
  accent — measured: on `swiss` (a single red) `current`'s two-colour crossing rendered in one
  colour, which does not degrade the look, it deletes the idea.
- `save_register.py` — keeps an INVENTED register after the deck ships. The example library held
  4 while one real look history held 9 that had shipped and been lost, and grep found no script
  anywhere that wrote a register or a look-history line: the mechanism was "remember to edit the
  markdown", which is not one. Nothing is re-described — it reads the pick, palette, signature move
  and `motif_generates` from `.deck-gates.json` and adds the colours `check_register_pixels`
  measured on the render. Writes to the USER'S registry root beside `taste.md`, never into the
  skill's own `bespoke-registers.md`, which is a teaching library rather than one user's
  collection. Preset-based decks are skipped (they are in the gallery already). Idempotent on a
  NORMALISED name: the gates record carries the English pick and the look history the human-typed
  one, so `Section Drawing` and `Section Drawing 建筑剖面` are one register, not two — comparing
  strings kept both on the first run. A gloss must ANNOUNCE itself (the other script, or an
  annotation separator): plain containment made `Grid`/`Gridiron` and `Ledger`/`Ledger Line` the
  same register too, and the loser vanished under "already kept". Reading spans every registry
  root the way `taste_file()` and `list_templates()` do — the same person runs Claude Code on one
  deck and a Codex host on the next — while new entries go to one. Writes temp-then-replace,
  because truncating the user's design memory to add one line is not an acceptable worst case. `--from-history` recovers what a look history already names.
  `render_deck --gate-check` NOTES an unkept register at hand-off, never blocks: keeping one is the
  user's call about their own collection.
- `check_register_guard.py` — the SHAPE-level half of a declared register. `apply()` sets palette,
  geometry tokens and ground and nothing else, so measured, one page through all 18 presets came
  out differing only in ground, radius and rule weight — memphis with no header bands, bauhaus with
  no primitive. `check_style_applied` verifies the CALL and `check_register_pixels` says in its own
  docstring that it judges COLOUR only, so "declare brutalist, ship its palette on rounded cards"
  cleared every gate. Reads `presets.FORBIDS`: rounded · gradient · soft-shadow (shadow.inherit
  left True) · proportional-face · confetti (>1 oversized primitive). Only 7 of 18 registers
  declare prohibitions and only OOXML-readable properties are listed — a check that fired on lawful
  composition would teach the waive reflex, and the undecidable guards ("photography carries ALL
  the colour") stay prose and are REPORTED as unchecked. The register is resolved by
  `check_style_applied.declared_preset`, never a substring search: a bespoke deck whose pick read
  "beat blueprint-the-preset" was checked as `blueprint` on the first try.
- `check_talk_time.py` — does the deck fit the SLOT the interview asked for? The interview asks in
  both languages ("for a talk, give me the time budget and I will confirm the slide count") and,
  measured by grep before this file, nothing ever compared the built deck against the answer: no
  words per minute, no per-slide budget, nothing. Estimates the spoken length from the SPEAKER NOTES
  only (on-slide text is not spoken by a presenter following this skill's own rule) as a BAND —
  130-150 wpm for any word-delimited script (Cyrillic/Greek/Arabic/Devanagari included), 180-220
  CJK characters per minute, and Thai/Lao/Khmer NOT CHECKED by name because no sourced rate exists
  here and their token counts come from where the combining marks fall — and reports OVER THE SLOT (a block, with
  how many slides' worth to cut), TIGHT, UNDER THE SLOT and ONE SLIDE EATS THE TALK. No recorded
  budget, or notes on fewer than half the slides, is NOT CHECKED and says which: an estimate of a
  third of a talk dressed as a whole one is worse than none. Both gate paths; waivable in writing.
- `check_qa_backup.py` — the questions the author prepared for, against the deck they actually
  built. Reads `content.qa` (`[{"question": …, "slide": <the backup that answers it>}]`) and the
  BUILT file's real slide actions: `PREPARED BUT UNREACHABLE` (blocks — the answer exists and during
  questions it can only be reached by arrowing past everything in between, which is why prepared
  answers go unused), `NO SLIDE`, `NO QUESTION`, `MALFORMED`, and `NO WAY BACK` as a note. Measured
  before it existed: `hlinkClick` appeared only in `_EA_FOLLOWERS`, a constant listing XML
  element order, and `click_action` in no file at all, so this library could not make a deck jump — see `deckkit.link`/`agenda`/
  `back_link` and `references/navigation-and-qa.md`. Nothing recorded is NOT CHECKED: anticipating
  questions is a practice, not a law. Both gate paths; waivable in writing.
- `citations.py` — an academic deck's bibliography, as a source of truth rather than a retyped
  string. Parses BibTeX (brace-matched, so a `{DNA}`-braced title does not truncate; LaTeX accents
  resolved, and an accent the table does not know still yields its base letter), derives the in-text
  marker AND the reference line from the SAME entry (`numeric` / `author-year`, with `etal=`/`amp=`
  so a Chinese deck writes 等 and 与), and renders the page with `reference_page` — every DOI
  clickable, in the deck's own ink. 🔴 It REFUSES an entry with no author/title/year rather than
  printing `n.d.`: under the never-invent floor a plausible-looking citation is worse than a missing
  one. Measured before it existed: nothing in this skill read a bibliography, so every citation ever
  built was typed by hand. See `references/citations-and-bibliography.md`.
- `check_citations.py` — the markers on the slides, the reference list and the .bib must be the same
  three things. Reads `content.citations` (`bib` · `style` · `keys` in cited order) and the BUILT
  file: `DANGLING MARKER` (a `[7]` over a six-entry list — the leftover of a cut slide, and the one
  an audience member looks up), `NOT IN THE LIST`, `NO SUCH ENTRY`, `INCOMPLETE ENTRY`, and
  `UNCITED` as a note. Reads full-width CJK markers too, and resolves the .bib path INSIDE the deck
  folder — a record written by a build is not a licence to read anywhere on the machine. Nothing
  recorded is NOT CHECKED. Both gate paths; waivable in writing.
- `render_deck.py` also owns three hand-off behaviours worth knowing by name: the **COVERAGE
  ledger** (`[gates] COVERAGE: N ran — X bound, Y NOT CHECKED`, printed on every gate run, pass or
  fail, because the run that passes is the one nobody reads), the **PDF/UA export** (the plain
  `--convert-to pdf` produced a tagged PDF with zero `/Alt` values, so every image description
  stopped at the .pptx; the raster is byte-identical either way), and **`<deck>-notes.pdf`**, the
  speaker handout `--deliverables` writes when the deck has notes.
- `derive_template_contract.py` — writes a registered template's `## Machine-checkable contract`
  block FROM the template, never by retyping it. 🔴 Measured: 10 of the 11 registered templates had
  no contract, so `check_template_profile.py` could bind to none of them and a deck built from any
  was checked against its template's look by NOTHING — and those 10 ship a `style.py` and no .pptx,
  so they have neither layout names nor a canvas size for the existing fingerprint to use. It reads
  the palette out of the style module's own constants (three dialects — `RGBColor(0x..)`,
  `C("hex")`, bare `"hex"` — and semicolon-chained `dk.FONT = …; dk.MONO = …`, because real
  registered templates use all of them), falls back to the profile's backticked hex tokens, and
  LEAVES OUT what it cannot derive. It refuses a palette that is just deckkit's defaults (it would
  match every stock deck) and refuses to overwrite an existing contract without `--force`.
- `purposes.py` + `check_purpose.py` — a deck's GENRE declares content it is not finished without,
  checked against the built file on both gate paths. `references/design-by-purpose.md` carried nine
  purpose recipes and, measured by grep, NOTHING consumed it — so every per-purpose rule there was
  advisory by construction — and the four genres with the most rigid conventions were missing from
  the list entirely: grant proposal (aims · feasibility · risk), progress/guidance committee
  (progress · plan · ask), journal club (attribution · critique), clinical case
  (presentation · investigations · management · outcome), thesis defense (contributions ·
  limitations · future work), conference talk (contribution · evidence · limitations), job talk
  (track record · research plan · fit) and exec/investor readout (the ask · the number · the
  risk) — plus lab meeting (what changed · open questions), work status (outcome · the ask), product
  pitch (positioning · benefits) and teaching (objectives · worked example · recap) — TWELVE of
  the thirteen entries in that file. 🔴 Every list was DERIVED FROM THAT FILE'S OWN PROSE, never
  invented: teaching's three were already in its Layout and Signature lines, the lab meeting's
  two are its Signature line verbatim. Where a genre's prose names no required section, none was
  added. The thirteenth, `webinar`, has no list ON PURPOSE — it is a delivery MODE, not a genre
  (the same session can be a lecture, a pitch or a readout), so `purposes.NOT_A_GENRE` recognises
  the medium words and `check_purpose` asks for the GENRE instead of silently checking nothing. 🔴 This is the `formats.py` / `check_surface.py` mechanism
  generalised from SURFACES to GENRES, for the same measured reason — the shape of a genre is
  exactly what an author under time pressure drops (a poster loses methods and limitations; a
  committee deck loses the ask and becomes a status update). Binds by matching the RECORDED purpose
  (read from both record schemas, including the audience brief) against `binds_on` terms; no match
  is NOT CHECKED, never a guessed genre, because firing a clinical section list at a product pitch
  teaches the author to ignore the check. Section terms are multilingual (a 中文 deck names the same
  section in 中文 and a monolingual list would fire on every one), extendable with
  `design_plan.purpose_section_terms`, waivable with `{"purpose": {"waived": …}}`. It asks whether
  the deck NAMES the section, not whether it does it well — judging that stays the critic's. Each
  purpose also carries one fidelity rule beyond never-invent, printed every run.
- `check_template_profile.py` — a registered template's `profile.md` must be OBEYED, not merely
  available. The registry is the one artefact in this skill with a MEMORY across decks — layout
  indices, decorative furniture that cannot be deleted from a layout and has to be covered by the
  build, the font decision someone already made and the trap they already hit. Measured by grep,
  `profile.md` was read by `registry.py` and `deckkit.py` (both producers) and by NO check, so a
  build could ignore every line of it and nothing downstream would know. Same claim as
  `check_direction_applied.py` one level down: a look that was CHOSEN must be verified against the
  deck that SHIPS. A profile opts in with ONE fenced `## Machine-checkable contract` json block
  (prose and contract in one file, so they cannot drift into two truths) declaring any of
  `match` / `layouts` / `fonts` / `title_color` / `must_cover`; it reports `LAYOUT OFF PROFILE`,
  `FONT OFF PROFILE`, `TITLE COLOUR OFF PROFILE` and `UNCOVERED TEMPLATE FURNITURE`. 🔴 Binding is
  by FINGERPRINT — the deck's own layout names + canvas size — not by a recorded template name, so
  a runtime that compressed the interview away is still checked. A profile with no contract block
  reports NOT CHECKED and exits 2; "there was nothing to check" and "everything checked out" are
  different sentences and it never prints the second for the first reason. Run by both gate paths;
  waive with `{"template_profile": {"waived": "<why this deck differs>"}}`.
- `check_fonts_resolve.py` — do the faces this deck NAMES resolve on the machine that MEASURED it?
  Not the portability question ("will the presenter have Calibri?" is unknowable from the file and
  is correctly advisory at PRE-FLIGHT 10) but the measurement one: every fit / wrap / overflow /
  footer-clearance guard sits on `deckkit._measure_lines`, which measures whichever face it can
  RESOLVE, so a named-but-absent face makes the build and the lint compute from the same wrong
  number and AGREE WITH EACH OTHER while the render disagrees with both. `deckkit.font_health()`
  has always been able to see this and `lint_layout` only `print`s it — in no `--json`, gating
  nothing, one line in a scrolling build log. It is NOT a build-time CRITICAL because deckkit's
  shipped defaults are `FONT='Calibri'` / `MONO='Consolas'` and neither ships with macOS: raising
  there would break every stock build on this skill's primary platform, and re-theming the
  defaults would silently change the look of every deck ever built from the library. So it blocks
  once, at hand-off, on both gate paths. Reads `latin`/`ea`/`cs` typefaces from the XML (the CJK
  and complex-script faces carry the text on exactly the decks where substitution hurts most) plus
  the theme's major/minor latin that an unstyled run inherits; a face carrying fewer than
  `MIN_CHARS` characters is reported, never blocked. Waive with
  `{"fonts": {"waived": "<why a substituted measurement is acceptable here>"}}`.
- `check_register_pixels.py` — the register a deck DECLARES must reach its RENDERED PIXELS, and
  must not be a previous deck's. The half `check_style_applied.py` structurally cannot reach: a
  BESPOKE register has no `presets.apply()` call to find, and a build that calls it and then
  hand-sets the tokens back passes there too. Reads the deck's own PNGs and reports
  `STOCK REGISTER SHIPPED` (deckkit's chromatic identity is what actually shipped while the
  declared hues are absent — SKILL.md's "never ship the default blue"),
  `DECLARED PALETTE ABSENT`, and `GROUND REPEAT` / `LAST DECK'S SCHEME` against `taste.md`'s LOOK
  HISTORY ("never reuse the last deck's scheme"). Presence is measured per-colour and NOT by area:
  measured on a real 15-page deck the signature accent covered 0.65% of its best page, so an
  area ranking called the deck's own palette absent; colours genuinely absent measured 0.0000%
  and an antialiased blend 0.093%, which is where the threshold sits. `DECLARED HUES ABSENT` is a
  separate rule from the count: a ground and an ink are shared by half the world's decks, so the
  HUES are the register — a deck rendered in greyscale scores 1 of 2 on the count and clears it.
  An unreadable PNG is reported as `UNREADABLE RENDER` and the remaining pages are still measured,
  because both callers wrap this module in try/except and anything RAISED would silently become
  "NOT CHECKED" for the whole deck. Waive with `design_plan.register_pixels_waived`. Imported by `render_deck.py --gate-check` (section
  `register_pixels`) and `codex_delivery_gate.py`. `--selftest` proves it both ways. It judges
  COLOUR only — composition is the sameness gate's and the critic's. `DARK GROUND ON A PRINTED
  BOARD` is the print carve: the freshness rule once told a real A0 poster to "move the VALUE (dark
  for a light run)" and the board was rebuilt dark, which is the one ground print shops uniformly
  advise against (ink, drying, streaking, surcharges, and light hairlines thinning at print
  resolution). On a `chrome == "print"` format the repeat is still reported, but the advice becomes
  paper warmth and accent hue; a dark canvas becomes its own finding. A projected deck is untouched
  — 8 of the 18 registers are dark. The dark finding is scoped to LARGE-FORMAT boards (>=300 sq in,
  which keeps A0/A1 in and A4/A3 out): the ink, drying and surcharge evidence is about wide-format
  poster printing, an A4 sheet is a sixteenth of the ink, and a dark A4 leave-behind is a legitimate
  design — below the threshold it is a note. And a LIGHT ground repeat on a printed board is
  reported rather than held, because print advice leaves only pale stocks and every pale stock
  matches every other; freshness there has to come from the accent and the type.
- `check_surface.py` — the canvas format's contract, checked against the BUILT deck. `formats.py`
  was producer-only: measured by grep, `import formats` appeared in two files and both write
  formats, so every per-surface rule in `references/canvas-formats.md` was advisory by
  construction. Recovers the format from the canvas SIZE (a built PPTX carries nothing else) and
  reports `SAFE ZONE` · `COLUMNS` · `DECK CHROME` · `TYPE FLOOR` · `FILL` · `MISSING SECTION`.
  The printed-board checks (`TYPE FLOOR`, `FILL`) apply only to formats declaring `type_floors` /
  `fill_range` — A0/A1 posters **in both orientations**, which are read at a fixed distance and so
  need ABSOLUTE point floors rather than lint's canvas-relative one. `COLUMNS` means a split of
  running COPY (both blocks ≥0.8in tall and ≥18% of the canvas wide), so a stat pair or chip row on
  a portrait card passes; `DECK CHROME` identifies furniture by what it SAYS — a page marker, slide
  count or date — so the `payoff/handle bottom` line `canvas-formats.md` prescribes passes while a
  real `deckkit.footer()`, whose tag and page number are two narrow shapes, is caught. `FILL`
  measures the area COMMITTED to content blocks — all a PPTX can answer, and it cannot tell a full
  panel from an empty one: measured on a real A0 board, 82% committed and 17% inked. When renders
  exist the inked share is REPORTED beside it (and a wide gap named), deliberately without a
  threshold — two poster renders is not a calibration set, and `lint_deck.py`'s calibrated
  HOLLOW FILL is switched off in `--surface` mode, so on a board nobody was reporting either
  number. A deck with no slides, and an unregistered canvas, report NOT CHECKED, never clean. Waive required sections with `design_plan.surface_sections_waived`. Imported by
  `render_deck.py --gate-check` (section `surface`) and `codex_delivery_gate.py`; `--selftest`
  proves it on built fixtures. `PROPORTION` and `TEXT BLOCK` hold a printed board to the ~20-25%
  text / 40-50% graphics split the poster literature converges on, and to ~50-word blocks. PROSE is
  what a reader has to READ: a panel drawn BEHIND text is a container, not a graphic (else a bigger
  box would pass the check); a run of six words or fewer is a LABEL that rides with the graphic it
  names (measured, classifying by "has text" scored a three-node flowchart 100% text and a results
  table 69%, telling both to add figures they already were); and headline-sized runs are navigation,
  not prose (counting the title penalised boards that size it correctly).
- `check_design_contracts.py` — the DESIGN stack's index guard: every self-verify cross-reference in
  the tree resolves to a real item, the `### Design self-verify (a–s)` header covers every item the
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
- `arc_divergence.py` — its content-side twin: mechanical divergence + strawman check for the
  2–3 narrative-arc candidates (Step 1), CJK-aware
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
  — a template's layouts/placeholders/logos. `requirements.txt` — deps.
  `install_skill.py` — the installer: `--target all` (default) writes into EVERY runtime skill
  root that exists (`~/.codex/skills/` · `~/.claude/skills/` · the host-neutral
  `~/.agents/skills/` that `npx skills add` uses). It covered only the first two once, and the
  third silently sat a whole major version behind while `check_version.py` correctly announced
  the newer release nobody could apply to it.
  `registry.py` — resolves the user's template + `taste.md` **Registry** root on ANY runtime
  (Claude/Codex roots keep priority, host-neutral `~/.slide-maker/slide-templates/` otherwise,
  `$SLIDE_MAKER_REGISTRY` overrides). 🔴 Run it instead of naming a root from memory — a
  hardcoded two-host list left every other runtime with no registry at all, so Q1(a) lost the
  saved-templates option and `taste.md` was never read or written, silently. `check_env.py`
  prints the resolved root on every preflight.
- `ornaments.py` — hand-made marks as native, editable, motif-tagged geometry: `squiggle` (a wave
  under a claim), `scribble` (a looping pen coil), `brush_stroke` (a swash behind a word), `tape`
  (translucent, torn ends, holding a print), `scallop` (a badge). Quiet by default, `loud=True` for
  a hero; the motif budget counts them and TEXT_OVER_MOTIF sees text across them.
- `native_art.py` — the drawn surfaces of the native visual languages: ink ridges (fading into mist), seal, ensō,
  paper hills/cards/clouds/sun with real soft shadows, drafting grid and drawing sheet, iso stack, dimension
  line, numbered balloon, page-clipped colour block, solid/grid slide backgrounds. Native and editable,
  deterministic for a seed, never past the page, every angle in range.
- `rotgeom.py` — where a ROTATED shape paints: the placed box (exact at 90° multiples, so a
  vertical margin label is measured exactly), the exact intersection of two tilted rectangles, and
  point-in-polygon. The one definition both geometry gates (`lint_deck.py`, `deckkit.lint_layout`)
  import — before it, both read the unrotated frame and were wrong in both directions.
- **`sigs.py`** — one lookup, many helpers: exact signature + docstring head for every named deckkit/designed_charts helper, plus the run-tuple and RGBColor call-shape contracts. `--search TERM` to find one, `--list` for all, `--full` for whole docstrings. Use it BEFORE writing a build script; reading deckkit.py one function at a time costs a round-trip per question.
- `lint_deck.py` — deterministic **render-time** layout lint and complement to deckkit's build-time
  `lint_layout`: re-checks geometry on the final file (off-slide overflow · block/image collision
  [containment excluded] · footer-zone intrusion · text-past-card · uneven rows) AND adds the
  render/parse-only faults (CJK kinsoku/widow · whole-page-image · orphan slides — plus missing EA font as the render-time BACKSTOP; `lint_layout` now catches it at build time as `CJK_NO_EA`, whose fix is `deckkit.retrofit_ea(prs)` on the line above the lint — setting `EAFONT` fixes the next build, not this one);
  run after render, before critic; non-zero on findings. `smoke_deckkit.py` — regression guard for the helpers.
- `ooxml_safety.py` — **PowerPoint safety**, read from the saved file: values PowerPoint repairs or deletes that
  LibreOffice renders (angles outside 0..21599999, negative shadow distances, alphas and gradient stops outside
  0..100000, letter spacing out of range, `spPr`/`rPr` children out of schema order, duplicate shape ids) are
  CRITICAL; shapes past the slide edge are advisory (`BEYOND THE PAGE`, quiet for `bleed_intent`). `lint_deck`
  runs it, so both delivery gates hold it.
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
  Step 5 runs it before acting on any review). **`--schema critic` PUBLISHES that contract as a
  JSON Schema** to hand a subagent as its structured-output shape — same file publishes and
  checks, from the same enum constants, so what a critic is asked for and judged by cannot drift.
  Use it at every dispatch: the contract was previously discoverable only by failing, and the
  failure arrives after the review has already run. (`--schema arbiter` deliberately refuses —
  the Job-1 and Job-2 payloads are two shapes and silently picking one would be worse than not
  offering it.)
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
- `image_prompts.py` (build the prompt manifest; `--facts <visual-facts.md>` folds OBSERVED subject
  attributes — written after looking at real reference photos — into each prompt as binding
  attributes) → `generate_images_codex.py` (no-key, Codex CLI; `--ref-dir` stages matching
  `slide-NN-*` reference photos beside the generation and REQUIRES `--ref-intent`
  generic-concrete | stylized-illustration | fallback-rung, which also injects the
  non-photographic render mode for the two illustration intents) /
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
- `deck_gates.py` — write and shape-check `.deck-gates.json`, the record every hand-off gate
  reads: `init <deck-dir> [--slides N]` (a fully-SHAPED skeleton whose every value is a placeholder
  the checker rejects) · `set <deck-dir> <dotted.path> <value>` · `check <deck-dir>` (EVERY shape
  problem at once — the half `--gate-check` deliberately cannot batch). A shape pre-flight, never
  the gate: it never opens the .pptx.
- `deck_cycle.py` — one call for the edit → build → check loop, so an iteration costs one
  round-trip: `deck_cycle.py build_<deck>.py` (build + build-time lint) · `--render` (adds render +
  render-time lint). Prints every finding VERBATIM, leaves rendering opt-in, and stops before
  rendering on a CRITICAL build fault. Carries the **LOOP BREAKER**: the same fault surviving three
  runs escalates, and the next run is REFUSED if the edit only moved numbers (the build script's AST
  is hashed with numeric literals normalised) — `--nudge-again "<why>"` overrides and records why.
- `run_eval.py` — score a produced deck against `evals/evals.json`, machine-decidable assertions
  only: `--score <deck-dir> --eval <id>` (+ `--transcript` for `reference_reached`, the only way to
  answer *was that reference actually read*), `--record` to append under the current `VERSION`.
  Exists because every suite in `tests/` asks whether the CODE works, never whether the DECK got
  better. 🔴 A **skipped** assertion is not a pass.
- `check_skill_lossless.py` — guard a SKILL.md slimming refactor: prove it LAYERED content instead
  of deleting it. `--baseline <ref>` (e.g. `main:skills/slide-maker/SKILL.md`); every SUBSTANTIVE LINE of the
  baseline must still be findable VERBATIM somewhere in the skill tree — moving a line between
  files is fine, reflowing is fine, changing what it says shows up as a missing line. Deliberate
  deletions go in an allowlist with a written reason. 🔴 It proves the lines SURVIVED, not that
  they still reach the context at the moment they are needed — see
  `references/maintenance-boundaries.md` for the half it cannot see.
- `check_tests_wired.py` — every `tests/test_*.py` must be named by a CI step, or CI fails.
  Measured: 16 files had never run, one of them already red with 4 failing assertions and nothing
  reporting it. Deliberate exclusions go in its ALLOWLIST with a written reason.
- `check_inventory.py` — every script, agent and reference must appear in THIS file, or CI fails.
  Same shape as `check_tests_wired.py`, and for the same reason: an undocumented capability is one a
  non-Claude agent cannot find. Measured at introduction: 11 scripts and 11 references missing.
- `skill_fingerprint.py` — can this COPY tell it is not running what main has? Compares git blob
  SHAs and commits nothing. Exists because `VERSION` only moves on a RELEASE, so every commit
  between releases was invisible to the update check — tested directly, a copy with 99.3% of
  SKILL.md truncated away passed the version check.
- `written_reason.py` — how long a written reason is, measured so the bar does not depend on the
  language. A dozen floors in this skill were `len(text) < N`, i.e. a count of CODEPOINTS, which
  quietly made the same requirement stricter in Chinese than in English.
- `fanout_record.py` — land what a parallel fan-out produced ON DISK, so one dead agent costs one
  agent rather than the whole round. Used by research, the critic panel, and section authoring —
  the three places this pipeline dispatches in parallel.
- `roundtrip_report.py` — how many round-trips a build actually cost, measured from a session
  transcript. 🔴 Explicitly NEVER a gate: it is a measurement to reason with, not a floor.
- `_console.py` — make this toolchain's output survive a console that cannot encode it. The reports
  are full of ✓ · ✗ · → · 🔴, and on a legacy Windows code page encoding those raises
  `UnicodeEncodeError` and kills the tool MID-REPORT.
- `smoke_component_audit.py` · `smoke_directions.py` · `smoke_render_slides.py` — regressions for
  three tools whose FALSE-POSITIVE side is the dangerous one: a component's own output must never be
  reported as a hand-roll (or the audit trains agents to stop using components); the direction gate
  must move the ink, not just the colourway; and a `--slides` preview must be byte-identical to the
  same page from a full render, leaving no cache behind.
- `deckkit.disc()` — the circle primitive. `box(round=True)` is a rounded rectangle at
  every radius, so before this the library could not draw a circle through any public
  helper while using `MSO_SHAPE.OVAL` seventeen times internally. Same fill/line grammar as
  `box`, top-left placement, `_flat`ed (no inherited theme shadow), `h=` for an ellipse.
  Backed by `tests/test_disc_primitive.py`, which also asserts that `box(round=True)` is
  still NOT an ellipse — the half that makes the new helper worth having.

- `canon_probe.py` — the part of the presentation canon that CONVERTS into a measurement over the
  built deck. This skill already cites Duarte, Minto, CRAP, Mayer, Gestalt and cognitive load, all
  of it in prose and none of it measured — which by the skill's own enforcement invariant makes
  them advisory. Three rules were made mechanical, each calibrated on 29 delivered decks / 349
  slides rather than on invented examples, and each measured at 0 false positives there: **NOTES
  ECHO SLIDE** (Mayer's redundancy principle — similarity between a slide's text and its speaker
  notes; real decks top out at 0.53 with a median of 0.10, so the floor sits at 0.75), **CATEGORY
  TITLE** (Knaflic — a title from an enumerated set of bare labels, `Overview` / `背景` / `Agenda`;
  cover and section roles are exempt), and **CHART SAYS IT TWICE** (Tufte — data labels AND a value
  axis/gridlines print the same number twice). The last two are high-precision and deliberately
  low-recall: they are floors, not critics.

  🔴 Two candidates were REJECTED BY THE DATA and the docstring records why, so that "tried and it
  does not work" never looks like "nobody thought of it". Knaflic's declarative-title rule measured
  as overlap with the recorded takeaway has median 0.33 and scores the BEST titles LOWEST — a sharp
  title re-words on purpose — so judging "declarative" stays a critic-rubric item. Gestalt proximity
  failed four separate formulations (shared-top grouping flagged 51 merely y-aligned rows; adding
  equal width+height dropped peers whose captions wrapped; dropping height left a timeline whose
  markers SHOULD be unevenly spaced; intra- vs inter-group distance "flagged" 200 of 360 pairs on
  guessed pairings). The root cause is structural: a .pptx records coordinates and no notion of
  which shapes belong together. The rules that convert all share one property — their criterion is
  already IN the record. Run by both gate paths; backed by `tests/test_canon_probe.py`, which
  asserts each rule fires on its defect and stays silent on the real shape it must not flag.
- `check_reason_width.py` — no written-reason floor may be measured with `len()`. `len()` counts
  CODEPOINTS, so `len(reason) < 12` means "12 letters" in English and roughly twice the information
  in Chinese: the bar silently doubles for the users least able to see why their reason was
  rejected. Measured on a real Chinese deck — `audience_brief` rejected an 11-codepoint decision
  against `MIN_TEXT = 12` while a 12-letter English phrase carrying a third as much passed.
  `written_reason.reason_width` had shipped months earlier and twelve sites across six modules
  simply never reached for it, two of them written the same day as a module that used it correctly,
  which is why this is a guard and not just a fix. It scans `scripts/*.py` for a `len(...)`
  compared against a NAMED floor (`MIN_TEXT` / `MIN_WHY` / `MIN_RULE` / `MIN_QUOTE` / …) and leaves
  literal comparisons alone — `len(x) < 2` is an emptiness test, not an information floor. The
  match is deliberately split in two (find the floor, then ask whether the compared expression
  calls `len`), because a single paren-counting regex CANNOT cross the inner `)` of
  `len(str(x.get("k") or "").strip())` — the form ten of the twelve real sites used — and the first
  version of this guard reported CLEAN on the planted bug. Deliberate exceptions go in `ALLOWLIST`
  with a reason. Backed by `tests/test_reason_width_floors.py`, which plants the bug in both
  spellings and fails if the guard misses either.
- `check_gate_parity.py` — the two runtimes must gate the same concerns, or CI fails. Every
  `_gate_section` in the shared path must be reachable in `codex_delivery_gate.py`, and every shared
  contract module one path imports must be imported by the other. It does NOT check they enforce
  identically — a delivery gate and a pre-flight legitimately differ in strictness — only that
  neither is missing the concern entirely, which is the failure that has actually happened, three
  times: `png`/`path`, `design_plan`/`design`, and `checkpoints`. Deliberate one-sidedness goes in
  its ALLOWLIST with a reason.
- `delegated_picks.py` — what the skill decided ON THE USER'S BEHALF, recorded and floored.
  Binds ONLY on a deck whose checkpoints were delivered as `auto` (read from `checkpoint.mode`, both
  schemas) — a supervised run is untouched, so the cost lands exactly where the risk is.
  `interview.picks` carries one row per Step-0 axis with its `source` (`stated` · `genre-default` ·
  `from-material` · `not-applicable` · `delegated`); a `delegated` pick needs a **`basis`** pointing
  at the request or the material, and the three that aim everything downstream (audience · purpose ·
  template) also need an **`alternative`**. 🔴 `angle` may never be `delegated` — the measured
  failure is a run that read "decide everything yourself" as licence to pick the angle and shipped a
  thesis nobody asked for, passing every gate. Gives `references/auto-delegation-quality-gates.md`
  and `checkpoint-convention.md`'s delegated-picks rule their first deterministic backstop.
- `composition_probe.py` — measure a slide's COMPOSITION so two versions of one page can be told
  apart mechanically: `probe <deck>.pptx --slide N` · `compare <deck>.pptx --slides 1,2,3`. Reads
  the BUILT pptx, never a render, and never measured text ink — so it reads a Chinese deck exactly
  as it reads an English one. Reports where the ink is (occupancy grid shaped to the canvas, so a
  9:16 story deck is not measured as a 16:9 slide), how many blocks carry the page, what dominates,
  which way it flows. `variant_signatures()` subtracts the furniture ALL variants share before
  comparing — variants of one page keep the deck's chrome by design, and counting it makes every
  variant look alike. Backs Step 4's **composition competition**: the signature page is competed
  between 2–3 skeletons rather than composed once, and this refuses three restylings of one layout
  the way `directions_diversity.py` refuses three colourways of one direction. The divergence
  weights and floor were found by search over a 10-layout corpus and validated on 9 layouts they
  were never fitted on (0 errors over 36 pairs); `tests/test_composition_probe.py` re-runs that
  held-out set, so a weight change that breaks generality fails there rather than in a real deck.
- `blind_read.py` — the BLIND READ-BACK: the one check that reads the rendered PICTURE rather than
  the file. `packet <deck-dir>` emits PNG paths + a fixed 7-question list and **nothing else** (no
  takeaways, no design plan, no deck title — each would prime the answer); an independent reader
  answers it (`agents/blind-reader.md`); `compare <deck-dir> --answers <f> [--write]` COMPUTES the
  disagreements against the record and triages them **hard** (fix + record `fixed`) / **ask**
  (answer in writing) / **note** (a judgement call, for the critic, owes nothing). The gate
  re-derives the findings from the recorded answers, so an edited severity or a deleted finding is
  caught. `refuted` is a legal exit — the reader is not infallible. Carves: `no-render` ·
  **`no-reader`** (records that the deck shipped UNREAD, which is not the same as saying it was
  read) · `tiny-ask` · `user-waived`. It owns the two-schema key lookups (`design_of`,
  `planned_icon_family`) so no gate spells `design_plan`/`design` or `icon_family`/`icons[]` itself.
- `taste_ledger.py` — what THIS user has already corrected by hand, so the next deck does not
  relearn it: `add` · `list [--binds-at …] [--format prompt]` · `retire <id> --gate <CODE>` ·
  `check <deck-dir>`. Data lives OUTSIDE the repo (`~/.slide-maker/taste-ledger.json`, override
  with `$SLIDE_MAKER_TASTE_LEDGER`) — a user's verbatim words are not repo content. **Self-limiting:
  an entry is RETIRED once it earns a deterministic gate**, so the ledger only ever holds
  taught-but-ungated rules. An empty ledger asks nothing; the gate checks each rule was CONSIDERED,
  never that it was obeyed.
- `audience_brief.py` — the AUDIENCE BRIEF contract (`content.audience_brief`): who is in the room
  and the ≥3 decisions they must make, written BEFORE the research because the frame aims it.
  Rejects a brief whose rows are "understand X" comprehension goals — that is the subject brief in
  disguise, and it passed every shape check until this rejected it.
- `material_probe.py` — the Step-2 material probe contract, and the one owner of the `png`/`path`
  file-key spelling that the shared and Codex records had already drifted on.
- `anchor_proof.py` — the THREE-anchor signature proof contract (signature · complex · data).
- `check_tests_wired.py` — every `tests/test_*.py` must be named by a CI step, or CI fails.
  Measured: 16 files had never run, one of them already red with 4 failing assertions and nothing
  reporting it. Deliberate exclusions go in its ALLOWLIST with a written reason.
- `fetch_images.py` — the SOURCED-photo pipeline: `search` (look, download nothing) · `fetch`
  (download candidates + write the `sources.json` provenance ledger) · `adopt` (mark the one you
  chose, after LOOKING) · `ledger --tokens|--credits` (the plan's evidence rows, and the credit
  lines the licence obliges). Keyless: Wikimedia Commons + Openverse. `--selftest` runs offline.
- `image_qc.py` — what a program CAN measure about a candidate photo before it is placed:
  resolution/DPI at the PLANNED box, crop loss, softness, flat plates, letterbox bars,
  near-duplicates, a possible-watermark heuristic, and EXIF rotation (`--fix` bakes it in). Its
  `--contact-sheet` is ONE labelled PNG of every candidate plus a sha256 — the artifact that makes
  looking cheap, and that a critic's consent can name.
- `visual_languages.py` — four complete image-led looks (editorial, soft, collage, storybook): palette with
  text-safe inks, system fonts per platform (`fonts="both"` default) and per SCRIPT (Han / kana / Hangul),
  a surface, image treatments and six page compositions; registered with register_surface for
  ground/card. Never imported by deckkit/presets/register_surface. See references/visual-languages.md.
- `vl_native.py` — page compositions of the native visual languages (`ink`, `poster`, `cutpaper`, `drafting`):
  plans the text first (measured, refused past each field's floor; display type breaks at clause marks, never a
  lone character), draws the art with the text kept clear, then sets the text; the points page; vertical CJK for
  `ink`; poster's colour field (with the deck's inks and card following it) and drafting's drawing sheet on every
  `new_slide()`.
- `collage.py` — `collage(slide, region, items, seed=, keep_clear=)`: 1-4 images as tilted, white-bordered,
  taped prints; geometry decided first — a print never enters `keep_clear` and never covers more than
  25% of its neighbour; deterministic for a seed; slot items keep the image-series tag.
- `display_type.py` — display typography: `stacked` (one headline, one line per paragraph, each sized by
  its REAL glyph width to fill the measure), `two_tone` (named words in a second colour, CJK too),
  `outlined` (hollow display marks drawn as a picture — LibreOffice renders a native hollow run filled).
- `surfaces.py` — grounds that are not flat colour: `grain_background(slide, color, strength=)` sets a
  deterministic tiled grain/paper tile as the slide's real background (`<p:bg>`), never a picture shape,
  amplitude capped so text contrast holds.
- `image_series.py` — the ART-DIRECTED IMAGE SERIES for an image-led deck (`imagery: series`): `check`
  validates `series.json` (every slot's meaning line, REFERENT RULE, the people rule, frames, the chroma
  key vs the palette), `prompts` writes the Codex generator's manifest, `qc` compares every image with
  the key image, `slot_picture` places a slot and tags it `+gen.<slot>` for the gates.
- `check_visual_language.py` — the VISUAL LANGUAGE gate: a deck recording `design_plan.visual_language` must be
  built in it (cover + half the pages carry `+vl.<name>`, its display face used) and keep its `forbids`;
  unknown names and unreadable decks block. Called by `render_deck.py --gate-check` AND `codex_delivery_gate.py`.
- `check_image_series.py` — the IMAGE SERIES gate of an image-led deck (`design_plan.imagery:
  "series"`), read from the FILE's `+gen.<slot>` tags and `series.json`: blocks an unplanned generated
  picture, a series with no slot placed, and a generated person given a name/role/quote or team /
  testimonial framing without a visible 'fictional' label; notes unplaced slots and a missing or
  unresolved series QC. Called by `render_deck.py --gate-check` AND `codex_delivery_gate.py`.
- `check_image_provenance.py` — holds each `image_sources` evidence token against the ledger and
  against the BUILT deck: a `searched, none found` rung must be backed by a recorded search (an
  `unreachable` network is refused as one), and an attribution-required photo must be credited on
  a slide. Called by `render_deck.py --gate-check` AND `codex_delivery_gate.py`, so both runtimes
  enforce one contract.
- `image_fx.py` — `duotone(img, ink_a, ink_b)` / `grayscale(img)` — preprocess a colour photo to the
  deck's ink so it doesn't fight the accent (riso/brutalist/ink/luxury/museum). See `design-gallery.md`.
  `sticker_outline(img)` — a die-cut border grown from a transparent cut-out's own alpha (it
  refuses an opaque photo: there is no silhouette to follow).
  `feather(img)` — fades an illustration's edges into the ground (the storybook language).
  `chroma_cutout(img, key=)` — keys a generated subject off its flat background (the image-series
  cut-out slots), despilling the edge band; it refuses a background that is not flat, a subject
  touching the frame edge, or a key that leaves no usable subject.
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
- `blind-reader.md` — the BLIND READER: handed slide PNGs and a fixed question list, never the content record. Reports what a viewer SEES so a machine can compare it against what the authors CLAIM; disagreement is the useful output. Tags each problem with a `kind` when writing in a language outside the triage's English/Chinese keyword sets.

**References** (`references/`, loaded on demand): `auto-delegation-quality-gates.md` (**auto mode rigor enforcement** — "decide yourself" means "you choose", not "skip steps"; checkpoint protocol, image legibility floors, component discipline, critic requirement) · `canvas-formats.md` (per-surface layout DNA for the non-16:9 formats — square/rednote/story/A4 — + the repurpose/batch pattern; pairs `scripts/formats.py`) · `design-principles.md` (the craft / the "why"; incl. the **C.R.A.P. framework** — Contrast · Repetition · Alignment · Proximity) · `design-gallery.md` (style+component catalogue mined from 21 pro decks — pick a preset, reach for the right component) · `semantic-color-contract.md` (bind a hue to a concept deck-wide) · `review-rubrics.md` (universal + per-purpose review criteria) · `design-by-purpose.md` (per-purpose look for "design a clean one") · `form-selection.md` (**content-shape → candidate FORMS** — the single design-decision map; generate a set, pick deliberately) · `schematic-diagrams.md` (**HOW to draw a labelled SCIENCE schematic** — force/ray/circuit/apparatus/vector/wave; matplotlib/domain-lib recipes for precise/label-critical ones, OR the image tool for complex/stylized/template-matched ones with labels overlaid native; + the domain-accuracy fidelity gate) · `clinical-evidence-figures.md` (**the FORMS a clinical / evidence deck is made of**, and the fidelity rule each carries — participant flow whose ARITHMETIC IS ENFORCED · forest (ratios on a LOG axis) · Kaplan–Meier (a STEP from raw times+events, censoring ticks, numbers at risk) · Bland–Altman (bias ± 1.96·SD of the DIFFERENCES, never a correlation) · ROC (square + chance diagonal + AUC); a confusion matrix routes to the existing `heat_matrix`. Exists because `design-by-topic.md` listed Medicine/clinical as a first-class domain while every row in it is an AESTHETIC row, so the skill could STYLE a clinical deck and not DRAW one; it also states what it does NOT supply) · `data-viz.md` (pick the chart type; editable-native vs raster) · `image-generation.md` (when/how; topical, text-free, consistently placed; **TEXT LEGIBILITY floor — scrim required for all text-over-image**) · `visual-languages.md` (**four complete image-led looks** — editorial · soft · collage · storybook: `visual_languages.use()`, the six page functions, fonts per platform and per script, the record fields and the gate) · `icons.md` (one coherent open-licensed icon family, recolored, restrained) · `generated-template.md` (Q1's image-tool template branch) · `style-analysis.md` (mimic a style example, Q4) · `font-guidance.md` (portable fonts, tofu recovery) · `multilingual.md` (non-Latin / CJK / RTL) · `east-asian-aesthetic.md` (Chinese ink / traditional looks — paper · seal · CJK numerals · `ink_wash`/`eastern_traditional`) · `animation.md` (when/why + `anim.py`) · `large-deck-orchestration.md` (section fan-out; default is single-author) · `citations-and-bibliography.md` (**cite from the .bib, never retype it** — BibTeX in, markers + reference page out, the refuse-don't-invent rule, and the marker/list/.bib consistency gate) · `navigation-and-qa.md` (**the deck you PRESENT FROM, not just read** — `link`/`agenda(targets=)`/`back_link`, the link scheme guard, where jumps belong, and the `content.qa` backup-slide gate) · `collaborative-mode.md` (direction→outline→draft gates) · `redesign-existing-deck.md` (diagnose-then-rebuild) · `handoff-and-iteration.md` (delivery + iterate without clobbering edits) · `design-intelligence-addendum.md` (the deck-level design gates Step 2 measures against — rhythm map · block-dependency audit · Concept→Visualization table · semantic-colour ledger · variation floors) · `troubleshooting-faq.md` (**symptom → cause → fix for every error surface** — env · build exceptions · both lints · render · images · CJK — plus the FAQ; consult on any failure, and report findings to the user in its plain-language form) · `user-taste.md` (the registry-root `taste.md` — schema · read protocol · dial-ledger promotion + consented-look write-back) · `interview-protocol.md` (**Step 0 in full** — Q1 template · Q2 purpose/venue · Q3 source material · Q4 style, incl. density levels, mimic modes and the direction-gate scope; opens with the trap that this interview has FIVE lines and a choice widget takes FOUR per call, so batching silently drops one) · `content-plan-spec.md` (the Step-1 plan's required fields — **audience brief first**, then the comprehension brief and the per-slide table) · `deck-setup.md` (Step 3 canvas — the non-default surfaces 4:3 · 小红书 3:4 · 1:1 · story 9:16 · A4 · A0/A1 poster, and §Fonts, which SKILL.md routes to before the first `set_palette`) · `asset-production.md` (the **evidence manifest** — probe asset geometry BEFORE the design plan, so the art director is not blind to a 2400×700 figure headed for a half-column; then crops, equations, plates) · `design-by-topic.md` (the other axis from `design-by-purpose.md`: what the SUBJECT is — finance · engineering · medicine · luxury · gaming · crime · climate — with the ANTI-PICK and the cliché guard) · `critic-panel.md` (the CONTRACT CARD's full field list and the panel/arbiter protocol) · `handoff-checklist.md` (what the hand-off note must carry — caveats and next steps, never a recap) · `runtime-routing.md` (pick a profile from CAPABILITIES first, not from the provider's name — an OpenAI model is not automatically a Codex delivery path) · `security-and-capabilities.md` (the honest inventory of what this skill does to your machine; read before installing, and again if a scanner flags it) · `maintenance-boundaries.md` (**read before merging, removing or simplifying any gate** — what each tempting simplification costs; the half `check_skill_lossless.py` cannot see) · `file-inventory.md` (this file). · `examples/` (`build_example_generic.py`, `style_example.py`, `section_example.py`).

`codex-runtime.md` is the **Codex-only** execution adapter: visible design proof, typography/icon/component evidence, and a focused critic-pair gate. It never changes Claude Code's workflow.

**Registry** (NOT part of the skill): resolved by `scripts/registry.py` — `~/.claude/slide-templates/` (Claude Code) · `~/.codex/slide-templates/` (Codex) · `~/.slide-maker/slide-templates/` (host-neutral: every other runtime, and the fallback that guarantees a write target exists) · `$SLIDE_MAKER_REGISTRY` overrides all three — the user's saved templates, **plus `taste.md` at the root** (the portable taste profile — schema + read/write protocol in `references/user-taste.md`); read for choices, write new `profile.md`s to the active host — a freshly-designed look saved at hand-off carries the vetted critic `strengths` distilled into its profile's Notes. Empty for a new user (no templates, no `taste.md` — silently skipped; no write until the first durable signal).
| `scripts/contact_sheet.py` | Montage every `slideNN.png` onto ONE image so a critic can survey a whole deck in a single look, then open individual slides at full size only where needed. Narrows the COST of a review round, never its scope. |
