"""The skin layer (Phase 2b): vocabulary, manifests, THEME, the four helpers, and that a skin reaches the drawing.
Prints `N passed, 0 failed`."""
import contextlib, io, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk, visual_languages as vl, component_tiers as ct, vl_specs, vl_contract

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)
WORK = Path(tempfile.mkdtemp(prefix="cskin_")); os.chdir(WORK)

def _use(L, g=None, W=13.333, H=7.5):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(L, prs, ground=g) if g else vl.use(L, prs)
    return prs, k

def _names(slide):
    return [sh.name for sh in slide.shapes]

# vocabulary and manifests
check(set(ct.SKIN_VOCAB) == {"card", "rule", "marker", "number"}, "the skin has four roles")
check(all(ct.SKIN_DEFAULT[r] in ct.SKIN_VOCAB[r] for r in ct.SKIN_VOCAB), "each default is in its vocabulary")
check(len(ct.TIER1) == 38 and set(ct.TIER2_SKIN) <= set(ct.TIER1) | {"bento"}, "38 Tier-1, Tier-2 drawn from them")
S = vl_specs.load()
check(all(set(S[n]["skin"]) == set(ct.SKIN_VOCAB) and all(S[n]["skin"][r] in ct.SKIN_VOCAB[r] for r in ct.SKIN_VOCAB)
          for n in S), "every manifest declares a skin value for every role, from the vocabulary")
bad_spec = dict(S["ink"], skin=dict(S["ink"]["skin"], card="velvet"))
check(any("skin" in p and "velvet" in p for p in vl_contract.validate(bad_spec)), "the contract refuses a value outside the vocabulary")
# THEME carries skin and floor; poster's field switch keeps them
prs, k = _use("chalkboard")
check(dk.THEME.get("skin") == S["chalkboard"]["skin"] and dk.THEME.get("floor") == 10, "vl.use puts skin and floor in THEME")
prs, k = _use("poster")
for _ in range(3):
    k.new_slide()
check(dk.THEME.get("skin") == S["poster"]["skin"] and dk.THEME.get("floor"), "poster's per-page field keeps skin and floor (Review Focus 4)")
dk.blank_deck(13.333, 7.5)
check(dk._skin("card") == "filled" and dk._fl(7) == 7, "an ordinary deck: default skin, no floor")
# each helper: the default value calls legacy() and nothing else; every other value draws tagged shapes
for role, values in ct.SKIN_VOCAB.items():
    for v in values:
        prs = dk.blank_deck(13.333, 7.5); s = dk.add_slide(prs)
        dk.set_theme({"ground": "F4EFE6", "ink": "1B1B1B", "mute": "5A5A55", "card": "EAE3D6", "card_ink": "1B1B1B",
                      "rule": "C9C0AE", "axis": "5A5A55", "track": "C9C0AE", "on_accent": "FFFFFF",
                      "highlight": "B23A28", "series": ["B23A28"], "dark": False,
                      "skin": dict(ct.SKIN_DEFAULT, **{role: v}), "floor": 9})
        called = []
        legacy = lambda: called.append(1) or dk.box(s, 1, 1, 1, 1, fill=dk.TINT)
        if role == "card":
            surf = dk._skin_card(s, 1, 1, 2, 1, fill=dk.RGBColor(0xB2, 0x3A, 0x28), legacy=legacy)
            check(isinstance(surf, dk.RGBColor), "card {} returns the surface colour".format(v))
        elif role == "rule":
            dk._skin_rule(s, (1, 1), (3, 1), color=dk.RGBColor(0x5A, 0x5A, 0x55), width=1.0, legacy=legacy)
        elif role == "marker":
            dk._skin_marker(s, 2, 2, 0.42, "3", fill=dk.RGBColor(0xB2, 0x3A, 0x28), ink=dk.RGBColor(0xFF, 0xFF, 0xFF),
                            size=14, legacy=legacy)
        else:
            continue
        if v == ct.SKIN_DEFAULT[role]:
            check(called == [1] and len(s.shapes) == 1, "{} {}: the default draws exactly the call site's own shape".format(role, v))
        else:
            check(called == [] and any(dk.SKIN_TAG + role + ":" + v in n for n in _names(s)),
                  "{} {}: draws its own shapes, tagged ({})".format(role, v, _names(s)[:3]))
dk.set_theme(None)
# number: display/mono pick a lining face; a CJK numeral keeps a face that has it (Review Focus 2)
dk.set_theme({"ground": "F4EFE6", "ink": "1B1B1B", "mute": "5A5A55", "card": "EAE3D6", "card_ink": "1B1B1B",
              "rule": "C9C0AE", "axis": "5A5A55", "track": "C9C0AE", "on_accent": "FFFFFF", "highlight": "B23A28",
              "series": ["B23A28"], "dark": False, "skin": dict(ct.SKIN_DEFAULT, number="display"), "floor": 9})
f = dk._skin_number_face("42", None)
check(f is not None and not dk.has_oldstyle_figures(f), "a display number skin gives digits a lining face ({})".format(f))
check(dk._skin_number_face("三", "PingFang SC") == "PingFang SC", "a CJK numeral keeps the caller's face (Review Focus 2)")
dk.set_theme(None)

# ── the skin reaches the drawing: a Tier-2 component under its language's skin draws differently from the same call
# under the default skin, whenever the language picks a non-default value for a role the component draws ──
import sigs, designed_charts as dc
from lxml import etree
# where the example does not draw every role the component routes, a call that does (the example's step_list is
# vertical; only the horizontal form draws connectors)
EXERCISE = {"step_list": 'dk.step_list(s, 0.8, 3.6, 8.0, [("Collect", "gather"), ("Train", "fit"), ("Ship", "go")], '
                         'orientation="horizontal", active_idx=1)',
            "pyramid": 'dk.pyramid(s, 7.4, 1.0, 5.0, 3.0, ["Vision", "Strategy", "Execution"], labels="side")',
            "gantt": 'dk.gantt(s, 0.6, 4.6, 8.8, [("Plan", 0, 4)], axis_min=0, axis_max=10, ticks=[0, 5, 10])',
            "heat_matrix": 'dk.heat_matrix(s, 7.6, 1.4, 5.0, 2.4, [[1, 2], [3, 4]], ["a", "b"], ["c", "d"], '
                           'cell_labels=True)'}
def _xml_of(L, name, skin):
    prs, k = _use(L)
    dk.set_theme(dict(dk.THEME, skin=skin))
    s = k.new_slide()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(sigs.EXAMPLES[name] + "\n" + EXERCISE.get(name, ""), name, "exec"),
             {"dk": dk, "dc": dc, "s": s, "prs": prs})
    charts = [etree.tostring(sh.chart._chartSpace).decode() for sh in s.shapes if getattr(sh, "has_chart", False)]
    return etree.tostring(s._element).decode() + "".join(charts)       # a chart lives in its own part
def _number_face(L, v):
    _use(L)
    return dk.numeral_face(dk.DISPLAY if v == "display" else dk.MONO)
# each role a language sets differently from the default must change what the component draws — unless it is a
# number face the component already sets its numerals in (cutpaper's display face IS its body face; agenda's
# numerals are mono already), which is checked, not assumed
DONE = ("step_list", "timeline", "agenda", "stat_row", "org_tree", "tier_stack", "funnel", "pyramid", "venn",
        "meter_bar", "gantt", "bento", "table", "native_chart", "heat_matrix")
for name in DONE:
    for L in vl.LANGS:
        sk = S[L]["skin"]
        for r in [r for r in ct.TIER2_SKIN[name] if sk[r] != ct.SKIN_DEFAULT[r]]:
            x_def = _xml_of(L, name, dict(ct.SKIN_DEFAULT))
            x_one = _xml_of(L, name, dict(ct.SKIN_DEFAULT, **{r: sk[r]}))
            same_face = r == "number" and 'typeface="{}"'.format(_number_face(L, sk[r])) in x_def
            check(x_one != x_def or same_face, "{} wears {}'s {} skin ({}){}".format(
                name, L, r, sk[r], " — already that face" if same_face and x_one == x_def else ""))
# CJK step numerals under a display number skin keep the face they had (Review Focus 2) — a Latin numeral face has
# no 壹/贰; compared with the same call under the default skin, not with "is the font installed"
def _cjk_faces(skin):
    prs, k = _use("ink")
    dk.set_theme(dict(dk.THEME, skin=skin))
    s = k.new_slide()
    dk.step_list(s, 0.8, 1.0, 8.0, [("採茶", "春分"), ("製茶", "穀雨")], numeral_style="cjk")
    nums = (dk.cjk_numeral(1), dk.cjk_numeral(2))
    return [r.font.name for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs
            if r.text.strip() in nums]
got, base = _cjk_faces(S["ink"]["skin"]), _cjk_faces(dict(ct.SKIN_DEFAULT))
check(len(got) == 2 and got == base, "step_list's CJK numerals keep their face under a display number skin ({} vs {})".format(got, base))
dk.set_theme(None)

# an explicit accent under a line-only card skin: the node text is chosen against the ground the skin leaves
# (Review Focus 1)
import lint_deck, re
prs, k = _use("ink")
s = k.new_slide()
dk.org_tree(s, 0.8, 1.2, 8.0, 3.0, ("CEO", [("Eng", []), ("Ops", [])]), accent=dk.RGBColor(0x1F, 0x3B, 0xFF))
prs.save(str(WORK / "org_ink.pptx")); buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
    lint_deck.lint(str(WORK / "org_ink.pptx"), static_ok=True)
hard = [l for l in buf.getvalue().splitlines() if re.match(r"\s+slide \d+: (LOW CONTRAST|INVISIBLE)", l)]
check(not hard, "org_tree with an explicit accent reads under a hairline card skin ({})".format(hard[:1]))
dk.set_theme(None)

# a dashed rule skin reaches the table's XML borders and the chart's gridlines
prs, k = _use("drafting")
s = k.new_slide()
dk.table(s, 0.8, 1.2, 8.0, [["Part", "Qty"], ["Bolt", "12"], ["Nut", "40"]], numeric_cols=[1])
s2 = k.new_slide()
dk.native_chart(s2, 0.6, 1.0, 6.0, 3.2, ["Q1", "Q2"], [("a", [3, 5])], kind="column")
from lxml import etree
x_tbl = etree.tostring(s._element).decode()
x_cht = etree.tostring(s2.shapes[-1].chart._chartSpace).decode()
check('prstDash val="dash"' in x_tbl, "drafting's dashed rule reaches the table borders")
check('prstDash val="dash"' in x_cht, "drafting's dashed rule reaches the chart gridlines")
dk.set_theme(None)

# no component draws text below its language's floor (spec §5.2) — on every language
import component_tiers as _ct2
for L in vl.LANGS:
    prs, k = _use(L)
    low = []
    for name in _ct2.TIER1:
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(L, prs)
        s = k.new_slide()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(sigs.EXAMPLES[name], name, "exec"), {"dk": dk, "dc": dc, "s": s, "prs": prs})
        for sh in s.shapes:
            if sh.has_text_frame:
                low += [(name, r.font.size.pt, r.text[:10]) for p in sh.text_frame.paragraphs for r in p.runs
                        if r.font.size and r.text.strip() and r.font.size.pt < dk.THEME["floor"] - 1e-6]
    check(not low, "{}: no component text under the floor {} ({})".format(L, dk.THEME["floor"], low[:3]))
dk.set_theme(None)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
