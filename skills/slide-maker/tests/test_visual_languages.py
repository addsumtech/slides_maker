#!/usr/bin/env python3
"""visual_languages: four complete looks — data, fonts per platform AND per script, contrast, register contracts, page compositions on every canvas and language."""
from __future__ import annotations
import contextlib, io, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk, register_surface as rs
import visual_languages as vl
# Face-precise checks: their expected values were MEASURED with the macOS faces (and the both-platform ones).
# The ubuntu CI runner has none of them — every name resolves to a DejaVu stand-in there — so those checks
# record a SKIP, printed at the end, instead of failing on the stand-in's widths. Everything else runs.
FACES_HERE = sys.platform == "darwin" and not any(dk._font_substituted(f) for f in (
    "Georgia", "Impact", "Arial Black", "Trebuchet MS", "Songti SC", "Hiragino Sans GB", "AppleMyungjo",
    "Apple SD Gothic Neo"))
skipped: list[str] = []


def check_mac(cond, msg):
    if FACES_HERE:
        check(cond, msg)
    else:
        skipped.append(msg)


check(set(vl.IMAGE_LED) == {"editorial", "soft", "collage", "storybook"}, "four image-led languages")
MAC_ONLY = {"Didot", "Bodoni 72", "Baskerville", "Arial Rounded MT Bold", "Avenir Next", "Helvetica Neue",
            "Bradley Hand", "Noteworthy", "Marker Felt", "Futura", "Optima", "Gill Sans"}
ON_DEMAND = {"Kaiti SC", "Yuanti SC", "Hannotate SC", "Wawati SC", "Libian SC", "HanziPen SC", "Lantinghei SC", "PingFang SC"}
for name, L in vl.LANGS.items():
    both = set(L["fonts"]["both"].values())
    check(not (both & MAC_ONLY), "{}: fonts='both' must not use a Mac-only face: {}".format(name, both & MAC_ONLY))
    for f in both:
        check_mac(not dk._font_substituted(f), "{}: both-platform face {!r} must be installed here".format(name, f))
    check(L["fonts"]["both"]["numeral"] not in ("Georgia", "Constantia", "Hoefler Text"), "{}: numerals in a lining face".format(name))
    pal = L["palette"]
    for ink in [pal["ink"]] + pal["text_accents"]:
        for ground in (pal["ground"], pal["panel"]):
            check(vl._contrast(ink, ground) >= 4.5, "{}: text ink {} on {} is {:.2f}:1".format(name, ink, ground, vl._contrast(ink, ground)))
for scr in ("han", "kana", "hangul"):
    for kind in ("serif", "sans"):
        f = vl.EA_FACES[scr][kind]["mac"]
        check(f not in ON_DEMAND, "{} {} mac face {!r} must not be an on-demand face".format(scr, kind, f))
        check_mac(not dk._font_substituted(f), "{} {} mac face {!r} must be a system face".format(scr, kind, f))
check(vl.script_of("城市菜园") == "han" and vl.script_of("きのテーブル") == "kana" and vl.script_of("木のテーブル") == "kana"
      and vl.script_of("나무 테이블") == "hangul" and vl.script_of("Garden") is None, "script detection")
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("storybook", prs)
s = k.new_slide()
check(s._element.find(".//" + dk.qn("a:tile")) is not None, "storybook paints a grain ground")
r = k.run("나무 테이블", 20, role="body")
check(r[6] in (vl.EA_FACES["hangul"]["serif"][k.platform], vl.EA_FACES["hangul"]["sans"][k.platform]), "a Hangul run gets a Hangul face: {}".format(r))
for bad in (lambda: vl.use("nope", prs), lambda: vl.use("editorial", prs, fonts="win")):
    try:
        bad()
        fails.append("an invalid use() call was accepted")
    except (KeyError, ValueError):
        pass
# Review Focus 4: fonts="mac" refuses a missing Mac face (simulate by a patched table)
saved = dict(vl.LANGS["editorial"]["fonts"]["mac"])
vl.LANGS["editorial"]["fonts"]["mac"]["display"] = "No Such Face 123"
try:
    vl.use("editorial", prs, fonts="mac")
    fails.append("fonts='mac' accepted a face that is not installed")
except ValueError as e:
    check("No Such Face 123" in str(e), str(e))
vl.LANGS["editorial"]["fonts"]["mac"] = saved
# register_surface contracts for the four (they are NOT covered by test_register_surface's PRESET loops)
CANVASES = {"16:9 10in": (10.0, 5.63), "16:9 13.33in": (13.333, 7.5), "4:3": (10.0, 7.5),
            "9:16 portrait": (5.63, 10.0), "1:1": (7.5, 7.5)}
for name in vl.IMAGE_LED:                       # the native four: tests/test_native_languages.py
    check(rs.has(name) and rs.is_bespoke(name), "{} registered".format(name))
    for cname, (W, H) in CANVASES.items():
        p = dk.blank_deck(W, H)
        vl.use(name, p)
        sl = dk.add_slide(p)
        for role in ("cover", "content", "section", "closer"):
            bx, by, bw, bh = rs.ground(sl, name, role=role, index=2)
            check(bw >= W * 0.35 and bh >= H * 0.28 and bx >= 0 and by >= 0 and bx + bw <= W + 1e-6 and by + bh <= H + 1e-6,
                  "{} {} {}: content rect {}".format(name, cname, role, (bx, by, bw, bh)))
        body, _hdr = rs.card(sl, name, 0.6, 0.6, min(4.0, W - 1.2), 2.0, label="Notes")

# ── Task 7: six page compositions on every canvas, in four scripts ──
from PIL import Image
import json
import image_series as ims
TXT = {"en": {"title": "Bring it broken, take it home working", "kicker": "A neighbourhood repair café",
              "body": "Volunteers guide; the visitor holds the screwdriver and leaves with the know-how.",
              "quote": "The wheel taught me patience.", "attr": "A volunteer", "label": "evenings a month", "num": "1"},
       "zh": {"title": "楼顶和阳台，也能长出一季菜", "kicker": "城市里的小菜园", "body": "从一个小花盆开始，不必一下子种满整个阳台。",
              "quote": "每天浇水半小时就够了。", "attr": "一位志愿者", "label": "个周末开始", "num": "1"},
       "ja": {"title": "屋上でも野菜は育つ", "kicker": "都市の小さな菜園", "body": "小さな鉢ひとつから始めれば十分です。",
              "quote": "毎日三十分の水やりで足りる。", "attr": "ボランティア", "label": "回の週末", "num": "1"},
       "ko": {"title": "옥상에서도 채소가 자란다", "kicker": "도시의 작은 텃밭", "body": "작은 화분 하나로 시작하면 충분합니다.",
              "quote": "하루 삼십 분 물주기면 충분하다.", "attr": "자원봉사자", "label": "번의 주말", "num": "1"}}
CANV = {"wide13": (13.333, 7.5), "wide10": (10.0, 5.625), "4:3": (10.0, 7.5), "9:16": (5.625, 10.0), "1:1": (7.5, 7.5)}
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    img = td / "photo.png"
    im = Image.new("RGB", (900, 600))
    im.putdata([(150 + (x * 7 + y * 3) % 90, 110 + (x * 3) % 80, 70 + (y * 5) % 60) for y in range(600) for x in range(900)])
    im.save(img)
    plan = {"art_direction": "warm documentary photography in a community hall, window light",
            "palette": ["F3EBDD", "C98A3D", "2F6F6A"], "render": "photo",
            "slots": [{"id": "hero", "slide": 1, "frame": {"shape": "rect", "w": 6, "h": 4}, "kind": "object",
                       "subject": "a table lamp being repaired on a wooden workbench", "alt": "a lamp",
                       "referent": "generic-concrete", "meaning": "broken things get fixed here, by neighbours"}]}
    Image.open(img).save(td / "slide-01-hero.png")
    for name in vl.IMAGE_LED:
        for cname, (W, H) in CANV.items():
            for lang, T in TXT.items():
                prs = dk.blank_deck(W, H)
                k = vl.use(name, prs, plan=plan, image_dir=td)
                pages = [
                    ("cover", dict(title=T["title"], kicker=T["kicker"], image="hero")),
                    ("section", dict(number="02", title=T["kicker"])),
                    ("image_text", dict(title=T["kicker"], body=T["body"], image=str(img))),
                    ("quote", dict(quote=T["quote"], attribution=T["attr"])),
                    ("quote", dict(quote=T["quote"], attribution=T["attr"], image=str(img))),
                    ("data", dict(number=T["num"], label=T["label"], note=T["body"])),
                    ("closing", dict(title=T["title"], image=str(img))),
                ]
                for page, kw in pages:
                    s = k.new_slide()
                    try:
                        res = getattr(k, page)(s, **kw)
                    except Exception as e:
                        fails.append("{} {} {} {}: {}: {}".format(name, cname, lang, page, type(e).__name__, e))
                        continue
                    check(any(dk.vl_name(sh) == name for sh in s.shapes), "{} {} {}: untagged".format(name, cname, page))
                    for sh in s.shapes:
                        if getattr(sh, "has_text_frame", False):
                            for p in sh.text_frame.paragraphs:
                                for r in p.runs:
                                    scr = vl.script_of(r.text)
                                    if scr:
                                        ea = r._r.find(".//" + dk.qn("a:ea"))
                                        want = {vl.EA_FACES[scr][x][k.platform] for x in ("serif", "sans")}
                                        check(ea is not None and ea.get("typeface") in want,
                                              "{} {} {} {}: {} run without a {} face".format(name, cname, lang, page, scr, scr))
                found = dk.lint_layout(prs, verbose=False)
                crit = [f for f in found if f[1] == "CRITICAL"]
                check(not crit, "{} {} {}: lint criticals: {}".format(name, cname, lang, [(f[0], f[2], f[3][:90]) for f in crit][:3]))
                # the engine's own spacing must not draw the deck's own spacing warnings (real decks, 2026-10-03:
                # every title sat 0.16in above its body — HEADLINE_CROWDED — and collage quote cards nearly
                # touched their print on a 10in canvas — SLIVER_GAP; the matrix read only CRITICALs)
                warn = [f for f in found if f[2] in ("HEADLINE_CROWDED", "SLIVER_GAP")]
                check(not warn, "{} {} {}: spacing warnings: {}".format(name, cname, lang, [(f[0], f[2], f[3][:70]) for f in warn][:3]))
    # Review Focus 2: an impossible title is refused, naming page and field
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use("editorial", prs)
    try:
        k.cover(k.new_slide(), title="word " * 120)
        fails.append("a 600-character cover title was accepted")
    except vl.VLTextOverflow as e:
        check("cover" in str(e) and "title" in str(e), str(e))
    try:
        k.image_text(k.new_slide(), title="x", body="y", image=str(td / "missing.png"))
        fails.append("a missing image was accepted")
    except FileNotFoundError:
        pass

# ── defects found by LOOKING at rendered decks (2026-10-03) ──
from PIL import ImageFont  # noqa: E402
E = 914400.0
def _norm(x):                    # a title set as clause lines is one paragraph per line
    return x.replace("\n", "").replace("\v", "").replace(" ", "")
def _runs(slide):
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False):
            for p_ in sh.text_frame.paragraphs:
                for r_ in p_.runs:
                    yield sh, r_
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("soft", prs)
for page, kw in (("section", dict(number="02", kicker="How it works", title="We fix it with you, not for you")),
                 ("data", dict(number="1", label="evening a month", note="Short enough to fit around work."))):
    s = k.new_slide()
    getattr(k, page)(s, **kw)
    ovals = [sh for sh in s.shapes if sh.shape_type == 1 and "+decor" in (sh.name or "") or (sh.name or "").startswith("deckkit-decor")]
    texts = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() not in ("", "02", "1")]
    for o in ovals:
        for t in texts:
            ox = min(o.left + o.width, t.left + t.width) - max(o.left, t.left)
            oy = min(o.top + o.height, t.top + t.height) - max(o.top, t.top)
            check(not (ox > 0.05 * E and oy > 0.05 * E), "soft {}: the colour disc lies under {!r} (it belongs behind the number only)".format(page, t.text_frame.text[:20]))
# the outlined number is sized to its own aspect and left-aligned with the column
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("collage", prs)
s = k.new_slide()
r = k.section(s, number="02", kicker="How it works", title="We fix it with you")
pics = [sh for sh in s.shapes if sh.shape_type == 13]
check_mac(pics and abs(pics[0].left / E - r["rects"]["title"][0]) < 0.05, "the outlined number starts at the column's left edge")
# Chinese has no italics; collage CJK display is heavy
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("storybook", prs)
s = k.new_slide()
k.quote(s, quote="每天浇水半小时就够了。", attribution="A gardener")
for sh, r_ in _runs(s):
    if dk._has_cjk(r_.text):
        check(not r_.font.italic, "a CJK run must not be italic: {!r}".format(r_.text))
    elif r_.text == "A gardener":
        check(r_.font.italic, "the Latin attribution keeps its italic")
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("collage", prs)
s = k.new_slide()
k.cover(s, title="楼顶和阳台，也能长出一季菜")
check(any(r_.font.bold for sh, r_ in _runs(s) if "楼顶" in r_.text), "a CJK collage title is bold (Impact has no CJK)")
# no widow: the last line of a title is never a lone short word / one or two CJK characters
def _lines(text, size, face, width):
    fnt = ImageFont.truetype(str(dk._font_file(face)), max(8, int(size * 10)))
    wd = lambda t: fnt.getlength(t) / 10.0 / 72.0
    units = list(text) if dk._has_cjk(text) else text.split(" ")
    joiner = "" if dk._has_cjk(text) else " "
    hang, close = "，。、；：！？．", "）」』》】〉〕"      # LibreOffice, probed 2026-10-03
    lines, cur = [], ""
    for u in units:
        nxt = (cur + joiner + u) if cur else u
        if not cur or wd(nxt) <= width:
            cur = nxt
        elif u in hang and wd(cur) <= width:
            cur = nxt                         # ONE mark hangs at the line end
        elif u in hang + close:               # a bracket or a second mark takes the hung mark and the
            n_ = len(cur) - len(cur.rstrip(hang))   # ideograph before it down: "一二三四五 / 六。」"
            n_ = n_ + 1 if len(cur) > n_ + 1 else n_
            if 0 < n_ < len(cur):
                lines.append(cur[:-n_]); cur = cur[-n_:] + u
            else:
                cur = nxt
        else:
            lines.append(cur); cur = u
    return lines + [cur]
_wtd = Path(tempfile.mkdtemp())
_wimg = _wtd / "photo.png"
_im = Image.new("RGB", (900, 600))
_im.putdata([(150 + (x * 7 + y * 3) % 90, 110 + (x * 3) % 80, 70 + (y * 5) % 60) for y in range(600) for x in range(900)])
_im.save(_wimg)
for name, title, cjk in (("editorial", "We fix it with you, not for you", False), ("storybook", "工具其实很少，门槛也很低", True),
                         ("collage", "工具其实很少", True)):
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use(name, prs)
    s = k.new_slide()
    r = (k.section(s, number="02", title=title) if not cjk else k.image_text(s, title=title, body="一把小铲、一个喷壶。", image=str(_wimg)))
    tb = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and _norm(sh.text_frame.text) == _norm(title)][0]
    run = tb.text_frame.paragraphs[0].runs[0]
    face = (run._r.find(".//" + dk.qn("a:ea")).get("typeface") if cjk else run.font.name)
    ls = [l_ for p_ in tb.text_frame.paragraphs for l_ in _lines(p_.text, run.font.size.pt, face, tb.width / E - 0.056)]
    last = ls[-1]
    check(len(ls) == 1 or (len(last) > 2 if cjk else len(last.split()) > 1),
          "{}: widow — {!r} ends with the lone line {!r}".format(name, title, last))

# the collage cover's Chinese title, beside its prints (rendered "楼顶和阳台，/也能长出一/季菜", 2026-10-03)
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("collage", prs)
s_ = k.new_slide()
ttl = "楼顶和阳台，也能长出一季菜"
k.cover(s_, kicker="城市里的小菜园", title=ttl, subtitle="从一个小花盆开始。", image=[str(_wimg), str(_wimg), str(_wimg)])
tb = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and _norm(sh.text_frame.text) == _norm(ttl)][0]
run = tb.text_frame.paragraphs[0].runs[0]
ls = [l_ for p_ in tb.text_frame.paragraphs
      for l_ in _lines(p_.text, run.font.size.pt, run._r.find(".//" + dk.qn("a:ea")).get("typeface"), tb.width / E - 0.056)]
check(len(ls) == 1 or len(ls[-1]) > 2, "collage cover: widow {!r} (lines {})".format(ls[-1], ls))

# portrait renders (2026-10-03): an italic quote wrapped to one more line than measured and ran into its
# attribution; a centred Chinese closing title ended on "一株"; cards were drawn at the full column height
prs = dk.blank_deck(5.625, 10.0)
k = vl.use("editorial", prs)
s_ = k.new_slide()
q = "The visitor holds the screwdriver; the volunteer only guides."
r = k.quote(s_, quote=q, attribution="How every repair begins", image=str(_wimg))
qb = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and _norm(sh.text_frame.text) == _norm(q)][0]
qr = qb.text_frame.paragraphs[0].runs[0]
it_lines = []
import display_type as _dt_it
_gi = _dt_it._italic_file("Georgia", False)          # the installed Georgia Italic file (None on the ubuntu runner)
fnt = ImageFont.truetype(_gi, int(qr.font.size.pt * 10)) if _gi else None
for qp_ in (qb.text_frame.paragraphs if fnt else []):
    cur = ""
    for wd_ in qp_.text.split(" "):
        nxt = (cur + " " + wd_) if cur else wd_
        if cur and fnt.getlength(nxt) / 10.0 / 72.0 > qb.width / E - 0.056:
            it_lines.append(cur); cur = wd_
        else:
            cur = nxt
    it_lines.append(cur)
need = len(it_lines) * qr.font.size.pt * dk._LINT_LINE_H / 72.0
check_mac(fnt is not None and qb.height / E + 0.02 >= need, "an italic quote's box holds its italic lines: {:.2f}in for {} lines needing {:.2f}in".format(qb.height / E, len(it_lines), need))
prs = dk.blank_deck(5.625, 10.0)
k = vl.use("soft", prs)
s_ = k.new_slide()
ct = "这个周末，先种下第一株"
k.closing(s_, title=ct, line="几个月后，就有自己的收获。", image=str(_wimg))
tb = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and _norm(sh.text_frame.text) == _norm(ct)][0]
run = tb.text_frame.paragraphs[0].runs[0]
ls = [l_ for p_ in tb.text_frame.paragraphs
      for l_ in _lines(p_.text, run.font.size.pt, run._r.find(".//" + dk.qn("a:ea")).get("typeface"), tb.width / E - 0.056)]
check(len(ls) == 1 or len(ls[-1]) > 2, "soft portrait closing: widow {!r} (lines {})".format(ls[-1], ls))
for name, page in (("collage", "quote"), ("soft", "quote"), ("soft", "image_text")):
    prs = dk.blank_deck(5.625, 10.0)
    k = vl.use(name, prs)
    s_ = k.new_slide()
    if page == "quote":
        res = k.quote(s_, quote="The visitor holds the screwdriver.", attribution="How it begins")
    else:
        res = k.image_text(s_, title="Tools", body="Shared tools on every bench.", image=str(_wimg))
    ys = [r_[1] for r_ in res["rects"].values()] + [r_[1] + r_[3] for r_ in res["rects"].values()]
    text_h = max(ys) - min(ys)
    cards = [sh for sh in s_.shapes if sh.shape_type == 1 and not getattr(sh, "has_text_frame", False) or
             (sh.shape_type == 1 and getattr(sh, "has_text_frame", False) and not sh.text_frame.text.strip()
              and sh.width / E > 2.0 and sh.height / E > 1.0)]
    for c in cards:
        check(c.height / E <= text_h + 1.0, "{} {} portrait: a card {:.2f}in tall around {:.2f}in of text".format(name, page, c.height / E, text_h))

# ── Task 12 (real decks, 2026-10-03): a display line breaks at its clauses when they fit ──
# "带着坏东西来，带着 / 好东西走" and "Bring it broken. Take / it home working." passed every gate; a reader sees the
# phrase torn in two. When the clauses fit — at the same size in a narrower measure, or a little smaller — the
# breaks land after the clause punctuation; never with more lines than before.
def _drawn_lines(k_, slide, field, text):
    """The lines a text box sets: its paragraphs, each broken by the engine's glyph model at the box width."""
    norm = lambda x: x.replace("\n", "").replace("\v", "").replace(" ", "")
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and norm(sh.text_frame.text) == norm(text):
            out = []
            for p_ in sh.text_frame.paragraphs:
                out += vl._break_lines(k_, field, p_.text, p_.runs[0].font.size.pt, sh.width / E)
            return out
    raise AssertionError("no text box holds {!r}".format(text))
_ph = str(ROOT / "assets" / "vl" / "photo" / "hall-repair.jpg")
for lang_name, W_, H_, field, page, kw, want_first_end in (
        ("soft", 13.333, 7.5, "title", "cover", dict(kicker="社区修理咖啡馆", title="带着坏东西来，带着好东西走", image=_ph), "，"),
        ("collage", 13.333, 7.5, "title", "cover", dict(kicker="社区修理咖啡馆", title="带着坏东西来，带着好东西走", image=[_ph, _ph, _ph]), "，"),
        ("collage", 5.625, 10.0, "title", "cover", dict(kicker="社区修理咖啡馆", title="带着坏东西来，带着好东西走", image=[_ph, _ph]), "，"),
        ("editorial", 13.333, 7.5, "title", "cover", dict(kicker="A repair café", title="Bring it broken. Take it home working.", image=_ph), "."),
        ("soft", 13.333, 7.5, "quote", "quote", dict(quote="The visitor holds the screwdriver; the volunteer only guides.", attribution="How every repair begins", image=_ph), ";"),
        ("storybook", 5.625, 10.0, "title", "cover", dict(kicker="都市の小さな菜園", title="屋上でも、野菜はちゃんと育つ", image=_ph), "、")):
    p_ = dk.blank_deck(W_, H_)
    k_ = vl.use(lang_name, p_)
    s_ = k_.new_slide()
    getattr(k_, page)(s_, **kw)
    ls_ = _drawn_lines(k_, s_, field, kw[field])
    check_mac(all(l_.rstrip().endswith(want_first_end) for l_ in ls_[:-1]),                 # one line is fine too
          "{} {}x{} {}: {} breaks mid-phrase: {}".format(lang_name, W_, H_, page, field, ls_))
# the engine's line model, against the same LibreOffice probe: marks hang, brackets push the ideograph before
# them down ("一二三四五 / 六）") — the model hung brackets too and predicted one line where two rendered
p_ = dk.blank_deck(13.333, 7.5)
k_ = vl.use("editorial", p_)
_w6 = 6 * 24 / 72.0 + vl._INSET + 0.02
_orig_face = k_.ea_face
k_.ea_face = lambda role, text: "Songti SC"
for mark in "，。、；：！？．":
    check_mac(vl._break_lines(k_, "quote", "一二三四五六" + mark, 24, _w6) == ["一二三四五六" + mark],
          "engine line model hangs {}: {}".format(mark, vl._break_lines(k_, "quote", "一二三四五六" + mark, 24, _w6)))
for mark in "）」』》】〉〕":
    check_mac(vl._break_lines(k_, "quote", "一二三四五六" + mark, 24, _w6) == ["一二三四五", "六" + mark],
          "engine line model pushes 六 down with {}: {}".format(mark, vl._break_lines(k_, "quote", "一二三四五六" + mark, 24, _w6)))
for tail in ("。」", "，」", "！？", "」。"):
    check_mac(vl._break_lines(k_, "quote", "一二三四五六" + tail, 24, _w6) == ["一二三四五", "六" + tail],
          "engine line model pushes 六{} down: {}".format(tail, vl._break_lines(k_, "quote", "一二三四五六" + tail, 24, _w6)))
# rendered in LibreOffice (corpus, 2026-10-03): an opening bracket never ends a line; mixed text never hangs
_got = vl._break_lines(k_, "quote", "数据显示，参与者的满意度很高（详见附录）。", 48, 3.57 + vl._INSET)
check_mac(_got == ["数据显示，", "参与者的满", "意度很高", "（详见附", "录）。"], "engine: opening bracket moves down: {}".format(_got))
_got = vl._break_lines(k_, "quote", "2026年的数据（n=120）显示，满意度为 87%。", 28, 7.75 + vl._INSET)
check_mac(len(_got) == 2, "engine: a mark after Latin does not hang (two lines rendered): {}".format(_got))
# Korean wraps at spaces, never between syllables (LibreOffice probe, 2026-10-04)
k_.ea_face = lambda role, text: "Apple SD Gothic Neo"
_got = vl._break_lines(k_, "quote", "옥상에서도 채소가 자란다", 24, 7 * 24 / 72.0 + vl._INSET + 0.02)
check_mac(_got == ["옥상에서도", "채소가 자란다"], "engine: Korean breaks at the space: {}".format(_got))
for _t in ("가나다라마바사아자차", "인공지능기반의료영상재구성"):     # wider than the line: syllable breaks, as rendered
    _got = vl._break_lines(k_, "quote", _t, 24, 6 * 24 / 72.0 + vl._INSET + 0.02)
    check_mac(2 <= len(_got) <= 3 and "".join(_got) == _t,                  # never fewer lines than the 2 rendered
          "engine: an over-wide Korean word breaks between syllables: {}".format(_got))
k_.ea_face = _orig_face
# no clause punctuation, or a clause too long for any line: unchanged, never refused
p_ = dk.blank_deck(13.333, 7.5)
k_ = vl.use("editorial", p_)
k_.cover(k_.new_slide(), title="Bring one broken thing to the hall", image=_ph)
k_.cover(k_.new_slide(), title="A very long first clause that cannot possibly sit on one line of a narrow column, then a tail", image=_ph)

# ── Task 14 generality probe (2026-10-04): an empty page is refused, an explicit line break is measured ──
p_ = dk.blank_deck(13.333, 7.5)
k_ = vl.use("soft", p_)
for kw in (dict(title="", kicker=""), dict(title="   ", kicker=" ")):
    try:
        k_.cover(k_.new_slide(), **kw)
        fails.append("a cover with nothing on it ({}) was built silently".format(kw))
    except ValueError as e:
        check("cover" in str(e), "the refusal names the page: {}".format(e))
k_.cover(k_.new_slide(), title="  ", image=_ph)                      # an image-only cover is a real cover
s_ = k_.new_slide()
r_ = k_.cover(s_, kicker="Two lines", title="Line one\nLine two", subtitle="A subtitle under it")
_tsz = [p__.runs[0].font.size.pt for sh in s_.shapes if getattr(sh, "has_text_frame", False)
        and "Line one" in sh.text_frame.text for p__ in sh.text_frame.paragraphs if p__.runs][0]
check(r_["rects"]["title"][3] >= 2 * _tsz * dk._LINT_LINE_H / 72.0,
      "an explicit line break is measured as two lines: {:.2f}in for {:.0f}pt".format(r_["rects"]["title"][3], _tsz))

# ── Task 13 (a docs-only non-Claude run, 2026-10-04): what it could not find, it guessed ──
import subprocess
def _run(*args):
    return subprocess.run([sys.executable] + list(args), cwd=str(ROOT), capture_output=True, text=True)
# sigs.py resolved `cover` to deckkit.cover (a different call) and knew no `section`/`quote`/`data`
r_ = _run("scripts/sigs.py", "cover")
check("Kit.cover(" in r_.stdout and "deckkit.cover(" in r_.stdout, "sigs cover shows BOTH covers: {}".format(r_.stdout[:300]))
r_ = _run("scripts/sigs.py", "section", "image_text", "quote", "data", "closing", "new_slide", "run")
check(r_.returncode == 0 and all("Kit.{}(".format(n) in r_.stdout for n in ("section", "image_text", "quote", "data", "closing", "new_slide", "run")),
      "sigs resolves every Kit page function: rc={} {}".format(r_.returncode, r_.stderr[:200]))
check("kicker=None" in r_.stdout and "image=None" in r_.stdout, "the Kit page signatures name their keyword fields")
# the palette the register-pixels gate reads was never stated; the run guessed it and was held
r_ = _run("scripts/visual_languages.py", "--gates", "editorial", "--deck", "my-deck", "--for", "a repair café")
_pal = vl.LANGS["editorial"]["palette"]
check(r_.returncode == 0 and "deck_gates.py set " in r_.stdout                 # the deck's path is printed absolute now
      and "my-deck design_plan.visual_language editorial" in r_.stdout
      and "design_plan.palette" in r_.stdout and all(h.upper() in r_.stdout.upper() for h in [_pal["ground"], _pal["ink"]] + list(_pal["text_accents"])),
      "--gates prints the full record with the language's hexes: {}".format(r_.stdout[:400] + r_.stderr[:200]))
check("design.visual_language" in r_.stdout, "--gates names the Codex evidence fields too")
# …and every command it prints RUNS as printed, on a fresh deck folder with a space and CJK in its path
# (2026-10-04: on a fresh folder all five `set` lines failed — the record must be init-ed first)
_fresh = Path(tempfile.mkdtemp()) / "我的 deck"
_fresh.mkdir()
r_ = _run("scripts/visual_languages.py", "--gates", "soft", "--deck", str(_fresh), "--for", "城市小菜园")
_cmds = [l_ for l_ in r_.stdout.splitlines() if l_.startswith("python3 ")]
_rcs = [subprocess.run(c_, shell=True, cwd=str(ROOT), capture_output=True, text=True).returncode for c_ in _cmds]
_rec = json.loads((_fresh / ".deck-gates.json").read_text(encoding="utf-8")) if (_fresh / ".deck-gates.json").exists() else {}
check(_cmds and not any(_rcs) and (_rec.get("design_plan") or {}).get("visual_language") == "soft"
      and "#" in str((_rec.get("design_plan") or {}).get("palette")),
      "--gates commands run verbatim on a fresh folder: rcs={} record={}".format(_rcs, (_rec.get("design_plan") or {}).get("visual_language")))
r_ = _run("scripts/visual_languages.py", "--gates", "soft", "--deck", str(_fresh))
check("deck_gates.py init" not in r_.stdout, "an existing record is not init-ed again")
r_ = _run("scripts/visual_languages.py", "--gates", "soft")
check(r_.returncode != 0 and "--deck" in r_.stderr and "<deck" not in r_.stdout,
      "--gates without --deck refuses instead of printing a placeholder path: {}".format(r_.stdout[:120]))
# the ordinary-page recipe: what new_slide paints, what ground/card return, how to make a run
_ref = (ROOT / "references" / "visual-languages.md").read_text(encoding="utf-8")
for needle in ("--gates", "k.run(", "body.left", "returns the content rect", "paints the language's ground"):
    check(needle in _ref, "references/visual-languages.md never says {!r}".format(needle))
check("autospace" in (ROOT / "references" / "multilingual.md").read_text(encoding="utf-8"),
      "multilingual.md explains the preview gap before ASCII punctuation after Hangul")

# ── Final review (2026-10-04) #1: an outlined numeral is drawn only when its face can draw it ──
import display_type as dt
def _pics_alt(slide):
    return [sh._element.nvPicPr.cNvPr.get("descr") for sh in slide.shapes if sh.shape_type == 13]
def _texts(slide):
    return [sh.text_frame.text for sh in slide.shapes if getattr(sh, "has_text_frame", False)]
p_ = dk.blank_deck(13.333, 7.5)
k_ = vl.use("collage", p_)
try:
    dt.outlined(k_.new_slide(), 1, 1, 2, 1, "三成", color="B23A28", face="Impact")
    fails.append("outlined() drew '三成' in Impact, which has no CJK glyphs (tofu)")
except ValueError as e:
    check("三" in str(e) or "draw" in str(e) or "installed" in str(e), "the refusal names what it cannot draw: {}".format(e))
for num in ("三成", "第一章", "세 번"):
    s_ = k_.new_slide()
    k_.data(s_, number=num, label="label")
    check(num not in _pics_alt(s_) and any(num in t for t in _texts(s_)),
          "collage number {!r} is set as text (outlined would be tofu): pics={} texts={}".format(num, _pics_alt(s_), _texts(s_)))
s_ = k_.new_slide()
k_.section(s_, number="02", title="How it works")
check_mac("02" in _pics_alt(s_), "a Latin collage numeral is still the outlined picture")
_sub = dk._font_substituted
dk._font_substituted = lambda n: True if n in ("Impact", "Arial Black") else _sub(n)
try:
    s_ = k_.new_slide()
    k_.section(s_, number="02", title="How it works")          # Linux: Impact not installed
    check("02" not in _pics_alt(s_) and any("02" in t for t in _texts(s_)),
          "without Impact installed the collage numeral falls back to text instead of refusing the page")
except Exception as e:
    fails.append("a collage page raises when Impact is not installed: {}: {}".format(type(e).__name__, e))
finally:
    dk._font_substituted = _sub

# ── Final review #3: a token wider than the column at the floor size is refused, never collided ──
p_ = dk.blank_deck(13.333, 7.5)
k_ = vl.use("editorial", p_)
try:
    k_.image_text(k_.new_slide(), title="Why torch.nn.functional.scaled_dot_product_attention is fast",
                  body="It fuses three kernels.", image=_ph)
    fails.append("an identifier wider than the column at the floor size was set (it rendered into the body)")
except vl.VLTextOverflow as e:
    check("title" in str(e) and "scaled_dot_product_attention" in str(e), "the refusal names the field and the word: {}".format(e))
k_.image_text(k_.new_slide(), title="데이터품질관리체계구축사업", body="세 개의 팀이 함께합니다.", image=_ph)   # breaks between syllables

# ── Final review #4: the engine hangs a mark only when the deck declares it ──
p_ = dk.blank_deck(13.333, 7.5)
for el in [p_.part._element] + [m._element for m in p_.slide_masters]:
    for node in el.iter():
        if node.get("hangingPunct") is not None:
            node.set("hangingPunct", "0")
_hp = dk.HANG_PUNCT
k_ = vl.use("editorial", p_)
_of = k_.ea_face
k_.ea_face = lambda role, text: "Songti SC"
check_mac(vl._break_lines(k_, "quote", "一二三四五六。", 24, 6 * 24 / 72.0 + vl._INSET + 0.02) == ["一二三四五", "六。"],
      "a deck without hanging punctuation: the mark takes 六 down")
k_.ea_face = _of
dk.HANG_PUNCT = _hp

# ── Final review #6: digits are never set in an old-style figure face (Georgia), whole run or mixed ──
for _ln in ("editorial", "storybook"):
    p_ = dk.blank_deck(13.333, 7.5)
    k_ = vl.use(_ln, p_)
    k_.cover(k_.new_slide(), kicker="Since 2019", title="Repair café 2026", image=_ph)
    k_.section(k_.new_slide(), number="03", title="1984 to 2026")
    k_.closing(k_.new_slide(), title="2026", line="See you on 12 March.")
    k_.quote(k_.new_slide(), quote="We fixed 40 lamps in 3 hours.", attribution="Volunteer, 2025")
    _old = [(sl_i, r_.text, r_.font.name) for sl_i, sl in enumerate(p_.slides, 1) for sh, r_ in _runs(sl)
            if any(c.isdigit() for c in r_.text) and dk.has_oldstyle_figures(r_.font.name or "")]
    check(not _old, "{}: digits set in an old-style figure face: {}".format(_ln, _old[:4]))
    check(not [f for f in dk.lint_layout(p_, verbose=False) if f[2] == "OLDSTYLE_FIGURES"], "{}: OLDSTYLE_FIGURES".format(_ln))
    _r = k_.runs("Repair café 2026", 30, role="display")
    check(len(_r) == 2 and _r[1][0] == "2026" and not dk.has_oldstyle_figures(_r[1][5]), "k.runs splits the digits: {}".format(_r))

# ── Final review (re-graded): images the caller passed are never silently dropped ──
def _refuses(fn, label, words):
    try:
        fn()
        fails.append("{} was accepted".format(label))
    except (ValueError, TypeError) as e:
        check(any(w_ in str(e) for w_ in words), "{}: the refusal says why: {}".format(label, e))
p_ = dk.blank_deck(13.333, 7.5)
k_ = vl.use("collage", p_)
_refuses(lambda: k_.image_text(k_.new_slide(), title="Tools", body="Shared."), "image_text without an image", ("image",))
_refuses(lambda: k_.cover(k_.new_slide(), title="Repair night", image=[_ph] * 5), "a collage cover with 5 images", ("4", "5"))
_refuses(lambda: k_.cover(k_.new_slide(), title="Repair night", image=[]), "an empty image list", ("empty", "image"))
k_e = vl.use("editorial", dk.blank_deck(13.333, 7.5))
_refuses(lambda: k_e.cover(k_e.new_slide(), title="Repair night", image=[_ph, _ph]), "two images on a single-image page", ("one", "1"))
k_.cover(k_.new_slide(), title="Repair night", image=[_ph] * 4)                  # four prints is the collage maximum
k_e.cover(k_e.new_slide(), title="Repair night", image=[_ph])                    # a one-item list is one image

# ── Task 10: bundled samples (the direction preview shows them) ──
A = ROOT / "assets" / "vl"
readme = (A / "README.md").read_text(encoding="utf-8") if (A / "README.md").exists() else ""
check("AI-generated" in readme and "not real people" in readme, "assets/vl/README.md states the images' provenance")
for name in vl.LANGS:
    sp_ = A / "samples" / "{}.jpg".format(name)
    check(sp_.exists(), "a bundled sample for {}".format(name))
    if sp_.exists():
        check(sp_.stat().st_size <= 350 * 1024, "{} sample <= 350 KB".format(name))
        check(Image.open(sp_).size[0] >= 800, "{} sample >= 800px wide".format(name))
for f in vl.SAMPLE_IMAGES.values():
    for x in f:
        check((A / x).exists(), "sample source {} is bundled".format(x))

# a page never writes beside the caller's images (a feathered copy landed in the skill's own assets/)
_ftd = Path(tempfile.mkdtemp())
_src = _ftd / "ill.png"
Image.open(_wimg).save(_src)
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("storybook", prs)
k.cover(k.new_slide(), title="A balcony garden", image=str(_src))
check(sorted(p_.name for p_ in _ftd.iterdir()) == ["ill.png"], "a storybook page wrote beside the source image: {}".format(
    sorted(p_.name for p_ in _ftd.iterdir())))

# ── Task 9: a visual language at the direction gate ──
import directions_diversity as dd, archetypes_html as ah  # noqa: E401,E402
d = vl.direction("collage")
check(d["vl"] == "collage" and d["sample"].startswith("data:image/jpeg;base64,") and d["cover"] in ah._COVERS
      and d["skeleton"] in ah._SKELETONS, "a direction dict: {}".format({k: str(v)[:30] for k, v in d.items()}))
pres = ah.preset_directions(["swiss", "editorial_paper"])
bes = {"name": "repair bench", "bg": "#F3EBDD", "ink": "#3B2F2A", "accent": "#C98A3D", "cover_motif": "<svg></svg>",
       "ambient_motif": "<svg></svg>", "cover": "low-left", "skeleton": "island"}
r = dd.check(pres + [d, bes])
check(not r["colourway_excess"] and not r["no_bespoke"], "a vl direction is styled and the bespoke one still counts: {}".format(r))
r2 = dd.check(pres + [d])
check(r2["no_bespoke"], "a vl direction does NOT satisfy the bespoke requirement")
_htd = Path(tempfile.mkdtemp())
ah.build_directions_html([d] + pres + [bes], str(_htd / "dirs.html"))
html = (_htd / "dirs.html").read_text(encoding="utf-8")
check("<img" in html and "style sample" in html.lower() and "not your content" in html.lower(), "the preview shows the labelled sample")
bad_ = dict(d, sample="javascript:alert(1)")
ah.build_directions_html([bad_] + pres, str(_htd / "bad.html"))
check("javascript:" not in (_htd / "bad.html").read_text(encoding="utf-8"), "a non-image sample is dropped")
for n_ in vl.LANGS:
    check(vl.direction(n_)["name"], "{} has a direction".format(n_))

# ── the bundled samples are FRESH: each JPG was rendered from the deck today's code builds (final review) ──
import json as _json, hashlib as _hl
_man = A / "samples" / "manifest.json"
# on EVERY platform: each language x ground has a bundled sample and a fingerprint (a new ground or language without
# its sample fails CI too); the fingerprint COMPARISON needs macOS, where the samples are built and fonts measured
_stems = {vl._sample_stem(n_, g_) for n_ in vl.LANGS for g_ in vl.VARIANTS[n_]}
_recs = set(_json.loads(_man.read_text(encoding="utf-8"))) if _man.exists() else set()
check(_stems <= _recs, "every language x ground has a fingerprinted sample: missing {}".format(sorted(_stems - _recs)))
check(all((A / "samples" / (st + ".jpg")).exists() for st in _stems), "every language x ground has its sample JPG")
if sys.platform != "darwin":
    print("  skip sample fingerprint comparison: samples are built and fingerprinted on macOS (other platforms measure "
          "fonts differently) — run tests/test_visual_languages.py on a Mac before a release")
else:
    check(_man.exists(), "assets/vl/samples/manifest.json records which deck each sample was rendered from")
    _rec = _json.loads(_man.read_text(encoding="utf-8")) if _man.exists() else {}
    _ftd = Path(tempfile.mkdtemp())
    for n_ in vl.LANGS:
        for g_ in vl.VARIANTS[n_]:
            stem = vl._sample_stem(n_, g_)
            with contextlib.redirect_stdout(io.StringIO()):
                p_ = vl.build_sample(n_, str(_ftd), ground=g_)
            check(_rec.get(stem) == vl.sample_fingerprint(p_),
                  "sample {}.jpg is current with the code that builds it — else rebuild: python3 scripts/"
                  "visual_languages.py --sample <dir>, then the NEXT/then lines it prints".format(stem))

# ── Task 11: the reference names what the code does ──
_ref = (ROOT / "references" / "visual-languages.md")
_doc = _ref.read_text(encoding="utf-8") if _ref.exists() else ""
for needle in list(vl.LANGS) + list(vl.PAGE_FIELDS) + ["seal=", "highlight=", "project=", "icons=", "native_fit", "design_plan.visual_language", "design_plan.vl_fonts",
               "deck_gates.py set", "unverified", "VLTextOverflow", "fonts=\"mac\"", "rs.card", "plan=", "direction(",
               "ground=\"auto\"", "vl_ground", "--ground", "printed board"] + [k_ for n_ in vl.VARIANTS for k_ in vl.VARIANTS[n_]]:
    check(needle in _doc, "references/visual-languages.md never says {!r}".format(needle))
for scr in vl.EA_FACES:
    for kind in ("serif", "sans"):
        for plat in ("mac", "win"):
            check(vl.EA_FACES[scr][kind][plat] in _doc, "the EA face {} is not in the reference".format(vl.EA_FACES[scr][kind][plat]))

if skipped:
    print("  skip {} face-precise check(s): this machine lacks the macOS faces they were measured with "
          "(e.g. {!r})".format(len(skipped), skipped[0][:80]))
print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_visual_languages] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
