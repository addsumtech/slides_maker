#!/usr/bin/env python3
"""The P5 native visual languages: interface (产品界面) and wayfinding (导视线路) — registered like the eleven before
them, every page × ground × canvas × script composes, nothing leaves the page or trips PowerPoint, the words only the
caller can give are never invented, and a structure (a route) is drawn only when the caller says the points are ordered."""
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
# Face-precise checks (as test_visual_languages): a Chinese line count is only measurable with the CJK faces the kit
# names. The ubuntu CI runner has none of them — SimSun / Microsoft YaHei resolve to a DejaVu stand-in with no CJK
# glyphs — so those checks record a SKIP there, printed at the end, instead of failing on the stand-in's widths.
FACES_HERE = sys.platform == "darwin" and not any(dk._font_substituted(f) for f in (
    "Songti SC", "Hiragino Sans GB", "Georgia", "Times New Roman", "Arial", "Arial Black", "Trebuchet MS"))
skipped = []
def check_mac(cond, why):
    if FACES_HERE:
        check(cond, why)
    else:
        skipped.append(why)

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
    """The page's visible text boxes (not the off-page title kept for screen readers)."""
    return [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0]
def txt_of(sh):
    """A text box's words as one string: display text is set one paragraph per measured line, so join them back."""
    ps = [p_.text for p_ in sh.text_frame.paragraphs]
    return ("" if dk._has_cjk("".join(ps)) else " ").join(ps)
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
                    if re.match(r"ppt/slides/slide\d+\.xml$", n)), "{}: no vertical setting in P5".format(tag))


def assert_palettes(name):
    for g, V in vl.VARIANTS[name].items():
        p = V["palette"]
        for key in ("ink", "mute"):
            check(cr(p[key], p["ground"]) >= 4.5, "{}/{} {} on ground".format(name, g, key))
            check(cr(p[key], p["panel"]) >= 4.5, "{}/{} {} on its panel (rs.card)".format(name, g, key))
        for t in p["text_accents"]:
            check(cr(t, p["ground"]) >= 4.5, "{}/{} text accent {} on ground".format(name, g, t))
            check(cr(t, p["panel"]) >= 4.5, "{}/{} text accent {} on its panel".format(name, g, t))


# ── native art (Task 1) ──
import native_art as na
from pptx.oxml.ns import qn
prs = dk.blank_deck(13.333, 7.5)
s = dk.add_slide(prs)
segs = na.route(s, [(0.0, 2.0), (5.0, 2.0), (6.5, 3.5)], "D7262E", w=0.16)
check(len(segs) == 2 and all(c._element.spPr.find(qn("a:ln")).get("cap") == "rnd" for c in segs),
      "route: one round-capped stroke per leg")
_w = segs[0]._element.spPr.find(qn("a:ln")).get("w")
check(_w is not None and abs(int(_w) / 12700.0 - 0.16 * 72) < 0.6, "route: the stroke is w inches wide ({})".format(_w))
st = na.station(s, 2.0, 2.0, 0.3, ring="16191E")
check(abs(st.width / EMU - 0.3) < 1e-3 and abs((st.left + st.width / 2) / EMU - 2.0) < 1e-3, "station: centred, d wide")
ic = na.interchange(s, 6.5, 3.5, 1.0, 0.7, ring="16191E")
check(abs(ic.width / EMU - 1.0) < 1e-3 and bool(ic._element.xpath(".//a:prstGeom[@prst='roundRect']")), "interchange: a rounded rect")
x, y, d, _ = na.roundel(s, 9.0, 2.0, 0.5, "1", fill="D7262E", ink="FFFFFF", size=17, face="Arial")
tb = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text == "1"]
check(bool(tb) and tb[0].text_frame.word_wrap is False and abs(x + d / 2 - 9.0) < 1e-6, "roundel: one unwrapped label, centred")
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
na.ui_toggle(s, 3.0, 7.0, False, on_fill="2F6BFF", off_line="8A91A0", h=0.34)
na.ui_cursor(s, 4.0, 6.5, fill="0F1115", edge="FFFFFF")
na.ui_bubble(s, 6.0, 5.5, 3.0, 1.5, fill="FFFFFF", line="E2E5EB")
p = td / "art.pptx"
prs.save(str(p))
check(ox.xml_findings(str(p)) == [] and ox.beyond_page(prs) == [], "native art: PowerPoint-safe and on the page: {} {}".format(
    ox.xml_findings(str(p))[:2], ox.beyond_page(prs)[:2]))

for line in ok:
    print("  ok   " + line)
if skipped:
    print("  skip {} face-precise check(s): this machine lacks the faces they were measured with (e.g. {!r})".format(
        len(skipped), skipped[0][:80]))
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
