#!/usr/bin/env python3
"""render_deck's command line: --help works, renders default to the folder BESIDE the deck (where the gates read them), and --slides naming every slide is a full render that the design checkpoint holds."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)



import json, os, subprocess
import deckkit as dk
RD = str(ROOT / "scripts" / "render_deck.py")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, RD] + list(args), capture_output=True, text=True, cwd=cwd)


# --help prints the usage and exits 0 (it was "unrecognised option(s): --help", exit 1)
for flag in ("--help", "-h"):
    r = run(flag)
    check(r.returncode == 0 and "--slides" in r.stdout and "out_dir" in r.stdout, "{}: usage on stdout, exit 0: rc={} {}".format(flag, r.returncode, (r.stdout + r.stderr)[:200]))
td = Path(tempfile.mkdtemp()) / "a deck 文件夹"
td.mkdir()
prs = dk.blank_deck(10.0, 5.625)
for i in range(4):
    dk.text(dk.add_slide(prs), 0.8, 0.8, 8, 1, [[("Slide {}".format(i + 1), 32, dk.DEEP, True, False)]])
deck = td / "deck.pptx"
prs.save(str(deck))
# the default output folder is BESIDE the deck (the gates read <deck>/render), not the process's CWD
elsewhere = Path(tempfile.mkdtemp())
r = run(str(deck), "--slides", "1", cwd=str(elsewhere))
check(r.returncode == 0 and (td / "render" / "slide01.png").exists() and not (elsewhere / "render").exists(),
      "renders land beside the deck: rc={} {}".format(r.returncode, (r.stdout + r.stderr)[-300:]))
# what it prints next runs AS PRINTED, in a folder with a space and CJK in its path (the next: line was unquoted)
r = run(str(deck), str(td / "full render"), cwd=str(elsewhere))
nxt = [l_[len("next: "):].split("  #")[0] for l_ in r.stdout.splitlines() if l_.startswith("next: ")]
check(nxt, "a next: line is printed: {}".format(r.stdout[-300:]))
if nxt:
    rr = subprocess.run(nxt[0], shell=True, capture_output=True, text=True, cwd=str(elsewhere))
    check(rr.returncode in (0, 1) and "No such file" not in rr.stderr and "usage" not in rr.stderr.lower(),
          "the printed next: command runs as printed: rc={} {}".format(rr.returncode, rr.stderr[-200:]))
listed = [l_.strip() for l_ in r.stdout.splitlines() if l_.strip().endswith(".png") and "/" in l_ and " read " not in l_]
check(listed and all(Path(x).exists() for x in listed), "every slide PNG it lists is one existing path per line: {}".format(listed[:3]))
# a content plan of 4 slides with no design checkpoint: a probe of one slide is exempt, a list of EVERY slide is
# a full render and is refused like one (it was a loophole: any --slides skipped the checkpoint)
(td / ".deck-gates.json").write_text(json.dumps({"content": {"slides": [{"n": i} for i in range(4)]}}), encoding="utf-8")
r = run(str(deck), str(td / "probe"), "--slides", "2")
check(r.returncode == 0, "a one-slide probe is exempt: {}".format((r.stdout + r.stderr)[-300:]))
r = run(str(deck), str(td / "all"), "--slides", "1,2,3,4")
check(r.returncode != 0 and "STEP 2 NOT DONE" in (r.stdout + r.stderr), "--slides listing every slide is refused like a full render: rc={} {}".format(r.returncode, (r.stdout + r.stderr)[-300:]))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_render_cli] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
