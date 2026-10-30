#!/usr/bin/env python3
"""What the skill decided ON THE USER'S BEHALF — recorded, sourced, and floored.

🔴 WHY THIS EXISTS. `references/checkpoint-convention.md` already states the rule precisely, with
its own measured failure: under "decide everything yourself" you ANSWER the Step-0 questions with
"defensible, purpose-derived picks" and post them as the FIRST FYI, "so a wrong pick costs one
glance to veto, not a build" — and **delegation covers preferences, never information only the user
has, and never which deck this is.** Measured: a run read a Chinese "you decide the rest" directive as licence to pick the ANGLE
too and delivered a thesis about 19th-century building regulation; every gate passed and it answered
a question nobody asked.

Nothing checked any of it. The FYI is prose in a chat; the record keeps `checkpoint.mode: auto` and
the picked VALUES, and from there a language the user stated and a language the skill invented are
byte-identical. So every downstream gate treats an INVENTED audience exactly like a given one, and
the hand-off has no way to say "these are the five things I decided for you".

WHAT THIS ADDS, and why it is a judgement lever rather than another field:

  basis        what IN THE REQUEST OR THE MATERIAL supports this pick. Not "I judged it" — being
               made to point at something turns a default into a reading of the actual input.
  alternative  on the three picks that decide everything downstream (audience · purpose ·
               template), what ELSE was plausible and why it lost. Every mechanism in this skill
               that demonstrably improves a decision works this way — the direction gate, the arc
               competition, the composition competition. A choice made against a named runner-up
               is a better choice than one made alone, and here it costs one sentence.

🔴 THE FLOOR, as a check rather than a paragraph. `angle` — which deck this actually is — may never
be `delegated`. A common genre carries a default the request already implies (「介绍巴黎的 PPT」 means
the city introduction people actually give), so it may be `genre-default`; it may be `stated`; it
may not be invented.

SCOPE. This binds only where the risk is: a deck whose checkpoints were delivered as `auto`. A deck
that ran a real interview records `stated` picks or nothing at all and is untouched.

    python3 scripts/delegated_picks.py --selftest

Exit 0 clean · 1 problems · 2 could not run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# The Step-0 decisions, named the way `checkpoint-convention.md` and the interview already name
# them. `audience` and `angle` are here because they are the two that decide everything downstream
# and neither was ever a recorded pick.
AXES = ("angle", "audience", "purpose", "template", "language", "goal", "density", "length",
        "style", "builds")

# Picks whose provenance changes what the record MEANS.
# 🔴 A LADDER, ORDERED BY DISTANCE FROM WHAT THE USER ACTUALLY SAID. The point is not to label a
# decision; it is to make the ones furthest from the user's own words the LOUDEST at hand-off.
#   stated               the user said it
#   genre-default        the request's genre already implies it (「介绍巴黎的 PPT」 → the city
#                        introduction people actually give)
#   inferred-from-request  the request does not say it, but something IN the request points at it
#   from-material        the source material settles it
#   not-applicable       this axis does not apply to this deck
#   delegated            nothing in the request or the material points at it — this is my
#                        preference, and it is the rung that must be shown first
SOURCES = ("stated", "genre-default", "inferred-from-request", "from-material", "not-applicable",
           "delegated")
# Ordered by how far the pick sits from the user's own words; the hand-off prints the far end first.
_DISTANCE = {s: i for i, s in enumerate(SOURCES)}

# 🔴 Never invented. See the module docstring for the deck this cost.
NEVER_DELEGATED = ("angle",)

# Where a named runner-up is worth the sentence: these three aim the research, the look and the
# whole build, and a wrong one is discovered at hand-off.
ALTERNATIVE_REQUIRED = ("audience", "purpose", "template")

MIN_BASIS = 16
MIN_ALT = 16


def _w(text) -> int:
    """Width, not codepoints — the same bar in Chinese as in English."""
    from written_reason import reason_width
    return reason_width(text)


def is_auto(gates) -> bool:
    """Did this deck deliver its checkpoints as FYIs rather than stops?

    Read from the record the gates already require, so nothing new has to be declared for this to
    know when it applies.
    """
    if not isinstance(gates, dict):
        return False
    for path in (("content", "checkpoint"), ("design_plan", "checkpoint"), ("design", "checkpoint")):
        node = gates
        for k in path:
            node = node.get(k) if isinstance(node, dict) else None
        if isinstance(node, dict) and str(node.get("mode") or "").strip().lower() == "auto":
            return True
    return False


def faults(interview, *, auto: bool) -> list[str]:
    """Everything wrong with the delegated-picks record. Empty list = clean.

    `auto=False` → nothing is required; a supervised deck's picks were the user's.
    """
    if not auto:
        return []
    if not isinstance(interview, dict):
        return [MISSING]
    picks = interview.get("picks")
    if not isinstance(picks, list) or not picks:
        return [MISSING]

    out: list[str] = []
    seen: dict[str, dict] = {}
    for i, p in enumerate(picks):
        if not isinstance(p, dict):
            out.append("`picks[{}]` must be an object.".format(i))
            continue
        axis = str(p.get("axis") or "").strip().lower()
        if axis not in AXES:
            out.append("`picks[{}].axis` is {!r} — it must be one of: {}."
                       .format(i, p.get("axis"), " · ".join(AXES)))
            continue
        if axis in seen:
            out.append("two picks both claim the `{}` axis.".format(axis))
            continue
        seen[axis] = p
        src = str(p.get("source") or "").strip().lower()
        if src not in SOURCES:
            out.append("`picks[{}]` ({}) needs a `source`: {}. This is the whole point — a value "
                       "the USER gave and a value the skill invented look identical once they are "
                       "in the record.".format(i, axis, " | ".join(SOURCES)))
            continue
        if src == "not-applicable":
            continue
        if _w(p.get("value")) < 2:
            out.append("`picks[{}]` ({}) has no `value`.".format(i, axis))
        if axis in NEVER_DELEGATED and src == "delegated":
            out.append("`{}` is marked `delegated`, and it may not be. Delegation covers "
                       "PREFERENCES — never information only the user has, and never WHICH DECK "
                       "THIS IS. A common genre carries a default the request already implies "
                       "(「介绍巴黎的 PPT」 means the city introduction people actually give): that "
                       "is `genre-default`, and it is a reading of the request, not an invention. "
                       "Measured: a run that invented the angle shipped a thesis on 19th-century "
                       "building regulation and passed every gate.".format(axis))
        if src in ("stated", "genre-default", "from-material"):
            continue                                   # the user or the input supplied it
        # `inferred-from-request` CLAIMS the request points at it, so it owes the pointer even
        # though it is not a free choice — that claim is the whole difference from `delegated`.
        if _w(p.get("basis")) < MIN_BASIS:
            out.append("`{}` was decided FOR the user and gives no `basis` — point at what in the "
                       "request or the material supports it. `I judged it` is the sentence this "
                       "field replaces; being made to point at something is what turns a default "
                       "into a reading of the actual input.".format(axis))
        if axis in ALTERNATIVE_REQUIRED and _w(p.get("alternative")) < MIN_ALT:
            out.append("`{}` needs an `alternative`: what ELSE was plausible here and why it lost. "
                       "It is one sentence, and it is the only thing separating a choice from a "
                       "default — the direction gate, the arc competition and the composition "
                       "competition all work exactly this way.".format(axis))

    missing = [a for a in AXES if a not in seen]
    if missing:
        out.append("no pick recorded for: {}. Under a `decide everything yourself` directive every "
                   "Step-0 axis was answered by SOMEONE — say who, even if the answer was "
                   "`not-applicable`.".format(" · ".join(missing)))
    return out


def delegated(interview) -> list[dict]:
    """The picks the user did NOT make, FURTHEST FROM THEIR OWN WORDS FIRST.

    The hand-off has a reading order, and it should not be the order the axes happen to be listed
    in. A pure `delegated` pick — nothing in the request or the material pointed at it — is the one
    most likely to be wrong and the one a glance can veto, so it goes at the top.
    """
    picks = (interview or {}).get("picks") if isinstance(interview, dict) else None
    rows = [p for p in (picks or []) if isinstance(p, dict)
            and str(p.get("source") or "").strip().lower() in ("delegated", "inferred-from-request")]
    return sorted(rows, key=lambda p: -_DISTANCE.get(
        str(p.get("source") or "").strip().lower(), 0))


MISSING = (
    '`interview.picks` is missing, and this deck delivered its checkpoints as `auto` — meaning the '
    'skill answered Step 0 itself. Record one row per axis, so a value the USER gave and a value '
    'the skill invented stop looking identical:\n'
    '    "interview": {"picks": [\n'
    '        {"axis": "angle",    "source": "genre-default", "value": "<the deck the request implies>"},\n'
    '        {"axis": "audience", "source": "delegated", "value": "<who>",\n'
    '         "basis": "<what in the request/material points at them>",\n'
    '         "alternative": "<who else it could have been for, and why not>"},\n'
    '        {"axis": "language", "source": "stated", "value": "<the user\'s own>"}, …]}\n'
    '  Axes: ' + " · ".join(AXES) + '\n'
    '  Sources: ' + " | ".join(SOURCES) + '  ·  `angle` may never be `delegated`.\n'
    '  Record each row with: python3 scripts/deck_gates.py picks <deck-dir> --set AXIS=VALUE --source …')


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────
def _selftest() -> int:
    fails = []

    def row(axis, source, **kw):
        d = {"axis": axis, "source": source, "value": "a real value"}
        d.update(kw)
        return d

    BASIS = "the request names a three-day trip and no venue"
    ALT = "a conference room was possible; the request says 'send it to me'"

    def full(**over):
        picks = []
        for a in AXES:
            if a == "angle":
                picks.append(row(a, "genre-default"))
            elif a in ALTERNATIVE_REQUIRED:
                picks.append(row(a, "delegated", basis=BASIS, alternative=ALT))
            else:
                picks.append(row(a, "delegated", basis=BASIS))
        iv = {"picks": picks}
        iv.update(over)
        return iv

    if faults(full(), auto=True):
        fails.append("a complete record was rejected: {}".format(faults(full(), auto=True)[:2]))
    # a SUPERVISED deck is untouched
    if faults(None, auto=False) or faults({}, auto=False):
        fails.append("a supervised deck was asked for delegated picks")
    if not faults(None, auto=True):
        fails.append("an auto deck with no picks passed")

    # 🔴 the floor
    bad = full()
    bad["picks"][0] = row("angle", "delegated", basis=BASIS, alternative=ALT)
    f = faults(bad, auto=True)
    if not any("may not be" in x for x in f):
        fails.append("an INVENTED angle passed — that is the measured failure this exists for")
    ok_angle = full()
    ok_angle["picks"][0] = row("angle", "genre-default")
    if faults(ok_angle, auto=True):
        fails.append("a genre-default angle was rejected")

    # basis / alternative
    nb = full()
    nb["picks"][AXES.index("density")] = row("density", "delegated")
    if not any("basis" in x for x in faults(nb, auto=True)):
        fails.append("a delegated pick with no basis passed")
    na = full()
    na["picks"][AXES.index("audience")] = row("audience", "delegated", basis=BASIS)
    if not any("alternative" in x for x in faults(na, auto=True)):
        fails.append("a delegated AUDIENCE with no alternative passed")
    # …but an axis outside the three does not owe one
    small = full()
    small["picks"][AXES.index("length")] = row("length", "delegated", basis=BASIS)
    if faults(small, auto=True):
        fails.append("an axis outside ALTERNATIVE_REQUIRED was asked for an alternative")

    # stated picks owe nothing
    st = full()
    st["picks"][AXES.index("language")] = row("language", "stated")
    if faults(st, auto=True):
        fails.append("a STATED pick was asked to justify itself")

    # 🔴 language-independent width: the same bar in Chinese
    cn = full()
    cn["picks"][AXES.index("audience")] = row(
        "audience", "delegated", basis="请求里写明是准备去旅行的人，没有提到会议场合",
        alternative="也可能是本地居民，但请求说的是「打算去旅行」")
    if faults(cn, auto=True):
        fails.append("a real CJK basis/alternative was rejected — len() instead of reason_width "
                     "would do exactly this: {}".format(faults(cn, auto=True)[:1]))

    # shape robustness
    for junk in (None, 7, "str", [1], {"picks": "not a list"}, {"picks": [7]}):
        try:
            faults(junk, auto=True)
        except Exception as e:                                         # noqa: BLE001
            fails.append("faults raised on {!r}: {}".format(junk, e))
    if not faults({"picks": [row("nonsense", "delegated", basis=BASIS)]}, auto=True):
        fails.append("an invented AXIS passed")
    if not faults({"picks": [row("audience", "invented", basis=BASIS)]}, auto=True):
        fails.append("an invented SOURCE passed")
    dup = {"picks": [row("audience", "stated"), row("audience", "delegated", basis=BASIS)]}
    if not any("two picks" in x for x in faults(dup, auto=True)):
        fails.append("two picks on one axis passed")

    # is_auto reads the record the gates already require
    if not is_auto({"content": {"checkpoint": {"mode": "auto"}}}):
        fails.append("is_auto missed content.checkpoint.mode")
    if not is_auto({"design": {"checkpoint": {"mode": "auto"}}}):
        fails.append("is_auto missed the CODEX spelling (design.checkpoint)")
    if is_auto({"content": {"checkpoint": {"mode": "approved"}}}):
        fails.append("is_auto fired on an APPROVED deck")
    for junk in (None, 7, "str", {}):
        if is_auto(junk):
            fails.append("is_auto fired on {!r}".format(junk))

    if len(delegated(full())) != len(AXES) - 1:
        fails.append("delegated() did not return the picks the hand-off must surface")

    for f in fails:
        print("FAIL " + f)
    print("[delegated_picks selftest] {}".format(
        "FAILED: {}".format(len(fails)) if fails else "ok"))
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
