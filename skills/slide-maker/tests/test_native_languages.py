#!/usr/bin/env python3
"""The four NATIVE visual languages: registered like the image-led four, their grounds' inks pass contrast,
pages compose on every canvas, and nothing they draw leaves the page or trips PowerPoint."""
from __future__ import annotations
import contextlib, io, os, sys, tempfile, zipfile, hashlib, json
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

def vl_native_fields():
    import vl_native
    return vl_native.POSTER_FIELDS


td = Path(tempfile.mkdtemp())
check(vl.NATIVE == ("ink", "poster", "cutpaper", "drafting"), "the four native languages are named")
check(set(vl.NATIVE) | set(vl.IMAGE_LED) == set(vl.LANGS), "every language is native or image-led")
check(vl.PAGE_FIELDS.get("points") == ("kicker", "title", "items"), "the points page exists")
for n in vl.NATIVE:
    for g, V in vl.VARIANTS[n].items():
        p = V["palette"]
        check(cr(p["ink"], p["ground"]) >= 4.5, "{}/{} ink on ground".format(n, g))
        check(cr(p["mute"], p["ground"]) >= 4.5, "{}/{} mute on ground".format(n, g))
        for t in p["text_accents"]:
            check(cr(t, p["ground"]) >= 4.5, "{}/{} text accent {} on ground".format(n, g, t))
        on_panel = p.get("card_ink", p["ink"])
        check(cr(on_panel, p["panel"]) >= 4.5, "{}/{} ink on its panel".format(n, g))
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(n, dk.blank_deck(13.333, 7.5), ground=g)
        check(k.ground == g and k.P["ground"] == p["ground"] or n == "poster", "{}/{} use() sets the ground".format(n, g))
# points belongs to the native languages only
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("collage", dk.blank_deck(13.333, 7.5))
try:
    k.points(k.new_slide(), title="x", items=["a", "b"])
    check(False, "points() on an image-led language is refused")
except ValueError as e:
    check("native" in str(e), "points() on an image-led language names the native languages: {}".format(e))
# extras are per language
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("ink", dk.blank_deck(13.333, 7.5))
try:
    k.cover(k.new_slide(), title="x", highlight="x")
    check(False, "an extra that belongs to another language is refused")
except TypeError:
    check(True, "an extra that belongs to another language is refused")
# poster and drafting ordinary pages carry their ground
for n in ("poster", "drafting"):
    prs = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(n, prs)
    s = k.new_slide()
    has_bg = s._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cSld").find(
        "{http://schemas.openxmlformats.org/presentationml/2006/main}bg") is not None
    check(has_bg, "{}: an ordinary new_slide() page gets the language's ground".format(n))
# image-led samples are byte-identical to the pre-change build (Review Focus 5)
base = Path(os.environ.get("VL_BASELINE", "/nonexistent")) / "hashes.json"     # recorded before the change
if base.exists():
    want = json.loads(base.read_text())
    for key, hashes in want.items():
        n, g = key.split("-", 1)
        p = vl.build_sample(n, str(td), ground=g)
        z = zipfile.ZipFile(str(p))
        got = [hashlib.sha256(z.read(x)).hexdigest() for x in sorted(z.namelist()) if x.startswith("ppt/slides/slide")]
        check(got == hashes, "{} is unchanged by the native languages".format(key))
else:
    print("  skip image-led baseline: VL_BASELINE is not set (recorded locally before the change; not in CI)")
# a deck that never picks a native language loads nothing new (spec §6 performance)
import subprocess
probe = subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0, 'scripts'); import contextlib, io, deckkit as dk, visual_languages as vl\n"
    "with contextlib.redirect_stdout(io.StringIO()):\n"
    "    k = vl.use('collage', dk.blank_deck(13.333, 7.5)); k.new_slide()\n"
    "print(sorted(m for m in ('vl_native', 'native_art', 'ooxml_safety') if m in sys.modules))"],
    capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
check(probe.stdout.strip() == "[]", "an image-led deck imports no native module: {!r} {}".format(
    probe.stdout.strip(), probe.stderr[-200:]))

# ── the page matrix: every page × canvas × copy, then lint, PowerPoint safety and the page edge ──
import re
CANVASES = {"16:9": (13.333, 7.5), "4:3": (10.0, 7.5), "portrait": (7.5, 13.333)}
COPY = {
    "en": dict(kicker="A guide for the room", title="Bring it broken, take it home working",
               subtitle="Once a month, on the corner", number="3", label="evenings a month", note="Short enough to fit around work.",
               quote="The visitor holds the screwdriver; the volunteer only guides.", attribution="How every repair begins",
               body="Screwdrivers, a soldering iron and thread, shared on every bench.", line="Bring a neighbour.",
               items=[("Share the tools", "One bench, many hands"), ("Open the door", None), ("Keep it local", "Walk, don't drive")]),
    "zh": dict(kicker="茶事", title="一盏茶的时间", subtitle="慢下来，看见日常", number="3", label="泡，滋味最浓",
               note="头泡醒茶，三泡正好", quote="茶有两种姿态，浮与沉", attribution="茶室题记", body="器净，心先静。",
               line="下次再见", items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")]),
    "ja": dict(kicker="茶の時間", title="一服のお茶", subtitle="ゆっくり、日常を見る", number="3", label="煎目がいちばん",
               note="一煎目で目覚め、三煎目で整う", quote="茶には浮くと沈むがある", attribution="茶室の記", body="器を清め、心を静める。",
               line="またお会いしましょう", items=[("器を清める", None), ("湯を沸かす", "蟹の目のように"), ("茶を注ぐ", None)]),
    "ko": dict(kicker="차 이야기", title="차 한 잔의 시간", subtitle="천천히, 일상을 보다", number="3", label="번째가 가장 진하다",
               note="첫 잔은 깨우고 셋째 잔은 맞춘다", quote="차에는 뜨는 것과 가라앉는 것이 있다", attribution="다실의 기록",
               body="그릇을 씻고 마음을 고른다.", line="다음에 또 만나요", items=[("그릇 씻기", None), ("물 끓이기", None)]),
}
EXTRA = {"ink": {"seal": "茶事"}, "poster": {"highlight": None}, "cutpaper": {}, "drafting": {"project": None}}


def build_matrix(name, ground, cname, lang):
    W, H = CANVASES[cname]
    T = COPY[lang]
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(name, prs, ground=ground)
    ex = {k_: v for k_, v in EXTRA[name].items() if v}
    if name == "ink" and lang not in ("zh", "ja"):
        ex = {}                                   # a Chinese seal on Latin or Hangul copy is not a test of the layout
    if name == "poster":
        ex = {"highlight": T["title"].split()[0]} if lang == "en" else {}
    pages = [("cover", dict(kicker=T["kicker"], title=T["title"], subtitle=T["subtitle"], **ex)),
             ("section", dict(number="02", kicker=T["kicker"], title=T["title"])),
             ("points", dict(kicker=T["kicker"], title=T["title"], items=T["items"])),
             ("quote", dict(quote=T["quote"], attribution=T["attribution"])),
             ("data", dict(number=T["number"], label=T["label"], note=T["note"])),
             ("closing", dict(title=T["title"], line=T["line"]))]
    for page, fields in pages:
        if name == "ink" and page in ("cover", "points", "quote") and "seal" in ex:
            fields.setdefault("seal", ex["seal"])
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
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
                check(not crit, "{}: no critical layout fault: {}".format(tag, crit[:2]))
                check(ox.xml_findings(str(p)) == [], "{}: PowerPoint-safe: {}".format(tag, ox.xml_findings(str(p))[:2]))
                check(ox.beyond_page(prs) == [], "{}: nothing past the page: {}".format(tag, ox.beyond_page(prs)[:2]))
                xml = "".join(zipfile.ZipFile(str(p)).read(n).decode("utf-8") for n in zipfile.ZipFile(str(p)).namelist()
                              if re.match(r"ppt/slides/slide\d+\.xml$", n))
                if name == "ink" and lang in ("en", "ko"):
                    check('vert="eaVert"' not in xml, "{}: no vertical setting for {} copy".format(tag, lang))


# ── ink ──
assert_matrix("ink")
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("ink", dk.blank_deck(13.333, 7.5))
s = k.new_slide()
k.cover(s, title="一盏茶的时间", subtitle="慢下来，看见日常")
check(not any(getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() in ("茶事",) for sh in s.shapes),
      "ink: no seal is drawn when seal= is not given")
s = k.new_slide()
k.cover(s, title="Bring it broken")
check(not any('vert="eaVert"' in sh._element.xml for sh in s.shapes if getattr(sh, "has_text_frame", False)),
      "ink: a Latin title is set horizontally")
try:
    k.cover(k.new_slide(), title="一盏茶的时间", seal="三个字")
    check(False, "ink: a three-character seal is refused")
except ValueError:
    check(True, "ink: a three-character seal is refused")
try:
    k.cover(k.new_slide(), title="此" * 60)
    check(False, "ink: an impossible vertical title is refused")
except vl.VLTextOverflow:
    check(True, "ink: an impossible vertical title is refused")
# a short CJK title stays ONE tall column when it fits at >= 85% of its size (the approved cover), not two short ones
out = k.cover(k.new_slide(), title="一盏茶的时间", subtitle="慢下来，看见日常")
rt = out["rects"]["title"]
check(rt[2] / rt[3] < 0.4, "ink: a six-character title is one tall column, not two: w/h={:.2f}".format(rt[2] / rt[3]))
for bad_items in (["一"], ["一", "二", "三", "四", "五"], ["一", ""]):
    try:
        k.points(k.new_slide(), title="三道工序", items=bad_items)
        check(False, "ink: points with {} refused".format(bad_items))
    except ValueError:
        check(True, "ink: points with {} refused".format(bad_items))

# ── poster ──
for g, fields in vl_native_fields().items():
    for i, fl in enumerate(fields):
        for a, b, what in ((fl["ink"], fl["bg"], "ink"), (fl["accent"], fl["bg"], "accent"),
                           (fl["panel_ink"], fl["panel"], "panel ink"), (fl["panel_accent"], fl["panel"], "panel accent"),
                           (fl["hl_ink"], fl["hl"], "highlight ink")):
            check(cr(a, b) >= 4.5, "poster/{} field {} {} {} on {}: {:.2f}".format(g, i, what, a, b, cr(a, b)))
assert_matrix("poster")
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("poster", prs)
bgs = []
for _ in range(5):
    s = k.new_slide()
    bgs.append(k.field["bg"])
check(bgs[0] != bgs[1] and bgs[4] == bgs[0], "poster: each page takes the next colour field, cycling")
try:
    k.cover(k.new_slide(), title="Make the room smaller", highlight="garden")
    check(False, "poster: a highlight that is not in the title is refused")
except ValueError:
    check(True, "poster: a highlight that is not in the title is refused")
s = k.new_slide()
k.cover(s, title="Make the room smaller", highlight="room")
check(any("a:highlight" in sh._element.xml for sh in s.shapes if getattr(sh, "has_text_frame", False)),
      "poster: the highlighted word sits on a highlighter")
# poster display type breaks like the rest of the kit: at a clause mark first, never a lone CJK character or a
# lone word on the last line (seen on the first render: "一盏茶的时 / 间", "慢下来，看 / 见日常")
def lines_of(slide):
    import vl_native
    out = []
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip():
            out.append([p_.text for p_ in sh.text_frame.paragraphs])
    return out
for g in vl.VARIANTS["poster"]:
    for W, H in ((13.333, 7.5), (7.5, 13.333)):
        prs = dk.blank_deck(W, H)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use("poster", prs, ground=g)
        for page, kw in (("closing", dict(title="一盏茶的时间")), ("section", dict(number="二", title="慢下来，看见日常")),
                         ("data", dict(number="3", label="泡，滋味最浓")), ("points", dict(title="一盏茶的时间", items=["洗盏", "候汤"]))):
            s = k.new_slide()
            out = getattr(k, page)(s, **kw)
            r = out["rects"]["title" if "title" in kw else "label"]
            txt = kw.get("title") or kw.get("label")
            shape = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.replace("\n", "").replace("\x0b", "") .replace(" ", "") == txt.replace(" ", "")]
            check(shape, "poster/{} {}: the {} is one text box".format(g, page, txt))
            if not shape:
                continue
            import vl_native
            fld = "title" if page in ("closing", "points") else "label"
            # the visible title, not the 10pt a11y title deckkit parks off the page for screen readers
            shape = sorted(shape, key=lambda sh: -sh.text_frame.paragraphs[0].runs[0].font.size.pt)
            sz = shape[0].text_frame.paragraphs[0].runs[0].font.size.pt
            ls = [p_.text for p_ in shape[0].text_frame.paragraphs]
            broken = ls if len(ls) > 1 else vl._break_lines(k, fld, txt, sz, shape[0].width / 914400.0)
            check(len(broken[-1].strip()) > 2 or len(broken) == 1,
                  "poster/{}/{}x{} {}: no lone character on the last line: {}".format(g, W, H, page, broken))
            if "，" in txt and len(broken) > 1:
                check(broken[0].endswith("，"), "poster/{} {}: a two-line clause breaks at its comma: {}".format(g, page, broken))
# ordinary pages on poster (k.new_slide + rs.card + dk.DEEP) stay readable on EVERY field (Review Focus 3): the
# field changes per page, so the deck's default ink, its card and the card's label follow it
import register_surface as rs
for g in vl.VARIANTS["poster"]:
    prs = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("poster", prs, ground=g)
    for i in range(4):
        s = k.new_slide()
        bg = k.field["bg"]
        body, header = rs.card(s, "poster", 1.0, 1.5, 5.0, 3.0, label="Agenda")
        fill = str(body.fill.fore_color.rgb)
        ink = str(dk.DEEP)
        lab = str(header.text_frame.paragraphs[0].runs[0].font.color.rgb)
        check(cr(ink, bg) >= 4.5, "poster/{} page {}: dk.DEEP {} reads on the field {} ({:.2f})".format(g, i, ink, bg, cr(ink, bg)))
        check(cr(ink, fill) >= 4.5, "poster/{} page {}: dk.DEEP {} reads on rs.card {} ({:.2f})".format(g, i, ink, fill, cr(ink, fill)))
        check(cr(lab, fill) >= 4.5, "poster/{} page {}: the card label {} reads on it ({:.2f})".format(g, i, lab, cr(lab, fill)))

# ── cutpaper ──
assert_matrix("cutpaper")
import vl_native as _vn
for g, A in _vn.CUT_ART.items():
    for disc_ in A["discs"]:
        check(cr("FFFFFF", disc_) >= 3.0, "cutpaper/{}: a white icon on disc {} clears 3:1".format(g, disc_))
    for ring in A["rings"][-1:]:
        pal = vl.VARIANTS["cutpaper"][g]["palette"]
        check(cr(pal["card_ink"], ring) >= 4.5, "cutpaper/{}: the figure on the inner sun ring reads".format(g))
# the quote sits on a STACK of offset sheets that shows (the first render hid both sheets behind the card)
for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333)):
    with contextlib.redirect_stdout(io.StringIO()):
        prs = dk.blank_deck(W, H); k = vl.use("cutpaper", prs)
    s = k.new_slide()
    k.quote(s, quote="Every forest began as one small seed.", attribution="A paper-cut science story")
    rr = [sh for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='roundRect']")]
    front = rr[-1]
    fr, fb = (front.left + front.width) / 914400.0, (front.top + front.height) / 914400.0
    for sh in rr[:-1]:
        r_, b_ = (sh.left + sh.width) / 914400.0, (sh.top + sh.height) / 914400.0
        check(r_ - fr >= 0.12 and b_ - fb >= 0.12, "cutpaper {}x{}: a back sheet shows past the card (right {:+.2f}, bottom {:+.2f})".format(
            W, H, r_ - fr, b_ - fb))
# a portrait cover's card fits its words (the first render left a fixed card two-thirds empty under one line)
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(7.5, 13.333); k = vl.use("cutpaper", prs)
s = k.new_slide()
out = k.cover(s, kicker="A paper-cut science story", title="How seeds travel")
tb = max(r_[1] + r_[3] for r_ in out["rects"].values())
cards = [sh for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='roundRect']")]
cb = (cards[-1].top + cards[-1].height) / 914400.0
check(0 <= cb - tb <= 0.75, "cutpaper portrait cover: the card ends just under its words (gap {:.2f}in)".format(cb - tb))
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("cutpaper", prs)
s = k.new_slide()
k.points(s, title="Three ways a seed gets around", items=["Wind", "Water", "Animals"],
         icons=["lucide:wind", "lucide:droplets", "lucide:paw-print"])
check(sum(1 for sh in s.shapes if sh.shape_type == 13) == 3, "cutpaper: one icon per point")
try:
    k.points(k.new_slide(), title="x", items=["a", "b"], icons=["lucide:wind"])
    check(False, "cutpaper: icons= must match the points one to one")
except ValueError:
    check(True, "cutpaper: icons= must match the points one to one")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
