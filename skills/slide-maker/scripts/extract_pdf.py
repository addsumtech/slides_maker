#!/usr/bin/env python3
"""extract_pdf — pull a figure OUT of a source PDF (paper / report) as a clean PNG.

The skill's first rule of figures is *use the source's own figure, whole* (step 4) — but
a figure trapped in a PDF can't be placed until it's a PNG. This gets it out, three ways,
in order of how often you want them:

1. render_page  — rasterise a WHOLE page to high-DPI PNG. The most reliable: it captures
   the figure exactly as it appears (vector + text + raster composited), so a multi-panel
   figure, axis labels, and a colour bar all come through. Then crop/place it in the build.
2. crop_region  — rasterise just a rectangle of a page (a single figure on a busy page),
   so you don't carry the surrounding body text. Give the rectangle in page POINTS
   (72/inch, origin top-left) or as fractions of the page with frac=True.
3. extract_images — dump the page's EMBEDDED raster images at native resolution. Highest
   quality for a single photo/bitmap figure, but a vector chart or a multi-image panel can
   come out fragmented or empty — fall back to render_page/crop_region when it does.

Why rasterise rather than always extract: a paper figure is usually vector + text, not one
bitmap; rendering the page is what reproduces what the reader actually sees. Use a high DPI
(>=300) so the placed figure stays crisp when it fills a slide.

PREFERRED — auto-detect & crop figures straight from the paper (no manual coordinates,
no asking the user for originals). It anchors on captions ("Figure N" / "Fig. N" / "Table N"),
grows into the adjacent graphics bounded by body text + neighbouring captions, then snaps to
content. This is the *primary* path; the manual page/crop commands below are the fallback.
    python extract_pdf.py figures paper.pdf            # list every detected figure + checks
    python extract_pdf.py figures paper.pdf 4          # just page 4
    python extract_pdf.py figure  paper.pdf 2 fig.png  # render detected figure #2 (auto-trimmed)
    python extract_pdf.py autofig paper.pdf figs/      # render ALL detected figures to figs/
`figures` prints each box with cov= (graphics coverage), bodyov= (body-text overlap) and a
"⚠ CHECK" flag when a crop looks suspect (low coverage, body/foreign-caption bleed) — ALWAYS
view a rendered crop before using it, and for a flagged one fall back to the manual loop.

Quick start (manual fallback):
    python extract_pdf.py info paper.pdf                      # page count + sizes
    python extract_pdf.py page paper.pdf 4 fig.png --dpi 300  # page 4 (1-based) -> PNG
    python extract_pdf.py crop paper.pdf 4 fig.png 60 90 540 360
    python extract_pdf.py crop paper.pdf 4 fig.png 0.1 0.12 0.95 0.55 --frac
    python extract_pdf.py images paper.pdf 4 figdir/          # embedded images -> figdir/

LONG-SOURCE MODE (a book / very long PDF — map before you read, then read the parts that matter):
    python extract_pdf.py map      book.pdf                   # structural skeleton: TOC + word-density
    python extract_pdf.py headings book.pdf 1 400            # reconstruct a skeleton for a NO-TOC book
    python extract_pdf.py text     book.pdf 40 72 ch3.txt    # dump pages 40-72 for a chunked read
`map` dumps NO body text (triage only: page + CJK-aware load/token estimate + the author's own
TOC/bookmarks + a binned density strip, and a ⚠ if the doc is scanned/non-PDF); `headings` emits
candidate heading lines by font-size outlier when there's no embedded TOC; `text` dumps a 1-indexed
inclusive page range, keeping PAGE markers so every claim traces back to a real page. Works on any
fitz-openable doc (PDF/EPUB/…); convert .docx/.md/web to PDF first. See the content-planner's
long-source method.

To find a manual crop box: render the page once, open the PNG, read off the figure's pixel
box with `crop_helper.py grid`, divide by the render scale (dpi/72) to get points — or use
--frac and eyeball fractions. Importable: from extract_pdf import find_figures, render_figure.
"""
import sys
import os
import re
import fitz   # PyMuPDF

# _rect_area_compat: pymupdf>=1.26 removed Rect.get_area()
if not hasattr(fitz.Rect, "get_area"):
    fitz.Rect.get_area = lambda self, unit=None: abs(self.width * self.height)
    fitz.IRect.get_area = lambda self, unit=None: abs(self.width * self.height)


def _open(pdf):
    if not os.path.exists(pdf):
        raise SystemExit(f"no such file: {pdf}")
    try:
        doc = fitz.open(pdf)
        _ = doc.page_count                       # force a parse so a corrupt file fails HERE, cleanly
    except Exception as e:                       # corrupt / not a document fitz understands
        raise SystemExit(f"can't open {pdf!r} as a document ({e.__class__.__name__}: {e}) — "
                         "expected a complete, non-corrupt PDF (or EPUB/XPS/…).")
    if doc.needs_pass:
        raise SystemExit("PDF is password-protected — can't read it. Supply an unlocked copy.")
    return doc


_CJK = re.compile(r"[㐀-鿿豈-﫿぀-ヿ가-힯]")


def _load(s):
    """Reading load = latin words + CJK chars / 2 (matches the skill's lint/plan counter, so the
    `source size:` trigger is correct for Chinese/Japanese/Korean, where whitespace-splitting would
    undercount 10-30x)."""
    cjk = len(_CJK.findall(s))
    latin = len(_CJK.sub(" ", s).split())
    return latin + cjk // 2


def info(pdf):
    """Print page count and per-page size in points and inches — so you can pick a page
    and reason about crop coordinates."""
    doc = _open(pdf)
    print(f"{pdf}: {doc.page_count} pages")
    for i, page in enumerate(doc, start=1):
        r = page.rect
        print(f"  p{i}: {r.width:.0f} x {r.height:.0f} pt  "
              f"({r.width/72:.2f} x {r.height/72:.2f} in)"
              f"  images={len(page.get_images())}")
    doc.close()


def outline_map(pdf, bins=30):
    """STRUCTURAL SKELETON for long-source mode — the cheap 'map before you read' pass.
    Prints page/word/token estimates, the embedded TOC/bookmarks (the author's own
    hierarchy = the first prioritisation signal), and a binned word-density strip showing
    where prose BULK sits — a SHAPE signal (front/back-matter, figure/reference pages),
    NOT an importance signal (the TOC + the deck's purpose drive what matters). Dumps NO
    body text — this is triage; pull the chapters that matter with `text` afterwards."""
    doc = _open(pdf)
    wpp = [_load(page.get_text("text")) for page in doc]
    total = sum(wpp)
    pc = doc.page_count
    fmt = (doc.metadata or {}).get("format", "") or "?"
    note = "" if doc.is_pdf else f"  ⚠ opened as {fmt}, NOT a PDF — confirm this is the file you meant"
    print(f"{pdf}: {pc} pages · ~{total:,} load-words · ~{total * 4 // 3:,} tokens est.  [{fmt}]{note}")
    # scanned / image-only / DRM guard — get_text() returns "" on image-only pages, so a
    # scanned book would otherwise print a normal-looking (but empty) skeleton.
    empty = sum(1 for w in wpp if w == 0)
    if total == 0 or empty >= max(1, int(0.9 * pc)):
        print(f"\n⚠ NO extractable text (~{total} words across {pc} pages · {empty} empty): this PDF "
              "is almost certainly SCANNED / image-only or DRM-locked. `map`/`text` cannot read it — "
              "request a text-based PDF, run OCR, or ask the user for the specific chapters. Do NOT "
              "infer contents from the skeleton below.")
    toc = doc.get_toc(simple=True)          # [[level, title, page], ...]
    if toc:
        print(f"\nTABLE OF CONTENTS / BOOKMARKS ({len(toc)} entries):")
        for lvl, title, pg in toc:
            print(f"  {'  ' * max(lvl - 1, 0)}p{pg:<5} {title}")
    else:
        print("\n(no embedded TOC/bookmarks — reconstruct a skeleton with `text`: scan for heading "
              "lines / chapter titles, or fall back to fixed-size page windows; triage costs more here)")
    print("\nWORD DENSITY (binned — text-dense vs sparse regions; a SHAPE cue, not importance):")
    nb = min(pc, bins)
    step = -(-pc // nb)                      # ceil division
    peak = max((sum(wpp[b:b + step]) for b in range(0, pc, step)), default=1) or 1
    for b in range(0, pc, step):
        w = sum(wpp[b:b + step])
        bar = "#" * int(round(24 * w / peak))
        print(f"  p{b + 1:>4}-{min(b + step, pc):<4} {w:>6}  {bar}")
    doc.close()


def dump_text(pdf, start, end, out=None):
    """Dump plain text of a 1-indexed INCLUSIVE page range — the chunked-read primitive for
    long-source mode. Read a chapter at a time and keep the PAGE markers, so every claim you
    later put on a slide traces back to a real page (the comprehension brief's hard rule).
    Returns 0 on success, 1 on an unusable range (so the caller can fail loudly)."""
    doc = _open(pdf)
    pc = doc.page_count
    if start < 1 or end < 1 or start > end or start > pc:
        doc.close()
        print(f"error: bad page range {start}-{end} — need 1 ≤ start ≤ end ≤ {pc} (PDF has {pc} pages)")
        return 1
    start = max(1, start)
    end = min(end, pc)
    parts = []
    body_words = 0                           # count BODY only (CJK-aware), never the PAGE markers
    for p in range(start, end + 1):
        t = doc[p - 1].get_text("text")
        body_words += _load(t)
        parts.append(f"\n===== PAGE {p} =====\n" + t)
    doc.close()
    text = "".join(parts)
    if body_words == 0:
        print(f"⚠ pages {start}-{end} contain NO extractable text (0 words) — likely "
              "scanned / image-only; this range needs OCR, don't infer its contents.")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote pages {start}-{end} -> {out} ({body_words:,} load-words)")
    else:
        print(text)
    return 0


def headings(pdf, start=1, end=None, limit=250):
    """Reconstruct a skeleton for a NO-TOC book — emit candidate heading lines (font-size
    outliers: larger than the range's dominant body size) with their page, so a book with no
    embedded bookmarks can still be triaged into a Source-coverage map WITHOUT reading every
    word. A heuristic aid, not ground truth — view it and pick the real chapter breaks."""
    from collections import Counter
    doc = _open(pdf)
    pc = doc.page_count
    start = max(1, start)
    end = min(end or pc, pc)
    if start > end:
        doc.close(); print(f"error: bad page range {start}-{end} (PDF has {pc} pages)"); return 1
    sizes = Counter()
    spans = []
    for p in range(start, end + 1):
        for blk in doc[p - 1].get_text("dict").get("blocks", []):
            for line in blk.get("lines", []):
                txt = "".join(sp["text"] for sp in line.get("spans", [])).strip()
                if not txt or not line.get("spans"):
                    continue
                sz = round(max(sp["size"] for sp in line["spans"]), 1)
                sizes[sz] += len(txt)
                spans.append((p, sz, txt))
    doc.close()
    if not sizes:
        print("no extractable text (scanned/image-only) — can't reconstruct headings; needs OCR")
        return 1
    body = sizes.most_common(1)[0][0]        # dominant size = body text
    print(f"candidate headings (body ≈ {body}pt; lines ≥ {body * 1.15:.1f}pt, ≤ 90 chars):")
    shown = 0
    for p, sz, txt in spans:
        if sz >= body * 1.15 and len(txt) <= 90:
            print(f"  p{p:<5} {sz:>5}pt  {txt}")
            shown += 1
            if shown >= limit:
                break
    if not shown:
        print("  (no font-size outliers — the book may be single-size; fall back to fixed-size page "
              "windows and title each window from its first line)")
    return 0


def render_page(pdf, page_no, out, dpi=300):
    """Rasterise a whole page (1-based) to a PNG at `dpi`. Returns the output path.
    This is the default, most reliable extractor — what the reader sees, composited."""
    doc = _open(pdf)
    page = doc[page_no - 1]
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(out)
    doc.close()
    print(f"wrote {out}  ({pix.width}x{pix.height}px @ {dpi}dpi)")
    return out


def crop_region(pdf, page_no, out, x0, y0, x1, y1, dpi=300, frac=False):
    """Rasterise a rectangle of a page (1-based) to PNG. Coordinates in page POINTS
    (origin top-left), or as fractions 0..1 of the page when frac=True. Use this to lift a
    single figure off a page that also has body text."""
    doc = _open(pdf)
    page = doc[page_no - 1]
    r = page.rect
    if frac:
        x0, y0, x1, y1 = x0 * r.width, y0 * r.height, x1 * r.width, y1 * r.height
    clip = fitz.Rect(x0, y0, x1, y1)
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
    pix.save(out)
    doc.close()
    print(f"wrote {out}  ({pix.width}x{pix.height}px, clip {clip})")
    return out


def extract_images(pdf, page_no, out_dir, min_px=120):
    """Dump the page's embedded raster images (native resolution) to out_dir, skipping
    anything smaller than min_px on a side (filters logos/rules/icons). Returns the list
    of written paths. Best for a single photo/bitmap figure; a vector chart won't appear
    here — use render_page/crop_region for those."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    doc = _open(pdf)
    page = doc[page_no - 1]
    written = []
    for k, img in enumerate(page.get_images(full=True), start=1):
        xref = img[0]
        try:
            pix = fitz.Pixmap(doc, xref)
        except Exception:
            continue
        if pix.width < min_px or pix.height < min_px:
            continue
        if pix.n - pix.alpha >= 4:          # CMYK/other -> convert to RGB
            pix = fitz.Pixmap(fitz.csRGB, pix)
        path = os.path.join(out_dir, f"p{page_no}_img{k}_{pix.width}x{pix.height}.png")
        pix.save(path)
        written.append(path)
        print(f"wrote {path}")
    doc.close()
    if not written:
        print("no embedded raster images above min_px — try `page` or `crop` instead "
              "(the figure is likely vector + text, not a bitmap).")
    return written


# ===================================================================== figure detection
import re
from collections import Counter

_CAP = re.compile(r'^\s*(fig(?:ure)?|tab(?:le)?|scheme|algorithm)\.?\s*'
                  r'(\d+|[ivxlc]+|[A-Z])\b', re.I)


def _spans(b):
    return [sp for ln in b.get("lines", []) for sp in ln.get("spans", [])]


def _btext(b):
    return "".join(sp["text"] for sp in _spans(b))


def _first_line(b):
    lns = b.get("lines", [])
    return "".join(sp["text"] for sp in lns[0].get("spans", [])) if lns else ""


def _text_blocks(page):
    return [b for b in page.get_text("dict")["blocks"] if b.get("type") == 0
            and b.get("lines")]


def _modal_size(blocks):
    c = Counter()
    for b in blocks:
        for sp in _spans(b):
            c[round(sp["size"])] += max(1, len(sp["text"]))
    return c.most_common(1)[0][0] if c else 10.0


def _is_body(b, modal, page_w):
    """A full-prose paragraph (NEVER part of a figure) — used to bound figure growth.
    Short/centered/odd-font blocks (captions, axis labels, legends, sub-panel letters)
    are NOT body, so they can live inside a figure."""
    if len(b.get("lines", [])) < 2:
        return False
    r = fitz.Rect(b["bbox"])
    if r.width < 0.30 * page_w:
        return False
    sizes = [sp["size"] for sp in _spans(b)] or [modal]
    return abs(sum(sizes) / len(sizes) - modal) <= 1.5


def _cluster(rects, tol=8):
    """Union rects that touch/are within `tol` points, repeatedly, until stable."""
    rects = [fitz.Rect(r) for r in rects]
    changed = True
    while changed:
        changed = False
        out, used = [], [False] * len(rects)
        for i in range(len(rects)):
            if used[i]:
                continue
            r = fitz.Rect(rects[i])
            for j in range(i + 1, len(rects)):
                if used[j]:
                    continue
                infl = fitz.Rect(r.x0 - tol, r.y0 - tol, r.x1 + tol, r.y1 + tol)
                if infl.intersects(rects[j]):
                    r |= rects[j]; used[j] = True; changed = True
            used[i] = True; out.append(r)
        rects = out
    return rects


def _graphics(page, R):
    """Figure-sized graphics rects: clustered vector drawings + raster placements, with
    hairline rules / page borders / tiny specks / page-spanning thin rules filtered out."""
    rects = []
    if hasattr(page, "cluster_drawings"):
        try:
            rects += list(page.cluster_drawings(x_tolerance=6, y_tolerance=6))
        except Exception:
            rects += [fitz.Rect(d["rect"]) for d in page.get_drawings()]
    else:
        rects += [fitz.Rect(d["rect"]) for d in page.get_drawings()]
    for im in page.get_images(full=True):
        try:
            rects += list(page.get_image_rects(im[0]))
        except Exception:
            pass
    try:
        rects += [fitz.Rect(ii["bbox"]) for ii in page.get_image_info(xrefs=True)]
    except Exception:
        pass
    pa = R.get_area()
    keep = []
    for r in rects:
        r = r & R
        if r.is_empty or r.is_infinite:
            continue
        if r.width < 8 or r.height < 8:                       # speck / hairline
            continue
        if r.width > 0.92 * R.width and r.height < 6:         # full-width rule
            continue
        if r.get_area() < 0.004 * pa:                         # too small to be a figure
            continue
        keep.append(r)
    return _cluster(keep, tol=10)


def _xshare(a, b):
    """Horizontal overlap as a fraction of the narrower box — i.e. 'same column?'."""
    ov = min(a.x1, b.x1) - max(a.x0, b.x0)
    m = min(a.width, b.width)
    return ov / m if m > 0 else 0


def _ovfrac(a, b):
    """Area overlap as a fraction of the smaller box."""
    inter = (a & b).get_area()
    m = min(a.get_area(), b.get_area())
    return inter / m if m > 0 else 0


def _table_text_bbox(cap, side_by_kind, blocks, body, cap_rects, R, hdr, ftr):
    """Fallback bbox for a BORDERLESS / rule-only table the graphics path can't see (booktabs
    toprule/midrule/bottomrule are hairlines that `_graphics` filters out, and the cells are
    plain text). Grow the table box from the caption over the CONTIGUOUS run of non-body,
    non-caption text rows on the table's convention side — bounded by body prose, neighbouring
    captions, and the header/footer band — capturing ALL columns/rows and excluding the
    'Table N.' caption line. Returns a fitz.Rect or None when there's nothing table-like."""
    cr = cap["r"]; side = side_by_kind.get("table", "below"); cx = (cr.x0 + cr.x1) / 2
    cand = []
    for b in blocks:
        rb = fitz.Rect(b["bbox"])
        if any(rb.intersects(c2) for c2 in cap_rects):                       # skip captions
            continue
        if any(rb.intersects(bb) and (bb & rb).get_area() > 0.5 * rb.get_area() for bb in body):
            continue                                                          # skip body prose
        if not (rb.x0 - 30 <= cx <= rb.x1 + 30 or _xshare(rb, cr) > 0.2):     # ~same column
            continue
        if side == "below" and rb.y0 < cr.y1 - 2:
            continue
        if side == "above" and rb.y1 > cr.y0 + 2:
            continue
        cand.append(rb)
    if not cand:
        return None
    cand.sort(key=lambda r: r.y0, reverse=(side == "above"))
    band = [cand[0]]                                  # contiguous run adjacent to the caption
    for r in cand[1:]:
        prev = band[-1]
        gap = (r.y0 - prev.y1) if side == "below" else (prev.y0 - r.y1)
        if gap > 1.8 * max(prev.height, r.height):
            break
        band.append(r)
    box = fitz.Rect(band[0])
    for r in band[1:]:
        box |= r
    if side == "below":
        box.y0 = max(box.y0, cr.y1 + 3)
    else:
        box.y1 = min(box.y1, cr.y0 - 3)
    box.y0 = max(box.y0, hdr); box.y1 = min(box.y1, ftr); box &= R
    return box if not box.is_empty else None


def find_figures(pdf, page_no=None):
    """Detect figure/table regions in a born-digital PDF by anchoring on captions
    ("Figure N" / "Fig. N" / "Table N") and growing into the adjacent graphics, bounded by
    body text. Returns a list of dicts: {page, label, kind, side, bbox(points), caption,
    checks}. When a page has graphics but NO caption (a figure-only page), the graphics
    clusters are returned as unlabelled figures. The manual `crop_helper grid`→`crop` loop
    remains the fallback when a `checks` warning shows detection is off."""
    doc = _open(pdf)
    pages = [page_no - 1] if page_no else range(doc.page_count)
    out = []
    for pi in pages:
        page = doc[pi]; R = page.rect
        blocks = _text_blocks(page)
        modal = _modal_size(blocks)
        caps = []
        for b in blocks:
            m = _CAP.match(_first_line(b))
            if m:
                kind = "table" if m.group(1).lower().startswith("tab") else \
                       ("figure" if m.group(1).lower().startswith("fig") else m.group(1).lower())
                caps.append({"r": fitz.Rect(b["bbox"]), "kind": kind,
                             "label": f"{m.group(1).title().split('.')[0]} {m.group(2)}",
                             "text": _btext(b)[:140]})
        cap_rects = [c["r"] for c in caps]
        body = [fitz.Rect(b["bbox"]) for b in blocks
                if _is_body(b, modal, R.width) and not any(fitz.Rect(b["bbox"]).intersects(cr) for cr in cap_rects)]
        margin = 0.12 * R.height

        def _is_chrome(b):
            """Page chrome — a running head / page number / footer: a single text line in
            the page's top or bottom margin. Never part of a figure, so it must be excluded
            from the nonbody set or the grow step will swallow it into an adjacent figure."""
            r = fitz.Rect(b["bbox"])
            return len(b.get("lines", [])) <= 2 and (r.y0 < R.y0 + margin or r.y1 > R.y1 - margin)

        nonbody = [fitz.Rect(b["bbox"]) for b in blocks
                   if not _is_body(b, modal, R.width) and not _is_chrome(b)
                   and not any(fitz.Rect(b["bbox"]).intersects(cr) for cr in cap_rects)]
        gfx = _graphics(page, R)
        hdr, ftr = R.y0 + 0.045 * R.height, R.y1 - 0.045 * R.height
        accepted = []                      # boxes already taken on this page (no overlap)

        def _take(rec):
            """Accept a detection only if it doesn't substantially overlap one already
            taken — dedups the 'same pixels under two labels' and figure/figure swaps."""
            b = fitz.Rect(*rec["bbox"])
            if any(_ovfrac(b, a) > 0.45 for a in accepted):
                return
            accepted.append(b); out.append(rec)

        if not caps:                       # figure-only page: emit graphics clusters
            for g in sorted(gfx, key=lambda r: (r.y0, r.x0)):
                _take(_emit(pi, None, "figure", None, g, "", gfx, body, R, cap_rects))
            continue

        # Caption convention: does the captioned element sit ABOVE its caption (caption-below,
        # the usual figure case) or BELOW it (caption-above, the usual TABLE case)? Decide from
        # the gap between a caption and its nearest graphics cluster on each side. Crucially this
        # is computed PER KIND, not per page: figures and tables follow OPPOSITE conventions, so
        # a page holding both must not be forced to one global side (which would mis-side one of
        # them). Per-kind + a per-caption geometry override (in the loop) handles mixed/stacked
        # layouts; the literature default (figures→above, tables→below) only breaks ties.
        def _near_gap(cr, sign):
            cx = (cr.x0 + cr.x1) / 2; gaps = []
            for g in gfx:
                if _xshare(g, cr) <= 0.2 and not (g.x0 - 24 <= cx <= g.x1 + 24):
                    continue
                if sign < 0 and g.y1 <= cr.y0 + 2:
                    gaps.append(cr.y0 - g.y1)
                elif sign > 0 and g.y0 >= cr.y1 - 2:
                    gaps.append(g.y0 - cr.y1)
            return min(gaps) if gaps else 1e9
        _DEFAULT_SIDE = {"table": "below"}        # tables → body below caption; else above
        side_by_kind = {}
        for kd in {c["kind"] for c in caps}:
            kc = [c for c in caps if c["kind"] == kd]
            a = sum(min(_near_gap(c["r"], -1), 1e6) for c in kc)
            b = sum(min(_near_gap(c["r"], +1), 1e6) for c in kc)
            if a == b:                            # no graphics either side for this kind → prior
                side_by_kind[kd] = _DEFAULT_SIDE.get(kd, "above")
            else:
                side_by_kind[kd] = "above" if a < b else "below"

        for c in caps:
            cr = c["r"]; cx = (cr.x0 + cr.x1) / 2

            # teaser case: caption sits INSIDE a much larger graphics cluster — the whole
            # cluster is the figure (caption is part of its layout); emit it whole.
            host = next((g for g in gfx if (g & cr).get_area() > 0.55 * cr.get_area()
                         and g.get_area() > 4 * cr.get_area()), None)
            if host is not None:
                box = fitz.Rect(host) & R
                # a big cluster can over-merge the figure with body-text vector elements
                # (citation links etc); clamp the box away from body paragraphs.
                for bb in body:
                    if box.intersects(bb) and (bb & box).get_area() > 0.3 * bb.get_area():
                        if bb.y0 >= cr.y1 - 2:
                            box.y1 = min(box.y1, bb.y0 - 1)
                        elif bb.y1 <= cr.y0 + 2:
                            box.y0 = max(box.y0, bb.y1 + 1)
                box.y0 = max(box.y0, hdr); box.y1 = min(box.y1, ftr); box &= R
                if not box.is_empty and box.width > 12 and box.height > 12:
                    _take(_emit(pi, c["label"], c["kind"], "around", box, c["text"], gfx, body, R, cap_rects, c["r"]))
                continue

            def collect(side):
                """Graphics on one side of the caption; a cluster straddling the caption is
                clipped to that side so it still counts (and never includes the caption)."""
                rs = []
                for g in gfx:
                    hov = min(g.x1, cr.x1) - max(g.x0, cr.x0)
                    if hov <= 0 and not (g.x0 - 24 <= cx <= g.x1 + 24):
                        continue
                    if side == "above" and g.y0 < cr.y0 - 2:
                        gg = fitz.Rect(g); gg.y1 = min(gg.y1, cr.y0 - 1)
                        if gg.height > 10:
                            rs.append(gg)
                    elif side == "below" and g.y1 > cr.y1 + 2:
                        gg = fitz.Rect(g); gg.y0 = max(gg.y0, cr.y1 + 1)
                        if gg.height > 10:
                            rs.append(gg)
                return rs

            aRs, bRs = collect("above"), collect("below")
            aA = sum(r.get_area() for r in aRs); bA = sum(r.get_area() for r in bRs)
            if aA == 0 and bA == 0:                # caption with no graphics on either side
                tbox = _table_text_bbox(c, side_by_kind, blocks, body, cap_rects, R, hdr, ftr) \
                    if c["kind"] == "table" else None
                if tbox is not None and tbox.width > 12 and tbox.height > 12:
                    _take(_emit(pi, c["label"], c["kind"], side_by_kind.get("table", "below"),
                                tbox, c["text"], gfx, body, R, cap_rects, c["r"]))
                continue                            # else: a caption with no extractable content
            # Choose the side the captioned element is on. PER-CAPTION GEOMETRY WINS: if one
            # side's graphics clearly hug the caption (gap < 0.6x the other), trust that. Only
            # when both sides are comparably close do we fall back to this caption KIND's
            # convention (figures→above, tables→below) — never a single page-wide vote, so a
            # page mixing a figure and a table sides each correctly.
            kind_side = side_by_kind.get(c["kind"], "above")
            ga, gb = _near_gap(cr, -1), _near_gap(cr, +1)
            if aA == 0:
                side, rs = "below", bRs
            elif bA == 0:
                side, rs = "above", aRs
            elif min(ga, gb) < 0.6 * max(ga, gb):          # one side decisively closer
                side, rs = ("above", aRs) if ga < gb else ("below", bRs)
            elif kind_side == "above" and aA > 0:
                side, rs = "above", aRs
            elif kind_side == "below" and bA > 0:
                side, rs = "below", bRs
            else:
                side, rs = ("above", aRs) if aA >= bA else ("below", bRs)
            box = fitz.Rect(rs[0])
            for r in rs[1:]:
                box |= r
            # Grow to swallow nearby in-figure text (axis labels, legend, panel letters),
            # but measure proximity from the FIXED graphics extent — not the growing box.
            # Measuring from the growing box lets the union chain outward (figure → panel
            # letters → page running-head/footer) and swallow page chrome that is NOT part of
            # the figure. Inflating a fixed graphics box keeps only text that truly hugs it.
            gbox = fitz.Rect(box)
            infl = fitz.Rect(gbox.x0 - 18, gbox.y0 - 18, gbox.x1 + 18, gbox.y1 + 18)
            for t in nonbody:
                if infl.intersects(t):
                    cand = box | t
                    if not any(cand.intersects(bb) and (bb & cand).get_area() > 0.3 * bb.get_area()
                               for bb in body):
                        box = cand
            # never include the caption; clamp to header/footer band & page
            # bound the figure to its OWN band: between this caption and the nearest other
            # caption (same column) on the figure side — stops a caption grabbing a
            # neighbour's figure/table on dense multi-element pages.
            others = [o["r"] for o in caps if o is not c and _xshare(o["r"], cr) > 0.3]
            # Clamp to the figure's own band with a 5pt gap from EVERY caption (its own and
            # the neighbour's) so the render pad can't bleed back into adjacent caption text.
            if side == "above":
                lim = max([o.y1 for o in others if o.y1 <= cr.y0 - 2] + [hdr])
                box.y0 = max(box.y0, lim + 5); box.y1 = min(box.y1, cr.y0 - 5)
            else:
                lim = min([o.y0 for o in others if o.y0 >= cr.y1 + 2] + [ftr])
                box.y1 = min(box.y1, lim - 5); box.y0 = max(box.y0, cr.y1 + 5)
            box &= R
            if box.is_empty or box.width < 12 or box.height < 12:
                continue
            _take(_emit(pi, c["label"], c["kind"], side, box, c["text"], gfx, body, R, cap_rects, c["r"]))
    doc.close()
    return out


def _emit(pi, label, kind, side, box, caption, gfx, body, R, cap_rects=(), self_cap=None):
    """Package a detection + run cheap geometric validity checks so the caller can flag a
    suspect crop. The crucial mislocalization check is `foreign_caption`: if the crop
    swallows a DIFFERENT figure/table's caption it has bled into a neighbour — the silent
    failure mode on dense pages — so it's flagged even when body-text overlap is low."""
    A = box.get_area() or 1
    gcov = sum((g & box).get_area() for g in gfx) / A
    bover = max([(b & box).get_area() / b.get_area() for b in body if b.intersects(box)] or [0])
    ar = box.width / box.height if box.height else 0
    foreign = any(cr is not self_cap and (cr & box).get_area() > 0.5 * cr.get_area()
                  for cr in cap_rects)
    checks = {
        "graphics_coverage": round(min(gcov, 1.0), 2),
        "body_text_overlap": round(bover, 2),
        "aspect": round(ar, 2),
        "foreign_caption": bool(foreign),
        "in_page": bool((box & R).get_area() >= 0.999 * box.get_area()),
    }
    checks["ok"] = (checks["graphics_coverage"] >= 0.40 and checks["body_text_overlap"] <= 0.20
                    and 0.08 <= ar <= 14 and checks["in_page"] and not foreign)
    return {"page": pi + 1, "label": label, "kind": kind, "side": side,
            "bbox": [round(box.x0, 1), round(box.y0, 1), round(box.x1, 1), round(box.y1, 1)],
            "caption": caption, "checks": checks}


def _content_edges(png_path, edge_px=3, tol=26, frac=0.18):
    """PIXEL self-check: which edges of the rendered PNG have content running flush to the
    border (so the crop likely CLIPS a legend/axis/colour bar there). Background is estimated
    from the four corners; an edge is 'content' if > `frac` of its `edge_px`-deep strip differs
    from background by > `tol`. Returns a set ⊆ {'top','bottom','left','right'} (empty = clean)."""
    try:
        from PIL import Image
    except Exception:
        return set()
    im = Image.open(png_path).convert("RGB"); W, H = im.size
    if W < 2 * edge_px or H < 2 * edge_px:
        return set()
    px = im.load()
    cs = [px[0, 0], px[W - 1, 0], px[0, H - 1], px[W - 1, H - 1]]
    bg = tuple(sorted(c[i] for c in cs)[len(cs) // 2] for i in range(3))   # median corner
    def on(p):
        return (abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2])) > tol
    out = set()
    if sum(on(px[x, y]) for y in range(edge_px) for x in range(W)) > frac * edge_px * W:
        out.add("top")
    if sum(on(px[x, y]) for y in range(H - edge_px, H) for x in range(W)) > frac * edge_px * W:
        out.add("bottom")
    if sum(on(px[x, y]) for x in range(edge_px) for y in range(H)) > frac * edge_px * H:
        out.add("left")
    if sum(on(px[x, y]) for x in range(W - edge_px, W) for y in range(H)) > frac * edge_px * H:
        out.add("right")
    return out


def render_figure(pdf, bbox, out, dpi=300, pad=3, do_trim=True):
    """Render a detected figure bbox (page points) to PNG, then SELF-CHECK the actual pixels and
    auto-correct the two universal partial-crop failures before returning:
      • BLEED — shrink the box away from any caption / lone page-number text block that would
        fall inside the padded clip, so page prose can't render into the figure;
      • CLIP — render, then read the PNG edges (`_content_edges`); if content runs flush to an
        edge that ISN'T the page boundary, the bbox under-covers there (a colour bar/axis just
        outside it), so grow the pad on that side and re-render (bounded retries).
    Then snap-to-content trim. Prints an [ok] / [clip-fixed] / [CLIP?] / [bleed-fixed] status.
    pad is in points; bbox = (page_no, x0, y0, x1, y1)."""
    doc = _open(pdf)
    pno, x0, y0, x1, y1 = bbox
    page = doc[pno - 1]; R = page.rect
    zoom = dpi / 72.0
    box = fitz.Rect(x0, y0, x1, y1)
    # --- BLEED guard: keep captions / page numbers out of the padded clip ---
    bled = False
    for b in _text_blocks(page):
        rb = fitz.Rect(b["bbox"]); txt = _first_line(b).strip()
        if not (_CAP.match(txt) or (txt.isdigit() and len(txt) <= 4)):
            continue
        infl = fitz.Rect(box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
        if not infl.intersects(rb):
            continue
        midy = (box.y0 + box.y1) / 2
        if rb.y1 <= midy and rb.y1 + 1 > box.y0 - pad:        # above-ish → push top down
            box.y0 = max(box.y0, rb.y1 + 2); bled = True
        elif rb.y0 >= midy and rb.y0 - 1 < box.y1 + pad:      # below-ish → pull bottom up
            box.y1 = min(box.y1, rb.y0 - 2); bled = True
    # --- CLIP guard: render, read edges, grow pad on under-covered sides, retry ---
    pads = {"top": pad, "bottom": pad, "left": pad, "right": pad}
    status = "ok"
    for _ in range(4):
        clip = fitz.Rect(box.x0 - pads["left"], box.y0 - pads["top"],
                         box.x1 + pads["right"], box.y1 + pads["bottom"]) & R
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False).save(out)
        edges = _content_edges(out)
        if not edges:
            break
        at = {"top": clip.y0 <= R.y0 + 0.5, "bottom": clip.y1 >= R.y1 - 0.5,
              "left": clip.x0 <= R.x0 + 0.5, "right": clip.x1 >= R.x1 - 0.5}
        grew = False
        for e in edges:
            if not at[e] and pads[e] < pad + 30:               # cap total growth
                pads[e] += 10; grew = True
        if not grew:
            status = "CLIP?"                                   # flush at a page bound — genuine
            break
        status = "clip-fixed"
    else:
        status = "CLIP?"
    doc.close()
    if bled and status == "ok":
        status = "bleed-fixed"
    if do_trim:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from crop_helper import trim
            trim(out, out, margin=0.012)
        except Exception as e:
            print(f"(trim skipped: {e})")
    print(f"wrote {out}  [{status}]")
    return out


def _print_figures(pdf, page_no=None):
    figs = find_figures(pdf, page_no)
    if not figs:
        print("no figures detected (try `page`/`crop`, or the page may be text-only/scanned)")
    for i, f in enumerate(figs):
        warn = "" if f["checks"]["ok"] else "  ⚠ CHECK (verify by viewing)"
        print(f"[{i}] p{f['page']} {f['label'] or '(figure)'} {f['bbox']} "
              f"cov={f['checks']['graphics_coverage']} bodyov={f['checks']['body_text_overlap']} "
              f"ar={f['checks']['aspect']}{warn}")
        if f["caption"]:
            print(f"      {f['caption']!r}")
    return figs


def _autofig(pdf, out_dir, dpi=300):
    os.makedirs(out_dir, exist_ok=True)
    figs = find_figures(pdf)
    for i, f in enumerate(figs):
        lab = (f["label"] or f"fig_{i}").replace(" ", "").replace(".", "")
        out = os.path.join(out_dir, f"p{f['page']}_{lab}.png")
        render_figure(pdf, [f["page"], *f["bbox"]], out, dpi=dpi)
        flag = "" if f["checks"]["ok"] else "  ⚠ verify"
        print(f"    -> {out}{flag}")
    return figs


def _main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    a = argv[2:]
    flags = {}
    pos = []
    i = 0
    while i < len(a):
        if a[i] == "--dpi":
            flags["dpi"] = int(a[i + 1]); i += 2
        elif a[i] == "--frac":
            flags["frac"] = True; i += 1
        elif a[i] == "--min-px":
            flags["min_px"] = int(a[i + 1]); i += 2
        else:
            pos.append(a[i]); i += 1
    if cmd == "info":
        info(pos[0])
    elif cmd == "map":                            # long-source: structural skeleton (TOC + density)
        if not pos:
            print("usage: extract_pdf.py map <src.pdf>"); return 1
        outline_map(pos[0])
    elif cmd == "headings":                       # long-source: reconstruct a skeleton (no-TOC books)
        if not pos:
            print("usage: extract_pdf.py headings <src.pdf> [start] [end]"); return 1
        try:
            s = int(pos[1]) if len(pos) > 1 else 1
            e = int(pos[2]) if len(pos) > 2 else None
        except ValueError:
            print("usage: extract_pdf.py headings <src.pdf> [start] [end]  (start/end integers)"); return 1
        return headings(pos[0], s, e)
    elif cmd == "text":                           # long-source: dump a page range for chunked reading
        if len(pos) < 3:
            print("usage: extract_pdf.py text <pdf> <start> <end> [out]  "
                  "(start/end are 1-based page numbers)"); return 1
        try:
            s, e = int(pos[1]), int(pos[2])
        except ValueError:
            print("usage: extract_pdf.py text <pdf> <start> <end> [out]  (start/end are integers)"); return 1
        return dump_text(pos[0], s, e, pos[3] if len(pos) > 3 else None)
    elif cmd == "page":
        render_page(pos[0], int(pos[1]), pos[2], dpi=flags.get("dpi", 300))
    elif cmd == "crop":
        coords = list(map(float, pos[3:7]))
        crop_region(pos[0], int(pos[1]), pos[2], *coords,
                    dpi=flags.get("dpi", 300), frac=flags.get("frac", False))
    elif cmd == "images":
        extract_images(pos[0], int(pos[1]), pos[2], min_px=flags.get("min_px", 120))
    elif cmd == "figures":                       # auto-detect figures (optionally one page)
        _print_figures(pos[0], int(pos[1]) if len(pos) > 1 else None)
    elif cmd == "figure":                        # render detected figure #idx -> out.png
        figs = find_figures(pos[0])
        idx = int(pos[1])
        if idx < 0 or idx >= len(figs):
            print(f"index {idx} out of range (found {len(figs)} figures); run `figures` first")
            return 1
        f = figs[idx]
        render_figure(pos[0], [f["page"], *f["bbox"]], pos[2], dpi=flags.get("dpi", 300))
    elif cmd == "autofig":                        # render ALL detected figures to a dir
        _autofig(pos[0], pos[1], dpi=flags.get("dpi", 300))
    else:
        print(__doc__); return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(_main(sys.argv))
    except SystemExit:
        raise
    except RuntimeError as e:                # mupdf content error surfaced mid-processing
        print(f"error: {e} — the document may be corrupt or partially unreadable.")
        sys.exit(1)
