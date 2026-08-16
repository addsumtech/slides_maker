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

  4. **The LOOP BREAKER: the third consecutive failure of the same fault is never answered with
     another nudge.** The one genuinely uncapped loop in the pipeline is edit → build → lint on
     a single stubborn slide: measured on a real deck, 10+ iterations of adjusting a constant by
     a few points each time — and the fix that finally landed (computing the layout from the
     measured content) landed on its FIRST try. So this tool keeps a per-fault streak across
     consecutive runs in `.deck-cycle-state.json` beside the build script (same slide + same lint
     code = same fault; the message's numbers may change, the key does not). When a fault
     survives 3 consecutive runs it escalates: stop nudging, RE-DERIVE that slide's layout by
     measurement — `fit_text`/ink measurement, or a form helper that owns the geometry
     (`sigs.py --example <form>`). A fault that clears resets its streak; a fresh build script
     resets them all.

     🔴 **And the escalation BINDS: the next run is refused if the edit was another nudge.** A
     rule whose only enforcement is the author choosing to obey it fails silently, and a silent
     failure here means the loop carries on exactly as before. So "another nudge" is defined by
     the FILE, not by intent: `_nudge_fingerprint` hashes the build script's AST with every
     numeric literal normalized to 0, so an edit that moved only numbers leaves the fingerprint
     UNCHANGED — and an unchanged fingerprint after an escalation is refused before the build is
     even spent. Restructure (a helper call, computed geometry, fewer words) and it runs. If a
     constant really is the fix, `--nudge-again "<why>"` runs it and records the reason beside the
     deck; a gate with no way through stops being a gate and becomes something to work around.
     It never changes THIS run's exit code and never suppresses a finding — it changes the next.

It is an ALTERNATIVE entry point, not a replacement. `render_deck.py` and `lint_deck.py` keep
their own behaviour and every existing invocation still works — nothing in the pipeline is routed
through here, and a step this skips is a step you can still run yourself.

USAGE
    python3 scripts/deck_cycle.py build_<deck>.py                 # build + build-time lint
    python3 scripts/deck_cycle.py build_<deck>.py --render        # …+ render + render-time lint
    python3 scripts/deck_cycle.py build_<deck>.py --render --fast # …re-rendering changed pages only
    python3 scripts/deck_cycle.py build_<deck>.py --slides 3,7    # render only these pages
    python3 scripts/deck_cycle.py build_<deck>.py --nudge-again "<why>"   # after an escalation

Exit code uses lint_deck.py's vocabulary, so a caller can tell the two apart:
    2 = a stage could not run   ·   1 = everything ran and the deck has findings   ·   0 = clean
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from written_reason import reason_width  # noqa: E402  (one shared definition, never a copy)

# Guard 4 — the loop breaker. A fault is keyed by (stage, slide, lint code), never by the message:
# the whole failure mode is that each nudge changes the NUMBERS in the message while the fault
# stays the same fault.
STREAK_LIMIT = 3
STATE_NAME = ".deck-cycle-state.json"
# An override has to be a sentence someone can disagree with later, like every other waiver in this
# skill — long enough that typing it is a decision rather than a reflex. Measured in
# `written_reason.reason_width`, so a Chinese reason is not refused for saying more in fewer
# characters (a 17-character Chinese sentence used to miss a 20-codepoint floor).
OVERRIDE_MIN = 20


def _nudge_fingerprint(script_path: Path) -> str | None:
    """Fingerprint a build script's STRUCTURE, blind to every numeric literal.

    This is what makes the escalation enforceable instead of advisory. "Stop nudging" cannot be
    checked by asking the author whether they nudged; it CAN be checked by asking the file. A
    nudge — 1.02 → 0.98, 14 → 13, a y offset moved by a tenth — leaves the AST identical once
    numbers are normalized, so an unchanged fingerprint IS the definition of another nudge.

    Deliberately NOT normalized: strings and everything else. Shortening the words on a slide is a
    real fix for OVERFLOW, restructuring is a real fix for anything, and both change the shape.
    Booleans are left alone too (`True`/`False` are decisions, not magnitudes) — Python spells them
    as constants that would otherwise fold into the same bucket as 0 and 1.

    Returns None when the file cannot be parsed (mid-edit, or not Python). An unreadable file is
    not evidence of a nudge, so the enforcement fails OPEN — a checker that cannot see must not
    block; the build is about to fail with its own SyntaxError anyway, which is the better message.
    """
    try:
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, complex)) \
                and not isinstance(node.value, bool):
            node.value = 0
    return hashlib.sha256(ast.dump(tree).encode("utf-8")).hexdigest()


def _fault_keys(build_out: str, lint_out: str | None) -> set[str]:
    """Extract stable per-slide fault keys from one cycle's verbatim outputs.

    build-time criticals: `[lint] ✗ slide  4 OVERFLOW      msg`  → `build:slide 4:OVERFLOW`
    render-time blockers: `  slide 4: TEXT NOT VISIBLE: msg`     → `deck:slide 4:TEXT NOT VISIBLE`
    ([warn] lines are advisory and never tracked — the loop this breaks is the fix-the-blocker loop).
    """
    keys: set[str] = set()
    for m in re.finditer(r"\[lint\] ✗ slide\s+(\d+)\s+(\S+)", build_out):
        keys.add(f"build:slide {int(m.group(1))}:{m.group(2)}")
    if lint_out is not None:
        for m in re.finditer(r"^  slide (\d+): (?!\[warn\])([^\n]+)", lint_out, re.M):
            msg = m.group(2)
            code = msg.split(":", 1)[0] if ":" in msg[:48] else " ".join(msg.split()[:4])
            keys.add(f"deck:slide {int(m.group(1))}:{code.strip()}")
    return keys


def _read_state(deck_dir: Path, script_name: str) -> dict:
    """Load the streak state, resetting it whenever it belongs to a different build script."""
    try:
        path = deck_dir / STATE_NAME
        state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        state = {}
    if not isinstance(state, dict) or state.get("script") != script_name:
        state = {"script": script_name, "streaks": {}}
    if not isinstance(state.get("streaks"), dict):
        state["streaks"] = {}
    return state


def _write_state(deck_dir: Path, state: dict) -> None:
    try:
        (deck_dir / STATE_NAME).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass                            # a loop aid must never be the reason a build cannot run


ESCALATION_ADVICE = (
    "   The third attempt is never another nudge. Adjusting a constant by a few points and\n"
    "   re-running is the strategy that has now failed three times on the same fault — stop\n"
    "   nudging and RE-DERIVE that slide's layout by MEASUREMENT: compute positions from the\n"
    "   real content (fit_text, measured ink heights, a stack pitch computed from the block\n"
    "   height), or rebuild the slide on a form helper that owns the geometry\n"
    "   (python3 scripts/sigs.py --example <form>). Measured precedent: 10+ nudge iterations\n"
    "   on one slide; the computed-fit rewrite landed on its first try."
)


def _enforce_escalation(deck_dir: Path, script_path: Path, override: str | None) -> tuple[bool, str]:
    """🔴 THE HARD CONSTRAINT. After an escalation, REFUSE a build whose script is another nudge.

    The escalation used to be a printed paragraph, which put it in the class of rule this repo
    keeps re-learning the cost of: a rule whose only enforcement is the model choosing to obey it
    fails silently, and a silent failure here means the loop it was written to break just carries
    on. So it is now a refusal, and the thing it refuses is defined by the FILE rather than by
    intent — `_nudge_fingerprint` is blind to numeric literals, so "the script changed only in its
    numbers" is exactly "unchanged fingerprint".

    Returns (allowed, message). It blocks only when ALL of these hold, which is why it costs
    nothing on a healthy loop:
      * a fault already escalated (>= STREAK_LIMIT consecutive failures), and
      * the build script is structurally identical to the run that escalated, and
      * no `--nudge-again "<reason>"` override was given.

    The override exists because a constant genuinely is the fix sometimes, and a gate with no way
    through stops being a gate and becomes something to work around. It is the same shape as every
    other waiver here: a written reason, recorded in the state file, never a bare flag. It does NOT
    reset the streak — one more nudge is a decision, not a fresh start.
    """
    state = _read_state(deck_dir, script_path.name)
    stuck = sorted(state.get("escalated") or ())
    if not stuck:
        return True, ""
    fp = _nudge_fingerprint(script_path)
    if fp is None or fp != state.get("fingerprint"):
        return True, ""                 # unparseable (fail open) or genuinely restructured
    if override:
        state.setdefault("overrides", []).append({"faults": stuck, "reason": override})
        _write_state(deck_dir, state)
        return True, ("\n── deck_cycle: nudging again ON THE RECORD " + "─" * 21 + "\n"
                      "   {}\n   (still failing: {})".format(override, " · ".join(stuck)))
    return False, (
        "\n── deck_cycle: REFUSED — this edit is another nudge " + "─" * 12 + "\n"
        "   Still open after {} consecutive runs: {}\n"
        "   The build script's structure is UNCHANGED since that run — only numbers moved, which\n"
        "   is the strategy that has already failed. So this run is refused before spending it.\n\n"
        "{}\n\n"
        "   If a constant really is the fix here, say why and it runs:\n"
        "     python3 scripts/deck_cycle.py {} --nudge-again \"<why this constant is the fix>\"\n"
        "   State: {}".format(
            STREAK_LIMIT, " · ".join(stuck), ESCALATION_ADVICE, script_path.name,
            deck_dir / STATE_NAME))


def _loop_breaker(deck_dir: Path, script_path: Path, build_out: str,
                  lint_out: str | None, lint_ran: bool) -> None:
    """Track fault streaks across CONSECUTIVE runs of the same build script; escalate at 3.

    Render-stage keys are carried (not reset) by a build-only run: a run that never rendered has
    not judged them either way. Never changes THIS run's exit code and never suppresses a finding —
    what it changes is the NEXT run, via `_enforce_escalation`.
    """
    script_name = script_path.name
    state = _read_state(deck_dir, script_name)
    old = state["streaks"]
    current = _fault_keys(build_out, lint_out if lint_ran else None)
    streaks = {key: int(old.get(key, 0)) + 1 for key in current}
    if not lint_ran:
        for key, cnt in old.items():
            if key.startswith("deck:") and key not in streaks:
                streaks[key] = int(cnt)
    stuck = sorted(k for k in current if streaks[k] >= STREAK_LIMIT)
    state["streaks"] = streaks
    state["escalated"] = stuck
    # The fingerprint of the script AS IT JUST RAN — the baseline the next run is compared against.
    state["fingerprint"] = _nudge_fingerprint(script_path) if stuck else None
    _write_state(deck_dir, state)
    if stuck:
        print("\n── deck_cycle: LOOP BREAKER " + "─" * 36)
        for key in stuck:
            print(f"   {key.split(':', 1)[1]} — failing for {streaks[key]} consecutive runs")
        print(ESCALATION_ADVICE)
        print("   🔴 The next run is REFUSED unless the script changes structurally — a numbers-only\n"
              "      edit is what this just measured. To nudge anyway, say why:\n"
              "      --nudge-again \"<why this constant is the fix>\"")


def _run(label, cmd, cwd=None):
    """Run one stage; return (rc, seconds, combined output, label). Output is never trimmed."""
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return proc.returncode, time.perf_counter() - t0, (proc.stdout or "") + (proc.stderr or ""), label


def _emit(label, rc, dt, out):
    """A checker that RAN and found things is not a checker that broke.

    Both used to print [FAIL]. That is worse than untidy: the render-time lint reports findings on
    most real decks, so the common case trained the reader to read FAIL on that stage as noise —
    and the next time the stage genuinely could not run, the label would have said the same thing.
    `lint_deck.py` already separates them (1 = ran, found things · 2 = could not run), so this
    reuses that vocabulary rather than inventing one.
    """
    mark = {0: "ok      ", 1: "findings", 2: "BROKEN  "}.get(rc, "BROKEN  ")
    print(f"\n── {label}  [{mark}]  {dt:.2f}s " + "─" * max(0, 44 - len(label)))
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
    # --nudge-again "<reason>": the recorded way through an escalation (guard 4). Parsed here
    # rather than forwarded — it is this tool's own decision, and render_deck knows nothing of it.
    override = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--nudge-again" or a.startswith("--nudge-again="):
            if "=" in a:
                override = a.split("=", 1)[1]
                argv.pop(i)
            else:
                override = argv[i + 1] if i + 1 < len(argv) else ""
                del argv[i:i + 2]
            continue
        i += 1
    if override is not None and reason_width(override) < OVERRIDE_MIN:
        print("deck_cycle: --nudge-again needs a REASON of at least {} characters — a sentence "
              "someone can disagree with later, not a flag.\n"
              "  It is recorded in {} beside the deck, like every other waiver in this skill."
              .format(OVERRIDE_MIN, STATE_NAME))
        return 2

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

    # Guard 4, the hard half: refuse BEFORE spending the build when the previous run escalated and
    # this edit is another nudge. Refusing after would still cost the cycle it exists to save.
    allowed, note = _enforce_escalation(deck_dir, script_path, override)
    if note:
        print(note)
    if not allowed:
        return 2

    stages = []
    rc, dt, out, label = _run("build (+ build-time lint)", [sys.executable, str(script_path)],
                              cwd=str(deck_dir))
    # A build either produced a deck or it did not; there is no "ran but found things" for it,
    # so any nonzero is BROKEN.
    _emit(label, 0 if rc == 0 else 2, dt, out)
    stages.append((label, rc, dt))
    if rc != 0:
        # Guard 3. The build script's own lint_layout(strict=True) raises on a CRITICAL geometry
        # fault. Rendering past that would produce pixels of a deck that is known to be broken and
        # invite reasoning about them as if they were finished.
        print("\ndeck_cycle: STOPPED before rendering — the build did not complete. A critical "
              "layout fault is a reason to fix the build, not to look at the render.")
        # Guard 4. This is the path the nudge loop lives on — count the streak before returning.
        _loop_breaker(deck_dir, script_path, out, None, False)
        return 2

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
        return 2

    lint_out, lint_ran = None, False
    if render:
        rdir = deck_dir / "render"
        rc_r, dt_r, out_r, lab_r = _run("render", [sys.executable, str(HERE / "render_deck.py"),
                                                   str(pptx), str(rdir)] + passthru)
        _emit(lab_r, 0 if rc_r == 0 else 2, dt_r, out_r)
        stages.append((lab_r, rc_r, dt_r))
        if rc_r == 0:
            rc_l, dt_l, out_l, lab_l = _run("render-time lint",
                                            [sys.executable, str(HERE / "lint_deck.py"),
                                             str(pptx), str(rdir)])
            _emit(lab_l, rc_l, dt_l, out_l)
            stages.append((lab_l, rc_l, dt_l))
            if rc_l != 2:
                lint_out, lint_ran = out_l, True
        else:
            print("\ndeck_cycle: the render did not complete, so the render-time lint was not "
                  "run — it reads the PNGs, and linting a stale or partial set reports the "
                  "previous deck.")

    # Guard 4. The build succeeded (its ✗ lines cleared), so only render-time blockers can extend
    # a streak here — and only when the lint actually ran and judged them.
    _loop_breaker(deck_dir, script_path, out, lint_out, lint_ran)

    total = sum(d for _l, _r, d in stages)
    line = " · ".join(f"{l} {d:.1f}s" for l, _r, d in stages)
    print(f"\n── cycle  {total:.1f}s  ({line})")
    if not render:
        print("   render not run (add --render). The build-time lint above is geometry only; "
              "pixel-level checks and the per-slide visual read still need a render.")
    # Same vocabulary as lint_deck.py, so a caller can tell the two apart:
    #   2 = a stage could not run   ·   1 = everything ran and the deck has findings   ·   0 = clean
    if any(r >= 2 for _l, r, _d in stages):
        return 2
    return 1 if any(r for _l, r, _d in stages) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
