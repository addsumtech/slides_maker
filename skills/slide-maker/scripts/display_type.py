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


def _glyph_width(text, size, face, bold, italic=False):
    """The rendered width of `text` (inches) from the font file's own advances. dk.measure_text breaks
    only at spaces, so it calls a too-wide single word "one line" — LibreOffice breaks it mid-word
    (measured: "BROKEN" at 199.6pt = 8.68in in a 4.94in box, rendered "BRO / KEN"). An italic run is
    measured with the face's real italic file when one is installed."""
    from PIL import ImageFont
    f = dk._font_file(face, bold=bold) if face else None
    if f is None:
        return None
    itf = _italic_file(face, bold) if italic else None
    fnt = ImageFont.truetype(str(itf or f), max(8, int(size * 10)))
    # Synthetic bold / slant does NOT change advance widths in the renderer (measured 2026-10-03: Impact
    # 72pt regular vs bold = 913px both; Hiragino Sans GB +0.4%), so no allowance is added for them.
    return fnt.getlength(text) / 10.0 / 72.0


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
    font = ImageFont.truetype(str(dk._font_file(face)), 600)
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
