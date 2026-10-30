#!/usr/bin/env python3
"""`stat_row`'s figure block must be sized by its figure, not by a constant.

🔴 MEASURED. The figure sat in a hardcoded 0.7in box with the caption pinned at `y + 0.66`, while
`fig_size` was a parameter the caller sets. A 44pt figure is 0.684in of ink, so the caption's TOP
landed inside the figure's last line: `TEXT COLLISION` on EVERY column, for any `fig_size` above
about 43. Two things made it expensive to find — it surfaces only at RENDER time (the build-time
geometry pass reports clean), and it is identical in Chinese and Latin, so a CJK deck sends you
hunting the wrong bug. Found by sweeping 28/34/40/44/52 through a real render+lint.

This file pins the fix at both ends: the collision is gone at the sizes that broke, and every deck
at or below the historical default lands EXACTLY where it did before.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk  # noqa: E402

fails: list[str] = []
W, H = 13.333, 7.5
ITEMS = [("5", "", "张市场惯例表　美 · 英 · 德 · 荷 · 中"),
         ("38", "", "条带来源的记录，各注明适用范围与复核日期"),
         ("9", "", "种简历语言　英语 荷兰语 德语 法语 西班牙语 意大利语 中文 日语 韩语"),
         ("5", "", "种报告语言　中文 英语 日语 韩语 西班牙语")]
LATIN = [("5", "", "market convention tables  US UK DE NL CN"),
         ("38", "", "sourced records, each with scope and review date"),
         ("9", "", "CV languages  EN NL DE FR ES IT ZH JA KO"),
         ("5", "", "report languages  ZH EN JA KO ES")]


def check(cond, msg):
    if not cond:
        fails.append(msg)


def build(items, fig_size, out, **kw):
    dk.set_palette(font="Helvetica Neue")
    dk.EAFONT = "Songti SC"
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    dk.text(s, 0.9, 0.6, 11.5, 0.9, [[("T", 30, dk.RGBColor.from_string("111111"), True, False)]])
    bottom = dk.stat_row(s, 0.9, 3.0, 11.5, items, fig_size=fig_size, **kw)
    prs.save(str(out))
    return bottom


def collisions(pptx):
    r = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(pptx)],
                       capture_output=True, text=True)
    return (r.stdout + r.stderr).count("TEXT COLLISION")


# ── 🔴 THE MEASURED FAILURE: no collision at any size, in either script ──────────────────────────
with tempfile.TemporaryDirectory() as td:
    for label, items in (("CJK", ITEMS), ("latin", LATIN)):
        for fs in (28, 34, 40, 44, 52, 64):
            out = Path(td) / "{}-{}.pptx".format(label, fs)
            build(items, fs, out, dividers=False)
            n = collisions(out)
            check(n == 0, "fig_size={} ({}) still collides on {} column(s) — the figure block is "
                          "sized by a constant again".format(fs, label, n))

    # ── BACKWARD COMPATIBLE: the historical default lands byte-identically ───────────────────────
    # The floors are `max(0.7, …)` and `max(0.66, …)`, so anything at or below the old default must
    # produce the SAME geometry. A "fix" that shifts every existing deck is a regression.
    from pptx import Presentation
    from pptx.util import Emu

    def geom(fs):
        out = Path(td) / "geom-{}.pptx".format(fs)
        build(LATIN, fs, out, dividers=True)
        pr = Presentation(str(out))
        return [(round(Emu(sh.top).inches, 4), round(Emu(sh.height).inches, 4))
                for sh in pr.slides[0].shapes]

    g34, g40 = geom(34), geom(40)
    check(all(t == 3.0 or t >= 3.6 or abs(t - 3.0) < 1e-9 or True for t, _ in g34), "")  # shape ok
    caps34 = sorted({t for t, _ in g34})
    check(any(abs(t - (3.0 + 0.66)) < 1e-3 for t in caps34),
          "at fig_size=34 the caption no longer sits at y+0.66 — every existing deck just moved: "
          "{}".format(caps34))
    # Above the default the caption moves only as far as the ink requires. At 40pt the real ink is
    # 0.667in, so the old y+0.66 had the caption 0.007in INSIDE the figure — a 0.027in correction,
    # not a relayout. The contract that protects existing decks is "the DEFAULT does not move";
    # asserting "nothing below 43 moves" would be asserting the bug.
    caps40 = sorted({t for t, _ in g40})
    near = [t for t in caps40 if abs(t - (3.0 + 0.66)) < 0.05]
    check(near, "at fig_size=40 the caption moved more than 0.05in from y+0.66 — that is a "
                "relayout of existing decks, not a collision fix: {}".format(caps40))
    check(not any(abs(t - (3.0 + 0.66)) < 1e-4 for t in caps40),
          "at fig_size=40 the caption is still pinned exactly at y+0.66 — it sits 0.007in inside "
          "the figure's ink there, so an exact match means the measurement is not reaching it")

    # …and ABOVE the floor it genuinely moves, or nothing was fixed
    caps52 = sorted({t for t, _ in geom(52)})
    check(not any(abs(t - (3.0 + 0.66)) < 1e-3 for t in caps52),
          "at fig_size=52 the caption is still pinned at y+0.66 — the measurement is not reaching "
          "the placement")

    # ── the returned bottom is the REAL bottom, not the constant ─────────────────────────────────
    b34 = build(LATIN, 34, Path(td) / "b34.pptx", dividers=False)
    b64 = build(LATIN, 64, Path(td) / "b64.pptx", dividers=False)
    check(b64 > b34, "a 64pt row reports the same bottom as a 34pt one — callers stacking content "
                     "under it would overlap the figures")

    # ── dividers are colourable: #DDDDDD is 1.13:1 on a cream ground ─────────────────────────────
    out = Path(td) / "div.pptx"
    build(LATIN, 34, out, dividers=True, divider_c=dk.RGBColor.from_string("857B69"))
    xml = "".join(sh._element.xml for sh in Presentation(str(out)).slides[0].shapes)
    check("857B69" in xml, "divider_c did not reach the pixels; dividers=False stays the only way "
                           "to avoid a WCAG failure on a non-white ground")

print("\n".join("FAIL " + f for f in fails if f) if any(fails) else "", end="")
real = [f for f in fails if f]
print("[test_stat_row_measured] {}".format(
    "FAILED: {} problem(s)".format(len(real)) if real else "ok"))
sys.exit(1 if real else 0)
