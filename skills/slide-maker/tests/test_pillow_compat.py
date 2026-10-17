#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""No pixel read goes through Image.getdata(), which Pillow 14 removes (2027-10-15).

WHY. Pillow 12+ warns on every getdata() call ("deprecated and will be removed in Pillow 14 … Use
get_flattened_data instead"); the warning printed through a real deck's lint output (2026-10-17), and on
Pillow 14 the same calls raise AttributeError inside the lint, the image QC and the surface probes. The
replacement only exists from Pillow 12, while requirements.txt allows Pillow 10, so the reads go through
`pil_compat.pixels()`, which uses whichever the installed Pillow has.

Two halves: a SOURCE scan (no `.getdata(` call left anywhere but the helper — the next one added is named),
and the BEHAVIOUR of the helper (the same values as getdata() in every mode, and no deprecation warning).

Run: python3 tests/test_pillow_compat.py
"""
import ast
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


calls = []
for py in sorted(list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").glob("*.py"))):
    if py.name in ("pil_compat.py", "test_pillow_compat.py"):
        continue
    tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "getdata":
            calls.append("{}:{}".format(py.relative_to(ROOT), node.lineno))
check(not calls, "no Image.getdata() call outside pil_compat ({} left: {})".format(len(calls), calls[:6]))

try:
    from pil_compat import pixels
except ImportError as e:
    pixels = None
    bad.append("pil_compat.pixels is importable ({})".format(e))

if pixels is not None:
    from PIL import Image
    same = []
    for mode, px in (("RGB", (5, 6, 7)), ("RGBA", (5, 6, 7, 8)), ("L", 5), ("P", 5), ("I", 5), ("1", 1)):
        im = Image.new(mode, (3, 2))
        im.putpixel((1, 1), px)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ref = list(im.getdata())
        same.append(list(pixels(im)) == ref)
    check(all(same), "pixels() returns getdata()'s values in RGB, RGBA, L, P, I and 1 ({})".format(same))
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        try:
            list(pixels(Image.new("RGB", (2, 2))))
            check(True, "pixels() raises no deprecation warning on this Pillow")
        except DeprecationWarning as e:
            check(False, "pixels() raised a deprecation warning ({})".format(e))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
if bad:
    print("[test_pillow_compat] FAILED: {} problem(s)".format(len(bad)))
    sys.exit(1)
print("[test_pillow_compat] ok")
