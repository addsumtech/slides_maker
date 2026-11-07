#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_benchmark.py — design-strength numbers for one built deck, so two decks can be compared.

Measured 2026-11-07: a real 9-slide run had six interior pages on one "title + row of cards" skeleton,
and lint's `distinct skeletons` still read 9 of 9 — the deck-level count could not see the repetition.
What this suite holds the script to:

  · a deck whose interior pages share one skeleton scores a HIGH skeleton_same_share, a deck of
    genuinely different pages a LOW one;
  · a deck built with plain python-pptx (no deckkit tags — the gallery decks are like this) still
    yields every key;
  · a portrait canvas (3:4 carousel) measures without breaking;
  · --compare prints the numbers of several decks side by side.

Run:  python3 tests/test_design_benchmark.py
"""
import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import pathlib
import subprocess
import sys
import tempfile

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import design_benchmark as DB  # noqa: E402

PASS, FAIL = [], []
KEYS = {"slides", "type_drama", "size_tokens", "avg_occupancy", "skeleton_same_share",
        "skeleton_mean_div", "card_dominance", "envelope_monoculture", "picture_slides",
        "chart_slides", "standout"}


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else f"{name}  {detail}")
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  {detail}"))


TMP = pathlib.Path(tempfile.mkdtemp(prefix="design-bench-"))


def _text(slide, x, y, w, h, s, pt):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    r = tb.text_frame.paragraphs[0].add_run()
    r.text, r.font.size = s, Pt(pt)
    return tb


def _rect(slide, x, y, w, h, rgb=(0xE8, 0xE4, 0xDC)):
    sh = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor(*rgb)
    sh.line.fill.background()
    return sh


def _deck(w=13.333, h=7.5):
    p = Presentation()
    p.slide_width, p.slide_height = Inches(w), Inches(h)
    return p


def _cover(p):
    s = p.slides.add_slide(p.slide_layouts[6])
    _text(s, 0.8, 2.6, 10, 1.6, "Annual review", 54)


def repetitive_deck(path):
    p = _deck()
    _cover(p)
    for i in range(6):
        s = p.slides.add_slide(p.slide_layouts[6])
        _text(s, 0.8, 0.5, 11, 0.8, "Point %d of the year" % (i + 1), 28)
        for c in range(3):
            _rect(s, 0.8 + c * 4.0, 1.8, 3.6, 3.2)
            _text(s, 1.0 + c * 4.0, 2.0, 3.2, 0.6, "Metric %d" % c, 16)
            _text(s, 1.0 + c * 4.0, 2.8, 3.2, 1.0, "%d,4%d0" % (c + 2, i), 36)
    p.save(path)


def varied_deck(path):
    p = _deck()
    _cover(p)
    s = p.slides.add_slide(p.slide_layouts[6])                     # one giant number, centred
    _text(s, 2.0, 1.6, 9.3, 3.0, "86%", 160)
    s = p.slides.add_slide(p.slide_layouts[6])                     # split: full-height block left
    _rect(s, 0, 0, 6.6, 7.5, (0x20, 0x30, 0x40))
    _text(s, 7.2, 2.4, 5.4, 2.4, "A paragraph on the right half explains the dark panel.", 20)
    s = p.slides.add_slide(p.slide_layouts[6])                     # chart-like: bars along the floor
    _text(s, 0.8, 0.5, 11, 0.8, "Twelve months", 28)
    for m in range(12):
        hh = 1.0 + (m % 5) * 0.8
        _rect(s, 0.9 + m * 1.0, 6.8 - hh, 0.6, hh, (0x2A, 0x7F, 0x62))
    s = p.slides.add_slide(p.slide_layouts[6])                     # a table across the page
    _text(s, 0.8, 0.5, 11, 0.8, "By department", 28)
    t = s.shapes.add_table(6, 4, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2)).table
    for r in range(6):
        for c in range(4):
            t.cell(r, c).text = "%d" % (r * 4 + c)
    s = p.slides.add_slide(p.slide_layouts[6])                     # a small quote low-left
    _text(s, 0.8, 5.2, 6.0, 1.2, "“We came for the data and stayed for the people.”", 24)
    s = p.slides.add_slide(p.slide_layouts[6])                     # tall strip right, label left
    _rect(s, 10.4, 0, 2.93, 7.5, (0xC8, 0x50, 0x3C))
    _text(s, 0.8, 0.8, 8.5, 1.0, "Next year", 40)
    p.save(path)


def portrait_deck(path):
    p = _deck(7.5, 10)
    _cover(p)
    for i in range(3):
        s = p.slides.add_slide(p.slide_layouts[6])
        _text(s, 0.6, 0.6, 6.3, 1.0, "Step %d" % (i + 1), 32)
        _rect(s, 0.6, 2.0 + i, 6.3, 3.0)
    p.save(path)


# ───────────────────────────────────────────── skeleton repetition
print("── skeleton repetition")
rep, var, por = TMP / "rep.pptx", TMP / "var.pptx", TMP / "por.pptx"
repetitive_deck(str(rep))
varied_deck(str(var))
portrait_deck(str(por))

m_rep = DB.metrics(str(rep))
m_var = DB.metrics(str(var))
check("every key is present", KEYS <= set(m_rep), sorted(KEYS - set(m_rep)))
check("repetitive deck: skeleton_same_share >= 0.8", m_rep["skeleton_same_share"] >= 0.8,
      m_rep["skeleton_same_share"])
check("varied deck: skeleton_same_share <= 0.3", m_var["skeleton_same_share"] <= 0.3,
      m_var["skeleton_same_share"])
check("the cover is not counted (7 slides, 6 interior pages -> 15 pairs measured)",
      m_rep["slides"] == 7 and m_rep.get("skeleton_pairs") == 15, (m_rep["slides"], m_rep.get("skeleton_pairs")))
check("standout: the giant number stands out more than the repetitive deck's biggest figure",
      m_var["standout"] > m_rep["standout"], (m_var["standout"], m_rep["standout"]))

# ───────────────────────────────────────────── inputs the gallery decks look like
print("── untagged and portrait decks")
check("untagged plain python-pptx deck yields every key", KEYS <= set(m_var), sorted(KEYS - set(m_var)))
m_por = DB.metrics(str(por))
check("portrait canvas measures: 0 <= skeleton_same_share <= 1",
      0.0 <= m_por["skeleton_same_share"] <= 1.0, m_por["skeleton_same_share"])
check("no pictures and no charts in these decks", m_var["picture_slides"] == 0 and m_var["chart_slides"] == 0,
      (m_var["picture_slides"], m_var["chart_slides"]))

# ───────────────────────────────────────────── CLI
print("── CLI")
a, b = TMP / "a.json", TMP / "b.json"
r1 = subprocess.run([sys.executable, str(SCRIPTS / "design_benchmark.py"), str(rep), "--json", str(a)],
                    capture_output=True, text=True)
r2 = subprocess.run([sys.executable, str(SCRIPTS / "design_benchmark.py"), str(var), "--json", str(b)],
                    capture_output=True, text=True)
check("CLI exits 0 and writes JSON", r1.returncode == 0 and a.is_file() and r2.returncode == 0,
      (r1.returncode, r1.stderr[-400:]))
if a.is_file():
    check("JSON carries the same keys", KEYS <= set(json.loads(a.read_text(encoding="utf-8"))))
rc = subprocess.run([sys.executable, str(SCRIPTS / "design_benchmark.py"), "--compare", str(a), str(b)],
                    capture_output=True, text=True)
check("--compare prints a table naming both files and type_drama",
      rc.returncode == 0 and "a.json" in rc.stdout and "b.json" in rc.stdout and "type_drama" in rc.stdout,
      rc.stdout[-400:] + rc.stderr[-400:])
bad = subprocess.run([sys.executable, str(SCRIPTS / "design_benchmark.py"), str(TMP / "missing.pptx")],
                     capture_output=True, text=True)
check("a missing deck is a clear error, not a traceback",
      bad.returncode != 0 and "Traceback" not in bad.stderr and "missing.pptx" in (bad.stderr + bad.stdout),
      bad.stderr[-300:])

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
