# Hand-off & iterating after delivery — don't lose the user's edits

The deck doesn't stop mattering once it's saved. Two things go wrong *after* delivery,
and both are avoidable:
1. The user doesn't realize the deck is fully editable (or is afraid to touch it).
2. The user hand-edits the deck, then asks for one more change — and a naive rebuild
   **overwrites their edits**, because the build script regenerates the file from
   scratch and the two never merged. (This has happened to a real user; it is the most
   damaging post-delivery failure.)

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
  neighbours (normal PowerPoint behaviour).
- **PDF on request.** `render_deck.sh` already leaves a `.pdf` beside the PNGs; offer it
  as a shareable read-only copy.

## Iterating after delivery — the safety rule
🔴 **MUST — before any post-delivery rebuild, determine whether the user has hand-edited the
file since your last build** — ask them, or compare the `.pptx` mtime to when you last wrote
it. This fires in a *later session* where no pipeline gate runs and the reflex path (just
rebuild) is the destructive one — treat it as a hard stop, not a courtesy.

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
The critic's design lens applies the matching check on iteration rounds (**pendulum
overshoot**, `review-rubrics.md` §9) — a fix that swung to the opposite extreme is a
finding, not a fix.

## Why this matters
A deck is a living document the user will rehearse with and keep tweaking. The skill
earns trust by making the deck genuinely theirs to own — editable, reproducible, and
safe to iterate — not a fragile binary that a "quick fix" silently resets. Treat their
manual edits as first-class content, exactly like their source material.
