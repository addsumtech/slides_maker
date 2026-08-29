#!/usr/bin/env python3
"""Regression for the DIRECTION GATE's divergence machinery.

Two things must hold or the gate is ceremony:
  1. `archetypes_html.py` renders each direction's declared COMPOSITION — if the cover/skeleton
     fields don't move the ink, three directions are three colourways of one layout;
  2. `directions_diversity.py` flags a collapsed pair and clears a genuinely divergent one,
     INCLUDING the brand-locked case (shared accent, divergence relocated to composition+type).

Run: python3 smoke_directions.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []


def ok(label, fn):
    try:
        fn()
        print("  ok   " + label)
    except AssertionError as e:
        FAILS.append(label)
        print("  FAIL " + label + " — " + str(e))
    except Exception as e:                                        # noqa: BLE001
        FAILS.append(label)
        print("  ERR  " + label + " — {}: {}".format(type(e).__name__, e))


DIVERSE = [
    # preset-driven directions carry a `dna` marker (as preset_directions() stamps), so they are
    # REAL STYLES, not motif-less colourways — the accurate representation of a preset slot.
    {"name": "Editorial", "bg": "#FCFAF5", "ink": "#1A1A1A", "accent": "#B0451F", "dna": "editorial_paper",
     "font_display": "Georgia, serif", "font_body": "'Helvetica Neue', Arial, sans-serif",
     "cover": "low-left", "skeleton": "rail"},
    {"name": "Swiss", "bg": "#FFFFFF", "ink": "#111111", "accent": "#D6002A", "dna": "swiss",
     "font_display": "'Helvetica Neue', sans-serif", "font_body": "'Helvetica Neue', sans-serif",
     "cover": "full-bleed-type", "skeleton": "split"},
    {"name": "Night", "bg": "#0E1420", "ink": "#EAEEF5", "accent": "#4FD1C5", "dna": "dark_tech",
     "font_display": "'Trebuchet MS', sans-serif", "font_body": "'Helvetica Neue', sans-serif",
     "cover": "split-vertical", "skeleton": "band"},
]
COLLAPSED = [
    {"name": "Warm Paper", "bg": "#FCFAF5", "ink": "#1A1A1A", "accent": "#B0451F",
     "font_display": "Georgia, serif", "font_body": "'Helvetica Neue', sans-serif"},
    {"name": "Cream Editorial", "bg": "#FBF8F2", "ink": "#141414", "accent": "#A8471E",
     "font_display": "'Times New Roman', serif", "font_body": "Arial, sans-serif"},
]
BRAND_LOCKED = [
    {"name": "Brand Light", "bg": "#FFFFFF", "ink": "#111111", "accent": "#0057B8", "dna": "consulting",
     "font_display": "Georgia, serif", "font_body": "Arial, sans-serif",
     "cover": "low-left", "skeleton": "rail"},
    {"name": "Brand Dark", "bg": "#0B1020", "ink": "#F0F3F8", "accent": "#0057B8", "dna": "blueprint",
     "font_display": "'Helvetica Neue', sans-serif", "font_body": "'Helvetica Neue', sans-serif",
     "cover": "full-bleed-type", "skeleton": "island"},
]


def _run_div(dirs, d):
    p = os.path.join(d, "dirs.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dirs, f)
    # UTF-8 forced on the child: this output is machine-read, not displayed. Inheriting the
    # console code page makes these assertions fail under a legacy page — the child's
    # safe_stdio() replaces what it cannot encode, and the parser then cannot find it.
    r = subprocess.run([sys.executable, os.path.join(HERE, "directions_diversity.py"), p],
                       capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, r.stdout + r.stderr


def _flagged(dirs, d):
    """DIVERGENCE only. The process exit code is shared with the bespoke gate, so asserting on
    it here would make these tests fail for a reason they are not about."""
    p = os.path.join(d, "dirs.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dirs, f)
    r = subprocess.run([sys.executable, os.path.join(HERE, "directions_diversity.py"), p, "--json"],
                       capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return json.loads(r.stdout)


def main():
    with tempfile.TemporaryDirectory() as d:
        def _diverse_passes():
            j = _flagged(DIVERSE, d)
            assert not j["flagged"], "a genuinely divergent set was flagged:\n" + json.dumps(j)[:400]
        ok("diversity: three divergent directions pass", _diverse_passes)

        def _collapsed_flagged():
            rc, out = _run_div(COLLAPSED, d)
            assert rc == 2, "two colourways of one idea were NOT flagged:\n" + out
            assert "TOO SIMILAR" in out and "REDIVERGE" in out, "no actionable message: " + out
            # and it must never auto-kill — the justification escape has to be offered
            assert "record the reason" in out, "the named-justification escape is missing"
        ok("diversity: two skins of one idea are flagged (and not auto-killed)", _collapsed_flagged)

        def _brand_lock_redirects():
            j = _flagged(BRAND_LOCKED, d)
            assert not j["flagged"], ("a brand-locked pair that diverged on composition+type was "
                                      "flagged — constraint must RELOCATE variance, not forbid "
                                      "it:\n" + json.dumps(j)[:400])
        ok("diversity: brand-locked accent passes when composition+type diverge", _brand_lock_redirects)

        def _bespoke_required():
            j = _flagged(DIVERSE, d)          # DIVERSE is preset-only by construction
            assert j["no_bespoke"], "a preset-only set must fail the bespoke gate"
            rc, out = _run_div(DIVERSE, d)
            assert rc == 2, "a preset-only set must exit 2"
            assert "NO BESPOKE DIRECTION" in out, "no actionable message: " + out
            assert "ESCAPE" in out and "record why" in out, \
                "the hard gate ships without its named escape — those get routed around"
            withb = list(DIVERSE) + [{"name": "Invented", "cover_motif": "<div/>",
                                      "ambient_motif": "<i/>"}]
            j2 = _flagged(withb, d)
            assert not j2["no_bespoke"] and j2["bespoke"] == ["Invented"], \
                "one bespoke candidate must satisfy the gate: " + json.dumps(j2)[:300]
        ok("directions: >=1 bespoke register is required, with a named escape", _bespoke_required)

        def _composition_reaches_html():
            sys.path.insert(0, HERE)
            import importlib
            import archetypes_html as ah
            importlib.reload(ah)
            out_html = os.path.join(d, "p.html")
            ah.build_directions_html(DIVERSE, out_html, "T")
            html = open(out_html, encoding="utf-8").read()
            # every declared composition must actually appear as a class on a slide
            for spec in DIVERSE:
                assert 'cov-{}"'.format(spec["cover"]) in html or \
                       'cov-{} '.format(spec["cover"]) in html or \
                       "cov-" + spec["cover"] in html, \
                    "cover '{}' never reached the markup".format(spec["cover"])
                assert "sk-" + spec["skeleton"] in html, \
                    "skeleton '{}' never reached the markup".format(spec["skeleton"])
            # and the CSS must actually define them (a class with no rule moves nothing)
            for spec in DIVERSE:
                assert re.search(r"\.cov-" + re.escape(spec["cover"]) + r"\s*\{", html), \
                    "cover '{}' has a class but NO CSS rule".format(spec["cover"])
                assert re.search(r"\.sk-" + re.escape(spec["skeleton"]) + r"[\s.{]", html), \
                    "skeleton '{}' has a class but NO CSS rule".format(spec["skeleton"])
            # the element/modifier class collision that once collapsed a whole slide
            assert '<div class="sk-rail"' not in html and '<div class="sk-band"' not in html, \
                "an inner element reuses the slide's modifier class — that collapsed the slide once"
        ok("composition tokens reach the markup AND have CSS rules", _composition_reaches_html)

        def _bad_value_is_loud():
            sys.path.insert(0, HERE)
            import archetypes_html as ah
            try:
                ah.build_directions_html([{"name": "X", "cover": "diagonal"}],
                                         os.path.join(d, "b.html"), "T")
                raise AssertionError("an unknown cover value was silently accepted")
            except ValueError:
                pass
        ok("an unknown composition value fails loudly, not silently", _bad_value_is_loud)

        def _sans_serif_generic():
            """'sans-serif' CONTAINS 'serif' — a bare generic stack once scored as a SERIF deck,
            making two all-sans directions look more different on the type axis than they are."""
            sys.path.insert(0, HERE)
            from directions_diversity import _face_class
            assert _face_class("sans-serif") == "sans", "bare 'sans-serif' misclassified"
            assert _face_class("Arial, sans-serif") == "sans"
            assert _face_class("Georgia, serif") == "serif"
            assert _face_class("Menlo, monospace") == "mono"
        ok("type classifier: 'sans-serif' is sans, not serif", _sans_serif_generic)

        def _shared_vocabulary():
            """A typo'd composition used to PASS the diversity check (scoring as a divergent
            composition) and only fail later in the renderer — so a collapsed set could earn a
            divergence credit from a value that does not exist."""
            sys.path.insert(0, HERE)
            from directions_diversity import check as dcheck
            try:
                dcheck([{"name": "A", "cover": "diagnoal"}, {"name": "B"}])
                raise AssertionError("a misspelled cover passed the diversity check")
            except ValueError:
                pass
            import archetypes_html as ah
            from directions_diversity import _COVERS, _SKELETONS
            assert set(_COVERS) == set(ah._COVERS) and set(_SKELETONS) == set(ah._SKELETONS), \
                "the two scripts' composition vocabularies have drifted apart"
        ok("both scripts share ONE composition vocabulary", _shared_vocabulary)

        def _callout_not_inside_body():
            """.callout/.ftr are position:absolute against the SLIDE. If .sk-body wraps them, any
            positioning on the body steals them and the callout floats into the bullet list."""
            sys.path.insert(0, HERE)
            import archetypes_html as ah
            html = ah.build_directions_html(DIVERSE, os.path.join(d, "c.html"), "T") and \
                open(os.path.join(d, "c.html"), encoding="utf-8").read()
            body_start = html.index('<div class="sk-body">')
            body_end = html.index("</div>", body_start)
            assert 'class="callout' not in html[body_start:body_end], \
                "the callout is inside .sk-body again — it will float out of place"
        ok("the callout is a sibling of .sk-body, not a descendant", _callout_not_inside_body)

        def _prose_and_script_agree():
            """The lens's counterexample: two light directions, near palettes, same type class,
            but different DENSITY and different COMPOSITION — the prose rule blesses this pair
            (differs on 2 of its 4 axes), so the script must too. Before unification the script
            did not measure density and double-counted mode+palette, flagging it."""
            sys.path.insert(0, HERE)
            import importlib, directions_diversity as dd
            importlib.reload(dd)
            pair = [
                {"name": "L1", "bg": "#FCFAF5", "accent": "#B0451F", "density": "minimal",
                 "font_display": "Georgia, serif", "font_body": "Arial, sans-serif",
                 "cover": "low-left", "skeleton": "rail"},
                {"name": "L2", "bg": "#FBF8F2", "accent": "#A8471E", "density": "dense",
                 "font_display": "'Times New Roman', serif", "font_body": "Arial, sans-serif",
                 "cover": "full-bleed-type", "skeleton": "band"},
            ]
            r = dd.check(pair)
            assert not r["flagged"], (
                "density+composition divergence must satisfy the >=2-axis rule, matched: "
                + str(r["pairs"][0]["matched_axes"]))
            # and a true collapse (same density too) still flags
            pair[1]["density"] = "minimal"; pair[1]["cover"] = "low-left"; pair[1]["skeleton"] = "rail"
            assert dd.check(pair)["flagged"], "a 3-axis match must still flag"
        ok("script axes == prose axes (density measured, mode folded into palette)", _prose_and_script_agree)

        def _preset_directions_carry_dna():
            """The direction gate must offer STYLES, not colour schemes: preset_directions() turns
            preset names into tokens that carry each preset's real DNA, and _dna_cover renders the
            signature motif — the whole point of the preset-driven gate."""
            sys.path.insert(0, HERE)
            import importlib, archetypes_html as ah
            importlib.reload(ah)
            dirs = ah.preset_directions(["swiss", "ink_wash", "memphis"])
            assert len(dirs) == 3 and all(d.get("dna") for d in dirs), "every preset direction carries a dna marker"
            # each renders its signature motif on the cover
            assert 'dna-ghost' in ah._dna_cover(ah._norm(dirs[0])), "swiss ghost numeral missing"
            assert 'dna-seal' in ah._dna_cover(ah._norm(dirs[1])), "ink_wash seal missing"
            assert 'dna-memphis' in ah._dna_cover(ah._norm(dirs[2])), "memphis motif missing"
            # a plain (no-dna) direction renders no motif
            assert ah._dna_cover(ah._norm({"name": "Plain"})) == "", "a dna-less direction must render nothing"
            # the whole page builds and mentions each style name
            import tempfile, os
            out = os.path.join(d, "gate.html")
            ah.build_directions_html(dirs, out, "T")
            html = open(out, encoding="utf-8").read()
            assert "Swiss" in html and "Ink Wash" in html and "Memphis" in html
        ok("preset_directions carry real DNA (styles, not colour schemes)", _preset_directions_carry_dna)

        def _style_runs_through_all_slides():
            """The chosen style must carry through ALL pages, not just the cover (the "只有首尾页"
            failure the user flagged). Every interior archetype slide (content, diagram, results)
            carries the preset's ambient register signature (dna-amb-<preset>)."""
            sys.path.insert(0, HERE)
            import importlib, archetypes_html as ah, os
            importlib.reload(ah)
            for name in ("swiss", "terminal", "blueprint", "memphis", "ink_wash"):
                S = ah._norm(ah.preset_directions([name])[0])
                marker = "dna-amb-" + name
                for fn in (ah._slide_bullets, ah._slide_diagram, ah._slide_data):
                    assert marker in fn(S), "{}: {} missing ambient DNA".format(name, fn.__name__)
            # a pure colour-scheme direction (no dna) carries NO ambient motif — its consistency is
            # palette+type, which run deck-wide anyway; this is the no-AI gate's 4th option.
            col = {"name": "Signal", "accent": "#4C86FF", "cover": "centred", "skeleton": "split"}
            dirs = ah.preset_directions(["swiss", "blueprint", "terminal", col])
            assert len(dirs) == 4 and dirs[3]["name"] == "Signal" and not dirs[3].get("dna"), \
                "a dict passes through as a colour-scheme direction (4th option, no dna)"
            Sc = ah._norm(dirs[3])
            assert "dna-amb-" not in ah._slide_diagram(Sc), "colour direction must carry no ambient motif"
        ok("style runs through ALL slides (ambient register) + colour 4th option", _style_runs_through_all_slides)

        def _bespoke_register_is_first_class():
            """A bespoke register invented for the content (not one of the 18 presets) must render its
            OWN real DNA in the preview — a first-class peer of a preset, not a motif-less colourway —
            so the preset-driven gate never demotes agent-invented bold design (的大胆设计能力)."""
            sys.path.insert(0, HERE)
            import importlib, archetypes_html as ah
            importlib.reload(ah)
            bespoke = {"name": "Sonar", "accent": "#35E0C9", "cover": "low-left", "skeleton": "island",
                       "cover_motif": '<div class="ping" style="border:2px solid #35E0C9"></div>',
                       "ambient_motif": '<span class="ping-echo" style="border:1px solid #35E0C9"></span>'}
            S = ah._norm(bespoke)
            # its own hero motif on the cover (wins over the empty dna switch)
            assert "ping" in ah._dna_cover(S), "bespoke cover_motif must render on the cover"
            # its quiet echo on EVERY interior slide
            for fn in (ah._slide_bullets, ah._slide_diagram, ah._slide_data):
                html = fn(S)
                assert "dna-amb-custom" in html and "ping-echo" in html, \
                    "bespoke ambient_motif must render on " + fn.__name__
            # it mixes into a preset_directions call and the whole page builds
            import os
            out = os.path.join(d, "bespoke.html")
            ah.build_directions_html(ah.preset_directions([bespoke, "swiss"]), out, "T")
            assert "Sonar" in open(out, encoding="utf-8").read()
        ok("bespoke register is first-class in the gate (renders its own DNA)", _bespoke_register_is_first_class)

        def _colourway_excess_flagged():
            """The STRUCTURE gate: at most ONE motif-less colourway (the branch-(c) colour-scheme
            option). Several bare colourways pass every PAIRWISE divergence test yet are exactly the
            'the options were just different colours' failure — so a set of 3 plain colourways + 1
            bespoke (the real regression that shipped) must flag, and a proper 3-styled + 1-colour-
            scheme set must clear."""
            sys.path.insert(0, HERE)
            import importlib, directions_diversity as dd
            importlib.reload(dd)
            # 3 motif-less colourways (no dna, no motif) + 1 bespoke — the mediocre set that shipped
            under = [
                {"name": "Signal", "bg": "#0E1116", "accent": "#E82127", "cover": "centred", "skeleton": "island"},
                {"name": "Ledger", "bg": "#FBF9F4", "accent": "#C4271D", "font_display": "Georgia, serif",
                 "cover": "low-left", "skeleton": "rail"},
                {"name": "Steel", "bg": "#EEF1F4", "accent": "#E4231F", "font_display": "'Arial Black', sans-serif",
                 "cover": "full-bleed-type", "skeleton": "band"},
                {"name": "Bespoke", "bg": "#101018", "accent": "#31D0E6", "cover": "split-vertical",
                 "skeleton": "split", "cover_motif": "<div/>", "ambient_motif": "<i/>"},
            ]
            r = dd.check(under)
            assert r["colourway_excess"] == ["Ledger", "Steel"], \
                "the two colourways beyond the allowed one must be named: " + str(r["colourway_excess"])
            rc, out = _run_div(under, d)
            assert rc == 2, "an under-designed set (3 colourways) must exit 2:\n" + out
            assert "UNDER-DESIGNED SET" in out and "preset_directions" in out, "no actionable message: " + out
            assert "record why" in out, "the named-justification escape is missing"
            # a PROPER set: 3 styled (preset dna and/or bespoke) + exactly 1 colour-scheme option
            proper = [
                {"name": "Blueprint", "bg": "#0A1B38", "accent": "#46C9E0", "dna": "blueprint",
                 "cover": "split-vertical", "skeleton": "band"},
                {"name": "Report", "bg": "#0E0E12", "accent": "#E8434A", "dna": "editorial_report",
                 "font_display": "Georgia, serif", "cover": "low-left", "skeleton": "rail"},
                {"name": "Current", "bg": "#101018", "accent": "#31D0E6", "cover": "centred",
                 "skeleton": "island", "cover_motif": "<div/>", "ambient_motif": "<i/>"},
                {"name": "Signal — palette", "bg": "#FFFFFF", "accent": "#D6002A",
                 "cover": "full-bleed-type", "skeleton": "statement"},   # the ONE allowed colourway
            ]
            rp = dd.check(proper)
            assert rp["colourway_excess"] == [], \
                "a 3-styled + 1-colourway set must NOT flag: " + str(rp["colourway_excess"])
        ok("structure gate: >1 motif-less colourway flags, 3-styled+1-colour passes", _colourway_excess_flagged)

    print("smoke_directions: {} failure(s)".format(len(FAILS)))
    return 1 if FAILS else 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
