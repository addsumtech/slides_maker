# P3 — Four native visual languages (ink · poster · cutpaper · blueprint): design

Date: 2026-10-05 · Status: approved in conversation (look and offer rule), awaiting written-spec review
Builds on: P2 (`scripts/visual_languages.py`: four image-led languages, `Kit`, `_flow`, grounds, samples,
`check_visual_language.py`, the direction-gate `images` rule) and P0/P1 primitives.
Look-dev: 28 rendered sample pages the user reviewed and approved, on the maintainer's Desktop
(`slide-maker 新设计语言 样张/`), built by a throwaway script; this spec turns that look into the kit.

## Why

All four existing visual languages are image-led: a deck with no pictures and no image tool cannot use them,
and that is most research, business and teaching decks. Of the 48 skillry.dev presentation styles, the families
not yet covered and buildable without pictures are: ink-wash landscape, type-as-image poster, layered cut paper,
and the technical drawing sheet. The 18 presets already carry palettes for `ink_wash` and `blueprint`, but a
preset is palette + fonts + flat ground and owns no page composition.

## Decisions (made with the user)

| # | Question | Decision |
|---|---|---|
| 1 | Which languages | `ink` (水墨), `poster` (海报大字), `cutpaper` (剪纸层叠), `blueprint` (蓝图技术线稿) |
| 2 | When they are offered | Whenever a direction gate runs, at least one visual language is a candidate: with pictures, one of the four image-led languages (the existing rule); with none, the native language that fits the topic best, with the reason recorded. Both runtimes hold it; a named `waived` is the escape. |
| 3 | The look | As in the approved look-dev (§2), "high-end with one surprise per language". |
| 4 | Process | Spec → plan → implement → verify → push. |

## Verified facts this design rests on (2026-10-05, this Mac, LibreOffice render)

- `bodyPr vert="eaVert"` sets CJK upright and top-to-bottom; Songti SC, Kaiti SC, Hiragino Sans GB render.
  SimSun is not installed here (Windows default; substituted, not render-verified).
- A soft `a:outerShdw` (blur) and a vertical transparency `a:gradFill` (alpha stops) render.
- **PowerPoint repaired the look-dev file** where LibreOffice rendered it: an `outerShdw dir` of -5400000 (a
  negative angle) is invalid OOXML. LibreOffice tolerates it; PowerPoint deletes the element and warns.
- **PowerPoint's editing view shows geometry past the slide edge**; LibreOffice and slideshow clip it. Bleeds
  drawn past the page read as "content spilling off the slide" to the user.
- Georgia sets old-style figures (user feedback: never for numbers); Times New Roman is the lining serif on
  both platforms.

## 1. Architecture

- The four languages join `LANGS` / `VARIANTS` / `TYPE` / `LAYOUTS` in `visual_languages.py` and use the same
  `Kit`, `use()`, `direction()`, `build_sample()`, `--gates`, grounds and `ground="auto"`. A deck picks them
  exactly as it picks `collage`.
- Each language adds an **art layer**: native, editable shapes drawn under or around the text, produced by a
  new module **`scripts/native_art.py`** (one function per motif, all deterministic for a seed):
  `ink_ridges`, `seal`, `enso`, `paper_hills`, `paper_disc`, `paper_sheet_stack`, `drawing_sheet`
  (border, zone marks, title block), `iso_stack`, `dimension_line`, `leader`, `clipped_block`. Every function
  returns its shapes, tags them with `+vl.<name>` through the shared name composer, and declares decorative
  marks with `dk.decorative`.
- `visual_languages.py` stays the one entry point; to keep it readable, each new language's page compositions
  live in `scripts/vl_native.py` (registered into `LAYOUTS`/page dispatch), not in a second public API.
- **Untouched:** the four image-led languages, the 18 presets, the bespoke kits, every deck that does not pick a
  native language. New modules import lazily.

## 2. The four languages

All text inks pass 4.5:1 on their ground (3:1 for display sizes), checked in a test per ground. Fonts are
system faces present on both macOS and Windows unless `fonts="mac"`; the Windows column is Microsoft's documented
default list and marked unverified (it cannot be rendered here).

1. **ink 水墨** — xuan-paper ground with fibre grain; ink black, one seal vermilion.
   - Type: Songti SC / SimSun (CJK), Georgia (Latin text), Times New Roman (figures). Kai only when asked
     (`ea_display="kai"`; Kaiti SC is an on-demand macOS download, KaiTi ships with Windows).
   - Surface: 2–4 ink ridges fading from crest to mist (transparency gradient), a red sun on the light ground
     and a pale moon on the contrast ground.
   - Surprise: **vertical CJK** (title, quote couplet, points as right-to-left columns), a hand-carved seal
     carrying 1–2 characters taken **from the caller's own text** (`seal=` argument; never invented — without it
     the page carries no seal), and the
     data page's number held by an open **ensō** brush circle.
   - Vertical setting is used only when the field is CJK (Han/kana); Latin, Hangul or mixed text with digits is
     set horizontally in the same composition.
   - Grounds: `light` xuan paper · `night` ink-black paper (pale ridges, moon).
2. **poster 海报大字** — the headline is the picture.
   - Type: Impact (display), Arial (body), Courier New (meta); CJK display in the heavy sans (Hiragino Sans GB /
     Microsoft YaHei Bold). Latin display is set in capitals; CJK is not transformed.
   - Surface: one saturated field per page, cycling cobalt → lime → black → signal orange; geometric blocks
     **clipped to the page**.
   - Surprise: an optional highlighted word (`highlight=` — must be a substring of the caller's title; the kit
     never chooses it), points as a rising staircase of panels, a figure that fills half the page.
   - Grounds: `light` (the colour fields) · `paper` (off-white fields, black type, one accent).
3. **cutpaper 剪纸层叠** — a paper diorama.
   - Type: Trebuchet MS; CJK sans.
   - Surface: layered paper hills, sun (or moon) and clouds, each with a soft paper shadow.
   - Surprise: the title card is **tucked between hill layers** (the near hill covers its foot), the quote sits on
     a stack of offset sheets, the figure sits on a layered paper sun.
   - Grounds: `light` day · `night` navy sky.
4. **blueprint 蓝图技术线稿** — every page a drawing sheet.
   - Type: Georgia (titles), Courier New (labels, title block), Times New Roman (figures).
   - Surface: a fine grid (one background image per canvas size), border, zone letters and numbers, and a title
     block whose fields are the sheet number and the caller's own words (`project=`, else the cover title the kit
     remembers, else the sheet number alone); never invented names, scales or dates.
   - Surprise: on the points page an **iso stack with one layer per point** and numbered leaders to each point;
     on the data page a dimension line spanning the figure; on the quote page the caller's optional image or no
     drawing at all.
   - Grounds: `light` drafting vellum · `cyanotype` navy.

**Meaning rule (the user's standing feedback):** a language's surface (ridges, hills, colour fields, the drawing
sheet) is its ground, like grain. A figure that implies structure — an iso stack, numbered leaders, a dimension
line — is drawn only from the page's content (one layer per point, the figure being dimensioned). The cover never
carries a generic diagram.

## 3. Pages

The six existing pages (`cover`, `section`, `image_text`, `quote`, `data`, `closing`) in landscape and portrait
for each language, plus a new **`points`** page for the four native languages: `kicker`, `title`, `items` (2–4
items of `head` + optional `line`), optional `icons=` (icon spec names, cutpaper) — because `image_text`
requires an image and a no-picture deck needs a content page. `points` on an image-led language raises with a
pointer to ordinary `k.new_slide()` pages. `image=` stays optional everywhere except `image_text`.

Text keeps P2's contract: flowed by measured height, shrunk toward per-field floors, refused (never truncated)
when it cannot fit, no widows. Vertical CJK is measured as columns: the column length is characters × (size +
letter spacing); a field that needs more than its allowed columns at the floor size is refused the same way.

## 4. PowerPoint safety (applies to every deck, not only these languages)

- **`scripts/ooxml_safety.py`** — reads a saved `.pptx` and reports values PowerPoint rejects or repairs:
  angles outside 0–21600000 (`dir`, `rot`, `ang`), negative `blurRad`/`dist`, `gs pos` and alpha outside
  0–100000, letter spacing outside ±400000, duplicate shape ids on a slide, and `spPr`/`rPr` children out of
  schema order. A finding is CRITICAL. `lint_deck` runs it, so both delivery gates hold it; it is cheap (one XML
  pass per slide).
- **Nothing drawn past the page.** Native art is clipped by construction (`clip_to_page`), and a test asserts
  every shape of every sample page lies inside the canvas. A new advisory lint `BEYOND THE PAGE` reports any
  undeclared non-text shape that extends past the slide (PowerPoint shows it while editing); `bleed_intent`
  declarations keep it quiet.
- `native_art` normalises every angle it writes into range.

## 5. The offer rule (direction gate, both runtimes)

- `directions_diversity.images_fault` (P2) keeps its meaning for pictures. A new `native_fault(images,
  directions, fit=None)`: when `images` is `none`, at least one candidate must be a native language, and the
  record carries **`direction_gate.native_fit`**: `{"language": "<name>", "why": "<the topic reason>"}`.
- Guidance for the pick (an offer, not a rule): culture / history / craft → ink; launch / manifesto / brand /
  opinion → poster; children / teaching / workshop / community → cutpaper; research / engineering / technical →
  blueprint.
- Held by `render_deck.py --gate-check` and `codex_delivery_gate.py` through the same function; the set's named
  `waived` escapes it. `references/interview-protocol.md`, `references/codex-runtime.md` and SKILL.md state it.

## 6. Generality and verification

- Every page × language × orientation × ground built in tests with English, Chinese, Japanese and Korean copy,
  short and long; overflow refusal tested; vertical text only for CJK.
- Canvases: 16:9, 4:3 and a portrait poster (the `formats` registry); art scales with the canvas.
- Contrast: every text ink on every ground and panel; the poster highlight goes through `dk.mark`'s WCAG check.
- `ooxml_safety` and the inside-the-page assertion run on every sample deck in CI; the bundled samples are rendered
  and looked at (sheets in the PR description), not only linted.
- Non-Claude: `references/visual-languages.md` documents the four languages, `points`, `seal=`, `highlight=`,
  `project=` and vertical text; `sigs.py --example` has a runnable call per new function (smoke-executed); a
  subagent restricted to SKILL.md + references + `sigs.py` builds a deck in each language and reports friction.
- Performance: decks that do not use a native language import nothing new; the grid background is generated once
  per canvas size and cached; the full suite time does not grow by more than the new tests' own run time.
- Bundled samples: `assets/vl/samples/<name>[-<ground>].jpg` (≤ 350 KB each, JPG — SkillHub filters PNG), built by
  `--sample` with sample copy labelled "style sample — not your content".

## Out of scope

- Generated imagery series for the native languages (they accept a picture, they do not commission one).
- A `points` page for the four image-led languages.
- Further languages (night-cinematic and others) — a later round.
