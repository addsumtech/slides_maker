#!/usr/bin/env python3
"""The native visual languages on inputs nobody tuned them on (a generated corpus, 2026-10-05): realistic LONG copy
in English, Chinese and mixed script, long numbers, on the small 10in 16:9, 4:3, square and A4-portrait canvases.

Every page must BUILD — a composition tries its alternative layouts before refusing — and nothing may land past
the page, overlap, or carry a value PowerPoint repairs. The first run of this corpus refused 184 of 1440 pages and
found 26 critical faults (circles off a square page, a mixed-script label running into its note)."""
from __future__ import annotations
import contextlib, io, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk
import visual_languages as vl
import ooxml_safety as ox

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

td = Path(tempfile.mkdtemp())
CANVASES = {"16:9 10in": (10.0, 5.625), "4:3": (10.0, 7.5), "1:1": (7.5, 7.5), "A4 portrait": (8.27, 11.69)}
# realistic LONG copy (Review Focus 2): a 14-word title, a 30-character Chinese title, 4 points of 2 lines
COPY = {
    "en": dict(kicker="Annual review of the repair network",
               title="Why every street deserves a place to fix what it already owns, not throw away",
               subtitle="What twelve months of evenings, benches and borrowed tools taught us",
               items=[("Share the tools", "One drawer of screwdrivers feeds three tables."),
                      ("Open the door", "No booking, no fee, no questions about the object."),
                      ("Keep it walkable", "Ten minutes on foot is the limit we keep."),
                      ("Write every repair down", "A notebook per bench becomes next year's manual.")],
               quote="The visitor holds the screwdriver; the volunteer only guides, and that is the whole evening.",
               attribution="From the volunteer handbook", number="1,250,000",
               label="kilograms kept out of landfill since the first evening", note="Weighed at the door, item by item.",
               line="Bring a neighbour, and bring something broken."),
    "zh": dict(kicker="社区修理网络 · 年度回顾", title="为什么每条街道都值得拥有一个修理自己物品的地方，而不是随手扔掉",
               subtitle="十二个月的夜晚、工作台和借来的工具教会我们的事",
               items=[("共享工具", "一抽屉螺丝刀可以供三张桌子同时使用。"), ("敞开大门", "不用预约，不收费，不问是什么东西。"),
                      ("步行可达", "步行十分钟是我们坚持的距离。"), ("记下每次修理", "每张桌一本笔记，就是明年的培训手册。")],
               quote="来访者握着螺丝刀，志愿者只在旁边指导，这就是整个夜晚的意义所在。", attribution="志愿者手册",
               number="98.6%", label="的物品当晚修好带回家", note="按门口登记的数量统计。", line="带上邻居，也带上坏掉的东西。"),
    "mixed": dict(kicker="AI 2026 路线图", title="用 GPT-5 做 3 件事", subtitle="Q3 计划 v2",
                  items=[("Step 1：数据", "100 万条"), ("Step 2：模型", None)], quote="Make it work, then make it fast.",
                  attribution="Kent Beck", number="$4.2M", label="预算 budget", note="FY2026", line="Q&A"),
}
EXTRA = {"ink": {"seal": "茶"}, "poster": {}, "cutpaper": {}, "drafting": {"project": "Repair network, phase 1"}}

for name in vl.NATIVE:
    grounds = list(vl.VARIANTS[name])
    for ci, (cname, (W, H)) in enumerate(CANVASES.items()):
        for lang, T in COPY.items():
            g = grounds[(ci + len(lang)) % len(grounds)]            # every ground meets every canvas somewhere
            tag = "{}/{}/{}/{}".format(name, g, cname, lang)
            prs = dk.blank_deck(W, H)
            with contextlib.redirect_stdout(io.StringIO()):
                k = vl.use(name, prs, ground=g)
            pages = [("cover", dict(kicker=T["kicker"], title=T["title"], subtitle=T["subtitle"])),
                     ("section", dict(number="02", kicker=T["kicker"], title=T["title"])),
                     ("points", dict(kicker=T["kicker"], title=T["title"], items=T["items"])),
                     ("quote", dict(quote=T["quote"], attribution=T["attribution"])),
                     ("data", dict(number=T["number"], label=T["label"], note=T["note"])),
                     ("closing", dict(title=T["title"], line=T["line"]))]
            built = 0
            for page, fields in pages:
                ex = dict(EXTRA[name])
                if name == "ink" and lang == "en":
                    ex = {}
                try:
                    getattr(k, page)(k.new_slide(), **fields, **ex)
                    built += 1
                except vl.VLTextOverflow as e:
                    check(False, "{} {}: realistic long copy was refused: {}".format(tag, page, str(e)[:160]))
            check(built == len(pages), "{}: every page built ({}/{})".format(tag, built, len(pages)))
            p = td / "g_{}_{}_{}_{}.pptx".format(name, g, cname.replace(" ", "").replace(":", ""), lang)
            prs.save(str(p))
            with contextlib.redirect_stdout(io.StringIO()):
                crit = [f_ for f_ in dk.lint_layout(prs, verbose=False) if f_[1] == "CRITICAL"]
            check(not crit, "{}: no critical layout fault: {}".format(tag, [(c[0], c[2], c[3][:80]) for c in crit[:3]]))
            check(ox.xml_findings(str(p)) == [], "{}: PowerPoint-safe: {}".format(tag, ox.xml_findings(str(p))[:2]))
            check(ox.beyond_page(prs) == [], "{}: nothing past the page: {}".format(tag, ox.beyond_page(prs)[:2]))


# ── what the RENDERS of the fallback layouts showed (each was green on every gate above) ──
import display_type as _dt
EMU = 914400.0
def rect_of(sh):
    return (sh.left / EMU, sh.top / EMU, sh.width / EMU, sh.height / EMU)
def meet(a, b, pad=0.0):
    return a[0] < b[0] + b[2] + pad and b[0] < a[0] + a[2] + pad and a[1] < b[1] + b[3] + pad and b[1] < a[1] + a[3] + pad
def texts(s):
    return [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0]
# 1. a number never breaks across lines: its glyphs fit its box (poster's 1,250,000 rendered as "1,250, / 000")
for name in vl.NATIVE:
    for W, H in ((10.0, 5.625), (7.5, 7.5)):
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(name, dk.blank_deck(W, H))
        s = k.new_slide()
        try:
            k.data(s, number="1,250,000", label="kilograms kept out of landfill")
        except vl.VLTextOverflow:
            check(True, "{} {}x{}: 1,250,000 refused rather than broken (this machine's faces)".format(name, W, H))
            continue
        num = max((sh for sh in texts(s) if sh.text_frame.text.strip() == "1,250,000"),
                  key=lambda sh: sh.text_frame.paragraphs[0].runs[0].font.size.pt)
        run = num.text_frame.paragraphs[0].runs[0]
        gw = _dt._glyph_width("1,250,000", run.font.size.pt, run.font.name, bool(run.font.bold)) or 0
        check(gw <= num.width / EMU - dk.TEXT_INSET_LR + 0.02,
              "{} {}x{}: 1,250,000 fits its box on one line ({:.2f} vs {:.2f}in)".format(name, W, H, gw, num.width / EMU))
# 2. ink's sun and moon never sit on words (the horizontal fallback put the sun on the closing title)
for W, H in ((10.0, 5.625), (13.333, 7.5), (7.5, 7.5)):
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("ink", dk.blank_deck(W, H))
    for page, kw in (("cover", dict(title=COPY["zh"]["title"], subtitle=COPY["zh"]["subtitle"])),
                     ("closing", dict(title=COPY["zh"]["title"], line=COPY["zh"]["line"])),
                     ("quote", dict(quote=COPY["zh"]["quote"], attribution="志愿者手册"))):
        s = k.new_slide()
        getattr(k, page)(s, **kw)
        suns = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']")]
        words = [rect_of(sh) for sh in texts(s) if len(sh.text_frame.text.strip()) > 2]
        check(not any(meet(a, b) for a in suns for b in words), "ink {}x{} {}: the sun sits clear of the words".format(W, H, page))
# 3. drafting's parts legend: no balloon on another balloon
for W, H in ((7.5, 7.5), (10.0, 5.625)):
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("drafting", dk.blank_deck(W, H))
    s = k.new_slide()
    k.points(s, kicker=COPY["zh"]["kicker"], title=COPY["zh"]["title"], items=COPY["zh"]["items"])
    balls = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='ellipse']")]
    clash = [(a, b) for i_, a in enumerate(balls) for b in balls[i_ + 1:] if meet(a, b)]
    check(not clash, "drafting {}x{}: no two balloons overlap ({} pairs)".format(W, H, len(clash)))
# 4. cutpaper's roomier cover card does not bury its own sun and cloud
with contextlib.redirect_stdout(io.StringIO()):
    k = vl.use("cutpaper", dk.blank_deck(7.5, 7.5))
s = k.new_slide()
k.cover(s, kicker=COPY["en"]["kicker"], title=COPY["en"]["title"], subtitle=COPY["en"]["subtitle"])
cards = [rect_of(sh) for sh in s.shapes if sh._element.xpath(".//a:prstGeom[@prst='roundRect']")]
card = max(cards, key=lambda r: r[2] * r[3])
deco = [rect_of(sh) for sh in s.shapes if "decor" in sh.name and (sh._element.xpath(".//a:prstGeom[@prst='ellipse']")
                                                                   or sh._element.xpath(".//a:custGeom"))
        and (sh.width / EMU) < 0.6 * 7.5 and sh.top / EMU < card[1] + card[3]]
check(not deco, "cutpaper 1:1 cover: the sun and cloud sit below the card, not under it ({})".format(len(deco)))

# 5. poster's credit-line kicker is measured: a long one wraps and the page starts below it (the extreme corpus
#    found it running into the cover title on a square page)
KICK = "Quarterly review for the neighbourhood repair network and its many volunteers across the city"
for W, H in ((7.5, 7.5), (10.0, 5.625), (13.333, 7.5)):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use("poster", prs)
    k.cover(k.new_slide(), kicker=KICK, title="Make the room smaller")
    k.section(k.new_slide(), number="02", kicker=KICK, title="Why small")
    k.points(k.new_slide(), kicker=KICK, title="Three moves", items=["Share", "Open", "Stay local"])
    with contextlib.redirect_stdout(io.StringIO()):
        crit = [f_ for f_ in dk.lint_layout(prs, verbose=False) if f_[1] == "CRITICAL"]
    check(not crit, "poster {}x{}: a long kicker never runs into the page: {}".format(W, H, [(c[0], c[2]) for c in crit[:3]]))

# 6. a long LATIN token inside Chinese text (a brand, a URL) is measured like any word: it fits its box or the page
#    is refused — never an 8.9in overrun that no gate reads (final review)
for title in ("预算 Supercalifragilisticexpialidocioussupercalifragilistic", "官网 www.example-neighbourhood-repair.org"):
    for W, H in ((10.0, 5.625), (13.333, 7.5)):
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use("poster", dk.blank_deck(W, H))
        s = k.new_slide()
        try:
            k.cover(s, title=title)
        except vl.VLTextOverflow:
            check(True, "poster {}x{}: an unfittable Latin token in a Chinese title is refused".format(W, H))
            continue
        tb = max((sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.top >= 0 and sh.text_frame.text.strip()),
                 key=lambda sh: sh.text_frame.paragraphs[0].runs[0].font.size.pt)
        run = tb.text_frame.paragraphs[0].runs[0]
        widest = max((_dt._glyph_width(wd, run.font.size.pt, "Impact", True) or 0)
                     for wd in tb.text_frame.text.split() if not dk._has_cjk(wd))      # the words as RENDERED
        check(widest <= tb.width / EMU - dk.TEXT_INSET_LR + 0.02,
              "poster {}x{}: every Latin word of a mixed title fits its box ({:.2f} vs {:.2f}in)".format(W, H, widest, tb.width / EMU))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
