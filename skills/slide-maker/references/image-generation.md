# Image Generation for Slide Visuals

Use generated images as optional visual plates, not as the source of truth. The deck's
claims, labels, tables, charts, equations, and important annotations still belong in
editable PowerPoint objects or faithful source figures.

> **Generating a whole TEMPLATE (not just a per-slide plate)?** That's a different job — a
> styled, **text-free** hero/divider illustration that becomes the deck's visual identity, with
> native content reproduced to match it. See **`references/generated-template.md`** (Q1's
> "generate a template with an image tool" branch). The text-free + fidelity rules below still
> apply; the palette is then extracted from the image with `deckkit.palette_from_image` so
> native blocks fit the generated look.

## Decide by taste and purpose — not by a rule or a quota
Whether a slide gets a generated image is a **design call**, the same way motion is. Reach
for a plate where your design sense says it will **emphasize** a point, make a slide **more
engaging**, or help **guide** the audience — and skip it where it wouldn't. There is **no
count to hit in either direction**: it's fine for two or several *consecutive* slides to
carry a plate when the design wants that, and fine for a long stretch (or a whole deck) to
have none. Don't think "most slides need zero" or "spread them out" — think about what
*this* slide and the deck's story need.

The failure to avoid is **thoughtless** use, not frequency:
- a plate dropped in for flourish, to fill space, or that competes with the slide's content;
- a generated image standing in where evidence belongs — a source figure, a real
  computed/extracted artifact, a chart, a screenshot, a logo. Those stay real and traceable.

When the user asks to use a GPT/image tool, this still applies: generate where your taste
says it helps, by design sense — and **propose plates for the user to opt into** rather than
generating on every slide by reflex. Decide image-by-image, the same way you decide
build-by-build.

**This per-slide content-image opt-in is available on EVERY deck, regardless of template choice** —
a registered template, a provided template, a clean design, or a generated template can all carry
generated *content* images. It is **separate from** Q1's "generate a template with an image tool"
path (that makes the text-free *visual identity*; this makes *content* plates for specific slides).
Offer it whenever an image tool is available, let the user decide, and — critically — **even when the
user opts in, generate for only the few slides that earn it, never every slide.**

## When to use image generation

**Two gates before you generate any image: (1) does it help the audience UNDERSTAND or feel this
specific slide's point** — clearer shown than told, the real thing they should picture, atmosphere
that frames a section — *not* decoration or space-filler; **and (2) does its design align with the
deck** — topic, content, and the **template/brand/style** (palette, the generated-template look, or
a mimicked style) so it reads as part of *this* deck, not pasted in. Feed the deck's palette + art
direction into the prompt. If either gate fails, use real/native assets or plain whitespace instead.

**The image must be *about this slide* — highly topical, not generic "fancy" filler.** A plate that
depicts the slide's actual subject (the concept, object, scene, or domain the slide is explaining)
earns its place; a pretty-but-generic abstract (random gradients, glowing orbs, "techy" swooshes that
could sit on *any* slide) is decoration that *makes no sense* against the content — cut it. **The test:
name, in one phrase, what the image shows about THIS slide's point.** If you can't — or if the same
image could drop onto an unrelated slide without anyone noticing — it's not topical; use a real asset,
a native diagram/chart, or plain whitespace instead. Put the slide's actual subject into the prompt.

Use the agent's native image generation skill when a slide would benefit from:

- a text-free hero image, atmospheric background, or side-panel photo/illustration;
- a conceptual scene where no source figure exists and exact factual detail is not the point;
- decorative texture, motif, object detail, or transition imagery that supports the deck's style;
- product/lifestyle/editorial imagery when the user is asking for a pitch or narrative deck and no real product asset is required.

Prefer real or deterministic assets instead when the visual carries evidence:

- source figures, tables, screenshots, charts, medical/scientific imagery, microscopy, maps, UI states, code, product shots, logos, or brand marks;
- any result whose content must be traceable to the user's material;
- any plot or diagram that needs readable labels, axes, numbers, or formulas.

## Place plates consistently — and a content plate is NOT a header
How a plate sits on the slide is part of the system, so keep it consistent and purposeful:
- **No one-off header band.** Don't drop a generated image as a decorative **header/banner strip on a
  single content slide** when the other content slides have none — it reads as arbitrary and breaks
  the deck's visual system (the eye asks "why does only this slide have a top image?"). A generated
  content plate **needn't be a header at all** — place it where it *serves the content*: a full-bleed
  background under native text, a **side panel** beside the points, or an **inline figure** in the
  content area. Title chrome is the `title_bar`/`editorial_header` job, not a generated image's.
- **One treatment family across the plated slides.** When several content slides carry a plate, give
  them the **same role and framing** (e.g. all right-side panels, or all full-bleed dividers) and one
  art-direction — not a header here, a corner image there. Section **dividers** are the natural place
  for a repeated full-bleed image; per-slide content plates are opt-in and should look deliberate, not
  sprinkled. (The cover/divider hero from the generated-template route is the *consistent* use; a lone
  header on one body slide is the inconsistency to avoid.)

## Real brand / product assets come first — never fill with a generic stand-in

Whenever a slide shows a real brand, product, company, logo, or UI — in **any** deck, not just a
product one: a research/conference talk citing a tool, framework, model, or dataset's source; a
teaching deck showing an app's interface; a status update naming a vendor; as well as the obvious
pitch / launch / stakeholder / competitor slide — the single biggest credibility lever is showing the
**real thing**, and a generated plate or a default-coloured box is the *wrong* answer, not a fallback.
Source the asset down a **recognizability hierarchy**, stopping at the first you can actually get:

1. the **real logo / product render / UI screenshot** (the user's, or a clearly-official asset they point you to);
2. the brand's **real colours + typography** applied to native deckkit blocks;
3. only then a tasteful neutral treatment — **never** a fake logo, an AI-imagined product, or a generic gradient silhouette standing in for the real mark.

**If the real asset is needed but missing, STOP and ask the user for it** — do not paper over the gap
with a generated look-alike or a placeholder that pretends to be the brand. A *correct placeholder*
("logo goes here") the user will swap is honest; an invented brand asset is a fidelity violation (it
misstates a real thing) and reads as fake instantly. This complements the rule above: generated
imagery is for *atmosphere/concept*, never for a real identity that should be shown as-is.

**When the deck is ABOUT a single company / institution / product, put that entity's logo on every
page — persistent brand chrome, not a one-off.** A pitch, a product/launch deck, a company or
stakeholder readout, an institution's report — anything whose subject *is* one organisation/product —
reads as more credible and finished when the mark is always present, the way real corporate decks
keep a logo in a fixed corner throughout. Place it small and in a **consistent position on every
slide** so it reads as chrome and never jumps; **top-right is the usual default**, but it's your call —
move it to a corner the title/figures/motifs leave free, just keep it the same everywhere. Use
`deckkit.logo(slide, path, corner=..., h=...)` (no-template / clean / generated decks have no layout
to carry it, so call it per slide). On a **provided/registered template** the branding usually already
lives on the layouts (`inspect_template.py` shows where) — don't double it; only add a per-slide logo
if the template *doesn't* carry one. Cases where a recurring logo does NOT apply: a deck that spans
many organisations (a survey, a literature review, a market landscape), or a neutral/academic talk
where house branding would be noise — there, name entities inline instead. Same fidelity rule as
above: the real mark or an honest placeholder, never a faked one.

## Planning workflow

1. During Step 3, decide each slide's visual role: source figure, deterministic chart,
   native diagram, generated plate, or no image — **by taste and purpose** (see the section
   above). Note which slides your design sense calls for a plate, so the manifest covers
   exactly those.
2. For generated plates, write the intended frame before prompting: full-bleed background,
   side panel, crop strip, texture block, or isolated object.
3. Build the prompt manifest from a sub-outline of **only the plate-worthy slides**, not the
   whole deck. Write a tiny `image-slides.md` with one heading per slide you decided needs a
   plate (or reuse just those headings), then run:

   ```bash
   python scripts/image_prompts.py image-slides.md ~/Downloads/<deck>/assets/generated \
     --deck-size 16:9 \
     --style "<deck art direction>" \
     --calm-zone "left third / right third / top band / none"
   ```

   **Do NOT pass `--count <deck-slide-count>`.** Feeding the full deck length would emit a
   context-free plate for every slide regardless of whether the design wants one — thoughtless,
   padded imagery. The script no longer pads to a count; it emits one prompt per heading in
   your sub-outline. (`--count` remains only as an optional *cap* that truncates the list.)
4. Feed each prompt from `image_prompt_manifest.json` to the
   agent's image generation skill/tool.
5. Save the selected outputs to the manifest filenames in the deck folder. **Note the
   manifest numbers files `slide-01.png`, `slide-02.png`… over your *sub-outline*, not by
   real deck position** — so map each generated file back to the actual deck slide it was
   planned for when you place it (e.g. the second plated slide is `slide-02.png` even if it's
   deck slide 7). In the build script, resolve the asset directory from the script location
   (`ROOT = Path(__file__).resolve().parent`) rather than from the process working directory.
6. Place the image with `deckkit.picture(...)`:

   ```python
   import deckkit as dk
   from pathlib import Path

   ROOT = Path(__file__).resolve().parent

   dk.picture(
       slide,
       ROOT / "assets/generated/slide-03.png",
       0.0, 0.0, 10.0, 5.625,
       fit="cover",
       alt="",  # decorative plate
   )
   ```

**Choosing `fit` — never crop the subject out.** `fit="cover"` fills the frame by cropping
the overflow; `fit="contain"` shows the whole image, letterboxed. The deciding question is
whether the image has a **subject the slide depends on**:
- **`fit="contain"`** whenever the subject — or all its parts — must stay fully visible: a
  object that must read as a whole, a scene of several items that must each show completely, a
  figure or screenshot whose edges matter. `cover` would slice the subject (leaving only part
  of the object in frame).
- **`fit="cover"`** only for edge-tolerant **texture, atmosphere, or backgrounds** where any
  crop is fine and there's no single subject to lose.
- If `contain` letterboxes too much, **shrink/zoom the placement or regenerate the plate at
  the frame's aspect ratio** — do NOT switch to `cover` and crop the subject away.

**Generate to fit the placement.** When a plate goes in a specific frame, either generate it
at that frame's aspect ratio, or prompt for the subject **centred with generous margin** so a
`cover` crop (or any reframing) can't cut it. For a full-bleed `cover` plate, require the
subject to sit well inside the central safe area, away from the edges.

**Always re-view after placing.** Look at the rendered slide and confirm the key subject is
whole and uncropped — for *every* `picture()`, generated or source. A cropped-out subject is
the most common generated-image failure; the static render is where you catch it.

## Generating the images — auto-detect the source (no API key needed)

The skill creates ONE manifest (`scripts/image_prompts.py` → `image_prompt_manifest.json`); in the
common cases image generation needs **no API key**. **Detect what's available, use it, and just say
which — don't prompt the user to choose a path, and don't ask for a key by default.** Preference order:

**1 · Native host imagegen** — if the host's agent has a built-in image tool (e.g. running *inside
Codex*), generate directly with that tool call. No key, no extra step. In Codex specifically this is
an agent tool, not a shell command a script can auto-detect; call it for each approved prompt, then
save/copy the selected bitmap into `~/Downloads/<deck>/assets/generated/` before the build script
references it.

**2 · Codex CLI** — the default outside a native-imagegen host (e.g. in Claude Code): if the `codex`
CLI is installed and logged in (check `which codex`; `codex login` once), shell out to it — it calls
Codex's hosted `image_generation` tool on the user's subscription. **No key.** Just proceed.
```bash
python scripts/generate_images_codex.py \
  ~/Downloads/<deck>/assets/generated/image_prompt_manifest.json \
  --orientation landscape        # hint 16:9 for hero/divider plates
```
One `codex exec` per image — the hosted tool's base64 lands in the Codex session rollout
(`~/.codex/sessions/.../rollout-*.jsonl`); the script decodes it to the PNG and verifies it (with a
rollout-extraction fallback). ~30–90s/image; no key, no per-image cost.

**3 · OpenAI API key — optional fallback, only if neither of the above is available.** Do **not**
request a key when native imagegen or `codex` is present.
```bash
export OPENAI_API_KEY="sk-..."
python scripts/generate_images_openai.py \
  ~/Downloads/<deck>/assets/generated/image_prompt_manifest.json \
  --model gpt-image-2 --size 2048x1152 --quality medium
```

Both scripts share the manifest format and the `--out-dir` / `--limit` / `--overwrite` / `--dry-run`
flags, save each output to the manifest path (e.g. `slide-01.png`), and skip existing files by default.

**Generation is the slowest step in the pipeline, and a manifest's images are independent — so the
scripts generate them CONCURRENTLY by default** (`--concurrency`, default 3 for the API path / 2 for the
Codex path). Put hero + divider + interior-plate (and any per-slide heroes) in ONE manifest and run it
once: a 3-image generated template lands in roughly the time of one image, not three. Lower
`--concurrency 1` only if you hit API rate limits; a single failure no longer aborts the batch (it's
reported and the rest continue). This is the main multi-process win in slide generation — the deck
*build* itself (python-pptx) is already fast and stays one script run.

> **Detection-first; ask only when stuck.** Pick native tool call → Codex CLI → API key by what's
> available, proceed, and tell the user which you used (one line). **Only ask** when *none* is available — then
> point them to `codex login` (no key) or, as a last resort, an `OPENAI_API_KEY`. Never block on a
> choice when a working path is already present.

Do not paste API keys into prompts, slide text, source files, or manifests. Keep any key in the
environment (`OPENAI_API_KEY`). The native and Codex paths need no key.

## Real subjects must be factually right

A generated image of **real, known things** must not be visibly *wrong*, even when it's
"only decorative" — a teaching/explainer audience spots it instantly and it costs you
credibility. Image models don't know real-world facts, so **state the ones that matter in
the prompt and verify them in the render**:

- **Relative size / proportion** — the classic failure. Two objects drawn the same size when
  one is much bigger (a person as tall as a building; a phone the size of a laptop; a car drawn
  the size of the truck beside it). Spell out the ratios in the prompt
  (e.g. "A is about half the height of B").
- **Count, colour, and arrangement** — the right number of items, the right colours for known
  things, the right spatial order.
- **Recognisable shape** — a real object should read as itself, not a mangled lookalike.

A **carefully prompted + verified** generated image often gets it right — spell out the
ratios, generate, then *measure/eyeball the result* and re-roll if it's wrong; a faithful
generated plate keeps the richer textured look. **Only if it still won't comply after a try
or two** — relative sizes are the usual offender — **draw it natively instead** (deckkit
ovals/shapes at correct proportions, a matplotlib plot, real data): "compute/draw the real
artifact" never fights the generator and gives exact control over sizes *and* label
alignment. Either is fine when the factual relationship *is* the point — generated-and-verified
for richness, native for guaranteed control; just never ship the unverified, wrong one.

## Prompt rules

Generated slide plates should be text-free:

- no readable words, letters, numbers, formulas, labels, logos, watermarks, citations, or fake UI copy;
- leave low-detail calm space where editable slide text will sit;
- ask for composition explicitly, e.g. "visual weight on the right, calm space on the left";
- carry a consistent palette, density, medium, and motif across the few plated slides;
- generate the first plate as the style-setter, then reuse its palette and treatment for the
  other plated slides (often just one or two) so they read as one family.

For generated images that suggest a technical domain, keep them illustrative. If the
slide needs actual evidence, compute or extract the real artifact instead.

## Verification

After placing generated assets:

- render the deck and check that the image does not compete with slide text;
- confirm no accidental readable text, pseudo-labels, fake logos, or fake charts appear;
- **confirm the key subject is whole, not cropped** — the main object/scene must be fully
  visible, not sliced by the frame (the #1 generated-image failure); switch `cover`→`contain`
  or shrink/regenerate if it's cut;
- make sure every informative image has alt text, and decorative plates use `alt=""`;
- keep final selected assets in the deck folder so the build script is reproducible.

Do not leave a build script pointing to an image in an agent's temporary or generated-images
cache. Copy the selected asset into the deck folder first.
