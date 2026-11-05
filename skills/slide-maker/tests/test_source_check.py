#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""source_check.py — a deck built from the user's own material, held to that material.

What this suite holds the tool to, in both directions:

  · every source format the user hands over is READ (pdf text layer, docx paragraphs + tables, pptx,
    xlsx cell values incl. percent formats, csv, markdown tables) — and an image / scanned PDF / .doc
    is reported UNREADABLE with its reason, never as a clean file;
  · a number typed onto a slide that is not in the files is caught (3,412 → 3,421) and the likely
    source figure is named; a number that IS in the files passes however it is written (12,345 ·
    1.2345万 · a percent cell 0.925 shown as 92.5%);
  · rounding, arithmetic, numbers read off a picture and non-claims are allowed only as RECORDED rows,
    and the gate re-checks each: a source_value must be in the files and round to the slide figure; a
    derived expression must use only file figures and evaluate to the slide figure;
  · page chrome, source-note lines, small counts and the cover date are not claims;
  · the material check finds a total that is not the sum of its rows (and of its columns), shares that
    do not reach 100%, and the same table in two files with a cell that disagrees — and stays quiet on
    a correct table, rounded shares, and same-layout tables about DIFFERENT things;
  · finding ids are stable across runs, and the gate needs a resolution for each.

Run:  python3 tests/test_source_check.py
"""
import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import pathlib
import subprocess
import sys
import tempfile
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
SC = SCRIPTS / "source_check.py"
sys.path.insert(0, str(SCRIPTS))

for _m in ("pptx", "fitz"):
    try:
        __import__(_m)
    except ImportError:
        print(f"skip: {_m} not installed")
        raise SystemExit(0)

import source_check as S  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else f"{name}  {detail}")
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  {detail}"))


TMP = pathlib.Path(tempfile.mkdtemp(prefix="srccheck-"))


# ───────────────────────────────────────────── fixtures (every format, written by hand)
def write_docx(path, paragraphs, tables=()):
    W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = "".join('<w:p><w:r><w:t>{}</w:t></w:r></w:p>'.format(p) for p in paragraphs)
    for t in tables:
        rows = "".join("<w:tr>" + "".join('<w:tc><w:p><w:r><w:t>{}</w:t></w:r></w:p></w:tc>'.format(c)
                                          for c in row) + "</w:tr>" for row in t)
        body += "<w:tbl>{}</w:tbl>".format(rows)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", '<?xml version="1.0"?><w:document {}><w:body>{}</w:body></w:document>'.format(W, body))


def write_xlsx(path, sheet, rows, pct_cells=()):
    """rows: list of lists; str → shared string, number → value. pct_cells: refs styled as 0.0%."""
    X = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    shared, cells_xml = [], []
    for r, row in enumerate(rows, 1):
        cs = []
        for c, v in enumerate(row):
            ref = "{}{}".format(chr(65 + c), r)
            if isinstance(v, str):
                shared.append(v)
                cs.append('<c r="{}" t="s"><v>{}</v></c>'.format(ref, len(shared) - 1))
            else:
                style = ' s="1"' if ref in pct_cells else ""
                cs.append('<c r="{}"{}><v>{}</v></c>'.format(ref, style, v))
        cells_xml.append('<row r="{}">{}</row>'.format(r, "".join(cs)))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", '<workbook {} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="{}" sheetId="1" r:id="rId1"/></sheets></workbook>'.format(X, sheet))
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet {}><sheetData>{}</sheetData></worksheet>'.format(X, "".join(cells_xml)))
        z.writestr("xl/sharedStrings.xml", '<sst {}>{}</sst>'.format(X, "".join("<si><t>{}</t></si>".format(s) for s in shared)))
        z.writestr("xl/styles.xml", '<styleSheet {}><numFmts count="1"><numFmt numFmtId="164" formatCode="0.0%"/></numFmts><cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="164"/></cellXfs></styleSheet>'.format(X))


def write_pdf(path, lines):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    font = fitz.Font("cjk")
    page.insert_font(fontname="cjk", fontbuffer=font.buffer)
    for i, ln in enumerate(lines):
        page.insert_text((50, 80 + 24 * i), ln, fontname="cjk", fontsize=12)
    doc.save(str(path))


def write_deck(path, slides):
    """slides: list of lists of text lines; each line a text box. Adds a '{n} / {N}' footer."""
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for n, lines in enumerate(slides, 1):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        for i, ln in enumerate(lines):
            s.shapes.add_textbox(Inches(0.8), Inches(0.6 + 0.9 * i), Inches(11), Inches(0.8)).text_frame.text = ln
        s.shapes.add_textbox(Inches(12), Inches(7.0), Inches(1), Inches(0.3)).text_frame.text = "{} / {}".format(n, len(slides))
    prs.save(str(path))


D = TMP / "deck"
D.mkdir()
(D / "annual.md").write_text(
    "# 青禾社区图书馆 2025 年度报告\n\n"
    "2025 年借阅量 12,345 册，2024 年为 10,500 册。读者满意度 92.5%。\n\n"
    "| 分馆 | 借阅量 | 占比 |\n|---|---|---|\n"
    "| 东区 | 5,000 | 40% |\n| 西区 | 4,345 | 35% |\n| 北区 | 3,000 | 24% |\n| 合计 | 12,345 | 100% |\n",
    encoding="utf-8")
write_pdf(D / "events.pdf", ["2025 年活动场次 86 场，参与人数 3,412 人。", "开放日 2025年4月23日。"])
write_xlsx(D / "data.xlsx", "2025", [["指标", "数值"], ["借阅量", 12345], ["满意度", 0.925], ["志愿者", 57]],
           pct_cells=("B3",))
write_docx(D / "members.docx", ["新增会员 1,208 人。"],
           tables=[[["项目", "金额"], ["购书", "10"], ["活动", "20"], ["合计", "31"]]])
(D / "branches_v2.csv").write_text("分馆,借阅量,占比\n东区,5000,40%\n西区,4435,35%\n北区,3000,24%\n合计,12345,100%\n",
                                   encoding="utf-8")
(D / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 64)
SOURCES = ["annual.md", "events.pdf", "data.xlsx", "members.docx"]

# ───────────────────────────────────────────── parse_number
print("── parse_number")
p = S.parse_number("1,350")
check("1,350 → 1350, 0 decimals", p and p["value"] == 1350 and p["decimals"] == 0, p)
p = S.parse_number("12%")
check("12% → 12, percent", p and p["value"] == 12 and p["pct"], p)
p = S.parse_number("9.8万")
check("9.8万 → 98000, mantissa 9.8, 1 decimal", p and p["value"] == 98000 and p["mantissa"] == 9.8 and p["decimals"] == 1, p)
p = S.parse_number("−3.5%")
check("−3.5% → magnitude 3.5", p and p["value"] == 3.5 and p["pct"], p)
p = S.parse_number("$4.2B")
check("$4.2B → 4.2e9", p and abs(p["value"] - 4.2e9) < 1, p)
p = S.parse_number("１２％")
check("full-width １２％ → 12%", p and p["value"] == 12 and p["pct"], p)
check("no digits → None", S.parse_number("abc") is None)

# ───────────────────────────────────────────── reading every format
print("── read_source")


def vals_of(name):
    nums, dates = S.read_source(D / name).numbers()
    return {round(v, 6) for v, _, _ in nums}, set(dates and [d for d, _ in dates])


v, _ = vals_of("annual.md")
check("markdown: prose and table numbers", {12345, 10500, 92.5, 5000, 4345, 100} <= v, sorted(v)[:20])
check("markdown: the table is read as a table", len(S.read_source(D / "annual.md").tables) == 1)
v, dts = vals_of("events.pdf")
check("pdf: text-layer numbers", {86, 3412} <= v, v)
check("pdf: a CJK date is one date", (2025, 4, 23) in dts, dts)
v, _ = vals_of("data.xlsx")
check("xlsx: cell values", {12345, 57, 0.925} <= v, v)
check("xlsx: a percent-formatted 0.925 also reads as 92.5", 92.5 in v, v)
v, _ = vals_of("members.docx")
check("docx: paragraph and table numbers", {1208, 10, 20, 31} <= v, v)
check("docx: the table is read as a table", len(S.read_source(D / "members.docx").tables) == 1)
for bad, why in (("shot.png", "image"), ("missing.pdf", "no such")):
    try:
        S.read_source(D / bad)
        check(f"{bad} is UNREADABLE", False, "read without error")
    except S.Unreadable as exc:
        check(f"{bad} is UNREADABLE, saying why", why in str(exc), str(exc))
(D / "old.doc").write_bytes(b"\xd0\xcf\x11\xe0")
try:
    S.read_source(D / "old.doc")
    check(".doc is UNREADABLE", False)
except S.Unreadable as exc:
    check(".doc is UNREADABLE and names the export to ask for", ".docx" in str(exc), str(exc))
import fitz  # noqa: E402
_d = fitz.open()
_d.new_page()
_d.save(str(D / "scan.pdf"))
try:
    S.read_source(D / "scan.pdf")
    check("a PDF with no text layer is UNREADABLE", False)
except S.Unreadable as exc:
    check("a PDF with no text layer is UNREADABLE (scanned)", "scanned" in str(exc), str(exc))

# ───────────────────────────────────────────── the numbers trace
print("── numbers")
write_deck(D / "deck.pptx", [
    ["青禾社区图书馆 2025 年度回顾", "2026年10月30日"],                                   # cover date: not a claim
    ["借阅量 12,345 册", "满意度 92.5%", "活动 86 场", "新增会员 1,208 人", "志愿者 57 人"],  # all in the files
    ["借阅量增长 17.6%", "约 1.2 万册", "5 个分馆", "来源：2025 年度报告 p.3"],              # derived · rounded · count · source line
    ["参与人数 3,421 人", "开放日 2025年4月23日"],                                         # mistyped · a date in the pdf
])
res = S.trace(D / "deck.pptx", SOURCES, base=D)
unt = sorted((s, t) for s, t, _, _ in res["untraced"])
check("untraced = the rounded, the derived and the mistyped number — nothing else",
      unt == [(3, "1.2"), (3, "17.6%"), (4, "3,421")] or unt == [(3, "1.2 万"), (3, "17.6%"), (4, "3,421")]
      or {t for _, t in unt} >= {"17.6%", "3,421"} and len(unt) == 3, unt)
near = {t: n for _, t, _, n in res["untraced"]}
check("the mistyped 3,421 names 3,412 as the likely source",
      any("3,412" in n[1] and "digits" in n[3] for n in near.get("3,421", [])), near.get("3,421"))
_r12 = [n for t, n in near.items() if t.startswith("1.2")]
check("the rounded 1.2万 names 12,345 as 'rounds to it'",
      _r12 and any(n[3] == "rounds to it" for n in _r12[0]), _r12)
check("page footers, the source line, '5 个分馆' and the cover date are not findings",
      not any(t in ("1", "2", "3", "4", "5", "2026-10-30") for _, t in unt), unt)
check("a date that is in the files traces", any(t == "2025-04-23" and h == "file" for _, t, h in res["traced"]),
      res["traced"])
check("cover date counted as such", res["counts"]["cover_date"] == 1, res["counts"])
report = S.format_trace(res)
check("report prints a paste-ready source_value row for the rounded number",
      '"source_value": "12,345"' in report, report)

_tok12 = [t for _, t in unt if t.startswith("1.2")][0]
rows_ok = [
    {"value": "17.6%", "slide": 3, "derived": "(12345-10500)/10500*100"},
    {"value": _tok12, "slide": 3, "source_value": "12,345"},
]
res = S.trace(D / "deck.pptx", SOURCES, rows_ok, base=D)
check("with a derived and a source_value row, only the mistyped number is left",
      [(s, t) for s, t, _, _ in res["untraced"]] == [(4, "3,421")] and not res["row_faults"],
      (res["untraced"], res["row_faults"]))
check("counts name each route", res["counts"]["derived"] == 1 and res["counts"]["source_value"] == 1, res["counts"])

bad_rows = [
    {"value": "17.6%", "slide": 3, "derived": "(12345-10500)/10000*100"},       # wrong arithmetic → 18.45
]
res = S.trace(D / "deck.pptx", SOURCES, bad_rows, base=D)
check("a derived row whose arithmetic does not give the slide figure is refused",
      any("18.4" in f or "18.5" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": "17.6%", "slide": 3, "derived": "(12345-10490)/10490*100"}], base=D)
check("a derived row using a figure the files do not state is refused, naming it",
      any("10490" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": _tok12, "slide": 3, "source_value": "12,354"}], base=D)
check("a source_value that is not in the files is refused", any("not in the source files" in f for f in res["row_faults"]),
      res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": _tok12, "slide": 3, "source_value": "10,500"}], base=D)
check("a source_value that does not round to the slide figure is refused",
      any("does not round" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": "3,421", "slide": 4, "not_a_claim": "x"}], base=D)
check("not_a_claim without a real reason is refused", any("reason" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": "999", "slide": 2, "from_image": "shot.png"}], base=D)
check("a row that matches no number on its slide is flagged as stale",
      any("matches no number" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": "3,421", "slide": 4, "derived": "1+1", "from_image": "a.png"}], base=D)
check("a row with two routes is refused", any("exactly one" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": "17.6%", "slide": 3, "derived": "__import__('os')"}], base=D)
check("a derived expression is arithmetic only (no names, no calls)",
      any("cannot be evaluated" in f for f in res["row_faults"]), res["row_faults"])
res = S.trace(D / "deck.pptx", SOURCES, [{"value": "3,421", "slide": 4, "from_image": "photo of the sign-in sheet"}], base=D)
check("from_image traces, and is counted as NOT machine-checked",
      res["counts"]["from_image"] == 1 and "NOT machine-checked" in S.format_trace(res), res["counts"])
res = S.trace(D / "deck.pptx", SOURCES, web_claims=["参与人数 3,421 人（官网公告）"], base=D)
check("a web provenance claim carrying the number traces it", not any(t == "3,421" for _, t, _, _ in res["untraced"]),
      res["untraced"])
res = S.trace(D / "deck.pptx", SOURCES + ["shot.png"], base=D)
check("an unreadable source is listed, never silently dropped", "shot.png" in res["unreadable"], res["unreadable"])

write_deck(D / "links.pptx", [["封面"], ["详情见 https://qinghe.org/report2025/p37 · 邮箱 info2026@qinghe.org", "借阅量 12,345 册"]])
res = S.trace(D / "links.pptx", SOURCES, base=D)
check("digits inside a URL or an email address are not claims", res["untraced"] == [],
      [(s_, t) for s_, t, _, _ in res["untraced"]])

# English deck, scale words
D2 = TMP / "en"
D2.mkdir()
(D2 / "memo.txt").write_text("Revenue reached 4,210,000 dollars in FY2025; churn was 3.1%.\n", encoding="utf-8")
write_deck(D2 / "deck.pptx", [["Annual review", "30 October 2026"],
                              ["Revenue $4.21 million", "Churn 3.1%", "Churn 3.4%"], ["Revenue about $4.2 million"]])
res = S.trace(D2 / "deck.pptx", ["memo.txt"], base=D2)
unt = [(s, t) for s, t, _, _ in res["untraced"]]
check("English: '$4.21 million' IS 4,210,000 — traces with no row; the wrong churn and the rounded 4.2 do not",
      sorted(unt) == [(2, "3.4%"), (3, "$4.2 million")], unt)
res = S.trace(D2 / "deck.pptx", ["memo.txt"], [{"value": "$4.2 million", "slide": 3, "source_value": "4,210,000"}], base=D2)
unt = [(s, t) for s, t, _, _ in res["untraced"]]
check("English: '$4.2 million' traces through its source_value row",
      unt == [(2, "3.4%")] and not res["row_faults"], (unt, res["row_faults"]))
check("English: 'October 30, 2026' style cover date is not a finding", res["counts"]["cover_date"] == 1, res["counts"])

# ───────────────────────────────────────────── generality: how real material and decks write numbers
print("── generality")
for text, want in (("学习率 1e-4", 1e-4), ("rate 1.2E+04", 12000.0), ("3.0×10⁴ cells", 30000.0),
                   ("3.0 × 10^4", 30000.0), ("2.5x10^-3 mol", 0.0025)):
    vals = [round(p["value"], 12) for p in S._tokens(S.split_dates(text)[0])]
    check(f"scientific notation is one number: {text!r} → {want}", vals == [want], vals)
for text in ("COVID-19 cases", "GPT-4 baseline", "H-1B visa"):
    check(f"a hyphenated name is not a number: {text!r}", S._tokens(text) == [], S._tokens(text))
for text, want in (("50k users", 50000.0), ("$4.5m raised", 4.5e6), ("€4.5mn", 4.5e6), ("$4.2b", 4.2e9)):
    vals = [p["value"] for p in S._tokens(text)]
    check(f"an abbreviated scale is kept: {text!r} → {want}", vals == [want], vals)
for text in ("4.5m tall", "12 km", "3 kg"):
    vals = [p["value"] for p in S._tokens(text)]
    check(f"a metric unit is not a money scale: {text!r}", all(v < 100 for v in vals), vals)
for text, want in (("2025.10 上线", (2025, 10, 0)), ("2025-10 launch", (2025, 10, 0)), ("2025年10月上线", (2025, 10, 0)),
                   ("in Oct 2025", (2025, 10, 0)), ("October 2025", (2025, 10, 0))):
    check(f"a year-month is a date: {text!r}", want in S.split_dates(text)[1], S.split_dates(text))
check("a price 2025.10 元 is not a date", S.split_dates("售价 2025.10 元")[1] == [], S.split_dates("售价 2025.10 元"))

G = TMP / "gen"
G.mkdir()
(G / "pnl.csv").write_text("line,FY2024,FY2025\nRevenue,38200000,42150000\nGross margin,0.412,0.437\n", encoding="utf-8")
(G / "plan.md").write_text("2025年10月8日上线新系统。满意度 91.2%。\n", encoding="utf-8")
(G / "gbk.csv").write_bytes("区域,销售额\n华东,5230\n华南,3180\n合计,8410\n".encode("gb18030"))
write_deck(G / "deck.pptx", [["Cover"], ["Gross margin 43.7%", "2025.10 新系统上线", "华东 5,230"],
                             ["Revenue chart"]])
from pptx import Presentation as _P  # noqa: E402
from pptx.chart.data import CategoryChartData as _CD  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE as _XT  # noqa: E402
from pptx.util import Inches as _In  # noqa: E402
_prs = _P(str(G / "deck.pptx"))
_cd = _CD(); _cd.categories = ["2024", "2025"]; _cd.add_series("满意度", (0.887, 0.912), number_format="0.0%")
_prs.slides[2].shapes.add_chart(_XT.COLUMN_CLUSTERED, _In(1), _In(2), _In(6), _In(4), _cd)
_cd = _CD(); _cd.categories = ["FY2024", "FY2025"]; _cd.add_series("Revenue ($M)", (38.2, 42.15))
_prs.slides[2].shapes.add_chart(_XT.COLUMN_CLUSTERED, _In(7), _In(2), _In(5), _In(4), _cd)
_prs.save(str(G / "deck.pptx"))
res = S.trace(G / "deck.pptx", ["pnl.csv", "plan.md", "gbk.csv"], base=G)
unt = {(s_, t) for s_, t, _, _ in res["untraced"]}
check("a % on the slide traces to the same value stored as a fraction (0.437 → 43.7%)", (2, "43.7%") not in unt, unt)
check("a year-month on the slide traces to a full date in the file", (2, "2025-10") not in unt and (2, "2025.10") not in unt, unt)
check("a GBK-encoded csv is read", (2, "5,230") not in unt, unt)
check("a %-formatted chart value (0.912) traces to 91.2% in the file", (3, "0.912") not in unt, unt)
check("a chart value with no file source (0.887) is still caught", (3, "0.887") in unt, unt)
check("a chart in $M (38.2) is NOT silently accepted against 38,200,000", (3, "38.2") in unt, unt)
near = {t: n for s_, t, _, n in res["untraced"]}
check("...but the report names the file figure and the unit to record",
      any("38200000" in n[1] or "38,200,000" in n[1] for n in near.get("38.2", [])) and
      '"unit": "M"' in S.format_trace(res), (near.get("38.2"), S.format_trace(res)[-600:]))
res = S.trace(G / "deck.pptx", ["pnl.csv", "plan.md", "gbk.csv"],
              [{"value": "38.2", "slide": 3, "source_value": "38200000", "unit": "M"},
               {"value": "42.15", "slide": 3, "source_value": "42150000", "unit": "M"}], base=G)
check("a source_value row with a declared unit traces a re-scaled chart value",
      not any(t in ("38.2", "42.15") for _, t, _, _ in res["untraced"]) and not res["row_faults"], res["row_faults"])
res = S.trace(G / "deck.pptx", ["pnl.csv", "plan.md", "gbk.csv"],
              [{"value": "38.2", "slide": 3, "source_value": "38200000", "unit": "万"}], base=G)
check("...and a WRONG declared unit is refused", any("does not round" in f for f in res["row_faults"]), res["row_faults"])
_r = S.read_source(G / "gbk.csv")
check("GBK csv labels decode (华东)", any("华东" in t for _, t in _r.lines), _r.lines[:3])

# ───────────────────────────────────────────── the material check
print("── material")
res = S.material(SOURCES + ["branches_v2.csv", "shot.png"], base=D)
kinds = sorted((f["kind"], f["where"]) for f in res["findings"])
check("docx: 10 + 20 ≠ 31 is a total-row finding",
      any(k == "total-row" and "members.docx" in w for k, w in kinds), kinds)
check("annual.md's correct total and its 99% rounded shares raise nothing",
      not any("annual.md" in w and k in ("total-row", "share-not-100") for k, w in kinds), kinds)
conf = [f for f in res["findings"] if f["kind"] == "conflict"]
check("the same table in annual.md and branches_v2.csv with 4,345 vs 4,435 is ONE conflict naming both files",
      len(conf) == 1 and "4,345" in conf[0]["detail"] and "4435" in conf[0]["detail"]
      and "annual.md" in conf[0]["detail"] and "branches_v2.csv" in conf[0]["detail"], conf)
check("branches_v2.csv: 5000+4435+3000 ≠ 12345 is its own total-row finding",
      any(k == "total-row" and "branches_v2.csv" in w for k, w in kinds), kinds)
check("the image is listed as UNREADABLE (NOT checked)", "shot.png" in res["unreadable"])
D4 = TMP / "shapes"
D4.mkdir()
_good = {
    "unit_row.csv": "单位：万元,,\n项目,2024,2025\n人员,120,135\n运营,80,92\n合计,200,227\n注：数据未经审计,,\n",
    "total_first.csv": "Segment,Revenue\nTotal,1000\nA,600\nB,400\n",
    "frac_share.csv": "channel,share\nonline,0.55\nretail,0.30\nother,0.15\n",
    "suffix_total.csv": "科目,金额\n工资,300\n房租,120\n费用合计,420\n",
    "neg.csv": "item,change\nA,-5\nB,12\nC,-3\nNet total,4\n",
    "years_v1.csv": "指标,2024,2025\n借阅,10500,12345\n活动,180,214\n会员,4800,5873\n志愿者,40,57\n",
}
for f, t in _good.items():
    (D4 / f).write_text(t, encoding="utf-8")
write_xlsx(D4 / "years_v2.xlsx", "data", [["指标", "2024", "2025"], ["借阅", 10500, 12345], ["活动", 180, 214],
                                          ["会员", 4800, 5873], ["志愿者", 40, 57]])
_r = S.material(list(_good) + ["years_v2.xlsx"], base=D4)
check("correct tables of other shapes raise nothing (a unit row above, year headers, total first, "
      "fractions, '费用合计', 'Net total', a csv and an xlsx that agree)", _r["findings"] == [],
      [(f["kind"], f["where"], f["detail"]) for f in _r["findings"]])
for f, old, new, kind in (("unit_row.csv", "合计,200,227", "合计,200,229", "total-row"),
                          ("total_first.csv", "Total,1000", "Total,1100", "total-row"),
                          ("frac_share.csv", "0.15", "0.25", "share-not-100"),
                          ("suffix_total.csv", "费用合计,420", "费用合计,430", "total-row"),
                          ("neg.csv", "Net total,4", "Net total,14", "total-row")):
    (D4 / ("bad_" + f)).write_text(_good[f].replace(old, new), encoding="utf-8")
    _r = S.material(["bad_" + f], base=D4)
    check(f"a seeded error in {f} is found ({kind})", [x["kind"] for x in _r["findings"]] == [kind],
          [(x["kind"], x["detail"]) for x in _r["findings"]])
write_xlsx(D4 / "years_v3.xlsx", "data", [["指标", "2024", "2025"], ["借阅", 10500, 12354], ["活动", 180, 214],
                                          ["会员", 4800, 5873], ["志愿者", 40, 57]])
_r = S.material(["years_v1.csv", "years_v3.xlsx"], base=D4)
check("a csv and an xlsx of one table with year headers: the cell that differs is a conflict",
      len(_r["findings"]) == 1 and _r["findings"][0]["kind"] == "conflict" and "12354" in _r["findings"][0]["detail"],
      [(x["kind"], x["detail"]) for x in _r["findings"]])
ids1 = [f["id"] for f in res["findings"]]
ids2 = [f["id"] for f in S.material(SOURCES + ["branches_v2.csv"], base=D)["findings"]]
check("finding ids are stable across runs", ids1 == ids2, (ids1, ids2))

D3 = TMP / "mat"
D3.mkdir()
(D3 / "share.csv").write_text("渠道,占比\n线上,50%\n线下,30%\n其他,10%\n", encoding="utf-8")
(D3 / "growth.csv").write_text("渠道,增长率\n线上,50%\n线下,30%\n其他,10%\n", encoding="utf-8")
(D3 / "cols.csv").write_text("季度,线上,线下,合计\nQ1,100,50,150\nQ2,120,60,190\n", encoding="utf-8")
(D3 / "east.csv").write_text("指标,2024,2025\n借阅,100,120\n活动,10,12\n会员,300,320\n志愿者,20,25\n", encoding="utf-8")
(D3 / "west.csv").write_text("指标,2024,2025\n借阅,200,210\n活动,15,18\n会员,500,530\n志愿者,40,41\n", encoding="utf-8")
(D3 / "dec.csv").write_text("项目,占比\nA,33.3%\nB,33.3%\nC,33.3%\n", encoding="utf-8")
res = S.material(["share.csv", "growth.csv", "cols.csv", "east.csv", "west.csv", "dec.csv"], base=D3)
k = [(f["kind"], f["where"]) for f in res["findings"]]
check("shares of 90% are a finding", any(x == "share-not-100" and "share.csv" in w for x, w in k), k)
check("a growth-rate column is not a share column", not any("growth.csv" in w for _, w in k), k)
check("a total COLUMN that is not the sum of its row (120+60≠190) is a finding, the correct row is not",
      [w for x, w in k if x == "total-column"] and all("Q2" in w for x, w in k if x == "total-column"), k)
check("same-layout tables about different branches are NOT conflicts", not any(x == "conflict" for x, _ in k), k)
check("33.3% × 3 = 99.9% is rounding, not a finding", not any("dec.csv" in w for _, w in k), k)

# ───────────────────────────────────────────── the gate function (both runtimes call this)
print("── gate_faults")
content = {"sources": [{"path": s} for s in SOURCES + ["branches_v2.csv"]], "numbers": rows_ok, "material_check": []}
faults, summary = S.gate_faults(content, D, D / "deck.pptx")
check("gate: the mistyped number fails", any("3,421" in f for f in faults), faults)
check("gate: each material finding fails until resolved", sum("unresolved" in f for f in faults) == len(ids1), faults)
content["numbers"] = rows_ok + [{"value": "3,421", "slide": 4, "from_image": "sign-in sheet photo, top row"}]
content["material_check"] = [{"id": i, "resolution": "用户确认 4,345 正确，v2 表为录入错误"} for i in ids1]
faults, summary = S.gate_faults(content, D, D / "deck.pptx")
check("gate: everything traced and resolved → no faults", faults == [], faults)
check("gate summary says what was checked", "traced" in summary and "material" in summary, summary)
content["material_check"].append({"id": "M-000000", "resolution": "an old finding that no longer exists"})
faults, _ = S.gate_faults(content, D, D / "deck.pptx")
check("gate: a resolution for a finding that no longer exists is flagged", any("M-000000" in f for f in faults), faults)
content["material_check"] = [{"id": ids1[0], "resolution": "<which value is right>"}]
faults, _ = S.gate_faults(content, D, D / "deck.pptx")
check("gate: a placeholder resolution does not resolve", any(ids1[0] in f for f in faults), faults)
faults, summary = S.gate_faults({"sources": []}, D, D / "deck.pptx")
check("gate: no user material → no faults, and the summary says nothing was traced",
      faults == [] and "no user material" in summary, summary)
faults, _ = S.gate_faults({"sources": ["nope.pdf"]}, D, D / "deck.pptx")
check("gate: a listed source that does not exist fails", faults and "not found" in faults[0], faults)

# ───────────────────────────────────────────── the Codex gate runs the same rules
print("── codex gate")
import codex_delivery_gate as CG  # noqa: E402
ev = {"content": {"sources": [{"kind": "provided", "path": s, "sha256": "x"} for s in SOURCES],
                  "claim_ledger": [], "numbers": rows_ok, "material_check": []}}
errs = []
CG.check_source_trace(ev, D, D / "deck.pptx", errs)
check("codex: the mistyped number fails through check_source_trace", any("3,421" in e for e in errs), errs)
ev["content"]["claim_ledger"] = [{"claim": "参与人数 3,421 人", "source": "https://example.org/notice", "verified": True}]
ev["content"]["material_check"] = [{"id": i, "resolution": "用户确认 docx 合计应为 30"} for i in
                                   [f["id"] for f in S.material(SOURCES, base=D)["findings"]]]
errs = []
CG.check_source_trace(ev, D, D / "deck.pptx", errs)
check("codex: a web claim-ledger row (URL source) traces it; resolved findings pass", errs == [], errs)
errs = []
CG.check_source_trace({"content": {"sources": [{"kind": "web", "locator": "https://x"}]}}, D, D / "deck.pptx", errs)
check("codex: a web-only deck has nothing to trace against and adds no error", errs == [], errs)

# ───────────────────────────────────────────── CLI
print("── CLI")
(D / ".deck-gates.json").write_text(json.dumps({"content": {"sources": SOURCES, "numbers": rows_ok}}), encoding="utf-8")
out = subprocess.run([sys.executable, str(SC), "numbers", str(D)], capture_output=True, text=True)
check("CLI numbers on a folder holding two decks refuses to guess, naming both",
      out.returncode != 0 and "deck.pptx" in (out.stdout + out.stderr) and "links.pptx" in (out.stdout + out.stderr),
      out.stdout[-300:] + out.stderr[-300:])
out = subprocess.run([sys.executable, str(SC), "numbers", str(D), "--pptx", str(D / "deck.pptx")],
                     capture_output=True, text=True)
check("CLI numbers on the deck folder: exit 1, names 3,421 and prints NEXT",
      out.returncode == 1 and "3,421" in out.stdout and "NEXT:" in out.stdout, out.stdout[-400:] + out.stderr[-300:])
out = subprocess.run([sys.executable, str(SC), "numbers", str(D / "deck.pptx"), "--source"] + [str(D / x) for x in SOURCES],
                     capture_output=True, text=True)
_next = [l for l in out.stdout.splitlines() if l.startswith("NEXT:")]
rerun = subprocess.run(__import__("shlex").split(_next[0].split("then: ", 1)[1]),
                       capture_output=True, text=True) if _next else None
check("CLI numbers on a .pptx: the printed NEXT command runs as printed (keeps --source)",
      rerun is not None and rerun.returncode == 1 and "3,421" in rerun.stdout, (_next, rerun and rerun.stdout[-300:]))
out = subprocess.run([sys.executable, str(SC), "numbers", str(D / "deck.pptx")] +
                     sum([["--source", str(D / x)] for x in SOURCES], []), capture_output=True, text=True)
check("--source repeated once per file keeps EVERY file (a real run lost all but the last: 111 false findings)",
      out.returncode == 1 and "3,421" in out.stdout and "12,345" not in "".join(
          l for l in out.stdout.splitlines() if l.strip().startswith("slide")), out.stdout[-500:])
out = subprocess.run([sys.executable, str(SC), "material", str(D)], capture_output=True, text=True)
check("CLI material on the deck folder: exit 1 with ids and the record shape",
      out.returncode == 1 and "M-" in out.stdout and "material_check" in out.stdout, out.stdout[-400:] + out.stderr[-300:])
out = subprocess.run([sys.executable, str(SC), "material", str(D3 / "east.csv")], capture_output=True, text=True)
check("CLI material on a clean file: exit 0 with NEXT", out.returncode == 0 and "NEXT:" in out.stdout, out.stdout)
out = subprocess.run([sys.executable, str(SC), "read", str(D / "shot.png")], capture_output=True, text=True)
check("CLI read on an image: UNREADABLE, exit 2", out.returncode == 2 and "UNREADABLE" in out.stdout, out.stdout)

# ───────────────────────────────────────────── --write-rows: only the unambiguous rows, tagged auto
# Measured 2026-10-30: the agent hand-typed the rows this report already printed, into JSON, through
# heredocs. --write-rows records those itself; everything a mistyped number could look like stays.
print("── --write-rows")
DW = TMP / "write-rows"
DW.mkdir()
(DW / "report.md").write_text("借阅量 12,345 册。收入 38,200,000 元。人均借阅 4.21 本（东区 4.24 本）。成本 41,000 元。\n",
                              encoding="utf-8")
write_deck(DW / "deck.pptx", [["借阅量约 1.2万 册"], ["收入（百万元）", "38.2"], ["收入 38.2M 元"],
                              ["人均 4.2 本"], ["成本约 4万 元"], ["借阅 12,400 册"]])
(DW / ".deck-gates.json").write_text(json.dumps({"content": {"sources": ["report.md"], "numbers": []}}),
                                     encoding="utf-8")
out = subprocess.run([sys.executable, str(SC), "numbers", str(DW)], capture_output=True, text=True)
check("without the flag: exit 1, and it says how many rows --write-rows would record",
      out.returncode == 1 and "2 of these" in out.stdout and "--write-rows" in out.stdout, out.stdout[-700:])
check("without the flag: the record is untouched",
      json.loads((DW / ".deck-gates.json").read_text(encoding="utf-8"))["content"]["numbers"] == [])
out = subprocess.run([sys.executable, str(SC), "numbers", str(DW), "--write-rows"], capture_output=True, text=True)
rows_w = json.loads((DW / ".deck-gates.json").read_text(encoding="utf-8"))["content"]["numbers"]
by_slide = {r["slide"]: r for r in rows_w}
check("writes exactly the two unambiguous rows (slides 1, 2; 38.2M on slide 3 is in the file as written)",
      sorted(by_slide) == [1, 2], rows_w)
check("a rounded figure: source_value 12,345 for 1.2万",
      by_slide.get(1, {}).get("source_value") == "12,345" and "unit" not in by_slide.get(1, {}), by_slide.get(1))
check("a unit-less chart value: source_value + unit M",
      str(by_slide.get(2, {}).get("source_value")).startswith("38,200,000") and by_slide.get(2, {}).get("unit") == "M",
      by_slide.get(2))
check("every written row is tagged `auto` with the file it came from",
      all("report.md" in str(r.get("auto")) for r in rows_w), rows_w)
check("two candidates (4.21 / 4.24), one significant digit (4万) and within-2% (12,400) are NOT written",
      not ({4, 5, 6} & set(by_slide)), rows_w)
check("after writing: exit 1 and only the three left-over numbers are still named",
      out.returncode == 1 and all(t in out.stdout for t in ("4.2", "4万", "12,400"))
      and "wrote 2 row(s)" in out.stdout, out.stdout[-900:])
res_w = S.trace(DW / "deck.pptx", ["report.md"], rows_w, base=DW)
check("the written rows pass the gate's own re-check (no row faults, 3 untraced left)",
      not res_w["row_faults"] and len(res_w["untraced"]) == 3, (res_w["row_faults"], res_w["untraced"]))
out = subprocess.run([sys.executable, str(SC), "numbers", str(DW), "--write-rows"], capture_output=True, text=True)
check("a second --write-rows adds nothing (no duplicate rows)",
      "nothing unambiguous" in out.stdout and len(json.loads((DW / ".deck-gates.json").read_text(
          encoding="utf-8"))["content"]["numbers"]) == 2, out.stdout[-300:])
out = subprocess.run([sys.executable, str(SC), "numbers", str(DW / "deck.pptx"), "--source", str(DW / "report.md"),
                      "--write-rows"], capture_output=True, text=True)
check("--write-rows on a bare .pptx refuses (exit 2): there is no record to write into",
      out.returncode == 2 and "deck folder" in out.stdout, out.stdout)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
print("[test_source_check] " + ("ok" if not FAIL else f"FAILED: {len(FAIL)} problem(s)"))
raise SystemExit(1 if FAIL else 0)
