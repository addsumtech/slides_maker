# P4 — Five more native visual languages (starlit · broadsheet · journal · tally · chalkboard): design

Date: 2026-10-08 · Status: look approved by the user (gallery, 40 pages), awaiting written-spec review
Builds on: P3 (`docs/superpowers/specs/2026-10-05-native-visual-languages-design.md`): `NATIVE`, `vl_native.py`
composers + `register(lang, page, alts=)`, `native_art.py`, `NATIVE_EXTRAS` / `EXTRA_PAGES`, `ooxml_safety.py`,
the direction gate's `native_fit`, the bundled samples + fingerprints.
Look-dev: `~/Desktop/slide-maker 新模板样张/` (index.html, 10 pptx, 40 pages: cover · points · quote · data per
language, two grounds, English and Chinese), built by a throwaway script (session scratchpad `lookdev3/lookdev3.py`).
This spec turns that look into the kit.

## Why

The user asked for more templates, and specifically for NEW ones, borrowed from somewhere rather than reworked
from what exists ("更多的是可否进一步思考或者借鉴出新的模版"). Each of the five borrows a real-world visual
convention that a no-picture deck can carry natively. Each also fills a purpose the nine languages leave open:

| Language | 中文 | Borrowed from | Purpose it fills |
|---|---|---|---|
| `starlit` | 星夜 | the night sky + the year-end letter | year in review, letters, thanks, commemoration, evening keynotes |
| `broadsheet` | 报纸头版 | the newspaper front page | newsletters, weekly/monthly reports, "what happened" updates |
| `journal` | 学术期刊 | the journal article layout | lab meetings, paper talks, defences, technical reviews |
| `tally` | 数据账本 | data dashboards / fintech reports | quarterly reviews, metrics, operations and growth reports |
| `chalkboard` | 黑板报 | the classroom blackboard | lessons, explainers, training, workshops |

## Decisions (made with the user)

| # | Question | Decision |
|---|---|---|
| 1 | Direction | New templates borrowed from outside, not reworking existing pages; the content-page work (agenda / compare / timeline) is parked. |
| 2 | Which | 星夜, 报纸头版, 学术期刊 (recommended set) + 数据账本, 黑板报. Not chosen: transit map, topographic, palace red. |
| 3 | The look | As in the approved gallery, with the corrections listed under "Changes from the look-dev". |
| 4 | Process | Spec → plan → implement → verify → push only when the user says so. |

## Naming (decided here; review point)

- **`tally`, not `ledger`.** `ledger` is already a bespoke surface kit (`bespoke_kits.py`; registered in
  `register_surface.GROUNDS`/`CARDS`). `register_surface.register()` refuses a preset's name but **silently replaces**
  an existing kit's, so a language called `ledger` would have overwritten the bespoke kit for every deck. The
  Chinese label stays 数据账本.
- The other four names collide with no registered name (presets, surface kits, languages), checked on 2026-10-08.
  As plain words: `journal` appears in the `journal_club` purpose and the citation fields, and "Chalkboard /
  blackboard" in `references/generated-template.md`, where it describes an image-generated template register.
  That reference gains a pointer to the native `chalkboard`, so an agent that reads it finds the no-picture option.
- **Guard (new, general):** `register()` refuses a name that is already registered from a different `source`. A
  re-registration from the same file is still allowed, so module reloads keep working. A test pins both cases.

## Verified facts this design rests on (2026-10-08, this Mac, LibreOffice render of the look-dev)

- **Radial gradient rim.** With `a:path path="circle"`, the gradient's 100% stop sits at the bounding box's
  corner, not at the disc edge. A fade that ends at 100% leaves a visible rim at about 71%. A fade that is clear
  by 68% shows no rim. On an ellipse, LibreOffice draws the same fill as a soft, roughly rectangular patch.
  PowerPoint's drawing of it is not render-verified here.
- **No drop cap in OOXML.** A two-box fake (a big initial in one box, the paragraph beside it) only works if the
  renderer breaks lines where the measure predicted, and renderers differ. In the look-dev it overlapped: the "W"
  of "What" ran into the next letter. **An in-flow raised initial** (a larger first run in the same paragraph)
  rendered cleanly.
- **Chalkboard SE is macOS-only.** Trebuchet MS ships on macOS and Windows.
- **Arial Black has no CJK glyphs.** CJK in the tally display role falls back to the bold East-Asian sans.
- **Literal spaces between CJK and Latin.** LibreOffice adds its own CJK–Latin spacing on top of them, so text
  like "心脏 MRI 的" set at 46pt showed a double-width gap. Without the spaces, the gap was normal.
- CJK display lines broke mid-word ("修/东西", "指/导", a lone "碳") until the line break was moved to a clause
  mark. P3's `display()` / `_clauses` already does this, and these languages must route all text through it.

## 1. Architecture

- The five names join `LANGS` / `VARIANTS` / `TYPE` and `NATIVE` in `visual_languages.py`. Their compositions are
  registered in `vl_native.py` with `@register(lang, page, alts=N)`, exactly like P3. Nothing new is added to the
  public API: `use(name, prs, ground=…)`, `Kit.<page>()`, `k.new_slide()`, `rs.ground(s, k.name)`,
  `build_sample`, `direction`, `--gates`.
- **New motifs go into `native_art.py`.** Each is one function, deterministic for a seed, clipped to the page,
  and marks its decorative shapes with `dk.decorative`:
  - `starfield_png`: a background picture, cached per canvas + seed + keep-clear zones. It is not 150 shapes per
    page, because the file size and the lint passes grow with the shape count.
  - `crescent`, `radial_glow` (the rim-free fade above), `horizon_glow`.
  - `chalk_path` (jittered, two passes), `chalk_box`, `chalk_ellipse`, `chalk_underline`, `chalk_arrow`,
    `board_frame` (the wooden frame inside the page, the ledge and a chalk stick).
  - `chip` (a pill whose width is measured per script), `share_bar`, `masthead_strip`.
- `vl_native.py` grows by five sections, one per language. If it passes ~2,500 lines, the new languages move to
  `vl_native2.py`, registered through the same `register`. That is a mechanical split decided at plan time.
- **Untouched:** the nine existing languages, the 18 presets and the bespoke kits. A deck that does not pick a
  new language imports nothing new.

## 2. The five languages

All text inks pass 4.5:1 on their ground and their panel (3:1 for display sizes), tested per ground. The `both`
fonts exist on macOS and Windows; `fonts="mac"` may use Mac-only faces. Digits always use a lining face
(`Kit.runs` already splits digits out of Georgia).

1. **starlit 星夜.** Midnight-blue sky, faint stars, a crescent moon, gold serif.
   - Type: Georgia (display, body), Times New Roman (figures); CJK serif.
   - Surface: the starfield picture, kept clear of text; 4-point sparkles; a crescent moon (gold, or rose on dawn).
   - Signature: **the points page is a constellation.** Each of 2–4 points is a star with a glow, and one gold
     line joins them. The data page's number sits in a glow above a warm horizon.
   - Grounds: `light` = **midnight** (0B1430) · `dawn` (22163A). Both are dark. See §5 for print.
2. **broadsheet 报纸头版.** Newsprint, a masthead, columns.
   - Type: Times New Roman bold (headlines, figures), Georgia (body, standfirst), Arial bold caps (meta); CJK serif.
   - Surface: paper grain, and on every page a masthead strip (name, double rule, edition, page number).
   - Signature: a **headline cover** with a standfirst; **points as newspaper columns**, each opening with an
     in-flow raised initial (Latin only; CJK is not enlarged); a pull quote between a heavy rule and a hairline;
     the data number in a boxed panel.
   - Grounds: `light` newsprint (F2EEE5, red accent) · `salmon` (FBE8D8, navy accent).
3. **journal 学术期刊.** An article page.
   - Type: Georgia (display, body), Times New Roman (figures), Arial bold caps (labels); CJK serif.
   - Surface: a running head (short title left, page number right, hairline) on every page except the cover; a
     left accent bar on the cover.
   - Signature: an **abstract block** on the cover; the **figure page** (`image_text`): figure label, title,
     caption, and a source line under a rule; numbered points with an optional margin note; the data number centred
     in a tinted panel.
   - Grounds: `light` paper (FBFAF6, green accent) · `green` (163A2E, gold accent).
4. **tally 数据账本.** A grid, heavy type, chips, one giant number.
   - Type: Arial Black (display, figures), Arial (body); CJK bold sans.
   - Surface: a fine grid (P3's cached `grid_background`).
   - Signature: **points as ledger rows** (`01` / `02` in blue, head + line, an optional tag chip, rules between
     rows and a closing rule); the data page's **giant number with a share bar** when the caller gives a total.
   - Grounds: `light` white grid (FFFFFF, cobalt 2438F0, lime C6F432) · `night` (0F1222).
5. **chalkboard 黑板报.** A board in a wooden frame, coloured chalk.
   - Type: Trebuchet MS (both), Chalkboard SE under `fonts="mac"`; CJK sans.
   - Surface: board grain, rim-free eraser smudges kept away from text, a wooden frame drawn inside the page, and
     a chalk stick on the ledge.
   - Signature: every line is a jittered chalk stroke (editable paths). Points are chalk boxes with circled
     numbers, sized to their measured words. The data number is circled in chalk, with an arrow to its label.
   - Grounds: `light` = **green board** (22392B) · `slate` (25282C). Both are dark. See §5.

**Meaning rule (carried from P3, the user's standing feedback).**
- A language's surface is its ground: stars, the masthead strip, the running head, the grid, the board.
- A figure that implies structure is drawn only from content: a constellation with one star per point, ledger
  rows, numbered chalk boxes.
- Chalk arrows between boxes would claim the points happen in order, so they appear only when the caller says so
  (`ordered=True`).
- The cover never carries a topic drawing the kit chose. The chalkboard cover draws one only from the caller's
  `doodle=`.

## 3. Pages

All seven pages for each language: `cover`, `section`, `image_text`, `quote`, `data`, `closing`, `points`. Each
comes in landscape and portrait, and in both grounds. The look-dev showed four of them. The other three, in the
same language:

| | section | image_text | closing |
|---|---|---|---|
| starlit | number in gold inside a small glow, kicker, title | the picture in a round window with a gold ring; text beside it | title + line under the moon, horizon glow |
| broadsheet | a section front: number in a black tab, heavy rule, title as headline | the picture as a news photo, caption under a rule; headline + body column | last headline + line, ending with a ■ end-of-article mark |
| journal | "§ {number}" in the accent, title, rule | the figure page (above) | title + line with the running head |
| tally | giant blue number, chip kicker, title | picture in a rounded card with a hairline; chip kicker, title, body | title + line, blue bar |
| chalkboard | number circled in chalk, title, double underline | picture held by four chalk corner marks; text beside it | title + underline, optional doodle |

**Portrait.** Compositions are computed from the canvas and from measured text, not from fixed inches, and each
page has an alternative layout to try before it refuses (P3's `alts`).
- Constellation: a vertical zig-zag.
- Broadsheet columns: stacked.
- Tally rows: unchanged.
- Chalk boxes: a vertical stack, with down-arrows when `ordered`.

**Text contract (P3, unchanged).**
- Text is flowed by measured height and shrunk toward per-field floors. When it cannot fit, it is refused with
  `VLTextOverflow`, never truncated. No widows.
- CJK breaks only at clause marks, or between words for unbreakable runs, via `display()`.
- Latin quotes use the balanced measure (`_balanced_width`).
- Vertical setting is not used by any of the five.

## 4. Words only the caller can give (`NATIVE_EXTRAS`)

Nothing below is ever invented. If an extra is absent, nothing is drawn. An extra passed on a page that does not
draw it is refused with the list of pages that do (P3's `EXTRA_PAGES` rule).

| Language | Extra | Pages | Meaning / fallback |
|---|---|---|---|
| broadsheet | `masthead=` | any; remembered for the deck | publication name. Falls back to the cover's kicker, then to the rules + page strip with no name. |
| broadsheet | `edition=` | any; remembered | left of the strip (e.g. the caller's date or issue). No fallback; the kit never invents a date or number. |
| broadsheet | `inside=` | cover | list of 1–4 short lines for the "Inside" sidebar. Absent: the standfirst takes the full width. |
| broadsheet, tally | `tags=` | points | one short label per point (column label / row chip). Must match the item count, else it is refused. |
| journal | `running=` | any; remembered | the running-head text. Falls back to the cover title on one line at its floor, else page number only. |
| journal | `authors=` | cover | author line. |
| journal | `abstract=` | cover | the abstract block. The kit never labels the subtitle "Abstract"; a subtitle is not an abstract. |
| journal | `margin=` | points | margin note. |
| tally | `total=` | data | a number ≥ the page's number. Draws the share bar with both numbers at its ends. A non-numeric or smaller value is refused. |
| chalkboard | `doodle=` | cover, closing | one icon spec (P1 icons), drawn in a chalk colour. |
| chalkboard | `ordered=` | points | `True` draws arrows between boxes. |

**Derived, not invented:**
- page numbers (slide index);
- journal figure numbers: "Figure n / 图 n / 図 n / 그림 n", counted over image_text pages, unless the caller's
  `kicker` is given;
- the broadsheet ■ end mark;
- localised structural labels ("Abstract / 摘要 / 要旨 / 초록", "Inside / 本期 / 今号 / 이번 호").

The Japanese and Korean labels are confirmed with a native-reading reference during implementation, not written
from memory.

## 5. Offer guidance and grounds

- The direction gate's `native_fault` already requires one native candidate and a `native_fit` record when there
  are no pictures. Extending `NATIVE` extends it on both runtimes with no new rule.
- The guidance (an offer, not a rule) is updated in `references/visual-languages.md`, `interview-protocol.md`
  and `codex-runtime.md`, and so are the `directions_diversity` messages that cite it:
  - culture, history, craft → ink
  - launch, manifesto, opinion → poster
  - children, storytelling, community → cutpaper
  - engineering, architecture, systems design → drafting
  - **year in review, letter, thanks, commemoration → starlit**
  - **newsletter, periodic report, community update → broadsheet**
  - **research talk, lab meeting, paper, defence → journal**
  - **metrics, quarterly review, operations, growth → tally**
  - **lesson, class, training, explainer → chalkboard**
- This splits two old entries. "Research / technical" now goes to journal for papers and to drafting for
  engineering. "Teaching" now goes to chalkboard for lessons and to cutpaper for children's stories.
- **Dark default grounds.** In starlit and chalkboard the `light` key is the language's default ground, and it is
  dark. `ground="auto"` keeps the register-pixels repeat logic. When it is asked for a printed board in either
  language, it returns the default ground with a `why` that says the language has no light ground and suggests
  another language for print. It warns rather than refuses.

## 6. Changes from the look-dev (decided while reviewing it)

- **Removed "— 30 —".** It is a journalism end mark that most viewers cannot decode in a second (frame-element
  decodability). Broadsheet's closing page ends with ■ instead, and the data page carries no end mark.
- **The broadsheet strip's "NO. 01 / THE CITY EDITION" was sample copy.** In the kit the strip carries only
  `edition=` and the page number. The "BY THE NUMBERS" header becomes a solid band with no words.
- **Sample copy is not drawn as content.** The look-dev's column labels, row chips, author line, abstract,
  margin note and share-bar end labels were sample copy. In the kit they come from `tags=`, `authors=`,
  `abstract=`, `margin=` and `total=`.
- **The chalkboard cover's sun was the sample topic's own drawing.** In the kit only `doodle=` draws on the cover.

## 7. Generality and verification

- Tests reuse P3's parametrised suites (`test_native_languages.py`, `test_native_generality.py`) by extending
  `NATIVE`. Every page × language × orientation × ground is built with English, Chinese, Japanese and Korean copy,
  short and long. The tests cover refusal (overflow, bad extras, `tags=` count, `total=` < number) and the
  fallbacks of every remembered extra.
- **Canvases:** 16:9, 4:3, square and portrait from the `formats` registry. Art scales with the canvas.
- **Contrast:** every text ink on every ground, panel, chip and box.
- **Geometry and safety:** `ooxml_safety` (0 findings) and the inside-the-page assertion run on every sample and
  corpus deck.
- **Generality corpus:** P3's corpus runner is extended to the five languages. Every refusal in it must be a real
  overflow, not a measuring error.
- **Linux font simulation (cisim):** run, with the three known artifacts unchanged.
- **Rendered and looked at:** sheets of every page, both grounds, landscape and portrait, are viewed by me before
  any claim of done, then shown to the user.
- **Non-Claude use:** `references/visual-languages.md` documents the five languages, every extra, the offer
  guidance and a call per page. `sigs.py --example` gains a runnable call per new `native_art` function
  (smoke-executed). A subagent limited to SKILL.md, the references and `sigs.py` builds one deck per language, and
  its friction report is fixed.
- **Samples:** `assets/vl/samples/<name>[-<ground>].jpg`, 10 new JPGs at ≤ 350 KB each, recorded in
  `manifest.json` with fingerprints. Sample copy is labelled "style sample — not your content". Journal's figure
  sample is a bundled illustrative plot stamped "illustrative".
- **Performance:** decks that use none of the five import nothing new, and the starfield and grid pictures are
  cached. The full suite should grow by no more than the new tests' own run time.

## Out of scope

- The parked content-page work (agenda / compare / timeline for the existing languages).
- Scenario templates (场景模板): the next sub-project.
- Generated imagery for these languages. They accept a picture; they do not commission one.
- Vertical CJK setting for any of the five.
