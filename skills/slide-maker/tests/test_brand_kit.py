#!/usr/bin/env python3
"""Brand kit: the user's brand files -> one reviewed brand.json -> the deck's palette and faces ->
a check of the BUILT deck for off-brand colours, faces and the logo rule, on both gate paths.

Every fixture is made here (an SVG and a PNG logo, a JPG logo on a white plate, a PDF brand guide
written with PyMuPDF, a .pptx carrying a theme) for two invented brands — never a user's file.

The calibration half builds real decks from `style` output in a SUBPROCESS each (deckkit's palette
is process-global state, and one process building two brands is exactly how a guard inherits the
first brand's colours and goes green on the second) and asserts the target the design doc sets:
0 findings on the on-brand decks, a catch on every deliberately off-brand variant.
"""
from __future__ import annotations

import io
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
BK = str(SCRIPTS / "brand_kit.py")

os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/nonexistent/taste-ledger-for-tests.json"
TMP = Path(tempfile.mkdtemp(prefix="brandkit-test-"))
os.environ["SLIDE_MAKER_REGISTRY"] = str(TMP / "registry")
(TMP / "registry").mkdir()        # an ABSENT override is skipped on read: the kit must never leak
                                  # into the user's real ~/.claude/slide-templates

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, BK] + [str(a) for a in args], capture_output=True,
                       text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr


def next_line(out):
    for ln in out.splitlines():
        if ln.startswith("NEXT:"):
            return ln
    return ""


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


r = subprocess.run([sys.executable, BK, "--selftest"], capture_output=True, text=True)
check(r.returncode == 0, "brand_kit.py --selftest failed:\n" + r.stdout + r.stderr)

# ── fixtures: two invented brands ─────────────────────────────────────────────────────────────
# "Tidewater Labs": ocean blue #0B5FFF, sunset orange #FF7A00, deep navy #0B2545, mist #F2F5F9.
# "青禾茶舍" (Qinghe Tea House, a CJK deck): tea green #2F7D4F, clay red #B5482A, ink #1E2A24,
# rice paper #FAF6EE. Both are made up for this test.
from PIL import Image, ImageDraw  # noqa: E402

FX = TMP / "fixtures"
FX.mkdir()
svg = FX / "tidewater.svg"
svg.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="80" viewBox="0 0 200 80">'
    '<rect x="0" y="0" width="80" height="80" fill="#0B5FFF"/>'
    '<circle cx="40" cy="40" r="18" style="fill:#ff7a00;stroke:#0B2545;stroke-width:3"/>'
    '<path d="M90 20 H190 V60 H90 Z" fill="#0B2545"/></svg>', encoding="utf-8")
svg_nofill = FX / "nofill.svg"
svg_nofill.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60">'
    '<path d="M5 5 H55 V55 H5 Z"/></svg>', encoding="utf-8")

png = FX / "qinghe.png"
im = Image.new("RGBA", (240, 120), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse((10, 10, 110, 110), fill=(0x2F, 0x7D, 0x4F, 255))
d.rectangle((130, 30, 230, 90), fill=(0xB5, 0x48, 0x2A, 255))
im.save(png)

jpg = FX / "plate.jpg"
im2 = Image.new("RGB", (200, 100), (255, 255, 255))
ImageDraw.Draw(im2).rectangle((40, 20, 160, 80), fill=(0x2F, 0x7D, 0x4F))
im2.save(jpg, quality=92)

import fitz  # noqa: E402

guide = FX / "tidewater-guide.pdf"
doc = fitz.open()
pg = doc.new_page()
lines = ["Tidewater Labs brand guide", "Primary colour  Ocean Blue  HEX #0B5FFF",
         "Accent  Sunset  #FF7A00", "Neutral  Deep Navy  RGB 11, 37, 69",
         "Background  Mist  #F2F5F9", "Print only: Pantone 2728 C",
         "Typeface: Helvetica Neue for headings", "Body text font: Arial"]
for i, t in enumerate(lines):
    pg.insert_text((50, 70 + 24 * i), t, fontsize=12)
doc.save(guide)
guide_bare = FX / "no-codes.pdf"
doc2 = fitz.open()
doc2.new_page().insert_text((50, 70), "Our brand is warm and friendly.", fontsize=12)
doc2.save(guide_bare)

# a .pptx carrying a theme: python-pptx's default, with its scheme rewritten to the tea house
from pptx import Presentation  # noqa: E402

theme_pptx = FX / "qinghe-old.pptx"
Presentation().save(theme_pptx)
with zipfile.ZipFile(theme_pptx) as z:
    parts = {n: z.read(n) for n in z.namelist()}
tname = [n for n in parts if n.startswith("ppt/theme/theme")][0]
x = parts[tname].decode("utf-8")
import re  # noqa: E402

for slot, val in (("accent1", "2F7D4F"), ("accent2", "B5482A"), ("dk2", "1E2A24"),
                  ("lt2", "FAF6EE")):
    x = re.sub(r"(<a:%s>\s*<a:srgbClr val=\")[0-9A-Fa-f]{6}" % slot, r"\g<1>" + val, x, count=1)
x = re.sub(r'(<a:majorFont>\s*<a:latin typeface=")[^"]*', r"\g<1>Georgia", x, count=1)
x = re.sub(r'(<a:minorFont>\s*<a:latin typeface=")[^"]*', r"\g<1>Arial", x, count=1)
x = re.sub(r'(<a:minorFont>.*?<a:ea typeface=")[^"]*', r"\g<1>Songti SC", x, count=1, flags=re.S)
parts[tname] = x.encode("utf-8")
with zipfile.ZipFile(theme_pptx, "w", zipfile.ZIP_DEFLATED) as z:
    for n, b in parts.items():
        z.writestr(n, b)

# ── extract ───────────────────────────────────────────────────────────────────────────────────
TW = TMP / "tidewater"
TW.mkdir()
code, out = run("extract", svg, guide, "--out", TW / "brand.json")
check(code == 0, "extract (svg + pdf) exits 0:\n" + out)
bj = load(TW / "brand.json")
hexes = {c["hex"] for c in bj["colors"]}
for h in ("#0B5FFF", "#FF7A00", "#0B2545", "#F2F5F9"):
    check(h in hexes, "extract found {} (got {})".format(h, sorted(hexes)))
check(all(c.get("source") for c in bj["colors"]), "every extracted colour records its source")
check(bj["status"] == "draft", "a fresh extraction is a DRAFT")
check(bj["fonts"]["heading"] and bj["fonts"]["heading"]["name"] == "Helvetica Neue",
      "the guide's heading face is read from its text: {}".format(bj["fonts"].get("heading")))
check(bj["fonts"]["body"] and bj["fonts"]["body"]["name"] == "Arial",
      "the guide's body face is read from its text: {}".format(bj["fonts"].get("body")))
check(any("Pantone" in u for u in bj.get("undecided", [])),
      "a Pantone reference with no hex is listed as undecided, not converted from memory")
check(bj["logos"] and bj["logos"][0]["ground"] in ("light", "dark", "both", "neither"),
      "the logo records the ground it reads on")
check(bj["logos"][0].get("raster") and (TW / bj["logos"][0]["raster"]).is_file(),
      "an SVG logo gets a PNG raster a deck can actually place (python-pptx cannot embed SVG)")
check("review" in next_line(out), "extract prints NEXT: review …\n" + out)

code, out = run("extract", svg_nofill, "--out", TMP / "nofill.json")
nf = load(TMP / "nofill.json") if (TMP / "nofill.json").exists() else {"colors": []}
check(code == 0 and any(c["hex"] == "#000000" for c in nf["colors"]),
      "an SVG with no fill attribute reads its RENDERED colour (black, per SVG), said out loud:\n"
      + out)
check("declares no" in out.lower() or "rendered" in out.lower(),
      "…and it says it read the render, not a declared colour")

code, out = run("extract", guide_bare, "--out", TMP / "bare.json")
check(code == 1 and "no hex" in out.lower() and "--hex" in out,
      "a PDF with no hex/RGB codes and nothing else fails loud and names the fix:\n" + out)

code, out = run("extract", TMP / "missing.png", "--out", TMP / "m.json")
check(code == 2 and "missing.png" in out, "an unreadable input names the file:\n" + out)
bad = FX / "corrupt.png"
bad.write_bytes(b"not a png at all")
code, out = run("extract", bad, "--out", TMP / "c.json")
check(code == 2 and "corrupt.png" in out, "a corrupt image names the file:\n" + out)

QH = TMP / "qinghe"
QH.mkdir()
code, out = run("extract", png, jpg, theme_pptx, "--hex", "#FAF6EE", "--font", "cjk=Songti SC",
                "--out", QH / "brand.json")
check(code == 0, "extract (png + jpg + pptx + --hex/--font) exits 0:\n" + out)
qb = load(QH / "brand.json")
qhex = {c["hex"]: c for c in qb["colors"]}
for h in ("#2F7D4F", "#B5482A", "#1E2A24"):
    check(h in qhex, "extract found {} from the png/theme (got {})".format(h, sorted(qhex)))
check("#FFFFFF" not in {c["hex"] for c in qb["colors"] if "plate.jpg" in c["source"]},
      "the JPG's white PLATE is background, not a brand colour")
check(qhex.get("#FAF6EE", {}).get("source", "").startswith("user")
      or "user" in qhex.get("#FAF6EE", {}).get("source", ""),
      "a --hex value records source user: {}".format(qhex.get("#FAF6EE")))
check(qb["fonts"]["heading"]["name"] == "Georgia" and qb["fonts"]["body"]["name"] == "Arial",
      "theme major/minor fonts read from the .pptx: {}".format(qb["fonts"]))
check(qb["fonts"]["cjk"]["name"] == "Songti SC", "the CJK face is recorded: {}".format(qb["fonts"]))
check(qhex["#2F7D4F"]["role_guess"] == "primary", "theme accent1 / heaviest logo hue is guessed primary")

# ── draft refusal ─────────────────────────────────────────────────────────────────────────────
code, out = run("style", TW / "brand.json")
check(code == 1 and "confirm" in out, "style refuses a DRAFT and names confirm:\n" + out)
code, out = run("check", TMP / "x.pptx", "--brand", TW / "brand.json")
check(code in (1, 2) and "confirm" in out, "check refuses a DRAFT:\n" + out)

# ── review ────────────────────────────────────────────────────────────────────────────────────
code, out = run("review", TW / "brand.json")
check(code == 0 and "#0B5FFF" in out and "confirm" in next_line(out),
      "review prints the table and a NEXT confirm line:\n" + out)
code, out = run("review", TW / "brand.json", "--auto")
check(code == 0 and '"axis": "template"' in out and '"basis"' in out and '"alternative"' in out,
      "review --auto prints a delegated-pick row to record:\n" + out)
import delegated_picks as dp  # noqa: E402
row = next((json.loads(ln) for ln in out.splitlines() if ln.startswith('{"axis"')), None)
picks = [{"axis": ax, "source": "genre-default", "value": "the deck the request implies"}
         if ax == "angle" else
         {"axis": ax, "source": "stated", "value": "what the user said"} for ax in dp.AXES]
picks = [row if p["axis"] == "template" else p for p in picks]
check(row is not None and not dp.faults({"picks": picks}, auto=True),
      "the printed auto-mode row passes the delegated-picks contract: {}".format(
          dp.faults({"picks": picks}, auto=True) if row else out))
# '#' unquoted starts a shell COMMENT — a printed confirm line must survive being pasted
nxt = next_line(out)
check("--primary '#" in nxt, "the printed confirm line quotes its hex values: " + nxt)
r = subprocess.run(nxt[len("NEXT: "):] + " --help", shell=True, capture_output=True, text=True)
check(r.returncode == 0, "the printed confirm line parses in a shell: " + r.stderr[-300:])

# ── confirm ───────────────────────────────────────────────────────────────────────────────────
code, out = run("confirm", TW / "brand.json")
check(code != 0 and "--primary" in out, "confirm without --primary names the flag:\n" + out)
code, out = run("confirm", TW / "brand.json", "--primary", "#0B5FFF", "--accent", "#FF7A00",
                "--neutral", "#0B2545", "--neutral", "#F2F5F9")
check(code == 0, "confirm Tidewater exits 0:\n" + out)
bj = load(TW / "brand.json")
check(bj["status"] == "confirmed", "confirm sets status confirmed")
roles = {c["hex"]: c["role"] for c in bj["colors"]}
check(roles.get("#0B5FFF") == "primary" and roles.get("#FF7A00") == "accent",
      "confirm sets the roles: {}".format(roles))
check(bj["confirmed"].get("pairs"), "confirm records text/background contrast pairs")
check(bj["confirmed"].get("ground_light") == "#F2F5F9" and bj["confirmed"].get("ground_dark") == "#0B2545",
      "the brand's OWN neutrals ground the deck before white/black: {}".format(bj["confirmed"]))
check("style" in next_line(out), "confirm prints NEXT: style …\n" + out)

# a font that is not installed -> a named, installed fallback, marked
code, out = run("confirm", QH / "brand.json", "--primary", "#2F7D4F", "--accent", "#B5482A",
                "--neutral", "#1E2A24", "--neutral", "#FAF6EE",
                "--heading-font", "Qinghe Brush Display (not installed)", "--lang", "zh-Hans")
qb = load(QH / "brand.json")
if code == 0:
    hf = qb["fonts"]["heading"]
    check(hf.get("installed") is False and hf.get("fallback"),
          "a missing heading face is marked with an installed fallback: {}".format(hf))
    cj = qb["fonts"]["cjk"]
    check(cj.get("covers") is not False or cj.get("fallback"),
          "the CJK face is checked for the deck's glyphs, with a fallback when it lacks them: {}"
          .format(cj))
else:
    check("install" in out.lower(), "a CJK confirm with no covering face says what to install:\n"
          + out)

# a hex that is not in the draft is accepted only as a USER value, recorded so
code, out = run("confirm", TMP / "nofill.json", "--primary", "#123456")
nf = load(TMP / "nofill.json")
check(code == 0 and any(c["hex"] == "#123456" and "user" in c["source"] for c in nf["colors"]),
      "a typed --primary not in the draft is recorded with source user:\n" + out)

# a CJK face confirmed without --lang: its glyphs were never checked, so a CJK deck is refused
NL = TMP / "nolang"
NL.mkdir()
run("extract", png, "--font", "cjk=Songti SC", "--font", "body=Arial", "--out", NL / "brand.json")
code, out = run("confirm", NL / "brand.json", "--primary", "#2F7D4F")
check(code == 0 and "--lang" in out, "confirm warns that a CJK face without --lang is unchecked:\n" + out)

# ── save / list / use ─────────────────────────────────────────────────────────────────────────
code, out = run("save", TW / "brand.json", "--name", "tidewater")
check(code == 0, "save exits 0:\n" + out)
code, out = run("list")
check(code == 0 and "tidewater" in out, "list shows the saved kit:\n" + out)
check((TMP / "registry" / "brands" / "tidewater" / "brand.json").is_file(),
      "save wrote under $SLIDE_MAKER_REGISTRY, not into some other registry root")
DECK2 = TMP / "deck2"
DECK2.mkdir()
code, out = run("use", "tidewater", DECK2)
check(code == 0 and (DECK2 / "brand.json").is_file() and "style" in next_line(out),
      "use copies the kit into a new deck folder and points at style:\n" + out)
used = load(DECK2 / "brand.json") if (DECK2 / "brand.json").is_file() else {"logos": []}
check(all((DECK2 / l["raster"]).is_file() for l in used["logos"] if l.get("raster")),
      "use brings the logo assets along")
code, out = run("save", TMP / "bare.json" if (TMP / "bare.json").exists() else TMP / "nofill.json",
                "--name", "x/../../evil")
check(code != 0, "save refuses a kit name that is a path:\n" + out)

# ── style ─────────────────────────────────────────────────────────────────────────────────────
code, out = run("style", TW / "brand.json")
check(code == 0 and (TW / "brand_style.py").is_file(), "style writes brand_style.py:\n" + out)
src = (TW / "brand_style.py").read_text(encoding="utf-8") if (TW / "brand_style.py").exists() else ""
for k in ("BRAND", "INK", "ACCENT", "GREY", "MUTE", "LINE", "WHITE", "FONT", "def apply"):
    check(k in src, "brand_style.py defines {}".format(k))
for k in ("bg", "ink", "muted", "accents", "font", "display", "ea", "ea_display"):
    check(re.search(r"['\"]%s['\"]\s*:" % k, src), "BRAND carries the preset key {}".format(k))
code, out = run("style", QH / "brand.json")
check(code == 0, "style (CJK brand) exits 0:\n" + out)

# ── calibration: build on-brand decks from style output, and off-brand variants ──────────────
BUILD = r'''
import sys, importlib.util
from pathlib import Path
here = Path(sys.argv[1]); variant = sys.argv[2]; out = sys.argv[3]
spec = importlib.util.spec_from_file_location("brand_style", str(here / "brand_style.py"))
bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
B = bs.apply()
import deckkit as dk
from pptx.dml.color import RGBColor
zh = B.get("ea") is not None and "zh" in (bs.LANG or "")
T = (lambda en, cn: cn if zh else en)
prs = dk.blank_deck()
s = dk.add_slide(prs)
if B.get("logo") and variant != "nologo":
    dk.picture(s, str(here / B["logo"]), 0.6, 0.5, 1.6, 0.64, alt="logo")
dk.text(s, 0.6, 1.6, 8.5, 1.0, [[(T("Quarterly review", "季度回顾"), 36, bs.INK, True, False)]])
dk.text(s, 0.6, 2.7, 8.5, 0.5, [[(T("What changed, and what we do next", "变化与下一步"), 16,
        bs.GREY, False, False)]])
s2 = dk.add_slide(prs)
dk.title_bar(s2, T("Three things moved this quarter", "本季度三件事"))
dk.bullet(s2, 0.7, 1.5, 5.0, [(T("Reach", "覆盖"), T(" grew in two regions", "两个地区增长")),
                              (T("Cost", "成本"), T(" fell per order", "单笔下降")),
                              (T("Churn", "流失"), T(" held flat", "持平"))])
dk.callout(s2, 6.0, 1.5, 3.4, 1.4, T("So what", "结论"), T("Double down on the two regions", "加码两个地区"))
dk.footer(s2, tag=T("Quarterly review", "季度回顾"), page=2)
s3 = dk.add_slide(prs)
dk.title_bar(s3, T("Orders by month", "月度订单"))
dk.native_chart(s3, 0.7, 1.4, 5.6, 3.2, ["Jan", "Feb", "Mar", "Apr"],
                [(T("Region A", "甲区"), [3, 4, 6, 7]), (T("Region B", "乙区"), [2, 3, 3, 5])],
                kind="bar")
dk.scorecard(s3, 6.6, 1.4, 2.8, 1.4, T("Orders", "订单"), "1,240", delta="+12%")
photo = here / "photo.png"
dk.picture(s3, str(photo), 6.6, 3.0, 2.8, 1.6, alt="a photo")
dk.footer(s3, tag=T("Quarterly review", "季度回顾"), page=3)
if variant == "offcolour":
    dk.box(s3, 0.7, 4.75, 2.0, 0.3, fill=RGBColor(0x7B, 0x2C, 0xBF))      # violet: no brand hue
if variant == "offtext":
    dk.text(s2, 0.7, 4.4, 5.0, 0.4, [[(T("Off-brand note", "离谱颜色"), 14,
            RGBColor(0xE0, 0x1E, 0x5A), True, False)]])                     # raspberry text
if variant == "offfont":
    dk.text(s2, 0.7, 4.4, 5.0, 0.4, [[(T("Comic aside", "Comic 另一种字体"), 14, bs.INK, False, False,
            "Comic Sans MS")]])
if variant == "offeafont":                                                  # a CJK face off-brand
    tb = dk.text(s2, 0.7, 4.4, 5.0, 0.4, [[("另一种中文字体", 14, bs.INK, False, False)]])
    from pptx.oxml.ns import qn
    for r in s2.shapes[-1]._element.iter(qn("a:r")):
        rPr = r.find(qn("a:rPr"))
        ea = rPr.find(qn("a:ea"))
        if ea is None:
            ea = rPr.makeelement(qn("a:ea"), {})
            rPr.append(ea)
        ea.set("typeface", "Weird CJK Face")
if variant == "offchart":
    dk.native_chart(s2, 0.7, 3.4, 4.0, 1.4, ["a", "b"], [("x", [1, 2])], kind="bar",
                    palette=[RGBColor(0x00, 0xA8, 0x6B)])                   # jade series
if variant == "nologo":
    pass
prs.save(out)
'''
(TMP / "build_fixture.py").write_text(BUILD, encoding="utf-8")
# a colourful "photo" the check must ignore — every hue on the wheel
ph = Image.new("RGB", (120, 60))
for i in range(120):
    for j in range(60):
        ph.putpixel((i, j), ((i * 7) % 256, (j * 11) % 256, ((i + j) * 5) % 256))


def build(brand_dir, variant):
    ph.save(brand_dir / "photo.png")
    out = brand_dir / "deck_{}.pptx".format(variant)
    r = subprocess.run([sys.executable, str(TMP / "build_fixture.py"), str(brand_dir), variant,
                        str(out)], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=str(SCRIPTS)))
    check(r.returncode == 0, "fixture build {} {} failed:\n{}".format(brand_dir.name, variant,
                                                                       r.stdout + r.stderr))
    return out


def findings(deck, brand_dir, *extra):
    r = subprocess.run([sys.executable, BK, "check", str(deck), "--brand",
                        str(brand_dir / "brand.json"), "--json"] + list(extra),
                       capture_output=True, text=True)
    code, out = r.returncode, r.stdout
    try:
        js = json.loads(out)
    except Exception:
        js = {"findings": [{"code": "UNPARSEABLE", "why": out}]}
    return code, js


for bdir in (TW, QH):
    deck = build(bdir, "onbrand")
    code, js = findings(deck, bdir)
    check(code == 0 and not js["findings"],
          "ON-BRAND {} deck has 0 findings (target 0), got {}".format(
              bdir.name, json.dumps(js["findings"], ensure_ascii=False)[:1500]))
    for variant, want in (("offcolour", "COLOUR OFF BRAND"), ("offtext", "COLOUR OFF BRAND"),
                          ("offfont", "FONT OFF BRAND"), ("offchart", "COLOUR OFF BRAND")):
        dv = build(bdir, variant)
        code, js = findings(dv, bdir)
        got = [f for f in js["findings"] if f["code"] == want]
        check(code == 1 and got and all(f.get("slide") for f in got),
              "OFF-BRAND {} {} is caught as {} with a slide number, got {}".format(
                  bdir.name, variant, want, json.dumps(js["findings"], ensure_ascii=False)[:600]))
    if bdir is QH:
        dv = build(bdir, "offeafont")
        code, js = findings(dv, bdir)
        check(code == 1 and any(f["code"] == "FONT OFF BRAND" and f["value"] == "Weird CJK Face"
                                for f in js["findings"]),
              "an off-brand CJK face is caught: {}".format(js["findings"]))
    dv = build(bdir, "nologo")
    code, js = findings(dv, bdir)
    check(code == 1 and any(f["code"] == "LOGO MISSING" for f in js["findings"]),
          "a single-entity {} deck with no logo is caught: {}".format(bdir.name, js["findings"]))
    code, js = findings(dv, bdir, "--multi-entity")
    check(code == 0, "…and the logo rule is not applied to a multi-entity deck: {}".format(js))

code, out = run("check", QH / "deck_onbrand.pptx", "--brand", NL / "brand.json")
check(code == 1 and "CJK UNCHECKED" in out, "a CJK deck against a kit confirmed without --lang is "
      "refused:\n" + out)

Presentation().save(TMP / "empty.pptx")
code, out = run("check", TMP / "empty.pptx", "--brand", TW / "brand.json")
check(code == 1 and "no slides" in out, "an EMPTY deck is refused, never checked clean:\n" + out)
code, out = run("check", TMP / "nope.pptx", "--brand", TW / "brand.json")
check(code == 2 and "nope.pptx" in out, "a missing deck names the file:\n" + out)

# the photo was ignored: no finding names a picture
code, js = findings(TW / "deck_onbrand.pptx", TW)
check(not any("Picture" in str(f.get("shape")) for f in js["findings"]), "pictures are ignored")

# ── gate: both runtimes, one module ───────────────────────────────────────────────────────────
import brand_kit as bk  # noqa: E402
import deck_gates as dg  # noqa: E402

for name in ("render_deck.py", "codex_delivery_gate.py", "deck_gates.py"):
    s = (SCRIPTS / name).read_text(encoding="utf-8")
    check("brand_kit" in s, "{} consumes the brand_kit contract".format(name))
check("_gate_section('brand')" in (SCRIPTS / "render_deck.py").read_text(encoding="utf-8"),
      "render_deck --gate-check has a `brand` section")

check(bk.recorded_brand({}) is None and bk.recorded_brand({"brand": None}) is None,
      "no brand section -> no brand gate")
check(bk.section_faults({"file": "brand.json"}) == [], "a {file} section is well-shaped")
check(bk.section_faults({"file": "<path to confirmed brand.json>"}),
      "a placeholder file is refused")
check(bk.section_faults({"waived": "co-branded with the hospital, their palette leads slides 3-5",
                         "waived_category": "co-branded"}) == [], "a categorised waiver is accepted")
check(bk.section_faults({"waived": "x"}), "a bare / uncategorised waiver is refused")
g = dg.template(3)
check("brand" in g, "deck_gates init scaffolds the `brand` section")
g["brand"] = {"file": "<path to confirmed brand.json>"}
check(any("brand" in p for p in dg.check(g)), "deck_gates check reports a placeholder brand file")

shutil_deck = TW / "deck_offcolour.pptx"
import render_deck as rd  # noqa: E402

for sec, expect_fail in (({"file": "brand.json"}, True),
                         ({"waived": "user approved the violet launch band on slide 3 in review",
                           "waived_category": "user-approved-deviation"}, False)):
    err = io.StringIO()
    died = False
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            rd._brand_gate(str(shutil_deck), {"brand": sec})
    except SystemExit:
        died = True
    check(died == expect_fail, "render_deck brand gate on an off-brand deck with {} -> died={}: {}"
          .format(sec, died, err.getvalue()[:300]))
err = io.StringIO()
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rd._brand_gate(str(TW / "deck_onbrand.pptx"), {"brand": {"file": "brand.json"}})
    ok_on = True
except SystemExit:
    ok_on = False
check(ok_on, "render_deck brand gate passes the on-brand deck: " + err.getvalue()[:300])

import codex_delivery_gate as cdg  # noqa: E402

errs: list[str] = []
with contextlib.redirect_stdout(io.StringIO()):
    cdg.check_brand({"brand": {"file": "brand.json"}}, shutil_deck, errs)
check(errs and any("COLOUR OFF BRAND" in e for e in errs), "codex gate fails the off-brand deck: {}"
      .format(errs))
errs = []
with contextlib.redirect_stdout(io.StringIO()):
    cdg.check_brand({"brand": {"file": "brand.json"}}, TW / "deck_onbrand.pptx", errs)
check(not errs, "codex gate passes the on-brand deck: {}".format(errs))
errs = []
with contextlib.redirect_stdout(io.StringIO()):
    cdg.check_brand({}, shutil_deck, errs)
check(not errs, "no brand section -> the codex gate does not apply one")

# a brand.json edited after confirm is refused (the roles were reviewed, the edit was not)
b = load(TW / "brand.json")
b["colors"].append({"hex": "#7B2CBF", "role": "accent", "source": "hand edit"})
(TMP / "edited.json").write_text(json.dumps(b), encoding="utf-8")
code, out = run("check", TW / "deck_offcolour.pptx", "--brand", TMP / "edited.json")
check(code != 0 and "confirm" in out.lower(), "an edited-after-confirm brand.json is refused:\n" + out)

# ── docs that ship ────────────────────────────────────────────────────────────────────────────
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
runbook = (ROOT / "references" / "codex-runtime.md").read_text(encoding="utf-8")
inv = (ROOT / "references" / "file-inventory.md").read_text(encoding="utf-8")
for name, txt in (("SKILL.md", skill), ("codex-runtime.md", runbook), ("file-inventory.md", inv)):
    check("brand_kit.py" in txt, "{} names brand_kit.py".format(name))
for sub in ("extract", "review", "confirm", "style", "check"):
    check("brand_kit.py " + sub in runbook, "the Codex runbook carries `brand_kit.py {}`".format(sub))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("\n[test_brand_kit] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
