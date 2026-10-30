#!/usr/bin/env python3
"""A freshness finding must name EVERY near neighbour, or clearing it becomes a search.

🔴 MEASURED, on a real 12-page build. `GROUND REPEAT` named one previous deck and `break`ed. The
author moved the canvas off it — and landed inside the tolerance of the NEXT deck in the history,
which the checker had known about the whole time. Three fail -> fix -> re-run rounds
(#F4F1EA -> #F0EADA -> #EADFBE) to learn a constraint that was fully computable on the first.

Reproduced exactly here: against a three-deck history, #F4F1EA is near ALL THREE, #F0EADA is near
two, and only the third value clears. One report naming all three, with the distances and the
threshold, turns that search into a single move.

The finding must also STILL FIRE and still block — a message that names more while catching less
would be a worse trade than the round-trips.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_register_pixels as rp  # noqa: E402

try:
    from PIL import Image
except Exception as exc:                                           # noqa: BLE001
    print("[test_ground_repeat_names_all] SKIP — no PIL: {}".format(exc))
    sys.exit(0)

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


# the three grounds the real build walked through, and the history it walked into
HIST = [("deck-a", (0xF3, 0xF5, 0xF4)), ("deck-b", (0xF5, 0xEF, 0xE1)),
        ("deck-c", (0xF7, 0xF2, 0xE8))]
INK = (0x1C, 0x1B, 0x19)


def build(td: Path, ground):
    d = td / "deck"
    (d / "render").mkdir(parents=True, exist_ok=True)
    for i in range(3):
        im = Image.new("RGB", (480, 270), ground)
        px = im.load()
        for y in range(20, 36):
            for x in range(20, 260):
                px[x, y] = INK
        im.save(d / "render" / ("slide%02d.png" % (i + 1)))
    (d / ".deck-gates.json").write_text(json.dumps({"design_plan": {
        "palette": "#%02X%02X%02X / #%02X%02X%02X" % (ground + INK)}}), encoding="utf-8")
    tp = d / "taste.md"
    rows = "\n".join("| 2026-01-0%d | %s | x | #%02X%02X%02X | y |" % ((i + 1, nm) + c)
                     for i, (nm, c) in enumerate(HIST))
    tp.write_text("## LOOK HISTORY\n| date | deck | look | canvas | motif |\n"
                  "|---|---|---|---|---|\n" + rows + "\n", encoding="utf-8")
    return d, str(tp)


def ground_msg(td, ground):
    d, tp = build(td, ground)
    probs, _facts = rp.check(d, taste=tp)
    return next((m for c, m in probs if c == "GROUND REPEAT"), None)


with tempfile.TemporaryDirectory() as _td:
    td = Path(_td)

    # ── 🔴 the value that was near THREE decks names all three ──────────────────────────────────
    msg = ground_msg(td, (0xF4, 0xF1, 0xEA))
    check(msg is not None, "GROUND REPEAT no longer fires on a canvas inside the tolerance of "
                           "three recent decks — naming more must not mean catching less")
    if msg:
        named = sum(1 for nm, _ in HIST if nm in msg)
        check(named == 3, "the finding names {} of the 3 near decks; clearing it is a search "
                          "again, one round-trip per neighbour:\n{}".format(named, msg[:400]))
        check("distance" in msg.lower(),
              "no distances given, so the author cannot tell how far to move:\n{}".format(msg[:300]))
        check("{:.0f}".format(rp.SAME_LOOK) in msg,
              "the threshold ({:.0f}) is not stated, so 'far enough' stays a guess:\n{}"
              .format(rp.SAME_LOOK, msg[:300]))

    # ── the intermediate value is still caught, and names the two it is near ────────────────────
    msg2 = ground_msg(td, (0xF0, 0xEA, 0xDA))
    check(msg2 is not None, "the second value in the real walk is no longer caught at all")
    if msg2:
        named2 = sum(1 for nm, _ in HIST if nm in msg2)
        check(named2 == 2, "expected 2 near decks for #F0EADA, message names {}:\n{}"
                           .format(named2, msg2[:300]))

    # ── …and the value that genuinely clears everything passes ──────────────────────────────────
    check(ground_msg(td, (0xEA, 0xDF, 0xBE)) is None,
          "a canvas outside every neighbour's tolerance is still reported — the finding would "
          "then be unclearable, which is worse than the search it replaced")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_ground_repeat_names_all] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
