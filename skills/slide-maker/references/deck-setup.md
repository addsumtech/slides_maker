# Deck setup — non-16:9 surfaces, the template branch, and fonts (Step 3)

## Canvas format — non-default surfaces (4:3 · 小红书 3:4 · 1:1 · story 9:16 · A4)

**Canvas format (only when the interview picked a non-default surface).** The default deck is
16:9 via `deckkit.blank_deck()` — untouched, and everything below assumes it. When the interview
confirmed a different surface (4:3 venue, 小红书 3:4, square 1:1, story 9:16, A4 print), start from
`scripts/formats.py` instead: `FMT = formats.get("<name>")` → `prs = formats.blank_deck(FMT)`,
take the safe content rect from `formats.band(FMT)` (it encodes the platform-UI safe zones — on
story/rednote, text outside it is covered by the platform), honor `FMT.chrome` (social surfaces get NO
deck footer/page numbers), branch stack-vs-split layouts on `FMT.columns_ok`, multiply only
display/cover type by `FMT.display_scale`, and pass `FMT.lint_flags` to the Step-5 lint. Keep the
SAME pt tokens for body/label type (canvas inches are chosen per format so relative size lands
right — the inch-normalization principle) and the same components/identity throughout; per-surface
layout DNA + the repurpose/batch pattern live in `references/canvas-formats.md`. The design plan
records a `format:` line whenever it's not `wide`.

## Template branch — build on the user's (or the conference's) .pptx

- **Template branch:** run `scripts/inspect_template.py <file.pptx>` to learn the
  layout indices, placeholder ids, and where logos/brand live (they sit on the
  layouts, so new slides inherit them). Then `deckkit.open_template()` loads the
  deck and wipes old slides while keeping masters/layouts. Pull the brand colors
  from the template and set `deckkit` palette/`FONT` to match. Save what you learn as
  a `profile.md` under the active template registry so it's reusable next time
  (a registered template's `profile.md` is a fully worked example of this).
  - **Conference template:** if step 0 turned up an official conference template,
    download it with the host's web fetch/download tool or `curl` and treat it exactly like a user template —
    inspect it, then build on it so the talk matches the venue's required look and
    aspect ratio.

## No-template branch — designing the look yourself

- **No-template branch:** `deckkit.blank_deck()` + `deckkit.add_slide()`, and give
  it consistent chrome with `deckkit.title_bar()` / `deckkit.footer()`. **Don't just
  accept deckkit's default blue — design the look to fit the purpose.** Read
  `references/design-by-purpose.md` for a per-purpose design language (palette mood,
  density, layout, chrome) and set the palette via **`deckkit.set_palette(deep=…, blue=…, magenta=…,
  mono=…, accents=[…])`** (call it ONCE right after import — a bare `deckkit.MAGENTA = …` does NOT
  re-theme components whose signature default is that colour, since those defaults are bound at
  import; `set_palette` rewrites them for you) + a **role-based font pairing** (`DISPLAY` title face
  + `FONT` body + `MONO`; add `EADISPLAY`+`EAFONT` for CJK) to
  match — or adopt a one-switch **`scripts/presets.py`** `preset(name)` (e.g. glassmorphism / swiss /
  editorial_paper / editorial_report / risograph / memphis / bauhaus / midcentury / terminal /
  synthwave — **18 total**, full catalogue with
  when-to-use in `references/design-gallery.md`: palette + fonts + surface + image-prompt)
  and tune it — then do a quick web-search for current, well-regarded examples of *this kind* of
  deck and adapt concrete ideas. A status update should read as crisp and corporate,
  a defense as sober and formal, a lecture as warm and clear — the design should
  signal the right kind of document before a word is read.
  - **Vary the look deliberately — don't default to one house style.** When *you* define
    the style, treat each deck as a fresh visual identity: choose a palette, type pairing,
    layout grid, and a signature motif that fit *this* purpose/audience/mood — and do NOT
    reuse the last deck's scheme out of habit (not the deckkit default blue, not whatever
    you built last time). Range widely across decks — warm vs cool, **light vs dark**,
    serif vs sans, minimal vs bold, restrained vs vivid; `design-by-purpose.md` gives a
    starting mood per purpose, but pick a *distinct, concrete* look within it. Unsure or
    brand-defining? Show 2–3 direction archetypes in **one HTML preview link** and let the user
    pick (collaborative mode, `scripts/archetypes_html.py`). Sameness across decks is the failure to
    avoid; the only constant is the craft (contrast, hierarchy, one idea per slide).

## Fonts — non-Latin (CJK), math, and portability

**Fonts for non-Latin languages (Chinese / Japanese / Korean)** — applies to both
branches. The defaults are Latin-only, so set a script-appropriate font before
building: `deckkit.EAFONT = "Hiragino Sans GB"` (macOS render-loop-safe; or Microsoft YaHei / Noto Sans
CJK SC), keeping `FONT` for Latin/numbers. This tags every run with a CJK `<a:ea>` font
so it renders correctly *and portably* (not an uncontrolled fallback), and mixed
中文+English stays right. Pick the CJK font to the purpose, emphasize with weight/colour
not italic (CJK has no true italic), and flag the font dependency at hand-off. Full
guidance + RTL limits in `references/multilingual.md`.

**Font portability (any deck).** A `.pptx` stores font *names*, not the fonts — pick fonts
present on every machine that will open it (a missing font substitutes, shifting metrics
or, for non-Latin, producing tofu). Default to cross-platform-safe fonts (Arial/Calibri,
Georgia, Consolas), set `deckkit.FONT/MONO` accordingly (and `deckkit.EQ_MATHFONT` — STIX Two Math /
Cambria Math — for native `equation_native` math; `EQFONT` only affects inline `eq_par` runs), and flag any brand-font
dependency at hand-off. Editable `equation_native` math needs a **math font** (STIX Two Math / Cambria
Math) for its glyphs — flag that dependency; `equation_png` is font-independent (rasterised).
Full list, fallbacks, and tofu recovery in `references/font-guidance.md`.
