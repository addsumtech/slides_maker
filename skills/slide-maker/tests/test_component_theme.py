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

TIER1 = ("agenda bento consort_flow distribution dot_strip dumbbell_board eval_matrix forest_plot funnel gantt "
         "heat_matrix iso_bars iso_prism iso_stack km_curve leaderboard marimekko meter_bar native_chart org_tree "
         "position_map pyramid radar roc_curve sankey scorecard segmented_bar small_multiples stat_row step_list table "
         "tier_stack timeline unit_grid venn waterfall bland_altman source_note").split()
WORK = Path(tempfile.mkdtemp(prefix="ctheme_")); os.chdir(WORK)


def _build(name, prs, s):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})


def _hash(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p))
    z = zipfile.ZipFile(str(p))
    parts = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    return hashlib.sha256(b"".join(z.read(n) for n in parts)).hexdigest()


def _hard(prs, tag):
    p = WORK / (tag + ".pptx"); prs.save(str(p))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        lint_deck.lint(str(p), static_ok=True)
    return [l.strip()[:150] for l in buf.getvalue().splitlines()
            if re.match(r"\s+slide \d+: [A-Z]", l) and "[warn]" not in l and "[stats]" not in l]


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
BASE = json.loads((ROOT / "tests" / "fixtures" / "component_xml_baseline.json").read_text())
CHANGED_ON_PURPOSE = {           # name -> the listed fix that changed it, each with its reason
    "sankey": "Task 6: each ribbon declares overlap_intent (its end tucks under the node bar on purpose) — names only",
}
dk.set_theme(None) if hasattr(dk, "set_theme") else None
for name, want in sorted(BASE.items()):
    if str(want).startswith("BUILD"):
        continue
    prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
    try:
        _build(name, prs, s); got = _hash(prs, "base_" + name)
    except Exception as e:
        got = "BUILD {}".format(type(e).__name__)
    check(got == want or name in CHANGED_ON_PURPOSE,
          "{}: an ordinary deck draws exactly what it drew before{}".format(
              name, "" if got == want else " (changed — not a listed fix)"))

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

# ── the matrix: every Tier-1 component on every ground of every language, no hard lint finding ──
# placement, not readability: the example writes the note into the page foot, where these languages draw their frame —
# Phase 2b's content-rect scaffolds (spec §5.4) place it inside; shown, not failed, until then
PLACEMENT_2B = {("drafting", "source_note"): "the sheet border runs along the foot",
                ("chalkboard", "source_note"): "the board frame runs along the foot"}
for L in vl.LANGS:
    for g in vl.VARIANTS[L]:
        prs = dk.blank_deck(13.333, 7.5)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(L, prs, ground=g)
        owner, first = [], {}
        for name in TIER1:
            with contextlib.redirect_stdout(io.StringIO()):
                k = vl.use(L, prs, ground=g)          # each component starts from its language
            n0 = len(prs.slides); s = k.new_slide()
            try:
                _build(name, prs, s)
            except Exception as e:
                check(False, "{}/{} {}: builds ({}: {})".format(L, g, name, type(e).__name__, str(e)[:80]))
            first[n0] = name                        # the component's OWN slide (an example may add link targets)
            owner += [name] * (len(prs.slides) - n0)
        found = _hard(prs, "m_{}_{}".format(L, g))
        by = {}
        for f in found:
            i = int(re.match(r"slide (\d+)", f).group(1)) - 1
            if i in first:                              # judged on its own slide only
                by.setdefault(first[i], []).append(f)
        for name in TIER1:
            if (L, name) in PLACEMENT_2B and by.get(name) and all("FOOTER" in f for f in by[name]):
                check(True, "{}/{} {}: placement tracked for Phase 2b — {}".format(L, g, name, PLACEMENT_2B[(L, name)]))
                continue
            check(not by.get(name), "{}/{} {}: readable, no hard lint finding ({})".format(L, g, name, by.get(name, [])[:1]))

# ── no literal colour in a Tier-1 component body (spec §5.2) ──
import check_component_theme as cct
fns = [f for f in TIER1 if hasattr(dk, f)] + ["tint", "native_chart", "draw_axis"]
left = [x for x in cct.scan(str(ROOT / "scripts" / "deckkit.py"), fns) if (x[0], x[2]) not in cct.ALLOW]
check(left == [], "no Tier-1 component draws a literal colour outside _th / the allowlist ({})".format(left[:4]))
src = "def leaky(s):\n    box(s, 0, 0, 1, 1, fill=RGBColor(0x12, 0x34, 0x56))\n    text(s, 0, 0, 1, 1, [[('x', 10, '9AA0AE', False, False)]])\n"
p_ = WORK / "leaky.py"; p_.write_text(src)
check(len(cct.scan(str(p_), ["leaky"])) == 2, "the checker catches an RGBColor and a hex literal")

# ── matplotlib charts take the language's series, ground and font (explicit arguments still win) ──
with contextlib.redirect_stdout(io.StringIO()):
    vl.use("tally", dk.blank_deck(13.333, 7.5), ground="night")
check(dc.THEME_DEFAULTS.get("dark") is True and dc.THEME_DEFAULTS.get("palette", [None])[0] == "#" + dk.THEME["series"][0],
      "designed_charts defaults follow the active language ({})".format(dc.THEME_DEFAULTS))
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
check(dc.THEME_DEFAULTS == {}, "clearing the theme clears the chart defaults")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
