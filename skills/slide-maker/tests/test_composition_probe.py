#!/usr/bin/env python3
"""The composition competition: the signature page is CHOSEN between, not composed once.

The module's `--selftest` builds the calibration pairs and proves the floor separates them. This
file covers what that cannot: that the measure means what it claims on inputs it was not tuned on,
that it generalises off 16:9 and off English, that the contract is wired into every gate path
identically, and that the anti-theatre check cannot be satisfied by restyling one layout.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import composition_probe as cp  # noqa: E402
import deckkit as dk  # noqa: E402

os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/nonexistent/taste-ledger-for-tests.json"

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


r = subprocess.run([sys.executable, str(SCRIPTS / "composition_probe.py"), "--selftest"],
                   capture_output=True, text=True)
check(r.returncode == 0, "composition_probe.py --selftest failed:\n{}{}".format(r.stdout, r.stderr))

W = "a real line of words that carries this page"


def deck_of(layouts, path):
    prs = dk.blank_deck()
    for boxes in layouts:
        s = dk.add_slide(prs)
        for (x, y, w, h) in boxes:
            dk.text(s, x, y, w, h, [[(W, 14, dk.DEEP, False, False, dk.FONT)]])
        dk.speaker_notes(s, "n")
    prs.save(str(path))
    return path


# ── 🔴 THE ANTI-THEATRE PROPERTY, on variants of ONE page ────────────────────────────────────────
# The direction gate learned this at look level: "options" collapse into one layout in three
# colourways unless something mechanical refuses them. Here the same trap is a page restyled.
CHROME = [(0.6, 0.5, 10.0, 0.3), (0.6, 0.9, 11.0, 1.1), (0.6, 6.9, 11.0, 0.4)]
THREE_COL = [(0.6 + i * 3.9, 2.6, 3.5, 2.4) for i in range(3)]
STACKED = [(5.2, 2.5 + i * 1.4, 6.4, 1.2) for i in range(3)]
HERO = [(0.6, 2.4, 7.0, 3.6), (8.2, 2.6, 3.6, 1.4), (8.2, 4.2, 3.6, 1.4)]

with tempfile.TemporaryDirectory() as td:
    d = deck_of([CHROME + THREE_COL, CHROME + STACKED, CHROME + HERO, CHROME + THREE_COL],
                Path(td) / "v.pptx")
    sigs = cp.variant_signatures(d, [0, 1, 2, 3])

    # A vs D is the SAME layout (identical boxes) — it must be caught even though the deck's
    # chrome is identical across all four, which is exactly what would mask it.
    check(cp.divergence(sigs[0], sigs[3]) < cp.SAME_COMPOSITION,
          "two identical layouts were not recognised as the same composition")
    for i, j in ((0, 1), (0, 2), (1, 2)):
        check(cp.divergence(sigs[i], sigs[j]) >= cp.SAME_COMPOSITION,
              "genuinely different compositions {} vs {} scored below the floor ({:.3f}) — the "
              "measure would reject real variants".format(i, j, cp.divergence(sigs[i], sigs[j])))
    labelled = [{"label": L, "signature": s} for L, s in zip("ABCD", sigs)]
    check(cp.faults(labelled), "a restyled duplicate passed as a competition")
    check(not cp.faults(labelled[:3]), "three real variants were rejected: {}"
                                       .format(cp.faults(labelled[:3])))

    # 🔴 THE SUBTRACTION IS LOad-BEARING. Without removing the shared chrome, variants of one page
    # all look alike and the floor separates nothing.
    raw = [cp.signature(d, i) for i in range(3)]
    kept = sum(1 for i, j in ((0, 1), (0, 2), (1, 2))
               if cp.divergence(raw[i], raw[j]) >= cp.SAME_COMPOSITION)
    sub = sum(1 for i, j in ((0, 1), (0, 2), (1, 2))
              if cp.divergence(sigs[i], sigs[j]) >= cp.SAME_COMPOSITION)
    check(sub >= kept, "dropping the shared chrome made variants look MORE alike, which is the "
                       "opposite of what it is for")

# ── 🔴 HELD-OUT VALIDATION — layouts the weights were NOT fitted on ──────────────────────────────
# The weights and the floor were found by search over a 10-layout corpus. A measure that only works
# on the corpus it was tuned on is exactly the defect this file exists to prevent, so it is re-run
# here against nine layouts that took no part in that search. Zero errors over 36 pairs when this
# was written; a weight change that breaks generality fails HERE rather than in a real deck.
HELD = {
    "5col":       [(0.6 + i * 2.3, 2.6, 2.1, 2.4) for i in range(5)],
    "5col_short": [(0.6 + i * 2.3, 2.8, 2.1, 1.8) for i in range(5)],   # same composition, shorter
    "5col_same":  [(0.6 + i * 2.3, 2.6, 2.1, 2.4) for i in range(5)],   # identical
    "L_shape":    [(0.6, 2.4, 4.0, 3.6), (5.0, 2.4, 7.0, 1.5), (5.0, 4.3, 7.0, 1.7)],
    "center_one": [(3.2, 2.4, 6.0, 3.4)],
    "asym_split": [(0.6, 2.4, 3.0, 3.6), (4.0, 2.4, 8.0, 3.6)],
    "ladder":     [(0.6 + i * 1.2, 2.4 + i * 1.0, 5.0, 0.9) for i in range(4)],
    "full_bleed": [(0.0, 2.2, 13.33, 3.8)],
    "corner4":    [(0.6, 2.3, 4.0, 1.6), (8.0, 2.3, 4.0, 1.6),
                   (0.6, 4.6, 4.0, 1.6), (8.0, 4.6, 4.0, 1.6)],
}
import itertools  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    hp = deck_of([CHROME + HELD[k] for k in HELD], Path(td) / "held.pptx")
    hs = dict(zip(HELD, cp.variant_signatures(hp, list(range(len(HELD))))))
    same_pairs = [(a, b) for a, b in itertools.combinations(HELD, 2)
                  if a.startswith("5col") and b.startswith("5col")]
    diff_pairs = [(a, b) for a, b in itertools.combinations(HELD, 2)
                  if not (a.startswith("5col") and b.startswith("5col"))]
    for a, b in same_pairs:
        d = cp.divergence(hs[a], hs[b])
        check(d < cp.SAME_COMPOSITION,
              "HELD-OUT: `{}` and `{}` are the same composition but scored {:.3f} >= {:.2f} — real "
              "variants of one layout would be rejected".format(a, b, d, cp.SAME_COMPOSITION))
    for a, b in diff_pairs:
        d = cp.divergence(hs[a], hs[b])
        check(d >= cp.SAME_COMPOSITION,
              "HELD-OUT: `{}` and `{}` are different compositions but scored {:.3f} < {:.2f} — a "
              "real competition would be refused as theatre".format(a, b, d, cp.SAME_COMPOSITION))
    # 🔴 the sparse case specifically: with one block the structure terms are degenerate, so the
    # weighting has to lean on the grid or a centred card reads as a full-bleed band
    check(cp.divergence(hs["center_one"], hs["full_bleed"]) >= cp.SAME_COMPOSITION,
          "a centred card and a full-bleed band read as the SAME composition — the adaptive "
          "weighting for sparse pages has regressed")

# ── generality: not 16:9, not English, not a shape the measure was tuned on ──────────────────────
check(cp._grid_dims(9 / 16)[1] > cp._grid_dims(9 / 16)[0],
      "a portrait canvas did not get a tall grid — a 9:16 story deck would be measured as if it "
      "were a slide deck")
check(cp._grid_dims(16 / 9) != cp._grid_dims(9 / 16),
      "landscape and portrait canvases share a grid")
for aspect in (16 / 9, 4 / 3, 1.0, 9 / 16, 0.71):
    c, rr = cp._grid_dims(aspect)
    check(c >= 2 and rr >= 2, "degenerate grid for aspect {:.2f}".format(aspect))

# The measure reads geometry only, so the SAME layout must fingerprint identically whatever the
# words are. This repo has shipped a family of geometry gates that measured CJK text 46% short.
with tempfile.TemporaryDirectory() as td:
    prs = dk.blank_deck()
    for txt in ("a short english line",
                "一行足够长的中文文案用来验证测量与语言无关" * 3):
        s = dk.add_slide(prs)
        for (x, y, w, h) in CHROME + THREE_COL:
            dk.text(s, x, y, w, h, [[(txt, 14, dk.DEEP, False, False, dk.FONT)]])
        dk.speaker_notes(s, "n")
    p = Path(td) / "lang.pptx"
    prs.save(str(p))
    en, zh = cp.signature(p, 0), cp.signature(p, 1)
    check(cp.divergence(en, zh) == 0.0,
          "the same layout fingerprinted differently in Chinese and English (divergence {:.3f}) — "
          "the measure is not language-independent".format(cp.divergence(en, zh)))

# ── robustness: malformed input degrades, never raises ───────────────────────────────────────────
for junk in (None, {}, 7, "str", [1], {"grid": None}):
    try:
        cp.divergence(junk, en)
        cp.divergence(en, junk)
    except Exception as e:                                             # noqa: BLE001
        fails.append("divergence raised on {!r}: {}".format(junk, e))
    check(cp.faults(junk) != [], "faults({!r}) passed as a competition".format(junk))

# ── the record contract ──────────────────────────────────────────────────────────────────────────
GOOD = {"variants": [{"label": "A", "signature": sigs[0]}, {"label": "B", "signature": sigs[1]}],
        "picked": "B", "why": "B carries its claim in one beat; A buried it under the list"}
check(not cp.competition_faults(GOOD), "a real competition was rejected: {}"
                                       .format(cp.competition_faults(GOOD)))
check(cp.competition_faults(dict(GOOD, why="looks better")),
      "`looks better` passed as the reason — the sentence this step exists to replace")
check(cp.competition_faults(dict(GOOD, why="this one reads much faster than the other one")),
      "a reason naming NEITHER version passed — a comparison that never mentions what it compared "
      "is a preference")
check(cp.competition_faults(dict(GOOD, picked="Z")), "a pick naming no variant passed")
check(cp.competition_faults(dict(GOOD, variants=GOOD["variants"][:1])),
      "one variant passed as a competition")
check(cp.competition_faults(None), "a missing record passed")
# 🔴 language-independent width: the same bar in Chinese as in English
check(not cp.competition_faults(dict(GOOD, why="B 的主张一眼读得出来，A 把它埋在列表里了")),
      "a real CJK reason was rejected — `len()` instead of reason_width would do exactly this")
check(cp.competition_faults({"waived": "x", "waived_category": "template-locked"}),
      "a carve with a token reason passed")

# ── 🔴 THE CARVE MUST BE TRUE OF THE ARTIFACT, NOT MERELY TYPED ─────────────────────────────────
# The icon gate paid for this lesson already: "the word was doing the work, not the fact". The
# generated-identity branch (Q1 d) is the case that matters — it sits on a BLANK deck, so it must
# not be able to borrow `template-locked`, whose whole claim is that someone's template is in play.
with tempfile.TemporaryDirectory() as td:
    blank = deck_of([CHROME + THREE_COL] * 8, Path(td) / "generated.pptx")
    tiny = deck_of([CHROME + THREE_COL] * 2, Path(td) / "tiny.pptx")
    ok, why = cp.carve_holds({"waived": "the generated identity owns the look",
                              "waived_category": "template-locked"}, blank, {})
    check(not ok, "a GENERATED visual identity borrowed `template-locked` — it is built on a blank "
                  "deck, and the Q1 choice decides the LOOK SOURCE, never who composes the pages")
    check("blank" in why.lower() or "stock" in why.lower(),
          "the refusal does not say why: {}".format(why[:120]))
    check(not cp.carve_holds({"waived": "a small deck, nothing to compete",
                              "waived_category": "tiny-ask"}, blank, {})[0],
          "an 8-slide deck claimed `tiny-ask`")
    check(cp.carve_holds({"waived": "a two-slide answer, no signature page",
                          "waived_category": "tiny-ask"}, tiny, {})[0],
          "a genuinely tiny deck was refused its carve")
    check(not cp.carve_holds({"waived": "no aesthetic risk was taken here",
                              "waived_category": "conservative"}, blank,
                             {"design_plan": {"boldness": "bold"}})[0],
          "a deck declaring `bold` claimed the `conservative` carve")
    # 🔴 and on the CODEX schema, where the design block is called `design`
    check(not cp.carve_holds({"waived": "no aesthetic risk was taken here",
                              "waived_category": "conservative"}, blank,
                             {"design": {"boldness": "bold"}})[0],
          "the carve check missed the Codex spelling — the runtime this generalisation is about")
    check(cp.carve_holds({"waived": "no aesthetic risk was taken here",
                          "waived_category": "conservative"}, blank,
                         {"design_plan": {"boldness": "conservative"}})[0],
          "a genuinely conservative deck was refused")
    # `user-waived` stays as declared, like the icon gate's `editorial-register`
    check(cp.carve_holds({"waived": "the user asked for one layout throughout",
                          "waived_category": "user-waived"}, blank, {})[0],
          "`user-waived` was measured — what the user said is not a property of the file")
    # never fail the gate on the reader itself
    for junk in (None, "/nonexistent.pptx"):
        try:
            cp.carve_holds({"waived_category": "template-locked"}, junk, {})
        except Exception as e:                                         # noqa: BLE001
            fails.append("carve_holds raised on {!r}: {}".format(junk, e))
check("carve_holds" in (SCRIPTS / "render_deck.py").read_text(encoding="utf-8"),
      "render_deck accepts the carve on the WORD alone — the check exists but nothing calls it")
check(not cp.competition_faults({"waived": "a provided template owns this composition entirely",
                                 "waived_category": "template-locked"}),
      "a properly claimed carve was rejected")

# ── wired into every gate path, like every other shared contract ─────────────────────────────────
for name in ("render_deck.py", "deck_gates.py", "codex_delivery_gate.py"):
    src = (SCRIPTS / name).read_text(encoding="utf-8")
    check("composition_probe" in src,
          "{} does not consume the composition contract — a floor kept in one runtime only is how "
          "the others stop enforcing it".format(name))
    check("SAME_COMPOSITION" not in src,
          "{} hard-codes the divergence floor instead of importing it".format(name))

# the init skeleton must PASS its own gate's shape, not fail it
r = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "--selftest"],
                   capture_output=True, text=True)
check(r.returncode == 0, "deck_gates --selftest failed after wiring:\n{}".format(r.stdout[-600:]))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_composition_probe] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
