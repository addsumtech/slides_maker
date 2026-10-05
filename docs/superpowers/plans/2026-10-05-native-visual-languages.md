# Native visual languages (P3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Four visual languages that need no pictures — `ink`, `poster`, `cutpaper`, `blueprint` — each a finished deck from the caller's words, plus a PowerPoint-safety lint and the "always offer a native language when a deck has no pictures" rule on both runtimes.

**Architecture:** The four join the existing `LANGS`/`VARIANTS`/`TYPE` tables in `scripts/visual_languages.py` (so `use()`, grounds, `direction()`, samples and the language gate work unchanged); their page functions dispatch to a new `scripts/vl_native.py`, whose compositions draw with a new `scripts/native_art.py` (native, page-clipped shapes) and reuse the kit's measured `_flow` for horizontal text. A new `scripts/ooxml_safety.py` is called by `lint_deck` for every deck.

**Tech Stack:** Python 3.9+, python-pptx, lxml, Pillow; LibreOffice for renders; tests are plain scripts (`check()` + a final `[name] ok` / `N passed, 0 failed` line) wired one step each into `.github/workflows/ci.yml`.

**Spec:** `docs/superpowers/specs/2026-10-05-native-visual-languages-design.md`

**Look-dev reference (approved look, throwaway):** `/private/tmp/claude-501/-Users-donghanglyu/2866adfa-b4b0-4b62-8845-b0d5410c5fde/scratchpad/lookdev/lookdev.py` and its renders in `~/Desktop/slide-maker 新设计语言 样张/`.

## Global Constraints

- Nothing drawn past the slide edge: every native-art shape lies inside `[0, W] × [0, H]` (PowerPoint's editing view shows off-page geometry).
- Every OOXML angle written is in `0..21599999`; alphas and gradient positions in `0..100000`; no negative `blurRad`/`dist`.
- System fonts only; `fonts="both"` uses faces on macOS AND Windows; the Windows column is unverified on this machine.
- Figures never in Georgia (old-style digits): numerals use Times New Roman, Impact or Trebuchet MS.
- Every text ink ≥ 4.5:1 on the ground or panel it sits on, on every ground.
- The kit never invents words: `seal=`, `highlight=`, `project=`, `icons=` come from the caller; absent → nothing drawn.
- Vertical setting only for CJK (Han/kana) text with no Latin letters or digits.
- A figure implying structure (iso stack, numbered leaders, dimension line) is drawn only from the page's content.
- Image-led languages (`editorial`, `soft`, `collage`, `storybook`) behave exactly as before.
- Bundled samples are JPG ≤ 350 KB (SkillHub filters PNG).
- Tests: plain scripts under `skills/slide-maker/tests/`, each wired into `ci.yml` (`check_tests_wired.py` holds it); every new script listed in `references/file-inventory.md` (`check_inventory.py`).
- Never push before the full suite, the CI-steps run and the font simulation are green; stage named paths only.

## Review Focus

1. **A Latin or Korean title on `ink`** — must be set horizontally in the same composition, never as a sideways vertical column (test in Task 4).
2. **The longest realistic copy** (a 14-word English title, a 30-character Chinese title, 4 points of 2 lines) on a portrait 7.5×13.333 canvas — fits or refuses with `VLTextOverflow`, never spills off the page (Task 4–7 tests run every page on the portrait canvas).
3. **Ordinary pages started with `k.new_slide()`** on `poster` and `blueprint` — get the page's field/sheet, and the deck still passes `check_visual_language` (Task 3 test).
4. **A deck with no pictures on Codex** — `codex_delivery_gate.py` holds a set with no native language exactly as `render_deck.py --gate-check` does (Task 9 test).
5. **An existing image-led deck rebuilt after this change** — byte-for-byte the same shapes as before (Task 3 test builds a collage sample and compares its slide XML with the pre-change build).

---

### Task 1: PowerPoint-safety lint (`ooxml_safety.py`)

**Files:**
- Create: `skills/slide-maker/scripts/ooxml_safety.py`
- Modify: `skills/slide-maker/scripts/lint_deck.py` (inside `lint()`, after the per-slide loop that ends with `warn_total += len(warns)`, before the duplicate-title block)
- Test: `skills/slide-maker/tests/test_ooxml_safety.py`
- Modify: `.github/workflows/ci.yml` (one step), `skills/slide-maker/references/file-inventory.md` (one entry)

**Interfaces:**
- Produces: `ooxml_safety.xml_findings(pptx_path) -> list[tuple[int, str]]` (slide number, message; every one is CRITICAL); `ooxml_safety.beyond_page(prs) -> list[tuple[int, str]]` (advisory); `ooxml_safety.SPPR_ORDER`, `ooxml_safety.RPR_ORDER`.

- [ ] **Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""ooxml_safety: values PowerPoint repairs that LibreOffice renders (found on the 2026-10-05 look-dev deck:
a negative outerShdw dir; and off-page geometry PowerPoint shows while editing)."""
import contextlib, io, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lxml import etree
from pptx.oxml.ns import qn
import deckkit as dk
import ooxml_safety as ox
import lint_deck

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
td = Path(tempfile.mkdtemp())

def shadow(shape, direction):
    sp = shape._element.spPr
    for e in sp.findall(qn("a:effectLst")):
        sp.remove(e)
    sp.append(etree.fromstring('<a:effectLst xmlns:a="%s"><a:outerShdw blurRad="91440" dist="36576" dir="%d" '
                               'algn="t" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="25000"/>'
                               '</a:srgbClr></a:outerShdw></a:effectLst>' % (A, direction)))

def deck(build):
    prs = dk.blank_deck(13.333, 7.5)
    s = dk.add_slide(prs)
    build(s)
    p = td / ("d%d.pptx" % len(list(td.iterdir())))
    prs.save(str(p))
    return p, prs

# 1. a negative shadow angle is CRITICAL, a normal one is clean
p, _ = deck(lambda s: shadow(dk.box(s, 1, 1, 2, 2, fill="FFFFFF"), -5400000))
f = ox.xml_findings(str(p))
check(f and f[0][0] == 1 and "dir" in f[0][1], "negative outerShdw dir is a finding: {}".format(f))
p, _ = deck(lambda s: shadow(dk.box(s, 1, 1, 2, 2, fill="FFFFFF"), 16200000))
check(ox.xml_findings(str(p)) == [], "an in-range shadow is clean")

# 2. spPr children out of schema order
def bad_order(s):
    b = dk.box(s, 1, 1, 2, 2, fill="FFFFFF")
    sp = b._element.spPr
    eff = sp.find(qn("a:effectLst"))
    if eff is None:
        eff = etree.SubElement(sp, qn("a:effectLst"))
    sp.remove(eff)
    sp.find(qn("a:prstGeom")).addnext(eff)            # effectLst before the fill: invalid
p, _ = deck(bad_order)
check(any("order" in m for _n, m in ox.xml_findings(str(p))), "spPr children out of order are a finding")

# 3. alpha out of range, duplicate shape ids
def bad_alpha(s):
    b = dk.box(s, 1, 1, 2, 2, fill="FFFFFF")
    clr = b._element.spPr.find(qn("a:solidFill"))[0]
    clr.append(clr.makeelement(qn("a:alpha"), {"val": "120000"}))
p, _ = deck(bad_alpha)
check(any("alpha" in m for _n, m in ox.xml_findings(str(p))), "alpha above 100000 is a finding")
def dup_ids(s):
    a = dk.box(s, 1, 1, 1, 1, fill="FFFFFF")
    b = dk.box(s, 3, 1, 1, 1, fill="FFFFFF")
    b._element.nvSpPr.cNvPr.set("id", a._element.nvSpPr.cNvPr.get("id"))
p, _ = deck(dup_ids)
check(any("id" in m for _n, m in ox.xml_findings(str(p))), "duplicate shape ids are a finding")

# 4. geometry past the page edge: advisory, quiet when declared a bleed
p, prs = deck(lambda s: dk.box(s, -0.5, 6.0, 4.0, 2.0, fill="333333"))
w = ox.beyond_page(prs)
check(w and w[0][0] == 1 and "BEYOND THE PAGE" in w[0][1], "a shape past the edge is reported: {}".format(w))
p, prs = deck(lambda s: dk.bleed_intent(dk.box(s, -0.5, 6.0, 4.0, 2.0, fill="333333"), "a full-bleed band"))
check(ox.beyond_page(prs) == [], "a declared bleed is quiet")
p, prs = deck(lambda s: dk.text(s, 1, 1, 4, 1, [[("inside", 18, dk.DEEP, False, False)]]))
check(ox.beyond_page(prs) == [] and ox.xml_findings(str(p)) == [], "a clean page is clean")

# 5. lint_deck runs it: the negative angle counts as a hard finding
p, _ = deck(lambda s: shadow(dk.box(s, 1, 1, 2, 2, fill="FFFFFF"), -5400000))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    n = lint_deck.lint(str(p))
check(n >= 1 and "OOXML" in buf.getvalue(), "lint_deck reports and counts it: n={} {}".format(n, buf.getvalue()[-300:]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd skills/slide-maker && python3 tests/test_ooxml_safety.py`
Expected: `ModuleNotFoundError: No module named 'ooxml_safety'`

- [ ] **Step 3: Write `ooxml_safety.py`**

```python
#!/usr/bin/env python3
"""ooxml_safety — values PowerPoint repairs (or deletes) that LibreOffice renders without a word.

🔴 MEASURED 2026-10-05. A look-dev deck rendered cleanly in LibreOffice and every lint passed; PowerPoint
opened it with "couldn't read some content — repaired and removed it". The cause was a soft shadow written
with `dir="-5400000"`: ST_PositiveFixedAngle is 0..21599999, LibreOffice reads the negative value, PowerPoint
drops the element. Every render-based check in this skill looks at LibreOffice, so this class is invisible to
all of them — it has to be read from the XML. The same deck also drew shapes past the slide edge, which
LibreOffice and the slideshow clip and PowerPoint's EDITING view shows: `beyond_page()` reports those.

    import ooxml_safety as ox
    ox.xml_findings("deck.pptx")      # [(slide, msg)] — CRITICAL, lint_deck counts them
    ox.beyond_page(prs)               # [(slide, msg)] — advisory, quiet for a declared bleed
"""
from __future__ import annotations

import re
import zipfile

from lxml import etree

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

# ECMA-376 sequences (only the children this skill writes are listed; anything else is not judged)
SPPR_ORDER = ("xfrm", "custGeom", "prstGeom", "noFill", "solidFill", "gradFill", "blipFill", "pattFill",
              "grpFill", "ln", "effectLst", "effectDag", "scene3d", "sp3d", "extLst")
RPR_ORDER = ("ln", "noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill", "effectLst",
             "effectDag", "highlight", "uLnTx", "uLn", "uFillTx", "uFill", "latin", "ea", "cs", "sym",
             "hlinkClick", "hlinkMouseOver", "rtl", "extLst")
_ANGLE = {"dir", "rot", "ang", "stAng", "swAng"}       # ST_PositiveFixedAngle / ST_FixedAngle in 60000ths
_POS_COORD = {"blurRad", "dist", "rad"}                 # ST_PositiveCoordinate
_PCT = {"pos"}                                          # gs pos: ST_PositiveFixedPercentage
_SLIDE = re.compile(r"ppt/slides/slide(\d+)\.xml$")


def _local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def _order_problem(el, seq):
    names = [_local(c.tag) for c in el if isinstance(c.tag, str)]
    idx = [seq.index(n) for n in names if n in seq]
    if idx != sorted(idx):
        return "{} children out of schema order: {}".format(_local(el.tag), names)
    return None


def xml_findings(pptx_path):
    """[(slide number, message)] for every value PowerPoint repairs. All CRITICAL."""
    out = []
    with zipfile.ZipFile(str(pptx_path)) as z:
        names = sorted((n for n in z.namelist() if _SLIDE.match(n)), key=lambda n: int(_SLIDE.match(n).group(1)))
        for name in names:
            n = int(_SLIDE.match(name).group(1))
            root = etree.fromstring(z.read(name))
            seen = set()

            def add(msg):
                if msg not in seen:
                    seen.add(msg)
                    out.append((n, "OOXML: " + msg + " — PowerPoint repairs or deletes it (LibreOffice does not)"))
            for el in root.iter():
                if not isinstance(el.tag, str):
                    continue
                tag = _local(el.tag)
                for att, val in el.attrib.items():
                    if not re.fullmatch(r"-?\d+", val or ""):
                        continue
                    v = int(val)
                    if att in _ANGLE and tag in ("outerShdw", "innerShdw", "lin") and not 0 <= v < 21600000:
                        add("{} {}={} outside 0..21599999".format(tag, att, v))
                    elif att in _POS_COORD and tag in ("outerShdw", "innerShdw", "glow", "softEdge") and v < 0:
                        add("{} {}={} is negative".format(tag, att, v))
                    elif att in _PCT and tag == "gs" and not 0 <= v <= 100000:
                        add("gradient stop pos={} outside 0..100000".format(v))
                    elif att == "val" and tag == "alpha" and not 0 <= v <= 100000:
                        add("alpha val={} outside 0..100000".format(v))
                    elif att == "spc" and tag in ("rPr", "defRPr", "endParaRPr") and not -400000 <= v <= 400000:
                        add("letter spacing spc={} outside -400000..400000".format(v))
                if tag == "spPr":
                    pr = _order_problem(el, SPPR_ORDER)
                    if pr:
                        add(pr)
                elif tag in ("rPr", "defRPr", "endParaRPr"):
                    pr = _order_problem(el, RPR_ORDER)
                    if pr:
                        add(pr)
            ids = [c.get("id") for c in root.iter(P + "cNvPr")]
            dup = sorted({i for i in ids if ids.count(i) > 1})
            if dup:
                add("duplicate shape id(s) {} on one slide".format(", ".join(dup)))
    return out


def beyond_page(prs):
    """[(slide number, message)] for undeclared non-text shapes that extend past the slide. Advisory: a
    deliberate bleed declares itself with deckkit.bleed_intent and is not reported."""
    import math
    import deckkit as dk
    W, H = prs.slide_width / 914400.0, prs.slide_height / 914400.0
    out = []
    for n, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if sh.width is None or sh.height is None:
                continue
            if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip():
                continue                                   # text past the edge is OFF_CANVAS's job
            name = str(getattr(sh, "name", "") or "")
            if name.startswith(dk.BLEED_TAG) or "+bleed" in name.split(":", 1)[0]:
                continue
            x, y, w, h = sh.left / 914400.0, sh.top / 914400.0, sh.width / 914400.0, sh.height / 914400.0
            rot = math.radians(float(getattr(sh, "rotation", 0.0) or 0.0))
            if rot:
                cx, cy = x + w / 2, y + h / 2
                hw = abs(w / 2 * math.cos(rot)) + abs(h / 2 * math.sin(rot))
                hh = abs(w / 2 * math.sin(rot)) + abs(h / 2 * math.cos(rot))
                x, y, w, h = cx - hw, cy - hh, 2 * hw, 2 * hh
            over = max(0.0, -x) + max(0.0, -y) + max(0.0, x + w - W) + max(0.0, y + h - H)
            if over > 0.02:
                out.append((n, "BEYOND THE PAGE: a {} reaches {:.2f}in past the slide edge — PowerPoint shows it "
                               "while editing; clip it to the page, or declare a deliberate bleed with "
                               "deckkit.bleed_intent(shape, '<why>')".format(str(sh.shape_type).split()[0].lower(), over)))
    return out
```

- [ ] **Step 4: Wire it into `lint_deck.lint()`**

Insert after the per-slide loop (the line `        warn_total += len(warns)` closes it) and before `    # duplicate slide titles (deck-level, advisory)`:

```python
    # PowerPoint safety (ooxml_safety): values PowerPoint repairs that LibreOffice renders, and geometry past
    # the slide edge, which PowerPoint shows while editing. Both read from the file, never from a render.
    try:
        import ooxml_safety as _ox
        for _sn, _m in _ox.xml_findings(path):
            print(f"  slide {_sn}: {_m}")
            j_findings.append({"slide": _sn, "text": _m, "severity": "error"})
            total += 1
        for _sn, _m in _ox.beyond_page(prs):
            print(f"  slide {_sn}: [warn] {_m}")
            j_warns.append({"slide": _sn, "text": _m, "severity": "warning"})
            warn_total += 1
    except ImportError:
        print("  [lint] ooxml_safety.py is missing — PowerPoint safety NOT CHECKED")
```

- [ ] **Step 5: Run the test — expect pass**

Run: `cd skills/slide-maker && python3 tests/test_ooxml_safety.py`
Expected: `N passed, 0 failed`

- [ ] **Step 6: Wire CI and the inventory**

Append a step after the "Uneven card heights" step in `.github/workflows/ci.yml`:

```yaml
      - name: PowerPoint safety (values PowerPoint repairs that LibreOffice renders)
        run: |
          set -o pipefail
          python tests/test_ooxml_safety.py | tee /tmp/ooxmlsafety.log
          grep -qE "(^[0-9]+ passed, 0 failed|\\] ok$)" /tmp/ooxmlsafety.log || {
            echo "::error::test_ooxml_safety did not run to completion"; exit 1; }
```

Add to `references/file-inventory.md`, next to the `lint_deck.py` entry:

```markdown
- `ooxml_safety.py` — **PowerPoint safety**, read from the saved file: values PowerPoint repairs or deletes that
  LibreOffice renders (angles outside 0..21599999, negative shadow distances, alphas and gradient stops outside
  0..100000, letter spacing out of range, `spPr`/`rPr` children out of schema order, duplicate shape ids) are
  CRITICAL; shapes past the slide edge are advisory (`BEYOND THE PAGE`, quiet for `bleed_intent`). `lint_deck`
  runs it, so both delivery gates hold it.
```

Run: `python3 scripts/check_inventory.py && python3 scripts/check_tests_wired.py` (from `skills/slide-maker`)
Expected: both report `0 problem(s)`.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/ooxml_safety.py skills/slide-maker/scripts/lint_deck.py skills/slide-maker/tests/test_ooxml_safety.py .github/workflows/ci.yml skills/slide-maker/references/file-inventory.md
git commit -m "ooxml_safety: values PowerPoint repairs that LibreOffice renders, read by lint_deck"
```

---

### Task 2: Native art primitives (`native_art.py`)

**Files:**
- Create: `skills/slide-maker/scripts/native_art.py`
- Test: `skills/slide-maker/tests/test_native_art.py`
- Modify: `.github/workflows/ci.yml`, `skills/slide-maker/references/file-inventory.md`

**Interfaces:**
- Consumes: `ornaments._shape(slide, x, y, w, h, path_xml, *, fill, alpha, line, line_w)`, `ornaments._smooth(points, closed=False)`, `ornaments._ring(points)`, `ornaments._pt(x, y)`; `deckkit.box/text/_connector/_as_rgb/decorative/overlap_intent`; `ooxml_safety.xml_findings/beyond_page` (Task 1).
- Produces (all coordinates in inches; colours as hex strings):
  - `page_size(slide) -> (W, H)`; `hexstr(c) -> str`; `angle(deg) -> int`; `clip_to_page(pts, W, H) -> list`
  - `poly(slide, pts, *, fill=None, alpha=None, line=None, line_w=0.75) -> shape | None`
  - `band(slide, top_pts, bottom_y, *, fill, alpha=None) -> shape`; `fade(shape, color, top, mid=None, stop=55) -> shape`
  - `soft_shadow(shape, *, blur=0.10, dist=0.04, alpha=0.25, color="2A1E10", direction=90.0) -> shape`
  - `disc(slide, cx, cy, d, fill, *, shadow=False) -> shape`; `seg(slide, x0, y0, x1, y1, color, *, w=0.75, dash=False, alpha=None) -> shape`
  - `no_autofit(textbox) -> textbox`; `vertical(textbox) -> textbox`
  - `solid_background(slide, color)`; `grid_background(slide, *, base, ink, step=0.25, major=4) -> str`
  - `INK_LAYERS: dict[str, tuple]`; `ink_ridges(slide, *, color, layers, seed=0, peak_span=(0.0, 0.62), keep_clear=()) -> list`
  - `seal(slide, x, y, size, chars, *, fill, ink, face) -> list`; `enso(slide, cx, cy, R, width, *, color, seed=3, gap=38.0, start=110.0, alpha=0.9) -> shape`
  - `hill_points(W, base, amp, seed, waves) -> list`; `paper_hill(slide, pts, bottom_y, *, fill, shadow=True) -> shape`
  - `paper_card(slide, x, y, w, h, *, fill="FFFFFF", r=0.22, rotation=0.0) -> shape`; `cloud(slide, cx, cy, w, *, fill="FFFFFF") -> shape`
  - `paper_sun(slide, cx, cy, diameters, colors) -> list`
  - `drawing_sheet(slide, *, ink, mute, accent, number, project, face) -> ((x, y, w, h) content, (x, y, w, h) block)`
  - `iso_stack(slide, cx, cy, size, gap, n, *, ink, accent=None, accent_layer=None, thick=0.18) -> list[list[(x, y)]]` (each layer's top rhombus corners, top layer first)
  - `dimension_line(slide, x, y0, y1, *, ink) -> list`; `balloon(slide, x, y, d, label, *, ink, accent, face, fill) -> list`
  - `clipped_block(slide, x, y, w, h, deg, *, fill) -> shape | None`

- [ ] **Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""native_art: every primitive draws ON the page, in range, deterministically, on any canvas."""
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk
import native_art as na
import ooxml_safety as ox

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

td = Path(tempfile.mkdtemp())
check(na.angle(-90) == 16200000 and na.angle(450) == 5400000 and na.angle(0) == 0, "angles normalise into range")
check(na.clip_to_page([(-1, -1), (2, -1), (2, 2), (-1, 2)], 1.0, 1.0) and
      all(0 <= x <= 1 and 0 <= y <= 1 for x, y in na.clip_to_page([(-1, -1), (2, -1), (2, 2), (-1, 2)], 1.0, 1.0)),
      "clip_to_page keeps a polygon inside the page")
check(na.clip_to_page([(5, 5), (6, 5), (6, 6)], 1.0, 1.0) == [], "a polygon wholly off the page clips to nothing")

def build(W, H, seed):
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    na.ink_ridges(s, color="1D1C1A", layers=na.INK_LAYERS["land" if W > H else "port"], seed=seed,
                  keep_clear=[(W * 0.78, 0.5, 1.0, H * 0.6)])
    na.seal(s, 1.0, 1.0, 0.6, "茶事", fill="B0362A", ink="F6EEE6", face="Songti SC")
    na.enso(s, W * 0.3, H * 0.5, min(W, H) * 0.3, 0.4, color="1D1C1A")
    na.paper_hill(s, na.hill_points(W, H * 0.7, H * 0.12, seed, 1.8), H + 1.0, fill="5AA38A")
    na.paper_card(s, 0.5, 0.5, 3.0, 2.0)
    na.cloud(s, W * 0.5, H * 0.2, 1.6)
    na.paper_sun(s, W * 0.7, H * 0.3, (2.0, 1.4), ("F7D38A", "F2B33D"))
    na.clipped_block(s, W - 2.0, H - 2.0, 4.0, 4.0, -9, fill="D7FF3B")
    tops = na.iso_stack(s, W * 0.5, H * 0.3, min(W, H) * 0.25, 0.8, 3, ink="1E3A5F", accent="E2552C", accent_layer=1)
    na.dimension_line(s, W * 0.9, H * 0.2, H * 0.7, ink="1E3A5F")
    na.balloon(s, 1.0, H - 1.5, 0.42, "2", ink="1E3A5F", accent="B8401A", face="Courier New", fill="F1EFE8")
    p = td / "art_{}x{}_{}.pptx".format(W, H, seed)
    prs.save(str(p))
    return p, prs, tops

for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333)):
    p, prs, tops = build(W, H, 3)
    check(len(tops) == 3 and all(len(t) == 4 for t in tops), "iso_stack returns one rhombus per layer ({}x{})".format(W, H))
    check(ox.xml_findings(str(p)) == [], "no PowerPoint-repaired value ({}x{}): {}".format(W, H, ox.xml_findings(str(p))[:2]))
    check(ox.beyond_page(prs) == [], "nothing past the page ({}x{}): {}".format(W, H, ox.beyond_page(prs)[:2]))
a = (td / "art_13.333x7.5_3.pptx").read_bytes()
p2, _, _ = build(13.333, 7.5, 3)
import zipfile
x1 = zipfile.ZipFile(str(td / "art_13.333x7.5_3.pptx")).read("ppt/slides/slide1.xml")
x2 = zipfile.ZipFile(str(p2)).read("ppt/slides/slide1.xml")
check(x1 == x2, "deterministic for a seed")
try:
    prs = dk.blank_deck(13.333, 7.5); na.seal(dk.add_slide(prs), 1, 1, 0.6, "三个字", fill="B0362A", ink="FFFFFF", face="Songti SC")
    check(False, "a three-character seal is refused")
except ValueError:
    check(True, "a three-character seal is refused")
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
na.grid_background(s, base="F1EFE8", ink="1E3A5F")
na.solid_background(dk.add_slide(prs), "1F3BFF")
p = td / "bg.pptx"; prs.save(str(p))
check(ox.xml_findings(str(p)) == [], "backgrounds are valid OOXML")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd skills/slide-maker && python3 tests/test_native_art.py`
Expected: `ModuleNotFoundError: No module named 'native_art'`

- [ ] **Step 3: Write `native_art.py`**

```python
#!/usr/bin/env python3
"""native_art — the drawn surfaces of the four NATIVE visual languages (ink, poster, cutpaper, blueprint):
native, editable shapes, deterministic for a seed, and ON THE PAGE by construction.

Two rules every function keeps, both found on the 2026-10-05 look-dev deck, which LibreOffice rendered and
PowerPoint did not open cleanly:
  · nothing is drawn past the slide edge. PowerPoint's editing view shows geometry beyond the slide, so a
    bleed is computed up to the edge (clip_to_page, band) — never left for the renderer to clip;
  · every angle written is in range. A negative outerShdw `dir` made PowerPoint repair the file (angle()).

    import native_art as na
    na.ink_ridges(s, color="1D1C1A", layers=na.INK_LAYERS["land"], keep_clear=[(9.6, 0.7, 1.2, 4.9)])
"""
from __future__ import annotations

import math
import random
import tempfile
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

import deckkit as dk
import ornaments as orn

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
U = 100000

# ridge layers, far to near: (crest base / H, peak height / H, top alpha, depth / H)
INK_LAYERS = {
    "land": ((0.57, 0.25, 0.34, 0.32), (0.67, 0.20, 0.46, 0.30), (0.77, 0.15, 0.62, 0.25), (0.89, 0.09, 0.80, 0.21)),
    "port": ((0.66, 0.12, 0.34, 0.20), (0.73, 0.10, 0.46, 0.18), (0.81, 0.08, 0.62, 0.15), (0.90, 0.05, 0.80, 0.11)),
    "faint": ((0.86, 0.10, 0.18, 0.16), (0.93, 0.06, 0.30, 0.10)),
}


def page_size(slide):
    pres = slide.part.package.presentation_part.presentation
    return pres.slide_width / 914400.0, pres.slide_height / 914400.0


def hexstr(c):
    if isinstance(c, str):
        return c.lstrip("#").upper()
    return "{:02X}{:02X}{:02X}".format(*c)


def _pct(v):
    return int(round(min(max(float(v), 0.0), 1.0) * 100000))


def angle(deg):
    """An OOXML angle (60000ths of a degree), always in 0..21599999 — PowerPoint repairs a negative one."""
    return int(round((float(deg) % 360.0) * 60000)) % 21600000


def clip_to_page(pts, W, H):
    """Sutherland-Hodgman: the polygon `pts` (inches) cut to the page rectangle [0, W] x [0, H]."""
    def clip(poly, inside, cross):
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))

    def at_y(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / (b[1] - a[1]), yv)

    pts = [tuple(p) for p in pts]
    for inside, cross in ((lambda p: p[0] >= 0.0, at_x(0.0)), (lambda p: p[0] <= W, at_x(W)),
                          (lambda p: p[1] >= 0.0, at_y(0.0)), (lambda p: p[1] <= H, at_y(H))):
        if not pts:
            break
        pts = clip(pts, inside, cross)
    return pts


def _custom(slide, x, y, w, h, path_xml, *, fill=None, alpha=None, line=None, line_w=1.0):
    return orn._shape(slide, x, y, w, h, path_xml, fill=fill, alpha=alpha, line=line, line_w=line_w)


def poly(slide, pts, *, fill=None, alpha=None, line=None, line_w=0.75):
    """A straight-edged polygon, clipped to the page; None when nothing of it is on the page."""
    W, H = page_size(slide)
    pts = clip_to_page(pts, W, H)
    if len(pts) < 3:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    w, h = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
    u = [((px - x0) / w * U, (py - y0) / h * U) for px, py in pts]
    path = '<a:path w="{u}" h="{u}"{f}>{d}</a:path>'.format(u=U, d=orn._ring(u),
                                                            f="" if fill is not None else ' fill="none"')
    return _custom(slide, x0, y0, w, h, path, fill=None if fill is None else hexstr(fill), alpha=alpha,
                   line=line, line_w=line_w)


def band(slide, top_pts, bottom_y, *, fill, alpha=None):
    """A band whose top edge is a smooth curve through `top_pts` and whose foot is flat — x clamped to the page,
    the foot to the page bottom, so a bleed reaches the edge and stops there."""
    W, H = page_size(slide)
    pts = [(min(max(px, 0.0), W), py) for px, py in top_pts]
    bottom_y = min(bottom_y, H)
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0 = max(0.0, min(min(p[1] for p in pts), bottom_y - 0.02))
    w, h = max(x1 - x0, 0.01), max(bottom_y - y0, 0.01)
    u = [((px - x0) / w * U, (max(py, y0) - y0) / h * U) for px, py in pts]
    d = "<a:moveTo>{}</a:moveTo>{}<a:lnTo>{}</a:lnTo><a:lnTo>{}</a:lnTo><a:close/>".format(
        orn._pt(*u[0]), orn._smooth(u), orn._pt(U, U), orn._pt(0, U))
    return _custom(slide, x0, y0, w, h, '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=U, d=d),
                   fill=hexstr(fill), alpha=alpha)


def fade(shape, color, top, mid=None, stop=55):
    """Swap a solid fill for a vertical transparency gradient: `top` alpha at the crest, mist at the foot."""
    sp = shape._element.spPr
    sf = sp.find(qn("a:solidFill"))
    if sf is None:
        raise ValueError("fade(): the shape has no solid fill to fade")
    mid = top * 0.35 if mid is None else mid
    g = etree.fromstring(
        '<a:gradFill xmlns:a="{a}" rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:srgbClr val="{c}"><a:alpha val="{t}"/></a:srgbClr></a:gs>'
        '<a:gs pos="{p}"><a:srgbClr val="{c}"><a:alpha val="{m}"/></a:srgbClr></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="{c}"><a:alpha val="0"/></a:srgbClr></a:gs></a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/></a:gradFill>'.format(
            a=A_NS, c=hexstr(color), t=_pct(top), m=_pct(mid), p=int(min(max(stop, 1), 99)) * 1000))
    sf.addprevious(g)
    sp.remove(sf)
    return shape


def soft_shadow(shape, *, blur=0.10, dist=0.04, alpha=0.25, color="2A1E10", direction=90.0):
    """A soft paper shadow (a real outerShdw), its angle normalised into range, placed in schema order."""
    sp = shape._element.spPr
    for e in sp.findall(qn("a:effectLst")):
        sp.remove(e)
    eff = etree.fromstring(
        '<a:effectLst xmlns:a="{a}"><a:outerShdw blurRad="{b}" dist="{d}" dir="{r}" algn="t" rotWithShape="0">'
        '<a:srgbClr val="{c}"><a:alpha val="{al}"/></a:srgbClr></a:outerShdw></a:effectLst>'.format(
            a=A_NS, b=int(abs(blur) * 914400), d=int(abs(dist) * 914400), r=angle(direction), c=hexstr(color),
            al=_pct(alpha)))
    ln = sp.find(qn("a:ln"))
    if ln is not None:
        ln.addnext(eff)
    else:
        sp.append(eff)
    return shape


def disc(slide, cx, cy, d, fill, *, shadow=False):
    b = dk.box(slide, cx - d / 2.0, cy - d / 2.0, d, d, fill=hexstr(fill))
    b._element.spPr.find(qn("a:prstGeom")).set("prst", "ellipse")
    return soft_shadow(b, blur=0.12, dist=0.05, alpha=0.24) if shadow else b


def seg(slide, x0, y0, x1, y1, color, *, w=0.75, dash=False, alpha=None):
    W, H = page_size(slide)
    cl = lambda v, hi: min(max(v, 0.0), hi)            # noqa: E731
    c = dk._connector(slide, cl(x0, W), cl(y0, H), cl(x1, W), cl(y1, H), dk._as_rgb(hexstr(color)), w=w, dash=dash)
    if alpha is not None:
        clr = c._element.spPr.find(qn("a:ln")).find(qn("a:solidFill"))[0]
        clr.append(clr.makeelement(qn("a:alpha"), {"val": str(_pct(alpha))}))
    return c


def no_autofit(tb):
    """A measured box keeps its size: PowerPoint re-runs spAutoFit on vertical text differently from LibreOffice."""
    bp = tb.text_frame._txBody.find(qn("a:bodyPr"))
    for e in list(bp):
        if e.tag in (qn("a:spAutoFit"), qn("a:normAutofit"), qn("a:noAutofit")):
            bp.remove(e)
    bp.insert(0, bp.makeelement(qn("a:noAutofit"), {}))
    return tb


def vertical(tb):
    """CJK set upright, top to bottom, columns right to left."""
    tb.text_frame._txBody.find(qn("a:bodyPr")).set("vert", "eaVert")
    return no_autofit(tb)


def _bg(slide, fill_xml):
    csld = slide._element.find(qn("p:cSld"))
    for old in csld.findall(qn("p:bg")):
        csld.remove(old)
    csld.insert(0, etree.fromstring('<p:bg xmlns:p="{p}" xmlns:a="{a}" xmlns:r="{r}"><p:bgPr>{f}<a:effectLst/>'
                                    '</p:bgPr></p:bg>'.format(p=P_NS, a=A_NS, r=R_NS, f=fill_xml)))


def solid_background(slide, color):
    _bg(slide, '<a:solidFill><a:srgbClr val="{}"/></a:solidFill>'.format(hexstr(color)))


def grid_background(slide, *, base, ink, step=0.25, major=4, dpi=150):
    """A drafting grid as the slide background — one picture per canvas and colour, cached, never a shape."""
    from PIL import Image, ImageDraw
    W, H = page_size(slide)
    path = Path(tempfile.gettempdir()) / "slide-maker-native-art" / "grid_{}_{}_{:.3f}x{:.3f}.png".format(
        hexstr(base), hexstr(ink), W, H)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pw, ph = int(W * dpi), int(H * dpi)
        b = tuple(int(hexstr(base)[i:i + 2], 16) for i in (0, 2, 4))
        k = tuple(int(hexstr(ink)[i:i + 2], 16) for i in (0, 2, 4))
        mix = lambda a: tuple(int(b[i] * (1 - a) + k[i] * a) for i in range(3))  # noqa: E731
        im = Image.new("RGB", (pw, ph), b)
        dr = ImageDraw.Draw(im)
        px = dpi * step
        for i in range(int(pw / px) + 1):
            dr.line([(int(i * px), 0), (int(i * px), ph)], fill=mix(0.13 if i % major == 0 else 0.055), width=1)
        for j in range(int(ph / px) + 1):
            dr.line([(0, int(j * px)), (pw, int(j * px))], fill=mix(0.13 if j % major == 0 else 0.055), width=1)
        im.save(str(path))
    _part, rid = slide.part.get_or_add_image_part(str(path))
    _bg(slide, '<a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{}"/><a:srcRect/><a:stretch><a:fillRect/>'
               '</a:stretch></a:blipFill>'.format(rid))
    return str(path)


def ink_ridges(slide, *, color, layers, seed=0, peak_span=(0.0, 0.62), keep_clear=()):
    """Ink-wash ridges, far to near, each fading from its crest into mist. Peaks rise only inside `peak_span`
    (fractions of W); over every `keep_clear` rect the crest stays below the rect's foot — text never sits on
    the wash. Declared decorative: the language's ground, like paper grain."""
    W, H = page_size(slide)
    out = []
    for i, (bf, af, top_alpha, df) in enumerate(layers):
        rnd = random.Random(seed * 31 + i)
        base, amp = bf * H, af * H
        lo, hi = peak_span[0] * W, peak_span[1] * W
        centers = [(rnd.uniform(lo, hi), rnd.uniform(0.45, 1.0) * amp, rnd.uniform(0.06, 0.16) * W) for _ in range(4)]
        pts = []
        for j in range(41):
            x = W * j / 40.0
            hgt = 0.12 * amp * (1 + math.sin(x / W * 12.0 + seed + i)) / 2.0
            for cx, a, sp in centers:
                hgt = max(hgt, a * math.exp(-((x - cx) / sp) ** 2 * 2.2) * (1 + 0.08 * math.sin(x * 9 + seed)))
            y = base - hgt
            for kx, ky, kw, kh in keep_clear:
                if kx - 0.25 <= x <= kx + kw + 0.25:
                    y = max(y, ky + kh + 0.15)
            pts.append((x, y))
        sh = band(slide, pts, base + df * H, fill=color)
        fade(sh, color, top_alpha)
        dk.decorative(sh, "an ink-wash ridge: the language's ground, like paper grain")
        out.append(sh)
    return out


def seal(slide, x, y, size, chars, *, fill, ink, face):
    """A carved seal carrying ONE or TWO characters of the caller's own text (never invented)."""
    chars = (chars or "").strip()
    if not 1 <= len(chars) <= 2:
        raise ValueError("seal(): one or two characters from the caller's own text, got {!r}".format(chars))
    rnd = random.Random(sum(map(ord, chars)))
    j = lambda: rnd.uniform(-0.035, 0.035) * size     # noqa: E731 — a carved stone's edge is never straight
    pts = [(x + j(), y + j()), (x + size / 2, y + j() * 0.6), (x + size + j(), y + j()),
           (x + size + j(), y + size / 2), (x + size + j(), y + size + j()), (x + size / 2, y + size + j() * 0.6),
           (x + j(), y + size + j()), (x + j() * 0.6, y + size / 2)]
    body = poly(slide, pts, fill=fill, alpha=0.94)
    pt = size * 72 * (0.40 if len(chars) == 2 else 0.60)
    tb = dk.text(slide, x, y, size, size, [[(chars, pt, dk._as_rgb(hexstr(ink)), True, False, face, face)]],
                 align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    (vertical if len(chars) == 2 else no_autofit)(tb)
    dk.overlap_intent(tb, "the seal's characters are carved into the seal")
    return [body, tb]


def enso(slide, cx, cy, R, width, *, color, seed=3, gap=38.0, start=110.0, alpha=0.9):
    """An open ensō brush circle: thick where the brush lands, dry and thin where it lifts."""
    rnd = random.Random(seed)
    n, sweep = 120, 360.0 - gap
    outer, inner = [], []
    for i in range(n + 1):
        t = i / float(n)
        a = math.radians(start + sweep * t)
        wob = 0.012 * R * math.sin(t * 23 + seed) + 0.01 * R * (rnd.random() - 0.5)
        w = width * (0.25 + 0.75 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6) * (1 - 0.55 * t ** 3)
        outer.append((cx + (R + wob) * math.cos(a), cy + (R + wob) * math.sin(a)))
        inner.append((cx + (R + wob - w) * math.cos(a), cy + (R + wob - w) * math.sin(a)))
    sh = poly(slide, outer + inner[::-1], fill=color, alpha=alpha)
    dk.decorative(sh, "an ensō brush circle around the figure; ornament")
    return sh


def hill_points(W, base, amp, seed, waves):
    ph = random.Random(seed).uniform(0.0, 6.28)
    return [(W * i / 16.0, base - amp * (0.55 + 0.45 * math.sin(ph + waves * 6.28318 * i / 16.0))) for i in range(17)]


def paper_hill(slide, pts, bottom_y, *, fill, shadow=True):
    sh = band(slide, pts, bottom_y, fill=fill)
    if shadow:
        soft_shadow(sh, blur=0.14, dist=0.05, alpha=0.22, direction=270.0)
    dk.decorative(sh, "a cut-paper hill: the language's ground")
    return sh


def paper_card(slide, x, y, w, h, *, fill="FFFFFF", r=0.22, rotation=0.0):
    c = dk.box(slide, x, y, w, h, fill=hexstr(fill), round=True, r=r)
    if rotation:
        c.rotation = float(rotation)
    return soft_shadow(c, blur=0.16, dist=0.06, alpha=0.24)


def cloud(slide, cx, cy, w, *, fill="FFFFFF"):
    pts = []
    for i in range(14):
        a = 6.28318 * i / 14
        r = 1 + 0.18 * math.sin(a * 3) + 0.08 * math.sin(a * 5)
        pts.append((cx + math.cos(a) * w / 2 * r, cy + math.sin(a) * w / 5.5 * r))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0, ww, hh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    u = [((px - x0) / ww * U, (py - y0) / hh * U) for px, py in pts]
    d = "<a:moveTo>{}</a:moveTo>{}<a:close/>".format(orn._pt(*u[0]), orn._smooth(u, closed=True))
    sh = _custom(slide, x0, y0, ww, hh, '<a:path w="{u}" h="{u}">{d}</a:path>'.format(u=U, d=d), fill=hexstr(fill))
    soft_shadow(sh, blur=0.08, dist=0.04, alpha=0.18)
    dk.decorative(sh, "a paper cloud: the cut-paper ground")
    return sh


def paper_sun(slide, cx, cy, diameters, colors):
    out = []
    for d, col in zip(diameters, colors):
        sh = disc(slide, cx, cy, d, col, shadow=True)
        dk.decorative(sh, "a layered paper sun")
        out.append(sh)
    return out


def drawing_sheet(slide, *, ink, mute, accent, number, project, face):
    """A drawing sheet's furniture: double border, zone marks, and a title block holding only the sheet number
    and the caller's own project words. Returns (content rect, title-block rect)."""
    W, H = page_size(slide)
    s = min(W, H) / 7.5
    m1, m2 = 0.32 * s, 0.42 * s
    rgb = lambda c: dk._as_rgb(hexstr(c))              # noqa: E731
    dk.box(slide, m1, m1, W - 2 * m1, H - 2 * m1, line=rgb(ink), line_w=1.0)
    dk.box(slide, m2, m2, W - 2 * m2, H - 2 * m2, line=rgb(ink), line_w=0.5)
    zpt = max(8.0, 8.0 * s)
    nx, ny = max(2, int(round(W / 2.2))), max(2, int(round(H / 1.9)))
    for i in range(nx):
        dk.text(slide, m2 + (W - 2 * m2) * (i + 0.5) / nx - 0.15, 0.03 * s, 0.3, m1 - 0.04 * s,
                [[(str(i + 1), zpt, rgb(mute), False, False, face)]], align=dk.PP_ALIGN.CENTER,
                anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    for j in range(min(ny, 8)):
        dk.text(slide, 0.02 * s, m2 + (H - 2 * m2) * (j + 0.5) / ny - 0.12, m1 - 0.04 * s, 0.24,
                [[("ABCDEFGH"[j], zpt, rgb(mute), False, False, face)]], align=dk.PP_ALIGN.CENTER,
                anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    bw, bh = min(3.9 * s, W * 0.36), 0.9 * s
    bx, by = W - m2 - 0.12 * s - bw, H - m2 - 0.12 * s - bh
    dk.box(slide, bx, by, bw, bh, line=rgb(ink), line_w=0.75)
    split = bx + bw * 0.66
    seg(slide, split, by, split, by + bh, ink, w=0.5)
    lab = max(8.0, 8.0 * s)
    if project:
        dk.text(slide, bx + 0.08 * s, by + 0.06 * s, split - bx - 0.14 * s, bh - 0.12 * s,
                [[("PROJECT", lab, rgb(mute), False, False, face)],
                 [(str(project), max(9.0, 10.0 * s), rgb(ink), True, False, face, face)]], space_after=0)
    dk.text(slide, split + 0.08 * s, by + 0.06 * s, bx + bw - split - 0.14 * s, bh - 0.12 * s,
            [[("SHEET", lab, rgb(mute), False, False, face)],
             [("{:02d}".format(number), max(14.0, 16.0 * s), rgb(accent), True, False, face)]], space_after=0)
    return (0.9 * s, 0.78 * s, W - 1.8 * s, H - 1.56 * s), (bx, by, bw, bh)


def _iso(cx, cy, a, b):
    return (cx + (a - b) * 0.866, cy + (a + b) * 0.5)


def iso_stack(slide, cx, cy, size, gap, n, *, ink, accent=None, accent_layer=None, thick=0.18):
    """`n` isometric layers (one per point of the page — never a generic diagram), top layer first; the layer at
    `accent_layer` is filled with `accent`. Returns each layer's top rhombus corners (top, right, bottom, left)."""
    tops = []
    for k_ in range(n):
        y = cy + k_ * gap
        p = [_iso(cx, y, 0, 0), _iso(cx, y, size, 0), _iso(cx, y, size, size), _iso(cx, y, 0, size)]
        if accent is not None and accent_layer == k_:
            poly(slide, p, fill=accent, alpha=0.9)
        poly(slide, p, line=dk._as_rgb(hexstr(ink)), line_w=1.0)
        poly(slide, [p[3], p[2], (p[2][0], p[2][1] + thick), (p[3][0], p[3][1] + thick)], line=dk._as_rgb(hexstr(ink)), line_w=1.0)
        poly(slide, [p[2], p[1], (p[1][0], p[1][1] + thick), (p[2][0], p[2][1] + thick)], line=dk._as_rgb(hexstr(ink)), line_w=1.0)
        tops.append(p)
    if n > 1:
        for corner in (0, 1, 3):
            x, y = tops[0][corner]
            seg(slide, x, y, x, tops[-1][corner][1], ink, w=0.5, dash=True, alpha=0.7)
    return tops


def dimension_line(slide, x, y0, y1, *, ink):
    out = [seg(slide, x, y0, x, y1, ink, w=0.6)]
    for y in (y0, y1):
        out.append(seg(slide, x - 0.09, y + 0.09, x + 0.09, y - 0.09, ink, w=0.9))
        out.append(seg(slide, x - 0.16, y, x + 0.16, y, ink, w=0.4))
    return out


def balloon(slide, x, y, d, label, *, ink, accent, face, fill):
    b = dk.box(slide, x, y, d, d, fill=hexstr(fill), line=dk._as_rgb(hexstr(ink)), line_w=0.9)
    b._element.spPr.find(qn("a:prstGeom")).set("prst", "ellipse")
    tb = dk.text(slide, x, y, d, d, [[(str(label), max(10.0, d * 72 * 0.40), dk._as_rgb(hexstr(accent)), True, False, face)]],
                 align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    no_autofit(tb)
    dk.overlap_intent(tb, "a numbered balloon: the number sits inside its circle")
    return [b, tb]


def clipped_block(slide, x, y, w, h, deg, *, fill):
    """A rotated colour block drawn as its polygon cut to the page (a rotated rectangle would hang off it)."""
    cx, cy, a = x + w / 2.0, y + h / 2.0, math.radians(deg)
    corners = [(cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))
               for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    sh = poly(slide, corners, fill=fill)
    if sh is not None:
        dk.decorative(sh, "a poster colour block: the language's ground")
    return sh
```

- [ ] **Step 4: Run the test — expect pass**

Run: `cd skills/slide-maker && python3 tests/test_native_art.py`
Expected: `N passed, 0 failed`

- [ ] **Step 5: Wire CI and inventory, commit**

CI step (after the PowerPoint-safety step): name `Native art (page-clipped, in-range, deterministic)`, running `python tests/test_native_art.py | tee /tmp/nativeart.log` with the same `grep -qE` completion guard as Task 1. Inventory entry next to `ornaments.py`:

```markdown
- `native_art.py` — the drawn surfaces of the native visual languages: ink ridges (fading into mist), seal, ensō,
  paper hills/cards/clouds/sun with real soft shadows, drafting grid and drawing sheet, iso stack, dimension
  line, numbered balloon, page-clipped colour block, solid/grid slide backgrounds. Native and editable,
  deterministic for a seed, never past the page, every angle in range.
```

```bash
git add skills/slide-maker/scripts/native_art.py skills/slide-maker/tests/test_native_art.py .github/workflows/ci.yml skills/slide-maker/references/file-inventory.md
git commit -m "native_art: page-clipped, in-range drawing primitives for the native visual languages"
```

---

### Task 3: Register the four languages in the kit; the native composer skeleton

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py` — `LANGS`, `VARIANTS`, `TYPE`, `PAGE_FIELDS`, `_flow` (colour key `mute`), `Kit.__init__`/`Kit.new_slide`, grounds/cards before the `for _n in LANGS: rs.register(...)` loop, `_page`, `_DISPLAY_NAMES`, `_RATIONALE`; new constants `NATIVE`, `IMAGE_LED`, `NATIVE_EXTRAS`
- Create: `skills/slide-maker/scripts/vl_native.py` (skeleton: helpers + dispatch; compositions arrive in Tasks 4–7)
- Modify: `skills/slide-maker/tests/test_visual_languages.py`, `tests/test_vl_page_fill.py`, `tests/test_vl_ground_variants.py` — loops over `vl.LANGS` that test IMAGE-LED behaviour become loops over `vl.IMAGE_LED`
- Test: `skills/slide-maker/tests/test_native_languages.py` (created here, extended in Tasks 4–8)

**Interfaces:**
- Consumes: `native_art` (Task 2).
- Produces:
  - `vl.NATIVE = ("ink", "poster", "cutpaper", "blueprint")`, `vl.IMAGE_LED = ("editorial", "soft", "collage", "storybook")`, `vl.NATIVE_EXTRAS = {"ink": ("seal",), "poster": ("highlight",), "cutpaper": ("icons",), "blueprint": ("project",)}`
  - `vl.PAGE_FIELDS["points"] == ("kicker", "title", "items")`; `Kit.points(slide, *, kicker=None, title=None, items=None, image=None, **extras)`
  - `Kit.project` (blueprint title-block words), `Kit.field` (poster: the current page's field dict)
  - `vl_native.register(lang, page)` decorator; `vl_native.compose(k, slide, page, fields, image) -> {"rects", "image", "free"}`; `vl_native.paint_ground(k, slide)`; `vl_native.GROUNDS: dict[lang, fn(k, slide)]`
  - `vl_native.ctx(k) -> (W, H, s, "land"|"port")`; `vl_native.points_of(items) -> [(head, line|None)]`; `vl_native.is_vertical(text) -> bool`
  - `vl_native.flow(k, slide, page, col, items, *, anchor="top", align="l", ink=None, accent=None, mute=None, start=None) -> (rects, draw)` — PLANS; `draw()` sets the text
  - `vl_native.vcol(k, slide, right, top, h_max, text, field, *, color=None, spacing=0.12, max_cols=2) -> ((x, y, w, h), size, draw)`
  - `vl_native.display(k, slide, rect, text, field, *, highlight=None, caps=True, ink=None, hl=None, hl_ink=None, align="l", anchor="t") -> ((x, y, w, h), size, draw)` — big type fitted by measurement

- [ ] **Step 1: Record the image-led baseline (Review Focus 5)**

Before editing anything:

```bash
cd skills/slide-maker && python3 - <<'EOF'
import sys, zipfile, hashlib, json
sys.path.insert(0, "scripts")
import visual_languages as vl
out = {}
for n in ("editorial", "soft", "collage", "storybook"):
    for g in vl.VARIANTS[n]:
        p = vl.build_sample(n, "/tmp/vl_baseline", ground=g)
        z = zipfile.ZipFile(str(p))
        out["%s-%s" % (n, g)] = [hashlib.sha256(z.read(x)).hexdigest() for x in sorted(z.namelist()) if x.startswith("ppt/slides/slide")]
json.dump(out, open("/tmp/vl_baseline/hashes.json", "w"), indent=1)
print(len(out), "baselines")
EOF
```
Expected: `8 baselines`.

- [ ] **Step 2: Write the failing test**

```python
#!/usr/bin/env python3
"""The four NATIVE visual languages: registered like the image-led four, their grounds' inks pass contrast,
pages compose on every canvas, and nothing they draw leaves the page or trips PowerPoint."""
from __future__ import annotations
import contextlib, io, sys, tempfile, zipfile, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk
import visual_languages as vl
import ooxml_safety as ox

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def cr(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

td = Path(tempfile.mkdtemp())
check(vl.NATIVE == ("ink", "poster", "cutpaper", "blueprint"), "the four native languages are named")
check(set(vl.NATIVE) | set(vl.IMAGE_LED) == set(vl.LANGS), "every language is native or image-led")
check(vl.PAGE_FIELDS.get("points") == ("kicker", "title", "items"), "the points page exists")
for n in vl.NATIVE:
    for g, V in vl.VARIANTS[n].items():
        p = V["palette"]
        check(cr(p["ink"], p["ground"]) >= 4.5, "{}/{} ink on ground".format(n, g))
        check(cr(p["mute"], p["ground"]) >= 4.5, "{}/{} mute on ground".format(n, g))
        for t in p["text_accents"]:
            check(cr(t, p["ground"]) >= 4.5, "{}/{} text accent {} on ground".format(n, g, t))
        on_panel = p.get("card_ink", p["ink"])
        check(cr(on_panel, p["panel"]) >= 4.5, "{}/{} ink on its panel".format(n, g))
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(n, dk.blank_deck(13.333, 7.5), ground=g)
        check(k.ground == g and k.P["ground"] == p["ground"] or n == "poster", "{}/{} use() sets the ground".format(n, g))
# points belongs to the native languages only
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("collage", dk.blank_deck(13.333, 7.5))
try:
    k.points(k.new_slide(), title="x", items=["a", "b"])
    check(False, "points() on an image-led language is refused")
except ValueError as e:
    check("native" in str(e), "points() on an image-led language names the native languages: {}".format(e))
# extras are per language
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("ink", dk.blank_deck(13.333, 7.5))
try:
    k.cover(k.new_slide(), title="x", highlight="x")
    check(False, "an extra that belongs to another language is refused")
except TypeError:
    check(True, "an extra that belongs to another language is refused")
# poster and blueprint ordinary pages carry their ground
for n in ("poster", "blueprint"):
    prs = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(n, prs)
    s = k.new_slide()
    has_bg = s._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cSld").find(
        "{http://schemas.openxmlformats.org/presentationml/2006/main}bg") is not None
    check(has_bg, "{}: an ordinary new_slide() page gets the language's ground".format(n))
# image-led samples are byte-identical to the pre-change build (Review Focus 5)
base = Path("/tmp/vl_baseline/hashes.json")
if base.exists():
    want = json.loads(base.read_text())
    for key, hashes in want.items():
        n, g = key.split("-", 1)
        p = vl.build_sample(n, str(td), ground=g)
        z = zipfile.ZipFile(str(p))
        got = [hashlib.sha256(z.read(x)).hexdigest() for x in sorted(z.namelist()) if x.startswith("ppt/slides/slide")]
        check(got == hashes, "{} is unchanged by the native languages".format(key))
else:
    print("  skip image-led baseline: no /tmp/vl_baseline/hashes.json (recorded locally in Step 1; not in CI)")
# a deck that never picks a native language loads nothing new (spec §6 performance)
import subprocess
probe = subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0, 'scripts'); import contextlib, io, deckkit as dk, visual_languages as vl\n"
    "with contextlib.redirect_stdout(io.StringIO()):\n"
    "    k = vl.use('collage', dk.blank_deck(13.333, 7.5)); k.new_slide()\n"
    "print(sorted(m for m in ('vl_native', 'native_art', 'ooxml_safety') if m in sys.modules))"],
    capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
check(probe.stdout.strip() == "[]", "an image-led deck imports no native module: {!r} {}".format(
    probe.stdout.strip(), probe.stderr[-200:]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

- [ ] **Step 3: Run it — expect failure**

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py`
Expected: `AttributeError: module 'visual_languages' has no attribute 'NATIVE'`

- [ ] **Step 4: Edit `visual_languages.py`**

(a) Append to `LANGS` (inside the dict, after `"storybook"`):

```python
    # ── NATIVE languages (P3): drawn, no pictures needed; compositions in vl_native.py ──
    "ink": {
        "palette": {"ground": "F1ECE1", "ink": "1D1C1A", "mute": "645C51", "panel": "E8E1D2",
                    "accents": ["B0362A"], "text_accents": ["A3322A"], "sun": "B0362A"},
        "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman"},
                  "mac": {"display": "Baskerville", "body": "Georgia", "numeral": "Times New Roman"}},
        "ea": {"display": "serif", "body": "serif"}, "grain": 4, "frames": ["feather"],
        "forbids": ("confetti",), "cover": "split-vertical", "skeleton": "rail"},
    "poster": {
        "palette": {"ground": "1F3BFF", "ink": "F3F0E8", "mute": "F3F0E8", "panel": "141414",
                    "accents": ["D7FF3B", "FF4B1F", "141414"], "text_accents": ["D7FF3B", "F3F0E8"]},
        "fonts": {"both": {"display": "Impact", "body": "Arial", "numeral": "Impact", "mono": "Courier New"},
                  "mac": {"display": "Impact", "body": "Helvetica Neue", "numeral": "Impact", "mono": "Courier New"}},
        "ea": {"display": "sans", "body": "sans"}, "ea_heavy": True, "grain": 0, "frames": ["rect"],
        "forbids": (), "cover": "full-bleed-type", "skeleton": "statement"},
    "cutpaper": {
        "palette": {"ground": "FBF2E3", "ink": "2A2733", "mute": "4A4656", "panel": "FFFFFF",
                    "accents": ["EE8A6B", "4E8FC7", "5B3F6E", "5AA38A"], "text_accents": ["A8442D", "2F6F62"],
                    "card_ink": "2A2733", "card_mute": "4A4656", "card_accent": "A8442D"},
        "fonts": {"both": {"display": "Trebuchet MS", "body": "Trebuchet MS", "numeral": "Trebuchet MS"},
                  "mac": {"display": "Avenir Next", "body": "Avenir Next", "numeral": "Avenir Next"}},
        "ea": {"display": "sans", "body": "sans"}, "grain": 3, "frames": ["rect"],
        "forbids": (), "cover": "low-left", "skeleton": "island"},
    "blueprint": {
        "palette": {"ground": "F1EFE8", "ink": "1E3A5F", "mute": "3E5674", "panel": "F1EFE8",
                    "accents": ["E2552C"], "text_accents": ["B8401A"]},
        "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman", "mono": "Courier New"},
                  "mac": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman", "mono": "Courier New"}},
        "ea": {"display": "serif", "body": "sans"}, "grain": 0, "frames": ["rect"],
        "forbids": ("confetti",), "cover": "low-left", "skeleton": "split"},
```

(b) Append to `VARIANTS`:

```python
    "ink": {
        "light": {"label": "xuan paper", "label_zh": "宣纸版", "grain": 4, "palette": LANGS["ink"]["palette"]},
        "night": {"label": "ink night", "label_zh": "墨夜版", "grain": 4,
                  "palette": {"ground": "1C1B19", "ink": "E9E2D2", "mute": "A99F8F", "panel": "262421",
                              "accents": ["B23A2C"], "text_accents": ["E07A63"], "sun": "E8DEC6"}}},
    "poster": {
        "light": {"label": "colour fields", "label_zh": "色场版", "grain": 0, "palette": LANGS["poster"]["palette"]},
        "paper": {"label": "paper", "label_zh": "白纸版", "grain": 0,
                  "palette": {"ground": "F3F0E8", "ink": "141414", "mute": "141414", "panel": "141414",
                              "accents": ["1F3BFF", "FF4B1F"], "text_accents": ["1F3BFF", "141414"]}}},
    "cutpaper": {
        "light": {"label": "day", "label_zh": "白天版", "grain": 3, "palette": LANGS["cutpaper"]["palette"]},
        "night": {"label": "paper night", "label_zh": "纸夜版", "grain": 3,
                  "palette": {"ground": "1D2742", "ink": "F2EEE4", "mute": "C6C9D6", "panel": "FFFFFF",
                              "accents": ["EE8A6B", "4E8FC7", "5B3F6E", "467E7A"], "text_accents": ["F2A285", "A8D5C4"],
                              "card_ink": "2A2733", "card_mute": "4A4656", "card_accent": "A8442D"}}},
    "blueprint": {
        "light": {"label": "vellum", "label_zh": "硫酸纸版", "grain": 0, "palette": LANGS["blueprint"]["palette"]},
        "cyanotype": {"label": "cyanotype", "label_zh": "晒图蓝版", "grain": 0,
                      "palette": {"ground": "123254", "ink": "E4ECF5", "mute": "B7C5D6", "panel": "123254",
                                  "accents": ["F27D4E"], "text_accents": ["F59A72"]}}},
```

(c) After `VARIANTS`, add:

```python
NATIVE = ("ink", "poster", "cutpaper", "blueprint")          # drawn, no pictures needed (vl_native.py)
IMAGE_LED = ("editorial", "soft", "collage", "storybook")    # built around the caller's pictures
# words only the CALLER can give — never invented by the kit; absent means nothing is drawn
NATIVE_EXTRAS = {"ink": ("seal",), "poster": ("highlight",), "cutpaper": ("icons",), "blueprint": ("project",)}
```

(d) Append to `TYPE` (fields + the points rows; `mute` is a new colour key, `mono` a new role):

```python
    "ink": {"kicker": (13, "body", False, "mute", False, 10), "title": (52, "display", False, "ink", False, 26),
            "subtitle": (19, "body", False, "mute", False, 12), "body": (17, "body", False, "ink", False, 11),
            "mark": (60, "display", False, "accent", False, 30), "quote": (44, "display", False, "ink", False, 22),
            "attribution": (15, "body", False, "mute", False, 10), "number": (230, "numeral", False, "ink", False, 72),
            "label": (34, "display", False, "ink", False, 16), "note": (16, "body", False, "mute", False, 10),
            "caption": (12, "body", False, "mute", False, 9), "line": (20, "body", False, "ink", False, 12),
            "item_head": (28, "display", False, "ink", False, 14), "item_line": (17, "body", False, "mute", False, 10)},
    "poster": {"kicker": (11, "mono", True, "ink", False, 9), "title": (150, "display", False, "ink", False, 44),
               "subtitle": (20, "body", True, "ink", False, 12), "body": (18, "body", False, "ink", False, 11),
               "mark": (300, "display", False, "accent", False, 120), "quote": (90, "display", False, "ink", False, 34),
               "attribution": (12, "mono", True, "accent", False, 10), "number": (380, "numeral", False, "ink", False, 110),
               "label": (70, "display", False, "ink", False, 26), "note": (19, "body", True, "ink", False, 12),
               "caption": (12, "body", False, "ink", False, 9), "line": (24, "body", True, "ink", False, 14),
               "item_head": (18, "body", True, "ink", False, 12), "item_line": (14, "body", False, "ink", False, 10)},
    "cutpaper": {"kicker": (14, "body", True, "accent", False, 10), "title": (60, "display", True, "ink", False, 28),
                 "subtitle": (20, "body", False, "mute", False, 12), "body": (18, "body", False, "ink", False, 11),
                 "mark": (90, "display", True, "accent", False, 40), "quote": (44, "display", True, "ink", False, 20),
                 "attribution": (13, "body", True, "accent", False, 10), "number": (200, "numeral", True, "ink", False, 64),
                 "label": (44, "display", True, "ink", False, 20), "note": (19, "body", False, "mute", False, 11),
                 "caption": (12, "body", False, "mute", False, 9), "line": (22, "body", False, "ink", False, 12),
                 "item_head": (28, "display", True, "ink", False, 14), "item_line": (17, "body", False, "mute", False, 10)},
    "blueprint": {"kicker": (11, "mono", True, "accent", False, 9), "title": (54, "display", False, "ink", False, 26),
                  "subtitle": (16, "display", False, "mute", True, 11), "body": (16, "body", False, "ink", False, 10),
                  "mark": (60, "display", False, "accent", False, 30), "quote": (44, "display", False, "ink", True, 20),
                  "attribution": (11, "mono", True, "mute", False, 9), "number": (330, "numeral", False, "ink", False, 100),
                  "label": (46, "display", False, "ink", False, 20), "note": (16, "display", False, "mute", True, 10),
                  "caption": (10, "mono", True, "mute", False, 8), "line": (20, "display", False, "ink", True, 12),
                  "item_head": (11, "mono", True, "ink", False, 9), "item_line": (15, "display", False, "mute", False, 10)},
```

(e) `PAGE_FIELDS`: add `"points": ("kicker", "title", "items"),`.

(f) In `_flow.draw()`, replace
`            color = k.color("text_accents") if ckey == "accent" else k.color("ink")`
with
`            color = (k.color("text_accents") if ckey == "accent" else k.color("mute") if ckey == "mute" else k.color("ink"))`

(g) `Kit.__init__`: after `self.ground = ground` add `self.project, self.field = None, None` and `self.P = dict(VARIANTS[name][ground]["palette"])` (a COPY — poster swaps it per page). `Kit.new_slide`: before `return s` add

```python
        if self.name in NATIVE:                 # poster's colour field, blueprint's drawing sheet
            import vl_native
            vl_native.paint_ground(self, s)
```

(h) Before the line `_card_editorial, _card_soft, _card_collage, _card_storybook = ...`, add grounds; extend that line and the registration loop picks them up because it iterates `LANGS`:

```python
def _ground_ink(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


def _ground_poster(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.55, 0.85, W - 1.1, H - 1.4)


def _ground_cutpaper(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.6, 0.6, W - 1.2, H - 1.2)


def _ground_blueprint(slide, role, index):
    W, H = rs._canvas(slide)
    s = min(W, H) / 7.5
    return (0.9 * s, 0.78 * s, W - 1.8 * s, H - 2.6 * s)      # above the title block
```

and after the `_card_editorial, ... = (...)` line:

```python
_card_ink, _card_poster, _card_cutpaper, _card_blueprint = (_card_for(n) for n in ("ink", "poster", "cutpaper", "blueprint"))
```

(i) `_page(page)`'s inner `fn`: replace the validation and the `out = _compose(...)` line with

```python
        extras = set(NATIVE_EXTRAS.get(self.name, ()))
        bad = set(fields) - set(PAGE_FIELDS[page]) - ({"line"} if page == "closing" else set()) - extras
        if bad:
            raise TypeError("{}.{}(): unknown field(s) {} — this page takes {}{}".format(
                self.name, page, sorted(bad), list(PAGE_FIELDS[page]) + ["image"],
                " and {}".format(sorted(extras)) if extras else ""))
        if self.name in NATIVE:
            import vl_native
            out = vl_native.compose(self, slide, page, fields, image)
        elif page == "points":
            raise ValueError("{}.points(): the points page belongs to the native languages ({}) — on {} build the "
                             "list on an ordinary page: s = k.new_slide(); x, y, w, h = rs.ground(s, {!r}, "
                             "role='content', index=n); then rs.card / dk.text".format(
                                 self.name, ", ".join(NATIVE), self.name, self.name))
        else:
            out = _compose(self, slide, page, fields, image)
```

(j) `_DISPLAY_NAMES` and `_RATIONALE`: add

```python
_DISPLAY_NAMES.update({"ink": "Ink wash", "poster": "Type poster", "cutpaper": "Cut paper", "blueprint": "Blueprint sheet"})
_RATIONALE.update({"ink": "drawn, no pictures: misty ink ridges, vertical CJK, a carved seal, an ensō around the figure",
                   "poster": "drawn, no pictures: the headline is the picture, one saturated field per page",
                   "cutpaper": "drawn, no pictures: a layered paper diorama with soft paper shadows",
                   "blueprint": "drawn, no pictures: a drawing sheet with grid, title block, dimensions and leaders"})
```

- [ ] **Step 5: Create `vl_native.py`**

```python
#!/usr/bin/env python3
"""vl_native — page compositions of the NATIVE visual languages (ink, poster, cutpaper, blueprint).

Imported by visual_languages only for those languages; the image-led four never load it. Each page PLANS its text
first (measured: the kit's _flow for horizontal text, vcol for vertical CJK, display for poster-scale type —
shrinking to each field's floor and refusing with VLTextOverflow past it), then draws its native art with that
text kept clear, then sets the text — so art never sits over words and z-order is art below type.
Nothing here invents a word: seal/highlight/project/icons come from the caller or are not drawn.
"""
from __future__ import annotations

import copy

import deckkit as dk
import native_art as na
import visual_languages as vl

COMPOSERS = {}     # language -> {page: fn(k, slide, fields, image) -> rects}
GROUNDS = {}       # language -> fn(k, slide): what every page of the language carries (new_slide)


def register(lang, page):
    def deco(fn):
        COMPOSERS.setdefault(lang, {})[page] = fn
        return fn
    return deco


def ctx(k):
    W, H = vl._canvas(k)
    return W, H, min(W, H) / 7.5, ("land" if W >= H * 1.2 else "port")


def text_of(fields, name):
    v = fields.get(name)
    return str(v).strip() if v is not None and str(v).strip() else None


def points_of(items):
    """2-4 points: strings, (head, line) pairs or {"head", "line"} dicts -> [(head, line or None)]."""
    if not isinstance(items, (list, tuple)) or not 2 <= len(items) <= 4:
        raise ValueError("points(): items= takes 2 to 4 points, got {!r}".format(items))
    out = []
    for it in items:
        if isinstance(it, dict):
            head, line = it.get("head"), it.get("line")
        elif isinstance(it, (list, tuple)):
            head, line = (list(it) + [None, None])[:2]
        else:
            head, line = it, None
        head = str(head or "").strip()
        if not head:
            raise ValueError("points(): every point needs its words — an empty one in {!r}".format(items))
        out.append((head, str(line).strip() if line is not None and str(line).strip() else None))
    return out


def _cjk(ch):
    o = ord(ch)
    return 0x3000 <= o <= 0x30FF or 0x3400 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or ch in "·—…"


def is_vertical(text):
    """Vertical only for CJK (Han/kana) with no Latin letters or digits — those would lie on their side."""
    t = "".join(ch for ch in (text or "") if not ch.isspace())
    if not t or any(ch.isascii() and ch.isalnum() for ch in t):
        return False
    return dk.script_of(t) in ("han", "kana") and all(_cjk(ch) for ch in t)


def _kit_on(k, ink=None, accent=None, mute=None):
    if not (ink or accent or mute):
        return k
    kk = copy.copy(k)
    kk.P = dict(k.P)
    if ink:
        kk.P["ink"] = ink
    if mute:
        kk.P["mute"] = mute
    if accent:
        kk.P["text_accents"] = [accent] + list(k.P["text_accents"][1:])
    return kk


def flow(k, slide, page, col, items, *, anchor="top", align="l", ink=None, accent=None, mute=None, start=None):
    """PLAN horizontal text with the kit's measured flow; returns (rects, draw). ink/accent/mute override the
    colours for text that sits on a card or panel instead of the ground."""
    if not items:
        return {}, (lambda: None)
    kk = _kit_on(k, ink, accent, mute)
    return vl._flow(kk, slide, page, col, items, anchor=anchor, align=align, start=start)


def _color(k, ckey):
    return k.color("text_accents") if ckey == "accent" else k.color("mute") if ckey == "mute" else k.color("ink")


def vcol(k, slide, right, top, h_max, text, field, *, color=None, spacing=0.12, max_cols=2):
    """PLAN CJK `text` set vertically, right edge at `right`: starts at the field's size, shrinks toward its floor,
    refuses past `max_cols` columns at the floor. Returns ((x, y, w, h), size, draw)."""
    base, role, bold, ckey, _italic, floor = vl.TYPE[k.name][field]
    s = ctx(k)[2]
    sz, fl = base * s, max(9.0, floor * s)
    n = len(text)
    while True:
        adv = sz * (1.0 + spacing) / 72.0
        per = max(1, int((h_max - 0.08) // adv))
        cols = -(-n // per)
        if cols <= max_cols or sz <= fl + 1e-6:
            break
        sz = max(fl, sz * 0.92)
    if cols > max_cols:
        raise vl.VLTextOverflow("{}: the {} {!r} needs {} vertical columns even at {:.0f}pt — shorten it".format(
            k.name, field, text[:24], cols, sz))
    w = cols * sz * 1.28 / 72.0 + 0.06
    h = min(h_max, -(-n // cols) * adv + 0.12)
    x = right - w
    col = color or _color(k, ckey)

    def draw():
        tb = dk.text(slide, x, top, w, h, [k.runs(text, sz, col, bold, role)], space_after=0)
        for p in tb.text_frame.paragraphs:
            for r in p.runs:
                r._r.get_or_add_rPr().set("spc", str(int(round(sz * spacing * 100))))
        na.vertical(tb)
    return (x, top, w, h), sz, draw


def display(k, slide, rect, text, field, *, highlight=None, caps=True, ink=None, hl=None, hl_ink=None,
            align="l", anchor="t"):
    """PLAN poster-scale type in `rect`: measured, shrinking to the field's floor, refused past it; Latin set in
    capitals; `highlight` (words of the caller's own text) set on a highlighter. Returns (rect, size, draw)."""
    base, role, bold, ckey, _italic, floor = vl.TYPE[k.name][field]
    s = ctx(k)[2]
    t = text.upper() if caps and not dk._has_cjk(text) else text
    if highlight is not None:
        hi = str(highlight).strip()
        if not hi or hi.upper() not in t.upper():
            raise ValueError("{}: highlight= must be words of the {} itself, got {!r}".format(k.name, field, highlight))
    x, y, w, h = rect
    face = k.ea_face(role, t) or k.face(role)
    sz, fl = base * s, max(9.0, floor * s)
    while True:
        need = dk.measure_text([(t, bool(bold))], w, sz, font=face, line_spacing=0.86)
        if need <= h or sz <= fl + 1e-6:
            break
        sz = max(fl, sz * 0.93)
    if need > h + 1e-6:
        raise vl.VLTextOverflow("{}: the {} {!r} does not fit {:.2f}x{:.2f}in even at {:.0f}pt — shorten it".format(
            k.name, field, text[:24], w, h, sz))
    ty = y if anchor == "t" else (y + h - need if anchor == "b" else y + (h - need) / 2.0)
    col = dk.RGBColor.from_string(ink) if ink else _color(k, ckey)

    def draw():
        runs = []
        if highlight:
            i = t.upper().index(str(highlight).strip().upper())
            j = i + len(str(highlight).strip())
            for part, marked in ((t[:i], False), (t[i:j], True), (t[j:], False)):
                if not part:
                    continue
                if marked:
                    runs += [dk.mark(r, hl) for r in k.runs(part, sz, dk.RGBColor.from_string(hl_ink), bold, role)]
                else:
                    runs += k.runs(part, sz, col, bold, role)
        else:
            runs = k.runs(t, sz, col, bold, role)
        al = {"l": dk.PP_ALIGN.LEFT, "c": dk.PP_ALIGN.CENTER, "r": dk.PP_ALIGN.RIGHT}[align]
        dk.text(slide, x, ty, w, need, [runs], align=al, space_after=0, line_spacing=0.86)
    return (x, ty, w, need), sz, draw


def place_image(k, slide, image, rect, page, treat="frame"):
    """The caller's picture in `rect` with the kit's own placement (feather for ink, a frame for the others)."""
    return vl._place_image(k, slide, image, rect, vl.L_((0, 0, 1, 1), treat, None), page)


def compose(k, slide, page, fields, image):
    fns = COMPOSERS.get(k.name, {})
    if page not in fns:
        raise NotImplementedError("{}.{}(): no composition is registered for this page".format(k.name, page))
    if page == "image_text" and image is None:
        raise ValueError("{}.image_text(): image= is required — for text alone use section(), quote() or points()"
                         .format(k.name))
    if not any(text_of(fields, f) for f in vl.PAGE_FIELDS[page] if f != "items") and not fields.get("items") \
            and image is None:
        raise ValueError("{}.{}(): nothing to place — pass the words".format(k.name, page))
    n0 = len(slide.shapes)
    rects = fns[page](k, slide, fields, image) or {}
    for sh in list(slide.shapes)[n0:]:
        dk._compose_tag(sh, vl=k.name)
    return {"rects": rects, "image": None, "free": None}


def paint_ground(k, slide):
    fn = GROUNDS.get(k.name)
    if fn:
        n0 = len(slide.shapes)
        fn(k, slide)
        for sh in list(slide.shapes)[n0:]:
            dk._compose_tag(sh, vl=k.name)
```

- [ ] **Step 6: Narrow the image-led tests**

In `tests/test_vl_page_fill.py` replace `for name in vl.LANGS:` with `for name in vl.IMAGE_LED:`. In `tests/test_visual_languages.py`, replace `vl.LANGS` with `vl.IMAGE_LED` in the loops at the lines that compose image pages (`for name in vl.LANGS:` before `for cname, (W, H) in CANV.items():`, the bundled-sample loop `for name in vl.LANGS:` under `# ── Task 10`, and `for n_ in vl.LANGS: check(vl.direction(n_)...)`) — the native languages get the same checks in `test_native_languages.py` (Task 8 restores the sample/direction loops to `vl.LANGS` once their samples exist). Run `grep -n "vl.LANGS" tests/test_vl_ground_variants.py` and narrow any loop there that composes image pages the same way.

- [ ] **Step 7: Run the tests — expect pass**

Run: `cd skills/slide-maker && for t in test_native_languages test_visual_languages test_vl_page_fill test_vl_ground_variants test_a11y_title; do python3 tests/$t.py | tail -1; done`
Expected: every line ends `0 failed` or `] ok`.

- [ ] **Step 8: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native.py skills/slide-maker/tests/test_native_languages.py skills/slide-maker/tests/test_visual_languages.py skills/slide-maker/tests/test_vl_page_fill.py skills/slide-maker/tests/test_vl_ground_variants.py
git commit -m "visual languages: register ink, poster, cutpaper and blueprint; the points page; vl_native skeleton"
```

---

### Task 4: `ink` compositions

**Files:**
- Modify: `skills/slide-maker/scripts/vl_native.py` (append the ink section)
- Modify: `skills/slide-maker/tests/test_native_languages.py` (append the shared page-matrix runner + ink cases)

**Interfaces:**
- Consumes: Task 3 helpers (`register`, `ctx`, `text_of`, `points_of`, `is_vertical`, `flow`, `vcol`, `place_image`); `native_art` (`ink_ridges`, `INK_LAYERS`, `seal`, `enso`, `disc`, `seg`).
- Produces: `COMPOSERS["ink"]` for all seven pages.

- [ ] **Step 1: Append the page-matrix runner and the ink cases to the test**

Insert before the final summary lines of `tests/test_native_languages.py`:

```python
# ── the page matrix: every page × canvas × copy, then lint, PowerPoint safety and the page edge ──
import re
CANVASES = {"16:9": (13.333, 7.5), "4:3": (10.0, 7.5), "portrait": (7.5, 13.333)}
COPY = {
    "en": dict(kicker="A guide for the room", title="Bring it broken, take it home working",
               subtitle="Once a month, on the corner", number="3", label="evenings a month", note="Short enough to fit around work.",
               quote="The visitor holds the screwdriver; the volunteer only guides.", attribution="How every repair begins",
               body="Screwdrivers, a soldering iron and thread, shared on every bench.", line="Bring a neighbour.",
               items=[("Share the tools", "One bench, many hands"), ("Open the door", None), ("Keep it local", "Walk, don't drive")]),
    "zh": dict(kicker="茶事", title="一盏茶的时间", subtitle="慢下来，看见日常", number="3", label="泡，滋味最浓",
               note="头泡醒茶，三泡正好", quote="茶有两种姿态，浮与沉", attribution="茶室题记", body="器净，心先静。",
               line="下次再见", items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")]),
    "ja": dict(kicker="茶の時間", title="一服のお茶", subtitle="ゆっくり、日常を見る", number="3", label="煎目がいちばん",
               note="一煎目で目覚め、三煎目で整う", quote="茶には浮くと沈むがある", attribution="茶室の記", body="器を清め、心を静める。",
               line="またお会いしましょう", items=[("器を清める", None), ("湯を沸かす", "蟹の目のように"), ("茶を注ぐ", None)]),
    "ko": dict(kicker="차 이야기", title="차 한 잔의 시간", subtitle="천천히, 일상을 보다", number="3", label="번째가 가장 진하다",
               note="첫 잔은 깨우고 셋째 잔은 맞춘다", quote="차에는 뜨는 것과 가라앉는 것이 있다", attribution="다실의 기록",
               body="그릇을 씻고 마음을 고른다.", line="다음에 또 만나요", items=[("그릇 씻기", None), ("물 끓이기", None)]),
}
EXTRA = {"ink": {"seal": "茶事"}, "poster": {"highlight": None}, "cutpaper": {}, "blueprint": {"project": None}}


def build_matrix(name, ground, cname, lang):
    W, H = CANVASES[cname]
    T = COPY[lang]
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(name, prs, ground=ground)
    ex = {k_: v for k_, v in EXTRA[name].items() if v}
    if name == "ink" and lang not in ("zh", "ja"):
        ex = {}                                   # a Chinese seal on Latin or Hangul copy is not a test of the layout
    if name == "poster":
        ex = {"highlight": T["title"].split()[0]} if lang == "en" else {}
    pages = [("cover", dict(kicker=T["kicker"], title=T["title"], subtitle=T["subtitle"], **ex)),
             ("section", dict(number="02", kicker=T["kicker"], title=T["title"])),
             ("points", dict(kicker=T["kicker"], title=T["title"], items=T["items"])),
             ("quote", dict(quote=T["quote"], attribution=T["attribution"])),
             ("data", dict(number=T["number"], label=T["label"], note=T["note"])),
             ("closing", dict(title=T["title"], line=T["line"]))]
    for page, fields in pages:
        if name == "ink" and page in ("cover", "points", "quote") and "seal" in ex:
            fields.setdefault("seal", ex["seal"])
        getattr(k, page)(k.new_slide(), **fields)
    p = td / "m_{}_{}_{}_{}.pptx".format(name, ground, cname, lang)
    prs.save(str(p))
    return p, prs


def assert_matrix(name):
    for ground in vl.VARIANTS[name]:
        for cname in CANVASES:
            for lang in COPY:
                tag = "{}/{}/{}/{}".format(name, ground, cname, lang)
                try:
                    p, prs = build_matrix(name, ground, cname, lang)
                except vl.VLTextOverflow as e:
                    check(False, "{}: ordinary copy refused: {}".format(tag, e)); continue
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
                check(not crit, "{}: no critical layout fault: {}".format(tag, crit[:2]))
                check(ox.xml_findings(str(p)) == [], "{}: PowerPoint-safe: {}".format(tag, ox.xml_findings(str(p))[:2]))
                check(ox.beyond_page(prs) == [], "{}: nothing past the page: {}".format(tag, ox.beyond_page(prs)[:2]))
                xml = "".join(zipfile.ZipFile(str(p)).read(n).decode("utf-8") for n in zipfile.ZipFile(str(p)).namelist()
                              if re.match(r"ppt/slides/slide\d+\.xml$", n))
                if name == "ink" and lang in ("en", "ko"):
                    check('vert="eaVert"' not in xml, "{}: no vertical setting for {} copy".format(tag, lang))


# ── ink ──
assert_matrix("ink")
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("ink", dk.blank_deck(13.333, 7.5))
s = k.new_slide()
k.cover(s, title="一盏茶的时间", subtitle="慢下来，看见日常")
check(not any(getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() in ("茶事",) for sh in s.shapes),
      "ink: no seal is drawn when seal= is not given")
s = k.new_slide()
k.cover(s, title="Bring it broken")
check(not any('vert="eaVert"' in sh._element.xml for sh in s.shapes if getattr(sh, "has_text_frame", False)),
      "ink: a Latin title is set horizontally")
try:
    k.cover(k.new_slide(), title="一盏茶的时间", seal="三个字")
    check(False, "ink: a three-character seal is refused")
except ValueError:
    check(True, "ink: a three-character seal is refused")
try:
    k.cover(k.new_slide(), title="此" * 60)
    check(False, "ink: an impossible vertical title is refused")
except vl.VLTextOverflow:
    check(True, "ink: an impossible vertical title is refused")
for bad_items in (["一"], ["一", "二", "三", "四", "五"], ["一", ""]):
    try:
        k.points(k.new_slide(), title="三道工序", items=bad_items)
        check(False, "ink: points with {} refused".format(bad_items))
    except ValueError:
        check(True, "ink: points with {} refused".format(bad_items))
```

- [ ] **Step 2: Run — expect failure**

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py 2>&1 | tail -3`
Expected: `NotImplementedError: ink.cover(): no composition is registered for this page`

- [ ] **Step 3: Append the ink compositions to `vl_native.py`**

```python
# ═══════════════════════════════════ ink 水墨 ═══════════════════════════════════
import math as _math
import re as _re

_NUM_ZH = "一二三四"


def _ink_seal(k, slide, fields, x, y, size):
    chars = text_of(fields, "seal")
    if not chars:
        return
    W, H, _s, _o = ctx(k)
    x = min(max(x, 0.12), W - size - 0.12)
    y = min(max(y, 0.12), H - size - 0.15)
    na.seal(slide, x, y, size, chars, fill=k.P["accents"][0], ink="F6EEE6",
            face=k.ea_face("display", chars) or k.face("display"))


def _ink_sun(k, slide, cx, cy, d):
    dk.decorative(na.disc(slide, cx, cy, d, k.P["sun"]), "the ink language's sun (a moon on the night ground)")


def _ink_hairline(k, slide, x, y0, y1, alpha=0.45):
    return lambda: na.seg(slide, x, y0, x, y1, k.P["ink"], w=0.5, alpha=alpha)


def _run_all(draws):
    for d in draws:
        d()


@register("ink", "cover")
def _ink_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    title, kicker, sub = text_of(f, "title"), text_of(f, "kicker"), text_of(f, "subtitle")
    rects, draws, clear = {}, [], []
    if kicker:
        r, d = flow(k, slide, "cover", (0.07 * W, 0.06 * H, 0.45 * W, 0.08 * H), [("kicker", kicker)])
        rects.update(r); draws.append(d); clear.extend(r.values())
    if title and is_vertical(title) and (sub is None or is_vertical(sub)):
        r1, _z, d1 = vcol(k, slide, W * (0.90 if o == "land" else 0.92), 0.09 * H,
                          H * (0.62 if o == "land" else 0.46), title, "title")
        rects["title"] = r1; draws.append(d1); clear.append(r1)
        if sub:
            r2, _z2, d2 = vcol(k, slide, r1[0] - 0.36 * s, 0.12 * H, r1[3] * 0.85, sub, "subtitle")
            rects["subtitle"] = r2; draws.append(d2); clear.append(r2)
            draws.append(_ink_hairline(k, slide, r1[0] - 0.18 * s, 0.12 * H, max(r2[1] + r2[3], 0.12 * H + 0.5)))
        seal_at = (r1[0] + r1[2] / 2.0, r1[1] + r1[3] + 0.2 * s)
    else:
        col = (0.50 * W, 0.16 * H, 0.42 * W, 0.40 * H) if o == "land" else (0.08 * W, 0.12 * H, 0.84 * W, 0.34 * H)
        items = [(x_, t) for x_, t in (("title", title), ("subtitle", sub)) if t]
        r, d = flow(k, slide, "cover", col, items, anchor="top")
        rects.update(r); draws.append(d); clear.extend(r.values())
        low = max((v[1] + v[3] for v in r.values()), default=col[1])
        seal_at = (col[0] + 0.3 * s, low + 0.3 * s)
    _ink_sun(k, slide, (0.20 if o == "land" else 0.22) * W, (0.30 if o == "land" else 0.58) * H, 0.95 * s)
    na.ink_ridges(slide, color=k.P["ink"], layers=na.INK_LAYERS[o], seed=1,
                  peak_span=(0.0, 0.62) if o == "land" else (0.0, 1.0), keep_clear=clear)
    _run_all(draws)
    z = 0.62 * s
    _ink_seal(k, slide, f, seal_at[0] - z / 2.0, seal_at[1], z)
    return rects


@register("ink", "section")
def _ink_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    num, kicker, title = text_of(f, "number"), text_of(f, "kicker"), text_of(f, "title")
    rects, draws, clear = {}, [], []
    left = (0.10 * W, 0.16 * H, 0.38 * W, 0.56 * H) if o == "land" else (0.08 * W, 0.08 * H, 0.84 * W, 0.30 * H)
    items = [(x_, t) for x_, t in (("kicker", kicker), ("number", num)) if t]
    r, d = flow(k, slide, "section", left, items, anchor="top", ink=k.P["text_accents"][0], start={"number": 150 * s})
    rects.update(r); draws.append(d); clear.extend(r.values())
    if title:
        if is_vertical(title):
            r1, _z, d1 = vcol(k, slide, W * (0.86 if o == "land" else 0.90), (0.14 if o == "land" else 0.42) * H,
                              H * (0.60 if o == "land" else 0.42), title, "title")
        else:
            col = (0.52 * W, 0.20 * H, 0.40 * W, 0.50 * H) if o == "land" else (0.08 * W, 0.42 * H, 0.84 * W, 0.34 * H)
            rr, d1 = flow(k, slide, "section", col, [("title", title)], anchor="top")
            r1 = rr.get("title", col)
        rects["title"] = r1; draws.append(d1); clear.append(r1)
    na.ink_ridges(slide, color=k.P["ink"], layers=na.INK_LAYERS["faint"], seed=2, peak_span=(0.0, 1.0), keep_clear=clear)
    _run_all(draws)
    if rects.get("title"):
        rt, z = rects["title"], 0.5 * s
        _ink_seal(k, slide, f, rt[0] + rt[2] / 2.0 - z / 2.0, rt[1] + rt[3] + 0.18 * s, z)
    return rects


@register("ink", "image_text")
def _ink_image_text(k, slide, f, image):
    W, H, s, o = ctx(k)
    if o == "land":
        img, col = (0.04 * W, 0.08 * H, 0.52 * W, 0.84 * H), (0.62 * W, 0.16 * H, 0.32 * W, 0.68 * H)
    else:
        img, col = (0.05 * W, 0.04 * H, 0.90 * W, 0.46 * H), (0.08 * W, 0.53 * H, 0.84 * W, 0.40 * H)
    items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title", "body", "caption") if text_of(f, x_)]
    r, d = flow(k, slide, "image_text", col, items, anchor="middle" if o == "land" else "top")
    place_image(k, slide, image, img, "image_text", treat="feather")
    d()
    if r:
        low = max(v[1] + v[3] for v in r.values())
        z = 0.45 * s
        _ink_seal(k, slide, f, col[0], low + 0.2 * s, z)
    return r


@register("ink", "quote")
def _ink_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    q, attr = text_of(f, "quote"), text_of(f, "attribution")
    rects, draws, clear = {}, [], []
    if q and is_vertical(q) and (attr is None or is_vertical(attr)) and o == "land":
        parts = [p for p in _re.split(r"(?<=[，、；])", q) if p]
        cols = [parts[0], "".join(parts[1:])] if len(parts) > 1 else [q]
        right, top = 0.80 * W, 0.11 * H
        for i, c in enumerate(cols):
            r1, _z, d1 = vcol(k, slide, right, top + i * 0.14 * H, 0.76 * H - i * 0.14 * H, c, "quote")
            rects["quote%d" % i] = r1; draws.append(d1); clear.append(r1)
            right = r1[0] - 0.40 * s
        if attr:
            r2, _z2, d2 = vcol(k, slide, right, 0.48 * H, 0.32 * H, attr, "attribution")
            rects["attribution"] = r2; draws.append(d2); clear.append(r2)
        seal_at = (right - 0.1 * s, 0.82 * H)
    else:
        col = (0.14 * W, 0.22 * H, 0.62 * W, 0.50 * H) if o == "land" else (0.08 * W, 0.16 * H, 0.84 * W, 0.46 * H)
        items = [(x_, t) for x_, t in (("quote", q), ("attribution", attr)) if t]
        r, d = flow(k, slide, "quote", col, items, anchor="middle")
        rects.update(r); draws.append(d); clear.extend(r.values())
        low = max((v[1] + v[3] for v in r.values()), default=col[1])
        seal_at = (col[0] + 0.2 * s, low + 0.25 * s)
    _ink_sun(k, slide, 0.21 * W, (0.22 if o == "land" else 0.10) * H, 0.62 * s)
    na.ink_ridges(slide, color=k.P["ink"], layers=na.INK_LAYERS["faint"], seed=3,
                  peak_span=(0.0, 0.45), keep_clear=clear)
    _run_all(draws)
    _ink_seal(k, slide, f, seal_at[0] - 0.24 * s, seal_at[1], 0.48 * s)
    return rects


@register("ink", "data")
def _ink_data(k, slide, f, image):
    W, H, s, o = ctx(k)
    num, label, note = text_of(f, "number"), text_of(f, "label"), text_of(f, "note")
    if o == "land":
        cx, cy, R = 0.27 * W, 0.50 * H, 0.33 * H
    else:
        cx, cy, R = 0.50 * W, 0.28 * H, 0.32 * W
    rects, draws, clear = {}, [], [(cx - R, cy - R, 2 * R, 2 * R)]
    if num:
        inner = (cx - R * 0.70, cy - R * 0.70, R * 1.40, R * 1.40)
        r, d = flow(k, slide, "data", inner, [("number", num)], anchor="middle", align="c")
        rects.update(r); draws.append(d)
    if o == "land" and label and is_vertical(label) and (note is None or is_vertical(note)):
        x0 = cx + R + 0.9 * s
        r1, _z, d1 = vcol(k, slide, x0 + 1.2 * s, 0.18 * H, 0.60 * H, label, "label")
        rects["label"] = r1; draws.append(d1); clear.append(r1)
        if note:
            r2, _z2, d2 = vcol(k, slide, r1[0] - 0.42 * s, 0.20 * H, 0.52 * H, note, "note")
            rects["note"] = r2; draws.append(d2); clear.append(r2)
            draws.append(_ink_hairline(k, slide, r1[0] - 0.21 * s, 0.20 * H, 0.20 * H + max(r1[3], r2[3]), 0.4))
        seal_at = (r1[0] + r1[2] / 2.0, r1[1] + r1[3] + 0.2 * s)
    else:
        hcol = ((cx + R + 0.6 * s, 0.22 * H, 0.92 * W - (cx + R + 0.6 * s), 0.56 * H) if o == "land"
                else (0.08 * W, cy + R + 0.4 * s, 0.84 * W, 0.88 * H - (cy + R + 0.4 * s)))
        items = [(x_, t) for x_, t in (("label", label), ("note", note)) if t]
        r, d = flow(k, slide, "data", hcol, items, anchor="middle" if o == "land" else "top")
        rects.update(r); draws.append(d); clear.extend(r.values())
        low = max((v[1] + v[3] for v in r.values()), default=hcol[1])
        seal_at = (hcol[0] + 0.3 * s, low + 0.25 * s)
    na.enso(slide, cx, cy, R, R * 0.17, color=k.P["ink"], seed=5)
    na.ink_ridges(slide, color=k.P["ink"], layers=na.INK_LAYERS["faint"], seed=4, peak_span=(0.4, 1.0), keep_clear=clear)
    _run_all(draws)
    _ink_seal(k, slide, f, seal_at[0] - 0.22 * s, seal_at[1], 0.45 * s)
    return rects


@register("ink", "closing")
def _ink_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    title, line = text_of(f, "title"), text_of(f, "line")
    rects, draws, clear = {}, [], []
    if title and is_vertical(title) and (line is None or is_vertical(line)):
        r1, _z, d1 = vcol(k, slide, W * (0.62 if o == "land" else 0.70), 0.10 * H, H * (0.56 if o == "land" else 0.44),
                          title, "title")
        rects["title"] = r1; draws.append(d1); clear.append(r1)
        if line:
            r2, _z2, d2 = vcol(k, slide, r1[0] - 0.4 * s, 0.14 * H, r1[3] * 0.8, line, "line")
            rects["line"] = r2; draws.append(d2); clear.append(r2)
        seal_at = (r1[0] + r1[2] / 2.0, r1[1] + r1[3] + 0.2 * s)
    else:
        col = (0.12 * W, 0.18 * H, 0.76 * W, 0.36 * H) if o == "land" else (0.08 * W, 0.12 * H, 0.84 * W, 0.34 * H)
        items = [(x_, t) for x_, t in (("title", title), ("line", line)) if t]
        r, d = flow(k, slide, "closing", col, items, anchor="top", align="c")
        rects.update(r); draws.append(d); clear.extend(r.values())
        low = max((v[1] + v[3] for v in r.values()), default=col[1])
        seal_at = (W / 2.0, low + 0.25 * s)
    _ink_sun(k, slide, (0.80 if o == "land" else 0.75) * W, (0.20 if o == "land" else 0.52) * H, 1.1 * s)
    na.ink_ridges(slide, color=k.P["ink"], layers=na.INK_LAYERS[o], seed=7, peak_span=(0.2, 1.0), keep_clear=clear)
    _run_all(draws)
    _ink_seal(k, slide, f, seal_at[0] - 0.25 * s, seal_at[1], 0.5 * s)
    return rects


@register("ink", "points")
def _ink_points(k, slide, f, image):
    W, H, s, o = ctx(k)
    title, kicker = text_of(f, "title"), text_of(f, "kicker")
    pts = points_of(f.get("items"))
    vertical_ok = (o == "land" and all(is_vertical(h) and (l is None or is_vertical(l)) for h, l in pts)
                   and (title is None or is_vertical(title)))
    rects, draws, clear = {}, [], []
    if vertical_ok:                                    # columns read right to left, as a book is
        right = 0.93 * W
        if title:
            r0, _z, d0 = vcol(k, slide, right, 0.10 * H, 0.60 * H, title, "title")
            rects["title"] = r0; draws.append(d0); clear.append(r0)
            right = r0[0] - 0.55 * s
        n = len(pts)
        step = min(2.35 * s, (right - 0.10 * W) / n)
        for i, (head, line) in enumerate(pts):
            cr_ = right - i * step
            nr, nd = flow(k, slide, "points", (cr_ - step * 0.75, 0.10 * H, step * 0.6, 0.09 * H), [("mark", _NUM_ZH[i])],
                          align="c", start={"mark": 30 * s})
            rh, _z1, dh = vcol(k, slide, cr_ - step * 0.12, 0.23 * H, 0.42 * H, head, "item_head")
            draws += [nd, dh]; clear += list(nr.values()) + [rh]
            if line:
                rl, _z2, dl = vcol(k, slide, rh[0] - 0.18 * s, 0.25 * H, 0.50 * H, line, "item_line")
                draws.append(dl); clear.append(rl)
            if i < n - 1:
                draws.append(_ink_hairline(k, slide, cr_ - step * 0.96, 0.12 * H, 0.76 * H, 0.3))
        if title:
            draws.append(_ink_hairline(k, slide, rects["title"][0] - 0.28 * s, 0.12 * H, 0.76 * H, 0.45))
        seal_at = ((rects["title"][0] + rects["title"][2] / 2.0) if title else right,
                   (rects["title"][1] + rects["title"][3] + 0.2 * s) if title else 0.82 * H)
    else:
        top = 0.10 * H
        head_items = [(x_, t) for x_, t in (("kicker", kicker), ("title", title)) if t]
        r, d = flow(k, slide, "points", (0.08 * W, top, 0.84 * W, 0.20 * H), head_items, anchor="top")
        rects.update(r); draws.append(d); clear.extend(r.values())
        y0 = max((v[1] + v[3] for v in r.values()), default=top) + 0.35 * s
        row_h = (0.86 * H - y0) / len(pts)
        cjk_num = title is not None and is_vertical(title)
        for i, (head, line) in enumerate(pts):
            y = y0 + i * row_h
            nr, nd = flow(k, slide, "points", (0.08 * W, y, 0.9 * s, row_h), [("mark", _NUM_ZH[i] if cjk_num else str(i + 1))],
                          start={"mark": 30 * s})
            tr, td_ = flow(k, slide, "points", (0.08 * W + 1.0 * s, y, 0.76 * W, row_h - 0.12 * s),
                           [(x_, t) for x_, t in (("item_head", head), ("item_line", line)) if t], anchor="top")
            draws += [nd, td_]; clear += list(nr.values()) + list(tr.values())
            if i < len(pts) - 1:
                yy = y + row_h - 0.06 * s
                draws.append(lambda yy=yy: na.seg(slide, 0.08 * W, yy, 0.92 * W, yy, k.P["ink"], w=0.5, alpha=0.25))
        seal_at = (0.86 * W, 0.12 * H)
    na.ink_ridges(slide, color=k.P["ink"], layers=na.INK_LAYERS["faint"], seed=6, peak_span=(0.0, 1.0), keep_clear=clear)
    _run_all(draws)
    _ink_seal(k, slide, f, seal_at[0] - 0.25 * s, seal_at[1], 0.5 * s)
    return rects
```

- [ ] **Step 4: Run — expect pass; render and LOOK**

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py 2>&1 | tail -3`
Expected: `N passed, 0 failed` (poster/cutpaper/blueprint matrices are added in Tasks 5–7).
Then render one deck per canvas and open the PNGs side by side with the look-dev sheet `~/Desktop/slide-maker 新设计语言 样张/sheets/ink.jpg`; any page that reads worse than the look-dev (art over words, stranded word, cramped seal) is fixed now, with a ruling in the ledger:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "skills/slide-maker/tests"); sys.argv = ["x"]
EOF
python3 -c "
import sys; sys.path.insert(0,'skills/slide-maker/scripts')
import contextlib, io, deckkit as dk, visual_languages as vl
for W,H,tag in ((13.333,7.5,'land'),(7.5,13.333,'port')):
    prs = dk.blank_deck(W,H)
    with contextlib.redirect_stdout(io.StringIO()): k = vl.use('ink', prs)
    k.cover(k.new_slide(), kicker='茶事 · 卷一', title='一盏茶的时间', subtitle='慢下来，看见日常', seal='茶事')
    k.points(k.new_slide(), title='三道工序', items=[('洗盏','器净，心先静'),('候汤','水沸，如蟹眼'),('分茶','浅斟，留七分')], seal='序')
    k.quote(k.new_slide(), quote='茶有两种姿态，浮与沉', attribution='茶室题记', seal='记')
    k.data(k.new_slide(), number='3', label='泡，滋味最浓', note='头泡醒茶，三泡正好')
    prs.save('/tmp/ink_%s.pptx' % tag)
"
python3 skills/slide-maker/scripts/render_deck.py /tmp/ink_land.pptx /tmp/ink_land_r && python3 skills/slide-maker/scripts/render_deck.py /tmp/ink_port.pptx /tmp/ink_port_r
```

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/vl_native.py skills/slide-maker/tests/test_native_languages.py
git commit -m "ink: seven pages — misty ridges, vertical CJK, seal, ensō; horizontal for Latin and Hangul"
```

---

### Task 5: `poster` compositions

**Files:**
- Modify: `skills/slide-maker/scripts/vl_native.py` (append the poster section), `skills/slide-maker/tests/test_native_languages.py`

**Interfaces:**
- Consumes: Task 3 helpers (`display`, `flow`, `place_image`, `register`, `GROUNDS`); `native_art.clipped_block`, `native_art.solid_background`.
- Produces: `vl_native.POSTER_FIELDS: dict[ground, list[dict]]` (keys `bg ink accent panel panel_ink panel_accent hl hl_ink block`); `GROUNDS["poster"]`; `COMPOSERS["poster"]` (seven pages).

- [ ] **Step 1: Append the poster cases to the test**

```python
# ── poster ──
for g, fields in vl_native_fields().items():
    for i, fl in enumerate(fields):
        for a, b, what in ((fl["ink"], fl["bg"], "ink"), (fl["accent"], fl["bg"], "accent"),
                           (fl["panel_ink"], fl["panel"], "panel ink"), (fl["panel_accent"], fl["panel"], "panel accent"),
                           (fl["hl_ink"], fl["hl"], "highlight ink")):
            check(cr(a, b) >= 4.5, "poster/{} field {} {} {} on {}: {:.2f}".format(g, i, what, a, b, cr(a, b)))
assert_matrix("poster")
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("poster", prs)
bgs = []
for _ in range(5):
    s = k.new_slide()
    bgs.append(k.field["bg"])
check(bgs[0] != bgs[1] and bgs[4] == bgs[0], "poster: each page takes the next colour field, cycling")
try:
    k.cover(k.new_slide(), title="Make the room smaller", highlight="garden")
    check(False, "poster: a highlight that is not in the title is refused")
except ValueError:
    check(True, "poster: a highlight that is not in the title is refused")
s = k.new_slide()
k.cover(s, title="Make the room smaller", highlight="room")
check(any("a:highlight" in sh._element.xml for sh in s.shapes if getattr(sh, "has_text_frame", False)),
      "poster: the highlighted word sits on a highlighter")
```

and add near the top of the file (after the imports):

```python
def vl_native_fields():
    import vl_native
    return vl_native.POSTER_FIELDS
```

- [ ] **Step 2: Run — expect failure**

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py 2>&1 | tail -3`
Expected: `AttributeError: module 'vl_native' has no attribute 'POSTER_FIELDS'`

- [ ] **Step 3: Append the poster compositions to `vl_native.py`**

```python
# ═══════════════════════════════════ poster 海报大字 ═══════════════════════════════════
# One saturated field per page, in turn. Every text colour is chosen against ITS field (tested >= 4.5:1).
POSTER_FIELDS = {
    "light": [
        dict(bg="1F3BFF", ink="F3F0E8", accent="D7FF3B", panel="141414", panel_ink="F3F0E8", panel_accent="D7FF3B",
             hl="D7FF3B", hl_ink="141414", block=("D7FF3B", "141414")),
        dict(bg="D7FF3B", ink="141414", accent="1F3BFF", panel="141414", panel_ink="F3F0E8", panel_accent="D7FF3B",
             hl="141414", hl_ink="D7FF3B", block=("1F3BFF", "141414")),
        dict(bg="141414", ink="F3F0E8", accent="D7FF3B", panel="D7FF3B", panel_ink="141414", panel_accent="141414",
             hl="D7FF3B", hl_ink="141414", block=("D7FF3B", "FF4B1F")),
        dict(bg="FF4B1F", ink="141414", accent="141414", panel="141414", panel_ink="F3F0E8", panel_accent="FF4B1F",
             hl="141414", hl_ink="FF4B1F", block=("141414", "F3F0E8"))],
    "paper": [
        dict(bg="F3F0E8", ink="141414", accent="1F3BFF", panel="141414", panel_ink="F3F0E8", panel_accent="F3F0E8",
             hl="1F3BFF", hl_ink="F3F0E8", block=("1F3BFF", "141414")),
        dict(bg="F3F0E8", ink="141414", accent="1F3BFF", panel="1F3BFF", panel_ink="F3F0E8", panel_accent="F3F0E8",
             hl="141414", hl_ink="F3F0E8", block=("141414", "1F3BFF")),
        dict(bg="141414", ink="F3F0E8", accent="9AA8FF", panel="F3F0E8", panel_ink="141414", panel_accent="1F3BFF",
             hl="1F3BFF", hl_ink="F3F0E8", block=("1F3BFF", "F3F0E8")),
        dict(bg="1F3BFF", ink="F3F0E8", accent="F3F0E8", panel="F3F0E8", panel_ink="141414", panel_accent="1F3BFF",
             hl="F3F0E8", hl_ink="1F3BFF", block=("F3F0E8", "141414"))],
}


def _poster_ground(k, slide):
    fields = POSTER_FIELDS[k.ground]
    fld = fields[(len(k.prs.slides) - 1) % len(fields)]
    k.field = fld
    k.P = dict(k.P, ground=fld["bg"], ink=fld["ink"], mute=fld["ink"], panel=fld["panel"],
               text_accents=[fld["accent"], fld["ink"]])
    na.solid_background(slide, fld["bg"])
    dk.set_ground(fld["bg"])


GROUNDS["poster"] = _poster_ground


def _poster_meta(k, slide, kicker):
    """The fine print: the caller's kicker left, the page number right — a poster's credit line."""
    W, H, s, _o = ctx(k)
    fld = k.field
    sz = max(9.0, 11.0 * s)
    col = dk.RGBColor.from_string(fld["ink"])
    if kicker:
        t = kicker if dk._has_cjk(kicker) else kicker.upper()
        dk.text(slide, 0.04 * W, 0.045 * H, 0.62 * W, 0.4 * s, [k.runs(t, sz, col, True, "mono")], space_after=0)
    dk.text(slide, 0.76 * W, 0.045 * H, 0.20 * W, 0.4 * s, [k.runs("{:02d}".format(len(k.prs.slides)), sz, col, True, "mono")],
            align=dk.PP_ALIGN.RIGHT, space_after=0)


def _blocks(k, slide, blocks):
    for (bx, by, bw, bh, deg), fill in zip(blocks, k.field["block"]):
        na.clipped_block(slide, bx, by, bw, bh, deg, fill=fill)


@register("poster", "cover")
def _poster_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    fld = k.field
    title, kicker, sub, hl = text_of(f, "title"), text_of(f, "kicker"), text_of(f, "subtitle"), text_of(f, "highlight")
    if o == "land":
        trect = (0.035 * W, 0.11 * H, 0.56 * W, 0.84 * H)
        blocks = ((0.63 * W, 0.45 * H, 0.37 * W, 0.37 * W, -9.0), (0.79 * W, 0.66 * H, 0.26 * W, 0.39 * H, -9.0))
    else:
        trect = (0.06 * W, 0.08 * H, 0.88 * W, 0.56 * H)
        blocks = ((0.46 * W, 0.74 * H, 0.60 * W, 0.40 * W, -9.0), (0.70 * W, 0.86 * H, 0.40 * W, 0.20 * H, -9.0))
    rects, draws = {}, []
    if sub:
        srect = (trect[0], trect[1] + trect[3] - 0.9 * s, trect[2], 0.9 * s)
        r, d = flow(k, slide, "cover", srect, [("subtitle", sub)], anchor="bottom")
        rects.update(r); draws.append(d)
        trect = (trect[0], trect[1], trect[2], trect[3] - 1.0 * s)
    if title:
        r1, _z, d1 = display(k, slide, trect, title, "title", highlight=hl, hl=fld["hl"], hl_ink=fld["hl_ink"])
        rects["title"] = r1; draws.append(d1)
    _blocks(k, slide, blocks)
    _poster_meta(k, slide, kicker)
    _run_all(draws)
    return rects


@register("poster", "section")
def _poster_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    fld = k.field
    num, kicker, title, hl = text_of(f, "number"), text_of(f, "kicker"), text_of(f, "title"), text_of(f, "highlight")
    nrect = (0.04 * W, 0.12 * H, 0.44 * W, 0.80 * H) if o == "land" else (0.06 * W, 0.08 * H, 0.88 * W, 0.40 * H)
    trect = (0.52 * W, 0.26 * H, 0.44 * W, 0.56 * H) if o == "land" else (0.06 * W, 0.52 * H, 0.88 * W, 0.36 * H)
    rects, draws = {}, []
    if num:
        r, _z, d = display(k, slide, nrect, num, "number", caps=False, ink=fld["accent"], anchor="b")
        rects["number"] = r; draws.append(d)
    if title:
        r, _z, d = display(k, slide, trect, title, "label", highlight=hl, hl=fld["hl"], hl_ink=fld["hl_ink"])
        rects["title"] = r; draws.append(d)
    _poster_meta(k, slide, kicker)
    _run_all(draws)
    return rects


@register("poster", "image_text")
def _poster_image_text(k, slide, f, image):
    W, H, s, o = ctx(k)
    img = (0.52 * W, 0.12 * H, 0.44 * W, 0.76 * H) if o == "land" else (0.06 * W, 0.08 * H, 0.88 * W, 0.42 * H)
    col = (0.05 * W, 0.14 * H, 0.42 * W, 0.72 * H) if o == "land" else (0.06 * W, 0.54 * H, 0.88 * W, 0.38 * H)
    items = [(x_, text_of(f, x_)) for x_ in ("title", "body", "caption") if text_of(f, x_)]
    r, d = flow(k, slide, "image_text", col, items, anchor="middle" if o == "land" else "top")
    place_image(k, slide, image, img, "image_text")
    _poster_meta(k, slide, text_of(f, "kicker"))
    d()
    return r


@register("poster", "quote")
def _poster_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    fld = k.field
    q, attr, hl = text_of(f, "quote"), text_of(f, "attribution"), text_of(f, "highlight")
    rects, draws = {}, []
    mrect = (0.03 * W, 0.08 * H, 0.18 * W, 0.40 * H) if o == "land" else (0.06 * W, 0.06 * H, 0.30 * W, 0.18 * H)
    qrect = (0.20 * W, 0.20 * H, 0.74 * W, 0.56 * H) if o == "land" else (0.06 * W, 0.26 * H, 0.88 * W, 0.52 * H)
    r, _z, d = display(k, slide, mrect, "“", "mark", caps=False, ink=fld["accent"])
    draws.append(d)
    if q:
        r1, _z, d1 = display(k, slide, qrect, q, "quote", highlight=hl, hl=fld["hl"], hl_ink=fld["hl_ink"])
        rects["quote"] = r1; draws.append(d1)
        if attr:
            ar, ad = flow(k, slide, "quote", (qrect[0], r1[1] + r1[3] + 0.25 * s, qrect[2], 0.6 * s),
                          [("attribution", attr)], accent=fld["accent"])
            rects.update(ar); draws.append(ad)
    _poster_meta(k, slide, None)
    _run_all(draws)
    return rects


@register("poster", "data")
def _poster_data(k, slide, f, image):
    W, H, s, o = ctx(k)
    num, label, note = text_of(f, "number"), text_of(f, "label"), text_of(f, "note")
    nrect = (0.02 * W, 0.08 * H, 0.52 * W, 0.86 * H) if o == "land" else (0.05 * W, 0.08 * H, 0.90 * W, 0.42 * H)
    lrect = (0.56 * W, 0.24 * H, 0.40 * W, 0.34 * H) if o == "land" else (0.06 * W, 0.54 * H, 0.88 * W, 0.20 * H)
    rects, draws = {}, []
    if num:
        r, _z, d = display(k, slide, nrect, num, "number", caps=False, anchor="b")
        rects["number"] = r; draws.append(d)
    if label:
        r1, _z, d1 = display(k, slide, lrect, label, "label")
        rects["label"] = r1; draws.append(d1)
        if note:
            nr, nd = flow(k, slide, "data", (lrect[0], r1[1] + r1[3] + 0.2 * s, lrect[2], 1.2 * s), [("note", note)])
            rects.update(nr); draws.append(nd)
    _poster_meta(k, slide, text_of(f, "kicker"))
    _run_all(draws)
    return rects


@register("poster", "closing")
def _poster_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    fld = k.field
    title, line, hl = text_of(f, "title"), text_of(f, "line"), text_of(f, "highlight")
    trect = (0.05 * W, 0.14 * H, 0.70 * W, 0.58 * H) if o == "land" else (0.06 * W, 0.12 * H, 0.88 * W, 0.50 * H)
    rects, draws = {}, []
    if title:
        r, _z, d = display(k, slide, trect, title, "title", highlight=hl, hl=fld["hl"], hl_ink=fld["hl_ink"])
        rects["title"] = r; draws.append(d)
        if line:
            lr, ld = flow(k, slide, "closing", (trect[0], r[1] + r[3] + 0.3 * s, trect[2], 1.0 * s), [("line", line)])
            rects.update(lr); draws.append(ld)
    blocks = ((0.80 * W, 0.62 * H, 0.30 * W, 0.30 * W, 12.0),) if o == "land" else ((0.62 * W, 0.80 * H, 0.50 * W, 0.24 * H, 12.0),)
    _blocks(k, slide, blocks)
    _poster_meta(k, slide, None)
    _run_all(draws)
    return rects


@register("poster", "points")
def _poster_points(k, slide, f, image):
    W, H, s, o = ctx(k)
    fld = k.field
    title, kicker = text_of(f, "title"), text_of(f, "kicker")
    pts = points_of(f.get("items"))
    n = len(pts)
    rects, draws = {}, []
    if o == "land":
        trect, (rx, ry, rw, rh) = (0.04 * W, 0.11 * H, 0.42 * W, 0.42 * H), (0.50 * W, 0.30 * H, 0.46 * W, 0.63 * H)
    else:
        trect, (rx, ry, rw, rh) = (0.06 * W, 0.08 * H, 0.88 * W, 0.20 * H), (0.06 * W, 0.34 * H, 0.88 * W, 0.58 * H)
    if title:
        r, _z, d = display(k, slide, trect, title, "label")
        rects["title"] = r; draws.append(d)
    gap = 0.15 * s
    pw = (rw - (n - 1) * gap) / n
    for i, (head, line) in enumerate(pts):
        ph = rh * (0.64 + 0.36 * (i / float(max(n - 1, 1))))
        px, py = rx + i * (pw + gap), ry + rh - ph
        dk.box(slide, px, py, pw, ph, fill=fld["panel"])
        nr, nd = flow(k, slide, "points", (px + 0.12 * s, py + 0.10 * s, pw - 0.24 * s, min(1.4 * s, ph * 0.4)),
                      [("mark", "{:02d}".format(i + 1))], accent=fld["panel_accent"],
                      start={"mark": min(80.0 * s, pw * 72 * 0.42)})
        tr, td_ = flow(k, slide, "points", (px + 0.14 * s, py + ph * 0.45, pw - 0.28 * s, ph * 0.52),
                       [(x_, t) for x_, t in (("item_head", head), ("item_line", line)) if t], anchor="bottom",
                       ink=fld["panel_ink"], mute=fld["panel_ink"])
        draws += [nd, td_]
    _poster_meta(k, slide, kicker)
    _run_all(draws)
    return rects
```

(`_run_all` is defined in the ink section of Task 4 and shared.)

- [ ] **Step 4: Run — expect pass; render and LOOK** against `~/Desktop/slide-maker 新设计语言 样张/sheets/poster.jpg` (same render recipe as Task 4 with `vl.use('poster', prs)` and English copy, highlight `ROOM`).

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py 2>&1 | tail -3`
Expected: `N passed, 0 failed`

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/vl_native.py skills/slide-maker/tests/test_native_languages.py
git commit -m "poster: seven pages — a colour field per page, measured display type, highlight, staircase points"
```

---

### Task 6: `cutpaper` compositions

**Files:**
- Modify: `skills/slide-maker/scripts/vl_native.py`, `skills/slide-maker/tests/test_native_languages.py`

**Interfaces:**
- Consumes: Task 3 helpers; `native_art` (`paper_hill`, `hill_points`, `paper_card`, `cloud`, `paper_sun`, `disc`); `icons.icon_png(spec, out_png, color=, px=)`, `deckkit.icon(slide, png, x, y, size, alt=)`.
- Produces: `vl_native.CUT_ART: dict[ground, dict]`; `COMPOSERS["cutpaper"]` (seven pages); `icons=` on `points` (one icon spec per point, e.g. `"lucide:wind"`).

- [ ] **Step 1: Append the cutpaper cases to the test**

```python
# ── cutpaper ──
assert_matrix("cutpaper")
import vl_native as _vn
for g, A in _vn.CUT_ART.items():
    for disc_ in A["discs"]:
        check(cr("FFFFFF", disc_) >= 3.0, "cutpaper/{}: a white icon on disc {} clears 3:1".format(g, disc_))
    for ring in A["rings"][-1:]:
        pal = vl.VARIANTS["cutpaper"][g]["palette"]
        check(cr(pal["card_ink"], ring) >= 4.5, "cutpaper/{}: the figure on the inner sun ring reads".format(g))
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("cutpaper", prs)
s = k.new_slide()
k.points(s, title="Three ways a seed gets around", items=["Wind", "Water", "Animals"],
         icons=["lucide:wind", "lucide:droplets", "lucide:paw-print"])
check(sum(1 for sh in s.shapes if sh.shape_type == 13) == 3, "cutpaper: one icon per point")
try:
    k.points(k.new_slide(), title="x", items=["a", "b"], icons=["lucide:wind"])
    check(False, "cutpaper: icons= must match the points one to one")
except ValueError:
    check(True, "cutpaper: icons= must match the points one to one")
```

- [ ] **Step 2: Run — expect failure** (`AttributeError: module 'vl_native' has no attribute 'CUT_ART'`).

- [ ] **Step 3: Append the cutpaper compositions to `vl_native.py`**

```python
# ═══════════════════════════════════ cutpaper 剪纸层叠 ═══════════════════════════════════
CUT_ART = {
    "light": {"hills": ("D3E8C9", "A2CFA3", "5AA38A", "2F6F62"), "sun": ("F7D38A", "F2B33D"),
              "rings": ("FBE6B4", "F7D38A", "F2B33D", "E8902F"), "cloud": "FFFFFF", "sheets": ("F2B33D", "EE8A6B"),
              "discs": ("C2553A", "2E6DA4", "5B3F6E", "2F7F69")},
    "night": {"hills": ("2E4A63", "3B6476", "467E7A", "234F4E"), "sun": ("D9CDA6", "F1E7C8"),
              "rings": ("39466A", "D9CDA6", "F1E7C8", "C9B98A"), "cloud": "C9D3E3", "sheets": ("F1E7C8", "EE8A6B"),
              "discs": ("C2553A", "2E6DA4", "5B3F6E", "2F7F69")},
}


def _card_flow(k, slide, page, col, items, **kw):
    return flow(k, slide, page, col, items, ink=k.P["card_ink"], mute=k.P["card_mute"], accent=k.P["card_accent"], **kw)


def _back_hills(k, slide, o, seed=1):
    W, H, s, _o = ctx(k)
    A = CUT_ART[k.ground]
    base = (0.61, 0.71) if o == "land" else (0.70, 0.78)
    na.paper_hill(slide, na.hill_points(W, base[0] * H, 0.16 * H if o == "land" else 0.08 * H, seed, 1.3), H, fill=A["hills"][0])
    na.paper_hill(slide, na.hill_points(W, base[1] * H, 0.15 * H if o == "land" else 0.07 * H, seed + 3, 1.7), H, fill=A["hills"][1])


def _front_hills(k, slide, o, seed=7, low=False):
    W, H, s, _o = ctx(k)
    A = CUT_ART[k.ground]
    if not low:
        na.paper_hill(slide, na.hill_points(W, (0.82 if o == "land" else 0.86) * H, 0.08 * H, seed, 1.9), H, fill=A["hills"][2])
    na.paper_hill(slide, na.hill_points(W, (0.92 if o == "land" else 0.93) * H, 0.05 * H, seed + 2, 2.6), H, fill=A["hills"][3])


@register("cutpaper", "cover")
def _cut_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    A = CUT_ART[k.ground]
    if o == "land":
        card, sun, clouds = (0.064 * W, 0.14 * H, 0.48 * W, 0.47 * H), (0.76 * W, 0.23 * H, 0.35 * H), \
            ((0.56 * W, 0.17 * H, 0.15 * W), (0.91 * W, 0.43 * H, 0.11 * W))
    else:
        card, sun, clouds = (0.08 * W, 0.10 * H, 0.84 * W, 0.32 * H), (0.70 * W, 0.53 * H, 0.26 * W), \
            ((0.28 * W, 0.50 * H, 0.30 * W),)
    pad = 0.4 * s
    items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title", "subtitle") if text_of(f, x_)]
    r, d = _card_flow(k, slide, "cover", (card[0] + pad, card[1] + pad, card[2] - 2 * pad, card[3] - 2 * pad), items)
    text_bottom = max((v[1] + v[3] for v in r.values()), default=card[1])
    na.paper_sun(slide, sun[0], sun[1], (sun[2], sun[2] * 0.7), A["sun"])
    for cx, cy, cw in clouds:
        na.cloud(slide, cx, cy, cw, fill=A["cloud"])
    _back_hills(k, slide, o)
    na.paper_card(slide, *card)
    if o == "land":                  # the near hill tucks the card's foot into the scene — never above its words
        foot = card[1] + card[3]
        tuck = max(text_bottom + 0.15 * s, foot - 0.30 * s)
        right = card[0] + card[2]
        pts = [(W * i / 16.0, min(H - 0.3, tuck + 0.12 * s * _math.sin(i * 0.9) + max(0.0, W * i / 16.0 - right) * 0.16))
               for i in range(17)]
        near = na.paper_hill(slide, pts, H, fill=A["hills"][2])
        dk.overlap_intent(near, "the near paper hill tucks the title card's foot into the scene")
        _front_hills(k, slide, o, low=True)
    else:
        _front_hills(k, slide, o)
    d()
    return r


@register("cutpaper", "section")
def _cut_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    A = CUT_ART[k.ground]
    num, kicker, title = text_of(f, "number"), text_of(f, "kicker"), text_of(f, "title")
    cx, cy, d0 = (0.24 * W, 0.46 * H, 0.52 * H) if o == "land" else (0.50 * W, 0.26 * H, 0.56 * W)
    rects, draws = {}, []
    if num:
        r, d = _card_flow(k, slide, "section", (cx - d0 * 0.3, cy - d0 * 0.3, d0 * 0.6, d0 * 0.6), [("number", num)],
                          anchor="middle", align="c", start={"number": 120 * s})
        rects.update(r); draws.append(d)
    col = (0.48 * W, 0.24 * H, 0.44 * W, 0.46 * H) if o == "land" else (0.08 * W, 0.56 * H, 0.84 * W, 0.28 * H)
    items = [(x_, t) for x_, t in (("kicker", kicker), ("title", title)) if t]
    r, d = flow(k, slide, "section", col, items, anchor="middle" if o == "land" else "top")
    rects.update(r); draws.append(d)
    na.paper_sun(slide, cx, cy, (d0, d0 * 0.72), (A["rings"][1], A["rings"][3]))
    _front_hills(k, slide, o, seed=11)
    _run_all(draws)
    return rects


@register("cutpaper", "image_text")
def _cut_image_text(k, slide, f, image):
    W, H, s, o = ctx(k)
    frame = (0.06 * W, 0.10 * H, 0.46 * W, 0.76 * H) if o == "land" else (0.08 * W, 0.05 * H, 0.84 * W, 0.44 * H)
    card = (0.57 * W, 0.18 * H, 0.37 * W, 0.62 * H) if o == "land" else (0.08 * W, 0.53 * H, 0.84 * W, 0.36 * H)
    pad = 0.35 * s
    items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title", "body", "caption") if text_of(f, x_)]
    r, d = _card_flow(k, slide, "image_text", (card[0] + pad, card[1] + pad, card[2] - 2 * pad, card[3] - 2 * pad), items,
                      anchor="middle")
    na.paper_card(slide, *frame)
    inset = 0.14 * s
    place_image(k, slide, image, (frame[0] + inset, frame[1] + inset, frame[2] - 2 * inset, frame[3] - 2 * inset), "image_text")
    na.paper_card(slide, *card)
    d()
    return r


@register("cutpaper", "quote")
def _cut_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    A = CUT_ART[k.ground]
    card = (0.12 * W, 0.17 * H, 0.76 * W, 0.61 * H) if o == "land" else (0.08 * W, 0.18 * H, 0.84 * W, 0.56 * H)
    for (dx, dy, rot), col in zip(((0.30, 0.28, 3.5), (0.15, 0.14, -2.0)), A["sheets"]):
        na.paper_card(slide, card[0] + dx * s, card[1] + dy * s, card[2] - 0.5 * s, card[3] - 0.3 * s, fill=col, rotation=rot)
    na.paper_card(slide, *card)
    pad = 0.6 * s
    items = [(x_, text_of(f, x_)) for x_ in ("quote", "attribution") if text_of(f, x_)]
    items = [("mark", "“")] + items
    r, d = _card_flow(k, slide, "quote", (card[0] + pad, card[1] + pad * 0.6, card[2] - 2 * pad, card[3] - 1.2 * pad), items,
                      anchor="middle")
    d()
    return r


@register("cutpaper", "data")
def _cut_data(k, slide, f, image):
    W, H, s, o = ctx(k)
    A = CUT_ART[k.ground]
    num, label, note = text_of(f, "number"), text_of(f, "label"), text_of(f, "note")
    cx, cy, D = (0.27 * W, 0.50 * H, 0.86 * H) if o == "land" else (0.50 * W, 0.28 * H, 0.86 * W)
    rects, draws = {}, []
    if num:
        inner = D * 0.39
        r, d = _card_flow(k, slide, "data", (cx - inner / 2, cy - inner / 2, inner, inner), [("number", num)],
                          anchor="middle", align="c")
        rects.update(r); draws.append(d)
    col = (cx + D / 2 + 0.5 * s, 0.24 * H, 0.94 * W - (cx + D / 2 + 0.5 * s), 0.50 * H) if o == "land" else \
        (0.08 * W, cy + D / 2 + 0.4 * s, 0.84 * W, 0.84 * H - (cy + D / 2 + 0.4 * s))
    items = [(x_, t) for x_, t in (("label", label), ("note", note)) if t]
    r, d = flow(k, slide, "data", col, items, anchor="middle" if o == "land" else "top")
    rects.update(r); draws.append(d)
    na.paper_sun(slide, cx, cy, tuple(D * x for x in (1.0, 0.78, 0.58, 0.39)), A["rings"])
    _run_all(draws)
    return rects


@register("cutpaper", "closing")
def _cut_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    A = CUT_ART[k.ground]
    card = (0.22 * W, 0.16 * H, 0.56 * W, 0.36 * H) if o == "land" else (0.08 * W, 0.12 * H, 0.84 * W, 0.30 * H)
    pad = 0.4 * s
    items = [(x_, text_of(f, x_)) for x_ in ("title", "line") if text_of(f, x_)]
    r, d = _card_flow(k, slide, "closing", (card[0] + pad, card[1] + pad, card[2] - 2 * pad, card[3] - 2 * pad), items,
                      anchor="middle", align="c")
    na.paper_sun(slide, 0.85 * W, (0.14 if o == "land" else 0.50) * H, (0.16 * min(W, H), 0.11 * min(W, H)), A["sun"])
    _back_hills(k, slide, o, seed=21)
    na.paper_card(slide, *card)
    _front_hills(k, slide, o, seed=23)
    d()
    return r


@register("cutpaper", "points")
def _cut_points(k, slide, f, image):
    import icons as _ic
    import tempfile as _tf
    W, H, s, o = ctx(k)
    A = CUT_ART[k.ground]
    pts = points_of(f.get("items"))
    icons_ = f.get("icons")
    if icons_ is not None and (not isinstance(icons_, (list, tuple)) or len(icons_) != len(pts)):
        raise ValueError("cutpaper.points(): icons= takes one icon spec per point ({} points), got {!r}".format(len(pts), icons_))
    rects, draws = {}, []
    head_items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title") if text_of(f, x_)]
    r, d = flow(k, slide, "points", (0.07 * W, 0.08 * H, 0.86 * W, 0.16 * H), head_items)
    rects.update(r); draws.append(d)
    n = len(pts)
    if o == "land":
        gap, top, ch = 0.35 * s, 0.28 * H, 0.48 * H
        cw = (0.86 * W - (n - 1) * gap) / n
        cards = [(0.07 * W + i * (cw + gap), top, cw, ch) for i in range(n)]
    else:
        gap, top = 0.25 * s, 0.24 * H
        ch = (0.64 * H - (n - 1) * gap) / n
        cards = [(0.08 * W, top + i * (ch + gap), 0.84 * W, ch) for i in range(n)]
    _front_hills(k, slide, o, seed=31, low=True)
    for i, ((cx, cy, cw, chh), (head, line)) in enumerate(zip(cards, pts)):
        na.paper_card(slide, cx, cy, cw, chh)
        dd = min(1.1 * s, chh * 0.38, cw * 0.38)
        dx, dy = cx + 0.3 * s + dd / 2, cy + 0.3 * s + dd / 2
        na.disc(slide, dx, dy, dd, A["discs"][i % len(A["discs"])], shadow=True)
        if icons_:
            png = str(Path(_tf.gettempdir()) / "slide-maker-native-art" / "icon_{}.png".format(str(icons_[i]).replace(":", "_")))
            Path(png).parent.mkdir(parents=True, exist_ok=True)
            _ic.icon_png(icons_[i], png, color="FFFFFF", px=200)
            draws.append(lambda png=png, dx=dx, dy=dy, dd=dd, head=head: dk.icon(slide, png, dx - dd * 0.3, dy - dd * 0.3, dd * 0.6, alt=head))
        else:
            nr, nd = flow(k, slide, "points", (dx - dd / 2, dy - dd / 2, dd, dd), [("mark", str(i + 1))], align="c",
                          anchor="middle", ink="FFFFFF", accent="FFFFFF", start={"mark": dd * 72 * 0.5})
            draws.append(nd)
        if o == "land":
            tcol = (cx + 0.3 * s, cy + 0.45 * s + dd, cw - 0.6 * s, chh - dd - 0.7 * s)
        else:
            tcol = (cx + 0.6 * s + dd, cy + 0.25 * s, cw - dd - 0.9 * s, chh - 0.5 * s)
        tr, td_ = _card_flow(k, slide, "points", tcol, [(x_, t) for x_, t in (("item_head", head), ("item_line", line)) if t],
                             anchor="top")
        draws.append(td_)
    _run_all(draws)
    return rects
```

Add `from pathlib import Path` to the imports at the top of `vl_native.py`.

- [ ] **Step 4: Run — expect pass; render and LOOK** against `sheets/cutpaper.jpg` and `sheets/cutpaper-night.jpg` (check that the near hill covers the card's foot, never its words).

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py 2>&1 | tail -3`
Expected: `N passed, 0 failed`

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/vl_native.py skills/slide-maker/tests/test_native_languages.py
git commit -m "cutpaper: seven pages — a paper diorama, the title card tucked between hills, the figure on a paper sun"
```

---

### Task 7: `blueprint` compositions

**Files:**
- Modify: `skills/slide-maker/scripts/native_art.py` (add `title_block_project`; `drawing_sheet` uses it), `skills/slide-maker/scripts/vl_native.py`, `skills/slide-maker/tests/test_native_languages.py`

**Interfaces:**
- Consumes: Task 3 helpers; `native_art` (`grid_background`, `drawing_sheet`, `iso_stack`, `dimension_line`, `balloon`, `seg`).
- Produces: `native_art.title_block_project(slide, block, project, *, ink, mute, face)`; `GROUNDS["blueprint"]`; `COMPOSERS["blueprint"]` (seven pages); `Kit._sheet = (content_rect, block_rect)`.

- [ ] **Step 1: Append the blueprint cases to the test**

```python
# ── blueprint ──
assert_matrix("blueprint")
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("blueprint", prs)
s1 = k.new_slide()
k.cover(s1, title="A room built layer by layer", kicker="Schematic 01")
s2 = k.new_slide()
k.points(s2, title="Three layers, one frame", items=[("Floor", "One plate"), ("Walls", "Panels slide"), ("Roof", "One span")])
txt = lambda s: " ".join(sh.text_frame.text for sh in s.shapes if getattr(sh, "has_text_frame", False))
check("A room built layer by layer" in txt(s2), "blueprint: the title block carries the cover title on later sheets")
check("SHEET" in txt(s1) and "01" in txt(s1) and "02" in txt(s2), "blueprint: each sheet is numbered")
n_tops = sum(1 for sh in s2.shapes if sh.shape_type == 5)        # freeform: the iso stack draws layers as polygons
check(n_tops >= 9, "blueprint: the points page draws one iso layer per point (3 layers x 3 faces)")
s3 = k.new_slide()
k.cover(s3, title="Another title", project="A modular reading room")
check("A modular reading room" in txt(s3), "blueprint: project= replaces the remembered title")
```

- [ ] **Step 2: Run — expect failure** (`NotImplementedError: blueprint.cover()`).

- [ ] **Step 3: `native_art.py` — split the title-block words out of `drawing_sheet`**

Replace the `if project:` block inside `drawing_sheet` with `if project: title_block_project(slide, (bx, by, bw, bh), project, ink=ink, mute=mute, face=face)` and add:

```python
def title_block_project(slide, block, project, *, ink, mute, face):
    """The caller's project words in a drawing sheet's title block (left field)."""
    W, H = page_size(slide)
    s = min(W, H) / 7.5
    bx, by, bw, bh = block
    split = bx + bw * 0.66
    rgb = lambda c: dk._as_rgb(hexstr(c))              # noqa: E731
    dk.text(slide, bx + 0.08 * s, by + 0.06 * s, split - bx - 0.14 * s, bh - 0.12 * s,
            [[("PROJECT", max(8.0, 8.0 * s), rgb(mute), False, False, face)],
             [(str(project), max(9.0, 10.0 * s), rgb(ink), True, False, face, face)]], space_after=0)
```

- [ ] **Step 4: Append the blueprint compositions to `vl_native.py`**

```python
# ═══════════════════════════════════ blueprint 蓝图技术线稿 ═══════════════════════════════════
def _bp_ground(k, slide):
    na.grid_background(slide, base=k.P["ground"], ink=k.P["ink"])
    content, block = na.drawing_sheet(slide, ink=k.P["ink"], mute=k.P["mute"], accent=k.P["text_accents"][0],
                                      number=len(k.prs.slides), project=k.project, face=k.face("mono"))
    k._sheet = (content, block, k.project is not None)


GROUNDS["blueprint"] = _bp_ground


def _bp_area(k):
    """The sheet's content rect above the title block, and the block itself."""
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), block, _done = k._sheet
    return (cx, cy, cw, block[1] - 0.15 * s - cy), block


def _bp_project(k, slide, f, fallback=None):
    """Remember the caller's project words (project=, else the cover title) and write them into this sheet's title
    block if the ground could not (the cover is where the title first arrives)."""
    words = text_of(f, "project") or k.project or fallback
    if words and words != k.project:
        k.project = words
        content, block, done = k._sheet
        if not done:
            na.title_block_project(slide, block, words, ink=k.P["ink"], mute=k.P["mute"], face=k.face("mono"))
            k._sheet = (content, block, True)


@register("blueprint", "cover")
def _bp_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f, fallback=text_of(f, "title"))
    col = (cx, cy + 0.10 * ch, cw * (0.62 if o == "land" else 1.0), ch * 0.80)
    items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title", "subtitle") if text_of(f, x_)]
    r, d = flow(k, slide, "cover", col, items, anchor="middle")
    d()
    return r


@register("blueprint", "section")
def _bp_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f)
    num, kicker, title = text_of(f, "number"), text_of(f, "kicker"), text_of(f, "title")
    rects, draws = {}, []
    dd = min(1.8 * s, ch * 0.5)
    by_ = cy + (ch - dd) / 2 if o == "land" else cy + 0.1 * ch
    if num:
        na.balloon(slide, cx, by_, dd, num, ink=k.P["ink"], accent=k.P["text_accents"][0], face=k.face("mono"),
                   fill=k.P["ground"])
    col = (cx + dd + 0.5 * s, cy, cw - dd - 0.5 * s, ch) if o == "land" else (cx, by_ + dd + 0.4 * s, cw, ch * 0.5)
    items = [(x_, t) for x_, t in (("kicker", kicker), ("title", title)) if t]
    r, d = flow(k, slide, "section", col, items, anchor="middle" if o == "land" else "top")
    rects.update(r); draws.append(d)
    _run_all(draws)
    return rects


@register("blueprint", "image_text")
def _bp_image_text(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f)
    img = (cx, cy, cw * 0.56, ch) if o == "land" else (cx, cy, cw, ch * 0.50)
    col = (cx + cw * 0.62, cy + 0.1 * ch, cw * 0.38, ch * 0.8) if o == "land" else (cx, cy + ch * 0.56, cw, ch * 0.44)
    items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title", "body", "caption") if text_of(f, x_)]
    r, d = flow(k, slide, "image_text", col, items, anchor="middle" if o == "land" else "top")
    place_image(k, slide, image, img, "image_text")
    d()
    return r


@register("blueprint", "quote")
def _bp_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f)
    has_img = image is not None
    col = (cx, cy + 0.12 * ch, cw * (0.58 if has_img and o == "land" else 0.85), ch * 0.72)
    items = [(x_, text_of(f, x_)) for x_ in ("quote", "attribution") if text_of(f, x_)]
    r, d = flow(k, slide, "quote", col, items, anchor="middle")
    if has_img:
        place_image(k, slide, image, (cx + cw * 0.64, cy, cw * 0.36, ch) if o == "land" else (cx, cy + ch * 0.6, cw, ch * 0.4),
                    "quote")
    d()
    return r


@register("blueprint", "data")
def _bp_data(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f)
    num, label, note = text_of(f, "number"), text_of(f, "label"), text_of(f, "note")
    rects, draws = {}, []
    nrect = (cx, cy, cw * 0.40, ch) if o == "land" else (cx, cy, cw, ch * 0.48)
    if num:
        r, d = flow(k, slide, "data", nrect, [("number", num)], anchor="middle", align="c")
        rects.update(r); draws.append(d)
        nr = r.get("number", nrect)
        dxl = nr[0] + nr[2] + 0.25 * s if o == "land" else nr[0] + nr[2] - 0.3 * s
        draws.append(lambda: na.dimension_line(slide, min(dxl, cx + cw * 0.46), nr[1] + 0.1 * nr[3], nr[1] + 0.9 * nr[3],
                                               ink=k.P["ink"]))
    col = (cx + cw * 0.50, cy + 0.15 * ch, cw * 0.50, ch * 0.7) if o == "land" else (cx, cy + ch * 0.54, cw, ch * 0.44)
    items = [(x_, t) for x_, t in (("label", label), ("note", note)) if t]
    r, d = flow(k, slide, "data", col, items, anchor="middle" if o == "land" else "top")
    rects.update(r); draws.append(d)
    _run_all(draws)
    return rects


@register("blueprint", "closing")
def _bp_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f)
    col = (cx, cy + 0.15 * ch, cw * (0.70 if o == "land" else 1.0), ch * 0.6)
    items = [(x_, text_of(f, x_)) for x_ in ("title", "line") if text_of(f, x_)]
    r, d = flow(k, slide, "closing", col, items, anchor="middle")
    d()
    return r


@register("blueprint", "points")
def _bp_points(k, slide, f, image):
    W, H, s, o = ctx(k)
    (cx, cy, cw, ch), _b = _bp_area(k)
    _bp_project(k, slide, f)
    pts = points_of(f.get("items"))
    n = len(pts)
    rects, draws = {}, []
    head_items = [(x_, text_of(f, x_)) for x_ in ("kicker", "title") if text_of(f, x_)]
    r, d = flow(k, slide, "points", (cx, cy, cw * (0.62 if o == "land" else 1.0), ch * 0.18), head_items)
    rects.update(r); draws.append(d)
    top = max((v[1] + v[3] for v in r.values()), default=cy) + 0.35 * s
    if o == "land":
        size = min(cw * 0.20, (cy + ch - top) * 0.55)
        gap = max(0.5 * s, (cy + ch - top - size - 0.4 * s) / max(n, 1))
        scx, scy = cx + cw * 0.28, top
        notes_x = cx + cw * 0.60
    else:
        size = min(cw * 0.28, ch * 0.16)
        gap = max(0.4 * s, ch * 0.30 / max(n, 1))
        scx, scy = cx + cw * 0.35, top
        notes_x = cx + cw * 0.62
    tops = na.iso_stack(slide, scx, scy, size, gap, n, ink=k.P["ink"], accent=k.P["accents"][0], accent_layer=0)
    bd = 0.42 * s
    for i, ((head, line), layer) in enumerate(zip(pts, tops)):
        ax, ay = layer[1]                                     # the layer's right corner
        by_ = ay - bd / 2
        draws.append(lambda ax=ax, ay=ay, by_=by_: na.seg(slide, ax, ay, notes_x, by_ + bd / 2, k.P["ink"], w=0.6))
        draws.append(lambda by_=by_, i=i: na.balloon(slide, notes_x, by_, bd, str(i + 1), ink=k.P["ink"],
                                                     accent=k.P["text_accents"][0], face=k.face("mono"),
                                                     fill=k.P["ground"]))
        tr, td_ = flow(k, slide, "points", (notes_x + bd + 0.2 * s, by_ - 0.05 * s, cx + cw - (notes_x + bd + 0.2 * s), gap * 0.95),
                       [(x_, t) for x_, t in (("item_head", head), ("item_line", line)) if t], anchor="top")
        draws.append(td_)
    _run_all(draws)
    return rects
```

- [ ] **Step 5: Run — expect pass; render and LOOK** against `sheets/blueprint.jpg` and `sheets/blueprint-cyanotype.jpg` (the leader from each layer must land on its balloon; the title block must not collide with text).

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py 2>&1 | tail -3`
Expected: `N passed, 0 failed`

- [ ] **Step 6: Commit**

```bash
git add skills/slide-maker/scripts/native_art.py skills/slide-maker/scripts/vl_native.py skills/slide-maker/tests/test_native_languages.py
git commit -m "blueprint: seven pages — a numbered drawing sheet, one iso layer per point, a dimensioned figure"
```

---

### Task 8: Bundled samples and the direction preview

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py` (`_SAMPLE_COPY_NATIVE`, `build_sample` native branch)
- Create: `skills/slide-maker/assets/vl/samples/{ink,ink-night,poster,poster-paper,cutpaper,cutpaper-night,blueprint,blueprint-cyanotype}.jpg`
- Modify: `skills/slide-maker/tests/test_visual_languages.py` (restore the sample/direction loops to `vl.LANGS`), `tests/test_native_languages.py`

**Interfaces:**
- Produces: `vl.build_sample(name, out_dir, ground=...)` for the native languages (cover, points, quote, data); `vl.direction(name)` works for all eight languages and their grounds.

- [ ] **Step 1: Test** — append to `tests/test_native_languages.py`:

```python
# ── samples + direction ──
for n in vl.NATIVE:
    for g in vl.VARIANTS[n]:
        p = vl.build_sample(n, str(td), ground=g)
        with contextlib.redirect_stdout(io.StringIO()):
            crit = [f for f in dk.lint_layout(__import__("pptx").Presentation(str(p)), verbose=False) if f[1] == "CRITICAL"]
        check(not crit, "{}/{} sample: no critical fault".format(n, g))
        sample = vl.ASSETS / "samples" / "{}.jpg".format(vl._sample_stem(n, g))
        check(sample.exists() and sample.stat().st_size <= 350 * 1024, "{}/{}: a bundled JPG sample <= 350 KB".format(n, g))
        d = vl.direction(n, ground=g)
        check(d["vl"] == n and d["sample"].startswith("data:image/jpeg"), "{}/{}: direction() previews it".format(n, g))
```

and in `tests/test_visual_languages.py` change the bundled-sample loop and the `vl.direction(n_)` loop back to `vl.LANGS`.

- [ ] **Step 2: Run — expect failure** (`build_sample` composes image pages: `ValueError ... image_text`), or missing samples.

- [ ] **Step 3: `visual_languages.py` — native sample copy and branch**

```python
_SAMPLE_COPY_NATIVE = {
    "ink": [("cover", dict(kicker="茶事 · 卷一", title="一盏茶的时间", subtitle="慢下来，看见日常", seal="茶事")),
            ("points", dict(title="三道工序", items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")], seal="序")),
            ("quote", dict(quote="茶有两种姿态，浮与沉", attribution="茶室题记", seal="记")),
            ("data", dict(number="3", label="泡，滋味最浓", note="头泡醒茶，三泡正好", seal="茶"))],
    "poster": [("cover", dict(kicker="A manifesto for neighbourhood rooms", title="Make the room smaller.", highlight="room")),
               ("points", dict(title="Three moves.", items=["Share the tools", "Open the door", "Keep it local"])),
               ("quote", dict(quote="A room is a promise you can walk into.", attribution="From the manifesto")),
               ("data", dict(number="01", label="Room on every street.", note="Close enough to walk to, small enough to share."))],
    "cutpaper": [("cover", dict(kicker="A paper-cut science story", title="How seeds travel")),
                 ("points", dict(title="Three ways a seed gets around",
                                 items=[("Wind", "Wings and parachutes drift far."), ("Water", "Some seeds float to a new shore."),
                                        ("Animals", "Hooks hitch a ride on fur.")],
                                 icons=["lucide:wind", "lucide:droplets", "lucide:paw-print"])),
                 ("quote", dict(quote="Every forest began as one small seed.", attribution="A paper-cut science story")),
                 ("data", dict(number="1", label="seed is all a forest needs", note="Small beginnings, slow growth."))],
    "blueprint": [("cover", dict(kicker="Schematic 01 · a modular reading room", title="A room built layer by layer.",
                                 subtitle="Floor, walls and roof drawn as one frame, each layer free to move.")),
                  ("points", dict(title="Three layers, one frame", items=[("Floor", "One continuous plate."),
                                                                         ("Walls", "Panels that slide on a track."),
                                                                         ("Roof", "A single span, no columns.")])),
                  ("quote", dict(quote="“Draw the quiet first, then the walls.”", attribution="Design principle")),
                  ("data", dict(number="3", label="layers, one structure.", note="Each layer can be built, moved and reused on its own."))],
}
```

In `build_sample`, before `kind = ...`, add:

```python
    if name in NATIVE:
        prs = dk.blank_deck(W, H)
        k = use(name, prs, ground=ground)
        for page, fields in _SAMPLE_COPY_NATIVE[name]:
            getattr(k, page)(k.new_slide(), **fields)
        out = Path(out_dir) / "sample-{}.pptx".format(_sample_stem(name, ground))
        out.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(out))
        return out
```

- [ ] **Step 4: Build, render and contact the samples — then LOOK at all eight sheets**

```bash
cd skills/slide-maker
python3 scripts/visual_languages.py --sample /tmp/vl_samples | grep -E "^(NEXT|then):" | sed 's/^NEXT: //; s/^then: //' > /tmp/vl_cmds.sh
grep -E "ink|poster|cutpaper|blueprint" /tmp/vl_cmds.sh | sh
ls -la assets/vl/samples/*.jpg
```
Expected: eight new JPGs, each ≤ 350 KB. Read every sheet; compare with the look-dev sheets on the Desktop.

- [ ] **Step 5: Run — expect pass**

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py | tail -1 && python3 tests/test_visual_languages.py | tail -1`
Expected: `0 failed` / `] ok`.

- [ ] **Step 6: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/assets/vl/samples/ink.jpg skills/slide-maker/assets/vl/samples/ink-night.jpg skills/slide-maker/assets/vl/samples/poster.jpg skills/slide-maker/assets/vl/samples/poster-paper.jpg skills/slide-maker/assets/vl/samples/cutpaper.jpg skills/slide-maker/assets/vl/samples/cutpaper-night.jpg skills/slide-maker/assets/vl/samples/blueprint.jpg skills/slide-maker/assets/vl/samples/blueprint-cyanotype.jpg skills/slide-maker/tests/test_native_languages.py skills/slide-maker/tests/test_visual_languages.py
git commit -m "native visual languages: bundled samples and direction previews"
```

---

### Task 9: The offer rule on both runtimes

**Files:**
- Modify: `skills/slide-maker/scripts/directions_diversity.py` (`NATIVE_LANGS`, `native_fault`), `scripts/render_deck.py` (`_direction_gate`), `scripts/codex_delivery_gate.py` (direction-gate block)
- Modify: `skills/slide-maker/SKILL.md` (one added sentence — no existing line rewritten), `references/interview-protocol.md`, `references/codex-runtime.md`
- Test: `skills/slide-maker/tests/test_direction_vl_rule.py` (append)

**Interfaces:**
- Produces: `directions_diversity.NATIVE_LANGS == visual_languages.NATIVE`; `directions_diversity.native_fault(images, directions, fit=None) -> str | None`; the record `direction_gate.native_fit = {"language": "<native language offered>", "why": "<the topic reason>"}`.

- [ ] **Step 1: Test** — append to `tests/test_direction_vl_rule.py` before the final print:

```python
# 5. a deck with NO pictures offers a native language — the one that fits the topic, with the reason recorded
ink_dir = vl.direction("ink")
check(tuple(dd.NATIVE_LANGS) == tuple(vl.NATIVE), "directions_diversity knows the same native languages")
f_ = dd.native_fault("none", plain)
check(f_ and "native" in f_ and "blueprint" in f_, "no pictures + no native language among the directions is a fault: {!r}".format(f_))
f_ = dd.native_fault("none", plain[:3] + [ink_dir])
check(f_ and "native_fit" in f_, "a native language offered without its reason asks for native_fit: {!r}".format(f_))
check(dd.native_fault("none", plain[:3] + [ink_dir], {"language": "ink", "why": "a talk on tea and craft"}) is None,
      "a native language with its reason passes")
check(dd.native_fault("none", plain[:3] + [ink_dir], {"language": "poster", "why": "a manifesto"}) is not None,
      "native_fit must name a language that was offered")
check(dd.native_fault("photos", plain) is None, "with pictures the native rule does not apply")
m = rd_msg({"candidates": plain, "picked": "A", "images": "none"})
check("native" in m, "render_deck holds a picture-less deck with no native language: {}".format(m[-300:]))
m = rd_msg({"candidates": plain[:3] + [ink_dir], "picked": "A", "images": "none",
            "native_fit": {"language": "ink", "why": "a talk on tea and craft"}})
check("native" not in m, "render_deck: a native language with its reason clears it: {}".format(m[-300:]))
e = cdg_errs({"candidates": plain, "picked": "A", "images": "none"})
check(any("native" in x for x in e), "codex gate holds the same deck: {}".format(e))
```

- [ ] **Step 2: Run — expect failure** (`AttributeError: ... 'native_fault'`).

- [ ] **Step 3: `directions_diversity.py`**

```python
NATIVE_LANGS = ("ink", "poster", "cutpaper", "blueprint")      # mirrors visual_languages.NATIVE (a test pins it)


def native_fault(images, directions, fit=None):
    """The native-language rule, held by BOTH runtimes' direction gates: a deck with NO pictures offers at least one
    native visual language (drawn, no pictures needed) — the one that fits the topic — and records why in
    direction_gate.native_fit (the user's decision, 2026-10-05: an optional offer is never made). Returns the
    fault, or None."""
    if str(images or "").strip().lower() != "none":
        return None
    offered = [d.get("vl") for d in (directions or []) if isinstance(d, dict) and d.get("vl") in NATIVE_LANGS]
    if not offered:
        return ("the deck has no pictures and no direction is a native visual language — offer the one that fits the "
                "topic with visual_languages.direction('<name>'): ink (culture, history, craft), poster (launch, "
                "manifesto, brand, opinion), cutpaper (children, teaching, workshop, community) or blueprint "
                "(research, engineering, technical) — references/visual-languages.md")
    if not isinstance(fit, dict) or fit.get("language") not in offered or len(str(fit.get("why") or "").strip()) < 8:
        return ('record direction_gate.native_fit: {"language": "<the native language offered>", "why": "<why it '
                'fits this topic>"} — offered: ' + ", ".join(offered))
    return None
```

- [ ] **Step 4: Wire both gates** — in `render_deck._direction_gate`, after the `_imgf` block:

```python
    _natf = directions_diversity.native_fault(dg.get("images"), cands, dg.get("native_fit"))
    if _natf:
        faults.append(_natf)
```

and in `codex_delivery_gate.py`, after the `_imgf` lines:

```python
                _natf = _dd.native_fault(_dg.get("images"), _c, _dg.get("native_fit"))   # same rule as render_deck.py
                if _natf:
                    _f.append(_natf)
```

Then the two record templates, so an agent filling them meets the field (the templates' placeholders are
REJECTED by `deck_gates.check`, so `native_fit` is named inside the existing `images` placeholder rather than added as
a new placeholder field a photo deck would be forced to fill). In `scripts/deck_gates.py`:

```python
                               "images": "<photos | illustrations | none — the pictures this deck will carry: the user's, generated or fetched; with none, also add native_fit: {language, why}>"},
```

and in `scripts/codex_delivery_gate.py`:

```python
                           "images": "<photos | illustrations | none: the user's, generated or fetched; with none, also native_fit: {language, why}>"},
```

Add `skills/slide-maker/scripts/deck_gates.py` to this task's commit.

- [ ] **Step 5: Docs** — add (never rewrite) one sentence after the visual-language bullet in `SKILL.md`:

```markdown
  A deck with NO pictures offers one of the four NATIVE visual languages (`ink` · `poster` · `cutpaper` ·
  `blueprint`, drawn, no pictures needed) — the one that fits the topic — and records why in
  `direction_gate.native_fit` (both gates hold it; `references/visual-languages.md`).
```

In `references/interview-protocol.md`, after the "A curated visual language." bullet:

```markdown
       - **A native visual language when the deck has no pictures.** When `direction_gate.images` is `none`, at
         least one offered direction is a NATIVE language — `ink` (culture, history, craft), `poster` (launch,
         manifesto, brand, opinion), `cutpaper` (children, teaching, workshop, community) or `blueprint` (research,
         engineering, technical) — and the record states the pick and its reason:
         `direction_gate.native_fit: {"language": "<name>", "why": "<topic reason>"}`. The guidance is an offer,
         not a rule; the record is the rule. Both runtimes hold it; a named `waived` is the escape.
```

In `references/codex-runtime.md`, after the paragraph on `images`:

```markdown
   With `images: none`, at least ONE candidate is a native language (`visual_languages.direction("ink" | "poster"
   | "cutpaper" | "blueprint")`) and the record carries `"native_fit": {"language": "<name>", "why": "<topic
   reason>"}`; `codex_delivery_gate.py` holds a set without it.
```

- [ ] **Step 6: Run — expect pass; then the fixtures**

Run: `cd skills/slide-maker && python3 tests/test_direction_vl_rule.py | tail -1`
Expected: `[test_direction_vl_rule] ok`.
Then run every test that builds a gate record with `"images": "none"` (`grep -ln '"images": "none"' tests/*.py`); a fixture that now fails because it offers no native language gets one added with a `native_fit` — record each as a `Ruling:` in the ledger.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/scripts/render_deck.py skills/slide-maker/scripts/codex_delivery_gate.py skills/slide-maker/scripts/deck_gates.py skills/slide-maker/SKILL.md skills/slide-maker/references/interview-protocol.md skills/slide-maker/references/codex-runtime.md skills/slide-maker/tests/test_direction_vl_rule.py
git commit -m "direction gate: a deck with no pictures offers a native visual language and records why (both runtimes)"
```

---

### Task 10: Reference, examples, inventory, changelog

**Files:**
- Modify: `skills/slide-maker/references/visual-languages.md`, `scripts/sigs.py` (`EXAMPLES` + guarantees), `references/file-inventory.md` (`vl_native.py`), `CHANGELOG.md`, `README.md` + `README_CN.md` (the visual-language section gains the four native samples)

- [ ] **Step 1: `references/visual-languages.md`** — change the title line to "eight complete looks", add the four rows to the language table, a "Native languages" section, and the grounds rows:

```markdown
| `ink` | none needed (an ink illustration is optional) | serif; vertical CJK, carved seal | xuan paper, misty ink ridges | ensō around the figure |
| `poster` | none needed (a cut-out object is optional) | Impact display, the headline is the picture | one saturated field per page | page-clipped colour blocks |
| `cutpaper` | none needed | rounded friendly sans | a layered paper diorama, soft paper shadows | title card tucked between hills |
| `blueprint` | none needed | Georgia titles, Courier New labels | drafting grid, drawing sheet, title block | iso stack, leaders, dimension line |

## Native languages (drawn — no pictures needed)

`ink`, `poster`, `cutpaper` and `blueprint` draw their own surface with native, editable shapes (`native_art.py`),
so they work for a deck with no pictures and no image tool. Everything they draw stays on the page, and every value
they write is one PowerPoint opens without repair (`ooxml_safety.py`, held by `lint_deck`).

- **`points`** — `k.points(s, kicker=…, title=…, items=[("Head", "line"), …])`, 2 to 4 points (a string, a
  `(head, line)` pair or a `{"head", "line"}` dict each). Native languages only; on the image-led four, build the
  list on an ordinary `k.new_slide()` page.
- **Words only you can give** (never invented; absent → nothing drawn): `seal="茶事"` on `ink` (one or two
  characters of your own text), `highlight="room"` on `poster` (words of the title, quote or closing),
  `icons=["lucide:wind", …]` on `cutpaper`'s `points` (one per point), `project="…"` on `blueprint` (else the
  cover title is remembered for every sheet's title block).
- **Vertical CJK** — `ink` sets a title, a quote couplet, a label and its points vertically ONLY when the text is
  Chinese or Japanese with no Latin letters or digits; Latin, Hangul or mixed text is set horizontally in the same
  composition.
- **Ordinary pages** — `k.new_slide()` gives `poster` its colour field (read `k.color("ink")` for text — the field
  changes per page) and `blueprint` its numbered drawing sheet.
- **When they are offered** — a deck with no pictures (`direction_gate.images: none`) offers the one that fits
  the topic and records `direction_gate.native_fit: {"language", "why"}` (both gates hold it).
```

Grounds table rows:

```markdown
| ink | xuan paper | `night` — ink-black paper, pale ridges, a moon |
| poster | colour fields (cobalt, lime, black, orange) | `paper` — off-white fields, black type, cobalt |
| cutpaper | day | `night` — navy sky, moon, dark hills |
| blueprint | vellum | `cyanotype` — navy, pale linework |
```

Run: `cd skills/slide-maker && python3 tests/test_visual_languages.py | tail -1` — its reference check requires every language, page and ground name. Expected: `] ok`.

- [ ] **Step 2: `sigs.py` examples** — add to `EXAMPLES` (each runs in the smoke suite with `dk`, `s`, `prs` in scope):

```python
    "points": 'import visual_languages as vl\n'
              'k = vl.use("ink", prs)\n'
              'k.points(k.new_slide(), title="三道工序",\n'
              '         items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")], seal="序")\n',
    "ink_ridges": 'import native_art as na\n'
                  'na.ink_ridges(s, color="1D1C1A", layers=na.INK_LAYERS["land"], keep_clear=[(7.0, 0.5, 1.0, 3.0)])\n',
    "clipped_block": 'import native_art as na\n'
                     'na.clipped_block(s, 7.0, 3.0, 4.0, 4.0, -9, fill="D7FF3B")   # a rotated block, cut to the page\n',
```

and their guarantees: `"points": "2 to 4 points, measured, refused rather than truncated; vertical only for CJK"`, `"ink_ridges": "ridges fade into mist and never pass the page; text in keep_clear is never covered"`, `"clipped_block": "drawn as its polygon cut to the page, so PowerPoint shows nothing past the slide edge"`.

- [ ] **Step 3: Inventory** — `vl_native.py` entry next to `visual_languages.py`:

```markdown
- `vl_native.py` — page compositions of the native visual languages (`ink`, `poster`, `cutpaper`, `blueprint`):
  plans the text first (measured, refused past each field's floor), draws the art with the text kept clear, then
  sets the text; the points page; vertical CJK for `ink`; poster's colour field and blueprint's drawing sheet on
  every `new_slide()`.
```

- [ ] **Step 4: CHANGELOG `[Unreleased]`** (English only):

```markdown
### Four native visual languages — no pictures needed

`ink` (misty ink ridges, vertical CJK, a carved seal, an ensō around the figure), `poster` (the headline is the
picture, one saturated field per page), `cutpaper` (a layered paper diorama, the title card tucked between hills)
and `blueprint` (a numbered drawing sheet, one iso layer per point, a dimensioned figure) join the four image-led
languages. They draw their surface with native, editable shapes, so a deck with no pictures and no image tool gets
a finished look; each has a light and a contrast ground and a new `points` page. Words the kit cannot invent —
a seal's characters, a highlighted word, icons, a project name — come only from the caller. A deck with no pictures
now offers the native language that fits its topic and records why (`direction_gate.native_fit`, both runtimes).

### PowerPoint safety

`lint_deck` now reads the saved file for values PowerPoint repairs or deletes but LibreOffice renders — angles out
of range, negative shadow distances, alphas and gradient stops out of range, `spPr`/`rPr` children out of schema
order, duplicate shape ids (CRITICAL) — and reports shapes past the slide edge, which PowerPoint shows while
editing (advisory; quiet for a declared bleed). Found when a look-dev deck rendered cleanly and PowerPoint repaired it.
```

- [ ] **Step 5: README (EN + CN)** — in the visual-language section, add a second table with the four native samples (`skills/slide-maker/assets/vl/samples/{ink,poster,cutpaper,blueprint}.jpg`, contrast grounds linked), a one-line caption each, and the sentence "Drawn, no pictures needed — offered when your deck has none." (CN: "原生绘制，不需要图片——deck 没有图片时会推荐。"). Each paragraph on one line (no hard wraps in Chinese).

- [ ] **Step 6: Run the doc and inventory checks**

Run: `cd skills/slide-maker && python3 scripts/check_inventory.py && python3 scripts/check_tests_wired.py && cd ../.. && python3 scripts/check_doc_commands.py && python3 skills/slide-maker/scripts/check_skill_lossless.py --baseline "origin/main:skills/slide-maker/SKILL.md" --allow skills/slide-maker/.skill-lossless-allow.json --report /tmp/skill-lost.md`
Expected: all clean; `LOSSLESS` (SKILL.md only gained lines).

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/references/visual-languages.md skills/slide-maker/scripts/sigs.py skills/slide-maker/references/file-inventory.md CHANGELOG.md README.md README_CN.md
git commit -m "docs: the four native visual languages, points, examples, inventory and changelog"
```

---

### Task 11: Verification, independent review, push

- [ ] **Step 1: Full suite on macOS** — every `tests/test_*.py`, sequentially; expected `failed=0`.
- [ ] **Step 2: Every CI step** — `python3 <scratchpad>/cisteps.py <repo> <logdir>`; expected `ran N, failed 0`.
- [ ] **Step 3: Linux font simulation** — `zsh <scratchpad>/cisim/all.sh <repo> <out>`; any failure must also fail identically on `origin/main` (simulation artefact) or it is fixed.
- [ ] **Step 4: Look** — render all eight new samples and one CJK + one Latin deck per native language on a portrait canvas; read every PNG; record a one-line verdict per page in the ledger.
- [ ] **Step 5: PowerPoint check** — `ooxml_safety.xml_findings` and `beyond_page` on every sample: zero.
- [ ] **Step 6: Non-Claude usability** — dispatch a subagent restricted to `SKILL.md`, `references/visual-languages.md`, `references/codex-runtime.md` and `python3 scripts/sigs.py` output (no source) to build one deck per native language; fix every friction it reports.
- [ ] **Step 7: Final whole-branch review** — a fresh reviewer (sonnet, per the user's standing preference) over `git diff origin/main...HEAD`; Critical/Important fixed with a failing test first; Minors ledgered.
- [ ] **Step 8: Merge and push** — fast-forward `main` to the branch, `git log origin/main..HEAD` read as its own step (only this work's commits), push, watch CI to `conclusion: success` (re-run once if the job was cancelled by the 15-minute install timeout), rsync the installed copy (`~/.agents/skills/slide-maker`, checksum dry run first).
