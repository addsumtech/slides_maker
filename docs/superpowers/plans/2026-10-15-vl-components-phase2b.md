# Visual-language components, Phase 2b — designed series, skins, placement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every language ground carries four designed series colours. The 15 Tier-2 components draw their cards, rules, markers and numerals in the language's skin. Every Tier-1 component has a placed scaffold (`sigs.py --example X --in L`) that runs inside the language's content rect on 16:9 and 3:4.

**Architecture:** A plain-data module (`component_tiers.py`) holds the tiers and the skin vocabulary, so docs, gates and deckkit share one source. Each manifest declares `skin = {card, rule, marker, number}`. `vl.use()` carries it in `dk.THEME` with the language's type floor. Four deckkit helpers draw a role in the active skin and take the call site's own draw as `legacy`. With no theme, or with the default value, they call `legacy()` and nothing else, so ordinary decks stay byte-identical. Series colours are designed per ground, shown to the user on a sheet, and land in the manifests only after approval (🔴 Task 9).

**Tech Stack:** python-pptx, matplotlib (designed_charts), LibreOffice + pdftoppm for the sheet, the repo's own gates (`lint_deck`, `vl_contract`, `check_component_theme`, `vl_docs`).

**Spec:** `docs/superpowers/specs/2026-10-15-visual-language-system-design.md` (§4.1 series floor ruling, §5.2–§5.6, §8). Phase 2a: `docs/superpowers/plans/2026-10-15-vl-components-phase2a.md` (branch `vl-components-p2a`; this plan stacks on it as `vl-components-p2b`).

## Global Constraints

- Never invent words, numbers or names on a page; derived words are declared.
- Commit locally; push, release or rsync the installed copy only when the user says so.
- Before any push: the full local CI (`cisteps.py`, chunks under 10 minutes) and the Linux font simulation.
- Codex usage: the single limited run of Phase 4 only (none here).
- CHANGELOG English-only; SKILL.md changes keep `check_skill_lossless.py` green.
- Fixtures are self-built; the user's own decks are never used as test input.
- Ordinary decks (no visual language) draw byte-identically: `tests/test_component_theme.py`'s guard (baseline from 76d0cfe, 76 examples) stays green; a changed example is a LISTED change with its exact new hash.
- Stage named paths only; identity dong845 <ldh199803@gmail.com>; never `git -c`.

## Review Focus

1. **An explicit colour argument under a non-filled skin.** For example `org_tree(accent=…)` on ink's `hairline` card. Text inside must be chosen against the surface the skin really leaves (the ground, not the accent fill), so it stays readable. Test: Task 3, step 1.
2. **CJK numerals under a `display`/`mono` number skin.** `step_list(numeral_style="cjk")` must keep a face that has 一二三, not switch to a Latin numeral face (tofu). Test: Task 2, step 1.
3. **A component wider than the 3:4 content rect.** It must fail loudly with the minimum width it needs, never overflow silently. Test: Task 6, step 1.
4. **Poster's per-page field switch.** It must keep the skin and the floor (`_poster_ground` rebuilds THEME). Test: Task 1, step 1.
5. **Running the scaffold exactly as `sigs.py --example X --in L` prints it**, in a fresh process (how a non-Claude agent uses it). It must build a deck with no hard lint finding. Test: Task 6, step 1.

---

## File Structure

| file | change | responsibility |
|---|---|---|
| `scripts/component_tiers.py` | create | plain data: `TIER1` (38), `TIER2_SKIN` (15 → roles), `SKIN_VOCAB`, `SKIN_DEFAULT` |
| `scripts/deckkit.py` | modify | THEME keys `skin`, `floor`; `_skin`, `_skin_card`, `skin_card`, `_skin_rule`, `_skin_marker`, `_skin_number_face`, `_fl`; Tier-2 call sites routed |
| `scripts/vl_specs/*.py` (15) | modify | `skin` per language (Task 1); `series` ≥ 4 per ground (Task 10, after approval) |
| `scripts/vl_contract.py` | modify | `skin` required + values from the vocabulary; `SERIES_MIN = 4` (Task 10) |
| `scripts/visual_languages.py` | modify | `use()` puts `skin` and `floor` in THEME |
| `scripts/vl_native.py` | modify | none needed (`_poster_ground` copies THEME) — pinned by a test |
| `scripts/sigs.py` | modify | `placed_example(name, lang, ground=None)`, `--in`/`--ground` flags, the vl-only preamble, agenda example |
| `scripts/check_component_theme.py` | modify | its TIER1 list from `component_tiers` |
| `scripts/vl_docs.py` | modify | blocks `tier1-list`, `tier2-table`, `skin-table` |
| `references/visual-languages.md` | modify | carry the three blocks; skin + placement paragraphs |
| `tests/test_component_skin.py` | create | helper unit tests, skin-reaches-drawing matrix, number/CJK, floors |
| `tests/test_component_theme.py` | modify | TIER1 from `component_tiers`; matrix from placed scaffolds on 16:9 and 3:4; PLACEMENT_2B removed |
| `.github/workflows/ci.yml` | modify | run `tests/test_component_skin.py` |

---

### Task 1: Skin plumbing — vocabulary, manifests, THEME, helpers

**Files:**
- Create: `scripts/component_tiers.py`, `tests/test_component_skin.py`
- Modify: `scripts/deckkit.py` (THEME block ~line 515; helpers after `_th`), `scripts/visual_languages.py` (`use()` ~line 245), `scripts/vl_contract.py` (`TOP_KEYS`, `validate`), `scripts/vl_specs/*.py` (15 files), `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `component_tiers.TIER1: tuple[str]`, `TIER2_SKIN: dict[str, tuple[str]]`, `SKIN_VOCAB: dict[str, tuple[str]]`, `SKIN_DEFAULT: dict[str, str]`.
- Produces: `dk.SKIN_TAG = "deckkit-skin:"` and `dk._skin(role) -> str`.
- Produces: `dk._skin_card(slide, x, y, w, h, *, fill, legacy, emphasis=False) -> RGBColor` (the surface text sits on) and `dk.skin_card(slide, x, y, w, h, *, fill=None, emphasis=False) -> RGBColor`.
- Produces: `dk._skin_rule(slide, p0, p1, *, color, width, legacy) -> None`.
- Produces: `dk._skin_marker(slide, cx, cy, d, label, *, fill, ink, size, face=None, legacy) -> None`.
- Produces: `dk._skin_number_face(value, face) -> str|None` and `dk._fl(pt) -> float`.
- THEME gains `skin: dict` and `floor: float`.

- [ ] **Step 1: Write the failing tests** — `tests/test_component_skin.py` (same `check()`/summary idiom as `test_component_theme.py`):

```python
"""The skin layer (Phase 2b): vocabulary, manifests, THEME, the four helpers, and that a skin reaches the drawing.
Prints `N passed, 0 failed`."""
import contextlib, io, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk, visual_languages as vl, component_tiers as ct, vl_specs, vl_contract

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)
WORK = Path(tempfile.mkdtemp(prefix="cskin_")); os.chdir(WORK)

def _use(L, g=None, W=13.333, H=7.5):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(L, prs, ground=g) if g else vl.use(L, prs)
    return prs, k

def _names(slide):
    return [sh.name for sh in slide.shapes]

# vocabulary and manifests
check(set(ct.SKIN_VOCAB) == {"card", "rule", "marker", "number"}, "the skin has four roles")
check(all(ct.SKIN_DEFAULT[r] in ct.SKIN_VOCAB[r] for r in ct.SKIN_VOCAB), "each default is in its vocabulary")
check(len(ct.TIER1) == 38 and set(ct.TIER2_SKIN) <= set(ct.TIER1) | {"bento"}, "38 Tier-1, Tier-2 drawn from them")
S = vl_specs.load()
check(all(set(S[n]["skin"]) == set(ct.SKIN_VOCAB) and all(S[n]["skin"][r] in ct.SKIN_VOCAB[r] for r in ct.SKIN_VOCAB)
          for n in S), "every manifest declares a skin value for every role, from the vocabulary")
bad_spec = dict(S["ink"], skin=dict(S["ink"]["skin"], card="velvet"))
check(any("skin" in p and "velvet" in p for p in vl_contract.validate(bad_spec)), "the contract refuses a value outside the vocabulary")
# THEME carries skin and floor; poster's field switch keeps them
prs, k = _use("chalkboard")
check(dk.THEME.get("skin") == S["chalkboard"]["skin"] and dk.THEME.get("floor") == 10, "vl.use puts skin and floor in THEME")
prs, k = _use("poster")
for _ in range(3):
    k.new_slide()
check(dk.THEME.get("skin") == S["poster"]["skin"] and dk.THEME.get("floor"), "poster's per-page field keeps skin and floor (Review Focus 4)")
dk.blank_deck(13.333, 7.5)
check(dk._skin("card") == "filled" and dk._fl(7) == 7, "an ordinary deck: default skin, no floor")
# each helper: the default value calls legacy() and nothing else; every other value draws tagged shapes
for role, values in ct.SKIN_VOCAB.items():
    for v in values:
        prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
        dk.set_theme({"ground": "F4EFE6", "ink": "1B1B1B", "mute": "5A5A55", "card": "EAE3D6", "card_ink": "1B1B1B",
                      "rule": "C9C0AE", "axis": "5A5A55", "track": "C9C0AE", "on_accent": "FFFFFF",
                      "highlight": "B23A28", "series": ["B23A28"], "dark": False,
                      "skin": dict(ct.SKIN_DEFAULT, **{role: v}), "floor": 9})
        called = []
        legacy = lambda: called.append(1) or dk.box(s, 1, 1, 1, 1, fill=dk.TINT)
        if role == "card":
            surf = dk._skin_card(s, 1, 1, 2, 1, fill=dk.RGBColor(0xB2, 0x3A, 0x28), legacy=legacy)
            check(isinstance(surf, dk.RGBColor), "card {} returns the surface colour".format(v))
        elif role == "rule":
            dk._skin_rule(s, (1, 1), (3, 1), color=dk.RGBColor(0x5A, 0x5A, 0x55), width=1.0, legacy=legacy)
        elif role == "marker":
            dk._skin_marker(s, 2, 2, 0.42, "3", fill=dk.RGBColor(0xB2, 0x3A, 0x28), ink=dk.RGBColor(0xFF, 0xFF, 0xFF),
                            size=14, legacy=legacy)
        else:
            continue
        if v == ct.SKIN_DEFAULT[role]:
            check(called == [1] and len(s.shapes) == 1, "{} {}: the default draws exactly the call site's own shape".format(role, v))
        else:
            check(called == [] and any(n.startswith(dk.SKIN_TAG + role + ":" + v) for n in _names(s)),
                  "{} {}: draws its own shapes, tagged ({})".format(role, v, _names(s)[:3]))
dk.set_theme(None)
# number: display/mono pick a lining face; a CJK numeral keeps a face that has it (Review Focus 2)
dk.set_theme({"ground": "F4EFE6", "ink": "1B1B1B", "mute": "5A5A55", "card": "EAE3D6", "card_ink": "1B1B1B",
              "rule": "C9C0AE", "axis": "5A5A55", "track": "C9C0AE", "on_accent": "FFFFFF", "highlight": "B23A28",
              "series": ["B23A28"], "dark": False, "skin": dict(ct.SKIN_DEFAULT, number="display"), "floor": 9})
f = dk._skin_number_face("42", None)
check(f is not None and not dk.has_oldstyle_figures(f), "a display number skin gives digits a lining face ({})".format(f))
check(dk._skin_number_face("三", "PingFang SC") == "PingFang SC", "a CJK numeral keeps the caller's face (Review Focus 2)")
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py`
Expected: `ModuleNotFoundError: No module named 'component_tiers'`

- [ ] **Step 3: Write `scripts/component_tiers.py`**

```python
"""Which general components wear a visual language, and how far (spec §5.5) — plain data, no deckkit import, so docs
and gates read it without building anything.

TIER1: every general component is held to every ground of every language (theme colours, readable, placed).
TIER2_SKIN: the components that also draw their containers, rules, markers and numerals in the language's SKIN, and
which of those roles each one draws. SKIN_VOCAB: the values a manifest may pick per role (spec §5.3); a value is
implemented once in deckkit and reused by every language that picks it. A new language picks from here and adds a
value only when none fits."""

TIER1 = ("agenda bento consort_flow distribution dot_strip dumbbell_board eval_matrix forest_plot funnel gantt "
         "heat_matrix iso_bars iso_prism iso_stack km_curve leaderboard marimekko meter_bar native_chart org_tree "
         "position_map pyramid radar roc_curve sankey scorecard segmented_bar small_multiples stat_row step_list table "
         "tier_stack timeline unit_grid venn waterfall bland_altman source_note").split()
TIER1 = tuple(TIER1)

TIER2_SKIN = {
    "bento": ("card",),                     # through dk.skin_card — bento returns the rects, the caller draws them
    "step_list": ("marker", "rule", "number"),
    "timeline": ("rule", "marker", "number"),
    "agenda": ("rule", "number"),
    "stat_row": ("rule", "number"),
    "org_tree": ("card", "rule"),
    "tier_stack": ("card", "rule"),
    "funnel": ("card", "rule"),
    "pyramid": ("card", "rule"),
    "venn": ("rule",),
    "meter_bar": ("rule", "number"),
    "gantt": ("rule", "number"),
    "table": ("rule", "number"),
    "native_chart": ("rule", "number"),
    "heat_matrix": ("number",),
}

SKIN_VOCAB = {
    "card": ("filled", "outlined", "hairline", "window", "sign", "chalk", "paper"),
    "rule": ("solid", "hairline", "dashed", "chalk"),
    "marker": ("disc-number", "dot", "roundel", "circled", "badge"),
    "number": ("body", "display", "mono"),
}
SKIN_DEFAULT = {"card": "filled", "rule": "solid", "marker": "disc-number", "number": "body"}
```

- [ ] **Step 4: Manifests** — add a top-level `'skin'` entry to each of the 15 `scripts/vl_specs/<name>.py` `SPEC` dicts, after `'look'`. These are the proposal shown on the Task 9 sheet:

| language | card | rule | marker | number |
|---|---|---|---|---|
| editorial | hairline | hairline | dot | display |
| soft | filled | solid | disc-number | body |
| collage | paper | solid | badge | display |
| storybook | paper | hairline | circled | display |
| ink | hairline | hairline | circled | display |
| poster | filled | solid | disc-number | display |
| cutpaper | paper | solid | disc-number | display |
| drafting | outlined | dashed | circled | mono |
| starlit | outlined | hairline | dot | display |
| broadsheet | hairline | hairline | dot | display |
| journal | hairline | hairline | dot | body |
| tally | filled | solid | badge | mono |
| chalkboard | chalk | chalk | circled | display |
| interface | window | hairline | badge | body |
| wayfinding | sign | solid | roundel | body |

Each is written as, e.g. for ink: `'skin': {'card': 'hairline', 'rule': 'hairline', 'marker': 'circled', 'number': 'display'},`

- [ ] **Step 5: Contract** — in `scripts/vl_contract.py` add `"skin"` to `TOP_KEYS` and, in `validate(spec)` after the type checks:

```python
    import component_tiers as _ct
    sk = spec.get("skin")
    if not isinstance(sk, dict) or set(sk) != set(_ct.SKIN_VOCAB):
        probs.append("{}: skin must name one value per role {} (got {!r})".format(name, sorted(_ct.SKIN_VOCAB), sk))
    else:
        for role, v in sk.items():
            if v not in _ct.SKIN_VOCAB[role]:
                probs.append("{}: skin {} {!r} is not in the vocabulary {} — pick one, or add the value to "
                             "component_tiers.SKIN_VOCAB and implement it in deckkit".format(
                                 name, role, v, list(_ct.SKIN_VOCAB[role])))
```

- [ ] **Step 6: THEME keys and helpers** — in `scripts/deckkit.py`:
  - Extend `_THEME_KEYS` with `"skin", "floor"`.
  - In `set_theme`, after the unknown-key check, validate the skin:

```python
    sk = theme.get("skin")
    if sk is not None:
        import component_tiers as _ct
        bad_v = {r: v for r, v in sk.items() if r not in _ct.SKIN_VOCAB or v not in _ct.SKIN_VOCAB[r]}
        if bad_v:
            raise ValueError("set_theme(): skin value(s) outside the vocabulary: {}".format(bad_v))
```

  Then, after `_th`, add:

```python
SKIN_TAG = "deckkit-skin:"   # names the shapes a skin value drew: `deckkit-skin:<role>:<value>` (tests and lint read it)


def _skin(role):
    """The active language's skin value for `role` ('card' | 'rule' | 'marker' | 'number'); the default without one."""
    import component_tiers as _ct
    return (THEME.get("skin") or {}).get(role) or _ct.SKIN_DEFAULT[role]


def _tag_new(slide, n0, role, value):
    """Name every shape added since `n0` by the skin — a primitive's own deckkit-* name (an overlap declaration, a
    decoration tag) is kept."""
    for sh in list(slide.shapes)[n0:]:
        if not str(sh.name).startswith("deckkit-"):
            sh.name = "{}{}:{}".format(SKIN_TAG, role, value)


def _fl(pt):
    """A component's type size, never below the active language's floor (spec §5.2). An ordinary deck: unchanged."""
    f = THEME.get("floor")
    return max(pt, f) if f else pt


def _skin_card(slide, x, y, w, h, *, fill, legacy, emphasis=False):
    """A component's container in the language's CARD skin. `legacy()` draws the call site's own box: an ordinary
    deck and a 'filled' language get exactly that. Returns the colour text inside sits on, so the caller picks its
    ink against what the skin really left there (an outlined card leaves the ground, not the fill). `emphasis` marks a
    container whose fill IS the message (an org chart's root, a funnel band): line-only skins draw it in that colour."""
    import native_art as na
    v = _skin("card")
    ground = _th("ground", WHITE)
    fill_c = _as_rgbc(fill) if fill is not None else None
    if v == "filled":
        legacy()
        return fill_c if fill_c is not None else ground
    n0 = len(slide.shapes)
    card = _th("card", WHITE)
    rule = _th("rule", RGBColor(0xD9, 0xDD, 0xE4))
    accent = fill_c if (emphasis and fill_c is not None) else None
    if v == "outlined":
        box(slide, x, y, w, h, fill=None, line=accent or _on_surface(rule, ground, 3.0),
            line_w=(1.8 if accent else 1.2) * RULE_W_SCALE, round=True, r=0.06)
        surf = ground
    elif v == "hairline":
        c = accent or _on_surface(rule, ground, 3.0)
        connector(slide, (x, y), (x + w, y), color=c, width=(1.6 if accent else 0.75), arrow=False)
        connector(slide, (x, y + h), (x + w, y + h), color=c, width=0.75, arrow=False)
        surf = ground
    elif v == "window":
        f = accent or card
        na.ui_window(slide, x, y, w, h, fill=str(f), line=str(_on_surface(rule, ground, 1.5)),
                     drop=str(_blend(ground, _th("ink", DEEP), 0.10)), r=0.12)
        surf = f
    elif v == "sign":
        f = accent or card
        na.sign_panel(slide, x, y, w, h, fill=str(f), keyline=str(_on_surface(rule, f, 3.0)), r=0.10)
        surf = f
    elif v == "chalk":
        na.chalk_box(slide, x, y, w, h, str(accent or _th("ink", WHITE)), seed=int(x * 7 + y * 13) % 97)
        surf = ground
    else:                                                   # paper
        f = accent or card
        na.paper_card(slide, x, y, w, h, fill=str(f), r=0.10)
        surf = f
    _tag_new(slide, n0, "card", v)
    return surf


def skin_card(slide, x, y, w, h, *, fill=None, emphasis=False):
    """A card in the active visual language's skin (paper, chalk, sign, window, hairline …) — for the cells
    `bento()` returns and any container you draw yourself. An ordinary deck draws `box(..., fill=fill)`. Returns the
    colour the card leaves under its text: pick ink with `dk.on(surface)`."""
    return _skin_card(slide, x, y, w, h, fill=fill, emphasis=emphasis,
                      legacy=lambda: box(slide, x, y, w, h, fill=fill))


def _skin_rule(slide, p0, p1, *, color, width, legacy):
    """A component's rule / connector / divider in the language's RULE skin. `legacy()` draws the call site's own
    line (a thin box, a connector, an hrule): an ordinary deck and a 'solid' language get exactly that."""
    import native_art as na
    v = _skin("rule")
    if v == "solid":
        legacy()
        return
    n0 = len(slide.shapes)
    if v == "hairline":
        connector(slide, p0, p1, color=color, width=max(0.5, width * 0.5), arrow=False)
    elif v == "dashed":
        connector(slide, p0, p1, color=color, width=max(0.75, width), arrow=False, style="dashed")
    else:                                                   # chalk
        na.chalk_path(slide, [p0, p1], str(_as_rgbc(color)), w=max(1.4, width * 1.4),
                      seed=int(p0[0] * 11 + p0[1] * 5) % 97)
    _tag_new(slide, n0, "rule", v)


def _skin_marker(slide, cx, cy, d, label, *, fill, ink, size, face=None, legacy):
    """A component's marker (a step's numbered disc, an event dot) in the language's MARKER skin. `legacy()` draws
    the call site's own disc. `label` None = a bare marker. The label's ink is chosen against what it sits on."""
    import native_art as na
    v = _skin("marker")
    if v == "disc-number":
        legacy()
        return
    n0 = len(slide.shapes)
    ground = _th("ground", WHITE)
    f = _as_rgbc(fill)
    if v == "dot":
        if label is None:
            box(slide, cx - d * 0.3, cy - d * 0.3, d * 0.6, d * 0.6, fill=f, round=True, r=d * 0.3)
        else:
            text(slide, cx - d, cy - d / 2, d * 2, d, [[(str(label), size, _on_surface(f, ground), True, False, face)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    elif v == "roundel":
        na.roundel(slide, cx, cy, d, str(label) if label is not None else "", fill=str(f),
                   ink=str(_legible_ink(f)), size=size, face=face or FONT)
    elif v == "circled":
        box(slide, cx - d / 2, cy - d / 2, d, d, fill=None, line=_on_surface(f, ground, 3.0), line_w=1.4,
            round=True, r=d / 2)
        if label is not None:
            text(slide, cx - d / 2, cy - d / 2, d, d, [[(str(label), size, _on_surface(f, ground), True, False, face)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    else:                                                   # badge
        bw = d if label is None else max(d, _natural_width_in([(str(label), True)], size, face) + 0.18)
        box(slide, cx - bw / 2, cy - d * 0.4, bw, d * 0.8, fill=f, round=True, r=0.06)
        if label is not None:
            text(slide, cx - bw / 2, cy - d * 0.4, bw, d * 0.8, [[(str(label), size, _legible_ink(f), True, False, face)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    _tag_new(slide, n0, "marker", v)


def _skin_number_face(value, face):
    """The face for a numeral in the language's NUMBER skin: 'body' keeps the caller's `face`; 'display' / 'mono' take
    the deck's display / mono face, always with lining figures. A run that is not digits (一二三, 'Q3 plan') keeps
    `face` — a Latin numeral face has no CJK glyphs."""
    v = _skin("number")
    if v == "body":
        return face
    pref = DISPLAY if v == "display" else MONO
    if _digit_share(str(value)) < _OLDSTYLE_NUMERAL_SHARE:
        return face
    return numeral_face(pref, fallback=face)
```

- [ ] **Step 7: `vl.use()`** — in `scripts/visual_languages.py`, the `dk.set_theme({...})` call gains two keys:

```python
                  "skin": dict(REGISTRY[name]["skin"]),
                  "floor": min(t[5] for t in REGISTRY[name]["type"].values() if isinstance(t, tuple)),
```

  And `_build_registry` (the function that deep-copies manifests into `REGISTRY`) copies `skin` through. Find it with `grep -n "REGISTRY\[" scripts/visual_languages.py`. The key is read from `SPEC["skin"]`.

- [ ] **Step 8: CI wiring** — in `.github/workflows/ci.yml`, after the component-theme step:

```yaml
      - name: Component skins (Phase 2b)
        run: python tests/test_component_skin.py
```

- [ ] **Step 9: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py && python3 tests/test_vl_contract.py | tail -1 && python3 tests/test_component_theme.py | tail -1 && python3 scripts/check_tests_wired.py`
Expected: every suite passes with 0 failed. The component-theme guard stays 76/76 (no component calls a skin helper yet).

- [ ] **Step 10: Commit**

```bash
git add scripts/component_tiers.py tests/test_component_skin.py scripts/deckkit.py scripts/visual_languages.py scripts/vl_contract.py scripts/vl_specs/*.py .github/workflows/ci.yml
git commit -m "skin layer: vocabulary in component_tiers, a skin per manifest (contract-checked), THEME carries skin and type floor, four helpers that draw the call site's own shape by default"
```

(Paths are relative to `skills/slide-maker/` except the workflow — stage with the repo-relative paths.)

---

### Task 2: Markers, rules and numerals — step_list, timeline, agenda, stat_row

**Files:** Modify `scripts/deckkit.py` (`step_list` ~8740, `timeline` ~2190, `agenda` ~2552, `stat_row` ~1903). Test `tests/test_component_skin.py`.

**Interfaces:** Consumes the Task 1 helpers. Produces the generic "skin reaches the drawing" check, reused by Tasks 3–4.

- [ ] **Step 1: Write the failing tests** — append before the summary in `tests/test_component_skin.py`:

```python
# ── the skin reaches the drawing: a Tier-2 component under its language's skin draws differently from the same call
# under the default skin, whenever the language picks a non-default value for a role the component draws ──
import sigs, designed_charts as dc, hashlib
def _xml_of(L, name, skin):
    prs, k = _use(L)
    dk.set_theme(dict(dk.THEME, skin=skin))
    s = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})
    from lxml import etree
    return hashlib.sha256(etree.tostring(s._element)).hexdigest()
DONE = ("step_list", "timeline", "agenda", "stat_row")           # grows as Tasks 3-4 route the rest
for name in DONE:
    for L in vl.LANGS:
        sk = S[L]["skin"]
        roles = [r for r in ct.TIER2_SKIN[name] if sk[r] != ct.SKIN_DEFAULT[r]]
        if not roles:
            continue
        check(_xml_of(L, name, sk) != _xml_of(L, name, dict(ct.SKIN_DEFAULT)),
              "{} wears {}'s skin ({})".format(name, L, ", ".join("{}={}".format(r, sk[r]) for r in roles)))
# CJK step numerals under a display number skin keep a CJK-capable face (Review Focus 2)
prs, k = _use("ink")
s = k.new_slide()
dk.step_list(s, 0.8, 1.0, 8.0, [("採茶", "春分"), ("製茶", "穀雨")], numeral_style="cjk")
faces = [r.font.name for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs
         if r.text.strip() in ("一", "二")]
check(faces and all(f in (None, dk.FONT, dk.EAFONT) or not dk._font_substituted(f) for f in faces),
      "step_list's CJK numerals keep a face that has them ({})".format(faces))
dk.set_theme(None)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | grep -c "FAIL .* wears"`
Expected: a count ≥ 20 (every language whose marker/rule/number differs from the default), e.g. `FAIL step_list wears ink's skin (rule=hairline, marker=circled, number=display)`.

- [ ] **Step 3: Route the call sites** (every edit keeps the original call as `legacy`):

`step_list` — horizontal branch, replace the disc box + numeral text and the connector:

```python
            def _disc(cx=cx, on=on, i=i):
                box(slide, cx + cw / 2 - d / 2, y, d, d, fill=acc if on else _th("card", WHITE),
                    line=None if on else acc, line_w=1.4, round=True, r=d / 2)
                tc = (_legible_ink(acc)) if on else _on_surface(acc, _th("card", WHITE))
                text(slide, cx + cw / 2 - d / 2, y, d, d, [[(numr(i), 15, tc, True, False,
                     _skin_number_face(numr(i), None))]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
            _skin_marker(slide, cx + cw / 2, y + d / 2, d, numr(i), fill=acc if on or active_idx is None else
                         _th("axis", MUTE), ink=_legible_ink(acc), size=15, face=_skin_number_face(numr(i), None),
                         legacy=_disc)
            if i:
                p0, p1 = (cx - g + 0.02, y + d / 2), (cx - 0.02, y + d / 2)
                lc = _blend(acc, _th("card", WHITE), 0.4)
                _skin_rule(slide, p0, p1, color=lc, width=1.0,
                           legacy=lambda p0=p0, p1=p1, lc=lc: connector(slide, p0, p1, color=lc))
```

The vertical branch, the same way: the disc `box` + numeral `text` move into `_disc()` and are passed as `legacy`. The marker fill is `acc if solid else _th("axis", MUTE)`, with size 14 and centre `(x + d / 2, cy + d / 2)`.

`timeline` — the two axis boxes become `_skin_rule`. Horizontal: `p0=(ax0, ay)`, `p1=(ax0 + axw, ay)`, `width=1.7`, `legacy=lambda: box(slide, ax0, ay - 0.012, axw, 0.024, fill=axis_c)`. Vertical: `p0=(ax, y)`, `p1=(ax, y + h)`, `legacy=lambda: box(slide, ax - 0.012, y, 0.024, h, fill=axis_c)`. The two event-dot boxes become `_skin_marker(slide, ex, ay, 0.18, None, fill=dc, ink=dc, size=10, legacy=lambda ex=ex, dc=dc: box(slide, ex - 0.09, ay - 0.09, 0.18, 0.18, fill=dc, round=True, r=0.09))`; the vertical branch does the same with `(ax, ey)`. Every date run `(str(when), 13, tc, True, False)` gains a sixth element `_skin_number_face(when, None)`.

`agenda` — the numeral run's face `chrome_face` becomes `_skin_number_face(num, chrome_face)`. The active `hrule(...)` becomes `_skin_rule(slide, (x, cur + row_h - 0.01), (x + min(w, 1.2), cur + row_h - 0.01), color=accent, width=1.6, legacy=lambda cur=cur: hrule(slide, x, cur + row_h - 0.02, min(w, 1.2), color=accent, weight=0.022))`.

`stat_row` — `_nface = numeral_run_face(fig, serif, fallback=FONT)` becomes `_nface = numeral_run_face(fig, _skin_number_face(fig, serif) or serif, fallback=FONT)`. The divider box becomes `_skin_rule(slide, (cx - gap / 2, y + 0.06), (cx - gap / 2, y + 0.06 + max(0.9, cap_y + 0.24)), color=dcol, width=1.0, legacy=lambda cx=cx, cap_y=cap_y, dcol=dcol: box(slide, cx - gap / 2, y + 0.06, 0.014, max(0.9, cap_y + 0.24), fill=dcol))`, with `dcol = divider_c if divider_c is not None else _th("rule", RGBColor(0xDD, 0xDD, 0xDD))` computed once before the call.

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | tail -1 && python3 tests/test_component_theme.py | tail -1`
Expected: `… passed, 0 failed` for both. The guard stays 76/76: ordinary decks call `legacy` only.

- [ ] **Step 5: Commit**

```bash
git add scripts/deckkit.py tests/test_component_skin.py
git commit -m "step_list, timeline, agenda, stat_row draw markers, rules and numerals in the language's skin; ordinary decks unchanged"
```

---

### Task 3: Cards and rules — org_tree, tier_stack (funnel, pyramid), venn, meter_bar, gantt, the bento example

**Files:** Modify `scripts/deckkit.py` (`org_tree` ~7103, `tier_stack` ~12016, `venn` ~2801, `meter_bar` ~9685, `gantt` ~12133) and `scripts/sigs.py` (the `bento` example). Test `tests/test_component_skin.py`.

- [ ] **Step 1: Write the failing tests** — extend `DONE` in the Task 2 block to `("step_list", "timeline", "agenda", "stat_row", "org_tree", "tier_stack", "funnel", "pyramid", "venn", "meter_bar", "gantt", "bento")`, and append:

```python
# an explicit accent under a line-only card skin: the node text is chosen against the ground the skin leaves
# (Review Focus 1)
import lint_deck, re
prs, k = _use("ink")
s = k.new_slide()
dk.org_tree(s, 0.8, 1.2, 8.0, ("CEO", [("Eng", []), ("Ops", [])]), accent=dk.RGBColor(0x1F, 0x3B, 0xFF))
prs.save(str(WORK / "org_ink.pptx")); buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
    lint_deck.lint(str(WORK / "org_ink.pptx"), static_ok=True)
hard = [l for l in buf.getvalue().splitlines() if re.match(r"\s+slide \d+: (LOW CONTRAST|INVISIBLE)", l)]
check(not hard, "org_tree with an explicit accent reads under a hairline card skin ({})".format(hard[:1]))
dk.set_theme(None)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | grep "FAIL" | grep -c "org_tree\|tier_stack\|venn\|meter_bar\|gantt\|bento\|funnel\|pyramid"`
Expected: a count ≥ 30.

- [ ] **Step 3: Route the call sites**

`org_tree` — the node:

```python
        nfill = acc if depth == 0 else _th("card", WHITE)
        surf = _skin_card(slide, nx, ny, node_w, node_h, fill=nfill, emphasis=(depth == 0),
                          legacy=lambda: box(slide, nx, ny, node_w, node_h, fill=nfill,
                                             line=(None if depth == 0 else acc), line_w=1.1, round=True, r=0.08))
```

The label ink becomes `_as_rgb(_legible_ink(_as_rgbc(acc))) if depth == 0 and _skin("card") == "filled" else _as_rgb(_on_surface(DEEP, surf))`. Ordinary decks: `_skin` is `filled`, so depth 0 keeps `_legible_ink(acc)`, and depth > 0 keeps `_on_surface(DEEP, card)`, which is DEEP unchanged without a theme. `b` is no longer a box return: `draw()` returns `None` and its single caller ignores the value (check with `grep -n "draw(root)"`). Each of the three connector boxes becomes `_skin_rule` with its centre line and `width=1.15`. Example for the stem: `_skin_rule(slide, (nx + node_w / 2, ny + node_h), (nx + node_w / 2, ny + node_h + gap_y / 2), color=lc, width=1.15, legacy=lambda nx=nx, ny=ny: box(slide, nx + node_w / 2 - 0.008, ny + node_h, 0.016, gap_y / 2, fill=lc))`.

`tier_stack` — the band:

```python
        surf = _skin_card(slide, bx, cy, band_w, band_h, fill=cols[i], emphasis=True,
                          legacy=lambda bx=bx, cy=cy, band_w=band_w, c=cols[i]: box(
                              slide, bx, cy, band_w, band_h, fill=c, round=True, r=min(0.06, band_h / 4.0)))
```

The inside-label ink `tc = _legible_ink(cols[i])` becomes `tc = _legible_ink(cols[i]) if _skin("card") == "filled" else _on_surface(_th("ink", DEEP), surf)`. Both leader `connector(...)` calls become `_skin_rule(..., color=MUTE, width=1.0, legacy=lambda …: connector(<the same arguments>))`. `funnel` and `pyramid` call `tier_stack`, so they need no edit.

`venn` — after the outline block (`if outline: o.line.color.rgb …`), route only the outline:

```python
        if outline and _skin("rule") != "solid":
            o.line.fill.background()
            _n0 = len(slide.shapes)
            if _skin("rule") == "chalk":
                import native_art as _na
                _na.chalk_ellipse(slide, cx, cy, rr, rr, str(_as_rgbc(col)))
            else:
                o.line.fill.solid(); o.line.color.rgb = _as_rgb(col)
                o.line.width = Pt(0.75 if _skin("rule") == "hairline" else 1.25)
                if _skin("rule") == "dashed":
                    from pptx.enum.dml import MSO_LINE_DASH_STYLE
                    o.line.dash_style = MSO_LINE_DASH_STYLE.DASH
            _tag_new(slide, _n0, "rule", _skin("rule"))
            if _skin("rule") != "chalk":
                o.name = "{}rule:{}".format(SKIN_TAG, _skin("rule"))
```

`meter_bar` — the track `box(slide, x, yt, w, h, fill=tr, round=True, r=h / 2)` becomes `_skin_rule(slide, (x, yt + h / 2), (x + w, yt + h / 2), color=tr, width=max(1.0, h * 72 * 0.35), legacy=lambda: box(slide, x, yt, w, h, fill=tr, round=True, r=h / 2))`. The value run's face `value_font or font` becomes `_skin_number_face(value, value_font or font)`.

`gantt` — each gridline `connector(...)` becomes `_skin_rule(slide, (gx, grid_top), (gx, chart_bottom), color=_th("rule", RGBColor(0xE4, 0xE7, 0xEC)), width=1.0, legacy=lambda gx=gx: connector(slide, (gx, grid_top), (gx, chart_bottom), color=_th("rule", RGBColor(0xE4, 0xE7, 0xEC)), width=1.0, arrow=False))`. The `today` line stays dashed: its dash is the semantic "now". The tick-label run gains the face `_skin_number_face(lbl, font)`.

`bento` example in `scripts/sigs.py`:

```python
for i, (bx, by, bw, bh) in enumerate(
        dk.bento(s, 0.6, 1.2, 8.8, 3.9,
                 [(2, 2), (2, 1), (1, 1), (1, 1), (4, 1)], cols=4)):
    fill = dk.DEEP if i == 0 else dk.TINT
    surface = dk.skin_card(s, bx, by, bw, bh, fill=fill, emphasis=(i == 0))   # the language's card (paper, chalk …)
    dk.text(s, bx + 0.2, by + 0.15, bw - 0.4, bh - 0.3,
            [[("tile %d" % i, 16 if i else 22, dk.on(surface), i == 0, False)]])   # ink picked for what it sits on
```

Ordinary decks: `skin_card` calls `box(s, bx, by, bw, bh, fill=fill)` and returns `fill`, so `dk.on(surface)` equals the old `dk.on(fill)` and the hash is unchanged.

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | tail -1 && python3 tests/test_component_theme.py | tail -1`
Expected: both `0 failed`; the guard 76/76.

- [ ] **Step 5: Commit**

```bash
git add scripts/deckkit.py scripts/sigs.py tests/test_component_skin.py
git commit -m "org_tree, tier_stack (funnel, pyramid), venn, meter_bar, gantt and bento cells wear the language's card and rule skin; text picked against the surface the skin leaves"
```

---

### Task 4: Rules and numerals inside chart and table XML — table, native_chart, heat_matrix

**Files:** Modify `scripts/deckkit.py` (`table` ~6405, `_cell_rules`, `_theme_chart` ~6050, `heat_matrix` ~12401). Test `tests/test_component_skin.py`.

- [ ] **Step 1: Write the failing tests** — extend `DONE` with `"table", "native_chart", "heat_matrix"`, and append:

```python
# a dashed rule skin reaches the table's XML borders and the chart's gridlines
prs, k = _use("drafting")
s = k.new_slide()
dk.table(s, 0.8, 1.2, 8.0, [["Part", "Qty"], ["Bolt", "12"], ["Nut", "40"]], numeric_cols=[1])
s2 = k.new_slide()
dk.native_chart(s2, 0.6, 1.0, 6.0, 3.2, ["Q1", "Q2"], [("a", [3, 5])], kind="column")
from lxml import etree
x_tbl = etree.tostring(s._element).decode()
x_cht = etree.tostring(s2.shapes[-1].chart._chartSpace).decode()
check('prstDash val="dash"' in x_tbl, "drafting's dashed rule reaches the table borders")
check('prstDash val="dash"' in x_cht, "drafting's dashed rule reaches the chart gridlines")
dk.set_theme(None)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | grep FAIL | grep -c "table\|native_chart\|heat_matrix\|dashed"`
Expected: a count ≥ 10.

- [ ] **Step 3: Implement**

`_cell_rules(cell, top=None, bottom=None)` gains a keyword `dash=None`. When `dash` is set, each `a:lnT` / `a:lnB` it writes gets a child `<a:prstDash val="{dash}"/>`, inserted after the `a:solidFill` child (that is the schema order). In `table`, before the spec loop:

```python
    rv = _skin("rule")
    wk = 0.5 if rv in ("hairline", "chalk") else 1.0       # chalk cannot be drawn in a table border: a hairline
    dash = "dash" if rv == "dashed" else None
```

The loop becomes `_cell_rules(tbl.cell(i, j), top=_wk(s.get('top')), bottom=_wk(s.get('bottom')), dash=dash)`, with `_wk = lambda t: (t[0], t[1] * wk) if t else t`. `cfont` becomes `numeral_run_face(raw, _skin_number_face(raw, font) or font, fallback=font or FONT)`.

In `_theme_chart`, after the gridline colour is set on the value axis's major gridlines (`grep -n "major_gridlines" scripts/deckkit.py`):

```python
    _rv = _skin("rule")
    if _rv != "solid":
        try:
            gl = ch.value_axis.major_gridlines.format.line
            gl.width = Pt(0.5 if _rv in ("hairline", "chalk") else 0.75)
            if _rv == "dashed":
                from pptx.enum.dml import MSO_LINE_DASH_STYLE
                gl.dash_style = MSO_LINE_DASH_STYLE.DASH
        except Exception:
            pass
```

`nfname = numeral_face(font, fallback=fname)` becomes `nfname = numeral_face(_skin_number_face("0", font) or font, fallback=fname)`.

`heat_matrix` — the cell-label run's face `font` becomes `_skin_number_face(lbl, font)`.

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | tail -1 && python3 tests/test_component_theme.py | tail -1 && python3 tests/test_clinical_forms.py | tail -1`
Expected: all `0 failed`; the guard 76/76.

- [ ] **Step 5: Commit**

```bash
git add scripts/deckkit.py tests/test_component_skin.py
git commit -m "table borders, chart gridlines and heat-map numerals follow the language's rule and number skin"
```

---

### Task 5: Type floors (spec §5.2)

**Files:** Modify `scripts/deckkit.py` (the sites below). Test `tests/test_component_skin.py`.

- [ ] **Step 1: Write the failing test** — append:

```python
# no component draws text below its language's floor (spec §5.2) — on every language
import component_tiers as _ct2
for L in vl.LANGS:
    prs, k = _use(L)
    low = []
    for name in _ct2.TIER1:
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(L, prs)
        s = k.new_slide()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})
        for sh in s.shapes:
            if sh.has_text_frame:
                low += [(name, r.font.size.pt, r.text[:10]) for p in sh.text_frame.paragraphs for r in p.runs
                        if r.font.size and r.text.strip() and r.font.size.pt < dk.THEME["floor"] - 1e-6]
    check(not low, "{}: no component text under the floor {} ({})".format(L, dk.THEME["floor"], low[:3]))
dk.set_theme(None)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | grep "FAIL .*under the floor" | cut -c1-200`
Expected: failures on every language with floor 9 or 10. The 2026-10-15 probe found these sites:
- gantt: today label 8 pt;
- source_note: 8.5 pt;
- eval_matrix: legend 9;
- heat_matrix: legend 9;
- leaderboard: sub 9;
- position_map: axis words 9;
- consort_flow, iso_stack and sankey: 9.5.

Drafting, broadsheet and journal (floor 8) flag fewer.

- [ ] **Step 3: Implement** — at each site the failing output names, wrap the literal run size in `_fl(...)`, e.g. in `source_note` `size` → `_fl(size)`, and in `eval_matrix`'s legend `(scale_label, 9, …)` → `(scale_label, _fl(9), …)`. Where a raised size no longer fits its fixed box (the matrix lint in Step 4 says so), grow that box by the size ratio at that site (`h * _fl(s) / s`). Ordinary decks are unchanged (`_fl` is the identity without a theme).

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_component_skin.py | tail -1 && python3 tests/test_component_theme.py | tail -1`
Expected: both `0 failed` (the matrix still has no hard lint finding; the guard 76/76).

- [ ] **Step 5: Commit**

```bash
git add scripts/deckkit.py tests/test_component_skin.py
git commit -m "component text never drops below the active language's type floor; ordinary decks unchanged"
```

---

### Task 6: Placement — `sigs.py --example X --in L`, the matrix built from it on 16:9 and 3:4

**Files:** Modify `scripts/sigs.py`, `tests/test_component_theme.py`, `scripts/check_component_theme.py`. Test: both test files.

**Interfaces:**
- Produces: `sigs.placed_example(name: str, lang: str, ground: str | None = None) -> str`. The returned code assumes `dk`, `dc`, `prs` exist and defines `k`, `s`, `x, y, w, h`. It raises `ValueError` naming the reason when the example cannot be placed.
- Produces: `sigs.PLACE_MIN_W: dict[str, float]`, the minimum content width a component needs. The placed code raises at run time when the rect is narrower.

- [ ] **Step 1: Write the failing tests** — in `tests/test_component_theme.py`:
  - Replace the local `TIER1 = (...)` with `from component_tiers import TIER1`.
  - Delete `PLACEMENT_2B` and its `2b` print branch.
  - Change the matrix loop to build each component from `sigs.placed_example(name, L, g)` on both canvases. The per-component body becomes:

```python
for W, H in ((13.333, 7.5), (7.5, 10.0)):
  for L in vl.LANGS:
    for g in vl.VARIANTS[L]:
        prs = dk.blank_deck(W, H)
        owner, first = [], {}
        for name in TIER1:
            for field in (range(4) if L == "poster" else (None,)):
                with contextlib.redirect_stdout(io.StringIO()):
                    k0 = vl.use(L, prs, ground=g)
                    while field is not None and len(prs.slides) % 4 != field:
                        k0.new_slide()
                n0 = len(prs.slides)
                try:
                    code = sigs.placed_example(name, L, g)
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        exec(compile(code, name, "exec"), {"dk": dk, "dc": dc, "prs": prs})
                except ValueError as e:
                    if "needs a content rect" in str(e):           # a declared minimum, raised loudly (Focus 3)
                        print("  min  {}x{} {}/{} {}: {}".format(W, H, L, g, name, e)); continue
                    check(False, "{}x{} {}/{} {}: builds ({})".format(W, H, L, g, name, e)); continue
                except Exception as e:
                    check(False, "{}x{} {}/{} {}: builds ({}: {})".format(W, H, L, g, name, type(e).__name__, str(e)[:80]))
                    continue
                first[n0] = name
        found = _hard(prs, "m_{}_{}_{}".format(L, g, int(W)))
        ...  # the existing per-slide attribution, messages prefixed with "{}x{} ".format(W, H)
```

  Then append the as-printed run (Review Focus 5):

```python
import subprocess
for name, L in (("timeline", "chalkboard"), ("native_chart", "ink"), ("org_tree", "wayfinding")):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sigs.py"), "--example", name, "--in", L],
                         capture_output=True, text=True).stdout
    src = out + "\nprs.save({!r})\n".format(str(WORK / "printed_{}_{}.pptx".format(name, L)))
    r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, cwd=str(WORK))
    check(r.returncode == 0 and not _hard_file(WORK / "printed_{}_{}.pptx".format(name, L)),
          "`sigs.py --example {} --in {}` runs as printed with no hard lint finding ({})".format(name, L, r.stderr[-160:]))
# a component wider than the rect fails loudly with what it needs (Review Focus 3)
try:
    exec(compile(sigs.placed_example("dumbbell_board", "ink") .replace("x, y, w, h = rs.ground", "x, y, w, h = 0.5, 1, 3.0, 4  # rs.ground"),
                 "narrow", "exec"), {"dk": dk, "dc": dc, "prs": dk.blank_deck(13.333, 7.5)})
    err = None
except ValueError as e:
    err = str(e)
check(err and "needs a content rect" in err and "in wide" in err, "a too-narrow rect raises with the width it needs ({})".format(err))
```

  `_hard_file(path)` is `_hard` for an already-saved file: factor `_hard`'s lint call into it.
  - In `scripts/check_component_theme.py`, its TIER1 becomes `tuple(n for n in component_tiers.TIER1 if n not in ("distribution", "forest_plot", "km_curve", "marimekko", "radar", "roc_curve", "waterfall", "bland_altman")) + ("tint", "axis_scale")`. Those eight are designed_charts functions; matplotlib draws them, and `_theme` covers their colours.

- [ ] **Step 2: Run them to make sure they fail**

Run: `cd skills/slide-maker && python3 tests/test_component_theme.py 2>&1 | tail -3`
Expected: `AttributeError: module 'sigs' has no attribute 'placed_example'`

- [ ] **Step 3: Implement in `scripts/sigs.py`**

```python
# minimum content-rect width a component needs to lay out (inches) — the placed scaffold raises below it instead of
# letting labels collide; measured on the 3:4 matrix (Task 6) and recorded here with the reason in a comment
PLACE_MIN_W = {}
# a component the example leaves to place itself at the foot: its keyword x/y/w and the note's height
_FOOT = {"source_note": 0.3}


def placed_example(name, lang, ground=None):
    """`EXAMPLES[name]` placed in visual language `lang`'s content rect — the code an agent runs as printed after
    `prs = dk.blank_deck(...)`. The example's ONE drawing call with literal geometry gets the rect's x, y, w (and h
    when the component takes one); `dk.add_slide(prs)` becomes `k.new_slide()`; comments are kept."""
    import ast
    import inspect
    import deckkit as dk
    import designed_charts as dc
    src = EXAMPLES[name]
    if "vl.use(" in src:
        raise ValueError("{}: a visual-language scaffold already — print it with --example {}".format(name, name))
    tree = ast.parse(src)
    hits = []
    for c in ast.walk(tree):
        if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and getattr(c.func.value, "id", "") in ("dk", "dc")
                and c.args and getattr(c.args[0], "id", "") == "s"):
            fn = getattr(dk if c.func.value.id == "dk" else dc, c.func.attr)
            params = list(inspect.signature(fn).parameters)
            geo = [(params[i], a) for i, a in enumerate(c.args) if i < len(params) and params[i] in ("x", "y", "w", "h")
                   and isinstance(a, ast.Constant) and isinstance(a.value, (int, float))]
            if geo:
                hits.append((c, geo, params))
    lines = src.splitlines(keepends=True)
    def _span(node):
        return (sum(len(l) for l in lines[:node.lineno - 1]) + node.col_offset,
                sum(len(l) for l in lines[:node.end_lineno - 1]) + node.end_col_offset)
    edits = []
    if len(hits) > 1:
        raise ValueError("{}: {} drawing calls with literal geometry — no single placement; place it by hand in the "
                         "rect rs.ground() returns".format(name, len(hits)))
    if hits:
        c, geo, params = hits[0]
        edits += [(_span(a), p) for p, a in geo]
    elif name in _FOOT:
        call = next(c for c in ast.walk(tree) if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == name)
        end = _span(call)[1] - 1
        edits.append(((end, end), ", x=x, y=y + h - {}, w=w".format(_FOOT[name])))
    else:
        raise ValueError("{}: no drawing call with literal geometry to place".format(name))
    out = src
    for (a, b), rep in sorted(edits, reverse=True):
        out = out[:a] + rep + out[b:]
    out = out.replace("dk.add_slide(prs)", "k.new_slide()")
    head = ("import visual_languages as vl, register_surface as rs\n"
            "k = vl.use({!r}, prs{})\n".format(lang, ", ground={!r}".format(ground) if ground else "") +
            "s = k.new_slide()                           # every page of a language deck starts here\n"
            "x, y, w, h = rs.ground(s, k.name, role=\"content\", index=1)   # the language's content rect (inches)\n")
    if name in PLACE_MIN_W:
        head += ("if w < {0}:\n    raise ValueError(\"{1} needs a content rect at least {0} in wide; this one is %.2f in "
                 "— use a wider canvas or split the content\" % w)\n").format(PLACE_MIN_W[name], name)
    return head + out
```

  `main()` gains `ap.add_argument("--in", dest="lang", metavar="LANGUAGE", help="place each --example in this visual language's content rect")` and `ap.add_argument("--ground", metavar="GROUND")`. On the `--example` path, when `a.lang` is set, print the preamble without its `s = dk.add_slide(prs)` line (see Task 7's `PREAMBLE_VL`) and then `placed_example(n, a.lang, a.ground)` for each name, instead of `EXAMPLES[n]`. A `ValueError` prints to stderr, followed by the plain example.

- [ ] **Step 4: Run the matrix; record the minimums**

Run: `cd skills/slide-maker && python3 tests/test_component_theme.py > /tmp/m.log 2>&1; grep "  FAIL" /tmp/m.log | cut -c1-200 | head -40`
Expected: the 16:9 matrix passes, PLACEMENT_2B's source_note included (it now sits inside the rect). For each 3:4 failure, read the finding:
- A component with a fixed internal width that the docstring already documents (e.g. `dumbbell_board`: "keep w ≥ ~8 so value labels clear") gets a `PLACE_MIN_W` entry, with the docstring's number and a comment quoting it.
- Any other failure is a component defect, fixed at its site with a RED→GREEN check in this file. Example: a fixed label box wider than `w`; the fix is to scale the box to `w`.
Re-run until `0 failed`. Every `min` line is listed in the commit message.

- [ ] **Step 5: Commit**

```bash
git add scripts/sigs.py scripts/check_component_theme.py tests/test_component_theme.py
git commit -m "placement: sigs.py --example X --in L prints a scaffold placed in the language's content rect; the component matrix is built from it on 16:9 and 3:4; components that need a wider rect say so"
```

---

### Task 7: Spec §5.6 — examples that leave no empty page

**Files:** Modify `scripts/sigs.py` (`agenda` example, `PREAMBLE_VL`), `tests/test_component_theme.py` (`CHANGED_ON_PURPOSE`).

- [ ] **Step 1: Write the failing test** — append to `tests/test_component_theme.py`:

```python
# §5.6: no example leaves an empty page, run as printed (the plain preamble's `s` included)
for name in ("agenda", "card"):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sigs.py"), "--example", name],
                         capture_output=True, text=True).stdout
    p = WORK / "printed_{}.pptx".format(name)
    r = subprocess.run([sys.executable, "-c", out + "\nprs.save({!r})\n".format(str(p))], capture_output=True, text=True,
                       cwd=str(WORK))
    check(r.returncode == 0 and not [f for f in _hard_file(p) if "EMPTY" in f],
          "`sigs.py --example {}` as printed leaves no empty page ({})".format(name, [f for f in _hard_file(p) if "EMPTY" in f][:1]))
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `cd skills/slide-maker && python3 tests/test_component_theme.py | grep "leaves no empty page"`
Expected: two FAIL lines. The agenda example adds three blank link targets. The card scaffold runs after a preamble whose `s = dk.add_slide(prs)` stays empty.

- [ ] **Step 3: Implement**
  - Rewrite the `agenda` example:

```python
dk.agenda(s, 0.7, 1.6, 6.6,
          ["Where we were", "What changed", "What is left"],
          active=1)                         # active= is also the progress page
# targets=[page_a, page_b, page_c] links each row to its page (one per row) — pass the deck's real pages
```

  - Add `PREAMBLE_VL`: `PREAMBLE` without its `s = dk.add_slide(prs)` line and that line's comment. `main()` prints it instead of `PREAMBLE` when every printed name's example contains `vl.use(`, or when `--in` is given.
  - Record the guard change in `CHANGED_ON_PURPOSE` with its exact hash. Compute the hash in the same way as sankey's, using the snippet in the 2a ledger, which hashes the slide XML parts:

```python
    "agenda": ("Task 7 (2b): the example no longer adds three blank link-target pages (spec §5.6)", "<sha256 printed by the snippet>"),
```

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_component_theme.py | tail -1 && python3 tests/test_sigs.py 2>/dev/null | tail -1; python3 tests/test_smoke.py 2>/dev/null | tail -1`
Expected: `0 failed` everywhere. If an existing test pinned the agenda example's `targets=`, update it to call `dk.agenda(..., targets=[...])` itself with three real pages it creates, so the link behaviour stays covered.

- [ ] **Step 5: Commit**

```bash
git add scripts/sigs.py tests/test_component_theme.py
git commit -m "examples leave no empty page: agenda shows targets= in a comment, a visual-language scaffold prints a preamble without the unused ordinary slide (spec §5.6)"
```

---

### Task 8: Docs — tiers and skins listed from one source

**Files:** Modify `scripts/vl_docs.py`, `references/visual-languages.md`. Test: `python3 scripts/vl_docs.py --check`.

- [ ] **Step 1: Make the check fail** — add to `REQUIRED[REF / "visual-languages.md"]` the blocks `"tier1-list", "tier2-table", "skin-table"`.

Run: `cd skills/slide-maker && python3 scripts/vl_docs.py --check`
Expected: three problems, `references/visual-languages.md must carry block tier1-list` (and the other two).

- [ ] **Step 2: Implement** — in `_render`'s table (import `component_tiers as ct` at the top; it is plain data):

```python
        "tier1-list": lambda: " · ".join("`{}`".format(n) for n in ct.TIER1),
        "tier2-table": lambda: "\n".join(["| component | draws in the skin |", "|---|---|"] +
                                         ["| `{}` | {} |".format(n, ", ".join(r)) for n, r in ct.TIER2_SKIN.items()]),
        "skin-table": lambda: "\n".join(["| language | card | rule | marker | number |", "|---|---|---|---|---|"] +
                                        ["| `{}` | {} | {} | {} | {} |".format(s["name"], *(s["skin"][r] for r in
                                         ("card", "rule", "marker", "number"))) for s in reg.values()]),
```

In `references/visual-languages.md`, after the "General components wear the language" paragraph, add:

```markdown
- **Tier 1 — held to every ground** (colours, readability, placement): <!-- vl:tier1-list --><!-- /vl -->.
  `python3 scripts/sigs.py --example <component> --in <language>` prints one placed in that language's content rect;
  it runs as printed. A component that needs a wider rect than a canvas gives raises with the width it needs.
- **Tier 2 — also draws in the language's skin** (spec §5.3): each language picks one value per role from
  `scripts/component_tiers.py` `SKIN_VOCAB`; the component draws that role the language's way and picks its text ink
  against what the skin leaves under it. `dk.skin_card(s, x, y, w, h, fill=…)` gives your own containers (the cells
  `dk.bento()` returns) the same card.

<!-- vl:tier2-table --><!-- /vl -->

<!-- vl:skin-table --><!-- /vl -->

  A new language picks from the vocabulary; it adds a value only when none fits, implemented once in deckkit's
  `_skin_*` helper for that role.
```

Then run `python3 scripts/vl_docs.py --write`.

- [ ] **Step 3: Run the checks**

Run: `cd skills/slide-maker && python3 scripts/vl_docs.py --check && cd ../.. && BASE=$(git merge-base origin/main HEAD) && python3 skills/slide-maker/scripts/check_skill_lossless.py --baseline "${BASE}:skills/slide-maker/SKILL.md" --allow skills/slide-maker/.skill-lossless-allow.json --quiet`
Expected: `[vl-docs] 0 problem(s)` and `LOSSLESS: …/… baseline lines accounted for`.

- [ ] **Step 4: Commit**

```bash
git add scripts/vl_docs.py references/visual-languages.md
git commit -m "docs: the component tiers, what each Tier-2 component draws in the skin, and each language's skin — generated from component_tiers and the manifests"
```

---

### Task 9: 🔴 The approval sheet — designed series and skins, before and after

**Files:** none in the repo. The sheet is built in the scratchpad and delivered to `~/Desktop/slide-maker-phase2b/`.

- [ ] **Step 1: The "before" tree** — `git archive vl-components-p2a skills/slide-maker | tar -x -C <scratch>/before` (the 2a result, without skins or new series).

- [ ] **Step 2: The proposed series** — `<scratch>/series_design.json`, from `series_design.py`, is built from each ground's own series and then candidates drawn from the language's world. Every colour passes the contract's rules (≥ 3:1 on ground and card, ΔE ≥ 20 to every other):

| ground | added to the ground's own series |
|---|---|
| editorial/light | 8A6516 ochre, 2E6B50 bottle green |
| editorial/ink | D9A441 gold, 6FB08A sage |
| soft/light | 2F6E78 deep teal |
| soft/dusk | E8D08F butter |
| collage/light | 5E7A2A olive |
| storybook/light | 2E6A86 lake blue |
| storybook/meadow | 2A4A66 deep lake |
| ink/light | 2C4A6E 靛青, 4E6B3A 石绿, 8A6A2A 赭石 |
| ink/night | 8FB3D9 靛青, 8FC49A 石绿, D9B36C 赭石 (lifted for night) |
| poster/light | FFB3D1 pink, 7FF0D0 aqua |
| poster/paper | D9400F orange, 5F7A00 lime (deepened for paper) |
| cutpaper/night | 8AA8E6 sky, C9A6E0 violet (the day palette, lifted) |
| drafting/light | 1F5FA8 blue, 2E7D4F green, 7A4FA8 violet pencil |
| drafting/cyanotype | 7FD3F0 cyan, F2D16B yellow, B6E388 green line |
| starlit/light | 9DB8E8 moonlight, E8A0B4 dusty rose, 8FD4C1 aurora |
| starlit/dawn | F2D88F first sun, A9C8F0 morning blue, C9A6E8 lavender |
| broadsheet/light | 1F4E79 navy, 2F6B3A racing green, 8A6516 ochre |
| broadsheet/salmon | 9E2A2B claret, 3A6B35 green, 7A4A00 brown |
| journal/light | 2C4F8A blue, 9C3D2E brick, 7A5A00 ochre |
| journal/green | 9EC2E8 pale blue, E8A08F coral, D9A0C8 pink |
| tally/light | E5484D tomato, 0F9D58 emerald, 8B5CF6 violet |
| tally/night | FF7A8A tomato, 4FD1C5 teal |
| chalkboard/light, slate | B6E388 green chalk (+ the three chalks it has) |
| interface/light | 15803D on-green, B45309 pending amber (the UI states, deepened) |

collage/slate, cutpaper/light, interface/dark and wayfinding (both grounds) already have four or more.

- [ ] **Step 3: Render the sheets** — one PNG per language, on its default ground, with three rows:
  - A **swatch row**: the series on both grounds, with the new colours marked as new.
  - **Before | after** pairs (2a vs this branch) for `org_tree`, `step_list`, `timeline`, `stat_row`, `tier_stack`, and a 4-series `native_chart` + `radar`.
  - The **skin line**: `card · rule · marker · number` values.

  Build with `soffice --headless --convert-to pdf` and `pdftoppm -r 60`. Compose with PIL into `~/Desktop/slide-maker-phase2b/<language>.png` plus one `overview.png` (all 15, small).

- [ ] **Step 4: Look at every sheet yourself first** — the settled render, not the gates. Fix anything unreadable or broken before the user sees it.

- [ ] **Step 5: 🔴 Ask** — AskUserQuestion: "approve all", "approve with changes (name the languages and what)", "redo the series/skins for some languages". Wait for the answer. A change request edits `series_design.json` / the manifests' `skin`, re-renders that language's sheet, and asks again.

---

### Task 10: Land the series, raise the floor, verify, review

**Files:** Modify `scripts/vl_specs/*.py` (25 grounds' `series`), `scripts/vl_contract.py` (`SERIES_MIN`), `tests/test_vl_contract.py`, `tests/test_component_theme.py`.

- [ ] **Step 1: Write the failing test** — in `tests/test_vl_contract.py`:

```python
check(vl_contract.SERIES_MIN == 4, "the series floor is four designed colours per ground (spec §4.1 ruling, Phase 2b)")
check(all(len(G["roles"]["series"]) >= 4 for s in vl_specs.load().values() for G in s["grounds"].values()),
      "every ground carries at least four series colours")
```

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | grep "series floor\|four series"`
Expected: two FAIL lines.

- [ ] **Step 2: Implement** — set `SERIES_MIN = 4` (its comment becomes "spec §4.1 ruling: four designed colours per ground, approved 2026-10-…"). Append each approved colour to its ground's `roles['series']` in the manifest, in the order shown on the sheet. In `tests/test_component_theme.py`, delete the `designed` exemption in the series check: every pair of the first four now meets the bar.

- [ ] **Step 3: Run everything**
  - `python3 tests/test_vl_contract.py && python3 tests/test_component_theme.py && python3 tests/test_component_skin.py && python3 scripts/check_vl_contract.py && python3 scripts/vl_docs.py --check`. Expected: all green.
  - The full local CI, in four chunks: `for a in 0 40 80 120; do CI_FROM=$a CI_TO=$((a+40)) python3 <scratch>/cisteps.py <repo> <scratch>/ci_2b; done`. Expected: `ran N, failed 0` per chunk.
  - The Linux font sim: `python3 <scratch>/cisim/cisim.py tests/test_component_theme.py` and `tests/test_component_skin.py`. Expected: `0 failed`, with the guard skip shown.

- [ ] **Step 4: Commit**

```bash
git add scripts/vl_specs/*.py scripts/vl_contract.py tests/test_vl_contract.py tests/test_component_theme.py
git commit -m "every language ground carries four designed series colours (approved on the 2b sheet); the contract's series floor is four"
```

- [ ] **Step 5: Final review** — `review-package` over `vl-components-p2a..HEAD`, with a fresh reviewer on the most capable model. Give it this plan's Review Focus verbatim and the ledger's `Ruling:` lines. Then one RED→GREEN fix pass, rulings and deferred minors to the user, and `superpowers:finishing-a-development-branch` (no merge or push without the user's word).
