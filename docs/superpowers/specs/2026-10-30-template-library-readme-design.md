# Unified template library

The user approved this structure on 2026-10-30:

- Replace the README's twelve example decks and separate visual-language gallery with one template library.
- Show all registered styles, five per row. The current registry has thirty styles, so the gallery has six rows.
- Generate the gallery from the registry so new styles appear without maintaining a separate showcase list.
- Keep English and Chinese READMEs aligned; these are the two README languages currently present in the repository.
- Describe use as selecting a style and providing material, audience and slide count; do not require a separate template-repository clone.
- Use the same template terminology and five-column desktop layout on the demo site's style library, with responsive layouts on smaller screens.
- Remove NEW badges, style identifiers and type labels beside names, and the detail header's type/date subtitle.
- Keep the detail dialog focused on page previews, palette switching and a copyable prompt; remove developer-only fields, font/colour parameters and code examples.
- Remove the library's generated-version footer and its source/install/reference links.
- Replace the site's tool-generated credit with `增和科技 Addsum 出品` / `Produced by Addsum`.

The existing template files, style manifests, rendered sample images and published promotional copy remain unchanged. This is a presentation and documentation change; it does not change PPT generation behaviour.

Validation covers generated documentation consistency, the existing visual-language contract checks, all thirty image/link mappings, desktop/mobile layout, language switching and opening a style preview.
