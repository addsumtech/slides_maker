#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deck versions: see what a rebuild changed, slide by slide, and go back.

WHY. A critic round or a user request ("把第 7 页改成图表") rebuilds the whole deck from its script,
and the user then sees a new file with no account of what moved. The one class of change they must
re-check by hand is a NUMBER — the never-invent rule makes every changed figure a claim somebody has
to confirm — so the diff reports numbers FIRST, then slides. And a rebuild that went the wrong way
should be undoable for the whole deck or for one slide, without anyone hand-merging slide XML.

STORAGE. `<deck-dir>/.versions/vNNN/` holds the .pptx, the build sources (`build_*.py`, `build.py`,
`style.py`, `surface_*.py` and every deck-local module they import), the render PNGs when they belong
to THIS pptx (`render/slideNN.png`), and `manifest.json` {version, created, note, keep, pptx_sha256,
content_sha256, slides[]: {index, title, text_lines, numbers, render_sha, ...}, slide_functions}.
A rebuild re-zips the package, so byte hashes differ on every build; "unchanged" is decided on the
package CONTENT (every part's bytes), which is what a person would call the same deck.
The newest 30 versions are kept; versions marked `--keep` (the ones the user was shown) never prune.

USAGE
    python3 scripts/deck_versions.py snapshot <deck-dir> [--note "..."] [--keep] [--pptx F]
    python3 scripts/deck_versions.py list     <deck-dir>
    python3 scripts/deck_versions.py diff     <deck-dir> [vA] [vB]          # default: the last two
    python3 scripts/deck_versions.py restore  <deck-dir> vNNN               # whole deck
    python3 scripts/deck_versions.py restore  <deck-dir> vNNN --slides 7[,9] # through the SOURCE
    python3 scripts/deck_versions.py prune    <deck-dir> --keep-last N

`deck_cycle.py` snapshots automatically after every build that completed (no CRITICAL fault).
`restore --slides N` numbers slides as they were IN vNNN, replaces the per-slide build function
(`def slide_NN(prs)` / `sNN_name`, the convention `slide_index.py` and the Codex gate read) in the
current build script with vNNN's source of it, and asks for a rebuild. It never splices slide XML,
and it refuses — naming the reason and the fix — whenever the slide-to-function match is ambiguous.

Exit codes: 0 done · 1 nothing done (unchanged / refused on content) · 2 could not run (bad input).
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import difflib
import hashlib
import html as _html
import json
import re
import shlex
import shutil
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

VERSIONS = ".versions"
KEEP_DEFAULT = 30
RENDER_DIR = "render"
MATCH_T = 0.45          # two slides below this similarity are different slides
MOVE_T = 0.60           # an out-of-order pair must be at least this alike to read as "moved"
VISUAL_EPS = 0.05       # % of pixels; below this two renders are the same picture
CHROME_EPS = 0.5        # % of pixels a renumbered page-number footer may change without counting
# The per-slide function convention — the same pattern slide_index.py uses to map slide -> function.
SLIDE_FN = re.compile(r"^(s\d+|slide)[_0-9]")


class Refuse(Exception):
    """A refusal with its cause and its fix. `code` 2 = bad input, 1 = refused on content."""

    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


# ───────────────────────────────────────────── commands the user can paste
def _cmd(script, *args):
    return "python3 " + " ".join(shlex.quote(str(a)) for a in (HERE / script,) + tuple(args))


def _next(script, *args):
    return "NEXT: " + _cmd(script, *args)


# ───────────────────────────────────────────── numbers, as decks write them
def _claim_re():
    """lint_deck's claim-number regex — the one owner of the unit vocabulary (%, 万, 亿, 倍, pt…)."""
    import lint_deck                                                   # noqa: PLC0415
    return lint_deck._CLAIM_NUM


_NUM = re.compile(r"(?<![A-Za-z_\d.])[+\-−]?[$€£¥]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def numbers_in(text):
    """Every number in `text`, as written: 1,350 · 12% · 9.8万 · −3.5% · 2026.

    Full-width forms are folded first (＋１２％ → +12%). A digit glued to an identifier (v2, H2O,
    slide_03) is not a number. A unit lint_deck counts as a claim unit stays attached, with the
    space dropped, so "9.8 万" and "9.8万" are the same number."""
    t = unicodedata.normalize("NFKC", text or "")
    claim = _claim_re()
    out = []
    for m in _NUM.finditer(t):
        tok, end = m.group(0), m.end()
        c = claim.match(t, m.start())
        if c and c.end() > end:          # the same number with its claim unit attached
            tok = c.group(0)
        out.append(re.sub(r"\s+", "", tok).rstrip(",."))
    return out


# ───────────────────────────────────────────── reading a deck
_PAGE_ONLY = re.compile(r"^\s*(?:(?:page|slide|p\.)\s*)?\d{1,3}\s*(?:(?:/|／|of|\|)\s*\d{1,3})?\s*$|^\s*第\s*\d{1,3}\s*页",
                        re.I)


def _fmt_val(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f.is_integer() else "{:g}".format(f)


def _walk(shapes, depth=0):
    from pptx.enum.shapes import MSO_SHAPE_TYPE                       # noqa: PLC0415
    for sh in shapes:
        try:
            is_group = sh.shape_type == MSO_SHAPE_TYPE.GROUP
        except Exception:
            is_group = False
        if is_group and depth < 12:
            yield from _walk(sh.shapes, depth + 1)
        else:
            yield sh


def _shape_lines(sh):
    """Text lines a shape shows: paragraphs, table rows, native chart series (values included)."""
    lines = []
    try:
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                cells = [" ".join("".join(r.text for r in p.runs).strip()
                                  for p in c.text_frame.paragraphs).strip() for c in row.cells]
                if any(cells):
                    lines.append(" | ".join(cells))
            return lines
        if getattr(sh, "has_chart", False) and sh.has_chart:
            for plot in sh.chart.plots:
                cats = [str(c) for c in plot.categories]
                for s in plot.series:
                    vals = list(s.values)
                    pairs = ["{} {}".format(cats[i], _fmt_val(v)) if i < len(cats) else _fmt_val(v)
                             for i, v in enumerate(vals)]
                    lines.append("chart · {}: {}".format(s.name or "series", ", ".join(pairs)))
            return lines
        if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = "".join(r.text for r in p.runs).strip()
                if t:
                    lines.append(" ".join(t.split()))
    except Exception:
        pass
    return lines


def read_deck(pptx):
    """One record per slide: title, text_lines (page chrome removed), numbers, geometry, notes."""
    from pptx import Presentation                                     # noqa: PLC0415
    from pptx.enum.shapes import PP_PLACEHOLDER                       # noqa: PLC0415
    from pptx.util import Emu                                         # noqa: PLC0415
    import lint_deck as L                                             # noqa: PLC0415  (title rule owner)
    prs = Presentation(str(pptx))
    canvas_h = Emu(prs.slide_height).inches
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        lines, bx, geo = [], [], []
        for sh in _walk(slide.shapes):
            try:
                l, t, w, h = (Emu(v or 0).inches for v in (sh.left, sh.top, sh.width, sh.height))
            except Exception:
                l = t = w = h = 0.0
            kind = "ph" if getattr(sh, "is_placeholder", False) else str(getattr(sh, "shape_type", "")).split(".")[-1].split(" ")[0]
            geo.append("{}:{:.1f},{:.1f},{:.1f},{:.1f}".format(kind, l, t, w, h))
            sl = _shape_lines(sh)
            lines.extend(sl)
            if sl and getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                try:
                    size = max((r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs
                                if r.font.size), default=0)
                except Exception:
                    size = 0
                is_title = False
                try:
                    is_title = sh.is_placeholder and sh.placeholder_format.type in (
                        PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
                except Exception:
                    pass
                bx.append({"text": True, "bg": False, "size": size, "t": t,
                           "full": " ".join(sl), "title_ph": is_title})
        ti = L._find_title(bx, canvas_h) if bx else None
        notes = ""
        try:
            if slide.has_notes_slide:
                notes = slide.notes_slide.notes_text_frame.text or ""
        except Exception:
            pass
        slides.append({"index": i, "title": bx[ti]["full"] if ti is not None else "",
                       "text_lines": lines, "geometry": geo,
                       "notes_sha": hashlib.sha256(notes.strip().encode("utf-8")).hexdigest()[:16]})
    _split_chrome(slides)
    for s in slides:
        s["numbers"] = [n for ln in s["text_lines"] for n in numbers_in(ln)]
    for s, slide in zip(slides, prs.slides):
        s["fingerprint"] = _slide_hash(slide)
    return slides


def _slide_hash(slide):
    """This slide's own content: its XML, its layout's identity and the bytes of every picture/media
    it references — and nothing deck-global. render_deck's per-slide fingerprints fold in
    presentation.xml (right for a render cache), so inserting one slide changes them ALL; here that
    would read as every slide "changed"."""
    h = hashlib.sha256(slide.part.blob)
    try:
        for rel in sorted(slide.part.rels.values(), key=lambda r: r.rId):
            if rel.is_external or rel.reltype.endswith("/notesSlide"):
                continue
            part = rel.target_part
            h.update(rel.rId.encode() + b"\0")
            h.update(str(part.partname).encode() if rel.reltype.endswith("/slideLayout")
                     else hashlib.sha256(part.blob).digest())
    except Exception:
        pass
    return h.hexdigest()[:24]


def _split_chrome(slides):
    """Move page chrome (page numbers, a repeated numbered footer) out of the content lines.

    Without this an inserted slide renumbers every later page and reads as N changed slides — the
    exact failure the alignment exists to avoid. Chrome = a page-number-only line, or a line whose
    digit-blind form repeats on at least half the deck (≥3 slides) and whose numbers are page
    numbers (the slide's own index or the slide count)."""
    n = len(slides)
    skel = Counter()
    for s in slides:
        for ln in set(s["text_lines"]):
            if re.search(r"\d", ln):
                skel[re.sub(r"\d+", "#", ln)] += 1
    floor = max(3, (n + 1) // 2)
    for s in slides:
        keep, chrome = [], []
        for ln in s["text_lines"]:
            nums = {int(x) for x in re.findall(r"\d+", ln)}
            if _PAGE_ONLY.match(ln) or (nums and skel[re.sub(r"\d+", "#", ln)] >= floor
                                        and nums <= {s["index"], n}):
                chrome.append(ln)
            else:
                keep.append(ln)
        s["text_lines"], s["chrome"] = keep, chrome


def content_sha(pptx):
    """sha256 over every package part's name + bytes — blind to zip timestamps and part order."""
    h = hashlib.sha256()
    with zipfile.ZipFile(str(pptx)) as z:
        for n in sorted(z.namelist()):
            h.update(n.encode("utf-8") + b"\0")
            h.update(hashlib.sha256(z.read(n)).digest())
    return h.hexdigest()


def _file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ───────────────────────────────────────────── the deck folder
def _deck_dir(arg):
    d = Path(arg).expanduser().resolve()
    if not d.is_dir():
        raise Refuse("deck_versions: no such deck folder: {} — pass the folder that holds the .pptx "
                     "and its build_<deck>.py".format(arg))
    v = d / VERSIONS
    if v.exists() and not v.is_dir():
        raise Refuse("deck_versions: {} exists but is not a folder — move it aside; versions live "
                     "there".format(v))
    return d


def _find_pptx(deck_dir, pptx=None, required=True):
    if pptx:
        p = Path(pptx).expanduser()
        p = p if p.is_absolute() else (deck_dir / p)
        if not p.is_file():
            raise Refuse("deck_versions: --pptx {} does not exist".format(pptx))
        return p.resolve()
    cands = sorted(p for p in deck_dir.glob("*.pptx") if not p.name.startswith(("~$", ".")))
    if len(cands) == 1:
        return cands[0]
    if not cands:
        if not required:
            return None
        raise Refuse("deck_versions: no .pptx in {} — build the deck first ({})".format(
            deck_dir, _cmd("deck_cycle.py", deck_dir / "build_<deck>.py")))
    for b in sorted(deck_dir.glob("build_*.py")):
        named = deck_dir / (b.stem[len("build_"):] + ".pptx")
        if named in cands:
            return named
    raise Refuse("deck_versions: {} .pptx files in {} ({}) and none is named after a build_<name>.py "
                 "— pass --pptx <file> to say which one is the deck".format(
                     len(cands), deck_dir, ", ".join(c.name for c in cands)))


def _build_sources(deck_dir, script=None):
    """Names of the deck-local Python files a rebuild depends on, imports followed transitively."""
    names = {p.name for p in deck_dir.glob("build_*.py")} | {p.name for p in deck_dir.glob("surface_*.py")}
    for extra in ("build.py", "style.py"):
        if (deck_dir / extra).is_file():
            names.add(extra)
    if script:
        names.add(Path(script).name)
    queue = sorted(names)
    while queue:
        f = deck_dir / queue.pop()
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                mods = [node.module.split(".")[0]]
            for mod in mods:
                cand = mod + ".py"
                if cand not in names and (deck_dir / cand).is_file():
                    names.add(cand)
                    queue.append(cand)
    return sorted(n for n in names if (deck_dir / n).is_file())


def _sources_sha(base, names):
    h = hashlib.sha256()
    for n in sorted(names):
        h.update(n.encode("utf-8") + b"\0")
        h.update(hashlib.sha256((base / n).read_bytes()).digest())
    return h.hexdigest()


def _pick_build_script(deck_dir, names, pptx, script=None):
    if script:
        return Path(script).name, ""
    builds = [n for n in names if n.startswith("build_") or n == "build.py"]
    if len(builds) == 1:
        return builds[0], ""
    if not builds:
        return None, "no build script (build_<deck>.py) beside the deck"
    if pptx is not None and "build_{}.py".format(pptx.stem) in builds:
        return "build_{}.py".format(pptx.stem), ""
    return None, "{} build scripts ({}) and none is named build_{}.py".format(
        len(builds), ", ".join(builds), pptx.stem if pptx else "<deck>")


# ───────────────────────────────────────────── slide -> build function (AST, never executed)
def _module_defs(tree):
    return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def slide_function_map(src, n_slides, script_name="the build script"):
    """[function name per slide] read from the build script's AST, or (None, why not).

    Order: an explicit `SLIDES = [...]` registry if there is one (the author's declared order), else
    the source order of every reference to a per-slide function outside the slide functions
    themselves — which covers `for build in (slide_01, slide_02): build(prs)` and direct calls in
    main(). Each function must be referenced once and the count must equal the deck's slide count;
    anything else means the source does not say which function made which slide, and a restore
    built on a guess would overwrite the wrong page."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return None, "{} does not parse ({}), so its slide functions cannot be read".format(script_name, e)
    defs = _module_defs(tree)
    cands = {k for k in defs if SLIDE_FN.match(k)}
    if not cands:
        return None, ("{} has no per-slide functions (def slide_NN(prs) / def sNN_name(prs)), so no "
                      "slide has a source of its own".format(script_name))
    order = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SLIDES" for t in node.targets) \
                and isinstance(node.value, (ast.List, ast.Tuple)):
            elts = node.value.elts
            if elts and all(isinstance(e, ast.Name) and e.id in cands for e in elts):
                order = [e.id for e in elts]
    if order is None:
        refs = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in cands:
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id in cands:
                    refs.append((sub.lineno, sub.col_offset, sub.id))
        order = [r[2] for r in sorted(refs)]
    dup = sorted(k for k, c in Counter(order).items() if c > 1)
    if dup:
        return None, ("{} references {} more than once outside its own body, so which slide it makes "
                      "is ambiguous".format(script_name, ", ".join(dup)))
    if len(order) != n_slides:
        return None, ("{} per-slide function(s) are called in {} but the deck has {} slide(s) — each "
                      "slide must come from exactly one def slide_NN(prs), called once, for a "
                      "per-slide restore to know which source made it".format(len(order), script_name, n_slides))
    return order, "{} slides <-> {} per-slide functions".format(n_slides, len(order))


# ───────────────────────────────────────────── renders that belong to THIS pptx
def _fresh_renders(pptx, render_dir, n):
    if not render_dir.is_dir():
        return None, "no render folder ({}) — render with deck_cycle.py --render to keep pictures".format(render_dir.name)
    try:
        cached = json.loads((render_dir / ".render-cache.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, ("{}/ has no .render-cache.json, so its PNGs cannot be tied to this pptx — "
                      "not stored".format(render_dir.name))
    import render_deck as R                                            # noqa: PLC0415
    fps, _blockers = R._slide_fingerprints(str(pptx))
    if cached.get("deck") != pptx.name or cached.get("fingerprints") != fps:
        return None, ("stale: {}/ was rendered from a different build of the deck — not stored "
                      "(deck_cycle.py --render keeps pictures with the version)".format(render_dir.name))
    pngs = [render_dir / "slide{:02d}.png".format(i) for i in range(1, n + 1)]
    missing = [p.name for p in pngs if not p.is_file()]
    if missing:
        return None, "{}/ is missing {} — not stored".format(render_dir.name, ", ".join(missing[:3]))
    return pngs, "stored (the render fingerprints match this pptx)"


# ───────────────────────────────────────────── the version store
def _vdir(deck_dir):
    return deck_dir / VERSIONS


def _all_versions(deck_dir):
    v = _vdir(deck_dir)
    if not v.is_dir():
        return []
    out = []
    for p in v.iterdir():
        if p.is_dir() and re.fullmatch(r"v\d{3,}", p.name) and (p / "manifest.json").is_file():
            out.append(p.name)
    return sorted(out, key=lambda s: int(s[1:]))


def _load(deck_dir, ver):
    try:
        return json.loads((_vdir(deck_dir) / ver / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refuse("deck_versions: cannot read {}/{}/manifest.json ({})".format(VERSIONS, ver, e))


def _save_manifest(deck_dir, ver, man):
    (_vdir(deck_dir) / ver / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _norm_ver(deck_dir, raw):
    have = _all_versions(deck_dir)
    m = re.fullmatch(r"v?0*(\d+)", str(raw).strip(), re.I)
    if m:
        name = "v{:03d}".format(int(m.group(1)))
        if name in have:
            return name
    raise Refuse("deck_versions: no version {!r} in {} — have: {}".format(
        raw, deck_dir / VERSIONS, ", ".join(have) or "none"))


def snapshot(deck_dir, *, note="", keep=False, pptx=None, script=None, render_dir=None,
             keep_last=KEEP_DEFAULT, backup=False, quiet=False):
    """Store the current state as a new version. Returns (rc, version-or-None)."""
    say = (lambda *a: None) if quiet else print
    pptx = _find_pptx(deck_dir, pptx, required=not backup)
    names = _build_sources(deck_dir, script)
    if pptx is None and not names:
        say("deck_versions: nothing to snapshot in {} (no .pptx, no build script)".format(deck_dir))
        return 1, None
    csha = content_sha(pptx) if pptx else None
    ssha = _sources_sha(deck_dir, names)
    have = _all_versions(deck_dir)
    latest = _load(deck_dir, have[-1]) if have else None
    if latest and latest.get("content_sha256") == csha:
        if latest.get("sources_sha256") == ssha or not backup:
            if keep and not latest.get("keep"):
                latest["keep"] = True
                _save_manifest(deck_dir, have[-1], latest)
            if latest.get("sources_sha256") == ssha:
                say("deck_versions: unchanged since {} — no new version{}".format(
                    have[-1], " (marked --keep)" if keep else ""))
            else:
                say("deck_versions: the deck is unchanged since {} — no new version. (The build "
                    "source changed without changing the deck; if you meant to change the deck, "
                    "rebuild first: {})".format(have[-1], _cmd("deck_cycle.py", deck_dir / (latest.get("build_script") or "build_<deck>.py"))))
            say(_next("deck_versions.py", "diff", deck_dir) if len(have) >= 2 else
                "NEXT: show the user this version; after the next rebuild: " + _cmd("deck_versions.py", "diff", deck_dir))
            return 0, have[-1]
    ver = "v{:03d}".format(int(have[-1][1:]) + 1 if have else 1)
    vd = _vdir(deck_dir) / ver
    vd.mkdir(parents=True)
    for n in names:
        shutil.copy2(deck_dir / n, vd / n)
    slides, renders, rnote = [], False, "no deck in this version"
    build_script, bnote = _pick_build_script(deck_dir, names, pptx, script)
    fmap, fnote = None, bnote or "no deck in this version"
    if pptx is not None:
        shutil.copy2(pptx, vd / pptx.name)
        slides = read_deck(pptx)
        pngs, rnote = _fresh_renders(pptx, Path(render_dir) if render_dir else deck_dir / RENDER_DIR, len(slides))
        if pngs and slides:
            (vd / "render").mkdir()
            for s, p in zip(slides, pngs):
                shutil.copy2(p, vd / "render" / p.name)
                s["render_sha"] = _file_sha(p)
            renders = True
        elif pngs is not None and not slides:
            rnote = "the deck has no slides"
        if build_script:
            fmap, fnote = slide_function_map((deck_dir / build_script).read_text(encoding="utf-8"),
                                             len(slides), build_script)
        if fmap:
            for s, fn in zip(slides, fmap):
                s["function"] = fn
    man = {"version": ver, "created": _dt.datetime.now().isoformat(timespec="seconds"),
           "note": note or "", "keep": bool(keep),
           "pptx_name": pptx.name if pptx else None,
           "pptx_sha256": _file_sha(pptx) if pptx else None, "content_sha256": csha,
           "sources": names, "sources_sha256": ssha, "build_script": build_script,
           "slide_functions": fmap, "slide_functions_note": fnote,
           "renders": renders, "renders_note": rnote, "slides": slides}
    _save_manifest(deck_dir, ver, man)
    pruned = _prune(deck_dir, keep_last)
    say("deck_versions: snapshot {} — {} · {} slide(s){}{}".format(
        ver, pptx.name if pptx else "(build sources only)", len(slides),
        " · kept (never pruned)" if keep else "", " · note: " + note if note else ""))
    if pptx is not None:
        say("   renders:   " + rnote)
        say("   per-slide: " + (fnote if fmap else "restore --slides unavailable for this version — " + fnote))
    if pruned:
        say("   pruned (beyond the newest {}): {}".format(keep_last, ", ".join(pruned)))
    say(_next("deck_versions.py", "diff", deck_dir) if have else
        "NEXT: show the user this version; after the next rebuild: " + _cmd("deck_versions.py", "diff", deck_dir))
    return 0, ver


def _prune(deck_dir, keep_last):
    have = _all_versions(deck_dir)
    if keep_last is None or len(have) <= keep_last:
        return []
    newest = set(have[-keep_last:]) if keep_last > 0 else set()
    gone = []
    for v in have:
        if v in newest:
            continue
        try:
            if _load(deck_dir, v).get("keep"):
                continue
        except Refuse:
            continue
        shutil.rmtree(_vdir(deck_dir) / v)
        gone.append(v)
    for g in gone:                       # a diff page whose pictures were pruned would show holes
        for page in deck_dir.glob("versions-diff_*{}*.html".format(g)):
            if re.search(r"(^|_){}(_|\.html$)".format(g), page.name):
                page.unlink()
    return gone


# ───────────────────────────────────────────── alignment
def _norm(s):
    return " ".join(unicodedata.normalize("NFKC", s or "").lower().split())


def _ratio(a, b):
    if not a and not b:
        return None
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def _body(s):
    return "\n".join(ln for ln in s["text_lines"] if ln != s["title"])


def similarity(a, b):
    """0..1. Title carries most of a slide's identity, the body the rest; a slide with no text at
    all is matched by its picture or geometry (weakly — order then decides)."""
    if a["title"] == b["title"] and a["text_lines"] == b["text_lines"]:
        if a["text_lines"]:
            return 1.0
        if a.get("render_sha") and a.get("render_sha") == b.get("render_sha"):
            return 1.0
        return 0.9 if a.get("geometry") == b.get("geometry") else 0.5
    rt = _ratio(_norm(a["title"]), _norm(b["title"]))
    rb = _ratio(_norm(_body(a)), _norm(_body(b)))
    if rt is None:
        return rb or 0.0
    if rb is None:
        return rt
    return 0.55 * rt + 0.45 * rb


def align(A, B):
    """[(i or None, j or None, kind)] with kind in matched / moved / removed / added.

    An order-preserving alignment (max total similarity, pairs below MATCH_T forbidden) reads an
    inserted or deleted slide as one gap instead of N shifted pages; pairs left over on both sides
    that are still alike are a slide that MOVED."""
    n, m = len(A), len(B)
    sim = [[similarity(A[i], B[j]) for j in range(m)] for i in range(n)]
    S = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best = max(S[i - 1][j], S[i][j - 1])
            s = sim[i - 1][j - 1]
            if s >= MATCH_T:
                best = max(best, S[i - 1][j - 1] + s)
            S[i][j] = best
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        s = sim[i - 1][j - 1]
        if s >= MATCH_T and abs(S[i][j] - (S[i - 1][j - 1] + s)) < 1e-9:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif abs(S[i][j] - S[i - 1][j]) < 1e-9:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    used_a, used_b = {p[0] for p in pairs}, {p[1] for p in pairs}
    left = sorted(((sim[a][b], a, b) for a in range(n) if a not in used_a
                   for b in range(m) if b not in used_b if sim[a][b] >= MOVE_T), reverse=True)
    moved = []
    for _s, a, b in left:
        if a in used_a or b in used_b:
            continue
        used_a.add(a)
        used_b.add(b)
        moved.append((a, b))
    rows = [(a, b, "matched") for a, b in pairs] + [(a, b, "moved") for a, b in moved]
    rows += [(None, b, "added") for b in range(m) if b not in used_b]
    rows += [(a, None, "removed") for a in range(n) if a not in used_a]
    a_to_b = dict(pairs)

    def key(r):
        a, b, _k = r
        if b is not None:
            return (b, 1)
        prev = [a_to_b[x] for x in a_to_b if x < a]
        return (max(prev) if prev else -1, 2)
    return sorted(rows, key=key)


# ───────────────────────────────────────────── per-slide comparison
def _visual_change(pa, pb):
    from PIL import Image                                             # noqa: PLC0415
    import numpy as np                                                # noqa: PLC0415
    with Image.open(pa) as ia, Image.open(pb) as ib:
        w = min(480, ia.width)
        size = (w, max(1, round(w * ia.height / ia.width)))
        a = np.asarray(ia.convert("L").resize(size), dtype=np.int16)
        b = np.asarray(ib.convert("L").resize(size), dtype=np.int16)
    return float((np.abs(a - b) > 24).mean() * 100.0)


def compare(a, b, pa=None, pb=None):
    """What changed between two matched slides."""
    sm = difflib.SequenceMatcher(None, a["text_lines"], b["text_lines"], autojunk=False)
    removed, added, line_pairs = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        removed += a["text_lines"][i1:i2]
        added += b["text_lines"][j1:j2]
        if tag == "replace":
            line_pairs += list(zip(a["text_lines"][i1:i2], b["text_lines"][j1:j2]))
    gone = Counter(a["numbers"]) - Counter(b["numbers"])
    new = Counter(b["numbers"]) - Counter(a["numbers"])
    changed = []
    for la, lb in line_pairs:
        xs = [x for x in numbers_in(la) if gone[x] > 0]
        ys = [y for y in numbers_in(lb) if new[y] > 0]
        for x, y in zip(xs, ys):
            if gone[x] > 0 and new[y] > 0:
                gone[x] -= 1
                new[y] -= 1
                changed.append((x, y, la, lb))
    num_removed = [x for x, c in gone.items() for _ in range(c)]
    num_added = [y for y, c in new.items() for _ in range(c)]
    visual, vnote = None, ""
    if pa and pb and Path(pa).is_file() and Path(pb).is_file():
        visual = 0.0 if a.get("render_sha") and a.get("render_sha") == b.get("render_sha") \
            else _visual_change(pa, pb)
        vnote = "visual: {:.1f}% of the page changed".format(visual)
    else:
        ga, gb = a.get("geometry") or [], b.get("geometry") or []
        if ga != gb:
            g = difflib.SequenceMatcher(None, ga, gb, autojunk=False)
            moved = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in g.get_opcodes() if t != "equal")
            vnote = "geometry: {} shape(s) added, removed or moved (no renders in both versions to measure pixels)".format(moved)
        elif a.get("fingerprint") and b.get("fingerprint") and a["fingerprint"] != b["fingerprint"] \
                and a.get("chrome") == b.get("chrome"):      # a renumbered page is not a formatting change
            vnote = "formatting changed (same text and geometry; no renders in both versions to measure pixels)"
    # When only the page chrome differs (a renumbered footer), its few changed pixels are not a change.
    eps = VISUAL_EPS if a.get("chrome") == b.get("chrome") else CHROME_EPS
    is_changed = bool(removed or added or a["title"] != b["title"] or a.get("notes_sha") != b.get("notes_sha")
                      or (visual is not None and visual >= eps)
                      or (visual is None and bool(vnote)))
    return {"changed": is_changed, "retitled": a["title"] != b["title"], "removed": removed,
            "added": added, "num_changed": changed, "num_removed": num_removed,
            "num_added": num_added, "visual": visual, "visual_note": vnote,
            "notes_changed": a.get("notes_sha") != b.get("notes_sha")}


def _render_path(deck_dir, ver, man, s):
    if not man.get("renders") or s is None:
        return None
    return _vdir(deck_dir) / ver / "render" / "slide{:02d}.png".format(s["index"])


def diff_versions(deck_dir, va, vb):
    ma, mb = _load(deck_dir, va), _load(deck_dir, vb)
    for v, m in ((va, ma), (vb, mb)):
        if m.get("pptx_name") is None:
            raise Refuse("deck_versions: {} holds no deck (a pre-restore backup of the build sources "
                         "only) — diff two versions that hold a .pptx (list them: {})".format(
                             v, _cmd("deck_versions.py", "list", deck_dir)))
    A, B = ma["slides"], mb["slides"]
    rows = []
    for i, j, kind in align(A, B):
        a = A[i] if i is not None else None
        b = B[j] if j is not None else None
        r = {"kind": kind, "a": a, "b": b, "pa": _render_path(deck_dir, va, ma, a),
             "pb": _render_path(deck_dir, vb, mb, b)}
        if a is not None and b is not None:
            r.update(compare(a, b, r["pa"], r["pb"]))
            if kind == "matched":
                r["kind"] = "changed" if r["changed"] else "unchanged"
        rows.append(r)
    counts = Counter(r["kind"] for r in rows)
    return ma, mb, rows, counts


def _q(s, n=60):
    s = s or "(no title)"
    return "\"{}\"".format(s if len(s) <= n else s[:n - 1] + "…")


def _idx(s):
    return str(s["index"]) if s else "·"


def text_report(va, vb, ma, mb, rows, counts):
    out = ["deck_versions diff {} → {}   ({} · {} → {} slides)".format(
        va, vb, mb.get("pptx_name"), len(ma["slides"]), len(mb["slides"])),
        "  {} changed · {} added · {} removed · {} moved · {} unchanged".format(
            counts["changed"], counts["added"], counts["removed"], counts["moved"], counts["unchanged"]), ""]
    num_lines = []
    for r in rows:
        a, b = r["a"], r["b"]
        head = "  slide {} → {}  {}".format(_idx(a), _idx(b), _q((b or a)["title"]))
        items = []
        if r["kind"] == "added":
            items = ["      + {}   (new slide)".format(n) for n in b["numbers"]]
        elif r["kind"] == "removed":
            items = ["      − {}   (slide removed)".format(n) for n in a["numbers"]]
        else:
            items = ["      {} → {}   ({}  →  {})".format(x, y, la, lb) for x, y, la, lb in r.get("num_changed", [])]
            items += ["      − {}   removed".format(n) for n in r.get("num_removed", [])]
            items += ["      + {}   added".format(n) for n in r.get("num_added", [])]
        if items:
            num_lines += [head] + items
    if num_lines:
        out.append("NUMBERS — check every one against its source (a changed figure is a claim):")
        out += num_lines
    else:
        out.append("NUMBERS — none added, removed or changed.")
    out += ["", "SLIDES"]
    label = {"changed": "changed  ", "unchanged": "unchanged", "added": "ADDED    ",
             "removed": "REMOVED  ", "moved": "MOVED    "}
    for r in rows:
        a, b = r["a"], r["b"]
        lab = label[r["kind"]]
        if r.get("retitled"):
            lab = "retitled "
        title = _q((b or a)["title"])
        if r.get("retitled"):
            title = "{} → {}".format(_q(a["title"]), _q(b["title"]))
        out.append("  {:>3} → {:<3} {}  {}".format(_idx(a), _idx(b), lab, title))
        if r["kind"] in ("changed", "moved") or r.get("retitled"):
            for ln in r.get("removed", [])[:12]:
                out.append("            − " + ln)
            for ln in r.get("added", [])[:12]:
                out.append("            + " + ln)
            if r.get("notes_changed"):
                out.append("            speaker notes changed")
            if r.get("visual_note"):
                out.append("            " + r["visual_note"])
    return "\n".join(out)


_CSS = """
:root{--bg:#f6f4ef;--ink:#1d2421;--mute:#6b716d;--card:#fff;--line:#d9d5cc;--add:#d8f0dc;--del:#f8dcd9;
--num:#ffe28a;--chg:#c2410c;--ok:#2f6f4f}
@media (prefers-color-scheme:dark){:root{--bg:#161a18;--ink:#e9ece9;--mute:#9aa29d;--card:#1f2522;--line:#333b37;
--add:#1f4a2c;--del:#5a2420;--num:#6b5512;--chg:#fb923c;--ok:#6fcf97}}
body{background:var(--bg);color:var(--ink);font:15px/1.45 -apple-system,"Segoe UI",Roboto,"Noto Sans","PingFang SC","Microsoft YaHei",sans-serif;margin:0;padding:24px 16px}
main{max-width:1180px;margin:0 auto}h1{font-size:22px;margin:0 0 4px}.sum{color:var(--mute);margin:0 0 20px}
section{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--line);border-radius:8px;margin:0 0 16px;padding:14px 16px}
section.changed,section.moved{border-left-color:var(--chg)}section.added{border-left-color:var(--ok)}section.removed{border-left-color:#b91c1c}
details.unchanged{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:0 0 8px;padding:8px 16px;color:var(--mute)}
details.unchanged summary{cursor:pointer}.ctx{color:var(--mute);font-size:13px;margin-left:6px}h2{font-size:16px;margin:0 0 8px}.k{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin-right:8px}
.nums{margin:6px 0 10px;padding:8px 10px;background:var(--bg);border-radius:6px}.nums b{display:block;font-size:12px;color:var(--mute);margin-bottom:4px}
mark{background:var(--num);color:inherit;padding:0 3px;border-radius:3px}
.l{margin:2px 0;padding:2px 6px;border-radius:4px;white-space:pre-wrap;word-break:break-word}.l.del{background:var(--del)}.l.add{background:var(--add)}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}.pair figure{margin:0}.pair img{width:100%;border:1px solid var(--line);border-radius:4px;display:block}
figcaption{font-size:12px;color:var(--mute);margin-top:4px}.none{border:1px dashed var(--line);border-radius:4px;padding:18px;color:var(--mute);font-size:13px}
@media (max-width:640px){.pair{grid-template-columns:1fr}}
"""


def html_report(deck_dir, va, vb, ma, mb, rows, counts):
    e = _html.escape

    def fig(path, ver, man, s):
        if s is None:
            return "<figure><div class=none>not in {}</div><figcaption>{}</figcaption></figure>".format(e(ver), e(ver))
        if path is None or not Path(path).is_file():
            return ("<figure><div class=none>no render stored in {} — {}</div><figcaption>{} · slide {}"
                    "</figcaption></figure>").format(e(ver), e(man.get("renders_note") or ""), e(ver), s["index"])
        rel = Path(path).relative_to(deck_dir).as_posix()
        return ("<figure><img src=\"{}\" alt=\"{} slide {}\" loading=lazy><figcaption>{} · slide {}"
                "</figcaption></figure>").format(e(rel), e(ver), s["index"], e(ver), s["index"])

    parts = []
    for r in rows:
        a, b = r["a"], r["b"]
        kind = "retitled" if r.get("retitled") else r["kind"]
        title = e((b or a)["title"] or "(no title)")
        if r.get("retitled"):
            title = "{} → {}".format(e(a["title"] or "(no title)"), e(b["title"] or "(no title)"))
        nums = []
        if r["kind"] == "added":
            nums = ["+ <mark>{}</mark>".format(e(n)) for n in b["numbers"]]
        elif r["kind"] == "removed":
            nums = ["− <mark>{}</mark>".format(e(n)) for n in a["numbers"]]
        else:
            nums = ["<mark>{}</mark> → <mark>{}</mark> <span class=ctx>{}</span>".format(e(x), e(y), e(lb))
                    for x, y, _la, lb in r.get("num_changed", [])]
            nums += ["− <mark>{}</mark> removed".format(e(n)) for n in r.get("num_removed", [])]
            nums += ["+ <mark>{}</mark> added".format(e(n)) for n in r.get("num_added", [])]
        body = ["<h2><span class=k>{}</span>slide {} → {} · {}</h2>".format(e(kind), _idx(a), _idx(b), title)]
        if nums:
            body.append("<div class=nums><b>Numbers — check each against its source</b>{}</div>".format(
                "<br>".join(nums)))
        for ln in r.get("removed", []):
            body.append("<div class='l del'>− {}</div>".format(e(ln)))
        for ln in r.get("added", []):
            body.append("<div class='l add'>+ {}</div>".format(e(ln)))
        if r.get("notes_changed"):
            body.append("<div class=k>speaker notes changed</div>")
        if r.get("visual_note"):
            body.append("<div class=k>{}</div>".format(e(r["visual_note"])))
        pair = "<div class=pair>{}{}</div>".format(fig(r["pa"], va, ma, a), fig(r["pb"], vb, mb, b))
        if r["kind"] == "unchanged":     # folded: the page is about what changed
            parts.append("<details class=unchanged><summary><span class=k>unchanged</span>slide {} → {} · {}"
                         "</summary>{}</details>".format(_idx(a), _idx(b), title, pair))
            continue
        body.append(pair)
        parts.append("<section class={}>{}</section>".format(r["kind"], "".join(body)))
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            "content=\"width=device-width,initial-scale=1\"><title>Deck versions {va} to {vb}</title>"
            "<style>{css}</style></head><body><main><h1>{deck}: {va} → {vb}</h1><p class=sum>{c} changed · "
            "{ad} added · {rm} removed · {mv} moved · {un} unchanged — {na} ({ta}) → {nb} ({tb}) slides</p>"
            "{parts}</main></body></html>\n").format(
        va=e(va), vb=e(vb), css=_CSS, deck=e(mb.get("pptx_name") or ""), c=counts["changed"],
        ad=counts["added"], rm=counts["removed"], mv=counts["moved"], un=counts["unchanged"],
        na=len(ma["slides"]), nb=len(mb["slides"]), ta=e(ma.get("created", "")), tb=e(mb.get("created", "")),
        parts="".join(parts))


# ───────────────────────────────────────────── commands
def cmd_snapshot(a):
    d = _deck_dir(a.deck_dir)
    rc, _v = snapshot(d, note=a.note or "", keep=a.keep, pptx=a.pptx,
                      render_dir=(d / a.render_dir) if a.render_dir else None)
    return rc


def _changed_count(counts):
    return counts["changed"] + counts["added"] + counts["removed"] + counts["moved"]


def cmd_list(a):
    d = _deck_dir(a.deck_dir)
    have = _all_versions(d)
    if not have:
        print("deck_versions: no versions in {} yet.".format(d))
        print(_next("deck_versions.py", "snapshot", d))
        return 0
    mans = {v: _load(d, v) for v in have}
    for v in have:
        m = mans[v]
        print("  {}  {}  {:>3} slides  {}  {}{}".format(
            v, (m.get("created") or "")[:16].replace("T", " "), len(m.get("slides") or []),
            "keep" if m.get("keep") else "    ", "pictures" if m.get("renders") else "no pictures",
            "  · " + m["note"] if m.get("note") else ""))
    latest = have[-1]
    kept = [v for v in have[:-1] if mans[v].get("keep")]
    if mans[latest].get("keep"):
        line = "version: {} (the version the user was shown)".format(latest)
    elif kept and mans[kept[-1]].get("pptx_name") and mans[latest].get("pptx_name"):
        _ma, _mb, _rows, counts = diff_versions(d, kept[-1], latest)
        n = _changed_count(counts)
        line = "version: {} · {} slide{} changed since {}, the version you last saw".format(
            latest, n, "" if n == 1 else "s", kept[-1])
    else:
        line = ("version: {} (no version is marked --keep yet — snapshot --keep when you show the user "
                "a version)".format(latest))
    print("\nHAND-OFF LINE: " + line)
    print(_next("deck_versions.py", "diff", d) if len(have) >= 2 else _next("deck_versions.py", "snapshot", d, "--keep"))
    return 0


def cmd_diff(a):
    d = _deck_dir(a.deck_dir)
    have = _all_versions(d)
    if a.va and a.vb:
        va, vb = _norm_ver(d, a.va), _norm_ver(d, a.vb)
    elif a.va:
        va = _norm_ver(d, a.va)
        vb = have[-1]
    else:
        if len(have) < 2:
            raise Refuse("deck_versions: {} version(s) in {} — a diff needs two. Rebuild after a change "
                         "(deck_cycle.py snapshots on every clean build) or: {}".format(
                             len(have), d, _cmd("deck_versions.py", "snapshot", d)))
        va, vb = have[-2], have[-1]
    if va == vb:
        raise Refuse("deck_versions: diff {} against itself — name two different versions".format(va))
    ma, mb, rows, counts = diff_versions(d, va, vb)
    print(text_report(va, vb, ma, mb, rows, counts))
    page = d / "versions-diff_{}_{}.html".format(va, vb)
    page.write_text(html_report(d, va, vb, ma, mb, rows, counts), encoding="utf-8")
    print("\nHTML: {}  (open it from the deck folder; it reads the pictures from {}/)".format(page.as_uri(), VERSIONS))
    if not (ma.get("renders") and mb.get("renders")):
        print("   pictures: {} {} · {} {}".format(va, ma.get("renders_note"), vb, mb.get("renders_note")))
    changed = [r for r in rows if r["kind"] in ("changed", "removed", "moved") and r["a"]]
    if changed:
        print("NEXT: show the user the page above. To take one slide back: " + _cmd(
            "deck_versions.py", "restore", d, va, "--slides", changed[0]["a"]["index"]))
    else:
        print("NEXT: show the user the page above; to go back to {} entirely: {}".format(
            va, _cmd("deck_versions.py", "restore", d, va)))
    return 0


def _pre_restore_backup(d, ver, pptx=None):
    """Snapshot the current state before a restore overwrites it. -> (version, newly_made)."""
    before = set(_all_versions(d))
    _rc, saved = snapshot(d, note="before restoring {}".format(ver), pptx=pptx, backup=True, quiet=True,
                          keep_last=None)
    return (saved, saved not in before) if saved else None


def _say_backup(d, saved):
    if not saved:
        print("   nothing was there to back up before the restore")
        return
    ver, new = saved
    print("   {} the state before this restore {} (undo: {})".format(
        "saved" if new else "already saved:", "as " + ver if new else "is " + ver,
        _cmd("deck_versions.py", "restore", d, ver)))


def cmd_restore(a):
    d = _deck_dir(a.deck_dir)
    ver = _norm_ver(d, a.version)
    if a.slides:
        return _restore_slides(d, ver, a.slides, a.pptx)
    man = _load(d, ver)
    saved = _pre_restore_backup(d, ver, a.pptx)
    vd = _vdir(d) / ver
    copied = []
    if man.get("pptx_name"):
        shutil.copy2(vd / man["pptx_name"], d / man["pptx_name"])
        copied.append(man["pptx_name"])
    for n in man.get("sources") or []:
        shutil.copy2(vd / n, d / n)
        copied.append(n)
    extra = sorted(set(_build_sources(d)) - set(man.get("sources") or []))
    print("deck_versions: restored {} — {}".format(ver, ", ".join(copied) or "nothing to copy"))
    _say_backup(d, saved)
    if extra:
        print("   not in {}, left as they are: {}".format(ver, ", ".join(extra)))
    print("   the pictures in {}/ are now stale — the rebuild below re-renders them".format(RENDER_DIR))
    bs = man.get("build_script")
    if bs:
        print(_next("deck_cycle.py", d / bs, "--render"))
    elif man.get("pptx_name"):
        print(_next("render_deck.py", d / man["pptx_name"], d / RENDER_DIR))
    return 0


def _names_defined(tree):
    out, star = set(), False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name):
                        out.add(sub.id)
        elif isinstance(node, ast.Import):
            out |= {(al.asname or al.name).split(".")[0] for al in node.names}
        elif isinstance(node, ast.ImportFrom):
            for al in node.names:
                if al.name == "*":
                    star = True
                else:
                    out.add(al.asname or al.name)
        elif isinstance(node, (ast.If, ast.Try, ast.With, ast.For)):
            for sub in ast.walk(node):
                if isinstance(sub, (ast.FunctionDef, ast.ClassDef)):
                    out.add(sub.name)
                elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    out.add(sub.id)
                elif isinstance(sub, (ast.Import, ast.ImportFrom)):
                    out |= {(al.asname or al.name).split(".")[0] for al in sub.names if al.name != "*"}
    return out, star


def _segment(text, node):
    lines = text.splitlines(keepends=True)
    start = min([node.lineno] + [dec.lineno for dec in node.decorator_list]) - 1
    return start, node.end_lineno, "".join(lines[start:node.end_lineno])


def _restore_slides(d, ver, spec, pptx=None):
    try:
        nums = sorted({int(x) for x in str(spec).replace(" ", "").split(",") if x})
    except ValueError:
        raise Refuse("deck_versions: --slides takes slide numbers like 7 or 7,9 (got {!r})".format(spec))
    if not nums:
        raise Refuse("deck_versions: --slides needs at least one slide number")
    man = _load(d, ver)
    n = len(man.get("slides") or [])
    bad = [x for x in nums if x < 1 or x > n]
    if bad:
        raise Refuse("deck_versions: {} has {} slide(s); --slides {} is out of range. Slides are numbered "
                     "as they were IN {} (see: {}).".format(ver, n, ",".join(map(str, bad)), ver,
                                                          _cmd("deck_versions.py", "diff", d, ver)))
    if not man.get("build_script"):
        raise Refuse("deck_versions: {} has no build script beside its deck ({}), so its slides have no "
                     "source to restore from — a per-slide restore never splices slide XML. Restore the "
                     "whole deck instead: {}".format(ver, man.get("slide_functions_note") or "",
                                                     _cmd("deck_versions.py", "restore", d, ver)), code=1)
    fmap = man.get("slide_functions")
    if not fmap:
        raise Refuse("deck_versions: cannot tell which function made which slide in {}: {}. Give each slide "
                     "its own def slide_NN(prs), called once from main(), or restore the whole deck: "
                     "{}".format(ver, man.get("slide_functions_note"), _cmd("deck_versions.py", "restore", d, ver)),
                     code=1)
    vd = _vdir(d) / ver
    old_texts = {nm: (vd / nm).read_text(encoding="utf-8") for nm in man.get("sources") or []}
    old_trees = {nm: ast.parse(t) for nm, t in old_texts.items()}
    cur_names = _build_sources(d)
    cur_texts = {nm: (d / nm).read_text(encoding="utf-8") for nm in cur_names}
    try:
        cur_trees = {nm: ast.parse(t) for nm, t in cur_texts.items()}
    except SyntaxError as e:
        raise Refuse("deck_versions: the current build sources do not parse ({}) — fix that first".format(e))
    plan, unchanged = [], []
    for k in nums:
        fn = fmap[k - 1]
        title = man["slides"][k - 1].get("title") or ""
        old_hits = [(nm, _module_defs(t)[fn]) for nm, t in old_trees.items() if fn in _module_defs(t)]
        if len(old_hits) != 1:
            raise Refuse("deck_versions: {} defines {} in {} file(s) of {}, so its source is ambiguous".format(
                ver, fn, len(old_hits), ver), code=1)
        old_file, old_node = old_hits[0]
        # cross-check: the slide's own title written as a literal in ANOTHER slide function only
        bs_tree = old_trees.get(man["build_script"])
        if title and len(title) >= 4 and bs_tree is not None:
            holders = [nm for nm, node in _module_defs(bs_tree).items() if SLIDE_FN.match(nm)
                       and title in (ast.get_source_segment(old_texts[man["build_script"]], node) or "")]
            if holders and fn not in holders:
                raise Refuse("deck_versions: slide {} of {} ({!r}) maps to {} by call order, but its title is "
                             "written in {} — the match is ambiguous, so nothing was changed. Restore the "
                             "whole deck, or copy the function by hand from {}".format(
                                 k, ver, title, fn, ", ".join(holders), vd / old_file), code=1)
        cur_hits = [(nm, node) for nm, t in cur_trees.items() for node in t.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn]
        if not cur_hits:
            raise Refuse("deck_versions: slide {} of {} was made by {}(), which the current build sources ({}) "
                         "no longer define — renamed or deleted. Nothing was changed. Rename it back, or "
                         "restore the whole deck: {}".format(k, ver, fn, ", ".join(cur_names) or "none",
                                                            _cmd("deck_versions.py", "restore", d, ver)), code=1)
        if len(cur_hits) > 1:
            raise Refuse("deck_versions: {}() has {} definitions in the current sources ({}) — defined twice, "
                         "so which one to replace is ambiguous. Nothing was changed; delete the stale one "
                         "and re-run.".format(fn, len(cur_hits), ", ".join(sorted({h[0] for h in cur_hits}))), code=1)
        cur_file, cur_node = cur_hits[0]
        _s0, _e0, old_seg = _segment(old_texts[old_file], old_node)
        s1, e1, cur_seg = _segment(cur_texts[cur_file], cur_node)
        if old_seg == cur_seg:
            unchanged.append((k, fn))
            continue
        called = any(isinstance(sub, ast.Name) and sub.id == fn and isinstance(sub.ctx, ast.Load)
                     for node in cur_trees[cur_file].body if node is not cur_node for sub in ast.walk(node))
        if not called:
            raise Refuse("deck_versions: {}() is defined but no longer called by {} — restoring its body would "
                         "not bring slide {} back. Add it to the build order first, or restore the whole "
                         "deck: {}".format(fn, cur_file, k, _cmd("deck_versions.py", "restore", d, ver)), code=1)
        old_defined, _st = _names_defined(old_trees[old_file])
        cur_defined, cur_star = _names_defined(cur_trees[cur_file])
        used = {sub.id for sub in ast.walk(old_node) if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load)}
        missing = sorted((used & old_defined) - cur_defined - {fn})
        if missing and not cur_star:
            raise Refuse("deck_versions: {}'s {}() uses {} which {} no longer defines — the restored slide "
                         "would not build. Nothing was changed. Copy those from {} too, or restore the whole "
                         "deck: {}".format(ver, fn, ", ".join(missing), cur_file, vd / old_file,
                                           _cmd("deck_versions.py", "restore", d, ver)), code=1)
        plan.append({"slide": k, "fn": fn, "title": title, "file": cur_file, "start": s1, "end": e1,
                     "new": old_seg})
    for k, fn in unchanged:
        print("deck_versions: slide {} of {} — {}() is unchanged between {} and now; its difference comes "
              "from elsewhere (a shared helper, style.py, data). Not restored.".format(k, ver, fn, ver))
    if not plan:
        print("NEXT: compare the two versions to see where the change lives: " + _cmd(
            "deck_versions.py", "diff", d, ver))
        return 1
    saved = _pre_restore_backup(d, ver, pptx)
    by_file = {}
    for p in plan:
        by_file.setdefault(p["file"], []).append(p)
    new_texts = {}
    for f, ps in by_file.items():
        lines = cur_texts[f].splitlines(keepends=True)
        for p in sorted(ps, key=lambda q: q["start"], reverse=True):
            seg = p["new"] if p["new"].endswith("\n") else p["new"] + "\n"
            lines[p["start"]:p["end"]] = [seg]
        txt = "".join(lines)
        try:
            ast.parse(txt)
        except SyntaxError as e:
            raise Refuse("deck_versions: the restored {} would not parse ({}) — nothing was written".format(f, e))
        new_texts[f] = txt
    for f, txt in new_texts.items():
        (d / f).write_text(txt, encoding="utf-8")
    for p in plan:
        print("deck_versions: slide {} of {} ({}) — {}() in {} replaced with {}'s source".format(
            p["slide"], ver, _q(p["title"]), p["fn"], p["file"], ver))
    _say_backup(d, saved)
    print("   the .pptx is NOT changed yet — rebuild it from the restored source:")
    bs = man.get("build_script")
    cur_bs = bs if (d / bs).is_file() else plan[0]["file"]
    print(_next("deck_cycle.py", d / cur_bs, "--render"))
    print("   then: " + _cmd("deck_versions.py", "diff", d))
    return 0


def cmd_prune(a):
    d = _deck_dir(a.deck_dir)
    if a.keep_last < 1:
        raise Refuse("deck_versions: --keep-last must be at least 1 (got {})".format(a.keep_last))
    gone = _prune(d, a.keep_last)
    have = _all_versions(d)
    print("deck_versions: pruned {} — kept {}".format(", ".join(gone) or "nothing", ", ".join(have) or "none"))
    print(_next("deck_versions.py", "list", d))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="deck_versions.py",
                                 description="Snapshot, list, diff and restore versions of a deck "
                                             "(stored in <deck-dir>/.versions/).")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("snapshot", help="store the current deck + build sources as a new version")
    p.add_argument("deck_dir")
    p.add_argument("--note", default="")
    p.add_argument("--keep", action="store_true", help="never prune this version (e.g. the user saw it)")
    p.add_argument("--pptx", help="which .pptx is the deck, when the folder holds several")
    p.add_argument("--render-dir", help="render folder inside the deck dir (default: render)")
    p = sub.add_parser("list", help="versions with time, note and slide count, then the hand-off line")
    p.add_argument("deck_dir")
    p = sub.add_parser("diff", help="slide-by-slide changes, numbers first (default: the last two)")
    p.add_argument("deck_dir")
    p.add_argument("va", nargs="?")
    p.add_argument("vb", nargs="?")
    p = sub.add_parser("restore", help="restore a whole version, or --slides through the build source")
    p.add_argument("deck_dir")
    p.add_argument("version")
    p.add_argument("--slides", help="slide numbers AS IN that version, e.g. 7 or 7,9")
    p.add_argument("--pptx", help="which .pptx is the deck, when the folder holds several")
    p = sub.add_parser("prune", help="delete old versions; --keep versions always stay")
    p.add_argument("deck_dir")
    p.add_argument("--keep-last", type=int, required=True)
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 2
    try:
        return {"snapshot": cmd_snapshot, "list": cmd_list, "diff": cmd_diff, "restore": cmd_restore,
                "prune": cmd_prune}[a.cmd](a)
    except Refuse as r:
        print(str(r))
        return r.code


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
