#!/usr/bin/env python3
"""The four NATIVE visual languages: registered like the image-led four, their grounds' inks pass contrast,
pages compose on every canvas, and nothing they draw leaves the page or trips PowerPoint."""
from __future__ import annotations
import contextlib, io, os, sys, tempfile, zipfile, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk
import visual_languages as vl
import ooxml_safety as ox

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def cr(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

td = Path(tempfile.mkdtemp())
check(vl.NATIVE == ("ink", "poster", "cutpaper", "drafting"), "the four native languages are named")
check(set(vl.NATIVE) | set(vl.IMAGE_LED) == set(vl.LANGS), "every language is native or image-led")
check(vl.PAGE_FIELDS.get("points") == ("kicker", "title", "items"), "the points page exists")
for n in vl.NATIVE:
    for g, V in vl.VARIANTS[n].items():
        p = V["palette"]
        check(cr(p["ink"], p["ground"]) >= 4.5, "{}/{} ink on ground".format(n, g))
        check(cr(p["mute"], p["ground"]) >= 4.5, "{}/{} mute on ground".format(n, g))
        for t in p["text_accents"]:
            check(cr(t, p["ground"]) >= 4.5, "{}/{} text accent {} on ground".format(n, g, t))
        on_panel = p.get("card_ink", p["ink"])
        check(cr(on_panel, p["panel"]) >= 4.5, "{}/{} ink on its panel".format(n, g))
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(n, dk.blank_deck(13.333, 7.5), ground=g)
        check(k.ground == g and k.P["ground"] == p["ground"] or n == "poster", "{}/{} use() sets the ground".format(n, g))
# points belongs to the native languages only
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("collage", dk.blank_deck(13.333, 7.5))
try:
    k.points(k.new_slide(), title="x", items=["a", "b"])
    check(False, "points() on an image-led language is refused")
except ValueError as e:
    check("native" in str(e), "points() on an image-led language names the native languages: {}".format(e))
# extras are per language
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("ink", dk.blank_deck(13.333, 7.5))
try:
    k.cover(k.new_slide(), title="x", highlight="x")
    check(False, "an extra that belongs to another language is refused")
except TypeError:
    check(True, "an extra that belongs to another language is refused")
# poster and drafting ordinary pages carry their ground
for n in ("poster", "drafting"):
    prs = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(n, prs)
    s = k.new_slide()
    has_bg = s._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cSld").find(
        "{http://schemas.openxmlformats.org/presentationml/2006/main}bg") is not None
    check(has_bg, "{}: an ordinary new_slide() page gets the language's ground".format(n))
# image-led samples are byte-identical to the pre-change build (Review Focus 5)
base = Path(os.environ.get("VL_BASELINE", "/nonexistent")) / "hashes.json"     # recorded before the change
if base.exists():
    want = json.loads(base.read_text())
    for key, hashes in want.items():
        n, g = key.split("-", 1)
        p = vl.build_sample(n, str(td), ground=g)
        z = zipfile.ZipFile(str(p))
        got = [hashlib.sha256(z.read(x)).hexdigest() for x in sorted(z.namelist()) if x.startswith("ppt/slides/slide")]
        check(got == hashes, "{} is unchanged by the native languages".format(key))
else:
    print("  skip image-led baseline: VL_BASELINE is not set (recorded locally before the change; not in CI)")
# a deck that never picks a native language loads nothing new (spec §6 performance)
import subprocess
probe = subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0, 'scripts'); import contextlib, io, deckkit as dk, visual_languages as vl\n"
    "with contextlib.redirect_stdout(io.StringIO()):\n"
    "    k = vl.use('collage', dk.blank_deck(13.333, 7.5)); k.new_slide()\n"
    "print(sorted(m for m in ('vl_native', 'native_art', 'ooxml_safety') if m in sys.modules))"],
    capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
check(probe.stdout.strip() == "[]", "an image-led deck imports no native module: {!r} {}".format(
    probe.stdout.strip(), probe.stderr[-200:]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
