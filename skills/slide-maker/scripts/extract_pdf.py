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


# byte-for-byte the same formula as lint_deck._text_load / plan_wordcount, so the `source size:`
# trigger and per-page triage use the SAME budget currency as the plan/render lints (a drifted
# counter made Chinese PDFs read ~19% heavier than the equivalent English ones).
_CJK_RANGES = ((0x3040, 0x30FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xAC00, 0xD7AF), (0xF900, 0xFAFF))


def _load(s):
    """Reading load = latin words + CJK chars / 2 (identical to the skill's lint/plan counter —
    CJK punctuation excluded from both streams, ASCII-punctuation splits, round-half-up)."""
    cjk = sum(1 for ch in s if any(a <= ord(ch) <= b for a, b in _CJK_RANGES))
    latin = len([w for w in "".join(ch if (ch.isalnum() and ord(ch) < 0x2E80) else " " for ch in s).split() if w])
    return latin + (cjk + 1) // 2


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
    ext = os.path.splitext(pdf)[1].lower()
    expected = ext in (".epub", ".xps", ".fb2", ".cbz") and not doc.is_pdf   # documented, supported routes
    if doc.is_pdf or expected:
        note = "" if doc.is_pdf else "  (supported; page numbers are fitz pagination, not print pages)"
    else:   # e.g. a .pdf that opened as Text — the renamed-wrong-file case the warning exists for
        note = f"  ⚠ opened as {fmt}, NOT a PDF — confirm this is the file you meant"
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
        print("\n(no embedded TOC/bookmarks — reconstruct a skeleton with `extract_pdf.py headings "
              "<src>` (font-size/bold/caps outliers, no whole-book read); if the book is single-size, "
              "fall back to fixed-size page windows)")
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
    bold_chars = 0
    total_chars = 0
    spans = []
    for p in range(start, end + 1):
        for blk in doc[p - 1].get_text("dict").get("blocks", []):
            for line in blk.get("lines", []):
                txt = "".join(sp["text"] for sp in line.get("spans", [])).strip()
                if not txt or not line.get("spans"):
                    continue
                sz = round(max(sp["size"] for sp in line["spans"]), 1)
                bold = any(sp.get("flags", 0) & 16 for sp in line["spans"])
                sizes[sz] += len(txt)
                total_chars += len(txt)
                if bold:
                    bold_chars += len(txt)
                spans.append((p, sz, txt, bold))
    doc.close()
    if not sizes:
        print("no extractable text (scanned/image-only) — can't reconstruct headings; needs OCR")
        return 1
    body = sizes.most_common(1)[0][0]        # dominant size = body text
    print(f"candidate headings (body ≈ {body}pt; lines ≥ {body * 1.15:.1f}pt, ≤ 90 chars):")
    shown = 0
    for p, sz, txt, _b in spans:
        if sz >= body * 1.15 and len(txt) <= 90:
            print(f"  p{p:<5} {sz:>5}pt  {txt}")
            shown += 1
            if shown >= limit:
                break
    if not shown:
        # second pass — the two most common real no-TOC layouts: bold same-size heads, ALL-CAPS heads
        body_is_bold = bold_chars > 0.5 * total_chars   # a mostly-bold book → bold isn't a signal
        for p, sz, txt, bold in spans:
            if len(txt) > 90:
                continue
            letters = [c for c in txt if c.isalpha()]
            caps = letters and sum(1 for c in letters if c.isupper()) >= 0.8 * len(letters) and len(letters) >= 4
            if (bold and not body_is_bold) or caps:
                print(f"  p{p:<5} {'bold' if bold else 'CAPS':>5}  {txt}")
                shown += 1
                if shown >= limit:
                    break
        if shown:
            print("  (no size outliers — showing bold/ALL-CAPS candidates instead)")
    if not shown:
        print("  (no size/bold/caps outliers — the book may be single-style; fall back to fixed-size "
              "page windows and title each window from its first line)")
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

# Caption labels. Two things the plain `fig(?:ure)?\s*N\b` form got wrong on real papers:
#
# 1. SMALL CAPS MAPPED INTO THE PRIVATE USE AREA. Journals that set "FIG." in small caps often
#    ship a font whose glyphs carry no Unicode mapping, so the text layer reads
#    'F\uf769\uf767. 1. Illustration of...' -- an F followed by two PUA codepoints. `fig` cannot
#    match that, and on one AAPM paper it took out ALL FOURTEEN captions: every figure came back
#    labelled '(figure)', so nothing downstream knew which figure it was or what it showed. The
#    leading real letter survives, so [FTSA] + a run of PUA recovers the label (and its kind);
#    a wholly-PUA label falls back to the kindless form.
#
# 2. IN-TEXT REFERENCES matched as captions. A paragraph opening "Fig. 7 shows an example of..."
#    or "Table 1 compares MoViD against baselines..." was taken as that figure's caption -- worse
#    than a miss, because a body sentence then gets attached and reported as the caption. A real
#    caption puts a DELIMITER after the number ("Fig. 1." / "Fig. 1:" / "Figure 1 |") or, in
#    IEEE style, an all-caps title ("TABLE I QUANTITATIVE COMPARISON..."); an in-text reference
#    continues with a lowercase verb. Hence the lookahead. `(?-i:[A-Z])` is scoped deliberately:
#    under re.I a plain [A-Z] matches lowercase and re-admits every reference.
#
# Measured over 15 real papers (AAPM, IOP, Nature, arXiv/LNCS, IEEE-style): +14 real captions
# recovered, -11 in-text references rejected, 0 real captions lost.
_CAP = re.compile(r'^\s*(?:'
                  r'(?P<word>fig(?:ure)?|tab(?:le)?|scheme|algorithm)\.?\s*'
                  r'|(?P<sc>[FTSA])[\uE000-\uF8FF]{1,8}\.?\s*'
                  r'|[\uE000-\uF8FF]{2,9}\.?\s*'
                  r')(?P<num>\d+|[ivxlc]+|[A-Z])'
                  r'(?=\s*[.:|)\]\-\u2013\u2014]|\s*$|\s+(?-i:[A-Z]))', re.I)

# The small-caps branch recovers only the label's FIRST letter, and the kind has to come from it:
# without this a PUA-mangled figure caption fell through to the table default, the table band-clamp
# then pushed the box past the caption, every box came out empty, and a paper that had detected 14
# figures detected NONE. A label recovered without its kind is worse than no label.
_SC_KIND = {"f": "figure", "t": "table", "s": "scheme", "a": "algorithm"}


def _cap_parse(m):
    """(kind, label) from a _CAP match, whichever branch matched."""
    num = m.group("num")
    w = m.group("word")
    if w:
        wl = w.lower()
        kind = "table" if wl.startswith("tab") else ("figure" if wl.startswith("fig") else wl)
        return kind, f"{w.title().split('.')[0]} {num}"
    sc = m.group("sc")
    if sc:
        kind = _SC_KIND.get(sc.lower(), "figure")
        return kind, f"{kind.title()} {num}"
    return "figure", f"Figure {num}"


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
    # A SECTION HEADING is neither body prose nor a caption, so it passes every filter above and
    # the contiguous run walks straight into it. Measured: a segmentation-results table absorbed
    # the following "3.3 Ablation Study", and the crop showed a results table with a stray heading
    # under it. Two cheap discriminators, either of which ends the run:
    #   · SIZE — table cells are usually set smaller than body text (7.0pt vs a 10.0pt heading in
    #     the measured case), so a row markedly larger than the run's first row is not a cell row;
    #   · NUMBERING — "3.3" / "4.1.2" alone on a line is a section number, never a table cell.
    # The size test alone would fail on a body-size table, and the numbering test alone would fail
    # on an unnumbered heading, so both are applied.
    def _row_size(r):
        best = 0.0
        for b in blocks:
            if fitz.Rect(b["bbox"]) == r:
                for l in b.get("lines", ()):
                    for s in l.get("spans", ()):
                        best = max(best, s.get("size", 0.0))
        return best

    def _looks_heading(r):
        for b in blocks:
            if fitz.Rect(b["bbox"]) == r:
                first = _first_line(b).strip()
                return bool(re.fullmatch(r"\d+(?:\.\d+)*\.?", first))
        return False

    band = [cand[0]]                                  # contiguous run adjacent to the caption
    base_size = _row_size(cand[0]) or 99.0
    for r in cand[1:]:
        prev = band[-1]
        gap = (r.y0 - prev.y1) if side == "below" else (prev.y0 - r.y1)
        if gap > 1.8 * max(prev.height, r.height):
            break
        if _row_size(r) > base_size + 1.5 or _looks_heading(r):
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
                kind, label = _cap_parse(m)
                caps.append({"r": fitz.Rect(b["bbox"]), "kind": kind,
                             "label": label,
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

        def _is_heading(b):
            """A SECTION HEADING is neither body prose, chrome, nor a caption, so it survives every
            other filter and the grow step unions it into the figure. Measured: a segmentation
            results table's crop absorbed the following "3.3 Ablation Study", so the slide showed a
            results table with a stray heading beneath it.

            Keyed on the section NUMBER *and* body-size type. The number alone would also match a
            table cell that happens to read "3.3" (a Dice score); requiring body-size excludes it,
            because cells are set smaller than body text (measured 7.0pt cells vs a 10.0pt
            heading). A size/boldness test alone would match a bolded "Ours" row."""
            first = _first_line(b).strip()
            if not re.match(r"^\d+(?:\.\d+)*\.?(?:\s|$)", first):
                return False
            if len(b.get("lines", [])) > 2:
                return False
            big = max((s.get("size", 0.0) for l in b.get("lines", ())
                       for s in l.get("spans", ())), default=0.0)
            return big >= modal - 0.5

        nonbody = [fitz.Rect(b["bbox"]) for b in blocks
                   if not _is_body(b, modal, R.width) and not _is_chrome(b)
                   and not _is_heading(b)
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
            # Restrict to the clusters in THIS caption's own band before unioning. `rs` is every
            # cluster on the chosen side, so on a page with two stacked figures the lower caption
            # sees both and the union spans from the upper figure to the lower one -- the band
            # clamp then only trims the ends, leaving a box full of the body prose between them.
            # Measured: a journal paper whose captions had been invisible (PUA small caps) started
            # detecting them and its boxes went from cov=1.0/bodyov=0 to bodyov up to 0.98. The
            # band has to be applied BEFORE the union, not after it.
            _others = [o["r"] for o in caps if o is not c and _xshare(o["r"], cr) > 0.3]
            if side == "above":
                _lo = max([o.y1 for o in _others if o.y1 <= cr.y0 - 2] + [hdr])
                _band = (_lo, cr.y0)
            else:
                _hi = min([o.y0 for o in _others if o.y0 >= cr.y1 + 2] + [ftr])
                _band = (cr.y1, _hi)
            _in = [r for r in rs if (r.y0 + r.y1) / 2 >= _band[0] and (r.y0 + r.y1) / 2 <= _band[1]]
            if _in:
                rs = _in
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


def _emit(pi, label, kind, side, box, caption, gfx, body, R, cap_rects=(), self_cap=None,
          body_pt=8.0):
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
    # How big this crop can get on a slide, and therefore whether it stays READABLE. A paper is
    # read at 100% on A4; a slide is read across a room. The band is deckkit's own safe rect, so
    # `mag` is the real magnification available and `slide_pt` is what the source's body type
    # becomes at it. Measured on real papers: a paper table is ~4.8in wide, so width alone allows
    # only ~1.78x -- HEIGHT is what binds, and past ~2.2in (about 12 rows incl. header) the crop
    # falls under ~14pt and cannot be read projected. That is the crop-whole vs subset decision,
    # and it is arithmetic rather than taste -- so it is printed instead of left to judgement.
    BAND_W, BAND_H = 8.56, 3.80
    w_in, h_in = box.width / 72.0, box.height / 72.0
    mag = min(BAND_W / w_in, BAND_H / h_in) if w_in > 0 and h_in > 0 else 0.0
    slide_pt = body_pt * mag
    checks = {
        "graphics_coverage": round(min(gcov, 1.0), 2),
        "body_text_overlap": round(bover, 2),
        "aspect": round(ar, 2),
        "foreign_caption": bool(foreign),
        "in_page": bool((box & R).get_area() >= 0.999 * box.get_area()),
    }
    checks["ok"] = (checks["graphics_coverage"] >= 0.40 and checks["body_text_overlap"] <= 0.20
                    and 0.08 <= ar <= 14 and checks["in_page"] and not foreign)
    # A table's caption IS its meaning -- which metric, what bold denotes, which datasets. The
    # body bbox deliberately excludes it (see _table_text_bbox), which is right for MEASURING the
    # table and wrong for a slide: a cropped results table with no caption is an untitled table.
    # So the caption-inclusive box travels alongside and the renderer can opt into it.
    boxc = fitz.Rect(box)
    if self_cap is not None:
        boxc |= self_cap
        boxc &= R
    return {"page": pi + 1, "label": label, "kind": kind, "side": side,
            "bbox": [round(box.x0, 1), round(box.y0, 1), round(box.x1, 1), round(box.y1, 1)],
            "bbox_caption": [round(boxc.x0, 1), round(boxc.y0, 1),
                             round(boxc.x1, 1), round(boxc.y1, 1)],
            "caption": caption, "checks": checks,
            "fit": {"mag": round(mag, 2), "slide_pt": round(slide_pt, 1),
                    "legible_cropped": bool(slide_pt >= 14.0)}}


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


def render_figure(pdf, bbox, out, dpi=300, pad=3, do_trim=True, keep_rect=None):
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
        # the figure's OWN caption is content here, not bleed -- only FOREIGN captions get shrunk
        # away. Without this, asking for a caption-inclusive crop silently gets the caption cut
        # back off again by the bleed guard.
        if keep_rect is not None and rb.intersects(keep_rect) \
                and (rb & keep_rect).get_area() > 0.5 * rb.get_area():
            continue
        infl = fitz.Rect(box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
        if not infl.intersects(rb):
            continue
        midy = (box.y0 + box.y1) / 2
        if rb.y1 <= midy and rb.y1 + 1 > box.y0 - pad:        # above-ish → push top down
            box.y0 = max(box.y0, rb.y1 + 2); bled = True
        elif rb.y0 >= midy and rb.y0 - 1 < box.y1 + pad:      # below-ish → pull bottom up
            box.y1 = min(box.y1, rb.y0 - 2); bled = True
    # --- pad CEILING: never grow the clip into FOREIGN text -------------------------------
    # The CLIP guard below grows the pad whenever it sees content flush at an edge, and prose that
    # merely sits next to the figure is content. Measured: a table crop grew downward and pulled in
    # the next section heading ("3.3 Ablation Study"), so the slide showed a results table with a
    # stray heading under it. Cap each side at the nearest text block that is strictly OUTSIDE the
    # box and is not the caption we were asked to keep, so growth stops 2pt short of it.
    ceil = {"top": pad + 30, "bottom": pad + 30, "left": pad + 30, "right": pad + 30}
    for b in _text_blocks(page):
        rb = fitz.Rect(b["bbox"])
        if keep_rect is not None and rb.intersects(keep_rect) \
                and (rb & keep_rect).get_area() > 0.5 * rb.get_area():
            continue                                        # our own caption is not foreign
        if rb.intersects(box):
            continue                                        # part of the figure's own content
        if rb.y0 >= box.y1 and _xshare(rb, box) > 0.15:
            ceil["bottom"] = min(ceil["bottom"], max(0.0, rb.y0 - box.y1 - 2))
        if rb.y1 <= box.y0 and _xshare(rb, box) > 0.15:
            ceil["top"] = min(ceil["top"], max(0.0, box.y0 - rb.y1 - 2))

    # --- CLIP guard: render, read edges, grow pad on under-covered sides, retry ---
    pads = {"top": min(pad, ceil["top"]), "bottom": min(pad, ceil["bottom"]),
            "left": pad, "right": pad}
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
            if not at[e] and pads[e] < ceil[e]:                # cap at foreign text, then total
                pads[e] = min(pads[e] + 10, ceil[e]); grew = True
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


def print_tables(pdf, page_no=None):
    """Structured table extraction via PyMuPDF's find_tables(), reported against the number of
    `Table N` CAPTIONS in the document -- because the recall is not good enough to trust silently.

    Measured on real papers: 5/6 tables on one, 0/5 on another whose tables are booktabs (rules
    only, no cell grid). A tool that returns 0 and prints nothing else reads as "this paper has no
    tables", which is the failure this gap report exists to prevent. So the caption count is the
    denominator and the shortfall is stated in the output, not left for the caller to notice.

    Use the rows for the 2-6 numbers a slide actually ASSERTS -- each is then verifiable verbatim
    against the text layer. Do not retype a whole table from this: the structure is only as good
    as the detector, and a value that lands in the wrong row is invisible once it is on a slide.
    """
    doc = _open(pdf)
    pages = [page_no - 1] if page_no else range(doc.page_count)
    caps, found, collapsed_tables = 0, 0, 0
    for pi in pages:
        page = doc[pi]
        for b in _text_blocks(page):
            m = re.match(r"\s*(TABLE|Table)\s+([IVX\d]+)", _first_line(b).strip())
            if m:
                caps += 1
        try:
            tabs = page.find_tables().tables
        except Exception as e:
            print(f"  p{pi + 1}: find_tables unavailable ({e})")
            continue
        for k, tb in enumerate(tabs):
            found += 1
            data = tb.extract()
            bb = [round(v, 1) for v in tb.bbox]
            # COLLAPSED grid: a cell holding several numeric tokens means the row/column split
            # failed and the whole column landed in one string. Measured on a real paper:
            # find_tables reported "1 rows x 3 cols" for a table with 15 visible rows, cells like
            # '88.26 83.56 92.25 88'. Fed to deckkit.table() that is not a table, it is a lie with
            # a grid drawn round it -- and every value is in the wrong place. Worth more than a
            # row count, so it is flagged per table.
            collapsed = sum(1 for row in data for c in row
                            if len(re.findall(r"\d+\.\d+|\d+", c or "")) >= 3)
            flag = ("   [COLLAPSED: {} cell(s) hold 3+ numbers -- the row/column split FAILED; "
                    "do NOT use these as rows]".format(collapsed)) if collapsed else ""
            print(f"[p{pi + 1} t{k}] {tb.row_count} rows x {tb.col_count} cols  bbox={bb}{flag}")
            for row in data[: min(4, len(data))]:
                print("      " + str([(c or "").strip()[:20] for c in row]))
            if len(data) > 4:
                print(f"      ... {len(data) - 4} more row(s)")
            if collapsed:
                collapsed_tables += 1
    doc.close()
    usable = found - collapsed_tables
    print(f"\n{found} table(s) extracted structurally ({usable} with an intact grid, "
          f"{collapsed_tables} collapsed) · {caps} `Table N` caption(s) present")
    if caps > found:
        print(f"⚠ SHORTFALL {caps - found}: that many captioned tables were NOT recovered as data "
              f"(booktabs/rule-only tables defeat find_tables). For those, crop the region as "
              f"evidence and retype only the numbers you assert — do NOT report this paper as "
              f"having fewer tables than it has.")
    elif found > caps:
        print(f"note: {found - caps} more structures than captions — find_tables also picks up "
              f"figure legends and layout grids; check each before using it as a table.")
    return found, caps


def _print_figures(pdf, page_no=None):
    figs = find_figures(pdf, page_no)
    if not figs:
        print("no figures detected (try `page`/`crop`, or the page may be text-only/scanned)")
    for i, f in enumerate(figs):
        warn = "" if f["checks"]["ok"] else "  ⚠ CHECK (verify by viewing)"
        fit = f.get("fit") or {}
        tag = ""
        if fit:
            tag = f" fit={fit['mag']}x->{fit['slide_pt']}pt"
            if not fit["legible_cropped"]:
                if (f["kind"] or "").startswith("tab"):
                    tag += ("  [too small cropped WHOLE -> keep the crop as the evidence and "
                            "retype ONLY the numbers you assert, or subset rows/cols natively]")
                else:
                    tag += ("  [the figure's own labels land near {:.0f}pt -> view the render; "
                            "if unreadable, lift the ONE sub-panel that carries the point]"
                            .format(fit["slide_pt"]))
        print(f"[{i}] p{f['page']} {f['label'] or '(figure)'} {f['bbox']} "
              f"cov={f['checks']['graphics_coverage']} bodyov={f['checks']['body_text_overlap']} "
              f"ar={f['checks']['aspect']}{tag}{warn}")
        if f["caption"]:
            print(f"      {f['caption']!r}")
    return figs


def _crop_args(f, with_caption=None):
    """Which bbox to render, and whether to protect the figure's own caption from the bleed guard.

    A TABLE defaults to caption-INCLUDED: the caption is what says which metric, what bold means,
    which datasets -- a cropped results table without it is an untitled table. A FIGURE defaults
    to caption-excluded, which is the long-standing behaviour (its axis labels already sit inside
    the box, and the prose caption belongs in the slide's own assertion line).
    """
    if with_caption is None:
        with_caption = (f["kind"] or "").startswith("tab")
    if with_caption and f.get("bbox_caption"):
        bb = f["bbox_caption"]
        keep = fitz.Rect(*bb)
    else:
        bb, keep = f["bbox"], None
    return bb, keep


def _autofig(pdf, out_dir, dpi=300, with_caption=None):
    os.makedirs(out_dir, exist_ok=True)
    figs = find_figures(pdf)
    for i, f in enumerate(figs):
        lab = (f["label"] or f"fig_{i}").replace(" ", "").replace(".", "")
        out = os.path.join(out_dir, f"p{f['page']}_{lab}.png")
        bb, keep = _crop_args(f, with_caption)
        render_figure(pdf, [f["page"], *bb], out, dpi=dpi, keep_rect=keep)
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
        elif a[i] == "--with-caption":
            flags["with_caption"] = True; i += 1
        elif a[i] == "--no-caption":
            flags["no_caption"] = True; i += 1
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
    elif cmd == "tables":                        # structured table data + an explicit gap report
        print_tables(pos[0], int(pos[1]) if len(pos) > 1 else None)
    elif cmd == "figures":                       # auto-detect figures (optionally one page)
        _print_figures(pos[0], int(pos[1]) if len(pos) > 1 else None)
    elif cmd == "figure":                        # render detected figure #idx -> out.png
        figs = find_figures(pos[0])
        idx = int(pos[1])
        if idx < 0 or idx >= len(figs):
            print(f"index {idx} out of range (found {len(figs)} figures); run `figures` first")
            return 1
        f = figs[idx]
        wc = True if flags.get("with_caption") else (False if flags.get("no_caption") else None)
        bb, keep = _crop_args(f, wc)
        render_figure(pos[0], [f["page"], *bb], pos[2], dpi=flags.get("dpi", 300),
                      keep_rect=keep)
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
