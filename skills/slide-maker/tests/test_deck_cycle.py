#!/usr/bin/env python3
"""deck_cycle.py and the contact sheet — and the guards that keep them from costing quality.

Both exist because a deck's wall clock is round-trips, not computation: 9.1 seconds of
deterministic pipeline inside an 88-minute build. Both are therefore shortcuts through a checking
pipeline, which is exactly how a pipeline stops checking. The guards are the point, so they are
what this suite asserts:

  · findings are printed VERBATIM, never summarised to a count — a number cannot be acted on;
  · rendering is OPT-IN, so the common iteration stays 1.8s instead of 7.2s;
  · a CRITICAL build fault STOPS the cycle before rendering;
  · the contact sheet is ADDITIVE — the render still writes every per-slide PNG, and the next-step
    hint still asks for all of them.
"""
import os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

ok, bad = [], []
for _m in ("pptx", "PIL"):
    try:
        __import__(_m)
    except ImportError:
        print(f"skip: {_m} not installed")
        raise SystemExit(0)

TMP = pathlib.Path(tempfile.mkdtemp(prefix="cycle-"))

GOOD = '''
import sys
sys.path.insert(0, %r)
import deckkit as dk
from pptx.dml.color import RGBColor as C
dk.FONT = "Helvetica Neue"
prs = dk.blank_deck()
for i in range(3):
    s = dk.add_slide(prs)
    dk.slide_background(s, "F5F1E6")
    dk.text(s, 0.6, 0.5, 8.8, 0.7, [[("Section %%d" %% (i + 1), 28, C.from_string("1F3B2F"), True, False)]])
    dk.text(s, 0.6, 1.6, 8.0, 0.8, [[("a line of ordinary body copy", 14, C.from_string("1F3B2F"), False, False)]])
dk.lint_layout(prs, strict=True)
prs.save("deck.pptx")
print("saved ->", "deck.pptx", "| slides:", 3)
''' % str(SCRIPTS)

# A CRITICAL geometry fault: text far off the canvas. lint_layout(strict=True) raises.
BAD = GOOD.replace('dk.text(s, 0.6, 1.6, 8.0, 0.8,', 'dk.text(s, 14.0, 9.9, 8.0, 0.8,')


def _write(name, body):
    d = TMP / name
    d.mkdir(exist_ok=True)
    (d / "build.py").write_text(body, encoding="utf-8")
    return d


def _cycle(d, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / "deck_cycle.py"), "build.py"] + list(args),
                       capture_output=True, text=True, cwd=str(d))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# ---------------------------------------------------------------- guard 2: render is opt-in
d = _write("good", GOOD)
rc, out = _cycle(d)
if rc == 0 and "build (+ build-time lint)" in out:
    ok.append("a clean build cycles green")
else:
    bad.append(f"a clean build did not cycle: rc={rc}\n{out[-500:]}")

if not (d / "render").exists():
    ok.append("rendering is OPT-IN — the common iteration stays the 1.8s geometry pass instead "
              "of paying 5.4s for pixels nobody asked for")
else:
    bad.append("the default cycle rendered without being asked")

if "render not run (add --render)" in out:
    ok.append("…and it SAYS the render did not run, so a skipped pixel check is never mistaken "
              "for a passed one")
else:
    bad.append("a cycle without a render did not say so")

rc, out = _cycle(d, "--render")
if rc == 0 and (d / "render" / "slide01.png").exists():
    ok.append("--render adds the render and the render-time lint")
else:
    bad.append(f"--render did not produce slide PNGs: rc={rc}\n{out[-500:]}")

# ---------------------------------------------------------------- guard 1: verbatim, not counted
if "no layout faults" in out or "[lint]" in out:
    ok.append("the build-time lint's own output is passed through verbatim")
else:
    bad.append("the build lint's output did not reach the cycle report")

import re                                                    # noqa: E402
if not re.search(r"\b\d+\s+findings?\b(?!.*:)", out.split("── cycle")[-1]):
    ok.append("the cycle summary reports STAGES and times, not a finding count standing in for "
              "the findings themselves")
else:
    bad.append("the cycle summary substituted a count for the findings")

# Parsed, not grepped — for the third time in this codebase a substring search matched a file's
# own PROSE about the thing's absence ("There is no --quiet"). Strip the docstrings and ask
# whether any CODE consumes such a flag.
import ast                                                   # noqa: E402

_src = (SCRIPTS / "deck_cycle.py").read_text()
_tree = ast.parse(_src)
_lits = [n.value for n in ast.walk(_tree)
         if isinstance(n, ast.Constant) and isinstance(n.value, str)
         and not (isinstance(getattr(n, "parent", None), ast.Module))]
_code_strings = {s for s in _lits if s.startswith("--")}
if not ({"--quiet", "--summary", "--brief"} & _code_strings):
    ok.append("no --quiet / --summary flag exists in code — findings cannot be suppressed "
              "(checked by parsing: the file's own prose says 'there is no --quiet')")
else:
    bad.append(f"a suppression flag is parsed by the code: {_code_strings}")

# ---------------------------------------------------------------- guard 3: stop before rendering
d2 = _write("bad", BAD)
rc, out = _cycle(d2, "--render")
if rc != 0:
    ok.append("a CRITICAL build fault fails the cycle")
else:
    bad.append("a deck with a critical layout fault cycled green")

if "STOPPED before rendering" in out:
    ok.append("…and it stops BEFORE rendering — a deck with a critical geometry fault should not "
              "be rasterised and then reasoned about as if it were finished")
else:
    bad.append("the cycle rendered past a critical build fault")

if not (d2 / "render" / "slide01.png").exists():
    ok.append("no pixels were produced for the broken deck")
else:
    bad.append("the broken deck was rendered anyway")

# ---------------------------------------------------------------- the contact sheet is ADDITIVE
d3 = _write("sheet", GOOD)
subprocess.run([sys.executable, str(SCRIPTS / "deck_cycle.py"), "build.py", "--render"],
               capture_output=True, text=True, cwd=str(d3))
rdir = d3 / "render"
slides = sorted(p.name for p in rdir.glob("slide*.png"))
if len(slides) == 3 and (rdir / "contact.png").exists():
    ok.append("the sheet is written BESIDE every per-slide PNG, not instead of any")
else:
    bad.append(f"per-slide PNGs missing or no contact sheet: {slides}")

p = subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"), "deck.pptx", "render"],
                   capture_output=True, text=True, cwd=str(d3))
hint = (p.stdout or "") + (p.stderr or "")
if "first read" in hint and "contact.png" in hint and "then read ALL 3 slide PNGs" in hint:
    ok.append("the next-step hint puts the sheet FIRST and still asks for ALL slide PNGs")
else:
    bad.append("the next-step hint lost either the sheet or the per-slide reads")

if "never replaces" in hint or "does not replace" in hint:
    ok.append("the hint says in words that the sheet does not replace the per-slide reads — the "
              "one way this artifact can cost quality is by being used as a substitute")
else:
    bad.append("nothing in the hint prevents the sheet being read as a substitute")

# a 1-page deck has no deck-level shape to look at
ONE = GOOD.replace("for i in range(3):", "for i in range(1):").replace('"| slides:", 3', '"| slides:", 1')
d4 = _write("one", ONE)
subprocess.run([sys.executable, str(SCRIPTS / "deck_cycle.py"), "build.py", "--render"],
               capture_output=True, text=True, cwd=str(d4))
if not (d4 / "render" / "contact.png").exists():
    ok.append("a 1-page deck gets no contact sheet — there is no deck-level shape in one page")
else:
    bad.append("a contact sheet was made for a single slide")

# ---------------------------------------------------------------- nothing else was rerouted
rd = (SCRIPTS / "render_deck.py").read_text()
if "deck_cycle" not in rd and "deck_cycle" not in (SCRIPTS / "lint_deck.py").read_text():
    ok.append("neither render_deck.py nor lint_deck.py routes through deck_cycle — it is an "
              "alternative entry point, so no stage can be dropped by editing one file")
else:
    bad.append("an existing entry point now depends on deck_cycle.py")

rr = (SCRIPTS / "roundtrip_report.py").read_text()
if "MUST NEVER BECOME A GATE" in rr:
    ok.append("roundtrip_report carries its own no-gate contract (a metric that rewards looking "
              "at less must not become a target)")
else:
    bad.append("roundtrip_report lost its no-gate contract")
for f in ("render_deck.py", "lint_deck.py", "codex_delivery_gate.py"):
    if "roundtrip" in (SCRIPTS / f).read_text():
        bad.append(f"{f} reads the round-trip metric — it must stay out of every gate")
if not any("roundtrip" in b for b in bad):
    ok.append("no gate or pipeline script reads the round-trip metric")

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print(f"\n{len(ok)} passed, {len(bad)} failed")
raise SystemExit(1 if bad else 0)
