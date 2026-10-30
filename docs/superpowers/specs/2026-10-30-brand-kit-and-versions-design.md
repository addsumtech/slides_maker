# Brand kit + deck versions — design (2026-10-30)

The user asked for these two features after a full audit of slide-maker 6.0.1 and said: build them as I
understand them, without more questions, but make sure (1) the changes land in the right files — the repo AND
the installed copy that actually runs — and (2) agents other than Claude (Codex first) can use them. Every
design choice below is the lead's call, not the user's.

## Shared constraints (both features)
- **CLI first.** Each feature is one script with subcommands. Every successful command prints a `NEXT:` line
  naming the exact next command; every failure names the cause and the fix. A non-Claude agent must be able to
  complete the workflow by running only what SKILL.md / references/codex-runtime.md say plus the printed NEXT
  lines (no reading of source code).
- **Local-first.** No network access in the scripts. No metered APIs.
- **Never invent.** A brand value comes from a file the user supplied or a value the user typed; every value
  records its `source`. Nothing is guessed from memory of what a brand "looks like".
- **Fail loud.** Unreadable input, missing fonts, ambiguous matches → a clear error or a NOT CHECKED line,
  never a silent pass.
- **Both runtimes.** A new gate section must exist in both `render_deck.py --gate-check` (`.deck-gates.json`)
  and `codex_delivery_gate.py` (`.codex-deck-evidence.json`); `check_gate_parity.py` must stay at 0 problems.
- **Docs that ship.** SKILL.md (short, where the step happens), the Codex runbook (references/codex-runtime.md),
  references/file-inventory.md and any other inventory/guard the CI checks (the CI has file-inventory guards —
  a new script without its inventory row turns CI red).
- Python ≥3.9 syntax; dependencies already in requirements.txt only (python-pptx, Pillow, numpy, PyMuPDF).

## Feature 1 — Brand kit (`scripts/brand_kit.py`)

**Intent.** A company / lab / product deck should come out on-brand without the user hand-building a .potx:
the user hands over what they have (logo, brand guide PDF, an old on-brand deck, or just hex codes and font
names), the skill turns it into one reviewed brand spec, uses it for the deck's palette and fonts, and checks
the built deck for off-brand colours and fonts before hand-off.

**Non-goals.** Fetching a brand from a website URL (the agent may download files with its own tools and pass
the local files; the script never fetches). Layout templates (that is the existing template branch).
Re-drawing or vectorising a logo. **Anti-goals:** a brand palette guessed from the company's name; a check that
flags every chart tint and photo so people learn to waive it.

**Subcommands.**
- `extract <files…> [--hex #RRGGBB …] [--font "Name" …] --out <brand.json>` — reads:
  - logo (SVG: fill/stroke colours; PNG/JPG: frequency-clustered colours ignoring transparent and near-white/near-black
    background; record the logo file and whether it reads on light and/or dark ground by contrast);
  - brand-guide PDF (hex/RGB codes in the text, font names embedded or named in the text);
  - .pptx/.potx (theme colours and theme fonts — reuse inspect_template / existing theme readers);
  - explicit `--hex` / `--font` (source `user`).
  Writes brand.json: `colors[]` {hex, role guess, source, count/weight}, `fonts` {heading, body, cjk} each with source,
  `logos[]` {file, ground: light|dark|both}, `status: draft`. Prints what it found, what it could not decide, and NEXT.
- `review <brand.json>` — prints the draft as a short table the agent shows the user (or, in auto mode, records as a
  delegated pick with source/basis per the auto-delegation rules), then `confirm`.
- `confirm <brand.json> --primary … --accent … [--neutral …] [--heading-font …] [--body-font …]` — sets roles, checks
  each font is installed (and, for a CJK deck, that the CJK face has the glyphs, else names an installed fallback and
  marks it), checks text/background contrast pairs, sets `status: confirmed`. A draft cannot be used by `style`/`check`.
- `save <brand.json> --name N` / `list` / `use N <deck-dir>` — reusable kits live beside the registered templates
  (registry.root_for_write / roots_for_read), so the second deck for the same brand needs no extraction.
- `style <brand.json>` — prints/writes the palette+font block the build script / style.py uses (in the same shape the
  presets and style.py already use), so the deck draws from brand values instead of a preset.
- `check <deck.pptx> --brand <brand.json>` — off-brand COLOURS used by text, fills, lines and native chart series
  (allowed: brand colours, their tints/shades — same hue family in Lab within a calibrated tolerance — and the declared
  neutrals; pictures are ignored), off-brand FONTS (not the brand fonts or the confirmed fallback), and the logo rule
  when the deck is single-entity. Output lists each finding with slide, shape and colour/font, verbatim.

**Gate.** `.deck-gates.json` section `brand` = {file: "<path to confirmed brand.json>"} or a waiver in the existing
waiver shape. When the section exists, `--gate-check` runs `check` and fails on findings; the Codex gate does the same.
No section → no brand gate (decks without a brand are unaffected).

**Calibration (required before merge).** Build at least two on-brand decks from fixtures (different brands, one CJK)
using `style`, plus deliberately off-brand variants. Report false positives on the on-brand decks (target 0) and
catches on the off-brand ones; set the tint tolerance from those numbers, not from a guess.

## Feature 2 — Deck versions (`scripts/deck_versions.py`)

**Intent.** When a critic round or a user request ("把第 7 页改成图表") rebuilds the deck, the user can see exactly
what changed slide by slide — above all any number that changed — and go back to an earlier version of the whole
deck or of one slide.

**Non-goals.** Git integration; collaboration/comments; diffing decks the skill did not build (v1 handles decks with
a build script beside them; for a deck without one, `snapshot`/`diff` still work but `restore --slides` refuses).

**Storage.** `<deck-dir>/.versions/vNNN/` holds the .pptx, the build script(s) (`build_*.py`, `style.py` and other
.py the build imports from the deck dir), the render PNGs if present (`render/slideNN.png`), and `manifest.json`
{version, created, note, pptx_sha256, slides[]: {index, title, text_lines[], numbers[], render_sha}}. Unchanged
pptx (same sha256 as the latest version) → no new version, print so. Keep the newest 30 by default; versions marked
`--keep` (e.g. ones the user was shown) are never pruned; `prune --keep-last N` exists.

**Subcommands.**
- `snapshot <deck-dir> [--note …] [--keep]` — also called automatically by `deck_cycle.py` after a clean build
  (no criticals), and recommended in Step 6 right before showing the user a version.
- `list <deck-dir>` — versions with time, note, slide count.
- `diff <deck-dir> [vA] [vB]` (default: the last two) — aligns slides by title similarity + order (so an inserted,
  deleted or moved slide reads as such, not as N changed slides); per slide reports text lines added/removed, every
  NUMBER added/removed/changed (flagged first — the never-invent rule makes these the ones the user must check), and
  a visual change measure from the render PNGs when both versions have them (else a shape-geometry signature).
  Writes `<deck-dir>/versions-diff_vA_vB.html` (before/after images side by side, changes highlighted, plain file://
  page, no network) and prints the text report.
- `restore <deck-dir> vNNN` — whole-deck restore: snapshot the current state first (so restore is undoable), copy
  back the pptx and build scripts.
- `restore <deck-dir> vNNN --slides 7[,9]` — per-slide restore through the SOURCE: replace the build function(s)
  that make those slides in the current build script with the old version's function source (AST, matched by the
  per-slide `build:` function convention the preflight already uses), then tell the agent to rebuild. If the
  function cannot be matched unambiguously, refuse and print what to do. Never splice slide XML between pptx files.

**Gate / hand-off.** No blocking gate. The hand-off checklist gets an optional `version:` line (vNNN + "N slides
changed since the version you last saw") when versions exist. Codex runbook documents the same commands.

## Verification the lead will run before merge
- Unit/CLI tests for every subcommand incl. edge cases (empty deck, no renders, CJK titles, a slide inserted in the
  middle, fonts missing, SVG without fills, PDF with no hex codes, waiver).
- The full local CI + Linux font simulation.
- A restricted non-Claude-style run: a fresh agent given only SKILL.md, references/codex-runtime.md and printed
  output builds a small branded deck from fixture brand files, changes it, diffs and restores one slide.
- `rsync` the skill to the installed copy (~/.agents/skills/slide-maker) and diff it clean.
