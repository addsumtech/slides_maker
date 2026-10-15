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

# ── the registry: every language is a manifest, and the manifests are valid ──
import vl_specs
import visual_languages as vl
REG = vl_specs.load()
check(list(REG) == list(vl.LANGS), "the registry and LANGS list the same languages in the same order")
check(len(REG) == 15, "fifteen languages are registered ({})".format(len(REG)))
probs = vc.validate_all(REG)
check(probs == [], "every manifest satisfies the contract: {}".format(probs[:4]))
check(vl.REGISTRY is not None and set(vl.REGISTRY) == set(REG), "visual_languages exposes REGISTRY")
for n, s in REG.items():
    for g, gd in s["grounds"].items():
        check(gd["palette"] == vl.VARIANTS[n][g]["palette"], "{}/{}: VARIANTS is built from the manifest".format(n, g))

# ── final review, group A: manifests that cannot brick the skill ──
import os, json, tempfile, shutil, contextlib, io
def _strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from _strings(v)
    elif isinstance(o, (list, tuple)):
        for v in o: yield from _strings(v)
absolute = [(n, x) for n, sp in REG.items() for x in _strings(sp) if os.path.isabs(x) or x.startswith("~")]
check(absolute == [], "no manifest string is an absolute path — a machine path breaks every other checkout (C1): {}".format(absolute[:2]))
missing_img = [(n, f.get("image")) for n in vl.NATIVE for _p, f in vl._SAMPLE_COPY_NATIVE[n]
               if isinstance(f, dict) and f.get("image") and not Path(f["image"]).is_file()]
check(missing_img == [], "every sample image resolves to a file ({})".format(missing_img))
# I4: load() refuses what would silently brick or shadow a language, naming the file
def _load_dir(files):
    d = Path(tempfile.mkdtemp(prefix="vlspec_"))
    shutil.copy(ROOT / "scripts" / "vl_specs" / "__init__.py", d / "__init__.py")
    for name, text in files.items():
        (d / (name + ".py")).write_text(text, encoding="utf-8")
    try:
        vl_specs.load(directory=d); return None
    except ValueError as e:
        return str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
tally_src = (ROOT / "scripts" / "vl_specs" / "tally.py").read_text(encoding="utf-8")
err = _load_dir({"tally": tally_src, "tallytwo": tally_src.replace("'order': 12", "'order': 16", 1)})
check(err and "tallytwo" in err and "name" in err, "a copied manifest that keeps the old name is refused, naming the file ({})".format(err))
err = _load_dir({"tally": tally_src.replace("'look':", "'look_missing':", 1)})
check(err and "tally" in err and "look" in err, "a manifest missing a top-level key is refused at load, naming file and key ({})".format(err))
import check_vl_contract as cvc
d = Path(tempfile.mkdtemp(prefix="vlspec_"))
try:
    for f in (ROOT / "scripts" / "vl_specs").glob("*.py"):
        shutil.copy(f, d / f.name)
    (d / "tally.py").write_text(tally_src.replace("'look':", "'look_missing':", 1), encoding="utf-8")
    os.environ["VL_SPECS_DIR"] = str(d)
    with contextlib.redirect_stdout(io.StringIO()) as out:
        try:
            rc = cvc.main(["tally"]); crash = None
        except Exception as e:
            rc, crash = None, "{}: {}".format(type(e).__name__, e)
    check(crash is None and rc == 1 and "look" in out.getvalue(),
          "check_vl_contract names a broken manifest instead of crashing ({} {})".format(rc, crash))
finally:
    os.environ.pop("VL_SPECS_DIR", None)
    shutil.rmtree(d, ignore_errors=True)
# I5: one palette, and the tables are copies (code that edits a table cannot rewrite a manifest)
s = good_spec(); s["look"] = dict(s["look"], palette=dict(s["look"]["palette"], ink="000000"))
check(any("look" in p and "palette" in p for p in vc.validate(s)), "look.palette that differs from grounds.light.palette is refused")
s = good_spec(); s["look"] = {}
check(any("look" in p for p in vc.validate(s)), "an empty look is refused")
check(all(vl.VARIANTS[n]["light"]["palette"] is vl.LANGS[n]["palette"] for n in REG), "the light palette is ONE object, as before the migration")
check(all(vl.TYPE[n] is not REG[n]["type"] and vl.LANGS[n] is not REG[n]["look"] for n in REG),
      "the tables are copies of the manifests, not aliases into them")
# I8: wrong-typed nested values are named, never a traceback
bad_inputs = [("display", None), ("offer", None), ("samples", None), ("painters", None), ("extras", {"tags": "points"}),
              ("grounds", {"light": None, "night": None})]
for key, val in bad_inputs:
    s = good_spec(); s[key] = val
    try:
        probs = vc.validate(s); crash = None
    except Exception as e:
        probs, crash = [], "{}: {}".format(type(e).__name__, e)
    check(crash is None and probs, "validate names a wrong-typed {} instead of raising ({})".format(key, crash))
for mut in ("palette_none", "series_str"):
    s = good_spec()
    if mut == "palette_none": s["grounds"]["light"]["palette"] = None
    else: s["grounds"]["light"]["roles"]["series"] = "D7262E"
    try:
        probs = vc.validate(s); crash = None
    except Exception as e:
        probs, crash = [], "{}: {}".format(type(e).__name__, e)
    check(crash is None and probs, "validate names {} instead of raising ({})".format(mut, crash))
a2, b2 = good_spec(), good_spec(); b2["name"], b2["order"] = "fixture2", 100; b2["extras"]["tags"]["pages"] = ["points"]
try:
    probs = vc.validate_all({"fixture": a2, "fixture2": b2}); crash = None
except Exception as e:
    probs, crash = [], "{}: {}".format(type(e).__name__, e)
check(crash is None and any("tags" in p for p in probs), "validate_all names a list-typed extra pages instead of raising ({})".format(crash))
# M6 (re-graded): the installed copy has no repo README — the checks skip it, never crash
import vl_conformance as _vcf0
_repo = _vcf0.REPO
_vcf0.REPO = Path(tempfile.mkdtemp(prefix="norepo_"))
try:
    try:
        r = _vcf0.assets_missing("tally"); crash = None
    except Exception as e:
        r, crash = None, "{}: {}".format(type(e).__name__, e)
    check(crash is None and not any("README" in x for x in (r or [])), "assets_missing skips the README rows when there is no repo README ({} {})".format(crash, r))
finally:
    shutil.rmtree(_vcf0.REPO, ignore_errors=True); _vcf0.REPO = _repo

# ── part 2: conformance over every registered language ──
import vl_conformance as vcf
for n in REG:
    check(vcf.pages_missing(n) == [], "{}: all seven pages have a composition ({})".format(n, vcf.pages_missing(n)))
    inv = vcf.invented_words(n)
    check(inv == [], "{}: every word on its sample pages is the caller's or declared derived ({})".format(n, inv[:3]))
    nr = vcf.extras_not_refused(n)
    check(nr == [], "{}: every extra is refused by name off its pages ({})".format(n, nr[:2]))
    am = vcf.assets_missing(n)
    check(am == [], "{}: samples, sigs scaffold and docs rows exist ({})".format(n, am[:3]))
check(vcf.suites_not_registry_driven() == [], "the build-matrix and own-pages suites iterate the registry ({})".format(
    vcf.suites_not_registry_driven()))
# Review Focus 3: a manifest with no compositions names every missing page, no crash
fx = good_spec()
miss = vcf.pages_missing("fixture", registry={"fixture": fx})
check(len(miss) == 7 and all("fixture" in m for m in miss), "a language with no compositions names its 7 missing pages ({})".format(miss[:1]))
# Review Focus 4: re-cased and clause-broken caller words are the caller's; a new word is not
tok = vcf.allowed_tokens("journal", ["Why every street deserves a place, not a bin", "社区修理网络，年度回顾"])
check({"WHY", "STREET", "DESERVES"} <= tok, "re-cased caller words are allowed tokens")
check({"社", "区", "年"} <= tok, "Chinese caller characters are allowed tokens")
check("ABSTRACT" in tok and "摘" in tok, "a declared derived label is an allowed token")
check("REVOLUTION" not in tok, "a word the caller never gave is not allowed")

# a language still being authored (no compositions yet) is reported, never a traceback (author's dry run, Task 5)
import check_vl_contract as cvc
_bs, _use = vl.build_sample, vl.use
def _no_comp(*a, **k):
    raise NotImplementedError("tally.cover(): no composition is registered for this page")
vl.build_sample = _no_comp
try:
    try:
        r = vcf.invented_words("tally"); err = None
    except Exception as e:
        r, err = None, "{}: {}".format(type(e).__name__, e)
    check(err is None and r and "composition" in r[0], "invented_words reports an unbuildable sample deck instead of raising ({} {})".format(err, r))
finally:
    vl.build_sample = _bs
_pages = vcf.pages_missing
vcf.pages_missing = lambda n, registry=None: ["{}: no composition for page 'cover'".format(n)]
_calls = []
_iw, _ex = vcf.invented_words, vcf.extras_not_refused
vcf.invented_words = lambda n: _calls.append(n) or []
vcf.extras_not_refused = lambda n: _calls.append(n) or []
try:
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = cvc.main(["tally"])
    check(rc == 1 and not _calls and "skipped" in out.getvalue(),
          "check_vl_contract skips the build checks while pages are missing, and says so ({} {})".format(rc, _calls))
finally:
    vcf.pages_missing, vcf.invented_words, vcf.extras_not_refused = _pages, _iw, _ex

# ── part 3: docs blocks follow the registry ──
import vl_docs
check(vl_docs.render("count-all") == "fifteen" and vl_docs.render("count-drawn") == "eleven"
      and vl_docs.render("count-image") == "four", "the count blocks read fifteen / eleven / four")
check(vl_docs.render("count-all-zh") == "十五" and vl_docs.render("count-drawn-zh") == "十一", "the Chinese counts read 十五 / 十一")
check(vl_docs.render("list-drawn").startswith("`ink` · `poster`") and vl_docs.render("list-drawn").endswith("`wayfinding`"),
      "the drawn list runs ink … wayfinding")
check("culture, history, craft → `ink`" in vl_docs.render("offer-arrow"), "the arrow guidance names ink's topics")
check("`ink` (culture, history, craft)" in vl_docs.render("offer-paren"), "the parenthesised guidance names ink's topics")
check("文化、历史、器物 → 水墨" in vl_docs.render("offer-zh"), "the Chinese guidance names 水墨's topics")
check(vl_docs.check() == [], "every docs block is current ({})".format(vl_docs.check()[:2]))
# Review Focus 5: a hand edit inside a block is caught, and --write restores it
import shutil, tempfile
tmp = Path(tempfile.mkdtemp())
src = ROOT / "references" / "visual-languages.md"
shutil.copy(src, tmp / "vl.md")
try:
    src.write_text(src.read_text(encoding="utf-8").replace("<!-- vl:count-all -->fifteen", "<!-- vl:count-all -->nine", 1),
                   encoding="utf-8")
    probs = vl_docs.check()
    check(any("visual-languages.md" in p and "count-all" in p for p in probs), "a hand-edited block is named ({})".format(probs[:1]))
    vl_docs.write()
    check(vl_docs.check() == [], "--write restores the block")
finally:
    shutil.copy(tmp / "vl.md", src)

# ── part 2 (Task 3) and part 3 (Task 4) are appended above this line ──

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
