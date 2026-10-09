# P5 — Two more native visual languages (interface · wayfinding): design

Date: 2026-10-09 · Status: look approved by the user (look-dev sheet, 10 pages), awaiting written-spec review
Builds on: P3 + P4 (`2026-10-05-native-visual-languages-design.md`, `2026-10-08-five-native-languages-design.md`):
`NATIVE`, `register(lang, page, alts=)` composers in `vl_native2.py`, `native_art.py`, `NATIVE_EXTRAS` /
`EXTRA_PAGES`, `TYPE`, `VARIANTS`, `ooxml_safety.py`, the direction gate's `native_fit`, bundled samples + fingerprints.
Look-dev: `~/Desktop/visual-language-lookdev.png` (sheet), built by a throwaway script (session scratchpad
`lookdev5/lookdev5.py`). This spec turns that look into the kit.

## Why

The user asked for two more languages, "新颖有设计感". Of four candidates the user picked the two that fill the
largest real gaps in the thirteen:

| Language | 中文 | Borrowed from | Purpose it fills |
|---|---|---|---|
| `interface` | 产品界面 | the product UI itself: windows, status chips, toggles, dialogs, dashboards | product launches, app / SaaS pitches, feature tours, internal-tool demos — the commonest deck there is, and none of the 13 speaks it (the 2026-10-09 Muse pitch had to invent a register for it) |
| `wayfinding` | 导视线路 | metro maps and station signage: coloured lines, roundels, station signs, departure boards | roadmaps, processes, onboarding steps, journeys, strategy routes, city / transport topics |

## Decisions (made with the user)

| # | Question | Decision |
|---|---|---|
| 1 | Which two | Interface + Wayfinding (recommended). Not chosen: Isometric, Specimen. |
| 2 | The look | As in the approved look-dev sheet, with the corrections in §6. |
| 3 | Process | Spec → plan → implement → verify → push only when the user says so. |

## Naming

`interface` and `wayfinding` collide with no registered name (18 presets, `register_surface` grounds incl. the
bespoke kits, the 13 languages), checked 2026-10-09. The bespoke kit `transit-signage` (`bespoke_kits.py`) is a
different name and stays; `references/bespoke-registers.md` gains a pointer from it to the native `wayfinding`.
P4's same-name guard in `register()` already protects both names.

## Verified facts this design rests on (2026-10-09, this Mac, LibreOffice render of the look-dev)

- **Pill widths must be measured.** Estimated by character count, short chips ("Live", "On", "New") wrapped to
  two lines. `dk._natural_width_in` (real font metrics) fixed every one; `native_art.chip` already measures.
- **Round-capped connectors render.** A straight connector with `a:ln cap="rnd"` at 11–14pt draws a clean
  transit line in LibreOffice, including 45° segments meeting horizontal ones.
- **An interchange is a rounded rectangle with a thick ink outline.** It read as an interchange at 0.7–1.0 in wide.
- **Dark mode needs its own panel/line tones**, not an inverted palette: window 171A21 on 0E1014, hairline 2A2F3A.
- **A display title in a window wraps early** ("…asking / for"); the cover must use `display()`'s widow control.

## 1. Architecture

- Both names join `LANGS` / `VARIANTS` / `TYPE` / `NATIVE` / `NATIVE_EXTRAS` / `EXTRA_PAGES` /
  `NATIVE_IMAGE_PAGES` in `visual_languages.py`, exactly like P4. Public API unchanged: `use(name, prs, ground=…)`,
  `Kit.<page>()`, `k.new_slide()`, `rs.ground(s, k.name)`, `build_sample`, `direction`, `--gates`.
- Compositions are registered with `@register(lang, page, alts=N)`. `vl_native2.py` is 1,672 lines; the two
  languages go in a new **`vl_native3.py`**, imported where `vl_native2` is, through the same `register`.
- New motifs go into `native_art.py`, one function each, deterministic, clipped to the page, decorative shapes
  marked with `dk.decorative`:
  - interface: `ui_window` (rounded panel + top bar + optional crumb/status), `ui_toggle`, `ui_button`,
    `ui_cursor`, `ui_device` (browser / phone frame around a picture), `ui_bubble` (chat bubble with tail).
  - wayfinding: `route` (a polyline of horizontal / vertical / 45° segments, round caps), `station`,
    `interchange`, `roundel`, `sign_panel` (rounded panel with an inner white keyline), `board` (departure board).
- Untouched: the 13 existing languages, the 18 presets, the bespoke kits. A deck that picks neither imports
  nothing new.

## 2. The two languages

All text inks pass 4.5:1 on their ground and every panel/sign/board they sit on (3:1 for display sizes), tested
per ground. `both` fonts exist on macOS and Windows; `fonts="mac"` may use Mac-only faces. Digits are lining.

1. **interface 产品界面.** Every page is an app screen.
   - Palette (light): ground F3F4F7, window FFFFFF, ink 0F1115, mute 5B6170, line E2E5EB, soft F6F7FA;
     status colours with ONE meaning each, deck-wide: blue 2F6BFF (primary / selected), green 16A34A (on / done),
     amber F5B83D (pending / needs attention), red E5484D (error / blocked); text-safe twins for each.
   - Type: Arial (both), Helvetica Neue (mac); CJK sans.
   - Surface: the app canvas + rounded windows with a slim top bar (crumb left, status chip right), a soft drop
     edge (a flat offset panel, not a blurred shadow).
   - Signature: **the page is a screen** — points are a settings list, data is a dashboard card, the quote is a
     chat message, the closing is a dialog with the caller's action as its primary button.
   - Grounds: `light` = app light (F3F4F7) · `dark` = dark mode (0E1014, window 171A21).
2. **wayfinding 导视线路.** Metro map + station signage.
   - Palette (light): enamel ground F6F5F1, ink 16191E, mute 5A6070, sign navy 1B2A41, sign keyline FFFFFF; line
     colours red D7262E · blue 0071BC · green 00954C · yellow F2B705 · purple 8E4FA1; board 0B0D10 with amber
     LED FFB020.
   - Type: Arial (both), Helvetica Neue (mac); the board in Courier New bold (both) / Menlo (mac); CJK bold sans.
   - Surface: the enamel page; signs as rounded navy panels with a white inner keyline; routes as thick
     round-capped lines.
   - Signature: **the deck is a network** — the cover is lines converging on an interchange, ordered points are a
     strip map, sections are station signs, data is a departure board, the closing is the way-out sign.
   - Line colour is identity, not data: page n of a section uses the line colour of its section number
     (1 red, 2 blue, 3 green, 4 yellow, 5 purple, then repeating) unless the caller names a line.
   - Grounds: `light` = enamel (F6F5F1) · `night` = navy (1B2A41, signs 22344F with the yellow edge rule).

**Meaning rule (P3, the user's standing feedback).** A structure is drawn only from content:
- A route claims the points come in order, so the **strip map is drawn only when the caller says so**
  (`ordered=True`). Unordered points become a **directory sign**: each point a destination row with its numbered
  roundel — the way a station sign lists exits, which claims no sequence.
- Interface status colours are never guessed from words: a chip's colour comes from the caller's state, else
  the neutral accent.
- Nothing on a cover is chosen by the kit beyond the language's own furniture.

## 3. Pages

All seven pages for each: `cover`, `section`, `image_text`, `quote`, `data`, `closing`, `points`, landscape and
portrait, both grounds.

| page | interface | wayfinding |
|---|---|---|
| cover | a large window: crumb, status chip, title, subtitle, the caller's actions as buttons (pointer on the primary); optional settings panel beside it from `toggles=` | 2–3 lines converging on an interchange from the left; kicker + title as the destination; subtitle on a navy sign with the line roundel |
| section | a tab bar: the section number in a rounded badge, title, active-tab underline | a station-name sign band across the page: roundel with the number, kicker, title, arrow |
| image_text | the caller's picture in a device frame (browser for wide pictures, phone for tall — derived from the aspect ratio); kicker chip, title, body, caption beside it | the picture as a station poster in a sign frame; kicker, title, body, caption beside it |
| points | a settings window: numbered badges, head + line, optional status chips from `tags=` | `ordered=True`: a strip map (stations alternate above/below; interchanges from `interchange=`); otherwise a directory sign |
| quote | a chat message: bubble with tail, avatar initials derived from the attribution | the quote on an enamel sign, attribution under it |
| data | a dashboard card: number, label, note; with `total=` a progress bar (tally's share rules) | a departure board: the page's label + number as the first row; extra rows from `board=` |
| closing | a dialog: title, line, the caller's actions as primary/secondary buttons | the way-out sign (localised structural label) with title + line; the route ending at a terminus |

**Portrait.** Compositions are computed from the canvas and measured text; each page has alternatives tried
before refusal (`alts`). Strip map → a vertical route; directory sign and settings list unchanged; dashboard and
board stack.

**Text contract (P3, unchanged).** Measured flow, shrink toward floors, `VLTextOverflow` instead of truncation,
no widows, CJK breaks at clause marks via `display()`, balanced quote measure.

## 4. Words only the caller can give (`NATIVE_EXTRAS`)

Never invented. Absent → nothing drawn. An extra on a page that does not draw it is refused with the pages that do.

| Language | Extra | Pages | Meaning / fallback |
|---|---|---|---|
| interface | `crumb=` | any; remembered | the window's breadcrumb (e.g. "Launch › Overview"). Absent: an empty top bar. |
| interface | `status=` | any; remembered | the top-bar status chip text, optionally `(text, state)` with state in on / pending / error / primary. Absent: no chip. |
| interface | `actions=` | cover, closing | 1–2 button labels (primary, secondary). Absent: no buttons, no pointer. |
| interface | `toggles=` | cover | 1–4 `(label, on)` rows for a settings panel beside the window. Absent: the window takes the width. |
| interface | `tags=` | points | one chip per point, text or `(text, state)`; count must match. |
| interface | `total=` | data | progress bar, tally's rules (plain numbers, same kind, ≤ total). |
| wayfinding | `line=` | any; remembered | a 1–3 character line code for the cover/section roundels, optionally `(code, colour name)`. Absent: section roundels show the section number; the cover draws no roundel. |
| wayfinding | `ordered=` | points | `True` draws the strip map; default draws the directory sign. |
| wayfinding | `interchange=` | points | indexes of points drawn as interchanges (strip map only; refused without `ordered=True`). |
| wayfinding | `board=` | data | 1–4 extra `(label, value)` rows under the page's own row. |

**Derived, not invented:** page numbers; avatar initials (first letters of the attribution's first two words —
none for CJK names, where the bubble carries no avatar); browser vs phone frame (picture aspect); a section's line
colour (section number); the localised way-out label ("Way out / 出口 / 出口 / 나가는 곳"), confirmed with a
native-reading reference during implementation.

## 5. Offer guidance and grounds

- `NATIVE` gains both, so `native_fault` and `native_fit` cover them on both runtimes with no new rule.
- Guidance (an offer, not a rule) in `references/visual-languages.md`, `interview-protocol.md`, `codex-runtime.md`
  and the `directions_diversity` messages:
  - **product launch, app, SaaS, feature tour, internal tool → interface**
  - **roadmap, process, onboarding, journey, strategy route, transport/city → wayfinding**
- Both have a light default ground, so `ground="auto"` and print behave as for tally.

## 6. Changes from the look-dev

- **Sample furniture is not drawn.** "Workspace ready / 3 teams joined today", the toggle rows, "Live",
  "3 changes", "NEXT STOP", "PLATFORM", the board's LINE / ROUTE / ON TIME headers and "End of the line" were
  sample copy. In the kit they come from `crumb=` / `status=` / `toggles=` / `kicker` / `board=`, or are not drawn.
- **The strip map is no longer the default points page** (meaning rule above); unordered points get the
  directory sign, which the look-dev did not show and which will be shown rendered before sign-off.
- **The cover pointer** appears only when a primary action exists.
- **The interchange roundels "R / G"** on the strip map were sample codes; interchanges draw as interchange
  stations with no letters.

## 7. Generality and verification

As P4: the parametrised suites (`test_native_languages.py`, `test_native_generality.py`, `test_vl_audit_fixes.py`
where it applies) extend through `NATIVE`. Every page × language × orientation × ground with English, Chinese,
Japanese, Korean, short and long copy; refusals (overflow, bad extras, `tags=` count, `total=`, `interchange=`
without `ordered=`, `board=` row count); 16:9, 4:3, square, portrait; contrast of every ink on every surface;
`ooxml_safety` 0 findings; the generality corpus; the Linux font simulation; rendered sheets of every page viewed
by me, then shown to the user; `references/visual-languages.md` documents both with a call per page; `sigs.py
--example` gains runnable calls for the new `native_art` functions; samples `assets/vl/samples/interface[-dark].jpg`
and `wayfinding[-night].jpg` (≤ 350 KB, manifest + fingerprints, labelled "style sample — not your content");
README / README_CN galleries gain the two. Decks that use neither import nothing new.

## Out of scope

- Isometric and Specimen (not chosen).
- Generated imagery for either language. They accept a picture; they do not commission one.
- Changes to the 13 existing languages, beyond the guidance text that now points at the two new ones.
