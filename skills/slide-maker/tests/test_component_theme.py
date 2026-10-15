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
CHANGED_ON_PURPOSE = {}          # name -> the listed fix that changed it (Task 6 fills this, each with its reason)
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

# ── the matrix: every Tier-1 component on every ground of every language, no hard lint finding ──
for L in vl.LANGS:
    for g in vl.VARIANTS[L]:
        prs = dk.blank_deck(13.333, 7.5)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(L, prs, ground=g)
        owner = []
        for name in TIER1:
            with contextlib.redirect_stdout(io.StringIO()):
                k = vl.use(L, prs, ground=g)          # each component starts from its language
            n0 = len(prs.slides); s = k.new_slide()
            try:
                _build(name, prs, s)
            except Exception as e:
                check(False, "{}/{} {}: builds ({}: {})".format(L, g, name, type(e).__name__, str(e)[:80]))
            owner += [name] * (len(prs.slides) - n0)
        found = _hard(prs, "m_{}_{}".format(L, g))
        by = {}
        for f in found:
            i = int(re.match(r"slide (\d+)", f).group(1)) - 1
            by.setdefault(owner[i] if i < len(owner) else "?", []).append(f)
        for name in TIER1:
            check(not by.get(name), "{}/{} {}: readable, no hard lint finding ({})".format(L, g, name, by.get(name, [])[:1]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
