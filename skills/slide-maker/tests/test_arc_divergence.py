#!/usr/bin/env python3
"""The arc-candidate divergence gate — and the two collapses it exists to separate.

The design side has had `directions_diversity.py` for a while; this is its content-side twin, and
the tests below are mostly about the ways the twin is NOT identical:

  · directions collapse into three colourways of one layout — equally developed, equally shallow.
  · arcs collapse into one real argument plus two foils — genuinely different, wildly unequal.

A divergence measure alone scores the second case as a healthy set (a two-beat sketch diverges
beautifully from a twelve-beat argument), which is why `check()` returns `sketches` separately and
why there are tests for each collapse independently.

The CJK cases are the load-bearing ones. This repo has already shipped a measurement that read
Chinese text with Latin assumptions and was silently 46% wrong; a whitespace tokeniser here would
score every pair of Chinese closing asks at 0.0 and turn two of the four axes off on every Chinese
deck — passing, quietly, forever. Both directions are tested: a Chinese collapse must FIRE, and
two genuinely different Chinese arcs must NOT.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import arc_divergence as A                                    # noqa: E402

ok, bad = [], []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="arcs-"))


def _arc(name, shape, roles, q, obj, ask, ev):
    return {"name": name, "shape": shape, "roles": roles, "audience_question": q,
            "objection": obj, "closing_ask": ask, "evidence": ev}


def _run(arcs):
    """Through the CLI, so the exit-code contract is tested and not just check()."""
    p = TMP / ("a%d.json" % len(list(TMP.glob("*.json"))))
    p.write_text(json.dumps(arcs, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "arc_divergence.py"), str(p)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def want(cond, good, wrong):
    (ok if cond else bad).append(good if cond else wrong)


# ----------------------------------------------------------------- a healthy competition
HEALTHY = [
    _arc("contribution", "contribution-first",
         ["problem", "method", "evidence", "comparison", "conclusion"],
         "is the INR formulation actually better than L+S",
         "the gain comes from the extra regulariser, not the representation",
         "accept implicit neural representation as the recon backbone",
         ["c1", "c2", "c3", "c4", "c5", "c6"]),
    _arc("decision", "recommendation-first",
         ["conclusion", "evidence", "comparison", "roadmap", "call-to-action"],
         "should we fund a clinical pilot next quarter",
         "scan-time savings will not survive a real scanner workflow",
         "approve a six-month pilot on the 3T scanner",
         ["c1", "c3", "c7", "c8"]),
    _arc("turn", "problem-turn-evidence",
         ["hook", "problem", "diagnosis", "evidence", "conclusion"],
         "why did every prior acceleration method plateau at 6x",
         "eight-fold undersampling cannot preserve wall motion",
         "believe that the temporal prior is what breaks the plateau",
         ["c2", "c4", "c5", "c9", "c10"]),
]
rc, out = _run(HEALTHY)
want(rc == 0, "three genuinely different arcs over one ledger pass clean",
     "a healthy competition was flagged (rc=%d):\n%s" % (rc, out[:400]))

# ----------------------------------------------------------------- collapse 1: rewordings
COLLAPSED = [
    _arc("A", "contribution-first", ["problem", "method", "evidence", "conclusion"],
         "is this method better than the baseline", "the improvement is within noise",
         "accept the method as the new backbone", ["c1", "c2", "c3", "c4"]),
    _arc("B", "contribution-first", ["problem", "method", "evidence", "comparison"],
         "is this method better than the baseline really",
         "the improvement is within the noise",
         "accept the method as a new backbone", ["c1", "c2", "c3"]),
]
rc, out = _run(COLLAPSED)
want(rc == 2 and "TOO SIMILAR" in out and "shape" in out and "ask" in out,
     "two rewordings of one arc are flagged, with the matched axes named",
     "a collapsed pair passed (rc=%d):\n%s" % (rc, out[:400]))
want("arc gate:" in out,
     "the flag points at the `arc gate:` line where a justification is recorded — the escape "
     "hatch is printed, so a flag is never a dead end",
     "the remedy text does not name where a justification goes:\n%s" % out[:400])

# ----------------------------------------------------------------- collapse 2: strawmen
STRAW = [
    _arc("real", "contribution-first", ["problem", "method", "evidence", "conclusion"],
         "does the representation carry the gain", "the regulariser is doing the work",
         "adopt the INR backbone", ["c%d" % i for i in range(1, 9)]),
    _arc("foil", "chronological", ["hook", "roadmap"],
         "how did the project unfold", "none really", "appreciate the journey", ["c1"]),
]
rc, out = _run(STRAW)
want(rc == 2 and "STRAWMAN" in out,
     "an undeveloped foil is caught even though it DIVERGES perfectly — the failure a pure "
     "divergence measure scores as a healthy set",
     "a strawman candidate passed (rc=%d):\n%s" % (rc, out[:400]))
want("matched: none" in out,
     "…and the divergence axes genuinely reported no match on that pair, proving the strawman "
     "check is what caught it rather than a lucky similarity hit",
     "the foil was caught by divergence, so this case does not test the effort floor:\n%s"
     % out[:400])

# ----------------------------------------------------------------- CJK: must FIRE
CJK_SAME = [
    _arc("甲", "contribution-first", ["problem", "method", "evidence", "conclusion"],
         "这个方法真的比基线更好吗", "提升来自额外的正则项而不是表示本身",
         "接受隐式神经表示作为重建骨干", ["c1", "c2", "c3", "c4"]),
    _arc("乙", "contribution-first", ["problem", "method", "evidence", "comparison"],
         "这个方法真的比基线好吗", "提升来自额外的正则项而非表示本身",
         "接受隐式神经表示作为重建的骨干", ["c1", "c2", "c3"]),
]
rc, out = _run(CJK_SAME)
want(rc == 2 and "TOO SIMILAR" in out,
     "a CHINESE collapse fires — a whitespace tokeniser scores these at 0.0 and switches the "
     "`ask` and `stance` axes off on every Chinese deck",
     "a Chinese collapse passed — the CJK tokeniser is not reaching the text (rc=%d):\n%s"
     % (rc, out[:400]))

# ----------------------------------------------------------------- CJK: must NOT fire
CJK_DIFF = [
    _arc("研究贡献", "contribution-first", ["problem", "method", "evidence", "conclusion"],
         "这个表示方式本身是不是增益的来源", "正则项才是真正起作用的部分",
         "接受隐式神经表示作为重建骨干", ["c1", "c2", "c3", "c4", "c5"]),
    _arc("决策建议", "recommendation-first",
         ["conclusion", "evidence", "roadmap", "call-to-action"],
         "下个季度要不要投人做临床试点", "扫描时间的节省在真实流程里保不住",
         "批准一个为期六个月的临床试点", ["c1", "c3", "c6", "c7"]),
]
rc, out = _run(CJK_DIFF)
want(rc == 0,
     "two genuinely different CHINESE arcs pass — the bigram tokeniser discriminates rather than "
     "flagging everything written in Chinese",
     "genuinely different Chinese arcs were flagged; the CJK threshold over-fires (rc=%d):\n%s"
     % (rc, out[:400]))

# ----------------------------------------------------------------- input contracts
rc, out = _run([HEALTHY[0]])
want(rc == 1 and "not a choice" in out,
     "ONE arc is rejected as a derivation rather than a competition — the exact state this gate "
     "was built to end",
     "a single arc was accepted as a candidate set (rc=%d):\n%s" % (rc, out[:300]))

rc, out = _run([dict(HEALTHY[0], shape="story-time"), HEALTHY[1]])
want(rc == 1 and "story-time" in out and "contribution-first" in out,
     "an unknown shape is refused AND the vocabulary is printed — a typo must never earn a "
     "divergence credit for a shape that does not exist",
     "an invented shape was accepted (rc=%d):\n%s" % (rc, out[:300]))

# THE ROLE VOCABULARY IS OPEN, and this pair of cases is why. content-planner.md §4 calls its role
# list "a *vocabulary*, not a straitjacket: a lecture, a defense and a status deck use different
# mixes" — so a hard refusal here would BLOCK a planner following its own instructions. The first
# version of this file did exactly that.
rc, out = _run([dict(HEALTHY[0], roles=["problem", "demo", "evidence"]), HEALTHY[1]])
want(rc == 0 and "demo" in out,
     "a role outside the documented list is ACCEPTED and merely reported — the skill's own text "
     "calls that vocabulary open, and a gate that contradicts the agent brief it enforces is a "
     "wall, not a check",
     "an undocumented role was refused, contradicting content-planner.md (rc=%d):\n%s"
     % (rc, out[:300]))

rc, out = _run([dict(HEALTHY[0], roles=["problem", "case study", "framework/idea"]), HEALTHY[1]])
want(rc == 0 and "[note]" not in out,
     "`case study` and `framework/idea` — the exact spellings content-planner.md prints, with a "
     "space and a slash — normalise onto the documented roles instead of reading as unknown",
     "the documented spelling was not recognised (rc=%d):\n%s" % (rc, out[:300]))

rc, out = _run([dict(HEALTHY[0], closing_ask=""), HEALTHY[1]])
want(rc == 1 and "closing_ask" in out,
     "a missing closing ask is refused — an arc that cannot name what it asks for has not been "
     "thought through as an argument",
     "an arc with no closing ask was accepted (rc=%d):\n%s" % (rc, out[:300]))

rc, out = _run([HEALTHY[0], dict(HEALTHY[1], name="contribution")])
want(rc == 1 and "share a name" in out,
     "two candidates with one name are refused (the report keys on names)",
     "duplicate candidate names were accepted (rc=%d):\n%s" % (rc, out[:300]))

# ----------------------------------------------------------------- the empty-ledger hole
# The effort check compares each candidate against the LARGEST. When no candidate names any
# evidence the largest is zero, every comparison is vacuously fine, and the check reported a clean
# set — deciding nothing on the one input where nothing had been decided. Its own fault now.
rc, out = _run([dict(HEALTHY[0], evidence=[]), dict(HEALTHY[1], evidence=[])])
want(rc == 2 and "NO CANDIDATE NAMES ITS EVIDENCE" in out,
     "a candidate set where NO arc names its evidence is refused — the effort check used to pass "
     "it silently, because a relative comparison against zero is vacuously satisfied",
     "an evidence-less candidate set passed (rc=%d):\n%s" % (rc, out[:300]))
rc, out = _run([dict(HEALTHY[0], evidence=["c1", "c2"]), dict(HEALTHY[1], evidence=["c3", "c4"])])
want(rc == 0,
     "…and equally-developed candidates still pass, so the new fault is about the ledger being "
     "absent, not about the counts differing",
     "a healthy equal-evidence set was caught by the empty-ledger rule (rc=%d):\n%s"
     % (rc, out[:300]))

# ----------------------------------------------------------------- the skeleton is usable
tmpl = subprocess.run([sys.executable, str(SCRIPTS / "arc_divergence.py"), "--template"],
                      capture_output=True, text=True)
want(tmpl.returncode == 0 and json.loads(tmpl.stdout),
     "--template prints parseable JSON — a field list that lives only in a docstring is a field "
     "list nobody reads, and this repo has already printed a raw format string onto a slide for "
     "exactly that reason",
     "--template did not print usable JSON: %r" % tmpl.stdout[:200])
rc, out = _run(json.loads(tmpl.stdout))
want(rc == 0,
     "…and the skeleton PASSES its own checker: a template that models a strawman (or a collapse) "
     "would teach one to every planner that fills it in",
     "the printed skeleton fails the checker it is a skeleton for (rc=%d):\n%s" % (rc, out[:300]))
want("shape" in tmpl.stderr and "roles" in tmpl.stderr,
     "…and the vocabularies are printed beside it, so filling the skeleton needs no second lookup",
     "--template does not print the vocabularies")

# ----------------------------------------------------------------- measurement contracts
want(A._overlap("", "anything at all") == 0.0,
     "an empty field scores 0.0 similarity, not 1.0 — an unfilled field is not evidence that two "
     "arcs agree, and treating it as a match would flag every under-filled candidate",
     "an empty field counts as a match")

short = A._pair(A._features(_arc("s", "scqa", ["problem", "evidence"], "q", "o", "a", ["c1"])),
                A._features(_arc("l", "scqa", ["problem", "evidence", "conclusion", "roadmap"],
                                 "q2", "o2", "a2", ["c1"])))
want("order" in short["matched_axes"],
     "openings are compared over the SHORTER arc's length — a 2-beat and a 4-beat arc opening "
     "identically match on order rather than diverging because one is longer",
     "the order axis missed an identical opening of unequal lengths: %s" % short["matched_axes"])

mixed = A._tokens("接受INR骨干")
want("受骨" not in mixed and "接受" in mixed and "骨干" in mixed,
     "bigrams stop at a Latin island — an earlier version filtered CJK out of the whole letter run "
     "and welded 受 to 骨, inventing a token that appears nowhere in the text and inflating the "
     "similarity of any two mixed-script strings that share a Latin term",
     "phantom cross-island bigram present: %r" % sorted(t for t in mixed if len(t) == 2))

nz = A._overlap("接受隐式神经表示作为重建骨干", "批准一个为期六个月的临床试点")
want(nz < A.OVERLAP_T,
     "two unrelated Chinese asks score below the threshold (%.2f) — the tokeniser separates, it "
     "does not just match everything CJK" % nz,
     "unrelated Chinese asks scored %.2f, at or above the %.2f threshold" % (nz, A.OVERLAP_T))

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print("\n%d passed, %d failed" % (len(ok), len(bad)))
raise SystemExit(1 if bad else 0)
