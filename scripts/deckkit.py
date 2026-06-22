#!/usr/bin/env python3
"""deckkit — reusable helpers for building clean slides with python-pptx.

General-purpose: works whether you build ON a user's template (open_template) or
from scratch when they have none (blank_deck + title_bar/footer). Import this from
a small per-deck build script rather than copy-pasting primitives every time.
A brand-free worked example lives at references/examples/build_example_generic.py.

Design intent (see references/design-principles.md — these are the PRESENTED-deck defaults; a
read-alone / reference / poster deck legitimately runs denser, so flex by delivery mode):
  - terse, few-word points for a SPOKEN deck (a visual aid, not a document); a read-alone deck
    carries the fuller sentence a speaker would otherwise say
  - native diagrams (boxes + arrows) over walls of text
  - a clear title per slide; results figures always get a legend + a takeaway

The palette/fonts below are sensible DEFAULTS. When building on a template, pull
the real brand colors from it (inspect_template.py / theme) and set FONT to match;
when building from scratch, pick colors from the user's brand or pick a clean set.

Equations: NEVER rely on Unicode modifier-letter super/subscripts (ᴴ ᵀ ᵣ) — many
display fonts lack those glyphs and render tofu/overlap. Use eq_par(), which draws
real baseline-shifted ASCII in a full-coverage font, so it is crisp anywhere.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn, nsdecls
from pptx.oxml import parse_xml
import math

# ---- default professional palette (a neutral blue scheme). NOT tied to any brand —
# when building on a template, override these with the template's real theme colours.
DEEP    = RGBColor(0x00, 0x3C, 0x66)   # deep navy — strong text / dark panels
BLUE    = RGBColor(0x00, 0x7C, 0xC2)   # accent blue — bullets, primary boxes
TEAL    = RGBColor(0x00, 0x9F, 0xBD)   # secondary accent
MAGENTA = RGBColor(0xE3, 0x00, 0x4F)   # highlight / "after" / callout rule
SLATE   = RGBColor(0x3A, 0x4A, 0x55)   # body text
MUTE    = RGBColor(0x5A, 0x64, 0x72)   # captions / secondary (clears 4.5:1 on white; code
                                       # panels use text_c, so this is safe on dark too)
TINT    = RGBColor(0xEA, 0xF3, 0xFA)   # light callout fill
LIGHT   = RGBColor(0xF4, 0xF8, 0xFB)   # lighter fill
PALE    = RGBColor(0xBF, 0xDE, 0xF0)   # pale text on dark panels
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
# secondary accents — for VARIETY so diagrams don't read monotone. The first two
# are from the template theme (brand-coherent); rotate through ACCENTS for chips.
GOLD    = RGBColor(0xC0, 0x96, 0x5C)   # theme accent5
STEEL   = RGBColor(0x6E, 0x90, 0xA6)   # theme accent3
VIOLET  = RGBColor(0x6A, 0x4C, 0x93)
GREEN   = RGBColor(0x2E, 0x8B, 0x57)
ACCENTS = [BLUE, TEAL, GOLD, STEEL, VIOLET, GREEN]   # cycle for multi-item diagrams

# layout: keep a consistent gutter of whitespace between a figure and any adjacent
# text/callout/edge. Crowding elements together reads as amateur — give them room.
GUTTER  = 0.4   # inches
# the bottom band reserved for footer() chrome (tag + page number sit at h_in - 0.35).
# content_band()/bottom_callout() keep content out of this zone, so a bottom callout can
# never grow into the footer — the recurring "callout collided with the footer" failure.
FOOTER_BAND = 0.5   # inches, measured up from the slide's bottom edge


def contrast_ratio(c1, c2):
    """WCAG contrast ratio between two colours (RGBColor or 'RRGGBB' hex string).
    Returns a number from 1 (none) to 21 (black-on-white). Body text wants >= 4.5;
    large/bold text >= 3. Use it to sanity-check a text colour against its fill before
    you even render — e.g. a pale caption on a tint, or grey body on white.
        if contrast_ratio(MUTE, WHITE) < 4.5: ...  # too faint, darken it
    Note: this checks the *colour pair*; the render still tells you about size/overlap."""
    def lum(c):
        if isinstance(c, str):
            c = RGBColor.from_string(c)
        chans = []
        for v in (c[0], c[1], c[2]):
            s = v / 255.0
            chans.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
        return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]
    l1, l2 = sorted((lum(c1), lum(c2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def _rgb_dist(a, b):
    """Euclidean RGB distance — a quick proxy for 'are these two fills visually distinct?'.
    (Use this, NOT contrast_ratio, for category colours: two different hues can share a
    luminance — cyan vs amber — so contrast_ratio reads ~1 while they're clearly distinct.)"""
    if isinstance(a, str): a = RGBColor.from_string(a)
    if isinstance(b, str): b = RGBColor.from_string(b)
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def palette(n, accents=None):
    """Return ``n`` DISTINCT categorical fills for a sequence of blocks/chips/cards.

    A sequence of blocks must read as a *thought-through* set of colours, not an accident:
    each block a deliberate, well-separated hue, **adjacent blocks visibly different**, and
    **no neutral gray dropped in as a category** (gray reads as disabled/secondary, not a
    category — reserve it for genuinely de-emphasised items). Pass the deck's own palette
    (e.g. your style's ``ACCENTS``); defaults to deckkit's ``ACCENTS``. Cycles with a warning
    if ``n`` exceeds the available hues (extend ``ACCENTS`` rather than repeat a category
    colour), and warns if any two ADJACENT fills are perceptually too close — so a same-colour
    or near-duplicate pair surfaces at build time instead of in the render.

        fills = dk.palette(4, ACCENTS)          # 4 distinct, well-separated hues
        for (x,y,w,h), label, fill in zip(cells, labels, fills):
            dk.chip(s, x, y, w, h, *label, fill)
    """
    pool = list(ACCENTS if accents is None else accents)
    if not pool:
        raise ValueError("palette needs a non-empty accents list")
    if n > len(pool):
        import warnings
        warnings.warn(f"palette({n}) exceeds {len(pool)} distinct hues — colours will repeat; "
                      f"add more entries to ACCENTS rather than reuse a category colour")
    fills = [pool[i % len(pool)] for i in range(n)]
    import warnings
    for a, b in zip(fills, fills[1:]):
        if _rgb_dist(a, b) < 60:                 # ~perceptually similar / identical
            warnings.warn("palette: two adjacent category fills are nearly identical — "
                          "reorder or extend ACCENTS so neighbouring blocks contrast")
    for c in fills:
        cc = c if not isinstance(c, str) else RGBColor.from_string(c)
        if max(cc[0], cc[1], cc[2]) - min(cc[0], cc[1], cc[2]) < 30:   # near-neutral / gray
            warnings.warn("palette: a near-gray fill is used as a category colour — gray reads "
                          "as disabled/secondary, not a category; use a saturated hue (reserve "
                          "gray for genuinely de-emphasised items)")
    return fills


def palette_from_image(path, n=5, *, keep_neutrals=False):
    """Extract ``n`` representative ACCENT colours from a generated template image, as
    ``RGBColor``, most-frequent first.

    This is the bridge that makes NATIVE content "fit a generated template": derive the
    template's palette from its hero/divider image, set your ``style.py`` colours to it, and
    every native card / chip / heading / motif comes out in the same hues — so the inserted
    blocks read as part of the generated look rather than pasted on top. By default it skips
    near-white and near-black (the background/ink, not accents) and the deck's *base* colour;
    pass ``keep_neutrals=True`` to keep them. Deduplicates perceptually-close hues.

        BASE = palette_from_image("assets/template_bg.png", 6)   # the template's own colours
        ACCENTS = BASE                                           # native content now matches
    """
    from PIL import Image
    from collections import Counter
    im = Image.open(path).convert("RGB")
    im.thumbnail((220, 220))
    q = im.quantize(colors=64, method=Image.FASTOCTREE).convert("RGB")
    out = []
    for (r, g, b), _ in Counter(q.getdata()).most_common():
        mx, mn = max(r, g, b), min(r, g, b)
        if not keep_neutrals:
            if mx > 236 and mn > 226:        # near-white background
                continue
            if mx < 30:                      # near-black ink
                continue
            if mx - mn < 22:                 # washed/near-gray, not an accent
                continue
        c = RGBColor(r, g, b)
        if all(_rgb_dist(c, o) > 48 for o in out):   # keep hues visibly distinct
            out.append(c)
        if len(out) >= n:
            break
    return out

FONT    = "Calibri"       # display font — cross-platform default (ships with MS Office,
                          # renders the same on Windows PowerPoint and macOS/Keynote).
MONO    = "Consolas"      # code / filenames — Calibri's cross-platform monospace pair.
EQFONT  = "Arial"         # equations — universal glyph + Greek coverage
EAFONT  = None            # East-Asian font for CJK text (e.g. "PingFang SC" / "Heiti SC"
                          # / "Microsoft YaHei" / "Noto Sans CJK SC"). When set, every run
                          # ALSO carries an <a:ea> typeface so PowerPoint/Keynote render
                          # Chinese/Japanese/Korean glyphs with THIS font (not an
                          # uncontrolled default) while Latin/numbers stay on FONT. Leave
                          # None for Latin decks. See references/multilingual.md.
DISPLAY = None            # optional DISPLAY/title font (Latin) — when set, title_bar uses it for
                          # the title so headings get their own face vs the FONT body. Falls back
                          # to FONT. Pairing roles (display / body / mono) beats one font for the
                          # whole deck — see references/font-guidance.md ("Type pairing").
EADISPLAY = None          # optional CJK DISPLAY/title font (e.g. "PingFang SC" titles over a
                          # "Hiragino Sans GB"/"Noto Sans CJK SC" EAFONT body). Falls back to EAFONT.
# To re-theme a whole deck (e.g. to match a style example), reassign these AND the
# palette constants above right after importing deckkit, before building — set_font
# resolves FONT at call time, so `deckkit.FONT = "Helvetica Neue"` takes effect.


# ====================================================================== text
def _apply_ea(run, typeface):
    """Set the East-Asian (<a:ea>) typeface so PowerPoint/Keynote render CJK glyphs with
    the chosen font (Latin chars keep the <a:latin> font). python-pptx only writes
    <a:latin>, so we add <a:ea> directly, in the correct schema position (after latin)."""
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        latin = rPr.find(qn('a:latin'))
        (latin.addnext(ea) if latin is not None else rPr.append(ea))
    ea.set('typeface', typeface)

def set_font(run, size, color, bold=False, italic=False, font=None, ea=None):
    run.font.name = font or FONT          # resolve FONT at call time so re-theming works
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    eaf = ea or EAFONT                     # also tag CJK font when set (mixed CN/EN stays correct)
    if eaf:
        _apply_ea(run, eaf)


def text(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         space_after=6, line_spacing=1.0):
    """runs = list of paragraphs; each paragraph = list of run tuples
    (txt, size, color, bold, italic[, font]).

    Vertical centring: to centre text inside a filled box/card, pass anchor=MSO_ANCHOR.MIDDLE
    AND give this textbox the SAME (x, y, w, h) as the box. A y-offset (e.g. y+0.07) combined
    with the box's full height pushes the centre below the box's true middle — text then reads
    "a bit low". Want top padding? Use margin_top, not a y-offset with unchanged height."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Pt(2)
    tf.margin_top = tf.margin_bottom = Pt(2)
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.space_before = Pt(0)
        p.line_spacing = line_spacing
        for (txt, size, color, bold, italic, *rest) in para:
            r = p.add_run(); r.text = txt
            set_font(r, size, color, bold, italic, rest[0] if rest else None)
    return tb


# ===================================================================== shapes
def _grad_fill(shape, stops, angle=90.0, radial=False):
    """Apply a gradient fill WITH PER-STOP ALPHA to a shape (python-pptx solid fills can't do
    this). `stops` = list of (pos 0..1, colour as 'RRGGBB'/RGBColor, alpha 0..1). `angle` is the
    linear direction in degrees (0=→, 90=↓); `radial=True` makes a centre-out radial (for glows).
    This is the enabler for glass cards, soft glows, and graduated photo scrims."""
    sp = shape._element.spPr
    for tag in ("a:noFill", "a:solidFill", "a:gradFill", "a:blipFill", "a:pattFill", "a:grpFill"):
        e = sp.find(qn(tag))
        if e is not None:
            sp.remove(e)
    gs = "".join(
        f'<a:gs pos="{int(round(max(0.0,min(1.0,p))*100000))}">'
        f'<a:srgbClr val="{_hex(c)}"><a:alpha val="{int(round(max(0.0,min(1.0,a))*100000))}"/></a:srgbClr></a:gs>'
        for (p, c, a) in stops)
    direction = ('<a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path>'
                 if radial else f'<a:lin ang="{int(round((angle % 360) * 60000))}" scaled="1"/>')
    el = parse_xml(f'<a:gradFill {nsdecls("a")}><a:gsLst>{gs}</a:gsLst>{direction}</a:gradFill>')
    geom = sp.find(qn("a:prstGeom"))
    if geom is None:
        geom = sp.find(qn("a:custGeom"))
    ln = sp.find(qn("a:ln"))
    if geom is not None:
        geom.addnext(el)
    elif ln is not None:
        ln.addprevious(el)
    else:
        sp.append(el)
    return shape


def box(slide, x, y, w, h, fill=None, line=None, line_w=1.0, round=False, corners="all", r=None,
        grad=None, grad_angle=90.0, grad_radial=False):
    """A rectangle. `round=True` rounds all four corners (radius = 8% of the shorter side,
    or `r` inches if given). For a colored HEADER BAND sitting on top of a rounded card,
    use `corners='top'` and pass `r=<the card's corner radius in inches>` so the band's
    curve MATCHES the card — a square band over a rounded card (corners poking out) is the
    tell to avoid. `corners='bottom'` rounds the bottom two. (A thin accent strip can
    instead be inset by the radius so its square ends fall on the card's straight edge.)

    `grad` gives a GRADIENT fill with per-stop alpha instead of a solid `fill`: a list of
    (pos 0..1, colour, alpha 0..1); `grad_angle` sets linear direction (deg), `grad_radial=True`
    a centre-out radial. Powers glass/glow/scrim — usually via the `glass_card`/`glow`/
    `scrim_overlay` helpers rather than called directly."""
    if not (round or r is not None or corners != "all"):
        t = MSO_SHAPE.RECTANGLE
    elif corners in ("top", "bottom"):
        t = MSO_SHAPE.ROUND_2_SAME_RECTANGLE   # rounds the two top corners (rotate for bottom)
    else:
        t = MSO_SHAPE.ROUNDED_RECTANGLE
    s = slide.shapes.add_shape(t, Inches(x), Inches(y), Inches(w), Inches(h))
    if grad is not None: _grad_fill(s, grad, angle=grad_angle, radial=grad_radial)
    elif fill is None: s.fill.background()
    else: s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None: s.line.fill.background()
    else: s.line.color.rgb = line; s.line.width = Pt(line_w)
    s.shadow.inherit = False
    if t != MSO_SHAPE.RECTANGLE:
        adj = (r / min(w, h)) if r is not None else 0.08
        adj = max(0.0, min(0.5, adj))
        try: s.adjustments[0] = adj
        except Exception: pass
        if corners == "bottom":
            s.rotation = 180
    return s


def glow(slide, cx, cy, w, h, color, alpha=0.5):
    """A soft radial colour GLOW (centre-out) for depth/atmosphere on a DARK slide — place 1-2
    off-centre behind glass cards so a flat black slide gets dimensional lighting. Invisible on
    light decks; don't use there. (cx,cy) is the glow centre in inches."""
    o = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - w / 2), Inches(cy - h / 2), Inches(w), Inches(h))
    o.line.fill.background(); o.shadow.inherit = False
    _grad_fill(o, [(0.0, color, alpha), (1.0, color, 0.0)], radial=True)
    return o


def scrim_overlay(slide, x, y, w, h, *, stops=((0.0, 0.0), (1.0, 0.75)), color="000000", angle=90.0):
    """A GRADUATED alpha scrim over a photo so overlaid text stays legible WHERE THE TEXT IS,
    while the image stays bright elsewhere — far better than a flat dark overlay. `stops` =
    (position, alpha) pairs; aim the gradient toward the text via `angle` (90 = darker at bottom,
    270 = darker at top). Size the rect to the text's zone, not always the whole slide."""
    return box(slide, x, y, w, h, grad=[(p, color, a) for (p, a) in stops], grad_angle=angle)


def glass_card(slide, x, y, w, h, tint, *, accent=None, r=0.14, rim=1.0):
    """A frosted-glass card (UI glassmorphism) rebuilt natively in three layers: (1) a low-alpha
    `tint` gradient body, (2) a white diagonal sheen, (3) a 1px white rim. It only reads as glass
    on a DARK / glowing / photographic background — pair with `glow()` on a dark base. Optional
    `accent` adds a colored top header band. Returns the body shape (place content on top)."""
    body = box(slide, x, y, w, h, round=True, r=r,
               grad=[(0.0, tint, 0.46), (1.0, tint, 0.20)], grad_angle=120)
    body.line.color.rgb = WHITE; body.line.width = Pt(rim)
    sheen = box(slide, x, y, w, h, round=True, r=r,
                grad=[(0.0, "FFFFFF", 0.20), (0.45, "FFFFFF", 0.05), (1.0, "FFFFFF", 0.0)], grad_angle=120)
    sheen.line.fill.background()
    if accent is not None:
        box(slide, x, y, w, 0.58, corners="top", r=r,
            grad=[(0.0, accent, 0.95), (1.0, accent, 0.70)], grad_angle=0)
    return body


def offset_shadow(slide, x, y, w, h, fill, *, dx=0.06, dy=0.06, shadow=None,
                  line=None, line_w=2.0, round=True, r=0.1):
    """A HARD offset 'sticker' / letterpress shadow (riso / print look): a crisp solid shadow
    copy behind the shape, offset by (dx,dy) — NOT a soft blur. Returns the top shape so you can
    place text on it. Use for bold/editorial/retro-print decks; skip in minimal/scientific ones."""
    sh = shadow if shadow is not None else RGBColor(0x1B, 0x1B, 0x1B)
    box(slide, x + dx, y + dy, w, h, fill=sh, round=round, r=r)
    return box(slide, x, y, w, h, fill=fill, line=line, line_w=line_w, round=round, r=r)


_GOOD = RGBColor(0x1F, 0x9D, 0x55)   # positive delta (green)
_BAD = RGBColor(0xE0, 0x3A, 0x2E)    # negative delta (red)

def scorecard(slide, x, y, w, h, label, value, *, delta=None, caption=None, good_up=True,
              ink=DEEP, accent=BLUE, glass_tint=None):
    """A KPI scorecard tile: small-caps label · oversized value · colored ▲/▼ delta · tiny
    caption — the 'current state in numbers' building block. `value`/`label` may be numbers or
    strings (coerced). `delta` is a string ('+3.2pp' / '-18%'); an unsigned value reads as an
    increase, so **a sign is required to mark a decrease**. Its colour is auto-set GREEN/RED by
    direction vs `good_up` (a falling cost with good_up=False is green). `glass_tint` makes it a
    glass tile (use on dark decks). Lay out 3-6 with columns()."""
    if glass_tint is not None:
        glass_card(slide, x, y, w, h, glass_tint); lab_c, val_c, cap_c = WHITE, WHITE, RGBColor(0xCF, 0xD7, 0xE6)
    else:
        box(slide, x, y, w, h, fill=WHITE, line=RGBColor(0xE3, 0xE8, 0xEE), line_w=1.0, round=True, r=0.1)
        box(slide, x, y, 0.1, h, fill=accent, round=True, r=0.05)          # accent spine
        lab_c, val_c, cap_c = MUTE, ink, MUTE
    px = x + 0.28
    text(slide, px, y + 0.22, w - 0.5, 0.3, [[(str(label).upper(), 11, lab_c, True, False)]], space_after=0)
    text(slide, px, y + 0.5, w - 0.5, 0.8, [[(str(value), 33, val_c, True, False)]], space_after=0)
    cy = y + 1.32
    if delta:
        d = str(delta).strip()
        up = not d.startswith(("-", "▼"))            # unsigned / '+' = increase; sign required for a decrease
        dc = _GOOD if (up == good_up) else _BAD
        text(slide, px, cy, w - 0.5, 0.3, [[(("▲ " if up else "▼ ") + d.lstrip("+-▲▼ "), 12, dc, True, False)]], space_after=0)
        cy += 0.3
    if caption:
        text(slide, px, cy, w - 0.5, 0.4, [[(caption, 10.5, cap_c, False, False)]], space_after=0)


def leaderboard(slide, x, y, w, rows, *, row_h=0.5, gap=0.1, ink=DEEP):
    """Ranked / part-to-whole list keyed to a chart: each row = a colored left swatch (matching a
    chart wedge/series) + name + right-aligned value (+ optional sub). Pass the SAME colour list
    you built the chart with so legend and chart stay in sync. rows = [(color, name, value[, sub])]."""
    cy = y
    for row in rows:
        color = row[0]; name = str(row[1]); value = str(row[2])
        sub = str(row[3]) if len(row) > 3 else None
        box(slide, x, cy, 0.12, row_h, fill=color, round=True, r=0.04)
        if sub:                                              # name + sub both stay INSIDE this row
            text(slide, x + 0.28, cy + 0.02, w - 2.0, row_h * 0.58, [[(name, 13, ink, True, False)]],
                 anchor=MSO_ANCHOR.BOTTOM, space_after=0)
            text(slide, x + 0.28, cy + row_h * 0.56, w - 2.0, row_h * 0.42, [[(sub, 9, MUTE, False, False)]], space_after=0)
        else:
            text(slide, x + 0.28, cy, w - 2.0, row_h, [[(name, 13, ink, True, False)]],
                 anchor=MSO_ANCHOR.MIDDLE, space_after=0)
        text(slide, x + w - 1.9, cy, 1.9, row_h, [[(value, 14, ink, True, False)]],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
        cy += row_h + gap
        hrule(slide, x, cy - gap / 2, w, color=RGBColor(0xE6, 0xE9, 0xEE), weight=0.01)
    return cy


def takeaway_rail(slide, x, y, w, label, hero, body, *, accent=MAGENTA, ink=DEEP, body_c=SLATE):
    """The narrative 'so-what' rail beside a chart (the ~35% right column): small caps accent
    label → one restated hero stat → a 2-3 line interpretation. Pair with a chart in the left
    ~65% (content_band). Every designed chart should carry one of these."""
    text(slide, x, y, w, 0.3, [[(label.upper(), 11, accent, True, False)]], space_after=0)
    text(slide, x, y + 0.34, w, 0.9, [[(hero, 34, ink, True, False)]], space_after=0)
    text(slide, x, y + 1.3, w, 2.0, [[(body, 14, body_c, False, False)]], space_after=0, line_spacing=1.2)


# ============================================ layout patterns (editorial / diagram / wayfinding)
def editorial_header(slide, eyebrow, title, *, x=0.6, y=0.55, w=None, accent=MAGENTA, ink=DEEP,
                     serif=None, size=28, rule_w=1.2):
    """Editorial header lockup: a caps eyebrow, a large title, and a short accent hairline beneath.
    The premium/showcase alternative to title_bar (use a serif `serif=` for an editorial register)."""
    if w is None:
        sw, _ = _slide_size(slide); w = sw - 2 * x
    text(slide, x, y, w, 0.3, [[(eyebrow.upper(), 12, accent, True, False)]], space_after=0)
    text(slide, x, y + 0.34, w, 0.8, [[(title, size, ink, True, False, serif)]], space_after=0)
    box(slide, x + 0.02, y + 0.34 + size / 72.0 * 1.18, rule_w, 0.05, fill=accent)


def big_numeral(slide, x, y, n, *, mode="marker", color=MAGENTA, size=None, w=None,
                italic=True, serif="Georgia"):
    """An oversized index figure as wayfinding/rhythm. mode='marker' (solid accent, ~44pt) for a
    numbered item; 'ghost' (very large, near-bg) as a watermark behind a title. The box is sized
    GENEROUSLY WIDE so a short token like '01' / '04' never wraps to two stacked glyphs (the bug
    seen in the Swiss deck — LibreOffice ignores word-wrap=off, so we prevent it by width)."""
    s = size or (44 if mode == "marker" else 132)
    c = color if mode == "marker" else RGBColor(0xE8, 0xE8, 0xE8)
    if w is None:
        w = len(str(n)) * s / 72.0 * 1.0 + 0.5     # wide enough that the figure stays one line
    tb = text(slide, x, y, w, s / 72.0 * 1.35, [[(str(n), s, c, True, italic, serif)]], space_after=0)
    tb.text_frame.word_wrap = False
    return tb


def stat_row(slide, x, y, w, items, *, ink=DEEP, accent=MAGENTA, serif=None, dividers=True,
             fig_size=34, label_c=MUTE):
    """Editorial big-number row: items = [(figure, unit, label), ...] in 2-4 equal columns with
    optional vertical hairline dividers. For 2-4 standout numbers with no trend to plot."""
    n = len(items); gap = 0.4; cw = (w - (n - 1) * gap) / n
    for i, (fig, unit, label) in enumerate(items):
        cx = x + i * (cw + gap)
        runs = [(str(fig), fig_size, ink, True, False, serif)]
        if unit:
            runs.append((" " + str(unit), fig_size * 0.42, accent, True, False, serif))
        text(slide, cx, y, cw, 0.7, [runs], space_after=0)
        text(slide, cx, y + 0.66, cw, 0.4, [[(str(label), 12, label_c, False, False)]], space_after=0)
        if dividers and i > 0:
            box(slide, cx - gap / 2, y + 0.06, 0.014, 0.9, fill=RGBColor(0xDD, 0xDD, 0xDD))
    return y + 1.1


def change_stat(slide, x, y, w, h, before, after, *, accent=MAGENTA, ink=DEEP, before_size=15,
                after_size=28, arrow="→", font=None, split=0.46):
    """A 'before → after' change stat with the AFTER value emphasized large and **vertically
    centered** with the small before+arrow. Mixing very different font sizes on ONE line baseline-
    aligns them, so the small prefix/arrow sinks to the baseline and looks dropped below the big
    number — the misalignment to avoid. Here the two halves are each MIDDLE-anchored on the same
    line (before right-aligned, after left-aligned) so the arrow and the big value meet at the
    centre, optically aligned. Returns nothing; place at the row's box."""
    bw = w * split
    text(slide, x, y, max(0.3, bw - 0.06), h,
         [[(f"{before} {arrow}", before_size, ink, False, False, font)]],
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    text(slide, x + bw + 0.06, y, w - bw - 0.06, h,
         [[(str(after), after_size, accent, True, False, font)]],
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE, space_after=0)


def quadrant(slide, x, y, w, h, *, x_labels=("", ""), y_labels=("", ""), gap=0.35, axis_c=MUTE):
    """A 2×2 matrix whose AXES carry meaning (e.g. frequency × severity). Draws edge axis captions
    and returns the four cell rects (TL, TR, BL, BR) to fill with cards/scorecards. Use only when
    items truly classify on two independent dimensions; else use a plain grid. Leave ≈1.4in of left
    margin (place at x≈1.5) when using `y_labels`, so they sit in the margin without clipping."""
    cw = (w - gap) / 2; ch = (h - gap) / 2
    if x_labels[0] or x_labels[1]:
        text(slide, x, y - 0.32, cw, 0.28, [[(x_labels[0].upper(), 10.5, axis_c, True, False)]], space_after=0)
        text(slide, x + cw + gap, y - 0.32, cw, 0.28, [[(x_labels[1].upper(), 10.5, axis_c, True, False)]], space_after=0)
    if y_labels[0] or y_labels[1]:
        lx = max(0.05, x - 1.35); lw = max(0.5, x - lx - 0.1)
        text(slide, lx, y + ch * 0.42, lw, 0.3, [[(y_labels[0].upper(), 10.5, axis_c, True, False)]], align=PP_ALIGN.RIGHT, space_after=0)
        text(slide, lx, y + ch + gap + ch * 0.42, lw, 0.3, [[(y_labels[1].upper(), 10.5, axis_c, True, False)]], align=PP_ALIGN.RIGHT, space_after=0)
    return [(x, y, cw, ch), (x + cw + gap, y, cw, ch), (x, y + ch + gap, cw, ch), (x + cw + gap, y + ch + gap, cw, ch)]


def _connector(slide, x0, y0, x1, y1, color, w=1.5, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x0), Inches(y0), Inches(x1), Inches(y1))
    c.line.color.rgb = color; c.line.width = Pt(w); c.shadow.inherit = False
    if dash:
        ln = c.line._get_or_add_ln()
        ln.append(parse_xml(f'<a:prstDash {nsdecls("a")} val="dash"/>'))
    return c


def hub_spoke(slide, cx, cy, radius, center, spokes, *, hub=(1.7, 1.0), node=(1.8, 0.78),
              accent=BLUE, ink=DEEP, fill=None):
    """Radial 'one core, many peers' diagram: a hub at (cx,cy) with N spoke cards evenly angled on
    a circle of `radius`, connectors drawn behind. `center`='label', spokes=['a','b',...] or
    [(title,sub)]. Use for a platform+modules / metric+drivers; not for sequences (use a pipeline)."""
    n = len(spokes); pts = []
    for i in range(n):
        ang = math.radians(-90 + i * 360.0 / n)
        pts.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang)))
    for (sx, sy) in pts:                       # connectors first (behind the nodes)
        _connector(slide, cx, cy, sx, sy, RGBColor(0xC8, 0xCE, 0xDA), w=1.4, dash=True)
    for (sx, sy), sp in zip(pts, spokes):
        title, sub = (sp if isinstance(sp, (tuple, list)) else (sp, ""))
        chip(slide, sx - node[0] / 2, sy - node[1] / 2, node[0], node[1], title, sub,
             fill if fill is not None else WHITE, tcolor=ink)
    chip(slide, cx - hub[0] / 2, cy - hub[1] / 2, hub[0], hub[1], center, "", accent)
    return pts


def timeline(slide, x, y, w, events, *, orientation="h", highlight=None, accent=MAGENTA,
             ink=DEEP, axis_c=RGBColor(0x9A, 0xA0, 0xAE), h=1.4):
    """Native timeline. events = [(when, title[, caption]), ...]. orientation='h' (axis L→R, 3-6
    evenly-weighted events) or 'v' (top→bottom spine, when each event needs 2+ lines). One node is
    recolored `accent` via `highlight` index. For chronology/roadmaps/evolution — not comparisons."""
    n = len(events)
    if orientation == "h":
        ay = y + 0.2
        box(slide, x, ay - 0.012, w, 0.024, fill=axis_c)
        step = w / max(1, n - 1) if n > 1 else 0
        for i, ev in enumerate(events):
            ex = x + (i * step if n > 1 else w / 2)
            when, title = ev[0], ev[1]; cap = ev[2] if len(ev) > 2 else ""
            em = (highlight is None or i == highlight)
            dc = accent if em else axis_c
            box(slide, ex - 0.09, ay - 0.09, 0.18, 0.18, fill=dc, round=True, r=0.09)
            text(slide, ex - 1.0, ay + 0.18, 2.0, 0.3, [[(str(when), 13, dc, True, False)]], align=PP_ALIGN.CENTER, space_after=0)
            text(slide, ex - 1.0, ay + 0.5, 2.0, 0.3, [[(title, 12, ink, True, False)]], align=PP_ALIGN.CENTER, space_after=0)
            if cap:
                text(slide, ex - 1.1, ay + 0.78, 2.2, 0.5, [[(cap, 10.5, MUTE, False, False)]], align=PP_ALIGN.CENTER, space_after=0)
    else:
        ax = x + 0.12
        box(slide, ax - 0.012, y, 0.024, h, fill=axis_c)
        step = h / max(1, n)
        for i, ev in enumerate(events):
            ey = y + i * step + 0.1
            when, title = ev[0], ev[1]; cap = ev[2] if len(ev) > 2 else ""
            em = (highlight is None or i == highlight); dc = accent if em else axis_c
            box(slide, ax - 0.09, ey - 0.09, 0.18, 0.18, fill=dc, round=True, r=0.09)
            text(slide, ax + 0.35, ey - 0.16, w - 0.5, 0.3, [[(str(when) + "  ", 13, dc, True, False), (title, 13, ink, True, False)]], space_after=0)
            if cap:
                text(slide, ax + 0.35, ey + 0.16, w - 0.5, 0.4, [[(cap, 10.5, MUTE, False, False)]], space_after=0)
    return y + (h if orientation == "v" else 1.4)


def image_tab(slide, x, y, text_str, *, color=DEEP, tcolor=WHITE, size=10.5):
    """A small solid corner label-tab that belongs to a photo (EXTERIOR / BEFORE / 第一). Place at
    the image's corner so the label reads as part of it, not floating beside it."""
    wpt = 0.16 + 0.085 * len(text_str)
    box(slide, x, y, wpt, 0.32, fill=color)
    text(slide, x, y, wpt, 0.32, [[(text_str.upper(), size, tcolor, True, False)]],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)


def before_after(slide, x, y, w, h, img_a, img_b, label_a="BEFORE", label_b="AFTER", *,
                 accent=MAGENTA, gap=0.7):
    """Two equal image cards with corner label-tabs and a connecting accent arrow — for old↔new /
    v1↔v2 / renovation comparisons (exactly two)."""
    cw = (w - gap) / 2
    picture(slide, img_a, x, y, cw, h, fit="cover"); image_tab(slide, x + 0.12, y + 0.12, label_a, color=accent)
    picture(slide, img_b, x + cw + gap, y, cw, h, fit="cover"); image_tab(slide, x + cw + gap + 0.12, y + 0.12, label_b, color=accent)
    arrow(slide, x + cw + 0.08, y + h / 2 - 0.13, gap - 0.16, 0.26, color=accent)


def photo_triptych(slide, imgs, *, x=0.0, y=1.1, w=None, h=4.4, scrim=False):
    """Three full-height image columns as one hero band (zero gutter). For one subject with several
    strong views / a 'scale & grandeur' message. Optional bottom scrim for an overlaid caption."""
    if w is None:
        sw, _ = _slide_size(slide); w = sw - 2 * x if x else sw
    cw = w / 3
    for i, im in enumerate(imgs[:3]):
        picture(slide, im, x + i * cw, y, cw, h, fit="cover")
    if scrim:
        scrim_overlay(slide, x, y + h - 1.4, w, 1.4, stops=((0.0, 0.0), (1.0, 0.7)), angle=90)


def corner_frame(slide, *, corners=("tl", "br"), color=MAGENTA, length=0.9, weight=0.04, inset=0.5):
    """Decorative L-corner brackets to frame a sparse closing/quote slide so it reads as composed,
    not unfinished. Use on one slide, not throughout."""
    sw, sh = _slide_size(slide)
    for c in corners:
        if c == "tl":   px, py, hx, vy = inset, inset, inset, inset
        elif c == "tr": px, py, hx, vy = sw - inset, inset, sw - inset - length, inset
        elif c == "bl": px, py, hx, vy = inset, sh - inset, inset, sh - inset - length
        else:           px, py, hx, vy = sw - inset, sh - inset, sw - inset - length, sh - inset - length
        box(slide, hx, py - weight / 2, length, weight, fill=color)   # horizontal arm
        box(slide, px - weight / 2, vy, weight, length, fill=color)   # vertical arm


def accent_one(items, featured_idx, accent, neutral=RGBColor(0xC2, 0xC6, 0xD2)):
    """One-accent discipline as a list: return a colour per item with ONLY `featured_idx` in the
    accent and every other item on `neutral`. Pass to chips/cards/series so the eye goes to the
    one thing that matters (the Swiss/data decks' restraint). Featured=None → all neutral."""
    return [accent if (featured_idx is not None and i == featured_idx) else neutral for i in range(len(items))]


# ================================== publication templates · editorial chrome · self-demo · texture
def _set_spc(shape, pts):
    """Letter-spacing (tracking) in points on every run of a textbox — for tracked caps eyebrows."""
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            r._r.get_or_add_rPr().set("spc", str(int(pts * 100)))
    return shape


def part_eyebrow(slide, x, y, text_str, *, w=6.0, color=MUTE, font=MONO, size=11, track=1.5):
    """A small TRACKED caps eyebrow in the chrome (usually mono) font — the editorial/technical
    'part label'. Route every kicker/eyebrow through one chrome font for a quiet signature."""
    tb = text(slide, x, y, w, 0.3, [[(text_str.upper(), size, color, True, False, font)]], space_after=0)
    return _set_spc(tb, track)


def page_marker(slide, page, total=None, *, font=MONO, color=MUTE, size=9):
    """A tiny mono page marker at bottom-right ('03 / 14') — chrome, not content."""
    sw, sh = _slide_size(slide)
    label = f"{int(page):02d} / {int(total):02d}" if total else f"{int(page):02d}"
    text(slide, sw - 1.6, sh - 0.42, 1.2, 0.3, [[(label, size, color, True, False, font)]],
         align=PP_ALIGN.RIGHT, space_after=0)


def cover(slide, title, *, issue_label=None, subtitle=None, mode_caption=None, x=0.7, y=None,
          accent=MAGENTA, ink=DEEP, bg=None, display=None, chrome=MONO):
    """A publication-style COVER (issue label + big display title + accent rule + subtitle + a
    date/mode caption) designed to be mirrored by colophon() as a bookend. Stronger than a plain
    title slide for editorial/report/zine decks."""
    sw, sh = _slide_size(slide)
    if bg is not None:
        box(slide, 0, 0, sw, sh, fill=bg)
    yy = (sh / 2 - 1.1) if y is None else y
    if issue_label:
        part_eyebrow(slide, x + 0.02, yy - 0.5, issue_label, color=accent, font=chrome)
    text(slide, x, yy, sw - 2 * x, 1.4, [[(title, 46, ink, True, False, display)]], space_after=2, line_spacing=1.0)
    box(slide, x + 0.02, yy + 1.5, 1.4, 0.06, fill=accent)
    if subtitle:
        text(slide, x, yy + 1.7, sw - 2 * x, 0.5, [[(subtitle, 16, ink, False, False)]], space_after=0)
    if mode_caption:
        part_eyebrow(slide, x + 0.02, sh - 0.7, mode_caption, color=MUTE, font=chrome)


def colophon(slide, tagline, *, credits=None, tooling=None, x=0.7, accent=MAGENTA, ink=DEEP,
             bg=None, display=None, chrome=MONO):
    """A closing COLOPHON mirroring the cover: a payoff tagline + small mono credits/tooling. A
    stronger close than 'Thanks'; the credits slot doubles as a research deck's sources note."""
    sw, sh = _slide_size(slide)
    if bg is not None:
        box(slide, 0, 0, sw, sh, fill=bg)
    yy = sh / 2 - 0.9
    text(slide, x, yy, sw - 2 * x, 1.4, [[(tagline, 40, ink, True, False, display)]], space_after=2, line_spacing=1.0)
    box(slide, x + 0.02, yy + 1.4, 1.4, 0.06, fill=accent)
    cy = yy + 1.72
    if credits:
        part_eyebrow(slide, x + 0.02, cy, "credits", color=accent, font=chrome)
        text(slide, x, cy + 0.28, sw - 2 * x, 0.6, [[(credits, 12, ink, False, False, chrome)]], space_after=0)
        cy += 0.92
    if tooling:
        part_eyebrow(slide, x + 0.02, cy, "made with", color=accent, font=chrome)
        text(slide, x, cy + 0.28, sw - 2 * x, 0.4, [[(tooling, 11, MUTE, False, False, chrome)]], space_after=0)


def sources_page(slide, sources, *, title="Sources", cols=2, x=0.7, y=1.4, accent=MAGENTA, ink=DEEP, chrome=MONO):
    """Render references as mono numbered columns under an accent header — a research deck's
    colophon / a credible 'where this came from' close."""
    sw, sh = _slide_size(slide)
    part_eyebrow(slide, x, 0.6, title, color=accent, font=chrome, size=13)
    box(slide, x, 1.02, 1.2, 0.05, fill=accent)
    w = (sw - 2 * x - 0.4 * (cols - 1)) / cols
    per = (len(sources) + cols - 1) // cols
    for ci in range(cols):
        cx = x + ci * (w + 0.4); cy = y
        for i in range(ci * per, min((ci + 1) * per, len(sources))):
            text(slide, cx, cy, w, 0.5, [[(f"{i+1:02d}  ", 9, accent, True, False, chrome),
                                          (sources[i], 9, ink, False, False, chrome)]], space_after=0, line_spacing=1.1)
            cy += 0.46


def specimen_card(slide, x, y, w, h, specimen, label, *, accent=MAGENTA, ink=DEEP, featured=False, serif=None):
    """A rule-on-top SPEC CARD with a giant specimen (a glyph 'Aa', a monogram, a number) as the
    hero — for comparing fonts / brands / metrics. The featured card's rule + specimen recolor to
    the accent. A lighter, more Swiss alternative to a boxed icon-card."""
    rc = accent if featured else RGBColor(0xDD, 0xDD, 0xDD)
    sc = accent if featured else ink
    box(slide, x, y, w, 0.06, fill=rc)                                  # top rule
    text(slide, x, y + 0.14, w, 0.3, [[(label.upper(), 11, MUTE, True, False)]], space_after=0)
    text(slide, x, y + 0.5, w, h - 0.6, [[(specimen, 64, sc, True, False, serif)]],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)


def wireframe_grid(slide, x, y, w, h, cells, *, cols=4, rows=3, highlight=None, line=None, ink=DEEP, accent=MAGENTA):
    """A SELF-DEMONSTRATING annotated wireframe — labeled outline cells over a cols×rows grid, for
    decks ABOUT layout/design/systems (show the scaffolding). cells = [(label, c0, cspan, r0, rspan)];
    `highlight` recolors one cell. Pair with spec_list() for the 'derived = base × n' math."""
    ln = line or RGBColor(0xCC, 0xCC, 0xCC)
    cw = w / cols; ch = h / rows
    for i in range(cols + 1): box(slide, x + i * cw - 0.005, y, 0.01, h, fill=ln)
    for j in range(rows + 1): box(slide, x, y + j * ch - 0.005, w, 0.01, fill=ln)
    for k, (label, c0, cspan, r0, rspan) in enumerate(cells):
        cx = x + c0 * cw; cy = y + r0 * ch
        em = (highlight == k)
        box(slide, cx + 0.04, cy + 0.04, cspan * cw - 0.08, rspan * ch - 0.08,
            fill=None, line=accent if em else ink, line_w=2 if em else 1)
        text(slide, cx + 0.12, cy + 0.1, cspan * cw - 0.24, 0.3,
             [[(label.upper(), 10, accent if em else ink, True, False, MONO)]], space_after=0)


def spec_list(slide, x, y, lines, *, font=MONO, color=DEEP, size=12, gap=0.32):
    """Monospace 'derived = base × n' spec lines — pairs with wireframe_grid for a systems deck."""
    cy = y
    for ln in lines:
        text(slide, x, cy, 6.0, 0.3, [[(ln, size, color, False, False, font)]], space_after=0); cy += gap
    return cy


def photo_card(slide, x, y, w, h, *, role="info", accent=MAGENTA, r=0.1, alpha=0.92):
    """A translucent tinted card to hold text ON a photo (keeps the image visible behind). `role`:
    'info' (light), 'primary' (dark), 'accent' (accent tint). Returns the text colour to use on it."""
    fc, tc = {"info": ("FFFFFF", DEEP), "primary": ("141414", WHITE),
              "accent": (_hex(accent), WHITE)}.get(role, ("FFFFFF", DEEP))
    box(slide, x, y, w, h, round=True, r=r, grad=[(0.0, fc, alpha), (1.0, fc, alpha)])
    return tc


def backdrop_motif(slide, *, kind="grid", color=None, spacing=0.6, accent_disc=None,
                   disc_at=None, disc_r=0.7):
    """A FAINT full-bleed texture (grid / graph-paper) + optional accent disc, to bookend a deck on
    its cover and closer as one object. Keep it faint (≈#EEE) so it never fights body content."""
    sw, sh = _slide_size(slide)
    c = color or RGBColor(0xEE, 0xEE, 0xEE)
    n = int(sw / spacing) + 1
    for i in range(n): box(slide, i * spacing - 0.004, 0, 0.008, sh, fill=c)
    for j in range(int(sh / spacing) + 1): box(slide, 0, j * spacing - 0.004, sw, 0.008, fill=c)
    if accent_disc is not None:
        cx, cy = disc_at or (sw - 1.6, 1.4)
        o = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - disc_r), Inches(cy - disc_r), Inches(2 * disc_r), Inches(2 * disc_r))
        o.fill.solid(); o.fill.fore_color.rgb = accent_disc; o.line.fill.background(); o.shadow.inherit = False


_ARROW_SHAPE = {"right": MSO_SHAPE.RIGHT_ARROW, "left": MSO_SHAPE.LEFT_ARROW,
                "up": MSO_SHAPE.UP_ARROW, "down": MSO_SHAPE.DOWN_ARROW}

def arrow(slide, x, y, w, h, color=BLUE, direction="right"):
    """A solid block arrow. **Point it in the direction the flow actually moves.**
    `direction` is "right" (default), "left", "up", or "down". For a vertical flow —
    e.g. two stacked boxes (problem on top, solution below) — use "down" (or "up"), NOT a
    sideways arrow: a left/right arrow between vertically-stacked blocks reads as wrong.
    For an up/down arrow give it a tall, narrow box (small w, larger h); for left/right a
    wide, short box. The arrow fills the (w, h) box you pass."""
    shape = _ARROW_SHAPE.get(direction.lower(), MSO_SHAPE.RIGHT_ARROW)
    a = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = color
    a.line.fill.background(); a.shadow.inherit = False
    try: a.adjustments[0] = 0.55; a.adjustments[1] = 0.55
    except Exception: pass
    return a


def arrow_label(slide, x, y, w, h, label, color=BLUE, size=9, lab_c=None, box_w=1.3, bold=True,
                direction="right"):
    """An arrow with its label snug against it — so connector labels (a verb, a transform
    name, a step — e.g. 'encode', 'train', 'merge', 'step 2') stay tight to the arrow rather
    than drifting. **Pass `direction` to match the flow** (right/left/up/down, same as
    `arrow`): for a horizontal arrow the label sits centred just above it; for a **vertical**
    (up/down) arrow it sits centred just to the **right** of it (placing it above a vertical
    arrow would read as belonging to the box above). `box_w` is the (transparent) label-box
    width; shrink it when the arrow sits in a narrow gap. Returns the arrow."""
    lab_c = lab_c or color
    th = size / 72.0 * 1.3
    if direction.lower() in ("up", "down"):
        text(slide, x + w + 0.06, y + h / 2.0 - th / 2.0, box_w, th + 0.04,
             [[(label, size, lab_c, bold, False)]], align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    else:
        text(slide, x + w / 2.0 - box_w / 2.0, y - th - 0.04, box_w, th + 0.04,
             [[(label, size, lab_c, bold, False)]], align=PP_ALIGN.CENTER, space_after=0)
    return arrow(slide, x, y, w, h, color=color, direction=direction)


# ====================================================================== images
def _round_pic_geom(pic, radius_in, w_in, h_in):
    """Give a placed picture rounded corners (so an image matches a rounded card/frame around it).
    `radius_in` is the corner radius in inches, applied to the picture's ACTUAL placed size."""
    ss = max(0.01, min(w_in, h_in))
    adj = int(max(0.0, min(0.5, radius_in / ss)) * 100000)
    g = pic._element.spPr.find(qn('a:prstGeom'))
    if g is None:
        return
    g.set('prst', 'roundRect')
    av = g.find(qn('a:avLst'))
    if av is None:
        av = g.makeelement(qn('a:avLst'), {}); g.append(av)
    for gd in list(av):
        av.remove(gd)
    av.append(av.makeelement(qn('a:gd'), {'name': 'adj', 'fmla': f'val {adj}'}))


def picture(slide, path, x, y, w, h, fit="contain", alt=None, round=False, r=None):
    """Place an image in a frame without distorting it.

    `fit="contain"` shows the whole image inside the frame, letterboxed by whitespace.
    Use it for source figures, charts, screenshots, and anything whose edges/labels matter.
    `fit="cover"` fills the frame and crops evenly from the long dimension. Use it for
    decorative plates, photo panels, and generated atmosphere where edge crop is acceptable.

    `round=True` (or `r=<inches>`) gives the image ROUNDED corners — match this to the deck's
    cards/panels so a square photo doesn't sit among rounded blocks (a consistency tell). For an
    image inside a rounded frame, use a radius ≈ the frame's radius minus the border so the curves
    stay concentric. Default radius is 8% of the image's shorter side.

    Pass `alt` for informative images; pass `alt=""` for decorative plates. Returns the
    picture shape. Requires Pillow for reliable aspect-ratio reads, matching the rest of
    deckkit's image/equation helpers.
    """
    from PIL import Image
    with Image.open(path) as im:
        iw, ih = im.size
    if iw <= 0 or ih <= 0:
        raise ValueError(f"cannot read image dimensions for {path}")

    img_ar = iw / ih
    frame_ar = w / h
    fit = fit.lower()
    if fit == "contain":
        if frame_ar > img_ar:
            ph = h
            pw = h * img_ar
            px = x + (w - pw) / 2
            py = y
        else:
            pw = w
            ph = w / img_ar
            px = x
            py = y + (h - ph) / 2
        pic = slide.shapes.add_picture(path, Inches(px), Inches(py), width=Inches(pw), height=Inches(ph))
    elif fit == "cover":
        pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
        if img_ar > frame_ar:
            crop = (1.0 - frame_ar / img_ar) / 2.0
            pic.crop_left = crop
            pic.crop_right = crop
        elif img_ar < frame_ar:
            crop = (1.0 - img_ar / frame_ar) / 2.0
            pic.crop_top = crop
            pic.crop_bottom = crop
    else:
        raise ValueError("fit must be 'contain' or 'cover'")

    if round or r is not None:
        pwp, php = (pw, ph) if fit == "contain" else (w, h)
        _round_pic_geom(pic, r if r is not None else 0.08 * min(pwp, php), pwp, php)
    if alt is not None:
        alt_text(pic, alt)
    return pic


def columns(n=2, *, slide=None, w_in=None, h_in=None, top=1.15, bottom=0.55, margin=None, gap=None):
    """Return ``n`` equal-width content-column rects ``(x, y, w, h)`` with **symmetric**
    outer margins and equal gutters between columns.

    Use this for any split slide — text+figure, two-up, three-up, image+caption — so the
    left and right regions (and the white margins flanking them) come out the SAME width.
    The most common lopsided-slide tell is a left panel and right panel of different
    widths, or a wider white margin on one side than the other; that happens when x/w are
    eyeballed per panel. Deriving every panel from one grid makes the layout balanced by
    construction:

        L, R = dk.columns(2, slide=s)         # two equal halves, equal flanking margins
        dk.bullet(s, *L[:3], items)           # text in the left half
        dk.picture(s, fig, *R, fit="contain") # figure in the right half (same width)

    **Pass ``slide=`` so the grid matches the deck's REAL size** — the width/height are then
    read from the presentation, so it stays symmetric on a 16:9, a widescreen 13.333×7.5, or
    a poster. Only the no-arg call falls back to the standard 10×5.625 deck; if you call it
    without ``slide=`` on a differently-sized deck, pass the same ``w_in``/``h_in`` you gave
    ``blank_deck`` (otherwise the right margin will be wrong — the very lopsidedness this
    helper exists to prevent).

    ``margin`` (outer left == outer right) and ``gap`` (between columns) default to
    ``GUTTER``. ``top``/``bottom`` reserve room for the title bar and footer. Returns a
    list of ``(x, y, w, h)`` tuples in inches, left to right.
    """
    if slide is not None:
        prs = slide.part.package.presentation_part.presentation
        if w_in is None:
            w_in = prs.slide_width / 914400
        if h_in is None:
            h_in = prs.slide_height / 914400
    w_in = 10.0 if w_in is None else w_in
    h_in = 5.625 if h_in is None else h_in
    margin = GUTTER if margin is None else margin
    gap = GUTTER if gap is None else gap
    if n < 1:
        raise ValueError("columns(n) needs n >= 1")
    usable = w_in - 2 * margin - (n - 1) * gap
    if usable <= 0:
        raise ValueError("margins/gap leave no room for columns; reduce margin or gap")
    cw = usable / n
    y = top
    h = h_in - top - bottom
    return [(margin + i * (cw + gap), y, cw, h) for i in range(n)]


def rows(n=2, *, slide=None, w_in=None, h_in=None, x=None, y=None, w=None, top=1.15, bottom=0.55, gap=None):
    """Return ``n`` equal-**height** row rects ``(x, y, w, h)`` stacked top-to-bottom with
    equal gaps — the vertical counterpart of :func:`columns`.

    Use it for a **vertical stack** of boxes (problem→solution, before→after, a list of
    cards) so the gaps — and any ``arrow(..., direction="down")`` connectors you drop between
    them — are **equal by construction** rather than eyeballed. Pass ``x``/``w`` to confine the
    stack to one column (e.g. the left half from ``columns``); they default to a full-width
    band inset by ``GUTTER`` (derived from the deck's real width when ``slide=`` is given)::

        L, R = dk.columns(2, slide=s)
        top_box, bot_box = dk.rows(2, slide=s, x=L[0], w=L[2], top=1.5, bottom=1.3)
        dk.chip(s, *top_box, "abandon", "used once", STEEL)
        gap_mid = bot_box[1] - (top_box[1] + top_box[3])          # the equal gap between rows
        dk.arrow(s, top_box[0] + top_box[2] / 2 - 0.11, top_box[1] + top_box[3] + (gap_mid - 0.3) / 2,
                 0.22, 0.3, direction="down")                     # centred in that gap
        dk.chip(s, *bot_box, "reuse", "flies again", ORANGE)

    Pass ``slide=`` so it matches the deck's real size. Returns ``(x, y, w, h)`` tuples,
    top to bottom.
    """
    if slide is not None:
        prs = slide.part.package.presentation_part.presentation
        if w_in is None:
            w_in = prs.slide_width / 914400
        if h_in is None:
            h_in = prs.slide_height / 914400
    w_in = 10.0 if w_in is None else w_in
    h_in = 5.625 if h_in is None else h_in
    gap = GUTTER if gap is None else gap
    x = GUTTER if x is None else x
    w = (w_in - 2 * GUTTER) if w is None else w
    y = top
    if n < 1:
        raise ValueError("rows(n) needs n >= 1")
    usable = h_in - top - bottom - (n - 1) * gap
    if usable <= 0:
        raise ValueError("top/bottom/gap leave no room for rows; reduce them")
    rh = usable / n
    return [(x, y + i * (rh + gap), w, rh) for i in range(n)]


def content_band(slide, *, top=1.15, footer_gap=0.15):
    """The one authoritative SAFE content rect ``(x, y, w, h)`` — below the title bar and
    **above the footer band** — read from the deck's REAL size.

    Use it instead of hand-picking 'somewhere above the footer' y-coordinates (the magic
    numbers like 4.3 / 5.05 that drift and let auto-growing blocks collide with the footer).
    The bottom edge is ``h_in - FOOTER_BAND - footer_gap``, so anything placed within the
    returned rect clears ``footer()``. Pair with :func:`vstack` / :func:`bottom_callout`.
    """
    w_in, h_in = _slide_size(slide)
    y = top
    bottom_y = h_in - FOOTER_BAND - footer_gap
    return (GUTTER, y, w_in - 2 * GUTTER, bottom_y - y)


def vstack(slide, x, y, w, blocks, *, gap=GUTTER, bottom=None, anchor="top"):
    """Measured vertical packer — **equal gaps and no overlap, guaranteed by construction**.

    Unlike :func:`rows` (which returns equal *fixed*-height cells), ``vstack`` respects each
    block's CONTENT-driven height, so a callout/bullet-list/chip that auto-grows can't overflow
    its cell and collide with the block below (the recurring "raised callout overlapped the
    bullets above it" failure).

    ``blocks`` = list of ``(height_in, draw)`` where ``draw(x, y, w)`` renders the block at that
    top-left and width. Measure each height first with :func:`measure_callout` /
    :func:`measure_bullets` / :func:`measure_text` (or a figure's known aspect).

    With ``bottom`` given (e.g. from ``content_band``): raises a located error if the blocks
    can't fit (so a collision surfaces at BUILD time, not at render); ``anchor='center'`` centres
    the stack in the band and ``anchor='justify'`` spreads equal gaps to fill it — both kill the
    "too much dead-white on the bottom" tell. Returns the placed ``(x, y, w, h)`` rects.
    """
    n = len(blocks)
    if n == 0:
        return []
    heights = [h for h, _ in blocks]
    content = sum(heights)
    total = content + gap * (n - 1)
    if bottom is not None:
        avail = bottom - y
        if total > avail + 1e-6:
            raise ValueError(
                f"vstack overflow: blocks need {total:.2f}in but the band is only {avail:.2f}in "
                f"— shorten text, drop a block, or raise the top. (Surfaced at build time on purpose.)")
        if anchor == "center":
            y += (avail - total) / 2
        elif anchor == "justify" and n > 1:
            gap = (avail - content) / (n - 1)
    cy = y
    rects = []
    for h, draw in blocks:
        draw(x, cy, w)
        rects.append((x, cy, w, h))
        cy += h + gap
    return rects


# ================================================================= components
def _is_wide(o):
    """True for CJK / full-width code points — their glyph advance is ≈ one em."""
    return (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xAC00 <= o <= 0xD7A3
            or 0xF900 <= o <= 0xFAFF or 0xFE30 <= o <= 0xFE4F or 0xFF00 <= o <= 0xFF60
            or 0xFFE0 <= o <= 0xFFE6 or 0x20000 <= o <= 0x3FFFD)


def _disp_len(s):
    """Display width in 'Latin-char' units: CJK / full-width glyphs count as 2. Used only by
    the heuristic FALLBACK in `_measure_lines`; the primary path measures real glyph
    advances. Counting wide glyphs as 2 keeps that fallback safe for CJK text."""
    return sum(2 if _is_wide(ord(ch)) else 1 for ch in s)


# Chars-per-line estimates over-count narrow glyphs (ASCII digits/spaces/dashes, CJK
# punctuation), so an item one char over the wrap threshold gets a phantom extra line. This
# slack absorbs that bias. It is now only used by the heuristic FALLBACK below — the primary
# path (`_measure_lines`) measures real glyph advances and needs no slack.
_WRAP_SLACK = 2

# ---- accurate text measurement (real glyph metrics, with a heuristic fallback) ----
_MEAS_PREC = 4                 # load fonts at size*PREC px for sub-point precision
_FONT_PATH_CACHE = {}
_PIL_FONT_CACHE = {}


def _font_file(name, bold=False):
    """Resolve a font family name to a file path (cached). Returns None if unresolvable."""
    key = (name, bold)
    if key not in _FONT_PATH_CACHE:
        try:
            from matplotlib import font_manager as _fm
            _FONT_PATH_CACHE[key] = _fm.findfont(
                _fm.FontProperties(family=name, weight=("bold" if bold else "normal")))
        except Exception:
            _FONT_PATH_CACHE[key] = None
    return _FONT_PATH_CACHE[key]


def _pil_font(name, size_pt, bold=False):
    """A cached Pillow font for `name` at `size_pt` (loaded at size*PREC px)."""
    key = (name, bold, round(size_pt, 2))
    f = _PIL_FONT_CACHE.get(key)
    if f is None:
        from PIL import ImageFont
        f = ImageFont.truetype(_font_file(name, bold), max(1, int(round(size_pt * _MEAS_PREC))))
        _PIL_FONT_CACHE[key] = f
    return f


def _lines_heuristic(text, size_pt, avail_in):
    """Chars-per-line line-count estimate — the fallback when measurement isn't available."""
    cpl = max(6, int(avail_in * 136.0 / size_pt))
    eff = max(1, _disp_len(text) - _WRAP_SLACK)
    return max(1, -(-eff // cpl))


def _measure_lines(runs, size_pt, avail_in, font=None):
    """How many lines styled text wraps to — MEASURED, not estimated.

    `runs` = [(text, bold), ...] set at `size_pt` within `avail_in` inches of usable width.
    Narrow runs are measured with the REAL Latin font's glyph advances (Pillow, the bold
    parts measured bold); CJK / full-width glyphs are one em (= size_pt) by definition.
    A greedy line-breaker then counts wraps, breaking at spaces, between CJK glyphs, and at
    CJK↔Latin boundaries (Latin words stay whole). Because it uses the same font metrics the
    renderer does, the count matches the rendered layout far more closely than a chars-per-
    line guess. Falls back to `_lines_heuristic` if Pillow or the font can't be loaded — so a
    build never breaks over measurement. Lazy-imports Pillow/matplotlib."""
    fontname = font or FONT
    flat = "".join(t for t, _ in runs)
    if not flat:
        return 1
    avail = max(1.0, avail_in * 72.0)                       # usable width, in points
    try:
        fonts = {b: _pil_font(fontname, size_pt, b) for b in (False, True)}
        getlen = lambda s, b: fonts[b].getlength(s) / _MEAS_PREC
        getlen("x", False)                                  # probe — raises if unusable
    except Exception:
        return _lines_heuristic(flat, size_pt, avail_in)

    items = []                                              # (width_pt, kind): 'w'ord 's'pace 'c'jk
    for text, bold in runs:
        word = []
        for ch in text:
            if ch == " ":
                if word:
                    items.append((getlen("".join(word), bold), "w")); word = []
                items.append((getlen(" ", bold), "s"))
            elif _is_wide(ord(ch)):
                if word:
                    items.append((getlen("".join(word), bold), "w")); word = []
                items.append((float(size_pt), "c"))
            else:
                word.append(ch)
        if word:
            items.append((getlen("".join(word), bold), "w"))

    x = 0.0
    lines = 1
    for w, kind in items:
        if kind == "s":                                     # a space never forces a wrap
            if x > 0:
                x += w
            continue
        if w > avail:                                       # token alone wider than the line
            if x > 0:
                lines += 1
            n = int(w // avail)
            lines += n
            x = w - n * avail
            continue
        if x + w > avail and x > 0:
            lines += 1
            x = 0.0
        x += w
    return max(1, lines)


# ---- public "measure before you place" helpers (so a build knows a block's true height
#      at a given width BEFORE choosing its y — measure-then-place, not place-and-pray) ----
def measure_lines(runs, size_pt, avail_in, font=None):
    """Public wrapper: how many lines ``runs`` = [(text, bold), ...] wrap to at ``size_pt``
    within ``avail_in`` inches. Same metric the renderer/`bullet`/`callout` use."""
    return _measure_lines(runs, size_pt, avail_in, font=font)


def measure_callout(label, body, w):
    """Height (inches) :func:`callout` will draw for this ``label``+``body`` at width ``w``.
    Measure it BEFORE placing so the box can be positioned to clear the footer / the block
    below — the single source of truth for the callout height formula."""
    nlines = _measure_lines([(label + "  ", True), (body, False)], 12.5, w - 0.44)
    return 0.30 + 0.245 * nlines   # 0.30 = top+bottom padding: snug to the text but not cramped


def measure_bullets(items, w, size=17, gap=0.26):
    """Height (inches) :func:`bullet` will occupy for ``items`` at width ``w`` (no trailing
    gap), using the same per-item line measurement — so a build can place the next block
    below the list (or hand the list to :func:`vstack`) without overlap."""
    line_h = size / 72.0 * 1.12
    total = 0.0
    for i, (lead, rest) in enumerate(items):
        nlines = _measure_lines([(lead, True), (rest, False)], size, w - 0.22)
        total += line_h * nlines
        if i < len(items) - 1:
            total += gap
    return total


def measure_text(runs, w, size, *, line_h_factor=1.12, pad=0.0):
    """Height (inches) a plain :func:`text` block of ``runs`` = [(text, bold), ...] needs at
    ``size`` within width ``w``. ``pad`` adds top+bottom slack."""
    nlines = _measure_lines(runs, size, w)
    return nlines * (size / 72.0 * line_h_factor) + pad


def bullet(slide, x, y, w, items, size=17, gap=0.26, marker=BLUE, lead_c=DEEP, body_c=SLATE):
    """Square-marker bullets. items = list of (lead, rest); keep both terse.
    Returns the bottom y, so a caller can place the next element (e.g. a callout)
    below the list without overlapping it.

    EVEN RHYTHM depends on every item occupying the SAME line count. Each marker is placed
    by advancing the cursor `line_h * nlines + gap`, where `nlines` is now MEASURED from the
    real font's glyph advances (`_measure_lines` — Latin runs via Pillow, the bold lead
    measured bold, CJK as one em), so it matches what the renderer actually lays out. This
    removes the old heuristic's two failure modes near the wrap boundary — undershoot
    (next bullet OVERLAPS the wrapped text) and overshoot (a PHANTOM blank line is reserved,
    so the gap before the next bullet looks uneven). If Pillow/the font can't load, it falls
    back to the chars-per-line heuristic. STILL TRUE regardless: an item that genuinely wraps
    to 2 lines takes more vertical space than its 1-line peers, so for an even-looking list
    keep items to a CONSISTENT line count (ideally each comfortably on one line). As always,
    verify the PNG. (At the default size=17 this matches the prior behaviour.)"""
    cy = y
    line_h = size / 72.0 * 1.12              # line height in inches, scaled to font size
    for lead, rest in items:
        box(slide, x, cy + 0.07, 0.09, 0.09, fill=marker)
        text(slide, x + 0.22, cy - 0.02, w - 0.22, 0.6,
             [[(lead, size, lead_c, True, False), (rest, size, body_c, False, False)]],
             space_after=0, line_spacing=1.02)
        # MEASURED line count (real glyph metrics; bold lead measured bold) so the marker
        # advance matches the renderer's layout — no phantom or missing lines.
        nlines = _measure_lines([(lead, True), (rest, False)], size, w - 0.22)
        cy += line_h * nlines + gap
    return cy


def callout(slide, x, y, w, h, label, body, label_c=MAGENTA, fill=TINT, body_c=DEEP):
    # auto-grow height so the body never spills outside the box. Height comes from
    # measure_callout (MEASURED glyph metrics, label measured bold) — the ONE place the
    # formula lives, so a build can call measure_callout()/bottom_callout() and get the
    # identical height it will render.
    h = max(h, measure_callout(label, body, w))
    box(slide, x, y, w, h, fill=fill, round=True)
    rad = 0.08 * min(w, h)                                   # inset the accent bar so its square
    box(slide, x, y + rad, 0.07, h - 2 * rad, fill=label_c)  # ends fall on the card's straight edge
    # text box spans the card's full height so MSO_ANCHOR.MIDDLE centres on the card's true
    # centre (y + h/2). A y-offset here with the same height would push the text below centre.
    text(slide, x + 0.24, y, w - 0.44, h,
         [[(label + "  ", 11, label_c, True, False), (body, 12.5, body_c, False, False)]],
         anchor=MSO_ANCHOR.MIDDLE, space_after=0, line_spacing=1.08)
    return y + h   # bottom edge, so callers can keep a margin below


def bottom_callout(slide, x, w, label, body, *, footer_gap=0.15, **kw):
    """A footer-SAFE bottom callout — **never collides with the footer**, whatever the body
    length. It MEASURES its own height (:func:`measure_callout`), anchors its BOTTOM just above
    the footer band, and grows UPWARD. Returns its TOP y, so the caller keeps content above it.

    This replaces the failure-prone pattern of hand-picking a low ``y`` and passing it to
    :func:`callout` (which grows DOWN into the footer when the text wraps). Use this for every
    bottom takeaway / WHY / NOTE bar::

        top = dk.bottom_callout(s, 0.6, W-1.2, "TAKEAWAY", "...")
        # ...place the slide's content within [title, top].
    """
    _, h_in = _slide_size(slide)
    ch = measure_callout(label, body, w)
    y = h_in - FOOTER_BAND - footer_gap - ch
    callout(slide, x, y, w, ch, label, body, **kw)
    return y


def chip(slide, x, y, w, h, title, sub, fill, tcolor=None):
    """A labelled box for pipeline stages. `sub` may contain '\\n' for line breaks.
    If `tcolor` is None the text colour is auto-picked (white or dark ink) for the better
    contrast against `fill` — so a chip on a light accent (gold/teal) gets dark text
    instead of unreadable white. Pass `tcolor` explicitly to override."""
    if tcolor is None:
        tcolor = WHITE if contrast_ratio(WHITE, fill) >= contrast_ratio(DEEP, fill) else DEEP
    box(slide, x, y, w, h, fill=fill, round=True)
    runs = [[(title, 14, tcolor, True, False)]]
    if sub:
        for line in sub.split("\n"):
            runs.append([(line, 10.5, tcolor, False, False)])
    # generous side padding so text never crowds the rounded edge
    text(slide, x + 0.13, y, w - 0.26, h, runs, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, space_after=1, line_spacing=0.98)


def modbox(slide, x, y, w, h, role, fname, fill, tcolor=None, check=False):
    """Module box for a code/architecture diagram: big role word + mono filename.
    `tcolor=None` auto-picks white/dark ink for contrast against `fill` (see chip)."""
    if tcolor is None:
        tcolor = WHITE if contrast_ratio(WHITE, fill) >= contrast_ratio(DEEP, fill) else DEEP
    box(slide, x, y, w, h, fill=fill, round=True)
    role_runs = [[(line, 16, tcolor, True, False)] for line in role.split("\n")]
    text(slide, x + 0.05, y + 0.12, w - 0.1, 0.55, role_runs, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, space_after=0, line_spacing=0.92)
    text(slide, x + 0.05, y + h - 0.32, w - 0.1, 0.3, [[(fname, 9.5, tcolor, False, False, MONO)]],
         align=PP_ALIGN.CENTER, space_after=0)
    if check:
        box(slide, x + w - 0.34, y - 0.12, 0.24, 0.24, fill=TEAL)
        text(slide, x + w - 0.34, y - 0.16, 0.24, 0.28, [[("✓", 12, WHITE, True, False)]],
             align=PP_ALIGN.CENTER, space_after=0)


# ============================================================= equations
def equation_png(latex_lines, out_path, color="FFFFFF", fontsize=28, dpi=300, mathfont="cm"):
    """Render LaTeX-style math lines to a transparent PNG (proper italics, \\odot,
    real subscripts/superscripts, fractions, Greek...) for a genuinely FORMAL look —
    this is the PREFERRED way to put equations on a slide. The ASCII eq_par() below is
    only a quick fallback; baseline-shifted ASCII never looks as good as real typeset
    math, so reach for equation_png whenever the audience will read the formula.

    Pass mathtext strings, e.g. r"\\hat{x} = \\mathrm{arg\\,min}_{x}\\,\\|Ax-y\\|_2^2 +
    \\lambda R(x)". Returns (w_px, h_px); place with add_picture, then scale to a target
    HEIGHT in inches (height = target_h; width = target_h * w_px/h_px) so glyph size is
    consistent across slides. Lazy-imports matplotlib.

    `mathfont` picks the math typeface (matplotlib mathtext.fontset):
      'cm'        — Computer Modern, the classic LaTeX look (default; formal & elegant)
      'stixsans' / 'dejavusans' — upright SANS math, to sit better next to a sans deck
      'stix'      — Times-like serif math
    Pick 'cm' for an academic/defense feel; a sans set to match a crisp corporate deck.
    `color` is an RRGGBB hex string (a leading '#' is tolerated; e.g. '202A37' for dark
    text on a light deck, 'FFFFFF' for light text on a dark panel).

    mathtext quirks (it is NOT full LaTeX — some control words differ, and older matplotlib
    is stricter, so prefer the safe forms below and you won't hit version differences):
      • use \\leq \\geq \\neq \\times (NOT \\le \\ge \\ne — these reliably raise ParseException);
      • write upright text as \\mathrm{...} (don't rely on \\text{}); use \\, \\; \\ for
        spacing inside it (e.g. \\mathrm{arg\\,min});
      • \\| gives the norm bars; \\hat \\mathcal \\Psi \\lambda \\epsilon \\Delta all work;
      • keep prose annotations OUT of the math (render them as a separate deck-font label),
        so the PNG stays pure math and font-independent."""
    import os
    import tempfile
    if not os.environ.get("MPLCONFIGDIR"):
        default = os.path.join(os.path.expanduser("~"), ".matplotlib")
        if not (os.path.isdir(default) and os.access(default, os.W_OK)):
            path = os.path.join(tempfile.gettempdir(), "slide-maker-matplotlib")
            os.makedirs(path, exist_ok=True)
            os.environ["MPLCONFIGDIR"] = path
    import matplotlib; matplotlib.use("Agg")
    matplotlib.rcParams["mathtext.fontset"] = mathfont   # math typeface (see docstring)
    import matplotlib.pyplot as plt
    from PIL import Image
    n = len(latex_lines)
    fig = plt.figure(figsize=(8, 0.66 * n + 0.15)); fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    col = "#" + color.lstrip("#")   # tolerate a leading '#' (a natural mistake)
    for i, ln in enumerate(latex_lines):
        m = ln if ln.strip().startswith("$") else f"${ln}$"   # math mode
        ax.text(0.01, 1 - (i + 0.5) / n, m, color=col, fontsize=fontsize, va="center")
    fig.savefig(out_path, dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return Image.open(out_path).size


def hrule(slide, x, y, w, color=MUTE, weight=0.012):
    """A thin horizontal rule — for real table lines / separators."""
    return box(slide, x, y, w, weight, fill=color)


# ================================================================= tables & code
def _hex(c):
    return c if isinstance(c, str) else str(c)   # RGBColor.__str__ -> 'RRGGBB'

def _clear_table_style(tbl):
    """Strip PowerPoint's default banded-blue table theme so WE control every fill and
    rule (the default theme looks nothing like the deck). Sets the built-in 'No Style,
    No Grid' style and turns off first-row/banding emphasis."""
    NO_STYLE = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
    el = tbl._tbl
    tblPr = el.find(qn('a:tblPr'))
    if tblPr is None:
        tblPr = el.makeelement(qn('a:tblPr'), {}); el.insert(0, tblPr)
    tblPr.set('firstRow', '0'); tblPr.set('bandRow', '0')
    sid = tblPr.find(qn('a:tableStyleId'))
    if sid is None:
        sid = tblPr.makeelement(qn('a:tableStyleId'), {}); tblPr.append(sid)
    sid.text = NO_STYLE

_FILLISH = {qn('a:noFill'), qn('a:solidFill'), qn('a:gradFill'), qn('a:blipFill'),
            qn('a:pattFill'), qn('a:grpFill'), qn('a:cell3D'), qn('a:headers')}

def _cell_rules(cell, top=None, bottom=None):
    """Add booktabs horizontal rules to a table cell. top/bottom = (color, weight_pt) or
    None. Inserts <a:lnT>/<a:lnB> in the correct schema position (before the fill)."""
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
        for old in tcPr.findall(qn(tag)):
            tcPr.remove(old)
    anchor = next((ch for ch in tcPr if ch.tag in _FILLISH), None)
    def make(tag, spec):
        color, w = spec
        ln = tcPr.makeelement(qn(tag), {'w': str(int(w * 12700)), 'cap': 'flat',
                                        'cmpd': 'sng', 'algn': 'ctr'})
        sf = ln.makeelement(qn('a:solidFill'), {})
        sf.append(ln.makeelement(qn('a:srgbClr'), {'val': _hex(color)}))
        ln.append(sf)
        return ln
    for tag, spec in (('a:lnT', top), ('a:lnB', bottom)):   # lnT before lnB (schema order)
        if spec is None:
            continue
        ln = make(tag, spec)
        (anchor.addprevious(ln) if anchor is not None else tcPr.append(ln))


def table(slide, x, y, w, rows, col_w=None, header=True, highlight=None,
          numeric_cols=None, size=13, row_h=0.34, head_c=DEEP, body_c=SLATE,
          rule_c=MUTE, hi_fill=TINT, hi_c=MAGENTA, font=None):
    """A clean booktabs-style data table — for a dense comparison a chart can't carry
    (many methods × many metrics). `rows` = list of rows of cell strings; row 0 is the
    header when header=True.

    Foreground the comparison the AUTHORS make (see step 1): pass `highlight=<i>` (0-based
    over the BODY rows) to bold + tint the proposed method's row, so the eye lands on the
    one row that matters — a results table exists to make ONE comparison obvious, not to be
    read cell by cell. `numeric_cols` = column indices to right-align (numbers read better
    right-aligned). `col_w` = column widths in inches (defaults to an equal split of `w`).

    Styled with NO PowerPoint theme — no banded blue, no gridlines: just a top rule, a rule
    under the header, and a bottom rule, so it reads like a paper table. Returns the bottom
    y so the caller keeps a GUTTER below it.

    NOTE: on a *presented* slide keep cells terse and highlight one row — it's a slide, not a
    spreadsheet. A **read-alone reference / appendix** table can legitimately be denser (more rows,
    smaller `row_h`, per-column rules) since the reader studies it without a narrator. A cell long
    enough to wrap past `row_h` will grow the row, so verify the render. For a *trend*, prefer a chart
    (`equation_png`/matplotlib or a dedicated figure-making workflow, if available);
    a table is for exact values."""
    ncol = max(len(r) for r in rows)
    nrow = len(rows)
    col_w = col_w or [w / ncol] * ncol
    h = row_h * nrow
    tbl = slide.shapes.add_table(nrow, ncol, Inches(x), Inches(y), Inches(w), Inches(h)).table
    _clear_table_style(tbl)
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    numeric = set(numeric_cols or [])
    hi_row = (highlight + (1 if header else 0)) if highlight is not None else None
    for i in range(nrow):
        tbl.rows[i].height = Inches(row_h)
        is_head = header and i == 0
        is_hi = (i == hi_row)
        for j in range(ncol):
            cell = tbl.cell(i, j)
            cell.text = rows[i][j] if j < len(rows[i]) else ""
            cell.margin_left = cell.margin_right = Pt(7)
            cell.margin_top = cell.margin_bottom = Pt(2)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if is_hi:
                cell.fill.solid(); cell.fill.fore_color.rgb = hi_fill
            else:
                cell.fill.background()
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT if j in numeric else PP_ALIGN.LEFT
            col = head_c if is_head else (hi_c if is_hi else body_c)
            for r in p.runs:
                set_font(r, size, col, bold=is_head or is_hi, font=font)
    # booktabs rules: \toprule, \midrule (under header), \bottomrule — nothing else
    spec = {}
    for j in range(ncol):
        spec.setdefault((0, j), {})['top'] = (head_c, 1.4)
        if header and nrow > 1:
            spec.setdefault((0, j), {})['bottom'] = (rule_c, 0.8)
        spec.setdefault((nrow - 1, j), {})['bottom'] = (head_c, 1.4)
    for (i, j), s in spec.items():
        _cell_rules(tbl.cell(i, j), top=s.get('top'), bottom=s.get('bottom'))
    return y + h


def code_block(slide, x, y, w, code, size=12, lang=None, highlight_lines=None,
               panel=DEEP, text_c=PALE, hi_c=WHITE, hi_fill=None, line_numbers=False,
               pad=0.16, line_h=None):
    """A monospace code panel — preserved indentation, optional per-line highlighting.
    `code` = a string with real newlines (or a list of lines); leading/trailing blank
    lines are trimmed. Renders on a dark rounded panel by default (for a LIGHT deck pass
    panel=LIGHT or a tint + text_c=DEEP). `highlight_lines` = 1-based line numbers to
    emphasise (brighter, bold; pass hi_fill=<color> for a highlight band too).

    Keep snippets SHORT — a slide shows the 5 lines that carry the idea, not a file; elide
    the rest with '# ...'. Uses MONO so indentation and columns line up. Returns bottom y."""
    lines = code.split("\n") if isinstance(code, str) else list(code)
    lines = [ln.expandtabs(4) for ln in lines]   # tabs -> spaces so indentation is real
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        lines = [""]
    hl = set(highlight_lines or [])
    line_h = line_h or size / 72.0 * 1.42
    gutter_w = (size / 72.0 * 0.62 * (len(str(len(lines))) + 1)) if line_numbers else 0.0
    h = pad * 2 + line_h * len(lines)
    box(slide, x, y, w, h, fill=panel, round=True)
    if hi_fill is not None:
        for k in hl:
            if 1 <= k <= len(lines):
                box(slide, x + 0.05, y + pad + (k - 1) * line_h - line_h * 0.06,
                    w - 0.10, line_h, fill=hi_fill)
    runs = [[(ln if ln.strip() else " ", size, (hi_c if k in hl else text_c),
              k in hl, False, MONO)]
            for k, ln in enumerate(lines, start=1)]
    tb = text(slide, x + pad + gutter_w, y + pad, w - 2 * pad - gutter_w, h, runs,
              space_after=0, line_spacing=1.0)
    tb.text_frame.word_wrap = False   # a long line clips instead of wrapping (which would
    #                                   break indentation and the height estimate) — the
    #                                   docstring's "keep snippets short" is the real fix.
    if line_numbers:
        nruns = [[(str(k), size, text_c, False, False, MONO)] for k in range(1, len(lines) + 1)]
        text(slide, x + pad - 0.02, y + pad, gutter_w, h, nruns,
             align=PP_ALIGN.RIGHT, space_after=0, line_spacing=1.0)
    if lang:
        text(slide, x + w - 1.3, y + 0.06, 1.2, 0.22,
             [[(lang, 9, text_c, False, False, MONO)]], align=PP_ALIGN.RIGHT, space_after=0)
    return y + h


# ----- lightweight ASCII equation fallback (editable text; use when matplotlib
#       isn't available or the equation is trivial) -----
N   = lambda t: (t, 'n')      # normal run
SUP = lambda t: (t, 'sup')    # superscript run
SUB = lambda t: (t, 'sub')    # subscript run

def eq_par(tf, tokens, base, color, first=False, italic=False, font=None):
    """One equation line inside a text frame. tokens = list of N()/SUP()/SUB().
    Uses real baseline shifts + ASCII letters, so it renders crisply in any font.
    `font` resolves to EQFONT at call time (so reassigning deckkit.EQFONT re-themes math).
    Example:  eq_par(tf, [N('A'),SUP('H'),N(' y = '),N('D'),SUB('r'),SUP('T')], 14, WHITE)"""
    font = font or EQFONT          # resolve at call time so re-theming EQFONT takes effect
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(2); p.space_before = Pt(0); p.line_spacing = 1.12
    p.alignment = PP_ALIGN.LEFT
    for txt, kind in tokens:
        r = p.add_run(); r.text = txt
        size = base if kind == 'n' else base * 0.62
        set_font(r, size, color, italic=italic, font=font)
        if kind in ('sup', 'sub'):
            r._r.get_or_add_rPr().set('baseline', '30000' if kind == 'sup' else '-22000')
    return p


# ================================================================ template reuse
def open_template(path):
    """Open the user's deck and delete its slides while KEEPING masters/layouts.
    A template's branding (header band, logos, footer) lives on the layouts, so new
    slides added afterwards inherit all of it automatically. Dropping the slide
    relationships also prunes the old slides' heavy media (e.g. GIFs) on save."""
    prs = Presentation(path)
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        prs.part.drop_rel(sldId.get(qn('r:id')))
        sldIdLst.remove(sldId)
    return prs


def drop_placeholders(slide, keep_idx):
    """Remove inherited placeholders whose idx is not in keep_idx (set)."""
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx not in keep_idx:
            ph._element.getparent().remove(ph._element)


def content_slide(prs, layout_idx, title_txt, size=23, footer="", date="",
                  title_color=WHITE, body_idx=1):
    """Add a content slide on the template's 'Title and Content with Logo' layout.
    Sets a WHITE title on the band, removes the empty body placeholder, fills the
    footer/date placeholders. Returns the slide for you to draw on.

    NOTE: layout_idx and placeholder types are template-specific — confirm them by
    inspecting the template once (inspect_template.py) and save them to the template's
    profile.md in the active template registry, e.g. ~/.codex/slide-templates/<name>/
    for Codex or ~/.claude/slide-templates/<name>/ for Claude Code."""
    s = prs.slides.add_slide(prs.slide_layouts[layout_idx])
    tf = s.shapes.title.text_frame; tf.text = title_txt
    for r in tf.paragraphs[0].runs:
        set_font(r, size, title_color, bold=True)
    # remove the empty body content placeholder so it doesn't show a prompt
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx == body_idx:
            ph._element.getparent().remove(ph._element)
    # fill footer (type 15) and date (type 16) placeholders if present
    for ph in list(s.placeholders):
        t = ph.placeholder_format.type
        if t == 15 and footer:
            ph.text = footer
            for r in ph.text_frame.paragraphs[0].runs: set_font(r, 9, MUTE)
        elif t == 16 and date:
            ph.text = date
            for r in ph.text_frame.paragraphs[0].runs: set_font(r, 9, MUTE)
    return s


# ===================================== no-template branch (build chrome yourself)
def blank_deck(w_in=10.0, h_in=5.625):
    """A fresh 16:9 deck when the user has NO template to match. Use add_slide() +
    title_bar()/footer() to give it simple, consistent branding you define from
    their brand colors (set the palette constants above) or a clean default."""
    prs = Presentation()
    prs.slide_width = Inches(w_in); prs.slide_height = Inches(h_in)
    return prs


def add_slide(prs):
    """Add a truly blank slide (layout 6) to draw on from scratch."""
    return prs.slides.add_slide(prs.slide_layouts[6])


def _slide_size(slide):
    """Return the slide's real width/height in inches."""
    prs = slide.part.package.presentation_part.presentation
    return prs.slide_width / 914400, prs.slide_height / 914400


def title_bar(slide, title, kicker="", accent=MAGENTA, title_c=DEEP, w_in=None):
    """Lightweight slide chrome for the no-template branch: optional kicker, title,
    and a short accent rule. Pair with footer().

    By default this reads the actual deck width from ``slide`` so it works on
    widescreen templates, custom ``blank_deck(w_in, h_in)`` sizes, and posters.
    Pass ``w_in`` only when deliberately overriding that geometry."""
    if w_in is None:
        w_in, _ = _slide_size(slide)
    if kicker:
        text(slide, 0.55, 0.30, w_in - 1.1, 0.3, [[(kicker.upper(), 11, BLUE, True, False)]], space_after=0)
        ty = 0.54
    else:
        ty = 0.40
    tb = text(slide, 0.55, ty, w_in - 1.1, 0.7,
              [[(title, 26, title_c, True, False, DISPLAY or FONT)]], space_after=0)  # title gets the DISPLAY face
    if EADISPLAY:                                    # ...and a distinct CJK display face if set
        for p in tb.text_frame.paragraphs:
            for r in p.runs:
                _apply_ea(r, EADISPLAY)
    box(slide, 0.57, ty + 0.62, 1.1, 0.045, fill=accent)


def footer(slide, tag="", page=None, w_in=None, h_in=None):
    """Footer tag (left) + optional page number (right) for the no-template branch.

    Defaults to the actual deck size, so custom-sized decks don't end up with a
    page number stranded at the old 10x5.625 coordinate."""
    if w_in is None or h_in is None:
        sw, sh = _slide_size(slide)
        w_in = sw if w_in is None else w_in
        h_in = sh if h_in is None else h_in
    if tag:
        text(slide, 0.55, h_in - 0.35, 6.0, 0.3, [[(tag, 8, MUTE, False, False)]], space_after=0)
    if page is not None:
        text(slide, w_in - 1.0, h_in - 0.35, 0.6, 0.3,
             [[(str(page), 9, MUTE, True, False)]], align=PP_ALIGN.RIGHT, space_after=0)


# ===================================================================== notes
def speaker_notes(slide, notes):
    """Attach speaker notes — the SPOKEN script — to a slide, off the visible canvas.
    The slide should show the phrase; the full sentences the presenter says live here.
    Notes do NOT render to the slide or the PNG (the critic won't see them); they appear
    in PowerPoint/Keynote Presenter View and print on Notes Pages. This is the right
    place to move full sentences OFF a slide for a talk/defense/lecture the user will
    rehearse — keeping the slide a clean visual aid while preserving the narration."""
    tf = slide.notes_slide.notes_text_frame
    tf.text = notes
    return slide.notes_slide


def alt_text(shape, description):
    """Set a shape's ACCESSIBILITY alt-text (the screen-reader description). Call it after
    add_picture() — and on any informative figure/diagram — so assistive tech can describe
    the visual. Alt-text does NOT render (it won't appear in the PNG or to the pixel
    critic); it lives in PowerPoint's accessibility metadata (the cNvPr 'descr' attribute)
    and shows in the Selection/Accessibility pane. Give a one-line factual description,
    e.g. alt_text(pic, "ROC curve: proposed method (pink) above baseline (grey)")."""
    cNvPr = shape._element.find(".//" + qn("p:cNvPr"))
    if cNvPr is not None:
        cNvPr.set("descr", description)
        if not cNvPr.get("title"):
            cNvPr.set("title", description[:120])
    return shape
