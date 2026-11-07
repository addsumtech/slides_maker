# Auto-delegation quality gates

## Purpose

When the user delegates decisions with "decide everything yourself" / "auto mode" / similar
directives, the skill MUST maintain the same quality bar and process rigor as user-supervised
mode. **Delegation is not permission to skip steps or lower standards** — it is permission to
make defensible choices yourself rather than asking.

## Core principle: Auto means "you choose", not "skip"

**Every workflow step still runs.** The checkpoints are still posted, the agents still produce
their artifacts, an independent critic still reviews. What changes:

- ✅ You answer the Step-0 interview questions yourself (with derived, defensible picks).
- ✅ You design the visual language yourself (within the design-intelligence targets).
- ✅ You build without waiting for explicit "proceed" — but only AFTER posting each checkpoint
  for async veto (user can interrupt if they see it and disagree).
- ❌ You do NOT skip the content plan agent.
- ❌ You do NOT skip the design plan agent.
- ❌ You do NOT skip rendering or the critic review (auto runs the `fast` tier — one sole critic
  carrying both lenses — and may escalate, never decline; see "Review tier in auto mode").
- ❌ You do NOT compress multiple steps into one pass.

## Checkpoint protocol under auto delegation

1. **Post each checkpoint artifact as specified** in `checkpoint-convention.md`:
   - Content checkpoint: full content plan with source-trace table, 角色/记忆句, digest
   - Design checkpoint: visual language, form ledger, signature move, rhythm map, all gates
   
2. **Give the user a brief moment to interrupt** (one conversational beat):
   ```
   [Post checkpoint artifact]
   
   Content plan ready. Proceeding to design phase in auto mode — interrupt if you want 
   to adjust the scope or angle.
   
   [Brief pause, then continue if no interrupt]
   ```

3. **If interrupted, stop and address the feedback.** Then resume from that checkpoint.

4. **Never write "I'll skip X because you said auto"** — that reasoning is invalid. Auto
   delegation covers *preferences*, not *process steps*.

## Quality enforcement in auto mode

### Review tier in auto mode

🔴 **Auto runs the post-build default, `fast` — and may never pick `none`.** The review question
is asked at Step 5 with the deck visible; under auto it is posted as an FYI, not a stop
(`review: fast (post-build default — auto)`). Declining review entirely is a decision only the
user can make, with the deck in front of them. Auto may ESCALATE above `fast` for a high-stakes
purpose (defense / exec readout / pitch) and must record the reason:
`review: thorough (escalated — defense deck, auto)`. The surviving-blocker rule still applies at
`fast`: a blocker the single round cannot absorb goes back to the USER named, never shipped.

### Design targets (must meet)

Even when you design the visual language yourself, you MUST hit the targets in
`design-intelligence-addendum.md`:
- ✅ 2-3 title treatments rotated (not the same chrome on every slide)
- ✅ Signature move appears 2-4 times (establishes visual identity)
- ✅ Rhythm variation (not all slides the same form)
- ✅ Color discipline (accent used deliberately, not everywhere)

### Image generation: topic relevance + text legibility

When generating images for slides, enforce BOTH:

1. **Strong topic relevance** (images must advance understanding, not just "look nice")
2. **Text legibility protection** (images used as backgrounds MUST NOT interfere with reading)

#### Image placement rules for auto mode

**A. Hero/atmosphere plates (full-bleed backgrounds):**

Use **`dk.scrim_overlay`** — the helper written for exactly this job. It emits a GRADIENT
fill, which is the only way a scrim can carry transparency: `<a:alpha>` lives on gradient
stops, and DrawingML's alpha scale is **0–100000**, not 0–255.

```python
# 1. Place the plate
dk.picture(slide, img_path, 0, 0, 10, 5.625, fit="cover", alt="<what it shows>")

# 2. Graduated scrim, AIMED at the text (angle 0 = darker at left, 90 = darker at bottom).
#    Size it to the text's zone — a flat slab over the whole slide flattens the image.
dk.scrim_overlay(slide, 0, 0, 10, 5.625,
                 stops=((0.0, 0.82), (0.55, 0.55), (1.0, 0.12)),
                 color="0A1420", angle=0.0)

# 3. Text on top
```

🔴 **Never write `shape.fill.fore_color.alpha = ...`.** python-pptx's `ColorFormat` has no
`alpha` setter and no `__slots__`, so the assignment **silently creates a dead attribute** and
raises nothing. The emitted XML is `<a:srgbClr val="000000"/>` with **no `<a:alpha>`** — a 100%
**opaque** rectangle that erases the plate entirely. Measured on a real deck: brightest pixel in
the image region **0/765**, and **every lint passed green** — text is painted last so
`TEXT NOT VISIBLE`/`OCCLUSION` cannot fire, and white-on-pure-black scores ~21:1 so
`TEXT-ON-IMAGE CONTRAST` reports the *best* number in the deck. A solid fill cannot be
translucent; reach for the gradient helper, or `deckkit.pic_alpha` to fade the picture itself.

**Text over a plate must be legible — but a scrim is only one way to get there, and not always
the right one.** When the plate already carries a calm dark region where the type sits, a scrim
subtracts from the image and adds nothing. Measure first with `image_fx.quiet_region(path)`,
then decide. `TEXT-ON-IMAGE CONTRAST` backstops the too-light direction; **nothing backstops the
too-heavy direction**, so that judgement is yours and it is the one that quietly ruins covers.

**B. Side panels / content plates (images as visual support, not backgrounds):**

These are placed BESIDE text, not under it:
```python
# Image in right 40% of slide
dk.picture(slide, img_path, 6.0, 1.0, 3.5, 3.5, fit="contain", alt="Topic illustration")

# Text in left 60%, no overlap
dk.text(slide, 0.8, 1.5, 5.0, 3.5, content)
```

No scrim needed — text has its own opaque background (the slide fill).

**C. Icon/diagram supplements:**

Small, non-decorative images that clarify content:
```python
# Icon tile with background — the param is `fill=`, not `tile_color=`.
# icon_tile reads the icon's own ink and auto-nudges the tile to >=3:1, so prefer it
# over hand-placing an icon on a raw box.
dk.icon_tile(slide, x, y, size, icon_path, fill=accent, glyph="white")

# Or inline diagram
dk.picture(slide, diagram_path, x, y, w, h, fit="contain", alt="Architecture diagram")
```

#### Image generation prompt discipline

When you decide an image would help, the prompt MUST:

1. **Describe the topic concept** (not just "abstract background"):
   ❌ "Abstract technology background with blue gradient"
   ✅ "Neural network architecture diagram showing interconnected layers, technical 
       schematic style, clean lines"

2. **Specify composition for text legibility** when used as background:
   - "with large empty calm region in [position] for text overlay"
   - "dark/light uniform background gradient"
   - "vignette darkening at edges, bright center"
   
3. **Declare the art direction** (match the deck's visual language):
   - If deck is "clean geometric" → "minimal geometric shapes, no texture"
   - If deck is "research technical" → "schematic, blueprint style, no decoration"
   - If deck is "warm human-centered" → "soft illustrations, approachable"

4. **Exclude text/labels in the image** (always):
   - Add to every prompt: "no text, no labels, no annotations"
   - Text belongs in native PowerPoint objects (editable, searchable, accessible)

#### When NOT to generate images (auto mode discipline)

Even in auto mode, do NOT generate images just because you can. Generate only when:

✅ The image would **clarify a concept** that's hard to describe in words alone
✅ The deck's purpose/audience expects visual richness (conference > internal meeting)
✅ You can describe a prompt that's **topic-specific** (not generic stock vibes)

❌ Do NOT generate for:
- Every slide "to make it look better" (visual clutter)
- Generic "technology/business" atmosphere (vague, low information)
- Covering up sparse content (fix the content instead)

**Default to clean, typography-focused slides** — generated images are an enhancement, not
a requirement.

## Build discipline: use the component library

In auto mode you're more likely to rush the build. **Resist the temptation to hard-code
simple boxes when a component exists:**

❌ **Don't:**
```python
dk.box(slide, x, y, w, h, fill=color)
dk.text(slide, x+0.2, y+0.2, w-0.4, h-0.4, content)
```

✅ **Do** — reach for a component that actually exists:
```python
dk.icon_card(slide, x, y, w, h, icon_png, title, body, accent=color)   # icon + title + body
dk.callout(slide, x, y, w, h, label, body)                             # labelled block, auto-grows
dk.spec_card(slide, x, y, w, h, rows, title="...")                     # key/value rows
```
Pre-tested padding, contrast and sizing. **Check the signature in `scripts/deckkit.py` before
you call it** — an invented helper or a guessed keyword fails at build time, and a guessed
*value* (wrong units, wrong scale) fails silently, which is worse.

The catalogue is the component list **inline in `SKILL.md`** plus
`references/design-gallery.md`. There is no `deckkit-component-guide.md`.

## Critic review: required in auto mode

🔴 **Running the critic review is NOT OPTIONAL in auto mode — at the tier the section above sets.**
It is the only independent verification that your auto-decisions produced a good deck. Auto runs
the post-build default, `fast`: ONE sole critic carrying BOTH lenses, one round
(`references/critic-panel.md`, SKILL.md Step 5). Escalating to `standard`/`thorough` for a
high-stakes deck dispatches the lens panel instead; `none` is never an auto pick. *(This section
once demanded the FULL panel in auto mode — written 2026-07-28, before the review question moved
to after the render and made `fast` the default, 2026-08-16. The tier rule above is the current one.)*

After build + render + lint, dispatch per `references/critic-panel.md` — critics are LENS-based,
pointed at `agents/critic.md`; there is no `role=content-critic` parameter:
1. **`fast` (the auto default):** one sole critic, both lenses as two passes —
   `python3 scripts/dispatch_brief.py prompt --brief <path> --role critic --lens AB --round 1 --deck <dir>`
   — given the render PNGs + `lint_deck --json`
2. **Escalated (`standard` / `thorough`):** one critic per lens — `--lens A` (content) and
   `--lens B` (design) — plus whatever that tier adds in `critic-panel.md`
3. Validate each returned review: `python3 scripts/validate_review.py critic <review.json>`
   — a review failing schema/coverage is **rejected and re-dispatched once**, never acted on
4. Record it as evidence, not as a claim:
   `python3 scripts/validate_review.py critic <review.json> --record <deck-dir>`
5. **If any critic reports blocker/major issues, fix them** — don't hand off a deck with known
   problems just because the user said "auto"

🔴 **If the host cannot dispatch subagents, say what was lost.** Running the lenses inline is
the author grading themselves — record `critic: inline (no dispatch on this host — not
independent)` rather than reporting a pass. See the capability ledger in
`references/interview-protocol.md`.

The user delegated *choices*, not *quality*. A deck with contrast violations, text walls,
or incoherent rhythm fails regardless of who made those mistakes.

## Summary checklist for auto mode

Before claiming "deck complete" in auto mode, verify:

- ✅ Posted content checkpoint (even if user didn't comment)
- ✅ Posted design checkpoint (even if user didn't comment)  
- ✅ Content plan has source-trace table and digest
- ✅ Design plan has form ledger, rhythm map, signature move, all gates
- ✅ Build script uses deckkit components (not hard-coded boxes)
- ✅ Generated images (if any) have topic-relevant prompts
- ✅ All text-over-image has adequate scrim (contrast ≥ 3:1)
- ✅ Deck rendered to PNG
- ✅ Lint ran (hard errors = 0)
- ✅ Both lenses reviewed (one sole `fast` critic, or one critic per lens when escalated) and
  issues addressed
- ✅ Review tier recorded: `fast (post-build default — auto)`, or the escalation with its reason —
  never `none`

If any checkbox is unchecked, the deck is not ready. "Auto mode" is not a waiver for
incomplete work.


## The per-deck AUTO WAIVER — full text

**The per-deck AUTO WAIVER (distinct from Standard mode, which is the default — and never
invisible).** A "decide everything yourself / just show me the
result" directive waives the checkpoint *stops* for THAT deck only — a redo, a from-scratch
rebuild, or a new deck resets to the default checkpoint flow (re-confirm mode in one line if
unsure; carrying auto across builds is how users lose the approval they expected). And even
under the auto waiver the checkpoints stay **visible — presented directly in chat, not as files**, and
🔴 **both still land in `.deck-gates.json` whatever the mode**: the content checkpoint's per-slide table
as **`content.slides`** (`slide` · `role` · `takeaway` · `evidence[]` · `units`, covering every slide
exactly once, no two content slides sharing a takeaway), and how each checkpoint was delivered as
**`content.checkpoint`** / **`design_plan.checkpoint`** (`{"mode": "approved"|"auto", "record": …}`).
Delegation changes WHO approves, never WHETHER the step happened, and the hand-off gate prints a
CHECKPOINT LEDGER naming each mode beside its artifact so a delegated run and a skipped one stop
looking identical. Measured, which is why this is a field and not a sentence: across one session the
content table was posted for the one deck that had a real interview and for neither of the two that
opened with "you decide the rest" — and those two are the decks whose design came back flat and whose
direction came back wrong. `content.slides` is not a new field either: `codex_delivery_gate.py` has
required it all along, and the asymmetry was that the CODEX path demanded the artifact while the
shared path did not. Under a genuine exception, waive it in writing (`content.slides_waived`). Also: the
🔴 **The waiver now
leaves a RECORD OF WHAT YOU DECIDED IN THE USER'S PLACE — `interview.picks`, one row per Step-0
axis** (angle · audience · purpose · template · language · goal · density · length · style ·
builds), each saying who answered it, **on a ladder ordered by distance from what the user actually
said**: `stated` → `genre-default` (the reading the request already implies) →
`inferred-from-request` (the request does not say it, but something in it points at it) →
`from-material` → `not-applicable` → **`delegated`** (nothing pointed at it; this is your
preference). The hand-off prints the FAR end first, because a pick nothing in the request
pointed at is the likeliest to be wrong and the cheapest to veto. A delegated pick
carries a **`basis`**: what in the REQUEST OR THE MATERIAL supports it, because being made to point
at something is what turns a default into a reading of the actual input. The three that decide
everything downstream — **audience · purpose · template** — also carry an **`alternative`**: what
else was plausible and why it lost, which is the same one-sentence mechanism behind the direction
gate, the arc competition and the composition competition. 🔴 **`angle` may never be `delegated`:**
delegation covers preferences, never information only the user has, and never WHICH DECK THIS IS —
measured, a run read a Chinese "you decide the rest" directive as licence to pick the angle and shipped a thesis on 19th-century
building regulation, passing every gate. Enforced by `scripts/delegated_picks.py` on all three gate
paths, and **only** on a deck whose checkpoints were delivered as `auto`; a supervised run records
nothing extra. **Record each row with `python3 scripts/deck_gates.py picks <deck> --set AXIS=VALUE
--source … [--basis …] [--alternative …]`** — validated before it is written; `deck_gates.py merge <deck>
<fragment.json>` takes a plan's gate block — never hand-edited JSON. Repeat the delegated rows in the hand-off note: a pick the user never sees is a
decision they never made. Also: the
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
