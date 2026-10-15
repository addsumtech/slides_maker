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
    """The deck's pages as PIL images (cached), or None when no renderer is installed. A renderer that is installed but
    returns nothing (another soffice holding the profile) is retried on its own profile, then FAILS the run — a measured
    check must not skip itself without a word."""
    if not CAN_RENDER:
        return None
    if tag not in _PNG:
        pp = WORK / (tag + ".pptx"); prs.save(str(pp))
        pages = []
        for attempt in range(3):
            subprocess.run(["soffice", "-env:UserInstallation=file://" + str(WORK / ("lo_profile%d" % attempt)), "--headless",
                            "--convert-to", "pdf", "--outdir", str(WORK), str(pp)], capture_output=True, timeout=240)
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(WORK / (tag + ".pdf")), str(WORK / (tag + "_pg"))],
                           capture_output=True, timeout=240)
            pages = [Image.open(f).convert("RGB") for f in sorted(WORK.glob(tag + "_pg*.png"))]
            if pages:
                break
        check(len(pages) == len(prs.slides), "the renderer drew all {} pages of {} (got {})".format(len(prs.slides), tag, len(pages)))
        _PNG[tag] = pages
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


def _ink_runs(img, box, dpi=100, gap=0.10, thr=70):
    """The horizontal bands of ink in `box`: [(y0, y1)] in inches, bands closer than `gap` merged."""
    a = np.asarray(img).astype(int)
    x0, y0, x1, y1 = [max(0, int(round(v * dpi))) for v in box]
    r = a[y0:y1, x0:x1]
    hit = (np.abs(r - np.median(r.reshape(-1, 3), axis=0)).sum(axis=2) > thr).any(axis=1)
    out, start, last = [], None, None
    for i, h in enumerate(hit):
        if h:
            if start is None:
                start = i
            elif i - last > gap * dpi:
                out.append((start, last)); start = i
            last = i
    if start is not None:
        out.append((start, last))
    return [((a_ + y0) / dpi, (b_ + 1 + y0) / dpi) for a_, b_ in out]


# ── Task 5 (B): poster: the quote's attribution sits ~0.4in under the quote's last line (it sat 1.12in under) ──
PQ = {"one line": "Make it.", "three lines": "A room is a promise you can walk into.",
      "five lines": "A room is a promise you can walk into, and a street is a long hallway of rooms that nobody locked, so "
                    "we keep the doors open and the benches warm for whoever is next in line to mend something."}
for g_ in ("light", "paper"):
    prs, k = _deck("poster", g_)
    for tag, q_ in PQ.items():
        with contextlib.redirect_stdout(io.StringIO()):
            k.quote(k.new_slide(), quote=q_, attribution="From the manifesto")
    imgs = _render(prs, "pq_" + g_)
    for (tag, q_), s_, pg in zip(PQ.items(), prs.slides, range(3)):
        wd = _words(s_)
        qb = next(w_ for w_ in wd if w_[0].upper().startswith(q_[:8].upper()))
        ab = next(w_ for w_ in wd if w_[0].startswith("From the"))
        if imgs:
            runs = _ink_runs(imgs[pg], (qb[1], qb[2], qb[3], ab[4] + 0.05))
            gap = runs[-1][0] - runs[-2][1] if len(runs) >= 2 else None
            check(gap is not None and 0.30 <= gap <= 0.55,
                  "poster/{} quote ({}): the attribution's ink starts {} under the quote's last line (want 0.30-0.55in)".format(
                      g_, tag, "{:.2f}in".format(gap) if gap is not None else "?"))
        else:                                        # no renderer: the planned boxes — the attribution right under the quote's
            check(-0.1 <= ab[2] - qb[4] <= 0.3, "poster/{} quote ({}): the attribution's box starts {:.2f}in from the quote's".format(
                g_, tag, ab[2] - qb[4]))
        check(not [f for f in _hard(prs, "pqh_" + g_ + tag.replace(" ", "")) if f.startswith("slide {}:".format(pg + 1))],
              "poster/{} quote ({}): the page stays lint-clean".format(g_, tag))
dk.set_theme(None)


# ── Task 5 (B): poster: the points staircase fills the page (the bottom-left 28% was empty) and still climbs with the order ──
PP = {"3 points": ("Three moves.", ["Share the tools", "Open the door", "Keep it local"]),
      "2 points": ("Two moves.", ["Share the tools", "Open the door"]),
      "4 points": ("Four moves for a street", ["Share the tools", "Open the door", "Keep it local", "Mend it together"]),
      "one-line title": ("Moves", ["Share the tools", "Open the door", "Keep it local"])}
for g_ in ("light", "paper"):
    prs, k = _deck("poster", g_)
    for tag, (t_, its) in PP.items():
        with contextlib.redirect_stdout(io.StringIO()):
            k.points(k.new_slide(), title=t_, items=its)
    for pg, ((tag, (t_, its)), s_) in enumerate(zip(PP.items(), prs.slides)):
        bars = sorted([(_inch(sh.left), _inch(sh.top), _inch(sh.width), _inch(sh.height)) for sh in s_.shapes
                       if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and _inch(sh.width) > 1.0], key=lambda b_: b_[0])
        check(len(bars) == len(its), "poster/{} points ({}): one bar a point ({} bars)".format(g_, tag, len(bars)))
        if len(bars) != len(its):
            continue
        # the staircase still encodes order: each step is taller than the one before and stands to its right
        check(all(b2[3] > b1[3] + 0.2 and b2[0] > b1[0] + b1[2] - 1e-6 and abs((b2[1] + b2[3]) - (b1[1] + b1[3])) < 0.01
                  for b1, b2 in zip(bars, bars[1:])),
              "poster/{} points ({}): the steps rise left to right on one baseline ({})".format(
                  g_, tag, ["{:.2f}".format(b_[3]) for b_ in bars]))
        # the bottom-left quarter of the page, under the title: how much of it carries ink (bars)
        tw = [w_ for w_ in _words(s_) if w_[0].upper().startswith(t_.split()[0].upper())][0]
        reg = (0.0, tw[4], 6.667, 7.5)              # below the title's box, left half
        area = (reg[2] - reg[0]) * (reg[3] - reg[1])
        cover = sum(max(0.0, min(b_[0] + b_[2], reg[2]) - max(b_[0], reg[0])) * max(0.0, min(b_[1] + b_[3], reg[3]) - max(b_[1], reg[1]))
                    for b_ in bars)
        check(cover / area >= 0.35, "poster/{} points ({}): the bottom-left under the title is {:.0%} filled (want >= 35%)".format(
            g_, tag, cover / area))
        check(not [f for f in _hard(prs, "ppt_" + g_ + str(pg)) if f.startswith("slide {}:".format(pg + 1))],
              "poster/{} points ({}): the page stays lint-clean".format(g_, tag))
dk.set_theme(None)


from pptx.enum.shapes import MSO_SHAPE


def _fill_of(sh):
    try:
        return str(sh.fill.fore_color.rgb) if sh.fill.type == 1 else None
    except Exception:
        return None


def _cards(slide, min_w=1.5):
    """The paper cards of a cutpaper page: rounded rectangles >= min_w wide -> [(x, y, w, h, fill, rotation)]."""
    return [(_inch(sh.left), _inch(sh.top), _inch(sh.width), _inch(sh.height), _fill_of(sh), sh.rotation)
            for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
            and sh.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE and _inch(sh.width) >= min_w]


# ── Task 5 (B): cutpaper: the cover's card is as tall as its words + padding + the hill tuck (it was a fixed 0.47H) ──
CCV = {"one word": dict(kicker="A paper-cut science story", title="Seeds"),
       "sample": dict(kicker="A paper-cut science story", title="How seeds travel"),
       "long": dict(kicker="A paper-cut science story", title="Why every forest on this hillside began as one small seed",
                    subtitle="Wings, water and fur carry them further than you would think."),
       "cjk": dict(kicker="剪纸科学故事", title="种子如何旅行")}
for g_ in ("light", "night"):
    prs, k = _deck("cutpaper", g_)
    for tag, kw in CCV.items():
        with contextlib.redirect_stdout(io.StringIO()):
            k.cover(k.new_slide(), **kw)
    imgs = _render(prs, "ccv_" + g_)
    for pg, ((tag, kw), s_) in enumerate(zip(CCV.items(), prs.slides)):
        cards = sorted(_cards(s_), key=lambda c_: -c_[2] * c_[3])
        check(bool(cards), "cutpaper/{} cover ({}): the title card is drawn".format(g_, tag))
        if not cards:
            continue
        cx_, cy_, cw_, ch_ = cards[0][:4]
        inside = [w_ for w_ in _words(s_) if w_[1] >= cx_ - 0.01 and w_[3] <= cx_ + cw_ + 0.01 and w_[2] >= cy_ - 0.01
                  and w_[4] <= cy_ + ch_ + 0.01]
        low = max(w_[4] for w_ in inside)
        # the card runs 0.4in of padding + the 0.3in the near hill tucks it under past its words, and no further
        check(0.55 <= cy_ + ch_ - low <= 0.80, "cutpaper/{} cover ({}): the card ends {:.2f}in under its words "
              "(want 0.55-0.80: padding + tuck)".format(g_, tag, cy_ + ch_ - low))
        if imgs:                                     # the picture: the card as it SHOWS, above the near hill's crest
            im = imgs[pg]
            px_ = lambda x, y: im.getpixel((int(round(x * 100)), int(round(y * 100))))        # noqa: E731
            col = px_(cx_ + cw_ - 0.25, cy_ + 0.2)
            shown = 99.0
            for i_ in range(12):                      # per column, from below the card up to its own colour: the crest
                x = cx_ + 0.3 + (cw_ - 0.6) * i_ / 11.0
                y = min(cy_ + ch_, im.size[1] / 100.0 - 0.05)
                while y > cy_ + 0.3 and sum(abs(a_ - b_) for a_, b_ in zip(px_(x, y), col)) >= 40:
                    y -= 0.01
                shown = min(shown, y)
            ib = _ink(im, (cx_ + 0.3, cy_ + 0.05, cx_ + cw_ - 0.3, shown - 0.02))
            blank = shown - ib[3] if ib else None
            check(blank is not None and 0.20 <= blank <= 0.75, "cutpaper/{} cover ({}): {} of bare card shows under the last "
                  "ink (want 0.20-0.75in)".format(g_, tag, "{:.2f}in".format(blank) if blank is not None else "?"))
        check(not [f for f in _hard(prs, "ccvh_" + g_ + str(pg)) if f.startswith("slide {}:".format(pg + 1))],
              "cutpaper/{} cover ({}): the page stays lint-clean".format(g_, tag))
dk.set_theme(None)


# ── Task 5 (B): cutpaper: the points cards are as tall as their content + padding, all one height (22-30% was empty) ──
CPT = {"3 short": ("Three ways a seed gets around", [("Wind", "Wings and parachutes drift far."),
                                                      ("Water", "Some seeds float to a new shore."),
                                                      ("Animals", "Hooks hitch a ride on fur.")], None),
       "2 short": ("Two ways", [("Wind", "Drift far."), ("Water", "Float to a shore.")], None),
       "icons": ("Three ways a seed gets around", [("Wind", "Wings and parachutes drift far."),
                                                   ("Water", "Some seeds float to a new shore."),
                                                   ("Animals", "Hooks hitch a ride on fur.")],
                 ["lucide:wind", "lucide:droplets", "lucide:paw-print"]),
       "4 long": ("Four ways a seed gets around the hillside", [
           ("Wind carries the light ones", "Wings and parachutes let a seed drift for a whole afternoon before it lands."),
           ("Water floats the heavy ones", "Some seeds are buoyant enough to ride a stream down to a brand new shore."),
           ("Animals hitch a ride", "Hooks and burrs catch on fur and stay there until they are scratched loose."),
           ("People carry them too", "Every pocket and boot sole on the path is a small seed vehicle.")], None),
       "cjk": ("种子旅行的三种方式", [("风", "种子随风飘得很远。"), ("水", "种子漂到新的岸边。"),
                                     ("动物", "种子挂在毛上搭车。")], None)}
for g_ in ("light", "night"):
    prs, k = _deck("cutpaper", g_)
    for tag, (t_, its, ic_) in CPT.items():
        with contextlib.redirect_stdout(io.StringIO()):
            k.points(k.new_slide(), title=t_, items=its, **({"icons": ic_} if ic_ else {}))
    for pg, ((tag, (t_, its, ic_)), s_) in enumerate(zip(CPT.items(), prs.slides)):
        cards = [c_ for c_ in _cards(s_) if c_[3] >= 1.0]
        check(len(cards) == len(its), "cutpaper/{} points ({}): one card a point ({})".format(g_, tag, len(cards)))
        if not cards:
            continue
        hs = [c_[3] for c_ in cards]
        check(max(hs) - min(hs) < 0.01, "cutpaper/{} points ({}): the cards share one height ({})".format(
            g_, tag, ["{:.2f}".format(h_) for h_ in hs]))
        wd = _words(s_)
        discs = [(_inch(sh.left), _inch(sh.top), _inch(sh.left + sh.width), _inch(sh.top + sh.height)) for sh in s_.shapes
                 if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and sh.auto_shape_type == MSO_SHAPE.OVAL and _inch(sh.width) < 1.5]
        blanks = []
        for ci, (cx_, cy_, cw_, ch_, _f, _r) in enumerate(cards):
            inside = [w_[4] for w_ in wd if w_[1] >= cx_ - 0.01 and w_[3] <= cx_ + cw_ + 0.01 and w_[2] >= cy_ - 0.01
                      and w_[4] <= cy_ + ch_ + 0.05]
            inside += [d_[3] for d_ in discs if d_[0] >= cx_ - 0.01 and d_[2] <= cx_ + cw_ + 0.01 and d_[1] >= cy_ - 0.01]
            blanks.append((cy_ + ch_ - max(inside)) / ch_)
        # one shared height means the card with the fewest words keeps a line's worth more paper than the fullest one
        check(0.04 <= min(blanks) and min(blanks) <= 0.15 and max(blanks) <= 0.22,
              "cutpaper/{} points ({}): the cards are {} empty under their content (fullest 4-15%, emptiest <= 22%)".format(
                  g_, tag, "/".join("{:.0%}".format(b_) for b_ in blanks)))
        check(not [f for f in _hard(prs, "cptl_" + g_ + str(pg)) if f.startswith("slide {}:".format(pg + 1))],
              "cutpaper/{} points ({}): the page stays lint-clean (no UNEVEN CARD HEIGHTS)".format(g_, tag))
dk.set_theme(None)


# ── Task 5 (B): cutpaper night: the cards are the cream paper of the back sheet, not pure white on navy ──
CREAM = "F1E7C8"
for g_, want in (("light", "FFFFFF"), ("night", CREAM)):
    prs, k = _deck("cutpaper", g_)
    with contextlib.redirect_stdout(io.StringIO()):
        k.cover(k.new_slide(), kicker="A paper-cut science story", title="How seeds travel")
        k.points(k.new_slide(), title="Three ways a seed gets around", items=[("Wind", "Drift far."), ("Water", "Float."),
                                                                          ("Animals", "Hitch a ride.")])
        k.quote(k.new_slide(), quote="Every forest began as one small seed.", attribution="A paper-cut science story")
        k.closing(k.new_slide(), title="Plant one", line="and watch it travel")
    for pg, (page, s_) in enumerate(zip(("cover", "points", "quote", "closing"), prs.slides)):
        cards = [c_ for c_ in _cards(s_) if abs(c_[5]) < 0.01]                  # the page's own cards (the back sheets tilt)
        check(bool(cards), "cutpaper/{} {}: the cards are drawn".format(g_, page))
        check(all(c_[4] == want for c_ in cards), "cutpaper/{} {}: every card is {} ({})".format(
            g_, page, want, sorted({c_[4] for c_ in cards})))
        wd = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0]
        for c_ in cards:
            for sh in wd:
                x_, y_ = _inch(sh.left), _inch(sh.top)
                if not (c_[0] - 0.01 <= x_ and x_ + _inch(sh.width) <= c_[0] + c_[2] + 0.01 and c_[1] - 0.01 <= y_ <= c_[1] + c_[3]):
                    continue
                for p_ in sh.text_frame.paragraphs:
                    for r_ in p_.runs:
                        if r_.text.strip() and r_.font.color and r_.font.color.type and str(r_.font.color.rgb) != "FFFFFF":
                            cr_ = dk.contrast_ratio(str(r_.font.color.rgb), want)
                            check(cr_ >= 4.5, "cutpaper/{} {}: {!r} ({}) reads on its card at {:.2f}:1 (want >= 4.5)".format(
                                g_, page, r_.text[:14], r_.font.color.rgb, cr_))
dk.set_theme(None)
pal_n = vl.REGISTRY["cutpaper"]["grounds"]["night"]["palette"]
check(pal_n["paper"].upper() == CREAM and dk.contrast_ratio(pal_n["paper"], pal_n["ground"]) < 14.0,
      "cutpaper night: the cards' paper is the cream of the back sheet ({})".format(pal_n.get("paper")))
check(all(dk.contrast_ratio(pal_n[key], pal_n["paper"]) >= 4.5 for key in ("card_ink", "card_mute", "card_accent")),
      "cutpaper night: card_ink, card_mute and card_accent read on the paper at >= 4.5:1 ({})".format(
          ["{:.2f}".format(dk.contrast_ratio(pal_n[key], pal_n["paper"])) for key in ("card_ink", "card_mute", "card_accent")]))
check(vl.REGISTRY["cutpaper"]["grounds"]["light"]["palette"]["paper"].upper() == "FFFFFF", "cutpaper day: the paper stays white")
# `panel` is the ordinary page's card (it carries the light default inks): the night keeps it navy
check(dk.contrast_ratio(pal_n["ink"], pal_n["panel"]) >= 4.5, "cutpaper night: the ordinary page's panel still carries the default ink")

# ── Task 5 (B): drafting points: the leader's head outranks the line under it (it was 11pt Courier under a 15pt line) ──
DPT = {"3 short": ("Three layers, one frame", [("Floor", "One continuous plate."), ("Walls", "Panels that slide on a track."),
                                                ("Roof", "A single span, no columns.")]),
       "2 short": ("Two layers", [("Floor", "One continuous plate."), ("Walls", "Panels that slide.")]),
       "4 long": ("Four layers, one frame", [
           ("Floor", "One continuous plate poured in a single day and left to cure for a week."),
           ("Walls", "Panels that slide on a track and lock at any of the nine positions."),
           ("Roof", "A single span with no columns, lifted whole by four cranes."),
           ("Skin", "A rain screen that can be replaced one panel at a time.")])}
for g_ in ("light", "cyanotype"):
    prs, k = _deck("drafting", g_)
    for tag, (t_, its) in DPT.items():
        with contextlib.redirect_stdout(io.StringIO()):
            k.points(k.new_slide(), title=t_, items=its)
    for pg, ((tag, (t_, its)), s_) in enumerate(zip(DPT.items(), prs.slides)):
        shapes = [sh for sh in s_.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0]
        for head, line in its:
            hs = [sh for sh in shapes if sh.text_frame.text.strip() == head]
            ls = [sh for sh in shapes if sh.text_frame.text.strip().startswith(line[:12])]
            if not hs or not ls:
                check(False, "drafting/{} points ({}): {} and its line are drawn".format(g_, tag, head)); continue
            hr, lr = hs[0].text_frame.paragraphs[0].runs[0], ls[0].text_frame.paragraphs[0].runs[0]
            # ordinary copy: 16pt+ and clear of the line; copy so long that every field is squeezed toward its floor:
            # still bold serif and larger than the line under it
            roomy = tag != "4 long"
            check(hr.font.size.pt >= (16 if roomy else 11) and hr.font.size.pt >= lr.font.size.pt + (2 if roomy else 0.5)
                  and bool(hr.font.bold) and hr.font.name != "Courier New",
                  "drafting/{} points ({}): {!r} is {:.0f}pt {} {} over a {:.0f}pt line (want {}, bold serif, larger than the line)".format(
                      g_, tag, head, hr.font.size.pt, "bold" if hr.font.bold else "regular", hr.font.name, lr.font.size.pt,
                      ">= 16pt" if roomy else "squeezed copy still ranks head over line"))
        check(not [f for f in _hard(prs, "dptl_" + g_ + str(pg)) if f.startswith("slide {}:".format(pg + 1))],
              "drafting/{} points ({}): the page stays lint-clean".format(g_, tag))
dk.set_theme(None)


# ── Task 5 (B): drafting cover and quote: a ghost drawing fills the blank right of the words, clear of every word ──
def _ghosts(slide):
    """The faint drawing: the outline-only freeform shapes declared decorative -> [(x0, y0, x1, y1)]."""
    return [(_inch(sh.left), _inch(sh.top), _inch(sh.left + sh.width), _inch(sh.top + sh.height)) for sh in slide.shapes
            if sh.shape_type == MSO_SHAPE_TYPE.FREEFORM and "+decor" in sh.name.split(":")[0] and "drafting" in sh.name]


for g_ in ("light", "cyanotype"):
    prs, k = _deck("drafting", g_)
    with contextlib.redirect_stdout(io.StringIO()):
        k.cover(k.new_slide(), kicker="Schematic 01 · a modular reading room", title="A room built layer by layer.",
                subtitle="Floor, walls and roof drawn as one frame, each layer free to move.")
        k.quote(k.new_slide(), quote="“Draw the quiet first, then the walls.”", attribution="Design principle")
        k.quote(k.new_slide(), quote="Draw the quiet first, then the walls, then the roof, then the light that will fall "
                                     "across the floor at four in the afternoon.", attribution="Design principle")
    imgs = _render(prs, "dgh_" + g_)
    for pg, (page, s_) in enumerate(zip(("cover", "quote", "long quote"), prs.slides)):
        gh = _ghosts(s_)
        check(len(gh) >= 1, "drafting/{} {}: a ghost drawing is declared decorative ({} shapes)".format(g_, page, len(gh)))
        if not gh:
            continue
        gx0, gy0, gx1, gy1 = min(g[0] for g in gh), min(g[1] for g in gh), max(g[2] for g in gh), max(g[3] for g in gh)
        wd = _words(s_)
        over = [w_[0][:18] for w_ in wd if w_[1] < gx1 + 0.02 and gx0 - 0.02 < w_[3] and w_[2] < gy1 + 0.02 and gy0 - 0.02 < w_[4]]
        check(not over, "drafting/{} {}: the ghost drawing ({:.1f}-{:.1f}in across) touches no word box ({})".format(
            g_, page, gx0, gx1, over))
        check(gx1 - gx0 >= 2.2 and gy1 - gy0 >= 2.2 and gx0 > 6.0,
              "drafting/{} {}: the ghost fills the right of the sheet ({:.1f}x{:.1f}in from x={:.1f})".format(
                  g_, page, gx1 - gx0, gy1 - gy0, gx0))
        if imgs:                                   # it SHOWS: a faint line, but there, and nothing else is in that corner
            ib = _ink(imgs[pg], (gx0 - 0.1, gy0 - 0.1, gx1 + 0.1, gy1 + 0.1), thr=45)
            check(ib is not None and (ib[2] - ib[0]) >= 0.6 * (gx1 - gx0), "drafting/{} {}: the ghost drawing is visible".format(g_, page))
        check(not [f for f in _hard(prs, "dghl_" + g_ + str(pg)) if f.startswith("slide {}:".format(pg + 1))],
              "drafting/{} {}: the page stays lint-clean".format(g_, page))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
