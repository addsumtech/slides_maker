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

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
