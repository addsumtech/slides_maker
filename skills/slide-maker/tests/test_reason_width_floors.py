#!/usr/bin/env python3
"""A written-reason floor must mean the same amount of INFORMATION in every language.

`len()` counts codepoints, so `len(reason) < 12` is "12 letters" in English and about 24 letters'
worth in Chinese. Measured on a real Chinese deck built with this skill: `audience_brief` rejected
「敢不敢把求职材料交给它」 (11 codepoints, width 22) while a 12-letter English phrase carrying a
third as much passed. `written_reason.reason_width` had shipped months earlier; four modules
simply never reached for it — two of them written the same day as a module that used it
correctly. Knowing the rule did not make anyone apply it, so the guard is the deliverable.

This file covers what `check_reason_width.py --list` cannot: that the guard DETECTS the form the
bug is actually written in, that it does not fire on correct code, and that every floor in the
repo now behaves identically in both scripts.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audience_brief as ab          # noqa: E402
import check_reason_width as crw     # noqa: E402
import written_reason as wr          # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


# ── 🔴 THE GUARD MUST DETECT THE FORM THE BUG IS WRITTEN IN ──────────────────────────────────────
# The first pattern was `len\s*\([^)]*\)\s*<=?\s*MIN_…`, which cannot cross the inner `)` of
# `len(str(x.get("k") or "").strip())` — the form 10 of the 12 real sites used. It reported CLEAN
# on the planted bug. A guard that only catches the easy spelling is worse than none.
NESTED = 'if len(str(r.get("needs") or "").strip()) < MIN_TEXT:'
SIMPLE = "if len(res) < MIN_TEXT:"
FIXED = "if _w(r.get(\"needs\")) < MIN_TEXT:"
LITERAL = "if len(str(_iv[k]).strip()) < 2:"          # emptiness test, not an information floor
UNRELATED = "if depth < MIN_TEXT and len(rows) > 3:"   # floor and length, unrelated to each other

with tempfile.TemporaryDirectory() as td:
    for name, line, want in (("nested", NESTED, True), ("simple", SIMPLE, True),
                             ("fixed", FIXED, False), ("literal", LITERAL, False),
                             ("unrelated", UNRELATED, False)):
        f = Path(td) / (name + ".py")
        f.write_text("MIN_TEXT = 12\n\n\ndef g(r, res, depth, rows, _iv, k):\n    " + line
                     + "\n        pass\n", encoding="utf-8")
        got = bool(crw.hits(f))
        check(got == want,
              "the guard {} `{}` — it must {}".format("fired on" if got else "MISSED", line,
                                                      "catch it" if want else "stay silent"))

# ── the repo is clean AND the guard was pointed at something ────────────────────────────────────
r = subprocess.run([sys.executable, str(SCRIPTS / "check_reason_width.py")],
                   capture_output=True, text=True)
check(r.returncode == 0, "check_reason_width.py reports problems:\n{}".format(r.stdout))
check("0 problem" in r.stdout and " file(s) scanned" in r.stdout,
      "the guard did not report how many files it scanned — a scan of nothing reports clean "
      "forever: {!r}".format(r.stdout.strip()))
n = int(r.stdout.split(" file(s) scanned")[0].split()[-1])
check(n > 40, "the guard only scanned {} file(s); scripts/ is far larger, so its glob has "
              "stopped matching".format(n))

# ── 🔴 THE BAR IS THE SAME IN BOTH LANGUAGES — the measured failure, encoded ─────────────────────
CN = "敢不敢把求职材料交给它"                      # 11 codepoints, width 22
check(len(CN) < ab.MIN_TEXT, "the example no longer demonstrates the bug (len {} >= MIN_TEXT {})"
                             .format(len(CN), ab.MIN_TEXT))
check(wr.reason_width(CN) >= ab.MIN_TEXT, "reason_width no longer clears the floor for the real "
                                          "Chinese phrase this was found on")
brief = {"who": "正在找工作、可能装这个工具的人",
         "decisions": [{"decision": CN, "needs": "它在编造这件事上的边界划在哪里"},
                       {"decision": "要不要把这个工具装到自己的环境里", "needs": "它解决的是什么场景"},
                       {"decision": "用它还是继续用现在写简历的办法", "needs": "和通用 AI 相比差在哪"}]}
f = ab.faults(brief)
check(not any("decision" in x and "empty" in x for x in f),
      "a real CJK decision was still rejected as empty: {}".format(f[:1]))

# …and the floor did not simply disappear: a genuinely thin reason is still caught, in both scripts
thin_cn = dict(brief)
thin_cn["decisions"] = [dict(d) for d in brief["decisions"]]
thin_cn["decisions"][0]["needs"] = "不知道"                      # width 6, under any floor
check(any("needs" in x for x in ab.faults(thin_cn)),
      "a three-character `needs` passed — widening the measure must not remove the floor")
thin_en = dict(brief)
thin_en["decisions"] = [dict(d) for d in brief["decisions"]]
thin_en["decisions"][0]["needs"] = "dunno"
check(any("needs" in x for x in ab.faults(thin_en)), "a five-letter `needs` passed")

# ── every module that owns a floor imports the ONE definition ───────────────────────────────────
for name in ("audience_brief", "blind_read", "composition_probe", "taste_ledger",
             "material_probe", "delegated_picks"):
    src = (SCRIPTS / (name + ".py")).read_text(encoding="utf-8")
    check("reason_width" in src,
          "{}.py applies a written-reason floor without importing reason_width — copied floors "
          "have drifted in this repo before".format(name))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_reason_width_floors] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
