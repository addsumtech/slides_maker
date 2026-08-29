# Codex runtime adapter

## Purpose and boundary

Use this file **only for the `codex` or `openai-gpt-bridged` runtime profiles** in
`references/runtime-routing.md`. It raises OpenAI execution reliability without changing Claude Code's
or Kimi's established path: do not alter their panel sizing, checkpoint UI, or the global meaning of
an advisory. The shared skill still owns content fidelity, craft, and the normal critic protocol; this
adapter closes the gap where an execution-capable OpenAI runtime can compress several visual decisions
into one build pass and then mistake a clean hard-lint for a good deck. A GPT Store sandbox without the
bridge may prepare these artifacts, but cannot claim the final gate passed.

The adapter has two kinds of rules:

- **Universal floors made explicit in Codex:** rendered proof, a readable type floor, pixel checks,
  and an independent content + design review record.
- **Truth floors reach this gate as blocking errors, not warnings.** `DATUM SCALE` (a bar whose
  length no longer matches the number it claims) and `ASSET NOT USABLE` (a picture that decoded to
  nothing, to one flat colour, or not at all) are computed by `deckkit` at BUILD time and replayed
  by `lint_deck.py`, so they arrive in `lint.findings` with `severity: "error"` and `check_lint`
  blocks on them like any other. There is no waiver: a chart that misstates its own data and a
  frame with no image in it are not judgment calls. If a bar genuinely should not be measured,
  do not tag it — an untagged bar is unchecked, which is an honest state, unlike a waived one.
- **Accessibility floors (`STRICT_WARNINGS`): remediate or waive, never ignore.** `ICON CONTRAST`
  and `NON-TEXT CONTRAST` are WCAG 1.4.11's 3:1 floor for marks that carry meaning. They arrive as
  per-slide *warnings*, a stream the gate previously had no strict path for at all — so a deck
  could ship an icon at 2.69:1 and pass. To waive one, record
  `{"kind": "a11y", "warning": "<CODE>", "reason": "<why this mark is decorative>"}`; a decorative
  flourish whose meaning is carried by an adjacent label is a legitimate waiver, and a bare "ok"
  is refused. Only floors with an arithmetic answer live here: a ratio either clears 3:1 or it
  does not. Density, component reach and form variety stay judgment calls — forcing a judgment
  through a waiver form turns it into a rubber stamp.
- **Taste-sensitive calls that stay explainable:** components, icon dosage, and form variety. Do not
  turn these into quotas. When the normal component or icon choice is intentionally wrong for this
  deck, record a slide-specific waiver and explain why.

Never use this adapter to prohibit bespoke work. A bespoke composition may still be the signature
move; the gate only rejects an *unexamined* hand-roll that duplicates a library component's known
geometry guarantees.

## Codex runbook

Read this before Step 2, then carry its evidence through the remaining steps. **Step 2 is
BRANCH-INVARIANT on the Codex path too** (SKILL.md Step 2): the design plan + design checkpoint run on
every Q1 choice, including a generated visual identity — a hero / style gate confirms the LOOK, it is
NOT the design checkpoint. Record the checkpoint as `design.checkpoint` in `.codex-deck-evidence.json`
(the shared path uses `design_plan.checkpoint` in `.deck-gates.json`); `render_deck.py` reads BOTH and
REFUSES a full render until one of them carries a recorded design plan + checkpoint, so the plan cannot
be reconstructed post-hoc at the delivery gate.

0. **Ask the whole interview, in plain text, before anything else.** This runbook used to begin at
   Step 2, which left the impression that the interview is the part a bridged runtime can compress.
   It is the opposite: with no choice UI there is no menu doing the remembering for you, so the
   questions have to be *typed*, and the ones that get dropped are the ones no artifact later
   demands. Ask SKILL.md's direct-question fallback in full — template · purpose/audience/delivery ·
   source material · **HOW MANY SLIDES** · style/language — as ONE compact message
   in the user's own language, then record the answers in `interview.record`. *(Review effort is
   NOT an interview axis: it is asked at the post-build review question, after the first clean
   render, with the rendered deck posted — see step 7.)*
   - 🔴 **Never fabricate a fake multiple-choice form**, and never present a menu the user cannot
     click. Numbered lines answered in free text are the correct shape here.
   - 🔴 **A missing answer is a QUESTION, not a default — and a deck is never silently ONE slide.**
     If no length and no time budget were given, ask. If the user declines, derive the count from
     what the CONTENT supports and state that number before building. (Measured: decks arriving at
     one page. The evidence template compounded it — `slide_count: 10` sat above a `slides` list
     showing exactly ONE row, and a template's example teaches louder than its numbers, so both
     lists now show several.)
   - **Offer the same escape the choice-UI hosts offer**: "decide everything yourself" is a real
     answer, and it triggers the per-deck AUTO WAIVER — every checkpoint still gets POSTED as an
     FYI, the stops are what disappear. Silence is not that answer; only saying so is.
1. **Make design visible before building.** On the `design a clean one` branch, create the normal
   direction preview and wait for the user's pick. In plain Codex chat, use the HTML preview or
   rendered archetype slides; do not replace the preview with a prose palette description. Keep the
   exact direction tokens and run the normal diversity check, rather than claiming four colorways are
   four directions. If a user says to decide, record the auto carve and the rejected alternatives.
   **Pick the look for the SUBJECT, not the reflex — run the topic contest in
   `references/design-by-topic.md` FIRST** (domain → apt presets → ANTI-PICK, the guardrail vetoes,
   the CLICHÉ GUARD: no reflex `dark_tech`/`synthwave` for "AI/tech", `terminal` for every dev deck),
   and record `design.style_pick` (`<preset|bespoke> for <domain> · beat <rival> · anti-pick avoided:
   <cliché>`, or `n/a — <locked look>`) — the evidence scaffold carries it, and both
   `codex_delivery_gate.py` and `render_deck.py --gate-check` require it, so produce it from the
   contest up front rather than by failing the gate. A bespoke register from
   `references/bespoke-registers.md` (adapt, never transplant) beats every preset when the subject
   has a visual world of its own. **On the GENERATE-A-TEMPLATE (image-tool) branch the SAME contest
   runs** — it shortlists the 3 generated styles and its ANTI-PICK/CLICHÉ GUARD governs the generated
   HERO's art-direction (no reflex neon/HUD sci-fi hero for "AI/tech", no green-globe for climate;
   `references/image-generation.md` CLICHÉ GUARD). `style_pick` is required on that branch too.
   Build and render the THREE anchor slides before the rest, as the normal anchor-proof rule requires
   (signature · the densest planned page · the key data/conclusion page — SKILL.md Step 4). One build
   script, one render call; `design_plan.signature_proof` is the role-bearing list both gates check.
2. **Write a focused build contract.** Declare type tokens before coding. On a 10in-wide 16:9 canvas,
   target body text at least 13.5pt for presented/text-heavy delivery and 12pt for self-read; a larger
   display token (normally at least 32pt) must create a real focal point. Reduce copy or split slides
   before reducing the body token. For CJK paragraphs leave deckkit line spacing unset unless the plan
   names a different, tested value.
   🔴 **The type floors above are for a PROJECTED canvas.** A surface printed at actual size — an
   A0/A1 conference poster — is read at a fixed distance, so its point sizes are absolute and these
   numbers do not apply: A0 wants display ≥90pt · section ≥36pt · body ≥24pt, 55–90% of the board
   covered, and methods + limitations as required content. `scripts/check_surface.py` enforces that
   contract on both paths, recovering the format from the built canvas size, and also enforces the
   safe-zone / `columns_ok` / social-chrome rules for every other non-16:9 surface — rules that were
   in `references/canvas-formats.md` and consumed by nothing. Record the surface as
   `design.format` when it is not `wide`; waive required sections with
   `design.surface_sections_waived`.
   🔴 **The accessibility floors are held on BOTH paths from one list.** `STRICT_WARNINGS` here is
   now derived from `lint_deck.A11Y_CODES` rather than restated, and `render_deck.py --gate-check`
   holds the same codes in its `a11y` section. Before that, this path held the two WCAG contrast
   codes and the shared path held nothing, so the same deck was accessible or not depending on
   which runtime shipped it. Missing alt-text, an untitled or duplicate-titled slide, and a
   scrambled reading order now block on both. Waive in writing with an `a11y` waiver and repeat it
   in the hand-off note.
   Also run `python3 scripts/palette_audit.py --inks …` at the palette step: it simulates
   deuteranopia/protanopia/tritanopia and names any pair that stops being two colours, which
   contrast ratios cannot see — two hues at different lightness always clear a ratio and can still
   be one colour to a dichromat.
   🔴 **A type contract is HALF a build contract — APPLY the register, do not just name it.** This
   step listed type tokens and nothing else, so a run following this runbook picked a preset in
   step 1, wrote its name into `design.style_pick`, and then hand-set colours: the register's
   *structural* half was never set at all. One call carries all three tokens —
   `p = presets.apply("<the style_pick preset>")` sets the palette, the geometry
   (`radius` — `0` squares every box-based component and `node()`, which is how `brutalist` /
   `swiss` / `ink_wash` / `blueprint` reach their own "no rounded cards" guard — and `rule_w`,
   which scales every card border, divider and node outline), and the **ground**
   (`set_ground`, painted by `add_slide()`; 8 of the 18 registers are dark, and before this
   existed a `dark_tech` deck shipped its light ink on a white canvas at 1.18:1). Read the
   returned dict for `surface` / `guard` / `image_prompt`.
   🔴 `scripts/check_style_applied.py` **is a hard gate on this path and on the shared one**:
   `design.style_pick` naming a preset while the build script never calls
   `presets.apply("<that name>")` is a BLOCK, because both gates already demanded the
   declaration and nothing verified it. A deliberate departure is a named waiver
   (`design.style_pick_waived`), not silence. A `bespoke` / `generated` / `n/a — <locked look>`
   pick is skipped by definition — those are not preset-based.
   🔴 And it checks the CALL, which is the weaker half. `scripts/check_register_pixels.py` is the
   other hard gate on both paths: it reads the deck's RENDERED PNGs and blocks when deckkit's own
   chromatic identity is what shipped while the declared hues are absent, when a declared colour
   reached no pixel at all, or when the canvas repeats a recent deck's from `taste.md`'s LOOK
   HISTORY. **This is the only check that can see a bespoke or generated register**, because those
   have no `presets.apply()` call for the source-level gate to find — so the pick this runbook most
   encourages was, until it existed, the pick nothing verified. Waive in writing with
   `design.register_pixels_waived`; render before the gate runs, since a pixel check with no pixels
   reports NOT CHECKED rather than clean.
2a. **Plan the deck's ARCHITECTURE before building any page, and build it from the helper.**
   `lint_deck` demands >=4 distinct page skeletons on an 8+-slide deck and reports three adjacent
   slides sharing 75% of their structure — but both fire AFTER the build, when varying the
   architecture means re-laying pages that are already written. One deterministic call proposes the
   whole sequence (~40ms, no model round-trip, which matters on this path):

       python3 scripts/plan_rhythm.py --roles <role,role,…> --carry <n,m> [--home <skeleton>]

   Then build each page from `deckkit.skeleton(slide, "<kind>")` — it returns the named rects for
   one of `statement · split · island · dashboard · band · full_bleed · rail · gallery`, and
   `python3 scripts/sigs.py --example skeleton` hands back a runnable call. `--home` makes a chosen
   composition the plurality, which is required whenever a direction gate picked one. Measured on
   identical content: 8 distinct skeletons planned against 2 improvised. It is a PROPOSAL — override
   any row the content argues with, and record the deviation in `design`.

2b. **The motif is a BUILT thing, not a described one — and both tiers have primitives.** The
   delivery gate requires `design.motif_generates` (background · markers · the one PAGE whose
   GEOMETRY is the motif), and a runbook that stops at "describe it" is how that page gets
   hand-rolled out of raw boxes — the failure `register_mark` was written for, one tier up.
   The QUIET signature is `deckkit.register_mark(slide, kind, corner=…)`; reach past the
   graphic-neutral `arcs`/`rule`/`ticks`/`ordinal`/`grid` for a subject-world kind — `seal` ·
   `stitch` · `trace` · `contour` · `caliper` · `hatch` — or the corner looks like every other
   deck's. The LOUD page is `deckkit.motif_page(slide, kind, legend="<what it MEANS>")`, whose
   kinds name RELATIONS, not looks: `seam` (a crossing) · `conduit` (accumulation along a line) ·
   `strata` (depth) · `radial` (dispersion) · `lattice` (coupling) · `orbit` (a cycle) ·
   `aperture` (focus) · `terrace` (staged advance) — pick the relation your CONTENT has, then swap
   in your subject's own material. `legend=` draws the key that satisfies the STRANGER TEST;
   without one anywhere the lint reports `MOTIF_UNEXPLAINED`, and on a deliberately FIGURATIVE
   device that advisory is the expected result — say so in the plan rather than adding a key you
   do not want.
3. **Treat categories as a visual-system decision.** In the per-slide design ledger, mark every slide
   as categorical or not. If the deck names roles, input types, product pillars, tools, or stages,
   choose one icon family and use it where it clarifies those categories. For each categorical slide,
   record the actual icon asset and its hash. A zero-icon result is allowed only when that list is
   empty or every omitted slide has a slide-specific reason; icons do not replace a mechanism diagram
   or evidence. **Do not use `qlmanage`, Quick Look, Preview thumbnails, screenshots, or crop-and-resize
   workarounds to make icon PNGs.** Generate them through `scripts/icons.py` / `icon_png()` from the
   source SVG, preserving transparent alpha; Codex evidence records the rasterizer and the gate rejects
   a recorded icon whose shortest edge is below 256px or whose PNG has no alpha channel. This is a
   Codex-only execution rule: it prevents thumbnail blur without changing the shared icon workflow.
3b2. **The DIRECTION competition is re-scored at delivery — `design.direction_gate` BLOCKS
   without it.** Same shape and same reason as the arc competition: the look was either chosen
   from rendered alternatives or it was not, and both are recordable.

   ```json
   "direction_gate": {"candidates": "directions.json", "picked": "<the one chosen>"}
   "direction_gate": "n/a - <locked template | mimic | user supplied the look | tiny ask>"
   ```

   `codex_delivery_gate.py` runs `scripts/directions_diversity.py` over the candidates ITSELF, so
   a verdict you type is not evidence the check ran. It scores two things a preset list quietly
   fails: a PAIR that is one idea in two colourways, and a set with no invented register at all.
   Measured on a real build — the author caught the first by eye and never noticed the second: the
   "bespoke" candidate carried a palette, a cover and a skeleton but no `cover_motif`, so the user
   chose from three presets and a colourway. If the set genuinely stands, record
   `"waived": "<why>"` beside it.

3c. **Every CONTENT IMAGE is sourced by the REFERENT RULE, and the plan says so in
   `design.image_sources` — the delivery gate BLOCKS without it.** This step exists because the
   gate got the requirement before this runbook did: `codex_delivery_gate.py` refuses a plan whose
   `design.image_sources` is missing, and an adapter that never mentions the field turns a design
   contract into a mystery failure at hand-off. One row per content image, each carrying its
   evidence token (grammar + the REFERENT RULE: `references/image-generation.md`), or the single
   string `"n/a - <why>"` on a deck with no content images.

   Classify the image's DEPICTED SUBJECT, not the slide topic: **real & specific** (a named place,
   a real product, a real person) → a REAL licence-clear photo; **generic-concrete** ("a warehouse")
   → generation is fine; **abstract** → native forms, no photo. A generated image CLAIMING
   photographic reality of a real thing is a fidelity bug, not a style choice.

   ```bash
   python3 scripts/fetch_images.py fetch "<subject>" --out <deck>/assets/sourced --slide N --limit 3
   python3 scripts/image_qc.py <deck>/assets/sourced --at <planned WxH inches> --contact-sheet
   #   ^ OPEN the sheet — reject watermarks, scaffolding, ugly or wrong-subject shots; --fix any
   #     EXIF ROTATION finding (this render loop ignores the flag, measured, so the photo would
   #     land sideways in a box sized for the wrong aspect with every gate green)
   python3 scripts/fetch_images.py adopt <deck>/assets/sourced <chosen file>
   python3 scripts/fetch_images.py ledger <deck>/assets/sourced --tokens    # the plan rows
   python3 scripts/fetch_images.py ledger <deck>/assets/sourced --credits   # the lines to RENDER
   ```

   `fetch_images.py` writes `sources.json`, and `check_image_provenance.py` (which the delivery
   gate calls) holds the plan against it. Two rows that fail there and nowhere else: a
   `searched (Commons, Openverse), none found → generated, flagged illustrative` rung with no
   RECORDED search behind it — and a search recorded as `unreachable`, which is a connectivity
   failure and never evidence that no photo exists — and an attribution-required photo whose credit
   never reaches a SLIDE (`deckkit.source_note` at the plate, or one line on
   `deckkit.sources_page`). The ledger's `--credits` output is that text.

   On the generate-a-template / plated branch, ground the prompt in what the subject actually looks
   like — `image_prompts.py --facts <visual-facts.md>` carries attributes you wrote after LOOKING
   at real reference photos. `generate_images_codex.py --ref-dir` stages those references beside
   the generation and REQUIRES `--ref-intent` (`generic-concrete` · `stylized-illustration` ·
   `fallback-rung`): a reference makes a fake ACCURATE, and a real subject that has a usable photo
   is not on that list — place the photo.

3a. **Write the shared record with `scripts/deck_gates.py`, not by hand.** The Codex path keeps
   its own `.codex-deck-evidence.json`, and the two files are different schemas — but a Codex run
   that also produces `.deck-gates.json` (any build script calling `deckkit.declare_delivery`
   does) gets the same benefit: `deck_gates.py init <deck-dir> --slides N` writes a fully SHAPED
   skeleton, and `deck_gates.py check <deck-dir>` reports EVERY shape problem at once. The
   delivery gates deliberately stop at the first problem in a section (their later checks read
   what the earlier one validated), so on a hand-typed record that costs one round-trip per wrong
   SHAPE — measured at six on one real build. 🔴 It is a shape pre-flight and never the gate: it
   never opens the .pptx.
   **Record the BUILDS choice while you are there** — `deckkit.declare_delivery(OUT, "presented",
   builds="static")` when the user opted out of appear-builds, so `NO BUILDS` stops firing on a
   deck that is static because they chose that, without `--static` being retyped every run.

3b. **Iterate through `deck_cycle.py`, not through hand-run steps — this is where the adapter's
   own worst time sink lives.** `python3 scripts/deck_cycle.py build_<deck>.py [--render]` runs
   build + lint (+ render + render-lint) in ONE call, which matters more on a bridged runtime than
   anywhere else: every step asked for separately is a full round-trip. 🔴 **It also carries the
   LOOP BREAKER, and the breaker is why this step is not optional here.** When the same fault
   (same slide, same lint code) survives 3 consecutive runs it escalates, and the next run is
   REFUSED if the build script changed only in its NUMBERS — an AST fingerprint blind to numeric
   literals decides that, not your intention. Re-derive the slide's layout by measurement
   (`fit_text`, measured ink, a form helper) and it runs; if a constant genuinely is the fix,
   `--nudge-again "<why>"` runs it and records the reason. A runtime that hand-runs
   `python3 build.py` then `lint_deck.py` gets neither the round-trip saving nor the guard, and the
   uncapped nudge loop is the one loop in this pipeline with no other ceiling.
4. **Make component decisions auditable.** Run `component_audit.py --json` after the build. For every
   detected cluster, use one of the audit's suggested components in the mapped slide builder or record
   a waiver with the exact slide, pattern, and bespoke reason. A real component emitter is accepted when
   it is called in that same slide builder and listed in the per-slide ledger; a deck-level
   `suppressed_by` value alone is not a Codex exemption. Do not waive a generic tile row merely because
   it already renders cleanly.
5. **Protect fragile local relationships in a visual contract.** Before the final render, create
   `visual-contract.json` for every manually composed local risk that a broad deck scan can miss:
   a callout next to a title, a component value next to a neighbouring diagram, or an icon whose glyph
   carries a specific meaning. Each zone names its exact text target or geometry, what it must clear,
   and a minimum `0.12in` gap; each semantic icon records the actual `lucide:*` build token and a
   sentence explaining its job. After render, run `codex_visual_contract.py` to recompute these checks
   against the final PPTX and produce small PNG crops for review. This is intentionally not a generic
   box-overlap lint: it makes the few high-risk relationships explicit without penalising deliberate
   overlays or bespoke composition.
6. **Resolve the palette as a MATRIX before building, and run the mechanical pre-flight before the
   first render.** Two checks that this adapter used to leave entirely to prose, both of which the
   shared path has since mechanised:
   - `python3 scripts/palette_audit.py` — computes every accent x ground pair at once and splits each
     hue into a FILL-only and a TEXT-safe token. The two-token rule was always stated; it is still
     easy to break, because the rule is per-PAIR and a build touches dozens. Record the resolved
     split in the evidence record's design section. 🔴 **The Codex delivery gate does NOT check
     contrast today** — `palette` and `contrast` appear nowhere in `codex_delivery_gate.py`, while
     the shared `.deck-gates.json` requires a `palette` field precisely because one deck shipped four
     separate contrast violations. Until the gate catches up, this step is the only thing standing
     between a Codex deck and that failure, so do not skip it on the grounds that nothing enforces it.
   - `python3 scripts/preflight_check.py <deck>.pptx --build build_<deck>.py` before the first
     whole-deck render, with `--selfread` / `--static` to match the delivery mode. It decides the
     mechanical half of PRE-FLIGHT — speaker-notes coverage, build timing, native charts, the as-of
     date, leaked `<slot>` text, a literal stride constant in a placement loop, a bar of sample
     means — plus four hard FAILs no geometry check can see: mono overflow, a mono face absent from
     the render box, **Latin -> full-width adjacency** (`原生 PPTX 。`, a defect that shipped on 5 of
     12 slides of a real deck and was caught only by a human at 5x zoom), and a non-positive text
     box. Exit 1 means not ready; `NOT CHECKED` + exit 2 means it could not run, which is never the
     same as clean. The five judgment items it prints as still-yours stay yours.
6b. **Read the composition cues before writing the review.** `python3 scripts/composition_cues.py
   <deck-dir>` reports seven measured cues per page and the deck-wide RANGE for each, from renders
   already on disk (~0.6s for 14 pages, no extra render pass). The RANGE is the point: a FLAT range
   is the finding no per-page look can produce — a deliberately dead deck that linted perfectly
   clean reported 6 of 7 cues flat. Cite the number, not the adjective. 🔴 REPORTED, NOT GATED:
   a quiet register and a cluttered mess share a low colorfulness, and this skill protects the
   first, so never turn it into a threshold.

7. **Ask the post-build review question first, then review by lens.** Once the render self-check
   is clean, post the rendered deck (contact sheet + slide PNG paths) and ask the ONE post-build
   question — `fast` (pre-selected default, ~10–20 min) · `standard` (~30–60 min) · `thorough`
   (~1–2 h) · `none` — with cost and what-is-skipped stated in the option text, exactly as
   SKILL.md's post-build review question specifies. In plain Codex chat this is a typed question,
   not a fake form. `none` is only ever the user's own typed answer. Then, at `standard` or `thorough`, dispatch the
   normal two focused critics separately: content/fidelity and design/layout/legibility. Each final
   review is a separate JSON file, has full-deck coverage, declares its lens, consents, and records the
   SHA-256 of the final PPTX it reviewed. The review must also record `reviewer: {origin, identity,
   fresh_context}`. `origin: isolated` or `human` is the normal path; `self-review` is allowed only
   with a named `critic-independence` waiver and must be reported as self-audit, never as independent
   consent. The design review's `probes` must include one `hotspot_checks` row for every visual-contract
   zone and one `icon_checks` row for every semantic icon, each with an observed-pixels note. A review
   that lists both lenses is not a substitute for two independent records in this adapter. For a full
   `thorough` panel, also preserve the arbiter's final fix-confirmation JSON; the original skill's
   `thorough light` route remains two focused critics.

   🔴 **Write the effort tier into the evidence record, and its tier-specific companion field —
   the gate reads them and no other file names them.** `review_effort` must be `fast` |
   `standard` | `thorough` | `none`; `standard` needs nothing extra. The other tiers each
   require one more key, and the gate rejects a companion still holding its `<placeholder>`:
   - `fast` → **`fast_basis`**: a >=12-character record of HOW the tier was reached — the user's
     post-build answer, or `post-build default — auto/not asked` on a non-interactive run.
     `fast` is the post-build DEFAULT, so the basis is not an opt-in proof but an honesty
     record: chosen-with-the-deck-visible and defaulted-because-nobody-was-there are different
     facts and the hand-off `review:` line must tell them apart. At `fast` the single
     `general`-lens review carries BOTH lenses' probe rows — including the visual-contract
     `hotspot_checks`/`icon_checks` the gate cross-examines.
   - `none` → **`none_opt_in`**: a >=12-character record quoting the user declining review AT the
     post-build question, with the rendered deck visible. 🔴 `none` is never a default, never
     derived, never an auto pick — the gate refuses the tier without the quoted decline, and
     refuses it again if any critic review is attached (record the tier that actually ran). The
     deterministic visual-contract recompute still runs at `none`; only the critic attestation
     is waived with the loop.
   - `thorough` → **`thorough_panel`**: `{scope: "light"|"full", record: "<>=12 chars>"}`.
     `scope: "full"` additionally requires the **`arbiters`** entries the gate cross-checks.

   Run `python3 scripts/codex_delivery_gate.py --init <path>` to get the rest of the skeleton
   (`interview`, `arbiters`, `waivers`, …); it is the authoritative shape of the record.

## Evidence record and gate

Create the hidden record beside the deck once the design direction is known:

```bash
python3 scripts/codex_delivery_gate.py --init .codex-deck-evidence.json
```

Fill it from actual artifacts, not memory. The v2 record binds the final PPTX and build script to their
SHA-256 hashes; stores the source/claim ledger, content and design checkpoint records, **both
competitions — the CONTENT arc (`content.arc`: the arc that won, the ones it beat with the clause that
lost each, and `arc_divergence.py`'s verdict) and the DESIGN direction** (`design.direction`), **the
governing picture** (`design.concept`: chosen + the two it beat), per-slide form
ledger, four clean-branch direction tokens and preview, final rendered signature proof, categorical
icon assets, visual-contract manifest/result, and two separate critic JSON files.
🔴 **A WEB-RESEARCHED deck (`source_mode: "web"`) additionally carries the three research floors from
`content-planner.md` §2(e):** `content.coverage` (全面, the domain enumerated + swept), `content.lifecycle`
(准确/全面, every featured product/version/entity checked live-vs-discontinued as of today — a headlined
dead/renamed thing is a defect, not a warning), a `content.provenance` digest (`checked/confirmed/fixed/cut`,
each fact corroborated ≥2 *independent* credible sources; MED facts labelled "per public reporting"), and a
`confidence` tier on every `claim_ledger` row. `codex_delivery_gate.py` now requires all four for a web deck,
so the Codex path and the shared content checkpoint enforce the same floors — closing the gap where a
no-source deck shipped thin and headlined two discontinued products.
*(All three were missing. This record bound the design competition to a hashed `directions.html` while
recording nothing about the arc — backwards by the skill's own reckoning, since a wrong form costs one
slide and a wrong arc costs the design plan and the build under it. `design.concept` had simply never
been added after `render_deck.py --gate-check` began requiring it, so a bridged run could satisfy this
gate with a design nobody had chosen a concept for and then fail the shared one.)* Every proof is
re-read and the critic/signature/visual-contract proofs must name the final deck hash. Keep the record
with `.deck-gates.json`; it is a workflow artifact, not a user-facing deck document.

After the final render and lint, produce the component JSON and run the gate:

```bash
python3 scripts/component_audit.py build_<deck>.py <deck>.pptx --json > components-final.json
python3 scripts/codex_visual_contract.py <deck>.pptx \
  --manifest visual-contract.json \
  --build-script build_<deck>.py \
  --renders render \
  --crops visual-crops \
  --out visual-contract-final.json
python3 scripts/codex_delivery_gate.py \
  --lint lint-final.json \
  --components components-final.json \
  --build-script build_<deck>.py \
  --evidence .codex-deck-evidence.json \
  --receipt .codex-delivery-receipt.json

python3 scripts/codex_handoff_guard.py \
  --receipt .codex-delivery-receipt.json \
  --deck <deck>.pptx
```

The gate blocks a Codex hand-off on remaining hard lint, missing pixel checks, undersized body text,
unresolved card/type/leading warnings, **four or more distinct deck-level monotony signals with at
least one structural among them** (the same composite `lint_deck.SAMENESS_CODES` drives on the shared
path — imported, never copied, and deliberately a COMPOSITE rather than seven more per-warning rows,
because any single monotony signal is legitimate on its own and a per-warning bar would refuse decks
the shared gate correctly ships), an untraced content plan, missing checkpoint evidence, a stale
signature image, unexplained component clusters, missing required icons, a failed visual-contract zone,
icon-semantic drift, absent design proof, **an unrecorded palette split** (`design.palette` — the
resolved FILL-only vs TEXT-safe pair per `palette_audit.py`; a hue that reads fine as a fill can
measure 2–4:1 as small text on the same tint), or a focused critic record that fails the normal JSON schema,
skim checks, reviewer-provenance requirement, or visual-probe coverage. Fix the deck first. A waiver is
valid only when it names the exact issue and a meaningful reason; it is a design decision, not a generic
`accepted` flag. It cannot waive source traceability, final-render binding, visual-contract recomputation,
or critic schema validity.
The gate also re-runs `component_audit.py` against the recorded final PPTX and build script, so a stale
or hand-authored component JSON cannot certify the deck.

The receipt is written only after `CODEX DELIVERY GATE: PASS`; the final hand-off guard hashes the
actual PPTX again. **Do not hand off a Codex-verified deck, expose its file link, or use an output
citation unless `CODEX HANDOFF GUARD: PASS` is in the current run log.** If a different backend is
required, disclose it as an **unverified draft — Codex gate not applicable**, rather than treating a
clean render or generic PPTX inspection as equivalent proof.

This command is **not** part of Claude Code's hand-off and must not be added to its default pipeline.
