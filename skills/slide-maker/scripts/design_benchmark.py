#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_benchmark — design-strength numbers for one built deck, so decks can be compared side by side.

🔴 WHY THIS EXISTS. The gates hold correctness: numbers trace, text fits, contrast clears. None of them
says whether a deck got TIMID. Measured 2026-11-07 on a real 9-slide run: six interior pages shared one
"title + row of cards" skeleton, type drama was 3.3x against 5.0–11.8x on the gallery decks — and
lint's deck-level `distinct skeletons` still read 9 of 9. So this script reads the things a design
regression shows up in, from the built file, and prints them for a side-by-side comparison with the
twelve gallery decks (the user's baseline for "how bold this skill can be").

It is ADVISORY. Nothing here blocks a deck: run it after a large change to the skill, on runs built
from the same material, and compare.

    python3 scripts/design_benchmark.py <deck>.pptx [--renders DIR] [--json OUT.json]
    python3 scripts/design_benchmark.py --compare a.json b.json ...

Numbers (one dict, fixed keys):
    slides                 slide count
    type_drama             largest type ÷ body median (lint deck stats)
    size_tokens            distinct type sizes in the deck (lint deck stats)
    avg_occupancy          mean share of the canvas carrying anything (lint deck stats)
    skeleton_same_share    share of interior page PAIRS whose composition signatures fall under
                           composition_probe.SAME_COMPOSITION — high = one skeleton repeated
                           🔴 NOT a repetition detector on real decks yet: measured 2026-11-07 it
                           read the monotone 9-slide run (0.14) inside the gallery's range
                           (0.05–0.13), with or without the shared chrome subtracted — "title + a
                           row of 2, 3 or 4 cards" is one skeleton to a reader and several to the
                           geometry. Synthetic same/different decks separate; real ones do not.
    skeleton_mean_div      mean divergence over those pairs
    skeleton_pairs         how many pairs were measured (the cover is left out)
    card_dominance         lint's CARD DOMINANCE warning fired
    envelope_monoculture   lint's ENVELOPE MONOCULTURE warning fired
    picture_slides         share of slides carrying a picture
    chart_slides           share of slides carrying a chart
    standout               the biggest type on any slide ÷ the median of each slide's biggest type —
                           a deck with one page that shouts scores high, an even deck near 1

Geometry only, never measured text ink, so a Chinese deck reads exactly as an English one; works on
decks built without deckkit (the gallery decks carry no deckkit tags).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

KEYS = ("slides", "type_drama", "size_tokens", "avg_occupancy", "skeleton_same_share",
        "skeleton_mean_div", "skeleton_pairs", "card_dominance", "envelope_monoculture",
        "picture_slides", "chart_slides", "standout")


def _lint(pptx_path, render_dir=None):
    """lint_deck's JSON report for the deck (run as a command, the way an agent runs it)."""
    with tempfile.TemporaryDirectory(prefix="design-bench-") as td:
        out = os.path.join(td, "lint.json")
        cmd = [sys.executable, str(HERE / "lint_deck.py"), str(pptx_path), "--json", out]
        if render_dir:
            cmd += ["--renders", str(render_dir)]
        subprocess.run(cmd, capture_output=True, text=True)
        try:
            with open(out, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            raise SystemExit("[design_benchmark] lint_deck produced no report for {} — run "
                             "`python3 scripts/lint_deck.py {}` to see why.".format(pptx_path, pptx_path))


def _skeleton(pptx_path, n_slides):
    import composition_probe as CP
    sigs = [CP.signature(pptx_path, i) for i in range(1, n_slides)]       # slide 1 is the cover
    divs = [CP.divergence(a, b) for a, b in combinations(sigs, 2)]
    if not divs:
        return 0.0, 0.0, 0
    same = sum(1 for d in divs if d < CP.SAME_COMPOSITION)
    return round(same / len(divs), 3), round(statistics.mean(divs), 3), len(divs)


def metrics(pptx_path: str, render_dir: str | None = None) -> dict:
    """The numbers for one deck. Raises SystemExit with a plain message on a missing/unreadable file."""
    if not os.path.isfile(pptx_path):
        raise SystemExit("[design_benchmark] no such deck: {}".format(pptx_path))
    rep = _lint(pptx_path, render_dir)
    deck, per = rep.get("deck") or {}, rep.get("per_slide") or []
    warns = rep.get("stats_warnings") or []
    n = len(per)
    same, mean_div, pairs = _skeleton(pptx_path, n)
    tops = [s.get("max_pt") or 0 for s in per if s.get("max_pt")]
    med = statistics.median(tops) if tops else 0
    return {
        "slides": n,
        "type_drama": deck.get("type_drama"),
        "size_tokens": deck.get("size_tokens"),
        "avg_occupancy": deck.get("avg_occupancy"),
        "skeleton_same_share": same,
        "skeleton_mean_div": mean_div,
        "skeleton_pairs": pairs,
        "card_dominance": any(w.startswith("CARD DOMINANCE") for w in warns),
        "envelope_monoculture": any(w.startswith("ENVELOPE MONOCULTURE") for w in warns),
        "picture_slides": round(sum(1 for s in per if s.get("n_pic")) / n, 3) if n else 0.0,
        "chart_slides": round(sum(1 for s in per if s.get("n_chart")) / n, 3) if n else 0.0,
        "standout": round(max(tops) / med, 2) if med else 0.0,
    }


def compare(paths) -> str:
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows.append((os.path.basename(p), json.load(f)))
    name_w = max([len("deck")] + [len(n) for n, _ in rows])
    head = "deck".ljust(name_w) + "  " + "  ".join(k for k in KEYS)
    lines = [head]
    for name, m in rows:
        cells = []
        for k in KEYS:
            v = m.get(k)
            s = "yes" if v is True else "no" if v is False else "—" if v is None else str(v)
            cells.append(s.rjust(len(k)))
        lines.append(name.ljust(name_w) + "  " + "  ".join(cells))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", nargs="?")
    ap.add_argument("--renders")
    ap.add_argument("--json")
    ap.add_argument("--compare", nargs="+", metavar="JSON")
    a = ap.parse_args(argv)
    if a.compare:
        print(compare(a.compare))
        return 0
    if not a.deck:
        ap.print_usage()
        return 2
    try:
        m = metrics(a.deck, a.renders)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    text = json.dumps(m, ensure_ascii=False, indent=1)
    if a.json:
        Path(a.json).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a character, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
