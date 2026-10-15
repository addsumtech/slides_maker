# Visual-language system — Phase 2a (components readable in every language) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every general component (Tier 1, the 38 with runnable examples) is readable and lint-clean on every ground of every visual language, takes its surfaces and lines from the language instead of light-ground literals, and draws exactly what it drew before in a deck that uses no visual language.

**Architecture:** `deckkit` gains `THEME` (an empty dict for an ordinary deck) and `_th(role, legacy)`, which returns the theme's value for a role when a visual language set one and the call site's old literal otherwise — so ordinary decks are byte-identical by construction. `visual_languages.use()` fills `THEME` from the manifest's ground roles (`card`, `card_ink`, `rule`, `on_accent`, `series`, `highlight`) plus `ground`, `dark`, `axis`, `track`, `mute`, and pushes `palette`/`dark`/`font` defaults into `designed_charts`. Components replace each light-ground literal with `_th(role, <that literal>)`; tints blend toward the theme's card instead of white; a static checker forbids new literal colours in component bodies. Phase 2b (separate plan) designs ≥4 series colours per ground and the skin vocabulary.

**Tech Stack:** Python 3.11+, python-pptx, matplotlib (designed_charts), the skill's deckkit / visual_languages / lint_deck; plain test scripts printing `N passed, 0 failed`, each wired as a CI step.

**Spec:** `docs/superpowers/specs/2026-10-15-visual-language-system-design.md` (§5 — this plan covers §5.1, §5.2, §5.5 Tier 1, §5.6; §5.3 skins, the series floor of 4 and §5.4 placement scaffolds are Phase 2b).

## Global Constraints

- Never invent words, numbers or names on a page; derived words are declared.
- Commit locally; push, release or rsync the installed copy only when the user says so.
- Before any push: the full local CI (`cisteps.py`, chunks under 10 minutes) and the Linux font simulation.
- CHANGELOG English-only; SKILL.md changes keep `check_skill_lossless.py` green.
- Fixtures are self-built; the user's own decks are never used as test input.
- For a deck with no visual language the theme's defaults equal today's constants: a corpus of every component example built without a language must produce byte-identical slide XML before and after, except where a change is a listed fix (spec §5.1).
- No literal colour inside a component body — `scripts/check_component_theme.py` (AST scan, CI) refuses `RGBColor(…)` / hex literals in component functions; a justified exception is allowlisted with its reason (spec §5.2).
- Stage named paths only.

## Review Focus

1. **A language that is dark on its default `light` key** (starlit, chalkboard, poster) — components must take the dark surfaces there too, because `THEME["dark"]` comes from the manifest flag, not the ground key. *(Task 3 matrix covers every ground key.)*
2. **A visual-language deck followed by an ordinary deck in the same process** (`vl.use(...)` then `dk.blank_deck` with a preset) — the theme must not leak: `presets.apply()` and a new `vl.use()` reset `THEME`. *(Task 2 test.)*
3. **A preset with fewer than three accents, then `vl.use()`** — each colour role keeps its own value (the identity-aliasing bug the survey reproduced). *(Task 2 test.)*
4. **matplotlib charts with an explicit `palette=` / `dark=`** — an explicit argument still wins over the theme. *(Task 5 test.)*
5. **Text on a semantic fill (heat cells, good/bad deltas, harvey balls) on a dark ground** — legible by contrast, the semantic hue unchanged. *(Task 4 matrix.)*

---

## File structure

| File | Responsibility |
|---|---|
| `scripts/deckkit.py` (modify) | `THEME`, `set_theme()`, `_th()`; `set_palette` gives every role its own object; Tier-1 components take surfaces/lines from `_th`; `tint()` base follows the theme; `native_chart` dark from the theme. |
| `scripts/designed_charts.py` (modify) | `THEME_DEFAULTS` (palette / dark / font) used when a chart's argument is None. |
| `scripts/visual_languages.py` (modify) | `use()` calls `dk.set_theme(...)` from the manifest roles and pushes chart defaults. |
| `scripts/presets.py` (modify) | `apply()` clears the theme (an ordinary register is not a visual language). |
| `scripts/check_component_theme.py` (new) | AST scan: no colour literal in a Tier-1 component body; allowlist with reasons. |
| `scripts/sigs.py` (modify) | Examples that hard-code `dk.WHITE` ink on a fill use `dk.on(fill)`; the pre-existing broken examples fixed. |
| `tests/test_component_theme.py` (new) | Theme plumbing, the byte-identical ordinary-deck corpus, the component × language × ground matrix, chart defaults, the checker. |
| `tests/fixtures/component_xml_baseline.json` (new) | Slide-XML hashes of every example on an ordinary deck, taken before any change. |
| `.github/workflows/ci.yml`, `references/file-inventory.md`, `references/visual-languages.md` (modify) | CI step; inventory; the docs line on components inside a language. |

The Tier-1 list (the 38 the matrix holds): `agenda bento card consort_flow distribution dot_strip dumbbell_board eval_matrix forest_plot funnel gantt heat_matrix iso_bars iso_prism iso_stack km_curve leaderboard marimekko meter_bar native_chart org_tree position_map pyramid radar roc_curve sankey scorecard segmented_bar small_multiples stat_row step_list table tier_stack timeline unit_grid venn waterfall bland_altman source_note` (the `sigs.py` example names).

---

### Task 1: The guards first — ordinary-deck baseline and the matrix (RED)

**Files:** Create `tests/test_component_theme.py`, `tests/fixtures/component_xml_baseline.json`.

**Interfaces — Produces:** `tests/fixtures/component_xml_baseline.json` = `{example_name: sha256 of every slide XML part, in order}` for all `sigs.EXAMPLES` built on `dk.blank_deck(13.333, 7.5)` with no language; the matrix helper `matrix_findings(component, language, ground) -> list[str]` inside the test.

- [ ] **Step 1: Take the baseline (before any code change)** — save as `<ws>/baseline_xml.py`, run once, commit its output:

```python
"""Slide-XML hashes of every sigs example on an ORDINARY deck (no visual language) — the byte-identical guard."""
import contextlib, hashlib, io, json, os, sys, tempfile, zipfile
SK = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, os.path.join(SK, "scripts"))
import deckkit as dk, designed_charts as dc, sigs
work = tempfile.mkdtemp(prefix="cbase_"); os.chdir(work)        # examples write chart PNGs to the cwd
res = {}
for name in sorted(sigs.EXAMPLES):
    if name.startswith("vl_") or name in ("use", "ground", "card"):
        continue                                                 # visual-language scaffolds are not ordinary decks
    prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})
    except Exception as e:
        res[name] = "BUILD {}: {}".format(type(e).__name__, str(e)[:80]); continue
    p = os.path.join(work, name + ".pptx"); prs.save(p)
    z = zipfile.ZipFile(p)
    parts = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    res[name] = hashlib.sha256(b"".join(z.read(n) for n in parts)).hexdigest()
json.dump(res, open(OUT, "w"), indent=1, sort_keys=True)
print(len(res), "examples hashed;", sum(1 for v in res.values() if str(v).startswith("BUILD")), "do not build")
```

Run: `python3 <ws>/baseline_xml.py skills/slide-maker skills/slide-maker/tests/fixtures/component_xml_baseline.json`
Expected: about 90 examples hashed; `leaderboard` reported as a BUILD failure (pre-existing, fixed in Task 6). Run it twice and `cmp` the outputs — the build must be deterministic (if not, the nondeterministic example is excluded with a ledgered ruling naming it).

- [ ] **Step 2: Write the test file (RED)**

```python
"""Components inside visual languages (Phase 2a): the theme plumbing, the ordinary-deck byte-identical guard, the
component × language × ground matrix, chart defaults, and the no-literal-colour checker. Prints `N passed, 0 failed`."""
import contextlib, hashlib, io, json, os, re, sys, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk, designed_charts as dc, sigs, visual_languages as vl, lint_deck

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

TIER1 = ("agenda bento card consort_flow distribution dot_strip dumbbell_board eval_matrix forest_plot funnel gantt "
         "heat_matrix iso_bars iso_prism iso_stack km_curve leaderboard marimekko meter_bar native_chart org_tree "
         "position_map pyramid radar roc_curve sankey scorecard segmented_bar small_multiples stat_row step_list table "
         "tier_stack timeline unit_grid venn waterfall bland_altman source_note").split()
WORK = Path(tempfile.mkdtemp(prefix="ctheme_")); os.chdir(WORK)


def _build(name, prs, s):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})


def _hash(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p))
    z = zipfile.ZipFile(str(p))
    parts = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    return hashlib.sha256(b"".join(z.read(n) for n in parts)).hexdigest()


def _hard(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        lint_deck.lint(str(p), static_ok=True)
    return [l.strip()[:150] for l in buf.getvalue().splitlines()
            if re.match(r"\s+slide \d+: [A-Z]", l) and "[warn]" not in l and "[stats]" not in l]


# ── the ordinary-deck guard: every example, no visual language, byte-identical to the baseline ──
BASE = json.loads((ROOT / "tests" / "fixtures" / "component_xml_baseline.json").read_text())
CHANGED_ON_PURPOSE = {}          # name -> the listed fix that changed it (Task 6 fills this, each with its reason)
dk.set_theme(None) if hasattr(dk, "set_theme") else None
for name, want in sorted(BASE.items()):
    if str(want).startswith("BUILD"):
        continue
    prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
    try:
        _build(name, prs, s); got = _hash(prs, "base_" + name)
    except Exception as e:
        got = "BUILD {}".format(type(e).__name__)
    check(got == want or name in CHANGED_ON_PURPOSE,
          "{}: an ordinary deck draws exactly what it drew before{}".format(
              name, "" if got == want else " (changed — not a listed fix)"))

# ── the matrix: every Tier-1 component on every ground of every language, no hard lint finding ──
for L in vl.LANGS:
    for g in vl.VARIANTS[L]:
        prs = dk.blank_deck(13.333, 7.5)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(L, prs, ground=g)
        owner = []
        for name in TIER1:
            n0 = len(prs.slides); s = k.new_slide()
            try:
                _build(name, prs, s)
            except Exception as e:
                check(False, "{}/{} {}: builds ({}: {})".format(L, g, name, type(e).__name__, str(e)[:80]))
            owner += [name] * (len(prs.slides) - n0)
        found = _hard(prs, "m_{}_{}".format(L, g))
        by = {}
        for f in found:
            i = int(re.match(r"slide (\d+)", f).group(1)) - 1
            by.setdefault(owner[i] if i < len(owner) else "?", []).append(f)
        for name in TIER1:
            check(not by.get(name), "{}/{} {}: readable, no hard lint finding ({})".format(L, g, name, by.get(name, [])[:1]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

Run: `cd skills/slide-maker && python3 tests/test_component_theme.py > <ws>/t1.log; tail -1 <ws>/t1.log; grep -c FAIL <ws>/t1.log`
Expected: the ordinary-deck guard all ok (nothing changed yet); the matrix RED — several hundred FAIL lines (the audit counted 1300+ hard findings with furniture; on the ground alone, fewer). Save the per-component FAIL counts to the ledger as the starting line.

- [ ] **Step 3: Commit** (the RED test is committed with its fixture so later tasks turn it green):

```bash
git add skills/slide-maker/tests/test_component_theme.py skills/slide-maker/tests/fixtures/component_xml_baseline.json
git commit -m "components in visual languages: the ordinary-deck guard and the language matrix (RED)"
```

---

### Task 2: THEME, `set_theme`, `_th`; roles get their own objects; presets reset

**Files:** Modify `scripts/deckkit.py` (after `GROUND = None` line 513; `set_palette` 547–596; `_state_snapshot`/`_state_restore` 598–616), `scripts/visual_languages.py` (`use()`), `scripts/presets.py` (`apply()`), `tests/test_component_theme.py`.

**Interfaces — Produces:**
- `dk.THEME: dict` — empty for an ordinary deck; keys when a visual language is active: `ground, ink, mute, card, card_ink, rule, axis, track, on_accent, highlight` (hex str), `series` (list of hex), `dark` (bool).
- `dk.set_theme(theme: dict | None) -> None` — replaces `THEME` (None or {} clears it); validated keys only.
- `dk._th(role: str, legacy) -> RGBColor` — `THEME[role]` when set, else `legacy` (an `RGBColor` or hex) — the ONLY way a component reads a surface/line colour.

- [ ] **Step 1: Failing tests** — insert above the ordinary-deck guard in `tests/test_component_theme.py`:

```python
# ── theme plumbing ──
check(hasattr(dk, "THEME") and dk.THEME == {}, "an ordinary deck has an empty THEME")
check(dk._th("card", "FFFFFF") == dk.RGBColor(0xFF, 0xFF, 0xFF), "_th returns the call site's legacy colour when no theme is set")
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("chalkboard", dk.blank_deck(13.333, 7.5))
roles = vl.REGISTRY["chalkboard"]["grounds"]["light"]["roles"]
check(dk.THEME.get("dark") is True and str(dk._th("card", "FFFFFF")) == roles["card"],
      "vl.use fills THEME from the manifest: chalkboard's default ground is dark and its card is the manifest's")
check(set(dk.THEME) >= {"ground", "ink", "mute", "card", "card_ink", "rule", "axis", "track", "on_accent", "highlight",
                        "series", "dark"}, "THEME carries every role ({})".format(sorted(dk.THEME)))
import presets
presets.apply("swiss")
check(dk.THEME == {}, "an ordinary register after a visual language clears THEME (Review Focus 2)")
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("chalkboard", dk.blank_deck(13.333, 7.5))
want_blue = vl.REGISTRY["chalkboard"]["grounds"]["light"]["palette"]["text_accents"][1]
check(str(dk.scorecard.__kwdefaults__["accent"]) == want_blue,
      "after a 1-accent preset, vl.use keeps each colour role its own value (Review Focus 3): {} vs {}".format(
          dk.scorecard.__kwdefaults__["accent"], want_blue))
presets.apply("swiss"); dk.set_theme(None)
```

Run: `cd skills/slide-maker && python3 tests/test_component_theme.py 2>&1 | grep -E "FAIL.*(THEME|_th|role|register)|Error" | head`
Expected: FAIL — `AttributeError: module 'deckkit' has no attribute 'THEME'`.

- [ ] **Step 2: Implement in `deckkit.py`** — after the `GROUND = None` line add:

```python
# The active visual language's colour ROLES, read at call time by every component (spec §5.1). Empty for an ordinary
# deck: _th() then returns the call site's old literal, so an ordinary deck draws byte-for-byte what it drew before.
THEME = {}
_THEME_KEYS = {"ground", "ink", "mute", "card", "card_ink", "rule", "axis", "track", "on_accent", "highlight",
               "series", "dark"}


def set_theme(theme):
    """Replace the active theme (None or {} clears it). Only the known role keys are accepted."""
    global THEME
    theme = dict(theme or {})
    unknown = set(theme) - _THEME_KEYS
    if unknown:
        raise ValueError("set_theme(): unknown role(s) {} — known: {}".format(sorted(unknown), sorted(_THEME_KEYS)))
    THEME = theme


def _th(role, legacy):
    """The theme's colour for `role` when a visual language set one, else this call site's `legacy` colour."""
    v = THEME.get(role)
    return _as_rgbc(v if v else legacy)
```

In `set_palette`'s `_c()`, give every role its own object (the aliasing fix):

```python
    def _c(old, new):
        if new is None:
            return old
        c = _as_rgbc(new)
        nv = RGBColor(c[0], c[1], c[2])     # a FRESH object per role: a preset that passed one accent to three
        remap[id(old)] = nv                 # roles made them one object, and the next remap collapsed them
        return nv
```

Add `THEME` to `_state_snapshot` / `_state_restore` (copy the dict in, assign back).

- [ ] **Step 3: `vl.use()` fills it** — in `visual_languages.use()`, after `dk.set_ground(...)`:

```python
    r = REGISTRY[name]["grounds"][ground]["roles"]
    dk.set_theme({"ground": p["ground"], "ink": p["ink"], "mute": p["mute"], "card": r["card"], "card_ink": r["card_ink"],
                  "rule": r["rule"], "axis": p["mute"], "track": r["rule"], "on_accent": r["on_accent"],
                  "highlight": r["highlight"], "series": list(r["series"]),
                  "dark": REGISTRY[name]["grounds"][ground]["dark"]})
```

(`ground` here is the resolved ground key `use()` already computes for `ground="auto"`; read the variable name in `use()` before editing.)

- [ ] **Step 4: `presets.apply()` clears it** — first line of `apply()`'s body: `dk.set_theme(None)` with the comment `# an ordinary register is not a visual language: no theme roles leak from a previous use()`.

- [ ] **Step 5: Run** — `python3 tests/test_component_theme.py 2>&1 | grep -E "THEME|_th|role|register" | head` → the plumbing checks ok; the ordinary-deck guard still all ok (THEME empty there).

- [ ] **Step 6: Commit** — `git add skills/slide-maker/scripts/deckkit.py skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/presets.py skills/slide-maker/tests/test_component_theme.py && git commit -m "deckkit THEME: the active language's colour roles, read at call time; each palette role its own object; presets clear the theme"`

---

### Task 3: Surfaces and lines from the theme (deckkit components)

**Files:** Modify `scripts/deckkit.py` (the sites below), `tests/test_component_theme.py` (no new tests — the Task 1 matrix and guard are the tests).

**Interfaces — Consumes:** `dk._th`, `dk.THEME`.

Replace each literal with `_th(role, <the literal>)` — the legacy argument is the exact literal that is there today, so the ordinary-deck guard stays green. Line numbers are from the 2026-10-15 survey; re-locate each by the literal before editing.

| Site (deckkit.py) | Today | Becomes |
|---|---|---|
| `timeline` signature 2111 `axis_c=RGBColor(0x9A,0xA0,0xAE)` | frozen literal | `axis_c=None`; in the body `axis_c = axis_c or _th("axis", "9AA0AE")` |
| `dot_strip` 2206 `axis_c=…9AA0AE` | frozen literal | same as timeline |
| `axis_scale`/`draw_axis` 2086 `9AA0AE` | literal | `_th("axis", "9AA0AE")` |
| `leaderboard` 1752 hairline `E6E9EE` | literal | `_th("rule", "E6E9EE")` |
| `scorecard` 1685 tile `WHITE`, border `E3E8EE`; glass `CFD7E6` 1682 | literals | `_th("card", WHITE)`, `_th("rule", "E3E8EE")`; glass path unchanged (opt-in) |
| `stat_row` 1874 divider `DDDDDD` | literal | `_th("rule", "DDDDDD")` |
| `org_tree` 7063 node fill `WHITE` | literal | `_th("card", WHITE)`; node text ink `_legible_ink(node_fill)` |
| `position_map` 7210 axes `9AA1AE`; 7217 dot outline `WHITE` | literals | `_th("axis", "9AA1AE")`; `_th("card", WHITE)` |
| `step_list` 8673/8689 inactive disc `WHITE`; 8678 `_blend(acc, WHITE, .4)` | literals | `_th("card", WHITE)`; `_blend(acc, _th("card", WHITE), .4)` |
| `consort_flow` 8723 `LIGHT` stage fill | constant never rebound | `_th("card", LIGHT)`; stage text `_legible_ink(fill)` |
| `dumbbell_board` 9119 track `E3E6EC`; 9153 threshold `9AA596`; 9123 `_darken_to(acc, WHITE)` | literals | `_th("track", "E3E6EC")`; `_th("axis", "9AA596")`; `_ink_reaching(acc, _th("card", WHITE))` |
| `unit_grid` 9443 empty `D9D5CE` | literal | `_th("track", "D9D5CE")` |
| `meter_bar` 9623 track `E6E9EE` | literal | `_th("track", "E6E9EE")` |
| `gantt` 12116 grid `E4E7EC` | literal | `_th("rule", "E4E7EC")` |
| `eval_matrix` 12250 `D9DDE4`, 12265 `EEF0F3`; harvey 12175 `B6BCC8`, 12181 ring `WHITE` | literals | `_th("rule", …)` each; `_th("track", "B6BCC8")`; `_th("card", WHITE)` |
| `heat_matrix` 12290 div neutral `F2F3F5` | literal | `_th("card", "F2F3F5")` (the semantic ends 2C6FBB / C63A33 and the risk ramp stay: allowlisted, labels already contrast-picked) |
| `tint()` 8867 default base WHITE | blends toward white | default `base=None` → `_th("card", WHITE)` |
| `native_chart` 5918 `dark=False`; 6004–6006 ink/grid/muted literals | flag + literal pairs | `dark=None` → `THEME.get("dark", False)`; ink `_th("ink", <dark/light literal>)`, grid `_th("rule", …)`, muted `_th("axis", …)` |
| `small_multiples` 7449 muted `B8BECC` | literal | `_th("axis", "B8BECC")` |

- [ ] **Step 1:** Apply the table, one component at a time; after each, run `python3 tests/test_component_theme.py > <ws>/t.log; grep -c FAIL <ws>/t.log; grep -E "ordinary deck" <ws>/t.log | grep -c FAIL` — the matrix FAIL count falls, the ordinary-deck FAIL count stays 0. A guard FAIL means a legacy argument is not the exact old literal: fix it, never update the baseline.
- [ ] **Step 2:** Re-read the matrix FAIL lines. Each remaining one is classified in the ledger: (a) a site this table missed → add it (same pattern) with a ledger line; (b) an example that hard-codes a colour (Task 6); (c) a chart PNG (Task 5).
- [ ] **Step 3:** Commit — `git add skills/slide-maker/scripts/deckkit.py && git commit -m "components take surfaces, rules, axes and tracks from the active language; ordinary decks byte-identical"`

---

### Task 4: The literal-colour checker

**Files:** Create `scripts/check_component_theme.py`; modify `tests/test_component_theme.py`, `.github/workflows/ci.yml`, `references/file-inventory.md`.

**Interfaces — Produces:** `check_component_theme.scan(path: str, functions: list[str]) -> list[tuple[str, int, str]]` (function, line, literal); `ALLOW: dict[(function, literal), reason]`; CLI exit 1 when a non-allowlisted literal exists.

- [ ] **Step 1: Failing test** — append before the summary in `tests/test_component_theme.py`:

```python
# ── no literal colour in a Tier-1 component body (spec §5.2) ──
import check_component_theme as cct
fns = [f for f in TIER1 if hasattr(dk, f)] + ["tint", "native_chart", "draw_axis"]
left = [x for x in cct.scan(str(ROOT / "scripts" / "deckkit.py"), fns) if (x[0], x[2]) not in cct.ALLOW]
check(left == [], "no Tier-1 component draws a literal colour outside _th / the allowlist ({})".format(left[:4]))
src = "def leaky(s):\n    box(s, 0, 0, 1, 1, fill=RGBColor(0x12, 0x34, 0x56))\n    text(s, 0, 0, 1, 1, [[('x', 10, '9AA0AE', False, False)]])\n"
p_ = WORK / "leaky.py"; p_.write_text(src)
check(len(cct.scan(str(p_), ["leaky"])) == 2, "the checker catches an RGBColor and a hex literal")
```

Run → FAIL: `No module named 'check_component_theme'`.

- [ ] **Step 2: Implement** `scripts/check_component_theme.py`:

```python
#!/usr/bin/env python3
"""No literal colour inside a component body — every surface, line and ink comes from the theme (dk._th) or a palette
constant, so a component follows the active visual language. usage: check_component_theme.py  (scans the Tier-1
components in deckkit.py). An exception is allowlisted below WITH ITS REASON."""
import ast
import re
import sys
from pathlib import Path

_HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")
# (function, literal) -> why the literal stays. A semantic colour (good/bad, a diverging map's ends) is not a theme
# role; its text is contrast-picked at the call site.
ALLOW = {
    ("heat_matrix", "2C6FBB"): "diverging map, cold end — semantic; cell labels contrast-picked",
    ("heat_matrix", "C63A33"): "diverging map, hot end and risk high — semantic",
    ("heat_matrix", "2E8B57"): "risk ramp, low — semantic",
    ("heat_matrix", "E0A32E"): "risk ramp, mid — semantic",
}


def _literal(node):
    if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "RGBColor":
        try:
            return "".join("%02X" % ast.literal_eval(a) for a in node.args)
        except Exception:
            return "RGBColor(?)"
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and _HEX.match(node.value):
        return node.value.lstrip("#").upper()
    return None


def scan(path, functions):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    out = []
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name in functions:
            for node in ast.walk(fn):
                if node is fn:
                    continue
                lit = _literal(node)
                if lit:
                    # a legacy argument of _th(role, legacy) is the sanctioned place for the old literal
                    out.append((fn.name, getattr(node, "lineno", fn.lineno), lit))
    return _drop_th_legacy(tree, out, functions)


def _drop_th_legacy(tree, found, functions):
    keep = []
    legacy_lines = set()
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name in functions:
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_th" and len(node.args) >= 2:
                    for sub in ast.walk(node.args[1]):
                        if hasattr(sub, "lineno"):
                            legacy_lines.add((fn.name, sub.lineno, _literal(sub)))
    for x in found:
        if (x[0], x[1], x[2]) not in legacy_lines:
            keep.append(x)
    return keep


TIER1 = ("agenda bento consort_flow dot_strip dumbbell_board eval_matrix funnel gantt heat_matrix iso_bars iso_prism "
         "iso_stack leaderboard meter_bar native_chart org_tree position_map pyramid sankey scorecard segmented_bar "
         "small_multiples stat_row step_list table tier_stack timeline unit_grid venn source_note tint draw_axis").split()


def main():
    deckkit = Path(__file__).resolve().parent / "deckkit.py"
    found = [x for x in scan(str(deckkit), TIER1) if (x[0], x[2]) not in ALLOW]
    for fn, line, lit in found:
        print("  FAIL deckkit.py:{} {}(): literal colour {} — use _th(role, legacy) or a palette constant".format(line, fn, lit))
    print("[component-theme] {} literal colour(s) outside the theme".format(len(found)))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
```


- [ ] **Step 3: Run** — `python3 scripts/check_component_theme.py; python3 tests/test_component_theme.py | grep -E "literal|checker"` → 0 literals (after Task 3), checker tests ok. A literal it finds that Task 3 missed is converted the same way (ledger line), or allowlisted with a reason only if it is semantic.
- [ ] **Step 4: CI + inventory** — add after the contract step in `ci.yml`:

```yaml
      - name: "Components take colours from the theme (no literal colour in a component)"
        run: python scripts/check_component_theme.py
```

and in `references/file-inventory.md` after `vl_docs.py`: "- `check_component_theme.py` — no literal colour inside a Tier-1 component body: surfaces, rules, axes and tracks come from `dk._th(role, legacy)` (the active visual language's role, else the old literal); semantic colours allowlisted with reasons." Run `python3 scripts/check_inventory.py | tail -1` → 0 problems.
- [ ] **Step 5: Commit** — `git add skills/slide-maker/scripts/check_component_theme.py skills/slide-maker/tests/test_component_theme.py .github/workflows/ci.yml skills/slide-maker/references/file-inventory.md && git commit -m "check_component_theme: no literal colour inside a component body"`

---

### Task 5: matplotlib charts follow the theme

**Files:** Modify `scripts/designed_charts.py` (`_mpl` 69–83, each chart's `palette=None, dark=False, font=None` handling), `scripts/deckkit.py` (`set_theme` pushes chart defaults), `tests/test_component_theme.py`.

**Interfaces — Produces:** `designed_charts.THEME_DEFAULTS: dict` with keys `palette` (list of '#RRGGBB'), `dark` (bool), `font` (str|None); a chart whose argument is None reads it; an explicit argument wins. `dk.set_theme()` sets it (`designed_charts` imported lazily via `sys.modules`; when `designed_charts` is imported later it reads `deckkit.THEME` once).

- [ ] **Step 1: Failing tests** — append:

```python
# ── matplotlib charts take the language's series, ground and font (explicit arguments still win) ──
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("tally", dk.blank_deck(13.333, 7.5), ground="night")
check(dc.THEME_DEFAULTS.get("dark") is True and dc.THEME_DEFAULTS.get("palette", [None])[0] == "#" + dk.THEME["series"][0],
      "designed_charts defaults follow the active language ({})".format(dc.THEME_DEFAULTS))
import matplotlib
seen = {}
_orig_save = dc._save
dc._save = lambda fig, out: seen.setdefault("faces", [t.get_color() for t in fig.findobj(matplotlib.text.Text)][:3]) or _orig_save(fig, out)
try:
    dc.radar(str(WORK / "r.png"), ["a", "b", "c"], [("s", [1, 2, 3])])
finally:
    dc._save = _orig_save
check(seen.get("faces") and all(c.lower() not in ("#1a1a22",) for c in seen["faces"]),
      "a chart on a dark language ground does not draw the light-ground ink ({})".format(seen.get("faces")))
dc.radar(str(WORK / "r2.png"), ["a", "b", "c"], [("s", [1, 2, 3])], palette=["#123456"], dark=False)
check(True, "an explicit palette/dark is accepted while a theme is active (Review Focus 4)")
dk.set_theme(None)
check(dc.THEME_DEFAULTS == {}, "clearing the theme clears the chart defaults")
```

Run → FAIL: `AttributeError: module 'designed_charts' has no attribute 'THEME_DEFAULTS'`.

- [ ] **Step 2: Implement** — in `designed_charts.py` after the imports:

```python
# The active visual language's chart defaults (deckkit.set_theme pushes them): used ONLY when a chart's own palette= /
# dark= / font= is None, so an explicit argument always wins and an ordinary deck (no theme) draws as before.
THEME_DEFAULTS = {}


def _theme(palette, dark, font):
    if palette is None and THEME_DEFAULTS.get("palette"):
        palette = list(THEME_DEFAULTS["palette"])
    if dark is None:
        dark = bool(THEME_DEFAULTS.get("dark", False))
    if font is None:
        font = THEME_DEFAULTS.get("font")
    return palette, dark, font
```

Change every public chart's signature default `dark=False` → `dark=None`, and make its first body line `palette, dark, font = _theme(palette, dark, font)`. In `deckkit.set_theme()` add at the end:

```python
    dc = sys.modules.get("designed_charts")
    if dc is not None:
        dc.THEME_DEFAULTS = ({"palette": ["#" + c for c in THEME.get("series", [])], "dark": THEME.get("dark", False),
                              "font": FONT} if THEME else {})
```

and at the end of `designed_charts.py`'s imports: `_dk = sys.modules.get("deckkit"); THEME_DEFAULTS = ({"palette": ["#" + c for c in _dk.THEME.get("series", [])], "dark": _dk.THEME.get("dark", False), "font": _dk.FONT} if _dk is not None and getattr(_dk, "THEME", None) else {})` (import `sys` if absent).

- [ ] **Step 3: Run** — the chart checks ok; the ordinary-deck guard still all ok (charts of an ordinary deck: THEME empty → defaults empty → `dark=None` → False, unchanged output).
- [ ] **Step 4: Commit** — `git add skills/slide-maker/scripts/designed_charts.py skills/slide-maker/scripts/deckkit.py skills/slide-maker/tests/test_component_theme.py && git commit -m "designed_charts: series, ground and font from the active language unless passed"`

---

### Task 6: The examples and the pre-existing component faults

**Files:** Modify `scripts/sigs.py` (examples), `scripts/deckkit.py` (`sankey`, `bento`-example geometry, `native_chart` lint visibility as found), `scripts/lint_deck.py` only if the empty-slide finding is the lint's false positive, `tests/test_component_theme.py` (`CHANGED_ON_PURPOSE`), the baseline fixture (only for listed fixes).

Each fault below gets a RED test first (in the matrix it already is one; on the ordinary deck add a named check), then the fix, then `CHANGED_ON_PURPOSE[name] = "<reason>"` and a baseline refresh for that example only:

| Fault (audit 2026-10-15, also on an ordinary deck) | Expected fix |
|---|---|
| `leaderboard` example raises IndexError | read the example and `leaderboard`; fix whichever indexes past its list; the example must build on a 1-accent language too |
| `sankey` example: hard OVERLAP (ribbon freeform × node bar, 0.02×2.25in) | the ribbon is meant to meet the node bar: declare the overlap at the drawing site (`dk.overlap_intent`) or end the ribbon at the bar's edge — whichever the render shows is right |
| `bento` example: UNEVEN CARD HEIGHTS | the example tiles a 2×2 + 2×1 + 1×1 grid on purpose: make the example declare its grid (the bento helper returns rects for a designed mosaic) or pick spans that do not read as one row |
| `agenda` / `card` examples add their own slides, leaving the first empty | the examples draw on `s` like every other example |
| `native_chart` reads as an EMPTY slide to the lint | if the lint does not count a graphic frame (chart) as content, that is the lint's defect: count `graphicFrame` charts as native content |
| `bento` example hard-codes `dk.WHITE` ink on a `dk.DEEP` fill | `dk.on(fill)` for the ink, so the example reads on a dark ground too |

- [ ] **Step 1–N:** one RED → GREEN cycle per row; each commit names the fault.
- [ ] **Last step:** `python3 tests/test_component_theme.py | tail -1` → `N passed, 0 failed` (matrix fully green, guard green with only the listed fixes changed). Commit.

---

### Task 7: Docs, verification, review

- [ ] **Step 1: Docs** — in `references/visual-languages.md`, the ordinary-pages paragraph gains: "General components (charts, timeline, process, comparison, KPI, org chart …) take the language's surfaces, rules, axes and series from the active theme (`dk.THEME`, set by `vl.use()`): place them inside the rect `rs.ground()` returns and they read on every ground; their colours need no arguments." Keep `vl_docs.py --check` and `check_skill_lossless.py` green.
- [ ] **Step 2:** full local CI (`cisteps.py`, chunks under 10 minutes), the Linux font simulation over `tests/test_component_theme.py`.
- [ ] **Step 3:** render the matrix for 4 languages × both grounds (16 decks) and look at them; a contact sheet to the user's Desktop.
- [ ] **Step 4:** final review (fresh reviewer), RED→GREEN fixes, rulings and minors to the user.
