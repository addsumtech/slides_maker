# Authoring a visual language

How to add a sixteenth language to slide-maker, and the rules the first fifteen taught. To *use* a language in a
deck, read `references/visual-languages.md` instead; to see one language at a glance, run
`python3 scripts/visual_languages.py --describe <name>`.

A language is **two files**, and nothing else in the skill is edited by hand while you build it:

| File | Holds | Read by |
|---|---|---|
| `scripts/vl_specs/<name>.py` | the **manifest**: one `SPEC` dict — names, grounds and colours, faces, type scale, skin, extras, derived words, sample copy | everything that needs data (`visual_languages.py`, the docs, the direction offer, the contract) |
| `scripts/vl_langs/<name>.py` | the **code**: `_ground_<name>` (an ordinary page's furniture), `_card_<name>`, and the seven page compositions | `vl_native.py` loads every module there |

Both folders are discovered: a new file is the whole registration. A half-made language never breaks the others — a
manifest whose code is missing (or does not import) is listed as *not ready*, and a manifest still holding a
`FILL:` decision is a *draft*, left out of every ordinary load. Both are named by `check_vl_contract.py`.

## The steps, in order

1. **Start it.** `python3 scripts/new_visual_language.py <name> --like <drawn language>` writes both files. The
   manifest is the model language's with every decision that makes your language *itself* replaced by
   `"FILL: <what to decide>"`; the module has a working ground painter, the card and one stub per page. It prints
   the next command.
2. **Decide the manifest.** `python3 scripts/check_vl_contract.py <name>` names every `FILL:` by its path
   (`grounds.night.palette.accents[0] is not filled — …`). Decide them all; then the same command checks contrast,
   series colours, the type floors and distinctiveness (next section).
3. **Compose the pages.** The check now names each page that is still a stub. Replace each with a composition
   (section "Composing a page"). Run the check after each one.
4. **Show the user.** Build the pages on both grounds, with short and long copy, render them, and show the sheets
   before anything ships. A language the user has not seen is not finished.
5. **Ship it.** What is left, the check names, one line each:
   - the bundled samples — `python3 scripts/visual_languages.py --sample <dir> --refresh-bundled`, then every printed
     `NEXT:` and `then:` line, on macOS (`assets/vl/README.md`);
   - a `vl_<name>` scaffold in `scripts/sigs.py`'s `EXAMPLES`;
   - its row in the table of `references/visual-languages.md` (`| \`<name>\` | …`);
   - its place in the library section of slides.addsum.top (#languages): `python3 scripts/vl_library_export.py --site
     <slides_maker-site> --only <name>`, then `--check`. The README gallery is a fixed showcase of twelve,
     generated from `SHOWCASE` in `scripts/vl_docs.py` — a new language gets no cell there; the README's counts ("N more are only in the library") follow from `vl_docs.py --write`;
   - the generated lists and counts: `python3 scripts/vl_docs.py --write`, then `--check`.
6. **Run the suites.** `python3 scripts/check_vl_contract.py <name>` prints no problem, then the `NEXT:` line it
   prints (`tests/test_vl_contract.py`), and the full CI before anything is pushed.

## The manifest, field by field

`scripts/vl_contract.py` checks every row; its message names the field.

| Field | What it is | The rule |
|---|---|---|
| `name` | the language's id | lowercase letters, digits or `_`; equals the file's stem |
| `order` | its place in every list | an int no other language uses |
| `kind` | `"drawn"` (words alone) or `"image-led"` | a new language is drawn: image-led ones compose through `visual_languages.LAYOUTS`, not a module |
| `display` | `{"en": …, "zh": …}` | both non-empty |
| `rationale` | one line: what it looks like, which decks it fits | at least a short sentence |
| `blurb` | `{"en": …, "zh": …}`: one or two plain sentences a visitor reads in the library section of slides.addsum.top (#languages) | en ≥ 40 characters, zh ≥ 12; describe what the language draws and what it suits, nothing more |
| `offer` | drawn: `{"en": [topics], "zh": [topics]}` | at least two topics per script — the direction offer matches decks to these |
| `look` | `palette` (the light ground's, one object), `fonts` (`both` and `mac`: `display`, `body`, `numeral`…), `ea` (the CJK face kind per role), `grain`, `frames`, `forbids`, `cover`, `skeleton` | all present |
| `grounds` | `light` (the key callers pass) and at least one contrast ground, each `{label, label_zh, palette, roles, dark}` | below |
| `grounds.*.palette` | `ground`, `ink`, `mute`, `panel`, `accents` [list], `text_accents` [list], plus any colour your code reads | hex `RRGGBB`; ink and mute ≥ 4.5:1 on the ground |
| `grounds.*.roles` | `card`, `card_ink`, `rule`, `on_accent`, `series` [≥ 4], `highlight` | card_ink ≥ 4.5:1 on card; on_accent ≥ 3:1 on accents[0]; every series colour ≥ 3:1 on ground and on card, and ΔE ≥ 20 from the others |
| `grounds.*.dark` | `True` / `False` | must match the palette (ink lighter than ground ⇒ dark) |
| `type` | role → `(size, face role, bold, colour key, italic, floor)` | every core role present (`kicker` `title` `subtitle` `body` `quote` `attribution` `number` `label` `note` `caption` `line` `item_head` `item_line`); floor ≤ size; a core role's size ≥ 12pt, a private role's ≥ 10pt; the attribution's **floor** ≥ 12pt |
| `skin` | one value per role: `card`, `rule`, `marker`, `number` | from `vl_contract.SKIN_VOCAB` — this is how charts and diagrams wear the language |
| `image_pages` | pages that take a picture | a tuple of page names (a drawn language usually `("image_text",)`) |
| `extras` | words only the caller gives (`masthead=`, `tags=` …): `{pages, remembered, takes, absent}` each | `pages` is `"any"` or a tuple; `remembered` says whether the deck keeps it; an extra name means one thing across all languages |
| `derived` | the few words the language writes itself: `[{id, what, words: {script: [words]}}]` | everything else on a page is the caller's |
| `samples` | drawn: `{"copy": [(page, fields), …]}` | one of each page, on a topic the language is offered for |
| `painters` | `{"ground": "_ground_<name>", "card": "_card_<name>"}` | exactly these names, defined in the module |

Across languages: two languages whose ground and first accent are close (ΔE of the grounds + ΔE of the accents, +10
for a different display face, under `DISTINCT_MIN` = 15) are one look under two names — change one, or record the
pair in `DISTINCT_WAIVERS` with the user's reason.

## Composing a page

A composition is `fn(k, slide, fields, image) -> rects`, registered with `@vn.register("<name>", "<page>", alts=n)`.
`k` is the kit (`k.P` the ground's palette, `k.face(role)`, `k.name`); `fields` holds the caller's words; `image` is
the caller's picture or `None`. Return `{field: (x, y, w, h)}` for what you drew.

The helpers in `vl_native.py` (`vn`) do the measuring:

- `vn.ctx(k)` → `(W, H, s, orient)`: the canvas, the scale (`s` = short side / 7.5), `"land"` or `"port"`;
- `vn.text_of(fields, "title")` → the caller's words or `None`; `vn.points_of(fields.get("items"))` → `[(head, line)]`;
- `vn.flow(k, slide, page, (x, y, w, h), [(field, text), …], anchor="top")` → `(rects, draw)`: sizes every field
  to the column (starting at the manifest's sizes, never under the floors) and plans before drawing — call `draw()`;
- `vl_native2.stack(k, slide, page, x, w, y0, y1, groups)` → `(rects, draws)`: groups of fields one under another,
  each planned in what the later ones leave it;
- `vn.alt()`: which layout `compose()` is trying (0 = the designed one); register `alts=2` or more and offer roomier
  layouts — a page refuses only when the last one overflows;
- `vl.VLTextOverflow`: raise it when the words cannot fit even at the floors — never cut or shrink past a floor;
- `vn.GROUNDS["<name>"] = fn(k, slide)`: what every page in the language carries (a grid, a frame), painted by
  `k.new_slide()`.

```python
@vn.register("mosaic", "cover", alts=1)
def _mosaic_cover(k, slide, fields, image):
    W, H, s, o = vn.ctx(k)
    head = [(f, vn.text_of(fields, f)) for f in ("kicker", "title", "subtitle") if vn.text_of(fields, f)]
    rects, draw = vn.flow(k, slide, "cover", (0.08 * W, 0.22 * H, 0.62 * W, 0.56 * H), head, anchor="top")
    draw()
    return rects
```

Read two shipped compositions before writing your own — `tally` (`vl_native2.py`, a measured grid) and
`wayfinding` (`vl_native3.py`, a sign system) — for alternatives, extras and CJK handled end to end.

## Rules the fifteen taught

- **Never invent.** Every word, number and name on a page is the caller's; the few a language derives (page numbers,
  structural labels in the page's script, a closing mark) are listed in `derived`. A route, an arrow or a sequence is
  drawn only when the caller says the items are ordered.
- **Measure with headroom, then set the measured lines.** Text is measured by the glyphs and by the measure lint
  reads; a field is drawn a little wider than it was measured, and a wrapping display field is set in the lines it
  was measured in — else the renderer wraps it again and the field grows a line its box never had.
- **Wrap before shrinking.** A title wraps first and shrinks at most 15%; a last line holding one word is fixed by a
  break at a clause, then a balanced (narrower) measure, then the ≤15% shrink, then breaks chosen at the same line
  count — and kept only when none of those can.
- **Alternatives before refusing.** A page offers a roomier layout before it raises `VLTextOverflow`; it never
  drops a field or shrinks it under its floor to make room.
- **Plan later fields' room first.** A headline planned alone leaves the list under it nothing on a small canvas
  (`stack()` and broadsheet's cover reserve what the later fields need).
- **Overlaps are declared.** A composed overlap (a tucked quote mark, a word over a band) carries
  `dk.overlap_intent(shape, reason)`; everything else that touches is a defect.
- **Designed contrast grounds.** A dark ground is designed, not inverted: no large near-white slab (the contract
  checks it), cards and paper in the ground's own tones.
- **Rules end at their content.** A column or margin rule ends just under the words it serves — and reaches the
  longer of the two columns it separates.
- **The smallest tier is read.** Kickers, credits and captions ≥ 12pt, furniture ≥ 10pt; a credit never shrinks
  under 12pt.
- **CJK copy.** Break at clause marks, never inside a Latin word, no spaces added between CJK and Latin; the faces and
  fallbacks are in `references/visual-languages.md` → "CJK and Hangul copy".
- **Real faces measure.** Sizes are measured with the faces installed; on a machine without them (CI's Linux) a
  check that depends on a face's width runs on macOS only — never tune a layout to a stand-in face.

## Review checklist

- [ ] `check_vl_contract.py <name>` prints no problem; `--describe <name>` reads right and its example runs.
- [ ] Every page builds on 16:9, 4:3, 1:1 and portrait, with short and long copy, in English and Chinese, lint-clean
      or refused loudly.
- [ ] Both grounds rendered and looked at; the user has seen the sheets.
- [ ] Nothing on a page that the caller did not give, except the words in `derived`.
- [ ] A general component (`sigs.py --example timeline --in <name>`) placed in the language reads right on both
      grounds.
- [ ] Samples, scaffold, docs row, the library page export and `vl_docs.py --write` done; the full CI green.
