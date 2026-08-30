#!/usr/bin/env python3
"""The direction gate has to bind at BOTH ends: what it shows, and what ships.

Two holes, both reported by an author on a real deck and neither visible to any check.

1. `cover_motif` / `ambient_motif` are raw HTML by design, so a bespoke register can draw its own
   signature. Nothing checked that what was supplied DREW anything — a sentence describing the
   motif rendered as literal text across all four sample tiles, and the author chose a direction
   whose preview was covered in the author's own notes.

2. The pick was recorded as a sentence and compared to nothing. The chosen direction declared a
   Georgia display face and a centred cover; the deck shipped Helvetica Neue titles and a low-left
   cover, because `style.py` set `display=` and every title passed `dk.FONT`. Two neighbouring
   checks for the identical class already existed — `check_register_pixels` (a declared colour must
   reach the pixels) and `check_style_applied` (a declared preset must be called) — and the
   direction, the one thing the USER personally chose, had none.
"""
import json
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
warnings.simplefilter("ignore")

import deckkit as dk                       # noqa: E402
import check_direction_applied as cda      # noqa: E402
import directions_diversity as dd          # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


# ---------------------------------------------------------------- a drawing slot is not a notepad
PROSE = {"name": "P", "bg": "#FFFFFF", "accent": "#E2231A", "display": "Helvetica",
         "body": "Helvetica", "cover": "low-left", "skeleton": "rail", "density": "minimal",
         "cover_motif": "<div class='datum'>a framed opening cut into the page, and you look "
                        "THROUGH it at the subject as the frame narrows</div>"}
DRAWS = {"name": "D", "bg": "#101418", "accent": "#40E0FF", "display": "Menlo", "body": "Menlo",
         "cover": "centred", "skeleton": "band", "density": "dense",
         "cover_motif": "<svg viewBox='0 0 10 10'><circle cx='5' cy='5' r='4'/></svg>"}
BOXES = {"name": "X", "bg": "#F5F5F5", "accent": "#333333", "display": "Georgia", "body": "Georgia",
         "cover": "centred", "skeleton": "island", "density": "medium",
         "ambient_motif": "<div style='width:40px;height:2px;background:#333'></div>"}
SHORT = {"name": "S", "bg": "#222222", "accent": "#EEEEEE", "display": "Menlo", "body": "Menlo",
         "cover": "low-left", "skeleton": "band", "density": "dense",
         "cover_motif": "<b>03</b>"}

r = dd.check([PROSE, DRAWS])
check([p for p in r["prose_motifs"] if p[0] == "P"],
      "a motif field holding a SENTENCE is reported — it renders as literal text on every sample "
      "tile, which is how an author picks a direction covered in the author's own notes")
check(not [p for p in r["prose_motifs"] if p[0] == "D"],
      "...and an <svg> that actually draws the mark passes")
check(not dd._prose_motif(BOXES),
      "...as does a styled div that makes a box — the test is whether it DRAWS, not whether it is svg")
check(not dd._prose_motif(SHORT),
      "...and a short label inside a mark is not prose; twelve words with no geometry is")


check(dd._prose_motif({"cover_motif": "<div>一道切进页面的门洞,你透过它看主题,随着 deck "
                                     "推进框会越收越窄</div>"}),
      "🔴 a motif description written in 中文 is caught too — `.split()` counts a 40-character "
      "Chinese sentence as ONE word, so the first version fired only for authors already writing "
      "in English, which is the same blindness as measuring CJK widths with Latin metrics")
check(not dd._prose_motif({"cover_motif": "<div>零叁</div>"}),
      "...and a short CJK label inside a mark is still not prose")


# ------------------------------- the pick is read by NAME, in whatever language the line is written
NAMED = [{"name": "A — Swiss Red"}, {"name": "B — Aperture (bespoke)"},
         {"name": "C — Dark Console"}, {"name": "D — Waybill (bespoke)"}]
for line, want in (
        ("picked `B — Aperture (bespoke)` of 4 rendered directions (A Swiss Red · C Dark Console)",
         "B — Aperture (bespoke)"),
        ("方向闸门:选定 B — Aperture (bespoke),4 个方向里挑的;落选 A — Swiss Red · C — Dark Console",
         "B — Aperture (bespoke)"),
        ("已采用「B — Aperture (bespoke)」", "B — Aperture (bespoke)"),
        ("direction gate: B — Aperture (bespoke)", "B — Aperture (bespoke)"),
        ("picked D — Waybill (bespoke) of 4 · lost: A — Swiss Red", "D — Waybill (bespoke)")):
    got, why = cda.picked({"design_plan": {"direction_gate": line}}, NAMED)
    check(got == want,
          "the pick reads out of {!r}".format(line[:40]) if got == want
          else "{!r} -> {!r}, wanted {!r} ({})".format(line[:50], got, want, why))
check(cda.picked({"design_plan": {"direction_gate": "picked B of 2"}},
                 [{"name": "B"}, {"name": "B2 — Aperture"}])[0] == "B",
      "...and a bare `B` never resolves to `B2` — the fallback matches at a word boundary")

# ------------------------------------------------------- the picked direction must be what ships
def _deck(tmp, *, ground, title_font, title_left, accent_used=True):
    dk.set_palette(deep="1E1B18", magenta="2F6B5F", font="Helvetica Neue", display="Georgia")
    dk.set_ground(ground)
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.text(s, title_left, 2.0, 6.0, 0.9,
            [[("A title", 40, dk.DEEP, True, False, title_font)]])
    dk.text(s, title_left, 3.1, 6.0, 0.4, [[("body copy", 13, dk.DEEP, False, False, dk.FONT)]])
    if accent_used:
        dk.box(s, 0.6, 4.2, 2.0, 0.06, fill=dk.MAGENTA)
    p = tmp / "d.pptx"
    prs.save(str(p))
    return p


DIRS = [{"name": "A — Swiss", "bg": "#FFFFFF", "accent": "#E2231A", "display": "Helvetica Neue",
         "body": "Helvetica Neue", "cover": "low-left"},
        {"name": "B — Aperture", "bg": "#F2EFE6", "accent": "#2F6B5F", "display": "Georgia",
         "body": "Helvetica Neue", "cover": "centred"}]

tmp = Path(tempfile.mkdtemp(prefix="dirfid-"))
(tmp / "directions.json").write_text(json.dumps(DIRS), encoding="utf-8")
GATES = {"design_plan": {"direction_gate": "picked `B — Aperture` of 4 rendered directions"}}

deck = _deck(tmp, ground="F2EFE6", title_font=dk.FONT, title_left=0.6)
problems, facts = cda.check(deck, gates=GATES, deck_dir=tmp)
axes = {a for a, _w in problems}
check(facts.get("picked") == "B — Aperture",
      "the pick is read out of the recorded `direction gate:` line")
check("display" in axes,
      "🔴 a display face DECLARED in the picked direction and never read by the build is caught — "
      "the exact drift a delivered deck shipped with")
check("cover" in axes,
      "...and a centred cover that shipped left-set is caught")
check("bg" not in axes and "accent" not in axes and "body" not in axes,
      "...while every axis the deck DID honour stays quiet — including BODY, which a median-size "
      "reading called a divergence on a two-run page ({})".format(sorted(axes)))

# The whole point of the accent axis: an EXACT match must not read as absent. The first version
# wrote `(_dist(...) or 999)`, and a distance of 0 is falsy.
check(cda._dist("#2F6B5F", "2F6B5F") == 0,
      "an exact colour match measures 0 — and 0 is falsy, which is what made a perfectly applied "
      "accent read as missing before this test existed")

deck2 = _deck(tmp, ground="E8DFC9", title_font=dk.FONT, title_left=0.6)
problems2, _f2 = cda.check(deck2, gates=GATES, deck_dir=tmp)
check("bg" in {a for a, _w in problems2},
      "a ground moved off the picked one is caught — #F2EFE6 and #E8DFC9 are different papers, "
      "which is exactly what the freshness gate says about them")

GATES_DEV = {"design_plan": dict(GATES["design_plan"], direction_deviations={
    "bg": "the freshness gate measured the picked value as a repeat of a recent deck's",
    "display": "the presenter's brand type replaces the direction's serif",
    "cover": "the cover carries a logo lockup that wants the left rail"})}
problems3, facts3 = cda.check(deck2, gates=GATES_DEV, deck_dir=tmp)
check(not problems3 and len(facts3.get("accepted", [])) == 3,
      "every deviation RECORDED IN WRITING is accepted and printed — moving a direction is "
      "legitimate design, moving it silently is what this catches")

problems4, facts4 = cda.check(deck2, gates={"design_plan": {}}, deck_dir=tmp)
check(not problems4 and facts4.get("note"),
      "an unreadable pick reports NOT CHECKED rather than clean — the two are different facts")

bare = Path(tempfile.mkdtemp(prefix="nodirs-"))
deck3 = _deck(bare, ground="FFFFFF", title_font=dk.FONT, title_left=0.6)
problems5, facts5 = cda.check(deck3, gates=GATES, deck_dir=bare)
check(not problems5 and "directions.json" in (facts5.get("note") or ""),
      "a deck that never went through the direction gate is not punished for it, and says so")

# A deck whose runs carry no explicit typeface inherits the theme's face, and that is NOT the same
# as matching the picked one. Reporting nothing there is the silent-skip class this repo treats as
# a defect of its own.
theme = Path(tempfile.mkdtemp(prefix="notheme-"))
(theme / "directions.json").write_text(json.dumps(DIRS), encoding="utf-8")
dk.set_palette(deep="1E1B18", magenta="2F6B5F")
dk.set_ground("F2EFE6")
_prs = dk.blank_deck()
_s = dk.add_slide(_prs)
_tb = _s.shapes.add_textbox(dk.Inches(1), dk.Inches(2), dk.Inches(5), dk.Inches(1))
_tb.text_frame.text = "a run with no explicit latin face"
_deck = theme / "d.pptx"
_prs.save(str(_deck))
_p, _f = cda.check(_deck, gates=GATES, deck_dir=theme)
check(any("typeface" in u for u in _f.get("unchecked", [])),
      "🔴 a deck that sets no explicit typeface reports the face axes as NOT CHECKED rather than "
      "passing them in silence — unchecked and clean are different facts")
check("display" not in {a for a, _w in _p},
      "...and does not invent a divergence it cannot measure")


# and the way the gate ACTUALLY runs: a fresh process reading the record off disk. Passing the
# gates in-process would have tested a path the gate never takes.
(tmp / ".deck-gates.json").write_text(json.dumps(GATES), encoding="utf-8")
out = subprocess.run([sys.executable, str(SCRIPTS / "check_direction_applied.py"), str(deck)],
                     capture_output=True, text=True, cwd=str(tmp))
check("DISPLAY" in out.stdout and out.returncode == 1,
      "🔴 and a FRESH PROCESS — how the gate actually runs — reports it and exits non-zero")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
