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


# render review (Task 2): a chip's dot never sits on its words; initials only from a name; the data page uses its width
prs, k = use("interface")
s = k.new_slide()
k.cover(s, title="Ship it", status=("Live", "on"))
dots = [sh for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']") and sh.width / EMU < 0.15]
lab = [sh for sh in texts(s) if txt_of(sh) == "Live"][0]
check(dots and all(not v2.meet(rect_of(d), (lab.left / EMU + 0.04, lab.top / EMU, lab.width / EMU - 0.08, lab.height / EMU))
                   for d in dots), "interface: the status dot sits beside its words, not on them")
check(v3.initials("How every repair begins") is None and v3.initials("Library principle") is None
      and v3.initials("Style sample") is None, "interface: no avatar from an attribution that is not a name")
prs, k = use("interface")
s = k.new_slide()
k.data(s, number="3", label="evenings a month", note="Short enough to fit around work.")
xs = [rect_of(sh)[0] + rect_of(sh)[2] for sh in s.shapes if sh.top >= 0 and sh.width < 12 * EMU]
check(max(xs) > 0.80 * 13.333, "interface: the data page spans the width (note beside the card)")

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
for lang, want in (("en", "Way out"), ("zh", "出口"), ("ja", "出口"), ("ko", "출구")):
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


# render review (Task 3): no route on the cover crosses the words, on any canvas
for W, H in list(CANVASES.values()) + [(7.5, 7.5), (10.0, 5.625)]:
    prs, k = use("wayfinding", W, H)
    s = k.new_slide()
    k.cover(s, kicker="A guide for the room", title="Bring it broken, take it home working",
            subtitle="Once a month, on the corner", line="1")
    conns = [sh for sh in s.shapes if sh._element.tag.endswith("cxnSp")]
    hit = [txt_of(t)[:20] for c in conns for t in texts(s) if v2.meet(rect_of(c), rect_of(t))]
    check(not hit, "wayfinding cover {}x{}: no route crosses the words {}".format(W, H, hit[:2]))

for line in ok:
    print("  ok   " + line)
if skipped:
    print("  skip {} face-precise check(s): this machine lacks the faces they were measured with (e.g. {!r})".format(
        len(skipped), skipped[0][:80]))
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
