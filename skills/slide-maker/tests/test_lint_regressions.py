#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Two-sided regression test for the render-time lint.

Every check here exists because a REAL deck shipped the defect, or because a real deck was
falsely flagged for craft. The two directions matter equally and are asserted separately:

  PASS deck — ordinary, correctly-built slides plus two DECLARED exceptions (a rhymed triptych,
              a quiet pause page). Zero hard findings. A change that breaks one of these is
              catching craft rather than defects, which is how a rule set makes decks worse.
  FAIL deck — one slide per defect the gates must catch. Each was clean before these checks
              existed; that was the bug.

Run:  python3 tests/test_lint_regressions.py
"""
import os, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def lint(pptx, renders):
    r = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(pptx),
                        "--renders", str(renders), "--static"],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


def _require_deps():
    """A missing dependency must read as a missing dependency.

    This suite imports deckkit and RENDERS, so it needs python-pptx, Pillow, matplotlib and
    LibreOffice. It was originally wired into CI ABOVE `pip install -r requirements.txt` and
    every run since died on a bare ModuleNotFoundError traceback inside a subprocess — which
    looks exactly like a lint regression and is not one. Fail with a sentence instead.
    """
    missing = []
    for mod, why in (("pptx", "python-pptx"), ("PIL", "Pillow"), ("matplotlib", "matplotlib")):
        try:
            __import__(mod)
        except ImportError:
            missing.append(why)
    if missing:
        print("SKIPPED: this suite needs %s — install requirements.txt BEFORE running it "
              "(in CI, this step must come after the dependency install)." % ", ".join(missing))
        sys.exit(0)
    if not shutil.which("soffice") and not os.path.exists(
            "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        print("SKIPPED: LibreOffice (soffice) not found — this suite renders decks.")
        sys.exit(0)


def main():
    _require_deps()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="lintfx-"))
    subprocess.run([sys.executable, str(HERE / "lint_fixture.py")], cwd=tmp, check=True,
                   capture_output=True)
    for d in ("fx_pass", "fx_fail", "fx_align_pass", "fx_align_fail"):
        subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"),
                        str(tmp / f"{d}.pptx"), str(tmp / f"{d}_render")],
                       cwd=tmp, capture_output=True)

    ok, bad = [], []

    def ran(out, label):
        """A token's ABSENCE only means 'suppressed' if the lint actually ran. Without this the
        harness reads a crash as two passing waivers — the same read-silence-as-success mistake
        the checks below exist to catch."""
        if "layout finding(s)" not in out:
            bad.append(f"{label}: lint did not complete, so no assertion below is meaningful:\n"
                       + out.strip()[:400])
            return False
        return True

    # A crashed check must never read as a passed check. The per-slide statistics used to be
    # wrapped in `except Exception: pass`, so one refactor that deleted a local variable took
    # TEXT WALL, LAYOUT SAMENESS, UNDERFILLED and FLAT RHYTHM off every deck while the report
    # still printed "✓ clean" — caught here only by luck, because two of those had tokens
    # asserted below. This asserts the machinery itself, on every deck the suite touches.
    p_out = lint(tmp / "fx_pass.pptx", tmp / "fx_pass_render")
    if not ran(p_out, "PASS deck"):
        print("\n".join("  FAIL " + b for b in bad)); return 1
    if "0 layout finding(s)" in p_out:
        ok.append("PASS deck has zero hard findings")
    else:
        bad.append("PASS deck gained a hard finding — a change is flagging craft, not a defect:\n"
                   + "\n".join(l for l in p_out.splitlines() if ": " in l and "[warn]" not in l))
    # the two DECLARED exceptions must actually be honoured
    if "LAYOUT SAMENESS" in p_out:
        bad.append("declared design_intent(rhyme=) did not suppress LAYOUT SAMENESS — a deliberate "
                   "triptych is being flagged as sameness, and the documented waiver is dead again")
    else:
        ok.append("declared rhyme suppresses LAYOUT SAMENESS")
    if "UNDERFILLED" in p_out:
        bad.append("declared design_intent(envelope=) did not suppress UNDERFILLED — the "
                   "deliberately quiet page cannot be built clean")
    else:
        ok.append("declared quiet envelope suppresses UNDERFILLED")

    f_out = lint(tmp / "fx_fail.pptx", tmp / "fx_fail_render")
    if not ran(f_out, "FAIL deck"):
        print("\n".join("  FAIL " + b for b in bad)); return 1
    for token, what in [
        ("under 3:1, the floor for text at ANY size", "text below the absolute contrast floor is caught"),
        ("RULE THROUGH TEXT", "a hairline painted over type is caught"),
        ("OCCLUSION", "a panel painted over a sentence is caught"),
        ("LAYOUT SAMENESS", "UNdeclared sameness is still flagged (the waiver is not a blanket)"),
        ("UNDERFILLED", "an UNdeclared thin page is still flagged"),
        # The three paint-order faults a PER-SHAPE threshold cannot see. Each shipped on a real
        # deck with the gate reporting clean. Asserted on their own text so a generic finding
        # elsewhere in the deck cannot stand in for them.
        ("OCCLUSION: 'COMPOSITE TILES",
         "150 tiles hiding a caption are caught (union coverage, not one shape at a time)"),
        ("RULE THROUGH TEXT: a", "a rule assembled from 40 dashes is caught like a solid one"),
        ("TEXT NOT VISIBLE: 'an opaque picture over l",
         "a PICTURE over one line is caught from the pixels — unknowable from the XML"),
        # A label must sit on the thing it labels. The panels of a composite figure have no
        # shape geometry, so nothing geometric can see this — and the PASS deck carries the
        # same figures captioned correctly, so over-strictness fails there instead.
        # BOTH slides are asserted by number, and that is the point: the ink test has two
        # halves, slide 11 exercises only `var` and slide 12 only `differs from ground`. With a
        # bare "CAPTION NOT ALIGNED" token, deleting the ground half left the suite green while
        # the real defect (flat panels — an MRI/photo strip) went undetected. Verified by
        # mutation: dropping either half now takes one of these two lines away.
    ]:
        (ok if token in f_out else bad).append(
            what if token in f_out else f"FAIL deck: {token} was NOT raised — the check regressed")

    # ── ALIGNMENT pair, in its own decks. A label must sit on the thing it labels; the panels
    # of a composite figure have no shape geometry, so nothing geometric can see this.
    # Both slides are asserted BY NUMBER because the ink test has two halves and each slide
    # exercises exactly one: slide 1's panels vary down their columns, slide 2's are flat and can
    # only be found by differing from the figure's own ground. With a bare "CAPTION NOT ALIGNED"
    # token, deleting the ground half left the suite green while the real defect — flat panels,
    # i.e. every photo and MRI strip — went undetected. Verified by mutation: dropping either
    # half now takes one of these two lines away.
    a_out = lint(tmp / "fx_align_fail.pptx", tmp / "fx_align_fail_render")
    if ran(a_out, "ALIGN-fail deck"):
        for token, what in [
                ("slide 1: CAPTION NOT ALIGNED",
                 "captions on the text grid under INSET panels are caught (varying columns)"),
                ("slide 2: CAPTION NOT ALIGNED",
                 "the same defect on FLAT panels on their own paper is caught (crop ground)")]:
            (ok if token in a_out else bad).append(
                what if token in a_out
                else f"ALIGN deck: {token} was NOT raised — the check regressed")
    ap_out = lint(tmp / "fx_align_pass.pptx", tmp / "fx_align_pass_render")
    if ran(ap_out, "ALIGN-pass deck"):
        if "CAPTION NOT ALIGNED" in ap_out:
            bad.append("ALIGN-pass deck: correctly centred captions were flagged — the check has "
                       "drifted into over-strictness:\n"
                       + "\n".join(l for l in ap_out.splitlines() if "CAPTION" in l))
        else:
            ok.append("correctly centred captions on both panel shapes stay clean")

    for label, out in (("PASS", p_out), ("FAIL", f_out), ("ALIGN-fail", a_out),
                       ("ALIGN-pass", ap_out)):
        if "[BROKEN]" in out:
            bad.append(f"{label} deck: the per-slide statistics CRASHED — checks silently "
                       f"disabled:\n" + "\n".join(l for l in out.splitlines() if "[BROKEN]" in l))
    if not any("[BROKEN]" in o for o in (p_out, f_out, a_out, ap_out)):
        ok.append("per-slide statistics ran on every fixture deck (no silently-disabled checks)")

    # ── the corpus that matters most: the skill's OWN reference deck. A change that adds a hard
    # finding here is a change that would fail the file SKILL.md tells every builder to copy.
    # This is not hypothetical: promoting the 3.0-4.5 contrast band to a hard failure looked
    # obviously right, passed both synthetic fixtures, and hard-failed this deck four times on
    # accent labels at 4.27:1. Synthetic fixtures cannot tell strictness from correctness; a real
    # deck built by the skill's own example can.
    ex = HERE.parent / "references" / "examples" / "build_example_generic.py"
    if ex.is_file():
        import os
        env = dict(os.environ, PYTHONPATH=str(SCRIPTS))
        r = subprocess.run([sys.executable, str(ex)], cwd=tmp, capture_output=True, text=True, env=env)
        demo = None
        for line in (r.stdout + r.stderr).splitlines():
            if "saved ->" in line:
                demo = pathlib.Path(line.split("saved ->")[1].split("|")[0].strip())
        if demo and demo.is_file():
            subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"), str(demo),
                            str(tmp / "ex_render")], cwd=tmp, capture_output=True, env=env)
            e_out = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(demo),
                                    "--renders", str(tmp / "ex_render")],
                                   capture_output=True, text=True, env=env).stdout
            n = next((int(l.split(":")[-1].split("layout")[0].strip())
                      for l in e_out.splitlines() if "layout finding(s)" in l), None)
            BASE = 3          # the example deck's own pre-existing footer overlap on slide 4
            if n is None:
                bad.append("reference example deck: lint did not complete")
            elif n <= BASE:
                ok.append(f"reference example deck holds at {n} hard findings (baseline {BASE})")
            else:
                bad.append(f"reference example deck rose to {n} hard findings (baseline {BASE}) — a "
                           f"change is failing the deck the skill tells builders to copy:\n"
                           + "\n".join(l for l in e_out.splitlines()
                                        if ": " in l and "[warn]" not in l and "[stats]" not in l))
        else:
            bad.append("reference example deck could not be built — the corpus check did not run")

    # ── UNSOURCED NUMBER: two-sided, on its own mini-deck ─────────────────────
    # Built separately on purpose: several assertions above name fx_fail slides BY NUMBER, so
    # appending a slide there would silently re-point them. A check that never fires is worth
    # nothing, and one that fires on a sourced deck is worse than nothing, so both directions
    # are asserted. The recap case is the one that matters most — it is the whole reason this
    # check is deck-level: a closing slide restating a figure sourced on its own page is good
    # practice, and a per-slide test calls it a defect.
    sys.path.insert(0, str(SCRIPTS))
    import deckkit as _dk

    def _prov_deck(dest, *slides):
        prs = _dk.blank_deck(10, 5.625)
        for lines, notes in slides:
            s = prs.slides.add_slide(prs.slide_layouts[6])
            for i, ln in enumerate(lines):
                _dk.text(s, 0.6, 0.8 + i * 0.6, 8.6, 0.5,
                         [[(ln, 18, _dk.DEEP, False, False)]])
            if notes:
                _dk.speaker_notes(s, notes)
        prs.save(str(dest))
        return dest

    def _lint_nr(pptx):
        r = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(pptx), "--static"],
                           capture_output=True, text=True)
        return r.stdout + r.stderr

    o = _lint_nr(_prov_deck(tmp / "prov_bare.pptx", (["Capex reached $400B this year"], None)))
    if "UNSOURCED NUMBER" in o and "$400B" in o:
        ok.append("a novel magnitude with no source anywhere is caught")
    else:
        bad.append("UNSOURCED NUMBER did not fire on a bare unsourced $400B — the check is dead")

    o = _lint_nr(_prov_deck(tmp / "prov_notes.pptx",
                            (["Capex reached $400B this year"], "Source: Crunchbase Q1 2026")))
    if "UNSOURCED NUMBER" in o:
        bad.append("UNSOURCED NUMBER fired although the citation is in the SPEAKER NOTES — a "
                   "presented deck legitimately sources there and must not be flagged")
    else:
        ok.append("a citation in the speaker notes counts as provenance")

    o = _lint_nr(_prov_deck(tmp / "prov_recap.pptx",
                            (["Capex reached $400B", "来源: Crunchbase"], None),
                            (["Takeaway: $400B of capex is the story"], None)))
    if "UNSOURCED NUMBER" in o:
        bad.append("UNSOURCED NUMBER fired on a RECAP slide restating a figure sourced earlier in "
                   "the same deck — this is the false positive the deck-level design exists to "
                   "prevent, and it is back")
    else:
        ok.append("a recap of a figure sourced elsewhere in the deck is not flagged")

    o = _lint_nr(_prov_deck(tmp / "prov_chrome.pptx", (["Part III", "13 / 20", "Section 4"], None)))
    if "UNSOURCED NUMBER" in o:
        bad.append("UNSOURCED NUMBER fired on page chrome ('13 / 20') — bare integers are not "
                   "claims, and counting them is what made the first cut fire on a good deck")
    else:
        ok.append("page numbers and section indices are not treated as claims")

    # ── grouped decks must be SEEN, not silently skipped ──────────────────────
    # _boxes() walked slide.shapes only, so on a deck whose content lives in groups — every
    # designer-tool export, and every deck handed over for redesign — it saw one shape per slide.
    # OVERLAP vanished, OVERFLOW could only name "GROUP ''", and every stat derived from boxes
    # (size clusters, text coverage, halves, skeleton, occupancy) read empty while the report still
    # printed "✓ clean". Measured before the fix: identical content, 11 shapes seen ungrouped vs 1
    # grouped.
    def _grp(dest, build, group=True):
        prs = _dk.blank_deck(10, 5.625)
        s = prs.slides.add_slide(prs.slide_layouts[6])
        build(s)
        if group:
            s.shapes.add_group_shape([x for x in list(s.shapes)])
        prs.save(str(dest))
        return dest

    def _defects(s):
        _dk.text(s, 0.6, 0.4, 8.8, 0.6, [[("Title", 28, _dk.DEEP, True, False)]])
        _dk.box(s, 1.0, 1.2, 3.5, 2.2, fill="C0362C")
        _dk.text(s, 7.6, 4.6, 3.2, 0.5, [[("runs off the right edge", 13, _dk.DEEP, False, False)]])

    import sys as _sys
    _sys.path.insert(0, str(SCRIPTS))
    import lint_deck as _L
    from pptx import Presentation as _P

    a = sorted((round(b["l"], 3), round(b["t"], 3), round(b["w"], 3), round(b["h"], 3))
               for b in _L._boxes(_P(str(_grp(tmp / "g_flat.pptx", _defects, False))).slides[0], 10, 5.625))
    b = sorted((round(x["l"], 3), round(x["t"], 3), round(x["w"], 3), round(x["h"], 3))
               for x in _L._boxes(_P(str(_grp(tmp / "g_grp.pptx", _defects, True))).slides[0], 10, 5.625))
    if a and a == b:
        ok.append("grouped and ungrouped decks yield IDENTICAL geometry (transform applied)")
    else:
        bad.append(f"grouped geometry does not match ungrouped: {len(a)} vs {len(b)} boxes; the "
                   f"group transform (off/ext/chOff/chExt) is wrong or the walk stopped at the group")

    o = _lint_nr(tmp / "g_grp.pptx")
    if "OVERFLOW" in o and "GROUP" not in o.split("OVERFLOW")[1][:40]:
        ok.append("OVERFLOW inside a group names the real shape, not the group")
    else:
        bad.append("OVERFLOW on a grouped deck did not resolve to the offending child shape")

    # A group is an AUTHORED unit: a badge straddling a card corner is layering, not a collision.
    def _composed(s):
        _dk.box(s, 0.8, 1.5, 3.6, 2.2, fill="FFFFFF", line="DDDDDD")
        _dk.box(s, 4.0, 1.32, 1.1, 0.42, fill="C0362C")      # badge over the card's top-right
        _dk.text(s, 4.05, 1.36, 1.0, 0.34, [[("NEW", 10, _dk.WHITE, True, False)]])
    o = _lint_nr(_grp(tmp / "g_composed.pptx", _composed, True))
    if "OVERLAP" in o:
        bad.append("OVERLAP fired INSIDE one group — a group is an authored composition (badge on a "
                   "card, icon on a panel); flagging it makes the check useless on designed decks")
    else:
        ok.append("layering INSIDE one group is not flagged as a collision")

    def _cross(s):
        _dk.box(s, 1.0, 1.6, 3.0, 1.6, fill="F2F4F8")
        _dk.text(s, 1.2, 1.8, 2.6, 0.5, [[("card", 12, _dk.DEEP, False, False)]])
    prs = _dk.blank_deck(10, 5.625)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _cross(s)
    s.shapes.add_group_shape([x for x in list(s.shapes)])
    _dk.box(s, 2.2, 2.4, 3.4, 2.0, fill="C0362C")            # OUTSIDE the group
    prs.save(str(tmp / "g_cross.pptx"))
    if "OVERLAP" in _lint_nr(tmp / "g_cross.pptx"):
        ok.append("a collision ACROSS a group boundary is still caught")
    else:
        bad.append("a shape colliding with a group's contents is no longer caught — the same-group "
                   "exemption has widened past the composed unit it was carved for")

    # An unmappable group must be reported ONCE, and must not take the run down with it. Both of
    # these were live bugs: the stats walks re-traversed the same tree and re-reported every rotated
    # group as "slide ?", and _report_group_skip sorted int slide numbers against that None, raising
    # a TypeError at the very END of lint() — discarding a whole completed run.
    A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    prs = _dk.blank_deck(10, 5.625)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _dk.box(s, 1.0, 1.0, 2.0, 1.0, fill="C0362C")
    g = s.shapes.add_group_shape([x for x in list(s.shapes)])
    g._element.find(f".//{A_NS}xfrm").set("rot", "2700000")
    prs.save(str(tmp / "g_rot.pptx"))
    o = _lint_nr(tmp / "g_rot.pptx")
    n_rot = o.count("rotated/flipped group")
    if n_rot == 1:
        ok.append("an unmappable group is reported exactly once, with its slide number")
    else:
        bad.append(f"the rotated-group skip was printed {n_rot}x (want 1) — the stats walks are "
                   f"re-recording it, which also reintroduces the None-vs-int sort crash")
    if "layout finding(s)" in o and "slide ?" not in o:
        ok.append("lint completes on a deck whose group cannot be mapped")
    else:
        bad.append("lint did not complete cleanly on an unmappable-group deck (or printed 'slide ?')")

    # ── the declared type_scale must actually bind ────────────────────────────
    # render_deck --gate-check requires design_plan.type_scale; nothing compared it to the deck, so
    # a deck could declare {34,24,14}, set 31/22/17 throughout, and pass both gates clean (measured).
    # The rule has to stay narrow: the skill's own 5-slide example uses TWELVE distinct sizes, so
    # "every size must be a declared tier" would fire on correct work and be abandoned immediately.
    import json as _json

    def _scaled(dest, sizes, declared):
        prs = _dk.blank_deck(10, 5.625)
        for i in range(3):
            s = prs.slides.add_slide(prs.slide_layouts[6])
            _dk.text(s, 0.6, 0.5, 8.8, 0.7, [[(f"Title {i+1}", sizes[0], _dk.DEEP, True, False)]])
            _dk.text(s, 0.6, 1.5, 8.8, 0.5, [[("Subhead", sizes[1], _dk.DEEP, False, False)]])
            _dk.text(s, 0.6, 2.3, 8.8, 1.5,
                     [[("Body copy carrying most of this deck's characters by a wide margin.",
                        sizes[2], _dk.MUTE, False, False)]])
        d = dest.parent / dest.stem
        d.mkdir(exist_ok=True)
        out = d / "t.pptx"
        prs.save(str(out))
        if declared:
            (d / ".deck-gates.json").write_text(_json.dumps({"design_plan": {"type_scale": declared}}))
        return out

    o = _lint_nr(_scaled(tmp / "sc_ok.pptx", (34, 24, 14), {"display": 34, "title": 24, "body": 14}))
    if "SCALE DRIFT" in o:
        bad.append("SCALE DRIFT fired on a deck that sets exactly what it declares")
    else:
        ok.append("a deck that honours its declared type scale is silent")

    o = _lint_nr(_scaled(tmp / "sc_drift.pptx", (31, 22, 17), {"display": 34, "title": 24, "body": 14}))
    if "SCALE DRIFT" in o and "body=14" in o:
        ok.append("a deck that declares one scale and sets another is caught")
    else:
        bad.append("SCALE DRIFT missed a deck declaring 34/24/14 while setting 31/22/17 — the "
                   "required field constrains nothing again")

    o = _lint_nr(_scaled(tmp / "sc_none.pptx", (34, 24, 14), None))
    if "SCALE DRIFT" in o:
        bad.append("SCALE DRIFT fired with no .deck-gates.json — it must be silent when nothing "
                   "was declared, or every deck without a gates file gains a warning")
    else:
        ok.append("no declaration means no drift finding")

    # a hero number way off the scale is normal and must not read as drift
    prs = _dk.blank_deck(10, 5.625)
    for i in range(3):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        _dk.text(s, 0.6, 0.5, 8.8, 0.8, [[(f"Title {i+1}", 34, _dk.DEEP, True, False)]])
        _dk.text(s, 0.6, 1.6, 8.8, 0.6, [[("Subhead", 24, _dk.DEEP, False, False)]])
        _dk.text(s, 0.6, 2.4, 8.8, 1.6,
                 [[("Body copy carrying most of the characters in this deck.", 14, _dk.MUTE, False, False)]])
    s = prs.slides[1]
    _dk.text(s, 6.6, 3.6, 3.0, 1.2, [[("97%", 96, _dk.DEEP, True, False)]])   # deliberate hero
    d = tmp / "sc_hero"; d.mkdir(exist_ok=True)
    prs.save(str(d / "t.pptx"))
    (d / ".deck-gates.json").write_text(_json.dumps(
        {"design_plan": {"type_scale": {"display": 34, "title": 24, "body": 14}}}))
    if "SCALE DRIFT" in _lint_nr(d / "t.pptx"):
        bad.append("SCALE DRIFT fired on a deliberate off-scale hero number — the check must key on "
                   "the size carrying the TEXT, not on every size present")
    else:
        ok.append("a deliberate off-scale hero number is not drift")

    # A run can INHERIT its size from the layout/theme and report none, so a template-based deck can
    # leave most of its body unmeasurable. Judging "which size carries the most text" from what is
    # left reads a caption as the body: measured, a deck with 1200 inherited characters and one
    # 28-character 9pt caption produced THREE confident findings from those 28 characters.
    prs = _dk.blank_deck(10, 5.625)
    from pptx.util import Inches as _In
    for _i in range(4):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        tb = s.shapes.add_textbox(_In(0.6), _In(1), _In(8.6), _In(2))
        tb.text_frame.text = "Body copy that inherits its size from the theme. " * 6
        _dk.text(s, 0.6, 3.6, 3, 0.4, [[("caption", 9, _dk.MUTE, False, False)]])
    d = tmp / "sc_inherit"; d.mkdir(exist_ok=True)
    prs.save(str(d / "t.pptx"))
    (d / ".deck-gates.json").write_text(_json.dumps(
        {"design_plan": {"type_scale": {"display": 34, "title": 24, "body": 14}}}))
    o = _lint_nr(d / "t.pptx")
    if "SCALE DRIFT NOT CHECKED" in o:
        ok.append("a deck whose type is mostly INHERITED refuses to be judged, and says so")
    elif "SCALE DRIFT" in o:
        bad.append("SCALE DRIFT judged a deck from a thin sample of explicitly-sized text — a "
                   "caption was read as the body, which is a confident wrong finding")
    else:
        bad.append("a deck with unmeasurable type went silent instead of reporting NOT CHECKED — "
                   "silence here is indistinguishable from a pass")

    # ── the APPENDIX run ──────────────────────────────────────────────────────
    # A thesis defense is told to "plan for backup/appendix slides for Q&A", and those are dense ON
    # PURPOSE. Judged as presented content they drew TEXT WALL + CROWDED on every one (measured: 6
    # findings on 3 backup slides), and the trailing run also stole the closing slide's exemption by
    # making a backup slide the last one. Declaring the run must fix both — and must not become a
    # free pass for cramming.
    def _defense(dest, declare):
        prs = _dk.blank_deck(10, 5.625)
        _dk.text(prs.slides.add_slide(prs.slide_layouts[6]), 1, 2, 8, 1,
                 [[("Defense", 34, _dk.DEEP, True, False)]])
        for k in range(2):
            s = prs.slides.add_slide(prs.slide_layouts[6])
            _dk.text(s, 0.6, 0.5, 8.8, 0.6, [[(f"Result {k+1}", 24, _dk.DEEP, True, False)]])
            _dk.text(s, 0.6, 1.5, 8.8, 1.0, [[("One clear finding.", 15, _dk.MUTE, False, False)]])
        s = prs.slides.add_slide(prs.slide_layouts[6])          # the real closer: thin by design
        # >=15 words on purpose: UNDERFILLED only looks at slides carrying real text, so a shorter
        # closer would never exercise the exemption this test exists to check.
        _dk.text(s, 0.6, 1.8, 8.8, 1.2,
                 [[("Contributions: a faithful reconstruction method, validated on three separate "
                    "cohorts, with limitations stated plainly and the code released for reproduction.",
                    18, _dk.DEEP, True, False)]])
        for k in range(3):                                       # dense backup material
            b = prs.slides.add_slide(prs.slide_layouts[6])
            if declare and k == 0:
                _dk.design_intent(b, role="appendix", reason="backup slides for Q&A")
            _dk.text(b, 0.6, 0.4, 8.8, 0.5, [[(f"Backup {k+1}", 20, _dk.DEEP, True, False)]])
            _dk.text(b, 0.6, 1.1, 8.8, 4.0,
                     [[(("Full ablation detail with every hyperparameter, dataset split, random seed "
                         "and per-cohort breakdown, kept off the main line but ready. ") * 4,
                        12, _dk.MUTE, False, False)]])
        prs.save(str(dest))
        return dest

    o = _lint_nr(_defense(tmp / "ap_undeclared.pptx", False))
    if "TEXT WALL" in o and "UNDERFILLED" in o:
        ok.append("an UNDECLARED trailing appendix is still judged as presented content")
    else:
        bad.append("the appendix exemption applies without being declared — it must not be free")

    o = _lint_nr(_defense(tmp / "ap_declared.pptx", True))
    if "TEXT WALL" in o:
        bad.append("dense backup slides still draw TEXT WALL after declaring role='appendix' — "
                   "reference material read on demand is dense on purpose")
    elif "UNDERFILLED" in o:
        bad.append("the closing slide still loses its exemption to a trailing appendix — last_body "
                   "is not being honoured")
    else:
        ok.append("a declared appendix reads at briefing density and gives the closer back its exemption")

    # the exemption RAISES the bar, it does not remove it
    prs = _dk.blank_deck(10, 5.625)
    _dk.text(prs.slides.add_slide(prs.slide_layouts[6]), 1, 2, 8, 1,
             [[("Cover", 34, _dk.DEEP, True, False)]])
    for k in range(2):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        _dk.text(s, 0.6, 0.5, 8.8, 0.6, [[(f"R{k+1}", 24, _dk.DEEP, True, False)]])
        _dk.text(s, 0.6, 1.5, 8.8, 1.0, [[("One finding.", 15, _dk.MUTE, False, False)]])
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _dk.text(s, 0.6, 1.8, 8.8, 1.0, [[("Contributions and limitations owned.", 20, _dk.DEEP, True, False)]])
    b = prs.slides.add_slide(prs.slide_layouts[6])
    _dk.design_intent(b, role="appendix", reason="Q&A")
    _dk.box(b, 0.2, 0.2, 9.6, 5.2, fill="EEF2F7")
    _dk.text(b, 0.3, 0.3, 9.4, 5.0,
             [[(("Freeform cramming with no structure at all. " * 30), 11, _dk.MUTE, False, False)]])
    prs.save(str(tmp / "ap_crammed.pptx"))
    if "TEXT WALL" in _lint_nr(tmp / "ap_crammed.pptx"):
        ok.append("a CRAMMED appendix slide is still caught — the bar rises, it does not vanish")
    else:
        bad.append("role='appendix' silenced a genuinely crammed slide — dense is correct there, "
                   "freeform cramming is not")

    # ── the translucent-overlap exemption must stay NARROW ────────────────────
    # venn()'s circles overlap by definition, so OVERLAP fired on every Venn ever built — a hard
    # gate failing on correct output is worse than no gate, because the author starts working
    # around the linter. The exemption keys on translucency (a gradient fill is this toolkit's only
    # alpha path) PLUS equal size. All four directions are asserted: widening it later would
    # silently switch off the card-on-card collision check, which is the whole point of OVERLAP.
    def _ov(dest, build):
        prs = _dk.blank_deck(10, 5.625)
        build(prs.slides.add_slide(prs.slide_layouts[6]))
        prs.save(str(dest))
        return dest

    def _g(c):
        return [(0.0, c, 0.3), (1.0, c, 0.3)]

    o = _lint_nr(_ov(tmp / "ov_opaque.pptx", lambda s: (
        _dk.box(s, 1.0, 1.0, 3.0, 2.0, fill="C0362C"),
        _dk.box(s, 2.2, 1.6, 3.0, 2.0, fill="1F77C4"))))
    if "OVERLAP" in o:
        ok.append("an OPAQUE same-size partial overlap still fires")
    else:
        bad.append("OVERLAP stopped firing on two opaque same-size cards — the translucency "
                   "exemption has widened into the defect it was carved around")

    o = _lint_nr(_ov(tmp / "ov_venn.pptx", lambda s: _dk.venn(
        s, 0.6, 1.0, 5.0, 3.8, ["A", "B"], zones={"12": "both"})))
    if "OVERLAP" in o:
        bad.append("OVERLAP fired on venn()'s circles — a Venn's regions ARE overlaps, so the gate "
                   "fails correct output and cannot be satisfied")
    else:
        ok.append("venn()'s intentional circle overlap is exempt")

    o = _lint_nr(_ov(tmp / "ov_mismatch.pptx", lambda s: (
        _dk.box(s, 1.0, 1.0, 4.0, 2.6, grad=_g("C0362C")),
        _dk.box(s, 3.6, 2.2, 2.2, 1.4, grad=_g("1F77C4")))))
    if "OVERLAP" in o:
        ok.append("translucent but MISMATCHED sizes still fires (not a set diagram)")
    else:
        bad.append("OVERLAP stopped firing on translucent shapes of different sizes — equal size is "
                   "what makes the exemption a set diagram rather than a stray panel")

    o = _lint_nr(_ov(tmp / "ov_text.pptx", lambda s: (
        _dk.box(s, 1.0, 1.0, 3.0, 2.0, grad=_g("C0362C")),
        _dk.text(s, 1.2, 1.4, 2.6, 0.6, [[("covered sentence", 14, _dk.DEEP, False, False)]]),
        _dk.box(s, 1.0, 1.0, 3.0, 2.0, grad=_g("1F77C4")))))
    if "layout finding(s)" in o:
        ok.append("a translucent pair carrying TEXT is still assessed (exemption needs textless)")
    else:
        bad.append("the lint did not complete on the translucent-plus-text deck")

    # ── text MEASUREMENT must never under-estimate ────────────────────────────
    # macOS ships a whole family as one .ttc, and matplotlib resolves bold and regular to
    # the SAME path; Pillow's truetype(path, size) with no index= then loads face 0, the
    # Regular. Every bold run in such a family was measured at REGULAR width — 3.9% narrow
    # for Helvetica Neue. Under-measuring is the dangerous direction: a measure-then-place
    # guard silently passes and the renderer wraps anyway, which is how a caption sized for
    # one line landed its second line on top of a footer, on a deck the lint called clean.
    sys.path.insert(0, str(SCRIPTS))
    import deckkit as dk
    fams = [f for f in ("Helvetica Neue", "Arial", "Helvetica", "DejaVu Sans")
            if dk._font_file(f, False)]
    if not fams:
        ok.append("font measurement: skipped — no resolvable font on this host")
    for fam in fams:
        probe = "MEASURING WIDTH AT A GIVEN WEIGHT"
        reg = dk._pil_font(fam, 100, False).getlength(probe)
        bld = dk._pil_font(fam, 100, True).getlength(probe)
        if bld < reg:
            bad.append(f"{fam}: bold measures NARROWER than regular ({bld:.0f} < {reg:.0f}) — "
                       f"the bold face was not selected inside the font file")
        else:
            ok.append(f"{fam}: bold measures >= regular ({bld / reg:.3f}x)")
        path = str(dk._font_file(fam, True) or "")
        if path.lower().endswith((".ttc", ".otc")) and dk._face_index(path, True) == 0:
            bad.append(f"{fam} is a font collection but bold still maps to face 0")

    # ── the measurement must agree with the RENDERER, not just with itself ────
    # Every measure-then-place guard in this skill — head()'s title assert, bound()'s caption
    # sizing, `assert measure_text(...) < h`, and _rbox(), which every geometry check is
    # computed against — trusts one number: how wide the renderer will set this string. When
    # that number came back 3.9% narrow for bold text in font-collection families, all of them
    # silently PASSED while text wrapped anyway, and a caption sized for one line put its
    # second line on top of a footer. The checks above cannot see that: they are computed from
    # the same wrong number. So calibrate against the only authority there is — render real
    # strings and measure the ink. Under-measuring is the dangerous direction; over-measuring
    # only costs a little slack, so the bar is one-sided and tight on the side that hurts.
    from PIL import Image
    cal_fonts = [f for f in ("Helvetica Neue", "Arial", "Helvetica", "DejaVu Sans")
                 if dk._font_file(f, False)]
    CASES = [("Measuring width at a given weight", 10, False),
             ("MEASURING WIDTH AT A GIVEN WEIGHT", 10, True),
             ("Neither number tells you how this compares", 13, False),
             ("Both numbers compare one thing to another.", 26, True),
             ("Ask for the comparator.", 48, True),
             ("1,356", 96, True)]
    for fam in cal_fonts[:2]:                       # two families is enough to catch the class
        prs = dk.blank_deck()
        for txt, size, bold in CASES:
            sl = prs.slides.add_slide(prs.slide_layouts[6])
            dk.box(sl, 0, 0, 10, 5.625, fill=dk.WHITE, line=None)
            dk.text(sl, 0.05, 2.2, 9.9, size / 72.0 * 1.6,
                    [[(txt, size, dk.DEEP, bold, False, fam)]], space_after=0, wrap=False)
        mp = tmp / ("cal_%s.pptx" % fam.replace(" ", ""))
        prs.save(str(mp))
        subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"), str(mp),
                        str(tmp / ("cal_%s" % fam.replace(" ", "")))],
                       cwd=tmp, capture_output=True)
        worst = None
        for i, (txt, size, bold) in enumerate(CASES, 1):
            png = tmp / ("cal_%s" % fam.replace(" ", "")) / ("slide%02d.png" % i)
            if not png.is_file():
                continue
            im = Image.open(png).convert("L").point(lambda v: 255 if v < 128 else 0)
            bb = im.getbbox()
            if not bb:
                continue
            rendered = (bb[2] - bb[0]) / (im.width / 10.0)
            measured = dk._pil_font(fam, size, bold).getlength(txt) / dk._MEAS_PREC / 72.0
            if measured <= 0:
                continue
            r = rendered / measured
            if worst is None or r > worst[0]:
                worst = (r, txt, size, bold)
        if worst is None:
            bad.append(f"font measurement vs render: {fam} produced no usable renders")
        elif worst[0] > 1.005:
            bad.append(f"{fam}: the renderer sets text {100*(worst[0]-1):.1f}% WIDER than the "
                       f"measurement predicts (worst: {worst[2]}pt "
                       f"{'bold' if worst[3] else 'regular'}, {worst[1]!r}). Every "
                       f"measure-then-place guard in the skill silently passes when this drifts")
        elif worst[0] < 0.80:
            bad.append(f"{fam}: measurement over-estimates width by more than 20% "
                       f"(ratio {worst[0]:.3f}) — layouts will be needlessly cramped")
        else:
            ok.append(f"{fam}: measurement matches the renderer (worst ratio {worst[0]:.3f}, "
                      f"never under-measures)")

    # ── SHALLOW BAND: the band between DEAD BOTTOM (per-slide, fires under 0.45) and ENVELOPE
    # MONOCULTURE (deck-level, needs bottoms within ±4%). A real 12-page build parked five interior
    # slides at 0.63–0.76 — visibly empty, spread too wide to be monoculture, too full to be dead —
    # and passed every gate. Both shapes are asserted: the one that shipped the defect must fire,
    # and the corrected rebuild of the SAME deck must stay silent, or the check is just a nag.
    sys.path.insert(0, str(SCRIPTS))
    import deckkit as _dk

    def _band_deck(bottoms, path):
        prs = _dk.blank_deck()
        for frac in [1.0] + bottoms + [1.0]:
            s = _dk.add_slide(prs)
            _dk.text(s, 0.6, 0.4, 8.8, 0.6, [[("A title for this slide here", 28,
                                               _dk.RGBColor(0, 0, 0), True, False, "Helvetica Neue")]])
            y, bot = 1.2, frac * 5.625            # ~20+ words so the slide clears the load >= 15 gate
            while y + 0.34 <= bot:
                _dk.text(s, 0.6, y, 8.8, 0.32,
                         [[("body copy line that carries several real words here", 14,
                            _dk.RGBColor(50, 50, 50), False, False, "Helvetica Neue")]], space_after=0)
                y += 0.34
        prs.save(str(path))

    for label, bottoms, want in [
            ("the shipped-defect shape", [0.76, 0.63, 0.68, 0.72, 0.66, 0.95, 0.97, 0.93, 0.96, 0.94], True),
            ("the corrected rebuild",    [0.87, 0.83, 0.89, 0.91, 0.86, 0.93, 0.95, 0.97, 0.90, 0.94], False)]:
        pth = tmp / f"fx_band_{int(want)}.pptx"
        _band_deck(bottoms, pth)
        out = lint(pth, tmp / "no_such_render_dir")
        if not ran(out, f"SHALLOW BAND deck ({label})"):
            continue
        fired = "SHALLOW BAND" in out
        if fired == want:
            ok.append(f"SHALLOW BAND {'fires on' if want else 'is silent on'} {label}")
        elif want:
            bad.append("SHALLOW BAND did not fire on the shape that shipped the defect — five of ten "
                       "interior slides ending at 63–76% of the canvas is invisible again")
        else:
            bad.append("SHALLOW BAND fired on the corrected rebuild — the threshold now flags decks "
                       "that fixed the problem, which makes the finding noise")

    # ── unit_grid's guarantee IS containment: square cells sized to fit w x h with the unit label
    # budgeted in. The first cut derived the cell from w alone, so 34 cells across 8.8in produced a
    # 5.4in-tall grid on a 5.625in canvas and drew five OVERFLOW findings — a form component that
    # can overflow guarantees nothing, which is the whole reason to prefer it over hand-placed boxes.
    ug_bad = 0
    for total in (1, 3, 7, 12, 34, 60, 100, 137, 250, 400):
        for w, h in ((8.8, 3.4), (3.0, 3.0), (9.4, 1.2), (2.0, 4.2), (5.0, 0.9)):
            prs = _dk.blank_deck()
            s = prs.slides.add_slide(prs.slide_layouts[6])
            yb = _dk.unit_grid(s, 0.4, 0.9, w, h, total, "1 = 1")
            cells = [sh for sh in s.shapes if not sh.has_text_frame or not sh.text_frame.text]
            right = max(sh.left / 914400.0 + sh.width / 914400.0 for sh in s.shapes)
            bottom = max(sh.top / 914400.0 + sh.height / 914400.0 for sh in s.shapes)
            if (len(cells) != total or right > 0.4 + w + 0.01
                    or bottom > 0.9 + h + 0.01 or yb > 0.9 + h + 0.01):
                ug_bad += 1
    if ug_bad:
        bad.append(f"unit_grid escaped its region or drew the wrong cell count in {ug_bad} of 50 "
                   f"total/region combinations — the containment guarantee is broken")
    else:
        ok.append("unit_grid: exact cell count, always inside w x h (50 total/region combos)")
    for why, call in [("total <= 0", lambda s: _dk.unit_grid(s, 0.4, 0.9, 5, 2, 0, "1 = 1")),
                      ("a texture, not a count", lambda s: _dk.unit_grid(s, 0.4, 0.9, 5, 2, 9999, "1 = 1")),
                      ("filled out of range", lambda s: _dk.unit_grid(s, 0.4, 0.9, 5, 2, 10, "1 = 1", filled=11)),
                      ("a blank unit label", lambda s: _dk.unit_grid(s, 0.4, 0.9, 5, 2, 34, "  "))]:
        prs = _dk.blank_deck()
        try:
            call(prs.slides.add_slide(prs.slide_layouts[6]))
            bad.append(f"unit_grid accepted {why} — the refusal is decorative")
        except ValueError:
            ok.append(f"unit_grid refuses {why}")

    # ── meter_bar drew the fill at `max(w*frac, h)` so a rounded cap never degenerated. Cosmetic
    # for a 62% progress row; a LIE for a small fraction — measured, frac=0.01 on a 9.7in bar drew
    # 0.46in, 4.7x the true width, and rendered as roughly 7%. A mark that overstates its own value
    # is a fidelity defect, and fidelity is a floor taste does not override.
    from pptx import Presentation as _Pres
    FR = (0.005, 0.01, 0.05, 0.25, 0.62, 1.0)
    prs = _dk.blank_deck()
    s = prs.slides.add_slide(prs.slide_layouts[6])
    for i, f in enumerate(FR):
        _dk.meter_bar(s, 0.6, 0.35 + i * 0.85, 7.4, f, value=f"{f*100:.1f}%",
                      accent=_dk.RGBColor(0xA6, 0x3A, 0x2A), track=_dk.RGBColor(0xDD, 0xD5, 0xC8))
    mb = tmp / "fx_meter.pptx"
    prs.save(str(mb))
    seen, mism = 0, []
    for sh in _Pres(str(mb)).slides[0].shapes:
        try:
            if str(sh.fill.fore_color.rgb) != "A63A2A":
                continue
        except Exception:
            continue
        idx = int(round((sh.top / 914400.0 - 0.35 - 0.34) / 0.85))
        seen += 1
        drawn, true = sh.width / 914400.0, 7.4 * FR[idx]
        if abs(drawn - true) > 0.005:
            mism.append(f"frac={FR[idx]} drew {drawn:.3f}in for a true {true:.3f}in")
    if seen != len(FR):
        bad.append(f"meter_bar fidelity check found {seen} fills, expected {len(FR)} — the probe "
                   f"is not measuring what it thinks it is")
    elif mism:
        bad.append("meter_bar overstates small fractions again: " + "; ".join(mism))
    else:
        ok.append("meter_bar: fill width == frac x track at every fraction incl. 0.5% (no cap floor)")

    # --- Two measurements that could not see what they were measuring. Both shipped, both were
    # --- reproduced here, and each is asserted in BOTH directions because each was wrong in both.

    # (1) ONE definition of "the title". `_find_title` looks for >=14.5pt in the top 28%; the
    # deck-stats scan used to run its own search over the top 20% with no size floor. A title
    # between the two bands was invisible to the stats scan, so the margin chrome above it won —
    # and title_txt feeds the TITLE SPINE that the coordinator and both critic lenses read as the
    # deck's argument. One measured deck presented its argument as three pieces of chrome.
    import deckkit as _dk
    _prs = _dk.blank_deck(10, 5.625)
    for _c, _t in (("FIRES", "The gate reported clean"),
                   ("SILENT", "The lint could not see it"),
                   ("ADVISORY", "Bind the claim to an artifact")):
        _s = _dk.add_slide(_prs)
        _dk.text(_s, 0.5, 0.52, 2.0, 0.3, [[(_c, 9.5, _dk.MUTE, False, False, _dk.FONT)]],
                 space_after=0)
        _dk.text(_s, 0.5, 1.30, 8.5, 0.7, [[(_t, 30, _dk.DEEP, False, False, _dk.FONT)]],
                 space_after=0)
        _dk.text(_s, 0.5, 2.40, 8.5, 1.5,
                 [[("Body copy at eighteen point with enough words to form a real body tier.",
                    18, _dk.SLATE, False, False, _dk.FONT)]], space_after=0)
    _prs.save(str(tmp / "fx_title.pptx"))
    _o = lint(tmp / "fx_title.pptx", tmp / "fx_title_render")
    if ran(_o, "title spine"):
        if "1. FIRES" in _o or "1. SILENT" in _o:
            bad.append("the title spine names margin chrome as the deck's argument again — the "
                       "deck-stats scan has stopped deferring to _find_title")
        elif "The gate reported clean" not in _o:
            bad.append("the title spine no longer carries the real 30pt titles: " + _o[:300])
        else:
            ok.append("title spine reads the real titles, not the chrome above them")

    # (2) Text width measured in the face the file actually names. A flat 0.52em per Latin char
    # under-measures uppercase (~0.66em real) and over-measures narrow glyphs and spaces
    # (~0.26em real), so it both MISSED real collisions and INVENTED them. The false positive is
    # the expensive one: on the measured build an author rewrote two correct titles to satisfy it.
    # The BOX WIDTHS below are computed from whatever face this machine actually resolves, not
    # hardcoded. A fixture tuned to macOS Helvetica silently stops discriminating on a CI runner
    # that has neither Helvetica nor Courier and falls everything back to DejaVu Sans — it still
    # passes, while testing nothing. Both error DIRECTIONS survive substitution (measured: caps
    # +17..+22%, narrow -34..-46% across Helvetica Neue / Helvetica / Calibri / DejaVu Sans); only
    # the magnitudes move, so the widths have to move with them.
    import lint_deck as _L
    _F = _dk.FONT
    _caps = "MEASUREMENT THAT CANNOT SEE THE FACE IS NOT MEASUREMENT"
    _flat_caps = len(_caps) * (26 / 72.0) * 0.52
    _real_caps = _L._text_w(_caps, 26, _F, True)
    _w_caps = (_flat_caps + _real_caps) / 2.0      # flat says it fits; the real face says it wraps
    # Place the body BETWEEN the one-line and two-line bottoms, using the linter's own line height
    # (_est_lines x size/72 x 1.25 for non-CJK). Then the flat estimate — which believes the title
    # fits on one line — sees clear space, and the real face, which wraps it to two, sees a
    # collision. That is the discrimination; a body parked well below both would pass either way.
    _lh = (26 / 72.0) * 1.25
    _prs = _dk.blank_deck(10, 5.625); _s = _dk.add_slide(_prs)
    _dk.text(_s, 0.5, 1.0, _w_caps, 0.55,
             [[(_caps, 26, _dk.DEEP, True, False, _F)]], space_after=0)
    _dk.text(_s, 0.5, 1.0 + 1.5 * _lh, _w_caps, 1.2,
             [[("The body sits directly beneath and the caps title wraps into it.", 16,
                _dk.SLATE, False, False, _F)]], space_after=0)
    _prs.save(str(tmp / "fx_caps.pptx"))
    _o = lint(tmp / "fx_caps.pptx", tmp / "fx_caps_render")
    if ran(_o, "caps collision"):
        if "COLLISION" in _o:
            ok.append("an ALL-CAPS title that really does collide is caught (was invisible under "
                      "the flat 0.52em estimate)")
        else:
            bad.append("ALL-CAPS under-measurement is back: a real collision reads clean")

    _narrow = "illicit if it fits, it fits"
    _flat_n = len(_narrow) * (26 / 72.0) * 0.52
    _real_n = _L._text_w(_narrow, 26, _F, False)
    _w_narrow = (_real_n + _flat_n) / 2.0          # the real face fits on one line; flat says wrap
    _prs = _dk.blank_deck(10, 5.625); _s = _dk.add_slide(_prs)
    _dk.text(_s, 0.5, 1.0, _w_narrow, 0.42,
             [[(_narrow, 26, _dk.DEEP, False, False, _F)]], space_after=0)
    _dk.text(_s, 0.5, 1.5, 6.0, 1.0,
             [[("Body copy immediately beneath the single-line title.", 16, _dk.SLATE,
                False, False, _F)]], space_after=0)
    _prs.save(str(tmp / "fx_narrow.pptx"))
    _o = lint(tmp / "fx_narrow.pptx", tmp / "fx_narrow_render")
    if ran(_o, "narrow-glyph false positive"):
        if "COLLISION" in _o:
            bad.append("narrow-glyph over-measurement is back: a title that fits on one line is "
                       "reported as colliding, which is what made an author rewrite correct titles")
        else:
            ok.append("narrow glyphs and spaces no longer invent a collision (0.26em real vs "
                      "0.52em assumed)")

    # ---- a MIXED-SIZE paragraph that fits on one line must not invent an overlap -------------
    # _ink_rect used to collapse every run to the paragraph's LARGEST size and measure the whole
    # string at it, so "257万1,037" at 38pt followed by " 人 · 在日外国劳动者" at 10.5pt scored as
    # ~3 lines of 38pt and "collided" with the block below. Measured on one real deck: 7 of the
    # first 20 build-time criticals were this, every one of them a phantom.
    _big, _small = "257万1,037", " 人 · 在日外国劳动者"
    _true_w = (_L._text_w(_big, 38, _F, True) + _L._text_w(_small, 10.5, _F, False))
    _box_w = _true_w + 0.45                        # comfortably fits at the RUNS' own sizes...
    _flat_w = _L._text_w(_big + _small, 38, _F, True)
    _prs = _dk.blank_deck(10, 5.625); _s = _dk.add_slide(_prs)
    _dk.text(_s, 0.5, 1.0, _box_w, 0.62,
             [[(_big, 38, _dk.DEEP, True, False, _F),
               (_small, 10.5, _dk.SLATE, False, False, _F)]], space_after=0)
    _dk.text(_s, 0.5, 1.72, _box_w, 0.9,
             [[("The block that the phantom third line used to collide with.", 14,
                _dk.SLATE, False, False, _F)]], space_after=0)
    # Asserts against lint_layout (BUILD time). The gate must STILL FIRE — the conservative
    # max-size model is deliberately kept, because a box sized to the exact per-run sum was
    # measured wrapping in a real render (CJK/Latin boundary spacing no width model here knows
    # about; an 11-boundary line still wrapped at +20% width). What must be present is the
    # CAUSE: without it an author reads a spacing symptom and restructures correct content.
    _findings = _dk.lint_layout(_prs, verbose=False) or []
    _ov = [f for f in _findings if len(f) > 2 and f[2] == "TEXT_OVERLAP"]
    if _flat_w <= _box_w:
        bad.append("mixed-size fixture is inert: the flat model fits anyway "
                   f"({_flat_w:.2f}in <= {_box_w:.2f}in), so it cannot exercise the diagnosis")
    elif not _ov:
        bad.append("the mixed-size TEXT_OVERLAP stopped firing — the conservative max-size model "
                   "must stay; suppressing it was measured UNSAFE (exact-fit boxes still wrap)")
    elif not any("ONE type size each" in str(f[3]) for f in _ov):
        bad.append("mixed-size TEXT_OVERLAP fires but no longer NAMES the cause — an author "
                   "reads it as a spacing problem and restructures text that was fine")
    else:
        ok.append("a mixed-size paragraph still trips TEXT_OVERLAP (conservative) AND the "
                  "finding names the cause: split into one type size per block")

    # ---- the CLI surface itself: a flag this tool documents must REACH the tool ----------
    # `--mode=static` was documented in references/file-inventory.md, under a paragraph promising
    # the map was "verified against the parsers, not the prose", and the parser read `--static`
    # only. The `startswith("--")` filter then dropped the token into oblivion: no error, exit 0,
    # and a NO BUILDS advisory raised against a user who had explicitly opted out of appear-builds
    # — which review-rubrics.md makes a critic finding. Nothing anywhere asserted the two spellings
    # agree, so the drift was invisible for as long as it existed. Both directions are checked: the
    # unknown-flag guard must reject a typo AND must not reject anything the docs promise.
    _flag_pptx, _flag_renders = tmp / "fx_pass.pptx", tmp / "fx_pass_render"

    def _flag_run(*flags):
        p = subprocess.run([sys.executable, str(SCRIPTS / "lint_deck.py"), str(_flag_pptx),
                            "--renders", str(_flag_renders), *flags],
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    _out_bare = _flag_run()[1]
    _out_short = _flag_run("--static")[1]
    _out_long = _flag_run("--mode=static")[1]
    if "NO BUILDS" not in _out_bare:
        bad.append("the flag fixture no longer trips NO BUILDS unflagged, so this check is inert")
    elif "NO BUILDS" in _out_short or "NO BUILDS" in _out_long:
        bad.append("--static and --mode=static do not both silence NO BUILDS "
                   f"(--static silenced: {'NO BUILDS' not in _out_short}, "
                   f"--mode=static silenced: {'NO BUILDS' not in _out_long})")
    else:
        ok.append("--static and --mode=static are the SAME flag (both silence NO BUILDS)")

    _rc_bogus, _out_bogus = _flag_run("--bogus")
    if _rc_bogus != 2 or "unrecognised option" not in _out_bogus:
        bad.append(f"an unknown flag is swallowed again (rc={_rc_bogus}) — the whole class of "
                   "silently-dropped options is back")
    else:
        ok.append("an unknown flag exits 2 with a named list instead of being swallowed")

    _rejected = [f for f in ("--selfread", "--briefing", "--surface", "--textheavy", "--static",
                             "--mode=selfread", "--mode=briefing", "--mode=surface",
                             "--mode=textheavy", "--mode=static", "--mode=presented")
                 if "unrecognised option" in _flag_run(f)[1]]
    if _rejected:
        bad.append("the unknown-flag guard rejects DOCUMENTED flags: " + " ".join(_rejected))
    else:
        ok.append("every delivery-mode flag file-inventory.md documents still reaches the tool")

    # ---- overlap_intent must mean the same thing at BOTH gates ---------------------------
    # It always worked at build time and was never read here, so an author who declared a
    # deliberate composition passed lint_layout and was still refused by lint_deck. Measured on a
    # delivered deck: a bar crossing its reference line — the page's entire claim — was declared,
    # cleared the build gate, and shipped an unresolvable OVERLAP. A declaration that one tool
    # honours and another ignores teaches authors that declaring is pointless.
    import deckkit as _dk
    import tempfile as _tf

    def _crossing(declare):
        _dk.FONT = "Helvetica Neue"
        prs = _dk.blank_deck()
        sl = _dk.add_slide(prs)
        _dk.box(sl, 0, 0, 10, 5.625, fill=_dk.RGBColor(0xF5, 0xF1, 0xE6))
        _dk.box(sl, 0.6, 2.4, 8.8, 0.02, fill=_dk.RGBColor(0x8A, 0x83, 0x77))
        bar = _dk.box(sl, 1.3, 1.9, 1.28, 1.6, fill=_dk.RGBColor(0xB4, 0x46, 0x2A))
        if declare:
            _dk.overlap_intent(bar, "the bar crossing its reference line IS this page's claim")
        d = _tf.mkdtemp()
        out = os.path.join(d, "t.pptx")
        prs.save(out)
        return [l for l in lint(out, d).splitlines() if "OVERLAP " in l and "[warn]" not in l]

    (ok if _crossing(False) else bad).append(
        "an UNdeclared solid-on-solid crossing still fires at render time")
    (ok if not _crossing(True) else bad).append(
        "a DECLARED overlap is silent at render time too, as it already was at build time")

    for line in ok:
        print("  ok   " + line)
    for line in bad:
        print("  FAIL " + line)
    print(f"\n{len(ok)} passed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
