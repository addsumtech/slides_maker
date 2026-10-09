# Two more native visual languages (P5: interface · wayfinding) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two more visual languages that need no pictures: `interface` (产品界面 — every page an app screen) and `wayfinding` (导视线路 — metro map + station signage). Each turns the caller's words into a finished deck on every canvas and in every script, and is offered by the direction gate when it fits the topic.

**Architecture:**
- Both names join `LANGS` / `VARIANTS` / `TYPE` / `NATIVE` / `NATIVE_EXTRAS` / `EXTRA_PAGES` in `scripts/visual_languages.py`. `use()`, grounds, `direction()`, samples, the language gate, `rs.ground` / `rs.card` then work with no extra wiring (P4 did exactly this).
- Their seven page compositions live in a new `scripts/vl_native3.py`, registered through `vl_native.register` and imported from the foot of `vl_native.py` next to `vl_native2`.
- New drawn motifs go into `scripts/native_art.py`. Text is planned with the kit's measured flow (`vl_native2.flow`, `stack`, `plan_together`), exactly as in P4.

**Tech Stack:** Python 3.9+, python-pptx, lxml, Pillow; LibreOffice for renders. Tests are plain scripts using `check()` that end with `N passed, 0 failed`; each is a step in `.github/workflows/ci.yml`.

**Spec:** `docs/superpowers/specs/2026-10-09-interface-wayfinding-languages-design.md`

**Look-dev reference (approved look, throwaway):** `/private/tmp/claude-501/-Users-donghanglyu/2866adfa-b4b0-4b62-8845-b0d5410c5fde/scratchpad/lookdev5/lookdev5.py`, sheet `~/Desktop/visual-language-lookdev.png`. Its palettes and proportions are the target; its copy is sample copy and never becomes kit text (spec §6).

**Prior art to read before Task 2:** `scripts/vl_native2.py` — `flow`, `stack`, `plan_together`, `fields`, `memo`, `tags_of`, `chip_size`, `num_value`, `lang_of`, `LABELS`, and the whole `tally` section (P5 compositions follow its plan → art → draw order). `docs/superpowers/plans/2026-10-08-five-native-languages.md` Task 7.

## Global Constraints

- **Page and file safety.** Every shape lies inside `[0, W] × [0, H]` (`ooxml_safety.beyond_page` stays `[]`); every OOXML angle in `0..21599999`, alpha in `0..100000` (`ooxml_safety.xml_findings` stays `[]`); `dk.lint_layout` reports no CRITICAL.
- **Fonts and type.** System fonts only. `fonts="both"`: Arial (both languages), Courier New (wayfinding's board). `fonts="mac"`: Helvetica Neue, Menlo. Figures are lining (Arial / Helvetica Neue / Courier New / Menlo all are).
- **Contrast.** Every text ink ≥ 4.5:1 on the ground, panel, window, sign, board, chip or button it sits on, on every ground; a meaning-bearing mark (status dot, station ring, roundel) ≥ 3:1 on what is behind it, or declared with `dk.decorative` when its meaning is also in words.
- **Words and meaning.** The kit never invents words. From the caller only, and absent → nothing drawn: `crumb=`, `status=`, `actions=`, `toggles=`, `tags=`, `total=` (interface); `line=`, `ordered=`, `interchange=`, `board=` (wayfinding). Derived, never typed: page numbers, avatar initials, browser-vs-phone frame, a section's line colour, the localised way-out label.
- **Meaning rule.** A route (claims order) is drawn only with `ordered=True`; unordered points become a directory sign. Interface status colours come from the caller's state, else the neutral primary.
- **Must not change.** The 13 existing languages behave exactly as before; their sample fingerprints (`assets/vl/samples/manifest.json`) still match a rebuild. A deck that picks neither new language imports nothing new beyond `vl_native3` (loaded only via `vl_native`, which only native decks import).
- **Delivery.** Samples are JPG ≤ 350 KB. Every new test script is wired into `ci.yml` (`check_tests_wired.py`); every new script is listed in `references/file-inventory.md` (`check_inventory.py`). Stage named paths only. Never push before the full suite, the CI-steps run and the font simulation are green, and only when the user says so; after pushing, rsync the installed copy (`~/.agents/skills/slide-maker`).

## Review Focus

1. **A long CJK crumb or status on a square or portrait canvas.** The window's top bar keeps both on one line or refuses the explicit value with `VLTextOverflow`; it never overlaps the title under it. *(Task 2 test.)*
2. **Unordered points in wayfinding.** No route line and no station circles are drawn; every point is a directory row with its numbered roundel. `interchange=` without `ordered=True` is refused by name. *(Task 3 test.)*
3. **A yellow line or roundel.** The digit on a yellow roundel is set in the dark ink (contrast picked, not assumed); a yellow route on the enamel ground is a graphic ≥ 3:1 only with its dark casing. *(Task 3 test.)*
4. **`interface.data(total=…)` with formatted numbers** (`"1,250"`, `"98.6%"`, `"$4.2M"`). Plain or percent numbers draw the right share; anything else is refused by name — the same rules as `tally`, from one shared function. *(Task 2 test.)*
5. **A tall screenshot on image_text.** A portrait picture gets the phone frame, a wide one the browser frame, from the picture's own aspect, on every canvas; the picture is never cropped. *(Task 2 test.)*

---

### Task 1: Native art for both languages (`native_art.py`)

**Files:**
- Modify: `skills/slide-maker/scripts/native_art.py` (append the functions below)
- Create: `skills/slide-maker/tests/test_native_languages_p5.py`
- Modify: `.github/workflows/ci.yml` (one step running the new test)

**Interfaces:**
- Produces (all coordinates in inches; colours as hex strings):
  - `route(slide, pts, color, *, w=0.16) -> list` — round-capped strokes through `[(x, y), …]`.
  - `station(slide, cx, cy, d, *, ring, fill="FFFFFF", w=2.25) -> shape`
  - `interchange(slide, cx, cy, w, h, *, ring, fill="FFFFFF", lw=3.0) -> shape`
  - `roundel(slide, cx, cy, d, text, *, fill, ink, size, face, ea_face=None) -> (x, y, d, d)`
  - `sign_panel(slide, x, y, w, h, *, fill, keyline="FFFFFF", r=0.12) -> (x, y, w, h)` — returns the INNER rect inside the keyline.
  - `ui_window(slide, x, y, w, h, *, fill, line, drop, r=0.22, bar=None) -> (x, y, w, h)` — `bar` = top-bar height (in) or None; returns the content rect below the bar.
  - `ui_toggle(slide, x, y, on, *, on_fill, off_line, knob="FFFFFF", w=0.62, h=0.34)`
  - `ui_button(slide, x, y, text, *, size, fill, ink, face, ea_face=None, line=None, h=None) -> (x, y, w, h)`
  - `ui_button_width(text, size, face) -> float`
  - `ui_cursor(slide, x, y, *, fill, edge, size=0.34)`
  - `ui_device(slide, x, y, w, h, kind, *, frame, screen) -> (x, y, w, h)` — `kind` "browser"|"phone"; returns the screen rect.
  - `ui_bubble(slide, x, y, w, h, *, fill, line, r=0.32) -> (x, y, w, h)`

- [ ] **Step 1: Write the failing test.** Create `tests/test_native_languages_p5.py` with the P4 scaffold (copy lines 1–118 of `tests/test_native_languages_p4.py` verbatim: imports, `check`, `check_mac`, `lum`, `cr`, `EMU`, `rect_of`, `texts`, `txt_of`, `use`, `td`, `PHOTO`, `CANVASES`, `COPY`, `EXTRAS`, `build_matrix`, `assert_matrix`, `assert_palettes`), change the docstring to "The P5 native languages: interface and wayfinding …", change the vertical-setting message to `"no vertical setting in P5"`, then append:

```python
# ── native art (Task 1) ──
import native_art as na
from pptx.oxml.ns import qn
prs = dk.blank_deck(13.333, 7.5)
s = dk.add_slide(prs)
segs = na.route(s, [(0.0, 2.0), (5.0, 2.0), (6.5, 3.5)], "D7262E", w=0.16)
check(len(segs) == 2 and all(c._element.spPr.find(qn("a:ln")).get("cap") == "rnd" for c in segs),
      "route: one round-capped stroke per leg")
check(abs(segs[0]._element.spPr.find(qn("a:ln")).get("w") and int(segs[0]._element.spPr.find(qn("a:ln")).get("w")) / 12700 - 0.16 * 72) < 0.6,
      "route: the stroke is w inches wide")
st = na.station(s, 2.0, 2.0, 0.3, ring="16191E")
check(abs(st.width / EMU - 0.3) < 1e-3 and abs((st.left + st.width / 2) / EMU - 2.0) < 1e-3, "station: centred, d wide")
ic = na.interchange(s, 6.5, 3.5, 1.0, 0.7, ring="16191E")
check(abs(ic.width / EMU - 1.0) < 1e-3 and ic._element.xpath(".//a:prstGeom[@prst='roundRect']"), "interchange: a rounded rect")
x, y, d, _ = na.roundel(s, 9.0, 2.0, 0.5, "1", fill="D7262E", ink="FFFFFF", size=17, face="Arial")
tb = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text == "1"]
check(tb and tb[0].text_frame.word_wrap is False and abs(x + d / 2 - 9.0) < 1e-6, "roundel: one unwrapped label, centred")
inner = na.sign_panel(s, 1.0, 5.0, 6.0, 1.0, fill="1B2A41")
check(inner[0] > 1.0 and inner[2] < 6.0 and inner[3] < 1.0, "sign_panel: returns the rect inside the keyline")
win = na.ui_window(s, 1.0, 1.0, 6.0, 3.0, fill="FFFFFF", line="E2E5EB", drop="DDE1E8", bar=0.62)
check(abs(win[1] - (1.0 + 0.62)) < 1e-6 and abs(win[3] - (3.0 - 0.62)) < 1e-6, "ui_window: the content rect starts below the bar")
w1 = na.ui_button_width("Get started", 15, "Arial")
w2 = na.ui_button_width("Get started now please", 15, "Arial")
check(0.8 < w1 < w2, "ui_button_width: measured, grows with the words")
bx = na.ui_button(s, 1.0, 4.4, "Get started", size=15, fill="2F6BFF", ink="FFFFFF", face="Arial")
check(abs(bx[2] - w1) < 1e-6, "ui_button: as wide as its measured words")
scr = na.ui_device(s, 8.0, 1.0, 4.0, 3.0, "browser", frame="FFFFFF", screen="F6F7FA")
check(scr[1] > 1.0 and scr[0] >= 8.0 and scr[0] + scr[2] <= 12.0, "ui_device(browser): the screen sits under the bar")
scr = na.ui_device(s, 8.0, 4.0, 1.6, 3.0, "phone", frame="0F1115", screen="FFFFFF")
check(scr[0] > 8.0 and scr[2] < 1.6, "ui_device(phone): the screen sits inside the bezel")
try:
    na.ui_device(s, 1, 1, 1, 1, "tablet", frame="FFFFFF", screen="FFFFFF")
    check(False, "ui_device refuses an unknown kind")
except ValueError as e:
    check("tablet" in str(e), "ui_device refuses an unknown kind by name")
na.ui_toggle(s, 3.0, 6.5, True, on_fill="2F6BFF", off_line="8A91A0")
na.ui_cursor(s, 4.0, 6.5, fill="0F1115", edge="FFFFFF")
na.ui_bubble(s, 6.0, 5.5, 3.0, 1.5, fill="FFFFFF", line="E2E5EB")
p = td / "art.pptx"
prs.save(str(p))
check(ox.xml_findings(str(p)) == [] and ox.beyond_page(prs) == [], "native art: PowerPoint-safe and on the page")

print("{} passed, {} failed".format(len(ok), len(bad)))
for b in bad:
    print("FAIL:", b)
for s_ in skipped:
    print("SKIP:", s_)
sys.exit(1 if bad else 0)
```

Keep the four `print`/`sys.exit` lines as the file's last lines in every later task (later tasks insert their tests ABOVE them).

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p5.py | tail -3`
Expected: `AttributeError: module 'native_art' has no attribute 'route'`.

- [ ] **Step 3: Implement.** Append to `native_art.py`:

```python
# ═══════════════════ P5: wayfinding (metro map + signage) and interface (app UI) ═══════════════════
def route(slide, pts, color, *, w=0.16):
    """A transit route through `pts` [(x, y), …] — horizontal, vertical or 45° legs — as round-capped strokes `w` in
    wide. Clipped to the page by seg(); a cap may overhang the edge, which beyond_page() does not count (it reads
    the connector's box)."""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        c = seg(slide, x0, y0, x1, y1, color, w=w * 72.0)
        c._element.spPr.find(qn("a:ln")).set("cap", "rnd")
        out.append(c)
    return out


def station(slide, cx, cy, d, *, ring, fill="FFFFFF", w=2.25):
    """A station: a white disc with a dark ring, centred on (cx, cy)."""
    return dk.disc(slide, cx - d / 2.0, cy - d / 2.0, d, fill=hexstr(fill), line=dk._as_rgb(hexstr(ring)), line_w=w)


def interchange(slide, cx, cy, w, h, *, ring, fill="FFFFFF", lw=3.0):
    """An interchange: a white rounded rectangle with a heavy dark ring, centred on (cx, cy)."""
    return dk.box(slide, cx - w / 2.0, cy - h / 2.0, w, h, fill=hexstr(fill), line=dk._as_rgb(hexstr(ring)),
                  line_w=lw, round=True, r=min(w, h) / 2.0)


def roundel(slide, cx, cy, d, text, *, fill, ink, size, face, ea_face=None):
    """A line roundel: a filled disc with one short unwrapped label. Returns (x, y, d, d)."""
    x, y = cx - d / 2.0, cy - d / 2.0
    dk.disc(slide, x, y, d, fill=hexstr(fill))
    run = (text, size, dk._as_rgb(hexstr(ink)), True, False, face) + ((ea_face,) if ea_face else ())
    tb = dk.text(slide, x, y, d, d, [[run]], align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    tb.text_frame.word_wrap = False
    dk.overlap_intent(tb, "the label sits on its own roundel")
    return (x, y, d, d)


def sign_panel(slide, x, y, w, h, *, fill, keyline="FFFFFF", r=0.12):
    """An enamel sign: a rounded panel with a white keyline inset by 0.07in. Returns the rect inside the keyline."""
    dk.box(slide, x, y, w, h, fill=hexstr(fill), round=True, r=r)
    k = dk.box(slide, x + 0.07, y + 0.07, w - 0.14, h - 0.14, fill=None, line=dk._as_rgb(hexstr(keyline)), line_w=1.5,
               round=True, r=max(0.02, r - 0.04))
    dk.decorative(k, "the sign's keyline")
    return (x + 0.07, y + 0.07, w - 0.14, h - 0.14)


def ui_window(slide, x, y, w, h, *, fill, line, drop, r=0.22, bar=None):
    """An app window: a flat drop offset under a rounded panel with a hairline, and an optional top bar separated by
    a hairline. Returns the content rect (below the bar)."""
    d = dk.box(slide, x + 0.04, y + 0.08, w, h, fill=hexstr(drop), round=True, r=r)
    dk.decorative(d, "the window's drop edge")
    dk.box(slide, x, y, w, h, fill=hexstr(fill), line=dk._as_rgb(hexstr(line)), line_w=0.75, round=True, r=r)
    if bar:
        hl = dk.box(slide, x, y + bar, w, 0.012, fill=hexstr(line))
        dk.decorative(hl, "the top bar's hairline")
        return (x, y + bar, w, h - bar)
    return (x, y, w, h)


def ui_toggle(slide, x, y, on, *, on_fill, off_line, knob="FFFFFF", w=0.62, h=0.34):
    """A switch: an on track filled with the primary, an off track outlined; the knob at the matching end."""
    if on:
        dk.box(slide, x, y, w, h, fill=hexstr(on_fill), round=True, r=h / 2.0)
    else:
        dk.box(slide, x, y, w, h, fill=None, line=dk._as_rgb(hexstr(off_line)), line_w=1.25, round=True, r=h / 2.0)
    d = h - 0.08
    dk.disc(slide, x + (w - d - 0.04 if on else 0.04), y + 0.04, d,
            fill=hexstr(knob if on else off_line))


def ui_button_width(text, size, face):
    """A button as wide as its words plus 1.6 em of padding (chip_width carries 1.2 em; a button breathes more)."""
    return chip_width(text, size, face) + 0.4 * size / 72.0 + 0.3


def ui_button(slide, x, y, text, *, size, fill, ink, face, ea_face=None, line=None, h=None):
    """A pill button, one line that never wraps, its width measured. Returns (x, y, w, h)."""
    w = ui_button_width(text, size, face)
    h = h or size / 72.0 * 2.6
    dk.box(slide, x, y, w, h, fill=hexstr(fill) if fill else None, line=dk._as_rgb(hexstr(line)) if line else None,
           line_w=1.0, round=True, r=h / 2.0)
    run = (text, size, dk._as_rgb(hexstr(ink)), True, False, face) + ((ea_face,) if ea_face else ())
    tb = dk.text(slide, x, y, w, h, [[run]], align=dk.PP_ALIGN.CENTER, anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    tb.text_frame.word_wrap = False
    dk.overlap_intent(tb, "the label sits on its own button")
    return (x, y, w, h)


def ui_cursor(slide, x, y, *, fill, edge, size=0.34):
    """A pointer arrow resting at (x, y) — its tip — drawn as a tilted triangle with a light edge."""
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt
    sh = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(x), Inches(y), Inches(size * 0.76), Inches(size))
    sh.rotation = 332.0
    sh.fill.solid()
    sh.fill.fore_color.rgb = dk._as_rgb(hexstr(fill))
    sh.line.color.rgb = dk._as_rgb(hexstr(edge))
    sh.line.width = Pt(1.5)
    dk.adopt(sh)
    dk.decorative(sh, "a pointer resting on the primary button")
    return sh


def ui_device(slide, x, y, w, h, kind, *, frame, screen):
    """A device frame around a picture: "browser" (a window with a slim bar and three dots) or "phone" (a rounded
    bezel). Returns the screen rect the picture goes in."""
    if kind == "browser":
        dk.box(slide, x, y, w, h, fill=hexstr(frame), line=dk._as_rgb(hexstr(screen)), line_w=0.75, round=True, r=0.14)
        bar = min(0.36, 0.09 * h)
        for i in range(3):
            dot = dk.disc(slide, x + 0.16 + i * 0.16, y + bar / 2.0 - 0.045, 0.09, fill=hexstr(screen))
            dk.decorative(dot, "browser window chrome")
        return (x + 0.06, y + bar, w - 0.12, h - bar - 0.06)
    if kind == "phone":
        dk.box(slide, x, y, w, h, fill=hexstr(frame), round=True, r=min(w, h) * 0.16)
        m = max(0.06, 0.045 * w)
        return (x + m, y + m * 1.6, w - 2 * m, h - m * 3.2)
    raise ValueError("ui_device(): kind must be 'browser' or 'phone', got {!r}".format(kind))


def ui_bubble(slide, x, y, w, h, *, fill, line, r=0.32):
    """A chat bubble: a rounded panel whose top-left corner is square (the tail side). Returns its rect."""
    dk.box(slide, x, y, w, h, fill=hexstr(fill), line=dk._as_rgb(hexstr(line)), line_w=0.75, round=True, r=r)
    sq = dk.box(slide, x, y, r, r, fill=hexstr(fill))
    dk.decorative(sq, "the bubble's tail corner")
    return (x, y, w, h)
```

Then add the CI step after the P4 native-languages step in `.github/workflows/ci.yml`:

```yaml
      - name: Native visual languages P5 (interface, wayfinding)
        run: python3 skills/slide-maker/tests/test_native_languages_p5.py
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p5.py | tail -3 && python3 scripts/check_tests_wired.py`
Expected: `… passed, 0 failed`; the wiring check passes.

- [ ] **Step 5: Commit**

```bash
git add skills/slide-maker/scripts/native_art.py skills/slide-maker/tests/test_native_languages_p5.py .github/workflows/ci.yml
git commit -m "native art for P5: routes, stations, roundels, signs; app windows, toggles, buttons, devices, bubbles"
```

---

### Task 2: `interface` 产品界面

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py` — `LANGS`, `VARIANTS`, `TYPE`, `NATIVE`, `NATIVE_EXTRAS`, `EXTRA_PAGES`, `_ground_interface`, `_card_interface`, `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Create: `skills/slide-maker/scripts/vl_native3.py`
- Modify: `skills/slide-maker/scripts/vl_native.py` (import `vl_native3` at the foot, after `vl_native2`)
- Modify: `skills/slide-maker/scripts/vl_native2.py` — extract tally's total= rules into `share_of(lang, num, total)` and call it from `_tl_data` (behaviour unchanged)
- Test: `skills/slide-maker/tests/test_native_languages_p5.py` (insert above the final prints)

**Interfaces:**
- Consumes: Task 1's `ui_*` functions; `vl_native2.flow/stack/plan_together/fields/memo/tags_of/chip_size/num_value/lang_of`.
- Produces:
  - `vl_native2.share_of(lang, num, total) -> float|None` (None when `total` is None; ValueError naming `total=` otherwise as `tally` did)
  - `vl_native3.ui_state(v, page, name) -> (text, state)`
  - `vl_native3.initials(attribution) -> str|None`
  - `vl_native3.device_for(path) -> "browser"|"phone"`
  - seven `@register("interface", page, alts=2)` compositions

- [ ] **Step 1: Write the failing tests.** Insert above the final prints:

```python
# ── interface 产品界面 ──
EXTRAS["interface"] = lambda lang, n: {
    "cover": {"crumb": "Launch › Overview", "status": ("Live", "on"), "actions": ["Get started", "Watch demo"],
              "toggles": [("Auto-sync", True), ("Public link", False)]},
    "points": {"tags": [("Required", "pending")] + ["New"] * (n - 1)},
    "data": {"total": "12"},
    "closing": {"actions": ["Start free"]}}
check("interface" in vl.NATIVE and set(vl.VARIANTS["interface"]) == {"light", "dark"}, "interface: two grounds")
assert_palettes("interface")
for g, V in vl.VARIANTS["interface"].items():
    p = V["palette"]
    check(cr("FFFFFF", p["primary_fill"]) >= 4.5, "interface/{}: white on the primary button".format(g))
    for st, c in p["states"].items():
        check(cr(c, p["panel"]) >= 3.0, "interface/{}: the {} dot reads on a window (3:1)".format(g, st))
    check(cr(p["off_line"], p["panel"]) >= 3.0, "interface/{}: an off switch's outline reads (3:1)".format(g))
assert_matrix("interface")
import vl_native3 as v3
check(v3.initials("Maya Kowalski, Operations lead") == "MK" and v3.initials("Ada") == "A"
      and v3.initials("茶室题记") is None and v3.initials("") is None, "interface: initials derived from Latin names only")
check(v3.ui_state("Live", "cover", "status") == ("Live", "primary") and v3.ui_state(("Beta", "pending"), "cover", "status")
      == ("Beta", "pending"), "interface: a state is the caller's, else primary")
try:
    v3.ui_state(("Beta", "green"), "cover", "status")
    check(False, "interface: an unknown state is refused")
except ValueError as e:
    check("status=" in str(e) and "pending" in str(e), "interface: an unknown state is refused by name")
# Review Focus 5: the frame follows the picture's aspect
from PIL import Image as _I
tall, wide = td / "tall.png", td / "wide.png"
_I.new("RGB", (390, 844), "white").save(tall); _I.new("RGB", (1600, 1000), "white").save(wide)
check(v3.device_for(str(tall)) == "phone" and v3.device_for(str(wide)) == "browser", "interface: phone for tall, browser for wide")
for W, H in CANVASES.values():
    for pic in (tall, wide):
        prs, k = use("interface", W, H)
        s = k.new_slide(); k.image_text(s, kicker="Tour", title="The new board", body="Everything in one place.", image=str(pic))
        pics = [sh for sh in s.shapes if sh.shape_type == 13]
        r_ = pics[0].width / pics[0].height
        a_ = _I.open(pic).size[0] / _I.open(pic).size[1]
        check(abs(r_ - a_) / a_ < 0.03, "interface {}x{}: the {} picture keeps its aspect".format(W, H, pic.stem))
# Review Focus 4: total= follows tally's rules from one function
import vl_native2 as v2
check(v2.share_of("interface", "12", "40") == 0.3 and v2.share_of("interface", "98.6%", "100%") == 0.986
      and v2.share_of("interface", "$4.2M", None) is None, "share_of: plain and percent numbers")
for num, total in (("$4.2M", "10"), ("50", "40"), ("12", "0"), ("12%", "40")):
    prs, k = use("interface")
    try:
        k.data(k.new_slide(), number=num, label="x", total=total)
        check(False, "interface: number={!r} total={!r} is refused".format(num, total))
    except ValueError as e:
        check("total" in str(e), "interface: number={!r} total={!r} is refused by name".format(num, total))
# Review Focus 1: a long CJK crumb and status stay on one line or are refused; never over the title
for W, H in ((7.5, 7.5), (7.5, 13.333)):
    prs, k = use("interface", W, H)
    s = k.new_slide()
    try:
        k.cover(s, title="产品发布", crumb="发布会 › 产品概览 › 新工作台", status=("内测中", "pending"))
        tb = {txt_of(sh): sh for sh in texts(s)}
        ttl = [sh for t_, sh in tb.items() if t_.startswith("产品")][0]
        bar = [sh for t_, sh in tb.items() if "发布会" in t_]
        check(bar and bar[0].text_frame.word_wrap is False or len(bar[0].text_frame.paragraphs) == 1,
              "interface {}x{}: the crumb is one line".format(W, H))
        check(not v2.meet(rect_of(bar[0]), rect_of(ttl)), "interface {}x{}: the crumb clears the title".format(W, H))
    except vl.VLTextOverflow as e:
        check("crumb" in str(e) or "status" in str(e), "interface {}x{}: refused by name: {}".format(W, H, e))
# the words are the caller's: no crumb/status/actions/toggles given → none drawn
prs, k = use("interface")
s = k.new_slide(); k.cover(s, title="Ship the feature", subtitle="A tour")
check(sorted(txt_of(sh) for sh in texts(s)) == sorted(["Ship the feature", "A tour"]), "interface: no extras → no invented words")
check(not [sh for sh in s.shapes if sh.rotation and abs(sh.rotation - 332.0) < 0.5], "interface: no action → no pointer")
# the remembered crumb reaches an ORDINARY page's window
import register_surface as rs
prs, k = use("interface")
k.cover(k.new_slide(), title="Ship it", crumb="Launch › Overview")
s = k.new_slide()
rect = rs.ground(s, k.name, role="content", index=2)
check(any(txt_of(sh) == "Launch › Overview" for sh in texts(s)) and rect[2] > 5, "interface: an ordinary page is a window")
# points: one chip per tag, coloured by the caller's state (pending → the pending dot)
prs, k = use("interface")
s = k.new_slide()
k.points(s, title="Three settings", items=["Approvals", "One source", "Weekly digest"], tags=[("Required", "pending"), "On", "New"])
dots = [sh for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']") and sh.width / EMU < 0.15]
fills = {str(sh.fill.fore_color.rgb) for sh in dots}
check(vl.VARIANTS["interface"]["light"]["palette"]["states"]["pending"] in fills, "interface: a pending tag carries the pending dot")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p5.py | tail -3`
Expected: `KeyError: 'interface'` (from `EXTRAS`/`vl.VARIANTS`).

- [ ] **Step 3: Implement.**

(a) `visual_languages.py` tables.
- `LANGS` (after `"chalkboard"`):

  ```python
      "interface": {
          "palette": {"ground": "F3F4F7", "ink": "0F1115", "mute": "5B6170", "panel": "FFFFFF",
                      "accents": ["2F6BFF", "16A34A", "D97706", "DC2626"], "text_accents": ["1F55E0"],
                      "line": "E2E5EB", "soft": "F6F7FA", "drop": "DDE1E8", "primary_fill": "2F6BFF",
                      "off_line": "8A91A0",
                      "states": {"primary": "2F6BFF", "on": "16A34A", "pending": "D97706", "error": "DC2626"}},
          "fonts": {"both": {"display": "Arial", "body": "Arial", "numeral": "Arial"},
                    "mac": {"display": "Helvetica Neue", "body": "Helvetica Neue", "numeral": "Helvetica Neue"}},
          "ea": {"display": "sans", "body": "sans"}, "grain": 0, "frames": ["rect"],
          "forbids": ("confetti",), "cover": "low-left", "skeleton": "island"},
  ```

- `VARIANTS`:

  ```python
      "interface": {
          "light": {"label": "app light", "label_zh": "浅色界面版", "grain": 0, "palette": LANGS["interface"]["palette"]},
          "dark": {"label": "dark mode", "label_zh": "深色模式版", "grain": 0,
                   "palette": {"ground": "0E1014", "ink": "F2F4F8", "mute": "A3AAB8", "panel": "171A21",
                               "accents": ["5B8CFF", "2DBE6C", "F5B83D", "FF6B70"], "text_accents": ["8FB0FF"],
                               "line": "2A2F3A", "soft": "1E222B", "drop": "07080B", "primary_fill": "2F6BFF",
                               "off_line": "7A8294",
                               "states": {"primary": "5B8CFF", "on": "2DBE6C", "pending": "F5B83D", "error": "FF6B70"}}}},
  ```

- `TYPE`:

  ```python
      "interface": {"kicker": (13, "body", True, "mute", False, 9), "title": (54, "display", True, "ink", False, 26),
                    "subtitle": (20, "body", False, "mute", False, 12), "body": (17, "body", False, "ink", False, 11),
                    "quote": (34, "display", True, "ink", False, 18), "attribution": (14, "body", False, "mute", False, 10),
                    "number": (150, "numeral", True, "ink", False, 54), "label": (22, "body", True, "mute", False, 13),
                    "note": (15, "body", False, "ink", False, 10), "caption": (12, "body", False, "mute", False, 9),
                    "line": (20, "body", False, "mute", False, 12), "item_head": (22, "body", True, "ink", False, 13),
                    "item_line": (16, "body", False, "mute", False, 10), "item_no": (20, "display", True, "accent", False, 13),
                    "tag": (13, "body", True, "ink", False, 9), "crumb": (13, "body", False, "mute", False, 9),
                    "status": (12, "body", True, "ink", False, 9), "action": (16, "body", True, "ink", False, 11),
                    "toggle": (16, "body", True, "ink", False, 11), "initials": (24, "display", True, "ink", False, 14),
                    "mark": (60, "display", True, "accent", False, 30)},
  ```

- `NATIVE += ("interface",)` (it is a tuple: rebuild it as `NATIVE = (... , "chalkboard", "interface")` in place).
- `NATIVE_EXTRAS["interface"] = ("crumb", "status", "actions", "toggles", "tags", "total")`.
- `EXTRA_PAGES.update({"actions": ("cover", "closing"), "toggles": ("cover",)})` — `tags`/`total` already map to `points`/`data`; `crumb`/`status` are on every page (absent from `EXTRA_PAGES`, like `masthead`).
- Ground and card (next to `_ground_chalkboard`):

  ```python
  def _ground_interface(slide, role, index):
      """An ordinary page in the interface language is a window: the content rect is inside it, below its bar."""
      import vl_native3
      return vl_native3.ordinary_window(slide)
  ```

  and `_card_interface = _card_for("interface")`.
- `_DISPLAY_NAMES["interface"] = "Product interface"`; `_RATIONALE["interface"] = "drawn, no pictures: every page an app screen — windows, status chips, a settings list, a dashboard card, a dialog"`.
- `_SAMPLE_COPY_NATIVE["interface"]`:

  ```python
      "interface": [("cover", dict(kicker="Product tour", title="One board for every request",
                                   subtitle="A ten-minute tour of the new workspace", crumb="Launch › Overview",
                                   status=("Live", "on"), actions=["Get started", "Watch demo"],
                                   toggles=[("Auto-sync", True), ("Share with team", True), ("Public link", False)])),
                    ("points", dict(title="Three settings change how a team works",
                                    items=[("Approvals before anything is sent", "Drafts wait until a lead signs off"),
                                           ("One shared source of truth", "Every edit syncs to the same page"),
                                           ("A weekly digest instead of pings", "Notifications batch into one summary")],
                                    tags=[("Required", "pending"), ("On", "on"), "New"])),
                    ("quote", dict(quote="We stopped chasing status updates. The board just tells us.",
                                   attribution="Style sample")),
                    ("data", dict(number="12", label="of 40 teams switched", note="Style sample — your numbers go here.",
                                  total="40"))],
  ```

(b) `vl_native2.py`: replace the validation block at the top of `_tl_data` with a call, and add the shared function above `@register("tally", "cover", …)`:

```python
def share_of(lang, num, total):
    """total= as a share: num/total for two plain or percent numbers of the same kind, num <= total; None when total
    is None. Anything else is refused by name — the bar must never show a fraction it cannot read (tally, interface)."""
    if total is None:
        return None
    v, t = num_value(num), num_value(total)
    if v is None or t is None:
        raise ValueError("{}.data(): total= draws a share bar, so number= and total= must both be plain, non-negative "
                         "numbers (12, 1,250, 98.6%) — got number={!r}, total={!r}".format(lang, num, total))
    if t <= 0:
        raise ValueError("{}.data(): total= must be greater than 0 — a share of nothing has no bar (got total={!r})"
                         .format(lang, total))
    if ("%" in (num or "")) != ("%" in total):
        raise ValueError("{}.data(): number= and total= must both be percentages or neither — got {!r} and "
                         "total={!r}".format(lang, num, total))
    if v > t:
        raise ValueError("{}.data(): the number {!r} is larger than total={!r} — a share cannot exceed its whole"
                         .format(lang, num, total))
    return v / t
```

In `_tl_data`, the lines from `frac = None` through `frac = v / t` become `frac = share_of("tally", num, total)`.

(c) `vl_native.py`, last line: `import vl_native3  # noqa: E402,F401` after `import vl_native2`.

(d) Create `vl_native3.py`:

```python
#!/usr/bin/env python3
"""vl_native3 — page compositions of the P5 native visual languages: interface (产品界面) and wayfinding (导视线路).

Same contract as vl_native2, which this module builds on: each page PLANS its text by measurement, draws its art
clear of that text, then sets the text. Nothing here invents a word: crumb / status / actions / toggles / tags /
total (interface) and line / ordered / interchange / board (wayfinding) come from the caller or nothing is drawn.
Page numbers, avatar initials, the device frame, a section's line colour and the way-out label are derived.
"""
from __future__ import annotations

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import _run_all, alt, ctx, points_of, register, text_of
from vl_native2 import chip_size, fields, flow, lang_of, meet, memo, plan_together, share_of, stack, tags_of  # noqa: F401

STATES = ("primary", "on", "pending", "error")


def _hex(v):
    return vl._hex(v)


# ═══════════════════════════════════ interface 产品界面 ═══════════════════════════════════
def ui_state(v, page, name):
    """An extra given as text or (text, state): -> (text, state), state one of STATES, default 'primary'."""
    if isinstance(v, (list, tuple)) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], str):
        t, st = v[0].strip(), v[1].strip()
        if st not in STATES:
            raise ValueError("interface.{}(): {}= state must be one of {} — got {!r}".format(page, name, list(STATES), st))
        if t:
            return t, st
    elif isinstance(v, str) and v.strip():
        return v.strip(), "primary"
    raise ValueError("interface.{}(): {}= takes words, or (words, state) with state in {} — got {!r}"
                     .format(page, name, list(STATES), v))


def initials(attribution):
    """Avatar initials from a Latin attribution: the first letters of its first two words (before any comma). CJK or
    empty -> None (no avatar: a Chinese name is not abbreviated by its first characters)."""
    t = (attribution or "").split(",")[0].strip()
    if not t or dk._has_cjk(t):
        return None
    words = [w for w in t.split() if w[:1].isalpha()]
    return "".join(w[0].upper() for w in words[:2]) or None


def device_for(path):
    """'phone' for a picture taller than wide, else 'browser' — derived from the picture, never chosen."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    return "phone" if h > w * 1.05 else "browser"


def _actions(f, page):
    v = f.get("actions")
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= 2 or not all(isinstance(a, str) and a.strip() for a in v):
        raise ValueError("interface.{}(): actions= takes 1 or 2 button labels (primary, secondary), got {!r}".format(page, v))
    return [a.strip() for a in v]


def _toggles(f):
    v = f.get("toggles")
    if v is None:
        return []
    ok_ = isinstance(v, (list, tuple)) and 1 <= len(v) <= 4 and all(
        isinstance(t, (list, tuple)) and len(t) == 2 and isinstance(t[0], str) and t[0].strip() and isinstance(t[1], bool)
        for t in v)
    if not ok_:
        raise ValueError("interface.cover(): toggles= takes 1 to 4 (label, True/False) rows, got {!r}".format(v))
    return [(t[0].strip(), t[1]) for t in v]


def _bar_h(k):
    return 0.62 * ctx(k)[2]


def _top_bar(k, slide, win, f, page):
    """The window's bar: the crumb (remembered) left, the status chip (remembered) right. The crumb is one line at
    its size or its floor, else refused. Draws at once."""
    W, H, s, o = ctx(k)
    x, y, w, _h = win
    bh = _bar_h(k)
    crumb = memo(k, f, "crumb")
    st = f.get("status") if f.get("status") is not None else k.memo.get("status")
    if f.get("status") is not None:
        k.memo = dict(k.memo, status=f.get("status"))
    right = x + w - 0.32 * s
    if st is not None:
        t, state = ui_state(st, page, "status")
        sz = chip_size(k, t, 0.45 * w, "status")
        if sz is None:
            raise vl.VLTextOverflow("interface.{}(): status={!r} does not fit the window's bar".format(page, t))
        cw = na.chip_width(t, sz, k.face("body")) + 0.22 * s
        ch = sz / 72.0 * 1.9
        cx = right - cw
        cy = y + (bh - ch) / 2.0
        na.chip(slide, cx, cy, t, size=sz, fill=k.P["soft"], ink=k.P["ink"], face=k.face("body"),
                ea_face=k.ea_face("body", t))
        dot = dk.disc(slide, cx + 0.10 * s, cy + ch / 2.0 - 0.045 * s, 0.09 * s, fill=_hex(k.P["states"][state]))
        dk.decorative(dot, "the status is named in the chip's words")
        right = cx - 0.2 * s
    if crumb:
        cw = right - (x + 0.32 * s)
        sz = chip_size(k, crumb, cw, "crumb")
        if sz is None:
            raise vl.VLTextOverflow("interface.{}(): crumb={!r} does not fit the window's bar on one line"
                                    .format(page, crumb))
        tb = dk.text(slide, x + 0.32 * s, y, cw, bh, [k.runs(crumb, sz, k.color("mute"))], anchor=dk.MSO_ANCHOR.MIDDLE,
                     space_after=0)
        tb.text_frame.word_wrap = False


def _window(k, slide, rect, f, page, *, bar=True):
    """Draw a window with its bar; returns the content rect inside it (padded)."""
    W, H, s, o = ctx(k)
    inner = na.ui_window(slide, *rect, fill=k.P["panel"], line=k.P["line"], drop=k.P["drop"], r=0.22 * s,
                         bar=_bar_h(k) if bar else None)
    if bar:
        _top_bar(k, slide, rect, f, page)
    p = 0.42 * s
    return (inner[0] + p, inner[1] + 0.3 * s, inner[2] - 2 * p, inner[3] - 0.3 * s - p)


def ordinary_window(slide):
    """rs.ground for interface: the page is one window (with the deck's remembered crumb and status)."""
    import vl_native2 as v2
    k = v2.kit_for("interface", slide)
    W, H, s, o = ctx(k)
    return _window(k, slide, (0.06 * W, 0.08 * H, 0.88 * W, 0.84 * H), {}, "ordinary")


def _buttons(k, slide, x, y, acts, max_w):
    """The caller's actions as buttons from (x, y): primary filled, secondary outlined; a pointer on the primary.
    Returns the row's height; refuses a row that cannot fit max_w."""
    W, H, s, o = ctx(k)
    if not acts:
        return 0.0
    sz = vl.TYPE["interface"]["action"][0] * s
    widths = [na.ui_button_width(a, sz, k.face("body")) for a in acts]
    while sum(widths) + 0.2 * s * (len(acts) - 1) > max_w and sz > vl.TYPE["interface"]["action"][5] * s:
        sz *= 0.92
        widths = [na.ui_button_width(a, sz, k.face("body")) for a in acts]
    if sum(widths) + 0.2 * s * (len(acts) - 1) > max_w:
        raise vl.VLTextOverflow("interface: actions={!r} do not fit one row".format(acts))
    h = sz / 72.0 * 2.6
    cx = x
    for i, a in enumerate(acts):
        if i == 0:
            fill, ink = k.P["primary_fill"], ("FFFFFF" if vl._contrast("FFFFFF", k.P["primary_fill"]) >= 4.5 else k.P["ink"])
            b = na.ui_button(slide, cx, y, a, size=sz, fill=fill, ink=ink, face=k.face("body"),
                             ea_face=k.ea_face("body", a), h=h)
            na.ui_cursor(slide, b[0] + b[2] * 0.82, b[1] + b[3] * 0.62, fill=k.P["ink"], edge=k.P["panel"], size=0.34 * s)
        else:
            b = na.ui_button(slide, cx, y, a, size=sz, fill=k.P["panel"], ink=k.P["ink"], face=k.face("body"),
                             ea_face=k.ea_face("body", a), line=k.P["off_line"], h=h)
        cx = b[0] + b[2] + 0.2 * s
    return h


@register("interface", "cover", alts=2)
def _ui_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    acts, tog = _actions(f, "cover"), _toggles(f)
    side = bool(tog) and o == "land"
    if o == "land":
        win = (0.06 * W, (0.15 if alt() == 0 else 0.08) * H, (0.60 if side else 0.88) * W, (0.74 if alt() == 0 else 0.84) * H)
    else:
        win = (0.07 * W, 0.06 * H, 0.86 * W, (0.56 if tog else 0.84) * H)
    col = _window(k, slide, win, f, "cover")
    bh = (vl.TYPE["interface"]["action"][0] * s / 72.0 * 2.6 + 0.35 * s) if acts else 0.0
    r, ds = stack(k, slide, "cover", col[0], col[2], col[1], col[1] + col[3] - bh,
                  [(fields(f, ("kicker",)), 0.12 * s), (fields(f, ("title",)), 0.25 * s), (fields(f, ("subtitle",)), 0.0)],
                  anchor="middle")
    _run_all(ds)
    if acts:
        foot = max(v[1] + v[3] for v in r.values()) if r else col[1]
        _buttons(k, slide, col[0], foot + 0.35 * s, acts, col[2])
    if tog:
        if side:
            px, py, pw = 0.69 * W, win[1], 0.25 * W
        else:
            px, py, pw = 0.07 * W, win[1] + win[3] + 0.25 * s, 0.86 * W
        rows = [(lab, on) for lab, on in tog]
        tw, th = 0.62 * s, 0.34 * s
        specs = [((0, 0, pw - 0.84 * s - tw - 0.2 * s, 10.0), [("toggle", lab)], {}) for lab, _on in rows]
        planned = plan_together(k, slide, "cover", specs)
        hs = [max(v[3] for v in rr.values()) for rr, _d in planned]
        ph = sum(max(hh, th) for hh in hs) + 0.42 * s * len(rows) + 0.42 * s
        if py + ph > H - 0.3 * s:
            raise vl.VLTextOverflow("interface.cover(): toggles= need more room than the page has")
        na.ui_window(slide, px, py, pw, ph, fill=k.P["panel"], line=k.P["line"], drop=k.P["drop"], r=0.22 * s)
        yy = py + 0.42 * s
        for (lab, on), hh in zip(rows, hs):
            rowh = max(hh, th)
            rr, d = flow(k, slide, "cover", (px + 0.42 * s, yy + (rowh - hh) / 2.0, pw - 0.84 * s - tw - 0.2 * s, hh),
                         [("toggle", lab)], start={"toggle": min(getattr(dd, "sizes", {}).get("toggle", 99) for _r2, dd in planned)})
            d()
            na.ui_toggle(slide, px + pw - 0.42 * s - tw, yy + (rowh - th) / 2.0, on, on_fill=k.P["states"]["primary"],
                         off_line=k.P["off_line"], w=tw, h=th)
            yy += rowh + 0.42 * s
    return r


@register("interface", "section", alts=2)
def _ui_section(k, slide, f, image):
    """A tab: the section number in a rounded badge, kicker and title beside it, the active-tab bar under the title."""
    W, H, s, o = ctx(k)
    top = (0.26 if alt() == 0 else 0.14) * H
    win = (0.06 * W, top, 0.88 * W, H - 2 * top) if o == "land" else (0.07 * W, 0.16 * H, 0.86 * W, 0.68 * H)
    col = _window(k, slide, win, f, "section")
    num = text_of(f, "number")
    x = col[0]
    if num:
        bs = min(1.6 * s, col[3] * 0.8)
        by = col[1] + (col[3] - bs) / 2.0 if o == "land" else col[1]
        dk.box(slide, x, by, bs, bs, fill=_hex(k.P["primary_fill"]), round=True, r=0.22 * s)
        r0, d0 = flow(k, slide, "section", (x, by, bs, bs), [("number", num)], anchor="middle", align="c",
                      ink="FFFFFF", start={"number": 72 * s})
        d0()
        if o == "land":
            x = x + bs + 0.5 * s
            col = (x, col[1], col[0] + col[2] - x, col[3])
        else:
            col = (col[0], by + bs + 0.4 * s, col[2], col[1] + col[3] - by - bs - 0.4 * s)
    r, ds = stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3] - 0.3 * s,
                  [(fields(f, ("kicker",)), 0.12 * s), (fields(f, ("title",)), 0.0)], anchor="middle")
    _run_all(ds)
    if "title" in r:
        t = r["title"]
        dk.box(slide, t[0], t[1] + t[3] + 0.14 * s, min(t[2], 2.4 * s), 0.07 * s, fill=_hex(k.P["primary_fill"]),
               round=True, r=0.035 * s)
    return r


@register("interface", "image_text", alts=2)
def _ui_image_text(k, slide, f, image):
    """The caller's picture in a device frame chosen by its aspect; kicker, title, body, caption beside it."""
    W, H, s, o = ctx(k)
    path, _alt, _slot = vl._resolve(k, image if not isinstance(image, (list, tuple)) else image[0])
    kind = device_for(path)
    from PIL import Image
    with Image.open(path) as im:
        ar = im.size[0] / float(im.size[1])
    if o == "land":
        box = (0.06 * W, 0.10 * H, (0.48 if alt() == 0 else 0.40) * W, 0.80 * H)
        cx0 = box[0] + box[2] + 0.55 * s
        col = (cx0, 0.14 * H, 0.94 * W - cx0, 0.72 * H)
    else:
        box = (0.07 * W, 0.05 * H, 0.86 * W, (0.48 if alt() == 0 else 0.40) * H)
        cy0 = box[1] + box[3] + 0.4 * s
        col = (0.07 * W, cy0, 0.86 * W, H - 0.5 * s - cy0)
    # the frame takes the picture's aspect inside `box` (screen aspect = picture aspect: nothing is cropped)
    if kind == "phone":
        fh = box[3]
        fw = min(box[2], (fh - 0.0) * ar * 1.0 + 0.1 * s)
        fh = min(fh, (fw - 0.1 * s) / ar + 0.3 * s)
        fx = box[0] + (box[2] - fw) / 2.0
        scr = na.ui_device(slide, fx, box[1], fw, fh, "phone", frame=k.P["ink"], screen=k.P["panel"])
    else:
        fw = box[2]
        bar = min(0.36, 0.09 * box[3])
        fh = min(box[3], fw / ar + bar + 0.06)
        fw = min(fw, (fh - bar - 0.06) * ar + 0.12)
        scr = na.ui_device(slide, box[0], box[1] + (box[3] - fh) / 2.0, fw, fh, "browser", frame=k.P["panel"],
                           screen=k.P["line"])
    vl._place_image(k, slide, image, scr, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    r, ds = stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                  [(fields(f, ("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.2 * s),
                   (fields(f, ("body",)), 0.2 * s), (fields(f, ("caption",)), 0.0)], anchor="middle")
    _run_all(ds)
    return r


@register("interface", "points", alts=2)
def _ui_points(k, slide, f, image):
    """A settings list: title above a window; one row per point — numbered badge, head + line, the caller's tag chip."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    raw = f.get("tags")
    if raw is not None and (not isinstance(raw, (list, tuple)) or len(raw) != n):
        raise ValueError("interface.points(): tags= takes one label per point ({} points), got {!r}".format(n, raw))
    tags = [ui_state(t, "points", "tags") for t in raw] if raw is not None else None
    x0, w0 = 0.06 * W, 0.88 * W
    r, ds = stack(k, slide, "points", x0, w0, 0.07 * H, (0.24 if alt() == 0 else 0.32) * H,
                  [(fields(f, ("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.0)], anchor="top")
    _run_all(ds)
    top = max((v[1] + v[3] for v in r.values()), default=0.07 * H) + 0.3 * s
    col = _window(k, slide, (x0, top, w0, H - 0.35 * s - top), f, "points")
    badge = 0.62 * s
    tagw = 0.0
    if tags:
        szs = [chip_size(k, t, 0.34 * col[2], "tag") for t, _st in tags]
        if any(z is None for z in szs):
            raise vl.VLTextOverflow("interface.points(): a tag does not fit its chip — tags={!r}".format([t for t, _ in tags]))
        tagw = max(na.chip_width(t, min(szs), k.face("body")) for t, _st in tags) + 0.3 * s
    tx = col[0] + badge + 0.3 * s
    tw = col[0] + col[2] - tx - tagw
    gap = 0.34 * s
    rowh = (col[3] - gap * (n - 1)) / n
    specs = [((tx, col[1] + i * (rowh + gap), tw, rowh), [("item_head", h)] + ([("item_line", l)] if l else []),
              {"anchor": "middle"}) for i, (h, l) in enumerate(pts)]
    planned = plan_together(k, slide, "points", specs)
    rects = dict(r)
    for i, ((rr, d), (h, l)) in enumerate(zip(planned, pts)):
        ry = col[1] + i * (rowh + gap)
        cy = ry + rowh / 2.0
        dk.box(slide, col[0], cy - badge / 2.0, badge, badge, fill=_hex(k.P["soft"]), line=dk._as_rgb(_hex(k.P["line"])),
               round=True, r=0.16 * s)
        r2, d2 = flow(k, slide, "points", (col[0], cy - badge / 2.0, badge, badge), [("item_no", str(i + 1))],
                      anchor="middle", align="c")
        d2()
        d()
        if tags:
            t, st = tags[i]
            sz = min(chip_size(k, tt, 0.34 * col[2], "tag") for tt, _ in tags)
            cw = na.chip_width(t, sz, k.face("body")) + 0.22 * s
            ch = sz / 72.0 * 1.9
            cx = col[0] + col[2] - cw
            na.chip(slide, cx, cy - ch / 2.0, t, size=sz, fill=k.P["soft"], ink=k.P["ink"], face=k.face("body"),
                    ea_face=k.ea_face("body", t))
            dot = dk.disc(slide, cx + 0.10 * s, cy - 0.045 * s, 0.09 * s, fill=_hex(k.P["states"][st]))
            dk.decorative(dot, "the state is named in the chip's words")
        if i < n - 1:
            hl = dk.box(slide, col[0], ry + rowh + gap / 2.0, col[2], 0.012, fill=_hex(k.P["line"]))
            dk.decorative(hl, "a hairline between settings rows")
        rects.update(rr)
    return rects


@register("interface", "quote", alts=2)
def _ui_quote(k, slide, f, image):
    """A chat message: the avatar's initials (from a Latin attribution), the quote in a bubble, the source under it."""
    W, H, s, o = ctx(k)
    a = text_of(f, "attribution")
    ini = initials(a)
    av = 1.0 * s
    x = (0.10 if alt() == 0 else 0.06) * W
    bx = x + (av + 0.35 * s if ini else 0.0)
    bw = (0.90 * W if o == "land" else 0.93 * W) - bx
    ah = 0.7 * s if a else 0.0
    bub = (bx, 0.16 * H, bw, H - 0.16 * H - 0.45 * s - ah - 0.3 * s)
    pad = 0.5 * s
    r, d = flow(k, slide, "quote", (bub[0] + pad, bub[1] + pad, bub[2] - 2 * pad, bub[3] - 2 * pad), fields(f, ("quote",)),
                anchor="middle")
    qt = min(v[1] for v in r.values())
    qb = max(v[1] + v[3] for v in r.values())
    bub = (bub[0], qt - pad, bub[2], qb - qt + 2 * pad)
    na.ui_bubble(slide, *bub, fill=k.P["panel"], line=k.P["line"], r=0.32 * s)
    if ini:
        dk.disc(slide, x, bub[1], av, fill=_hex(k.P["states"]["primary"]))
        r0, d0 = flow(k, slide, "quote", (x, bub[1], av, av), [("initials", ini)], anchor="middle", align="c", ink="FFFFFF")
        d0()
    d()
    rects = dict(r)
    if a:
        r2, d2 = flow(k, slide, "quote", (bub[0] + pad, bub[1] + bub[3] + 0.25 * s, bub[2] - 2 * pad, ah),
                      [("attribution", a)], anchor="top")
        d2()
        rects.update(r2)
    return rects


@register("interface", "data", alts=2)
def _ui_data(k, slide, f, image):
    """A dashboard card: label, the number, a progress bar when total= is given (tally's rules), the note as a
    notice under the card."""
    W, H, s, o = ctx(k)
    num, total = text_of(f, "number"), text_of(f, "total")
    frac = share_of("interface", num, total)
    note = text_of(f, "note")
    nh = 1.2 * s if note else 0.0
    if o == "land":
        card = (0.06 * W, 0.10 * H, (0.62 if alt() == 0 else 0.88) * W, H - 0.10 * H - 0.4 * s - nh - 0.3 * s)
    else:
        card = (0.07 * W, 0.08 * H, 0.86 * W, (0.55 if alt() == 0 else 0.62) * H)
    col = _window(k, slide, card, f, "data", bar=False)
    barh = 0.45 * s if frac is not None else 0.0
    r, ds = stack(k, slide, "data", col[0], col[2], col[1], col[1] + col[3] - barh,
                  [(fields(f, ("label",)), 0.15 * s), ([("number", num)] if num else [], 0.0)], anchor="middle")
    _run_all(ds)
    if frac is not None:
        foot = max(v[1] + v[3] for v in r.values())
        na.share_bar(slide, col[0], foot + 0.25 * s, col[2], frac, track=k.P["line"], fill=k.P["states"]["primary"],
                     h=0.16 * s)
    rects = dict(r)
    if note:
        ny = card[1] + card[3] + 0.3 * s
        if o != "land":
            nh = H - 0.4 * s - ny
        ib = na.ui_window(slide, card[0], ny, card[2], nh, fill=k.P["panel"], line=k.P["line"], drop=k.P["drop"], r=0.22 * s)
        dd = 0.42 * s
        dk.disc(slide, ib[0] + 0.35 * s, ib[1] + (ib[3] - dd) / 2.0, dd, fill=_hex(k.P["states"]["primary"]))
        r1, d1 = flow(k, slide, "data", (ib[0] + 0.35 * s, ib[1] + (ib[3] - dd) / 2.0, dd, dd), [("item_no", "i")],
                      anchor="middle", align="c", ink="FFFFFF")
        d1()
        r2, d2 = flow(k, slide, "data", (ib[0] + 1.0 * s, ib[1] + 0.15 * s, ib[2] - 1.3 * s, ib[3] - 0.3 * s),
                      [("note", note)], anchor="middle")
        d2()
        rects.update(r2)
    return rects


@register("interface", "closing", alts=2)
def _ui_closing(k, slide, f, image):
    """A dialog: title and line in a centred window, the caller's actions as its buttons."""
    W, H, s, o = ctx(k)
    acts = _actions(f, "closing")
    ww = (0.62 if alt() == 0 else 0.80) * W if o == "land" else 0.86 * W
    wh = (0.62 if o == "land" else 0.50) * H
    win = ((W - ww) / 2.0, (H - wh) / 2.0, ww, wh)
    col = _window(k, slide, win, f, "closing", bar=False)
    bh = (vl.TYPE["interface"]["action"][0] * s / 72.0 * 2.6 + 0.4 * s) if acts else 0.0
    r, ds = stack(k, slide, "closing", col[0], col[2], col[1], col[1] + col[3] - bh,
                  [(fields(f, ("title",)), 0.25 * s), (fields(f, ("line",)), 0.0)], anchor="middle")
    _run_all(ds)
    if acts:
        foot = max(v[1] + v[3] for v in r.values())
        _buttons(k, slide, col[0], foot + 0.4 * s, acts, col[2])
    return r
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p5.py | tail -5 && python3 tests/test_native_languages_p4.py | tail -2`
Expected: P5 `… passed, 0 failed`; P4 unchanged (tally's share rules still hold through `share_of`).

- [ ] **Step 5: Render and look.** Build the 7 pages × 2 grounds × 3 canvases deck from `build_matrix("interface", g, c, "en")` and `"zh"`, render with `python3 scripts/render_deck.py <deck> <dir>`, read every PNG in one message and fix what you see (crumb, buttons, pointer, toggles, bubble, device frame). Record the verdicts in the ledger line.

- [ ] **Step 6: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native.py skills/slide-maker/scripts/vl_native2.py skills/slide-maker/scripts/vl_native3.py skills/slide-maker/tests/test_native_languages_p5.py
git commit -m "interface (产品界面): a native visual language where every page is an app screen"
```

---

### Task 3: `wayfinding` 导视线路

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py` — `LANGS`, `VARIANTS`, `TYPE`, `NATIVE`, `NATIVE_EXTRAS`, `EXTRA_PAGES`, `_ground_wayfinding`, `_card_wayfinding`, `_DISPLAY_NAMES`, `_RATIONALE`, `_SAMPLE_COPY_NATIVE`
- Modify: `skills/slide-maker/scripts/vl_native3.py` (append the wayfinding section)
- Test: `skills/slide-maker/tests/test_native_languages_p5.py` (insert above the final prints)

**Interfaces:**
- Consumes: Task 1's `route`, `station`, `interchange`, `roundel`, `sign_panel`; Task 2's module header.
- Produces: `vl_native3.line_colour(k, n) -> hex`, `vl_native3.ink_on(k, fill) -> hex`, `vl_native3.LABELS3`, `vl_native3.ordinary_sign(slide)`, seven `@register("wayfinding", page, alts=2)` compositions.

- [ ] **Step 1: Write the failing tests.** Insert above the final prints:

```python
# ── wayfinding 导视线路 ──
EXTRAS["wayfinding"] = lambda lang, n: {"cover": {"line": "1"}, "points": {"ordered": True, "interchange": [1]},
                                        "data": {"board": [("Route B", "93.1%"), ("Route C", "91.8%")]}}
check("wayfinding" in vl.NATIVE and set(vl.VARIANTS["wayfinding"]) == {"light", "night"}, "wayfinding: two grounds")
assert_palettes("wayfinding")
for g, V in vl.VARIANTS["wayfinding"].items():
    p = V["palette"]
    check(cr(p["sign_ink"], p["sign"]) >= 4.5 and cr(p["sign_mute"], p["sign"]) >= 4.5, "wayfinding/{}: words on a sign".format(g))
    check(cr(p["led"], p["board"]) >= 4.5 and cr(p["board_mute"], p["board"]) >= 4.5, "wayfinding/{}: the board's LED".format(g))
    check(cr(p["exit_ink"], p["exit"]) >= 4.5, "wayfinding/{}: words on the way-out sign".format(g))
assert_matrix("wayfinding")
import vl_native3 as v3
# Review Focus 3: the digit on a yellow roundel is dark
prs, k = use("wayfinding")
check(v3.ink_on(k, "F2B705") == k.P["ink"] and v3.ink_on(k, "0071BC") == "FFFFFF", "wayfinding: roundel ink picked by contrast")
check([v3.line_colour(k, n) for n in (1, 2, 6)] == [k.P["lines"][0], k.P["lines"][1], k.P["lines"][0]],
      "wayfinding: a section's line colour follows its number")
# Review Focus 2: unordered points → a directory sign, no route; interchange= without ordered= refused
for W, H in CANVASES.values():
    prs, k = use("wayfinding", W, H)
    s = k.new_slide()
    k.points(s, title="Four pillars", items=["Speed", "Care", "Craft", "Reach"])
    conns = [sh for sh in s.shapes if sh.shape_type == 9 or sh._element.tag.endswith("cxnSp")]
    check(not conns, "wayfinding {}x{}: unordered points draw no route".format(W, H))
    rnd = [sh for sh in texts(s) if txt_of(sh) in ("1", "2", "3", "4")]
    check(len(rnd) == 4, "wayfinding {}x{}: four directory rows with numbered roundels".format(W, H))
    s2 = k.new_slide()
    k.points(s2, title="Four stops", items=["Sign up", "First project", "Invite", "Upgrade"], ordered=True, interchange=[2])
    conns = [sh for sh in s2.shapes if sh._element.tag.endswith("cxnSp")]
    check(conns, "wayfinding {}x{}: ordered points draw the route".format(W, H))
    hit = [c for c in conns for sh in texts(s2) if v2.meet(rect_of(c), rect_of(sh))]
    check(not hit, "wayfinding {}x{}: the route crosses no words".format(W, H))
try:
    prs, k = use("wayfinding")
    k.points(k.new_slide(), title="x", items=["a", "b"], interchange=[0])
    check(False, "wayfinding: interchange= without ordered= is refused")
except ValueError as e:
    check("interchange=" in str(e) and "ordered" in str(e), "wayfinding: interchange= without ordered= is refused by name")
for bad_ix in ([5], ["a"], 1):
    try:
        prs, k = use("wayfinding")
        k.points(k.new_slide(), title="x", items=["a", "b"], ordered=True, interchange=bad_ix)
        check(False, "wayfinding: interchange={!r} is refused".format(bad_ix))
    except ValueError as e:
        check("interchange=" in str(e), "wayfinding: interchange={!r} refused by name".format(bad_ix))
# the board: the page's own row first, then the caller's rows; refused beyond four extra rows
prs, k = use("wayfinding")
s = k.new_slide()
k.data(s, number="96.4%", label="Harbour line on time", board=[("North loop", "93.1%")])
tt = [txt_of(sh) for sh in texts(s)]
check("96.4%" in tt and "Harbour line on time" in tt and "North loop" in tt and "93.1%" in tt, "wayfinding: board rows drawn")
try:
    k.data(k.new_slide(), number="1", label="x", board=[("a", "1")] * 5)
    check(False, "wayfinding: board= beyond 4 rows is refused")
except ValueError as e:
    check("board=" in str(e), "wayfinding: board= beyond 4 rows refused by name")
# the way-out label follows the deck's language
for lang, want in (("en", "Way out"), ("zh", "出口"), ("ja", "出口"), ("ko", "나가는 곳")):
    prs, k = use("wayfinding")
    s = k.new_slide(); k.closing(s, title=COPY[lang]["title"], line=COPY[lang]["line"])
    check(any(txt_of(sh).upper() == want.upper() for sh in texts(s)), "wayfinding/{}: way-out label {!r}".format(lang, want))
# no invented words on the cover; line= draws the roundel
prs, k = use("wayfinding")
s = k.new_slide(); k.cover(s, title="Our plan", subtitle="Strategy 2027")
check(sorted(txt_of(sh) for sh in texts(s)) == sorted(["Our plan", "Strategy 2027"]), "wayfinding: cover invents nothing")
import register_surface as rs
prs, k = use("wayfinding")
s = k.new_slide()
rect = rs.ground(s, k.name, role="content", index=2)
check(rect[1] > 0.4 and rect[2] > 5, "wayfinding: an ordinary page carries the sign strip above its content rect")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p5.py | tail -3`
Expected: `KeyError: 'wayfinding'`.

- [ ] **Step 3: Implement.**

(a) `visual_languages.py` tables.
- `LANGS`:

  ```python
      "wayfinding": {
          "palette": {"ground": "F6F5F1", "ink": "16191E", "mute": "5A6070", "panel": "ECEAE3",
                      "accents": ["D7262E", "0071BC", "00954C", "F2B705", "8E4FA1"], "text_accents": ["1B2A41"],
                      "lines": ["D7262E", "0071BC", "00954C", "F2B705", "8E4FA1"],
                      "sign": "1B2A41", "sign_ink": "FFFFFF", "sign_mute": "B9C3D4", "edge": "F2B705",
                      "board": "0B0D10", "led": "FFB020", "board_mute": "9AA0AA",
                      "exit": "007A3D", "exit_ink": "FFFFFF", "casing": "16191E"},
          "fonts": {"both": {"display": "Arial", "body": "Arial", "numeral": "Arial", "board": "Courier New"},
                    "mac": {"display": "Helvetica Neue", "body": "Helvetica Neue", "numeral": "Helvetica Neue",
                            "board": "Menlo"}},
          "ea": {"display": "sans", "body": "sans"}, "ea_heavy": True, "grain": 0, "frames": ["rect"],
          "forbids": ("confetti",), "cover": "split-vertical", "skeleton": "band"},
  ```

- `VARIANTS`:

  ```python
      "wayfinding": {
          "light": {"label": "enamel", "label_zh": "珐琅白版", "grain": 0, "palette": LANGS["wayfinding"]["palette"]},
          "night": {"label": "navy", "label_zh": "藏青夜间版", "grain": 0,
                    "palette": {"ground": "1B2A41", "ink": "F2F4F8", "mute": "B9C3D4", "panel": "22344F",
                                "accents": ["E8454C", "3D9BE0", "1DB66A", "F2B705", "B07CC6"], "text_accents": ["F2B705"],
                                "lines": ["E8454C", "3D9BE0", "1DB66A", "F2B705", "B07CC6"],
                                "sign": "0F1A2C", "sign_ink": "FFFFFF", "sign_mute": "B9C3D4", "edge": "F2B705",
                                "board": "0B0D10", "led": "FFB020", "board_mute": "9AA0AA",
                                "exit": "007A3D", "exit_ink": "FFFFFF", "casing": "0F1A2C"}}},
  ```

- `TYPE`:

  ```python
      "wayfinding": {"kicker": (14, "body", True, "mute", False, 10), "title": (52, "display", True, "ink", False, 26),
                     "subtitle": (20, "body", True, "ink", False, 12), "body": (17, "body", False, "ink", False, 11),
                     "quote": (34, "display", True, "ink", False, 18), "attribution": (14, "body", True, "mute", False, 10),
                     "number": (96, "board", True, "ink", False, 40), "label": (24, "board", False, "ink", False, 13),
                     "note": (15, "body", False, "mute", False, 10), "caption": (12, "body", False, "mute", False, 9),
                     "line": (20, "body", False, "ink", False, 12), "item_head": (22, "body", True, "ink", False, 13),
                     "item_line": (15, "body", False, "mute", False, 10), "item_no": (18, "display", True, "ink", False, 12),
                     "roundel": (18, "display", True, "ink", False, 11), "exit": (14, "body", True, "ink", False, 10),
                     "row": (20, "board", False, "ink", False, 11), "mark": (60, "display", True, "accent", False, 30)},
  ```

  (`number`/`label`/`row` use the `board` role. `Kit.face("board")` resolves it; `ea_face` maps any non-display role to the body EA face.)
- `NATIVE` gains `"wayfinding"`.
- `NATIVE_EXTRAS["wayfinding"] = ("line", "ordered", "interchange", "board")`; `EXTRA_PAGES.update({"interchange": ("points",), "board": ("data",)})` — `ordered` already maps to `points`; `line` is on every page.
- Ground and card:

  ```python
  def _ground_wayfinding(slide, role, index):
      """An ordinary page carries the sign strip; the content rect starts below it."""
      import vl_native3
      return vl_native3.ordinary_sign(slide)
  ```

  and `_card_wayfinding = _card_for("wayfinding")`.
- `_DISPLAY_NAMES["wayfinding"] = "Wayfinding"`; `_RATIONALE["wayfinding"] = "drawn, no pictures: metro lines converging on an interchange, station signs, a strip map for ordered steps, a departure board"`.
- `_SAMPLE_COPY_NATIVE["wayfinding"]`:

  ```python
      "wayfinding": [("cover", dict(kicker="Next stop", title="Our plan to reach one million riders",
                                    subtitle="Strategy 2027", line="1")),
                     ("points", dict(title="Four stops between sign-up and a paying customer", ordered=True,
                                     items=[("Sign up", "Under two minutes, no card"), ("First project", "A template does the setup"),
                                            ("Invite a teammate", "Work stops being solo"), ("Upgrade", "Billing when the team is in")],
                                     interchange=[2])),
                     ("quote", dict(quote="If a stranger can find the platform, anyone can.", attribution="Style sample")),
                     ("data", dict(number="96.4%", label="Harbour line on time", note="Style sample — your numbers go here.",
                                   board=[("North loop", "93.1%"), ("Riverside", "91.8%")]))],
  ```

(b) Append to `vl_native3.py`:

```python
# ═══════════════════════════════════ wayfinding 导视线路 ═══════════════════════════════════
# 나가는 곳 is the Seoul Metro exit sign wording; 出口 is used on Chinese and Japanese station signs (confirmed against
# operator signage photos during implementation — replace if the reference says otherwise).
LABELS3 = {"way_out": {"en": "Way out", "zh": "出口", "ja": "出口", "ko": "나가는 곳"}}


def ink_on(k, fill):
    """The page's ink or white on a coloured fill — whichever reads better (a yellow roundel takes the dark ink)."""
    return "FFFFFF" if vl._contrast("FFFFFF", fill) >= vl._contrast(k.P["ink"], fill) else k.P["ink"]


def line_colour(k, n):
    """A section's line colour from its number: 1 red, 2 blue, 3 green, 4 yellow, 5 purple, repeating."""
    try:
        i = max(1, int(str(n).strip())) - 1
    except ValueError:
        i = 0
    return k.P["lines"][i % len(k.P["lines"])]


def _line_code(k, f, page):
    """line=: the caller's 1-3 character line code, optionally (code, colour name). Remembered for the deck."""
    v = f.get("line") if f.get("line") is not None else k.memo.get("line")
    if f.get("line") is not None:
        k.memo = dict(k.memo, line=f.get("line"))
    if v is None:
        return None
    names = {"red": 0, "blue": 1, "green": 2, "yellow": 3, "purple": 4}
    code, colour = (v, None) if isinstance(v, str) else (tuple(v) + (None,))[:2] if isinstance(v, (list, tuple)) else (None, None)
    if not isinstance(code, str) or not 1 <= len(code.strip()) <= 3 or (colour is not None and colour not in names):
        raise ValueError("wayfinding.{}(): line= takes a 1-3 character line code, or (code, colour) with colour in {} — "
                         "got {!r}".format(page, sorted(names), v))
    return code.strip(), k.P["lines"][names[colour]] if colour else k.P["lines"][0]


def _roundel(k, slide, cx, cy, d, text, fill):
    W, H, s, o = ctx(k)
    sz = min(vl.TYPE["wayfinding"]["roundel"][0] * s * d / (0.5 * s), d * 72 * 0.5)
    return na.roundel(slide, cx, cy, d, text, fill=fill, ink=ink_on(k, fill), size=sz, face=k.face("display"),
                      ea_face=k.ea_face("display", text))


def ordinary_sign(slide):
    """rs.ground for wayfinding: a navy sign strip with the yellow edge across the top; the content rect below it."""
    import vl_native2 as v2
    k = v2.kit_for("wayfinding", slide)
    W, H, s, o = ctx(k)
    h = 0.34 * s
    dk.box(slide, 0, 0, W, h, fill=_hex(k.P["sign"]))
    e = dk.box(slide, 0, h, W, 0.05 * s, fill=_hex(k.P["edge"]))
    dk.decorative(e, "the sign strip's edge")
    return (0.07 * W, h + 0.35 * s, 0.86 * W, H - h - 0.8 * s)


@register("wayfinding", "cover", alts=2)
def _wf_cover(k, slide, f, image):
    """Two or three lines converge on an interchange; kicker + title as the destination; the subtitle on a sign."""
    W, H, s, o = ctx(k)
    lc = _line_code(k, f, "cover")
    lw = 0.16 * s
    if o == "land":
        ix, iy = (0.50 if alt() == 0 else 0.44) * W, 0.52 * H
        col = (ix + 0.75 * s, 0.18 * H, 0.94 * W - ix - 0.75 * s, 0.70 * H)
    else:
        ix, iy = 0.55 * W, 0.30 * H
        col = (0.07 * W, iy + 0.9 * s, 0.86 * W, H - iy - 0.9 * s - 0.5 * s)
    L = k.P["lines"]
    ya = iy - 0.23 * H if o == "land" else iy - 0.18 * H
    na.route(slide, [(0, ya), (ix - (iy - ya), ya), (ix, iy)], L[0], w=lw)
    na.route(slide, [(0, iy), (ix, iy)], L[1], w=lw)
    xc = ix - 0.6 * (H - iy) if o == "land" else 0.18 * W
    na.route(slide, [(xc, H), (xc, iy + (ix - xc)), (ix, iy)], L[2], w=lw)
    for x_, y_ in ((0.12 * W, ya), (0.27 * W, ya), (0.12 * W, iy)):
        if x_ < ix - (iy - ya) - 0.3 * s:
            dk.decorative(na.station(slide, x_, y_, 0.26 * s, ring=k.P["casing"]), "a station on the network")
    na.interchange(slide, ix, iy, 1.0 * s, 0.7 * s, ring=k.P["casing"])
    sub = text_of(f, "subtitle")
    sh = 0.0
    if sub:
        sh = 0.95 * s
    r, ds = stack(k, slide, "cover", col[0], col[2], col[1], col[1] + col[3] - (sh + 0.4 * s if sub else 0.0),
                  [(fields(f, ("kicker",), capsed=("kicker",)), 0.12 * s), (fields(f, ("title",)), 0.0)], anchor="middle")
    _run_all(ds)
    rects = dict(r)
    if sub:
        foot = max((v[1] + v[3] for v in r.values()), default=col[1]) + 0.4 * s
        inner = na.sign_panel(slide, col[0], foot, col[2], sh, fill=k.P["sign"])
        tx = inner[0] + 0.2 * s
        if lc:
            d = 0.52 * s
            _roundel(k, slide, inner[0] + 0.15 * s + d / 2.0, inner[1] + inner[3] / 2.0, d, lc[0], lc[1])
            tx = inner[0] + 0.3 * s + d
        r2, d2 = flow(k, slide, "cover", (tx, inner[1], inner[0] + inner[2] - tx - 0.15 * s, inner[3]),
                      [("subtitle", sub + "  →")], anchor="middle", ink=k.P["sign_ink"])
        d2()
        rects.update(r2)
    return rects


@register("wayfinding", "section", alts=2)
def _wf_section(k, slide, f, image):
    """A station-name sign across the page: the roundel (section number, or the line code), kicker, title, arrow."""
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    lc = _line_code(k, f, "section")
    band = (0, (0.28 if alt() == 0 else 0.20) * H, W, (0.44 if alt() == 0 else 0.60) * H)
    dk.box(slide, *band, fill=_hex(k.P["sign"]))
    e = dk.box(slide, 0, band[1], W, 0.08 * s, fill=_hex(k.P["edge"]))
    dk.decorative(e, "the sign's yellow edge")
    d = min(1.6 * s, band[3] * 0.62)
    x = 0.07 * W
    label = lc[0] if lc else num
    if label:
        fill = lc[1] if lc else line_colour(k, num)
        _roundel(k, slide, x + d / 2.0, band[1] + band[3] / 2.0, d, label, fill)
        x += d + 0.5 * s
    r, ds = stack(k, slide, "section", x, 0.93 * W - x - 1.0 * s, band[1] + 0.25 * s, band[1] + band[3] - 0.2 * s,
                  [(fields(f, ("kicker",), capsed=("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.0)], anchor="middle",
                  ink=k.P["sign_ink"], mute=k.P["sign_mute"])
    _run_all(ds)
    ar = dk.arrow(slide, 0.93 * W - 0.85 * s, band[1] + band[3] / 2.0 - 0.3 * s, 0.85 * s, 0.6 * s,
                  color=dk._as_rgb(_hex(k.P["sign_ink"])))
    dk.decorative(ar, "the sign's direction arrow")
    return r


@register("wayfinding", "image_text", alts=2)
def _wf_image_text(k, slide, f, image):
    """The picture as a station poster in a sign frame; kicker, title, body, caption beside it."""
    W, H, s, o = ctx(k)
    if o == "land":
        fr = (0.06 * W, 0.10 * H, (0.48 if alt() == 0 else 0.40) * W, 0.80 * H)
        cx0 = fr[0] + fr[2] + 0.55 * s
        col = (cx0, 0.14 * H, 0.94 * W - cx0, 0.72 * H)
    else:
        fr = (0.07 * W, 0.05 * H, 0.86 * W, (0.46 if alt() == 0 else 0.38) * H)
        cy0 = fr[1] + fr[3] + 0.4 * s
        col = (0.07 * W, cy0, 0.86 * W, H - 0.5 * s - cy0)
    inner = na.sign_panel(slide, *fr, fill=k.P["sign"])
    pad = 0.12 * s
    vl._place_image(k, slide, image, (inner[0] + pad, inner[1] + pad, inner[2] - 2 * pad, inner[3] - 2 * pad),
                    vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    r, ds = stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                  [(fields(f, ("kicker",), capsed=("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.2 * s),
                   (fields(f, ("body",)), 0.2 * s), (fields(f, ("caption",)), 0.0)], anchor="middle")
    _run_all(ds)
    return r


def _interchange_ix(f, n):
    v = f.get("interchange")
    if v is None:
        return set()
    if not f.get("ordered"):
        raise ValueError("wayfinding.points(): interchange= marks stops on a route, so it needs ordered=True — "
                         "unordered points are a directory sign with no route")
    if not isinstance(v, (list, tuple)) or not all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < n for i in v):
        raise ValueError("wayfinding.points(): interchange= takes point indexes 0..{} — got {!r}".format(n - 1, v))
    return set(v)


@register("wayfinding", "points", alts=2)
def _wf_points(k, slide, f, image):
    """ordered=True: a strip map (stations on one line, names alternating above and below; a vertical route on a
    portrait page). Otherwise a directory sign: one row per point with its numbered roundel — no route, no order."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    ordered = f.get("ordered")
    if ordered not in (None, True, False):
        raise ValueError("wayfinding.points(): ordered= takes True or False, got {!r}".format(ordered))
    ixs = _interchange_ix(f, n)
    x0, w0 = 0.07 * W, 0.86 * W
    colour = (_line_code(k, f, "points") or (None, k.P["lines"][1]))[1]
    if not ordered:
        r, ds = stack(k, slide, "points", x0, w0, 0.07 * H, (0.22 if alt() == 0 else 0.30) * H,
                      [(fields(f, ("kicker",), capsed=("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.0)], anchor="top")
        _run_all(ds)
        top = max((v[1] + v[3] for v in r.values()), default=0.07 * H) + 0.35 * s
        inner = na.sign_panel(slide, x0, top, w0, H - 0.4 * s - top, fill=k.P["sign"])
        d = 0.56 * s
        tx = inner[0] + 0.35 * s + d + 0.35 * s
        gap = 0.2 * s
        rowh = (inner[3] - 0.4 * s - gap * (n - 1)) / n
        specs = [((tx, inner[1] + 0.2 * s + i * (rowh + gap), inner[0] + inner[2] - tx - 1.0 * s, rowh),
                  [("item_head", h)] + ([("item_line", l)] if l else []), {"anchor": "middle", "ink": k.P["sign_ink"],
                                                                            "mute": k.P["sign_mute"]})
                 for i, (h, l) in enumerate(pts)]
        planned = plan_together(k, slide, "points", specs)
        rects = dict(r)
        for i, (rr, dd) in enumerate(planned):
            cy = inner[1] + 0.2 * s + i * (rowh + gap) + rowh / 2.0
            _roundel(k, slide, inner[0] + 0.35 * s + d / 2.0, cy, d, str(i + 1), k.P["lines"][i % len(k.P["lines"])])
            dd()
            ar = dk.arrow(slide, inner[0] + inner[2] - 0.75 * s, cy - 0.2 * s, 0.5 * s, 0.4 * s,
                          color=dk._as_rgb(_hex(k.P["sign_ink"])))
            dk.decorative(ar, "a direction arrow on the directory sign")
            if i < n - 1:
                hl = dk.box(slide, tx, cy + rowh / 2.0 + gap / 2.0, inner[0] + inner[2] - tx - 0.3 * s, 0.012,
                            fill=_hex(k.P["sign_mute"]))
                dk.decorative(hl, "a rule between directory rows")
            rects.update(rr)
        return rects
    # the strip map: the title on a sign band, the route under it
    r, ds = stack(k, slide, "points", x0 + 0.3 * s, w0 - 0.6 * s, 0.07 * H + 0.2 * s, 0.07 * H + 1.6 * s,
                  [(fields(f, ("title",)), 0.0)], anchor="middle", ink=k.P["sign_ink"])
    tb = max(v[1] + v[3] for v in r.values()) + 0.2 * s
    na.sign_panel(slide, x0, 0.07 * H, w0, tb - 0.07 * H, fill=k.P["sign"])
    _run_all(ds)
    rects = dict(r)
    lw = 0.2 * s
    sd = 0.42 * s
    if o == "land":
        y = tb + (H - tb) * 0.50
        xs = [x0 + 0.5 * s + i * (w0 - 1.0 * s) / (n - 1) for i in range(n)]
        cw = min(2.8 * s, (w0 - 0.5 * s) / max(2, n) * 1.6)
        specs = []
        for i, (h, l) in enumerate(pts):
            up = i % 2 == 0
            ry = (tb + 0.3 * s) if up else (y + sd / 2.0 + 0.35 * s)
            rh = (y - sd / 2.0 - 0.35 * s - ry) if up else (H - 0.4 * s - ry)
            cx = min(max(xs[i] - 0.2 * s, x0), x0 + w0 - cw)
            specs.append(((cx, ry, cw, rh), [("item_head", h)] + ([("item_line", l)] if l else []),
                          {"anchor": "bottom" if up else "top"}))
        planned = plan_together(k, slide, "points", specs)
        na.route(slide, [(0.0, y), (W, y)], colour, w=lw)
        for i, x in enumerate(xs):
            if i in ixs:
                na.interchange(slide, x, y, 0.8 * s, 0.56 * s, ring=k.P["casing"])
            else:
                na.station(slide, x, y, sd, ring=k.P["casing"])
        for rr, dd in planned:
            dd()
            rects.update(rr)
        return rects
    x = x0 + 0.3 * s
    ys = [tb + 0.6 * s + i * (H - 0.8 * s - tb - 0.6 * s) / (n - 1) for i in range(n)]
    specs = [((x + 0.6 * s, yy - 0.5 * s, w0 - 0.9 * s, 1.0 * s), [("item_head", h)] + ([("item_line", l)] if l else []),
              {"anchor": "middle"}) for yy, (h, l) in zip(ys, pts)]
    planned = plan_together(k, slide, "points", specs)
    na.route(slide, [(x, tb + 0.2 * s), (x, H)], colour, w=lw)
    for i, yy in enumerate(ys):
        if i in ixs:
            na.interchange(slide, x, yy, 0.56 * s, 0.8 * s, ring=k.P["casing"])
        else:
            na.station(slide, x, yy, sd, ring=k.P["casing"])
    for rr, dd in planned:
        dd()
        rects.update(rr)
    return rects


@register("wayfinding", "quote", alts=2)
def _wf_quote(k, slide, f, image):
    """The quote on an enamel sign; the source under it."""
    W, H, s, o = ctx(k)
    a = text_of(f, "attribution")
    x = (0.08 if alt() == 0 else 0.05) * W
    w = W - 2 * x
    ah = 0.7 * s if a else 0.0
    pad = 0.55 * s
    r, d = flow(k, slide, "quote", (x + pad, 0.14 * H + pad, w - 2 * pad, H - 0.14 * H - 0.45 * s - ah - 2 * pad),
                fields(f, ("quote",)), anchor="middle", ink=k.P["sign_ink"])
    qt = min(v[1] for v in r.values())
    qb = max(v[1] + v[3] for v in r.values())
    na.sign_panel(slide, x, qt - pad, w, qb - qt + 2 * pad, fill=k.P["sign"])
    d()
    rects = dict(r)
    if a:
        r2, d2 = flow(k, slide, "quote", (x, qb + pad + 0.25 * s, w, ah), [("attribution", "— " + a)], anchor="top")
        d2()
        rects.update(r2)
    return rects


def _board_rows(f):
    v = f.get("board")
    if v is None:
        return []
    ok_ = isinstance(v, (list, tuple)) and 1 <= len(v) <= 4 and all(
        isinstance(t, (list, tuple)) and len(t) == 2 and all(isinstance(x, str) and x.strip() for x in t) for t in v)
    if not ok_:
        raise ValueError("wayfinding.data(): board= takes 1 to 4 (label, value) rows under the page's own row, got {!r}"
                         .format(v))
    return [(a.strip(), b.strip()) for a, b in v]


@register("wayfinding", "data", alts=2)
def _wf_data(k, slide, f, image):
    """A departure board: the page's label and number as the first, largest row; the caller's board= rows under it;
    the note beneath the board."""
    W, H, s, o = ctx(k)
    rows = _board_rows(f)
    num, lab, note = text_of(f, "number"), text_of(f, "label"), text_of(f, "note")
    x0, w0 = 0.06 * W, 0.88 * W
    nh = 0.9 * s if note else 0.0
    board = (x0, 0.10 * H, w0, H - 0.10 * H - 0.4 * s - nh)
    dk.box(slide, *board, fill=_hex(k.P["board"]), round=True, r=0.14 * s)
    pad = 0.45 * s
    rd = 0.5 * s
    inner = (board[0] + pad, board[1] + pad, board[2] - 2 * pad, board[3] - 2 * pad)
    head_h = inner[3] * (0.55 if rows else 1.0)
    rest_h = inner[3] - head_h
    rects = {}
    _roundel(k, slide, inner[0] + rd / 2.0, inner[1] + head_h / 2.0, rd, "1", k.P["lines"][0])
    lx = inner[0] + rd + 0.4 * s
    nw = inner[2] * 0.42
    r1, d1 = flow(k, slide, "data", (inner[0] + inner[2] - nw, inner[1], nw, head_h), [("number", num)] if num else [],
                  anchor="middle", align="r", ink=k.P["led"])
    r2, d2 = flow(k, slide, "data", (lx, inner[1], inner[2] - nw - (lx - inner[0]) - 0.3 * s, head_h),
                  [("label", lab)] if lab else [], anchor="middle", ink=k.P["led"])
    d1(); d2()
    rects.update(r1); rects.update(r2)
    if rows:
        rh = rest_h / len(rows)
        for i, (a, b) in enumerate(rows):
            ry = inner[1] + head_h + i * rh
            hl = dk.box(slide, inner[0], ry, inner[2], 0.01, fill=_hex(k.P["board_mute"]))
            dk.decorative(hl, "a rule between board rows")
            _roundel(k, slide, inner[0] + rd * 0.8 / 2.0, ry + rh / 2.0, rd * 0.8, str(i + 2),
                     k.P["lines"][(i + 1) % len(k.P["lines"])])
            ra, da = flow(k, slide, "data", (lx, ry, inner[2] * 0.55, rh), [("row", a)], anchor="middle", ink=k.P["led"])
            rb, db = flow(k, slide, "data", (inner[0] + inner[2] - nw, ry, nw, rh), [("row", b)], anchor="middle",
                          align="r", ink=k.P["led"])
            da(); db()
            rects.update(ra); rects.update(rb)
    if note:
        r3, d3 = flow(k, slide, "data", (x0, board[1] + board[3] + 0.25 * s, w0, nh - 0.1 * s), [("note", note)],
                      anchor="top")
        d3()
        rects.update(r3)
    return rects


@register("wayfinding", "closing", alts=2)
def _wf_closing(k, slide, f, image):
    """The way-out sign: the localised label, the title and line in white on green; the route ends at a terminus."""
    W, H, s, o = ctx(k)
    lab = LABELS3["way_out"][lang_of(text_of(f, "title"), text_of(f, "line"), k=k, f=f)]
    x, w = 0.07 * W, (0.66 if alt() == 0 else 0.86) * W if o == "land" else 0.86 * W
    top = 0.14 * H
    ry = (0.80 if o == "land" else 0.86) * H
    pad = 0.45 * s
    r, ds = stack(k, slide, "closing", x + pad, w - 2 * pad, top + pad, ry - 0.9 * s - pad,
                  [([("exit", caps(lab))], 0.15 * s), (fields(f, ("title",)), 0.2 * s), (fields(f, ("line",)), 0.0)],
                  anchor="top", ink=k.P["exit_ink"], mute=k.P["exit_ink"])
    foot = max(v[1] + v[3] for v in r.values()) + pad
    na.sign_panel(slide, x, top, w, foot - top, fill=k.P["exit"])
    _run_all(ds)
    tx = min(0.62 * W, x + w * 0.85)
    na.route(slide, [(0.0, ry), (tx, ry)], k.P["lines"][0], w=0.16 * s)
    for i in range(3):
        sx = 0.1 * W + i * (tx - 0.1 * W - 0.6 * s) / 3.0
        dk.decorative(na.station(slide, sx, ry, 0.28 * s, ring=k.P["casing"]), "a station before the terminus")
    na.interchange(slide, tx, ry, 0.9 * s, 0.7 * s, ring=k.P["casing"])
    return r


def caps(t):
    return t.upper() if t and not dk._has_cjk(t) and dk.script_of(t) is None else t
```

If `dk.arrow` takes different parameters, call `python3 scripts/sigs.py arrow` and adapt the two calls to its signature (a right-pointing block arrow of the given box, coloured sign ink).

- [ ] **Step 4: Run to verify it passes**

Run: `cd skills/slide-maker && python3 tests/test_native_languages_p5.py | tail -5`
Expected: `… passed, 0 failed`.

- [ ] **Step 5: Confirm the Korean way-out wording** with one search (Seoul Metro exit signage, "나가는 곳"); if a reference shows another standard wording, change `LABELS3` and the test together and note the source in the comment.

- [ ] **Step 6: Render and look**, as Task 2 Step 5, for wayfinding (both orderings on the points page).

- [ ] **Step 7: Commit**

```bash
git add skills/slide-maker/scripts/visual_languages.py skills/slide-maker/scripts/vl_native3.py skills/slide-maker/tests/test_native_languages_p5.py
git commit -m "wayfinding (导视线路): a native visual language of metro lines, station signs and a departure board"
```

---

### Task 4: Samples, guidance and docs for any agent

**Files:**
- Create: `skills/slide-maker/assets/vl/samples/interface.jpg`, `interface-dark.jpg`, `wayfinding.jpg`, `wayfinding-night.jpg`; Modify: `assets/vl/samples/manifest.json`, `assets/vl/samples/hues.json`
- Modify: `skills/slide-maker/scripts/directions_diversity.py` (guidance message), `references/visual-languages.md`, `references/interview-protocol.md`, `references/codex-runtime.md`, `references/bespoke-registers.md` (pointer from `transit-signage`), `references/file-inventory.md` (+ `vl_native3.py`), `SKILL.md` (the sentence listing the nine drawn languages → eleven), `README.md`, `README_CN.md` (gallery rows), `scripts/sigs.py` examples for `route`, `roundel`, `sign_panel`, `ui_window`, `ui_button`, `ui_device`
- Test: `tests/test_visual_languages.py` (sample fingerprints already cover every `NATIVE` member — run it)

- [ ] **Step 1: Write the failing test.** Run the existing sample check, which now iterates the two new names:

Run: `cd skills/slide-maker && python3 tests/test_visual_languages.py | tail -3`
Expected: FAIL naming the missing `interface` / `wayfinding` samples or manifest fingerprints.

- [ ] **Step 2: Build the samples** exactly as P4 did (the script header of `tests/test_visual_languages.py` names the command): for each `(name, ground)` in `(interface, light) (interface, dark) (wayfinding, light) (wayfinding, night)`: `vl.build_sample(name, out, ground=ground)`, render, `vl.sample_sheet(render_dir, assets/vl/samples/<stem>.jpg)`, keep ≤ 350 KB (lower the JPEG quality if larger), and write `vl.sample_fingerprint(pptx)` into `manifest.json`; then `python3 scripts/visual_languages.py --gates <name> --ground <g> --deck <tmp>` for each to refresh `hues.json`. Look at each sheet before saving it.

- [ ] **Step 3: Guidance text.** In `directions_diversity.py` line ~257, in `interview-protocol.md` (the native-language bullet) and in `visual-languages.md` (§ Native languages, the guidance list), add exactly: `product launch, app, SaaS, feature tour, internal tool → interface`; `roadmap, process, onboarding, journey, strategy route, transport/city → wayfinding`. In `visual-languages.md` add a "### The third set — `interface` · `wayfinding`" section modelled on P4's, documenting: the two grounds, every extra with its pages and fallback (spec §4 table verbatim), the meaning rule (route only with `ordered=True`; states from the caller), and one runnable call per page. In `bespoke-registers.md`, under `transit-signage`, add: "For a deck that only needs the look, the native visual language `wayfinding` builds all seven pages (`references/visual-languages.md`)." Update `SKILL.md`'s visual-language bullet list of drawn languages to include `interface` and `wayfinding` and keep `check_skill_lossless.py` green (add an allowlist entry only if a line is reworded, with its reason).

- [ ] **Step 4: README galleries.** Add the two sample JPGs as two more cells in the 3-column visual-language gallery of `README.md` and `README_CN.md` (same markup as the existing cells; captions "Product interface · 产品界面", "Wayfinding · 导视线路").

- [ ] **Step 5: Run to verify**

Run: `cd skills/slide-maker && python3 tests/test_visual_languages.py | tail -3 && python3 scripts/check_inventory.py && python3 scripts/check_skill_lossless.py && python3 scripts/sigs.py --example route roundel ui_window | head -20`
Expected: all green; the examples print runnable calls.

- [ ] **Step 6: Commit**

```bash
git add skills/slide-maker/assets/vl/samples/interface.jpg skills/slide-maker/assets/vl/samples/interface-dark.jpg skills/slide-maker/assets/vl/samples/wayfinding.jpg skills/slide-maker/assets/vl/samples/wayfinding-night.jpg skills/slide-maker/assets/vl/samples/manifest.json skills/slide-maker/assets/vl/samples/hues.json skills/slide-maker/scripts/directions_diversity.py skills/slide-maker/scripts/sigs.py skills/slide-maker/references/visual-languages.md skills/slide-maker/references/interview-protocol.md skills/slide-maker/references/codex-runtime.md skills/slide-maker/references/bespoke-registers.md skills/slide-maker/references/file-inventory.md skills/slide-maker/SKILL.md README.md README_CN.md
git commit -m "interface and wayfinding: samples, guidance, docs and gallery"
```

---

### Task 5: Verification and delivery

**Files:** none new (fixes go into the files above, each with its own RED→GREEN test).

- [ ] **Step 1: Full suite.** Run every test script the CI runs (scratchpad `cisteps.py` over all steps, in chunks of < 10 minutes, foreground). Expected: every step green. A failure is investigated, fixed with a failing test first, and the run repeated.
- [ ] **Step 2: Generality corpus.** Extend the P3/P4 corpus runner's language list through `NATIVE` (it already iterates it) and run it. Every refusal must be a real overflow.
- [ ] **Step 3: Linux font simulation** (scratchpad `cisim/cisim.py`) over the P5 test and the corpus. Expected: only the known artifacts.
- [ ] **Step 4: Look.** Render every page × ground × canvas for both languages in English and Chinese; read the PNGs in batches; fix anything wrong; then put a sheet on `~/Desktop` for the user.
- [ ] **Step 5: Non-Claude run.** One subagent, limited to `SKILL.md`, `references/` and `sigs.py`, builds one 7-page deck per language from a short brief; fix every friction it reports.
- [ ] **Step 6: Independent review** of the whole branch (one fresh reviewer); fix Critical/Important with RED→GREEN tests; park minors.
- [ ] **Step 7: Deliver.** Report what is committed and unpushed. Push only when the user says so; after a push, wait for the GitHub CI conclusion, then `rsync -a --checksum --dry-run` and `rsync -a --checksum` the skill into `~/.agents/skills/slide-maker`.
