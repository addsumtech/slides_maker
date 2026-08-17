#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A written reason is judged by how much it SAYS, not by which language it says it in.

WHY. Every "record a written reason" floor in this skill was `len(text) < N` — a count of
codepoints — which made the bar depend on the writing system:

    "看过了，不用再审"                       8 codepoints → refused by a floor of 12
    "这个盒子是模板固定槽位，只能改常数"       17 codepoints → refused by a floor of 20
    "the box is a fixed template slot"     32 codepoints → accepted

The Chinese strings say more and were refused for using fewer characters. On a Chinese deck —
which is most of the decks this skill actually builds — that is a gate nobody can satisfy
honestly, and the only way past a gate you cannot satisfy is padding it with words nobody means.
That destroys the one property these reasons exist to have.

`written_reason.reason_width` counts an East-Asian wide/fullwidth character as 2. Both directions
are asserted, because a fix that quietly lowered the bar for everyone would be worse than the bug:
CJK reasons of real substance now pass, short ones (in ANY language) still do not, and every ASCII
floor keeps its behaviour exactly.

Run:  python3 tests/test_written_reason.py
"""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
RENDER = SKILL / "scripts" / "render_deck.py"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(HERE))

import codex_delivery_gate as cg  # noqa: E402
import deck_cycle  # noqa: E402
from written_reason import reason_width  # noqa: E402
from test_critic_waiver_gate import fit_content, ARC_OK, DESIGN_OK, build_deck, write_proof  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


# Real sentences, not padding: each states a position someone could disagree with.
ZH_CRITIC = "用户在渲染稿出来后选择不再评审，说这版已经可以直接用了，所以整个评审环节按其要求跳过。"
ZH_SHORT = "跳过了"
EN_SHORT = "skipped it"


def gate(deck, gates):
    gates = fit_content(gates, deck)
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates, ensure_ascii=False),
                                                  encoding="utf-8")
    p = subprocess.run([sys.executable, str(RENDER), str(deck), "--gate-check", "--static"],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    print("== reason_width: wide characters count double, ASCII is untouched ==")
    check("ASCII is plain length", reason_width("the box is a fixed slot") == 23)
    check("whitespace does not count", reason_width("  abc  ") == 3)
    check("a CJK character counts 2", reason_width("看过了") == 6)
    check("fullwidth punctuation counts 2", reason_width("，") == 2)
    check("mixed text adds up", reason_width("a中b") == 4)
    check("a non-string is 0, never an error", reason_width(None) == 0 and reason_width(7) == 0)
    check("ambiguous-width stays 1 (accents must not clear a floor for free)",
          reason_width("café") == 4)

    print("== the shared gate: a Chinese waiver is a waiver ==")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        deck = build_deck(d)
        write_proof(d)
        base = {"design_plan": copy.deepcopy(DESIGN_OK), "content": copy.deepcopy(ARC_OK)}

        rc, out = gate(deck, {**base, "critic": {"waived": ZH_CRITIC,
                                                 "waived_category": "user-waived"}})
        check("a substantive Chinese critic waiver passes", rc == 0, out)

        rc, out = gate(deck, {**base, "critic": {"waived": ZH_SHORT,
                                                 "waived_category": "user-waived"}})
        check("a 3-character Chinese non-reason still blocks", rc != 0 and "placeholder" in out, out)

        rc, out = gate(deck, {**base, "critic": {"waived": EN_SHORT,
                                                 "waived_category": "user-waived"}})
        check("a short ENGLISH non-reason still blocks — the floor did not move", rc != 0, out)

        # The sameness waiver's floor is 40, the highest in the file: a Chinese register name
        # clears it at 20 characters, which is a whole sentence.
        zh_sameness = "这是一套小红书图卡系列，重复的版式本身就是作品的形式，不是单调。"
        check("the 40-wide sameness floor is reachable in Chinese",
              reason_width(zh_sameness) >= 40, reason_width(zh_sameness))

    print("== the codex gate: same measure, same definition (imported, not copied) ==")
    check("codex gate uses the shared function", cg.reason_width is reason_width)
    check("deck_cycle uses the shared function", deck_cycle.reason_width is reason_width)
    errs = []
    cg.require_string("看过了，不用再审，直接交付", "none_opt_in", errs, minimum=12)
    check("a Chinese post-build decline satisfies none_opt_in", not errs, errs)
    errs = []
    cg.require_string("跳过", "none_opt_in", errs, minimum=12)
    check("...but two characters do not", bool(errs))
    errs = []
    cg.require_string("skipped", "none_opt_in", errs, minimum=12)
    check("...and neither does a short English one", bool(errs))

    print("== deck_cycle --nudge-again accepts a real Chinese reason ==")
    zh_nudge = "这个盒子是模板固定槽位，只能改常数"
    check("a 17-character Chinese reason clears the override floor",
          reason_width(zh_nudge) >= deck_cycle.OVERRIDE_MIN, reason_width(zh_nudge))
    check("...while a 3-character one does not",
          reason_width("再试试") < deck_cycle.OVERRIDE_MIN)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
