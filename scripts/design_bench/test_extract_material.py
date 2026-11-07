#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_material.py — a gallery deck's CONTENT as a material folder, with none of its design.

Run:  python3 scripts/design_bench/test_extract_material.py
"""
import io
import pathlib
import re
import sys
import tempfile

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract_material as EM  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  %s" % (detail,)))


TMP = pathlib.Path(tempfile.mkdtemp(prefix="extract-material-"))


def png(rgb, size=(800, 600), mode="RGB"):
    b = io.BytesIO()
    Image.new(mode, size, rgb + ((0,) if mode == "RGBA" else ())).save(b, "PNG")
    b.seek(0)
    return b


p = Presentation()
s = p.slides.add_slide(p.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
r = tb.text_frame.paragraphs[0].add_run()
r.text, r.font.size, r.font.name = "季度营收 125.6 亿", Pt(60), "Source Han Serif SC"
r.font.color.rgb = RGBColor(0xE5, 0x09, 0x14)
s.shapes.add_picture(png((200, 30, 30)), Inches(7), Inches(1))
s.notes_slide.notes_text_frame.text = "开场：先讲营收。"
s = p.slides.add_slide(p.slide_layouts[6])
t = s.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(4), Inches(1)).table
t.cell(0, 0).text, t.cell(0, 1).text, t.cell(1, 0).text, t.cell(1, 1).text = "地区", "收入", "北美", "56.1"
cd = CategoryChartData()
cd.categories = ["Q1", "Q2"]
cd.add_series("营收", (118.2, 125.6))
s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(5), Inches(1), Inches(4), Inches(3), cd)
s.shapes.add_picture(png((200, 30, 30)), Inches(1), Inches(4))       # the same image again
s.shapes.add_picture(png((30, 30, 200)), Inches(3), Inches(4))
s.shapes.add_picture(png((180, 120, 40), (200, 200), "RGBA"), Inches(6), Inches(4))    # an icon: design, dropped
s.shapes.add_picture(png((90, 90, 90), (300, 200)), Inches(8), Inches(4))              # a small swatch: dropped
src = TMP / "deck.pptx"
p.save(src)

out = TMP / "out"
res = EM.extract(str(src), title="季度经营复盘", use="季度复盘, 经营汇报, 董事会汇报", out_dir=str(out))
md = (out / "素材.md").read_text(encoding="utf-8")
brief = (out / "测试材料说明.md").read_text(encoding="utf-8")

print("── content")
check("returns counts", res == {"pages": 2, "images": 2, "tables": 1, "charts": 1}, res)
check("text kept", "季度营收 125.6 亿" in md)
check("table kept as a markdown table", "| 地区 | 收入 |" in md and "| 北美 | 56.1 |" in md, md)
check("chart data kept as a table", "Q2" in md and "125.6" in md and "营收" in md, md)
check("speaker notes kept", "开场：先讲营收。" in md)
check("material says it is a pool, not a page plan", "内容池" in md)
check("images exported once each", len(list((out / "images").iterdir())) == 2)
check("icons and small decorative rasters are not material", sorted(f.name for f in (out / "images").iterdir()) == ["img01.png", "img02.png"],
      sorted(f.name for f in (out / "images").iterdir()))
check("each page names its images", re.search(r"img0?1", md) is not None)

print("── no design information")
both = md + brief
check("no hex colours", not re.search(r"#[0-9A-Fa-f]{6}", both))
check("no font names", "Source Han" not in both and "Serif" not in both)
check("no font sizes", not re.search(r"\b60\s*pt\b", both, re.I))
check("brief carries title and use", "季度经营复盘" in brief and "董事会汇报" in brief)
check("brief carries the page count as a length hint", "2" in brief and "页" in brief)

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
