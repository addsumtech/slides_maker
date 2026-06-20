#!/usr/bin/env python3
"""deckkit — reusable helpers for building clean slides with python-pptx.

General-purpose: works whether you build ON a user's template (open_template) or
from scratch when they have none (blank_deck + title_bar/footer). Import this from
a small per-deck build script rather than copy-pasting primitives every time.
A brand-free worked example lives at references/examples/build_example_generic.py.

Design intent (see references/design-principles.md):
  - terse, few-word points — the slide is a visual aid, not a document
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
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

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
def box(slide, x, y, w, h, fill=None, line=None, line_w=1.0, round=False, corners="all", r=None):
    """A rectangle. `round=True` rounds all four corners (radius = 8% of the shorter side,
    or `r` inches if given). For a colored HEADER BAND sitting on top of a rounded card,
    use `corners='top'` and pass `r=<the card's corner radius in inches>` so the band's
    curve MATCHES the card — a square band over a rounded card (corners poking out) is the
    tell to avoid. `corners='bottom'` rounds the bottom two. (A thin accent strip can
    instead be inset by the radius so its square ends fall on the card's straight edge.)"""
    if not (round or r is not None or corners != "all"):
        t = MSO_SHAPE.RECTANGLE
    elif corners in ("top", "bottom"):
        t = MSO_SHAPE.ROUND_2_SAME_RECTANGLE   # rounds the two top corners (rotate for bottom)
    else:
        t = MSO_SHAPE.ROUNDED_RECTANGLE
    s = slide.shapes.add_shape(t, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None: s.fill.background()
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


def arrow(slide, x, y, w, h, color=BLUE):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = color
    a.line.fill.background(); a.shadow.inherit = False
    try: a.adjustments[0] = 0.55; a.adjustments[1] = 0.55
    except Exception: pass
    return a


def arrow_label(slide, x, y, w, h, label, color=BLUE, size=9, lab_c=None, box_w=1.3, bold=True):
    """An arrow with its label centred just above it, with a tight gap — so connector
    labels (a verb, a transform name, a step — e.g. 'encode', 'train', 'merge', 'step 2')
    stay centred on the arrow and snug, rather than drifting to one side or floating far
    above it. The label box is centred on the
    arrow's horizontal centre and its bottom sits ~0.04 in above the arrow's top.
    `box_w` is the (transparent) label-box width; shrink it (e.g. 1.2) when the arrow sits
    in a narrow gap between figures so the box can't visually collide. Returns the arrow."""
    lab_c = lab_c or color
    th = size / 72.0 * 1.3
    text(slide, x + w / 2.0 - box_w / 2.0, y - th - 0.04, box_w, th + 0.04,
         [[(label, size, lab_c, bold, False)]], align=PP_ALIGN.CENTER, space_after=0)
    return arrow(slide, x, y, w, h, color=color)


# ====================================================================== images
def picture(slide, path, x, y, w, h, fit="contain", alt=None):
    """Place an image in a frame without distorting it.

    `fit="contain"` shows the whole image inside the frame, letterboxed by whitespace.
    Use it for source figures, charts, screenshots, and anything whose edges/labels matter.
    `fit="cover"` fills the frame and crops evenly from the long dimension. Use it for
    decorative plates, photo panels, and generated atmosphere where edge crop is acceptable.

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
    # auto-grow height so the body never spills outside the box. The label + body share one
    # wrap width; nlines is MEASURED from real glyph metrics (label measured bold) so the
    # box fits the rendered text rather than a chars-per-inch guess.
    nlines = _measure_lines([(label + "  ", True), (body, False)], 12.5, w - 0.44)
    h = max(h, 0.36 + 0.245 * nlines)
    box(slide, x, y, w, h, fill=fill, round=True)
    rad = 0.08 * min(w, h)                                   # inset the accent bar so its square
    box(slide, x, y + rad, 0.07, h - 2 * rad, fill=label_c)  # ends fall on the card's straight edge
    # text box spans the card's full height so MSO_ANCHOR.MIDDLE centres on the card's true
    # centre (y + h/2). A y-offset here with the same height would push the text below centre.
    text(slide, x + 0.24, y, w - 0.44, h,
         [[(label + "  ", 11, label_c, True, False), (body, 12.5, body_c, False, False)]],
         anchor=MSO_ANCHOR.MIDDLE, space_after=0, line_spacing=1.08)
    return y + h   # bottom edge, so callers can keep a margin below


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

    NOTE: keep cells terse — it's a slide, not a spreadsheet. A cell long enough to wrap
    past `row_h` will grow the row, so verify the render. For a *trend*, prefer a chart
    (`equation_png`/matplotlib or the paper-figures skill); a table is for exact values."""
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
    profile.md in ~/.claude/slide-templates/<name>/."""
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


def title_bar(slide, title, kicker="", accent=MAGENTA, title_c=DEEP, w_in=10.0):
    """Lightweight slide chrome for the no-template branch: optional kicker, title,
    and a short accent rule. Pair with footer()."""
    if kicker:
        text(slide, 0.55, 0.30, w_in - 1.1, 0.3, [[(kicker.upper(), 11, BLUE, True, False)]], space_after=0)
        ty = 0.54
    else:
        ty = 0.40
    text(slide, 0.55, ty, w_in - 1.1, 0.7, [[(title, 26, title_c, True, False)]], space_after=0)
    box(slide, 0.57, ty + 0.62, 1.1, 0.045, fill=accent)


def footer(slide, tag="", page=None, w_in=10.0, h_in=5.625):
    """Footer tag (left) + optional page number (right) for the no-template branch."""
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
