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

MODULES = ("deckkit", "designed_charts")

# The two call-shape errors that actually cost round-trips on a real build. They are properties of
# the API that no single signature line states, so they are printed with every lookup rather than
# left in one helper's docstring where only that helper's reader would find them.
CONTRACTS = """\
CALL-SHAPE CONTRACTS (the two that have actually gone wrong):
  · a text RUN is (text, size, color, bold, italic[, font])  — font is the SIXTH item. Runs live in
    paragraphs: text(slide, x, y, w, h, [[run, run], [run]]) is TWO paragraphs.
  · colours passed to set_font / box(line=) / anything typed RGBColor must BE RGBColor, not "RRGGBB".
    box(fill=) and box(grad=) do accept a hex string. When unsure, wrap: RGBColor.from_string(h).
"""


# A RUNNABLE call per form component. Only 1 of 19 docstrings carried a copyable call, which is the
# gap between "form-selection.md told me to use a timeline" and "I hand-rolled a timeline out of box
# + text" — and a hand-rolled form re-introduces exactly the geometry the component guarantees away.
#
# Every one of these is EXECUTED by scripts/smoke_deckkit.py. A scaffold that does not run is worse
# than none: it is copied once, fails, and teaches that the tool cannot be trusted. The test is the
# guarantee; the author of this dict is not.
EXAMPLES = {
    "timeline": 'dk.timeline(s, 0.7, 2.0, 8.6, [("1979", "first"), ("2026", "now", "caption")],\n'
                '            highlight=1)',
    "stat_row": 'dk.stat_row(s, 0.7, 2.0, 8.6, [("8", "x", "faster"), ("99", "%", "coverage")])',
    "step_list": 'dk.step_list(s, 0.8, 1.0, 8.0, [("Collect", "gather the inputs"),\n'
                 '                                ("Train", "fit the model")])',
    "segmented_bar": 'dk.segmented_bar(s, 0.8, 2.0, 8.4, 0.5, [46, 30, 24],\n'
                     '                 labels=["Cloud", "Devices", "Other"])',
    "tier_stack": 'dk.tier_stack(s, 1.0, 1.0, 6.0, 3.4,\n'
                  '              [("Visitors", "12k"), ("Trials", "3k"), ("Paid", "410")],\n'
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
    return out


def _guarantee(name):
    """The one geometric promise the component makes and a hand-roll loses."""
    try:
        import component_audit
        return component_audit.FORM_GUARANTEE.get(name, "a form component")
    except Exception:
        return "a form component"


def show(name, mod, fn, full=False):
    try:
        sig = str(inspect.signature(fn))
    except (TypeError, ValueError):
        sig = "(signature unavailable)"
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
    ap.add_argument("--search", metavar="TERM", help="find helpers whose name or docstring matches")
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
        q = a.search.lower()
        hits = [(n, m, f) for n, (m, f) in reg.items()
                if q in n.lower() or q in (inspect.getdoc(f) or "").lower()]
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
        miss = [n for n in a.names if n not in EXAMPLES]
        for n in a.names:
            if n in EXAMPLES:
                print(f"\n# {n} — {_guarantee(n)}\n{EXAMPLES[n]}")
        for n in miss:
            print(f"sigs: no scaffold for {n!r}"
                  + (" (it is a primitive — you supply the geometry)" if n in reg else ""),
                  file=sys.stderr)
        return 1 if miss else 0

    missing = []
    for n in a.names:
        if n in reg:
            m, f = reg[n]
            show(n, m, f, a.full)
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


if __name__ == "__main__":
    sys.exit(main())
