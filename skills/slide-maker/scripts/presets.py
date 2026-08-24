#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""presets — named DESIGN-LANGUAGE presets: one switch sets a coherent palette + fonts + surface
treatment + image-prompt style, so a deck's look is consistent from the first slide.

These are *starting languages*, not straitjackets — the model still tunes to the brand/purpose and
the user's references always win. Apply one like:

    from presets import preset
    # NOTE: CJK faces use 'Hiragino Sans GB', NOT 'PingFang SC' — the macOS LibreOffice
    # render loop substitutes a handwriting face for PingFang (see deckkit.EAFONT comment).
    p = preset("glassmorphism")
    deckkit.FONT = p["font"]; deckkit.DISPLAY = p["display"]; deckkit.MONO = p["mono"]
    INK = p["ink"]; ACCENTS = p["accents"]; BG = p["bg"]
    # For a CJK (Chinese/Japanese/Korean) deck, ALSO set the East-Asian slot, or the Latin face
    # (e.g. "Arial Black") tofus on CJK glyphs:
    deckkit.EAFONT = p["ea"]; deckkit.EADISPLAY = p["ea_display"]
    # build glass cards on a BG-filled slide lit by deckkit.glow(...), per p["surface"]

Each preset carries Latin faces (`font`/`display`/`mono`) AND a CJK fallback pair (`ea`/`ea_display`,
sensible defaults to adjust per script — the JP/KR equivalents are in references/multilingual.md).
`image_prompt` is the prefix to feed the generated-template image route (references/
generated-template.md) so generated plates match the chosen language. Pair with the Style library
in references/generated-template.md and the per-purpose guidance in references/design-by-purpose.md.

`guard` = the preset's 1-3 REGISTER-DEFINING constraints (countable/absolute, negatives first).
Unlike the rest of the preset, guards survive the "vary it" rule: the designer/builder honor them
literally and the critic flags any violation as a register break. They define the register; they
are not a straitjacket on palette tuning.

PRECEDENCE: a guard is a register floor for the SKILL'S OWN choices only. An explicit user request
or a recorded named deviation (the plan line naming the guard it overrides) lifts it, and the
critic treats a recorded guard deviation like the stylized-illustration deviation — a taste call,
not a register break.
"""
import sys as _sys
import warnings
from pptx.dml.color import RGBColor
def C(h): return RGBColor.from_string(h)

# The calligraphic 楷体 family ships under DIFFERENT names per platform: macOS has 'Kaiti SC'
# (no family named plain 'KaiTi' exists there), Windows has 'KaiTi'. Resolve at import so the
# ink presets' signature titles never ride an uncontrolled font substitution in the build loop.
_KAITI = "Kaiti SC" if _sys.platform == "darwin" else "KaiTi"

PRESETS = {
    "glassmorphism": {
        "radius": 1.4, "rule_w": 1.0,   # structural tokens — see deckkit.set_geometry
        "mood": "premium dark UI / tech — depth, light, frosted glass",
        "bg": C("0A0E27"), "ink": C("F2F5FC"), "muted": C("AEB7CC"),
        "accents": [C("5B8DEF"), C("3DDDFC"), C("A26BFA"), C("FB7185"), C("4ADE80")],
        "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Noto Sans CJK SC", "ea_display": "Hiragino Sans GB",
        "surface": "glass_card (tint+sheen+rim) on a BG-filled slide lit by 1-2 glow()s; KPI tiles "
                   "use scorecard(glass_tint=); white headline keyword in the accent.",
        "guard": "no glass cards on a light base — the dark BG IS the register; max 2 glow()s per "
                 "slide; ONE accent per headline keyword, never a rainbow.",
        "image_prompt": "dark atmospheric gradient background, deep navy to violet, soft neon color "
                        "glows and subtle bokeh, premium tech mood, no text, calm zone for a title",
        "when": "launches, product/tech talks, dashboards, design-forward decks. NEEDS a dark base.",
    },
    "swiss": {
        "radius": 0.0, "rule_w": 0.6,   # structural tokens — see deckkit.set_geometry
        "mood": "International Typographic Style — grid, restraint, one red",
        "bg": C("FFFFFF"), "ink": C("111111"), "muted": C("777777"),
        "accents": [C("E2231A")], "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Noto Sans CJK SC", "ea_display": "Hiragino Sans GB",
        "surface": "strict flush-left columns(), hairline rules, big type-scale ratio, generous "
                   "whitespace; spend the ONE red on the single focal item (accent_one); ghost "
                   "numerals for enumerated grids.",
        "guard": "ONE red only; no gradients, no rounded cards, no soft shadows.",
        "image_prompt": "minimal swiss graphic, faint grid / graph-paper texture, a single red disc, "
                        "lots of white space, no text",
        "when": "research, design, editorial, defense, any minimal/typographic register.",
    },
    "editorial_paper": {
        "radius": 0.3, "rule_w": 0.6,   # structural tokens — see deckkit.set_geometry
        "mood": "luxury magazine — warm paper, serif, gold, big photography",
        "bg": C("FAF6EE"), "ink": C("1C1A17"), "muted": C("8A8275"),
        "accents": [C("B58A2E"), C("CBB46A")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Noto Serif CJK SC", "ea_display": "Songti SC",
        "surface": "editorial_header (caps eyebrow + serif title + hairline); full-bleed photos under "
                   "scrim_overlay; big italic Georgia numerals (big_numeral; digits via a lining "
                   "face beside CJK — font-guidance.md); stat_row for figures; "
                   "photos carry all saturation, chrome stays neutral.",
        "guard": "no saturated chrome — photography carries ALL the colour; gold stays on "
                 "numerals/kickers/hairlines, never large fills.",
        "image_prompt": "warm, refined editorial photography (architecture / interiors / lifestyle), "
                        "soft natural light, magazine quality, no text",
        "when": "brand, portfolio, award, culture/lifestyle, showcase — tone over data density.",
    },
    "editorial_report": {
        "radius": 0.4, "rule_w": 0.7,   # structural tokens — see deckkit.set_geometry
        "mood": "serious dark briefing — FT/Bloomberg gravitas, one-red discipline",
        "bg": C("0E0E12"), "ink": C("ECECEF"), "muted": C("8C8C97"),
        "accents": [C("E0392B"), C("D9A441")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Noto Serif CJK SC", "ea_display": "Songti SC",
        "surface": "serif display headlines + caps kicker over a hairline; a designed chart per slide "
                   "(designed_charts) with single-highlight + takeaway_rail; per-slide source line; "
                   "roman-numeral section dividers; atmospheric orb image ONLY on dividers. "
                   "ICONS: not the device here (dark gravitas + designed charts) — at most one "
                   "restrained monochrome wayfinding mark on dividers; no icon-card grids.",
        "guard": "ONE red emphasis per slide; no icon-card grids; orb imagery on dividers only.",
        "image_prompt": "a single abstract glowing orb / eclipse on near-black, restrained, mood-shifted "
                        "per chapter, no text — for section dividers only",
        "when": "market/landscape reports, investor/strategy briefings, thought-leadership.",
    },
    "risograph": {
        "radius": 0.4, "rule_w": 1.3,   # structural tokens — see deckkit.set_geometry
        "mood": "indie print zine — riso in 2 inks + the navy neutral, halftone, hard offset shadows",
        "bg": C("F3ECD9"), "ink": C("1B2A4A"), "muted": C("6B7280"),
        "accents": [C("FF4D8D"), C("F5B301"), C("1B2A4A")], "font": "Arial", "display": "Arial Black",
        "mono": "Consolas", "ea": "Hiragino Sans GB", "ea_display": "Heiti SC",
        "surface": "offset_shadow 'sticker' cards/numbers/headlines (hard, not soft); mono chrome "
                   "(eyebrows/footers/page-markers); full-bleed duotone halftone illustrations.",
        "guard": "no soft shadows, no gradients — offset shadows are HARD; hold to the 2 inks + "
                 "the navy neutral, no extra hues.",
        "image_prompt": "two-color risograph halftone print, navy + fluorescent pink on cream paper, "
                        "grain and slight misregistration, bold flat illustration, no text",
        "when": "culture, marketing, teaching, launch — audiences that reward personality.",
    },
    "memphis": {
        "radius": 1.6, "rule_w": 1.2,   # structural tokens — see deckkit.set_geometry
        "mood": "80s-90s New Wave — bold, playful, chaotic-geometric",
        "bg": C("FCF2D8"), "ink": C("1A1A17"), "muted": C("9A9384"),
        "accents": [C("F76302"), C("0548C5"), C("E2342B"), C("1B7A3D"), C("F6BE1A")],
        "font": "Arial", "display": "Arial Black", "mono": "Consolas",
        "ea": "Hiragino Sans GB", "ea_display": "Heiti SC",
        "surface": "cream bg; rounded cards with colored header bands (auto-contrast label); dark "
                   "emphasis bands; scattered Memphis motifs (dots/zigzags/triangles) as margin accents.",
        "guard": "no motifs behind text — margins only; keep the cream ground on every content slide.",
        "image_prompt": "Memphis / New Wave 80s-90s flat illustration, bold black outlines, squiggles "
                        "zigzags dots triangles, vivid colors on cream, no text, calm title zone",
        "when": "events, festivals, launches, culture decks wanting energy.",
    },
    "brutalist": {
        "radius": 0.0, "rule_w": 3.0,   # structural tokens — see deckkit.set_geometry
        "mood": "brutalist newspaper / annual report — heavy rules, raw type, ink-red-white",
        "bg": C("FFFFFF"), "ink": C("111111"), "muted": C("3A3A3A"),
        "accents": [C("C8102E")], "font": "Arial", "display": "Arial Black", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "multi-column NEWSPAPER grid with THICK black rules/borders (heavy hrule, boxed "
                   "tables with bold borders); ALL-CAPS condensed headlines (Arial Black / Impact); "
                   "Consolas mono for data/labels; the ONE red for a single emphasis; big raw "
                   "numerals; high density, flush-left, NO rounded corners, NO soft shadows.",
        "guard": "no rounded corners, no soft shadows, no pastels; the ONE red appears once per slide.",
        "image_prompt": "high-contrast black and white halftone / newsprint photo, stark, one red "
                        "overprint, no text",
        "when": "annual report, manifesto, data-journalism with attitude, bold tech/culture decks.",
    },
    "blueprint": {
        "radius": 0.0, "rule_w": 0.6,   # structural tokens — see deckkit.set_geometry
        "mood": "engineering / academic blueprint — schematic line-work on deep navy, one warm accent",
        "bg": C("0A1B38"), "ink": C("EAF2FF"), "muted": C("8FA6C4"),
        "accents": [C("46B4E8"), C("F1764E")], "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "deep-navy panels, cyan schematic line-work (thin rules, node/connector motifs, a "
                   "faint blueprint frame/grid), mono eyebrow chrome; build architecture/pipeline "
                   "diagrams from boxed nodes + arrows; reserve the ONE coral accent for the focal "
                   "path/result. Native tables + typeset equations sit on the dark panels.",
        "guard": "ONE coral accent, reserved for the focal path/result; line-work stays thin — "
                 "no filled multi-colour nodes.",
        "image_prompt": "technical blueprint schematic, thin cyan line-work on deep navy, grid, nodes "
                        "and connectors, engineering drawing, no text, calm title zone",
        "when": "technical/method talks, architecture, agents/AI/engineering, paper-reading decks.",
    },
    "ink_wash": {
        "radius": 0.0, "rule_w": 0.5,   # structural tokens — see deckkit.set_geometry
        "mood": "Chinese ink editorial (藏拙) — warm paper, ink black, one seal red, KaiTi serif",
        "bg": C("F5F1E8"), "ink": C("1A1A1A"), "muted": C("8B8680"),
        "accents": [C("A52A2A"), C("5C5852")], "font": "Hiragino Sans GB", "display": _KAITI, "mono": "Consolas",
        "ea": "Hiragino Sans GB", "ea_display": _KAITI,
        "surface": "warm-paper bg, large KaiTi/Songti CJK display, ink-black body; ONE seal-red accent "
                   "as a chop/seal stamp (deckkit.seal) + CJK numeral section markers (壹贰叁, via "
                   "deckkit.cjk_numeral); hairline rules, generous margins, dark label-chips for "
                   "emphasis, a restrained ink-wash motif. Calm, literary, lots of breathing room.",
        "guard": "preserve 留白 — no filled corners, no dense grids; ONE seal-red accent (the chop), "
                 "never a second warm hue.",
        "image_prompt": "minimal Chinese ink-wash (shuimo) painting, soft mountains / a branch, warm "
                        "rice-paper texture, muted, one vermilion seal mark, vast empty space, no text",
        "when": "Chinese cultural / literary / brand / humanities decks; any 中文 editorial register.",
    },
    "eastern_traditional": {
        "radius": 0.0, "rule_w": 0.7,   # structural tokens — see deckkit.set_geometry
        "mood": "Eastern traditional-colour narrative — warm paper, ochre-gold + sage, KaiTi",
        "bg": C("F7F2E8"), "ink": C("3A3530"), "muted": C("7A7068"),
        "accents": [C("C99E62"), C("6F8F75"), C("A52A2A")], "font": "Hiragino Sans GB", "display": _KAITI, "mono": "Consolas",
        "ea": "Hiragino Sans GB", "ea_display": _KAITI,
        "surface": "warm-paper bg with a TRADITIONAL Chinese colour palette (ochre-gold 赭 + sage 竹青 + "
                   "vermilion 朱); KaiTi/Songti display, refined body; colour-name swatches, seal "
                   "stamps (deckkit.seal), vertical-text accents, ink-wash motifs. The colours "
                   "themselves carry the story (e.g. a 传统色 / plant-dye palette).",
        "guard": "only the named 传统色 hues — no neon, no corporate blue; seal red as CHROME stays "
                 "a small stamp, never a fill — content colour-swatches exempt.",
        "image_prompt": "traditional East-Asian artwork, warm earth pigments — ochre, sage green, "
                        "vermilion — on aged paper, botanical / landscape motif, muted, no text",
        "when": "traditional-culture, heritage, colour/material, plant-dye, museum/exhibition CN decks.",
    },
    "consulting": {
        "radius": 0.8, "rule_w": 1.0,   # structural tokens — see deckkit.set_geometry
        "mood": "top-tier (MBB) strategy deck — white, action titles, navy insight banners, semantic 5-colour",
        "bg": C("FFFFFF"), "ink": C("1A2B45"), "muted": C("5A6B82"),
        "accents": [C("1A2B45"), C("1F8A70"), C("C9A227"), C("C0492E"), C("64748B")],
        "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Microsoft YaHei", "ea_display": "Microsoft YaHei",
        "surface": "clean white; every title is a full-sentence ACTION TITLE (the conclusion), paired "
                   "with a deckkit.insight_banner (navy 'so-what' bar) under it; a navy->emerald "
                   "gradient_rule along the top; a SEMANTIC 5-colour contract (navy=structure, "
                   "emerald=good/opportunity, gold=brand/highlight, coral=risk/gap, slate=neutral) "
                   "propagated to headings/badges/table-columns/chart-series; scorecard tiles, "
                   "step_list roadmaps, quadrant/matrix; a small CONFIDENTIAL footer status_stamp. "
                   "ICONS: heroicons-solid or tabler, sparingly, for the few section/category marks + "
                   "status flags ONLY (not on every KPI tile) — alongside, not on top of, the furniture.",
        "guard": "no CONTENT-slide title that isn't a full-sentence conclusion (covers/dividers/"
                 "agenda exempt); semantic hues never reassigned (emerald=good, coral=risk); icons "
                 "on section/category marks + status flags only.",
        "image_prompt": "clean corporate abstract, soft navy and emerald geometric, lots of white "
                        "space, professional, no text",
        "when": "strategy proposals, board/exec readouts, consulting, business cases.",
    },
    "dark_tech": {
        "radius": 1.0, "rule_w": 1.0,   # structural tokens — see deckkit.set_geometry
        "mood": "calm near-black engineering — semantic accents on navy, white 'diagram islands', mono brand",
        "bg": C("0C1320"), "ink": C("E8EDF5"), "muted": C("8A96AC"),
        "accents": [C("4F9CF5"), C("33C2A6"), C("F2A33C"), C("E0556E"), C("A98BF0")],
        "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Microsoft YaHei", "ea_display": "Microsoft YaHei",
        "surface": "near-black canvas; build flowcharts/figures inside a bright deckkit.diagram_island "
                   "(white device-bezel panel + 'Figure N' caption) so diagrams read on dark; header "
                   "master = tick + tracked mono eyebrow + bold H1 + amber->blue gradient_rule; a "
                   "terminal '>_' / mono brand voice; multi-colour SEMANTIC accents (one hue per "
                   "concept) on the node/connector diagram kit; insight callouts with an accent left bar.",
        "guard": "no diagrams drawn straight on the navy — host them in a diagram_island; one hue "
                 "per concept, never remixed mid-deck.",
        "image_prompt": "dark engineering schematic ambience, deep navy, faint circuit / node mesh, "
                        "cool glow, no text, calm title zone",
        "when": "AI/ML, infra, agents, developer-tool, eng-blog and safety decks (dark, technical).",
    },
    "luxury_dark": {
        "radius": 0.4, "rule_w": 0.6,   # structural tokens — see deckkit.set_geometry
        "mood": "dark luxury editorial — near-black, ONE metallic accent, photography supplies the colour",
        "bg": C("0A0A0A"), "ink": C("F5F0EB"), "muted": C("9E9690"),
        "accents": [C("C9A96E"), C("8B7355")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Microsoft YaHei", "ea_display": "Songti SC",
        "surface": "warm near-black; a SINGLE champagne/brass accent carried only through gold serif "
                   "numerals, kickers and hairlines; full-bleed photography spreads supply all colour "
                   "(use duotone/grayscale on stray photos so nothing competes); bilingual_lockup "
                   "covers; thin masthead/issue chrome; generous negative space, restrained, premium.",
        "guard": "ONE champagne accent FAMILY — accents[1] is its darker shade (hairlines/kickers), "
                 "never a contrasting hue; stray photos go duotone/grayscale so nothing competes.",
        "image_prompt": "high-end fashion/editorial photography mood, deep shadow, warm champagne "
                        "highlight, luxurious, minimal, no text",
        "when": "fashion, luxury brand, premium product, gallery/awards — tone over data.",
    },
    "museum_memorial": {
        "radius": 0.2, "rule_w": 0.6,   # structural tokens — see deckkit.set_geometry
        "mood": "midnight-navy memorial / exhibition — brass-gold accents, archival duotone, serif gravitas",
        "bg": C("0E1A2B"), "ink": C("ECE6D8"), "muted": C("8B93A3"),
        "accents": [C("C5A253"), C("6E8CA8")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Microsoft YaHei", "ea_display": "Songti SC",
        "surface": "deep midnight-navy gradient ground; brass-gold serif headings + hairlines; archival "
                   "photos as duotone (navy+gold); a thin double-line catalogue_frame inset from edges; "
                   "year_badge chronology; a serif gold 'monument' closing line; quiet, reverent, "
                   "exhibition-catalogue cadence (works in EN or 中文).",
        "guard": "no full-colour archival photos — duotone (navy+gold) only; brass gold for "
                 "headings/hairlines, never large fills.",
        "image_prompt": "archival sepia/duotone photograph mood, midnight navy and brass gold, museum "
                        "exhibition lighting, dignified, no text",
        "when": "memorial, history/heritage, museum exhibition, biography, retrospective decks.",
    },
    "bauhaus": {
        "radius": 0.0, "rule_w": 2.6,   # structural tokens — see deckkit.set_geometry
        "mood": "Bauhaus modernism — the primitive triad (circle/square/triangle) as the layout's "
                "structural actors, primary red/yellow/blue on white, lowercase geometric sans.",
        "bg": [245, 243, 238], "ink": [26, 26, 26], "muted": [110, 108, 102],
        "accents": [[213, 43, 30], [247, 181, 0], [0, 90, 168], [26, 26, 26]],
        "font": "Century Gothic", "display": "Century Gothic", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "oversized filled PRIMITIVES (circle/square/triangle) placed as compositional "
                   "anchors behind/beside titles (deckkit.box round + freeform triangle); primary-"
                   "triad fills, one primitive per slide as the hero shape; lowercase geometric sans, "
                   "occasional 45° rotation; thick black rules; zero ornament, generous whitespace.",
        "guard": "one hero primitive per slide, never a confetti of shapes (that is memphis); keep "
                 "the triad pure — no tints or gradients on the primary fills.",
        "image_prompt": "Bauhaus poster, primary red yellow blue and black on off-white, large "
                        "geometric primitives, Moholy-Nagy composition, no text",
        "when": "design, architecture, education, modernist brand, a bold geometric register.",
    },
    "midcentury": {
        "radius": 1.8, "rule_w": 0.8,   # structural tokens — see deckkit.set_geometry
        "mood": "Mid-century modern — warm harvest palette + atomic/starburst/boomerang motifs, "
                "1950s-60s optimism; geometric-humanist type.",
        "bg": [244, 237, 221], "ink": [42, 37, 30], "muted": [120, 108, 90],
        "accents": [[197, 90, 42], [214, 160, 44], [74, 122, 106], [45, 78, 92]],
        "font": "Futura", "display": "Futura", "mono": "Menlo",
        "ea": "Songti SC", "ea_display": "Songti SC",
        "surface": "harvest ramp (burnt orange · mustard · avocado/teal · cream); one signature motif "
                   "per section — starburst (radial line-array from a point) · boomerang (two joined "
                   "arcs) · atomic orbit (ellipse rings + dot nodes), drawn as thin-line vector; "
                   "solid-fill + thin-line mix, rounded organic shapes, no texture.",
        "guard": "the harvest palette is the identity — never pastel it up or add a fifth loud hue; "
                 "the LOUD atomic/starburst motif is dosed one per section, not per slide (a quiet "
                 "corner-echo register mark may repeat every slide — that is SYSTEM, not stamping).",
        "image_prompt": "mid-century modern illustration, mustard avocado burnt-orange teal on cream, "
                        "atomic starburst motifs, 1950s optimism, no text",
        "when": "culture, retro brand, lifestyle, a warm optimistic register; anything Eames-era.",
    },
    "terminal": {
        "radius": 0.0, "rule_w": 1.0,   # structural tokens — see deckkit.set_geometry
        "mood": "Terminal / monospace — phosphor-on-black CRT: fixed-width type throughout, a "
                "command-line register for engineers.",
        "bg": [10, 15, 10], "ink": [200, 240, 200], "muted": [90, 130, 90],
        "accents": [[51, 255, 102], [255, 176, 0], [90, 200, 255], [255, 90, 90]],
        "font": "Consolas", "display": "Consolas", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "single MONOSPACE stack everywhere; phosphor-green (#33FF66) or amber (#FFB000) on "
                   "near-black; faint scanline texture (thin horizontal rules at low alpha); list "
                   "bullets are `>` / `$` prompt glyphs; a block cursor accent; boxed output panels "
                   "with mono labels; keep it legible — phosphor on black is high-contrast by design.",
        "guard": "mono for EVERY run including headings — a proportional face breaks the register; "
                 "one phosphor accent, the others only for status (ok/warn/error).",
        "image_prompt": "retro CRT terminal, phosphor green text on black, scanlines, monospace, "
                        "command line, no real words",
        "when": "developer-tool, CLI/infra, hacker/CTF, an eng-blog or release-notes register.",
    },
    "synthwave": {
        "radius": 0.6, "rule_w": 1.2,   # structural tokens — see deckkit.set_geometry
        "mood": "Synthwave / Outrun — retro-futurist neon: a receding perspective grid to a horizon, "
                "sunset gradient, glow. Vivid and high-contrast.",
        "bg": [18, 12, 38], "ink": [240, 235, 255], "muted": [150, 130, 190],
        "accents": [[255, 45, 149], [64, 224, 255], [255, 138, 61], [150, 90, 255]],
        "font": "Trebuchet MS", "display": "Trebuchet MS", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "deep indigo/black ground; a receding perspective GRID horizon (converging lines to "
                   "a vanishing point) as the signature backdrop; a banded sunset gradient (orange→"
                   "magenta→purple) with a horizon sun; neon magenta/cyan accents with a soft glow "
                   "(layered offset shadows); chrome/beveled display type. Vivid but keep text on a "
                   "solid panel where it crosses the grid.",
        "guard": "the neon glow is chrome, never on body text (it kills legibility); the LOUD full grid "
                 "horizon is dosed one per divider/cover, not on every content slide (a faint low-edge "
                 "horizon register may repeat every slide — that is SYSTEM, not stamping).",
        "image_prompt": "synthwave outrun, neon magenta cyan sunset grid horizon, 80s retro-future, "
                        "glowing perspective grid, no text",
        "when": "launch, gaming, music/culture, a bold retro-future register; audiences wanting energy.",
    },
}


def apply(name):
    """Apply a preset's COLOUR and its STRUCTURE in one call, then return the preset dict.

    Before the structural tokens existed a preset was 5 colours, 5 font names and 3 English
    sentences — and the sentences ("NO rounded corners", "hairline rules", "THICK black
    rules/borders") were the part that made a register look like itself, and the part nothing
    implemented. Honouring them meant abandoning the component library and hand-rolling with
    box(), because 55 components pass round=True with no caller-side switch. Now they are data:

        import presets, deckkit as dk
        p = presets.apply("brutalist")      # palette + fonts + hard edges + thick rules

    Returns the preset so the caller can still read `surface` / `guard` / `image_prompt`, which
    stay prose on purpose — they are art direction, not geometry.

    It also sets the GROUND. It did not, and that was the third half-application in a row: the
    preset carried `bg`, `apply()` returned it, and NOTHING painted it. 8 of the 18 registers are
    dark, so a caller doing exactly what this docstring said got the register's light ink on a
    white canvas — measured on `dark_tech`, body text at 1.18:1, surfaced only by the render lint,
    one build->render->diagnose round trip after the fact was already known. `set_ground` exists
    because `apply()` runs before any slide does, so it cannot call `slide_background()` itself.
    """
    import deckkit as dk

    # 🔴 A preset's FACE is a name, and a name that is not installed is measured in a substitute —
    # which is worst precisely where the register is typographic. Measured: `terminal` declares
    # Consolas, absent from macOS, so every fixed-width measurement in a mono register would have
    # been computed in a proportional fallback. deckkit already knows how to ask; apply() did not.
    _pre = PRESETS.get(name) or {}
    _seen = set()
    for _slot in ("font", "display", "mono"):
        _face = _pre.get(_slot)
        if not _face or _face in _seen:
            continue                              # one warning per FACE, not per slot
        _seen.add(_face)
        try:
            if dk._font_substituted(_face):
                warnings.warn(
                    "presets.apply({!r}): the preset's {} face {!r} is NOT installed on this "
                    "machine, so every measurement in it falls back to a metric-incompatible "
                    "substitute. Set an installed face after apply() — dk.FONT = dk.MONO = "
                    "'<installed>' — or run deckkit.use_platform_fonts().".format(
                        name, _slot, _face),
                    stacklevel=2)
        except Exception:
            pass                                  # a font probe must never break a build
    p = preset(name)
    dk.set_palette(deep=p["ink"], slate=p["muted"], accents=list(p["accents"]),
                   font=p["font"], display=p["display"], mono=p["mono"],
                   eafont=p["ea"], eadisplay=p["ea_display"])
    dk.set_geometry(radius=p["radius"], rule_w=p["rule_w"])
    dk.set_ground(ground(name))
    return p


def ground(name):
    """A preset's background as an RGBColor — the colour `apply()` hands to `deckkit.set_ground`."""
    return preset(name)["bg"]


_COLOUR_KEYS = ("bg", "ink", "muted")


def _rgb(v):
    """One colour, however the table wrote it -> RGBColor."""
    if isinstance(v, RGBColor):
        return v
    if isinstance(v, (list, tuple)):
        return RGBColor(*(int(c) for c in v))
    h = str(v).lstrip("#")
    return RGBColor(*(int(h[i:i + 2], 16) for i in (0, 2, 4)))


def preset(name):
    """Return a COPY of the named preset dict (palette as RGBColor, fonts, surface + image-prompt
    guidance). Raises KeyError on an unknown name — see names().

    NORMALISES every colour, because the docstring's "palette as RGBColor" was not true. The table
    is hand-written and the four registers added last — `bauhaus`, `midcentury`, `terminal`,
    `synthwave` — wrote every colour as a plain `[r, g, b]` list while the first fourteen wrote
    RGBColor. Nothing coerced them, so the documented usage

        p = presets.apply("bauhaus"); dk.text(s, ..., [[(t, 13, p["accents"][0], True, False)]])

    raised `ValueError: assigned value must be type RGBColor` on 4 of 18 registers and worked on
    the other 14 — the worst shape for a bug, since it looks like the caller's mistake. `bg` had
    the same split. Normalising HERE means the table stays writable in whichever notation suits
    an entry and every consumer gets one type.
    """
    if name not in PRESETS:
        raise KeyError(f"unknown preset '{name}'; choose from {list(PRESETS)}")
    p = PRESETS[name]
    out = dict(p)
    out["accents"] = [_rgb(a) for a in p["accents"]]
    for k in _COLOUR_KEYS:
        if k in out:
            out[k] = _rgb(out[k])
    return out


def names():
    return list(PRESETS)
