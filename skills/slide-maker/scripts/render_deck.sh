#!/bin/bash
# Thin shim -> the cross-platform render_deck.py (the real implementation).
# Keeps `bash scripts/render_deck.sh deck.pptx [out_dir]` working on macOS / Linux /
# Git Bash / WSL. NATIVE Windows (PowerShell / cmd) has no bash — run instead:
#     python scripts\render_deck.py deck.pptx [out_dir]
# Requires: LibreOffice + pymupdf. Override LibreOffice with SOFFICE=/path/to/soffice.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3 || command -v python)"
[ -n "$PY" ] || { echo "python not found on PATH" >&2; exit 1; }
exec "$PY" "$DIR/render_deck.py" "$@"
