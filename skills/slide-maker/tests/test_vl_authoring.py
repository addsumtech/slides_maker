"""Phase 4 — the authoring kit and any-agent use (spec §7): a sixteenth language is started by one command and named
by the checks until it is finished, without breaking the fifteen; the docs and the scripts' printed output are enough
for an agent that is not Claude. Prints `N passed, 0 failed`."""
import contextlib, copy, io, os, pprint, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import vl_contract as vc, vl_specs

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)
WORK = Path(tempfile.mkdtemp(prefix="vlauth_"))
SHIPPED = vl_specs.load()


def _write_spec(d, spec):
    (d / (spec["name"] + ".py")).write_text("SPEC = " + pprint.pformat(spec, width=118, sort_dicts=False) + "\n",
                                            encoding="utf-8")


def mosaic_spec():
    """tally's manifest as a sixteenth language: its own name, order, painters, and a ground/accent far enough from
    every shipped language's that the manifest validates on its own."""
    s = copy.deepcopy(SHIPPED["tally"])
    s["name"], s["order"] = "mosaic", max(v["order"] for v in SHIPPED.values()) + 1
    s["painters"] = {"ground": "_ground_mosaic", "card": "_card_mosaic"}
    for g, (ground, accent) in zip(s["grounds"], (("FAF6FC", "6A1B9A"), ("1E0B2E", "F06292"))):
        s["grounds"][g]["palette"]["ground"] = ground
        s["grounds"][g]["palette"]["accents"] = [accent] + list(s["grounds"][g]["palette"]["accents"][1:])
    s["look"]["palette"] = s["grounds"]["light"]["palette"]
    return s


def specs_dir_with(*extra):
    d = Path(tempfile.mkdtemp(prefix="vlspecs_", dir=WORK))
    for f in (ROOT / "scripts" / "vl_specs").glob("*.py"):
        if not f.name.startswith("_"):
            shutil.copy(f, d / f.name)
    for s in extra:
        _write_spec(d, s)
    return d


def run(code_or_args, env_extra=None, script=False):
    env = dict(os.environ, **(env_extra or {}))
    cmd = [sys.executable] + (code_or_args if script else ["-c", "import sys; sys.path.insert(0, 'scripts'); " + code_or_args])
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)


# ── Task 1: a language's code is discovered; a manifest whose painters are not written breaks only that language ──
_m = mosaic_spec()
check(not [p for p in vc.validate(_m)], "the mosaic fixture manifest validates on its own ({})".format(vc.validate(_m)[:1]))
check(not [p for p in vc.distinct_pairs(dict(SHIPPED, mosaic=_m)) if "mosaic" in p],
      "the mosaic fixture is distinct from every shipped language")
D16 = specs_dir_with(_m)
ENV16 = {"VL_SPECS_DIR": str(D16)}
r = run("import deckkit as dk, visual_languages as vl; prs = dk.blank_deck(13.333, 7.5); k = vl.use('tally', prs); "
        "k.cover(k.new_slide(), title='Fix it together'); print('ok')", ENV16)
check(r.returncode == 0 and "ok" in r.stdout, "a 16th manifest with no code leaves tally working ({})".format(r.stderr[-160:]))
r = run("import deckkit as dk, visual_languages as vl; prs = dk.blank_deck(13.333, 7.5); vl.use('mosaic', prs)", ENV16)
check(r.returncode != 0 and "vl_langs/mosaic.py" in r.stderr and "_ground_mosaic" in r.stderr and "KeyError" not in r.stderr,
      "using the unready language is refused by name, naming the file to write ({})".format(r.stderr[-160:]))
r = run([str(ROOT / "scripts" / "check_vl_contract.py"), "mosaic"], ENV16, script=True)
check(r.returncode == 1 and "_ground_mosaic" in r.stdout and "Traceback" not in r.stdout + r.stderr,
      "check_vl_contract names the unwritten painters instead of crashing ({} {})".format(r.returncode, (r.stdout + r.stderr)[-160:]))
_bad = copy.deepcopy(_m); _bad["painters"] = {"ground": "ground", "card": "_card_mosaic"}
check(any("painters" in p and "_ground_mosaic" in p for p in vc.validate(_bad)),
      "a painter not named _ground_<name> / _card_<name> is refused by the manifest check")

# ── Task 2: an unfilled field and a stub page are named, with the file to edit ──
_s = mosaic_spec()
_s["display"]["zh"] = "FILL: the language's Chinese name"
_s["grounds"]["night"]["palette"]["accents"][0] = "FILL: one accent that reads on the night ground"
_p = vc.validate(_s)
check(any("display.zh" in x and "Chinese name" in x for x in _p), "an unfilled display.zh is named by its path and hint ({})".format(_p[:2]))
check(any("grounds.night.palette.accents[0]" in x for x in _p), "an unfilled list item is named by its path")
check(_p and all("not filled" in x for x in _p), "while fields are unfilled, only they are reported (not as bad hexes)")
check(vc.unfilled(mosaic_spec()) == [], "a filled manifest has nothing unfilled")
import vl_native as vn, vl_conformance as vcf
vn.stub("stubcheck", "cover")
_pm = vcf.pages_missing("stubcheck", registry={"stubcheck": {"kind": "drawn"}})
check(any("cover" in x and "still a stub" in x and "scripts/vl_langs/stubcheck.py" in x for x in _pm),
      "a stub page is a missing page, naming the file to compose it in ({})".format(_pm[:1]))
check(len(_pm) == 7, "the six unregistered pages are missing too ({})".format(len(_pm)))
try:
    vn.COMPOSERS["stubcheck"]["cover"](None, None, {}, None); _raised = None
except NotImplementedError as e:
    _raised = str(e)
check(_raised and "stubcheck" in _raised and "cover" in _raised, "a stub raises, naming its language and page")

# ── Task 3: new_visual_language.py starts a language; check_vl_contract names everything still to do ──
GEN = str(ROOT / "scripts" / "new_visual_language.py")
CHK = str(ROOT / "scripts" / "check_vl_contract.py")
SD, LD = specs_dir_with(), Path(tempfile.mkdtemp(prefix="vllangs_", dir=WORK))
ENVG = {"VL_SPECS_DIR": str(SD), "VL_LANGS_DIR": str(LD)}
r = run([GEN, "mosaic", "--like", "tally", "--specs-dir", str(SD), "--langs-dir", str(LD)], script=True)
check(r.returncode == 0 and (SD / "mosaic.py").is_file() and (LD / "mosaic.py").is_file()
      and re.search(r"NEXT: .*python3 \S*check_vl_contract\.py mosaic", r.stdout),
      "the generator writes the manifest and the module and prints the next command ({})".format((r.stdout + r.stderr)[-200:]))
_gen = vl_specs.load(SD, drafts=True).get("mosaic") if (SD / "mosaic.py").is_file() else None
check("mosaic" not in vl_specs.load(SD) and "mosaic" in vl_specs.DRAFTS,
      "an ordinary load leaves the draft out and names it in DRAFTS")
check(bool(_gen) and _gen["display"]["zh"].startswith("FILL:") and _gen["painters"] == {"ground": "_ground_mosaic", "card": "_card_mosaic"}
      and _gen["look"]["palette"] is _gen["grounds"]["light"]["palette"],
      "the written manifest loads, its Chinese hint intact, its light palette one object")
r = run([CHK, "mosaic"], ENVG, script=True)
_out = r.stdout + r.stderr
for _path in ("display.en", "display.zh", "rationale", "offer.en[0]", "grounds.light.palette.ground", "grounds.light.label",
              "look.fonts.both.display", "samples.copy"):
    check("mosaic: {} is not filled".format(_path) in _out, "check_vl_contract names the unfilled {} ({})".format(_path, _out[-160:]))
check(r.returncode == 1 and "Traceback" not in _out, "an untouched draft is reported, not crashed on")
r = run("import deckkit as dk, visual_languages as vl; prs = dk.blank_deck(13.333, 7.5); k = vl.use('tally', prs); "
        "k.cover(k.new_slide(), title='Fix it together'); print('ok')", ENVG)
check(r.returncode == 0 and "ok" in r.stdout, "an untouched draft leaves tally working ({})".format(r.stderr[-160:]))
for _args, _why, _word in ((["tally"], "an existing language", "already"), (["Pebble"], "an uppercase name", "lowercase"),
                           (["my-lang"], "a hyphen", "lowercase"), (["9lives"], "a leading digit", "lowercase"),
                           (["mosaic2", "--like", "editorial"], "an image-led model", "image-led"),
                           (["mosaic3", "--like", "nosuch"], "an unknown model", "nosuch")):
    r = run([GEN] + _args + ["--specs-dir", str(SD), "--langs-dir", str(LD)], script=True)
    # the message must say WHY — python's own exit 2 for a missing script passed this check vacuously at first
    check(r.returncode == 2 and _word in (r.stdout + r.stderr) and "new_visual_language" in (r.stdout + r.stderr)
          and (_args[0] == "tally" or not (SD / (_args[0] + ".py")).exists()),
          "the generator refuses {}, saying why ({} {})".format(_why, r.returncode, (r.stdout + r.stderr)[-120:]))
# end to end: decide every FILL (here: the values of the mosaic fixture) …
_want = mosaic_spec()


def _at(o, path):
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        o = o[int(part[1:-1])] if part.startswith("[") else o[part]
    return o


def _fill(o, path=""):
    if isinstance(o, dict):
        return {k: _fill(v, "{}.{}".format(path, k) if path else k) for k, v in o.items()}
    if isinstance(o, list):
        return [_fill(v, "{}[{}]".format(path, i)) for i, v in enumerate(o)]
    if isinstance(o, tuple):
        return tuple(_fill(v, "{}[{}]".format(path, i)) for i, v in enumerate(o))
    return copy.deepcopy(_at(_want, path)) if isinstance(o, str) and o.startswith("FILL:") else o
if _gen:
    _filled = _fill(_gen)
    for _k in ("extras", "derived", "samples"):
        _filled[_k] = copy.deepcopy(_want[_k])
    _filled["look"]["palette"] = _filled["grounds"]["light"]["palette"]
    _write_spec(SD, _filled)
r = run([CHK, "mosaic"], ENVG, script=True)
_out = r.stdout + r.stderr
check(r.returncode == 1 and _out.count("is still a stub") == 7 and "scripts/vl_langs/mosaic.py" in _out,
      "with the manifest decided, the seven stub pages are named ({})".format(_out[-200:]))
# … then compose (here: borrow tally's compositions) — what remains is the shipping list, each item named
_mod = (LD / "mosaic.py").read_text(encoding="utf-8") if (LD / "mosaic.py").is_file() else ""
check("vn.stub(" in _mod, "the module drafts one stub per page")
(LD / "mosaic.py").write_text(_mod + "\n\nfor _p in PAGES:      # composed: here, tally's compositions\n"
                              "    vn.register('mosaic', _p, vn.ALTS[('tally', _p)])(vn.COMPOSERS['tally'][_p])\n",
                              encoding="utf-8")
r = run([CHK, "mosaic"], ENVG, script=True)
_fails = [l for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("FAIL")]
check(_fails and all(any(w in l for w in ("bundled sample", "fingerprint", "sigs.py --example", "table row", "gallery"))
                     for l in _fails),
      "composed, only the shipping steps remain — samples, scaffold, docs row, gallery ({})".format(_fails[:3]))

# ── Task 4: --describe prints a language's card and an example that runs as printed ──
VLPY = str(ROOT / "scripts" / "visual_languages.py")
from pptx import Presentation as _P
for _n, _sp in SHIPPED.items():
    r = run([VLPY, "--describe", _n], script=True)
    _card = r.stdout
    check(r.returncode == 0 and all(h in _card for h in ("grounds:", "pages:", "extras:", "derived words:",
                                                          "offered for:", "fonts:", "\nexample (")),
          "--describe {}: every section of the card is printed ({})".format(_n, (r.stdout + r.stderr)[-120:]))
    check(all(x + "=" in _card for x in _sp["extras"]), "--describe {}: every extra is listed by name".format(_n))
    _code = _card.split("\nexample (", 1)[-1].split("\n", 1)[-1] if "\nexample (" in _card else ""
    _wd = Path(tempfile.mkdtemp(prefix="desc_", dir=WORK))
    rr = subprocess.run([sys.executable, "-c", _code], cwd=_wd, capture_output=True, text=True, timeout=600)
    _decks = list(_wd.glob("*.pptx"))
    check(rr.returncode == 0 and len(_decks) == 1 and len(_P(str(_decks[0])).slides) == 4,
          "--describe {}: its example runs as printed and saves a 4-page deck ({})".format(_n, rr.stderr[-160:]))
r = run([VLPY, "--describe", "nosuch"], script=True)
check(r.returncode == 2 and "tally" in r.stderr, "--describe of an unknown name lists the registered languages")
r = run([VLPY, "--describe", "mosaic"], ENV16, script=True)
check(r.returncode == 0 and "not ready" in r.stdout and "vl_langs/mosaic.py" in r.stdout and "\nexample (" not in r.stdout,
      "--describe of a language with no code says what to write, and prints no example ({})".format((r.stdout + r.stderr)[-160:]))
SDd, LDd = specs_dir_with(), Path(tempfile.mkdtemp(prefix="vllangs_", dir=WORK))
run([GEN, "pebble", "--specs-dir", str(SDd), "--langs-dir", str(LDd)], script=True)
r = run([VLPY, "--describe", "pebble"], {"VL_SPECS_DIR": str(SDd), "VL_LANGS_DIR": str(LDd)}, script=True)
check(r.returncode == 0 and "draft" in r.stdout and "check_vl_contract.py pebble" in r.stdout,
      "--describe of a draft says it is a draft and how to see what to decide ({})".format((r.stdout + r.stderr)[-160:]))

# ── Task 5: sigs.py places by CHARACTER offsets (M1); --in / --ground are checked when typed (M8) ──
import sigs
sigs.EXAMPLES["probe_cjk"] = ('s = dk.add_slide(prs)\n'
                              't = "中文标题"; dk.text(s, 0.8, 0.6, 6.0, 1.0, [[(t, 24, dk.RGBColor(0x22, 0x22, 0x22), True, False)]])\n')
try:
    _placed = sigs.placed_example("probe_cjk", "tally"); _err = None
except Exception as e:
    _placed, _err = "", "{}: {}".format(type(e).__name__, e)
try:
    compile(_placed, "<placed>", "exec"); _compiles = True
except SyntaxError:
    _compiles = False
check(_err is None and _compiles and "dk.text(s, x, y, w, h, [[(t," in _placed and '"中文标题"' in _placed,
      "a scaffold with Chinese before its call is placed with its arguments intact ({})".format(_err or _placed[-140:]))
del sigs.EXAMPLES["probe_cjk"]
SIGS = str(ROOT / "scripts" / "sigs.py")
for _args, _word in ((["timeline", "--example", "--ground", "night"], "--ground goes with --in"),
                     (["timeline", "--example", "--in", "nosuch"], "tally"),
                     (["timeline", "--example", "--in", "tally", "--ground", "nosuch"], "night")):
    r = run([SIGS] + _args, script=True)
    check(r.returncode == 2 and _word in r.stderr, "sigs.py {} is refused when typed, saying why ({} {})".format(
        " ".join(_args), r.returncode, (r.stdout + r.stderr)[-120:]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
