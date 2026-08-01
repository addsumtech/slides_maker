# Redesigning a deck the user already made — diagnose first, then rebuild to scope

This is the path for *"here are my slides, they're not good enough — make them better."*
It differs from building from scratch in one crucial way: **the user has already made
decisions** (their content, their structure, often their branding), and they're emotionally
and practically invested in some of them. Your job is to improve the deck *as theirs*, not to
silently replace it with a different deck that happens to cover the same topic. So you **lead
with a diagnosis** and **agree on how much to change** before rebuilding anything.

Read this when the user hands you an existing `.pptx`/Keynote/PDF to improve, redesign, clean
up, or "tell me what's weak" — for a pure critique (no rebuild requested), skip R0 and run only
R1 steps 1–3 (render → extract → critic), deliver the diagnosis, and OFFER the rebuild; the
interview + R0 fire only when they take it. The critic, rubrics, `deckkit`, and render loop are
all the same as the build path — this just adds the front end.

## Table of contents
- Step R0 — Redesign interview: R0 REPLACES the template question (ask alongside purpose/audience/source/style)
- Step R1 — Diagnose THEIR deck first (don't rebuild blind)
- Step R2 — Rebuild to scope (selective, not scorched-earth)
- Step R3 — Verify, loop, and show the before/after
- Gate mapping on the light-cleanup / surgical fix-pass path

## Step R0 — Redesign interview: R0 REPLACES the template question (ask alongside purpose/audience/source/style)
On the redesign path the keep/redesign answer IS the template decision — do not ask Q1's
four-option template question up front. Beyond purpose/audience/source/style, a redesign
hinges on two questions the build path doesn't ask. Fold them into the same interview turn,
using the host's natural UI: structured choices when available, or one compact direct
question in plain Codex chat.

- **Keep the design, or redesign the look too?** Their deck may carry branding (a template,
  a colour scheme, a logo) they must keep, or it may be a blank-PowerPoint look they'd happily
  replace. *Keep* → their deck IS the template (`deckkit.open_template` preserves its
  masters/layouts/brand; pull its palette) and improve *within* it; this counts as a *provided*
  template, so per SKILL.md's gate carve do NOT offer the direction gate. *Redesign the look*
  → NOW ask Q1's four standard choices as the follow-up (registered / they provide one / design
  a clean one / generate with an image tool): "design a clean one" opens the direction gate per
  Q1's design-one branch; "generate with an image tool" runs `references/generated-template.md`
  and skips the gate.
- **How deep a change?** This governs everything downstream:
  - *Light cleanup* — keep their structure and slide order; fix the worst offenders (text
    walls, illegible figures, overflow, weak titles). The user is attached to the deck's shape.
  - *Full re-author* — keep the *content and figures*, but you're free to re-cut the narrative,
    merge/split slides, and reorder. The default when they say "it's just not good."
  When unsure, ask — getting this wrong means either a timid cleanup that leaves it weak, or a
  ground-up rewrite that throws away structure they wanted.

## Step R1 — Diagnose THEIR deck first (don't rebuild blind)
The natural first move when optimizing is to find out what's actually wrong — and to align
with the user on it before spending effort. So:

1. **Render their deck** — `bash scripts/render_deck.sh their_deck.pptx` → one PNG per slide.
2. **Extract their content** — `python3 scripts/extract_deck.py their_deck.pptx <dir>` (accepts
   `.potx`) → a `content.md` carrying, per slide, the text, the tables, **every native chart's real
   CATEGORIES AND SERIES** (rebuild those with `native_chart` — never re-read the numbers off the
   picture) and **the speaker notes** (their planned narration — carry it into the rebuild's notes,
   don't re-draft it), plus every embedded figure saved whole to `assets/`. This is what you carry
   forward; reuse their figures, don't redraw them. **Read the `⚠ UNEXTRACTED` lines if there are
   any** — a shape the script could not read is listed with its type rather than dropped, so a lossy
   extraction says so instead of looking complete.
3. **Critique the current deck** — run the **same critic** (`agents/critic.md`) on the rendered
   PNGs against the deck's purpose + audience (and the source material, if they gave any). This
   produces a concrete, per-slide weakness list — the diagnosis.
4. **Show the user the diagnosis and confirm scope.** Lead with the 3–5 biggest levers ("slides
   4–6 are walls of text"; "the results figure is illegible from the back"; "no single take-home
   message"), in plain language, and confirm the plan: which slides to keep, which to rebuild,
   and the depth/branding answers from R0. This is cheap, builds trust, and prevents a big
   rebuild in the wrong direction. *Then* build.

## Step R2 — Rebuild to scope (selective, not scorched-earth)
- **Honor "light cleanup".** If they asked to keep structure, **keep the slides that already
  work** and rebuild only the weak ones. Don't reorder or drop slides they're keeping. Note that
  `deckkit.open_template()` wipes *all* slides — so for a selective cleanup, either re-add the
  good slides faithfully (their content from `content.md`, their figures from `assets/`), or
  copy the source file and edit in place rather than rebuilding from blank.
- **For a full re-author,** apply the normal build path (plan → deckkit → render → critic loop),
  but seed it with *their* real content and figures from the extraction — the point of a redesign
  is that the facts and figures are theirs; only the *presentation* changes.
- **Which geometry net runs depends on the path.** A *re-author* has a deckkit build script, so end it
  with the build-time `dk.lint_layout(prs)` gate (Step 4) before `prs.save()`. A *copy-in-place edit* has
  no build script — there's nothing to call `lint_layout` from — so it relies on the **render-time**
  `scripts/lint_deck.py` (Step 5) after rendering. Either way the deck reaches the critic geometry-clean.
- **Carry their numbers and emphasis faithfully.** A redesign that "improves" a slide into saying
  something the source doesn't is a fidelity failure (see the critic's fidelity check) — the most
  damaging thing you can do to someone's own deck.

### The SURGICAL FIX-PASS protocol (copy-in-place edits on a foreign deck)
A "fix pass keeping the look" runs python-pptx edits against shapes you didn't build and can't
rebuild. Every rule below exists because its violation shipped compounding errors on a real pass:

1. **One consolidated script, run from the ORIGINAL, every time.** Never iterate mutations on an
   already-mutated copy — each round's mis-fix becomes the next round's ground truth, and by round
   four you're repairing your own repairs. Fold each round's learnings back into ONE script that
   regenerates `-fixed` from the untouched source; the script is idempotent and the original is
   never written to.
2. **Target shapes by the lint report's COORDINATES, never by container heuristics.** "The card
   behind this text" matchers silently grow the wrong shape (a scrim, a divider, an outer panel)
   and report success. Match on the flagged bottom/size (`abs(bottom − flagged) < 0.06in`) plus a
   horizontal-overlap check with the flagged text — and re-lint after every batch to prove the
   flagged item actually moved.
3. **Grow into MEASURED space only.** Before extending or moving any shape, know the reserved
   bands (footer band = content above ~0.91 × slide-height; on a 10×5.625in canvas ≈ 5.10in) and
   what sits below/beside the shape. Growth that clears a TEXT PADDING flag by invading the footer
   band trades one finding for another — when the band leaves no room, fix the TEXT instead:
   shrink its size a step, trim it (parking the full sentence in the speaker notes), or raise the
   whole row.
4. **Colour remaps are CANVAS-AWARE.** Foreign decks reuse one hex on light and dark canvases; a
   global "darken #B9863A" fixes the cream slides and breaks the dark ones. Remap exact values
   per slide, keyed by that slide's canvas value — keep an explicit dark-slide exclusion list.
5. **Decorative backing shapes are IMMUNE.** Photo frames, soft-shadow plates, seal insets, and
   scrims overlap their content BY DESIGN — "fixing" those overlaps mangles the composition.
   Only separate ink-on-ink collisions; leave shape-on-shape layering that renders correctly.
6. **The lint measures INK, not boxes.** Clamping a textbox's height doesn't move its ink — an
   ink collision is fixed by separating the elements (nudge apart) or shrinking/trimming the
   text, never by resizing the container around it.
7. **Content removed is content PARKED.** Any trim lands verbatim in that slide's speaker notes
   (add a full spoken thread while you're there — a foreign deck with empty notes isn't
   presentable), so the fix pass never silently deletes the author's material.

## Step R3 — Verify, loop, and show the before/after
Run the build → render → actor-critic loop as usual until consent. When you present, **show the
before/after** for the slides you changed and name what each fix addressed (from the R1
diagnosis) — the user should *see* the deck become more clearly theirs, not just "different".

## Gate mapping on the light-cleanup / surgical fix-pass path
The copy-in-place path has no Content plan, no Design plan, and no build script — so the pipeline
gates that reference those artifacts map as follows (this carve is the rule; "PRE-FLIGHT, every
deck" is satisfied THROUGH it, not skipped): the **R1 diagnosis + confirmed scope** stand in for
the Step-1/2 plans — PRE-FLIGHT items that diff against plan artifacts (Spoken-thread notes,
design-plan row vs docstring, motion manifest) are checked against the diagnosis + the fix ledger
instead, and items with no analogue on an untouched slide are ticked `n/a — light-cleanup path
(diagnosis is the plan)`. The **build-time geometry gate still runs in full** (`lint_layout(prs,
strict=True)` on the edited file before save), as do render → `lint_deck.py` → the critic loop on
the touched slides + a whole-deck coherence look. Nothing about this path relaxes hard floors —
it only renames where the plan-shaped evidence lives.
