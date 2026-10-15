"""Phase 3 — the languages' own pages, measured (spec §6): quote scale, title fit, rules at their content, designed dark
grounds, the smallest tier, distinctiveness, and the per-language fixes. Prints `N passed, 0 failed`."""
import contextlib, io, os, re, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk, visual_languages as vl, lint_deck

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)
WORK = Path(tempfile.mkdtemp(prefix="vlopt_")); os.chdir(WORK)


def _deck(L, g=None):
    prs = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(L, prs, ground=g) if g else vl.use(L, prs)
    return prs, k


def _hard(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p)); buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        lint_deck.lint(str(p), static_ok=True)
    return [l.strip()[:150] for l in buf.getvalue().splitlines()
            if re.match(r"\s+slide \d+: [A-Z]", l) and "[warn]" not in l and "[stats]" not in l]


def _size_of(slide, words):
    """The largest run size of the text shape holding `words` (the quote's own runs)."""
    best = 0.0
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and words.lower() in sh.text_frame.text.replace("\n", " ").lower():
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.text.strip():
                        best = max(best, r.font.size.pt)
    return best


# ── Task 1 (F1): a quote page scales with the quote; the attribution is a readable line, not a caption ──
SHORT, LONG = "Fix it together.", " ".join(["Every repair we made that evening was a small argument for keeping"
                                            " things, and the room kept making it until the last lamp came on."] * 3)
for L in vl.LANGS:
    base = vl.TYPE[L]["quote"][0]
    prs, k = _deck(L)
    s1 = k.new_slide()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            k.quote(s1, quote=SHORT, attribution="Repair café volunteer")
    except Exception as e:
        check(False, "{}: a short quote builds ({}: {})".format(L, type(e).__name__, str(e)[:80])); continue
    z = _size_of(s1, "Fix it")                  # poster stacks a quote one line per shape
    # ink sets a CJK couplet vertically; poster stacks its quote as display type already sized to the page (27% of it)
    check(z >= 1.3 * base - 1e-6 or L in ("ink", "poster"), "{}: a 3-word quote is set larger than the language's quote size "
          "({:.1f}pt vs {}pt)".format(L, z, base))
    za = _size_of(s1, "repair caf")             # some languages set it in caps
    check(za >= 16 - 1e-6, "{}: the attribution is >= 16pt ({:.1f}pt)".format(L, za))
    s2 = k.new_slide()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            k.quote(s2, quote=LONG, attribution="Repair café volunteer")
        refused = None
    except vl.VLTextOverflow as e:
        refused = str(e)
    judged = ("slide 1:",) if refused else ("slide 1:", "slide 2:")     # a refused quote leaves its page empty, loudly
    found = [f for f in _hard(prs, "q_" + L) if f.startswith(judged)]
    check(not found, "{}: the quote pages are lint-clean ({})".format(L, found[:1]))
dk.set_theme(None)

# ── Task 2 (F2): a cover title wraps before it shrinks — a phrase per line only while that costs <= 15% of the size ──
TITLES = [("short", "Fix it together", 0.85), ("comma", "Bring it broken, take it home working", 0.85),
          ("cjk", "带着坏东西来，带着好东西走", 0.85)]
for L in vl.LANGS:
    base = vl.TYPE[L]["title"][0]
    for tag, t, need in TITLES:
        prs, k = _deck(L)
        sl = k.new_slide()
        try:
            pic = str(vl.ASSETS / "photo/hall-repair.jpg") if L in vl.IMAGE_LED else None   # the narrow column
            with contextlib.redirect_stdout(io.StringIO()):
                k.cover(sl, title=t, kicker="Repair café", **({"image": pic} if pic else {}))
        except Exception as e:
            check(False, "{} cover ({}) builds ({}: {})".format(L, tag, type(e).__name__, str(e)[:70])); continue
        words = t.split()[0] if tag != "cjk" else t[:2]
        z = _size_of(sl, words)
        # poster's title size is the CEILING of a display stack sized to the page, not a target
        # ink sets a CJK title vertically in the approved two-column scroll (bounded by the column's height)
        check(z >= need * base - 1e-6 or L == "poster" or (L == "ink" and tag == "cjk"), "{} cover title ({}) holds >= {:.0%} of {}pt ({:.1f}pt)".format(L, tag, need, base, z))
dk.set_theme(None)

# ── shared helpers for the Task 5 (A) checks (image-led languages) ──
def _deck_at(L, g, W, H):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(L, prs, ground=g)
    return prs, k


def _text_shapes(slide):
    return [sh for sh in slide.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]


def _run_of(sh):
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            if r.font.size and r.text.strip():
                return r
    return None


# ── Task 5 (A): editorial: a points item number never wraps ──
# "01" in Arial Black 30.5pt measured 0.5651in in a box whose inner width was 0.5644in, so LibreOffice set "0" over "1".
# The number's box is now its measured width + >= 10% (measured by both widths the kit uses), at 2, 3 and 4 points.
import display_type as _dt
_PTS = [("Your broken thing", "Any size that fits through the door."), ("An hour", "Most repairs take less."),
        ("Curiosity", "Volunteers explain every step."), ("A cup of tea", "There is always a kettle on.")]
for L in ("editorial", "soft", "collage"):
    for g in vl.VARIANTS[L]:
        for n in (2, 3, 4):
            for (W, H, pic) in ((13.333, 7.5, str(vl.ASSETS / "photo/tools-tray.jpg")), (13.333, 7.5, None),
                                (7.5, 10.0, str(vl.ASSETS / "photo/tools-tray.jpg"))):
                prs, k = _deck_at(L, g, W, H)
                sl = k.new_slide()
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        k.points(sl, kicker="A repair café", title="Things to bring", items=_PTS[:n], image=pic)
                except Exception as e:
                    check(False, "{}/{}: points x{} builds ({}: {})".format(L, g, n, type(e).__name__, str(e)[:70])); continue
                nums = [sh for sh in _text_shapes(sl) if re.fullmatch(r"\d\d", sh.text_frame.text.strip())]
                worst = 9.0
                for sh in nums:
                    r = _run_of(sh)
                    face, bold = r.font.name, bool(r.font.bold)
                    need = max(dk._natural_width_in([(r.text, bold)], r.font.size.pt, face),
                               _dt._glyph_width(r.text, r.font.size.pt, face, bold) or 0.0)
                    worst = min(worst, (sh.width / 914400.0 - dk.TEXT_INSET_LR) / need)
                check(len(nums) == n and worst >= 1.10 - 1e-6,
                      "{}/{} {} points x{}{}: every item number's box holds its digits with >= 10% to spare "
                      "(tightest {:.3f}x, {} numbers)".format(L, g, "landscape" if W > H else "portrait", n,
                                                              "" if pic else " (no picture)", worst, len(nums)))
dk.set_theme(None)


# ── Task 5 (A): editorial: the full-bleed cover is cropped for the part of it that is VISIBLE, biased to the top ──
# The picture was cover-fitted to the whole 13.33in page while the panel covers x >= 7.2in: a 853x1280 portrait kept
# 37.4% of its height in a 7.2in-wide window, and the crop (centred) cut the heads at the top edge.
from PIL import Image as _PIL


def _visible_source(slide):
    """(x0, y0, x1, y1) as fractions of the SOURCE picture that the viewer sees on `slide`'s first picture — the
    picture's frame and crop, minus the opaque panel box that follows it — and the pixel aspect of that window."""
    W, H = slide.part.package.presentation_part.presentation.slide_width / 914400.0, \
        slide.part.package.presentation_part.presentation.slide_height / 914400.0
    shapes = list(slide.shapes)
    pi = next(i for i, sh in enumerate(shapes) if sh.shape_type == 13)
    pic = shapes[pi]
    panel = next(sh for sh in shapes[pi + 1:] if sh.shape_type == 1)
    px, py, pw, ph = (v / 914400.0 for v in (panel.left, panel.top, panel.width, panel.height))
    if pw < 0.9 * W:                                    # a side band
        vis = (px + pw, 0.0, W, H) if px < 0.01 else (0.0, 0.0, px, H)
    else:                                               # a top or bottom band
        vis = (0.0, py + ph, W, H) if py < 0.01 else (0.0, 0.0, W, py)
    fx, fy, fw, fh = (v / 914400.0 for v in (pic.left, pic.top, pic.width, pic.height))
    cl, cr, ct, cb = pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom
    x0, x1 = max(vis[0], fx), min(vis[2], fx + fw)
    y0, y1 = max(vis[1], fy), min(vis[3], fy + fh)
    sx = lambda x: cl + (1 - cl - cr) * (x - fx) / fw
    sy = lambda y: ct + (1 - ct - cb) * (y - fy) / fh
    return (sx(x0), sy(y0), sx(x1), sy(y1)), vis


for pg in ("cover", "closing"):
    for tag, src in (("portrait", "photo/hall-repair.jpg"), ("landscape", "photo/tools-tray.jpg"),
                     ("square", "photo/bench-toaster.jpg")):
        path = str(vl.ASSETS / src)
        iw, ih = _PIL.open(path).size
        for g in vl.VARIANTS["editorial"]:
            prs, k = _deck_at("editorial", g, 13.333, 7.5)
            sl = k.new_slide()
            with contextlib.redirect_stdout(io.StringIO()):
                if pg == "cover":
                    k.cover(sl, title="Bring it broken, take it home working", kicker="Repair café", image=path)
                else:
                    k.closing(sl, title="Questions", line="Thank you.", image=path)
            (sx0, sy0, sx1, sy1), vis = _visible_source(sl)
            win_ar = ((sx1 - sx0) * iw) / ((sy1 - sy0) * ih)
            vis_ar = (vis[2] - vis[0]) / (vis[3] - vis[1])
            # the share of the picture's height a window of the visible rect's shape can show: all of it for a
            # picture wider than the window, vis_ar-limited (ih/iw * ...) for a taller one
            max_h = 1.0 if iw / ih >= vis_ar else (iw / ih) / vis_ar
            check(abs(win_ar - vis_ar) / vis_ar < 0.02,
                  "editorial {} ({} source, {}): the visible window shows the picture undistorted ({:.3f} vs {:.3f})".format(pg, tag, g, win_ar, vis_ar))
            check((sy1 - sy0) >= 0.95 * max_h,
                  "editorial {} ({} source, {}): the crop is made for the visible rect — it keeps {:.1%} of the picture's height "
                  "(the most that rect can show is {:.1%})".format(pg, tag, g, sy1 - sy0, max_h))
            if max_h < 0.999:                           # a taller picture is cropped top/bottom: the top is the side kept
                check(sy0 <= 0.12 and sy0 < (1 - sy1), "editorial {} ({} source, {}): the crop is biased to the top (top edge "
                      "{:.1%} cut, bottom {:.1%})".format(pg, tag, g, sy0, 1 - sy1))
dk.set_theme(None)

# ── Task 5 (A): soft: a quote card is sized to its content and the mark sits next to the quote ──
# The mark's 90pt line box (1.56in) is mostly blank under a glyph 0.38in tall, and the quote started under all of it:
# 1.16in of blank card between the mark and the first line, the top 58% of the card holding only the mark. Measured
# on the RENDER (the glyph's ink is not in the file): the longest run of blank rows inside the card, between its ink.
import subprocess
import render_deck as _rd


def _render_slides(prs, tag, dpi=60):
    """The slides of `prs` as PIL images, rendered by LibreOffice; None when it is not installed (the caller fails
    loudly — a render check that did not run must not read as one that passed)."""
    soffice = _rd.find_soffice()
    if not soffice:
        return None
    import fitz
    from PIL import Image
    d = WORK / ("r_" + tag); d.mkdir(exist_ok=True)
    f = d / (tag + ".pptx"); prs.save(str(f))
    for _try in range(3):                       # LibreOffice sometimes exits without a PDF when another instance is closing
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(d), str(f)], capture_output=True,
                       timeout=180)
        if (d / (tag + ".pdf")).exists():
            break
    if not (d / (tag + ".pdf")).exists():
        return None
    out = []
    for pg in fitz.open(str(d / (tag + ".pdf"))):
        pix = pg.get_pixmap(dpi=dpi)
        out.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return out


def _blank_runs(im, rect_in, dpi, bg, tol=60):
    """(first ink row, last ink row, longest blank run between them) in inches, for the ink inside `rect_in` — pixels
    further than `tol` (summed channel difference) from the colour `bg`."""
    x, y, w, h = (int(round(v * dpi)) for v in rect_in)
    rows = []
    for yy in range(y, y + h):
        rows.append(any(sum(abs(a - b) for a, b in zip(im.getpixel((xx, yy)), bg)) > tol for xx in range(x, x + w, 2)))
    inked = [i for i, v in enumerate(rows) if v]
    if not inked:
        return None
    gap = best = 0
    for v in rows[inked[0]:inked[-1] + 1]:
        gap = 0 if v else gap + 1
        best = max(best, gap)
    return (y + inked[0]) / dpi, (y + inked[-1] + 1) / dpi, best / dpi


for g in vl.VARIANTS["soft"]:
    prs, k = _deck_at("soft", g, 13.333, 7.5)
    sl = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()):
        k.quote(sl, quote="The visitor holds the screwdriver; the volunteer only guides.", attribution="How every repair begins",
                image=str(vl.ASSETS / "photo/hall-repair.jpg"))
    card = max((sh for sh in sl.shapes if sh.shape_type == 1), key=lambda sh: sh.width * sh.height)
    cx, cy, cw, ch = (v / 914400.0 for v in (card.left, card.top, card.width, card.height))
    ims = _render_slides(prs, "softq_" + g)
    if ims is None:
        check(False, "soft/{} quote card: LibreOffice not found — the render half of this check did not run".format(g)); continue
    bg = ims[0].getpixel((int((cx + 0.12) * 60), int((cy + 0.05) * 60)))      # the card's own colour, near its top-left corner
    first, last, blank = _blank_runs(ims[0], (cx + 0.2, cy + 0.12, cw - 0.4, ch - 0.24), 60, bg)
    check(blank <= 0.35, "soft/{} quote card: no blank band inside the card is taller than 0.35in — the mark sits next to the "
          "quote (longest blank run {:.2f}in)".format(g, blank))
    check(ch <= (last - first) + 1.0, "soft/{} quote card stays sized to its content: {:.2f}in of card for {:.2f}in of "
          "ink (<= 1.0in of padding in all)".format(g, ch, last - first))
dk.set_theme(None)

# ── Task 5 (A): soft: the figure's disc keeps its true colour and the digit takes the ground's ink (dusk) ──
# On dusk the sage disc was blended toward the ground (9DB8A0 -> 7C8D83) so the off-white digit read at 3.05:1 on it
# (the disc itself 3.98:1 on the ground). The disc stays the language's sage and the digit is set in the ground's
# dark ink — 6.5:1 — on the data page and on the section pill alike.
from pptx.enum.shapes import MSO_SHAPE as _MS


def _hexc(c):
    return str(c).upper()


for g in vl.VARIANTS["soft"]:
    acc_sage = vl.VARIANTS["soft"][g]["palette"]["accents"][1]
    for page, kw in (("data", dict(number="1", label="evening a month", note="Short enough to fit around work.")),
                     ("data", dict(number="87%", label="of repairs end well")),
                     ("section", dict(number="02", kicker="Repair café", title="Everything you need is on the table"))):
        for pic in (str(vl.ASSETS / "photo/jacket-mend.jpg"), None):
            for (W, H) in ((13.333, 7.5), (7.5, 10.0)):
                prs, k = _deck_at("soft", g, W, H)
                sl = k.new_slide()
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        getattr(k, page)(sl, image=pic, **kw)
                except Exception as e:
                    check(False, "soft/{} {} builds ({}: {})".format(g, page, type(e).__name__, str(e)[:70])); continue
                num = next((sh for sh in _text_shapes(sl) if sh.text_frame.text.strip() == kw["number"]), None)
                if num is None:
                    check(False, "soft/{} {}: the figure {!r} is on the page".format(g, page, kw["number"])); continue
                # the disc is drawn on the figure's own line: it spans the figure's box from top to bottom (to 0.3in) and meets it across
                held = [sh for sh in sl.shapes if sh.shape_type == 1 and sh.auto_shape_type in (_MS.OVAL, _MS.ROUNDED_RECTANGLE)
                        and sh.top <= num.top + 0.3 * 914400 and sh.top + sh.height >= num.top + num.height - 0.3 * 914400
                        and sh.left < num.left + num.width and sh.left + sh.width > num.left]
                if not held:
                    check(False, "soft/{} {} '{}': a disc holds the figure".format(g, page, kw["number"])); continue
                disc = min(held, key=lambda sh: sh.width * sh.height)
                fill = _hexc(disc.fill.fore_color.rgb)
                ink = _hexc(_run_of(num).font.color.rgb)
                cr = vl._contrast(fill, ink)
                ground = vl.VARIANTS["soft"][g]["palette"]["ground"]
                check(fill == acc_sage and cr >= 4.5 and (g != "dusk" or ink == _hexc(ground)),
                      "soft/{} {} '{}' {}{}: the disc is the true sage {} (is {}) and its figure reads {:.2f}:1 ({} on it)".format(
                          g, page, kw["number"], "landscape" if W > H else "portrait", "" if pic else " (no picture)", acc_sage, fill, cr, ink))
                if g == "dusk":
                    # the lint reads dark ink against what is behind its text box: the disc must hold the box (it read the
                    # ground — '1' ink #2E2940 on fill #2E2940, INVISIBLE TEXT — until the box was the disc's)
                    mine = [f for f in _hard(prs, "sd_{}_{}_{}".format(page, int(W), int(bool(pic)))) if "'{}'".format(kw["number"]) in f]
                    check(not mine, "soft/dusk {} '{}' {}{}: the figure on its disc raises no lint finding ({})".format(
                        page, kw["number"], "landscape" if W > H else "portrait", "" if pic else " (no picture)", mine[:1]))
dk.set_theme(None)

# ── Task 5 (A): collage: on slate the prints and notes are cream paper with dark ink; kraft stays exactly as it is ──
# Every print on slate kept its FFFFFF border (14.4:1 on the ground — the brightest thing on a dark page) and the quote
# note was the ground's own dark panel 3B3934 (1.24:1 on the ground, a dark slab with tape the only paper cue). Both are
# cream now (E8DFC9), the note's words in the light ground's dark inks; kraft's white borders, white notes and ink are as before.
def _lumh(c):
    return vl._lum(c)


def _frames(slide):
    """(frame fill, picture) for each print on `slide`: the filled box drawn right under the picture."""
    sh = list(slide.shapes)
    return [(_hexc(sh[i - 1].fill.fore_color.rgb), s_) for i, s_ in enumerate(sh)
            if s_.shape_type == 13 and i and sh[i - 1].shape_type == 1 and sh[i - 1].fill.type == 1]


def _notes_text(slide):
    """[(card fill, run colour, text)] for every run of text that sits on a filled card (the smallest one holding the
    text box's centre), excluding the page's own ground."""
    out = []
    cards = [sh for sh in slide.shapes if sh.shape_type == 1 and sh.fill.type == 1
             and sh.width * sh.height < 0.5 * 13.333 * 7.5 * 914400 ** 2 and sh.height > 0.5 * 914400]
    for t in _text_shapes(slide):
        cx, cy = t.left + t.width / 2, t.top + t.height / 2
        held = [c for c in cards if c.left - 0.2 * 914400 <= cx <= c.left + c.width + 0.2 * 914400
                and c.top - 0.2 * 914400 <= cy <= c.top + c.height + 0.2 * 914400]
        if not held:
            continue
        card = min(held, key=lambda c: c.width * c.height)
        for p in t.text_frame.paragraphs:
            for r in p.runs:
                if r.text.strip() and r.font.color and r.font.color.type is not None:
                    out.append((_hexc(card.fill.fore_color.rgb), _hexc(r.font.color.rgb), r.text.strip()))
    return out


_CPTS = [("Your broken thing", "Any size that fits through the door."), ("An hour", "Most repairs take less."),
         ("Curiosity", "Volunteers explain every step.")]
for g in vl.VARIANTS["collage"]:
    ground = vl.VARIANTS["collage"][g]["palette"]["ground"]
    prs, k = _deck_at("collage", g, 13.333, 7.5)
    pic = str(vl.ASSETS / "photo/hall-repair.jpg")
    slides = {}
    with contextlib.redirect_stdout(io.StringIO()):
        slides["quote"] = k.new_slide(); k.quote(slides["quote"], quote="The visitor holds the screwdriver; the volunteer only guides.",
                                                 attribution="How every repair begins", image=pic)
        slides["points"] = k.new_slide(); k.points(slides["points"], kicker="A repair café", title="Three things to bring", items=_CPTS,
                                                   image=str(vl.ASSETS / "photo/tools-tray.jpg"))
        slides["data"] = k.new_slide(); k.data(slides["data"], number="1", label="evening a month", note="Short enough.",
                                               image=str(vl.ASSETS / "photo/jacket-mend.jpg"))
        slides["cover"] = k.new_slide(); k.cover(slides["cover"], kicker="Repair café", title="Bring it broken",
                                                 image=[str(vl.ASSETS / x) for x in vl.SAMPLE_IMAGES["photo"][:3]])
    fr = [f for sl in slides.values() for f in _frames(sl)]
    if g == "light":
        check(fr and all(f == "FFFFFF" for f, _p in fr), "collage/kraft: every print keeps its white border exactly ({} prints)".format(len(fr)))
        nt = _notes_text(slides["quote"]) + _notes_text(slides["points"])
        check(nt and all(c == "FFFFFF" and i != "FFFFFF" and vl._contrast(c, i) >= 4.5 for c, i, _t in nt),
              "collage/kraft: notes stay white with the language's own ink ({} runs)".format(len(nt)))
        tapes = [_hexc(sh.fill.fore_color.rgb) for sl in slides.values() for sh in sl.shapes
                 if sh.shape_type == 5 and sh.fill.type == 1]
        check(tapes and set(tapes) == {"EDE3C8"}, "collage/kraft: the tape stays washi EDE3C8 ({} strips: {})".format(len(tapes), sorted(set(tapes))))
    else:
        check(fr and all(0.55 <= _lumh(f) <= 0.80 and vl._contrast(f, ground) >= 4.5 for f, _p in fr),
              "collage/slate: every print has a cream border, not white: {} prints, luminance {} (white is 1.0), {:.1f}:1 on the ground".format(
                  len(fr), sorted({round(_lumh(f), 2) for f, _p in fr}), min([vl._contrast(f, ground) for f, _p in fr] or [0])))
        for pg in ("quote", "points"):
            nt = _notes_text(slides[pg])
            worst = min([vl._contrast(c, i) for c, i, _t in nt] or [0])
            check(nt and all(_lumh(c) >= 0.55 and _lumh(i) <= 0.2 and vl._contrast(c, i) >= 4.5 for c, i, _t in nt),
                  "collage/slate {}: every note is cream paper with dark ink on it — {} runs, card luminance {}, ink luminance <= {:.2f}, "
                  "worst {:.1f}:1".format(pg, len(nt), sorted({round(_lumh(c), 2) for c, _i, _t in nt}),
                                          max([_lumh(i) for _c, i, _t in nt] or [0]), worst))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
