#!/usr/bin/env python3
"""The clinical / evidence-synthesis forms: the numbers, the guards, and the routing.

These components exist because `design-by-topic.md` listed "Medicine / biotech / clinical" as a
first-class domain while a grep for kaplan-meier / forest / CONSORT / Bland-Altman / ROC across
references + scripts + agents returned nothing: the skill could STYLE a clinical deck and could
not DRAW one.

Each component owns a rule that is wrong BY DEFAULT when the form is hand-rolled, and a wrong
chart is a perfectly well-formed set of shapes — no geometry lint can see one. So this suite
checks three things and not just that the code runs:

  1. the ESTIMATORS against hand-computable answers (a KM ladder, a published AUC, an SD)
  2. every GUARD in both directions — the bad input raises, the good input does not
  3. the ROUTING — a form nobody is pointed at is a form nobody picks

Run: python3 tests/test_clinical_forms.py
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import os
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import matplotlib                                                          # noqa: E402
matplotlib.use("Agg")

import deckkit as dk                                                       # noqa: E402
import designed_charts as dc                                               # noqa: E402

OK, BAD = [], []
TMP = tempfile.mkdtemp()


def ck(cond, msg):
    (OK if cond else BAD).append(msg)
    print(("  ok   " if cond else "  ✗    ") + msg)


def raises(fn, needle, msg):
    try:
        fn()
    except Exception as exc:                       # noqa: BLE001 - any refusal is the point
        got = str(exc)
        ck(needle.lower() in got.lower(),
           msg + (" (message: %s…)" % got[:70] if needle.lower() in got.lower()
                  else " — raised, but the message did not mention %r: %s" % (needle, got[:90])))
        return
    ck(False, msg + " — it did NOT raise")


def out(name):
    return os.path.join(TMP, name)


print("— consort_flow: the arithmetic is the point")
raises(lambda: dk.consort_flow(dk.add_slide(dk.blank_deck()), 0.6, 1.2, 8.8, 3.8, [
           ("Assessed", 250, [("Ineligible", 40), ("Declined", 12)]),
           ("Randomised", 190, []), ("Analysed", 190, [])]),
       "does not balance",
       "a flow losing 8 people between two boxes is REFUSED")
raises(lambda: dk.consort_flow(dk.add_slide(dk.blank_deck()), 0.6, 1.2, 8.8, 3.8, [
           ("Assessed", 250, [("Ineligible", 40), ("Declined", 12)]),
           ("Randomised", 190, []), ("Analysed", 190, [])]),
       "198",
       "…and the refusal SPELLS OUT the sum it expected")
_prs = dk.blank_deck(); _s = dk.add_slide(_prs)
dk.consort_flow(_s, 0.55, 1.05, 8.9, 3.95, [
    ("Assessed for eligibility", 250, [("Did not meet criteria", 40), ("Declined", 12)]),
    ("Randomised", 198, [("Lost to follow-up", 9), ("Withdrew consent", 5)]),
    ("Analysed", 184, [])])
ck(True, "a balanced flow builds")
dk.lint_layout(_prs, strict=True)
ck(True, "…and passes the build-time geometry lint")
raises(lambda: dk.consort_flow(dk.add_slide(dk.blank_deck()), 0.6, 1.2, 8.8, 1.0,
                               [("a", 5, [])] * 4),
       "do not fit", "a stack too tall for its region is refused, not squashed")
raises(lambda: dk.consort_flow(dk.add_slide(dk.blank_deck()), 0.6, 1.2, 8.8, 3.8,
                               [("a", -1, []), ("b", -1, [])]),
       "negative", "a negative count is refused")

print("\n— km_curve: the estimator, against a hand-computed ladder")
times = [6, 6, 6, 7, 10, 13, 16, 22, 23]
events = [1, 1, 1, 1, 0, 1, 1, 1, 1]
dc.km_curve(out("km.png"), [("arm", times, events)], risk_table=True)
ck(os.path.exists(out("km.png")), "a KM curve renders from RAW (times, events)")
# 🔴 The REAL estimator, compared by exact list — never a re-implementation in the test. This arm
# used to rebuild the estimator here and compare THAT to the textbook, so it never saw what
# km_curve drew; and it compared with zip(), which passes an empty ladder.
_ts, _sv, _cens = dc._km_steps(times, events)
ladder = [(t, round(v, 4)) for t, v in zip(_ts[1:], _sv[1:])]
want = [(6, 0.6667), (7, 0.5556), (13, 0.4167), (16, 0.2778), (22, 0.1389), (23, 0.0)]
ck(ladder == want, "the Kaplan–Meier ladder matches the textbook series exactly: %s" % ladder)
ck(_ts[0] == 0.0 and _sv[0] == 1.0 and len(_cens) == 1 and _cens[0][0] == 10
   and abs(_cens[0][1] - 5 / 9) < 1e-9,
   "...starts at (0, 1), and the one censored subject is marked ON the curve at t=10 (%s)" % _cens)
ck(_ts.count(23) == 1, "...and when the last observation is an EVENT nothing is appended after it")

_ts, _sv, _cens = dc._km_steps([3, 5, 8, 12, 15, 20], [1, 1, 0, 1, 1, 0])
ck(_ts[-1] == 20 and abs(_sv[-1] - 2 / 9) < 1e-9 and abs(_sv[-2] - 2 / 9) < 1e-9,
   "🔴 a curve whose LAST subject is censored runs on to that follow-up (t=20, S=2/9) instead of "
   "ending in a bare vertical drop at the last event (got %s)" % list(zip(_ts, _sv))[-2:])
ck((20, _sv[-1]) in [(t, v) for t, v in _cens],
   "...so the final censor mark sits ON the line rather than floating after it")

_ts, _sv, _cens = dc._km_steps([4, 9, 12], [0, 0, 0])
ck(_ts == [0.0, 12] and _sv == [1.0, 1.0],
   "🔴 a group with NO events is a flat line at 1.0 out to its last follow-up — it used to be a "
   "single (0, 1) point, which draws nothing (got %s)" % list(zip(_ts, _sv)))
_ts, _sv, _cens = dc._km_steps([2, 5, 5], [1, 1, 0])
ck(_ts == [0.0, 2, 5] and abs(_sv[-1] - 1 / 3) < 1e-9 and _cens == [(5, _sv[-1])],
   "a tied event and censoring at the final time adds no extra step (got %s)" % list(zip(_ts, _sv)))

# …and what is DRAWN, read off the real figure, not inferred from the estimator
_figs = []
_real_save = dc._save
dc._save = lambda fig, path: (_figs.append(fig), _real_save(fig, path))[1]
try:
    dc.km_curve(out("km_tail.png"), [("Control", [3, 5, 8, 12, 15, 20], [1, 1, 0, 1, 1, 0]),
                                     ("Treated", [6, 9, 14, 18, 24, 30], [1, 0, 1, 0, 1, 0]),
                                     ("No events", [7, 11], [0, 0])])
finally:
    dc._save = _real_save
_ax = _figs[-1].axes[0]
_drawn = {ln.get_label(): list(ln.get_xdata()) for ln in _ax.lines if not ln.get_label().startswith("_")}
ck(_drawn.get("Control", [None])[-1] == 20 and _drawn.get("Treated", [None])[-1] == 30
   and _drawn.get("No events", [None])[-1] == 11,
   "the plotted lines end at each group's last follow-up — Control 20, Treated 30, No events 11 "
   "(drawn: %s)" % {k: v[-1] for k, v in _drawn.items()})
ck(_ax.get_xlim()[1] >= 30,
   "...and the x-range reaches the longest follow-up (30), not the last event (24): xlim %s"
   % (tuple(round(v, 2) for v in _ax.get_xlim()),))
raises(lambda: dc.km_curve(out("x.png"), [("a", [1, 2, 3], [1, 0])]),
       "aligned", "misaligned times/events are refused")
raises(lambda: dc.km_curve(out("x.png"), [("a", [1, 2], [1, 2])]),
       "0 or 1", "an event flag that is not 0/1 is refused")
raises(lambda: dc.km_curve(out("x.png"), [("a", [1, 2], [0.5, 0.9], "precomputed")]),
       "increases", "a precomputed curve that INCREASES is refused — survival cannot go up")

print("\n— forest_plot: the log axis and the interval guards")
raises(lambda: dc.forest_plot(out("x.png"), [("A", 1.4, 0.6, 1.1)]),
       "outside its interval", "a point estimate outside its own CI is refused")
raises(lambda: dc.forest_plot(out("x.png"), [("A", 0.8, -0.2, 1.1)]),
       "non-positive", "a non-positive bound on a LOG axis is refused")
dc.forest_plot(out("forest.png"), [("A", 0.82, 0.61, 1.10, 12), ("B", 0.74, 0.55, 0.99, 20)],
               summary=("Pooled", 0.78, 0.66, 0.92))
ck(os.path.exists(out("forest.png")), "a ratio forest plot with a pooled diamond renders")
dc.forest_plot(out("forest_d.png"), [("A", -2.4, -4.1, -0.7), ("B", -0.8, -2.9, 1.3)], null=0.0)
ck(os.path.exists(out("forest_d.png")),
   "a DIFFERENCE forest (null=0) renders — negatives are legal there, log defaults off")
raises(lambda: dc.forest_plot(out("x.png"), [("A", 0.8, 0.6, 1.1)],
                              summary=("P", 2.0, 0.6, 0.9)),
       "outside its own interval", "a summary outside its own interval is refused too")

print("\n— bland_altman: limits of agreement, not a correlation")
a = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
b = [10.5, 10.8, 12.4, 12.9, 14.6, 14.8, 16.7, 16.9, 18.5, 19.1]
d = [x - y for x, y in zip(a, b)]
bias, sd = statistics.mean(d), statistics.stdev(d)
dc.bland_altman(out("ba.png"), a, b, names=("MRI", "CT"))
ck(os.path.exists(out("ba.png")), "an agreement plot renders")
ck(abs(bias - (-0.22)) < 1e-9 and abs(sd - 0.35528) < 1e-4,
   "bias and SD match the hand computation (bias %+.4f, sd %.4f)" % (bias, sd))
raises(lambda: dc.bland_altman(out("x.png"), [1, 2, 3], [1, 2]),
       "same length", "unequal-length methods are refused — the pairs are per subject")
raises(lambda: dc.bland_altman(out("x.png"), [1, 2], [1, 2]),
       "at least 3", "two points cannot estimate an SD, and it says so")
raises(lambda: dc.bland_altman(out("x.png"), [1, -1, 2], [-1, 1, 2], percent=True),
       "zero", "percent mode refuses data whose pair mean crosses zero")

print("\n— roc_curve: a published AUC, and the binary guards")
dc.roc_curve(out("roc.png"), [("m", [0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])])
ck(os.path.exists(out("roc.png")), "an ROC renders from raw (y_true, y_score)")
y, sc = [0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]
P, N = sum(y), len(y) - sum(y)
order = sorted(range(len(sc)), key=lambda i: -sc[i])
tp = fp = 0; fpr = [0.0]; tpr = [0.0]; prev = None
for i in order:
    if prev is not None and sc[i] != prev:
        fpr.append(fp / N); tpr.append(tp / P)
    if y[i] == 1: tp += 1
    else: fp += 1
    prev = sc[i]
fpr.append(fp / N); tpr.append(tp / P)
auc = sum((x1 - x0) * (y0 + y1) / 2 for (x0, y0), (x1, y1)
          in zip(zip(fpr, tpr), zip(fpr[1:], tpr[1:])))
ck(abs(auc - 0.75) < 1e-9, "the AUC matches the published worked example exactly (%.4f)" % auc)
raises(lambda: dc.roc_curve(out("x.png"), [("m", [1, 1, 1], [0.1, 0.2, 0.3])]),
       "one class", "a single-class outcome is refused — ROC is undefined there")
raises(lambda: dc.roc_curve(out("x.png"), [("m", [0, 1, 2], [0.1, 0.2, 0.3])]),
       "0 or 1", "a non-binary label is refused")
raises(lambda: dc.roc_curve(out("x.png"), [("m", [0, 1], [1.4, 0.2], "precomputed")]),
       "outside [0, 1]", "a precomputed rate outside [0,1] is refused")

print("\n— routing: a form nobody is pointed at is a form nobody picks")
import component_audit as ca                                              # noqa: E402
ck("consort_flow" in ca.FORM_GUARANTEE,
   "component_audit names a guarantee for consort_flow — it draws on a slide, so a hand-rolled "
   "one is reportable")
import sigs as _sigs                                                      # noqa: E402
ck("consort_flow" in _sigs.EXAMPLES,
   "…and it carries the runnable scaffold every FORM_GUARANTEE entry owes (smoke_deckkit enforces "
   "FORM_GUARANTEE ⊆ EXAMPLES, and executes each scaffold against a real slide)")
for _name in ("forest_plot", "km_curve", "bland_altman", "roc_curve"):
    ck(_name in _sigs.EXAMPLES and "placeholder" in _sigs.EXAMPLES[_name]
       and _sigs._guarantee(_name),
       "%s has a RUNNABLE scaffold (smoke_deckkit executes it), says its numbers are placeholders, "
       "and states the guarantee a hand-roll loses — a recipe with no scaffold printed 'no copy-paste "
       "scaffold yet', and a form nobody can copy is a form that gets hand-rolled wrong" % _name)
ck(not ({"forest_plot", "km_curve", "bland_altman", "roc_curve"} & set(ca.FORM_GUARANTEE)),
   "the four PNG recipes are NOT in FORM_GUARANTEE — they write a file rather than drawing on a "
   "slide, exactly like waterfall/distribution/marimekko, so their backstop is the routing")
skill = open(os.path.join(SKILL, "SKILL.md")).read()
ck("clinical-evidence-figures.md" in skill,
   "SKILL.md routes to the clinical reference — layer 1 carries the trigger, which is what a "
   "non-Claude runtime reads")
for fname, why in (("references/form-selection.md", "the form is CHOSEN there"),
                   ("references/data-viz.md", "the chart type is chosen there"),
                   ("references/design-by-topic.md", "the domain is matched there")):
    txt = open(os.path.join(SKILL, fname)).read()
    ck("clinical-evidence-figures" in txt, "%s points at it — %s" % (fname, why))
ref = open(os.path.join(SKILL, "references/clinical-evidence-figures.md")).read()
ck("phylogenetic" in ref and "does NOT cover" in ref,
   "the reference states what it does NOT supply, rather than implying full coverage")
ck("heat_matrix" in ref,
   "…and routes the confusion matrix to the component that already exists, instead of adding one")

print()
print("%d passed, %d failed" % (len(OK), len(BAD)))
raise SystemExit(1 if BAD else 0)
