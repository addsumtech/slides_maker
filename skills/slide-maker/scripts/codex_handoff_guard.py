#!/usr/bin/env python3
"""Refuse a Codex-verified PPTX hand-off unless its final file matches a PASS receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


RECEIPT_SCHEMA = "slide-maker-codex-delivery-receipt/v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_receipt(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("receipt must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Require a PASS receipt for a Codex PPTX hand-off")
    parser.add_argument("--receipt", required=True, type=Path, help="PASS receipt from codex_delivery_gate.py")
    parser.add_argument("--deck", required=True, type=Path, help="final PPTX that will be handed off")
    args = parser.parse_args()

    try:
        receipt = load_receipt(args.receipt)
        actual = sha256_file(args.deck)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CODEX HANDOFF GUARD: BLOCKED — {exc}", file=sys.stderr)
        return 1

    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("status") != "PASS":
        print("CODEX HANDOFF GUARD: BLOCKED — no valid PASS receipt", file=sys.stderr)
        return 1
    expected = receipt.get("pptx_sha256")
    if not isinstance(expected, str) or actual != expected:
        print("CODEX HANDOFF GUARD: BLOCKED — receipt does not match final PPTX", file=sys.stderr)
        return 1

    print("CODEX HANDOFF GUARD: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
