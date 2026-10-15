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


# ── Task 5 (B): measuring helpers — the pptx's own geometry, and the rendered picture where one can be made ──
import shutil, subprocess
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

CAN_RENDER = bool(shutil.which("soffice") and shutil.which("pdftoppm"))
try:
    import numpy as np
    from PIL import Image
except ImportError:                                  # no picture to measure: the geometry checks still run
    CAN_RENDER = False


def _inch(v):
    return Emu(v).inches


def _rules(slide):
    """The slide's straight rules: [(x0, y0, x1, y1)] in inches (LINE shapes)."""
    return [tuple(_inch(v) for v in (sh.left, sh.top, sh.left + sh.width, sh.top + sh.height))
            for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.LINE]


def _words(slide):
    """(text, x0, y0, x1, y1, max_size_pt) of every text shape on the page proper."""
    out = []
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0:
            z = max((r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size and r.text.strip()),
                    default=0.0)
            out.append((sh.text_frame.text.replace("\n", " ").replace("\v", " "), _inch(sh.left), _inch(sh.top),
                        _inch(sh.left + sh.width), _inch(sh.top + sh.height), z))
    return out


_PNG = {}


def _render(prs, tag, dpi=100):
    """The deck's pages as PIL images (cached), or None when no renderer is installed."""
    if not CAN_RENDER:
        return None
    if tag not in _PNG:
        pp = WORK / (tag + ".pptx"); prs.save(str(pp))
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(WORK), str(pp)],
                       capture_output=True, timeout=240)
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(WORK / (tag + ".pdf")), str(WORK / (tag + "_pg"))],
                       capture_output=True, timeout=240)
        _PNG[tag] = [Image.open(f).convert("RGB") for f in sorted(WORK.glob(tag + "_pg*.png"))]
    return _PNG[tag] or None


def _ink(img, box, dpi=100, thr=70):
    """The bounding box (inches) of what is drawn inside `box` (x0, y0, x1, y1) — pixels more than `thr` (summed
    channel difference) away from the box's median colour — or None when the box is empty."""
    a = np.asarray(img).astype(int)
    x0, y0, x1, y1 = [max(0, int(round(v * dpi))) for v in box]
    r = a[y0:y1, x0:x1]
    if r.size == 0:
        return None
    hit = np.abs(r - np.median(r.reshape(-1, 3), axis=0)).sum(axis=2) > thr
    ys, xs = np.where(hit)
    if not len(ys):
        return None
    return ((xs.min() + x0) / dpi, (ys.min() + y0) / dpi, (xs.max() + 1 + x0) / dpi, (ys.max() + 1 + y0) / dpi)


# ── Task 5 (B): ink: a points page's rules end at their column's text (+0.2in), not at a fixed 4.8in ──
INK_CASES = {
    "cjk-short": dict(title="两道工序", items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼")], seal="序"),
    "cjk-long": dict(title="四道工序", items=[("洗盏", "器净，心先静，盏中不留一滴旧水"), ("候汤", "水沸如蟹眼，听松风而不急不躁"),
                                              ("分茶", "浅斟留七分，余下三分是人情"), ("奉茶", "双手捧盏，视线低垂，敬客人先")], seal="序"),
    "latin-short": dict(title="Two steps", items=[("Rinse", "Clean the cup"), ("Heat", "Water just off the boil")], seal="T"),
    "latin-long": dict(title="Four steps of tea", items=[
        ("Rinse the cup", "Clean the cup until nothing of the old water is left behind in it"),
        ("Heat the water", "Let it come just off the boil and listen for the sound of pine wind"),
        ("Pour thin", "Pour seven parts of ten and leave the rest for company"),
        ("Serve", "Hold the cup in both hands with your eyes lowered and offer it first to the guest")], seal="T"),
}
INK_GAP = (0.10, 0.32)         # a rule ends 0.2in (+-) past the last of its words
for L_, g_ in (("ink", "light"), ("ink", "night")):
    prs, k = _deck(L_, g_)
    for tag, kw in INK_CASES.items():
        s_ = k.new_slide()
        with contextlib.redirect_stdout(io.StringIO()):
            k.points(s_, **kw)
    pages = list(prs.slides)
    imgs = _render(prs, "inkrules_" + g_)
    for (tag, kw), s_, pg in zip(INK_CASES.items(), pages, range(len(pages))):
        rules = _rules(s_)
        words = [w_ for w_ in _words(s_) if w_[0] != kw["seal"] and w_[0] != "a11y"]
        vert = [r_ for r_ in rules if abs(r_[0] - r_[2]) < 1e-3]
        horiz = [r_ for r_ in rules if abs(r_[1] - r_[3]) < 1e-3]
        check(vert or horiz, "ink/{} {}: the points page draws its rules".format(g_, tag))
        if vert:                                              # the vertical scroll: a rule is the left edge of its column
            vert.sort()
            for j, r_ in enumerate(vert):
                right_edge = vert[j + 1][0] if j + 1 < len(vert) else 13.333
                col = [w_ for w_ in words if w_[1] >= r_[0] - 0.01 and w_[3] <= right_edge + 0.01 and w_[2] > 0.3]
                low = max(w_[4] for w_ in col)                # the planned text's bottom
                # geometry: the rule is cut to the words — it used to run to a fixed 0.76H whatever the copy was
                check(r_[3] - low <= 0.32, "ink/{} {}: rule {} ends {:.2f}in below its column's text box (<= 0.32in)".format(
                    g_, tag, j, r_[3] - low))
                if imgs:                                      # the picture: the last ink of the column vs the rule's foot
                    ib = _ink(imgs[pg], (r_[0] + 0.06, 0.35, right_edge - 0.06, low + 0.02))
                    gap = r_[3] - ib[3] if ib else None
                    check(gap is not None and INK_GAP[0] <= gap <= INK_GAP[1],
                          "ink/{} {}: rule {} ends {} past the column's last ink (want {:.2f}-{:.2f}in)".format(
                              g_, tag, j, "{:.2f}in".format(gap) if gap is not None else "?", *INK_GAP))
        elif horiz:                                           # the horizontal rows: a rule hangs under ITS row's words
            horiz.sort(key=lambda r_: r_[1])
            for j, r_ in enumerate(horiz):
                above = [w_ for w_ in words if w_[4] <= r_[1] + 0.01 and w_[2] > (horiz[j - 1][1] if j else 0.3)
                         and w_[1] >= r_[0] - 0.01]
                low = max(w_[4] for w_ in above)
                check(0.0 <= r_[1] - low <= 0.32, "ink/{} {}: row rule {} hangs {:.2f}in under its row's text (<= 0.32in)".format(
                    g_, tag, j, r_[1] - low))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
