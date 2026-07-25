# Interview protocol

## Step 0 — personalization, Q1 (template), Q2 (purpose/venue), Q3 (source material)

**Personalize options only from THIS user's own footprint — never a hardcoded or guessed
domain — and roll past work up into ONE option, drilling in only on pick (Q1's two-stage
pattern), so personalization never crowds out the general choices.** Any *suggestions* you pre-fill into a question — candidate topics, example
subjects, registered templates — must come from what this user has actually given you:
materials they provided (now or in a past session) or their saved registry / profile /
memory. In Codex, prefer the registry root `~/.codex/slide-templates/`; in Claude Code,
prefer `~/.claude/slide-templates/`. If only one exists, use it. **Read `taste.md` at that
same registry root in the same pass** — the user's portable taste profile (schema +
read/write protocol: `references/user-taste.md`): its DIALS/NO-GOs seed *delegated* picks
under an auto directive, and its LOOK HISTORY supplies the substance of the two-stage
rolled-up history options below — never new option shapes, never an auto-lock. **Precedence
(🔴 MUST): current request > this interview's answers > `taste.md`** — the profile seeds
defaults and options only and never overrides an explicit answer or checkpoint decision,
because a memory that outranks the user's live words is a cage *(gate: the Design plan's
required `taste profile:` line records what was applied, so an override is visible)*. A
missing or empty `taste.md` is **silently skipped**. A **brand-new user has no footprint**, so do NOT seed a specific domain (e.g.
don't offer "MRI reconstruction" or any field as a topic just because some *past* deck
used it) or a prior user's branding — ask the subject **openly** (a genuinely open-ended
topic is the one place free text beats options) and offer only the generic template/look
choices: "provide a template", "design a clean one", and, when a more vivid custom identity
would fit, "generate a template with an image tool". Personalizing from a *returning* user's
own materials is good and encouraged; assuming a domain for someone who gave you nothing is
the failure to avoid.
**The TWO-STAGE rule governs past-work personalization in EVERY question, not just templates:**
whatever the question, history enters as **ONE rolled-up option beside the always-present general
choices**, and the specific past items are listed only in a follow-up if the user picks it.
Instances — **Q1 template:** "one of your saved templates (N)" (worked mechanics in Q1 below) ·
**topic/subject:** a returning user with known past projects gets ONE "continue one of my previous
topics" option beside the open free-text ask — never their domains enumerated as competing options ·
**Q4 style:** ONE "like one of my previous decks" option beside the generic density/tone choices,
expanding to named past looks on pick — the named looks come from `taste.md`'s LOOK HISTORY
(`— praised` lines first) plus the registered templates (`references/user-taste.md`) · same shape
for any other history (past purposes, prior venues). Marking a *general* option "(Recommended)" is fine and unaffected — the rule bounds how
PAST ITEMS enter, so they never crowd generic paths out of a bounded-option UI.

**Scale the interview to the ask:** a full deck needs
all four; a genuinely tiny ask (a single slide, a quick infographic) still needs purpose
and content confirmed, but you may collapse template/style to a sensible default *stated
in one line* ("I'll do a clean minimal look — say if you have a template") rather than a
full prompt. Scaling ≠ skipping — never infer purpose or content. Some answers trigger a quick follow-up *after* the
batch: *a conference talk* → ask which venue, then research it; *a new template* → they
hand over the file; *"design a clean one" (no template)* → run the **direction gate**
(DEFAULT on this branch — see Q1's design-one branch for the named skip carves; a Q4 Mode-A
mimic example decides the look and skips it) — show **4** rendered style directions to pick
from before the full build (3 best-fit REAL-DNA presets + 1 pure colour-scheme direction —
see Q1(c)); *"generate a template with an image tool"* → run the mini-interview + generation
+ feedback loop in `references/generated-template.md` (its style gate shows **3** best-fit
image-backed styles), then **skip the direction gate** (the look is already decided).
**The count rule, by branch: no image tool → 4 offered; with image tool → 3 offered.** The
four template choices:

1. **Template / brand.** First **check this user's registered templates** — the
   host-appropriate registry (`~/.codex/slide-templates/` in Codex, `~/.claude/slide-templates/`
   in Claude Code; if only one exists, use it). Each subfolder is one template they've used before,
   with a `profile.md`.
   **⚠️ WHENEVER the template question is asked, it MUST present ALL FOUR standard choices — do not
   silently drop one (especially the image-tool option, which is easy to forget). The question itself
   may be skipped only per the named carves: the current request already answers Q1, or the tiny-ask
   scale-down (default stated in one line) — and on the redesign path R0's keep/redesign answer
   REPLACES this question (on "redesign the look" ask it as the follow-up — see
   `references/redesign-existing-deck.md`):**
   **(a)** *"one of your saved templates (N registered)"* — the registry **rolled up as ONE option**
   · **(b)** *"a new template (I'll provide one)"* · **(c)** *"design a clean one"* · **(d)**
   *"generate a template with an image tool"* (a bespoke generated visual identity).
   **🔴 Before offering (d), PROBE that a free image path exists** — inside Codex the native imagegen
   tool counts; anywhere else (Claude Code included) run `command -v codex`. This costs one shell call
   and prevents the one dead end in this question: a user picks (d), the whole look is planned around
   generated imagery, and only at generation time does it emerge that nothing can generate. If no free
   path is present, still offer (d) but name its one-time prerequisite in the option itself —
   *"generate a template with an image tool (needs `codex login` once — free on your subscription)"* —
   so the setup cost is visible **before** the choice, not after. Never silently substitute a paid
   path for the missing free one; see the billing gate in `references/image-generation.md`.
   **Past work rolls up; general choices always stay.** Never enumerate the saved templates in the
   first question — a returning user's registry (which can hold many) would crowd the general
   choices out of a bounded-option UI, and the generic paths must stay visible on every deck. If the
   user picks (a), ask a quick FOLLOW-UP listing the registered templates by name (+ a one-clause
   hint each from `profile.md`) — with many, the few most recently used / best-fit first plus "show
   the rest". Carve: exactly ONE registered template may be inlined directly in place of the
   rolled-up option (no follow-up needed); an empty registry drops (a) entirely (brand-new user).
   (This instantiates the two-stage personalization rule above — the same shape applies to topic,
   style, and every other history-seeded question.) Then:
   - *A registered template* → build on it using its saved `profile.md` (step 3).
   - *A new template* → they give a `.pptx`/brand; build on it, AND after profiling it
     (step 3) **save a new subfolder to the active template registry** (its
     `profile.md`) so it becomes a remembered choice next time. The registry **grows
     through conversation.**
   - *Design a clean one* → build from preferences (brand colour/logo? formality?),
     and **shape the look to the chosen purpose** (step 3 / `references/design-by-purpose.md`)
     rather than always shipping the same default blue — a defense, an exec readout,
     and a lecture should not look alike.
     **Because the look is entirely yours to invent here, the direction gate RUNS BY
     DEFAULT on this branch — a 🔴 checkpoint-grade step, not an optional offer.** This is
     the one branch where preference, not just quality, is unresolved; history shows an
     "offer" gets skipped under momentum (a whole deck shipped without the user ever seeing
     a choice of looks), so the gate is the default and skipping is the exception. Named
     carves (skip ONLY when one applies, and say so in one clause at the design checkpoint):
     the user explicitly says "just design one and go / 你定"; a Q4 Mode-A mimic example
     decides the look; the deck reuses a registered template; or a tiny-ask (1–2 slide)
     edit. Under a full per-deck AUTO WAIVER, still GENERATE the four directions, auto-pick
     the best fit, and post the rendered images + pick as the FYI (mirror of the Q1(d)
     image-tool hero checkpoint) — the waiver removes the stop, never the artifact.
     - *Running the gate* → run **Gate A** of `references/collaborative-mode.md`. **The directions
       are REAL STYLES — a named preset OR a bespoke register with its own motif — never three shades
       of one palette.** ("Synthesised" is not the enemy; a *motif-less colourway* is. A bespoke
       register you invent for this content is a real style and a first-class peer of a preset — often
       the more daring answer, see the launchpad note below.) Pick the **3 best-fit design languages** for
       THIS topic/audience — presets from the 18-preset library (read each preset's `when` field in
       `scripts/presets.py` / `references/design-gallery.md`; e.g. a technical talk → blueprint /
       dark_tech / swiss, a culture deck → memphis / risograph / editorial_paper, a Chinese-heritage
       deck → ink_wash / eastern_traditional / museum_memorial), then
       **`archetypes_html.preset_directions([names])`** turns them into direction tokens that carry
       each preset's real **DNA** (its signature motif — Swiss's ghost numeral, Memphis's scattered
       shapes, blueprint's schematic grid, ink_wash's seal chop), rendered by
       `scripts/archetypes_html.py` into **ONE self-contained HTML page** showing them in the
       **same** representative slides (cover / points+callout / diagram / data). This is the fix for
       "the 3 options were just different colours": a preset is a whole visual language, and the
       preview now SHOWS it — **and the DNA runs through every preview slide, not just the cover**
       (the ambient register signature; `_dna_ambient`), so the user sees a style that carries the
       whole deck.
       - 🔴 **On this no-image-tool branch, offer FOUR rendered directions, not three:** the 3
         best-fit DNA presets (A/B/C) **plus a 4th "colour-scheme" direction (D)** — one tasteful
         palette+type combination for THIS topic with **no motif**, the classic clean look (this is
         itself a legitimate style; a user asked for it to stay on the menu). Build all four in one
         call: `preset_directions(["p1","p2","p3", {colour_token}])` — a **dict** is passed through
         verbatim as a no-`dna` colour direction (name it e.g. *"Signal — pure palette + type"*).
         The HTML labels A–D as the four options and **E — describe your own** as the fifth slot (the
         own-letter is dynamic, so no collision). *(With an image tool it's the OTHER branch — Q1(d)'s
         style gate — which stays at 3.)*
       - **Presets are the FLOOR you beat, not the menu you satisfy — PREFER a bespoke register when
         the content has one.** Any of A–C may be a **bespoke synthesised direction** (a dict in the
         `preset_directions` list, carrying its OWN motif so it renders real DNA) — and when THIS
         content has a distinctive visual world of its own, *prefer* inventing that register over a
         merely-adequate preset. A bespoke register with a named motif + palette + type + its own guard
         + item-(q) all-pages carry is as legitimate as any preset and usually the bolder pick. Weigh it
         on every design-clean deck — it is a default consideration, not a fallback for "a topic no
         preset fits". The library raises the floor; your job is still to beat it.
       - 🔴 **DIVERGENCE IS A PAIRWISE RULE, NOT AN EXHORTATION: any two directions must differ on
         ≥2 of four axes — {palette mood · type attitude · density/scale · COMPOSITION ENVELOPE}.**
         "Distinct light/dark, warm/cool, serif/sans" describes *knobs*; a dark version and a light
         version of one layout are two coats on one design. The composition axis is the token set's
         `cover` (`centred | low-left | split-vertical | full-bleed-type`) and `skeleton`
         (`statement | split | island | band | rail`) — **where the ink sits**, which is what a
         viewer reads first with the page squinted. *(Measured motivation: a real delivered deck had
         8/12 pages on one composition signature and 55/66 page pairs under the "same shape" line —
         while its FORMS varied correctly. Composition was never chosen, only defaulted.)*
       - **LOCK-AND-REDIRECT.** When the user or a brand fixes an axis (a mandated accent, "match our
         corporate look", a Q4 mimic), that axis LEAVES the divergence set and the ≥2 rule re-applies
         to the ones that remain. A constraint relocates variance; it never licenses convergence.
       - 🔴 **Run the mechanical check before you post the link:**
         `python scripts/directions_diversity.py directions.json`. It scores four axes — **palette
         mood** (a light/dark flip counts as a palette divergence, so mode is folded in) · **type
         pairing** · **density** · **composition** — and flags any pair matching on ≥3 of the 4. **Exit 2 is
         not an auto-kill** — REDIVERGE the flagged pair, or keep it and record the reason on the
         `direction gate:` line ("brand-locked accent — divergence moved to composition + type").
         The check exists because the agent that writes the directions is the same agent that
         judges whether they differ; only an outside measurement catches several skins of one idea. **Hand the user the single `file://…
       directions.html` link** to open in a browser, review side-by-side, and pick from — no
       local pptx samples. Collect the pick + knobs. Present the pick as **A / B / C / D (the four
       rendered directions) plus a final "E — describe your own" option**: if the user picks E, they
       *type the look they have in mind* (a reference, a brand, a mood, a constraint) and you
       **synthesize a new direction from that description** — regenerate the HTML link and show it
       alongside (iterate until they consent), rather than forcing one of your four guesses. The four
       are only your opening proposals; the author's own intention always outranks them. **The pick
       fixes the REGISTER (palette · type · composition · the interior register signature), NOT the
       daring — it is a launchpad, not a finished design.** "Picked a preset → rendered the preset" does
       not discharge the design step: the boldness/signature-move gate still runs in full and the deck
       still owes one `signature move` this preset would not have made (`agents/slide-design.md` §1,
       self-verify (h)/(k); the critic's distinctiveness axis flags a faithful-preset-with-no-bespoke-move
       as template-with-extra-steps). On the
       pick, the chosen token-set becomes the deck's `style.py` **including its composition — the
       `cover` token is BUILT as the cover's actual layout, and the `skeleton` token becomes the
       rhythm map's plurality skeleton (`collaborative-mode.md` Gate A step 7; a style.py that
       keeps the hexes and drops the composition has discarded half the pick)** — then **render ONE
       real slide in it to confirm fidelity** before building. **Once they pick, delete the throwaway
       `_directions/` preview files + rejected token-sets** (keep only the chosen style), then
       build the full deck in it — don't leave demo files littering Downloads.
     - *Picks design-one (via a named carve)* → build a single look shaped to purpose, as above.
     The gate is the DEFAULT on this branch, skipped only via the named carves above — a
     brand-new from-scratch deck is exactly when showing options pays off; "just design one
     and go" remains one click away, but it is the user's exception, never your shortcut.
   - *Generate a template with an image tool* → **a bespoke visual identity** — a styled, **text-free**
     hero/divider illustration, then reproduced natively so every content block fits it — for a vivid,
     designed deck (launch, event, brand, playful pitch) where a clean default isn't enough. **Follow
     `references/generated-template.md`**: a mini-interview *now* (scenario/topic first — brand colours
     fold into tailoring; **pick the 3 best-fit, deliberately DIVERSE styles for the TOPIC + CONTENT
     from its Style library** (different visual languages — e.g. Swiss vs Manga vs Glassmorphism — never
     colour-variations of one look), **GENERATE 1 real template image per candidate style (2 for the
     front-runner) on this topic, and show them in ONE HTML gallery — the "style gate"** (one `file://`
     link; the winner's image is reused as the deck's hero, so the cost is ~3–4 images; native
     `archetypes_html.py` mockups are only the no-image-tool fallback), then the user picks. **Offer
     these as first-class, peer choices in the prompt — A / B / C (a shown style) · "describe your own /
     a reference" · and "Auto — let me pick the best-fit and just go" (an explicit option, not a
     fallback).** On Auto (or "you decide"), YOU select & name the topic-best-fit style and may SKIP the
     HTML gate, going straight to generate → the 🔴 hero checkpoint (still the real gate in the default
     flow; a full per-deck "decide everything yourself" directive downgrades it to a posted FYI like the
     other approval stops — "never a blind commit" is met by posting the renders, not by waiting)) →
     generate the text-free hero with a calm title zone (**no key** — native imagegen in Codex, else
     `generate_images_codex.py`; see `image-generation.md`) → **derive a matching `style.py`** (palette
     via `deckkit.palette_from_image`, motif + component helpers, so native blocks match) → render the
     cover + one real content slide and gate it:
     > **🔴 CHECKPOINT** — show the hero + a sample content slide; iterate until the user confirms.
     > *(A request to change the **atmosphere/mood/style** ⇒ RE-generate the imagery to embody it — new
     > subject/composition/lighting/motifs — then re-derive `style.py`; don't just recolour the old plate.
     > A minor palette/contrast tweak is a `style.py`-only change. See `references/generated-template.md`.)*
     Then **the look is decided — SKIP the direction gate**, finish the interview normally, and build
     (image cover/dividers with native title on top; content built natively in `style.py`. **🔴 MUST
     (this generated/image-tool template branch ONLY — not provided-template or "design a clean one" decks),
     not a default: also GENERATE a faint, TOPIC-RELATED interior-background PLATE (same style, the
     deck's own subject-matter motifs — never generic texture) and place it (lightly scrimmed) on
     every interior page — the shallow background is itself a generated image, not a flat/native fill —
     AND make content blocks FROSTED / semi-transparent (~30–45% see-through, α≈0.55–0.72), never flat
     opaque panels. Only the end pages — the cover, the section dividers, AND a closing/ending page that bookends the cover — carry full-strength imagery; interior
     pages get the faint plate.** Carve: a deliberately minimal/flat style (Swiss/Scandinavian/Brutalist)
     may use a faint native texture instead. Text kept ≥4.5:1; see `generated-template.md`); save the
     confirmed template to the registry.

   **Never hardcode or assume a specific institution's template.** This skill ships
   to anyone: a brand-new user has an *empty* registry, so they see only generic choices
   ("provide one", "design a clean one", and optionally "generate a template with an image
   tool") — no prior user's branding is ever offered to them.

2. **Purpose & audience.** "What's this deck for, and who's the audience?" Offer the
   common cases since the bar differs sharply between them:
   *research meeting with a supervisor* · *work status update to a manager/boss* ·
   *academic conference talk* · *academic job talk / faculty interview* ·
   *company/stakeholder readout* · *product description / pitch* · *thesis defense* ·
   *teaching* · *webinar / online presentation*. Get the **time budget**. This selects
   the critic's rubric (`references/review-rubrics.md`).
   - **Also capture two axes that the purpose alone doesn't pin down — ASK, don't infer them**
     (both change foundational design decisions *before* you build):
     - **Delivery context — presented live to a room · shared/screen-shared in a meeting · sent
       digitally / self-read.** This is the **single most design-determining answer**: it sets the
       deck's **delivery mode** (`design-principles.md` "Delivery mode"). A *presented* deck wants few
       words per slide + larger type + speaker notes; a *self-read* deck must be self-sufficient and can
       carry more text per surface. The same purpose can go either way (a status update presented vs
       emailed), so **don't infer it from the purpose or the density choice — ask it.** For self-read,
       there's no talking-time, so also get the **deck length** directly (short ~5–8 / medium ~9–15 /
       long 16+) instead of deriving it from minutes.
       **Canvas format rides on this answer:** an ordinary talk/meeting/self-read deck is 16:9 —
       never ask a format question there (16:9 is the unchanged default and every rule assumes it).
       But when the deliverable is a **non-slide surface** — a rednote/小红书 image note, an Instagram
       square post, a Story/Reels/Shorts vertical, an A4 print one-pager, or a venue demanding 4:3 —
       **confirm the canvas format** (one option-line, or fold into this question) and build on the
       matching `scripts/formats.py` preset: per-format safe zones, chrome policy, density, and
       layout DNA live in `references/canvas-formats.md`. Same identity + components, recomposed —
       never a 16:9 layout transplanted onto a portrait canvas.
     - **Deck length is ALWAYS the user's choice — surface it, never silently derive it.** Make it an
       explicit interview option: a **self-read** deck → ask **short ~5–8 / medium ~9–15 / long 16+**; a
       **spoken** deck → the **time budget** sets the working count (~1 slide/min), but still **confirm the
       resulting slide count** with the user at the Step-1 content checkpoint before building. Don't ship a
       length the user never saw (e.g. quietly building 14 slides because the content "felt like 14").
     - **Appear-builds (in-slide staged reveals) — the USER decides WHETHER; you decide WHERE.**
       A *presented* deck can reveal a slide's content one beat at a time on click so the room follows
       the speaker instead of reading ahead. **Whether to use builds at all is the user's call, offered
       explicitly — not a silent skill default** (recommended ON for a live talk, since an audience
       benefits, but a user who wants a plain click-through deck just says so). Ask this on **presented
       decks only** — *self-read / screen-shared-to-read* decks are static by design, so don't ask.
       If the user opts **IN**, YOU still choose WHERE (which slides earn a staged reveal) and each
       chosen slide is staged **FULLY** — every content element reveals in a deliberate reading order,
       nothing pre-shown but the title/frame (Step 4 / `references/animation.md`). If they opt **OUT**,
       the deck is static: no builds, and no `NO BUILDS` pressure (run lint with `--static`). Carry the
       choice into the design plan's motion manifest.
     - **Primary goal / intent — inform & educate · support a decision · inspire / motivate action.**
       This sets the **rhetorical arc**: *inform* builds to the evidence; *decide* leads with the
       recommendation and the ask; *inspire* opens on stakes and closes on a call to action. Purpose
       hints at it but doesn't fix it (a conference talk can inform *or* persuade) — so confirm it.
   - *(Structure emphasis — data/trends vs narrative-insights vs sector/section breakdown — and the
     fine-grained slide count are best steered at the **Step-1 content checkpoint**, where the user
     approves the arc, rather than front-loaded here — keep this interview cheap.)*
   - **Webinar / online presentation** = a talk delivered over video, watched in a shrunk
     window on mixed-size screens. Build it like a conference talk but for a shared screen:
     larger type, light background, content in the central safe area, more/lighter slides
     to hold a remote audience, and "ask in the chat" prompts (see `design-by-purpose.md`).
   - **Academic job talk / faculty interview** = a candidate selling their research
     *program* + vision + fit to a hiring department (not one paper to peers). Unlike a
     conference talk it's longer (~45 min), personal, and must connect past work into one
     through-line and a concrete future agenda — so don't model it as a long conference talk.
   - **Product description / pitch** = presenting or selling a *product* to
     prospects, customers, or users (launch deck, sales pitch, product overview) —
     distinct from a *stakeholder readout* (which reports business status/decisions).
     Lead with the value proposition, sell benefits over features, show the real
     product, and end on a call to action. If it targets a named market/event or has
     a brand, treat that like a venue/template and research/honor it. **Confirm the
     audience: an *investor* pitch (raising capital) is a distinct variant** — it sells
     the company/opportunity (market, traction, business model, team, the ask), not just
     the product, so ask "investors, customers/users, or internal stakeholders?" and judge
     it against the investor overlay in `references/review-rubrics.md`.
   - **Conference talk → ALWAYS identify and research the specific venue.** First
     ask *which* conference and (if relevant) which track/format — oral, spotlight,
     poster (e.g. MICCAI, ISMRM, NeurIPS, RSNA, CVPR). **This is required, not
     optional: never build a "generic conference" deck.** Then **web-search the
     named venue** even if you think you know it (guidelines change yearly) to learn:
     talk length & slot, slide aspect ratio, file/format rules, whether an
     **official template** exists (fetch & use it if so), the **audience**
     composition (specialists vs. broad), and what a *strong talk at this venue*
     looks like (single-message expectations, how technical, clinical vs. ML
     framing, Q&A norms, any companion poster). Venue norms vary widely — a clinical
     society ≠ an ML conference — so ground every choice in what you find, cite it
     back to the user, and fold it into the plan, the build, and the critic's rubric.
     If the host exposes no web tool, apply the same fallback as Step 1's no-source
     rule: ask the USER for the venue specs (slot length, aspect ratio, official
     template, audience) instead of searching — never guess them.
     - *Poster, not a talk?* A conference **poster** is a different artifact — one large
       single-canvas layout, not a sequence of slides — so the deck arc and the per-slide
       rubric don't apply directly. `deckkit` can build a single large-canvas "slide"
       (`blank_deck(w_in, h_in)` at the poster's real size, e.g. 33×47 in / A0), and the
       craft rules still hold (whole figures, hierarchy, contrast, one clear story), but
       say plainly that this skill is tuned for *talks* — confirm size/orientation and
       the venue's poster spec before building.

3. **Source material.** "Do you have content for me to work from — code, a paper, a PDF,
   a Word/PowerPoint/Excel file, a doc, existing slides, figures/images, a video or recording?"
   - *Yes* → **dig in deeply** (step 1, content branch): read it properly and build
     from the real material. (But per "requirements first" above — if they didn't
     ask you to reuse a provided deck's *content/wording* as-is, mine it for facts
     and figures, don't inherit its structure or text.) **Route each format to its ingest
     path (content-planner §1 "Input formats") — each dedicated extractor kept uncrossed:** a **`.docx`**
     → `scripts/ingest.py doctext` (exact; a long/book-length one → `ingest.py office`→PDF so long-source
     triage applies); **`.pptx`** → `extract_deck.py` (native — the redesign path); **`.xlsx`** →
     `ingest.py sheet` (exact rows; NOT office→PDF, which drops data); **PDF** → `extract_pdf.py`; an
     **image** → read with vision (understand + place the pixels freely; a number/quote you *type* off
     it is `verified? = N` until confirmed — no OCR here); a **video** → **ask for a transcript** for the
     spoken content + `ingest.py frames` for visuals (no speech-to-text, so narration you can't hear is a
     gap, never invented); **audio-only / a cloud doc (Google/Notion/URL)** → ask for a transcript /
     an exported file respectively. The fidelity floor: text extracts exactly; pixels/audio are
     `verified? = N` until confirmed.
   - *No* → **build the content yourself** from your knowledge, and **web-search to
     ground it** (correct facts, current numbers, credible framing) rather than
     inventing. Confirm the intended scope/outline with the user before building.

## Step 0 — Q4 (style): density levels, mimic modes, and the direction-gate scope

4. **Style.** "How do you want it to look and feel?" Offer these (applies to *every*
   purpose):
   - **Density — ALWAYS a surfaced choice, defined by TEXT-PER-POINT (not "text vs no text").** EVERY
     level has *both* text and visuals; what changes is how much each *point* says and how much the
     diagram carries. Offer three concrete levels (this is the "text-heavy vs diagram-heavy" question):
     - **Diagram-heavy** — *a phrase per point* (~3–7 words); a diagram / figure / chart carries the
       idea, the text is a terse label or takeaway. Lets an audience follow a *speaker*. (Presented default.)
     - **Balanced** — *one short sentence per point* + a supporting visual; scannable live, still mostly
       clear when skimmed.
     - **Text-heavy** — *2–3 self-contained sentences per point* (a short paragraph); the slide reads on
       its own without a speaker, visuals support the prose. For a **read-without-a-speaker** artifact —
       leave-behind, emailed/reference/appendix deck, board pre-read, **poster**, single-slide
       **infographic** — that fuller text is the deliverable, not a flaw.
     **Surface it explicitly (like deck length) and scale the options to delivery (Q2):** a **presented**
     deck → *diagram-heavy (recommended) ↔ balanced* (a text-heavy presented deck is a wall of text —
     steer away); a **self-read / poster** deck → *balanced ↔ text-heavy*. Don't silently decide it from
     the purpose. (This sets the deck's **delivery mode** — see `references/design-principles.md`.)
   - **"Mimic an example I'll provide"** — the user hands over a **whole deck, a few slides, or even ONE
     slide / screenshot** whose design they want echoed. Different from a *template* (Q1): you do NOT
     build on it or inherit its logos/content — you reproduce what they value in your own build.
     **First ask which INTENT** (they mean one of two — the build differs):
     - **(1) Reproduce the look** — same family: match the example's **palette, fonts, motifs, density**
       (a faithful style clone, with the user's content).
     - **(2) Borrow its components & layout, but redesign the style for MY topic** — keep the example's
       *structure + component vocabulary* (its card style, callout, diagram/layout pattern, signature
       motif) but **re-choose the palette / mood / type to fit the topic** and refill with the user's
       content ("inspired by, not copied"). *This is the common ask* ("mimic but not copy, restyle for
       the topic, apply some of its components").
     Then **understand it before building** — a glance won't do (for a single slide, treat its treatment
     as the deck-wide system, confirming with the user). Write the structured **style brief** (structure/
     rhythm, grid, colour, type, decorations & motifs, the **2–4 components worth reusing**, tone) and
     build per the chosen mode — **follow `references/style-analysis.md`** (Mode A reproduces; Mode B
     borrows components + restyles to the topic), keeping the user's content + the craft rules. Composes
     with everything (e.g. build on the user's template for branding, yet borrow an example's components).
   - Plus any tone (academic, corporate, playful).
   Honor their choice over your own habits; nudge toward concise + visual when
   unsure; carry the choice into the plan (steps 1–2) and the build (step 4).
   - **Direction gate (when to show rendered options first).** Two cases call for it:
     (a) **"design a clean one" / no template** → it's the *recommended default* there —
     offer **4** directions as described in Q1's design-one branch above (3 best-fit DNA presets +
     1 colour-scheme direction); (b) any other case where the user is **unsure on style** or it's a
     **brand-defining / high-stakes** deck → offer **2–3 directions** as a lighter opt-in. Either way it's the same machinery
     (collaborative mode Gate A, `references/collaborative-mode.md` + `scripts/archetypes_html.py`):
     **one HTML link** showing the archetype slides per direction, which the user opens and picks
     from before the full build. **Scope differs by case, and the difference matters:** on case (a)
     — the no-template branch — the gate **RUNS BY DEFAULT** and is skippable only via one of Q1(c)'s
     NAMED carves, recorded on the checkpoint's `direction gate:` line (a design checkpoint on that
     branch with no gate line is not ready). Only case (b), the lighter unsure/brand-defining offer,
     is **skippable, never forced.** A *registered or provided* template, **a generated template** (Q1's image-tool
     branch), **or a Mode-A mimic example** (Q4 "reproduce the look")
     means the look is already decided — **don't offer the gate** in those cases. (A Mode-B mimic
     stays eligible for the lighter case-(b) offer — its palette/mood is re-chosen for the topic.)
