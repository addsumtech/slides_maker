# Five more native visual languages (P4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Five more visual languages that need no pictures: `starlit` (星夜), `broadsheet` (报纸头版), `journal` (学术期刊), `tally` (数据账本) and `chalkboard` (黑板报). Each turns the caller's words into a finished deck on every canvas and in every script, and is offered by the direction gate when it fits the topic.

**Architecture:**
- The five languages are added to `LANGS` / `VARIANTS` / `TYPE` / `NATIVE` in `scripts/visual_languages.py`. As a result, `use()`, grounds, `direction()`, samples, the language gate and `rs.ground` / `rs.card` all work with no extra wiring.
- Their seven page compositions live in a new `scripts/vl_native2.py`. It registers into `vl_native`'s `COMPOSERS` / `GROUNDS` and is imported from the foot of `vl_native.py`, so any import of `vl_native` registers them.
- New drawn motifs go into `scripts/native_art.py`.
- Text is planned with the kit's measured `_flow`, exactly as in P3.

**Tech Stack:** Python 3.9+, python-pptx, lxml, Pillow; LibreOffice for renders. Tests are plain scripts: they use `check()` and end with a final `N passed, 0 failed` line, and each one is a step in `.github/workflows/ci.yml`.

**Spec:** `docs/superpowers/specs/2026-10-08-five-native-languages-design.md`

**Look-dev reference (approved look, throwaway):**
- Script: `/private/tmp/claude-501/-Users-donghanglyu/2866adfa-b4b0-4b62-8845-b0d5410c5fde/scratchpad/lookdev3/lookdev3.py`
- Renders: `~/Desktop/slide-maker 新模板样张/`
- Its palettes and proportions are the target. Its copy is sample copy and never becomes kit text (spec §6).

**Prior art to read before Task 4:**
- `scripts/vl_native.py`: `register`, `alt`, `ctx`, `flow`, `display`, `compose`, and the cutpaper and drafting sections. P4 compositions follow the same plan → art → draw order.
- `docs/superpowers/plans/2026-10-05-native-visual-languages.md`, Tasks 3–7.

## Global Constraints

- **Page and file safety.**
  - Nothing is drawn past the slide edge: every shape lies inside `[0, W] × [0, H]` (`ooxml_safety.beyond_page` stays `[]`).
  - Every OOXML angle is in `0..21599999`; alphas and gradient positions are in `0..100000` (`ooxml_safety.xml_findings` stays `[]`).
  - A replaced slide background drops the picture it held: no orphan image relationships.
- **Fonts and type.**
  - System fonts only. `fonts="both"` uses faces present on macOS AND Windows; the Windows column is unverified here.
  - Figures are never set in Georgia. `Kit.runs` already splits digits into a lining face; numerals use Times New Roman, Arial Black or Trebuchet MS.
  - Every text ink is ≥ 4.5:1 on the ground, panel, chip or box it sits on, on every ground.
- **Words and meaning.**
  - The kit never invents words. These extras come from the caller, and when absent nothing is drawn: `masthead=`, `edition=`, `inside=`, `tags=`, `running=`, `authors=`, `abstract=`, `margin=`, `total=`, `doodle=`, `ordered=`.
  - Derived structure (page numbers, figure numbers, the ■ end mark, localised structural labels) is computed, never typed in.
  - A figure that implies structure is drawn only from content: one star per point, one ledger row per point, one chalk box per point. Chalk arrows appear only with `ordered=True`.
- **Things that must not change.**
  - The nine existing languages behave exactly as before. Their bundled sample fingerprints (`assets/vl/samples/manifest.json`) still match a rebuild, which `tests/test_visual_languages.py` checks on macOS.
  - A deck that picks none of the five imports nothing new. `vl_native2` is loaded only through `vl_native`, which only native decks import.
- **Delivery.**
  - Bundled samples are JPG and ≤ 350 KB. SkillHub filters PNG, and that applies to bundled figures too.
  - Every new test script is wired into `ci.yml` (`check_tests_wired.py`); every new script is listed in `references/file-inventory.md` (`check_inventory.py`).
  - Stage named paths only. Never push before the full suite, the CI-steps run and the font simulation are green, and only when the user says so.

## Review Focus

1. **A long CJK masthead or running head on a 4:3 or square canvas.** It fits, or the kit falls back (the remembered cover title gives way to page number only), or an explicit value is refused with `VLTextOverflow`. It never overlaps the headline under it. *(Task 5 + Task 6 tests.)*
2. **An ORDINARY page in each new language** (`k.new_slide()` then `rs.ground(s, k.name)` then `rs.card`). It carries the language's surface (sky, strip, running head, grid, frame), and the content rect `rs.ground` returns does not overlap that surface. *(One test per language task.)*
3. **Japanese and Korean decks see their own structural labels.** A Korean abstract is labelled 초록, not "Abstract". A Japanese figure reads 図 1. Labels follow the page's own words. *(Task 3 helper test + Task 6 test.)*
4. **Four long points on a square canvas.** Every point layout (constellation, columns, ledger rows, chalk boxes) tries its alternative before refusing. No art line (constellation segment, chalk arrow, column rule) crosses a text box. *(The generality corpus + a geometry test in Tasks 4, 5 and 8.)*
5. **`tally.data(total=…)` with formatted numbers** (`"1,250"`, `"98.6%"`, `"$4.2M"`). A plain or percent number draws the right share. Anything else is refused by name, and the bar never shows the wrong fraction. *(Task 7 test.)*

---

### Task 1: `register()` refuses a name another file already registered

**Files:**
- Modify: `skills/slide-maker/scripts/register_surface.py` (`register()`, after the preset check, ~line 920)
- Test: `skills/slide-maker/tests/test_register_surface.py` (append before the summary block)

**Interfaces:**
- Produces: `register_surface.register(name, *, ground, card=None, forbids=(), source=None)` raises `ValueError` when `name` is already in `BESPOKE` with a different `source`. Re-registering from the same `source` still works (module reloads; `load_kits` re-reading a deck's own kit).

- [ ] **Step 1: Write the failing test** — append to `tests/test_register_surface.py` immediately before `for line in ok:`:

```python
# a name another FILE registered is refused, not silently replaced (spec P4 §Naming: `ledger` is a bespoke kit, and
# registering a language under it would have overwritten the kit for every deck)
import bespoke_kits as _bk2                                          # noqa: E402
_src = rs.BESPOKE["ledger"]["source"]
try:
    rs.register("ledger", ground=lambda sl, r, i: (1, 1, 2, 2), source="/somewhere/else.py")
    bad.append("a kit registered from another file replaced the bespoke `ledger` kit")
except ValueError as exc:
    check("ledger" in str(exc) and "already" in str(exc),
          "registering a name another file already registered is REFUSED, naming it: {}".format(str(exc)[:90]))
check(rs.BESPOKE["ledger"]["source"] == _src, "...and the original kit is untouched")
_g = rs.GROUNDS["ledger"]
rs.register("ledger", ground=_g, card=rs.CARDS["ledger"], forbids=rs.BESPOKE["ledger"]["forbids"], source=_src)
check(rs.GROUNDS["ledger"] is _g, "re-registering from the SAME file still works (a reload, load_kits)")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_register_surface.py | tail -5`
Expected: `FAIL a kit registered from another file replaced the bespoke `ledger` kit` and a non-zero failed count.

- [ ] **Step 3: Implement.** In `register()`, directly after the `if key in _p.PRESETS:` block, add:

```python
    prior = BESPOKE.get(key)
    if prior is not None and str(prior.get("source") or "") != str(source or ""):
        raise ValueError(
            "{!r} is already registered by {} — registering it again from {} would silently replace that kit for "
            "every deck that asks for it. Pick another name.".format(
                name, prior.get("source") or "an unnamed source", source or "an unnamed source"))
```

- [ ] **Step 4: Run it to verify it passes**

Run: `cd skills/slide-maker && python3 tests/test_register_surface.py | tail -2 && python3 tests/test_bespoke_kits.py | tail -1 && python3 tests/test_visual_languages.py | tail -1`
Expected: `N passed, 0 failed` for all three. Visual languages register once each, from one file, so they are unaffected.

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/register_surface.py skills/slide-maker/tests/test_register_surface.py
git commit -m "register_surface: refuse a name another file already registered, instead of replacing its kit"
```

---

### Task 2: Native art for the five languages (`native_art.py`)

**Files:**
- Modify: `skills/slide-maker/scripts/native_art.py`: change `_bg` (drop the old background's picture) and the module docstring (it no longer says "four"); add the new primitives at the end of the file
- Test: `skills/slide-maker/tests/test_native_art.py` (append before the summary block)

**Interfaces:**
- Produces (all page-safe, deterministic for their seed, decorative marks declared with `dk.decorative`):
  - `starfield_png(slide, *, base, ink, glow, seed=0, keep_clear=(), density=1.0, dpi=200) -> str`: sets the slide background to a cached sky PNG and returns its path
  - `radial_glow(slide, cx, cy, d, color, *, alpha=0.42) -> shape`: a rim-free radial fade, clear by 68%
  - `horizon_glow(slide, top, color, deep, *, alpha=0.45) -> shape`
  - `crescent(slide, cx, cy, d, color, ground) -> (shape, shape)`
  - `ring(slide, cx, cy, d, color, *, w=1.0) -> shape`
  - `polyline(slide, pts, color, *, w=1.0, alpha=None) -> shape`: open, every point clamped to the page
  - `chalk_path(slide, pts, color, *, w=2.2, seed=0, passes=2) -> [shape]`
  - `chalk_box(slide, x, y, w, h, color, *, seed=0) -> [shape]`
  - `chalk_ellipse(slide, cx, cy, rx, ry, color, *, seed=0, turns=1.08) -> [shape]`
  - `chalk_underline(slide, x, y, w, color, *, seed=0) -> [shape]`
  - `chalk_arrow(slide, x0, y0, x1, y1, color, *, seed=0) -> [shape]`
  - `board_frame(slide, wood, chalk) -> (x, y, w, h)`: the inner rect
  - `chip_width(text, size, face, *, bold=True) -> float`
  - `chip(slide, x, y, text, *, size, fill, ink, face, ea_face=None, bold=True) -> (x, y, w, h)`
  - `share_bar(slide, x, y, w, frac, *, track, fill, h=0.16) -> None`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_native_art.py` before `for line in ok:`:

```python
# ── P4: the five new languages' motifs ──
import zipfile, re as _re
from PIL import Image
def p4_page(W, H, seed):
    prs = dk.blank_deck(W, H)
    s = dk.add_slide(prs)
    na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=seed, keep_clear=[(1.0, 1.0, 3.0, 1.0)])
    na.radial_glow(s, W * 0.5, H * 0.4, min(W, H) * 0.5, "F1D9A6")
    na.radial_glow(s, 0.1, 0.1, 3.0, "F1D9A6")                       # near a corner: shrinks to stay whole
    na.horizon_glow(s, H * 0.84, "F1D9A6", "D9B36C")
    na.crescent(s, W - 0.2, 0.2, 0.9, "D9B36C", "0B1430")           # asked for off the corner: moved on
    na.ring(s, W * 0.3, H * 0.5, 1.4, "D9B36C")
    na.polyline(s, [(-1, 1), (W + 1, 2), (W * 0.5, H + 1)], "F3F1EA", w=1.5)
    na.chalk_box(s, 0.5, 0.5, 3.0, 1.6, "F2D16B", seed=seed)
    na.chalk_ellipse(s, W * 0.7, H * 0.5, 1.0, 0.8, "F2A9B8", seed=seed)
    na.chalk_underline(s, 0.5, H * 0.8, 3.0, "F2D16B", seed=seed)
    na.chalk_arrow(s, 4.0, 2.0, 5.0, 2.0, "F3F1EA", seed=seed)
    inner = na.board_frame(s, "7A4F2A", "E8E2D2")
    r1 = na.chip(s, 1.0, 3.0, "MEMBERS", size=12, fill="C6F432", ink="0E0E10", face="Arial")
    r2 = na.chip(s, 1.0, 3.6, "会员", size=12, fill="C6F432", ink="0E0E10", face="Arial", ea_face="Hiragino Sans GB")
    na.share_bar(s, 0.5, H - 1.0, W - 1.0, 0.3, track="E7EAF1", fill="2438F0")
    p = td / "p4_{}x{}_{}.pptx".format(W, H, seed)
    prs.save(str(p))
    return p, prs, s, inner, (r1, r2)

for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333), (7.5, 7.5)):
    p, prs, s, inner, chips = p4_page(W, H, 3)
    check(ox.xml_findings(str(p)) == [], "P4 art {}x{}: PowerPoint-safe: {}".format(W, H, ox.xml_findings(str(p))[:2]))
    check(ox.beyond_page(prs) == [], "P4 art {}x{}: nothing past the page: {}".format(W, H, ox.beyond_page(prs)[:2]))
    check(0 < inner[0] < 0.5 and inner[0] + inner[2] < W and inner[1] + inner[3] < H,
          "P4 art {}x{}: board_frame returns the rect inside its frame {}".format(W, H, inner))
# the glow is clear by 68% of its path: with path="circle" the 100% stop is the bbox CORNER (a rim showed at ~71%)
_p, _prs, _s, _i, _c = p4_page(13.333, 7.5, 3)
gls = [g for sh in _s.shapes for g in sh._element.iter("{%s}gradFill" % na.A_NS) if g.find("{%s}path" % na.A_NS) is not None]
check(gls, "radial glows are radial gradients")
for g in gls:
    stops = {int(gs.get("pos")): int(gs.find(".//{%s}alpha" % na.A_NS).get("val")) for gs in g.iter("{%s}gs" % na.A_NS)}
    check(all(a == 0 for pos, a in stops.items() if pos >= 68000), "a glow is clear from 68% outwards: {}".format(stops))
# the sky is one background PICTURE, deterministic, and clear where words go
pa = na.starfield_png(dk.add_slide(dk.blank_deck(13.333, 7.5)), base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=5,
                      keep_clear=[(2.0, 2.0, 4.0, 2.0)])
pb = na.starfield_png(dk.add_slide(dk.blank_deck(13.333, 7.5)), base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=5,
                      keep_clear=[(2.0, 2.0, 4.0, 2.0)])
check(pa == pb and Path(pa).read_bytes() == Path(pb).read_bytes(), "the same sky is the same picture (cached, deterministic)")
im = Image.open(pa).convert("RGB")
dpi = im.size[0] / 13.333
inside = {im.getpixel((int(x * dpi), int(y * dpi))) for x in (2.2, 3.5, 5.8) for y in (2.2, 3.0, 3.8)}
check(inside == {(0x0B, 0x14, 0x30)}, "no star inside the keep-clear rect: {}".format(inside))
# repainting the background drops the old picture (a starlit page is painted at new_slide, then with its words clear)
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=1)
na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=1, keep_clear=[(1, 1, 2, 2)])
imgs = [r for r in s.part.rels.values() if r.reltype.endswith("/image")]
check(len(imgs) == 1, "a repainted sky leaves one picture on the slide, not an orphan ({})".format(len(imgs)))
na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=1, keep_clear=[(1, 1, 2, 2)])
imgs = [r for r in s.part.rels.values() if r.reltype.endswith("/image")]
check(len(imgs) == 1 and s._element.find(".//" + "{%s}blip" % na.A_NS) is not None,
      "repainting with the SAME picture keeps it (the old and new share one relationship)")
# chips are as wide as their words, one line, and a CJK chip is at least an em a character
w_en, w_long = na.chip_width("TAGS", 12, "Arial"), na.chip_width("TAGS AND MORE TAGS", 12, "Arial")
check(w_long > w_en > 0.4, "a chip grows with its words ({:.2f} < {:.2f})".format(w_en, w_long))
check(na.chip_width("会员资格", 12, "Arial") >= 4 * 12 / 72.0, "a CJK chip is at least an em per character")
_tbs = [sh for sh in _s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text in ("MEMBERS", "会员")]
check(len(_tbs) == 2 and all(t.text_frame.word_wrap is False for t in _tbs), "chip text never wraps")
# the share bar draws its fraction of the track, clamped
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
na.share_bar(s, 1.0, 6.0, 10.0, 0.3, track="E7EAF1", fill="2438F0")
na.share_bar(s, 1.0, 6.5, 10.0, 1.7, track="E7EAF1", fill="2438F0")
ws = sorted(round(sh.width / 914400.0, 2) for sh in s.shapes)
check(ws == [3.0, 10.0, 10.0, 10.0], "share bars: 30% of the track, and a fraction over 1 clamps to the track ({})".format(ws))
# chalk is deterministic for a seed
def chalk_xml(seed):
    prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
    na.chalk_box(s, 1, 1, 3, 2, "F2D16B", seed=seed)
    return "".join(sh._element.xml for sh in s.shapes)
check(chalk_xml(4) == chalk_xml(4) and chalk_xml(4) != chalk_xml(5), "chalk strokes are deterministic for a seed")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_art.py | tail -3`
Expected: `AttributeError: module 'native_art' has no attribute 'starfield_png'`.

- [ ] **Step 3: Implement.**

(a) Replace `_bg` in `native_art.py` with:

```python
def _bg(slide, fill_xml):
    """Set the slide background. A picture the OLD background held is dropped with it, unless the new one uses the
    same relationship: a starlit page is painted at new_slide and again once its words are known, and the first sky
    would otherwise ride along as an orphan picture."""
    import re as _re
    csld = slide._element.find(qn("p:cSld"))
    keep = set(_re.findall(r'r:embed="([^"]+)"', fill_xml))
    stale = set()
    for old in csld.findall(qn("p:bg")):
        stale |= {b.get(qn("r:embed")) for b in old.iter(qn("a:blip"))} - keep - {None}
        csld.remove(old)
    csld.insert(0, etree.fromstring('<p:bg xmlns:p="{p}" xmlns:a="{a}" xmlns:r="{r}"><p:bgPr>{f}<a:effectLst/>'
                                    '</p:bgPr></p:bg>'.format(p=P_NS, a=A_NS, r=R_NS, f=fill_xml)))
    for rid in stale:
        if not slide._element.xpath('.//*[@r:embed="{}"]'.format(rid)):
            slide.part.drop_rel(rid)
```

(b) In the module docstring, change "the drawn surfaces of the four NATIVE visual languages (ink, poster, cutpaper, blueprint)" to "the drawn surfaces of the NATIVE visual languages (ink, poster, cutpaper, drafting, starlit, broadsheet, journal, tally, chalkboard)".

(c) Append to the end of `native_art.py`:

```python
# ═══════════════════ P4: starlit · broadsheet · journal · tally · chalkboard ═══════════════════
def _rgb3(h):
    h = hexstr(h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def starfield_png(slide, *, base, ink, glow, seed=0, keep_clear=(), density=1.0, dpi=200):
    """A night sky as the slide BACKGROUND: small stars and six four-point sparkles, deterministic for `seed`, none
    within 0.12in of a `keep_clear` rect (inches). One picture, cached by its inputs, never ~150 shapes: the deck's
    size and every lint pass grow with the shape count. Returns the PNG's path."""
    import hashlib
    from PIL import Image, ImageDraw
    W, H = page_size(slide)
    sig = repr((hexstr(base), hexstr(ink), hexstr(glow), seed, round(W, 3), round(H, 3),
                [tuple(round(float(v), 2) for v in r) for r in keep_clear], round(float(density), 3), dpi))
    path = Path(tempfile.gettempdir()) / "slide-maker-native-art" / "sky_{}.png".format(
        hashlib.sha1(sig.encode("utf-8")).hexdigest()[:16])
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        rnd = random.Random(seed)
        b, kc, gc = _rgb3(base), _rgb3(ink), _rgb3(glow)
        mix = lambda c, a: tuple(int(round(b[i] * (1 - a) + c[i] * a)) for i in range(3))   # noqa: E731
        im = Image.new("RGB", (int(W * dpi), int(H * dpi)), b)
        dr = ImageDraw.Draw(im)

        def clear(x, y, m=0.0):
            return not any(kx - 0.12 - m <= x <= kx + kw + 0.12 + m and ky - 0.12 - m <= y <= ky + kh + 0.12 + m
                           for kx, ky, kw, kh in keep_clear)
        for _ in range(int(140 * float(density) * (W * H) / (13.333 * 7.5))):
            x, y = rnd.uniform(0.05, W - 0.05), rnd.uniform(0.05, H - 0.05)      # every draw consumed: the sky
            d = rnd.choice((0.018, 0.022, 0.026, 0.03, 0.04)) if rnd.random() < 0.85 else rnd.uniform(0.05, 0.07)
            c = mix(kc if rnd.random() < 0.8 else gc, rnd.uniform(0.35, 0.95))   # is the same whatever is kept clear
            if clear(x, y):
                r = d * dpi / 2.0
                dr.ellipse([x * dpi - r, y * dpi - r, x * dpi + r, y * dpi + r], fill=c)
        lw = max(1, int(round(dpi / 120.0)))
        for _ in range(6):
            x, y, L = rnd.uniform(0.3, W - 0.3), rnd.uniform(0.3, H * 0.6), rnd.uniform(0.12, 0.2)
            if clear(x, y, L):
                c = mix(gc, 0.8)
                dr.line([((x - L) * dpi, y * dpi), ((x + L) * dpi, y * dpi)], fill=c, width=lw)
                dr.line([(x * dpi, (y - L) * dpi), (x * dpi, (y + L) * dpi)], fill=c, width=lw)
                r = 0.03 * dpi
                dr.ellipse([x * dpi - r, y * dpi - r, x * dpi + r, y * dpi + r], fill=mix(gc, 0.9))
        im.save(str(path), optimize=True)
    _part, rid = slide.part.get_or_add_image_part(str(path))
    _bg(slide, '<a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{}"/><a:srcRect/><a:stretch><a:fillRect/>'
               '</a:stretch></a:blipFill>'.format(rid))
    return str(path)


def _radial(shape, color, alpha):
    """Swap a solid fill for a radial fade: `alpha` at the centre, clear by 68% of the path. path="circle" puts the
    100% stop at the bounding box's CORNER, not the disc's edge — a fade ending at 100% left a rim at ~71%
    (look-dev render, 2026-10-08)."""
    sp = shape._element.spPr
    sf = sp.find(qn("a:solidFill"))
    sf.addprevious(etree.fromstring(
        '<a:gradFill xmlns:a="{a}" rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:srgbClr val="{c}"><a:alpha val="{a0}"/></a:srgbClr></a:gs>'
        '<a:gs pos="34000"><a:srgbClr val="{c}"><a:alpha val="{a1}"/></a:srgbClr></a:gs>'
        '<a:gs pos="68000"><a:srgbClr val="{c}"><a:alpha val="0"/></a:srgbClr></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="{c}"><a:alpha val="0"/></a:srgbClr></a:gs></a:gsLst>'
        '<a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path></a:gradFill>'.format(
            a=A_NS, c=hexstr(color), a0=_pct(alpha), a1=_pct(alpha * 0.45))))
    sp.remove(sf)
    return shape


def radial_glow(slide, cx, cy, d, color, *, alpha=0.42):
    """A soft glow behind a figure or a star, shrunk until it is whole on the page."""
    W, H = page_size(slide)
    d = max(0.05, min(d, 2 * cx, 2 * (W - cx), 2 * cy, 2 * (H - cy)))
    sh = _radial(disc(slide, cx, cy, d, color), color, alpha)
    dk.decorative(sh, "a soft glow behind a figure; the words beside it carry the meaning")
    return sh


def horizon_glow(slide, top, color, deep, *, alpha=0.45):
    """A warm horizon at the foot of the page: clear at `top`, `alpha` of `deep` at the page's bottom edge."""
    W, H = page_size(slide)
    top = min(max(float(top), 0.0), H - 0.05)
    b = dk.box(slide, 0, top, W, H - top, fill=hexstr(color))
    sp = b._element.spPr
    sf = sp.find(qn("a:solidFill"))
    sf.addprevious(etree.fromstring(
        '<a:gradFill xmlns:a="{a}" rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:srgbClr val="{c}"><a:alpha val="0"/></a:srgbClr></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="{d}"><a:alpha val="{al}"/></a:srgbClr></a:gs></a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/></a:gradFill>'.format(a=A_NS, c=hexstr(color), d=hexstr(deep), al=_pct(alpha))))
    sp.remove(sf)
    dk.decorative(b, "the warm horizon at the foot of a night page")
    return b


def crescent(slide, cx, cy, d, color, ground):
    """A crescent moon: a disc of `color` cut by a disc of the ground, offset up and right — moved so both discs are
    whole on the page."""
    W, H = page_size(slide)
    cx = min(max(cx, 0.5 * d + 0.05), W - 0.71 * d - 0.05)
    cy = min(max(cy, 0.60 * d + 0.05), H - 0.5 * d - 0.05)
    a = disc(slide, cx, cy, d, color)
    b = disc(slide, cx + 0.24 * d, cy - 0.13 * d, 0.94 * d, ground)
    for sh in (a, b):
        dk.decorative(sh, "the crescent moon of the night sky; nothing reads from it")
    return a, b


def ring(slide, cx, cy, d, color, *, w=1.0):
    """A thin circle outline (a round window's rim)."""
    b = dk.box(slide, cx - d / 2.0, cy - d / 2.0, d, d, fill=None, line=dk._as_rgb(hexstr(color)), line_w=w)
    b._element.spPr.find(qn("a:prstGeom")).set("prst", "ellipse")
    dk.decorative(b, "the rim of a round picture window")
    return b


def polyline(slide, pts, color, *, w=1.0, alpha=None):
    """An OPEN polyline as one editable shape, every point clamped onto the page."""
    W, H = page_size(slide)
    pts = [(min(max(float(x), 0.0), W), min(max(float(y), 0.0), H)) for x, y in pts]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    bw, bh = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
    u = [((px - x0) / bw * U, (py - y0) / bh * U) for px, py in pts]
    d = "<a:moveTo>{}</a:moveTo>".format(orn._pt(*u[0])) + "".join("<a:lnTo>{}</a:lnTo>".format(orn._pt(*q)) for q in u[1:])
    sh = _custom(slide, x0, y0, bw, bh, '<a:path w="{u}" h="{u}" fill="none">{d}</a:path>'.format(u=U, d=d),
                 line=hexstr(color), line_w=w)
    if alpha is not None:
        clr = sh._element.spPr.find(qn("a:ln")).find(qn("a:solidFill"))[0]
        clr.append(clr.makeelement(qn("a:alpha"), {"val": str(_pct(alpha))}))
    return sh


def chalk_path(slide, pts, color, *, w=2.2, seed=0, passes=2):
    """A chalk stroke: `passes` jittered copies of the polyline, the second thinner and fainter (chalk dragged twice)."""
    rnd = random.Random(seed)
    out = []
    for k in range(passes):
        j = [(x + rnd.uniform(-0.012, 0.012), y + rnd.uniform(-0.012, 0.012)) for x, y in pts]
        sh = polyline(slide, j, color, w=w * (1.0 if k == 0 else 0.6), alpha=0.85 if k == 0 else 0.45)
        dk.decorative(sh, "a chalk stroke; the words it frames carry the meaning")
        out.append(sh)
    return out


def chalk_box(slide, x, y, w, h, color, *, seed=0):
    rnd = random.Random(seed)
    o = lambda: rnd.uniform(-0.04, 0.04)   # noqa: E731
    pts = [(x + o(), y + o()), (x + w + o(), y + o()), (x + w + o(), y + h + o()), (x + o(), y + h + o()), (x + 0.05, y + o())]
    return chalk_path(slide, pts, color, w=2.0, seed=seed)


def chalk_ellipse(slide, cx, cy, rx, ry, color, *, seed=0, turns=1.08):
    rnd = random.Random(seed)
    pts = [(cx + rx * (1 + rnd.uniform(-0.03, 0.03)) * math.cos(a), cy + ry * (1 + rnd.uniform(-0.03, 0.03)) * math.sin(a))
           for a in [2 * math.pi * turns * t / 60 - 2.2 for t in range(61)]]
    return chalk_path(slide, pts, color, w=2.4, seed=seed)


def chalk_underline(slide, x, y, w, color, *, seed=0):
    a = chalk_path(slide, [(x + w * t / 10.0, y + 0.03 * math.sin(t * 1.7 + seed)) for t in range(11)], color, w=2.6, seed=seed)
    b = chalk_path(slide, [(x + 0.1 + (w - 0.2) * t / 10.0, y + 0.11 + 0.03 * math.sin(t * 1.3 + seed)) for t in range(11)],
                   color, w=1.8, seed=seed + 1)
    return a + b


def chalk_arrow(slide, x0, y0, x1, y1, color, *, seed=0):
    ang = math.atan2(y1 - y0, x1 - x0)
    L = 0.16
    head = [(x1 + L * math.cos(ang + 2.6), y1 + L * math.sin(ang + 2.6)), (x1, y1),
            (x1 + L * math.cos(ang - 2.6), y1 + L * math.sin(ang - 2.6))]
    return chalk_path(slide, [(x0, y0), (x1, y1)], color, w=2.2, seed=seed) + \
        chalk_path(slide, head, color, w=2.2, seed=seed + 1, passes=1)


def board_frame(slide, wood, chalk):
    """A blackboard's wooden frame drawn INSIDE the page, and a stick of chalk on the ledge. Returns the inner rect."""
    W, H = page_size(slide)
    t = 0.14 * min(W, H) / 7.5
    for x, y, w, h in ((0, 0, W, t), (0, H - t, W, t), (0, 0, t, H), (W - t, 0, t, H)):
        dk.decorative(dk.box(slide, x, y, w, h, fill=hexstr(wood)), "the blackboard's wooden frame")
    stick = dk.box(slide, 0.32 * W, H - t - 0.06, 1.2 * min(W, H) / 7.5, 0.06, fill=hexstr(chalk))
    dk.decorative(stick, "a stick of chalk on the board's ledge")
    return (t, t, W - 2 * t, H - 2 * t)


def chip_width(text, size, face, *, bold=True):
    """The width (in) of a one-line pill holding `text` at `size`: every CJK character an em, each Latin run measured
    in `face` (0.62 em a character when the face is not installed here), plus the pill's padding."""
    import display_type as _dt
    em = size / 72.0

    def run_w(r):
        if not r:
            return 0.0
        g = _dt._glyph_width(r, size, face, bold)
        return g if g is not None else 0.62 * em * len(r)
    w, run = 0.0, ""
    for ch in text:
        if dk._has_cjk(ch):
            w, run = w + run_w(run) + em, ""
        else:
            run += ch
    return w + run_w(run) + 1.2 * em


def chip(slide, x, y, text, *, size, fill, ink, face, ea_face=None, bold=True):
    """A pill label: rounded, one line that never wraps, as wide as its measured words. Returns (x, y, w, h)."""
    w, h = chip_width(text, size, face, bold=bold), size / 72.0 * 1.9
    dk.box(slide, x, y, w, h, fill=hexstr(fill), round=True, r=h / 2.0)
    run = (text, size, dk._as_rgb(hexstr(ink)), bold, False, face) + ((ea_face,) if ea_face else ())
    tb = dk.text(slide, x, y, w, h, [[run]], align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE)
    tb.text_frame.word_wrap = False
    dk.overlap_intent(tb, "the label sits on its own pill")
    return (x, y, w, h)


def share_bar(slide, x, y, w, frac, *, track, fill, h=0.16):
    """A rounded share bar: the whole track, and `frac` (clamped to 0..1) of it filled from the left."""
    frac = min(max(float(frac), 0.0), 1.0)
    dk.box(slide, x, y, w, h, fill=hexstr(track), round=True, r=h / 2.0)
    if frac > 0:
        dk.box(slide, x, y, max(h, w * frac), h, fill=hexstr(fill), round=True, r=h / 2.0)
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd skills/slide-maker && python3 tests/test_native_art.py | tail -2 && python3 tests/test_native_languages.py | tail -1`
Expected: `N passed, 0 failed` for both. The second run shows that the `_bg` change left P3 untouched. If `dk.box(..., fill=None, line=…)` rejects `fill=None` here, read `sigs.py box` and pass the no-fill form it documents; record a `Ruling:`.

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/native_art.py skills/slide-maker/tests/test_native_art.py
git commit -m "native_art: a night sky, rim-free glows, a crescent, chalk strokes, a board frame, chips and share bars; a replaced background drops its picture"
```

---

### Task 3: The second composer module and its shared helpers

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py`
  - `Kit.__init__`: add `self.memo = {}`
  - `_flow`: `draw.sizes`
  - module state `_MEMO`, cleared in `use()`
  - `_auto_ground`: the dark-default print note
- Modify: `skills/slide-maker/scripts/vl_native.py`: `compose()` publishes `k.memo`; the foot imports `vl_native2`
- Create: `skills/slide-maker/scripts/vl_native2.py`: shared helpers only; each language arrives in Tasks 4–8
- Modify: `skills/slide-maker/tests/test_native_languages.py` line 32: `vl.NATIVE[:4] == (…)`
- Modify: `skills/slide-maker/tests/test_native_generality.py`: `EXTRA.get(name, {})`
- Create: `skills/slide-maker/tests/test_native_languages_p4.py`: the harness, extended in Tasks 4–8
- Modify: `.github/workflows/ci.yml`: one step after "Native languages on untuned input"
- Modify: `skills/slide-maker/references/file-inventory.md`: entries for `vl_native2.py` and the new test

**Interfaces:**
- Consumes: Task 2 primitives.
- Produces:
  - `vl._MEMO: dict[lang, dict]`: the remembered extras of a deck's composed pages, cleared by `use()`
  - `Kit.memo: dict`: always REASSIGNED, never mutated in place (`compose()` restores `k.__dict__` shallowly on a retry)
  - `draw.sizes: dict[field, pt]` on the draw function `_flow` returns
  - In `vl_native2`:
    - `memo(k, f, name, fallback=None) -> str|None`
    - `page_no(slide) -> int`
    - `lang_of(*texts) -> "en"|"zh"|"ja"|"ko"`
    - `label(kind, *texts) -> str`, with `LABELS` keys `abstract`, `inside`, `figure`, `page`, `note`
    - `caps(t) -> str` (Latin upper-cased, CJK untouched)
    - `fields(f, names, capsed=()) -> [(field, words)]`
    - `stack(k, slide, page, x, w, y0, y1, groups, *, anchor="middle", align="l", **flow_kw) -> (rects, draws)`, where `groups = [(items, gap_after), …]`
    - `meet(a, b, pad=0.0) -> bool`
    - `tags_of(f, n, lang) -> list|None`
    - `inside_lines(v) -> list|None`
    - `raise_initial(tb, factor=2.3, face=None) -> float` (the height it adds)
    - `end_mark(tb, color, face="Arial") -> bool`
    - `kit_for(name, slide) -> Kit`
    - `max_extra(size_pt, s, factor=2.3) -> float`

- [ ] **Step 1: Write the failing test.** Create `tests/test_native_languages_p4.py`:

```python
#!/usr/bin/env python3
"""The second set of NATIVE visual languages (P4): starlit, broadsheet, journal, tally, chalkboard — registered like
the first four, every page × ground × canvas × script composes, nothing leaves the page or trips PowerPoint, and the
words only the caller can give are never invented."""
from __future__ import annotations
import contextlib, io, re, sys, tempfile, zipfile
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

EMU = 914400.0
def rect_of(sh):
    return (sh.left / EMU, sh.top / EMU, sh.width / EMU, sh.height / EMU)
def texts(s):
    return [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]
def use(name, W=13.333, H=7.5, ground="light"):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(name, prs, ground=ground)
    return prs, k

td = Path(tempfile.mkdtemp())
PHOTO = str(vl.ASSETS / "photo" / "hall-repair.jpg")
CANVASES = {"16:9": (13.333, 7.5), "4:3": (10.0, 7.5), "portrait": (7.5, 13.333)}
COPY = {
    "en": dict(kicker="A guide for the room", title="Bring it broken, take it home working",
               subtitle="Once a month, on the corner", number="3", label="evenings a month", note="Short enough to fit around work.",
               quote="The visitor holds the screwdriver; the volunteer only guides.", attribution="How every repair begins",
               body="Screwdrivers, a soldering iron and thread, shared on every bench.", caption="Photo: the hall on a Tuesday",
               line="Bring a neighbour.",
               items=[("Share the tools", "One bench, many hands"), ("Open the door", None), ("Keep it local", "Walk, don't drive")]),
    "zh": dict(kicker="茶事", title="一盏茶的时间", subtitle="慢下来，看见日常", number="3", label="泡，滋味最浓",
               note="头泡醒茶，三泡正好", quote="茶有两种姿态，浮与沉", attribution="茶室题记", body="器净，心先静。",
               caption="摄于茶室", line="下次再见", items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")]),
    "ja": dict(kicker="茶の時間", title="一服のお茶", subtitle="ゆっくり、日常を見る", number="3", label="煎目がいちばん",
               note="一煎目で目覚め、三煎目で整う", quote="茶には浮くと沈むがある", attribution="茶室の記", body="器を清め、心を静める。",
               caption="茶室にて", line="またお会いしましょう", items=[("器を清める", None), ("湯を沸かす", "蟹の目のように"), ("茶を注ぐ", None)]),
    "ko": dict(kicker="차 이야기", title="차 한 잔의 시간", subtitle="천천히, 일상을 보다", number="3", label="번째가 가장 진하다",
               note="첫 잔은 깨우고 셋째 잔은 맞춘다", quote="차에는 뜨는 것과 가라앉는 것이 있다", attribution="다실의 기록",
               body="그릇을 씻고 마음을 고른다.", caption="다실에서", line="다음에 또 만나요", items=[("그릇 씻기", None), ("물 끓이기", None)]),
}
# per language: the extras each page takes in the matrix (filled by Tasks 4–8; a missing language is a KeyError)
EXTRAS = {}


def build_matrix(name, ground, cname, lang):
    W, H = CANVASES[cname]
    T = COPY[lang]
    prs, k = use(name, W, H, ground)
    ex = EXTRAS[name](lang, len(T["items"]))
    pages = [("cover", dict(kicker=T["kicker"], title=T["title"], subtitle=T["subtitle"])),
             ("section", dict(number="02", kicker=T["kicker"], title=T["title"])),
             ("image_text", dict(kicker=T["kicker"], title=T["title"], body=T["body"], caption=T["caption"], image=PHOTO)),
             ("points", dict(kicker=T["kicker"], title=T["title"], items=T["items"])),
             ("quote", dict(quote=T["quote"], attribution=T["attribution"])),
             ("data", dict(number=T["number"], label=T["label"], note=T["note"])),
             ("closing", dict(title=T["title"], line=T["line"]))]
    for page, fields in pages:
        fields.update(ex.get(page, {}))
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
                with contextlib.redirect_stdout(io.StringIO()):
                    crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
                check(not crit, "{}: no critical layout fault: {}".format(tag, [(c[0], c[2], c[3][:70]) for c in crit[:2]]))
                check(ox.xml_findings(str(p)) == [], "{}: PowerPoint-safe: {}".format(tag, ox.xml_findings(str(p))[:2]))
                check(ox.beyond_page(prs) == [], "{}: nothing past the page: {}".format(tag, ox.beyond_page(prs)[:2]))
                check('vert="eaVert"' not in "".join(
                    zipfile.ZipFile(str(p)).read(n).decode("utf-8") for n in zipfile.ZipFile(str(p)).namelist()
                    if re.match(r"ppt/slides/slide\d+\.xml$", n)), "{}: no vertical setting in P4".format(tag))


def assert_palettes(name):
    for g, V in vl.VARIANTS[name].items():
        p = V["palette"]
        for key in ("ink", "mute"):
            check(cr(p[key], p["ground"]) >= 4.5, "{}/{} {} on ground".format(name, g, key))
            check(cr(p[key], p["panel"]) >= 4.5, "{}/{} {} on its panel (rs.card)".format(name, g, key))
        for t in p["text_accents"]:
            check(cr(t, p["ground"]) >= 4.5, "{}/{} text accent {} on ground".format(name, g, t))
            check(cr(t, p["panel"]) >= 4.5, "{}/{} text accent {} on its panel".format(name, g, t))


# ── shared helpers (Task 3) ──
import vl_native2 as v2
check(v2.lang_of("Abstract text") == "en" and v2.lang_of("摘要") == "zh" and v2.lang_of("要旨です") == "ja"
      and v2.lang_of("초록") == "ko", "lang_of reads the script of the page's own words")
check(v2.label("abstract", "고른다") == "초록" and v2.label("figure", "一服のお茶").format(1) == "図 1"
      and v2.label("inside", "Bring it") == "Inside", "structural labels follow the words' script (Review Focus 3)")
check(v2.caps("year in review") == "YEAR IN REVIEW" and v2.caps("年度回顾") == "年度回顾", "caps() leaves CJK alone")
check(v2.meet((0, 0, 1, 1), (0.5, 0.5, 1, 1)) and not v2.meet((0, 0, 1, 1), (2, 2, 1, 1)), "meet() is rect overlap")
for bad_tags in (["a"], ["a", "", "c"], "abc", ["a", "b", "c", "d"]):
    try:
        v2.tags_of({"tags": bad_tags}, 3, "broadsheet")
        check(False, "tags={!r} for 3 points is refused".format(bad_tags))
    except ValueError as e:
        check("tags" in str(e), "tags={!r} for 3 points is refused".format(bad_tags))
check(v2.tags_of({}, 3, "tally") is None and v2.tags_of({"tags": ["A", "B", "C"]}, 3, "tally") == ["A", "B", "C"],
      "no tags= draws no tags; one per point is kept")
for bad_inside in ([], ["a"] * 5, ["a", " "], "a"):
    try:
        v2.inside_lines(bad_inside)
        check(False, "inside={!r} is refused".format(bad_inside))
    except ValueError:
        check(True, "inside={!r} is refused".format(bad_inside))
# memo: given words are remembered by REASSIGNING (a failed layout's state restore must undo them)
class _K: pass
kk = _K(); kk.memo = {}
before = kk.memo
check(v2.memo(kk, {"masthead": "The Weekly"}, "masthead") == "The Weekly" and kk.memo is not before
      and before == {}, "memo() remembers by reassigning the dict, never mutating it")
check(v2.memo(kk, {}, "masthead") == "The Weekly" and v2.memo(kk, {}, "edition", fallback="x") == "x",
      "memo() returns the remembered words, else the fallback")
# raise_initial / end_mark on a real text box
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
tb = dk.text(s, 1, 1, 4, 1, [[("Anything that switches on", 18, dk.DEEP, False, False, "Georgia")]])
h0 = tb.height
added = v2.raise_initial(tb, face="Times New Roman")
r0, r1 = tb.text_frame.paragraphs[0].runs[:2]
check(r0.text == "A" and r1.text == "nything that switches on" and r0.font.size.pt > 2 * r1.font.size.pt
      and tb.height > h0 and added > 0, "raise_initial enlarges the first letter IN its line and grows the box")
tb2 = dk.text(s, 1, 3, 4, 1, [[("器净，心先静", 18, dk.DEEP, False, False, "Georgia")]])
check(v2.raise_initial(tb2) == 0.0 and len(tb2.text_frame.paragraphs[0].runs) == 1, "no raised initial on CJK")
tb3 = dk.text(s, 1, 5, 4, 1, [[("Bring a neighbour. ■", 18, dk.DEEP, False, False, "Georgia")]])
check(v2.end_mark(tb3, "A32018") and tb3.text_frame.paragraphs[-1].runs[-1].text == "■"
      and str(tb3.text_frame.paragraphs[-1].runs[-1].font.color.rgb) == "A32018", "end_mark sets ■ in its own accent run")
# _flow exposes the sizes it planned
with contextlib.redirect_stdout(io.StringIO()):
    kx = vl.use("ink", dk.blank_deck(13.333, 7.5))
_r, _d = vl._flow(kx, kx.new_slide(), "cover", (1, 1, 8, 4), [("title", "A title")], anchor="top", align="l")
check(set(getattr(_d, "sizes", {})) == {"title"} and _d.sizes["title"] > 9, "_flow's draw carries the sizes it planned")
# stack(): groups one under another with their own gap, an empty group skipped, centred when asked
_sr, _sd = v2.stack(kx, kx.new_slide(), "cover", 1.0, 8.0, 1.0, 6.5,
                    [([("title", "A title")], 0.6), ([], 0.3), ([("subtitle", "A line under it")], 0.0)], anchor="middle")
check(set(_sr) == {"title", "subtitle"} and _sr["subtitle"][1] - (_sr["title"][1] + _sr["title"][3]) >= 0.59
      and abs((_sr["title"][1] - 1.0) - (6.5 - (_sr["subtitle"][1] + _sr["subtitle"][3]))) < 0.05,
      "stack(): the gap after a group is kept, an empty group is skipped, the stack is centred: {}".format(_sr))
# a deck that never picks a native language still imports nothing new
import subprocess
probe = subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0, 'scripts'); import contextlib, io, deckkit as dk, visual_languages as vl\n"
    "with contextlib.redirect_stdout(io.StringIO()):\n"
    "    k = vl.use('collage', dk.blank_deck(13.333, 7.5)); k.new_slide()\n"
    "print(sorted(m for m in ('vl_native', 'vl_native2', 'native_art') if m in sys.modules))"],
    capture_output=True, text=True, cwd=str(ROOT))
check(probe.stdout.strip() == "[]", "an image-led deck imports no native module: {!r}".format(probe.stdout.strip()))

# ── per language (Tasks 4–8 append their sections below this line) ──


for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `ModuleNotFoundError: No module named 'vl_native2'`.

- [ ] **Step 3: Implement.**

(a) `visual_languages.py`:
- In `Kit.__init__`, after `self.project, self.field = None, None`, add:

  ```python
          self.memo = {}        # P4: the deck's remembered extras (masthead, edition, running) — REASSIGN, never mutate
  ```

- After `_PAL_OVERRIDE = {}`, add:

  ```python
  _MEMO = {}   # language -> the last composed page's remembered extras, for ordinary pages (rs.ground has no kit)
  ```

- In `use()`, after `_PAL_OVERRIDE.clear()`, add `_MEMO.clear()`.
- In `_flow`, immediately before `return rects, draw`, add:

  ```python
      draw.sizes = {f: sz for f, _t, sz, _r in plan}      # what each field was planned at (P4 sizes its art by it)
  ```

- In `_auto_ground`, replace the print-format branch's `return` with:

  ```python
          if _lum(VARIANTS[name]["light"]["palette"]["ground"]) < 0.2:
              return "light", ("a printed board ({}) takes a light ground, and {} has none — its default ground is "
                               "dark and prints as a dark page; for print, pick a language with a light ground"
                               .format(fmt.label, name))
          return "light", "a printed board ({}) takes a light ground".format(fmt.label)
  ```

  `_lum(c)` is defined at line 203; it takes a hex and returns relative luminance.

(b) `vl_native.py`:
- In `compose()`, after the `for sh in list(slide.shapes)[n0:]: dk._compose_tag(...)` loop, add:

  ```python
      if getattr(k, "memo", None):
          vl._MEMO[k.name] = dict(k.memo)        # ordinary pages (rs.ground) read the deck's remembered extras
  ```

- At the very end of the file, add:

  ```python
  # ── the second set (P4) registers its compositions on import: every importer of vl_native gets them ──
  import vl_native2  # noqa: E402,F401
  ```

(c) Create `scripts/vl_native2.py`:

```python
#!/usr/bin/env python3
"""vl_native2 — page compositions of the second set of NATIVE visual languages: starlit (星夜), broadsheet (报纸头版),
journal (学术期刊), tally (数据账本) and chalkboard (黑板报).

Same contract as vl_native, which imports this module from its foot (so any importer of vl_native gets these): each
page PLANS its text by measurement, draws its art clear of that text, then sets the text. Nothing here invents a word:
masthead / edition / inside / tags / running / authors / abstract / margin / total / doodle / ordered come from the
caller or nothing is drawn. Page numbers, figure numbers, the ■ end mark and the structural labels (Abstract, Inside,
Figure, Page, Note — in the page's own script) are derived, never typed in.
"""
from __future__ import annotations

import copy
import math
import re
from pathlib import Path

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import GROUNDS, _run_all, alt, ctx, display, fit_circle, flow, points_of, register, text_of  # noqa: F401

# Japanese and Korean entries are confirmed against a native-reading source in Task 6, not written from memory.
LABELS = {
    "abstract": {"en": "Abstract", "zh": "摘要", "ja": "要旨", "ko": "초록"},
    "inside": {"en": "Inside", "zh": "本期", "ja": "今号", "ko": "이번 호"},
    "figure": {"en": "Figure {}", "zh": "图 {}", "ja": "図 {}", "ko": "그림 {}"},
    "page": {"en": "Page {}", "zh": "第 {} 版", "ja": "{} 面", "ko": "{}면"},
    "note": {"en": "Note", "zh": "注", "ja": "注", "ko": "주"},
}


def lang_of(*texts):
    """The language a structural label is set in: the script of the page's own words (Hangul, kana, Han), else en."""
    scr = dk.script_of("".join(t for t in texts if t))
    return {"han": "zh", "kana": "ja", "hangul": "ko"}.get(scr, "en")


def label(kind, *texts):
    return LABELS[kind][lang_of(*texts)]


def caps(t):
    """Latin set in capitals (kickers, meta lines); CJK has no case and is left as written."""
    return t.upper() if t and not dk._has_cjk(t) else t


def fields(f, names, capsed=()):
    """[(field, words)] for the fields of `names` the caller gave, in order; those in `capsed` set in capitals."""
    return [(n, caps(text_of(f, n)) if n in capsed else text_of(f, n)) for n in names if text_of(f, n)]


def stack(k, slide, page, x, w, y0, y1, groups, *, anchor="middle", align="l", **flow_kw):
    """Plan GROUPS of fields one under another — groups = [(items, gap_after_in), …], an empty group skipped — inside
    [y0, y1], the whole stack anchored top or middle. Two passes: measured at the top, then placed. The gaps give an
    underline or a rule its own room (flow's own gaps are for type). Returns (rects, draws)."""
    groups = [(items, gap) for items, gap in groups if items]

    def plan(top):
        rects, draws, y = {}, [], top
        for i, (items, gap) in enumerate(groups):
            r, d = flow(k, slide, page, (x, y, w, y1 - y), items, anchor="top", align=align, **flow_kw)
            rects.update(r)
            draws.append(d)
            y = max((v[1] + v[3] for v in r.values()), default=y) + (gap if i < len(groups) - 1 else 0.0)
        return rects, draws, y
    rects, draws, foot = plan(y0)
    if anchor == "middle" and groups:
        rects, draws, foot = plan(y0 + max(0.0, (y1 - foot) / 2.0))
    return rects, draws


def meet(a, b, pad=0.0):
    return a[0] < b[0] + b[2] + pad and b[0] < a[0] + a[2] + pad and a[1] < b[1] + b[3] + pad and b[1] < a[1] + a[3] + pad


def memo(k, f, name, fallback=None):
    """The caller's words for an extra that holds for the whole deck (masthead=, edition=, running=). Given on this
    page, they are remembered by REASSIGNING k.memo — compose() restores k.__dict__ shallowly when a layout fails, so
    an in-place update would survive the failed attempt. Else the remembered words, else `fallback`."""
    v = text_of(f, name)
    if v:
        k.memo = dict(k.memo, **{name: v})
    return k.memo.get(name) or fallback


def page_no(slide):
    prs = slide.part.package.presentation_part.presentation
    return [s.slide_id for s in prs.slides].index(slide.slide_id) + 1


def tags_of(f, n, lang):
    """tags=: one short label per point, from the caller. Absent → None (no tags drawn)."""
    v = f.get("tags")
    if v is None:
        return None
    if not isinstance(v, (list, tuple)) or len(v) != n or not all(str(t or "").strip() for t in v):
        raise ValueError("{}.points(): tags= takes one non-empty label per point ({} points), got {!r}".format(lang, n, v))
    return [str(t).strip() for t in v]


def inside_lines(v):
    """inside=: 1 to 4 short lines for a broadsheet cover's 'Inside' sidebar. Absent → None."""
    if v is None:
        return None
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= 4 or not all(str(t or "").strip() for t in v):
        raise ValueError("broadsheet.cover(): inside= takes 1 to 4 non-empty lines, got {!r}".format(v))
    return [str(t).strip() for t in v]


def max_extra(size_pt, s, factor=2.3):
    """The most height (in) a raised initial can add to a body field whose base size is `size_pt` at scale `s`."""
    return (factor - 1.0) * size_pt * s * 1.2 / 72.0


def raise_initial(tb, factor=2.3, face=None):
    """Enlarge the first letter of `tb`'s first paragraph IN its line — a raised initial. pptx has no drop cap, and a
    two-box fake re-wraps differently in PowerPoint, Keynote and LibreOffice (the look-dev's "W" ran into its own
    word). Latin letters only; returns the height (in) the taller first line adds, which the box grows by."""
    from pptx.text.text import _Run
    from pptx.util import Emu, Pt
    p = tb.text_frame.paragraphs[0]
    if not p.runs:
        return 0.0
    r0 = p.runs[0]
    t = r0.text
    if not t or not t[0].isalpha() or dk._has_cjk(t[0]) or len(t) < 2:
        return 0.0
    size = r0.font.size.pt
    el = copy.deepcopy(r0._r)
    r0._r.addprevious(el)
    first = _Run(el, p)
    first.text, r0.text = t[0], t[1:]
    first.font.size, first.font.bold = Pt(size * factor), True
    if face:
        first.font.name = face
    added = (factor - 1.0) * size * 1.2 / 72.0
    tb.height = Emu(int(tb.height + added * 914400))
    return added


def end_mark(tb, color, face="Arial"):
    """Set the end-of-article ■ (planned into the words as " ■", so the measured height holds it) in its own
    run, in the accent. Returns whether a mark was found."""
    from pptx.text.text import _Run
    p = tb.text_frame.paragraphs[-1]
    if not p.runs or not p.runs[-1].text.endswith("■"):
        return False
    r = p.runs[-1]
    r.text = r.text[:-1]
    el = copy.deepcopy(r._r)
    r._r.addnext(el)
    m = _Run(el, p)
    m.text = "■"
    m.font.color.rgb = dk.RGBColor.from_string(color)
    m.font.name = face
    return True


def kit_for(name, slide):
    """A kit for an ORDINARY page: rs.ground() receives only the slide, so the ground use() set and the deck's
    remembered extras (vl._MEMO) are read back here."""
    prs = slide.part.package.presentation_part.presentation
    k = vl.Kit(name, prs, "both", None, None, None, vl._ACTIVE.get(name, "light"))
    k.memo = dict(vl._MEMO.get(name, {}))
    return k


def last_shape(slide, n0, text):
    """The text box drawn after the first n0 shapes whose words are `text` (to finish a raised initial or end mark)."""
    for sh in list(slide.shapes)[n0:][::-1]:
        if getattr(sh, "has_text_frame", False) and sh.text_frame.text.replace("\n", "").startswith(text[:12]):
            return sh
    return None
```

(d) `tests/test_native_languages.py` line 32: change it to

```python
check(vl.NATIVE[:4] == ("ink", "poster", "cutpaper", "drafting"), "the first four native languages are named, in order")
```

(e) `tests/test_native_generality.py`: in the corpus loop, change `ex = dict(EXTRA[name])` to `ex = dict(EXTRA.get(name, {}))`.

(f) `ci.yml`: add a step immediately after the "Native languages on untuned input" step:

```yaml
      - name: Native visual languages, second set (starlit, broadsheet, journal, tally, chalkboard)
        run: |
          set -o pipefail
          python tests/test_native_languages_p4.py | tee /tmp/nativep4.log
          grep -qE "(^[0-9]+ passed, 0 failed|\\] ok$)" /tmp/nativep4.log || {
            echo "::error::test_native_languages_p4 did not run to completion"; exit 1; }
```

(g) `references/file-inventory.md`: add two entries, `vl_native2.py` in the scripts list after `vl_native.py` and `test_native_languages_p4.py` in the tests list, in the same style as their neighbours:
- `vl_native2.py`: "page compositions of the second set of native visual languages (`starlit`, `broadsheet`, `journal`, `tally`, `chalkboard`); imported from the foot of `vl_native.py`".
- `test_native_languages_p4.py`: "the second set: every page × ground × canvas × script, extras never invented, PowerPoint-safe".

- [ ] **Step 4: Run to verify it passes**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -2 && python3 tests/test_native_languages.py | tail -1 && python3 scripts/check_tests_wired.py && python3 scripts/check_inventory.py`
Expected: `N passed, 0 failed` twice; both checkers exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native.py skills/slide-maker/scripts/vl_native2.py \
  skills/slide-maker/tests/test_native_languages_p4.py skills/slide-maker/tests/test_native_languages.py \
  skills/slide-maker/tests/test_native_generality.py .github/workflows/ci.yml skills/slide-maker/references/file-inventory.md
git commit -m "native languages, second set: the composer module, remembered extras, script-aware labels, raised initial and end mark"
```

---
### Task 4: `starlit` 星夜

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py`
  - `LANGS`, `VARIANTS`, `TYPE`, `NATIVE` (append `"starlit"`)
  - `_ground_starlit` + `_card_starlit` before the `for _n in LANGS: rs.register(...)` loop
  - `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Modify: `skills/slide-maker/scripts/vl_native2.py` (the starlit section)
- Modify: `skills/slide-maker/scripts/directions_diversity.py`: append `"starlit"` to `NATIVE_LANGS` and a clause to the `native_fault` message
- Create: `skills/slide-maker/assets/vl/samples/starlit.jpg`, `starlit-dawn.jpg`
- Modify: `skills/slide-maker/assets/vl/samples/manifest.json` (written by `--sample-sheet`)
- Test: `skills/slide-maker/tests/test_native_languages_p4.py` (append the starlit section)

**Interfaces:**
- Consumes:
  - Task 2: `starfield_png`, `radial_glow`, `horizon_glow`, `crescent`, `ring`, `seg`, `disc`
  - Task 3: `fields`, `stack`, `meet`
- Produces:
  - `vl.LANGS["starlit"]`, grounds `light` (midnight) and `dawn`, palette key `glow`
  - `vl_native2.GROUNDS["starlit"]`
  - seven `@register("starlit", page, alts=2)` compositions

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_native_languages_p4.py` under the "per language" marker:

```python
# ── starlit 星夜 ──
EXTRAS["starlit"] = lambda lang, n: {}
check("starlit" in vl.NATIVE and set(vl.VARIANTS["starlit"]) == {"light", "dawn"}, "starlit is native, two grounds")
assert_palettes("starlit")
assert_matrix("starlit")
POINTS4 = [("We shipped slower", "and broke less"), ("We listened more", "to the people who use it"),
           ("We kept the team", "through a hard spring"), ("We wrote it all down", None)]
def segs_of(s):
    return [sh for sh in s.shapes if sh._element.tag.endswith("}cxnSp")]
def crosses(seg, rect, n=24):
    x0, y0, x1, y1 = seg.begin_x / EMU, seg.begin_y / EMU, seg.end_x / EMU, seg.end_y / EMU
    return any(rect[0] + 0.02 < x0 + (x1 - x0) * t / n < rect[0] + rect[2] - 0.02 and
               rect[1] + 0.02 < y0 + (y1 - y0) * t / n < rect[1] + rect[3] - 0.02 for t in range(n + 1))
for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 7.5), (7.5, 13.333), (10.0, 5.625)):
    prs, k = use("starlit", W, H)
    s = k.new_slide()
    k.points(s, kicker="Year in review", title="Four things we learned", items=POINTS4)
    stars = [sh for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']")
             and not sh._element.xpath(".//a:gradFill") and sh.width / EMU < 0.3]
    check(len(stars) == 4, "starlit {}x{}: one star per point ({})".format(W, H, len(stars)))
    check(len(segs_of(s)) == 3, "starlit {}x{}: one line joins the stars in order ({})".format(W, H, len(segs_of(s))))
    hit = [(sh.text_frame.text[:20]) for g in segs_of(s) for sh in texts(s) if crosses(g, rect_of(sh))]
    check(not hit, "starlit {}x{}: no constellation line crosses words (Review Focus 4): {}".format(W, H, hit[:3]))
# the moon never sits on words; the sky is ONE picture per page (the new_slide sky is replaced, not orphaned)
for W, H in ((13.333, 7.5), (7.5, 7.5), (7.5, 13.333)):
    prs, k = use("starlit", W, H)
    for page, kw in (("cover", dict(kicker="Year in review", title="What this year taught us about building slowly and well",
                                    subtitle="A letter to the team")),
                     ("closing", dict(title="Thank you for this year", line="See you in the spring"))):
        s = k.new_slide()
        getattr(k, page)(s, **kw)
        moon = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']")
                and not sh._element.xpath(".//a:gradFill") and sh.width / EMU > 0.5]
        words = [rect_of(sh) for sh in texts(s)]
        check(not any(v2.meet(a, b) for a in moon for b in words), "starlit {}x{} {}: the moon is clear of words".format(W, H, page))
        imgs = [r for r in s.part.rels.values() if r.reltype.endswith("/image")]
        check(len(imgs) == 1, "starlit {}x{} {}: one sky picture on the page, no orphan ({})".format(W, H, page, len(imgs)))
# the number is set in the lining numeral face, never Georgia
prs, k = use("starlit")
s = k.new_slide()
k.data(s, number="2026", label="the year we slowed down")
big = max(texts(s), key=lambda sh: sh.text_frame.paragraphs[0].runs[0].font.size.pt)
check(big.text_frame.paragraphs[0].runs[0].font.name == "Times New Roman", "starlit: the figure is in Times New Roman")
# an ordinary page (Review Focus 2): new_slide paints the sky, rs.ground keeps its content rect clear of stars
import register_surface as rs
prs, k = use("starlit")
s = k.new_slide()
x, y, w, h = rs.ground(s, k.name, role="content", index=4)
check(s._element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip") is not None and w > 5 and h > 3,
      "starlit: an ordinary page gets the sky and a content rect ({:.1f}x{:.1f})".format(w, h))
check(len([r for r in s.part.rels.values() if r.reltype.endswith("/image")]) == 1, "starlit: the ordinary page has one sky")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `KeyError: 'starlit'` from `assert_palettes`.

- [ ] **Step 3: Implement.**

(a) `visual_languages.py`, the tables.
- `LANGS`, after `drafting`:

  ```python
      # ── NATIVE, second set (P4): compositions in vl_native2.py ──
      "starlit": {
          "palette": {"ground": "0B1430", "ink": "F3EBD8", "mute": "AEB6CC", "panel": "16204A",
                      "accents": ["D9B36C"], "text_accents": ["D9B36C"], "glow": "F1D9A6"},
          "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman"},
                    "mac": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman"}},
          "ea": {"display": "serif", "body": "serif"}, "grain": 0, "frames": ["ellipse"],
          "forbids": ("confetti",), "cover": "centred", "skeleton": "statement"},
  ```

- `VARIANTS`, after `drafting`:

  ```python
      "starlit": {
          "light": {"label": "midnight", "label_zh": "午夜版", "grain": 0, "palette": LANGS["starlit"]["palette"]},
          "dawn": {"label": "dawn", "label_zh": "黎明版", "grain": 0,
                   "palette": {"ground": "22163A", "ink": "F6E9E4", "mute": "C9B7C9", "panel": "2D1F4A",
                               "accents": ["EDB3A0"], "text_accents": ["EDB3A0"], "glow": "F7D2C2"}}},
  ```

- `NATIVE = ("ink", "poster", "cutpaper", "drafting", "starlit")`
- `TYPE`, after `drafting`:

  ```python
      "starlit": {"kicker": (13, "body", False, "accent", False, 10), "title": (54, "display", False, "ink", False, 26),
                  "subtitle": (18, "body", False, "mute", True, 11), "body": (17, "body", False, "ink", False, 11),
                  "mark": (110, "display", False, "accent", False, 40), "quote": (34, "display", False, "ink", True, 18),
                  "attribution": (13, "body", False, "accent", False, 10), "number": (170, "numeral", False, "accent", False, 44),
                  "label": (26, "display", False, "ink", False, 14), "note": (15, "body", False, "mute", True, 10),
                  "caption": (12, "body", False, "mute", True, 9), "line": (20, "body", False, "mute", True, 12),
                  "item_head": (24, "display", False, "ink", False, 13), "item_line": (16, "body", False, "mute", True, 10)},
  ```

- Before the `_card_editorial, … = …` lines:

  ```python
  def _ground_starlit(slide, role, index):
      """An ordinary starlit page: the sky, kept clear of the content rect it returns (painted in REAL inches —
      register_surface scales the reference canvas by _K)."""
      import native_art as na
      W, H = rs._canvas(slide)
      K = rs._K[0]
      rect = (0.6, 0.55, W - 1.2, H - 1.1)
      p = _pal("starlit")
      na.starfield_png(slide, base=p["ground"], ink=p["ink"], glow=p["glow"], seed=int(index),
                       keep_clear=[tuple(v * K for v in rect)])
      return rect
  ```

- After the `_card_ink, … = …` line, add `_card_starlit = _card_for("starlit")`.
- Add `"starlit": "Starlit night"` to `_DISPLAY_NAMES`, and to `_RATIONALE` add `"starlit": "drawn, no pictures: a night sky and a crescent moon, points as a constellation, the figure in a glow"`.
- `_SAMPLE_COPY_NATIVE["starlit"]`:

  ```python
      "starlit": [("cover", dict(kicker="Year in review", title="What this year taught us", subtitle="A letter to the team")),
                  ("points", dict(title="Three things we learned", items=[("We shipped slower", "and broke less"),
                                  ("We listened more", "to the people who use it"), ("We kept the team", "through a hard spring")])),
                  ("quote", dict(quote="We measured the year in conversations, not in launches.", attribution="From the founder's letter")),
                  ("data", dict(number="12", label="conversations that changed our plan", note="Each one is written up in the archive."))],
  ```

(b) `vl_native2.py`: append

```python
# ═══════════════════════════════════ starlit 星夜 ═══════════════════════════════════
def _st_sky(k, slide, keep, seed):
    na.starfield_png(slide, base=k.P["ground"], ink=k.P["ink"], glow=k.P["glow"], seed=seed, keep_clear=list(keep))


def _st_ground(k, slide):
    _st_sky(k, slide, (), seed=len(k.prs.slides))       # an ordinary page: the sky; its words are not known yet


GROUNDS["starlit"] = _st_ground


def _st_rule(k, slide, rects, a, b):
    """A short gold rule in the gap between field `a` and field `b` (stack() leaves that gap)."""
    if a not in rects or b not in rects:
        return lambda: None
    W, H, s, o = ctx(k)
    y = (rects[a][1] + rects[a][3] + rects[b][1]) / 2.0
    return lambda: na.seg(slide, W / 2 - 0.55 * s, y, W / 2 + 0.55 * s, y, k.P["text_accents"][0], w=1.0)


def _st_moon(k, slide, clear):
    """The crescent at the first corner clear of the words — top right, top left, bottom right; none when no corner
    is clear (it is the sky's, not the page's)."""
    W, H, s, o = ctx(k)
    d = 0.9 * s
    for cx, cy in ((0.86 * W, 0.16 * H), (0.14 * W, 0.16 * H), (0.86 * W, 0.80 * H)):
        r = (cx - 0.5 * d, cy - 0.6 * d, 1.21 * d, 1.1 * d)
        if not any(meet(r, c, 0.2 * s) for c in clear):
            na.crescent(slide, cx, cy, d, k.P["text_accents"][0], k.P["ground"])
            return


@register("starlit", "cover", alts=2)
def _st_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = (0.12 * W, 0.76 * W) if o == "land" else (0.08 * W, 0.84 * W)
    y0, y1 = (0.20 * H, 0.80 * H) if alt() == 0 else (0.07 * H, 0.92 * H)
    r, ds = stack(k, slide, "cover", x, w, y0, y1,
                  [(fields(f, ("kicker", "title"), ("kicker",)), 0.40 * s), (fields(f, ("subtitle",)), 0.0)], align="c")
    _st_sky(k, slide, r.values(), seed=1)
    _st_moon(k, slide, list(r.values()))
    _run_all([_st_rule(k, slide, r, "title", "subtitle")] + ds)
    return r


@register("starlit", "section", alts=2)
def _st_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    cx, cy = 0.5 * W, (0.32 if o == "land" else 0.26) * H
    d0 = fit_circle(k, cx, cy, (min(0.46 * H, 0.40 * W) if o == "land" else 0.62 * W) * (1.0 if alt() == 0 else 0.72))
    rects, draws = {}, []
    if num:
        r, d = flow(k, slide, "section", (cx - d0 * 0.42, cy - d0 * 0.3, d0 * 0.84, d0 * 0.6), [("number", num)],
                    anchor="middle", align="c", start={"number": 96 * s})
        rects.update(r); draws.append(d)
    top = cy + d0 / 2 + 0.1 * s if num else 0.12 * H
    r, d = flow(k, slide, "section", (0.10 * W, top, 0.80 * W, 0.92 * H - top),
                fields(f, ("kicker", "title"), ("kicker",)), anchor="top" if num else "middle", align="c")
    rects.update(r); draws.append(d)
    _st_sky(k, slide, rects.values(), seed=2)
    if num:
        na.radial_glow(slide, cx, cy, d0, k.P["glow"])
    _run_all(draws)
    return rects


@register("starlit", "image_text", alts=2)
def _st_image_text(k, slide, f, image):
    """The caller's picture in a round window with a gold rim, the words beside it (under it in portrait)."""
    W, H, s, o = ctx(k)
    if o == "land":
        d = min(0.70 * H, 0.40 * W) * (1.0 if alt() == 0 else 0.8)
        cx, cy = 0.07 * W + 0.09 * s + d / 2, 0.5 * H
        x0 = cx + d / 2 + 0.6 * s
        col = (x0, 0.10 * H, 0.93 * W - x0, 0.80 * H)
    else:
        d = min(0.80 * W, 0.40 * H) * (1.0 if alt() == 0 else 0.75)
        cx, cy = 0.5 * W, 0.06 * H + 0.09 * s + d / 2
        y0 = cy + d / 2 + 0.4 * s
        col = (0.08 * W, y0, 0.84 * W, 0.92 * H - y0)
    r, dr = flow(k, slide, "image_text", col, fields(f, ("kicker", "title", "body", "caption"), ("kicker",)),
                 anchor="middle" if o == "land" else "top")
    rim = d + 0.18 * s
    _st_sky(k, slide, list(r.values()) + [(cx - rim / 2, cy - rim / 2, rim, rim)], seed=3)
    vl._place_image(k, slide, image, (cx - d / 2, cy - d / 2, d, d),
                    vl.L_((0, 0, 1, 1), "frame", None, frame="ellipse"), "image_text")
    na.ring(slide, cx, cy, rim, k.P["text_accents"][0], w=1.25)
    dr()
    return r


@register("starlit", "quote", alts=2)
def _st_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = (0.20 * W, 0.60 * W) if (o == "land" and alt() == 0) else (0.08 * W, 0.84 * W)
    r, ds = stack(k, slide, "quote", x, w, 0.10 * H, 0.90 * H,
                  [([("mark", "“")] + fields(f, ("quote",)), 0.40 * s), (fields(f, ("attribution",), ("attribution",)), 0.0)],
                  align="c")
    _st_sky(k, slide, r.values(), seed=4)
    _run_all([_st_rule(k, slide, r, "quote", "attribution")] + ds)
    return r


@register("starlit", "data", alts=2)
def _st_data(k, slide, f, image):
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    cx, cy = 0.5 * W, (0.36 if o == "land" else 0.28) * H
    d0 = fit_circle(k, cx, cy, (min(0.60 * H, 0.46 * W) if o == "land" else 0.80 * W) * (1.0 if alt() == 0 else 0.75))
    rects, draws = {}, []
    if num:
        r, d = flow(k, slide, "data", (0.06 * W, cy - d0 * 0.32, 0.88 * W, d0 * 0.64), [("number", num)],
                    anchor="middle", align="c")
        rects.update(r); draws.append(d)
    top = cy + d0 / 2 + 0.05 * s if num else 0.30 * H
    r, d = flow(k, slide, "data", (0.10 * W, top, 0.80 * W, 0.90 * H - top), fields(f, ("label", "note")),
                anchor="top", align="c")
    rects.update(r); draws.append(d)
    _st_sky(k, slide, rects.values(), seed=5)
    if num:
        na.radial_glow(slide, cx, cy, d0, k.P["glow"])
    na.horizon_glow(slide, 0.86 * H, k.P["glow"], k.P["text_accents"][0])
    _run_all(draws)
    return rects


@register("starlit", "closing", alts=2)
def _st_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = (0.12 * W, 0.76 * W) if alt() == 0 else (0.07 * W, 0.86 * W)
    r, ds = stack(k, slide, "closing", x, w, (0.22 if alt() == 0 else 0.08) * H, 0.80 * H,
                  [(fields(f, ("title",)), 0.40 * s), (fields(f, ("line",)), 0.0)], align="c")
    _st_sky(k, slide, r.values(), seed=6)
    _st_moon(k, slide, list(r.values()))
    na.horizon_glow(slide, 0.86 * H, k.P["glow"], k.P["text_accents"][0])
    _run_all([_st_rule(k, slide, r, "title", "line")] + ds)
    return r


@register("starlit", "points", alts=2)
def _st_points(k, slide, f, image):
    """A constellation: one star per point, joined in order by one gold line. Across a landscape page the stars step
    high, low, high with their words under them; in portrait (and for long copy) they climb a zig-zag at the left
    with their words beside them. The line never reaches the words: from a high star it drops 0.75s over a whole
    column span, so at the column's edge it is still above y + 0.375s, and the words start at y + 0.42s."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    r, d = flow(k, slide, "points", (0.07 * W, 0.07 * H, 0.86 * W, (0.20 if o == "land" else 0.16) * H),
                fields(f, ("kicker", "title"), ("kicker",)))
    rects, draws, clear = dict(r), [d], list(r.values())
    top = max((v[1] + v[3] for v in r.values()), default=0.07 * H) + 0.3 * s
    stars, cols = [], []
    if o == "land" and alt() == 0:
        span = 0.86 * W / n
        for i in range(n):
            x, y = 0.07 * W + span * (i + 0.5), top + (0.45 if i % 2 == 0 else 1.20) * s
            stars.append((x, y))
            cols.append((x - span / 2 + 0.12 * s, y + 0.42 * s, span - 0.24 * s, 0.92 * H - (y + 0.42 * s)))
        align = "c"
    else:
        slot = (0.92 * H - top) / n
        lx = 0.30 * W
        for i in range(n):
            y = top + slot * (i + 0.5)
            stars.append(((0.13 if i % 2 == 0 else 0.22) * W, y))
            cols.append((lx, y - min(0.30 * s, slot / 2), 0.92 * W - lx, slot - 0.06 * s))
        align = "l"
    for (hd, ln), col in zip(pts, cols):
        tr, td_ = flow(k, slide, "points", col, [(x_, t) for x_, t in (("item_head", hd), ("item_line", ln)) if t],
                       anchor="top", align=align)
        clear += list(tr.values())
        draws.append(td_)
    _st_sky(k, slide, clear + [(x - 0.35 * s, y - 0.35 * s, 0.7 * s, 0.7 * s) for x, y in stars], seed=7)
    for a, b in zip(stars, stars[1:]):
        na.seg(slide, a[0], a[1], b[0], b[1], k.P["text_accents"][0], w=0.9, alpha=0.55)
    for x, y in stars:
        na.radial_glow(slide, x, y, 1.0 * s, k.P["glow"])
        dk.decorative(na.disc(slide, x, y, 0.16 * s, k.P["glow"]), "a star of the constellation; its words sit beside it")
    _run_all(draws)
    return rects
```

(c) `directions_diversity.py`:
- `NATIVE_LANGS = ("ink", "poster", "cutpaper", "drafting", "starlit")`
- In the `native_fault` message, change "… or drafting (research, engineering, technical)" to "…, drafting (research, engineering, technical) or starlit (year in review, letter, thanks, commemoration)". Task 9 rewrites the whole guidance once all five exist.

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `N passed, 0 failed`.

The samples loop in `test_native_languages.py` needs the bundled JPG (Step 5), so it is run after Step 5.

- [ ] **Step 5: Build, render and LOOK at the samples**

```bash
cd skills/slide-maker
python3 -c "import sys; sys.path.insert(0,'scripts'); import contextlib,io,visual_languages as vl
with contextlib.redirect_stdout(io.StringIO()):
    out=[vl.build_sample('starlit','/tmp/vl_p4',ground=g) for g in vl.VARIANTS['starlit']]
print(out)"
for stem in starlit starlit-dawn; do
  python3 scripts/render_deck.py /tmp/vl_p4/sample-$stem.pptx /tmp/vl_p4/render-$stem >/dev/null &&
  python3 scripts/visual_languages.py --sample-sheet /tmp/vl_p4/render-$stem assets/vl/samples/$stem.jpg
done
ls -la assets/vl/samples/starlit*.jpg
```

Expected: two JPGs, each ≤ 350 KB, and `manifest.json` gains `starlit` and `starlit-dawn`.

**Read both JPGs with the Read tool and compare them with the look-dev gallery** (`~/Desktop/slide-maker 新模板样张/sheets/starlit.jpg`). Check that:
- the sky is clear of every word;
- the glows show no rim;
- the constellation line stays above the words;
- the moon is clear of the title.

A defect seen here is fixed before the commit, with a test that would have caught it.

- [ ] **Step 6: Run the neighbouring suites**

Run: `cd skills/slide-maker && python3 tests/test_native_languages.py | tail -1 && python3 tests/test_native_generality.py | tail -1 && python3 tests/test_direction_vl_rule.py | tail -1 && python3 tests/test_visual_languages.py | tail -1`
Expected: `N passed, 0 failed` for all four. The generality corpus now includes starlit through `vl.NATIVE`.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native2.py \
  skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/tests/test_native_languages_p4.py \
  skills/slide-maker/assets/vl/samples/starlit.jpg skills/slide-maker/assets/vl/samples/starlit-dawn.jpg \
  skills/slide-maker/assets/vl/samples/manifest.json
git commit -m "native languages: starlit (星夜) — a night sky, points as a constellation, the figure in a glow"
```

---
### Task 5: `broadsheet` 报纸头版

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py`
  - `LANGS`, `VARIANTS`, `TYPE`, `NATIVE` (+ `"broadsheet"`)
  - `NATIVE_EXTRAS["broadsheet"] = ("masthead", "edition", "inside", "tags")`
  - `EXTRA_PAGES` (+ `"inside": ("cover",)`, `"tags": ("points",)`)
  - `_ground_broadsheet`, `_card_broadsheet`, `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Modify: `skills/slide-maker/scripts/vl_native2.py` (the broadsheet section)
- Modify: `skills/slide-maker/scripts/directions_diversity.py` (`NATIVE_LANGS` + message clause)
- Create: `skills/slide-maker/assets/vl/samples/broadsheet.jpg`, `broadsheet-salmon.jpg`; Modify: `manifest.json`
- Test: `skills/slide-maker/tests/test_native_languages_p4.py` (append)

**Interfaces:**
- Consumes:
  - Task 3: `memo`, `page_no`, `label`, `lang_of`, `caps`, `fields`, `tags_of`, `inside_lines`, `max_extra`, `raise_initial`, `end_mark`, `last_shape`, `kit_for`
  - Task 2: `chip_width`, `seg`
- Produces:
  - `vl_native2.bs_strip(k, slide, f, big=False) -> float` (the y under the strip); used by `_ground_broadsheet`
  - seven `@register("broadsheet", page, alts=2)` compositions

**Planned deviation from the spec (ledger it as a `Ruling:`).** Spec §1 lists `masthead_strip` among the
`native_art` motifs. The strip sets the caller's measured words through the kit (`flow`, its fonts and floors), and
`native_art` has no kit. So it lives in `vl_native2` as `bs_strip`. `journal`'s running head, `jn_running`, is placed
there for the same reason. Cost if wrong: one function in a different module.

- [ ] **Step 1: Write the failing tests.** Append under the starlit section:

```python
# ── broadsheet 报纸头版 ──
EXTRAS["broadsheet"] = lambda lang, n: {
    "cover": {"masthead": {"en": "The Weekly", "zh": "街坊周报", "ja": "週刊まちなか", "ko": "동네 주간"}[lang],
              "edition": {"en": "No. 12", "zh": "第 12 期", "ja": "第12号", "ko": "제12호"}[lang],
              "inside": [COPY[lang]["items"][i][0] for i in range(min(n, 3))]},
    "points": {"tags": [COPY[lang]["kicker"][:6] or "A"] * n}}
check("broadsheet" in vl.NATIVE and set(vl.VARIANTS["broadsheet"]) == {"light", "salmon"}, "broadsheet: two grounds")
assert_palettes("broadsheet")
assert_matrix("broadsheet")
def strip_texts(s):
    """The words of the masthead strip: every text box drawn before the strip's second rule (its hairline) — the
    strip is drawn first on every broadsheet page."""
    out, rules = [], 0
    for sh in s.shapes:
        if sh._element.tag.endswith("}cxnSp"):
            rules += 1
            if rules == 2:
                break
        elif getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip():
            out.append(sh.text_frame.text)
    return out
# the masthead: masthead= is remembered; else the cover's kicker names the paper; else no name — never invented
prs, k = use("broadsheet")
s1 = k.new_slide(); k.cover(s1, kicker="The Corner Paper", title="Every street needs a night for fixing things")
s2 = k.new_slide(); k.quote(s2, quote="The visitor holds the screwdriver.", attribution="Volunteer handbook")
check("The Corner Paper" in strip_texts(s1) and "The Corner Paper" in strip_texts(s2),
      "broadsheet: with no masthead=, the cover's kicker names the paper on every page ({})".format(strip_texts(s2)))
check("THE CORNER PAPER" not in [sh.text_frame.text for sh in texts(s1)],
      "broadsheet: ...and is not repeated above the headline")
s3 = k.new_slide(); k.section(s3, number="2", title="The evening", masthead="Repair Weekly", edition="No. 3")
s4 = k.new_slide(); k.data(s4, number="3", label="evenings a month")
check("Repair Weekly" in strip_texts(s4) and "NO. 3" in strip_texts(s4), "broadsheet: masthead= and edition= hold for later pages")
check(any(t == "PAGE 4" for t in strip_texts(s4)), "broadsheet: the page number is the slide's own ({})".format(strip_texts(s4)))
prs, k = use("broadsheet")
s = k.new_slide(); k.cover(s, title="Every street needs a night for fixing things")
check(strip_texts(s) == ["PAGE 1"], "broadsheet: no masthead, no kicker → no name, no date, only the page ({})".format(strip_texts(s)))
prs, k = use("broadsheet")
s = k.new_slide(); k.cover(s, title="每条街，都需要一个修东西的夜晚", masthead="街坊修理周报")
check("第 1 版" in strip_texts(s), "broadsheet: a Chinese paper numbers its pages 第 n 版 ({})".format(strip_texts(s)))
# a long CJK masthead on 4:3 and square fits or is refused — never runs into the headline (Review Focus 1)
for W, H in ((10.0, 7.5), (7.5, 7.5)):
    prs, k = use("broadsheet", W, H)
    s = k.new_slide()
    try:
        k.cover(s, title="每条街，都需要一个修东西的夜晚", masthead="社区修理网络与街坊工具图书馆联合出版的每周通讯")
    except vl.VLTextOverflow:
        check(True, "broadsheet {}x{}: an unfittable masthead is refused".format(W, H)); continue
    with contextlib.redirect_stdout(io.StringIO()):
        crit = [f_ for f_ in dk.lint_layout(prs, verbose=False) if f_[1] == "CRITICAL"]
    check(not crit, "broadsheet {}x{}: a long CJK masthead never runs into the headline: {}".format(W, H, crit[:2]))
# columns: a raised initial opens a Latin body, none on CJK; rules between columns never cross words
for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333)):
    prs, k = use("broadsheet", W, H)
    s = k.new_slide()
    k.points(s, title="How a repair evening works", tags=["The idea", "The evening", "Next"],
             items=[("Bring it broken", "Anything that switches on is welcome."), ("Fix it together", "A volunteer sits beside you."),
                    ("Take it home", "What could not be fixed goes on a list.")])
    firsts = [sh.text_frame.paragraphs[0].runs[0] for sh in texts(s) if sh.text_frame.text.startswith(("Anything", "A volunteer", "What"))]
    check(len(firsts) == 3 and all(len(r.text) == 1 and r.font.size.pt > 30 for r in firsts),
          "broadsheet {}x{}: each Latin column opens on a raised initial".format(W, H))
    hit = [g for g in segs_of(s) for sh in texts(s) if crosses(g, rect_of(sh))]
    check(not hit, "broadsheet {}x{}: no column rule crosses words".format(W, H))
prs, k = use("broadsheet")
s = k.new_slide()
k.points(s, title="修理之夜怎么进行", items=[("带着坏东西来", "能开机的都欢迎。"), ("一起动手修", "动手的是你。")])
check(all(len(sh.text_frame.paragraphs[0].runs) >= 1 and sh.text_frame.paragraphs[0].runs[0].font.size.pt < 30
          for sh in texts(s) if sh.text_frame.text.startswith(("能开机", "动手"))), "broadsheet: no raised initial on CJK")
for bad_kw in (dict(tags=["a"]), dict(inside=["x"])):
    prs, k = use("broadsheet")
    try:
        k.points(k.new_slide(), title="x", items=["a", "b"], **bad_kw)
        check(False, "broadsheet.points({}) is refused".format(bad_kw))
    except (ValueError, TypeError):
        check(True, "broadsheet.points({}) is refused (wrong count / a cover-only extra)".format(bad_kw))
# the closing ends on the ■ end mark, in the accent
prs, k = use("broadsheet")
s = k.new_slide(); k.closing(s, title="See you next week", line="Bring a neighbour.")
last = texts(s)[-1].text_frame.paragraphs[-1].runs[-1]
check(last.text == "■" and str(last.font.color.rgb) == vl.VARIANTS["broadsheet"]["light"]["palette"]["text_accents"][0],
      "broadsheet: the closing ends on ■ in the accent")
# an ordinary page (Review Focus 2) carries the strip; its content rect starts under it
import register_surface as rs
prs, k = use("broadsheet")
k.cover(k.new_slide(), title="Every street", masthead="Repair Weekly")
s = k.new_slide()
x, y, w, h = rs.ground(s, k.name, role="content", index=2)
check("Repair Weekly" in strip_texts(s) and y >= max(sh.top / EMU + sh.height / EMU for sh in texts(s)),
      "broadsheet: an ordinary page carries the masthead strip and its content starts under it ({:.2f})".format(y))
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `KeyError: 'broadsheet'`.

- [ ] **Step 3: Implement.**

(a) `visual_languages.py`, the tables.
- `LANGS`:

  ```python
      "broadsheet": {
          "palette": {"ground": "F2EEE5", "ink": "141414", "mute": "4A4744", "panel": "E6E0D3",
                      "accents": ["A32018"], "text_accents": ["A32018"]},
          "fonts": {"both": {"display": "Times New Roman", "body": "Georgia", "numeral": "Times New Roman", "meta": "Arial"},
                    "mac": {"display": "Times New Roman", "body": "Georgia", "numeral": "Times New Roman", "meta": "Arial"}},
          "ea": {"display": "serif", "body": "serif"}, "grain": 4, "frames": ["rect"],
          "forbids": ("confetti",), "cover": "full-bleed-type", "skeleton": "split"},
  ```

- `VARIANTS`:

  ```python
      "broadsheet": {
          "light": {"label": "newsprint", "label_zh": "报纸版", "grain": 4, "palette": LANGS["broadsheet"]["palette"]},
          "salmon": {"label": "pink paper", "label_zh": "粉报版", "grain": 4,
                     "palette": {"ground": "FBE8D8", "ink": "1A1714", "mute": "54493F", "panel": "F3DAC6",
                                 "accents": ["0F4C81"], "text_accents": ["0F4C81"]}}},
  ```

- `TYPE`:

  ```python
      "broadsheet": {"kicker": (12, "meta", True, "accent", False, 9), "title": (80, "display", True, "ink", False, 30),
                     "subtitle": (24, "body", False, "ink", True, 13), "body": (18, "body", False, "ink", False, 11),
                     "mark": (100, "display", True, "accent", False, 40), "quote": (38, "body", False, "ink", True, 18),
                     "attribution": (11, "meta", True, "mute", False, 9), "number": (150, "numeral", True, "ink", False, 44),
                     "label": (22, "body", True, "ink", False, 12), "note": (14, "body", False, "mute", True, 9),
                     "caption": (12, "body", False, "mute", True, 9), "line": (20, "body", False, "ink", True, 12),
                     "item_head": (28, "display", True, "ink", False, 14), "item_line": (18, "body", False, "ink", False, 11),
                     "masthead": (40, "display", True, "ink", False, 12), "edition": (10, "meta", True, "mute", False, 8),
                     "inside": (16, "body", False, "ink", False, 10), "inside_h": (11, "meta", True, "accent", False, 9),
                     "tag": (10, "meta", True, "accent", False, 8)},
  ```

- `NATIVE` gains `"broadsheet"`.
- Extras:
  - `NATIVE_EXTRAS["broadsheet"] = ("masthead", "edition", "inside", "tags")`
  - `EXTRA_PAGES["inside"] = ("cover",)`; `EXTRA_PAGES["tags"] = ("points",)`
- Ground and card:

  ```python
  def _ground_broadsheet(slide, role, index):
      """An ordinary broadsheet page: the masthead strip (the deck's remembered masthead and edition, this page's
      number), and the content rect under it — in REFERENCE inches."""
      import vl_native2 as v2
      K = rs._K[0]
      W, H = rs._canvas(slide)
      y = v2.bs_strip(v2.kit_for("broadsheet", slide), slide, {}) / K
      return (0.05 * W, y + 0.15, 0.90 * W, H - y - 0.75)
  ```

  Add `_card_broadsheet = _card_for("broadsheet")`.
- `_DISPLAY_NAMES["broadsheet"] = "Broadsheet front page"`; `_RATIONALE["broadsheet"] = "drawn, no pictures: a masthead strip, a headline and standfirst, newspaper columns, a pull quote between rules"`.
- `_SAMPLE_COPY_NATIVE["broadsheet"]`:

  ```python
      "broadsheet": [("cover", dict(title="Every street needs a night for fixing things",
                                    subtitle="Volunteers, borrowed tools and one long table: how a repair evening works.",
                                    masthead="The Neighbourhood Repair Weekly", inside=["The idea", "The evening", "The numbers"])),
                     ("points", dict(title="How a repair evening works", tags=["The idea", "The evening", "The next step"],
                                     items=[("Bring it broken", "Anything that switches on, unzips or wobbles is welcome."),
                                            ("Fix it together", "A volunteer sits beside you, but your hands do the work."),
                                            ("Take it home", "What could not be fixed today goes on a list for next time.")])),
                     ("quote", dict(quote="The visitor holds the screwdriver; the volunteer only guides.",
                                    attribution="From the volunteer handbook")),
                     ("data", dict(number="3", label="evenings a month", note="Short enough to fit around work."))],
  ```

(b) `vl_native2.py`: append

```python
# ═══════════════════════════════════ broadsheet 报纸头版 ═══════════════════════════════════
def bs_strip(k, slide, f, big=False):
    """The masthead strip every page carries: the paper's name (masthead=, else the cover's kicker, else none), a
    heavy rule, the caller's edition= at the left and the page number at the right, a hairline. Never invents a name,
    a date or an issue number. Draws at once and returns the y under it."""
    W, H, s, o = ctx(k)
    name = memo(k, f, "masthead", fallback=k.memo.get("_cover_kicker"))
    edition = memo(k, f, "edition")
    y = 0.04 * H
    draws = []
    if name:
        nh = (0.80 if big else 0.52) * s
        r, d = flow(k, slide, "masthead", (0.05 * W, y, 0.90 * W, nh), [("masthead", name)], anchor="middle", align="c",
                    start={"masthead": (44 if big else 26) * s})
        draws.append(d)
        y = max(y + nh, max(v[1] + v[3] for v in r.values())) + 0.04 * s
    rule_y, meta_y = y, y + 0.10 * s
    draws.append(lambda: na.seg(slide, 0.05 * W, rule_y, 0.95 * W, rule_y, k.P["ink"], w=2.5))
    if edition:
        r, d = flow(k, slide, "edition", (0.05 * W, meta_y, 0.62 * W, 0.30 * s), [("edition", caps(edition))])
        draws.append(d)
    pg = caps(label("page", name, edition, text_of(f, "title"), text_of(f, "quote"), k.memo.get("_title")).format(page_no(slide)))
    sz = vl.TYPE[k.name]["edition"][0] * s
    draws.append(lambda: dk.text(slide, 0.70 * W, meta_y, 0.25 * W, 0.30 * s,
                                 [k.runs(pg, sz, k.color("mute"), True, "meta")], align=dk.PP_ALIGN.RIGHT))
    hair = meta_y + 0.34 * s
    draws.append(lambda: na.seg(slide, 0.05 * W, hair, 0.95 * W, hair, k.P["ink"], w=0.6))
    _run_all(draws)
    return hair + 0.10 * s


def _with_initial(k, slide, draw, words):
    """Run a planned draw, then open the body it set on a raised initial (planned with room for it: max_extra)."""
    def go():
        n0 = len(slide.shapes)
        draw()
        tb = last_shape(slide, n0, words)
        if tb is not None:
            raise_initial(tb, face=k.face("display"))
    return go


@register("broadsheet", "cover", alts=2)
def _bs_cover(k, slide, f, image):
    """A front page: the headline across the page, a rule, the standfirst; the caller's inside= lines in a sidebar
    (under the standfirst in portrait). With no masthead= the cover's kicker names the paper and is not repeated."""
    W, H, s, o = ctx(k)
    kick, title = text_of(f, "kicker"), text_of(f, "title")
    as_name = bool(kick) and not text_of(f, "masthead") and not k.memo.get("masthead")
    if title:
        k.memo = dict(k.memo, _title=title)
    if as_name:
        k.memo = dict(k.memo, _cover_kicker=kick)
    top = bs_strip(k, slide, f, big=True) + 0.12 * s
    lines = inside_lines(f.get("inside"))
    head = ([("kicker", caps(kick))] if kick and not as_name else []) + ([("title", title)] if title else [])
    hh = ((0.50 if o == "land" else 0.36) if alt() == 0 else (0.62 if o == "land" else 0.48)) * H
    r, d = flow(k, slide, "cover", (0.05 * W, top, 0.90 * W, hh), head, anchor="top")
    rects, draws = dict(r), [d]
    yr = max((v[1] + v[3] for v in r.values()), default=top) + 0.16 * s
    art = [lambda: na.seg(slide, 0.05 * W, yr, 0.95 * W, yr, k.P["ink"], w=0.75)]
    side = bool(lines) and o == "land"
    sub, sb, foot = text_of(f, "subtitle"), yr, H - 0.6
    if sub:
        r, d = flow(k, slide, "cover", (0.05 * W, yr + 0.16 * s, (0.62 if side else 0.90) * W, foot - yr - 0.16 * s),
                    [("subtitle", sub)], anchor="top")
        rects.update(r); draws.append(d)
        sb = max(v[1] + v[3] for v in r.values())
    if lines:
        if side:
            ix, iy, iw = 0.71 * W, yr + 0.16 * s, 0.24 * W
            art.append(lambda: na.seg(slide, 0.685 * W, yr + 0.16 * s, 0.685 * W, foot, k.P["ink"], w=0.5))
        else:
            ix, iy, iw = 0.05 * W, sb + 0.3 * s, 0.90 * W
        r, d = flow(k, slide, "cover", (ix, iy, iw, foot - iy),
                    [("inside_h", caps(label("inside", *lines))), ("inside", "\n".join(lines))], anchor="top")
        draws.append(d)
    _run_all(art + draws)
    return rects


@register("broadsheet", "section", alts=2)
def _bs_section(k, slide, f, image):
    """A section front: the number in a black tab on a heavy rule, the section's title as its headline."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    num = text_of(f, "number")
    rects, art, draws = {}, [], []
    y = top + (0.6 if alt() == 0 else 0.3) * s
    if num:
        th = 0.95 * s
        tw = min(0.6 * W, max(1.1 * s, na.chip_width(num, 44 * s, k.face("numeral")) + 0.2 * s))
        r, d = flow(k, slide, "section", (0.05 * W + 0.1 * s, y, tw - 0.2 * s, th), [("number", num)], anchor="middle",
                    align="c", ink=k.P["ground"], accent=k.P["ground"], start={"number": 44 * s})
        rects.update(r); draws.append(d)
        art.append(lambda y=y: dk.box(slide, 0.05 * W, y, tw, th, fill=k.P["ink"]))
        y += th
    art.append(lambda y=y: na.seg(slide, 0.05 * W, y, 0.95 * W, y, k.P["ink"], w=3.0))
    r, d = flow(k, slide, "section", (0.05 * W, y + 0.3 * s, 0.90 * W, H - 0.6 - y - 0.3 * s),
                fields(f, ("kicker", "title"), ("kicker",)), anchor="top")
    rects.update(r); draws.append(d)
    _run_all(art + draws)
    return rects


@register("broadsheet", "image_text", alts=2)
def _bs_image_text(k, slide, f, image):
    """A news photograph with its caption under a hairline; the story's headline and body beside it (under it in
    portrait)."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f) + 0.25 * s
    bottom = H - 0.6
    cap = text_of(f, "caption")
    rects, draws, art = {}, [], []
    if o == "land":
        img_x, img_w = 0.05 * W, (0.58 if alt() == 0 else 0.50) * W
        cx0 = img_x + img_w + 0.35 * s
        col = (cx0, top, 0.95 * W - cx0, bottom - top)
        img_y1 = bottom
        if cap:
            cr_, cd = flow(k, slide, "image_text", (img_x, bottom - 0.9 * s, img_w, 0.9 * s), [("caption", cap)], anchor="bottom")
            img_y1 = cr_["caption"][1] - 0.22 * s
    else:
        img_x, img_w = 0.05 * W, 0.90 * W
        img_y1 = top + (0.42 if alt() == 0 else 0.34) * H
        if cap:
            cr_, cd = flow(k, slide, "image_text", (img_x, img_y1 + 0.22 * s, img_w, 0.6 * s), [("caption", cap)], anchor="top")
        cy0 = (max(v[1] + v[3] for v in cr_.values()) if cap else img_y1) + 0.3 * s
        col = (0.05 * W, cy0, 0.90 * W, bottom - cy0)
    if cap:
        rects.update(cr_); draws.append(cd)
        hy = cr_["caption"][1] - 0.11 * s
        art.append(lambda: na.seg(slide, img_x, hy, img_x + img_w, hy, k.P["ink"], w=0.5))
    r, d = flow(k, slide, "image_text", col, fields(f, ("kicker", "title", "body"), ("kicker",)), anchor="top")
    rects.update(r); draws.append(d)
    vl._place_image(k, slide, image, (img_x, top, img_w, img_y1 - top), vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(art + draws)
    return rects


@register("broadsheet", "quote", alts=2)
def _bs_quote(k, slide, f, image):
    """A pull quote between a heavy rule and a hairline, the quote mark hung in the margin, the source under it."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    x0, x1 = (0.12 * W, 0.88 * W) if (o == "land" and alt() == 0) else (0.06 * W, 0.94 * W)
    mw = 0.9 * s
    q, a = text_of(f, "quote"), text_of(f, "attribution")
    rects, draws = {}, []
    qy0, qy1 = top + 0.85 * s, H - 1.4 * s
    if q:
        r, d = flow(k, slide, "quote", (x0 + mw, qy0, x1 - x0 - mw, qy1 - qy0), [("quote", q)], anchor="middle")
        rects.update(r); draws.append(d)
        qt, qb = r["quote"][1], r["quote"][1] + r["quote"][3]
        _m, dm = flow(k, slide, "quote", (x0, qt - 0.12 * s, mw, 1.2 * s), [("mark", "“")], start={"mark": 80 * s})
        draws.append(dm)
    else:
        qt = qb = (qy0 + qy1) / 2.0
    art = [lambda: na.seg(slide, x0, qt - 0.3 * s, x1, qt - 0.3 * s, k.P["ink"], w=3.0),
           lambda: na.seg(slide, x0, qb + 0.25 * s, x1, qb + 0.25 * s, k.P["ink"], w=0.6)]
    if a:
        r, d = flow(k, slide, "quote", (x0 + mw, qb + 0.40 * s, x1 - x0 - mw, 0.8 * s), [("attribution", caps(a))])
        rects.update(r); draws.append(d)
    _run_all(art + draws)
    return rects


@register("broadsheet", "data", alts=2)
def _bs_data(k, slide, f, image):
    """By the numbers: the figure, a short rule, its label and note, in a boxed panel under a solid band — a header
    with no words, because the kit has none to give it."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    bw = ((0.42 if o == "land" else 0.80) if alt() == 0 else 0.86) * W
    bx, band, pad = (W - bw) / 2.0, 0.30 * s, 0.30 * s
    y_in, avail = top + 0.3 * s, (H - 0.6) - (top + 0.3 * s)
    items = fields(f, ("number", "label", "note"))

    def plan(y):
        return flow(k, slide, "data", (bx + pad, y + band + pad, bw - 2 * pad, avail - band - 2 * pad), items,
                    anchor="top", align="c")
    r, _unused = plan(y_in)
    bh = band + 2 * pad + (max(v[1] + v[3] for v in r.values()) - (y_in + band + pad)) + 0.1 * s
    by = y_in + max(0.0, (avail - bh) / 2.0)
    r, d = plan(by)
    art = [lambda: dk.box(slide, bx, by, bw, bh, fill=None, line=dk._as_rgb(k.P["ink"]), line_w=1.25),
           lambda: dk.decorative(dk.box(slide, bx, by, bw, band, fill=k.P["ink"]), "the header band of a numbers box")]
    if "number" in r and "label" in r:
        yl = (r["number"][1] + r["number"][3] + r["label"][1]) / 2.0
        art.append(lambda: na.seg(slide, W / 2 - 0.15 * bw, yl, W / 2 + 0.15 * bw, yl, k.P["ink"], w=0.6))
    _run_all(art + [d])
    return r


@register("broadsheet", "closing", alts=2)
def _bs_closing(k, slide, f, image):
    """The last story's end: its headline, its line, and the ■ end-of-article mark after the last words."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    t, ln = text_of(f, "title"), text_of(f, "line")
    items = [("title", t if ln or not t else t + " ■")] if t else []
    if ln:
        items.append(("line", ln + " ■"))
    col = (0.05 * W, top + 0.3 * s, (0.70 if o == "land" and alt() == 0 else 0.90) * W, H - 0.6 - top - 0.3 * s)
    r, d = flow(k, slide, "closing", col, items, anchor="middle")
    d()
    end_mark(list(slide.shapes)[-1], k.P["text_accents"][0])
    return r


@register("broadsheet", "points", alts=2)
def _bs_points(k, slide, f, image):
    """Newspaper columns: each point a column — the caller's tag over its head over its body, a Latin body opening on
    a raised initial — hairline rules between. Portrait and long copy stack the columns as rows."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    pts = points_of(f.get("items"))
    n = len(pts)
    tags = tags_of(f, n, "broadsheet")
    r, d = flow(k, slide, "points", (0.05 * W, top + 0.05 * s, 0.90 * W, 0.20 * H), fields(f, ("kicker", "title"), ("kicker",)))
    rects, draws, art = dict(r), [d], []
    ctop = max((v[1] + v[3] for v in r.values()), default=top) + 0.30 * s
    bottom = H - 0.6
    extra = max_extra(vl.TYPE["broadsheet"]["item_line"][0], s)
    stacked = o != "land" or alt() == 1
    if stacked:
        slot = (bottom - ctop) / n
        boxes = [(0.05 * W, ctop + i * slot, 0.90 * W, slot - 0.15 * s) for i in range(n)]
    else:
        gap = 0.30 * s
        cw = (0.90 * W - (n - 1) * gap) / n
        boxes = [(0.05 * W + i * (cw + gap), ctop, cw, bottom - ctop) for i in range(n)]
    for i, ((hd, ln), (x, y, w, h)) in enumerate(zip(pts, boxes)):
        if i and stacked:
            art.append(lambda y=y: na.seg(slide, 0.05 * W, y - 0.08 * s, 0.95 * W, y - 0.08 * s, k.P["ink"], w=0.5))
        elif i:
            art.append(lambda x=x: na.seg(slide, x - 0.15 * s, ctop, x - 0.15 * s, bottom, k.P["ink"], w=0.5))
        items = ([("tag", caps(tags[i]))] if tags else []) + [("item_head", hd)] + ([("item_line", ln)] if ln else [])
        initial = bool(ln) and ln[0].isalpha() and not dk._has_cjk(ln[0])
        _tr, td_ = flow(k, slide, "points", (x, y, w, h - (extra if initial else 0.0)), items, anchor="top")
        draws.append(_with_initial(k, slide, td_, ln) if initial else td_)
    _run_all(art + draws)
    return rects
```

(c) `directions_diversity.py`: append `"broadsheet"` to `NATIVE_LANGS`, and add the message clause "broadsheet (newsletter, periodic report, community update)".

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `N passed, 0 failed`.

If lint reports the raised-initial box as overflowing, the lint line model does not credit the larger first run. Measure it: render the page, look, and compare the box height with the ink. Then either correct `raise_initial`'s `added` to what the lint measures, or record a `Ruling:` that explains which one is right.

- [ ] **Step 5: Build, render and LOOK at the samples**

Use the same commands as Task 4 Step 5, with `broadsheet` and the stems `broadsheet`, `broadsheet-salmon`. Read both JPGs and compare them with `~/Desktop/slide-maker 新模板样张/sheets/broadsheet.jpg`. Check that:
- the strip carries only the masthead and page number;
- the raised initials sit in their lines;
- the pull quote's rules clear the words;
- the data box fits its words;
- there is no "— 30 —".

- [ ] **Step 6: Run the neighbouring suites** (the same four commands as Task 4 Step 6). Expected: all `0 failed`.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native2.py \
  skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/tests/test_native_languages_p4.py \
  skills/slide-maker/assets/vl/samples/broadsheet.jpg skills/slide-maker/assets/vl/samples/broadsheet-salmon.jpg \
  skills/slide-maker/assets/vl/samples/manifest.json
git commit -m "native languages: broadsheet (报纸头版) — a masthead strip, headline cover, newspaper columns, a pull quote"
```

---
### Task 6: `journal` 学术期刊

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py`
  - `LANGS`, `VARIANTS`, `TYPE`, `NATIVE` (+ `"journal"`)
  - `NATIVE_EXTRAS["journal"] = ("running", "authors", "abstract", "margin")`
  - `EXTRA_PAGES` (+ `"authors": ("cover",)`, `"abstract": ("cover",)`, `"margin": ("points",)`)
  - `_ground_journal`, `_card_journal`, `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Modify: `skills/slide-maker/scripts/vl_native2.py` (the journal section; `LABELS` confirmed)
- Modify: `skills/slide-maker/scripts/directions_diversity.py`
- Create: `skills/slide-maker/assets/vl/figure/illustrative-curves.jpg` (the sample's figure, stamped "illustrative")
- Create: `assets/vl/samples/journal.jpg`, `journal-green.jpg`; Modify: `manifest.json`
- Test: `skills/slide-maker/tests/test_native_languages_p4.py` (append)

**Interfaces:**
- Consumes: Task 3 helpers; `vl._resolve(k, image) -> (path, alt, slot_id)`.
- Produces:
  - `vl_native2.jn_running(k, slide, f) -> float` (the y under the running head); used by `_ground_journal`
  - seven `@register("journal", page, alts=2)` compositions
  - figure numbering through `k.memo["_fig"]`

- [ ] **Step 1: Confirm the Japanese and Korean labels before testing them.**
  - **What to confirm.** Use WebSearch to check each of these against a native-language source: a university's thesis-format guide, a journal's author instructions, or a newspaper's own page:
    - abstract: 要旨 (ja), 초록 (ko)
    - figure: 図 1 (ja), 그림 1 (ko)
    - this issue: 今号 (ja), 이번 호 (ko)
    - page n of a paper: n面 (ja), n면 (ko)
    - note: 注 (ja), 주 (ko)
  - **Ledger.** Record each source URL in the ledger as `Task 6: Ruling: label <term> — <source> — cost if wrong: a wrong word on every page of that script's decks`.
  - **If a term does not hold**, change `LABELS` and the Task 3 test together.

- [ ] **Step 2: Write the failing tests.** Append:

```python
# ── journal 学术期刊 ──
EXTRAS["journal"] = lambda lang, n: {
    "cover": {"authors": {"en": "A. One · B. Two", "zh": "作者一 · 作者二", "ja": "著者一 · 著者二", "ko": "저자 1 · 저자 2"}[lang],
              "abstract": COPY[lang]["subtitle"] + " " + COPY[lang]["body"]},
    "points": {"margin": COPY[lang]["note"]}}
check("journal" in vl.NATIVE and set(vl.VARIANTS["journal"]) == {"light", "green"}, "journal: two grounds")
assert_palettes("journal")
assert_matrix("journal")
def head_texts(s):
    """The running head's words: text boxes above the first rule of the page."""
    rule = min((sh.top / EMU for sh in s.shapes if sh._element.tag.endswith("}cxnSp")), default=0)
    return [sh.text_frame.text for sh in texts(s) if sh.top / EMU < rule]
# the running head: running= remembered; else the cover title on one line; else the page number alone
prs, k = use("journal")
k.cover(k.new_slide(), title="Learning to reconstruct undersampled cardiac MRI")
s = k.new_slide(); k.closing(s, title="Questions")
check(head_texts(s) == ["Learning to reconstruct undersampled cardiac MRI", "2"],
      "journal: the cover title runs at the head of later pages, with the page number ({})".format(head_texts(s)))
s = k.new_slide(); k.closing(s, title="Questions", running="Lab meeting · reconstruction")
s2 = k.new_slide(); k.quote(s2, quote="Measure twice.", attribution="A reviewer")
check(head_texts(s2)[0] == "Lab meeting · reconstruction", "journal: running= holds for later pages")
LONG = "A very long article title about learning to reconstruct undersampled cardiac magnetic resonance imaging " * 3
prs, k = use("journal", 7.5, 7.5)
k.cover(k.new_slide(), title="Short")
k.memo = dict(k.memo, _title=LONG)
s = k.new_slide(); k.closing(s, title="Thank you")
check(head_texts(s) == ["2"], "journal: a remembered title too long for one line leaves the page number alone ({})".format(head_texts(s)))
try:
    k.closing(k.new_slide(), title="Thank you", running=LONG)
    check(False, "journal: an explicit running= that cannot fit is refused")
except vl.VLTextOverflow:
    check(True, "journal: an explicit running= that cannot fit is refused (Review Focus 1)")
# the abstract label appears only with abstract=, in the words' own script (Review Focus 3)
for abstract, want in (("We ask whether a learned reconstruction keeps fine edges.", "ABSTRACT"),
                       ("我们想知道学习重建能否保住细小的边缘。", "摘要"), ("학습 재구성이 가는 경계를 지키는지 묻는다.", "초록"),
                       ("学習再構成が細い縁を保てるかを問う。", "要旨")):
    prs, k = use("journal")
    s = k.new_slide(); k.cover(s, title="A title", abstract=abstract)
    check(want in [sh.text_frame.text for sh in texts(s)], "journal: abstract= is labelled {!r}".format(want))
prs, k = use("journal")
s = k.new_slide(); k.cover(s, title="A title", subtitle="A talk for the lab")
check(not any(t in ("ABSTRACT", "摘要") for t in (sh.text_frame.text for sh in texts(s))),
      "journal: a subtitle is never labelled Abstract")
# figures are numbered over the deck's figure pages; kicker= overrides; the figure is whole (contain)
prs, k = use("journal")
labels_ = []
for kw in (dict(title="Error across acceleration"), dict(title="Edges at 8×", kicker="Figure S2"), dict(title="Third")):
    s = k.new_slide(); k.image_text(s, image=PHOTO, body="A caption.", **kw)
    labels_.append([sh.text_frame.text for sh in texts(s) if sh.text_frame.text.upper().startswith("FIGURE")][0])
check(labels_ == ["FIGURE 1", "FIGURE S2", "FIGURE 3"], "journal: figures number themselves; kicker= overrides ({})".format(labels_))
pic = [sh for sh in s.shapes if sh.shape_type == 13][0]
check(pic.crop_left == 0 and pic.crop_right == 0 and pic.crop_top == 0 and pic.crop_bottom == 0,
      "journal: the figure is placed whole, never cropped")
prs, k = use("journal")
s = k.new_slide(); k.image_text(s, image=PHOTO, title="一服のお茶", body="図の説明。")
check(any(sh.text_frame.text == "図 1" for sh in texts(s)), "journal: a Japanese figure reads 図 1")
# section: § only before a numeral or roman numeral
for num, want in (("2", "§ 2"), ("IV", "§ IV"), ("Part two", "Part two")):
    prs, k = use("journal")
    s = k.new_slide(); k.section(s, number=num, title="Method")
    check(want in [sh.text_frame.text for sh in texts(s)], "journal: section number {!r} → {!r}".format(num, want))
# margin= sits beside the list (under it in portrait), under its Note label
for W, H in ((13.333, 7.5), (7.5, 13.333)):
    prs, k = use("journal", W, H)
    s = k.new_slide()
    k.points(s, title="What we set out to test", items=[("The question", "Edges at high acceleration?"), ("The check", None)],
             margin="Every figure is labelled with its source.")
    tt = [sh.text_frame.text for sh in texts(s)]
    check("NOTE" in tt and "Every figure is labelled with its source." in tt, "journal {}x{}: the margin note and its label".format(W, H))
# an ordinary page (Review Focus 2) carries the running head; its content rect starts under it
import register_surface as rs
prs, k = use("journal")
k.cover(k.new_slide(), title="Learning to reconstruct")
s = k.new_slide()
x, y, w, h = rs.ground(s, k.name, role="content", index=2)
check(head_texts(s)[:1] == ["Learning to reconstruct"] and y > 0.6, "journal: an ordinary page carries the running head")
```

- [ ] **Step 3: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `KeyError: 'journal'`.

- [ ] **Step 4: Implement.**

(a) `visual_languages.py`, the tables.
- `LANGS`:

  ```python
      "journal": {
          "palette": {"ground": "FBFAF6", "ink": "1B1B1B", "mute": "5A5A55", "panel": "F1EFE7",
                      "accents": ["1F5C46"], "text_accents": ["1F5C46"]},
          "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman", "meta": "Arial"},
                    "mac": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman", "meta": "Arial"}},
          "ea": {"display": "serif", "body": "serif"}, "grain": 0, "frames": ["rect"],
          "forbids": ("confetti",), "cover": "low-left", "skeleton": "rail"},
  ```

- `VARIANTS`:

  ```python
      "journal": {
          "light": {"label": "paper", "label_zh": "论文白版", "grain": 0, "palette": LANGS["journal"]["palette"]},
          "green": {"label": "title green", "label_zh": "期刊绿版", "grain": 0,
                    "palette": {"ground": "163A2E", "ink": "F1EEE4", "mute": "BFC8BF", "panel": "1E4A3B",
                                "accents": ["D9C27A"], "text_accents": ["D9C27A"]}}},
  ```

- `TYPE`:

  ```python
      "journal": {"kicker": (12, "meta", True, "accent", False, 9), "title": (46, "display", False, "ink", False, 24),
                  "subtitle": (20, "body", False, "mute", True, 12), "body": (16, "body", False, "ink", False, 10),
                  "mark": (80, "display", False, "accent", False, 32), "quote": (30, "body", False, "ink", True, 16),
                  "attribution": (13, "meta", True, "mute", False, 9), "number": (140, "numeral", False, "accent", False, 40),
                  "label": (24, "body", False, "ink", False, 13), "note": (15, "body", False, "mute", False, 10),
                  "caption": (11, "body", False, "mute", True, 8), "line": (20, "body", False, "mute", True, 12),
                  "item_head": (21, "body", True, "ink", False, 12), "item_line": (15, "body", False, "mute", False, 10),
                  "item_no": (30, "numeral", True, "accent", False, 14), "authors": (17, "body", False, "ink", False, 11),
                  "abstract": (16, "body", False, "ink", False, 10), "abstract_h": (11, "meta", True, "accent", False, 8),
                  "margin": (12, "body", False, "mute", True, 9), "margin_h": (10, "meta", True, "accent", False, 8),
                  "running": (10, "body", False, "mute", True, 8), "fig_label": (13, "meta", True, "accent", False, 9),
                  "sec_no": (40, "numeral", True, "accent", False, 20)},
  ```

- `NATIVE` gains `"journal"`.
- Extras:
  - `NATIVE_EXTRAS["journal"] = ("running", "authors", "abstract", "margin")`
  - `EXTRA_PAGES`: `"authors": ("cover",)`, `"abstract": ("cover",)`, `"margin": ("points",)`
- Ground and card:

  ```python
  def _ground_journal(slide, role, index):
      """An ordinary journal page: the running head (the deck's remembered words, this page's number) and the
      content rect under it — in REFERENCE inches."""
      import vl_native2 as v2
      K = rs._K[0]
      W, H = rs._canvas(slide)
      y = v2.jn_running(v2.kit_for("journal", slide), slide, {}) / K
      return (0.07 * W, y + 0.1, 0.86 * W, H - y - 0.7)
  ```

  Add `_card_journal = _card_for("journal")`.
- `_DISPLAY_NAMES["journal"] = "Journal article"`; `_RATIONALE["journal"] = "drawn around your figures: a running head, an abstract, numbered figures with captions, margin notes"`.
- `_SAMPLE_COPY_NATIVE["journal"]` uses the bundled illustrative figure:

  ```python
      "journal": [("cover", dict(kicker="Lab meeting", title="Learning to reconstruct undersampled cardiac MRI",
                                 authors="Author One · Author Two · Author Three",
                                 abstract="We ask whether a learned reconstruction keeps fine edges when far fewer measurements "
                                          "are taken, and how we would know.")),
                  ("image_text", dict(title="Reconstruction error across acceleration",
                                      body="Error as acceleration grows. Illustrative curves for this style sample, not results.",
                                      caption="Style sample — not data.", image=str(ASSETS / "figure" / "illustrative-curves.jpg"))),
                  ("points", dict(title="What we set out to test",
                                  items=[("The question", "Does the method keep edges at high acceleration?"),
                                         ("The method", "Retrospective undersampling of fully sampled scans."),
                                         ("The check", "Compare against the fully sampled reference, slice by slice.")],
                                  margin="Every figure in this deck is labelled with its source.")),
                  ("data", dict(number="8×", label="acceleration we aim to support",
                                note="A target for the study, stated before any result."))],
  ```

(b) Create the figure once, then commit the JPG. The run needs no network; matplotlib is already a dependency:

```bash
cd skills/slide-maker && mkdir -p assets/vl/figure && python3 - <<'PY'
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
x = np.array([2, 4, 6, 8, 10, 12])
fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=150)
for k, (lab, col) in enumerate((("Method A", "#1F5C46"), ("Method B", "#A57F2C"), ("Baseline", "#8A8A85"))):
    ax.plot(x, 0.02 * x ** (1.2 + 0.25 * k), marker="o", color=col, label=lab, lw=2)
ax.set_xlabel("Acceleration (×)"); ax.set_ylabel("Error (a.u.)")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.legend(frameon=False)
ax.text(0.98, 0.04, "illustrative — not data", transform=ax.transAxes, ha="right", color="#777", fontsize=10)
fig.tight_layout(); fig.savefig("assets/vl/figure/illustrative-curves.jpg", facecolor="white", pil_kwargs={"quality": 85})
PY
ls -la assets/vl/figure/illustrative-curves.jpg
```

(c) `vl_native2.py`: append

```python
# ═══════════════════════════════════ journal 学术期刊 ═══════════════════════════════════
def jn_running(k, slide, f):
    """The running head: the caller's running= (remembered for the deck), else the cover title when it fits one
    line at its floor, else no words — the page number at the right either way, a hairline under both. An explicit
    running= that does not fit is refused. Draws at once and returns the y under it."""
    W, H, s, o = ctx(k)
    explicit = text_of(f, "running")
    words = memo(k, f, "running", fallback=k.memo.get("_title"))
    y, h = 0.035 * H, 0.32 * s
    if words:
        try:
            _r, d = flow(k, slide, "running", (0.07 * W, y, 0.66 * W, h), [("running", words)])
            d()
        except vl.VLTextOverflow:
            if explicit:
                raise
    sz = vl.TYPE["journal"]["running"][0] * s
    dk.text(slide, 0.75 * W, y, 0.18 * W, h, [k.runs(str(page_no(slide)), sz, k.color("mute"), False, "numeral")],
            align=dk.PP_ALIGN.RIGHT)
    yl = y + h + 0.06 * s
    na.seg(slide, 0.07 * W, yl, 0.93 * W, yl, k.P["ink"], w=0.5)
    return yl + 0.25 * s


@register("journal", "cover", alts=2)
def _jn_cover(k, slide, f, image):
    """An article's first page: an accent bar at the left edge; kicker, title, subtitle and the caller's authors=;
    then a rule and the caller's abstract= under its label (in the abstract's own script). The block sits on the
    page's optical centre; never a running head on the cover."""
    W, H, s, o = ctx(k)
    t, ab = text_of(f, "title"), text_of(f, "abstract")
    if t:
        k.memo = dict(k.memo, _title=t)
    x, w = 0.10 * W, (0.78 if o == "land" else 0.82) * W
    lab_w = 0.15 * W if o == "land" else 0.0
    head = fields(f, ("kicker", "title", "subtitle", "authors"), ("kicker",))

    def plan(y0):
        out, ry = [], None
        r, d = flow(k, slide, "cover", (x, y0, w, H - 0.6 - y0), head, anchor="top")
        out.append((r, d))
        foot = max((v[1] + v[3] for v in r.values()), default=y0)
        if ab:
            ry = foot + 0.30 * s
            lab = caps(label("abstract", ab))
            if o == "land":
                lr, ld = flow(k, slide, "cover", (x, ry + 0.22 * s, lab_w - 0.2 * s, 0.5 * s), [("abstract_h", lab)])
                ar, ad = flow(k, slide, "cover", (x + lab_w, ry + 0.18 * s, w - lab_w, H - 0.6 - ry - 0.18 * s),
                              [("abstract", ab)], anchor="top")
            else:
                lr, ld = flow(k, slide, "cover", (x, ry + 0.2 * s, w, 0.4 * s), [("abstract_h", lab)])
                ay = max(v[1] + v[3] for v in lr.values()) + 0.1 * s
                ar, ad = flow(k, slide, "cover", (x, ay, w, H - 0.6 - ay), [("abstract", ab)], anchor="top")
            out += [(lr, ld), (ar, ad)]
            foot = max(v[1] + v[3] for v in ar.values())
        return out, foot, ry
    _o, foot, _ry = plan(0.08 * H)
    y0 = max(0.08 * H, (H - (foot - 0.08 * H)) / 2.0 - 0.1 * s) if alt() == 0 else 0.06 * H
    out, foot, ry = plan(y0)
    art = [lambda: dk.decorative(dk.box(slide, 0, 0, 0.035 * W, H, fill=k.P["accents"][0]), "the journal's edge bar")]
    if ry is not None:
        art.append(lambda: na.seg(slide, x, ry, x + w, ry, k.P["ink"], w=0.5))
    rects = {}
    for r, _d in out:
        rects.update(r)
    _run_all(art + [d for _r, d in out])
    return rects


@register("journal", "section", alts=2)
def _jn_section(k, slide, f, image):
    """A section heading: § and the caller's number (a numeral or roman numeral; other words are set as given) in the
    accent, then kicker and title, a rule under them."""
    W, H, s, o = ctx(k)
    top = jn_running(k, slide, f)
    num = text_of(f, "number")
    lab = ("§ " + num) if num and re.fullmatch(r"[0-9]+(\.[0-9]+)*|[IVXLCivxlc]+", num) else num
    items = ([("sec_no", lab)] if lab else []) + fields(f, ("kicker", "title"), ("kicker",))
    r, d = flow(k, slide, "section", (0.10 * W, top, 0.80 * W, H - 0.6 - top - (0.4 if alt() == 0 else 0.2) * s), items,
                anchor="middle")
    yb = max(v[1] + v[3] for v in r.values()) + 0.25 * s
    _run_all([lambda: na.seg(slide, 0.10 * W, yb, 0.90 * W, yb, k.P["ink"], w=0.6), d])
    return r


@register("journal", "image_text", alts=2)
def _jn_figure(k, slide, f, image):
    """The figure page: its title above; the caller's figure WHOLE (contain, never cropped); beside it the figure's
    label (kicker=, else Figure n counted over the deck's figure pages, in the page's own script), its caption (body=)
    and, under a hairline, the source line (caption=)."""
    W, H, s, o = ctx(k)
    top = jn_running(k, slide, f)
    n = k.memo.get("_fig", 0) + 1
    k.memo = dict(k.memo, _fig=n)
    lab = text_of(f, "kicker") or label("figure", text_of(f, "title"), text_of(f, "body")).format(n)
    r, d = flow(k, slide, "image_text", (0.07 * W, top, 0.86 * W, 0.16 * H), fields(f, ("title",)), anchor="top")
    rects, draws, art = dict(r), [d], []
    ty = max((v[1] + v[3] for v in r.values()), default=top) + 0.25 * s
    bottom = H - 0.6
    if o == "land":
        img = (0.07 * W, ty, (0.52 if alt() == 0 else 0.46) * W, bottom - ty)
        cx0 = img[0] + img[2] + 0.45 * s
        col = (cx0, ty, 0.93 * W - cx0, bottom - ty)
    else:
        img = (0.07 * W, ty, 0.86 * W, (bottom - ty) * (0.56 if alt() == 0 else 0.48))
        cy0 = img[1] + img[3] + 0.3 * s
        col = (0.07 * W, cy0, 0.86 * W, bottom - cy0)
    src = text_of(f, "caption")
    src_h = 0.9 * s if src else 0.0
    main = [("fig_label", caps(lab))] + fields(f, ("body",))
    r, d = flow(k, slide, "image_text", (col[0], col[1], col[2], col[3] - src_h), main, anchor="top")
    rects.update(r); draws.append(d)
    if src:
        yl = col[1] + col[3] - src_h
        sr, sd = flow(k, slide, "image_text", (col[0], yl + 0.15 * s, col[2], src_h - 0.15 * s), [("caption", src)])
        rects.update(sr); draws.append(sd)
        art.append(lambda: na.seg(slide, col[0], yl, col[0] + col[2], yl, k.P["ink"], w=0.4))
    path, alt_txt, slot = vl._resolve(k, image[0] if isinstance(image, (list, tuple)) else image)
    pic = dk.picture(slide, path, *img, fit="contain", alt=alt_txt)
    if slot:
        dk._compose_tag(pic, gen=slot)
    _run_all(art + draws)
    return rects


@register("journal", "points", alts=2)
def _jn_points(k, slide, f, image):
    """Numbered findings (1, 2, 3 in the accent), each a bold head over its line; the caller's margin= beside them
    past an accent rule under its Note label (under the list in portrait or for long copy)."""
    W, H, s, o = ctx(k)
    top = jn_running(k, slide, f)
    pts = points_of(f.get("items"))
    n = len(pts)
    mg = text_of(f, "margin")
    r, d = flow(k, slide, "points", (0.07 * W, top, 0.86 * W, 0.18 * H), fields(f, ("kicker", "title"), ("kicker",)))
    rects, draws, art = dict(r), [d], []
    ty = max((v[1] + v[3] for v in r.values()), default=top) + 0.35 * s
    bottom, list_bottom = H - 0.6, H - 0.6
    side = bool(mg) and o == "land" and alt() == 0
    lw = (0.62 if side else 0.86) * W
    if mg:
        if side:
            mx = 0.07 * W + lw + 0.5 * s
            mcol = (mx + 0.2 * s, ty, 0.93 * W - mx - 0.2 * s, bottom - ty)
            art.append(lambda: na.seg(slide, mx, ty, mx, bottom, k.P["text_accents"][0], w=0.75))
        else:
            mh = 1.3 * s
            mcol = (0.07 * W + 0.2 * s, bottom - mh, 0.86 * W - 0.2 * s, mh)
            art.append(lambda: na.seg(slide, 0.07 * W, bottom - mh, 0.07 * W, bottom, k.P["text_accents"][0], w=0.75))
            list_bottom = bottom - mh - 0.3 * s
        _mr, md = flow(k, slide, "points", mcol, [("margin_h", caps(label("note", mg))), ("margin", mg)], anchor="top")
        draws.append(md)
    slot = (list_bottom - ty) / n
    nw = 0.07 * W
    for i, (hd, ln) in enumerate(pts):
        y = ty + i * slot
        _nr, nd = flow(k, slide, "points", (0.07 * W, y, nw, slot), [("item_no", str(i + 1))], anchor="top")
        _tr, td_ = flow(k, slide, "points", (0.07 * W + nw, y, lw - nw, slot - 0.1 * s),
                        [(x_, t) for x_, t in (("item_head", hd), ("item_line", ln)) if t], anchor="top")
        draws += [nd, td_]
    _run_all(art + draws)
    return rects


@register("journal", "quote", alts=2)
def _jn_quote(k, slide, f, image):
    """A block quotation, indented behind an accent rule, its source after an em dash."""
    W, H, s, o = ctx(k)
    top = jn_running(k, slide, f)
    a = text_of(f, "attribution")
    x = (0.16 if (o == "land" and alt() == 0) else 0.10) * W
    items = fields(f, ("quote",)) + ([("attribution", "— " + a)] if a else [])
    r, d = flow(k, slide, "quote", (x + 0.35 * s, top + 0.3 * s, 0.92 * W - x - 0.35 * s, H - 0.6 - top - 0.3 * s), items,
                anchor="middle")
    y0, y1 = min(v[1] for v in r.values()), max(v[1] + v[3] for v in r.values())
    _run_all([lambda: na.seg(slide, x, y0, x, y1, k.P["text_accents"][0], w=2.0), d])
    return r


@register("journal", "data", alts=2)
def _jn_data(k, slide, f, image):
    """The one number in a tinted panel, its label and note beside it (under it in portrait)."""
    W, H, s, o = ctx(k)
    top = jn_running(k, slide, f)
    num = text_of(f, "number")
    avail = H - 0.6 - (top + 0.3 * s)
    ph = min(avail, 0.62 * H)
    px, py, pw = 0.07 * W, top + 0.3 * s + (avail - ph) / 2.0, 0.86 * W
    rects, draws = {}, []
    if o == "land" and alt() == 0:
        nrect, col, anchor = (px + 0.4 * s, py, pw * 0.42, ph), (px + pw * 0.48, py + 0.3 * s, pw * 0.48, ph - 0.6 * s), "middle"
    else:
        nrect = (px + 0.3 * s, py + 0.2 * s, pw - 0.6 * s, ph * 0.45)
        col, anchor = (px + 0.3 * s, py + ph * 0.5, pw - 0.6 * s, ph * 0.46), "top"
    if num:
        r, d = flow(k, slide, "data", nrect, [("number", num)], anchor="middle", align="c")
        rects.update(r); draws.append(d)
    r, d = flow(k, slide, "data", col, fields(f, ("label", "note")), anchor=anchor)
    rects.update(r); draws.append(d)
    _run_all([lambda: dk.box(slide, px, py, pw, ph, fill=k.P["panel"])] + draws)
    return rects


@register("journal", "closing", alts=2)
def _jn_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    top = jn_running(k, slide, f)
    r, d = flow(k, slide, "closing", (0.10 * W, top, (0.70 if o == "land" and alt() == 0 else 0.80) * W, H - 0.6 - top),
                fields(f, ("title", "line")), anchor="middle")
    d()
    return r
```

(d) `directions_diversity.py`: append `"journal"` to `NATIVE_LANGS`, and add the message clause "journal (research talk, lab meeting, paper, defence)".

- [ ] **Step 5: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `N passed, 0 failed`.

- [ ] **Step 6: Build, render and LOOK at the samples**

Use the same commands as Task 4 Step 5, with `journal` and the stems `journal`, `journal-green`. Read both JPGs and compare them with `~/Desktop/slide-maker 新模板样张/sheets/journal.jpg`. Check that:
- the cover block is centred;
- the figure is whole, with its label, caption and source line;
- the margin note sits past its rule;
- the data panel centres its number;
- the running head is on every page except the cover.

- [ ] **Step 7: Run the neighbouring suites** (the same four as Task 4 Step 6). Expected: all `0 failed`.

- [ ] **Step 8: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native2.py \
  skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/tests/test_native_languages_p4.py \
  skills/slide-maker/assets/vl/figure/illustrative-curves.jpg skills/slide-maker/assets/vl/samples/journal.jpg \
  skills/slide-maker/assets/vl/samples/journal-green.jpg skills/slide-maker/assets/vl/samples/manifest.json
git commit -m "native languages: journal (学术期刊) — running head, abstract, numbered whole figures, margin notes"
```

---
### Task 7: `tally` 数据账本

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py`
  - `LANGS`, `VARIANTS`, `TYPE`, `NATIVE` (+ `"tally"`)
  - `NATIVE_EXTRAS["tally"] = ("tags", "total")`
  - `EXTRA_PAGES` (+ `"total": ("data",)`; `"tags"` exists from Task 5)
  - `_ground_tally`, `_card_tally`, `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Modify: `skills/slide-maker/scripts/vl_native2.py` (the tally section)
- Modify: `skills/slide-maker/scripts/directions_diversity.py`
- Create: `assets/vl/samples/tally.jpg`, `tally-night.jpg`; Modify: `manifest.json`
- Test: `skills/slide-maker/tests/test_native_languages_p4.py` (append)

**Interfaces:**
- Consumes:
  - Task 2: `grid_background`, `chip`, `chip_width`, `share_bar`, `seg`
  - Task 3 helpers
- Produces:
  - `vl_native2.chip_size(k, text, max_w, field) -> float|None`
  - `vl_native2.tl_chip(k, slide, x, y, text, max_w, *, field="tag", fill=None) -> (x, y, w, h)|None`
  - `vl_native2.num_value(t) -> float|None`
  - seven `@register("tally", page, alts=2)` compositions

- [ ] **Step 1: Write the failing tests.** Append:

```python
# ── tally 数据账本 ──
EXTRAS["tally"] = lambda lang, n: {"points": {"tags": ["A{}".format(i + 1) for i in range(n)]},
                                   "data": {"total": "12"}}
check("tally" in vl.NATIVE and set(vl.VARIANTS["tally"]) == {"light", "night"}, "tally: two grounds")
assert_palettes("tally")
for g, V in vl.VARIANTS["tally"].items():
    p = V["palette"]
    check(cr(p["chip_ink"], p["lime"]) >= 4.5, "tally/{}: pill ink on the lime pill".format(g))
    check(cr(p["text_accents"][0], p["track"]) >= 3.0, "tally/{}: the bar's fill reads against its track (3:1, a graphic)".format(g))
assert_matrix("tally")
import vl_native2 as v2
check([v2.num_value(t) for t in ("12", "1,250", "98.6%", " 40 ", "$4.2M", "3–5", "1,25", "")] ==
      [12.0, 1250.0, 98.6, 40.0, None, None, None, None], "tally: num_value reads plain and percent numbers only")
# total= draws the right share, or is refused by name (Review Focus 5)
for num, total, frac in (("12", "40", 0.30), ("1,250", "5,000", 0.25), ("98.6%", "100%", 0.986)):
    prs, k = use("tally")
    s = k.new_slide(); k.data(s, number=num, label="of the whole", total=total)
    bars = sorted((sh.width / EMU for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='roundRect']")
                   and sh.height / EMU < 0.3 and sh.width / EMU > 0.3), reverse=True)
    check(len(bars) == 2 and abs(bars[1] / bars[0] - frac) < 0.01,
          "tally: {} of {} fills {:.0%} of the bar ({})".format(num, total, frac, [round(b, 2) for b in bars]))
    tt = [sh.text_frame.text for sh in texts(s)]
    check(num in tt and total in tt, "tally: both numbers stand at the bar's ends")
for num, total in (("$4.2M", "10"), ("50", "40"), ("12", "0"), ("12%", "40")):
    prs, k = use("tally")
    try:
        k.data(k.new_slide(), number=num, label="x", total=total)
        check(False, "tally: number={!r} total={!r} is refused".format(num, total))
    except ValueError as e:
        check("total" in str(e), "tally: number={!r} total={!r} is refused by name".format(num, total))
prs, k = use("tally")
s = k.new_slide(); k.data(s, number="$4.2M", label="budget")
check(not [sh for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='roundRect']")], "tally: no total → no bar")
# ledger rows: a rule above each row and one closing the ledger; tags in one-line pills inside the page
for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333), (7.5, 7.5)):
    prs, k = use("tally", W, H)
    s = k.new_slide()
    k.points(s, kicker="Q3 review", title="Three lines on the ledger", tags=["MEMBERS", "LOANS", "REPAIRS"],
             items=[("New members joined", "Mostly through word of mouth"), ("Tools went out on loan", "Drills and ladders"),
                    ("Items came back repaired", None)])
    check(len(segs_of(s)) == 4, "tally {}x{}: three rows, four rules ({})".format(W, H, len(segs_of(s))))
    pills = [sh for sh in texts(s) if sh.text_frame.text in ("MEMBERS", "LOANS", "REPAIRS", "Q3 review")]
    check(len(pills) == 4 and all(p.text_frame.word_wrap is False for p in pills), "tally {}x{}: tags and kicker in pills".format(W, H))
    hit = [g for g in segs_of(s) for sh in texts(s) if crosses(g, rect_of(sh))]
    check(not hit, "tally {}x{}: no ledger rule crosses words".format(W, H))
# a kicker too long for a pill is set as plain words, never dropped; a tag too long for its pill is refused by name
prs, k = use("tally")
s = k.new_slide()
LONGK = "A quarterly review of the neighbourhood lending library network and all its volunteers across the city"
k.cover(s, kicker=LONGK, title="The lending library")
check(any(sh.text_frame.text == LONGK for sh in texts(s)), "tally: a long kicker is kept as plain words")
try:
    k.points(k.new_slide(), title="x", items=["a", "b"], tags=["x" * 120, "y"])
    check(False, "tally: a tag too long for its pill is refused")
except vl.VLTextOverflow as e:
    check("tag" in str(e), "tally: a tag too long for its pill is refused by name")
# the grid is the background picture; an ordinary page gets it
import register_surface as rs
prs, k = use("tally")
s = k.new_slide()
rect = rs.ground(s, k.name, role="content", index=2)
check(s._element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip") is not None and rect[2] > 5,
      "tally: an ordinary page is on the grid")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `KeyError: 'tally'`.

- [ ] **Step 3: Implement.**

(a) `visual_languages.py`, the tables.
- `LANGS`:

  ```python
      "tally": {
          "palette": {"ground": "FFFFFF", "ink": "0E0E10", "mute": "5A5F6B", "panel": "F4F6FA",
                      "accents": ["2438F0", "C6F432"], "text_accents": ["2438F0"],
                      "lime": "C6F432", "chip_ink": "0E0E10", "grid_ink": "1E2A60", "track": "E7EAF1"},
          "fonts": {"both": {"display": "Arial Black", "body": "Arial", "numeral": "Arial Black"},
                    "mac": {"display": "Arial Black", "body": "Helvetica Neue", "numeral": "Arial Black"}},
          "ea": {"display": "sans", "body": "sans"}, "ea_heavy": True, "grain": 0, "frames": ["rect"],
          "forbids": (), "cover": "low-left", "skeleton": "split"},
  ```

- `VARIANTS`:

  ```python
      "tally": {
          "light": {"label": "white grid", "label_zh": "白网格版", "grain": 0, "palette": LANGS["tally"]["palette"]},
          "night": {"label": "night ledger", "label_zh": "夜间账本版", "grain": 0,
                    "palette": {"ground": "0F1222", "ink": "F2F4FA", "mute": "A5ACC4", "panel": "1A1F38",
                                "accents": ["7C89FF", "C6F432"], "text_accents": ["7C89FF"],
                                "lime": "C6F432", "chip_ink": "0E0E10", "grid_ink": "8090D0", "track": "2A3150"}}},
  ```

- `TYPE`:

  ```python
      "tally": {"kicker": (12, "body", True, "ink", False, 9), "title": (60, "display", False, "ink", False, 28),
                "subtitle": (20, "body", False, "mute", False, 12), "body": (17, "body", False, "ink", False, 11),
                "mark": (90, "display", False, "accent", False, 36), "quote": (38, "display", False, "ink", False, 18),
                "attribution": (12, "body", True, "ink", False, 9), "number": (200, "numeral", False, "accent", False, 60),
                "label": (26, "body", True, "ink", False, 14), "note": (15, "body", False, "mute", False, 10),
                "caption": (12, "body", False, "mute", False, 9), "line": (20, "body", False, "mute", False, 12),
                "item_head": (26, "body", True, "ink", False, 13), "item_line": (17, "body", False, "mute", False, 10),
                "item_no": (50, "display", False, "accent", False, 24), "tag": (12, "body", True, "ink", False, 9)},
  ```

- `NATIVE` gains `"tally"`.
- Extras: `NATIVE_EXTRAS["tally"] = ("tags", "total")`; `EXTRA_PAGES["total"] = ("data",)`.
- Ground and card:

  ```python
  def _ground_tally(slide, role, index):
      W, H = rs._canvas(slide)
      return (0.55, 0.55, W - 1.1, H - 1.1)          # the grid is the page's background (new_slide paints it)
  ```

  Add `_card_tally = _card_for("tally")`.
- `_DISPLAY_NAMES["tally"] = "Data tally"`; `_RATIONALE["tally"] = "drawn, no pictures: a fine grid, heavy type, pill tags, one giant number with its share bar"`.
- `_SAMPLE_COPY_NATIVE["tally"]`:

  ```python
      "tally": [("cover", dict(kicker="Q3 review", title="The lending library, quarter three",
                               subtitle="Members, loans and repairs across the network")),
                ("points", dict(title="Three lines on the ledger", tags=["Members", "Loans", "Repairs"],
                                items=[("New members joined", "Mostly through word of mouth"),
                                       ("Tools went out on loan", "Drills and ladders led the list"),
                                       ("Items came back repaired", "Fixed at the monthly evening")])),
                ("quote", dict(quote="Count what people borrow, not what we own.", attribution="Library principle")),
                ("data", dict(number="12", label="of 40 neighbourhoods now have a shelf", note="A target of 20 by next year.",
                              total="40"))],
  ```

(b) `vl_native2.py`: append

```python
# ═══════════════════════════════════ tally 数据账本 ═══════════════════════════════════
def _tl_ground(k, slide):
    na.grid_background(slide, base=k.P["ground"], ink=k.P["grid_ink"], step=0.25, major=4)


GROUNDS["tally"] = _tl_ground


def chip_size(k, text, max_w, field):
    """The size (pt) a pill of `text` takes to fit `max_w` — the field's size, shrinking toward its floor — or None."""
    W, H, s, o = ctx(k)
    base, role, _b, _c, _i, floor = vl.TYPE[k.name][field]
    sz, face = base * s, k.face(role)
    while na.chip_width(text, sz, face) > max_w and sz > floor * s + 1e-6:
        sz = max(floor * s, sz * 0.92)
    return sz if na.chip_width(text, sz, face) <= max_w else None


def tl_chip(k, slide, x, y, text, max_w, *, field="tag", fill=None):
    """A lime pill (or `fill`) for the caller's words, the darker or lighter ink by contrast. None when it cannot fit."""
    sz = chip_size(k, text, max_w, field)
    if sz is None:
        return None
    fill = fill or k.P["lime"]
    ink = k.P["chip_ink"] if vl._contrast(k.P["chip_ink"], fill) >= vl._contrast("FFFFFF", fill) else "FFFFFF"
    role = vl.TYPE[k.name][field][1]
    return na.chip(slide, x, y, text, size=sz, fill=fill, ink=ink, face=k.face(role), ea_face=k.ea_face(role, text))


def _tl_kicker(k, slide, f, x, y, max_w):
    """The kicker as a pill; a kicker too long for one is set as plain words — still the caller's, never dropped.
    Draws at once; returns its foot."""
    t = text_of(f, "kicker")
    if not t:
        return y
    c = tl_chip(k, slide, x, y, t, max_w, field="kicker")
    if c:
        return y + c[3]
    r, d = flow(k, slide, "kicker", (x, y, max_w, 1.0 * ctx(k)[2]), [("kicker", t)])
    d()
    return max(v[1] + v[3] for v in r.values())


def num_value(t):
    """A plain or percent number ("12", "1,250", "98.6%") as a float; None for anything else ("$4.2M", "3–5")."""
    m = re.fullmatch(r"\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(\.[0-9]+)?\s*%?\s*", t or "")
    return float((m.group(1) + (m.group(2) or "")).replace(",", "")) if m else None


@register("tally", "cover", alts=2)
def _tl_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = 0.07 * W, 0.86 * W
    y = _tl_kicker(k, slide, f, x, (0.16 if alt() == 0 else 0.07) * H, w) + 0.25 * s
    r, ds = stack(k, slide, "cover", x, (0.78 if o == "land" else 0.86) * W, y, H - 0.6,
                  [(fields(f, ("title",)), 0.70 * s), (fields(f, ("subtitle",)), 0.0)], anchor="top")
    art = []
    if "title" in r:
        yb = r["title"][1] + r["title"][3] + 0.30 * s
        art.append(lambda: dk.box(slide, x, yb, 2.4 * s, 0.09 * s, fill=k.P["text_accents"][0], round=True, r=0.045 * s))
    _run_all(art + ds)
    return r


@register("tally", "section", alts=2)
def _tl_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    rects, draws = {}, []
    if o == "land" and alt() == 0:
        nrect, col = (0.07 * W, 0.18 * H, 0.38 * W, 0.64 * H), (0.50 * W, 0.22 * H, 0.43 * W, 0.60 * H)
    else:
        nrect, col = (0.07 * W, 0.10 * H, 0.86 * W, 0.34 * H), (0.07 * W, 0.48 * H, 0.86 * W, 0.42 * H)
    if num:
        r, d = flow(k, slide, "section", nrect, [("number", num)], anchor="middle", start={"number": 150 * s})
        rects.update(r); draws.append(d)
    ky = _tl_kicker(k, slide, f, col[0], col[1], col[2]) + (0.2 * s if text_of(f, "kicker") else 0.0)
    r, d = flow(k, slide, "section", (col[0], ky, col[2], col[1] + col[3] - ky), fields(f, ("title",)), anchor="top")
    rects.update(r); draws.append(d)
    _run_all(draws)
    return rects


@register("tally", "image_text", alts=2)
def _tl_image_text(k, slide, f, image):
    """The caller's picture under a hairline frame; kicker pill, title, body and caption beside it."""
    W, H, s, o = ctx(k)
    if o == "land":
        img = (0.07 * W, 0.12 * H, (0.50 if alt() == 0 else 0.44) * W, 0.76 * H)
        cx0 = img[0] + img[2] + 0.5 * s
        col = (cx0, 0.12 * H, 0.93 * W - cx0, 0.76 * H)
    else:
        img = (0.07 * W, 0.07 * H, 0.86 * W, (0.40 if alt() == 0 else 0.32) * H)
        cy0 = img[1] + img[3] + 0.4 * s
        col = (0.07 * W, cy0, 0.86 * W, H - 0.6 - cy0)
    y = _tl_kicker(k, slide, f, col[0], col[1], col[2]) + (0.2 * s if text_of(f, "kicker") else 0.0)
    r, d = flow(k, slide, "image_text", (col[0], y, col[2], col[1] + col[3] - y), fields(f, ("title", "body", "caption")),
                anchor="top")
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    frame = dk.box(slide, *img, fill=None, line=dk._as_rgb(k.P["ink"]), line_w=0.75)
    dk.decorative(frame, "a hairline frame around the picture")
    d()
    return r


@register("tally", "points", alts=2)
def _tl_points(k, slide, f, image):
    """Ledger rows: 01, 02 … in the accent, the point's head and line, the caller's tag in a pill at the right (under
    the words when the pills are wide); a rule above each row and one closing the ledger. A tag too long for its pill
    is refused by name, never dropped."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    tags = tags_of(f, n, "tally")
    x, w = 0.07 * W, 0.86 * W
    y = _tl_kicker(k, slide, f, x, 0.07 * H, w) + 0.15 * s
    r, d = flow(k, slide, "points", (x, y, w, 0.18 * H), fields(f, ("title",)), anchor="top")
    rects, draws, art = dict(r), [d], []
    top = max((v[1] + v[3] for v in r.values()), default=y) + 0.40 * s
    bottom = H - 0.6
    pitch = (bottom - top) / n
    tag_sz = vl.TYPE["tally"]["tag"][0] * s
    tw = (max(na.chip_width(t, tag_sz, k.face("body")) for t in tags) + 0.3 * s) if tags else 0.0
    beside = bool(tags) and tw <= 0.30 * w
    nw = (1.7 if alt() == 0 else 1.1) * s
    for i, (hd, ln) in enumerate(pts):
        ry = top + i * pitch
        art.append(lambda ry=ry: na.seg(slide, x, ry - 0.12 * s, x + w, ry - 0.12 * s, k.P["ink"], w=0.6, alpha=0.5))
        _nr, nd = flow(k, slide, "points", (x, ry, nw, pitch - 0.24 * s), [("item_no", "{:02d}".format(i + 1))],
                       anchor="middle", start={"item_no": (50 if alt() == 0 else 34) * s})
        tcol = (x + nw + 0.2 * s, ry, w - nw - 0.2 * s - (tw if beside else 0.0), pitch - 0.24 * s)
        if tags and not beside:
            tcol = (tcol[0], tcol[1], tcol[2], tcol[3] - 0.45 * s)
        _tr, td_ = flow(k, slide, "points", tcol, [(x_, t) for x_, t in (("item_head", hd), ("item_line", ln)) if t],
                        anchor="middle")
        draws += [nd, td_]
        if tags:
            mw = (tw - 0.3 * s) if beside else tcol[2]
            if chip_size(k, tags[i], mw, "tag") is None:
                raise vl.VLTextOverflow("tally.points(): the tag {!r} does not fit its pill even at the floor size — "
                                        "shorten it".format(tags[i][:40]))
            ch = tag_sz / 72.0 * 1.9
            cx_, cy_ = (x + w - tw + 0.3 * s, ry + (pitch - 0.24 * s - ch) / 2.0) if beside else (tcol[0], tcol[1] + tcol[3] + 0.1 * s)
            draws.append(lambda t=tags[i], cx_=cx_, cy_=cy_, mw=mw: tl_chip(k, slide, cx_, cy_, t, mw))
    yl = top + n * pitch - 0.12 * s
    art.append(lambda: na.seg(slide, x, yl, x + w, yl, k.P["ink"], w=0.6, alpha=0.5))
    _run_all(art + draws)
    return rects


@register("tally", "quote", alts=2)
def _tl_quote(k, slide, f, image):
    """The quote in heavy type behind a rounded accent bar; the source in a pill (as words when too long for one)."""
    W, H, s, o = ctx(k)
    x = (0.10 if alt() == 0 else 0.06) * W
    a = text_of(f, "attribution")
    col = (x + 0.45 * s, 0.14 * H, 0.90 * W - x - 0.45 * s, H - 0.6 - 0.14 * H - (0.9 * s if a else 0.0))
    r, d = flow(k, slide, "quote", col, fields(f, ("quote",)), anchor="middle")
    rects, draws = dict(r), [d]
    qt = min((v[1] for v in r.values()), default=col[1])
    qb = max((v[1] + v[3] for v in r.values()), default=col[1])
    art = [lambda: dk.box(slide, x, qt, 0.10 * s, max(0.2, qb - qt), fill=k.P["text_accents"][0], round=True, r=0.05 * s)]
    if a:
        ay = qb + 0.3 * s
        if chip_size(k, a, col[2], "attribution") is not None:
            draws.append(lambda: tl_chip(k, slide, col[0], ay, a, col[2], field="attribution"))
        else:
            r2, d2 = flow(k, slide, "quote", (col[0], ay, col[2], H - 0.6 - ay), [("attribution", a)])
            rects.update(r2); draws.append(d2)
    _run_all(art + draws)
    return rects


@register("tally", "data", alts=2)
def _tl_data(k, slide, f, image):
    """The giant number, its label and note — and, when the caller gives total=, a share bar: the number's share of
    the total with both numbers at its ends. A total the number cannot be read against is refused, never guessed."""
    W, H, s, o = ctx(k)
    num, total = text_of(f, "number"), text_of(f, "total")
    frac = None
    if total is not None:
        v, t = num_value(num), num_value(total)
        if v is None or t is None or t <= 0:
            raise ValueError("tally.data(): total= draws a share bar, so number= and total= must both be plain numbers "
                             "(12, 1,250, 98.6%) — got number={!r}, total={!r}".format(num, total))
        if ("%" in (num or "")) != ("%" in total):
            raise ValueError("tally.data(): number= and total= must both be percentages or neither — got {!r} and "
                             "total={!r}".format(num, total))
        if v > t:
            raise ValueError("tally.data(): the number {!r} is larger than total={!r} — a share cannot exceed its whole"
                             .format(num, total))
        frac = v / t
    x, w = 0.07 * W, 0.86 * W
    bottom = H - 0.6 - (1.0 * s if frac is not None else 0.0)
    rects, draws, art = {}, [], []
    if o == "land" and alt() == 0:
        nrect, col, anchor = (x, 0.12 * H, 0.52 * W, bottom - 0.12 * H), (0.62 * W, 0.18 * H, 0.31 * W, bottom - 0.18 * H), "middle"
    else:
        hh = bottom - 0.08 * H
        nrect, col, anchor = (x, 0.08 * H, w, hh * 0.5), (x, 0.08 * H + hh * 0.52, w, hh * 0.48), "top"
    if num:
        r, d = flow(k, slide, "data", nrect, [("number", num)], anchor="middle")
        rects.update(r); draws.append(d)
    r, d = flow(k, slide, "data", col, fields(f, ("label", "note")), anchor=anchor)
    rects.update(r); draws.append(d)
    if frac is not None:
        by, sz = bottom + 0.25 * s, vl.TYPE["tally"]["tag"][0] * s
        art.append(lambda: na.share_bar(slide, x, by, w, frac, track=k.P["track"], fill=k.P["text_accents"][0], h=0.16 * s))
        art.append(lambda: dk.text(slide, x, by + 0.25 * s, w / 2, 0.35 * s, [k.runs(num, sz, k.color("mute"), True)]))
        art.append(lambda: dk.text(slide, x + w / 2, by + 0.25 * s, w / 2, 0.35 * s, [k.runs(total, sz, k.color("mute"), True)],
                                   align=dk.PP_ALIGN.RIGHT))
    _run_all(art + draws)
    return rects


@register("tally", "closing", alts=2)
def _tl_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    x = 0.07 * W
    col = (x, 0.20 * H, (0.78 if o == "land" else 0.86) * W, 0.60 * H) if alt() == 0 else (x, 0.08 * H, 0.86 * W, 0.78 * H)
    r, d = flow(k, slide, "closing", col, fields(f, ("title", "line")), anchor="middle")
    yb = max(v[1] + v[3] for v in r.values()) + 0.35 * s
    _run_all([d, lambda: dk.box(slide, x, yb, 2.4 * s, 0.09 * s, fill=k.P["text_accents"][0], round=True, r=0.045 * s)])
    return r
```

(c) `directions_diversity.py`: append `"tally"` to `NATIVE_LANGS`, and add the message clause "tally (metrics, quarterly review, operations, growth)".

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `N passed, 0 failed`.

- [ ] **Step 5: Build, render and LOOK at the samples**

Use the same commands as Task 4 Step 5, with `tally` and the stems `tally`, `tally-night`. Read both JPGs and compare them with `~/Desktop/slide-maker 新模板样张/sheets/ledger.jpg` (the look-dev's name for this language). Check that:
- the grid is faint;
- the pills are one line and inside the page;
- the rows fill the page with rules between them;
- the share bar is 30% (12 of 40), with 12 and 40 at its ends.

- [ ] **Step 6: Run the neighbouring suites** (the same four as Task 4 Step 6). Expected: all `0 failed`.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native2.py \
  skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/tests/test_native_languages_p4.py \
  skills/slide-maker/assets/vl/samples/tally.jpg skills/slide-maker/assets/vl/samples/tally-night.jpg \
  skills/slide-maker/assets/vl/samples/manifest.json
git commit -m "native languages: tally (数据账本) — grid, pills, ledger rows, a giant number with its share of the caller's total"
```

---
### Task 8: `chalkboard` 黑板报

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py`
  - `LANGS`, `VARIANTS`, `TYPE`, `NATIVE` (+ `"chalkboard"`)
  - `NATIVE_EXTRAS["chalkboard"] = ("doodle", "ordered")`
  - `EXTRA_PAGES` (+ `"doodle": ("cover", "closing")`, `"ordered": ("points",)`)
  - `_ground_chalkboard`, `_card_chalkboard`, `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Modify: `skills/slide-maker/scripts/vl_native2.py` (the chalkboard section)
- Modify: `skills/slide-maker/scripts/directions_diversity.py`
- Create: `assets/vl/samples/chalkboard.jpg`, `chalkboard-slate.jpg`; Modify: `manifest.json`
- Test: `skills/slide-maker/tests/test_native_languages_p4.py` (append)

**Interfaces:**
- Consumes:
  - Task 2: `board_frame`, `chalk_box`, `chalk_ellipse`, `chalk_underline`, `chalk_arrow`, `chalk_path`, `chip_width`, `_radial`
  - Task 3: `stack`, `fields`, `meet`
  - `icons.icon_png(spec, out_png, *, color, px)`
  - `dk.icon(slide, png, x, y, size, *, alt) -> picture`
- Produces: seven `@register("chalkboard", page, alts=2)` compositions; `vl_native2.ink_w(k, field, text, size) -> float`

- [ ] **Step 1: Write the failing tests.** Append:

```python
# ── chalkboard 黑板报 ──
EXTRAS["chalkboard"] = lambda lang, n: {"points": {"ordered": True}}
check("chalkboard" in vl.NATIVE and set(vl.VARIANTS["chalkboard"]) == {"light", "slate"}, "chalkboard: two grounds")
assert_palettes("chalkboard")
assert_matrix("chalkboard")
def arrows(s):
    """Chalk arrow heads: a one-pass three-point chalk path (a box is five points, an underline eleven)."""
    return [sh for sh in s.shapes if sh._element.xpath(".//a:custGeom") and len(sh._element.xpath(".//a:lnTo")) == 2]
STEPS = [("Catch the light", "Chlorophyll traps its energy"), ("Take in water and CO₂", "Roots drink, leaves breathe in"),
         ("Make sugar and oxygen", "Sugar stays, oxygen goes out")]
for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333), (7.5, 7.5)):
    for ordered in (False, True):
        prs, k = use("chalkboard", W, H)
        s = k.new_slide()
        k.points(s, title="Three things a leaf does", items=STEPS, ordered=ordered)
        check(len(arrows(s)) == (2 if ordered else 0),
              "chalkboard {}x{} ordered={}: arrows only when the caller says the points are in order ({})".format(
                  W, H, ordered, len(arrows(s))))
        # every point's words sit inside its own chalk box (a box is a 5-point path: its bbox is the box)
        boxes = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:custGeom") and len(sh._element.xpath(".//a:lnTo")) == 4]
        heads = [rect_of(sh) for sh in texts(s) if sh.text_frame.text in [h for h, _l in STEPS]]
        inside = [any(b[0] - 0.05 <= t[0] and t[0] + t[2] <= b[0] + b[2] + 0.05 and b[1] - 0.05 <= t[1] and
                      t[1] + t[3] <= b[1] + b[3] + 0.05 for b in boxes) for t in heads]
        check(len(heads) == 3 and all(inside), "chalkboard {}x{}: each head sits inside its chalk box ({})".format(W, H, inside))
try:
    prs, k = use("chalkboard")
    k.points(k.new_slide(), title="x", items=["a", "b"], ordered="yes")
    check(False, "chalkboard: ordered= that is not a bool is refused")
except TypeError:
    check(True, "chalkboard: ordered= that is not a bool is refused")
# no doodle without doodle=; with it, one picture, clear of every word
prs, k = use("chalkboard")
s = k.new_slide(); k.cover(s, kicker="Science · lesson 3", title="How photosynthesis works", subtitle="A leaf is a tiny factory")
check(not [sh for sh in s.shapes if sh.shape_type == 13], "chalkboard: no doodle= → no drawing on the cover")
s = k.new_slide(); k.cover(s, kicker="Science · lesson 3", title="How photosynthesis works", doodle="lucide:sun")
pics = [rect_of(sh) for sh in s.shapes if sh.shape_type == 13]
check(len(pics) == 1 and not any(v2.meet(pics[0], rect_of(t)) for t in texts(s)), "chalkboard: the doodle is drawn, clear of the words")
# the kicker's chalk box hugs its words (one line: measured), and the eraser smudges keep clear of every word
for W, H in ((13.333, 7.5), (7.5, 7.5)):
    prs, k = use("chalkboard", W, H)
    s = k.new_slide(); k.cover(s, kicker="科学课 · 第 3 讲", title="光合作用是怎么回事", subtitle="一片叶子，就是一座小工厂")
    kb = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:custGeom") and len(sh._element.xpath(".//a:lnTo")) == 4]
    check(kb and kb[0][2] < 0.5 * W, "chalkboard {}x{}: the kicker box hugs its words ({:.2f}in)".format(W, H, kb[0][2] if kb else -1))
    for page, kw in (("quote", dict(quote="一片叶子就是一座小工厂。", attribution="科学课笔记")),
                     ("data", dict(number="6", label="个二氧化碳分子", note="和 6 个水分子一起，做出一个葡萄糖分子。"))):
        s = k.new_slide(); getattr(k, page)(s, **kw)
        smudges = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']") and sh._element.xpath(".//a:gradFill")]
        check(not any(v2.meet(a, rect_of(t)) for a in smudges for t in texts(s)),
              "chalkboard {}x{} {}: eraser smudges keep clear of the words".format(W, H, page))
# an ordinary page is a framed board; its content rect sits inside the frame
import register_surface as rs
prs, k = use("chalkboard")
s = k.new_slide()
x, y, w, h = rs.ground(s, k.name, role="content", index=2)
frame = [rect_of(sh) for sh in s.shapes if not getattr(sh, "has_text_frame", False) or not sh.text_frame.text.strip()]
check(len(frame) >= 5 and x > 0.14 and x + w < 13.333 - 0.14 and y + h < 7.5 - 0.14,
      "chalkboard: an ordinary page is a framed board; content inside the frame")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `KeyError: 'chalkboard'`.

- [ ] **Step 3: Implement.**

(a) `visual_languages.py`, the tables.
- `LANGS`:

  ```python
      "chalkboard": {
          "palette": {"ground": "22392B", "ink": "F3F1EA", "mute": "C9D3C9", "panel": "2B4436",
                      "accents": ["F2D16B", "F2A9B8", "A4CDE6"], "text_accents": ["F2D16B", "F2A9B8"],
                      "wood": "7A4F2A", "chalk": "E8E2D2"},
          "fonts": {"both": {"display": "Trebuchet MS", "body": "Trebuchet MS", "numeral": "Trebuchet MS"},
                    "mac": {"display": "Chalkboard SE", "body": "Chalkboard SE", "numeral": "Chalkboard SE"}},
          "ea": {"display": "sans", "body": "sans"}, "grain": 7, "frames": ["rect"],
          "forbids": (), "cover": "low-left", "skeleton": "island"},
  ```

- `VARIANTS`:

  ```python
      "chalkboard": {
          "light": {"label": "green board", "label_zh": "绿黑板版", "grain": 7, "palette": LANGS["chalkboard"]["palette"]},
          "slate": {"label": "slate", "label_zh": "石板版", "grain": 7,
                    "palette": {"ground": "25282C", "ink": "F2F1EC", "mute": "C7C9CC", "panel": "30343A",
                                "accents": ["F2D16B", "F2A9B8", "A4CDE6"], "text_accents": ["F2D16B", "F2A9B8"],
                                "wood": "5B4632", "chalk": "E8E2D2"}}},
  ```

- `TYPE`:

  ```python
      "chalkboard": {"kicker": (16, "body", True, "accent", False, 10), "title": (58, "display", True, "ink", False, 28),
                     "subtitle": (22, "body", False, "mute", False, 12), "body": (19, "body", False, "ink", False, 12),
                     "mark": (130, "display", True, "accent", False, 48), "quote": (44, "display", True, "ink", False, 20),
                     "attribution": (20, "body", False, "accent", False, 11), "number": (150, "numeral", True, "accent", False, 48),
                     "label": (28, "display", True, "ink", False, 14), "note": (18, "body", False, "mute", False, 11),
                     "caption": (14, "body", False, "mute", False, 10), "line": (22, "body", False, "mute", False, 12),
                     "item_head": (24, "display", True, "ink", False, 14), "item_line": (19, "body", False, "mute", False, 11),
                     "item_no": (24, "display", True, "accent", False, 14)},
  ```

- `NATIVE` gains `"chalkboard"`.
- Extras: `NATIVE_EXTRAS["chalkboard"] = ("doodle", "ordered")`; `EXTRA_PAGES["doodle"] = ("cover", "closing")`; `EXTRA_PAGES["ordered"] = ("points",)`.
- Ground and card:

  ```python
  def _ground_chalkboard(slide, role, index):
      W, H = rs._canvas(slide)
      return (0.7, 0.6, W - 1.4, H - 1.3)             # inside the wooden frame new_slide drew
  ```

  Add `_card_chalkboard = _card_for("chalkboard")`.
- `_DISPLAY_NAMES["chalkboard"] = "Chalkboard"`; `_RATIONALE["chalkboard"] = "drawn, no pictures: a framed board, coloured chalk strokes, boxed steps, a circled figure"`.
- `_SAMPLE_COPY_NATIVE["chalkboard"]`, Chinese, like the approved look-dev; a real fact (6 CO₂ + 6 H₂O → C₆H₁₂O₆ + 6 O₂):

  ```python
      "chalkboard": [("cover", dict(kicker="科学课 · 第 3 讲", title="光合作用是怎么回事", subtitle="一片叶子，就是一座小工厂")),
                     ("points", dict(title="叶子做的三件事", ordered=True,
                                     items=[("吸收阳光", "叶绿素抓住光的能量"), ("吸进水和二氧化碳", "根吸水，叶子吸二氧化碳"),
                                            ("做出糖和氧气", "糖留给植物，氧气放出来")])),
                     ("quote", dict(quote="一片叶子就是一座小工厂。", attribution="科学课笔记")),
                     ("data", dict(number="6", label="个二氧化碳分子", note="和 6 个水分子一起，做出一个葡萄糖分子。"))],
  ```

(b) `vl_native2.py`: append

```python
# ═══════════════════════════════════ chalkboard 黑板报 ═══════════════════════════════════
def _cb_ground(k, slide):
    na.board_frame(slide, k.P["wood"], k.P["chalk"])      # the frame inside the page, the ledge, a stick of chalk


GROUNDS["chalkboard"] = _cb_ground


def ink_w(k, field, text, size):
    """The width (in) one line of `text` takes at `size` in the field's face (CJK an em a character)."""
    _b, role, bold, *_r = vl.TYPE[k.name][field]
    return na.chip_width(text, size, k.face(role), bold=bool(bold)) - 1.2 * size / 72.0


def _one_line(rect, size):
    return rect[3] <= size * 1.2 / 72.0 * 1.5 + 0.06


def _cb_smudges(k, slide, keep, seed):
    """Up to three faint eraser smudges (rim-free radial fades) where no words are; fewer when the board is full."""
    import random as _random
    W, H, s, o = ctx(k)
    rnd = _random.Random(seed)
    placed = 0
    for _ in range(40):
        if placed == 3:
            break
        w = rnd.uniform(3.0, 4.5) * s
        x, y = rnd.uniform(0.3 * s, max(0.3 * s, W - w - 0.3 * s)), rnd.uniform(0.4 * s, H - 1.2 * s)
        r = (x, y, w, w * 0.22)
        if x + w > W - 0.2 * s or any(meet(r, c, 0.1 * s) for c in keep):
            continue
        e = dk.box(slide, x, y, w, w * 0.22, fill=k.P["ink"])
        e._element.spPr.find(dk.qn("a:prstGeom")).set("prst", "ellipse")
        na._radial(e, k.P["ink"], 0.06)
        dk.decorative(e, "an eraser smudge on the board; nothing reads from it")
        placed += 1


def _cb_doodle(k, slide, spec, cx, cy, size):
    """The caller's icon (doodle=, an icons.py spec) drawn in yellow chalk. Fetched while PLANNING, so an unknown
    icon raises (naming what it tried) before anything is drawn."""
    import icons as _ic
    import tempfile as _tf
    png = Path(_tf.gettempdir()) / "slide-maker-native-art" / "doodle_{}_{}.png".format(
        re.sub(r"[^A-Za-z0-9]+", "_", spec), k.P["text_accents"][0])
    png.parent.mkdir(parents=True, exist_ok=True)
    _ic.icon_png(spec, str(png), color=k.P["text_accents"][0], px=320)

    def draw():
        pic = dk.icon(slide, str(png), cx - size / 2.0, cy - size / 2.0, size, alt=spec.split(":")[-1].replace("-", " "))
        dk.decorative(pic, "a chalk doodle beside the title; the title carries the meaning")
    return draw


@register("chalkboard", "cover", alts=2)
def _cb_cover(k, slide, f, image):
    """A lesson's first board: the kicker in a pink chalk box, the title with a double chalk underline, the subtitle;
    the caller's doodle= drawn in yellow chalk beside them — nothing drawn without it."""
    W, H, s, o = ctx(k)
    dd = text_of(f, "doodle")
    x, w = 0.08 * W, (0.60 if dd and o == "land" else 0.84) * W
    y0, y1 = (0.12 if alt() == 0 else 0.07) * H, (0.66 if dd and o != "land" else 0.86) * H
    r, ds = stack(k, slide, "cover", x, w, y0, y1,
                  [(fields(f, ("kicker", "title")), 0.40 * s), (fields(f, ("subtitle",)), 0.0)],
                  accent=k.P["text_accents"][1])
    art = []
    if "kicker" in r:
        kr = r["kicker"]
        sz = ds[0].sizes["kicker"]
        kw = min(kr[2], ink_w(k, "kicker", text_of(f, "kicker"), sz)) if _one_line(kr, sz) else kr[2]
        art.append(lambda: na.chalk_box(slide, kr[0] - 0.12 * s, kr[1] - 0.06 * s, kw + 0.24 * s, kr[3] + 0.12 * s,
                                        k.P["text_accents"][1], seed=3))
    if "title" in r:
        tr = r["title"]
        art.append(lambda: na.chalk_underline(slide, tr[0], tr[1] + tr[3] + 0.08 * s, min(tr[2], 0.55 * W),
                                              k.P["text_accents"][0], seed=5))
    if dd:
        size = 1.6 * s
        if o == "land":
            cx_, cy_ = 0.80 * W, 0.62 * H
        else:
            foot = max(v[1] + v[3] for v in r.values())
            cx_, cy_ = 0.70 * W, min(foot + 0.4 * s + size / 2, H - 0.9 * s - size / 2)
        art.append(_cb_doodle(k, slide, dd, cx_, cy_, size))
    _cb_smudges(k, slide, list(r.values()), seed=1)
    _run_all(art + ds)
    return r


@register("chalkboard", "section", alts=2)
def _cb_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    rects, draws, art = {}, [], []
    if o == "land" and alt() == 0:
        cx, cy, R = 0.24 * W, 0.50 * H, min(0.30 * H, 0.17 * W)
        col = (0.44 * W, 0.16 * H, 0.48 * W, 0.68 * H)
    else:
        cx, cy = 0.50 * W, 0.24 * H
        R = min(0.16 * H, 0.30 * W) * (1.0 if alt() == 0 else 0.75)
        col = (0.08 * W, cy + R + 0.4 * s, 0.84 * W, H - 0.7 * s - (cy + R + 0.4 * s))
    R = fit_circle(k, cx, cy, 2 * R) / 2.0
    if num:
        r, d = flow(k, slide, "section", (cx - R * 0.75, cy - R * 0.55, 1.5 * R, 1.1 * R), [("number", num)],
                    anchor="middle", align="c", start={"number": 110 * s})
        rects.update(r); draws.append(d)
        art.append(lambda: na.chalk_ellipse(slide, cx, cy, R, R * 0.85, k.P["text_accents"][1], seed=9))
    r, ds = stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3], [(fields(f, ("kicker", "title")), 0.0)],
                  accent=k.P["text_accents"][1])
    rects.update(r); draws += ds
    if "title" in r:
        tr = r["title"]
        art.append(lambda: na.chalk_underline(slide, tr[0], tr[1] + tr[3] + 0.08 * s, min(tr[2], 0.4 * W),
                                              k.P["text_accents"][0], seed=11))
    _cb_smudges(k, slide, list(rects.values()) + [(cx - R, cy - R, 2 * R, 2 * R)], seed=2)
    _run_all(art + draws)
    return rects


@register("chalkboard", "image_text", alts=2)
def _cb_image_text(k, slide, f, image):
    """The caller's picture pinned to the board by four chalk corner marks, the words beside it (under it in
    portrait)."""
    W, H, s, o = ctx(k)
    if o == "land":
        img = (0.08 * W, 0.14 * H, (0.46 if alt() == 0 else 0.40) * W, 0.70 * H)
        cx0 = img[0] + img[2] + 0.6 * s
        col = (cx0, 0.12 * H, 0.92 * W - cx0, 0.76 * H)
    else:
        img = (0.10 * W, 0.08 * H, 0.80 * W, (0.40 if alt() == 0 else 0.32) * H)
        cy0 = img[1] + img[3] + 0.5 * s
        col = (0.08 * W, cy0, 0.84 * W, H - 0.7 * s - cy0)
    r, ds = stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                  [(fields(f, ("kicker", "title", "body", "caption")), 0.0)], anchor="middle" if o == "land" else "top",
                  accent=k.P["text_accents"][1])
    vl._place_image(k, slide, image, img, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    L = 0.35 * s
    x0, y0, x1, y1 = img[0] - 0.08 * s, img[1] - 0.08 * s, img[0] + img[2] + 0.08 * s, img[1] + img[3] + 0.08 * s
    for i, (ax, ay, dx, dy) in enumerate(((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1))):
        na.chalk_path(slide, [(ax + dx * L, ay), (ax, ay), (ax, ay + dy * L)], k.P["ink"], w=2.2, seed=20 + i, passes=1)
    _run_all(ds)
    return r


@register("chalkboard", "points", alts=2)
def _cb_points(k, slide, f, image):
    """Chalk boxes, one per point, each sized to its measured words, a circled number at its corner; arrows between
    them only when the caller says the points happen in order (ordered=True) — numbers alone read as a list."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    ordered = f.get("ordered", False)
    if not isinstance(ordered, bool):
        raise TypeError("chalkboard.points(): ordered= is True or False, got {!r}".format(ordered))
    r, d = flow(k, slide, "points", (0.08 * W, 0.08 * H, 0.84 * W, 0.18 * H), fields(f, ("kicker", "title")),
                accent=k.P["text_accents"][1])
    rects, draws, art = dict(r), [d], []
    if "title" in r:
        tr = r["title"]
        art.append(lambda: na.chalk_underline(slide, tr[0], tr[1] + tr[3] + 0.08 * s, min(tr[2], 0.36 * W),
                                              k.P["text_accents"][0], seed=2))
    top = max((v[1] + v[3] for v in r.values()), default=0.08 * H) + 0.50 * s
    bottom = H - 0.75 * s
    cols = [k.P["text_accents"][0], k.P["text_accents"][1], k.P["accents"][2], k.P["ink"]]
    row = o == "land" and alt() == 0
    gap, pad, numd = ((0.55, 0.30, 0.64) if alt() == 0 else (0.35, 0.20, 0.50))
    gap, pad, numd = gap * s, pad * s, numd * s
    bw = (0.84 * W - (n - 1) * gap) / n if row else 0.84 * W
    xs = [0.08 * W + i * (bw + gap) for i in range(n)] if row else [0.08 * W] * n

    def plan_box(i, y, h):
        hd, ln = pts[i]
        if row:
            tcol = (xs[i] + pad, y + pad + numd + 0.15 * s, bw - 2 * pad, h - (2 * pad + numd + 0.15 * s))
        else:
            tcol = (xs[i] + pad + numd + 0.25 * s, y + pad, bw - 2 * pad - numd - 0.25 * s, h - 2 * pad)
        return flow(k, slide, "points", tcol, [(x_, t) for x_, t in (("item_head", hd), ("item_line", ln)) if t], anchor="top")
    # pass 1: each box's height from its own words; pass 2: the row (or the stack) centred in the room under the title
    if row:
        hs = [max(v[1] + v[3] for v in plan_box(i, top, bottom - top)[0].values()) - top + pad for i in range(n)]
        bh = max(max(hs), numd + 2 * pad)
        y = top + max(0.0, (bottom - top - bh) / 2.0)
        boxes = [(xs[i], y, bw, bh) for i in range(n)]
    else:
        slot = (bottom - top - (n - 1) * gap) / n
        hs = [max(max(v[1] + v[3] for v in plan_box(i, top, slot)[0].values()) - top + pad, numd + 2 * pad) for i in range(n)]
        y = top + max(0.0, (bottom - top - sum(hs) - (n - 1) * gap) / 2.0)
        boxes = []
        for h_ in hs:
            boxes.append((xs[0], y, bw, h_))
            y += h_ + gap
    for i, (x, y, w, h_) in enumerate(boxes):
        c = cols[i % len(cols)]
        _tr, td_ = plan_box(i, y, h_ + 0.01)
        art.append(lambda x=x, y=y, w=w, h_=h_, c=c, i=i: na.chalk_box(slide, x, y, w, h_, c, seed=20 + i))
        ncx, ncy = x + pad + numd / 2.0, y + pad + numd / 2.0
        art.append(lambda ncx=ncx, ncy=ncy, c=c, i=i: na.chalk_ellipse(slide, ncx, ncy, numd / 2.0, numd / 2.0, c, seed=30 + i))
        _nr, nd = flow(k, slide, "points", (ncx - numd / 2.0, ncy - numd / 2.0, numd, numd), [("item_no", str(i + 1))],
                       anchor="middle", align="c", ink=c, accent=c)
        draws += [nd, td_]
        if ordered and i < n - 1:
            if row:
                ay = y + h_ / 2.0
                art.append(lambda x=x, w=w, ay=ay, i=i: na.chalk_arrow(slide, x + w + 0.10 * s, ay, x + w + gap - 0.10 * s, ay,
                                                                     k.P["ink"], seed=40 + i))
            else:
                ax = x + w / 2.0
                art.append(lambda ax=ax, y=y, h_=h_, i=i: na.chalk_arrow(slide, ax, y + h_ + 0.06 * s, ax, y + h_ + gap - 0.06 * s,
                                                                       k.P["ink"], seed=40 + i))
    _cb_smudges(k, slide, list(rects.values()) + boxes, seed=3)
    _run_all(art + draws)
    return rects


@register("chalkboard", "quote", alts=2)
def _cb_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    x = max(0.17 * W, 1.6 * s) if alt() == 0 else max(0.10 * W, 1.45 * s)
    a = text_of(f, "attribution")
    r, ds = stack(k, slide, "quote", x, 0.90 * W - x, 0.16 * H, H - 0.75 * s,
                  [(fields(f, ("quote",)), 0.45 * s), ([("attribution", "— " + a)] if a else [], 0.0)],
                  accent=k.P["text_accents"][1])
    art = []
    if "quote" in r:
        qr = r["quote"]
        _m, md = flow(k, slide, "quote", (x - 1.35 * s, qr[1] - 0.25 * s, 1.2 * s, 1.4 * s), [("mark", "“")],
                      start={"mark": 110 * s})
        ds.append(md)
        art.append(lambda: na.chalk_underline(slide, qr[0], qr[1] + qr[3] + 0.08 * s, min(qr[2], 0.22 * W),
                                              k.P["text_accents"][0], seed=8))
    _cb_smudges(k, slide, list(r.values()) + [(x - 1.35 * s, 0.0, 1.2 * s, H)], seed=4)
    _run_all(art + ds)
    return r


@register("chalkboard", "data", alts=2)
def _cb_data(k, slide, f, image):
    """The number circled in pink chalk, a chalk arrow from it to its label and note."""
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    rects, draws, art = {}, [], []
    if o == "land" and alt() == 0:
        cx, cy, R = 0.28 * W, 0.48 * H, min(0.30 * H, 0.18 * W)
        col = (0.56 * W, 0.22 * H, 0.36 * W, 0.56 * H)
    else:
        cx, cy = 0.5 * W, 0.26 * H
        R = min(0.17 * H, 0.32 * W) * (1.0 if alt() == 0 else 0.8)
        col = (0.10 * W, cy + R + 0.7 * s, 0.80 * W, H - 0.75 * s - (cy + R + 0.7 * s))
    R = fit_circle(k, cx, cy, 2 * R) / 2.0
    if num:
        r, d = flow(k, slide, "data", (cx - 1.05 * R, cy - 0.7 * R, 2.1 * R, 1.4 * R), [("number", num)],
                    anchor="middle", align="c")
        rects.update(r); draws.append(d)
        art.append(lambda: na.chalk_ellipse(slide, cx, cy, 1.15 * R, 0.92 * R, k.P["text_accents"][1], seed=9, turns=1.12))
    r, ds = stack(k, slide, "data", col[0], col[2], col[1], col[1] + col[3], [(fields(f, ("label", "note")), 0.0)],
                  anchor="middle" if o == "land" else "top")
    rects.update(r); draws += ds
    if num and r:
        ty = min(v[1] for v in r.values())
        if o == "land" and alt() == 0:
            art.append(lambda: na.chalk_arrow(slide, cx + 1.2 * R, cy - 0.1 * R, col[0] - 0.2 * s, ty + 0.25 * s,
                                              k.P["ink"], seed=60))
        else:
            art.append(lambda: na.chalk_arrow(slide, cx, cy + 0.98 * R, cx, ty - 0.12 * s, k.P["ink"], seed=60))
    _cb_smudges(k, slide, list(rects.values()) + [(cx - 1.2 * R, cy - R, 2.4 * R, 2 * R)], seed=5)
    _run_all(art + draws)
    return rects


@register("chalkboard", "closing", alts=2)
def _cb_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    dd = text_of(f, "doodle")
    w = (0.62 if dd and o == "land" else 0.84) * W
    r, ds = stack(k, slide, "closing", 0.08 * W, w, (0.14 if alt() == 0 else 0.07) * H, (0.68 if dd and o != "land" else 0.86) * H,
                  [(fields(f, ("title",)), 0.45 * s), (fields(f, ("line",)), 0.0)])
    art = []
    if "title" in r:
        tr = r["title"]
        art.append(lambda: na.chalk_underline(slide, tr[0], tr[1] + tr[3] + 0.08 * s, min(tr[2], 0.5 * W),
                                              k.P["text_accents"][0], seed=12))
    if dd:
        size = 1.6 * s
        if o == "land":
            cx_, cy_ = 0.82 * W, 0.50 * H
        else:
            foot = max(v[1] + v[3] for v in r.values())
            cx_, cy_ = 0.70 * W, min(foot + 0.4 * s + size / 2, H - 0.9 * s - size / 2)
        art.append(_cb_doodle(k, slide, dd, cx_, cy_, size))
    _cb_smudges(k, slide, list(r.values()), seed=6)
    _run_all(art + ds)
    return r
```

(c) `directions_diversity.py`: append `"chalkboard"` to `NATIVE_LANGS`, and add the message clause "chalkboard (lesson, class, training, explainer)".

- [ ] **Step 4: Run the tests**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -3`
Expected: `N passed, 0 failed`. The doodle test fetches `lucide:sun` once, as the P3 cutpaper sample already does with its icons.

- [ ] **Step 5: Build, render and LOOK at the samples**

Use the same commands as Task 4 Step 5, with `chalkboard` and the stems `chalkboard`, `chalkboard-slate`. Read both JPGs and compare them with `~/Desktop/slide-maker 新模板样张/sheets/chalkboard.jpg`. Check that:
- each box fits its words, with no lone character on a line;
- the arrows sit between the boxes (the sample is `ordered=True`);
- the smudges never sit on words;
- the frame is inside the page.

- [ ] **Step 6: Run the neighbouring suites** (the same four as Task 4 Step 6). Expected: all `0 failed`.

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native2.py \
  skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/tests/test_native_languages_p4.py \
  skills/slide-maker/assets/vl/samples/chalkboard.jpg skills/slide-maker/assets/vl/samples/chalkboard-slate.jpg \
  skills/slide-maker/assets/vl/samples/manifest.json
git commit -m "native languages: chalkboard (黑板报) — a framed board, chalk boxes sized to their words, arrows only when ordered"
```

---
### Task 9: Docs, guidance and runnable examples for any agent

**Files:**
- Modify: `skills/slide-maker/references/visual-languages.md`
  - "Native languages" section: new subsection, guidance line
  - "Grounds" table: five rows
- Modify: `skills/slide-maker/scripts/directions_diversity.py` (the final nine-way guidance in `native_fault`)
- Modify: `skills/slide-maker/scripts/sigs.py`
  - `EXAMPLES` (one per new `native_art` function, plus `vl_extras`)
  - the `use` / `points` comments
  - `_EXTRA_GUARANTEES["points"]`
- Modify: `skills/slide-maker/SKILL.md` (the native-languages sentence, ~line 1686) and, if the lossless check flags it, `skills/slide-maker/.skill-lossless-allow.json`
- Modify: `skills/slide-maker/references/interview-protocol.md` (~line 259), `references/codex-runtime.md` (~line 416), `references/generated-template.md` (the Chalkboard bullet, ~line 602)
- Modify: `skills/slide-maker/scripts/vl_native.py` (module docstring), `scripts/check_visual_language.py` ("points on the native four" → "points on the native languages")
- Modify: `skills/slide-maker/references/file-inventory.md` (`native_art.py` entry), `CHANGELOG.md` ([Unreleased]), `README.md`, `README_CN.md`
- Test: `skills/slide-maker/tests/test_native_languages_p4.py`, `skills/slide-maker/tests/test_direction_vl_rule.py`

**Interfaces:**
- Consumes: everything from Tasks 2–8.
- Produces: documentation and scaffolds only, with no behaviour change. Any agent that reads SKILL.md, the references and `sigs.py` can build each language.

- [ ] **Step 1: Write the failing tests.**

Append to `tests/test_native_languages_p4.py` (before the summary block):

```python
# ── what an agent reading only the docs needs (Task 9) ──
ref = (ROOT / "references" / "visual-languages.md").read_text(encoding="utf-8")
for n in ("starlit", "broadsheet", "journal", "tally", "chalkboard"):
    check("`{}`".format(n) in ref and "→ `{}`".format(n) in ref, "the reference documents {} and when to offer it".format(n))
for ex in ("masthead=", "edition=", "inside=", "tags=", "running=", "authors=", "abstract=", "margin=", "total=", "doodle=",
           "ordered="):
    check(ex in ref, "the reference documents {}".format(ex))
import sigs
for fn in ("starfield_png", "radial_glow", "horizon_glow", "crescent", "ring", "polyline", "chalk_path", "chalk_box",
           "chalk_ellipse", "chalk_underline", "chalk_arrow", "board_frame", "chip", "chip_width", "share_bar", "vl_extras"):
    check(fn in sigs.EXAMPLES, "sigs.py --example {} has a runnable scaffold".format(fn))
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
check(all(n in skill for n in ("starlit", "broadsheet", "journal", "tally", "chalkboard")), "SKILL.md names the nine native languages")
```

Append to `tests/test_direction_vl_rule.py` before its summary:

```python
msg = dd.native_fault("none", [{"name": "x"}], None) or ""
check(all(n in msg for n in vl.NATIVE), "the native-language fault names every native language: {}".format(msg[:120]))
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p4.py | grep FAIL | head; python3 tests/test_direction_vl_rule.py | tail -2`
Expected: FAIL lines for the reference, sigs and SKILL.md checks. `test_direction_vl_rule` passes already if Tasks 4–8 each added their clause; it then guards the final rewrite.

- [ ] **Step 3: Write the docs.**

(a) `references/visual-languages.md`.
- **First sentence of "Native languages".** Change it so it lists nine languages: "`ink` (水墨), `poster` (海报大字), `cutpaper` (剪纸层叠) and `drafting` (蓝图技术线稿 — named `drafting` because `blueprint` is a preset), and the second set below,". Leave the rest of the paragraph unchanged.
- **Guidance line.** Replace the "Guidance, not a rule: …" sentence with:

  > Guidance, not a rule: culture, history, craft → `ink`; launch, manifesto, opinion → `poster`; children, storytelling, community → `cutpaper`; engineering, architecture, systems design → `drafting`; year in review, letter, thanks, commemoration → `starlit`; newsletter, periodic report, community update → `broadsheet`; research talk, lab meeting, paper, defence → `journal`; metrics, quarterly review, operations, growth → `tally`; lesson, class, training, explainer → `chalkboard`.

- **New subsection.** Insert this immediately before `## Grounds`:

  ````markdown
  ### The second set — `starlit` · `broadsheet` · `journal` · `tally` · `chalkboard`

  Five more drawn languages, each borrowed from a convention people already read at a glance. Same contract as the
  first four: no pictures needed, everything on the page, nothing PowerPoint repairs, and no word invented.

  | language | 中文 | borrowed from | for |
  |---|---|---|---|
  | `starlit` | 星夜 | the night sky and the year-end letter | year in review, letters, thanks, commemoration |
  | `broadsheet` | 报纸头版 | the newspaper front page | newsletters, periodic reports, community updates |
  | `journal` | 学术期刊 | the journal article | research talks, lab meetings, papers, defences |
  | `tally` | 数据账本 | data dashboards and finance reports | metrics, quarterly reviews, operations, growth |
  | `chalkboard` | 黑板报 | the classroom blackboard | lessons, classes, training, explainers |

  - **Words only you can give.** A word given on a page that does not draw it is refused, naming the pages that do;
    when it is absent, nothing is drawn.
    - `masthead="…"` (`broadsheet`, any page, remembered for the deck): the paper's name in the masthead strip.
      Without it, the cover's `kicker` names the paper and is not repeated above the headline; without either, the
      strip has rules and the page number only.
    - `edition="…"` (`broadsheet`, any page, remembered): the strip's left words, such as your date or issue.
    - `inside=[…]` (`broadsheet` cover): 1–4 short lines for the "Inside" sidebar.
    - `tags=[…]` (`broadsheet` and `tally` `points`): one short label per point, used as the column's label or the
      row's pill. The count must match; a tag too long for its pill is refused by name.
    - `running="…"` (`journal`, any page, remembered): the running head. Without it, the cover title runs there when
      it fits one line, else the page number stands alone. An explicit `running=` that cannot fit is refused.
    - `authors="…"`, `abstract="…"` (`journal` cover): the author line and the abstract block. A subtitle is never
      labelled "Abstract".
    - `margin="…"` (`journal` `points`): a margin note under a "Note" label.
    - `total="…"` (`tally` `data`): draws a share bar, the number's share of the total, with both numbers at its ends.
      The rules:
      - both are plain numbers (`12`, `1,250`, `98.6%`);
      - both are percentages or neither is;
      - the number is no larger than the total.

      Anything else is refused, never guessed.
    - `doodle="lucide:sun"` (`chalkboard` cover and closing): one icon spec, drawn in yellow chalk.
    - `ordered=True` (`chalkboard` `points`): chalk arrows between the boxes, only when the points really happen in
      order. The numbers already read as a list.
  - **Derived, never typed in.**
    - page numbers;
    - `journal` figure numbers: "Figure n" over the deck's `image_text` pages, with `kicker=` to override;
    - the `broadsheet` ■ end mark;
    - the structural labels Abstract, Inside, Figure, Page and Note, in the script of the page's own words:
      摘要 / 要旨 / 초록; 图 1 / 図 1 / 그림 1; 第 2 版 / 2 面 / 2면.
  - **Pages.** All seven pages come in both orientations.
    - `journal`'s `image_text` is its figure page: the title above, your figure WHOLE (never cropped), its label,
      caption (`body=`) and source line (`caption=`).
    - `broadsheet` opens a Latin column body on a raised initial: an enlarged first letter in its own line, because
      pptx has no drop cap. CJK bodies are not enlarged.
    - `starlit`'s points are a constellation (one star per point), `tally`'s are ledger rows, and `chalkboard`'s are
      chalk boxes sized to their words.
  - **Ordinary pages** (`s = k.new_slide()`, then `rs.ground(s, k.name, …)`):
    - `starlit` paints its sky clear of the returned rect;
    - `broadsheet` draws the masthead strip, and `journal` the running head, with the deck's remembered words, and
      return the rect under it;
    - `tally` is on its grid;
    - `chalkboard` is a framed board.
  - **No light ground.** `starlit` and `chalkboard` are dark by default: their `light` key IS their default ground.
    A printed board in either prints a dark page, and `ground="auto"` says so.
  - **No spaces between Chinese and Latin words** ("心脏MRI的", not "心脏 MRI 的"). The renderers add their own gap,
    and a typed space doubles it; this was measured on the look-dev.

  ```python
  import deckkit as dk, visual_languages as vl
  prs = dk.blank_deck(13.333, 7.5)
  k = vl.use("broadsheet", prs)
  k.cover(k.new_slide(), title="Every street needs a night for fixing things",
          subtitle="How a repair evening works, and why it spreads.", masthead="The Repair Weekly", edition="No. 12",
          inside=["The idea", "The evening", "The numbers"])
  k.points(k.new_slide(), title="How it works", tags=["Idea", "Evening", "Next"],
           items=[("Bring it broken", "Anything that switches on is welcome."), ("Fix it together", "Your hands do the work."),
                  ("Take it home", "What is not fixed goes on the list.")])
  k.closing(k.new_slide(), title="See you next week", line="Bring a neighbour.")
  prs.save("weekly.pptx")
  ```
  ````

- **Grounds table.** Add these rows:

  ```markdown
  | starlit | midnight (dark — no light ground) | `dawn` — deep violet, rose gold |
  | broadsheet | newsprint | `salmon` — pink paper, navy accent |
  | journal | paper | `green` — title green, gold accent |
  | tally | white grid | `night` — navy grid, periwinkle and lime |
  | chalkboard | green board (dark — no light ground) | `slate` — grey slate |
  ```

(b) `directions_diversity.native_fault` message, the first fault:

```python
        return ("the deck has no pictures and no direction is a native visual language — offer the one that fits the "
                "topic with visual_languages.direction('<name>'): ink (culture, history, craft), poster (launch, "
                "manifesto, opinion), cutpaper (children, storytelling, community), drafting (engineering, "
                "architecture, systems design), starlit (year in review, letter, thanks, commemoration), broadsheet "
                "(newsletter, periodic report, community update), journal (research talk, lab meeting, paper, defence), "
                "tally (metrics, quarterly review, operations, growth) or chalkboard (lesson, class, training, "
                "explainer) — references/visual-languages.md")
```

(c) `sigs.py`:
- **`EXAMPLES`.** Add, after `"clipped_block"`:

  ```python
    "starfield_png": 'import native_art as na\n'
                     'na.starfield_png(s, base="0B1430", ink="F3EBD8", glow="F1D9A6", seed=3,\n'
                     '                 keep_clear=[(1.0, 1.0, 6.0, 1.6)])     # the sky as background; none where words go\n'
                     'dk.text(s, 1.0, 1.0, 6.0, 1.6, [[("A year in review", 36, dk.RGBColor(0xF3, 0xEB, 0xD8), False, False)]])',
    "radial_glow": 'import native_art as na\n'
                   'na.radial_glow(s, 5.0, 2.8, 3.0, "F1D9A6")         # a rim-free glow behind a figure',
    "horizon_glow": 'import native_art as na\n'
                    'na.horizon_glow(s, 4.6, "F1D9A6", "D9B36C")        # clear at its top, warm at the page foot',
    "crescent": 'import native_art as na\n'
                'na.crescent(s, 8.6, 1.0, 0.8, "D9B36C", "0B1430")     # moved onto the page if asked off it',
    "ring": 'import native_art as na\n'
            'na.ring(s, 2.5, 2.8, 3.2, "D9B36C", w=1.25)                # the rim of a round picture window',
    "polyline": 'import native_art as na\n'
                'na.polyline(s, [(1, 4.5), (4, 3.8), (7, 4.4)], "1E3A5F", w=1.5)   # open; clamped onto the page',
    "chalk_path": 'import native_art as na\n'
                  'na.chalk_path(s, [(1, 4.0), (5, 4.1)], "F3F1EA", seed=2)   # dragged twice; deterministic for a seed',
    "chalk_box": 'import native_art as na\n'
                 'na.chalk_box(s, 1.0, 1.0, 3.6, 1.8, "F2D16B", seed=4)\n'
                 'dk.text(s, 1.3, 1.3, 3.0, 1.2, [[("Catch the light", 22, dk.RGBColor(0xF3, 0xF1, 0xEA), True, False)]])',
    "chalk_ellipse": 'import native_art as na\n'
                     'na.chalk_ellipse(s, 3.0, 2.8, 1.4, 1.1, "F2A9B8", seed=9)   # circle a figure in chalk',
    "chalk_underline": 'import native_art as na\n'
                       'na.chalk_underline(s, 1.0, 1.6, 4.0, "F2D16B", seed=5)   # a double chalk underline',
    "chalk_arrow": 'import native_art as na\n'
                   'na.chalk_arrow(s, 4.2, 2.8, 5.4, 2.8, "F3F1EA", seed=40)   # only between steps that ARE in order',
    "board_frame": 'import native_art as na\n'
                   'x, y, w, h = na.board_frame(s, "7A4F2A", "E8E2D2")   # a framed board; content goes in x, y, w, h',
    "chip": 'import native_art as na\n'
            'na.chip(s, 0.8, 0.6, "Q3 REVIEW", size=12, fill="C6F432", ink="0E0E10", face="Arial")   # one line, measured',
    "chip_width": 'import native_art as na\n'
                  'w = na.chip_width("会员资格", 12, "Arial")               # an em per CJK character, plus the padding\n'
                  'na.chip(s, 9.0 - w, 0.6, "会员资格", size=12, fill="C6F432", ink="0E0E10", face="Arial",\n'
                  '        ea_face="Hiragino Sans GB")',
    "share_bar": 'import native_art as na\n'
                 'na.share_bar(s, 0.8, 4.6, 8.4, 12 / 40, track="E7EAF1", fill="2438F0")   # 12 of 40: YOUR numbers',
    "vl_extras": 'import visual_languages as vl\n'
                 'k = vl.use("broadsheet", prs)        # words only YOU give: masthead=, edition=, inside=, tags=\n'
                 'k.cover(k.new_slide(), title="Every street needs a night for fixing things", masthead="The Repair Weekly",\n'
                 '        edition="No. 12", inside=["The idea", "The evening"])\n'
                 'k.points(k.new_slide(), title="How it works", tags=["Idea", "Evening"],\n'
                 '         items=[("Bring it broken", "Anything that switches on."), ("Fix it together", "Your hands do the work.")])\n'
                 'k = vl.use("tally", prs)             # total= draws a share bar: plain numbers, number <= total\n'
                 'k.data(k.new_slide(), number="12", label="of 40 neighbourhoods have a shelf", total="40")',
  ```

- **Comments.** In `"use"`, change the comment `# ink · poster · cutpaper · drafting: no pictures needed` to `# 9 native languages: ink poster cutpaper drafting starlit broadsheet journal tally chalkboard`. In `"points"`, change `# or "poster" / "cutpaper" / "drafting" — no pictures needed` to `# or any native language — no pictures needed`.
- **`_EXTRA_GUARANTEES["points"]`.** Append to the string: `; one star per point (starlit), one ledger row per point (tally), chalk boxes sized to their words with arrows only when ordered=True (chalkboard)`.

(d) `SKILL.md`, ~line 1686. Change "A deck with NO pictures offers one of the four NATIVE visual languages (`ink` · `poster` · `cutpaper` · `drafting`, drawn, no pictures needed)" to "A deck with NO pictures offers one of the NATIVE visual languages (`ink` · `poster` · `cutpaper` · `drafting` · `starlit` · `broadsheet` · `journal` · `tally` · `chalkboard`, drawn, no pictures needed)". Then run the lossless check the way CI runs it:

```bash
cd /Users/donghanglyu/code_project/slides_maker && git fetch -q origin main && BASE=$(git merge-base origin/main HEAD) && \
  python3 skills/slide-maker/scripts/check_skill_lossless.py --baseline "${BASE}:skills/slide-maker/SKILL.md" \
  --allow skills/slide-maker/.skill-lossless-allow.json --report /tmp/skill-lost.md; echo rc=$?
```

If it reports the old sentence as missing, add it to the allowlist with `--write-allow`, giving the reason "the native set grew from four to nine languages (P4); the sentence now lists all nine". Then re-run; expect `rc=0`.

(e) The other passages that name the native set:
- `interview-protocol.md`, the bullet "A native visual language when the deck has no pictures": replace the four-way list with the nine-way guidance from (a).
- `codex-runtime.md`: change `visual_languages.direction("ink" | "poster" | "cutpaper" | "drafting")` to `visual_languages.direction("<a native language>")`, followed by "— `ink`, `poster`, `cutpaper`, `drafting`, `starlit`, `broadsheet`, `journal`, `tally` or `chalkboard`".
- `generated-template.md`: after the Chalkboard bullet, add "→ with no image tool, the native `chalkboard` language draws this register with editable chalk strokes (`references/visual-languages.md`)".
- `vl_native.py` docstring: after "(ink, poster, cutpaper, drafting)", add "; the second set — starlit, broadsheet, journal, tally, chalkboard — is in vl_native2.py, imported at this module's foot".
- `check_visual_language.py`: change "points on the native four" to "points on the native languages".
- `file-inventory.md`, the `native_art.py` entry: add "a night sky picture, rim-free glows, a crescent, chalk strokes and a board frame, pills and share bars (P4)".

(f) `CHANGELOG.md` under `## [Unreleased]`, before "### Four native visual languages":

```markdown
### Five more native visual languages — borrowed from the world

`starlit` (a night sky, points as a constellation, the figure in a glow), `broadsheet` (a masthead strip, a headline
cover, newspaper columns opening on a raised initial, a pull quote between rules), `journal` (a running head, an
abstract, numbered whole figures with captions and sources, margin notes), `tally` (a fine grid, heavy type, pill
tags, a giant number with its share of the caller's total) and `chalkboard` (a framed board, chalk boxes sized to
their words, arrows only when the points are in order). Every page in both orientations and two grounds. Words the
kit cannot invent — a masthead, an edition, an Inside list, tags, a running head, authors, an abstract, a margin
note, a total, a doodle — come only from the caller; page and figure numbers, the end mark and the structural labels
(in the page's own script: 摘要 / 要旨 / 초록) are derived. A deck with no pictures is offered the one that fits its
topic. Also: `register_surface.register()` refuses a name another file already registered (it silently replaced
the kit before), and a replaced slide background drops its old picture.
```

(g) The READMEs.
- `README.md`:
  - **Heading.** Change "## Visual languages: four drawn looks, no pictures needed" to "## Visual languages: nine drawn looks, no pictures needed".
  - **First sentence.** Change "Four more languages draw…" to "Nine more languages draw…".
  - **Rows.** Add three `<tr>` rows to the table, in the same markup as the existing rows, for `starlit` (contrast: `dawn`), `broadsheet` (`salmon`), `journal` (`green`), `tally` (`night`) and `chalkboard` (`slate`). Each row's `<sub>` line is the language's `_RATIONALE` minus its "drawn, no pictures: " prefix.
  - **Pick sentence.** Append "…, a year in review → starlit, a newsletter → broadsheet, a paper or lab meeting → journal, a metrics review → tally, a lesson → chalkboard".
- `README_CN.md`: the same, in Chinese: "## 设计语言：九套原生绘制的风格，不需要图片", "另外九套…", the same five table rows with Chinese captions, and the same additions to the pick sentence.

- [ ] **Step 4: Run to verify**

Run:

```bash
cd skills/slide-maker && python3 tests/test_native_languages_p4.py | tail -1 && python3 tests/test_direction_vl_rule.py | tail -1 && \
  python3 scripts/smoke_deckkit.py 2>&1 | tail -3 && python3 scripts/check_doc_commands.py && python3 scripts/check_inventory.py && \
  python3 scripts/sigs.py --example starfield_png chalk_box vl_extras | head -20
```

Expected:
- all tests `0 failed`;
- smoke_deckkit ends with its all-passed line (every scaffold runs, including the new ones);
- both checkers exit 0;
- `sigs.py --example` prints the three scaffolds.

- [ ] **Step 5: Commit**

```bash
cd /Users/donghanglyu/code_project/slides_maker
git add skills/slide-maker/references/visual-languages.md skills/slide-maker/scripts/directions_diversity.py \
  skills/slide-maker/scripts/sigs.py skills/slide-maker/SKILL.md skills/slide-maker/references/interview-protocol.md \
  skills/slide-maker/references/codex-runtime.md skills/slide-maker/references/generated-template.md \
  skills/slide-maker/scripts/vl_native.py skills/slide-maker/scripts/check_visual_language.py \
  skills/slide-maker/references/file-inventory.md CHANGELOG.md README.md README_CN.md \
  skills/slide-maker/tests/test_native_languages_p4.py skills/slide-maker/tests/test_direction_vl_rule.py
git status --short skills/slide-maker/.skill-lossless-allow.json | grep -q . && git add skills/slide-maker/.skill-lossless-allow.json
git commit -m "docs: the five new native languages, their words-only-you-give, the nine-way offer guidance, runnable scaffolds"
```

---

### Task 10: Verification, a non-Claude run, independent review, delivery

**Files:** none planned. Fixes found here get their own failing test first, in the file that owns the code.

- [ ] **Step 1: Recreate the local CI tools in the scratchpad.** They are throwaway and never committed. Let `SP` be the session scratchpad.
  - Write `$SP/cisteps.py`, which runs every `run:` step of `ci.yml` in order, skipping install steps:

```python
#!/usr/bin/env python3
"""Run every `run:` step of the slides_maker CI workflow locally, in order, in each step's working directory; skip
only install steps. usage: cisteps.py <repo-root> <log-dir>"""
import os, subprocess, sys
import yaml
root, logdir = sys.argv[1], sys.argv[2]
os.makedirs(logdir, exist_ok=True)
job = list(yaml.safe_load(open(os.path.join(root, ".github/workflows/ci.yml")))["jobs"].values())[0]
dwd = (job.get("defaults", {}).get("run", {}) or {}).get("working-directory", ".")
SKIP = ("apt-get", "pip install", "brew ", "sudo ")
env = dict(os.environ)
shim = os.path.join(logdir, "bin"); os.makedirs(shim, exist_ok=True)
if not os.path.exists(os.path.join(shim, "python")):
    os.symlink(sys.executable, os.path.join(shim, "python"))
env["PATH"] = shim + os.pathsep + env["PATH"]
ran = failed = skipped = 0
for i, st in enumerate(job["steps"]):
    cmd = st.get("run")
    if not cmd:
        continue
    if any(k in cmd for k in SKIP):
        skipped += 1; continue
    ran += 1
    r = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", cmd], cwd=os.path.join(root, st.get("working-directory", dwd)),
                       env=env, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        failed += 1
        print("FAILED [%d] %s\n    %s" % (i, st.get("name"), "\n    ".join((r.stdout + r.stderr).strip().splitlines()[-8:])))
        open(os.path.join(logdir, "fail_%03d.log" % i), "w").write(r.stdout + r.stderr)
print("ci steps: ran %d, failed %d, skipped (install) %d" % (ran, failed, skipped))
```

  - Write `$SP/cisim/cisim.py` and `$SP/cisim/all.sh`. These run every `tests/test_*.py` with the ubuntu runner's fonts (only DejaVu, Liberation and Noto CJK; every other face reads as substituted; `sys.platform = "linux"`):

```python
"""Run a test file with the font environment of the ubuntu CI runner."""
import os, sys, runpy
import matplotlib
SK = os.path.expanduser("~/code_project/slides_maker/skills/slide-maker")
os.chdir(SK); sys.path.insert(0, os.path.join(SK, "scripts")); sys.platform = "linux"
TTF = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
ALLOW = ("DejaVu", "Liberation", "Noto Sans CJK", "Noto Serif CJK")
import deckkit as dk
_orig = dk._font_face
def _face(name, bold=False):
    if not name or not str(name).startswith(ALLOW):
        return (os.path.join(TTF, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), 0)
    return _orig(name, bold)
dk._font_face = _face; dk._FONT_FACE_CACHE.clear()
dk._font_substituted = lambda n: not str(n or "").startswith(ALLOW); dk._FONT_SUB_CACHE.clear()
import display_type as dt
dt._italic_file = lambda f, b: None
test = sys.argv[1]; sys.argv = [test]
runpy.run_path(test, run_name="__main__")
```

```zsh
#!/bin/zsh
# every tests/test_*.py under the simulated ubuntu font environment; prints failures
SIM=${0:A:h}/cisim.py; OUT=$1; mkdir -p $OUT
cd ~/code_project/slides_maker/skills/slide-maker
n=0; bad=0
for t in tests/test_*.py; do
  n=$((n+1)); b=$(basename $t .py)
  python3 $SIM $t > $OUT/$b.log 2>&1 || { bad=$((bad+1)); echo "FAILED: $b"; }
done
echo "ran $n under simulation, nonzero: $bad"
```

- [ ] **Step 2: Run every CI step locally**

Run: `python3 $SP/cisteps.py ~/code_project/slides_maker $SP/ci-p4 2>&1 | tail -15`
Expected: `ci steps: ran N, failed 0`. Read any failure's log in full. A failure in a file this plan did not touch is still reported by name; it is not called pre-existing without checking it against `origin/main`.

- [ ] **Step 3: Run the font simulation**

Run: `zsh $SP/cisim/all.sh $SP/cisim/p4 | tail -8`
Expected: the only failures are the three known artifacts (`test_cjk_measurement`, `test_font_verifiability`, `test_lint_regressions`); `test_native_languages_p4` and `test_native_generality` pass. A P4 refusal under substitute faces means a composition measured too tightly: give it room (an `alt()` layout or a margin) and add the canvas and copy to the test.

- [ ] **Step 4: Render and LOOK, beyond the samples.**
  - Build one deck per language from the matrix copy in Chinese and English: all seven pages, on 16:9, 4:3, portrait and square.
  - Render with `scripts/render_deck.py` and read the sheets. Check each item in the spec §7 list:
    - text out of frame;
    - art over words;
    - lone characters;
    - a strip or running head colliding with a headline;
    - rims on glows;
    - arrows without `ordered`.
  - Fix any defect with a test that fails first.
  - Copy the final sheets to `~/Desktop/slide-maker 新模板实现样张/` for the user.

- [ ] **Step 5: The non-Claude run.**
  - **Brief.** Dispatch a subagent on a mid-tier model (sonnet). Tell it it may read ONLY `skills/slide-maker/SKILL.md`, `references/visual-languages.md` and the output of `scripts/sigs.py`. Its task: build one 6-page deck in each new language for a topic of its choosing, using no picture except the bundled `assets/vl/photo/hall-repair.jpg` on an `image_text` page. Then render the decks, look at them and report every place where the docs misled it or where it had to guess.
  - **Afterwards.** Read its decks yourself (weak runs overclaim). Fix each real friction point in the docs or code, with a test where code changed.

- [ ] **Step 6: Final review and push only on the user's word.**
  - **Review.** Run `../subagent-driven-development/scripts/review-package` over the branch and dispatch the reviewer on the most capable model. Include the plan's Review Focus verbatim and the ledger's `Ruling:` lines. Re-grade findings by effect: Critical and Important get one fix pass, each RED→GREEN with a green suite; Minors go to the ledger.
  - **Report.** Give the user, in Chinese:
    - what was built and verified (with the counts);
    - the rulings and the deferred minors;
    - the CI wall time measured by cisteps. If the job would exceed ~22 minutes, propose moving the native-language steps into a parallel job, and ask before restructuring CI.
  - **Ask** whether to push, and whether to release (the pending v5.8.0 offer covers P3; P4 may go in the same release). Do not push or release without that answer.
  - **Install.** After a push, rsync the installed copy (`~/.agents/skills/slide-maker`, with `--checksum`, dry run first).
