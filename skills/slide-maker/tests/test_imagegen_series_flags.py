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
check("background" in cl.lower() and "prompt" in cl.lower() and "wins" in cl.lower(),
      "the prompt's background (a cut-out's flat key) must win over the reference's: " + cl)

# a series item states its OWN aspect in its prompt; the generator's --orientation default ("landscape",
# appended INSIDE the prompt) would contradict a tall arch. An item's own "orientation" wins.
check(gic._orientation_for({"orientation": "auto"}, "landscape") == "auto", "an item's orientation must win")
check(gic._orientation_for({}, "landscape") == "landscape", "no item orientation -> the CLI default")
check(gic._orient_clause(gic._orientation_for({"orientation": "auto"}, "landscape")) == "",
      "an 'auto' item gets no orientation clause")

# A generation that produced nothing must SAY WHY. Measured 2026-10-03: the ChatGPT account Codex was
# signed into had dropped to the FREE plan, which gives a codex session no image tool; the agent tried
# `tools.image_generation` / `tools.image_gen`, got "is not a function", answered TOOL_RETURNS_NO_FILE,
# and the script printed only "no image produced" — twice, with no cause.
with tempfile.TemporaryDirectory() as td:
    roll = Path(td) / "rollout.jsonl"
    roll.write_text("\n".join(json.dumps(r) for r in (
        {"type": "session_meta", "payload": {"id": "x"}},
        {"type": "event_msg", "payload": {"type": "token_count", "rate_limits": {"plan_type": "free"}}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "output": [
            {"type": "input_text", "text": "TypeError: tools.image_gen is not a function"}]}},
        {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [
            {"type": "output_text", "text": "TOOL_RETURNS_NO_FILE"}]}})) + "\n", encoding="utf-8")
    why = gic._why_no_image(roll)
    check(why and "free" in why.lower() and "codex login" in why, "a free-plan session must be named: {!r}".format(why))
    roll.write_text("\n".join(json.dumps(r) for r in (
        {"type": "event_msg", "payload": {"type": "token_count", "rate_limits": {"plan_type": "plus"}}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "output": [
            {"type": "input_text", "text": "TypeError: tools.image_gen is not a function"}]}})) + "\n", encoding="utf-8")
    why = gic._why_no_image(roll)
    check(why and "no image tool" in why.lower(), "a session with no image tool must say so: {!r}".format(why))
    roll.write_text(json.dumps({"type": "event_msg", "payload": {"type": "token_count",
                                "rate_limits": {"plan_type": "plus"}}}) + "\n", encoding="utf-8")
    check(gic._why_no_image(roll) is None, "no evidence -> no invented cause")
    check(gic._why_no_image(None) is None, "no transcript -> no invented cause")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_imagegen_series_flags] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
