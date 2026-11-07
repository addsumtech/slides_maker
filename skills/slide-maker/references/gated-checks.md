# Gated checks — the rules each hand-off gate enforces

Read the section a gate names when it fails, or when SKILL.md sends you here. Everything in this file is enforced by a script (`render_deck.py --gate-check`, `codex_delivery_gate.py`, `lint_deck.py`, `deckkit.lint_layout`), which prints the failing section and its fix — that is why it could leave SKILL.md. Moved verbatim from SKILL.md (2026-11-07).


## Purpose sections, talk slot, coverage, deliverables, navigation, citations

🔴 **TWELVE of the thirteen purposes DECLARE required content, and the deck is held to it at
hand-off.** grant (aims · feasibility · risk) · progress/guidance committee (progress · plan ·
**ask**) · journal club (attribution · critique) · clinical case (presentation · investigations ·
management · outcome) · thesis defense (contributions · limitations · future work) · conference
talk (contribution · evidence · limitations) · job talk (track record · research plan · fit) ·
exec/investor readout (the ask · the number · the risk) · lab meeting (what changed · open
questions) · work status (outcome · the ask) · product pitch (positioning · benefits) · teaching
(objectives · worked example · recap). Each carries sections its audience is asked to judge
against, so a deck missing one is not a lean deck — it is a deck missing something the room needs.
`scripts/purposes.py` declares them and `scripts/check_purpose.py` looks for them in the built file
(both gate paths, CJK terms included, extend with `design_plan.purpose_section_terms`, waive in
writing). It binds ONLY when the recorded purpose matches a registry entry — anything else is NOT
CHECKED, never a guessed genre. **This is the `formats.py`/`check_surface.py` mechanism generalised
from SURFACES to GENRES**, and for the same measured reason: the shape of a genre is exactly what an
author under time pressure drops.
🔴 **A TALK ALSO HAS A SLOT, and the interview already asks for it** ("for a talk, give me the time
budget and I will confirm the slide count"). Record it as `content.talk_minutes` — both `--init`
scaffolds now show the field — and `scripts/check_talk_time.py` compares the BUILT deck against it
on both gate paths. It reads the SPEAKER NOTES only, because that is what gets said out loud (the
on-slide words are not spoken by anyone following PRE-FLIGHT 1, and counting both would punish the
decks that follow it), and it reports a BAND, never one number: 130-150 words per minute for a
word-delimited script, 180-220 characters per minute for CJK. **A script it has no sourced rate
for and cannot segment — Thai, Lao, Khmer — is NOT CHECKED by name rather than given a number**,
and a per-slide budget (`10 minutes each` / `每页 2 分钟`) is read as no budget at all, because
taken as the talk's length it makes a correctly sized deck look twelve times too long. `OVER THE SLOT` blocks — with how many slides' worth of
speech to cut — while `TIGHT`, `UNDER THE SLOT` and `ONE SLIDE EATS THE TALK` (a page carrying more
than a quarter of the slot) are notes. **No budget recorded, or notes on fewer than half the slides,
is NOT CHECKED and says which** — a deck that will be READ is never late, and an estimate built from
a third of the talk is worse than none because it reads like a whole one. Waive in writing
(`{"talk_time": {"waived": "…"}}`) when the slot really did change.
🔴 **"PASSED" IS NOT "CHECKED" — read the COVERAGE line.** Every gate run now ends with
`[gates] COVERAGE: N section(s) ran — X bound, Y NOT CHECKED`, one row per section that could not
bind and why. Measured, which is why it exists: three gates were silent on every deck because
nothing asked for the field they read, the template gate could bind to 1 of 11 registered
templates, and each was found by a human reading a transcript rather than by the tool. A row is
not a failure — a section that does not apply to this deck is correctly unchecked — but an
unread ledger is how a capability goes quietly unused. The Codex delivery gate prints the same
tally.
🔴 **THE DELIVERED PDF NOW KEEPS ITS ALT TEXT, AND THERE IS A SPEAKER HANDOUT.** `--deliverables`
exports through LibreOffice's PDF/UA filter: measured, the plain export produced a tagged PDF with
ZERO `/Alt` values, so every image description the a11y gate demanded stopped at the .pptx — in
the one artifact that gets emailed. It is a SEPARATE export from the render's: putting the filter
on the rasterization path changed a pixel check's verdict on another LibreOffice, so the render's
PDF stays plain and the accessible copy is made at hand-off.
It also writes **`<deck>-notes.pdf`**, one page per slide with the slide above its notes: this
skill requires speaker notes and reads them to estimate the talk's length, and then handed over
two artifacts in which they are invisible. A deck with no notes gets no handout and says so.
🔴 **A PRESENTED DECK IS NAVIGATED, NOT JUST READ — and until now this library could not make one
jump.** Measured: `hlinkClick` appeared only in `_EA_FOLLOWERS`, a constant listing XML element order,
and `click_action` in no file at all, so every "backup slide" this skill ever built was reachable only by arrowing past
everything in between — which is exactly why prepared answers go unused. `dk.link` (shape → slide,
shape/run → URL, **scheme-guarded**: a link target usually comes from the untrusted material the
deck was built from), `dk.agenda(..., targets=[...])` (a contents page you can present FROM, and
the section-progress page a long deck repeats) and `dk.back_link` (the other half of a jump) close
it. **Read `references/navigation-and-qa.md` whenever the deck will be presented live and the room
can interrupt** — a defense, a committee, a conference talk, a board readout, anything with an
appendix. Record the questions you expect as `content.qa`
(`[{"question": …, "slide": <the backup that answers it>}]`, in both `--init` scaffolds) and
`scripts/check_qa_backup.py` checks the BUILT file on both gate paths: a backup slide nothing links
to BLOCKS (`PREPARED BUT UNREACHABLE`), as does a slide number the deck does not have, while
`NO WAY BACK` is a note. **Nothing recorded is NOT CHECKED** — anticipating questions is a practice,
not a law, and a gate demanding it of every deck would only teach authors to record an empty list.
🔴 **AN ACADEMIC DECK CITES FROM ITS .bib, NEVER FROM MEMORY.** Measured: nothing in this skill
ever read a bibliography — `sources_page` and `source_note` take STRINGS — so every citation it had
ever built was typed by hand, which is where a year drifts by one and a middle author disappears.
`scripts/citations.py` parses the BibTeX and derives **both** the in-text marker and the reference
line from the SAME entry (`cit.in_text` / `cit.reference_page`, `numeric` or `author-year`, with
`etal=`/`amp=` so a Chinese deck writes 等 and 与), and **it REFUSES an entry with no
author/title/year instead of printing `n.d.`** — under the never-invent floor a plausible-looking
citation is worse than a missing one, because nobody downstream can tell it from a real one. Record
`content.citations` (`bib` · `style` · `keys` in cited order) and `scripts/check_citations.py`
checks the BUILT file on both gate paths: a `DANGLING MARKER` and a cited key that is `NOT IN THE
LIST` block, an `UNCITED` entry is a note. **Read `references/citations-and-bibliography.md`
whenever the deck cites published work** — it also carries the measured reason
`reference_page` sets the deck's link colour (a renderer paints a linked run in the THEME's hlink
colour whatever fill the run carries, so one references page came out half navy and half Word-blue,
decided by which entries happened to have a DOI).
🔴 **Every section list was DERIVED FROM `design-by-purpose.md`'s OWN PROSE, never invented** —
teaching's objectives/example/recap were already in its Layout and Signature lines, the lab
meeting's "what changed" and "open questions" are its Signature line verbatim. Where a genre's prose
names no required section, none was added: a check that fires on good decks is how people learn to
ignore checks.
🔴 **The thirteenth, `webinar`, has NO section list on purpose — it is a delivery MODE, not a
genre.** The same session can be a lecture, a pitch or a readout, so a list attached to it would be
a guess about which. What it constrains is the MEDIUM, already held by the type floors and
`formats.py`'s safe zones — and `check_purpose` recognises the medium words and asks you for the
GENRE instead of silently checking nothing.
Each genre also carries one fidelity rule beyond never-invent — a pilot stated as a pilot, open work
that reads as open, their claim separable from yours, a simplification flagged to a novice, and on a
clinical case **de-identification, which is the one irreversible item on this page**.


## The user's own files, checked against themselves

> **🔴 THE USER'S OWN FILES, checked against themselves — before the planner reads them.** Record the
> files in the gate record (`content.sources`: `[{"path": "report.pdf"}, …]`, relative to the deck
> folder; `[]` for a deck with no user material) and run
> `python3 scripts/source_check.py material <deck-dir>`. It finds a total that is not the sum of its
> rows or columns, shares off 100% beyond rounding, and the same table in two files with a cell that
> disagrees. Each finding is a **「材料自相矛盾」 open question at the content checkpoint** — only the
> user can say which value is right (auto mode: decide, give the basis, and list it in the hand-off) —
> recorded as `content.material_check: [{"id": "M-…", "resolution": "<which value, who said so>"}]`.
> The gate later traces **every number on the built slides** to these files
> (`source_check.py numbers <deck-dir>`): a figure rounded, converted or worked out goes in
> `content.numbers` as a `source_value` / `derived` row the gate re-checks; one read off a picture is a
> `from_image` row and is reported as not machine-checked. Images, scanned PDFs and .doc/.xls are
> UNREADABLE — ask for a .pdf/.docx/.xlsx/.csv export when the numbers matter.
> `source_check.py numbers <deck-dir> --write-rows` records the unambiguous rows for you (one file figure
> that rounds to the slide's, or the same figure in another unit — each tagged `auto`); read what it wrote,
> delete a wrong one, and decide the rest yourself.


## The icon waiver's category is verified against the pages

🔴 **The category is a claim about PAGES, not about the deck — and it is VERIFIED against the
built file** (`motif-dominant` needs a real loud motif in the file, `tiny-deck` a real tiny deck,
`template-locked` a real template). A deck-level reason may not cover pages the reason does not
reach: `motif-dominant` on a deck whose roster pages carry no motif at all is the measured failure
— a coherence argument overriding a stated default with no per-page test, and the first human
reader's first note was "icons should be here". Re-decide page by page; the honest answer is
usually neither zero icons nor an icon everywhere, but icons on the pages where they do work
nothing else on the page is doing (three DIFFERENT KINDS of fact side by side; the one row a
reader scans FOR an item) and none where another element already encodes the distinction (a
position map, semantic colour, numbered routes, the motif itself).
`design_plan.icon_none_category` + `icon_none_checked: [slides]` (Codex: an `icon` waiver with
`category`). A bare "not category-rich" no longer clears it, and the category explains the REST of the
deck — it is **never** a licence to drop icons from the categorical slides that do have them (a
motif-dominant deck may still put icons on its one roster/preview page, as this skill's own UK-labour
deck does on its two 3-item slides). 🔴 **But icons must ENCODE, not decorate** — a topic-stamp beside
a lone big number or a single statement is decoration that fails the 1-second-decodability floor
(`design-must-be-meaningful`); the default is "icons on the categorical/conceptual slides," not "an
icon on every slide." **(3) diverse formats** (not a card grid repeated) — musts 2–3 are
*applied where they help or justified where not* (a must to consider + apply, never a blank per-slide
quota — still smart about where/when). A plan that defaults its look, over-relies on one format, forgets
icons, or — when builds are opted in — leaves a built slide half-staged or forgets builds where they'd
clearly help is **not ready** — send it back to the art director.


## Accessibility floor

- **Accessibility is a FLOOR, not a nicety.** `lint_deck.A11Y_CODES` — missing alt-text, untitled or duplicate-titled slides, reading order, non-text contrast — is held by `--gate-check`'s `a11y` section and by the codex gate from **one shared list**, because a floor kept in two places is how one runtime quietly stops enforcing it. 🔴 **Decodability is now MEASURED, not asserted.** Three checks, each turning a rule this skill already stated into something countable, all added after a first human reader asked three questions of a deck that had passed every gate: **`MOTIF_UNEXPLAINED_AT_FIRST_USE`** — the stranger test is about FIRST appearance, and the old check cleared on a legend *anywhere*, which is the deferred reading SKILL.md calls "a FAILED test written as a passing sentence"; **`UNNAMED_REPEATED_MARK`** — four or more identical marks with no text within reach are reported, because unlabelled repetition reads as texture whatever you meant by it, and such a group is invisible to every other check (not text, not tagged, trivially clears contrast); and the **icon waiver's category is verified against the built file** — `motif-dominant` needs a real loud motif, `tiny-deck` a real tiny deck, `template-locked` a real template, and the waiver must name EVERY flagged slide, not a subset. Only the **unambiguous** subset blocks (`lint_deck.A11Y_BLOCKING`): a shape either carries a description or it does not, two slides either share a title or they do not, a ratio either clears 3:1 or it does not. **`NO SLIDE TITLE` stays advisory on purpose** — lint's own message calls an off-canvas title "a sanctioned trick for statement slides", so the skill EXPECTS slides that look untitled, and measured on an ordinary well-built 11-slide deck it fired once, on the closing slide. A gate that fires on a deck built exactly to spec is not a floor; it is training for the waiver reflex. Waive in writing (`{"a11y": {"waived": "<who reads this deck, and how>", "waived_category": "…"}}`) and say so in the hand-off note. `scripts/palette_audit.py` now also simulates deuteranopia/protanopia/tritanopia and names any pair that stops being two colours — `dk.OKABE_ITO` was recommended for years with nothing checking it.


## Material-probe carve record

> 🔴 **The carve is now RECORDABLE, which it was not:** `{"material_probe": {"waived": "<which
> template / which mimic / how many slides>", "waived_category": "registered-template |
> provided-template | mode-a-mimic | tiny-ask"}}`. Both gate paths accept it and both refuse
> `conservative` as a category, because this block says restraint is a material decision too. Before
> this the gate had no waiver arm at all, so a deck on a registered template had to invent a probe
> artifact and write a note explaining that the gate and this text disagreed — a rule whose
> documented exception cannot be recorded forces a false record.


## Build-time lint — every CRITICAL and why

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


## Sameness and timidity

> **One of those gates is SAMENESS, and it is the one that can send you back to the build.** The
> deck-level monotony signals (`LAYOUT SAMENESS` · `SKELETON VARIETY` · `CARD DOMINANCE` ·
> `BOTTOM-STRIP MONOCULTURE` · `TITLE-RULE MONOCULTURE` · `ENVELOPE MONOCULTURE` · `FLAT RHYTHM`)
> were measured on every deck and blocked nothing — printed as advisories under a line saying they
> were advisory. **≥4 distinct ones, with at least one structural, now block the hand-off.** It
> applies only to a deck that is ≥8 CONTENT slides (cover, closer and any declared
> `design_intent(role="appendix")` run excluded), landscape, and not `--surface` — calibrated by
> building and linting decks in the registers this skill itself prescribes, where a 6-slide status
> update, a rednote carousel and an appendix-heavy defense deck all trip 3+ signals *legitimately*.
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
> side only, the cheap way always wins.** The user's verdict was that *the design had got weaker* and nothing in the
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


## What --deliverables requires in the gate record

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
**`style_pick`** (the TOPIC-adapted look choice — `<preset|bespoke|generated register> for <domain> ·
beat <nearest rival> because <clause> · anti-pick avoided: <the domain / image cliché>`, or `n/a —
<locked template | mimic | provided>`; run the ranked contest in `references/design-by-topic.md`
(domain → apt presets → ANTI-PICK + CLICHÉ GUARD) so the look fits the SUBJECT, not a reflex — it
governs the design-a-clean, bespoke, AND generate-a-template branches alike) /
**`motif_generates`** (background · markers · one page whose geometry IS the motif — a motif that
only recurs is an ornament with a schedule; carved out, like `signature_proof`, under a
`conservative` dial with a recorded `deliberately restrained:` move) /
**`image_sources`** (one row per CONTENT IMAGE carrying its EVIDENCE TOKEN — `slide <n> | <subject>
| sourced — <origin> (<licence>)` · `provided — user (own material)` · `generated — <tool>` ·
`searched (Commons, Openverse), none found → generated, flagged illustrative` · `… → native form`;
the grammar and the REFERENT RULE that picks between them live in `references/image-generation.md`,
and a deck with no content images writes the string `n/a — <why>`, exactly like a `logo plan: n/a —
…` line. The tokens are not taken on trust: `scripts/check_image_provenance.py` — run by BOTH gate
paths — holds each one against `assets/**/sources.json`, the ledger `scripts/fetch_images.py`
writes, and against the built deck's own text. Two claims it makes checkable for the first time:
a `searched, none found` rung must be backed by a RECORDED search (and an `unreachable` network is
refused as one — a blocked host is not evidence that no photo of Amsterdam exists), and an
attribution-required photo must be CREDITED ON A SLIDE, not merely licensed in the plan) /
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


## preflight_check.py — the four hard FAILs that are not numbered items

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


## notes="none" when the user declined the spoken script

🔴 **And `notes="none"` when the user declined the spoken script** —
`dk.declare_delivery(OUT, "presented", builds="static", notes="none")`. Exactly the same argument
one rule later: `NO NOTES` fires on a presented deck with empty speaker notes, and a user who asks
for the script to be removed has made a decision that had nowhere to live, so the warning fired on
every lint run forever and was waived by hand each time. 🔴 **It silences that ONE warning and
nothing else — the word budget is deliberately NOT raised.** The skill's position is that the
sentences belong in the notes, so a deck carrying them on the slides instead is a real tension worth
still seeing; moving the ceiling would use the tooling to endorse what the skill argues against.
`selfread` · `surface`. **Pass `builds="static"` on a presented deck whose user opted OUT of
appear-builds** (`dk.declare_delivery(OUT, "presented", builds="static")`): the builds choice is a
user decision exactly like the mode, and it was the one still carried by memory — without it
`--static` has to be retyped on every lint run or `NO BUILDS` fires on a deck that is static
*because they chose that*. It writes `delivery` into `<deck dir>/.deck-gates.json`, which **both**
`lint_deck.py` and `render_deck.py --gate-check` read, and a recorded value beats a conflicting
flag in both (they say so and name the file). Why it is a 🔴 and not a convenience: a mode that
lives only in flags is a fact carried by memory, and it gets dropped. Measured on a delivered
14-page self-read deck — 20 `[stats]` lines with no flag, 10 with `--selfread`; the ten were the
~40-word *presented* budget applied to a deck nobody speaks, plus "14 of 14 slides have empty
speaker notes". Half the advisory output was noise the tool generated by not knowing what it was
looking at, and noise is what teaches people to skim gates. (`--briefing` is lint-only and is NOT
recordable — `render_deck.py` has no briefing floor, so recording it yields a deck that lints
clean and cannot pass hand-off; the lint refuses it by name and says why.)


## Deck stats — what each [stats] warning measures

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
it has been seen on real decks, not on the day it ships), **`TEMPLATE-BOUND`** (the composition-boldness
counterweight — fires ONLY when the deck's own `design_plan.boldness` is `bold`/`experimental` yet NOT
ONE interior page breaks its default frame: no full-bleed, no statement-with-void, no dominant hero,
every content page a variation of the same safe rectangle. It measures the *floor* of compositional
timidity — a deck can score 11 distinct skeletons and still park all its daring in the concept + chrome,
never in where the ink sits; whether a breakout is genuinely *innovative* stays the critic's
distinctiveness call. Advisory, and — like `WEIGHT MONOCULTURE` — deliberately kept OUT of the blocking
timidity composite until seen on real decks; sound restraint is never nudged (`boldness: conservative`
silences it)), and on CJK decks **`CJK TIGHT LEADING`** (multi-line
CJK at ≤ single spacing → use the script-aware default) and **`CJK-LATIN SPACING`** (both pangu spacing
conventions mixed → pick one deck-wide). Treat each `[stats]` warning as the NAMED design rule
having failed measurably: fix it or write one clause of why this deck is the exception, and **paste
the stats block into the critic's input** so the judges score numbers, not impressions. It's a safety
net for the no-overlap / fits-its-box / density / rhythm rules, **not** a
replacement for looking (it can't judge crop, balance, legibility, or fidelity).
