#!/usr/bin/env python3
"""Render a .pptx to one PNG per slide, so you can SEE each slide and catch
overflow / contrast / glyph problems before handing the deck back.

Cross-platform: works on macOS, Linux, WSL, and NATIVE Windows (PowerShell / cmd) —
no shell required. The .sh wrapper just delegates here.

Usage:
    python render_deck.py /path/to/deck.pptx [out_dir]
    # Windows:  python scripts\\render_deck.py C:\\path\\deck.pptx
Output: <out_dir>/slide01.png, slide02.png, ...   (default out_dir: ./render)

Requires: LibreOffice + pymupdf (python -m pip install pymupdf). One-time installs.
Override LibreOffice discovery with the SOFFICE env var (full path to the binary).
"""
import json
import os
import re
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path


def find_soffice():
    """Locate the LibreOffice binary across macOS / Linux / WSL / native Windows.

    Order: $SOFFICE override -> anything on PATH -> known install locations.
    On Windows, prefer the sibling ``soffice.com`` (the console front-end that
    blocks until conversion finishes) over ``soffice.exe`` (which can detach and
    leave the PDF half-written).
    """
    def prefer_com(path):
        if path and path.lower().endswith("soffice.exe"):
            com = path[:-4] + ".com"
            if os.path.isfile(com):
                return com
        return path

    env = os.environ.get("SOFFICE")
    if env and os.path.isfile(env):
        return prefer_com(env)

    for cmd in ("soffice", "libreoffice", "soffice.com", "soffice.exe"):
        found = shutil.which(cmd)
        if found:
            return prefer_com(found)

    candidates = [
        # macOS
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        # Linux
        "/usr/bin/soffice", "/usr/bin/libreoffice", "/usr/local/bin/soffice",
        "/snap/bin/libreoffice", "/opt/libreoffice/program/soffice",
        # native Windows (default installer locations)
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        # Windows install reached from WSL via the /mnt/c mount
        "/mnt/c/Program Files/LibreOffice/program/soffice.exe",
    ]
    # %ProgramFiles% may point somewhere non-default on Windows.
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        base = os.environ.get(var)
        if base:
            candidates.append(os.path.join(base, "LibreOffice", "program", "soffice.exe"))

    for path in candidates:
        if os.path.isfile(path):
            return prefer_com(path)
    return None


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _report_carried_by(pptx_path, cb):
    """Say, as a number, how many `carried_by` slides are structurally distinct from the deck.

    WHY. `carried_by` was presence-checked only: a list of ≥2 slide numbers passed. Naming a slide
    is free, so the cheapest way to satisfy the field is to list three and put a token of the motif
    — a stripe, a matching hue — on two of them, while the actual structural work happens on one.
    Measured on a real build: carried_by=[1, 9, 12], and only slide 9 had a skeleton the deck did
    not otherwise use. The plan read bravely and the deck read safe, which is precisely the failure
    `boldness`/`signature_move` exist to prevent.

    NOT A FAILURE, deliberately. A signature move can legitimately live on colour, type or concept
    and touch no geometry at all — dying on that would push authors toward layout stunts. So this
    prints the count and warns; the author has to look at a number instead of at their own sentence.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import lint_deck as _ld
        from pptx import Presentation as _P
        prs = _P(str(pptx_path))
        sw = prs.slide_width / 914400.0
        sh = prs.slide_height / 914400.0
        skels = [_ld._skeleton(_ld._boxes(s, sw, sh)) for s in prs.slides]
    except Exception as e:                      # never let a measurement break the delivery gate
        print(f"[gates] carried_by: not measurable on this deck ({type(e).__name__}) — "
              f"check by eye that each named slide is structurally distinct")
        return
    if not skels:
        return

    def _same(a, b):
        return len(a & b) / max(1, len(a | b)) >= 0.75

    # the deck's default page = the skeleton the most slides share
    modal, best = skels[0], 0
    for cand in skels:
        c = sum(1 for k in skels if _same(cand, k))
        if c > best:
            modal, best = cand, c
    distinct = [i for i in cb
                if isinstance(i, int) and 1 <= i <= len(skels) and not _same(skels[i - 1], modal)]
    print(f"[gates] carried_by structure: {len(distinct)}/{len(cb)} named slide(s) differ from the "
          f"deck's default skeleton (distinct: {distinct or 'none'})")
    if len(distinct) < 2:
        print("        ⚠ the signature move is doing structural work on fewer than 2 of the slides "
              "that claim it. If it lives on colour/type/concept instead, fine — say which in the "
              "hand-off. If it does not, the deck is safer than its plan and this is the moment to "
              "fix that, not after the user says '不够大胆'.")


def _report_form_reach(pptx_path):
    """Say how much of the CATALOGUE the build actually reached for, at the moment of hand-off.

    WHY, measured on this skill's own last deck. The library exposes ~174 helpers. The build called
    15, of which exactly one (`stat_row`) was a composed form; the other 59 shapes were raw
    `box`/`text`. `component_audit.py` reports precisely this and SKILL.md's pre-flight points at
    it — but the pointer is prose, and the author (me) never ran it. The cost was concrete: slide 3
    hand-built a track + fill + label out of two boxes, and `meter_bar`'s docstring opens by calling
    itself "the correct, reusable form of the hand-built 'track + fill + number' row".

    Bespoke composition is NOT the failure — a Mondrian page and a tessellation cannot come from a
    catalogue, and forcing components onto them would make the deck worse. The failure is never
    having LOOKED, which is invisible unless somebody prints the number. So this prints it and
    names the one command that answers it, and never blocks.
    """
    try:
        here = Path(__file__).resolve().parent
        sys.path.insert(0, str(here))
        import component_audit as _ca
        # the build script sits next to the deck by convention (build_deck.py / build_<name>.py)
        cands = sorted(Path(pptx_path).parent.glob("build*.py"))
        if not cands:
            return
        called = _ca._script_calls(str(cands[0]))
    except Exception:
        return
    forms = sorted(set(called) & set(_ca.FORM_GUARANTEE))
    prims = sum(1 for n in ("box", "text") if n in called)
    if len(forms) >= 3 or not prims:
        print(f"[gates] form reach: {len(forms)} named component(s) — {', '.join(forms) or 'none'}")
        return None
    print(f"[gates] form reach: {len(forms)} of {len(_ca.FORM_GUARANTEE)} named components "
          f"({', '.join(forms) or 'none'}); the rest of {cands[0].name} is raw box/text.")
    print("        Bespoke composition is legitimate and often right — but confirm it was CHOSEN, "
          "not defaulted to: `python3 scripts/sigs.py --list` (or --search <shape>) is one call and "
          "answers it. Measured cost of skipping it once: a meter_bar rebuilt out of two boxes.")
    # Returning the count is what turns this from a line nobody reads into a question somebody
    # answers. It still never blocks on the NUMBER — only on the absence of a decision. See the
    # `form_reach` waiver in the gate below.
    return {"forms": forms, "total": len(_ca.FORM_GUARANTEE), "script": cands[0].name}


def _report_plan_files(pptx_path):
    """Plan files left in the deliverable folder — the checkpoint that became a file.

    `checkpoint-convention.md` says it plainly: the checkpoint artifact is a compact table PASTED
    INTO THE CONVERSATION, and `content-plan.md` / `design-plan.md` must not be written into the
    deliverable folder — the conversation is the record, and a folder the user opens should hold
    the deck, not the working notes that produced it.

    That rule lived only as one sentence inside a reference file, which is the position most
    likely to be skipped: nothing anywhere reported a plan file, so writing one cost nothing and
    the user found the clutter instead of a gate. Advisory rather than blocking — a user may have
    ASKED for plan files, and that carve is in the same sentence — but it is now said out loud at
    the moment the folder is handed over.
    """
    try:
        d = Path(pptx_path).parent
        stray = sorted(p.name for p in d.glob("*.md")
                       if p.name.lower() in ("content-plan.md", "design-plan.md",
                                             "content_plan.md", "design_plan.md"))
    except Exception:
        return
    if stray:
        print("[gates] plan files in the deliverable folder: %s — the checkpoint artifact belongs "
              "in the conversation, not on disk (checkpoint-convention.md). Delete them unless the "
              "user asked for plan files." % ", ".join(stray))


def _report_palette_drift(pptx_path, declared):
    """Name the slides where deckkit's OWN default accents survived into a deck with its own palette.

    WHY. `set_palette()` exists because a component's colour defaults BIND AT IMPORT — SKILL.md
    says so ("a bare `deckkit.MAGENTA = ...` does NOT re-theme components whose signature default
    binds at import"). The natural build script does not call it: it defines its palette as local
    constants and passes them where the API takes a colour. Every component that takes one
    IMPLICITLY then keeps deckkit blue or magenta.

    Measured on a real 10-slide build whose declared palette was a single bound teal: `title_bar`
    drew its accent rule in deckkit BLUE on all eight interior slides and `bottom_callout` set its
    label in deckkit MAGENTA — two foreign hues on a deck whose entire argument was one colour
    meaning one thing. Zero hard findings, zero warnings, every hand-off gate passed. The
    semantic-colour contract is a required plan FIELD and nothing compared it to the pixels.

    Deliberately narrow: it looks only for deckkit's own shipped constants, not for "any hue not in
    the palette". A generic scan would flag every photo, chart theme and template colour; this one
    answers a bounded question — did the LIBRARY's defaults leak past the deck's own choices? —
    which is the failure that actually happens. Prints, never dies: a deck may legitimately keep
    one deckkit hue if it declared it.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import deckkit as dk
        import lint_deck as _ld
        from pptx import Presentation
    except Exception:
        return
    want = set(re.findall(r"[0-9A-Fa-f]{6}", json.dumps(declared) if not isinstance(declared, str)
                          else declared))
    want = {w.upper() for w in want}
    # deckkit's shipped accent constants — the ones a component reaches for when the caller passes
    # nothing. Neutrals (DEEP/SLATE/MUTE/WHITE/TINT/LIGHT) are excluded on purpose: they are the
    # library's ink and paper, and a deck that keeps them has not lost its identity.
    lib = {}
    for name in ("BLUE", "MAGENTA", "TEAL", "GOLD", "STEEL", "VIOLET", "GREEN"):
        v = getattr(dk, name, None)
        if v is not None:
            lib[str(v).upper()] = name
    leaked = {h: n for h, n in lib.items() if h not in want}
    if not want or not leaked:
        return
    try:
        prs = Presentation(pptx_path)
        sw = prs.slide_width / 914400.0
        sh = prs.slide_height / 914400.0
    except Exception:
        return
    hits = {}
    for i, slide in enumerate(prs.slides, 1):
        try:
            boxes = _ld._boxes(slide, sw, sh)
        except Exception:
            continue
        for b in boxes:
            for key in ("fill", "line", "ink"):
                v = b.get(key)
                h = str(v).upper() if v else ""
                if len(h) == 6 and h in leaked:
                    hits.setdefault(leaked[h], set()).add(i)
    if not hits:
        return
    print("[gates] palette drift: deckkit's own default accent(s) survived into a deck that "
          "declared its own palette —")
    for name, pages in sorted(hits.items()):
        print("        {} ({}) on slide(s) {}".format(
            name, getattr(dk, name), ", ".join(str(p) for p in sorted(pages))))
    print("        These are component defaults bound at IMPORT, not choices: title_bar's accent "
          "rule, a callout's label, a marker. Call deckkit.set_palette(...) once after import so "
          "the whole component set follows the deck, or pass the colour explicitly at each call.")
    print("        (A hue you DID choose is not drift — declare it in the design plan's `palette` "
          "field and this goes quiet.)")


def _report_icon_waiver(pptx_path, fam):
    """Name the slides that contradict an `icon_family: none - <reason>` waiver.

    WHY. The waiver is meant to stay satisfiable — a deliberately icon-free deck is a real choice.
    But the reason is free text written at PLAN time, before any slide exists, and nothing ever
    revisits it. Measured on a real build: the plan said 'none — 概念性内容,图标会变装饰', and the
    deck then shipped three category slides (church vs market · pronk vs vanitas · four genres)
    that are exactly the entity-rich case SKILL.md calls a design must. The waiver was not a lie
    when written; it was never re-tested against what got built. So test it against the built file.

    A peer group = 3+ text boxes at the same size, aligned in a row or a column: the shape of a
    category set. It over-counts (tables, timelines), which is why this prints slides and does not
    die — but naming '2, 6, 7' is much harder to wave past than a general nag.
    """
    if not isinstance(fam, str):
        return
    if not fam.strip().lower().startswith("none"):
        # THE OTHER DIRECTION, and it is the one the incident actually took. This guard was
        # installed because "a deck shipped with ZERO icons through every automated gate" — and it
        # then checked only `icon_family: none` against a deck that HAS icons, i.e. a stale record
        # in the harmless direction. A deck declaring `icon_family: lucide-outline, 24 icons` and
        # shipping none passed silently: the guard installed for the incident could not fire on it.
        #
        # Counted by IMAGE IDENTITY, not by position+size. The geometry signature below is a chrome
        # detector — it asks "does this rectangle recur?" — and a real icon SET is many different
        # pictures at similar sizes, so counting distinct geometries miscounts it. Hashing the blob
        # answers the question actually being asked: how many distinct small pictures are in here?
        try:
            from pptx import Presentation as _P1
            import hashlib as _h1
            _prs1 = _P1(str(pptx_path))
            _blobs, _per = {}, {}
            for _i1, _s1 in enumerate(_prs1.slides):
                for _sh1 in _s1.shapes:
                    try:
                        if _sh1.width / 914400.0 >= 1.2 or _sh1.height / 914400.0 >= 1.2:
                            continue
                        # `.image` raises on any non-picture shape, which is the test — no
                        # MSO_SHAPE_TYPE import needed, and nothing silently swallows a NameError.
                        _k1 = _h1.sha256(_sh1.image.blob).hexdigest()[:16]
                    except Exception:
                        continue
                    _blobs[_k1] = _blobs.get(_k1, 0) + 1
                    _per.setdefault(_k1, set()).add(_i1)
            _n_sl1 = len(_prs1.slides) or 1
            # A logo is ONE picture stamped on most slides; an icon set is many pictures on a
            # minority. Drop any blob appearing on more than half the deck.
            _icons = {k: v for k, v in _blobs.items() if len(_per[k]) <= max(2, 0.5 * _n_sl1)}
            if not _icons:
                print("[gates] icon record: the plan declares `icon_family: {}` but the deck "
                      "contains NO icon-sized picture that is not deck chrome. The record and the "
                      "file disagree — either the icons were never built, or the field is stale. "
                      "This is the direction the guard was written for: a deck once shipped with "
                      "zero icons through every automated gate.".format(fam.strip()[:60]))
        except Exception:
            pass
        return
    # Caught on its first run: a rebuild ADDED icons and the plan record still said `none`, because
    # nothing ever compares the record to the file. Say so before looking for peer groups — a record
    # that disagrees with the deck makes every other field in it suspect too.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import lint_deck as _ld0
        from pptx import Presentation as _P0
        _prs0 = _P0(str(pptx_path))
        _sw0, _sh0 = _prs0.slide_width / 914400.0, _prs0.slide_height / 914400.0
        # A repeated LOGO is icon-SIZED and would be miscounted as an icon family — measured: a
        # deck stamping one 0.6in mark on 8 slides counted 8 "icons" and would have been told its
        # record was stale. Chrome repeats at the same geometry; content does not. Drop any picture
        # whose position+size recurs on 3+ slides before counting.
        _sig, _n_sl = {}, len(_prs0.slides) or 1
        for _s0 in _prs0.slides:
            for _b0 in _ld0._boxes(_s0, _sw0, _sh0):
                if _b0.get("pic") and not _b0.get("bg") and _b0["w"] < 1.2 and _b0["h"] < 1.2:
                    _k = (round(_b0["l"], 1), round(_b0["t"], 1), round(_b0["w"], 1), round(_b0["h"], 1))
                    _sig[_k] = _sig.get(_k, 0) + 1
        # Chrome repeats on MOST slides; a content icon set appears on a minority of them. A bare
        # ">=3 occurrences = chrome" rule was wrong in both directions (measured): it cleared a
        # 3-icon row that recurred on 3 of 8 slides, which is content, while a logo on 8 of 8 is not.
        n_ic = sum(c for c in _sig.values() if c <= max(2, 0.5 * _n_sl))
        if n_ic >= 2:
            print(f"[gates] icon waiver: the plan says `icon_family: none` but the deck contains "
                  f"{n_ic} icon-sized image(s) — the record is stale. Update it to the family you "
                  f"actually shipped; a plan that disagrees with the file is not a record of anything.")
            return
    except Exception:
        pass
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import lint_deck as _ld
        from pptx import Presentation as _P
        prs = _P(str(pptx_path))
        sw, sh = prs.slide_width / 914400.0, prs.slide_height / 914400.0
    except Exception:
        return
    hits = []
    for i, s in enumerate(prs.slides, 1):
        try:
            bx = [b for b in _ld._boxes(s, sw, sh) if b.get("text") and not b.get("bg")]
        except Exception:
            continue
        groups = {}
        for b in bx:
            if not (b.get("full") or "").strip() or len((b.get("full") or "").split()) > 8:
                continue                        # a peer LABEL is short; a paragraph is not a peer
            groups.setdefault(round(b.get("size", 0) or 0, 1), []).append(b)
        for _sz, g in groups.items():
            if len(g) < 3:
                continue
            # ROWS ONLY, and they must actually span the page. A vertical stack of short lines at one
            # left edge is a bullet list, not a category set — counting columns made every deck with
            # a 3-line body block "entity-rich" (measured: fired on all 8 slides of a fixture whose
            # only pictures were one repeated logo). A category set reads ACROSS: 3+ peers sharing a
            # baseline, spread over at least half the canvas.
            for anchor in g:
                row = [b for b in g if abs(b["t"] - anchor["t"]) < 0.15]
                if len(row) < 3:
                    continue
                spread = max(b["l"] for b in row) - min(b["l"] for b in row)
                if spread >= 0.45 * sw:
                    hits.append(i)
                    break
            if hits and hits[-1] == i:
                break
    if len(hits) >= 2:
        print(f"[gates] icon waiver: `icon_family: none` but slides {hits} carry parallel label sets "
              f"(3+ peers in a row/column) — the entity-rich case SKILL.md calls a design must.")
        print("        ⚠ Re-decide NOW against the built slides, not against the plan sentence: either "
              "give these a family, or restate in the hand-off why THESE specific slides are better "
              "without one. A plan-time waiver that was never re-tested is how a deck ships zero icons.")


def _tail(text, limit=4000):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return "...<truncated>...\n" + text[-limit:]


# Exactly what a render writes: slide01.png … slideNN.png and the two bookend thumbnails. Used to
# decide what may be deleted when the out dir is shared with the user's own files.
_RENDER_PNG = re.compile(r"^(slide\d{2,}|thumb_first|thumb_last|contact(_\d{2})?)\.png$")


def _rels_targets(xml_bytes, base_dir):
    """Parse a .rels part -> {rId: normalized package path}.

    Parsed as XML, not by regex: OOXML allows the Id/Target attributes in either order, and a
    Target may be absolute ("/ppt/slides/slide1.xml"). Getting this wrong is not a cosmetic bug —
    a rId that fails to resolve silently drops a slide from the deck order, which shifts every
    index after it and writes real slides into the wrong PNG filenames.
    """
    import posixpath
    import xml.etree.ElementTree as ET
    out = {}
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    for rel in root:
        rid = rel.get("Id")
        tgt = rel.get("Target")
        if not rid or not tgt or (rel.get("TargetMode") or "") == "External":
            continue
        if tgt.startswith("/"):
            out[rid] = tgt.lstrip("/")
        else:
            out[rid] = posixpath.normpath(posixpath.join(base_dir, tgt))
    return out


def _slide_fingerprints(pptx):
    """One content hash per slide, in deck order, plus any reason the deck cannot be diffed.

    Each slide's hash covers its own XML, its rels, the BYTES of every media part it references,
    and a DECK-GLOBAL digest (presentation.xml, theme, masters, layouts and the media those
    reference) — so a re-cropped photo, a swapped plate, a new theme or a different canvas size all
    count as changes.

    Returns (hashes, blockers). `blockers` is a list of human-readable reasons the caller must fall
    back to a full render; it is never a soft signal. Anything that makes the slide->page mapping
    uncertain belongs here, because a wrong mapping writes a real slide into another slide's PNG.
    """
    import hashlib
    import zipfile
    blockers = []
    with zipfile.ZipFile(pptx) as z:
        names = set(z.namelist())
        _part_cache = {}

        def part_digest(name):
            """Hash a package part ONCE. A background plate shared by every slide was previously
            re-read and re-hashed per referencing slide, making cost O(slides x media-bytes)."""
            d = _part_cache.get(name)
            if d is None:
                d = hashlib.sha256(z.read(name)).digest()
                _part_cache[name] = d
            return d
        pres_rels = _rels_targets(z.read("ppt/_rels/presentation.xml.rels"), "ppt") \
            if "ppt/_rels/presentation.xml.rels" in names else {}

        # ---- deck-global digest -------------------------------------------------------
        # docProps/* is excluded on purpose: core.xml carries a modified-timestamp that changes on
        # every save, which would force a full render every time and delete the feature.
        # ppt/media and ppt/notesSlides are excluded here — slide media is covered per-slide below,
        # and notes never reach a rendered pixel. But media referenced by a LAYOUT, MASTER or THEME
        # is deck-global and IS folded in: swapping a master's background image in place changes no
        # slide's XML, so without this the whole deck would render stale under "no slide changed".
        gh = hashlib.sha256()
        global_media = set()
        for n in sorted(names):
            if not n.startswith("ppt/"):
                continue
            if n.startswith(("ppt/slides/", "ppt/media/", "ppt/notesSlides/")):
                continue
            gh.update(n.encode())
            gh.update(z.read(n))
            if n.startswith(("ppt/slideLayouts/_rels/", "ppt/slideMasters/_rels/", "ppt/theme/_rels/")):
                base = n.rsplit("/_rels/", 1)[0]
                for tgt in _rels_targets(z.read(n), base).values():
                    if "/media/" in "/" + tgt:
                        global_media.add(tgt)
        for m in sorted(global_media):
            if m in names:
                gh.update(m.encode())
                gh.update(part_digest(m))
        global_digest = gh.digest()

        # ---- deck order ---------------------------------------------------------------
        import re
        pres = z.read("ppt/presentation.xml").decode("utf-8", "replace")
        rids = re.findall(r'<p:sldId[^>]*r:id="([^"]+)"', pres)
        order = [pres_rels.get(r) for r in rids]
        if any(t is None for t in order):
            blockers.append("a slide reference could not be resolved in presentation.xml.rels")
            order = [t for t in order if t]

        fps = []
        for sname in order:
            if sname not in names:
                # Never hash a missing part as b"" — every affected slide would collapse to the
                # same constant and real edits would stop registering, forever.
                blockers.append("slide part missing from the package: {}".format(sname))
                continue
            h = hashlib.sha256()
            h.update(global_digest)
            body = z.read(sname)
            h.update(body)
            if b'type="slidenum"' in body:
                # An auto slide-number field renumbers itself inside a subset.
                blockers.append("deck uses auto slide-number fields")
            if re.search(rb'<p:sld\b[^>]*\bshow="0"', body):
                # LibreOffice DROPS hidden slides from the PDF, so PDF page N is no longer deck
                # slide N — on the full path too. Verified with a 4-slide deck: one hidden slide
                # produced a 3-page PDF.
                blockers.append("deck has hidden slides")
            rname = sname.replace("slides/", "slides/_rels/") + ".rels"
            rel_bytes = z.read(rname) if rname in names else b""
            h.update(rel_bytes)
            for tgt in sorted(_rels_targets(rel_bytes, "ppt/slides").values()):
                if "/media/" in "/" + tgt and tgt in names:
                    h.update(tgt.encode())
                    h.update(part_digest(tgt))
            fps.append(h.hexdigest())

        if len(fps) != len(rids):
            blockers.append("deck order could not be fully resolved ({} of {} slides)".format(
                len(fps), len(rids)))
    # de-dup, order-stable
    seen, uniq = set(), []
    for b in blockers:
        if b not in seen:
            seen.add(b); uniq.append(b)
    return fps, uniq


def _subset_pptx(src, keep_idx, dest):
    """Copy `src` keeping ONLY the 0-indexed slides in `keep_idx` (order preserved).

    Deleting sldId entries is safe and cheap; the orphaned parts stay in the package and
    LibreOffice ignores them. Verified pixel-identical to the same slide rendered from the
    full deck, which is what makes the fast path trustworthy rather than merely fast.
    """
    import shutil
    from pptx import Presentation
    shutil.copy(src, dest)
    prs = Presentation(dest)
    lst = prs.slides._sldIdLst
    for i, sid in enumerate(list(lst)):
        if i not in keep_idx:
            lst.remove(sid)
    prs.save(dest)
    return dest


def _profile_pool_dir():
    """Where the reusable LibreOffice profiles live. Same convention as the icon cache."""
    env = os.environ.get("SLIDE_MAKER_CACHE")
    if env:
        return os.path.join(env, "lo-profiles")
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "slide-maker", "lo-profiles")


PROFILE_POOL_SLOTS = 8       # more concurrent renders than that, and the extras go throwaway


class _Profile(object):
    """A LibreOffice user profile to render with, plus how to let it go.

    Building a user profile from scratch is most of what a headless `--convert-to` run spends
    its time on: measured 3.71s per export with a fresh profile against 2.16s once the profile
    already exists — ~42% of the export, on every render, spent recreating the same directory.

    The old code paid that every time by design, and the design had two real reasons, both of
    which this pool has to keep:

      1. **Parallel renders must not fight.** The large-deck section fan-out renders several
         decks at once, and two `soffice` processes pointed at ONE profile collide: measured,
         one of the pair exits 1 having written no PDF at all.
      2. **The user's own LibreOffice may be open.** A render must not touch the GUI's profile.

    So this is a POOL, not a shared singleton: N private slots, each held under an exclusive
    `flock` for the duration of one render. Concurrent renders land on different slots; a slot
    is only ever used by one process at a time, which is exactly the invariant a throwaway
    profile gave for free. Nothing here goes near LibreOffice's default profile.

    When every slot is busy, or the platform has no `flock` (Windows), or anything at all goes
    wrong, we hand back a throwaway profile — i.e. precisely the old behaviour. The pool is an
    optimization; it is never the reason a deck fails to render.
    """

    def __init__(self, path, pooled, lock_fh=None):
        self.path = path
        self.pooled = pooled
        self._lock_fh = lock_fh

    def release(self, discard=False):
        if not self.pooled:
            shutil.rmtree(self.path, ignore_errors=True)
            return
        if discard:
            # This slot was in hand for a render that failed. It may be the cause (a profile
            # torn by a killed process, or one written by a different LibreOffice version), so
            # do not leave it for the next run to trip over.
            shutil.rmtree(self.path, ignore_errors=True)
        if self._lock_fh is not None:
            try:
                import fcntl
                fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                self._lock_fh.close()
            except Exception:
                pass


def _acquire_profile():
    """Take a pooled profile slot, or fall back to a throwaway one."""
    if os.environ.get("SLIDE_MAKER_NO_PROFILE_POOL"):
        return _Profile(tempfile.mkdtemp(prefix="lo_render_"), pooled=False)
    try:
        import fcntl                                    # POSIX only; Windows keeps the old path
    except ImportError:
        return _Profile(tempfile.mkdtemp(prefix="lo_render_"), pooled=False)
    try:
        root = _profile_pool_dir()
        os.makedirs(root, exist_ok=True)
        for i in range(PROFILE_POOL_SLOTS):
            slot = os.path.join(root, "slot{:02d}".format(i))
            os.makedirs(slot, exist_ok=True)
            # The lock file lives BESIDE the slot, not inside it: `release(discard=True)` deletes
            # the slot tree, and unlinking the file we hold the lock on would drop the lock.
            fh = open(os.path.join(root, "slot{:02d}.lock".format(i)), "a+")
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                fh.close()
                continue                                # another render holds this slot
            return _Profile(slot, pooled=True, lock_fh=fh)
    except Exception:
        pass
    return _Profile(tempfile.mkdtemp(prefix="lo_render_"), pooled=False)


def _render_pdf(soffice, src, outdir):
    """pptx -> pdf via a private LibreOffice profile, into an EMPTY private directory.

    `outdir` must not already contain `<src-stem>.pdf`. Rendering into a directory that may hold a
    previous PDF is how a FAILED conversion gets read back as success: the caller checks only that
    the file exists, and a stale one satisfies that. Reproduced with real LibreOffice on a deck it
    refuses to convert — the run printed "rendered N slides" and exit 0 over untouched output.
    Returns (pdf_path, result, cmd); the caller must check `result.returncode`.

    The profile comes from `_acquire_profile()` — a pooled, warm one when a slot is free, a
    throwaway otherwise. On a non-zero exit with a POOLED profile we throw that slot away and
    retry ONCE on a throwaway, so a poisoned slot degrades into the old behaviour instead of
    into a failed render. A genuine bad deck fails both times and is reported as before.
    """
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")

    def _once(profile):
        cmd = [soffice, "-env:UserInstallation=" + Path(profile.path).as_uri(),
               "--headless", "--convert-to", "pdf", "--outdir", outdir, src]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=300)
        except subprocess.TimeoutExpired:
            profile.release(discard=True)
            die("LibreOffice render exceeded 300s and was killed — the .pptx may be malformed or "
                "hostile (e.g. a decompression bomb). Nothing was produced from {}.".format(src))
        return result, cmd

    profile = _acquire_profile()
    result, cmd = _once(profile)
    if result.returncode != 0 and profile.pooled:
        profile.release(discard=True)
        print("note: render failed on a pooled LibreOffice profile — discarding it and retrying "
              "with a fresh one", file=sys.stderr)
        retry = _Profile(tempfile.mkdtemp(prefix="lo_render_"), pooled=False)
        result, cmd = _once(retry)
        retry.release()
        return (pdf, result, cmd)
    profile.release()
    return (pdf, result, cmd)


# --- parallel rasterization -------------------------------------------------------------
# Rasterizing is the one render stage that is embarrassingly parallel: each page is an
# independent draw into its own file. It is also, on an image-heavy deck, the stage that
# actually costs something.
#
# Two things about the shape below are load-bearing, both measured rather than reasoned:
#
#  1. **Chunk contiguously; open the PDF ONCE per worker.** The obvious version — one task
#     per page — was measured at 18.5s against 2.9s serial on a 16-page image deck: 6.5x
#     SLOWER, because every task re-opens and re-parses the whole PDF. Chunked, the same
#     deck rasterizes in 1.27s (4 workers).
#  2. **Never let this fail a render.** It is an optimization on a step that already worked.
#     Any failure — no process pool in a locked-down sandbox, a worker dying, pickling
#     trouble — returns False and the caller runs the original serial loop. A deck that
#     renders slower is a nuisance; a deck that does not render is a broken run.
#
# Verified byte-identical to the serial loop (sha256 over every PNG, text and image decks).
# `SLIDE_MAKER_RENDER_WORKERS=1` forces the serial path.
RASTER_MIN_PAGES = 8          # below this the pool costs more than the pages save
RASTER_MAX_WORKERS = 4        # measured: 4 workers ~= 8 workers (1.27s vs 1.25s), half the RAM
# Page COUNT was the wrong gate on its own: what a worker pool saves is DECODE work, and a page's
# decode cost is set by its weight, not by how many neighbours it has. Measured serial rasterize:
#
#     18-page text/CJK deck   2.5-5.5 KB/page,  0 images   0.05-0.08s   (2.9-4.7 ms/page)
#     16-page image deck       84.5 KB/page,   16 images   0.47s        (29.3 ms/page)
#
# Fanning out costs ~70 ms in process starts and `import fitz` per worker, so on the text decks the
# pool spent more than the whole job — measured +2.1% wall clock, i.e. the optimization ran and made
# the render slower. On the image deck it is a clear -11.4%. PDF bytes-per-page separates the two by
# ~15x, which is a wide enough margin that a threshold in the middle is not a tuned constant: below
# it there is not enough decode work to pay a single process start, whatever the page count.
# This changes only WHICH path runs; both are already asserted byte-identical by
# tests/test_render_parallel.py, so a mis-set threshold costs milliseconds and never a wrong PNG.
RASTER_MIN_BYTES_PER_PAGE = 20 * 1024


def _rasterize_chunk(args):
    """Render a contiguous run of pages in one worker. Module-level so it is picklable.

    `thumbs` maps a page index this chunk owns to a thumbnail name. The bookend thumbnails
    are produced HERE, by the worker that already rasterized that page at 2x, and only after
    the whole chunk is done — because a page's thumbnail is not independent of whether that
    page was rendered at 2x first. Measured: `thumb_first` of an image-heavy deck hashes
    differently when rendered from a fresh document than when rendered after the 2x pass
    (both individually deterministic). MuPDF is scaling a cached decode in one case and
    doing a scaled decode in the other. So the thumbnail follows its page into the worker,
    which keeps the ordering — 2x pass, then thumbnails — byte-for-byte what it has always
    been. Rendering them in the parent instead silently changes two PNGs the critic looks at.
    """
    pdf, idxs, out, thumbs = args
    import fitz
    doc = fitz.open(pdf)
    try:
        for i in idxs:
            doc[i].get_pixmap(matrix=fitz.Matrix(2, 2)).save(
                os.path.join(out, "slide{:02d}.png".format(i + 1)))
        for i, name in sorted(thumbs.items()):
            page = doc[i]
            zoom = 240.0 / max(1.0, page.rect.width)
            page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(
                os.path.join(out, name + ".png"))
    finally:
        doc.close()
    return len(idxs)


def _raster_workers(n_pages, pdf=None):
    """How many workers to rasterize `n_pages` with — 1 means 'use the serial loop'.

    `pdf` is optional so an explicit `SLIDE_MAKER_RENDER_WORKERS` and the page-count floor still
    answer without it; when it is given, page WEIGHT gets the final say (see
    RASTER_MIN_BYTES_PER_PAGE). An unreadable size is treated as heavy — the pool is the safe
    guess there, since being wrong costs ~70 ms and the serial path is the fallback anyway.
    """
    env = os.environ.get("SLIDE_MAKER_RENDER_WORKERS")
    if env:
        try:
            return max(1, min(int(env), n_pages))
        except ValueError:
            pass                                  # a typo'd override must not break the render
    if n_pages < RASTER_MIN_PAGES:
        return 1
    if pdf is not None:
        try:
            if os.path.getsize(pdf) / float(n_pages) < RASTER_MIN_BYTES_PER_PAGE:
                return 1                          # not enough decode work to pay a process start
        except Exception:
            pass
    try:
        cores = os.cpu_count() or 1
    except Exception:
        cores = 1
    return max(1, min(RASTER_MAX_WORKERS, cores - 1, n_pages))


def _rasterize_parallel(pdf, n_pages, out):
    """Try to rasterize all pages across worker processes. Returns True if it wrote them all.

    Returns False (writing nothing, or leaving a partial set the serial loop then overwrites)
    whenever the fast path is unavailable or fails, so the caller can fall back.
    """
    workers = _raster_workers(n_pages, pdf)
    if workers < 2:
        return False
    per = -(-n_pages // workers)
    parts = [list(range(k * per, min(n_pages, (k + 1) * per))) for k in range(workers)]
    parts = [p for p in parts if p]
    # Hand each bookend thumbnail to whichever chunk owns its page (see _rasterize_chunk).
    want = {0: "thumb_first", n_pages - 1: "thumb_last"} if n_pages else {}
    jobs = [(pdf, p, out, {i: nm for i, nm in want.items() if i in p}) for p in parts]
    try:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=len(parts)) as ex:
            done = list(ex.map(_rasterize_chunk, jobs))
    except Exception as exc:
        print("note: parallel rasterize unavailable ({}) — using the serial path".format(exc),
              file=sys.stderr)
        return False
    if sum(done) != n_pages:
        # A worker returned but wrote fewer pages than it was given. Do not trust a partial
        # set: say so and let the serial loop rewrite every page.
        print("note: parallel rasterize covered {}/{} pages — redoing serially".format(
            sum(done), n_pages), file=sys.stderr)
        return False
    return True


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


GATES_FILE = ".deck-gates.json"


def _deck_slide_count(pptx):
    """How many slides the deck ACTUALLY has — the number a coverage claim is checked against.

    Deliberately fails loud rather than returning 0: a count of zero would make every coverage
    claim vacuously complete, which is the failure mode this number exists to close.
    """
    from pptx import Presentation
    try:
        return len(Presentation(pptx).slides)
    except Exception as exc:
        die("cannot read {} to count its slides ({}). The coverage gate compares the critic's "
            "`slides_opened` against the real deck, so an unreadable deck is not a pass."
            .format(pptx, exc))


CRITIC_WAIVER_KINDS = {
    "no-dispatch-on-host":
        "the runtime cannot dispatch a subagent (record it in the capability ledger too)",
    "already-reviewed-minor-edit":
        "a 1-2 slide edit to a deck that already passed its loop",
    "user-waived":
        "the user was asked and chose to ship over it",
    "external-deck":
        "a deck this skill did not author (redesign diagnosis / critique-only run)",
    # The loop RAN and did not converge. Every kind above describes a loop that was SKIPPED, so a
    # deck that reached its round cap with majors still open had no honest route: `user-waived`
    # asserts "the user was asked and chose to ship over it", which is a claim about a conversation
    # that did not happen. Measured on a real build — the builder's words were "the four options
    # force either a lie or a red gate", and it correctly left the gate red rather than fabricate
    # one. A record with no state for the commonest non-consent ending is a record that teaches
    # people to lie to it.
    "cap-reached-majors-open":
        "the loop RAN to its round cap and majors remain open (needs `open` + `surfaced_to_user`)",
}
# Every message that offers the categories renders them from this dict. They were hand-copied into
# four places and the fifth kind reached none of them, so the file that ACCEPTED
# `cap-reached-majors-open` also told every reader it did not exist — which is the same lie the
# fifth kind was added to prevent.
CRITIC_WAIVER_LIST = " | ".join(sorted(CRITIC_WAIVER_KINDS))


def _critic_waiver_menu(indent="    "):
    return "\n".join("{}{:28s} {}".format(indent, k, v)
                     for k, v in sorted(CRITIC_WAIVER_KINDS.items()))


def _critic_effort(critic):
    """How much reviewing happened, said in the unit the record can actually back.

    `rounds` is the only hand-typed field in the critic block — `validate_review.py --record`
    preserves one but never derives it, because nothing inside a review file says which round it
    belongs to. `reviews_seen` is the machine-counted one. These lines used to print
    `rounds` with a bare `"?"` fallback, which reported "consented after ? round(s)" on every
    tool-written record: the number the tool DOES know was sitting in the same dict, unread.
    """
    if isinstance(critic.get("rounds"), int):
        return "{} round(s)".format(critic["rounds"])
    if isinstance(critic.get("reviews_seen"), int):
        return "{} review(s) [rounds not recorded]".format(critic["reviews_seen"])
    return "an unrecorded number of rounds"


def check_handoff_gates(pptx, mode="presented", gate_check=False):
    """Refuse --deliverables until the quality gates have actually run.

    The gates that guard a deck's quality — the design plan, the independent critic, the
    primary-source spot-check — are all *self-reported prose artifacts*. The model that skipped
    them is the same model that writes the hand-off note claiming they happened, so skipping is
    invisible: the note reads identically either way. This skill's own enforcement invariant
    ranks prose last for exactly that reason (deterministic lint > required-field > checklist >
    prose), yet these three sat at the bottom of it.

    So put the check where the incentive is. `--deliverables` produces the PDF and the preview
    page — the artifacts the user actually asked for — which makes it the one step nobody skips.
    Requiring evidence *here* costs nothing on a deck that ran its loop and blocks the shortcut on
    one that didn't.

    Evidence lives in `<deck-dir>/.deck-gates.json`:

        {"critic": {"verdict": "consent", "rounds": 2, "review": "reviews/r2.json"},
         "provenance": {"claims": [{"claim": "<the claim>", "verdict": "CONFIRMED",
                                    "url": "https://<primary source>"}]}}

    (A summary tally like {"checked": 87} is REJECTED on purpose — a tally is written by the same
    pass that would have skipped the refutation.)

    A gate may be waived — quick decks exist — but a waiver is a written reason that travels with
    the deck AND names which kind of skip it is, not a silence:

        {"critic": {"waived": "1-slide fix to an already-reviewed deck",
                    "waived_category": "already-reviewed-minor-edit"}}

    Set SLIDE_MAKER_SKIP_GATES=1 to bypass entirely (CI smoke tests, throwaway renders).
    """
    if os.environ.get("SLIDE_MAKER_SKIP_GATES"):
        # Say so, and never let the caller print a pass. Measured: with this variable set on a deck
        # carrying NO .deck-gates.json at all, `--gate-check` exited 0 under the line "all hand-off
        # gates pass — the deck may be handed over". A bypass is legitimate for CI smoke renders and
        # throwaway previews; asserting that skipped gates PASSED is the one thing it must not do,
        # because that sentence is the artifact a hand-off note is written from.
        print("[gates] SKIPPED — SLIDE_MAKER_SKIP_GATES=1 is set. NOTHING was checked: not the "
              "critic record, not the design plan, not provenance, not density.")
        if gate_check:
            die("`--gate-check` is the hand-off gate itself, so bypassing it has no honest meaning. "
                "Unset SLIDE_MAKER_SKIP_GATES (it exists for CI smoke renders), or record a written, "
                "classified waiver in .deck-gates.json — a waiver is visible, an env var is not.")
        return
    path = os.path.join(os.path.dirname(os.path.abspath(pptx)) or ".", GATES_FILE)
    if not os.path.isfile(path):
        die("--deliverables is the hand-off run, and this deck has no record that its quality "
            "gates ran.\n"
            "  Missing: {}\n\n"
            "  The independent critic (Step 5) is the one that cannot be self-certified — you are "
            "not the final judge of your own deck.\n"
            "  Let the loop WRITE it, so the record is evidence and not a claim — one flag on a\n"
            "  step you already run before acting on any review:\n\n"
            "    python3 scripts/validate_review.py critic <review.json> --record {}\n\n"
            "  (that fills `critic` from the review itself, with its path + sha256, and the gate\n"
            "  re-reads it). Then add the two blocks only you can supply. Full shape:\n\n"
            '    {{"critic": {{"verdict": "consent", "rounds": 2}},\n'
            '     "design_plan": {{"boldness": "balanced+", "signature_move": "<the one risk>",\n'
            '                     "carried_by": [4, 6, 8], "form_ledger": "<family tally>",\n'
            '                     "icon_family": "<family | none - reason>",\n'
            '                     "palette": "<FILL vs TEXT-safe split, per palette_audit.py>",\n'
            '                     "type_scale": {{"display": 34, "title": 24, "body": 14}},\n'
            '                     "signature_proof": {{"slide": 6, "png": "render/slide06.png"}}}},\n'
            '     "provenance": {{"claims": [{{"claim": "<the claim>", "verdict": "CONFIRMED",\n'
            '                                "url": "https://<primary source>"}}]}}}}\n\n'
            "  (A summary tally like {{\"checked\": 87}} is REJECTED on purpose — a tally is "
            "written by the same pass that would have skipped the refutation.)\n\n"
            "  A gate you deliberately skipped is waived in writing AND CLASSIFIED, not omitted:\n\n"
            '    {{"critic": {{"waived": "why this deck does not need a critic round",\n'
            '                 "waived_category": "{}",\n'
            '                 "inline_ran": true}}}}\n\n'
            "  (`inline_ran` is required only for `no-dispatch-on-host`; "
            "`cap-reached-majors-open` — the loop RAN and did not converge — additionally needs\n"
            "  `open` and `surfaced_to_user`.)\n\n"
            "  Renders without --deliverables are unaffected; iterate freely."
            .format(path, os.path.dirname(path) or ".", CRITIC_WAIVER_LIST))
    # --- resolve the DELIVERY once, above every gate that keys off it -------------------------
    # Measured divergence: the type-scale floor read a `delivery` key out of this JSON while the
    # density gate three blocks below read the raw `mode` the CLI flags set. One run could
    # therefore enforce two different deliveries, and a NOTE claiming "using the recorded value"
    # was true of only one of them. Resolve it here, once, and hand the SAME value to both.
    #
    # `mode` is what --selfread / --surface / --textheavy set. A recorded key wins over it, since
    # it travels with the deck; an unrecognised recorded value dies rather than silently falling
    # back to the presented floor, which would be a legibility floor quietly not applied.
    # BODY_FLOORS is deliberately the SAME three keys the Codex delivery gate validates, so the
    # two paths cannot disagree; `surface` is a CLI mode rather than a recorded delivery, and it
    # maps to `selfread` because a poster is read up close — the same reason --surface already
    # exempts it from the presented density budget.
    _KNOWN_DELIVERY = ("presented", "textheavy", "selfread", "surface")
    _DELIVERY_ALIAS = {"surface": "selfread"}
    try:
        gates = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        die("{} is not readable JSON: {}".format(path, e))

    _recorded = str(gates.get("delivery") or "").strip()
    if _recorded and _recorded not in _KNOWN_DELIVERY:
        die("`delivery` in {} is {!r}, which is not a delivery mode. One of: {}. An unrecognised "
            "value used to fall through to the presented floor, i.e. a legibility floor silently "
            "not applied to the deck it was recorded for."
            .format(path, _recorded, ", ".join(_KNOWN_DELIVERY)))
    if _recorded and mode != "presented" and _recorded != mode:
        print("[gates] NOTE: {} records delivery={!r} but you passed {!r} — using the RECORDED "
              "value for every gate in this run. Fix whichever is wrong; the two must not "
              "disagree about which deck this is.".format(path, _recorded, mode))
    delivery = _recorded or mode          # one of _KNOWN_DELIVERY, un-aliased

    critic = gates.get("critic") or {}
    if critic.get("waived"):
        # A waiver is legitimate — quick decks and hosts without subagent dispatch are real —
        # but an UNCLASSIFIED one is just a sentence, and the model that skipped the loop writes
        # the same sentence as the model that ran it. The Codex delivery gate has required a
        # distinct schema-valid review artifact per lens for a while; this path accepted any
        # string. Measured: a hand-typed waiver carried a whole deck through `all hand-off gates
        # pass` without an independent critic ever seeing it. So: name the category, and say
        # whether the lenses ran at all.
        WAIVER_KINDS = CRITIC_WAIVER_KINDS
        reason = critic["waived"]
        kind = critic.get("waived_category")
        if not isinstance(reason, str) or len(reason.strip()) < 24:
            die("`critic.waived` must be a written reason that travels with the deck, not a "
                "placeholder. Say what was skipped and why, in a sentence someone can disagree "
                "with later.")
        if kind not in WAIVER_KINDS:
            die("`critic.waived_category` must name WHICH kind of skip this is — an unclassified "
                "waiver is indistinguishable from never having run the loop. One of:\n"
                + _critic_waiver_menu()
                + "\n\n  If none of these fit, the honest move is to run the critic.")
        if kind == "cap-reached-majors-open":
            # This kind asserts the OPPOSITE of the others — that the work happened — so it carries
            # the evidence: which findings survived, and whether the user was actually told. Without
            # `open` it degrades into "we tried", which is what every other waiver already says.
            _open = critic.get("open")
            if not isinstance(_open, list) or not _open or not all(
                    isinstance(x, str) and x.strip() for x in _open):
                die("`waived_category: cap-reached-majors-open` must list the surviving findings in "
                    "`\"open\": [\"...\"]` — one short string each. This category claims the loop "
                    "RAN, so the deck owes the reader what it ran INTO; an empty list is a consent "
                    "verdict wearing a waiver's name.")
            if not isinstance(critic.get("surfaced_to_user"), bool):
                die("`waived_category: cap-reached-majors-open` must record "
                    "`\"surfaced_to_user\": true|false` — whether these open majors were put in "
                    "front of the user. Shipping over a known major is a decision; the record has "
                    "to say whose it was.")
        if kind == "no-dispatch-on-host" and "inline_ran" not in critic:
            die("`waived_category: no-dispatch-on-host` must also record `\"inline_ran\": true|false` "
                "— whether the content and design lenses were at least run inline. 'Ran inline in "
                "the author's own context' and 'was never reviewed' are different claims, and the "
                "hand-off note reads identically for both unless this file separates them.")
        print("[gates] critic WAIVED [{}] — NOT INDEPENDENTLY REVIEWED".format(kind))
        print("        {}".format(reason))
        if kind == "no-dispatch-on-host":
            print("        lenses run inline: {} — inline review is the author grading "
                  "themselves.".format("yes" if critic.get("inline_ran") else "NO"))
        print("        Say this in the hand-off note too; a waiver the user never sees is a "
              "silence.")
    elif critic.get("verdict") == "consent":
        # A record the model TYPED at hand-off is self-certification: the model that skipped the
        # loop writes the same JSON as the model that ran it. So when the record points at the
        # review artifact (validate_review.py --record puts it there), re-read that artifact and
        # verify it still says what the record claims. A hand-written record still passes — but it
        # is LABELLED self-reported, so the two are distinguishable instead of identical.
        src = critic.get("source")
        if src:
            if not os.path.isfile(src):
                die("`critic.source` points at {} — which does not exist. The gate re-reads the "
                    "review artifact rather than trusting the summary; restore the file, re-run "
                    "`validate_review.py critic <review.json> --record <deck-dir>`, or waive in "
                    "writing.".format(src))
            digest = critic.get("sha256")
            if digest and _sha256(src) != digest:
                die("`critic.source` ({}) has changed since it was recorded — the sha256 no longer "
                    "matches. Re-validate it with `validate_review.py critic <review.json> "
                    "--record <deck-dir>` so the record and the evidence agree.".format(src))
            try:
                review = json.load(open(src, encoding="utf-8"))
            except Exception as exc:
                die("`critic.source` ({}) is not readable JSON: {}".format(src, exc))
            if review.get("verdict") != "consent":
                die("the recorded verdict says consent, but the review at {} says {!r}. The "
                    "artifact wins.".format(src, review.get("verdict")))
            hard = [f for f in (review.get("findings") or [])
                    if isinstance(f, dict) and f.get("severity") in ("blocker", "major")]
            if hard:
                die("the review at {} consents while still carrying {} blocker/major finding(s) — "
                    "that is a contract violation (agents/critic.md: any blocker/major -> revise). "
                    "Fix them and re-review, or waive in writing.".format(src, len(hard)))
            # --- bind the coverage claim to the DECK, not just to the file --------------------
            # Until this ran, "verified" meant only "the artifact exists and still hashes to what
            # was recorded". Measured: a schema-valid review of a 15-slide deck declaring
            # slides_opened=[1] was accepted, recorded with a sha256, and printed as verified, and
            # every hand-off gate passed. `slides_opened` is the anti-skim field; nothing compared
            # it to the deck it claims to have read. SKILL.md Step 5 already tells the coordinator
            # to make this comparison by hand ("lists every slide in the critic's ASSIGNED scope —
            # whole deck for a sole critic; its section's range for a per-section critic"); the
            # Codex delivery gate already mechanises it. This is the shared path catching up.
            _cov = review.get("coverage") or {}
            _opened = {v for v in (_cov.get("slides_opened") or []) if isinstance(v, int)}
            _scope = _cov.get("scope")
            if isinstance(_scope, (list, tuple)) and len(_scope) == 2 \
                    and all(isinstance(v, int) for v in _scope):
                _expect = set(range(_scope[0], _scope[1] + 1))
                _what = "its declared scope (slides {}-{})".format(*_scope)
            else:
                _expect = set(range(1, _deck_slide_count(pptx) + 1))
                _what = "the whole deck ({} slides)".format(len(_expect))
            _missing = sorted(_expect - _opened)
            if _missing:
                die("the review at {} consents for {}, but `coverage.slides_opened` never lists "
                    "slide(s) {}{}.\n"
                    "  A critic can only judge what it opened, and consent on an unopened slide is "
                    "not a verdict — it is a gap the record renders as a pass.\n"
                    "  Re-dispatch the critic over the missing slides, or — for a per-section "
                    "critic — declare the range it was assigned:\n"
                    '      "coverage": {{"scope": [4, 9], "slides_opened": [4,5,6,7,8,9], ...}}'
                    .format(src, _what,
                            ", ".join(str(m) for m in _missing[:12]),
                            " (+{} more)".format(len(_missing) - 12) if len(_missing) > 12 else ""))
            print("[gates] critic consented after {} — verified against {} "
                  "(opened {}/{} slides)".format(
                      _critic_effort(critic), os.path.basename(src),
                      len(_opened & _expect), len(_expect)))
        else:
            print("[gates] critic consented after {} — SELF-REPORTED (no review "
                  "artifact).\n"
                  "        The evidence-backed path is one flag on a step you already run:\n"
                  "          python3 scripts/validate_review.py critic <review.json> --record {}"
                  .format(_critic_effort(critic), os.path.dirname(path) or "."))
        if critic.get("corroborated_by"):
            # An arbiter pass is only corroboration when it CORROBORATES. Read what it actually
            # said: a Job-2 payload reporting an unresolved finding, a dulled strength, or a
            # regressed neighbour is the opposite of a confirmation, and printing it as one is how
            # a failed verification round became a hand-off credential.
            _open = critic.get("arbiter_open") or []
            if _open:
                _lines = []
                for c in _open[:6]:
                    bits = []
                    if not c.get("resolved"):
                        bits.append("NOT resolved" + (": " + c["still_wrong"] if c.get("still_wrong") else ""))
                    if c.get("dulled"):
                        bits.append("dulled a named strength")
                    if c.get("regressions"):
                        bits.append("regressed " + "; ".join(map(str, c["regressions"])))
                    _lines.append("    - {}: {}".format(c.get("finding_ref") or "?", " · ".join(bits)))
                die("the arbiter pass recorded against this deck reports {} item(s) that are still "
                    "open, so it is not a corroboration:\n{}\n\n"
                    "  Fix them and re-run the round, or — if you are shipping over it — say so in "
                    "writing where the user can see it. The loop RAN here, so the honest category "
                    "is the one that says so:\n"
                    '    {{"critic": {{"waived": "shipping over: <the open item and why>",\n'
                    '                 "waived_category": "cap-reached-majors-open",\n'
                    '                 "open": ["<each surviving finding>"],\n'
                    '                 "surfaced_to_user": true|false}}}}\n\n'
                    "  Use `user-waived` ONLY if you actually asked the user and they chose to "
                    "ship — it is a claim about a conversation, and writing it for a conversation "
                    "that did not happen is the failure this classification exists to catch."
                    .format(len(_open), "\n".join(_lines)))
            print("[gates] consent corroborated by {} arbiter pass(es), no open items".format(
                len(critic["corroborated_by"])))
    elif critic.get("verdict") == "revise":
        die("the last critic review returned verdict=revise. Fix the blockers and re-run the "
            "loop, or record a waiver with the reason you are shipping over it. The loop RAN "
            "here, so the honest category is the one that says so:\n"
            '    {"critic": {"waived": "shipping over: <the surviving finding and why>",\n'
            '                "waived_category": "cap-reached-majors-open",\n'
            '                "open": ["<each surviving finding>"],\n'
            '                "surfaced_to_user": true|false}}\n\n'
            "  Use `user-waived` ONLY if you actually asked the user and they chose to ship — it "
            "is a claim about a conversation, and writing it for a conversation that did not "
            "happen is the failure this classification exists to catch.")
    else:
        die("{} has no usable `critic` record — needs {{\"verdict\": \"consent\"|\"revise\"}} or "
            "{{\"waived\": \"<reason>\", \"waived_category\": \"<one of these>\"}}:\n{}"
            .format(path, _critic_waiver_menu()))

    # The design plan is the art director's output (Step 2). Self-authoring one is indistinguishable
    # from dispatching for it — unless the record has to carry the fields the dispatch produces.
    # `icon_family` joins the four originals for one measured reason: a deck shipped with ZERO
    # icons through every automated gate, while a missing LOGO was caught by a required
    # checkpoint token. Icons are called a design must on every branch and had no field, no
    # column and no check anywhere. The token grammar mirrors `logo plan:` — a family name or
    # an explicit `none — <reason>` — so a deliberately icon-free deck is always satisfiable.
    # `palette` joins them for the same measured reason as `icon_family`. SKILL.md already
    # states the two-token rule -- a hue used as TEXT must itself clear 4.5:1, so keep a bright
    # FILL token and a darker TEXT twin. The rule is correct and still easy to break, because
    # the check is per-PAIR and a build touches dozens of them. Measured on one deck: the author
    # declared the rule in the design plan and then broke it FOUR times -- a vivid ochre set as a
    # label on its own pale slab (2.34:1), coral emphasis text on a coral tint (4.19:1), a table
    # highlight (4.19:1), a muted grey carrying real content on cream (4.26:1). None were
    # reckless; each was a pair nobody was thinking about while computing contrast for a
    # different pair, and each surfaced at render time or in review, a round later.
    # `scripts/palette_audit.py` resolves the whole matrix in one call, so the field is cheap to
    # fill honestly and cannot be filled at all without having run something.
    # type_scale and signature_proof were gated on the CODEX delivery path only, so on the shared
    # path typography was the one pillar of the visual language nobody had to resolve (palette,
    # icons and forms all had required fields), and the signature move was accepted as a SENTENCE
    # with nothing showing it survived into the render. That asymmetry is the exact shape of a bug
    # this repo already fixed once: the critic waiver was schema-checked for Codex and a hand-typed
    # string everywhere else, and it carried a real deck through "all gates pass".
    DESIGN_FIELDS = ("concept", "boldness", "signature_move", "carried_by", "form_ledger",
                     "icon_family", "palette", "type_scale", "signature_proof")
    # THE RESTRAINT CARVE — built on the escape the skill ALREADY documents, not a new one.
    # agents/slide-design.md: under a *conservative* dial (user-requested or purpose-defaulted for a
    # sober defense / regulatory / status deck) "the risk is OPTIONAL: take a modest, restrained
    # signature move if one fits, OR — if none does — fill the field with the one-clause
    # `deliberately restrained: <why>` so the field is never blank either way."
    #
    # That escape existed in prose and nowhere in the gate, so an honest 5-minute lab-meeting plan
    # was rejected for lacking a rendered `signature_proof` — a PNG proving an aesthetic risk
    # survived the build, for a deck that deliberately took none. The only way out was
    # {"waived": …}, which also switches off palette, type_scale and icon_family: the real choice
    # was "invent a risk" or "abandon all design gating", and both corrupt the record.
    #
    # What it deliberately does NOT do: it does not relax `signature_move` (the field is still never
    # blank — you must WRITE why restraint is the position) and it does not relax `carried_by`,
    # `palette`, `type_scale`, `icon_family` or `form_ledger`. And it cannot be claimed above the
    # conservative dial: at balanced+ and above a real signature move is required, not optional.
    design = gates.get("design_plan") or {}
    _dial = str(design.get("boldness", "")).strip().lower()
    _move = str(design.get("signature_move", "")).strip().lower()
    # Validate the enum. Every dial-keyed branch in this file and in codex_delivery_gate.py is an
    # equality test against "conservative", so an unrecognised value is not a loud error — it is a
    # SILENT demotion to "not carved, not conservative". Verified: `"boldness": "BANANA"` printed
    # "all hand-off gates pass". A typo must not be a way out of a dial-keyed rule.
    _DIALS = ("conservative", "balanced+", "bold", "experimental")
    if design and not design.get("waived") and _dial and _dial not in _DIALS:
        die("`design_plan.boldness` is {!r}, which is not a dial. One of: {}.\n"
            "  (Every dial-keyed rule tests for `conservative`, so an unrecognised value silently "
            "reads as 'not conservative' rather than failing — which makes a typo an escape.)"
            .format(design.get("boldness"), " | ".join(_DIALS)))
    _carved = _dial == "conservative" and _move.startswith("deliberately restrained")
    if design.get("waived"):
        print("[gates] design plan WAIVED — {}".format(design["waived"]))
    elif design:
        required = [f for f in DESIGN_FIELDS if not (_carved and f == "signature_proof")]
        missing = [f for f in required if not design.get(f)]
        if missing:
            hint = ("\n    palette: the resolved FILL-only vs TEXT-safe split — run\n"
                    "      python3 scripts/palette_audit.py --from-style <deck>/style.py\n"
                    "    and paste what it hands back. A hue that works as a fill can read at\n"
                    "    2-4:1 as text on the same tint; the matrix is what stops that being\n"
                    "    found a render later." if "palette" in missing else "")
            die("`design_plan` is missing {}. These are the art director's outputs "
                "(agents/slide-design.md, Step 2) — a plan without them was not designed, it was "
                "defaulted. Fill them, or waive with a reason.{}".format(", ".join(missing), hint))
        scale = design["type_scale"]
        if not isinstance(scale, dict) or not all(
                isinstance(scale.get(k), (int, float)) for k in ("display", "title", "body")):
            die('`type_scale` must resolve the three tiers as numbers, e.g. '
                '{"display": 34, "title": 24, "body": 14}. SIZE SPRAWL tells authors to draw sizes '
                '"from the deck\'s declared type-scale tokens" — this is where they get declared. '
                'A deck with no scale does not have restrained typography, it has whatever each '
                'slide happened to pick.')
        # same floors the Codex delivery gate uses, so the two paths cannot disagree about what
        # counts as legible body type
        BODY_FLOORS = {"presented": 13.5, "textheavy": 13.5, "selfread": 12.0}
        # `delivery` is resolved ONCE at the top of this function (recorded key > CLI mode, with
        # surface aliased to selfread) and is the same value the density gate uses. Hardcoding
        # "presented" here made --selfread INERT for this floor: a self-read deck with body 12pt
        # died citing the *presented* floor while the same flag correctly drove density.
        floor = BODY_FLOORS[_DELIVERY_ALIAS.get(delivery, delivery)]
        if scale["body"] < floor:
            die(f'`type_scale.body` is {scale["body"]}pt, under the {floor}pt floor for a '
                f'{delivery} deck — that is a legibility floor, not a style choice.')
        if not (scale["display"] > scale["title"] > scale["body"]):
            die(f'`type_scale` is not a scale: display {scale["display"]} > title {scale["title"]} '
                f'> body {scale["body"]} must hold, or the tiers do not rank and the hierarchy is '
                f'decorative rather than structural.')
        if _carved:
            print("[gates] boldness=conservative with a 'deliberately restrained:' signature move — "
                  "signature_proof not required (there is no risk to prove); every other field is")
        proof = None if _carved else design["signature_proof"]
        if proof is not None:
            # `png` or `path`: the Codex delivery gate spells this key `path` in its own evidence file,
            # and a Codex run keeps BOTH records (references/codex-runtime.md). Demanding one spelling
            # here would reject the field an OpenAI-bridged run naturally writes — the same evidence,
            # rejected for its key name.
            # isinstance FIRST: this guard used to run one line after the .get() it protects, so the
            # natural shorthand `"signature_proof": "sig.png"` raised AttributeError and printed a
            # traceback instead of the message below, which says exactly what to write.
            proof_file = proof.get("png") or proof.get("path") if isinstance(proof, dict) else None
            if not isinstance(proof, dict) or not proof_file or not proof.get("slide"):
                die('`signature_proof` must be {"slide": <n>, "png": "<rendered png>"} (the key may also '
                    'be spelled "path", as the Codex delivery gate does) — the rendered evidence that '
                    'the signature move actually SURVIVED into the deck. A move that exists only as a '
                    'sentence in the plan is the documented failure: it gets sanded back to the safe '
                    'catalogue during the build and nobody notices, because the plan still reads bravely.')
            png = Path(proof_file)
            if not png.is_absolute():
                png = Path(pptx).parent / png
            if not png.exists() or png.stat().st_size < 512:
                die(f'`signature_proof` file ({proof_file}) does not exist or is empty — render '
                    f'the slide first (render_deck.py <deck> <dir>) and point at the real PNG.')
        cb = design["carried_by"]
        if not isinstance(cb, list) or len(cb) < 2:
            die("`carried_by` must name at least 2 slides where the signature move does structural "
                "work. One brave slide among eleven safe ones is a tonal break, not a position.")
        # SKILL.md, slide-design.md and review-rubrics.md all name the same three answers as the
        # SAFE CATALOGUE rather than a signature move. Nothing checked, so the literal example
        # passed: a plan whose signature_move was the string "a big number" was accepted and
        # printed approvingly by this gate. A denylist is trivially evaded by paraphrase and that
        # is fine — what it closes is the case that actually happens, the example copied verbatim
        # because it was the nearest words to hand. Judging whether a REAL move is bold stays the
        # critic's distinctiveness axis; this only refuses the three the skill already disowned.
        # CONCEPT — what the deck's idea is a picture of, and the two pictures it beat.
        # The pipeline diverged on STYLE (the direction gate: "the same four slide types … only the
        # style differs") and on LAYOUT (form-selection's per-slide runner-up) and never on the
        # IDEA. A motif does not fill that hole: it is chosen as an attribute of a preset picked
        # first and capped at <=3 appearances, so a governing image is structurally forbidden from
        # governing. The field is cheap by design — three sentences at plan time, no extra dispatch
        # and no extra round trip — so the only thing worth checking is that three genuinely
        # different pictures were considered, not one relabelled twice.
        _con = design.get("concept")
        if _con is not None and not design.get("waived"):
            _rej = (_con.get("rejected") if isinstance(_con, dict) else None) or []
            _win = str((_con.get("chosen") if isinstance(_con, dict) else _con) or "").strip()
            if not isinstance(_con, dict) or not _win or len(_rej) < 2:
                die('`design_plan.concept` must name the governing image AND the two it beat:\n'
                    '    "concept": {"chosen": "<what this deck is a picture of>",\n'
                    '                "rejected": [{"concept": "<the runner-up>", "why_lost": "<one clause>"},\n'
                    '                             {"concept": "<the other>", "why_lost": "<one clause>"}]}\n'
                    "  One picture with no alternatives is not a choice, it is the first thing that "
                    "came to mind — which is the default this field exists to interrupt.")
            _names = [_win.lower()] + [" ".join(str((r or {}).get("concept", "")).lower().split())
                                       for r in _rej]
            if len(set(n for n in _names if n)) < 3:
                die("`design_plan.concept` lists the same picture more than once ({}). Three "
                    "governing images for one argument, not one relabelled — a network, an "
                    "organism and a pair of hands want different motifs, different colour logic "
                    "and different covers, which is the whole reason to choose between them."
                    .format(" · ".join(_names)))
            for r in _rej:
                if not str((r or {}).get("why_lost", "")).strip():
                    die("`design_plan.concept.rejected` needs `why_lost` on each entry — a rejected "
                        "concept with no reason is a decoration on the record, not a decision.")
            print("[gates] concept: {} · beat {}".format(
                _win[:60], " · ".join(str((r or {}).get("concept", "?"))[:28] for r in _rej)))
        _sm = " ".join(str(design["signature_move"]).lower().split())
        _CATALOGUE = ("a big number", "a nice gradient", "a full-bleed photo", "a full bleed photo")
        if any(_sm == c or _sm.rstrip(".") == c for c in _CATALOGUE):
            die('`signature_move` is {!r} — the skill names that (with "a nice gradient" and "a '
                'full-bleed photo") as the SAFE CATALOGUE, explicitly NOT a signature move '
                '(SKILL.md Step 2 · agents/slide-design.md self-verify (h) · '
                'references/review-rubrics.md distinctiveness).\n'
                "  The field wants the ONE aesthetic RISK a template would not take, scoped to "
                "where it lands, and doing structural work on the carried_by slides — the motif "
                "becoming the shape of the content, not a decoration repeated.\n"
                "  If this deck genuinely takes no risk, that is a legitimate answer with its own "
                'arm: set `boldness: conservative` and write `signature_move: "deliberately '
                'restrained: <why>"`.'.format(design["signature_move"]))
        print("[gates] design plan: boldness={} · signature={} · carried_by={}".format(
            design["boldness"], str(design["signature_move"])[:48], cb))
        _report_carried_by(pptx, cb)
        # the declared palette, re-tested against the BUILT file — same reason as the icon
        # waiver above: a plan field written before any slide exists proves nothing about
        # the slides.
        _report_palette_drift(pptx, design.get("palette"))
        _report_plan_files(pptx)
        _report_icon_waiver(pptx, design.get("icon_family"))
        _low_reach = _report_form_reach(pptx)
        # 🔴 A report that never asks for an answer is a line people learn to scroll past. This one
        # printed `1 of 23 named components; the rest is raw box/text` on a delivered deck and let
        # it through — and three of that deck's review findings were defects the unused components
        # prevent by construction (a label grazing its bar, a value floating off a track's
        # centreline, a reference line drawn three different ways).
        #
        # It still does NOT block on the number. Bespoke composition is legitimate and often the
        # signature move itself; a Mondrian page cannot come from a catalogue. What it blocks on is
        # the absence of a DECISION — the failure is never having looked, and `sigs.py --list` is
        # one call. Same shape as the sameness waiver: a written reason, in the record.
        if _low_reach is not None:
            _fr = design.get("form_reach")
            _why = str((_fr or {}).get("waived") or "").strip() if isinstance(_fr, dict) else ""
            if len(_why) < 24:
                die("form reach is {n} of {t} named components and the rest of {s} is raw "
                    "box/text, with no recorded reason.\n"
                    "  Look once — `python3 scripts/sigs.py --list` (or --search <shape>) — then "
                    "either build the component, or record WHY the hand-rolled form is the right "
                    "one for this deck:\n"
                    '    {{"design_plan": {{..., "form_reach": {{"waived": "<why bespoke here — '
                    'name the form and what a component would have cost it>"}}}}}}\n'
                    "  This never blocks on the NUMBER; it blocks on there being no decision. "
                    "Measured: a deck shipped at 1 of 23, and three of its review findings were "
                    "defects the unused components prevent by construction."
                    .format(n=len(_low_reach["forms"]), t=_low_reach["total"],
                            s=_low_reach["script"]))
            print("[gates] form reach WAIVED — %s" % _why[:150])
    else:
        die("no `design_plan` record. Step 2 dispatches agents/slide-design.md as the deck's art "
            "director; nothing else decides deck rhythm or the signature move.\n"
            # Built from DESIGN_FIELDS so this template cannot drift behind the gate again — it
            # listed SIX of the eight for a while, so copying it verbatim produced a record that
            # died on "missing type_scale, signature_proof".
            + "    {\"design_plan\": {" + ", ".join('"%s": ...' % f for f in DESIGN_FIELDS) + "}}\n"
            '    (type_scale is {"display": 34, "title": 24, "body": 14}; signature_proof is\n'
            '     {"slide": N, "png": "render/slideNN.png"} — the rendered evidence the move survived)\n'
            '    or {"design_plan": {"waived": "<reason>"}}')

    # Provenance: a self-filled tally proves nothing — the refutation pass is what the gate is FOR.
    # Require per-claim verdicts, so "confirmed" means someone tried to break it and could not.
    prov = gates.get("provenance") or {}
    if prov.get("waived"):
        print("[gates] provenance WAIVED — {}".format(prov["waived"]))
    elif prov:
        claims = prov.get("claims")
        if not isinstance(claims, list) or not claims:
            die("`provenance` needs a per-claim `claims` list, not a summary tally. A tally is "
                "written by the same pass that would have skipped the check.\n"
                '    "claims": [{"claim": "...", "verdict": "CONFIRMED|WRONG|PARTLY-WRONG|'
                'UNVERIFIABLE", "url": "https://..."}]')
        ALLOWED = {"CONFIRMED", "WRONG", "PARTLY-WRONG", "UNVERIFIABLE"}
        bad = [c for c in claims if c.get("verdict") not in ALLOWED]
        if bad:
            die("{} claim row(s) carry no valid verdict (one of {}).".format(
                len(bad), " / ".join(sorted(ALLOWED))))
        nourl = [c for c in claims if c.get("verdict") == "CONFIRMED" and not c.get("url")]
        if nourl:
            die("{} claim(s) are CONFIRMED with no primary-source URL. Confirmed-without-a-source "
                "is the exact failure this gate exists to catch.".format(len(nourl)))
        unresolved = [c for c in claims if c["verdict"] in ("WRONG", "PARTLY-WRONG")]
        if unresolved:
            die("{} claim(s) still verdict WRONG / PARTLY-WRONG. Fix or cut them before hand-off:\n"
                "  - {}".format(len(unresolved),
                                "\n  - ".join(str(c.get("claim"))[:90] for c in unresolved[:5])))
        tally = {}
        for c in claims:
            tally[c["verdict"]] = tally.get(c["verdict"], 0) + 1
        print("[gates] provenance: {} claim(s) adversarially checked — {}".format(
            len(claims), " · ".join("{} {}".format(v, k) for k, v in sorted(tally.items()))))
    else:
        print("[gates] no provenance record — fine for a deck built from the user's own material; "
              "a research-sourced deck should carry one.")

    # ── SAMENESS: the deck-level monotony the [stats] block measured and nobody read ──────────
    # Every deck-level "this deck is one page repeated" signal the linter computes is a
    # `warns.append` printed under a line that says the stats are advisory; `lint()` returns only
    # the hard-finding count, and nothing on this path ever read the warns. So blandness was
    # DETECTED deterministically and blocked nothing. This turns the measurement into a gate —
    # and only the measurement: whether a deck is TIMID stays the critic's taste call (which the
    # skill deliberately caps as non-blocking), whether it is REPETITIVE is a share of slides
    # agreeing with each other, which is a defect with a concrete fix. `agents/critic.md` states
    # that exact test, and it is why this can hold a deck while the distinctiveness axis cannot.
    _check_sameness(pptx, delivery, gates)

    # ── DENSITY: a slide is a visual aid, not a document ────────────────────────
    # This one is a gate rather than a warning because the warning already existed and was
    # already ignored — twice, by the same author, on two consecutive decks. Measured: one
    # deck shipped with 8 of 12 slides over the presented text budget, the next with 12 of 12
    # (loads of 81-144 words against a budget of ~40), and both times the per-slide TEXT WALL
    # line was read and dismissed as advisory. The skill's OWN reference deck — the file it
    # tells every builder to copy — runs at a median of 27 words a slide, so the budget is not
    # unrealistic; what failed was that nothing made ignoring it cost anything.
    # A deck may legitimately be denser (a self-read leave-behind, a spec sheet). That is what
    # the waiver is for: not a rule against text, a rule against text arriving by default.
    #
    # DELIVERY MODE. The budget here is lint_deck's budget, taken from lint_deck: 70 words for a
    # presented deck, 120 for a self-read one, and no budget at all on a poster (`surface`) or a
    # deck whose density the user CHOSE at Q4 (`textheavy`). A gate that fires on a mode the
    # interview offers, the rubric protects and the lint deliberately passes does not enforce
    # anything for long — it teaches the author to paste a waiver, and after that it is decoration.
    txt = gates.get("density")
    # the SAME resolved delivery the type floor used — reading raw `mode` here is how one run
    # enforced two different deliveries
    if delivery in ("surface", "textheavy"):
        print("[gates] density: not applied — %s deck (the user chose this density, or the "
              "surface has no per-slide budget)" % delivery)
        return
    over, total, median = _density_stats(pptx, budget=70 if delivery == "presented" else 120)
    if total:
        if isinstance(txt, dict) and txt.get("waived"):
            print("[gates] density: {}/{} slide(s) over the presented text budget, median {} "
                  "words — WAIVED: {}".format(over, total, median, str(txt["waived"])[:110]))
        elif over * 3 > total:
            die("{} of {} slides are over the {} text budget (median {} words a slide; "
                "aim ~40, warn >{}). The skill's own reference deck runs at 27.\n"
                "    A slide is a visual aid for a speaker — the sentences belong in the speaker "
                "notes, which this deck already has.\n"
                "    Cut the on-slide prose, or record the deliberate choice:\n"
                '    "density": {{"waived": "why this deck is meant to be read, not presented"}}'
                .format(over, total, delivery, median, 70 if delivery == "presented" else 120))
        else:
            print("[gates] density: {}/{} slide(s) over the text budget, median {} words a slide"
                  .format(over, total, median))


SAMENESS_WAIVER_KINDS = {
    "series-frame":
        "a carousel / board / poster series where the REPEATED FRAME is the artifact",
    "register-uniform":
        "a deliberately single-register deck (留白 / ink-wash, a uniformly dark editorial briefing)",
    "template-locked":
        "a registered or provided template whose grid this deck may not break",
    "reference-run":
        "the repeated pages are reference material (first try design_intent(role='appendix') — "
        "that is the real fix, and it takes those pages out of the count)",
    "user-waived":
        "the user was shown the finding and chose to ship over it",
}


def _sameness_stats(pptx, delivery):
    """The deck-level sameness codes, taken from lint_deck's OWN measurement.

    Same reason `_density_stats` calls `reading_load`: the number in the [stats] line and the
    number in this gate have to be ONE number by construction. Nothing is re-implemented here —
    a second implementation is how lint came to say 136 words a slide while the gate said 4.

    `renders_dir=None` keeps lint's normal auto-discovery of ./render beside the deck, INCLUDING
    its staleness guard, so the gate inherits the same freshness rule the CLI has.
    """
    import contextlib
    import io
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lint_deck as _ld
    from pptx import Presentation
    try:
        prs = Presentation(pptx)
        aspect = (prs.slide_width / float(prs.slide_height)) if prs.slide_height else 0.0
    except Exception as exc:
        die("the sameness gate could not open {} ({}). An unreadable deck is not a pass."
            .format(pptx, exc))
    stats, buf = {}, io.StringIO()
    gates_path = os.path.join(os.path.dirname(os.path.abspath(pptx)) or ".", GATES_FILE)
    try:
        with contextlib.redirect_stdout(buf):        # lint prints its whole report; we want the data
            _ld.lint(pptx, mode=delivery, renders_dir=None, static_ok=True,
                     gates_path=gates_path, stats_out=stats)
    except SystemExit as exc:
        die("the sameness gate could not lint {} (lint_deck exited {}). An unreadable deck is not "
            "a pass.".format(pptx, exc.code))
    return stats, aspect


def _check_sameness(pptx, delivery, gates):
    """Block a hand-off when the deck measurably repeats itself, unless the repetition is declared.

    Scope and threshold are calibrated against 11 decks BUILT AND LINTED in the registers this
    skill itself prescribes, not against intuition. The raw signal count is a bad gate: a 6-slide
    template-locked status update with ZERO hard findings already reaches 3 families, a 9-card
    小红书 carousel built exactly to canvas-formats.md's DNA reaches 7, and an appendix-heavy
    defense deck reaches 5. Each of those is a deck the skill tells you to build.

    So the scope is three DETERMINISTIC properties of the deck rather than a taxonomy of registers
    (the registers have no working wire today: --briefing / --selfread / --textheavy relieve
    nothing on the sameness side, and --surface relieves three signals only at n=1):
        body_n >= 8    — lint's own body run, cover/closer/appendix excluded. Kills the whole
                         status-update class, whose measured cliff was SIX total slides.
        landscape      — kills the carousel class, whose repeated frame IS the artifact.
        not surface    — a single canvas has no deck-level rhythm to vary.
    and the threshold is >= 4 distinct codes WITH at least one structural code. Three is where a
    competent consistent system lands (repeated layout + one card + one footer strip); the
    structural requirement excludes the one 4-code set that means "same frame, varied bodies".
    """
    if not isinstance(gates, dict):
        gates = {}
    waiver = gates.get("sameness") or {}
    stats, aspect = _sameness_stats(pptx, delivery)
    fired = tuple(stats.get("sameness_codes") or ())
    body_n = int(stats.get("body_n") or 0)
    ran = bool(stats.get("render_signals_ran"))
    skip_reason = stats.get("render_skip_reason")
    total = len(_LD_SAMENESS_CODES())
    could_run = total if ran else total - len(_LD_SAMENESS_RENDER_DEPENDENT())
    tail = "" if ran else "  · NOT CHECKED: {} ({})".format(
        " · ".join(_LD_SAMENESS_RENDER_DEPENDENT()), skip_reason or "no renders beside the deck")

    if delivery == "surface" or aspect < 1.2 or body_n < 8:
        why = ("a single-canvas surface" if delivery == "surface"
               else "a portrait/square canvas — a series' repeated frame is the artifact"
               if aspect < 1.2 else "%d content slide(s), under the 8 this is calibrated for" % body_n)
        print("[gates] sameness: not applied — {} (the per-signal [stats] warnings still print)"
              .format(why))
        return

    structural = [c for c in fired if c in _LD_SAMENESS_STRUCTURAL()]
    blocks = len(fired) >= 4 and bool(structural)
    listed = " · ".join(fired) if fired else "none"

    if waiver:
        reason = waiver.get("waived")
        kind = waiver.get("waived_category")
        if not isinstance(reason, str) or len(reason.strip()) < 40:
            die("`sameness.waived` must be a written reason that names the REGISTER this deck is "
                "in, not a circumstance — a sentence someone can disagree with later (>=40 chars).")
        if kind not in SAMENESS_WAIVER_KINDS:
            die("`sameness.waived_category` must name WHICH kind of deliberate repetition this "
                "is. One of:\n" + "\n".join("    {:18s} {}".format(k, v)
                                            for k, v in sorted(SAMENESS_WAIVER_KINDS.items())))
        recorded = waiver.get("codes")
        if not isinstance(recorded, list) or set(recorded) != set(fired):
            die("`sameness.codes` records {} but this deck now fires {}. A waiver written for a "
                "different state of the deck does not certify this one — re-read the measurement "
                "and rewrite the reason against it.\n    codes: {}"
                .format(sorted(recorded) if isinstance(recorded, list) else recorded,
                        sorted(fired) or "nothing", json.dumps(sorted(fired))))
        if not blocks:
            print("[gates] sameness: recorded waiver is NOT needed — {} of {} signal(s) fired ({})"
                  .format(len(fired), could_run, listed) + tail)
        else:
            print("[gates] sameness: WAIVED [{}] — {} of {} fired: {}".format(
                kind, len(fired), could_run, listed) + tail)
            print("        {}".format(reason.strip()))
        return

    if blocks:
        die("SAMENESS: {} of {} deck-level signals fired across {} content slides —\n"
            "        {}\n\n"
            "  Each is a MEASURED share, not a taste call: this deck repeats one page structure, "
            "one content vehicle, one piece of chrome or one vertical envelope across most of its "
            "pages.\n"
            "  Fix the deck — rotate the canvas architecture, break the card grid on the WOW "
            "slide, move the takeaway off the bottom strip on some pages, let one page bleed —\n"
            "  or record why the repetition IS the design:\n\n"
            '    "sameness": {{"waived": "<why this deck repeats on purpose>",\n'
            '                 "waived_category": "{}",\n'
            '                 "codes": {}}}\n\n'
            "  Categories: {}"
            .format(len(fired), could_run, body_n, " · ".join(fired),
                    " | ".join(sorted(SAMENESS_WAIVER_KINDS)), json.dumps(sorted(fired)),
                    "; ".join("{} = {}".format(k, v)
                              for k, v in sorted(SAMENESS_WAIVER_KINDS.items()))))

    # The boundary the count cannot decide: one more signal would have crossed the line, and one
    # signal did not run. Passing here would be a verdict about a measurement that was never taken.
    if len(fired) == 3 and structural and not ran:
        die("SAMENESS: 3 of the {} signals that could run fired ({}), and {} did not run ({}).\n"
            "  At three fired the verdict turns on the signal that is missing, so this deck cannot "
            "be decided as it stands.\n"
            "  Render it —  python3 scripts/render_deck.py {} <out>  — and re-run --gate-check, "
            "or record the waiver."
            .format(could_run, listed, " · ".join(_LD_SAMENESS_RENDER_DEPENDENT()),
                    skip_reason or "no renders beside the deck", pptx))

    print("[gates] sameness: {} of {} deck-level signal(s) fired across {} content slides{}"
          .format(len(fired), could_run, body_n,
                  " — " + listed if fired else "") + tail)


def _LD_SAMENESS_CODES():
    import lint_deck as _ld
    return _ld.SAMENESS_CODES


def _LD_SAMENESS_STRUCTURAL():
    import lint_deck as _ld
    return _ld.SAMENESS_STRUCTURAL


def _LD_SAMENESS_RENDER_DEPENDENT():
    import lint_deck as _ld
    return _ld.SAMENESS_RENDER_DEPENDENT


def _density_stats(pptx, budget=70):
    """(slides over the text budget, total slides, median load).

    Calls `lint_deck.reading_load` — the SAME function the per-slide TEXT WALL warning calls —
    so the number in the warning and the number in this gate are one number by construction.
    An earlier version of this only shared the string-level word counter and re-implemented the
    per-slide accumulation and the chrome filter, which is where all the drift actually lives:
    its `sz <= 10.5 and len(t) < 40` skip had no POSITION test, so it was not a footer filter
    but an amnesty for small type anywhere on the slide. Measured on one deck: lint said 136
    words a slide, the gate said 4, and a wall of 10.5pt prose passed. Sharing a helper is not
    the same as sharing the measurement — share the measurement.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from lint_deck import _boxes, reading_load
        from pptx import Presentation
        prs = Presentation(pptx)
        sw = prs.slide_width / 914400.0
        sh = prs.slide_height / 914400.0
    except Exception:
        return 0, 0, 0
    loads = [reading_load(sl, _boxes(sl, sw, sh), sh) for sl in prs.slides]
    if not loads:
        return 0, 0, 0
    loads.sort()
    return sum(1 for x in loads if x > budget), len(loads), loads[len(loads) // 2]



def _contact_sheet(out, n_pages):
    """One image of the WHOLE deck, written beside the per-slide PNGs as `contact.png`.

    🔴 ADDITIVE, and the distinction is not a nicety. Measured on a real 12-page deck, a page in
    this sheet is 460px wide — 46 px/inch against the render's 144. At that size a 23pt title is
    15px and readable, and **13.5pt body text is 8.6px and a 10pt source line is 6.4px: neither
    can be read at all**. So this image answers DECK-LEVEL questions only — the light/dark rhythm,
    whether the bookends bookend, form variety, whether one chrome treatment is stamped on every
    page, a canvas flip that lands on exactly one slide. It is the view the deck-level checks
    (ONE-OFF CANVAS FLIP · TITLE-RULE MONOCULTURE · FLAT RHYTHM · BOTTOM-STRIP MONOCULTURE)
    measure, finally visible to a reader.

    It CANNOT answer a per-slide question — typography, contrast, a label grazing its bar, an
    overlap, whether a number is right — and it must never be used as if it had. The render
    self-check still reads slides page by page; this sheet is what you look at BEFORE that, to
    know which pages deserve the attention. Substituting it for the per-slide read would be the
    same failure this skill keeps finding elsewhere: passing a check by not looking.

    Silent no-op without Pillow, and never fatal — a missing contact sheet must not fail a render.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    import glob as _glob
    pngs = sorted(_glob.glob(os.path.join(out, "slide*.png")),
                  key=lambda p: int(re.sub(r"\D", "", os.path.basename(p)) or 0))
    if len(pngs) < 2:
        return None                                      # a 1-page deck has no deck-level shape
    # SPLIT rather than shrink past legibility. A single sheet of 40 pages measures 1890x2860, and
    # an image that tall is downscaled to fit before anyone looks at it — measured, a 0.55 factor,
    # which takes a tile from 460px to 252px and a 23pt title from 15px to 8px. The sheet would
    # still be produced, still be called the deck-level view, and no longer show anything: a
    # silent degradation, which is the failure mode this skill treats as worse than a loud one.
    # 12 per sheet is the size that was verified readable on a real deck, so a long deck gets
    # several readable sheets instead of one useless one.
    PER = 12
    chunks = [pngs[i:i + PER] for i in range(0, len(pngs), PER)]
    made = []
    try:
        w0, h0 = Image.open(pngs[0]).size
        tw = 460
        th = max(1, int(round(tw * h0 / float(w0))))
        pad, lab = 10, 16
        for ci, chunk in enumerate(chunks):
            cols = 4 if len(chunk) > 6 else (3 if len(chunk) > 2 else 2)
            rows = -(-len(chunk) // cols)
            sheet = Image.new("RGB", (cols * tw + (cols + 1) * pad,
                                      rows * (th + lab) + (rows + 1) * pad), (235, 235, 238))
            d = ImageDraw.Draw(sheet)
            for i, p in enumerate(chunk):
                im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
                x = pad + (i % cols) * (tw + pad)
                y = pad + (i // cols) * (th + lab + pad)
                sheet.paste(im, (x, y))
                d.rectangle([x, y, x + tw, y + th], outline=(180, 180, 186))
                d.text((x + 3, y + th + 2), "%02d" % (ci * PER + i + 1), fill=(60, 60, 66))
            name = "contact.png" if len(chunks) == 1 else "contact_%02d.png" % (ci + 1)
            dest = os.path.join(out, name)
            sheet.save(dest)
            made.append(dest)
        return made
    except Exception:
        return None                                      # never fail a render over a preview

def main(argv):
    # --deliverables (alias --final): ALSO park the PDF beside the .pptx and write viewer.html.
    # OFF by default: while a deck is still being iterated, those two are pure churn — they are
    # regenerated every round, clutter the deck root, and go stale the moment the user hand-edits
    # the .pptx. They are produced once, at hand-off, when the user says the deck is final.
    deliverables = False
    # --fast: re-render ONLY the slides whose content changed since the last render.
    # Measured on a real 18-slide deck: full = 9.1s LibreOffice + 24.4s rasterize; one changed
    # slide = 2.5s + 0.7s. Rasterization, not the PDF export, is the dominant cost — so the win
    # comes from rasterizing one page, and subsetting the pptx makes the export cheap too.
    fast = False
    # --slides N[,M]: render ONLY these 1-indexed slides. Unlike --fast (which DIFFS against a
    # cache and therefore renders everything on a first run), this is an explicit "show me page N"
    # — the SIGNATURE PROOF that opens SKILL.md Step 4, and any "re-render the page I edited" loop.
    only = None
    argv = list(argv)
    while "--fast" in argv:
        argv.remove("--fast")
        fast = True
    for i, a in enumerate(list(argv)):
        if a == "--slides" or a.startswith("--slides="):
            raw = a.split("=", 1)[1] if "=" in a else (argv[i + 1] if i + 1 < len(argv) else "")
            try:
                only = sorted({int(t) for t in raw.replace(" ", "").split(",") if t})
            except ValueError:
                die("--slides wants 1-indexed slide numbers, e.g. --slides 1,6")
            if not only:
                die("--slides wants at least one slide number, e.g. --slides 6")
            argv.remove(a)
            if "=" not in a and raw in argv:
                argv.remove(raw)
            break
    # --gate-check runs the hand-off gates and exits, rendering nothing. The gates were reachable
    # only through --deliverables, which Step 6 deliberately makes a decline-able OFFER ("want a PDF
    # and a browser preview?"), so on every deck where the user said no, the strongest gate in the
    # skill never ran at all. Step 6 now calls this unconditionally, whatever the user answers.
    # Delivery mode — the SAME flags lint_deck.py takes, spelled the same way, because the gate
    # below enforces the lint's budget and the two must never disagree about which deck this is.
    mode = "presented"
    for flag, name in (("--selfread", "selfread"), ("--surface", "surface"),
                       ("--textheavy", "textheavy")):
        while flag in argv or ("--mode=" + name) in argv:
            argv = [a for a in argv if a not in (flag, "--mode=" + name)]
            mode = name
    # --static: accepted and intentionally inert. lint_deck.py takes it to silence NO BUILDS on a
    # deck whose user opted OUT of appear-builds; this tool already lints with static_ok=True, so
    # there is nothing for it to switch. It is consumed rather than rejected because callers pass
    # it by symmetry with lint_deck.py (the test suite does, on every gate call) — and before the
    # unknown-flag guard below existed it was silently absorbed as the OUTPUT DIRECTORY.
    while "--static" in argv or "--mode=static" in argv:
        argv = [a for a in argv if a not in ("--static", "--mode=static")]
    gate_only = False
    if "--gate-check" in argv:
        argv = [a for a in argv if a != "--gate-check"]
        gate_only = True
    for flag in ("--deliverables", "--final"):
        while flag in argv:
            argv.remove(flag)
            deliverables = True
    if fast and deliverables:
        # Decided here, not after LibreOffice has already run: --deliverables needs a whole-deck
        # PDF, which a subset render cannot produce. Failing late meant either an exit-1 after a
        # successful render, or (with nothing changed) a silent exit-0 that produced no PDF and no
        # viewer.html at the exact moment the hand-off contract required them.
        die("--deliverables needs a full-deck render — drop --fast for the hand-off run")
    if only and deliverables:
        # Same reason as --fast: a subset cannot produce the whole-deck PDF the hand-off promises.
        die("--deliverables needs a full-deck render — drop --slides for the hand-off run")
    if only and fast:
        # Contradictory intents: --fast decides WHICH slides to render, --slides declares them.
        die("--slides and --fast both choose the slide set — pass one")
    # Every flag this tool knows has been consumed by now, so anything still starting with `--`
    # is one it does not take — and until this guard existed it was not an error. `argv[0]` is
    # the deck and `argv[1]` is the output dir, so `render_deck.py deck.pptx --gate-check
    # --briefing` resolved to out="--briefing" and ran the hand-off gate at the `presented`
    # floor: a briefing deck (lint budget ~150 words) silently held to the ~40-word budget, with
    # nothing printed either way. That is the same silent-fallthrough class the `delivery` key
    # below already dies on ("a legibility floor silently not applied"); a mode flag typed at the
    # CLI deserves the same treatment. NB `--briefing` is a real lint_deck.py mode that this tool
    # genuinely does not implement — the message says so rather than pretending it is a typo.
    _stray = [a for a in argv if a.startswith("--")]
    if _stray:
        _hint = ""
        if any(a in ("--briefing", "--mode=briefing") for a in _stray):
            _hint += ("\n  `--briefing` is a lint_deck.py mode; the hand-off gate has no briefing "
                      "floor yet, so it would have run at `presented`. Lint the deck with "
                      "`lint_deck.py <deck> --briefing` and record `delivery` in .deck-gates.json.")
        die("unrecognised option(s): " + " ".join(_stray) + "\n  render_deck.py takes: --slides "
            "N[,M] · --fast · --deliverables/--final · --gate-check · --selfread · --textheavy · "
            "--surface (each mode also spelled --mode=NAME). The output dir is POSITIONAL: "
            "render_deck.py <deck>.pptx [out_dir]." + _hint)
    if not argv:
        die("usage: python render_deck.py /path/to/deck.pptx [out_dir] "
            "[--fast | --slides N[,M]] [--deliverables] [--gate-check]")
    pptx = argv[0]
    out = argv[1] if len(argv) > 1 else "./render"

    if not os.path.isfile(pptx):
        die("no such file: " + pptx)

    if gate_only:
        check_handoff_gates(pptx, mode, gate_check=True)
        print("[gates] all hand-off gates pass — the deck may be handed over")
        return 0

    # Checked here, before LibreOffice runs — same reason the --fast/--slides conflicts are:
    # failing after a successful render wastes the render and reads as a late surprise.
    if deliverables:
        check_handoff_gates(pptx, mode)

    soffice = find_soffice()
    if not soffice:
        die(
            "LibreOffice not found — needed to render slides for the verify + critic loop.\n"
            "  macOS:         brew install --cask libreoffice\n"
            "  Debian/Ubuntu: sudo apt install libreoffice\n"
            "  Windows:       winget install TheDocumentFoundation.LibreOffice\n"
            "                 (or choco install libreoffice-fresh)\n"
            "  other:         https://www.libreoffice.org/download\n"
            "  (or set the SOFFICE env var to the full path of the soffice binary)"
        )

    # Decide full vs incremental BEFORE spending anything on LibreOffice.
    # When out == the deck's own folder (the code below explicitly tolerates the user passing "."),
    # <deck>.pdf and viewer.html there are the HAND-OFF deliverables, not render products. Nothing
    # in this run may delete or overwrite them.
    _deck_dir = os.path.dirname(os.path.abspath(pptx)) or "."
    _out_is_deck_dir = os.path.abspath(out) == os.path.abspath(_deck_dir)

    cache_path = os.path.join(out, ".render-cache.json")
    # Cheap, but not free on a big deck — and a full render still needs them, both to validate the
    # page count and to leave a cache the NEXT --fast can diff against. Guarded so an unreadable
    # package falls back to LibreOffice's own diagnostic instead of a zipfile traceback (v3.5.1
    # behaviour, which the friendly error in troubleshooting-faq.md documents).
    try:
        fps, blockers = _slide_fingerprints(pptx)
    except Exception as exc:
        fps, blockers = [], ["could not read the .pptx package: {}".format(exc)]
    changed, skip_reason = None, None
    if fast:
        prev = None
        try:
            with open(cache_path, encoding="utf-8") as f:
                cached = json.load(f)
            prev = cached.get("fingerprints") if isinstance(cached, dict) else None
            if not (isinstance(prev, list) and all(isinstance(x, str) for x in prev)):
                prev = None                     # a JSON list/garbage must not crash the tool
        except Exception:
            prev = None
        if blockers:
            # Correctness beats speed: anything that makes the slide->page mapping uncertain
            # forces a full render.
            skip_reason = blockers[0]
        elif not prev:
            skip_reason = "no previous render cache"
        elif len(prev) != len(fps):
            # Slides inserted or deleted shifts every index after the edit; PNG filenames would
            # silently point at the wrong slides.
            skip_reason = "slide count changed ({} -> {})".format(len(prev), len(fps))
        else:
            changed = [i for i, h in enumerate(fps) if h != prev[i]]

            def _usable(name):                  # a 0-byte file from a killed rasterize is NOT a render
                p = os.path.join(out, name)
                try:
                    return os.path.getsize(p) > 0
                except OSError:
                    return False

            missing = [i for i in range(len(fps)) if not _usable("slide{:02d}.png".format(i + 1))]
            # thumbnails are regenerated only when a bookend slide is re-rendered, so a missing
            # thumb must pull its bookend into the changed set or the critic's poster test runs
            # on a stale or absent image while the run prints success
            if not _usable("thumb_first.png"):
                missing.append(0)
            if not _usable("thumb_last.png"):
                missing.append(len(fps) - 1)
            changed = sorted(set(changed) | set(i for i in missing if 0 <= i < len(fps)))

    try:
        _st = os.stat(pptx)
        pptx_stat = (_st.st_mtime_ns, _st.st_size)
    except OSError:
        pptx_stat = None
    if only is not None:
        if blockers:
            # The SAME correctness bar as --fast: anything that makes the slide->page mapping
            # uncertain (hidden slides, an unresolvable part, auto slide-number fields that
            # renumber inside a subset) must not be papered over just because the user named a page.
            die("cannot render a subset of this deck: {}\n"
                "  drop --slides and render the whole deck".format(blockers[0]))
        bad = [n for n in only if not (1 <= n <= len(fps))]
        if bad:
            die("--slides {} out of range — this deck has {} slide(s)".format(
                ",".join(str(b) for b in bad), len(fps)))
        changed = [n - 1 for n in only]
    incremental = (fast or only is not None) and changed is not None and 0 < len(changed) < len(fps)
    if fast and changed is not None and len(changed) == len(fps) and len(fps):
        # Every slide changed (a rebuild that touched everything, or a deck-global edit such as a
        # theme/canvas change). A subset of "all slides" is just a full render with extra steps.
        skip_reason = "every slide changed"
    if fast and changed is not None and not changed:
        print("no slide changed since the last render — nothing to re-render")
        print("next: python3 {} {} --renders {}".format(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_deck.py"), pptx, out))
        return 0



    # Give this invocation a LibreOffice profile NO OTHER PROCESS IS USING: lets parallel
    # renders (the large-deck section fan-out) run at once without fighting a shared profile
    # lock, and lets the render work even while the user has the LibreOffice GUI open.
    # Without this, concurrent/coexisting soffice calls silently produce no PDF.
    # `_acquire_profile()` keeps that invariant with an exclusively-flocked slot from a
    # persistent pool (warm profile, ~1.5s cheaper per export) and falls back to the original
    # throwaway `mkdtemp` whenever a slot is unavailable — see `_Profile` for the whole story.
    src_pptx, keep = pptx, None
    tmp_subset = tmp_dir = None
    if incremental:
        keep = changed
        tmp_dir = tempfile.mkdtemp(prefix="lo_subset_")
        tmp_subset = os.path.join(tmp_dir, "subset.pptx")
        _subset_pptx(pptx, set(keep), tmp_subset)
        src_pptx = tmp_subset

    # A subset renders into its OWN temp dir. Writing out/subset.pdf would collide between two
    # concurrent runs sharing a render dir (which the per-invocation LibreOffice profile above
    # exists to allow), and a crashed run would leave a file that breaks the render-only cleanup.
    # ALWAYS convert into a private empty directory, never straight into `out`: `out` may already
    # hold a <deck>.pdf (a previous render, or a --deliverables artefact when out is the deck
    # folder), and a stale file there would make a failed conversion look like a successful one.
    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp(prefix="lo_render_out_")
    import atexit
    atexit.register(shutil.rmtree, tmp_dir, True)       # a die() mid-render must not leak a deck copy
    pdf, result, cmd = _render_pdf(soffice, src_pptx, tmp_dir)
    try:
        import fitz  # pymupdf
    except ImportError:
        die("pymupdf not installed — run: {} -m pip install pymupdf".format(
            os.path.basename(sys.executable) or "python"))

    if result.returncode != 0 or not os.path.isfile(pdf):
        detail = [
            "LibreOffice failed to convert {} (exit {}).".format(pptx, result.returncode)
            if result.returncode != 0 else "LibreOffice produced no PDF from {}.".format(pptx),
            "Command: " + " ".join(cmd),
            "Exit code: {}".format(result.returncode),
        ]
        stdout = _tail(result.stdout)
        stderr = _tail(result.stderr)
        if stdout:
            detail.append("stdout:\n" + stdout)
        if stderr:
            detail.append("stderr:\n" + stderr)
        detail.append(
            "Check that the file opens, close any open copy, and in sandboxed runtimes "
            "rerun the render with the permissions needed for LibreOffice."
        )
        die("\n".join(detail))

    # Open the PDF BEFORE the cleanup: a non-zero exit and a missing file were already fatal, but a
    # zero-exit run that writes a truncated/garbage PDF passed both checks, and the cleanup had
    # already deleted the previous render by the time fitz raised.
    try:
        _probe = fitz.open(pdf)
        _npages = _probe.page_count
        _probe.close()
    except Exception as exc:
        die("LibreOffice produced an unreadable PDF from {} ({}). The previous render in {} was "
            "left untouched.".format(pptx, exc, out))
    if _npages < 1:
        die("LibreOffice produced an empty PDF (0 pages) from {}. The previous render in {} was "
            "left untouched.".format(pptx, out))

    # Clear the previous render only NOW, after LibreOffice has actually produced a readable PDF. Doing it
    # earlier meant a failed conversion destroyed the last good render and left nothing at all —
    # the user lost working output to a run that produced none.
    # Wiping the render dir BEFORE deciding is what made --fast a no-op: every PNG looked
    # "missing", so every slide looked changed. An incremental run keeps the existing PNGs and
    # overwrites only the ones it re-renders.
    if os.path.isdir(out) and not incremental:
        entries = os.listdir(out)
        own_pdf = os.path.splitext(os.path.basename(pptx))[0] + ".pdf"
        render_only = all(
            (e.startswith(("slide", "thumb_")) and e.endswith(".png"))
            or e == "viewer.html" or e == own_pdf          # only THIS deck's fallback pdf is ours
            or e in (".DS_Store", "Thumbs.db", ".render-cache.json")   # OS junk + our own cache only
            for e in entries)                              # make the dir look deletable
        if render_only:
            shutil.rmtree(out, ignore_errors=True)
        else:
            # out holds files that are NOT ours (worst case: the user passed "." — the pptx's own
            # directory). NEVER rmtree it; clear only our previous render products.
            for e in entries:
                if _out_is_deck_dir and (e == "viewer.html" or not _RENDER_PNG.match(e)):
                    # out IS the deck folder: only files matching our own strict output pattern
                    # (slideNN.png / thumb_first|last.png) are ours. A user's slide_background.png
                    # or thumb_hero.png sitting beside the deck was being deleted silently.
                    continue
                if ((e.startswith(("slide", "thumb_")) and e.endswith(("png",)))
                        or e == "contact.png" or e.startswith("contact_")
                        or e == "viewer.html"):
                    try:
                        os.remove(os.path.join(out, e))
                    except OSError:
                        pass
    os.makedirs(out, exist_ok=True)


    doc = fitz.open(pdf)
    skip_cache = False
    if only is not None:
        # A --slides run rasterized SOME pages; the fingerprints in hand describe ALL of them.
        # Caching them would tell the next --fast "nothing changed" while most PNGs are stale —
        # precisely the lie the incremental path exists to avoid. Drop the cache instead, so the
        # next --fast honestly does a full render.
        skip_cache = True
    if incremental:
        # PDF page k corresponds to deck slide keep[k] — write ONLY those PNGs and leave the
        # rest of render/ untouched.
        if doc.page_count != len(keep):
            die("incremental render produced {} page(s) for {} changed slide(s) — refusing to "
                "write PNGs that may be mismatched; re-run without --fast".format(
                    doc.page_count, len(keep)))
        for k, page in enumerate(doc):
            page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(
                os.path.join(out, "slide{:02d}.png".format(keep[k] + 1)))
        # thumbnails only matter when a bookend slide moved
        for name, idx in (("thumb_first", 0), ("thumb_last", len(fps) - 1)):
            if idx in keep:
                page = doc[keep.index(idx)]
                zoom = 240.0 / max(1.0, page.rect.width)
                page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(os.path.join(out, name + ".png"))
        n_pages = len(fps)
    else:
        pages = list(enumerate(doc, 1))
        # Fast path first; it returns False on a small deck or any trouble, and then both
        # loops below run exactly as they always did. When it succeeds it has ALSO written
        # the two bookend thumbnails, from the workers that own those pages — see
        # _rasterize_chunk for why they cannot be re-rendered here instead.
        drawn_in_parallel = _rasterize_parallel(pdf, doc.page_count, out)
        if not drawn_in_parallel:
            for i, page in pages:
                page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(
                    os.path.join(out, "slide{:02d}.png".format(i)))
        # bookend thumbnails (~240px wide) for the critic's poster test — first + last slide small,
        # the scale at which a cover either survives or dies. Same PyMuPDF path, no new deps.
        if pages and not drawn_in_parallel:
            for name, (_, page) in (("thumb_first", pages[0]), ("thumb_last", pages[-1])):
                zoom = 240.0 / max(1.0, page.rect.width)
                page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(os.path.join(out, name + ".png"))
        n_pages = doc.page_count
        if n_pages != len(fps) and fps:
            # LibreOffice emitted a different number of pages than the deck has slides (hidden
            # slides are the known cause). slideNN.png no longer means deck slide NN, so no cache
            # may claim this render — and the user must be told rather than quietly trusting it.
            print("WARNING: {} slides in the deck but {} PDF page(s) rendered — slideNN.png may "
                  "not correspond to deck slide NN. Not caching fingerprints; --fast is disabled "
                  "until this is resolved.".format(len(fps), n_pages), file=sys.stderr)
            skip_cache = True
    doc.close()
    if incremental:
        pdf = None                              # a subset PDF is not the deck's PDF
        # Drop the previous FULL render's intermediate PDF, which the new PNGs have outdated —
        # but never when `out` IS the deck folder, where that same filename is the user's
        # hand-off deliverable. Deleting it there silently destroyed a --deliverables artefact.
        if not _out_is_deck_dir:
            try:
                os.remove(os.path.join(out, os.path.splitext(os.path.basename(pptx))[0] + ".pdf"))
            except OSError:
                pass

    # Record fingerprints so the NEXT run can diff against them. Written only after the PNGs
    # actually landed, so a crashed render never leaves a cache claiming work that did not happen.
    # Two guards: (1) if the .pptx changed WHILE we rendered, the fingerprints we hold describe
    # state that was never rasterized — caching them would freeze that slide stale forever;
    # (2) a failed write must DELETE the cache, because a cache older than the PNGs is exactly the
    # "no slide changed" lie this whole path must not tell.
    if not skip_cache and fps:
        # A stat() beats re-hashing the whole package: we only need to know whether the file moved
        # under us during the ~10s render, and mtime+size answers that for a fraction of the cost.
        try:
            st = os.stat(pptx)
            moved = (st.st_mtime_ns, st.st_size) != pptx_stat
        except OSError:
            moved = True
        if moved:
            skip_cache = True
            print("note: the .pptx changed during the render — not caching fingerprints",
                  file=sys.stderr)
    if skip_cache:
        try:
            os.remove(cache_path)
        except OSError:
            pass
    else:
        try:
            tmp_cache = cache_path + ".tmp"
            with open(tmp_cache, "w", encoding="utf-8") as f:
                json.dump({"fingerprints": fps}, f)
            os.replace(tmp_cache, cache_path)
        except OSError:
            try:
                os.remove(cache_path)
            except OSError:
                pass
            print("note: could not write the render cache — the next --fast will do a full render",
                  file=sys.stderr)

    # The PDF is an INTERMEDIATE of this render (pptx -> PDF -> PNG), so it always exists. Whether
    # it is promoted to a deliverable beside the .pptx is the user's call at hand-off.
    pdf_dest = pdf
    if deliverables and pdf is None:
        die("--deliverables needs a full-deck render; re-run without --fast")
    if deliverables:
        pdf_dest = os.path.join(os.path.dirname(os.path.abspath(pptx)) or ".",
                                os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
        try:
            if os.path.abspath(pdf_dest) != os.path.abspath(pdf):
                shutil.move(pdf, pdf_dest)   # move, not replace: the source is a temp dir that may
        except OSError:                      # sit on a different filesystem
            pdf_dest = pdf                   # couldn't move (odd mount/permissions)

    # Self-contained flip-through viewer — parked BESIDE the .pptx (deck root), same as the PDF, so
    # the user finds it without digging into render/. It references the PNGs through the render subdir
    # (relative to the viewer's own location), so a plain double-click works. One file:// link, any
    # browser, any OS (arrow keys / click / thumbnail strip). Zero dependencies, zero network.
    deck_dir = os.path.dirname(os.path.abspath(pptx)) or "."
    viewer = None
    if deliverables:
        rel = os.path.relpath(os.path.abspath(out), deck_dir)
        pref = "" if rel in (".", "") else rel.replace(os.sep, "/").rstrip("/") + "/"
        slides = [pref + "slide{:02d}.png".format(i) for i in range(1, n_pages + 1)]
        viewer = os.path.join(deck_dir, "viewer.html")
        try:
            with open(viewer, "w", encoding="utf-8") as f:
                f.write(_viewer_html(os.path.splitext(os.path.basename(pptx))[0], slides))
        except OSError:
            viewer = None
    # sweep a stale viewer.html left inside the render dir by an older build (it now lives at root)
    stale = os.path.join(out, "viewer.html")
    if viewer and os.path.abspath(stale) != os.path.abspath(viewer) and os.path.exists(stale):
        try: os.remove(stale)
        except OSError: pass
    if incremental:
        print("{}: {} of {} slides re-rendered ({}) -> {}".format(
            "slides render" if only is not None else "fast render",
            len(keep), len(fps), ", ".join(str(i + 1) for i in keep), out))
        # If a hand-off already produced the deck-root pair, they now lag the deck. Say so loudly:
        # a stale PDF someone opens and reviews is the failure this whole path is built to avoid.

    else:
        print("rendered {} slides -> {}".format(n_pages, out))
        if fast and skip_reason:
            print("(--fast fell back to a full render: {})".format(skip_reason))
    _cs = _contact_sheet(out, n_pages)
    if _cs:
        print("contact sheet -> {}  (DECK-LEVEL view only: rhythm, bookends, form variety, "
              "chrome repetition. Body text is ~8px here and unreadable — the per-slide visual "
              "read is still required and this does not replace it.)".format(", ".join(_cs)))
    if not deliverables:
        print("pdf/viewer: not generated (deck still in progress) — at hand-off, once the user "
              "confirms the deck is final, re-run with --deliverables")
    else:
        print("pdf: {}".format(pdf_dest))
    if viewer:
        print("preview: {}  (open in a browser; arrow keys flip)".format(
            Path(viewer).resolve().as_uri()))
    # Any render that is NOT the hand-off run leaves an already-delivered pair behind the deck.
    # This must fire on the full path too: re-rendering a delivered deck is the likeliest way to
    # end up with a PDF someone opens and reviews after it stopped matching the .pptx.
    if not deliverables:
        _stale = [f for f in (os.path.splitext(os.path.basename(pptx))[0] + ".pdf", "viewer.html")
                  if os.path.isfile(os.path.join(_deck_dir, f))]
        if _stale:
            print("WARNING: {} at the deck root {} now STALE — re-run with --deliverables (and "
                  "without --fast) before handing the deck over".format(
                      " and ".join(_stale), "is" if len(_stale) == 1 else "are"), file=sys.stderr)
    print("next: python3 {} {} --renders {}  # render-time lint, then the actor-critic loop".format(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_deck.py"), pptx, out))
    # The render self-check is the single largest round-trip sink in the pipeline: one image Read
    # per slide, one message each, every message re-sending the whole conversation. SKILL.md Step 5
    # says to batch those reads, and a measured run showed the prose alone did not move it — the
    # build chained its shell commands 98% of the time and still read every PNG in its own message.
    # So the instruction is repeated HERE, in tool output the reader cannot skip, with the actual
    # paths already assembled. Cheap to print, and it names the files so there is nothing to look up.
    _pngs = sorted(f for f in os.listdir(out)
                   if f.startswith("slide") and f.endswith(".png")) if os.path.isdir(out) else []
    if len(_pngs) > 1:
        _sheets = sorted(f for f in os.listdir(out)
                         if f == "contact.png" or f.startswith("contact_"))
        _cs = ", ".join(os.path.join(out, f) for f in _sheets)
        if _sheets:
            # Deck-level FIRST, then every page. The order matters: the sheet tells you which
            # pages deserve scrutiny, and it is worthless for judging any of them — body text is
            # ~8px there. It is a way to arrive at the per-slide read informed, never a way to
            # skip it, and the line below still asks for ALL of them.
            print("      first read {}  — the whole deck at once: rhythm, bookends, form "
                  "variety, chrome repetition. It CANNOT settle a per-slide question (body text "
                  "is unreadable at that size), so it never replaces the reads below.".format(_cs))
        print("      then read ALL {} slide PNGs in ONE message (one tool block per slide, same "
              "message), and record a one-line verdict per slide:".format(len(_pngs)))
        print("      " + "  ".join(os.path.join(out, f) for f in _pngs))


def _viewer_html(title, slides):
    """Single-file dark flip-through viewer: big slide + thumbnail rail + keyboard/click nav."""
    import json
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — preview</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ margin: 0; box-sizing: border-box; }}
  body {{ background: #17191f; color: #cfd4de; font: 13px/1.4 system-ui, sans-serif;
         height: 100vh; display: flex; flex-direction: column; user-select: none; }}
  header {{ padding: 8px 14px; display: flex; align-items: center; gap: 12px; }}
  header b {{ color: #fff; font-weight: 600; }}
  #stage {{ flex: 1; display: flex; align-items: center; justify-content: center;
            min-height: 0; padding: 0 12px; cursor: pointer; }}
  #main {{ max-width: 100%; max-height: 100%; box-shadow: 0 6px 30px rgba(0,0,0,.5);
           border-radius: 4px; }}
  #rail {{ display: flex; gap: 6px; overflow-x: auto; padding: 10px 14px; flex: none; }}
  #rail img {{ height: 62px; border-radius: 3px; opacity: .45; cursor: pointer;
               border: 2px solid transparent; }}
  #rail img.on {{ opacity: 1; border-color: #5b8def; }}
  #num {{ margin-left: auto; font-variant-numeric: tabular-nums; color: #8a93a6; }}
  kbd {{ background:#2a2e38; border-radius:3px; padding:1px 5px; font-size:11px; color:#9aa3b2; }}
</style></head><body>
<header><b>{title}</b><span>&larr;/&rarr; or click to flip &nbsp;<kbd>F</kbd> fullscreen</span><span id="num"></span></header>
<div id="stage"><img id="main" alt="slide"></div>
<div id="rail"></div>
<script>
const S = {slides}; let i = 0;
const main = document.getElementById('main'), rail = document.getElementById('rail'),
      num = document.getElementById('num');
S.forEach((src, k) => {{ const t = document.createElement('img'); t.src = src; t.loading = 'lazy';
  t.onclick = () => go(k); rail.appendChild(t); }});
function go(k) {{ i = (k + S.length) % S.length; main.src = S[i];
  num.textContent = (i + 1) + ' / ' + S.length;
  [...rail.children].forEach((t, k2) => t.classList.toggle('on', k2 === i));
  rail.children[i].scrollIntoView({{ inline: 'center', block: 'nearest', behavior: 'smooth' }});
  if (i + 1 < S.length) (new Image()).src = S[i + 1]; }}
document.getElementById('stage').onclick = () => go(i + 1);
addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') go(i + 1);
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') go(i - 1);
  else if (e.key === 'Home') go(0); else if (e.key === 'End') go(S.length - 1);
  else if (e.key.toLowerCase() === 'f') document.documentElement.requestFullscreen?.(); }});
go(0);
</script></body></html>
""".format(title=title.replace("&", "&amp;").replace("<", "&lt;"), slides=json.dumps(slides))


if __name__ == "__main__":
    main(sys.argv[1:])
