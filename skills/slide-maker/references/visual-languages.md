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
k = vl.use("collage", prs)                       # fonts="both" (default): faces on macOS AND Windows
k.cover(k.new_slide(), kicker="A repair café", title="Bring it broken", subtitle="Once a month",
        image=["<deck>/a.jpg", "<deck>/b.jpg", "<deck>/c.jpg"])     # collage cover: up to 4 images
k.section(k.new_slide(), number="02", kicker="How it works", title="We fix it with you")
k.image_text(k.new_slide(), kicker="What you find", title="Tools on every bench", body="…", image="<deck>/tools.jpg")
k.quote(k.new_slide(), quote="…", attribution="…")
k.data(k.new_slide(), number="1", label="evening a month", note="…")
k.closing(k.new_slide(), title="Bring one broken thing.", line="And bring a neighbour.", image="<deck>/table.jpg")
```

- **Pages:** `cover`, `section`, `image_text`, `quote`, `data`, `closing` — keyword fields only; `image=`
  is optional everywhere except `image_text`. Each returns `{"rects": {field: (x, y, w, h)}, …}`.
- **Images:** a file path (the user's photo, a fetched public-domain image), or — with
  `vl.use(name, prs, plan=plan, image_dir=…)` — a P1 image-series slot id (placed with `slot_picture`,
  so the series gate still sees it). A missing image raises `FileNotFoundError`.
- **Text that cannot fit** shrinks toward each field's floor size; if even the floors overflow, the page
  raises `vl.VLTextOverflow` naming the page, the field and the inches — shorten the copy, never
  truncate it. Titles never end in a lone word or one or two CJK characters (shrunk a little, or set in
  a balanced measure).
- **Ordinary pages in the same look** (agenda, bullets, charts): `k.new_slide()` gives the language's
  ground; `rs.card(slide, "<name>", x, y, w, h, label=…)` gives its card; `rs.ground(slide, "<name>",
  role=…)` its furniture and content rect.
- **Any canvas:** every page has a landscape and a portrait layout (portrait when W < 1.2 H).

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

```bash
python3 scripts/deck_gates.py set <deck> design_plan.visual_language collage
python3 scripts/deck_gates.py set <deck> design_plan.vl_fonts both
python3 scripts/deck_gates.py set <deck> design_plan.style_pick "bespoke collage for a neighbourhood repair café"
python3 scripts/deck_gates.py set <deck> design_plan.look_source bespoke
```

(Codex evidence: the same two fields under `design`.) Put the language's hex codes in
`design_plan.palette` so the register-pixels gate can find them. The delivery gate on both runtimes then
checks that the cover and at least half the pages were built with the language's page functions, that its
display face is used, and that its prohibitions hold (`editorial` and `storybook` forbid confetti) — a
recorded language that was not applied blocks.

## Direction gate

`vl.direction(name)` returns a direction for `directions.json` with the language's tokens and its bundled
style sample (the preview shows it, labelled "style sample — not your content"). It counts as a STYLED
direction, never as the topic-invented bespoke direction the gate also requires. Image-led languages pair
with the P1 image series (`references/image-generation.md`, the SERIES exception) when the deck's images
are generated; with the user's own or fetched photos they need no generation at all.
