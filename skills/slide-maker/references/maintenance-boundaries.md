# Maintenance boundaries — what not to collapse

**Read this before merging, removing, or "simplifying" any gate, artifact, or check in this
skill.** Not before an ordinary deck build; this file is for whoever is changing the skill itself.

`check_skill_lossless.py` already guards one half of a refactor: it proves the *bytes* survived.
It cannot see the other half. Two gates merged into one, a warning promoted to an auto-fix, a plan
field trusted instead of re-tested — every one of those keeps every line of text and still removes
the property the text was describing. The lossless check reports a perfect score while the skill
gets worse.

So the boundaries below are **negative contracts**. Each one names a tempting simplification and
what it would cost. Violating one is not a refactor; it is an architecture change, and it should be
argued for on its own rather than arriving inside a cleanup commit.

Where a boundary is decidable by a program, `tests/test_maintenance_boundaries.py` asserts it. The
rest are here because someone has to read them — which is why this file is short and why every
entry says *why*, not just *don't*.

| Do not | Why |
|---|---|
| **Merge build-time `lint_layout` and render-time `lint_deck`** | They answer questions that cannot be asked at the same moment. `lint_layout` reads the `.pptx` and must fire *before* a render is paid for; `lint_deck` reads the rendered PNGs and can see what no geometry knows — text that renders as nothing, a plate that vanishes into its ground, a deck with no light/dark rhythm. Merging them either delays the cheap checks or invents pixel answers before pixels exist. |
| **Add auto-fix to any lint** | A mechanical patch silently overwrites design intent and ships a worse page than the one it "fixed". The findings are written to be *acted on*, which is why every message names a remedy instead of applying one. This is also why `--fix` has never existed: its absence is the contract. |
| **Trust a plan field as evidence about the built deck** | A field written at plan time, before any slide exists, proves nothing about what got built. Measured repeatedly: an `icon_family: none — <reason>` waiver that was true when written and false by page 3; a declared single-hue palette that shipped two library defaults; a `form_reach` claim beside a deck of raw boxes. Every plan claim that can be re-tested against the `.pptx` is re-tested against the `.pptx` (`_report_icon_waiver`, `_report_palette_drift`, `_report_form_reach`, `_report_carried_by`). A new plan field should arrive with its re-test, not instead of one. |
| **Let a gate's vocabulary drift from what the linter emits** | A gate that names codes nothing produces believes it is enforcing them and can never fire. Measured: two of seven `STRICT_STATS` entries matched no linter output at all, while the test fed the gate its own expected shape and passed. Cross-file agreements are decidable by a program; assert them. |
| **Move operational knowledge out of SKILL.md into `references/`** | Layer 2 is safe only for content with a backstop — a required artifact, a deterministic check, or a checklist item naming the file. Which component to reach for and what to scan a render against have none: nothing reports their absence, the build succeeds, the lint passes, and the output is quietly wrong. Measured on the split that tried it: the next real run read 3 of 10 reference files, hand-rolled a chart with the wrong helper, and shipped zero icons — passing every automated gate. |
| **Widen an exemption to quiet a false positive** | The tempting fix for a check that cries wolf is a broader exemption, which usually silences the true positives with it. The pattern that works: measure which cases misfire, name the *class*, and guard exactly that class — `RAGGED LEFT EDGE` reports nothing on a correct deck because of five specific guards, not one loose threshold. If a check cannot reach acceptable precision, do not ship it; a gate nobody trusts is worse than no gate. |
| **Fan out a single argument across blind agents** | Parallelism speeds *gathering* and never *understanding*. Separate documents, separate asset prep, separate review lenses: fine. One paper's intro / method / results split across agents that cannot see each other: the through-line is one mind's job, and the seams show. |
| **Turn the actor–critic loop into a single pass** | Its *weight* is what scales to stakes — two focused lenses for a quick deck, a full panel for a high-stakes one. Its existence does not. The critic is the only stage that judges the deck as a reader rather than as a file. |
| **Assume an asset that exists is an asset that worked** | A failed generation writes a truncated file or a flat placeholder plate; a bad crop writes a fully transparent frame. All three embed without complaint and pass every geometric and density check, because the picture does occupy its box. `ASSET NOT USABLE` exists because existence is not success. |
| **Move a check from deterministic code into the critic's judgment** | The direction of travel is one-way: deterministic > required field > checklist > prose. A contrast ratio, a bar-length proportion, a schema order — each has one arithmetic answer, and paying model prices for it in a dispatch that might not look next time is a downgrade even when the model gets it right. The reverse move (critic judgment → deterministic check) is always welcome. |
