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

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_visual_languages] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
