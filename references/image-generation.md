# Image Generation for Slide Visuals

Use generated images as optional visual plates, not as the source of truth. The deck's
claims, labels, tables, charts, equations, and important annotations still belong in
editable PowerPoint objects or faithful source figures.

## Use sparingly — most slides need no generated image
Image generation is a **per-slide judgment call, not a per-deck habit** — the same restraint
as animation. Many strong decks use **zero** generated images, and a generated plate on
*every* slide is the failure to avoid: it makes a deck look templated and pulls attention
off the content. Default to **no** generated image, and add one only when a *specific* slide
clears this bar:
- the slide would genuinely feel visually thin without it, **and**
- a *decorative or conceptual* image (not evidence) is what it needs, **and**
- nothing more faithful — a source figure, a real computed/extracted artifact, a chart, or
  simply more whitespace — would serve that slide better.

If you can't name what a plate adds to *that particular slide*, don't generate it. When the
user asks to use a GPT/image tool, this still applies: generate for the few slides that need
it, not one per slide. Decide image-by-image, the same way you decide build-by-build.

## When to use image generation

Use the agent's native image generation skill when a slide would benefit from:

- a text-free hero image, atmospheric background, or side-panel photo/illustration;
- a conceptual scene where no source figure exists and exact factual detail is not the point;
- decorative texture, motif, object detail, or transition imagery that supports the deck's style;
- product/lifestyle/editorial imagery when the user is asking for a pitch or narrative deck and no real product asset is required.

Prefer real or deterministic assets instead when the visual carries evidence:

- source figures, tables, screenshots, charts, medical/scientific imagery, microscopy, maps, UI states, code, product shots, logos, or brand marks;
- any result whose content must be traceable to the user's material;
- any plot or diagram that needs readable labels, axes, numbers, or formulas.

## Planning workflow

1. During Step 3, decide each slide's visual role: source figure, deterministic chart,
   native diagram, generated plate, or **no image** (the default — see "Use sparingly"
   above). Write down the short list of slides that actually earned a plate; for most decks
   that list is empty or one or two slides.
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

   **Do NOT pass `--count <deck-slide-count>`.** Feeding the full deck length generates a
   context-free plate for *every* slide — the one-image-per-slide habit to avoid. The script
   no longer pads to a count; it emits one prompt per heading in the sub-outline. (`--count`
   remains only as an optional *cap* that truncates the list.)
4. Feed each prompt from `image_prompt_manifest.json` or `image_prompts.md` to the
   agent's image generation skill/tool.
5. Save the selected outputs to the manifest filenames in the deck folder. **Note the
   manifest numbers files `slide-01.png`, `slide-02.png`… over your *sub-outline*, not by
   real deck position** — so map each generated file back to the actual deck slide it was
   planned for when you place it (e.g. the second plated slide is `slide-02.png` even if it's
   deck slide 7).
6. Place the image with `deckkit.picture(...)`:

   ```python
   import deckkit as dk

   dk.picture(
       slide,
       "assets/generated/slide-03.png",
       0.0, 0.0, 10.0, 5.625,
       fit="cover",
       alt="",  # decorative plate
   )
   ```

Use `fit="contain"` for source figures or screenshots whose edges must remain visible.
Use `fit="cover"` only when cropping is acceptable.

## OpenAI API fallback

In Codex, prefer the native imagegen tool when available. Outside Codex, users can
generate the same manifest through the OpenAI Images API:

```bash
export OPENAI_API_KEY="sk-..."

python scripts/generate_images_openai.py \
  ~/Downloads/<deck>/assets/generated/image_prompt_manifest.json \
  --model gpt-image-2 \
  --size 2048x1152 \
  --quality medium
```

The script saves each output to the manifest path, such as `slide-01.png`. By default it
skips existing files; pass `--overwrite` to regenerate. Use `--dry-run` to preview what
would be generated without calling the API.

Do not paste API keys into prompts, slide text, source files, or manifests. Keep the key in
the environment (`OPENAI_API_KEY`) or the user's normal secret manager.

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
- check that important subject matter is not cropped awkwardly;
- make sure every informative image has alt text, and decorative plates use `alt=""`;
- keep final selected assets in the deck folder so the build script is reproducible.

Do not leave a build script pointing to an image in an agent's temporary or generated-images
cache. Copy the selected asset into the deck folder first.
