# P2 — Visual languages (curated register family): design

Date: 2026-10-03 · Status: approved in conversation, awaiting written-spec review
Builds on: P0 (on main: picture shapes / rotation / focus, `dk.mark`, `ornaments.py`, `image_fx.sticker_outline`,
`frosted_panel`, `dk.decorative`) and P1 (on main, 176b9e3: `image_series.py`, `slot_picture`, the image-series gate).
Source: the skillry.dev gap analysis (memory `slide-maker-visual-language-gap.md`) — the 33 image-led
"visual language" decks there are each a complete look: a type voice, a surface, image treatments and a set of
page compositions. slide-maker's 18 presets carry palette + fonts + flat ground + furniture (`register_surface`),
but no register owns its page compositions, there is no display-type vocabulary (outlined, two-tone, stacked),
no grain/paper surface, and no collage arrangement.

## Decisions (made with the user)

| # | Question | Decision |
|---|---|---|
| 1 | What should P2 deliver? | **Pick a visual language → a whole finished deck**: each language is a complete kit (page compositions + type + surface), offered at the direction gate, image-led ones wired to P1's series. Missing primitives are added as the kits need them. |
| 2 | Which languages first? | **All four**: editorial magazine (photo, quiet), soft organic (photo, warm), collage scrapbook (photo, loud), watercolour storybook (illustration). |
| 3 | Display-type strategy | **System fonts + typographic technique.** No bundled fonts. Each role has a per-platform face list; the default range uses faces present on BOTH macOS and Windows so the render matches what the viewer opens; Mac-only flourish faces only on explicit request. The look comes mostly from technique (scale, outline, two-tone, stacked, highlight). |
| 4 | Previewing image-led languages at the direction gate | **Bundled style samples**: one real render per language, labelled "style sample — not your content"; no generation at gate time. |
| 5 | Architecture | **A — a new kit library** (`visual_languages.py`) beside `bespoke_kits.py`; the 18 presets and 4 bespoke kits are untouched. |

## Verified facts this design rests on (2026-10-03, this Mac)

- Installed and resolvable by the renderer: Georgia, Didot, Bodoni 72, Baskerville, Big Caslon, Times New Roman,
  Arial Rounded MT Bold, Avenir Next (+ Condensed), Futura, Gill Sans, Optima, Bradley Hand, Noteworthy, Marker Felt,
  Chalkboard SE, Snell Roundhand, Comic Sans MS, Impact, Arial Black, Arial Narrow, Helvetica Neue, Trebuchet MS,
  Verdana, Rockwell, American Typewriter, Courier New; CJK: Songti SC, Hiragino Sans GB.
- Present here only as macOS ON-DEMAND (downloaded) assets, so not guaranteed on another Mac: Kaiti SC, Yuanti SC,
  Hannotate SC, Wawati SC, Libian SC, HanziPen SC, Lantinghei SC, PingFang SC.
- Not installed here (the renderer substitutes DejaVu): Cambria, Century Gothic, Segoe Print, Ink Free, SimSun,
  KaiTi, Microsoft YaHei. **Windows faces cannot be render-verified on this machine**; the Windows column of each
  font table is taken from Microsoft's documented default fonts and is marked unverified in code and docs.
- A pptx run carries ONE Latin and ONE East-Asian typeface — there is no fallback chain inside the file, so face
  choice happens at build time.
- Presets carry no layout fields; `register_surface.ground()/card()` paint furniture only; `dna` never reaches the
  build; the direction preview cannot show images; grounds are flat colour only.

## 1. Architecture and components

- **`scripts/visual_languages.py`** registers four languages: `editorial`, `soft`, `collage`, `storybook`. Each is:
  1. **palette** — ground, ink, 2-3 accents, each accent with its text-safe twin (`palette_audit` rules);
  2. **type** — roles `display`, `body`, `accent`, `cjk_display`, `cjk_body`, each a list of faces tagged with
     platforms. `fonts="both"` (default) uses only faces on macOS AND Windows; `fonts="mac"` unlocks Mac-only
     faces (Didot, Bradley Hand, Baskerville, Arial Rounded); CJK defaults to always-present system faces (Songti /
     SimSun serif, Hiragino Sans GB / Microsoft YaHei sans); on-demand CJK faces (Kaiti, Yuanti) only when named;
  3. **ground + card** via `register_surface.register(name, ground=, card=, forbids=)`, so `register_guard`,
     `check_register_pixels` and the register contracts apply;
  4. **six page functions** — `cover`, `section`, `image_text`, `quote`, `data`, `closing` — that take content
     (title, body, attribution, number, image) and lay the page out with P0/P1 primitives, returning the rects they
     used. They never invent words, numbers or names.
- **Use:** `vl = visual_languages.use("collage", prs, fonts="both")` sets palette/fonts/ground; then per slide
  `vl.cover(s, title=…, kicker=…, image="hero")`.
- **Images:** `image=` takes either a P1 series slot id (placed with `image_series.slot_picture`, tagged `+gen.<slot>`)
  or a file path (a user's real photo, a fetched public-domain image) placed with the same frame treatment, untagged.
  A missing image raises with the command that makes it.
- **Untouched:** the 18 presets, the 4 bespoke kits, and every deck that does not pick a visual language.

## 2. The four languages

1. **editorial** (photo-led, quiet) — warm paper or near-black ground, one accent; large serif display (Georgia;
   Didot with `fonts="mac"`), sans body; big numbers always in a lining-figure face (Georgia's old-style figures are
   forbidden there); CJK display Songti/SimSun, body Hiragino/YaHei. Large bleed photos (rect, occasional arch),
   small captions, standfirst and pull quotes. Pages: cover = full-bleed photo with the title in the measured
   calm region; section = oversized number + hairline; image_text ≈ 60/40; quote = big quote marks + attribution;
   data = one big number + one sentence; closing = a quiet image + one line. Minimal ornament (rules, folio).
2. **soft** (photo-led, warm) — cream or pastel ground (peach, sage, lavender) with dark text inks that pass
   contrast; Trebuchet (both) / Arial Rounded (mac); CJK sans. Arch, ellipse and blob frames, large rounded cards,
   soft colour blobs underlay; scallop edges; no hard rules.
3. **collage** (photo-led, loud) — kraft or grid-paper ground; Impact / Arial Black headlines with `dk.mark`
   highlights; handwritten accents only with `fonts="mac"` (Bradley Hand), otherwise scribble/squiggle underlines;
   CJK heavy sans + highlight. Rotated print-style photos with white borders, tape, cut-out stickers, overlap;
   ornaments within the existing loud-motif budget (≤ 3).
4. **storybook** (illustration-led) — paper ground with fine grain; serif display and body (Georgia; Baskerville
   with `fonts="mac"`); CJK Songti/SimSun. P1 watercolour series, edges feathered into the paper (no hard frame),
   cut-out illustration elements as accents. Cover: illustration over the top ~2/3, title on the paper.

All four meet every existing gate: contrast floors, text-on-image (text only in a measured calm region or on a
near-opaque panel), motif budget, layout sameness, the P1 series and people rules.

## 3. New general primitives

1. **`scripts/display_type.py`** — `stacked(...)` (each line width-fitted to one measure, CJK-aware), `two_tone(...)`
   (named words in a second colour, optional offset shadow), `outlined(...)` (hollow display type for oversized
   numbers/section marks). Each is verified first by a native pptx rendered in LibreOffice; an effect that does not
   render is not shipped and is reported.
2. **Surfaces** — deterministic grain / paper-fibre tiles generated per ground colour and set as the SLIDE
   BACKGROUND (`<p:bg>` picture fill, tiled), not as a picture shape (no alt-text finding, never over text);
   amplitude capped so every contrast check still passes; tiled rendering verified in LibreOffice first.
3. **`image_fx.feather(src, out=None, *, radius=…)`** — edges fade to transparent so an illustration melts into
   the paper.
4. **`collage(slide, region, items, *, seed=…, keep_clear=…)`** — 2-4 images as white-bordered prints with small
   rotations and tape, bounded overlap, `overlap_intent` declared, a text-safe rect never invaded, deterministic
   for a given seed.
5. Every new function: a runnable `sigs --example` (executed by smoke), unit tests (EN/ZH, aspect ratios, edge
   inputs), inventory entry, CI step.

## 4. Direction gate, build flow and gates

1. **Direction gate** — a visual language appears among the offered directions as a styled slot (alongside presets
   and bespoke registers), carrying the tokens the diversity checker reads (bg, accent, faces, cover, skeleton);
   the preview shows its bundled sample, labelled "style sample — not your content". Samples are built by
   `visual_languages.py --sample` with the real kit, from P1's generated sets plus public-domain photos where a
   type is missing, compressed and bundled under a size budget.
2. **Build** — picking one records `design_plan.visual_language` and `design_plan.vl_fonts` ("both" | "mac");
   image-led decks also record `imagery: "series"` (P1) unless the images are the user's own or fetched.
3. **New gate `visual_language`** (one module, imported by both `render_deck --gate-check` and
   `codex_delivery_gate.py`; parity + schema reach): a deck recording a language must carry that language's page
   tags (a `+vl.<name>` flag through `_compose_tag`) on the cover and on at least half of its pages, and use its
   display face — "picked collage, built plain" blocks. NOT CHECKED when no language is recorded; an unknown name
   blocks.
4. **Non-Claude** — a Codex runbook step; scripts print runnable NEXT lines; every function is findable through
   `sigs --search` with a runnable example.

## 5. Generality and verification

1. **Matrix tests** — each language × each page function × {EN, ZH, JA} × {13.333×7.5, 10×5.625, 4:3, 9:16
   portrait} × {short, normal, very long text} × {slot id, real path, missing image} × {fonts both, mac}: zero
   build-time criticals. **Refuse, don't truncate**: text that cannot fit shrinks within the type floors, then raises
   naming the page, the field and the overflow.
2. **Real runs** — per language one EN and one ZH deck, rendered and every page looked at, then the real delivery
   gate. Images: P1's two generated sets and public-domain photos (no spend). Any NEW generation needs the user's
   permission first (the Codex account is on the FREE plan, so it would be the metered API).
3. **No effect on existing decks** — `visual_languages` is not imported by `deckkit`; deckkit only gains new
   functions; full suite green; timing compared before/after on the smoke suite.
4. **Restricted non-Claude run** — printed-output-only, a third language, one language end to end.
5. **Close-out** — independent final review + a generality probe; findings fixed test-first; full suite + CI green
   before pushing to main.

## Out of scope

More languages (neo-brutalist, Y2K, art deco…) — the kit format makes them additive later; bundled fonts; editable
PowerPoint masters; animation per language.
