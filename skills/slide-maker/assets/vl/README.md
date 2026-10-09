# Visual-language sample images

These images are AI-generated for slide-maker's own style samples (2026-10-03, metered image API,
authorised by the maintainer). The people shown are not real people and the places are not real places:
the people are generic, the hall, garden and objects are invented. They exist only so the direction preview can show what each
visual language does with photographs or illustrations — "style sample — not your content".

- `photo/` — a warm documentary series (a neighbourhood repair café); `kettle-cutout.png` is keyed.
- `watercolour/` — a watercolour series (a balcony garden); `seedling-cutout.png` is keyed.
- `samples/<language>.jpg` — rendered samples (one per language and ground) and `samples/manifest.json`, the
  fingerprint of the deck each one was rendered from.

## Maintainer note: refreshing the bundled samples

`python3 "$SKILL/scripts/visual_languages.py" --sample <dir>` builds every sample deck into `<dir>` and prints, per
deck, a `NEXT:` render command and a `then:` sheet command. Those write into `<dir>` only, so a user who runs them
never touches the files shipped here.

To refresh the bundled previews after a change to the code that draws them, add `--refresh-bundled`: the `then:`
lines then write `samples/<stem>.jpg` here and update `samples/manifest.json`. Run every printed `NEXT:` and `then:`
line, on macOS (the samples are measured and rendered there), and commit the JPGs with the manifest.
`tests/test_visual_languages.py` rebuilds each sample deck and compares it with `manifest.json`, so a preview that
no longer matches the code fails there.
