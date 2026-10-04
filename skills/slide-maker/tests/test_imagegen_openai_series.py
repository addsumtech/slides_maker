#!/usr/bin/env python3
"""generate_images_openai: the METERED path must run an image series as faithfully as the Codex one.

Measured 2026-10-03: with the Codex account on a plan that has no image tool, the user authorised the
metered API for a series — and this script asked for every image at one fixed 2048x1152 landscape
size with no way to generate the key first or to hand the key to the others as a style reference. A
series run that way comes out landscape and unchained, and nothing says so. Run here through
--dry-run and the pure builders: no network, no spend.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import generate_images_openai as gio  # noqa: E402
from PIL import Image  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = gio.main(argv)
    return rc, buf.getvalue()


# without --size each slot's aspect picks the nearest size the API takes; an explicit --size wins for every item
check(gio._size_for({"aspect": 0.75}, None) == "1024x1536", "a 3:4 arch slot must ask for a portrait size")
check(gio._size_for({"aspect": 1.0}, None) == "1024x1024", "a square slot -> square")
check(gio._size_for({"aspect": 2.65}, None) == "2048x1152", "a wide band -> the widest size")
check(gio._size_for({"aspect": 1.45}, None) == "1536x1024", "a 3:2 slot -> 1536x1024")
check(gio._size_for({}, None) == gio.DEFAULT_SIZE, "no aspect and no --size -> the default size")
check(gio._size_for({"aspect": 0.75}, "2048x1152") == "2048x1152", "an explicit --size wins over the item aspect")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    man = td / "image_prompt_manifest.json"
    man.write_text(json.dumps([
        {"id": "hero", "slide": 1, "filename": "slide-01-hero.png", "aspect": 0.75, "prompt": "a lamp being repaired"},
        {"id": "tools", "slide": 2, "filename": "slide-02-tools.png", "aspect": 1.33, "prompt": "a tray of tools"}]),
        encoding="utf-8")
    rc, out = run([str(man), "--dry-run", "--only", "hero", "--out-dir", str(td)])
    check(rc == 0 and "slide-01-hero.png" in out and "slide-02-tools.png" not in out and "1024x1536" in out,
          "--only hero must plan only the key, at its own size: rc={} out={}".format(rc, out[-300:]))
    rc, out = run([str(man), "--dry-run", "--only", "nope", "--out-dir", str(td)])
    check(rc == 2 and "nope" in out, "--only with no match must refuse (exit 2)")
    rc, out = run([str(man), "--dry-run", "--style-ref", str(td / "missing.png"), "--out-dir", str(td)])
    check(rc == 2 and "missing.png" in out, "a missing --style-ref must refuse (exit 2)")
    Image.new("RGB", (64, 48), (120, 90, 60)).save(td / "slide-01-hero.png")
    rc, out = run([str(man), "--dry-run", "--style-ref", str(td / "slide-01-hero.png"), "--out-dir", str(td)])
    check("skip existing" in out and "slide-02-tools.png" in out and "style reference" in out.lower(),
          "existing key skipped, the rest planned WITH the style reference: " + out[-300:])
    # the multipart body the edits endpoint gets: every field, and the reference's own bytes
    body, ctype = gio._multipart({"model": "m", "prompt": "p"}, [("image[]", td / "slide-01-hero.png")])
    check(ctype.startswith("multipart/form-data; boundary=") and b'name="model"' in body and b'name="image[]"' in body
          and (td / "slide-01-hero.png").read_bytes() in body, "multipart body must carry fields and the file")
p = gio._with_style("a tray of tools")
check(p.startswith("a tray of tools") and "do not copy its subject" in p.lower(), "style instruction: " + p)
check("background" in p.lower() and "wins" in p.lower(), "the prompt's background must win: " + p)

# --only selects EXACTLY one item: with slots "hero" and "s04-hero", a suffix match picked both — the
# second then got made WITHOUT the style reference and was skipped as "existing" by the --style-ref run
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    m2 = td / "image_prompt_manifest.json"
    m2.write_text(json.dumps([
        {"id": "hero", "slide": 1, "filename": "slide-01-hero.png", "prompt": "a lamp on a workbench in a hall", "subject": "a lamp on a workbench"},
        {"id": "s04-hero", "slide": 4, "filename": "slide-04-s04-hero.png", "prompt": "a kettle on a counter in a kitchen", "subject": "a kettle on a counter"}]),
        encoding="utf-8")
    rc, out = run([str(m2), "--dry-run", "--only", "hero", "--out-dir", str(td)])
    check(rc == 0 and "slide-01-hero.png" in out and "slide-04-s04-hero.png" not in out,
          "--only hero must not also select s04-hero: " + out[-300:])
    m2.write_text(json.dumps([
        {"slide": 1, "filename": "slide-01-a-hero.png", "prompt": "a lamp on a workbench in a hall"},
        {"slide": 2, "filename": "slide-02-b-hero.png", "prompt": "a kettle on a counter in a kitchen"}]), encoding="utf-8")
    rc, out = run([str(m2), "--dry-run", "--only", "hero", "--out-dir", str(td)])
    check(rc == 2 and "matches 2" in out, "an --only that matches two items must refuse: rc={} {}".format(rc, out[-200:]))

# a series run prints the NEXT step (generation stubbed — no network, no spend)
import image_series as ims  # noqa: E402
_plan = {"art_direction": "warm documentary photography in a community hall, window light",
         "palette": ["F3EBDD", "C98A3D", "2F6F6A"], "render": "photo",
         "slots": [{"id": "hero", "slide": 1, "frame": {"shape": "rect", "w": 4, "h": 3}, "kind": "object",
                    "subject": "a table lamp being repaired on a wooden workbench", "alt": "a lamp",
                    "referent": "generic-concrete", "meaning": "broken things get fixed here, by neighbours"}]}
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    pp = td / "series.json"
    pp.write_text(json.dumps(_plan), encoding="utf-8")
    ims.prompts(_plan, td / "gen", plan_path=pp)
    man = td / "gen" / "image_prompt_manifest.json"
    real = gio._generate_item

    def _fake(item, out_path, args, api_key):
        Image.new("RGB", (64, 48), (120, 90, 60)).save(out_path)
        return out_path
    gio._generate_item = _fake
    import os  # noqa: E402
    os.environ["SM_TEST_KEY"] = "x"
    try:
        rc, out = run([str(man), "--only", "hero", "--api-key-env", "SM_TEST_KEY"])
        nxt = [l for l in out.splitlines() if l.startswith("NEXT")]
        check(rc == 0 and nxt and "generate_images_openai.py" in nxt[0] and "--style-ref" in nxt[0],
              "after the key, NEXT must be the metered --style-ref run: {}".format(nxt))
        def _boom(item, out_path, args, api_key):
            raise RuntimeError("HTTP 400: billing hard limit")
        gio._generate_item = _boom
        rc, out = run([str(man), "--only", "hero", "--overwrite", "--api-key-env", "SM_TEST_KEY"])
        nxt = [l for l in out.splitlines() if l.startswith("NEXT")]
        check(rc == 1 and nxt and "--only hero" in nxt[0], "a failed metered run must print the rerun command: {}".format(nxt))
    finally:
        gio._generate_item = real
        os.environ.pop("SM_TEST_KEY", None)

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_imagegen_openai_series] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
