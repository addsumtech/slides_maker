# Canvas formats — one deck skill, many surfaces (16:9 · 4:3 · 1:1 · 3:4 · 9:16 · A4 · A0/A1 poster)

`scripts/formats.py` is the registry (dimensions · safe zones · chrome policy · density ·
lint flags); this file is the **design intelligence per surface**. The rule that governs
everything: **a format is a different design surface, not a resized slide.** Transplanting a
16:9 layout onto a portrait canvas produces the two classic failures at once — type that reads
tiny on a phone, and dead horizontal bands where a side-by-side split starved. Re-choose the
layout per surface; keep the *identity* (palette, type pairing, motif, semantic colours).

## Two invariants (before anything else)

1. **16:9 is the unchanged default — this module must do it no harm.** `formats.py` is
   OPT-IN: a build that never imports it behaves exactly as before, and `get("wide")` is
   byte-identical to today's default (10×5.625, no safe zones, full chrome, no extra lint
   flags). Every SKILL.md rule is written against 16:9 and stays authoritative there. The
   format question never fires for an ordinary talk/meeting deck.
2. **The existing craft + component library CARRY OVER to every format — only the layout
   adapts.** All deckkit components (cards, icon tiles, charts, timelines, callouts, frost
   panels…) read the real canvas size and work on any surface; all design rules (contrast
   floors, hierarchy, C.R.A.P., semantic colour, fidelity, the critic loop) apply unchanged.
   What a format changes is ONLY: canvas inches, the safe content rect (`band`), chrome
   policy, density budget, per-slide FORM choice (stack vs split), and display scale. A
   format is never a different design system — same identity, recomposed.

## How sizing works (read this before building)

- **Inch-normalization:** every format's canvas inches are chosen so the SAME pt tokens land
  right per surface (14pt body ≈ 1.9% of a 10in-wide talk slide, ≈ 3.5% of a 5.625in story —
  automatically phone-legible). So build scripts keep ONE type scale across formats; do NOT
  multiply body/label sizes per format. 🔴 **The exception is a surface PRINTED AT ACTUAL SIZE.**
  Inch-normalization works because a projected canvas is scaled to fill whatever screen it meets,
  so only *relative* size matters. A poster is not scaled: it is printed at 33in and read at a
  fixed distance, where the printed point size is the whole story. Those formats therefore declare
  ABSOLUTE floors in `type_floors`, and `check_surface.py` enforces them — applying the relative
  rule instead would demand a ~45pt body on A0 (absurd) while letting a 46pt title ship on a board
  nobody can read across a hall. Both errors, in opposite directions, from one missing distinction.
  Only display/cover type takes the format's
  `display_scale` multiplier.
- **Safe zones are load-bearing, not padding:** `formats.band(FMT)` returns the content rect
  after margins + platform-UI zones. On `story`, ~1.3in top (profile/camera chrome) and
  ~1.8in bottom (swipe/CTA/caption overlays) are COVERED BY THE PLATFORM at view time — text
  or key content there is simply lost. A full-bleed hero image may ignore the band; text never.
- **Chrome policy:** `full` (deck title_bar + footer) · `social` (no footer, no page numbers —
  a social card with deck chrome reads as a repurposed slide; use a small corner wordmark/@handle
  at most) · `print` (document header/footer + page numbers are correct).
- **Lint:** pass each format's `lint_flags` to `lint_deck.py` (social/print are `--selfread`);
  `dk.lint_layout(prs, strict=True)` runs unchanged on every format (it reads real canvas size).

## The three verified layout patterns (how "nice at every size" is actually achieved)

These came out of a 6-format visual-verification pass (2 judge rounds per format) — the failures
they fix appeared on EVERY taller-than-16:9 canvas, so treat them as required mechanics, not tips:

1. **Band-driven vertical distribution — never fixed row gaps.** Compute each stack's pitch from
   the band (`pitch = region_h / n_rows`), center each row inside its pitch cell, and let photos/
   figures take `avail_h` minus their caption line. Fixed 16:9-tuned gaps are exactly what leaves
   the "content ends at 55% height" dead band on 4:3/3:4/9:16/A4.
2. **Anchor the closing element at the band bottom.** A takeaway strip / last row is placed at
   `band_bottom − its_height` (the band already reserves footer + safe zones), with the rows above
   distributing into what remains — not appended after the rows wherever they happen to end.
3. **MIDDLE-anchor every self-contained cluster.** A stat cluster inside a panel, a bar's
   name/value labels over the bar's rect — place them with `anchor=MIDDLE` over the exact host
   rect so padding is equal by construction at ANY canvas size (hand-tuned y-offsets that look
   centered on 16:9 drift off-center the moment the host grows or shrinks).

**Component widths on narrow canvases:** deckkit components read the real slide size, and
fixed-width *defaults* are clamped to the canvas (e.g. `part_eyebrow`'s 6.0in default box
clamps on the 5.625in story canvas — found and fixed by this verification). If you hand a helper
an explicit width, derive it from the band (`bw`), never a 16:9-remembered number.

## Per-surface layout DNA

| fmt | surface | layout DNA | type & density | pitfalls to avoid |
|---|---|---|---|---|
| `wide` 16:9 | talks, meetings | the skill's default — everything in SKILL.md assumes it | presented budget | — |
| `classic` 4:3 | legacy projector, some defenses | same DNA as wide; the extra height takes **one more stacked row** (or a taller figure), splits stay 2-col | presented budget | shrinking type to "use" the height; letterboxing a 16:9 layout with dead bands |
| `square` 1:1 | IG/FB feed post | **centered, poster-like**: one hook line + one visual + 3–5 scannable points, vertically stacked; generous margins | ONE idea per card; display ×1.15 | 2-col splits (cramped at 7.5in); deck chrome; body prose |
| `red` 3:4 | 小红书 image note | **vertical flow**: bold hook top (≈upper third) → content middle → payoff/handle bottom; list-cards may carry 4–6 short rows; card 1 of a carousel = pure hook cover | ONE idea per card; display ×1.25; 封面 hook ≥ ~10% of canvas height | side-by-side columns; small dense text (rednote is browsed at phone size); ignoring top/bottom safe zones |
| `story` 9:16 | story/Reels/Shorts/抖音 cover | **one message, huge type**: hero visual + a 1–2 line statement; content lives in the middle ~65% (the band); stack everything | ONE message; display ×1.35; nothing that needs study | ANY text in the top 1.3in / bottom 1.8in (platform UI covers it); multi-point layouts; footers |
| `poster_a0` / `poster_a1` (+ `_land`) | conference poster, printed — **portrait AND landscape are both registered**; the venue usually specifies, so ask | **three reading distances at once**: one headline claim across the top, 4–6 sections in 2 columns beneath it, every body block short enough to read standing. The board is composed ONCE — plan the whole surface, not a sequence | **ABSOLUTE pt, not canvas-relative**: A0 display ≥90 · section ≥36 · body ≥24 (A1: 72/32/20). Fill 55–90% of the board. **Methods + limitations are required content** | typesetting it like a slide (deckkit's cover caps titles at 46pt — unreadable at 5m on a 33in board); leaving half the board empty because "whitespace is rhythm" (it is, across a *sequence*; here it is the only space the work gets); the billboard trap — a huge result with no method and no limitation, the two things a passer-by cannot reconstruct |
| `a4` print portrait | handout, one-pager | **document logic**: 2-col text+figure splits fine; sections flow down the page; margins 0.75in | self-read prose is the deliverable (density is correct, not a flaw) | presented-style sparse slides (wastes the page); social-style display type |

## Repurposing one deck across formats (the batch pattern)

One CONTENT plan → several surfaces is the intended use (e.g. a talk deck + a 小红书
carousel + a story teaser from the same research). What carries over **unchanged**: the
comprehension brief, claim ledger, semantic-colour contract, palette/type/motif identity,
photo/asset pool. What is **re-decided per format**: slide count + what makes the cut
(a 12-slide talk → a 6-card carousel → a 1-card story hook), each card's FORM (the
form-selection pass reruns against the new surface), density, and chrome. Never ship the
talk deck re-rendered at 3:4 — re-compose it.

Mechanics — parameterize the build script by format and loop:

```python
# build_<deck>.py  — one script, N surfaces
import formats, sys
FMT = formats.get(sys.argv[1] if len(sys.argv) > 1 else "wide")
prs = formats.blank_deck(FMT)
X, Y, W, H = formats.band(FMT)                    # safe content rect
...
prs.save(f"{deck}-{FMT.name}.pptx")
# batch:  for f in wide red story; do python3 build_<deck>.py $f; done
```

Layout code branches on `FMT.kind` / `FMT.columns_ok` (side-by-side on landscape, stacked on
portrait/square), reads `FMT.chrome` before drawing footers, and multiplies ONLY cover/display
type by `FMT.display_scale`.

## Gates (unchanged machinery, format-aware inputs)

- The **interview** confirms the format whenever the deliverable is not obviously a talk
  (social card, print piece, poster) — never silently assume 16:9 for a 小红书 ask, and never
  ask the question when "conference talk" already answers it.
- The **design plan** records a `format:` line whenever it's not `wide` (with the safe-zone +
  chrome consequences named); the checkpoint shows it.
- 🔴 **The registry is CHECKED, not merely offered.** It used to be producer-only — measured by
  grep, `import formats` appeared in `formats.py` and `extract_pdf.py` and nowhere else, so a
  build opted in voluntarily and nothing afterwards could tell whether it had. Every rule on this
  page was advisory by construction. `scripts/check_surface.py` now recovers the format from the
  BUILT canvas size and enforces the contract, wired into `render_deck.py --gate-check` (section
  `surface`) and `codex_delivery_gate.py`:
  `SAFE ZONE` (text inside a platform-UI zone) · `COLUMNS` (a side-by-side split of running COPY
  where `columns_ok=False` — a stat pair or a chip row is a legitimate portrait form and is not
  flagged) · `DECK CHROME` (a page marker, slide count or date on a social surface — identified by
  what it SAYS, so the `payoff/handle bottom` line this page prescribes passes and a real
  `deckkit.footer()` does not) · `TYPE FLOOR` and `FILL` (printed boards only) ·
  `MISSING SECTION` (content a surface is not finished without). `FILL` measures the board area
  COMMITTED to content blocks; where renders exist the check also REPORTS how much of it is
  actually inked, because a poster can be 82% committed and 17% inked — panels drawn and left
  mostly empty. That gap is reported, not thresholded. `PROPORTION` and `TEXT BLOCK` hold a printed
  board to the ~20-25% text / 40-50% graphics split the literature converges on and to ~50-word
  blocks — a panel drawn BEHIND text counts as a container, not a graphic, so a bigger box does not
  buy a pass. And a printed board must not go dark: `check_register_pixels.py` reports
  `DARK GROUND ON A PRINTED BOARD`, and its freshness rule changes its advice on a printed surface
  (vary the paper and the accent hue, never the value) — ink cost, drying, streaking, print-shop
  surcharges, and light hairlines thinning at print resolution all point one way.
  Put the code, its caption and the plain-text URL on with `deckkit.qr_panel()`: it holds the 10:1
  rule (a code read from 5ft wants ~6in) and always prints the URL beneath, for the many people who
  photograph a poster instead of scanning it.
  Run it alone with `python3 scripts/check_surface.py <deck.pptx>`; `--selftest` proves it on
  purpose-built fixtures. A canvas matching no registered format reports NOT CHECKED, never clean.
  Waive required sections in writing via `design_plan.surface_sections_waived`.
- **Verification is per-surface:** the render self-check + critic judge the deck AT its real
  aspect — a portrait card montaged next to 16:9 renders is easy to misjudge, so view it at
  its own proportions, and check the story/red safe zones explicitly (nothing text-bearing
  inside them).
