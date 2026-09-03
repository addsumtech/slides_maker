#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 2 must MAKE something before it declares anything — and a blank PNG is not evidence.

WHY. The pipeline gates a motif's CONCEPT thoroughly — a derivation ladder with two middle rungs,
two rejected pictures each with the clause that lost it, the STRANGER TEST, ONE-form-ONE-meaning,
the generativity triple — and its MATERIAL not at all.

Measured on a delivered deck: the concept was genuinely right (a config row, derived from the
product's own `cordis.yml`, correctly rejecting the plug-socket stereotype every plugin deck
reaches for) and passed every one of those checks. What shipped was six grey rectangles. The
repair changed ONLY the material — the same rows became a real config with keys, values and a
`-`/`+` diff — and nothing about the concept moved. No step between "concept approved" and "deck
delivered" had ever asked what the device is MADE of.

The cause was an order-of-work failure, not a missing rule: the design turn carried ~20 required
declarations and zero required artifacts, so effort went into sentences that pass rather than a
thing that works. `signature move: 封面自己演示论点` is a good sentence that was true of nothing on
the page. Pixels cannot be faked that way, which is why the probe is a rendered slide.

Two holes are closed here, and the second is the sharper one:

  MATERIAL PROBE  the design plan must carry a rendered PNG of the signature page plus the one-line
                  "what would the SAFE version have been" comparison — the single field on that
                  plan that cannot be written without having made something.
  FLAT PNG        an anchor/probe image that is one uniform colour is refused. Measured: a 960x540
                  rectangle of one grey satisfied `signature_proof` — the ANCHOR PROOF, whose whole
                  purpose is to put rendered evidence where the design decision is made.

Run:  python3 tests/test_material_probe.py
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

import render_deck as RD  # noqa: E402
from test_critic_waiver_gate import (  # noqa: E402
    fit_content,  # noqa: E402
    ARC_OK, DESIGN_OK, GOOD_REASON, PROV_OK, build_deck, write_proof,
)

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}\n       {str(detail)[:320]}")


def anti_drift():
    """The same shape as tests/test_anchor_proof.py, one field earlier.

    The carve list had been hand-written into TWO gates, and adding the Codex arm would have made a
    third copy — while the shared/Codex pair has already diverged on exactly this kind of field: the
    anchor proof's file key was spelled `path` in one gate and `png` in the other, so a bridged run
    wrote what its own gate demanded and the other rejected it for the key name alone.
    """
    import ast
    import material_probe as mp

    print("== one contract module, imported by every gate path ==")
    for name in ("render_deck.py", "deck_gates.py", "codex_delivery_gate.py"):
        src = (SKILL / "scripts" / name).read_text(encoding="utf-8")
        imported = any(
            (isinstance(n, ast.Import) and any(a.name == "material_probe" for a in n.names))
            or (isinstance(n, ast.ImportFrom) and n.module == "material_probe")
            for n in ast.walk(ast.parse(src)))
        check("%s imports the shared material_probe contract rather than restating it" % name,
              imported,
              "a local copy looks correct in review and simply stops being the same rule six "
              "months later — which is what happened to the anchor proof's file key")
        check("...and %s carries no private copy of the carve tuple" % name,
              '"registered-template", "provided-template"' not in src)

    check("🔴 BOTH spellings are the contract, so neither runtime is blocked for its own word",
          mp.file_value({"png": "a.png"}) == "a.png" and mp.file_value({"path": "b"}) == "b",
          "the shared gate's skeleton says `png`; every Codex evidence record spells a file `path`")
    check("...and reading two keys does not mean accepting neither",
          mp.file_value({}) == "" and mp.file_value(None) == "")
    check("...and a blank `waived` is not a waiver, so whitespace cannot buy the carve",
          not mp.is_waived({"waived": "   "}))
    check("🔴 `conservative` is refused BY NAME, with the reason attached",
          any("conservative" in f for f in
              mp.waiver_faults({"waived": "x" * 40, "waived_category": "conservative"})),
          "it carves the Step-4 ANCHOR proof — a deck that took no risk has nothing to prove — and "
          "deliberately not this one; whoever meets the error is exactly who needs to know why")
    check("...and maintenance-boundaries.md tells the next person what re-inlining it would cost",
          "material_probe.py" in
          (SKILL / "references" / "maintenance-boundaries.md").read_text(encoding="utf-8"),
          "check_skill_lossless.py would score that refactor perfect while the property disappears")


def gate(deck, gates):
    gates = fit_content(gates, deck)
    if "interview" not in gates:                 # the four recorded answers are now required;
        gates = dict(gates, interview={          # no fixture below is ABOUT the interview, so
            "language": "English", "density": "balanced",     # filling it here keeps each test
            "length": "medium 9-15", "goal": "inform"})       # about the thing it checks
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates, ensure_ascii=False),
                                                  encoding="utf-8")
    p = subprocess.run([sys.executable, str(RENDER), str(deck), "--gate-check", "--static"],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def record(**design):
    d = copy.deepcopy(DESIGN_OK)
    d.update(design)
    return {"critic": {"waived": GOOD_REASON, "waived_category": "no-dispatch-on-host",
                       "inline_ran": True},
            "design_plan": d, "content": copy.deepcopy(ARC_OK),
            "provenance": copy.deepcopy(PROV_OK)}


def main():
    print("== _png_is_flat: a uniform rectangle is not a render ==")
    with tempfile.TemporaryDirectory() as td:
        from PIL import Image
        d = pathlib.Path(td)
        flat = d / "flat.png"
        Image.new("RGB", (960, 540), (240, 240, 245)).save(flat)
        real = d / "real.png"
        im = Image.new("RGB", (960, 540), (240, 240, 245))
        for x in range(100, 800):
            for y in range(150, 320):
                im.putpixel((x, y), (15, 110, 99))
        im.save(real)
        check("a single-colour PNG is flat", RD._png_is_flat(flat))
        check("a PNG with a drawn region is not", not RD._png_is_flat(real))
        check("an unreadable path is not called flat (unreadable is not a lie)",
              not RD._png_is_flat(d / "nope.png"))

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        deck = build_deck(d)
        write_proof(d)

        print("== the probe is required, and it is an ARTIFACT not a sentence ==")
        rec = record()
        rec["design_plan"].pop("material_probe")
        rc, out = gate(deck, rec)
        check("a plan with no material probe is refused", rc != 0, out)
        check("...and the message says Step 2 opens by BUILDING one real slide",
              "BUILDING one real slide" in out, out)

        rec = record(material_probe={"png": "missing.png", "safe_version": "安全版本会是一张通用图表页"})
        rc, out = gate(deck, rec)
        check("a probe pointing at nothing is refused", rc != 0 and "REAL rendered slide" in out, out)

        from PIL import Image
        Image.new("RGB", (960, 540), (200, 200, 200)).save(d / "blank.png")
        rec = record(material_probe={"png": "blank.png", "safe_version": "安全版本会是一张通用图表页"})
        rc, out = gate(deck, rec)
        check("a flat PNG is refused as a probe", rc != 0 and "flat colour" in out, out)

        print("== the comparison question cannot be waved through ==")
        rec = record(material_probe={"png": "probe.png", "safe_version": "差不多"})
        rc, out = gate(deck, rec)
        check("a three-character answer is not a comparison",
              rc != 0 and "SAFE version" in out, out)

        rec = record()      # DESIGN_OK carries a real probe + a real sentence
        rc, out = gate(deck, rec)
        check("a real render + a real comparison passes", rc == 0, out)
        check("...and the gate prints both, so a weak answer is one glance from a veto",
              "material probe:" in out and "safe version would have been" in out, out)

        print("== the same flat-PNG rule protects the ANCHOR PROOF ==")
        rec = record()
        Image.new("RGB", (960, 540), (250, 250, 250)).save(d / "proof.png")   # blank it out
        rc, out = gate(deck, rec)
        check("a blank anchor is refused", rc != 0 and "single flat colour" in out, out)
        check("...and says what the anchor proof is FOR",
              "rendered evidence where the design decision is made" in out, out)

    anti_drift()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
