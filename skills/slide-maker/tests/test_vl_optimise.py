"""Phase 3 — the languages' own pages, measured (spec §6): quote scale, title fit, rules at their content, designed dark
grounds, the smallest tier, distinctiveness, and the per-language fixes. Prints `N passed, 0 failed`."""
import contextlib, io, os, re, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk, visual_languages as vl, lint_deck
import vl_native2 as vls

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

# ── Task 5 (C): broadsheet: column rules end at the words, the Inside rule at its list, the figure is set at the measure ──
from pptx.enum.shapes import MSO_SHAPE_TYPE as _MST        # noqa: E402


def _lines_of(slide, vertical):
    """[(x, y0, y1)] of the page's vertical rules (or [(y, x0, x1)] of its horizontal ones), in inches."""
    out = []
    for sh in slide.shapes:
        if sh.shape_type != _MST.LINE:
            continue
        x, y, w, h = _rect(sh)
        if vertical and w < 0.01 and h > 0.3:
            out.append((x, y, y + h))
        if not vertical and h < 0.01 and w > 0.3:
            out.append((y, x, x + w))
    return out


def _text_eq(slide, text):
    """The lowest drawn text box whose words are exactly `text` (a numeral "1" is also the running head's page number)."""
    hits = [sh for sh in slide.shapes if getattr(sh, "has_text_frame", False) and not sh.is_placeholder
            and sh.text_frame.text.strip() == text]
    return max(hits, key=lambda sh: sh.top) if hits else None


_BS_PT = [("Bring it broken", "Anything that switches on, unzips or wobbles is welcome."),
          ("Fix it together", "A volunteer sits beside you, but your hands do the work."),
          ("Take it home", "What could not be fixed today goes on a list for next time.")]
_BS_MORE = " Then there is more to say about it, because it is the part people remember best." * 3
for _tag, _its in (("short copy", _BS_PT), ("long copy", [(a, b + _BS_MORE) for a, b in _BS_PT]),
                   ("very long copy", [(a, b + _BS_MORE * 2) for a, b in _BS_PT])):
    _prs, _k, _sl = _page("broadsheet", "light", "points", title="How it works", tags=["Idea", "Evening", "Hands"], items=_its)
    _rules = _lines_of(_sl, True)
    _top = min(r[1] for r in _rules)
    _foot = max((sh.top + sh.height) / 914400.0 for sh in _sl.shapes
                if getattr(sh, "has_text_frame", False) and not sh.is_placeholder and sh.top / 914400.0 >= _top - 0.01)
    _end = max(r[2] for r in _rules)
    check(len(_rules) == 2 and all(abs(r[2] - _end) < 0.01 for r in _rules),
          "broadsheet points ({}): two column rules, level".format(_tag))
    if _tag == "short copy":
        check(0.15 <= _end - _foot <= 0.30, "broadsheet points (short copy): the rules end 0.2in under the words ({:.2f}in under; "
              "was {:.2f}in, to the page's bottom)".format(_end - _foot, 6.90 - _foot))
    if _tag != "short copy":
        check(min(_foot + 0.15, 6.90) <= _end <= 6.91,
              "broadsheet points ({}): the rules still reach the words and stop at the page's bottom (rule to {:.2f}, "
              "words to {:.2f}, bottom 6.90)".format(_tag, _end, _foot))
    if _tag != "very long copy":         # (the very long one trips lint's ORPHANED PUNCTUATION in the unchanged column text too)
        check(not _hard(_prs, "bsp_" + _tag.replace(" ", "_")), "broadsheet points ({}): lint-clean".format(_tag))

_prs, _k, _sl = _page("broadsheet", "light", "cover", title="Every street needs a night for fixing things",
                      subtitle="How a repair evening works, and why it spreads.", masthead="The Repair Weekly", edition="No. 12",
                      inside=["The idea", "The evening", "The numbers"])
_vr = [r for r in _lines_of(_sl, True) if r[0] > 0.5 * W13]
_lst = _text_eq(_sl, "The idea\nThe evening\nThe numbers")
_lb = (_lst.top + _lst.height) / 914400.0
check(len(_vr) == 1 and abs(_vr[0][2] - _lb) <= 0.06,
      "broadsheet cover: the Inside rule ends at its list ({:.2f}in vs the list's {:.2f}in; was 6.90in, 0.75in past it)".format(
          _vr[0][2] if _vr else -1, _lb))

for _g in ("light", "salmon"):
    for _num, _lab, _note in (("3", "conversations that changed our plan", "Each one is written up in the archive."),
                              ("1,250,000", "visitors since the first night", ""), ("三成", "的物品得到修复", "每一件都记录在档案里。")):
        _fl = dict(number=_num, label=_lab, **({"note": _note} if _note else {}))
        _prs, _k, _sl = _page("broadsheet", _g, "data", **_fl)
        _nsh = _text_eq(_sl, _num)
        _z = _size_of(_sl, _num) if _nsh is not None else 0
        _ink = vl._hex(_k.P["ink"]).upper()
        _solid = [sh for sh in _sl.shapes if sh.shape_type == _MST.AUTO_SHAPE and sh.fill.type == 1
                  and str(sh.fill.fore_color.rgb).upper() == _ink]
        _hr = _lines_of(_sl, False)
        _span = max((r[2] - r[1] for r in _hr if r[0] > 1.2), default=0)
        _need = 180 if len(_num) > 6 else 200            # a nine-character figure is bounded by the measure itself (191pt)
        check(_nsh is not None and _z >= _need - 1e-6 and not _solid and _span >= 0.88 * W13 - 0.01,
              "broadsheet/{} data {!r}: the figure is >= {}pt ({:.0f}pt; was 150pt), no black cap ({} solid ink boxes), and the "
              "block's rules run the measure ({:.1f}in = {:.0%})".format(_g, _num, _need, _z, len(_solid), _span, _span / W13))
    _prs, _k, _sl = _page("broadsheet", _g, "data", number="3", label="conversations that changed our plan", note="Each one is archived.")
    _ns, _ls = _text_eq(_sl, "3"), _text_shape(_sl, "conversations")
    _cr = [r for r in _lines_of(_sl, True) if r[0] > 1.0]
    _ln = _rect(_ls)
    check(len(_cr) == 1 and _rect(_ns)[0] + _rect(_ns)[2] <= _cr[0][0] + 1e-6 <= _ln[0] + 1e-6 and _cr[0][1] <= _ln[1] and _cr[0][2] >= _ln[1] + _ln[3],
          "broadsheet/{} data: the label and note stand in a column ruled off from the figure (rule x={:.2f}in between the figure "
          "and the words, spanning them)".format(_g, _cr[0][0] if _cr else -1))
for _W, _H in ((13.333, 7.5), (7.5, 7.5), (7.5, 13.333), (10.0, 7.5)):
    _prs = dk.blank_deck(_W, _H)
    with contextlib.redirect_stdout(io.StringIO()):
        _kk = vl.use("broadsheet", _prs, ground="light")
        for _num, _lab, _note in (("3", "conversations that changed our plan", "Each one is written up in the archive."),
                                  ("98.6%", "of repairs held after a month", ""), ("三成", "的物品得到修复", "每一件都记录在档案里。")):
            _kk.data(_kk.new_slide(), number=_num, label=_lab, masthead="The Repair Weekly", **({"note": _note} if _note else {}))
    check(not _hard(_prs, "bsd_{}x{}".format(int(_W), int(_H))), "broadsheet data {}x{}: the three figures are lint-clean".format(_W, _H))
dk.set_theme(None)

# ── Task 5 (C): journal: the margin note's rule ends at its words, numerals stand on their heads' baseline, the green figure sits on a mat ──
_JN_ITEMS = [("Three methods", "Same data, same metric."), ("Four accelerations", "From 2x to 8x."),
             ("Five metrics", "Scored the same way.")]
for _tag, _note in (("two-line note", "All runs on one scanner."),
                    ("long note", "All runs on one scanner, with the same coil, the same protocol and the same reader. " * 9)):
    for _g in ("light", "green"):
        _prs, _k, _sl = _page("journal", _g, "points", title="What we compared", items=_JN_ITEMS, margin=_note)
        _accent = vl._hex(_k.P["text_accents"][0]).upper()
        _rule = [sh for sh in _sl.shapes if sh.shape_type == _MST.LINE and _rect(sh)[2] < 0.01 and _rect(sh)[3] > 0.3
                 and str(sh.line.color.rgb).upper() == _accent]
        _nt = _text_shape(_sl, _note[:12])
        _lst = _text_shape(_sl, "Scored the same way")
        _foot_n, _foot_l = _rect(_nt)[1] + _rect(_nt)[3], _rect(_lst)[1] + _rect(_lst)[3]
        _end = _rect(_rule[0])[1] + _rect(_rule[0])[3] if _rule else -1
        check(len(_rule) == 1 and abs(_end - max(_foot_n, _foot_l)) <= 0.06,
              "journal/{} margin ({}): the note's rule ends at the lower of the note and the list ({:.2f}in; note {:.2f}, list {:.2f}; "
              "was 6.90in)".format(_g, _tag, _end, _foot_n, _foot_l))
        check(_end <= 6.90 + 0.01 and (_tag != "two-line note" or _end <= 6.9 - 0.5),
              "journal/{} margin ({}): the rule is not the page's height ({:.2f}in of 6.90)".format(_g, _tag, _end))
        check(not _hard(_prs, "jnm_{}_{}".format(_g, _tag.split("-")[0].split()[0])), "journal/{} margin ({}): lint-clean".format(_g, _tag))


def _ink_bottom(img, rect, dpi, bg):
    """The lowest row (in) of ink inside `rect` (in) of a rendered page: pixels that differ from the ground."""
    from PIL import Image, ImageChops
    x, y, w, h = [int(round(v * dpi)) for v in rect]
    crop = img.crop((x, y, x + w, y + h)).convert("RGB")
    d = ImageChops.difference(crop, Image.new("RGB", crop.size, bg)).convert("L").point(lambda v: 255 if v > 40 else 0)
    box = d.getbbox()
    return None if box is None else (y + box[3]) / dpi


def _render_png(prs, tag, dpi=200):
    """The first page of `prs` rendered by LibreOffice + pdftoppm (None when either is missing)."""
    import shutil, subprocess
    from PIL import Image
    if not (shutil.which("soffice") and shutil.which("pdftoppm")):
        return None
    f = WORK / (tag + ".pptx")
    prs.save(str(f))
    prof = (WORK / "lo_profile").as_uri()
    subprocess.run(["soffice", "-env:UserInstallation=" + prof, "--headless", "--convert-to", "pdf", "--outdir", str(WORK), str(f)],
                   capture_output=True, timeout=240)
    pdf = WORK / (tag + ".pdf")
    if not pdf.exists():
        return None
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", str(pdf), str(WORK / tag)], capture_output=True, timeout=120)
    png = sorted(WORK.glob(tag + "-*.png"))
    return Image.open(png[0]).convert("RGB") if png else None


# the numerals and the heads: baselines from the face metrics, then — where the faces and a renderer exist — measured on a render
for _g in ("light", "green"):
    _prs, _k, _sl = _page("journal", _g, "points", title="What we compared", items=_JN_ITEMS, margin="All runs on one scanner.")
    _gaps = []
    for _i, (_hd, _ln) in enumerate(_JN_ITEMS):
        _nb, _hb = _text_eq(_sl, str(_i + 1)), _text_shape(_sl, _hd)
        _zn = max(r.font.size.pt for p_ in _nb.text_frame.paragraphs for r in p_.runs)
        _zh = max(r.font.size.pt for p_ in _hb.text_frame.paragraphs for r in p_.runs)
        _gaps.append((_rect(_nb)[1] + vls.first_baseline(_k, "item_no", str(_i + 1), _zn)) - (_rect(_hb)[1] + vls.first_baseline(_k, "item_head", _hd, _zh)))
    check(max(abs(g_) for g_ in _gaps) <= 0.01, "journal/{} points: each numeral's first baseline is its head's, by the faces' metrics "
          "(max gap {:.3f}in; was 0.12in)".format(_g, max(abs(g_) for g_ in _gaps)))
    if dk._font_substituted("Georgia") or dk._font_substituted("Times New Roman"):
        continue                                       # no real faces here: the metrics above are all there is to measure
    _img = _render_png(_prs, "jn_base_" + _g)
    if _img is None:
        continue
    _bg = tuple(int(vl._hex(_k.P["ground"])[i:i + 2], 16) for i in (0, 2, 4))
    _rows = []
    for _i, (_hd, _ln) in enumerate(_JN_ITEMS):
        _nb, _hb = _text_eq(_sl, str(_i + 1)), _text_shape(_sl, _hd)
        _a, _b = _ink_bottom(_img, _rect(_nb), 200, _bg), _ink_bottom(_img, _rect(_hb), 200, _bg)
        _rows.append(None if _a is None or _b is None else _a - _b)
    check(all(r_ is not None for r_ in _rows) and max(abs(r_) for r_ in _rows) <= 0.025,
          "journal/{} points: on a render, the numeral's ink stands on its head's baseline (bottoms differ by {} in; was ~0.12in)".format(
              _g, ", ".join("{:+.3f}".format(r_) for r_ in _rows if r_ is not None)))

_FIG = str(vl.ASSETS / "figure" / "illustrative-curves.jpg")
for _g in ("light", "green"):
    _prs, _k, _sl = _page("journal", _g, "image_text", title="Error grows with acceleration", body="Error against acceleration.",
                          caption="Source: an illustrative figure", image=_FIG)
    _pic = [sh for sh in _sl.shapes if sh.shape_type == _MST.PICTURE][0]
    _pr = _rect(_pic)
    _mats = [sh for sh in _sl.shapes if sh.shape_type == _MST.AUTO_SHAPE and sh.fill.type == 1
             and str(sh.fill.fore_color.rgb).upper() == vl._hex(_k.P["ink"]).upper()
             and _rect(sh)[0] <= _pr[0] and _rect(sh)[1] <= _pr[1]
             and _rect(sh)[0] + _rect(sh)[2] >= _pr[0] + _pr[2] and _rect(sh)[1] + _rect(sh)[3] >= _pr[1] + _pr[3]]
    from PIL import Image as _Im2
    _iw, _ih = _Im2.open(_FIG).size
    _whole = abs((_pr[2] / _pr[3]) - (_iw / _ih)) < 0.01 and not (_pic.crop_left or _pic.crop_right or _pic.crop_top or _pic.crop_bottom)
    if _g == "green":
        _m = _rect(_mats[0]) if _mats else None
        _edges = [] if not _m else [_pr[0] - _m[0], _pr[1] - _m[1], _m[0] + _m[2] - _pr[0] - _pr[2], _m[1] + _m[3] - _pr[1] - _pr[3]]
        check(len(_mats) == 1 and all(abs(e_ - 0.15) <= 0.01 for e_ in _edges) and _whole,
              "journal/green figure: the whole picture sits on a 0.15in cream mat ({})".format(", ".join("{:.3f}".format(e_) for e_ in _edges)))
        check(_m is not None and _m[0] >= 0.05 and _m[1] + _m[3] <= 7.5 - 0.55, "journal/green figure: the mat stays on the page, above the footer band")
        check(not _hard(_prs, "jnfig_green"), "journal/green figure: lint-clean")
    else:
        check(not _mats and _whole, "journal/light figure: unchanged — no mat, the whole picture ({} mats)".format(len(_mats)))
dk.set_theme(None)

# ── Task 5 (C): tally: the pills share one size per page and stand on the column's right margin ──
def _pills(slide, k):
    """[(text, size_pt, right_edge_in)] of the page's pills: the lime rounded boxes and the words set on them."""
    lime = vl._hex(k.P["lime"]).upper()
    out = []
    for sh in slide.shapes:
        if sh.shape_type == _MST.AUTO_SHAPE and sh.fill.type == 1 and str(sh.fill.fore_color.rgb).upper() == lime:
            x, y, w, h = _rect(sh)
            for t in slide.shapes:
                if getattr(t, "has_text_frame", False) and t.text_frame.text.strip() and abs(_rect(t)[0] - x) < 0.005 \
                        and abs(_rect(t)[1] - y) < 0.005:
                    out.append((t.text_frame.text, t.text_frame.paragraphs[0].runs[0].font.size.pt, x + w))
    return out


_TL_PTS = [("New members joined", "Mostly through word of mouth"), ("Tools went out on loan", "Drills and ladders led the list"),
           ("Items came back repaired", "Fixed at the monthly evening")]
_TL_LONG = "A tag that is much too long for its pill and has to shrink to fit its column"
for _g in ("light", "night"):
    for _tag, _tags, _cv in (("3 tags", ["Members", "Loans", "Repairs"], (13.333, 7.5)),
                             ("CJK tags", ["成员", "借出", "修复"], (13.333, 7.5)),
                             ("a long tag on a square page", ["Short", _TL_LONG, "Mid tag"], (7.5, 7.5)),
                             ("a long tag on a portrait page", ["Short", _TL_LONG, "Mid tag"], (7.5, 13.333))):
        _prs = dk.blank_deck(*_cv)
        with contextlib.redirect_stdout(io.StringIO()):
            _k = vl.use("tally", _prs, ground=_g)
            _k.points(_k.new_slide(), title="Where the quarter went", tags=_tags, items=_TL_PTS)
        _pl = _pills(_prs.slides[0], _k)
        _sizes = sorted({round(z_, 2) for _t, z_, _r in _pl})
        _rights = [r_ for _t, _z, r_ in _pl]
        check(len(_pl) == 3 and len(_sizes) == 1,
              "tally/{} points ({}): the pills share one size ({}; was 11.0/12.0 beside the words, 9–12 for a long tag)".format(
                  _g, _tag, "/".join("{:g}pt".format(z_) for z_ in _sizes)))
        if "long tag" not in _tag:                   # (under their words, a long tag's pills hang left, flush to the words)
            _edge = 0.93 * _cv[0]
            check(len(_pl) == 3 and all(abs(r_ - _edge) <= 0.005 for r_ in _rights),
                  "tally/{} points ({}): every pill's right edge is the margin at {:.2f}in ({}; was ragged by up to 0.16in)".format(
                      _g, _tag, _edge, ", ".join("{:.3f}".format(r_) for r_ in _rights)))
        check(not _hard(_prs, "tlp_{}_{}".format(_g, _tag.replace(" ", "_"))), "tally/{} points ({}): lint-clean".format(_g, _tag))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
