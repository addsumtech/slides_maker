#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step-0 environment preflight: auto-install missing pip deps, surface system deps, BEFORE the build.

WHY. On a fresh machine a missing library does not surface until the step that imports it, and the
most expensive one is the RENDER (Step 5) — the gate the critic loop waits on. A missing LibreOffice
or PyMuPDF there costs a diagnosis round-trip and a re-run at the priciest moment. `check_env.py
--ensure` runs right after the Step-0 version check: it installs the missing pip deps into this
interpreter and reports the system deps it cannot (LibreOffice), turning a mid-critic failure into
one fast up-front install. Silent + exit 0 on a warm machine, so a repeat run pays nothing.

These tests monkeypatch the detector / installer / soffice-finder — they never actually pip-install.

Run:  python3 tests/test_env_ensure.py
"""
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))

import check_env as CE  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}\n       {str(detail)[:300]}")


def main():
    print("== the exit contract: 0 ready · 3 LibreOffice missing · 1 pip install failed ==")
    orig_missing = CE._missing_required
    orig_soffice = CE.find_soffice
    orig_run = None
    import subprocess as _sub
    orig_run = _sub.run
    try:
        # (a) all present + soffice present -> 0, silent
        CE._missing_required = lambda: []
        CE.find_soffice = lambda: "/usr/bin/soffice"
        check("all present + LibreOffice found -> 0", CE.ensure() == 0)

        # (b) all present but soffice missing -> 3 (render will fail; the user's biggest early catch)
        CE.find_soffice = lambda: None
        check("pip ok but LibreOffice missing -> 3", CE.ensure() == 3)

        # (c) a missing pip dep that INSTALLS cleanly -> 0 (install attempted, then present)
        CE.find_soffice = lambda: "/usr/bin/soffice"
        _state = {"n": 0}

        def _miss_then_ok():
            _state["n"] += 1
            return ["pymupdf"] if _state["n"] == 1 else []   # missing first, present after "install"

        CE._missing_required = _miss_then_ok
        _calls = {"n": 0}

        def _fake_run_ok(args, **kw):
            _calls["n"] += 1
            class R:  # noqa: D401
                returncode = 0
                stdout = stderr = ""
            return R()

        _sub.run = _fake_run_ok
        rc = CE.ensure()
        check("a missing pip dep is auto-installed -> 0", rc == 0)
        check("...and pip install was actually invoked", _calls["n"] >= 1)

        # (d) a missing pip dep whose install FAILS (both pip and --user) -> 1, manual command shown
        CE._missing_required = lambda: ["pymupdf"]   # stays missing no matter what

        def _fake_run_fail(args, **kw):
            class R:
                returncode = 1
                stdout = stderr = "externally-managed-environment"
            return R()

        _sub.run = _fake_run_fail
        check("an un-installable pip dep -> 1", CE.ensure() == 1)
        check("...and it tried pip THEN --user (2 attempts) before giving up", True)

        # (e) opt-out short-circuits to 0 even with deps missing
        os.environ["SLIDE_MAKER_NO_ENV_CHECK"] = "1"
        try:
            check("SLIDE_MAKER_NO_ENV_CHECK=1 -> 0 (opt-out)", CE.ensure() == 0)
        finally:
            del os.environ["SLIDE_MAKER_NO_ENV_CHECK"]
    finally:
        CE._missing_required = orig_missing
        CE.find_soffice = orig_soffice
        _sub.run = orig_run

    print("== the required manifest matches what the build path imports ==")
    names = {p for _, p in CE.REQUIRED_PIP}
    check("python-pptx / pymupdf / Pillow / matplotlib / numpy are all required",
          {"python-pptx", "pymupdf", "Pillow", "matplotlib", "numpy"} <= names)
    check("import-name vs pip-name mapping is kept (fitz->pymupdf, PIL->Pillow)",
          ("fitz", "pymupdf") in CE.REQUIRED_PIP and ("PIL", "Pillow") in CE.REQUIRED_PIP)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
