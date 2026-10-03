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

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_image_series] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
