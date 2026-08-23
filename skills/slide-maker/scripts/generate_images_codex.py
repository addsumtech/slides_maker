#!/usr/bin/env python3
"""Generate slide visual plates from image_prompt_manifest.json via the **Codex CLI** — no API key.

For Codex / ChatGPT-subscription users who don't want to provide an OpenAI API key: this shells out
to `codex exec`, which calls Codex's hosted **image_generation** tool (a stable, on-by-default
feature). The generated image lands as base64 in the Codex session rollout
(`~/.codex/sessions/.../rollout-*.jsonl`, an `image_generation_call` payload); the agent decodes it
to the target PNG, and this script verifies it (with a rollout-extraction fallback).

A drop-in alternative to generate_images_openai.py with the SAME manifest format:
    [{"slide": 1, "filename": "hero.png", "prompt": "...", "path"?: "..."}, ...]

Prereqs: the `codex` CLI installed and logged in (`codex login`); image_generation enabled
(default — check `codex features list`). Slower than the API (one agent turn per image) and the
hosted tool steers size by prompt, so this script asks for the requested orientation in the prompt.
"""
import argparse
import base64
import concurrent.futures as _cf
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SESSIONS = Path.home() / ".codex" / "sessions"


def _default_concurrency():
    """How many `codex exec` image jobs to run at once.

    The old default was a flat 2, described as "safe" — but the work each job does is almost
    entirely WAITING on a hosted image model, not burning a local core, so 2 left a multi-image
    deck serialised against nothing. Scaling with the machine keeps the old behaviour on a small
    box (a 4-core CI runner still gets 2) while a workstation stops queueing. Capped at 4 because
    the constraint above ~4 stops being local and becomes the service's own rate limit, which this
    script cannot see — `--concurrency 1` remains the escape hatch when a batch starts erroring."""
    try:
        cores = os.cpu_count() or 4
    except Exception:
        cores = 4
    return max(2, min(4, cores // 3))

INSTR = (
    "Generate ONE image using your hosted image_generation tool (the 'image_generation' feature is "
    "enabled — it is NOT a local model and NOT PIL). Pass the EXACT text between the <IMAGE_PROMPT> "
    "markers to the tool as the image prompt — VERBATIM: do not paraphrase, summarize, translate, "
    "shorten, embellish, or fold any of these file-handling instructions into it.\n"
    "<IMAGE_PROMPT>\n{prompt}{orient}\n</IMAGE_PROMPT>\n\n"
    "It MUST be a generated illustration — do NOT draw it with PIL/code and do NOT search for local "
    "model files. The tool's base64 result appears in your session rollout JSONL as an "
    "'image_generation_call' payload; decode that base64 and write the raw bytes to ./{fname} in the "
    "current working directory, then run `ls -l ./{fname}`. Reply only 'OK' when the file exists, or "
    "'TOOL_RETURNS_NO_FILE' if the hosted tool truly returns nothing saveable."
)


def _have_codex():
    return shutil.which("codex") is not None


# How stale a rollout may be and still plausibly be THIS run's. A generation that just happened is
# seconds old; anything older is a different session's transcript and reading it is not this
# script's business.
_ROLLOUT_MAX_AGE_S = 30 * 60
_SESSION_ENV = ("CODEX_SESSION_ID", "CODEX_ROLLOUT_PATH", "CODEX_THREAD_ID")


def _newest_rollout(*, quiet=False):
    """The rollout holding THIS run's image, scoped as tightly as the host lets us.

    A Codex session rollout is a full transcript — prompts, tool output, file paths. This script
    needs exactly one thing out of it: the base64 in an `image_generation_call`. It used to take
    the newest `rollout-*.jsonl` under ~/.codex/sessions with no scoping at all, so on a machine
    with several sessions it could open an UNRELATED session's transcript. Three limits now:

      1. an explicit session pointer from the environment wins, when the host provides one;
      2. otherwise the newest file must be recent enough to plausibly be this run's;
      3. whichever file is used is NAMED on stderr, so reading a transcript is never silent.

    `_extract_from_rollout` still only ever pulls the image payload — no other field is read out,
    and nothing from the file is echoed.
    """
    for var in _SESSION_ENV:
        hint = os.environ.get(var, "").strip()
        if not hint:
            continue
        p = Path(hint).expanduser()
        if p.is_file():
            return p
        for cand in SESSIONS.rglob(f"rollout-*{hint}*.jsonl"):
            return cand
    try:
        files = sorted(SESSIONS.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    if not files:
        return None
    newest = files[0]
    try:
        age = time.time() - newest.stat().st_mtime
    except OSError:
        return None
    if age > _ROLLOUT_MAX_AGE_S:
        if not quiet:
            print(f"generate_images_codex: newest rollout is {int(age // 60)} min old — too stale "
                  f"to be this run's, not reading it. Pass the image path directly, or set "
                  f"{_SESSION_ENV[0]}.", file=sys.stderr)
        return None
    if not quiet:
        print(f"generate_images_codex: reading the image payload from {newest} "
              f"(image_generation_call only; no other field is read).", file=sys.stderr)
    return newest


def _extract_from_rollout(rollout, out_path):
    """Fallback: pull the LAST image_generation_call base64 from a rollout JSONL and write it."""
    if not rollout or not rollout.exists():
        return False
    b64 = None
    for line in rollout.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue
        payload = rec.get("payload") or {}
        if rec.get("type") == "response_item" and payload.get("type") == "image_generation_call":
            res = payload.get("result")
            if isinstance(res, str) and len(res) > 100:
                b64 = res
    if not b64:
        return False
    try:
        out_path.write_bytes(base64.b64decode(b64))
        return True
    except Exception:
        return False


def _valid_image(path):
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return True  # Pillow absent → trust the size check


def _orient_clause(orientation):
    # appended INSIDE the verbatim <IMAGE_PROMPT> block, so it steers the generation (not plumbing)
    if orientation == "landscape":
        return " Wide 16:9 landscape composition (a hero/divider plate)."
    if orientation == "portrait":
        return " Tall portrait composition."
    return ""


def _generate_one(prompt, out_path, *, orientation, timeout):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    instr = INSTR.format(prompt=prompt, fname=out_path.name, orient=_orient_clause(orientation))
    cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write",
           "-c", 'approval_policy="never"', instr]
    before = _newest_rollout(quiet=True)   # baseline marker only; the real read announces itself
    try:
        subprocess.run(cmd, cwd=str(out_path.parent), stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        pass
    except Exception as exc:
        print(f"  codex exec error: {exc}", file=sys.stderr)
    if _valid_image(out_path):
        return True
    roll = _newest_rollout()                       # fallback: decode straight from this run's rollout
    if roll and roll != before:
        _extract_from_rollout(roll, out_path)
    return _valid_image(out_path)


def _resolve_out(item, out_dir):
    return Path(out_dir) / item["filename"] if out_dir else Path(item.get("path") or item["filename"])


# Words that carry STYLE or COLOUR rather than subject matter. A prompt built only from these
# produces art that could sit under any deck -- which is precisely the FUSION gate's failure mode
# (`generated-template.md`: "beautifully on-style but topically generic FAILS"). That gate is prose
# and nothing read it, so a generic prompt cost a generation, a render and a review round before a
# human noticed. This checks the PROMPT, before the spend. It cannot judge the resulting pixels'
# semantics, and does not pretend to.
_STYLE_WORDS = set("""
abstract background backdrop gradient gradients texture textured gloss glossy matte gleam
gleaming gentle soft softly warm cool cold vivid muted pastel gorgeous elegant beautiful modern
minimal minimalist clean sleek premium luxury luxurious gritty grainy grain gauzy hazy gauze gauzed
gaussian bokeh gauzier swoosh swooshes mesh meshes particles particle glow glowing radiant sheen
lighting light lights lit shadow shadows shading composition composed frame framed framing
photograph photographic photo photorealistic render rendered illustration illustrated illustrative
style styled stylised stylized aesthetic vibe mood atmosphere atmospheric cinematic
red orange yellow green blue indigo violet purple pink teal cyan magenta cream beige ivory tan
brown grey gray black white gold golden silver bronze copper coral crimson scarlet vermilion navy
azure emerald olive amber ochre sepia
no text lettering logos labels annotations watermarks words numbers letters caption captions
landscape portrait square wide tall high low left right upper lower centre center top bottom edge
edges corner corners zone region area space negative empty calm quiet plain even uniform flat
low-contrast contrast faint subtle whisper barely perceptible washed desaturated saturation
the a an and or of for with in on at to from into over under across through by as is are be
one two three four five six seven eight nine ten several few many lots plenty generous
""".split())
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9'-]{2,}")


def topic_terms(s):
    """Content-bearing words in a string, with style/colour vocabulary removed.

    Deliberately GENEROUS -- it lets some non-nouns through ('above', 'being'). That is the safe
    direction: it inflates good prompts, while the failure case scores ~0 either way.
    """
    return {w.lower() for w in _WORD.findall(s or "")
            if w.lower() not in _STYLE_WORDS and len(w) > 3}


MIN_SUBJECT_NOUNS = 6


def check_prompt_topicality(items, min_nouns=MIN_SUBJECT_NOUNS):
    """(findings, ...) — prompts too thin on SUBJECT vocabulary to be depicting anything.

    Measured across real and deliberately-generic prompts, style/colour words removed:

        my shipped hero          38      "technology background"     1
        my shipped plate         18      abstract blue gradient      0
        a cardiac-MRI prompt     18      premium swoosh + bokeh      1
        a garden-brand prompt    15

    So the separation is ~15x and the threshold sits in open space. This counts DENSITY, not
    topic agreement: an earlier version required >=2 shared words with a `--topic` string and
    false-positived on both of my own good prompts, because a prompt says "slide-shaped paper
    cards / vellum / ruler" while a topic line says "PowerPoint deck" -- lexical overlap cannot
    bridge concrete visual nouns to abstract subject nouns. Density needs no topic string and has
    no such failure.

    What it CANNOT do is judge the generated pixels' semantics. It gates the prompt, which is
    where the failure originates, and claims nothing more.
    """
    out = []
    for i, it in enumerate(items):
        nouns = sorted(topic_terms(it.get("prompt", "")))
        if len(nouns) < min_nouns:
            out.append((i, it.get("filename") or it.get("path") or "?", nouns))
    return out


def main():
    ap = argparse.ArgumentParser(description="Generate images from a manifest via the Codex CLI (no API key).")
    ap.add_argument("manifest", help="Path to image_prompt_manifest.json.")
    ap.add_argument("--out-dir", help="Override output directory (else manifest item paths/filenames).")
    ap.add_argument("--orientation", choices=["landscape", "portrait", "auto"], default="landscape",
                    help="Hint the composition (the hosted tool steers size by prompt). Default: landscape.")
    ap.add_argument("--limit", type=int, help="Only the first N entries.")
    ap.add_argument("--overwrite", action="store_true", help="Regenerate existing files (default: skip).")
    ap.add_argument("--timeout", type=int, default=360, help="Per-image timeout (seconds).")
    ap.add_argument("--dry-run", action="store_true", help="Print planned outputs without calling codex.")
    ap.add_argument("--allow-generic", action="store_true",
                    help="generate anyway when a prompt looks generic")
    ap.add_argument("--concurrency", type=int, default=_default_concurrency(),
                    help="Images generated in parallel (each is a `codex exec` subprocess). Default "
                         "scales with the machine (cores//3, clamped to 2-4); set 1 to serialize if "
                         "you hit rate limits. Speeds a multi-image deck.")
    args = ap.parse_args()

    if not args.dry_run and not _have_codex():
        print("error: the `codex` CLI is not installed / on PATH. Install it and run `codex login` "
              "— that path is free on the user's existing subscription.\n"
              "Do NOT silently switch to scripts/generate_images_openai.py: that path is METERED "
              "(real money per image) and needs the user's explicit go-ahead first — see the "
              "BILLING GATE in references/image-generation.md.", file=sys.stderr)
        return 2

    manifest = Path(args.manifest)
    if not manifest.is_file():
        print(f"error: manifest not found: {manifest}", file=sys.stderr)
        return 2
    try:
        items = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in manifest {manifest}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(items, list):
        print("error: manifest must be a JSON list", file=sys.stderr)
        return 2
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict) or "prompt" not in it or ("filename" not in it and "path" not in it):
            print(f"error: manifest item {i} needs 'prompt' and 'filename' (or 'path')", file=sys.stderr)
            return 2
    if args.limit is not None:
        items = items[: max(0, args.limit)]

    # FUSION gate, before the spend: a generic prompt yields generic art, and one generation +
    # render + review round is the cost of finding that out afterwards.
    _thin = check_prompt_topicality(items)
    if _thin:
        print(f"PROMPT NOT TOPICAL — {len(_thin)} prompt(s) name fewer than {MIN_SUBJECT_NOUNS} "
              f"subject things, so they describe a MOOD rather than this deck's subject:",
              file=sys.stderr)
        for i, fn, nouns in _thin:
            print(f"  [{i}] {fn}  subject words: {nouns or '(none — style/colour only)'}",
                  file=sys.stderr)
        print("  A plate must depict THIS deck's topic — a stranger should be able to name it from\n"
              "  the picture. Fold the deck's own subject nouns in, or pass --allow-generic.",
              file=sys.stderr)
        if not args.allow_generic:
            return 2

    # partition first: skip / dry-run are instant; only real generations get parallelized
    ok = skipped = failed = 0
    worklist = []
    for item in items:
        out_path = _resolve_out(item, args.out_dir)
        label = f"slide {item.get('slide', '?')}: {out_path}"
        if out_path.exists() and not args.overwrite:
            print(f"skip existing: {out_path}"); skipped += 1; continue
        if args.dry_run:
            print(f"would generate {label}"); continue
        worklist.append((item, out_path))

    def _work(item, out_path):                              # independent per item (own file, own subprocess)
        return _generate_one(item["prompt"], out_path, orientation=args.orientation, timeout=args.timeout)

    conc = max(1, min(args.concurrency, len(worklist)))
    if conc <= 1 or len(worklist) <= 1:
        for item, out_path in worklist:
            print(f"generate slide {item.get('slide','?')}: {out_path} … (codex exec; ~30-90s)")
            if _work(item, out_path): print(f"  ok -> {out_path}"); ok += 1
            else: print(f"  FAILED: {out_path} — no image produced", file=sys.stderr); failed += 1
    else:
        print(f"generating {len(worklist)} images, concurrency {conc} … (codex exec; ~30-90s each)")
        with _cf.ThreadPoolExecutor(max_workers=conc) as ex:
            futs = {ex.submit(_work, item, out_path): out_path for item, out_path in worklist}
            for fut in _cf.as_completed(futs):
                out_path = futs[fut]
                try:
                    if fut.result(): print(f"  ok -> {out_path}"); ok += 1
                    else: print(f"  FAILED: {out_path} — no image produced", file=sys.stderr); failed += 1
                except Exception as exc:
                    print(f"  FAILED: {out_path} — {exc}", file=sys.stderr); failed += 1

    print(f"done: generated {ok}, skipped {skipped}, failed {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
