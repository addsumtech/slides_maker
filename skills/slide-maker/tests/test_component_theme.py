"""Components inside visual languages (Phase 2a): the theme plumbing, the ordinary-deck byte-identical guard, the
component × language × ground matrix, chart defaults, and the no-literal-colour checker. Prints `N passed, 0 failed`."""
import contextlib, hashlib, io, json, os, re, sys, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk, designed_charts as dc, sigs, visual_languages as vl, lint_deck

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)

from vl_contract import TIER1                      # the 38 (one source: docs, checker, tests)
WORK = Path(tempfile.mkdtemp(prefix="ctheme_")); os.chdir(WORK)


def _build(name, prs, s):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})


def _hash(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p))
    z = zipfile.ZipFile(str(p))
    parts = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    return hashlib.sha256(b"".join(z.read(n) for n in parts)).hexdigest()


def _hard_file(p):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        lint_deck.lint(str(p), static_ok=True)
    return [l.strip()[:150] for l in buf.getvalue().splitlines()
            if re.match(r"\s+slide \d+: [A-Z]", l) and "[warn]" not in l and "[stats]" not in l]


def _hard(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p))
    return _hard_file(p)


# ── theme plumbing ──
_SNAP = dk._state_snapshot()      # the plumbing checks switch palettes; the guard below needs the pristine state
check(hasattr(dk, "THEME") and dk.THEME == {}, "an ordinary deck has an empty THEME")
check(dk._th("card", "FFFFFF") == dk.RGBColor(0xFF, 0xFF, 0xFF), "_th returns the call site's legacy colour when no theme is set")
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("chalkboard", dk.blank_deck(13.333, 7.5))
roles = vl.REGISTRY["chalkboard"]["grounds"]["light"]["roles"]
check(dk.THEME.get("dark") is True and str(dk._th("card", "FFFFFF")) == roles["card"],
      "vl.use fills THEME from the manifest: chalkboard's default ground is dark and its card is the manifest's")
check(set(dk.THEME) >= {"ground", "ink", "mute", "card", "card_ink", "rule", "axis", "track", "on_accent", "highlight",
                        "series", "dark"}, "THEME carries every role ({})".format(sorted(dk.THEME)))
import presets
presets.apply("swiss")
check(dk.THEME == {}, "an ordinary register after a visual language clears THEME (Review Focus 2)")
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("chalkboard", dk.blank_deck(13.333, 7.5))
want_blue = vl.REGISTRY["chalkboard"]["grounds"]["light"]["palette"]["text_accents"][1]
check(str(dk.scorecard.__kwdefaults__["accent"]) == want_blue,
      "after a 1-accent preset, vl.use keeps each colour role its own value (Review Focus 3): {} vs {}".format(
          dk.scorecard.__kwdefaults__["accent"], want_blue))
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("starlit", dk.blank_deck(13.333, 7.5))
dk.blank_deck(13.333, 7.5)
check(dk.THEME == {}, "a new deck starts with no theme: an ordinary deck after a visual-language deck does not inherit it")
presets.apply("swiss"); dk.set_theme(None)
dk._state_restore(_SNAP); dk.set_theme(None)

# ── the ordinary-deck guard: every example, no visual language, byte-identical to the baseline ──
# The baseline was taken from the code BEFORE Phase 2a (76d0cfe), each example from deckkit's pristine state. An example
# that opens a visual language (vl.use) is a language scaffold, not an ordinary deck — and it left its palette behind
# for every later example (`points` did: the first baseline hashed 35 examples in ink's palette).
BASE = json.loads((ROOT / "tests" / "fixtures" / "component_xml_baseline.json").read_text())
CHANGED_ON_PURPOSE = {           # name -> the listed fix that changed it, and the exact hash it draws now
    "agenda": ("2b: the example no longer adds three blank link-target pages (spec §5.6; on poster each one switched "
               "the page field before the agenda was drawn)", "df52779038053f2e1bf355cfde458f37c8ac3c589b6f97a58bc778eb7e2f5f75"),
    "sankey": ("Task 6: each ribbon declares overlap_intent (its end tucks under the node bar on purpose) — names only",
               "a580101c1d4dc22f451c31e0f5bb9eaed53294e63cd00f7ff5da83385ad0aec8"),
}
dk.set_theme(None)
# the hashes were taken with macOS faces: text measured with another platform's faces lays out differently, so the
# guard runs where its baseline was taken (the pre-push local CI) and records a skip elsewhere (ubuntu CI, the sim)
GUARD_HERE = sys.platform == BASE.get("_platform") and not dk._font_substituted("Calibri")
if not GUARD_HERE:
    print("  skip the ordinary-deck guard: baseline taken on {}, this is {} — run it on macOS".format(
        BASE.get("_platform"), sys.platform))
_PRISTINE = dk._state_snapshot()
guarded = 0
for name, want in sorted(BASE.items()):
    if name.startswith("_") or str(want).startswith("BUILD") or not GUARD_HERE:
        continue
    dk._state_restore(_PRISTINE); dk.set_theme(None)
    prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
    try:
        _build(name, prs, s); got = _hash(prs, "base_" + name)
    except Exception as e:
        got = "BUILD {}".format(type(e).__name__)
    guarded += 1
    if name in CHANGED_ON_PURPOSE:
        why, now = CHANGED_ON_PURPOSE[name]
        check(got != want and (now is None or got == now),
              "{}: changed only by its listed fix — {} ({})".format(name, why, got[:12]))
    else:
        check(got == want, "{}: an ordinary deck draws exactly what it drew before Phase 2a{}".format(
            name, "" if got == want else " (changed — not a listed fix)"))
dk._state_restore(_PRISTINE); dk.set_theme(None)
if GUARD_HERE:
    want_n = sum(1 for k, v in BASE.items() if not k.startswith("_") and not str(v).startswith("BUILD"))
    check(guarded == want_n, "the ordinary-deck guard ran {}/{} examples".format(guarded, want_n))

# ── Task 6: the examples and the pre-existing component faults ──
# a slide holding only a native chart is content, not an EMPTY page (the lint missed graphic frames)
prs_c = dk.blank_deck(13.333, 7.5); s_c = dk.add_slide(prs_c)
dk.native_chart(s_c, 1, 1, 6, 3.5, ["Q1", "Q2", "Q3"], [("Revenue", [3, 5, 4])], kind="column")
check(not any("EMPTY" in f for f in _hard(prs_c, "chart_only")), "a slide with only a native chart is not EMPTY")
# the leaderboard example runs on a one-accent language (it indexed dk.ACCENTS[1])
prs_l = dk.blank_deck(13.333, 7.5)
with contextlib.redirect_stdout(io.StringIO()):
    k_l = vl.use("ink", prs_l)
try:
    _build("leaderboard", prs_l, k_l.new_slide()); err = None
except Exception as e:
    err = "{}: {}".format(type(e).__name__, e)
check(err is None, "the leaderboard example builds on a one-accent language ({})".format(err))
# the bento example's ink reads on a dark ground (it hard-coded white on DEEP)
prs_b = dk.blank_deck(13.333, 7.5)
with contextlib.redirect_stdout(io.StringIO()):
    k_b = vl.use("starlit", prs_b)
_build("bento", prs_b, k_b.new_slide())
check(not any("INVISIBLE" in f or "CONTRAST" in f for f in _hard(prs_b, "bento_dark")), "the bento example reads on a dark ground")
# a bento MOSAIC (a two-row hero beside stacked one-row tiles that end level with it) is not "uneven cards";
# two plain side-by-side cards of different heights still are
prs_m = dk.blank_deck(13.333, 7.5); s_m = dk.add_slide(prs_m)
_build("bento", prs_m, s_m)
check(not any("UNEVEN" in f for f in _hard(prs_m, "bento_mosaic")), "a bento mosaic is not flagged as uneven cards")
prs_u = dk.blank_deck(13.333, 7.5); s_u = dk.add_slide(prs_u)
dk.box(s_u, 1.0, 1.0, 3.0, 1.2, fill=dk.TINT); dk.box(s_u, 4.3, 1.0, 3.0, 2.6, fill=dk.TINT)
check(any("UNEVEN" in f for f in _hard(prs_u, "uneven_row")), "two side-by-side cards of different heights are still flagged")
dk.set_theme(None)

# ── every language's content rect (what rs.ground returns, what a placed scaffold fills) lies on the canvas ──
import register_surface as rs
for W, H in ((13.333, 7.5), (7.5, 10.0), (10.0, 5.625)):
    for L in vl.LANGS:
        prs = dk.blank_deck(W, H)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(L, prs)
        x, y, w, h = rs.ground(k.new_slide(), k.name, role="content", index=1)
        check(x >= 0 and y >= 0 and x + w <= W + 1e-6 and y + h <= H + 1e-6 and w > 1 and h > 1,
              "{}x{} {}: rs.ground's content rect is on the canvas ({})".format(
                  W, H, L, tuple(round(v, 2) for v in (x, y, w, h))))
dk.set_theme(None)

# ── the matrix: every Tier-1 component, PLACED in the content rect of every language, no hard lint finding and
# nothing it draws outside that rect — built from `sigs.placed_example`, the scaffold `sigs.py --example X --in L`
# prints. 16:9 and 3:4 on every ground; the format registry's default 10in canvas and 9:16 story on each language's
# first ground. A component that needs a wider rect than a canvas gives raises with the width (sigs.PLACE_MIN_W). ──
RG_LINE = 'x, y, w, h = rs.ground(s, k.name, role="content", index=1)'


def _escapes(slide, n_furn, rect, tol=0.05):
    """What the component drew outside the rect: glyph ink for text, bounds for every other shape. Ornament and
    declared overlaps are furniture, not content."""
    rx, ry, rw, rh = rect
    out = []
    for sh in list(slide.shapes)[n_furn:]:
        nm = str(sh.name)
        if "+decor" in nm.split(":", 1)[0] or nm.startswith("deckkit-decor") or dk._declared_overlap(sh):
            continue
        bb = dk._bbox_in(sh)
        if bb is None:
            continue
        if sh.shape_type == 17 and not sh.text_frame.text.strip():
            continue                                    # an empty text box draws nothing (gantt's "" tick label)
        if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip():
            r = dk._ink_rect(sh, bb)
            if r is None:
                continue
            bx, by, bw, bh = r[0]
        else:
            bx, by, bw, bh = bb
        if bx < rx - tol or bx + bw > rx + rw + tol or by < ry - tol or by + bh > ry + rh + tol:
            out.append("{} '{}' {:.2f}..{:.2f} x {:.2f}..{:.2f} vs rect {:.2f}..{:.2f} x {:.2f}..{:.2f}".format(
                sh.shape_type, (sh.text_frame.text[:12] if getattr(sh, "has_text_frame", False) else ""),
                bx, bx + bw, by, by + bh, rx, rx + rw, ry, ry + rh))
    return out


CANVASES = [((13.333, 7.5), None), ((7.5, 10.0), None), ((10.0, 5.625), "first"), ((5.625, 10.0), "first")]
for (W, H), which in CANVASES:
    for L in vl.LANGS:
        for g in (list(vl.VARIANTS[L])[:1] if which == "first" else vl.VARIANTS[L]):
            prs = dk.blank_deck(W, H)
            first = {}
            for name in TIER1:
                for field in (range(4) if L == "poster" else (None,)):
                    with contextlib.redirect_stdout(io.StringIO()):
                        k0 = vl.use(L, prs, ground=g)
                        while field is not None and len(prs.slides) % 4 != field:
                            k0.new_slide()                # poster: page N takes field N mod 4 — judge every field
                    n0 = len(prs.slides)
                    try:
                        code = sigs.placed_example(name, L, g)
                        head, body = code.split(RG_LINE)
                        ns = {"dk": dk, "dc": dc, "prs": prs}
                        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                            exec(compile(head + RG_LINE, name, "exec"), ns)
                            n_furn = len(ns["s"].shapes)
                            exec(compile(body, name, "exec"), ns)
                    except ValueError as e:
                        if "needs a content rect" in str(e):           # a declared minimum, raised loudly (Focus 3)
                            print("  min  {}x{} {}/{} {}: {}".format(W, H, L, g, name, e))
                            continue
                        check(False, "{}x{} {}/{} {}: builds ({})".format(W, H, L, g, name, e))
                        continue
                    except Exception as e:
                        check(False, "{}x{} {}/{} {}: builds ({}: {})".format(W, H, L, g, name, type(e).__name__,
                                                                              str(e)[:80]))
                        continue
                    first[n0] = name                    # the component's OWN slide (an example may add link targets)
                    esc = _escapes(ns["s"], n_furn, (ns["x"], ns["y"], ns["w"], ns["h"]))
                    check(not esc, "{}x{} {}/{} {}: stays inside the content rect ({})".format(W, H, L, g, name, esc[:1]))
            found = _hard(prs, "m_{}_{}_{}".format(L, g, int(W * 10)))
            by = {}
            for f in found:
                i = int(re.match(r"slide (\d+)", f).group(1)) - 1
                if i in first:                          # judged on its own slide only
                    by.setdefault(first[i], []).append(f)
            for name in TIER1:
                if name in first.values():
                    check(not by.get(name), "{}x{} {}/{} {}: placed, readable, no hard lint finding ({})".format(
                        W, H, L, g, name, by.get(name, [])[:1]))
# the scaffold runs AS PRINTED, in a fresh process — how a non-Claude agent uses it (Review Focus 5)
import subprocess
for name, L in (("timeline", "chalkboard"), ("native_chart", "ink"), ("org_tree", "wayfinding")):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sigs.py"), "--example", name, "--in", L],
                         capture_output=True, text=True).stdout
    pf = WORK / "printed_{}_{}.pptx".format(name, L)
    r = subprocess.run([sys.executable, "-c", out + "\nprs.save({!r})\n".format(str(pf))], capture_output=True,
                       text=True, cwd=str(WORK))
    check(r.returncode == 0 and pf.exists() and not _hard_file(pf),
          "`sigs.py --example {} --in {}` runs as printed with no hard lint finding ({})".format(
              name, L, (r.stderr or "")[-160:] or (_hard_file(pf)[:1] if pf.exists() else "no deck")))
# `--in` on an example it cannot place still prints something that RUNS (it printed a body with no `s`: NameError)
for name, L in (("chip", "ink"), ("back_link", "ink"), ("vl_ink", "ink")):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sigs.py"), "--example", name, "--in", L],
                         capture_output=True, text=True).stdout
    pf = WORK / "printed_unplaced_{}.pptx".format(name)
    r = subprocess.run([sys.executable, "-c", out + "\nprs.save({!r})\n".format(str(pf))], capture_output=True,
                       text=True, cwd=str(WORK))
    check(r.returncode == 0 and pf.exists(), "`sigs.py --example {} --in {}` (not placeable) still runs as printed ({})".format(
        name, L, (r.stderr or "")[-140:]))
# a component given a rect narrower than it needs fails loudly, with the width it needs (Review Focus 3)
saved = dict(sigs.PLACE_MIN_W)
try:
    sigs.PLACE_MIN_W["dumbbell_board"] = sigs.PLACE_MIN_W.get("dumbbell_board", 8.0)
    code = sigs.placed_example("dumbbell_board", "ink").replace(
        'x, y, w, h = rs.ground(s, k.name, role="content", index=1)', "x, y, w, h = 0.5, 1.0, 3.0, 4.0")
    exec(compile(code, "narrow", "exec"), {"dk": dk, "dc": dc, "prs": dk.blank_deck(13.333, 7.5)})
    err = None
except ValueError as e:
    err = str(e)
finally:
    sigs.PLACE_MIN_W.clear(); sigs.PLACE_MIN_W.update(saved)
check(bool(err) and "needs a content rect" in err and "in wide" in err,
      "a too-narrow rect raises with the width it needs ({})".format(err))
dk.set_theme(None)

# §5.6: no example leaves an empty page, run as printed (the plain preamble's `s` included)
for name in ("agenda", "card"):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sigs.py"), "--example", name],
                         capture_output=True, text=True).stdout
    p = WORK / "printed_{}.pptx".format(name)
    r = subprocess.run([sys.executable, "-c", out + "\nprs.save({!r})\n".format(str(p))], capture_output=True, text=True,
                       cwd=str(WORK))
    check(r.returncode == 0 and not [f for f in _hard_file(p) if "EMPTY" in f],
          "`sigs.py --example {}` as printed leaves no empty page ({})".format(name, [f for f in _hard_file(p) if "EMPTY" in f][:1]))

# ── no literal colour in a Tier-1 component body (spec §5.2) ──
import check_component_theme as cct
DK = str(ROOT / "scripts" / "deckkit.py")
check(cct.unknown(DK, cct.TIER1) == [], "every name the checker lists is a top-level deckkit function ({})".format(
    cct.unknown(DK, cct.TIER1)))
check(not [f for f in TIER1 if not hasattr(dk, f) and not hasattr(dc, f)],
      "every matrix component exists in deckkit or designed_charts")
left = [x for x in cct.scan(DK, cct.with_helpers(DK, cct.TIER1)) if (x[0], x[2]) not in cct.ALLOW]
check(left == [], "no Tier-1 component or helper it calls draws a literal colour outside _th / the allowlist ({})".format(left[:4]))
src = ("def leaky(s):\n    box(s, 0, 0, 1, 1, fill=RGBColor(0x12, 0x34, 0x56))\n    text(s, 0, 0, 1, 1, [[('x', 10, '9AA0AE', False, False)]])\n"
       "def comp(s):\n    _helper(s)\n"
       "def _helper(s):\n    box(s, 0, 0, 1, 1, fill=RGBColor(0x65, 0x43, 0x21))\n"
       "def outer(s):\n    def inner():\n        pass\n")
p_ = WORK / "leaky.py"; p_.write_text(src)
check(len(cct.scan(str(p_), ["leaky"])) == 2, "the checker catches an RGBColor and a hex literal")
check(len(cct.scan(str(p_), cct.with_helpers(str(p_), ["comp"]))) == 1, "the checker follows a component into its helpers")
check(cct.unknown(str(p_), ["outer", "inner", "gone"]) == ["gone", "inner"],
      "the checker names a listed function it cannot scan (nested or missing)")

# ── matplotlib charts take the language's series, ground and font (explicit arguments still win) ──
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("tally", dk.blank_deck(13.333, 7.5), ground="night")
check(dc.theme_defaults().get("dark") is True and dc.theme_defaults().get("palette", [None])[0] == "#" + dk.THEME["series"][0],
      "designed_charts defaults follow the active language ({})".format(dc.theme_defaults()))
import matplotlib
seen = {}
_orig_save = dc._save
dc._save = lambda fig, out: seen.setdefault("faces", [t.get_color() for t in fig.findobj(matplotlib.text.Text)][:3]) or _orig_save(fig, out)
try:
    dc.radar(str(WORK / "r.png"), ["a", "b", "c"], [("s", [1, 2, 3])])
finally:
    dc._save = _orig_save
check(seen.get("faces") and all(c.lower() not in ("#1a1a22",) for c in seen["faces"]),
      "a chart on a dark language ground does not draw the light-ground ink ({})".format(seen.get("faces")))
dc.radar(str(WORK / "r2.png"), ["a", "b", "c"], [("s", [1, 2, 3])], palette=["#123456"], dark=False)
check(True, "an explicit palette/dark is accepted while a theme is active (Review Focus 4)")
# a language with ONE series colour must not crash a chart that indexes three (bland_altman, forest_plot): the theme
# palette is padded with the language's own colours (Phase 2b designs four real ones)
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("ink", dk.blank_deck(13.333, 7.5))
for nm in ("bland_altman", "forest_plot", "km_curve", "roc_curve", "waterfall", "marimekko", "distribution", "radar"):
    prs_ = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k_ = vl.use("ink", prs_)
    s_ = k_.new_slide()
    try:
        _build(nm, prs_, s_); err = None
    except Exception as e:
        err = "{}: {}".format(type(e).__name__, e)
    check(err is None, "{} builds on a one-series language ({})".format(nm, err))
dk.set_theme(None)
check(dc.theme_defaults() == {}, "clearing the theme clears the chart defaults")

# ── final-review fixes: every language ground, not one example per language ──
def _on(L, g):
    prs = dk.blank_deck(13.333, 7.5)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(L, prs, ground=g)
    return prs, k


GROUNDS = [(L, g) for L in vl.LANGS for g in vl.VARIANTS[L]]
for L, g in GROUNDS:
    prs, k = _on(L, g)
    ground = dk.THEME["ground"]
    # a chart's series stay tellable apart on a one- or two-colour language (they were cycled: one hue for all)
    pal, _dark, face = dc._theme(None, None, None)
    four = [c.lstrip("#") for c in pal[:4]]
    # the language's own (designed, approved 2026-10-15) colours are held by the contract — ΔE >= 20, 3:1 on ground and
    # card; this RGB-distance / not-grey bar is for the colours theme_series INVENTS beyond them
    designed = {c.upper() for c in dk.THEME["series"]}
    close = [(a, b) for i, a in enumerate(four) for b in four[i + 1:]
             if dk._rgb_dist(a, b) < 60 and not (a in designed and b in designed)]
    faint = [c for c in four if dk.contrast_ratio(c, ground) < 3.0]
    grey = [c for c in four if c not in designed and max(dk._as_rgb(c)) - min(dk._as_rgb(c)) < 30]
    check(len(four) == 4 and not close and not faint and not grey,
          "{}/{}: a chart's first four series are distinct, 3:1 on the ground and not grey ({} close {} faint {} grey {})".format(
              L, g, four, close, faint, grey))
    # chart figures are lining, whatever face the language sets its words in (Georgia's digits bob)
    check(face is None or not dk.has_oldstyle_figures(face),
          "{}/{}: the chart default face has lining figures ({})".format(L, g, face))
    # chart text (ticks, labels, notes) in the language's ink and muted ink, readable on its ground (spec §5.2)
    _plt, c_ink, _grid, c_mute = dc._mpl(_dark)
    check(min(dk.contrast_ratio(c_ink.lstrip("#"), ground), dk.contrast_ratio(c_mute.lstrip("#"), ground)) >= 4.5,
          "{}/{}: chart ink {} and muted {} read on the ground".format(L, g, c_ink, c_mute))
    # native_chart takes the language's series, not its text accents, and keeps three series apart
    s = k.new_slide()
    ch = dk.native_chart(s, 0.6, 1.0, 6.0, 3.2, ["Q1", "Q2", "Q3"], [("a", [3, 5, 4]), ("b", [2, 4, 5]), ("c", [1, 2, 3])],
                         kind="column")
    got = [str(ser.format.fill.fore_color.rgb) for ser in ch.series]
    own = [c.upper() for c in dk.THEME["series"][:3]]
    check(got[:len(own)] == own and len(set(got)) == 3,
          "{}/{}: native_chart's series are the language's own, three apart ({} vs {})".format(L, g, got, own))
    # a regressed dumbbell row (risk red) and the ✓/✕/◐ marks read on every ground
    s = k.new_slide()
    dk.dumbbell_board(s, 0.6, 1.4, 8.8, [("Latency", "p95", 120, 48, 0, 140, "ms"), ("Cost", "per run", 61, 90, 0, 100, "$")],
                      regress=[1])
    s = k.new_slide()
    dk.eval_matrix(s, 0.8, 1.6, 8.4, ["A", "B"], ["speed", "cost", "risk"],
                   [["yes", "no"], ["partial", "yes"], ["no", "maybe"]], mark="mark", recommend=1)
    found = _hard(prs, "fix_{}_{}".format(L, g))
    check(not [f for f in found if f.startswith("slide 2:")],
          "{}/{}: a regressed dumbbell row reads ({})".format(L, g, [f for f in found if f.startswith("slide 2:")][:1]))
    check(not [f for f in found if f.startswith("slide 3:")],
          "{}/{}: eval_matrix's marks read ({})".format(L, g, [f for f in found if f.startswith("slide 3:")][:1]))
# poster changes its field every page: step_list's active step reads on all four, in both orientations
for g in vl.VARIANTS["poster"]:
    for orient in ("vertical", "horizontal"):
        prs, k = _on("poster", g)
        for i in range(4):
            dk.step_list(k.new_slide(), 0.8, 1.0, 8.0, [("Collect", "gather"), ("Train", "fit"), ("Ship", "go")],
                         active_idx=1, orientation=orient)
        found = _hard(prs, "poster_steps_{}_{}".format(g, orient))
        check(not found, "poster/{} step_list ({}) with an active step reads on every field ({})".format(g, orient, found[:1]))
# opening a template starts a deck: the last deck's language does not follow it
prs, k = _on("starlit", "light"); k.new_slide(); prs.save(str(WORK / "tpl.pptx"))
dk.open_template(str(WORK / "tpl.pptx"))
check(dk.THEME == {} and dc._theme(None, None, None) == (None, False, None),
      "open_template starts with no theme ({})".format(sorted(dk.THEME)))
# a state restore (smoke runs examples between snapshots) leaves the chart defaults agreeing with deckkit
snap = dk._state_snapshot()
_on("tally", "night")
dk._state_restore(snap)
check(dc._theme(None, None, None) == (None, False, None),
      "after a state restore the chart defaults follow deckkit's restored theme ({})".format(dc._theme(None, None, None)))
# an explicit palette/dark wins while a dark theme is active (Review Focus 4) — measured on the drawn figure
_on("tally", "night")
seen = {}
dc._save = lambda fig, out: seen.update(
    lines=[l.get_color() for l in fig.findobj(matplotlib.lines.Line2D)],
    texts=[t.get_color() for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip()]) or _orig_save(fig, out)
try:
    dc.radar(str(WORK / "r3.png"), ["a", "b", "c"], [("s", [1, 2, 3])], palette=["#123456"], dark=False)
finally:
    dc._save = _orig_save
check("#123456" in [str(c).lower() for c in seen.get("lines", [])] and "#e8ecf5" not in [str(c).lower() for c in seen.get("texts", [])],
      "an explicit palette and dark=False win over a dark theme (lines {} texts {})".format(
          sorted(set(map(str, seen.get("lines", []))))[:4], sorted(set(map(str, seen.get("texts", []))))[:3]))
dk.set_theme(None)

# ── eval_matrix takes a type size (iPhone 18 explainer, 2026-10-17) ─────────────────────────────────────────────
# Its labels were fixed at 11.5pt and its heads at 12pt — under half the ~18pt a presented 13.3in deck needs, with no
# parameter to raise them, so the deck had to rewrite the runs after the call. `size=` sets the labels; the heads,
# the label column and the marks grow with it; the default keeps every existing deck byte-for-byte.
def _em_runs(size=None):
    prs = dk.blank_deck(13.333, 7.5)
    s = dk.add_slide(prs)
    kw = {} if size is None else {"size": size}
    bottom = dk.eval_matrix(s, 0.67, 1.5, 12.0, ["Gets iOS 27", "Gets Siri AI"],
                            ["iPhone 16 or newer", "iPhone 15 Pro, Pro Max", "Older than iPhone 11"],
                            [["yes", "yes"], ["yes", "yes"], ["no", "no"]], mark="mark", **kw)
    runs = {}
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.text.strip():
                        runs[r.text] = r.font.size.pt if r.font.size is not None else None
    return runs, bottom, s

_r0, _b0, _ = _em_runs()
check(_r0.get("iPhone 16 or newer") == 11.5 and _r0.get("Gets iOS 27") == 12,
      "eval_matrix with no size keeps its 11.5pt labels and 12pt heads ({} / {})".format(
          _r0.get("iPhone 16 or newer"), _r0.get("Gets iOS 27")))
try:
    _em_runs(0)
    check(False, "eval_matrix(size=0) is refused (it drew a grid)")
except ValueError as _e:
    check("size" in str(_e), "eval_matrix(size=0) is refused, naming size= ({})".format(str(_e)[:60]))
_r1, _b1, _s1 = _em_runs(18)
check(_r1.get("iPhone 16 or newer") == 18 and (_r1.get("Gets iOS 27") or 0) >= 18,
      "eval_matrix(size=18) sets 18pt labels and heads at least as large ({} / {})".format(
          _r1.get("iPhone 16 or newer"), _r1.get("Gets iOS 27")))
check(_b1 > _b0, "the larger type takes more height, so the grid's bottom moves down ({:.2f} > {:.2f})".format(_b1, _b0))
_marks = [r.font.size.pt for sh in _s1.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs
          for r in p.runs if r.text in ("✓", "✕", "✔", "✗", "◐") and r.font.size is not None]
check(_marks and min(_marks) >= 18, "the marks grow with the labels ({})".format(sorted(set(_marks))))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
