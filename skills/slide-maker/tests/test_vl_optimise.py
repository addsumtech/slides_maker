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

# ── Task 5 (D): interface: data / quote tail / points / window bar / dark bezel — measured on the built shapes ──
def _in(v):
    return v / 914400.0


def _texts(slide):
    return [sh for sh in slide.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]


def _by_text(slide, t):
    return [sh for sh in _texts(slide) if sh.text_frame.text.strip() == t]


def _top_size(sh):
    return max((r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size), default=0.0)


def _fill_hex(sh):
    try:
        return str(sh.fill.fore_color.rgb)
    except Exception:
        return None


def _line_hex(sh):
    try:
        return str(sh.line.color.rgb)
    except Exception:
        return None


def _cross(a, b):
    """True when the two shapes' rects overlap."""
    return (a.left < b.left + b.width and b.left < a.left + a.width and a.top < b.top + b.height
            and b.top < a.top + a.height)


UI_PICK = lambda L_: _deck("interface", L_)      # noqa: E731

# data: the label under the number; the bar names the fill's end (the number) and its right end (the total)
for g, num, tot in (("light", "12", "40"), ("dark", "12", "40"), ("light", "39", "40"), ("light", "40", "40")):
    prs, k = UI_PICK(g)
    sl = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()):
        k.data(sl, number=num, label="of {} teams switched".format(tot), total=tot)
    big = max(_by_text(sl, num), key=_top_size)
    lab = _by_text(sl, "of {} teams switched".format(tot))[0]
    tag = "interface/{} data {} of {}".format(g, num, tot)
    if (num, tot) == ("12", "40"):
        check(_in(lab.top) >= _in(big.top) + _in(big.height) - 0.02,
              "{}: the label sits BELOW the number (label top {:.2f}in, number bottom {:.2f}in)".format(
                  tag, _in(lab.top), _in(big.top) + _in(big.height)))
    bars = sorted([sh for sh in sl.shapes if sh.shape_type == 1 and abs(_in(sh.height) - 0.16) < 0.01 and _in(sh.width) > 2],
                  key=lambda sh: -sh.width)
    check(len(bars) >= 1, "{}: a progress bar is drawn".format(tag))
    if not bars:
        continue
    trk, fill = bars[0], bars[-1]
    ends = [(num, _in(fill.left + fill.width)), (tot, _in(trk.left + trk.width))]
    under = [sh for sh in _texts(sl) if _top_size(sh) < 40 and sh.top >= trk.top + trk.height - 9144
             and sh.text_frame.text.strip() in (num, tot)]           # the labels printed under the bar
    check(len(under) == 2, "{}: both ends of the bar are labelled ({} labels under it)".format(tag, len(under)))
    if (num, tot) == ("12", "40") and len(under) == 2:             # a share well clear of both edges
        for words, edge in ends:
            lb = next(sh for sh in under if sh.text_frame.text.strip() == words)
            right = _in(lb.left + lb.width) - 0.028
            check(abs(right - edge) <= 0.08, "{}: '{}' labels its end of the bar ({:.2f}in vs the bar's {:.2f}in)".format(
                tag, words, right, edge))
    if len(under) == 2:
        check(not _cross(under[0], under[1]), "{}: the two bar labels do not overlap".format(tag))
dk.set_theme(None)

# quote: the bubble has a real tail (a triangle protruding from its edge), its outline >= 1.5:1 against card and ground
for g in ("light", "dark"):
    prs, k = UI_PICK(g)
    sl = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()):
        k.quote(sl, quote="We stopped asking where the request lived. It was just there.", attribution="Priya, operations lead")
    panel, ground = k.P["panel"], k.P["ground"]
    body = max([sh for sh in sl.shapes if sh.shape_type == 1 and _fill_hex(sh) == panel], key=lambda sh: sh.width * sh.height)
    tails = [sh for sh in sl.shapes if sh.shape_type == 5 and _line_hex(sh)]
    check(len(tails) >= 1, "interface/{} quote: the bubble draws its tail".format(g))
    if tails:
        t = tails[0]
        out = _in(body.left) - _in(t.left)
        c1, c2 = vl._contrast(_line_hex(t), panel), vl._contrast(_line_hex(t), ground)
        check(out >= 0.15 and _in(t.height) >= 0.2,
              "interface/{} quote: the tail protrudes {:.2f}in from the bubble's edge, {:.2f}in tall".format(g, out, _in(t.height)))
        check(c1 >= 1.5 and c2 >= 1.5,
              "interface/{} quote: the tail's edge reads {:.2f}:1 against the card and {:.2f}:1 against the ground".format(g, c1, c2))
        cb = vl._contrast(_line_hex(body), panel)
        check(cb >= 1.5 and _line_hex(body) == _line_hex(t),
              "interface/{} quote: the bubble's outline matches the tail's ({:.2f}:1 against the card)".format(g, cb))
dk.set_theme(None)

# points: with 4 items a head is never set smaller than its 20pt badge numeral
P4 = [("Approvals first", "One gate before anything ships."), ("One source of truth", "Every team reads the same list."),
      ("A weekly digest", "Monday morning, in your inbox."), ("Quiet hours", "Nothing pings after six.")]
for g in ("light", "dark"):
    for tag, items, kw, size in (("16:9", P4, {}, (13.333, 7.5)), ("16:9 heads only", [(h, None) for h, _l in P4], {}, (13.333, 7.5)),
                                 ("4:3", P4, {}, (10.0, 7.5)), ("with tags", P4, {"tags": ["New", "On", "Beta", "Off"]}, (13.333, 7.5))):
        prs = dk.blank_deck(*size)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use("interface", prs, ground=g)
            sl = k.new_slide()
            k.points(sl, title="Four settings", items=items, **kw)
        heads = [_top_size(sh) for sh in _texts(sl) if sh.text_frame.text.strip() in [h for h, _l in P4]]
        badge = [_top_size(sh) for sh in _texts(sl) if sh.text_frame.text.strip() in ("1", "2", "3", "4")]
        check(len(heads) == 4 and min(heads) >= 20 - 1e-6 and min(heads) >= max(badge or [0]) - 1e-6,
              "interface/{} points x4 ({}): heads hold >= 20pt and the badge numeral ({:.1f}pt vs {:.1f}pt)".format(
                  g, tag, min(heads or [0]), max(badge or [0])))
dk.set_theme(None)

# …and long copy that cannot hold 20pt in the first layout moves to a roomier one (two columns) instead of shrinking
LONG4 = [(h + " and then some more words to make it long", ln + " " + ln) for h, ln in
         (("Approvals first, always, before shipping", "One gate before anything ships to a customer, reviewed by two people."),
          ("One source of truth for every team", "Every team reads the same list and nobody keeps a private spreadsheet."),
          ("A weekly digest on Monday morning", "Monday morning, in your inbox, with what changed and who changed it."),
          ("Quiet hours after six in the evening", "Nothing pings after six unless somebody marks the request as urgent."))]
for n in (3, 4):
    prs, k = UI_PICK("light")
    sl = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()):
        k.points(sl, title="Settings", items=LONG4[:n])
    heads = [_top_size(sh) for sh in _texts(sl) if any(sh.text_frame.text.strip().startswith(h[:18]) for h, _l in LONG4[:n])]
    check(len(heads) == n and min(heads) >= 20 - 1e-6,
          "interface points x{} with long copy: the heads hold >= 20pt in a roomier layout ({:.1f}pt)".format(n, min(heads or [0])))
dk.set_theme(None)

# window: no crumb= and no status= -> no header strip (the window stays); given, the strip is drawn
def _window_of(slide):
    shapes = [sh for sh in slide.shapes if sh.shape_type == 1]      # a window's drop edge is drawn first, same size
    return max(reversed(shapes), key=lambda sh: sh.width * sh.height, default=None)


def _strip(slide):
    """The window's header hairline: as wide as the window itself (a row hairline starts inside its padding)."""
    win = _window_of(slide)
    return [sh for sh in slide.shapes if sh.shape_type == 1 and 0.008 < _in(sh.height) < 0.016
            and abs(sh.left - win.left) < 9144 and abs(sh.width - win.width) < 9144]


for page, kw in (("cover", dict(kicker="Product tour", title="One board for every request")),
                 ("section", dict(number="02", kicker="Part two", title="Setting it up")),
                 ("points", dict(title="Three settings", items=["Approvals first", "One source of truth", "A weekly digest"]))):
    for extra, want in (({}, False), ({"crumb": "Launch › Setup"}, True), ({"status": ("Live", "on")}, True)):
        prs, k = UI_PICK("light")
        sl = k.new_slide()
        with contextlib.redirect_stdout(io.StringIO()):
            getattr(k, page)(sl, **kw, **extra)
        win = _window_of(sl)
        check(bool(_strip(sl)) == want and win is not None and _in(win.width) > 8,
              "interface {} {}: the window {} its header strip".format(page, sorted(extra) or "(no crumb, no status)",
                                                                         "keeps" if want else "drops"))
dk.set_theme(None)

# image_text: the phone bezel on the dark ground is dark with a hairline, not the near-white ink; light is unchanged
for g in ("light", "dark"):
    prs, k = UI_PICK(g)
    sl = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()):
        k.image_text(sl, kicker="Inside the app", title="Requests land in one inbox",
                     body="Every request from every channel arrives in the same list.", caption="The inbox view",
                     image=str(vl.ASSETS / "photo/hall-repair.jpg"))
    bez = max([sh for sh in sl.shapes if sh.shape_type == 1], key=lambda sh: sh.width * sh.height)
    fh = _fill_hex(bez)
    share = _in(bez.width) * _in(bez.height) / (13.333 * 7.5)
    if g == "dark":
        check(vl._lum(fh) < 0.06 and _line_hex(bez) is not None,
              "interface/dark image_text: the bezel is dark ({} luminance {:.2f}, {:.0%} of the page) with a hairline ({})".format(
                  fh, vl._lum(fh), share, _line_hex(bez)))
    else:
        check(fh == k.P["ink"] and _line_hex(bez) is None,
              "interface/light image_text: the bezel is the ink colour, unchanged ({})".format(fh))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
