#!/usr/bin/env python3
"""The research progress deck: the shape it needs, the ledger that keeps it honest, one geometry trap.

Four defects from one delivered lab-meeting deck, each of which the pipeline had no way to catch:

1. The commonest lab deck there is — *what we built, what it showed, why we are changing approach*
   — had no ARC SHAPE, so it was filed as `problem-turn-evidence`. That shape's evidence proves the
   NEW thing, so the prior work's result pages landed AFTER the pivot and the user reordered them
   by hand.
2. A slide asserted that extra respiratory bins helped the reconstruction while the source listed
   *"tests whether each bin helps"* as an OPEN GATE. The fact was really in the source — promoted
   from hypothesis to result — so never-invent and the claim ledger both waved it through.
3. A later edit deleted the status page, and with it the only statement that the new method had no
   reconstruction result yet. Nothing noticed.
4. `measure_text` assumed its own line factor while `text()` took any `line_spacing`, so a measured
   height placed at 1.16 was ~4% short — and a divider derived from it was drawn THROUGH the block
   above, with both linters reporting the page clean.
"""
import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
warnings.simplefilter("ignore")

import deckkit as dk                 # noqa: E402
import deck_gates as dg              # noqa: E402
import arc_divergence as ad          # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


# ------------------------------------------------------- 1. the arc shape that did not exist
check("method-pivot" in ad._SHAPES,
      "🔴 `method-pivot` is a shape the arc gate accepts — the commonest lab-meeting deck (what we "
      "built / what it showed / why we are changing approach) previously had to file itself as "
      "`problem-turn-evidence`, whose evidence proves the NEW thing, which is what put the prior "
      "work's results after the pivot")
check("method-pivot" not in ad._TEACHING_SHAPES,
      "...and it is an argue/report shape, so its `objection` and `closing_ask` keep their ordinary "
      "reading rather than the learner's-misconception one")
_pl = (ROOT / "agents" / "content-planner.md").read_text(encoding="utf-8")
check("method-pivot" in _pl and "BEFORE the pivot" in _pl,
      "...and the planner spells out the ORDER it implies — the retired approach's results come "
      "BEFORE the turn, which is the whole reason the shape exists rather than a synonym")
check("ENDS ON STATUS" in _pl,
      "...and that the deck ends on status, because the replacement's slide is not evidence")

_dp = (ROOT / "references" / "design-by-purpose.md").read_text(encoding="utf-8")
check("method-pivot" in _dp and "WHAT IT WAS FOR" in _dp,
      "the design half carries the same three moves under *Research meeting*, where an art "
      "director actually reads them — including that every step of the retired method owes its "
      "PURPOSE, not just its mechanics")
check("owes a result" in _dp,
      "...and that an enumerated step owes a result or an explicit 'not yet reported', so a later "
      "slide cannot argue from a measurement the deck never showed")


# --------------------------------------------- 2 & 3. the OPEN ledger, and its gate
tpl = json.loads(json.dumps(dg.template(3, "presented")))
check("open_ledger" in tpl["content"],
      "🔴 `content.open_ledger` is in the scaffold — a capability that does not reach the scaffold "
      "is one nobody fills in")

missing = json.loads(json.dumps(tpl))
del missing["content"]["open_ledger"]
probs = [p for p in dg.check(missing) if "open_ledger" in p]
check(probs and "established voice" in probs[0],
      "🔴 the MISSING key blocks, and the message names the failure it exists for: a claim the "
      "source marks as open must not reach a slide in the established voice")

empty = json.loads(json.dumps(tpl))
empty["content"]["open_ledger"] = []
check(not [p for p in dg.check(empty) if "open_ledger" in p],
      "...while `[]` PASSES — it records that the sweep happened. The gate blocks the absence of a "
      "decision, never the count, exactly like `form_reach`")

noloc = json.loads(json.dumps(tpl))
noloc["content"]["open_ledger"] = [{"claim": "each extra bin helps the reconstruction",
                                    "source": "", "in_deck": "absent"}]
probs = [p for p in dg.check(noloc) if "open_ledger" in p]
check(probs and "locator" in probs[0],
      "...and a row with no SOURCE locator is refused — without it the row is an opinion about the "
      "material rather than a reading of it")

good = json.loads(json.dumps(tpl))
good["content"]["open_ledger"] = [
    {"claim": "whether each respiratory bin helps after motion compensation",
     "source": "WALKTHROUGH §Decision Gates — 'Bin-value gate'",
     "in_deck": "stated as open on slide 10"}]
check(not [p for p in dg.check(good) if "open_ledger" in p],
      "...and a complete row passes")

_spec = (ROOT / "references" / "content-plan-spec.md").read_text(encoding="utf-8")
check("OPEN ledger" in _spec and "promoted from hypothesis to result" in _spec,
      "the brief spec names this as a DIFFERENT failure from inventing — the fact is traceable, "
      "which is exactly why the claim ledger passes it")
_cc = (ROOT / "references" / "checkpoint-convention.md").read_text(encoding="utf-8")
check("open ledger:" in _cc,
      "...and the content checkpoint carries an `open ledger:` line, so the user sees the sweep's "
      "result before a slide is designed")

# 🔴 BOTH RUNTIMES, or the floor is only a floor on one of them.
_cg = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")
check('if "open_ledger" not in content' in _cg,
      "🔴 the CODEX gate binds it too — this is the exact shape the repo has drifted on twice, and "
      "a floor kept in one runtime is how the other quietly stops enforcing it")
check('"open_ledger": [' in _cg,
      "...and the Codex evidence SKELETON carries the field, because a runtime filling a template "
      "copies its shape: a check with no scaffold is a field nobody can fill")
_cr = (ROOT / "references" / "codex-runtime.md").read_text(encoding="utf-8")
check("open_ledger" in _cr,
      "...and codex-runtime.md — the file that runtime reads before Step 2 — says so in prose")

# BOTH streams on purpose: `--template` puts the JSON skeleton on stdout so it stays pipeable and
# the shape LISTING on stderr, so a test that reads only stdout checks the wrong stream and passes
# for the wrong reason.
_r = __import__("subprocess").run(
    [sys.executable, str(SCRIPTS / "arc_divergence.py"), "--template"],
    capture_output=True, text=True)
_tpl = (_r.stdout or "") + (_r.stderr or "")
check("method-pivot" in _tpl,
      "🔴 and `arc_divergence.py --template` PRINTS the new shape — that listing is the lookup an "
      "agent actually reads to pick one, and a shape in the enum but not in the listing is a shape "
      "nobody chooses")


# ------------------------------------------- 4. measure and place must name the same spacing
runs = [("a sentence long enough to wrap across several lines inside a fairly narrow column", False)]
base = dk.measure_text(runs, 2.4, 12)
wider = dk.measure_text(runs, 2.4, 12, line_spacing=1.16)
check(wider > base,
      "🔴 `measure_text` takes `line_spacing=`, so measuring at the default and placing at 1.16 is "
      "no longer a silent ~4% shortfall — the defect that drew a divider through the line above it "
      "while both linters called the page clean ({:.3f} -> {:.3f}in)".format(base, wider))
check(abs(wider / base - 1.16) < 0.02,
      "🔴 ...and it COMPOSES with the natural line height rather than replacing it — spcPct is a "
      "multiplier on the face's own line height, so 1.16 must buy 16%, not the 3.6% you get by "
      "substituting 1.16 for the 1.12 default. The first version of this fix substituted, which is "
      "optimistic in the one direction this module forbids, and still looked correct because it "
      "was larger than the default (ratio {:.3f})".format(wider / base))

cjk = [("一段足够长的中文句子用来测试换行与行距下限的行为", False)]
check(dk.measure_text(cjk, 2.4, 12, line_spacing=1.0) >= dk.measure_text(cjk, 2.4, 12) - 1e-9,
      "...and an explicit SMALL spacing cannot push a CJK block under the pitch its script-aware "
      "default actually renders — the floor still applies after the override")
_sig = (SCRIPTS / "sigs.py").read_text(encoding="utf-8")
check("SAME LINE SPACING" in _sig,
      "and it joins the measure-vs-place contract block in `sigs.py` beside its two siblings (the "
      "run-shape mismatch and the font mismatch) — the one lookup an author actually makes")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
