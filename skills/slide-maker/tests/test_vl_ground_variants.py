#!/usr/bin/env python3
"""Visual-language ground variants: every language has its light ground and one contrast ground (inks pass 4.5:1, a different look by the register-pixels distance), use(ground='auto') avoids the look history (a printed board stays light), and the record, the direction preview and the gate name the variant."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)



import json, subprocess
import deckkit as dk, visual_languages as vl, register_surface as rs, check_register_pixels as crp, check_visual_language as cvl
def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
CONTRAST = {"editorial": "ink", "soft": "dusk", "collage": "slate", "storybook": "meadow"}
ph = str(ROOT / "assets" / "vl" / "photo" / "hall-repair.jpg")
wc = str(ROOT / "assets" / "vl" / "watercolour" / "rooftop-garden.jpg")
# every language has its light ground and ONE contrast variant; every text ink passes 4.5:1 on its ground and panel
for name, var in CONTRAST.items():
    check(set(vl.VARIANTS[name]) == {"light", var}, "{}: variants {}".format(name, sorted(vl.VARIANTS[name])))
    check(vl.VARIANTS[name]["light"]["palette"] == vl.LANGS[name]["palette"], "{}: light is the language's own palette".format(name))
    for key, V in vl.VARIANTS[name].items():
        P = V["palette"]
        for ink in [P["ink"], P["mute"]] + P["text_accents"]:
            for g in (P["ground"], P["panel"]):
                check(vl._contrast(ink, g) >= 4.5, "{} {}: {} on {} is {:.2f}:1".format(name, key, ink, g, vl._contrast(ink, g)))
        check(V.get("label") and V.get("label_zh"), "{} {}: labelled".format(name, key))
    d = crp._dist(rgb(vl.VARIANTS[name][var]["palette"]["ground"]), rgb(vl.LANGS[name]["palette"]["ground"]))
    check(d > 2 * crp.SAME_LOOK, "{}: the contrast ground is a different look (distance {:.0f})".format(name, d))
# use(ground=…) builds in the variant; a card and a ground follow it
for name, var in CONTRAST.items():
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use(name, prs, ground=var)
    check(k.ground == var and k.P == vl.VARIANTS[name][var]["palette"], "{}: the kit carries the variant".format(name))
    s = k.new_slide()
    body_, _h = rs.card(s, name, 1, 1, 4, 2, label=None)
    check(str(body_.fill.fore_color.rgb) == vl.VARIANTS[name][var]["palette"]["panel"], "{}: rs.card follows the variant panel".format(name))
    img = wc if name == "storybook" else ph
    for page, kw in (("cover", dict(kicker="A repair café", title="Bring it broken. Take it home working.", image=[ph, ph, ph] if name == "collage" else img)),
                     ("section", dict(number="02", kicker="How it works", title="We fix it with you")),
                     ("image_text", dict(kicker="Tools", title="Tools on every bench", body="Shared tools.", image=img)),
                     ("quote", dict(quote="The visitor holds the screwdriver; the volunteer only guides.", attribution="A volunteer", image=img)),
                     ("data", dict(number="1", label="evening a month", note="Short enough.")),
                     ("closing", dict(title="Bring one broken thing.", line="And bring a neighbour.", image=img))):
        getattr(k, page)(k.new_slide(), **kw)
    bad = [f for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL" or f[2] in ("HEADLINE_CROWDED", "SLIVER_GAP")]
    check(not bad, "{} {}: lint on the variant: {}".format(name, var, [(f[0], f[2]) for f in bad][:3]))
    if name == "collage":
        qs = prs.slides[4]
        fills = [str(sh.fill.fore_color.rgb) for sh in qs.shapes if sh.shape_type == 1 and sh.fill.type == 1]
        check("FFFFFF" in fills and vl.VARIANTS["collage"]["slate"]["palette"]["panel"] in fills,
              "collage slate: prints stay white, the note card takes the variant panel: {}".format(fills))
        hl = [(r_.font.color.rgb, r_._r.find(".//" + dk.qn("a:highlight"))) for sh in prs.slides[1].shapes                 # slide 0 is the rs.card page; the cover is next
              if getattr(sh, "has_text_frame", False) for p_ in sh.text_frame.paragraphs for r_ in p_.runs
              if r_._r.find(".//" + dk.qn("a:highlight")) is not None]
        for col, h in hl:
            hc = h.find(dk.qn("a:srgbClr")).get("val")
            check(vl._contrast(str(col), hc) >= 4.5, "collage slate: the marked kicker reads on its highlight ({} on {})".format(col, hc))
        check(hl, "collage slate: the kicker is still marked")
# looked at (variant samples, 2026-10-04): soft dusk set its light "1" on the pale sage disc (~2:1); storybook meadow
# left each watercolour's cream paper as a pale patch on the green paper
import io
from PIL import Image
for g in ("light", "dusk"):
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use("soft", prs, ground=g)
    s_ = k.new_slide()
    k.data(s_, number="1", label="evening a month")
    disc = [sh for sh in s_.shapes if sh.shape_type == 1 and "disc" in (sh.name or "") or
            (sh.shape_type == 1 and getattr(sh, "auto_shape_type", None) == 9)]
    num = [r_ for sh in s_.shapes if getattr(sh, "has_text_frame", False) for p_ in sh.text_frame.paragraphs
           for r_ in p_.runs if r_.text == "1"]
    check(disc and num, "soft {}: a disc and a number: {} {}".format(g, len(disc), len(num)))
    if disc and num:
        c = vl._contrast(str(num[0].font.color.rgb), str(disc[0].fill.fore_color.rgb))
        check(c >= 3.0, "soft {}: the number reads on its disc ({:.2f}:1)".format(g, c))
for g in ("light", "meadow"):
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use("storybook", prs, ground=g)
    s_ = k.new_slide()
    k.image_text(s_, kicker="Tools", title="You need very few tools", body="A trowel.", image=wc)
    pics = [sh for sh in s_.shapes if sh.shape_type == 13]
    im = Image.open(io.BytesIO(pics[0].image.blob)).convert("RGBA")
    px = [p_[:3] for p_ in im.getdata() if p_[3] > 230]
    px.sort(key=lambda c: sum(c))
    paper = px[int(len(px) * 0.9)]                     # the light end of the painting: its paper
    d = crp._dist(paper, rgb(vl.VARIANTS["storybook"][g]["palette"]["ground"]))
    check(d <= 45, "storybook {}: the watercolour's paper matches the slide's (distance {:.0f}, paper {})".format(g, d, paper))

# every language on BOTH grounds, every page: nothing the hand-off a11y gate holds a deck on. The collage
# note's washi tape (EDE3C8 on the white note, 1.28:1) was a NON-TEXT CONTRAST on every collage page since P2
# shipped — pure ornament, so it is declared decorative, as soft's blobs are.
import lint_deck as ld, contextlib, re as _re
_a11y_dir = Path(tempfile.mkdtemp())
for name, var in CONTRAST.items():
    for g in ("light", var):
        prs = dk.blank_deck(13.333, 7.5)
        k = vl.use(name, prs, ground=g)
        img = wc if name == "storybook" else ph
        k.cover(k.new_slide(), kicker="A repair café", title="Bring it broken", image=[ph, ph] if name == "collage" else img)
        k.section(k.new_slide(), number="02", kicker="How it works", title="We fix it with you")
        k.image_text(k.new_slide(), kicker="Tools", title="Tools on every bench", body="Shared tools.", image=img)
        k.quote(k.new_slide(), quote="The visitor holds the screwdriver.", attribution="A volunteer")
        k.data(k.new_slide(), number="1", label="evening a month", note="Short enough.")
        k.closing(k.new_slide(), title="Bring one broken thing.", line="And bring a neighbour.")
        p_ = _a11y_dir / "a11y-{}-{}.pptx".format(name, g)
        prs.save(str(p_))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ld.lint(str(p_), mode="presented", static_ok=True)
        held = [l_.strip()[:140] for l_ in buf.getvalue().splitlines()
                if any(_re.search(r"\]\s+" + _re.escape(c) + ":", l_) for c in ld.A11Y_BLOCKING)]
        check(not held, "{} {}: the hand-off a11y gate holds nothing: {}".format(name, g, held[:3]))

try:
    vl.use("editorial", dk.blank_deck(13.333, 7.5), ground="neon")
    fails.append("an unknown ground was accepted")
except ValueError as e:
    check("light" in str(e) and "ink" in str(e) and "auto" in str(e), "the refusal lists the grounds: {}".format(e))
# ground="auto": the look history decides; nothing to read means light; a printed board stays light
td = Path(tempfile.mkdtemp())
def taste(*rows):
    p = td / "taste-{}.md".format(len(list(td.iterdir())))
    p.write_text("## LOOK HISTORY\n| date | deck | look | canvas | motif |\n|---|---|---|---|---|\n" +
                 "".join("| 2026-10-0{} | d{} | x | #{} | - |\n".format(i + 1, i, c) for i, c in enumerate(rows)), encoding="utf-8")
    return str(p)
prs = dk.blank_deck(13.333, 7.5)
key, why = vl._auto_ground("editorial", prs, taste=taste("F5EFE1", "F2EEE5", "F4EFE6"))
check(key == "ink" and why, "after three cream decks auto picks the contrast ground: {} {}".format(key, why))
key, why = vl._auto_ground("editorial", prs, taste=taste("1B1A17", "202020", "F5EFE1"))
check(key == "light", "after dark decks auto keeps light: {} {}".format(key, why))
key, why = vl._auto_ground("editorial", prs, taste=str(td / "missing.md"))
check(key == "light", "no history: light ({})".format(why))
poster = dk.blank_deck(23.39, 33.11)                       # A1 portrait, a printed board
key, why = vl._auto_ground("editorial", poster, taste=taste("F5EFE1", "F2EEE5", "F4EFE6"))
check(key == "light" and "print" in why, "a printed board stays light: {} {}".format(key, why))
k = vl.use("soft", dk.blank_deck(13.333, 7.5), ground="auto")
check(k.ground in vl.VARIANTS["soft"], "use(ground='auto') resolves to a variant: {}".format(k.ground))
# auto resolves on the REAL canvas everywhere: use(), direction() and --gates agreed only on 16:9 — an A4 board built
# light was recorded (and previewed) on the contrast ground (final review 2026-10-04)
import os as _os, registry as _reg
_cream = taste("F5EFE1", "F2EEE5", "F4EFE6")
_orig_tf = _reg.taste_file
_reg.taste_file = lambda: Path(_cream)
try:
    check(vl.use("editorial", dk.blank_deck(8.27, 11.69), ground="auto").ground == "light", "use(): A4 stays light")
    check(vl.direction("editorial", ground="auto", W=8.27, H=11.69)["vl_ground"] == "light",
          "direction(ground='auto', W=, H=) resolves on the board's canvas: A4 stays light")
    check(vl.direction("editorial", ground="auto")["vl_ground"] == "ink", "direction(): 16:9 after cream decks -> ink")
finally:
    _reg.taste_file = _orig_tf
_home = Path(tempfile.mkdtemp())
(_home / ".slide-maker" / "slide-templates").mkdir(parents=True)
(_home / ".slide-maker" / "slide-templates" / "taste.md").write_text(Path(_cream).read_text(encoding="utf-8"), encoding="utf-8")
_env = dict(_os.environ, HOME=str(_home))
_a4 = Path(tempfile.mkdtemp()); dk.blank_deck(8.27, 11.69).save(str(_a4 / "board.pptx"))
r_ = subprocess.run([sys.executable, "scripts/visual_languages.py", "--gates", "editorial", "--ground", "auto", "--deck", str(_a4)],
                    cwd=str(ROOT), capture_output=True, text=True, env=_env)
check(r_.returncode == 0 and "design_plan.vl_ground light" in r_.stdout,
      "--gates --ground auto reads the deck's canvas: an A4 board records light: {}".format(r_.stdout[-300:] + r_.stderr[-200:]))
_wide = Path(tempfile.mkdtemp()); dk.blank_deck(13.333, 7.5).save(str(_wide / "deck.pptx"))
r_ = subprocess.run([sys.executable, "scripts/visual_languages.py", "--gates", "editorial", "--ground", "auto", "--deck", str(_wide)],
                    cwd=str(ROOT), capture_output=True, text=True, env=_env)
check(r_.returncode == 0 and "design_plan.vl_ground ink" in r_.stdout, "...and a 16:9 deck after cream decks records ink: {}".format(r_.stdout[-200:]))
r_ = subprocess.run([sys.executable, "scripts/visual_languages.py", "--gates", "editorial", "--ground", "auto", "--deck", str(Path(tempfile.mkdtemp()))],
                    cwd=str(ROOT), capture_output=True, text=True, env=_env)
check(r_.returncode == 2 and "printed" in r_.stderr, "--ground auto with no built deck refuses (it cannot know the canvas) and "
      "points to the ground use() printed: {}".format(r_.stderr[-300:]))
# use()'s hint is a runnable command: the script's path and --deck, not a bare flag
import io as _io2, contextlib as _cl2
_buf = _io2.StringIO()
_reg.taste_file = lambda: Path(_cream)
try:
    with _cl2.redirect_stdout(_buf):
        vl.use("editorial", dk.blank_deck(13.333, 7.5), ground="auto")
finally:
    _reg.taste_file = _orig_tf
check("visual_languages.py --gates editorial --ground ink --deck" in _buf.getvalue() and "python3 " in _buf.getvalue(),
      "use(ground='auto') prints the record command with the script path and --deck: {}".format(_buf.getvalue()))
# --gates prints commands that RUN AS PRINTED from wherever the agent is (a docs-only agent ran them from its own deck
# folder and had to path-prefix every one: they said `python3 scripts/deck_gates.py`, 2026-10-04)
_elsewhere = Path(tempfile.mkdtemp())
_deckdir = Path(tempfile.mkdtemp()) / "my deck 菜园"
_deckdir.mkdir()
r_ = subprocess.run([sys.executable, str(ROOT / "scripts" / "visual_languages.py"), "--gates", "collage", "--ground", "slate",
                     "--deck", str(_deckdir), "--for", "a repair café"], cwd=str(_elsewhere), capture_output=True, text=True)
_cmds = [l_ for l_ in r_.stdout.splitlines() if l_.startswith("python3 ")]
check(r_.returncode == 0 and len(_cmds) >= 6, "--gates printed its commands: {}".format(r_.stdout[-300:] + r_.stderr[-200:]))
for _c in _cmds:
    _rr = subprocess.run(_c, shell=True, cwd=str(_elsewhere), capture_output=True, text=True)
    check(_rr.returncode == 0, "printed command runs as printed from another folder: {} -> {}".format(_c[:90], (_rr.stdout + _rr.stderr)[-200:]))
import json as _js
_rec = _js.loads((_deckdir / ".deck-gates.json").read_text(encoding="utf-8")) if (_deckdir / ".deck-gates.json").exists() else {}
check((_rec.get("design_plan") or {}).get("vl_ground") == "slate", "...and the record holds vl_ground slate: {}".format(_rec.get("design_plan")))
# the direction preview and the record name the variant
d_ = vl.direction("editorial", ground="ink")
check(d_["bg"].lstrip("#").upper() == vl.VARIANTS["editorial"]["ink"]["palette"]["ground"] and d_["sample"] != vl.direction("editorial", ground="light")["sample"],
      "direction(ground='ink') shows the ink sample and ground")
r_ = subprocess.run([sys.executable, "scripts/visual_languages.py", "--gates", "collage", "--ground", "slate", "--deck", str(td)],
                    cwd=str(ROOT), capture_output=True, text=True)
check(r_.returncode == 0 and "design_plan.vl_ground slate" in r_.stdout and vl.VARIANTS["collage"]["slate"]["palette"]["ground"] in r_.stdout.upper(),
      "--gates --ground prints the variant's record and palette: {}".format(r_.stdout[-300:] + r_.stderr[-200:]))
f, _ = cvl.check(str(ROOT / "assets" / "vl" / "samples" / "editorial.jpg"), {"name": "editorial", "fonts": "both", "ground": "neon"})
check(any(c == "UNKNOWN GROUND VARIANT" for _s, c, _w in f), "an unknown recorded ground blocks: {}".format(f))
check(cvl.recorded_language({"design_plan": {"visual_language": "soft", "vl_ground": "dusk"}}).get("ground") == "dusk", "the record carries the ground")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_vl_ground_variants] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
