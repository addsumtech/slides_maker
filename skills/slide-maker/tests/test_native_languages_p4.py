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
    return [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]
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


for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
