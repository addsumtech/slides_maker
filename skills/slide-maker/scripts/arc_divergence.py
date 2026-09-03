#!/usr/bin/env python3
"""Mechanical DIVERGENCE check for narrative-arc candidates — the content-side anti-theater gate.

The design side has had a competition for a while: the direction gate shows 2-4 rendered
directions and `directions_diversity.py` measures, deterministically, whether they actually
differ. The content side has had nothing. The arc was DERIVED — primary goal maps to arc shape
(inform -> build to the evidence, decide -> recommendation first, inspire -> stakes then ask) —
and the planner then recorded "which arc I chose and why". A derivation is not a choice: the
reason is written after the fact, against no alternative, and nothing anywhere reports that the
runner-up never existed. Choosing the wrong arc is the most expensive rework class in the whole
pipeline, because it invalidates the design plan and the build underneath it, not just a slide.

So the planner now produces 2-3 arcs over the SAME evidence ledger and this script checks them.
It is deliberately the same shape as `directions_diversity.py` — same >=3-of-4 rule, same
never-auto-kill response, same "record the justification on the gate line" escape — because the
failure being prevented is the same one: **one mind writing a set of candidates and then judging
its own set.**

But the failure MODE differs, and that is why there are two checks rather than one. Directions
collapse into three colourways of one layout: the candidates are equally developed and equally
shallow. Arcs collapse differently — into **one real arc plus two strawmen**, where the losers are
not similar to the winner, they are just thinner than it. A divergence check alone scores that as
a healthy set, because a two-beat sketch diverges beautifully from a twelve-beat argument. Hence:

  DIVERGENCE   are the candidates different stories?      (per pair, 4 axes, >=3 matched = flagged)
  EFFORT       are the losers real candidates, or sketches? (evidence coverage vs the largest)

The four divergence axes, chosen so no perceptual difference is counted twice (the lesson
`directions_diversity.py` records when it folded `mode` into `palette`):

  shape    the arc archetype itself — the loudest single signal
  order    the first three CONTENT roles. Where the claim sits relative to its evidence is decided
           in the opening third; two arcs that open problem->method->evidence tell the same story
           however they end. The opening role is NOT a separate axis: it is roles[0], already here.
  ask      the closing ask — what the room is asked to do or believe. Two arcs arguing for the
           same thing are one arc with two decorations.
  stance   the audience question AND the pre-empted objection. Matched only when BOTH read the
           same, deliberately conservative: arguing against the same objection from a different
           question is a real alternative.

Text fields are compared by token overlap, and the tokeniser is CJK-aware ON PURPOSE. Splitting
on whitespace scores two Chinese closing asks as 0.0 similar no matter what they say, which would
silently disable the `ask` and `stance` axes on every Chinese deck — the same class of bug as
measuring Chinese glyph widths with Latin metrics. CJK runs are compared as character bigrams.

The overlap threshold is a COARSE signal and is treated as one: the response to a flag is never a
kill, it is REDIVERGE-or-justify, and the justification is recorded on the `arc gate:` line of the
content checkpoint. A false flag therefore costs one sentence; a missed collapse costs a rebuild.

CLI:  python3 arc_divergence.py --template          # a fillable skeleton + the vocabularies
      python3 arc_divergence.py arcs.json [--json]
Exit: 0 = candidates diverge and none is a sketch · 2 = flagged (printed) · 1 = unreadable input.
"""
import argparse
import itertools
import json
import re
import sys

OVERLAP_T = 0.60        # token-overlap at or above which two free-text fields "read the same"
EFFORT_T = 0.50         # a candidate carrying under this share of the largest one's evidence

# Kept in lockstep with `agents/content-planner.md` §3 ON PURPOSE — the same reason
# directions_diversity.py pins its cover/skeleton vocabulary: a typo that passes HERE would earn a
# divergence credit for a shape that does not exist, and only fail later (or never).
_SHAPES = (
    "evidence-build",        # inform & educate — build to the evidence, then explain
    "recommendation-first",  # support a decision — lead with the ask, then justify
    "stakes-to-action",      # inspire / motivate — open on stakes, close on the call
    "scqa",                  # situation -> complication -> question -> answer
    "sparkline",             # alternate current-reality / future-state, one engineered peak
    "problem-turn-evidence",  # the turn is the spine: what broke, what changed, what proves it
    "contribution-first",    # the research claim up front, the work as its support
    "chronological",         # the story in the order it happened
    "survey",                # a landscape with no single climax
    # --- the RESEARCH PIVOT ---------------------------------------------------------------
    # The commonest lab-meeting deck there is — "here is what we built, here is what it showed,
    # here is why we are changing approach" — had no shape, so it was filed as
    # `problem-turn-evidence`. That mislabel is not cosmetic: in problem-turn-evidence the
    # evidence proves the NEW thing, and a planner following it puts the results after the turn.
    # In a pivot the evidence belongs to the approach being RETIRED and the new one has none yet,
    # so the order inverts and the deck must end on STATUS rather than proof. Measured: a real
    # progress deck placed the prior work's result pages after the pivot and had to be reordered
    # by the user, and a later edit deleted the status page without anything noticing.
    "method-pivot",          # what we built & why -> what it showed -> where it stopped -> what replaces it -> what is not yet known
    # --- INSTRUCTIONAL shapes ---------------------------------------------------------------
    # The nine above are all shapes of an ARGUMENT or a REPORT, and the closed list therefore
    # refused a lecture outright: `concept-example-check` and `misconception-first` were rejected
    # at read time, so a teaching deck had to relabel itself `evidence-build` or `chronological`
    # to get through the gate — and the `arc gate:` line then recorded a shape the deck was not.
    # That is not a niche: `design-by-purpose.md` prescribes a "concept -> example -> check"
    # rhythm for Teaching/lecture by name, and the skill's own description lists teaching as a
    # first-class purpose. The design side named a structure the content vocabulary could not.
    "concept-example-check",  # teach — state the idea, work an example, check understanding
    "misconception-first",    # teach — open on what the room already believes wrongly, break it
    "worked-example",         # teach — one problem solved end-to-end, the theory falls out of it
    "prerequisite-chain",     # teach — build strictly on what was established one beat earlier
    "spiral",                 # teach — the same idea three times at increasing depth
)

# Shapes whose "objection" is a learner's MISCONCEPTION and whose "closing_ask" is a capability
# ("you can now predict when aliasing appears"), not a decision. The fields keep their names —
# renaming them per shape would fork the record format — but the report says which reading applies,
# so a planner filling them for a lecture is not being asked to invent a boardroom objection.
_TEACHING_SHAPES = frozenset((
    "concept-example-check", "misconception-first", "worked-example",
    "prerequisite-chain", "spiral",
))

# The role vocabulary of `agents/content-planner.md` §3, plus the structural rows that are excluded
# from the order axis (a cover is not a beat in the argument).
#
# 🔴 THIS LIST IS OPEN, and that is not laziness — content-planner.md calls it "a *vocabulary*, not
# a straitjacket: a lecture, a defense and a status deck use different mixes". An earlier version
# RAISED on anything outside it, so a planner following its own instructions could be hard-blocked
# for writing `demo` or `context`. Unrecognised roles are accepted as opaque tokens and compared by
# equality like any other, so an open vocabulary costs exactly this: two different typos of one role
# read as divergent rather than identical — a mild false-negative on ONE of four axes, against a
# wall. They are printed in the report, so a typo is visible rather than silent.
# `framework-idea` is the normalised form of content-planner.md's own "framework/idea", and it is
# listed BESIDE the two halves rather than instead of them: a planner may write either the joint
# role or one side of it, and neither spelling should read as undocumented.
_ROLES = ("hook", "problem", "diagnosis", "framework", "idea", "framework-idea", "method",
          "evidence", "case-study", "comparison", "roadmap", "conclusion", "call-to-action",
          # Instructional roles. The list is open, so these were always *accepted* — but an
          # undocumented role is one nobody reaches for, and a lecture's beats were nowhere in
          # the vocabulary a planner reads. `design-by-purpose.md` already asks Teaching decks
          # for an objectives slide, a concept -> example -> check rhythm and a recap; these are
          # the names for those beats.
          "objective", "prerequisite", "concept", "worked-example", "misconception",
          "counterexample", "practice", "check", "recap")
_STRUCTURAL = ("cover", "agenda", "divider", "closing", "section", "thanks", "qa")

_CJK_CLASS = "぀-ヿ㐀-䶿一-鿿豈-﫿가-힯"
_CJK = re.compile("[" + _CJK_CLASS + "]")
_CJK_RUN = re.compile("[" + _CJK_CLASS + "]+")


def _norm_role(r):
    """`case study` / `Case Study` / `framework/idea` all normalise to one token.

    content-planner.md writes the vocabulary with SPACES and a SLASH ("case study",
    "framework/idea"). Matching those literally against a hyphenated tuple rejected the exact
    spelling the agent is told to use. Two files have to agree about a name; here is the cheap
    place to make them agree.
    """
    return re.sub(r"[\s/_]+", "-", str(r or "").strip().lower())


def _tokens(s):
    """Tokenise for overlap. Latin words by whitespace; CJK runs by character bigram.

    A whitespace split on '让评审委员会接受这个方法' yields ONE token, so every pair of Chinese
    asks scores either 1.0 (identical string) or 0.0 (anything else) — an axis that is on paper
    and off in practice. Bigrams give the same graded signal Latin text gets.

    Bigrams are taken PER CONTIGUOUS CJK RUN, never across a Latin island. An earlier version
    collected the whole letter run '接受INR骨干' and filtered the CJK out of it, which welded 受 to
    骨 and produced the bigram '受骨' — a token appearing nowhere in the text. Two mixed strings
    sharing only a Latin term would then also share phantom bigrams and score more similar than
    they are, on exactly the CJK path this function exists to get right.
    """
    s = (s or "").strip().lower()
    if not s:
        return set()
    out = set()
    for w in re.findall(r"[a-z0-9][a-z0-9\-']*", s):
        if len(w) > 1:
            out.add(w)
    for cjk in _CJK_RUN.findall(s):
        if len(cjk) == 1:
            out.add(cjk)
        for i in range(len(cjk) - 1):
            out.add(cjk[i:i + 2])
    return out


def _overlap(a, b):
    """Jaccard over the token sets. 0.0 when either side is empty — an unfilled field is not
    evidence of similarity, and treating it as a match would flag every under-filled candidate."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / float(len(ta | tb))


def _checked(d, key, allowed):
    v = d.get(key)
    if v not in allowed:
        raise ValueError("arc {!r}: {} must be one of {}, got {!r}".format(
            d.get("name", "?"), key, list(allowed), v))
    return v


def _content_roles(d):
    roles = d.get("roles") or []
    if not isinstance(roles, list) or not roles:
        raise ValueError("arc {!r}: `roles` must be a non-empty list of beat roles".format(
            d.get("name", "?")))
    out, unknown = [], []
    for r in roles:
        r = _norm_role(r)
        if not r or r in _STRUCTURAL:
            continue
        if r not in _ROLES:
            unknown.append(r)
        out.append(r)
    if not out:
        raise ValueError("arc {!r}: every role is structural — an arc needs beats".format(
            d.get("name", "?")))
    return out, unknown


def _required_text(d, key):
    v = str(d.get(key) or "").strip()
    if not v:
        raise ValueError(
            "arc {!r}: `{}` is required. An arc that does not name it has not been thought "
            "through as an argument.".format(d.get("name", "?"), key))
    return v


def _features(d):
    roles, unknown = _content_roles(d)
    ev = d.get("evidence") or []
    if not isinstance(ev, list):
        raise ValueError("arc {!r}: `evidence` must be a list of claim-ledger ids".format(
            d.get("name", "?")))
    return {
        "name": str(d.get("name") or "?"),
        "shape": _checked(d, "shape", _SHAPES),
        "roles": roles,
        "unknown_roles": unknown,
        "opening": tuple(roles[:3]),
        "ask": _required_text(d, "closing_ask"),
        "question": _required_text(d, "audience_question"),
        "objection": _required_text(d, "objection"),
        # 🔴 HOW THIS CANDIDATE SERVES THE RECORDED `interview.goal`. Required, because the axis
        # this competition kept being decided on was elegance. Measured: a deck whose recorded
        # goal was "they leave able to plan a trip" picked its arc because "it is the only
        # candidate whose organising idea also does the organising work … nothing is easier to
        # remember a week later", and rejected the practical candidate for becoming "the same
        # list every travel site gives me" — which, for someone planning a trip, is the
        # deliverable. The goal was in the record the whole time and was never used to score.
        "serves_goal": _required_text(d, "serves_goal"),
        "evidence": {str(x) for x in ev},
    }


def _pair(a, b):
    ask = _overlap(a["ask"], b["ask"])
    q = _overlap(a["question"], b["question"])
    obj = _overlap(a["objection"], b["objection"])
    # Compare the opening on the SHORTER arc's length so a 2-beat and a 5-beat candidate that open
    # identically are not scored as divergent purely because one of them is longer.
    n = min(len(a["opening"]), len(b["opening"]))
    axes = {
        "shape": a["shape"] == b["shape"],
        "order": n > 0 and a["opening"][:n] == b["opening"][:n],
        "ask": ask >= OVERLAP_T,
        "stance": q >= OVERLAP_T and obj >= OVERLAP_T,
    }
    matched = [k for k, v in axes.items() if v]
    return {"a": a["name"], "b": b["name"], "matched_axes": matched,
            "too_similar": len(matched) >= 3,
            "ask_overlap": round(ask, 2), "question_overlap": round(q, 2),
            "objection_overlap": round(obj, 2),
            "a_opening": "->".join(a["opening"]), "b_opening": "->".join(b["opening"])}


def check(arcs):
    feats = [_features(d) for d in arcs]
    names = [f["name"] for f in feats]
    if len(set(names)) != len(names):
        raise ValueError("two candidates share a name: {}".format(names))
    pairs = [_pair(x, y) for x, y in itertools.combinations(feats, 2)]
    # Three candidates that serve the goal in the same words are one candidate. This is the
    # goal-side twin of the stance check: it catches the set where `serves_goal` was filled in
    # afterwards, from the same sentence, to satisfy the field.
    same_goal = [{"a": x["name"], "b": y["name"], "overlap": round(_overlap(x["serves_goal"],
                                                                           y["serves_goal"]), 2)}
                 for x, y in itertools.combinations(feats, 2)
                 if _overlap(x["serves_goal"], y["serves_goal"]) >= OVERLAP_T]
    top = max((len(f["evidence"]) for f in feats), default=0)
    # A candidate nobody bothered to develop is not an alternative, it is a foil. This is the arc
    # equivalent of directions_diversity's no-bespoke check, and it catches the collapse a pure
    # divergence measure scores as healthy: a two-beat sketch diverges wonderfully from a real arc.
    sketches = [{"name": f["name"], "evidence": len(f["evidence"]), "top": top}
                for f in feats
                if top and len(f["evidence"]) < EFFORT_T * top]
    # `top == 0` means NOT ONE candidate named the evidence it carries. The comparison above is
    # relative, so that case produced an empty `sketches` list and a clean exit — the effort check
    # silently deciding nothing on the one input where nothing was decided. It is its own fault
    # now: without ledger ids the whole competition is three assertions about the same unexamined
    # material, which is the state this gate exists to end.
    no_ledger = not top
    return {"pairs": pairs, "flagged": [p for p in pairs if p["too_similar"]],
            "sketches": sketches, "count": len(feats), "no_ledger": no_ledger,
            "same_goal": same_goal,
            "unknown_roles": sorted({r for f in feats for r in f["unknown_roles"]}),
            "shapes": {f["name"]: f["shape"] for f in feats},
            "evidence": {f["name"]: len(f["evidence"]) for f in feats}}


TEMPLATE = [
    {"name": "<label-A>",
     "shape": "contribution-first",
     "roles": ["problem", "method", "evidence", "comparison", "conclusion"],
     "audience_question": "<the question this room is actually asking>",
     "serves_goal": "<how THIS arc serves the recorded interview.goal — not why it is elegant>",
     "objection": "<the objection this arc pre-empts>",
     "closing_ask": "<what the room should do or believe>",
     "evidence": ["<claim-ledger id>", "<claim-ledger id>"]},
    {"name": "<label-B>",
     "shape": "recommendation-first",
     "roles": ["conclusion", "evidence", "roadmap", "call-to-action"],
     "audience_question": "<a DIFFERENT question>",
     "serves_goal": "<a DIFFERENT way of serving the SAME goal>",
     "objection": "<a DIFFERENT objection>",
     "closing_ask": "<a DIFFERENT ask>",
     # Comparable depth on purpose: a candidate carrying under half the winner's evidence is
     # reported as a strawman, and a skeleton that models a strawman teaches one.
     "evidence": ["<claim-ledger id>", "<claim-ledger id>"]},
]


def main():
    ap = argparse.ArgumentParser(description="mechanical narrative-arc candidate divergence check")
    ap.add_argument("arcs", nargs="?", help="JSON list of 2-3 candidate arc objects")
    ap.add_argument("--json", action="store_true", dest="as_json")
    # A fillable skeleton, because a field list that lives only in this file's docstring is a field
    # list nobody reads: this repo has already printed a raw format string onto a slide because a
    # parameter's dialect was documented in a docstring and nowhere the author was looking.
    ap.add_argument("--template", action="store_true",
                    help="print a fillable candidate-set skeleton and exit")
    a = ap.parse_args()
    if a.template:
        print(json.dumps(TEMPLATE, indent=2, ensure_ascii=False))
        arg = [s for s in _SHAPES if s not in _TEACHING_SHAPES]
        print("\n# shapes (argue/report): " + " | ".join(arg), file=sys.stderr)
        print("# shapes (teach):        " + " | ".join(sorted(_TEACHING_SHAPES)), file=sys.stderr)
        print("#   on a TEACH shape, read two fields differently: `objection` is the learner's "
              "MISCONCEPTION,\n#   and `closing_ask` is the CAPABILITY they leave with "
              "(\"you can predict when aliasing appears\"),\n#   not a decision the room makes. "
              "The field names stay the same so the record format does not fork.",
              file=sys.stderr)
        print("# roles:  " + " | ".join(_ROLES) + "   (open list — others are accepted)",
              file=sys.stderr)
        print("# structural roles are ignored by the order axis: " + " | ".join(_STRUCTURAL),
              file=sys.stderr)
        return 0
    if not a.arcs:
        ap.error("give a candidates JSON file, or --template to print a skeleton")
    try:
        with open(a.arcs, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or len(data) < 2:
            raise ValueError("expected a JSON list of 2+ candidate arcs — one arc is a derivation, "
                             "not a choice")
        r = check(data)
    except Exception as e:                                        # noqa: BLE001
        print("[arcs] could not read candidates: {}".format(e))
        sys.exit(1)
    bad = bool(r["flagged"] or r["sketches"] or r["no_ledger"] or r["same_goal"])
    if a.as_json:
        print(json.dumps(r, indent=1, ensure_ascii=False))
        sys.exit(2 if bad else 0)

    for p in r["pairs"]:
        mark = "x TOO SIMILAR" if p["too_similar"] else "v"
        print("  {}  {} vs {}: opening {} vs {} · ask {} · stance {}/{} · matched: {}".format(
            mark, p["a"], p["b"], p["a_opening"], p["b_opening"], p["ask_overlap"],
            p["question_overlap"], p["objection_overlap"],
            ", ".join(p["matched_axes"]) or "none"))
    print("  shapes: " + " · ".join("{}={}".format(k, v) for k, v in r["shapes"].items()))
    print("  evidence carried: " + " · ".join(
        "{}={}".format(k, v) for k, v in r["evidence"].items()))

    if r["flagged"]:
        involved = sorted({n for p in r["flagged"] for n in (p["a"], p["b"])})
        print("[arcs]     {} pair(s) tell the SAME story in different words (involving: {}).".format(
            len(r["flagged"]), ", ".join(involved)))
        print("           REDIVERGE them, or keep the pair and record why on the `arc gate:` line")
        print("           of the content checkpoint. Real divergence moves the CLAIM, not the")
        print("           wording: put the evidence before the claim instead of after it, argue to")
        print("           a different ask, or pre-empt a different objection.")
    if r["sketches"]:
        print("[effort]   x STRAWMAN CANDIDATE(S): {}".format(", ".join(
            "{} carries {} evidence units vs {}".format(s["name"], s["evidence"], s["top"])
            for s in r["sketches"])))
        print("           A candidate nobody developed is a foil, not an alternative — the winner")
        print("           beat nothing. Build it out over the same ledger, or drop it and say so.")
        print("           ESCAPE: a decision arc legitimately carries less evidence than a")
        print("           contribution arc. If that is the case here, keep it and record the")
        print("           reason on the `arc gate:` line.")
    if r["same_goal"]:
        print("[goal]     x candidates that serve the goal in the SAME words: "
              + " · ".join("{} vs {} ({:.2f})".format(g["a"], g["b"], g["overlap"])
                           for g in r["same_goal"]))
        print("           `serves_goal` filled from one sentence is the field being satisfied, "
              "not the competition being run. Say how EACH arc gets this room to the recorded\n"
              "           goal by a different route — or drop the one that has no distinct route.")
    if r["no_ledger"]:
        print("[effort]   x NO CANDIDATE NAMES ITS EVIDENCE. Every `evidence` list is empty, so the")
        print("           effort comparison has nothing to compare and the competition is three")
        print("           assertions about material nobody linked to the claim ledger. Put the")
        print("           ledger ids each arc actually carries on each candidate — which evidence")
        print("           an arc leaves on the floor is most of what distinguishes it.")
    if r["unknown_roles"]:
        # Not a failure: content-planner.md calls the role list "a vocabulary, not a straitjacket".
        # Printed so a TYPO is visible — an unrecognised role still compares by equality, so
        # `problm` vs `problem` reads as divergent and quietly weakens the order axis.
        print("[note]     roles outside the documented vocabulary: {}. Accepted (the list is open "
              "by design) — check none of them is a typo of a documented role, which would read as "
              "divergence.".format(", ".join(r["unknown_roles"])))
    if not bad:
        print("[arcs]     v {} candidates, all developed, none a rewording of another.".format(
            r["count"]))
    sys.exit(2 if bad else 0)


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    main()
