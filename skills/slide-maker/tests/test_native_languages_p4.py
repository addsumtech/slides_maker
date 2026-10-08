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
    """The page's visible text boxes (not the off-page title kept for screen readers)."""
    return [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0]
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
# long Chinese copy on a short page falls to the 2x2 ring: still one star per point, no line through words
LONGZH = [("共享工具", "一抽屉螺丝刀可以供三张桌子同时使用。"), ("敞开大门", "不用预约，不收费，不问是什么东西。"),
          ("步行可达", "步行十分钟是我们坚持的距离。"), ("记下每次修理", "每张桌一本笔记，就是明年的培训手册。")]
import vl_native as _vn
for W, H in ((10.0, 5.625), (7.5, 7.5), (13.333, 7.5)):
    prs, k = use("starlit", W, H)
    s = k.new_slide()
    _vn._ALT[0] = 2                       # the ring is the LAST layout: drive it directly, every canvas
    try:
        _vn.COMPOSERS["starlit"]["points"](k, s, dict(title="长文案", items=LONGZH), None)
    finally:
        _vn._ALT[0] = 0
    hit = [sh.text_frame.text[:12] for g in segs_of(s) for sh in texts(s) if crosses(g, rect_of(sh))]
    check(len(segs_of(s)) == 3 and not hit, "starlit {}x{}: the ring layout's lines never cross words: {}".format(W, H, hit[:3]))
# the constellation sits in the room under the title, not crowded against it (sample render, 2026-10-08: the lower
# half of the page was empty)
for W, H in ((13.333, 7.5), (10.0, 7.5)):
    prs, k = use("starlit", W, H)
    s = k.new_slide()
    k.points(s, title="Three things we learned", items=POINTS4[:3])
    tb = [sh for sh in texts(s) if sh.text_frame.text == "Three things we learned"][0]
    star_ys = [sh.top / EMU + sh.height / EMU / 2 for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']")
               and not sh._element.xpath(".//a:gradFill") and sh.width / EMU < 0.3]
    lab = [sh.top / EMU + sh.height / EMU for sh in texts(s) if sh.text_frame.text != "Three things we learned"]
    above, below = min(star_ys) - (tb.top + tb.height) / EMU, (H - 0.6) - max(lab)
    check(abs(above - below) < 0.8, "starlit {}x{}: the constellation is centred under the title (above {:.2f}, below {:.2f})".format(
        W, H, above, below))
# the quote mark sits close over its quote (sample render: a 110pt mark's line box left ~1in of air between them)
prs, k = use("starlit")
s = k.new_slide(); k.quote(s, quote="We measured the year in conversations, not in launches.", attribution="The letter")
mk = [sh for sh in texts(s) if sh.text_frame.text == "“"][0]
qt = [sh for sh in texts(s) if sh.text_frame.text.startswith("We measured")][0]
check((qt.top - mk.top) / EMU <= 1.45, "starlit: the quote mark sits close over the quote ({:.2f}in)".format((qt.top - mk.top) / EMU))
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
# a printed board in a language with no light ground: auto keeps the default and SAYS it prints dark (Task 3 ruling)
_g, _why = vl._auto_ground("starlit", dk.blank_deck(8.27, 11.69))
check(_g == "light" and "has none" in _why and "dark" in _why,
      "starlit on an A4 print board: auto keeps the default ground and says it prints dark ({})".format(_why))
_g, _why = vl._auto_ground("ink", dk.blank_deck(8.27, 11.69))
check(_g == "light" and "dark" not in _why, "ink on an A4 print board: the plain light-ground note ({})".format(_why))


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
        elif getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0:
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
# lint measures a DECLARED raised initial as it renders: the first line at the initial's size, every other line at the
# body's (its conservative every-line-at-the-largest-run model read a 3-line column with a 41pt initial as 8 lines)
prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
BODY = "Anything that switches on, unzips or wobbles is welcome; nobody is turned away at the door."
plain_tb = dk.text(s, 1.0, 0.5, 2.6, 2.0, [[(BODY, 18, dk.DEEP, False, False, "Georgia")]])
plain_h = dk._ink_rect(plain_tb, (1.0, 0.5, 2.6, 2.0))[0][3]
init_tb = dk.text(s, 5.0, 0.5, 2.6, 2.0, [[(BODY, 18, dk.DEEP, False, False, "Georgia")]])
v2.raise_initial(init_tb, face="Times New Roman")
bb = (init_tb.left / EMU, init_tb.top / EMU, init_tb.width / EMU, init_tb.height / EMU)
init_h = dk._ink_rect(init_tb, bb)[0][3]
check("+initial" in init_tb.name or init_tb.name.startswith("deckkit-initial"), "raise_initial declares the initial ({})".format(init_tb.name))
check(init_h <= plain_h + (2.3 - 1.0) * 18 * 1.25 / 72 + 18 * 1.25 / 72 + 0.05,       # + at most the one line its width pushes
      "lint reads a declared initial as one taller line ({:.2f} vs plain {:.2f})".format(init_h, plain_h))
undecl = dk.text(s, 9.0, 0.5, 2.6, 2.0, [[("A", 41.4, dk.DEEP, True, False, "Times New Roman"), (BODY[1:], 18, dk.DEEP, False, False, "Georgia")]])
und_h = dk._ink_rect(undecl, (9.0, 0.5, 2.6, 2.0))[0][3]
check(und_h > 1.6 * init_h, "an UNDECLARED mixed-size paragraph keeps lint's conservative measure ({:.2f})".format(und_h))
# long column bodies on a 4:3 page: the raised initial never makes lint read the column past the page (lint sizes every
# line of a paragraph at its largest run — the generality corpus found three OFF_CANVAS on 4:3); the words always set
LONGB = [("Share the tools", "One drawer of screwdrivers feeds three tables."),     # the generality corpus's copy
         ("Open the door", "No booking, no fee, no questions about the object."),
         ("Keep it walkable", "Ten minutes on foot is the limit we keep."),
         ("Write every repair down", "A notebook per bench becomes next year's manual.")]
for W, H in ((10.0, 7.5), (10.0, 5.625), (7.5, 7.5)):
    prs, k = use("broadsheet", W, H)
    k.points(k.new_slide(), title="Why every street deserves a place to fix what it owns", items=LONGB)
    with contextlib.redirect_stdout(io.StringIO()):
        crit = [f_ for f_ in dk.lint_layout(prs, verbose=False) if f_[1] == "CRITICAL"]
    check(not crit, "broadsheet {}x{}: long columns stay on the page under lint's measure: {}".format(W, H, [(c[2], c[3][:50]) for c in crit[:2]]))
# the front-page headline size is the cover's: an inside page's title is a section head (sample render: 80pt on points)
prs, k = use("broadsheet")
for page, kw in (("points", dict(title="How a repair evening works", items=["a", "b"])),
                 ("image_text", dict(title="The hall on a Tuesday", body="Benches and tools.", image=PHOTO))):
    s = k.new_slide(); getattr(k, page)(s, **kw)
    t = [sh for sh in texts(s) if sh.text_frame.text == kw["title"]][0]
    check(t.text_frame.paragraphs[0].runs[0].font.size.pt <= 48, "broadsheet {}: the title is a section head, not the cover's headline ({}pt)".format(
        page, t.text_frame.paragraphs[0].runs[0].font.size.pt))
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
    k.points(k.new_slide(), title="x", items=["a", "b"], tags=["x" * 400, "y"])   # wider than the page at the floor
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

# the measure leaves headroom: LibreOffice set "Three lines on the ledger" (11.39in of Arial Black, measured to fit an
# 11.41in box) on two lines, drawn over the first ledger row; P4 measures in 97% of a column and draws at its full width
prs, k = use("tally")
s = k.new_slide()
k.points(s, kicker="Q3 review", title="Three lines on the ledger", tags=["Members", "Loans", "Repairs"],
         items=[("New members joined", "Mostly through word of mouth"), ("Tools went out on loan", "Drills and ladders"),
                ("Items came back repaired", "Fixed at the monthly evening")])
tt = [sh for sh in texts(s) if sh.text_frame.text == "Three lines on the ledger"][0]
row = [sh for sh in texts(s) if sh.text_frame.text == "New members joined"][0]
sz = tt.text_frame.paragraphs[0].runs[0].font.size.pt
check(dk.measure_text([("Three lines on the ledger", False)], tt.width / EMU * 0.97, sz, font="Arial Black") <= tt.height / EMU + 0.02
      and row.top >= tt.top + tt.height, "tally: the title holds its words with headroom and the first row starts under it")
import vl_native2 as _v2h
_r, _d = _v2h.flow(k, k.new_slide(), "cover", (1.0, 1.0, 8.0, 3.0), [("title", "A title")], anchor="top")
check(abs(_r["title"][0] - 1.0) < 1e-6 and abs(_r["title"][2] - 8.0) < 0.01 and hasattr(_d, "sizes"),
      "P4 flow: rects report the full column while the words were measured in 97% of it ({})".format(_r["title"]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
