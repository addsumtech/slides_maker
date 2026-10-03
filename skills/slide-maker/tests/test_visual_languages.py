#!/usr/bin/env python3
"""visual_languages: four complete looks — data, fonts per platform AND per script, contrast, register contracts, page compositions on every canvas and language."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import deckkit as dk, register_surface as rs
import visual_languages as vl
check(set(vl.LANGS) == {"editorial", "soft", "collage", "storybook"}, "four languages")
MAC_ONLY = {"Didot", "Bodoni 72", "Baskerville", "Arial Rounded MT Bold", "Avenir Next", "Helvetica Neue",
            "Bradley Hand", "Noteworthy", "Marker Felt", "Futura", "Optima", "Gill Sans"}
ON_DEMAND = {"Kaiti SC", "Yuanti SC", "Hannotate SC", "Wawati SC", "Libian SC", "HanziPen SC", "Lantinghei SC", "PingFang SC"}
for name, L in vl.LANGS.items():
    both = set(L["fonts"]["both"].values())
    check(not (both & MAC_ONLY), "{}: fonts='both' must not use a Mac-only face: {}".format(name, both & MAC_ONLY))
    for f in both:
        check(not dk._font_substituted(f), "{}: both-platform face {!r} must be installed here".format(name, f))
    check(L["fonts"]["both"]["numeral"] not in ("Georgia", "Constantia", "Hoefler Text"), "{}: numerals in a lining face".format(name))
    pal = L["palette"]
    for ink in [pal["ink"]] + pal["text_accents"]:
        for ground in (pal["ground"], pal["panel"]):
            check(vl._contrast(ink, ground) >= 4.5, "{}: text ink {} on {} is {:.2f}:1".format(name, ink, ground, vl._contrast(ink, ground)))
for scr in ("han", "kana", "hangul"):
    for kind in ("serif", "sans"):
        f = vl.EA_FACES[scr][kind]["mac"]
        check(f not in ON_DEMAND and not dk._font_substituted(f), "{} {} mac face {!r} must be a system face".format(scr, kind, f))
check(vl.script_of("城市菜园") == "han" and vl.script_of("きのテーブル") == "kana" and vl.script_of("木のテーブル") == "kana"
      and vl.script_of("나무 테이블") == "hangul" and vl.script_of("Garden") is None, "script detection")
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("storybook", prs)
s = k.new_slide()
check(s._element.find(".//" + dk.qn("a:tile")) is not None, "storybook paints a grain ground")
r = k.run("나무 테이블", 20, role="body")
check(r[6] == vl.EA_FACES["hangul"]["serif"]["mac"] or r[6] == vl.EA_FACES["hangul"]["sans"]["mac"], "a Hangul run gets a Hangul face: {}".format(r))
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
for name in vl.LANGS:
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
    for name in vl.LANGS:
        for cname, (W, H) in CANV.items():
            for lang, T in TXT.items():
                prs = dk.blank_deck(W, H)
                k = vl.use(name, prs, plan=plan, image_dir=td)
                pages = [
                    ("cover", dict(title=T["title"], kicker=T["kicker"], image="hero")),
                    ("section", dict(number="02", title=T["kicker"])),
                    ("image_text", dict(title=T["kicker"], body=T["body"], image=str(img))),
                    ("quote", dict(quote=T["quote"], attribution=T["attr"])),
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
                                        want = {vl.EA_FACES[scr][x]["mac"] for x in ("serif", "sans")}
                                        check(ea is not None and ea.get("typeface") in want,
                                              "{} {} {} {}: {} run without a {} face".format(name, cname, lang, page, scr, scr))
                crit = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]
                check(not crit, "{} {} {}: lint criticals: {}".format(name, cname, lang, [(f[0], f[2], f[3][:90]) for f in crit][:3]))
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
check(pics and abs(pics[0].left / E - r["rects"]["title"][0]) < 0.05, "the outlined number starts at the column's left edge")
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
    lines, cur = [], ""
    for u in units:
        nxt = (cur + joiner + u) if cur else u
        if cur and u in "，。、；：！？）」』》":
            cur = nxt                         # hangs at the line end, never starts a line
        elif cur and wd(nxt) > width:
            lines.append(cur); cur = u
        else:
            cur = nxt
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
    tb = [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text == title][0]
    run = tb.text_frame.paragraphs[0].runs[0]
    face = (run._r.find(".//" + dk.qn("a:ea")).get("typeface") if cjk else run.font.name)
    ls = _lines(title, run.font.size.pt, face, tb.width / E - 0.056)
    # the renderer never starts a line with closing CJK punctuation — it hangs it on the line before
    for i_ in range(1, len(ls)):
        while ls[i_] and ls[i_][0] in "，。、；：！？）」』》":
            ls[i_ - 1] += ls[i_][0]
            ls[i_] = ls[i_][1:]
    last = ls[-1]
    check(len(ls) == 1 or (len(last) > 2 if cjk else len(last.split()) > 1),
          "{}: widow — {!r} ends with the lone line {!r}".format(name, title, last))

# the collage cover's Chinese title, beside its prints (rendered "楼顶和阳台，/也能长出一/季菜", 2026-10-03)
prs = dk.blank_deck(13.333, 7.5)
k = vl.use("collage", prs)
s_ = k.new_slide()
ttl = "楼顶和阳台，也能长出一季菜"
k.cover(s_, kicker="城市里的小菜园", title=ttl, subtitle="从一个小花盆开始。", image=[str(_wimg), str(_wimg), str(_wimg)])
tb = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text == ttl][0]
run = tb.text_frame.paragraphs[0].runs[0]
ls = _lines(ttl, run.font.size.pt, run._r.find(".//" + dk.qn("a:ea")).get("typeface"), tb.width / E - 0.056)
for i_ in range(1, len(ls)):
    while ls[i_] and ls[i_][0] in "，。、；：！？）」』》":
        ls[i_ - 1] += ls[i_][0]
        ls[i_] = ls[i_][1:]
check(len(ls) == 1 or len(ls[-1]) > 2, "collage cover: widow {!r} (lines {})".format(ls[-1], ls))

# portrait renders (2026-10-03): an italic quote wrapped to one more line than measured and ran into its
# attribution; a centred Chinese closing title ended on "一株"; cards were drawn at the full column height
prs = dk.blank_deck(5.625, 10.0)
k = vl.use("editorial", prs)
s_ = k.new_slide()
q = "The visitor holds the screwdriver; the volunteer only guides."
r = k.quote(s_, quote=q, attribution="How every repair begins", image=str(_wimg))
qb = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text == q][0]
qr = qb.text_frame.paragraphs[0].runs[0]
it_lines = []
fnt = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Italic.ttf", int(qr.font.size.pt * 10))
cur = ""
for wd_ in q.split(" "):
    nxt = (cur + " " + wd_) if cur else wd_
    if cur and fnt.getlength(nxt) / 10.0 / 72.0 > qb.width / E - 0.056:
        it_lines.append(cur); cur = wd_
    else:
        cur = nxt
it_lines.append(cur)
need = len(it_lines) * qr.font.size.pt * dk._LINT_LINE_H / 72.0
check(qb.height / E + 0.02 >= need, "an italic quote's box holds its italic lines: {:.2f}in for {} lines needing {:.2f}in".format(qb.height / E, len(it_lines), need))
prs = dk.blank_deck(5.625, 10.0)
k = vl.use("soft", prs)
s_ = k.new_slide()
ct = "这个周末，先种下第一株"
k.closing(s_, title=ct, line="几个月后，就有自己的收获。", image=str(_wimg))
tb = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text == ct][0]
run = tb.text_frame.paragraphs[0].runs[0]
ls = _lines(ct, run.font.size.pt, run._r.find(".//" + dk.qn("a:ea")).get("typeface"), tb.width / E - 0.056)
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

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_visual_languages] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
