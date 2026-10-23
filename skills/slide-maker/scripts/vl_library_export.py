#!/usr/bin/env python3
"""vl_library_export — write the visual-language library's data and images (served from slides.addsum.top/languages/,
shown in the home page's #languages section).

    python3 scripts/vl_library_export.py --site ~/code_project/slides_maker-site               # data + images
    python3 scripts/vl_library_export.py --site … --no-render                                  # data + sample sheets
    python3 scripts/vl_library_export.py --site … --only ink                                   # render one language
    python3 scripts/vl_library_export.py --site … --check                                      # exit 1 if stale

The library section (site repo: index.html and cn/index.html, #languages, with languages/library.js) renders whatever
library.json lists, so a new language reaches
it by re-running this — nothing on the site is edited by hand. Everything comes from the manifests (scripts/vl_specs)
and the registry; the stats are counted, never typed.

Writes ONLY under <site>/languages/: library.json, media/<id>/sample-<ground>.jpg (the bundled four-page sheet) and
media/<id>/<ground>/<page>.jpg (the seven page types rendered from ONE shared demo text, 960px JPEG). A file under
languages/media that the new library.json does not name is removed — a language that left the skill leaves the page.

added_at is the date a language first appeared in an export and survives re-exports; `baseline` is the first export's
date. The page marks NEW only a language added AFTER the baseline (and within 30 days): the first fifteen were all
under a month old on the day the page launched, and a page where every card says NEW says nothing.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vl_contract as ct  # noqa: E402
import deckkit as dk  # noqa: E402
import visual_languages as vl  # noqa: E402

PAGES = ("cover", "section", "image_text", "points", "quote", "data", "closing")
PAGE_NAMES = {"cover": ("Cover", "封面"), "section": ("Section", "章节页"), "image_text": ("Image & text", "图文页"),
              "points": ("Points", "要点页"), "quote": ("Quote", "引语页"), "data": ("Data", "数据页"),
              "closing": ("Closing", "结尾页")}
PICTURES_ZH = {"photos": "照片", "illustrations": "插画"}
WIDTH = 960

# ONE demo text for every language, so languages compare on identical words. The words for the four sample pages are
# the bundled samples' own (visual_languages._SAMPLE_COPY); the other three pages are added here. An illustration-led
# language gets the garden text on the bundled watercolours: repair-café words over garden paintings misstate the look.
_EXTRA = {
    "photo": dict(subtitle="One evening a month, in the community hall", sec_kicker="How an evening runs",
                  sec_title="Sign in, sit down, fix it together", caption="The tool table before the doors open",
                  pts_kicker="Three steps", pts_title="How every repair begins",
                  items=[("Sign in", "Say what is broken"), ("Sit down", "A volunteer joins you"),
                         ("Fix it", "You hold the screwdriver")],
                  close_title="Bring something broken", close_line="See you at the next session"),
    "watercolour": dict(subtitle="What grows in a few pots, season by season", sec_kicker="Getting started",
                        sec_title="Start with one pot and a sunny rail", caption="The few tools a balcony needs",
                        pts_kicker="Three habits", pts_title="What a balcony garden asks for",
                        items=[("Light", "A sunny rail or sill"), ("Water", "A little, every evening"),
                               ("Patience", "A season to grow")],
                        close_title="Start with one pot", close_line="A window sill will do"),
}


class ExportError(Exception):
    """A refusal the maintainer must act on; main() prints it and exits 2."""


def demo_pages(name):
    """[(page, fields, image path or None)] — the seven pages of `name`'s demo deck, pictures only on the pages the
    language draws a picture on."""
    spec = vl.REGISTRY[name]
    kind = "watercolour" if spec["offer"].get("pictures") == "illustrations" else "photo"
    T, X = vl._SAMPLE_COPY[kind], _EXTRA[kind]
    imgs = [str(vl.ASSETS / p) for p in vl.SAMPLE_IMAGES[kind]]
    pages = [
        ("cover", dict(kicker=T["kicker"], title=T["title"], subtitle=X["subtitle"]),
         imgs[:3] if name == "collage" else imgs[0]),
        ("section", dict(number="01", kicker=X["sec_kicker"], title=X["sec_title"]), imgs[4]),
        ("image_text", dict(kicker=T["kicker"], title=T["it_title"], body=T["body"], caption=X["caption"]), imgs[1]),
        ("points", dict(kicker=X["pts_kicker"], title=X["pts_title"], items=X["items"]), imgs[3]),
        ("quote", dict(quote=T["quote"], attribution=T["attr"]), imgs[2]),
        ("data", dict(number=T["num"], label=T["label"], note=T["note"]), imgs[3]),
        ("closing", dict(title=X["close_title"], line=X["close_line"]), imgs[4]),
    ]
    assert [p for p, _f, _i in pages] == list(PAGES)
    return [(p, f, i if p in spec["image_pages"] else None) for p, f, i in pages]


def demo_deck(name, ground, out_pptx):
    """Build the seven-page demo deck of `name` on `ground`; a page the language refuses raises naming both."""
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use(name, prs, ground=ground)
    for page, fields, image in demo_pages(name):
        try:
            getattr(k, page)(k.new_slide(), image=image, **fields)
        except Exception as e:  # noqa: BLE001 — every refusal is reported the same way, with its own words
            raise ExportError("{}.{} ({} ground) refused the shared demo text: {}: {} — the page set must be whole, "
                              "so nothing was written for it".format(name, page, ground, type(e).__name__, e)) from None
    out_pptx = Path(out_pptx)
    out_pptx.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_pptx))
    return out_pptx


def deck_fingerprint(pptx):
    """sha256 of everything in a built deck that a render draws — slides, their relationships, every picture and
    texture (ppt/media), theme, masters and layouts — i.e. every part but docProps. A slide-XML-only hash
    (visual_languages.sample_fingerprint) stays the same when a photo is re-shot or a grain tile changes, so renders
    made from the old pictures would have been called fresh."""
    import hashlib
    import zipfile
    h = hashlib.sha256()
    with zipfile.ZipFile(str(pptx)) as z:
        for n in sorted(n for n in z.namelist() if not n.startswith("docProps/")):
            h.update(n.encode("utf-8") + b"\0" + z.read(n) + b"\0")
    return h.hexdigest()


def _fingerprint(name, ground):
    with tempfile.TemporaryDirectory() as td:
        return deck_fingerprint(demo_deck(name, ground, Path(td) / "demo.pptx"))


def _contract_problems():
    """Every manifest problem the contract names — refused before anything is read, so a manifest without a blurb is a
    named problem, not a KeyError halfway through the export."""
    return [p for s in vl.REGISTRY.values() for p in ct.validate(s)]


def _skill_version():
    f = HERE.parent / "VERSION"
    return f.read_text(encoding="utf-8").strip() if f.exists() else None


def _inside(lang_dir, p):
    """`p`, refused unless it resolves inside languages/ — the exporter never writes anywhere else on the site."""
    p = Path(p)
    if lang_dir.resolve() not in (p.resolve(), *p.resolve().parents):
        raise ExportError("refusing to write {} — outside {}".format(p, lang_dir))
    return p


def _entry(name, prev, lang_dir, today, rendered):
    """The library.json entry for one language. `rendered`: {ground: render_fp} rendered in this run."""
    s = vl.REGISTRY[name]
    old = {g["id"]: g for g in (prev or {}).get("grounds", [])}
    disp = s["display"]
    pics = s["offer"].get("pictures")
    best = ({"en": [pics], "zh": [PICTURES_ZH.get(pics, pics)]} if pics
            else {"en": list(s["offer"]["en"]), "zh": list(s["offer"]["zh"])})
    grounds = []
    for gid, gd in s["grounds"].items():
        pal, roles = gd["palette"], gd["roles"]
        pages = {p: "media/{}/{}/{}.jpg".format(name, gid, p) for p in PAGES}
        pages = {p: r for p, r in pages.items() if (lang_dir / r).is_file()}
        fp = rendered.get(gid) or (old.get(gid, {}).get("render_fp") if pages else None)
        label = {"en": gd["label"], "zh": gd["label_zh"]}
        light = gid == "light"
        grounds.append({
            "id": gid, "label": label, "dark": bool(gd["dark"]),
            "swatches": {"ground": pal["ground"], "ink": pal["ink"], "mute": pal["mute"], "panel": pal["panel"],
                         "accents": list(pal["accents"]), "text_accents": list(pal["text_accents"]),
                         "series": list(roles["series"])},
            "sample": "media/{}/sample-{}.jpg".format(name, gid),
            "pages": pages, "render_fp": fp,
            "python": 'k = vl.use("{}", prs)'.format(name) if light else
                      'k = vl.use("{}", prs, ground="{}")'.format(name, gid),
            "prompt": {"en": "Use the {} ({}) visual language{} for this deck.".format(
                           name, disp["en"], "" if light else ", on its {} ground,".format(gd["label"])),
                       "zh": "用 {}（{}）视觉语言{}做这份 PPT。".format(
                           name, disp["zh"], "" if light else "的{}".format(gd["label_zh"]))},
        })
    ea = s["look"]["ea"]
    return {
        "id": name, "order": s["order"], "kind": s["kind"],
        "added_at": (prev or {}).get("added_at") or today,
        "name": dict(disp), "blurb": dict(s["blurb"]), "best_for": best,
        "grounds": grounds,
        "fonts": {"both": dict(s["look"]["fonts"]["both"]), "mac": dict(s["look"]["fonts"]["mac"]),
                  "cjk": {role: dict(dk.EA_FACES["han"][ea[role]], kind=ea[role]) for role in ("display", "body")}},
        "image_pages": list(s["image_pages"]),
        "extras": [{"name": x, "pages": d["pages"] if d["pages"] == "any" else list(d["pages"]), "takes": d["takes"]}
                   for x, d in s["extras"].items()],
        "derived": [{"id": d["id"], "what": d["what"]} for d in s["derived"]],
        "usage": {"prompt": grounds[0]["prompt"], "python": grounds[0]["python"]},
    }


def _baseline_ids(prev):
    """The ids the page launched with (the first export) — the page marks NEW only a language NOT among them. Kept
    from the previous library.json; one written before this field existed gives it from its dates (on or before the
    baseline); the first export takes every language there is."""
    if not prev:
        return list(vl.REGISTRY)
    if isinstance(prev.get("baseline_ids"), list):
        return list(prev["baseline_ids"])
    base = prev.get("baseline")
    return [x["id"] for x in prev.get("languages", []) if base and x.get("added_at") and x["added_at"] <= base]


def build_library(lang_dir, prev, today, rendered=None):
    """The whole library.json as a dict (writes nothing). `prev`: the previous library.json, or None."""
    rendered = rendered or {}
    prev_by = {x["id"]: x for x in (prev or {}).get("languages", [])}
    return {
        "schema": 1,
        "generated": today,
        "baseline": (prev or {}).get("baseline") or today,
        "baseline_ids": _baseline_ids(prev),
        "skill_version": _skill_version(),
        "stats": {"languages": len(vl.REGISTRY), "grounds": sum(len(s["grounds"]) for s in vl.REGISTRY.values()),
                  "page_types": len(PAGES), "components": len(ct.TIER1)},
        "page_types": [{"id": p, "name": {"en": PAGE_NAMES[p][0], "zh": PAGE_NAMES[p][1]}} for p in PAGES],
        "languages": [_entry(n, prev_by.get(n), lang_dir, today, rendered.get(n, {})) for n in vl.REGISTRY],
    }


def _site_dirs(site):
    site = Path(site).expanduser()
    if not site.is_dir():
        raise ExportError("--site {} is not a folder — pass the site repo's folder (the one holding index.html)".format(
            site))
    if not (site / "index.html").is_file():
        raise ExportError("--site {} has no index.html — pass the site repo's folder (slides_maker-site); nothing was "
                          "written".format(site))
    lang_dir = site / "languages"
    if lang_dir.is_symlink():
        raise ExportError("{} is a symlink — the exporter writes only inside the site".format(lang_dir))
    return site, lang_dir


def _load_prev(lang_dir):
    f = lang_dir / "library.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ExportError("{} is not valid JSON ({}) — fix it by hand (git checkout it); deleting it resets every "
                          "language's added_at and the NEW baseline".format(
            f, e)) from None


def _render(name, ground, lang_dir, scratch):
    """Render `name` on `ground` into media/<name>/<ground>/<page>.jpg; returns the deck's fingerprint."""
    from PIL import Image
    deck = demo_deck(name, ground, scratch / "{}-{}.pptx".format(name, ground))
    out = scratch / "render-{}-{}".format(name, ground)
    r = subprocess.run([sys.executable, str(HERE / "render_deck.py"), str(deck), str(out)],
                       capture_output=True, text=True)
    pngs = [out / "slide{:02d}.png".format(i) for i in range(1, len(PAGES) + 1)]
    missing = [p.name for p in pngs if not p.is_file()]
    if missing:
        raise ExportError("{} ({} ground): render_deck.py produced no {} (exit {}):\n{}".format(
            name, ground, missing, r.returncode, (r.stdout + r.stderr).strip()[-1200:]))
    dest = _inside(lang_dir, lang_dir / "media" / name / ground)
    dest.mkdir(parents=True, exist_ok=True)
    for page, png in zip(PAGES, pngs):
        with Image.open(png) as im:
            im = im.convert("RGB")
            h = round(im.size[1] * WIDTH / im.size[0])
            im.resize((WIDTH, h), Image.LANCZOS).save(_inside(lang_dir, dest / (page + ".jpg")), "JPEG", quality=84,
                                                      optimize=True, progressive=True)
    return deck_fingerprint(deck)


def _copy_samples(lang_dir):
    for name, s in vl.REGISTRY.items():
        for gid in s["grounds"]:
            src = vl.ASSETS / "samples" / (vl._sample_stem(name, gid) + ".jpg")
            if not src.is_file():
                raise ExportError("{} ({} ground) has no bundled sample sheet {} — build it first "
                                  "(visual_languages.py --sample … --refresh-bundled)".format(name, gid, src))
            dst = _inside(lang_dir, lang_dir / "media" / name / "sample-{}.jpg".format(gid))
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)


def _prune(lang_dir, lib):
    """Remove every file under languages/media the library does not name (and the folders left empty)."""
    named = {g["sample"] for x in lib["languages"] for g in x["grounds"]}
    named |= {r for x in lib["languages"] for g in x["grounds"] for r in g["pages"].values()}
    media = lang_dir / "media"
    if not media.is_dir():
        return []
    gone = []
    for f in sorted(media.rglob("*")):
        rel = f.relative_to(lang_dir).as_posix()      # library.json names files with '/', on Windows too
        if f.is_file() and rel not in named:
            _inside(lang_dir, f).unlink()
            gone.append(rel)
    for d in sorted((d for d in media.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    return gone


def _changes(prev, lib):
    """Lines naming what changed against the previous library, language by language (`generated` and the version
    are not changes)."""
    before = {x["id"]: x for x in (prev or {}).get("languages", [])}
    after = {x["id"]: x for x in lib["languages"]}
    out = ["added: {}".format(n) for n in after if n not in before]
    out += ["removed: {}".format(n) for n in before if n not in after]
    for n in after:
        if n in before and before[n] != after[n]:
            keys = sorted(k for k in set(before[n]) | set(after[n]) if before[n].get(k) != after[n].get(k))
            out.append("changed: {} ({})".format(n, ", ".join(keys)))
    for k in ("stats", "page_types", "schema"):
        if (prev or {}).get(k) != lib.get(k):
            out.append("changed: {}".format(k))
    return out


def export(site, *, render=True, only=None, today=None):
    site, lang_dir = _site_dirs(site)
    bad = _contract_problems()
    if bad:
        raise ExportError("the manifests do not pass the contract — fix them first (check_vl_contract.py names the "
                          "same):\n  " + "\n  ".join(bad))
    today = today or _dt.date.today().isoformat()
    if only:
        unknown = [n for n in only if n not in vl.REGISTRY]
        if unknown:
            raise ExportError("--only {}: no such language — one of {}".format(", ".join(unknown), ", ".join(vl.REGISTRY)))
    prev = _load_prev(lang_dir)
    lang_dir.mkdir(exist_ok=True)
    _copy_samples(lang_dir)
    rendered = {}
    if render:
        names = list(only) if only else list(vl.REGISTRY)
        with tempfile.TemporaryDirectory() as td:
            for n in names:
                for gid in vl.REGISTRY[n]["grounds"]:
                    print("rendering {} / {} …".format(n, gid), flush=True)
                    rendered.setdefault(n, {})[gid] = _render(n, gid, lang_dir, Path(td))
    lib = build_library(lang_dir, prev, today, rendered)
    gone = _prune(lang_dir, lib)
    f = _inside(lang_dir, lang_dir / "library.json")
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(lib, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(f)
    lines = _changes(prev, lib) + ["removed file: {}".format(g) for g in gone]
    print("wrote {} — {} languages, {} grounds".format(f, lib["stats"]["languages"], lib["stats"]["grounds"]))
    print("\n".join(lines) if lines else "no change against the previous library.json")
    unrendered = [x["id"] for x in lib["languages"] if any(len(g["pages"]) < len(PAGES) for g in x["grounds"])]
    if unrendered:
        print("NOTE: no page renders yet for {} — run without --no-render before publishing".format(", ".join(unrendered)))
    return lib


def check(site):
    """[reasons the page is stale]; empty when library.json and its media match the skill."""
    site, lang_dir = _site_dirs(site)
    bad = _contract_problems()
    if bad:
        return ["the manifests do not pass the contract: " + p for p in bad]
    prev = _load_prev(lang_dir)
    if prev is None:
        return ["{} does not exist — run the export".format(lang_dir / "library.json")]
    want = build_library(lang_dir, prev, prev.get("generated"))
    out = [ln for ln in _changes(prev, want)]
    for name, s in vl.REGISTRY.items():
        for gid in s["grounds"]:
            src = vl.ASSETS / "samples" / (vl._sample_stem(name, gid) + ".jpg")
            dst = lang_dir / "media" / name / "sample-{}.jpg".format(gid)
            if not dst.is_file() or dst.read_bytes() != src.read_bytes():
                out.append("stale sample sheet: {} ({} ground)".format(name, gid))
    # a card whose dialog has no pages is not ready to publish, and renders nobody fingerprinted (a library.json
    # rebuilt with --no-render over old files) cannot be shown to match the skill — both are stale, not fresh
    for x in prev.get("languages", []):
        if x["id"] not in vl.REGISTRY:
            continue
        for g in x["grounds"]:
            if g["id"] not in vl.REGISTRY[x["id"]]["grounds"]:
                continue
            have = [p for p in PAGES if (g.get("pages") or {}).get(p)]
            if not have:
                out.append("no page renders: {} ({} ground)".format(x["id"], g["id"]))
            elif len(have) < len(PAGES):
                out.append("missing page renders: {} ({} ground): {}".format(
                    x["id"], g["id"], ", ".join(p for p in PAGES if p not in have)))
            elif not g.get("render_fp"):
                out.append("no render fingerprint: {} ({} ground) — its pages cannot be shown to match the skill; "
                           "render it".format(x["id"], g["id"]))
            elif g["render_fp"] != _fingerprint(x["id"], g["id"]):
                out.append("stale page renders: {} ({} ground) — the demo deck no longer matches them".format(
                    x["id"], g["id"]))
    # a file the page does not name is left over from an older export; only an export removes it
    named = {g.get("sample") for x in prev.get("languages", []) for g in x.get("grounds", [])}
    named |= {r for x in prev.get("languages", []) for g in x.get("grounds", []) for r in (g.get("pages") or {}).values()}
    media = lang_dir / "media"
    if media.is_dir():
        out += ["orphan media file: {}".format(f.relative_to(lang_dir).as_posix()) for f in sorted(media.rglob("*"))
                if f.is_file() and f.relative_to(lang_dir).as_posix() not in named]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="write the visual-language library page's data and images")
    ap.add_argument("--site", required=True, help="the site repo's folder (slides_maker-site)")
    ap.add_argument("--no-render", action="store_true", help="data and sample sheets only; keep renders already there")
    ap.add_argument("--only", nargs="+", metavar="ID", help="render only these languages (the data covers all)")
    ap.add_argument("--check", action="store_true", help="exit 1 when the page is stale, naming each language")
    ap.add_argument("--today", help=argparse.SUPPRESS)          # tests: a fixed export date
    a = ap.parse_args(argv)
    try:
        if a.check:
            stale = check(a.site)
            if stale:
                print("the library page is stale:\n  " + "\n  ".join(stale))
                print("NEXT: python3 {} --site {}".format(Path(__file__).resolve(), a.site))
                return 1
            print("the library page matches the skill ({} languages)".format(len(vl.REGISTRY)))
            return 0
        if a.only and a.no_render:
            raise ExportError("--only picks what to render, and --no-render renders nothing — pass one of them")
        if a.today:
            _dt.date.fromisoformat(a.today)
        export(a.site, render=not a.no_render, only=a.only, today=a.today)
        return 0
    except ExportError as e:
        print("vl_library_export: {}".format(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
