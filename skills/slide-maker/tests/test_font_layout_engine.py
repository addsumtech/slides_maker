#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every font the skill loads with Pillow is laid out by Pillow's BASIC engine.

WHY. Pillow 13.0.0 reached CI's Linux runner between two runs of an unchanged tree (2026-10-16), and
the native-languages suite crashed inside a width measurement — `RuntimeError: raqm_layout() failed`,
from `display_type._glyph_width`, reached from `visual_languages._flow`. The commit under test changed
one Markdown file. A font loaded without `layout_engine=` uses RAQM whenever libraqm is importable,
so whether a width could be measured at all depended on which wheel pip happened to fetch.

BASIC is also the engine every width in this skill was tuned against: the macOS wheels carry no
libraqm, so every measurement on the maintainers' machines — and in the Linux-font simulation — is a
BASIC measurement. RAQM shapes (kerning, ligatures), so the same words measured differently on the
two platforms even on the days it did not crash.

Two halves, because either alone is blind:
  * the SOURCE scan names any `ImageFont.truetype(...)` call without the keyword — including the
    ones a future change adds — and refuses to pass if it found no calls at all;
  * the BEHAVIOUR half loads fonts through the real helpers and reads the engine off the objects
    they return, which is what the scan cannot see (a keyword passed the wrong value).

Run: python3 tests/test_font_layout_engine.py
"""
import ast
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from PIL import ImageFont  # noqa: E402

PASS, FAIL = [], []


def check(ok, what):
    (PASS if ok else FAIL).append(what)
    if not ok:
        print("FAIL", what)


def truetype_calls(path):
    """Every `ImageFont.truetype(...)` call in a file, with whether it names `layout_engine`."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "truetype" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "ImageFont"):
            out.append((node.lineno, any(k.arg == "layout_engine" for k in node.keywords)))
    return out


# ── the source scan ─────────────────────────────────────────────────────────────────────────
found = 0
for py in sorted(SCRIPTS.rglob("*.py")):
    for line, named in truetype_calls(py):
        found += 1
        check(named, "{}:{} loads a font without layout_engine=ImageFont.Layout.BASIC".format(
            py.relative_to(SCRIPTS.parent), line))
check(found >= 9, "the scan found {} ImageFont.truetype calls — expected at least 9; if the loads moved "
                  "behind a helper, point this scan at the helper".format(found))

# ── the behaviour half ──────────────────────────────────────────────────────────────────────
import deckkit as dk  # noqa: E402
import display_type as dt  # noqa: E402

BASIC = ImageFont.Layout.BASIC

w = dt._glyph_width("Measured widths", 24, dk.FONT, False)
check(w is not None and w > 0, "display_type._glyph_width measured a width ({!r})".format(w))
engines = {getattr(f, "layout_engine", None) for f in dt._GW_FONTS.values()}
check(engines == {BASIC}, "display_type._glyph_width's fonts use BASIC (got {})".format(engines))

f = dk._pil_font(dk.FONT, 18)
check(getattr(f, "layout_engine", None) == BASIC,
      "deckkit._pil_font returns a BASIC font (got {})".format(getattr(f, "layout_engine", None)))

import crop_helper  # noqa: E402
import image_qc  # noqa: E402

for mod in (crop_helper, image_qc):
    fn = getattr(mod, "_font", None)
    if fn is None:
        continue
    try:
        got = fn(20)
    except TypeError:
        continue
    if isinstance(got, ImageFont.FreeTypeFont):
        check(got.layout_engine == BASIC, "{}._font returns a BASIC font (got {})".format(
            mod.__name__, got.layout_engine))

print("[test_font_layout_engine] {} passed, {} failed".format(len(PASS), len(FAIL)))
if FAIL:
    print("[test_font_layout_engine] FAILED: {} problem(s)".format(len(FAIL)))
    sys.exit(1)
print("[test_font_layout_engine] ok")
