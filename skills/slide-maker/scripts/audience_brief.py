#!/usr/bin/env python3
"""The AUDIENCE BRIEF contract, in one place, imported by every gate path.

Step 1 writes a comprehension brief about the SOURCE. On a deck with no source there is nothing to
comprehend, so that brief becomes a summary of the SUBJECT — and a subject brief produces a deck
*about* the topic where one *for* the audience was asked for.

🔴 THE MEASURED DEFECT. A deck was built from the interview answers `audience = people planning a
trip` and `goal = they leave able to plan one`. The comprehension brief described Melbourne. Three
arc candidates were then generated inside that frame, and the winner was picked because "it is the
only candidate whose organising idea also does the organising work … nothing is easier to remember
a week later" — a DECK-QUALITY test. The recorded `goal` was never used to score them. The runner-up
was rejected for becoming "the same list every travel site gives me", which for someone planning a
trip is the deliverable, not the failure mode. What shipped was a thesis on an 1837 land survey.

The damage starts UPSTREAM of the arc and reaches the research: that build verified chain lengths,
allotment widths and inscription years, and gathered nothing on daily cost, distances, a rainy-day
alternative or what to skip. Information gathering is aimed by the frame, so a wrong frame aims it
wrongly and every later gate passes.

🔴 THE SAME RULE ALREADY EXISTED AND DID NOT FIRE. `checkpoint-convention.md` carries the Paris
measurement — a run that refused the Eiffel-tower silhouette as a motif and then deleted the
landmarks from the CONTENT — but it is scoped to the auto-waiver's *delegated Step-0 picks*. The
Melbourne build ran a full interview, so it was never inside that rule's scope. A correct rule in
the wrong scope is not a gate.

WHAT THIS FIELD IS. Not a persona and not a summary: the DECISIONS the audience has to make, in
the order they will face them, each with what they need in hand to make it. Write it BEFORE
gathering information, and aim the gathering at it.

    "audience_brief": {
      "who": "<who is in the room and what they are about to do>",
      "decisions": [
        {"decision": "<what they must decide>", "needs": "<what they need in hand to decide it>"},
        …
      ]
    }
"""
from __future__ import annotations

MIN_DECISIONS = 3
MIN_TEXT = 12

# A deck whose audience has no decision to make: the brief is not skipped for being hard, only for
# being genuinely inapplicable.
CARVES = ("reference-only", "external-deck", "tiny-ask", "user-waived")


def is_waived(brief) -> bool:
    """Is this record claiming a carve rather than supplying the brief?"""
    return isinstance(brief, dict) and bool(str(brief.get("waived") or "").strip())


def waiver_faults(brief) -> list[str]:
    """Complaints about a WAIVED brief. Empty means the carve is properly claimed."""
    out: list[str] = []
    cat = str((brief or {}).get("waived_category") or "").strip().lower()
    if cat not in CARVES:
        out.append("needs a `waived_category` naming the carve: {}. A deck being hard to think "
                   "about is not one of them.".format(" | ".join(CARVES)))
    if len(str((brief or {}).get("waived") or "").strip()) < MIN_TEXT:
        out.append("needs a written reason beside the category — who the audience is and why they "
                   "have nothing to decide.")
    return out


def faults(brief) -> list[str]:
    """Complaints about a SUPPLIED brief. Empty means it is filled."""
    out: list[str] = []
    if not isinstance(brief, dict):
        return [MISSING]
    if len(str(brief.get("who") or "").strip()) < MIN_TEXT:
        out.append("`who` must say who is in the room and what they are about to do.")
    rows = brief.get("decisions")
    if not isinstance(rows, list) or len(rows) < MIN_DECISIONS:
        out.append("`decisions` must list at least {} decisions the audience has to make, in the "
                   "order they will face them. Fewer than that is a persona, not a brief."
                   .format(MIN_DECISIONS))
        return out
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            out.append("`decisions[{}]` must be an object.".format(i))
            continue
        if len(str(r.get("decision") or "").strip()) < MIN_TEXT:
            out.append("`decisions[{}].decision` is empty — name what they must decide.".format(i))
        if len(str(r.get("needs") or "").strip()) < MIN_TEXT:
            out.append("`decisions[{}].needs` is empty. This is the half that aims the research: "
                       "a decision with no stated need gathers nothing.".format(i))
    return out


MISSING = (
    'is missing. Step 1 opens by writing down what the AUDIENCE has to DECIDE — in the order they '
    'will face it, each with what they need in hand — and the information gathering is aimed at '
    'that list. On a deck with NO SOURCE this replaces the comprehension brief outright: there is '
    'no source to comprehend, and a brief about the SUBJECT produces a deck about the subject '
    'where one for the audience was asked for.\n'
    '    {"audience_brief": {"who": "<who is in the room, and what they are about to do>",\n'
    '                        "decisions": [{"decision": "<what they must decide>",\n'
    '                                       "needs": "<what they need in hand to decide it>"}, …]}}\n'
    '  Or claim a carve: {"waived": "<why this audience has nothing to decide>", '
    '"waived_category": "' + " | ".join(CARVES) + '"}')
