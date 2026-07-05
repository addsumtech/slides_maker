# Mimic a style example — understand it, then reproduce OR borrow-and-restyle

When the user gives an example to **mimic** (Q4), you reproduce what they value in your *own* build —
never building on it or taking its logos/content. **Two things to settle first:**

**A) How much of an example?** A whole **deck**, a **few slides**, or even a **single slide / screenshot**
are all valid. A deck shows the *system* (what repeats); a single slide shows one slide's *layout +
components + decorations* but NOT the deck-wide rhythm/archetypes — so for a single slide, **ask whether
that one slide's treatment should become the style for the whole deck** (usually yes), and infer the
recurring system from it (its title chrome, card style, palette, type → applied to every slide).

**B) Which INTENT?** Ask the user (they mean one of two quite different things):
- **(1) Reproduce the look** — make my deck read as the *same family*: same palette, fonts, motifs,
  density. A faithful style clone (with the user's content). → *Mode A* below.
- **(2) Borrow its components & layout, but redesign the style for MY topic** — keep the example's
  *structure and component vocabulary* (its card style, callout treatment, the way it lays out a
  comparison/diagram, its signature motif) but **re-choose the palette / mood / type to fit my topic**,
  and fill it with my content. "Inspired by, not copied." → *Mode B* below.
If unsure which, ask in one line — the build differs (Mode A keeps the example's colours; Mode B replaces
them). The user's phrasing — "mimic but not copy, redesign the style for the topic, apply some of its
components" — is **Mode B**.

## Look at it, then write a STYLE BRIEF (both modes)
**Render and view the example** (`render_deck.sh` for .pptx · pymupdf for .pdf · read the image for a
screenshot). Zoom to read fonts, measure spacing, sample exact hex. Capture concretely:
1. **Structure & rhythm** — recurring archetypes (title / divider / content / figure / two-column /
   results / closing); sectioning; density per slide. *(From a single slide: just that slide's structure.)*
2. **Grid & layout** — margins/safe area; alignment; where the title & footer sit; airy vs packed; column grid.
3. **Colour system** — background, text, 1–3 accents and **exactly where each is used**; light/dark; gradients.
4. **Typography** — heading vs body font; sizes/weights for title/section/body/caption; case; all-caps labels.
5. **Decorations & motifs (the character)** — header/footer bands; rules/dividers; shapes (rounded vs
   sharp, circles, chevrons, ribbons); icon/bullet style; shadows/borders; page-marker; the **signature
   touch** that makes it recognisable (a corner accent, a colour side-strip, a dotted leader).
6. **Component vocabulary** — how it styles each recurring piece: titles, callout/emphasis boxes, figure
   framing & captions, tables (ruled? shaded header? zebra?), equations, ▢→▢ pipelines/diagrams, "takeaway"
   bars, quotes, cards/tiles. **Name the 2–4 components worth reusing** (e.g. "a left-accent-bar card",
   "a numbered step row", "a duotone photo strip").
7. **Tone** — formal/academic · corporate · playful · editorial — and what makes it so.

## Mode A — reproduce the look (faithful clone of the style)
Build with `deckkit` but **override the defaults to the brief**: set the palette to the example's hex,
the fonts to its fonts, the title/footer treatment, corner style, bullet/rule/band motifs, and the
table/figure/equation styling. Re-create the *system + decorations*, applied to the **user's** content.

## Mode B — borrow the components & layout, restyle to the topic (the "inspired by" path)
Keep the example's **structure and component vocabulary** (brief items 1–2 and the named components from
item 6 + the signature motif from item 5), but **re-choose the visual style for the user's topic**:
- **Palette & mood:** design a *new* palette fit to the topic/purpose (via `design-by-purpose.md` or a
  `presets.py` preset) — do NOT carry the example's colours. (A finance example reused for a marine-biology
  talk keeps the *card + step-row layout*, but goes teal/sand, not the example's corporate navy.)
- **Type:** a topic-appropriate pairing, not necessarily the example's fonts (keep portability).
- **Components:** recreate the 2–4 borrowed components as `deckkit` constructs (the card with its accent
  bar, the callout, the diagram pattern) and **use them to present YOUR content** — same *shape*, your
  *substance* and *colours*. Don't reuse every component slavishly; take what serves your content and drop
  the rest (and add deckkit components the example didn't have where your content needs them).
- **Content:** entirely the user's (refilled from the topic/source), never the example's text.
The example governs **structure & component shapes**; the **topic governs palette, mood, and which
components apply.** This is mimicry of *design ideas*, not a colour-for-colour copy.

## Both modes — keep the craft, then verify
A style preference never overrides the craft rules (whole figures, gutters/margins, legible results,
≥4.5:1 contrast, one idea per slide). If a **template (Q1)** is also in play, the template's branding wins
where they conflict; the example governs the rest. **Verify by render:** for Mode A, put your slide next
to the example — they should read as the same family. For Mode B, your slide should clearly *echo the
example's components/layout* while looking like **your topic** (its own palette/mood), not a recolour of
the example.
