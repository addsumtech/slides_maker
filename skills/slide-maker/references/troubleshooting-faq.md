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
| a Python traceback | your build script crashed | fix the code line it names (§3) |

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
| `OFF_CANVAS` ✗ | A shape/text sticks out past a canvas edge (message names which edge) | Move or shrink it — the canvas is `0..W × 0..H` of **your** deck (the skill's templates build `10 × 5.625` in by default; `13.333 × 7.5` only when the deck was authored at that size — check your `blank_deck(W, H)` call); full-bleed images use `picture(..., fit="cover")` at exactly canvas size |
| `OVERFLOW` ✗ | More text than its visible (filled/outlined) box can hold — it will clip or spill in the render | The message shows text-height vs box-height: shorten the text, shrink the font 1–2 pt, or grow the box; `fit_text_size()` computes the largest size that fits |
| `TEXT_OVERLAP` ✗ | Two text blocks intersect — one will sit on the other | Move one, or restructure (merge into one block / put the label inside the panel it annotates) |
| `STRETCHED THIN` • | A wide blank vertical channel runs through the slide's interior. Two calibration fixes since: the content test is now RELATIVE to the slide's own dynamic range (a fixed colour distance is a light-deck number — on a near-black canvas panels differ from the canvas by ~42 and read as blank, so the check found "voids" between glyph strokes and fired on 7 of 20 slides of a professional dark briefing, one of them filled edge-to-edge with a chart); and a channel with real ink on BOTH flanks is a GUTTER, not emptiness — a two-column comparison or a divider with a numeral left and a graphic right is composition | If it still fires, the void has content on one side only. Enrich, merge with a neighbour, or declare the quiet register with `design_intent(envelope=…)` |
| `PLATE NOT VISIBLE` • | An interior page's full-bleed background has been scrimmed into a flat field — its exposed area varies by <0.6 grey levels. It satisfies "a plate on every page" in code while reading as no plate at all, and no contrast check can see it (a whiter background only makes dark text score *better*). Cover / dividers / closer are exempt — their imagery is loud by design | Lift the scrim and recover text contrast with the frosted blocks instead (`generated-template.md`'s visibility floor). Measured on real renders: 1.58 as generated, 1.16 under a light wash, 0.21 scrimmed to near-white |
| `FONT NOT INSTALLED` • | A face the deck DECLARES (`FONT`/`MONO`/`EAFONT`/…) is not on this machine, so measurement falls back to a metric-incompatible substitute — and every wrap/fit/overflow check in the library is computed from that measurement, so all of them carry ~1 line of slack. The shipped defaults `Calibri`/`Consolas` are Office faces absent from macOS | `deckkit.use_platform_fonts()` near the top of the build (picks installed equivalents for this OS), or set the faces yourself. `deckkit.font_health()` lists what is missing |
| `ESCAPES_CARD` • | A child element pokes past the edge of the card/panel it visually belongs to | Shrink the child or its step spacing until it sits ≥0.1 in inside the card |
| `OFFCENTER` • | A single text line sits noticeably high or low inside its tall box — looks like a spacing bug | Cheapest: `anchor=MSO_ANCHOR.MIDDLE` on the textbox at the card's exact x/y/w/h; else shrink the box to the text or move its y; harmless on deliberately top-anchored chips |
| `SLIVER_GAP` • | Two blocks almost touch (a hair-thin gap) — reads as a rendering accident | Open the gap to ≥ ~0.13 in — derive the pitch from `rows()`/`vstack()`, never `block_h + ε` (touching edges are their own flaw — "one merged block"; deliberately-jointed zones are a named exception, not the default fix) |
| `FOOTER` • | Content dips into the reserved footer band at the bottom | Keep content above the band (the card/panel variant of the message gives the exact y-line; the text variant quotes the colliding block — move it up) |
| `OLDSTYLE_FIGURES` • | A big number is set in a face whose digits sit at different heights (Georgia, Hoefler Text, Constantia… — measured from the installed font, not a fixed list) — 6 and 8 ride high, 3/4/5/7/9 drop below the line, so the number looks like it bobs up and down | Keep the serif for WORDS and set any run containing digits in a lining-figure face — Helvetica Neue, Arial or Cambria. Only fires at 20pt and above; old-style figures in body prose are correct and are not flagged. See `references/font-guidance.md` |
| `HOLLOW FILL` (stats) | The page reads as full but most of its ink is a **drawn container** rather than content — an outlined frame with no fill and no text of its own, wrapped around very little. Occupancy is a bounding-box union, so a hollow frame counts its whole footprint: measured, one empty rect with four characters inside scored **49%**, which is "full" by every density check and therefore exempt from `UNDERFILLED` as well. | 🔴 **Ask whether the FORM is right before touching the spacing** — every other message in this file points at geometry, and on a real build many rounds went into re-spacing a page whose actual problem was that its diagram carried one sentence. The cheap repair is usually to demote the container (an annotation, a line in the list it sits beside), not to re-space it. It fires only when the container dominates AND the content is thin AND the page has no typographic hero; a hero with air is protected, as it is for `UNDERFILLED` |
| `CJK_FACE_UNREACHED` • | A CJK face (Songti / PingFang / YaHei / Noto Sans CJK …) is named as a run's **Latin** font on a run that contains CJK, so it reaches none of those glyphs — they render in `EAFONT`. The rule was *wrong* rather than missing: the author followed the documented call shape and got a silent no-op, which on one measured build gave 6 of 14 slides a title in a face nobody chose. | A run tuple's sixth element is the Latin face; the **seventh** is the East-Asian one: `(text, size, colour, bold, italic, latin_face, ea_face)`. Set the Latin face to the deck's Latin font (which is also what keeps digits on a lining face) and the CJK face in slot 7. Silent when there is no CJK in the run, when both slots name the same face, and when slot 6 is a Latin face |
| `OOXML_SHAPE` ✕ | The slide part violates its own schema — a duplicated element the schema allows once, or children out of order. **This is the only defect class where the file does not open at all**, and every other check here is structurally blind to it: they are geometric, pixel-based or semantic, and none asks whether the part is well-formed. Measured: two `Build(s)` on one slide left TWO `<p:timing>` elements — `save()` raised nothing, LibreOffice rendered it, `lint_layout` reported clean, and `preflight_check.py` (which counts occurrences of the string `p:timing`) read the *duplicate* as **more** compliant. The first human signal would have been PowerPoint offering to repair the file. | Do not route around it — the file really is broken. If the message names `<p:timing>`: you called `Build.apply()` twice on one slide, which `anim.apply()` now refuses outright. Use ONE `Build` per slide and put every beat in its steps; a second Build's steps were never in the first's sequence, so keeping either tree ships a click order nobody wrote. If it names order: you appended where you should have inserted — CT_Slide runs `cSld, clrMapOvr?, transition?, timing?, extLst?` (`slide_transition()`'s `addprevious` is the pattern to copy) |
| `TEXT_GRAZES_SHAPE` • | A label's ink runs INTO a filled shape it is not inside — a caption grazing a bar, a row name touching a chip, a legend key on a node. `TEXT_OVERLAP` measures text against **text**, so this is invisible to it, exactly as a motif was before `TEXT_OVER_MOTIF`; the difference is that nobody tags a bar. Measured on a delivered deck: a right-aligned row label ran 0.015in² into the negative bar beside it, both lints clean, found by eye. | 🔴 **Move the label column's EDGE, not the string.** The first repair on that deck shortened the text and the label still grazed, because a right-aligned column that clears the *axis* does not clear a bar that grows *past* it. Derive the edge from the data — `right = ZERO − max(abs(v) for negative v)·SCALE − pad`. A value printed INSIDE its own bar is not reported (containment, not overlap, is the test), and a deliberate ride can be declared with `deckkit.overlap_intent(shape, "<why>")` |
| `WEIGHT MONOCULTURE` `[stats]` | The deck puts its visual weight on the **same side page after page**. One lopsided page is composition — this skill asks for it — so nothing per-slide is built on the measurement; `LOPSIDED` only speaks when a half is essentially dead (<5% occupancy), which is a different, rarer thing. Measured on a real deck: ink pushed left and the right held as air, over and over, with no gate saying a word. | Vary which side carries the weight across the deck — that is a rhythm decision, made once over the whole thing, not a per-page fix. Where a lean is deliberate, declare it: `design_intent(weight='left'\|'right'\|'asymmetric')`; declared slides are excluded from both sides of the ratio, so declaring is not a way to silence the signal, it is a way to be counted as having decided |
| `TEXT_OVER_MOTIF` • | A title/caption's ink crosses a shape tagged as the deck's signature motif. `TEXT_OVERLAP` cannot see this — it measures text against TEXT, and a motif is geometry, so a subtitle laid straight across a decorative ring produced **zero** findings until this check existed (measured: the same defect was caught by eye, written down as a build rule, and recurred on the next page). | Three legitimate answers, in order of preference: move the text out of the device's region; move the device (a corner mark belongs in chrome space); or, when the overlap **is** the composition — a display word riding a rule, a caption on a plate — declare it: `deckkit.overlap_intent(shape, "<why>")`. A full-bleed motif is a ground rather than an object and is never reported |
| `MOTIF_BUDGET` • | More than 3 slides carry a **loud** motif appearance. The design plan budgets the loud device at ≤3 because a device stamped on every page reads as a template tell rather than a signature; nothing counted it until motifs were tagged. | Demote the extras to the quiet register signature — `register_mark(…, loud=False)` — which may legitimately repeat on **every** page and is deliberately excluded from this count. If more than three loud appearances are the design, say so at the design checkpoint and accept the advisory |
| `DUPLICATE_TEXT` • | Two separate shapes on ONE slide render the same string. Three measured causes: a build script patched repeatedly left an **orphaned copy of an earlier layout** drawing over the new one (the tell: your edits appear to do nothing — four consecutive coordinate changes moved nothing, because two layouts were running at once); a **component's own auto-label printed beside a hand-written one** (a single quantity then appears twice, often at two different roundings); a **name repeated in both a list and a diagram** below it. | Find which one it is before fixing: `grep` the build script for the string and count the call sites. Orphaned code → delete the older block outright (not "adjust" it). Double label → let the component own it (`show_pct`, `labels=`) or drop yours, never both. Repeated name → the list already said it; cut it from the diagram, or cut the diagram (a figure that repeats a line of the list beside it is usually spending a third of the page on a footnote). Short shared tokens (是 / N/A / an axis tick) are deliberately NOT flagged |
| `CHROME_SLOT_DRIFT` • | A per-slide **source line** sits at a different height than the rest of the deck's. Measured on a real deck: 11 source lines, 8 pinned to one slot and 3 placed wherever their page's last block happened to end — one of them rendering `as of <date>` **inside a diagram box**, where it reads as part of the diagram rather than as provenance. | Do not nudge the strays. The root cause is that the slot was a *constant each page applied by hand*, and a rule a page can decline to follow is not a contract — route every source line through ONE helper that ignores any x/y the caller passes: `def src(s, sources, as_of): dk.source_note(s, sources, as_of=as_of, x=L, y=SRC_Y, w=CW)`. Under three source lines no slot is established and nothing is reported |
| `CJK_NO_EA` ✗ | CJK text with no `<a:ea>` font — PowerPoint/LibreOffice would pick an uncontrolled fallback and 避头尾 never engages. It resolves **inheritance** first (the run's own slot → its paragraph's `defRPr` → the shape's `lstStyle`), so a supplied template that puts the face one level up is silent, as it should be. It stops at the shape: a face inherited from the **layout, master or theme** lives in another part and still reads as missing, so a corporate template can flag on text that renders fine — the fix below is correct either way and costs one line | **Two moves, in this order.** (1) Set `deckkit.EAFONT = "Hiragino Sans GB"` (macOS; Microsoft YaHei on Windows, Noto Sans CJK SC on Linux) at the top of the script — `references/multilingual.md` has the pairing table. This is what makes the NEXT build clean, and it is first because step 2 needs a face. (2) Fix the deck in hand, on the line above the lint and before `prs.save()`: `deckkit.retrofit_ea(prs)` — or 🔴 **`deckkit.retrofit_ea(prs, "Hiragino Sans GB")` if you have not done step 1, because with no face set anywhere it raises rather than silently fixing nothing.** It stamps the slot on every CJK run and returns the count, reaching groups, table cells, date/footer fields and chart text that the check itself cannot see; it skips runs that already resolve a face, so a template's own CJK typeface survives. **`EAFONT` alone never fixes a deck already built** (the runs exist), and on a redesign / surgical fix-pass — runs this skill did not author, which never pass through `set_font()` — it will not fix the next build either, so keep calling `retrofit_ea` there. If it reports CJK left on **layouts/masters**, that text composites onto every slide and no gate sees it: re-run with `layouts=True` |
| `CONNECTOR_IN_BOX` ✗ | An arrow/line endpoint sits in a block's interior and is drawn ABOVE the block, so the stroke crosses it (classic: hub-and-spoke connectors anchored at the hub's centre, cutting through its own label) | Dock both ends on block EDGES — `connect_boxes(a, b)` / `hub_spokes(hub, spokes)` from the block rects, or `edge_point(rect, toward)` for one end. Or add the connector BEFORE the node so the node paints over the seam. Never pass a block's centre as an endpoint on a line that's drawn on top |
| `[components] N cluster(s) look like a form the library already implements` (printed by `component_audit.py`) | The build script composed a common form — a bar row, a 100% band, a tile row, a marker row — from raw `box`/`text` while a component for it exists and was never called. The hand-roll re-inherits the geometry bugs the component fixes. | **Not an error, and not a blocker.** Either build the component, or record the one clause that makes the hand-roll deliberate (a bespoke composition IS the signature move). The tool suppresses a cluster whenever a component that could have drawn it was called, so a flag means the library genuinely went unused. |
| `INHERITED_EFFECT` (build-time WARN) | A shape still carries the theme `<p:style>` — it was created with raw python-pptx, not deckkit, so LibreOffice draws a soft drop shadow under it (the '2010 SmartArt' look deckkit strips everywhere else). | Create the shape through a deckkit helper, or pass it through `deckkit._flat(shape)` after creating it. |
| `RULE_THROUGH_TEXT` ✗ | A thin decorative rule (divider / hairline / accent bar) is drawn **through** a text block's ink instead of between blocks. Always caused by a hand-picked `y`: the rule was placed under text of a given length, then the text was edited and grew into it. | Derive the rule's position from the block it follows — capture the loop's end (`stack_end = y + pad`) and draw the rule there. Moving the coordinate by hand fixes today's wording and breaks again on the next edit. |
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
off-canvas-invisible title is the sanctioned trick for statement slides), `READING ORDER` (title
should be first in z-order — add it first in the build code), `NON-TEXT CONTRAST` (solid marks/lines
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
- **If the attribution is already there in prose** ("这是 README 举的例子"), it is a false alarm —
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
| `PINGFANG ON MACOS` warn | The macOS LibreOffice render loop substitutes PingFang SC with a handwriting-style face — the QC loop then judges pixels PowerPoint will never show | Switch `dk.EAFONT` to `"Hiragino Sans GB"` for the build/render loop (PingFang SC is final-deck-only) — the render-loop trap in `references/multilingual.md` |

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
