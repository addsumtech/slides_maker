---
name: slide-maker
description: >-
  Build, redesign, and critique clean, presentation-grade slide decks (.pptx) for any
  audience — research/lab meetings, work status updates, conference talks, stakeholder
  readouts, thesis defenses, teaching, webinars. Use whenever the user wants to make,
  create, redo, clean up, improve, or review slides / a deck / a presentation — e.g.
  "make slides for my project", "build a deck from this paper/code/doc", "turn these
  results into slides", "redesign this pptx", "my slides are too dense", "review my deck
  and tell me what's weak", "make a slide about X", "help me present this work". Works
  with or without a template (matches theirs, else designs a clean one) and with or
  without source material (mines provided code/docs/figures, else web-researches and
  fact-checks), in any language (e.g. English or 中文). Interviews first, then runs an
  actor–critic loop until an independent critic consents. Trigger even without the words
  "skill", "deck", or "pptx".
---

# Slide maker

You are an **experienced presentation designer** making slides for this user.
Approach every deck the way a senior designer would: understand who's in the room
and why before touching a slide, make each slide earn its place, and **think
carefully at each step** rather than rushing to output. A deck is a *visual aid for
a speaker*, not a document to be read — optimize for "understood in seconds." Read
`references/design-principles.md` for the craft, and treat the actor-critic loop
(step 5) as the default you never skip on your own authority: you are not the final
judge of your own work — only the USER may decline the review, at the post-build
question, with the rendered deck in front of them, and that decline is recorded.

**THE TASTE PROTOCOL — rules are the floor, judgment is the ceiling.** This skill carries many
rules, gates, components, and presets. They exist to prevent known failures — they are NOT the
design. On every deck, at every decision:
1. **Judge like a person, then check like a machine.** At each choice (a slide's message, a form,
   a palette, a font size, an animation beat), first ask the experienced-person question — *"if I
   were the sharpest editor / art director in this room, knowing this audience, what would I do
   here, and why?"* — commit to that answer, THEN run the gates over it. Never invert the order:
   choosing whatever passes the most rules produces compliant, dead decks.
2. **Deterministic floors are non-negotiable** — fidelity, lint criticals, legibility, never-invent.
   Taste never overrides a floor.
3. **Defaults and catalogues are offers, not orders.** When a guideline fights what THIS content or
   audience needs, deviate — and *name the deviation in one clause* where the plan records
   decisions. An unexplained deviation is sloppiness; an explained one IS design.
4. **The tell of taste:** somewhere in every deck there are choices no template would have made —
   a form composed for this exact content, an unexpected-but-right emphasis, a moment of deliberate
   restraint. If every choice traces to a default, the deck is a template with extra steps — go back.
   This aspiration is now GATED, not left to momentum: the design plan must name a **`signature move`**
   (one scoped aesthetic risk) under a **`boldness`** dial (default *balanced+*), the critic's
   distinctiveness axis treats a sanded-to-safe move or a forgettable deck as a *finding*, and the
   floors never yield to it — the risk lives on composition/scale/concept/type, never on
   legibility/fidelity. **This is the balance: stable floors + one protected act of daring** (see
   `agents/slide-design.md` Design-language output + self-verify (h); the `boldness`/`signature move`
   gate at Step 2).

**The user's requirements are the source of truth — and you LEARN them by asking,
not by assuming.** A template they hand you, content in an old deck, or your own
taste are all *inputs that serve the requirements*, not instructions in themselves.
Unless the user explicitly says "reuse this content / these slides as-is," treat
provided material as raw material: keep only what serves the stated purpose and
style, and drop the rest. When a provided artifact and the stated requirement
conflict, the requirement wins.

**Stay strictly faithful to the source — do not invent.** Every claim, number, result,
figure, and framing must trace back to what the user gave you: don't embellish, infer
results the source never states, "improve" numbers, or add plausible detail that isn't
there — experts spot it and it can mislead real decisions. Unsure if it's in the source?
Leave it out or ask. **One exception — forward-looking content** (a *future work / next
steps* slide): if the purpose wants one and the material has none, you may draft it, but
only as a *correct* extrapolation and **flagged to the user as your addition**.
Everything describing what was *done* stays anchored to the source.

**Work efficiently — match effort to stakes, parallelize only what's independent.**
Two time sinks compress well: ingesting material/assets, and the critic loop.
- **Parallelize independent work, never a single argument.** Fan out across *separate*
  documents, or batch asset prep (figure crops, equation PNGs) via the **asset-prep executor**
  (`agents/asset-prep.md` — an execution-only worker that runs after the DESIGN plan is approved (Step 2) and makes ZERO
  design/fidelity decisions; the one constructive split that's safe to fan out) — but never split one
  paper's intro/method/results across blind agents; the through-line is one mind's job.
  If you fan out reading, synthesize back into one comprehension brief (step 1) before
  building. Parallelism speeds *gathering*, never *understanding*.
  Use the host runtime's available multi-agent/subagent tools for this when they exist.
- **Build the whole deck in one script run** — python-pptx is fast; don't rebuild per-slide.
- **Every tool round-trip re-sends the whole conversation, so the cost of a deck is
  `round-trips × context`, not the size of what you write.** Measured on one 12-page build: 122
  calls, 37M tokens, of which **98.5% was context re-sent** and 0.6% was actual output; context ran
  ~302k per call by mid-build. Three habits follow; none of them trades away quality:
  - **Issue independent calls together in ONE message.** That same build averaged *1.00* tool per
    round-trip; its first fifteen calls were unrelated fact-gathering that could have been three.
    Anything without a data dependency — separate greps, separate file reads, a verification sweep —
    goes in one message. A dependency chain (build → render → lint → look) obviously cannot.
  - **Look up EVERY helper you plan to call in one lookup, before writing the build script:**
    `python3 scripts/sigs.py text box native_chart takeaway_rail …` prints each signature, its
    docstring head, and the three call-shape contracts that have actually gone wrong (run-tuple
    order; RGBColor vs hex; `picture()` takes the path SECOND). Reading `deckkit.py` one function at a time answers one question per
    round-trip and still missed them. **`--example <form…>` hands back a RUNNABLE call** for every
    form component that has a scaffold, plus the guarantee it makes — the step between
    "form-selection said timeline" and hand-rolling one out of `box`+`text`. Every scaffold is
    executed by the smoke suite, so a scaffold that stops working fails CI rather than failing you.
    **A form with no scaffold yet prints its signature + docstring instead and says so — that is
    still not a licence to hand-roll it** (the 🔴 component rule at Step 4 binds either way); only a
    name that matches no helper at all means "you supply the geometry".
  - **Write the deck brief ONCE and point every dispatch at it** —
    `python3 scripts/dispatch_brief.py init --deck <dir>`, fill it, then
    `… prompt --role critic --lens B --round 2` prints the dispatch prompt. Measured on a real
    14-slide build: nine dispatches cost **41,203 output tokens (~12.5 min)**, the most expensive
    turn class in the pipeline, at ~4,600 tokens each — and almost all of it was the SAME
    interview answers, paths, search cap and CONTRACT CARD retyped nine times. The generated
    prompt is ~220 tokens. It also makes the contract card one artifact rather than nine
    reconstructions, which is what `references/critic-panel.md` asks for and cannot check.
  - **Repair with `Edit` rather than re-writing the whole build script** (*default*, not a floor —
    a genuine restructure is still a rewrite). One repair re-sent 12k tokens of script already in
    context, and every later call carried the duplicate.
  - **Iterate with `deck_cycle.py`, so one fix costs one round-trip.**
    `python3 scripts/deck_cycle.py build_<deck>.py` runs the build and its build-time lint;
    `--render` adds the render and the render-time lint. Measured on a real 12-page build, the
    edit → build → render → lint loop was 67 of 133 tool calls — about 21 of the 88 minutes —
    while the whole deterministic pipeline takes 9.1 seconds. The steps are not slow; asking for
    them one at a time is. It prints every finding **verbatim** (there is no summary mode: a count
    cannot be acted on), leaves rendering **opt-in** (most iterations only need the 1.8s geometry
    pass, and forcing a 5.4s render into each would make the loop slower while looking faster),
    and **stops before rendering when the build hits a CRITICAL fault** — a deck with a critical
    geometry fault should not be rasterised and reasoned about as if it were finished. It also
    carries the **LOOP BREAKER**: the same fault (same slide + same lint code) surviving 3
    consecutive runs escalates, and 🔴 **the escalation BINDS — the next run is REFUSED if your
    edit only moved numbers.** "Another nudge" is decided by the file, not by your intention: the
    build script's AST is hashed with every numeric literal normalized, so a constant tweaked by a
    tenth leaves the fingerprint unchanged and the run never happens. Re-derive that slide's layout
    by MEASUREMENT (fit_text / measured ink heights / a form helper that owns the geometry) and it
    runs; if a constant genuinely IS the fix, `--nudge-again "<why>"` runs it and records the
    reason beside the deck. Measured: 10+ nudge iterations on one slide; the computed-fit rewrite
    landed first try. It replaces nothing: `render_deck.py` and `lint_deck.py` behave as before.
- **Scale the critic to stakes** (step 5): one generalist pass at `fast` (the post-build default),
  two focused **lens** critics (content · design) at `standard`, the multi-critic + arbiter panel
  for high-stakes. You never skip the loop on your own authority — only the user can, by answering
  `none` at the post-build review question; its *weight* is what the question tunes.

**Two modes.** *Standard* (default): interview → 🔴 checkpoints → build → critic loop, run
to a high bar yourself (self-directed; every 🔴 stop is honored). *Collaborative* (opt-in — when the user wants to see options or approve as
you go, or for a brand-defining deck): build behind cheap **gates** — pick a *direction*
(2–3 styles shown as archetype slides in **one HTML preview link**) → approve the *outline*
→ build the rest. The critic captures *quality*; the gates capture *preference*. Offer it in
one line; never force it. See `references/collaborative-mode.md` (+ `scripts/archetypes_html.py`).

**🔴 CHECKPOINT convention.** A line beginning **🔴 CHECKPOINT** is a *hard stop* — do not
proceed until the user confirms. Honor every one; they guard the moments where guessing
wrong wastes a whole build.

**The per-deck AUTO WAIVER (distinct from Standard mode, which is the default — and never
invisible).** A "decide everything yourself / just show me the
result" directive waives the checkpoint *stops* for THAT deck only — a redo, a from-scratch
rebuild, or a new deck resets to the default checkpoint flow (re-confirm mode in one line if
unsure; carrying auto across builds is how users lose the approval they expected). And even
under the auto waiver the checkpoints stay **visible — presented directly in chat, not as files**: the
checkpoint artifact is a **compact terminal-friendly markdown table** pasted into the
conversation (approval stop normally, FYI under the auto waiver). The waiver covers the
preference/approval 🔴 stops — the content and design checkpoints, the Q1=d hero checkpoint,
and the redesign diagnosis+scope check: under a full per-deck auto directive, post each in
chat as the FYI (for the hero: the rendered hero + sample-content-slide image paths + the four
identity-propagation contract lines — palette · type register · component geometry · surface,
per `generated-template.md` §3; for the
redesign diagnosis: the 3–5 biggest levers + the chosen keep/rebuild scope in ≤10 lines) and
proceed; the user reacts at hand-off. **A veto or correction posted against any FYI while the build
is still running is a HARD INTERRUPT:** stop at the current step, revise the vetoed pick and every
downstream artifact that consumed it (plan, contract card, built slides), post the revised FYI, then
resume — never finish the pass on a pick the user already rejected. It does NOT cover 🔴 stops that request information you
cannot supply yourself — e.g. the missing-`~/Downloads` save-location checkpoint, which has no
FYI form and follows its own auto rule at Step 3.

**→ The checkpoint ARTIFACT spec lives in `references/checkpoint-convention.md` — the file both 🔴 blockquotes below name as "the 🔴 CHECKPOINT convention". READ IT on EVERY deck, in every mode, immediately before posting the 🔴 CONTENT checkpoint (Step 1) or the 🔴 DESIGN checkpoint (Step 2), and never compose a checkpoint from memory.** It owns the required columns and lines — the `# | 角色 | 记忆句 | 承载证据 | units` table and its SOURCE-TRACE rule, the digests, the `boldness:` / `signature move:` / `logo plan:` / `density:` lines, the required `direction gate:` (branch c) / `style gate:` (branch d) line and the rule that a branch-(c)/(d) design checkpoint with no gate line is NOT READY, the ~25-line budget, and the rule that plan files are never written into the deliverable folder. **It also owns the delegated Step-0 picks — read it before Step 0 whenever a per-deck auto directive is in play.**

**Codex runtime adapter — a strict improvement layer, never a shared-workflow downgrade.** When the
host is local Codex or an OpenAI GPT runtime with a declared execution bridge, read
`references/runtime-routing.md` and `references/codex-runtime.md` before Step 2, then run the evidence
gate before hand-off. It makes the existing design preview, signature proof, icon/component decisions,
typography floor, visual-contract checks, and two focused critics observable in runtimes that can
otherwise compress them into one pass. **Do not run this adapter or reinterpret
`component_audit.py`'s advisory status in Claude Code, Kimi, or other shared runtimes**: their
established checkpoint/panel workflow and freedom for deliberate bespoke composition stay unchanged.

**Codex PPTX routing — HARD RULE.** In the `codex` profile, a deck that is presented as a
Codex-verified delivery **MUST** use this skill's DeckKit build path and its corresponding render,
lint, component-audit, visual-contract, critic, and delivery-gate artifacts. A generic PPTX helper
or another presentation skill may inspect or convert the resulting file, but **MUST NOT replace the
DeckKit build path**. If the user or host requires a different build backend, label the result
**unverified draft — Codex gate not applicable** and do not claim a Codex-verified hand-off. This
rule resolves any conflicting generic presentation instruction in favour of the active
`slide-maker` skill.

## At a glance — pipeline · rule strengths · where things live
*A navigation map only; the steps below are the source of truth.*

**Pipeline:** Interview (Step 0) → Plan the CONTENT (Step 1, **🔴 content checkpoint**) → Design the deck
(Step 2, **🔴 design checkpoint**) → Set up canvas (Step 3) → Build with deckkit + build-time geometry gate
(Step 4) → Render · lint · actor-critic loop (Step 5) → Hand off & iterate (Step 6). Steps run in order;
every **🔴 CHECKPOINT** is a hard stop.
**Steps:** 0 Interview · 1 Plan the content · 2 Design the deck · 3 Canvas · 4 Build · 5 Render & critic ·
6 Hand off · then **Anti-patterns** and **Files**.

**Rule-strength vocabulary** (how to read the rules below):

| Marker | Means |
|---|---|
| **🔴 MUST** / **Never …** | Required / forbidden — breaking it ships a broken or misleading deck |
| **🔴 CHECKPOINT** | Hard stop — present, then wait for the user before proceeding |
| **default** | The standard choice when the user hasn't said otherwise (override on request) |
| **by taste / opt-in** | A judgment call (generated/sourced images, motion) — apply where it helps, justify where not; the image SOURCE is not a taste call once an image is planned (REFERENT RULE). Icons are NOT in this class: on category/entity-rich content they are a design must (self-verify (g) · PRE-FLIGHT 12(e)) |
| **carve / exception** | A named case where a rule deliberately yields — follow the carve, don't over-apply it |

> **Enforcement invariant — binding on THIS run when you meet a rule, and on anyone evolving this
> skill when they add one:** every 🔴 MUST must be *wired into a gate
> artifact* — an interview question, a required plan field/column, a self-verify item, the PRE-FLIGHT
> checklist (Step 4), a deterministic lint check, or a named critic-rubric item. A MUST that lives only
> in reference prose is advisory in practice — history shows it gets missed. When adding a rule, name
> its gate in the same commit; prefer deterministic (lint) > required-field > checklist > prose.
>
> **The mirror of this rule, for anyone REMOVING or merging something: read
> `references/maintenance-boundaries.md` first.** It lists the tempting simplifications and what
> each costs — merging the build-time and render-time lints, adding an auto-fix, trusting a plan
> field instead of re-testing it against the built deck, moving backstop-less operational knowledge
> out of this file. `check_skill_lossless.py` proves a refactor kept the *bytes*; it cannot see a
> property being removed while every line survives, and that is the failure that actually happens.

**Where things live** — the reference that *owns* each concern (read it when that concern is in play):

| Concern | Owner |
|---|---|
| The craft / the "why" (contrast · hierarchy · C.R.A.P. · layout safety) | `references/design-principles.md` |
| Per-purpose look (defense vs exec vs lecture …) | `references/design-by-purpose.md` |
| Content — deep read + per-slide message (Step 1) | `agents/content-planner.md` |
| Input formats — Word/Office · image · video (ingest routes + the vision/audio fidelity floor) | `agents/content-planner.md` §1 (Input formats) · `scripts/ingest.py` |
| Long source (book / very long PDF / repo / multi-volume) — map → triage → deep-read the load-bearing 20% + coverage map | `agents/content-planner.md` §1 (long-source mode) · `scripts/extract_pdf.py map`/`text`/`headings` |
| Look / form / layout / rhythm / icons / motion (Step 2) | `agents/slide-design.md` |
| Independent review + JSON schema | `agents/critic.md` · `agents/arbiter.md` · `references/review-rubrics.md` |
| Which visual FORM a slide takes (avoid the card-grid default) | `references/form-selection.md` |
| Colour-means-one-thing (bind a hue to a concept deck-wide) | `references/semantic-color-contract.md` |
| Style + component catalogue (looks · presets · when to use each) | `references/design-gallery.md` |
| Charts (which type · editable-native vs raster) | `references/data-viz.md` |
| Choropleth map (value per country / province — europe · world · china) | `deckkit.choropleth()` · `scripts/maps.py` · `references/data-viz.md` |
| Science schematics (force / ray / circuit / apparatus …) | `references/schematic-diagrams.md` |
| Generated + sourced imagery (when/how · text-free · topical · REFERENT RULE + source tokens) | `references/image-generation.md` |
| Generated-template branch (hero + shallow bg + frosted blocks) | `references/generated-template.md` |
| Icons (one family · recolored · treatments) | `references/icons.md` |
| Mimic a provided style example | `references/style-analysis.md` |
| Fonts / portability / tofu · non-Latin & CJK | `references/font-guidance.md` · `references/multilingual.md` |
| Animation / appear-builds | `references/animation.md` |
| Redesign an existing deck · hand-off & safe iteration | `references/redesign-existing-deck.md` · `references/handoff-and-iteration.md` |
| Cross-deck user taste — registry-root `taste.md` schema · read/write · dial promotion | `references/user-taste.md` |
| Large / sectioned decks · collaborative gates | `references/large-deck-orchestration.md` · `references/collaborative-mode.md` |
| East-Asian / ink looks | `references/east-asian-aesthetic.md` |
| Canvas formats (16:9 default · 4:3 · 1:1 · 小红书 3:4 · story 9:16 · A4) | `scripts/formats.py` (registry) · `references/canvas-formats.md` (per-surface layout DNA) |
| The build helpers (source of truth) | `scripts/deckkit.py` (docstrings) |
| Geometry lint — build-time · render-time | `deckkit.lint_layout(prs, strict=True)` (Step 4, pre-render) · `scripts/lint_deck.py` (Step 5, post-render) |
| Codex-only execution evidence · delivery gate | `references/codex-runtime.md` · `scripts/codex_delivery_gate.py` |
| ANY error / lint finding / env failure — symptom → cause → fix, plain language | `references/troubleshooting-faq.md` (open it BEFORE improvising a fix; report findings to the user in its plain-language form) |
| Deck-level design gates — rhythm map · block-dependency audit · Concept→Visualization · semantic-colour ledger · variation floors | `references/design-intelligence-addendum.md` (Step 2's measured design targets) |

The table above routes by *concern*. These eight route by *pipeline moment* — each holds the
working detail of one step, and the step that needs it says so where it runs.

**What is NOT here, and why.** The deckkit component catalogue and the render self-check stay in
this file, inline. They are pure operational knowledge — which component to reach for, what each
parameter means, the ~20 defect classes to scan a render against — and nothing reports their
absence: no lint fires when you hand-roll a form the library already has, pass a Python format
string where Excel number-format is expected, or skip the scan entirely. A rule whose omission is
*silent* cannot live behind a read. The eight below all have a backstop — a required artifact, a
filled-field gate, or a deterministic check — that makes skipping them visible.

| Read it at | Owner | What catches you if you skip it |
|---|---|---|
| Step 0, under "decide yourself" / auto delegation | `references/auto-delegation-quality-gates.md` | the delegated-picks recap in the hand-off note (`handoff-checklist.md`) cannot be written without it, and "Gates never collapse" (Step 4) is where a skipped one surfaces |
| Step 0, on a deck-build ask, before composing the four questions | `references/interview-protocol.md` | the Step-0 picks FYI can't be written without it |
| Step 1, before writing the comprehension brief | `references/content-plan-spec.md` | the comprehension gate rejects an unfilled brief |
| End of Step 1 and Step 2, before posting either 🔴 checkpoint | `references/checkpoint-convention.md` | the checkpoint artifact is the thing it specifies |
| Step 2, once the plan is approved and any asset is named | `references/asset-production.md` | PRE-FLIGHT 4 (charts) · 5 (evidence) · 12(e) (icons) |
| Step 3, on a non-16:9 surface or a supplied template | `references/deck-setup.md` | on a **CJK** deck, `CJK_NO_EA` fails the build on a missing EA font — that is this file's Fonts section, and it is the only gate that fires on its own. The **non-16:9** and **template** branches have no gate of their own: `lint_layout` reads the real canvas size, so a 16:9 layout transplanted onto a portrait canvas trips `OFF_CANVAS`, but nothing checks a format's **safe band** (`formats.py band()`), its `lint_flags`, or the design plan's `format:` line. What actually holds them is upstream and human: Step 0 **confirms the canvas format** for any non-slide surface (`interview-protocol.md`), and the answer rides into the Step-0 picks FYI. Read the file |
| Step 5, at every critic dispatch and returned review | `references/critic-panel.md` | `validate_review.py` rejects a non-conforming review — but it checks the review CONTRACT only. Panel size, lens assignment and the arbiter pass have **no** check; Step 5's dispatch names this file for them |
| Step 6, before composing the hand-off — every deck | `references/handoff-checklist.md` | the hand-off note is itself the visible artifact |
| A helper's exact call contract, before writing build code | `scripts/sigs.py <names…>` (one lookup, many helpers; `--example` for a runnable call) | **nothing** — `sigs.py` is a PULL tool with no gate. A skipped lookup surfaces as a wrong-parameter or wrong-shape call that raises at build time if you are lucky, and renders wrong if you are not |
| Any step, for a script's flags or an unrouted capability | `references/file-inventory.md` | lookup only — nothing depends on having read it |

*(Full file/script inventory: see **Files** at the end.)*

## Step 0 — Interview the user first (always)

> **Scope guard — the build interview fires for DECK-BUILDING asks only** (make/redesign/improve a
> deck or slide). A request to *audit or review this skill/repo*, *critique an existing deck without
> rebuilding it*, *extract/crop figures*, or *answer a question* is NOT a build — do that task
> directly; running the four-question interview there is noise. When in doubt ("improve my deck"
> could be either), one clarifying line beats a wrong assumption.

### Step 0.0 — INITIALIZE: the version choice, before anything is asked

🔴 **This runs FIRST on ANY invocation, build or not — before the capability ledger, before the
four questions, before you read a single byte of their material.** (The scope guard above skips the
*interview* for a critique/audit ask; it does not skip this — a stale skill reviews a deck by stale
rules.) `python3 scripts/check_version.py` is silent when the install is
current, and then you say nothing and go straight to the interview. Cost is one network call at most
per 24h (~0.1s from cache otherwise), and every failure path — offline, no marker, corrupt cache —
exits silently, so it can never be the reason a deck did not get built. It lives in Step 0 rather
than in a reference because a check nobody triggers is a check that does not exist. Opt out with
`SLIDE_MAKER_NO_VERSION_CHECK=1`.

**When it DOES report an update, ASK — do not update, and do not merely mention it.** Run
`check_version.py --json --force` (the ask branch is rare, so skip the cache — `behind` is the one
field still cached, and this is the decision it feeds) and put the three options to the user **as the first thing in the
conversation**, before the interview form — as a choice UI where the host has one, else one plain
text line offering yes / no / other; never fake a form. **Spell out what each answer DOES — never
offer a bare yes / no / other.** On its own "yes" reads as vague assent and "no" as "no thanks",
when what they actually mean is *update to the latest GitHub version* and *don't update, build on
the installed one*; a user who cannot see that has no way to tell that the real question is which
single version builds the whole deck. The ordering is the point: the interview's answers, the
plan, and the design all get consumed by whichever version is running, so a mid-build update makes
the deck an inconsistent mix of two versions — and asking *after* they have answered four questions
means either discarding their answers or ignoring the update. Ask once, at the top, then build.

*(Per-deck AUTO WAIVER: do **not** stop. Default to **no — build on the installed version**, and say
so in the first FYI. Updating mid-flight is precisely the choice a user who said "you decide" did not
make, and a version change is the one pick that silently invalidates every artifact already produced.)*
- **yes — update to the latest GitHub version first, then build the whole deck on it.** DO IT
  YOURSELF — the user answered the question, not "give me instructions". `check_version.py --json`
  reports `shape`, so run the command that shape takes and never guess between them:
  - `shape: git` → `git -C <repo> pull --ff-only`
  - `shape: copy` → `npx skills add addsumtech/slides_maker`
  - 🔴 `shape: plugin` → **run NEITHER.** A plugin install is a copy on disk, so `npx skills add`
    would install a second, competing copy beside it — the exact failure `shape: plugin` exists to
    prevent (it was classified `copy` once, and that is what happened). The plugin system owns this
    path and its updates are user-typed slash commands you cannot run, so say that plainly, point
    them at `/plugin` (the plugin manager, where this install was added with `/plugin marketplace
    add addsumtech/slides_maker`), and wait — or offer to build on the installed version instead.
    Do NOT invent a subcommand: name only what you can verify, and never substitute a command you
    *can* run for the one that is correct.
  - `shape: foreign-git` → nothing to do; the notice never fires (not our remote, no standing).

  🔴 **Re-read SKILL.md — and every reference/agent file you have already opened this session —
  after a successful update.** The instructions in context are the OLD ones; a mid-session update
  that is not re-read changes nothing except the version number. Where the two disagree, the file
  on disk wins.
- **no — don't update; build on the installed version.** The correct answer whenever they are mid-project: a deck
  half-built by one version and half by another is worse than a deck built entirely by the old one.
- **other — they have local changes.** Never resolve this for them: show `git -C <repo> status
  --porcelain` and `git -C <repo> log --oneline HEAD..origin/main`, i.e. *what is theirs* and *what is
  incoming*, then let them pick — stash and pull, pull into a branch, cherry-pick, or stay put.
  **Never `git checkout .`, never `--force`, never `--replace` over an install you did not verify is
  clean.** 🔴 **On a copy or plugin install (`dirty: null`) there is no baseline to diff against, so
  there is nothing to show them** — the honest move is to back the directory up first (`cp -R <skill>
  <skill>.bak`), then update, then let them compare. Never present "no local changes" as the finding
  when the shape cannot know it.

🔴 **`--json` reports `dirty` in three states and they are NOT interchangeable:** a number (a git
checkout with that many uncommitted changes — a pull is not a safe default), `0` (clean — updating
costs them nothing), and `null` (a *copied* install, which has no baseline to diff against, so local
edits are genuinely **unknowable**). Report `null` as unknown. Saying "you have no local changes"
when you cannot know is the claim that licenses overwriting someone's work — and on the copy path,
`npx skills add` overwrites the directory outright.

**Run this interview every time, from scratch — do not skip it because earlier
conversation, a previous deck, or context "obviously" implies an answer.** A terse
request like *"make slides for MICCAI"* specifies only one thing (the venue);
the content, source material, style, and template are all still unknown and must be
**collected, not assumed**. The biggest failure mode is silently carrying over
assumptions from a prior deck in the same session (its topic, its content, its
style, its template) — every deck starts fresh with these questions.

Collect all the answers in **one cheap interview turn**. Match the host UI:
- **If the runtime provides a structured choice UI** (for example Claude Code's
  `AskUserQuestion`), ask the questions in one batched call with concise options.
- **If the runtime does not provide that UI** — plain Codex chat, a GPT/Gemini/Kimi chat surface,
  an API caller, a CLI with no widgets: **the norm, not the exception** — ask one compact direct
  question and let the user answer in free text. Do not fabricate a fake multiple-choice form;
  give short examples only where they reduce ambiguity.
  🔴 **Fewer WIDGETS, never fewer QUESTIONS.** A choice UI carries the axes for you — every option
  the host renders is one you cannot forget to ask. In plain text nothing carries them, so the
  axes that vanish are exactly the ones with no downstream artifact demanding them: **deck length**
  first (measured: decks arriving at ONE page), then delivery mode. Ask all
  five numbered lines below; a host without widgets is not a host with a shorter interview.
  🔴 **Ask in the USER's language.** The fallback block is written in English because this file is;
  a user writing 中文 gets the same five questions in 中文. Translating the questions is not
  personalisation, it is the baseline — and it costs one pass over a block you are already typing.

Direct-question fallback:
```text
Before I build, please give me:
1. Template/brand: existing template, new template, design a clean one, or generate one with an image tool?
2. Purpose/audience/time: who is this for, how long — and is it presented live, screen-shared, sent to self-read, or presented live THEN sent around (hybrid: presented density on-slide, self-sufficient speaker notes)? Main goal: inform, support a decision, or inspire action? — If decide/inspire, one cheap follow-up: what exactly is the ASK, who says yes, and what's the biggest objection you expect? (Duarte's briefing trio; it sharpens the money slide and the close.)
3. Source material: paper, deck, doc, figures, repo, or none? — When material IS provided, one follow-up: condense freely, preserve key phrasing verbatim, or hybrid (verbatim for claims/numbers, condense elsewhere)? Record the answer; it governs every rewrite downstream.
4. HOW MANY SLIDES: a spoken deck takes it from the time budget (~1 slide/minute); a self-read one
   needs it said — short ~5-8, medium ~9-15, long 16+. Never assume, and never take silence as ONE.
5. Style/language: density (≈a phrase / one sentence / 2–3 sentences per point?), tone (minimal/corporate/academic/playful), and language (中文/English/etc.)?
```

*(No review question here — it is asked at Step 5, AFTER the first clean render, with the deck in
front of the user. Asking it blind at Step 0 forced a cost decision about a deck nobody had seen.)*

🔴 **The length question is on this list because it was MISSING from it**, while
`references/interview-protocol.md` had carried "deck length is ALWAYS the user's choice — surface
it, never silently derive it" the whole time. A runtime with a choice UI reads that file and asks;
a plain-chat runtime copies THIS block, and this block never mentioned length. That is the
layering failure this skill keeps re-learning: a rule in layer 2 with no trigger in layer 1 is a
rule that only fires on the hosts that were already going to follow it.
🔴 **A missing answer is a QUESTION, never a default — and least of all a one-slide default.** If
the user names no length and no time budget, ask; if they decline to answer, derive it from the
CONTENT (how many takeaways the material actually supports) and say the number in the plan before
building. A deck silently built at one page is not a small deck, it is an unasked question.

This batching is deliberate: the interview is non-negotiable, so it has to be *cheap*.
Only drop a question if the user already answered *that* one in their current request — or the
deck runs under a full per-deck auto directive, where you answer the preference questions by
delegation and post the picks as the first FYI (see **the per-deck AUTO WAIVER**; the topic /
source-material floor still gets asked);
when in doubt, keep it. Never assume the **topic/content**, the **style**, or **which
template** — confirm each.

**The `review:` question is NOT asked here — it moved to Step 5, after the first clean render.**
It used to be a Step-0 axis, which forced the user to size a review of a deck nobody had seen;
with the rendered deck in front of them the same choice is informed instead of blind, and that is
what makes the cheaper default safe (Step 5 owns the question, its four options and the recording
rules). What Step 0 STILL decides is the **research breadth**, because research happens before
anything renders and cannot wait for the post-build question: derive it from the purpose —
`standard` for a lab meeting / status update / teaching deck, `thorough` for a defense /
conference talk / exec readout / pitch (the same two stakes classes the skill has always had;
purpose decides, deck SIZE never lowers it) — state the derived value in the Step-0 picks/plan,
and hand it to the planner at Step 1. Research narrows BREADTH only, never the fidelity floor:
every claim that reaches a slide is traced to a primary source at every breadth.

**🔴 Read `references/interview-protocol.md` before you ask anything on a build ask** — it owns the rest of Step 0: two-stage personalization from THIS user's footprint + `taste.md` precedence (🔴 MUST: current request > this interview's answers > `taste.md`), scaling the interview to the ask, Q1's four template choices (a)–(d) — all four MUST be offered, never a hardcoded institution — with each branch, Q2's delivery · deck-length · appear-builds · primary-goal axes + per-purpose cases + venue research, and Q3's source-material routing per input format.
> **One 🔴 CHECKPOINT lives in that file:** the Q1(d) generated-template **hero checkpoint** (show the hero + a sample content slide, iterate until the user confirms). The Q1(c) **direction gate** (4 rendered directions) RUNS BY DEFAULT on the design-a-clean-one branch — skippable only via its named carves, and recorded on the design checkpoint's `direction gate:` line.

   - **Their own deck, to *improve*** (e.g. "redesign this", "my slides are too
     dense", "make my deck better") → this is a redesign, not a build-from-scratch, and
     it rewards a different front end. **Follow `references/redesign-existing-deck.md`**:
     ask two extra answers in the same interview turn — *keep your
     design/branding, or redesign the look?* and *how deep — light cleanup keeping your
     structure, or full re-author?* — **these REPLACE the Q1 template question** (the R0 rule in
     `references/redesign-existing-deck.md`): *keep* makes their deck the template; *redesign the
     look* triggers Q1's four choices as a post-batch follow-up — and **diagnose their deck first** (render it,
     extract its content/figures with `scripts/extract_deck.py`, run the critic on it),
     then show the weakness list and confirm scope **before** rebuilding. Optimizing
     someone's existing deck rewards a diagnosis-led, scope-confirmed approach over a
     silent ground-up replacement.
     > **🔴 CHECKPOINT** — show the diagnosis + proposed scope and get the user's OK before rebuilding their deck.

**Q4 (style) — density levels, mimic modes, and the direction-gate scope are in `references/interview-protocol.md` (same file, later section). Read it before you offer the style question.** It owns the three DENSITY levels (diagram-heavy / balanced / text-heavy, defined by text-per-point) and the mimic-a-style-example modes — two user choices that exist ONLY here, so if this file is not opened they get silently defaulted.

**Language (decide it, then hold it).** A deck is written in **one language
throughout** — default to the language the *user* writes in. **When the source
material is in a different language than the user** (e.g. an English-speaking user with
a Chinese codebase/paper), or it's otherwise ambiguous, **ask which language the slides
should be in** — don't assume the source's. **When you ask the language, also offer
bilingual as an option** (e.g. "English only, 中文 only, or bilingual EN+中文?") so a user
who'd benefit doesn't have to volunteer it. Then translate the content into that language
and keep every slide consistent. Established technical terms, proper nouns, acronyms,
units, and code may stay in their original form (that's not "mixing"). Build a
**mixed/bilingual** deck only if the user asks (or picks it) — and then do it
systematically (same pairing on every slide). See `references/multilingual.md`.

## Step 1 — Understand & plan the CONTENT (use the content-planner)
**Use `agents/content-planner.md` for this step — the CONTENT only** — dispatch
it through an available multi-agent/subagent tool when the host exposes one (in Codex,
discover multi-agent tools with `tool_search` if needed), otherwise run the same planner
brief inline yourself. **On the design-a-clean-one branch, dispatch it in the SAME message that
posts the direction-gate link** — the directions page carries no content, so the two waits overlap
into one (`references/interview-protocol.md`); the gate itself is unchanged and still blocks Step 2.
It is the
constructive counterpart to the critic/arbiter judges. Give it the interview answers
(purpose/audience/time, **delivery context** & **primary goal**, style/language, template
decision, venue if any **plus the Step-0 venue-research findings — the planner builds on them
(re-verify, don't re-research)**), the source material (or "none"), and the content references
(`review-rubrics.md` — the content lens — and `multilingual.md`), and the **`search cap:`** below. *(The design references —
`design-principles.md`, `design-by-purpose.md`, `form-selection.md`, `schematic-diagrams.md`,
`animation.md`, `image-generation.md` — belong to the slide-design agent in Step 2, not here.)*
It returns a **Content plan** — message only, no design: a comprehension brief + a claim ledger
+ the authors'-emphasis check + the narrative arc (incl. the planned **emotional curve** + what's
deliberately staged for later slides) + a per-slide CONTENT spec (takeaway that passes the
memory test · **role · question · beat** · content units · visual source: which figure/number/data
+ which question — what/how/why), plus flagged forward-looking content and open questions. You then take that plan into the **Step-1 CONTENT
checkpoint** (show it, get the user's OK on the story/message — the pace/slide-count check happens
HERE); only *after* content is approved does the slide-design agent design the look (Step 2). The
planner is *one mind* — it may fan out *reading* across multiple documents, but it synthesises the
understanding, arc, and per-slide message itself; never split one paper across blind agents. For a
quick, low-stakes deck you may do this pass inline yourself rather than dispatching — but
the deep-understanding and planning standard below is the same either way.
**🔴 The arc is COMPETED, not derived — 2–3 candidates over one ledger.** The planner returns 2–3
candidate arcs (each naming its audience question, the objection it pre-empts, its closing ask and
the ledger ids it carries), you run `python3 scripts/arc_divergence.py <arcs>.json`, and **YOU pick**
— it is not a new user stop. The competition reaches the user as the content checkpoint's required
**`arc gate:`** line (picked + the losers + one clause each + the divergence verdict); a content
checkpoint without it is not ready. Rationale, both collapse modes, and the escape hatch:
`agents/content-planner.md` §3. This exists because the arc is the only decision whose error
invalidates everything downstream — a wrong form costs one slide, a wrong arc costs the design plan
and the build under it — and it was the one decision with no alternative on the record.
**🔴 Hand the planner a `search cap:` too — and do the SMALL, NAMED lookups BEFORE dispatching it.**
Web search is capped per SESSION, shared with every subagent, and it does not reset between decks in
one conversation. Measured: one research fan-out — 12 agents plus 7 verifiers, none of them told a
cap existed — spent all 200, and the bill arrived hours later when a single lookup for a company's
official logo could not run and that deck shipped without it. The cheap, late, small queries starve
because the big early fan-out took everything, so fix it in the order that buys the most: (1) run the
handful of NAMED lookups first — the logo, the brand colours, the one clearance number — since they
are few, they are exactly what starves, and Step 2 needs them anyway; (2) state a per-agent cap **in
each dispatch prompt** — an agent not told a cap searches until satisfied, and N of them do it in
parallel — keeping the whole round under about half of what REMAINS, not half of the original cap;
(3) carry `searches: planned N / spent N` to the hand-off `cost:` line. If the budget does run out,
say so on the deck's limitations page and in the hand-off: **"could not verify" must never be allowed
to look like "does not exist"** (full rationale at Step 5's SEARCH BUDGET block).
**Hand the planner the RESEARCH breadth too** — the purpose-derived value from Step 0 (`standard`
for the low-stakes class, `thorough` for defense / conference / exec / pitch). It sizes only the
research sweep; the REVIEW tier is chosen later, at Step 5, with the rendered deck visible, and
the planner neither knows nor needs it. What breadth narrows is BREADTH, never the fidelity
floor: every claim that reaches a slide is still traced to a primary source at every breadth. If
no derivation was recorded, the planner works at `standard` and says so.

The rest of this step is the **specification the planner works to** (and what
you check its plan against). The bar — understand it deeply, don't skim:

A deck is only as good as your grasp of the material — a superficial read produces a
deck that *looks* right but misrepresents the work, which an expert audience spots
instantly. Read **all of it**, not the abstract: run the code's README, read the
paper end-to-end (intro → method → **every results table/figure** → conclusion).
*(That end-to-end read is the default for a BOUNDED source; for a LONG source — a book /
very long PDF / large corpus — do NOT fake a single linear read: classify the size, then
run **long-source mode** (map → triage → deep-read the load-bearing ~20% + a blocking
Source-coverage map). See the long-source bullet below and `content-planner.md` §1.)*

Then **write a comprehension brief — a REQUIRED, fixed-field, source-traced artifact** (the
planner's `agents/content-planner.md` §1 is the spec); every field must trace to a locatable
source span, not memory:

- **The field list is in `references/content-plan-spec.md` §Comprehension brief — read it before writing (or checking) the brief.** It holds the one-sentence message + its verbatim source sentence, the contributions, the method essence, the one-row-per-figure-AND-table spec, the nuance/limitation quotes, and the claim-ledger columns (same spec as `agents/content-planner.md` §1–2).

**This is a hard gate, not a sanity check.** Self-verify the brief against the source; if any
field is empty, hedged, or untraced — or the emphasis test fails (your one-sentence message
would surprise the authors) — you have NOT understood it: re-read or log an open question.
**An incomplete or untraced brief blocks the build.** Every slide must be faithful to the
authors' actual emphasis, not a plausible-sounding paraphrase. Reuse their figures
(relabel for the slide).

**Having a source is rarely the whole story — use the web for the gaps, even with one.**
Most decks are *partial*: a paper that needs related-work-since-publication or current
framing, a code repo with no writeup, figures with no prose, a doc that omits the venue. So
the web step below is **not only for the "No content" case** — run it whenever a source
leaves a gap, and in particular **re-verify the source's own falsifiable / time-bound claims
at *today's* date**: a paper's "state-of-the-art", an adoption number, a "first/largest/
latest" superlative may be stale by presentation day. Re-verifying a source claim is not
inventing — it's fidelity to what's *true now*.

- **No content — and any web fact-check on any deck:** draft the outline from your own expertise, then ground *and verify* every falsifiable claim against a **primary** source, and ground the deck to *today*. **Read `references/content-plan-spec.md` §Web verification & no-source decks before running any search or putting a falsifiable/time-bound claim on a slide** — it owns the PROVENANCE CONTRACT, the re-verify-on-every-build list, the dated-event tense rule, and the no-web-tool fallback.

- **A long source (a book / very long PDF / large corpus / multi-volume set)** is NOT read front-to-back — a faked linear read either overflows or, worse, *fits* and goes shallow. **The moment a source might exceed ~40–50 pp or not fit one pass, read `references/content-plan-spec.md` §Long-source mode** — deterministic size classification (`extract_pdf.py map`, CJK counting, multi-file sum), structure map, triage, the verbatim ~20% deep-read with page-traced claims, **page-scoped figure locators (never whole-document `autofig`)**, the Source-coverage map, the TWO-PHASE dispatch that posts the selection FYI *before* the deep-read, and the scanned/DRM no-text case.

**End Step 1 at the 🔴 CONTENT checkpoint — pace-check first, then approve the story.** The
Content plan is the cheapest place to fix a misread or a wrong emphasis, so present it *before any
design begins*: the **comprehension brief + claim ledger** FIRST (so the user can spot a misread
before a single slide is designed), then the **authors'-emphasis check**, the **narrative arc**,
and the **per-slide takeaways + content** (message only — no look yet), plus any flagged
forward-looking content and open questions. **The pace / slide-count check happens HERE, not
later:** for a *spoken* deck scale the slide count to the time budget — ~1 slide per talking-minute
as a loose anchor (short talk/status ~6–9, lecture/thesis defense/job talk ~10–20+), counting an
animated/build slide *once*; compute `slide_count ÷ time_minutes` and, if it runs well over ~1/min,
cut slides or get more time and flag it. A *read-alone / poster* deck has no talking-minute budget —
its scope is set by content completeness, and deliberate density is fine, not a defect. **Confirm
the resulting slide count** with the user (never ship a length they never saw). **For a long source
(book / very long PDF), the checkpoint ALSO carries a DIGEST of the Source-coverage map** (the chosen
slice + a built-around/summarised/cut tally; the full per-chapter map stays in the plan) **and
confirms the SELECTION.** Ordering matters: the verbatim deep-read that produces the verified ledger
happens *inside* Step 1, so the wrong-slice must be caught earlier — the planner surfaces the coverage
map as a **cheap selection FYI right after mapping+triage, before sinking the verbatim deep-read**,
and it is re-confirmed here **before DESIGN and BUILD (Step 2+) commit.** The wrong-slice risk is the
biggest one at book scale, so it is surfaced even under the auto-waiver (as an FYI). **Precondition —
the comprehension gate:** before showing the plan, confirm it carries a *complete* comprehension
brief (every field filled + traced) and claim ledger (no shipped `verified? = N` rows), **a
Takeaway spine that reads as one argument** (an incoherent spine is "not ready" — send it back to
the planner), a `scripts/plan_wordcount.py` pass over the per-slide table (advisory — but an
over-budget row with no recorded "over budget → notes/split" resolution goes back too), **a
`source size:` line on any file-sourced deck** (the bounded-vs-long classification must be a
recorded measurement — its absence means the classification never ran), **for an over-threshold
long source a complete Source-coverage map** (a disposition for every **skeleton section** — the
`map` TOC *or* the recorded reconstructed skeleton, every file for a multi-file source — + the
verbatim-vs-skimmed line + the `selection FYI:` line; a missing/partial map is "not ready"), **and
for a video-sourced deck the transcript-status line** (supplied locator or the visual-only GAP
line); an empty/hedged/untraced brief is **not ready** — send it back to the planner. Fold in the
user's edits to the story, then move to design (Step 2).
> **🔴 CHECKPOINT — CONTENT:** show the comprehension brief + claim ledger + narrative arc + the
> per-slide takeaways/content, and confirm the pace/slide-count, before any design work begins —
> rendered as the compact ≤~25-line checkpoint artifact defined under the 🔴 CHECKPOINT convention
> (the brief + ledger appear as its 2-line digest; post the full versions on request or on any
> digest anomaly — unverified rows, open questions). **For a long source (book / very long PDF), the
> artifact also carries a DIGEST of the Source-coverage map** (chosen slice + a built-around/
> summarised/cut tally; full per-chapter map in the plan) **and the SELECTION is confirmed here** —
> the coverage gate at book scale (also surfaced earlier as a cheap FYI, before the verbatim deep-read).

## Step 2 — Design the deck (use the slide-design agent)

> ### 🔴 STEP 2 OPENS WITH A MATERIAL PROBE — one REAL slide, built and looked at, BEFORE the plan is written
> **Author the signature page in the invented register with real deckkit, render it, and LOOK at it —
> then write the design plan's declarations to describe what you made.** Not after. The plan is a
> description of an artifact that exists, never a promise about one that does not.
>
> **WHY, measured on a delivered deck in this repo's own history.** The pipeline gates a motif's
> CONCEPT thoroughly — a derivation ladder with two middle rungs, two rejected pictures with the
> clause that lost each, the STRANGER TEST, ONE-form-ONE-meaning, the generativity triple — and its
> MATERIAL not at all. On that deck the concept was genuinely right (a config row, derived from the
> product's own `cordis.yml`, correctly rejecting the plug-socket stereotype every plugin deck
> reaches for) and it passed every one of those checks. **What shipped was six grey rectangles.**
> The user's verdict was 设计能力变弱了. The repair changed only the material — the same rows became
> a real config with keys, values and a `-`/`+` diff — and nothing about the concept moved. **No step
> between "concept approved" and "deck delivered" had asked what the device is MADE of.**
>
> The cause is an order-of-work failure, not a missing rule: the design turn had ~20 required
> declarations and zero required artifacts, so the effort went into sentences that pass instead of
> a thing that works. `signature move: 封面自己演示论点` is a good sentence and it was true of
> nothing on the page. **Pixels cannot be faked this way** — a grey-bars register renders as grey
> bars — which is the whole reason this probe comes first.
>
> 1. Build ONE slide: the page the signature move lands on, in the register you just invented,
>    using the same `build_<deck>.py` the deck will use. Render it (`render_deck.py … --slides 1`).
> 2. **Look at it, and answer one question in one line: what would the SAFE version of this page
>    have been?** If the honest answer is "about the same thing", the register is a look, not a
>    move — go back and invent, before twenty declarations are written on top of it.
> 3. Then write the design plan. The checkpoint carries a **`material probe:`** line — the rendered
>    PNG plus that one-sentence comparison.
>
> **Cost is one build + one render (seconds), and the page is not a throwaway** — it becomes the
> deck's signature slide and serves as the Step-4 anchor proof's `signature` anchor, so the ritual
> is paid once. **It is a different question from the anchor proof**, which asks whether the move
> SURVIVED the build; this asks whether the register was worth building at all.
>
> **Skip only when the look is not yours to invent:** a registered/provided template or a Mode-A
> mimic (the material is the template's), or a 1–2 slide tiny ask. `boldness: conservative` does
> NOT skip it — restraint is a material decision too, and a page is exactly where you see whether
> it reads as deliberate or as nothing.

With the **Content plan approved**, first build the **Evidence manifest** — one READ-ONLY probe line per asset the approved plan names, so the art director plans geometry with its eyes open (a no-asset deck skips it entirely). **Read `references/asset-production.md` §Evidence manifest before dispatching slide-design** for the line format, the probing tools, and the rule that probing NEVER materializes crops/equations/plates (asset-prep still runs only after the design plan is approved). That file is the asset lifecycle end-to-end — probe → image opt-in → crops → charts → logo/icons → equations.

**The per-asset SPEC asset-prep consumes has a named producer:** the Design plan's per-slide rows
(or its image opt-in list) carry, per asset, the crop spec (or `autofig index N` — **but on a
long-source deck the locator must be page-scoped**: `figures <src> <page>` + the caption label,
never a whole-document `autofig` index, whose global numbering shifts between runs), a generated
plate's topical prompt, an equation's target height, and a GIF's poster frame — and where the
approved plan left one implicit, the COORDINATOR completes it from the plan's own geometry when
assembling asset-prep's work order (asset-prep itself never decides these; it only executes).
Then dispatch `agents/slide-design.md` — the deck's **art director**
— to design the look on top of the locked message. Dispatch it through an available multi-agent/
subagent tool when the host exposes one, otherwise run the same brief inline. Give it the **approved
Content plan** (comprehension brief, claim ledger, narrative arc with its emotional curve, and the
per-slide CONTENT table with each slide's *role · question · beat* and *visual source* cells),
**the Evidence manifest** (asset geometry, above), the **taste lines** —
`taste.md`'s DIALS + NO-GOs + its LAST look-history line, read from the registry root per
`references/user-taste.md` ("none on file" for a brand-new user) — so §1 Freshness has something
real to vary against and the chrome-budget default is seeded, while the interview's explicit
answers and the LOCKED-look carve always outrank them, the
interview answers that steer register
(purpose/audience/time, delivery mode, style, template/brand decision, venue — plus, when the user
gave a Q4 style example, the **written style brief + chosen mimic mode**), and the craft
references it designs against (`form-selection.md`, `design-gallery.md`, `scripts/presets.py`,
`design-by-purpose.md`, `design-principles.md`, `design-intelligence-addendum.md`, `semantic-color-contract.md`, `data-viz.md`,
`schematic-diagrams.md`, `icons.md`, `animation.md`, `image-generation.md`,
`east-asian-aesthetic.md` — and, for a mimic deck, `style-analysis.md`). It consumes the approved content — it does **not** reopen it — and
returns a **Design plan**: the deck's **Design language** (a *named* signature motif + a
deliberately-chosen palette/type + the polish moves), the **deck rhythm**, a **per-slide design
table** (form + the runner-up it beat · reasoning · layout · motion · image?), the
**Form ledger + diversity gate**, the **design self-verify checks**, the **10-item design-critic
checklist** (which the Step-5 critic's design lens then applies), and the **image opt-in list**. The
art director is *one mind* over the whole deck — only it sees every slide at once, so deck rhythm and
where the appear-builds fall are its call, not the builder's.

**The design plan is the cheapest place to change visual direction**, so end the step by showing it
and getting the user's OK before the canvas is set up or anything is built. **This design intelligence
runs on EVERY deck — it's how the art director designs, never opt-in per deck — and scales down
gracefully to small decks (a 4-slide deck still earns one hero per slide, no card-grid reflex, semantic
colour, and one memorable moment); only the deck-level numeric floors are size-gated (hard at ~8+ content
slides, strong guidance at 6–7).** **Precondition — the design gate:** the plan is **not ready** unless it carries a **`concept:` line
— what this deck's idea is a PICTURE of, **the two middle rungs that produced it** (`via <core
concepts> → <visual language>`), plus the TWO pictures it beat and the clause that lost each**
*(the ladder is `topic → core concepts → visual language → motif`; the MIDDLE rung is the one that
gets skipped, and skipping it is what produces industry stereotype — an MRI deck jumped straight to a
picture gives you a scanner, routed through `frequency · sampling` it gives you a k-space grid. A
winner with no rungs is a picture that arrived, not one that was derived. Full ladder + the
domain-neutral §3 dictionary it resolves through: `agents/slide-design.md` §1)*
(*an intelligence network* · *a digital organism* · *a hand and a machine hand doing one job* — three
governing images for the same approved argument, not three styles and not three layouts). This is the
one divergence the pipeline never had: the direction gate diverges on STYLE (its own preview page says
"the same four slide types … only the *style* differs") and form-selection diverges on LAYOUT per
slide, and both hold the picture constant. The motif does not fill the hole — it is chosen as an
attribute of a preset picked first and capped at ≤3 appearances, so a governing image is structurally
forbidden from governing. It costs three sentences at plan time: no extra dispatch, no extra render,
no extra round trip (`agents/slide-design.md` §0). One picture with no alternatives is not a choice,
it is the first thing that came to mind — and the hand-off gate rejects two "alternatives" that are
the winner in other words. It also has a concrete **Design language** (a *named*
signature motif + a deliberately-chosen palette/type, not a defaulted light/minimal/blue), a one-line
**taste-profile field** in that Design language section — `taste profile: <n dials applied / none on
file> · freshness: varied <foundation> vs <last look-history line>`, or the alternate arm `look
LOCKED (registered/provided template) — carve applies` — the line that makes the freshness rule
checkable and any profile override visible (`references/user-taste.md`), **a `boldness:` line
(conservative | balanced+ | bold | experimental — **DERIVED, not a flat default**: explicit user
request > `taste.md`'s promoted dial > the purpose — *conservative* for a sober defense / regulatory
/ status readout unless asked otherwise, *bold* for a pitch / launch / brand / culture deck,
**balanced+** for everything else; record which arm set it (`agents/slide-design.md` owns the full
table). This derivation used to live ONLY in the art-director's own file, so an inline run — which
never opens it — gave a launch deck and a status readout the same middling dial, and then judged
both against it: the pitch was never asked to be brave and the status readout was told off for not
being. Layer 1 has to carry the mapping because layer 1 is what an inline run reads; **at `conservative` the risk is
OPTIONAL — take a modest restrained move, or fill the field with the one-clause `deliberately
restrained: <why>`, and then `signature_proof` is not required because there is no risk to prove.
Every other field still is, and above `conservative` a real move is required, not optional**) AND a real `signature move:`
line** — the ONE deliberate aesthetic RISK a template wouldn't make, scoped to where it lands (cover /
WOW / money slide) and adapting a named bold reference, **plus a `carried_by:` clause naming 2–3
slides (the signature slide + ≥1 more) where the same idea does STRUCTURAL work** — one brave slide
among nineteen safe ones reads as a tonal break, not a position; coherence is what makes daring look
deliberate. Carried means the idea becomes the *shape of the content* on those slides (the motif
turns into the diagram's own geometry), **not** a decorative repeat — a device stamped on every page
is the opposite failure and the motif budget (≤3 appearances) still binds; a `signature move` that reduces to "a big
number / a nice gradient / a full-bleed photo" is the safe catalogue, **not** a signature move, and
makes the plan incomplete (send it back; self-verify (h) owns this) — only `boldness: conservative`
(whether user-set or purpose-defaulted) makes the risk optional, softening the field to a named
"deliberately restrained" clause so it's never blank; the risk lives on
composition/scale/concept/type and **never** overrides a floor (legibility/fidelity/lint win), **an
`AR a.b -> <zone>` annotation in the Layout cell of every slide placing a manifest-listed
figure/table** (a plan that commits a known-geometry asset to a zone without checking the fit is
not ready — send it back to the art director; the slide-design §3 Image-fit rule owns the
re-form-vs-taste-reason call), a **Form
ledger** whose diversity gate passes (no one format-family on >~40–50% of content slides — the
card-overuse guard), the addendum's **deck-level design gates** — a **rhythm map**, a **semantic-colour
ledger**, a passing **block-dependency audit** (no >2 consecutive card slides), and the **minimum
deck-level variation** (`references/design-intelligence-addendum.md`) — plus, on **ANY deck that NAMES
a real entity** (not only a single-entity one: a company / product / brand / institution / government
body as the SUBJECT, a tool/framework/model named as content, **or a slide whose FORM is a roster of
named real entities** — an ecosystem map, an alliance's member list, a comparison whose rows are
institutions), a **logo plan WITH EVIDENCE** per the slide-design LOGO PRINCIPLE's situation
table: the line must read `official asset — <source>`, `searched, none found → designed wordmark
(flagged)`, or `n/a — <named inline as text | template carries it | user opted out | third-party assessment>`
— and a **roster slide additionally carries `entity marks: <N of M sourced | none — reason>`**, because
one line cannot say both "the deck's own mark" and "the eight institutions on slide 5". 🔴 **A generic
placeholder glyph in a mark's slot — a coloured square, a repeated stock icon, a bullet dot dressed as a
crest — is NOT an acceptable value for that field.** It is decoration impersonating information and it
fails the 1-second decodability floor; plain type beats a shape that looks like it means something.
*(Measured: a 12-page deck listed all eight Go8 universities around a hub — the exact ecosystem-map form
the LOGO PRINCIPLE says earns a logo wall — and shipped eight identical blue squares. Nothing was wrong
with the rule; the deck was multi-entity, so no `logo plan:` line was ever required, and a rule nobody is
asked to evaluate is a rule that does not run.)*
— **`third-party assessment` is a full member of this set, not a footnote**: it is decided BEFORE the
search and overrides its result (the 🔴 row below), so a deck that qualifies for it must be able to
name it here — a bare "wordmark"/
"text only" with no recorded search, or a missing line on any deck that names a real entity (including a roster slide), makes the plan
**incomplete** (send it back; self-verify (o) owns this) — and the **THREE
DESIGN MUSTS** addressed (`slide-design.md`'s three design musts) —
**(1) appear-builds — ONLY if the user opted in** (the interview's presented-deck choice): if IN, a
motion manifest places builds where they help (build/static *with a reason* per slide) and each built
slide is staged FULLY (every content element in a step, deliberate order); if OUT, every slide is
`static: user opted out` and that is complete, not a gap. **(2) a style-matched SVG icon family** on any
category/entity-rich deck — every branch, incl. generated-template (self-verify (g); "opt-in" never waives it), **(3) diverse formats** (not a card grid repeated) — musts 2–3 are
*applied where they help or justified where not* (a must to consider + apply, never a blank per-slide
quota — still smart about where/when). A plan that defaults its look, over-relies on one format, forgets
icons, or — when builds are opted in — leaves a built slide half-staged or forgets builds where they'd
clearly help is **not ready** — send it back to the art director.

**Codex only:** include `references/codex-runtime.md` in the art-director brief and begin its hidden
`.codex-deck-evidence.json` once the design direction is known. Its per-slide ledger must mark which
slides are categorical, bind those to one actual icon family or a slide-specific waiver, and name any
early component carve; do not let either decision disappear into the builder's convenience.

**🔴 One row of the LOGO PRINCIPLE table decides BEFORE the search and overrides its result: a
THIRD-PARTY ASSESSMENT.** The deck is *about* an entity but is not *from* it, and carries what that
entity would not publish about itself — open recalls, a "first but not unique" correction, a
limitations page, competitor counter-evidence. There the answer is `n/a — third-party assessment`
plus the finding that makes it so: **no official livery on any page**, the entity's name set in the
deck's own type. The test is authorship, not sentiment — a favourable independent review has the
same problem as a critical one. A reader seeing the mark concludes the entity produced or endorsed
this, and for an independent assessment that is a misattribution: the same class of error as an
unsourced number, committed in the chrome instead of the body. Because it is a question about who
wrote the deck, finding a real logo does not overturn it and "not found" is never its reason.
*(Real: a briefing carrying two open Class I recalls and a "first, but not alone" correction was
headed for build in its subject's brand colours; it was caught by hand and recorded as a named
deviation. This row makes that the default instead of a save.)*

**The per-slide content-image opt-in is a CROSS-CUTTING choice available on EVERY deck** — independent of the template decision and separate from Q1's generate-a-template path; offer it whenever an image tool OR web search for sourced photos is available. **Read `references/asset-production.md` §Per-slide content-image opt-in before writing the opt-in list** — the three guardrails (content-related, never every slide, and the REFERENT RULE that decides generated vs real sourced imagery) and the per-row source-token grammar. Fold in the user's design edits, then set up the canvas (Step 3).

> **🔴 CHECKPOINT — DESIGN:** show the **`concept:` line (the governing image + the two middle rungs
> that produced it — `via <core concepts> → <visual language>` — + the two it beat, each with the
> clause that lost it)** + the Design language + Form ledger + the 3 design musts + the
> **`boldness:` line + the `signature move:` line with its `carried_by:` clause** (the one scoped
> aesthetic risk + where it lands + the bold reference it adapts + the 2–3 slides where the same idea
> does STRUCTURAL work — so a wrong dial, a timid/too-wild move, or a risk that lives on exactly one
> slide costs one glance to veto) + the
> image opt-in list (each row with its `generated — <tool>` / `sourced — <origin> (<license>)` /
> `provided — …` / `searched, none found → …` rung — full grammar: `references/image-generation.md`
> step 5 — source token) + (on ANY deck naming a real entity — subject, named-as-content, or a ROSTER slide) the **`logo plan:` line WITH its
> evidence token** (`official asset — <source>` / `searched, none found → designed wordmark (flagged)` /
> `n/a — <reason, incl. third-party assessment>`) + the **motif line stating the device AND its meaning
> + how it's made legible + `motif generates:` (background · markers · one PAGE whose geometry IS the
> motif — `none — <reason>` beats an invented artifact) + ONE MEANING PER REPEATED FORM deck-wide** —
> the last two are gates, not garnish: a motif that only recurs is an ornament with a schedule, and a
> device meaning one thing on the cover and another inside passes every per-page check while still
> sending the reader asking what it means (measured twice, on two different decks). On branch (c) both
> are REQUIRED rather than weighed, because there the motif IS the deck's visual design; `conservative`
> and a 1–2 slide tiny ask carve out, and on a locked template the ladder is not re-run on its device
> (label / legend / figurative / **removed** — the STRANGER TEST; **a motif may be a CONSTRUCTED
> OBJECT rather than a shape** — something this deck's own material would BUILD, gaining a part per
> beat instead of appearing again per beat, which is what makes `carried_by` structural rather than
> stamped. Derive it from this content; there is deliberately no menu, because a menu of objects
> becomes the next house style. The test: *could this object belong to any other deck?* And it is
> the right answer only when the argument ACCUMULATES — a comparison, a set of independent findings,
> or a sober regulatory register wants the abstract device instead, and picking that deliberately is
> the same judgement working, not a failure to be bold. Full when/when-not:
> `agents/slide-design.md`; a reading that DEFERS to a later
> slide is a failed test written as a passing sentence) + the **`interior register:` line** (the quiet
> cue that carries the style onto ordinary interior pages, or `none (flat by register — <reason>)` —
> self-verify (q) · PRE-FLIGHT 6b · the critic's `register_interiors` check all read this field, and a
> style dressed only on the bookends fails) + the **`density:` line as two numbers**
> — presented as the compact checkpoint artifact from the 🔴 CHECKPOINT convention block
> (same fields, incl. the rhythm-map table and the branch **gate line** — `direction gate:` on branch
> (c), `style gate:` on branch (d); picked look or named carve) — and get the user's OK before building.

## Step 3 — Set up the canvas
**First, decide where the deck lands.** Deliver each deck as one self-contained
folder in the user's Downloads — `~/Downloads/<deck-name>/`, holding the
`<deck-name>.pptx` and a `render/` subfolder of slide PNGs — so the user gets a tidy,
findable bundle rather than a stray file in `/tmp`.
**🔴 The `.pdf` and `viewer.html` are NOT produced during the build.** A deck is iterated
— rebuilt each critic round, then usually hand-edited in PowerPoint — so a PDF and a preview
page generated on every render are churn: they clutter the deck root and go **stale** the moment
the `.pptx` changes, which is worse than absent (a user opens a stale PDF and reviews the wrong
deck). They are **reserved deliverables**: at hand-off (step 6), once the user confirms the deck
is final, offer them and generate both with `render_deck … --deliverables`. Point your build script's
output path and `render_deck.sh`'s out-dir there from the start (no need to copy
files around at the end). **Before the first save, confirm `~/Downloads` exists; if
it doesn't, ask the user where they'd like outputs** and use that location instead —
don't silently dump into `/tmp`. You'll remind them to open it in step 6.
> **🔴 CHECKPOINT** — if `~/Downloads` is missing, ask where to save before writing any file.
> *(Per-deck auto: this checkpoint is a question, so it has no FYI form — do not stop. Default:
> `mkdir -p ~/Downloads` when the home directory is writable (keeps the standard
> `~/Downloads/<deck>/` layout every reference assumes); only if home is unwritable, use
> `./<deck-name>/` in the working directory. Never `/tmp`. State the chosen location in chat the
> moment you decide it — auto mode is never invisible — and repeat it in the hand-off.)*

> ### 🔴 The moment you have a folder, DISPATCH THE IMAGE MANIFEST — then keep working
> Generated plates are the slowest thing in this pipeline (~30–90s each, and the scripts run them
> concurrently). Authoring the build script is the longest thing YOU do. They are independent:
> generation is waiting on a hosted model, authoring is you writing Python. **Run them at the same
> time.** Put every approved plate — hero, dividers, interior, per-slide — into ONE manifest, start
> it, and go straight on to the canvas and the build script without waiting. By the time you
> *execute* the script the images are on disk, and you paid for them in wall clock you were
> spending anyway.
> - **The build RUN is the barrier, not your judgment** — `python-pptx` raises on a missing image
>   file, so a script executed too early fails loudly and names the file. There is no version of
>   this that quietly ships a deck with holes in it.
> - **The one thing that genuinely blocks: the signature slide's assets.** Step 4 opens with the
>   SIGNATURE PROOF, so `asset-prep` delivers that slide's plate/figure/icons first (its brief
>   already says so). Everything else can land while you author.
> - **Order the manifest to match:** signature slide first, then the rest.
> - **Do not** dispatch before the Step-2 DESIGN checkpoint is approved — the prompts, placements
>   and opt-ins are exactly what that checkpoint locks, and regenerating a rejected plate costs
>   more than it saved.
>
> *(Serial by default was never a decision anyone made — the pipeline simply read top-to-bottom.
> Measured cost of leaving it serial: the full generation batch, dead, before authoring starts.)*

**Canvas format.** The default deck is 16:9 via `deckkit.blank_deck()` — untouched, and everything below assumes it. **If the interview confirmed any non-16:9 surface (4:3 venue · 小红书 3:4 · square 1:1 · story 9:16 · A4 print) — or the design plan carries a `format:` line that isn't `wide` — read `references/deck-setup.md` §Canvas format BEFORE creating the presentation object**; it carries the `scripts/formats.py` contract (`band` safe rect · `chrome` · `columns_ok` · `display_scale` · `lint_flags`) and the rule that the design plan records a `format:` line whenever it isn't `wide`.

**Keep the per-deck build script (`build_<deck>.py`) in that same folder, beside the
`.pptx`.** The build script — not the rendered file — is the *source of truth* for the
deck, so it should travel with the artifact: this makes every later iteration
reproducible (re-run it, get the same deck) and is what lets you fold the user's
later change requests back into the build rather than hand-patching the binary. See
`references/handoff-and-iteration.md` for why this matters at hand-off and how to
iterate without clobbering the user's manual edits. In that script, resolve deck assets
relative to the script file (for example `ROOT = Path(__file__).resolve().parent`) rather
than the current working directory, so `python /path/to/build_<deck>.py` works from anywhere.

- **Template branch** — the user supplied a `.pptx`, or Step 0 found an official conference template: read `references/deck-setup.md` → "Template branch" BEFORE creating the deck object (inspect → `open_template()` → adopt the template's brand → register a reusable `profile.md`).

- **No-template branch** — you are designing the look yourself: read `references/deck-setup.md` → "No-template branch" BEFORE the first palette/preset/font call. **Reach for `presets.apply("<name>")` — one call, palette AND structure.** `set_palette` alone re-themes only colour (a bare `deckkit.MAGENTA = …` does not re-theme components whose signature default binds at import); `deckkit.set_geometry(radius=…, rule_w=…)` carries the other half — **`radius=0` squares every rounded component**, which is the only way to reach `brutalist`/`swiss`/`ink_wash`/`blueprint`, whose own guards forbid rounded cards and which the library previously could not draw at all. Both are no-ops at their defaults (`scripts/presets.py` · `references/design-by-purpose.md` · `references/design-gallery.md`). Two rules that survive no matter what: **never ship deckkit's default blue, and never reuse the last deck's scheme** — each deck gets its own distinct identity.

**Fonts (every deck, both branches).** A `.pptx` stores font *names*, not the fonts — before setting `deckkit.FONT`/`MONO`/`EAFONT`/`EQ_MATHFONT`, read `references/deck-setup.md` → "Fonts" (CJK `EAFONT` is required for any 中文/日本語/한국어 deck; portability, the `EQ_MATHFONT` / STIX / Cambria Math dependency to flag at hand-off, and tofu recovery live there) and flag any font dependency at hand-off.

## Step 4 — Build with deckkit

> ### 🔴 Step 4 opens with the ANCHOR PROOF — THREE slides, rendered, BEFORE the other slides exist
> The `boldness:` / `signature move:` contract is approved as **prose**. The pixels that either honour
> it or sand it back to safe do not appear until Step 5, after the whole deck is built — at which point
> the critic's "the signature move got sanded" finding costs a rebuild, and that cost is exactly why it
> gets accepted instead of fixed. **Put the evidence where the decision is** — and prove the three
> things that each cost a rebuild when they surface at Step 5, not just the one:
>
> | anchor | the page | what it proves | the failure it catches |
> |---|---|---|---|
> | **`signature`** | the slide `signature move:` names | the aesthetic risk survived the build | the move got sanded back to the safe catalogue |
> | **`complex`** | the densest page in the content plan | the design HOLDS the content | 好看但装不下内容 — a look approved on a spacious page |
> | **`data`** | the most critical data/conclusion page | the charts speak the same visual language | palette + type were chosen against text, and the first native chart obeys none of them |
>
> *(Why not the cover, the obvious third? It already has two gates — branch (c) renders four full
> directions at the direction gate, branch (d) posts a rendered hero at its own 🔴 checkpoint. Making
> it an anchor would re-prove the one page nothing was missing on, and leave these two unproven.)*
>
> 1. Author the **three anchor slides first** — the signature slide plus its `carried_by:` partner if
>    the idea's structural claim is only legible across the pair, the densest planned page, and the
>    key data/conclusion page. On a deck with fewer than three slides the count drops to the deck size
>    (a 1–2 slide tiny-ask skips the ritual entirely, below).
> 2. Build, then render just those pages:
>    `python3 scripts/render_deck.py <deck>.pptx <out> --slides N,M,K`. The PNGs are byte-identical to
>    the same pages from a full render, so they are evidence, not an approximation. 🔴 **`--slides` is
>    not the saving here** — three pages cost about what all eighteen cost (below), because the render
>    is a fixed LibreOffice start. What this ritual saves is AUTHORING: you learn the design is wrong
>    having built three slides instead of twenty.
> 3. **Post the three PNGs** with one line each: *"this is what `<signature move>` actually looks
>    like"* · *"this is the design carrying the heaviest page"* · *"this is a real chart in this
>    language."* A 🔴 stop in the default flow; under a per-deck AUTO WAIVER it downgrades to a posted
>    FYI like every other approval stop — the waiver removes the wait, never the artifact.
> 4. Then author the rest. If the proof is wrong you have re-authored THREE slides, not twenty.
> 5. **Record it** — the run carries a `signature proof:` token to Step 5 on the critic contract
>    card, one entry per anchor: `signature proof: signature slide N → <png> · complex slide M → <png>
>    · data slide K → <png>` or `skipped: <the named carve>`. Without it the
>    step is advisory by construction, which is the failure mode this whole batch exists to fix:
>    the critic can then check each SHIPPED anchor against the frame that was approved, and
>    a silent skip is visible instead of invisible. The delivery gates enforce the same three
>    (`design_plan.signature_proof` is now a LIST of `{role, slide, png}` — one contract in
>    `scripts/anchor_proof.py`, imported by both gate paths so they cannot drift apart).
>
> **Skip only when:** `boldness: conservative` with its "deliberately restrained" clause recorded (no
> risk was taken, so there is nothing to prove), or a 1–2 slide tiny-ask. A registered/provided template
> does NOT skip it — a borrowed look still has a signature slide, and that is exactly where a template
> deck either becomes designed or stays a template.
>
> *(Measured on an 18-slide deck: a `--slides` render ≈ 2.9s and a FULL render ≈ 2.8s — the same,
> because both pay one ~2.5s LibreOffice start and page count barely moves it. So the proof is cheap
> in absolute terms (one build + one render, a few seconds), not because it renders fewer pages; the
> saving that matters is the twenty slides you did not author yet. **Going from one anchor to three
> is therefore close to free on both axes that cost anything:** the render is one fixed start either
> way (~0s more machine time), and all three pages go in the SAME build script and the SAME render
> call, so the ROUND-TRIP count — the thing a deck's wall clock is actually made of — does not move.
> What you spend is authoring two more slides; what you buy is discovering that the design cannot
> hold your densest page while three slides exist instead of twelve. It costs less than one
> critic round, and it is spent BEFORE the expensive authoring rather than after. This does not
> contradict "build the whole deck in one script run" below: the proof runs the SAME build script
> while it still contains only the three anchors — you extend one script, you never maintain two.
> Asset note: the signature slide's assets are the first thing asset-prep delivers, per its brief.
> One render can serve several rituals: when Gate A's one-real-slide fidelity confirm has not yet
> run, use the signature slide AS that confirm slide; on a large deck the proof doubles as the
> early-render sample. Never run three separate single-slide ceremonies.
> If the proof looks WRONG: revise the signature slide in the same build script and re-run the same
> `--slides N` command — the loop is slide-level and costs seconds; slide N here is the slide's
> CURRENT index, so if later authoring renumbers it, the `signature proof:` token records the final
> number at hand-off.)*

Write a small per-deck build script that imports `scripts/deckkit.py` (don't re-derive primitives;
full signatures + behaviour are in its docstrings). **Build the approved Design plan** (form ledger,
rhythm, per-slide design, colour, logo) as the source of truth — the slide-design agent already chose
each slide's visual FORM and the user approved it at the DESIGN checkpoint, so **don't re-derive an
approved form.** *Fallback only where the plan left something open:* pick that slide's form deliberately —
generate 2-3 candidate forms and choose with the tie-breaker in `references/form-selection.md`;
**don't default every multi-item slide to a card grid.**
> **🔴 When a COMPONENT exists for the form, BUILD that component — do NOT hand-roll a substitute from
> raw `box`/`connector` primitives.** Reaching for a plotted form (`waterfall`, `gantt`,
> `dumbbell_board`, `dot_strip`, `tier_stack`, `native_chart`, `eval_matrix`, `heat_matrix`, `meter_bar`,
> `timeline` …) and then hand-drawing it with boxes **re-introduces the exact geometry & grammar bugs the
> component already fixed** — a baseline width hardcoded to a number that stops short of the last bar
> (the component derives its axis from the data), a waterfall that double-counts (+8 / +8.3 / +16.3 as
> peer bars) or conflates two quantity kinds (take-home vs employer cost in one 135% stack). This is the
> #1 source of "the chart looks messy / wrong" defects. Adapt a component's params or compose from
> primitives ONLY for a form the library genuinely lacks — and *then* the burden is on you: **derive
> every axis / baseline / track extent from the data** (`last_bar_x_end − axis_x`, never a hand-picked
> width), and don't double-count (`references/design-principles.md` "Designed plots" + "Big numbers").
The helper set, by job:
- **Chrome:** `title_bar`/`content_slide`, `footer`, `editorial_header` (caps eyebrow + title +
  hairline), `part_eyebrow`/`page_marker` (mono eyebrow + page marker), `logo` (persistent
  brand/institution/product mark in a fixed corner on every page — see the brand-logo rule below).
- **Safe layout — measure or anchor, never hand-pick a y:** `columns`/`rows` (equal **or
  `weights=`-proportioned** split panels — a measured 1/3–2/3 or rail+main split — symmetric outer
  margins either way), `content_band` (the SAFE rect below title / above footer), **`bottom_callout`**
  (footer-safe bottom takeaway — anchors to the band, grows UP, can't collide), **`vstack(…, bottom=)`**
  (measured stack: equal gaps + no overlap by construction, errors at build time on overflow) with the
  `measure_callout/measure_bullets/measure_text` helpers, **`spaced_centers`** (evenly-spaced marker
  centers for a timeline / tick row / numbered steps, **inset at the ends so a centered caption stays
  co-centered with its end marker** — use it instead of hand-rolling a row of dots+captions, which
  desyncs the first/last caption from its dot near a slide edge; `timeline` already uses it),
  `picture` (`fit="contain"` keeps edges /
  `"cover"` crops), `make_gif` (GENERATE a looping GIF from computed frames) + `gif` (embed the animated
  GIF, undistorted + size/still warnings) + `gif_poster` (extract the first/representative frame to
  verify what the render & PDF export show) — generate → embed → review, `icon`/`icon_tile`/
  `icon_badge`/`icon_ghost`/`icon_card` (place an open-licensed SVG icon — recolored + rasterized via
  `scripts/icons.py`, which also does **duotone** weights + **gradient-fill**; `icon_tile` is the
  versatile container — circle/squircle/square × solid/gradient/glass tile, `icon_badge` a ring badge,
  `icon_ghost` an oversized faint watermark, `icon_card` the upper-left feature-card pattern; vary the
  treatment to fit the deck — see `references/icons.md` "Treatments"). *(These exist so you never
  hardcode a low `y` — the recurring overlap/footer bug.)*
- **Text & blocks:** `bullet`, `callout` (auto-grows), `chip`, `modbox` (a labelled MODULE box —
  reach for it as the node when mapping architecture modules / code files / system parts joined by
  `connector`, where a plain `node` is too bare; role word + optional filename/tag), `arrow`, `table` (highlight
  the key row), `code_block`, `hrule`.
- **Colour:** `palette(n, ACCENTS)` (n distinct, contrast-checked fills — warns on adjacent same-hue;
  never a gray filler), `palette_from_image` (match a generated template's palette), `accent_one`
  (one-accent discipline), `contrast_ratio` (verify ≥~4.5:1 before committing).
- **Data furniture & charts:** `scorecard`/`leaderboard`/`takeaway_rail`, `change_stat` (baseline-
  centred before→after), `stat_row`, `big_numeral`; **editable native charts** `native_chart` /
  `native_dual_axis` / `native_donut` / `native_pareto` / `native_bubble` (feed them straight from a
  spreadsheet with **`series_from_csv(path, x_col, y_cols)`** → `(categories, series)`, stdlib, no pandas),
  plus the raster recipes in `scripts/designed_charts.py` (incl. **`waterfall`** — a total's rise/fall/
  total walk, semantic up/down colour; **`distribution`** — the form to use when a value is a mean of
  MEASUREMENTS rather than a count, since a bar of sample means hides n, shape and outliers;
  **`marimekko`** — size *and* share at once; **`radar`** — a profile across 3–8 axes, ≤3 series)
  — pick per `references/data-viz.md`.
- **Walkthrough / hierarchy / comparison-grid:** **`image_grid`** (an N×M LABELLED IMAGE
  COMPARISON — methods across the columns, cases down the rows, a metric under each cell. THE
  results slide of an image/reconstruction talk, and the one image idiom where a grid IS the
  argument, so `form-selection.md`'s "one strong image beats a grid of small ones" does not apply.
  It reads each picture's REAL placed rect back and derives every label from it, and locks ONE
  aspect ratio for the whole grid so `contain` and `cover` coincide — zero letterbox, zero crop, by
  construction. Refuses mixed FOVs, ragged rows, a missing `col_labels`, >16 cells, sub-0.8in cells
  and a metric that wraps, rather than shipping unreadable thumbnails. Measured on the hand-rolled
  version it replaces: every label 0.67in off the panel it named, 65% of each cell lost to
  letterbox — and `lint_deck` reported `0 findings ✓ clean`, because `CAPTION NOT ALIGNED`
  structurally cannot fire on a multi-row grid) · **`annotated_figure`** (a real figure + numbered
  markers + a numbered caption rail + optional magnified inset — the guided figure walkthrough the
  integral-figure rule kept demanding by hand) · **`small_multiples`** (identical mini native charts
  with a SHARED value axis — the documented recipe left each panel auto-scaling, so a small bump and
  a huge bump looked identical) · **`position_map`** (N LABELLED items on two continuous axes — the
  within-cell position quadrant() throws away) · **`org_tree`** (tidy hierarchy: centroid parents,
  horizontal bus; raises when it can't fit legibly).
- **2.5D isometric (native — no generated image):** **`iso_bars`** (a FAITHFUL 2.5D bar chart —
  extrusion height is linear in the value and zero-based, so the depth never distorts the data) ·
  **`iso_stack`** (a layered architecture / disclosure ladder / decision stack — floating isometric
  slabs with labels aligned beside each one) · **`iso_prism`** (one extruded block as a hero).
  Fixed projection (true 30° isometric, parallel not perspective) and one-light-source face shading,
  so every 2.5D element in a deck reads as one system. **Dose like generated imagery** — a stack, a
  hierarchy, or ONE hero chart, never every slide; text cannot be sheared onto a face, so labels sit
  beside the geometry. When the 2.5D wants to be a rich atmospheric *scene* (not data), that is the
  generated-image branch, not these.
- **The register signature (`register_mark`) — build the quiet motif, don't re-derive it.** A
  bespoke register is REQUIRED at the direction gate, and until this helper existed deckkit had no
  primitive to draw one, so every deck hand-rolled its signature out of raw boxes. Measured: one
  such helper offset each ring in x but **not in y** and therefore drew three *interlocking*
  circles — a Venn diagram — in the corner of twelve pages, and nothing caught it because no gate
  knows what a motif is supposed to look like. `register_mark(slide, kind, corner=…)` draws the
  five common shapes correct-by-construction — **`arcs`** (concentric rings sharing ONE centre, so
  that bug is unrepresentable) · **`rule`** (an inset edge rule) · **`ticks`** (an evenly-spaced
  scale) · **`ordinal`** (a corner numeral) · **`grid`** (a small hairline field) — and TAGS what
  it draws. Invention stays open: draw whatever you like and call **`deckkit.tag_motif(shape,
  loud=…)`** on it. 🔴 **The tag is what gives the motif a machine-readable existence**, and two
  contracts the skill has always stated become checkable only because of it: **`TEXT_OVER_MOTIF`**
  (a title crossing the device — invisible to `TEXT_OVERLAP`, which measures text against TEXT
  while a motif is geometry; declare a deliberate one with `overlap_intent`) and
  **`MOTIF_BUDGET`** (the ≤3 LOUD appearances the design plan promises — pass `loud=True` for a
  hero appearance; the quiet register signature is excluded by design, because it is *meant* to
  repeat on every page). An untagged deck is never punished for not using this vocabulary.
- **Composed overlap (`overlap_intent`)** — `lint_layout`'s `TEXT_OVERLAP` is a CRITICAL that refuses
  to save, and it is right to be: colliding text is the commonest way a build ships unreadable. But it
  also refused two moves that are ordinary editorial design — **a giant display word with a small line
  riding it** (scale contrast) and **background geometry running through a paragraph** — with no way to
  say "this one is on purpose", so those decks could not be saved at all. Tag the element that is
  deliberately the ground: `dk.overlap_intent(big, "the display word is the ground the caption rides")`.
  A TAG, not a threshold, for the reason already written beside `ghost_numeral`'s exemption —
  *"guessing from size either waves through a real defect or blocks a legitimate watermark."* The
  reason is required (≥16 chars) and travels in the shape, so the declaration is evidence in the
  artifact rather than a claim in a plan. **It waives the GEOMETRY, never the floor:** contrast,
  `TEXT NOT VISIBLE` and the render-time occlusion checks still apply, and an undeclared collision
  still fails exactly as before.
- **Placement by measurement:** `image_fx.quiet_region(path)` → the image's calmest ONE-INK region
  + its mean luminance (choose dark vs light ink from data, not eyeballing) · `deckkit.pic_alpha`
  (native picture opacity — a faint plate that keeps its own hues, no scrim shape) ·
  `deckkit.design_intent(slide, envelope=…, rhyme=…, weight=…)` (declare a deliberate quiet/baseline/bleed
  register so the render-time lint audits intent instead of guessing it). **`role="appendix"`** marks where the backup/Q&A run
  starts: from there the slides are read at *briefing* density (reference material is dense on
  purpose — undeclared, a defense's backup slides draw TEXT WALL + CROWDED on every one), and the
  slide before it gets back the closing-slide exemption a trailing appendix otherwise steals.
  **`weight="left"|"right"|
  "asymmetric"`** declares a deliberately one-sided editorial composition — the art-director move where
  the opposite half is held as real air. It is the one register whose lint advice ("rebalance") would
  destroy the design, so it is declarable rather than argued with; undeclared lopsidedness still flags.
- **Decision / plan / grid:** **`eval_matrix`** (options×criteria scoring grid — `harvey_ball` fifths-fill
  glyphs or ✓/◐/✕ marks, `recommend=` tints the winner) · **`heat_matrix`** (category×category grid coloured
  by value, `scale="seq"|"div"|"risk"`) · **`tier_stack`** (one taper: `mode="funnel"` drop-off /
  `mode="pyramid"` layers, + `funnel()`/`pyramid()` wrappers) · **`gantt`** (dated task bars on a shared
  `axis_scale`, `lanes=` swimlanes, `today=` marker — durations & overlap, where `timeline` shows only points) ·
  **`sankey`** (CIRCULATION — where a quantity GOES, ribbon width strictly proportional to value on ONE
  deck-wide scale: money out and back, a supply chain, a budget split; `links=[(src,dst,value),…]`,
  columns derived from the graph, `col_labels=` names the stages. It reserves `label_w` label gutters
  and derives the ribbon area from what is LEFT, so hand it a whole region. Refuses a zero/negative
  value or a cyclic graph rather than drawing a width that means nothing).
- **Diagrams / patterns:** `quadrant`, `hub_spoke`, `timeline`, `before_after`/`image_tab`/
  `photo_triptych`, **`device_frame`** (a real screenshot in a `chrome="browser"`/`"phone"` bezel),
  `wireframe_grid`+`spec_list`, `corner_frame`, `photo_card`, `backdrop_motif`,
  `repeat_row` (N identical-except-index units as representatives + `…` + `×N`, shared detail said
  once — never N duplicate blocks).
- **Value→geometry mappers — pick by what the mark ENCODES, and never hand-roll the arithmetic:**
  **`axis_scale(x, w, lo, hi)`** maps a value to a POSITION on a track (dot strips, dumbbells,
  value-spaced timelines, `gantt`); any `lo` is legitimate there, because a dot at 47 between 40
  and 50 reads correctly. **`bar_scale(span, values, group=)`** maps a value to a LENGTH, and takes
  **no `lo` at all** — a bar's length is a proportion claim, so a non-zero baseline is not a scaling
  choice but a false statement (1.5 and 2.1 drawn from 1.4 look like 1 : 7). Call `sc.bar(slide, x,
  y, thickness, value, fill=…)` (`vertical=True` for columns): it draws zero-based, puts negatives
  on the far side of the zero line — the `max(abs(v))` slip picks the largest POSITIVE value and
  mis-places that line — and tags each bar so the build-time **`DATUM SCALE`** check can confirm the
  geometry still matches the numbers. A bar you draw yourself is unchecked, not assumed correct;
  `mark_datum(shape, value, group=)` opts it in.
- **Surface (dark / glass / print):** `glass_card`/`glow`/`scrim_overlay` (gradient+alpha fill),
  `offset_shadow` (hard letterpress/riso shadow).
  **`slide_background(s, color)` paints a SOLID page backdrop — use it instead of
  `box(s, 0, 0, W, H, fill=…)`.** It writes the real `<p:bg>`, so the backdrop is not a shape the
  user can select, drag or delete while editing (a full-canvas rect is, and click-dragging any
  empty part of the slide grabs it). Renders identically, lints identically — the linter
  synthesises the same background record from `<p:bg>`, so contrast, dark-plate and density
  checks are unchanged. **Non-solid backdrops keep the rect/`picture()`/`scrim_overlay` path**:
  gradients, images and alpha have no `<p:bg>` route here.
- **Publication & math:** `cover`/`colophon` (bookend the deck), `sources_page`, `specimen_card`;
  **`equation_native`** (EDITABLE LaTeX-subset math — real text runs, renders everywhere; the default) /
  `equation_png` (rasterised LaTeX, for 2-D math: fractions/matrices) / `eq_par` (inline runs).
- **East-Asian (CJK) accents:** `seal` (vermilion chop/印章 stamp — the one red accent on an ink deck),
  `cjk_numeral` (壹·贰·叁 section markers vs Latin "01"). See `references/east-asian-aesthetic.md`.
- **Diagram kit (general flowcharts):** `node` + `connector` / `flow_chain` (straight links between adjacent nodes) + `elbow_connector` /
  `loop_path` (elbow / U-shaped paths for a feedback/repeat loop, a return, or a link between NON-adjacent
  nodes) — any architecture from rounded-rect/pill/circle nodes (+ diamond/parallelogram/cylinder when
  formal flowchart notation applies — see the Standard-notation crib in `design-gallery.md`) with
  **stroke semantics** (solid=required
  · dashed=optional · dotted=feedback) and **shape semantics** (straight=adjacent flow · elbow/U=loop /
  return / non-adjacent), exactly one `hub` (hub optional in the system-architecture recipe — the
  focal path can carry emphasis instead)  *(NB two similarly-named helpers: **`hub_spoke`** draws the
  whole radial FIGURE — one centre + labelled spoke nodes on a ring; **`hub_spokes`** only draws the
  CONNECTORS from an existing hub to existing nodes. Reach for `hub_spoke` to build the diagram,
  `hub_spokes` to wire one you laid out yourself.)*; `diagram_island` (bright figure panel on a dark slide);
  `concentric_rings` (nested framework); `step_list` (numbered process, vertical/horizontal).
  - **This kit draws conceptual BOX-FLOW only — not physical science schematics.** For a
    **labelled science schematic** explaining a principle / mechanism / experiment / definition (a
    **free-body / force diagram, optics ray path, electric circuit, chemistry apparatus + reaction,
    vector / coordinate geometry, wave / field** — physics · chemistry · biology · engineering · any
    subject), NOT the node/connector kit. Two faithful build paths (pick by precision-vs-polish):
    **matplotlib / a domain library** → transparent PNG (the safe default when the exact geometry/labels
    ARE the meaning — deterministic, correct-by-construction), OR — for a **complex / fancy / generated-
    template-matched** schematic whose geometry isn't load-bearing — the **OpenAI image tool for a
    text-free styled visual with the labels overlaid as native editable text**. **Never bake labels or
    unverifiable geometry into a generated image** (garbled text + wrong physics). Recipes, the
    image-tool workflow, and the **domain-accuracy fidelity gate** are in
    `references/schematic-diagrams.md` — build it correct (a wrong schematic misleads worse than none).
- **Editorial / consulting furniture:** `insight_banner` (so-what bar), `bilingual_lockup` (CJK+tracked
  Latin headline), `highlight` (inline `<k>keyword</k>` recolour), `ghost_numeral` (faint watermark
  ordinal), `concept_equation` (ZINE=MAGAZINE word-equation), `pull_quote`/`standfirst`, `cta_button`/
  `cta_pair`, `status_stamp`/`corner_tab`, `spec_card`, `year_badge`, `gradient_rule` (2-stop brand rule),
  `catalogue_frame` (double-line specimen frame — museum/eastern presets).
- **Sample data / overlap:** **`designed_charts.distribution`** (SPREAD, not just the average —
  `groups=[(label,[v,…]),…]`; `kind="auto"` gives a box plot at n≥5, mean ± error at n=3–4, and
  **refuses n<3**; every observation overlaid; `err="sd"|"se"|"ci95"` is printed ON the figure).
  **Reach for it whenever a value is a mean of MEASUREMENTS rather than a count** — per-subject Dice,
  per-run latency, per-rater score. A bar chart of such means hides n, the shape and the outliers, and
  is the one chart choice the literature calls a defect (Nature Methods, *Kick the bar chart habit*).
  · **`designed_charts.marimekko`** (width = segment size, height = its split → cell **area** = the
  absolute quantity; what a 100%-stacked bar throws away) · **`designed_charts.radar`** (profile across
  3–8 axes, ≤3 series, zero-anchored spokes — raises outside that; prefer `small_multiples` for
  "who wins per metric") · **`venn`** (2–3 sets, `zones={"1":…,"12":…,"123":…}` by set index; zone
  labels are placed and SIZED from each region's own geometry, and one too long for its lens raises.
  Circles are equal — area encodes nothing by design).
- **Micro-viz:** `dot_meter` (●●○), `tradeoff_list` (+/−), `segmented_bar` (cumulative 100%), `meter_bar`
  (a single percentile/share/progress row — track + accent fill + a value label **vertically centered on
  the bar**; use this instead of hand-building "track box + fill box + number", which is how value labels
  end up floating off the bar's centerline; canvas-safe by construction — an overflowing value
  auto-shortens the bar instead of leaving the slide) · **`unit_grid`** (an isotype/waffle field —
  N square cells sized to fit the region, `filled=` of them accented, plus a **mandatory unit label**
  saying what one cell IS. Reach for it when the COUNT is the point — 34 attributed paintings, 12 of
  40 sites, the "N in 100" framing — and ALSO when a share is so TINY a bar would hide it: a 1%
  sliver is a hairline, one dark cell in a field of a hundred is unmistakable. Use `meter_bar` for a
  single large percentage/progress row instead. It refuses a texture rather
  than a count (8,412 cells is a texture), and refuses a blank unit label, because an unlabelled grid
  of squares means nothing) ·
  **`range_bars`** (the "football field" — floating min–max bars per row on a SHARED axis, for a value
  RANGE per category: a valuation band, a forecast spread, a min–max estimate. Use `dot_strip` instead
  when each row is really one best-estimate point).
- **Provenance:** **`source_note`** (the per-SLIDE source line — `sources`, `as_of=`, `label="来源"` on a
  CJK deck; auto-lifts clear of a `footer`, so call it last). `sources_page` defends the *deck*; this
  defends the *slide*, which is the unit that actually travels — screenshotted, pasted into a memo, shown
  out of order. **DEFAULT ON in the `briefing` register and on any slide whose numbers a reader could act
  on;** a chart whose source sits 14 pages away is unsourced at the moment someone doubts it.
- **Photo on-brand (`scripts/image_fx.py`):** `duotone` / `grayscale` so a colour photo doesn't fight
  the accent (riso/brutalist/ink/luxury/museum), then `picture(fit="cover")`.

If the user gave a **style example** (Q4),
build to your **style brief** of it *per the chosen mimic mode* (`references/style-analysis.md`) —
**Mode A:** match its palette/accents, density, title treatment, and figure/table/equation motifs
(override the deckkit defaults to suit); **Mode B:** recreate its structure, density, and the 2–4
borrowed components + signature motif, but keep the topic-fit palette/type already locked in the
Step-2 design plan — do NOT carry the example's colours.
A few rules that matter (see `references/design-principles.md`):
- **Use the source's own figures, WHOLE — integral is the default.** For *any* deck
  (research, work, exec, teaching): if the source — paper, report, doc, existing slide, or a
  chart already produced from the code/data — has a figure (architecture, results, a plot),
  use *that*; don't redraw it (slow, risks wrong detail) and don't chop it into pieces. Many users
  *prefer* the whole figure even when it's dense (it's the artifact they know and trust), so
  when a figure feels too busy, your *first* move is to give it a whole slide — large, with an
  **assertion title + a one-line caption** pointing attention to the part that matters (e.g.
  "the orange line is this quarter", or "rightmost column is ours") — not to crop it down. Reach for cropping only to (a) **trim**
  surrounding page header / caption / whitespace (leaving a small margin, never flush), or (b) lift
  **one cleanly-separable sub-figure** that genuinely stands alone. Chopping a multi-panel figure into a few columns
  *loses context and changes what the authors showed* — do it only when the whole is truly
  unusable on a slide, and prefer to **confirm with the user** before discarding panels.
  Build native diagrams only for structure with no source figure.

  - **Cropping, PDF extraction (`extract_pdf.py`), the see-it `crop_helper.py` loop, and panel-grid reassembly → `references/asset-production.md` §Figures. Read it IN FULL before you crop, trim, or extract any figure**, including from a PDF — it holds the three 🔴 crop rules (crop the whole SEMANTIC object; the auto-detected bbox is only the plot panel; zoom each of the four edges afterwards), the rule that a legend you add on the slide does NOT substitute for the figure's own axis labels, and the never-crop-blind loop.

- **Animated results (embedding + sparingly generating GIFs), turning raw data into the RIGHT chart type (editable native vs raster; non-Latin = native, no tofu), and computing a REAL domain visual — plus the plot-must-render-correctly rules (dense sampling, legend never over the data, always view the PNG) → `references/asset-production.md` §Charts, GIFs, and computed domain visuals. Read it before you produce any chart, GIF, or computed image.**

- **Generated visual plates (atmosphere / conceptual) — by taste & purpose, opt-in; full mechanics in
  `references/image-generation.md`.** Generate where it genuinely helps (no quota), styled to the deck;
  **never bake words/numbers/labels/charts/logos into a plate** (those stay editable objects / real
  assets). **Each plate must be *highly topical* — depict THIS slide's actual subject, not a generic
  "fancy" image that could sit on any slide** (name what it shows, else cut). **Place plates
  consistently — never a one-off generated *header* on a single body slide** (title chrome is
  `title_bar`'s; a content plate goes full-bleed / side-panel / inline, one role + art-direction across
  the plated slides). Generate with **no key** (auto-detect the FREE rungs: native imagegen →
  `generate_images_codex.py`; build the manifest with `image_prompts.py`). The OpenAI-API path is
  **metered and gated** — an available key is not consent; ask first (🔴 `image-generation.md`
  BILLING GATE), keep assets in
  `~/Downloads/<deck>/assets/generated/`, place with `deckkit.picture(fit="contain"|"cover")`, and
  render-check (calm space behind text, no pseudo-text/fake charts, subject whole, real things right).

- **Brand logo / wordmark on every page (single-entity decks: real mark → `deckkit.wordmark` → ask; never a faked replica) and the SVG icon family (ONE open-licensed family, palette-recolored, the treatments, the rule-of-thumb + five quality marks) → `references/asset-production.md` §Brand logo and the SVG icon family. Read it before you place a logo or the first icon.** Craft detail also lives in the untouched `references/icons.md` / `references/image-generation.md` (routing table rows above).

- **Speaker notes — for a PRESENTED deck, put the spoken script in the notes, not on the slide.**
  For any deck the user will *present* (especially a conference talk, defense, or lecture), move the
  full sentences off the slide into speaker notes with `deckkit.speaker_notes(slide, "…")`.
  The slide shows the phrase; the notes hold what the presenter says. **The notes text comes from
  the content plan's Spoken thread — pipe it, don't re-draft** (the planner's VOICE PASS and claim
  ledger already covered it; a builder-invented narration bypasses both). Notes don't render on
  the slide, but the lint measures them (the DECK STATS `notes` column + the `NO NOTES` warn) and
  ships them to the critics in its `--json` — they also show in Presenter View and on printed
  Notes Pages, so the user can rehearse without the slide becoming a wall of text. Offer this at
  hand-off; it directly serves the "few words per point" rule. **For a read-alone deck there is no
  presenter** — the explanatory prose belongs **on the slide** (a reader won't open the notes), so
  keep the sentences visible there rather than hiding them in notes.
- **Layout & diagrams — full rules in `references/design-principles.md`; the essentials:**
  keep a `deckkit.GUTTER` (~0.4 in) between elements and clear of the footer; build **balanced
  split panels** and **equal-gap stacks** from one grid — `columns(n)` (horizontal) / `rows(n)`
  (vertical), with symmetric outer margins (an intentional asymmetric split still keeps equal
  outer margins, and don't strand a narrow element in a too-wide column); point
  `arrow(direction=…)` the way the flow moves (down/up between stacked boxes), keep repeated
  connectors evenly spaced and adjacent blocks **gapped with a clearly visible gap (≥ ~⅓ `GUTTER`, never near-touching)** — derive the stack pitch from `rows`/`vstack`, not a pitch that barely clears the block height — and centre a lone
  glyph in its box; place figures/plates with **`picture(..., fit="contain")`** so the subject
  is never cropped (`cover` only for edge-tolerant texture).
- **Never hand-pick a y for an auto-growing block — measure or anchor.** A bottom callout
  placed at an eyeballed low `y` grows *down* into the footer when its text wraps (the #1
  recurring layout bug). Use **`bottom_callout()`** (anchors to the footer band, grows up),
  get the safe region from **`content_band()`**, and pack content-height blocks with
  **`vstack(..., bottom=…)`** (equal gaps + no overlap by construction, errors at build time on
  overflow). Use `measure_callout/measure_bullets/measure_text` when you must position manually.
  **A block that grows can be measured — every one of them, so this rule is followable rather than
  aspirational:** `measure_table(rows)` · `measure_timeline(events, orientation=, polarity=)` ·
  `measure_takeaway_rail(label, hero, body, w)` · `measure_chip(title, sub, w)` ·
  `measure_modbox(role, fname, w)` · `measure_node(label, sub, w)`. The last four are *enforced by
  their own component* (`h = max(h, measure_…)`, the way `callout` has always enforced
  `measure_callout`), so a chip/modbox/node cannot be built too small for its own text — size a
  row of chips with `ch = max(measure_chip(t, s, cw) for t, s in stages)` to keep it even.
  `takeaway_rail` now MEASURES its body and returns its bottom y; it used to reserve a fixed 2.0in
  and put a long body's ink at y=5.45, inside the footer band, with every gate reporting clean.
  Then run the Step-5 render self-check.
  - **Those measurements are CALIBRATED against the renderer in CI, and that is why you can lean
    on them.** Everything here trusts one number — how wide the renderer will set this string —
    and when that number drifted narrow (bold text in font-collection families measured at
    regular width, 3.9% short), every guard built on it silently PASSED while the text wrapped
    anyway: a caption sized for one line put its second line on top of a footer, and the lint
    agreed with the build because both were computed from the same wrong number. `tests/` now
    renders real strings and compares the ink against the prediction, one-sided and tight on the
    side that hurts: the measurement may be a little conservative, never optimistic. So trust it
    to the inch — and still keep a real gap, because an estimate that is *correct* is not the
    same as one with margin.
  - **Reserve the bottom callout's space BEFORE sizing content above it — don't add it last.**
    `bottom_callout()` returns its TOP y; the recurring mistake is to hardcode tall panels/cards
    (e.g. `y=1.7, h=2.5`) and *then* drop a callout on top, so the bar overlaps the cards' bottom
    edge. Call the callout FIRST, then size content to end **a full `GUTTER` above** its returned
    top: `top = dk.bottom_callout(s, 0.6, W-1.2, "要点", "…"); card_h = top - GUTTER - card_y`. A
    *near-zero* overlap is not harmless — the bar draws on top and **clips the cards' rounded
    corners** — so require a visible gap, not just non-collision. (The build-time lint now warns
    **`SLIVER_GAP`** on panel-on-panel grazing — a 0.005–0.10in seam between panels or a panel and
    a picture — and the Step-5 render self-check still eyeballs the seam; reserving the space by
    construction remains the fix, the warn is the net.)
- **Never hand-pick an x for a LABEL either — derive it from the thing the label names.** The
  y-rule above has an x-twin, and it is the more common miss because nothing crashes: a caption,
  a tag, a unit, a legend key, an axis note is *positioned* rather than *anchored*, and it lands
  near its subject instead of on it. Every such element gets its x from one of exactly three
  sources — the same grid column as its subject, its subject's own measured edge, or its
  subject's centre — and never from an offset nudged off a neighbour until it "fits". **Two
  measured failures, one class:**
  - *Caption on the wrong grid.* A four-panel figure is ONE picture, so its panels have no shape
    geometry to align to; the captions went onto the text grid (`ML + i*CW/4`) while the panels
    sat where matplotlib put them, at **unequal widths** — each panel keeps its own aspect ratio,
    so equal quarters are wrong by construction. Fix: have the plotting script export each
    panel's span as a fraction of the figure (`ax.images[0].get_window_extent()` after
    `fig.canvas.draw()`, over `fig.get_window_extent().width`) and place captions from the
    picture's *placed* rect — `dk.picture` returns the shape, so `pic.left/914400` is the real x
    after `fit="contain"` letterboxing. Backstopped by the **`CAPTION NOT ALIGNED`** render lint.
  - *A tag nudged into a corner.* A Chinese gloss for an English product name was placed at
    `(mx + 1.46, yy + 0.24)` — past the end of the rule, above the next row — giving one unit
    three left edges and four baselines, so the eye could not tell what it belonged to. Fix: an
    apposition is not a separate element. Same paragraph, same baseline, one left edge:
    `[[(name, …, FONT), ("　", …), (tag, …, EAFONT)]]`.

  The general rule behind both: **an element that annotates another element is not free to be
  anywhere.** If you find yourself adding a constant to make a label sit nicely, the constant is
  the bug — ask what edge it should share and compute that instead. Only the caption case has a
  lint; the rest is on you, which is why it is also PRE-FLIGHT 9.
- **🔴 Gate the geometry at BUILD time — end the build script with `dk.lint_layout(prs, strict=True)`
  before `prs.save()`.** `strict=True` makes it a *real* gate: an unresolved CRITICAL **raises and the
  deck is never saved**, so you can't accidentally ship a broken layout to the render/critic (plain
  `lint_layout(prs)` only *prints* and relies on you noticing — use it only when you deliberately want a
  non-blocking report, e.g. a known off-canvas bleed). This is the cheapest place to catch
  the mechanical layout faults: it runs in-process in milliseconds, *before* the slow render +
  visual-critic round, and walks **every** shape — however it was placed, the grid helpers or raw
  coordinates — reasoning about each label's **ink** rectangle (where the glyphs actually land), so it
  stays quiet on the generously-sized frames real builds use. It **hard-fails (CRITICAL)** on seven
  things: content (text ink / a card / a non-bleed image) **off-canvas**, text **overflowing** a visible
  box, **text-on-text** overlap, a **connector routed through a block** (`CONNECTOR_IN_BOX`), a **decorative RULE
  drawn through a text block's ink** (`RULE_THROUGH_TEXT` — a divider/hairline placed at a hand-picked `y`
  that the text above it later grew into; derive the rule from the block's measured end, never a guessed
  coordinate), **a slide part that violates its own schema** (`OOXML_SHAPE` — the cardinality and order
  of the elements this toolkit writes by hand. 🔴 This is the only defect class where the file **does not
  open at all**, and it is the one every other check here is structurally blind to: they are geometric,
  pixel-based or semantic, and none asks whether the part is well-formed. Measured: two `Build(s)` on one
  slide left TWO `<p:timing>` elements — `save()` silent, LibreOffice happy, `lint_layout` clean, and
  `preflight_check.py` read the *duplicate* as more compliant, so the deck got a tick for the thing that
  broke it; the first human signal would have been PowerPoint offering to repair the file. `anim.apply()`
  now refuses a second call outright — a second Build's steps were never in the first's sequence, so
  keeping either tree ships a click order nobody wrote — and this code is the net under it, because the
  next hand-written element will not carry its own guard), and **CJK runs with no `<a:ea>` font** (`CJK_NO_EA` — set
  `deckkit.EAFONT` before building; catching it here saves the render round-trip lint_deck previously
  needed. When it fires anyway, **`dk.retrofit_ea(prs, "<face>")` on the line above the lint** is
  the fix for the deck in hand — setting `EAFONT` cannot be, since the runs already exist — and it
  covers the groups, table cells, fields and chart text this check is blind to. Pass the face unless
  `EAFONT` is set; it raises rather than fixing nothing. `EAFONT` afterwards keeps the NEXT build
  clean, except on a redesign fix-pass, whose runs never reach `set_font()` at all); it **warns** on **display numerals in an old-style figure face** (`OLDSTYLE_FIGURES` — digits at mixed heights make a big number visibly bob; the figure components resolve a lining face themselves via `deckkit.numeral_run_face`, so this fires only on hand-set runs — a taste call, deliberately not a build blocker), on a label/figure **escaping its card**, a **single
  line left off-centre** in a card, content **reaching the footer**, and **two panels nearly
  touching** (`SLIVER_GAP` — a 0.005–0.10in seam between panels, or a panel and a picture: the
  hand-picked-pitch bug). It also warns on the two faults a PER-SLIDE check structurally cannot
  see, both measured on a delivered deck *after* both lints had reported clean: **`DUPLICATE_TEXT`**
  — the same string rendered by two separate shapes on one slide, whose real causes are an
  ORPHANED copy of an earlier layout left behind by repeated patching (the tell: your coordinate
  edits appear to do nothing, because two layouts are running at once), a component's own
  auto-label printed beside a hand-written one, or a name repeated in both a list and the diagram
  under it — and **`CHROME_SLOT_DRIFT`** — a per-slide source line that does not sit where the rest
  of the deck puts its own. 🔴 **The fix for slot drift is never to nudge the strays**: the slot was
  a constant each page applied by hand, and a rule a page can decline to follow is not a contract.
  Route every source line through ONE helper that ignores any x/y the caller passes. *(Measured:
  11 source lines, 8 pinned and 3 placed wherever their page's last block ended — one rendering
  `as of <date>` inside a diagram box. Prose held 8 times out of 11.)* (Each code's plain-language
  meaning + first fix: `references/troubleshooting-faq.md` §4.) Every CRITICAL it prints is real *when the deck's fonts are
  installed* — when a font is substituted for measurement it says so and carries ~1 line of slack
  (conservative, may under-flag), so it never fabricates. It is a **net, not a substitute for
  looking** (it can't see contrast, z-order, a figure smothering text, or shapes inside groups — the
  critic's job). The **layout contract** below maps to it as: the lint *enforces* rules 1 & 3 (off-canvas
  + text-on-text as CRITICALs) and *warns* on 5 (off-centre) and footer; the rest (padding, fit,
  grid-gap, diagram-bbox-first) it doesn't check — the named helpers satisfy those *by construction*, so
  you rarely trip the net in the first place:
  1. **Stay in the safe area** — get the rect from `content_band()`; only full-bleed hero/divider art bleeds. (On a provided/registered template, pass `content_band(slide, top=<the template's title-band bottom>)` so the safe rect honours the template's own header/footer instead of the deckkit default.)
  2. **Give text padding** — inset every label ≥0.1in inside its card (`cx+0.2`, width `cw-0.4`); flush-to-edge reads as a mistake.
  3. **No text-on-text** — one column/stack owns each region; never drop a second text box into the same rectangle.
  4. **If it doesn't fit, resolve it** — `fit_text_size(runs, w, h, start)` gives the largest size that fits; else shorten or grow the box.
  5. **Text in a *self-contained* block → equal top/bottom padding (vertically centre it)** — anchor it `MIDDLE` over the block's own rect: draw the block, then place the text at that block's exact `(x, y, w, h)` with `anchor=MSO_ANCHOR.MIDDLE` (wrap this as a small deck helper so centring is automatic, not per-call), whether it's one line or several. Placing text at a **hand-picked y-offset inside a fixed-height block** is the recurring "the takeaway text is closer to the top edge than the bottom" bug — the padding must be equal *by construction*, not eyeballed (the `OFFCENTER` warn fires on a lone-line card). *Carve:* a one-line reading column that must top-align with a taller sibling column under a shared header stays top-anchored (alignment beats centring).
  6. **Grid/stack over hand-picked y, and leave a real gap (~`GUTTER`)** — *and this includes the
     DIVIDERS between blocks: a hairline at a guessed `y` is crossed by the text above it the moment
     that text is edited and wraps one line further. Derive it (`rule_y = stack_end + pad`, where
     `stack_end` comes from the loop that drew the stack), which `RULE_THROUGH_TEXT` now enforces.* — `columns()/rows()` for equal panels, `vstack(…, bottom=…)` for content-height blocks (no overlap, even gaps by construction), `content_band()` for the vertical extent. (On a provided template, the layout's **placeholders** already anchor content — these helpers are the no-template path; fill placeholders where the template gives them.)
  7. **For a diagram, compute all bounding boxes first, then draw into them** — lay out the rects (and reserve arrow channels), *then* place nodes/labels — never eyeball one shape against the previous one.
- **Colour.** Rotate `deckkit.ACCENTS` so diagrams aren't monotone; reserve magenta
  for emphasis. For a **sequence of blocks** (chips / cards / pipeline stages) give each a
  **distinct, deliberately-contrasted hue** via `deckkit.palette(n, ACCENTS)` — it returns `n`
  distinct fills and **warns if any two adjacent blocks aren't visibly different**; never reuse a
  hue for adjacent blocks and **never use a neutral gray as a category colour** (gray reads as
  disabled, not a category — it makes a coloured row look half-finished). **Bind each hue to ONE
  concept deck-wide** (the accent = the proposed method, or "risk", or one product) — a colour that
  means the same thing on every slide is the biggest "this deck is credible" move: see
  `references/semantic-color-contract.md`. **🔴 A hue used as TEXT must itself clear ≥4.5:1 on its
  background** — a vivid gold / coral / lime that looks great as a fill can render at 2–4:1 as small
  label/kicker/emphasis text on a light surface (invisible-ish), the recurring "the coloured text is
  too faint" bug. So keep TWO tokens per accent when needed: a **bright fill-only** variant (rules,
  bars, icon tiles, header bands) and a **darker text-safe** variant (`contrast_ratio(...) ≥ 4.5`)
  for any run set in that colour — verify each bound hue's *text* value with `deckkit.contrast_ratio`
  at design time, not just the fill. **The same split covers a MARK ON A FILLED GROUND — an icon
  glyph on its tile, a symbol/number on a coloured chip, an arrowhead on a band — which must clear the
  WCAG non-text bar ~3:1 against *that ground*, not just against the slide.** The classic misses are a
  same-hue pair (a teal glyph on an aqua tile) and a dark-on-dark pair (a coloured glyph on a
  near-black tile) — both invisible. `deckkit.icon_tile` guards this by construction: it reads the
  icon's ink from the PNG (or takes an explicit `glyph=<colour>`) and auto-nudges the tile to ≥3:1, so
  **prefer `icon_tile` over hand-placing an icon on a raw `box`**; when you compose a mark on a fill by
  hand, pick it with `deckkit.contrast_ratio(mark, ground) ≥ 3` (or invert to white / near-black). Name the closing slide
  for its purpose, in the deck's language ("Conclusion" for an English talk; 结论/总结 on a Chinese deck).
- **Accessibility.** Keep text ≥4.5:1 on its fill (`contrast_ratio`; `chip`/`modbox`
  auto-pick a readable text colour) and never encode meaning by colour alone. Set
  **alt-text** on every informative figure — `deckkit.alt_text(shape, "one-line
  description")` after `add_picture()` — for screen readers; it doesn't render (invisible
  to the critic) so make it a build habit. More in `references/design-principles.md`.

- **Equations & inline math symbols → `references/asset-production.md` §Equations and inline math. Read it IN FULL the moment the deck needs any formula, variable, or math glyph** — it holds the 🔴 editable-`equation_native`-by-default rule and the `equation_png` 2-D carve, the math-font dependency to flag at hand-off (`references/deck-setup.md` §Fonts owns the font itself), formula sizing, the never-Unicode-super/subscript rule, and transcribe-from-paper / derive-from-code fidelity.

- **One language.** Keep the whole deck in the chosen target language — don't drift
  (no stray English on a Chinese deck, no English headings over translated bullets).
  Technical terms / proper nouns / acronyms / units / code may stay original; only
  build mixed/bilingual decks when the user asked (`references/multilingual.md`).

Copy `references/examples/build_example_generic.py` (brand-free) — or a registered
template's own `build_example.py` — for how the helpers compose. **For the single-author path,
copy its per-slide-function scaffold too** (STYLE block → one function per slide with a plan-row
docstring `role=… | form=… | build:…/static:… | takeaway='…'` → an ordered `SLIDES` registry →
`main()`): the docstrings make plan↔code correspondence greppable instead of remembered, and it
does not change "build the whole deck in one script run" — `main()` always builds every slide.

**Scaling up — section fan-out.** For a **tiny deck (~≤5 slides)** one author writing one build
script is both cheaper and more coherent — **that's the default there**. From **~6 slides up,
fan out** (when the host can dispatch subagents); also fan out at any size for
**independently-sourced sections** (different papers/datasets/areas). *(This threshold has moved
twice, 15+ → 9 → 6, both times on the same evidence. The old rule was weighed on TOKEN cost,
where one author is genuinely cheaper — no context is duplicated — and wall clock was never on
the scale. Measured across five real build sessions, the build step is 40–71% of all
model-active minutes, and it is one agent generating serially into a context that runs ~500k by
mid-build. Fan-out does not make the deck cost fewer tokens; it makes the tokens happen at the
same time, and it gives each author a fresh ~60k context instead of the coordinator's saturated
one — which also buys better rule-following, since a 500k context is where instructions start
getting missed. The 9→6 move added a second measurement: a 13-slide deck built solo ran 241
round-trips against a ~125 budget with a 1.00 batching ratio and 37 slide images read one
message at a time — the batching rules were IN context the whole time and stopped being
followed, which is precisely the failure a fresh 60k context prevents.)*
🔴 **The decision is RECORDED, not assumed: `design_plan.build_shape` in `.deck-gates.json`** —
`"fanout — <n> sections"` or `"solo — <reason>"` (e.g. `solo — host has no subagent dispatch`,
`solo — 6 slides but one tightly-coupled argument`). The hand-off gate requires it on any deck
of ~6+ content slides and never blocks on the CHOICE — solo is legitimate on every host and
mandatory on hosts without dispatch — only on the absence of a decision, exactly the
`form_reach` pattern. It exists because this rule was prose: the 241-round-trip deck above was
13 slides, well past the threshold, and nothing anywhere asked why it was built solo. The
rule that keeps quality high: **centralize coherence, parallelize only the independent
work.** The coordinator (you) keeps the comprehension brief, the arc, and a single
shared `style.py` (palette/font/chrome — copy `references/examples/style_example.py`);
then dispatch **one subagent per *section* (not per slide)** in parallel, each
importing that `style` and exposing `build_section(prs)` (copy
`references/examples/section_example.py`), each self-rendering its own section to
optimize it; finally `scripts/assemble.py` runs them in order into **one** deck (no
fragile .pptx merging). Don't do one-agent-per-slide-with-neighbour-chat — it drifts,
fights the single-file artifact, and doesn't speed up the parts that actually cost
time. Full workflow (incl. the critic panel + finding-routing) in
`references/large-deck-orchestration.md`.
🔴 **Fanning out the BUILD does not change the REVIEW shape.** The sectioned critic panel
(per-section critics + one whole-deck coherence critic, at every tier — `references/critic-panel.md`)
belongs to a **large** deck, ~15+ slides, because a 40-slide deck read as one document is a worse
review. It is not triggered by having used section authors: a 10-slide deck built by three authors
is still reviewed by the normal two focused lens critics reading the whole deck. Keep the two
thresholds apart deliberately — wiring them together would quietly add critics to every mid-sized
deck and spend the wall clock this fan-out just saved.

**Motion & builds — the animation that matters is in-slide "appear" builds, NOT slide transitions.**
🔴 **Do not "animate" a deck by putting a fade transition on every slide — that adds nothing and is the
lazy mistake to avoid.** What "add animation" means here is **revealing a slide's content one beat at a
time on click** (an *appear* build) so the audience follows the speaker instead of reading ahead.
**Builds are the USER's opt-in choice** (the interview asks it on presented decks; see Step 0) — this
section is about how to build them WELL *once the user has opted in*; if they opted out, the deck is
static and that is correct, not a missing must. The two layers are **not** equal:
- **(1) In-slide appear builds — THE real work, WHEN the user opted in.** *You* decide WHERE (which
  slides earn a staged reveal): reach for it wherever stepping the reveal will *emphasize*, *engage*,
  or *guide* — a multi-point list, a **pipeline / multi-stage diagram** (stage at a time), a
  **multi-part argument**, **before→after**, **evidence→takeaway**. Leave title / divider /
  single-image / scan-all-at-once slides plain. Not every slide needs a build (a plain stretch is
  fine) — but **a slide that DOES get a build is staged FULLY**: 🔴 **every content element on it is
  assigned to a build step and reveals in a deliberate reading order — never animate some blocks while
  the rest sit pre-shown from frame 0** (the "half-animated slide" is the exact weirdness to avoid).
  The static base holds ONLY the persistent scaffold — the title/header + any frame, axes, or
  always-true context the beats land on; everything that is *content to be paced* begins hidden and
  accumulates. Group the shapes of one thought into one step (a box *and* its arrow reveal together).
- **(2) Slide-to-slide transition — optional, secondary, off the critical path.** A calm deck-wide
  `slide_transition(s, "fade")` is *allowed* but never the point; a deck with **no** transition and good
  appear-builds beats one with a fade on every slide and no builds. Decide it once; **don't count
  "added transitions" as having animated the deck.**

Use `scripts/anim.py`: draw ONLY the persistent scaffold outside steps, then wrap **each content beat**
(the first one included) in a `Build.step()` — one bullet/block/stage per step, in reading order, so the
content area opens EMPTY and fills in click by click — then `apply(effect="appear")` (instant) or
`"fade"` (soft). Recipe in `references/animation.md` ("bread-and-butter build" + "full staged reveal").
A slide must still read correctly **fully-built** (for print/PDF) — builds layer on a correct static
slide, never fix a cluttered one.

**Record a one-line motion manifest** as you go — for each slide, `build: <what reveals,
in order>` or `static: <why nothing to pace>`, plus whether the deck-wide transition is on.
You'll hand this to the critic in step 5 (it can't *see* motion in a static render, so it
judges your motion *design* from this manifest plus the build-candidates it spots in the
pixels). **The canonical home is the per-slide function docstrings** (the scaffold above — the
`build:`/`static:` line lives in each slide's docstring and is handed to the critic as-is); a
comment block in `build_<deck>.py` remains the fallback for template-specific build_examples
that don't use the scaffold.

### 🔴 PRE-FLIGHT — tick these 12 before the first render, EVERY deck, no exceptions
*(The Step-4 SIGNATURE PROOF is not "the first render" in this sense — it is a one-slide probe of a
deck that does not exist yet, so most of these 12 have nothing to check. Run the ones that apply to
that single slide (legibility, no placeholder text, lining figures), and run the full 12 before the
first WHOLE-deck render as always.)*
This is the fixed boarding-pass between build and render. **Emit it as twelve literal ✓/✗ lines** (in
your working notes or the build script's tail comment) — writing the ticks is what forces the checks
to actually run; a deck with un-ticked pre-flight items is not ready to render.

**🔴 First run `python3 scripts/preflight_check.py <deck>.pptx --build build_<deck>.py` and paste
its block into the ticks** (add `--selfread` / `--static` to match the deck's mode). It decides the
MECHANICAL half — speaker-notes coverage (1), build timing present/absent (2), every `build:`
docstring actually having `Build.step` calls (3b), native charts + `equation_native` (4), the deck
carrying an as-of date (7), **meta-annotations and unfilled `<slot>`/`{slot}` template text leaked
onto a slide (8)**. With `--build` it also reads the SCRIPT: a literal stride constant in a placement
loop (the #1 geometry defect), and a **bar of sample means** — a computed mean/median fed to a
column/bar `native_chart`, which hides n, the spread and the outliers; the fix is
`designed_charts.distribution`. Items 2, 7 and 10 are **advisory** — whether builds were opted in, whether
any claim is time-bound, and whether a font exists on the PRESENTER's machine are all facts absent
from the file, and a check that fails on what it cannot know is one people learn to ignore. Exit 1 means not ready;
`NOT CHECKED` + exit 2 means it could not run, which is never the same as clean.
**It also emits four hard FAILs that are NOT numbered items** — each is a defect no geometry check
can see, so when one fires, read it and fix the deck rather than routing around a check whose rule
was never written down: **(i) mono overflow** — `code_block` sets `word_wrap=False`, so a too-long
line does not wrap, it OVERFLOWS its panel, and a broken command line is not a cosmetic defect but a
*wrong* command *(measured: a shipped deck's `npx skills add …` install line rendered as three lines
and copied back as a repo path that 404s — the one line a persuaded reader must transcribe exactly
was the broken one)*; a line within 15% of its box is reported as **tight**, not clean, because the
default `MONO` is Consolas — absent from macOS and most Linux — and the substitute face is wider,
which is how the historical failure fit with ~10% margin and broke anyway. **(ii) mono face not
installed** — same cause, reported outright; fix it by setting a `MONO` that exists on the render
box, not by shortening the line until it looks fine locally. **(iii) Latin→full-width adjacency** —
a space appears BEFORE a full-width mark that follows a Latin run (`原生 PPTX 。`, `既搭 deck 、又给它
打分`, `（第 3 、 5 步）`). The renderer's CJK/Latin auto-spacer inserts the gap and python-pptx has no
switch for it, so the adjacency ITSELF is the defect: reword so a CJK glyph precedes the mark, or
drop the mark *(shipped on 5 of 12 slides of a real deck and caught only by a human at 5× zoom)*.
**(iv) non-positive text box** — `h = card_h - 1.42` with `card_h = 1.30` stores −0.12; the run
overflows a box that has no inside and every geometry check stays green because there is nothing to
overlap. `deckkit.text()` now raises at the call site, so a FAIL here means the box was built by
other means. A box under half a line of its own type is ADVISORY, not a FAIL.
**It deliberately does NOT decide 5, 6, 6b, 9, 11** — those are judgment (is the figure the real
artifact, does the first look land on the hero, is the title the takeaway) and it prints them as
still-yours rather than implying coverage. Item 12 keeps its own script. *(Why: eleven of the twelve
ticks were self-attested — the model wrote twelve checkmarks and nothing anywhere read them, which is
the exact silent-skip class the checklist was written to prevent.)* It exists because
these are the rules that history shows get *silently* skipped when they live only as prose — they are
judgment calls the render-time lint cannot measure (lint already covers: word load, ink coverage,
font drama, build presence, layout sameness, CJK ea-font, contrast, footer, overlaps — don't re-tick
those here; read its report instead).
1. **Speaker notes**: presented deck (screen-shared = presented) → every slide's notes = the plan's **Spoken thread, verbatim**, via `dk.speaker_notes` (deviations — e.g. a split/merged slide — noted in one clause); self-read → prose is ON the slides instead.
2. **Builds — opted-in? then FULLY staged**: builds appear only if the user opted in; every animated slide reveals ALL its content beats in order (nothing content-bearing pre-shown but the title/frame — no half-animated slide), starting from an empty content area (first beat included), with no spoiling summary/legend in the base.
3. **Plan↔code correspondence**: (a) mechanical — diff the design plan's per-slide rows against the slide-function docstrings (icon family included; the classic inline-mode miss); (b) spot-check — each `build:` docstring has matching `Build.step` calls in its function body; (c) **cover carries its promises** — the built cover shows the self-verify-(l) device, the motif's label/legend where the plan said the STRANGER TEST is satisfied by labeling, and the `logo plan:` asset placed as planned (official file untouched; on a single-entity deck a cover with no logo and no recorded `n/a` reason is a ✗; and a roster slide's declared `entity marks:` count is matched by that many REAL marks in the render — a generic glyph sitting in a mark's slot is a ✗, not a partial pass).
4. **Charts native**: every chart is editable-native unless a matplotlib look was deliberately chosen; legends sit off the data. Same bar for math: every 1-D equation is `equation_native`; raster `equation_png` only for genuinely 2-D layout (fractions/matrices), named as such.
5. **Evidence real**: every domain image/figure is the real computed/source artifact — no plausible stand-in; PDF crops checked on all four edges; every SOURCED photo comes from a sanctioned origin (Commons / Openverse / press kit / user file), its subject verified against caption/geotag/category, it is **watermark-free** (a watermark is an unlicensed-preview tell → reject the file; never crop/blur/inpaint the mark away), its license recorded (credit placed where required), it is **aesthetically vetted** (an ugly / under-construction / blurry / unrepresentative shot is rejected even when the subject is correct → re-source, or generate a declared-stylized illustration via the `searched, found but low-quality → generated, flagged illustrative` rung), and it is palette-treated so mixed sources read as one deck; no generated CONTENT image claims photographic reality for a real-and-specific subject (REFERENT RULE, `references/image-generation.md` — generated-template identity plates and declared stylized illustrations are exempt; a real subject with no findable photo uses a recorded `searched, none found → …` rung). **CLINICAL imagery carries one more check, before anything else:** no burned-in patient identifier (name, MRN/ID, accession, date of birth, study date, institution), read on all four edges and in any overlay/header strip rather than the middle — highest risk on a user-supplied scan or PACS screenshot, and a published figure is usually de-identified already but is still read. **If one is there, get a de-identified export — do NOT crop or blur it out and ship:** a crop can miss a second identifier in another corner and a blur is not a guarantee. Unlike every other item here this one is irreversible once the deck is sent. Any **text over a hero/photo/plate** is verified legible against the pixels — no image linework crosses the glyphs (a scrim only dims a bright line; cover it with a near-opaque panel), eyebrow/kicker included, with a clear title↔subtitle gap (render self-check "Text over an image").
6. **Colour keyed**: the semantic-colour ledger's meanings are taught on-slide (key at first use) and no accent appears outside its bound meaning; chrome stays quiet — the **loud** signature motif ≤3 appearances (a *quiet register signature* — faint grid/scanline, corner numeral, edge rule, small seal — MAY repeat on every slide; that is SYSTEM, not stamping) — AND the chosen preset's `guard` constraints hold on every slide (quote the guard line in the tick).
6b. **Register carries all pages (的风格要走所有页)**: the quiet register signature reaches ordinary interior slides, not just the cover/dividers — the `interior register:` contract cue is present on interiors, or a `none (flat by register — <reason>)` carve is recorded. A style dressed only on the bookends fails.
7. **Claims current**: every time-bound ledger row re-verified with as-of = TODAY; the deck carries its "as of" date.
8. **Language & hygiene**: one language throughout; zero meta-annotations ("placeholder"/"TODO"/"AI-generated"); voice pass done on every line.
9. **Eye path & anchoring**: squint each slide — first look lands on the named hero, 3–4 hierarchy levels survive the blur. Then, un-squinted, **name the anchor of every label** — caption, tag, unit, legend key, axis note: which edge does it share with the thing it names (its subject's left / centre / right, or the same grid column)? **List the slides that carry labels and the anchor each uses.** A label whose x is a constant nobody can justify is the defect; `CAPTION NOT ALIGNED` only backstops the captions-under-panels case, and **`TEXT_GRAZES_SHAPE`** backstops the *collision* half (a label's ink running INTO the bar/chip/node beside it — invisible to `TEXT_OVERLAP`, which measures text against TEXT). Neither sees a label that merely floats near the wrong thing, so the anchoring judgement is still yours. 🔴 **When `TEXT_GRAZES_SHAPE` fires, the fix is the label COLUMN'S EDGE, derived from how far the mark can actually reach — not the string.** Measured: the first repair shortened the text and the label still grazed, because a right-aligned column that clears the *axis* does not clear a bar that grows *past* it (`_name_r = ZERO − max(|negative value|)·SCALE − pad`).
10. **Hand-off ready**: font/portability deps + per-slide click order noted for the hand-off; open questions carried, not dropped; output dir resolved + announced (`~/Downloads/<deck>/` or the user's stated choice); image licenses/credits noted (sourced photos).
11. **Titles bound to takeaways**: every content slide's title IS the plan's takeaway or a compression keeping its subject + verb + claim; **list the slide numbers** of compressions and of noted exceptions (bare topic labels are fine on cover/divider/agenda/closing; a named exception covers: Mode A "match its title treatment", a registered user template with a fixed title register, or a slide whose planned takeaway demonstrably lands as its named hero / `insight_banner` / `takeaway_rail` — note which element carries it). Emitting the slide numbers, not just a ✓, is what forces the per-slide comparison.
12. **Form diversity & frame fill — EMIT THE TALLY**: **first run
    `python scripts/component_audit.py build_<deck>.py <deck>.pptx` and paste its two summary lines
    into the tick** (it takes ~50ms and reads the finished file, so it costs nothing and cannot be
    guessed). It states one fact — how many of the form components it can name a guarantee for this
    deck actually called (deckkit's wider form catalogue is ~59) — and points at clusters whose
    geometry matches a component the deck never used. **If it prints `NOT CHECKED`, the tick is not
    done**: a wrong path or an unreadable deck exits 1 and says so, rather than reporting clean.
    **It is ADVISORY BY DESIGN and must never be treated as a blocker:** geometry cannot tell a lazy
    hand-roll from a deliberate bespoke composition, and the deliberate one is the *signature move*.
    So for each cluster, either reach for the component, or write the one clause that makes the
    hand-roll a decision ("the track is the deck's motif — a meter_bar would centre the value and
    kill the gap"). *(Why this tick exists, measured: across three delivered decks the build scripts
    called 3 of 59 form components. Every other form was composed from raw box+text, re-inheriting
    the geometry bugs — a baseline short of the last bar, a value label off the bar's centreline —
    that the components were written to fix. SKILL.md had said "when a COMPONENT exists, BUILD that
    component" as prose for a long time; it was violated dozens of times and detected zero times.)*
    🔴 **And the hand-off gate now asks for the answer rather than printing the question.** When
    `--gate-check` measures a low reach against a build that is otherwise raw `box`/`text`, it
    **blocks until `design_plan.form_reach.waived` records a written reason**. It never blocks on
    the NUMBER — bespoke composition is legitimate and is often the signature move itself, and a
    catalogue cannot produce a Mondrian page. It blocks on the absence of a DECISION, because that
    is the failure that actually happens: nobody looked, and `sigs.py --list` is one call.
    *(Measured: a delivered deck shipped at 1 of 23 named components, and three of its review
    findings — a label grazing its bar, a value floating off a track's centreline, a reference line
    drawn three different ways — are defects the unused components prevent by construction.)*
    Then write the deck's form-family tally as one literal line (`cards/panels: N · diagram: N · chart/proportional: N · big-type/editorial: N · timeline/roadmap: N · hero-image: N …`) and check six things against it: (a) **no family >~40–50% of content slides** (the same band the Step-2 form-ledger diversity gate, the critic and `form-selection.md` use — a family landing inside the band needs the one-clause content reason the plan-time gate asks for, not a silent ✗) — a first draft's greedy default is the card/panel, and per-slide checks can't see deck-level sameness, so this tally is the one place the crutch becomes visible; (b) every slide whose content is a RATIO / FLIP / DIVISION / PROCESS uses the form that *shows* it (a proportional bar, a topology diagram, a split, a roadmap), not a box that states it; (c) each interior slide **fills its frame** — a slide whose content ends in the top half either gets enriched, merged with its neighbour, or names its deliberate quiet register in one clause; (d) **one canvas system** — no background value/colour flip landing on exactly one interior slide (a flip must recur as a divider family or bookend; on the generated-template branch the plate stays on every content page and rhythm comes from imagery strength — `ONE-OFF CANVAS FLIP` lint is the render-time backstop); (e) **icons where content is categorical** — list the slides whose content names tools/entities/roles/pillars/categories; each such slide carries the planned icon family (one family, palette-recolored) or a one-clause waiver — "opt-in" never waives this silently (self-verify (g)); (f) **architecture rotation** — emit a second one-line tally of each content slide's TAKEAWAY SLOT (bottom-strip / side-rail / inline / headline / none) and CONTAINMENT (panelled / direct-on-canvas): no single takeaway slot on more than ~half the content slides (a bottom strip on every page is a template tell — `BOTTOM-STRIP MONOCULTURE` lint backstops it), and on a calm canvas at least ~1/3 of content slides put their protagonist directly on the canvas, un-panelled. Emitting the tallies + the (b)/(c)/(d)/(e)/(f) slide numbers, not just a ✓, is what forces the deck-level look a slide-by-slide build never takes.

**Codex only:** after PRE-FLIGHT 12, follow `references/codex-runtime.md`. Its separate gate does
not change the global audit's advisory classification; it merely requires Codex to either use a
detected component or preserve a slide-specific bespoke rationale in the evidence record.

**Gates never collapse.** A quick / low-stakes / inline run scales the *size* of each artifact
(a 5-line content plan, a 10-line design plan), never the *existence* of the gates: interview →
content plan → design plan (with self-verify) → pre-flight → lint+stats → critic. Every rule-miss
this skill has shipped happened when a step was run "in my head" instead of emitted — if it isn't
written down, it didn't happen. **The auto-waiver/inline path is where this bites hardest:** with
no checkpoint audience, the build slides into a single greedy pass that reaches for the same
handy component on every slide and stops at "nothing's broken" — every gate above is a floor, and
only the emitted form-candidates (per-slide runner-up from a different family) + the PRE-FLIGHT 12
tally push toward the ceiling. A delegated deck emits them for itself, not for the user.

## Step 5 — Render, verify, then run the actor–critic loop
**You should already have run the build-time geometry gate** (`dk.lint_layout(prs)` at the end of
Step 4) and cleared its CRITICALs (off-canvas · overflow · text-on-text) in-process, so the render
loop starts mostly geometry-clean. `lint_deck.py` below then re-checks that geometry on the final file
as a backstop and adds the render/parse-only faults; the rest is what needs real pixels (crop,
contrast, balance, a tofu glyph, text on a busy image), which only the render shows.

**Iterating on a deck you already rendered? Add `--fast`.** `render_deck … --fast` fingerprints
every slide (its XML + rels + the bytes of the media it references, mixed with a deck-global digest
covering the theme/master/layouts/canvas size) against the previous run, then re-renders **only the
slides that changed** — it subsets the pptx to those slides, converts that, and overwrites just their
PNGs. Measured on an 18-slide deck: a full render is ~2.8s, a one-slide change **~2.3s**, and a run
where nothing changed **0.07s**. 🔴 **The no-op round is the big win, not the one-slide round** — a
no-op never starts LibreOffice, while any real render pays one ~2.5s start that dwarfs the page work,
so a one-slide round saves about a fifth. Never skip a re-render on the belief that rendering is
expensive; it is a couple of seconds. Output is byte-identical to a full render (verified), so the
critic and the render-time lint see exactly what they would have seen anyway. It falls back to a full
render — and says why — whenever the mapping could be wrong: slide count changed, every slide changed,
no cache, or the deck contains **auto slide-number fields** or **hidden slides** (LibreOffice drops
hidden slides from the PDF, so page N stops being slide N — a full render now warns loudly and
refuses to cache when the page count and slide count disagree). **Use it for the actor-critic fix rounds
and for post-delivery tweaks** ("change slide 7 to a chart"); use a plain full render for the first
render of a deck and whenever you pass `--deliverables`.

First **render and look** (`bash scripts/render_deck.sh <deck.pptx>` → one PNG per
slide). python-pptx writes blind — overflow, low contrast, a callout on the footer,
or a missing glyph only show up in the image. Fix mechanical issues and re-render.
**Chain build → render → lint into ONE command** — `python3 build_<deck>.py && bash
scripts/render_deck.sh <deck>.pptx --fast && python3 scripts/lint_deck.py <deck>.pptx --renders render`.
🔴 **`--fast` belongs in the chain itself, not in your judgment.** It is safe on the FIRST render
too: with no cache it prints `--fast fell back to a full render: no previous render cache` and does
the full one — same for a changed slide count, a deck-global edit, hidden slides, or auto
slide-number fields. So the flag costs nothing when it cannot help and saves a full render on every
round when it can. It was previously advised one paragraph above this command and omitted FROM it,
which is the same as not being there: the chain is what gets copied each round.
(The one command that must NOT carry it is the hand-off render — `--deliverables` needs a whole-deck
PDF and dies if you pass both.)
They are a strict dependency chain, so they cannot run in parallel, but they also need no
decision between them: running them as three messages buys nothing and pays the full
conversation context three times instead of once. `&&` already stops the chain at the first
failure, which is the same place you would have stopped anyway.
(First time on a machine, or a render errors? `bash scripts/check_env.sh` verifies
LibreOffice + the python deps and prints the fix for anything missing.)
**When anything in this step fails or flags** — a build exception, a lint finding you don't
immediately recognize, a render that produces nothing — open `references/troubleshooting-faq.md`
first: it maps every error surface (build exceptions · `lint_layout` codes · render failures ·
`lint_deck` findings · `[stats]` act-or-accept guidance) to symptom → cause → first fix. And when
you surface a finding to the user (in a checkpoint, FYI, or hand-off), say it in that page's
plain language — *what broke, why, and the fix applied or proposed* — never as a raw lint code
the user would need documentation to decode.
**Codex sandbox note:** LibreOffice may abort or produce no PDF when launched inside a managed
sandbox even though `check_env.py` passes; in that case rerun only the render command with elevated /
unsandboxed execution, then continue the normal render -> lint -> critic loop. This is an environment
permission issue, not evidence that the deck is malformed.

**Then run the layout lint** — `python scripts/lint_deck.py <deck.pptx>` (add `--json out.json` for a structured copy of findings + the stats block — hand THAT to dispatched critics instead of re-parsing console text; the lint auto-reads the `./render` PNGs beside the deck to add the colour/value-pacing row + the `FLAT RHYTHM` warn, or pass `--renders <dir>` — silently skipped when no renders exist, so it never changes a render-less run). `render_deck.sh` also emits `render/thumb_first.png` + `thumb_last.png` (~240px) for the critic's poster test. The build-time
`dk.lint_layout` (Step 4) already cleared the pure-geometry faults *before* this render; **lint_deck.py
is its render-time complement** — it re-checks geometry on the FINAL file and adds the faults that only
the rendered/parsed deck reveals (which `lint_layout` deliberately leaves to it). A cheap, deterministic
check, it flags **invisible/low-contrast text against its backing fill (an uncoloured run defaults to black and vanishes on a dark card), off-slide overflow, text overflowing the card behind it, uneven card heights in a
row, two solid blocks/images overlapping (neither contained), footer collisions, orphaned punctuation
/ widow (a lone 。/，or single glyph on the last line — 避头尾), CJK text with no EA font (the kinsoku
root cause), whole-page-image (editability), and orphan/empty slides**: exactly the failures the eye
misses (a callout tucked under a panel; a 2-line body hanging below a card; a 。 stranded on its own row). Fix every finding, re-render, and re-lint
to clean before handing to the critic. It also prints soft **`[warn]`s** (advisory, non-blocking) for
what the hard families can't fail on: **missing alt-text** on an informative image, a **math-font
tofu** risk (an `equation_native` font not installed on the render host), **LOW/BODY CONTRAST**
bands (1.8–4.5:1), **grouped-only content**, and the **accessibility set** — NO SLIDE TITLE /
DUPLICATE SLIDE TITLES / READING ORDER (screen-reader navigation), NON-TEXT CONTRAST (WCAG
1.4.11 for solid marks/lines) and **ICON CONTRAST** (the same 3:1 floor for a recolored
monochrome icon vs its backing — icons are PICTURES, so the check above cannot see them). Resolve them or consciously accept them (FAQ §7). The hard families also
include **TEXT ON IMAGE** — a render-pixel contrast estimate (<1.5:1) for text sitting on a
photo/gradient with no opaque backing, exactly the class solid-fill contrast checks can't see;
its 1.5–3.0 band is the TEXT-ON-IMAGE CONTRAST `[warn]`.

**🔴 RECORD the delivery mode once, in the build script, instead of retyping a flag:**
`dk.declare_delivery(OUT, "selfread")` beside `prs.save(OUT)` — one of `presented` · `textheavy` ·
`selfread` · `surface`. It writes `delivery` into `<deck dir>/.deck-gates.json`, which **both**
`lint_deck.py` and `render_deck.py --gate-check` read, and a recorded value beats a conflicting
flag in both (they say so and name the file). Why it is a 🔴 and not a convenience: a mode that
lives only in flags is a fact carried by memory, and it gets dropped. Measured on a delivered
14-page self-read deck — 20 `[stats]` lines with no flag, 10 with `--selfread`; the ten were the
~40-word *presented* budget applied to a deck nobody speaks, plus "14 of 14 slides have empty
speaker notes". Half the advisory output was noise the tool generated by not knowing what it was
looking at, and noise is what teaches people to skim gates. (`--briefing` is lint-only and is NOT
recordable — `render_deck.py` has no briefing floor, so recording it yields a deck that lints
clean and cannot pass hand-off; the lint refuses it by name and says why.)

**It then prints a DECK STATS block — the measured form of the design targets. READ it, don't skim
past it** (pass `--selfread` for a read-alone deck — it raises the TEXT WALL budget (~40→~90 words); `--briefing` for an **editorial data briefing** — an FT/Economist-style dense read where ~150 words beside six charts is the FORM, which raises the word budget to ~150 and the occupancy band to 80% rather than removing either check the way `--textheavy` does
and drops the presented-only SMALL TYPE / NO BUILDS warns; the other warns are mode-independent —
`--surface` for a poster/single-canvas artifact, `--textheavy` when the user explicitly chose
text-heavy density for a presented deck, or `--static` on a presented deck when the user opted OUT of
appear-builds (silences NO BUILDS — a static presented deck was their choice, not an omission), so the
budgets fit the delivery mode). Per slide it measures:
reading **load** (latin words + CJK chars/2) vs the ~40-word presented budget · **text% / ink%
coverage** vs its role's OCCUPANCY band (cover/divider ~25–35 · exec/summary ~45–60 · technical/evidence ~55–70; past ~70–75 is `CROWDED`) — note the lint measures INK, so read the bands as ink, not as their whitespace complement · **max font pt** · shape/picture/chart counts ·
**build** presence · **sim↑** (layout-skeleton similarity vs the previous slide); deck-wide it
prints the **font histogram + type-drama ratio** and **builds/transitions n/N**. Its `[stats]`
warnings name the rule they measure — **`TEXT WALL`** (word budget blown → cut copy to notes or
split), **`HOLLOW FILL`** (the page reads as full but most of its ink is a drawn CONTAINER — occupancy is a bounding-box union, so an outlined frame counts its whole footprint and a page carrying four characters inside one measured 49%. 🔴 **Ask whether the FORM is right before touching the spacing**: every other warning here points at geometry, and the repair for this one is usually to demote the container, not to re-space it), **`CROWDED`** (occupancy past ~70% — role bands: cover 25–35 · exec 45–60 · technical 55–70 →
subtract or split, don't shrink), **`LAYOUT SAMENESS`**
(3 consecutive slides share one skeleton → the §1.2 skeleton-rotation rule failed), **`FLAT TYPE`**
(no typographic hero → the type-scale drama rule failed), **`SMALL TYPE`** (body-median under the
canvas-relative ≈18pt-equivalent floor → fewer words, bigger type), **`SIZE SPRAWL`** (>3–4 font sizes
on one slide → use the declared type-scale tokens), **`NO BUILDS`** (presented deck with no
appear-builds → the motion manifest failed *unless the user opted out of builds* — then pass
`--static`), **`SKELETON VARIETY`** (<4 distinct layout skeletons
across an 8+-slide deck → the canvas architecture barely rotates), **`TIMID COVER`** (slide 1's
largest run under 2× body → the cover lacks poster scale), **`FLAT RHYTHM`** (when render PNGs are
present via `--renders`/`./render`: no light/dark or colour-temperature event across the deck → the
rhythm map's Background-mode column is single-note), **`WEIGHT MONOCULTURE`** (the deck puts its
visual weight on the SAME side page after page — a share, never a per-slide verdict. One lopsided
page is composition and this skill asks for it; `LOPSIDED` only speaks when a half is essentially
dead (<5% occupancy), and a per-slide balance metric would punish exactly the asymmetric editorial
compositions the taste protocol exists to produce, which is why the continuous quantity is used
ONLY as a deck-level share. Slides carrying `design_intent(weight=…)` are excluded from both sides
of the ratio — they were decided, not defaulted. Deliberately **not** in `SAMENESS_CODES` yet: that
composite is calibrated against this skill's own registers, and a new signal earns its way in after
it has been seen on real decks, not on the day it ships), and on CJK decks **`CJK TIGHT LEADING`** (multi-line
CJK at ≤ single spacing → use the script-aware default) and **`CJK-LATIN SPACING`** (both 盘古之白
conventions mixed → pick one deck-wide). Treat each `[stats]` warning as the NAMED design rule
having failed measurably: fix it or write one clause of why this deck is the exception, and **paste
the stats block into the critic's input** so the judges score numbers, not impressions. It's a safety
net for the no-overlap / fits-its-box / density / rhythm rules, **not** a
replacement for looking (it can't judge crop, balance, legibility, or fidelity).

**Codex only — close the execution loop before consent is treated as hand-off:** retain the final
lint JSON and component-audit JSON, complete `.codex-deck-evidence.json`, then run
`scripts/codex_delivery_gate.py` exactly as `references/codex-runtime.md` specifies, with a
`.codex-delivery-receipt.json` output. Before sharing a file path, download link, file citation, or
claim of completion, run `scripts/codex_handoff_guard.py` against that receipt and the final PPTX.
**No matching `CODEX HANDOFF GUARD: PASS` means no delivery** — report progress or an
**unverified draft** instead. A clean hard-lint alone is not a pass: unresolved card dominance, type
sprawl, CJK leading, or missing evidence stays blocked unless a precise, named waiver explains why
this deck is the exception.

**🔴 When the gate says clean and the pixels say broken, the PIXELS win.** Paint order is the fault
class that keeps proving this: a shape added after a text box is drawn ON TOP of it while every
geometry check stays green. Three real decks shipped that way — a footer hairline over a sources
line, a 150-tile field erasing a caption, a dashed rule of 40 boxes struck through a footnote — and
each was found by a human looking at a PNG. The lesson was not "add another rule": the old check
enumerated *causes* (this shape type, painted then, covering that much), and causes are unbounded,
so every exclusion in it was a hole. `OCCLUSION` / `RULE THROUGH TEXT` now measure the **union** of
everything painted over a text block, so a thing built from many small parts cannot slip a
per-shape threshold; and `TEXT NOT VISIBLE` asks the one question with a bounded answer — *does
this line render any glyphs at all?* — straight from the pixels, so it catches a picture, a group,
a gradient or a same-colour-as-its-ground block without knowing which it was. Still a net, not a
proof. The model remains
blind to: **shapes inside groups** (imported SVG and user .pptx files on the redesign branch),
**chart interiors** (neither linter opens a chart part, so a bad number-format code renders raw),
**rotated shapes**, **text measured with a substituted font** (the lint says so and carries ~1 line
of slack), and anything **LibreOffice draws differently** from what the XML implies. A clean lint
means "nothing the model can see is wrong", never "the slide is right" — which is the entire reason
this scan exists and why it is not optional.

**Also read what the lint says it did NOT do.** With no renders beside the deck the pixel-backed
families disable themselves; the run now prints one `[skipped] … NOT checked: …` line and carries
`pixel_checks` in `--json`. `0 findings` with that line present is a different sentence from `0
findings` without it, and only one of them means what it looks like.

**Render self-check — scan EVERY slide for these before handing to the critic** (they're
invisible in the build code and only appear in the pixels; catching them yourself saves a
critic round — full rationale in `references/design-principles.md`):

> **Look at `render/contact.png` first — then read every slide anyway.** The render writes one
> image of the whole deck beside the per-slide PNGs. It is the only view in which the DECK-level
> questions are actually visible: the light/dark rhythm, whether the bookends bookend, form
> variety, one chrome treatment stamped on every page, a canvas flip that lands on exactly one
> slide — the things `ONE-OFF CANVAS FLIP` / `TITLE-RULE MONOCULTURE` / `FLAT RHYTHM` /
> `BOTTOM-STRIP MONOCULTURE` measure and no single-slide read can see. 🔴 **It settles NO per-slide
> question and never substitutes for the reads below.** Measured: a page there is 46 px/inch, so a
> 23pt title is 15px and legible while **13.5pt body text is 8.6px and a 10pt source line 6.4px —
> both unreadable.** Typography, contrast, a label grazing its bar, an overlap, whether a number is
> right: none of that is decidable from the sheet. Use it to arrive at the per-slide read knowing
> which pages deserve the most attention; treating it as the visual check IS the "passed because
> nothing looked" failure this skill keeps finding elsewhere.
>
> 🔴 **Read the slide PNGs in ONE message — every slide, one tool block — then judge them one at a
> time.** This is the preamble's `round-trips × context` rule at the place it binds hardest: reading
> N slides in N messages re-sends the whole conversation N times, and by mid-build that context runs
> ~300k, so a 14-slide deck spends ~4.2M tokens to look at ~21k tokens of image. Reading them
> together costs the images once. **Batching the READS must not blur the JUDGMENTS:** walk the
> slides in order afterwards and **record a one-line verdict for EVERY slide** — `s07: ok` /
> `s07: teal glyph on aqua tile, <3:1` — because one aggregate impression over fourteen images is
> not the same act as fourteen scans, and the zoom-level checks this list demands (each icon tile at
> ~3:1 on its own ground; all four edges of every PDF crop) still need their own look. The verdict
> lines are the artifact that shows the scan happened; a slide with no line was not checked.
- **Overflow / contrast / footer / glyphs** — no clipped or spilling text, ≥4.5:1 contrast,
  nothing jammed on the footer, no tofu/missing glyphs, and **no orphaned punctuation** (a lone 。/，
  or single glyph stranded on its own row — set `deckkit.EAFONT` so PowerPoint's kinsoku keeps it
  attached, and widen/reword if needed).
- **No build/meta annotation visible** — scan for any text that describes *how the slide was made*
  rather than its content: "（可点击编辑的原生图表）"/"(editable native chart)", "(AI-generated)", "(placeholder)",
  "(draft/草稿)", "generated by…", TODO/FIXME. It must NOT be on a slide — delete it (it belongs in code
  comments or the hand-off). A leaked meta-label ships broken.
- **Stacked groups read as separate** — for stacked labelled groups (stat label+value+caption, stacked
  cards), the gap *between* groups is clearly larger than the gaps *within* one (proximity); no caption
  crowding the next group's label.
- **Balance & suitable space** — every element has a comfortable margin on **all four sides**:
  nothing crowds an edge, nothing strands a big dead gap (the right *degree* — not too tight,
  not too loose). Split panels + flanking margins equal; no large dead-white band beside a
  narrow element; a **figure beside text is anchored to its margin (not centred-and-far-
  stranded)** with the text one gutter away; repeated blocks/connectors evenly spaced; grid-
  aligned, nothing lopsided. **A column/stack inside a card fills the space below its header** — a
  ladder, a list, stacked chips should **distribute evenly** to fill the available height; don't
  bottom-/top-anchor and strand a visible gap between the header and the first item (compute the gap
  from the region — `(region_h − n·item_h)/(n−1)` — or use `vstack`/`rows`, never a hand-picked offset).
  **And every label sits ON the thing it labels** — a caption centred on its own panel (not on the
  text column divided by N, which is wrong the moment the panels are unequal), a tag on its subject's
  baseline and left edge. A label sharing no edge with its subject reads as floating even though
  nothing overlaps and nothing overflows; PRE-FLIGHT 9 makes you name each anchor, and
  `CAPTION NOT ALIGNED` backstops only the captions-under-panels case.
- **Block padding & no inflated filler** — text inside a chip/card/callout hugs the box with a
  **modest, balanced** top/bottom margin (middle-anchored; not floating in a tall box, not cramped).
  A short card must not leave a white strip at the bottom. **No oversized block faking a full slide:**
  a single short line of small font swimming in a big box is a placeholder tell — either *add real
  content* to fill it or *shrink the box to hug the text* and use the freed space; never inflate a
  container to cover a gap.
- **Font hierarchy (content < title)** — body/content/callout/label text is **visibly smaller** than
  the slide title (clear step between levels, ~1.4–1.8×); no body, formula, or chip label set as large
  as (or larger than) the title. The only thing that may exceed body size is a deliberate **hero**
  element (the one big numeral or the slide-defining equation) — and even it stays below the title.
- **Hero numerals read clean** — an **integral number stays on ONE line** (no "2026" broken into
  "202"/"6" — use `wrap=False` or a wide-enough box); digits are **uniform-height & baseline-aligned**
  (a lining-figure face — Helvetica Neue / Arial / Cambria — NOT an old-style-figure face like Georgia,
  whose digits sit at different heights); and a numeral run **aligns** with adjacent CJK/Latin on its
  line (`design-principles.md` "Big numbers", `font-guidance.md`).
- **Chart axis spans every bar; a cumulative doesn't double-count** — a bar/waterfall/dot chart's
  baseline/value-axis runs under **all** its bars (not stopping short of the last one), and a
  cumulative/waterfall shows increments *or* their total, never both as peer bars (a "+8 / +8.3 /
  +16.3" trio is a double-count); keep different quantity kinds in separate stacks. Prefer
  `designed_charts.waterfall` over hand-rolled floating boxes (`design-principles.md` "Designed plots").
- **Geometry matches the number** — read one bar/band/cell's *size or colour* against its *printed
  value*: a magnitude column/bar starts at **0** (a cropped axis makes 210/220/230 read as a ~3×
  cliff); a proportional shape (funnel band, bubble) is sized to `value/max`, not clamped up by a
  min-size floor that contradicts its label; a diverging/signed scale reads its **sign** (a true 0
  is neutral, not blue). deckkit defaults handle all three — flag any hand-rolled/matplotlib chart
  that doesn't (`data-viz.md` "Chart anti-patterns", `design-principles.md` "Designed plots").
- **Formula sized to content** — every equation's glyphs read at ≈ **body size** (not blown up to fill
  the slide width, not illegibly shrunk), and **consistent across slides** (same placed height); any
  inline variable/symbol is in **math format** (italic, real sub/superscript), never plain body letters
  or Unicode super/subscripts.
- **No rule/divider crossing text** — every hairline, divider and accent bar passes BETWEEN blocks,
  never through one. The build-time `RULE_THROUGH_TEXT` gate catches this deterministically now; if you
  see one in a render it means the rule was drawn at a hand-picked `y` computed from how long the text
  happened to be at the time. Fix the *derivation*, not the coordinate.
- **Footer collision / overlap** — no block crosses into the footer band and no two stacked
  blocks overlap. If one does, the cause is almost always a hand-picked `y` for an auto-growing
  callout/stack — fix it by switching to `bottom_callout()` / `vstack()` / `content_band()`, not
  a one-off coordinate nudge (that just recurs when the text changes). **Look specifically at the
  seam where content meets a bottom callout/bar:** a *wide* bar grazing the cards above it by even
  a sliver clips their rounded corners — there must be a visible gap, so size content to the
  callout's returned top minus a `GUTTER` (reserve its space before sizing content, don't add it last).
- **Adjacent / stacked blocks — a VISIBLE gap, not a sliver** — between any two same-axis blocks
  (stacked panels, side-by-side cards, pipeline nodes) the gap must read clearly: **≥ ~0.13in
  (~⅓ `GUTTER`)**. A ~0.02in seam (three panels at pitch 1.04 with height 1.02) reads as touching —
  a gap far smaller than the slide's own margins looks cramped even though nothing overlaps. Cause:
  a hand-picked pitch that nearly equals the block height. Fix: **derive the pitch from the region** —
  `rows(n)` / `vstack(..., bottom=…)` — so the gap is set by construction, never `block_h + 0.02`.
  (The build-time lint's `SLIVER_GAP` warn catches this class deterministically — an unaddressed
  one at render time means the build-time report was skipped.)
- **Bar labels sit ON the bar** — for any track+fill row (percentile / share / progress / "want vs
  have"), the value/percent label is **vertically centered on the bar's centerline**, not floating
  above or below it, and doesn't overlap the track. Use `meter_bar()` (which centers the value by
  construction) rather than hand-placing a number at a guessed `y`.
- **Marker captions sit UNDER their marker** — on a timeline / tick row / numbered-step row, each
  caption (date · title · sub) is **horizontally co-centered with its dot/marker**, *including the
  first and last*. The classic bug: an end marker sits near the slide edge and its centered caption
  gets clamped inward, so the caption drifts off to the side of its dot. Use `timeline()` or
  `spaced_centers()` (which **inset the end markers** so every caption stays co-centered) — never
  hand-roll a dots+captions row with a per-caption edge clamp.
- **Diagrams** — arrows point the way the flow moves (down/up between stacked boxes); adjacent
  blocks have a visible gap (never touching); a lone glyph/icon optically centred (ASCII, not
  full-width, for a centred mark on a CJK deck). **A connector / loop label (e.g. a feedback-loop's
  「修订」/「retry」) sits in the OPEN GAP next to the line — offset above a horizontal segment, or beside a
  vertical one, with clearance — NOT inside an opaque chip that STANDS OUT over the line.** A chip that
  contrasts with the slide reads as a band-aid; route the label into clear space so the line and text
  simply don't collide. (On a PLAIN background a label that knocks the line OUT in the background colour —
  the line breaking cleanly for the text — is fine; the band-aid is a *visible* chip, e.g. a white block on
  a coloured/textured slide. Add a subtle *translucent* backing only if the label must cross a busy area.
  See `references/design-principles.md` → "Connector labels".)
- **Block colours** — in a sequence of chips/cards/stages, every block is a **distinct,
  deliberately-contrasted hue**: no two adjacent blocks share a colour, and **no neutral gray
  sits in the sequence as if it were a category** (use `palette()` — it warns on both). A vivid
  block beside a gray one reads as half-finished.
- **Mark-on-fill contrast — an icon glyph on its tile, a symbol/number on a coloured chip** — the
  mark must stand out from the ground it sits ON (~3:1), not just from the slide. Zoom each icon tile:
  a **same-hue pair** (teal glyph on aqua tile) or a **dark-on-dark pair** (coloured glyph on
  near-black tile) is invisible — the exact bug a mid-tone tile hides. `icon_tile` auto-guards this
  (white/near-white glyph on a deep tile, or deep glyph on a pale tile); a hand-placed icon-on-`box`
  does not, so check it here.
- **Titles** — a subtitle/definition line has a clear gap below the title's accent rule; the
  kicker/eyebrow adds a section label, it doesn't echo a word the title already leads with. **The
  title CHROME itself is not one fixed template repeated on every slide** — an identical
  eyebrow + rule-under-the-title on all ~12 content slides is a template tell (creativity is a design
  metric, not just correctness). **`lint_deck.py` now backstops the most common case deterministically —
  `TITLE-RULE MONOCULTURE` fires when the same thin rule sits under the title at the same height on
  >60% of content slides** (a `head()`-style helper that stamps one treatment deck-wide is exactly how
  this regresses); the other treatments (tab/rail/ordinal) it can't measure stay on this self-check.
  Rotate **2–3 title treatments** across the deck (e.g. a classic
  accent-rule · an eyebrow in a filled tab/pill · a left vertical accent bar · a section ordinal ·
  a motif mark) so no two adjacent slides share the exact chrome and no single treatment dominates —
  the eyebrow-ornament analogue of the skeleton-rotation floor (`references/design-intelligence-addendum.md`).
  This does **not** fight the Repetition principle: the visual SYSTEM stays constant (same palette,
  type pairing, signature motif on every slide) — you rotate the *chrome treatment*, not the identity.
  That IS "repeat the system, vary the protagonist" (`references/design-principles.md` C.R.A.P.), not a
  license to make each title look unrelated.
- **Images** — the key **subject is whole, not cropped** (`contain` vs `cover`); a generated
  image of real things is **factually right** (relative size/proportion, count, colour); any
  **labels sit under the feature** they name. A **sourced photo is aesthetically usable**, not just
  subject-correct: reject an ugly / under-construction (cranes, scaffolding) / blurry / badly-lit /
  cluttered / unrepresentative shot — re-source, or generate a **declared-stylized illustration**
  instead (a beautiful accurate illustration beats an ugly real photo; `references/image-generation.md`
  aesthetic gate + the `searched, found but low-quality → generated, flagged illustrative` rung).
- **Text over an image (hero / photo / plate)** — read the title against the pixels behind it: **(a)**
  no image **line / edge / motif / frame-ornament crosses the glyphs** (a scrim only *dims* a bright
  Deco line — it stays visible; when the image carries linework where the title lands, cover it with a
  **near-opaque panel** α ≥ 0.88, a lower-third band or corner card filled to the canvas edge, never
  bleeding off-canvas); **(b)** every run — including a gold/tint **eyebrow** — clears ≥4.5:1 against
  what's actually behind it; **(c)** an **unmistakable gap** separates the big title from its
  subtitle/rule (a subtitle hugging the title's baseline reads as an error). Fix by strengthening the
  backing, moving the text to an empty region, or re-spacing — treat a title fighting the image as a
  real defect, like an overflow.
- **PDF figures cropped precisely** — for every figure pulled from a paper, zoom **each of the four
  edges** close-up (not a glance at the whole) and confirm: (a) none of the figure's own parts is
  clipped **or flush** (flush = cut); (b) no page text bled in (its caption, a neighbour's caption
  fragment, a running head, a page number, a stray body-text line); (c) the figure is
  **self-contained — its own x/y axis labels are present**, not silently replaced by a legend you
  added on the slide. The full element list + the plot-panel-bbox pitfall (the auto-detector's box
  excludes the axis titles/ticks/legend, so an eyeballed crop near it drops them) are under **“Never
  clip the figure's OWN parts”** in Step 4. A clipped, flush, or axis-label-missing crop is a real flaw, not a nitpick.
- **Motion & images by taste** — what's there earns its place (emphasises/engages/guides),
  nothing thoughtless; what's plain is fine.
**On native Windows (PowerShell / cmd) there is no bash — call the Python entry points
directly: `python scripts\render_deck.py <deck.pptx>` and `python scripts\check_env.py`.**
The `.sh` files are just shims that forward to those `.py` scripts, so macOS / Linux /
Git Bash / WSL keep working unchanged; everything else in the toolchain is already
cross-platform Python.

**If a render fails *after* `check_env.sh` passes** (a build/LibreOffice error mid-loop),
isolate it rather than thrash: the **build script is the source of truth and re-runnable**,
so comment out the suspect slide (or the shape you last added), rebuild + re-render to
confirm the rest is fine, then fix that one slide and restore it. A frequent culprit is a
bad asset path (a figure/GIF/equation PNG that doesn't exist) or a malformed `equation_png`
string — the Python traceback names it. Don't ship a partially-rendered deck silently; if
one slide can't render, tell the user which and why. (Symptom → cause → fix tables:
`references/troubleshooting-faq.md` §5 for render failures, §3 for build tracebacks.)

**If you used animation/builds:** the render (and the critic) see only the **final
built state** — they can't play the sequence (the anim.py timing is verified to
round-trip through real PowerPoint as native builds; LibreOffice just can't *play* it).
So verify the fully-built PNG reads correctly on its own (run the loop as normal), and
in step 6 **describe the click order** to the user. Builds are a layer on a correct
static slide, never a fix for a cluttered one.

### 🔴 THE POST-BUILD REVIEW QUESTION — ask it HERE, with the deck in front of the user

The render is clean, both lints are clean, the self-check verdict lines are written. **Now — not
at Step 0 — post the rendered deck (contact sheet + the slide PNG paths) and ask ONE question:**

| option | what runs | rough cost |
|---|---|---|
| **`fast` (default)** | 1 generalist critic, 1 round, top-5 claims re-checked | ~10–20 min · ~250k tok |
| `standard` | 2 lens critics (content · design), 2 rounds, top-10 claims — worth it for a defense / pitch / exec readout | ~30–60 min · ~600k |
| `thorough` | multi-critic panel + arbiter, 3 rounds, every claim | ~1–2 h · ~2M |
| `none` | no review — deliver as-is | 0 |

🔴 **On a runtime with NO choice UI — plain Codex chat, Kimi, a GPT surface, an API caller: the
norm, not the exception — ask it as ONE typed question and never fake a form.** Say it in the
USER's language. This is the same rule Step 0 carries, and it is repeated here because this
question has no interview block to inherit it from — and an unaskable question does not become a
default quietly, it becomes a default *silently*:
> The deck is rendered — slides are at `<path>/render/slideNN.png` (contact sheet:
> `<path>/render/contact.png`). Have a look, then tell me how hard to review it:
> **fast** (default — 1 critic, 1 round, ~10–20 min) · **standard** (2 lens critics, 2 rounds,
> ~30–60 min) · **thorough** (panel + arbiter, 3 rounds, ~1–2 h) · **none** (ship it as-is).

**A host that cannot DISPLAY images still asks it** — the paths are the deck: the user opens them.
What a no-image host may not do is answer the question on the user's behalf; that is the one
substitution this question exists to prevent.

Why the question lives here and not in the interview: at Step 0 it was a **blind** cost decision
about a deck nobody had seen, and blind is why `fast` could never be the default (a silent recall
drop the user never chose). With the deck visible the same choice is **informed** — the user has
already judged the thing itself, so the cheap tier is a proportionate default and declining
entirely is a legitimate answer, not a loophole. Three rules keep it honest:
- **The option texts carry the cost and what is skipped, every time** (the table above). On a
  RESEARCH-SOURCED deck, `none`'s option text must additionally say it skips the adversarial
  primary-source re-check — the one defect class the user's own eyes cannot catch — and the
  hand-off's `provenance:` line then reads `skipped — user declined post-build review`, never a
  tally that implies it ran.
- **`none` is recorded, not silent**: the standard `user-waived` critic waiver in
  `.deck-gates.json`, quoting the decline — `{"critic": {"waived": "<the user's words>",
  "waived_category": "user-waived"}}`, plus `{"provenance": {"waived": "skipped — user declined
  the post-build review"}}` on a research-sourced deck, so the record and the hand-off line say
  the same thing. (Codex path: `review_effort: "none"` + `none_opt_in`.) This is the machinery
  that always existed for exactly this.
  A surviving `fast` blocker still goes back to the user by name (the cap rule below), so the
  default tier never silently ships a known-broken deck.
- **Under a per-deck AUTO WAIVER, run `fast` — never `none`.** "You decide" delegates effort
  sizing, not the decision to skip review entirely; the FYI records `review: fast (post-build
  default — auto)` and the user escalates at hand-off if they want more. Auto MAY escalate above
  `fast` for a high-stakes purpose (defense / exec readout / pitch) with the reason recorded —
  `review: standard (escalated — defense deck, auto)` — it may only never decline.

Then run the **actor-critic loop** at the chosen tier — this is the quality engine, and the
critic is a *demanding* judge (see `agents/critic.md`), not a rubber stamp:
> 🔴 **Do not retype the dispatch below.** `python3 scripts/dispatch_brief.py prompt --brief <path>
> --role critic --lens A|B --round N --deck <dir>` prints it — ~220 tokens against the ~4,600 a
> hand-written one measured, and the CONTRACT CARD then comes from the one file every critic reads
> rather than being reconstructed at each dispatch (the reconstruction this step warns about
> below). The brief is written once, at Step 1, with `dispatch_brief.py init`; the tool refuses to
> emit a prompt while any required section is unfilled, so a hollow brief fails loudly instead of
> dispatching a critic that was told nothing. Everything the numbered item asks for still has to be
> in the brief — the tool changes where it is written, never whether it is.

1. **Critique.** Dispatch an independent critic subagent through the host's available
   multi-agent/subagent tool, pointed at `agents/critic.md`, giving it the rendered PNGs, the deck's **purpose + audience**
   (plus the interview's recorded **delivery mode + density choice**, so the rubric's density carves can apply),
   `references/review-rubrics.md`, the **motion manifest** from step 4 (so it can judge the
   motion *design* it can't see in a static render), **the CONTRACT CARD** (below), **and the
   source material** (so it can
   verify claims/figures/numbers, not just style). A *separate* agent matters: it judges the
   pixels, not your intentions. It returns structured JSON — `verdict`
   ("consent"/"revise"), per-slide `findings` (severity + concrete fix), strengths, the
   `plan_audit` + `probes` blocks, and (on a full-deck consent) a one-line `ceiling`.
   **Validate the review BEFORE acting on it (the anti-skim gate's consumer side):** run
   `python3 scripts/validate_review.py critic <json>` (schema conformance), then check
   `coverage.slides_opened` lists every slide in the critic's ASSIGNED scope (whole deck for a
   sole critic; its section's range for a per-section critic), `passes` covers both lenses on a
   sole critic, `stats_block_seen: true`, and `contract_card_seen` is not false when a card was
   sent. A review failing any of these is **rejected and re-dispatched once** with the gap named —
   never acted on.
   **The contract-card audit is checked by the same command, not by your eye.** `validate_review.py`
   requires the `plan_audit` block and the `probes` entry each lens in `passes` owes (content →
   `lens_a` + `memory_sentence`; design → `lens_b` + `per_slide`), every named subfield inside them,
   and refuses `contract_card_seen: true` over an empty or null `plan_audit`. That last rule is the
   one worth knowing: a review can otherwise assert it received the card while auditing none of its
   contracts, and `concept_landed`, `signature_move`, `register_interiors`, `takeaway_titles` and
   the rest — the entire mechanism by which declared design intent is tested against pixels — go
   unchecked with the deck still consenting.
   **The coverage half of that check is now MECHANICAL, at hand-off** — `render_deck.py
   --gate-check` re-opens the recorded review, counts the deck's real slides, and refuses a consent
   whose `slides_opened` does not reach them. So a **per-section critic MUST declare its range** or
   the gate reads it as a whole-deck review with holes: `"coverage": {"scope": [4, 9],
   "slides_opened": [4,5,6,7,8,9], …}`. (Why it was added: a schema-valid review of a 15-slide deck
   declaring `slides_opened: [1]` was accepted, recorded with a sha256, printed as *verified*, and
   passed every hand-off gate — "verified" meant the FILE still hashed to what was recorded, never
   that the DECK had been looked at. `slides_opened` is the anti-skim field; nothing compared it to
   the deck. The Codex delivery gate already bound it; this is the shared path catching up.) Arbiter outputs validate the same way (`validate_review.py arbiter`); an
   arbiter's `escalated_unreviewed` entries are handed to the next round's fresh critic as
   candidate findings (or, at the round cap, surfaced to the user with the other open questions).

   - 🔴 **ASK FOR THE REVIEW IN THE SHAPE THE VALIDATOR ACCEPTS — get it from the validator, never
     hand-roll it:** `python3 scripts/validate_review.py --schema critic` prints the contract as a
     JSON Schema you pass straight to the subagent as its structured-output schema. Same file
     publishes and checks, built from the same enum constants, so the shape a critic is ASKED for
     and the shape it is JUDGED by cannot drift. **Before this, the contract was readable exactly
     one way — by failing — and the failure lands AFTER the review has run**, when the agent's
     tokens are spent and the returned review cannot be filed at all. Measured on a real deck:
     both lenses ran, read all 12 slides and produced genuine findings (1 blocker + 7 majors + 6
     minors, and 3 + 4 + 4), and NEITHER could be recorded, because the dispatch had invented
     `{slide, severity, what, fix}` instead of `{id, slide, severity, dimension, issue, why,
     fix}`. That deck's `critic` block had to be hand-written as a classified waiver rather than
     recorded consent — the loop ran and the evidence file could not say so. Two things the flat
     schema deliberately does not carry, because they are conditional and it would lie about
     them: `plan_audit`'s per-lens obligations, and the coupling that `contract_card_seen: true`
     REQUIRES a real audit (both stated in the schema's own descriptions, both still enforced on
     return).
   - 🔴 **LAND EVERY RETURNED REVIEW ON DISK THE MOMENT IT ARRIVES, before you read it or act on
     it:** `python3 scripts/fanout_record.py put <deck-dir> --round critic-r1 --member <lens>
     --file <review.json>`, and for a member that died,
     `… miss <deck-dir> --round critic-r1 --member <lens> --why "<what happened>"`. Then
     `… status <deck-dir> --round critic-r1 --expect content,design` — it **exits 1** and names
     only the members to re-dispatch, so "the round is complete" is a check rather than something
     you remember. **A fan-out is otherwise atomic in the worst way:** results come back into your
     context, context is not a file, and one dead member costs the whole round. Measured on a real
     build — the DESIGN lens died on a session limit while the CONTENT lens had already produced a
     complete review (1 blocker, 7 majors, 6 minors) that was read out of the workflow result and
     never written down, so `validate_review.py --record` had nothing to register and the deck
     shipped with a `.deck-gates.json` holding only `delivery`. Recording the FAILURE matters as
     much as recording the result: a 19-agent round once returned `surviving: 0`, which reads
     exactly like "nothing was found" and was in fact "they all died". **This is persistence, not
     a channel** — nothing moves sideways between agents, because a critic that knows the author's
     intent stops being independent.
   - **Record the consent as EVIDENCE, not as a claim — add `--record <deck-dir>` to the validation
     you are already running:** `python3 scripts/validate_review.py critic <review.json> --record
     ~/Downloads/<deck>/`. It writes the `critic` block of `.deck-gates.json` **from the validated
     review itself** (verdict · blocker/major counts · the review file's path + sha256), and the
     Step-6 gate then re-reads that artifact instead of trusting a summary — a moved, edited, or
     revise-verdict review fails the hand-off. Run it on **every review, not once per round** — the
     field it writes is **`reviews_seen`**, the number of distinct review FILES it has been handed,
     so a standard 2-lens × 2-round panel records `reviews_seen: 4`. 🔴 **`reviews_seen` is not
     `rounds`** and the tool never derives one from the other: a round is N lens reviews of the same
     build, and nothing inside a review file says which round it belongs to, so only you know that
     number. `--record` preserves a `rounds` you wrote and invents none — which means `rounds` is
     the one hand-typed field in this block, and it is on you to keep it honest. On a high-stakes deck, `--record` on the
     arbiter's Job-2 payload files the corroborating pass under `critic.corroborated_by`. **Why this
     is not ceremony:** a record you TYPE at hand-off is self-certification — the model that skipped
     the loop writes the same JSON as the model that ran it, so both produce identical prose and
     only an artifact tells them apart. A hand-written record still passes, and is labelled
     `SELF-REPORTED` when it does.

   - **Hand the critic the approved claim ledger WHOLE — never a summary you retyped for the
     dispatch.** A critic can only check a slide against what it was handed, so every verified
     fact compressed out of the brief comes back as a false "unsourced" finding. Measured on one
     deck: **7 of 8 such findings in a round-2 review were briefing artifacts**, and the round
     they consumed was pure waste — a larger loss than any panel-size choice. The ledger already
     exists as an artifact at Step 1; pass the artifact, not your memory of it.

   - **The CONTRACT CARD's full field list is in `references/critic-panel.md` → "The CONTRACT CARD". Assemble it from the approved plans (declarations only, never rationale) at every critic dispatch — read the field list each time rather than reconstructing it**; an external/redesign deck with no Step-1 plan states "none-declared" instead. The validation gate above rejects any review without `contract_card_seen`.

   - **When a validated review comes back, read `references/critic-panel.md` → "Handling a returned review"**: the prior round's `strengths` as a do-not-harm ledger for the actor (and the rule that they are NEVER shown to the next fresh critic), the probes-vs-plan diff and its dispositions, and how a `ceiling` line is contained.

   - **Scale the critic to the stakes — and run it as a panel** (this is the main
     speed lever):

     - **Panel sizes, lens assignments and the arbiter cross-validation pass (including the asymmetric promote/discard rule) → `references/critic-panel.md` → "Panel composition by stakes". Read it at every dispatch, before choosing the panel.**

2. **Decide.** Stop as soon as `verdict == "consent"` (the critic would present it
   as-is) — not merely when the last round's issues are fixed.
   **At ANY stakes, reaching the cap with a surviving blocker/major is never a silent ship:**
   surface the unresolved finding(s) in the Step-6 note as an honest open question — the
   low-stakes analogue of high-stakes' "fail loudly at the cap" below. Cap the rounds by
   stakes so the loop converges fast: **low-stakes ≈ up to 2 rounds, high-stakes up
   to 3.**
   **The user's `review:` tier (the POST-BUILD question above) is the same rule with a handle on
   it:** `fast` = 1 round, `standard` = 2, `thorough` = 3, `none` = 0 (recorded as `user-waived`,
   never run). `standard` and `thorough` are pure ALIASES for the two stakes classes above — same
   panel, same arbitration, same fresh whole-deck re-review on every round. `fast` is the DEFAULT
   because the choice is made with the rendered deck visible — an informed cheap tier, not a
   silent one. At `fast` there is no second round to absorb a surviving blocker/major, so it goes
   back to the USER named, and the run does not end until they answer: either they authorise one
   extra round (a recorded exception to the cap) or the ship is recorded as *their* waiver, never
   the model's — this rule is what makes the cheap default safe. Tier table:
   `references/critic-panel.md` → "Review effort tiers".
   *(The cap numbers live in TWO places on purpose — here, because a cap is coordinator-enforced and
   nothing lints it, so layer 1 must carry it; and in `critic-panel.md`, which owns the rest. They
   must agree: change one, change both — the same drift hazard the distinctiveness rule carries
   below.)*
   > 🔴 **One exception to "surface it and ship": a surviving `timid` / `sanded-to-safe`
   > distinctiveness finding on a deck whose `boldness:` is `bold` or `experimental`.** There the
   > deck does **not** ship on your say-so — after the one improvement attempt, put the choice to the
   > USER in two lines: *(a) one more round — naming the concrete change you would make; (b) ship
   > as-is, recorded as a knowing accept.* Either answer ships it; what changes is **who waives**.
   > A deck the user asked to be bold and received forgettable did not deliver what was asked, and
   > you are the party with an interest in calling your own output good enough. **This is the only
   > taste finding that can hold a deck, it needs the user's own dial set to `bold`/`experimental`
   > to fire, and it is never a floor** (a bold idea that broke legibility is a floor finding first).
   > At `balanced+`/`conservative`, unchanged: one attempt, then ship with the note.
   > **Record the outcome in the Step-6 hand-off note** — `distinctiveness: user waived (bold)` or
   > `distinctiveness: resolved in round N`. Without it, "they accepted it" and "I never asked" are
   > indistinguishable afterwards, which is exactly the hole the gate lines were added to close.
   > *(Owned by `agents/critic.md` distinctiveness axis + `references/review-rubrics.md`; all three
   > must say the same thing — this rule has a history of drifting apart across files.)* If the first render is already clean and the critic consents, you're done
   in one round — don't manufacture extra rounds. Otherwise apply the blocker+major
   fixes, rebuild, re-render.
   > 🔴 **On a fanned-out deck, get the slide map before you fix anything** —
   > `python3 scripts/slide_index.py section_*.py` prints `slide N -> file:line function` plus each
   > slide's plan-row docstring. Section fan-out means YOU DID NOT WRITE THIS CODE, so a finding on
   > slide 7 otherwise starts with grepping three modules you have never read: on one measured
   > build that search cost 33 round-trips and ~30,000 output tokens (~9 min), re-deriving a map the
   > section authors already had. Read the map once; open files at lines after that.
   > 🔴 **Apply the whole promoted fix list in ONE message, then rebuild + re-render + re-lint in
   > ONE chained command** (`python3 build_<deck>.py && python3 scripts/render_deck.py <deck>.pptx
   > render --fast && python3 scripts/lint_deck.py <deck>.pptx --renders render`). The promoted
   > findings arrive as a list and have no data dependency on each other, so one `Edit` per finding
   > is the preamble's *1.00 tool per round-trip* failure with a fresh name: ~18 findings across a
   > standard two-round loop, each re-sending ~300k of context, is ~5.4M tokens spent to emit a few
   > hundred. Fixes that genuinely conflict (two findings on the same block, where the second edit
   > depends on how the first landed) are the exception — do those in a second message and say why.
   > This changes only how the edits are *transmitted*: every promoted finding is still applied,
   > still individually, and the change manifest still lists them one by one.
3. **Repeat.** The critic **re-reviews the whole deck fresh** (fixes introduce new
   issues). Converge; keep a short record of what changed each round so improvement is
   visible, not just churn.

**🔴 THE SEARCH BUDGET IS A SHARED, SESSION-SCOPED, NON-RENEWABLE RESOURCE — spend it like one.**
Web search is capped per SESSION (Claude Code: `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`,
default 200), the cap is shared with every subagent you dispatch, and **it does not reset between
decks in the same conversation.** Measured: one research fan-out — 12 research agents plus 7
verifiers, each searching freely because nothing told them otherwise — consumed the entire 200.
Nothing metered it and nothing warned; the exhaustion surfaced hours later, on a different task,
when a single lookup for a company's official logo could not run. The deck that needed that logo
shipped without it and said so on its own limitations page. That is the shape of the failure:
**the cheap, late, small lookups starve, because the big early fan-out took everything.**

Three rules, in order of how much they buy:

1. **Do the SMALL, NAMED lookups FIRST — before any research fan-out.** The logo, the brand
   colours, a licensed photo, one specific clearance number: these are a handful of searches, they
   are the ones that get starved, and they are needed by Step 2 anyway. Front-loading them costs
   nothing and removes the failure entirely.
2. **Budget the fan-out explicitly and say the number in each dispatch.** An agent with no stated
   cap searches until satisfied, and N of them do it in parallel. Write it into the prompt —
   *"you have at most 6 searches; spend them on the claims you cannot resolve any other way"* —
   and size the round so the whole fan-out stays under roughly **half of what REMAINS — not half of
   the original cap**. Half, not all: verification, mid-build fact-checks, and asset sourcing all
   still have to happen. *(Remains, not original, because the cap is SESSION-scoped and does not
   reset between decks: on the second deck of a conversation "half the cap" can be more than
   everything left. Step 1's dispatch rule says the same thing in the same words — they are one
   rule stated at the two moments it binds, so change one, change both.)*
3. **Record what you planned and what you spent**, so exhaustion is a number someone chose rather
   than a wall someone hit. When the budget IS gone, say so in the deck's limitations and in the
   hand-off — never let a missing fact read as an absent fact.

**🔴 PRIMARY-SOURCE GATE — research-sourced decks only, before hand-off.** When the deck's
load-bearing claims came from **web research** (every no-source deck, and any sourced deck where
research supplied slide-level numbers/quotes), the content critic verifying slides *against the
ledger* is not enough — a hallucinated or secondhand ledger row passes that check by construction.
So before hand-off, run one **adversarial primary-source spot-check**: independent verifier
agent(s) with live web access take the deck's load-bearing claims (every headline number, date,
direct quote, ranking, attribution) and try to **REFUTE** each against its **primary source** (the
original paper / the org's own post / official docs — never an aggregator), returning per claim
`CONFIRMED (URL) / WRONG / PARTLY-WRONG / UNVERIFIABLE`. **WRONG and PARTLY-WRONG are fixed before
ship; UNVERIFIABLE is hedged as unverified or cut — never shipped as established fact.** While
there, verifiers also flag the planner's PROVENANCE CONTRACT breaks (spliced figures, quote-mark
abuse — `agents/content-planner.md` §2, rubric item 10). Scale it to stakes like the critic itself
(a quick deck: one verifier over the top ~10 claims; high-stakes: a fan-out over all of them) —
**and the user's `review:` tier is the handle on that same scale** — `fast` = the top ~5 load-bearing
claims, `standard` = the top ~10, `thorough` = all of them. The tier narrows the SAMPLE and never the
gate; on a research-sourced deck the gate runs at every tier that RUNS —
this is the gate between "the slides match the ledger" and "the ledger matches reality."
**The one exception is `none` at the post-build question:** the user declined the whole review
loop with the deck visible, and this gate rides on it. That is the single most consequential thing
`none` gives up — a wrong number is the one defect the user's own eyes cannot catch — which is why
`none`'s option text on a research-sourced deck must SAY it skips this, and the hand-off's
`provenance:` line must read `skipped — user declined post-build review` rather than a tally.
**Ordering:** run the
verifier pass in parallel with (or immediately before) the FINAL critic round; any WRONG /
PARTLY-WRONG fix re-enters the normal rebuild → re-render → re-lint path, and a fix landing after
critic consent gets a cheap confirmation look (the touched slides, not a fresh full round) — gate
fixes never count against the critic round caps. **The gate's artifact (required, per the enforcement
invariant):** the Step-6 hand-off carries one `provenance:` line — `N claims checked · N confirmed
· N fixed · N cut/hedged` — plus the per-claim verdict list on request; a research-sourced hand-off
without that line means the gate did not run (Step 6's checklist lists it). Decks built purely from the user's own material skip
this gate — there, fidelity is to the provided source, and item 10 already owns it — **but** a
source claim that §2(b) re-verification *updated or replaced* with a web-found current value counts
as research-supplied, and pulls the gate in for those rows.

**High-stakes decks:** after each fix round's re-render, read `references/critic-panel.md` → "Verify the fixes and corroborate consent" — the arbiter re-check of the change manifest (with its required `dulled` flag) and the corroborated-consent rule that gates shipping. *(This is the "fail loudly at the cap" passage the round-cap rule above points at.)*

## Step 6 — Show the user, then iterate on feedback
Present the rendered slides (or a contact sheet) plus a short note: slides count,
purpose it was built for, and the font/portability caveat if relevant. **Tell the
user the exact output folder path (`~/Downloads/<deck-name>/`, or wherever they
chose) and ask them to open it and check the `.pptx`** — the rendered PNGs verify
layout, but they should confirm the editable deck itself opens cleanly on their
machine. **Then OFFER the two reserved deliverables rather than shipping them unasked** — a
**`.pdf`** (submission / email / print) and a **`viewer.html`** flip-through preview
(one `file://` link, any browser, any OS, no PowerPoint needed). It is zero-dependency, not
self-contained: it references the `render/` PNGs by relative path, so move the two together. They are deliberately not generated
during the build, because a deck still being edited makes them stale immediately. Ask in one line
("want a PDF and a browser preview?"); on a yes — or once the user confirms this is the final
version — run `bash scripts/render_deck.sh <deck.pptx> --deliverables` (or
`python scripts/render_deck.py … --deliverables`), which parks both at the deck root beside the
`.pptx`, and surface the two `file://` links then. **Re-run it after any later change** so the pair
never lags the deck. If you added any forward-looking content (per the fidelity rule), call that
out explicitly here so they can confirm it.

> **🔴 Run the gates on EVERY hand-off, whatever the user answers about the PDF:**
> `python3 scripts/render_deck.py <deck>.pptx --gate-check` — it runs every hand-off gate, renders
> nothing, and takes under a second. Add `--selfread` / `--textheavy` / `--surface` when that is the
> deck's delivery mode, exactly as you would for `lint_deck.py`, so the text budget it enforces is
> the budget that mode is actually held to — or, better, record it once with
> `dk.declare_delivery(OUT, "<mode>")` in the build script and neither tool needs the flag again.
>
> 🔴 **It reports EVERY failure at once — `[1/N] <section>`, so FIX THEM ALL, then re-run.** Fixing
> the first one and re-running is the habit this batching exists to kill: the gate used to stop at
> the first problem, which cost one round-trip per field at the most expensive point of the run.
> The only stops that still come alone are structural (no `.deck-gates.json`, unreadable JSON, an
> unknown recorded delivery) — every later gate reads what those could not produce.
>
> **One of those gates is SAMENESS, and it is the one that can send you back to the build.** The
> deck-level monotony signals (`LAYOUT SAMENESS` · `SKELETON VARIETY` · `CARD DOMINANCE` ·
> `BOTTOM-STRIP MONOCULTURE` · `TITLE-RULE MONOCULTURE` · `ENVELOPE MONOCULTURE` · `FLAT RHYTHM`)
> were measured on every deck and blocked nothing — printed as advisories under a line saying they
> were advisory. **≥4 distinct ones, with at least one structural, now block the hand-off.** It
> applies only to a deck that is ≥8 CONTENT slides (cover, closer and any declared
> `design_intent(role="appendix")` run excluded), landscape, and not `--surface` — calibrated by
> building and linting decks in the registers this skill itself prescribes, where a 6-slide status
> update, a 小红书 carousel and an appendix-heavy defense deck all trip 3+ signals *legitimately*.
> **Repetition alone does not block; four independent kinds of it do.** Type drama (`TIMID COVER` /
> `FLAT TYPE`) is deliberately NOT counted — it is one fact twice, and the skill's own
> must-stay-clean fixture emits both.
> Where the repetition IS the design, say so — the escape is a written reason, not a flag:
> ```json
> "sameness": {"waived": "<why this deck repeats on purpose — name the register>",
>              "waived_category": "series-frame | register-uniform | template-locked | reference-run | user-waived",
>              "codes": ["<exactly the codes the gate reported>"]}
> ```
> The `codes` list is the freshness binding, the cheap version of `critic.sha256`: a waiver written
> for a different state of the deck does not certify this one. **This gate is deliberately about
> MEASUREMENT, never taste** — whether a deck is *timid* stays the critic's distinctiveness axis and
> stays non-blocking at `balanced+`; whether it *repeats itself* is a share of slides agreeing with
> each other, which is a defect with a concrete fix. That is the skill's own test for what may hold
> a deck (`agents/critic.md`), and it is why these two live on opposite sides of it.
> **Why a separate flag exists at all:** the gates used to be reachable only through
> `--deliverables`, and the paragraph above deliberately makes that a *decline-able offer*. So on
> every deck where the user said "no PDF, thanks", the strongest gate in the skill never ran — and
> nobody could see that it hadn't. A gate whose execution depends on an unrelated user preference is
> not a gate.
>
> **🔴 The other one is TIMIDITY — the counterweight, and the newer half of the same idea.** Every
> blocking signal above punishes a deck for being too MUCH or too SAME. Nothing could hold one for
> being too SAFE: `TIMID COVER` / `FLAT TYPE` are excluded from the sameness composite, and the one
> force that can call a deck forgettable — the critic's distinctiveness axis — is non-blocking at
> the default dial and lives inside a review the user may decline. **Measured, on a real build: a
> 12-page deck was iterated ten times, every pass driven by an advisory, and every pass made it
> flatter** — the dark pivot page deleted for `ONE-OFF CANVAS FLIP`, content cut for `TEXT WALL`,
> the type scale collapsed for `SIZE SPRAWL`. Each of those advisories names the ambitious repair
> FIRST ("enrich with a second column of substance", "repeat the treatment as a divider family");
> subtraction is merely the cheaper way to make the number disappear, and **with feedback on one
> side only, the cheap way always wins.** The user's verdict was *设计能力变弱了* and nothing in the
> pipeline had said so. So: `TIMID COVER` · `FLAT TYPE` · **`TEXT-ONLY DECK`** (most content slides
> carry no chart, no figure, no drawn form — every page's protagonist is a sentence) ·
> **`MONOTONE INK`** (the rendered pages are effectively greyscale), blocking at **≥2 with ≥1
> structural** (the two type signals are one fact twice, so drama alone can never hold a deck).
> It stands down under `boldness: conservative` with a recorded `deliberately restrained:` move —
> there restraint IS the position — and under the same size/aspect floors as sameness. Where the
> quiet is the design, name the register:
> ```json
> "timidity": {"waived": "<the register, named>",
>              "waived_category": "register-restrained | text-is-the-artifact | template-locked | user-waived",
>              "codes": ["<exactly the codes the gate reported>"]}
> ```
> 🔴 **When it fires, take the repair the advisories name first, not the one that deletes.** The
> measurable half of timidity is now gated; the unmeasurable half is still the critic's, and this
> is the moment to notice you have been optimising a warning count instead of designing.

**`--deliverables` refuses to run until `<deck-dir>/.deck-gates.json` records that the Step-2
design plan, the Step-5 critic and the Step-6 provenance pass actually ran.** Write it when the
critic loop converges — `{"critic": {"verdict": "consent", "rounds": N}}`, **the Step-1 arc
competition** (`{"content": {"arc": {"chosen": …, "rejected": [{"name": …, "why_lost": …}],
"divergence": …}}}` — the losers and their clauses ARE the artifact, since `picked
contribution-first` on its own is a sentence anyone can write without a competition having
happened; `{"content": {"waived": "<why this deck had one possible arc>"}}` if it genuinely did.
This joined the file because the arc was the one Step-1/2 decision whose verdict reached only the
*conversation* while every other one reached this record — and the Codex path had already been
binding it), the design plan's
`boldness` / `signature_move` / `carried_by` / `form_ledger` / `icon_family` / `palette` /
**`motif_generates`** (background · markers · one page whose geometry IS the motif — a motif that
only recurs is an ornament with a schedule; carved out, like `signature_proof`, under a
`conservative` dial with a recorded `deliberately restrained:` move) /
**`type_scale`** (the three tiers as numbers — SIZE SPRAWL tells authors to draw sizes "from the
deck's declared type-scale tokens", and this is where they get declared) / **`signature_proof`**
(the ANCHOR PROOF — a LIST `[{"role": "signature"|"complex"|"data", "slide": N, "png": "<rendered
png>"}, …]`, one entry per anchor: the rendered evidence that the signature move SURVIVED
the build, that the design HOLDS the deck's densest page, and that the charts speak its visual
language. A move that exists only as a sentence gets sanded back to the safe catalogue and nobody
notices, because the plan still reads bravely — and a design proved on one spacious page tells you
nothing about the other two failures), and the provenance pass's **per-claim
`claims` list, never a summary tally** (a tally is written by the same pass that would have skipped
the refutation). A gate you deliberately skipped is **waived in writing** — never omitted; the tool
prints the reason, so a skip is visible instead of invisible. 🔴 **The CRITIC waiver must be
CLASSIFIED, not just written** — an unclassified one is indistinguishable from never having run
the loop, so the gate rejects it (the `design_plan`, `provenance` and `density` waivers take a
written reason only — the category is required for the critic alone):
```json
{"critic": {"waived": "<a sentence someone can disagree with later — ≥24 chars>",
            "waived_category": "already-reviewed-minor-edit | cap-reached-majors-open | external-deck | no-dispatch-on-host | user-waived",
            "inline_ran": true}}
```
`no-dispatch-on-host` = the runtime cannot dispatch a subagent (and it **additionally requires
`inline_ran: true|false`** — "ran inline in my own context" and "was never reviewed" are different
claims, and the hand-off note reads identically for both unless this file separates them) ·
`already-reviewed-minor-edit` = a 1–2 slide edit to a deck that already passed its loop ·
`user-waived` = the user was asked and chose to ship over it · `external-deck` = a deck this skill
did not author (redesign diagnosis / critique-only run) · 🔴 **`cap-reached-majors-open` = the loop
RAN to its round cap and majors are still open** — the other four all describe a loop that was
SKIPPED, so this is the only honest label for the commonest non-consent ending, and it
**additionally requires `open: ["<each surviving finding>"]` (non-empty) and `surfaced_to_user:
true|false`**. Reach for it instead of `user-waived` whenever the loop ran: `user-waived` is a claim
about a conversation, and writing it for a conversation that did not happen is exactly what
classifying the waiver was meant to stop. **If none of the five fits, the honest move
is to run the critic.**
This file is the hand-off's evidence, not a formality: the model that
skips a gate is the same model that would write the note claiming it ran, so both produce identical
prose and only an artifact tells them apart (`references/handoff-checklist.md` lists it).
The `critic` block is **written by `validate_review.py --record`, not by hand** (Step 5) — you supply
only the two blocks no tool can produce for you: the whole `design_plan` block enumerated above and
the provenance pass's per-claim list. *(The one exception: `--record` writes a CONSENT record from a
real review, so it cannot produce the waiver shape above — a waiver is always hand-written, which is
exactly why it must carry its category.)*

**Before you write the hand-off note, read `references/handoff-checklist.md` — every deck.** It is the ONE authoritative list of what the note carries (minimal caveats + next steps, never a recap or self-praise) and of the conditional REQUIRED lines the owning rules point here for: `provenance:`, **`review:`** (the effort tier that ran + how it was reached) and **`cost:`** (subagents · tokens · wall-clock — a dial whose bill is never shown builds no intuition), click order, image licences, the GIF note, accepted advisories, `distinctiveness:`, the delegated-picks recap, the optional `ceiling` line, and the two taste-ecosystem offers — **including the save-this-look offer, which is skipped entirely under a per-deck auto directive: never an un-consented registry write.** For a Codex-verified PPTX, the hand-off note is forbidden until the final-file guard passes; an explicit **unverified draft** is the only disclosure alternative.

**For a long deck (~15+ slides), show work at ~50%, not only at 100%.** When a build is large enough
that a wrong direction is expensive to unwind, render the first few finished slides (cover + a couple
of content archetypes) and check in **before** completing the rest — "here's the look and the first 3
slides; continuing in this direction unless you'd change something." Cheaper than discovering a
palette/density/structure mismatch after all 20 are built. (A soft check-in, not a 🔴 stop: under a
per-deck auto directive, post the early renders as an FYI and continue without waiting; in the
default flow, wait briefly for a reaction before finishing. Short decks: just build and run the critic.)

**Presenting, editing, and iterating after delivery — `references/handoff-checklist.md` (same file, later section).** Read it at hand-off on **any deck that carries speaker notes** (Presenter View / `export_notes.py` / how to edit without losing work), and **always** before you re-run the build on the user's feedback — it holds the reconcile-don't-clobber procedure and the required `user-dials:` round-record line.

**Step-6 close — the taste write-back (a named checklist, not prose; full protocol in
`references/user-taste.md`):**
1. **Append ONE look-history line** for the delivered deck to `taste.md` at the registry root
   (`date | deck | preset/look | canvas value | signature motif`, pruned to the 10 most recent) —
   next deck's freshness rule needs a real record to vary against.
2. **Promote a dial into `taste.md` ONLY on the recurrence gate (🔴 MUST):** the user's own words
   mark it standing ("always", "一直", "in general", "for all my decks"), **or** the same
   dimension+direction appears in the round records of **≥2 distinct decks**. One-off or
   purpose-driven corrections stay deck-scoped — a mis-promoted dial silently steers every future
   build. Every promoted row carries its verbatim quote + deck + date *(gate: invalid by schema
   without them)*; conflicting later feedback UPDATES the existing row, never appends a contradiction.
3. **Announce every write in the hand-off FYI line with the easy veto** (above) — a silent write
   didn't happen.
A brand-new user with nothing durable gets no writes and no FYI — create `taste.md` only when the
first durable signal exists.

## Anti-patterns — never do this
A checkable red-flag list; if a draft does any of these, stop and fix it before shipping:
- **Never invent** numbers, results, citations, or figures the source doesn't state (the
  one allowed exception is *flagged* forward-looking content).
- **Never skip the interview**, and **never assume** the topic/content, template, style,
  or — for a brand-new user with no footprint — a domain (ask the subject openly).
- **Never present last year's data as current** on a deck dated this year — ground to today.
- **Never leave a build/meta annotation on a slide** — "（可点击编辑的原生图表）"/"(editable native chart)",
  "(AI-generated)", "(placeholder)", "(draft)", "generated by…", TODO/FIXME. Slide text is the
  audience's content, never a note about how it was made; that goes in code comments or the hand-off.
- **Never let stacked groups blur together** — the gap between groups must beat the gap within a group.
- **Never leave a slide LEFTOVER-empty, and never fake fullness with an oversized block** — fill space
  by **enriching the content** (add the detail/example/figure the point deserves) or enlarging the hero;
  never inflate a card/callout around a single short line of small font to cover a gap (shrink the box
  to hug its text instead). **The word is LEFTOVER, and the distinction is the whole rule**, because two
  pages with identical ink coverage are opposite things:
  **COMPOSED** — one protagonist, vast air around it. A 60pt statement over an empty lower half is the
  oldest move in editorial design; the air is the frame the hero is mounted in. `UNDERFILLED` and
  `DEAD BOTTOM` now stand down on their own when a slide has typographic dominance (its biggest run
  ≥2× its own body tier) AND few objects (≤6) — you no longer have to declare a composition to be
  allowed one. **LEFTOVER** — a grid that ran out of content: flat type, many peers, and a band of
  nothing at the bottom because the last row had nothing to put in it. That is what this rule forbids.
  *(Interior pages keep balanced fullness — the role OCCUPANCY bands stand. Vast whitespace is a
  register for the BOOKENDS and the statement/pivot page, not the default for a content slide; the
  cover/divider band is already ~25–35% ink for exactly that reason.)*
- **Never set content text as large as (or larger than) the slide title** — body/callout/formula/label
  must be visibly smaller than the title; only a deliberate hero numeral/equation may exceed body size,
  and it still stays below the title.
- **Never oversize a formula or leave a variable in plain text** — size every equation to ≈ body text
  (consistent across slides, not blown up to fill the slide width), and set even a lone inline variable
  in math format (italic + real sub/superscript), keeping the LaTeX in the build script so it stays
  reproducible/editable.
- **Never act as your own final critic** — an independent critic must consent; **never ship
  a partially-rendered or contested-blocker deck silently** (surface the disagreement).
- **Never clobber the user's hand-edits** — reconcile before regenerating over their file.
- **Never** ship a wall-of-text slide the user didn't explicitly choose (Q4), a redrawn source figure where a real one exists, a
  cine GIF reduced to one frame, meaning carried by colour alone, or text below ~4.5:1 contrast.
- **Never** put real slide text, labels, numbers, logos, citations, source figures, or
  evidence-bearing charts inside an AI-generated image; generated images are text-free
  visual support unless the user explicitly requested a raster mockup.
- **Never** clip a figure's own parts (legend, colour bar, axis labels/ticks, outer
  row/column) with a crop or a too-large placement, and **never** chop a multi-panel figure
  into context-losing pieces when the whole figure would serve — default to the integral
  figure; **re-view every figure after cropping/placing** to confirm nothing is cut off.
- **Never** leave text in a callout / chip / takeaway bar visibly off-centre (sitting low or
  edge-hugging) — centred boxes need the textbox to span the box's true extent.
- **Never** paste Unicode super/subscripts (ᴴ ᵀ ᵣ); **never** build a "generic conference"
  deck (research the venue); **never** let the deck drift between languages.

## Files

**Changing the SKILL itself? Score it, don't guess.** `scripts/run_eval.py --score <deck-dir>
--eval <id>` checks a produced deck against `evals/evals.json` — machine-decidable assertions
only (pptx exists · hard-lint clean · the `.deck-gates.json` blocks present · the user's numbers
verbatim on a slide · **no figure the prompt never supplied** · notes coverage · and
`reference_reached`, which needs `--transcript` and is the ONLY way to answer *was that reference
actually read during the run*). Deliberately no taste scoring: reference-similarity rewards
imitation and closed-form beauty composites fight this skill's own diversity gates, so both were
examined and rejected. `--record` appends the result under the current `VERSION` so "this
version is better" stops being an impression. 🔴 A **skipped** assertion is not a pass. This
exists because the suites in `tests/` all ask whether the CODE works, and a lossless refactor can
score 2298/2298 while the next live run reads 3 of 10 reference files and ships zero icons —
which has happened, twice.

Full inventory — every script and its flags, the agents, all reference files, the 18 `presets.py` design presets, and the template **Registry** paths — is in `references/file-inventory.md`. Read it whenever you need a capability the *Where things live* table above doesn't already route (an unfamiliar script's arguments, the preset list, which agent or reference owns a concern). Each script's own operating contract is also restated at the step that runs it, so this is a lookup, not a gate.
