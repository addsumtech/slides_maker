#!/bin/bash
# Thin shim -> the cross-platform check_env.py (the real implementation).
# Keeps `bash scripts/check_env.sh` working on macOS / Linux / Git Bash / WSL.
# NATIVE Windows (PowerShell / cmd) has no bash — run instead:
#     python scripts\check_env.py
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3 || command -v python)"
[ -n "$PY" ] || { echo "python not found on PATH" >&2; exit 1; }
exec "$PY" "$DIR/check_env.py" "$@"
