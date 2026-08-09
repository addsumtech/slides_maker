#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""""Never hand-pick a y" was unfollowable for eight components, because none of them could be measured.

SKILL.md's layout rule is measure-or-anchor, and `vstack` takes `(height, draw)` pairs — so a
block can only join a measured layout if its height is knowable BEFORE it is placed. Audited:
173 public callables, 4 `measure_*` helpers. Everything else that grows with its content —
`takeaway_rail`, `table`, `timeline`, `chip`, `modbox`, `node` — had no way to answer "how tall
will this be?", so the only available technique was the one the rule forbids.

Two of them were not merely unmeasurable, they were already wrong:

  · `takeaway_rail` had NO height parameter and NO return value, and reserved a hard-coded 2.0in
    for its body. Measured: a 2.10in body overflowed by 0.10in, putting its ink at y=5.45 — inside
    the footer band, which starts at 5.12 — with `lint_layout` reporting clean.
  · `node`, the general box/connector builder every hand-built diagram uses, is below the 0.5 in²
    threshold at ordinary flowchart sizes, so it is not a "card" to the ESCAPES_CARD check. A
    label on a 1.2 x 0.35in node escaped its box by 0.55in above AND below, gates all clean.

So the helpers are not documentation: `chip`, `modbox`, `node` and `takeaway_rail` ENFORCE their
own measurement, exactly as `callout` has always enforced `measure_callout` — one formula, two
callers, no way to drift.

Every assertion here compares a helper against the REAL rendered geometry (`_ink_rect`), never
against its own arithmetic. That is the point: the first version of `measure_takeaway_rail`
agreed with itself perfectly and was under by 1.20x, because `line_h_factor` and `line_spacing`
are two multipliers and it passed only one.

Run:  python3 tests/test_measure_contracts.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import deckkit as dk                                                  # noqa: E402

PASS, FAIL = [], []
LONG = ("A much longer interpretation that keeps going well past what a two-inch box can hold, "
        "because the author had more to say about what this chart means for the decision in the "
        "room, and nobody measured it before placing the rail, and nothing in the pipeline asked.")


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def fresh():
    prs = dk.blank_deck()
    return prs, dk.add_slide(prs)


def ink_bottom(slide):
    bots = []
    for sh in slide.shapes:
        r = dk._ink_rect(sh, dk._bbox_in(sh))
        if r and r[0]:
            bots.append(r[0][1] + r[0][3])
    return max(bots) if bots else 0.0


def box_of(slide):
    """The non-text shape (the card the component drew)."""
    for sh in slide.shapes:
        if not (sh.has_text_frame and sh.text_frame.text):
            return sh
    return None


def main():
    print("measure contracts")
    dk.FONT, dk.MONO = "Helvetica Neue", "Menlo"      # installed here; keeps ink honest

    # ---- takeaway_rail: the measured defect --------------------------------------------
    for label, body in (("2 lines", "Two lines of interpretation that fit the rail."),
                        ("4 lines", "A longer interpretation that keeps going well past what a "
                                    "two-inch box can hold, because there was more to say."),
                        ("8 lines", LONG)):
        prs, s = fresh()
        bottom = dk.takeaway_rail(s, 6.2, 1.4, 3.2, "what to notice", "3.7x", body)
        real = ink_bottom(s)
        check("takeaway_rail (%s) returns a bottom at or below its real ink" % label,
              bottom is not None and bottom >= real - 1e-6, (bottom, real))
        check("...and is not wastefully over (within 0.05in)", abs(bottom - real) < 0.05,
              abs(bottom - real))
        check("...and measure_takeaway_rail agrees with what it drew (%s)" % label,
              abs(dk.measure_takeaway_rail("what to notice", "3.7x", body, 3.2)
                  - (bottom - 1.4)) < 1e-6)

    # ...and the label/hero bands wrap too. `check_param_reach.py` flagged both as "accepted and
    # never read", which was a BUG report, not a style note: a 34pt hero wrapping to 4 lines
    # overflowed its 0.9in box by 1.394in, ink running to y=4.03 through a body starting at 2.70.
    for hero in ("3.7x", "3.7x faster end-to-end", "3.7x faster end-to-end on the full cohort"):
        prs, s = fresh()
        bottom = dk.takeaway_rail(s, 6.2, 1.4, 3.2, "what to notice", hero, "Two lines that fit.")
        check("a %d-line hero is measured, not assumed"
              % dk._measure_lines([(hero, True)], 34, 3.2),
              bottom >= ink_bottom(s) - 1e-6, (bottom, ink_bottom(s)))
    # When label AND hero AND body all wrap, the rail genuinely needs 5.0in and does not fit —
    # and the point is that this is now SAYABLE. It reports OFF_CANVAS instead of quietly
    # overprinting itself, which is what the fixed-box version did.
    prs, s = fresh()
    bottom = dk.takeaway_rail(s, 6.2, 1.4, 3.2, "what to notice about this comparison in particular",
                              "3.7x faster end-to-end on the full cohort", LONG)
    codes = {f[2] for f in dk.lint_layout(prs, verbose=False)}
    check("an unfittable rail reports OFF_CANVAS rather than overprinting itself",
          bottom > 5.625 and "OFF_CANVAS" in codes, (bottom, codes))
    check("...and no two of its own bands overlap each other",
          "TEXT_OVERLAP" not in codes, codes)

    # the one-line case must be unchanged byte for byte — 0.30 + 0.04 + 0.90 + 0.06 = 1.30
    check("a one-line label+hero still reserves exactly the historical 1.30in",
          abs(dk.measure_takeaway_rail("what to notice", "3.7x", "x", 3.2)
              - (1.30 + 0.03 + dk.measure_text([("x", False)], 3.2, 14,
                                               line_h_factor=dk._LINT_LINE_H * 1.2))) < 1e-6)

    # a long MONO filename wraps in a narrow modbox; the strip has to have the room
    prs, s = fresh()
    dk.modbox(s, 0.6, 2.0, 1.2, 0.5, "Ingest", "a_very_long_module_filename.py", dk.BLUE)
    check("modbox measures its mono filename too",
          box_of(s).height / 914400.0
          >= dk.measure_modbox("Ingest", "a_very_long_module_filename.py", 1.2) - 1e-6)
    check("...and the result is clean",
          [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"] == [])

    # measure_table deliberately has NO header flag — a parameter that cannot change the answer
    import inspect
    check("measure_table refuses a no-op `header` argument",
          "header" not in inspect.signature(dk.measure_table).parameters,
          list(inspect.signature(dk.measure_table).parameters))

    # the original failure, end to end: a long rail must no longer reach the footer band
    prs, s = fresh()
    dk.footer(s, "tag", page=3)
    band_top = 5.625 - dk.FOOTER_BAND
    top = dk.content_band(s)[1]
    h = dk.measure_takeaway_rail("what to notice", "3.7x", LONG, 3.2)
    dk.takeaway_rail(s, 6.2, top, 3.2, "what to notice", "3.7x", LONG)
    check("a rail placed from the band top, sized by its measure, clears the footer",
          top + h <= band_top, (top + h, band_top))

    # ---- node: the component refuses to be too small for its label ---------------------
    prs, s = fresh()
    dk.node(s, 0.6, 2.0, 1.2, 0.35, "An extremely long node label that cannot possibly fit",
            sub="module.py")
    bx = box_of(s)
    drawn = bx.height / 914400.0
    check("a node too small for its label GROWS instead of leaking",
          drawn >= dk.measure_node("An extremely long node label that cannot possibly fit",
                                   "module.py", 1.2) - 1e-6, drawn)
    r = dk._ink_rect([x for x in s.shapes if x.has_text_frame and x.text_frame.text][0],
                     dk._bbox_in([x for x in s.shapes if x.has_text_frame and x.text_frame.text][0]))
    check("...and its ink now sits inside the node",
          r[0][1] >= 2.0 - 0.03 and r[0][1] + r[0][3] <= 2.0 + drawn + 0.03,
          (r[0][1], r[0][1] + r[0][3], 2.0 + drawn))

    prs, s = fresh()
    dk.node(s, 0.6, 2.0, 2.0, 0.9, "Short", sub="")
    check("a node with room to spare is left exactly as asked",
          abs(box_of(s).height / 914400.0 - 0.9) < 1e-6, box_of(s).height / 914400.0)

    ctr = dk.node(dk.add_slide(dk.blank_deck()), 0.6, 2.0, 1.2, 0.3, "A long label here")
    check("node still returns a centre (connectors depend on it)",
          isinstance(ctr, tuple) and len(ctr) == 2, ctr)

    # ---- chip / modbox: same rule, and their gates still agree -------------------------
    prs, s = fresh()
    dk.chip(s, 0.6, 2.0, 1.6, 0.4, "A Long Stage Name That Wraps", "two\nextra\nlines", dk.BLUE)
    drawn = box_of(s).height / 914400.0
    check("chip grows to fit its own title + sub",
          drawn >= dk.measure_chip("A Long Stage Name That Wraps", "two\nextra\nlines", 1.6) - 1e-6,
          drawn)
    check("...and the grown chip no longer trips ESCAPES_CARD",
          not [f for f in dk.lint_layout(prs, verbose=False) if f[2] == "ESCAPES_CARD"])

    prs, s = fresh()
    dk.modbox(s, 0.6, 2.0, 1.6, 0.5, "Data\nIngest\nLayer", "ingest.py", dk.BLUE)
    drawn = box_of(s).height / 914400.0
    check("modbox grows for a 3-line role",
          drawn >= dk.measure_modbox("Data\nIngest\nLayer", "ingest.py", 1.6) - 1e-6, drawn)
    check("...and the grown modbox no longer trips TEXT_OVERLAP",
          not [f for f in dk.lint_layout(prs, verbose=False) if f[2] == "TEXT_OVERLAP"])

    prs, s = fresh()
    dk.chip(s, 0.6, 2.0, 1.9, 1.2, "Input", "one line", dk.BLUE)
    check("a chip with room to spare keeps the height it was given",
          abs(box_of(s).height / 914400.0 - 1.2) < 1e-6)

    # a row of chips sized from the widest member comes out even — the documented use
    stages = [("Input", "one line"), ("Process", "two\nlines here"), ("Model", "one line")]
    ch = max(dk.measure_chip(t, sb, 1.9) for t, sb in stages)
    prs, s = fresh()
    for i, (t, sb) in enumerate(stages):
        dk.chip(s, 0.6 + i * 2.1, 2.0, 1.9, ch, t, sb, dk.BLUE)
    hs = {round(x.height / 914400.0, 4) for x in s.shapes if not (x.has_text_frame and x.text_frame.text)}
    check("a row sized from max(measure_chip) comes out one height", len(hs) == 1, hs)

    # ---- table / timeline: measurable before placing -----------------------------------
    rows = [["m", "a", "b"], ["x", "1", "2"], ["y", "3", "4"], ["z", "5", "6"]]
    prs, s = fresh()
    bottom = dk.table(s, 0.6, 1.6, 6.0, rows)
    check("measure_table matches where table says it ends",
          abs(dk.measure_table(rows) - (bottom - 1.6)) < 1e-6,
          (dk.measure_table(rows), bottom - 1.6))
    check("measure_table scales with row count",
          dk.measure_table(rows * 2) == dk.measure_table(rows) * 2)
    check("a custom row_h is honoured",
          abs(dk.measure_table(rows, row_h=0.5) - 2.0) < 1e-6, dk.measure_table(rows, row_h=0.5))

    events = [("2019", "Start"), ("2022", "Middle"), ("2026", "Now")]
    prs, s = fresh()
    bottom = dk.timeline(s, 0.6, 1.6, 8.8, events)
    check("measure_timeline matches where timeline says it ends (horizontal)",
          abs(dk.measure_timeline(events) - (bottom - 1.6)) < 1e-6,
          (dk.measure_timeline(events), bottom - 1.6))
    prs, s = fresh()
    bottom = dk.timeline(s, 0.6, 1.6, 8.8, events, orientation="v", h=2.4)
    check("...and vertical, where the height is the caller's",
          abs(dk.measure_timeline(events, orientation="v", h=2.4) - (bottom - 1.6)) < 1e-6,
          (dk.measure_timeline(events, orientation="v", h=2.4), bottom - 1.6))

    # ---- and the whole point: these blocks can now join a measured layout ---------------
    prs, s = fresh()
    dk.title_bar(s, "A page that packs three measured blocks", kicker="test")
    dk.footer(s, "tag", page=2)
    band = dk.content_band(s)
    blocks = [
        (dk.measure_table(rows), lambda x, y, w: dk.table(s, x, y, w, rows)),
        (dk.measure_timeline(events), lambda x, y, w: dk.timeline(s, x, y, w, events)),
    ]
    try:
        dk.vstack(s, band[0], band[1], band[2], blocks, gap=0.3, bottom=band[1] + band[3])
        crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
        check("a table and a timeline pack into one vstack with no CRITICAL", crit == [], crit)
    except Exception as exc:
        check("a table and a timeline pack into one vstack with no CRITICAL", False, repr(exc))

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
