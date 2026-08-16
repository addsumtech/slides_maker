#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loop-breaker regression test for deck_cycle.py (guard 4) — the streak AND the refusal.

The one genuinely uncapped loop in the pipeline is edit → build → lint on a single stubborn
slide: measured on a real deck, 10+ iterations of nudging a constant, and the computed-fit
rewrite landed first try. The breaker keys each fault by (stage, slide, lint code) — NOT by the
message, whose numbers change on every nudge — and escalates on the third consecutive failure.

The escalation then BINDS, which is the half that makes it more than a printed paragraph: after it
fires, a run whose build script changed only in its NUMBERS is refused before the build is spent.
"Another nudge" is decided by the file (an AST fingerprint blind to numeric literals), never by
asking the author what they intended — the whole point is that a rule enforced by good intentions
fails silently, and a silent failure here is the loop continuing.

Every direction is asserted, because a gate that over-fires is worse than none: it fires at 3 on
an unchanged script, it does NOT fire on a restructured one, it does NOT fire on an unparseable
one (fails open), a `--nudge-again "<reason>"` runs and is recorded, a bare/short reason is not a
reason, and the refused run really does skip the build rather than reporting after paying for it.

Run:  python3 tests/test_deck_cycle_loop_breaker.py
"""
import io
import json
import pathlib
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
CYCLE = HERE.parent / "scripts" / "deck_cycle.py"
sys.path.insert(0, str(HERE.parent / "scripts"))

import deck_cycle  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


# Verbatim shapes from the real tools: lint_layout's report line and lint_deck's per-slide lines.
BUILD_FAIL_A = "[lint] ✗ slide  4 OVERFLOW      ink needs 1.42in, box has 1.10in\n"
BUILD_FAIL_A2 = "[lint] ✗ slide  4 OVERFLOW      ink needs 1.38in, box has 1.10in\n"  # nudged numbers
BUILD_WARN = "[lint] • slide  6 SLIVER_GAP    0.03in seam\n"
DECK_BLOCK = "  slide 7: TEXT NOT VISIBLE: sampled fg/bg contrast 1.3:1\n"
DECK_WARN = "  slide 7: [warn] TEXT WALL: reading load ~92 words\n"

# A build script that always fails the same way, and records that it RAN. The number on the
# NUDGE line is what a nudge moves; the assertion is that moving it changes nothing that matters.
FAKE_BUILD = '''import pathlib
with open("runs.log", "a") as fh:
    fh.write("ran\\n")
NUDGE = {value}
print("[lint] ✗ slide  4 OVERFLOW      ink needs %.2fin, box has 1.10in" % NUDGE)
raise SystemExit(1)
'''


def write_script(deck_dir, name="build_x.py", value="1.02", extra=""):
    path = deck_dir / name
    path.write_text(FAKE_BUILD.format(value=value) + extra, encoding="utf-8")
    return path


def run_breaker(deck_dir, script_path, build_out, lint_out, lint_ran):
    buf = io.StringIO()
    with redirect_stdout(buf):
        deck_cycle._loop_breaker(deck_dir, script_path, build_out, lint_out, lint_ran)
    return buf.getvalue()


def state_of(deck_dir):
    return json.loads((deck_dir / deck_cycle.STATE_NAME).read_text(encoding="utf-8"))


def streaks(deck_dir):
    return state_of(deck_dir).get("streaks", {})


def cycle(deck_dir, script_name, *flags):
    p = subprocess.run([sys.executable, str(CYCLE), script_name, *flags],
                       capture_output=True, text=True, cwd=str(deck_dir))
    return p.returncode, p.stdout + p.stderr


def runs(deck_dir):
    log = deck_dir / "runs.log"
    return len(log.read_text(encoding="utf-8").split()) if log.exists() else 0


def main():
    print("== _fault_keys: stable keys from verbatim output ==")
    keys = deck_cycle._fault_keys(BUILD_FAIL_A + BUILD_WARN, None)
    check("build ✗ line becomes a key", keys == {"build:slide 4:OVERFLOW"}, repr(keys))
    check("nudged numbers give the SAME key",
          deck_cycle._fault_keys(BUILD_FAIL_A2, None) == keys)
    dkeys = deck_cycle._fault_keys("", DECK_BLOCK + DECK_WARN)
    check("deck blocker keyed by code, [warn] ignored",
          dkeys == {"deck:slide 7:TEXT NOT VISIBLE"}, repr(dkeys))

    print("== _nudge_fingerprint: blind to numbers, awake to structure ==")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        base = deck_cycle._nudge_fingerprint(write_script(d, value="1.02"))
        check("a numbers-only edit is the SAME fingerprint",
              deck_cycle._nudge_fingerprint(write_script(d, value="0.98")) == base)
        check("...even across many literals",
              deck_cycle._nudge_fingerprint(write_script(d, value="7")) == base)
        check("a structural edit is a DIFFERENT fingerprint",
              deck_cycle._nudge_fingerprint(
                  write_script(d, value="1.02", extra="import math\n")) != base)
        check("a string edit counts as real (shorter text IS a fix for OVERFLOW)",
              deck_cycle._nudge_fingerprint(
                  write_script(d, value="1.02", extra='X = "shorter"\n')) != base)
        check("booleans are decisions, not magnitudes",
              deck_cycle._nudge_fingerprint(write_script(d, value="1.02", extra="B = True\n"))
              != deck_cycle._nudge_fingerprint(write_script(d, value="1.02", extra="B = False\n")))
        (d / "broken.py").write_text("def (\n", encoding="utf-8")
        check("an unparseable script fingerprints as None",
              deck_cycle._nudge_fingerprint(d / "broken.py") is None)

    print("== escalation at 3 consecutive failures, silent before ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        sp = write_script(deck)
        out1 = run_breaker(deck, sp, BUILD_FAIL_A, None, False)
        out2 = run_breaker(deck, sp, BUILD_FAIL_A2, None, False)
        check("runs 1-2 stay silent", "LOOP BREAKER" not in out1 + out2, out1 + out2)
        out3 = run_breaker(deck, sp, BUILD_FAIL_A, None, False)
        check("run 3 escalates", "LOOP BREAKER" in out3, out3)
        check("escalation names the fault", "slide 4:OVERFLOW" in out3, out3)
        check("escalation says re-derive by measurement", "MEASUREMENT" in out3, out3)
        check("escalation warns the next run is refused", "REFUSED" in out3, out3)
        check("...and the baseline fingerprint is recorded",
              state_of(deck).get("fingerprint") == deck_cycle._nudge_fingerprint(sp))

    print("== a cleared fault resets its streak ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        sp = write_script(deck)
        run_breaker(deck, sp, BUILD_FAIL_A, None, False)
        run_breaker(deck, sp, BUILD_FAIL_A2, None, False)
        run_breaker(deck, sp, "", None, False)                    # fixed: clean build
        check("clean run drops the key", streaks(deck) == {}, repr(streaks(deck)))
        check("...and clears the escalation", not state_of(deck).get("escalated"))
        out = run_breaker(deck, sp, BUILD_FAIL_A, None, False)
        check("re-appearing fault starts at 1 (no escalation)",
              "LOOP BREAKER" not in out and streaks(deck)["build:slide 4:OVERFLOW"] == 1)

    print("== render-stage keys carry through a build-only run ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        sp = write_script(deck)
        run_breaker(deck, sp, "", DECK_BLOCK, True)
        run_breaker(deck, sp, "", DECK_BLOCK, True)
        mid = run_breaker(deck, sp, "", None, False)              # geometry-only iteration
        check("build-only run neither escalates nor resets deck key",
              "LOOP BREAKER" not in mid and streaks(deck)["deck:slide 7:TEXT NOT VISIBLE"] == 2,
              repr(streaks(deck)))
        out = run_breaker(deck, sp, "", DECK_BLOCK, True)
        check("third JUDGED failure escalates after the carry", "LOOP BREAKER" in out, out)

    print("== a different build script resets all streaks ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        run_breaker(deck, write_script(deck, "build_x.py"), BUILD_FAIL_A, None, False)
        run_breaker(deck, write_script(deck, "build_x.py"), BUILD_FAIL_A, None, False)
        out = run_breaker(deck, write_script(deck, "build_y.py"), BUILD_FAIL_A, None, False)
        check("new script starts at 1",
              "LOOP BREAKER" not in out and streaks(deck)["build:slide 4:OVERFLOW"] == 1)

    print("== _enforce_escalation: the hard constraint, both directions ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        sp = write_script(deck)
        allowed, note = deck_cycle._enforce_escalation(deck, sp, None)
        check("no escalation → nothing to enforce", allowed and not note)
        for _ in range(3):
            run_breaker(deck, sp, BUILD_FAIL_A, None, False)      # escalate
        allowed, note = deck_cycle._enforce_escalation(deck, sp, None)
        check("escalated + unchanged script → REFUSED", not allowed, note)
        check("...names the open fault", "slide 4:OVERFLOW" in note, note)
        check("...and offers the recorded way through", "--nudge-again" in note, note)
        write_script(deck, value="0.98")                          # another nudge
        allowed, _ = deck_cycle._enforce_escalation(deck, sp, None)
        check("a numbers-only edit is still refused", not allowed)
        allowed, note = deck_cycle._enforce_escalation(
            deck, sp, "the 1.10in box is a fixed template slot, so the text has to shrink")
        check("an override with a real reason runs", allowed, note)
        check("...and is recorded beside the deck",
              state_of(deck)["overrides"][0]["reason"].startswith("the 1.10in box"))
        check("...without resetting the streak",
              streaks(deck)["build:slide 4:OVERFLOW"] >= deck_cycle.STREAK_LIMIT)
        write_script(deck, value="1.02", extra="import math\n")   # structural change
        allowed, note = deck_cycle._enforce_escalation(deck, sp, None)
        check("a restructured script runs, no override needed", allowed and not note)
        (deck / "build_x.py").write_text("def (\n", encoding="utf-8")
        allowed, _ = deck_cycle._enforce_escalation(deck, sp, None)
        check("an unparseable script fails OPEN (its SyntaxError is the better message)", allowed)

    print("== end to end: the refused run never spends the build ==")
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td)
        write_script(deck)
        for i in range(1, 4):
            rc, out = cycle(deck, "build_x.py")
            check(f"run {i} executes the build", rc == 2 and runs(deck) == i, out)
        check("run 3 escalated", "LOOP BREAKER" in out, out)
        write_script(deck, value="0.97")                          # the fourth nudge
        rc, out = cycle(deck, "build_x.py")
        check("run 4 is refused", rc == 2 and "REFUSED" in out, out)
        check("...before the build ran — the point of refusing early", runs(deck) == 3,
              f"runs={runs(deck)}")
        rc, out = cycle(deck, "build_x.py", "--nudge-again", "too short")
        check("a short reason is not a reason", rc == 2 and "at least" in out, out)
        check("...and it did not run either", runs(deck) == 3, f"runs={runs(deck)}")
        rc, out = cycle(deck, "build_x.py", "--nudge-again",
                        "the box is a fixed template slot, so only the constant can move")
        check("a real reason runs the build", runs(deck) == 4, out)
        check("...on the record", "ON THE RECORD" in out, out)
        write_script(deck, value="1.02", extra="import math\n")   # restructured
        rc, out = cycle(deck, "build_x.py")
        check("a restructured script runs with no flag", runs(deck) == 5, out)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
