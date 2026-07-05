# Generate a template with an image tool

The user picked Q1's **"generate a template with an image tool."** Instead of building on a
provided template or designing a clean default, you **create a bespoke visual identity with the
image tool** (a styled hero/divider illustration) and then **reproduce it natively** so every
content block fits it. Use it for a *vivid, designed* deck — a product launch, a festival/event,
a brand or culture deck, a playful pitch — where a clean default look isn't enough.

This branch **decides the look up front**, so after it's confirmed you **skip the 3-direction
gate** and run the rest of the interview (purpose, audience, source, language) normally.

## The construction model (this is the whole idea)
A good generated template is a **cohesive visual SYSTEM**, not one pretty picture — a palette, a
small **motif vocabulary** (the signature shapes/decorations), a type pairing, and **component
treatments** (how a card, a stat, an emphasis band, a title look). It is realised in **two
layers**, and the split is what keeps it editable *and* on-brand:

- **Hero + section-divider slides → a full-bleed GENERATED image.** A rich, styled, **text-free**
  illustration carries the mood; the title and badges sit on top as **native** editable shapes.
  These carry the full-strength imagery (interior pages get only the faint plate). **And bookend the deck** — it OPENS on the hero cover and should CLOSE on a matching **ENDING page** in the same divider-strength imagery, so the deck doesn't simply stop on a faint body slide; the wrap-up sits natively on top (thank-you / recap / call-to-action / contact), the mirror of the cover. The ending page can reuse the divider/hero plate — no new generation needed.
- **Content slides → built NATIVELY to match, on a SHALLOW background — never a flat single
  colour.** The content (cards/chips/bands) is native python-pptx that reuses the template's
  palette, motifs, and component treatments — that's why inserted blocks *fit*. But the slide
  **canvas underneath them is not a plain fill**: every interior page carries a *subtle, low-
  contrast* background so the deck feels designed end-to-end, not "cover is gorgeous, body is
  blank." A flat one-colour content slide next to a lush cover is the #1 tell of a half-finished
  generated template. The shallow background is **faint by design** (it sits *behind* content and
  must never fight the text — see the legibility guardrail), and — **in the general case (and on the
  non-image-tool branches)** — it comes from one of (the image-tool MUST below then *picks* the plate):
  - a **faint native texture** in the palette — a soft two-stop gradient wash, a faint
    `backdrop_motif` field, or a tinted corner/band — the lightest-weight option, fully editable; **or**
  - a **subtle imagery plate** — a dedicated low-contrast, text-free background image generated in
    the same style (placed `picture(fit="cover")`), or the hero re-placed full-bleed under a heavy
    `scrim_overlay` so a soft but **still-visible** ghost of it remains (a ghost you genuinely can't see is the same failure as no plate — see the visibility floor in the legibility guardrails).
  **🔴 MUST for the image-tool template — the interior shallow background is itself a GENERATED image
  plate, not a flat / merely-native fill.** Since the user chose a *generated visual identity*, every
  interior page carries a **dedicated low-contrast, text-free background image generated in the same
  style** (the subtle imagery plate above), so the body reads as *designed* as the cover; a flat — or a
  merely-native, gradient-only — interior under a lush generated cover is the failure to avoid. Apply the
  **SAME plate on every content slide** so they read as one system; only the cover and dividers get the
  full, vivid imagery. **The plate is a faint DERIVATIVE of the hero itself** — the hero's own signature motif and palette, softened, evenly-toned, low-saturation — **not a generic or unrelated texture** (a stock triangulated mesh, random grain): a plate whose motif differs from the hero reads as a second, unrelated design and quietly breaks the one-system illusion, so 'a plate on every page' is met on paper while the deck stops feeling like one identity. *Carves (audit-scoped) — the MUST yields to:* **(1)** a deliberately **minimal /
  flat** generated style (Swiss · Scandinavian · Brutalist) whose aesthetic *is* near-flat; **(2)** the
  **user explicitly asking for clean / flat / minimal interiors**, or a **brand identity that is itself a
  flat colour field** (honour the request/brand — a faint native texture or the flat brand field is then
  correct); **(3)** a **line-heavy figure slide**, where you **mask / suppress the plate** (the
  motif-suppression rule above). Outside those, generate the plate. *(Outside this image-tool branch — e.g. a "design a clean one" deck — a
  faint native texture is still a fine shallow background; the generated-plate MUST is specific to having
  chosen the image tool.)*
  - **But SUPPRESS the motif on a slide whose content is itself the same visual language** — e.g. a
    **line/grid** shallow background (blueprint grid, hatch) behind a slide whose figure is **dense
    line-work** (a timing diagram, a k-space line stack, a wave/axis plot, a ruled table): the motif and
    the figure blend and muddle each other. Provide a **grid-free variant of the same background** (keep
    the frame/footer chrome so it still reads as one system) or seat the figure on a solid/frosted panel
    that masks the motif. This is the one place "same treatment on every slide" yields — see
    `design-principles.md` "A textured / line / grid background must not compete with line-heavy content."
  - **🔴 MUST — on a generated-template deck the content BLOCKS are FROSTED (semi-transparent),
    NEVER flat opaque.** A *hard rule*, not a skippable default: a generated template's whole point is a
    rich, *designed* background, so a flat **opaque** card reads as "pasted on" and breaks the illusion.
    Every interior page therefore pairs the **shallow background (above)** with **frosted blocks** — the
    two go together, and shipping either a flat-colour content page **or** opaque cards on the generated
    background is the failure to avoid. (Narrow exceptions that may stay OPAQUE: a thumbnail's own image; a deliberately solid emphasis
    band; a panel placed to MASK a line motif under a line-heavy figure (that one MUST be solid, per the
    suppress-motif rule above); a **full-bleed figure / photo that fills the slide** (not a "block" — out
    of scope); and a **deliberately PLAIN / near-flat minimal style** (Swiss · Scandinavian · Brutalist)
    whose interior background is flat by design — there a crisp **opaque** card is correct, matching
    design-principles.md "Block fill must FIT the background". Otherwise cards / panels / chips default
    frosted.)
    Give every card/panel/chip a **slight transparency** so the background shows through (~30–45%) and it
    belongs to the scene — a low-alpha glass tint of the block colour + a subtle lighter rim
    (`deckkit.glass_card`, or `box(grad=[(0,tint,α),(1,tint,α)])` with **α ≈ 0.55–0.72**), the **same
    treatment deck-wide**, tint/rim **harmonised with the palette** (dark deck → dark glass + a faint
    accent rim; light deck → white glass). **Pick α by how rich/busy the background is** — a busy plate →
    a bit more opaque (higher α) for contrast; a faint shallow wash → more transparent. **Text ≥4.5:1 is
    non-negotiable** — raise α or strengthen the tint over a bright/busy patch (never drop the transparency
    just to pass contrast — adjust α instead). (design-principles.md "Block fill must FIT the background".)

> Don't make every slide a generated image with text baked in — baked text isn't editable, wraps
> badly in other languages, and can't be critiqued/fixed. Images set the mood on heroes/dividers;
> native shapes carry the content.

## Workflow

### 1 — Mini-interview for the visual identity (before generating)
Run a short extra interview *now* — only what the *look* needs (purpose/audience/source come
later in the normal interview):
- **Scenario / topic** — what the deck is for (e.g. "summer music festival annual handbook").
- **Show the candidate styles as a VISUAL HTML preview, not just a text list — a "style gate"
  (recommended).** Don't make the user choose a style from words alone. Pick the **3–4 best-fit named
  styles** for this scenario from the **Style library** at the end of this file (e.g. **Memphis** from
  the Sugar Rush sample, or Swiss, Art Deco, Vaporwave, Editorial, Risograph, Glassmorphism, Blueprint…),
  **tailor each to the topic + brand colours**, turn each into a **token-set** (palette + portable fonts +
  motif/accent — pull from `presets.py` when the style is a named preset, else author it), and render all
  of them into **ONE self-contained HTML** with **`scripts/archetypes_html.py styles.json out.html
  "Deck Title"`** — each style shown across a few representative pages (cover · content · diagram · data).
  **Hand the user the single `file://…` link** to open in a browser and *see what each style is actually
  like* — then pick (each card has a **Pick** button that copies a paste-back line). This mirrors the
  **direction gate** (`collaborative-mode.md`) but for the generated-template look.
  - The HTML mockups are **native token-set previews** — they convey each style's **palette / type / mood**
    (the *direction*); the style's **motifs and the actual generated imagery** are NOT in the mockup —
    those land **only for the chosen style** at the 🔴 hero checkpoint below. **Don't generate 3–4 real
    hero images just for the picker** —
    that's slow and wasteful; mock them natively in the HTML, generate only the winner for real.
  - **The choice prompt MUST offer these as FIRST-CLASS, peer options — not just fallbacks** (present
    them as selectable choices, e.g. via the host's option UI; some users want to *delegate* the look
    and shouldn't have to engage with the picker to do it):
    - **A / B / C — pick one of the shown styles** (the common path: they *see* the candidates and choose).
    - **"Auto — you pick the best-fit and just go"** — an explicit, up-front peer option (NOT only a
      "liked none" escape). When the user takes it (or says "you decide / design it for me"), YOU select
      the best-fit library style from **scenario + brand colours** and **name it back** ("for a summer
      festival I'll go Memphis/pop"), or, for a distinctive scenario, give a richer **mood-led** prompt
      (scenario + energy + palette + "design a cohesive visual identity") instead of a named style — then
      generate and let them react at the hero checkpoint. **If they pick Auto up front, you may SKIP the
      HTML style gate entirely** and go straight to generate → the 🔴 hero checkpoint (don't make a
      delegating user wait on a picker they didn't want).
    - **"D — describe your own / provide a reference"** — synthesize a fresh token-set from their words /
      reference image / brand and **regenerate the HTML** so they still pick from something they can *see*.
  Auto is **not a blind commit**: every path — pick, auto, or own — resolves to a concrete look the user
  reacts to at the 🔴 hero checkpoint, which is the real gate.
- **Vibe / mood (if describing your own)** — the aesthetic in words: energy (calm↔loud), era,
  references. Use this to pick/blend a library style or to author a fresh one.
- **Brand colours / must-haves** — any fixed colours, a logo, words that must appear.
- **Reference material — invite drop-ins.** Explicitly offer: *"drop in any reference images, a
  logo, a mood board, screenshots of a look you like, or a brand guide and I'll steer the
  generation by them."* Use provided references to anchor the style (and, if a logo/photo is
  given, place it natively, not regenerated).

**Then TAILOR the chosen style to *this* deck before generating** — fold in the topic, the brand
colours, the energy, and anything from the reference materials. The library entry is the *starting
language, not a straitjacket*: customise its palette/motifs to fit, and blending two presets (or a
preset + a reference) is fine — just name what you're combining so the choice is legible to the user.

### 2 — Generate the template image(s)
Generate a **full-bleed, text-free** hero/divider illustration in the chosen style:
- **Tooling — auto-detect the source, no API key needed** (build the prompt with
  `scripts/image_prompts.py`; full guidance in `references/image-generation.md`). Use what's present,
  in order: **(1)** native imagegen when the host has it (inside Codex — use the agent tool call
  directly, free, no key); **(2)** else
  the **Codex CLI** `scripts/generate_images_codex.py --orientation landscape` if `codex` is installed
  (Codex/ChatGPT subscription, **no key** — shells `codex exec`, decodes the hosted image from the
  session rollout); **(3)** else, only as a fallback, the OpenAI API `scripts/generate_images_openai.py`
  with `OPENAI_API_KEY`. **Don't prompt the user to choose or ask for a key when (1) or (2) is
  available — just use it and say which; ask only if none exists.** Render at the deck's
  aspect (16:9 → e.g. `1536x864` / `2048x1152`). In Codex's native path, follow its save-path policy:
  generate first, then move/copy the selected output from `$CODEX_HOME/generated_images/...` into
  this deck's folder before referencing it in `style.py` or a build script.
- **Prompt craft:** describe the *style + motif vocabulary + palette*, the subject/scene, **"no
  text, no lettering, no logos"**, and **leave a calm, lower-contrast zone** (a corner/band)
  where the title will sit. Ask for the **signature motifs** explicitly (e.g. "scattered Memphis
  geometric shapes — zigzags, dots, triangles, squiggles, checkerboard — bold black outlines")
  so you can reproduce them natively later.
- Generate **1–2 plates**: a **hero** (cover) and, if the look differs, a **divider** variant.
- **Generate the interior shallow-background plate too — 🔴 MUST (see the construction model).**
  Alongside the hero, generate **one extra low-contrast background plate**: a **text-free, faint,
  evenly-toned** version of the style (calm, low-saturation, no strong focal point, generous negative
  space) made to sit *behind* content on **every interior page**. Prompt it explicitly for low contrast
  and even tone ("soft, faded, low-contrast background texture, lots of calm negative space in the
  centre, no focal subject, no text") so dark text stays readable on top with only a **light scrim**.
  *Carve:* a deliberately **minimal / flat** generated style (Swiss · Scandinavian · Brutalist) may skip
  the plate and use a faint native texture instead — its aesthetic is near-flat by design.
- Keep assets in `~/Downloads/<deck>/assets/generated/`. Never leave a generated template
  image referenced only from Codex's default generated-images cache or an OS temp folder.

### 3 — Derive a matching `style.py` (treat the image as a style example)
Study the generated image the way you'd study a provided style example
(`references/style-analysis.md`) and encode it so native content matches:
- **Palette — extract it from the image** so colours are coherent:
  resolve the image path relative to the deck/build script, then call
  `BASE = deckkit.palette_from_image(ROOT / "assets/generated/hero.png", 6)`; set the style's
  base/ink and `ACCENTS` from it. (This is the bridge that makes native blocks fit the
  generated look.) Avoid bare `"assets/..."` paths that depend on the shell's current directory.
- **Motif vocabulary** — write 3–5 tiny native helpers for the signature shapes (e.g.
  `zigzag()`, `dot()`, `triangle()`, `squiggle()`), drawn with `deckkit` autoshapes in the
  palette, with the same outline weight. **Sprinkle them sparingly** as accents near content —
  never over the text.
- **Component treatments** — define the template's card / stat / emphasis-band / chip /
  title-chrome look as helpers (e.g. a rounded card with a **colour-header band**, a dark
  **emphasis band** with an accent headline, an accent-bar **title chrome**). Content slides call
  these so every block is on-system.
- **A `content_bg(slide)` helper — the shallow interior background, called FIRST on every content
  slide.** This is what stops content pages being flat. Per the 🔴 MUST it places the **GENERATED
  interior plate**: `deckkit.picture(bg_plate, fit="cover")` then a **light scrim** (`scrim_overlay`, or
  a white low-alpha `box`) to mute it to a shallow wash. Encode it ONCE so it's identical on every slide;
  keep it *low-contrast by construction* and verify body text clears 4.5:1 on top. *(Minimal/flat-style
  carve only — when no plate was generated: a faint two-stop gradient, or a faint
  `deckkit.backdrop_motif(color=<very light palette tint>)`, instead.)*
- **A `brand(slide)` helper for the logo (only if the deck is about a company/institution/product).**
  Wrap `deckkit.logo(slide, LOGO_PATH, corner=..., h=...)` so the real logo lands in the SAME spot
  on every slide. Decide the corner once to fit the template (top-right is the usual choice; move it
  if the title chrome or motifs occupy that corner) and keep it consistent. On a vivid hero, add a
  small scrim/light plate behind the logo so it stays legible.
- **Type + chrome** — pick a display font that fits the vibe (portable; see `font-guidance.md`)
  and set `deckkit.FONT`/`EAFONT`; define `title_bar`/`footer` to the template's chrome.
- Put all of this in the deck's `style.py` (copy `references/examples/style_example.py` as the
  starting shape).

### 4 — Render a sample and get feedback (hard gate)
Build **two** slides — the **cover** (hero image + native title/badges) and **one real content
slide** (native, using the derived components: a few cards + an emphasis band + motifs) — render
them, and show both. The content slide is essential: it proves the blocks actually fit.
> **🔴 CHECKPOINT** — show the generated template (hero + a sample content slide) and get the
> user's OK. Iterate on their feedback until they confirm. Only then proceed.

**Match the FIX to what they asked to change — don't reflexively recolor:**
- **A small palette / contrast tweak** ("warmer accent", "lighter background", "less saturated", "bigger
  title zone") → adjust `style.py` (and re-place natively); **no regeneration needed**.
- **A change of ATMOSPHERE / mood / style / feel** ("make it more energetic / calmer / darker / more
  futuristic / more organic / more playful / more premium / more clinical") → **RE-GENERATE the hero —
  do not just change the colour.** A mood lives in the **imagery itself** — its *subject, composition,
  lighting, texture, and motifs* — not only the palette. Rewrite the image prompt so **all** of those
  shift to embody the new atmosphere (e.g. *more energetic* → dynamic diagonal composition, bold forms,
  vivid directional light; *calmer* → sparse, soft, generous negative space; *more organic* → natural
  materials and hand-made texture instead of hard geometry), generate a fresh plate, then **re-derive
  `style.py` from the new image** so the native blocks match. Recoloring the old plate leaves its
  original mood baked into the picture, and the hero then fights the feeling the user asked for. If it's
  unclear whether they mean a tweak or a new atmosphere, ask in one line before spending a generation.

### 5 — Continue the interview, then build to the template
- The look is decided → **skip the 3-direction gate** and any style question; run the rest of the
  normal interview (purpose & audience & time, source material, language).
- **Build (step 4 of SKILL.md):**
  - **Cover, section dividers, and the closing / ending page** → the generated image full-bleed (`picture(..., fit="cover")`),
    with the **title and badges native on top**, placed in the image's calm zone (add a soft
    scrim/plate behind the title if the area under it is busy, so contrast stays ≥ 4.5:1).
  - **Content slides** → built **natively** in `style.py`, in this order: **(1)** `content_bg(slide)`
    first so the page has its shallow background (never a flat single colour); **(2)** the template's
    cards/bands/chips/motifs for the content; **(3)** `brand(slide)` last (if it's a
    company/institution/product deck) so the logo sits on top of everything. Reuse the source's real
    figures/tables as always — framed to sit on the template (a thin card/plate behind a figure helps
    it sit on a textured background).
  - **The logo also goes on the cover and dividers** (placed natively over the imagery, with a scrim
    if needed) so the brand is present on every page, including the end pages.
  - Keep the craft rules (one idea/slide, whole figures, contrast, suitable spacing, balanced
    blocks). Then the normal **render + critic loop** — the critic judges whether content
    genuinely fits the template (palette, motifs, components consistent), whether **every interior
    page carries the shallow background** (none left flat), whether the **logo is present and
    consistently placed** where the deck calls for one, and that everything stays legible.
- **Save the confirmed template to the registry** (`~/.codex/slide-templates/<name>/` in
  Codex, or `~/.claude/slide-templates/<name>/` in Claude Code): the `style.py`, the
  generated `assets/`, and a `profile.md` — so it's a reusable choice next time (it shows up
  under Q1's registered templates).

## Legibility & fidelity guardrails (busy styles fight text)
- **Text-free images, native text on top** — never bake slide copy, numbers, labels, or logos
  into the generated plate (the deck's standing rule). *One narrow, opt-in exception:* a purely
  **decorative hero WORDMARK** baked into the cover image **only if the user explicitly asks** for
  that exact stylised-lettering look — and even then, every other piece of text stays native.
- **Contrast on a busy background** — a vivid hero will wreck a thin title. Put the title in the
  image's **calm zone**, or behind a **solid / translucent plate** (a rounded box in a palette
  colour), and check `contrast_ratio ≥ 4.5`.
- **Don't let motifs crowd content** — decorations are *accents in the margins/corners*, not a
  layer over the words. If a motif overlaps text, move or drop it.
- **Consistency across slides** — same palette, same motif set, same component treatments, the
  **same shallow background**, and the **same logo placement** on every slide. A one-off card style,
  a stray colour, a flat content page among textured ones, or a logo that jumps corners breaks the
  "template" illusion faster than anything; the critic should flag it.
- **The shallow background must stay BEHIND the content** — it's atmosphere, not a competing layer.
  If it darkens or busies the area under text, mute it harder (lighter tint, stronger scrim, fewer
  motifs); body text must clear 4.5:1 against whatever the background leaves under it. A subtle
  background that forces every text block onto its own opaque card has been made too strong. **But there is a FLOOR as well: the plate must stay SUBTLY VISIBLE** — a viewer should be able to *see* the body page is textured, not have to guess. Muting is one-directional pressure, so it's easy to over-scrim the plate into a flat near-white field that satisfies 'a plate on every page' in code yet reads as absent — the same failure as no plate at all. If you can't tell the plate is there at a glance, the scrim is too heavy: lift it until the hero's motif is faintly but genuinely perceptible, and recover text contrast with the frosted blocks rather than by erasing the plate.
- **Logo = the REAL mark, present where it belongs** — for a company/institution/product deck the
  logo appears on every page; use the real asset (image-generation.md's hierarchy), never a faked or
  recolored one, and if it's missing, ask the user or use an honest "logo here" placeholder.
- **Generated real things must be right** — if the hero depicts real objects/places, the
  size/proportion/count/colour must be factually correct (the image-generation fidelity rule).

## Checklist
- [ ] Mini-interview done (scenario; style offered as a choice — **best-fit library styles** +
      describe-own + reference drop-ins + **"let the image tool pick" (auto)**; brand colours).
- [ ] A style **chosen and tailored** to the scenario — a picked library style, an auto-picked one
      (named back to the user), or a fresh look from a reference — palette/motifs customised, not raw.
- [ ] Hero (and divider) generated **text-free**, in-style, with a **calm zone** for the title — **plus
      the 🔴 MUST interior shallow-background plate** (low-contrast, even-toned; skipped only for a
      deliberately minimal/flat style).
- [ ] `style.py` derived: palette **extracted from the image**, motif helpers, component helpers,
      fonts/chrome, a **`content_bg(slide)`** for the shallow interior background, and a
      **`brand(slide)`** logo helper if the deck is about a company/institution/product.
- [ ] Sample **cover + content slide** rendered and **confirmed by the user** (🔴 checkpoint).
- [ ] Direction gate **skipped**; rest of the interview completed.
- [ ] Built: dividers use the image; content is native and **on-system** with the **GENERATED shallow-
      background plate on every interior page** (🔴 MUST — no flat single-colour or merely-gradient
      interior, except a deliberately minimal/flat style) + frosted blocks; the **real logo present and
      consistently placed** on every page if it's a company/institution/product deck; figures framed
      to sit on the template; legibility ≥ 4.5:1 everywhere.
- [ ] The interior plate is a **faint DERIVATIVE of the hero** (same motif/palette, not a generic texture) and stays **subtly visible** on every body page — not scrimmed into a flat near-white field.
- [ ] A **closing / ending page bookends the cover** — full-strength divider-style imagery with a native wrap-up (thank-you / recap / CTA / contact), so the deck doesn't stop on a body slide.
- [ ] Template **saved to the registry** for reuse.

## Style library — well-known starting styles (seed, then tailor)
Proven visual languages to seed the generation from — pick the **3–4 best-fit for the scenario**,
offer them as options (+ "describe your own" / "I'll provide a reference"), then **tailor** the
pick (palette, energy, brand colours) before generating. Each entry gives the *palette* /
*motifs* / *type* you'll both put in the image prompt **and** encode in the native `style.py`
(so content matches). Blend two when it fits; add new ones as you discover them.

**Bold & geometric**
- **Memphis / New Wave** *(80s–90s, the Sugar Rush sample's style)* — playful, loud, chaotic-
  geometric. *Palette:* hot-pink · cyan · yellow · green · black on cream. *Motifs:* squiggles,
  zigzags, confetti dots, triangles, checkerboard, bold black outlines. *Type:* chunky rounded
  display + clean sans. Heroes are busy illustrations; content = cream bg + colour-header cards +
  sprinkled motifs.
- **Bauhaus** — functional, primary, geometric. *Palette:* red/yellow/blue + black/white.
  *Motifs:* circles/triangles/squares, diagonals, grids. *Type:* geometric sans.
- **Swiss / International** — rigorous grid, objective, minimal. *Palette:* black/white + one red,
  lots of white. *Motifs:* strong grid, hairline rules, flush-left, big numerals. *Type:*
  neo-grotesque (Helvetica-like).
- **Constructivist** — propaganda-poster energy. *Palette:* red/black/cream. *Motifs:* hard
  diagonals, photo-cutouts, heavy slab type, angular blocks.
- **Pop Art** — comic, bold, halftone. *Palette:* primaries + black outlines. *Motifs:* Ben-Day
  dots, speech bubbles, thick outlines. *Type:* comic bold.

**Retro-future & digital**
- **Vaporwave / Synthwave** — nostalgic retro-future, neon. *Palette:* neon pink/purple/cyan on
  dark, sunset gradient. *Motifs:* grid horizon, chrome, sun, glow, glitch. *Type:* bold italic retro.
- **Cyberpunk / tech-noir** — dark, neon, edgy. *Palette:* near-black + neon cyan/magenta/lime.
  *Motifs:* HUD frames, scanlines, circuitry, glitch. *Type:* condensed/mono techy.
- **Y2K / Frutiger Aero** — glossy, optimistic, early-2000s. *Palette:* aqua/lime/chrome/white.
  *Motifs:* bubbles, gloss, chrome, bokeh, gradients. *Type:* rounded bold.
- **Glassmorphism** — soft, modern, depth. *Palette:* vivid gradient bg + frosted translucent
  panels. *Motifs:* blurred glass cards, soft shadows, light orbs. *Type:* clean rounded sans.
- **Gradient / modern SaaS** — friendly-tech. *Palette:* vivid multi-stop gradients + dark/white.
  *Motifs:* blobs, soft gradients, glassy cards. *Type:* geometric sans.

**Editorial & refined**
- **Editorial / magazine** — typographic, sophisticated. *Palette:* ink + one accent on off-white.
  *Motifs:* columns, drop caps, hairlines, big serif headlines. *Type:* elegant serif + sans.
- **Art Deco** — luxe, symmetric, glamorous. *Palette:* gold/black + deep green or navy. *Motifs:*
  sunburst/fan, chevrons, thin gold lines, symmetry. *Type:* high-contrast serif / geometric caps.
- **Scandinavian minimal** — calm, airy, warm-muted. *Palette:* muted earth + soft pastel + much
  white. *Motifs:* generous whitespace, thin lines, simple shapes. *Type:* humanist sans.
- **Brutalism** — raw, stark, intentional-unpolished. *Palette:* high-contrast black/white + one
  harsh accent. *Motifs:* thick borders, exposed structure, monospace. *Type:* mono/system.

**Textured & organic**
- **Risograph** — grainy, spot-colour, handmade. *Palette:* 2–3 riso inks (fluoro pink, blue,
  yellow), overprinted. *Motifs:* grain, halftone, slight misregistration. *Type:* bold sans.
- **Hand-drawn / sketch** — friendly, approachable. *Palette:* warm marker tones. *Motifs:*
  hand-drawn arrows/underlines, doodles, paper texture. *Type:* handwritten + clean sans.
- **Watercolour / botanical** — soft, artistic, natural. *Palette:* washed pastels, earthy.
  *Motifs:* watercolour washes, leaves/botanicals, soft edges. *Type:* light serif.
- **Blueprint / technical** — precise, engineering. *Palette:* cyan/white lines on deep blue.
  *Motifs:* grid, schematic lines, dimension marks, callout leaders. *Type:* technical mono/sans.

**Clean & corporate**
- **Corporate-bold / modern brand** — confident, premium. *Palette:* one strong brand hue + dark +
  white. *Motifs:* big type, bold shapes, hero numbers, subtle gradient. *Type:* strong geometric sans.

> These are *starting points*, not a closed list. The user's own reference, brand, or a described
> look always outranks a preset; a preset just gives the image tool and the native build a strong,
> coherent target instead of a cold start.
