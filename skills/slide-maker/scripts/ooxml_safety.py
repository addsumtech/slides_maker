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
# ST_PositiveFixedAngle (0..21599999, 60000ths of a degree) — PowerPoint repairs a value outside it. NOT listed:
# xfrm `rot` (ST_Angle) and arcTo `stAng`/`swAng` (ST_AdjAngle) are SIGNED types; a negative arc sweep is valid.
_ANGLE = {"dir", "ang", "fadeDir"}
_ANGLE_TAGS = ("outerShdw", "innerShdw", "prstShdw", "reflection", "lin")
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
                    if att in _ANGLE and tag in _ANGLE_TAGS and not 0 <= v < 21600000:
                        add("{} {}={} outside 0..21599999".format(tag, att, v))
                    elif att in _POS_COORD and tag in ("outerShdw", "innerShdw", "prstShdw", "reflection", "glow",
                                                       "softEdge") and v < 0:
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
                out.append((n, "BEYOND THE PAGE: shape {!r} reaches {:.2f}in past the slide edge — PowerPoint shows "
                               "it while editing; clip it to the page, or declare a deliberate bleed with "
                               "deckkit.bleed_intent(shape, '<why>')".format(name.split(":", 1)[0] or "?", over)))
    return out
