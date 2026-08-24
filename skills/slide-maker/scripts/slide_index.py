#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slide N -> the file, function and line that draws it.

Why this exists
---------------
Section fan-out (`references/large-deck-orchestration.md`) hands three agents one section each and
assembles the results. It buys a large wall-clock win, and it hands the coordinator a problem it
did not have before: **it did not write the code**. So when a critic says "slide 7 crops its
caption", the coordinator has to go find slide 7 — and it does that by grepping three modules it
has never read.

Measured on one 14-slide build: the miscellaneous-shell bucket was 33 round-trips and 30,049
output tokens (~9 minutes), and most of it was exactly this — `grep -n "Layer 1 is the only"
section_*.py`, `sed -n '211,240p' section_b.py`, `grep -n "SLIDES = \\|^def slide_"` — re-deriving a
map that the authors already had and threw away.

This rebuilds it deterministically, so the fix loop opens a file at a line instead of searching for
it. It reads the section modules the same way `assemble.py` does; if a module cannot be imported it
says so per-module rather than failing the run, because a half-map still beats grepping.

Usage
-----
  python3 scripts/slide_index.py section_a.py section_b.py section_c.py
  python3 scripts/slide_index.py --json build_deck.py        # single-author deck works too
"""
import argparse
import importlib.util
import inspect
import json
import os
import re
import sys


def _load(path):
    name = "sm_idx_" + re.sub(r"\W", "_", os.path.basename(path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _slide_fns(mod):
    """Functions that draw one slide, in source order.

    Two conventions in this skill produce them: the per-slide-function scaffold (`sNN_name`, an
    ordered `SLIDES` registry) and section modules whose `build_section` calls them. Prefer an
    explicit registry when the module has one — that is the author's own declared order — and fall
    back to source order, which is what the scaffold's `main()` walks anyway."""
    registry = getattr(mod, "SLIDES", None)
    if isinstance(registry, (list, tuple)) and registry and all(callable(f) for f in registry):
        return list(registry)
    fns = [f for _n, f in inspect.getmembers(mod, inspect.isfunction)
           if getattr(f, "__module__", None) == mod.__name__
           and re.match(r"^(s\d+|slide)[_0-9]", _n or "")]
    fns.sort(key=lambda f: inspect.getsourcelines(f)[1])
    return fns


def build_index(paths):
    rows, notes = [], []
    n = 0
    for p in paths:
        p = os.path.abspath(p)
        try:
            mod = _load(p)
        except Exception as e:  # a module that will not import is a real problem, but not THIS
            notes.append("{}: could not import ({}: {}) — not indexed"
                         .format(os.path.basename(p), type(e).__name__, e))
            continue
        fns = _slide_fns(mod)
        if not fns:
            notes.append("{}: no per-slide functions found — the scaffold in "
                         "references/examples/section_example.py is what makes a deck indexable"
                         .format(os.path.basename(p)))
            continue
        start = getattr(mod, "START_PAGE", None)
        for i, f in enumerate(fns):
            try:
                line = inspect.getsourcelines(f)[1]
            except Exception:
                line = 0
            n = (start + i) if isinstance(start, int) else (n + 1)
            doc = (inspect.getdoc(f) or "").strip().splitlines()
            rows.append(dict(slide=n, file=p, func=f.__name__, line=line,
                             plan=(doc[0][:110] if doc else "")))
    return rows, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modules", nargs="+", help="section modules (or one build script), in deck order")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    for m in args.modules:
        sys.path.insert(0, os.path.dirname(os.path.abspath(m)))
    rows, notes = build_index(args.modules)
    if args.json:
        print(json.dumps({"slides": rows, "notes": notes}, indent=2))
        return 0 if rows else 2
    if not rows:
        sys.stderr.write("slide_index: nothing indexed.\n" + "\n".join("  " + n for n in notes) + "\n")
        return 2
    w = max(len(os.path.basename(r["file"])) for r in rows)
    for r in rows:
        print("s{:<3} {:<{w}}:{:<5} {:<22} {}".format(
            r["slide"], os.path.basename(r["file"]), r["line"], r["func"], r["plan"], w=w))
    for nt in notes:
        sys.stderr.write("note: " + nt + "\n")
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
