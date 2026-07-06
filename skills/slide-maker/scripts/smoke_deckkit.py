#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_deckkit — call every public deckkit helper (+ the chart recipes) with a canonical example on
a blank deck and assert none raises. A cheap regression guard for the crash-prone positional/tuple
colour contracts that have accumulated. Run after editing deckkit/designed_charts:

    python scripts/smoke_deckkit.py     # exits non-zero on any failure
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deckkit as dk          # noqa: E402
import designed_charts as dc  # noqa: E402
from deckkit import RGBColor  # noqa: E402

def C(h):
    return RGBColor.from_string(h)

TMP = tempfile.gettempdir()
IMG = os.path.join(TMP, "_smoke.png")
from PIL import Image  # noqa: E402
Image.new("RGB", (800, 450), (120, 150, 200)).save(IMG)

W, H = 13.333, 7.5
prs = dk.blank_deck(W, H)
def S():
    return dk.add_slide(prs)
def last():
    return prs.slides[-1]

fails = []
def ok(name, fn):
    try:
        fn()
    except Exception as e:
        fails.append((name, repr(e))); print(f"  FAIL {name} -> {e!r}")
def raises(name, fn):                       # a guard that SHOULD reject bad input
    try:
        fn(); fails.append((name, "did not raise")); print(f"  FAIL {name} (expected an error)")
    except Exception:
        pass

s = S()
ok("box (hex colours)", lambda: dk.box(s, 0, 0, 3, 1, fill="C0362C", line="333333"))     # unified colour API
ok("text", lambda: dk.text(s, 0, 2, 4, 1, [[("hi", 18, C("222222"), True, False)]]))
ok("title_bar/footer", lambda: (dk.title_bar(s, "T", kicker="k"), dk.footer(s, "tag", 1)))
ok("columns/rows", lambda: (dk.columns(3, slide=s), dk.rows(2, slide=s)))
ok("callout", lambda: dk.callout(s, 0, 3, 4, 1, "head", "body"))
ok("chip", lambda: dk.chip(s, 6, 4, 2, 0.6, "A", "sub", C("007CC2")))
ok("bullet", lambda: dk.bullet(s, 5, 1, 5, [("Lead ", "body")]))
ok("hrule", lambda: dk.hrule(s, 0, 5, 5))
ok("table", lambda: dk.table(S(), 0.6, 1.5, 6, [["A", "B"], ["1", "2"]], highlight=1))
ok("scorecard (numeric value)", lambda: dk.scorecard(S(), 0.6, 1, 2.5, 1.8, "Users", 1234, delta="3.2pp"))
ok("scorecard glass", lambda: dk.scorecard(last(), 4, 1, 2.5, 1.8, "X", "9", glass_tint=C("5B8DEF")))
ok("leaderboard (mixed + short row)", lambda: dk.leaderboard(S(), 0.6, 1, 5,
   [(C("007CC2"), "a", 42), (C("C0362C"), "b", "18", "sub"), (C("1B7A3D"), "short-row")]))
ok("takeaway_rail", lambda: dk.takeaway_rail(last(), 7, 1, 3, "lab", "+5", "body"))
ok("change_stat", lambda: dk.change_stat(S(), 4, 3, 3, 0.7, "<10%", "≈40%"))
ok("stat_row", lambda: dk.stat_row(S(), 0.7, 2, 8, [("8", "x", "label"), ("99", "%", "two")]))
ok("stat_row (2-tuple, no unit)", lambda: dk.stat_row(last(), 0.7, 3.2, 8, [("8", "no-unit"), ("9", "also")]))
ok("quadrant", lambda: dk.quadrant(S(), 1.6, 1.6, 5, 4, x_labels=("lo", "hi"), y_labels=("a", "b")))
ok("hub_spoke", lambda: dk.hub_spoke(S(), 6, 4, 1.8, "Core", ["a", "b", "c", "d"]))
ok("timeline h", lambda: dk.timeline(S(), 0.7, 2, 11.4, [("1979", "first"), ("2026", "now", "cap")], highlight=1))
ok("timeline v", lambda: dk.timeline(S(), 0.7, 2, 5, [("x", "a"), ("y", "b")], orientation="v"))
ok("image_tab", lambda: dk.image_tab(S(), 0.5, 0.5, "BEFORE"))
ok("before_after", lambda: dk.before_after(last(), 0.7, 2, 7, 3, IMG, IMG))
ok("photo_triptych", lambda: dk.photo_triptych(S(), [IMG, IMG, IMG]))
ok("photo_card", lambda: dk.photo_card(S(), 0.5, 0.5, 3, 1, role="primary"))
ok("corner_frame", lambda: dk.corner_frame(S()))
ok("accent_one", lambda: dk.accent_one(["a", "b", "c"], 1, C("C0362C")))
ok("cover", lambda: dk.cover(S(), "Title", issue_label="No 1", subtitle="sub"))
ok("colophon (list credits)", lambda: dk.colophon(S(), "tag", credits=["a", "b"], tooling="x"))
ok("sources_page", lambda: dk.sources_page(S(), [f"ref {i}" for i in range(6)]))
ok("part_eyebrow/page_marker", lambda: (dk.part_eyebrow(S(), 0.7, 0.5, "x"), dk.page_marker(last(), 2, 8)))
ok("specimen_card", lambda: dk.specimen_card(S(), 1, 1, 2, 2.5, "Aa", "Sans"))
ok("specimen_card (small h)", lambda: dk.specimen_card(last(), 4, 1, 1, 0.5, "Aa", "tiny"))
ok("wireframe_grid/spec_list", lambda: (dk.wireframe_grid(S(), 0.7, 1.5, 7, 4, [("H", 0, 4, 0, 1)]),
                                        dk.spec_list(last(), 8, 1.5, ["base = 8 px"])))
ok("glass/glow/scrim/offset", lambda: (lambda sl: (dk.box(sl, 0, 0, W, H, fill="0A0E27"),
   dk.glow(sl, 3, 3, 5, 4, C("5B4BE0")), dk.glass_card(sl, 1, 1, 3, 2, C("5B8DEF")),
   dk.scrim_overlay(sl, 0, 5, W, 2), dk.offset_shadow(sl, 5, 5, 2, 0.6, C("F5B301"))))(S()))
ok("editorial_header", lambda: dk.editorial_header(S(), "eyebrow", "Title", serif="Georgia"))
ok("big_numeral", lambda: dk.big_numeral(S(), 0.5, 0.5, "04", mode="ghost"))
ok("picture", lambda: dk.picture(S(), IMG, 1, 1, 4, 3, round=True))
def _wordmark():
    p = os.path.join(TMP, "_wm.png")
    dk.wordmark("Acme Labs", p, rule=True, monogram=True)
    assert os.path.exists(p) and os.path.getsize(p) > 0, "wordmark PNG missing/empty"
    dk.logo(S(), p, h=0.4)                       # placed afterward, exactly like a real logo
ok("wordmark (typographic logo stand-in)", _wordmark)
ok("backdrop_motif", lambda: dk.backdrop_motif(S(), accent_disc=C("C0362C")))
ok("native_chart (editable)", lambda: dk.native_chart(S(), 0.6, 1, 6, 3.2, ["Q1", "Q2", "Q3"],
   [("新客", [10, 18, 26]), ("老客", [30, 33, 36])], kind="column", dark=True, highlight=0))
ok("native_dual_axis (editable)", lambda: dk.native_dual_axis(S(), 0.6, 1, 7, 3.2, ["m1", "m2", "m3"],
   [5, 24, 40], [100, 80, 62], left_name="占比（%）", right_name="成本（指数）", dark=True))
ok("native_donut (editable)", lambda: dk.native_donut(S(), 0.6, 1, 5, 4, [("私域", 40), ("公域", 35), ("其他", 25)], "40%", "私域占比", dark=True))
ok("native_pareto (editable)", lambda: dk.native_pareto(S(), 0.6, 1, 8, 4, [("华东", 45), ("华北", 28), ("华南", 18)], dark=True))
ok("native_bubble (editable)", lambda: dk.native_bubble(S(), 0.6, 1, 8, 4, [(1, 2, 30), (2, 3, 55), (3, 2.4, 20)], dark=True))
def _csv_chart():
    p = os.path.join(TMP, "_s.csv"); open(p, "w").write("m,a,b\nJ,1,\"2,000\"\nF,3,4\n")
    cats, series = dk.series_from_csv(p, "m", ["a", "b"])
    assert cats == ["J", "F"] and series[0] == ("a", [1.0, 3.0]) and series[1][1] == [2000.0, 4.0], "series_from_csv parse"
    dk.native_chart(S(), 0.6, 1, 6, 3, cats, series, kind="column")
ok("series_from_csv + native_chart", _csv_chart)
raises("series_from_csv rejects a missing column", lambda: dk.series_from_csv(os.path.join(TMP, "_s.csv"), "nope", ["a"]))

ok("dc.donut_kpi", lambda: dc.donut_kpi(os.path.join(TMP, "_d.png"), [("a", 3), ("b", 2)], "5", "x"))
ok("dc.dumbbell", lambda: dc.dumbbell(os.path.join(TMP, "_db.png"), [("a", 1, 2)], highlight=0))
ok("dc.slope", lambda: dc.slope(os.path.join(TMP, "_sl.png"), [("a", 1, 2)], highlight=0))
ok("dc.dual_axis", lambda: dc.dual_axis(os.path.join(TMP, "_da.png"), [1, 2], [1, 2], [2, 1]))
ok("dc.bubble_trend", lambda: dc.bubble_trend(os.path.join(TMP, "_bt.png"), [(1, 2, 3, "a"), (2, 3, 5, "b")]))
ok("dc.pareto", lambda: dc.pareto(os.path.join(TMP, "_pa.png"), [("a", 4), ("b", 2)]))

# --- the build-time geometry gate must actually catch a fault and (strict) block the save ---
def _offcanvas_deck():
    p = dk.blank_deck(10, 5.625); s = dk.add_slide(p)
    dk.text(s, 9.2, 2.0, 3.0, 0.5, [[("this text runs off the right slide edge entirely here", 16, dk.DEEP, False, False)]])
    return p
def _lint_layout_gate():
    crit = [f for f in dk.lint_layout(_offcanvas_deck(), verbose=False) if f[1] == "CRITICAL"]
    assert crit, "lint_layout missed an off-canvas CRITICAL"
    p = dk.blank_deck(10, 5.625); s = dk.add_slide(p)
    dk.text(s, 1.0, 1.0, 4.0, 0.5, [[("a tidy line well inside the slide", 16, dk.DEEP, False, False)]])
    assert not [f for f in dk.lint_layout(p, verbose=False) if f[1] == "CRITICAL"], "lint_layout false-flagged a clean slide"
ok("lint_layout catches off-canvas + passes clean", _lint_layout_gate)
raises("lint_layout(strict=True) raises on a CRITICAL", lambda: dk.lint_layout(_offcanvas_deck(), strict=True, verbose=False))

raises("donut_kpi([]) rejects empty", lambda: dc.donut_kpi(os.path.join(TMP, "_x.png"), [], "0", "n"))
raises("dual_axis rejects empty", lambda: dc.dual_axis(os.path.join(TMP, "_x.png"), [], [], []))
raises("wireframe_grid rejects cols=0", lambda: dk.wireframe_grid(S(), 0, 0, 5, 4, [], cols=0))
raises("picture rejects missing file", lambda: dk.picture(S(), "/no/such/img.png", 0, 0, 3, 2))

prs.save(os.path.join(TMP, "_smoke_deck.pptx"))
print(f"\nsmoke_deckkit: {len(fails)} failure(s)" + ("" if not fails else " — " + "; ".join(n for n, _ in fails)))
sys.exit(1 if fails else 0)
