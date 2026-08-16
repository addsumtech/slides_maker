#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loop-breaker regression test for deck_cycle.py (guard 4).

The one genuinely uncapped loop in the pipeline is edit → build → lint on a single stubborn
slide: measured on a real deck, 10+ iterations of nudging a constant, and the computed-fit
rewrite landed first try. The breaker keys each fault by (stage, slide, lint code) — NOT by the
message, whose numbers change on every nudge — and escalates on the third consecutive failure.

Both directions are asserted: it fires when the same fault survives 3 consecutive runs, and it
stays silent when a fault clears (streak reset), when the run count is below the limit, and when
a build-only run simply didn't judge the render-stage keys (carry, not reset).

Run:  python3 tests/test_deck_cycle_loop_breaker.py
"""
import io
import json
import pathlib
import sys
import tempfile
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import deck_cycle  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


# Verbatim shapes from the real tools: lint_layout's report line and lint_deck's per-slide lines.
BUILD_FAIL_A = "[lint] ✗ slide  4 OVERFLOW      ink needs 1.42in, box has 1.10in\n"
BUILD_FAIL_A2 = "[lint] ✗ slide  4 OVERFLOW      ink needs 1.38in, box has 1.10in\n"  # nudged numbers
BUILD_WARN = "[lint] • slide  6 SLIVER_GAP    0.03in seam\n"
DECK_BLOCK = "  slide 7: TEXT NOT VISIBLE: sampled fg/bg contrast 1.3:1\n"
DECK_WARN = "  slide 7: [warn] TEXT WALL: reading load ~92 words\n"


def run_breaker(deck_dir, script, build_out, lint_out, lint_ran):
    buf = io.StringIO()
    with redirect_stdout(buf):
        deck_cycle._loop_breaker(deck_dir, script, build_out, lint_out, lint_ran)
    return buf.getvalue()


def streaks(deck_dir):
    state = json.loads((deck_dir / deck_cycle.STATE_NAME).read_text(encoding="utf-8"))
    return state.get("streaks", {})


def main():
    print("== _fault_keys: stable keys from verbatim output ==")
    keys = deck_cycle._fault_keys(BUILD_FAIL_A + BUILD_WARN, None)
    check("build ✗ line becomes a key", keys == {"build:slide 4:OVERFLOW"}, repr(keys))
    check("nudged numbers give the SAME key",
          deck_cycle._fault_keys(BUILD_FAIL_A2, None) == keys)
    dkeys = deck_cycle._fault_keys("", DECK_BLOCK + DECK_WARN)
    check("deck blocker keyed by code, [warn] ignored",
          dkeys == {"deck:slide 7:TEXT NOT VISIBLE"}, repr(dkeys))

    print("== escalation at 3 consecutive failures, silent before ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        out1 = run_breaker(deck, "build_x.py", BUILD_FAIL_A, None, False)
        out2 = run_breaker(deck, "build_x.py", BUILD_FAIL_A2, None, False)
        check("runs 1-2 stay silent", "LOOP BREAKER" not in out1 + out2, out1 + out2)
        out3 = run_breaker(deck, "build_x.py", BUILD_FAIL_A, None, False)
        check("run 3 escalates", "LOOP BREAKER" in out3, out3)
        check("escalation names the fault", "slide 4:OVERFLOW" in out3, out3)
        check("escalation says re-derive by measurement", "MEASUREMENT" in out3, out3)

    print("== a cleared fault resets its streak ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        run_breaker(deck, "build_x.py", BUILD_FAIL_A, None, False)
        run_breaker(deck, "build_x.py", BUILD_FAIL_A2, None, False)
        run_breaker(deck, "build_x.py", "", None, False)          # fixed: clean build
        check("clean run drops the key", streaks(deck) == {}, repr(streaks(deck)))
        out = run_breaker(deck, "build_x.py", BUILD_FAIL_A, None, False)
        check("re-appearing fault starts at 1 (no escalation)",
              "LOOP BREAKER" not in out and streaks(deck)["build:slide 4:OVERFLOW"] == 1)

    print("== render-stage keys carry through a build-only run ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        run_breaker(deck, "build_x.py", "", DECK_BLOCK, True)
        run_breaker(deck, "build_x.py", "", DECK_BLOCK, True)
        mid = run_breaker(deck, "build_x.py", "", None, False)    # geometry-only iteration
        check("build-only run neither escalates nor resets deck key",
              "LOOP BREAKER" not in mid and streaks(deck)["deck:slide 7:TEXT NOT VISIBLE"] == 2,
              repr(streaks(deck)))
        out = run_breaker(deck, "build_x.py", "", DECK_BLOCK, True)
        check("third JUDGED failure escalates after the carry", "LOOP BREAKER" in out, out)

    print("== a different build script resets all streaks ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        run_breaker(deck, "build_x.py", BUILD_FAIL_A, None, False)
        run_breaker(deck, "build_x.py", BUILD_FAIL_A, None, False)
        out = run_breaker(deck, "build_y.py", BUILD_FAIL_A, None, False)
        check("new script starts at 1",
              "LOOP BREAKER" not in out and streaks(deck)["build:slide 4:OVERFLOW"] == 1)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
