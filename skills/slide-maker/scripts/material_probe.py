#!/usr/bin/env python3
"""The Step-2 MATERIAL PROBE contract, in one place, imported by every gate path.

Step 2 opens by BUILDING one real slide — the page the signature move lands on, in the register you
just invented — rendering it, and LOOKING at it, before the design plan's twenty declarations are
written. The record is the rendered PNG plus one sentence: *what would the SAFE version of this page
have been?*

🔴 **WHY THIS IS A SHARED MODULE AND NOT A CONSTANT IN EACH GATE.** `anchor_proof.py` exists because
`render_deck.py --gate-check` and `codex_delivery_gate.py` diverged on the anchor proof's file key —
one spelled it `path`, the other `png` — so a bridged run wrote what its own gate demanded and the
other rejected it. The material probe was heading the same way: the carve list had just been written
into two gates by hand, and adding the Codex arm would have made three copies of a four-word tuple.

What lives here is the CONTRACT — which carves exist, and what a waiver must carry. What stays local
to each gate is the STRICTNESS of the artifact check: the shared path opens the PNG and rejects a
flat one, while the Codex path binds it to a SHA-256 and to the final PPTX hash. Folding those
together would have to weaken one to the weaker of the two.

🔴 `conservative` IS NOT A CARVE, deliberately. Step 2 says so in as many words: restraint is a
material decision too, and a page is exactly where you see whether it reads as deliberate or as
nothing. (The ANCHOR PROOF at Step 4 *does* carve for it — that one proves a risk survived the
build, and a deck that took no risk has nothing to prove. Two different questions, two different
carves; conflating them is why this note is here.)
"""
from __future__ import annotations

# The look is not yours to invent, so there is no register of your own to probe.
CARVES = ("registered-template", "provided-template", "mode-a-mimic", "tiny-ask")

MIN_REASON = 20

# 🔴 THE KEY IS READ, NEVER DICTATED. The shared gate's skeleton says `png`; every Codex evidence
# record spells a file `path` (`signature_proof`, `icons`, the critic reviews). That is the SAME
# split — `path` here, `png` there — that made a bridged run write what its own gate demanded and
# the other reject it, and it is the reason `anchor_proof.py` exists. So both keys are the contract
# and every gate accepts either; nobody has to guess which runtime's spelling to use.
FILE_KEYS = ("png", "path")


def file_value(probe) -> str:
    """The probe's rendered-slide path under EITHER spelling, or "" if it names none."""
    for k in FILE_KEYS:
        v = str((probe or {}).get(k) or "").strip()
        if v:
            return v
    return ""


def is_waived(probe) -> bool:
    """Is this record claiming the carve rather than supplying the artifact?"""
    return isinstance(probe, dict) and bool(str(probe.get("waived") or "").strip())


def waiver_faults(probe) -> list[str]:
    """Complaints about a WAIVED probe's shape. Empty means the carve is properly claimed."""
    out: list[str] = []
    cat = str((probe or {}).get("waived_category") or "").strip().lower()
    if cat not in CARVES:
        out.append("needs a `waived_category` naming the carve: {}. `conservative` is NOT one of "
                   "them — Step 2 says restraint is a material decision too, and a page is where "
                   "you see whether it reads as deliberate or as nothing."
                   .format(" | ".join(CARVES)))
    reason = str((probe or {}).get("waived") or "").strip()
    if len(reason) < MIN_REASON:
        out.append("needs a written reason beside the category — which template, which mimic, how "
                   "many slides. A bare category is a label, not a decision.")
    return out


MISSING = ('is missing. Step 2 opens by BUILDING one real slide — the signature page in the '
           'register you invented — rendering it, and looking at it, before any of the plan is '
           'written.\n'
           '    {"material_probe": {"png": "render/slideNN.png",   # or "path" — either is read\n'
           '                        "safe_version": "<what the DEFAULT version of this page would '
           'have been — if it is about the same thing, the register is a look, not a move>"}}\n'
           '  Or claim a carve: {"waived": "<which template / mimic / how many slides>", '
           '"waived_category": "' + " | ".join(CARVES) + '"}')
