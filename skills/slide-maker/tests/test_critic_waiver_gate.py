#!/usr/bin/env python3
"""The critic waiver on the shared path must be CLASSIFIED, not just written.

Script-style (`main()` + explicit exit) to match test_lint_regressions.py and the codex
suites; pytest collects nothing from this file by design, and ci.yml invokes it directly.

History this guards: the Codex delivery gate required a distinct schema-valid review artifact
per lens, while the shared path accepted `{"critic": {"waived": "<any string>"}}` and printed
one line. A hand-typed waiver carried a real 10-slide deck through "all hand-off gates pass"
with no independent critic ever involved.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
RENDER = SKILL / "scripts" / "render_deck.py"

GOOD_REASON = ("No subagent dispatch on this host, so the content and design lenses were "
               "run inline in the author's own context.")

DESIGN_OK = {
    "boldness": "balanced+",
    "signature_move": "s" * 30,
    "carried_by": ["slide 3", "slide 4"],
    "form_ledger": "f" * 30,
    "icon_family": "tabler",
    "palette": "FILL E2543A / TEXT BD4630 on cream, A3341F on tint",
    "type_scale": {"display": 34, "title": 24, "body": 14},
    "signature_proof": {"slide": 3, "png": "proof.png"},
}
PROV_OK = {"claims": [{"claim": "c", "verdict": "CONFIRMED", "url": "https://example.org"}]}


def build_deck(dest: Path) -> Path:
    sys.path.insert(0, str(SKILL / "scripts"))
    import deckkit as dk
    prs = dk.blank_deck(10, 5.625)
    for i in range(3):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        dk.text(s, 1, 1, 8, 1, [[(f"Slide {i+1}", 28, dk.DEEP, True, False)]])
    out = dest / "t.pptx"
    prs.save(str(out))
    return out


def write_proof(dest: Path) -> None:
    """A real PNG next to the deck — signature_proof points at rendered evidence, not a promise."""
    sys.path.insert(0, str(SKILL / "scripts"))
    from PIL import Image
    Image.new("RGB", (960, 540), (240, 240, 245)).save(dest / "proof.png")


def run_gate(deck: Path, gates: dict) -> tuple[int, str]:
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates))
    p = subprocess.run(
        [sys.executable, str(RENDER), str(deck), "--gate-check", "--static"],
        capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


CASES = [
    ("a placeholder waiver is refused",
     {"critic": {"waived": "auto mode"}},
     False, "written reason"),

    ("a substantive but UNCLASSIFIED waiver is refused",
     {"critic": {"waived": GOOD_REASON}},
     False, "waived_category"),

    ("an unknown category is refused",
     {"critic": {"waived": GOOD_REASON, "waived_category": "because-i-said-so"}},
     False, "waived_category"),

    ("no-dispatch-on-host without inline_ran is refused",
     {"critic": {"waived": GOOD_REASON, "waived_category": "no-dispatch-on-host"}},
     False, "inline_ran"),

    ("a fully classified waiver passes, labelled NOT INDEPENDENT",
     {"critic": {"waived": GOOD_REASON, "waived_category": "no-dispatch-on-host",
                 "inline_ran": True}},
     True, "NOT INDEPENDENTLY REVIEWED"),

    ("a legitimate minor-edit waiver passes",
     {"critic": {"waived": "One-slide typo fix to a deck that already passed its full loop.",
                 "waived_category": "already-reviewed-minor-edit"}},
     True, "critic WAIVED"),

    ("the consent path is unchanged",
     {"critic": {"verdict": "consent", "rounds": 2}},
     True, "critic consented"),

    # The two-token contrast rule was declared in a design plan and then broken four times on
    # the same deck, each in a pair nobody was computing contrast for. `palette` is a required
    # field so the split has to be resolved (palette_audit.py) rather than remembered.
    ("a design plan with no resolved palette is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items() if k != "palette"}},
     False, "palette"),

    ("a design plan carrying the palette split passes",
     {"critic": {"verdict": "consent", "rounds": 2}, "design_plan": DESIGN_OK},
     True, "design plan: boldness"),

    # type_scale and signature_proof were gated on the CODEX path only. Typography was then the one
    # pillar of the visual language the shared path never made anyone resolve, and the signature move
    # was accepted as a sentence with nothing showing it survived the build. Same asymmetry as the
    # critic-waiver bug above, which is why both directions are pinned here.
    ("a design plan with no type_scale is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items() if k != "type_scale"}},
     False, "type_scale"),

    ("a type_scale whose tiers do not rank is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": dict(DESIGN_OK, type_scale={"display": 18, "title": 24, "body": 14})},
     False, "not a scale"),

    ("a body size under the legibility floor is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": dict(DESIGN_OK, type_scale={"display": 34, "title": 24, "body": 9})},
     False, "legibility floor"),

    ("a design plan with no signature_proof is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items() if k != "signature_proof"}},
     False, "signature_proof"),

    # An OpenAI/Codex-bridged run keeps both .codex-deck-evidence.json and .deck-gates.json, and its
    # own gate spells this key "path". Rejecting that spelling here would fail the same evidence for
    # its key name alone.
    ("the Codex spelling signature_proof.path is accepted",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": dict(DESIGN_OK, signature_proof={"slide": 3, "path": "proof.png"})},
     True, "design plan: boldness"),

    ("a signature_proof pointing at a MISSING png is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": dict(DESIGN_OK, signature_proof={"slide": 3, "png": "nope.png"})},
     False, "does not exist"),
]


def main() -> int:
    passed = failed = 0
    with tempfile.TemporaryDirectory() as td:
        deck = build_deck(Path(td))
        write_proof(Path(td))
        for name, critic_block, should_pass, needle in CASES:
            gates = dict(critic_block)
            gates.setdefault("design_plan", DESIGN_OK)
            gates.setdefault("provenance", PROV_OK)
            code, out = run_gate(deck, gates)
            ok = (code == 0) == should_pass and needle in out
            if ok:
                passed += 1
                print(f"  ok   {name}")
            else:
                failed += 1
                print(f"  FAIL {name}: exit={code} (wanted pass={should_pass}), "
                      f"missing {needle!r}")
                print("       " + out.strip().replace("\n", "\n       ")[:400])
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
