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
    {"name": "Editorial", "bg": "#FCFAF5", "ink": "#1A1A1A", "accent": "#B0451F",
     "font_display": "Georgia, serif", "font_body": "'Helvetica Neue', Arial, sans-serif",
     "cover": "low-left", "skeleton": "rail"},
    {"name": "Swiss", "bg": "#FFFFFF", "ink": "#111111", "accent": "#D6002A",
     "font_display": "'Helvetica Neue', sans-serif", "font_body": "'Helvetica Neue', sans-serif",
     "cover": "full-bleed-type", "skeleton": "split"},
    {"name": "Night", "bg": "#0E1420", "ink": "#EAEEF5", "accent": "#4FD1C5",
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
    {"name": "Brand Light", "bg": "#FFFFFF", "ink": "#111111", "accent": "#0057B8",
     "font_display": "Georgia, serif", "font_body": "Arial, sans-serif",
     "cover": "low-left", "skeleton": "rail"},
    {"name": "Brand Dark", "bg": "#0B1020", "ink": "#F0F3F8", "accent": "#0057B8",
     "font_display": "'Helvetica Neue', sans-serif", "font_body": "'Helvetica Neue', sans-serif",
     "cover": "full-bleed-type", "skeleton": "island"},
]


def _run_div(dirs, d):
    p = os.path.join(d, "dirs.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dirs, f)
    r = subprocess.run([sys.executable, os.path.join(HERE, "directions_diversity.py"), p],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    with tempfile.TemporaryDirectory() as d:
        def _diverse_passes():
            rc, out = _run_div(DIVERSE, d)
            assert rc == 0, "a genuinely divergent set was flagged:\n" + out
        ok("diversity: three divergent directions pass", _diverse_passes)

        def _collapsed_flagged():
            rc, out = _run_div(COLLAPSED, d)
            assert rc == 2, "two colourways of one idea were NOT flagged:\n" + out
            assert "TOO SIMILAR" in out and "REDIVERGE" in out, "no actionable message: " + out
            # and it must never auto-kill — the justification escape has to be offered
            assert "record the reason" in out, "the named-justification escape is missing"
        ok("diversity: two skins of one idea are flagged (and not auto-killed)", _collapsed_flagged)

        def _brand_lock_redirects():
            rc, out = _run_div(BRAND_LOCKED, d)
            assert rc == 0, ("a brand-locked pair that diverged on composition+type was flagged — "
                             "constraint must RELOCATE variance, not forbid it:\n" + out)
        ok("diversity: brand-locked accent passes when composition+type diverge", _brand_lock_redirects)

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

    print("smoke_directions: {} failure(s)".format(len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
