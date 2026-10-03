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
         "subject": "a potter's hands shaping wet clay on a turning wheel", "kind": "scene",
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
    # ...and when the KEY image itself is a cut-out, the others are compared with its subject
    pk = copy.deepcopy(plan); pk["key"] = "kettle"
    fh = {s["id"]: s["flags"] for s in ims.qc(pk, td)["slots"]}["hero"]
    check(not any("OFF-SERIES" in f for f in fh), "a cut-out key must be compared on its subject: {}".format(fh))
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
    kett.save(td / "slide-03-kettle.cut.png")
    warm(td / "slide-03-kettle.png", size=(300, 300))
    prs = dk.blank_deck(13.333, 7.5)
    s1 = dk.add_slide(prs)
    pic = ims.slot_picture(s1, GOOD, "hero", 0.6, 0.8, 4.2, 5.6, image_dir=td)
    check(dk.generated_slot(pic) == "hero", "slot_picture must tag the picture with its slot")
    check("round2SameRect" in pic._element.xml, "the hero's arch frame must be applied")
    check(pic._element.find(".//" + dk.qn("p:cNvPr")).get("descr") == GOOD["slots"][0]["alt"], "alt from the plan")
    s3 = dk.add_slide(prs)
    cp = ims.slot_picture(s3, GOOD, "kettle", 6.0, 1.0, 3.0, 3.0, image_dir=td)
    check(dk.generated_slot(cp) == "kettle" and cp.image.content_type == "image/png", "cut-out slot places the keyed PNG")
    try:
        ims.slot_picture(s3, GOOD, "hero", 1, 1, 1, 1, image_dir=td / "nowhere")
        fails.append("slot_picture accepted a missing image")
    except FileNotFoundError as e:
        check("--only hero" in str(e), "the refusal should print the command that makes it: {}".format(e))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_image_series] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
