# Orchestration — parallel section fan-out for large decks

**Default: don't.** For a normal deck (~6–14 slides) a *single* author writing one
build script is both faster and higher-quality — the cost is thinking and reviewing,
not writing the file, and one author keeps the palette, grid, chrome, narrative arc,
and one-message thread coherent for free. Reach for fan-out only when it actually
pays:
- **Large decks (~15+ slides)**, where authoring the slides genuinely dominates time.
- **Independently-sourced sections** (different papers / datasets / product areas)
  that can be researched and drafted in parallel.

When you do fan out, the rule that protects quality is: **centralize coherence, fan
out only the independent work.** One coordinator owns the comprehension brief, the
plan/arc, and a single shared style module; sections (not single slides) are authored
in parallel against that style; then everything is assembled into one deck and judged
by an independent critic panel.

> Why sections, not one-agent-per-slide-with-neighbor-chat: a `.pptx` is a single
> file (no clean slide-copy API — per-slide merging is fragile), and a deck's quality
> lives in *cross-slide* consistency and arc. N independent slide-agents drift and
> fight the artifact; the wins (understanding, the critic rounds) don't parallelize
> per-slide anyway. Sections + a shared style module capture the real parallelism
> without the drift. "Neighbor awareness" is a *global* property — the coordinator
> supplies each section the context of its neighbors; it is not pairwise gossip.

## Table of contents
- Actor side — coordinator + parallel section authors
- Critic side — independent panel + routing (the "second orchestrator")
- Checklist / gotchas

## Actor side — coordinator + parallel section authors

1. **Coordinator does the non-parallelizable core itself (one owner) — two minds, in sequence.**
   Both the CONTENT and the DESIGN of a large deck are owned centrally; only the *authoring*
   fans out. On a large deck the coordinator *is* these two planner minds (or dispatches each
   once); like them it may fan out *reading* across the independent sources, but it must never
   split the brief, the arc, or the design system across the section subagents — that one owner
   is what keeps the deck coherent.
   - **Content-planner mind → CONTENT checkpoint** (`agents/content-planner.md`, SKILL.md Step 1):
     - the **comprehension brief** — one mind holds the through-line,
     - the **plan/arc** (Step 1) — write each slide's takeaway, then **group slides into
       contiguous sections** and assign each section its **role** and its **page range**
       (`START_PAGE`).
     Approve the arc + per-slide takeaways at the **Step-1 CONTENT checkpoint** before any design.
   - **Slide-design mind → DESIGN checkpoint** (`agents/slide-design.md`, SKILL.md Step 2):
     - **`style.py`** — the single source of truth for palette, `FONT`, title/footer
       chrome, and layout constants (copy `references/examples/style_example.py`, tune to
       purpose via `design-by-purpose.md`). Sections never redefine colours or chrome.
     - the **rhythm** + a **per-slide design table** — each slide's **form · protagonist ·
       motion**, grouped so every section carries its own design rows.
     Approve the design language + rhythm + per-slide design at the **Step-2 DESIGN checkpoint**
     before fanning out authors.

2. **Fan out one subagent per section, in parallel** using the host runtime's available
   multi-agent/subagent tool (in Codex, discover multi-agent tools with `tool_search` if
   they are not already exposed). Give each subagent: the comprehension
   brief, the full plan, **`style.py`**, **its** section's role + slide takeaways +
   **its per-slide DESIGN rows (form · protagonist · motion) from the design table** +
   `START_PAGE`, and a one-line summary of the **neighbouring** sections (so seams and
   transitions are clean) — so a section author never skips the art-director stage. Each
   subagent:
   - writes `section_NN_<name>.py` exposing `build_section(prs)` that imports `style`
     and appends its slides (copy `references/examples/section_example.py`),
   - **self-renders just its section** with `assemble.preview_section(...)` →
     `render_deck.sh`, looks at the PNGs, and optimizes (same style/base as the final
     deck, so preview == final),
   - returns the finalized module path.
   Parallelize **asset prep** the same way (figure crops, equation PNGs, native
   diagrams) — these are independent and a real time win.

3. **Assemble into one deck** (`scripts/assemble.py`):
   ```python
   from assemble import build_deck
   build_deck("~/Downloads/<deck>/<deck>.pptx",
              ["section_01_intro.py", "section_02_method.py", ...],  # plan order
              template="<brand.pptx>")   # or omit for a blank styled deck
   ```
   One base deck, every `build_section` run in order — one file, no XML merge, no drift.
   `build_deck()` (and `preview_section()`) run the 🔴 build-time geometry gate —
   `deckkit.lint_layout(prs, strict=True)` — before saving, so the sectioned path has the same
   never-save-with-CRITICALs floor as a single-author build (`lint=False` is debugging-only).
   Per-section critics list their SECTION's page range in `slides_opened` (the coverage gate is
   scoped to the assigned range — `agents/critic.md`); the whole-deck coherence critic covers
   every slide.

## Critic side — independent panel + routing (the "second orchestrator")

Render the **assembled** deck, then run the critic as a panel (this is the high-stakes
pattern from step 5, made explicit):
- Dispatch the dimension critics **in parallel** — content/fidelity, design/layout,
  back-of-room audience (`agents/critic.md` + `review-rubrics.md`). For very large
  decks, optionally add **per-section critics** plus **one whole-deck critic** whose
  only job is **coherence, arc, and seams** between sections.
- The coordinator **merges and de-dups** their findings, then — before routing — runs
  the **arbiter pass** over the candidate findings in parallel (like the panel;
  `agents/arbiter.md` + the promote/discard rule in `review-rubrics.md`), and **routes
  only the *promoted* findings** to the section subagent that owns that slide (or fixes
  them in the module), re-assembles, re-renders, and re-critiques. So a section author
  never burns a round on a false-positive, and a cross-section coherence finding is
  validated before it forces a re-assemble. Stop at consent / round cap (step 5).
  *Scaling:* on a very large deck the per-section + whole-deck critics already
  double-cover, so the arbitration can **fold into the whole-deck critic's pass** rather
  than spawning separate arbiters; arbiter **job 2** (fix-verification) re-checks the
  promoted findings on the re-assembled deck, focused on the touched sections + their
  seams.

This *is* the "two orchestrators communicating" idea — realized the way the harness
actually supports it: a round-based **actor-coordinator ↔ critic-panel** loop with
finding-routing, **not** a persistent peer mesh. Keep the critic **independent** — it
judges the assembled pixels, it does not co-design — because that independence is what
makes its verdict worth anything.

## Checklist / gotchas
- Sections **import** `style`; they never redefine palette, font, or chrome.
- The coordinator assigns `START_PAGE` per section so page numbers stay continuous.
- Assembly order = plan order; the arc is the coordinator's responsibility.
- Animations (`anim.py`) are added **inside** a section's `build_section`, per slide.
- Output still lands in `~/Downloads/<deck>/` (the normal rule); the assembled `.pptx`
  is the deliverable, with a `render/` of the final PNGs (the `.pdf` and `viewer.html` are the
  reserved hand-off pair — `render_deck … --deliverables`, generated once the deck is final). Section subagents' self-renders no longer drop a PDF beside their section deck (the PDF is a
  reserved deliverable now), so there is nothing to clean up at assembly.
- If the deck is small, skip all of this — one build script is the right tool.

**Final rhythm-normalization pass (required after assembly).** Section authors each see only their
slice, so seams show at section boundaries: two dashboards butting together, the same skeleton three
slides running, colour temperature jumping. After `assemble.py`, ONE mind (the coordinator) re-reads
the assembled deck's rhythm map end-to-end — and the render-time lint's `sim↑` skeleton-similarity
column + `LAYOUT SAMENESS` warning now measure exactly this across boundaries. Fix seams by reordering
within a section or swapping one slide's skeleton, then re-render.
- **The deck-level `signature move` has named owners — plural, because it is CARRIED.** The
  `signature move:` line names a signature slide **and a `carried_by:` set of 2–3 slides** where the
  same idea does structural work; on a fan-out those slides can sit in DIFFERENT sections, and an
  idea carried by two authors who never compared notes is how a carry becomes a coincidence.
  So the coordinator hands the full line — signature slide **plus every `carried_by:` slide** — to
  **each** owning section, names which one is the signature slide, and requires the carry to be
  structural (the motif becoming that slide's geometry), not a stamped repeat. **Run the Step-4
  SIGNATURE PROOF once, centrally, on the signature slide BEFORE the sections fan out** — a proof
  per section would race, and a wrong signature discovered after N sections are authored is exactly
  the cost the proof exists to avoid. It's a single deck-level idea, not a per-section decision, so
  the coordinator also **hands that author the `signature move:` line explicitly**
  (it lives in the deck-level Design language, not in the per-slide form·protagonist·motion rows the
  fan-out itemizes). This post-assembly pass then **confirms the ONE signature move landed** (or, on a
  `bold` dial, the ≤2 beats) and did not get duplicated per section — the whole-deck coherence critic's
  distinctiveness axis is the backstop.
