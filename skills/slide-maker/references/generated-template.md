# Generate a template with an image tool

The user picked Q1's **"generate a template with an image tool."** Instead of building on a
provided template or designing a clean default, you **create a bespoke visual identity with the
image tool** (a styled hero/divider illustration) and then **reproduce it natively** so every
content block fits it. Use it for a *vivid, designed* deck — a product launch, a festival/event,
a brand or culture deck, a playful pitch — where a clean default look isn't enough.

This branch **decides the look up front**, so after it's confirmed you **skip the 3-direction
gate** and any LOOK question — the rest of the interview (purpose, audience, source, language,
and Q4's density + tone, which the visual identity does not decide) still runs normally.

## Table of contents
- The construction model (this is the whole idea)
- Workflow
  - 1 — Mini-interview for the visual identity (before generating)
  - 2 — Generate the template image(s)
  - 3 — Derive a matching `style.py` (treat the image as a style example)
  - 4 — Render a sample and get feedback (hard gate)
  - 5 — Continue the interview, then build to the template
- Legibility & fidelity guardrails (busy styles fight text)
- Checklist
- Style library — well-known starting styles (seed, then tailor)

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
  plate, not a flat / merely-native fill — and it is TOPICAL.** The chosen style is the **whole deck's**
  identity, not cover decoration: every
  interior/main-content page carries a **dedicated low-contrast, text-free background image generated in
  the same style AND related to the deck's topic/content** (the subtle imagery plate above — a faint
  circuit-and-node field for an AI deck, faint botanicals for a garden brand, never a generic mesh or
  abstract filler that could sit under any deck), so the body reads as *designed* as the cover; a flat — or a
  merely-native, gradient-only — interior under a lush generated cover is the failure to avoid. Apply the
  **SAME plate on every content slide** so they read as one system (a second topical plate variant is
  fine for a long deck's section change); only the cover and dividers get the
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
    **The composite card components default OPAQUE — switch them to their glass variants here:**
    `kpi_card(fill="glass")` (frosted body instead of the white default), `icon_tile(glass=True)`,
    or seat any other component (`dumbbell_board`, `flow_compare`, a stat block) on a `glass_card`
    first and pass `fill`-less content on top. A stock component dropped at its white-canvas default
    onto an interior plate is exactly the "opaque card on generated background" failure above.
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
- **Show the candidate styles as a VISUAL HTML preview of REAL generated images — a "style gate"
  (recommended).** Don't make the user choose a style from words alone — and don't frame this gate
  around *colour* (colour variations of one look belong to the flat/clean **direction gate** in
  `collaborative-mode.md`; palette here is a *derived detail*, tailored after the style is chosen).
  This gate is about **STYLE, chosen for the TOPIC + CONTENT**: pick the **3 best-fit named styles for
  what this deck is actually about** from the **Style library** at the end of this file, and make them
  **deliberately DIVERSE** — three different visual *languages* (e.g. Swiss vs Manga vs Glassmorphism;
  Ink-wash vs Blueprint vs Claymorphism), never three moods of one language. For each candidate,
  **GENERATE 1 real template image (2 for the front-runner) in that style, on this topic** — a
  text-free hero/cover-grade plate with a calm title zone, exactly what the winner's cover will be —
  then compose **ONE self-contained HTML gallery** (the images beside the file, one `<img>` card per
  style with its name, a one-line "why it fits this topic", and a **Pick** line) and **hand the user
  the single `file://…` link**. The user judges the *actual generated look*, not a native mock of it —
  for an image-driven template, palette-token mockups under-sell every image-native style (manga,
  clay, watercolour, collage) and the choice is only real when they see the imagery. Cost is bounded:
  3–4 images total, and the winner's gate image **is reused as the deck's hero** (no regeneration).
  - *Fallback:* if image generation is unavailable (no tool, no key) or the user wants the fastest
    path, fall back to native token-set mockups via `scripts/archetypes_html.py` — say plainly that
    they show palette/type direction only, and the real imagery lands at the 🔴 hero checkpoint.
  - **The choice prompt MUST offer these as FIRST-CLASS, peer options — not just fallbacks** (present
    them as selectable choices, e.g. via the host's option UI; some users want to *delegate* the look
    and shouldn't have to engage with the picker to do it):
    - **A / B / C — pick one of the shown styles** (the common path: they *see* the candidates and choose).
    - **"Auto — you pick the best-fit and just go"** — an explicit, up-front peer option (NOT only a
      "liked none" escape). When the user takes it (or says "you decide / design it for me"), YOU select
      the best-fit library style from **the topic + content + audience** (brand colours fold in at the
      tailoring step) and **name it back** ("for a summer
      festival I'll go Memphis/pop"), or, for a distinctive scenario, give a richer **mood-led** prompt
      (scenario + energy + palette + "design a cohesive visual identity") instead of a named style — then
      generate and let them react at the hero checkpoint. **If they pick Auto up front, you may SKIP the
      HTML style gate entirely** and go straight to generate → the 🔴 hero checkpoint (don't make a
      delegating user wait on a picker they didn't want).
    - **"D — describe your own / provide a reference"** — synthesize a fresh token-set from their words /
      reference image / brand and **regenerate the HTML** so they still pick from something they can *see*.
  Auto is **not a blind commit**: every path — pick, auto, or own — resolves to a concrete look the user
  reacts to at the 🔴 hero checkpoint, which is the real gate in the default flow (a full per-deck
  "decide everything yourself / just show me the result" directive downgrades it to an FYI — post the
  renders and proceed; see SKILL.md "The per-deck AUTO WAIVER").
- **Vibe / mood (if describing your own)** — the aesthetic in words: energy (calm↔loud), era,
  references. Use this to pick/blend a library style or to author a fresh one.
- **Brand colours / must-haves** — any fixed colours, a logo, words that must appear.
- **Reference material — invite drop-ins.** Explicitly offer: *"drop in any reference images, a
  logo, a mood board, screenshots of a look you like, or a brand guide and I'll steer the
  generation by them."* Use provided references to anchor the style (and, if a logo/photo is
  given, place it natively, not regenerated). If the user frames a dropped-in example as
  **"mimic this"**, first ask Q4's intent question before generating — a Q4 mimic answer lands
  HERE on this branch, with the example as the anchor reference: **Mode A** — its style brief
  (`style-analysis.md`) seeds the token-set and hero prompt directly, steering the generation to
  faithfully clone its look (skip the library pick); **Mode B** — the chosen generated style sets
  palette/mood, and the example's 2–4 borrowed components/structure are recreated in the native
  helpers (the generated identity restyles them).

**Then TAILOR the chosen style to *this* deck before generating** — fold in the topic, the brand
colours, the energy, and anything from the reference materials. The library entry is the *starting
language, not a straitjacket*: customise its palette/motifs to fit, and blending two presets (or a
preset + a reference) is fine — just name what you're combining so the choice is legible to the user.

### 2 — Generate the template image(s)
Generate a **full-bleed, text-free** hero/divider illustration in the chosen style. *(Came through
the real-image style gate? The winner's gate image IS the hero — don't regenerate it; this step then
only adds the divider variant, if wanted, and the 🔴 interior plate below.)*
- **Tooling — auto-detect the source, no API key needed** (build the prompt with
  `scripts/image_prompts.py`; full guidance in `references/image-generation.md`). Use what's present,
  in order: **(1)** native imagegen when the host has it (inside Codex — use the agent tool call
  directly, free, no key); **(2)** else
  the **Codex CLI** `scripts/generate_images_codex.py --orientation landscape` if `codex` is installed
  (Codex/ChatGPT subscription, **no key** — shells `codex exec`, decodes the hosted image from the
  session rollout); **(3)** else, only as a fallback, the OpenAI API `scripts/generate_images_openai.py`
  with `OPENAI_API_KEY` — **metered, and gated: an available key is not consent. Ask before the first
  paid call (🔴 stop, not waived by an auto directive), and if the user declines, fall back to a
  non-generated look rather than spending** (the BILLING GATE in `image-generation.md`).
  **Don't prompt the user to choose or ask for a key when (1) or (2) is
  available — just use it and say which; the ask applies only to the paid rung.** Render at the deck's
  aspect (16:9 → e.g. `1536x864` / `2048x1152`). In Codex's native path, follow its save-path policy:
  generate first, then move/copy the selected output from `$CODEX_HOME/generated_images/...` into
  this deck's folder before referencing it in `style.py` or a build script.
- **Prompt craft:** describe the *style + motif vocabulary + palette*, the subject/scene, **"no
  text, no lettering, no logos"**, and **leave a calm, lower-contrast zone** (a corner/band)
  where the title will sit. Ask for the **signature motifs** explicitly (e.g. "scattered Memphis
  geometric shapes — zigzags, dots, triangles, squiggles, checkerboard — bold black outlines")
  so you can reproduce them natively later.
- **🔴 Title-over-hero legibility — prompting a calm zone is NECESSARY but NOT SUFFICIENT; you MUST
  back the text AND verify.** The model often ignores the calm-zone request and runs a decorative
  **frame line / ray / motif right through where the title lands** — and the build-time lint can't see
  it (it only checks text-on-text / off-canvas, never text-on-image-linework). So on EVERY hero/divider
  that carries text: (1) place a **scrim behind the whole text block** — a gradient (or frosted panel)
  strong enough that at the glyphs the effective background is dark/quiet enough for ≥4.5:1 (a corner
  scrim reaching **α ≈ 0.55–0.85** over light text is typical; a token 0.2 wash is not enough over a
  busy plate); (2) **in the render, look specifically at the title**: no image line/edge/motif crosses
  the glyphs, and every run (including a low-contrast **eyebrow/kicker** in gold/tint) clears the
  contrast floor — if a line still cuts the text or the eyebrow washes out, strengthen the scrim,
  move the text to a genuinely empty region, or lighten the run. Treat a title fighting the image's
  linework as a real defect, exactly like an overflow.
  **🔴 A translucent scrim DIMS a bright line but does NOT erase it** — a gold/teal Deco frame-line or
  a bright edge stays visible through a 0.5–0.7 wash and keeps cutting the glyphs. When the hero
  carries **framing / linework / high-detail exactly where the title lands** (common with Deco /
  bordered / ornamented styles), escalate from a scrim to a **near-opaque title panel** (a solid or
  α ≥ 0.88 block — a lower-third band or a corner card **anchored to and filling to the canvas edge**,
  never bleeding off-canvas, which the strict lint rejects) that fully COVERS the linework; verify the
  covered area is clean. And keep an **unmistakable gap between the title and its subtitle** (the rule/
  subtitle is a separate block, not touching the big title's baseline) — cramped title/subtitle
  spacing reads as an error even when nothing technically overlaps.
- Generate **1–2 plates**: a **hero** (cover) and, if the look differs, a **divider** variant.
- **Generate the interior shallow-background plate too — 🔴 MUST (see the construction model).**
  Alongside the hero, generate **one extra low-contrast background plate**: a **text-free, faint,
  evenly-toned, TOPIC-RELATED** version of the style (calm, low-saturation, no strong focal point,
  generous negative
  space) made to sit *behind* content on **every interior page**. Name the deck's own subject motifs
  in the prompt — the topical requirement from the construction model, not a generic texture — while
  prompting explicitly for low contrast
  and even tone ("soft, faded, low-contrast background of scattered faint <topic motifs — e.g.
  circuit nodes / botanical leaves / musical staves>, lots of calm negative space in the
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
- **Component treatments — GEOMETRY derived from the image, not defaulted.** Define the template's
  card / stat / emphasis-band / chip / title-chrome look as helpers, and set their geometry by
  READING four properties off the generated image:
  (1) **outline weight** — comic/hand-drawn → bold 2–3pt ink-coloured outlines on cards and chips;
  blueprint/technical → hairlines, some dashed; painterly → no outlines, shape by fill;
  (2) **corner language** — comic/soft-organic → rounded; pixel/brutalist → square, zero radius;
  one radius scale across ALL components (mixed corner languages are an existing critic flag);
  (3) **shadow/depth** — comic → hard offset shadows (`offset_shadow`, zero blur); soft-organic →
  diffuse or none; flat/minimal → none;
  (4) **fill flatness** — comic/pixel → flat fills, no gradients; painterly → soft tints; frosted
  glass only where imagery sits underneath.
  A COMIC identity, concretely: 2.5pt ink outlines + rounded corners + hard offset shadows + flat
  palette fills + speech-bubble/burst motif helpers sharing the same outline weight. **Echo, don't
  cosplay:** the plates carry the heavy style; components pick up the palette + these four
  properties — never painted mimicry of the artwork — and the floors never bend to style
  (contrast ≥4.5:1, text always native/editable, legibility before flavour). Component outlines/shadows are part of the CONTENT surface
  language, not chrome — the chrome budget still governs title furniture, rules and footers at
  every register.
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
- **Type register — derive it from the image's CHARACTER, never choose it independently.** A
  gorgeous plate with an off-register default face on top is the type-level version of the
  pasted-on card. Map the identity family to a register, then pick portable faces inside it
  (portability + CJK pairing: `references/multilingual.md`, `references/font-guidance.md` — a
  style-matched face must be install-safe or get a register-adjacent system fallback, flagged at
  hand-off):

  | Identity family | Latin register | CJK pairing note |
  |---|---|---|
  | Comic / hand-drawn / doodle | rounded humanist or comic-adjacent display (Comic Neue if installed → Trebuchet MS/Verdana fallback) | a rounded 圆体-class face if installed → Hiragino Sans GB fallback; never a brush Kai (reads formal, not playful) |
  | Blueprint / technical / terminal | technical sans + mono labels (Consolas/Menlo class) | Hiragino Sans GB · mono digits |
  | Ink-wash / brush / 东方 | serif Latin (Georgia class) | Kai/Song per `east-asian-aesthetic.md`; lining digits beside CJK |
  | Pixel / retro / arcade | geometric sans or mono, square terminals | Hiragino Sans GB; avoid rounded faces |
  | Painterly / organic / botanical | humanist serif or light humanist sans | Songti or Hiragino by warmth |
  | Editorial / magazine / collage | high-contrast serif display + grotesque body | Songti display + Hiragino body |
  | Corporate-clean / minimal | neo-grotesque (Helvetica Neue class) | Hiragino Sans GB |
  | Luxury / museum | serif display, generous tracking | Songti; thin rules |

  An identity OUTSIDE these families (cinematic-photoreal, memphis/pop, collage…) follows the
  same logic, not a dead-end: read the letterform character the image itself implies (what type
  would a poster in this world use?), pick the nearest register, and record the reasoning in the
  contract's type line — the table is a map, not a cage. On a CJK-only deck the Latin column
  still governs numerals and any Latin fragments.

  Set `deckkit.FONT`/`EAFONT` from the chosen pair; define `title_bar`/`footer` to the template's
  chrome in the same register.
- Put all of this in the deck's `style.py` (copy `references/examples/style_example.py` as the
  starting shape) — **and record the four-line IDENTITY-PROPAGATION CONTRACT in the Design plan**:
  `palette: extracted from hero` · `type: <register — faces + CJK pair>` · `geometry:
  <outline/corner/shadow/fill read off the image>` · `surface: <frosted / tint / outlined>`. These
  four lines accompany the hero + sample-content renders at the 🔴 hero checkpoint (or its
  auto-waiver FYI), so the user approves the whole SYSTEM — not just the pictures — and the critic
  judges the built deck against them.

### 4 — Render a sample and get feedback (hard gate)
Build **two** slides — the **cover** (hero image + native title/badges) and **one real content
slide** (native, using the derived components: a few cards + an emphasis band + motifs) — render
them, and show both. The content slide is essential: it proves the blocks actually fit.
> **🔴 CHECKPOINT** — show the generated template (hero + a sample content slide) and get the
> user's OK. Iterate on their feedback until they confirm. Only then proceed.
> *(Under a full per-deck auto directive this stop is posted as an FYI and you proceed.)*

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
- The look is decided → **skip the 3-direction gate** and any LOOK question; the rest of the
  normal interview still runs — purpose & audience & time, source material, language, AND Q4's
  density (text-per-point) and tone: those are content/register choices a generated visual
  identity does not decide (density stays an ALWAYS-surfaced choice per SKILL.md Q4).
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
  under Q1's registered templates). **Under a per-deck auto directive the hero checkpoint was an
  FYI, not a confirmation — defer the save to Step 6's save-this-look offer (explicit yes
  required); only a user-confirmed hero checkpoint earns the automatic save** (never an
  un-consented registry write).

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
- **Rhythm on this branch comes from IMAGERY STRENGTH, never a foreign canvas.** The generic
  "vary the canvas value on at least one beat" pressure (FLAT RHYTHM lint; rhythm-map guidance)
  does NOT license flipping one mid-deck slide to a different background colour — on a
  generated-identity deck, a lone flipped canvas abandons the plate and reads as an *error*, not
  a rhythm event (users call it out immediately). Make the beats by varying how strongly the
  generated imagery shows: faint plate on working slides ↔ full-strength hero imagery on the
  cover, dividers, and the closer. If you genuinely want a canvas value change, it must RECUR as
  a family (all section dividers dark, or dark bookends) — never exactly one interior slide
  (`ONE-OFF CANVAS FLIP` in lint_deck.py enforces this deterministically). Answer FLAT RHYTHM
  with the register exception line, not with a one-off flip.
- **Frosted blocks are a legibility TOOL, not the page format.** The frosted-panel treatment exists
  so text stays readable where the plate is busy — it is NOT an instruction to panel everything.
  On a calm, even plate, big type, hero numbers, chips, and diagrams can (and on ~1/3 of content
  slides SHOULD) sit directly on the canvas; reserve panels for dense mixed content. A deck where
  every element lives in a panel plus a bottom strip on every page reads as one template stamped
  nine times — the architecture-rotation rule (slide-design §4) applies fully on this branch.
- **Icons belong on this branch too** — the icon MUST (self-verify (g)) is not suspended by a
  generated identity: fetch one family (`scripts/icons.py`), recolor to the deck palette, and use
  glass/tile treatments so the glyphs sit inside the same frosted system as the panels.
- **The shallow background must stay BEHIND the content** — it's atmosphere, not a competing layer.
  If it darkens or busies the area under text, mute it harder (lighter tint, stronger scrim, fewer
  motifs); body text must clear 4.5:1 against whatever the background leaves under it. A subtle
  background that forces every text block onto its own opaque card has been made too strong. **But there is a FLOOR as well: the plate must stay SUBTLY VISIBLE** — a viewer should be able to *see* the body page is textured, not have to guess. Muting is one-directional pressure, so it's easy to over-scrim the plate into a flat near-white field that satisfies 'a plate on every page' in code yet reads as absent — the same failure as no plate at all. If you can't tell the plate is there at a glance, the scrim is too heavy: lift it until the hero's motif is faintly but genuinely perceptible, and recover text contrast with the frosted blocks rather than by erasing the plate.
- **Logo = the REAL mark, present where it belongs** — for a company/institution/product deck the
  logo appears on every page; when found, use the real asset **untouched** (image-generation.md's
  hierarchy), never a faked or recolored one; not found → a clean typographic wordmark flagged as a
  designer's stand-in (never a literal "logo here" string in a shipped deck). Either way the DESIGN
  checkpoint's `logo plan:` line carries its evidence token per the slide-design LOGO PRINCIPLE.
- **Generated real things must be right** — if the hero depicts real objects/places, the
  size/proportion/count/colour must be factually correct (the image-generation fidelity rule).
  Identity plates (hero / dividers / interior plate) are the REFERENT RULE's sanctioned carve — a
  place-anchored deck renders the real place as DECLARED STYLIZED ART in the chosen style, never as
  fake photography; the factual-rightness rule (size/proportion/count/colour) still applies to the
  stylized rendering.

## Checklist
- [ ] Mini-interview done (scenario; style offered as a choice — **best-fit library styles** +
      describe-own + reference drop-ins + **"let the image tool pick" (auto)**; brand colours).
- [ ] A style **chosen and tailored** to the scenario — a picked library style, an auto-picked one
      (named back to the user), or a fresh look from a reference — palette/motifs customised, not raw.
- [ ] Hero (and divider) generated **text-free**, in-style, with a **calm zone** for the title — **plus
      the 🔴 MUST interior shallow-background plate** (low-contrast, even-toned, **topic-related** — the
      deck's own subject motifs, never generic texture; skipped only for a
      deliberately minimal/flat style).
- [ ] `style.py` derived: palette **extracted from the image**, motif helpers, component helpers,
      fonts/chrome, a **`content_bg(slide)`** for the shallow interior background, and a
      **`brand(slide)`** logo helper if the deck is about a company/institution/product.
- [ ] Sample **cover + content slide** rendered and **confirmed by the user** (🔴 checkpoint).
- [ ] Direction gate **skipped**; rest of the interview (incl. density/tone) completed.
- [ ] Built: dividers use the image; content is native and **on-system** with the **GENERATED shallow-
      background plate on every interior page** (🔴 MUST — no flat single-colour or merely-gradient
      interior, except a deliberately minimal/flat style) + frosted blocks; the **real logo present and
      consistently placed** on every page if it's a company/institution/product deck; figures framed
      to sit on the template; legibility ≥ 4.5:1 everywhere.
- [ ] Where content names tools/entities/categories, a **palette-recolored icon family** is placed (`scripts/icons.py`; glass/tile treatments on-system) — or the one-clause waiver is recorded.
- [ ] **Architecture rotates** — takeaway slot varies (no bottom strip on every page) and ≥1/3 of protagonists sit direct-on-canvas on a calm plate.
- [ ] The interior plate is a **faint DERIVATIVE of the hero** (same motif/palette, not a generic texture) and stays **subtly visible** on every body page — not scrimmed into a flat near-white field.
- [ ] A **closing / ending page bookends the cover** — full-strength divider-style imagery with a native wrap-up (thank-you / recap / CTA / contact), so the deck doesn't stop on a body slide.
- [ ] Template **saved to the registry** for reuse.

## Style library — well-known starting styles (seed, then tailor)
Proven visual languages to seed the generation from — pick the **3 best-fit for the TOPIC + CONTENT,
deliberately diverse** (three different visual languages, never three moods of one),
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
- **Luxury dark** — hushed, premium, gallery-like. *Palette:* near-black + gold/champagne + one deep
  jewel tone. *Motifs:* thin gold rules, serif numerals, generous dark space. *Type:* high-contrast serif.
- **Dark tech / engineering** — command-deck confidence. *Palette:* near-black navy + 1–2 neon accents.
  *Motifs:* glowing nodes, thin connectors, grid ghosts, diagram islands. *Type:* heavy sans + mono chrome.

**Illustration & character** *(image-native — these only read in real generated imagery, never in a token mock)*
- **Manga / anime** — kinetic, expressive, story-driven. *Palette:* cel-shaded brights or B/W screentone.
  *Motifs:* speed lines, halftone screentone, panel frames, expressive skies. *Type:* bold condensed +
  a hand-lettered accent. Great for youth/community/launch energy.
- **Ukiyo-e / woodblock** — timeless, crafted, Japanese. *Palette:* indigo, vermilion, cream, seafoam.
  *Motifs:* flat colour planes, bold keylines, stylised waves/clouds, washi grain. *Type:* serif/brush accent.
- **Ink wash / 水墨** — contemplative, literati. *Palette:* ink blacks on paper + one vermilion seal-red.
  *Motifs:* brush strokes, mist gradients, negative space. *Type:* see `east-asian-aesthetic.md` (`ink_wash`).
- **Flat vector illustration** — friendly product/explainer. *Palette:* 4–6 cheerful mids on white.
  *Motifs:* geometric characters/scenes, simple shadows, spot illustrations. *Type:* rounded geometric sans.
- **Claymorphism / clay 3D** — tactile, warm, playful. *Palette:* soft pastels, cream bg. *Motifs:*
  squishy rounded 3D forms, soft double shadows, plasticine texture. *Type:* chunky rounded sans.
- **Isometric / low-poly 3D** — systems made charming. *Palette:* 2–3 hues + tints on light/dark.
  *Motifs:* isometric mini-worlds, faceted geometry, exploded diagrams. *Type:* clean sans/mono.
- **3D render / hyper-surreal** — glossy C4D-style hero objects, impossible-but-photoreal scenes.
  *Palette:* vivid on studio gradients. *Motifs:* floating objects, soft studio light, depth of field.
  *Type:* minimal sans (the image is the drama).

**Photo & layout-led**
- **Cinematic photographic** — full-bleed atmospheric photography/imagery + scrim + minimal type; the
  classic big-keynote look. *Palette:* drawn from the imagery + one accent. *Motifs:* edge-to-edge
  plates, gradient scrims, one bold line per slide. *Type:* large clean sans. (Duotone-treat photos
  via `image_fx.py` to keep them on-palette.)
- **Bento grid** — modular tile mosaic (the Apple-keynote / bentoslides look). *Palette:* one bg +
  2–3 tile tints. *Motifs:* rounded tiles of mixed spans, one stat/visual per tile, generous gaps.
  *Type:* bold geometric sans. Great for feature/summary/dashboard-flavoured decks.
- **Neo-brutalism** — the web-native, friendlier brutalism. *Palette:* off-white + 1–2 loud accents
  (neon yellow/pink). *Motifs:* thick black borders, hard offset shadows, raw chunky buttons/chips,
  stark grids. *Type:* heavy grotesque + mono.
- **Neumorphism / soft UI** — quiet, tactile monochrome. *Palette:* one soft grey/tinted bg.
  *Motifs:* extruded soft-shadow cards, pillowy depth, minimal colour. *Type:* light rounded sans.

**Collage & nostalgia**
- **Collage / scrapbook** — eclectic, human, zine-energy. *Palette:* paper neutrals + punchy accents.
  *Motifs:* photo cutouts, torn edges, tape, polaroids, handwritten notes, mixed ephemera. *Type:*
  serif clippings + hand-written accent.
- **Papercut / paper craft** — layered, dimensional, warm. *Palette:* 3–5 saturated paper tones.
  *Motifs:* layered cut-paper depth, soft drop shadows between layers. *Type:* rounded sans.
- **Retro-futurism / Space Age** — optimistic mid-century tomorrow. *Palette:* atomic orange/teal/cream.
  *Motifs:* starbursts, ringed planets, streamlined forms, boomerang shapes. *Type:* retro geometric sans.
- **Art Nouveau** — organic, ornamental, whiplash curves. *Palette:* muted golds/greens/creams.
  *Motifs:* flowing botanical frames, stylised figures, decorative borders. *Type:* flowing display serif.
- **Pixel art / 8-bit** — playful dev/gaming nostalgia. *Palette:* limited console palette. *Motifs:*
  pixel sprites, dithering, scanline CRT hints. *Type:* pixel/mono.
- **70s groovy / psychedelic** — warm, wavy, optimistic. *Palette:* mustard/burnt-orange/olive/cream.
  *Motifs:* wavy stripes, arches, suns, bubbly curves. *Type:* bubbly rounded display serif.
- **Modern heritage / vintage print** — old-world credibility, new restraint. *Palette:* cream/ink +
  oxblood or forest. *Motifs:* crests, engraving-style linework, ornamental rules, letterpress grain.
  *Type:* classic serif + small caps.
- **Organic modern / mid-century** — warm, crafted, architectural. *Palette:* terracotta/sage/bone/
  walnut. *Motifs:* arches, rounded blobs, linen/paper grain, simple botanical or furniture linework.
  *Type:* humanist serif + sans. (Studio credentials, architecture/interior, craft brands.)
- **Chalkboard / blackboard** — the teaching register. *Palette:* deep slate/green board + chalk
  white + one pastel chalk accent. *Motifs:* hand-chalked rules/arrows/diagrams, dust texture.
  *Type:* chalk hand + clean sans. (Lectures, workshops, explainers.)
- **Maximalist pattern-clash** — loud, dense, fashion-editorial. *Palette:* many saturated hues,
  clashing on purpose. *Motifs:* layered patterns, oversized type over imagery, stickers/badges.
  *Type:* mixed display weights. (Use with discipline — legibility guardrails below apply doubly.)
- **Line art / monoline** — elegant single-weight economy. *Palette:* ink on paper + one accent.
  *Motifs:* continuous-line illustrations, thin geometric frames, tiny filled accents. *Type:* light
  sans with generous tracking.

> These are *starting points*, not a closed list — and the gate's job is matching a style to the
> TOPIC, so range across families (a fintech readout, a children's charity, and a robotics lab talk
> should surface completely different candidate sets). The user's own reference, brand, or a described
> look always outranks a preset; a preset just gives the image tool and the native build a strong,
> coherent target instead of a cold start.
