#!/usr/bin/env python3
"""image_series: an ART-DIRECTED image series for an image-led deck (imagery: series).

The 33 image-led decks studied (skillry.dev, 2026-10-03) carry a series-consistent image on nearly every
page; this skill could only give a few slides a plate, each prompted alone. The plan is the contract:
every slot says what its image MEANS on its slide, real subjects stay real photos, and people follow the
user's rule — generic people yes, a fictional persona only with a visible label, real people never
generated.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import image_series as ims  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


GOOD = {
    "art_direction": "warm editorial craft photography, soft window daylight, shallow depth of field",
    "palette": ["F2E8D8", "D9A13B", "C2462E", "1A1A1A"],
    "render": "photo",
    "slots": [
        {"id": "hero", "slide": 1, "frame": {"shape": "arch", "w": 4.2, "h": 5.6},
         "subject": "a potter's hands shaping wet clay on a turning wheel", "kind": "generic-person",
         "cutout": False, "calm_zone": "none", "focus": [0.5, 0.3], "alt": "a potter's hands shaping clay",
         "meaning": "making by hand is the deck's argument; the hands carry it before any word does",
         "referent": "generic-concrete"},
        {"id": "kettle", "slide": 3, "frame": {"shape": "rect", "w": 3.0, "h": 3.0},
         "subject": "a hand-thrown stoneware kettle with an ash glaze, three-quarter view", "kind": "object",
         "cutout": True, "alt": "a stoneware kettle",
         "meaning": "the finished object, cut out so the page can set it on its own colour field",
         "referent": "generic-concrete"},
    ],
}
check(ims.check(GOOD) == [], "a valid plan has problems: {}".format(ims.check(GOOD)))
check(ims.key_id(GOOD) == "hero", "the key defaults to the first slot")


def bad(mutate, word):
    p = copy.deepcopy(GOOD)
    mutate(p)
    probs = ims.check(p)
    check(any(word in x for x in probs), "expected a problem mentioning {!r}, got {}".format(word, probs))


bad(lambda p: p["slots"][0].update(meaning="nice"), "meaning")
bad(lambda p: p["slots"][0].update(referent="real-specific"), "real")
bad(lambda p: p["slots"][0].update(kind="team-member"), "not generatable")
bad(lambda p: p["slots"][0].update(kind="persona"), "persona_label")
bad(lambda p: p["slots"][0].update(kind="rocket"), "kind")
bad(lambda p: p["slots"][0]["frame"].update(shape="star"), "shape")
bad(lambda p: p["slots"][0]["frame"].update(w=0), "frame")
bad(lambda p: p["slots"][1].update(id="hero"), "duplicate")
bad(lambda p: p["slots"][1].update(id="Kettle 2"), "id")
bad(lambda p: p.update(palette=["F2E8D8", "yellow"]), "palette")
bad(lambda p: p.update(art_direction="nice"), "art_direction")
bad(lambda p: p.update(render="3d"), "render")
bad(lambda p: p["slots"][0].update(referent="stylized"), "stylized")      # stylized needs render illustration
bad(lambda p: p["slots"][0].update(alt=""), "alt")
bad(lambda p: p["slots"][0].update(focus=[1.4, 0.2]), "focus")
# the key colour must not eat the palette: a green palette keyed on green is refused
bad(lambda p: p.update(palette=["F4F1E6", "00A651", "1B5E20"], chroma="00B140"), "chroma")
g = copy.deepcopy(GOOD)
g.update(palette=["F4F1E6", "00A651", "1B5E20"], chroma="FF00FF")
check(ims.check(g) == [], "a green palette on a magenta key is valid: {}".format(ims.check(g)))
# a subject that NAMES people cannot hide under a non-person kind: measured 2026-10-03, a "scene" slot
# for "volunteers' hands repairing a lamp" came back as four people — and the people gate only reads
# person kinds, so a name + role beside that picture would have passed. English and Chinese.
for subj in ("volunteers' hands repairing a broken table lamp on a workbench",
             "two neighbours leaning over a disassembled toaster in a hall",
             "一位老人在社区菜园里给番茄浇水的场景"):
    bad(lambda p, subj=subj: p["slots"][0].update(subject=subj, kind="scene"), "generic-person")
# ...and OBJECTS named after people stay objects (final review, 2026-10-03): the suggested fix (kind
# generic-person) would add "People: ordinary people…" to a knife still-life's prompt
for subj in ("a chef's knife on a walnut cutting board", "baby carrots in a ceramic bowl",
             "a vintage coffee maker on a counter", "a potter's wheel in an empty studio",
             "a man-made lake at dawn", "a granite rock face at dusk", "an old clock face with brass hands",
             "kid gloves on a wooden table", "手工人偶摆在木桌上", "用户界面草图贴在白板上"):
    ok_ = copy.deepcopy(GOOD); ok_["slots"][0].update(subject=subj, kind="object")
    check(ims.check(ok_) == [], "{!r} is an object but was refused: {}".format(subj, ims.check(ok_)))
# ...while a person's own hands or face still make it a person slot
for subj in ("a potter's hands shaping wet clay on a turning wheel", "a farmer's weathered face in morning light"):
    bad(lambda p, subj=subj: p["slots"][0].update(subject=subj, kind="scene"), "generic-person")
# ...while subjects that name no one stay valid ("hand-thrown" is a making word, not a person)
for subj in ("a hand-thrown stoneware kettle with an ash glaze on linen",
             "a long workbench with a soldering iron and spools of thread",
             "雨后的城市屋顶菜园，番茄架和水壶"):
    ok_ = copy.deepcopy(GOOD); ok_["slots"][0].update(subject=subj, kind="scene")
    check(ims.check(ok_) == [], "{!r} names no one but was refused: {}".format(subj, ims.check(ok_)))
# the KEY sets the series' look, so it must be a graded picture, not a cut-out object
bad(lambda p: p.update(key="kettle"), "key")
ck = copy.deepcopy(GOOD); ck["slots"] = [ck["slots"][1], ck["slots"][0]]       # a cut-out FIRST, no key
check(any("key" in x for x in ims.check(ck)), "a cut-out first slot cannot be the default key: {}".format(ims.check(ck)))
# a subject must name a THING: the prompt boilerplate alone ("presentation deck", "same hand", "crop")
# used to clear the generator's topicality gate, so "an abstract soft gradient backdrop" sailed through
for subj in ("an abstract soft gradient backdrop", "抽象柔和的渐变背景"):
    bad(lambda p, subj=subj: p["slots"][1].update(subject=subj), "subject")
# a cut-out whose subject IS the key's colour is refused before any money is spent
bad(lambda p: p["slots"][1].update(subject="a bright green seedling with fresh leaves in a clay pot"), "FF00FF")
bad(lambda p: p["slots"][1].update(subject="一株绿色的薄荷幼苗种在陶盆里"), "FF00FF")
mg = copy.deepcopy(GOOD); mg["chroma"] = "FF00FF"; mg["slots"][1]["subject"] = "a pink orchid in a glass vase"
check(any("00B140" in x for x in ims.check(mg)), "a pink subject on the magenta key must be refused: {}".format(ims.check(mg)))
# a malformed plan is REFUSED with a message, never a traceback (a crash inside the gates read as
# NOT CHECKED — a soft pass for an image-led deck); a boolean is not a slide number
for mutate in (lambda p: p["slots"][0].update(frame="arch"), lambda p: p["slots"][0].update(id=["x"]),
               lambda p: p.update(key=["hero"]), lambda p: p["slots"][0].update(slide=True),
               lambda p: p["slots"][0].update(focus="centre"), lambda p: p.update(slots={"hero": {}})):
    mp = copy.deepcopy(GOOD)
    mutate(mp)
    try:
        probs = ims.check(mp)
        check(probs, "a malformed plan must have problems: {}".format(mp))
    except Exception as e:
        fails.append("check() crashed on a malformed plan: {}: {}".format(type(e).__name__, e))
# the subject check is language-fair beyond English and Chinese: Korean, Arabic, Russian, kana-only
# Japanese subjects were refused as "names no thing" (generality probe, 2026-10-03) — every script counts
for subj in ("나무 테이블 위에 놓인 찻주전자와 찻잔", "إبريق شاي خزفي مصنوع يدويا على طاولة خشبية",
             "глиняный чайник ручной работы на деревянном столе", "きのテーブルのうえにおかれたきゅうすとゆのみ",
             "木のテーブルの上に置かれた急須と湯呑み"):
    lp = copy.deepcopy(GOOD); lp["slots"][0].update(subject=subj, kind="scene")
    check(ims.check(lp) == [], "{!r} names things but was refused: {}".format(subj, ims.check(lp)))
# a persona WITH its label is valid
pp = copy.deepcopy(GOOD)
pp["slots"][0].update(kind="persona", persona_label="虚构人物 · illustrative persona")
check(ims.check(pp) == [], "a labelled persona is valid: {}".format(ims.check(pp)))
# Review Focus 1: CJK subject / meaning / alt clear the language-fair floors
cj = copy.deepcopy(GOOD)
cj["slots"][0].update(subject="陶艺师的手在转盘上塑形湿泥", alt="陶艺师的手",
                      meaning="手作是整份演示的论点，这双手先于文字把它说出来")
check(ims.check(cj) == [], "a CJK slot is valid: {}".format(ims.check(cj)))
# load(): bad JSON names the file
with tempfile.TemporaryDirectory() as td:
    bp = Path(td) / "series.json"
    bp.write_text("{not json", encoding="utf-8")
    try:
        ims.load(bp)
        fails.append("load() accepted invalid JSON")
    except ValueError as e:
        check("series.json" in str(e), "load()'s refusal should name the file: {}".format(e))
try:
    ims.slot(GOOD, "nope")
    fails.append("slot() accepted an unknown id")
except KeyError as e:
    check("hero" in str(e), "slot()'s refusal should list the known ids: {}".format(e))

# ── prompts ──────────────────────────────────────────────────────────────────────────────────
import generate_images_codex as gic  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    items = ims.prompts(GOOD, td)
    man = json.loads((Path(td) / "image_prompt_manifest.json").read_text(encoding="utf-8"))
    check(man == items and len(items) == 2, "the manifest must hold one item per slot")
    h = items[0]
    check(h["id"] == "hero" and h["filename"] == "slide-01-hero.png" and h["slide"] == 1, "item shape: {}".format(h))
    check(all(it.get("orientation") == "auto" for it in items),
          "series items carry orientation 'auto' — the aspect is already in each prompt")
    check(items[0].get("aspect") == round(4.2 / 5.6, 3) and items[1].get("aspect") == 1.0,
          "series items carry their slot's aspect (the metered path picks its size from it): {}".format(
              [it.get("aspect") for it in items]))
    p0, p1 = items[0]["prompt"], items[1]["prompt"]
    check(GOOD["art_direction"] in p0 and GOOD["art_direction"] in p1, "every prompt carries the art direction")
    check("#D9A13B" in p0, "every prompt carries the palette")
    check("photograph" in p0.lower(), "the RENDER clause is INSIDE the prompt (photo)")
    check("no text" in p0.lower(), "every prompt forbids text")
    check("#00B140" in p1 and "#00B140" not in p0, "only the cut-out slot asks for the chroma background")
    check(gic.check_prompt_topicality(items) == [], "the prompts must pass the generator's topicality check")
# illustration render goes in verbatim too
il = copy.deepcopy(GOOD)
il["render"] = "illustration"
check("not a photograph" in ims.build_prompt(il, il["slots"][0]).lower(), "illustration render clause")
# Review Focus 1: a CJK subject still passes the generator's topicality check
with tempfile.TemporaryDirectory() as td:
    its = ims.prompts(cj, td)
    probs = gic.check_prompt_topicality(its)
    check(not probs, "a CJK-subject prompt fails the generator's topicality check: {}".format(probs))
# Review Focus 2: extreme frames state their aspect
tall = copy.deepcopy(GOOD)
tall["slots"][0]["frame"] = {"shape": "arch", "w": 1.6, "h": 6.4}
check("tall" in ims.build_prompt(tall, tall["slots"][0]).lower(), "a 1:4 frame must ask for a tall composition")
wide = copy.deepcopy(GOOD)
wide["slots"][0]["frame"] = {"shape": "rect", "w": 8.0, "h": 2.0}
check("wide" in ims.build_prompt(wide, wide["slots"][0]).lower(), "a 4:1 frame must ask for a wide composition")
el = copy.deepcopy(GOOD); el["slots"][0]["frame"] = {"shape": "ellipse", "w": 3, "h": 3}
check(" a ellipse" not in ims.build_prompt(el, el["slots"][0]), "article before a vowel-initial shape")
check("湿泥。" in ims.build_prompt(cj, cj["slots"][0]), "a CJK subject ends with a CJK full stop, not '.'")
# the CLI refuses an invalid plan with exit 1 and lists the problems
with tempfile.TemporaryDirectory() as td:
    bp = Path(td) / "series.json"
    badp = copy.deepcopy(GOOD); badp["slots"][0]["meaning"] = "x"
    bp.write_text(json.dumps(badp), encoding="utf-8")
    check(ims.main(["check", str(bp)]) == 1, "check CLI must exit 1 on an invalid plan")
    check(ims.main(["prompts", str(bp), td]) == 1, "prompts CLI must refuse an invalid plan")
    # the NEXT line printed by `check` must run as printed — no <placeholder>
    gp = Path(td) / "ok.json"
    gp.write_text(json.dumps(GOOD), encoding="utf-8")
    import contextlib, io  # noqa: E401,E402
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ims.main(["check", str(gp)])
    nxt = [l for l in buf.getvalue().splitlines() if l.startswith("NEXT")]
    check(nxt and "<" not in nxt[0] and str(Path(td) / "assets" / "generated") in nxt[0],
          "check's NEXT line must be runnable as printed: {}".format(nxt))

# ── QC: consistency with the key image ───────────────────────────────────────────────────────
from PIL import Image  # noqa: E402

def warm(path, shift=0, size=(400, 300)):
    im = Image.new("RGB", size)
    im.putdata([(200 + (x * 30) // size[0], 150 + shift + (y * 20) // size[1], 90 + shift)
                for y in range(size[1]) for x in range(size[0])])
    im.save(path)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    plan = copy.deepcopy(GOOD)
    plan["slots"].append({"id": "odd", "slide": 4, "frame": {"shape": "rect", "w": 3, "h": 2},
                          "subject": "a stoneware cup on a linen cloth in daylight", "kind": "object",
                          "cutout": False, "alt": "a cup", "referent": "generic-concrete",
                          "meaning": "the everyday object the craft ends in; the cup closes the story"})
    warm(td / "slide-01-hero.png", size=(300, 400))                       # the key (arch frame 4.2x5.6)
    warm(td / "slide-03-kettle.png", shift=8, size=(300, 300))
    Image.new("RGB", (300, 200)).save(td / "slide-04-odd.png")
    odd = Image.open(td / "slide-04-odd.png")
    odd.putdata([(20, 60 + (x % 50), 200) for y in range(200) for x in range(300)])       # cold blue: off-series
    odd.save(td / "slide-04-odd.png")
    # the kettle slot is a cut-out: it needs its keyed file
    rep = ims.qc(plan, td)
    flags = {s["id"]: s["flags"] for s in rep["slots"]}
    check(any("OFF-SERIES" in f for f in flags["odd"]), "a cold-blue image in a warm series must be OFF-SERIES: {}".format(flags))
    check(not any("OFF-SERIES" in f for f in flags["kettle"]), "a near-key image must not be OFF-SERIES: {}".format(flags))
    check(any("CUTOUT" in f for f in flags["kettle"]), "a cut-out slot without its .cut.png must say so")
    check((td / "series-qc.json").exists(), "qc writes series-qc.json")
    check(rep["key"] == "hero" and "hero" not in rep["outliers"], "the key is the reference, never an outlier")
    # a CUT-OUT slot is generated on the key colour: its subject matches the series, its background
    # never will — the comparison must read the SUBJECT, or every cut-out is "off-series"
    kim = Image.new("RGB", (300, 300), (0, 177, 64))
    from PIL import ImageDraw  # noqa: E402
    sub = Image.open(td / "slide-01-hero.png").resize((180, 180))
    kim.paste(sub, (60, 60))
    kim.save(td / "slide-03-kettle.png")
    repc = ims.qc(plan, td)
    fk = {s["id"]: s["flags"] for s in repc["slots"]}["kettle"]
    check(not any("OFF-SERIES" in f for f in fk), "a warm subject on the green key is in-series: {}".format(fk))
    check(not any(f.startswith("LETTERBOX") for f in fk), "the flat key colour is not a letterbox: {}".format(fk))
    # ...and a cut-out is an isolated OBJECT: its colour is the object's, not the series' grade, so it is
    # not colour-compared at all. Measured 2026-10-03 on a real series: a cream kettle cut-out read 30.3
    # from a warm hall scene and was flagged OFF-SERIES while plainly belonging to the series.
    kim2 = Image.new("RGB", (300, 300), (0, 177, 64))
    ImageDraw.Draw(kim2).ellipse((70, 60, 230, 250), fill=(238, 228, 200))
    kim2.save(td / "slide-03-kettle.png")
    rk = {s["id"]: s for s in ims.qc(plan, td)["slots"]}["kettle"]
    check(not any("OFF-SERIES" in f for f in rk["flags"]) and rk.get("delta_e") is None,
          "a cut-out is not colour-compared: {}".format(rk))
    kim.save(td / "slide-03-kettle.png")
    # ...and when the KEY image itself is a cut-out, the others are compared with its subject
    pk = copy.deepcopy(plan); pk["key"] = "kettle"
    fh = {s["id"]: s["flags"] for s in ims.qc(pk, td)["slots"]}["hero"]
    check(not any("OFF-SERIES" in f for f in fh), "a cut-out key must be compared on its subject: {}".format(fh))
    # `cutout` cuts every cut-out slot with the PLAN's key — and refuses one generated on the wrong ground
    cut_plan = td / "plan.json"
    cut_plan.write_text(json.dumps(plan), encoding="utf-8")
    import contextlib, io  # noqa: E401,E402
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ims.main(["cutout", str(cut_plan), "--dir", str(td)])
    check(rc == 0 and (td / "slide-03-kettle.cut.png").exists(), "cutout must key the kettle slot: rc={} {}".format(rc, buf.getvalue()))
    rq = {s["id"]: s for s in ims.qc(plan, td)["slots"]}["kettle"]
    check(not any(f.startswith("CUTOUT") for f in rq["flags"]), "after `cutout` the CUTOUT flag clears: {}".format(rq["flags"]))
    (td / "slide-03-kettle.cut.png").unlink()
    Image.new("RGB", (300, 300), (252, 243, 224)).save(td / "slide-03-kettle.png")
    ImageDraw.Draw(Image.open(td / "slide-03-kettle.png")).ellipse((60, 60, 240, 240))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ims.main(["cutout", str(cut_plan), "--dir", str(td)])
    check(rc == 1 and "kettle" in buf.getvalue() and not (td / "slide-03-kettle.cut.png").exists(),
          "a cut-out on the wrong ground must be refused, naming the slot: rc={} {}".format(rc, buf.getvalue()[-200:]))
    kim.save(td / "slide-03-kettle.png")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ims.main(["qc", str(cut_plan), "--dir", str(td)])
    cl = [l for l in buf.getvalue().splitlines() if "CUTOUT" in l]
    check(cl and "<" not in cl[0] and str(cut_plan) in cl[0], "the CUTOUT line must run as printed: {}".format(cl))
    # paper margins are the MEDIUM of an illustration series, not a padded export: no LETTERBOX there
    lb = Image.new("RGB", (400, 300), (250, 244, 228))
    lb.paste(Image.open(td / "slide-01-hero.png").resize((400, 200)), (0, 50))
    lb.save(td / "slide-04-odd.png")
    il_plan = copy.deepcopy(plan); il_plan["render"] = "illustration"
    fo = {s["id"]: s["flags"] for s in ims.qc(il_plan, td)["slots"]}["odd"]
    check(not any(f.startswith("LETTERBOX") for f in fo), "an illustration's paper margin is not a letterbox: {}".format(fo))
    # Review Focus 2: an image far from its frame's aspect is flagged
    warm(td / "slide-01-hero.png", size=(800, 200))                       # 4:1 for a 3:4 arch frame
    rep2 = ims.qc(plan, td)
    check(any("ASPECT" in f for f in {s["id"]: s["flags"] for s in rep2["slots"]}["hero"]), "aspect mismatch flagged")
    # missing file
    (td / "slide-04-odd.png").unlink()
    rep3 = ims.qc(plan, td)
    check(any("MISSING" in f for f in {s["id"]: s["flags"] for s in rep3["slots"]}["odd"]), "missing file flagged")

# ── placement ────────────────────────────────────────────────────────────────────────────────
import deckkit as dk  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    warm(td / "slide-01-hero.png", size=(300, 400))
    kett = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    from PIL import ImageDraw  # noqa: E402
    ImageDraw.Draw(kett).ellipse((40, 40, 260, 260), fill=(150, 92, 60, 255))
    warm(td / "slide-03-kettle.png", size=(300, 300))       # generated first, then cut out — the real order
    kett.save(td / "slide-03-kettle.cut.png")
    import os as _os  # noqa: E402
    _t = (td / "slide-03-kettle.png").stat().st_mtime
    _os.utime(td / "slide-03-kettle.cut.png", (_t + 5, _t + 5))
    prs = dk.blank_deck(13.333, 7.5)
    s1 = dk.add_slide(prs)
    pic = ims.slot_picture(s1, GOOD, "hero", 0.6, 0.8, 4.2, 5.6, image_dir=td)
    check(dk.generated_slot(pic) == "hero", "slot_picture must tag the picture with its slot")
    check("round2SameRect" in pic._element.xml, "the hero's arch frame must be applied")
    check(pic._element.find(".//" + dk.qn("p:cNvPr")).get("descr") == GOOD["slots"][0]["alt"], "alt from the plan")
    s3 = dk.add_slide(prs)
    cp = ims.slot_picture(s3, GOOD, "kettle", 6.0, 1.0, 3.0, 3.0, image_dir=td)
    check(dk.generated_slot(cp) == "kettle" and cp.image.content_type == "image/png", "cut-out slot places the keyed PNG")
    # a die-cut sticker is a slot_picture option, so the documented route never needs dk.picture
    sp_ = ims.slot_picture(s3, GOOD, "kettle", 9.4, 1.0, 3.0, 3.0, image_dir=td, sticker=True)
    check(dk.generated_slot(sp_) == "kettle" and (td / "slide-03-kettle.cut.sticker.png").exists(),
          "sticker=True must place the die-cut sticker of the cut-out, tagged")
    # a slot regenerated AFTER its cut-out (--overwrite --only kettle) must not place the old cut-out
    _os.utime(td / "slide-03-kettle.png", (_t + 60, _t + 60))
    try:
        ims.slot_picture(s3, GOOD, "kettle", 6.0, 1.0, 3.0, 3.0, image_dir=td)
        fails.append("slot_picture placed a cut-out older than its regenerated image")
    except ValueError as e:
        check("cutout" in str(e), "the refusal should print the cutout command: {}".format(e))
    stale = {r["id"]: r["flags"] for r in ims.qc(GOOD, td)["slots"]}["kettle"]
    check(any(f.startswith("CUTOUT") and "older" in f for f in stale), "qc must flag a stale cut-out: {}".format(stale))
    try:
        ims.slot_picture(s3, GOOD, "hero", 1, 1, 1, 1, image_dir=td / "nowhere")
        fails.append("slot_picture accepted a missing image")
    except FileNotFoundError as e:
        check("--only hero" in str(e), "the refusal should print the command that makes it: {}".format(e))

# ── the docs name every value the code accepts (a restricted-agent run, 2026-10-03, had to guess the
# kind list from one example sentence, read chroma as "a colour like this", and found how to get `plan`
# and import the helpers only from source-adjacent output) ──────────────────────────────────────────
_doc = (ROOT / "references" / "image-generation.md").read_text(encoding="utf-8")
_sec = _doc[_doc.index("## Image-led decks"):]
_sec = _sec[:_sec.index("\n## ", 5)]
for _vals, _what in ((ims.KINDS, "kind"), (ims.NOT_GENERATABLE, "refused kind"), (ims.REFERENTS, "referent"),
                     (ims.RENDERS, "render"), (ims.CHROMAS, "chroma"), (ims.FRAME_SHAPES, "frame shape")):
    _miss = [v for v in _vals if "`{}`".format(v) not in _sec]
    check(not _miss, "image-generation.md's series section does not name {} value(s) {}".format(_what, _miss))
for _needle in ("image_series.load(", "sys.path.insert", "calm_zone", "[fx, fy]", "only these two",
                "deck_gates.py set", "English and Chinese credit lines"):
    check(_needle in _sec, "image-generation.md's series section never says {!r}".format(_needle))

# ...and the generator's gate reads the SUBJECT of a series item, not its boilerplate
gen_plan = copy.deepcopy(GOOD)
gen_plan["slots"][1]["subject"] = "an abstract soft gradient backdrop"     # bypassing check()
with tempfile.TemporaryDirectory() as td:
    its = ims.prompts(gen_plan, td)
    thin = gic.check_prompt_topicality(its)
    check(any(t[0] == 1 for t in thin), "a generic series subject must fail the generator's gate: {}".format(thin))
    check(not any(t[0] == 0 for t in thin), "a real subject must pass it: {}".format(thin))
    its = ims.prompts(cj, td)
    check(gic.check_prompt_topicality(its) == [], "a Chinese subject must pass on its own words: {}".format(
        gic.check_prompt_topicality(its)))

# a black-and-white series: hue is noise when there is almost no saturation (final review: a hair of warm
# tint against a hair of cool tint read hue distance 1.00 -> a false OFF-SERIES, and "regenerate" costs)
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    bw = copy.deepcopy(GOOD)
    bw["slots"][1]["cutout"] = False
    def grey(path, tint, size=(300, 300)):
        im = Image.new("RGB", size)
        im.putdata([tuple(max(0, min(255, (x * 200) // size[0] + 30 + t)) for t in tint)
                    for y in range(size[1]) for x in range(size[0])])
        im.save(path)
    grey(td / "slide-01-hero.png", (3, 0, -3), size=(300, 400))
    grey(td / "slide-03-kettle.png", (-3, 0, 3))
    fb = {r["id"]: r["flags"] for r in ims.qc(bw, td)["slots"]}["kettle"]
    check(not any("OFF-SERIES" in f for f in fb), "a near-grey pair must not be off-series on hue noise: {}".format(fb))
    # ...but a saturated picture in a grey series is still off-series
    Image.new("RGB", (300, 300), (230, 40, 160)).save(td / "slide-03-kettle.png")
    fb = {r["id"]: r["flags"] for r in ims.qc(bw, td)["slots"]}["kettle"]
    check(any("OFF-SERIES" in f for f in fb), "a magenta image in a grey series must be off-series: {}".format(fb))

# every printed command runs AS PRINTED, even when the deck folder has a space or CJK in its name
# (generality probe, 2026-10-03: "My Deck 菜园" split into three arguments)
import shlex  # noqa: E402
import contextlib as _cl, io as _io  # noqa: E401,E402


def _runnable(line, must_exist=()):
    cmd = line[line.index("python3"):]
    toks = shlex.split(cmd)
    # a path token is whole when it, its parent or its grandparent exists (an output folder the step creates)
    return all(Path(t).exists() or Path(t).parent.exists() or Path(t).parent.parent.exists()
               for t in toks if "/" in t and not t.startswith("scripts/")) \
        and all(str(m) in toks for m in must_exist)


with tempfile.TemporaryDirectory() as td:
    deck = Path(td) / "My Deck 菜园"
    deck.mkdir()
    sp = deck / "series.json"
    sp.write_text(json.dumps(GOOD), encoding="utf-8")
    gen = deck / "assets" / "generated"
    for argv, want in ((["check", str(sp)], [sp]), (["prompts", str(sp), str(gen)], [gen / "image_prompt_manifest.json"])):
        buf = _io.StringIO()
        with _cl.redirect_stdout(buf):
            ims.main(argv)
        nxt = [l for l in buf.getvalue().splitlines() if l.startswith("NEXT")]
        check(nxt and _runnable(nxt[0], want), "{} NEXT must run as printed: {}".format(argv[0], nxt))
    warm(gen / "slide-03-kettle.png", size=(300, 300))
    buf = _io.StringIO()
    with _cl.redirect_stdout(buf):
        ims.main(["qc", str(sp), "--dir", str(gen)])
    cl = [l for l in buf.getvalue().splitlines() if "CUTOUT" in l]
    check(cl and _runnable(cl[0], [sp, gen]), "the CUTOUT command must run as printed: {}".format(cl))

# ASPECT asks only for what a generator CAN make (between 2:3 and 16:9), symmetrically: a 1:4 arch got
# "regenerate at the frame's aspect" forever, and a 1:1 frame with a 3:2 image was flagged while a 3:2
# frame with a 1:1 image was not (generality probe / final review, 2026-10-03)
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    ap = copy.deepcopy(GOOD)
    ap["slots"] = [dict(ap["slots"][0], cutout=False)]
    def aspect_flags(frame, size):
        ap["slots"][0]["frame"] = frame
        warm(td / "slide-01-hero.png", size=size)
        return [f for f in {r["id"]: r["flags"] for r in ims.qc(ap, td)["slots"]}["hero"] if f.startswith("ASPECT")]
    check(not aspect_flags({"shape": "arch", "w": 1, "h": 4}, (300, 450)), "a 1:4 frame given the tallest image a generator makes must pass")
    check(aspect_flags({"shape": "arch", "w": 1, "h": 4}, (450, 300)), "a 1:4 frame given a LANDSCAPE image must be flagged")
    check(bool(aspect_flags({"shape": "rect", "w": 1, "h": 1}, (450, 300))) == bool(aspect_flags({"shape": "rect", "w": 3, "h": 2}, (300, 300))),
          "the aspect check must be symmetric (1:1 frame/3:2 image vs 3:2 frame/1:1 image)")

# a flagged slot gets a RUNNABLE fix, and an acknowledgement with a reason survives the next qc run
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    qp = copy.deepcopy(GOOD)
    qp["slots"] = [dict(qp["slots"][0]), dict(qp["slots"][0], id="odd", slide=2, frame={"shape": "rect", "w": 3, "h": 2})]
    pf = td / "series.json"
    pf.write_text(json.dumps(qp), encoding="utf-8")
    ims.prompts(qp, td, plan_path=pf)
    tex = Image.new("RGB", (300, 400))                     # a textured warm key: a smooth gradient is a FLAT PLATE
    tex.putdata([(120 + (x * 7 + y * 13) % 120, 80 + (x * 3 + y) % 100, 40 + (y * 5) % 70)
                 for y in range(400) for x in range(300)])
    tex.save(td / "slide-01-hero.png")
    cold = Image.new("RGB", (300, 200))
    cold.putdata([(20, 60 + (x % 50), 200) for y in range(200) for x in range(300)])
    cold.save(td / "slide-02-odd.png")
    buf = _io.StringIO()
    with _cl.redirect_stdout(buf):
        rc = ims.main(["qc", str(pf), "--dir", str(td)])
    fixes = [l for l in buf.getvalue().splitlines() if "--overwrite --only odd" in l]
    check(rc == 1 and fixes and "--style-ref" in fixes[0] and _runnable(fixes[0], [td / "image_prompt_manifest.json"]),
          "a flagged slot must get a runnable regenerate command: {}".format(buf.getvalue()[-400:]))
    check("acknowledged" in buf.getvalue(), "qc must say how to keep a flagged slot on purpose")
    rep_ = json.loads((td / "series-qc.json").read_text(encoding="utf-8"))
    rep_["acknowledged"] = {"odd": "kept: the cold night scene is the deck's deliberate turn"}
    (td / "series-qc.json").write_text(json.dumps(rep_), encoding="utf-8")
    with _cl.redirect_stdout(_io.StringIO()):
        rc2 = ims.main(["qc", str(pf), "--dir", str(td)])
    rep2 = json.loads((td / "series-qc.json").read_text(encoding="utf-8"))
    check(rc2 == 0 and rep2.get("acknowledged", {}).get("odd"),
          "an acknowledged slot passes and the acknowledgement survives: rc={} {}".format(rc2, rep2.get("acknowledged")))
    rep2["acknowledged"] = {"odd": "ok"}
    (td / "series-qc.json").write_text(json.dumps(rep2), encoding="utf-8")
    with _cl.redirect_stdout(_io.StringIO()):
        rc3 = ims.main(["qc", str(pf), "--dir", str(td)])
    check(rc3 == 1, "a one-word acknowledgement is not a reason")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_image_series] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
