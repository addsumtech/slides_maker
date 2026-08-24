#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard the DESIGN stack's cross-references and shared numbers.

WHY THIS EXISTS, measured. A whole-skill audit found that the design pipeline's *rules* were sound
and its *indexing* had drifted. Every defect was a count, a range, a letter or a token list — the
one class of content that no artifact and no check ever re-derives, so it rots silently:

  · `agents/slide-design.md` declared "Design self-verify (a-q)" in two places while the list ran
    to (r). Item (r) landed 2026-07-27; the header was written 2026-07-22 and never updated. (r) is
    the density line — the ONE self-verify item with a hard deterministic backstop. An art director
    sweeping "a through q" licenses itself to stop one item short of the gated one.
  · PRE-FLIGHT 12(a) said the form-family ceiling was ">~40%" while eight other files said
    "~40-50%", so a 45% card family passed Step 2 and the critic and then failed a post-build tick
    that has no justification arm.
  · SKILL.md's DESIGN checkpoint named `direction gate:` and dropped branch (d)'s `style gate:`;
    `interior register:` was required by self-verify (q), PRE-FLIGHT 6b and the critic contract card
    and appeared nowhere in the file SKILL.md names as the OWNER of the checkpoint's required lines.

None of these is catchable by reading — they are agreements between files. They are all decidable by
a program, which is where the skill's own layering doctrine says they belong. So:

    python3 scripts/check_design_contracts.py            # exit 1 on any drift
    python3 scripts/check_design_contracts.py --selftest # prove the checks can still fail

Exit 0 = the design stack's indexes agree. Exit 1 = named drift. Exit 2 = could not run, which is
never the same as clean.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

# Files whose prose participates in these agreements. Missing files are reported, not skipped: a
# check that quietly shrinks its own corpus is the failure mode this whole script exists to prevent.
CORPUS_DIRS = ("", "references", "agents")

SELF_VERIFY_OWNER = os.path.join("agents", "slide-design.md")
CHECKPOINT_OWNER = os.path.join("references", "checkpoint-convention.md")


def _read(rel):
    p = os.path.join(SKILL, rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def _corpus():
    """(relpath, text) for every markdown file a skill trigger can reach."""
    out = []
    for sub in CORPUS_DIRS:
        d = os.path.join(SKILL, sub) if sub else SKILL
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            rel = os.path.join(sub, name) if sub else name
            out.append((rel, _read(rel) or ""))
    return out


# ---------------------------------------------------------------- self-verify integrity

_ITEM = re.compile(r"^- \*\*\(([a-z][0-9]?)\)", re.M)
_HEADER = re.compile(r"^### Design self-verify \(([^)]*)\)", re.M)
# `self-verify (g)` and `self-verify-(l)` are both used in the tree; accept either joiner.
_XREF = re.compile(r"self-verify[ \-]\(?([a-z][0-9]?)\)")


def _letters_in_range(spec):
    """'a-r' / 'a-r, plus h2 - NINETEEN checks' -> the set of letters the header claims."""
    m = re.search(r"([a-z])\s*[-–—]\s*([a-z])", spec)
    if not m:
        return None
    lo, hi = m.group(1), m.group(2)
    if lo > hi:
        return None
    return {chr(c) for c in range(ord(lo), ord(hi) + 1)}


def check_self_verify(problems):
    text = _read(SELF_VERIFY_OWNER)
    if text is None:
        problems.append(("MISSING FILE", SELF_VERIFY_OWNER, "the self-verify owner does not exist"))
        return
    body = text.split("### Design self-verify")[1] if "### Design self-verify" in text else ""
    # stop at the next h3 so a later section's bullets cannot be counted as items
    body = re.split(r"^### ", body, maxsplit=1, flags=re.M)[0]
    items = _ITEM.findall(body)

    if not items:
        problems.append(("NO ITEMS", SELF_VERIFY_OWNER,
                         "found no `- **(x)**` self-verify items — the parser or the format changed"))
        return

    dupes = sorted({i for i in items if items.count(i) > 1})
    if dupes:
        problems.append(("DUPLICATE ITEM", SELF_VERIFY_OWNER,
                         "self-verify letter(s) defined twice: {}".format(", ".join(dupes))))

    hdr = _HEADER.search(text)
    if not hdr:
        problems.append(("NO HEADER", SELF_VERIFY_OWNER,
                         "no `### Design self-verify (...)` header to check the list against"))
    else:
        claimed = _letters_in_range(hdr.group(1))
        plain = {i for i in items if len(i) == 1}
        if claimed is None:
            problems.append(("UNPARSEABLE RANGE", SELF_VERIFY_OWNER,
                             "header range {!r} is not an x-y span".format(hdr.group(1))))
        else:
            uncovered = sorted(plain - claimed)
            if uncovered:
                problems.append((
                    "HEADER RANGE STALE", SELF_VERIFY_OWNER,
                    "header claims ({}) but the list also defines {} — an agent sweeping the declared "
                    "range stops before {}".format(hdr.group(1), ", ".join("(%s)" % u for u in uncovered),
                                                   "(%s)" % uncovered[0])))
            phantom = sorted(claimed - plain)
            if phantom:
                problems.append((
                    "HEADER RANGE OVERCLAIMS", SELF_VERIFY_OWNER,
                    "header claims ({}) but {} are never defined".format(
                        hdr.group(1), ", ".join("(%s)" % p for p in phantom))))
        # a spelled-out count in the header must match too
        words = {"fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
                 "nineteen": 19, "twenty": 20, "twenty-one": 21}
        for w, n in words.items():
            if re.search(w, hdr.group(1), re.I) and n != len(items):
                problems.append(("HEADER COUNT WRONG", SELF_VERIFY_OWNER,
                                 "header says {} checks, the list defines {}".format(w.upper(), len(items))))

    defined = set(items)
    for rel, text2 in _corpus():
        for ref in set(_XREF.findall(text2)):
            if ref not in defined:
                problems.append(("DANGLING SELF-VERIFY REF", rel,
                                 "references self-verify ({}) — no such item in {}".format(
                                     ref, SELF_VERIFY_OWNER)))
    return len(items)


# ---------------------------------------------------------------- shared numeric agreements

# Each entry: (label, regex over the normalized text, the tuple every match MUST equal, why).
# The regex must capture the numbers so a drifted statement is reported with what it actually says.
SHARED = [
    ("form-family ceiling",
     re.compile(r"(\d{2})\s*[-–]\s*(\d{2})%\s*of\s*(?:the\s*)?content\s*slides"),
     ("40", "50"),
     "the Step-2 form-ledger gate, the critic, form-selection.md, review-rubrics.md and PRE-FLIGHT "
     "12(a) must name ONE band — a family inside the band needs the plan-time justification arm, and "
     "a tick using a narrower number fails decks the plan-time gate passed"),
    ("consecutive card/panel slides",
     re.compile(r"(?:no more than|More than)\s*(?:two|2)\s*consecutive\s*slides", re.I),
     None,   # presence-only: assert nobody states a different integer
     "the block-dependency audit's consecutive rule"),
]

_CONSEC_DRIFT = re.compile(r"no more than\s*(three|four|\d)\s*consecutive\s*slides", re.I)

# The drift that actually shipped was not a wrong BAND, it was a single number where the contract is
# a band: PRE-FLIGHT 12(a) read ">~40% of content slides" while eight other files read "~40-50%".
# A lone percentage against `content slides` is therefore itself the defect, whatever its value —
# but ONLY when it is talking about format families. `TITLE-RULE MONOCULTURE` legitimately fires at
# ">60% of content slides" and is a different rule; flagging it would make this check the kind of
# always-wrong report people learn to ignore, which is worse than no check.
_LONE_PCT = re.compile(r"[>≥]\s*~?(\d{2})%\s*of\s*(?:the\s*)?content\s*slides")
_FAMILY_CTX = re.compile(r"famil|format", re.I)


def check_shared_numbers(problems):
    checked = 0
    for label, rx, must, why in SHARED:
        if must is None:
            continue
        for rel, text in _corpus():
            for m in rx.finditer(text):
                checked += 1
                if m.groups() != must:
                    line = text[:m.start()].count("\n") + 1
                    problems.append((
                        "THRESHOLD DRIFT", "{}:{}".format(rel, line),
                        "{}: says {}-{}%, everywhere else says {}-{}% — {}".format(
                            label, m.group(1), m.group(2), must[0], must[1], why)))
    for rel, text in _corpus():
        for m in _LONE_PCT.finditer(text):
            if not _FAMILY_CTX.search(text[max(0, m.start() - 140):m.start()]):
                continue                      # a different rule's threshold, not the family ceiling
            checked += 1
            line = text[:m.start()].count("\n") + 1
            problems.append((
                "THRESHOLD DRIFT", "{}:{}".format(rel, line),
                "form-family ceiling stated as a single number (>~{}%) where the contract is the "
                "~40-50% BAND. A hard tick using the low end fails decks the plan-time gate passed, "
                "and the tick has no justification arm to absorb it.".format(m.group(1))))
        for m in _CONSEC_DRIFT.finditer(text):
            if m.group(1).lower() not in ("two", "2"):
                line = text[:m.start()].count("\n") + 1
                problems.append(("THRESHOLD DRIFT", "{}:{}".format(rel, line),
                                 "consecutive card/panel slides: says {}, the rule is two".format(m.group(1))))
    return checked


# ---------------------------------------------------------------- checkpoint owner completeness

# SKILL.md names references/checkpoint-convention.md as the owner of "the required columns and
# lines" and forbids composing a checkpoint from memory. A field the DESIGN checkpoint requires but
# the owner never lists is a field the author will not write, because the owner is what they read.
REQUIRED_CHECKPOINT_FIELDS = [
    ("boldness:", "the boldness dial"),
    ("signature move:", "the one scoped aesthetic risk"),
    ("carried_by", "the 2-3 slides where the signature idea does structural work"),
    ("logo plan:", "the logo evidence token"),
    # The per-image evidence tokens. Same reason the logo line is here: the sourcing DECISION is
    # what the user approves, and `design_plan.image_sources` (required by both gate paths) is the
    # same list read back later by check_image_provenance.py.
    ("image sources:", "the per-image evidence tokens"),
    ("entity marks:", "the roster slide's per-mark sourcing count"),
    ("interior register:", "the quiet cue that carries the style onto interior pages "
                           "(self-verify (q) - PRE-FLIGHT 6b - the critic's register_interiors check)"),
    ("density:", "the two planned density numbers (self-verify (r); the hand-off gate compares to them)"),
    ("direction gate:", "branch (c)'s recorded look-choice"),
    ("style gate:", "branch (d)'s recorded look-choice"),
    ("third-party assessment", "the logo row decided before the search, which a found logo cannot overturn"),
]


def check_checkpoint_owner(problems):
    text = _read(CHECKPOINT_OWNER)
    if text is None:
        problems.append(("MISSING FILE", CHECKPOINT_OWNER, "the checkpoint-spec owner does not exist"))
        return 0
    # Markdown wraps: `signature\nmove:` is the same field as `signature move:`. Collapsing
    # whitespace first is the difference between a check that reports drift and one that reports
    # line breaks — and a checker that cries wolf is a checker everyone learns to ignore.
    flat = " ".join(text.split())
    for field, why in REQUIRED_CHECKPOINT_FIELDS:
        if field not in flat:
            problems.append((
                "OWNER MISSING FIELD", CHECKPOINT_OWNER,
                "does not carry `{}` — {}. SKILL.md names this file the owner of the checkpoint's "
                "required lines and says never compose one from memory, so a field absent HERE is a "
                "field that does not get written.".format(field, why)))
    return len(REQUIRED_CHECKPOINT_FIELDS)


# ---------------------------------------------------------------- design_plan gate coverage

def check_design_plan_fields(problems):
    """Every field the hand-off gate REQUIRES must be named where the plan is written."""
    src = _read(os.path.join("scripts", "render_deck.py"))
    if src is None:
        src = ""
        try:
            with open(os.path.join(HERE, "render_deck.py"), encoding="utf-8") as fh:
                src = fh.read()
        except OSError:
            problems.append(("MISSING FILE", "scripts/render_deck.py", "cannot read the gate"))
            return 0
    m = re.search(r"DESIGN_FIELDS\s*=\s*\(([^)]*)\)", src, re.S)
    if not m:
        problems.append(("NO DESIGN_FIELDS", "scripts/render_deck.py",
                         "cannot find DESIGN_FIELDS — the gate's field list moved or was renamed"))
        return 0
    fields = re.findall(r'"([a-z_]+)"', m.group(1))
    skill = _read("SKILL.md") or ""
    for f in fields:
        if f not in skill:
            problems.append((
                "GATE FIELD UNDOCUMENTED", "SKILL.md",
                "`{}` is REQUIRED by render_deck.py --gate-check but is never named in SKILL.md — "
                "the author cannot write a field they are never told to plan.".format(f)))
    return len(fields)


# ---------------------------------------------------------------- runner

CHECKS = (
    ("self-verify integrity", check_self_verify),
    ("shared design thresholds", check_shared_numbers),
    ("checkpoint owner completeness", check_checkpoint_owner),
    ("design_plan gate coverage", check_design_plan_fields),
)


def run():
    problems = []
    counts = {}
    for name, fn in CHECKS:
        counts[name] = fn(problems)
    return problems, counts


def selftest():
    """A gate with no test regresses the same silent way the drift it catches does."""
    import copy
    fails = []

    def expect(desc, fn):
        problems = []
        fn(problems)
        if not problems:
            fails.append(desc)
        else:
            print("  ok   {} -> {}".format(desc, problems[0][0]))

    global REQUIRED_CHECKPOINT_FIELDS
    keep = copy.copy(REQUIRED_CHECKPOINT_FIELDS)
    REQUIRED_CHECKPOINT_FIELDS = keep + [("__no_such_field__", "a field nobody carries")]
    expect("checkpoint owner check can FAIL", check_checkpoint_owner)
    REQUIRED_CHECKPOINT_FIELDS = keep

    # a header that stops one letter short of the list must be caught
    text = ("### Design self-verify (a-b)\n"
            "- **(a)** one\n- **(b)** two\n- **(c)** three\n")
    problems = []
    items = _ITEM.findall(text)
    hdr = _HEADER.search(text)
    claimed = _letters_in_range(hdr.group(1))
    if sorted(set(items) - claimed) != ["c"]:
        fails.append("stale-range detection")
    else:
        print("  ok   stale header range detected -> (c) uncovered")

    # a drifted threshold must be caught
    m = SHARED[0][1].search("no one format-family on >~40-45% of content slides")
    if not m or m.groups() == ("40", "50"):
        fails.append("threshold drift detection")
    else:
        print("  ok   threshold drift detected -> {}-{}%".format(*m.groups()))

    if fails:
        print("SELFTEST FAILED: " + "; ".join(fails), file=sys.stderr)
        return 1
    print("selftest ok - every check can still fail")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify the design stack's cross-references and shared numbers.")
    ap.add_argument("--selftest", action="store_true",
                    help="prove each check can still FAIL (a gate that cannot fail is not a gate)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    try:
        problems, counts = run()
    except Exception as e:                      # NOT CHECKED is never the same as clean
        print("NOT CHECKED: {}: {}".format(type(e).__name__, e), file=sys.stderr)
        return 2

    print("checked {} self-verify items | {} shared-threshold statements | {} checkpoint fields "
          "| {} gate fields".format(*(counts[n] if counts[n] is not None else 0 for n, _ in CHECKS)))
    if not problems:
        print("clean - the design stack's indexes agree with each other and with the gate.")
        return 0
    print("\n{} design-contract problem(s):\n".format(len(problems)))
    for kind, where, why in problems:
        print("  [{}] {}\n      {}\n".format(kind, where, why))
    return 1


if __name__ == "__main__":
    sys.exit(main())
