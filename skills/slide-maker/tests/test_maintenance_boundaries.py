#!/usr/bin/env python3
"""The negative contracts in references/maintenance-boundaries.md, asserted where a program can.

`check_skill_lossless.py` proves a refactor kept the BYTES. It cannot see two gates merged into
one, a warning promoted to an auto-fix, or a plan field trusted instead of re-tested — each of
which keeps every line of text and removes the property the text described. The lossless check
reports a perfect score while the skill gets worse.

This suite is the other half. It is deliberately small: only boundaries that are decidable
mechanically, so nothing here depends on someone remembering. The rest of the table stays prose
because a human has to read it.
"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

ok, bad = [], []
BOUNDARIES = ROOT / "references" / "maintenance-boundaries.md"


def _read(p):
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------- the file exists and is reachable
if BOUNDARIES.exists():
    ok.append("references/maintenance-boundaries.md exists")
else:
    bad.append("references/maintenance-boundaries.md is missing — the negative contracts are gone")
    print("\n".join("  FAIL " + x for x in bad))
    raise SystemExit(1)

skill = _read(ROOT / "SKILL.md")
if "maintenance-boundaries.md" in skill:
    ok.append("SKILL.md points at it, so a maintainer can find it without knowing it exists")
else:
    bad.append("nothing in SKILL.md names maintenance-boundaries.md — a reference with no live "
               "pointer is a deleted reference")

# ---------------------------------------------------------------- 1. the two lints stay separate
build_lint = _read(SCRIPTS / "deckkit.py")
render_lint = _read(SCRIPTS / "lint_deck.py")
if "def lint_layout(" in build_lint and "def lint(" in render_lint:
    ok.append("build-time lint_layout and render-time lint_deck.lint are still separate entry "
              "points (one reads the .pptx before a render is paid for; the other reads pixels)")
else:
    bad.append("one of the two lint entry points is gone — they answer questions that cannot be "
               "asked at the same moment")

if "renders_dir" in render_lint and "renders_dir" not in build_lint:
    ok.append("only the render-time lint takes a renders dir — the split is real, not nominal")
else:
    bad.append("the build/render lint split has blurred: both or neither read rendered pages")

# ---------------------------------------------------------------- 2. no auto-fix, anywhere
for name in ("lint_deck.py", "deckkit.py", "render_deck.py"):
    src = _read(SCRIPTS / name)
    if re.search(r'["\']--(fix|autofix|repair)["\']', src):
        bad.append(f"{name} accepts a --fix/--repair flag — a mechanical patch silently "
                   f"overwrites design intent and ships a worse page than the one it 'fixed'")
if not any("--fix" in b for b in bad):
    ok.append("no lint or gate exposes an auto-fix flag; findings name a remedy instead of "
              "applying one")

# Parsed, not grepped. A substring search matched a REMEDY MESSAGE containing `p.save(deck)` —
# the checker telling the author how to fix a CJK deck — and reported the checker as writing
# files. A test that fires on the text of its own advice is exactly the "cries wolf" failure the
# table above warns about, so this asks the AST for real calls.
import ast                                                   # noqa: E402

_saves = [n for n in ast.walk(ast.parse(render_lint))
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "save"]
if not _saves:
    ok.append("the render-time linter never writes the deck back — it reports, it does not edit "
              "(checked by parsing, since its own remedy text mentions p.save())")
else:
    bad.append(f"lint_deck.py makes {len(_saves)} .save() call(s); a checker that edits pages can "
               f"mask the defect it was asked to find")

# ---------------------------------------------------------------- 3. plan claims are re-tested
gate = _read(SCRIPTS / "render_deck.py")
for fn in ("_report_icon_waiver", "_report_palette_drift", "_report_form_reach",
           "_report_carried_by"):
    m = re.search(r"def %s\(([^)]*)\)" % fn, gate)
    if not m:
        bad.append(f"{fn} is gone — a plan claim lost its re-test against the built file")
    elif "pptx" not in m.group(1):
        bad.append(f"{fn} no longer takes the built .pptx, so it can only re-read the plan that "
                   f"made the claim")
if not any("_report_" in b for b in bad):
    ok.append("every plan claim that can be re-tested against the built .pptx still is "
              "(icon waiver · palette drift · form reach · carried_by)")

# ---------------------------------------------------------------- 4. gate vocabulary matches
sys.path.insert(0, str(SCRIPTS))
try:
    import codex_delivery_gate as _gate
    emitted = {"_".join(m.group(1).strip().lower().split())
               for m in re.finditer(r'["\']([A-Z][A-Z0-9 \-/&]{2,40}):', render_lint)}
    dead = sorted(n for n in _gate.STRICT_STATS if n not in emitted)
    strict_w = [c for c in getattr(_gate, "STRICT_WARNINGS", ())
                if "_".join(c.lower().split()) not in emitted]
    if dead or strict_w:
        bad.append("codex gate names codes the linter never emits: "
                   + ", ".join(dead + strict_w))
    else:
        ok.append("every codex-gate code name is a code lint_deck.py really emits — the gate "
                  "cannot believe it is enforcing something invisible")
except Exception as exc:
    bad.append(f"could not check the codex gate vocabulary: {type(exc).__name__}: {exc}")

# ---------------------------------------------------------------- 5. layer-1 knowledge stays put
for marker, what in (("Value→geometry mappers", "the component catalogue"),
                     ("PRE-FLIGHT", "the pre-flight checklist")):
    if marker in skill:
        ok.append(f"{what} is still inline in SKILL.md, where nothing reports its absence if it "
                  f"moves")
    else:
        bad.append(f"{what} is no longer in SKILL.md — content with no backstop must not move to "
                   f"layer 2")

# ---------------------------------------------------------------- 6. the table itself is intact
table = _read(BOUNDARIES)
rows = [l for l in table.splitlines() if l.startswith("| **Do") or
        (l.startswith("| **") and l.count("|") >= 3)]
if len(rows) >= 8:
    ok.append(f"the boundary table still carries {len(rows)} contracts")
else:
    bad.append(f"the boundary table has shrunk to {len(rows)} rows — removing a contract is a "
               f"decision that belongs in its own commit with a reason")

if all(len(l.split("|")[2].strip()) > 80 for l in rows):
    ok.append("every contract still explains WHY — a rule reduced to a bare imperative degrades "
              "into pattern-matching and fails on the case it was written for")
else:
    bad.append("a boundary has lost its rationale")

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print(f"\n{len(ok)} passed, {len(bad)} failed")
raise SystemExit(1 if bad else 0)
