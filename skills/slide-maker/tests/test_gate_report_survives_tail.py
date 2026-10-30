#!/usr/bin/env python3
"""A gate report must stay readable when an agent reads only the TAIL of it.

🔴 WHY. Batching every fault into one run is only half the win. The other half is that the reader
actually SEES them — and every agent reads a long report the same way: `2>&1 | tail -N`, because
it wants the verdict without a wall of text. MEASURED, on the real 12-page build that motivated
this work:

  · `deck_gates.py` reported all 9 problems in ONE pass and said so on its FIRST line. The run
    read it through `tail -8`, cut the header off, fixed the three rows it could see, and paid
    three more round-trips finding the rest. The gate was right; the window hid the total.
  · `render_deck.py --gate-check` was worse. Under a pipe stdout is block-buffered and stderr is
    not, so its 30 stderr lines of FAILURES came out AHEAD of its 36 stdout `[gates]` lines in a
    `2>&1` merge. `tail -20` showed nothing but informational chatter and NOT ONE failure — a
    blocked gate that reads as clean.
  · `codex_delivery_gate.py` printed a bare `- ` list: no numbering, no total, so any window shows
    some errors with no hint that more exist.

So the invariant is not "the report contains the count" — it is "EVERY tail window reveals it".
`[4/9]` on each line plus a trailing total gives that for free, in any window of one line or more.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "tests"))

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def reveals_total(window: str) -> bool:
    """Can a reader of THIS window alone tell how many problems there are?"""
    return bool(re.search(r"\[\d+/(\d+)\]", window)
                or re.search(r"(\d+)\s+(shape problem|hand-off gate|error)", window))


# ── deck_gates.py ────────────────────────────────────────────────────────────────────────────────
from test_critic_waiver_gate import (  # noqa: E402
    fit_content, ARC_OK, DESIGN_OK, PROV_OK, build_deck, write_proof)

import copy  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    dd = Path(td)
    deck = build_deck(dd)
    write_proof(dd)
    rec = {"critic": {"verdict": "consent", "rounds": 2},
           "design_plan": copy.deepcopy(DESIGN_OK),
           "content": copy.deepcopy(ARC_OK),
           "provenance": copy.deepcopy(PROV_OK)}
    # several independent faults, so the report is long enough for a tail to bite
    for d in rec["content"]["audience_brief"]["decisions"][:3]:
        d["decision"] = "adopt it"
        d["needs"] = "some info"
    rec["design_plan"]["type_scale"] = {"display": 10, "title": 30, "body": 18}
    g = fit_content(rec, deck)
    g.setdefault("interview", {"language": "English", "density": "balanced",
                               "length": "medium 9-15", "goal": "inform"})
    (dd / ".deck-gates.json").write_text(json.dumps(g), encoding="utf-8")

    for name, argv in (("deck_gates.py check",
                        [sys.executable, str(SCRIPTS / "deck_gates.py"), "check", str(dd)]),
                       ("render_deck.py --gate-check",
                        [sys.executable, str(SCRIPTS / "render_deck.py"), str(deck),
                         "--gate-check", "--static"])):
        # reproduce `2>&1 | tail` FAITHFULLY: one pipe, both streams, in the order the OS
        # interleaves them. Concatenating captured stdout+stderr would hide the buffering bug this
        # test exists for — the whole defect was that the merge order is NOT the write order.
        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        merged = p.stdout
        check(p.returncode != 0, "{}: the fixture no longer fails, so this proves nothing"
                                 .format(name))
        lines = [ln for ln in merged.splitlines() if ln.strip()]
        check(len(lines) > 6, "{}: report is only {} line(s); a tail cannot bite and the test is "
                              "not exercising anything".format(name, len(lines)))
        for k in (1, 3, 6, 10, 20):
            window = "\n".join(lines[-k:])
            check(reveals_total(window),
                  "{}: `2>&1 | tail -{}` does not reveal how many problems there are — an agent "
                  "reading that window fixes what it can see and pays a round-trip for the rest."
                  "\n---\n{}\n---".format(name, k, window[:400]))
        # …and the FAILURES themselves must be in the tail, not buried under informational chatter
        for k in (6, 20):
            window = "\n".join(lines[-k:])
            check(re.search(r"\[\d+/\d+\]|shape problem|hand-off gate", window),
                  "{}: `2>&1 | tail -{}` shows no failure at all — a blocked gate that reads as "
                  "clean is worse than a truncated one.\n---\n{}\n---"
                  .format(name, k, window[:400]))

# ── codex_delivery_gate.py: numbering is asserted at source ─────────────────────────────────────
# Its fixture needs a full `.codex-deck-evidence.json`; the property is the same and the reporter
# is three lines, so it is pinned where it lives.
cx = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")
check("[{i}/{n}]" in cx or "[{i}/{n}]" in cx.replace("f\"", "\""),
      "codex_delivery_gate no longer numbers its errors `[i/n]`; a bare list read through `tail` "
      "shows some errors with no hint that more exist")
check("ALL listed below" in cx and "fix them in ONE pass" in cx,
      "codex_delivery_gate no longer states its total at both ends of the list")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_gate_report_survives_tail] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
