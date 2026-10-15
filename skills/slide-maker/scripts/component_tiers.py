"""Which general components wear a visual language, and how far (spec §5.5) — plain data, no deckkit import, so docs
and gates read it without building anything.

TIER1: every general component is held to every ground of every language (theme colours, readable, placed).
TIER2_SKIN: the components that also draw their containers, rules, markers and numerals in the language's SKIN, and
which of those roles each one draws. SKIN_VOCAB: the values a manifest may pick per role (spec §5.3); a value is
implemented once in deckkit and reused by every language that picks it. A new language picks from here and adds a
value only when none fits."""

TIER1 = ("agenda bento consort_flow distribution dot_strip dumbbell_board eval_matrix forest_plot funnel gantt "
         "heat_matrix iso_bars iso_prism iso_stack km_curve leaderboard marimekko meter_bar native_chart org_tree "
         "position_map pyramid radar roc_curve sankey scorecard segmented_bar small_multiples stat_row step_list table "
         "tier_stack timeline unit_grid venn waterfall bland_altman source_note").split()
TIER1 = tuple(TIER1)

TIER2_SKIN = {
    "bento": ("card",),                     # through dk.skin_card — bento returns the rects, the caller draws them
    "step_list": ("marker", "rule", "number"),
    "timeline": ("rule", "marker", "number"),
    "agenda": ("rule", "number"),
    "stat_row": ("rule", "number"),
    "org_tree": ("card", "rule"),
    "tier_stack": ("card", "rule"),
    "funnel": ("card", "rule"),
    "pyramid": ("card", "rule"),
    "venn": ("rule",),
    "meter_bar": ("rule", "number"),
    "gantt": ("rule", "number"),
    "table": ("rule", "number"),
    "native_chart": ("rule", "number"),
    "heat_matrix": ("number",),
}

SKIN_VOCAB = {
    "card": ("filled", "outlined", "hairline", "window", "sign", "chalk", "paper"),
    "rule": ("solid", "hairline", "dashed", "chalk"),
    "marker": ("disc-number", "dot", "roundel", "circled", "badge"),
    "number": ("body", "display", "mono"),
}
SKIN_DEFAULT = {"card": "filled", "rule": "solid", "marker": "disc-number", "number": "body"}
