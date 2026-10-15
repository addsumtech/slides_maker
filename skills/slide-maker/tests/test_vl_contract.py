"""The visual-language contract: the manifest validator (part 1) and the conformance checks over every registered
language (part 2, Task 3) and the docs blocks (part 3, Task 4). Prints `N passed, 0 failed`."""
import copy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import vl_contract as vc

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)


def good_spec():
    """A minimal valid manifest (a light and a dark ground) — the unit tests mutate a copy of it."""
    pal_l = {"ground": "F6F5F1", "ink": "16191E", "mute": "5A6070", "panel": "FFFFFF",
             "accents": ["D7262E", "0071BC"], "text_accents": ["1B2A41"]}
    pal_d = {"ground": "1B2A41", "ink": "F2F4F8", "mute": "B9C3D4", "panel": "22344F",
             "accents": ["E8454C", "3D9BE0"], "text_accents": ["F2B705"]}
    t = {r: (20, "body", False, "ink", False, 11) for r in vc.CORE_TYPE}
    return {
        "name": "fixture", "order": 99, "kind": "drawn",
        "display": {"en": "Fixture", "zh": "测试"}, "rationale": "drawn, no pictures: a test fixture",
        "offer": {"en": ["testing", "fixtures"], "zh": ["测试", "样例"]},
        "look": {"palette": pal_l, "fonts": {"both": {"display": "Arial", "body": "Arial"},
                                             "mac": {"display": "Arial", "body": "Arial"}},
                 "ea": {"display": "sans", "body": "sans"}, "grain": 0, "frames": ["rect"], "forbids": (),
                 "cover": "low-left", "skeleton": "band"},
        "grounds": {
            "light": {"label": "paper", "label_zh": "纸面版", "grain": 0, "palette": pal_l, "dark": False,
                      "roles": {"card": "FFFFFF", "card_ink": "16191E", "rule": "C9C7C0", "on_accent": "FFFFFF",
                                "series": ["D7262E", "0071BC"], "highlight": "1B2A41"}},
            "night": {"label": "navy", "label_zh": "夜间版", "grain": 0, "palette": pal_d, "dark": True,
                      "roles": {"card": "22344F", "card_ink": "F2F4F8", "rule": "3B4E6B", "on_accent": "0F1A2C",
                                "series": ["F2B705", "E8454C"], "highlight": "F2B705"}}},
        "type": t, "image_pages": ("image_text",),
        "extras": {"tags": {"pages": ("points",), "remembered": False, "takes": "one label per point",
                            "absent": "no chips"}},
        "derived": [{"id": "point_numbers", "what": "1 2 3 on points", "words": {}}],
        "samples": {"copy": [("cover", {"title": "A fixture"})]},
        "painters": {"ground": "_ground_fixture", "card": "_card_fixture"},
    }


# ── part 1: the validator ──
check(vc.validate(good_spec()) == [], "a complete manifest validates ({})".format(vc.validate(good_spec())))
for key in ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters"):
    s = good_spec(); del s[key]
    probs = vc.validate(s)
    check(any(key in p for p in probs), "a manifest without {!r} is refused naming it ({})".format(key, probs[:1]))
s = good_spec(); s["kind"] = "painted"
check(any("kind" in p for p in vc.validate(s)), "an unknown kind is refused")
s = good_spec(); s["grounds"]["night"]["dark"] = False
check(any("dark" in p and "night" in p for p in vc.validate(s)),
      "a dark flag that disagrees with the colours is refused, naming the ground (Review Focus 1)")
s = good_spec(); s["grounds"]["light"]["palette"] = dict(s["grounds"]["light"]["palette"], ink="9A9A9A")
check(any("ink" in p and "light" in p for p in vc.validate(s)), "an ink under 4.5:1 on its ground is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["card_ink"] = "EEEEEE"
check(any("card_ink" in p for p in vc.validate(s)), "a card ink under 4.5:1 on its card is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["series"] = []
check(any("series" in p for p in vc.validate(s)), "an empty series is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["series"] = ["F6F5F0"]
check(any("series" in p for p in vc.validate(s)), "a series colour under 3:1 on the ground is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["series"] = ["D7262E", "D9282F"]
check(any("series" in p and "distinguish" in p for p in vc.validate(s)), "two near-identical series colours are refused")
s = good_spec(); del s["type"]["quote"]
check(any("quote" in p for p in vc.validate(s)), "a missing core type role is refused, naming it")
s = good_spec(); s["image_pages"] = ("gallery",)
check(any("gallery" in p for p in vc.validate(s)), "an image page that is not a page is refused")
s = good_spec(); s["extras"]["tags"]["pages"] = ("sidebar",)
check(any("sidebar" in p for p in vc.validate(s)), "an extra on an unknown page is refused")
s = good_spec(); s["grounds"]["light"]["roles"]["rule"] = "nothex"
check(any("rule" in p for p in vc.validate(s)), "a colour that is not 6-digit hex is refused")
s = good_spec(); s["offer"] = {"en": [], "zh": []}
check(any("offer" in p for p in vc.validate(s)), "a drawn language with no offer topics is refused")
a, b = good_spec(), good_spec()
b["name"], b["order"] = "fixture2", 100
b["extras"]["tags"]["pages"] = ("data",)
probs = vc.validate_all({"fixture": a, "fixture2": b})
check(any("tags" in p and "fixture" in p and "fixture2" in p for p in probs),
      "one extra name with two meanings is refused, naming both languages (Review Focus 2): {}".format(probs[:1]))
b2 = good_spec(); b2["name"] = "fixture2"
check(any("order" in p for p in vc.validate_all({"fixture": good_spec(), "fixture2": b2})), "a duplicate order is refused")
check(abs(vc.contrast("FFFFFF", "000000") - 21.0) < 0.01, "contrast(white, black) is 21")
check(vc.delta_e("FF0000", "FF0000") == 0.0 and vc.delta_e("FF0000", "0000FF") > 50, "delta_e is a colour distance")

# ── part 2 (Task 3) and part 3 (Task 4) are appended above this line ──

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
