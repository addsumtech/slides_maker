#!/usr/bin/env python3
"""Generate slide visual plates from an image_prompt_manifest.json via OpenAI.

This is an optional non-Codex path. In Codex, prefer the native imagegen tool when it
is available. Outside Codex, set OPENAI_API_KEY and run this script to materialize the
same manifest that scripts/image_prompts.py creates.
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "2048x1152"
DEFAULT_QUALITY = "medium"
DEFAULT_FORMAT = "png"


def _load_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("manifest must be a JSON list")
    required = {"slide", "filename", "prompt"}
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"manifest item {i} is not an object")
        missing = required - set(item)
        if missing:
            raise ValueError(f"manifest item {i} missing keys: {', '.join(sorted(missing))}")
    return data


def _api_error(exc):
    body = ""
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        pass
    if body:
        try:
            payload = json.loads(body)
            msg = payload.get("error", {}).get("message")
            if msg:
                return f"{exc.code} {exc.reason}: {msg}"
        except Exception:
            pass
        return f"{exc.code} {exc.reason}: {body[:800]}"
    return f"{exc.code} {exc.reason}"


def _request_image(api_key, payload, *, timeout, retries):
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(retries + 1):
        req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in {408, 409, 429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RuntimeError(_api_error(exc)) from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RuntimeError(f"request failed: {exc.reason}") from exc


def _write_response_image(result, out_path):
    data = result.get("data") or []
    if not data:
        raise RuntimeError("API response did not include image data")
    first = data[0]
    b64 = first.get("b64_json")
    if b64:
        out_path.write_bytes(base64.b64decode(b64))
        return
    url = first.get("url")
    if url:
        with urllib.request.urlopen(url, timeout=120) as resp:
            out_path.write_bytes(resp.read())
        return
    raise RuntimeError("API response included neither b64_json nor url")


def _resolve_out_path(item, out_dir):
    if out_dir:
        return Path(out_dir) / item["filename"]
    return Path(item.get("path") or item["filename"])


def main():
    ap = argparse.ArgumentParser(
        description="Generate images from image_prompt_manifest.json using the OpenAI Images API."
    )
    ap.add_argument("manifest", help="Path to image_prompt_manifest.json.")
    ap.add_argument("--out-dir", help="Override output directory. Defaults to manifest item paths.")
    ap.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Environment variable holding the API key.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Image model. Default: {DEFAULT_MODEL}.")
    ap.add_argument("--size", default=DEFAULT_SIZE, help=f"Output size. Default: {DEFAULT_SIZE}.")
    ap.add_argument("--quality", default=DEFAULT_QUALITY, help=f"Quality: low, medium, high, or auto. Default: {DEFAULT_QUALITY}.")
    ap.add_argument("--output-format", default=DEFAULT_FORMAT, choices=["png", "webp", "jpeg"], help="Image file format.")
    ap.add_argument("--background", choices=["opaque", "auto"], help="Background mode when supported by the selected model.")
    ap.add_argument("--moderation", choices=["auto", "low"], help="Moderation strictness when supported by the selected model.")
    ap.add_argument("--limit", type=int, help="Generate only the first N manifest entries.")
    ap.add_argument("--only-missing", action="store_true", help="Skip files that already exist. This is the default behavior.")
    ap.add_argument("--overwrite", action="store_true", help="Regenerate and overwrite existing files.")
    ap.add_argument("--dry-run", action="store_true", help="Print planned outputs without calling the API.")
    ap.add_argument("--timeout", type=int, default=300, help="Per-request timeout in seconds.")
    ap.add_argument("--retries", type=int, default=2, help="Retries for transient failures.")
    args = ap.parse_args()

    api_key = os.environ.get(args.api_key_env, "")
    if not api_key and not args.dry_run:
        print(f"error: set {args.api_key_env} before running this script", file=sys.stderr)
        return 2

    items = _load_manifest(args.manifest)
    if args.limit is not None:
        items = items[: max(0, args.limit)]
    if args.out_dir:
        Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0
    for item in items:
        out_path = _resolve_out_path(item, args.out_dir)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not args.overwrite:
            print(f"skip existing: {out_path}")
            skipped += 1
            continue

        payload = {
            "model": args.model,
            "prompt": item["prompt"],
            "size": args.size,
            "quality": args.quality,
            "output_format": args.output_format,
        }
        if args.background:
            payload["background"] = args.background
        if args.moderation:
            payload["moderation"] = args.moderation

        label = f"slide {item.get('slide', '?')}: {out_path}"
        if args.dry_run:
            print(f"would generate {label}")
            continue

        print(f"generate {label}")
        result = _request_image(api_key, payload, timeout=args.timeout, retries=args.retries)
        _write_response_image(result, out_path)
        generated += 1

    print(f"done: generated {generated}, skipped {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
