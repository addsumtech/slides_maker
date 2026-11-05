#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""progress.py — the user hears about the run while it happens, from the commands themselves.

Measured 2026-10-30 (two real runs, 9 slides): a full first render existed at minute 7.5–8.6 and the user
first saw a page at minute 34–41. What this suite holds the scripts to, run as real commands so the
assertion is on what an agent actually reads in the output, whichever agent it is:

  · outside a real run (no .deck-gates.json) nothing is printed and nothing is written — the examples'
    CI renders and every other test stay silent;
  · the interview's last answer announces the brief, in the deck's language;
  · the FIRST full render of a real run prints the early preview — the slide count, the contact sheet's
    absolute path, the measured time still to go, and an AGENT NEXT line naming the review command —
    and a second render never repeats it;
  · a critic dispatch announces the review on stderr, so the dispatch prompt on stdout stays clean;
  · every stage is said once, the state lives in <deck-dir>/.deck-progress.json, and a broken state
    file never fails the command that tried to announce.

Run:  python3 tests/test_progress.py
"""
import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import progress as P  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else f"{name}  {detail}")
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  {detail}"))


def run(*args, cwd=None):
    return subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True, cwd=cwd)


TMP = pathlib.Path(tempfile.mkdtemp(prefix="progress-"))


def deck_dir(name, language=None):
    d = TMP / name
    d.mkdir()
    g = {"interview": {"language": language}} if language else {}
    (d / ".deck-gates.json").write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    return d


# ───────────────────────────────────────────── the module
print("── announce")
plain = TMP / "not-a-run"
plain.mkdir()
check("outside a run: nothing printed", P.announce(str(plain), "preview", slides=9) == "")
check("outside a run: no state file written", not (plain / ".deck-progress.json").exists())

zh = deck_dir("zh", "中文")
txt = P.announce(str(zh), "preview", slides=9, contact="/x/render/contact.png")
check("zh deck: the preview is in Chinese, with step 3/6, the slide count and the contact sheet",
      "告诉用户（第 3/6 步）" in txt and "共 9 页" in txt and "/x/render/contact.png" in txt, txt)
check("zh deck: the measured time still to go is said as a range", "25–33 分钟" in txt, txt)
check("zh deck: the user is invited to comment now", "现在就可以提意见" in txt, txt)
check("a stage is said once", P.announce(str(zh), "preview", slides=9) == "")
st = json.loads((zh / ".deck-progress.json").read_text(encoding="utf-8"))
check("state records the stage time and the slide count", "preview" in st.get("stages", {}) and st.get("slides") == 9, st)

en = deck_dir("en", "English")
txt = P.announce(str(en), "brief")
check("en deck: English, step 1/6", txt.startswith("TELL THE USER (step 1/6):") and "brief is confirmed" in txt, txt)
check("no language recorded → English", P.announce(str(deck_dir("nolang")), "plan").startswith("TELL THE USER"))
check("'bilingual EN+中文' reads as Chinese (the user wrote Chinese)", P._lang(str(deck_dir("bi", "bilingual EN+中文"))) == "zh")
check("an unknown stage prints nothing", P.announce(str(en), "nonsense") == "")
long_deck = deck_dir("long", "English")
check("a deck much longer than the measured one is told it takes longer",
      "more slides take longer" in P.announce(str(long_deck), "preview", slides=24))
broken = deck_dir("broken", "English")
(broken / ".deck-progress.json").write_text("{not json", encoding="utf-8")
check("a corrupt state file never raises, and the stage is still said",
      P.announce(str(broken), "done").startswith("TELL THE USER"))

cx = TMP / "codex-only"
cx.mkdir()
(cx / ".codex-deck-evidence.json").write_text(json.dumps({"interview": {"language": "zh"}}), encoding="utf-8")
check("a Codex run with only .codex-deck-evidence.json is a run, and its interview language is used",
      "告诉用户（第 3/6 步）" in P.announce(str(cx), "preview", slides=9))

out = run(SCRIPTS / "progress.py", en, "plan")
check("CLI: announces a stage by hand, exit 0", out.returncode == 0 and "step 2/6" in out.stdout, out.stdout + out.stderr)
out = run(SCRIPTS / "progress.py", plain, "plan")
check("CLI outside a run: exit 2 and says why", out.returncode == 2 and "not a slide-maker run" in out.stderr, out.stderr)
out = run(SCRIPTS / "progress.py", en, "--status")
check("CLI --status lists every stage", out.returncode == 0 and all(s in out.stdout for s in P.STAGES), out.stdout)

# ───────────────────────────────────────────── the hooks, as commands
print("── hooks")
iv = deck_dir("interview", None)
out = run(SCRIPTS / "deck_gates.py", "interview", iv, "--set", "language=中文", "--set", "density=balanced",
          "--set", "length=9", "--set", "goal=年度汇报")
check("deck_gates interview: the last answer announces the brief, in Chinese",
      out.returncode == 0 and "告诉用户（第 1/6 步）" in out.stdout, out.stdout[-600:] + out.stderr[-300:])
out = run(SCRIPTS / "deck_gates.py", "interview", iv, "--set", "goal=年度汇报（改）")
check("deck_gates interview: changing an answer later does not announce again",
      out.returncode == 0 and "告诉用户" not in out.stdout, out.stdout[-400:])

rv = deck_dir("review-" + TMP.name.rsplit("-", 1)[-1], "English")   # the brief is named after it, in the system temp dir
out = run(SCRIPTS / "dispatch_brief.py", "init", "--deck", rv)
brief_path = out.stdout.strip().splitlines()[0] if out.returncode == 0 and out.stdout.strip() else ""
if brief_path:
    import dispatch_brief as DB
    _b = pathlib.Path(brief_path)
    _b.write_text(_b.read_text(encoding="utf-8").replace(
        DB.TODO, "filled for the test — English, balanced, 9 slides; web supplement: source only"), encoding="utf-8")
    out = run(SCRIPTS / "dispatch_brief.py", "prompt", "--brief", brief_path, "--role", "critic", "--lens", "AB",
              "--round", "1", "--deck", plain)
    check("a critic dispatch outside a run announces nothing (stderr has no TELL THE USER)",
          out.returncode == 0 and "TELL THE USER" not in out.stderr, (out.returncode, out.stderr[-300:]))
    out = run(SCRIPTS / "dispatch_brief.py", "prompt", "--brief", brief_path, "--role", "critic", "--lens", "AB",
              "--round", "1", "--deck", rv)
    check("dispatch_brief prompt --role critic: the review is announced on stderr, never in the prompt",
          "step 5/6" in out.stderr and "TELL THE USER" not in out.stdout, (out.returncode, out.stderr[-400:]))
    _b.unlink()                     # never leave a brief behind in the shared temp folder
else:
    check("dispatch_brief init made a brief to dispatch from", False, out.stdout + out.stderr)

# validate_review.py critic: the review-stage event every host produces (the Codex path has no dispatch script)
GOOD_CRITIC = {
    "purpose": "annual review, 12 min", "rubric_overlay": "work status update",
    "coverage": {"slides_opened": [1, 2, 3], "passes": ["content lens (full deck)", "design lens (full deck)"],
                 "stats_block_seen": True, "contract_card_seen": "none-declared"},
    "plan_audit": None,
    "probes": {"per_slide": [{"slide": 1, "first_read": "big title", "takeaway_guess": "visits grew"}],
               "memory_sentence": "visits grew; message understood"},
    "verdict": "revise", "summary": "Fix the clipped legend first.", "strengths": ["clean grid"],
    "findings": [{"id": "s2-crop-1", "slide": 2, "severity": "major", "dimension": "figures",
                  "issue": "legend clipped", "why": "the curves cannot be decoded",
                  "fix": "re-crop to include the legend", "fix_risk": "low"}],
}
vr = deck_dir("validate-review", "中文")
(vr / "critic.json").write_text(json.dumps(GOOD_CRITIC), encoding="utf-8")
out = run(SCRIPTS / "validate_review.py", "critic", vr / "critic.json")
check("validate_review critic, review JSON in the deck folder: valid, and the review stage is announced in Chinese",
      out.returncode == 0 and "告诉用户（第 5/6 步）" in out.stdout, out.stdout[-400:] + out.stderr[-300:])
out = run(SCRIPTS / "validate_review.py", "critic", vr / "critic.json")
check("validate_review a second round: not announced again", "告诉用户" not in out.stdout, out.stdout[-300:])
(plain / "critic.json").write_text(json.dumps(GOOD_CRITIC), encoding="utf-8")
out = run(SCRIPTS / "validate_review.py", "critic", plain / "critic.json")
check("validate_review outside a run: valid and silent", out.returncode == 0 and "告诉用户" not in out.stdout
      and "TELL THE USER" not in out.stdout, out.stdout[-300:])

soffice = shutil.which("soffice") or shutil.which("libreoffice") or os.environ.get("SOFFICE")
try:
    import pptx  # noqa: F401
    have_pptx = True
except ImportError:
    have_pptx = False
if soffice and have_pptx:
    from pptx import Presentation
    from pptx.util import Inches
    rd = deck_dir("render", "English")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for i in range(3):
        prs.slides.add_slide(prs.slide_layouts[6]).shapes.add_textbox(
            Inches(1), Inches(1), Inches(8), Inches(1)).text_frame.text = "Slide {}".format(i + 1)
    prs.save(str(rd / "deck.pptx"))
    out = run(SCRIPTS / "render_deck.py", rd / "deck.pptx", rd / "render")
    contact = os.path.abspath(str(rd / "render" / "contact.png"))
    check("render_deck, first render of a run: the early preview with 3 slides and the contact sheet's path",
          "TELL THE USER (step 3/6)" in out.stdout and "3 slides" in out.stdout and contact in out.stdout,
          out.stdout[-900:] + out.stderr[-300:])
    check("render_deck: the AGENT NEXT line says to tell the user before the next command, and does NOT hand the "
          "agent a review command to time (a real run fired it at once)",
          "AGENT NEXT:" in out.stdout and "before your next command" in out.stdout
          and "progress.py" not in out.stdout.split("AGENT NEXT:", 1)[-1].split("\n", 1)[0], out.stdout[-600:])
    nxt = [l for l in out.stdout.splitlines() if l.startswith("next:")]
    check("render_deck, first render: telling the user is step (1) of the next: line, the lint is (2) — agents act "
          "on next:, and both real runs skipped a preview printed above it",
          nxt and nxt[-1].startswith("next: (1) post the TELL THE USER block") and "(2) python3" in nxt[-1], nxt)
    out = run(SCRIPTS / "render_deck.py", rd / "deck.pptx", rd / "render", "--fast")
    check("render_deck, second render: no preview again", out.returncode == 0 and "TELL THE USER" not in out.stdout,
          out.stdout[-400:])
    check("render_deck, second render: next: is the plain lint command again",
          any(l.startswith("next: python3") for l in out.stdout.splitlines()), out.stdout[-300:])

    # deck_cycle --render (the Codex path's entry point) prints its own summary after the render's output,
    # so the render's next: line is no longer last; the cycle repeats the instruction at the very end.
    dc = deck_dir("cycle", "中文")
    (dc / "build_deck.py").write_text(
        "from pptx import Presentation\nfrom pptx.util import Inches\nimport os\n"
        "p = Presentation(); p.slide_width, p.slide_height = Inches(13.333), Inches(7.5)\n"
        "for i in range(2):\n"
        "    p.slides.add_slide(p.slide_layouts[6]).shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))"
        ".text_frame.text = '第 %d 页' % (i + 1)\n"
        "p.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deck.pptx'))\n", encoding="utf-8")
    out = run(SCRIPTS / "deck_cycle.py", dc / "build_deck.py", "--render", cwd=dc)
    tail = [l for l in out.stdout.splitlines() if l.strip()][-3:]
    check("deck_cycle --render, first render of a run: the preview printed AND the last lines say to post it first",
          "告诉用户（第 3/6 步）" in out.stdout and any(l.startswith("NEXT: before anything else, post the TELL THE USER")
                                                    for l in tail), (out.returncode, tail, out.stderr[-300:]))
    out = run(SCRIPTS / "deck_cycle.py", dc / "build_deck.py", "--render", cwd=dc)
    check("deck_cycle --render, again: no preview and no tell-the-user NEXT",
          "告诉用户" not in out.stdout and "post the TELL THE USER" not in out.stdout, out.stdout[-300:])
    nr = TMP / "no-record"
    nr.mkdir()
    shutil.copy(rd / "deck.pptx", nr / "deck.pptx")
    out = run(SCRIPTS / "render_deck.py", nr / "deck.pptx", nr / "render")
    check("render_deck outside a run (an example, a probe): silent, no state file",
          out.returncode == 0 and "TELL THE USER" not in out.stdout and not (nr / ".deck-progress.json").exists(),
          out.stdout[-300:])
else:
    print("  skip render hook: LibreOffice or python-pptx missing (CI's core job has both)")

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
print("[test_progress] " + ("ok" if not FAIL else f"FAILED: {len(FAIL)} problem(s)"))
raise SystemExit(1 if FAIL else 0)
