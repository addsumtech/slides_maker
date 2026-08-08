"""`validate_review.py` is the ONLY gate on the critic, and it had three fixtures.

The review contract is where a deck's quality claim becomes machine-checkable: the critic is
the one judgement that cannot be self-certified, and this validator is the only thing standing
between "a critic consented" and "a JSON file says consent". It carries ~30 distinct rules and
its whole test suite was `--selftest`'s three inline fixtures — one valid critic, one broken
critic, one arbiter pair. By comparison the waiver gate next door has 770 lines of tests.

Worse, the canonical `good_critic` fixture set `"plan_audit": None` — the documented escape
hatch for direction previews — so the positive path never exercised a populated audit at all.
That is exactly where the hole was: `{"plan_audit": {}}` with `contract_card_seen: true` and no
`probes` validated clean and consented, while `agents/critic.md:987` told the critic that the
main loop "rejects a review whose lens-required probe fields or plan_audit subfields are
missing". This suite exists so that sentence is true and stays true.

Both directions are asserted throughout. A gate that only rejects is as broken as one that only
accepts: over-rejecting here means a per-section critic or a direction preview cannot file a
legitimate review, and the first honest failure teaches everyone to bypass the gate.

Run:  python3 tests/test_validate_review.py
"""
import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_review import (  # noqa: E402
    validate_critic, validate_arbiter, PLAN_AUDIT_FIELDS, RUBRIC_OVERLAYS,
)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  — " + detail) if detail and not cond else ""))


def has(errors, needle):
    return any(needle in e for e in errors)


# --------------------------------------------------------------------- fixtures ----

LENS_A_AUDIT = {
    "memory_sentence": "4D recon in one pass; the method is the point.",
    "matches_deck_message": True,
    "curve_visible": "build-up then payoff on slide 6",
    "takeaway_titles": "all content titles match the takeaway table",
    "motion_manifest": "kept",
}
LENS_B_AUDIT = {
    "concept_landed": "carried: the lattice motif is the geometry on 4 slides",
    "skeleton_rhythm": "kept",
    "signature_move": {"verdict": "landed", "why": "the split cover reads at thumbnail size",
                       "carried": [], "proof": "matches"},
    "memorable_one_thing": "one pass, no gating",
    "composition": {"cover_archetype": "kept", "home_skeleton_plurality": "kept"},
    "register_interiors": "kept",
    "money_slide": "landed on slide 6",
    "semantic_colour": "ledger kept",
    "type_tokens": "sizes drawn from the declared tokens",
}
PROBES_BOTH = {
    "per_slide": [{"slide": 1, "first_read": "the title", "takeaway_guess": "the method is fast"}],
    "memory_sentence": "4D recon in one pass; message understood",
}


def sole_critic():
    """A sole critic: runs both lenses, owes both audits and both probes."""
    return {
        "purpose": "MICCAI oral, 10 min, broad audience",
        "rubric_overlay": "academic conference talk",
        "coverage": {"slides_opened": [1, 2, 3],
                     "passes": ["content lens (full deck)", "design lens (full deck)"],
                     "stats_block_seen": True, "contract_card_seen": True},
        "plan_audit": {"lens_a": copy.deepcopy(LENS_A_AUDIT),
                       "lens_b": copy.deepcopy(LENS_B_AUDIT)},
        "probes": copy.deepcopy(PROBES_BOTH),
        "verdict": "consent",
        "summary": "Ships.",
        "strengths": ["clean grid"],
        "findings": [],
    }


def design_lens_critic():
    """A panel critic assigned ONE lens owes only that lens's audit and probe."""
    r = sole_critic()
    r["coverage"]["passes"] = ["design lens (full deck)"]
    r["plan_audit"] = {"lens_b": copy.deepcopy(LENS_B_AUDIT)}
    r["probes"] = {"per_slide": copy.deepcopy(PROBES_BOTH["per_slide"])}
    return r


def audience_critic():
    """The third panel critic: back-of-room readability and jargon, not the contract card.

    `references/review-rubrics.md` gives it its own turf, `references/large-deck-orchestration.md`
    dispatches it beside content and design, `references/critic-panel.md` lists it as the optional
    third panel member — and `agents/critic.md` defines a `plan_audit` shape for two lenses only.
    So this critic legitimately holds the card as context and audits none of it.
    """
    r = sole_critic()
    r["coverage"]["passes"] = ["back-of-room pass (full deck)"]
    r["plan_audit"] = None
    r.pop("probes", None)
    return r


def direction_preview():
    """No plans exist, so there is no contract card to audit and no probe owed."""
    r = sole_critic()
    r["coverage"]["contract_card_seen"] = "none-declared"
    r["plan_audit"] = None
    r.pop("probes", None)
    return r


# ------------------------------------------------------------------------ tests ----

def main():
    print("validate_review contract")

    # --- the positive paths must stay open -------------------------------------------
    check("a sole critic with both audits validates", validate_critic(sole_critic()) == [],
          str(validate_critic(sole_critic())))
    check("a single-lens panel critic is not asked for the other lens",
          validate_critic(design_lens_critic()) == [], str(validate_critic(design_lens_critic())))
    check("a direction preview (plan_audit null, no probes) validates",
          validate_critic(direction_preview()) == [], str(validate_critic(direction_preview())))

    # --- D1: the hole this suite was written for -------------------------------------
    r = sole_critic()
    r["plan_audit"] = {}
    r.pop("probes")
    errs = validate_critic(r)
    check("D1 — empty plan_audit + contract_card_seen:true is rejected",
          has(errs, "contract_card_seen` is true but the audit is empty"))
    check("D1 — the omitted lens audits are each named", has(errs, "$.plan_audit.lens_a: missing")
          and has(errs, "$.plan_audit.lens_b: missing"))

    for lens, fields in PLAN_AUDIT_FIELDS.items():
        for field in fields:
            r = sole_critic()
            del r["plan_audit"][lens][field]
            check("a missing %s.%s is rejected" % (lens, field),
                  has(validate_critic(r), "$.plan_audit.%s.%s: missing" % (lens, field)))

    r = sole_critic()
    del r["plan_audit"]["lens_b"]["signature_move"]["verdict"]
    check("signature_move.verdict is required inside the nested block",
          has(validate_critic(r), "signature_move.verdict"))
    r = sole_critic()
    del r["plan_audit"]["lens_b"]["composition"]["cover_archetype"]
    check("composition.cover_archetype is required inside the nested block",
          has(validate_critic(r), "composition.cover_archetype"))

    # --- probes are owed per lens, not globally --------------------------------------
    r = sole_critic()
    r["probes"] = {"memory_sentence": "x"}
    check("the design lens is held to its per_slide probe",
          has(validate_critic(r), "$.probes.per_slide: missing"))
    r = sole_critic()
    r["probes"] = {"per_slide": copy.deepcopy(PROBES_BOTH["per_slide"])}
    check("the content lens is held to its memory_sentence probe",
          has(validate_critic(r), "$.probes.memory_sentence: missing"))
    r = design_lens_critic()
    check("a design-lens critic is NOT asked for memory_sentence",
          not has(validate_critic(r), "$.probes.memory_sentence"))

    # --- the THIRD panel critic must still be able to file -----------------------------
    # review-rubrics.md gives the audience critic its own turf at raise-count 1,
    # large-deck-orchestration.md dispatches it beside content and design, and critic-panel.md
    # lists it as the optional third panel member. It judges the ROOM, not the contract card,
    # so it owes no lens audit — the first draft of this gate rejected it outright, which is
    # the over-rejection this suite's header warns about, caught by its own rule.
    for phrasing in ("back-of-room pass (full deck)", "audience pass (full deck)",
                     "back of room readability pass"):
        r = audience_critic()
        r["coverage"]["passes"] = [phrasing]
        check("an audience critic (%s) is not asked for a lens audit" % phrasing[:22],
              validate_critic(r) == [], str(validate_critic(r)))
    r = audience_critic()
    r["plan_audit"] = {}
    check("an audience critic may leave plan_audit empty as well as null",
          validate_critic(r) == [], str(validate_critic(r)))

    # --- the SECTIONED panel: role decides the probe, not the lens ---------------------
    # agents/critic.md:958 — "section critics fill per_slide for their slides and the whole-deck
    # coherence critic fills memory_sentence". Deriving the probe from the lens rejected BOTH
    # halves of a panel that large-deck-orchestration.md makes mandatory on every ~15+ slide deck.
    r = sole_critic()
    r["coverage"]["scope"] = [4, 9]
    r["coverage"]["slides_opened"] = [4, 5, 6, 7, 8, 9]
    r["coverage"]["passes"] = ["content lens (slides 4-9)", "design lens (slides 4-9)"]
    r["probes"] = {"per_slide": copy.deepcopy(PROBES_BOTH["per_slide"])}
    check("a per-section critic owes per_slide and NOT a whole-deck memory sentence",
          validate_critic(r) == [], str(validate_critic(r)))
    r["probes"] = {"memory_sentence": "x"}
    check("...but it is still held to per_slide",
          has(validate_critic(r), "$.probes.per_slide: missing"))

    r = sole_critic()
    r["coverage"]["passes"] = ["whole-deck coherence pass — arc, seams, content and design"]
    r["probes"] = {"memory_sentence": "one pass, no gating"}
    check("the whole-deck coherence critic owes memory_sentence and NOT per_slide",
          validate_critic(r) == [], str(validate_critic(r)))

    # --- a scalar where the evidence goes is a skipped judgement, not a shorthand -------
    # The sibling fields ARE plain strings (`skeleton_rhythm`, `register_interiors`), so this is
    # how the block naturally degrades — and a `_is(…, "dict")` guard with no else let it buy a
    # silent exemption from `proof`, the rendered evidence the audit exists for.
    for key, bad in (("signature_move", "landed"), ("composition", "kept"),
                     ("signature_move", None), ("composition", ["kept"])):
        r = design_lens_critic()
        r["plan_audit"]["lens_b"][key] = bad
        check("a %s of %r is rejected, not skipped" % (key, bad),
              has(validate_critic(r), "$.plan_audit.lens_b.%s: wrong type" % key))

    # --- the gate must understand the language the deck is written in ------------------
    # This skill dispatches the critic in the deck's language; a critic writing
    # `passes: ["设计视角（全篇）"]` matched no English word and was asked for the OTHER lens.
    r = design_lens_critic()
    r["coverage"]["passes"] = ["设计视角（全篇）"]
    check("a Chinese single-lens critic is not asked for the other lens",
          validate_critic(r) == [], str(validate_critic(r)))
    r = sole_critic()
    r["coverage"]["passes"] = ["内容视角（全篇）", "设计视角（全篇）"]
    check("a Chinese sole critic validates", validate_critic(r) == [], str(validate_critic(r)))

    # ...but an UNPARSEABLE passes line is a sole critic, not a free exemption
    r = sole_critic()
    r["coverage"]["passes"] = ["a pass with no lens word in it"]
    r["plan_audit"] = {"something_else": 1}
    errs = validate_critic(r)
    check("a passes line naming no known pass is held to BOTH lens audits",
          has(errs, "$.plan_audit.lens_a: missing") and has(errs, "$.plan_audit.lens_b: missing"))
    # ...and EMPTY lens dicts are not an audit either. `{"lens_a": {}, "lens_b": {}}` is the D1
    # shape plus two characters, and a fallback that asked only whether a lens KEY exists let it
    # through — clean, consenting, and recorded into .deck-gates.json as machine-verified.
    for passes in (["full deck (both lenses)"], [], ["a pass with no known word"]):
        r = sole_critic()
        r["coverage"]["passes"] = passes
        r["plan_audit"] = {"lens_a": {}, "lens_b": {}}
        r.pop("probes", None)
        errs = validate_critic(r)
        check("empty lens dicts are rejected (passes=%s)" % str(passes)[:26],
              has(errs, "$.plan_audit.lens_a.memory_sentence: missing")
              and has(errs, "$.plan_audit.lens_b.concept_landed: missing")
              and has(errs, "$.probes."))
    r = sole_critic()
    r["coverage"]["passes"] = ["a pass with no lens word in it"]
    r["plan_audit"] = None
    r.pop("probes", None)
    check("an unparseable passes line cannot buy the exemption with plan_audit:null",
          has(validate_critic(r), "contract_card_seen` is true but the audit is null"))

    # --- rules that already existed, now actually covered ----------------------------
    r = sole_critic()
    r["findings"] = [{"id": "f1", "slide": 2, "severity": "blocker", "dimension": "figures",
                      "issue": "clipped", "why": "unreadable", "fix": "recrop"}]
    check("consent with an open blocker is rejected",
          has(validate_critic(r), "forces verdict 'revise'"))

    r = sole_critic()
    r["coverage"]["slides_opened"] = [1, "2", 3]
    check("a non-int slide number in slides_opened is rejected",
          has(validate_critic(r), "slides_opened[1]"))

    r = sole_critic()
    r["coverage"]["contract_card_seen"] = "maybe"
    check("an invalid contract_card_seen value is rejected",
          has(validate_critic(r), "contract_card_seen: invalid value"))

    for bad in ("vibes", "none"):
        r = sole_critic()
        r["rubric_overlay"] = bad
        check("rubric_overlay %r is rejected" % bad, validate_critic(r) != [])
    for good in RUBRIC_OVERLAYS[:2] + ("none — external deck, no purpose overlay fits",):
        r = sole_critic()
        r["rubric_overlay"] = good
        check("rubric_overlay %r is accepted" % good[:34], validate_critic(r) == [],
              str(validate_critic(r)))

    r = sole_critic()
    del r["purpose"]
    check("a missing purpose is rejected", has(validate_critic(r), "$.purpose: missing"))
    r = sole_critic()
    del r["coverage"]
    check("a missing coverage block is rejected", has(validate_critic(r), "$.coverage: missing"))
    check("a non-object review is rejected", validate_critic([1, 2]) != [])

    # --- arbiter side ----------------------------------------------------------------
    arb_ok = {"verdicts": [{"finding_ref": "s2-crop-1", "fix_verdict": "helps",
                            "real_verdict": "real",
                            "rederivation": "opened slide 2's PNG; the legend is cut mid-glyph",
                            "why": "the legend is whole now"}]}
    check("a well-formed arbiter verdict validates", validate_arbiter(arb_ok) == [],
          str(validate_arbiter(arb_ok)))
    arb_bad = {"verdicts": [{"finding_ref": "s2-crop-1", "fix_verdict": "hurts",
                             "real_verdict": "real",
                             "rederivation": "opened slide 2's PNG; the axis label is gone",
                             "why": "it clipped the axis"}]}
    check("fix_verdict 'hurts' without better_fix is rejected",
          has(validate_arbiter(arb_bad), "better_fix"))

    # --- the CLI itself, not just the functions --------------------------------------
    tmp = tempfile.mkdtemp(prefix="validate_review_")
    good_path = os.path.join(tmp, "good.json")
    json.dump(sole_critic(), open(good_path, "w"))
    r = subprocess.run([sys.executable, str(SCRIPTS / "validate_review.py"), "critic", good_path],
                       capture_output=True, text=True)
    check("CLI exits 0 on a valid review", r.returncode == 0, r.stdout + r.stderr)
    bad_path = os.path.join(tmp, "bad.json")
    b = sole_critic()
    b["plan_audit"] = {}
    json.dump(b, open(bad_path, "w"))
    r = subprocess.run([sys.executable, str(SCRIPTS / "validate_review.py"), "critic", bad_path],
                       capture_output=True, text=True)
    check("CLI exits non-zero on an unaudited contract card", r.returncode != 0)

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
