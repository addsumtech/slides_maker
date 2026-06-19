# Redesigning a deck the user already made — diagnose first, then rebuild to scope

This is the path for *"here are my slides, they're not good enough — make them better."*
It differs from building from scratch in one crucial way: **the user has already made
decisions** (their content, their structure, often their branding), and they're emotionally
and practically invested in some of them. Your job is to improve the deck *as theirs*, not to
silently replace it with a different deck that happens to cover the same topic. So you **lead
with a diagnosis** and **agree on how much to change** before rebuilding anything.

Read this when the user hands you an existing `.pptx`/Keynote/PDF to improve, redesign, clean
up, or "tell me what's weak." The critic, rubrics, `deckkit`, and render loop are all the same
as the build path — this just adds the front end.

## Step R0 — Two extra interview answers (ask alongside the usual four)
Beyond purpose/audience/source/style, a redesign hinges on two questions the build path
doesn't ask. Fold them into the same interview turn, using the host's natural UI:
structured choices when available, or one compact direct question in plain Codex chat.

- **Keep the design, or redesign the look too?** Their deck may carry branding (a template,
  a colour scheme, a logo) they must keep, or it may be a blank-PowerPoint look they'd happily
  replace. *Keep* → treat their deck as the template (`deckkit.open_template` preserves its
  masters/layouts/brand; pull its palette) and improve *within* it. *Redesign* → you may
  re-theme freely.
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
2. **Extract their content** — `python3 scripts/extract_deck.py their_deck.pptx <dir>` → a
   `content.md` (per-slide text + tables + image filenames) and every embedded figure saved
   whole to `assets/`. This is what you carry forward; reuse their figures, don't redraw them.
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
- **Carry their numbers and emphasis faithfully.** A redesign that "improves" a slide into saying
  something the source doesn't is a fidelity failure (see the critic's fidelity check) — the most
  damaging thing you can do to someone's own deck.

## Step R3 — Verify, loop, and show the before/after
Run the build → render → actor-critic loop as usual until consent. When you present, **show the
before/after** for the slides you changed and name what each fix addressed (from the R1
diagnosis) — the user should *see* the deck become more clearly theirs, not just "different".
