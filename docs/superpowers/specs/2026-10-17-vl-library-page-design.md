# Visual-language library page — design

Date: 2026-10-17 · Status: approved in chat (four choices + the design), awaiting review of this document
Repos: `addsumtech/slides_maker` (exporter, manifest field) · `addsumtech/slides_maker-site` (the page)

## Goal

A page on slides.addsum.top that shows and explains slide-maker's visual-language library — today fifteen
languages — so a visitor can see each look, understand what it is for and how to ask for it, and so the library
can grow: a sixteenth language reaches the page by re-running one command, with nothing hand-edited on the site.

Modelled on the video-shotcraft library page (a data-driven card grid with search, filters, a language toggle, a
stats row and a NEW badge), adapted to what a visual language is: a complete look with two grounds and seven page
compositions, not a single motion recipe.

## Decisions taken with the user

| Question | Decision |
|---|---|
| How deep per language | Cards **and** a detail view; the detail view shows all seven page types, freshly rendered, on both grounds |
| Entry from the existing site | **None.** The page lives at its own URL; `index.html`, `cn/`, `viewer.html`, `decks.js` and `templates/` are not touched |
| How the page learns about a new language | An **exporter in the skill repo**, one command, writes the page's data and images from the language manifests |
| Look of the page | The site's existing look: paper ground, ink type, vermilion accent (`--paper #f6f2ea`, `--ink #1d1b16`, `--accent #b13a24`, …) |
| Seven page types: whose content | **One shared demo content** for every language (the skill's own repair-café example with its bundled pictures), so languages compare on identical words and a new language needs no extra copy |
| sitemap.xml | One added URL line for the new page (the only file outside `languages/` the site commit touches) |

## Isolation

Everything the page needs lives under `slides_maker-site/languages/`:

```
languages/
  index.html          the page (EN/中文 toggle inside, no separate /cn/ copy)
  library.css         its styles — tokens copied from the site's :root, nothing imported from index.html
  library.js          rendering, filters, search, detail view, i18n strings
  library.json        the data, written by the exporter — never edited by hand
  media/<id>/sample-<ground>.jpg        the language's own four-page sample sheet, per ground
  media/<id>/<ground>/<page>.jpg        the seven page types, per ground
```

The exporter refuses to write anything outside `<site>/languages/`. The site commit adds `languages/` and one
`<url>` in `sitemap.xml`; a check in the exporter's test asserts that no other site path is written.

## The page

**Header.** Site wordmark linking to `/`, the page title (Visual-language library / 视觉语言模版库), an EN/中文
toggle (remembered in `localStorage`, defaulting to the browser language), a link to the GitHub repo.

**Hero.** One paragraph on what a visual language is — a complete, checked look: two designed grounds, a type
pairing that works in Latin and CJK, seven page compositions, and every general component (charts, timelines,
tables …) wearing it — then a stats row computed by the exporter: languages · grounds · page types · components held
to every ground (today 15 · 30 · 7 · 38). No number on the page is typed by hand.

**Controls.** A search box (matches id, both names, blurb, best-for topics, in the active language) and a kind
filter: All · Image-led · Drawn. Clicking a best-for tag on a card searches for it. An empty state with "clear
filters". Filter state is mirrored in the URL query so a filtered view can be linked.

**Card (one per language, in manifest `order`).**
- the language's four-page sample sheet, with a ground switch (its two ground labels, e.g. 宣纸版 / 墨夜版);
- name (`display` in the active language), the id in code type (`ink`), a kind badge;
- the blurb (two short sentences);
- best-for topics as tags; the active ground's palette as swatches;
- **Copy prompt** — copies one sentence an agent understands, e.g. "Use the ink (Ink wash) visual language for this
  deck." / "用 ink（水墨）视觉语言做这份 PPT。";
- a NEW badge while `added_at` is within 30 days;
- the card opens the detail view.

**Detail view** (a dialog, deep-linkable as `#ink`, closable with Esc, focus-trapped):
- the seven page types — cover, section, image & text, points, quote, data, closing — on the active ground, with the
  ground switch; each image captioned with the page type;
- the language's own sample sheets (both grounds) — the look on its own topic;
- palette per ground (ground, ink, mute, accents); fonts (cross-platform `both` set, the macOS set, the CJK faces);
- the words only the caller gives (`extras`: e.g. `seal=` — 1–4 characters for the seal) and the words the language
  writes itself (`derived`);
- how to use it: the prompt sentence and the Python line (`k = vl.use("ink", prs)`), each with a copy button, and a
  link to `references/visual-languages.md` on GitHub.

**Behaviour.** Plain HTML/CSS/JS, no build step and no third-party script, like the rest of the site. Images
lazy-load. Works from 390px wide (one column, the sample sheet full width) to wide screens (three columns).
Keyboard: cards are buttons; the dialog traps focus and returns it. Respects `prefers-reduced-motion`.

## Data — `library.json`

```json
{
  "schema": 1,
  "generated": "2026-10-17",
  "skill_version": "5.9.0",
  "stats": {"languages": 15, "grounds": 30, "page_types": 7, "components": 38},
  "page_types": [{"id": "cover", "name": {"en": "Cover", "zh": "封面"}}, …],
  "languages": [{
    "id": "ink", "order": 5, "kind": "drawn", "added_at": "2026-10-17",
    "name": {"en": "Ink wash", "zh": "水墨"},
    "blurb": {"en": "…", "zh": "…"},
    "best_for": {"en": ["culture", "history", "craft"], "zh": ["文化", "历史", "器物"]},
    "grounds": [{"id": "light", "label": {"en": "xuan paper", "zh": "宣纸版"}, "dark": false,
                 "swatches": {"ground": "F0E6CE", "ink": "1C1A17", "mute": "…", "accents": ["BE2E1A"]},
                 "sample": "media/ink/sample-light.jpg",
                 "pages": {"cover": "media/ink/light/cover.jpg", …}}, …],
    "fonts": {"both": {…}, "mac": {…}, "cjk": {…}},
    "image_pages": ["image_text"],
    "extras": [{"name": "seal", "pages": "any", "takes": "1-4 characters for the seal"}],
    "derived": [{"id": "point_numbers", "what": "…"}],
    "usage": {"prompt": {"en": "…", "zh": "…"}, "python": "k = vl.use(\"ink\", prs)"}
  }, …]
}
```

Every field comes from the manifest or the registry; the exporter computes `stats`. `added_at` is the date a
language first appeared in an export: re-exporting keeps it, a new id gets the export date (this drives NEW).

## The exporter — `skills/slide-maker/scripts/vl_library_export.py`

```
python3 scripts/vl_library_export.py --site ~/code_project/slides_maker-site            # data + images
python3 scripts/vl_library_export.py --site … --no-render                               # data + sample sheets only
python3 scripts/vl_library_export.py --site … --check                                   # exit 1 if the page is stale
```

1. Load the registry (drafts excluded) and the previous `library.json` if any (for `added_at`).
2. For each language: build the JSON entry; copy `assets/vl/samples/<stem>.jpg` for each ground to
   `media/<id>/sample-<ground>.jpg`.
3. Unless `--no-render`: build one seven-slide deck per language per ground from the shared demo content (cover,
   section, image_text, points, quote, data, closing — pictures only on the pages that language draws pictures on,
   from the bundled photo or watercolour set), render it with `render_deck.py` into a scratch folder, and write each
   slide as a 960px JPEG to `media/<id>/<ground>/<page>.jpg`. A page a language refuses is a hard error that names
   the language and page — the exporter never ships a partial set.
4. Write `library.json` (sorted keys, stable order) and print what changed: new languages, removed languages,
   changed grounds — the line the maintainer reads before committing the site.
5. `--check` recomputes the JSON (without rendering) and compares: a language added to the skill but not exported is
   reported by name.

The shared demo content is a constant in the exporter (English; the zh page shows the same renders — the look, not
the words, is what a visitor compares).

## The manifest gains `blurb`

`SPEC["blurb"] = {"en": "<1–2 sentences for visitors>", "zh": "<同上>"}` — public-facing, plainer than `rationale`
(which stays the author's technical line). `vl_contract.validate` requires it on every non-draft language (en ≥ 40
characters, zh ≥ 12), `new_visual_language.py` writes it as a `FILL:` decision, and
`references/visual-language-authoring.md`'s field table gains the row. The fifteen manifests get their blurbs in the
same change — written from each language's rationale, offer topics and samples, describing the look and what it suits,
with no claim beyond what the language draws.

## Testing

- **Skill repo — `tests/test_vl_library_export.py`** (CI step, inventory entry): run `--no-render` into a temp
  site; assert the schema, one entry per registry language in `order`, stats equal to the registry's counts, every
  referenced sample file present, `added_at` preserved on a re-export and set for a new id, `--check` failing on a
  stale page and naming the language, and nothing written outside `languages/`. The contract test gains the `blurb`
  cases (missing, too short, unfilled).
- **Render path** — one language exported with rendering in the test (`--only ink`), asserting fourteen page images
  (seven per ground), each a real JPEG of the expected size.
- **Page** — `slides_maker-site/tools/check_languages_page.py`: headless Chrome loads the page from a local server;
  asserts fifteen cards, the ground switch swaps the sheet, search and the kind filter narrow the grid, `#ink` opens
  the dialog with seven page images, the 中文 toggle swaps names and blurbs, and the console has no errors. Run at
  1400px and at a true 390px (inside an iframe — headless Chrome's minimum window is wider), with screenshots that are
  looked at before committing.

## Publishing

Both repos commit locally. Pushing the site publishes it (GitHub Pages serves `main`), so the site push and the
skill push each wait for the user's word.

## Out of scope

Any change to the existing gallery, viewer or home page; per-language copy for the seven page types; analytics;
a server-side API; video previews.
