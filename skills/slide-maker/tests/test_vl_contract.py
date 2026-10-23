"""The visual-language contract: the manifest validator (part 1) and the conformance checks over every registered
language (part 2, Task 3) and the docs blocks (part 3, Task 4). Prints `N passed, 0 failed`."""
import copy, re, sys
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
    t["attribution"] = (20, "body", False, "ink", False, 12)     # a credit never shrinks under the smallest tier
    return {
        "name": "fixture", "order": 99, "kind": "drawn",
        "display": {"en": "Fixture", "zh": "测试"}, "rationale": "drawn, no pictures: a test fixture",
        "blurb": {"en": "A plain test look: two grounds, one accent, nothing drawn.", "zh": "一套测试用的朴素外观，两种底色。"},
        "offer": {"en": ["testing", "fixtures"], "zh": ["测试", "样例"]},
        "look": {"palette": pal_l, "fonts": {"both": {"display": "Arial", "body": "Arial"},
                                             "mac": {"display": "Arial", "body": "Arial"}},
                 "ea": {"display": "sans", "body": "sans"}, "grain": 0, "frames": ["rect"], "forbids": (),
                 "cover": "low-left", "skeleton": "band"},
        "grounds": {
            "light": {"label": "paper", "label_zh": "纸面版", "grain": 0, "palette": pal_l, "dark": False,
                      "roles": {"card": "FFFFFF", "card_ink": "16191E", "rule": "C9C7C0", "on_accent": "FFFFFF",
                                "series": ["D7262E", "0071BC", "00954C", "8E4FA1"], "highlight": "1B2A41"}},
            "night": {"label": "navy", "label_zh": "夜间版", "grain": 0, "palette": pal_d, "dark": True,
                      "roles": {"card": "22344F", "card_ink": "F2F4F8", "rule": "3B4E6B", "on_accent": "0F1A2C",
                                "series": ["F2B705", "E8454C", "3D9BE0", "1DB66A"], "highlight": "F2B705"}}},
        "type": t, "image_pages": ("image_text",),
        "extras": {"tags": {"pages": ("points",), "remembered": False, "takes": "one label per point",
                            "absent": "no chips"}},
        "derived": [{"id": "point_numbers", "what": "1 2 3 on points", "words": {}}],
        "samples": {"copy": [("cover", {"title": "A fixture"})]},
        "painters": {"ground": "_ground_fixture", "card": "_card_fixture"},
        "skin": {"card": "filled", "rule": "solid", "marker": "disc-number", "number": "body"},
    }


# ── part 1: the validator ──
check(vc.validate(good_spec()) == [], "a complete manifest validates ({})".format(vc.validate(good_spec())))
for key in ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters", "skin"):
    s = good_spec(); del s[key]
    probs = vc.validate(s)
    check(any(key in p for p in probs), "a manifest without {!r} is refused naming it ({})".format(key, probs[:1]))
# the public blurb the library page shows (vl_library_export.py) — required, plain, long enough to say something
s = good_spec(); del s["blurb"]
check(any("blurb" in p for p in vc.validate(s)), "a manifest without a blurb is refused naming it")
s = good_spec(); s["blurb"] = {"en": "Too short.", "zh": "一套测试用的朴素外观，两种底色。"}
check(any("blurb" in p for p in vc.validate(s)), "an English blurb under 40 characters is refused")
s = good_spec(); s["blurb"] = {"en": "A plain test look: two grounds, one accent, nothing drawn.", "zh": "太短"}
check(any("blurb" in p for p in vc.validate(s)), "a Chinese blurb under 12 characters is refused")
s = good_spec(); s["blurb"] = {"en": "FILL: one or two sentences for visitors", "zh": "FILL: 同上"}
check(any("blurb" in p for p in vc.validate(s)), "an unfilled blurb is named as still to decide")
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
check(len(REG) == len([f for f in (ROOT / "scripts" / "vl_specs").glob("*.py") if not f.name.startswith("_")]),
      "every manifest file is registered ({})".format(len(REG)))
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
              ("grounds", {"light": None, "night": None}), ("skin", "chalk")]
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
    # Phase 3 (spec §6.2): the recurring design defects, held for every language — a new one included
    bs = vcf.bright_slabs(n)
    check(bs == [], "{}: no light-mode slab on a dark ground ({})".format(n, bs[:2]))
    rp = vcf.rules_past_content(n)
    check(rp == [], "{}: every column / margin rule ends at its text ({})".format(n, rp[:2]))
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

# ── final review, group B: the checks see everything and are proven to bite ──
import vl_native as _vn
# I1 + I2: a composition that invents a word or a number on ANY page, in either script, is caught with page and token
_orig_closing = _vn.COMPOSERS["tally"]["closing"]
def _inventing_closing(k, slide, f, image):
    r = _orig_closing(k, slide, f, image)
    import deckkit as _dk
    _dk.text(slide, 0.5, 0.5, 4.0, 0.5, [[("Revolution 98765 ⑲ 革命", 14, _dk.DEEP, False, False)]])
    return r
_vn.COMPOSERS["tally"]["closing"] = _inventing_closing
try:
    inv = vcf.invented_words("tally")
finally:
    _vn.COMPOSERS["tally"]["closing"] = _orig_closing
for tok in ("Revolution", "98765", "革", "命"):
    check(any("'{}'".format(tok) in x and "closing" in x for x in inv),
          "an invented {!r} on the closing page is caught, naming page and token ({})".format(tok, inv[:3]))
check(any("zh" in x for x in inv) and any("en" in x for x in inv), "both the English and the Chinese pass see the page")
check(not any("'1'" in x or "'02'" in x for x in inv), "page and section numbers (1-2 digits) are not inventions")
# initials are derived only where the manifest declares them, and only from the caller's own name
check(vcf.invented_words("interface") == [], "interface's initials from the caller's name are declared, not invented")
# I3: each conformance check is proven to bite (committed, not a manual note)
_ep = vl.EXTRA_PAGES["tags"]
vl.EXTRA_PAGES["tags"] = _ep + ("cover",)
try:
    nr = vcf.extras_not_refused("tally")
finally:
    vl.EXTRA_PAGES["tags"] = _ep
check(any("tags" in x and "accepted" in x for x in nr), "an extra accepted off its pages is caught ({})".format(nr[:1]))
vl.VARIANTS["tally"]["ghost"] = vl.VARIANTS["tally"]["night"]
try:
    am = vcf.assets_missing("tally")
finally:
    del vl.VARIANTS["tally"]["ghost"]
check(any("tally-ghost" in x and "sample" in x for x in am) and any("fingerprint" in x for x in am),
      "a ground with no bundled sample or fingerprint is caught ({})".format(am[:2]))
_sk = vcf.SKILL
fake = Path(tempfile.mkdtemp(prefix="fakeskill_"))
try:
    (fake / "tests").mkdir()
    (fake / "tests" / "test_native_generality.py").write_text("for name in ('ink',):\n    pass\n")
    (fake / "tests" / "test_vl_audit_fixes.py").write_text("OWN = []\n")
    vcf.SKILL = fake
    nd = vcf.suites_not_registry_driven()
finally:
    vcf.SKILL = _sk
    shutil.rmtree(fake, ignore_errors=True)
check(len(nd) == 2, "suites that stop iterating the registry are caught ({})".format(nd))
# M4: the checks leave nothing behind in the system temp folder
import glob as _glob
_before = set(_glob.glob(os.path.join(tempfile.gettempdir(), "vlconf_*")))
vcf.invented_words("poster")
check(set(_glob.glob(os.path.join(tempfile.gettempdir(), "vlconf_*"))) <= _before, "invented_words leaves no temp folder behind")

# a language still being authored (no compositions yet) is reported, never a traceback (author's dry run, Task 5)
import check_vl_contract as cvc
import vl_native as _vn0
_cov = _vn0.COMPOSERS["tally"].pop("cover")          # a language still being authored: no cover composition yet
try:
    try:
        r = vcf.invented_words("tally"); err = None
    except Exception as e:
        r, err = None, "{}: {}".format(type(e).__name__, e)
    check(err is None and r and "composition" in r[0], "invented_words reports an unbuildable language instead of raising ({} {})".format(err, r))
finally:
    _vn0.COMPOSERS["tally"]["cover"] = _cov
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

# the NEXT line names a command that runs: a copy of the skill with no tests/ (the SkillHub package, 2026-10-23) printed
# "NEXT: python3 …/tests/test_vl_contract.py", a file that is not there
_saved = {f: getattr(vcf, f) for f in ("painters_missing", "pages_missing", "assets_missing", "invented_words",
                                       "extras_not_refused", "bright_slabs", "rules_past_content")}
_tests0 = cvc.TESTS if hasattr(cvc, "TESTS") else None
try:
    for _f in _saved:
        setattr(vcf, _f, lambda n, registry=None: [])
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = cvc.main(["tally"])
    _nx = [l for l in out.getvalue().splitlines() if l.startswith("NEXT:")]
    check(rc == 0 and len(_nx) == 1 and Path(_nx[0].split()[-1]).is_file(),
          "a clean check names the contract tests, a file that exists: {}".format(_nx))
    cvc.TESTS = Path(tempfile.mkdtemp(prefix="notests_"))
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = cvc.main(["tally"])
    _txt = out.getvalue()
    check(rc == 0 and "NEXT:" not in _txt and "source repository" in _txt,
          "without tests/ the check names no missing file and says where the tests run: {!r}".format(_txt[-200:]))
finally:
    for _f, _v in _saved.items():
        setattr(vcf, _f, _v)
    if _tests0 is not None:
        cvc.TESTS = _tests0

# ── part 3: docs blocks follow the registry ──
import vl_docs
_n = len(REG); _nd = len([s_ for s_ in REG.values() if s_["kind"] == "drawn"]); _ni = _n - _nd
check(vl_docs.render("count-all") == vl_docs._en(_n) and vl_docs.render("count-drawn") == vl_docs._en(_nd)
      and vl_docs.render("count-image") == vl_docs._en(_ni), "the count blocks read the registry's counts")
check(vl_docs.render("count-image-cap") == vl_docs._en(_ni).capitalize(), "a sentence-initial count is capitalised")
check(vl_docs.render("count-all-zh") == vl_docs._zh(_n) and vl_docs.render("count-image-zh") == vl_docs._zh(_ni),
      "the Chinese counts read the registry's counts")
drawn_names = [s_["name"] for s_ in REG.values() if s_["kind"] == "drawn"]
image_names = [s_["name"] for s_ in REG.values() if s_["kind"] == "image-led"]
check(vl_docs.render("list-drawn") == " · ".join("`{}`".format(n_) for n_ in drawn_names), "the drawn list follows the registry")
check(vl_docs.render("list-image") == " · ".join("`{}`".format(n_) for n_ in image_names), "the image-led list follows the registry")
check(vl_docs.render("list-image-comma") == ", ".join("`{}`".format(n_) for n_ in image_names), "the comma image-led list")
check(vl_docs.render("list-drawn-plain") == ", ".join(drawn_names), "the plain drawn list (file inventory)")
check("culture, history, craft → `ink`" in vl_docs.render("offer-arrow"), "the arrow guidance names ink's topics")
check("`ink` (culture, history, craft)" in vl_docs.render("offer-paren"), "the parenthesised guidance names ink's topics")
check("文化、历史、器物 → 水墨" in vl_docs.render("offer-zh"), "the Chinese guidance names 水墨's topics")
check(vl_docs.check() == [], "every docs block is current and every required block is present ({})".format(vl_docs.check()[:2]))
# I6 + M1: marker integrity, on TEMP copies (a killed test must not leave a tracked doc edited)
tmpd = Path(tempfile.mkdtemp(prefix="vldocs_"))
try:
    t = tmpd / "visual-languages.md"
    shutil.copy(ROOT / "references" / "visual-languages.md", t)
    docs = {t: vl_docs.REQUIRED[ROOT / "references" / "visual-languages.md"]}
    # whatever the count reads today (it grows with every language): a hard-coded "fifteen" stopped matching at 19
    t.write_text(re.sub(r"(<!-- vl:count-all -->)[^<]+", r"\1zero", t.read_text(encoding="utf-8"), count=1),
                 encoding="utf-8")
    probs = vl_docs.check(docs=docs)
    check(any("visual-languages.md" in p_ and "count-all" in p_ for p_ in probs), "a hand-edited block is named ({})".format(probs[:1]))
    vl_docs.write(docs=docs)
    check(vl_docs.check(docs=docs) == [], "--write restores a hand-edited block")
    before = t.read_text(encoding="utf-8")
    broken = before.replace("<!-- /vl -->", "", 1)                 # one closing marker lost
    t.write_text(broken, encoding="utf-8")
    probs = vl_docs.check(docs=docs)
    check(any("unbalanced" in p_ for p_ in probs), "an unbalanced marker is named ({})".format(probs[:1]))
    res = vl_docs.write(docs=docs)
    check(t.read_text(encoding="utf-8") == broken and res and "unbalanced" in str(res),
          "--write refuses an unbalanced doc and changes nothing (it swallowed prose before)")
    t.write_text(before.replace("<!-- vl:count-all -->", "<!-- vl:count-everything -->", 1), encoding="utf-8")
    try:
        probs = vl_docs.check(docs=docs); crash = None
    except Exception as e:
        probs, crash = [], "{}: {}".format(type(e).__name__, e)
    check(crash is None and any("count-everything" in p_ and "visual-languages.md" in p_ for p_ in probs),
          "an unknown block is named with its file ({} {})".format(crash, probs[:1]))
    t.write_text(_BLOCKLESS := __import__("re").sub(r"<!-- /?vl[^>]*-->", "", before), encoding="utf-8")
    probs = vl_docs.check(docs=docs)
    check(any("count-all" in p_ and "missing" in p_ for p_ in probs), "a doc whose required blocks were removed is caught ({})".format(probs[:1]))
finally:
    shutil.rmtree(tmpd, ignore_errors=True)
# I7: the SKILL.md lossless gate reads a vl block as one thing, so a new language does not need waivers
import check_skill_lossless as _csl
check(_csl.normalize("and the <!-- vl:count-drawn -->eleven<!-- /vl --> drawn ones below")
      == _csl.normalize("and the <!-- vl:count-drawn -->twelve<!-- /vl --> drawn ones below"),
      "the lossless gate ignores what is inside a vl block")

# ── part 2 (Task 3) and part 3 (Task 4) are appended above this line ──

# Phase 2b: four designed series colours per ground (spec §4.1 ruling; approved on the 2b sheet, 2026-10-15)
check(vc.SERIES_MIN == 4, "the series floor is four designed colours per ground")
check(all(len(G["roles"]["series"]) >= 4 for s_ in vl_specs.load().values() for G in s_["grounds"].values()),
      "every ground carries at least four series colours")

# the README gallery is a fixed showcase: a language without a cell lives on the library page, and the README
# names how many more there are. Since 2026-10-23 it is twelve looks the user asked for, generated from SHOWCASE, three
# to a row like the template gallery, each cell opening its language in the library section of the home page
import vl_docs as _vd
_reg = vl_specs.load()
_g = _vd.gallery(_reg)
check(len(_vd.SHOWCASE) == 12 == len(set(_vd.SHOWCASE)) and set(_vd.SHOWCASE) <= set(_reg),
      "SHOWCASE names twelve distinct registered languages: {}".format(_vd.SHOWCASE))
check(_g == set(_vd.SHOWCASE) and len(_g) < len(_reg),
      "the README gallery shows exactly the showcase, not every language ({})".format(sorted(_g or [])))
for _blk, _site in (("vl-gallery", "https://slides.addsum.top/#vl-"), ("vl-gallery-zh", "https://slides.addsum.top/cn/#vl-")):
    _t = _vd._render(_blk, _reg)
    _cells = re.findall(r"<td[^>]*>(.*?)</td>", _t, re.S)
    check(len(_cells) == 12 and _t.count("<tr>") == 4,
          "{} lays twelve cells out three to a row ({} cells, {} rows)".format(_blk, len(_cells), _t.count("<tr>")))
    check(all(c.count('href="{}{}"'.format(_site, n)) == 2 and "samples/{}.jpg".format(n) in c
              for n, c in zip(_vd.SHOWCASE, _cells)),
          "{}: every cell shows its sample and links its picture and its line to {}<name>".format(_blk, _site))
    check(all(re.search(r"<strong>[^<]+</strong>", c) for c in _cells), "{}: every cell names its look".format(_blk))
check("配你的照片" in _vd._render("vl-gallery-zh", _reg) and "with your photos" in _vd._render("vl-gallery", _reg),
      "a picture language says what it carries instead of topic tags")
_bad_show = _vd.SHOWCASE
try:
    _vd.SHOWCASE = _bad_show[:11] + ("nosuchlook",)
    _err = None
    try:
        _vd._render("vl-gallery", _reg)
    except ValueError as e:
        _err = str(e)
    check(_err is not None and "nosuchlook" in _err, "a showcase name with no language fails loudly: {!r}".format(_err))
finally:
    _vd.SHOWCASE = _bad_show
# the section sits directly under the template gallery (the user, 2026-10-23), in both READMEs
for _f, _a, _b, _c in (("README.md", "## Template gallery", "## Visual languages", "## How to use the templates"),
                       ("README_CN.md", "## 模板库", "## 设计语言", "## 模板怎么用")):
    _txt = (_vd.REPO / _f).read_text(encoding="utf-8")
    _heads = [l for l in _txt.splitlines() if l.startswith("## ")]
    check(_a in _heads and _b in _heads and _c in _heads and _heads.index(_b) == _heads.index(_a) + 1 and
          _heads.index(_c) == _heads.index(_b) + 1,
          "{}: the visual languages follow the template gallery and precede how to use it ({})".format(_f, _heads[:6]))
_n_more = len(_reg) - len(_g)
check(_vd._render("gallery-more", _reg).startswith("The gallery above shows {} of them; {} more".format(
      _vd._en(len(_g)), _vd._en(_n_more))), "gallery-more names the gallery and how many more: {!r}".format(
      _vd._render("gallery-more", _reg)))
check(_vd._render("gallery-more-zh", _reg).startswith("上面只展示了其中{}套".format(_vd._zh(len(_g)))),
      "gallery-more-zh names the gallery: {!r}".format(_vd._render("gallery-more-zh", _reg)))
_all_shown = {n: s_ for n, s_ in _reg.items() if n in _g}
check(_vd._render("gallery-more", _all_shown) == "" and _vd._render("gallery-more-zh", _all_shown) == "",
      "with every language in the gallery the clause says nothing (no 'zero more')")
# counts past twenty stay words: "four image-led and 26 drawn" mixed the two styles in one sentence (2026-10-22, 30)
check([_vd._en(n) for n in (19, 20, 21, 26, 30, 45, 99)] ==
      ["nineteen", "twenty", "twenty-one", "twenty-six", "thirty", "forty-five", "ninety-nine"],
      "_en spells counts past twenty: {}".format([_vd._en(n) for n in (21, 26, 30, 99)]))
# the badge beside ClawHub counts the library (2026-10-22): generated, so the number follows the registry
_b = _vd._render("vl-badge", _reg)
# the library is a section of the home page since 2026-10-23 (#languages), the Chinese badge on the Chinese home page
check('href="https://slides.addsum.top/#languages"' in _b and "-{}-".format(len(_reg)) in _b and "alt=\"Visual languages: {}\"".format(len(_reg)) in _b,
      "vl-badge links the library section and carries the count: {!r}".format(_b))
_bz = _vd._render("vl-badge-zh", _reg)
check('href="https://slides.addsum.top/cn/#languages"' in _bz and "-{}-".format(len(_reg)) in _bz,
      "vl-badge-zh links the Chinese home page's library and carries the count: {!r}".format(_bz))
for _f, _url in (("README.md", "https://slides.addsum.top/#languages"), ("README_CN.md", "https://slides.addsum.top/cn/#languages")):
    _txt = (_vd.REPO / _f).read_text(encoding="utf-8")
    check("slides.addsum.top/languages/\"" not in _txt and _txt.count(_url) >= 2,
          "{} links the library section ({}), not the retired /languages/ page".format(_f, _url))
for _f, _blk in (("README.md", "vl-badge"), ("README_CN.md", "vl-badge-zh")):
    _txt = (_vd.REPO / _f).read_text(encoding="utf-8")
    _i, _j = _txt.find("<!-- vl:{} -->".format(_blk)), _txt.find("clawhub")
    check(_i >= 0 and abs(_i - _j) < 400, "{} carries {} beside the ClawHub badge".format(_f, _blk))
import vl_conformance as _vcf1
check(not any("gallery" in x for x in _vcf1.assets_missing("herbarium")),
      "a language off the README gallery is not a missing asset: {}".format(_vcf1.assets_missing("herbarium")))
_repo1 = _vcf1.REPO
_t1 = Path(tempfile.mkdtemp(prefix="gal_"))
try:
    (_t1 / "README.md").write_text("samples/ink.jpg samples/tally.jpg", encoding="utf-8")
    (_t1 / "README_CN.md").write_text("samples/ink.jpg", encoding="utf-8")
    _vcf1.REPO = _t1
    check(any("README_CN.md" in x for x in _vcf1.assets_missing("tally")) and
          not any("gallery" in x for x in _vcf1.assets_missing("ink")),
          "a language in one README's gallery and not the other's is named: {}".format(_vcf1.assets_missing("tally")))
finally:
    _vcf1.REPO = _repo1; shutil.rmtree(_t1, ignore_errors=True)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
