# Visual languages — four complete image-led looks

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
  x, y, w, h = rs.ground(s, "editorial", role="content", index=2)   # furniture; returns the content rect
  body, header = rs.card(s, "editorial", x, y + 0.9, w, h - 1.0, label=None)  # SHAPES, not a rect
  dk.text(s, body.left.inches + 0.3, body.top.inches + 0.25, body.width.inches - 0.6, body.height.inches - 0.5,
          [k.runs("1.  Why a repair café", 20), k.runs("2.  How an evening runs", 20)])
  ```
  `rs.ground` returns the content rect `(x, y, w, h)` in inches; `rs.card` returns `(body, header)` —
  python-pptx shapes (`header` is None for a card with no band), so read `body.left.inches` and friends.
  `body` is the WHOLE card: with `label=…` the label sits inside its top, so start the content below it
  (`header.top.inches + header.height.inches`), or it lands on the label.
  Make every paragraph with `k.runs(text, size, color=None, bold=False, role="body")` (a list of runs; one
  run is `k.run(…)`): it picks the language's face and, for Chinese, Japanese or Korean text, that script's
  East-Asian face — never type a font name — and sets digits in a LINING face where the language's face has
  old-style figures (Georgia), so "Repair café 2026" never bobs.
- **Any canvas:** every page has a landscape and a portrait layout (portrait when W < 1.2 H).

## Grounds

Each language has its own light paper and ONE contrast ground; every text ink passes 4.5:1 on both:

| language | `light` | contrast ground |
|---|---|---|
| editorial | warm paper | `ink` — warm black, paper-white type, the same red |
| soft | cream | `dusk` — deep plum-indigo, the pastel blobs kept |
| collage | kraft | `slate` — dark grey paper, white prints, dark note cards |
| storybook | paper | `meadow` — green paper; the watercolours are tinted onto it, as if painted there |

`use(name, prs, ground=…)`: `"light"` (the default — the same deck on every machine), the contrast key, or
`"auto"` — the light ground unless the last three decks in your look history already sit on it (the
register-pixels GROUND REPEAT distance), then the contrast one; a printed board (A4, the A0/A1 posters) always
stays light, and no history means light. `auto` prints what it chose and the `--gates … --ground …` to record
it. `vl.direction(name, ground="auto")` shows the sample of that same ground, so the picked preview and the
built deck agree. `python3 scripts/visual_languages.py --list` lists every language's grounds.

## Fonts

`fonts="both"` (default) uses only faces present on macOS AND Windows, so the render matches what the
viewer opens. `fonts="mac"` unlocks Mac-only faces and refuses one that is not installed.

| language | display (both / mac) | body (both / mac) | numerals |
|---|---|---|---|
| editorial | Georgia / Didot | Arial / Helvetica Neue | Arial Black (lining) |
| soft | Trebuchet MS / Arial Rounded MT Bold | Trebuchet MS / Avenir Next | Trebuchet MS |
| collage | Impact / Impact (+ Bradley Hand accents on mac) | Arial / Avenir Next | Impact |
| storybook | Georgia / Baskerville | Georgia | Times New Roman (lining) |

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
(`--ground` = the ground the deck was built on; `auto` resolves as `use()` does) prints the exact commands,
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
are generated; with the user's own or fetched photos they need no generation at all.
