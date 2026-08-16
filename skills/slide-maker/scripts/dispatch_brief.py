#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the deck's dispatch brief ONCE, then point every subagent at it.

Why this exists
---------------
Measured on a real 14-slide build: nine subagent dispatches cost **41,203 output tokens —
~12.5 minutes**, the most expensive turn class in the whole pipeline, at ~4,600 tokens per
dispatch. Almost none of that was per-dispatch information. Every prompt re-stated the same
interview answers, the same absolute paths, the same search cap, the same auto-waiver state and
the same CONTRACT CARD; what genuinely differed was a lens letter, a section range, or a round
number — a few dozen tokens.

Prose cannot fix this. "Don't repeat yourself in dispatch prompts" is exactly the class of
instruction this skill keeps proving gets skipped, because nothing reports it: the dispatch
works, the subagent does its job, and the bill arrives as wall clock nobody attributes. So the
repetition is removed structurally — the shared part becomes a FILE the subagent reads, and the
dispatch prompt becomes a pointer.

There is a fidelity dividend, and it may matter more than the minutes. `references/critic-panel.md`
requires the CONTRACT CARD to be assembled from the approved plans "declarations only, never
rationale" at EVERY critic dispatch, and warns that reconstructing it from memory is how a
declared contract quietly stops matching what was approved. A file written once and read by all
is the same card every time, by construction.

What it does NOT do
-------------------
It does not invent content. The brief is written by the coordinator, from the approved plans;
this tool creates the skeleton, refuses to hand out a prompt while required sections are still
unfilled, and prints the pointer. A brief that lies is still a brief that lies — being in a file
does not make it true.

The brief is written to a SCRATCH path, never into the deliverable folder
(`references/checkpoint-convention.md`: plan files never ship beside the deck).

Usage
-----
  python3 scripts/dispatch_brief.py init  --deck <deck-dir>          # create + print the path
  python3 scripts/dispatch_brief.py check --brief <path>             # gate: all sections filled?
  python3 scripts/dispatch_brief.py prompt --brief <path> \\
          --role critic --lens A --round 2                           # print the dispatch prompt
  python3 scripts/dispatch_brief.py prompt --brief <path> \\
          --role section --section 2 --slides 6-10
"""
import argparse
import os
import re
import sys
import tempfile

# Sections the brief must carry. Each maps to the thing a dispatched agent otherwise has to be
# told inline, every single time. The TODO marker is what `check` looks for.
TODO = "<<FILL>>"
SECTIONS = [
    ("Deck", "absolute path of the deck dir + the .pptx filename"),
    ("Interview answers", "purpose · audience · time · delivery context · primary goal · "
                          "density · tone · language · template decision · review tier (chosen "
                          "at the POST-BUILD question, not the interview — 'pending' before it)"),
    ("Mode", "standard, or a per-deck AUTO WAIVER (say which, and that checkpoints post as FYI)"),
    ("Search cap", "planned / spent, and 'do not search at all' when the deck is local-sourced"),
    ("Source material", "what it is and where it lives, the condense/verbatim/hybrid answer, and "
                        "the WEB-SUPPLEMENT answer: (a) source only / (b) named gaps only / "
                        "(c) free within a cap — plus the gaps you named. On (a), a claim the "
                        "source cannot settle stays flagged, never filled from memory"),
    ("Contract card", "assembled from the APPROVED plans — declarations only, never rationale. "
                      "Full required field list: references/critic-panel.md -> 'The CONTRACT CARD'"),
]

ROLE_PROMPTS = {
    "critic": (
        "You are an INDEPENDENT CRITIC applying **LENS {lens} ONLY** for the slide-maker skill.\n"
        "🔴 Read `{skill}/agents/critic.md` and apply ONLY lens {lens} (plus the shared "
        "high-recurrence box). Read `{skill}/references/review-rubrics.md` for your lens, and the "
        "ONE per-purpose section matching this deck's purpose — not the other eight.\n"
        "🔴 Read the deck brief and CONTRACT CARD at `{brief}` before you open a slide.\n"
        "Round {round}. Judge the RENDERED PIXELS in `{renders}`; the deck is `{deck}`.\n"
        "You judge, you do not co-design. Return the review JSON your brief specifies; it is "
        "validated by `validate_review.py critic`, so a non-conforming review is rejected."),
    "section": (
        "Author ONE section of this deck as a Python module, per the slide-maker skill.\n"
        "🔴 Read the deck brief, the approved plans and the CONTRACT CARD at `{brief}` first.\n"
        "🔴 Copy the scaffold in `{skill}/references/examples/section_example.py`: import the "
        "shared `style`, expose `build_section(prs)`, one function per slide with its plan-row "
        "docstring, and set START_PAGE so page numbers stay continuous.\n"
        "You own SECTION {section} — slides {slides}. Do not restyle: palette, type and chrome all "
        "come from `style.py`, which is already fixed.\n"
        "Self-render just your section to check it, then return the finished module path plus a "
        "one-line slide -> function index so the coordinator never has to grep for a slide."),
    "planner": (
        "You are the CONTENT PLANNER for this deck, per the slide-maker skill.\n"
        "🔴 Read `{skill}/agents/content-planner.md` and work to it, plus "
        "`{skill}/references/content-plan-spec.md` and the CONTENT lens of "
        "`{skill}/references/review-rubrics.md`.\n"
        "🔴 Read the deck brief at `{brief}` — it carries the interview answers, the source "
        "material and the search cap. Honour the cap exactly and report planned/spent.\n"
        "CONTENT ONLY — no design, no colour, no layout."),
    "design": (
        "You are the ART DIRECTOR (slide-design agent) for this deck, per the slide-maker skill.\n"
        "🔴 Read `{skill}/agents/slide-design.md` and work to it.\n"
        "🔴 Read the deck brief and the APPROVED content plan at `{brief}` — the message is "
        "locked; you design on top of it and never re-open it.\n"
        "Return the Design plan with every required field, including the gate line."),
}


def _skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _default_brief_path(deck_dir):
    name = os.path.basename(os.path.abspath(deck_dir.rstrip("/"))) or "deck"
    return os.path.join(tempfile.gettempdir(), "slide-maker-brief-{}.md".format(name))


def cmd_init(args):
    path = args.out or _default_brief_path(args.deck)
    if os.path.exists(path) and not args.force:
        sys.stderr.write("dispatch_brief: {} already exists — pass --force to overwrite, or edit "
                         "it in place (that is the normal case: write it once, reuse it).\n"
                         .format(path))
        return 1
    lines = ["# Deck brief — read this before doing anything",
             "",
             "Written ONCE by the coordinator, read by every dispatched agent. If something here",
             "is wrong, fix it HERE — the agents all read this copy, so a fix reaches all of them.",
             ""]
    for name, hint in SECTIONS:
        lines += ["## {}".format(name), "*({})*".format(hint), TODO, ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(path)
    print("\nFill every {} section, then:  dispatch_brief.py check --brief {}"
          .format(TODO, path), file=sys.stderr)
    return 0


def _unfilled(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    missing = []
    for name, _hint in SECTIONS:
        m = re.search(r"^##\s+" + re.escape(name) + r"\s*$(.*?)(?=^##\s|\Z)",
                      text, re.M | re.S)
        body = (m.group(1) if m else "")
        body = re.sub(r"^\*\(.*?\)\*\s*$", "", body, flags=re.M)   # drop the hint line
        if not m or TODO in body or not body.strip():
            missing.append(name)
            continue
        # SUB-FIELD check. A section can be "filled" and still be missing the one answer a
        # downstream agent needs — which is how a required field becomes decorative. Only the
        # answers with a fixed, machine-checkable vocabulary are asserted here; prose is not.
        if name == "Source material":
            low = body.lower()
            said_none = any(k in low for k in ("no source", "无用户素材", "无素材", "none provided",
                                               "no material", "no user material"))
            answered = any(k in low for k in ("source only", "仅用源", "named gaps", "点名的缺口",
                                              "free within", "上限内自由", "web-supplement",
                                              "web supplement", "不搜索", "do not search"))
            if not (said_none or answered):
                missing.append(name + " → the WEB-SUPPLEMENT answer (source only / named gaps only "
                                      "/ free within a cap). Provided material is where the gap is "
                                      "least visible: it is complete for its own purpose, not the "
                                      "deck's. Name the gaps you can already see, or say none.")
    return missing


def cmd_check(args):
    if not os.path.exists(args.brief):
        sys.stderr.write("dispatch_brief: no brief at {}\n".format(args.brief))
        return 2
    missing = _unfilled(args.brief)
    if missing:
        sys.stderr.write("dispatch_brief: NOT READY — still unfilled: {}\n"
                         "  A dispatched agent reads this file instead of being told inline, so an\n"
                         "  unfilled section is information that reaches NOBODY.\n"
                         .format(", ".join(missing)))
        return 1
    print("brief ready: {}".format(args.brief))
    return 0


def cmd_prompt(args):
    if not os.path.exists(args.brief):
        sys.stderr.write("dispatch_brief: no brief at {} — run `init` first\n".format(args.brief))
        return 2
    missing = _unfilled(args.brief)
    if missing:
        sys.stderr.write("dispatch_brief: refusing to emit a dispatch prompt — the brief still has "
                         "unfilled sections: {}\n".format(", ".join(missing)))
        return 1
    if args.role == "critic" and not args.lens:
        sys.stderr.write("dispatch_brief: --lens is required for a critic dispatch (A = content · "
                         "fidelity · narrative, B = design · layout · legibility). One lens each — "
                         "a critic carrying both is a different, weaker review.\n")
        return 1
    if args.role == "section" and not (args.section and args.slides):
        sys.stderr.write("dispatch_brief: --section and --slides are required for a section "
                         "dispatch.\n")
        return 1
    deck_dir = os.path.dirname(os.path.abspath(args.brief))
    print(ROLE_PROMPTS[args.role].format(
        skill=_skill_root(), brief=os.path.abspath(args.brief),
        lens=args.lens or "", round=args.round, section=args.section or "",
        slides=args.slides or "", deck=args.deck or "<deck>.pptx",
        renders=os.path.join(args.deck or deck_dir, "render") if args.deck else "render/"))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create the brief skeleton")
    p.add_argument("--deck", required=True, help="deck directory (names the scratch file)")
    p.add_argument("--out", help="explicit path (default: a scratch path, never the deck folder)")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("check", help="are all required sections filled?")
    p.add_argument("--brief", required=True)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("prompt", help="print the short dispatch prompt")
    p.add_argument("--brief", required=True)
    p.add_argument("--role", required=True, choices=sorted(ROLE_PROMPTS))
    p.add_argument("--lens", choices=["A", "B"])
    p.add_argument("--round", default="1")
    p.add_argument("--section")
    p.add_argument("--slides")
    p.add_argument("--deck", help="deck dir, for the render path")
    p.set_defaults(fn=cmd_prompt)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
