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

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
