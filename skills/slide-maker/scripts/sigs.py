#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sigs — print the exact call contract for several helpers in ONE lookup.

WHY THIS EXISTS, measured. On one 12-page build the author read helper signatures one at a time,
each read costing a full round-trip, and still shipped two call-shape errors that took three more
round-trips to correct: a run tuple passed with the font in the wrong position, and a colour passed
as a hex string where an RGBColor was required. Reading `deckkit.py` around a function answers one
question; planning a slide needs five answers at once, and every extra round-trip re-sends the whole
conversation (measured: ~302k tokens per call by mid-build).

So: name every helper the slide will use, get every signature back together, before writing code.

    python3 scripts/sigs.py text box native_chart takeaway_rail source_note
    python3 scripts/sigs.py --search sankey          # find helpers by name/docstring
    python3 scripts/sigs.py --full venn              # whole docstring, not just the head

Covers deckkit and designed_charts. Exits 1 if any name is unknown, with near-miss suggestions —
a typo must not read as "no such helper, hand-roll it", which is the failure this guards against.
"""
from __future__ import annotations

import argparse
import difflib
import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# `register_surface` is here for the same reason the other two are: this lookup is where an agent
# finds out what already exists, and SKILL.md tells it that a name matching NO helper means "you
# supply the geometry". Leaving the surface kits out of it therefore did worse than hide them — it
# told anyone asking for `halftone` or `starburst` to hand-roll the thing that had just been built.
MODULES = ("deckkit", "designed_charts", "register_surface", "citations", "ornaments", "image_fx",
           "image_series", "surfaces", "display_type", "collage", "visual_languages", "native_art")

# The three call-shape errors that actually cost round-trips on a real build. They are properties of
# the API that no single signature line states, so they are printed with every lookup rather than
# left in one helper's docstring where only that helper's reader would find them.
CONTRACTS = """\
CALL-SHAPE CONTRACTS (the ones that have actually gone wrong):
  · a text RUN is (text, size, color, bold, italic[, font])  — font is the SIXTH item. Runs live in
    paragraphs: text(slide, x, y, w, h, [[run, run], [run]]) is TWO paragraphs.
  · MEASURING takes a DIFFERENT run shape than PLACING. measure_text(runs, w, size) wants a FLAT
    list of (text, bold) 2-tuples — not the paragraphs text() takes. SKILL.md tells you to use the
    pair together ("measure or anchor, never hand-pick a y"), so the mismatch is hit on the first
    honest attempt: passing text()'s paragraphs raises `not enough values to unpack (expected 2)`.
        h = dk.measure_text([(body, False)], w, 14)      # measure
        dk.text(s, x, y, w, h, [[(body, 14, dk.DEEP, False, False, dk.FONT)]])   # place
    🔴 …and the SAME LINE SPACING. `text()` takes `line_spacing=`; `measure_text` assumed its own
    default and nothing tied them together, so measuring at the default and placing at 1.16
    reserves ~4% too little. Measured: a divider derived from that return was drawn through the
    last line of the block above it, and BOTH linters passed the page — the geometry they check
    is computed from the same short number. Pass the value to both:
        h = dk.measure_text(runs, w, 12, line_spacing=1.16)                     # measure AT it
        dk.text(s, x, y, w, h, paras, line_spacing=1.16)                        # place AT it
    🔴 The measure and the place must name the SAME face. measure_text takes `font=` — pass it
    whenever you place in anything but the deck default, above all MONO. Measured: the same
    command string is 4.04in in Helvetica and 5.44in in Courier, so measuring mono text in the
    default face under-reports it by 26% and the box is then built to the wrong size, which every
    later check happily agrees with.
        h = dk.measure_text([(cmd, False)], w, 12, font=dk.MONO)                 # measure IN MONO
        dk.text(s, x, y, w, h, [[(cmd, 12, dk.DEEP, False, False, dk.MONO)]])    # place
  · colours passed to set_font / box(line=) / anything typed RGBColor must BE RGBColor, not "RRGGBB".
    box(fill=) and box(grad=) do accept a hex string. When unsure, wrap: RGBColor.from_string(h).
  · picture(slide, PATH, x, y, w, h, fit=…) takes the path SECOND — before the geometry, unlike
    every other placing helper. Passing it after w/h raises a `stat: path should be string … not
    float`, which reads as a broken file rather than a swapped argument.
  · value_fmt IS TWO DIALECTS, split by who renders the number. native_chart / native_dual_axis /
    native_donut / native_pareto hand it to POWERPOINT, so it is an EXCEL number-format code
    ('0.0%', '#,##0', '0.0"x"') — and native_chart raises a lecture if you pass '{...}'. sankey,
    iso_bars and the designed_charts recipes format in PYTHON, so there it is a format STRING
    ('{:.0f}', '{:.0%}'). Crossing them is silent on the sankey/iso side: the literal text
    '0%' is printed onto every node. Excel dialect for native_*, Python dialect for everything else.
  · ONE TYPE SIZE PER PARAGRAPH. lint_layout measures a paragraph's INK at its LARGEST run size, so
    a 38pt number inline with 10.5pt CJK is scored as multi-line 38pt text and "collides" with
    whatever sits below — while the frames themselves are provably fine. The fix is never a bigger
    gap; it is two blocks:
        y = place(x, y, [[("257万1,037", 38, …, FONT)]])          # the number
        place(x, y + 0.08, [[("人 · 在日外国劳动者", 10.5, …, EAFONT)]])   # its unit, separately
    Measured on one deck: 7 of the first 20 build-time criticals were this single mistake.
  · A COMPONENT OWNS ITS AXIS — never hand-derive one to overlay on it. dot_strip / dumbbell_board /
    timeline(spacing='value') reserve their own label gutter, so an axis_scale() you build from the
    same (x, w) does NOT land where theirs did. Measured: a 1.00 parity line computed that way was
    drawn to the RIGHT of the 1.18 dot — the chart contradicting its own numbers, and no lint can
    see it. Either set the component's `lo` to the threshold so the axis origin IS the reference
    (best — geometry becomes true by construction), or drop the overlay and say it in the caption.
  · highlight= SELECTS A SERIES; emphasize= selects a BAR. On a SINGLE-series column/bar chart
    highlight is a no-op that greys everything — which silently deletes a semantic-colour binding
    the whole page rests on. One series → emphasize=<category index>.
  · native_chart(kind="bar") plots the FIRST category at the BOTTOM. Feed the list ASCENDING for it
    to read as a descending ranking top-to-bottom. A ranking rendered upside down still lints clean.
  · source_note() anchors to the canvas floor and then LIFTS clear of whatever it finds — on a full
    page that walks it up INTO the content (measured: landed at y=3.88 on a 5.6in canvas, straight
    through a data row). On any dense page pass an explicit `y`, and reserve that strip when you
    compute the page's content bottom. Call it LAST either way.
  · A COLOUR TOKEN IS SCOPED TO ITS GROUND. A muted grey chosen for a light canvas measures ~3:1 on
    the dark bookend; a text-safe accent for the light ground measures ~2.9:1 on it. Keep a token
    per ground and resolve by ground (`mute_for(bg)`, `on(fill)`), never by name — the failure is
    invisible in the build and legible only in the render.
  · A HAND-MADE SHAPE KEEPS THE THEME SHADOW. add_shape() stamps <p:style> with the theme's soft
    drop shadow; `shadow.inherit = False` writes an empty effectLst that PowerPoint honours and
    LibreOffice IGNORES — so the render and the visual critic still see it. Pass every hand-made
    shape through deckkit._flat().
"""


# A RUNNABLE call per form component. Only 1 of 19 docstrings carried a copyable call, which is the
# gap between "form-selection.md told me to use a timeline" and "I hand-rolled a timeline out of box
# + text" — and a hand-rolled form re-introduces exactly the geometry the component guarantees away.
#
# Every one of these is EXECUTED by scripts/smoke_deckkit.py. A scaffold that does not run is worse
# than none: it is copied once, fails, and teaches that the tool cannot be trusted. The test is the
# guarantee; the author of this dict is not.
EXAMPLES = {
    # photo_backdrop() places the photo FULL-BLEED and returns the content rect on a solid panel
    # over the image's calmest region, plus the ink to use on it. `alt` is required and an alpha
    # under 0.88 raises: a scrim only dims linework, it does not remove it.
    "photo_backdrop": 'x, y, w, h, ink = dk.photo_backdrop(\n'
                      '    s, "skyline.png",\n'
                      '    alt="a city skyline under an open sky",\n'
                      '    credit="Photographer / CC BY-SA")     # placed INSIDE the panel\n'
                      'dk.text(s, x, y, w, 1.0, [[("The claim", 30, ink, True, False)]])\n'
                      '# panel="left"|"right"|"bottom" overrides the measurement;\n'
                      '# panel="none" gives the safe rect and an ink chosen from the image\'s own\n'
                      '# luminance - and then the contrast is yours to own.',

    # skeleton() RETURNS NAMED RECTS for one of the eight page ARCHITECTURES and paints nothing.
    # `plan_rhythm.py` proposes which kind each slide gets; this is how you build it.
    "skeleton": 'R = dk.skeleton(s, "split")            # statement split island dashboard\n'
                '                                       # band rail gallery full_bleed\n'
                'lx, ly, lw, lh = R["lead"]\n'
                'dk.box(s, lx, ly, lw, lh, fill=dk.DEEP)\n'
                'dk.text(s, lx + 0.25, ly + 0.2, lw - 0.5, lh - 0.4,\n'
                '        [[("the argument", 18, dk.WHITE, True, False)]])\n'
                'sx, sy, sw_, sh_ = R["support"]\n'
                'dk.text(s, sx, sy, sw_, sh_, [[("what qualifies it", 14, dk.DEEP, False, False)]])',
    # bento RETURNS RECTS and paints nothing — the shape most likely to be got wrong, because
    # every other form component in this dict draws. Written as a loop so the return value is
    # visibly the thing you build from.
    "bento": 'for i, (bx, by, bw, bh) in enumerate(\n'
             '        dk.bento(s, 0.6, 1.2, 8.8, 3.9,\n'
             '                 [(2, 2), (2, 1), (1, 1), (1, 1), (4, 1)], cols=4)):\n'
             '    dk.box(s, bx, by, bw, bh, fill=dk.DEEP if i == 0 else dk.TINT)\n'
             '    dk.text(s, bx + 0.2, by + 0.15, bw - 0.4, bh - 0.3,\n'
             '            [[("tile %d" % i, 16 if i else 22,\n'
             '               dk.WHITE if i == 0 else dk.DEEP, i == 0, False)]])',
    # qr_panel needs a PRE-RENDERED png unless segno/qrcode is installed; `size` is held to the
    # 10:1 scan rule and the caption/URL are sized from the CANVAS, not from the code.
    "qr_panel": 'dk.qr_panel(s, 0.7, 2.4, 1.8, "https://example.org/preprint",\n'
                '            caption="Scan for the preprint",\n'
                '            contact="you@lab.nl", image="qr.png")',
    "timeline": 'dk.timeline(s, 0.7, 2.0, 8.6, [("1979", "first"), ("2026", "now", "caption")],\n'
                '            highlight=1)',
    # the counts must BALANCE: 250 - (40 + 12) = 198, and 198 - (9 + 5) = 184. Change one number
    # and it raises with the sum — that refusal is the component, not the boxes.
    "consort_flow": 'dk.consort_flow(s, 0.6, 1.1, 8.8, 3.9, [\n'
                    '    ("Assessed for eligibility", 250,\n'
                    '     [("Did not meet criteria", 40), ("Declined", 12)]),\n'
                    '    ("Randomised", 198,\n'
                    '     [("Lost to follow-up", 9), ("Withdrew consent", 5)]),\n'
                    '    ("Analysed", 184, []),\n'
                    '])',
    # NAVIGATION. A long deck is answered from its appendix, and a backup slide you cannot reach
    # live is one you did not prepare. `targets=` wires the contents page to the slides it names.
    "agenda": 'a1, a2, a3 = (dk.add_slide(prs) for _ in range(3))\n'
              'dk.agenda(s, 0.7, 1.6, 6.6,\n'
              '          ["Where we were", "What changed", "What is left"],\n'
              '          active=1, targets=[a1, a2, a3])   # active= is also the progress page',
    "back_link": 'home = dk.add_slide(prs)\n'
                 'dk.back_link(s, home, label="Back to agenda")   # width is measured from the label',
    "link": 'q = dk.box(s, 0.7, 3.4, 3.2, 0.5, fill=None, line=dk.DEEP)\n'
            'backup = dk.add_slide(prs)\n'
            'dk.link(q, backup)                       # a shape JUMPS to a slide\n'
            'run = dk.text(s, 0.7, 4.1, 5, 0.4,\n'
            '              [[("Preprint", 12, dk.DEEP, False, False, dk.FONT)]]\n'
            '              ).text_frame.paragraphs[0].runs[0]\n'
            'dk.link(run, "https://doi.org/10.1000/xyz")   # a RUN opens a URL',
    # CITATIONS. The reference line is DERIVED from the .bib entry, never retyped beside it.
    "reference_page": 'import citations as cit\n'
                      'db = cit.parse_bibtex(open("refs.bib", encoding="utf-8").read())\n'
                      'keys = ["lustig2007", "schlemper2018"]        # in CITED order\n'
                      'cit.reference_page(s, [db[k] for k in keys], style="numeric")\n'
                      '# the marker that goes on the slide, for key i (1-based):\n'
                      '# cit.in_text(db[keys[0]], "numeric", 1)  ->  "[1]"',
    "set_link_color": 'dk.set_link_color(prs, dk.DEEP)   # links in the deck ink, not Word-blue',
    "stat_row": 'dk.stat_row(s, 0.7, 2.0, 8.6, [("8", "x", "faster"), ("99", "%", "coverage")])',
    "step_list": 'dk.step_list(s, 0.8, 1.0, 8.0, [("Collect", "gather the inputs"),\n'
                 '                                ("Train", "fit the model")])',
    "segmented_bar": 'dk.segmented_bar(s, 0.8, 2.0, 8.4, 0.5, [46, 30, 24],\n'
                     '                 labels=["Cloud", "Devices", "Other"])',
    # tiers are LABEL STRINGS; `values=` is the SEPARATE display kwarg — and when numeric it is what
    # makes the taper value-proportional, which is the whole guarantee. Passing (label, value) tuples
    # paints "('Visitors', '12k')" onto the band: tier_stack renders each tier with str(lab).
    "tier_stack": 'dk.tier_stack(s, 1.0, 1.0, 6.0, 3.4,\n'
                  '              ["Visitors", "Trials", "Paid"], values=[12000, 3000, 410],\n'
                  '              mode="funnel")',
    "leaderboard": 'dk.leaderboard(s, 0.6, 1.0, 5.0,\n'
                   '               [(dk.ACCENTS[0], "alpha", 42), (dk.ACCENTS[1], "beta", "18", "sub")])',
    "scorecard": 'dk.scorecard(s, 0.6, 1.0, 2.5, 1.8, "Users", 1234, delta="3.2pp")',
    "meter_bar": 'dk.meter_bar(s, 0.6, 2.0, 4.7, 0.62, value="62%")',
    "dot_strip": 'dk.dot_strip(s, 0.6, 2.0, 8.0, [("A", 70), ("B", 100), ("C", 180)], 0, 200)',
    # cells is cells[row][col] = criteria x options, and 0..4 in the default ball mode
    "eval_matrix": 'dk.eval_matrix(s, 0.8, 1.6, 8.4, ["Option A", "Option B"],\n'
                   '               ["speed", "cost", "risk"],\n'
                   '               [[4, 2], [3, 4], [1, 3]], recommend=1)',
    "heat_matrix": 'dk.heat_matrix(s, 1.2, 1.4, 6.2, 3.2, [[10, 20, 30], [40, 50, 60]],\n'
                   '               ["r1", "r2"], ["c1", "c2", "c3"], scale="div")',
    "table": 'dk.table(s, 0.6, 1.5, 6.0, [["Metric", "Value"], ["Dice", "0.91"]], highlight=1)',
    "native_chart": 'dk.native_chart(s, 0.6, 1.0, 6.0, 3.2, ["Q1", "Q2", "Q3"],\n'
                    '                [("revenue", [3, 5, 4])], kind="column")',
    "org_tree": 'dk.org_tree(s, 0.6, 0.6, 8.8, 4.4,\n'
                '            ("CEO", [("Eng", [("Web", [])]), ("Sales", [])]))',
    "position_map": 'dk.position_map(s, 0.8, 0.8, 8.4, 4.2,\n'
                    '                [("A", 1, 1), ("B", 9, 8), ("C", 5, 2)], highlight=1)',
    "image_grid": 'dk.image_grid(s, *dk.content_band(s),\n'
                  '              images=[["gt_c1.png", "zf_c1.png", "ours_c1.png"],\n'
                  '                      ["gt_c2.png", "zf_c2.png", "ours_c2.png"]],\n'
                  '              col_labels=["Reference", "Zero-filled", "Ours"],\n'
                  '              row_labels=["Case 01", "Case 02"],\n'
                  '              metrics=[["--", "26.1", "34.6"], ["--", "25.4", "33.9"]],\n'
                  '              highlight_col=2, caption="PSNR (dB), 8x undersampled")',
    "small_multiples": 'dk.small_multiples(s, 0.6, 0.6, 8.8, 4.2,\n'
                       '                   [("A", [1, 2, 3]), ("B", [2, 2, 2]), ("C", [1, 5, 9])],\n'
                       '                   categories=["x", "y", "z"], highlight=2)',
    "iso_bars": 'dk.iso_bars(s, 0.8, 1.4, 8.4, 3.4, [10, 90, 40],\n'
                '            labels=["a", "b", "c"], highlight=1)',
    "iso_stack": 'dk.iso_stack(s, 0.6, 1.1, 9.0, 4.0,\n'
                 '             [("Base", "x"), ("Mid", "y"), ("Top", "z")])',
    "iso_prism": 'dk.iso_prism(s, 2.0, 4.0, 1.2, 1.2, 1.0, "3E6E9E")',
    "sankey": 'dk.sankey(s, 0.5, 1.1, 9.0, 3.8,\n'
              '          [("Capital", "LabA", 100), ("Capital", "LabB", 30),\n'
              '           ("LabA", "Compute", 100), ("LabB", "Compute", 30)],\n'
              '          value_fmt="${:.0f}B", col_labels=["out", "labs", "back"])',
    "venn": 'dk.venn(s, 0.6, 1.1, 5.2, 4.0, ["Fast", "Cheap", "Good"],\n'
            '        zones={"123": "pick two"})',
    "unit_grid": 'dk.unit_grid(s, 0.6, 1.7, 8.8, 3.2, 34, "1 square = 1 attributed painting",\n'
                 '             filled=34, fill="A63A2A")',
    "source_note": 'dk.source_note(s, "Crunchbase Q1 2026", as_of="30 July 2026")',
    # SKILL.md's 🔴 "when a COMPONENT exists, BUILD that component" rule names waterfall, gantt and
    # dumbbell_board BY NAME. They had no scaffold, and --example answered "it is a primitive — you
    # supply the geometry", i.e. the tool told the author to do the one thing the rule forbids.
    "gantt": 'dk.gantt(s, 0.6, 1.4, 8.8,\n'
             '         [("Design", 0, 3), ("Build", 2, 7), ("Ship", 7, 9)],\n'
             '         axis_min=0, axis_max=10, ticks=[0, 2.5, 5, 7.5, 10],\n'
             '         tick_labels=["Q1", "Q2", "Q3", "Q4", ""], today=6)',
    # rows = (name, sub, v_before, v_after, scale_lo, scale_hi, unit) — SEVEN items, per-row scale
    "dumbbell_board": 'dk.dumbbell_board(s, 0.6, 1.4, 8.8,\n'
                      '                  [("Latency", "p95", 120, 48, 0, 140, "ms"),\n'
                      '                   ("Cost", "per run", 90, 61, 0, 100, "$")])',
    "funnel": 'dk.funnel(s, 1.0, 1.0, 6.0, 3.4,\n'
              '          ["Visitors", "Trials", "Paid"], values=[12000, 3000, 410])',
    "pyramid": 'dk.pyramid(s, 1.0, 1.0, 6.0, 3.4,\n'
               '           ["Vision", "Strategy", "Execution"])',
    # designed_charts forms render a transparent PNG you then place with dk.picture(fit="contain").
    # `dc` is `import designed_charts as dc`; the path is yours.
    "waterfall": 'dc.waterfall("waterfall.png",\n'
                 '             [("Start", 120), ("Q1", 25), ("Q2", -12), ("", None)],\n'
                 '             total_label="End")\n'
                 'dk.picture(s, "waterfall.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    "distribution": 'dc.distribution("dice.png",\n'
                    '                [("baseline", [0.81, 0.86, 0.79, 0.9, 0.84]),\n'
                    '                 ("ours", [0.88, 0.92, 0.9, 0.94, 0.89])],\n'
                    '                value_label="Dice", highlight=1)\n'
                    'dk.picture(s, "dice.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    "marimekko": 'dc.marimekko("mix.png", [("EU", 5, [3, 2]), ("US", 9, [4, 5])],\n'
                 '             ["hardware", "services"], width_label="$B")\n'
                 'dk.picture(s, "mix.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    "radar": 'dc.radar("profile.png", ["speed", "cost", "risk", "reach", "effort"],\n'
             '         [("baseline", [2, 4, 3, 2, 5]), ("ours", [5, 3, 2, 4, 3])],\n'
             '         axis_range=(0, 5), highlight=1)\n'
             'dk.picture(s, "profile.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    # The four clinical / evidence recipes. Each one's DEFAULT is the thing a hand-roll gets wrong
    # (a linear axis for ratios, a line for survival, a correlation for agreement, a stretched ROC).
    # 🔴 Every number below is a PLACEHOLDER — an effect size, interval, survival time or AUC on a
    # slide comes from the source, never from a scaffold.
    "forest_plot": '# placeholder numbers: every estimate and interval comes from the source\n'
                   'dc.forest_plot("forest.png",\n'
                   '               [("Trial A", 0.82, 0.61, 1.10, 120),\n'
                   '                ("Trial B", 0.74, 0.55, 0.99, 200)],\n'
                   '               summary=("Pooled", 0.77, 0.63, 0.94), xlabel="Hazard ratio")\n'
                   'dk.picture(s, "forest.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    "km_curve": '# placeholder data: times and events (1 = event, 0 = censored) come from the source\n'
                'dc.km_curve("km.png", [\n'
                '    ("Control", [3, 5, 8, 12, 15, 20], [1, 1, 0, 1, 1, 0]),\n'
                '    ("Treated", [6, 9, 14, 18, 24, 30], [1, 0, 1, 0, 1, 0]),\n'
                '], xlabel="Months")\n'
                'dk.picture(s, "km.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    "bland_altman": '# placeholder data: one pair of measurements per subject, from the source\n'
                    'dc.bland_altman("agreement.png",\n'
                    '                [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],\n'
                    '                [10.5, 10.8, 12.4, 12.9, 14.6, 14.8, 16.7, 16.9, 18.5, 19.1],\n'
                    '                names=("MRI", "CT"))\n'
                    'dk.picture(s, "agreement.png", 0.8, 1.2, 8.4, 3.6, fit="contain")',
    "roc_curve": '# placeholder data: true labels and model scores come from the source\n'
                 'dc.roc_curve("roc.png",\n'
                 '             [("Model", [0, 0, 1, 1, 0, 1], [0.1, 0.4, 0.35, 0.8, 0.2, 0.7])])\n'
                 'dk.picture(s, "roc.png", 2.6, 1.0, 4.8, 4.3, fit="contain")   # keep it square',
    # The editorial forms. frosted_panel RETURNS the content rect and the ink measured on the
    # glass; mark() is a run, used INSIDE a text() paragraph; the ornaments are motif-tagged.
    "frosted_panel": 'bd = dk.picture(s, "skyline.png", 0, 0, 10, 5.625, fit="cover",\n'
                     '                alt="a city skyline under an open sky")\n'
                     'x, y, w, h, ink = dk.frosted_panel(s, bd, 5.4, 0.8, 4.0, 2.2)\n'
                     'dk.text(s, x, y, w, h, [[("The claim", 24, ink, True, False)]],\n'
                     '        anchor=dk.MSO_ANCHOR.MIDDLE)',
    "mark": 'dk.text(s, 0.6, 0.6, 8.8, 1.6, [[\n'
            '    ("BUILD THE SMALLEST ", 36, dk.DEEP, True, False),\n'
            '    dk.mark(("OBJECT", 36, dk.DEEP, True, False), "D4FF3A"),\n'
            '    (" THAT ASKS A QUESTION", 36, dk.DEEP, True, False)]])',
    # picture(shape=) clips a photo to an editorial form; focus aims the cover crop.
    "picture": 'dk.picture(s, "skyline.png", 0.6, 0.8, 2.6, 2.6, fit="cover", shape="ellipse",\n'
               '           focus=(0.5, 0.0), alt="a city skyline under an open sky")\n'
               '# shape="arch"|"snip"|"notch"|"blob"; rotation=-4 tilts a pinned print',
    "scribble": 'import ornaments as orn\n'
                'orn.scribble(s, 0.6, 3.6, 3.6, 1.0, "1A1A1A", loops=3, seed=2)   # a pen coil',
    "brush_stroke": 'import ornaments as orn\n'
                    'orn.brush_stroke(s, 0.6, 1.2, 4.2, 0.8, "F2C230", seed=4)    # the swash first\n'
                    'n = dk.text(s, 0.9, 1.3, 3.8, 0.6, [[("ONE NUMBER", 28, dk.DEEP, True, False)]])\n'
                    'dk.overlap_intent(n, "the number sits on its brush swash")',
    "scallop": 'import ornaments as orn\n'
               'orn.scallop(s, 7.4, 1.0, 1.5, "2F5BEA")\n'
               'n = dk.text(s, 7.4, 1.0, 1.5, 1.5, [[("12", 36, dk.WHITE, True, False)]],\n'
               '            align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE)\n'
               'dk.overlap_intent(n, "the count sits on its badge")   # declared on the TEXT',
    "use": 'import visual_languages as vl\n'
           'k = vl.use("drafting", prs, ground="auto")       # ink · poster · cutpaper · drafting: no pictures needed\n'
           'k.cover(k.new_slide(), kicker="Schematic 01", title="A modular bike shelter", project="Bike shelter, phase 1")\n'
           'k.section(k.new_slide(), number="01", title="The frame")\n'
           'k.points(k.new_slide(), title="Three parts", items=[("Base", "One cast plate."), ("Posts", "Bolted, not welded."), ("Roof", "A single sheet.")])\n'
           'k.quote(k.new_slide(), quote="Build the quiet part first.", attribution="Design note")\n'
           'k.data(k.new_slide(), number="12", label="bikes under one roof")\n'
           'k.closing(k.new_slide(), title="Questions", line="Thank you.")\n'
           's = k.new_slide()                                 # an ORDINARY page in the same look\n'
           'import register_surface as rs\n'
           'x, y, w, h = rs.ground(s, k.name, role="content", index=7)   # k.name, never another language\'s\n'
           'rows = ["1.  Why a shelter", "2.  How it is built"]\n'
           'size = 24 * min(prs.slide_width.inches, prs.slide_height.inches) / 7.5   # scaled with the canvas\n'
           'rows_h = sum(dk.measure_text([(r, False)], w - 0.8, size, font=k.face("body")) + 0.18 for r in rows)\n'
           'body, hdr = rs.card(s, k.name, x, y + max(0.0, (h - rows_h - 1.1) / 2), w, rows_h + 1.1, label="Agenda")\n'
           'top = hdr.top.inches + hdr.height.inches + 0.2 if hdr else body.top.inches + 0.45   # below the label\n'
           'dk.text(s, body.left.inches + 0.4, top, body.width.inches - 0.8, rows_h, [k.runs(r, size) for r in rows],\n'
           '        space_after=8)                            # k.runs: the language\'s own face and ink',
    "points": 'import visual_languages as vl\n'
              'k = vl.use("ink", prs)                         # or "poster" / "cutpaper" / "drafting" — no pictures needed\n'
              'k.points(k.new_slide(), title="三道工序",\n'
              '         items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")], seal="序")',
    "ink_ridges": 'import native_art as na\n'
                  'na.ink_ridges(s, color="1D1C1A", layers=na.INK_LAYERS["land"], keep_clear=[(7.0, 0.5, 1.0, 3.0)])',
    "clipped_block": 'import native_art as na\n'
                     'na.clipped_block(s, 7.0, 3.0, 4.0, 4.0, -9, fill="D7FF3B")   # a rotated block, cut to the page',
    "slot_picture": 'import image_series as ims\n'
                    'plan = ims.load("series.json")                 # validated by: image_series.py check\n'
                    'ims.slot_picture(s, plan, "hero", 0.6, 0.6, 3.2, 4.2, image_dir=".")   # arch + alt + +gen tag',
    "chroma_cutout": 'import image_fx\n'
                     'cut = image_fx.chroma_cutout("subject_on_key.png", key="00FF00")   # a generated subject on a flat key\n'
                     'dk.picture(s, cut, 1.0, 0.6, 3.0, 3.0, fit="contain", alt="the subject, cut out")',
    "feather": 'import image_fx\n'
               'f = image_fx.feather("skyline.png", radius=0.1)       # edges fade into the ground\n'
               'dk.picture(s, f, 1.0, 0.6, 8.0, 4.4, fit="contain", alt="a city skyline")',
    "grain_background": 'import surfaces\n'
                        'surfaces.grain_background(s, "F3EBDD", strength=5)   # a paper ground; text stays crisp\n'
                        'dk.text(s, 0.8, 0.8, 8, 1, [[("On paper", 28, dk.DEEP, True, False)]])',
    "stacked": 'import display_type as dt\n'
               'dt.stacked(s, 0.6, 0.6, 5.0, ["BRING IT", "BROKEN"], color=dk.DEEP, face="Impact")',
    "two_tone": 'import display_type as dt\n'
                'dt.two_tone(s, 0.6, 0.6, 8.0, 1.2, "Bring it broken.", ["broken."], size=40,\n'
                '            color=dk.DEEP, accent=dk.RGBColor(0xB2, 0x3A, 0x28), face="Georgia")',
    "outlined": 'import display_type as dt\n'
                'if dt.covers("Arial Black", "07"):   # installed here AND draws every character (else: boxes)\n'
                '    dt.outlined(s, 0.6, 0.6, 3.0, 2.0, "07", color="B23A28", face="Arial Black")   # a hollow number\n'
                'else:                                # no such face here (Linux): set the number as text\n'
                '    dk.text(s, 0.6, 0.6, 3.0, 2.0, [[("07", 96, dk.DEEP, True, False, "Arial Black")]])',
    "collage": 'import collage\n'
               'collage.collage(s, (5.0, 0.4, 4.6, 4.8), ["skyline.png", "gt_c1.png", "ours_c1.png"],\n'
               '                seed=3, keep_clear=(0.4, 0.6, 4.2, 2.4))   # tilted prints + tape',
    "vl_cover": 'import visual_languages as vl\n'
                'k = vl.use("editorial", prs)               # fonts="both": faces on macOS AND Windows\n'
                'pg = k.new_slide()\n'
                'k.cover(pg, title="Bring it broken, take it home working", kicker="A repair café", image="skyline.png")',
    "sticker_outline": 'import image_fx\n'
                       'st = image_fx.sticker_outline("cutout.png")      # needs a transparent cut-out\n'
                       'dk.picture(s, st, 6.6, 0.6, 2.6, 3.4, fit="contain", alt="a cut-out subject")',
    "a11y_title": 'dk.text(s, 0.6, 3.6, 8.8, 1.0, [[("Bring it broken, take it home working", 34, dk.DEEP, True, False)]])\n'
                  'dk.a11y_title(s, "Bring it broken, take it home working")   # the title screen readers navigate by',
    "decorative": 'import ornaments as orn\n'
                  't = orn.tape(s, 6.0, 4.4, 1.6, 0.42, "F2D16B")     # pale tape on the page ground\n'
                  'dk.decorative(t, "washi tape is ornament; no meaning rides on seeing it")',
    "squiggle": 'import ornaments as orn\n'
                'dk.text(s, 0.6, 0.6, 6.0, 0.8, [[("The claim", 30, dk.DEEP, True, False)]])\n'
                'orn.squiggle(s, 0.7, 1.45, 3.4, 0.3, "E5483B")   # under the claim',
    "tape": 'import ornaments as orn\n'
            'pic = dk.picture(s, "skyline.png", 3.0, 1.2, 3.6, 2.7, fit="cover", rotation=-3,\n'
            '                 alt="a city skyline under an open sky")   # a pinned print\n'
            'orn.tape(s, 4.1, 0.98, 1.4, 0.4, "F2D16B", holds=pic)   # holding it to the page',
}


def load():
    out = {}
    for m in MODULES:
        try:
            mod = __import__(m)
        except Exception as e:                       # a broken import must not look like a missing name
            print(f"sigs: cannot import {m} ({type(e).__name__}: {e})", file=sys.stderr)
            continue
        for name, fn in vars(mod).items():
            if name.startswith("_") or not inspect.isfunction(fn):
                continue
            if getattr(fn, "__module__", None) != m:  # skip re-exports, keep each helper's real home
                continue
            out.setdefault(name, (m, fn))
    # The visual-language page functions are METHODS of the kit `visual_languages.use()` returns. They were
    # invisible here, so `sigs.py cover` answered with deckkit.cover — a different call — and `section`,
    # `quote`, `data` resolved to nothing (a docs-only run, 2026-10-04). Listed as Kit.<name>.
    try:
        import visual_languages as _vl
        for name, fn in vars(_vl.Kit).items():
            if not name.startswith("_") and inspect.isfunction(fn):
                out.setdefault("Kit." + name, ("visual_languages", fn))
    except Exception as e:
        print(f"sigs: cannot list the visual-language kit ({type(e).__name__}: {e})", file=sys.stderr)
    return out


# Guarantees for forms that have a scaffold but are NOT in component_audit.FORM_GUARANTEE (that
# dict drives the geometry audit's EMITTERS set, so adding names to it changes what the audit
# suppresses — a separate concern from what --example prints). Without these, --example printed the
# filler "a form component" while SKILL.md promises "plus the guarantee it makes".
_EXTRA_GUARANTEES = {
    "points": "2 to 4 points, measured; a roomier layout is tried before anything is refused, never truncated; "
              "vertical only for CJK text (ink), one iso layer per point (drafting), one icon per point when icons= "
              "is given (cutpaper)",
    "ink_ridges": "ridges fade into mist and never pass the page; over every keep_clear rect the crest stays "
                  "below the text, falling away on a shoulder rather than a cliff",
    "clipped_block": "drawn as its polygon cut to the page, so PowerPoint's editing view shows nothing past "
                     "the slide edge",
    "slot_picture": "the slot's own frame shape, focus and alt text from series.json (the keyed PNG for a "
                    "cut-out), tagged +gen.<slot> — the tag the image-series delivery gate reads from "
                    "the saved file",
    "gantt": "every bar keyed to ONE shared axis_scale, so durations are comparable across lanes",
    "dumbbell_board": "a per-row scale, and direction-aware value labels placed OUTWARD so they "
                      "cannot collide with the dumbbell",
    "funnel": "a taper whose band width tracks value/max — a 5% tier is drawn at 5%, not clamped "
              "up to a legible minimum that would contradict its own label",
    "pyramid": "the same value-proportional taper as funnel, narrow-top-first",
    "waterfall": "floating step bars on the running cumulative, with rises/falls/totals coloured "
                 "distinctly and no increment double-counted against its own total",
    "distribution": "the SPREAD, not just the mean — every observation overlaid, n printed, and a "
                    "refusal below n=3 rather than a bar that hides the sample",
    "marimekko": "cell AREA = the absolute quantity (width = size, height = its split), which a "
                 "100%-stacked bar throws away",
    "radar": "zero-anchored spokes on a shared range, so profile area is not inflated by a "
             "cropped axis",
    "forest_plot": "a LOG axis for ratios by default (0.5 and 2 read as the same size of effect), "
                   "every interval checked to contain its own estimate, and the pooled estimate "
                   "drawn as a diamond",
    "km_curve": "survival computed from raw times and events and drawn as a STEP — the estimate "
                "changes only at an observed event — with censoring ticks and numbers at risk",
    "bland_altman": "the bias and 95% limits of agreement (bias ± 1.96·SD of the differences), "
                    "drawn and labelled — agreement, not a correlation; unpaired or too-short data "
                    "is refused",
    "roc_curve": "a square canvas with the chance diagonal and the AUC computed from raw labels and "
                 "scores; a single-class or non-binary outcome is refused",
    "agenda": "one row per section with the active one accented, and — with `targets=` — every row "
              "wired as a real PowerPoint slide jump, so the contents page works while presenting; "
              "a targets list that does not match the items is refused rather than half-wired",
    "back_link": "a chip whose width is MEASURED from its label (and widened when the label's face "
                 "does not resolve here, where the measurement is a stand-in's), so the label never "
                 "wraps through the chip's own edge",
    "reference_page": "every line and every marker derived from the SAME .bib entry, so a retyped "
                      "year cannot drift; an entry with no author/title/year is REFUSED rather "
                      "than printed with `n.d.`; each DOI is clickable in the deck's own ink",
    "set_link_color": "the DECK's hyperlink colour, because a renderer paints a linked run in the "
                      "theme's hlink colour whatever fill the run itself carries",
    "frosted_panel": "the blur is the picture region really under the panel, and the ink clears "
                     "4.5:1 against the glass's dark and light ends at the lightest wash that "
                     "allows it — or it refuses",
    "mark": "the highlight is a run property, so it follows the glyphs through every wrap, and an "
            "ink under WCAG on it is refused",
    "link": "a slide jump or a URL, with the scheme checked — a link target can come from the "
            "material the deck was built from, and javascript:/file:/data: in a delivered deck is "
            "somebody else's machine",
}


def _guarantee(name):
    """The one geometric promise the component makes and a hand-roll loses, or None."""
    if name in _EXTRA_GUARANTEES:
        return _EXTRA_GUARANTEES[name]
    try:
        import component_audit
        return component_audit.FORM_GUARANTEE.get(name)
    except Exception:
        return None


def show(name, mod, fn, full=False):
    try:
        sig = str(inspect.signature(fn))
    except (TypeError, ValueError):
        sig = "(signature unavailable)"
    if name.startswith("Kit."):                  # a method of the kit: k = visual_languages.use("<name>", prs)
        sig = sig.replace("(self, ", "(", 1).replace("(self)", "()", 1)
        print(f"\n{'─' * 78}\n{name}{sig}    # k = visual_languages.use(\"<language>\", prs); k.{name[4:]}(...)")
    else:
        print(f"\n{'─' * 78}\n{mod}.{name}{sig}")
    doc = inspect.getdoc(fn) or "(no docstring)"
    if full:
        print("\n" + doc)
        return
    # the head of a docstring is the "what is this for" line; the rest is usually parameter detail
    para = doc.split("\n\n")
    print("\n" + para[0].strip())
    if len(para) > 1:
        rest = " ".join(" ".join(para[1:]).split())
        print(f"\n{rest[:420]}{' …  (--full for all)' if len(rest) > 420 else ''}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print exact call contracts for slide-maker helpers.")
    ap.add_argument("names", nargs="*", help="helper names, e.g. text box native_chart")
    ap.add_argument("--search", metavar="TERM",
                    help="find helpers whose name or docstring contains TERM (plain text, any case); "
                         "'a|b' matches either word")
    ap.add_argument("--full", action="store_true", help="print whole docstrings")
    ap.add_argument("--list", action="store_true", help="list every helper name")
    ap.add_argument("--example", action="store_true",
                    help="print a RUNNABLE call for each named form component")
    a = ap.parse_args(argv)
    reg = load()
    if not reg:
        print("sigs: no helpers found — is this running from the skill's scripts/ dir?", file=sys.stderr)
        return 2

    if a.list:
        for m in MODULES:
            names = sorted(n for n, (mm, _f) in reg.items() if mm == m)
            print(f"\n{m} ({len(names)}):")
            for i in range(0, len(names), 5):
                print("  " + "  ".join(f"{n:<22}" for n in names[i:i + 5]))
        return 0

    if a.search:
        # 'a|b' (or grep-style 'a\\|b') is EITHER word. It was one literal substring, so an agent
        # that searched the way it greps found nothing and was told so (measured 2026-10-03).
        import re as _re
        terms = [t_.strip() for t_ in _re.split(r"\\?\|", a.search.lower()) if t_.strip()] or [""]
        hits = [(n, m, f) for n, (m, f) in reg.items()
                if any(q in n.lower() or q in (inspect.getdoc(f) or "").lower() for q in terms)]
        if not hits:
            print(f"sigs: nothing matches {a.search!r}")
            return 1
        for n, m, f in sorted(hits):
            show(n, m, f, a.full)
        print(f"\n{len(hits)} match(es).")
        return 0

    if not a.names:
        ap.print_help()
        return 2

    if a.example:
        # a page name (`section`) is the kit's page function, as on the plain lookup path
        a.names = [n if (n in EXAMPLES or n in reg or "Kit." + n not in reg) else "Kit." + n for n in a.names]
        miss = [n for n in a.names if n not in EXAMPLES]
        for n in a.names:
            if n in EXAMPLES:
                g = _guarantee(n)
                print(f"\n# {n}" + (f" — {g}" if g else "") + f"\n{EXAMPLES[n]}")
        # A real helper with no scaffold is NOT a licence to hand-roll it — that is the exact
        # failure this tool exists to prevent, and SKILL.md's 🔴 component rule forbids it by name.
        # Only a name that resolves to no helper at all is "you supply the geometry".
        for n in miss:
            if n in reg:
                m, f = reg[n]
                print(f"sigs: no copy-paste scaffold for {n!r} yet — its signature and docstring "
                      f"are below. Build the COMPONENT from them; do NOT hand-roll a substitute "
                      f"out of box/text (SKILL.md Step 4, 🔴 component rule)."
                      + (" A whole deck in a visual language, every page called: --example use."
                         if n.startswith("Kit.") else ""), file=sys.stderr)
                show(n, m, f, a.full)
            else:
                near = difflib.get_close_matches(n, reg, n=3, cutoff=0.6)
                print(f"sigs: no helper named {n!r}"
                      + (f" — did you mean {', '.join(near)}?" if near else
                         " — check `--list` before you build it yourself"), file=sys.stderr)
        # 🔴 The contracts print on the --example path TOO. They used to not, and that made
        # --example a STRICTLY WORSE lookup than the plain one it was meant to shortcut:
        # `sigs.py text` printed 68 lines including "RGBColor vs hex"; `sigs.py --example text`
        # printed 9 and dropped every contract. Measured: a build script written from --example
        # output died on `ValueError: assigned value must be type RGBColor` — one of the three
        # contracts this block exists to state, withheld by the flag whose whole purpose is
        # saving the round-trip that error then costs. A scaffold shows the SHAPE of one call;
        # the contracts are what stop the call being wrong in a way no lint can see.
        print("\n" + "─" * 78)
        print(CONTRACTS)
        # 1 only for a name that resolves to NO helper: a helper whose signature printed is an answer, and a
        # non-zero exit after printing it read as total failure (non-Claude run, 2026-10-05)
        return 1 if any(n not in reg for n in miss) else 0

    missing = []
    for n in a.names:
        kit = "Kit." + n if not n.startswith("Kit.") else None
        if n in reg:
            m, f = reg[n]
            show(n, m, f, a.full)
            if kit and kit in reg:               # two helpers share the name — say which is which
                print(f"\n(also: {kit}, the visual-language page function — a different call)")
                show(kit, *reg[kit], a.full)
        elif kit and kit in reg:
            show(kit, *reg[kit], a.full)
        else:
            missing.append(n)
    print("\n" + "─" * 78)
    print(CONTRACTS)
    if missing:
        for n in missing:
            near = difflib.get_close_matches(n, reg, n=3, cutoff=0.6)
            print(f"sigs: no helper named {n!r}"
                  + (f" — did you mean {', '.join(near)}?" if near else
                     " — check `--list`, and do NOT hand-roll it before checking"), file=sys.stderr)
        return 1
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
