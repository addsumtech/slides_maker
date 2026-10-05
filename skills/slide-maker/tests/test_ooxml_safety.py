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

# 4b. the angle rule follows the schema: ST_PositiveFixedAngle attributes (shadow/reflection dir, gradient ang)
#     must be in range; signed types (xfrm rot, arcTo stAng/swAng — ST_Angle/ST_AdjAngle) may be negative
def reflection(s):
    b = dk.box(s, 1, 1, 2, 2, fill="FFFFFF")
    b._element.spPr.append(etree.fromstring('<a:effectLst xmlns:a="%s"><a:reflection blurRad="6350" stA="50000" '
                                            'endA="300" dist="0" dir="-5400000" sy="-100000" algn="bl" '
                                            'rotWithShape="0"/></a:effectLst>' % A))
p, _ = deck(reflection)
check(any("reflection" in m for _n, m in ox.xml_findings(str(p))), "a negative reflection dir is a finding")
def arc(s):
    import ornaments as orn
    orn._shape(s, 1, 1, 2, 2, '<a:path w="100000" h="100000"><a:moveTo><a:pt x="0" y="50000"/></a:moveTo>'
                              '<a:arcTo wR="50000" hR="50000" stAng="10800000" swAng="-5400000"/></a:path>', fill="FFFFFF")
p, _ = deck(arc)
check(ox.xml_findings(str(p)) == [], "a counter-clockwise arc (negative swAng, a signed type) is valid: {}".format(
    ox.xml_findings(str(p))))
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
