# Visual-language library page — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A page at slides.addsum.top/languages/ that shows every visual language (sample sheets, seven freshly
rendered page types per ground, palette, fonts, how to ask for it), fed by one exporter command in the skill repo.

**Architecture:** The skill repo owns the data: each manifest gains a public `blurb`, and
`scripts/vl_library_export.py` turns the registry into `languages/library.json` plus images inside the site repo.
The site repo owns presentation only: a static `languages/` folder (HTML + CSS + JS, no build, no third-party
script) that renders whatever `library.json` lists.

**Tech Stack:** Python 3 + python-pptx + LibreOffice (`render_deck.py`) + Pillow; plain HTML/CSS/JS; headless
Chrome for the page check.

**Spec:** `docs/superpowers/specs/2026-10-17-vl-library-page-design.md`

## Global Constraints

- The exporter writes only under `<site>/languages/`; the site commit touches `languages/` and one `<url>` in `sitemap.xml`.
- No number on the page is typed by hand: stats come from the registry (today 15 · 30 · 7 · 38).
- Site tokens: `--ink #1d1b16; --paper #f6f2ea; --mute #7a7263; --accent #b13a24; --accent-deep #93301e; --line #e0d9cb; --card #fdfbf5; --tint #f2e5dc`.
- `blurb`: `{"en": ≥40 chars, "zh": ≥12 chars}`, required by `vl_contract.validate`; nothing claimed beyond what the language draws.
- One shared demo content for the seven page types; a refused page is a hard error naming language + page.
- Page images 960px JPEG; works from 390px to wide; keyboard + `prefers-reduced-motion`.
- Both repos commit locally; the site push and the skill push each wait for the user.
- Stage named paths only; never `git add -A`.

## Review Focus

1. A 16th language with three grounds, or a ground id never seen before — the page must lay out any count of grounds, not two.
2. A language removed from the skill — its `media/<id>/` must go, and `--check` must name it.
3. `--no-render` on a site that already holds renders — page links must keep pointing at the files that exist, never at missing ones.
4. A deep link to `#nosuch` or a stale `?kind=` value — the page must ignore it, not throw.
5. The first export — every language present then must not wear NEW (all fifteen are under 30 days old today).

---

### Task 1: the manifest `blurb`

**Files:**
- Modify: `skills/slide-maker/scripts/vl_contract.py` (validate: a blurb check after the rationale check)
- Modify: `skills/slide-maker/scripts/new_visual_language.py:44` (write `blurb` as a FILL decision)
- Modify: `skills/slide-maker/references/visual-language-authoring.md:51` (field table row)
- Modify: `skills/slide-maker/scripts/vl_specs/*.py` (15 blurbs)
- Test: `skills/slide-maker/tests/test_vl_contract.py` (fixture gains a blurb; missing / too short / unfilled cases)

**Interfaces:** Produces `SPEC["blurb"] = {"en": str, "zh": str}` on every registry language.

- [ ] Step 1: add the three failing cases to test_vl_contract.py (a spec without `blurb` → a problem naming `blurb`;
  `en` of 10 chars → a problem; `"FILL: …"` → reported by `unfilled`) and the fixture's blurb.
- [ ] Step 2: run `python3 tests/test_vl_contract.py` → the three cases FAIL.
- [ ] Step 3: in `validate`, after the rationale check:
  ```python
  b = spec.get("blurb")
  if not (isinstance(b, dict) and isinstance(b.get("en"), str) and len(b["en"].strip()) >= 40
          and isinstance(b.get("zh"), str) and len(b["zh"].strip()) >= 12):
      probs.append("{}: blurb needs 'en' (40+ characters) and 'zh' (12+) — one or two plain sentences a visitor "
                   "reads on the library page".format(name))
  ```
  Not added to `TOP_KEYS` (the loader refuses a manifest missing a TOP_KEY, which would brick every importer for a
  field only the exporter reads). Generator: `s["blurb"] = {"en": FILL + " …", "zh": FILL + " …"}`.
- [ ] Step 4: write the 15 blurbs from each rationale, offer topics and sample sheet; run the contract test and
  `python3 scripts/vl_contract.py` (every manifest) → PASS.
- [ ] Step 5: commit `vl: every language carries a public blurb`.

### Task 2: the exporter

**Files:**
- Create: `skills/slide-maker/scripts/vl_library_export.py`
- Test: `skills/slide-maker/tests/test_vl_library_export.py`
- Modify: `.github/workflows/ci.yml` (one step), `skills/slide-maker/references/file-inventory.md` (one entry)

**Interfaces:**
- Produces: `export(site, *, render=True, only=None, today=None) -> dict` (the written JSON),
  `check(site) -> list[str]` (stale reasons; empty = fresh), `demo_deck(name, ground, out_pptx) -> Path`,
  CLI `--site DIR [--no-render] [--only ID …] [--check] [--today YYYY-MM-DD]`.
- `library.json` (schema 1): `schema, generated, baseline, skill_version, stats{languages,grounds,page_types,components},
  page_types[{id,name{en,zh}}], languages[{id, order, kind, added_at, name, blurb, best_for, grounds[{id, label{en,zh},
  dark, swatches{ground,ink,mute,panel,accents,text_accents}, sample, pages{<page>: path}, render_fp, python}], fonts{both,
  mac, cjk{display,body,faces}}, image_pages, extras[{name,pages,takes}], derived[{id,what}], usage{prompt{en,zh}, python}}]`.

Rules the code holds:
- Writes resolve under `<site>/languages/` (asserted per path); `media/<id>/` of a language no longer in the registry is removed.
- `added_at`: kept from the previous JSON; a new id gets `today`. `baseline`: the previous JSON's, else `today`.
  The page shows NEW only when `added_at > baseline` and within 30 days — the first export marks nobody NEW.
- `pages` lists only files present after the run; `render_fp` = `visual_languages.sample_fingerprint` of the demo deck
  the pages were rendered from (kept from the previous JSON on `--no-render`).
- `--check` recomputes the JSON without rendering and reports, by language: added, removed, changed data, sample
  sheet bytes differing, or a demo-deck fingerprint differing from `render_fp` (stale renders). `generated` ignored.
- Demo content: the repair-café copy on the bundled photos; storybook (an illustration language) gets the
  balcony-garden copy on the bundled watercolours, because repair-café words over garden paintings would misstate the look.

- [ ] Step 1: write the failing test: `--no-render` into a temp site → schema 1, ids in registry `order`, stats equal
  registry counts (len, sum of grounds, 7, `len(component_tiers.TIER1)`), every `sample` file present, nothing outside
  `languages/`; a planted `media/ghost/` removed; re-export keeps a hand-set `added_at`; deleting one entry from the
  JSON → re-export sets it to `--today`; `--check` on the fresh site → exit 0; after editing a blurb in the JSON →
  exit 1 naming the language; a site path that is a file → refused; an unknown `--only` id → refused.
- [ ] Step 2: run it → FAIL (no module).
- [ ] Step 3: implement data + samples + `--check`.
- [ ] Step 4: run it → PASS.
- [ ] Step 5: render path: `demo_deck` + render each ground with `render_deck.py` into a scratch dir, write
  `media/<id>/<ground>/<page>.jpg` at 960px; a refused page raises naming `<id>.<page>`. Test (`--only ink`, skipped
  with a printed reason when LibreOffice is absent): 14 JPEGs, each 960px wide and 16:9; JSON `pages` lists them.
- [ ] Step 6: CI step + inventory entry; commit `vl_library_export: the library page's data and images in one command`.

### Task 3: the page

**Files (site repo):** Create `languages/index.html`, `languages/library.css`, `languages/library.js`,
`tools/check_languages_page.py`; generated `languages/library.json` + `languages/media/`; modify `sitemap.xml`.

**Interfaces:** Consumes `library.json` exactly as Task 2 writes it.

- [ ] Step 1: write `tools/check_languages_page.py`: serve the site on 127.0.0.1, load a harness that iframes
  `/languages/` at 1400 and 390px and asserts: cards == `len(languages)`; ground switch swaps the sheet `src`; search
  `ink` narrows to 1; kind filter Drawn → count of drawn; `#ink` opens the dialog with 7 page images per ground;
  中文 toggle changes the first card's name to its zh name; `#nosuch` throws nothing; no console error; no horizontal
  scroll at 390 (`scrollWidth <= innerWidth`); screenshots to a folder.
- [ ] Step 2: run it → FAIL (no page).
- [ ] Step 3: write the page (header, hero + stats, controls, grid, dialog; i18n table; URL state).
- [ ] Step 4: run the exporter into the site, run the check → PASS; open the screenshots and look.
- [ ] Step 5: sitemap line; commit in the site repo `Add the visual-language library page`.

### Task 4: README links

- [ ] Under the visual-language block of `README.md` and `README_CN.md` (after the samples caption paragraph): one
  line linking `https://slides.addsum.top/languages/`. Run `python3 scripts/check_doc_commands.py` if it reads README.
- [ ] Commit `README: link the visual-language library page`.
