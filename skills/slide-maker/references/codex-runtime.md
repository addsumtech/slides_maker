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

Read this before Step 2, then carry its evidence through the remaining steps.

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
   Build and render the THREE anchor slides before the rest, as the normal anchor-proof rule requires
   (signature · the densest planned page · the key data/conclusion page — SKILL.md Step 4). One build
   script, one render call; `design_plan.signature_proof` is the role-bearing list both gates check.
2. **Write a focused build contract.** Declare type tokens before coding. On a 10in-wide 16:9 canvas,
   target body text at least 13.5pt for presented/text-heavy delivery and 12pt for self-read; a larger
   display token (normally at least 32pt) must create a real focal point. Reduce copy or split slides
   before reducing the body token. For CJK paragraphs leave deckkit line spacing unset unless the plan
   names a different, tested value.
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
