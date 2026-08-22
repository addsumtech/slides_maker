#!/usr/bin/env python3
"""check_doc_commands — a documented command must be runnable AS WRITTEN.

Right now it enforces one rule, because one rule is what has actually broken:

    bare `python <something>.py`  ->  must be `python3 <something>.py`

WHY THIS IS A GATE AND NOT A STYLE PREFERENCE
---------------------------------------------
`/usr/bin/python` does not exist on macOS — Apple removed Python 2 and never shipped a
`python` shim — and a Homebrew install provides `python3` only. On the author's machine it
works anyway, because Anaconda puts a `python` on PATH; that is exactly what let 12 bare
`python scripts/…` lines sit in SKILL.md, its references and the agent prompts while 18 other
lines said `python3`.

The reader this breaks is an AGENT following the documented line literally. A model that
troubleshoots will recover; one that copies the string and reports `command not found` will
not, and non-Claude runtimes hit this hardest because the skill's whole cross-runtime story is
"the scripts are plain python3, run them from any shell."

CI could not see it: `actions/setup-python` puts a `python` on PATH, so every documented line
ran green in the one environment that is guaranteed not to resemble a user's laptop. That is
the shape this repo keeps legislating against — a check whose passing environment is the only
environment where the bug is invisible.

THE ONE LEGITIMATE EXCEPTION
----------------------------
Native Windows ships the `python` launcher and frequently has no `python3` at all. A line that
is explicitly about Windows may use bare `python`; mark it with

    python3-sweep-exempt

on the same line, or anywhere in the 6 lines above it — a window, not "the line before",
because the marker is normally the first line of a multi-line comment explaining WHY, and a
one-line lookback would silently fail to see its own carve. An unmarked exception fails, so the
carve is a decision someone wrote down rather than a pattern that silently re-accumulates.

USAGE
    python3 scripts/check_doc_commands.py          # exit 1 on any finding
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "slide-maker"

# Bare `python` immediately followed by something that is clearly a script invocation.
# Deliberately NOT matching `python3`, ```python fences, "python-pptx", or prose like
# "a python script" — a linter that cries wolf gets ignored, which is worse than no linter.
BARE_PYTHON = re.compile(r"(?<![\w.-])python(?![\w.-])\s+(?=[\w./~$-]*\.py\b)")
EXEMPT = "python3-sweep-exempt"
WINDOW = 6   # how far above a line the marker may sit; see the docstring


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    out = []
    for i, line in enumerate(lines):
        if not BARE_PYTHON.search(line):
            continue
        if EXEMPT in line or any(EXEMPT in l for l in lines[max(0, i - WINDOW):i]):
            continue
        out.append((i + 1, line.strip()))
    return out


def main() -> int:
    targets: list[Path] = []
    for pat in ("SKILL.md", "references/**/*.md", "agents/*.md", "scripts/*.py", "scripts/*.sh"):
        targets.extend(sorted(SKILL.glob(pat)))
    targets = [p for p in targets if "__pycache__" not in p.parts]

    findings = [(p, n, t) for p in targets for n, t in scan(p)]
    if not findings:
        print(f"check_doc_commands: {len(targets)} file(s) — every documented python "
              f"invocation is `python3` (or a marked Windows carve). clean.")
        return 0

    print(f"check_doc_commands: {len(findings)} bare `python <script>.py` invocation(s).")
    print("`python` does not exist on macOS; an agent copying these lines gets "
          "'command not found'. Use `python3`, or mark a genuine native-Windows line with "
          f"`{EXEMPT}`.\n")
    for p, n, text in findings:
        print(f"  {p.relative_to(REPO)}:{n}")
        print(f"      {text[:140]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
