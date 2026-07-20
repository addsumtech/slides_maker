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

## Table of contents
- Decide by taste and purpose — not by a rule or a quota
- When to use image generation
- Place plates consistently — and a content plate is NOT a header
- Real brand / product assets come first — never fill with a generic stand-in
- Sourced real imagery — the REFERENT RULE (does the subject actually exist?)
- Planning workflow
- Generating the images — auto-detect the source (no API key needed)
- Real subjects must be factually right
- Prompt rules
- Verification

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
And when the slide's title or source language is **figurative** (a metaphor, an idiom, a rhetorical
image), the default is to **resolve it to the UNDERLYING concept first** — this resolution happens
BEFORE the referent classification below, and the resolved concept gets a *native* visualization of
the idea (an image only if the resolved concept is generic-concrete per the referent table) — a
"电锯切西瓜"-style phrase gets a visualization of the disproportionate-tool-for-the-task idea, not a
chainsaw and a watermelon. A literal rendering of the metaphor is legitimate only as a recorded
named deviation or an explicit user request (a visual-pun/comic register). The referent rule's
stylized escape applies to real subjects the slide is ABOUT, not to metaphor vehicles.

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
with a generated look-alike or a placeholder that pretends to be the brand, and **never ship literal
placeholder text ("logo goes here") on a slide**: that text IS the meta-annotation PRE-FLIGHT 8 and
the critic treat as a blocker. The honest fallbacks are the designed wordmark (flagged) or asking
the user; an invented brand asset is a fidelity violation (it
misstates a real thing) and reads as fake instantly. This complements the rule above: generated
imagery is for *atmosphere/concept*, never for a real identity that should be shown as-is.

### Logo / brand mark — its own hierarchy (a typographic stand-in is honest; a fake replica is not)
A logo has one rung the other assets don't: a **typographic** stand-in is an honest, legitimate choice
where a fabricated product render never is. Source it in order, stopping at the first you can get:

1. the **real logo** the content-planner's web-search found (or the user's / a clearly-official asset) — always first;
2. **a clean designed typographic WORDMARK / monogram** in the deck's own type — **the DEFAULT when the
   real logo wasn't found**, legitimate and honest **only when clearly flagged as a non-official
   designer's stand-in**; surface it at the **DESIGN checkpoint** for the user to confirm or override;
3. **NEVER a fabricated fake of a real entity's official logo** — an invented mark passed off as the
   real thing is a fidelity violation (it misstates a real thing) and reads as fake instantly.

**Minimal wordmark recipe — keep it restrained:** set the entity's **name in the deck's DISPLAY face** (a CJK name automatically takes the EA display face — `deckkit.wordmark` is CJK-aware, so a Chinese entity name never ships as tofu),
optionally with a **simple monogram** (its initial in a disc / square) or a thin rule / dot separator, in
the **deck palette** — nothing more. A wordmark is type done well, not an illustration.

**Fidelity guard:** designing a mark is fully appropriate for the user's **OWN** product or a **new /
fictional** one with no official logo; for **another** real entity, the real logo stays real or the gap is
flagged as an open question — you never invent its official mark. (This is the honest counterpart to
"STOP and ask": a *product render / UI screenshot* of a real other entity has no typographic stand-in, so
ask; a *logo* has a clearly-labelled wordmark as its sanctioned default.)

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
above: the real mark or the flagged designed wordmark, never a faked one.

## Sourced real imagery — the REFERENT RULE (does the subject actually exist?)

Before generating ANY content image, classify the slide subject's **referent** — the image *source*
follows it. This is why "can we put an image here?" is the wrong first question; the right one is
"does this subject exist in the world, and if so, why would we show a synthetic version of it?"

| Referent | Examples | Image source |
|---|---|---|
| **Real & specific** | a named city / landmark / route, a real product or device, a real person, a historical event or artifact, a specific building / campus | **REAL photo** — license-clear sourced (pipeline below), official press asset, or the user's own file. A generated image **claiming photographic reality** of it is a *fidelity bug* (a generated "Amsterdam canal" with the wrong architecture); a **plainly stylized illustration** in the deck's declared art-direction (watercolour travel-poster register, a Q1=d identity plate) is a legitimate *taste* choice when recorded as a named deviation or user request — the escape is valid only when the deck's ONE recorded art-direction line itself declares a stylized plate register (a per-image "stylized" declaration inside an otherwise photographic/realistic register is off-contract), and under a per-deck auto waiver real-and-specific subjects DEFAULT to sourced: the stylized deviation needs an explicit user request or the declared stylized register |
| **Generic-concrete** | "a warehouse", "a robot arm", "a classroom", "a market street" — no particular one | **Generation is fine** (often better — art-directable to the palette); a sourced photo also works |
| **Abstract** | strategy, finance, algorithms, org design | **No photographic supplement** — native diagrams / charts / icons carry it; imagery appears only as cover/divider mood, if at all |

**Scope + tie-break:** the rule governs **per-slide CONTENT images** — plates that depict a slide's
subject as evidence or atmosphere. It does NOT govern the generated-template branch's stylized
identity plates (hero / dividers / interior plate — `references/generated-template.md` owns those,
and a place-anchored Q1=d deck renders the place as declared stylized art, not fake photography) or
cover/divider *mood* imagery — the mood exemption relaxes only the SOURCING obligation, never the
fidelity bar: mood imagery of a real-and-specific subject is still sourced or plainly stylized;
generation claiming photographic reality of a real referent is a fidelity bug anywhere in the deck,
cover included. Classify the **image's depicted subject, not the slide topic** — a
Shanghai-skyline mood image on a finance slide is still a real-&-specific image; and a generic scene
that merely *evokes* an entity (an office vibe, a lab atmosphere) is generic-concrete unless the
deck presents it as THAT entity's actual premises. **Real living people:** a CC license clears
copyright, not personality/publicity rights — for a commercial deck prefer official press/headshot
assets or user-supplied photos.

**The sourced-photo pipeline (real-referent subjects):**
1. **Search license-clear sources only**: Wikimedia Commons and Openverse (both keyless APIs,
   CC-licensed, captioned), official press kits / brand pages, or the user's own material. Never
   grab from arbitrary image-search results — provenance and license unknown.
2. **Verify the subject, that the file is WATERMARK-FREE, and that it is AESTHETICALLY USABLE**: the
   file's caption / description / geotag / Commons category must confirm it shows the *claimed*
   subject — a mislabeled photo is the photographic version of an invented number, and the critic's
   fidelity lens checks it. View the downloaded file for watermarks, stock-preview overlays,
   photographer stamps, or site logos: a watermark is a **licensing tell** (it usually marks an
   unlicensed preview), so a watermarked file is **rejected** — never cropped, blurred, or inpainted
   to hide the mark (that is license circumvention, not cleanup); find a clean file or fall back to a
   `searched, none found → …` rung.
   **Then VET IT AESTHETICALLY — a subject-correct photo is not automatically a usable one, and you
   MUST look before you place it.** Reject a file that is *unrepresentative or unflattering*: a
   landmark **mid-construction / scaffolded / with cranes**, a dish that looks unappetising or is the
   wrong preparation, or any **blurry / low-res / badly-lit / cluttered / awkwardly-cropped /
   snapshot-grade** shot, or one whose real subject is buried or tiny in frame. A technically-correct
   but ugly photo **fails** — it misrepresents the place as much as a wrong caption would, and "it *is*
   the right subject" is not a defence. Try other candidates first; **if no license-clear photo of
   sufficient quality exists, GENERATE a declared-stylized illustration of the subject instead** (the
   `searched, found but low-quality → generated, flagged illustrative` rung below). A beautiful,
   accurate illustration in the deck's own art-direction beats an ugly real photo, and — unlike a fake
   *photographic* claim of a real subject — a plainly-declared illustration is on-contract. (A
   comparison of iconic real objects — building heights, product sizes — is often served best by an
   exact native chart *plus* a clean generated illustration of the objects, not a generic photo.)
3. **Record the license**: CC0 / CC BY / CC BY-SA / press-kit terms; attribution-required licenses
   get a credit (small mute caption at the image, or one credits line on the sources page).
4. **Treat to the palette** so mixed sources read as one deck: duotone/tint to the deck palette,
   consistent crop ratios, scrims under any text-over-photo (the contrast floor still applies).
5. **Evidence token (the gate — THIS list is the authoritative grammar; other files point here):**
   every image row in the plan / checkpoint opt-in list states its source class:
   - `sourced — <origin> (<license>)` — a found license-clear photo;
   - `provided — user (own material)` — the user's own file (no license interrogation);
   - `generated — <tool>` — a generated plate (generic-concrete subject, or declared stylized
     illustration of a real one — say which);
   - `searched, none found → generated, flagged illustrative` — the not-found rung: no license-clear
     photo exists (obscure place, private premises, pre-photography history, unreachable sources) →
     generate, clearly framed as illustration, never as photographic evidence;
   - `searched, found but low-quality → generated, flagged illustrative` — the quality rung: a
     license-clear photo exists but every candidate is unrepresentative/ugly (construction, poor shot,
     wrong preparation) → generate a declared-stylized illustration in the deck's art-direction
     instead (the aesthetic gate in step 2);
   - `searched, none found → native form` — the other sanctioned exit: drop the photo, let a map /
     diagram / native form carry the slide.
   A `searched, none found` rung must NAME the origins tried — write it
   `searched (Commons, Openverse[, press kit]), none found → …`; a bare rung with no named origins
   is incomplete, the same clause pattern as the logo token.
   A bare filename with no token is an **incomplete plan**, same pattern as the logo-plan token.
   (Pre-photography events can also use Commons artwork/artifact photos; the user's OWN unreleased
   product follows the logo table's own-product logic — an honest flagged stand-in.)

**Who does what:** the slide-design agent PLANS each row (subject + intended source class) — it does
not fetch; the **main loop** runs the Commons/Openverse/press-kit search and fills `<origin>
(<license>)` into the checkpoint artifact before presenting it (exactly how the logo evidence line
is assembled) — and records each found photo's **direct file URL** into the asset spec handed to
asset-prep (or keeps it for itself on small inline decks where no asset-prep runs); the
**asset-prep executor** downloads, subject-checks, and palette-treats after
design approval.

**The dose rule is unchanged — only the PRESSURE inverts on photo-friendly topics:** on a travel /
city / place-anchored deck the temptation flips from too-few earned images to wall-to-wall photos;
the opt-in discipline (only the slides that genuinely earn one) and balanced fullness still rule,
with native maps, routes, and cost tables doing the informational work while photos carry the few
atmosphere beats that deserve them.

## Planning workflow

1. During Step 2 (the slide-design agent's design plan), decide each slide's visual role: source figure, deterministic chart,
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

**What this means in Claude Code specifically** (the most common non-Codex host): CC has no native
image tool, so rung 2 *is* the path — and it is **free on the user's Codex subscription**, needing
`codex login` exactly once. The generated-template branch is therefore fully available in CC; it is
not a degraded or paid experience. It degrades only if `codex` is absent, and then the correct move
is `codex login` (free) — **not** a silent step down to the metered rung 3 below.

**3 · OpenAI API key — a PAID fallback, and the one rung that must be ASKED FOR.** Do **not**
request a key when native imagegen or `codex` is present.

> **🔴 BILLING GATE — the single exception to "detection-first, never block."** Rungs 1 and 2 are
> covered by the user's existing subscription and cost nothing per image, so they are used silently.
> Rung 3 is **metered: every image is real money on the user's card.** Therefore:
> - **A present `OPENAI_API_KEY` is NOT consent.** A key exported in the environment (or sitting in a
>   dotfile) means the path is *possible*, not that spending was *authorised*. Detection-first stops
>   at rung 2.
> - **Ask before the first paid call, every deck.** State plainly that this path bills per image, how
>   many images the plan needs (a generated template is typically 3–4; a style gate adds ~3), and that
>   `codex login` is a free alternative. Then wait — this is a 🔴 stop, and it is NOT waived by a
>   per-deck auto directive, which delegates *preferences*, never the user's money.
> - **If the user declines or does not answer, do not spend.** Fall back to a non-generated route —
>   branch (c) "design a clean one", a native `backdrop_motif` texture, or sourced Commons imagery —
>   and say which you used. A deck that ships on a clean native look is a fine outcome; an unexpected
>   bill is not.
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

> **Detection-first for the FREE rungs; ask before the paid one.** Pick native tool call → Codex CLI
> by what's available, proceed, and tell the user which you used (one line) — never block on a choice
> when a *free* working path is already present. **Rung 3 is different:** an available API key does
> not authorise spending, so when neither free rung exists, point the user to `codex login` (free)
> and ask before any metered call — see the billing gate above.

Do not paste API keys into prompts, slide text, source files, or manifests. Keep any key in the
environment (`OPENAI_API_KEY`). The native and Codex paths need no key.

## Real subjects must be factually right

**Scope: this section governs GENERIC-CONCRETE real things (kinds of things — "a robot arm", "a
container ship"), where generation is sanctioned. A real-AND-SPECIFIC referent (a named place, a
real product, a real person) goes to the REFERENT RULE above and gets a sourced photo — or a
declared stylized illustration, never generation passed off as photographic reality.**

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
