# Visual-language contract — Phase 1 (contract + registry) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every visual language is declared by one manifest file that a validator checks; all fifteen are migrated with no change to what they draw; one conformance suite and a docs generator hold every registered language, so adding a sixteenth needs a manifest, its compositions and its samples — nothing else.

**Architecture:** `scripts/vl_specs/<name>.py` each define `SPEC`; `scripts/vl_specs/__init__.py` discovers them; `scripts/visual_languages.py` builds its existing tables (`LANGS`, `VARIANTS`, `TYPE`, `NATIVE`, `IMAGE_LED`, `NATIVE_IMAGE_PAGES`, `NATIVE_EXTRAS`, `EXTRA_PAGES`, `_SAMPLE_COPY_NATIVE`, `_DISPLAY_NAMES`, `_RATIONALE`) from them, so every importer keeps working. `scripts/vl_contract.py` validates a manifest (pure, no deckkit import). `scripts/vl_conformance.py` holds the build-time checks (never-invent, extras on the wrong page, compositions, assets) shared by `tests/test_vl_contract.py` and the CLI `scripts/check_vl_contract.py`. `scripts/vl_docs.py` writes/checks marker blocks in the docs.

**Tech Stack:** Python 3.11+, python-pptx, the skill's own deckkit / visual_languages / vl_native modules; tests are plain scripts printing `N passed, 0 failed` (the repo's pattern), each wired as a CI step.

**Spec:** `docs/superpowers/specs/2026-10-15-visual-language-system-design.md` (§4 is this phase).

## Global Constraints

- Never invent words, numbers or names on a page; derived words are declared.
- Commit locally; push, release or rsync the installed copy only when the user says so.
- Before any push: the full local CI (`cisteps.py`, chunks under 10 minutes) and the Linux font simulation.
- CHANGELOG English-only; SKILL.md changes keep `check_skill_lossless.py` green.
- Fixtures are self-built; the user's own decks are never used as test input.
- Migration guard (spec §4.2): every bundled sample's fingerprint in `assets/vl/samples/manifest.json` stays byte-identical, and the existing suites (P3/P4/P5, audit, generality corpus) stay green.
- Phase-1 palette roles (ruling recorded in the spec on 2026-10-15): `series` holds the colours each ground already has that pass (≥ 1); Phase 2 raises the floor to 4 with designed colours.
- Stage named paths only (`git add <paths>`), never `git add -A`.

## Review Focus

1. **A manifest whose `dark` flag disagrees with its colours** (a ground marked light whose ink is lighter than its ground) — the validator refuses it by name; Phase 2 will pick component inks from this flag. *(Task 1 test.)*
2. **Two languages declaring the same extra name with different pages** (e.g. `tags` on `points` in one, `data` in another) — `validate_all` refuses it, naming both languages. *(Task 1 test.)*
3. **A new language with a manifest but no compositions** — the conformance check names every missing page instead of crashing. *(Task 3 test.)*
4. **Re-cased or clause-broken caller words** (a capitalised kicker, a title split at a comma, a Chinese title split at a clause mark) — the never-invent check accepts them; a word the caller never gave is refused with the page and the word. *(Task 3 tests.)*
5. **Docs edited by hand inside a marker block** — `vl_docs.py --check` fails naming the file and block, and `--write` restores it. *(Task 4 test.)*

---

## File structure

| File | Responsibility |
|---|---|
| `scripts/vl_contract.py` (new) | `validate(spec) -> list[str]`, `validate_all(specs) -> list[str]`, `contrast(a, b)`, `delta_e(a, b)`, constants `PAGES`, `CORE_TYPE`, `KINDS`. Pure; imports nothing from the skill. |
| `scripts/vl_specs/__init__.py` (new) | `load() -> dict[name, SPEC]` ordered by `SPEC["order"]`, discovered from the package's modules. |
| `scripts/vl_specs/<name>.py` × 15 (new) | One `SPEC` per language — generated once from today's tables (Task 2), then hand-maintained. |
| `scripts/visual_languages.py` (modify) | Replace the literal per-language tables with tables built from `vl_specs.load()`; keep every public name. |
| `scripts/vl_conformance.py` (new) | `pages_missing(name)`, `invented_words(name)`, `extras_not_refused(name)`, `assets_missing(name)`, `suites_not_registry_driven()`. |
| `scripts/check_vl_contract.py` (new) | CLI: validate + conformance for the named languages (all by default); prints a NEXT line. |
| `scripts/vl_docs.py` (new) | `--write` / `--check` the `<!-- vl:… -->` blocks in the docs. |
| `scripts/directions_diversity.py` (modify) | `NATIVE_LANGS` and the guidance message from the registry. |
| `scripts/check_inventory.py` (modify) | Add the `scripts/vl_specs` group. |
| `tests/test_vl_contract.py` (new) | Unit tests of the validator + the conformance checks over every registered language + docs check. |
| `.github/workflows/ci.yml` (modify) | Steps: the new test, `vl_docs.py --check`. |
| docs (modify) | `SKILL.md`, `references/visual-languages.md`, `references/interview-protocol.md`, `references/codex-runtime.md`, `references/file-inventory.md`, `README.md`, `README_CN.md`: marker blocks. |

---

### Task 1: The contract validator

**Files:**
- Create: `skills/slide-maker/scripts/vl_contract.py`
- Test: `skills/slide-maker/tests/test_vl_contract.py` (first part)

**Interfaces:**
- Produces: `vl_contract.validate(spec: dict) -> list[str]`; `vl_contract.validate_all(specs: dict[str, dict]) -> list[str]`; `vl_contract.contrast(a_hex: str, b_hex: str) -> float`; `vl_contract.delta_e(a_hex, b_hex) -> float`; `vl_contract.is_dark(palette: dict) -> bool`; constants `PAGES`, `CORE_TYPE`, `KINDS`, `ROLE_KEYS`.
- SPEC shape (every later task relies on it):

```python
SPEC = {
    "name": "tally", "order": 12, "kind": "drawn",                    # kind: "image-led" | "drawn"
    "display": {"en": "Data tally", "zh": "数据账本"},
    "rationale": "drawn, no pictures: …",
    "offer": {"en": ["metrics", "quarterly review", "operations", "growth"],
              "zh": ["指标", "季度复盘", "运营", "增长"]},              # image-led: {"pictures": "photos"|"illustrations"}
    "look": {...},          # today's LANGS[name], unchanged (palette, fonts, ea, grain, frames, forbids, cover, skeleton, …)
    "grounds": {"light": {"label": …, "label_zh": …, "grain": …, "palette": {...},     # today's VARIANTS[name][g]
                          "dark": False,
                          "roles": {"card": "FFFFFF", "card_ink": "…", "rule": "…", "on_accent": "…",
                                    "series": ["…"], "highlight": "…"}},
                "night": {...}},
    "type": {...},          # today's TYPE[name], unchanged
    "image_pages": ("image_text",),
    "extras": {"tags": {"pages": ("points",), "remembered": False, "takes": "…", "absent": "…"}, …},
    "derived": [{"id": "point_numbers", "what": "01 02 03 on points", "words": {}}, …],
    "samples": {"copy": [...]},                      # drawn: today's _SAMPLE_COPY_NATIVE[name]; image-led: {"kind": "photo"}
    "painters": {"ground": "_ground_tally", "card": "_card_tally"},
}
```

- [ ] **Step 1: Write the failing tests** — create `skills/slide-maker/tests/test_vl_contract.py`:

```python
"""The visual-language contract: the manifest validator (part 1) and the conformance checks over every registered
language (part 2, Task 3) and the docs blocks (part 3, Task 4). Prints `N passed, 0 failed`."""
import copy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import vl_contract as vc

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)


def good_spec():
    """A minimal valid manifest (a light and a dark ground) — the unit tests mutate a copy of it."""
    pal_l = {"ground": "F6F5F1", "ink": "16191E", "mute": "5A6070", "panel": "FFFFFF",
             "accents": ["D7262E", "0071BC"], "text_accents": ["1B2A41"]}
    pal_d = {"ground": "1B2A41", "ink": "F2F4F8", "mute": "B9C3D4", "panel": "22344F",
             "accents": ["E8454C", "3D9BE0"], "text_accents": ["F2B705"]}
    t = {r: (20, "body", False, "ink", False, 11) for r in vc.CORE_TYPE}
    return {
        "name": "fixture", "order": 99, "kind": "drawn",
        "display": {"en": "Fixture", "zh": "测试"}, "rationale": "drawn, no pictures: a test fixture",
        "offer": {"en": ["testing", "fixtures"], "zh": ["测试", "样例"]},
        "look": {"palette": pal_l, "fonts": {"both": {"display": "Arial", "body": "Arial"},
                                             "mac": {"display": "Arial", "body": "Arial"}},
                 "ea": {"display": "sans", "body": "sans"}, "grain": 0, "frames": ["rect"], "forbids": (),
                 "cover": "low-left", "skeleton": "band"},
        "grounds": {
            "light": {"label": "paper", "label_zh": "纸面版", "grain": 0, "palette": pal_l, "dark": False,
                      "roles": {"card": "FFFFFF", "card_ink": "16191E", "rule": "C9C7C0", "on_accent": "FFFFFF",
                                "series": ["D7262E", "0071BC"], "highlight": "1B2A41"}},
            "night": {"label": "navy", "label_zh": "夜间版", "grain": 0, "palette": pal_d, "dark": True,
                      "roles": {"card": "22344F", "card_ink": "F2F4F8", "rule": "3B4E6B", "on_accent": "0F1A2C",
                                "series": ["F2B705", "E8454C"], "highlight": "F2B705"}}},
        "type": t, "image_pages": ("image_text",),
        "extras": {"tags": {"pages": ("points",), "remembered": False, "takes": "one label per point",
                            "absent": "no chips"}},
        "derived": [{"id": "point_numbers", "what": "1 2 3 on points", "words": {}}],
        "samples": {"copy": [("cover", {"title": "A fixture"})]},
        "painters": {"ground": "_ground_fixture", "card": "_card_fixture"},
    }


# ── part 1: the validator ──
check(vc.validate(good_spec()) == [], "a complete manifest validates ({})".format(vc.validate(good_spec())))
for key in ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters"):
    s = good_spec(); del s[key]
    probs = vc.validate(s)
    check(any(key in p for p in probs), "a manifest without {!r} is refused naming it ({})".format(key, probs[:1]))
s = good_spec(); s["kind"] = "painted"
check(any("kind" in p for p in vc.validate(s)), "an unknown kind is refused")
s = good_spec(); s["grounds"]["night"]["dark"] = False
check(any("dark" in p and "night" in p for p in vc.validate(s)),
      "a dark flag that disagrees with the colours is refused, naming the ground (Review Focus 1)")
s = good_spec(); s["grounds"]["light"]["palette"] = dict(s["grounds"]["light"]["palette"], ink="9A9A9A")
check(any("ink" in p and "light" in p for p in vc.validate(s)), "an ink under 4.5:1 on its ground is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["card_ink"] = "EEEEEE"
check(any("card_ink" in p for p in vc.validate(s)), "a card ink under 4.5:1 on its card is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["series"] = []
check(any("series" in p for p in vc.validate(s)), "an empty series is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["series"] = ["F6F5F0"]
check(any("series" in p for p in vc.validate(s)), "a series colour under 3:1 on the ground is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["series"] = ["D7262E", "D9282F"]
check(any("series" in p and "distinguish" in p for p in vc.validate(s)), "two near-identical series colours are refused")
s = good_spec(); del s["type"]["quote"]
check(any("quote" in p for p in vc.validate(s)), "a missing core type role is refused, naming it")
s = good_spec(); s["image_pages"] = ("gallery",)
check(any("gallery" in p for p in vc.validate(s)), "an image page that is not a page is refused")
s = good_spec(); s["extras"]["tags"]["pages"] = ("sidebar",)
check(any("sidebar" in p for p in vc.validate(s)), "an extra on an unknown page is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["rule"] = "nothex"
check(any("rule" in p for p in vc.validate(s)), "a colour that is not 6-digit hex is refused")
s = good_spec(); s["offer"] = {"en": [], "zh": []}
check(any("offer" in p for p in vc.validate(s)), "a drawn language with no offer topics is refused")
a, b = good_spec(), good_spec()
b["name"], b["order"] = "fixture2", 100
b["extras"]["tags"]["pages"] = ("data",)
probs = vc.validate_all({"fixture": a, "fixture2": b})
check(any("tags" in p and "fixture" in p and "fixture2" in p for p in probs),
      "one extra name with two meanings is refused, naming both languages (Review Focus 2): {}".format(probs[:1]))
b2 = good_spec(); b2["name"] = "fixture2"
check(any("order" in p for p in vc.validate_all({"fixture": good_spec(), "fixture2": b2})), "a duplicate order is refused")
check(abs(vc.contrast("FFFFFF", "000000") - 21.0) < 0.01, "contrast(white, black) is 21")
check(vc.delta_e("FF0000", "FF0000") == 0.0 and vc.delta_e("FF0000", "0000FF") > 50, "delta_e is a colour distance")

# ── part 2 (Task 3) and part 3 (Task 4) are appended above this line ──

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | tail -3`
Expected: FAIL — `ModuleNotFoundError: No module named 'vl_contract'`.

- [ ] **Step 3: Write the validator** — create `skills/slide-maker/scripts/vl_contract.py`:

```python
"""The visual-language contract: what every language's manifest (scripts/vl_specs/<name>.py) declares, checked.

validate(spec) -> [problem, …] (empty = valid); validate_all({name: spec}) adds the rules across languages (one extra
name means one thing; unique names and orders). Pure: imports nothing from the skill, so the manifests, the tests and
a new language's author can all run it. Spec: docs/superpowers/specs/2026-10-15-visual-language-system-design.md §4."""
import re

PAGES = ("cover", "section", "image_text", "points", "quote", "data", "closing")
KINDS = ("image-led", "drawn")
# the type roles every page and component may ask for; a language may add private ones (item_no is private: six drawn
# languages number their points in their own furniture)
CORE_TYPE = ("kicker", "title", "subtitle", "body", "quote", "attribution", "number", "label", "note", "caption",
             "line", "item_head", "item_line")
ROLE_KEYS = ("card", "card_ink", "rule", "on_accent", "series", "highlight")
TOP_KEYS = ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters")
_HEX = re.compile(r"^[0-9A-Fa-f]{6}$")
SERIES_MIN = 1          # Phase 1 (spec ruling 2026-10-15): the colours each ground already has; Phase 2 raises it to 4
SERIES_DE = 20.0        # two series colours closer than this (CIE76) read as one


def _rgb(h):
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    r, g, b = (_lin(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _lab(h):
    r, g, b = (_lin(c) for c in _rgb(h))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = [t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116 for t in (x, y, z)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def delta_e(a, b):
    return sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5


def is_dark(palette):
    """A ground is dark when its text ink is lighter than it — the meaning a component needs to pick its ink."""
    return luminance(palette["ink"]) > luminance(palette["ground"])


def _hexes(where, d, keys, probs):
    for k in keys:
        v = d.get(k)
        vals = v if isinstance(v, list) else [v]
        if not vals or any(not isinstance(x, str) or not _HEX.match(x) for x in vals):
            probs.append("{}: {} must be 6-digit hex colour(s), got {!r}".format(where, k, v))
            return False
    return True


def validate(spec):
    probs = []
    name = spec.get("name", "?")
    for k in TOP_KEYS:
        if k not in spec:
            probs.append("{}: the manifest has no {!r}".format(name, k))
    if probs:
        return probs
    if not isinstance(name, str) or not re.match(r"^[a-z][a-z0-9_]*$", name):
        probs.append("{!r}: name must be lowercase letters, digits or _".format(name))
    if not isinstance(spec["order"], int):
        probs.append("{}: order must be an int".format(name))
    if spec["kind"] not in KINDS:
        probs.append("{}: kind must be one of {}, got {!r}".format(name, KINDS, spec["kind"]))
    if not all(isinstance(spec["display"].get(s), str) and spec["display"][s].strip() for s in ("en", "zh")):
        probs.append("{}: display needs non-empty 'en' and 'zh'".format(name))
    if not isinstance(spec["rationale"], str) or len(spec["rationale"]) < 12:
        probs.append("{}: rationale must say in a line what the language is".format(name))
    off = spec["offer"]
    if spec["kind"] == "drawn":
        if not all(isinstance(off.get(s), list) and len(off[s]) >= 2 and all(isinstance(t, str) and t for t in off[s])
                   for s in ("en", "zh")):
            probs.append("{}: offer needs at least two topics in 'en' and in 'zh'".format(name))
    elif off.get("pictures") not in ("photos", "illustrations"):
        probs.append("{}: an image-led language's offer names its pictures: 'photos' or 'illustrations'".format(name))
    gr = spec["grounds"]
    if "light" not in gr or len(gr) < 2:
        probs.append("{}: grounds need 'light' (the default key callers pass) and a contrast ground".format(name))
    for g, gd in gr.items():
        where = "{}/{}".format(name, g)
        pal, roles = gd.get("palette", {}), gd.get("roles", {})
        if not _hexes(where, pal, ("ground", "ink", "mute", "panel", "accents", "text_accents"), probs):
            continue
        if not isinstance(gd.get("dark"), bool):
            probs.append("{}: dark must be True or False".format(where))
        elif gd["dark"] != is_dark(pal):
            probs.append("{}: dark={} but its ink is {} than its ground".format(
                where, gd["dark"], "lighter" if is_dark(pal) else "darker"))
        missing = [k for k in ROLE_KEYS if k not in roles]
        if missing:
            probs.append("{}: roles missing {}".format(where, missing))
            continue
        if not _hexes(where, roles, ROLE_KEYS, probs):
            continue
        for a, b, floor, what in ((pal["ink"], pal["ground"], 4.5, "ink on ground"),
                                  (pal["mute"], pal["ground"], 4.5, "mute on ground"),
                                  (roles["card_ink"], roles["card"], 4.5, "card_ink on card"),
                                  (roles["on_accent"], pal["accents"][0], 3.0, "on_accent on accents[0]")):
            c = contrast(a, b)
            if c < floor:
                probs.append("{}: {} is {:.2f}:1 (floor {}:1) — {} on {}".format(where, what, c, floor, a, b))
        ser = roles["series"]
        if len(ser) < SERIES_MIN:
            probs.append("{}: series needs at least {} colour(s)".format(where, SERIES_MIN))
        for c in ser:
            for surf, sname in ((pal["ground"], "ground"), (roles["card"], "card")):
                if contrast(c, surf) < 3.0:
                    probs.append("{}: series colour {} is {:.2f}:1 on the {} (floor 3:1)".format(
                        where, c, contrast(c, surf), sname))
        for i, a in enumerate(ser):
            for b in ser[i + 1:]:
                if delta_e(a, b) < SERIES_DE:
                    probs.append("{}: series colours {} and {} are too close to distinguish (ΔE {:.1f} < {})".format(
                        where, a, b, delta_e(a, b), SERIES_DE))
    t = spec["type"]
    for r in CORE_TYPE:
        if r not in t:
            probs.append("{}: type has no core role {!r}".format(name, r))
    for r, v in t.items():
        if not (isinstance(v, tuple) and len(v) == 6 and isinstance(v[0], (int, float)) and isinstance(v[5], (int, float))
                and v[5] <= v[0]):
            probs.append("{}: type role {!r} must be (size, role, bold, colour, italic, floor<=size), got {!r}".format(
                name, r, v))
    for p in spec["image_pages"]:
        if p not in PAGES:
            probs.append("{}: image page {!r} is not one of {}".format(name, p, PAGES))
    for x, d in spec["extras"].items():
        pages = d.get("pages")
        if pages != "any" and (not isinstance(pages, tuple) or any(p not in PAGES for p in pages)):
            probs.append("{}: extra {!r} pages must be 'any' or a tuple of {}, got {!r}".format(name, x, PAGES, pages))
        if not isinstance(d.get("remembered"), bool):
            probs.append("{}: extra {!r} must say remembered=True/False".format(name, x))
        for k in ("takes", "absent"):
            if not isinstance(d.get(k), str) or not d[k].strip():
                probs.append("{}: extra {!r} must say what it {}".format(name, x, k))
    for d in spec["derived"]:
        if not (isinstance(d, dict) and isinstance(d.get("id"), str) and isinstance(d.get("what"), str)
                and isinstance(d.get("words"), dict)):
            probs.append("{}: each derived entry is {{'id', 'what', 'words': {{script: [word, …]}}}}, got {!r}".format(
                name, d))
    sm = spec["samples"]
    if spec["kind"] == "drawn" and not (isinstance(sm.get("copy"), list) and sm["copy"]):
        probs.append("{}: a drawn language's samples need 'copy': [(page, fields), …]".format(name))
    if spec["kind"] == "image-led" and sm.get("kind") not in ("photo", "watercolour"):
        probs.append("{}: an image-led language's samples name 'kind': 'photo' or 'watercolour'".format(name))
    for k in ("ground", "card"):
        if not isinstance(spec["painters"].get(k), str):
            probs.append("{}: painters needs the name of its {} function".format(name, k))
    return probs


def validate_all(specs):
    probs = []
    for n, s in specs.items():
        probs += validate(s)
        if s.get("name") != n:
            probs.append("{}: the manifest says name={!r}".format(n, s.get("name")))
    orders = {}
    for n, s in specs.items():
        orders.setdefault(s.get("order"), []).append(n)
    probs += ["order {} is used by {}".format(o, ns) for o, ns in orders.items() if len(ns) > 1]
    meaning = {}
    for n, s in specs.items():
        for x, d in s.get("extras", {}).items():
            key = (d.get("pages"), d.get("remembered"))
            meaning.setdefault(x, {}).setdefault(key, []).append(n)
    for x, m in meaning.items():
        if len(m) > 1:
            probs.append("extra {!r} means different things: {}".format(
                x, "; ".join("{} in {}".format(k, ns) for k, ns in m.items())))
    return probs
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | tail -3`
Expected: `NN passed, 0 failed` (about 30).

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/vl_contract.py skills/slide-maker/tests/test_vl_contract.py
git commit -m "vl_contract: the visual-language manifest validator"
```

---

### Task 2: Manifests for all fifteen languages; the tables are built from them

**Files:**
- Create: `skills/slide-maker/scripts/vl_specs/__init__.py`, `skills/slide-maker/scripts/vl_specs/<name>.py` × 15 (generated in Step 3)
- Modify: `skills/slide-maker/scripts/visual_languages.py` (lines 37–260: `LANGS` … `EXTRA_PAGES`; line 602 `TYPE = {…}` through its end; lines 1956–… `_SAMPLE_COPY_NATIVE = {…}`; lines 2150–2175 `_DISPLAY_NAMES` / `_RATIONALE`; line ~579 the `rs.register` loop)
- Modify: `skills/slide-maker/scripts/check_inventory.py:38` (`GROUPS`), `skills/slide-maker/references/file-inventory.md`
- Test: `skills/slide-maker/tests/test_vl_contract.py` (registry checks appended)

**Interfaces:**
- Consumes: `vl_contract.validate_all`, `vl_contract.is_dark`, `vl_contract.contrast`, `vl_contract.delta_e`.
- Produces: `vl_specs.load() -> dict[str, dict]` (ordered by `order`); `visual_languages.REGISTRY` (= that dict); every existing table name in `visual_languages` keeps its value.

- [ ] **Step 1: Snapshot today's tables** (the migration's equality guard) — save to the plan workspace (`<ws>` = the directory `sdd-workspace` printed) as `<ws>/snapshot_tables.py` and run it once now:

```python
"""Dump visual_languages' per-language tables as JSON (tuples kept distinct from lists) — run before and after."""
import json, sys
sys.path.insert(0, sys.argv[1])
import visual_languages as vl
def enc(o):
    if isinstance(o, tuple): return {"__t": [enc(x) for x in o]}
    if isinstance(o, list): return [enc(x) for x in o]
    if isinstance(o, dict): return {str(k): enc(v) for k, v in o.items()}
    return o
names = ["LANGS", "VARIANTS", "TYPE", "NATIVE", "NATIVE_IMAGE_PAGES", "IMAGE_LED", "NATIVE_EXTRAS", "EXTRA_PAGES",
         "_SAMPLE_COPY_NATIVE", "_DISPLAY_NAMES", "_RATIONALE", "SAMPLE_IMAGES", "_SAMPLE_COPY"]
out = {n: enc(getattr(vl, n)) for n in names}
# dict ORDER matters to callers that iterate (LANGS drives every loop): keep it
out["_order"] = {n: list(getattr(vl, n)) for n in names if isinstance(getattr(vl, n), dict)}
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=0, sort_keys=True)
```

Run: `python3 <ws>/snapshot_tables.py skills/slide-maker/scripts <ws>/tables_before.json && wc -c <ws>/tables_before.json`
Expected: a JSON file of tens of KB.

- [ ] **Step 2: Write the failing registry test** — append to `tests/test_vl_contract.py` above the `# ── part 2` marker line:

```python
# ── the registry: every language is a manifest, and the manifests are valid ──
import vl_specs
import visual_languages as vl
REG = vl_specs.load()
check(list(REG) == list(vl.LANGS), "the registry and LANGS list the same languages in the same order")
check(len(REG) == 15, "fifteen languages are registered ({})".format(len(REG)))
probs = vc.validate_all(REG)
check(probs == [], "every manifest satisfies the contract: {}".format(probs[:4]))
check(vl.REGISTRY is not None and set(vl.REGISTRY) == set(REG), "visual_languages exposes REGISTRY")
for n, s in REG.items():
    for g, gd in s["grounds"].items():
        check(gd["palette"] == vl.VARIANTS[n][g]["palette"], "{}/{}: VARIANTS is built from the manifest".format(n, g))
```

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | tail -3`
Expected: FAIL — `ModuleNotFoundError: No module named 'vl_specs'`.

- [ ] **Step 3: Generate the fifteen manifests** — save as `<ws>/migrate_specs.py` and run it once. It reads today's tables and writes each manifest with today's values verbatim, adding the new contract fields (`dark`, `roles`, `offer`, `display.zh`, `derived`, `extras` meanings, `painters`). The values it computes are written as literals, so the files are the source of truth from then on.

```python
"""One-off: write scripts/vl_specs/<name>.py from visual_languages' current tables (run from the repo root)."""
import pprint, sys
from pathlib import Path
SK = Path("skills/slide-maker")
sys.path.insert(0, str(SK / "scripts"))
import visual_languages as vl, vl_contract as vc

ZH = {"editorial": "杂志", "soft": "柔和", "collage": "拼贴", "storybook": "绘本", "ink": "水墨", "poster": "海报大字",
      "cutpaper": "剪纸层叠", "drafting": "蓝图技术线稿", "starlit": "星夜", "broadsheet": "报纸头版", "journal": "学术期刊",
      "tally": "数据账本", "chalkboard": "黑板报", "interface": "产品界面", "wayfinding": "导视线路"}   # README_CN, verbatim
OFFER = {   # references/visual-languages.md and README_CN.md guidance, verbatim
    "editorial": {"pictures": "photos"}, "soft": {"pictures": "photos"}, "collage": {"pictures": "photos"},
    "storybook": {"pictures": "illustrations"},
    "ink": {"en": ["culture", "history", "craft"], "zh": ["文化", "历史", "器物"]},
    "poster": {"en": ["launch", "manifesto", "opinion"], "zh": ["发布会", "宣言", "观点"]},
    "cutpaper": {"en": ["children", "storytelling", "community"], "zh": ["儿童", "讲故事", "社区"]},
    "drafting": {"en": ["engineering", "architecture", "systems design"], "zh": ["工程", "建筑", "系统设计"]},
    "starlit": {"en": ["year in review", "letter", "thanks", "commemoration"], "zh": ["年度回顾", "书信", "致谢", "纪念"]},
    "broadsheet": {"en": ["newsletter", "periodic report", "community update"], "zh": ["通讯", "定期报告", "社区动态"]},
    "journal": {"en": ["research talk", "lab meeting", "paper", "defence"], "zh": ["学术报告", "组会", "论文", "答辩"]},
    "tally": {"en": ["metrics", "quarterly review", "operations", "growth"], "zh": ["指标", "季度复盘", "运营", "增长"]},
    "chalkboard": {"en": ["lesson", "class", "training", "explainer"], "zh": ["课程", "课堂", "培训", "讲解"]},
    "interface": {"en": ["product launch", "app", "SaaS", "feature tour", "internal tool"],
                  "zh": ["产品发布", "应用", "SaaS", "功能导览", "内部工具"]},
    "wayfinding": {"en": ["roadmap", "process", "onboarding", "journey", "strategy route", "transport/city"],
                   "zh": ["路线图", "流程", "新人上手", "用户旅程", "战略路径", "交通与城市"]},
}
# references/visual-languages.md "Derived, never typed in" + the localised structural labels table, verbatim
LABELS = {"ABSTRACT": {"en": ["ABSTRACT"], "zh": ["摘要"], "ja": ["要旨"], "ko": ["초록"]},
          "INSIDE": {"en": ["INSIDE"], "zh": ["本期"], "ja": ["目次"], "ko": ["목차"]},
          "FIGURE": {"en": ["FIGURE"], "zh": ["图"], "ja": ["図"], "ko": ["그림"]},
          "PAGE": {"en": ["PAGE"], "zh": ["第", "版"], "ja": ["面"], "ko": ["면"]},
          "NOTE": {"en": ["NOTE"], "zh": ["注"], "ja": ["注"], "ko": ["주석"]}}
DERIVED = {
    "editorial": [{"id": "quote_mark", "what": "the opening quote mark on quote pages", "words": {}}],
    "soft": [{"id": "quote_mark", "what": "the opening quote mark on quote pages", "words": {}}],
    "collage": [{"id": "quote_mark", "what": "the opening quote mark on quote pages", "words": {}}],
    "storybook": [{"id": "quote_mark", "what": "the opening quote mark on quote pages", "words": {}}],
    "ink": [{"id": "point_numbers", "what": "一 二 三 on points when the title is Chinese or Japanese, else 1 2 3", "words": {}}],
    "poster": [{"id": "page_numbers", "what": "a two-digit number on every page", "words": {}},
               {"id": "point_numbers", "what": "01 02 03 on points", "words": {}}],
    "cutpaper": [{"id": "point_numbers", "what": "1 2 3 on points", "words": {}}],
    "drafting": [{"id": "sheet_border", "what": "the sheet border 1-6 and A-D", "words": {"en": ["A", "B", "C", "D"]}},
                 {"id": "title_block", "what": "SHEET with the sheet's two-digit number, and PROJECT",
                  "words": {"en": ["SHEET", "PROJECT"]}}],
    "starlit": [],
    "broadsheet": [{"id": "page_label", "what": "PAGE n on every page", "words": LABELS["PAGE"]},
                   {"id": "inside_label", "what": "the Inside list's label", "words": LABELS["INSIDE"]},
                   {"id": "end_mark", "what": "the end mark on the closing page", "words": {}}],
    "journal": [{"id": "page_numbers", "what": "a plain number on every page but the cover", "words": {}},
                {"id": "section_mark", "what": "§ before a section's number", "words": {}},
                {"id": "point_numbers", "what": "1 2 3 on points", "words": {}},
                {"id": "figure_label", "what": "FIGURE n over image pages", "words": LABELS["FIGURE"]},
                {"id": "abstract_label", "what": "the abstract's label", "words": LABELS["ABSTRACT"]},
                {"id": "note_label", "what": "the margin note's label", "words": LABELS["NOTE"]},
                {"id": "attribution_dash", "what": "the dash before an attribution", "words": {}}],
    "tally": [{"id": "point_numbers", "what": "01 02 03 on points", "words": {}}],
    "chalkboard": [{"id": "point_numbers", "what": "circled 1 2 3 on points", "words": {}},
                   {"id": "attribution_dash", "what": "the dash before an attribution", "words": {}}],
    "interface": [{"id": "point_numbers", "what": "1 2 3 badges on points", "words": {}},
                  {"id": "initials", "what": "the avatar's initials, from a name only", "words": {}},
                  {"id": "info_glyph", "what": "the i beside a data note", "words": {"en": ["i"]}}],
    "wayfinding": [{"id": "roundel_numbers", "what": "numbered roundels on the directory sign and the board",
                    "words": {}},
                   {"id": "way_out", "what": "the way-out label on the closing sign",
                    "words": {"en": ["WAY", "OUT"], "zh": ["出口"], "ja": ["出口"], "ko": ["출구"]}},
                   {"id": "attribution_dash", "what": "the dash before an attribution", "words": {}}],
}
TAKES = {   # what each extra takes and what is drawn without it (references/visual-languages.md extras tables)
    "seal": ("1-4 characters for the seal", "no seal"), "highlight": ("one word of the title to highlight", "no highlight"),
    "icons": ("one library:name icon spec per point", "numbered discs"),
    "project": ("the project name for the title block", "the title block without a project"),
    "masthead": ("the masthead's words", "no masthead words"), "edition": ("the edition line", "no edition line"),
    "inside": ("1-4 Inside entries", "no Inside list"), "tags": ("one label per point", "no chips"),
    "running": ("the running head", "no running head"), "authors": ("the author line", "no author line"),
    "abstract": ("the abstract text", "no abstract"), "margin": ("one margin note", "no margin note"),
    "total": ("the total the number is a share of", "no share bar"), "doodle": ("one library:name icon spec", "no doodle"),
    "ordered": ("True when the points happen in order", "no arrows or route"),
    "crumb": ("the window's breadcrumb", "an empty top bar"), "status": ("text or (text, state)", "no status chip"),
    "actions": ("1-2 button labels", "no buttons"), "toggles": ("1-4 (label, on) rows", "no settings panel"),
    "line": ("a 1-3 character line code, or (code, colour name)", "the section number in the roundel"),
    "interchange": ("0-based point indexes drawn as interchanges", "plain stations"),
    "board": ("1-4 (label, value) rows", "the page's own row only"),
}
REMEMBERED = {"project", "masthead", "edition", "running", "crumb", "status", "line"}   # memo()/k.project in vl_native*.py; seal is per page


def roles(pal):
    acc, ta = list(pal["accents"]), list(pal["text_accents"])
    card = pal["panel"]
    on = max(("FFFFFF", pal["ink"], pal["ground"]), key=lambda c: vc.contrast(c, acc[0]))
    rule = pal.get("line") or "".join("%02X" % round(int(pal["ink"][i:i + 2], 16) * 0.3 + int(pal["ground"][i:i + 2], 16) * 0.7)
                                      for i in (0, 2, 4))
    series = []
    for c in acc + ta + list(pal.get("lines", [])):
        if c in series or vc.contrast(c, pal["ground"]) < 3 or vc.contrast(c, card) < 3:
            continue
        if all(vc.delta_e(c, s) >= vc.SERIES_DE for s in series):
            series.append(c)
    return {"card": card, "card_ink": pal["ink"], "rule": rule, "on_accent": on, "series": series, "highlight": ta[0]}


for order, name in enumerate(vl.LANGS, 1):
    drawn = name in vl.NATIVE
    grounds = {}
    for g, v in vl.VARIANTS[name].items():
        gd = dict(v)
        gd["dark"] = vc.is_dark(v["palette"])
        gd["roles"] = roles(v["palette"])
        grounds[g] = gd
    extras = {x: {"pages": vl.EXTRA_PAGES.get(x, "any"), "remembered": x in REMEMBERED,
                  "takes": TAKES[x][0], "absent": TAKES[x][1]} for x in vl.NATIVE_EXTRAS.get(name, ())}
    spec = {
        "name": name, "order": order, "kind": "drawn" if drawn else "image-led",
        "display": {"en": vl._DISPLAY_NAMES[name], "zh": ZH[name]}, "rationale": vl._RATIONALE[name],
        "offer": OFFER[name], "look": vl.LANGS[name], "grounds": grounds, "type": vl.TYPE[name],
        "image_pages": vl.NATIVE_IMAGE_PAGES[name] if drawn else ("cover", "image_text", "quote", "data", "closing"),
        "extras": extras, "derived": DERIVED[name],
        "samples": {"copy": vl._SAMPLE_COPY_NATIVE[name]} if drawn else
                   {"kind": "watercolour" if name == "storybook" else "photo"},
        "painters": {"ground": "_ground_" + name, "card": "_card_" + name},
    }
    head = ('"""{} — the {} visual language ({}). The manifest the contract checks (scripts/vl_contract.py);\n'
            'visual_languages builds its tables from it. Generated from the tables on 2026-10-15, maintained by hand."""\n\n'
            ).format(name, spec["display"]["en"], spec["display"]["zh"])
    body = "SPEC = " + pprint.pformat(spec, width=118, sort_dicts=False) + "\n"
    (SK / "scripts" / "vl_specs" / (name + ".py")).write_text(head + body, encoding="utf-8")
    print("wrote", name)
```

Run first: `mkdir -p skills/slide-maker/scripts/vl_specs`, then create `skills/slide-maker/scripts/vl_specs/__init__.py`:

```python
"""One manifest per visual language: scripts/vl_specs/<name>.py defines SPEC (the contract: scripts/vl_contract.py).

load() returns {name: SPEC} ordered by SPEC["order"]. A new language is a new file here — nothing else to register."""
import importlib
import pkgutil
from pathlib import Path


def load():
    specs = []
    for m in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
        if m.name.startswith("_"):
            continue
        specs.append(importlib.import_module("vl_specs." + m.name).SPEC)
    specs.sort(key=lambda s: s["order"])
    return {s["name"]: s for s in specs}
```

Then: `python3 <ws>/migrate_specs.py`
Expected: fifteen `wrote <name>` lines; `ls skills/slide-maker/scripts/vl_specs | wc -l` → 16.

Note the image-led `image_pages`: those languages draw the caller's picture on cover, image_text, quote, data and closing; check it against `LAYOUTS[name]` keys and correct the generator line if a page differs (a ruling if it does).

- [ ] **Step 4: Check the generated manifests validate**

Run: `cd skills/slide-maker && python3 -c "import sys; sys.path.insert(0,'scripts'); import vl_specs, vl_contract as vc; print(vc.validate_all(vl_specs.load()) or 'all valid')"`
Expected: `all valid`. Any problem printed is a real contract violation in today's data: rule on it in the ledger (fix the data if the drawing stays identical; otherwise record it for Phase 3) — never loosen the validator to pass.

- [ ] **Step 5: Build the tables from the registry** — in `skills/slide-maker/scripts/visual_languages.py`:

1. Replace the block from `LANGS = {` (line 37) through the end of `EXTRA_PAGES = {…}` (line 257) with:

```python
import vl_specs as _vl_specs
# Every language is ONE manifest, scripts/vl_specs/<name>.py, checked by scripts/vl_contract.py; the tables below are
# built from them and keep their old names for every importer. Each language's GROUNDS: its own light paper, and ONE
# contrast ground (user's decision, 2026-10-04); every text ink passes 4.5:1 on its ground AND panel (the contract
# checks it). The storybook contrast is a meadow-green PAPER, not a dark ground: light watercolours would halo on dark.
REGISTRY = _vl_specs.load()
LANGS = {n: s["look"] for n, s in REGISTRY.items()}
VARIANTS = {n: {g: {k: v for k, v in gd.items() if k not in ("dark", "roles")} for g, gd in s["grounds"].items()}
            for n, s in REGISTRY.items()}
NATIVE = tuple(n for n, s in REGISTRY.items() if s["kind"] == "drawn")          # drawn, no pictures needed (vl_native.py)
# the pages on which a drawn language draws the caller's picture; image= anywhere else is refused, naming these — it
# was dropped without a word, even a path to no file (robustness + docs audits, 2026-10-09)
NATIVE_IMAGE_PAGES = {n: REGISTRY[n]["image_pages"] for n in NATIVE}
IMAGE_LED = tuple(n for n, s in REGISTRY.items() if s["kind"] == "image-led")    # built around the caller's pictures
# words only the CALLER can give — never invented by the kit; absent means nothing is drawn
NATIVE_EXTRAS = {n: tuple(REGISTRY[n]["extras"]) for n in NATIVE if REGISTRY[n]["extras"]}
# the pages that DRAW each extra; on any other page it is refused, never silently dropped (non-Claude run, 2026-10-05)
EXTRA_PAGES = {x: d["pages"] for s in REGISTRY.values() for x, d in s["extras"].items() if d["pages"] != "any"}
```

Before deleting, list every comment line in the removed block (`git diff -U0 | grep '^-\s*#'` after the edit) and carry each one that explains a language's choice into that language's manifest as a comment above `SPEC` (the generator cannot carry comments). Step 7 checks this.

2. Replace `TYPE = {` (line ~602) through its closing `}` with `TYPE = {n: s["type"] for n, s in REGISTRY.items()}`, carrying its per-language comments into the manifests the same way.
3. Replace `_SAMPLE_COPY_NATIVE = {` through its closing `}` with `_SAMPLE_COPY_NATIVE = {n: REGISTRY[n]["samples"]["copy"] for n in NATIVE}`.
4. Replace the `_DISPLAY_NAMES` / `_RATIONALE` definitions and their `.update` / item assignments (lines ~2150–2175) with:

```python
_DISPLAY_NAMES = {n: s["display"]["en"] for n, s in REGISTRY.items()}
_RATIONALE = {n: s["rationale"] for n, s in REGISTRY.items()}
```

5. In the `rs.register` loop (line ~579) replace `globals()["_ground_" + _n]` / `globals()["_card_" + _n]` with `globals()[REGISTRY[_n]["painters"]["ground"]]` / `globals()[REGISTRY[_n]["painters"]["card"]]`.

- [ ] **Step 6: Prove nothing changed**

Run: `python3 <ws>/snapshot_tables.py skills/slide-maker/scripts <ws>/tables_after.json && cmp <ws>/tables_before.json <ws>/tables_after.json && echo IDENTICAL`
Expected: `IDENTICAL`. A difference is a migration bug — fix the generator or the build code, regenerate, re-run.

Run: `cd skills/slide-maker && python3 tests/test_visual_languages.py | tail -1 && python3 tests/test_vl_contract.py | tail -1`
Expected: `[test_visual_languages] ok` (every sample fingerprint unchanged) and `NN passed, 0 failed`.

- [ ] **Step 7: Check no explanatory comment was lost**

Run (from the repo root):
```bash
git diff -U0 skills/slide-maker/scripts/visual_languages.py | grep '^-' | grep -v '^---' | sed -n 's/^-\s*#\s*//p' | sort -u > <ws>/removed_comments.txt
python3 - <<'EOF'
from pathlib import Path
ws = Path("<ws>")
specs = "".join(p.read_text() for p in Path("skills/slide-maker/scripts/vl_specs").glob("*.py"))
vl = Path("skills/slide-maker/scripts/visual_languages.py").read_text()
lost = [l for l in (ws / "removed_comments.txt").read_text().splitlines() if l.strip() and l.strip() not in specs and l.strip() not in vl]
print("\n".join(lost) or "no comment lost")
EOF
```
Expected: `no comment lost` (after carrying them over in Step 5).

- [ ] **Step 8: Inventory** — in `skills/slide-maker/scripts/check_inventory.py` change line 38 to:

```python
GROUPS = (("scripts", "*.py"), ("scripts/vl_specs", "*.py"), ("agents", "*"), ("references", "*.md"))
```

and add to `references/file-inventory.md`, after the `vl_native3.py` entry:

```markdown
- `vl_contract.py` — the visual-language contract: `validate(spec)` / `validate_all(specs)` check a manifest (identity,
  offer topics, grounds with their `dark` flag and palette roles, type roles, pages, extras, derived words, samples,
  painters); pure, imports nothing from the skill.
- `vl_specs/` — one manifest per visual language (`SPEC`), loaded by `vl_specs/__init__.py` (`load()`, ordered by
  `order`); `visual_languages.py` builds its tables from them: `editorial.py`, `soft.py`, `collage.py`, `storybook.py`,
  `ink.py`, `poster.py`, `cutpaper.py`, `drafting.py`, `starlit.py`, `broadsheet.py`, `journal.py`, `tally.py`,
  `chalkboard.py`, `interface.py`, `wayfinding.py`.
```

Run: `cd skills/slide-maker && python3 scripts/check_inventory.py | tail -1`
Expected: `… 0 problem(s).` (`__init__.py` is listed by the `vl_specs/__init__.py` mention).

- [ ] **Step 9: The suites the migration must keep green**

Run, from `skills/slide-maker`, each separately: `python3 tests/test_native_languages.py | tail -1`, `python3 tests/test_native_languages_p4.py | tail -1`, `python3 tests/test_native_languages_p5.py | tail -1`, `python3 tests/test_vl_audit_fixes.py | tail -1`, `python3 tests/test_native_generality.py | tail -1`, `python3 tests/test_vl_ground_variants.py | tail -1`
Expected: each ends `… 0 failed` / `ok`.

- [ ] **Step 10: Commit**

```bash
git add skills/slide-maker/scripts/vl_specs skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/check_inventory.py skills/slide-maker/references/file-inventory.md skills/slide-maker/tests/test_vl_contract.py
git commit -m "visual languages: one manifest per language (vl_specs), the tables built from them — samples byte-identical"
```

---

### Task 3: Conformance over every registered language + the CLI

**Files:**
- Create: `skills/slide-maker/scripts/vl_conformance.py`, `skills/slide-maker/scripts/check_vl_contract.py`
- Modify: `skills/slide-maker/tests/test_vl_contract.py` (part 2), `.github/workflows/ci.yml`, `skills/slide-maker/references/file-inventory.md`

**Interfaces:**
- Consumes: `visual_languages.REGISTRY`, `vl_native.COMPOSERS`, `visual_languages.LAYOUTS`, `sigs.EXAMPLES`, `visual_languages.build_sample`, `visual_languages.initials` is not used (interface's `vl_native3.initials`).
- Produces (each returns a list of problem strings, empty = conforming):
  - `vl_conformance.pages_missing(name, registry=None) -> list[str]`
  - `vl_conformance.invented_words(name) -> list[str]`
  - `vl_conformance.extras_not_refused(name) -> list[str]`
  - `vl_conformance.assets_missing(name) -> list[str]`
  - `vl_conformance.suites_not_registry_driven() -> list[str]`
  - `vl_conformance.allowed_tokens(name, caller_texts) -> set[str]` (exposed for its own tests)

**Ruling recorded here (spec §4.3 items 2–3):** the page × canvas × ground × script build matrix and the own-pages lint are already run for every entry of `vl.LANGS` by `tests/test_native_generality.py` (4 canvases × en/zh/mixed long copy, every page must build) and `tests/test_vl_audit_fixes.py` (B2: own pages, no hard lint). Rebuilding them here would double the CI time; `suites_not_registry_driven()` instead asserts both iterate the registry, so a new language is covered by them automatically.

- [ ] **Step 1: Write the failing tests** — append part 2 to `tests/test_vl_contract.py` above the `# ── part 2 (Task 3) and part 3 …` line:

```python
# ── part 2: conformance over every registered language ──
import vl_conformance as vcf
for n in REG:
    check(vcf.pages_missing(n) == [], "{}: all seven pages have a composition ({})".format(n, vcf.pages_missing(n)))
    inv = vcf.invented_words(n)
    check(inv == [], "{}: every word on its sample pages is the caller's or declared derived ({})".format(n, inv[:3]))
    nr = vcf.extras_not_refused(n)
    check(nr == [], "{}: every extra is refused by name off its pages ({})".format(n, nr[:2]))
    am = vcf.assets_missing(n)
    check(am == [], "{}: samples, sigs scaffold and docs rows exist ({})".format(n, am[:3]))
check(vcf.suites_not_registry_driven() == [], "the build-matrix and own-pages suites iterate the registry ({})".format(
    vcf.suites_not_registry_driven()))
# Review Focus 3: a manifest with no compositions names every missing page, no crash
fx = good_spec()
miss = vcf.pages_missing("fixture", registry={"fixture": fx})
check(len(miss) == 7 and all("fixture" in m for m in miss), "a language with no compositions names its 7 missing pages ({})".format(miss[:1]))
# Review Focus 4: re-cased and clause-broken caller words are the caller's; a new word is not
tok = vcf.allowed_tokens("journal", ["Why every street deserves a place, not a bin", "社区修理网络，年度回顾"])
check({"WHY", "STREET", "DESERVES"} <= tok, "re-cased caller words are allowed tokens")
check({"社", "区", "年"} <= tok, "Chinese caller characters are allowed tokens")
check("ABSTRACT" in tok and "摘" in tok, "a declared derived label is an allowed token")
check("REVOLUTION" not in tok, "a word the caller never gave is not allowed")
```

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | tail -3`
Expected: FAIL — `ModuleNotFoundError: No module named 'vl_conformance'`.

- [ ] **Step 2: Write `scripts/vl_conformance.py`**

```python
"""Build-time conformance checks of the visual-language contract, over any registered language (tests/test_vl_contract.py
runs them for all; scripts/check_vl_contract.py for the ones you name). Each returns a list of problems, empty = conforms.
Spec: docs/superpowers/specs/2026-10-15-visual-language-system-design.md §4.3."""
import contextlib
import io
import re
import tempfile
from pathlib import Path

import deckkit as dk
import visual_languages as vl
import vl_native as vn
from vl_contract import PAGES

SKILL = Path(__file__).resolve().parent.parent
_CJK = re.compile(r"[぀-ヿ㐀-鿿豈-﫿가-힯]")
_WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")
# numerals a page may number itself with (page / point / section / sheet / figure numbers): 1-2 digits, CJK numerals
# one to ten, circled one to twenty — a longer number must be the caller's
_NUMERAL = re.compile(r"^(?:\d{1,2}|[一二三四五六七八九十]|[①-⑳])$")


def pages_missing(name, registry=None):
    reg = registry or vl.REGISTRY
    spec = reg[name]
    if spec["kind"] == "image-led":
        have = set(vl.LAYOUTS.get(name, {})) | {"points"}       # points: the shared image-led points page
    else:
        have = set(vn.COMPOSERS.get(name, {}))
    return ["{}: no composition for page {!r}".format(name, p) for p in PAGES if p not in have]


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _strings(v)


def allowed_tokens(name, caller_texts):
    """Upper-cased Latin words and single CJK characters the caller gave, plus the language's declared derived words."""
    tok = set()
    for t in caller_texts:
        tok |= {w.upper() for w in _WORD.findall(t)}
        tok |= set(_CJK.findall(t))
    for d in vl.REGISTRY[name]["derived"]:
        for words in d["words"].values():
            for w in words:
                tok |= {x.upper() for x in _WORD.findall(w)}
                tok |= set(_CJK.findall(w))
    return tok


def _sample_deck(name):
    """Build the language's sample deck (both grounds) and return (pptx paths, the caller's strings)."""
    td = Path(tempfile.mkdtemp(prefix="vlconf_"))
    paths = []
    for g in vl.VARIANTS[name]:
        with contextlib.redirect_stdout(io.StringIO()):
            paths.append(vl.build_sample(name, td, W=10.0, H=5.625, ground=g))
    if name in vl.NATIVE:
        texts = list(_strings(vl._SAMPLE_COPY_NATIVE[name]))
    else:
        texts = list(_strings(vl._SAMPLE_COPY["watercolour" if name == "storybook" else "photo"]))
    return paths, texts


def invented_words(name):
    from pptx import Presentation
    paths, texts = _sample_deck(name)
    tok = allowed_tokens(name, texts)
    probs = []
    for p in paths:
        prs = Presentation(str(p))
        for i, s in enumerate(prs.slides, 1):
            for sh in s.shapes:
                if not sh.has_text_frame or sh.top is None or sh.top < 0:      # the off-page a11y title repeats a field
                    continue
                for w in _WORD.findall(sh.text_frame.text):
                    if w.upper() not in tok and not _NUMERAL.match(w):
                        probs.append("{} slide {}: {!r} is not the caller's and not declared derived".format(p.name, i, w))
                for c in _CJK.findall(sh.text_frame.text):
                    if c not in tok and not _NUMERAL.match(c):
                        probs.append("{} slide {}: {!r} is not the caller's and not declared derived".format(p.name, i, c))
    return sorted(set(probs))


def extras_not_refused(name):
    spec = vl.REGISTRY[name]
    probs = []
    for x, d in spec["extras"].items():
        if d["pages"] == "any":
            continue
        off = [p for p in PAGES if p not in d["pages"] and p != "image_text"][0]
        prs = dk.blank_deck(10.0, 5.625)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(name, prs)
        fields = {"cover": dict(title="A title"), "section": dict(number="1", title="A section"),
                  "points": dict(title="Points", items=["One", "Two"]), "quote": dict(quote="A quote."),
                  "data": dict(number="3", label="a label"), "closing": dict(title="Thanks")}[off]
        try:
            getattr(k, off)(k.new_slide(), **fields, **{x: "value"})
            probs.append("{}: {}= on {} was accepted (it draws only on {})".format(name, x, off, d["pages"]))
        except (ValueError, TypeError) as e:
            if x not in str(e):
                probs.append("{}: {}= on {} was refused without naming it: {}".format(name, x, off, str(e)[:100]))
    return probs


def assets_missing(name):
    import json
    import sigs
    probs = []
    stems = [vl._sample_stem(name, g) for g in vl.VARIANTS[name]]
    man = json.loads((SKILL / "assets" / "vl" / "samples" / "manifest.json").read_text())
    for st in stems:
        if not (SKILL / "assets" / "vl" / "samples" / (st + ".jpg")).exists():
            probs.append("{}: no bundled sample {}.jpg".format(name, st))
        if st not in json.dumps(man):
            probs.append("{}: sample {} has no fingerprint in manifest.json".format(name, st))
    if not any(('"{}"'.format(name) in src) or ("'{}'".format(name) in src)
               for k, src in sigs.EXAMPLES.items() if k.startswith("vl_")):
        probs.append("{}: no sigs.py --example vl_* scaffold names it".format(name))
    ref = (SKILL / "references" / "visual-languages.md").read_text(encoding="utf-8")
    if "| `{}` |".format(name) not in ref:
        probs.append("{}: references/visual-languages.md has no table row for it".format(name))
    for readme in ("README.md", "README_CN.md"):
        if "samples/{}.jpg".format(name) not in (SKILL.parent.parent / readme).read_text(encoding="utf-8"):
            probs.append("{}: {} gallery has no cell for it".format(name, readme))
    return probs


def suites_not_registry_driven():
    probs = []
    gen = (SKILL / "tests" / "test_native_generality.py").read_text(encoding="utf-8")
    if "for name in vl.LANGS" not in gen:
        probs.append("tests/test_native_generality.py no longer iterates vl.LANGS — a new language would skip the build matrix")
    aud = (SKILL / "tests" / "test_vl_audit_fixes.py").read_text(encoding="utf-8")
    if "vl.LANGS" not in aud:
        probs.append("tests/test_vl_audit_fixes.py no longer iterates vl.LANGS — a new language would skip the own-pages lint")
    return probs
```

- [ ] **Step 3: Run the tests; calibrate the never-invent check**

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | grep -E "FAIL|passed"`
Expected: the unit checks pass. Any `invented_words` finding is one of two things — rule on each in the ledger:
- a word the kit derives that the manifest does not declare yet (a structural label, a localised word) → add it to that manifest's `derived` with `what` saying where it comes from;
- a word the kit really invents → a defect: write a test that reproduces it in `tests/test_vl_contract.py`, watch it fail, fix the composition, watch it pass.
Any `extras_not_refused` finding is a defect handled the same way (RED → GREEN). Re-run until `0 failed`.

- [ ] **Step 4: The CLI** — create `skills/slide-maker/scripts/check_vl_contract.py`:

```python
#!/usr/bin/env python3
"""Check visual languages against the contract: the manifest (scripts/vl_contract.py) and the build-time conformance
(scripts/vl_conformance.py). usage: check_vl_contract.py [name …]   (default: every registered language)"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vl_contract as vc            # noqa: E402
import vl_conformance as vcf        # noqa: E402
import visual_languages as vl       # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="languages to check (default: all)")
    a = ap.parse_args(argv)
    names = a.names or list(vl.REGISTRY)
    unknown = [n for n in names if n not in vl.REGISTRY]
    if unknown:
        print("unknown language(s) {} — registered: {}".format(unknown, ", ".join(vl.REGISTRY)))
        return 2
    probs = [p for p in vc.validate_all(vl.REGISTRY) if any(n in p for n in names)]
    for n in names:
        for fn in (vcf.pages_missing, vcf.invented_words, vcf.extras_not_refused, vcf.assets_missing):
            probs += fn(n)
    for p in probs:
        print("  FAIL " + p)
    print("[vl-contract] {} language(s), {} problem(s)".format(len(names), len(probs)))
    if not probs:
        print("NEXT: python3 {}/tests/test_vl_contract.py".format(Path(__file__).resolve().parent.parent))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run: `cd skills/slide-maker && python3 scripts/check_vl_contract.py tally wayfinding; echo "exit $?"`
Expected: `[vl-contract] 2 language(s), 0 problem(s)`, a NEXT line, `exit 0`. And `python3 scripts/check_vl_contract.py nosuch; echo "exit $?"` → the unknown-language line and `exit 2`.

- [ ] **Step 5: Wire CI and the inventory** — in `.github/workflows/ci.yml`, after the "Native visual languages, third set (interface, wayfinding)" step, add (same pattern as that step):

```yaml
      - name: "Visual-language contract (manifests, never-invent, extras, assets)"
        run: |
          set -o pipefail
          python tests/test_vl_contract.py | tee /tmp/vlcontract.log
          grep -qE "^[0-9]+ passed, 0 failed" /tmp/vlcontract.log || {
            echo "::error::test_vl_contract did not run to completion"; exit 1; }
```

and to `references/file-inventory.md`, after the `vl_specs/` entry:

```markdown
- `vl_conformance.py` — build-time checks of the contract over any registered language: all seven pages composed,
  no word on a sample page that is neither the caller's nor declared derived, every extra refused by name off its
  pages, samples / sigs scaffold / docs rows present, and the build-matrix suites still iterating the registry.
- `check_vl_contract.py` — `check_vl_contract.py [name …]`: the manifest and the conformance checks for the named
  languages (all by default), with a NEXT line.
```

Run: `cd skills/slide-maker && python3 scripts/check_inventory.py | tail -1 && python3 scripts/check_tests_wired.py | tail -1`
Expected: both `0 problem(s)`.

- [ ] **Step 6: Commit**

```bash
git add skills/slide-maker/scripts/vl_conformance.py skills/slide-maker/scripts/check_vl_contract.py skills/slide-maker/tests/test_vl_contract.py skills/slide-maker/scripts/vl_specs .github/workflows/ci.yml skills/slide-maker/references/file-inventory.md
git commit -m "visual-language contract: conformance over every registered language, check_vl_contract.py, CI"
```
(Add any composition files a Step 3 defect fix touched to the `git add` list.)

---

### Task 4: Docs and the offer guidance generated from the registry

**Files:**
- Create: `skills/slide-maker/scripts/vl_docs.py`
- Modify: `skills/slide-maker/scripts/directions_diversity.py:244-262`, `skills/slide-maker/SKILL.md` (the visual-language bullet: "the eleven drawn ones below", the native list), `skills/slide-maker/references/visual-languages.md` (title line, "## The fifteen languages", the guidance sentence at "Guidance, not a rule:"), `skills/slide-maker/references/interview-protocol.md` (the native-language bullet), `skills/slide-maker/references/codex-runtime.md` (the native list at line ~425), `README.md` / `README_CN.md` (the counts sentence and the "How one gets picked" guidance), `skills/slide-maker/.skill-lossless-allow.json`, `.github/workflows/ci.yml`, `skills/slide-maker/references/file-inventory.md`
- Test: `skills/slide-maker/tests/test_vl_contract.py` (part 3)

**Interfaces:**
- Consumes: `visual_languages.REGISTRY`.
- Produces: `vl_docs.render(block: str) -> str`; `vl_docs.write() -> list[str]` (files changed); `vl_docs.check() -> list[str]` (problems); CLI `vl_docs.py --write | --check`. Blocks: `count-all`, `count-drawn`, `count-image`, `count-all-zh`, `count-drawn-zh`, `list-drawn`, `offer-arrow`, `offer-paren`, `offer-zh`.
- Produces: `directions_diversity.NATIVE_LANGS` built from the registry.

Block formats (the generator's output, exactly):
- `count-all` / `count-drawn` / `count-image`: the English number word (`fifteen`, `eleven`, `four`);
- `count-all-zh` / `count-drawn-zh`: the Chinese numeral (`十五`, `十一`);
- `list-drawn`: the drawn languages as `` `ink` · `poster` · … `` in registry order;
- `offer-arrow`: `` culture, history, craft → `ink`; launch, manifesto, opinion → `poster`; … `` ending with `.` (drawn languages, registry order);
- `offer-paren`: `` `ink` (culture, history, craft), `poster` (launch, manifesto, opinion), … or `wayfinding` (…) ``;
- `offer-zh`: `文化、历史、器物 → 水墨；…；路线图、…、交通与城市 → 导视线路。`

A block in a doc is `<!-- vl:NAME -->generated text<!-- /vl -->` (inline, invisible when rendered).

- [ ] **Step 1: Write the failing tests** — append part 3 to `tests/test_vl_contract.py` above the `# ── part 2 (Task 3) and part 3 …` line:

```python
# ── part 3: docs blocks follow the registry ──
import vl_docs
check(vl_docs.render("count-all") == "fifteen" and vl_docs.render("count-drawn") == "eleven"
      and vl_docs.render("count-image") == "four", "the count blocks read fifteen / eleven / four")
check(vl_docs.render("count-all-zh") == "十五" and vl_docs.render("count-drawn-zh") == "十一", "the Chinese counts read 十五 / 十一")
check(vl_docs.render("list-drawn").startswith("`ink` · `poster`") and vl_docs.render("list-drawn").endswith("`wayfinding`"),
      "the drawn list runs ink … wayfinding")
check("culture, history, craft → `ink`" in vl_docs.render("offer-arrow"), "the arrow guidance names ink's topics")
check("`ink` (culture, history, craft)" in vl_docs.render("offer-paren"), "the parenthesised guidance names ink's topics")
check("文化、历史、器物 → 水墨" in vl_docs.render("offer-zh"), "the Chinese guidance names 水墨's topics")
check(vl_docs.check() == [], "every docs block is current ({})".format(vl_docs.check()[:2]))
# Review Focus 5: a hand edit inside a block is caught, and --write restores it
import shutil, tempfile
tmp = Path(tempfile.mkdtemp())
src = ROOT / "references" / "visual-languages.md"
shutil.copy(src, tmp / "vl.md")
try:
    src.write_text(src.read_text(encoding="utf-8").replace("<!-- vl:count-all -->fifteen", "<!-- vl:count-all -->nine", 1),
                   encoding="utf-8")
    probs = vl_docs.check()
    check(any("visual-languages.md" in p and "count-all" in p for p in probs), "a hand-edited block is named ({})".format(probs[:1]))
    vl_docs.write()
    check(vl_docs.check() == [], "--write restores the block")
finally:
    shutil.copy(tmp / "vl.md", src)
```

Run: `cd skills/slide-maker && python3 tests/test_vl_contract.py | tail -3`
Expected: FAIL — `ModuleNotFoundError: No module named 'vl_docs'`.

- [ ] **Step 2: Write `scripts/vl_docs.py`**

```python
#!/usr/bin/env python3
"""The docs' visual-language lists, counts and offer guidance, generated from the registry (scripts/vl_specs/).

A doc carries a block as <!-- vl:NAME -->text<!-- /vl -->; `--write` regenerates every block, `--check` (CI) fails on any
block that differs. A hand-written count once drifted ("the nine DRAWN languages" after two more were added); now it
cannot. usage: vl_docs.py --write | --check"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visual_languages as vl       # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent
DOCS = [SKILL / "SKILL.md", SKILL / "references" / "visual-languages.md", SKILL / "references" / "interview-protocol.md",
        SKILL / "references" / "codex-runtime.md", REPO / "README.md", REPO / "README_CN.md"]
_BLOCK = re.compile(r"<!-- vl:([a-z\-]+) -->(.*?)<!-- /vl -->", re.S)
_EN = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
       "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
_ZH = "零一二三四五六七八九十"


def _zh(n):
    if n <= 10:
        return _ZH[n]
    if n < 20:
        return "十" + _ZH[n - 10]
    return _ZH[n // 10] + "十" + (_ZH[n % 10] if n % 10 else "")


def render(block):
    reg = vl.REGISTRY
    drawn = [s for s in reg.values() if s["kind"] == "drawn"]
    image = [s for s in reg.values() if s["kind"] == "image-led"]
    if block == "count-all":
        return _EN[len(reg)]
    if block == "count-drawn":
        return _EN[len(drawn)]
    if block == "count-image":
        return _EN[len(image)]
    if block == "count-all-zh":
        return _zh(len(reg))
    if block == "count-drawn-zh":
        return _zh(len(drawn))
    if block == "list-drawn":
        return " · ".join("`{}`".format(s["name"]) for s in drawn)
    if block == "offer-arrow":
        return "; ".join("{} → `{}`".format(", ".join(s["offer"]["en"]), s["name"]) for s in drawn) + "."
    if block == "offer-paren":
        parts = ["`{}` ({})".format(s["name"], ", ".join(s["offer"]["en"])) for s in drawn]
        return ", ".join(parts[:-1]) + " or " + parts[-1]
    if block == "offer-zh":
        return "；".join("{} → {}".format("、".join(s["offer"]["zh"]), s["display"]["zh"]) for s in drawn) + "。"
    raise KeyError("unknown vl docs block {!r}".format(block))


def _rewrite(text):
    return _BLOCK.sub(lambda m: "<!-- vl:{} -->{}<!-- /vl -->".format(m.group(1), render(m.group(1))), text)


def write():
    changed = []
    for p in DOCS:
        t = p.read_text(encoding="utf-8")
        n = _rewrite(t)
        if n != t:
            p.write_text(n, encoding="utf-8")
            changed.append(str(p))
    return changed


def check():
    probs = []
    for p in DOCS:
        for m in _BLOCK.finditer(p.read_text(encoding="utf-8")):
            want = render(m.group(1))
            if m.group(2) != want:
                probs.append("{}: block vl:{} reads {!r}, the registry says {!r}".format(
                    p.relative_to(REPO), m.group(1), m.group(2)[:60], want[:60]))
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        for c in write():
            print("wrote", c)
        return 0
    probs = check()
    for p in probs:
        print("  FAIL " + p)
    print("[vl-docs] {} problem(s)".format(len(probs)) + ("" if not probs else " — run: python3 {} --write".format(
        Path(__file__).resolve())))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Put the blocks into the docs** — wrap today's text, keeping the sentence around it (the generated text must equal the text it replaces, apart from the README rewording noted below):
- `references/visual-languages.md` line 1: `# Visual languages — <!-- vl:count-all -->fifteen<!-- /vl --> complete looks: <!-- vl:count-image -->four<!-- /vl --> image-led, <!-- vl:count-drawn -->eleven<!-- /vl --> drawn`; the heading `## The <!-- vl:count-all -->fifteen<!-- /vl --> languages`; the sentence after `Guidance, not a rule: ` becomes `<!-- vl:offer-arrow -->…<!-- /vl -->`; "The eleven native" → `The <!-- vl:count-drawn -->eleven<!-- /vl --> native`; "On the eleven DRAWN languages" → `On the <!-- vl:count-drawn -->eleven<!-- /vl --> DRAWN languages`.
- `references/interview-protocol.md`: "one of the fifteen visual languages" / "eleven drawn" → count blocks; the parenthesised list `` `ink` (culture, history, craft) … or `wayfinding` (…) `` → `<!-- vl:offer-paren -->…<!-- /vl -->`.
- `references/codex-runtime.md` line ~425: the native list → `<!-- vl:list-drawn -->…<!-- /vl -->` (its separator changes from `, … or` to ` · `: a ruling — the block has one format).
- `SKILL.md`: "the eleven drawn ones below" → `the <!-- vl:count-drawn -->eleven<!-- /vl --> drawn ones below`; the native list in the NATIVE bullet → `<!-- vl:list-drawn -->…<!-- /vl -->`.
- `README.md`: "ships fifteen complete" / "Eleven draw" → count blocks (`<!-- vl:count-all -->fifteen<!-- /vl -->`; "Eleven" at a sentence start stays capitalised by putting the block after "The": rephrase to "The other <!-- vl:count-drawn -->eleven<!-- /vl --> draw …"); the guidance list after "The fit is guidance, not a lookup: " → `<!-- vl:offer-arrow -->…<!-- /vl -->` (the README's own wording "a launch, manifesto or opinion → poster" becomes the shared arrow wording — a ruling).
- `README_CN.md`: "还内置十五套" → `还内置<!-- vl:count-all-zh -->十五<!-- /vl -->套`, "另外十一套" → `另外<!-- vl:count-drawn-zh -->十一<!-- /vl -->套`, the list after "对应关系是参考，不是查表：" → `<!-- vl:offer-zh -->…<!-- /vl -->`.

Run: `cd skills/slide-maker && python3 scripts/vl_docs.py --write && python3 scripts/vl_docs.py --check && git -C ../.. diff --stat`
Expected: `[vl-docs] 0 problem(s)`; the diff touches only those files. Read every changed line (`git diff -U0`) and confirm each rendered sentence still reads correctly in its context.

- [ ] **Step 4: SKILL.md stays lossless** — the two SKILL.md lines changed shape:

Run: `cd ../.. && python3 skills/slide-maker/scripts/check_skill_lossless.py --baseline "$(git merge-base main HEAD):skills/slide-maker/SKILL.md" --allow skills/slide-maker/.skill-lossless-allow.json --report /tmp/skill-lost.md | tail -1`
Expected: either `LOSSLESS` or the two changed lines listed; for each, add a waiver to `.skill-lossless-allow.json` with the reason "Rewritten in place, not deleted: the count / list is now a generated vl block (scripts/vl_docs.py); the sentence is otherwise unchanged." and re-run → `LOSSLESS`.

- [ ] **Step 5: directions_diversity from the registry** — in `scripts/directions_diversity.py`, replace the `NATIVE_LANGS = (…)` tuple (line ~244) with a lazy registry read, and the hand-written guidance in its message (lines ~257–262) with the generated paren list:

```python
def _native_langs():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import visual_languages as _vl
    return tuple(n for n, s in _vl.REGISTRY.items() if s["kind"] == "drawn")


NATIVE_LANGS = _native_langs()
```

and in the message string replace the literal `"ink (culture, history, craft), poster (…) … or wayfinding (…)"` with `vl_docs.render("offer-paren").replace("`", "")` (import `vl_docs` the same lazy way). Add `from pathlib import Path` to the imports if absent.

Run: `cd skills/slide-maker && python3 -c "import sys; sys.path.insert(0,'scripts'); import directions_diversity as d; print(d.NATIVE_LANGS)" && python3 tests/test_vl_contract.py | tail -1`
Expected: the eleven drawn names; `NN passed, 0 failed`. Also run every test that imports `directions_diversity`: `grep -l directions_diversity tests/*.py | while read t; do python3 "$t" | tail -1; done` → all pass.

- [ ] **Step 6: CI + inventory** — in `.github/workflows/ci.yml`, after the contract step add:

```yaml
      - name: "Visual-language docs blocks match the registry"
        run: python scripts/vl_docs.py --check
```

and in `references/file-inventory.md` after `check_vl_contract.py`:

```markdown
- `vl_docs.py` — `--write` / `--check` the `<!-- vl:NAME -->…<!-- /vl -->` blocks (counts, the drawn list, the offer
  guidance in three wordings) in SKILL.md, the references and both READMEs, from the registry; CI runs `--check`.
```

Run: `cd skills/slide-maker && python3 scripts/check_inventory.py | tail -1 && python3 tests/test_visual_languages.py | tail -1`
Expected: `0 problem(s)`; `[test_visual_languages] ok`.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/vl_docs.py skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/SKILL.md skills/slide-maker/references/visual-languages.md skills/slide-maker/references/interview-protocol.md skills/slide-maker/references/codex-runtime.md skills/slide-maker/references/file-inventory.md skills/slide-maker/.skill-lossless-allow.json skills/slide-maker/tests/test_vl_contract.py README.md README_CN.md .github/workflows/ci.yml
git commit -m "visual-language docs: counts, the drawn list and the offer guidance generated from the registry"
```

---

### Task 5: Verification and close-out

**Files:** none new (fixes only, each with its RED test).

- [ ] **Step 1: Full local CI** — `cisteps.py` over every CI step in chunks under 10 minutes (`CI_FROM`/`CI_TO`), foreground, sequentially.
Expected: every step green. A failure is investigated, reproduced by a failing test, fixed, and the chunk re-run.

- [ ] **Step 2: Linux font simulation** over `tests/test_vl_contract.py`, `tests/test_native_generality.py`, `tests/test_native_languages_p5.py` (`cisim.py`).
Expected: the same pass counts as on the Mac (face-precise checks skip, never fail).

- [ ] **Step 3: An author's dry run** — prove the "a new language is a manifest" claim on a throwaway copy: in a temporary clone (`git worktree add --detach /tmp/vlwt HEAD`), copy `vl_specs/tally.py` to `vl_specs/tallytwo.py` with `name`/`order`/`display` changed, run `python3 scripts/check_vl_contract.py tallytwo`.
Expected: the only problems are the missing compositions (seven, named), the missing samples and docs rows — nothing crashes, nothing silently passes. Remove the worktree (`git worktree remove /tmp/vlwt`).

- [ ] **Step 4: Final review** — `review-package` for the branch; one fresh reviewer; fix Critical/Important with RED→GREEN tests; park minors in the ledger.

- [ ] **Step 5: Report** — commits on the branch, unpushed; the rulings; deferred minors. No push without the user's word.
