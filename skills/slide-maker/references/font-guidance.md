# Font guidance — pick portable fonts, avoid tofu

A `.pptx` stores font *names*, not the fonts themselves (unless you embed them). If a
machine opening the deck lacks the named font, PowerPoint/Keynote silently substitutes
one — shifting metrics and spacing, and for non-Latin text producing **tofu** (□□□) when
the substitute lacks the glyphs. So choose fonts that are present *everywhere the deck
will be opened*, and flag the dependency at hand-off.

## Cross-platform-safe Latin fonts
Reliable on Windows + macOS (and close enough on Linux/LibreOffice via metric clones):
- **Sans:** Calibri, Arial, Verdana, Tahoma, Trebuchet MS. (Calibri ships with MS Office — and
  on macOS it ships *inside the app bundle*, invisible to the render loop and to the width
  measurement even when Office IS installed; see the app-bundle section below. Arial is the
  safest universal sans.)
- **Serif:** Georgia, Times New Roman, Cambria.
- **Mono (code):** Consolas, Courier New.
LibreOffice (what `render_deck.sh` uses) substitutes Calibri→Carlito, Cambria→Caladea,
etc. — metric-compatible, so the render is representative.

`deckkit` defaults: `FONT="Calibri"`, `MONO="Consolas"`, `EQFONT="Arial"`, `EQ_MATHFONT="STIX Two Math"` (editable native math). Override them
right after import to match a brand or to maximise portability (`deckkit.FONT="Arial"`).

## The ACADEMIC / LAB register — the expected default is a conference face, not a designer face
**A lab meeting, a group progress update, a conference talk, a job talk and a thesis defense all
share one type convention, and it is not the one a design-led deck reaches for: Times New Roman,
Calibri, or Arial.** That room reads papers, posters and templates set in those faces all day, so
they are invisible in the right way — the type gets out of the way of the physics. A characterful
humanist or geometric sans (Avenir Next, Futura, Poppins, Gill Sans, Montserrat) is a *good face*
that carries the wrong signal here: it reads as marketing, and on a page of equations it also
mismatches the math, because the formula and the sentence around it end up in two different worlds.
- **Serif register** (papers, defenses, anything equation-heavy): **Times New Roman** throughout —
  display, body AND `EQ_MATHFONT`. One face for prose and math is what makes a formula look like
  part of the argument instead of pasted in.
- **Sans register** (slide-native talks, engineering status updates): **Calibri** (the face most
  institutional .pptx templates are themed in — check the template's own `majorFont`/`minorFont`
  before choosing anything else) or **Arial** where Calibri cannot be verified (below).
- **Mono**: **Courier New**, not Consolas or Menlo — Consolas needs Office, Menlo is macOS-only.
- This is a DEFAULT, not a floor. A deck that is deliberately editorial, a branded institutional
  template with its own type, or a user who asks for something else all override it — say which in
  one clause where the design plan records decisions.

## 🔴 A font that lives inside an APP BUNDLE is a font this pipeline cannot verify
Portability is usually framed as "will the *recipient* have it". There is a second, quieter failure
that costs more, because it corrupts the build's own evidence.

**On macOS, Microsoft Office does not install Calibri, Cambria or Aptos system-wide — it carries
them inside its own app folder** (`/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts`).
PowerPoint renders them perfectly. **LibreOffice — the render loop — and the width-measurement path
cannot see them at all.** So a deck set in Calibri on such a machine is:
- **laid out against a substitute's metrics**, which silently voids every "measure, never hand-pick"
  guarantee (`measure_text`, `vstack`, `bottom_callout`, `fit_text_size` — all of them), and
- **"verified" against a render of a face nobody will see**, so the Step-5 render self-check passes
  on pixels that are not the deliverable.

Both linters stay green throughout, because neither knows which font actually got used.
**`preflight_check.py` item 10 now detects this specifically** and says so in those terms rather
than the generic "may be fine where the deck is presented". Three responses, in order:
1. **Pick a system-wide face** (Times New Roman, Arial, Georgia, Courier New are installed on stock
   macOS *and* Windows). This is the default answer and needs no permission.
2. **Make the bundled font visible to the renderer** — copy those files into `~/Library/Fonts`, then
   rebuild so the measurements and the render are of the real face. It changes the user's font
   environment, so **ask first**.
3. **Ship it unverified, knowingly** — legitimate when the deck must match an institutional theme,
   but then say in the hand-off that the layout was computed against a substitute.

**`Cambria Math` is not implied by having Office.** Measured on a machine with PowerPoint installed:
Cambria, Cambria Bold and Cambria Italic were in the bundle and **Cambria Math was not present at
all** — so `EQ_MATHFONT = "Cambria Math"` would have tofu'd every formula. Set the math font to a
face you have confirmed is installed; **Times New Roman is the safe academic answer**, since
`equation_native` writes real text runs (italic variables, true sub/superscripts) and Times carries
Σ Φ ∇ λ ⟨⟩ and the rest of the operators an MR/ML deck needs. `equation_png` remains the
font-independent escape for 2-D math.

## Type pairing — give different roles different fonts (don't ship one font everywhere)
**This applies to EVERY deck, in any language** — a Latin/English deck benefits from role-based
type pairing exactly as much as a CJK one; it is a general typography default, not a CJK special
case. A deck set in a **single** font reads flat and unconsidered; role-based pairing is the cheapest
lift in perceived quality. Map a small, deliberate set of faces to roles:
- **Display** — titles, section headers, big numbers: a face with presence.
- **Body** — bullets, captions, labels: a clean, legible workhorse.
- **Mono** — code, filenames, page-markers / chrome: `MONO`.

Keep it to **≤2 *text* families (display + body)** — a **mono** and a **CJK/EA** face are *functional*
roles, not extra style fonts, so they don't count against this (more genuine display/body styles looks
chaotic), pair for contrast (a characterful display over a
neutral body), and apply the mapping **consistently on every slide**. `deckkit` supports it directly:
set `DISPLAY` (title face) alongside `FONT` (body) — `title_bar`/`editorial_header` use `DISPLAY`
for the title automatically; body stays on `FONT`; code/chrome on `MONO`. Per-run control: the 6th
element of a `text()` run tuple is that run's Latin font. Match the pairing to **purpose**
(`design-by-purpose.md`) — a serif display reads editorial, a heavy sans reads bold/modern.

Safe, portable Latin pairings: **Georgia** (display) + **Arial/Calibri** (body); **Arial Black**
(display) + **Arial** (body); **Helvetica Neue / Verdana** for a crisp numeric face.

**🔴 NUMERALS need LINING (uniform-height, baseline-aligned) figures — pick the numeral face for its DIGITS, not just its letters.** Many otherwise-good *serif display* faces ship **old-style figures** by default — **Georgia, Constantia, Hoefler Text, Calluna, Candara** (Palatino and Baskerville are often named here but measure as LINING on macOS — the skill checks the installed font rather than trusting a list) — where the digits sit at *different heights* (0/1/2 are x-height; 6/8 rise; 3/4/5/7/9 drop). On a big hero number this reads as **"some digits smaller / higher / lower than others"** (e.g. Georgia's "2026" wobbles), and it **misaligns with adjacent CJK/Latin** on a shared line. PPTX/LibreOffice can't reliably force the OpenType lining-figures (`lnum`) feature, so the fix is the FONT: set **big numerals in a lining-figure face** — **Helvetica Neue, Arial, Verdana** (sans; these also sit cleanest next to a sans CJK like Hiragino/YaHei), or **Cambria, Times New Roman** (serif, if you want serif gravitas AND uniform digits). Keep letters in your chosen display face if you like, but route the *numerals* through a lining face (per-run: the 6th run-tuple element). And **check the alignment**: a numeral run beside CJK or Latin should share the baseline and read the same visual size — verify it in the render, both for `中文 + 15亿` and for pure-Latin lines.

**Latin *inside* another language is its own role.** Numbers, units, and English terms embedded in
CJK (or other) text should ride a clean Latin face while the script keeps its own font — so
"私域营收 ≈40%" reads intentional, not like a fallback. deckkit does this via `FONT` (Latin) +
`EAFONT` (CJK), and `DISPLAY`+`EADISPLAY` for headings. Full CJK pairing in `multilingual.md`.

## Equations: native math needs a math font; raster is font-independent
**`equation_native`** (the editable default) renders real text runs in a **math font** (`EQ_MATHFONT`
= STIX Two Math; `Cambria Math` for Office) — its glyphs (ℒ Σ ‖) **tofu if that font is absent** on the
opening machine (STIX ships on neither stock macOS nor Windows; Cambria Math needs MS Office **and is
frequently missing even where Office is installed** — verify it, don't assume it. For an academic deck
set `EQ_MATHFONT` to **Times New Roman**: system-wide on macOS and Windows, and it matches the body). **`equation_png`**
rasterises math with matplotlib's bundled fonts, so it carries **no font dependency** and renders
identically anywhere — so when the math font can't be guaranteed (or the formula is 2-D), **fall back to
`equation_png`**. Flag the math-font dependency at hand-off (see `design-principles.md`).

## Non-Latin (CJK / etc.)
Set `deckkit.EAFONT` to a script-appropriate font so every run is tagged with a CJK
typeface (not an uncontrolled fallback): Hiragino Sans GB (macOS, render-loop-safe) / Noto Sans CJK SC / Microsoft YaHei — beware PingFang SC: LibreOffice substitutes it with a handwriting face, blinding the render self-check
(Chinese), Hiragino / Noto Sans JP (Japanese), Apple SD Gothic / Noto Sans KR (Korean).
Noto fonts are the most portable (free, broad coverage). Full guidance + RTL limits in
`references/multilingual.md`.

## Brand fonts
If the user's brand uses a non-standard font (e.g. a foundry font), the recipient needs it
installed or the deck won't match. Options, in order: (1) use it but **flag** that viewers
need it installed; (2) **embed fonts** in the .pptx (PowerPoint: File → Options → Save →
"Embed fonts in the file" — note this is a manual step python-pptx can't do, and bloats
the file); (3) substitute a safe near-equivalent and tell the user. Default to a safe font
unless the brand font is essential.

## If you see tofu / wrong fonts in the render
1. The glyph is missing in the (substituted) font — for CJK, set `EAFONT`; for special
   symbols, prefer `equation_png` or a Unicode-complete font (Arial).
2. The font name isn't installed on the render machine — `bash scripts/check_env.sh`
   <!-- python3-sweep-exempt: native Windows ships the `python` launcher and frequently has no
        `python3` at all, so this is the one place in the skill where bare `python` is correct.
        Everywhere else it is a bug — /usr/bin/python does not exist on macOS, so an agent
        copying a documented `python scripts/…` line verbatim gets "command not found". -->
   (or `python scripts/check_env.py` on native Windows) lists what's available; switch
   `FONT`/`MONO`/`EQFONT` to a present font and rebuild.
3. Re-render and confirm. At hand-off, tell the user which fonts the deck depends on.
