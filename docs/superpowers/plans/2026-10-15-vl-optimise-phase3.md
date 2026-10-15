# Visual languages, Phase 3 — optimise the fifteen languages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:**
- Fix the language-page defects that measurement confirmed.
- Turn the recurring ones into contract checks, so a new language cannot reintroduce them.
- Show every changed language to the user before/after, and keep only what they approve.

**Architecture:**
- Step 1 of spec §6, "verify first", is done. Four verifiers measured the art-director's ~50 candidates on the vl-components-p2b pages (.pptx values plus full-size renders). Their reports are in the scratchpad `p3verify/report_{A,B,C,D}.md` and are summarised in the Findings table below.
- Shared causes get one shared fix each: quote size ignores quote length, the cover title shrinks one phrase per line, rules run past their content, and dark grounds keep near-white slabs.
- Single-language defects are fixed at their page function.
- Each recurring class gets a conformance check in `vl_conformance.py`, run by `check_vl_contract.py` and `tests/test_vl_contract.py`. Its threshold is calibrated on the confirmed cases and on the currently-good pages.

**Tech Stack:** the visual-language engine (`visual_languages.py` page engine, `vl_native.py`, `vl_native2.py`, `vl_native3.py`), python-pptx, `lint_deck`, `vl_conformance`, LibreOffice + pdftoppm for the sheets.

**Spec:** `docs/superpowers/specs/2026-10-15-visual-language-system-design.md` §6 (also §8 constraints). Branch `vl-optimise-p3`, stacked on `vl-components-p2b`.

## Global Constraints

- Never invent words, numbers or names on a page; derived words are declared.
- Commit locally. Push, release or rsync the installed copy only when the user says so.
- Before any push: the full local CI and the Linux font simulation. Between tasks, run the suites the task touches. The full CI runs once, at the end (the user asked for speed, 2026-10-15).
- Fixtures are self-built; the user's own decks are never used as test input.
- A threshold that flags a page the user approved is re-examined, not silenced (spec §10).
- Ordinary decks stay byte-identical: the 76-example guard holds.
- Samples are re-rendered and committed only for the languages the user approves (spec §6.4).

## Review Focus

1. **Quote scaling at the extremes.** A 3-word quote must not explode past the page. A 60-word quote must still fit, shrinking toward the floor, or be refused loudly (VLTextOverflow), never truncated. Test: Task 1.
2. **Title wrapping in CJK.** A two-line cover title in Chinese or Japanese must break at a word or phrase boundary, never mid-word or with a lone character. Test: Task 2.
3. **Rule end tied to content.** Rules must still reach content when a column is the longest (4 items, long copy). They must not shrink to nothing when a column is empty. Test: Task 3.
4. **The slab check and real photographs.** A user's own photo on a dark ground is content, not a slab; only drawn fills are judged. Test: Task 4.
5. **Distinctiveness, calibrated.** The check must flag editorial/light vs ink/light, and must pass every pair the user has seen and approved, e.g. starlit vs tally-night. Test: Task 7.

---

## Findings (verified 2026-10-15; MEDIUM+ unless marked)

| # | class | where | measured | fix site |
|---|---|---|---|---|
| F1 | quote scale | all 15 | quote fixed at 29–44pt whatever its length (a 7-char quote covers 0.3% of the page); attribution 11–15pt; starlit shrinks to 29pt because its box is 0.60W | each `_<lang>_quote` and the engine's quote layout |
| F2 | title fit | editorial, storybook, wayfinding, cutpaper covers; chalkboard with doodle | cover titles 27–34% below spec because the fit sets one phrase per line and shrinks (`_phrase_lines`); wayfinding cover 34pt vs 52pt inside | `visual_languages._phrase_lines`; `_wf_cover`, `_cut_cover`, `_cb_cover` |
| F3 | rule run-on | ink points, broadsheet points and cover, journal margin rule | rules run 2.2in (29–30% of H) past the last text | `_ink_points`, `_bs_points`, `_bs_cover`, `_jn_points` |
| F4 | bright slab on dark | cutpaper-night cards FFFFFF (18–44% of page); interface-dark phone bezel F2F4F8 (24%); collage-slate prints and note card; soft-dusk disc digit 3.05:1; journal-green sample figure FFFFFF (33%) | night palette `panel`; `_ui_image_text` bezel; collage slate print border; soft dusk disc and digit; journal figure mat |
| F5 | HIGH, renderer-dependent | editorial points | "01" wraps to "0 / 1": number box 0.5644in inner vs 0.5651in ink | `_points_led` `item_no` box from measured width + 10% |
| F6 | inverted hierarchy | drafting points; interface points with 4 items | drafting: leader heads 11pt under 15pt lines; interface: heads collapse to 15pt beside 20pt badges | `_bp_points` heads ≥ line size; `_ui_points` head floor 20pt or the two-column alt |
| F7 | empty card or column | cutpaper cover card 49% blank; soft quote card top 58% empty; chalkboard and cutpaper points cards 20–30% empty; drafting cover and quote right 40–47% blank; poster points bottom-left 28% | cards sized to content; drafting gets a drawing on cover and quote |
| F8 | data pages | broadsheet boxed "3" with a wordless cap; interface label above its number, bar labels only 40; storybook vignette 10.9% of the page with a thin digit; starlit glow 3.0:1 under the numeral; wayfinding board rows 20pt thin | per page function |
| F9 | misc | editorial cover crop cuts heads (portrait source); poster quote attribution 12pt, 1.12in away; interface quote tail invisible (1.3:1); wayfinding quote ignores `line=`; journal numerals 0.12in off the heads' baseline; tally pills far and ragged; collage cover title break inside a phrase | per page function |
| F10 | smallest tier (LOW, size only) | all | contrast ≥ 4.8:1 everywhere (faint NOT confirmed); size 10–14pt (1.0–1.5%W) | type roles in the manifests |
| F11 | distinctiveness (LOW–MEDIUM) | editorial/light vs ink/light: ground ΔE 1.5, accent ΔE 2.6, same Georgia; editorial/ink vs ink/night; editorial vs broadsheet ground ΔE 0.6; tally-night vs interface-dark ΔE 9.5/8.2 | the user decides on the sheet |
| dropped | NOT CONFIRMED | ink points contrast; poster "03 touches its bar"; broadsheet drop-cap gap; storybook-meadow hard edge and 3:1 kicker; interface-dark card edges; chalkboard body size and contrast; tally "night only" grid; starlit title size; lists ending half-way in 7 languages | — |

---

### Task 1: Quote pages scale with the quote (F1)

**Files:** `scripts/vl_layout.py` (create: `quote_size(text, base_pt, box_w, box_h, face, *, grow=1.6, floor)`); each `_<lang>_quote` in `vl_native*.py`; the engine's quote layout in `visual_languages.py`; `tests/test_vl_contract.py` or a new `tests/test_vl_optimise.py`.

**Interfaces:** `quote_size(...) -> float`. The largest size ≤ base·grow (when the quote is short) that fits `box_w × box_h` measured with `dk.measure_text` (lint line model), and ≥ floor. Below the floor it raises VLTextOverflow.

- [ ] **Step 1: test** — for every language, a 3-word, a 15-word and a 60-word quote:
  - the 3-word quote's ink covers ≥ 2× the page area it covers today;
  - no quote overflows its box or the page (lint clean);
  - the attribution is ≥ 16pt and sits ≤ 0.5in below the quote's last line.

  Run it; expect FAIL on every language.
- [ ] **Step 2: implement** — `quote_size`, then call it in each quote composer. Starlit's box widens from 0.60W to 0.76W, and its attribution rises to ≥ 16pt.
- [ ] **Step 3: run** — the new test, `tests/test_vl_audit_fixes.py`, `tests/test_native_languages*.py`.
- [ ] **Step 4: commit.**

### Task 2: Cover titles wrap before they shrink (F2)

- [ ] **Test:** each language's cover with a 4-, 10- and 16-word title (Latin and CJK) holds ≥ 85% of the spec title size, on up to 2 lines (3 for 16 words), with no break inside a phrase for CJK.
- [ ] **Implement:** `_phrase_lines` tries a 2-line wrap at the spec size before shrinking; `_wf_cover`, `_cut_cover` and `_cb_cover` (doodle) follow.
- [ ] **Run, commit.**

### Task 3: Rules end at their content (F3) + conformance check

- [ ] **Test (conformance):** on every language's points and cover pages with 2 short items and with 4 long items, every vertical rule (h/w > 20) ends ≤ 0.4in below the lowest text ink in its column band.
- [ ] **Implement:** `_ink_points`, `_bs_points`, `_bs_cover` and `_jn_points` end rules at the measured content bottom + 0.2in.
- [ ] **Run, commit.**

### Task 4: Designed dark grounds (F4) + conformance check

- [ ] **Test (conformance):** on a `dark` ground, no drawn filled shape with luminance > 0.85 covers more than 8% of the page unless it is declared. User pictures are excluded (Review Focus 4).
- [ ] **Implement:**
  - cutpaper-night `panel` becomes cream F1E7C8, with `card_ink`/`card_accent` re-checked to 4.5:1;
  - interface-dark device bezel 2A2F3A;
  - collage-slate print border E8DFC9 and a cream note card;
  - soft-dusk disc stays 9DB8A0 with a 2E2940 digit;
  - the journal-green sample figure gets a cream mat.
- [ ] **Run, commit.**

### Task 5: Per-language fixes (F5–F9)

One commit per language, each with a measured assertion in `tests/test_vl_optimise.py`:
- **editorial:** item_no box measured +10% (F5); cover crop for the visible rect, biased to the top.
- **soft:** quote card sized to content; mark beside the quote.
- **storybook:** data watercolour slot ≥ 20% of the page; heavier digit; point dots carry order, not a repeating cycle.
- **poster:** points rebalance; quote attribution ≥ 16pt, ≤ 0.4in from the quote.
- **cutpaper:** cover card height from content; cover title ≥ the points title; points card heights from content.
- **drafting:** leader heads ≥ line size; a ghost drawing on cover and quote.
- **starlit:** data glow dimmed under the numeral to ≥ 4.5:1.
- **broadsheet:** data at full measure with no wordless cap.
- **journal:** numerals on the heads' baseline; caption-to-rule gap.
- **tally:** pills right-aligned at one size; quote 54–60pt.
- **interface:**
  - data label below the number, bar labelled 12 / 40;
  - quote tail at ≥ 1.5:1;
  - 4-item points keep heads ≥ 20pt;
  - an empty window bar is dropped.
- **wayfinding:**
  - quote draws `line=`;
  - board rows 2+ bold at ≥ 26pt;
  - route labels left-aligned.
- **chalkboard:** quote underline from the measured ink.

### Task 6: Smallest tier (F10) + conformance check

- [ ] Kicker, attribution, chip, caption and label ≥ 12pt, and running head and folio ≥ 10pt, on the 13.333in canvas, scaled by the canvas factor, all at ≥ 4.5:1. The floor is calibrated on the measured current values; the user can raise it on the sheet.
- [ ] Raise the manifests' type sizes where they fall below.
- [ ] The check runs in `vl_conformance`.

### Task 7: Distinctiveness (F11) + conformance check

- [ ] **Check:** per pair of grounds, ΔE(ground) + ΔE(accent) + face penalty ≥ T, with T calibrated so it flags editorial/ink and passes approved pairs.
- [ ] **🔴 The user picks:** for editorial vs ink, which language moves and how. Offered as rendered options: ink's cinnabar 朱砂 accent and warmer xuan paper; or editorial's ink-black and brick; or keep them alike with a recorded waiver. Same for tally-night vs interface-dark.

### Task 8: 🔴 Before/after sheets → the user's gate

- [ ] For each changed language, render a sheet: every page, before (p2b) | after, plus the 3-word and 60-word quotes and the long title.
- [ ] Deliver to `~/Desktop/slide-maker-phase3/`.
- [ ] Ask (AskUserQuestion) per language: approve / revise / revert.
- [ ] Re-render the samples (`assets/vl/samples/*.jpg`, with fingerprints) only for approved languages.

### Task 9: Verify and review

- [ ] Full local CI + the Linux sim.
- [ ] One Sonnet whole-branch review.
- [ ] One RED→GREEN fix pass.
- [ ] Rulings and deferred minors to the user.
- [ ] The finishing menu.
