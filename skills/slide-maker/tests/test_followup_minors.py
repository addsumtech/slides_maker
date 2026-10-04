#!/usr/bin/env python3
"""Deferred minors from P0-P2, fixed or pinned: function defaults restored with the palette, a slot id without plan= says so, the overflow message leads with the total, a photo is not a cut-out, mark()'s size error, the seam space off a highlight, frosted_panel's .alpha."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)



import deckkit as dk, visual_languages as vl, image_fx
from PIL import Image
td = Path(tempfile.mkdtemp())
# P2 #M1: a palette set by an example leaked into every later one through the FUNCTION DEFAULTS set_palette rewrites
snap = dk._state_snapshot()
before_kw = dict(dk.scorecard.__kwdefaults__ or {})
before_deep = dk.DEEP
vl.use("editorial", dk.blank_deck(13.333, 7.5), ground="ink")
check(dk.DEEP != before_deep or dict(dk.scorecard.__kwdefaults__ or {}) != before_kw, "precondition: use() changed the palette")
dk._state_restore(snap)
check(dict(dk.scorecard.__kwdefaults__ or {}) == before_kw and dk.DEEP == before_deep,
      "the snapshot restores globals AND function keyword defaults")
smoke = (ROOT / "scripts" / "smoke_deckkit.py").read_text(encoding="utf-8")
check("_state_restore" in smoke, "smoke restores state through the helper that covers keyword defaults")
# P2 #M3: a slot id with no plan= says how to pass one
k = vl.use("soft", dk.blank_deck(13.333, 7.5))
try:
    k.cover(k.new_slide(), title="Repair night", image="hero")
    fails.append("an unknown image 'hero' was accepted")
except FileNotFoundError as e:
    check("plan=" in str(e) and "image_dir=" in str(e), "the missing-image error names plan=/image_dir= for a slot id: {}".format(e))
# ...and WITH a plan, a misspelt slot id lists the plan's slots instead of asking for plan= again
k = vl.use("soft", dk.blank_deck(13.333, 7.5), plan={"slots": [{"id": "hero", "slide": 1}, {"id": "bench", "slide": 3}]},
           image_dir=str(td))
try:
    k.cover(k.new_slide(), title="Repair night", image="heor")
    fails.append("an unknown slot 'heor' was accepted")
except FileNotFoundError as e:
    check("hero" in str(e) and "bench" in str(e) and "pass plan=" not in str(e),
          "with a plan, a misspelt slot id lists the plan's slots: {}".format(e))
# P2 #M4: the overflow message leads with the total the column could not hold
k = vl.use("editorial", dk.blank_deck(13.333, 7.5))
try:
    k.quote(k.new_slide(), quote="word " * 400, attribution="line " * 40)   # 70 words FIT a 10in column
    fails.append("an impossible quote page was accepted")
except vl.VLTextOverflow as e:
    m = str(e)
    check("all fields together need" in m and m.index("all fields together") < m.index("longest"), "the message leads with the total: {}".format(m))
# P0 #M7: a "cut-out" with a single transparent pixel is a photo, not a cut-out
im = Image.new("RGBA", (200, 200), (180, 120, 60, 255))
im.putpixel((0, 0), (0, 0, 0, 0))
im.save(td / "photo.png")
try:
    image_fx.sticker_outline(str(td / "photo.png"))
    fails.append("sticker_outline outlined a photo with one transparent pixel")
except ValueError as e:
    check("transparent" in str(e) or "cut" in str(e), "the refusal says why: {}".format(e))
cut = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
for y in range(40, 160):
    for x in range(50, 150):
        cut.putpixel((x, y), (180, 120, 60, 255))
cut.save(td / "cut.png")
image_fx.sticker_outline(str(td / "cut.png"))                      # a real cut-out still works
# P0 minors already fixed in place — pinned so they stay fixed
try:
    dk.mark(("No size", None, dk.DEEP, True, False), "D4FF3A")
    fails.append("mark() accepted a run with no size")
except TypeError as e:
    check("size" in str(e), "mark() says the size is missing: {}".format(e))
old = dk.CJK_SPACING
dk.CJK_SPACING = "spaced"
try:
    para = dk._pangu_para([dk.mark(("速度", 20, dk.DEEP, True, False), "D4FF3A"), ("3倍", 20, dk.DEEP, False, False)])
    check(not para[0][0].endswith(" ") and para[1][0].startswith(" "), "the seam space stays off the highlighted run: {}".format([r[0] for r in para]))
finally:
    dk.CJK_SPACING = old
bg = td / "bg.png"
Image.new("RGB", (800, 450), (40, 90, 140)).save(bg)
prs = dk.blank_deck(10, 5.625)
s = dk.add_slide(prs)
pic = dk.picture(s, str(bg), 0, 0, 10, 5.625, fit="cover", alt="a blue field")
g = dk.frosted_panel(s, pic, 5.4, 0.8, 4.0, 2.2)
check(getattr(g, "alpha", None) is not None, "frosted_panel reports the wash it used (.alpha)")

# Restricted non-Claude run (2026-10-04), docs + printed output only:
# (1) the runbook said "claim waived_category: no-reader"; the agent kept answers/findings beside it and the gate only
#     said "answers is missing" — a half-made waiver now says which field it lacks and the whole shape
import blind_read as _br
_hf = _br.faults({"waived_category": "no-reader", "answers": "no reader here", "findings": "n/a"}, 3)
check(_hf and "waived" in _hf[0] and "no-reader" in _hf[0] and "answers" not in _hf[0].split("—")[0],
      "a half-made blind_read waiver names the missing `waived` field: {}".format(_hf[:1]))
# (2) the prose spells it "self-read"; the enum is "selfread" — the hyphenated word is the same mode
_dd = Path(tempfile.mkdtemp())
try:
    dk.declare_delivery(str(_dd), "self-read")
    check("selfread" in (_dd / ".deck-gates.json").read_text(encoding="utf-8"), "declare_delivery('self-read') records selfread")
except Exception as e:
    check(False, "declare_delivery('self-read') is accepted as selfread: {!r}".format(e))
# (3) lint_deck.py --help prints its usage and exits 0 (it was an "unrecognised option" error)
import subprocess as _sp
_r = _sp.run([sys.executable, str(ROOT / "scripts" / "lint_deck.py"), "--help"], capture_output=True, text=True)
check(_r.returncode == 0 and "--renders" in _r.stdout, "lint_deck.py --help: rc {} {}".format(_r.returncode, (_r.stdout + _r.stderr)[:160]))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_followup_minors] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
