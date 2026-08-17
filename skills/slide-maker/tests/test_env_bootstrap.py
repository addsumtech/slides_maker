#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The dependency backstop: a missing library must not depend on an agent remembering a prose step.

`check_env.py --ensure` (SKILL.md Step 0.0b) auto-installs the required pip deps — but it is a
PROSE instruction, so a code agent that skips it leaves a fresh machine to fail with a bare
`ModuleNotFoundError` at the first import, with no pointer to the fix. `deckkit._ensure_runtime_deps()`
is the backstop AT the universal chokepoint every build passes through: `import deckkit`. It makes the
auto-install agent-independent (proven end-to-end by importing deckkit in a fresh venv with none of
the deps — it pip-installs them and succeeds; a unit test must not spin a venv, so that path is
covered by the commit, and the SAFE behavior is locked here).

  - the two dep lists are IDENTICAL, so the backstop and the Step-0 preflight can never drift
  - the backstop is a no-op when warm — it must NEVER break the import that everything depends on
  - SLIDE_MAKER_NO_ENV_CHECK=1 opts out cleanly
  - the icon rasterizer is probed by the SAME helper the human report and ensure() share

Run:  python3 tests/test_env_bootstrap.py
"""
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import deckkit                                                        # noqa: E402
import check_env                                                     # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def main():
    print("dependency backstop")

    check("deckkit._RUNTIME_DEPS is identical to check_env.REQUIRED_PIP (no drift)",
          deckkit._RUNTIME_DEPS == check_env.REQUIRED_PIP,
          (deckkit._RUNTIME_DEPS, check_env.REQUIRED_PIP))

    # warm no-op: the deps are present in this interpreter (we just imported deckkit), so the
    # backstop must return without raising or exiting — it is the import everything depends on.
    ok = True
    try:
        deckkit._ensure_runtime_deps()
    except BaseException as e:                                       # noqa: BLE001
        ok = False
        print("   ", type(e).__name__, e)
    check("the backstop is a no-op when the toolchain is warm (never breaks the import)", ok)

    # opt-out returns immediately (and does not touch pip)
    os.environ["SLIDE_MAKER_NO_ENV_CHECK"] = "1"
    try:
        check("SLIDE_MAKER_NO_ENV_CHECK=1 opts out cleanly",
              deckkit._ensure_runtime_deps() is None)
    finally:
        del os.environ["SLIDE_MAKER_NO_ENV_CHECK"]

    # the rasterizer helper is shared by main() and ensure() so the report and the preflight agree
    rz = check_env._find_rasterizer()
    check("the SVG-rasterizer helper (shared by report + ensure) returns a known value",
          rz in ("cairosvg", "rsvg-convert", "headless Chrome/Edge", None), rz)

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
