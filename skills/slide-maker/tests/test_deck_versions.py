#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deck_versions.py — snapshot, list, diff, restore and prune a deck's versions.

The feature exists so a user can see exactly what a rebuild changed, slide by slide — above all any
NUMBER that changed, because the never-invent rule makes those the lines a person must re-check —
and can go back to an earlier version of the whole deck or of one slide.

What this suite holds the tool to, in both directions:

  · slide ALIGNMENT reads an inserted / deleted / moved / retitled slide as that one event, never as
    "every later slide changed"; an unchanged rebuild reports 0 changes (a rebuild re-zips the
    package, so the byte hash differs while nothing changed);
  · numbers are tokenised the way decks write them (1,350 · 12% · 9.8 万 · full-width digits) and
    are reported FIRST;
  · renders are snapshotted only when they belong to THIS pptx (a stale render folder is said to be
    stale, never filed as this version's pictures);
  · the diff page is a plain file:// page: relative image paths that resolve from the deck folder,
    no network reference;
  · `restore --slides` goes through the build script's SOURCE (AST) and REFUSES on every ambiguity —
    no build script, a slide count the functions do not explain, a function the current script no
    longer has or defines twice, a helper it needs that is gone;
  · a whole restore snapshots the current state first, so it can be undone;
  · deck_cycle.py snapshots automatically after a clean build, never after a failed one, and the
    snapshot never changes the cycle's exit code;
  · every successful command prints a NEXT: line; every refusal names the cause and the fix.

Run:  python3 tests/test_deck_versions.py
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
DV = SCRIPTS / "deck_versions.py"
CYCLE = SCRIPTS / "deck_cycle.py"
sys.path.insert(0, str(SCRIPTS))

for _m in ("pptx", "PIL", "numpy"):
    try:
        __import__(_m)
    except ImportError:
        print(f"skip: {_m} not installed")
        raise SystemExit(0)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else f"{name}  {detail}")
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  {detail}"))


TMP = pathlib.Path(tempfile.mkdtemp(prefix="deckver-"))

HEADER = '''import sys
sys.path.insert(0, {scripts!r})
import deckkit as dk
from pptx.dml.color import RGBColor as C
dk.FONT = "Helvetica Neue"
dk.EAFONT = "Hiragino Sans GB" if sys.platform == "darwin" else "Noto Sans CJK SC"
INK = C.from_string("1F3B2F")


def _page(prs, title, lines):
    s = dk.add_slide(prs)
    dk.slide_background(s, "F5F1E6")
    dk.text(s, 0.6, 0.5, 8.8, 0.7, [[(title, 28, INK, True, False)]])
    for i, line in enumerate(lines):
        dk.text(s, 0.6, 1.6 + 0.6 * i, 8.0, 0.5, [[(line, 14, INK, False, False)]])
    return s
'''


def script_for(slides, order=None):
    """A build script with one `def slide_NN(prs)` per slide, called in order from main()."""
    src = HEADER.format(scripts=str(SCRIPTS))
    for fn, title, lines in slides:
        src += "\n\ndef {}(prs):\n    _page(prs, {!r}, {!r})\n".format(fn, title, list(lines))
    names = order or [fn for fn, _t, _l in slides]
    src += ("\n\ndef main():\n    prs = dk.blank_deck()\n    for build in ({},):\n        build(prs)\n"
            "    dk.lint_layout(prs, strict=True)\n    prs.save(\"deck.pptx\")\n"
            "    print(\"saved ->\", \"deck.pptx\")\n\n\nif __name__ == \"__main__\":\n    main()\n"
            ).format(", ".join(names))
    return src


def make_deck(name, slides, order=None):
    d = TMP / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "build_deck.py").write_text(script_for(slides, order), encoding="utf-8")
    return d


def build(d):
    p = subprocess.run([sys.executable, "build_deck.py"], cwd=str(d), capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    return d / "deck.pptx"


def dv(*args, cwd=None):
    p = subprocess.run([sys.executable, str(DV)] + [str(a) for a in args], capture_output=True,
                       text=True, cwd=str(cwd) if cwd else None)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def cycle(d, *args):
    p = subprocess.run([sys.executable, str(CYCLE), "build_deck.py"] + list(args), cwd=str(d),
                       capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def versions(d):
    v = d / ".versions"
    return sorted(p.name for p in v.iterdir() if p.is_dir()) if v.is_dir() else []


def manifest(d, v):
    return json.loads((d / ".versions" / v / "manifest.json").read_text(encoding="utf-8"))


BASE = [
    ("slide_01", "Repair café annual report", ["Prepared for the board"]),
    ("slide_02", "How an evening runs", ["Bring it broken", "Fix it with a volunteer"]),
    ("slide_03", "Results this year", ["Repairs: 1,350", "Success rate: 72%", "Visitors: 9.8 万"]),
    ("slide_04", "Who volunteers", ["Retired engineers", "Students"]),
    ("slide_05", "Next year", ["Two more halls", "A tool library"]),
]

import deck_versions as V  # noqa: E402  (after the skip guard; fails loudly if the script is missing)

# ───────────────────────────────────────────── numbers are tokenised the way decks write them
toks = V.numbers_in("Repairs 1,350 · up 12% · 用户 9.8 万 · ＋１２％ · v2 build · −3.5%")
check("numbers: thousands separator kept whole (1,350 is one number, not 1 and 350)", "1,350" in toks, toks)
check("numbers: a percent keeps its sign of being a percent (12%)", "12%" in toks, toks)
check("numbers: CJK magnitude 9.8 万 is one token", "9.8万" in toks, toks)
check("numbers: full-width digits normalise (＋１２％ → +12%)", "+12%" in toks, toks)
check("numbers: a digit glued to an identifier (v2) is not a number", not any(t == "2" for t in toks), toks)
check("numbers: a unicode minus is kept as a sign (−3.5%)", "−3.5%" in toks, toks)
check("numbers: a sentence with no digits has none", V.numbers_in("no digits here, 没有数字") == [])

# ───────────────────────────────────────────── snapshot: create, dedupe, --keep
d = make_deck("basic", BASE)
build(d)
rc, out = dv("snapshot", d, "--note", "first look")
check("snapshot creates v001", rc == 0 and versions(d) == ["v001"], out[-400:])
check("snapshot prints a NEXT: line", "NEXT:" in out, out[-300:])
m = manifest(d, "v001")
check("manifest records version/created/note/pptx_sha256/slides",
      all(k in m for k in ("version", "created", "note", "pptx_sha256", "slides")) and m["note"] == "first look", m.keys())
check("manifest has one entry per slide with title, text_lines and numbers",
      len(m["slides"]) == 5 and m["slides"][2]["title"] == "Results this year"
      and "1,350" in m["slides"][2]["numbers"] and m["slides"][2]["text_lines"], m["slides"][2])
check("the build script is stored in the version", (d / ".versions/v001/build_deck.py").is_file())
check("the pptx is stored in the version", (d / ".versions/v001/deck.pptx").is_file())
check("the slide→function map is recorded from the build script's AST",
      m.get("slide_functions") == ["slide_01", "slide_02", "slide_03", "slide_04", "slide_05"], m.get("slide_functions"))
check("no render folder → manifest says why renders are absent", m.get("renders") is False and m.get("renders_note"), m.get("renders_note"))

rc, out = dv("snapshot", d)
check("an unchanged pptx makes no new version, and says so", rc == 0 and versions(d) == ["v001"]
      and "unchanged" in out.lower(), out[-300:])
build(d)                                       # rebuild: new zip bytes, same content
rc, out = dv("snapshot", d)
check("a REBUILD of the same deck (new zip bytes, same content) is still 'unchanged'",
      versions(d) == ["v001"], out[-300:])
rc, out = dv("snapshot", d, "--keep")
check("--keep on an unchanged deck marks the latest version kept instead of duplicating it",
      versions(d) == ["v001"] and manifest(d, "v001").get("keep") is True, out[-300:])

# ───────────────────────────────────────────── diff: unchanged deck → 0 changes
shutil.copytree(d / ".versions" / "v001", d / ".versions" / "v002")
mm = manifest(d, "v002")
mm["version"] = "v002"
(d / ".versions/v002/manifest.json").write_text(json.dumps(mm), encoding="utf-8")
rc, out = dv("diff", d)
check("diff of two identical versions reports 0 changes", rc == 0 and re.search(r"\b0 changed\b", out)
      and "0 added" in out and "0 removed" in out and "0 moved" in out, out[:600])
check("diff prints a NEXT: line", "NEXT:" in out)
shutil.rmtree(d / ".versions" / "v002")


def two_versions(name, before, after, order_after=None):
    dd = make_deck(name, before)
    build(dd)
    dv("snapshot", dd)
    (dd / "build_deck.py").write_text(script_for(after, order_after), encoding="utf-8")
    build(dd)
    rc, out = dv("snapshot", dd)
    assert rc == 0 and len(versions(dd)) == 2, out
    return dd


# ───────────────────────────────────────────── an inserted slide in the middle
ins = BASE[:3] + [("slide_03b", "Pilot sites", ["Leiden", "Delft"])] + BASE[3:]
d_ins = two_versions("insert", BASE, ins)
rc, out = dv("diff", d_ins)
check("insert: reads as 1 added, 0 changed — not as every later slide changed",
      "1 added" in out and re.search(r"\b0 changed\b", out) and "0 removed" in out, out[:900])
check("insert: the added slide is named with its title", "Pilot sites" in out, out[:900])
check("insert: slides after it are matched across the shift (4 → 5)", re.search(r"\b4 → 5\b", out), out[:1200])

# ───────────────────────────────────────────── a deleted slide
dele = BASE[:1] + BASE[2:]
d_del = two_versions("delete", BASE, dele)
rc, out = dv("diff", d_del)
check("delete: reads as 1 removed, 0 changed", "1 removed" in out and re.search(r"\b0 changed\b", out)
      and "0 added" in out, out[:900])
check("delete: the removed slide is named", "How an evening runs" in out)

# ───────────────────────────────────────────── a moved slide
order = ["slide_01", "slide_03", "slide_04", "slide_05", "slide_02"]
d_mov = two_versions("move", BASE, BASE, order_after=order)
rc, out = dv("diff", d_mov)
check("move: reads as 1 moved, 0 added/removed/changed", "1 moved" in out and "0 added" in out
      and "0 removed" in out and re.search(r"\b0 changed\b", out), out[:900])

# ───────────────────────────────────────────── a retitled slide
ret = [list(s) for s in BASE]
ret[3] = ("slide_04", "The people who fix things", BASE[3][2])
d_ret = two_versions("retitle", BASE, [tuple(s) for s in ret])
rc, out = dv("diff", d_ret)
check("retitle: the same slide with a new title is matched, not removed+added",
      "0 added" in out and "0 removed" in out and "retitled" in out.lower(), out[:900])

# ───────────────────────────────────────────── CJK titles + numbers changed, flagged first
cjk = [("slide_01", "年度报告", ["面向理事会"]),
       ("slide_02", "运营结果", ["用户数 9.8 万", "同比增长 12%", "维修 1,350 件"]),
       ("slide_03", "下一步", ["再开两个场地"])]
cjk2 = [list(s) for s in cjk]
cjk2[1] = ("slide_02", "运营结果", ["用户数 10.2 万", "同比增长 15%", "维修 1,350 件"])
d_cjk = two_versions("cjk", cjk, [tuple(s) for s in cjk2])
rc, out = dv("diff", d_cjk)
check("CJK: the changed slide is matched by its CJK title", "运营结果" in out and "0 added" in out, out[:900])
check("CJK: 9.8万 → 10.2万 is reported as a changed number", re.search(r"9\.8万\s*→\s*10\.2万", out), out[:900])
check("CJK: 12% → 15% is reported as a changed number", re.search(r"12%\s*→\s*15%", out), out[:900])
check("CJK: an unchanged number (1,350) is NOT reported as changed", "1,350 →" not in out, out[:900])
npos, spos = out.find("NUMBERS"), out.find("SLIDES")
check("numbers are reported BEFORE the per-slide list", 0 <= npos < spos, (npos, spos))
html = d_cjk / "versions-diff_v001_v002.html"
check("diff writes versions-diff_vA_vB.html in the deck folder", html.is_file())
page = html.read_text(encoding="utf-8") if html.is_file() else ""
check("the diff page references nothing on the network", not re.search(r"(src|href)=[\"']https?:", page))
check("the diff page highlights the changed number", "10.2万" in page and "9.8万" in page)

# ───────────────────────────────────────────── restore --slides refuses on every ambiguity
rc, out = dv("restore", d_ins, "v001", "--slides", "9")
check("restore --slides refuses a slide number the version does not have", rc != 0 and "v001" in out
      and "5 slide" in out, out[-400:])
rc, out = dv("restore", d_ins, "v001", "--slides", "2")
check("restore --slides on an unchanged slide says nothing changed (no silent rewrite)",
      rc != 0 and "unchanged" in out.lower(), out[-400:])

d_nob = TMP / "nobuild"
d_nob.mkdir()
shutil.copy(d / "deck.pptx", d_nob / "deck.pptx")
rc, out = dv("snapshot", d_nob)
check("a deck with no build script can still be snapshotted", rc == 0 and versions(d_nob) == ["v001"], out[-300:])
rc, out = dv("restore", d_nob, "v001", "--slides", "1")
check("restore --slides REFUSES on a deck with no build script, and says why", rc != 0
      and "build script" in out.lower(), out[-400:])

two = TMP / "twoslides"
two.mkdir()
src = script_for(BASE[:2]).replace("    _page(prs, 'How an evening runs'",
                                   "    _page(prs, 'Extra page', [])\n    _page(prs, 'How an evening runs'")
(two / "build_deck.py").write_text(src, encoding="utf-8")
build(two)
dv("snapshot", two)
rc, out = dv("restore", two, "v001", "--slides", "1")
check("restore --slides REFUSES when the functions do not explain the slide count (2 functions, 3 slides)",
      rc != 0 and "3 slide" in out and "2" in out, out[-500:])

d_gone = two_versions("gone", BASE, ins)
txt = (d_gone / "build_deck.py").read_text(encoding="utf-8").replace("def slide_03(", "def slide_three(") \
    .replace("slide_03,", "slide_three,")
(d_gone / "build_deck.py").write_text(txt, encoding="utf-8")
rc, out = dv("restore", d_gone, "v001", "--slides", "3")
check("restore --slides REFUSES when the current script no longer defines the function",
      rc != 0 and "slide_03" in out, out[-400:])
txt2 = (d_gone / "build_deck.py").read_text(encoding="utf-8").replace("def slide_three(", "def slide_03(") \
    .replace("slide_three,", "slide_03,") + "\n\ndef slide_03(prs):\n    pass\n"
(d_gone / "build_deck.py").write_text(txt2, encoding="utf-8")
rc, out = dv("restore", d_gone, "v001", "--slides", "3")
check("restore --slides REFUSES when the current script defines the function twice",
      rc != 0 and ("twice" in out.lower() or "2 definitions" in out.lower()), out[-400:])

# ───────────────────────────────────────────── whole restore: snapshot first, undoable
d_w = two_versions("whole", BASE, ins)
before_script = (d_w / "build_deck.py").read_text(encoding="utf-8")
rc, out = dv("restore", d_w, "v001")
check("whole restore succeeds and prints NEXT:", rc == 0 and "NEXT:" in out, out[-500:])
check("whole restore copied back the build script", "Pilot sites" not in (d_w / "build_deck.py").read_text(encoding="utf-8"))
check("whole restore copied back the pptx",
      V.content_sha(d_w / "deck.pptx") == manifest(d_w, "v001")["content_sha256"])
# the current state was v002 already (unchanged) — restoring again after an edit must snapshot it first
(d_w / "build_deck.py").write_text(before_script, encoding="utf-8")
build(d_w)
n_before = len(versions(d_w))
rc, out = dv("restore", d_w, "v001")
check("whole restore SNAPSHOTS the current state first when it is not saved yet",
      len(versions(d_w)) == n_before + 1 or "already saved: the state before this restore is v002" in out, (versions(d_w), out[-400:]))
(d_w / "build_deck.py").write_text("# edited but not rebuilt\n" + before_script, encoding="utf-8")
n_before = len(versions(d_w))
rc, out = dv("restore", d_w, "v001")
check("…including build-script edits that were never rebuilt (the pptx alone would not show them)",
      len(versions(d_w)) == n_before + 1, (versions(d_w), out[-400:]))
last = versions(d_w)[-1]
check("…and the backup holds the edited script, so the restore is undoable",
      (d_w / ".versions" / last / "build_deck.py").read_text(encoding="utf-8").startswith("# edited but not rebuilt"))

# ───────────────────────────────────────────── prune keeps --keep versions
d_p = make_deck("prune", BASE)
for i in range(5):
    sl = [list(s) for s in BASE]
    sl[4] = ("slide_05", "Next year", ["Two more halls", "Round {}".format(i)])
    (d_p / "build_deck.py").write_text(script_for([tuple(s) for s in sl]), encoding="utf-8")
    build(d_p)
    dv("snapshot", d_p, *(["--keep"] if i == 0 else []))
check("five different builds make five versions", len(versions(d_p)) == 5, versions(d_p))
rc, out = dv("prune", d_p, "--keep-last", "2")
check("prune --keep-last 2 keeps the newest two plus every --keep version",
      versions(d_p) == ["v001", "v004", "v005"], (versions(d_p), out[-300:]))
rc, out = dv("list", d_p)
check("list shows each version with its slide count", "v005" in out and "5 slides" in out, out[-500:])
check("list ends with the hand-off version line against the version the user last saw",
      re.search(r"version: v005 .*since v001", out), out[-400:])

# ───────────────────────────────────────────── the realistic flow, through deck_cycle with renders
flow = make_deck("flow", BASE)
rc, out = cycle(flow, "--render")
check("deck_cycle: a clean build + render snapshots automatically (v001)", versions(flow) == ["v001"], out[-800:])
check("deck_cycle: the auto snapshot reports itself in the cycle output", "versions" in out and "v001" in out, out[-600:])
m1 = manifest(flow, "v001")
check("deck_cycle: renders that belong to this pptx are stored with the version",
      m1.get("renders") is True and (flow / ".versions/v001/render/slide03.png").is_file(), m1.get("renders_note"))
check("deck_cycle: the cycle's exit code is the lint's, not the snapshot's", rc in (0, 1), rc)

edit = [list(s) for s in BASE]
edit[2] = ("slide_03", "Results this year", ["Repairs: 1,420", "Success rate: 75%", "Visitors: 10.2 万"])
edit = [tuple(s) for s in edit]
edit = edit[:3] + [("slide_03b", "Pilot sites", ["Leiden", "Delft"])] + edit[3:]
(flow / "build_deck.py").write_text(script_for(edit), encoding="utf-8")
rc, out = cycle(flow, "--render")
check("deck_cycle: the edited rebuild snapshots v002", versions(flow) == ["v001", "v002"], out[-600:])
rc, out = dv("diff", flow)
REPORT_1 = out
check("flow diff: slide 3's three numbers are flagged", all(re.search(p, out) for p in
      (r"1,350\s*→\s*1,420", r"72%\s*→\s*75%", r"9\.8万\s*→\s*10\.2万")), out[:1500])
check("flow diff: the inserted slide reads as added", "1 added" in out and "Pilot sites" in out, out[:1500])
check("flow diff: 1 changed — only slide 3", re.search(r"\b1 changed\b", out), out[:1500])
check("flow diff: a visual change measure from the renders is reported", "visual" in out.lower(), out[:1500])
page = (flow / "versions-diff_v001_v002.html").read_text(encoding="utf-8")
srcs = re.findall(r"<img[^>]+src=\"([^\"]+)\"", page)
check("flow diff page: images use RELATIVE paths that resolve from the deck folder",
      srcs and all(not s.startswith(("/", "file:", "http")) and (flow / s).is_file() for s in srcs), srcs[:4])

# a stale render folder is not filed as the next version's pictures
(flow / "build_deck.py").write_text(script_for(edit[:-1]), encoding="utf-8")
rc, out = cycle(flow)                         # build only: render/ still holds v002's pictures
m3 = manifest(flow, versions(flow)[-1])
check("a build-only cycle snapshots WITHOUT the now-stale renders, and says so",
      m3.get("renders") is False and "stale" in (m3.get("renders_note") or ""), m3.get("renders_note"))
shutil.rmtree(flow / ".versions" / versions(flow)[-1])
(flow / "build_deck.py").write_text(script_for(edit), encoding="utf-8")
rc, out = cycle(flow, "--render")             # back to v002's deck: deduplicated, no new version
check("rebuilding the v002 deck again makes no new version", versions(flow) == ["v001", "v002"], out[-400:])

rc, out = dv("restore", flow, "v001", "--slides", "3")
check("restore v001 --slides 3 succeeds and points at the rebuild", rc == 0 and "NEXT:" in out
      and "deck_cycle.py" in out, out[-600:])
cur = (flow / "build_deck.py").read_text(encoding="utf-8")
check("restore --slides replaced slide_03's source with v001's", "Repairs: 1,350" in cur and "1,420" not in cur)
check("restore --slides left the inserted slide and the rest of the script alone",
      "Pilot sites" in cur and cur.count("def slide_") == 6)
rc, out = cycle(flow, "--render")
rc, out = dv("diff", flow)
REPORT_2 = out
check("after the rebuild, diff shows slide 3's numbers changed BACK",
      re.search(r"1,420\s*→\s*1,350", out) and re.search(r"75%\s*→\s*72%", out), out[:1200])
rc, out = dv("diff", flow, "v001", versions(flow)[-1])
check("and against v001, slide 3 is unchanged and the only event is the inserted slide",
      re.search(r"\b0 changed\b", out) and "1 added" in out, out[:1200])

# ───────────────────────────────────────────── deck_cycle never snapshots a failed build
bad = make_deck("badbuild", BASE)
(bad / "build_deck.py").write_text(script_for(BASE).replace("dk.text(s, 0.6, 1.6 + 0.6 * i, 8.0, 0.5,",
                                                            "dk.text(s, 14.0, 9.9, 8.0, 0.5,"), encoding="utf-8")
rc, out = cycle(bad)
check("deck_cycle: a build that hits a CRITICAL fault is not snapshotted", rc == 2 and versions(bad) == [], out[-300:])

# ───────────────────────────────────────────── page numbers are chrome, not content
FOOT = HEADER.format(scripts=str(SCRIPTS)) + '''

def _numbered(prs, title, lines, n, total):
    s = _page(prs, title, lines)
    dk.text(s, 0.6, 5.0, 4.0, 0.3, [[("Repair café · {} / {}".format(n, total), 10, INK, False, False)]])

'''


def footer_script(slides):
    src = FOOT
    total = len(slides)
    for k, (fn, title, lines) in enumerate(slides, 1):
        src += "\ndef {}(prs):\n    _numbered(prs, {!r}, {!r}, {}, {})\n".format(fn, title, list(lines), k, total)
    src += ("\n\ndef main():\n    prs = dk.blank_deck()\n    for build in ({},):\n        build(prs)\n"
            "    prs.save(\"deck.pptx\")\n\n\nmain()\n").format(", ".join(fn for fn, _t, _l in slides))
    return src


d_ft = TMP / "footer"
d_ft.mkdir()
(d_ft / "build_deck.py").write_text(footer_script(BASE), encoding="utf-8")
build(d_ft)
dv("snapshot", d_ft)
(d_ft / "build_deck.py").write_text(footer_script(ins), encoding="utf-8")
build(d_ft)
dv("snapshot", d_ft)
rc, out = dv("diff", d_ft)
check("a numbered footer (\"· 3 / 5\" → \"· 4 / 6\") does not make an insert read as every slide changed",
      "1 added" in out and re.search(r"\b0 changed\b", out), out[:900])
check("…and its page numbers are not reported as changed numbers", "NUMBERS — none" in out, out[:600])

# ───────────────────────────────────────────── native chart values are numbers too
CHART = HEADER.format(scripts=str(SCRIPTS)) + '''
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches


def slide_01(prs):
    s = _page(prs, "Repairs by month", [])
    cd = CategoryChartData()
    cd.categories = ["Jan", "Feb", "Mar"]
    cd.add_series("Repairs", VALUES)
    s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.5), Inches(8), Inches(3.5), cd)


def main():
    prs = dk.blank_deck()
    for build in (slide_01,):
        build(prs)
    prs.save("deck.pptx")


main()
'''
d_ch = TMP / "chart"
d_ch.mkdir()
(d_ch / "build_deck.py").write_text(CHART.replace("VALUES", "(110, 125, 140)"), encoding="utf-8")
build(d_ch)
dv("snapshot", d_ch)
(d_ch / "build_deck.py").write_text(CHART.replace("VALUES", "(110, 128, 140)"), encoding="utf-8")
build(d_ch)
dv("snapshot", d_ch)
rc, out = dv("diff", d_ch)
check("a native chart's changed series value is a changed number (125 → 128)", re.search(r"125\s*→\s*128", out), out[:700])

# ───────────────────────────────────────────── an empty deck
d_em = TMP / "empty"
d_em.mkdir()
EMPTY = HEADER.format(scripts=str(SCRIPTS)) + "\n\nprs = dk.blank_deck()\nprs.save(\"deck.pptx\")\n"
(d_em / "build_deck.py").write_text(EMPTY, encoding="utf-8")
build(d_em)
rc, out = dv("snapshot", d_em)
check("an empty deck (0 slides) snapshots without error", rc == 0 and versions(d_em) == ["v001"], out[-300:])
(d_em / "build_deck.py").write_text(script_for(BASE[:1]), encoding="utf-8")
build(d_em)
dv("snapshot", d_em)
rc, out = dv("diff", d_em)
check("an empty deck → one slide reads as 1 added", rc == 0 and "1 added" in out, out[:500])

# ───────────────────────────────────────────── refusals name the fix
rc, out = dv("diff", TMP / "nobuild_missing")
check("diff on a folder that does not exist fails with a sentence, exit 2", rc == 2 and "no such" in out.lower(), out[-200:])
rc, out = dv("diff", d_nob)
check("diff with only one version says so and what to do", rc != 0 and "snapshot" in out, out[-300:])
rc, out = dv("--help")
check("--help works", rc == 0 and "snapshot" in out)

print("\n── realistic flow, diff v001 → v002 ──\n" + REPORT_1)
print("── after restore v001 --slides 3 + rebuild ──\n" + REPORT_2)
print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
raise SystemExit(1 if FAIL else 0)
