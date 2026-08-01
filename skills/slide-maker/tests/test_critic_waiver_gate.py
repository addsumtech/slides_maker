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


def run_gate(deck: Path, gates: dict, *flags: str) -> tuple[int, str]:
    (deck.parent / ".deck-gates.json").write_text(json.dumps(gates))
    p = subprocess.run(
        [sys.executable, str(RENDER), str(deck), "--gate-check", "--static", *flags],
        capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


# The delivery a gate enforces comes from two places — a recorded `delivery` key and the CLI mode
# flags — and they used to be read INDEPENDENTLY: the type-scale floor read the key, the density
# gate read the flag. One run could therefore enforce two different deliveries, and --selfread was
# INERT for the floor (a self-read deck with 12pt body died citing the *presented* floor).
# The rule now: a recorded key wins, the flag is the fallback, an unrecognised recorded value DIES
# rather than falling back to a floor it was never meant to be held to, and both gates read the one
# resolved value. Body is 12.0 throughout, which is legal for selfread/surface and illegal for
# presented/textheavy — so each cell's outcome is decided purely by the resolved delivery.
DELIVERY_CASES = [
    # (name,                          recorded,      flags,           expect_floor_death)
    ("no key + no flag = presented",  None,          (),              True),
    ("no key + --selfread applies",   None,          ("--selfread",), False),
    ("no key + --surface applies",    None,          ("--surface",),  False),
    ("recorded presented wins",       "presented",   (),              True),
    ("recorded presented beats flag", "presented",   ("--selfread",), True),
    ("recorded selfread applies",     "selfread",    (),              False),
    ("recorded selfread beats flag",  "selfread",    ("--textheavy",), False),
    ("unknown recorded value dies",   "briefing",    (),              None),
]


def check_delivery(deck: Path) -> tuple[int, int]:
    ok = bad = 0
    for name, recorded, flags, want_death in DELIVERY_CASES:
        g = {"critic": {"verdict": "consent", "rounds": 2},
             "design_plan": dict(DESIGN_OK, type_scale={"display": 34, "title": 24, "body": 12}),
             "provenance": PROV_OK}
        if recorded:
            g["delivery"] = recorded
        _, out = run_gate(deck, g, *flags)
        if want_death is None:                       # unknown value must be REFUSED, not defaulted
            good = "not a delivery mode" in out
            why = "died on the unknown delivery" if good else "silently accepted an unknown delivery"
        else:
            died = "legibility floor, not a style choice" in out
            good = died == want_death
            why = ("enforced the floor" if died else "let 12pt through")
        if good:
            ok += 1
            print("  ok   delivery: {} -> {}".format(name, why))
        else:
            bad += 1
            print("  FAIL delivery: {} -> {}\n       {}".format(
                name, why, out.strip().splitlines()[-1][:150] if out.strip() else "(no output)"))
    return ok, bad


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

    # THE RESTRAINT CARVE, on the escape agents/slide-design.md already documents: under a
    # *conservative* dial the risk is OPTIONAL — take a modest move, or write the one-clause
    # "deliberately restrained: <why>" so the field is never blank. That existed only in prose, so an
    # honest 5-minute lab-meeting plan was rejected for lacking a rendered proof of a risk it never
    # took, and the only escape ({"waived": …}) also switches off palette/type_scale/icon_family.
    # The carve must stay narrow, so every direction is pinned.
    ("conservative + a 'deliberately restrained:' move drops only signature_proof",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items() if k != "signature_proof"}
      | {"boldness": "conservative",
         "signature_move": "deliberately restrained: 5-minute working update; one accent is "
                           "reserved for the new result and nothing competes with it"}},
     True, "signature_proof not required"),

    # at balanced+ and above a real signature move is required, not optional — the phrase alone
    # must not buy the exemption
    ("the 'deliberately restrained:' phrase does NOT work above the conservative dial",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items() if k != "signature_proof"}
      | {"signature_move": "deliberately restrained: trying to dodge the proof"}},
     False, "signature_proof"),

    ("a conservative deck that took a REAL move still owes the proof",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items() if k != "signature_proof"}
      | {"boldness": "conservative"}},
     False, "signature_proof"),

    ("the carved plan still needs a NON-BLANK signature_move",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items()
                      if k not in ("signature_proof", "signature_move")}
      | {"boldness": "conservative"}},
     False, "signature_move"),

    ("the carve is not a blanket exemption — type_scale is still required",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": {k: v for k, v in DESIGN_OK.items()
                      if k not in ("signature_proof", "type_scale")}
      | {"boldness": "conservative",
         "signature_move": "deliberately restrained: sober status readout"}},
     False, "type_scale"),

    ("a signature_proof pointing at a MISSING png is refused",
     {"critic": {"verdict": "consent", "rounds": 2},
      "design_plan": dict(DESIGN_OK, signature_proof={"slide": 3, "png": "nope.png"})},
     False, "does not exist"),
]


def build_icon_deck(dest: Path, *, logo_every=False, icon_slides=(), label_row=False, n=8) -> None:
    """A deck shaped to probe one branch of the icon waiver at a time."""
    sys.path.insert(0, str(SKILL / "scripts"))
    import deckkit as dk
    from PIL import Image
    lg = dest.parent / "iconfx_logo.png"
    Image.new("RGB", (64, 64), (30, 60, 120)).save(lg)
    prs = dk.blank_deck(10, 5.625)
    for i in range(n):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        dk.text(s, 0.6, 0.4, 8.8, 0.6, [[(f"Title of slide {i+1}", 28, dk.DEEP, True, False)]])
        for k in range(6):                                   # ordinary body copy: NOT a category set
            dk.text(s, 0.6, 1.3 + k * 0.34, 8.8, 0.32,
                    [[("body copy line carrying several real words", 14, dk.DEEP, False, False)]],
                    space_after=0)
        if logo_every:
            dk.logo(s, str(lg), corner="tr", h=0.6)
        if label_row and i in (1, 3, 5):                     # 4 short labels ACROSS the page
            for j, lab in enumerate(("Portrait", "Genre", "Still life", "Landscape")):
                dk.text(s, 0.6 + j * 2.2, 4.6, 2.0, 0.34, [[(lab, 15, dk.DEEP, True, False)]],
                        space_after=0)
        if i + 1 in icon_slides:
            for j in range(3):
                p = dest.parent / f"iconfx_{i}{j}.png"
                Image.new("RGB", (64, 64), (200, 40, 40)).save(p)
                dk.picture(s, str(p), 0.7 + j * 2.6, 3.9, 0.5, 0.5)
    prs.save(str(dest))


ICON_CASES = [
    # (name, deck shape, icon_family, must the waiver fire?)
    ("icon waiver: a LOGO repeated on every slide is not an icon family",
     {"tag": "ic_logo", "logo_every": True}, "none - brand allows only the logo", False),
    ("icon waiver: plain body copy is not a category set",
     {"tag": "ic_plain"}, "none - narrative deck, no entities", False),
    ("icon waiver: a real icon set contradicts a `none` record",
     {"tag": "ic_real", "icon_slides": (2, 4, 6)}, "none - conceptual content", True),
    ("icon waiver: a logo does not mask a real icon set",
     {"tag": "ic_both", "logo_every": True, "icon_slides": (2, 4, 6)}, "none - x", True),
    ("icon waiver: label ROWS across the page do contradict `none`",
     {"tag": "ic_rows", "label_row": True}, "none - concepts, icons would decorate", True),
    ("icon waiver: a declared family is never second-guessed",
     {"tag": "ic_decl", "icon_slides": (2, 4, 6)}, "tabler outline 1.75px", False),
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
        # ── the `icon waiver` gate. `icon_family: "none - <reason>"` is free text written at PLAN
        # time, before any slide exists, and nothing revisited it: one real build shipped ZERO icons
        # past every gate on a deck of category slides. It must stay satisfiable for a genuinely
        # icon-free deck, so both FALSE-POSITIVE cases below matter at least as much as the true
        # ones — every one of them was a live bug in the first cut of this check.
        for name, kw, fam, want in ICON_CASES:
            d2 = Path(td) / (kw["tag"] + ".pptx")
            build_icon_deck(d2, **{k: v for k, v in kw.items() if k != "tag"})
            g = {"critic": {"verdict": "consent", "rounds": 2},
                 "design_plan": dict(DESIGN_OK, icon_family=fam, carried_by=[2, 3]),
                 "provenance": PROV_OK}
            code, out = run_gate(d2, g)
            if "hand-off gates pass" not in out and "icon waiver" not in out:
                failed += 1
                print(f"  FAIL {name}: the gate aborted before the icon check ran, so this "
                      f"assertion means nothing\n       " + out.strip().splitlines()[-1][:160])
                continue
            fired = "icon waiver" in out
            if fired == want:
                passed += 1
                print(f"  ok   {name}")
            else:
                failed += 1
                print(f"  FAIL {name}: icon waiver {'fired' if fired else 'stayed silent'}, "
                      f"wanted the opposite")
        o, b = check_delivery(deck)
        passed += o
        failed += b
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
