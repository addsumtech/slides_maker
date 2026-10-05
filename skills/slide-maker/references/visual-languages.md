# Visual languages — eight complete looks: four image-led, four drawn

**When to read this:** the picked direction is a visual language (its entry in `directions.json` carries
`"vl": "<name>"`), or the user asks for one of these looks by name. Read it before writing the build script.

A visual language is a whole look, not a palette: a type voice from system fonts, a surface, image
treatments and six page compositions. Picking one gives a finished deck from your own words and images —
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

## Build

```python
import sys
sys.path.insert(0, "<skill>/scripts")
import deckkit as dk
import register_surface as rs
import visual_languages as vl

prs = dk.blank_deck(13.333, 7.5)
k = vl.use("collage", prs, ground="auto")       # fonts="both" (default): faces on macOS AND Windows;
                                                 # ground="auto": light, or the contrast ground after cream decks
k.cover(k.new_slide(), kicker="A repair café", title="Bring it broken", subtitle="Once a month",
        image=["<deck>/a.jpg", "<deck>/b.jpg", "<deck>/c.jpg"])     # collage cover: up to 4 images
k.section(k.new_slide(), number="02", kicker="How it works", title="We fix it with you")
k.image_text(k.new_slide(), kicker="What you find", title="Tools on every bench", body="…", image="<deck>/tools.jpg")
k.quote(k.new_slide(), quote="…", attribution="…")
k.data(k.new_slide(), number="1", label="evening a month", note="…")
k.closing(k.new_slide(), title="Bring one broken thing.", line="And bring a neighbour.", image="<deck>/table.jpg")
```

- **Pages:** `cover`, `section`, `image_text`, `quote`, `data`, `closing` — keyword fields only; `image=`
  is optional everywhere except `image_text` (which refuses without one). A list of images is for the
  collage cover and closing only (1 to 4); anywhere else, or empty, or longer, it is refused rather than
  silently cut. A page with no text and no image is refused. Each returns `{"rects": {field: (x, y, w, h)}, …}`.
- **Images:** a file path (the user's photo, a fetched public-domain image), or — with
  `vl.use(name, prs, plan=plan, image_dir=…)` — a P1 image-series slot id (placed with `slot_picture`,
  so the series gate still sees it). A missing image raises `FileNotFoundError`.
- **Text that cannot fit** shrinks toward each field's floor size; if even the floors overflow, the page
  raises `vl.VLTextOverflow` naming the page, the field and the inches — shorten the copy, never
  truncate it. A single token wider than the column even at the floor (a code identifier, a URL) is
  refused the same way, naming the word; a long Korean compound breaks between syllables instead. Titles never end in a lone word or one or two CJK characters (shrunk a little, or set in
  a balanced measure). A title, quote, label or line with clause punctuation INSIDE it breaks after its
  clauses when they fit ("带着坏东西来，/ 带着好东西走", "Bring it broken. / Take it home working.") —
  at down to 0.7x its size, never with more lines, set as one paragraph per line.
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
  `k.points(...)` on ink, poster and cutpaper; on drafting, `points` draws one plate per item, so keep an agenda
  there as this ordinary page.)
  Pass `k.name` — the page's OWN language; another language's name on it is refused. `rs.ground` returns the
  content rect `(x, y, w, h)` in inches; `rs.card` returns `(body, header)` —
  python-pptx shapes (`header` is None for a card with no band), so read `body.left.inches` and friends.
  `body` is the WHOLE card: with `label=…` the label sits inside its top, so start the content below it
  (`header.top.inches + header.height.inches`), or it lands on the label.
  Make every paragraph with `k.runs(text, size, color=None, bold=False, role="body")` (a list of runs; one
  run is `k.run(…)`): it picks the language's face and, for Chinese, Japanese or Korean text, that script's
  East-Asian face — never type a font name — and sets digits in a LINING face where the language's face has
  old-style figures (Georgia), so "Repair café 2026" never bobs.
- **Any canvas:** every page has a landscape and a portrait layout (portrait when W < 1.2 H). A storybook page given a
  PORTRAIT illustration (width/height < 0.85) takes its tall frame — beside the text on a landscape slide, taller on a
  portrait one — so the picture is not shrunk into a frame drawn for a landscape one.
- **A data page with no picture** sets the figure big — about 60% of the column's height on a landscape slide, with
  the label and note beside it; stacked below it on a portrait one — never wider than half the column, so a long
  number shrinks rather than crowding the label.
- **Screen readers:** every page declares its title with `deckkit.a11y_title` (the quote page: the quote; the data
  page: number + label) — first in reading order, above the canvas, nothing drawn — so a kicker set above the title
  never trips READING ORDER. Ordinary `k.new_slide()` pages need their own title (or `dk.a11y_title`).

## Native languages — drawn, no pictures needed

`ink` (水墨), `poster` (海报大字), `cutpaper` (剪纸层叠) and `drafting` (蓝图技术线稿 — named `drafting` because
`blueprint` is a preset) draw their own surface with native, editable shapes (`scripts/native_art.py`), so they
make a finished deck for a talk with no pictures and no image tool. Everything they draw stays on the page, and
every value they write is one PowerPoint opens without repair (`scripts/ooxml_safety.py`, which `lint_deck` runs).

- **`points`** — `k.points(s, kicker=…, title=…, items=[("Head", "line"), …])`: 2 to 4 points, each a string, a
  `(head, line)` pair or a `{"head": …, "line": …}` dict. Native languages only; on the image-led four, build
  the list on an ordinary `k.new_slide()` page (`rs.ground` + `rs.card`).
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
  character or word on the last line; Latin is set in capitals; a figure (`1,250,000`) stays on one line.
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
  `native_fit.language` is one of the native languages among the candidates (not necessarily the one picked). Guidance, not a rule: culture, history, craft → `ink`; launch, manifesto, brand, opinion →
  `poster`; children, teaching, workshop, community → `cutpaper`; research, engineering, technical → `drafting`.

## Grounds

Each language has its own light paper and ONE contrast ground; every text ink passes 4.5:1 on both:

| language | `light` | contrast ground |
|---|---|---|
| editorial | warm paper | `ink` — warm black, paper-white type, the same red |
| soft | cream | `dusk` — deep plum-indigo, the pastel blobs kept |
| collage | kraft | `slate` — dark grey paper, white prints, dark note cards |
| storybook | paper | `meadow` — green paper; the watercolours are tinted onto it, as if painted there |
| ink | xuan paper | `night` — ink-black paper, pale ridges, a moon for the sun |
| poster | colour fields (cobalt, lime, black, signal orange, one per page) | `paper` — off-white and black fields, cobalt accents |
| cutpaper | day | `night` — navy sky, a paper moon, dark hills |
| drafting | vellum | `cyanotype` — blueprint navy, pale linework |

`use(name, prs, ground=…)`: `"light"` (the default — the same deck on every machine), the contrast key, or
`"auto"` (this machine's look history, across every deck built here — pass the ground yourself when the topic
asks for one, e.g. a children's lesson on light paper) — the light ground unless the last three decks in your look history already sit on it (the
register-pixels GROUND REPEAT distance), then the contrast one; a printed board (A4, the A0/A1 posters) always
stays light, and no history means light. `auto` prints what it chose and the `--gates … --ground …` command that
records it (fill in its `DECK_DIR` and `TOPIC`). `vl.direction(name, ground="auto", W=…, H=…)` — the deck's canvas in
inches, 13.333 x 7.5 by default — shows the sample of that same ground, so the picked preview and the built deck agree. `python3 scripts/visual_languages.py --list` lists every language's grounds.

## Fonts

`fonts="both"` (default) uses only faces present on macOS AND Windows, so the render matches what the
viewer opens. `fonts="mac"` unlocks Mac-only faces and refuses one that is not installed.

| language | display (both / mac) | body (both / mac) | numerals |
|---|---|---|---|
| editorial | Georgia / Didot | Arial / Helvetica Neue | Arial Black (lining) |
| soft | Trebuchet MS / Arial Rounded MT Bold | Trebuchet MS / Avenir Next | Trebuchet MS |
| collage | Impact / Impact (+ Bradley Hand accents on mac) | Arial / Avenir Next | Impact |
| storybook | Georgia / Baskerville | Georgia | Times New Roman (lining) |
| ink | Georgia / Baskerville | Georgia | Times New Roman (lining) |
| poster | Impact | Arial / Helvetica Neue (meta: Courier New) | Impact |
| cutpaper | Trebuchet MS / Avenir Next | Trebuchet MS / Avenir Next | Trebuchet MS |
| drafting | Georgia | Georgia (labels and title block: Courier New) | Times New Roman (lining) |

East-Asian faces follow the SCRIPT of each run — a Chinese face has no Hangul:

| script | serif (mac / win) | sans (mac / win) |
|---|---|---|
| Han (Chinese) | Songti SC / SimSun | Hiragino Sans GB / Microsoft YaHei |
| kana (Japanese) | Hiragino Mincho ProN / Yu Mincho | Hiragino Sans / Yu Gothic |
| Hangul (Korean) | AppleMyungjo / Batang | Apple SD Gothic Neo / Malgun Gothic |

The Windows faces come from Microsoft's documented defaults and are **unverified** here (the build machine
has no Windows renderer). On-demand macOS CJK faces (Kaiti SC, Yuanti SC, Hannotate SC, PingFang SC, …) are
never chosen. CJK runs are never italic; a collage CJK headline is bold (Impact has no CJK).

## Record and gates

`python3 scripts/visual_languages.py --gates collage --ground slate --deck <deck> --for "a neighbourhood repair café"`
(`--ground` = the ground the deck was built on; the commands carry `deck_gates.py`'s full path, so they run as
printed from any folder; `auto` reads the canvas of the one built `.pptx` in `--deck` and
resolves as `use()` did — with no built deck it refuses, so pass the ground `use()` printed) prints the exact commands,
with that ground's own hex codes in the palette (the register-pixels gate holds a palette that never reached a
pixel, so never type them yourself):

```bash
python3 scripts/deck_gates.py set <deck> design_plan.visual_language collage
python3 scripts/deck_gates.py set <deck> design_plan.vl_fonts both
python3 scripts/deck_gates.py set <deck> design_plan.vl_ground slate
python3 scripts/deck_gates.py set <deck> design_plan.style_pick "bespoke collage for a neighbourhood repair café"
python3 scripts/deck_gates.py set <deck> design_plan.look_source bespoke
python3 scripts/deck_gates.py set <deck> design_plan.palette "ground #… ink #… accents #… #…"   # from --gates
```

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
are generated; with the user's own or fetched photos they need no generation at all. The four native
languages need no pictures: a deck without any offers the one that fits its topic and records why in
`direction_gate.native_fit` (see Native languages above).
