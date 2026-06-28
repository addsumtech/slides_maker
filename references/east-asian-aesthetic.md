# East-Asian editorial aesthetics — ink, paper, seal, traditional colour

A distinct design family for Chinese (and Japanese/Korean) cultural, literary, heritage, brand, and
humanities decks — *not* the same as a Western "editorial" look. It reads as **calm, literary, and
rooted**: warm paper, ink-black type, a single vermilion seal, large brush/serif CJK display, and
vast breathing room. Reach for it on 中文 cultural / 文化 / 人文 / 传统 / 品牌 decks; pair with the
`ink_wash` or `eastern_traditional` preset (`scripts/presets.py`).

## The two presets
- **`ink_wash` (藏拙 register)** — warm paper `#F5F1E8` · ink `#1A1A1A` · ONE seal-red `#A52A2A` ·
  KaiTi/Songti display. Minimal, literary, monochrome-plus-one-red. For essays, philosophy, brand
  manifestos, a single strong idea per slide.
- **`eastern_traditional` (传统色 register)** — warm paper `#F7F2E8` · ink `#3A3530` · ochre-gold
  `#C99E62` + sage `#6F8F75` + vermilion `#A52A2A` · KaiTi. The **colours themselves carry meaning**
  (传统色 names, plant-dye swatches, material/heritage palettes). For colour/material/heritage decks.

## Signature elements (what makes it read as authentically East-Asian)
- **Warm paper, not white.** Background is a warm rice-paper cream (`bg`), never pure `#FFF`; ink is
  near-black, never pure `#000`. The contrast is *soft*, which is the point.
- **One vermilion seal — the signature accent.** A red chop/印章 is the single spot of saturated
  colour. Use **`deckkit.seal(s, x, y, size, "藏拙")`** — a filled vermilion square (阴文, light char)
  or `shape="circle"`, with the classic thin inner rule. ONE per slide, small (≈0.45–0.8 in), in a
  corner or beside the title. It's a signature, not a sticker — never a row of them.
- **CJK numeral section markers** — use `deckkit.cjk_numeral(n)` → 壹·贰·叁 (formal 大写) or
  一·二·三 (`style="simple"`) instead of Latin "01 / 02 / 03". Set them in the seal-red or ink, large,
  as wayfinding (TOC, dividers, enumerated columns). This single swap is what most makes a CJK deck
  stop looking like a translated Western template.
- **Brush / serif CJK display.** Set `deckkit.EADISPLAY = "KaiTi"` (楷体) or `"Songti SC"` (宋体) for
  titles — a calligraphic/serif face carries the register; PingFang/Heiti (sans) for body. (Flag the
  font dependency at hand-off — KaiTi ships on macOS; on Windows use 楷体/STKaiti, and a render machine
  without it falls back, though the `.pptx` still tags it. See `font-guidance.md` / `multilingual.md`.)
- **Generous emptiness (留白).** Negative space is a *positive* element here — a near-empty slide with
  one line of large type and a seal reads as confident and literary. Resist filling it (this is the one
  register where the "no large empty region" rule yields to deliberate 留白 — keep ONE focal element).
- **Hairline rules + dark label-chips.** Thin ink rules separate ideas; a solid ink (or seal-red)
  chip with light text carries the one emphasis (为赢 / 所以忍). No rounded "SaaS cards", no soft
  shadows — the surface is flat and papery.
- **Restrained ink-wash motif.** At most one soft shuimo element (a branch, a mountain ridge, a wash)
  as atmosphere — generate it text-free via the preset's `image_prompt`, placed with calm space for
  text (`picture(fit="contain")`), low-contrast so type stays legible. Never a busy background.
- **Vertical-text accents (optional).** A short vertical column of CJK characters (a title, a couplet)
  is an authentic touch for a divider — keep it short and aligned to a margin.

## Build recipe
```python
from presets import preset
import deckkit as dk
p = preset("ink_wash")
dk.EAFONT = p["ea"]; dk.EADISPLAY = p["ea_display"]; dk.DISPLAY = p["display"]
BG, INK, RED = p["bg"], p["ink"], p["accents"][0]
dk.box(s, 0, 0, 10, 5.625, fill=BG)                       # warm paper
dk.seal(s, 8.7, 0.45, 0.7, "藏拙", fill=RED)               # the one red seal
dk.text(s, 0.7, 0.55, 7, 0.7, [[("木秀于林，风必摧之", 30, INK, True, False, dk.EADISPLAY)]])
for i,(head,body) in enumerate(items):                    # 壹·贰·叁 markers
    dk.text(s, *col[i][:3], [[(dk.cjk_numeral(i+1), 26, RED, True, False, dk.EADISPLAY)]])
```

## Pitfalls (what makes a CJK deck look machine-translated)
- Latin "01/02" numerals, a sans-everywhere look, pure white bg + pure black text, a SaaS rounded-card
  grid, a generic blue accent, emoji — all read as a Western template with Chinese text poured in.
- **SVG line-icon card grids (Tabler/Lucide/etc.) are the same translated-Western-template tell** —
  banning emoji does not license a line-icon family. Use `deckkit.seal` + `cjk_numeral` for
  section/wayfinding marks, never a line-icon grid (see `icons.md` Scenario fit).
- **Tofu / wrong fallback:** always set `EAFONT`/`EADISPLAY` (a CJK face) or glyphs render as boxes;
  the lint flags CJK-without-EA-font. Emphasise with weight/colour, not italic (CJK has no true italic).
- Over-decorating: more than one seal, a busy ink-wash behind text, or filling the 留白 kills the calm.
- Keep it **one language** unless bilingual was requested (`multilingual.md`); technical terms/acronyms
  may stay Latin.
