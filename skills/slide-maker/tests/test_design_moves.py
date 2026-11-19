#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The design moves of 2026-11-18: headline chassis, type as image, Morph, provenance on one line.

What this suite holds them to:
  · `deckkit.headline()` draws each of its five kinds and returns a body rect on the canvas; `none` keeps
    the title in the outline (a11y_title) and draws none; an unknown kind is refused;
  · `design_plan_record.headline_faults()` passes a deck built as planned and names each planned page
    the built file does not carry; the `headlines:` line is required and parsed in English and Chinese;
  · `display_type()` refuses an undeclared run off the canvas and records a declared one as a bleed;
    `vertical_title()` refuses Latin text and sets eaVert;
  · `anim.morph()` writes Morph with a fade fallback BEFORE <p:timing>, once per slide, and
    `morph_slides()` reads it back; `morph_key()` names a plain shape and refuses a tagged one;
  · `source_note()` records its line count and the lint reports SOURCE CLUTTER on a presented deck only;
  · `plan_rhythm.headline_plan()` proposes kinds deckkit can build, lower_third only with photographs.

Run:  python3 tests/test_design_moves.py
"""
import _hermetic  # noqa: F401,E402
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import deckkit as dk  # noqa: E402
import anim  # noqa: E402
import design_plan_record as DPR  # noqa: E402
import plan_rhythm  # noqa: E402

PASS, FAIL = [], []
TMP = pathlib.Path(tempfile.mkdtemp(prefix="moves-"))


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  %s" % (detail,)))


def raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def photo():
    from PIL import Image
    p = TMP / "photo.png"
    im = Image.new("RGB", (1600, 900))
    im.putdata([(40 + (i % 1600) // 12, 70 + (i // 1600) // 8, 110) for i in range(1600 * 900)])
    im.save(p)
    return str(p)


dk.EAFONT = "Hiragino Sans GB"
IMG = photo()

print("── headline()")
prs = dk.blank_deck()
W, H = dk._slide_size(prs.slides.add_slide(prs.slide_layouts[6]))
prs = dk.blank_deck()
kinds = [("header", "营收与利润率均落在指引之内", {}),
         ("hero", "两级台阶已经发生，第三级写在指引里", {}),
         ("lower_third", "第一次，全尺寸树莓派运行在自家设计的芯片之上", {"image": IMG}),
         ("rail", "真正能感觉到的地方", {}),
         ("none", "970 亿小时", {}),
         ("rail", "A Latin rail headline", {})]
for kind, title, kw in kinds:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    x, y, w, h = dk.headline(s, kind, title, kicker="kicker", **kw)
    check("%s returns a body rect on the canvas" % kind,
          x >= 0 and y >= 0 and w > 1 and h > 0.4 and x + w <= W + 0.01 and y + h <= H + 0.01, (x, y, w, h))
none_slide = prs.slides[4]
visible = [sh for sh in none_slide.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()
           and (sh.top or 0) >= 0]
check("`none` draws no visible title but keeps one for the outline",
      not visible and any((sh.top or 0) < 0 for sh in none_slide.shapes), [sh.name for sh in none_slide.shapes])
rail_cjk = prs.slides[3]
check("a CJK rail title is set vertically",
      any(getattr(sh, "has_text_frame", False) and sh.text_frame._txBody.bodyPr.get("vert") == "eaVert"
          for sh in rail_cjk.shapes))
check("an unknown kind is refused", raises(lambda: dk.headline(prs.slides[0], "banner", "x")))
for (pw, ph), t in [((5.625, 10.0), "两级台阶已经发生，第三级写在指引里"), ((10.0, 7.5), "Two steps up, the third is guided")]:
    pp_ = dk.blank_deck(pw, ph)                     # a hero title that WRAPS — the body must start under its measured end
    sp = pp_.slides.add_slide(pp_.slide_layouts[6])
    bx, by, bw_, bh_ = dk.headline(sp, "hero", t, kicker="Q3")
    dk.text(sp, bx, by, bw_, 0.6, [[("正文" if "台" in t else "Body", 14, dk.DEEP, False, False)]])
    try:
        dk.lint_layout(pp_, strict=True)
        ok_ = True
    except Exception as e:
        ok_ = str(e)
    check("a wrapped hero title (%gx%g) clears the body under it" % (pw, ph), ok_ is True, ok_)
s = prs.slides.add_slide(prs.slide_layouts[6])
dk.display_type(s, -0.4, 1.2, "970", size=300, bleed="the numeral is the page")
anim.morph(s)
dk.lint_layout(prs, strict=True)
deck = TMP / "moves.pptx"
prs.save(str(deck))

print("── headline_faults()")
good = DPR.parse_headlines("headlines: hero 2; lower-third 3; rail 4, 6; none 5 — the turns")
check("the planned chassis on a deck built from headline() passes", DPR.headline_faults(good, str(deck)) == [],
      DPR.headline_faults(good, str(deck)))
wrong = {"pages": {"1": "hero", "2": "lower-third", "3": "rail", "6": "none"}}
f = DPR.headline_faults(wrong, str(deck))
check("each planned page the built file does not carry is named", len(f) == 4, f)
check("...with the kind in the message", all(k in " ".join(f) for k in ("HERO", "LOWER-THIRD", "RAIL", "NO visible")), f)
check("Chinese line parses", DPR.parse_headlines("标题位置：hero 3、7；none 9 — 两个转折")["pages"] == {3: "hero", 7: "hero", 9: "none"})
check("`header — report` parses as header-only",
      DPR.parse_headlines("headlines: header — report: a newspaper masthead") == {"header": "report", "why": "a newspaper masthead"})
v = DPR.validate("### Deck rhythm\nnothing")
check("a plan without the line is refused, naming it", any("headlines:" in x for x in v), v)
v = DPR.validate("### Deck rhythm\nheadlines: hero 3 — only one")
check("a single moved page is refused — headlines move as a family", any("names 1 page" in x for x in v), v)
v = DPR.validate("### Deck rhythm\nheadlines: header — because: I like it")
check("an unknown header-only category is refused", any("category" in x for x in v), v)

print("── display_type() · vertical_title()")
p2 = dk.blank_deck()
s2 = p2.slides.add_slide(p2.slide_layouts[6])
check("an undeclared run off the canvas is refused", raises(lambda: dk.display_type(s2, -0.5, 1, "2016", size=300)))
check("body-size text is refused", raises(lambda: dk.display_type(s2, 1, 1, "2016", size=40)))
t = dk.display_type(s2, -0.5, 1, "2016", size=300, bleed="cropped at the trim")
check("a declared bleed is recorded on the shape", dk._declared_bleed(t), t.name)
inside = dk.display_type(s2, 1, 3.0, "OK", size=90)
check("type that stays on the canvas needs no declaration", not dk._declared_bleed(inside), inside.name)
check("vertical_title refuses Latin text", raises(lambda: dk.vertical_title(s2, 1, 1, 1, 4, "Latin")))

print("── morph")
p3 = dk.blank_deck()
a = p3.slides.add_slide(p3.slide_layouts[6])
b = p3.slides.add_slide(p3.slide_layouts[6])
build = anim.Build(b)
with build.step():
    dk.box(b, 1, 1, 2, 1, fill=dk.DEEP)
build.apply()
anim.morph(b)
kids = [c.tag.split("}")[1] for c in b._element]
check("Morph sits before <p:timing>", kids.index("AlternateContent") < kids.index("timing"), kids)
xml = b._element.xml
check("...with a fade fallback", "p159:morph" in xml and "<p:fade/>" in xml.split("Fallback")[1])
check("a second transition on one slide is refused", raises(lambda: anim.morph(b)))
check("morph_slides reads it back", anim.morph_slides(p3) == [2], anim.morph_slides(p3))
k = anim.morph_key(dk.box(a, 1, 1, 2, 1, fill=dk.DEEP), "hero")
check("morph_key names a plain shape !!key", k.name == "!!hero", k.name)
tagged = dk._tag_chrome(dk.box(a, 1, 3, 2, 0.2, fill=dk.DEEP))
check("morph_key refuses a shape carrying a deckkit tag", raises(lambda: anim.morph_key(tagged, "x")))
p3.save(str(TMP / "morph.pptx"))
from pptx import Presentation  # noqa: E402
check("the file reopens", len(Presentation(str(TMP / "morph.pptx")).slides) == 2)

print("── source note · SOURCE CLUTTER")
p4 = dk.blank_deck()
for i in range(4):
    s4 = p4.slides.add_slide(p4.slide_layouts[6])
    dk.title_bar(s4, "Revenue landed inside guidance %d" % i)
    long_src = ("Q2'26 shareholder letter and the What We Watched report (H1 2026); the letter does not "
                "disclose paid memberships, the viewing report moves to yearly from 2027, so this page does "
                "not estimate the member count") if i == 2 else "Q2'26 shareholder letter"
    dk.source_note(s4, long_src, label="Source")
out = TMP / "src"
out.mkdir()
pp = out / "deck.pptx"
p4.save(str(pp))
names = [sh.name for sh in p4.slides[2].shapes if sh.name.startswith("deckkit-source")]
check("source_note records its measured line count", names and int(names[0].split(":")[1]) >= 2, names)
LINT = [sys.executable, str(SCRIPTS / "lint_deck.py")]
r = subprocess.run(LINT + [str(pp)], capture_output=True, text=True)          # presented is the default
check("a presented deck with a 2-line source gets SOURCE CLUTTER naming the slide",
      "SOURCE CLUTTER" in r.stdout and "slide(s) 3" in r.stdout, r.stdout[-600:])
r = subprocess.run(LINT + [str(pp), "--selfread"], capture_output=True, text=True)
check("a self-read deck does not", "SOURCE CLUTTER" not in r.stdout, r.stdout[-400:])

print("── plan_rhythm.headline_plan()")
rows = plan_rhythm.plan(["cover", "context", "problem", "method", "result", "result", "compare", "takeaway",
                         "next", "close"])
hp = plan_rhythm.headline_plan(rows, images=2)
check("a 10-slide argument moves two or more headlines", len(hp) >= 2, hp)
check("every proposed kind is one deckkit.headline() builds", set(hp.values()) <= set(dk.HEADLINES), hp)
check("no photographs, no lower_third", "lower_third" not in plan_rhythm.headline_plan(rows, images=0).values())
line = plan_rhythm.headline_line(hp)
check("the proposed line parses back to the same pages",
      DPR.parse_headlines(line.replace("<why these pages>", "x"))["pages"] ==
      {i: k.replace("_", "-") for i, k in hp.items()}, line)

print("── cjk_punct(): half-width marks inside a Chinese clause")
CP = {"Hailo-10H, 40 TOPS (INT4), 自带 8 GB 内存, 走 PCIe.": "Hailo-10H, 40 TOPS (INT4), 自带 8 GB 内存，走 PCIe.",
      "营收持平; 利润率下滑": "营收持平；利润率下滑",
      "營收持平 ; 毛利率下滑": "營收持平；毛利率下滑",
      "同比 11.7%; 营业利润率 33.2%": "同比 11.7%; 营业利润率 33.2%",   # after a digit: no gap-making full-width
      "来源: Product Brief": "来源：Product Brief",
      "两路 MIPI 通道, 各 1.5 Gb/s": "两路 MIPI 通道，各 1.5 Gb/s",
      "真的吗?是的!": "真的吗？是的！",
      "16:9 画幅": "16:9 画幅", "10:1 拆股": "10:1 拆股", "Netflix, Inc. 第二季度": "Netflix, Inc. 第二季度",
      "见 https://a.com/x?y=1, 第二页": "见 https://a.com/x?y=1, 第二页",
      "目录 /usr/local/bin, 第二页": "目录 /usr/local/bin, 第二页",
      "東京, そして大阪": "東京, そして大阪", "서울, 부산": "서울, 부산",
      "Revenue grew 13%, margin flat": "Revenue grew 13%, margin flat"}
bad = [(k, dk.cjk_punct(k)) for k, v in CP.items() if dk.cjk_punct(k) != v]
check("Chinese clauses convert; Latin lists, ratios, URLs, paths, Japanese and Korean do not", not bad, bad)
check("cjk_punct is idempotent", all(dk.cjk_punct(dk.cjk_punct(k)) == dk.cjk_punct(k) for k in CP))
import re as _re
check("it never writes a Latin glyph before a full-width mark (preflight's Latin→full-width defect)",
      not any(_re.search(r"[A-Za-z0-9%+\)\]][，；：！？]", dk.cjk_punct(k)) for k in CP))


def _one(eafont, runs):
    old = dk.EAFONT
    dk.EAFONT = eafont
    try:
        p_ = dk.blank_deck()
        return dk.text(p_.slides.add_slide(p_.slide_layouts[6]), 1, 1, 6, 1, runs).text_frame.text
    finally:
        dk.EAFONT = old


R_ = lambda t, *f: (t, 14, dk.DEEP, False, False) + f
check("text() converts across a run seam on a Chinese deck",
      _one("Hiragino Sans GB", [[R_("营收"), R_(", 同比 +13.4%")]]) == "营收，同比 +13.4%")
check("an English deck quoting a Chinese name keeps its comma",
      _one(None, [[R_("Visited 北京, then Shanghai")]]) == "Visited 北京, then Shanghai")
check("a Japanese paragraph split into runs is left alone",
      _one("Hiragino Sans", [[R_("東京,"), R_("そして大阪")]]) == "東京,そして大阪")
check("a MONO run keeps its code punctuation",
      _one("Hiragino Sans GB", [[R_("代码 "), R_("f(a, b)", dk.MONO)]]) == "代码 f(a, b)")
mk = dk._cjk_punct_para([dk.mark(("关键,", 14, dk.DEEP, True, False), "FFE066"), R_("同比")])
check("a mark()ed run keeps its highlight", mk[0][0] == "关键，" and str(getattr(mk[0], "highlight", None)) == "FFE066", mk)

print("── copy tells (preflight + lint)")
import preflight_check as PF  # noqa: E402


def _deck(pages, eafont="Hiragino Sans GB"):
    old = dk.EAFONT
    dk.EAFONT = eafont
    try:
        p_ = dk.blank_deck()
        for lines in pages:
            s_ = p_.slides.add_slide(p_.slide_layouts[6])
            for k, line in enumerate(lines):
                dk.text(s_, 0.6, 0.4 + 0.7 * k, 8.5, 0.6, [[R_(line)]])
        return p_
    finally:
        dk.EAFONT = old


body = "营收同比增长百分之十三，利润率小幅回落，现金流下降近三成，回购创下单季新高。"
clean = _deck([[body], [body], ["来源说明", "[1] 股东信"]])
check("a plain Chinese deck passes", PF.check_copy_tells(clean)[0] == "PASS", PF.check_copy_tells(clean))
st, det = PF.check_copy_tells(_deck([[body, "占比为本 deck 计算"], [body, "倍数为公司公布值，非本文档计算"],
                                      ["来源说明", "占比与增量为本 deck 计算"]]))
check("on-slide self-provenance is named by slide, and the sources page is exempt",
      st == "ADVISORY" and "slide(s) [1, 2]" in det, det)
check("an ordinary 本文档编制于 date line is not self-provenance",
      PF.check_copy_tells(_deck([[body, "本文档编制于 2026 年 7 月 26 日"]]))[0] == "PASS")
check("a 来源 [1] footer on every page does not make every page a sources page",
      "slide(s) [1, 2]" in PF.check_copy_tells(_deck([[body, "来源 [1] 股东信；占比为本 deck 计算"],
                                                      [body, "来源 [2] 报表；本 deck 计算"]]))[1])
one = _deck([["它不是给 I/O 做加法，是做乘法"], [body]])
check("one not-X-but-Y line (the hook) is allowed", PF.check_copy_tells(one)[0] == "PASS", PF.check_copy_tells(one))
two = _deck([["它不是给 I/O 做加法，是做乘法"], ["这不是字数问题，是冲突没找准"]])
check("a second one is named", "2 not-X-but-Y" in PF.check_copy_tells(two)[1], PF.check_copy_tells(two))
en2 = _deck([["It's not a faster board, it's a new platform"], ["This is not a chip, it's a system"]], eafont=None)
check("...in English too", "2 not-X-but-Y" in PF.check_copy_tells(en2)[1], PF.check_copy_tells(en2))
en_ref = _deck([["Margin fell 0.7 points (this deck's own calculation)"]], eafont=None)
check("English on-slide self-reference is named", "self-reference" in PF.check_copy_tells(en_ref)[1])
caps = _deck([["IN-LINE WITH GUIDANCE", body], [body]])
check("an English caps kicker in a Chinese deck is named", "caps line" in PF.check_copy_tells(caps)[1])
check("...not a dated title or citation in caps",
      PF.check_copy_tells(_deck([["1979 · OFF THE WALL", body], ["VASWANI ET AL. · NEURIPS 2017", body]]))[0] == "PASS")
check("...not caps in an English deck",
      PF.check_copy_tells(_deck([["QUARTERLY BUSINESS REVIEW", "Revenue grew thirteen percent and margin held."]],
                                eafont=None))[0] == "PASS")
cp = TMP / "tells.pptx"
caps.save(str(cp))
r = subprocess.run(LINT + [str(cp)], capture_output=True, text=True)
check("the render-time lint prints COPY TELLS (it runs on every render; preflight can be skipped)",
      "COPY TELLS" in r.stdout, r.stdout[-500:])

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
