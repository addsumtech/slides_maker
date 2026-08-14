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

CLI:  python arc_divergence.py arcs.json [--json]
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
)

# The role vocabulary of `agents/content-planner.md` §3, plus the structural rows that are excluded
# from the order axis (a cover is not a beat in the argument).
_ROLES = ("hook", "problem", "diagnosis", "framework", "idea", "method", "evidence",
          "case-study", "comparison", "roadmap", "conclusion", "call-to-action")
_STRUCTURAL = ("cover", "agenda", "divider", "closing", "section", "thanks", "qa")

_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿豈-﫿가-힯]")


def _tokens(s):
    """Tokenise for overlap. Latin words by whitespace; CJK runs by character bigram.

    A whitespace split on '让评审委员会接受这个方法' yields ONE token, so every pair of Chinese
    asks scores either 1.0 (identical string) or 0.0 (anything else) — an axis that is on paper
    and off in practice. Bigrams give the same graded signal Latin text gets.
    """
    s = (s or "").strip().lower()
    if not s:
        return set()
    out = set()
    # Latin/numeric words, with CJK stripped out so a mixed string contributes both ways.
    for w in re.findall(r"[a-z0-9][a-z0-9\-']*", s):
        if len(w) > 1:
            out.add(w)
    for run in re.findall(r"[^\W\d_]+", s, flags=re.UNICODE):
        if not _CJK.search(run):
            continue
        cjk = "".join(ch for ch in run if _CJK.match(ch))
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
    out = []
    for r in roles:
        r = str(r).strip().lower()
        if r in _STRUCTURAL:
            continue
        if r not in _ROLES:
            raise ValueError("arc {!r}: unknown role {!r}. Vocabulary: {}".format(
                d.get("name", "?"), r, ", ".join(_ROLES + _STRUCTURAL)))
        out.append(r)
    if not out:
        raise ValueError("arc {!r}: every role is structural — an arc needs beats".format(
            d.get("name", "?")))
    return out


def _required_text(d, key):
    v = str(d.get(key) or "").strip()
    if not v:
        raise ValueError(
            "arc {!r}: `{}` is required. An arc that does not name it has not been thought "
            "through as an argument.".format(d.get("name", "?"), key))
    return v


def _features(d):
    roles = _content_roles(d)
    ev = d.get("evidence") or []
    if not isinstance(ev, list):
        raise ValueError("arc {!r}: `evidence` must be a list of claim-ledger ids".format(
            d.get("name", "?")))
    return {
        "name": str(d.get("name") or "?"),
        "shape": _checked(d, "shape", _SHAPES),
        "roles": roles,
        "opening": tuple(roles[:3]),
        "ask": _required_text(d, "closing_ask"),
        "question": _required_text(d, "audience_question"),
        "objection": _required_text(d, "objection"),
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
    top = max((len(f["evidence"]) for f in feats), default=0)
    # A candidate nobody bothered to develop is not an alternative, it is a foil. This is the arc
    # equivalent of directions_diversity's no-bespoke check, and it catches the collapse a pure
    # divergence measure scores as healthy: a two-beat sketch diverges wonderfully from a real arc.
    sketches = [{"name": f["name"], "evidence": len(f["evidence"]), "top": top}
                for f in feats
                if top and len(f["evidence"]) < EFFORT_T * top]
    return {"pairs": pairs, "flagged": [p for p in pairs if p["too_similar"]],
            "sketches": sketches, "count": len(feats),
            "shapes": {f["name"]: f["shape"] for f in feats},
            "evidence": {f["name"]: len(f["evidence"]) for f in feats}}


def main():
    ap = argparse.ArgumentParser(description="mechanical narrative-arc candidate divergence check")
    ap.add_argument("arcs", help="JSON list of 2-3 candidate arc objects")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()
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
    if a.as_json:
        print(json.dumps(r, indent=1, ensure_ascii=False))
        sys.exit(2 if (r["flagged"] or r["sketches"]) else 0)

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
    if not r["flagged"] and not r["sketches"]:
        print("[arcs]     v {} candidates, all developed, none a rewording of another.".format(
            r["count"]))
    sys.exit(2 if (r["flagged"] or r["sketches"]) else 0)


if __name__ == "__main__":
    main()
