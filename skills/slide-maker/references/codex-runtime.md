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
- **Taste-sensitive calls that stay explainable:** components, icon dosage, and form variety. Do not
  turn these into quotas. When the normal component or icon choice is intentionally wrong for this
  deck, record a slide-specific waiver and explain why.

Never use this adapter to prohibit bespoke work. A bespoke composition may still be the signature
move; the gate only rejects an *unexamined* hand-roll that duplicates a library component's known
geometry guarantees.

## Codex runbook

Read this before Step 2, then carry its evidence through the remaining steps.

1. **Make design visible before building.** On the `design a clean one` branch, create the normal
   direction preview and wait for the user's pick. In plain Codex chat, use the HTML preview or
   rendered archetype slides; do not replace the preview with a prose palette description. Keep the
   exact direction tokens and run the normal diversity check, rather than claiming four colorways are
   four directions. If a user says to decide, record the auto carve and the rejected alternatives.
   Build and render the signature slide before the rest, as the normal signature-proof rule requires.
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
6. **Review by lens, not by one permissive generalist.** At `standard` or `thorough`, dispatch the
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
   `standard` | `thorough`; it defaults to `standard` when absent, so a standard run needs
   nothing extra. The other two tiers each require one more key:
   - `fast` → **`fast_opt_in`**: a >=12-character record of the user asking for it. 🔴 `fast` is
     opt-in only and never derived, so the gate refuses the tier without this. **This field is
     not in the `--init` skeleton** — it is the one gate requirement that is otherwise
     discoverable only by reading `codex_delivery_gate.py`, which is why it is named here.
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
SHA-256 hashes; stores the source/claim ledger, content and design checkpoint records, per-slide form
ledger, four clean-branch direction tokens and preview, final rendered signature proof, categorical
icon assets, visual-contract manifest/result, and two separate critic JSON files. Every proof is
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
  --evidence .codex-deck-evidence.json
```

The gate blocks a Codex hand-off on remaining hard lint, missing pixel checks, undersized body text,
unresolved card/type/leading warnings, an untraced content plan, missing checkpoint evidence, a stale
signature image, unexplained component clusters, missing required icons, a failed visual-contract zone,
icon-semantic drift, absent design proof, or a focused critic record that fails the normal JSON schema,
skim checks, reviewer-provenance requirement, or visual-probe coverage. Fix the deck first. A waiver is
valid only when it names the exact issue and a meaningful reason; it is a design decision, not a generic
`accepted` flag. It cannot waive source traceability, final-render binding, visual-contract recomputation,
or critic schema validity.
The gate also re-runs `component_audit.py` against the recorded final PPTX and build script, so a stale
or hand-authored component JSON cannot certify the deck.

This command is **not** part of Claude Code's hand-off and must not be added to its default pipeline.
