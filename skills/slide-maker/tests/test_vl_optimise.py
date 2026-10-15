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

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
