#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""presets — named DESIGN-LANGUAGE presets: one switch sets a coherent palette + fonts + surface
treatment + image-prompt style, so a deck's look is consistent from the first slide.

These are *starting languages*, not straitjackets — the model still tunes to the brand/purpose and
the user's references always win. Apply one like:

    from presets # NOTE: CJK faces use 'Hiragino Sans GB', NOT 'PingFang SC' — the macOS LibreOffice
# render loop substitutes a handwriting face for PingFang (see deckkit.EAFONT comment).
import preset
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
"""
from pptx.dml.color import RGBColor
def C(h): return RGBColor.from_string(h)

PRESETS = {
    "glassmorphism": {
        "mood": "premium dark UI / tech — depth, light, frosted glass",
        "bg": C("0A0E27"), "ink": C("F2F5FC"), "muted": C("AEB7CC"),
        "accents": [C("5B8DEF"), C("3DDDFC"), C("A26BFA"), C("FB7185"), C("4ADE80")],
        "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Noto Sans CJK SC", "ea_display": "Hiragino Sans GB",
        "surface": "glass_card (tint+sheen+rim) on a BG-filled slide lit by 1-2 glow()s; KPI tiles "
                   "use scorecard(glass_tint=); white headline keyword in the accent.",
        "image_prompt": "dark atmospheric gradient background, deep navy to violet, soft neon color "
                        "glows and subtle bokeh, premium tech mood, no text, calm zone for a title",
        "when": "launches, product/tech talks, dashboards, design-forward decks. NEEDS a dark base.",
    },
    "swiss": {
        "mood": "International Typographic Style — grid, restraint, one red",
        "bg": C("FFFFFF"), "ink": C("111111"), "muted": C("777777"),
        "accents": [C("E2231A")], "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Noto Sans CJK SC", "ea_display": "Hiragino Sans GB",
        "surface": "strict flush-left columns(), hairline rules, big type-scale ratio, generous "
                   "whitespace; spend the ONE red on the single focal item (accent_one); ghost "
                   "numerals for enumerated grids.",
        "image_prompt": "minimal swiss graphic, faint grid / graph-paper texture, a single red disc, "
                        "lots of white space, no text",
        "when": "research, design, editorial, defense, any minimal/typographic register.",
    },
    "editorial_paper": {
        "mood": "luxury magazine — warm paper, serif, gold, big photography",
        "bg": C("FAF6EE"), "ink": C("1C1A17"), "muted": C("8A8275"),
        "accents": [C("B58A2E"), C("CBB46A")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Noto Serif CJK SC", "ea_display": "Songti SC",
        "surface": "editorial_header (caps eyebrow + serif title + hairline); full-bleed photos under "
                   "scrim_overlay; big italic Georgia numerals (big_numeral); stat_row for figures; "
                   "photos carry all saturation, chrome stays neutral.",
        "image_prompt": "warm, refined editorial photography (architecture / interiors / lifestyle), "
                        "soft natural light, magazine quality, no text",
        "when": "brand, portfolio, award, culture/lifestyle, showcase — tone over data density.",
    },
    "editorial_report": {
        "mood": "serious dark briefing — FT/Bloomberg gravitas, one-red discipline",
        "bg": C("0E0E12"), "ink": C("ECECEF"), "muted": C("8C8C97"),
        "accents": [C("E0392B"), C("D9A441")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Noto Serif CJK SC", "ea_display": "Songti SC",
        "surface": "serif display headlines + caps kicker over a hairline; a designed chart per slide "
                   "(designed_charts) with single-highlight + takeaway_rail; per-slide source line; "
                   "roman-numeral section dividers; atmospheric orb image ONLY on dividers. "
                   "ICONS: not the device here (dark gravitas + designed charts) — at most one "
                   "restrained monochrome wayfinding mark on dividers; no icon-card grids.",
        "image_prompt": "a single abstract glowing orb / eclipse on near-black, restrained, mood-shifted "
                        "per chapter, no text — for section dividers only",
        "when": "market/landscape reports, investor/strategy briefings, thought-leadership.",
    },
    "risograph": {
        "mood": "indie print zine — 2-color riso, halftone, hard offset shadows",
        "bg": C("F3ECD9"), "ink": C("1B2A4A"), "muted": C("6B7280"),
        "accents": [C("FF4D8D"), C("F5B301"), C("1B2A4A")], "font": "Arial", "display": "Arial Black",
        "mono": "Consolas", "ea": "Hiragino Sans GB", "ea_display": "Heiti SC",
        "surface": "offset_shadow 'sticker' cards/numbers/headlines (hard, not soft); mono chrome "
                   "(eyebrows/footers/page-markers); full-bleed duotone halftone illustrations.",
        "image_prompt": "two-color risograph halftone print, navy + fluorescent pink on cream paper, "
                        "grain and slight misregistration, bold flat illustration, no text",
        "when": "culture, marketing, teaching, launch — audiences that reward personality.",
    },
    "memphis": {
        "mood": "80s-90s New Wave — bold, playful, chaotic-geometric",
        "bg": C("FCF2D8"), "ink": C("1A1A17"), "muted": C("9A9384"),
        "accents": [C("F76302"), C("0548C5"), C("E2342B"), C("1B7A3D"), C("F6BE1A")],
        "font": "Arial", "display": "Arial Black", "mono": "Consolas",
        "ea": "Hiragino Sans GB", "ea_display": "Heiti SC",
        "surface": "cream bg; rounded cards with colored header bands (auto-contrast label); dark "
                   "emphasis bands; scattered Memphis motifs (dots/zigzags/triangles) as margin accents.",
        "image_prompt": "Memphis / New Wave 80s-90s flat illustration, bold black outlines, squiggles "
                        "zigzags dots triangles, vivid colors on cream, no text, calm title zone",
        "when": "events, festivals, launches, culture decks wanting energy.",
    },
    "brutalist": {
        "mood": "brutalist newspaper / annual report — heavy rules, raw type, ink-red-white",
        "bg": C("FFFFFF"), "ink": C("111111"), "muted": C("3A3A3A"),
        "accents": [C("C8102E")], "font": "Arial", "display": "Arial Black", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "multi-column NEWSPAPER grid with THICK black rules/borders (heavy hrule, boxed "
                   "tables with bold borders); ALL-CAPS condensed headlines (Arial Black / Impact); "
                   "Consolas mono for data/labels; the ONE red for a single emphasis; big raw "
                   "numerals; high density, flush-left, NO rounded corners, NO soft shadows.",
        "image_prompt": "high-contrast black and white halftone / newsprint photo, stark, one red "
                        "overprint, no text",
        "when": "annual report, manifesto, data-journalism with attitude, bold tech/culture decks.",
    },
    "blueprint": {
        "mood": "engineering / academic blueprint — schematic line-work on deep navy, one warm accent",
        "bg": C("0A1B38"), "ink": C("EAF2FF"), "muted": C("8FA6C4"),
        "accents": [C("46B4E8"), C("F1764E")], "font": "Arial", "display": "Arial", "mono": "Consolas",
        "ea": "Heiti SC", "ea_display": "Heiti SC",
        "surface": "deep-navy panels, cyan schematic line-work (thin rules, node/connector motifs, a "
                   "faint blueprint frame/grid), mono eyebrow chrome; build architecture/pipeline "
                   "diagrams from boxed nodes + arrows; reserve the ONE coral accent for the focal "
                   "path/result. Native tables + typeset equations sit on the dark panels.",
        "image_prompt": "technical blueprint schematic, thin cyan line-work on deep navy, grid, nodes "
                        "and connectors, engineering drawing, no text, calm title zone",
        "when": "technical/method talks, architecture, agents/AI/engineering, paper-reading decks.",
    },
    "ink_wash": {
        "mood": "Chinese ink editorial (藏拙) — warm paper, ink black, one seal red, KaiTi serif",
        "bg": C("F5F1E8"), "ink": C("1A1A1A"), "muted": C("8B8680"),
        "accents": [C("A52A2A"), C("5C5852")], "font": "Hiragino Sans GB", "display": "KaiTi", "mono": "Consolas",
        "ea": "Hiragino Sans GB", "ea_display": "KaiTi",
        "surface": "warm-paper bg, large KaiTi/Songti CJK display, ink-black body; ONE seal-red accent "
                   "as a chop/seal stamp (deckkit.seal) + CJK numeral section markers (壹贰叁, via "
                   "deckkit.cjk_numeral); hairline rules, generous margins, dark label-chips for "
                   "emphasis, a restrained ink-wash motif. Calm, literary, lots of breathing room.",
        "image_prompt": "minimal Chinese ink-wash (shuimo) painting, soft mountains / a branch, warm "
                        "rice-paper texture, muted, one vermilion seal mark, vast empty space, no text",
        "when": "Chinese cultural / literary / brand / humanities decks; any 中文 editorial register.",
    },
    "eastern_traditional": {
        "mood": "Eastern traditional-colour narrative — warm paper, ochre-gold + sage, KaiTi",
        "bg": C("F7F2E8"), "ink": C("3A3530"), "muted": C("7A7068"),
        "accents": [C("C99E62"), C("6F8F75"), C("A52A2A")], "font": "Hiragino Sans GB", "display": "KaiTi", "mono": "Consolas",
        "ea": "Hiragino Sans GB", "ea_display": "KaiTi",
        "surface": "warm-paper bg with a TRADITIONAL Chinese colour palette (ochre-gold 赭 + sage 竹青 + "
                   "vermilion 朱); KaiTi/Songti display, refined body; colour-name swatches, seal "
                   "stamps (deckkit.seal), vertical-text accents, ink-wash motifs. The colours "
                   "themselves carry the story (e.g. a 传统色 / plant-dye palette).",
        "image_prompt": "traditional East-Asian artwork, warm earth pigments — ochre, sage green, "
                        "vermilion — on aged paper, botanical / landscape motif, muted, no text",
        "when": "traditional-culture, heritage, colour/material, plant-dye, museum/exhibition CN decks.",
    },
    "consulting": {
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
        "image_prompt": "clean corporate abstract, soft navy and emerald geometric, lots of white "
                        "space, professional, no text",
        "when": "strategy proposals, board/exec readouts, consulting, business cases.",
    },
    "dark_tech": {
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
        "image_prompt": "dark engineering schematic ambience, deep navy, faint circuit / node mesh, "
                        "cool glow, no text, calm title zone",
        "when": "AI/ML, infra, agents, developer-tool, eng-blog and safety decks (dark, technical).",
    },
    "luxury_dark": {
        "mood": "dark luxury editorial — near-black, ONE metallic accent, photography supplies the colour",
        "bg": C("0A0A0A"), "ink": C("F5F0EB"), "muted": C("9E9690"),
        "accents": [C("C9A96E"), C("8B7355")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Microsoft YaHei", "ea_display": "Songti SC",
        "surface": "warm near-black; a SINGLE champagne/brass accent carried only through gold serif "
                   "numerals, kickers and hairlines; full-bleed photography spreads supply all colour "
                   "(use duotone/grayscale on stray photos so nothing competes); bilingual_lockup "
                   "covers; thin masthead/issue chrome; generous negative space, restrained, premium.",
        "image_prompt": "high-end fashion/editorial photography mood, deep shadow, warm champagne "
                        "highlight, luxurious, minimal, no text",
        "when": "fashion, luxury brand, premium product, gallery/awards — tone over data.",
    },
    "museum_memorial": {
        "mood": "midnight-navy memorial / exhibition — brass-gold accents, archival duotone, serif gravitas",
        "bg": C("0E1A2B"), "ink": C("ECE6D8"), "muted": C("8B93A3"),
        "accents": [C("C5A253"), C("6E8CA8")], "font": "Arial", "display": "Georgia", "mono": "Consolas",
        "ea": "Microsoft YaHei", "ea_display": "Songti SC",
        "surface": "deep midnight-navy gradient ground; brass-gold serif headings + hairlines; archival "
                   "photos as duotone (navy+gold); a thin double-line catalogue_frame inset from edges; "
                   "year_badge chronology; a serif gold 'monument' closing line; quiet, reverent, "
                   "exhibition-catalogue cadence (works in EN or 中文).",
        "image_prompt": "archival sepia/duotone photograph mood, midnight navy and brass gold, museum "
                        "exhibition lighting, dignified, no text",
        "when": "memorial, history/heritage, museum exhibition, biography, retrospective decks.",
    },
}


def preset(name):
    """Return a COPY of the named preset dict (palette as RGBColor, fonts, surface + image-prompt
    guidance). Raises KeyError on an unknown name — see names()."""
    if name not in PRESETS:
        raise KeyError(f"unknown preset '{name}'; choose from {list(PRESETS)}")
    p = PRESETS[name]
    out = dict(p)
    out["accents"] = list(p["accents"])
    return out


def names():
    return list(PRESETS)
