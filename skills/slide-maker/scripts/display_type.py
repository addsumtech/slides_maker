#!/usr/bin/env python3
"""display_type — display typography a register can build its voice from.

stacked   a headline set one line per box, each line sized to fill the same measure
two_tone  named words of a headline in a second colour
outlined  hollow display marks (section numbers, big figures) — a PICTURE: a native hollow run
          (<a:ln> + <a:noFill/>) renders FILLED in LibreOffice (verified 2026-10-03), so the render and
          PowerPoint would disagree. Pillow draws the strokes from the installed font file.
"""
from __future__ import annotations

import hashlib
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import deckkit as dk  # noqa: E402

_LINE_H = 1.12


def _italic_file(face, bold):
    """The installed ITALIC file of `face`, or None (matplotlib's own lookup, no fallback)."""
    try:
        from matplotlib import font_manager as fm
        f = fm.findfont(fm.FontProperties(family=face, style="italic", weight="bold" if bold else "normal"),
                        fallback_to_default=False)
        return f if "italic" in f.lower() or "oblique" in f.lower() else None
    except Exception:
        return None


_GW_FONTS = {}     # (file, face index, px) -> a loaded font: loading it was half the cost of every visual-language build
_GW_WIDTHS = {}    # (text, size, face, bold, italic) -> width; the same words are measured again and again while a
#                    layout shrinks and tries its alternatives (profiled 2026-10-09: 245k font loads in 217s)
_GW_FACES = {}     # (face, bold, italic) -> [(file, face index), ...]


def _faces_for(face, bold, italic):
    """The (file, face index) pairs a run of `face` at this weight and style is measured in — deckkit's one choice
    (dk._font_face: the family's faces across every file that holds them, chosen by their OS/2 metadata), never a
    second rule. 🔴 macOS ships whole families as ONE .ttc collection and Pillow opens face 0 unless told otherwise:
    measured that way, every bold run of Rockwell, Chalkboard SE, Helvetica Neue … read at the REGULAR width (a bold
    "45" in Rockwell, 2.444in for 2.625, broke over two lines of a timer dial — recipe, 2026-10-22) and every run of
    Avenir Next read at its BOLD width (face 0).

    Italic: the family's own italic faces, chosen by the same rule (dk._choose_face). A family without one is slanted
    by the renderer, which keeps the upright advances (measured 2026-10-22: Chalkboard SE and American Typewriter
    italic set every glyph origin where the upright does) — so the upright face measures it. A BOLD italic the family
    lacks may be drawn either way — LibreOffice set Didot's as the slanted Bold, Futura's as its Medium Italic — so
    both faces are returned and the wider one is used."""
    key = (face, bool(bold), bool(italic))
    if key in _GW_FACES:
        return _GW_FACES[key]
    up = dk._font_face(face, bool(bold)) if face else None
    out = [up] if up else []
    if up and italic:
        fam = dk._norm_family(face)
        files = {str(p_) for p_ in (up[0], (dk._font_face(face, not bold) or (None,))[0],
                                    _italic_file(face, False), _italic_file(face, True)) if p_}
        try:
            from matplotlib import font_manager as fm
            files |= {str(e.fname) for e in fm.fontManager.ttflist if dk._norm_family(e.name) == fam}
        except ImportError:
            pass
        ital = [dict(f_, path=p_) for p_ in sorted(files) for f_ in dk._face_meta(p_)
                if f_["italic"] and fam in f_["families"]]
        if ital:
            pick = dk._choose_face(ital, bool(bold))
            out = [(pick["path"], pick["i"])]
            if bold and pick is dk._choose_face(ital, False):      # no heavier italic: the renderer may slant the bold
                out.append(up)
    _GW_FACES[key] = out
    return out


def _glyph_width(text, size, face, bold, italic=False):
    """The rendered width of `text` (inches) from the font file's own advances, in the face of the family LibreOffice
    draws this weight and style in (`_faces_for`). dk.measure_text breaks only at spaces, so it calls a too-wide
    single word "one line" — LibreOffice breaks it mid-word (measured: "BROKEN" at 199.6pt = 8.68in in a 4.94in box,
    rendered "BRO / KEN"). Memoised: a pure function of its arguments."""
    key = (text, size, face, bool(bold), bool(italic))
    if key in _GW_WIDTHS:
        return _GW_WIDTHS[key]
    from PIL import ImageFont
    faces = _faces_for(face, bold, italic)
    if not faces:
        return None
    w = 0.0
    for path, idx in faces:
        fk = (str(path), idx, max(8, int(size * 10)))
        fnt = _GW_FONTS.get(fk)
        if fnt is None:
            fnt = _GW_FONTS[fk] = ImageFont.truetype(fk[0], fk[2], index=idx, layout_engine=ImageFont.Layout.BASIC)
        # Synthetic bold / slant does NOT change advance widths in the renderer (measured 2026-10-03: Impact
        # 72pt regular vs bold = 913px both; Hiragino Sans GB +0.4%), so no allowance is added for them.
        w = max(w, fnt.getlength(text) / 10.0 / 72.0)
    if len(_GW_WIDTHS) > 400000:
        _GW_WIDTHS.clear()
    _GW_WIDTHS[key] = w
    return w


# ── one line of mixed script, as LibreOffice sets it ─────────────────────────────────────────────────────────────────
# Measured 2026-10-22 (a PDF of dk.text() runs, glyph origins read back with PyMuPDF): LibreOffice gives every character
# a SCRIPT and sets it in that script's face — a CJK character in the run's <a:ea> face, a letter or digit in its
# <a:latin> face — and a space, or a mark of no script (“ ” — … → ①), takes the script of the character BEFORE it (at
# the start, of the first one that has a script): the space in "用 GPT" is set in Songti SC, the one in "GPT-5 做" in
# Times New Roman. Then, at every change between East-Asian and Western text, it adds AUTOSPACE — 0.237-0.242 em at
# 9-72pt, the same for Hiragino Sans GB, Songti SC, PingFang SC, Hiragino Mincho, Hiragino Sans and Apple SD Gothic Neo
# against Arial, Times New Roman, Didot, Avenir Next, Georgia and Helvetica Neue. Measured without either rule (the
# Latin part in the Latin face, the CJK part in the East-Asian face, nothing between), "用 GPT-5 做 3 件事" (31.5pt
# bold, four changes) read 3.67in where LibreOffice set 4.04in: planned as one line of a 3.79in measure, its last
# character rendered alone on a second line (calendar, 2026-10-22). On 280 generated mixed lines (zh/ja/ko, 7 face
# pairs, 12-31.5pt) this model is within -0.007..+0.30 em of the render; the old one was up to 1.25 em under.
AUTOSPACE_EM = 0.25          # the measured 0.24 em, never under it


def script_class(ch):
    """'a' (East-Asian), 'l' (everything else that has a script) or None (WEAK: it takes its neighbour's script) — the
    classes LibreOffice's i18npool gives (BreakIteratorImpl::getScriptClass): a space and a no-break space are weak;
    Latin-1 … spacing modifiers, Greek … Armenian, Georgian and Latin Extended Additional are Latin (so are the ASCII
    digits and punctuation — "3" and "-" were set in the Latin face); CJK radicals … Hangul syllables, compatibility
    ideographs and forms and the half/full-width forms are East-Asian; Number Forms, and every other character of no
    script (general punctuation, symbols, arrows, enclosed numbers), are weak."""
    o = ord(ch)
    if o in (0x20, 0xA0, 0x01, 0x02, 0x2C7, 0x2CA, 0x2CB, 0x2D9):
        return None
    if o < 0x300 or 0x370 <= o <= 0x58F or 0x10A0 <= o <= 0x10FF or 0x1E00 <= o <= 0x1FFF:
        return "l"
    if dk._has_cjk(ch) or 0x2E80 <= o <= 0xD7AF or 0xFE30 <= o <= 0xFE4F:
        return "a"
    if 0x2150 <= o <= 0x218F:
        return None
    import unicodedata
    return None if unicodedata.category(ch)[0] in "PSZNMC" else "l"


def script_runs(text):
    """`text` cut where its script changes, weak characters given to the script before them (the first script, at
    the start; Latin when nothing has one): [(segment, 'a' | 'l'), ...]."""
    cls = [script_class(c) for c in text]
    cur = next((c for c in cls if c), "l")
    out = []
    for ch, c in zip(text, cls):
        cur = c or cur
        if out and out[-1][1] == cur:
            out[-1][0] += ch
        else:
            out.append([ch, cur])
    return [(s_, c_) for s_, c_ in out]


# ── figures in a lining face ─────────────────────────────────────────────────────────────────────────────────────────
# A run whose face has OLD-STYLE figures (Didot, Hoefler Text, Georgia …) is drawn with every figure sequence cut out into
# a run of a LINING face (visual_languages.Kit.runs; deckkit.numeral_face — Times New Roman), so the figures never bob.
# Those figures must be MEASURED in the lining face too: Times New Roman's are 23% wider than Didot's ("12" at 40pt,
# 0.453in measured, 0.556in drawn) and narrower than Georgia's, and a figure measured in Didot and drawn in Times New
# Roman broke "21 / 4" and "1:25 / 0" in their boxes (stainedglass, airmail, rendered 2026-10-23). One cut, shared by the
# drawing and every measure.
FIGURE_RUN = re.compile(r"(\d(?:[\d,.:/%–-]*\d)?%?)")


def figure_runs(text, face, figures=None):
    """`text` as [(part, face)]: every figure sequence (FIGURE_RUN, with its own separators: "1,250", "3.5%", "9:30") in
    `figures` — the lining face the run sets its figures in — and the rest in `face`. Without `figures`, or without a
    digit: [(text, face)]."""
    if not figures or not any(c.isdigit() for c in text):
        return [(text, face)]
    return [(p_, figures if p_[0].isdigit() else face) for p_ in FIGURE_RUN.split(text) if p_]


def figures_width(text, size, face, bold, italic=False, figures=None):
    """The width (in) of Latin `text` drawn as `figure_runs` cuts it: each part in its own face (no kerning across the
    cut — LibreOffice sets them as separate runs)."""
    return sum(_glyph_width(p_, size, f_, bold, italic) or 0.0 for p_, f_ in figure_runs(text, face, figures))


def line_width(text, size, latin, ea, bold, italic=False, figures=None):
    """The width (in) LibreOffice sets ONE line of `text` in (see AUTOSPACE_EM): each script run in its own face —
    East-Asian runs in `ea`, the rest in `latin` (italic applies to those only: CJK has none) — plus the autospace at
    every change of script. `figures`: the lining face the run's figure sequences are drawn in (see `figure_runs`),
    when they are cut out of an old-style `latin`. Without an `ea` face (or where it is not installed and its stand-in
    has no CJK glyphs), a CJK character counts one em. The width a line takes, not where it may break: a caller
    breaking lines measures each candidate line with it."""
    runs = script_runs(text)
    em = size / 72.0
    total = 0.0
    for seg, c in runs:
        if c == "l":
            total += figures_width(seg, size, latin, bold, italic, figures)
            continue
        rest = "".join(ch for ch in seg if not dk._has_cjk(ch))
        floor = (len(seg) - len(rest)) * em + ((_glyph_width(rest, size, ea or latin, bold) or 0.0) if rest else 0.0)
        gw = _glyph_width(seg, size, ea, bold) if ea and dk._face_covers(ea, seg.strip()) else None
        total += gw if gw is not None else floor
    return total + AUTOSPACE_EM * em * (len(runs) - 1)


def em_width(text, size, latin, bold):
    """The width (in) a line reads at in the LINTS' model: one em per CJK character, every other character in the
    Latin face (lint_deck._text_w and deckkit._measure_lines both count a CJK character as one em)."""
    em = size / 72.0
    total, run = 0.0, ""
    for ch in text:
        if dk._has_cjk(ch):
            total += ((_glyph_width(run, size, latin, bold) or 0.62 * em * len(run)) if run else 0.0) + em
            run = ""
        else:
            run += ch
    return total + ((_glyph_width(run, size, latin, bold) or 0.62 * em * len(run)) if run else 0.0)


def _one_line_size(text, w, face, bold, lo, hi):
    """The largest point size (lo..hi) at which `text` stays on one line of inner width `w`: its real glyph
    width fits (and, as a second guard, measure_text sees one line)."""
    def fits(sz):
        gw = _glyph_width(text, sz, face, bold)
        if gw is not None and gw > w:
            return False
        return dk.measure_text([(text, bold)], w, sz, font=face) <= sz * _LINE_H * 1.3 / 72.0
    if not fits(lo):
        return None
    while hi - lo > 0.5:
        mid = (lo + hi) / 2.0
        lo, hi = (mid, hi) if fits(mid) else (lo, mid)
    return round(lo, 1)


def stacked(slide, x, y, w, lines, *, color, face=None, ea=None, bold=True, max_size=120, min_size=18, gap=0.04):
    """ONE headline set one line per paragraph, each line sized to fill the measure `w` on a single line.
    One textbox, so lint and PowerPoint read it as one block (separate boxes read as a headline crowded by
    the block under it). Returns (textbox, bottom_y); the box height is the sum of each line's rendered
    height (dk._LINT_LINE_H x size — the LibreOffice line box) plus `gap` between lines."""
    paras, height = [], 0.04
    for line in lines:
        # fit to the box's INNER width (text() insets 0.028in a side) less 2% — fitting the full width
        # let a line wrap in the render and in lint's model, and the headline grew into the next block
        sz = _one_line_size(line, (w - 0.056) * 0.98, face or ea, bold, float(min_size), float(max_size))
        if sz is None:
            raise ValueError("stacked(): {!r} does not fit on one line of {:.2f}in even at min_size {}pt — "
                             "shorten it or widen the box".format(line, w, min_size))
        paras.append([(line, sz, color, bold, False, face, ea)])
        height += sz * dk._LINT_LINE_H / 72.0
    height += gap * max(0, len(lines) - 1)
    box = dk.text(slide, x, y, w, height, paras, space_after=gap * 72.0, line_spacing=1.0)
    return box, y + height


def two_tone(slide, x, y, w, h, text, accent_words, *, size, color, accent, face=None, ea=None, bold=True):
    spans, i = [], 0
    marks = sorted({(text.find(a), a) for a in accent_words if a and text.find(a) >= 0})
    for pos, a in marks:
        if pos < i:
            continue
        if pos > i:
            spans.append((text[i:pos], color))
        spans.append((a, accent))
        i = pos + len(a)
    if i < len(text):
        spans.append((text[i:], color))
    return dk.text(slide, x, y, w, h, [[(t, size, c, bold, False, face, ea) for t, c in spans]])


_CMAP_CACHE = {}


def covers(face, text):
    """True when the INSTALLED file of `face` has a glyph for every non-space character of `text` (its cmap).
    A face without the glyphs draws hollow boxes in a raster — Impact has no CJK, so a collage "三成" came
    out as tofu with every gate green (final review, 2026-10-04)."""
    return dk._face_covers(face, text) is True          # one cmap reader, in deckkit; not installed = False


def outlined(slide, x, y, w, h, text, *, color, face="Arial Black", stroke=None):
    from PIL import Image, ImageDraw, ImageFont
    if not text or len(text) > 6:
        raise ValueError("outlined(): for short display marks only (1-6 characters), got {!r}".format(text))
    if dk._font_substituted(face):
        raise ValueError("outlined(): face {!r} is not installed here — pass an installed face".format(face))
    if not covers(face, text):
        raise ValueError("outlined(): face {!r} has no glyph for {!r} — it would draw boxes; set it as a text run "
                         "instead".format(face, "".join(sorted({c for c in text if not c.isspace() and not covers(face, c)}))))
    c = color.lstrip("#")
    rgb = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    font = ImageFont.truetype(str(dk._font_file(face)), 600, layout_engine=ImageFont.Layout.BASIC)
    sw = stroke or max(4, int(600 * 0.03))
    bb = font.getbbox(text, stroke_width=sw)
    im = Image.new("RGBA", (bb[2] - bb[0] + 2 * sw, bb[3] - bb[1] + 2 * sw), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((sw - bb[0], sw - bb[1]), text, font=font, fill=(0, 0, 0, 0),
                            stroke_width=sw, stroke_fill=rgb + (255,))
    key = hashlib.sha1("{}|{}|{}|{}".format(text, face, c, sw).encode()).hexdigest()[:16]
    d = Path(tempfile.gettempdir()) / "slide-maker-outlined"
    d.mkdir(parents=True, exist_ok=True)
    out = d / "outlined-{}.png".format(key)
    im.save(out)
    ar = im.width / float(im.height)
    pw, ph = (h * ar, h) if h * ar <= w else (w, w / ar)     # its own aspect, anchored top-left
    return dk.picture(slide, str(out), x, y, pw, ph, fit="contain", alt=text)
