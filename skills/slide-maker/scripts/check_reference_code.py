#!/usr/bin/env python3
"""Verify that every deckkit call taught in the skill's prose actually EXISTS.

Why this exists, measured: the shared references shipped four wrong API facts at once --
`dk.card(...)` (no such helper), `icon_tile(tile_color=...)` (the param is `fill=`), a pointer
to `references/deckkit-component-guide.md` (no such file), and a `role=content-critic` dispatch
contract that appears nowhere in the skill. Every one of them was prose, so nothing reported
them: the build crashes at the reader's desk, not in CI.

A rule about which helper to reach for is operational knowledge. Prose cannot enforce it and a
docstring cannot either -- only a check that fails can. This is that check.

  python3 scripts/check_reference_code.py            # lint the skill
  python3 scripts/check_reference_code.py --quiet    # errors only

Exit 0 clean · 1 findings · 2 could not run (never silently "clean").
"""
from __future__ import annotations

import argparse
import builtins
import ast
import inspect
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent

FENCE = re.compile(r"```python\n(.*?)```", re.S)
LINKED_MD = re.compile(r"`references/([A-Za-z0-9_.-]+\.md)`")
DK_ALIASES = {"dk", "deckkit"}


def load_deckkit():
    sys.path.insert(0, str(HERE))
    import deckkit  # noqa
    return deckkit


def md_files() -> list[Path]:
    out = [SKILL / "SKILL.md"]
    out += sorted((SKILL / "references").glob("*.md"))
    out += sorted((SKILL / "agents").glob("*.md"))
    return [p for p in out if p.is_file()]


# Helper names named in prose: `mute_for(bg)` or `dk.picture(...)`.
PROSE_CALL = re.compile(r"`([a-z_][a-z0-9_]*)\(")
DOTTED_CALL = re.compile(r"\b(?:dk|deckkit)\.([a-z_][a-z0-9_]*)\(")


def check_contract_card(dk, findings: list[str], stats: dict) -> None:
    """The CALL-SHAPE CONTRACTS block in `scripts/sigs.py` must name helpers that EXIST.

    This checker's scope was SKILL.md + references/*.md + agents/*.md — every prose file except
    the one whose entire job is stating correct call shapes. The contract card is a Python string
    inside a script, so it fell outside, and it told authors for a long time to

        "keep a token per ground and resolve by ground (`mute_for(bg)`, `on(fill)`)"

    while NEITHER function existed in deckkit. Following the contract card verbatim raised
    AttributeError. That is the same defect class this file was written for — a documented deckkit
    call that does not resolve — reached through a file extension nobody thought to include.
    """
    try:
        sys.path.insert(0, str(HERE))
        import sigs
    except Exception as exc:                       # never fail the whole run on an import
        findings.append(f"scripts/sigs.py: NOT CHECKED -> {exc.__class__.__name__}: {exc}")
        return
    card = getattr(sigs, "CONTRACTS", "")
    if not card:
        findings.append("scripts/sigs.py: CONTRACTS is empty or renamed — the contract card is "
                        "the highest-traffic call-shape documentation in the skill and it is now "
                        "unchecked")
        return
    names = set(PROSE_CALL.findall(card)) | set(DOTTED_CALL.findall(card))
    stats["contract_names"] = len(names)
    for n in sorted(names):
        if n.startswith("_") or hasattr(dk, n) or hasattr(builtins, n):
            continue
        findings.append(
            f"scripts/sigs.py (CONTRACTS): UNRESOLVED HELPER -> `{n}()` is taught by the "
            f"call-shape contract card but does not exist in deckkit. An author following the "
            f"card verbatim gets AttributeError."
        )


def fence_spans(text: str):
    """Yield (code, line_offset) for each ```python fence."""
    for m in FENCE.finditer(text):
        yield m.group(1), text[: m.start()].count("\n") + 1


def check_file(path: Path, dk, findings: list[str], stats: dict) -> None:
    text = path.read_text(encoding="utf-8")

    # ---- 1. dead reference pointers ------------------------------------------
    for m in LINKED_MD.finditer(text):
        target = SKILL / "references" / m.group(1)
        if not target.is_file():
            line = text[: m.start()].count("\n") + 1
            findings.append(
                f"{path.relative_to(SKILL)}:{line}: DEAD POINTER -> references/{m.group(1)} "
                f"does not exist"
            )

    # ---- 2. deckkit calls inside python fences --------------------------------
    for code, off in fence_spans(text):
        stats["fences"] += 1
        # A fence may be a fragment; make a best effort, and never fail the run on
        # unparseable pseudo-code -- just count it so a silent skip is visible.
        try:
            tree = ast.parse(code)
        except SyntaxError:
            stats["unparseable"] += 1
            continue

        # ---- 2a. the silent-no-op assignment that started this check ----------
        # `shape.fill.fore_color.alpha = ...` raises nothing, writes nothing, and yields a
        # 100% opaque shape. python-pptx ColorFormat has no alpha setter and no __slots__,
        # so the attribute is simply swallowed. Measured: it erased a full-bleed cover
        # plate to pure black (brightest pixel 0/765) while every lint passed green.
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AugAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Attribute) and t.attr == "alpha":
                    inner = t.value
                    if isinstance(inner, ast.Attribute) and inner.attr in {
                        "fore_color", "back_color"
                    }:
                        findings.append(
                            f"{path.relative_to(SKILL)}:{off + node.lineno - 1}: "
                            f"SILENT NO-OP -> `.{inner.attr}.alpha = ...` does nothing "
                            f"(python-pptx solid fills cannot carry alpha; the shape renders "
                            f"100% OPAQUE). Use deckkit.scrim_overlay() / a `grad=` fill, "
                            f"whose <a:alpha> is on the 0-100000 scale."
                        )

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)):
                continue
            if fn.value.id not in DK_ALIASES:
                continue

            name, line = fn.attr, off + node.lineno - 1
            stats["calls"] += 1
            target = getattr(dk, name, None)
            if target is None:
                findings.append(
                    f"{path.relative_to(SKILL)}:{line}: NO SUCH HELPER -> "
                    f"deckkit.{name}() does not exist"
                )
                continue
            if not callable(target):
                continue
            try:
                sig = inspect.signature(target)
            except (TypeError, ValueError):
                continue
            params = sig.parameters
            if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
                continue
            for kw in node.keywords:
                if kw.arg is None:
                    continue
                if kw.arg not in params:
                    ok = ", ".join(
                        n for n, p in params.items()
                        if p.kind is not inspect.Parameter.VAR_POSITIONAL
                    )
                    findings.append(
                        f"{path.relative_to(SKILL)}:{line}: BAD KEYWORD -> "
                        f"deckkit.{name}({kw.arg}=...) is not a parameter; accepts: {ok}"
                    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    try:
        dk = load_deckkit()
    except Exception as exc:                       # never report clean when it did not run
        print(f"NOT CHECKED - could not import deckkit: {exc}", file=sys.stderr)
        return 2

    findings: list[str] = []
    stats = {"fences": 0, "calls": 0, "unparseable": 0}
    files = md_files()
    for p in files:
        check_file(p, dk, findings, stats)
    check_contract_card(dk, findings, stats)

    if not args.quiet:
        print(
            f"checked {len(files)} markdown file(s) + the sigs.py contract card "
            f"({stats.get('contract_names', 0)} helper name(s)) · {stats['fences']} python "
            f"fence(s) · {stats['calls']} deckkit call(s)"
            + (f" · {stats['unparseable']} fence(s) unparseable (skipped)"
               if stats["unparseable"] else "")
        )
    for f in findings:
        print("  " + f)
    if findings:
        print(f"\n{len(findings)} finding(s) - the prose teaches an API that does not exist.")
        return 1
    if not args.quiet:
        print("clean - every documented deckkit call resolves against the real module.")
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
