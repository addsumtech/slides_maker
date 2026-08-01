# Handoff checklist

## The hand-off note — what it must carry

**Keep the hand-off minimal — caveats + next steps, not a recap.** The note should carry only what
the user *acts on*: the folder path, the open-the-pptx check, the font/portability caveat, any
forward-looking content you added, open questions (e.g. a missing real brand asset to supply) —
**plus, when they apply, these REQUIRED-by-their-owning-rule lines (this list is the ONE
authoritative hand-off checklist; the owning rules point here):** the `provenance: N checked · N
confirmed · N fixed · N cut` line (research-sourced decks — the PRIMARY-SOURCE GATE's artifact), the
**capability ledger** (the four host lines from Step 0, plus what was LOST wherever a
capability was absent — a degraded run must be legible as degraded), the
**`review:` line** (the effort tier that ran, plus its derivation, and the reason whenever it sat
below the derived default — `standard (derived from purpose)` / `fast (derived default was
thorough — user chose speed)`) and the **`cost:` line** (subagents · tokens · wall-clock · **web searches planned/spent**). Searches belong on this line because the cap is per SESSION and shared with every subagent: the deck that exhausts it is rarely the deck that suffers, so the only way the number ever becomes visible is if each deck reports what it took. The
cost line is not bookkeeping: a dial the user sets but never sees the bill for builds no
intuition, so the next deck's choice is as blind as the last one's. Report both even when the
tier was derived rather than chosen. Then, as before: **`render_deck.py <deck>.pptx --gate-check` run and reported** (every hand-off gate, no render, under a second — run it whether or not the user wants the PDF, because the gates used to ride on `--deliverables` and that is a decline-able offer), the
**`.deck-gates.json` written at the deck root** (the record `--deliverables` checks: critic verdict,
the design plan's **boldness · signature_move · carried_by · form_ledger · icon_family · palette ·
type_scale · signature_proof** — all eight, since the four that were added are exactly the ones whose
absence let a deck ship with zero icons through every automated gate — and the provenance pass's
per-claim `claims` list, never a summary tally — or, for any gate deliberately skipped, a written
`waived` reason **plus its `waived_category`** (`no-dispatch-on-host` — which also requires
`inline_ran: true|false` — `already-reviewed-minor-edit`, `user-waived`, `external-deck`); an
unclassified waiver is rejected, because it is indistinguishable from never having run the loop. The
`critic` block on the CONSENT path is written by `validate_review.py … --record <deck-dir>` from the
review itself, never typed here; a waiver is always hand-written, which is why it must be
classified), the
per-slide **click order** (appear-builds opted in), **image licenses/credits** (sourced photos), the
**GIF plays-in-slideshow** note (embedded GIFs), **accepted advisories** one plain-language line
each, the **`distinctiveness:` line whenever Step 5's bold/experimental escalation fired**
(`user waived (bold)` or `resolved in round N` — without it, "they accepted it" and "I never asked"
are indistinguishable afterwards), and on an auto-waiver deck the **delegated-picks recap** the user
reacts to at hand-off — and —
optional, exactly one sentence — the critic's `ceiling`, verbatim, as one *"if you want to push it
further:"* line (the terminal consent's recorded headroom; if the user adopts it, it flows through
the normal post-delivery feedback loop). Two taste-ecosystem lines ride the same note when they
apply (`references/user-taste.md`): **(a) the save-this-look offer** — for a freshly-designed look
(Q1 branch (c), either sub-path) not yet registered, one line: *"save this look to your registry as
<name>?"*; on an **explicit yes** persist the deck's `style.py` + a `profile.md` per the existing
registry conventions, distilling the final round's critic `strengths` and any cross-round recurring
finding dimensions into the profile's existing **Notes** field (hand-off, after the critic loop, is
when the profile can carry what the vetted deck *proved* — this is collaborative mode's Gate A 7(b)
persist, re-timed: one save, one owner); **skip the offer entirely under a per-deck auto directive**
— never an un-consented registry write; **(b) the taste write-back FYI** — whenever the Step-6 close
below wrote anything to `taste.md`, one line: *"recorded to your taste profile: <X> — say the word
and I'll drop it"* (visibility + easy veto is what keeps a memory trustworthy). Do
**not** narrate the deck slide-by-slide, restate what they can see in the render, or self-praise the
result — a tight hand-off respects their time and reads as senior.

## Speaker notes, editability, and iterating after delivery

**If the deck has speaker notes, tell them how to use the notes.** They render nowhere on
the slide, so the user may not know they exist: "the spoken script is in the notes — open
**Presenter View** (PowerPoint: Slide Show → Presenter View; Keynote: Play with a second
display / rehearse mode) to see it while presenting." Offer to **export the notes** as a
plain-text rehearsal script with `scripts/export_notes.py deck.pptx` if they'd rather
rehearse away from the slides.

**Tell them the deck is fully editable — and how to change it without losing work.**
The `.pptx` is native (real text/shapes/images), so they can edit anything in
PowerPoint/Keynote and save. But the build script *regenerates the file from scratch*,
so a later rebuild would overwrite anything they hand-edited — the two don't merge. So
give them the two non-conflicting lanes in one line: **(a)** take it from here in
PowerPoint themselves (you won't rebuild over their file), or **(b)** tell you the
changes and you edit the build script (reproducible, survives future iterations). Note
the font/portability caveat if relevant. Full guidance — and the rule for iterating
safely — is in `references/handoff-and-iteration.md`.

Then **fold in the user's feedback** — treat their corrections as the highest-priority
signal, re-run the build → render → critic loop, and keep going until **the user is
satisfied**. **One safety rule when iterating after delivery:** before you re-run the
build, check whether the user has hand-edited the delivered file (ask, or compare its
mtime to your last build); if they have, **don't regenerate over it** — reconcile first
(fold their edits back into the script via `scripts/extract_deck.py`, or edit their file
in place). Never silently clobber edits you didn't make. Each round should make the deck
more specifically theirs (their emphasis, their wording, their priorities), not just
generically "better". On each user-feedback round, add one **`user-dials:`** line to the round
record — `dimension → direction, layer — "verbatim user words"` (e.g. `colour: +vivid, content
layer — "太素了"`) — WHY the round happened is the datum the taste profile promotes from, and the
evidence the pendulum-overshoot check cites (`references/handoff-and-iteration.md` "Move the dial").
