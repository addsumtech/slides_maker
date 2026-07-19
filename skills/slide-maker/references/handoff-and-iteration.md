# Hand-off & iterating after delivery — don't lose the user's edits

The deck doesn't stop mattering once it's saved. Two things go wrong *after* delivery,
and both are avoidable:
1. The user doesn't realize the deck is fully editable (or is afraid to touch it).
2. The user hand-edits the deck, then asks for one more change — and a naive rebuild
   **overwrites their edits**, because the build script regenerates the file from
   scratch and the two never merged. (This has happened to a real user; it is the most
   damaging post-delivery failure.)

## Table of contents
- Two cheap disciplines worth keeping
- What the deliverable folder contains
- The core model: the script is the source of truth
- What to tell the user at hand-off (step 6)
- Iterating after delivery — the safety rule
- Move the dial, don't flip it — correcting on design feedback
- The taste write-back (step 6 close) — durable dials only
- Why this matters

## Two cheap disciplines worth keeping
- **Versioned critic rounds:** keep each critic-round build as `deck_v<N>.pptx` (+ its renders)
  instead of overwriting in place; when applying round-N fixes, diff the new renders against
  round N-1 for the slides you did NOT touch — a "fix" that regresses a previously-approved slide
  is the loop's classic own-goal, and the diff catches it deterministically.
- **Prewire note (decide-goal decks):** the hand-off note may include one line — "this deck asks
  for a decision: consider walking the key approver(s) through the storyline 1:1 before the
  meeting, so the meeting confirms rather than debates" (the consulting prewire norm; out of
  scope for the builder, high value for the presenter).

## What the deliverable folder contains
The deck + `<deck>.pdf` (parked beside the pptx by `render_deck` — submission/email/print-ready) +
`render/` PNGs + `render/viewer.html` (the flip-through preview), the build script (source of truth), the speaker-notes source,
`assets/` (incl. `sourced/credits.txt` when sourced photos exist),
and the final lint/stats snapshot — a tidy, buildable bundle. The content/design PLANS are **not**
files here: they are presented directly in chat as compact tables at the two checkpoints (that
conversation is the record); write plan `.md` files only if the user explicitly asks.

## The core model: the script is the source of truth
A per-deck build (`build_<deck>.py`) **regenerates** the entire `.pptx` every run. So:
- The **script** is the source of truth; the **`.pptx` is a build artifact**.
- Keep the script in the deck folder next to the `.pptx` (step 3) so it travels with the
  deck and any iteration is reproducible.
- The moment the user hand-edits the `.pptx`, there are **two diverging sources of
  truth** (their edited file, your script) that do not auto-merge. From then on you must
  *reconcile*, never blindly regenerate.

## What to tell the user at hand-off (step 6)
Say it plainly, in one or two lines:
- **It's fully editable.** The `.pptx` is native — real text frames, shapes, and images,
  not a flattened picture. They can edit anything in PowerPoint/Keynote and save; nothing
  is locked or rasterized.
- **Two non-conflicting lanes for changes** (so a rebuild never eats their work):
  1. **Take it from here in PowerPoint.** They keep editing the file themselves; you
     won't re-run the build over it (if they later want *your* help, you work on a copy
     or reconcile first — see below).
  2. **Tell you the changes.** You edit the **build script** and rebuild — reproducible,
     and it survives every future iteration.
- **Caveats worth a sentence:** fonts substitute if the recipient's machine lacks them
  (text may reflow — note any CJK/brand-font dependency from `multilingual.md`); the
  layout is absolutely positioned, so heavily expanding a text box won't auto-reflow its
  neighbours (normal PowerPoint behaviour); and credit portability — CC BY/BY-SA credits live
  on-slide / on the sources page + `credits.txt`, so keep them if the images are reused.
- **PDF included by default.** `render_deck` parks `<deck>.pdf` beside the `.pptx` on every
  render; mention it at hand-off as the shareable read-only copy. On versioned critic rounds this
  also produces `deck_v<N>.pdf` per round — **delete the stale round PDFs before hand-off** so the
  bundle ships only the final `<deck>.pdf` (same tidy-bundle rule as the round pptx files).

## Iterating after delivery — the safety rule
🔴 **MUST — before any post-delivery rebuild, determine whether the user has hand-edited the
file since your last build** — ask them, or compare the `.pptx` mtime to when you last wrote
it. This fires in a *later session* where no pipeline gate runs and the reflex path (just
rebuild) is the destructive one — treat it as a hard stop, not a courtesy. **Gate artifact
(required, per the enforcement invariant):** record one literal line in the round's response
BEFORE rebuilding — `hand-edit check: asked|mtime-compared — clean|reconciled` — a post-delivery
rebuild with no such line means the check didn't run. (The Step-6 note spec in SKILL.md is the one
authoritative hand-off checklist — conditional items like the `provenance:` line, click order, and
image credits live there; this file adds the iterate-safely mechanics only.)

- **They have NOT hand-edited** → safe path: edit the **build script**, rebuild, re-render,
  re-run the critic. This is the normal iteration loop.
- **They HAVE hand-edited** → **do not regenerate over their file.** Reconcile instead:
  - *Preferred:* recover their changes with `python3 scripts/extract_deck.py
    <their_deck.pptx>` (pulls their current text/tables/figures), fold those edits back
    into the build script so the script matches reality, *then* make the new change and
    rebuild. Now the script is the source of truth again.
  - *Or, for a small tweak:* open **their** edited file and make the change in place
    (python-pptx or by hand), leaving the rest untouched — and don't run the generator.
  - Either way, **confirm which version is canonical before overwriting anything you
    didn't just create** (the general "look before you clobber" rule). If you keep a
    rebuild aside, name it clearly (e.g. `_rebuilt_backup.pptx`) rather than replacing
    their file.
- **Re-verify the right file.** If they hand-edited, render *their* file
  (`render_deck.sh their_deck.pptx`) to re-check layout — not a fresh build.

## Move the dial, don't flip it — correcting on design feedback
Design feedback names a **dimension**, not a pole — treat it as "move this dial a step,"
never "jump to the opposite extreme." Overshooting trades one complaint for its mirror
image and costs another full round: *muted → rainbow chrome on every slide* is as wrong
as the muted deck was; *dense → stripped bare* and *static → everything animated* are the
same failure on other dials. So when the user critiques a dimension:
1. **Locate WHERE it actually failed** — almost always the *content layer*, not the
   scaffolding. "More colour / more contrast" means colour on the elements that carry
   meaning (data, diagram nodes, icons, hero numbers); it is **not** a licence to paint
   the chrome (title furniture, spines, rules, footers stay quiet — the chrome budget in
   `agents/slide-design.md` §1).
2. **Move that one dial a deliberate step** and re-render; if the user says "further,"
   take another step — two cheap rounds beat one overshoot.
3. **Hold every dimension they did NOT criticise stable**, so they can judge the fix in
   isolation rather than re-reviewing the whole design.
4. **Record WHY the round happened** — the round record gains one **`user-dials:`** line per
   criticised dimension: `dimension → direction, layer — "verbatim user words"` (e.g.
   `colour: +vivid, content layer — "太素了"`). Zero cost when no iteration happens — and it is
   the observation stream the Step-6 taste write-back promotes from (below), so a preference
   the user voiced twice never has to be re-taught at the cost of a render-review round.
The critic's design lens applies the matching check on **any round after the first —
critic-fix rounds exactly like user-feedback rounds** (**pendulum
overshoot**, `review-rubrics.md` §9) — a fix that swung to the opposite extreme is a
finding, not a fix, whoever named the dial; when a `user-dials:` line exists for the round,
cite it as the check's evidence — the user's own words fix which dial moved and how far.

## The taste write-back (step 6 close) — durable dials only
The `user-dials:` ledger above is the per-deck observation stream; **`taste.md` at the
registry root** (`~/.claude/slide-templates/` · `~/.codex/slide-templates/`) is the durable
store; the **Step-6 close is the only bridge** — full schema + protocol in
`references/user-taste.md`. Three named actions (the Step-6 close checklist in SKILL.md is
the gate — a write not on it didn't happen):
1. **Append ONE look-history line** for the delivered deck (`date | deck | preset/look |
   canvas value | signature motif`, pruned to the 10 most recent) — next deck's freshness
   rule varies against it.
2. **Promote a dial ONLY on the recurrence gate (🔴 MUST):** the user's own words mark it
   standing ("always", "一直", "in general", "for all my decks"), or the same
   dimension+direction appears in the round records of **≥2 distinct decks** — once is a
   deck-scoped correction, twice is a preference. Every DIALS row carries its verbatim quote
   + deck + date (an unevidenced dial is an invention); later conflicting feedback **UPDATES
   the row — move the dial** — never appends a contradiction (two rows arguing about one
   dimension is exactly the diverging-sources-of-truth failure this file exists to prevent).
3. **Say it, don't hide it** — every write gets one hand-off FYI line (*"recorded to your
   taste profile: <X> — say the word and I'll drop it"*); the file is the user's own, so the
   veto is one edit.
A brand-new user (no `taste.md`) gets no writes until the first durable signal — never
manufacture a profile. The **save-this-look offer** (persist a freshly-designed look to the
registry, Notes distilled from the final critic `strengths`) rides the same hand-off note —
opt-in on an explicit yes only; see `references/user-taste.md` §"Consented-look mining".

## Why this matters
A deck is a living document the user will rehearse with and keep tweaking. The skill
earns trust by making the deck genuinely theirs to own — editable, reproducible, and
safe to iterate — not a fragile binary that a "quick fix" silently resets. Treat their
manual edits as first-class content, exactly like their source material.
