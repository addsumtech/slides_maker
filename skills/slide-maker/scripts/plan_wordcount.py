#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_wordcount.py — plan-time twin of lint_deck's render-time TEXT WALL warn: measure each
slide's ON-SLIDE reading load (takeaway + content units) straight from the Content plan's
"Per-slide content" markdown table, BEFORE the user approves it — so a blown word budget is a
two-cell text edit at Step 1, not a slide split after design/build/render.

    python scripts/plan_wordcount.py <content-plan.md> [--presented|--selfread|--textheavy|--surface]

Thresholds sit BELOW the render lint's warn lines, because plan words are a SUBSET of rendered
words (design adds captions/labels): --presented warns > ~50 plan-words (nominal budget ~40;
lint warns >70) · --selfread warns > ~110 (nominal ~90; lint warns >120) · --textheavy and
--surface print per-slide loads but NEVER warn (mirroring lint_deck's TEXT WALL carve for both).
ADVISORY ONLY — over-budget rows get "over budget → notes/split" recorded in the plan's notes
column for the user to approve at the CONTENT checkpoint; a parse failure prints a note and
exits 0 (a broken table must never block the checkpoint). lint_deck's TEXT WALL is the
unchanged render-time backstop.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lint_deck import _text_load   # noqa: E402 — ONE source of truth: latin words + CJK chars/2


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    mode = "presented"
    for m in ("selfread", "textheavy", "surface", "presented"):
        if f"--{m}" in argv or f"--mode={m}" in argv:
            mode = m
            break
    if not args:
        print("usage: python plan_wordcount.py <content-plan.md> "
              "[--presented|--selfread|--textheavy|--surface]")
        return 0
    try:
        lines = open(args[0], encoding="utf-8").read().splitlines()
    except Exception as e:
        print(f"[plan-wordcount] note: cannot read {args[0]} ({e}) — advisory skipped")
        return 0
    rows = []                       # (#, takeaway, content units) from the Per-slide content table
    for ln in lines:
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0].isdigit():
            rows.append((int(cells[0]), cells[1], cells[3]))
    if not rows:
        print("[plan-wordcount] note: no per-slide table rows parsed — advisory skipped")
        return 0
    warn_at = {"presented": 50, "selfread": 110}.get(mode)
    print(f"  ── plan word budget (mode: {mode}) — plan-time, advisory ──")
    over = 0
    for num, takeaway, units in rows:
        load = _text_load(takeaway) + _text_load(units)
        flag = ""
        if warn_at is not None and load > warn_at:
            flag = (f"  [over budget >{warn_at} — trim, move prose to the Spoken thread / "
                    f"speaker notes, or split; record 'over budget → notes/split' in the row's notes]")
            over += 1
        print(f"    slide {num:2d}: plan load ~{load} words{flag}")
    if warn_at is None:
        print(f"    ({mode}: no plan-time word budget — loads printed for information only, "
              f"matching the render lint's TEXT WALL carve)")
    elif over:
        print(f"  [plan-wordcount] {over} slide(s) over the {mode} plan budget (~{warn_at}); "
              f"the render lint's TEXT WALL stays the backstop")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
