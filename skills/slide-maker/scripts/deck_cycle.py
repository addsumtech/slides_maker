#!/usr/bin/env python3
"""One call for the edit → build → check loop, so an iteration costs one round-trip.

WHY. Measured on a delivered 12-page build: 133 tool calls, of which the
edit/build/render/lint loop was 67 — about 21 of the 88 minutes the whole deck took. Almost none
of that was computation. The deterministic pipeline for that same deck is 9.1 seconds end to end
(build 1.8 · render 5.4 · lint 1.9); everything else was the cost of asking for one step at a
time. This does not make the steps faster. It makes one iteration one question.

WHAT IT DELIBERATELY DOES NOT DO — three guards, because a shortcut through a checking pipeline
is exactly how a pipeline stops checking:

  1. **Findings are printed VERBATIM, never counted.** A report that says "2 findings" instead of
     the two messages has moved the cost from round-trips to information, which is a worse trade:
     the messages name the slide, the shape and the remedy, and acting on a number is impossible.
     There is no --quiet, and there is no summary mode.

  2. **Rendering is OPT-IN (`--render`).** Most iterations are "fix a geometry fault and re-check",
     which needs the build-time lint and nothing else — 1.8s. Forcing a render into every cycle
     would add 5.4s to the majority of iterations and make the loop SLOWER while looking faster.

  3. **A CRITICAL build fault stops the cycle before rendering.** The build script's own
     `lint_layout(strict=True)` raises, and that stop is load-bearing, not an inconvenience: a
     deck with a critical geometry fault should not be rasterised, looked at, or reasoned about
     as if it were finished. This tool propagates the stop; it never renders past one.

It is an ALTERNATIVE entry point, not a replacement. `render_deck.py` and `lint_deck.py` keep
their own behaviour and every existing invocation still works — nothing in the pipeline is routed
through here, and a step this skips is a step you can still run yourself.

USAGE
    python3 scripts/deck_cycle.py build_<deck>.py                 # build + build-time lint
    python3 scripts/deck_cycle.py build_<deck>.py --render        # …+ render + render-time lint
    python3 scripts/deck_cycle.py build_<deck>.py --render --fast # …re-rendering changed pages only
    python3 scripts/deck_cycle.py build_<deck>.py --slides 3,7    # render only these pages

Exit code is nonzero when any stage fails, so the loop can be scripted.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _run(label, cmd, cwd=None):
    """Run one stage; return (ok, seconds, combined output). Output is never trimmed."""
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    dt = time.perf_counter() - t0
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, dt, out, label


def _emit(label, ok, dt, out):
    mark = "ok  " if ok else "FAIL"
    print(f"\n── {label}  [{mark}]  {dt:.2f}s " + "─" * max(0, 46 - len(label)))
    text = out.rstrip()
    if text:
        print(text)


def main(argv):
    argv = list(argv)
    render = False
    passthru = []
    for flag in ("--render",):
        while flag in argv:
            argv.remove(flag)
            render = True
    # flags that belong to render_deck.py, forwarded verbatim rather than re-implemented
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--fast":
            passthru.append(a)
            argv.pop(i)
            render = True
            continue
        if a == "--slides" or a.startswith("--slides="):
            if "=" in a:
                passthru.append(a)
                argv.pop(i)
            else:
                passthru.extend(argv[i:i + 2])
                del argv[i:i + 2]
            render = True
            continue
        i += 1

    script = next((a for a in argv if not a.startswith("-")), None)
    if not script:
        print(__doc__.split("USAGE")[1].strip())
        return 2
    script_path = Path(script).resolve()
    if not script_path.exists():
        print(f"deck_cycle: no such build script: {script}")
        return 2
    deck_dir = script_path.parent

    stages = []
    ok, dt, out, label = _run("build (+ build-time lint)", [sys.executable, str(script_path)],
                              cwd=str(deck_dir))
    _emit(label, ok, dt, out)
    stages.append((label, ok, dt))
    if not ok:
        # Guard 3. The build script's own lint_layout(strict=True) raises on a CRITICAL geometry
        # fault. Rendering past that would produce pixels of a deck that is known to be broken and
        # invite reasoning about them as if they were finished.
        print("\ndeck_cycle: STOPPED before rendering — the build did not complete. A critical "
              "layout fault is a reason to fix the build, not to look at the render.")
        return 1

    pptx = None
    for line in out.splitlines():
        if "saved ->" in line:
            pptx = (deck_dir / line.split("saved ->", 1)[1].split("|")[0].strip()).resolve()
            break
    if pptx is None or not pptx.exists():
        cands = sorted(deck_dir.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
        pptx = cands[0] if cands else None
    if pptx is None:
        print("\ndeck_cycle: the build succeeded but no .pptx was found beside the build script.")
        return 1

    if render:
        rdir = deck_dir / "render"
        ok_r, dt_r, out_r, lab_r = _run("render", [sys.executable, str(HERE / "render_deck.py"),
                                                   str(pptx), str(rdir)] + passthru)
        _emit(lab_r, ok_r, dt_r, out_r)
        stages.append((lab_r, ok_r, dt_r))
        ok_l, dt_l, out_l, lab_l = _run("render-time lint",
                                        [sys.executable, str(HERE / "lint_deck.py"),
                                         str(pptx), str(rdir)])
        _emit(lab_l, ok_l, dt_l, out_l)
        stages.append((lab_l, ok_l, dt_l))

    total = sum(d for _l, _o, d in stages)
    line = " · ".join(f"{l} {d:.1f}s" for l, _o, d in stages)
    print(f"\n── cycle  {total:.1f}s  ({line})")
    if not render:
        print("   render not run (add --render). The build-time lint above is geometry only; "
              "pixel-level checks and the per-slide visual read still need a render.")
    return 0 if all(o for _l, o, _d in stages) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
