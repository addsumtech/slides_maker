#!/usr/bin/env python3
"""A rule whose documented exception cannot be recorded forces a FALSE record.

Three of these were hit in one session, and they share a shape: the skill states a legitimate
exception, the gate has no way to express it, and the author writes something untrue to get past.

1. `material_probe` — Step 2 says the probe is skipped on "a registered/provided template or a
   Mode-A mimic … or a 1-2 slide tiny ask". `grep -c 'material_probe.*waiv'` was **0 in both
   gates**. A deck on a registered template had to invent a probe artifact and write a note into
   the record explaining that the gate and the prose disagreed.
2. `icon_none_category` — the four values all make a claim about the DECK, and none can say *the
   user asked for no icons*. A deck whose user said 「不需要icon」 was filed `template-locked`, a
   different claim — and the Codex gate VERIFIES that claim against the built file, so a forced
   label can also fail for the wrong reason.
3. `NO NOTES` — `builds="static"` exists so a user's opt-out stops reading as an omission.
   Removing the spoken script is the same kind of decision and had nowhere to live, so the warning
   fired on every lint run forever.

Plus the divergence nothing watched for: a user's hand-edits to a delivered .pptx were invisible to
every tool in the repo.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import warnings
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
warnings.simplefilter("ignore")

import deckkit as dk                      # noqa: E402
import deck_gates as dg                   # noqa: E402
import render_deck as rd                  # noqa: E402
import codex_delivery_gate as cg          # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


def _filled(n=2):
    g = json.loads(json.dumps(dg.template(n, "presented")))
    d = g["design_plan"]
    d.update({"boldness": "balanced+",
              "concept": {"chosen": "a measured column",
                          "rejected": [{"concept": "a scanner", "why_lost": "the domain stereotype"},
                                       {"concept": "a gauge", "why_lost": "encodes cost not physics"}]},
              "signature_move": "the extent drawn at true proportion",
              "carried_by": [1, 2], "form_ledger": "blocks 2", "icon_family": "tabler",
              "palette": "FILL/TEXT split", "style_pick": "n/a — locked template",
              "build_shape": "solo — one argument",
              "image_sources": ["slide 1 | x | provided — user (own material)"],
              "motif_generates": {"background": "flat", "markers": "tick", "page": "slide 2"},
              "signature_proof": [{"role": r, "slide": 1, "png": "render/slide01.png"}
                                  for r in ("signature", "complex", "data")],
              "checkpoint": {"mode": "approved", "record": "posted"}})
    g["content"]["open_ledger"] = []
    g["critic"] = {"waived": "the user declined with the deck visible",
                   "waived_category": "user-waived"}
    g["render_selfcheck"] = {"slides": [{"n": i + 1, "verdict": "ok"} for i in range(n)]}
    return g


# ------------------------------------------------- 1. the material probe's documented carve
check(dg.MATERIAL_PROBE_CARVES == rd.MATERIAL_PROBE_CARVES,
      "the two gates share ONE carve vocabulary — a pre-flight that rejects what the gate accepts "
      "is worse than no pre-flight, and this repo has drifted on duplicated field lists before")

g = _filled()
g["design_plan"]["material_probe"] = {
    "waived": "built on the user's own registered LKEB/LUMC template — the material is its",
    "waived_category": "registered-template"}
check(not [p for p in dg.check(g) if "material_probe" in p],
      "🔴 a NAMED carve is accepted — before this the gate had no waiver arm at all, so a deck on "
      "a registered template invented a probe artifact and noted that the gate and SKILL.md "
      "disagreed")

g["design_plan"]["material_probe"] = {"waived": "boldness is conservative, nothing to prove",
                                      "waived_category": "conservative"}
probs = [p for p in dg.check(g) if "material_probe" in p]
check(probs and "conservative" in probs[0],
      "🔴 ...and `conservative` is REFUSED by name — Step 2 says restraint is a material decision "
      "too, and a page is where you see whether it reads as deliberate or as nothing")

g["design_plan"]["material_probe"] = {"waived": "template", "waived_category": "registered-template"}
check([p for p in dg.check(g) if "material_probe" in p],
      "...and a category with no written reason is refused: which template, which mimic, how many "
      "slides — a bare category is a label, not a decision")


# ----------------------------------------------------- 2. the icon reason that could not be said
for mod, name in ((rd, "shared"), (cg, "codex")):
    cats = getattr(mod, "_ICON_NONE_CATEGORIES", None) or getattr(mod, "ICON_NONE_CATEGORIES")
    check("user-declined" in cats,
          "🔴 `user-declined` is a category on the {} path — the other four each make a claim about "
          "the DECK and none can say the USER decided, so a deck whose user said 不需要icon was "
          "filed `template-locked`, a different claim the Codex gate then verifies against the "
          "file".format(name))
check(set(getattr(rd, "_ICON_NONE_CATEGORIES")) == set(getattr(cg, "ICON_NONE_CATEGORIES")),
      "...and the two runtimes carry the SAME set, which is the drift this repo keeps having to fix")


# ------------------------------------------------------- 3. the notes opt-out, twin of builds
tmp = Path(tempfile.mkdtemp(prefix="rec-"))
prs = dk.blank_deck()
# FOUR slides on purpose: `NO NOTES` only fires above two, so a smaller fixture would assert the
# absence of a warning that was never going to appear — a test passing for the wrong reason.
for _i in range(4):
    s = dk.add_slide(prs)
    dk.text(s, 1, 1, 8, 1, [[("A headline %d" % _i, 24, dk.DEEP, True, False, dk.FONT)]])
deck = tmp / "d.pptx"
prs.save(str(deck))
dk.declare_delivery(str(deck), "presented", builds="static", notes="none")
blob = json.loads((tmp / ".deck-gates.json").read_text(encoding="utf-8"))
check(blob.get("notes") == "none" and blob.get("builds") == "static",
      "🔴 `declare_delivery(..., notes='none')` records the user's decision, exactly as "
      "`builds='static'` already did for the other one")
try:
    dk.declare_delivery(str(deck), "presented", notes="maybe")
    bad.append("an unknown notes value was accepted")
except ValueError as exc:
    check("none" in str(exc),
          "...and an unknown value raises rather than silently recording a state nothing reads")

r = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(deck)],
                   capture_output=True, text=True)
out = r.stdout + r.stderr
# the WARNING form carries a colon; the stand-down line names the code too, so match precisely
check("NO NOTES:" not in out,
      "🔴 ...and NO NOTES stands down for a deck that recorded the choice, instead of firing on "
      "every lint run forever and being waived by hand each time")
check("notes: RECORDED as none" in out,
      "...and it SAYS it stood down, so a silenced warning is visible rather than merely absent")
check("word budget is unchanged" in out,
      "🔴 ...while stating that the word budget is NOT raised — the skill argues sentences belong "
      "in the notes, so a deck carrying them on the slides is a tension worth still seeing, and "
      "moving the ceiling would use the tooling to endorse what the skill argues against")


# --------------------------------------------- 4. the hand-edit nothing used to watch for
check(blob.get("deck_sha256") and blob.get("deck_file") == "d.pptx",
      "🔴 the build records the sha256 of what it saved — `handoff-and-iteration.md` documented "
      "the reconcile procedure the whole time and nothing ever said a reconcile was NEEDED")
before = blob["deck_sha256"]
with zipfile.ZipFile(deck, "a") as z:
    z.writestr("docProps/edited.txt", "a user edit in PowerPoint")
after = hashlib.sha256(deck.read_bytes()).hexdigest()
check(after != before,
      "...and a save from PowerPoint moves it, which is what makes the comparison meaningful")

_hi = (ROOT / "references" / "handoff-and-iteration.md").read_text(encoding="utf-8")
check("EDITED SINCE BUILD" in _hi and "never blocks" in _hi,
      "...and the reconcile reference says the detector exists AND that it reports rather than "
      "blocks — hand-editing a delivered deck is normal; what was missing was any way to know")
check("not before a rebuild overwrites" in _hi,
      "🔴 ...and states its honest limit rather than implying it prevents the clobber: it fires at "
      "the gate, so run --gate-check before regenerating a deck you have handed over")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
