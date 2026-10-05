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
        # an ORDINARY page's card (rs.card fills `panel`) carries text in the DEFAULT inks — not card_ink, which is
        # for the white paper cards the compositions draw (a non-Claude run set cream-on-white at 1.16:1)
        for key in ("ink", "mute"):
            check(cr(p[key], p["panel"]) >= 4.5, "{}/{} {} on its panel (rs.card)".format(n, g, key))
        for t in p["text_accents"][:1]:
            check(cr(t, p["panel"]) >= 4.5, "{}/{} the card label {} on its panel".format(n, g, t))
        for key in ("card_ink", "card_mute", "card_accent"):
            if key in p:
                check(cr(p[key], "FFFFFF") >= 4.5, "{}/{} {} on the white paper card".format(n, g, key))
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
s = k.new_slide()
k.cover(s, title="此" * 60)                      # too long for 2 vertical columns: set across, not refused
check(not any('vert="eaVert"' in sh._element.xml for sh in s.shapes if getattr(sh, "has_text_frame", False)),
      "ink: a title too long for vertical columns is set horizontally")
try:
    k.cover(k.new_slide(), title="此" * 400)
    check(False, "ink: a title too long for ANY layout is refused")
except vl.VLTextOverflow:
    check(True, "ink: a title too long for ANY layout is refused")
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
# a headline stacked one word a line ("THREE / MOVES.") is a poster's stack, not a widow — it keeps its size
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("poster", prs)
s = k.new_slide()
k.points(s, title="Three moves.", items=["Share the tools", "Open the door", "Keep it local"])
big = max((sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and "THREE" in sh.text_frame.text),
          key=lambda sh: sh.text_frame.paragraphs[0].runs[0].font.size.pt)
check(big.text_frame.paragraphs[0].runs[0].font.size.pt >= 85,
      "poster: a two-word title stacks at display size ({:.0f}pt)".format(big.text_frame.paragraphs[0].runs[0].font.size.pt))
# a long points title on a narrow poster shrinks to the label floor, never refused (CI's Linux faces measure wider:
# the matrix copy was refused there at the title field's 44pt floor)
for W, H in ((10.0, 7.5), (13.333, 7.5), (7.5, 13.333)):
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("poster", dk.blank_deck(W, H))
    try:
        k.points(k.new_slide(), title="Bring it broken, take it home working, every month of the year",
                 items=["Share the tools", "Open the door", "Keep it local"])
        check(True, "poster {}x{}: a long points title fits by shrinking".format(W, H))
    except vl.VLTextOverflow as e:
        check(False, "poster {}x{}: a long points title fits by shrinking: {}".format(W, H, e))
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

# ── drafting (蓝图技术线稿; `blueprint` is a preset's name) ──
assert_matrix("drafting")
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("drafting", prs)
s1 = k.new_slide()
k.cover(s1, title="A room built layer by layer", kicker="Schematic 01")
s2 = k.new_slide()
k.points(s2, title="Three layers, one frame", items=[("Floor", "One plate"), ("Walls", "Panels slide"), ("Roof", "One span")])
txt = lambda s: " ".join(sh.text_frame.text for sh in s.shapes if getattr(sh, "has_text_frame", False))
check("A room built layer by layer" in txt(s2), "drafting: the title block carries the cover title on later sheets")
check("SHEET" in txt(s1) and "01" in txt(s1) and "02" in txt(s2), "drafting: each sheet is numbered")
n_tops = sum(1 for sh in s2.shapes if sh.shape_type == 5)        # freeform: the iso stack draws layers as polygons
check(n_tops >= 9, "drafting: the points page draws one iso layer per point (3 layers x 3 faces)")
s3 = k.new_slide()
k.cover(s3, title="Another title", project="A modular reading room")
check("A modular reading room" in txt(s3), "drafting: project= replaces the remembered title")
# the dimension line stands BESIDE the numeral's ink, on every canvas (portrait first drew it through the "3")
import display_type as _dt
for W, H in ((13.333, 7.5), (10.0, 7.5), (7.5, 13.333)):
    with contextlib.redirect_stdout(io.StringIO()):
        prs = dk.blank_deck(W, H); k = vl.use("drafting", prs)
    s = k.new_slide()
    k.data(s, number="3", label="layers, one structure.")
    num = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() == "3"
           and sh.text_frame.paragraphs[0].runs[0].font.size.pt > 40][0]
    run = num.text_frame.paragraphs[0].runs[0]
    gw = _dt._glyph_width("3", run.font.size.pt, run.font.name, bool(run.font.bold))
    right_ink = (num.left + num.width / 2) / 914400.0 + gw / 2
    verts = [sh for sh in s.shapes if sh.shape_type == 9 and abs(sh.width) < 914400 * 0.01 and sh.height > 914400]
    check(verts and min(sh.left / 914400.0 for sh in verts) >= right_ink + 0.05,
          "drafting {}x{}: the dimension line clears the numeral's ink ({} vs {:.2f})".format(
              W, H, [round(sh.left / 914400.0, 2) for sh in verts], right_ink))
# portrait notes sit beside the stack they label, not strung down the whole sheet
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(7.5, 13.333); k = vl.use("drafting", prs)
s = k.new_slide()
k.points(s, title="Three layers, one frame", items=[("Floor", "One plate"), ("Walls", "Panels slide"), ("Roof", "One span")])
balloons = sorted(sh.top / 914400.0 for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']"))
polys = [sh for sh in s.shapes if sh.shape_type == 5]
stack_bottom = max((sh.top + sh.height) / 914400.0 for sh in polys)
check(balloons and balloons[-1] <= stack_bottom + 0.6,
      "drafting portrait: the last note sits beside the stack (balloon {:.2f} vs stack bottom {:.2f})".format(
          balloons[-1] if balloons else -1, stack_bottom))
# the Task 3 "ordinary page gets the ground" check passed trivially (every slide has a bg); pin what each ground IS
P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("poster", prs)
for _ in range(3):
    s = k.new_slide()
    clr = s._element.find(P_NS + "cSld").find(P_NS + "bg").find(".//" + A_NS + "srgbClr")
    check(clr is not None and clr.get("val") == k.field["bg"], "poster: an ordinary page's background IS its field {}".format(k.field["bg"]))
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("drafting", prs)
s = k.new_slide()
check("SHEET" in txt(s) and s._element.find(P_NS + "cSld").find(P_NS + "bg").find(".//" + A_NS + "blip") is not None,
      "drafting: an ordinary page is a numbered drawing sheet on the grid")

# ── samples + direction ──
for n in vl.NATIVE:
    for g in vl.VARIANTS[n]:
        p = vl.build_sample(n, str(td), ground=g)
        with contextlib.redirect_stdout(io.StringIO()):
            crit = [f for f in dk.lint_layout(__import__("pptx").Presentation(str(p)), verbose=False) if f[1] == "CRITICAL"]
        check(not crit, "{}/{} sample: no critical fault".format(n, g))
        check(ox.xml_findings(str(p)) == [] and ox.beyond_page(__import__("pptx").Presentation(str(p))) == [],
              "{}/{} sample: PowerPoint-safe, nothing past the page".format(n, g))
        sample = vl.ASSETS / "samples" / "{}.jpg".format(vl._sample_stem(n, g))
        check(sample.exists() and sample.stat().st_size <= 350 * 1024, "{}/{}: a bundled JPG sample <= 350 KB".format(n, g))
        d = vl.direction(n, ground=g)
        check(d["vl"] == n and d["sample"].startswith("data:image/jpeg"), "{}/{}: direction() previews it".format(n, g))

# the poster's per-page palette does not outlive its deck: a later use() of ANY language starts clean (final review)
import register_surface as _rs2
with contextlib.redirect_stdout(io.StringIO()):
    kp = vl.use("poster", dk.blank_deck(13.333, 7.5))
for _ in range(3):
    kp.new_slide()                                   # ends on a non-first field
with contextlib.redirect_stdout(io.StringIO()):
    pe = dk.blank_deck(13.333, 7.5); ke = vl.use("editorial", pe)
body, _h = _rs2.card(dk.add_slide(pe), "poster", 1.0, 1.0, 3.0, 2.0)     # a plain page: no language of its own
check(str(body.fill.fore_color.rgb) == vl.VARIANTS["poster"]["light"]["palette"]["panel"],
      "a later deck's poster card is the base palette, not the last deck's field ({})".format(body.fill.fore_color.rgb))
# drafting's title block holds what fits: a long remembered cover title shrinks to fit or is left out (the spec's
# fallback chain ends at the sheet number alone); an explicit project= that cannot fit is refused (final review)
LONG = "A modular reading room built layer by layer for every neighbourhood library across the whole city this year"
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("drafting", prs)
k.cover(k.new_slide(), title=LONG)
s2 = k.new_slide()
blk = [sh for sh in s2.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.paragraphs[0].text == "PROJECT"]
if blk:
    tb_ = blk[0]
    paras = [(p_.text, p_.runs[0].font.size.pt) for p_ in tb_.text_frame.paragraphs if p_.runs]
    need = sum(dk.measure_text([(t_, True)], tb_.width / 914400.0, sz_, font="Courier New") for t_, sz_ in paras)
    check(need <= tb_.height / 914400.0 + 0.02, "drafting: the remembered title fits the title block ({:.2f} vs {:.2f}in)".format(
        need, tb_.height / 914400.0))
else:
    check(True, "drafting: a remembered title too long for the block is left out (sheet number alone)")
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("drafting", dk.blank_deck(13.333, 7.5))
try:
    k.cover(k.new_slide(), title="x", project=LONG + " " + LONG)
    check(False, "drafting: a project= too long for the title block is refused")
except vl.VLTextOverflow:
    check(True, "drafting: a project= too long for the title block is refused")
# vertical columns break at the CLAUSE, and a couplet is two equal columns (a weak-model run, 2026-10-05: the
# cover read "宋代点茶：一 / 盏茶里的审美" and the couplet's second line split into two short columns)
def vparas(slide):
    """[(paragraph texts, size, visual columns)] of every vertical text box — a paragraph WRAPS into further columns
    when the box is short, so the column count is read from the box width (vcol sizes it: cols x size x 1.28 + 0.06)."""
    out = []
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and 'vert="eaVert"' in sh._element.xml:
            sz = sh.text_frame.paragraphs[0].runs[0].font.size.pt
            cols = int(round((sh.width / 914400.0 - 0.06) / (sz * 1.28 / 72.0)))
            out.append(([p_.text for p_ in sh.text_frame.paragraphs], sz, cols))
    return out
for W, H in ((13.333, 7.5), (10.0, 5.625)):
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("ink", dk.blank_deck(W, H), ground="night")
    s = k.new_slide()
    k.cover(s, title="宋代点茶：一盏茶里的审美")
    vp = vparas(s)
    check(any(ps == ["宋代点茶：", "一盏茶里的审美"] and c == 2 for ps, _z, c in vp) or any(c == 1 for _p, _z, c in vp),
          "ink {}x{}: a vertical title breaks its columns at the clause: {}".format(W, H, vp))
    s = k.new_slide()
    k.section(s, number="一", title="溯源：宋茶的黄金时代")
    vp = vparas(s)
    check(any(ps == ["溯源：", "宋茶的黄金时代"] and c == 2 for ps, _z, c in vp) or any(c == 1 for _p, _z, c in vp),
          "ink {}x{}: section title breaks at the clause: {}".format(W, H, vp))
    s = k.new_slide()
    k.quote(s, quote="琴里知闻唯渌水，茶中故旧是蒙山。", attribution="白居易")
    vp = [v for v in vparas(s) if "白居易" not in "".join(v[0])]
    check(len(vp) == 2 and all(len(ps) == 1 and c == 1 for ps, _z, c in vp) and len({z for _p, z, _c in vp}) == 1,
          "ink {}x{}: the couplet is two single columns at one size: {}".format(W, H, vp))
# ── found by the non-Claude usability run (2026-10-05) ──
import register_surface as rs, subprocess as _sp
with contextlib.redirect_stdout(io.StringIO()):
    prs = dk.blank_deck(13.333, 7.5); k = vl.use("cutpaper", prs)
s = k.new_slide()
try:
    rs.ground(s, "editorial", role="content", index=2)
    check(False, "rs.ground with ANOTHER language's name on a cutpaper page is refused")
except ValueError as e:
    check("cutpaper" in str(e), "rs.ground with another language's name names the page's own: {}".format(e))
check(len(rs.ground(s, "cutpaper", role="content", index=2)) == 4, "rs.ground with the page's own language works")
for lang, page, kw in (("poster", "data", dict(number="3", label="x", highlight="x")),
                       ("poster", "points", dict(title="x", items=["a", "b"], highlight="x")),
                       ("cutpaper", "cover", dict(title="x", icons=["lucide:wind"]))):
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(lang, dk.blank_deck(13.333, 7.5))
    try:
        getattr(k, page)(k.new_slide(), **kw)
        check(False, "{}.{}: an extra this page never draws is refused, not silently dropped".format(lang, page))
    except TypeError as e:
        check(True, "{}.{}: an extra this page never draws is refused".format(lang, page))
r = _sp.run([sys.executable, str(ROOT / "scripts" / "sigs.py"), "--example", "section", "use"], capture_output=True, text=True)
check(r.returncode == 0 and "Kit.section(" in r.stdout and "# use" in r.stdout,
      "sigs --example: a page name resolves to Kit.<page>, and `use` has a whole-deck scaffold: rc={} {}".format(
          r.returncode, r.stderr[-200:]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
