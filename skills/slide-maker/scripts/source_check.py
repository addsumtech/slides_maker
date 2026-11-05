#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""source_check — hold a deck built from the USER'S OWN material to that material, number by number.

A deck built from someone's annual report, spreadsheet or memo has no web source to refute it against,
so the primary-source spot-check skips it, and the claim ledger and the critic both compare the
slides with what the PLANNER wrote down. A number mistyped while copying it out (3,412 → 3,421), or a
growth rate worked out wrongly, passes all of that. And material that disagrees with itself — a total
that is not the sum of its rows, shares that do not reach 100%, the same figure different in two
files — ships whichever version the planner happened to read first.

Two checks, both local and deterministic (no network, no model):

  numbers   every number on the built slides must TRACE to the user's files: found there as written,
            or recorded in `content.numbers` as one of
              {"value": "1.2万", "slide": 3, "source_value": "12,345"}              rounded / re-unit
              {"value": "38.2", "slide": 4, "source_value": "38,200,000", "unit": "M"}  a chart in $M
              {"value": "17.6%", "slide": 3, "derived": "(12345-10500)/10500*100"}  worked out
              {"value": "57", "slide": 2, "from_image": "volunteers.png (top table)"}  read off a picture
              {"value": "2026", "slide": 1, "not_a_claim": "<why this number is not a claim>"}
            The check re-does the arithmetic: a source_value must be in the files and round to the
            slide's figure; every literal of a `derived` expression must be in the files (or be a
            calendar/unit constant) and the expression must evaluate to the slide's figure. A number
            from web research traces through a provenance row with a `url` whose claim contains it.

  material  the user's files checked against THEMSELVES — tables whose total row/column is not the
            sum of its parts, share columns that do not reach 100%, and the same cell (row label ×
            column header) holding different values in two versions of the same table. Each finding
            gets a stable id; the gate needs a `content.material_check` row resolving every one
            ({"id": "M-3fa2c1", "resolution": "<which value is right and who said so>"}), because
            only the user can say which version is right — the skill never silently picks one.

Read as one number each: 1.2e-3 · 3.0×10⁴ · 50k · $4.5m · 4.21 million · 3.2亿. A % on a slide also
traces to the same value stored as a fraction (0.437), a %-formatted chart value (0.912) to 91.2%, and
a year-month (2025.10 · 2025年10月 · Oct 2025) to any date in that month.

Ignored on the deck side, by rule, not by taste: page chrome (page numbers, a numbered footer —
deck_versions owns that), source-note lines ("Source: …", "来源：…"), bare integers 0–10 with no
unit (counts, list numbers, ordinals) and a full date on the cover slide (the deck's own date).

Readable source formats: .pdf (text layer) .docx .pptx/.potx .xlsx/.xlsm (cached cell values; a
percent-formatted cell also counts ×100) .csv/.tsv .md/.txt/.json/.html/.htm. Anything else — an
image, a scanned PDF, .doc/.xls/.key — is reported as UNREADABLE with the reason, never as clean.

    python3 scripts/source_check.py numbers  <deck-dir> [--pptx deck.pptx]   # reads .deck-gates.json
    python3 scripts/source_check.py numbers  <deck-dir> --write-rows          # + record the unambiguous rows
    python3 scripts/source_check.py numbers  <deck.pptx> --source a.pdf b.xlsx
    python3 scripts/source_check.py material <deck-dir>                      # or: material a.pdf b.xlsx
    python3 scripts/source_check.py read     <file>                          # what a file yields
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
import re
import shlex
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
_SELF = "python3 " + shlex.quote(str(HERE / "source_check.py"))

TEXT_EXT = {".md", ".markdown", ".txt", ".json", ".html", ".htm", ".rst"}
CSV_EXT = {".csv", ".tsv"}
XLSX_EXT = {".xlsx", ".xlsm"}
PPTX_EXT = {".pptx", ".potx"}

# Constants a `derived` expression may use without them being in the files: small integers, and the
# unit / calendar factors a rate or a per-period figure is built from.
FREE_CONSTANTS = {100.0, 1000.0, 10000.0, 1e6, 1e8, 1e9, 12.0, 24.0, 52.0, 60.0, 365.0, 366.0}
SMALL_INT = 10            # a bare integer up to this, with no unit, is a count / list number / ordinal

SCALE = {"万": 1e4, "亿": 1e8, "兆": 1e12, "千": 1e3, "百万": 1e6, "千万": 1e7,
         "k": 1e3, "K": 1e3, "M": 1e6, "B": 1e9, "bn": 1e9, "T": 1e12,
         "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_SCALE_WORD = re.compile(r"\s*(thousand|million|billion|trillion|千万|百万|千)\b", re.I)
_SRC_LINE = re.compile(r"^\s*(?:sources?|资料来源|資料來源|数据来源|數據來源|来源|來源|出处|出處)\s*[:：]", re.I)


class Unreadable(Exception):
    """A source file the check cannot read numbers from — reported with its reason, never as clean."""


# ════════════════════════════════════════════════════════════════════════ numbers
def numbers_in(text):
    """Number tokens as decks and documents write them — deck_versions owns the tokeniser."""
    import deck_versions                                               # noqa: PLC0415
    return deck_versions.numbers_in(text)


def parse_number(tok):
    """'1,350' · '12%' · '9.8万' · '−3.5%' · '$4.2B' → dict(value, mantissa, decimals, pct, scale, unit).

    `value` is the magnitude (sign dropped: "down 3.5%" on a slide and "-3.5%" in a table are the same
    figure); `mantissa` is the number as written before the scale word; `decimals` its written
    precision. None when the token holds no number."""
    t = unicodedata.normalize("NFKC", str(tok or "")).strip()
    m = re.search(r"\d[\d,]*(?:\.\d+)?", t)
    if not m:
        return None
    digits = m.group(0)
    if "," in digits and not re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", digits):
        digits = digits.split(",")[0]                                  # "3,4" is two numbers, not 34
    raw = digits.replace(",", "")
    try:
        mant = float(raw)
    except ValueError:
        return None
    dec = len(raw.split(".")[1]) if "." in raw else 0
    rest = t[m.end():].strip()
    pct = rest.startswith("%") or "百分点" in rest
    unit, scale = "", 1.0
    for word in sorted(SCALE, key=len, reverse=True):
        if rest.startswith(word) and (not word.isalpha() or not word.isascii()
                                      or re.match(re.escape(word) + r"\b", rest)):
            unit, scale = word, SCALE[word]
            break
    return {"value": abs(mant) * scale, "mantissa": abs(mant), "decimals": dec, "pct": pct,
            "scale": scale, "unit": unit, "token": tok}


_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
# 1e-4 · 1.2E+04 · 3.0×10⁴ · 3.0 × 10^4 · 2.5x10^-3 — matched on the RAW text, because NFKC would
# fold "10⁴" into "104" before anyone could read it as a power.
_SCI = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:[eE]([+\-−]?\d+)(?![\w.])|[×xX*]\s*10\s*(?:\^|\*\*)?\s*"
                  r"([+\-−]?\d+|[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+))")
_HYPHEN_NAME = re.compile(r"(?<=[A-Za-z])-\d+[A-Za-z]*")          # COVID-19 · GPT-4 · H-1B
_K = re.compile(r"\s?[kK](?![A-Za-z])")
_MONEY_SCALE = re.compile(r"\s?(mn|m|bn|b)(?![A-Za-z])")
_MONEY_SCALE_VAL = {"m": 1e6, "mn": 1e6, "b": 1e9, "bn": 1e9}


def _sci(raw):
    """(text with scientific numbers blanked, [parsed]) — one value per 1.2e-3 / 3.0×10⁴."""
    out = []

    def _sub(m):
        exp = (m.group(2) or m.group(3)).translate(_SUP).replace("−", "-")
        try:
            val = float(m.group(1)) * 10 ** int(exp)
        except (ValueError, OverflowError):
            return m.group(0)
        out.append({"value": abs(val), "mantissa": abs(val), "decimals": 0, "pct": False, "scale": 1.0,
                    "unit": "", "token": m.group(0).strip(), "sci": True})
        return " " * len(m.group(0))
    return _SCI.sub(_sub, raw), out


def _tokens(line):
    """parse_number over every token of a line: scientific notation as one number, a hyphenated
    name (COVID-19) as no number, and the scale written after a number folded in — "4.21 million",
    "50k", "$4.5m" (m / b only after a currency sign: "4.5m" alone is a length)."""
    raw, out = _sci(line or "")
    t = _HYPHEN_NAME.sub(lambda m: " " * len(m.group(0)), unicodedata.normalize("NFKC", raw))
    cursor = 0
    for tok in numbers_in(t):
        p = parse_number(tok)
        if not p:
            continue
        core = re.search(r"\d[\d,]*(?:\.\d+)?", tok).group(0)
        i = t.find(core, cursor)
        end = -1
        if i >= 0:
            end = i + len(core)
            cursor = end
            while end < len(t) and t[end] in "%万亿兆倍" and p["token"].endswith(t[end]):
                end += 1
        if p["scale"] == 1.0 and not p["pct"] and end >= 0:
            w = _SCALE_WORD.match(t, end)
            k = _K.match(t, end)
            money = _MONEY_SCALE.match(t, end) if re.match(r"[+\-−]?[$€£¥]", tok) else None
            if w:
                word = w.group(1).lower() if w.group(1).isascii() else w.group(1)
                p.update(unit=word, scale=SCALE[word], value=p["mantissa"] * SCALE[word],
                         token=tok + " " + w.group(1) if w.group(1).isascii() else tok + w.group(1))
            elif k:
                p.update(unit="k", scale=1e3, value=p["mantissa"] * 1e3, token=tok + "k")
            elif money:
                sc = _MONEY_SCALE_VAL[money.group(1)]
                p.update(unit=money.group(1), scale=sc, value=p["mantissa"] * sc, token=tok + money.group(1))
        out.append(p)
    return out


def _same(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


# ════════════════════════════════════════════════════════════════════════ dates
_DATE_PATTERNS = [
    re.compile(r"(?<!\d)(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]"),
    re.compile(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)"),
]
_MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
                                        "oct", "nov", "dec"), 1)}
_DATE_EN = [
    re.compile(r"\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+(\d{4})\b", re.I),
    re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b", re.I),
]


_YM_PATTERNS = [
    re.compile(r"(?<![\d.])((?:19|20)\d{2})\s*年\s*(\d{1,2})\s*月(?!\s*\d)"),
    re.compile(r"(?<![\d.])((?:19|20)\d{2})[-/](0?[1-9]|1[0-2])(?![\d.\-/])"),
    # "2025.10" is a month only with two month digits and no unit after it — "2025.10 元" is a price
    re.compile(r"(?<![\d.])((?:19|20)\d{2})\.(0[1-9]|1[0-2])(?![\d.])(?!\s*(?:元|%|％|万|亿|美元|USD|RMB|[A-Za-z]))"),
]
_YM_EN = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+((?:19|20)\d{2})\b", re.I)


def split_dates(line):
    """(line with dates blanked, [(y, m, d), …]) — a date is ONE fact, not three numbers. A
    year-month ("2025.10", "2025年10月", "Oct 2025") is (y, m, 0)."""
    found = []
    t = unicodedata.normalize("NFKC", line or "")

    def _keep(y, m, d, span):
        nonlocal t
        try:
            y, m, d = int(y), int(m), int(d)
        except ValueError:
            return
        if 1 <= m <= 12 and 1 <= d <= 31:
            found.append((y, m, d))
            t = t[:span[0]] + " " * (span[1] - span[0]) + t[span[1]:]

    for rx in _DATE_PATTERNS:
        for m in list(rx.finditer(t)):
            _keep(m.group(1), m.group(2), m.group(3), m.span())
    for m in list(_DATE_EN[0].finditer(t)):
        _keep(m.group(3), _MONTHS[m.group(2)[:3].lower()], m.group(1), m.span())
    for m in list(_DATE_EN[1].finditer(t)):
        _keep(m.group(3), _MONTHS[m.group(1)[:3].lower()], m.group(2), m.span())

    def _keep_ym(y, mo, span):
        nonlocal t
        y, mo = int(y), int(mo)
        if 1 <= mo <= 12:
            found.append((y, mo, 0))
            t = t[:span[0]] + " " * (span[1] - span[0]) + t[span[1]:]

    for rx in _YM_PATTERNS:
        for m in list(rx.finditer(t)):
            _keep_ym(m.group(1), m.group(2), m.span())
    for m in list(_YM_EN.finditer(t)):
        _keep_ym(m.group(2), _MONTHS[m.group(1)[:3].lower()], m.span())
    return t, found


# ════════════════════════════════════════════════════════════════════════ reading sources
class Source:
    """What one file yields: text lines with a locator each, and its tables (lists of row lists)."""

    def __init__(self, path):
        self.path = Path(path)
        self.lines = []            # [(locator, text)]
        self.tables = []           # [{"where": str, "rows": [[str, …], …]}]
        self.extra_values = []     # [(value, locator)] numbers held as cell VALUES (xlsx), not text

    def numbers(self):
        """[(value, token, locator)] — every number this file states, plus its dates as (y,m,d)."""
        out, dates = [], []
        for where, text in self.lines:
            rest, ds = split_dates(text)
            dates.extend((d, where) for d in ds)
            for p in _tokens(rest):
                out.append((p["value"], p["token"], where))
                if p["scale"] != 1.0:                       # "9.8万" also states 9.8
                    out.append((p["mantissa"], p["token"], where))
            for g in re.finditer(r"(?<=[A-Za-z])\d{2,}(?:\.\d+)?", unicodedata.normalize("NFKC", text)):
                out.append((float(g.group(0)), g.group(0), where))   # FY2024 states 2024 too
        for v, where in self.extra_values:
            out.append((abs(v), _fmt(v), where))
        return out, dates


def _fmt(v):
    return ("{:.10g}".format(v)) if isinstance(v, float) else str(v)


_CACHE = {}


def read_source(path):
    """Source for `path`, or raise Unreadable naming why (and what to hand over instead).
    Cached per (path, mtime, size): one gate run reads each file for both checks."""
    p = Path(path)
    if not p.is_file():
        raise Unreadable("no such file")
    st = p.stat()
    key = (str(p.resolve()), st.st_mtime_ns, st.st_size)
    if key not in _CACHE:
        try:
            _CACHE[key] = _read_source(p)
        except Unreadable as exc:
            _CACHE[key] = exc
    hit = _CACHE[key]
    if isinstance(hit, Unreadable):
        raise hit
    return hit


def _read_source(p):
    ext = p.suffix.lower()
    src = Source(p)
    try:
        if ext == ".pdf":
            _read_pdf(p, src)
        elif ext == ".docx":
            _read_docx(p, src)
        elif ext in PPTX_EXT:
            _read_pptx(p, src)
        elif ext in XLSX_EXT:
            _read_xlsx(p, src)
        elif ext in CSV_EXT:
            _read_csv(p, src)
        elif ext in TEXT_EXT:
            _read_text(p, src)
        elif ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".tif", ".tiff", ".bmp"}:
            raise Unreadable("an image has no text layer — numbers read off it go in content.numbers "
                             "as from_image rows")
        else:
            raise Unreadable("{} is not a format this check reads (export it as .pdf / .docx / "
                             ".xlsx / .csv / .md)".format(ext or "a file without an extension"))
    except Unreadable:
        raise
    except Exception as exc:                                           # a damaged file, a bad zip
        raise Unreadable("could not be opened ({}: {})".format(type(exc).__name__, exc))
    if not src.lines and not src.extra_values:
        raise Unreadable("no text found in it" + (" — a scanned PDF has no text layer; numbers read "
                                                  "off it go in content.numbers as from_image rows"
                                                  if ext == ".pdf" else ""))
    return src


def _read_pdf(p, src):
    import fitz                                                        # noqa: PLC0415
    with fitz.open(str(p)) as doc:
        for i, page in enumerate(doc, 1):
            for ln in page.get_text().splitlines():
                if ln.strip():
                    src.lines.append(("p.{}".format(i), ln.strip()))


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _wtext(el):
    return "".join(t.text or "" for t in el.iter(_W + "t")).strip()


def _read_docx(p, src):
    with zipfile.ZipFile(str(p)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(_W + "body")
    n_par = n_tab = 0
    for el in (body if body is not None else []):
        if el.tag == _W + "p":
            n_par += 1
            t = _wtext(el)
            if t:
                src.lines.append(("¶{}".format(n_par), t))
        elif el.tag == _W + "tbl":
            n_tab += 1
            rows = [[_wtext(tc) for tc in tr.findall(_W + "tc")] for tr in el.findall(_W + "tr")]
            where = "table {}".format(n_tab)
            src.tables.append({"where": where, "rows": rows})
            for r, row in enumerate(rows, 1):
                src.lines.append(("{} row {}".format(where, r), " | ".join(row)))


def _read_pptx(p, src):
    from pptx import Presentation                                      # noqa: PLC0415
    import deck_versions as dv                                         # noqa: PLC0415
    prs = Presentation(str(p))
    for i, slide in enumerate(prs.slides, 1):
        n_tab = 0
        for sh in dv._walk(slide.shapes):
            if getattr(sh, "has_table", False) and sh.has_table:
                n_tab += 1
                rows = [[c.text_frame.text.strip() for c in row.cells] for row in sh.table.rows]
                src.tables.append({"where": "slide {} table {}".format(i, n_tab), "rows": rows})
            for ln in dv._shape_lines(sh):
                src.lines.append(("slide {}".format(i), ln))
        try:
            if slide.has_notes_slide:
                for ln in (slide.notes_slide.notes_text_frame.text or "").splitlines():
                    if ln.strip():
                        src.lines.append(("slide {} notes".format(i), ln.strip()))
        except Exception:
            pass


_X = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PCT_BUILTIN = {9, 10}


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _read_xlsx(p, src):
    with zipfile.ZipFile(str(p)) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(_X + "si"):
                shared.append("".join(t.text or "" for t in si.iter(_X + "t")))
        pct_xf = set()
        if "xl/styles.xml" in names:
            st = ET.fromstring(z.read("xl/styles.xml"))
            custom_pct = {int(f.get("numFmtId")) for f in st.iter(_X + "numFmt")
                          if "%" in (f.get("formatCode") or "")}
            xfs = st.find(_X + "cellXfs")
            for i, xf in enumerate(xfs if xfs is not None else []):
                fid = int(xf.get("numFmtId") or 0)
                if fid in _PCT_BUILTIN or fid in custom_pct:
                    pct_xf.add(i)
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels}
        for sh in wb.iter(_X + "sheet"):
            tgt = target.get(sh.get(_R + "id"), "")
            path = "xl/" + tgt.lstrip("/").replace("xl/", "", 1) if not tgt.startswith("/xl/") else tgt[1:]
            if path not in names:
                continue
            name = sh.get("name") or "sheet"
            grid = {}
            for c in ET.fromstring(z.read(path)).iter(_X + "c"):
                ref, typ = c.get("r") or "", c.get("t")
                v = c.find(_X + "v")
                if typ == "inlineStr":
                    text = "".join(t.text or "" for t in c.iter(_X + "t"))
                elif v is None:
                    continue
                elif typ == "s":
                    text = shared[int(v.text)] if v.text and int(v.text) < len(shared) else ""
                elif typ in ("str", "e", "b"):
                    text = v.text or ""
                else:
                    try:
                        num = float(v.text)
                    except (TypeError, ValueError):
                        continue
                    is_pct = int(c.get("s") or 0) in pct_xf
                    src.extra_values.append((num, "{}!{}".format(name, ref)))
                    if is_pct:
                        src.extra_values.append((round(num * 100, 10), "{}!{}".format(name, ref)))
                    text = (_fmt(round(num * 100, 10)) + "%") if is_pct else _fmt(num)
                    grid[ref] = text
                    continue
                grid[ref] = text
                if text.strip():
                    src.lines.append(("{}!{}".format(name, ref), text.strip()))
            if grid:
                rows = {}
                for ref, text in grid.items():
                    r = int(re.search(r"\d+", ref).group(0))
                    rows.setdefault(r, {})[_col_index(ref)] = text
                width = max(max(cols) for cols in rows.values()) + 1
                table = [[rows[r].get(ci, "") for ci in range(width)] for r in sorted(rows)]
                src.tables.append({"where": "sheet {}".format(name), "rows": table})


def _decode(p):
    """Text of a file a user exported: UTF-8 (with or without BOM), else GB18030 (Excel on a Chinese
    Windows saves csv that way), else UTF-8 with replacement — never a crash."""
    b = p.read_bytes()
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def _read_csv(p, src):
    text = _decode(p)
    delim = "\t" if p.suffix.lower() == ".tsv" else ","
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delim)]
    src.tables.append({"where": "table", "rows": rows})
    for i, r in enumerate(rows, 1):
        if any(c.strip() for c in r):
            src.lines.append(("row {}".format(i), " | ".join(c.strip() for c in r)))


_MD_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
_MD_RULE = re.compile(r"^\s*\|?\s*:?-{2,}")


def _read_text(p, src):
    text = _decode(p)
    if p.suffix.lower() in (".html", ".htm"):
        text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
        text = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d)>", "\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
    table, n_tab = [], 0
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.strip():
            src.lines.append(("line {}".format(i), ln.strip()))
        m = _MD_ROW.match(ln)
        if m and not _MD_RULE.match(ln.replace("|", "", 1) if ln.strip().startswith("|") else ln):
            table.append([c.strip() for c in m.group(1).split("|")])
            continue
        if m:
            continue                                                    # the |---|---| rule row
        if table:
            n_tab += 1
            src.tables.append({"where": "table {} (ends line {})".format(n_tab, i - 1), "rows": table})
            table = []
    if table:
        n_tab += 1
        src.tables.append({"where": "table {}".format(n_tab), "rows": table})


# ════════════════════════════════════════════════════════════════════════ check 1 — numbers trace
def _date_tok(d):
    return "{:04d}-{:02d}".format(d[0], d[1]) + ("-{:02d}".format(d[2]) if d[2] else "")


def _date_traced(d, src_dates):
    """A full date needs that day in the files; a year-month is stated by any date in that month."""
    if d[2]:
        return d in src_dates
    return any(x[0] == d[0] and x[1] == d[1] for x in src_dates)


def _file_hit(p, line, vals):
    """Is this slide figure a figure the files state? As written, by its mantissa when it carries a
    scale word, as a fraction when the slide shows a % (0.437 in a csv → 43.7%), and ×100 when it is
    a chart value (a %-formatted chart stores 0.912 and SHOWS 91.2%)."""
    if _found(p["value"], vals):
        return True
    if p["scale"] != 1.0 and _found(p["mantissa"], vals):
        return True
    if p["pct"] and _found(p["value"] / 100.0, vals):
        return True
    if line.startswith("chart ·") and not p["pct"] and p["value"] < 10 and _found(round(p["value"] * 100, 10), vals):
        return True
    return False


def deck_numbers(pptx):
    """[(slide, token, parsed, line)] for every CLAIM number on the built slides."""
    import deck_versions as dv                                         # noqa: PLC0415
    out = []
    for s in dv.read_deck(pptx):
        for line in s["text_lines"]:
            if _SRC_LINE.match(unicodedata.normalize("NFKC", line)):
                continue
            rest, dates = split_dates(line)
            for d in dates:
                out.append((s["index"], _date_tok(d), {"date": d}, line))
            for p in _tokens(rest):
                if (p["scale"] == 1.0 and not p["pct"] and p["decimals"] == 0 and not p["unit"]
                        and p["mantissa"] <= SMALL_INT and "," not in p["token"]):
                    continue
                out.append((s["index"], p["token"], p, line))
    return out


def _load_sources(paths, base=None):
    """({path: Source}, {path: reason}) — every readable file, and why each other one is not."""
    ok, bad = {}, {}
    for raw in paths:
        p = Path(os.path.expanduser(str(raw)))
        if base and not p.is_absolute():
            p = Path(base) / p
        try:
            ok[str(raw)] = read_source(p)
        except Unreadable as exc:
            bad[str(raw)] = str(exc)
    return ok, bad


def _index(sources):
    vals, dates = [], set()
    for name, src in sources.items():
        nums, ds = src.numbers()
        vals.extend((v, tok, "{} {}".format(name, where)) for v, tok, where in nums)
        dates.update(d for d, _ in ds)
    return _Vals(vals), dates


class _Vals(list):
    """The files' figures, with an index by value so a 300-page source is not scanned per number."""

    def __init__(self, items):
        super().__init__(items)
        self.by = {}
        for v, tok, where in self:
            self.by.setdefault(_key(v), []).append((tok, where))


def _key(v):
    return "{:.9g}".format(abs(v))


def _found(value, vals):
    if isinstance(vals, _Vals):
        return list(vals.by.get(_key(value), []))
    return [(tok, where) for v, tok, where in vals if _same(v, value)]


def _rounds_to(src_value, p):
    """Does a source value, written at the slide's unit and precision, read as the slide's figure?"""
    if p.get("date"):
        return False
    m = src_value / p["scale"]
    if round(m, p["decimals"]) == round(p["mantissa"], p["decimals"]) and \
            abs(m - p["mantissa"]) <= 0.5 * 10 ** (-p["decimals"]) + 1e-9:
        return True
    zeros = len(re.search(r"(0*)$", str(int(p["mantissa"]))).group(1)) if p["decimals"] == 0 else 0
    if zeros and p["mantissa"] >= 10:                                  # "约 12,000" from 12,345
        return round(m, -zeros) == p["mantissa"]
    return False


_RESCALE = {3: "k", 4: "万", 6: "M", 8: "亿", 9: "B"}


def _near(p, vals, limit=3):
    """Source figures a mistyped or rounded slide number most likely came from."""
    if p.get("date"):
        return []
    target, cands = p["value"], []
    seen = set()
    for v, tok, where in vals:
        if v <= 0 or (v, where) in seen:
            continue
        seen.add((v, where))
        rel = abs(v - target) / max(target, 1e-12)
        same_digits = sorted(re.sub(r"\D", "", _fmt(v))) == sorted(re.sub(r"\D", "", _fmt(target)))
        if _rounds_to(v, p):
            cands.append((0, tok, where, "rounds to it"))
        elif p["scale"] == 1.0 and not p["pct"] and v >= 1000 and any(
                _rounds_to(v, dict(p, scale=10.0 ** e)) for e in _RESCALE):
            e = next(e for e in _RESCALE if _rounds_to(v, dict(p, scale=10.0 ** e)))
            cands.append((0, tok, where, "the same figure in " + _RESCALE[e]))
        elif same_digits and rel < 0.2:
            cands.append((1, tok, where, "same digits, different order"))
        elif rel <= 0.02:
            cands.append((2, tok, where, "within 2%"))
    cands.sort(key=lambda c: c[0])
    return cands[:limit]


class _Expr(ast.NodeVisitor):
    OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd)

    def __init__(self):
        self.literals = []

    def run(self, text):
        expr = unicodedata.normalize("NFKC", str(text)).replace("×", "*").replace("÷", "/")
        expr = re.sub(r"(?<=\d),(?=\d{3}\b)", "", expr)                 # 12,345 → 12345
        tree = ast.parse(expr, mode="eval")
        return self._eval(tree.body)

    def _eval(self, n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            self.literals.append(float(n.value))
            return float(n.value)
        if isinstance(n, ast.BinOp) and isinstance(n.op, self.OPS):
            a, b = self._eval(n.left), self._eval(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b
            return a ** b
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = self._eval(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        raise ValueError("only numbers, + - * / ** and brackets are allowed")


def _row_slides(row):
    s = row.get("slide")
    if isinstance(s, bool):
        return None
    if isinstance(s, int):
        return {s}
    if isinstance(s, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in s):
        return set(s)
    return None


ROW_KINDS = ("source_value", "derived", "from_image", "not_a_claim")


def trace(pptx, source_paths, rows=(), web_claims=(), base=None):
    """The numbers check. Returns a dict:
       traced      [(slide, token, how)]             — found in a file / via a row / via a web row
       untraced    [(slide, token, line, near)]      — the findings
       row_faults  [str]                             — rows that are malformed, wrong or unused
       unreadable  {file: reason}
       counts      {"file": n, "source_value": n, "derived": n, "from_image": n, "not_a_claim": n,
                    "web": n, "cover_date": n}"""
    sources, unreadable = _load_sources(source_paths, base)
    vals, src_dates = _index(sources)
    web_vals = []
    for claim in web_claims:
        for p in _tokens(split_dates(str(claim))[0]):
            web_vals.append(p["value"])
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    faults, used = [], set()
    counts = {k: 0 for k in ("file", "web", "cover_date") + ROW_KINDS}
    traced, untraced = [], []

    parsed_rows = []
    for i, r in enumerate(rows):
        label = "content.numbers[{}]".format(i)
        kinds = [k for k in ROW_KINDS if str(r.get(k) or "").strip()]
        rp = parse_number(r.get("value")) if r.get("value") is not None else None
        rdate = split_dates(str(r.get("value") or ""))[1]
        if len(kinds) != 1:
            faults.append("{} needs exactly one of {} (has {})".format(
                label, " / ".join(ROW_KINDS), ", ".join(kinds) or "none"))
            continue
        if rp is None and not rdate:
            faults.append("{} `value` must be the figure as the slide writes it".format(label))
            continue
        if _row_slides(r) is None:
            faults.append("{} `slide` must be the slide number (or a list of them)".format(label))
            continue
        kind = kinds[0]
        if kind == "not_a_claim" and len(str(r["not_a_claim"]).strip()) < 8:
            faults.append("{} not_a_claim needs a reason a reader can check (≥8 characters)".format(label))
            continue
        if kind == "from_image" and len(str(r["from_image"]).strip()) < 4:
            faults.append("{} from_image must name the picture (and where on it)".format(label))
            continue
        parsed_rows.append((i, r, kind, rp, rdate[0] if rdate else None))

    def _row_ok(i, r, kind, rp, slide_p):
        """Check a row against the slide's figure; returns a fault string or None."""
        label = "content.numbers[{}] ({} on slide {})".format(i, r.get("value"), r.get("slide"))
        if kind == "source_value":
            sp = parse_number(r["source_value"])
            if sp is None:
                return "{}: source_value holds no number".format(label)
            unit = str(r.get("unit") or "").strip()
            if unit:
                if unit not in SCALE:
                    return "{}: unit {!r} is not one of {}".format(label, unit, " / ".join(sorted(SCALE)))
                if slide_p["scale"] != 1.0:
                    return "{}: the slide already writes its unit ({}) — drop `unit`".format(label, slide_p["token"])
                slide_p = dict(slide_p, scale=SCALE[unit], unit=unit, value=slide_p["mantissa"] * SCALE[unit])
            if not _found(sp["value"], vals) and not (sp["scale"] != 1 and _found(sp["mantissa"], vals)):
                return "{}: source_value {} is not in the source files — copy it exactly as the " \
                       "file writes it".format(label, r["source_value"])
            if not _rounds_to(sp["value"], slide_p):
                return "{}: {} does not round to {} (at the slide's unit and precision)".format(
                    label, r["source_value"], slide_p["token"])
            return None
        if kind == "derived":
            ev = _Expr()
            try:
                result = ev.run(r["derived"])
            except Exception as exc:                                   # noqa: BLE001
                return "{}: derived `{}` cannot be evaluated ({})".format(label, r["derived"], exc)
            missing = [lit for lit in ev.literals
                       if not _found(abs(lit), vals) and abs(lit) not in FREE_CONSTANTS
                       and not (float(lit).is_integer() and abs(lit) <= SMALL_INT)]
            if missing:
                return "{}: derived uses {} — not in the source files (every input must be a " \
                       "figure the files state)".format(label, ", ".join(_fmt(m) for m in missing))
            target = abs(result)
            if not _rounds_to(target, slide_p):
                return "{}: `{}` = {:.6g}, which the slide would write as {}{} — not {}".format(
                    label, r["derived"], result,
                    round(target / slide_p["scale"], slide_p["decimals"]),
                    slide_p["unit"] or ("%" if slide_p["pct"] else ""), slide_p["token"])
        return None

    for slide, tok, p, line in deck_numbers(pptx):
        if p.get("date"):
            if _date_traced(p["date"], src_dates):
                traced.append((slide, tok, "file"))
                counts["file"] += 1
                continue
            if slide == 1:
                traced.append((slide, tok, "cover date"))
                counts["cover_date"] += 1
                continue
        else:
            if _file_hit(p, line, vals):
                traced.append((slide, tok, "file"))
                counts["file"] += 1
                continue
        match = None
        for i, r, kind, rp, rdate in parsed_rows:
            if slide not in _row_slides(r):
                continue
            if p.get("date"):
                if rdate == p["date"]:
                    match = (i, r, kind, rp)
                    break
            elif rp is not None and _same(rp["value"], p["value"]) and rp["pct"] == p["pct"]:
                match = (i, r, kind, rp)
                break
        if match:
            i, r, kind, rp = match
            used.add(i)
            fault = None if p.get("date") else _row_ok(i, r, kind, rp, p)
            if fault:
                faults.append(fault)
                untraced.append((slide, tok, line, []))
            else:
                traced.append((slide, tok, kind))
                counts[kind] += 1
            continue
        if not p.get("date") and any(_same(v, p["value"]) for v in web_vals):
            traced.append((slide, tok, "web"))
            counts["web"] += 1
            continue
        untraced.append((slide, tok, line, _near(p, vals)))

    for i, r, kind, rp, rdate in parsed_rows:
        if i not in used:
            faults.append("content.numbers[{}] ({} on slide {}) matches no number on that slide — "
                          "remove it, or fix its value/slide".format(i, r.get("value"), r.get("slide")))
    return {"traced": traced, "untraced": untraced, "row_faults": faults, "unreadable": unreadable,
            "counts": counts}


def format_trace(res, cmd_hint=None):
    """The human report: what traced, every untraced number with its likely source, the row to add."""
    out = []
    c = res["counts"]
    out.append("numbers: {} traced — {} found in the files{}{}{}{}{}{}".format(
        len(res["traced"]), c["file"],
        " · {} rounded (source_value)".format(c["source_value"]) if c["source_value"] else "",
        " · {} worked out (derived)".format(c["derived"]) if c["derived"] else "",
        " · {} from web rows".format(c["web"]) if c["web"] else "",
        " · {} read off images (NOT machine-checked)".format(c["from_image"]) if c["from_image"] else "",
        " · {} marked not-a-claim".format(c["not_a_claim"]) if c["not_a_claim"] else "",
        " · {} cover date".format(c["cover_date"]) if c["cover_date"] else ""))
    for f, why in sorted(res["unreadable"].items()):
        out.append("  UNREADABLE {}: {}".format(f, why))
    if res["untraced"]:
        out.append("  {} number(s) on the slides trace to nothing in the source files:".format(
            len(res["untraced"])))
        for slide, tok, line, near in res["untraced"]:
            out.append("    slide {}: {}   ← \"{}\"".format(slide, tok, line[:80]))
            for _, ntok, where, why in near:
                out.append("        closest in the files: {} ({}) — {}".format(ntok, where, why))
                if why == "rounds to it":
                    out.append('        if that is it, add: {{"value": "{}", "slide": {}, "source_value": "{}"}}'
                               .format(tok, slide, ntok))
                elif why.startswith("the same figure in "):
                    out.append('        if that is it, add: {{"value": "{}", "slide": {}, "source_value": "{}", '
                               '"unit": "{}"}}'.format(tok, slide, ntok, why.rsplit(" ", 1)[1]))
        out.append("  For each: correct the slide to the file's figure; or record how it was reached in "
                   "content.numbers — source_value (rounded), derived (an expression over file figures), "
                   "from_image (read off a picture), not_a_claim (why it is not a claim).")
    for f in res["row_faults"]:
        out.append("  ROW: " + f)
    if cmd_hint:
        out.append(cmd_hint)
    return "\n".join(out)


def _sig_digits(tok):
    p = parse_number(tok)
    if p is None:
        return 0
    # "12,000" → 2, "1.2万" → 2, "0.05" → 1, "1.05" → 3: the digits that carry information
    return len(re.sub(r"\D", "", "{:.12g}".format(abs(p["mantissa"]))).strip("0"))


def auto_rows(res):
    """The rows `--write-rows` may write by itself, and the numbers it leaves to the agent.

    Only the two matches the report already spells out as a ready row: ONE source figure (however
    often it appears) that rounds to the slide's figure, or the same figure in another unit (万/M/亿…).
    Two different candidates, a figure with a single significant digit (a "15" can round from almost
    anything), "same digits, different order" and "within 2%" are the agent's call — they are how a
    mistyped number looks, so writing them away would hide exactly what this check exists to catch.
    Each written row carries `auto` naming where the figure came from, so the critic and the next
    reader can see the row was not typed by a person."""
    rows, left = [], []
    for slide, tok, line, near in res["untraced"]:
        best = [c for c in near if c[0] == 0]
        vals = {parse_number(c[1])["value"] for c in best if parse_number(c[1])}
        if len(vals) != 1 or _sig_digits(tok) < 2:
            left.append((slide, tok, line, near))
            continue
        _, ntok, where, why = best[0]
        row = {"value": tok, "slide": slide, "source_value": ntok}
        if why.startswith("the same figure in "):
            row["unit"] = why.rsplit(" ", 1)[1]
        row["auto"] = "{} in {} — {}".format(ntok, where, why)
        rows.append(row)
    return rows, left


# ════════════════════════════════════════════════════════════════════════ check 2 — material
_TOTAL = re.compile(r"^\s*(合计|總計|总计|总和|總和|小计|小計|共计|共計|总数|總數|全部|"
                    r"total|sum|overall|grand total|all)\b", re.I)
_SUBTOTAL = re.compile(r"(小计|小計|subtotal)", re.I)
_TOTAL_END = re.compile(r"(合计|總計|总计|总和|總和|小计|小計|共计|共計|总数|總數|total|subtotal|sum)\s*$", re.I)


def _is_total(label):
    """A total row/column label: starts with the word (合计, Total, Sum …) or ends with it (费用合计,
    Net total, Segment subtotal)."""
    lbl = unicodedata.normalize("NFKC", str(label or "")).strip()
    return bool(lbl) and bool(_TOTAL.match(lbl) or _TOTAL_END.search(lbl))


def _yearish(cell):
    t = unicodedata.normalize("NFKC", str(cell or "")).strip()
    return bool(re.fullmatch(r"(?:FY|CY)?\s*(?:19|20)\d{2}(?:\s*(?:年|H[12]|Q[1-4]))?|Q[1-4]|H[12]", t, re.I))
_SHARE = re.compile(r"占比|佔比|比例|比重|份额|份額|构成|構成|share|proportion|breakdown|distribution|mix", re.I)
_NOT_PART = re.compile(r"率|rate|均|avg|average|mean|median|per\b|每|指数|index|排名|rank|id\b|编号|年份|year", re.I)
# growth / change columns add up when they hold amounts (a net change), never when they hold percents
_GROWTH = re.compile(r"增长|增長|增幅|growth|change|同比|环比|yoy|qoq", re.I)


def _cell_number(cell):
    """The cell's number when the cell IS a number (with its unit), else None."""
    t = unicodedata.normalize("NFKC", str(cell or "")).strip()
    if not t or not re.search(r"\d", t):
        return None
    if not re.fullmatch(r"[+\-−]?[$€£¥]?\s*\d[\d,]*(?:\.\d+)?\s*(%|万|亿|千|k|K|M|B|bn|元|人|册|次|场|个|件|份)?", t):
        return None
    p = parse_number(t)
    if p is None:
        return None
    neg = t.lstrip().startswith(("-", "−"))
    p = dict(p)
    p["signed"] = -p["value"] if neg else p["value"]
    return p


def _norm_label(s):
    return re.sub(r"[\s\W_]+", "", unicodedata.normalize("NFKC", str(s or "")).lower())


def _fid(*parts):
    return "M-" + hashlib.sha1("\x1f".join(str(x) for x in parts).encode("utf-8")).hexdigest()[:6]


def _tol(cells):
    """Rounding slack for a sum of displayed values: half a unit in the last displayed place, each."""
    dec = max((c["decimals"] for c in cells), default=0)
    if dec == 0 and not any(c["pct"] for c in cells):
        return 1e-9                                                    # whole counts must add exactly
    return 0.5 * 10 ** (-dec) * max(1, len(cells)) + 1e-9


def _table_shape(rows):
    """(header row index or None, label column index, first body row index).

    The body starts at the first DATA row — a row with a text label and at least one number that is
    not a year — and the header is the row just above it. So a title or a "单位：万元" line above the
    header is skipped, and a header of years (指标 | 2024 | 2025) is a header, not data."""
    first = None
    for i, r in enumerate(rows[:8]):
        cells = [c for c in r if str(c).strip()]
        texts = [c for c in cells if _cell_number(c) is None and not _yearish(c)]
        nums = [c for c in cells if _cell_number(c) is not None and not _yearish(c)]
        if texts and nums:
            first = i
            break
    if first is None:
        first = 1 if len(rows) > 1 else 0
    hdr = first - 1 if first >= 1 else None
    width = max((len(r) for r in rows), default=0)
    label = 0
    for ci in range(width):
        col = [r[ci] for r in rows[first:] if ci < len(r) and str(r[ci]).strip()]
        if col and sum(1 for c in col if _cell_number(c) is None) >= len(col) / 2:
            label = ci
            break
    return hdr, label, first


def material(source_paths, base=None):
    """The material check. Returns {"findings": [ {id, kind, where, detail} ], "unreadable": {…},
    "tables": n} — findings sorted by id so a re-run lists them the same way."""
    sources, unreadable = _load_sources(source_paths, base)
    findings, all_tables = [], []
    for name, src in sources.items():
        for t in src.tables:
            rows = [list(r) for r in t["rows"] if any(str(c).strip() for c in r)]
            if len(rows) < 2:
                continue
            hdr, lab, first = _table_shape(rows)
            header = rows[hdr] if hdr is not None else []
            body = rows[first:]
            where = "{} · {}".format(name, t["where"])
            width = max(len(r) for r in rows)
            headers = [header[ci] if ci < len(header) else "" for ci in range(width)]
            labels = [r[lab] if lab < len(r) else "" for r in body]
            all_tables.append((where, headers, labels, body, lab))

            # (a) a TOTAL ROW is the sum of the rows it closes — or, when it comes FIRST (some reports
            # lead with the total), of the rows it opens
            for ci in range(width):
                if ci == lab or _NOT_PART.search(str(headers[ci])):
                    continue
                cells = [(_cell_number(r[ci]) if ci < len(r) else None, str(r[lab]) if lab < len(r) else "")
                         for r in body]
                if _GROWTH.search(str(headers[ci])) and any(c and c["pct"] for c, _ in cells):
                    continue
                since, everything = [], []
                for ri, (cell, lbl) in enumerate(cells):
                    if _is_total(lbl) and cell is not None:
                        parts = since if _SUBTOTAL.search(lbl) else everything
                        if not parts:                                   # a total that leads
                            parts = []
                            for c2, l2 in cells[ri + 1:]:
                                if _is_total(l2):
                                    break
                                if c2 is not None:
                                    parts.append(c2)
                        if len(parts) >= 2:
                            tot = sum(c["signed"] for c in parts)
                            if abs(tot - cell["signed"]) > _tol(parts + [cell]):
                                findings.append({
                                    "id": _fid("total-row", where, lbl, headers[ci]),
                                    "kind": "total-row",
                                    "where": "{} — row \"{}\", column \"{}\"".format(where, lbl, headers[ci]),
                                    "detail": "its parts add up to {} but the total says {}".format(
                                        _fmt(round(tot, 10)), cell["token"])})
                        since = []
                    elif cell is not None and not _is_total(lbl):
                        since.append(cell)
                        everything.append(cell)
            # (b) a TOTAL COLUMN is the sum of the part columns beside it
            tcols = [ci for ci in range(width) if ci != lab and _is_total(headers[ci])]
            for tc in tcols:
                parts_cols = [ci for ci in range(width) if ci not in tcols and ci != lab
                              and not _NOT_PART.search(str(headers[ci])) and not _GROWTH.search(str(headers[ci]))
                              and not _SHARE.search(str(headers[ci]))]
                for r in body:
                    if tc >= len(r) or _is_total(r[lab] if lab < len(r) else ""):
                        continue
                    tot = _cell_number(r[tc])
                    cells = [_cell_number(r[ci]) for ci in parts_cols if ci < len(r)]
                    cells = [c for c in cells if c is not None]
                    if tot is None or len(cells) < 2 or any(c["pct"] for c in cells) != tot["pct"]:
                        continue
                    s = sum(c["signed"] for c in cells)
                    if abs(s - tot["signed"]) > _tol(cells + [tot]):
                        lbl = r[lab] if lab < len(r) else ""
                        findings.append({
                            "id": _fid("total-col", where, lbl, headers[tc]),
                            "kind": "total-column",
                            "where": "{} — row \"{}\", column \"{}\"".format(where, lbl, headers[tc]),
                            "detail": "the columns beside it add up to {} but the total says {}".format(
                                _fmt(round(s, 10)), tot["token"])})
            # (c) a SHARE column reaches 100%
            for ci in range(width):
                if ci == lab or not _SHARE.search(str(headers[ci])) or _NOT_PART.search(str(headers[ci])) \
                        or _GROWTH.search(str(headers[ci])):
                    continue
                cells = []
                for r in body:
                    if ci >= len(r) or _is_total(r[lab] if lab < len(r) else ""):
                        continue
                    c = _cell_number(r[ci])
                    if c is not None:
                        cells.append(c)
                if len(cells) < 2 or any(c["signed"] < 0 for c in cells):
                    continue
                if all(c["pct"] or "%" in str(headers[ci]) for c in cells):
                    whole, unit = 100.0, "%"
                elif not any(c["pct"] for c in cells) and all(c["value"] <= 1 for c in cells):
                    whole, unit = 1.0, ""                                # shares stored as fractions
                else:
                    continue
                s = sum(c["value"] for c in cells)
                slack = max(_tol(cells), 0.5 * len(cells) if unit and all(c["decimals"] == 0 for c in cells) else 0)
                if abs(s - whole) > slack:
                    findings.append({
                        "id": _fid("share", where, headers[ci]),
                        "kind": "share-not-100",
                        "where": "{} — column \"{}\"".format(where, headers[ci]),
                        "detail": "the shares add up to {}{}, not {}{}".format(
                            _fmt(round(s, 10)), unit, _fmt(whole), unit)})

    # (d) the SAME table, twice, with cells that disagree (two versions / the deck vs the sheet)
    def _cells(tab):
        where, headers, labels, body, lab = tab
        out = {}
        for r in body:
            lbl = _norm_label(r[lab] if lab < len(r) else "")
            if not lbl:
                continue
            for ci, h in enumerate(headers):
                if ci == lab or ci >= len(r):
                    continue
                c = _cell_number(r[ci])
                if c is not None and _norm_label(h):
                    out[(lbl, _norm_label(h))] = (c, r[lab], h)
        return out

    cellmaps = [(tab[0], _cells(tab)) for tab in all_tables]
    for i in range(len(cellmaps)):
        for j in range(i + 1, len(cellmaps)):
            (wa, a), (wb, b) = cellmaps[i], cellmaps[j]
            shared = set(a) & set(b)
            if len(shared) < 4:
                continue
            agree = [k for k in shared if _same(a[k][0]["value"], b[k][0]["value"])]
            if len(agree) < len(shared) / 2:                       # different entities, same layout
                continue
            for k in sorted(shared - set(agree)):
                ca, cb = a[k][0], b[k][0]
                findings.append({
                    "id": _fid("conflict", wa, wb, k),
                    "kind": "conflict",
                    "where": "\"{}\" × \"{}\"".format(a[k][1], a[k][2]),
                    "detail": "{} says {}, {} says {} ({} of {} shared cells agree)".format(
                        wa, ca["token"], wb, cb["token"], len(agree), len(shared))})
    findings.sort(key=lambda f: (f["kind"], f["id"]))
    seen, uniq = set(), []
    for f in findings:
        if f["id"] not in seen:
            seen.add(f["id"])
            uniq.append(f)
    return {"findings": uniq, "unreadable": unreadable, "tables": len(all_tables)}


def format_material(res):
    out = ["material: {} table(s) checked across the source files — {} finding(s)".format(
        res["tables"], len(res["findings"]))]
    for f, why in sorted(res["unreadable"].items()):
        out.append("  UNREADABLE {}: {} (NOT checked)".format(f, why))
    for f in res["findings"]:
        out.append("  {}  [{}] {}\n      {}".format(f["id"], f["kind"], f["where"], f["detail"]))
    if res["findings"]:
        out.append("  Only the user can say which value is right. Ask them (in auto mode: decide, "
                   "and list it in the hand-off), fix the deck to the answer, and record each:\n"
                   '    "material_check": [{"id": "<M-…>", "resolution": "<which value is right, '
                   'and who said so>"}]')
    return "\n".join(out)


# ════════════════════════════════════════════════════════════════════════ the gate (both runtimes)
def _placeholder(v):
    s = str(v or "").strip()
    return not s or (s.startswith("<") and s.endswith(">"))


def gate_faults(content, deck_dir, pptx, web_claims=(), source_paths=None):
    """(faults, summary_line) for the gate. `content` is the record's content section; the source
    files are `source_paths` when given (the Codex record's provided sources), else
    content["sources"] (each a path string or {"path": …}). An empty list means the deck has no
    user material — nothing to trace against, and the summary says so."""
    faults = []
    if source_paths is None:
        raw = content.get("sources")
        source_paths = [s.get("path") if isinstance(s, dict) else s for s in (raw or [])]
    source_paths = [s for s in source_paths if isinstance(s, str) and s.strip()]
    if not source_paths:
        return [], "source check: no user material recorded — nothing to trace against"
    missing = [s for s in source_paths
               if not (Path(os.path.expanduser(s)) if os.path.isabs(os.path.expanduser(s))
                       else Path(deck_dir) / s).is_file()]
    if missing:
        return (["content.sources: {} file(s) not found relative to the deck folder {}: {}".format(
            len(missing), deck_dir, ", ".join(missing[:5]))], "")

    nums = content.get("numbers", [])
    if not isinstance(nums, list):
        faults.append("content.numbers must be a LIST of rows ([] when every number is in the files)")
        nums = []
    res = trace(pptx, source_paths, nums, web_claims, base=deck_dir)
    for slide, tok, line, near in res["untraced"]:
        hint = "; closest in the files: " + ", ".join("{} ({})".format(n[1], n[3]) for n in near) if near else ""
        faults.append("slide {}: {} traces to nothing in the source files{} — \"{}\"".format(
            slide, tok, hint, line[:70]))
    faults.extend(res["row_faults"])

    mat = material(source_paths, base=deck_dir)
    checks = content.get("material_check", [])
    if not isinstance(checks, list):
        faults.append("content.material_check must be a LIST of {id, resolution} rows")
        checks = []
    resolved = {str(c.get("id")): c for c in checks if isinstance(c, dict)}
    for f in mat["findings"]:
        c = resolved.get(f["id"])
        if c is None or _placeholder(c.get("resolution")) or len(str(c.get("resolution")).strip()) < 8:
            faults.append("material {} [{}] unresolved — {}: {}".format(f["id"], f["kind"], f["where"],
                                                                        f["detail"]))
    live = {f["id"] for f in mat["findings"]}
    for cid in resolved:
        if cid not in live:
            faults.append("content.material_check: {} matches no current finding — remove it (the "
                          "material changed, or the id was mistyped)".format(cid))
    unread = dict(res["unreadable"])
    unread.update(mat["unreadable"])
    summary = "{} | material: {} table(s), {} finding(s) resolved{}".format(
        format_trace(res).splitlines()[0], mat["tables"], len(mat["findings"]),
        " | NOT CHECKED (unreadable): " + ", ".join("{} — {}".format(k, v) for k, v in sorted(unread.items()))
        if unread else "")
    return faults, summary


# ════════════════════════════════════════════════════════════════════════ CLI
RECORDS = (".codex-deck-evidence.json", ".deck-gates.json")


def _record_path(deck_dir):
    """The record this run's gate reads. The Codex runtime keeps its sources and number rows in
    `.codex-deck-evidence.json` and may carry a `.deck-gates.json` too (the interview command writes
    one), so the evidence file wins when present — reading or writing the other one is how a real
    run (2026-11-05) saw rows the gate had accepted reported as missing, and would have had
    --write-rows write where its gate never looks."""
    for name in RECORDS:
        p = Path(deck_dir) / name
        if p.is_file():
            return p
    return None


def _sources_of(content):
    """Source paths from a record's content: plain paths, {"path"} rows, and on the Codex record
    only the `provided` ones (a `web` row is traced through its claims, not read as a file)."""
    out = []
    for s in (content.get("sources") or []):
        if isinstance(s, dict):
            if s.get("kind", "provided") == "provided" and isinstance(s.get("path"), str):
                out.append(s["path"])
        elif isinstance(s, str):
            out.append(s)
    return out


def _record(deck_dir):
    p = _record_path(deck_dir)
    if p is None:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit("cannot read {}: {}".format(p, exc))


def _pick_pptx(deck_dir):
    """The one .pptx in the folder — several is a question for the caller, never a guess."""
    cands = sorted(c for c in Path(deck_dir).glob("*.pptx") if not c.name.startswith("~$"))
    if not cands:
        raise SystemExit("no .pptx in {} — pass --pptx <deck.pptx>".format(deck_dir))
    if len(cands) > 1:
        raise SystemExit("{} .pptx files in {} ({}) — say which deck: --pptx <one of them>".format(
            len(cands), deck_dir, ", ".join(c.name for c in cands)))
    return cands[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("numbers", help="every number on the slides traces to the user's files")
    n.add_argument("target", help="the deck folder (reads .deck-gates.json) or a .pptx")
    n.add_argument("--pptx")
    n.add_argument("--source", nargs="+", action="extend", help="source files (instead of content.sources); "
                   "list them after one --source or repeat the flag")
    n.add_argument("--write-rows", action="store_true",
                   help="write the unambiguous rows (one source figure that rounds to the slide's, or the "
                        "same figure in another unit) into content.numbers, tagged `auto`; the rest stay "
                        "for you. Needs the deck folder as the target.")
    m = sub.add_parser("material", help="the user's files checked against themselves")
    m.add_argument("targets", nargs="+", help="the deck folder (reads content.sources) or the files")
    r = sub.add_parser("read", help="what one source file yields")
    r.add_argument("file")
    a = ap.parse_args(argv)

    if a.cmd == "read":
        try:
            src = read_source(a.file)
        except Unreadable as exc:
            print("UNREADABLE {}: {}".format(a.file, exc))
            return 2
        nums, dates = src.numbers()
        print("{}: {} line(s), {} table(s), {} number(s), {} date(s)".format(
            a.file, len(src.lines), len(src.tables), len(nums), len(dates)))
        for v, tok, where in nums[:60]:
            print("  {:<14} {}".format(tok, where))
        return 0

    if a.cmd == "material":
        t0 = Path(a.targets[0])
        if len(a.targets) == 1 and t0.is_dir():
            rec = _record(t0) or {}
            paths = _sources_of(rec.get("content", {}) or {})
            if not paths:
                print("no content.sources in {} — pass the files: {} material <file> …".format(
                    t0 / ".deck-gates.json", _SELF))
                return 2
            res = material(paths, base=t0)
        else:
            res = material(a.targets)
        print(format_material(res))
        if res["findings"]:
            print("NEXT: put each finding to the user, then record its resolution in "
                  "content.material_check")
            return 1
        print("NEXT: plan the content (Step 1) — the material agrees with itself where it could be checked")
        return 0

    target = Path(a.target)
    rows, web, base = [], [], None
    if target.is_dir():
        base = target
        rec = _record(target) or {}
        content = rec.get("content", {}) or {}
        paths = a.source or _sources_of(content)
        rows = content.get("numbers") or []
        web = [c.get("claim", "") for c in ((rec.get("provenance") or {}).get("claims") or [])
               if isinstance(c, dict) and c.get("url")]
        pptx = Path(a.pptx) if a.pptx else _pick_pptx(target)
    else:
        paths, pptx = a.source or [], target
    if not paths:
        print("no source files: record them in content.sources, or pass --source <files>")
        return 2
    res = trace(pptx, paths, rows, web, base=base)
    if a.write_rows:
        if not target.is_dir() or _record_path(target) is None:
            print("--write-rows writes into the deck folder's record (.codex-deck-evidence.json or "
                  ".deck-gates.json) — pass the deck folder")
            return 2
        new, _ = auto_rows(res)
        if new:
            rec = _record(target)
            rec.setdefault("content", {}).setdefault("numbers", [])
            rec["content"]["numbers"].extend(new)
            _record_path(target).write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                                            encoding="utf-8")
            rows = rec["content"]["numbers"]
            print("wrote {} row(s) to content.numbers in {} — check each; a wrong one is deleted, not argued with:"
                  .format(len(new), _record_path(target).name))
            for r in new:
                print("  slide {}: {} ← {}".format(r["slide"], r["value"], r["auto"]))
            res = trace(pptx, paths, rows, web, base=base)
        else:
            print("--write-rows: nothing unambiguous to write")
    print(format_trace(res))
    if res["untraced"] or res["row_faults"]:
        again = [shlex.quote(str(a.target))] + (["--pptx", shlex.quote(a.pptx)] if a.pptx else []) + \
            (["--source"] + [shlex.quote(x) for x in a.source] if a.source else [])
        auto_n = len(auto_rows(res)[0])
        if auto_n and not a.write_rows and target.is_dir():
            print("{} of these have exactly one source figure that rounds to them — add --write-rows to "
                  "record those rows for you (tagged `auto`), then decide the rest.".format(auto_n))
        print("NEXT: fix those slides or rows, rebuild, then: {} numbers {}".format(_SELF, " ".join(again)))
        return 1
    print("NEXT: every number traces — run the gate check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
