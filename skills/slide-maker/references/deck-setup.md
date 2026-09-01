# Deck setup

## Canvas format — non-default surfaces (4:3 · 小红书 3:4 · 1:1 · story 9:16 · A4 · A0/A1 poster)

**Canvas format (only when the interview picked a non-default surface).** The default deck is
16:9 via `deckkit.blank_deck()` — untouched, and everything below assumes it. When the interview
confirmed a different surface (4:3 venue, 小红书 3:4, square 1:1, story 9:16, A4 print, A0/A1
conference poster in either orientation — `a0` · `a1` · `a0-landscape` · `a1-landscape`), start from
`scripts/formats.py` instead: `FMT = formats.get("<name>")` → `prs = formats.blank_deck(FMT)`,
take the safe content rect from `formats.band(FMT)` (it encodes the platform-UI safe zones — on
story/rednote, text outside it is covered by the platform), honor `FMT.chrome` (social surfaces get NO
deck footer/page numbers), branch stack-vs-split layouts on `FMT.columns_ok`, multiply only
display/cover type by `FMT.display_scale`, and pass `FMT.lint_flags` to the Step-5 lint. Keep the
SAME pt tokens for body/label type (canvas inches are chosen per format so relative size lands
right — the inch-normalization principle) and the same components/identity throughout; per-surface
layout DNA + the repurpose/batch pattern live in `references/canvas-formats.md`. The design plan
records a `format:` line whenever it's not `wide`.

🔴 **Two things change on a surface PRINTED AT ACTUAL SIZE — an A0/A1 poster.** (1) The
inch-normalization rule above does NOT apply: a printed board is not scaled to a screen, it is read
at ~5m / ~2m / ~1m, so keep the *format's* absolute floors (`formats.floors(FMT)` → A0: display ≥90pt
· section ≥36pt · body ≥24pt; A1: 72/36-ish/20) rather than the deck's usual pt tokens. deckkit's
`cover()` caps titles at 46pt, which is right on a 10in slide and unreadable across a hall on a 33in
board, so set the poster title size explicitly. (2) The board is composed ONCE and the whole of it is
the deliverable, so `FMT.fill_range` (55–90%) applies where a deck's whitespace-as-rhythm does not,
and **methods + limitations are required content** — `FMT.required_sections`. All of it is enforced
by `scripts/check_surface.py` at hand-off, which also enforces the safe-zone / `columns_ok` /
social-chrome rules on every other non-16:9 surface; run it yourself with
`python3 scripts/check_surface.py <deck.pptx>` while iterating. A poster written in a language whose
section headings the checker does not know extends it with `design_plan.surface_section_terms`
(e.g. `{"limitations": ["beperkingen"]}`) rather than waiving the check off.

## Template branch — build on the user's (or the conference's) .pptx

- **Template branch:** run `scripts/inspect_template.py <file.pptx>` — **a `.potx` works too**
  (institutions ship their brand template as `.potx`; python-pptx refuses that content type, so
  every entry point routes through `deckkit.open_presentation`, which rewrites it into a temp
  `.pptx` copy and leaves the user's file untouched) — to learn the
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

**🔴 Two font rules that are decided HERE, before the first `set_palette`.** (1) **The academic /
lab / conference register expects a conference face** — Times New Roman (serif, and the answer
whenever the deck carries equations, so prose and math share one face), or Calibri / Arial for a
sans register, with Courier New for mono; a designer sans reads as marketing in that room
(`design-by-purpose.md` → Type by register). (2) **A font that lives inside an APP BUNDLE cannot be
verified by this pipeline** — on macOS, Office keeps Calibri / Cambria / Aptos inside
`/Applications/Microsoft *.app/Contents/Resources/DFonts`, where PowerPoint sees them and
LibreOffice and the width measurement do not, so the deck gets laid out against a substitute and
the render self-check verifies a face nobody will see. `preflight_check.py` item 10 detects this
case by name; the default fix is a system-wide face. `Cambria Math` in particular is **often absent
even where Office is installed** — verify it before setting `EQ_MATHFONT`, or use Times New Roman.
Full rationale: `references/font-guidance.md`.
