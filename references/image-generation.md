# Image Generation for Slide Visuals

Use generated images as optional visual plates, not as the source of truth. The deck's
claims, labels, tables, charts, equations, and important annotations still belong in
editable PowerPoint objects or faithful source figures.

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
   native diagram, generated plate, or no image.
2. For generated plates, write the intended frame before prompting: full-bleed background,
   side panel, crop strip, texture block, or isolated object.
3. Run:

   ```bash
   python scripts/image_prompts.py outline.md ~/Downloads/<deck>/assets/generated \
     --count <slide-count> \
     --deck-size 16:9 \
     --style "<deck art direction>" \
     --calm-zone "left third / right third / top band / none"
   ```

4. Feed each prompt from `image_prompt_manifest.json` or `image_prompts.md` to the
   agent's image generation skill/tool.
5. Save the selected outputs to the manifest filenames in the deck folder, for example
   `~/Downloads/<deck>/assets/generated/slide-03.png`.
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
- carry the deck's palette, density, medium, and motif consistently across slides;
- generate slide 1 or the first visual plate as the style-setter, then reuse its palette
  and treatment in later prompts.

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
