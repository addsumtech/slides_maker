# Why-log — the measured incidents behind SKILL.md rules

Each rule these stories explain is still stated in SKILL.md; this file keeps the long account of the run that caused it, for anyone weighing whether a rule can change. Moved verbatim from SKILL.md (2026-11-07).


## Audience brief — the two measured failures

> **Measured, twice, and the second time the rule already existed.** (1) a Chinese request reading "a PPT introducing Paris" →
> a deck that correctly refused the Eiffel-tower motif and then also deleted the landmarks, the
> districts and the food, delivering an argument about 19th-century building regulation. (2) A
> Melbourne deck built from the recorded answers `audience = people planning a trip` and
> `goal = they leave able to plan one`: the Step-1 brief described the city, the three arc
> candidates were all generated inside that frame, and the winner was picked because *"it is the
> only candidate whose organising idea also does the organising work … nothing is easier to
> remember a week later"* — a DECK-QUALITY test. The recorded `goal` was never used to score them,
> and the practical candidate was rejected for becoming *"the same list every travel site gives
> me"* — which, for someone planning a trip, IS the deliverable. What shipped was a thesis on an
> 1837 land survey. The frame also aimed the RESEARCH: chains, allotment widths and inscription
> years were verified; daily cost, distances, a rainy-day alternative and what to skip were never
> asked for. Every gate passed.
> 🔴 **Why the existing rule did not fire:** the Paris lesson lives in
> `references/checkpoint-convention.md` under the *delegated Step-0 picks*, so it binds only under
> the auto-waiver. The Melbourne build ran a full interview and was never inside its scope. **A
> correct rule in the wrong scope is not a gate** — which is why the rule is restated HERE, where
> it binds on every deck, and why it now has a required field instead of a paragraph.
>


## Material probe — why it exists

> **WHY, measured on a delivered deck in this repo's own history.** The pipeline gates a motif's
> CONCEPT thoroughly — a derivation ladder with two middle rungs, two rejected pictures with the
> clause that lost each, the STRANGER TEST, ONE-form-ONE-meaning, the generativity triple — and its
> MATERIAL not at all. On that deck the concept was genuinely right (a config row, derived from the
> product's own `cordis.yml`, correctly rejecting the plug-socket stereotype every plugin deck
> reaches for) and it passed every one of those checks. **What shipped was six grey rectangles.**
> The user's verdict was that the design had got WEAKER. The repair changed only the material — the same rows became
> a real config with keys, values and a `-`/`+` diff — and nothing about the concept moved. **No step
> between "concept approved" and "deck delivered" had asked what the device is MADE of.**
>
> The cause is an order-of-work failure, not a missing rule: the design turn had ~20 required
> declarations and zero required artifacts, so the effort went into sentences that pass instead of
> a thing that works. `signature move: the cover demonstrates the argument itself` is a good sentence and it was true of
> nothing on the page. **Pixels cannot be faked this way** — a grey-bars register renders as grey
> bars — which is the whole reason this probe comes first.
>


## Anchor proof — what it costs

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


## Measured text heights are calibrated in CI

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
