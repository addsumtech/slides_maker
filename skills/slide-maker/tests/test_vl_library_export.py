#!/usr/bin/env python3
"""vl_library_export.py writes the library page's data and images (served from slides.addsum.top/languages/, shown in the home page's #languages section) from the registry.

WHAT IS HELD. The page must never need a hand edit when a language is added, so the exporter is held to: one entry per
registry language in manifest order; stats counted from the registry, never typed; every image the JSON names exists;
nothing written outside <site>/languages/; a language that left the skill leaves the page (its media too); `added_at`
survives a re-export and a new id gets the export date; `--check` fails on a stale page and names the language. The
render path (`--only ink`) writes seven page images per ground, each a real 16:9 JPEG 960px wide.

Run: python3 tests/test_vl_library_export.py   (the render half needs LibreOffice; without it, it says SKIP)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import vl_contract as ct  # noqa: E402
import vl_specs  # noqa: E402

EXPORT = SCRIPTS / "vl_library_export.py"
REG = vl_specs.load()
PAGES = ("cover", "section", "image_text", "points", "quote", "data", "closing")
ok, bad, skipped = [], [], []


def check(cond, why):
    (ok if cond else bad).append(why)


def run(*args, env=None):
    r = subprocess.run([sys.executable, str(EXPORT)] + [str(a) for a in args], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def tree(site):
    return sorted(str(p.relative_to(site)) for p in Path(site).rglob("*") if p.is_file())


with tempfile.TemporaryDirectory() as td:
    site = Path(td) / "site"
    site.mkdir()
    (site / "index.html").write_text("<!doctype html><title>gallery</title>", encoding="utf-8")
    (site / "sitemap.xml").write_text("<urlset/>", encoding="utf-8")
    before = {p: (site / p).read_bytes() for p in ("index.html", "sitemap.xml")}
    (site / "languages" / "media" / "ghost").mkdir(parents=True)
    (site / "languages" / "media" / "ghost" / "sample-light.jpg").write_bytes(b"x")

    code, out = run("--site", site, "--no-render", "--today", "2026-10-17")
    check(code == 0, "a --no-render export runs (exit {}: {})".format(code, out.strip()[-300:]))
    lib_p = site / "languages" / "library.json"
    lib = json.loads(lib_p.read_text(encoding="utf-8")) if lib_p.exists() else {}
    langs = lib.get("languages", [])
    if not langs:                      # nothing to inspect: say so instead of tracing back on the first lookup
        print("  FAIL the export wrote no languages ({})\n[test_vl_library_export] FAILED: 1 problem(s)".format(
            out.strip()[-300:]))
        sys.exit(1)

    # ── the data is the registry's ──
    check(lib.get("schema") == 1, "library.json says schema 1 ({})".format(lib.get("schema")))
    check([x.get("id") for x in langs] == list(REG), "one entry per registry language, in manifest order ({})".format(
        [x.get("id") for x in langs]))
    want = {"languages": len(REG), "grounds": sum(len(s["grounds"]) for s in REG.values()), "page_types": len(PAGES),
            "components": len(ct.TIER1)}
    check(lib.get("stats") == want, "stats are counted from the registry ({} vs {})".format(lib.get("stats"), want))
    check([p.get("id") for p in lib.get("page_types", [])] == list(PAGES),
          "the seven page types, in the page's reading order")
    for x in langs:
        s = REG.get(x.get("id"), {})
        check(x.get("blurb") == s.get("blurb"), "{}: the blurb is the manifest's".format(x.get("id")))
        check(x.get("name") == s.get("display"), "{}: the names are the manifest's display names".format(x.get("id")))
        check([g.get("id") for g in x.get("grounds", [])] == list(s.get("grounds", {})),
              "{}: every ground, in the manifest's order".format(x.get("id")))
        check("ground=" not in x["grounds"][0].get("python", "") and all(
            'ground="{}"'.format(g["id"]) in g.get("python", "") for g in x["grounds"][1:]),
            "{}: each ground's python line asks for that ground".format(x.get("id")))
        check(x["id"] in x.get("usage", {}).get("prompt", {}).get("en", "") and
              s["display"]["zh"] in x.get("usage", {}).get("prompt", {}).get("zh", ""),
              "{}: the copy-prompt sentence names the language in both scripts".format(x.get("id")))
        check(x.get("best_for", {}).get("en") and x.get("best_for", {}).get("zh"),
              "{}: best-for tags in both scripts".format(x.get("id")))
    names = set()
    for x in langs:
        for g in x.get("grounds", []):
            names.add(g.get("sample"))
            check(bool(g.get("sample")) and (site / "languages" / g["sample"]).is_file(),
                  "{}/{}: its sample sheet is on disk ({})".format(x["id"], g.get("id"), g.get("sample")))
            check(g.get("pages") == {}, "{}/{}: --no-render on an empty site lists no page images ({})".format(
                x["id"], g.get("id"), g.get("pages")))
    check(len(names) == want["grounds"], "every ground has its own sample sheet ({} of {})".format(len(names), want["grounds"]))

    # ── isolation ──
    check(all(p.startswith("languages/") for p in tree(site) if p not in before),
          "nothing written outside languages/ ({})".format([p for p in tree(site) if not p.startswith("languages/")
                                                           and p not in before]))
    check(all((site / p).read_bytes() == b for p, b in before.items()), "the gallery's files are untouched")
    check(not (site / "languages" / "media" / "ghost").exists(), "a language no longer in the skill leaves the page's media")

    # ── NEW: the first export marks nobody new; a later id gets the export date ──
    check(lib.get("baseline") == "2026-10-17" and all(x.get("added_at") == "2026-10-17" for x in langs),
          "the first export sets the baseline and dates every language to it ({}, {})".format(
              lib.get("baseline"), sorted({x.get("added_at") for x in langs})))
    # NEW is decided by WHO was there at launch, not by comparing dates: a language added on the launch day itself
    # would otherwise never wear NEW (added_at == baseline), and a clock ahead of UTC could hide one for hours
    check(lib.get("baseline_ids") == list(REG), "the first export records which languages the page launched with ({})".format(
        lib.get("baseline_ids")))
    # a file under media/ that library.json does not name is stale too (only an export removes it)
    (site / "languages" / "media" / "orphan").mkdir(parents=True)
    (site / "languages" / "media" / "orphan" / "a.jpg").write_bytes(b"x")
    code, out = run("--site", site, "--check")
    check(code == 1 and "orphan media file: media/orphan/a.jpg" in out,
          "--check names a media file library.json does not list ({}: {})".format(code, out.strip()[-200:]))
    # a page whose cards have no rendered pages is not ready to publish: --check says so, by language and ground
    code, out = run("--site", site, "--check")
    check(code == 1 and all("no page renders: {} ({} ground)".format(n, g) in out for n in (langs[0]["id"], langs[-1]["id"])
                            for g in REG[n]["grounds"]),
          "--check after --no-render names every unrendered ground ({}: {})".format(code, out.strip()[-300:]))

    lib["languages"][0]["added_at"] = "2026-01-02"
    gone = lib["languages"].pop(1)
    lib["languages"][2]["blurb"] = {"en": "edited by hand", "zh": "手改"}
    lib_p.write_text(json.dumps(lib), encoding="utf-8")
    code, out = run("--site", site, "--check")
    check(code == 1 and gone["id"] in out and lib["languages"][2]["id"] in out,
          "--check fails on a stale page and names each language ({}: {})".format(code, out.strip()[-300:]))
    code, out = run("--site", site, "--no-render", "--today", "2026-11-20")
    lib2 = json.loads(lib_p.read_text(encoding="utf-8"))
    by = {x["id"]: x for x in lib2["languages"]}
    check(by[langs[0]["id"]]["added_at"] == "2026-01-02", "a re-export keeps added_at")
    check(by[gone["id"]]["added_at"] == "2026-11-20", "a language new to the page is dated to the export")
    check(lib2["baseline"] == "2026-10-17", "a re-export keeps the baseline")
    check(lib2.get("baseline_ids") == list(REG), "a re-export keeps the launch set ({})".format(lib2.get("baseline_ids")))
    check(not (site / "languages" / "media" / "orphan").exists(), "the export removes the orphan media file")
    # a library.json from before baseline_ids existed: the launch set is the languages dated on or before the baseline
    legacy = dict(lib2)
    legacy.pop("baseline_ids", None)
    lib_p.write_text(json.dumps(legacy), encoding="utf-8")
    run("--site", site, "--no-render", "--today", "2026-11-21")
    lib_legacy = json.loads(lib_p.read_text(encoding="utf-8"))
    check(lib_legacy.get("baseline_ids") == [n for n in REG if n != gone["id"]],
          "an old library.json gets its launch set from the dates, without the language added later ({})".format(
              lib_legacy.get("baseline_ids")))
    check(by[langs[3]["id"]]["blurb"] == REG[langs[3]["id"]]["blurb"], "a re-export restores the manifest's words")
    check("added" in out and gone["id"] in out, "the export says which language is new to the page ({})".format(
        out.strip()[-200:]))

    # ── refusals ──
    code, out = run("--site", site / "index.html", "--no-render")
    check(code == 2 and "folder" in out, "a site path that is a file is refused ({}: {})".format(code, out.strip()[-160:]))
    code, out = run("--site", site, "--only", "nosuch")
    check(code == 2 and "nosuch" in out, "an unknown --only id is refused, naming it ({}: {})".format(code, out.strip()[-160:]))
    stray = Path(td) / "not-a-site"
    stray.mkdir()
    code, out = run("--site", stray, "--no-render")
    check(code == 2 and "index.html" in out and not (stray / "languages").exists(),
          "a folder that is not the site (no index.html) is refused and left untouched ({}: {})".format(
              code, out.strip()[-160:]))
    # a manifest the contract refuses is named, not a bare KeyError (the contract normally catches it first)
    specs = Path(td) / "specs-noblurb"
    shutil.copytree(SCRIPTS / "vl_specs", specs, ignore=shutil.ignore_patterns("__pycache__"))
    victim = specs / "tally.py"
    txt = victim.read_text(encoding="utf-8")
    i = txt.index(" 'blurb': ")
    victim.write_text(txt[:i] + txt[txt.index(" 'offer': ", i):], encoding="utf-8")
    code, out = run("--site", site, "--no-render", env=dict(os.environ, VL_SPECS_DIR=str(specs)))
    check(code == 2 and "tally" in out and "blurb" in out and "Traceback" not in out,
          "a manifest without a blurb is refused by name ({}: {})".format(code, out.strip()[-200:]))

    # ── the render path: seven pages per ground ──
    if not (shutil.which("soffice") or shutil.which("libreoffice") or Path("/Applications/LibreOffice.app").exists()):
        skipped.append("no LibreOffice — the render half of the exporter was not run")
    else:
        code, out = run("--site", site, "--only", "ink", "--today", "2026-11-20")
        check(code == 0, "--only ink renders (exit {}: {})".format(code, out.strip()[-400:]))
        lib3 = json.loads(lib_p.read_text(encoding="utf-8"))
        ink = {x["id"]: x for x in lib3["languages"]}["ink"]
        from PIL import Image
        for g in ink["grounds"]:
            check(list(g.get("pages", {})) == list(PAGES), "ink/{}: all seven pages listed ({})".format(
                g["id"], list(g.get("pages", {}))))
            for page, rel in g.get("pages", {}).items():
                f = site / "languages" / rel
                try:
                    with Image.open(f) as im:
                        good = im.format == "JPEG" and im.size[0] == 960 and abs(im.size[0] / im.size[1] - 16 / 9) < 0.02
                        size = im.size
                except Exception as e:      # noqa: BLE001 — any unreadable file is the finding
                    good, size = False, e
                check(good, "ink/{}/{}: a 960px 16:9 JPEG ({})".format(g["id"], page, size))
            check(bool(g.get("render_fp")), "ink/{}: the render fingerprint is recorded".format(g["id"]))
        others = [x for x in lib3["languages"] if x["id"] != "ink"]
        check(all(g.get("pages") == {} for x in others for g in x["grounds"]), "--only renders only the named language")
        code, out = run("--site", site, "--check")
        check(code == 1 and "no page renders: ink " not in out and "no page renders: {} ".format(others[0]["id"]) in out,
              "after --only ink, --check names the languages still unrendered and not ink ({}: {})".format(
                  code, out.strip()[-300:]))
        code, out = run("--site", site, "--no-render", "--today", "2026-11-21")
        lib4 = json.loads(lib_p.read_text(encoding="utf-8"))
        ink4 = {x["id"]: x for x in lib4["languages"]}["ink"]
        check(all(list(g["pages"]) == list(PAGES) and g.get("render_fp") for g in ink4["grounds"]),
              "--no-render keeps the renders already on disk listed")
        # the render fingerprint covers everything a render draws — pictures, textures, theme — not the slide XML only:
        # a re-shot photo or a changed grain tile leaves every slide XML byte the same
        import zipfile
        import visual_languages as vl
        import vl_library_export as vx
        d1, d2 = vx.demo_deck("ink", "light", Path(td) / "fp1.pptx"), vx.demo_deck("ink", "light", Path(td) / "fp2.pptx")
        check(vx.deck_fingerprint(d1) == vx.deck_fingerprint(d2), "two builds of one demo deck fingerprint the same")
        swapped = Path(td) / "fp3.pptx"
        with zipfile.ZipFile(d1) as zin, zipfile.ZipFile(swapped, "w", zipfile.ZIP_DEFLATED) as zout:
            media = [n for n in zin.namelist() if n.startswith("ppt/media/")]
            for n in zin.namelist():
                data = zin.read(n)
                zout.writestr(n, data + b"\0" if media and n == media[0] else data)
        check(bool(media) and vx.deck_fingerprint(swapped) != vx.deck_fingerprint(d1),
              "a changed picture changes the render fingerprint ({} media parts)".format(len(media)))
        check(vl.sample_fingerprint(swapped) == vl.sample_fingerprint(d1),
              "(and the slide-XML hash alone would not have seen it — why the fingerprint changed)")
        # renders made from an older demo deck are stale even when every file is present
        ink4["grounds"][1]["render_fp"] = "0" * 64
        lib_p.write_text(json.dumps(lib4), encoding="utf-8")
        code, out = run("--site", site, "--check")
        check(code == 1 and "stale page renders: ink ({} ground)".format(ink4["grounds"][1]["id"]) in out,
              "--check names renders that no longer match the demo deck ({}: {})".format(code, out.strip()[-200:]))

        # ── a whole page: every ground rendered (ink's real renders stand in for the others' files, each carrying
        # the fingerprint of its OWN demo deck) — --check passes; the same files listed by a library.json rebuilt with
        # --no-render (no fingerprints) must not pass as fresh ──
        lib5 = json.loads(lib_p.read_text(encoding="utf-8"))
        ink5 = {x["id"]: x for x in lib5["languages"]}["ink"]
        ink5["grounds"][1]["render_fp"] = vx._fingerprint("ink", ink5["grounds"][1]["id"])
        for x in lib5["languages"]:
            if x["id"] == "ink":
                continue
            for g in x["grounds"]:
                g["pages"] = {}
                for page in PAGES:
                    rel = "media/{}/{}/{}.jpg".format(x["id"], g["id"], page)
                    (site / "languages" / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(site / "languages" / ink5["grounds"][0]["pages"][page], site / "languages" / rel)
                    g["pages"][page] = rel
                g["render_fp"] = vx._fingerprint(x["id"], g["id"])
        lib_p.write_text(json.dumps(lib5), encoding="utf-8")
        code, out = run("--site", site, "--check")
        check(code == 0, "--check passes on a fully rendered page (exit {}: {})".format(code, out.strip()[-300:]))
        lib_p.unlink()
        code, out = run("--site", site, "--no-render", "--today", "2026-10-18")
        code, out = run("--site", site, "--check")
        check(code == 1 and "no render fingerprint: ink" in out and "no page renders" not in out,
              "renders listed without a fingerprint are not called fresh ({}: {})".format(code, out.strip()[-300:]))

for line in ok:
    print("  ok   " + line)
for line in skipped:
    print("  SKIP " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed, {} skipped".format(len(ok), len(bad), len(skipped)))
if bad:
    print("[test_vl_library_export] FAILED: {} problem(s)".format(len(bad)))
    sys.exit(1)
print("[test_vl_library_export] ok")
