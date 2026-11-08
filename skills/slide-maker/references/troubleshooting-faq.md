# Troubleshooting & FAQ — symptom → cause → fix

The one page to open when anything fails. Every entry follows the same shape: the **exact message
(or symptom) you see → what it means in plain words → the first fix to try**. Nothing here requires
reading another document first; pointers at the end of an entry are for *going deeper*, not for
understanding the fix.

**For the model running this skill:** when a build, lint, or render step fails, consult this page
before improvising — and when you report a finding to the user, report it in this page's
plain-language form (what broke → why → the fix you applied or propose), never as raw lint jargon.

## Table of contents
1. [How to read an error](#1--how-to-read-an-error)
2. [Environment & install](#2--environment--install)
3. [Build-time Python exceptions](#3--build-time-python-exceptions)
4. [Build-time lint (`deckkit.lint_layout`)](#4--build-time-lint-deckkitlint_layout)
5. [Render stage failures](#5--render-stage-failures)
6. [Render-lint hard findings (`lint_deck.py`)](#6--render-lint-hard-findings-lint_deckpy)
7. [Advisory `[stats]` warnings — act or accept?](#7--advisory-stats-warnings--act-or-accept)
8. [Images: generation & sourcing](#8--images-generation--sourcing)
9. [CJK / bilingual issues](#9--cjk--bilingual-issues)
10. [FAQ one-liners](#10--faq-one-liners)
11. [Source ingestion & long-source (`ingest.py` · `extract_pdf.py map/text/headings`)](#11--source-ingestion--long-source-ingestpy--extract_pdfpy-maptextheadings)

## 1 · How to read an error

Three error surfaces, three prefixes:

| You see | Stage | Severity |
|---|---|---|
| `[lint] ✗ slide N CODE message` | build-time, before rendering (`deckkit.lint_layout`) | **critical — must fix** (strict mode refuses to save) |
| `[lint] • slide N CODE message` | build-time | warning — judgment call |
| `slide N: FINDING message` + `N layout finding(s)` | render-time (`lint_deck.py` on the PNGs) | **hard finding — must reach 0** |
| `slide N: [warn] MESSAGE` | render-time | advisory (alt-text, math-font tofu risk, low/body contrast…) — does not fail the exit code |
| `[stats] FAMILY: …` | render-time | advisory — never fails the exit code (see §7) |
| `render_deck: N hand-off gate(s) failed` + `[i/N] <section>` | hand-off (`render_deck.py --gate-check`) | **all N must be fixed — the run reports every one** |
| a Python traceback | your build script crashed | fix the code line it names (§3) |

**`deck_cycle: REFUSED — this edit is another nudge`.** Not a bug: the same fault failed 3
consecutive runs and your last edit changed only NUMBERS (the build script's AST is identical once
numeric literals are normalized, which is what "another nudge" means as a file property). Fix it
the way that works — compute the geometry from the real content (`fit_text`, measured ink heights,
a stack pitch derived from the block height) or rebuild the slide on a form helper
(`sigs.py --example <form>`); shortening the text counts too. Measured precedent: 10+ nudge
iterations on one slide, then the computed-fit rewrite landed first try. If a constant really is
the fix (a fixed template slot, say), `--nudge-again "<why>"` runs it and records the reason in
`.deck-cycle-state.json`. A fault that clears, or a different build script, resets everything.

🔴 **The hand-off gate lists EVERY failure in one run — fix them ALL before re-running.** It used
to stop at the first, so a thin `.deck-gates.json` cost one fail → fix → re-run cycle per field, at
the point in the session where a round-trip is most expensive. Only a structural stop still comes
alone (no `.deck-gates.json`, unreadable JSON, an unknown recorded `delivery`), because every later
gate reads what it could not produce. Within one section the first stop wins for the same reason.

`slide N` is 1-based and matches the rendered `slideNN.png` (e.g. `slide07.png`). When a message
names a shape it quotes the first words of its text — search your build script for those words to
find the line to change.

## 2 · Environment & install

**First move for ANY environment problem:** `bash scripts/check_env.sh` (native Windows:
`python scripts\check_env.py`). It prints one line per dependency with the **exact install command**
for your platform — run the command it gives you, nothing else to figure out.

| Symptom | Cause | Fix |
|---|---|---|
| `soffice: command not found` / PDF never appears | LibreOffice missing or not on PATH | macOS: `brew install --cask libreoffice` · Debian/Ubuntu: `sudo apt install libreoffice` · check_env prints the platform-exact line |
| `Error: The operation was canceled.` while `apt install libreoffice` runs (CI / a runner) | **NOT a dependency conflict.** apt resolved cleanly — `0 upgraded, N newly installed, 0 to remove and M not upgraded` means no conflict (a conflict removes packages or reports *unmet dependencies* / *held broken packages*; `M not upgraded` is normal). The step was **cancelled / timed out** mid-download — that exact phrasing is what a CI runner prints on cancel, not apt | Give the step more time: LibreOffice pulls ~66 packages / ~160 MB, plus `fonts-noto-cjk` for CJK decks. Non-interactive: `sudo apt-get install -y --no-install-recommends libreoffice fonts-noto-cjk`. On CI, raise the step's timeout or cache the LibreOffice layer; then `bash scripts/check_env.sh` should report it present |
| `pymupdf not installed — run: … -m pip install pymupdf` (printed by `render_deck.py`) | PyMuPDF missing from the interpreter you're running | Run the exact pip command it printed (or `pip install -r requirements.txt`) |
| `ModuleNotFoundError: pptx` (or PIL / fitz / matplotlib) | Python deps not installed into the interpreter you're running | `python3 -m pip install -r scripts/../requirements.txt` — use the same `python3` you run the build with (check_env prints the exact path) |
| Text renders as hollow boxes (tofu) | The chosen font has no glyphs for that script (usually CJK on a Latin-only font) | Set an East-Asian font for CJK runs (`dk.EAFONT = "Hiragino Sans GB"` on macOS, `"Microsoft YaHei"` on Windows, `"Noto Sans CJK SC"` on Linux); `references/multilingual.md` has the pairing table |
| Deck looks right on your Mac, wrong fonts on a colleague's Windows | macOS-only fonts (Chalkboard SE, PingFang, Hiragino) don't exist there — PowerPoint silently substitutes | Either stick to the cross-platform pairs in `references/font-guidance.md`, or ship a **PDF** next to the pptx for sharing (the hand-off should flag this whenever a platform font was a deliberate style choice) |
| `KeyError` / auth error from an image script | API key env var not set in *this* shell | First check you should be on this path at all: the API is **metered** and needs the user's explicit go-ahead (BILLING GATE in `image-generation.md`) — `codex login` is the free alternative. Once agreed: `OPENAI_API_KEY="$(cat ~/.openai_key)"` inline before the command (never echo or commit a key) |

## 3 · Build-time Python exceptions

The traps that actually bite, in the order people hit them:

| Traceback says | Cause | Fix |
|---|---|---|
| `AttributeError: ISOCELES_TRIANGLE` | The enum is spelled `MSO_SHAPE.ISOSCELES_TRIANGLE` (double S) | Fix the spelling; when unsure of any enum name: `python3 -c "from pptx.enum.shapes import MSO_SHAPE; print([n for n in dir(MSO_SHAPE) if 'TRI' in n])"` |
| `FileNotFoundError` on an asset (hero.png, icon, plate) | Build run from the wrong directory — relative paths resolve against the CWD | Run from the deck folder, or better: build paths from `ROOT = Path(__file__).parent` like the templates do |
| `ValueError: text(): non-positive box …` | A box's size was DERIVED from arithmetic that came out ≤ 0 — classically `h = card_h - 1.42` where `card_h` is 1.30. python-pptx used to accept it silently, the run then overflowed a box with no interior, and every geometry check stayed green because there was nothing to overlap | The traceback names the slide function, which is where the bad arithmetic is. Reserve the fixed elements FIRST, then derive this box from what is left (`vstack(…, bottom=)` / `rows()` / `content_band()`) rather than subtracting a hand-picked constant |
| `ValueError: hub_spoke(): radius … too small` (and similar from deckkit helpers) | The helper pre-checked your geometry and refused to draw an overlapping diagram | The message states the minimum that fits — pass that radius/size, or drop the element count |
| Colors behave oddly / `AttributeError` on a color | Passing a hex string where an `RGBColor` is needed (or vice versa) | deckkit component APIs take `RGBColor(0xRR, 0xGG, 0xBB)`; only documented string params take hex |
| `TypeError` on `text(...)` rows | The rows argument is a list of paragraphs, each a list of run tuples: `[[(txt, size, color, bold, italic, font)]]` | Match that nesting exactly — one missing bracket level is the classic cause |

## 4 · Build-time lint (`deckkit.lint_layout`)

Runs before saving; with `strict=True` (as the generic build template calls it before `prs.save()`)
it refuses to save while criticals exist. Codes, in plain words:

| Code | Means | First fix |
|---|---|---|
| `OFF_CANVAS` ✗ | A shape/text sticks out past a canvas edge (message names which edge) | Move or shrink it — the canvas is `0..W × 0..H` of **your** deck (the skill's templates build `10 × 5.625` in by default; `13.333 × 7.5` only when the deck was authored at that size — check your `blank_deck(W, H)` call); full-bleed images use `picture(..., fit="cover")` at exactly canvas size. **A device that leaves the canvas ON PURPOSE is declared, not exempted**: `deckkit.bleed_intent(shape, "<why>")` — per shape, with a reason, honoured here and by `OVERFLOW` at file level. It exists because the only previous escape was `lint_layout(strict=False)`, which switches the check off for the whole deck; an UNdeclared shape off the canvas still fails |
| `OVERFLOW` ✗ | More text than its visible (filled/outlined) box can hold — it will clip or spill in the render | The message shows text-height vs box-height: shorten the text, shrink the font 1–2 pt, or grow the box; `fit_text_size()` computes the largest size that fits |
| `TEXT_OVERLAP` ✗ | Two text blocks intersect — one will sit on the other | Move one, or restructure (merge into one block / put the label inside the panel it annotates). 🔴 **Do not dismiss it because the render looks clean**: for a no-wrap box (`wrap=False`, `<a:bodyPr wrap="none">`) LibreOffice wraps the line at the box width anyway — measured on LibreOffice 26.2 for Latin and CJK alike — so the render shows two tidy lines where PowerPoint draws one line straight into its neighbour. The geometry check models PowerPoint; the render cannot show this collision |
| `STRETCHED THIN` • | A wide blank vertical channel runs through the slide's interior. Two calibration fixes since: the content test is now RELATIVE to the slide's own dynamic range (a fixed colour distance is a light-deck number — on a near-black canvas panels differ from the canvas by ~42 and read as blank, so the check found "voids" between glyph strokes and fired on 7 of 20 slides of a professional dark briefing, one of them filled edge-to-edge with a chart); and a channel with real ink on BOTH flanks is a GUTTER, not emptiness — a two-column comparison or a divider with a numeral left and a graphic right is composition | If it still fires, the void has content on one side only. Enrich, merge with a neighbour, or declare the quiet register with `design_intent(envelope=…)` |
| `PLATE NOT VISIBLE` • | An interior page's full-bleed background has been scrimmed into a flat field — its exposed area varies by <0.6 grey levels. It satisfies "a plate on every page" in code while reading as no plate at all, and no contrast check can see it (a whiter background only makes dark text score *better*). Cover / dividers / closer are exempt — their imagery is loud by design | Lift the scrim and recover text contrast with the frosted blocks instead (`generated-template.md`'s visibility floor). Measured on real renders: 1.58 as generated, 1.16 under a light wash, 0.21 scrimmed to near-white |
| `FONT NOT INSTALLED` • | A face the deck DECLARES (`FONT`/`MONO`/`EAFONT`/…) is not on this machine, so measurement falls back to a metric-incompatible substitute — and every wrap/fit/overflow check in the library is computed from that measurement, so all of them carry ~1 line of slack. The shipped defaults `Calibri`/`Consolas` are Office faces absent from macOS | `deckkit.use_platform_fonts()` near the top of the build (picks installed equivalents for this OS), or set the faces yourself. `deckkit.font_health()` lists what is missing |
| `ESCAPES_CARD` • | A child element pokes past the edge of the card/panel it visually belongs to | Shrink the child or its step spacing until it sits ≥0.1 in inside the card |
| `OFFCENTER` • | A single text line sits noticeably high or low inside its tall box — looks like a spacing bug | Cheapest: `anchor=MSO_ANCHOR.MIDDLE` on the textbox at the card's exact x/y/w/h; else shrink the box to the text or move its y; harmless on deliberately top-anchored chips |
| `SLIVER_GAP` • | Two blocks almost touch (a hair-thin gap) — reads as a rendering accident | Open the gap to ≥ ~0.13 in — derive the pitch from `rows()`/`vstack()`, never `block_h + ε` (touching edges are their own flaw — "one merged block"; deliberately-jointed zones are a named exception, not the default fix) |
| `FOOTER` • | Content dips into the reserved footer band at the bottom | Keep content above the band (the card/panel variant of the message gives the exact y-line; the text variant quotes the colliding block — move it up) |
| `TEXT CONTRAST` ✗ (a11y floor) | Text that is NOT "large" in WCAG 1.4.3's sense — under 14pt at any weight, or under 18pt and not bold — sits under 4.5:1 on a resolved backing (a solid fill or a highlight). Under 14pt there is no judgement to make: no weight makes it large. The hand-off a11y gate holds it on both runtimes (the old `BODY CONTRAST` warn let a 12.5pt caption at 3.38:1 through `--gate-check`). | Use the ink the finding names (the nearest one that keeps the hue and reaches 4.5:1), lighten the fill, or take `deckkit.on(fill)` (a neutral readable ink), or set it at 18pt / 14pt bold if it is meant to be large. A deck handed over with it open records `a11y.waived` with a reason, like the other a11y floors. |
| `LOW_RES_IMAGE` ✗/• | A picture's visible source pixels (after its crop) are spread too thin over its frame: • under 72 ppi (reads soft — a 13.33in slide on a 1080p screen is ~144 ppi), ✗ under 36 ppi (the pixels show as blocks). Only pictures whose long side is ≥ 1.5in; vector images, `decorative()` pictures and declared pixel art are skipped. Commonest cause: a thumbnail or a heavily cropped photo stretched to fill a frame (a portrait photo cropped to a full-bleed landscape cover keeps a third of its pixels). | Use a larger source (the message names the pixels this size wants, ~144 per inch on the long side), place it smaller, or crop less. If the pixels ARE the point — pixel art, a screenshot of a low-resolution screen — declare it: `deckkit.low_res_intent(pic, "<why the pixels are the point>")`. |
| `OLDSTYLE_FIGURES` • | A big number is set in a face whose digits sit at different heights (Georgia, Hoefler Text, Constantia… — measured from the installed font, not a fixed list) — 6 and 8 ride high, 3/4/5/7/9 drop below the line, so the number looks like it bobs up and down | Keep the serif for WORDS and set any run containing digits in a lining-figure face — Helvetica Neue, Arial or Cambria. Only fires at 20pt and above; old-style figures in body prose are correct and are not flagged. See `references/font-guidance.md` |
| `HOLLOW FILL` (stats) | The page reads as full but most of its ink is a **drawn container** rather than content — an outlined frame with no fill and no text of its own, wrapped around very little. Occupancy is a bounding-box union, so a hollow frame counts its whole footprint: measured, one empty rect with four characters inside scored **49%**, which is "full" by every density check and therefore exempt from `UNDERFILLED` as well. | 🔴 **Ask whether the FORM is right before touching the spacing** — every other message in this file points at geometry, and on a real build many rounds went into re-spacing a page whose actual problem was that its diagram carried one sentence. The cheap repair is usually to demote the container (an annotation, a line in the list it sits beside), not to re-space it. It fires only when the container dominates AND the content is thin AND the page has no typographic hero; a hero with air is protected, as it is for `UNDERFILLED` |
| `CJK_FACE_UNREACHED` • | A CJK face (Songti / PingFang / YaHei / Noto Sans CJK …) is named as a run's **Latin** font on a run that contains CJK, so it reaches none of those glyphs — they render in `EAFONT`. The rule was *wrong* rather than missing: the author followed the documented call shape and got a silent no-op, which on one measured build gave 6 of 14 slides a title in a face nobody chose. | A run tuple's sixth element is the Latin face; the **seventh** is the East-Asian one: `(text, size, colour, bold, italic, latin_face, ea_face)`. Set the Latin face to the deck's Latin font (which is also what keeps digits on a lining face) and the CJK face in slot 7. Silent when there is no CJK in the run, when both slots name the same face, and when slot 6 is a Latin face |
| `OOXML_SHAPE` ✕ | The slide part violates its own schema — a duplicated element the schema allows once, or children out of order. **This is the only defect class where the file does not open at all**, and every other check here is structurally blind to it: they are geometric, pixel-based or semantic, and none asks whether the part is well-formed. Measured: two `Build(s)` on one slide left TWO `<p:timing>` elements — `save()` raised nothing, LibreOffice rendered it, `lint_layout` reported clean, and `preflight_check.py` (which counts occurrences of the string `p:timing`) read the *duplicate* as **more** compliant. The first human signal would have been PowerPoint offering to repair the file. | Do not route around it — the file really is broken. If the message names `<p:timing>`: you called `Build.apply()` twice on one slide, which `anim.apply()` now refuses outright. Use ONE `Build` per slide and put every beat in its steps; a second Build's steps were never in the first's sequence, so keeping either tree ships a click order nobody wrote. If it names order: you appended where you should have inserted — CT_Slide runs `cSld, clrMapOvr?, transition?, timing?, extLst?` (`slide_transition()`'s `addprevious` is the pattern to copy) |
| `TEXT_GRAZES_SHAPE` • | A label's ink runs INTO a filled shape it is not inside — a caption grazing a bar, a row name touching a chip, a legend key on a node. `TEXT_OVERLAP` measures text against **text**, so this is invisible to it, exactly as a motif was before `TEXT_OVER_MOTIF`; the difference is that nobody tags a bar. Measured on a delivered deck: a right-aligned row label ran 0.015in² into the negative bar beside it, both lints clean, found by eye. | 🔴 **Move the label column's EDGE, not the string.** The first repair on that deck shortened the text and the label still grazed, because a right-aligned column that clears the *axis* does not clear a bar that grows *past* it. Derive the edge from the data — `right = ZERO − max(abs(v) for negative v)·SCALE − pad`. A value printed INSIDE its own bar is not reported (containment, not overlap, is the test), and a deliberate ride can be declared with `deckkit.overlap_intent(shape, "<why>")` |
| `WEIGHT MONOCULTURE` `[stats]` | The deck puts its visual weight on the **same side page after page**. One lopsided page is composition — this skill asks for it — so nothing per-slide is built on the measurement; `LOPSIDED` only speaks when a half is essentially dead (<5% occupancy), which is a different, rarer thing. Measured on a real deck: ink pushed left and the right held as air, over and over, with no gate saying a word. | Vary which side carries the weight across the deck — that is a rhythm decision, made once over the whole thing, not a per-page fix. Where a lean is deliberate, declare it: `design_intent(weight='left'\|'right'\|'asymmetric')`; declared slides are excluded from both sides of the ratio, so declaring is not a way to silence the signal, it is a way to be counted as having decided |
| `TEXT_OVER_MOTIF` • | A title/caption's ink crosses a shape tagged as the deck's signature motif. `TEXT_OVERLAP` cannot see this — it measures text against TEXT, and a motif is geometry, so a subtitle laid straight across a decorative ring produced **zero** findings until this check existed (measured: the same defect was caught by eye, written down as a build rule, and recurred on the next page). | Three legitimate answers, in order of preference: move the text out of the device's region; move the device (a corner mark belongs in chrome space); or, when the overlap **is** the composition — a display word riding a rule, a caption on a plate — declare it: `deckkit.overlap_intent(shape, "<why>")`. A motif GROUND is exempt — a painted colour FIELD (full-bleed, or a half-page register that `motif_page` paints) is a canvas text is MEANT to sit on, so only line-and-ring DEVICES can be crossed. Without that carve every word on a loud motif page reported, which is what made the loud tier unusable the day it landed |
| `MOTIF_UNEXPLAINED` • | The deck carries a **loud** motif and no legend anywhere. The STRANGER TEST asks that a device be readable by someone who has never seen the deck — label it, key it, or make it figurative — and two of those three are shapes that nothing counted, so the requirement was satisfiable by intending to satisfy it. | Draw the key: `deckkit.motif_legend(slide, '<what the device MEANS>')` at the device's FIRST appearance, or `motif_page(..., legend='…')`, which draws one with the device. If the motif is **figurative** — a stranger reads the shape on its own — this advisory is the expected one; say so on the plan's motif line and leave it standing |
| `MOTIF_BUDGET` • | More than 3 slides carry a **loud** motif appearance. The design plan budgets the loud device at ≤3 because a device stamped on every page reads as a template tell rather than a signature; nothing counted it until motifs were tagged. | Demote the extras to the quiet register signature — `register_mark(…, loud=False)` — which may legitimately repeat on **every** page and is deliberately excluded from this count. If more than three loud appearances are the design, say so at the design checkpoint and accept the advisory |
| `DUPLICATE_TEXT` • | Two separate shapes on ONE slide render the same string. Three measured causes: a build script patched repeatedly left an **orphaned copy of an earlier layout** drawing over the new one (the tell: your edits appear to do nothing — four consecutive coordinate changes moved nothing, because two layouts were running at once); a **component's own auto-label printed beside a hand-written one** (a single quantity then appears twice, often at two different roundings); a **name repeated in both a list and a diagram** below it. | Find which one it is before fixing: `grep` the build script for the string and count the call sites. Orphaned code → delete the older block outright (not "adjust" it). Double label → let the component own it (`show_pct`, `labels=`) or drop yours, never both. Repeated name → the list already said it; cut it from the diagram, or cut the diagram (a figure that repeats a line of the list beside it is usually spending a third of the page on a footnote). Short shared tokens (是 / N/A / an axis tick) are deliberately NOT flagged |
| `CHROME_SLOT_DRIFT` • | A per-slide **source line** sits at a different height than the rest of the deck's. Measured on a real deck: 11 source lines, 8 pinned to one slot and 3 placed wherever their page's last block happened to end — one of them rendering `as of <date>` **inside a diagram box**, where it reads as part of the diagram rather than as provenance. | Do not nudge the strays. The root cause is that the slot was a *constant each page applied by hand*, and a rule a page can decline to follow is not a contract — route every source line through ONE helper that ignores any x/y the caller passes: `def src(s, sources, as_of): dk.source_note(s, sources, as_of=as_of, x=L, y=SRC_Y, w=CW)`. Under three source lines no slot is established and nothing is reported |
| `CJK_NO_EA` ✗ | CJK text with no `<a:ea>` font — PowerPoint/LibreOffice would pick an uncontrolled fallback and 避头尾 never engages. It resolves **inheritance** first (the run's own slot → its paragraph's `defRPr` → the shape's `lstStyle`), so a supplied template that puts the face one level up is silent, as it should be. It stops at the shape: a face inherited from the **layout, master or theme** lives in another part and still reads as missing, so a corporate template can flag on text that renders fine — the fix below is correct either way and costs one line | **Two moves, in this order.** (1) Set `deckkit.EAFONT = "Hiragino Sans GB"` (macOS; Microsoft YaHei on Windows, Noto Sans CJK SC on Linux) at the top of the script — `references/multilingual.md` has the pairing table. This is what makes the NEXT build clean, and it is first because step 2 needs a face. (2) Fix the deck in hand, on the line above the lint and before `prs.save()`: `deckkit.retrofit_ea(prs)` — or 🔴 **`deckkit.retrofit_ea(prs, "Hiragino Sans GB")` if you have not done step 1, because with no face set anywhere it raises rather than silently fixing nothing.** It stamps the slot on every CJK run and returns the count, reaching groups, table cells, date/footer fields and chart text that the check itself cannot see; it skips runs that already resolve a face, so a template's own CJK typeface survives. **`EAFONT` alone never fixes a deck already built** (the runs exist), and on a redesign / surgical fix-pass — runs this skill did not author, which never pass through `set_font()` — it will not fix the next build either, so keep calling `retrofit_ea` there. If it reports CJK left on **layouts/masters**, that text composites onto every slide and no gate sees it: re-run with `layouts=True` |
| `CONNECTOR_IN_BOX` ✗ | An arrow/line endpoint sits in a block's interior and is drawn ABOVE the block, so the stroke crosses it (classic: hub-and-spoke connectors anchored at the hub's centre, cutting through its own label) | Dock both ends on block EDGES — `connect_boxes(a, b)` / `hub_spokes(hub, spokes)` from the block rects, or `edge_point(rect, toward)` for one end. Or add the connector BEFORE the node so the node paints over the seam. Never pass a block's centre as an endpoint on a line that's drawn on top |
| `[components] N cluster(s) look like a form the library already implements` (printed by `component_audit.py`) | The build script composed a common form — a bar row, a 100% band, a tile row, a marker row — from raw `box`/`text` while a component for it exists and was never called. The hand-roll re-inherits the geometry bugs the component fixes. | **Not an error, and not a blocker.** Either build the component, or record the one clause that makes the hand-roll deliberate (a bespoke composition IS the signature move). The tool suppresses a cluster whenever a component that could have drawn it was called, so a flag means the library genuinely went unused. |
| `INHERITED_EFFECT` (build-time WARN) | A shape still carries the theme `<p:style>` — it was created with raw python-pptx, not deckkit, so LibreOffice draws a soft drop shadow under it (the '2010 SmartArt' look deckkit strips everywhere else). | Create the shape through a deckkit helper, or pass it through `deckkit._flat(shape)` after creating it. |
| `RULE_THROUGH_TEXT` ✗ | A thin decorative rule (divider / hairline / accent bar) is drawn **through** a text block's ink instead of between blocks. Always caused by a hand-picked `y`: the rule was placed under text of a given length, then the text was edited and grew into it. | Derive the rule's position from the block it follows — capture the loop's end (`stack_end = y + pad`) and draw the rule there. Moving the coordinate by hand fixes today's wording and breaks again on the next edit.. **A crossing that IS the mark — a strike-through — is declared, not fought**: `deckkit.overlap_intent(rule, "<why>")` waives the geometry here, exactly as it does for `TEXT_OVERLAP`; the pixel checks still run and an undeclared crossing still fails |
| `HEADLINE_CROWDED` ✗/• | The slide's **headline and the block directly under it are touching or nearly touching** (✗ under 0.06in, • under 0.18in). The classic cause: the title box is sized for ONE line and the content below sits at a picked `y`, so the moment the title wraps to TWO its ink grows down into a block that never moved. `TEXT_OVERLAP` cannot see it (the inks graze rather than cross), `RULE_THROUGH_TEXT` cannot (no rule is crossed), and `SLIVER_GAP` cannot (it measures panel against panel). | Derive the following block's `y` from the headline's MEASURED end — `h = dk.measure_text([(title, False)], w, size, font=…)`, then place at `y + h + gap` — never a coordinate. If the layout genuinely wants them tight, the fix is still measurement: compute the small gap, do not hard-code the position. |

A build that ends `0 critical, N warning(s)` **saves fine** — warnings are judgment calls; the two
you most often accept deliberately are `OFFCENTER` on chip labels and `ESCAPES_CARD` on
intentional sticker/burst overhangs.

## 5 · Render stage failures

The shipped pipeline is one command: `bash scripts/render_deck.sh <deck.pptx>` — internally
LibreOffice (`soffice --headless --convert-to pdf`, with an **isolated per-run profile**) then
PyMuPDF rasterizes each page at a fixed 2× (~144 DPI) to `render/slide01.png … slideNN.png`
(plus `thumb_first/last.png`. The `<deck>.pdf` and a self-contained `viewer.html` preview are
**reserved hand-off deliverables**, NOT build output: pass `--deliverables` to park them at the deck
root once the deck is final. Re-rendering a deck already rendered? `--fast` re-renders only the
slides whose content changed; `--slides N[,M]` renders exactly the pages you name, for when you
already know which — neither combines with `--deliverables` or with each other.)
(zero-padded, no hyphen) plus `thumb_first.png`/`thumb_last.png`; then
`python3 scripts/lint_deck.py <deck.pptx> --renders render/`.

| Symptom | Cause | Fix |
|---|---|---|
| `bash: command not found` / `render_deck.sh` won't run (native Windows PowerShell or cmd) | There is no bash. The `.sh` files are thin shims that forward to the `.py` entry points; everything else in the toolchain is already cross-platform Python | Call the Python directly: `python scripts\render_deck.py <deck.pptx>` and `python scripts\check_env.py`. macOS / Linux / Git Bash / WSL keep using the `.sh` wrappers unchanged |
| `no such file: … .pptx` | The path didn't resolve — **most often a previous shell `cd`-ed somewhere else** and a relative path now points nowhere | Re-run from the deck folder, or pass the absolute path |
| `LibreOffice produced no PDF from … .pptx` (render_deck.py prints the soffice command, exit code, and stderr) | soffice failed — the deck is open in another app, or a **sandboxed runtime blocked soffice** (see SKILL.md's Codex sandbox note) | Read the captured stderr it printed; close any open copy of the file; in a sandbox, rerun just the render command with elevated/unsandboxed execution. Last resort: `pkill -f soffice`, wait 2 s, retry (each run already uses its own temp profile, so this is rarely the cause) |
| Renders look blurry when zooming into crops | Rasterization is a fixed 2× (~144 DPI, `fitz.Matrix(2, 2)` in `render_deck.py`) — plenty for the lint/critic loop | Zoom the pptx/PDF itself for fine inspection; the deck is unaffected — the PNG is only a preview. (If you must, raise the Matrix zoom in `render_deck.py`) |
| A font looks different in the PNG than in PowerPoint | LibreOffice substitutes fonts it doesn't have — the **pptx still carries the right font** | Judge geometry/lint from the render, judge the named font by opening the pptx; install the font locally if render fidelity matters |

## 6 · Render-lint hard findings (`lint_deck.py`)

These fail the exit code and must reach **0** before hand-off. Plain-word dictionary:

| Finding | Means | First fix |
|---|---|---|
| `OVERFLOW [edges]` | A block extends past the canvas edge in the *rendered* geometry | Same as build-time OFF_CANVAS — move/shrink; if build lint passed but this fires, a font substitution wrapped the text longer: shorten text or widen the box |
| `INVISIBLE TEXT` | Ink vs background contrast < 1.8:1 — unreadable (classic: default-black text on a dark card, because no explicit color was set) | Set an explicit light color on dark fills; the message prints both hex values so you can see the pair |
| `OVERLAP a×b in` | Two blocks intersect by that many inches | Move/shrink one so they separate cleanly (≥0.12 in gap) or nest one fully inside the other; decorative hard-shadow pairs are auto-exempt |
| `FOOTER collision` / `FOOTER-ZONE intrusion` | Content covers the footer text / dips into its reserved band | Keep content above the y-line the message states |
| `TEXT PADDING` / `CHIP/LABEL TOO SMALL` / `TEXT COLLISION` | Estimated wrapped lines don't fit the card/chip → text will kiss or cross the edge | Fewer words, smaller font, or a taller card — the message says how many lines it measured |
| `ORPHANED PUNCTUATION` / `WIDOW` | The last wrapped line is a lone `。`/`)` or a single glyph | Reword by ±1–2 characters, or widen the box a hair |
| `CJK TEXT without an EA font` | CJK characters in a run that resolves no East-Asian font → tofu risk off-machine, and no 避头尾. Same fault as build-time `CJK_NO_EA` and the same test (it borrows deckkit's `_has_cjk` / `_inherited_ea`), so the two cannot disagree | You are holding a **saved file**, not a live `prs`, so `dk.EAFONT` cannot reach it — reopen, retrofit, save: `p = Presentation(deck); deckkit.retrofit_ea(p, "Hiragino Sans GB"); p.save(deck)`. Then set `dk.EAFONT` at the top of the build script so the next build never gets here (see §2 tofu row); deckkit applies it automatically to CJK runs it creates |
| `META-ANNOTATION LEAK` | A visible run looks like an instruction to the builder ("placeholder", "TODO", "draft v2") rather than content | Delete/replace the text. **False positive?** If it's a genuine content word (a diagram edge labeled "draft"), rename to an unambiguous content phrase ("submits work") — cheaper than arguing with the lint |
| `EDITABILITY` | The slide is one big image with no native text — the user can't edit it | Rebuild the content as native shapes/text; images are backgrounds and figures, never the whole slide |
| `EMPTY/ORPHAN slide` | A slide with no content survived a refactor | Delete it or fill it |
| `UNEVEN CARD HEIGHTS` | A visual row of cards has mismatched heights — reads as sloppy | Give the row one shared height (the max), let inner text float |
| `TEXT ON IMAGE` | Render-pixel estimate: text sits on a photo/gradient with est. contrast < 1.5:1 — unreadable (the class solid-fill checks can't see; needs renders) | Add an opaque panel or scrim behind the text, or move it off the busy region (pixel sampling already accounts for an existing scrim) |

Render-time **advisory `[warn]`s** (never fail the exit code): `LOW CONTRAST` / `BODY CONTRAST`
(1.8–4.5:1 bands), `MISSING ALT-TEXT`, `MATH-FONT TOFU RISK`, `GROUPED-ONLY` content,
**`UNSOURCED NUMBER`** — plus the
**accessibility set**: `TEXT-ON-IMAGE CONTRAST` (the 1.5–3.0 band of the hard check above),
`NO SLIDE TITLE` / `DUPLICATE SLIDE TITLES` (screen readers navigate by unique titles; an
off-canvas-invisible title is the sanctioned trick for statement slides —
`deckkit.a11y_title(slide, "<title>")` makes it: a TITLE placeholder above the canvas, first in reading order,
skipped by OFF_CANVAS and DUPLICATE_TEXT; a plain text box there is an OFF_CANVAS critical), `READING ORDER` (title
should be first in z-order — add it first in the build code, or declare it with `a11y_title`; every
visual-language page does this itself), `NON-TEXT CONTRAST` (solid marks/lines
< 3:1 vs backing, WCAG 1.4.11), and `ICON CONTRAST` (the same floor for a recolored
monochrome icon; it is reported separately because icons are pictures and the shape-based
check skips them — the remedy is a darker tone of the same hue, or a plate under the icon).
Resolve or consciously accept per §7.

**Paint-order and deck-level codes `lint_deck.py` also prints, which this page used to omit.**
SKILL.md routes ANY finding here and tells you to report it in this page's plain language, so a code
the linter emits and this page never names sends you back to reading source. The first three are
PIXEL-BACKED — they disable themselves with a `[skipped] … NOT checked:` line when no renders sit
beside the deck, and `0 findings` with that line present is a different sentence from `0 findings`
without it.

| You see | What it means | First fix |
|---|---|---|
| `TEXT NOT VISIBLE` ✗ | Asked straight from the pixels: does this text line render ANY glyphs at all? Deliberately cause-agnostic, so it catches a picture, a group, a gradient, or a same-colour-as-its-ground block covering the text without needing to know which it was | Find what is painted over that line and move it, restyle it, or reorder it. Paint order is the usual cause: a shape added AFTER a text box draws on top of it while every geometry check stays green |
| `OCCLUSION` ✗ | A text block is N% covered by the **union** of everything painted over it — union, because the old per-shape threshold was slipped by a thing built from many small parts (a 150-tile field erasing a caption, a dashed rule of 40 boxes struck through a footnote) | Same as above. Do not chase the individual shape; look at what the region accumulates |
| `CAPTION NOT ALIGNED` ✗ | A caption under a multi-panel figure is off its panel's centre. The panels are ONE picture at unequal widths, so captions placed on the text grid (`ML + i*CW/4`) cannot line up by construction | Export each panel's span from the plotting script and place captions from the picture's PLACED rect (`dk.picture` returns the shape; `pic.left/914400` is the real x after `fit="contain"` letterboxing). PRE-FLIGHT 9 covers every OTHER label — this lint backstops only the captions-under-panels case |
| `TITLE-RULE MONOCULTURE` • | The same thin rule sits under the title at the same height on >60% of content slides — a `head()`-style helper stamped one treatment deck-wide | Rotate 2–3 title treatments (accent rule · eyebrow in a filled tab · left vertical bar · section ordinal · motif mark). The visual SYSTEM stays constant; you rotate the chrome, not the identity |
| `ONE-OFF CANVAS FLIP` • | Exactly ONE interior slide's canvas value departs sharply from the rest — reads as a mistake rather than a rhythm event | Make the flip RECUR as a divider family or a bookend, or return that slide to the deck's canvas. On the generated-template branch the plate stays on every content page and rhythm comes from imagery strength instead |
| `FLAT RHYTHM` • | With renders present: no light/dark or colour-temperature event anywhere across the deck — the rhythm map's Background-mode column is single-note | Give the deck at least one value event (a dark divider, a full-bleed hero, a warm-accent conflict page). Needs `./render` PNGs beside the deck or `--renders <dir>`; without them the check silently does not run |
| `FLAT TYPE` • | No run anywhere reaches 2× the body size — the deck has no typographic hero | Let one thing win per slide (the squint test). This is the type-scale drama rule failing measurably, not a style opinion |
| `REGISTRATION DRIFT` • | Consecutive slides' title tops differ by a hair (0.02–0.12in) on 2+ pages — the deck's masthead wobbles page to page | Pin titles to ONE y across the deck. Identical is calm and a deliberate jump is fine; a wobble is neither |
| `RAGGED LEFT EDGE` • | The horizontal sibling of the above, WITHIN one slide: two vertically stacked blocks start 4–12px apart — too small to read as an indent, too large to look aligned | Snap them to one x, or indent deliberately (>0.12in) so it reads as a decision. Four things are exempt by design and will never be reported: a label nested inside a card (that indent is the card's padding), a value label trailing its own bar (bars of different length MUST give different lefts), two elements too far apart to be compared, and any offset that recurs on 2+ slides (a repeated offset is a design decision — same logic as `ONE-OFF CANVAS FLIP`) |

**`UNSOURCED NUMBER` — how to read it.** It is *deck-level*: it fires only when a magnitude
(`$400B`, `81%`, `+46pt`, `2.3x`, `95 亿`) appears on a slide with no source stated **and no source
is stated anywhere in the deck for that same figure**. So a recap or divider restating a number
sourced on its own page stays clean — that is normal, good practice, and the reason the check is not
per-slide. Bare integers are excluded on purpose (page chrome `13 / 20`, section indices, years);
counting them made a first cut fire on 4 of 20 slides of a professionally-made deck.
- **Fix:** `deckkit.source_note(slide, "Crunchbase Q1 2026", as_of="30 July 2026")` — the per-slide
  provenance line; or cite it in the **speaker notes**, which count (a presented deck legitimately
  keeps the slide clean and the citation in the notes).
- **If the attribution is already there in prose** ("this is the example the README gives"), it is a false alarm —
  the source-phrase vocabulary is deliberately generous but cannot be exhaustive. Accept and move on.
- **If you cannot name where the figure came from, that is not a lint problem.** It is the
  never-invent floor: source it, go qualitative, or ask. This is the one advisory whose finding may
  mean the *content* is wrong rather than the formatting.

**`bar of means` (pre-flight, advisory — needs `--build`).** The build script computes a mean or
median and feeds that variable to a column/bar `native_chart`. A bar's length asserts "this value
fills the range from zero", which is a claim about a COUNT; over sample measurements it hides n, the
shape of the spread and any outlier, and invites reading two bar heights as if the samples did not
overlap. **Fix:** `designed_charts.distribution(out, groups, ...)` — it picks a box plot at n≥5 and
mean ± error at n=3–4 for you, overlays every observation, and prints which interval it drew.
**Ignore it only if these are POPULATION means rather than a sample** — that is a fair bar, and
nothing in the file separates the two, which is why this is advisory and not a failure. It stays
silent on a bar of counts and on a LINE of averages over time; both are legitimate.

**`LOPSIDED` on a deliberately asymmetric slide.** An editorial composition weighted to one side,
with the other half held as air, is a design choice — and "rebalance" is the one piece of advice that
would wreck it. Declare it: `deckkit.design_intent(slide, weight="left", reason="…")` (also
`"right"` / `"asymmetric"`); `envelope=` silences it too. Undeclared lopsidedness still flags, so the
declaration is the record of a decision, not a mute button.

**`[skipped] slide N: rotated/flipped group`.** That slide's shapes were **NOT geometry-checked** —
overlap, overflow, occlusion, density and type-scale all skip it. A rotated group's children are no
longer axis-aligned in slide space, and every check here reasons about axis-aligned boxes, so the
lint refuses to guess rather than invent overlaps. Ungroup it (or drop the rotation) to have it
examined. Note the related rule: two shapes **inside the same group** never raise `OVERLAP` — a group
is an authored composition (a badge on a card, an icon on a panel), and that is how layering is built.
A child colliding with anything OUTSIDE its group is still caught.

**`SCALE DRIFT` (deck-level, advisory).** The `type_scale` in `.deck-gates.json` and the type the
deck actually sets disagree. `render_deck --gate-check` requires that field; nothing used to compare
it to the artifact, so a deck could declare `{34, 24, 14}`, set 31/22/17 throughout, and pass both
gates clean. Two narrow checks only: **body** must be the size carrying the most text (a declared
14pt against a deck set at 17pt is the declaration being fiction), and **display/title** must at
least appear somewhere. A long tail of other sizes is NOT flagged — the skill's own five-slide
example uses twelve sizes, and any "every size must be a declared tier" rule would fire on correct
work. A hero number, a page number, a caption are all untouched.
- **Fix:** correct whichever is wrong — usually the declaration, written early and never revisited.
- Pass `--gates <path>` to point at a gates file elsewhere; with no file, the check is silent.
- **`SCALE DRIFT NOT CHECKED`** means most of the deck's text INHERITS its size from the
  layout/theme rather than setting it on the run, so there is too little explicitly-sized text
  to say which size is the body. It is reported rather than passed over in silence, because a
  silent skip is indistinguishable from a clean result. Set sizes on the runs (deckkit's
  `text()` always does) or read the scale by eye.

**`design_plan` is missing `signature_proof` on a deliberately plain deck.** A working session —
a lab meeting, a status update — is told by `design-by-purpose.md` to "optimise for fast technical
read, not polish", so it takes no aesthetic risk and has nothing to prove with a rendered PNG. The
escape is the one `agents/slide-design.md` already documents, now honoured by the gate: set
`"boldness": "conservative"` and write the signature move as **`deliberately restrained: <why>`**.
`signature_proof` then drops; `signature_move`, `carried_by`, `palette`, `type_scale`,
`icon_family` and `form_ledger` all stay required, and the phrase buys nothing above the
conservative dial. Do NOT reach for `{"design_plan": {"waived": …}}` for this — that switches off
palette contrast and the type scale as well.

**`TEXT WALL` / `CROWDED` on backup or appendix slides, or `UNDERFILLED` on the closing slide of a
deck that has them.** A thesis defense is told to "plan for backup/appendix slides for Q&A", and
that material is dense on purpose — judged as presented content it draws a finding on every backup
slide, and the trailing run also steals the closer's exemption by making a backup slide the last
one. Mark the start: `deckkit.design_intent(slide, role="appendix", reason="…")`. From there the
run is read at *briefing* density and the slide before it is treated as the closer. The bar RISES,
it does not vanish — a genuinely crammed appendix slide is still caught, which is what
design-by-purpose means by "dense is correct on these surfaces … but typed and organised, never
freeform cramming".

**When a finding seems wrong:** each check has documented escapes (shadow pairs, chip labels,
containment). Don't fight the linter in code — adjust the deck (rename, nudge 0.05 in) and move on;
if it's genuinely a lint bug, note it in the hand-off rather than shipping a `✗`.

## 7 · Advisory `[stats]` warnings — act or accept?

`[stats]` lines **never fail the run**. They exist so density/variety drift is visible, not to be
zeroed. Rule of thumb:

- **Usually act:** `TEXT-ON-IMAGE CONTRAST`, `NO SLIDE TITLE` / `READING ORDER` / `NON-TEXT
  CONTRAST` on any deck that will be distributed (enterprise recipients run the Accessibility
  Checker), `LOPSIDED` / `UNDERFILLED` / `DEAD BOTTOM` / `STRETCHED THIN` (the frame-fill rule's
  measured forms), `INVERTED TYPE HIERARCHY`, `TIMID COVER`, `SMALL TYPE` on a presented deck,
  `LAYOUT SAMENESS` / `SKELETON VARIETY` on 8+ slides, `NO NOTES` on a presented deck.
- **Judgment / taste:** `TEXT WALL`, `CROWDED`, `SIZE SPRAWL`, `CARD DOMINANCE` — a user who asked
  for fuller, denser slides has *chosen* these; accept them and say so in the hand-off.
- **Context:** `NO BUILDS` is noise on a self-read deck (`--selfread` suppresses the presented
  budgets); `BOTTOM-STRIP MONOCULTURE` wants the takeaway *device* rotated across slides, not removed.

Accepted advisories belong in the hand-off note in one line, plain-language first with the code in
parentheses — "kept the fuller, denser slides you asked for; the density advisory (TEXT WALL) is a
deliberate choice, not a miss" — silence reads as "didn't notice".

## 8 · Images: generation & sourcing

| Symptom | Cause | Fix |
|---|---|---|
| Generation call killed at ~2 min | Shell timeout, generation is slower than the default limit | Run generation in the background with a skip-if-done retry loop; never block the build on it |
| Generated image contains letter/digit-like squiggles | Models drift toward pseudo-text; the text-free gate rejects it | Regenerate with explicit anti-glyph prompt language ("no text, no letters, no numbers, no signage, no captions"); inspect at full size before accepting |
| Sourced photo has a watermark | Wrong source variant (stock preview) | **Reject and re-source — never crop, blur, or inpaint a watermark out** (that's laundering a license violation); Wikimedia/Openverse/press kits carry clean originals |
| Image looks off-palette against the deck | Raw photo dropped in without treatment | Run the palette treatment step (`image_fx.py`) so sourced images join the deck's color system |
| Wrong aspect / stretched | Placed with raw dimensions | Place with `picture(..., fit="cover")` and matching box ratio (16:9 canvas → generate 16:9) |

## 9 · CJK / bilingual issues

| Symptom | Cause | Fix |
|---|---|---|
| `CJK TIGHT LEADING` warn / CJK lines nearly touching (cramped) — or too airy | `line_spacing` set as if it were an em-multiple — **python-pptx floats are multiples of SINGLE spacing (~1.2× font size)**, so 1.28 actually renders ≈1.54× | Leave `line_spacing=None` (deckkit resolves per-script defaults), or stay within ~1.08–1.21 for CJK body (deckkit's default `CJK_LS = 1.12` ≈ 1.34× font size; never below ≈1.04 even on a dense deck — `references/multilingual.md` owns the ladder) |
| `CJK-LATIN SPACING` warn | Mixed `中文 Latin` spaced *and* unspaced in the same deck | Pick one convention (spaced is house style) and apply it everywhere — `pangu()` normalizes |
| CJK text much wider than planned | CJK glyphs are ~1.7–2× the width of Latin at equal pt | Budget CJK strings at that multiplier when sizing boxes (the width contract in `references/multilingual.md`) |
| Font renders as serif/wrong style for 中文 | EA font not set per-run; PowerPoint fell back | Set `dk.EAFONT` before building (§2). If the deck is already built or was not authored here, `deckkit.retrofit_ea(prs, "<face>")` is the fix for the file in hand (§4, `CJK_NO_EA`) |
| `PINGFANG ON MACOS` warn | The deck sets PingFang SC but THIS Mac has no PingFang file to load — it is a downloadable asset, not in /System/Library/Fonts — so every CJK line was measured in a stand-in | Switch `dk.EAFONT` to `"Hiragino Sans GB"` (on every Mac). Where PingFang is installed the warning does not fire: it measures and renders correctly — *CJK faces on macOS* in `references/multilingual.md` |

## 10 · FAQ one-liners

- **The linter flags something that looks fine to my eye. Ship anyway?** Hard findings: no — they
  encode failures that read fine at authoring zoom and break at presentation scale. Advisory
  `[stats]`: yes, if it's a deliberate choice, named in the hand-off (§7).
- **Can I hand-edit the .pptx afterwards?** Yes — everything is native and editable; that's the
  point. But re-running the build script **overwrites the file**, so either fold your edits back
  into the script or stop rebuilding after hand-edits (see `references/handoff-and-iteration.md`).
- **Why does the same deck lint clean here and dirty on another machine?** Different installed
  fonts → different wrap geometry. The lint substitutes metrics for missing fonts with ~1 line of
  slack, but a hard swap (CJK font absent) changes real geometry: install the font or switch to a
  cross-platform pair.
- **How do I re-run only the lint, without rebuilding?** Build-time: it runs inside the build
  script. Render-time: `python3 scripts/lint_deck.py deck.pptx --renders render/` — add `--json
  out.json` for structured findings, `--selfread` for a self-read deck's budgets.
- **Where do I see WHY a rule exists?** Each finding's rationale lives with its owner reference
  (`design-principles.md` for contrast/spacing, `multilingual.md` for CJK, `review-rubrics.md` for
  the critic's bar). This page stays symptom-first on purpose.
- **The build refuses to save (`strict` raise). Can I bypass it?** `lint_layout(prs, strict=False)`
  exists for debugging **only** — a deck with criticals is broken at presentation scale; fix the
  two-three findings instead, they're always cheap (§4).
- **Rendering works but everything is slow.** Measured on an 18-slide deck: the first render of a
  session is ~4.3 s (it also creates the LibreOffice profile), and every render after it is a flat
  **~2.9 s**. 🔴 **"Subsequent converts are fast" is not true and the belief is expensive** — there
  is no warm LibreOffice; each render starts one, and that start is ~2.5 s of the total whatever the
  deck contains. Page count barely moves it (a 1-slide deck renders in ~2.5 s, an 18-slide deck in
  ~2.9 s), which is why `--slides N` is not a speed flag. The one genuinely fast case is `--fast`
  with nothing changed — **0.07 s**, because it starts LibreOffice not at all. So: re-render freely,
  it costs seconds; use `--fast` for every iteration round; and do not restructure a build to
  "avoid renders", because rendering was never the expensive part of a build.
- **Something not on this page?** Run `bash scripts/check_env.sh` first (rules out environment),
  then read the error's owner section above; if it's genuinely new, the error text + the slide
  number + the build-script line are the three facts that make it debuggable.

## 11 · Source ingestion & long-source (`ingest.py` · `extract_pdf.py map/text/headings`)
Every message below is deliberate tool output, not a crash — each tells you the next move.

| You see | Cause | First fix |
|---|---|---|
| `⚠ NO extractable text (~0 words across N pages)` from `map` | The PDF is scanned / image-only or DRM-locked — there is no text layer, and no OCR is installed | Ask the user for a text-based PDF, OCR, or the specific chapters. Do NOT infer contents; vision-reading pages yields `verified? = N` claims only |
| `PDF is password-protected — can't read it` | Encrypted file | Ask for an unlocked copy |
| `can't open '…' as a document (…)` | Corrupt/truncated file, or a format fitz can't parse (`.md`, `.doc`, a half-downloaded PDF) | Re-download/re-export; `.docx`→`ingest.py doctext`/`office`; `.md`/`.txt` are read directly, no tool needed |
| `error: bad page range …` from `text`/`headings` | Reversed / out-of-range / sub-1 pages (often a TOC page number past the real page count) | Re-check against `map`'s page count |
| `(no embedded TOC/bookmarks — reconstruct a skeleton with headings …)` | The book has no bookmarks | Run `extract_pdf.py headings <src>`; if it reports no size/bold/caps outliers, fall back to fixed-size page windows |
| `python-docx not installed` / `openpyxl not installed` | Missing optional dep for `doctext`/`sheet` | `pip install python-docx` / `pip install openpyxl`, or use the printed alternative route |
| `LibreOffice (soffice) not found` / `ffmpeg not found` | Missing system tool for `office`/`frames` | Install it, or ask the user to export a PDF / supply a transcript |
| `conversion FAILED (rc=…) . soffice said: …` from `office` | LibreOffice couldn't read the file (corrupt, unsupported) | The quoted soffice stderr names it; ask for a re-export |
| `⚠ N formula cell(s) have no cached value` from `sheet` | The workbook was written programmatically and never re-saved by a spreadsheet app — formula cells carry no computed value | Open + re-save in Excel/LibreOffice, or get a CSV export; the blanked columns are NOT absent in the source |
| `⚠ this .docx has footnotes/endnotes — doctext does NOT extract them` | python-docx can't see those parts | Use `office` → PDF and read the pages if they carry content |
| `'…' has no video track (audio-only?)` from `frames` | The file is audio-only — there is no speech-to-text here | Ask for a transcript/captions (.srt/.vtt/.txt); never invent narration |
| `⚠ clamping to --every …s` from `frames` | The video is long; the 60-frame cap bounds the vision-reading load | Expected. To inspect a region closely, cut a sub-clip with ffmpeg and sample that |
| `⚠ VISUAL only: the SPOKEN narration is NOT captured` | Reminder printed on every `frames` run | The plan must carry the transcript-status line; spoken-track claims without a transcript stay `verified? = N` |

## Setup and version (moved here from setup-and-version.md)

Read this when `check_version.py` reports an update or `DIFFERS … at the same version`, and when `check_env.py --ensure` exits non-zero. Moved verbatim from SKILL.md (2026-11-07) so the main file can be read in full; both scripts print what they found, so skipping this file is never silent.


### When check_version reports an update

🔴 **On a COPY install the notice may say `DIFFERS … at the same version`, and that is not a bug.**
`--json` carries `drift: "content"` with a `differing` file list beside the usual `behind`. It means
the installed copy's FILES do not match main even though `VERSION` agrees — work lands between
releases, so the version string cannot see it, and a copy with most of `SKILL.md` missing used to
pass silently. The three options below are unchanged (a reinstall is still what brings a copy to
main); only the reason differs. Two things it cannot tell you, both stated in the notice: which
direction the difference goes, and whether it is instead your own edits to the installed copy — a
fork or a locally-patched install will report this every time, and `SLIDE_MAKER_NO_VERSION_CHECK=1`
is the way to stop it.

**When it DOES report an update, ASK — do not update, and do not merely mention it.** Run
`check_version.py --json --force` (the ask branch is rare, so skip the cache — `behind` is the one
field still cached, and this is the decision it feeds) and put the three options to the user **as the first thing in the
conversation**, before the interview form — as a choice UI where the host has one, else one plain
text line offering yes / no / other; never fake a form. **Spell out what each answer DOES — never
offer a bare yes / no / other.** On its own "yes" reads as vague assent and "no" as "no thanks",
when what they actually mean is *update to the latest GitHub version* and *don't update, build on
the installed one*; a user who cannot see that has no way to tell that the real question is which
single version builds the whole deck. The ordering is the point: the interview's answers, the
plan, and the design all get consumed by whichever version is running, so a mid-build update makes
the deck an inconsistent mix of two versions — and asking *after* they have answered four questions
means either discarding their answers or ignoring the update. Ask once, at the top, then build.

*(Per-deck AUTO WAIVER: do **not** stop. Default to **no — build on the installed version**, and say
so in the first FYI. Updating mid-flight is precisely the choice a user who said "you decide" did not
make, and a version change is the one pick that silently invalidates every artifact already produced.)*
- **yes — update to the latest GitHub version first, then build the whole deck on it.** DO IT
  YOURSELF — the user answered the question, not "give me instructions". `check_version.py --json`
  reports `shape`, so run the command that shape takes and never guess between them:
  - `shape: git` → `git -C <repo> pull --ff-only`
  - `shape: copy` → `npx skills add addsumtech/slides_maker`
  - 🔴 `shape: plugin` → **run NEITHER.** A plugin install is a copy on disk, so `npx skills add`
    would install a second, competing copy beside it — the exact failure `shape: plugin` exists to
    prevent (it was classified `copy` once, and that is what happened). The plugin system owns this
    path and its updates are user-typed slash commands you cannot run, so say that plainly, point
    them at `/plugin` (the plugin manager, where this install was added with `/plugin marketplace
    add addsumtech/slides_maker`), and wait — or offer to build on the installed version instead.
    Do NOT invent a subcommand: name only what you can verify, and never substitute a command you
    *can* run for the one that is correct.
  - `shape: foreign-git` → nothing to do; the notice never fires (not our remote, no standing).

  🔴 **Re-read SKILL.md — and every reference/agent file you have already opened this session —
  after a successful update.** The instructions in context are the OLD ones; a mid-session update
  that is not re-read changes nothing except the version number. Where the two disagree, the file
  on disk wins.
- **no — don't update; build on the installed version.** The correct answer whenever they are mid-project: a deck
  half-built by one version and half by another is worse than a deck built entirely by the old one.
- **other — they have local changes.** Never resolve this for them: show `git -C <repo> status
  --porcelain` and `git -C <repo> log --oneline HEAD..origin/main`, i.e. *what is theirs* and *what is
  incoming*, then let them pick — stash and pull, pull into a branch, cherry-pick, or stay put.
  **Never `git checkout .`, never `--force`, never `--replace` over an install you did not verify is
  clean.** 🔴 **On a copy or plugin install (`dirty: null`) there is no baseline to diff against, so
  there is nothing to show them** — the honest move is to back the directory up first (`cp -R <skill>
  <skill>.bak`), then update, then let them compare. Never present "no local changes" as the finding
  when the shape cannot know it.

🔴 **`--json` reports `dirty` in three states and they are NOT interchangeable:** a number (a git
checkout with that many uncommitted changes — a pull is not a safe default), `0` (clean — updating
costs them nothing), and `null` (a *copied* install, which has no baseline to diff against, so local
edits are genuinely **unknowable**). Report `null` as unknown. Saying "you have no local changes"
when you cannot know is the claim that licenses overwriting someone's work — and on the copy path,
`npx skills add` overwrites the directory outright.


### The toolchain check in full

🔴 **The moment the version is settled and BEFORE the interview, run
`python3 scripts/check_env.py --ensure` on a deck-BUILD ask.** It is the same silent-when-warm shape
as the version check: it imports the required pip deps (`python-pptx`, `pymupdf`, `Pillow`,
`matplotlib`, `numpy`), and if any are missing it **installs them into this interpreter** (pip, then
`--user` on an externally-managed env) — one fast install now instead of an `ImportError` at the step
that needs them. **Why here and not "when a render errors":** on a fresh machine the missing library
does not surface until the step that imports it, and the most expensive one is the **RENDER (Step 5),
the gate the critic loop waits on** — a missing LibreOffice or PyMuPDF there costs a diagnosis
round-trip and a re-run at the priciest moment in the pipeline. Catching it at Step 0 turns that into
one up-front install, which is the whole point (less wall-clock, fewer tokens). Cost on a warm machine
is ~0.1s and it prints nothing; opt out with `SLIDE_MAKER_NO_ENV_CHECK=1`.

**Act on the exit code — it distinguishes what you CAN auto-fix from what you cannot:**
- **`0`** — everything required is present (or was just installed) and LibreOffice is found. If it
  installed something it says so in one line; otherwise say nothing and go to the interview.
- **`3`** — pip deps are ready but **LibreOffice is MISSING**. It cannot be pip-installed (a system
  app needing a package manager / GUI download), so the script prints the one install command per OS
  and does not run it. **Surface that command to the user now** — LibreOffice is what Step 5's render
  needs, so a deck built without noticing will die at the render, after all the authoring is spent.
- **`1`** — a required pip dep could not be installed (a hard externally-managed block). The script
  prints the manual command; surface it, and do not add `--break-system-packages` on the user's behalf
  — overriding the OS package manager is their call.

This is a BUILD-ask step: a pure critique/audit/question run does not need the render toolchain, so
skip it there (the version check still runs — it is not gated on build). One shared `check_env.py`
owns both the `--ensure` auto-fix and the human-readable report, so "what is required" never drifts.


## Gated checks — what each hand-off gate enforces (moved here from gated-checks.md)

Read the section a gate names when it fails, or when SKILL.md sends you here. Everything in this file is enforced by a script (`render_deck.py --gate-check`, `codex_delivery_gate.py`, `lint_deck.py`, `deckkit.lint_layout`), which prints the failing section and its fix — that is why it could leave SKILL.md. Moved verbatim from SKILL.md (2026-11-07).


### Purpose sections, talk slot, coverage, deliverables, navigation, citations

🔴 **TWELVE of the thirteen purposes DECLARE required content, and the deck is held to it at
hand-off.** grant (aims · feasibility · risk) · progress/guidance committee (progress · plan ·
**ask**) · journal club (attribution · critique) · clinical case (presentation · investigations ·
management · outcome) · thesis defense (contributions · limitations · future work) · conference
talk (contribution · evidence · limitations) · job talk (track record · research plan · fit) ·
exec/investor readout (the ask · the number · the risk) · lab meeting (what changed · open
questions) · work status (outcome · the ask) · product pitch (positioning · benefits) · teaching
(objectives · worked example · recap). Each carries sections its audience is asked to judge
against, so a deck missing one is not a lean deck — it is a deck missing something the room needs.
`scripts/purposes.py` declares them and `scripts/check_purpose.py` looks for them in the built file
(both gate paths, CJK terms included, extend with `design_plan.purpose_section_terms`, waive in
writing). It binds ONLY when the recorded purpose matches a registry entry — anything else is NOT
CHECKED, never a guessed genre. **This is the `formats.py`/`check_surface.py` mechanism generalised
from SURFACES to GENRES**, and for the same measured reason: the shape of a genre is exactly what an
author under time pressure drops.
🔴 **A TALK ALSO HAS A SLOT, and the interview already asks for it** ("for a talk, give me the time
budget and I will confirm the slide count"). Record it as `content.talk_minutes` — both `--init`
scaffolds now show the field — and `scripts/check_talk_time.py` compares the BUILT deck against it
on both gate paths. It reads the SPEAKER NOTES only, because that is what gets said out loud (the
on-slide words are not spoken by anyone following PRE-FLIGHT 1, and counting both would punish the
decks that follow it), and it reports a BAND, never one number: 130-150 words per minute for a
word-delimited script, 180-220 characters per minute for CJK. **A script it has no sourced rate
for and cannot segment — Thai, Lao, Khmer — is NOT CHECKED by name rather than given a number**,
and a per-slide budget (`10 minutes each` / `每页 2 分钟`) is read as no budget at all, because
taken as the talk's length it makes a correctly sized deck look twelve times too long. `OVER THE SLOT` blocks — with how many slides' worth of
speech to cut — while `TIGHT`, `UNDER THE SLOT` and `ONE SLIDE EATS THE TALK` (a page carrying more
than a quarter of the slot) are notes. **No budget recorded, or notes on fewer than half the slides,
is NOT CHECKED and says which** — a deck that will be READ is never late, and an estimate built from
a third of the talk is worse than none because it reads like a whole one. Waive in writing
(`{"talk_time": {"waived": "…"}}`) when the slot really did change.
🔴 **"PASSED" IS NOT "CHECKED" — read the COVERAGE line.** Every gate run now ends with
`[gates] COVERAGE: N section(s) ran — X bound, Y NOT CHECKED`, one row per section that could not
bind and why. Measured, which is why it exists: three gates were silent on every deck because
nothing asked for the field they read, the template gate could bind to 1 of 11 registered
templates, and each was found by a human reading a transcript rather than by the tool. A row is
not a failure — a section that does not apply to this deck is correctly unchecked — but an
unread ledger is how a capability goes quietly unused. The Codex delivery gate prints the same
tally.
🔴 **THE DELIVERED PDF NOW KEEPS ITS ALT TEXT, AND THERE IS A SPEAKER HANDOUT.** `--deliverables`
exports through LibreOffice's PDF/UA filter: measured, the plain export produced a tagged PDF with
ZERO `/Alt` values, so every image description the a11y gate demanded stopped at the .pptx — in
the one artifact that gets emailed. It is a SEPARATE export from the render's: putting the filter
on the rasterization path changed a pixel check's verdict on another LibreOffice, so the render's
PDF stays plain and the accessible copy is made at hand-off.
It also writes **`<deck>-notes.pdf`**, one page per slide with the slide above its notes: this
skill requires speaker notes and reads them to estimate the talk's length, and then handed over
two artifacts in which they are invisible. A deck with no notes gets no handout and says so.
🔴 **A PRESENTED DECK IS NAVIGATED, NOT JUST READ — and until now this library could not make one
jump.** Measured: `hlinkClick` appeared only in `_EA_FOLLOWERS`, a constant listing XML element order,
and `click_action` in no file at all, so every "backup slide" this skill ever built was reachable only by arrowing past
everything in between — which is exactly why prepared answers go unused. `dk.link` (shape → slide,
shape/run → URL, **scheme-guarded**: a link target usually comes from the untrusted material the
deck was built from), `dk.agenda(..., targets=[...])` (a contents page you can present FROM, and
the section-progress page a long deck repeats) and `dk.back_link` (the other half of a jump) close
it. **Read `references/navigation-and-qa.md` whenever the deck will be presented live and the room
can interrupt** — a defense, a committee, a conference talk, a board readout, anything with an
appendix. Record the questions you expect as `content.qa`
(`[{"question": …, "slide": <the backup that answers it>}]`, in both `--init` scaffolds) and
`scripts/check_qa_backup.py` checks the BUILT file on both gate paths: a backup slide nothing links
to BLOCKS (`PREPARED BUT UNREACHABLE`), as does a slide number the deck does not have, while
`NO WAY BACK` is a note. **Nothing recorded is NOT CHECKED** — anticipating questions is a practice,
not a law, and a gate demanding it of every deck would only teach authors to record an empty list.
🔴 **AN ACADEMIC DECK CITES FROM ITS .bib, NEVER FROM MEMORY.** Measured: nothing in this skill
ever read a bibliography — `sources_page` and `source_note` take STRINGS — so every citation it had
ever built was typed by hand, which is where a year drifts by one and a middle author disappears.
`scripts/citations.py` parses the BibTeX and derives **both** the in-text marker and the reference
line from the SAME entry (`cit.in_text` / `cit.reference_page`, `numeric` or `author-year`, with
`etal=`/`amp=` so a Chinese deck writes 等 and 与), and **it REFUSES an entry with no
author/title/year instead of printing `n.d.`** — under the never-invent floor a plausible-looking
citation is worse than a missing one, because nobody downstream can tell it from a real one. Record
`content.citations` (`bib` · `style` · `keys` in cited order) and `scripts/check_citations.py`
checks the BUILT file on both gate paths: a `DANGLING MARKER` and a cited key that is `NOT IN THE
LIST` block, an `UNCITED` entry is a note. **Read `references/citations-and-bibliography.md`
whenever the deck cites published work** — it also carries the measured reason
`reference_page` sets the deck's link colour (a renderer paints a linked run in the THEME's hlink
colour whatever fill the run carries, so one references page came out half navy and half Word-blue,
decided by which entries happened to have a DOI).
🔴 **Every section list was DERIVED FROM `design-by-purpose.md`'s OWN PROSE, never invented** —
teaching's objectives/example/recap were already in its Layout and Signature lines, the lab
meeting's "what changed" and "open questions" are its Signature line verbatim. Where a genre's prose
names no required section, none was added: a check that fires on good decks is how people learn to
ignore checks.
🔴 **The thirteenth, `webinar`, has NO section list on purpose — it is a delivery MODE, not a
genre.** The same session can be a lecture, a pitch or a readout, so a list attached to it would be
a guess about which. What it constrains is the MEDIUM, already held by the type floors and
`formats.py`'s safe zones — and `check_purpose` recognises the medium words and asks you for the
GENRE instead of silently checking nothing.
Each genre also carries one fidelity rule beyond never-invent — a pilot stated as a pilot, open work
that reads as open, their claim separable from yours, a simplification flagged to a novice, and on a
clinical case **de-identification, which is the one irreversible item on this page**.


### The user's own files, checked against themselves

> **🔴 THE USER'S OWN FILES, checked against themselves — before the planner reads them.** Record the
> files in the gate record (`content.sources`: `[{"path": "report.pdf"}, …]`, relative to the deck
> folder; `[]` for a deck with no user material) and run
> `python3 scripts/source_check.py material <deck-dir>`. It finds a total that is not the sum of its
> rows or columns, shares off 100% beyond rounding, and the same table in two files with a cell that
> disagrees. Each finding is a **「材料自相矛盾」 open question at the content checkpoint** — only the
> user can say which value is right (auto mode: decide, give the basis, and list it in the hand-off) —
> recorded as `content.material_check: [{"id": "M-…", "resolution": "<which value, who said so>"}]`.
> The gate later traces **every number on the built slides** to these files
> (`source_check.py numbers <deck-dir>`): a figure rounded, converted or worked out goes in
> `content.numbers` as a `source_value` / `derived` row the gate re-checks; one read off a picture is a
> `from_image` row and is reported as not machine-checked. Images, scanned PDFs and .doc/.xls are
> UNREADABLE — ask for a .pdf/.docx/.xlsx/.csv export when the numbers matter.
> `source_check.py numbers <deck-dir> --write-rows` records the unambiguous rows for you (one file figure
> that rounds to the slide's, or the same figure in another unit — each tagged `auto`); read what it wrote,
> delete a wrong one, and decide the rest yourself.


### The icon waiver's category is verified against the pages

🔴 **The category is a claim about PAGES, not about the deck — and it is VERIFIED against the
built file** (`motif-dominant` needs a real loud motif in the file, `tiny-deck` a real tiny deck,
`template-locked` a real template). A deck-level reason may not cover pages the reason does not
reach: `motif-dominant` on a deck whose roster pages carry no motif at all is the measured failure
— a coherence argument overriding a stated default with no per-page test, and the first human
reader's first note was "icons should be here". Re-decide page by page; the honest answer is
usually neither zero icons nor an icon everywhere, but icons on the pages where they do work
nothing else on the page is doing (three DIFFERENT KINDS of fact side by side; the one row a
reader scans FOR an item) and none where another element already encodes the distinction (a
position map, semantic colour, numbered routes, the motif itself).
`design_plan.icon_none_category` + `icon_none_checked: [slides]` (Codex: an `icon` waiver with
`category`). A bare "not category-rich" no longer clears it, and the category explains the REST of the
deck — it is **never** a licence to drop icons from the categorical slides that do have them (a
motif-dominant deck may still put icons on its one roster/preview page, as this skill's own UK-labour
deck does on its two 3-item slides). 🔴 **But icons must ENCODE, not decorate** — a topic-stamp beside
a lone big number or a single statement is decoration that fails the 1-second-decodability floor
(`design-must-be-meaningful`); the default is "icons on the categorical/conceptual slides," not "an
icon on every slide." **(3) diverse formats** (not a card grid repeated) — musts 2–3 are
*applied where they help or justified where not* (a must to consider + apply, never a blank per-slide
quota — still smart about where/when). A plan that defaults its look, over-relies on one format, forgets
icons, or — when builds are opted in — leaves a built slide half-staged or forgets builds where they'd
clearly help is **not ready** — send it back to the art director.


### Accessibility floor

- **Accessibility is a FLOOR, not a nicety.** `lint_deck.A11Y_CODES` — missing alt-text, untitled or duplicate-titled slides, reading order, non-text contrast — is held by `--gate-check`'s `a11y` section and by the codex gate from **one shared list**, because a floor kept in two places is how one runtime quietly stops enforcing it. 🔴 **Decodability is now MEASURED, not asserted.** Three checks, each turning a rule this skill already stated into something countable, all added after a first human reader asked three questions of a deck that had passed every gate: **`MOTIF_UNEXPLAINED_AT_FIRST_USE`** — the stranger test is about FIRST appearance, and the old check cleared on a legend *anywhere*, which is the deferred reading SKILL.md calls "a FAILED test written as a passing sentence"; **`UNNAMED_REPEATED_MARK`** — four or more identical marks with no text within reach are reported, because unlabelled repetition reads as texture whatever you meant by it, and such a group is invisible to every other check (not text, not tagged, trivially clears contrast); and the **icon waiver's category is verified against the built file** — `motif-dominant` needs a real loud motif, `tiny-deck` a real tiny deck, `template-locked` a real template, and the waiver must name EVERY flagged slide, not a subset. Only the **unambiguous** subset blocks (`lint_deck.A11Y_BLOCKING`): a shape either carries a description or it does not, two slides either share a title or they do not, a ratio either clears 3:1 or it does not. **`NO SLIDE TITLE` stays advisory on purpose** — lint's own message calls an off-canvas title "a sanctioned trick for statement slides", so the skill EXPECTS slides that look untitled, and measured on an ordinary well-built 11-slide deck it fired once, on the closing slide. A gate that fires on a deck built exactly to spec is not a floor; it is training for the waiver reflex. Waive in writing (`{"a11y": {"waived": "<who reads this deck, and how>", "waived_category": "…"}}`) and say so in the hand-off note. `scripts/palette_audit.py` now also simulates deuteranopia/protanopia/tritanopia and names any pair that stops being two colours — `dk.OKABE_ITO` was recommended for years with nothing checking it.


### Material-probe carve record

> 🔴 **The carve is now RECORDABLE, which it was not:** `{"material_probe": {"waived": "<which
> template / which mimic / how many slides>", "waived_category": "registered-template |
> provided-template | mode-a-mimic | tiny-ask"}}`. Both gate paths accept it and both refuse
> `conservative` as a category, because this block says restraint is a material decision too. Before
> this the gate had no waiver arm at all, so a deck on a registered template had to invent a probe
> artifact and write a note explaining that the gate and this text disagreed — a rule whose
> documented exception cannot be recorded forces a false record.


### Build-time lint — every CRITICAL and why

  non-blocking report, e.g. a known off-canvas bleed). This is the cheapest place to catch
  the mechanical layout faults: it runs in-process in milliseconds, *before* the slow render +
  visual-critic round, and walks **every** shape — however it was placed, the grid helpers or raw
  coordinates — reasoning about each label's **ink** rectangle (where the glyphs actually land), so it
  stays quiet on the generously-sized frames real builds use. It **hard-fails (CRITICAL)** on seven
  things: content (text ink / a card / a non-bleed image) **off-canvas**, text **overflowing** a visible
  box, **text-on-text** overlap, a **connector routed through a block** (`CONNECTOR_IN_BOX`), a **decorative RULE
  drawn through a text block's ink** (`RULE_THROUGH_TEXT` — a divider/hairline placed at a hand-picked `y`
  that the text above it later grew into; derive the rule from the block's measured end, never a guessed
  coordinate), **a slide part that violates its own schema** (`OOXML_SHAPE` — the cardinality and order
  of the elements this toolkit writes by hand. 🔴 This is the only defect class where the file **does not
  open at all**, and it is the one every other check here is structurally blind to: they are geometric,
  pixel-based or semantic, and none asks whether the part is well-formed. Measured: two `Build(s)` on one
  slide left TWO `<p:timing>` elements — `save()` silent, LibreOffice happy, `lint_layout` clean, and
  `preflight_check.py` read the *duplicate* as more compliant, so the deck got a tick for the thing that
  broke it; the first human signal would have been PowerPoint offering to repair the file. `anim.apply()`
  now refuses a second call outright — a second Build's steps were never in the first's sequence, so
  keeping either tree ships a click order nobody wrote — and this code is the net under it, because the
  next hand-written element will not carry its own guard), and **CJK runs with no `<a:ea>` font** (`CJK_NO_EA` — set
  `deckkit.EAFONT` before building; catching it here saves the render round-trip lint_deck previously
  needed. When it fires anyway, **`dk.retrofit_ea(prs, "<face>")` on the line above the lint** is
  the fix for the deck in hand — setting `EAFONT` cannot be, since the runs already exist — and it
  covers the groups, table cells, fields and chart text this check is blind to. Pass the face unless
  `EAFONT` is set; it raises rather than fixing nothing. `EAFONT` afterwards keeps the NEXT build
  clean, except on a redesign fix-pass, whose runs never reach `set_font()` at all); it **warns** on **display numerals in an old-style figure face** (`OLDSTYLE_FIGURES` — digits at mixed heights make a big number visibly bob; the figure components resolve a lining face themselves via `deckkit.numeral_run_face`, so this fires only on hand-set runs — a taste call, deliberately not a build blocker), on a label/figure **escaping its card**, a **single
  line left off-centre** in a card, content **reaching the footer**, and **two panels nearly
  touching** (`SLIVER_GAP` — a 0.005–0.10in seam between panels, or a panel and a picture: the
  hand-picked-pitch bug). It also warns on the two faults a PER-SLIDE check structurally cannot
  see, both measured on a delivered deck *after* both lints had reported clean: **`DUPLICATE_TEXT`**
  — the same string rendered by two separate shapes on one slide, whose real causes are an
  ORPHANED copy of an earlier layout left behind by repeated patching (the tell: your coordinate
  edits appear to do nothing, because two layouts are running at once), a component's own
  auto-label printed beside a hand-written one, or a name repeated in both a list and the diagram
  under it — and **`CHROME_SLOT_DRIFT`** — a per-slide source line that does not sit where the rest
  of the deck puts its own. 🔴 **The fix for slot drift is never to nudge the strays**: the slot was
  a constant each page applied by hand, and a rule a page can decline to follow is not a contract.
  Route every source line through ONE helper that ignores any x/y the caller passes. *(Measured:
  11 source lines, 8 pinned and 3 placed wherever their page's last block ended — one rendering
  `as of <date>` inside a diagram box. Prose held 8 times out of 11.)* (Each code's plain-language


### Sameness and timidity

> **One of those gates is SAMENESS, and it is the one that can send you back to the build.** The
> deck-level monotony signals (`LAYOUT SAMENESS` · `SKELETON VARIETY` · `CARD DOMINANCE` ·
> `BOTTOM-STRIP MONOCULTURE` · `TITLE-RULE MONOCULTURE` · `ENVELOPE MONOCULTURE` · `FLAT RHYTHM`)
> were measured on every deck and blocked nothing — printed as advisories under a line saying they
> were advisory. **≥4 distinct ones, with at least one structural, now block the hand-off.** It
> applies only to a deck that is ≥8 CONTENT slides (cover, closer and any declared
> `design_intent(role="appendix")` run excluded), landscape, and not `--surface` — calibrated by
> building and linting decks in the registers this skill itself prescribes, where a 6-slide status
> update, a rednote carousel and an appendix-heavy defense deck all trip 3+ signals *legitimately*.
> **Repetition alone does not block; four independent kinds of it do.** Type drama (`TIMID COVER` /
> `FLAT TYPE`) is deliberately NOT counted — it is one fact twice, and the skill's own
> must-stay-clean fixture emits both.
> Where the repetition IS the design, say so — the escape is a written reason, not a flag:
> ```json
> "sameness": {"waived": "<why this deck repeats on purpose — name the register>",
>              "waived_category": "series-frame | register-uniform | template-locked | reference-run | user-waived",
>              "codes": ["<exactly the codes the gate reported>"]}
> ```
> The `codes` list is the freshness binding, the cheap version of `critic.sha256`: a waiver written
> for a different state of the deck does not certify this one. **This gate is deliberately about
> MEASUREMENT, never taste** — whether a deck is *timid* stays the critic's distinctiveness axis and
> stays non-blocking at `balanced+`; whether it *repeats itself* is a share of slides agreeing with
> each other, which is a defect with a concrete fix. That is the skill's own test for what may hold
> a deck (`agents/critic.md`), and it is why these two live on opposite sides of it.
> **Why a separate flag exists at all:** the gates used to be reachable only through
> `--deliverables`, and the paragraph above deliberately makes that a *decline-able offer*. So on
> every deck where the user said "no PDF, thanks", the strongest gate in the skill never ran — and
> nobody could see that it hadn't. A gate whose execution depends on an unrelated user preference is
> not a gate.
>
> **🔴 The other one is TIMIDITY — the counterweight, and the newer half of the same idea.** Every
> blocking signal above punishes a deck for being too MUCH or too SAME. Nothing could hold one for
> being too SAFE: `TIMID COVER` / `FLAT TYPE` are excluded from the sameness composite, and the one
> force that can call a deck forgettable — the critic's distinctiveness axis — is non-blocking at
> the default dial and lives inside a review the user may decline. **Measured, on a real build: a
> 12-page deck was iterated ten times, every pass driven by an advisory, and every pass made it
> flatter** — the dark pivot page deleted for `ONE-OFF CANVAS FLIP`, content cut for `TEXT WALL`,
> the type scale collapsed for `SIZE SPRAWL`. Each of those advisories names the ambitious repair
> FIRST ("enrich with a second column of substance", "repeat the treatment as a divider family");
> subtraction is merely the cheaper way to make the number disappear, and **with feedback on one
> side only, the cheap way always wins.** The user's verdict was that *the design had got weaker* and nothing in the
> pipeline had said so. So: `TIMID COVER` · `FLAT TYPE` · **`TEXT-ONLY DECK`** (most content slides
> carry no chart, no figure, no drawn form — every page's protagonist is a sentence) ·
> **`MONOTONE INK`** (the rendered pages are effectively greyscale), blocking at **≥2 with ≥1
> structural** (the two type signals are one fact twice, so drama alone can never hold a deck).
> It stands down under `boldness: conservative` with a recorded `deliberately restrained:` move —
> there restraint IS the position — and under the same size/aspect floors as sameness. Where the
> quiet is the design, name the register:
> ```json
> "timidity": {"waived": "<the register, named>",
>              "waived_category": "register-restrained | text-is-the-artifact | template-locked | user-waived",
>              "codes": ["<exactly the codes the gate reported>"]}
> ```
> 🔴 **When it fires, take the repair the advisories name first, not the one that deletes.** The
> measurable half of timidity is now gated; the unmeasurable half is still the critic's, and this
> is the moment to notice you have been optimising a warning count instead of designing.


### What --deliverables requires in the gate record

**`--deliverables` refuses to run until `<deck-dir>/.deck-gates.json` records that the Step-2
design plan, the Step-5 critic and the Step-6 provenance pass actually ran.** Write it when the
critic loop converges — `{"critic": {"verdict": "consent", "rounds": N}}`, **the Step-1 arc
competition** (`{"content": {"arc": {"chosen": …, "rejected": [{"name": …, "why_lost": …}],
"divergence": …}}}` — the losers and their clauses ARE the artifact, since `picked
contribution-first` on its own is a sentence anyone can write without a competition having
happened; `{"content": {"waived": "<why this deck had one possible arc>"}}` if it genuinely did.
This joined the file because the arc was the one Step-1/2 decision whose verdict reached only the
*conversation* while every other one reached this record — and the Codex path had already been
binding it), the design plan's
`boldness` / `signature_move` / `carried_by` / `form_ledger` / `icon_family` / `palette` /
**`style_pick`** (the TOPIC-adapted look choice — `<preset|bespoke|generated register> for <domain> ·
beat <nearest rival> because <clause> · anti-pick avoided: <the domain / image cliché>`, or `n/a —
<locked template | mimic | provided>`; run the ranked contest in `references/design-by-topic.md`
(domain → apt presets → ANTI-PICK + CLICHÉ GUARD) so the look fits the SUBJECT, not a reflex — it
governs the design-a-clean, bespoke, AND generate-a-template branches alike) /
**`motif_generates`** (background · markers · one page whose geometry IS the motif — a motif that
only recurs is an ornament with a schedule; carved out, like `signature_proof`, under a
`conservative` dial with a recorded `deliberately restrained:` move) /
**`image_sources`** (one row per CONTENT IMAGE carrying its EVIDENCE TOKEN — `slide <n> | <subject>
| sourced — <origin> (<licence>)` · `provided — user (own material)` · `generated — <tool>` ·
`searched (Commons, Openverse), none found → generated, flagged illustrative` · `… → native form`;
the grammar and the REFERENT RULE that picks between them live in `references/image-generation.md`,
and a deck with no content images writes the string `n/a — <why>`, exactly like a `logo plan: n/a —
…` line. The tokens are not taken on trust: `scripts/check_image_provenance.py` — run by BOTH gate
paths — holds each one against `assets/**/sources.json`, the ledger `scripts/fetch_images.py`
writes, and against the built deck's own text. Two claims it makes checkable for the first time:
a `searched, none found` rung must be backed by a RECORDED search (and an `unreachable` network is
refused as one — a blocked host is not evidence that no photo of Amsterdam exists), and an
attribution-required photo must be CREDITED ON A SLIDE, not merely licensed in the plan) /
**`type_scale`** (the three tiers as numbers — SIZE SPRAWL tells authors to draw sizes "from the
deck's declared type-scale tokens", and this is where they get declared) / **`signature_proof`**
(the ANCHOR PROOF — a LIST `[{"role": "signature"|"complex"|"data", "slide": N, "png": "<rendered
png>"}, …]`, one entry per anchor: the rendered evidence that the signature move SURVIVED
the build, that the design HOLDS the deck's densest page, and that the charts speak its visual
language. A move that exists only as a sentence gets sanded back to the safe catalogue and nobody
notices, because the plan still reads bravely — and a design proved on one spacious page tells you
nothing about the other two failures), and the provenance pass's **per-claim
`claims` list, never a summary tally** (a tally is written by the same pass that would have skipped
the refutation). A gate you deliberately skipped is **waived in writing** — never omitted; the tool
prints the reason, so a skip is visible instead of invisible. 🔴 **The CRITIC waiver must be
CLASSIFIED, not just written** — an unclassified one is indistinguishable from never having run
the loop, so the gate rejects it (the `design_plan`, `provenance` and `density` waivers take a
written reason only — the category is required for the critic alone):
```json
{"critic": {"waived": "<a sentence someone can disagree with later — ≥24 chars>",
            "waived_category": "already-reviewed-minor-edit | cap-reached-majors-open | external-deck | no-dispatch-on-host | user-waived",
            "inline_ran": true}}
```
`no-dispatch-on-host` = the runtime cannot dispatch a subagent (and it **additionally requires
`inline_ran: true|false`** — "ran inline in my own context" and "was never reviewed" are different
claims, and the hand-off note reads identically for both unless this file separates them) ·
`already-reviewed-minor-edit` = a 1–2 slide edit to a deck that already passed its loop ·
`user-waived` = the user was asked and chose to ship over it · `external-deck` = a deck this skill
did not author (redesign diagnosis / critique-only run) · 🔴 **`cap-reached-majors-open` = the loop
RAN to its round cap and majors are still open** — the other four all describe a loop that was
SKIPPED, so this is the only honest label for the commonest non-consent ending, and it
**additionally requires `open: ["<each surviving finding>"]` (non-empty) and `surfaced_to_user:
true|false`**. Reach for it instead of `user-waived` whenever the loop ran: `user-waived` is a claim
about a conversation, and writing it for a conversation that did not happen is exactly what
classifying the waiver was meant to stop. **If none of the five fits, the honest move
is to run the critic.**
This file is the hand-off's evidence, not a formality: the model that
skips a gate is the same model that would write the note claiming it ran, so both produce identical
prose and only an artifact tells them apart (`references/handoff-checklist.md` lists it).
The `critic` block is **written by `validate_review.py --record`, not by hand** (Step 5) — you supply
only the two blocks no tool can produce for you: the whole `design_plan` block enumerated above and
the provenance pass's per-claim list. *(The one exception: `--record` writes a CONSENT record from a
real review, so it cannot produce the waiver shape above — a waiver is always hand-written, which is
exactly why it must carry its category.)*


### preflight_check.py — the four hard FAILs that are not numbered items

**It also emits four hard FAILs that are NOT numbered items** — each is a defect no geometry check
can see, so when one fires, read it and fix the deck rather than routing around a check whose rule
was never written down: **(i) mono overflow** — `code_block` sets `word_wrap=False`, so a too-long
line does not wrap, it OVERFLOWS its panel, and a broken command line is not a cosmetic defect but a
*wrong* command *(measured: a shipped deck's `npx skills add …` install line rendered as three lines
and copied back as a repo path that 404s — the one line a persuaded reader must transcribe exactly
was the broken one)*; a line within 15% of its box is reported as **tight**, not clean, because the
default `MONO` is Consolas — absent from macOS and most Linux — and the substitute face is wider,
which is how the historical failure fit with ~10% margin and broke anyway. **(ii) mono face not
installed** — same cause, reported outright; fix it by setting a `MONO` that exists on the render
box, not by shortening the line until it looks fine locally. **(iii) Latin→full-width adjacency** —
a space appears BEFORE a full-width mark that follows a Latin run (`原生 PPTX 。`, `既搭 deck 、又给它
打分`, `（第 3 、 5 步）`). The renderer's CJK/Latin auto-spacer inserts the gap and python-pptx has no
switch for it, so the adjacency ITSELF is the defect: reword so a CJK glyph precedes the mark, or
drop the mark *(shipped on 5 of 12 slides of a real deck and caught only by a human at 5× zoom)*.
**(iv) non-positive text box** — `h = card_h - 1.42` with `card_h = 1.30` stores −0.12; the run
overflows a box that has no inside and every geometry check stays green because there is nothing to
overlap. `deckkit.text()` now raises at the call site, so a FAIL here means the box was built by
other means. A box under half a line of its own type is ADVISORY, not a FAIL.


### notes="none" when the user declined the spoken script

🔴 **And `notes="none"` when the user declined the spoken script** —
`dk.declare_delivery(OUT, "presented", builds="static", notes="none")`. Exactly the same argument
one rule later: `NO NOTES` fires on a presented deck with empty speaker notes, and a user who asks
for the script to be removed has made a decision that had nowhere to live, so the warning fired on
every lint run forever and was waived by hand each time. 🔴 **It silences that ONE warning and
nothing else — the word budget is deliberately NOT raised.** The skill's position is that the
sentences belong in the notes, so a deck carrying them on the slides instead is a real tension worth
still seeing; moving the ceiling would use the tooling to endorse what the skill argues against.
`selfread` · `surface`. **Pass `builds="static"` on a presented deck whose user opted OUT of
appear-builds** (`dk.declare_delivery(OUT, "presented", builds="static")`): the builds choice is a
user decision exactly like the mode, and it was the one still carried by memory — without it
`--static` has to be retyped on every lint run or `NO BUILDS` fires on a deck that is static
*because they chose that*. It writes `delivery` into `<deck dir>/.deck-gates.json`, which **both**
`lint_deck.py` and `render_deck.py --gate-check` read, and a recorded value beats a conflicting
flag in both (they say so and name the file). Why it is a 🔴 and not a convenience: a mode that
lives only in flags is a fact carried by memory, and it gets dropped. Measured on a delivered
14-page self-read deck — 20 `[stats]` lines with no flag, 10 with `--selfread`; the ten were the
~40-word *presented* budget applied to a deck nobody speaks, plus "14 of 14 slides have empty
speaker notes". Half the advisory output was noise the tool generated by not knowing what it was
looking at, and noise is what teaches people to skim gates. (`--briefing` is lint-only and is NOT
recordable — `render_deck.py` has no briefing floor, so recording it yields a deck that lints
clean and cannot pass hand-off; the lint refuses it by name and says why.)


### Deck stats — what each [stats] warning measures

reading **load** (latin words + CJK chars/2) vs the ~40-word presented budget · **text% / ink%
coverage** vs its role's OCCUPANCY band (cover/divider ~25–35 · exec/summary ~45–60 · technical/evidence ~55–70; past ~70–75 is `CROWDED`) — note the lint measures INK, so read the bands as ink, not as their whitespace complement · **max font pt** · shape/picture/chart counts ·
**build** presence · **sim↑** (layout-skeleton similarity vs the previous slide); deck-wide it
prints the **font histogram + type-drama ratio** and **builds/transitions n/N**. Its `[stats]`
warnings name the rule they measure — **`TEXT WALL`** (word budget blown → cut copy to notes or
split), **`HOLLOW FILL`** (the page reads as full but most of its ink is a drawn CONTAINER — occupancy is a bounding-box union, so an outlined frame counts its whole footprint and a page carrying four characters inside one measured 49%. 🔴 **Ask whether the FORM is right before touching the spacing**: every other warning here points at geometry, and the repair for this one is usually to demote the container, not to re-space it), **`CROWDED`** (occupancy past ~70% — role bands: cover 25–35 · exec 45–60 · technical 55–70 →
subtract or split, don't shrink), **`LAYOUT SAMENESS`**
(3 consecutive slides share one skeleton → the §1.2 skeleton-rotation rule failed), **`FLAT TYPE`**
(no typographic hero → the type-scale drama rule failed), **`SMALL TYPE`** (body-median under the
canvas-relative ≈18pt-equivalent floor → fewer words, bigger type), **`SIZE SPRAWL`** (>3–4 font sizes
on one slide → use the declared type-scale tokens), **`NO BUILDS`** (presented deck with no
appear-builds → the motion manifest failed *unless the user opted out of builds* — then pass
`--static`), **`SKELETON VARIETY`** (<4 distinct layout skeletons
across an 8+-slide deck → the canvas architecture barely rotates), **`TIMID COVER`** (slide 1's
largest run under 2× body → the cover lacks poster scale), **`FLAT RHYTHM`** (when render PNGs are
present via `--renders`/`./render`: no light/dark or colour-temperature event across the deck → the
rhythm map's Background-mode column is single-note), **`WEIGHT MONOCULTURE`** (the deck puts its
visual weight on the SAME side page after page — a share, never a per-slide verdict. One lopsided
page is composition and this skill asks for it; `LOPSIDED` only speaks when a half is essentially
dead (<5% occupancy), and a per-slide balance metric would punish exactly the asymmetric editorial
compositions the taste protocol exists to produce, which is why the continuous quantity is used
ONLY as a deck-level share. Slides carrying `design_intent(weight=…)` are excluded from both sides
of the ratio — they were decided, not defaulted. Deliberately **not** in `SAMENESS_CODES` yet: that
composite is calibrated against this skill's own registers, and a new signal earns its way in after
it has been seen on real decks, not on the day it ships), **`TEMPLATE-BOUND`** (the composition-boldness
counterweight — fires ONLY when the deck's own `design_plan.boldness` is `bold`/`experimental` yet NOT
ONE interior page breaks its default frame: no full-bleed, no statement-with-void, no dominant hero,
every content page a variation of the same safe rectangle. It measures the *floor* of compositional
timidity — a deck can score 11 distinct skeletons and still park all its daring in the concept + chrome,
never in where the ink sits; whether a breakout is genuinely *innovative* stays the critic's
distinctiveness call. Advisory, and — like `WEIGHT MONOCULTURE` — deliberately kept OUT of the blocking
timidity composite until seen on real decks; sound restraint is never nudged (`boldness: conservative`
silences it)), and on CJK decks **`CJK TIGHT LEADING`** (multi-line
CJK at ≤ single spacing → use the script-aware default) and **`CJK-LATIN SPACING`** (both pangu spacing
conventions mixed → pick one deck-wide). Treat each `[stats]` warning as the NAMED design rule
having failed measurably: fix it or write one clause of why this deck is the exception, and **paste
the stats block into the critic's input** so the judges score numbers, not impressions. It's a safety
net for the no-overlap / fits-its-box / density / rhythm rules, **not** a
replacement for looking (it can't judge crop, balance, legibility, or fidelity).


## Efficiency and iteration (moved here from efficiency-and-iteration.md)

The rules themselves are stated in SKILL.md ("Work efficiently"); this file keeps the measured cost model, the full `deck_cycle.py` behaviour and the canon-probe notes. Moved verbatim from SKILL.md (2026-11-07).


### Round-trips and context

- **Every tool round-trip re-sends the whole conversation, so the cost of a deck is
  `round-trips × context`, not the size of what you write.** Measured on one 12-page build: 122
  calls, 37M tokens, of which **98.5% was context re-sent** and 0.6% was actual output; context ran
  ~302k per call by mid-build. Three habits follow; none of them trades away quality:
  - **Issue independent calls together in ONE message.** That same build averaged *1.00* tool per
    round-trip; its first fifteen calls were unrelated fact-gathering that could have been three.
    Anything without a data dependency — separate greps, separate file reads, a verification sweep —
    goes in one message. A dependency chain (build → render → lint → look) obviously cannot.


### Repairs and the canon probe

  - **Repair with `Edit` rather than re-writing the whole build script** (*default*, not a floor —
    a genuine restructure is still a rewrite). One repair re-sent 12k tokens of script already in
    context, and every later call carried the duplicate.
  - **The canon is cited here in prose and MEASURED in `scripts/canon_probe.py` — know which is
    which.** Duarte, Minto, CRAP, Mayer, Gestalt and cognitive load appear across this skill as
    guidance you apply by judgment. Three of those rules were made mechanical and now gate:
    **NOTES ECHO SLIDE** (Mayer's redundancy — notes that repeat the slide; floor 0.75, real decks
    top out at 0.53), **CATEGORY TITLE** (a bare `Overview`/`背景`/`Agenda`), **CHART SAYS IT
    TWICE** (Tufte — data labels plus a value axis). Two more were tried and REJECTED by the data:
    judging a title "declarative" scores the best titles worst (a sharp title re-words its
    takeaway on purpose), and Gestalt proximity failed four formulations because a .pptx records
    coordinates and no notion of which shapes belong together. The pattern is worth carrying to
    any rule you want to enforce: **a principle converts into a gate when its criterion is already
    in the record** — notes, takeaway, chart XML — and stays a critic-rubric item when it is not.


### deck_cycle.py in full

  - **Iterate with `deck_cycle.py`, so one fix costs one round-trip.**
    `python3 scripts/deck_cycle.py build_<deck>.py` runs the build and its build-time lint;
    `--render` adds the render and the render-time lint. Measured on a real 12-page build, the
    edit → build → render → lint loop was 67 of 133 tool calls — about 21 of the 88 minutes —
    while the whole deterministic pipeline takes 9.1 seconds. The steps are not slow; asking for
    them one at a time is. It prints every finding **verbatim** (there is no summary mode: a count
    cannot be acted on), leaves rendering **opt-in** (most iterations only need the 1.8s geometry
    pass, and forcing a 5.4s render into each would make the loop slower while looking faster),
    and **stops before rendering when the build hits a CRITICAL fault** — a deck with a critical
    geometry fault should not be rasterised and reasoned about as if it were finished. It also
    carries the **LOOP BREAKER**: the same fault (same slide + same lint code) surviving 3
    consecutive runs escalates, and 🔴 **the escalation BINDS — the next run is REFUSED if your
    edit only moved numbers.** "Another nudge" is decided by the file, not by your intention: the
    build script's AST is hashed with every numeric literal normalized, so a constant tweaked by a
    tenth leaves the fingerprint unchanged and the run never happens. Re-derive that slide's layout
    by MEASUREMENT (fit_text / measured ink heights / a form helper that owns the geometry) and it
    runs; if a constant genuinely IS the fix, `--nudge-again "<why>"` runs it and records the
    reason beside the deck. Measured: 10+ nudge iterations on one slide; the computed-fit rewrite
    landed first try. It replaces nothing: `render_deck.py` and `lint_deck.py` behave as before.
    After every build that completed it also **snapshots the deck** into `<deck-dir>/.versions/`
    (`scripts/deck_versions.py`; unchanged content makes no new version) — Step 6 shows the user the diff.


### render_deck --fast in full

**Iterating on a deck you already rendered? Add `--fast`.** `render_deck … --fast` fingerprints
every slide (its XML + rels + the bytes of the media it references, mixed with a deck-global digest
covering the theme/master/layouts/canvas size) against the previous run, then re-renders **only the
slides that changed** — it subsets the pptx to those slides, converts that, and overwrites just their
PNGs. Measured on an 18-slide deck: a full render is ~2.8s, a one-slide change **~2.3s**, and a run
where nothing changed **0.07s**. 🔴 **The no-op round is the big win, not the one-slide round** — a
no-op never starts LibreOffice, while any real render pays one ~2.5s start that dwarfs the page work,
so a one-slide round saves about a fifth. Never skip a re-render on the belief that rendering is
expensive; it is a couple of seconds. Output is byte-identical to a full render (verified), so the
critic and the render-time lint see exactly what they would have seen anyway. It falls back to a full
render — and says why — whenever the mapping could be wrong: slide count changed, every slide changed,
no cache, or the deck contains **auto slide-number fields** or **hidden slides** (LibreOffice drops
hidden slides from the PDF, so page N stops being slide N — a full render now warns loudly and
refuses to cache when the page count and slide count disagree). **Use it for the actor-critic fix rounds
and for post-delivery tweaks** ("change slide 7 to a chart"); use a plain full render for the first
render of a deck and whenever you pass `--deliverables`.

