#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dispatch_brief.py prints a dispatch for every critic the review tiers dispatch.

WHY. The `fast` tier — the post-build DEFAULT — dispatches "1 generalist, carrying BOTH lenses"
(references/critic-panel.md, SKILL.md Step 5), and agents/critic.md tells a sole critic to run both lenses
as two passes. But `dispatch_brief.py prompt --role critic` refused any dispatch without `--lens A|B`, and
its refusal called a two-lens critic "a different, weaker review". So the default tier had no prompt: a
real run (iPhone 18 explainer, 2026-10-17) dispatched two single-lens critics instead, paying the
`standard` tier's cost under the `fast` label.

Run: python3 tests/test_dispatch_brief.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "dispatch_brief.py"
ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


def run(*args):
    r = subprocess.run([sys.executable, str(TOOL)] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


tmp = Path(tempfile.mkdtemp(prefix="dispatch-brief-"))
deck = tmp / "deck"
deck.mkdir()
brief = tmp / "brief.md"
code, out, err = run("init", "--deck", str(deck), "--out", str(brief)) if "--out" in run("init", "-h")[1] \
    else run("init", "--deck", str(deck))
if not brief.exists():                       # init chose its own path: it prints it on the last line
    brief = Path((out.strip().splitlines() or [""])[-1].strip())
check(brief.exists(), "init wrote a brief ({})".format(brief))
text = brief.read_text(encoding="utf-8")
brief.write_text(text.replace("<<FILL>>", "no source; web-supplement: free within a cap of 10"), encoding="utf-8")

code, out, err = run("prompt", "--brief", str(brief), "--role", "critic", "--lens", "AB", "--round", "1",
                     "--deck", str(deck))
check(code == 0, "--lens AB prints a dispatch (exit {}; {})".format(code, err.strip()[:120]))
check("sole critic" in out.lower() and "both lenses" in out.lower() and "`fast`" in out,
      "the AB prompt names the sole critic of the fast tier and both lenses ({!r})".format(out[:160]))
check("two passes" in out and "coverage.passes" in out,
      "the AB prompt asks for the two passes the validator reads off coverage.passes")

code, out, err = run("prompt", "--brief", str(brief), "--role", "critic", "--round", "1")
check(code == 1 and "AB" in err and "fast" in err,
      "a critic dispatch with no lens is refused, and the refusal names AB for the fast tier ({})".format(
          err.strip()[:160]))

code, out, err = run("prompt", "--brief", str(brief), "--role", "critic_sole", "--round", "1")
check(code == 2, "the internal critic_sole prompt is not offered as a --role (exit {})".format(code))

code, out, err = run("prompt", "--brief", str(brief), "--role", "critic", "--lens", "A", "--round", "2")
check(code == 0 and "LENS A ONLY" in out, "--lens A still prints the single-lens dispatch")

# ── the design dispatch names the APPROVED content plan FILE (audit 2026-10-29) ─────────────────────────────
# The design prompt said the approved content plan was "in the deck brief", and the brief had no slot for it —
# so the art director was pointed at a document that carried no plan.
b2 = tmp / "brief2.md"
code, out, err = run("init", "--deck", str(deck), "--out", str(b2))
t2 = b2.read_text(encoding="utf-8")
check("## Approved plans" in t2 and "content plan:" in t2 and "design plan:" in t2,
      "init writes an Approved plans slot with content plan:/design plan: lines")
b2.write_text(t2.replace("<<FILL>>", "no source; web-supplement: free within a cap of 10"), encoding="utf-8")
code, out, err = run("prompt", "--brief", str(b2), "--role", "planner")
check(code == 0, "the planner dispatch needs no approved plan — it writes it (exit {}; {})".format(code, err.strip()[:160]))
code, out, err = run("prompt", "--brief", str(b2), "--role", "design")
check(code == 1 and "content plan" in err, "the design dispatch is refused while the content plan is pending "
                                          "(exit {}; {})".format(code, err.strip()[:160]))
code, out, err = run("check", "--brief", str(b2), "--role", "design")
check(code == 1 and "content plan" in err, "check --role design requires the content plan path (exit {}; {})"
      .format(code, err.strip()[:160]))
plan = tmp / "content-plan.md"
b2.write_text(b2.read_text(encoding="utf-8").replace("content plan: pending", "content plan: " + str(tmp / "nope.md")),
              encoding="utf-8")
code, out, err = run("prompt", "--brief", str(b2), "--role", "design")
check(code == 1 and "nope.md" in err, "a content plan path that does not exist is refused by name ({})"
      .format(err.strip()[:160]))
plan.write_text("# Content plan\n", encoding="utf-8")
b2.write_text(b2.read_text(encoding="utf-8").replace(str(tmp / "nope.md"), str(plan)), encoding="utf-8")
code, out, err = run("check", "--brief", str(b2), "--role", "design")
check(code == 0, "check --role design passes once the content plan exists (exit {}; {})".format(code, err.strip()[:160]))
code, out, err = run("prompt", "--brief", str(b2), "--role", "design")
check(code == 0 and str(plan) in out, "the design prompt names the content plan FILE ({!r})".format(out[:300]))
code, out, err = run("prompt", "--brief", str(b2), "--role", "section", "--section", "1", "--slides", "1-4")
check(code == 1 and "design plan" in err, "a section author also needs the approved design plan (exit {}; {})"
      .format(code, err.strip()[:160]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
if bad:
    print("[test_dispatch_brief] FAILED: {} problem(s)".format(len(bad)))
    sys.exit(1)
print("[test_dispatch_brief] ok")
