# Unified template library

The user approved this structure on 2026-10-30:

- Replace the README's twelve example decks and separate visual-language gallery with one template library.
- Show twelve selected styles in the README, three per row; link to all thirty styles in the online library.
- Generate each selected preview from its registry entry and count all registered styles in the library badge.
- Keep English and Chinese READMEs aligned; these are the two README languages currently present in the repository.
- Describe use as selecting a style and providing material, audience and slide count; do not require a separate template-repository clone.
- Use the same template terminology and a four-column desktop layout for all thirty styles on the demo site, with responsive layouts on smaller screens.
- Remove the site's old example-deck gallery too, leaving one template library.
- Remove NEW badges, style identifiers and type labels beside names, and the detail header's type/date subtitle.
- Keep the detail dialog focused on page previews, palette switching and a copyable prompt; remove developer-only fields, font/colour parameters and code examples.
- Remove the library's generated-version footer and its source/install/reference links.
- Replace the site's tool-generated credit with `增和科技 Addsum 出品` / `Produced by Addsum`.
- Keep the introduction video before the template library, as explicitly requested by the user.
- Use a neutral canvas and quieter controls to give the template samples visual priority. Keep four columns on desktop, two on tablets and one on phones.
- Edit both READMEs for plain, precise language. Name the four image-led templates explicitly, distinguish editable objects from images, and remove unsupported comparisons and old timing estimates.
- Preserve installation commands and dependency guidance; align both README versions with the current generation and review workflow.

The existing template files, style manifests, rendered sample images and published promotional copy remain unchanged. This is a presentation and documentation change; it does not change PPT generation behaviour.

Validation covers generated documentation consistency, the existing visual-language contract checks, all thirty image/link mappings, desktop/mobile layout, language switching and opening a style preview.

## Amendment, 2026-11-03: the example decks return as their own section

The repository owner restored the twelve example decks in both READMEs (`## Example decks` / `## 完整示例`) and on the demo site (`#examples`), directly after the template library. The two do different jobs:

- **Template library:** choose a look. Each style has two palettes and a few sample pages, plus a prompt to copy.
- **Example decks:** see what a finished deck contains. Each is 10–16 slides of real material for one common use, with KPI grids, native charts, tables, timelines, diagrams, equations, backup slides and a sources page. Each can be flipped through online or downloaded as a `.pptx`. To reuse a deck's design, give its `.pptx` to slide-maker as a reference deck.

The template library still links styles only; the example section links whole decks only. `tests/test_vl_contract.py` checks both, as well as the order of the two sections.
