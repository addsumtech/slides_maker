# Non-Latin languages (Chinese / Japanese / Korean / …)

The pipeline is Unicode-clean — python-pptx, the LibreOffice renderer, and PowerPoint
all handle non-Latin text. The deck won't break. The things that make it look *good*
(not just render) are **font glyph coverage**, **PowerPoint portability**, and a few
**script-specific typography** habits.

## One language, consistently (the default)

**A deck is written in ONE language throughout** — every title, bullet, callout, label,
axis, footer, and the closing slide. This applies to every purpose, not just research. The most
common failure when building from source material in another language — an English-speaking PM
making a status deck from a Chinese vendor's docs, a product team localizing a pitch, an
English-speaking user + a Chinese codebase, or a Chinese paper presented to an English audience — is a
deck that drifts: English headings over Chinese bullets, one slide in the wrong language, a stray
translated-vs-untranslated mix. Pick the **target language** (step 0) and hold it across the whole deck.

- **Decide the target language explicitly.** Default to the language the *user* is
  writing in. **When the source material's language differs from the user's**, or it's
  otherwise ambiguous, **ask** which language the slides should be in — don't assume the
  source's language.
- **Translate the content into the target language** — don't paste source text verbatim
  in the other language just because that's how the source had it (faithfulness is to the
  *facts*, not the source's language).
- **Legitimate exceptions (not "mixing"):** established technical terms, proper nouns,
  brand/product names, acronyms, units, math symbols, and code/identifiers may stay in
  their original form — e.g. a Chinese deck can say "基于 Transformer 的重建" or "DeepSeek
  API"; that's normal, not a language violation.
- **Mixed / bilingual only on request.** Only produce a deck that mixes languages (e.g.
  EN + 中文 lines together, or a bilingual conference deck) if the user explicitly asks.
  Then do it *systematically* — the same pairing on every slide (e.g. English title with
  a 中文 subtitle throughout), not ad-hoc drift.

## The one required change: set a script-appropriate font

deckkit's default `FONT` (Calibri) has **no CJK glyphs**. It still *renders* here only
because LibreOffice silently substitutes a CJK font — but in the user's PowerPoint that
substitution is uncontrolled (wrong/inconsistent font, possibly tofu □□□ on a machine
without a good fallback). So for a CJK deck, set the East-Asian font explicitly:

```python
import deckkit
deckkit.FONT   = "Calibri"      # Latin letters + numbers
deckkit.EAFONT = "PingFang SC"  # CJK glyphs  (or "Heiti SC" / "Microsoft YaHei" / "Noto Sans CJK SC")
```

`EAFONT` makes every run carry **both** `<a:latin>` (for Latin/numbers) **and** `<a:ea>`
(for CJK) — so PowerPoint/Keynote render Chinese with *your* chosen font while English
and numbers stay on `FONT`. Mixed "中文 + English 28%" text then looks intentional and
travels correctly. (Without `EAFONT`, CJK falls back to an uncontrolled default.)

### Font choices
| Role | Portable (recommended) | macOS | Windows |
|---|---|---|---|
| CJK sans (default) | Noto Sans CJK SC / Source Han Sans | PingFang SC, Heiti SC | Microsoft YaHei |
| CJK serif (formal) | Noto Serif CJK SC / Source Han Serif | Songti SC | SimSun |
| CJK brush/handwritten | — | Kaiti SC | KaiTi |
| Japanese / Korean | Noto Sans JP / KR | Hiragino Sans / Apple SD Gothic | Yu Gothic / Malgun Gothic |

Pick the CJK font to match the *purpose* the same way as Latin (`design-by-purpose.md`):
sans (Heiti/PingFang) for modern/corporate/talks, serif (Songti) for formal/defense.

**Pair CJK fonts by role too — don't set the whole deck in one face** (see the "Type pairing"
section of `font-guidance.md`). Use a CJK **display** face for titles and a CJK **body** face for
text, plus a clean **Latin** face for the numbers/English inside CJK runs:
- `deckkit.EADISPLAY` = CJK title face (e.g. **PingFang SC**), `deckkit.EAFONT` = CJK body face
  (e.g. **Hiragino Sans GB** / **Noto Sans CJK SC**) — `title_bar`/`editorial_header` then set
  titles in EADISPLAY and body in EAFONT automatically.
- `deckkit.DISPLAY`/`deckkit.FONT` = the Latin faces for those same roles, so digits/units/English
  (e.g. "≈40%", "1/5–1/7") render in a crisp Latin face, not the CJK fallback.

A tasteful, portable Chinese pairing: **PingFang SC** (titles) + **Hiragino Sans GB** or **Noto
Sans CJK SC** (body) + **Helvetica Neue/Arial** (Latin). Keep it to **≤2 text families (display +
body)** — the Latin and mono faces are functional roles, not extra style fonts — and apply it on
every slide. *(Avoid setting everything to "Arial" — it has no CJK glyphs, so the whole deck rides
an uncontrolled single fallback, the flat one-font look to fix.)*

### Portability caveat (say this in step 6)
PowerPoint can embed fonts, but python-pptx can't, so the recipient's machine needs the
CJK font installed — or PowerPoint substitutes. Prefer a widely-installed font (PingFang
on macOS, Microsoft YaHei on Windows) or **Noto Sans/Serif CJK** for maximum portability,
and tell the user which font the deck expects.

## CJK typography habits (so it reads like a native deck, not translated)
- **No true italic.** CJK fonts fake italic by slanting — it looks wrong. Emphasize with
  **weight, colour, or size**, never italic, for CJK runs. (Latin runs can still italic.)
- **Full-width punctuation.** Use 。，、：；（）「」 — don't add Latin spaces around them,
  and don't end CJK sentences with a Latin period. **But for a lone, centred large mark** (a
  "?" in a box, a standalone "!"), use the **ASCII** form: a full-width `？！` sits
  left-of-centre within its advance and won't optically centre. Full-width is for *running*
  CJK text, not a centred single glyph.
- **Line-breaking (断句).** CJK wraps at any character (no spaces needed) — fine, but give text
  boxes a little more room and consider `line_spacing` ~1.1–1.2; dense CJK at tight
  leading is hard to read. Because it breaks anywhere, **check a wrapped title/term doesn't split
  at a meaningless point** (mid-term, or between a number and its unit) — widen the box or rebreak.
- **No 叠字 (overlapping glyphs).** If glyphs visibly collide/overlap, the box is too narrow or the
  tracking is off — widen the box or fix spacing; never squeeze CJK to fit.
- **Equal, consistent space width around an operator/symbol.** Around an inline `=` `≈` `→` `+` `：`,
  use the **same space character on both sides** — the classic CJK bug is a **full-width space (`　`,
  ~1 em) on one side and an ASCII space on the other**, so the symbol sits lopsided. Pick one (a
  full-width space reads well between CJK terms) and use it symmetrically; verify in the render.
- **No orphaned punctuation (避头尾 / kinsoku).** A line must not **start** with closing punctuation
  (`。， 、！？：；）》】" '`) and must not **end** with an opening one (`（《【" '`); and never leave a
  **lone punctuation mark on its own row** (a trailing `。`/`，` pushed to the next line is the ugly
  tell). PowerPoint/Keynote apply East-Asian line-break rules automatically *if the run carries an
  EA font* — so always set `EAFONT` (not Arial) — but a too-tight box can still strand a mark. Fix by
  **widening the box / lowering the size a touch / rebreaking the line** so punctuation stays attached
  to its character; for a hard case, hand-place the break. Same idea in Latin: don't let a lone ")" or
  "." wrap to its own line.
- **Density.** A CJK character carries more meaning per glyph, so for a **presented** deck terse
  points matter even more — resist filling the line just because it fits. *(A read-alone / reference
  CJK deck may run denser like any read-alone deck — then lean on `line_spacing` 1.1–1.2 and the
  kinsoku guidance above; see `design-principles.md` "Delivery mode".)*
- **Numbers / Latin terms** inside CJK text render in `FONT` (the latin font) — choose a
  Latin font that pairs cleanly with the CJK one (Calibri/Arial with most sans CJK).

## Equations & figures
- `eq_par` / `equation_png` use ASCII + Greek (`EQFONT`) — unaffected by language. Don't
  put CJK *inside* `equation_png` (matplotlib's math font may lack the glyphs); label CJK
  around the equation with normal `text()` instead.
- Reuse the source's figures whole as always; if a figure has burned-in text in another
  language, that's the source's, not yours.

## Right-to-left scripts (Arabic / Hebrew) — limited
deckkit lays out left-to-right and doesn't handle RTL reordering or right alignment of
flow. You can set an Arabic/Hebrew font, but bidi layout, RTL bullet/indent direction,
and mirrored chrome are **not** supported well — treat RTL as a known limitation, flag it
to the user, and keep such decks very simple (or build RTL-critical slides by hand).

## Verify
The critic already flags tofu/missing glyphs — so render and **look**: every glyph is a
real character (no □), the CJK font is the one you chose, and emphasis isn't faux-italic.
