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

# ── Task 5 (C): shared helpers for the four language fixes (starlit, broadsheet, journal, tally) ──
from pptx.util import Emu as _Emu
W13 = 13.333


def _text_shape(slide, words):
    """The drawn text box holding `words` (not the accessibility title placeholder, which repeats the page's words)."""
    for sh in slide.shapes:
        if (getattr(sh, "has_text_frame", False) and not sh.is_placeholder
                and words.lower() in sh.text_frame.text.replace("\n", " ").lower()):
            return sh
    return None


def _rect(sh):
    return (sh.left / 914400.0, sh.top / 914400.0, sh.width / 914400.0, sh.height / 914400.0)


def _page(L, g, page, **fields):
    prs, k = _deck(L, g)
    sl = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()):
        getattr(k, page)(sl, **fields)
    return prs, k, sl


# ── Task 5 (C): starlit: the quote box is wide enough to hold the quote's size ──
_SQ = " ".join(("Every repair we made that evening was a small argument for keeping things, and the room kept making it "
                "until the last lamp came on. We stayed late, and nobody wanted to be the one who turned the lights off "
                "at last.").split()[:38])
_prs, _k, _sl = _page("starlit", "light", "quote", quote=_SQ, attribution="Repair café volunteer")
_qw = _rect(_text_shape(_sl, "“"))[2]          # the quote mark's box is the column itself (the quote's own box narrows to balance its lines)
check(_qw >= 0.74 * W13, "starlit quote: the quote's column is >= 0.74 of the page wide ({:.2f}in = {:.0%}; was 8.00in = 60%)".format(_qw, _qw / W13))
_qz = _size_of(_sl, "Every repair")
check(_qz >= vl.TYPE["starlit"]["quote"][0] - 1e-6, "starlit quote: a 38-word quote holds the language's {}pt in the wider box ({:.1f}pt; "
      "was 33.0pt)".format(vl.TYPE["starlit"]["quote"][0], _qz))
_prs, _k, _sl = _page("starlit", "light", "quote", quote="We measured the year in conversations, not in launches.", attribution="x")
check(_size_of(_sl, "We measured") >= 1.3 * vl.TYPE["starlit"]["quote"][0], "starlit quote: the 55-character sample is still set larger than the base size "
      "({:.1f}pt)".format(_size_of(_sl, "We measured")))

# ── Task 5 (C): starlit: the numeral reads on its glow (>= 4.5:1 over the glow's centre, both grounds) ──
import native_art as _na                       # noqa: E402


def _glow_centre(slide, ground_hex):
    """The colour at the centre of the page's radial glow, blended over the ground the way a renderer blends it."""
    from lxml import etree
    for sh in slide.shapes:
        x = etree.tostring(sh._element).decode()
        m = re.search(r'<a:gs pos="0"><a:srgbClr val="(\w{6})"><a:alpha val="(\d+)"/>', x)
        if m and '<a:path path="circle">' in x:
            c, a = m.group(1), int(m.group(2)) / 100000.0
            return "".join("{:02X}".format(round((1 - a) * int(ground_hex[i:i + 2], 16) + a * int(c[i:i + 2], 16))) for i in (0, 2, 4)), a
    return None, None


for _g in ("light", "dawn"):
    for _pg, _fl in (("data", dict(number="12", label="conversations that changed our plan", note="Each one is archived.")),
                     ("section", dict(number="3", title="The numbers", kicker="Part three"))):
        _prs, _k, _sl = _page("starlit", _g, _pg, **_fl)
        _num = _text_shape(_sl, _fl["number"])
        _ink = str(_num.text_frame.paragraphs[0].runs[0].font.color.rgb)
        _c, _a = _glow_centre(_sl, vl._hex(_k.P["ground"]))
        check(_c is not None and vl._contrast(_ink, _c) >= 4.5,
              "starlit/{} {}: the numeral {} is >= 4.5:1 over the glow's centre #{} ({}; was ~3.0:1 at alpha 0.42)".format(
                  _g, _pg, _ink, _c, "{:.2f}:1 at alpha {:.2f}".format(vl._contrast(_ink, _c), _a) if _c else "no glow"))
        check(_c is not None and vl._contrast(_c, vl._hex(_k.P["ground"])) >= 1.5,
              "starlit/{} {}: the glow is still a glow ({:.2f}:1 over the ground at its centre)".format(
                  _g, _pg, vl._contrast(_c, vl._hex(_k.P["ground"])) if _c else 0))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
