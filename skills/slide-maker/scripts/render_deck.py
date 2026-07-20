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


def _tail(text, limit=4000):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return "...<truncated>...\n" + text[-limit:]


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


def _render_pdf(soffice, src, outdir):
    """pptx -> pdf via a throwaway LibreOffice profile. Returns (pdf_path, result, cmd)."""
    profile = tempfile.mkdtemp(prefix="lo_render_")
    try:
        cmd = [soffice, "-env:UserInstallation=" + Path(profile).as_uri(),
               "--headless", "--convert-to", "pdf", "--outdir", outdir, src]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=300)
        except subprocess.TimeoutExpired:
            die("LibreOffice render exceeded 300s and was killed — the .pptx may be malformed or "
                "hostile (e.g. a decompression bomb). Nothing was produced from {}.".format(src))
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    return (os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf"), result, cmd)


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
    argv = list(argv)
    while "--fast" in argv:
        argv.remove("--fast")
        fast = True
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
    if not argv:
        die("usage: python render_deck.py /path/to/deck.pptx [out_dir] [--fast] [--deliverables]")
    pptx = argv[0]
    out = argv[1] if len(argv) > 1 else "./render"

    if not os.path.isfile(pptx):
        die("no such file: " + pptx)

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
    incremental = fast and changed is not None and 0 < len(changed) < len(fps)
    if fast and changed is not None and len(changed) == len(fps) and len(fps):
        # Every slide changed (a rebuild that touched everything, or a deck-global edit such as a
        # theme/canvas change). A subset of "all slides" is just a full render with extra steps.
        skip_reason = "every slide changed"
    if fast and changed is not None and not changed:
        print("no slide changed since the last render — nothing to re-render")
        print("next: python3 {} {} --renders {}".format(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_deck.py"), pptx, out))
        return 0


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
                if e == "viewer.html" and _out_is_deck_dir:
                    continue                    # that is the hand-off preview, not our render output
                if (e.startswith(("slide", "thumb_")) and e.endswith(("png",))) or e == "viewer.html":
                    try:
                        os.remove(os.path.join(out, e))
                    except OSError:
                        pass
    os.makedirs(out, exist_ok=True)

    # Give this invocation its OWN LibreOffice profile: lets parallel renders (the
    # large-deck section fan-out) run at once without fighting a shared profile lock,
    # and lets the render work even while the user has the LibreOffice GUI open.
    # Without this, concurrent/coexisting soffice calls silently produce no PDF.
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
    if tmp_dir:
        import atexit
        atexit.register(shutil.rmtree, tmp_dir, True)   # a die() mid-render must not leak a deck copy
    pdf, result, cmd = _render_pdf(soffice, src_pptx, tmp_dir if incremental else out)
    if not os.path.isfile(pdf):
        detail = [
            "LibreOffice produced no PDF from {}.".format(pptx),
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

    try:
        import fitz  # pymupdf
    except ImportError:
        die("pymupdf not installed — run: {} -m pip install pymupdf".format(
            os.path.basename(sys.executable) or "python"))

    doc = fitz.open(pdf)
    skip_cache = False
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
        for i, page in pages:
            page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(
                os.path.join(out, "slide{:02d}.png".format(i)))
        # bookend thumbnails (~240px wide) for the critic's poster test — first + last slide small,
        # the scale at which a cover either survives or dies. Same PyMuPDF path, no new deps.
        if pages:
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
                os.replace(pdf, pdf_dest)
        except OSError:
            pdf_dest = pdf                 # couldn't move (odd mount/permissions) — it stays in out/

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
        print("fast render: {} of {} slides re-rendered ({}) -> {}".format(
            len(keep), len(fps), ", ".join(str(i + 1) for i in keep), out))
        # If a hand-off already produced the deck-root pair, they now lag the deck. Say so loudly:
        # a stale PDF someone opens and reviews is the failure this whole path is built to avoid.

    else:
        print("rendered {} slides -> {}".format(n_pages, out))
        if fast and skip_reason:
            print("(--fast fell back to a full render: {})".format(skip_reason))
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
    if not deliverables and not _out_is_deck_dir:
        _stale = [f for f in (os.path.splitext(os.path.basename(pptx))[0] + ".pdf", "viewer.html")
                  if os.path.isfile(os.path.join(_deck_dir, f))]
        if _stale:
            print("WARNING: {} at the deck root {} now STALE — re-run with --deliverables (and "
                  "without --fast) before handing the deck over".format(
                      " and ".join(_stale), "is" if len(_stale) == 1 else "are"), file=sys.stderr)
    print("next: python3 {} {} --renders {}  # render-time lint, then the actor-critic loop".format(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_deck.py"), pptx, out))


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
