#!/usr/bin/env python3
"""generate_images_codex: generate the KEY image alone, then the series with the key as a STYLE reference.

`--ref-dir` stages REAL photographs of a subject and tells codex "they show the REAL subject"; a series
needs the opposite instruction — match this image's look, NOT its subject — so the style reference has
its own flag and its own clause. Run here through --dry-run and the pure instruction builder: no codex.
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

import generate_images_codex as gic  # noqa: E402
from PIL import Image  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = gic.main(argv)
    return rc, buf.getvalue()


SUBJ = "a hand-thrown stoneware kettle with an ash glaze in soft window daylight on linen"
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    man = td / "image_prompt_manifest.json"
    items = [{"id": "hero", "slide": 1, "filename": "slide-01-hero.png", "prompt": SUBJ + " — hero"},
             {"id": "kettle", "slide": 3, "filename": "slide-03-kettle.png", "prompt": SUBJ + " — detail"}]
    man.write_text(json.dumps(items), encoding="utf-8")
    rc, out = run([str(man), "--dry-run", "--only", "hero"])
    check(rc == 0 and "slide-01-hero.png" in out and "slide-03-kettle.png" not in out,
          "--only hero must select only the key: rc={} out={}".format(rc, out[-300:]))
    rc, out = run([str(man), "--dry-run", "--only", "nope"])
    check(rc == 2 and "nope" in out, "--only with no match must refuse (exit 2) naming the id")
    # Review Focus 4: an existing key is skipped on the full run, and a missing style ref refuses
    Image.new("RGB", (64, 48), (120, 90, 60)).save(td / "slide-01-hero.png")
    rc, out = run([str(man), "--dry-run", "--style-ref", str(td / "slide-01-hero.png")])
    check("skip existing" in out and "slide-03-kettle.png" in out, "existing key skipped, rest planned")
    check("style reference" in out.lower(), "dry-run must say which style reference it will stage")
    rc, out = run([str(man), "--dry-run", "--style-ref", str(td / "missing.png")])
    check(rc == 2 and "missing.png" in out, "a missing --style-ref must refuse (exit 2) naming the file")
# the STYLE clause: match the look, NOT the subject — and never the REAL-subject wording
cl = gic.style_clause("_style-ref.png")
check("_style-ref.png" in cl and "do not copy its subject" in cl.lower(), "style clause wording: " + cl)
check("REAL subject" not in cl, "the style clause must not reuse the real-photo wording")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_imagegen_series_flags] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
