#!/usr/bin/env python3
"""The two runtimes must gate the same things, or one of them quietly stops enforcing a floor.

🔴 WHY. This skill delivers through two gate paths over two record schemas — `render_deck.py
--gate-check` reading `.deck-gates.json`, and `codex_delivery_gate.py` reading
`.codex-deck-evidence.json`. They have drifted apart THREE times, each time silently, each time
found by accident:

  1. `png` vs `path` — the same probe file spelled two ways. `material_probe.file_value` exists
     because of it.
  2. `design_plan` vs `design` — a taste gate reached for a key the Codex schema has never had, so
     it was permanently unsatisfiable on that runtime and nobody could have filled it.
  3. `checkpoints` — 16 of 17 shared gate sections were mirrored on the Codex path and this was the
     exception: the one record that says whether a HUMAN approved anything, missing on the runtime
     most likely to compress the whole pipeline into a single pass.

Every one of those was invisible because a gate that never runs and a gate that passes look exactly
the same from outside. Adding the missing three fixed the day; this fixes the fourth.

WHAT IT CHECKS. Every `_gate_section('name')` in the shared path must be reachable in the Codex
gate, and every shared CONTRACT module the shared path imports must be imported there too. It does
NOT check that they enforce identically — a delivery gate and a pre-flight legitimately differ in
strictness — only that neither runtime is missing the concern entirely, which is the failure that
has actually happened.

A concern may be deliberately one-sided. That is a decision someone writes in ALLOWLIST with a
reason, not a gap nobody noticed.

    python3 scripts/check_gate_parity.py           # from the skill directory
    python3 scripts/check_gate_parity.py --list

Exit 0 clean · 1 drift · 2 could not run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SHARED = SKILL / "scripts" / "render_deck.py"
CODEX = SKILL / "scripts" / "codex_delivery_gate.py"

# Contracts both paths must read from ONE module rather than re-implementing. Each of these exists
# because the two paths had already disagreed about the thing it owns.
CONTRACTS = ("anchor_proof", "material_probe", "audience_brief", "blind_read", "taste_ledger",
             "composition_probe", "delegated_picks")

# 🔴 Gate sections whose CHECK IS FED by something extracted from the record — as opposed to the
# ~19 shared / 11 Codex reads that only look up a WAIVER, which is absent from a scaffold by design.
# This file compares the two gate FILES and cannot tell whether an extractor can actually read
# either runtime's schema: `check_purpose` was wired into both paths, reported here as 21 sections
# and 0 problems, and read `design.purpose` — a key the Codex schema does not have, at any level.
# The gate existed there and could almost never bind, with parity green throughout.
#
# So each name here must be exercised by `tests/test_schema_reach.py`, which fills BOTH runtimes'
# real scaffolds the way each runtime actually fills them and asserts the extraction succeeds. A
# static scan cannot replace it: the extractor that failed loops over a tuple of candidate key
# names, which no regex reads.
RECORD_FED = ("purpose", "surface", "content.audience_brief", "checkpoints", "design_plan",
               "talk_time", "qa_backup", "citations", "image_series",
               "visual_language")

REACH_SUITE = "tests/test_schema_reach.py"

# One-sided on purpose, with the reason. An empty reason is what this script prevents.
ALLOWLIST = {
    "surface": "the Codex evidence file records the surface as a field rather than gating it; "
               "`check_surface.py` runs on both and owns the check itself",
}


def sections() -> list[str]:
    return sorted(set(re.findall(r"_gate_section\('([^']+)'\)", SHARED.read_text(encoding="utf-8"))))


def reaches(codex_src: str, name: str) -> bool:
    """Is this concern present in the Codex gate at all? Dotted names match on their last part —
    `content.arc` is `arc` there — because the two schemas nest differently by design."""
    return name in codex_src or name.split(".")[-1] in codex_src


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)

    for f in (SHARED, CODEX):
        if not f.exists():
            print("[parity] missing {} — cannot compare the two gate paths.".format(f),
                  file=sys.stderr)
            return 2
    cx = CODEX.read_text(encoding="utf-8")
    names = sections()
    if not names:
        print("[parity] found no gate sections in {} — the pattern this reads has changed, and a "
              "guard that matches nothing reports clean forever.".format(SHARED.name),
              file=sys.stderr)
        return 2

    rows = [(n, reaches(cx, n)) for n in names]
    if a.list:
        for n, ok in rows:
            print("{:<10} {}".format("both" if ok else ("skip" if n in ALLOWLIST else "SHARED-ONLY"),
                                     n))
        for c in CONTRACTS:
            print("{:<10} contract: {}".format("both" if c in cx else "SHARED-ONLY", c))
        return 0

    missing = [n for n, ok in rows if not ok and n not in ALLOWLIST]
    stale = [n for n in ALLOWLIST if n not in names]
    # a record-FED section with no behavioural reach coverage is the hole this guard could not see
    reach_src = ""
    try:
        reach_src = (SKILL / REACH_SUITE).read_text(encoding="utf-8")
    except OSError:
        pass
    uncovered = ([] if not reach_src
                 else [n for n in RECORD_FED if n not in reach_src
                       and n.split(".")[-1] not in reach_src])
    if not reach_src:
        uncovered = list(RECORD_FED)
    stale_fed = [n for n in RECORD_FED if n not in names and "." not in n]
    shared_src = SHARED.read_text(encoding="utf-8")
    contract_gap = [c for c in CONTRACTS if c in shared_src and c not in cx]

    for n in missing:
        print("[parity] `{}` is gated on the shared path and reachable nowhere in "
              "codex_delivery_gate.py. A floor kept in one runtime only is how the other stops "
              "enforcing it — add it there, or ALLOWLIST it here with a reason.".format(n))
    for c in contract_gap:
        print("[parity] the shared path imports the `{}` contract and the Codex gate does not. That "
              "module exists because these two paths already disagreed about what it owns."
              .format(c))
    for n in stale:
        print("[parity] ALLOWLIST names `{}`, which is no longer a gate section — stale permission."
              .format(n))
    for n in uncovered:
        print("[parity] `{}` is FED by something read out of the record, and {} does not exercise "
              "it. Being CALLED on both paths is not the same as being able to READ either schema "
              "— measured: check_purpose was wired into both, parity was green, and it read a key "
              "the Codex evidence file does not contain at any level.".format(n, REACH_SUITE))
    for n in stale_fed:
        print("[parity] RECORD_FED names `{}`, which is no longer a gate section — stale entry."
              .format(n))

    bad = len(missing) + len(contract_gap) + len(stale) + len(uncovered) + len(stale_fed)
    print("[parity] {} gate section(s) + {} shared contract(s) + {} record-fed section(s): "
          "{} problem(s)."
          .format(len(names), len(CONTRACTS), len(RECORD_FED), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
