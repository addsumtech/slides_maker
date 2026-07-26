#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Two-sided regression test for the render-time lint.

Every check here exists because a REAL deck shipped the defect, or because a real deck was
falsely flagged for craft. The two directions matter equally and are asserted separately:

  PASS deck — ordinary, correctly-built slides plus two DECLARED exceptions (a rhymed triptych,
              a quiet pause page). Zero hard findings. A change that breaks one of these is
              catching craft rather than defects, which is how a rule set makes decks worse.
  FAIL deck — one slide per defect the gates must catch. Each was clean before these checks
              existed; that was the bug.

Run:  python3 tests/test_lint_regressions.py
"""
import pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def lint(pptx, renders):
    r = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(pptx),
                        "--renders", str(renders), "--static"],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="lintfx-"))
    subprocess.run([sys.executable, str(HERE / "lint_fixture.py")], cwd=tmp, check=True,
                   capture_output=True)
    for d in ("fx_pass", "fx_fail"):
        subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"),
                        str(tmp / f"{d}.pptx"), str(tmp / f"{d}_render")],
                       cwd=tmp, capture_output=True)

    ok, bad = [], []

    def ran(out, label):
        """A token's ABSENCE only means 'suppressed' if the lint actually ran. Without this the
        harness reads a crash as two passing waivers — the same read-silence-as-success mistake
        the checks below exist to catch."""
        if "layout finding(s)" not in out:
            bad.append(f"{label}: lint did not complete, so no assertion below is meaningful:\n"
                       + out.strip()[:400])
            return False
        return True

    p_out = lint(tmp / "fx_pass.pptx", tmp / "fx_pass_render")
    if not ran(p_out, "PASS deck"):
        print("\n".join("  FAIL " + b for b in bad)); return 1
    if "0 layout finding(s)" in p_out:
        ok.append("PASS deck has zero hard findings")
    else:
        bad.append("PASS deck gained a hard finding — a change is flagging craft, not a defect:\n"
                   + "\n".join(l for l in p_out.splitlines() if ": " in l and "[warn]" not in l))
    # the two DECLARED exceptions must actually be honoured
    if "LAYOUT SAMENESS" in p_out:
        bad.append("declared design_intent(rhyme=) did not suppress LAYOUT SAMENESS — a deliberate "
                   "triptych is being flagged as sameness, and the documented waiver is dead again")
    else:
        ok.append("declared rhyme suppresses LAYOUT SAMENESS")
    if "UNDERFILLED" in p_out:
        bad.append("declared design_intent(envelope=) did not suppress UNDERFILLED — the "
                   "deliberately quiet page cannot be built clean")
    else:
        ok.append("declared quiet envelope suppresses UNDERFILLED")

    f_out = lint(tmp / "fx_fail.pptx", tmp / "fx_fail_render")
    if not ran(f_out, "FAIL deck"):
        print("\n".join("  FAIL " + b for b in bad)); return 1
    for token, what in [
        ("under 3:1, the floor for text at ANY size", "text below the absolute contrast floor is caught"),
        ("RULE THROUGH TEXT", "a hairline painted over type is caught"),
        ("OCCLUSION", "a panel painted over a sentence is caught"),
        ("LAYOUT SAMENESS", "UNdeclared sameness is still flagged (the waiver is not a blanket)"),
        ("UNDERFILLED", "an UNdeclared thin page is still flagged"),
    ]:
        (ok if token in f_out else bad).append(
            what if token in f_out else f"FAIL deck: {token} was NOT raised — the check regressed")

    # ── the corpus that matters most: the skill's OWN reference deck. A change that adds a hard
    # finding here is a change that would fail the file SKILL.md tells every builder to copy.
    # This is not hypothetical: promoting the 3.0-4.5 contrast band to a hard failure looked
    # obviously right, passed both synthetic fixtures, and hard-failed this deck four times on
    # accent labels at 4.27:1. Synthetic fixtures cannot tell strictness from correctness; a real
    # deck built by the skill's own example can.
    ex = HERE.parent / "references" / "examples" / "build_example_generic.py"
    if ex.is_file():
        import os
        env = dict(os.environ, PYTHONPATH=str(SCRIPTS))
        r = subprocess.run([sys.executable, str(ex)], cwd=tmp, capture_output=True, text=True, env=env)
        demo = None
        for line in (r.stdout + r.stderr).splitlines():
            if "saved ->" in line:
                demo = pathlib.Path(line.split("saved ->")[1].split("|")[0].strip())
        if demo and demo.is_file():
            subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"), str(demo),
                            str(tmp / "ex_render")], cwd=tmp, capture_output=True, env=env)
            e_out = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(demo),
                                    "--renders", str(tmp / "ex_render")],
                                   capture_output=True, text=True, env=env).stdout
            n = next((int(l.split(":")[-1].split("layout")[0].strip())
                      for l in e_out.splitlines() if "layout finding(s)" in l), None)
            BASE = 3          # the example deck's own pre-existing footer overlap on slide 4
            if n is None:
                bad.append("reference example deck: lint did not complete")
            elif n <= BASE:
                ok.append(f"reference example deck holds at {n} hard findings (baseline {BASE})")
            else:
                bad.append(f"reference example deck rose to {n} hard findings (baseline {BASE}) — a "
                           f"change is failing the deck the skill tells builders to copy:\n"
                           + "\n".join(l for l in e_out.splitlines()
                                        if ": " in l and "[warn]" not in l and "[stats]" not in l))
        else:
            bad.append("reference example deck could not be built — the corpus check did not run")

    for line in ok:
        print("  ok   " + line)
    for line in bad:
        print("  FAIL " + line)
    print(f"\n{len(ok)} passed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
