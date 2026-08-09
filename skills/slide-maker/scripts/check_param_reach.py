#!/usr/bin/env python3
"""Every keyword parameter a helper ACCEPTS must be READ somewhere in its body.

The defect class this closes is silent by construction. A component takes a parameter, documents
it, and never reads it — so the caller writes the call the docs describe, no exception is raised,
no lint fires, and the deck ships with the setting ignored. Three shipped instances, each found by
hand and each in a different file:

  * ``deckkit.gantt(accents=[...])``  — ignored for plain 3-tuple tasks, so every bar drew in
    deckkit's default blue. That silently violates SKILL.md's 🔴 "never ship deckkit's default
    blue", with no backstop anywhere in the tree.
  * ``anim.slide_transition(kind="push")`` — ``kind`` appeared exactly once in the file, in the
    signature; the body hardcoded ``<p:fade/>``. Every non-fade transition was a fade.
  * ``deckkit.native_bubble(xlabel=, ylabel=, point_labels=)`` — all three discarded, one of them
    documented in the docstring.

Whether a parameter is read is decidable by a program, so it belongs here rather than in prose.
The rule is deliberately weak — *mentioned anywhere in the body* — because the strong version
("actually affects the output") is undecidable and the weak one already catches every instance
above. False positives get a written waiver, never a loosened rule.

    python3 scripts/check_param_reach.py           # exit 0 clean · 1 findings · 2 cannot run
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Modules whose public helpers are called from build scripts — the surface where an ignored
# parameter reaches a slide.
TARGETS = ("deckkit.py", "anim.py", "designed_charts.py", "icons.py", "maps.py", "image_fx.py",
           "formats.py", "presets.py", "archetypes.py", "image_prompts.py")

# Parameters that are accepted and deliberately not read. Each needs a reason, so that an
# intentional no-op is a decision somebody recorded rather than the bug this file exists to find.
EXPECTED_UNREAD = {
    "deckkit.py:measure_timeline:events":
        "a timeline's HEIGHT is deliberately independent of how many events it carries — they are "
        "spaced along a fixed-height axis, and running out of room raises inside `timeline` rather "
        "than growing the band (its own docstring documents the polarity='alternate' escape). The "
        "argument is kept so the call mirrors `timeline(s, x, y, w, events, ...)`: a caller who "
        "has to drop it in one place and pass it in the other will eventually pass the wrong one. "
        "Verified against the component in tests/test_measure_contracts.py for all three branches "
        "(below 1.4 / alternate 2.7 / vertical h), which is what would catch this going stale.",
    "deckkit.py:vstack:slide":
        "every placing helper is fn(slide, x, y, ...); vstack only computes geometry and hands "
        "each block its own rect, so it never needs the slide. Dropping it would make one helper "
        "in the library take a different first argument than all the others.",
    "deckkit.py:icon_card:accent":
        "the icon PNG is recoloured upstream by icons.py (the docstring says so), and the card "
        "itself is deliberately neutral so a row of cards reads as one system. Kept so a caller "
        "can pass the deck accent through the same keyword every icon helper takes.",
    "deckkit.py:device_frame:accent":
        "the bezel is deliberately neutral — the screenshot inside it is the only coloured thing "
        "on the slide. Kept for call-compatibility with the other framing helpers; the docstring "
        "now says ACCEPTED AND CURRENTLY UNUSED rather than 'available for theming'.",
}

# Never interesting: conventional receivers and the catch-alls a wrapper forwards wholesale.
SKIP_NAMES = {"self", "cls"}


def params_of(fn):
    """Keyword-ish parameters worth checking: positional, positional-only and keyword-only.

    *args / **kwargs are excluded — a forwarding wrapper legitimately never names them, and they
    are not the shape that produces a silently-ignored setting.
    """
    a = fn.args
    out = []
    for node in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs):
        if node.arg not in SKIP_NAMES:
            out.append(node.arg)
    return out


def names_read(fn):
    """Every identifier LOADED anywhere in the body, including nested functions and comprehensions.

    Loads only: a parameter that is merely reassigned (``kind = "fade"``) and never read is exactly
    the bug, so a Store must not count as reaching it. Attribute and subscript bases are Name loads
    already, so ``ax.tick_labels`` and ``rows[i]`` are covered for free.
    """
    seen = set()
    body = list(fn.body)
    # skip the docstring: a parameter named only in prose is precisely the case we are hunting
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                seen.add(node.id)
            elif isinstance(node, ast.Call):
                # f(**opts) forwards everything; treat it as reading the whole local scope rather
                # than reporting every parameter of a wrapper that legitimately passes them on.
                for kw in node.keywords:
                    if kw.arg is None:
                        seen.add("**")
    return seen


def scan(path):
    rel = os.path.basename(path)
    try:
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    except SyntaxError as exc:
        print("cannot parse {}: {}".format(rel, exc), file=sys.stderr)
        return None
    findings = []
    for fn in tree.body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if fn.name.startswith("_"):
            continue
        read = names_read(fn)
        if "**" in read:                      # forwards a whole mapping — cannot decide, skip
            continue
        for p in params_of(fn):
            if p in read:
                continue
            key = "{}:{}:{}".format(rel, fn.name, p)
            if key in EXPECTED_UNREAD:
                continue
            findings.append((key, fn.lineno))
    return findings


def main():
    total, checked = [], 0
    for name in TARGETS:
        path = os.path.join(HERE, name)
        if not os.path.isfile(path):
            continue
        got = scan(path)
        if got is None:
            return 2
        checked += 1
        total.extend(got)
    if not total:
        print("checked {} module(s) — every accepted parameter is read by its own body."
              .format(checked))
        return 0
    print("{} accepted-but-unread parameter(s):\n".format(len(total)))
    for key, line in total:
        mod, fn, p = key.split(":")
        print("  {}:{}  {}(): `{}` is accepted and never read".format(mod, line, fn, p))
    print("\nEach is either a bug (the caller's setting is silently discarded) or a deliberate\n"
          "no-op — and if deliberate it needs a line in EXPECTED_UNREAD saying why, so the next\n"
          "reader can tell the two apart.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
