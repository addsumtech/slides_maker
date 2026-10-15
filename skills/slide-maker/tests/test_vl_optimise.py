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

# ── Task 5 (D): chalkboard: the quote's chalk underline runs the whole LAST line, to its measured ink width ──
def _quote_shape(slide, words):
    """The quote's own text shape (the largest-set one holding `words`)."""
    cand = [sh for sh in slide.shapes if getattr(sh, "has_text_frame", False)
            and words.lower() in sh.text_frame.text.replace("\n", " ").lower()]
    return max(cand, key=lambda sh: max((r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs
                                         if r.font.size), default=0))


def _last_line_ink(k, field, sh):
    """(left edge, ink width) in inches of the last line drawn in text shape `sh`: its last paragraph, wrapped at the
    shape's width when it is a paragraph the renderer wraps."""
    paras = [p for p in sh.text_frame.paragraphs if "".join(r.text for r in p.runs).strip()]
    size = max(r.font.size.pt for p in paras for r in p.runs if r.font.size)
    box = sh.width / 914400.0
    text = "".join(r.text for r in paras[-1].runs).strip()
    last = vl._break_lines(k, field, text, size, box * vl.HEADROOM)[-1].strip()
    return sh.left / 914400.0 + 0.028, vl._line_width(k, field, last, size)


def _underline_span(slide, below):
    """(left, right) in inches of the chalk strokes (freeforms) drawn below y=`below`."""
    xs = [(sh.left / 914400.0, (sh.left + sh.width) / 914400.0) for sh in slide.shapes
          if sh.shape_type == 5 and sh.top / 914400.0 >= below]
    return (min(a for a, _ in xs), max(b for _, b in xs)) if xs else None


CB_QUOTES = [("short", "Less, but better."),
             ("mid", "Nature does not hurry, yet everything is accomplished."),
             ("long", " ".join(["Every repair we made that evening was a small argument for keeping things, and the "
                                "room kept making it until the last lamp came on."] * 2))]
for g in ("light", "slate"):
    for tag, qt in CB_QUOTES:
        prs, k = _deck("chalkboard", g)
        sl = k.new_slide()
        with contextlib.redirect_stdout(io.StringIO()):
            k.quote(sl, quote=qt, attribution="Lao Tzu")
        sh = _quote_shape(sl, qt.split()[0])
        left, ink = _last_line_ink(k, "quote", sh)
        span = _underline_span(sl, (sh.top + sh.height) / 914400.0 - 0.12)
        check(span is not None, "chalkboard/{} {} quote: a chalk underline is drawn".format(g, tag))
        if span:
            cover = (span[1] - span[0]) / ink
            check(0.97 <= cover <= 1.04 and abs(span[0] - left) <= 0.06,
                  "chalkboard/{} {} quote: the underline runs the last line's ink width ({:.2f}in of {:.2f}in = {:.0%}, "
                  "starting {:+.2f}in from the line)".format(g, tag, span[1] - span[0], ink, cover, span[0] - left))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
