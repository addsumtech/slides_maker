# Visual languages — <!-- vl:count-all -->thirty<!-- /vl --> complete looks: <!-- vl:count-image -->four<!-- /vl --> image-led, <!-- vl:count-drawn -->twenty-six<!-- /vl --> drawn

**When to read this:** the picked direction is a visual language (its entry in `directions.json` carries
`"vl": "<name>"`), or the user asks for one of these looks by name. Read it before writing the build script.
One language at a glance — its grounds, pages, extras, derived words and an example that runs as printed:
`python3 "$SKILL/scripts/visual_languages.py" --describe <name>`. To ADD a language, read
`references/visual-language-authoring.md` instead.

**The skill folder, named once.** `SKILL` is the folder that holds `SKILL.md` (the path this skill was loaded
from, e.g. `~/.claude/skills/slide-maker`). Every command in this file is written `python3 "$SKILL/scripts/…"` and
runs from any working directory once you set it; a build script reads the same variable:

```bash
export SKILL="/absolute/path/to/slide-maker"         # the folder with SKILL.md in it
python3 "$SKILL/scripts/visual_languages.py" --list   # check: one line per language
```

## Build a visual-language deck, in order

Every command below was run, in this order, from a fresh folder outside the skill, on two decks: `editorial` with
the bundled photos and `tally` drawn (2026-10-09). `DECK` is the deck's folder, as an absolute path. The record is
the shared runtime's `$DECK/.deck-gates.json`; on the Codex runtime the same values go into
`.codex-deck-evidence.json` under `design` (`references/codex-runtime.md`).

1. **Pick the canvas.** `python3 "$SKILL/scripts/formats.py"` prints every canvas. In the build script,
   `formats.blank_deck("<name or alias>")` makes the deck; `formats.get()` resolves these names (any case):

   | name | aliases | size (in) |
   |---|---|---|
   | `wide` | `16:9` `16x9` `ppt` `landscape` `widescreen` `default` | 10 × 5.625 |
   | `wide13` | `13.33x7.5` `13.333x7.5` `powerpoint` `16:9-13` `widescreen-13` | 13.333 × 7.5 |
   | `classic` | `4:3` `4x3` `standard` | 10 × 7.5 |
   | `square` | `1:1` `1x1` `instagram` `ins` `facebook` `post` | 7.5 × 7.5 |
   | `red` | `3:4` `3x4` `xiaohongshu` `小红书` `rednote` `portrait` | 7.5 × 10 |
   | `story` | `9:16` `9x16` `vertical` `reels` `shorts` `douyin` `抖音` `tiktok` | 5.625 × 10 |
   | `a4` | `print` `a4-portrait` `handout` `onepager` `one-pager` | 8.27 × 11.69 |
   | `poster_a0` | `a0` `poster` `a0-portrait` `conference-poster` `海报` | 33.11 × 46.81 |
   | `poster_a1` | `a1` `a1-portrait` `poster-a1` | 23.39 × 33.11 |
   | `poster_a0_land` | `a0-landscape` `a0l` `poster-a0-landscape` `横版海报` | 46.81 × 33.11 |
   | `poster_a1_land` | `a1-landscape` `a1l` `poster-a1-landscape` | 33.11 × 23.39 |

   `"16:9"` resolves to `wide`, the **10 in** canvas. The examples in this file use 13.333 × 7.5, which is
   `wide13` (`dk.blank_deck(13.333, 7.5)` is the same canvas), and so do `sigs.py --example` scaffolds — a
   scaffold placed with `--in <language>` fits any canvas; one printed without `--in` keeps literal 13.333in
   coordinates. `"portrait"` is the 3:4 `red` canvas. **One deck per folder:** `render/` beside a deck is that
   deck's; `render_deck.py` refuses to render a second deck over it — give each deck a folder of its own.
   A4 and the posters are printed boards.
2. **Interview, then make the record.** Ask the questions of SKILL.md Step 0 (on Codex, `references/codex-runtime.md`
   step 1). Then:
   ```bash
   python3 "$SKILL/scripts/deck_gates.py" init "$DECK" --slides 5
   python3 "$SKILL/scripts/deck_gates.py" interview "$DECK" --set language=en --set density=balanced --set length="5 slides" --set goal="invite neighbours to a repair evening"
   ```
   - `init` writes `$DECK/.deck-gates.json`, every value a placeholder; `--slides` is the planned slide count.
   - If the record already exists, `init` exits 2 and changes nothing. Keep it and go on with `set`; `--force`
     overwrites it and discards what is recorded.
   - Either order works: on a folder with no record, `interview --set` writes one holding only the interview, and
     `init` then builds the full skeleton around those answers (it refuses only a record holding more than that).
   - Give `length` in words (`"5 slides"`): a one-character answer such as `5` is refused at hand-off.
3. **Write the build script** `$DECK/build_repair-cafe.py` with `vl.use` and one page function per slide, each in its own
   `def slide_NN(prs, k):` (the Codex gate reads the calls inside each `def`). Name it `build_<deck stem>.py` — the
   STYLE APPLIED check looks for exactly that name beside the deck. A deck that is READ rather than presented says so
   from the script: `dk.declare_delivery(HERE, "selfread")` (`presented` — the default — `textheavy`, `selfread`,
   `surface`); the lint's budgets follow it. The `editorial` test deck:
   ```python
   import os
   import sys
   from pathlib import Path

   SKILL = os.environ["SKILL"]                     # the folder that holds SKILL.md
   sys.path.insert(0, os.path.join(SKILL, "scripts"))
   import deckkit as dk
   import formats
   import visual_languages as vl

   HERE = Path(__file__).resolve().parent
   PHOTO = Path(SKILL) / "assets" / "vl" / "photo"  # bundled sample photos; a real deck uses the user's own


   def slide_01(prs, k):
       k.cover(k.new_slide(), kicker="A repair café", title="Bring it broken, take it home working",
               subtitle="Once a month, in the church hall", image=str(PHOTO / "hall-repair.jpg"))


   def slide_02(prs, k):
       k.section(k.new_slide(), number="01", kicker="How it works", title="We fix it with you")


   def slide_03(prs, k):
       k.image_text(k.new_slide(), kicker="What you find", title="Tools on every bench",
                    body="Volunteers bring the tools; you bring the broken thing and stay while it is fixed.",
                    image=str(PHOTO / "tools-tray.jpg"))


   def slide_04(prs, k):
       k.quote(k.new_slide(), quote="I came with a dead toaster and left knowing how it works.",
               attribution="A visitor")


   def slide_05(prs, k):
       k.closing(k.new_slide(), title="Bring one broken thing.", line="And bring a neighbour.",
                 image=str(PHOTO / "table-mended.jpg"))


   def main():
       prs = formats.blank_deck("16:9")             # "16:9" is the 10 x 5.625 in canvas
       k = vl.use("editorial", prs, ground="auto")
       for build in (slide_01, slide_02, slide_03, slide_04, slide_05):
           build(prs, k)
       prs.save(str(HERE / "repair-cafe.pptx"))
       print("saved", HERE / "repair-cafe.pptx")


   if __name__ == "__main__":
       main()
   ```
   The `tally` test deck was the same shape, with `formats.blank_deck("wide13")`, an ordinary agenda page (see
   **Ordinary pages** below), `points` with `tags=` and `data` with `total=`. More scaffolds:
   `python3 "$SKILL/scripts/sigs.py" --example vl_drawn vl_tally vl_broadsheet vl_journal vl_chalkboard vl_interface vl_wayfinding vl_herbarium vl_airmail vl_vinyl vl_receipt vl_comic vl_pixel vl_bricks vl_boardgame vl_circuit vl_topo
   vl_scoreboard vl_periodic vl_recipe vl_stainedglass vl_calendar rs.ground`.
4. **Build:** `python3 "$DECK/build_repair-cafe.py"`. With `ground="auto"` it prints the ground it chose and a
   `--gates` line with two `<…>` blanks. That line is a template: fill both blanks, because it will not run as printed.
5. **Record the language.** Pass the ground the build printed (on the test machine `ink`, because its last decks
   sat on light paper; yours may print `light`), or `auto`, which reads the one `.pptx` in `$DECK`:
   ```bash
   python3 "$SKILL/scripts/visual_languages.py" --gates editorial --ground ink --deck "$DECK" --for "a neighbourhood repair café" | tee "$DECK/gates.txt"
   sh "$DECK/gates.txt"
   ```
   It prints six `deck_gates.py set` commands with absolute paths, plus an `init` line when there is no record yet.
   Its `#` lines are comments, so the saved output runs as a shell script. Run it as printed.
6. **Record the plan and the two checkpoints.** While `content.slides` has 4 or more rows (the placeholder rows
   `init` writes count) and `design_plan.checkpoint.mode` is not `approved` or `auto`, a full render refuses with
   `STEP 2 NOT DONE`. `--gate-check` reads both checkpoints (its "checkpoint ledger" line). Write one row per slide
   with its real takeaway, and use `"mode": "auto"` when the user delegated the call. `auto` also asks for
   `interview.picks`: one row per Step-0 axis (angle, audience, purpose, template, language, goal, density, length,
   style, builds) saying who answered it (`stated`, `genre-default`, `inferred-from-request`, `from-material`,
   `not-applicable` or `delegated`, with a `basis` for a delegated one, and an `alternative` for audience, purpose and
   template); `angle` is never `delegated`. The rows `init` writes show the shape; `references/checkpoint-convention.md`
   is the full rule:
   ```bash
   python3 "$SKILL/scripts/deck_gates.py" set "$DECK" content.slides '[{"slide": 1, "role": "cover", "takeaway": "A repair café fixes your broken things with you, once a month.", "evidence": ["the user brief"], "units": 2}, {"slide": 2, "role": "section", "takeaway": "The evening is hands-on: you fix it with a volunteer.", "evidence": ["the user brief"], "units": 1}, {"slide": 3, "role": "evidence", "takeaway": "Every bench has the tools; you bring only the broken thing.", "evidence": ["the user brief"], "units": 2}, {"slide": 4, "role": "quote", "takeaway": "Visitors leave knowing how their thing works.", "evidence": ["a visitor, quoted in the brief"], "units": 1}, {"slide": 5, "role": "close", "takeaway": "Bring one broken thing, and a neighbour.", "evidence": ["the user brief"], "units": 1}]'
   python3 "$SKILL/scripts/deck_gates.py" set "$DECK" content.checkpoint '{"mode": "approved", "record": "the slide table was shown in chat and the user said go"}'
   python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.checkpoint '{"mode": "approved", "record": "the user named the look; the direction and the per-slide pages were shown and approved"}'
   ```
7. **Render, then look at every PNG:** `python3 "$SKILL/scripts/render_deck.py" "$DECK/repair-cafe.pptx"`. The PNGs
   land in `$DECK/render/`.
8. **Lint:** `python3 "$SKILL/scripts/lint_deck.py" "$DECK/repair-cafe.pptx"`. It reads the renders beside the deck.
   Both test decks came back with 0 hard findings and only advisory `[stats]` warnings.
9. **Hand-off gates:** `python3 "$SKILL/scripts/render_deck.py" "$DECK/repair-cafe.pptx" --gate-check`. It lists
   every gate still owed, numbered, and exits 1 until all of them pass. `python3 "$SKILL/scripts/deck_gates.py"
   check "$DECK"` lists every record field that is still a placeholder, all at once.

**Which hand-off gates a user-named visual-language look still owes.** After steps 1–8, `--gate-check` on the
test decks passed `visual language` ("5 of 5 slide(s) built with it"), `register pixels`, `a11y`, `fonts`,
`surface`, `density` and `interview`. It listed the rest, 8 gates on each deck, each with the record it wants (the
count is the FIRST pass: a gate whose record is half-filled can list more faults on the next run —
`deck_gates.py check "$DECK"` lists every unfilled field at once):

- **What the look itself changes.**
  - There was no competition, so record `design_plan.direction_gate` as `"n/a - user supplied the look"`. On Codex,
    also record `design.direction` as `{"branch": "user-named", …}` (step 2u there).
  - `visual_language`, `vl_fonts`, `vl_ground`, `style_pick`, `look_source` and `palette` come from step 5.
  - A GROUND REPEAT is answered by rebuilding on the other ground — or, when the USER named this ground, by
    appending ` — deliberate repeat: the user named the <g> ground` to `design_plan.palette` (it waives the two
    look-history checks only; the declared colours must still be on the pages). `--gates … --ground <g>` prints
    that line. `design_plan.register_pixels_waived` waives the whole pixel check (see **Record and gates**).
- **Everything else applies as on any deck.**
  - `critic`: `{"verdict": "consent" | "revise"}` from the review. A waiver is `{"waived": "<reason>",
    "waived_category": "<category>"}`, and the gate prints the five categories, `user-waived` among them;
    `no-dispatch-on-host` also records `"inline_ran": true|false` (whether you ran the review inline).
  - `design_plan`: the rest of the Step 2 plan — `boldness`, `concept`, `signature_move`, `form_ledger`,
    `icon_family`, `build_shape`, `material_probe`, `signature_proof`, `composition`. `deck_gates.py check` lists
    the missing ones. A `conservative` deck records `composition` as
    `{"waived": "<why>", "waived_category": "conservative"}`; a deck with no picture records `image_sources` as the
    string `"n/a — <why>"` (not a list).
  - `taste` (when this machine's taste ledger has entries): one `design_plan.taste_applied` row per active entry.
    The command the gate prints lists them.
  - `content.arc`: the 2–3 candidate arcs themselves.
  - `content.audience_brief`: 3 or more decisions.
  - `render_selfcheck`: a verdict for every slide, written after looking at it.
  - `blind_read`: answers from a reader who was not shown the record (`blind_read.py`).
  - `provenance`: a verdict on every researched claim (`CONFIRMED` needs the primary-source URL). When every fact on
    the pages is the user's own brief and nothing was researched, record `provenance.waived` with that reason — the
    gate prints it as WAIVED, which is true; marking the user's facts `UNVERIFIABLE` is not.

  The rows marked `NOT CHECKED` (template profile, purpose, talk time, Q&A backup, citations, image series, and a
  direction with no `directions.json`) checked nothing and block nothing.

## The <!-- vl:count-all -->thirty<!-- /vl --> languages

A visual language is a whole look, not a palette: a type voice from system fonts, a surface, image
treatments and seven page compositions (cover, section, image_text, points, quote, data, closing). Picking one gives a finished deck from your own words and images —
the page functions never invent a word, a number or a name.

| language | images | voice | surface | frames |
|---|---|---|---|---|
| `editorial` | photographs, quiet | large serif display, sans body, pull quotes | warm paper, faint grain | bleed photos, rect, arch |
| `soft` | photographs, warm | rounded sans, generous space | cream / pastel, colour blobs | arch, ellipse, blob, rounded cards |
| `collage` | photographs, loud | heavy headlines, highlighter kicker, squiggles | kraft grain | tilted taped prints, note cards, outlined numbers |
| `storybook` | illustrations (a P1 watercolour series) | serif display and body | paper grain | feathered illustrations melting into the paper |
| `ink` | none needed (an ink illustration is optional) | serif; vertical CJK, a carved seal | xuan paper, misty ink ridges | an ensō around the figure |
| `poster` | none needed (a cut-out object is optional) | Impact display — the headline is the picture | one saturated colour field per page | page-clipped colour blocks |
| `cutpaper` | none needed (icons from the built-in library) | rounded friendly sans | a layered paper diorama, soft paper shadows | the title card tucked between hills |
| `drafting` | none needed | Georgia titles, Courier New labels, Times New Roman figures | drafting grid, drawing sheet, title block | an iso stack, numbered leaders, a dimension line |
| `starlit` | none needed (a photo in a round window is optional) | Georgia serif, gold kicker | midnight sky, stars, a crescent moon | points as a constellation; the figure in a glow |
| `broadsheet` | none needed (a news photo is optional) | Times New Roman headlines, Georgia body | newsprint grain, a masthead strip | newspaper columns, a raised initial, a pull quote between rules |
| `journal` | your own figures (placed whole, never cropped) | Georgia, small-caps labels | plain paper, a running head | numbered figures with captions, an abstract, margin notes |
| `tally` | none needed (a photo is optional) | Arial Black display, Arial body | a fine grid | ledger rows, pill tags, a giant number with its share bar |
| `chalkboard` | none needed (a chalk doodle icon is optional) | Trebuchet MS (Chalkboard SE on mac) | a framed board with grain | chalk boxes, circled numbers, arrows only when ordered |
| `interface` | none needed (a screenshot in a device frame is optional) | Arial (Helvetica Neue on mac), bold | the app canvas, windows with a status bar | a settings list, a dashboard card, a chat bubble, a dialog |
| `wayfinding` | none needed (a poster photo is optional) | Arial (Helvetica Neue on mac); the board in Courier New / Menlo | enamel ground, navy station signs | lines and roundels, a strip map when ordered, a departure board |
| `herbarium` | none needed (a specimen photograph is optional) | Georgia (Baskerville on mac); labels in Courier New (American Typewriter on mac) | archival paper, a hairline double frame, plate numbers | pressed sprigs held by paper tape, typed label cards, a specimen tag for the figure |
| `airmail` | none needed (a postcard photo is optional) | Trebuchet MS (Futura on mac); quotes in a letter face | envelope paper inside the red-and-blue striped border | a perforated stamp carrying the number, a postmark, address labels, a wax seal |
| `vinyl` | none needed (a square album photo is optional) | Impact (DIN Condensed on mac); liner notes in Georgia / Didot italic | a black record sleeve | grooved records with a coloured centre label, the title on an album sleeve, a track list |
| `receipt` | none needed (a photo laid on the counter is optional) | Courier New (Menlo on mac), monospaced throughout | a thermal slip on a counter | torn zigzag edges, dashed separators, line items, the figure as the total, a barcode |
| `comic` | none needed (a photo becomes a panel) | Impact display, Trebuchet MS lettering (Avenir Next body on mac) | a newsprint page of panels | heavy panel borders, Ben-Day dots, caption boxes, speech balloons, a burst for the figure |
| `pixel` | none needed (a photo in a pixel window frame) | Arial Black display, Courier New (Menlo on mac) | an 8-bit screen with a pixel frame and a heart-and-coin HUD | sprites built square by square, a level map, an RPG dialogue box, a score counter |
| `bricks` | none needed (a photo printed on a flat tile) | Trebuchet MS (Avenir Next on mac), Arial Black figures | a studded baseplate | glossy 2.5D toy bricks: a build, one brick per point, the figure on a tower |
| `boardgame` | none needed (a photo printed on a card) | Georgia (Futura display on mac), Arial Black figures | a property board | a ring of colour-banded squares, dice, a pawn moving square to square when ordered, cards |
| `circuit` | none needed (a photo as a display module) | Arial (DIN Condensed / Avenir Next on mac), Courier New labels | a solder-mask board with mounting holes | traces routed round the words, chips with pins on a bus, gold edge-connector fingers |
| `topo` | none needed (a photo as an inset map panel) | Georgia display (Baskerville on mac), Trebuchet MS body | survey paper inside a neatline | contour lines broken round the words, waypoints, a trail to the summit when ordered |
| `scoreboard` | none needed (a photo on the stadium's big screen) | Impact display (DIN Condensed on mac), Arial body | a pitch under floodlights | chalk pitch lines, the title on a scoreboard, jersey numbers, a lineup, an LED board |
| `periodic` | none needed (a photo mounted in a tile) | Arial (Helvetica Neue on mac), Georgia italic lines | lab white, the table as a motif | element tiles coloured by real chemical family, a wall-chart cover, a legend tile |
| `recipe` | none needed (a snapshot clipped to the card) | Georgia italic titles (Hoefler Text on mac), Courier New labels | a gingham tablecloth | a ruled index card, washi tape, tick boxes or numbered steps, a kitchen timer for the figure |
| `stainedglass` | none needed (a photo in a pointed arch) | Georgia (Baskerville on mac) | limestone | geometric rose and lancet windows in lead, words only on stone or clear panes |
| `calendar` | none needed (a photo on a picture-calendar page) | Times New Roman display and figures (Didot on mac), Arial body | a tear-off pad on a desk | binding rings, torn stubs, a page stack that thins as the deck goes on, a giant date numeral |

## Build

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ["SKILL"], "scripts"))   # or the skill folder's absolute path
import deckkit as dk
import register_surface as rs
import visual_languages as vl

P = lambda f: vl.sample_picture("photo/" + f)   # the bundled sample photos (a drawn stand-in in a package
                                                 # that ships no pictures); put the user's own pictures here
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("collage", prs, ground="auto")       # fonts="both" (default): faces on macOS AND Windows;
                                                 # ground="auto": light, or the contrast ground after cream decks
k.cover(k.new_slide(), kicker="A repair café", title="Bring it broken", subtitle="Once a month",
        image=[P("hall-repair.jpg"), P("bench-toaster.jpg"), P("jacket-mend.jpg")])   # collage cover: up to 4
k.section(k.new_slide(), number="02", kicker="How it works", title="We fix it with you")
k.image_text(k.new_slide(), kicker="What you find", title="Tools on every bench",
             body="Volunteers bring the tools.", image=P("tools-tray.jpg"))
k.quote(k.new_slide(), quote="I left knowing how it works.", attribution="A visitor")
k.data(k.new_slide(), number="1", label="evening a month", note="Always the first Friday.")
k.closing(k.new_slide(), title="Bring one broken thing.", line="And bring a neighbour.", image=P("table-mended.jpg"))
prs.save("collage.pptx")
```

- **Pages:** `cover`, `section`, `image_text`, `points`, `quote`, `data`, `closing` — keyword fields only; `image=`
  is optional everywhere except `image_text` (which refuses without one). A list of images is for the
  collage cover and closing only (1 to 4); anywhere else, or empty, or longer, it is refused rather than
  silently cut. A page with no text and no image is refused. Each returns `{"rects": {field: (x, y, w, h)}, …}`.
  On the <!-- vl:count-drawn -->twenty-six<!-- /vl --> DRAWN languages a picture is drawn on `image_text` only (`drafting` also on `quote`;
  `vl.NATIVE_IMAGE_PAGES`): `image=` on any other page of theirs is refused, naming those pages — never dropped.
- **Fields are text.** Pass every field as a string, exactly as it should read; `number=` also takes a whole
  number (`12`, shown as written). A list, a tuple or a float is refused by field name (`number=0.1 + 0.2` would
  print 0.30000000000000004 — pass `"0.3"`). A point is `(head, line)`, `"head"` or `{"head": …, "line": …}`;
  a third member or another key is refused, never dropped.
- **A refused page leaves its slide as it found it** (no half-drawn picture or furniture), so catching
  `VLTextOverflow` and retrying shorter copy on the same slide is safe.
- **Images:** a file path (the user's photo, a fetched public-domain image), or — with
  `vl.use(name, prs, plan=plan, image_dir=…)` — a P1 image-series slot id (placed with `slot_picture`,
  so the series gate still sees it). A missing image raises `FileNotFoundError`. Every picture is placed from
  an upright, embeddable copy (the caller's file is never rewritten): a phone photo's EXIF orientation is
  baked in (PowerPoint ignores the flag and placed it on its side), a 16-bit PNG is scaled to 8 bits, WebP
  and other formats PowerPoint cannot embed are re-saved as PNG. A file that cannot be read — truncated, or not
  a picture — is refused naming the page and the file (`vl.VLImageError`, a `ValueError`).
- **Credits:** every page that takes a picture also takes `credit="Photo: A. Name, CC BY 4.0"` — set by the page ON
  the picture (its bottom-right corner, on a chip of the ground, at the caption size and never under 12pt, clear of
  the footer band). A licence that requires attribution is met on the page that shows the photo; `credit=` without
  `image=` is refused.
- **The picture gives the words room.** When a page's words do not fit beside its picture, the picture shrinks
  (to 80%, then 65% on the image-led pages; by a tenth, then a fifth on the drawn languages' `image_text`)
  before the page refuses.
- **Text that cannot fit** shrinks toward each field's floor size; if even the floors overflow, the page
  raises `vl.VLTextOverflow` naming the page, the field and the inches — shorten the copy, never
  truncate it. A single token wider than the column even at the floor (a code identifier, a URL) is
  refused the same way, naming the word; a long Korean compound breaks between syllables instead. Titles never end in a lone word or one or two CJK characters (shrunk a little, or set in
  a balanced measure). A title, quote, label or line with clause punctuation INSIDE it breaks after its
  clauses when they fit ("带着坏东西来，/ 带着好东西走", "Bring it broken. / Take it home working.") —
  at down to 0.7x its size, never with more lines, set as one paragraph per line. Which marks count, and how to
  punctuate Chinese, Japanese and Korean copy: **CJK and Hangul copy** below.
- **Ordinary pages in the same look** (agenda, bullets, charts) — every page starts with `k.new_slide()`,
  which paints the language's ground (and its grain) and marks the slide as built in the language, so the
  delivery gate counts it; a plain `dk.add_slide()` page is NOT in the language. Then:
  ```python
  s = k.new_slide()
  x, y, w, h = rs.ground(s, k.name, role="content", index=2)    # furniture; returns the content rect
  rows = ["1.  Why a repair café", "2.  How an evening runs", "3.  What to bring"]
  W, H = prs.slide_width.inches, prs.slide_height.inches
  size = 24 * min(W, H) / 7.5                                     # list type scaled with the canvas, never a tiny 12pt
  rows_h = sum(dk.measure_text([(r, False)], w - 0.8, size, font=k.face("body")) + 0.18 for r in rows)
  card_h = rows_h + 1.1                                           # the card fits its words: room for the label band
  body, header = rs.card(s, k.name, x, y + max(0.0, (h - card_h) / 2), w, card_h, label="Agenda")   # SHAPES
  top = header.top.inches + header.height.inches + 0.2 if header else body.top.inches + 0.45   # BELOW the label
  dk.text(s, body.left.inches + 0.4, top, body.width.inches - 0.8, rows_h, [k.runs(r, size) for r in rows], space_after=8)
  ```
  (Run as written in every language: the card is sized to its words and sits in the content rect; a fixed
  full-height card under 14pt rows read as an empty page in two test decks. A list of 2–4 items is better as
  `k.points(...)`, on every language; on drafting, `points` draws one plate per item, so keep an agenda
  there as this ordinary page.)
- **General components wear the language — the 38 in the matrix.** Charts (native and matplotlib), timelines, steps,
  tables, KPI rows, org charts, scorecards, evaluation grids, flows and the rest of the list in
  `tests/test_component_theme.py` (`TIER1`) take the language's surfaces, rules, axes, tracks and series from the active
  theme (`dk.THEME`, set by `vl.use()`; `dk.blank_deck()` and `dk.open_template()` start every deck without one): call
  them with no colour arguments, inside the rect `rs.ground()` returns, and they read on every ground — dark ones and
  each of poster's four page fields included. Text a component draws on its own card keeps its colour where it reads
  and moves the least distance where it would not; a semantic colour (a regression's red, a ✓/✕/◐ mark) keeps its hue
  the same way. A chart with more series than the language designs gets the language's own colours first and then
  its hues turned apart (`dk.theme_series(n)` — use it for any categorical set you draw yourself). matplotlib charts
  (`designed_charts`) take series, ground, ink and a lining-figure face the same way unless you pass `palette=` /
  `dark=` / `font=`. The test holds those 38 on every ground of every language. **Outside that list** —
  `ui_window`, `skeleton`, `brush_stroke`, `grain_background`, `two_tone`, callouts, pills, chips, glass cards — a
  component is not yet held to every ground: lint the page on the language's dark ground before you rely on it.
- **Tier 1 — held to every ground** (colours, readability, placement, the language's type floor):
  <!-- vl:tier-one-list -->`agenda` · `bento` · `consort_flow` · `distribution` · `dot_strip` · `dumbbell_board` · `eval_matrix` · `forest_plot` · `funnel` · `gantt` · `heat_matrix` · `iso_bars` · `iso_prism` · `iso_stack` · `km_curve` · `leaderboard` · `marimekko` · `meter_bar` · `native_chart` · `org_tree` · `position_map` · `pyramid` · `radar` · `roc_curve` · `sankey` · `scorecard` · `segmented_bar` · `small_multiples` · `stat_row` · `step_list` · `table` · `tier_stack` · `timeline` · `unit_grid` · `venn` · `waterfall` · `bland_altman` · `source_note`<!-- /vl -->.
  `python3 scripts/sigs.py --example <component> --in <language>` prints one placed in that language's content rect
  (`rs.ground()`); it runs as printed, and the matrix holds every one inside that rect with no hard lint finding on
  16:9, 3:4, the 10in default and 9:16. A component that needs a wider rect than the canvas gives (consort_flow
  5.5in, sankey 5.0in — `sigs.PLACE_MIN_W`) raises with the width it needs instead of crowding. An example it cannot
  place is printed with the language's page and rect above it, still runnable — move its coordinates into the rect.
- **Tier 2 — also draws in the language's skin** (spec §5.3): each language picks one value per role from
  `scripts/vl_contract.py` `SKIN_VOCAB`; the component draws that role the language's way and picks its text ink
  against what the skin leaves under it. `dk.skin_card(s, x, y, w, h, fill=…)` gives your own containers (the cells
  `dk.bento()` returns) the same card.

<!-- vl:tier-two-table -->
| component | draws in the skin |
|---|---|
| `bento` | card |
| `step_list` | marker, rule, number |
| `timeline` | rule, marker, number |
| `agenda` | rule, number |
| `stat_row` | rule, number |
| `org_tree` | card, rule |
| `tier_stack` | card, rule |
| `funnel` | card, rule |
| `pyramid` | card, rule |
| `venn` | rule |
| `meter_bar` | rule, number |
| `gantt` | rule, number |
| `table` | rule, number |
| `native_chart` | rule, number |
| `heat_matrix` | number |
<!-- /vl -->

<!-- vl:skin-table -->
| language | card | rule | marker | number |
|---|---|---|---|---|
| `editorial` | hairline | hairline | dot | display |
| `soft` | filled | solid | disc-number | body |
| `collage` | paper | solid | badge | display |
| `storybook` | paper | hairline | circled | display |
| `ink` | hairline | hairline | circled | display |
| `poster` | filled | solid | disc-number | display |
| `cutpaper` | paper | solid | disc-number | display |
| `drafting` | outlined | dashed | circled | mono |
| `starlit` | outlined | hairline | dot | display |
| `broadsheet` | hairline | hairline | dot | display |
| `journal` | hairline | hairline | dot | body |
| `tally` | filled | solid | badge | mono |
| `chalkboard` | chalk | chalk | circled | display |
| `interface` | window | hairline | badge | body |
| `wayfinding` | sign | solid | roundel | body |
| `herbarium` | paper | hairline | circled | display |
| `airmail` | paper | dashed | badge | display |
| `vinyl` | filled | hairline | disc-number | display |
| `receipt` | paper | dashed | dot | mono |
| `comic` | outlined | solid | badge | display |
| `pixel` | filled | solid | badge | display |
| `bricks` | filled | solid | badge | display |
| `boardgame` | paper | solid | badge | display |
| `circuit` | outlined | solid | roundel | display |
| `topo` | outlined | hairline | circled | body |
| `scoreboard` | filled | solid | badge | display |
| `periodic` | outlined | hairline | badge | display |
| `recipe` | paper | solid | circled | display |
| `stainedglass` | outlined | solid | roundel | display |
| `calendar` | hairline | hairline | dot | display |
<!-- /vl -->

  A new language picks from the vocabulary; it adds a value only when none fits, implemented once in deckkit's
  `_skin_*` helper for that role.
- **The kit's own pages are clean.** A deck made only of a language's page functions has no hard `lint_deck`
  finding and passes its own prohibitions — `tests/test_vl_audit_fixes.py` builds every language on 16:9 and 3:4,
  both grounds. Furniture that overlaps by design (paper hills over cards, a sun behind a ridge, a blob behind a
  photo, tape across a note) is declared with `dk.overlap_intent`; a texture ground (grid, slate, grain, a night
  sky) reads as its solid colour for contrast; the screen readers' title parked above the page is not counted
  as text in a safe zone. A HARD finding on one of the kit's own pages is therefore a kit defect: report it with
  the language, page and canvas, do not move the kit's shapes. Advisory `[warn]` lines can still appear on your
  own pictures (TEXT-ON-IMAGE CONTRAST over a busy photo) — they ask you to look, not to rebuild.
  Pass `k.name` — the page's OWN language; another language's name on it is refused. `rs.ground` returns the
  content rect `(x, y, w, h)` in inches; `rs.card` returns `(body, header)` —
  python-pptx shapes (`header` is None for a card with no band), so read `body.left.inches` and friends.
  `body` is the WHOLE card: with `label=…` the label sits inside its top, so start the content below it
  (`header.top.inches + header.height.inches`), or it lands on the label.
  Make every paragraph with `k.runs(text, size, color=None, bold=False, role="body")` (a list of runs; one
  run is `k.run(…)`): it picks the language's face and, for Chinese, Japanese or Korean text, that script's
  East-Asian face — never type a font name — and sets digits in a LINING face where the language's face has
  old-style figures (Georgia), so "Repair café 2026" never bobs.
- **Any canvas:** every page has a landscape and a portrait layout (portrait when W < 1.2 H). Given a PORTRAIT
  illustration (width/height < 0.85), storybook's cover, quote and closing switch to a tall frame beside the text on
  a landscape slide (its section, image_text and data frames are tall already); on a portrait slide every page
  switches to a narrower, taller frame. Either way the picture is not shrunk into a frame drawn for a landscape one.
- **A data page with no picture** (the four image-led languages) sets a short figure as big as its column allows.
  Measured on "42" in editorial and storybook: on a 13.333 × 7.5 slide its line is about 60% of the slide's height
  (editorial 274pt), with the label and note beside it; on a 7.5 × 10 portrait slide about 37%, with the label and
  note stacked below. A long number shrinks rather than crowding the label ("1,250,000": 72pt on the same landscape
  editorial page). Collage draws a short figure as an outlined shape. The drawn languages size their own figure.
- **Screen readers:** every page declares its title with `deckkit.a11y_title` (the quote page: the quote; the data
  page: number + label) — first in reading order, above the canvas, nothing drawn — so a kicker set above the title
  never trips READING ORDER. Ordinary `k.new_slide()` pages need their own title (or `dk.a11y_title`).

## Native languages — drawn, no pictures needed

`ink` (水墨), `poster` (海报大字), `cutpaper` (剪纸层叠) and `drafting` (蓝图技术线稿 — named `drafting` because
`blueprint` is a preset), and the second set below, draw their own surface with native, editable shapes (`scripts/native_art.py`), so they
make a finished deck for a talk with no pictures and no image tool. Everything they draw stays on the page, and
every value they write is one PowerPoint opens without repair (`scripts/ooxml_safety.py`, which `lint_deck` runs).

- **`points`** — `k.points(s, kicker=…, title=…, items=[("Head", "line"), …])`: 2 to 4 points, each a string, a
  `(head, line)` pair or a `{"head": …, "line": …}` dict — on every language. The image-led four set each point
  as a number, a head and a line in their own furniture (editorial: a hairline over each; soft: a rounded panel;
  collage: a taped note; storybook: a painted dot instead of a number), in a row, a 2x2 grid or a stack —
  whichever sets them largest — and take an optional `image=` beside them (landscape) or above them (portrait).
- **Words only you can give** — the kit never invents them, and draws nothing when they are absent:
  - `seal="茶事"` on any `ink` page: one or two characters
    of your own text, carved into a red seal;
  - `highlight="room"` on `poster` (`cover`, `section`, `quote`, `closing` — refused on any other page): words of
    that page's own title or quote, set on a highlighter (refused when they are not in it);
  - `icons=["lucide:wind", …]` on `cutpaper`'s `points`: one `library:name` spec per point (names as on
    lucide.dev/icons or tabler.io/icons); an unknown name raises naming the URL it tried — never a blank disc;
  - `project="…"` on any `drafting` page: the words in the sheet's title block, measured into it (10pt down to
    7pt; refused when they still do not fit). Without it the cover title is remembered and carried to every later
    sheet — or left out when too long for the block (the sheet number stands alone). Sheets are numbered by
    themselves.
- **Vertical CJK** — `ink` sets a title, a quote couplet, a label and its points as vertical columns read right
  to left ONLY when the text is Chinese or Japanese with no Latin letters or digits; Latin, Hangul or mixed text
  is set horizontally in the same composition. A vertical field shrinks toward its floor and is refused past
  its columns, like any other field.
- **Display type** (`poster`) breaks like the rest of the kit: at a clause mark first, never a lone CJK
  character or word on the last line; a figure (`1,250,000`) stays on one line. Latin kickers, the cover, section,
  points and closing titles, the quote and the data label are set in capitals; the `image_text` title, the body
  copy, point heads and lines, notes and attributions stay as you typed them.
- **Vertical columns break at the clause** (`ink`): "宋代点茶： / 一盏茶里的审美", never mid-word; a quote couplet
  is two equal columns at one size.
- **Long copy gets a roomier layout before it is refused.** Each native page tries its designed layout first,
  then alternatives: `ink` sets a field horizontally when its vertical columns cannot hold it; `poster`'s points
  become a full-width staircase under the title; `cutpaper`'s cards grow or form a two-column grid; `drafting`'s
  notes take more width, then become a numbered parts legend (a balloon on each plate, no leaders).
  `VLTextOverflow` means even the last layout could not hold the words — shorten them. Verified on 10in 16:9,
  4:3, square and A4-portrait canvases with 14-word titles and four two-line points
  (`tests/test_native_generality.py`).
- **Ordinary pages** — `k.new_slide()` gives `poster` the next colour field (the deck's inks — `dk.DEEP` and
  friends — and `rs.card` follow it, so read `k.color("ink")` for text) and `drafting` its numbered drawing sheet
  on the grid.
- **When they are offered** — a deck with no pictures (`direction_gate.images: none`) offers the one that fits
  the topic and records why beside `images`; both gates hold it:
  ```json
  "direction_gate": {"candidates": "directions.json", "picked": "<the one chosen>", "images": "none",
                     "native_fit": {"language": "ink", "why": "a talk on tea craft: culture and ritual"}}
  ```
  `native_fit.language` is one of the native languages among the candidates (not necessarily the one picked). Guidance, not a rule: <!-- vl:offer-arrow -->culture, history, craft → `ink`; launch, manifesto, opinion → `poster`; children, storytelling, community → `cutpaper`; engineering, architecture, systems design → `drafting`; year in review, letter, thanks, commemoration → `starlit`; newsletter, periodic report, community update → `broadsheet`; research talk, lab meeting, paper, defence → `journal`; metrics, quarterly review, operations, growth → `tally`; lesson, class, training, explainer → `chalkboard`; product launch, app, SaaS, feature tour, internal tool → `interface`; roadmap, process, onboarding, journey, strategy route, transport/city → `wayfinding`; nature, ecology, sustainability, field research, biology → `herbarium`; travel, international, cross-border, logistics, global teams, exchange programme → `airmail`; music, podcast, culture, creative work, anniversary → `vinyl`; pricing, budget, cost breakdown, retail, e-commerce, expenses → `receipt`; storytelling, user journey, explainer, product launch, team story → `comic`; games, gamification, hackathon, youth event, onboarding challenge, game jam → `pixel`; children's education, modular product, system architecture, teamwork, building blocks, STEM workshop → `bricks`; processes, onboarding, strategy, gamified training, step-by-step plans, game plan → `boardgame`; hardware, IoT, embedded systems, AI infrastructure, engineering review, electronics → `circuit`; geography, outdoors, climate, field work, strategy landscape → `topo`; sports, competition, team results, sales push, leaderboard, tournament → `scoreboard`; science education, chemistry, building blocks of a topic, frameworks, taxonomies → `periodic`; food, cooking, recipes, how-to guide, step-by-step process, workshop → `recipe`; heritage, culture, celebrations, festivals, art and design history → `stainedglass`; timeline, event, anniversary, schedule, countdown, daily habit → `calendar`.<!-- /vl -->

### The second set — `starlit` · `broadsheet` · `journal` · `tally` · `chalkboard`

Five more drawn languages, each borrowed from a convention people already read at a glance. Same contract as the
first four: no pictures needed, everything on the page, nothing PowerPoint repairs, and no word invented.

| language | 中文 | borrowed from | for |
|---|---|---|---|
| `starlit` | 星夜 | the night sky and the year-end letter | year in review, letters, thanks, commemoration |
| `broadsheet` | 报纸头版 | the newspaper front page | newsletters, periodic reports, community updates |
| `journal` | 学术期刊 | the journal article | research talks, lab meetings, papers, defences |
| `tally` | 数据账本 | data dashboards and finance reports | metrics, quarterly reviews, operations, growth |
| `chalkboard` | 黑板报 | the classroom blackboard | lessons, classes, training, explainers |

- **Words only you can give.** A word given on a page that does not draw it is refused, naming the pages that do;
  when it is absent, nothing is drawn. `python3 "$SKILL/scripts/sigs.py" Kit.cover` (any page) lists them all; they arrive as `**extras`.
  - `masthead="…"` (`broadsheet`, any page, remembered for the deck): the paper's name in the masthead strip.
    Without it, the cover's `kicker` names the paper and is not repeated above the headline; without either, the
    strip has rules and the page number only.
  - `edition="…"` (`broadsheet`, any page, remembered): the strip's left words, such as your date or issue.
  - `inside=[…]` (`broadsheet` cover): 1–4 short lines for the "INSIDE" sidebar.
  - `tags=[…]` (`broadsheet` and `tally` `points`): one short label per point — a broadsheet column's label (it
    wraps like any label) or a tally row's pill (beside the words, or under them when the pills are wide). The count
    must match; a tally tag too long even for a pill under its row's words is refused by name.
  - `running="…"` (`journal`, any page — the cover too, though it draws none — remembered): the running head. Without it, the cover title runs there when
    it fits one line, else the page number stands alone. An explicit `running=` that cannot fit is refused.
  - `authors="…"`, `abstract="…"` (`journal` cover): the author line and the abstract block. A subtitle is never
    labelled "ABSTRACT".
  - `margin="…"` (`journal` `points`): a margin note under a "NOTE" label.
  - `total="…"` (`tally` `data`): draws a share bar, the number's share of the total, with both numbers at its ends.
    The rules:
    - both are plain numbers (`12`, `1,250`, `98.6%`);
    - both are percentages or neither is;
    - the number is no larger than the total.

    Anything else is refused, never guessed.
  - `doodle="lucide:sun"` (`chalkboard` cover and closing): one icon spec, drawn in yellow chalk. It is fetched from
    the icon library on first use (network) and cached; an unknown name raises, naming the URL it tried, and the page
    is not built — check the name on lucide.dev/icons or tabler.io/icons.
  - `ordered=True` (`chalkboard` `points`): chalk arrows between the boxes, only when the points really happen in
    order. The numbers already read as a list.
- **Derived, never typed in** — what the drawn languages write by themselves (checked by building every page,
  2026-10-09); everything else on a page is your own words:
  - page numbers: `PAGE n` on every `broadsheet` page, the cover too; a two-digit number (`01`, `02` …) on every
    `poster` page; a plain number on every `journal` page except the cover. The four image-led languages, `ink`,
    `cutpaper`, `starlit`, `tally` and `chalkboard` number no pages;
  - `drafting`'s sheet border (`1`–`6`, `A`–`D`) and its title-block labels `SHEET` (with the sheet's two-digit
    number) and `PROJECT`, in English whatever the deck's language;
  - `journal`'s `§` before a section's `number=` (`§ 02`; no `number=`, no `§`);
  - point numbers: `01 02 03` on `tally` and `poster` `points`; `一 二 三` on `ink` when the title is Chinese or
    Japanese, else `1 2 3`; `1 2 3` on `cutpaper`, `journal` and `chalkboard` (circled there); `starlit` numbers none;
    `No. 1 No. 2` (`第 1 号` in Chinese or Japanese) on `herbarium`'s label cards; `1 2 3` on `airmail`'s small stamps;
    the track numbers `A1 A2 … B1 B2` on `vinyl` (the first half of the points on side A); `01 02 03` on `receipt`;
    `1 2 3` on `calendar`'s day cells, `stainedglass`'s lancet panes, `periodic`'s tiles (top left) and the shirts
    of `scoreboard`'s lineup; `1 2 3` on `boardgame`'s squares, `topo`'s waypoints and `recipe`'s steps only with
    `ordered=True`; the designators `U1 U2 …` on `circuit`'s chips; the level numbers `1-1 1-2 …` on `pixel`'s
    level map; `comic` and `bricks` number none;
  - `pixel`'s page number (`01 02 …`) beside the coin in the HUD at the top of every page;
  - `herbarium`'s plate number at the top right of every page — the page's own number (`PL. 4`; `图版 4` / `図版 4`);
  - `journal` figure numbers over the deck's `image_text` pages, with `kicker=` to override;
  - the `broadsheet` ■ end mark on the closing page; the opening `“` on quote pages (not on `ink` or `tally`); the
    `— ` before an attribution on `journal`, `chalkboard` and `wayfinding`;
  - `interface`: `1 2 3` badges on `points`; the avatar's initials on `quote` (from a name only — "Mara Jensen, Ops
    lead" gives `MJ`; a description or a CJK name gives no avatar); the `i` beside a data `note=`; with `total=`, the
    total printed at the end of the progress bar;
  - `wayfinding`: numbered roundels `1 2 3` on the directory sign and on the departure board's rows (each in its line
    colour); the way-out label on the closing sign (`WAY OUT` / `出口` / `出口` / `출구`, in the script of the page's
    words);
  - the structural labels, stored in CAPITALS in English (`ABSTRACT`, `INSIDE`, `FIGURE 1`, `PAGE 2`, `NOTE`) and
    in the script of the page's own words otherwise:

    | label | 中文 | 日本語 | 한국어 |
    |---|---|---|---|
    | ABSTRACT | 摘要 | 要旨 | 초록 |
    | INSIDE | 本期 | 目次 | 목차 |
    | FIGURE n | 图 1 | 図 1 | 그림 1 |
    | PAGE n | 第 2 版 | 2 面 | 2면 |
    | NOTE | 注 | 注 | 주석 |

  Some of your own words are re-cased: `poster` (above), the kicker and attribution on `starlit` and
  `broadsheet`, the kicker on `journal` and on `wayfinding` (cover, section, image_text, directory sign), the kicker
  on `airmail`, `vinyl` and `receipt`, and each line item's head on `receipt`.
- **Pages.** All seven pages come in both orientations.
  - `journal`'s `image_text` is its figure page: the title above, your figure WHOLE (never cropped), its label,
    caption (`body=`) and source line (`caption=`).
  - `broadsheet` opens a Latin column body on a raised initial: an enlarged first letter in its own line, because
    pptx has no drop cap. CJK bodies are not enlarged.
  - `starlit`'s points are a constellation (one star per point), `tally`'s are ledger rows, and `chalkboard`'s are
    chalk boxes sized to their words.
- **Ordinary pages** (`s = k.new_slide()`, then `rs.ground(s, k.name, …)`):
  - `starlit` paints its sky clear of the returned rect;
  - `broadsheet` draws the masthead strip, and `journal` the running head, with the deck's remembered words, and
    return the rect under it;
  - `tally` is on its grid;
  - `chalkboard` is a framed board.
- **No light ground.** `starlit` and `chalkboard` have no light ground: both their grounds are dark, and their
  `light` key IS their dark default. `poster`'s default is saturated colour fields, which print dark too. On a printed
  board `ground="auto"` keeps the default for all three and says it prints as a dark page. For a lighter printed
  poster pass `ground="paper"` yourself (off-white fields, with a black and a cobalt one in every four pages).
- **No spaces between Chinese and Latin words** ("心脏MRI的", not "心脏 MRI 的"). The renderers add their own gap,
  and a typed space doubles it; this was measured on the look-dev.

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ["SKILL"], "scripts"))
import deckkit as dk, visual_languages as vl
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("broadsheet", prs)
k.cover(k.new_slide(), title="Every street needs a night for fixing things",
        subtitle="How a repair evening works, and why it spreads.", masthead="The Repair Weekly", edition="No. 12",
        inside=["The idea", "The evening", "The numbers"])
k.points(k.new_slide(), title="How it works", tags=["Idea", "Evening", "Next"],
         items=[("Bring it broken", "Anything that switches on is welcome."), ("Fix it together", "Your hands do the work."),
                ("Take it home", "What is not fixed goes on the list.")])
k.closing(k.new_slide(), title="See you next week", line="Bring a neighbour.")
prs.save("weekly.pptx")
```

### The third set — `interface` · `wayfinding`

| Language | 中文 | Borrowed from | Purpose |
|---|---|---|---|
| `interface` | 产品界面 | the product UI: windows, status chips, toggles, dialogs, dashboards | product launches, app / SaaS pitches, feature tours, internal-tool demos |
| `wayfinding` | 导视线路 | metro maps and station signage: lines, roundels, station signs, departure boards | roadmaps, processes, onboarding, journeys, strategy routes, transport / city |

- **interface** — every page is an app screen. The cover is a window (crumb and status in its bar, title, subtitle,
  your actions as buttons with a pointer on the first) with an optional settings panel beside it; `points` is a
  settings list (numbered badges, head + line, an optional chip per point); `quote` is a chat message (initials
  only when the attribution is a name); `data` a dashboard card with a progress bar when `total=` is given (tally's
  rules) and the note beside it; `closing` a dialog whose buttons are your `actions=`; `image_text` puts your
  picture in a phone frame when it is taller than wide, a browser frame otherwise. Grounds: `light` (app light) ·
  `dark` (dark mode).
- **wayfinding** — the deck is a network. The cover is lines converging on an interchange, your title the
  destination and your subtitle on a station sign; `section` a station-name sign (its roundel shows the section
  number, coloured by it: 1 red, 2 blue, 3 green, 4 yellow, 5 purple); `points` is a strip map ONLY with
  `ordered=True` — a route claims an order — and otherwise a directory sign (one row per point with its numbered
  roundel); `data` a departure board (your label and number first, `board=` rows under them); `closing` the way-out
  sign (Way out / 出口 / 出口 / 출구, in the page's script) with the route ending at a terminus. A line too light for
  its ground (yellow on the enamel) runs on its dark casing. Grounds: `light` (enamel) · `night` (navy).
- **Extras** (from you only; absent → nothing drawn; on a page that does not draw one it is refused by name):

  | Language | Extra | Pages | Meaning / fallback |
  |---|---|---|---|
  | interface | `crumb=` | any; remembered | the window's breadcrumb (e.g. "Launch › Overview"), drawn in the top bar of the windows that have one — cover, section, points (image_text, quote, data and closing draw no bar, but remember it). Given on a points page that only fits without its bar, the page is refused rather than the crumb dropped. Absent (and no `status=`): the window has no top bar. |
  | interface | `status=` | any; remembered | the top-bar status chip text, optionally `(text, state)` with state in on / pending / error / primary. Absent: no chip. |
  | interface | `actions=` | cover, closing | 1–2 button labels (primary, secondary). Absent: no buttons, no pointer. |
  | interface | `toggles=` | cover | 1–4 `(label, on)` rows for a settings panel beside the window. Absent: the window takes the width. |
  | interface | `tags=` | points | one chip per point, text or `(text, state)`; count must match. |
  | interface | `total=` | data | progress bar, tally's rules (plain numbers, same kind, ≤ total); the number is printed under the bar's fill end and the total under its right end. |
  | wayfinding | `line=` | any but closing; remembered | a 1–3 character line code for the cover/section roundels, optionally `(code, colour name)`. On the cover it sits on the subtitle sign, or above the kicker when there is no subtitle; on a section it REPLACES the section number in the roundel. A longer code (`M10`, `一号线`) is set smaller, or in a pill as wide as its words; one too long even for a pill is refused naming `line=` (a long `number=` likewise). On `closing`, `line=` is the closing's own line of text. On a quote the line arrives from the page's edge as a route ending in the roundel above the sign. Absent: section roundels show the section number; the cover and the quote draw no roundel. |
  | wayfinding | `ordered=` | points | `True` draws the strip map; default draws the directory sign. |
  | wayfinding | `interchange=` | points | 0-based indexes of points drawn as interchanges (`[2]` = the third stop; strip map only; refused without `ordered=True`). |
  | wayfinding | `board=` | data | 1–4 extra `(label, value)` rows under the page's own row. |

```python
import visual_languages as vl, deckkit as dk
prs = dk.blank_deck()
k = vl.use("interface", prs)
k.cover(k.new_slide(), kicker="Product tour", title="One board for every request", crumb="Launch › Overview",
        status=("Live", "on"), actions=["Get started"], toggles=[("Auto-sync", True), ("Public link", False)])
k.points(k.new_slide(), title="Three settings", items=["Approvals first", "One source of truth", "A weekly digest"],
         tags=[("Required", "pending"), "On", "New"])
k.data(k.new_slide(), number="12", label="of 40 teams switched", note="Since the beta opened.", total="40")
k.closing(k.new_slide(), title="Start with one team", line="Free for the first month.", actions=["Start free"])
w = vl.use("wayfinding", dk.blank_deck())
w.points(w.new_slide(), title="Four stops to a paying customer", ordered=True, interchange=[2],
         items=["Sign up", "First project", "Invite a teammate", "Upgrade"])
w.data(w.new_slide(), number="96.4%", label="Harbour line on time", board=[("North loop", "93.1%")])
```

### The fourth set — `herbarium` · `airmail` · `vinyl` · `receipt`

| Language | 中文 | Borrowed from | Purpose |
|---|---|---|---|
| `herbarium` | 标本图鉴 | a natural-history specimen sheet: pressed sprigs, paper tape, typed labels, numbered plates | nature, ecology, sustainability, field research, biology |
| `airmail` | 航空邮件 | an air-mail envelope: the striped border, stamps, postmarks, address labels, a wax seal | travel, international work, cross-border, logistics, global teams, exchange programmes |
| `vinyl` | 黑胶唱片 | a record and its sleeve: grooves, the centre label, the album front, the track list, the tonearm | music, podcasts, culture, creative work, anniversaries |
| `receipt` | 购物小票 | a thermal till slip: torn edges, monospaced lines, dashed rules, the total, the barcode | pricing, budgets, cost breakdowns, retail, e-commerce, expenses |

- **herbarium** — every page is a plate in a specimen collection, inside a hairline double frame with its plate
  number at the top right. The cover sets your title beside a tall pressed sprig and a fern taped to the sheet, your
  kicker typed on the label card under them; `section` flanks your number with two small sprigs; `image_text` mounts
  your picture like a specimen (a card mount, tape at its corners, the caption on a label card); `points` is a plate
  of specimens — a different leaf over each point's typed label card (rows with a single leaf on a portrait or square
  page); `data` puts your number on a specimen tag with its eyelet and string; `closing` crosses two sprigs over your
  title. Grounds: `light` (archival paper) · `cabinet` (specimen-cabinet green-black).
- **airmail** — the deck is a letter. Every page sits inside the red-and-blue striped air-mail border; the cover is
  an envelope front (your kicker where the sender writes, a stamp with a paper plane struck by a postmark, your title
  where the address goes); `section` and `data` print your number as a stamp's denomination; `image_text` is a
  postcard with a postmark across its corner; `points` are address labels with the striped band and a small numbered
  stamp each; `quote` reads like a line from a letter; `closing` is the envelope's back — its flap and a wax seal.
  Grounds: `light` (envelope) · `night` (night-mail navy).
- **vinyl** — the deck is an album. The cover is the album front (your title printed on a coloured sleeve, the record
  sliding out of it); `section` and `data` put your number on the record's centre label (a tonearm resting on the
  record on `data`); `image_text` makes your picture the square album photograph with its record behind it; `points`
  is a track list — A1 A2 … B1 B2 — beside a half record rising from the page's edge; `quote` is set like liner notes;
  `closing` raises a record from the page's foot. Grounds: `light` (black sleeve, dark) · `cream` (cream sleeve).
- **receipt** — every page is a till slip on a counter: torn zigzag edges, monospaced type, dashed rules, a barcode at
  the foot. The cover and the closing lay an older slip askew behind; `points` reads as line items (`01  RENT AND
  BILLS`, its line under it; two slips side by side for long copy on a wide page); `data` reads your number as the
  total, set to the right under your label; `image_text` lays the slip over your picture's edge, the picture a print
  on the counter. Grounds: `light` (till slip) · `carbon` (canary carbon copy, violet ink).
- **Extras:** none — every word on these pages is yours, except the derived numbers above.

```python
import visual_languages as vl, deckkit as dk
k = vl.use("herbarium", dk.blank_deck())
k.data(k.new_slide(), number="214", label="trees counted in one afternoon", note="Mapped by twelve volunteers")
v = vl.use("vinyl", dk.blank_deck(), ground="cream")
v.points(v.new_slide(), title="This season", items=[("The driver", "Twenty years on the last route home"),
         ("The baker", "Bread out of the oven at four"), ("The nurse", "A shift that ends at sunrise")])
r = vl.use("receipt", dk.blank_deck(), ground="carbon")
r.data(r.new_slide(), number="18%", label="of income saved this month", note="Up from twelve per cent")
```

### The fifth set — `comic` · `pixel` · `bricks` · `boardgame` · `circuit` · `topo` · `scoreboard` · `periodic` · `recipe` · `stainedglass` · `calendar`

| Language | 中文 | Borrowed from | Purpose |
|---|---|---|---|
| `comic` | 漫画分镜 | a printed comic page: panels, Ben-Day dots, caption boxes, balloons, bursts | storytelling, user journeys, explainers, product launches, team stories |
| `pixel` | 像素游戏 | an 8-bit game screen: sprites on a pixel grid, a HUD, a level map, a dialogue box | games, gamification, hackathons, youth events, onboarding challenges |
| `bricks` | 积木 | interlocking toy bricks on a baseplate | children's education, modular products, system architecture, teamwork |
| `boardgame` | 棋盘游戏 | a property-style board game: banded squares, dice, a pawn, cards | processes, onboarding, strategy, gamified training, step-by-step plans |
| `circuit` | 电路板 | a printed circuit board: traces, pads and vias, chips, silkscreen | hardware, IoT, embedded systems, AI infrastructure, engineering reviews |
| `topo` | 等高线地形图 | a topographic survey sheet: contours, summits, waypoints, a trail | geography, outdoors, climate, field work, strategy landscapes |
| `scoreboard` | 体育记分牌 | a stadium: pitch markings, the scoreboard, jerseys, a fans' banner | sports, competitions, team results, sales pushes, leaderboards |
| `periodic` | 元素周期表 | the periodic table: element tiles coloured by chemical family | science education, chemistry, building blocks of a topic, frameworks |
| `recipe` | 食谱卡 | a recipe index card on a gingham tablecloth | food, cooking, how-to guides, step-by-step processes, workshops |
| `stainedglass` | 彩绘玻璃 | stained-glass windows: rose and lancet windows in lead, stone arches | heritage, culture, celebrations, festivals, art and design history |
| `calendar` | 撕页日历 | a desk tear-off calendar: rings, torn stubs, a giant date | timelines, events, anniversaries, schedules, countdowns |

- **comic** — every page is a comic page with paper gutters. The cover sets your kicker on a red masthead band and
  your title in a caption block on a burst; `section` puts your number in a two-layer burst; `image_text` makes your
  picture a panel and your body a balloon pointing at it; `points` gives each point a panel (head in a corner caption
  box); `quote` is one big balloon whose tail points at the attribution; `data` sets your number in a burst with
  focus lines; `closing` is a final wide panel. Grounds: `light` (newsprint) · `noir` (black page, one hot red).
- **pixel** — an 8-bit game screen with a pixel frame and a heart-and-coin HUD on every page. The cover is a title
  screen; `section` a level card with your number large; `image_text` frames your picture in a pixel window (on the
  green ground it is shown dithered into the four greens — a copy; your file is untouched); `points` is a level map
  of tiles `1-1 1-2 …` (a path, the hero and a goal flag with `ordered=True`); `quote` an RPG dialogue box with the
  speaker standing above it; `data` a score counter (an HP bar with `total=`); `closing` the end screen with a goal
  flag. Grounds: `light` (handheld green, four olive greens) · `arcade` (arcade night).
- **bricks** — glossy toy bricks on a studded baseplate. The cover builds a small ziggurat beside your title;
  `section` sets your number on one big brick; `image_text` prints your picture on a flat tile with bricks locked on
  its corner; `points` gives each point its own brick (a course, a staggered stack, or a pyramid of two courses);
  `quote` sets your words on a yellow flat tile under a red brick; `data` stands your number on a tower of bricks
  (a stack, never a chart); `closing` finishes the build on a green plate. Grounds: `light` (grey baseplate) · `blue`
  (blue baseplate).
- **boardgame** — a generic property board: no brand, no game words. The cover is the whole board with your title on
  its centre banner, dice and a pawn on the start corner; `section` puts your number on a big corner square;
  `image_text` prints your picture on a card from the deck; `points` are squares on the track (with `ordered=True`
  numbered, the pawn on square 1 and hops between them); `quote` is a drawn card; `data` is the square the pawn
  landed on; `closing` runs into a chequered finish corner. Grounds: `light` (classic board) · `felt` (deluxe felt
  table).
- **circuit** — the page is a board: traces routed at 45° and 90° round your words, stopping in vias. The cover
  converges buses on a large chip; `section` and `data` put your number on a chip (leads on four sides on `data`);
  `image_text` makes your picture a display module; `points` are chips `U1 U2 …` on one gold bus; `quote` sits in a
  silkscreen keep-out; `closing` is the board's edge-connector fingers. Grounds: `light` (green solder mask, dark) ·
  `matte` (matte black board with gold traces).
- **topo** — a survey sheet: contours traced from a height field, broken wherever a word sits, inside a graduated
  neatline. The cover sets a summit with its survey triangle, a north arrow, a figureless scale bar and a stream
  beside your title; `section` puts your number on a summit; `image_text` is an inset map panel; `points` are
  numbered waypoints (a dashed trail to the summit with `ordered=True`); `quote` is a map legend box; `data` your
  number as the summit's spot height; `closing` a path in switchbacks to a pennant. Grounds: `light` (survey paper) ·
  `night` (night relief).
- **scoreboard** — a stadium under floodlights; no team names, scores or labels of its own. The cover lights your
  title on the scoreboard over a pitch in perspective; `section` prints your number on a jersey on its hook;
  `image_text` puts your picture on the big screen, the caption in its ticker; `points` is a lineup, each point in a
  numbered shirt, the shirts also in formation on a half pitch; `quote` a fans' banner on the stand's rail; `data`
  your number on an LED board; `closing` the whole pitch from above. Grounds: `light` (night match, dark) · `turf`
  (striped turf, dark).
- **periodic** — the periodic table as a design system: tiles coloured by the real family of the element they stand
  for (section N and point N take element N's family). The cover is a wall chart with your title in the table's bay;
  `section` a large solid tile with your number and a small table with element N lit; `image_text` mounts your
  picture in a tile; `points` are element tiles — the number top left, your head as the large mark, your line as the
  name line; `quote` the legend tile; `data` a giant tile with your number (a percentage lights that share of a small
  table); `closing` the table as an outline with element 118 lit. Grounds: `light` (lab white) · `dark` (charcoal,
  glowing outline tiles).
- **recipe** — a cream index card with a red header rule and blue ruled lines on a gingham tablecloth; words sit only
  on cards. The cover lays the card over an older one with a whisk and spoon in red line; `section` is a recipe-box
  divider with your number on its tab; `image_text` clips your picture to the card as a snapshot; `points` is a
  checklist with tick boxes (numbered steps in rings with `ordered=True`); `quote` a yellow note card; `data` your
  number on a kitchen timer's dial; `closing` a card signed with a red heart. Grounds: `light` (gingham tablecloth) ·
  `kraft` (butcher paper with a blue-gingham napkin).
- **stainedglass** — windows built from geometry: jewel glass in thick lead, stone tracery; your words never sit on
  busy glass — only on stone, plaster or a clear pane. The cover sets a rose window beside your title; `section` and
  `data` put your number on the rose's clear centre; `image_text` masks your picture to a pointed arch; `points` is an
  arcade of lancets, one glass colour per point, the number on each pane, head and line on the stone below; `quote` a
  plastered niche under an arch; `closing` a single lancet casting coloured light on the floor. Grounds: `light`
  (limestone) · `nave` (night nave, glowing glass).
- **calendar** — a tear-off pad on a desk: a bound header with two rings, torn stubs under it, a stack of leaves at
  the foot that thins as the deck goes on (the closing page is the last leaf). The cover prints your kicker where the
  month goes and your title large; `section` and `data` set your number as a giant red date; `image_text` is a picture
  calendar; `points` a week-like strip of day cells numbered 1 2 3; `quote` a quote-a-day page. No month or weekday
  names — only your words. Grounds: `light` (paper on oak) · `night` (black stock at night).
- **Extras:** `ordered=True` on `points` for `boardgame`, `topo`, `recipe` and `pixel` (the same meaning as
  `chalkboard`'s and `wayfinding`'s: a route or numbering only when the points really happen in order);
  `total="…"` on `pixel` `data` (tally's rules: plain numbers, same kind, ≤ total).

```python
import visual_languages as vl, deckkit as dk
p = vl.use("pixel", dk.blank_deck(), ground="arcade")
p.points(p.new_slide(), title="The rounds", ordered=True,
         items=[("Pitch", "Friday night"), ("Build", "All Saturday"), ("Play", "Sunday afternoon")])
t = vl.use("topo", dk.blank_deck())
t.data(t.new_slide(), number="2,410", label="metres at the top", note="Measured at the survey cairn")
c = vl.use("calendar", dk.blank_deck(), ground="night")
c.section(c.new_slide(), number="30", title="Days to launch")
```

## Grounds

Each language has its own light paper and ONE contrast ground; every text ink passes 4.5:1 on both:

| language | `light` | contrast ground |
|---|---|---|
| editorial | warm paper | `ink` — warm black, paper-white type, a lighter red and blue |
| soft | cream | `dusk` — deep plum-indigo, the pastel blobs kept |
| collage | kraft | `slate` — dark grey paper, cream prints and note cards (the light ground's dark inks on them) |
| storybook | paper | `meadow` — green paper; the watercolours are tinted onto it, as if painted there |
| ink | xuan paper | `night` — ink-black paper, pale ridges, a moon for the sun |
| poster | colour fields (cobalt, lime, black, signal orange, one per page) | `paper` — off-white fields, with a black and a cobalt one in every four pages |
| cutpaper | day | `night` — navy sky, a paper moon, dark hills |
| drafting | vellum | `cyanotype` — blueprint navy, pale linework |
| starlit | midnight (dark — no light ground) | `dawn` — deep violet, rose gold |
| journal | paper | `green` — title green, gold accent |
| broadsheet | newsprint | `salmon` — pink paper, navy accent |
| chalkboard | green board (dark — no light ground) | `slate` — grey slate |
| tally | white grid | `night` — navy grid, periwinkle and lime |
| interface | app light | `dark` — dark mode, deep windows |
| wayfinding | enamel | `night` — navy, darker signs |
| herbarium | archival paper | `cabinet` — specimen-cabinet green-black, sage leaves, labels in its own tones |
| airmail | envelope | `night` — night-mail navy, red and ivory stripes |
| vinyl | black sleeve (dark) | `cream` — cream sleeve, a teal album front |
| receipt | till slip on a grey counter | `carbon` — canary carbon copy, violet carbon ink |
| comic | newsprint | `noir` — black page, paper-white keylines and balloons, one hot red |
| pixel | handheld green (four olive greens) | `arcade` — arcade night, deep navy with saturated sprites |
| bricks | grey baseplate | `blue` — blue baseplate, azure and white bricks |
| boardgame | classic board (mint) | `felt` — deluxe felt table, gold banner and pawn |
| circuit | green solder mask (dark — no light ground) | `matte` — matte black board, gold traces |
| topo | survey paper | `night` — night relief, pale sage contours |
| scoreboard | night match (dark — no light ground) | `turf` — striped turf, chalk-white lines |
| periodic | lab white | `dark` — charcoal, glowing outline tiles |
| recipe | gingham tablecloth | `kraft` — butcher paper, a blue-gingham napkin (a second light colourway) |
| stainedglass | limestone | `nave` — night nave, glowing glass |
| calendar | paper on oak | `night` — black stock at night, oxblood header, brass rings |

`use(name, prs, ground=…)`: `"light"` (the default — the same deck on every machine), the contrast key, or
`"auto"` (this machine's look history, across every deck built here — pass the ground yourself when the topic
asks for one, e.g. a children's lesson on light paper) — the light ground unless the last three decks in your look history already sit on it (the
register-pixels GROUND REPEAT distance), then the contrast one; a printed board (A4, the A0/A1 posters) always
stays light, and no history means light. `auto` prints what it chose and the `--gates … --ground …` command that
records it, as a template with two `<…>` blanks (the deck folder and what the deck is for): fill both in, because
it will not run as printed. `vl.direction(name, ground="auto", W=…, H=…)` — the deck's canvas in
inches, 13.333 x 7.5 by default — shows the sample of that same ground, so the picked preview and the built deck agree. `python3 "$SKILL/scripts/visual_languages.py" --list` lists every language's grounds.

## Fonts

`fonts="both"` (default) uses only faces present on macOS AND Windows, so the render matches what the
viewer opens. `fonts="mac"` unlocks Mac-only faces and refuses one that is not installed.

| language | display (both / mac) | body (both / mac) | numerals (both / mac) |
|---|---|---|---|
| editorial | Georgia / Didot | Arial / Helvetica Neue | Arial Black (lining) / Helvetica Neue |
| soft | Trebuchet MS / Arial Rounded MT Bold | Trebuchet MS / Avenir Next | Trebuchet MS / Arial Rounded MT Bold |
| collage | Impact / Impact (+ Bradley Hand accents on mac) | Arial / Avenir Next | Impact |
| storybook | Georgia / Baskerville | Georgia | Times New Roman (lining) |
| ink | Georgia / Baskerville | Georgia | Times New Roman (lining) |
| poster | Impact | Arial / Helvetica Neue (meta: Courier New) | Impact |
| cutpaper | Trebuchet MS / Avenir Next | Trebuchet MS / Avenir Next | Trebuchet MS / Avenir Next |
| drafting | Georgia | Georgia (labels and title block: Courier New) | Times New Roman (lining) |
| starlit | Georgia | Georgia | Times New Roman (lining) |
| broadsheet | Times New Roman | Georgia (meta lines: Arial) | Times New Roman |
| journal | Georgia | Georgia (labels: Arial) | Times New Roman (lining) |
| tally | Arial Black | Arial / Helvetica Neue | Arial Black |
| chalkboard | Trebuchet MS / Chalkboard SE | Trebuchet MS / Chalkboard SE | Trebuchet MS / Chalkboard SE |
| interface | Arial / Helvetica Neue | Arial / Helvetica Neue | Arial / Helvetica Neue |
| wayfinding | Arial / Helvetica Neue | Arial / Helvetica Neue (the board: Courier New / Menlo) | Courier New / Menlo on the board |
| herbarium | Georgia / Baskerville | Georgia (labels: Courier New / American Typewriter) | Times New Roman (lining) |
| airmail | Trebuchet MS / Futura | Trebuchet MS / Avenir Next (quotes: Georgia / Baskerville) | Times New Roman / Didot |
| vinyl | Impact / DIN Condensed | Arial / Avenir Next (liner notes: Georgia / Didot) | Impact / DIN Condensed |
| receipt | Courier New / Menlo | Courier New / Menlo | Courier New / Menlo |
| comic | Impact | Trebuchet MS / Avenir Next (lettering: Trebuchet MS) | Impact |
| pixel | Arial Black | Courier New / Menlo | Arial Black |
| bricks | Trebuchet MS / Avenir Next | Trebuchet MS / Avenir Next | Arial Black |
| boardgame | Georgia / Futura | Georgia | Arial Black |
| circuit | Arial / DIN Condensed | Arial / Avenir Next (labels: Courier New / Menlo) | Arial / DIN Condensed |
| topo | Georgia / Baskerville | Trebuchet MS / Avenir Next (labels: Trebuchet MS / Gill Sans) | Trebuchet MS / Avenir Next |
| scoreboard | Impact / DIN Condensed | Arial / Avenir Next Condensed | Impact / DIN Condensed |
| periodic | Arial / Helvetica Neue | Arial / Helvetica Neue (lines: Georgia italic) | Arial / Helvetica Neue |
| recipe | Georgia / Hoefler Text | Georgia (labels: Courier New) | Trebuchet MS |
| stainedglass | Georgia / Baskerville | Georgia (inscriptions: Georgia / Optima) | Times New Roman / Baskerville |
| calendar | Times New Roman / Didot | Arial / Avenir Next | Times New Roman / Didot |

The numerals column is the face of the `data` page's figure (collage draws a short one as an outlined shape).
Digits inside Georgia text — body or display — are set in Times New Roman, a lining face, and so are the digits
in editorial's Didot display under `fonts="mac"` (`k.runs` does this for you).

East-Asian faces follow the SCRIPT of each run — a Chinese face has no Hangul:

| script | serif (mac / win) | sans (mac / win) |
|---|---|---|
| Han (Chinese) | Songti SC / SimSun | Hiragino Sans GB / Microsoft YaHei |
| kana (Japanese) | Hiragino Mincho ProN / Yu Mincho | Hiragino Sans / Yu Gothic |
| Hangul (Korean) | AppleMyungjo / Batang | Apple SD Gothic Neo / Malgun Gothic |

The Windows faces come from Microsoft's documented defaults and are **unverified** here (the build machine
has no Windows renderer). On-demand macOS CJK faces (Kaiti SC, Yuanti SC, Hannotate SC, PingFang SC, …) are
never chosen. CJK runs are never italic; a collage CJK headline is bold (Impact has no CJK).

## CJK and Hangul copy

Checked by building pages and rendering them with `render_deck.py` (LibreOffice, 2026-10-09). PowerPoint was not
available to check.

- **Clause marks.** The full-width marks `，。、；：！？` are clause breaks anywhere in a field. ASCII `. , ; : ! ?`
  and the dashes `— –` are clause breaks only before a space: "宋代点茶: 一盏茶里…" breaks after the colon, but
  "宋代点茶:一盏茶里…" does not, and neither does "3.5". `ink`'s vertical columns break at full-width marks only.
- **Use full-width marks in Chinese and Japanese.** An ASCII mark inside CJK text renders with a gap on each side
  ("宋代点茶 : 一盏茶"). The kit does not measure that gap, so the line can grow past its box. Measured:
  "宋代点茶:一盏茶里的审美与日常生活" was planned as 2 lines and rendered as 3, with a lone "活" under the box.
- **No Latin letter straight before a full-width mark.** "心脏MRI：重建…" renders as "心脏 MRI ：", with a gap
  before the colon. End the clause on a CJK character ("心脏磁共振：…") or reword it. Never put full-width marks in
  Latin text: "broken：take" renders "broken ： take", and a title measured as one line rendered as two.
- **Korean: leave ASCII punctuation off titles and labels.** After Hangul, LibreOffice draws a gap before an ASCII
  mark ("고쳤습니다 .", "다 ,", "다 :"). PowerPoint may not. The gap widens the line past what the kit measured:
  "수리 카페의 저녁, 함께해요" was planned as one line and rendered as two, and the same title with no mark stayed
  on one. Full-width marks only partly help: "。" renders tight but is not Korean usage, and "，" and "：" still
  look spaced off. Prefer no mark at all.
- **A number and its counter can split across lines.** "修好了 12 / 个水壶", "コートを 12 / 着直しました",
  "외투 128 / 벌을" all rendered that way. Where it matters, break the line yourself: a typed `\n` before the number
  is kept as your own break.

## Record and gates

`python3 "$SKILL/scripts/visual_languages.py" --gates collage --ground slate --deck "$DECK" --for "a neighbourhood repair café"`
(`--ground` = the ground the deck was built on; the commands carry `deck_gates.py`'s full path, so they run as
printed from any folder; `auto` reads the canvas of the one built `.pptx` in `--deck` and
resolves as `use()` did — with no built deck it refuses, so pass the ground `use()` printed; a `--deck` with `<` or
`>` in it is refused as an unfilled template) prints the exact commands,
with that ground's own hex codes in the palette (the register-pixels gate holds a palette that never reached a
pixel, so never type them yourself). For a deck folder with no record yet it prints this, `init` first, because
`set` refuses a record that was never made:

```bash
python3 "$SKILL/scripts/deck_gates.py" init "$DECK"
python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.visual_language collage
python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.vl_fonts both
python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.vl_ground slate
python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.style_pick 'bespoke collage for a neighbourhood repair café'
python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.look_source bespoke
python3 "$SKILL/scripts/deck_gates.py" set "$DECK" design_plan.palette 'ground #2B2A27 ink #F4EEE2 accents #F2C230 #F08A64 #7CC3E3'
```

`init` runs once per deck: on a folder that already has a record it exits 2 and changes nothing (`--force`
overwrites it and discards what was recorded).

(Codex evidence: the same six values under `design` — `--gates` names them. An unknown `vl_ground` blocks.) The delivery gate on both runtimes then
checks that the cover was built with `cover()` and at least half the pages are in the language (its page
functions, or ordinary pages started with `k.new_slide()`), that its
display face is used, and that its prohibitions hold (`editorial` and `storybook` forbid confetti) — a
recorded language that was not applied blocks. The register notes name it a curated language whose kit
ships with the skill (nothing to scaffold or keep with `save_register.py`).

The register-pixels gate compares a deck's ground with the user's last decks (GROUND REPEAT, from the look
history). Build with `ground="auto"` and the language moves to its contrast ground when the light one would
repeat; if it still holds, rebuild on the other ground, or — when the repeat is the point (a series in one
house look) — record a written `design_plan.register_pixels_waived` saying so. Never repaint a ground by hand:
the ground, its grain, its card and its inks are one look, and the variants are what keep them together.

## Direction gate

`vl.direction(name)` returns a direction for `directions.json` with the language's tokens and its bundled
style sample (the preview shows it, labelled "style sample — not your content"). It counts as a STYLED
direction, never as the topic-invented bespoke direction the gate also requires. Image-led languages pair
with the P1 image series (`references/image-generation.md`, the SERIES exception) when the deck's images
are generated; with the user's own or fetched photos they need no generation at all. The <!-- vl:count-drawn -->twenty-six<!-- /vl --> native
languages need no pictures: a deck without any offers the one that fits its topic and records why in
`direction_gate.native_fit` (see Native languages above).
