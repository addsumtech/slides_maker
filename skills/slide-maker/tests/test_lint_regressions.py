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

    for line in ok:
        print("  ok   " + line)
    for line in bad:
        print("  FAIL " + line)
    print(f"\n{len(ok)} passed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
