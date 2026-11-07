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

🔴 **All four below are now BUILDABLE, not just describable.** `scripts/bespoke_kits.py`
registers each one through `register_surface.register()`, so `ground()` and `card()` work for them
exactly as they do for a preset — the returned content rect, the loud-mark invariant, canvas
scaling, ground-resolved ink, and each register's own declared prohibitions enforced by
`check_register_guard`. `import bespoke_kits` is all it takes; `--sample <out.pptx>` renders one
page per register. They remain STARTING POINTS: each was invented for a specific subject and the
"fits" clause names its family — adapt it to the subject in front of you rather than pasting it
because it renders. To invent a new one, `python3 scripts/register_surface.py --new "<name>"`
scaffolds a kit with every contract already wired, and `scripts/save_register.py` records the kit
file beside the register when the deck ships.

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
- For a deck that only needs the look, the native visual language `wayfinding` builds all seven pages
  (`references/visual-languages.md`).
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


## Register kits — surfaces, invented registers, the shipped direction

- 🔴 **`apply()` gives you the register's COLOURWAY; `register_surface.py` builds its SURFACE.** Measured by rendering it: one identical page through all 18 presets produced 18 pages differing only in ground, ink, accent, one font swap and a line weight — no memphis bands, no bauhaus primitive, no glass, no overprint, no scanlines, because `apply()` calls exactly `set_palette` / `set_geometry` / `set_ground` / the font setters and each preset's `surface` field is prose for an author to build by hand, which meant it was never built. `register_surface.ground(slide, "<register>", role=…, index=n)` paints that register's own furniture and **returns the content rect left over** (like `title_bar()` returns its content top — nothing loud is painted into it, and a kit that breaks that RAISES); `register_surface.card(slide, "<register>", x, y, w, h)` gives its card FORM, which is what stops the pages differing only in colour: a memphis banded card, a bauhaus hard square, a riso sticker with an offset plate, a glass panel, a terminal output block. The marks (`halftone` · `starburst` · `boomerang` · `zigzag` · `tri` · `scanlines` · `color_band`) are callable on their own, so a BESPOKE register can borrow one. 🔴 **All 18 registers have a kit** — `--list` prints each one beside the `surface` line it was built from, `--sample <out.pptx>` renders one page per register with identical content so the difference IS the register, and a name that is not a register RAISES rather than quietly handing back a plain page (as does painting a surface before `presets.apply()` has set the palette). Both `--gate-check` and the codex gate NOTE a deck that declared a kitted register and used none of it: a deliberate quiet treatment is a real choice, forgetting the kit exists is not.

- 🔴 **A kit scales, and a kit may not INVENT.** Kits compose in REFERENCE inches on a 10 x 5.63in canvas and scale to whatever canvas they are handed, so the same furniture keeps its proportion on the 13.33in variant, on portrait 9:16, and on the A0/A1 posters `formats.py` supports — inches do not travel, and a fixed 0.42in mark measured 4.2% of one canvas's width and 1.3% of another's before the scale layer existed (bauhaus also RAISED on portrait, because a `max()` floor on the leftover band pushed the rect back over the hero it was protecting). And **furniture may state the page's own facts and nothing else**: an early version printed an invented masthead brand, a fabricated revision letter and a made-up year badge on every page that used them — the never-invent rule broken by the CHROME rather than by the content. A test now holds the entire vocabulary a ground is allowed to say, and another holds its chrome to the 3:1 text-contrast floor on its own ground (`dk.MUTE` is tuned for a LIGHT canvas: used flat it measured 2.85:1 on blueprint's navy — resolve it with `mute_for(GROUND)`).

- 🔴 **An INVENTED register can be a kit too — it is not limited to components and a palette.** `register_surface.register(name, ground=…, card=…, forbids=…)` gives a bespoke look the same standing the 18 presets have: `ground()`/`card()` work, the loud-mark invariant holds, the furniture scales to any canvas, the ink resolves from the ground, and `check_register_guard` enforces the prohibitions the register DECLARES — what a register refuses to do is what separates it from a colourway. `python3 scripts/register_surface.py --new "<name>"` scaffolds one with every contract already wired (fill in `ground()` and `card()`, then run the file: it renders its own three-page preview). Before this, a bespoke register's look was hand-built in the deck's `style.py` and NONE of those contracts reached it, and `references/bespoke-registers.md`'s four worked examples were prose — zero lines of runnable code. Those four now ship as `scripts/bespoke_kits.py` (`current` · `transit-signage` · `ledger` · `k-space`): `import bespoke_kits` registers them, `--sample` renders them. They are STARTING POINTS for their family, not looks to paste. `save_register.py` records the kit file beside the register at hand-off, so the next deck on that subject starts from the built look instead of from a description.

- 🔴 **A deck's own kit lives BESIDE the deck, as `surface_*.py`, and every gate loads it from there.** Registration happens at import time and the gates run in a fresh process after the build, so before this a bespoke register's declared prohibitions were enforced in-process and NOWHERE ELSE — measured with a scaffolded kit forbidding gradients and a deck drawing one: caught in a test, and reported by the real gate as "a bespoke look has no FORBIDS to check". `register_surface.load_kits(<deck dir>)` is called by `check_register_guard` on both runtimes; a kit that fails to import produces a NOTE saying its register is unregistered, never a silent "nothing to check". Both `--gate-check` and the codex gate also say, at hand-off, whether an invented register HAS a kit — without one its look is hand-built and none of the contracts (content rect, loud-mark invariant, canvas scaling, ground-resolved ink, its own prohibitions) reach it. Put the file in the deck folder: `--new "<name>" --out <deck-dir>/surface_<name>.py`.

- 🔴 **The direction the user PICKED is checked against the deck that SHIPS.** The branch-(c) gate renders four directions and records the pick as a sentence; nothing compared that sentence to the built file. Measured on a delivered deck: the chosen direction declared a **Georgia** display face and a **centred** cover, and the deck shipped Helvetica Neue titles and a low-left cover — `style.py` set `display=` and every title passed `dk.FONT`, so the DISPLAY slot was never read. The author caught it; no gate could, while `check_register_pixels` (a declared colour must reach the pixels) and `check_style_applied` (a declared preset must be called) had covered the identical class for a long time. `check_direction_applied.py` compares ground, accent presence, display and body faces, and `centred` vs `low-left` — and names skeleton and motif as NOT CHECKED rather than guessing at a judgement. **A deviation is normal design and is recorded per axis** (`design_plan.direction_deviations`): a freshness gate moves a ground, a contrast floor moves an accent. An unrecorded one is the version the user cannot see. 🔴 **And a direction's `cover_motif`/`ambient_motif` must DRAW, not describe** — they are raw HTML and the preview renders them, so a sentence lands as literal text on all four sample tiles and the author picks a direction covered in the author's own notes; `directions_diversity.py` reports prose in a drawing slot, and the description belongs in `note`, which the preview already shows.

- 🔴 **An invented register is KEPT at hand-off, or it is gone when the folder is.** `python3 scripts/save_register.py <deck-dir>` appends it to `<registry root>/registers.md` beside `taste.md` — nothing is re-described, it reads the pick, palette, signature move and `motif_generates` already in `.deck-gates.json` and adds the colours that reached the pixels. Measured before it existed: the example library held 4 invented registers while one user's look history held 9 that had shipped and been lost, because the mechanism was "remember to edit the markdown". `--from-history` recovers what a look history already names; `--list` shows the collection. **Read it at Step 2 alongside the preset gallery** — not to reuse a look (freshness still forbids that) but because a register that already made an argument about X visible is the best start for the next X.
