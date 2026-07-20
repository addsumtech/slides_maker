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
| `KeyError` / auth error from an image script | API key env var not set in *this* shell | `OPENAI_API_KEY="$(cat ~/.openai_key)"` inline before the command (never echo or commit a key) |

## 3 · Build-time Python exceptions

The traps that actually bite, in the order people hit them:

| Traceback says | Cause | Fix |
|---|---|---|
| `AttributeError: ISOCELES_TRIANGLE` | The enum is spelled `MSO_SHAPE.ISOSCELES_TRIANGLE` (double S) | Fix the spelling; when unsure of any enum name: `python3 -c "from pptx.enum.shapes import MSO_SHAPE; print([n for n in dir(MSO_SHAPE) if 'TRI' in n])"` |
| `FileNotFoundError` on an asset (hero.png, icon, plate) | Build run from the wrong directory — relative paths resolve against the CWD | Run from the deck folder, or better: build paths from `ROOT = Path(__file__).parent` like the templates do |
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
| `ESCAPES_CARD` • | A child element pokes past the edge of the card/panel it visually belongs to | Shrink the child or its step spacing until it sits ≥0.1 in inside the card |
| `OFFCENTER` • | A single text line sits noticeably high or low inside its tall box — looks like a spacing bug | Cheapest: `anchor=MSO_ANCHOR.MIDDLE` on the textbox at the card's exact x/y/w/h; else shrink the box to the text or move its y; harmless on deliberately top-anchored chips |
| `SLIVER_GAP` • | Two blocks almost touch (a hair-thin gap) — reads as a rendering accident | Open the gap to ≥ ~0.13 in — derive the pitch from `rows()`/`vstack()`, never `block_h + ε` (touching edges are their own flaw — "one merged block"; deliberately-jointed zones are a named exception, not the default fix) |
| `FOOTER` • | Content dips into the reserved footer band at the bottom | Keep content above the band (the card/panel variant of the message gives the exact y-line; the text variant quotes the colliding block — move it up) |
| `OLDSTYLE_FIGURES` ✗ | A big number is set in a face whose digits sit at different heights (Georgia, Palatino, Baskerville, Constantia, Hoefler Text) — 6 and 8 ride high, 3/4/5/7/9 drop below the line, so the number looks like it bobs up and down | Keep the serif for WORDS and set any run containing digits in a lining-figure face — Helvetica Neue, Arial or Cambria. Only fires at 20pt and above; old-style figures in body prose are correct and are not flagged. See `references/font-guidance.md` |
| `CJK_NO_EA` ✗ | CJK text with no `<a:ea>` font — PowerPoint/LibreOffice would pick an uncontrolled fallback and 避头尾 never engages | Set `deckkit.EAFONT = "Hiragino Sans GB"` (macOS; Microsoft YaHei on Windows, Noto Sans CJK SC on Linux) before building — `references/multilingual.md` has the pairing table |
| `CONNECTOR_IN_BOX` ✗ | An arrow/line endpoint sits in a block's interior and is drawn ABOVE the block, so the stroke crosses it (classic: hub-and-spoke connectors anchored at the hub's centre, cutting through its own label) | Dock both ends on block EDGES — `connect_boxes(a, b)` / `hub_spokes(hub, spokes)` from the block rects, or `edge_point(rect, toward)` for one end. Or add the connector BEFORE the node so the node paints over the seam. Never pass a block's centre as an endpoint on a line that's drawn on top |

A build that ends `0 critical, N warning(s)` **saves fine** — warnings are judgment calls; the two
you most often accept deliberately are `OFFCENTER` on chip labels and `ESCAPES_CARD` on
intentional sticker/burst overhangs.

## 5 · Render stage failures

The shipped pipeline is one command: `bash scripts/render_deck.sh <deck.pptx>` — internally
LibreOffice (`soffice --headless --convert-to pdf`, with an **isolated per-run profile**) then
PyMuPDF rasterizes each page at a fixed 2× (~144 DPI) to `render/slide01.png … slideNN.png`
(plus `thumb_first/last.png`; a self-contained `viewer.html` preview is parked at the deck root beside
the `.pptx`, and the intermediate `<deck>.pdf` beside it too — both root files are expected deliverables)
(zero-padded, no hyphen) plus `thumb_first.png`/`thumb_last.png`; then
`python3 scripts/lint_deck.py <deck.pptx> --renders render/`.

| Symptom | Cause | Fix |
|---|---|---|
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
| `CJK TEXT without an EA font` | CJK characters in a run with no East-Asian font set → tofu risk off-machine | Set `dk.EAFONT` (see §2 tofu row); deckkit applies it automatically to CJK runs it creates |
| `META-ANNOTATION LEAK` | A visible run looks like an instruction to the builder ("placeholder", "TODO", "draft v2") rather than content | Delete/replace the text. **False positive?** If it's a genuine content word (a diagram edge labeled "draft"), rename to an unambiguous content phrase ("submits work") — cheaper than arguing with the lint |
| `EDITABILITY` | The slide is one big image with no native text — the user can't edit it | Rebuild the content as native shapes/text; images are backgrounds and figures, never the whole slide |
| `EMPTY/ORPHAN slide` | A slide with no content survived a refactor | Delete it or fill it |
| `UNEVEN CARD HEIGHTS` | A visual row of cards has mismatched heights — reads as sloppy | Give the row one shared height (the max), let inner text float |
| `TEXT ON IMAGE` | Render-pixel estimate: text sits on a photo/gradient with est. contrast < 1.5:1 — unreadable (the class solid-fill checks can't see; needs renders) | Add an opaque panel or scrim behind the text, or move it off the busy region (pixel sampling already accounts for an existing scrim) |

Render-time **advisory `[warn]`s** (never fail the exit code): `LOW CONTRAST` / `BODY CONTRAST`
(1.8–4.5:1 bands), `MISSING ALT-TEXT`, `MATH-FONT TOFU RISK`, `GROUPED-ONLY` content — plus the
**accessibility set**: `TEXT-ON-IMAGE CONTRAST` (the 1.5–3.0 band of the hard check above),
`NO SLIDE TITLE` / `DUPLICATE SLIDE TITLES` (screen readers navigate by unique titles; an
off-canvas-invisible title is the sanctioned trick for statement slides), `READING ORDER` (title
should be first in z-order — add it first in the build code), and `NON-TEXT CONTRAST` (icons/lines
< 3:1 vs backing, WCAG 1.4.11). Resolve or consciously accept per §7.

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
| Font renders as serif/wrong style for 中文 | EA font not set per-run; PowerPoint fell back | Set `dk.EAFONT` before building (§2) |
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
- **Rendering works but everything is slow.** First render of a session pays LibreOffice startup
  (~5–10 s); subsequent converts are fast, and the fixed 2× rasterization keeps the loop snappy.
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
