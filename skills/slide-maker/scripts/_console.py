#!/usr/bin/env python3
"""Make this toolchain's output survive a console that cannot encode it.

SKILL.md tells native-Windows users to call the Python entry points directly, and the whole
toolchain writes ✓ · ✗ · • · → · ≥ · 🔴 into its reports. On a console using a legacy code page —
the default for `cmd`/PowerShell on Python 3.11–3.14, which is what CI pins and what most installs
run — encoding those characters raises `UnicodeEncodeError`, and the tool dies MID-REPORT with a
traceback. Measured with `PYTHONIOENCODING=cp1252` on this repo:

    lint_deck.py <deck>              -> rc=1, UnicodeEncodeError after printing part of the report
    render_deck.py <deck> --gate-check -> rc=1, same
    check_image_provenance.py --selftest -> rc=1 on '\\u2192' (the token grammar's arrow)
    deck_gates.py check <dir>        -> rc=1 on the 🔴, AFTER printing 'shape clean'

That last one is the shape of the harm: **a partial report plus a crash reads as a broken deck**,
when the deck was fine and the CONSOLE could not print a tick. And the failure lands on the two
commands an agent runs most.

`safe_stdio()` reconfigures stdout/stderr to replace unencodable characters instead of raising.
A UTF-8 console is untouched and still prints the real glyphs; a legacy one gets `?` where a tick
was and, crucially, **the rest of the report**. It never changes an exit code and never suppresses
a finding — the one thing worse than a mangled tick is a gate that stopped talking.

Call it as the first statement of a CLI's `main()`:

    from _console import safe_stdio
    safe_stdio()
"""
from __future__ import annotations

import sys


def safe_stdio():
    """Degrade unencodable output instead of raising. Returns True if anything was reconfigured."""
    changed = False
    for stream in (sys.stdout, sys.stderr):
        try:
            enc = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
            if enc in ("utf8", "utf8mb4"):
                continue                      # a UTF-8 console needs nothing
            stream.reconfigure(errors="replace")
            changed = True
        except Exception:
            # Not reconfigurable (a StringIO under test, a wrapped stream, Python without
            # reconfigure). Never raise from a helper whose whole job is to stop a crash.
            pass
    return changed
