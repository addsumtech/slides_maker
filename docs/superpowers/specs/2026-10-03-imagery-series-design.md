# P1 — Imagery Series: design

Date: 2026-10-03 · Status: approved in conversation, awaiting written-spec review
Source: the skillry.dev gap analysis (memory `slide-maker-visual-language-gap.md`) — 33 of 33 image-led
"visual language" decks there carry an art-directed, series-consistent image on nearly every page;
slide-maker's rule `image-generation.md` ("generate for only the few slides that earn it, never every
slide") and its tooling (one shared `--style` string, per-slide REAL-photo references) cannot produce
that. P0 (on main, a3abdc6) added the placement vocabulary — picture shapes, rotation, stickers, glass —
P1 adds the imagery those forms hold.

## Decisions (made with the user)

| # | Question | Decision |
|---|---|---|
| 1 | When does per-page imagery apply? | Only when the user picks an **image-led direction**; every other deck keeps today's rule unchanged. |
| 2 | How are images generated while developing/testing? | **Codex subscription**; the user grants a permission rule so the agent can run the generator itself. No paid API. |
| 3 | Cut-outs | **Generate on a flat colour background, key it out with Pillow.** No new dependency; refuse (raise) when the key is not clean. |
| 4 | People | **Generic people may be generated; a fictional persona may carry a name only with a visible "fictional" label on its slide; team / customer / testimonial / any real person = real photo or no portrait — the gate blocks it.** |
| 5 | Approach | **A — reference-chained series**: art-direction line + per-slot plan → one approved key image → the rest generated with the key image staged as a STYLE reference → cut-outs → consistency QC → placement by slot. |

## 1. The switch and the rule exception

- A new pick axis, recorded where the other picks live: `interview.picks` gets
  `{"axis": "imagery", "value": "series" | "selective"}` in `.deck-gates.json`, and the Codex evidence
  scaffold gets the same field. Absent = `selective` (today's behaviour).
- At the direction gate, when an image tool is available, the offered directions include one marked
  **image-led** (its preview shows an imagery-led composition). Picking it records `imagery: series`.
  The direction-diversity rules are unchanged; the image-led option is one of the existing slots, not an
  extra one.
- `references/image-generation.md` keeps its default and gains ONE explicit exception section for
  `imagery: series`: imagery may sit on most pages because it is the deck's visual language, with three
  floors that do not relax —
  1. every image slot carries a **meaning line** (what this image says on this slide; language-fair
     written-reason floor). A slot with nothing to say does not exist; the gate refuses an image without
     one;
  2. evidence is never generated — charts, source figures, screenshots, logos stay real; a chart page may
     carry no image;
  3. the REFERENT RULE stands: a real, specific subject gets a real photo (or a declared stylized
     register), never a photographic fake.
- Decks without `imagery: series` behave exactly as before (asserted by the existing suites).

## 2. The pipeline

New module **`scripts/image_series.py`** (CLI + importable), small extensions elsewhere.

### 2.1 The plan — `series.json`
Written by the agent at the design step (Step 2), validated by `image_series.py check series.json`:

```json
{
  "art_direction": "warm editorial craft photography, soft daylight, shallow depth, ochre/vermilion accents",
  "palette": ["F2E8D8", "D9A13B", "C2462E", "1A1A1A"],
  "render": "photo",                       // photo | illustration — goes INTO every prompt verbatim
  "slots": [
    {"id": "s01-hero", "slide": 1, "frame": {"shape": "arch", "w": 4.2, "h": 5.6},
     "subject": "a potter's hands shaping wet clay on a wheel",
     "kind": "scene",                      // scene | object | generic-person | persona | illustration
     "cutout": false, "calm_zone": "none", "focus": [0.5, 0.3],
     "alt": "a potter's hands shaping clay",
     "meaning": "making by hand is the deck's argument — the hands carry it before any word does",
     "referent": "generic-concrete"        // generic-concrete | stylized | real-specific (→ refused)
    }
  ]
}
```

`check` refuses (exit 1, message naming the slot and the fix): a missing/too-short meaning line; a
`real-specific` referent in a generated slot; `kind` in {team-member, customer, testimonial,
real-person} (people decision #4: not generatable); a `persona` without `persona_label`; a frame shape
not in `picture()`'s `PIC_SHAPES`/`rect`; a palette entry that is not hex; duplicate slot ids.

### 2.2 Prompts — `image_series.py prompts series.json out_dir`
Writes an `image_prompt_manifest.json` that `generate_images_codex.py` already consumes (one item per
slot, `slide-NN-<id>.png` stems, aspect from the frame). Each prompt contains, verbatim: the art
direction, the palette, the RENDER clause (memory: a render-mode clause outside the prompt was ignored
and produced photoreal output), "no text, letters, numbers or logos", the subject centred with margin for
the frame's crop, and — for `cutout: true` — "isolated on a perfectly flat, uniform #00B140 background,
no shadow on the background, subject fully inside the frame with margin on every side".

### 2.3 Key image, then the series — `generate_images_codex.py`
- `--only <slot-id>` generates just the key slot first; the agent LOOKS at it (and shows the user when the
  checkpoint is interactive) before continuing.
- New `--style-ref PATH`: staged beside EVERY generation (as `--ref-dir` already stages per-slide
  references), with a prompt instruction to match the reference's palette, light, grain/brushwork and
  rendering — and NOT its subject or composition. It is a STYLE reference, distinct from `--ref-dir`
  (subject references) and both may be used together.

### 2.4 Cut-outs — `image_fx.chroma_cutout(src, out=None, *, tol=…)`
Estimates the background colour from the border ring; refuses (ValueError naming the reason and
"regenerate on a flatter background") when the border is not uniform enough, when the subject touches the
frame edge, or when the result keeps < a minimum subject share; otherwise keys it out with a soft edge and
removes colour spill. The output feeds P0's `sticker_outline` when the design wants a die-cut border.

### 2.5 Consistency QC — `image_series.py qc series.json --dir <generated>`
Per image: mean Lab colour, luminance, saturation and a coarse palette histogram compared with the key
image; flags outliers beyond a threshold calibrated on real series (not on synthetic pairs — memory
`composition-competition`: synthetic calibration flatters a measure); also flags a missing file, a flat
image (P0's shared `_flat_bucket`), an aspect far from the slot's frame, and an unusable cut-out. Writes
`series-qc.json` and a contact sheet (reusing `image_qc.py`).

### 2.6 Placement — `image_series.slot_picture(slide, plan, slot_id, x, y, w, h)`
Places the slot's image with `picture(fit="cover", shape=frame.shape, focus=…, alt=…)` (or, for a
cut-out, `fit="contain"` of the keyed PNG), and TAGS the picture (`deckkit-gen:<slot-id>` through the
shared name composer, so it survives the save and composes with the other declarations).

## 3. Honesty and gates

Read from the FILE (tags) plus `series.json`, by a shared check imported by both delivery gates
(`render_deck --gate-check` and `codex_delivery_gate.py`) — parity by construction.

1. **SERIES PLAN** — when `imagery: series`: every `deckkit-gen:` picture maps to a slot in `series.json`
   with a meaning line; a generated picture with no slot, or a slot whose meaning line is missing, blocks.
2. **GENERATED PERSON NAMED** — on a slide carrying a generated `generic-person` or `persona` picture:
   a person-name + role/quote pattern, or team / testimonial / customer keywords (English and Chinese),
   with no fictional label on the slide → blocks. Conservative by design (better a miss than a false
   block); its patterns are tested on both directions.
3. **SERIES QC** — `series-qc.json` must exist and each outlier must be resolved (regenerated) or
   acknowledged with a written reason; otherwise a NOTE at hand-off.
4. Unchanged floors: text-free images, evidence never generated, contrast/occlusion/a11y checks.

## 4. Non-Claude support

- `references/codex-runtime.md` gets a step for the series pipeline (the same commands, printed NEXT
  lines between steps so an agent following only printed output reaches the end).
- Every new helper has a runnable `sigs.py --example` executed by `smoke_deckkit.py`.
- Verified by re-running the restricted-agent simulation (SKILL.md + Codex runbook + sigs output only) on
  the series pipeline.

## 5. Testing and verification

1. **Unit tests, no network** (a stub generator): plan validation (each refusal), prompt contents (render
   clause inside, no-text, chroma clause for cut-outs), `--style-ref` staging (`--dry-run`), chroma
   cut-out (clean passes; noisy background / edge-touching subject refused), QC outlier detection,
   placement mapping + tagging, and the three gates — every one in both directions.
2. **Real generation** (Codex subscription, the user's permission rule): topic 1 — a photo-register,
   image-led 6-page deck with a cut-out; topic 2 — a Chinese, illustration-register deck. Render, look at
   every page, read the QC report. The QC threshold is calibrated on these real series.
3. **Restricted-agent simulation** for the series pipeline.
4. Full suite + CI green before anything is pushed to main. No user files are used as test input
   (memory `no-user-decks-as-test-input`).

## Out of scope (P2 or later)

The curated register family (layout kits per visual language, CJK display-font strategy), multi-image
collage layouts, and photo-quality AI matting.
