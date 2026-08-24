# Bespoke-register library — verified invented registers to ADAPT (open-ended, grow it)

The 18 presets (`scripts/presets.py`, routed by `design-by-topic.md`) are the FLOOR. A **bespoke
register invented from the subject's own world** — its objects, signage, instruments, documents —
routinely beats every preset, because its colour, marker and line carry *meaning* instead of taste
(direction-gate rule, `interview-protocol.md`; slide-design §1). This file is where the good ones are
**kept**, so the next deck on a related subject ADAPTS a verified register instead of reinventing one
from scratch — the analogue of `slides-to-video/remotion/LIBRARY.md`.

**🔴 THE LIBRARY IS OPEN-ENDED — grow it, don't satisfy it.** These are verified STARTING POINTS to
adapt, never a menu to pick from. A register copied and merely re-coloured is the "template every time"
failure the whole direction gate exists to prevent. **Derive from THIS subject first; reach here only to
see how a register was *made legible and generative*, then invent your own.** When a subject has a world
no entry captures, that is the normal case — invent, ship, and (if it worked) register it below.

## How to ADAPT an entry (not transplant it)

Each entry names: the **subject world** it came from · the **motif** (device + the one thing it MEANS) ·
how it was made **legible at first appearance** (the STRANGER TEST) · how it **generates** (background ·
markers · one page whose geometry IS the motif) · the **build note** (the deckkit primitives). To adapt:
keep the *method* (what made it legible + generative), swap the *material* for your subject. The
STRANGER TEST, ONE-form-ONE-meaning, and the generativity triple (slide-design §1) all still bind on what
you produce.

## Building one — the primitives, and which tier they serve

- The **quiet** signature (the chrome cue on every ordinary page) is `deckkit.register_mark(slide,
  kind, corner=…)`. Reach past the graphic-neutral kinds (`arcs` · `rule` · `ticks` · `ordinal` ·
  `grid`) for one drawn from the subject's own world — `seal` · `stitch` · `trace` · `contour` ·
  `caliper` · `hatch` — or hand-roll anything and `deckkit.tag_motif(shape, loud=False)` it.
- The **loud** tier — the ONE page whose geometry IS the motif, which `motif_generates.page` asks
  every deck for — is `deckkit.motif_page(slide, kind, legend=…)`, and its kinds are named after
  RELATIONS, not looks: `seam` (a crossing) · `conduit` (accumulation along a line) · `strata`
  (depth/hierarchy) · `radial` (dispersion) · `lattice` (coupling) · `orbit` (cycles) · `aperture`
  (focus) · `terrace` (staged advance). Pick the relation your CONTENT has, then swap the material
  for your subject's own conduit/layer/seam — the `current` entry below is exactly a `conduit`
  whose material is an electric bus, and reading it as "use the conduit kind" instead of "use a bus"
  is what adapting means here.
- The **key** that satisfies the STRANGER TEST is `deckkit.motif_legend(slide, "<the meaning>")`,
  drawn at the device's first appearance (`motif_page(..., legend=…)` does it for you). It is not
  tagged as the motif: a key must not spend the ≤3 loud budget, and `MOTIF_UNEXPLAINED` looks for it.

## Verified registers

### `current` — a live electric BUS (from: EV / energy / autonomy)
- **Motif:** a horizontal glowing "bus" line that crosses from one colour register to another at a node,
  with tap-off traces to markers. **Means:** the crossing from a present state to a future one (on the
  Tesla deck: cars/today → autonomy/the-bet); the taps are the sub-points feeding each side.
- **Legible at first appearance:** end-labels on the cover ("CARS · TODAY" red / "AUTONOMY · THE BET"
  cyan) + the node drawn as a real circuit junction; a stranger reads "a current crossing", not "two
  lines".
- **Generates:** background = a quiet 2px bus rule in the top margin on every page · markers = the tap
  nodes as the bullet/step system · page = the split slide whose geometry IS the bus (a red half, a cyan
  half, the seam as the hinge).
- **Build note:** `box()` for the gradient bus + `slide_background`; `tag_motif(seam, loud=True)` on the
  hero seam; `columns(weights=(1,2))` for the crossing split; contrast-check both register hues on the
  dark canvas. Fits **any subject that ACCUMULATES across a divide** (before→after, old-guard→challenger,
  supply→demand) — swap "electric bus" for the subject's own conduit (a pipeline, a supply line, a nerve).

### `transit-signage` — a transit-map register (from: routes / pathways / processes)
- **Motif:** transit-map grammar — line COLOUR = a route/category, a numbered ROUNDEL = a step, a buffer
  stop = a dead end. **Means:** the distinct paths through a system and where they terminate (measured
  origin: routes into a country's labour market — line colour = visa route, roundel = step, buffer stop =
  a route that closes).
- **Legible at first appearance:** the map legend on the opening spread names each line's route; the
  roundels are numbered; a stranger reads a transit map unaided.
- **Generates:** background = a faint route-line field · markers = numbered roundels for steps · page =
  the route-map slide whose geometry IS the network. It supplied that deck's **signature move for free**
  because the motif was load-bearing (each route is real content), not decorative.
- **Build note:** `connect_boxes`/`loop_between` for edge-docked lines, `palette(n)` for one hue per
  route, `big_numeral`/roundel for stops. Fits **any subject that is a set of distinct PATHS to an
  outcome** (onboarding funnels, migration/eligibility routes, decision trees) — swap "transit" for the
  subject's own network.

### `ledger` — a ruled account page (from: finance / accounting / accountability)
- **Motif:** a ruled ledger column with a balance rule that either closes or **breaks**. **Means:** an
  account that does or doesn't balance (measured lineage: the Dutch 17th-century double-entry example in
  slide-design §1 — "a ledger page whose balance rule breaks").
- **Legible at first appearance:** the column headers + the struck rule are labelled; a stranger reads
  "an account that doesn't add up".
- **Generates:** background = faint ruled columns · markers = row numerals in a lining tabular face ·
  page = the reconciliation slide whose geometry IS the ledger (debits vs credits, the broken rule).
- **Build note:** `rows()`/`columns()` for the rule grid, `table()` with a highlighted row, a struck
  `hrule` for the break. Fits **any subject about a balance that fails or holds** (budgets, trust
  accounts, carbon accounting).

### `k-space` — an acquired-vs-skipped sampling grid (from: imaging / signal / sampling)
- **Motif:** a grid of sampled vs skipped points (the MRI k-space lineage in slide-design §1:
  `frequency · sampling → grid · trajectory → the acquired-vs-skipped row`). **Means:** what was
  measured vs inferred.
- **Legible at first appearance:** filled vs hollow cells with a one-line legend ("● acquired ○ skipped");
  a stranger reads "some points measured, some not".
- **Generates:** background = a whisper grid · markers = filled/hollow cell glyphs · page = the sampling
  slide whose geometry IS the grid.
- **Build note:** `unit_grid()` (filled vs empty cells + a mandatory unit label), `palette` for one accent.
  Fits **any subject about partial measurement / coverage / a mask** (survey coverage, test coverage, a
  sampling scheme).

## Registering a NEW one (the write-back, at hand-off)

A bespoke register earns a library entry only after it **shipped and worked** — a verified register, not
a sketch. At Step 6 hand-off, when a deck's invented register passed its critic loop and the user kept it,
**offer to register it** (one line, like the taste look-history write-back, `references/user-taste.md`):
*"this <name> register worked — add it to the bespoke-register library for future decks?"* On an explicit
yes, append an entry here in the same five-field shape (subject world · motif+meaning · legible-at-first ·
generates-triple · build note), distilled from the shipped `build_<deck>.py`. **Skip the offer entirely
under a per-deck auto directive** — never an un-consented library write, the same rule as the taste
registry. A new register that fits no existing "family" is not a problem to solve — it is the point; add
it and move on (slides-to-video's "open a new family" philosophy: novel and daring beats a clean
taxonomy).
