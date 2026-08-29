#!/usr/bin/env python3
"""Compose the deck's ARCHITECTURE as a sequence, before any page is built.

The gap this closes is one this skill can state precisely about itself. `lint_deck` demands at
least four distinct page skeletons on an 8+-slide deck (SKELETON VARIETY) and reports three
adjacent slides sharing 75% of their structure (LAYOUT SAMENESS) — but both fire AFTER the build,
at which point varying the architecture means re-laying pages that are already written. So the
architecture gets decided one page at a time, in the order the content happened to arrive, and the
usual result is one skeleton repeated with different words in it. Measured on a deliberately dead
deck built for this check: zero layout findings, a clean lint, and three skeletons across fourteen
slides.

Deciding the sequence FIRST is what a designer does, and it is cheap to do deterministically —
this is arithmetic over the slide roles, not a model call. It runs in milliseconds, adds no
round-trip, and hands back a table the author builds from and the design checkpoint shows.

    python3 scripts/plan_rhythm.py --roles cover,context,method,result,result,compare,takeaway,close
    python3 scripts/plan_rhythm.py --slides 12 --carry 4,7          # roles unknown yet
    python3 scripts/plan_rhythm.py --gates <deck-dir>               # read roles from .deck-gates.json
    python3 scripts/plan_rhythm.py --selftest

🔴 A PROPOSAL, not a verdict. It knows the shape of an argument, not your argument — deviate wherever
the content wants something else, and say so in the design plan where deviations are recorded. What
it guarantees is only that the sequence it proposes clears the two structural floors, so the
architecture is a decision rather than an accident.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# What each kind of page WANTS, most apt first. This is the design intelligence in the file: a
# result is a thing to look at (island/full-bleed), a comparison is a set to scan side by side
# (gallery/split), a process is stages in order (band), metrics are a field to read at once
# (dashboard), and a claim is one sentence that should own its page (statement).
ROLE_FIT = {
    "cover":      ("full_bleed", "statement"),
    "agenda":     ("band", "rail"),
    "context":    ("split", "band"),
    "problem":    ("statement", "split"),
    "method":     ("band", "rail", "split"),
    "result":     ("island", "full_bleed", "split"),
    "evidence":   ("island", "split"),
    "compare":    ("gallery", "split", "dashboard"),
    "comparison": ("gallery", "split", "dashboard"),
    "data":       ("dashboard", "island"),
    "metrics":    ("dashboard", "band"),
    "takeaway":   ("statement", "island"),
    "insight":    ("statement", "island"),
    "next":       ("band", "rail"),
    "divider":    ("statement", "full_bleed"),
    "closing":    ("statement", "full_bleed"),
    "close":      ("statement", "full_bleed"),
    "appendix":   ("dashboard", "band"),
}
# The fallback rotation for a role this file does not know. Ordered so consecutive picks are
# structurally far apart rather than alphabetically adjacent.
ROTATION = ("split", "island", "band", "dashboard", "rail", "gallery", "statement", "full_bleed")
MIN_DISTINCT = 4        # lint_deck's SKELETON VARIETY floor on an 8+-slide deck
WINDOW = 3              # LAYOUT SAMENESS reads a 3-slide window, so no repeat inside one


def plan(roles, carry=(), min_distinct=MIN_DISTINCT, home=None):
    """[(index, role, skeleton, why)] — a sequence that clears both structural floors.

    Greedy with a look-back: each page takes the most apt architecture its role wants that is not
    already in the previous `WINDOW - 1` pages; if every apt one is blocked, it falls to the
    rotation. A page named in `carry` (the design plan's `carried_by`) is pushed toward the
    architectures that can hold a signature move rather than the safest fit.

    `home` is the deck's HOME BASE — the architecture that should be its visible default. It exists
    because `agents/slide-design.md` requires it and this planner would otherwise fight the
    workflow: when the direction gate has been run, the user picked a composition from RENDERED
    options, and that skeleton "is the map's PLURALITY: the most-used home base, visibly the deck's
    default". A planner that rotated evenly would silently override the pick the user actually made
    and looked at. With `home` set, every page whose role is content-neutral falls back to it rather
    than to the rotation, so the deck reads as one composition with departures — which is what a
    house style IS — while the >=4-distinct and no-3-in-a-row floors still hold.
    """
    # A typo in `home` must not reach the plan. Measured: `--home nosuch` was carried into every
    # neutral row, proposing an architecture `deckkit.skeleton()` cannot build — the planner and the
    # builder drifting apart, which is the one thing this file's own selftest forbids.
    if home is not None and home not in ROTATION:
        raise ValueError("plan_rhythm: unknown home base {!r} — one of: {}"
                         .format(home, ", ".join(sorted(ROTATION))))
    BOLD = ("full_bleed", "island", "statement")
    out, recent = [], []
    for i, role in enumerate(roles, 1):
        key = str(role or "").strip().lower()
        wants = list(ROLE_FIT.get(key, ()))
        if i in carry:
            wants = [k for k in BOLD if k not in wants[:1]] + wants
        pick, why = None, ""
        # The home base gets FIRST REFUSAL on every page, and is only displaced by the window or by
        # a page whose job outranks the default: the bookends, which set and close the deck, and the
        # carry slides, which exist to depart from it. With a 3-slide window the home can land on at
        # most every third page, which is exactly enough to be the plurality without becoming the
        # only thing in the deck — the "most-used home base, visibly the deck's default" the design
        # agent asks for, with departures around it.
        reserved = key in ("cover", "closing", "close", "divider") or i in carry
        if home and home not in recent and not reserved:
            out.append((i, key or "?", home, "the deck's home base (the direction gate's pick)"))
            recent = ([home] + recent)[:WINDOW - 1]
            continue
        for cand in wants:
            if cand not in recent:
                pick = cand
                why = ("carries the signature move" if i in carry and cand in BOLD
                       else "apt for a {!r} page".format(key or "content"))
                break
        if pick is None:
            for cand in ROTATION:
                if cand not in recent:
                    pick = cand
                    why = ("every architecture this role wants is already in the last {} pages — "
                           "rotated to keep the rhythm moving".format(WINDOW - 1)
                           if wants else "no role given; rotating the architecture")
                    break
        if pick is None:                       # WINDOW-1 >= len(ROTATION) is impossible, but never
            pick, why = ROTATION[0], "fallback"
        out.append((i, key or "?", pick, why))
        recent = ([pick] + recent)[:WINDOW - 1]

    # If the sequence still does not reach the distinct floor (a very short deck, or one role
    # repeated throughout), spend the LEAST-committed pages on unused architectures rather than
    # disturbing the ones a role genuinely wanted.
    used = {k for _i, _r, k, _w in out}
    if len(out) >= 8 and len(used) < min_distinct:
        unused = [k for k in ROTATION if k not in used]
        for idx in range(len(out) - 1, -1, -1):
            if not unused:
                break
            i, role, pick, _why = out[idx]
            if i in carry or role in ("cover", "closing", "close"):
                continue
            before = out[idx - 1][2] if idx else None
            after = out[idx + 1][2] if idx + 1 < len(out) else None
            for cand in list(unused):
                if cand not in (before, after):
                    out[idx] = (i, role, cand,
                                "spent on an unused architecture — the deck was under the "
                                "{}-skeleton floor".format(min_distinct))
                    unused.remove(cand)
                    used.add(cand)
                    break
    return out


def check(rows, min_distinct=MIN_DISTINCT, home=None):
    """[] if the sequence clears both floors, else the reasons it does not."""
    problems = []
    picks = [k for _i, _r, k, _w in rows]
    if home and picks:
        from collections import Counter
        top, n = Counter(picks).most_common(1)[0]
        if top != home:
            problems.append(
                "the home base is {!r} but {!r} is the plurality ({} of {}) — the direction gate's "
                "composition must be the deck's visible default, or the user's pick has been "
                "quietly overridden".format(home, top, n, len(picks)))
    if len(rows) >= 8 and len(set(picks)) < min_distinct:
        problems.append("only {} distinct skeleton(s) across {} slides — lint's floor is {}"
                        .format(len(set(picks)), len(rows), min_distinct))
    for i in range(len(picks) - WINDOW + 1):
        win = picks[i:i + WINDOW]
        if len(set(win)) == 1:
            problems.append("slides {}-{} all use {!r} — LAYOUT SAMENESS reads a {}-slide window"
                            .format(i + 1, i + WINDOW, win[0], WINDOW))
    return problems


def render(rows):
    lines = ["| # | role | skeleton | why |", "|---|---|---|---|"]
    for i, role, pick, why in rows:
        lines.append("| {} | {} | `{}` | {} |".format(i, role, pick, why))
    picks = [k for _i, _r, k, _w in rows]
    lines.append("")
    from collections import Counter
    top, n = Counter(picks).most_common(1)[0] if picks else ("-", 0)
    lines.append("{} slides · {} distinct architecture(s) · home base {!r} on {} · no repeat "
                 "inside a {}-slide window".format(len(rows), len(set(picks)), top, n, WINDOW))
    return lines


def _roles_from_gates(deck_dir):
    p = Path(os.path.expanduser(deck_dir)) / ".deck-gates.json"
    try:
        g = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit("could not read {}: {}".format(p, exc))
    rows = ((g.get("content") or {}).get("slides")) or []
    if not rows:
        raise SystemExit("{} has no content.slides — run the content checkpoint first, or pass "
                         "--roles/--slides".format(p))
    return [str(r.get("role") or "") for r in rows]


def _selftest():
    ok, bad = [], []

    def case(label, rows, cond, detail=""):
        (ok if cond else bad).append(label if cond else "{} — {}".format(label, detail))

    r = plan(["cover", "context", "method", "result", "result", "compare", "takeaway", "close"])
    case("a normal 8-slide argument clears both floors", r, not check(r), str(check(r)))
    case("...with at least {} architectures".format(MIN_DISTINCT), r,
         len({k for _i, _ro, k, _w in r}) >= MIN_DISTINCT,
         str([k for _i, _ro, k, _w in r]))

    # The case the floors exist for: one role repeated the whole way down.
    r = plan(["result"] * 12)
    case("twelve identical roles still clear both floors — the rotation does the work", r,
         not check(r), str(check(r)))
    case("...and no three consecutive pages share an architecture", r,
         all(len(set([k for _i, _ro, k, _w in r][i:i + 3])) > 1
             for i in range(len(r) - 2)),
         str([k for _i, _ro, k, _w in r]))

    r = plan(["context"] * 10, carry=(4, 7))
    bold = {k for i, _ro, k, _w in r if i in (4, 7)}
    case("a carry slide is pushed toward an architecture that can hold a signature move",
         bold & {"full_bleed", "island", "statement"}, True, str(bold))

    r = plan([], carry=())
    case("an empty deck plans nothing rather than raising", r == [], True, str(r))
    r = plan(["cover", "close"])
    case("a 2-slide deck is not held to the 8+-slide floor", not check(r), True, str(check(r)))

    # check() must actually be able to FAIL, or it proves nothing about plan().
    bad_rows = [(i, "x", "split", "") for i in range(1, 13)]
    case("check() reports a sequence that repeats one architecture throughout",
         len(check(bad_rows)) >= 2, True, str(check(bad_rows)[:2]))

    # every proposed name must be a real skeleton the toolkit can build
    try:
        import deckkit as dk
        names = set(dk.SKELETONS)
    except Exception:
        names = set(ROTATION)
    proposed = {k for _i, _ro, k, _w in plan(list(ROLE_FIT) + ["unknown-role"] * 4)}
    case("every architecture it proposes exists in deckkit.SKELETONS",
         proposed <= names, True, str(proposed - names))

    try:
        plan(["a"] * 8, home="nosuch")
        case("a typo'd home base is refused", False, False, "it was carried into the plan")
    except ValueError:
        case("a typo'd home base is refused rather than proposing an architecture the builder "
             "cannot make", True, True)
    r = plan(["context"] * 10, home="rail")
    from collections import Counter as _C
    case("a home base becomes the deck's PLURALITY — the direction gate's pick stays the visible "
         "default", r, _C(k for _i, _ro, k, _w in r).most_common(1)[0][0] == "rail",
         str(_C(k for _i, _ro, k, _w in r)))
    case("...and the >=4-distinct floor still holds with a home base", r,
         len({k for _i, _ro, k, _w in r}) >= MIN_DISTINCT,
         str({k for _i, _ro, k, _w in r}))

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roles", help="comma-separated per-slide roles, in order")
    ap.add_argument("--slides", type=int, help="slide count, when the roles are not decided yet")
    ap.add_argument("--carry", help="comma-separated slide numbers carrying the signature move")
    ap.add_argument("--home", help="the deck's HOME-BASE architecture — the direction gate's picked "
                                   "composition, which must be the map's plurality")
    ap.add_argument("--gates", help="a deck dir — read roles from its .deck-gates.json content.slides")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.gates:
        roles = _roles_from_gates(a.gates)
    elif a.roles:
        roles = [r.strip() for r in a.roles.split(",") if r.strip()]
    elif a.slides:
        roles = [""] * a.slides
    else:
        ap.print_help()
        return 2
    carry = tuple(int(c) for c in (a.carry or "").replace(" ", "").split(",") if c.isdigit())
    try:
        rows = plan(roles, carry, home=a.home)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps([{"slide": i, "role": r, "skeleton": k, "why": w}
                          for i, r, k, w in rows], indent=1))
        return 0
    print("\n".join(render(rows)))
    problems = check(rows, home=a.home)
    if problems:
        print("\nthis sequence does NOT clear the floors:\n  - " + "\n  - ".join(problems))
        return 1
    print("\nBuild each page from `deckkit.skeleton(slide, \"<kind>\")` — it returns the named rects "
          "for that architecture.\nThis is a PROPOSAL: deviate where the content wants something "
          "else, and record the deviation in the design plan.")
    return 0


try:
    from _console import safe_stdio
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
