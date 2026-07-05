# Semantic colour contract — bind a hue to a concept, deck-wide

The single biggest "this deck is credible" move in professional technical/consulting/data decks:
**a colour always means the same thing.** Not "use accent_one for emphasis" (rationing) and not
"palette(n) for n distinct hues" (categorical variety) — but a *contract* where each concept is
bound to one hue and that hue is propagated identically to every element that expresses the concept:
headings, icons, badges, table columns/cells, chart series, node fills, and inline keyword highlights.

## How to use it
1. **Declare the map once**, at the top of the build, e.g.:
   ```python
   SEM = {"structure": NAVY, "good": EMERALD, "risk": CORAL, "brand": GOLD, "neutral": SLATE}
   def sem(k): return SEM[k]
   ```
2. **Propagate it everywhere** the concept appears — the SAME `sem('risk')` colours the risk icon, the
   risk heading, the risk table cell, the risk chart series, and the risk keyword in a sentence
   (`highlight("…<k>critical gap</k>…", size, INK, sem('risk'))`). Never let "risk" be coral here and
   red there.
3. **Teach the legend early** (a small key on slide 2, or inline the first time each colour appears) so
   the audience learns the code, then reads colour as meaning for the rest of the deck.

## The standard contracts
- **Two-tier (technical):** `structure` (navy) vs `highlight` (accent blue) — encoder card navy header,
  decoder card blue header; the rest of the type stays ink so only the *role* is coloured.
- **Semantic data:** `good`/`cheap`/`winning` = green, `bad`/`expensive`/`losing` = red, everything
  else neutral — so a table or chart shows the *verdict* in colour and nothing else competes.
- **MBB 5-colour:** structure=navy · opportunity/good=emerald · brand/highlight=gold · risk/gap=coral ·
  neutral=slate. (The `consulting` preset ships this set.)

## Section / positional binding (a special case)
For a chaptered editorial or risograph deck, bind the active hue to the **section** instead of a
concept: an "active section accent" tints that chapter's numeral badge, kicker, page marker, divider,
and highlighted headline keyword — so flipping to a new section recolours the chrome with zero per-slide
choices. Implement as a `section_accent = ACCENTS[chapter_idx]` you thread into the chrome calls, and/or
auto-cycle a fixed ink set (blue→pink→ochre→black) per section. Same principle: colour carries
*which group*, consistently.

## Pitfalls
- Don't overload one hue with two meanings (gold = "brand" AND "warning" reads as confusion).
- Keep it to ≤5 bound concepts; beyond that colour stops being legible as meaning.
- Verify every bound colour clears ≥4.5:1 on its background (`contrast_ratio`), and never encode meaning
  by colour ALONE — pair it with a label/icon/shape (accessibility + projection).
- The contract is deck-wide: a one-off recolour that breaks it (a green "risk" cell) is a real flaw the
  critic should flag.
