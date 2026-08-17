# Checkpoint convention

## The checkpoint artifact spec (CONTENT + DESIGN) and the auto-delegated Step-0 picks

**The waiver extends to the Step-0 interview — by DELEGATION, with a hard floor.** Under a full
"decide everything yourself" directive you don't fire the four-question form; you ANSWER the
questions yourself with defensible, purpose-derived picks (template → design a clean one shaped
to the purpose, unless the request itself points elsewhere — an attached template, or explicit
vivid/branded language that earns the image-tool branch; delivery/goal/density → derived from
the stated purpose; **appear-builds → derived from delivery** (presented → builds ON, the
recommended default; self-read → static); language → the user's own), and post the picks as the FIRST FYI — one
compact block, one line per question — before any planning, so a wrong pick costs one glance to
veto, not a build. The FLOOR: delegation covers *preferences*, never *information only the user
has*, and never **which deck this is**. 🔴 A common genre carries a DEFAULT the request already
implies — 「介绍巴黎的 PPT」 means the city introduction people actually give: places, districts,
food, what to see. Take that reading unless the user signalled otherwise. Measured: a run read
「你自行决定」 as licence to pick the ANGLE too, and delivered a thesis about 19th-century building
regulation — every gate passed, and it answered a question nobody asked. Deciding the angle is
not a preference pick; it is deciding what the deck IS, which is the one thing the ask already
did. An unusual angle is a proposal: name it in one line in the first FYI so it costs one glance
to veto — a missing TOPIC or unlocatable source material is still asked (that one question, not the
form), same class as the save-location stop. Preference questions the request already answers
are simply recorded, not re-picked.
**Delegated picks are DERIVED, not defaulted — the waiver removes the asking, never the
understanding.** Before picking, actually look at what they gave: scan provided material for its
genre, register, density, and audience clues (a clinical paper, a pitch doc, and a course note
want different answers to every question); read a terse few-sentence ask for its real intent.
For a returning user, also read `taste.md` at the registry root (`references/user-taste.md`) and
let its DIALS/NO-GOs seed the picks — evidenced past preference is exactly what deriving wants —
naming the applied dials in the first-FYI pick block so a stale dial costs one glance to veto
(no `taste.md` = nothing to seed; the request and material still outrank any dial).
Then choose the way the sharpest person in the room would choose *for THIS deck* — the TASTE
PROTOCOL applies to the picks themselves, and "a defensible default" that ignores what the
material obviously wants is not defensible. Downstream, nothing relaxes: Step 1's deep-read /
comprehension-brief bar, the no-source web-verification, the **full design intelligence** (a
topical cover visual, harmonised + value-varied backgrounds, the design musts, the semantic-colour
ledger — deciding with limited info is never a licence for a barren default-blue type deck), and
the full critic loop all run at the
same standard as an interviewed deck. And if the deep read later contradicts an initial pick
(the material turns out self-read-shaped, denser, or more formal than the first scan suggested),
REVISE the pick and say so in the next FYI — riding a wrong guess to delivery is the one failure
delegation must never produce. Content checkpoint = the deck
memory sentence + a 2-line brief/ledger DIGEST (the comprehension brief's one-sentence message +
a claim-ledger tally, e.g. `ledger: 14 claims · 14 verified · 0 open` — full brief + ledger stay
in the plan, posted on request or on any digest anomaly) + emotional-curve line + pace check +
**(long source only) a 1-line Source-coverage DIGEST** (`source: 320 pp · built-around 4 ch ·
summarised 3 · cut 5` + the chosen slice — full per-chapter map in the plan) + **(video source only)
the transcript-status line** (supplied locator, or "visual-only — spoken content is a GAP") + ONE table (`# | 角色 | 记忆句(takeaway) |
承载证据 | units` — **headers follow the conversation language**: on an English-conversation deck use
`# | role | takeaway | carrying evidence | units`; the column MEANINGS are fixed, the header language
is not) — the `units` column is the count of content units the row carries (the
distribution pass's output): a `1` on a standalone content slide or a `6+` on a spoken beat is
visible at a glance, so an about-to-be-empty or about-to-be-dense page gets caught at the
checkpoint, not at the render. The table's takeaway column, read top to bottom, IS the Takeaway spine: append only
the plan's one-line spine verdict, never the spine paragraph (new plan fields like the money
slide / Spoken thread live in the FULL plan; at most a one-line marker appears here).
**+ one required GATE line naming the arc-choice that was made — `arc gate:`.** Shape:
`arc gate: picked <name> (<shape>) of N · lost: <name> — <one clause> · <name> — <one clause> · divergence: <ok | flagged <pair> → rediverged | justified: <reason>>`.
🔴 **The table and this line also LAND IN `.deck-gates.json`** — the table as `content.slides`
(`slide` · `role` · `takeaway` · `evidence[]` · `units`), the competition as
`content.arc.candidates` + `chosen` + `rejected`. The hand-off gate re-scores the candidates with
`arc_divergence.check()` and checks the table covers every slide exactly once with no two content
slides sharing a takeaway. Posting the table in chat is still required and is still not checkable;
this is the half that is. **A content checkpoint with no `arc gate:` line is NOT READY**, exactly as a branch-(c)/(d) design
checkpoint with no `direction gate:` line is not ready — and for the identical reason, which the
design side learned the expensive way: a choose-from-alternatives step with no line to record it
silently becomes a derivation, and an Auto pick leaves NO trace that alternatives ever existed.
The losers and their reasons are the whole artifact; `picked contribution-first` on its own is a
claim the coordinator can write without any competition having happened. Under the AUTO WAIVER the
line still appears — the waiver removes the stop, never the record — and the coordinator picks,
so this is an FYI in every mode rather than a new user stop (`agents/content-planner.md` §3).
**The 承载证据
column carries a concrete SOURCE TRACE, not a vague label** — a locator ("Fig 3 / p.4 ¶2", a table
cell, a short verbatim span) — so a watching auto-mode user can catch a per-slide grounding mismatch
even though the checkpoint is an FYI, not a stop (this is the cheapest fidelity catch on the path
delegation uses most; the comprehension gate still forbids shipping any unverified claim). Design
checkpoint = look/palette/type/motif in ~4 lines (the **motif line states device + meaning + how a
stranger reads it AT FIRST APPEARANCE** — label/legend/figurative, the slide-design STRANGER TEST;
a reading that defers to a later slide is a FAILED test written as a passing sentence, and the fix is
a label at first use or removing the device, never a promise that it lands later. 🔴 **It also states
ONE MEANING PER REPEATED FORM, deck-wide** — a device meaning one thing on the cover and another
inside passes every per-page check and still sends the reader asking, which is the test failing;
list the repeated forms and the single thing each means)
**+ the `motif generates:` line — three fields, because a motif that only recurs is an ornament with
a schedule and a motif that GENERATES is what makes the deck look designed rather than decorated:**
`background: <what the motif makes the canvas do | flat by register — reason>` ·
`markers: <the numeral/icon/bullet system it implies>` ·
`page: <the slide whose GEOMETRY is the motif — diagram, chart frame, rail, picture hang or type
composition; `none — <reason>` when the content has no such page, NEVER an invented one>`.
Two "nothing obvious" answers means the motif is a shape someone liked — that is a one-glance veto,
which is the whole point of putting it here.
🔴 **On branch (c) these are REQUIRED, not weighed** — with no generated plate the motif carries the
entire visual load, so "considered and skipped" is unavailable. **Three carves, each stated in
`agents/slide-design.md` §1:** `boldness: conservative` answers the whole triple with its one
`deliberately restrained` clause; a **1–2 slide tiny ask** skips it; and on a **registered/provided
template or Mode-A mimic** the template's device IS the motif — the ladder is NOT re-run on it (that
would re-litigate an approved identity), while the STRANGER TEST, ONE-form-ONE-meaning, and the
triple applied to what you ADD all still bind.
+ the rhythm-map table +
the three design musts + a one-line Form-ledger/diversity verdict + the **`boldness:` + `signature
move:` lines, the latter carrying its `carried_by:` clause** (the dial + the one scoped aesthetic risk
+ the bold reference it adapts + the 2–3 slides where the same idea does STRUCTURAL work — even as an
auto-waiver FYI, a timid "big number" signature move, a wrong dial, or a risk that lands on exactly
one slide should cost one glance to veto) + the **`interior register:` line** — the quiet cue that
carries the style onto ORDINARY INTERIOR pages (a faint grid/scanline, a corner numeral system, a thin
edge rule, a small seal), or the explicit carve `none (flat by register — <reason>)`. It is a required
line, not an optional one: self-verify (q), PRE-FLIGHT 6b and the critic's Lens-B `register_interiors`
check all READ this field, and a deck whose style lives only on the cover and dividers fails all
three — 的风格要走所有页. Do not confuse it with the loud signature motif, whose ≤3-appearance budget
still binds; this one is the chrome-quiet echo that MAY repeat on every page. + the **`density:`
line as two numbers** (planned median words/slide, planned count over 70, and how many content slides
have a non-text protagonist — self-verify (r); the hand-off density gate is compared against these) +
the image opt-in list (the
few proposed images, for approval — **each row carries its source token**: `generated — <tool>` /
`sourced — <origin> (<license>)` / `provided — …` / a `searched, none found → …` rung (full grammar:
`references/image-generation.md` step 5), per the REFERENT RULE in `image-generation.md`) + the **`logo plan:` line with its evidence token**
(`official asset — <source>` / `searched, none found → designed wordmark (flagged)` / `n/a — <reason>`,
where the reasons include **`third-party assessment`** — a deck ABOUT an entity but not FROM it,
carrying what that entity would not publish about itself; that row is decided before the search and a
found logo does not overturn it; a bare
"wordmark" with no recorded search on ANY deck that names a real entity = incomplete, even as an
auto-waiver FYI) **+ on a roster slide, the `entity marks: <N of M sourced | none — reason>` line**
(the deck's own mark and the eight institutions on one slide are two different answers, and one
field cannot carry both)
**+ one required GATE line naming the look-choice that was made — `direction gate:` on the
design-clean branch (c), `style gate:` on the generated-template branch (d).** Branch (c):
`picked A/B/C/D/E of 4 (html: <path>) · said: "<the user's verbatim paste-back line>" · diversity: <ok | flagged <pair> → rediverged | justified: <reason>>`
— the `said:` field quotes the line the directions page copied to the user's clipboard (`I pick
direction B — Keynote`, or `I pick E (my own): <text>`) **verbatim, or the carve**. It exists because
the gate is now rendered CONCURRENTLY with the Step-1 planner rather than blocking it, and a gate
that no longer blocks is a gate that can quietly become self-attested — "picked B" is a claim the
coordinator can write without any user having chosen anything, whereas a quoted paste-back line is
evidence a person acted. Under the AUTO WAIVER write `said: auto-pick (waiver)` — the waiver removes
the stop, never the record.
— **4 rendered directions (A–C = >=1 bespoke register + best-fit DNA presets, D = the colour-scheme option), E = describe-your-own**;
the mechanical-check verdict rides on the same line, so a collapsed set cannot be posted as a
choice without the collapse being spoken — or the named carve (e.g. `carve: user said just-go` /
`carve: Mode-A mimic`). Branch (d): `picked <X> of 3 (gallery: <path>)`, **or**, when Auto/你决定
skipped the gallery, `carve: auto-pick — ` **followed by all three candidate styles WITH the
one-clause reason each loser lost** (e.g. `art-deco: 与 shanghai-city 撞档 · photo-collage: 无版权图源`).
**A design checkpoint on branch (c) or (d) with no gate line is not ready.** Both are the gate
artifact that keeps the choose-a-look step from silently vanishing — history: branch (c)'s gate was
made a default precisely because an "offer" got skipped under momentum, and branch (d)'s gallery
carried the same wording with no line to record it, so an Auto pick left NO trace that alternatives
ever existed. The carve arm is what makes this cheap: Auto never has to *generate* three galleries,
but it must always *name* what it rejected — the user's veto costs one glance either way. Keep each under ~25 lines — the user reads it in the
terminal and answers in one click. Do **NOT** write `content-plan.md` / `design-plan.md` files
into the deliverable folder (they clutter it; the conversation is the record) — unless the user
explicitly asks for plan files.

**(web-researched / no-source decks) the content checkpoint carries THREE more required lines — the
research floors from `content-planner.md` §2(e).** `coverage:` (全面 — the domain areas enumerated ·
covered · consciously cut), `lifecycle:` (every featured product/version/entity confirmed live as of
today · anything found discontinued/renamed + how the deck handles it — a proactive status sweep, not
the reactive recency check), and a `provenance:` digest (准确 — `checked N · confirmed N · fixed N ·
cut N`, each load-bearing fact corroborated across ≥2 *independent* credible sources; content-farm /
AI-spun blogs corroborate nothing; MED facts ship only when labelled "per public reporting, as of
&lt;month year&gt;"). 充实 rides on the per-slide `承载证据` column — a load-bearing row whose evidence
is all adjectives and no concrete specific (number / date / price / named result) is not ready. 🔴 **A
web-researched content checkpoint missing any of the three is NOT READY** — the same rule, and for the
same reason, as a branch-(c)/(d) design checkpoint with no gate line: a floor with no line to record it
silently becomes a floor nobody stood on. Measured: a no-source deck shipped thin and headlined two
discontinued products because the sweep, the status check, and the depth were never recorded. The
Codex path carries the identical floors as `content.coverage` / `content.lifecycle` /
`content.provenance` + a per-`claim_ledger` `confidence` tier, enforced by `codex_delivery_gate.py`.

**The design checkpoint carries a `density:` line, and it is a NUMBER, not an adjective.**
Write it in the SAME two quantities the gate measures, so plan and gate can be compared at all:
the planned **median** load, and how many slides you expect to be **over 70** — plus the count of
slides whose protagonist is NOT text.
`density: median ~35 words/slide · 0-2 of 11 over 70 · 4 of 11 content slides carry a figure or chart`.
A planned *median* against a gate that counts a *tail* is two different questions: a deck sitting at
69 words on every single slide — 2x this example, 1.7x the budget — has a perfect tail count and
passes cleanly, and the plan line would never have caught it either. Name both numbers or the plan
teaches a value nothing can check. It exists because
the density warning already existed, was already correct, and was already ignored: two
consecutive decks shipped with 8/12 and then 12/12 slides over the presented budget (loads of
81-144 words against ~40) while the per-slide `TEXT WALL` line was read and dismissed as
advisory both times. The skill's own reference deck runs at a median of **27 words a slide**, so
the budget is not the problem. A number on the checkpoint makes density a decision at plan time
instead of a discovery at lint time — and `scripts/render_deck.py --deliverables` now refuses the
hand-off when more than a third of slides are over, unless `.deck-gates.json` carries
`"density": {"waived": "<why this deck is meant to be read, not presented>"}`.
**Slides are a visual aid for a speaker; the sentences belong in the speaker notes, which a
pipeline-built deck already has.**

**The `review:` tier is NOT a delegated Step-0 pick** — it is asked at Step 5, after the first
clean render, with the deck visible (SKILL.md → the post-build review question). What the auto
waiver changes: the post-build question is not posted as a stop; the coordinator runs the
**default, `fast`**, and records it in the FYI and hand-off as
`review: fast (post-build default — auto)`. 🔴 **Auto may never pick `none`.** Delegation covers
preferences the user would have expressed; it does not cover declining review of a deck they never
saw — skipping the loop entirely is a decision only the user can make, with the deck in front of
them. An auto run that wants MORE than `fast` (a defense, an exec readout) may escalate and must
record the reason: `review: standard (escalated — defense deck, auto)`. Either way the tier and
its derivation appear in the hand-off `review:` line; a tier recorded nowhere is
indistinguishable from a review never run.
