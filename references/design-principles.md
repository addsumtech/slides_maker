# Design principles — why these slides look the way they do

The recurring failure mode in research progress decks is treating a slide like a
page of notes: long run-on sentences, vague phrasing ("improving the system by
optimizing the approach"), and figures dropped in with no explanation. The audience can't
read a paragraph and listen at the same time, so the slide competes with the
speaker instead of supporting them.

Everything below follows from one idea: **a slide is a visual aid, not a
document.** Optimize for "understood in a few seconds."

## Tell a story — especially the opening
A deck should pull the audience along, not list facts. The motivation/opening is
where you win or lose them: build it **step by step** toward the problem, don't dump
it. A reliable shape — *what matters → what's hard about it → the gap nobody has
filled → (next slide) our idea.* Use a short visual progression (a few chips with
arrows, a numbered build) so the audience feels the logic, and end the setup on a
crisp **hook** — the open question your work answers. Name the concrete problems you
aim to solve; that's what makes a method feel necessary rather than arbitrary. Every
later slide should answer a question the previous one raised.

## One idea per slide
Decide the single takeaway before writing anything. Title states the point;
the body supports it. If a slide needs two takeaways, it's two slides.

## Few words per point
Points should be phrases, not sentences — often 2–5 words. Good:
- "Latency dropped 40%"
- "Cache = single source of truth"
- "Retry only on timeout"

Bad (what to fix):
- "We tried several configurations on the staging dataset, running the full pipeline
  with retries enabled (the queue is the bottleneck); 1. pick the first batch ..."

The speaker says the sentence; the slide shows the phrase.

## Diagrams over text
A relationship is clearer drawn than described. For structure you are creating from
scratch (a pipeline, a state machine, a module map with no source figure), prefer native
shapes (boxes + arrows via deckkit) over bullet lists. But see the next rule first.

## Use the source's own figures — whole
*(True for any deck, not just academic ones.)* If the source — a paper, report,
doc, an existing slide, or a chart/plot already produced from the code/data — has a
figure for something (an architecture, results, a dashboard, a graph), **use that
figure** rather than redrawing it. Redrawing by hand is slow and risks dropping or
mis-stating detail — getting it subtly *wrong* in front of the audience (an expert
panel *or* your boss) is far worse than showing the original correct figure. And show the figure **whole**: a partial crop hides context and invites
"what about the rest?". Annotate the whole figure with native callouts/arrows to
guide the eye; don't chop it. For a **dense** whole figure (e.g. a paper
architecture), enlarge it and overlay **big native labels the audience reads
instead of the paper's tiny ones** — numbered markers (✪ on the 3–4 parts you name
aloud) + a large legend strip, or endpoint labels over the columns that matter. Trim only the page header, the figure's caption, and
dead outer whitespace — never the figure's content. Crop to a sub-region *only*
when a figure is genuinely too dense to read at all, and say so.

## Every figure gets a legend + a takeaway
A bare image grid means nothing to the audience. State what the rows/columns are
(write your own caption — don't rely on tiny in-figure text), and add a one-line
TAKEAWAY of what to notice. Without the takeaway, the audience guesses.

## Tables and equations
- **A table exists to make one comparison obvious.** Decide what it should compare
  (it follows from the source's message), and make *that* the salient axis — don't
  introduce a second, distracting comparison. If the point is "X helps", foreground
  *baseline vs +X*; don't lay it out so the eye instead compares two unrelated rows.
  Use real **rules** (`deckkit.hrule`) — a header rule, a separator under the
  baseline — so it reads as a table, not floating numbers. Include uncertainty
  (± std / error bars) when the source reports it. Distil — never paste a giant
  paper table; show the rows that carry the message.
- **Formal math.** When equations should look polished, render them with
  `deckkit.equation_png` (matplotlib mathtext: true italics, ⊙, fractions, proper
  sub/superscripts) and place the image. Keep `eq_par` for quick, editable inline
  math. Either way the notation must match the source's.

## Layout: give every element room
The overall layout of a slide — margins, alignment, balance, whitespace — matters
as much as the words on it. Design is not optional polish; it is half the job.
- **Gutters.** Leave a consistent ~0.4 in (`deckkit.GUTTER`) between a figure and
  any adjacent text, callout, or slide edge. Text butted against a figure looks
  amateur.
- **Bottom margin.** Keep content clear of the footer — nothing should touch or
  cross the footer band (stop content by ~5.05 in on a 5.625-in slide). A line or
  box jammed against the bottom edge is the most common amateur tell.
- **Text must fit its box.** Never let text spill outside its callout/box. Size the
  box to the text (deckkit `callout` auto-grows), shorten the text, or both — then
  *check the render*, because overflow is invisible until you look.
- **Interior padding.** Text should never crowd a block's edge — keep a comfortable
  inset between a label/title/body and the boundary of its chip, callout, card, or
  box (the deckkit `chip`/`callout` helpers bake this in; for boxes you draw yourself,
  inset text ~0.15 in from the edges, more at the top of a titled card). Cramped text
  touching a rounded corner reads as unfinished even when nothing overflows.
- **Diagram shapes stay inside their container.** When you draw a native diagram into a
  card/panel (e.g. nodes in a box, icons around a hub, items flanking a centre), every
  shape must sit *inside* that frame with a margin — a block escaping the card edge (or an
  asymmetric, off-centre cluster) is the "out of lock" tell. Compute positions from the
  container's centre and keep them symmetric; after rendering, check no shape pokes outside
  its frame.
- **Match corner rounding between a card and anything overlaid on it.** A *rounded* card
  with a **square** colored header band (or a square accent bar) on top is a classic tell —
  the band's right-angle corners poke past the card's curve. Fix it one of two ways: give
  the band rounded *top* corners that match the card's radius (`deckkit.box(corners='top',
  r=<card radius>)`), or **inset** a thin accent strip/bar by the corner radius so its
  square ends land on the card's *straight* edge, not over the rounded corner (deckkit's
  `callout` insets its accent bar this way). Never lay a square block over a rounded one.
- **Connector labels: centred and tight.** A word over an arrow (a verb or transform name —
  e.g. "encode", "train", "merge") should be *centred on the arrow* and sit just above it
  with a small gap — not drifting to one side or floating far above. `deckkit.arrow_label`
  does this for you (places the label at the arrow's centre x, a hair above its top), so
  every connector label stays consistent.
- **Let the hero breathe.** When a figure *is* the point of the slide (results, an
  ablation, an architecture), give it the slide — enlarge it and reduce competing
  text to one caption + one takeaway, rather than shrinking it to make room for
  bullets. And prefer the figure's **own** legend/labels over re-creating them
  natively (re-created legends drift out of sync and add clutter).
- Align elements to a shared grid; don't let things float at random offsets.

## Colour: vary within the brand
Don't paint every block the same accent — a diagram where every box is the one blue
reads as monotone and unconsidered. Rotate through the theme's accents
(`deckkit.ACCENTS` = blue · teal · gold · steel · violet · green; the first few are
the template's own secondary accents, so they stay on-brand) so colour signals
*structure*, and reserve one colour (magenta) for emphasis/warnings. Pull the base
palette from the template; these are accents on top of it.

**Never let colour be the *only* signal.** If a chart's series, a status, or a
"before/after" is distinguished by hue alone, it collapses under a projector's washed-out
colours and disappears for colour-blind viewers. Back colour with a second cue — a direct
label, a shape/marker, a pattern, or a position — so the meaning survives without it.

## Accessibility
A few cheap habits make a deck usable by everyone, and most are things you should do
anyway:
- **Contrast ≥ 4.5:1** for normal text (≥ 3:1 for large/bold ≥ ~18pt). Check a colour
  against its fill with `deckkit.contrast_ratio()` *before* committing — light-grey
  captions on white and white text on a light accent are the usual failures. (`chip`/
  `modbox` now auto-pick a readable text colour; the `deckkit` palette defaults clear
  4.5:1 on their intended backgrounds.)
- **Don't encode meaning by colour alone** (see above) — pair hue with a label/shape.
- **Alt-text on every informative figure.** Call `deckkit.alt_text(shape, "…")` after
  `add_picture()` (and on diagrams) with a one-line factual description ("ROC curve:
  proposed method above baseline"). It doesn't render — it's screen-reader metadata in
  the .pptx — so it's invisible to the pixel critic; set it at build time as a habit.
  Decorative-only shapes can be left without alt-text.
- **Logical reading order & real text.** Keep titles in the title placeholder, use real
  text (not text baked into an image), and order content top-to-bottom / left-to-right so
  assistive tech follows the intended flow.
- **Legible type sizes** — body large enough to read from the back (see the size floor
  here and in the rubric); accessibility and back-of-room legibility are the same fix.

## Visual hierarchy
- High-contrast titles (white on a colored band, or dark on white) — readable at a
  glance, consistent across slides. Keep text-vs-background contrast high (≈4.5:1 or
  better); light-grey body on white or pale labels on a tint fail from the back row.
- Body 16–18 pt; don't shrink text to fit — cut text instead.
- **Mind the canvas scale when judging sizes.** The deck is built on a 10 × 5.625 in
  canvas (75% of the standard 13.33 in), so every point size is ~¾ of its
  standard-deck equivalent: 16 pt here ≈ 21 pt on a normal deck, and a 12.5 pt callout
  ≈ 17 pt, an 8–9 pt caption ≈ 11–12 pt. That means **callouts/captions/figure labels
  are the things that go illegible first** — keep callout body ≥12 pt and anything the
  audience actually needs to read ≥14 pt here. When in doubt, the render tells you:
  if you have to squint at the PNG, the back row can't read it.
- Accent colours for emphasis, used with intent (see Colour above); a thin colored
  rule or a small marker is enough.
- Name the closing slide for its purpose — an academic talk ends on **"Conclusion"**,
  not "Take home"; a status update might end on "Next steps".
- Generous whitespace. A slightly empty slide reads as confident; a packed one
  reads as a data dump.

## Callouts carry the message
A short labelled callout (THE GAP, PAYOFF, TAKEAWAY, NOTE) is where the
"so what" goes. Keep it to one line.

## Render and look — always
python-pptx places text blind: it never complains about overflow, a callout on the
footer, low contrast, or a missing glyph. The only way to know a slide is right is
to render it to an image and look. This caught every layout bug in practice; it is
not optional polish, it is part of building.
