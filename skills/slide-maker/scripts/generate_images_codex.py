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
import shutil
import subprocess
import sys
from pathlib import Path

SESSIONS = Path.home() / ".codex" / "sessions"

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


def _newest_rollout():
    try:
        files = sorted(SESSIONS.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    return files[0] if files else None


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
    before = _newest_rollout()
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
    ap.add_argument("--concurrency", type=int, default=2,
                    help="Images generated in parallel (each is a `codex exec` subprocess — 2 is a safe "
                         "default; raise on a beefy machine, set 1 to serialize). Speeds a multi-image deck.")
    args = ap.parse_args()

    if not args.dry_run and not _have_codex():
        print("error: the `codex` CLI is not installed / on PATH. Run `codex login` first, or use "
              "scripts/generate_images_openai.py with OPENAI_API_KEY instead.", file=sys.stderr)
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
