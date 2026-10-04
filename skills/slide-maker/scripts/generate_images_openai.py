#!/usr/bin/env python3
"""Generate slide visual plates from an image_prompt_manifest.json via OpenAI.

This is an optional non-Codex path. In Codex, prefer the native imagegen tool when it
is available. Outside Codex, set OPENAI_API_KEY and run this script to materialize the
same manifest that scripts/image_prompts.py creates.
"""
import argparse
import base64
import concurrent.futures as _cf
import json
import os
import shlex
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://api.openai.com/v1/images/generations"
EDITS_URL = "https://api.openai.com/v1/images/edits"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "2048x1152"
DEFAULT_QUALITY = "medium"
DEFAULT_FORMAT = "png"


# The sizes an item's aspect is snapped to (an image-series item carries its slot's w/h as "aspect";
# image_series.prompts writes it). Nearest by log-ratio, so 3:4 and 4:3 are equally far from square.
SIZES = (("2048x1152", 2048 / 1152), ("1536x1024", 1.5), ("1024x1024", 1.0), ("1024x1536", 1024 / 1536))


def _size_for(item, explicit):
    """The size to request: an EXPLICIT --size wins (it was silently overridden by every item's aspect); else
    the nearest SIZES entry to the item's own `aspect`; else DEFAULT_SIZE. Measured 2026-10-03: every image of a
    series was requested at one 2048x1152, so a tall arch slot got a landscape picture to crop."""
    if explicit:
        return explicit
    a = item.get("aspect")
    if not isinstance(a, (int, float)) or a <= 0:
        return DEFAULT_SIZE
    import math
    return min(SIZES, key=lambda sz: abs(math.log(a / sz[1])))[0]


def _with_style(prompt):
    """The prompt for a generation made beside the series' KEY image (the edits endpoint sees the
    image itself): match its look, never its subject."""
    return (prompt + "\n\nThe attached image is an earlier image of the SAME series: match its palette, "
            "light, colour temperature, grain or brushwork and rendering, so the two read as one series. "
            "Do NOT copy its subject, its objects or its composition — the subject is the one described "
            "above. If this prompt asks for a flat background colour (a cut-out), the prompt's background "
            "wins over the reference's.")


def _multipart(fields, files):
    """(body, content_type) for a multipart/form-data POST — `files` is [(field, path)]."""
    import uuid
    boundary = "sm-" + uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                    % (boundary, k, v)).encode("utf-8"))
    for k, path in files:
        path = Path(path)
        ctype = {".png": "image/png", ".webp": "image/webp"}.get(path.suffix.lower(), "image/jpeg")
        out.append(('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
                    'Content-Type: %s\r\n\r\n' % (boundary, k, path.name, ctype)).encode("utf-8"))
        out.append(path.read_bytes() + b"\r\n")
    out.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(out), "multipart/form-data; boundary=" + boundary


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


def _request_image(api_key, payload, *, timeout, retries, files=None):
    """POST a generation — JSON to /generations, or multipart to /edits when `files` (the series'
    style reference) are given."""
    if files:
        body, ctype = _multipart(payload, files)
        url = EDITS_URL
    else:
        body, ctype, url = json.dumps(payload).encode("utf-8"), "application/json", API_URL
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": ctype,
    }
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
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


def _generate_item(item, out_path, args, api_key):
    """Generate one image (blocking). Independent per item — safe to run concurrently:
    each writes a distinct file, shares no mutable state. Returns out_path on success."""
    style_ref = getattr(args, "style_ref", None)
    payload = {
        "model": args.model,
        "prompt": _with_style(item["prompt"]) if style_ref else item["prompt"],
        "size": _size_for(item, args.size),
        "quality": args.quality,
        "output_format": args.output_format,
    }
    if args.background:
        payload["background"] = args.background
    if args.moderation and not style_ref:
        payload["moderation"] = args.moderation     # generations only: the SDK's images.edit() has no moderation
    elif args.moderation and not getattr(args, "_moderation_noted", False):
        print("note: --moderation applies to generations only; the style-reference (edits) request has no "
              "such parameter, so it is not sent", file=sys.stderr)
        args._moderation_noted = True
    result = _request_image(api_key, payload, timeout=args.timeout, retries=args.retries,
                            files=[("image[]", style_ref)] if style_ref else None)
    _write_response_image(result, out_path)
    return out_path



def _series_next(items, script, manifest, out_of, only, style_ref, failed=False):
    """The NEXT line after a successful run of an image-SERIES manifest, so an agent that follows only
    printed output reaches the end (final review, 2026-10-03: neither generator printed a next step)."""
    plans = {it.get("series_plan") for it in items if it.get("series_plan")}
    if len(plans) != 1:
        return None
    plan = plans.pop()
    if failed:      # a failed run still names its next step: the same command, once the cause is fixed
        again = (" --only " + shlex.quote(str(only))) if only else ""
        again += (" --style-ref " + shlex.quote(str(style_ref))) if style_ref else ""
        return "NEXT (once the cause above is fixed): python3 scripts/{} {}{}".format(
            script, shlex.quote(str(manifest)), again)
    if only:
        key = out_of(items[0])
        return ("NEXT (LOOK at {} first; to redo it: --overwrite --only {}): python3 scripts/{} {} --style-ref {}"
                .format(key, only, script, shlex.quote(str(manifest)), shlex.quote(str(key))))
    if style_ref:
        return "NEXT: python3 scripts/image_series.py cutout {} --dir {}".format(
            shlex.quote(plan), shlex.quote(str(Path(manifest).resolve().parent)))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate images from image_prompt_manifest.json using the OpenAI Images API."
    )
    ap.add_argument("manifest", help="Path to image_prompt_manifest.json.")
    ap.add_argument("--out-dir", help="Override output directory. Defaults to manifest item paths.")
    ap.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Environment variable holding the API key.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Image model. Default: {DEFAULT_MODEL}.")
    ap.add_argument("--size", default=None, help=f"Output size for EVERY image. Default: each item's own aspect "
                                                 f"(else {DEFAULT_SIZE}).")
    ap.add_argument("--quality", default=DEFAULT_QUALITY, help=f"Quality: low, medium, high, or auto. Default: {DEFAULT_QUALITY}.")
    ap.add_argument("--output-format", default=DEFAULT_FORMAT, choices=["png", "webp", "jpeg"], help="Image file format.")
    ap.add_argument("--background", choices=["opaque", "auto"], help="Background mode when supported by the selected model.")
    ap.add_argument("--moderation", choices=["auto", "low"], help="Moderation strictness when supported by the selected model.")
    ap.add_argument("--limit", type=int, help="Generate only the first N manifest entries.")
    ap.add_argument("--only", metavar="ID",
                    help="generate only the item whose id (or filename stem) is ID — an image series' "
                         "KEY image first, so it can be looked at before the rest are made in its style")
    ap.add_argument("--style-ref", metavar="PATH",
                    help="the series' approved KEY image: every generation goes to the edits endpoint "
                         "WITH it, told to match its look — not its subject or composition")
    ap.add_argument("--overwrite", action="store_true",
                    help="Regenerate and overwrite existing files (default: skip files that already exist).")
    ap.add_argument("--dry-run", action="store_true", help="Print planned outputs without calling the API.")
    ap.add_argument("--timeout", type=int, default=300, help="Per-request timeout in seconds.")
    ap.add_argument("--retries", type=int, default=2, help="Retries for transient failures.")
    ap.add_argument("--concurrency", type=int, default=3,
                    help="Images generated in parallel (I/O-bound HTTP; near-linear speedup for a "
                         "multi-image deck — hero+divider+plate at once). Lower to 1 if you hit rate limits.")
    args = ap.parse_args(argv)

    api_key = os.environ.get(args.api_key_env, "")
    if not api_key and not args.dry_run:
        print(f"error: set {args.api_key_env} before running this script", file=sys.stderr)
        return 2

    items = _load_manifest(args.manifest)
    if args.limit is not None:
        items = items[: max(0, args.limit)]
    if args.only:
        # EXACT id first, then exact stem, then a unique "-ID" suffix — never several: with slots "hero"
        # and "s04-hero" a suffix match picked both, and the second was made without the style reference
        def _stem(it):
            return Path(str(it.get("filename") or it.get("path") or "")).stem
        sel = ([it for it in items if it.get("id") == args.only]
               or [it for it in items if _stem(it) == args.only]
               or [it for it in items if _stem(it).endswith("-" + args.only)])
        if not sel:
            print(f"error: no manifest item matches --only {args.only!r}", file=sys.stderr)
            return 2
        if len(sel) > 1:
            print(f"error: --only {args.only!r} matches {len(sel)} items ({', '.join(_stem(i) for i in sel)}) — "
                  f"pass the exact slot id", file=sys.stderr)
            return 2
        items = sel
    if args.style_ref:
        args.style_ref = Path(args.style_ref).expanduser()
        if not args.style_ref.is_file() or args.style_ref.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            print(f"error: --style-ref {args.style_ref} is not an image file — generate and LOOK at the key "
                  f"first (--only <key-id>), then pass its path", file=sys.stderr)
            return 2
        print(f"style reference: {args.style_ref} (sent with every generation, edits endpoint)")
    if args.out_dir:
        Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    # partition first: skip-existing and dry-run are instant; only real generations get parallelized
    skipped = 0
    worklist = []
    for item in items:
        out_path = _resolve_out_path(item, args.out_dir)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        label = f"slide {item.get('slide', '?')}: {out_path} ({_size_for(item, args.size)})"
        if out_path.exists() and not args.overwrite:
            print(f"skip existing: {out_path}")
            skipped += 1
            continue
        if args.dry_run:
            print(f"would generate {label}")
            continue
        worklist.append((item, out_path))

    generated = 0
    errors = []
    conc = max(1, min(args.concurrency, len(worklist)))
    if conc <= 1:
        for item, out_path in worklist:
            print(f"generate slide {item.get('slide', '?')}: {out_path}")
            try:
                _generate_item(item, out_path, args, api_key)
                generated += 1
            except Exception as exc:                       # one failure must not abort the batch
                errors.append((out_path, str(exc)))
                print(f"  FAILED {out_path}: {exc}", file=sys.stderr)
    elif worklist:
        print(f"generating {len(worklist)} images, concurrency {conc} …")
        with _cf.ThreadPoolExecutor(max_workers=conc) as ex:
            futs = {ex.submit(_generate_item, item, out_path, args, api_key): out_path
                    for item, out_path in worklist}
            for fut in _cf.as_completed(futs):
                out_path = futs[fut]
                try:
                    fut.result()
                    generated += 1
                    print(f"  ok -> {out_path}")
                except Exception as exc:
                    errors.append((out_path, str(exc)))
                    print(f"  FAILED {out_path}: {exc}", file=sys.stderr)

    print(f"done: generated {generated}, skipped {skipped}" + (f", failed {len(errors)}" if errors else ""))
    if not args.dry_run:
        nxt = _series_next(items, "generate_images_openai.py", args.manifest,
                           lambda it: _resolve_out_path(it, args.out_dir), args.only, args.style_ref,
                           failed=bool(errors))
        if nxt:
            print(nxt)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
