#!/usr/bin/env python3
"""The image-series gate, read from the FILE on both runtimes.

Three things a reviewer cannot see in a rendered image-led deck: whether each generated picture was
PLANNED (has a slot with a meaning line), whether a generated person was given a real-looking name or a
testimonial without a 'fictional' label (the user's people rule), and whether the series was QC'd
against its key. Both directions are asserted for each.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_image_series as cis  # noqa: E402
import deckkit as dk  # noqa: E402
import image_series as ims  # noqa: E402
from PIL import Image  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def codes(findings, sev=None):
    return [c for (s, c, w) in findings if sev is None or s == sev]


PLAN = {"art_direction": "warm editorial craft photography, soft window daylight, shallow depth",
        "palette": ["F2E8D8", "D9A13B", "C2462E", "1A1A1A"], "render": "photo",
        "slots": [{"id": "maker", "slide": 1, "frame": {"shape": "arch", "w": 4.0, "h": 5.0},
                   "subject": "a ceramic maker at a wheel in a sunlit studio", "kind": "generic-person",
                   "cutout": False, "alt": "a maker at a wheel", "referent": "generic-concrete",
                   "meaning": "the hands-on work the program funds; a person, not a product, opens the deck"},
                  {"id": "mira", "slide": 2, "frame": {"shape": "ellipse", "w": 3.0, "h": 3.0},
                   "subject": "a young designer with a notebook in a bright workshop", "kind": "persona",
                   "persona_label": "Illustrative persona", "cutout": False, "alt": "persona portrait",
                   "referent": "generic-concrete",
                   "meaning": "the persona this service is designed around; her needs drive every later slide"}]}


def build(td, *, persona_label=True, name_on_maker=False, team_words=False, place=("maker", "mira"),
          untagged_extra=False, maker_lines=(), raw_mira=False):
    td = Path(td)
    for s in PLAN["slots"]:
        im = Image.new("RGB", (300, 360))
        im.putdata([(200 + x % 40, 150 + y % 30, 90) for y in range(360) for x in range(300)])
        im.save(td / "slide-{:02d}-{}.png".format(s["slide"], s["id"]))
    (td / "series.json").write_text(json.dumps(PLAN), encoding="utf-8")
    prs = dk.blank_deck(13.333, 7.5)
    s1, s2 = dk.add_slide(prs), dk.add_slide(prs)
    if "maker" in place:
        ims.slot_picture(s1, PLAN, "maker", 0.6, 0.8, 4.0, 5.0, image_dir=td)
    dk.text(s1, 5.0, 1.0, 7, 1.0, [[("Our makers' program", 30, dk.DEEP, True, False)]])
    if name_on_maker:
        dk.text(s1, 5.0, 2.4, 7, 1.0, [[("Daniel Okafor, Head of Ceramics", 18, dk.DEEP, False, False)]])
    if team_words:
        dk.text(s1, 5.0, 3.6, 7, 1.0, [[("Meet the team", 18, dk.DEEP, False, False)]])
    for i, line in enumerate(maker_lines):
        dk.text(s1, 5.0, 4.6 + 0.5 * i, 7, 0.5, [[(line, 14, dk.DEEP, False, False)]])
    if "mira" in place:
        ims.slot_picture(s2, PLAN, "mira", 0.6, 0.8, 3.0, 3.0, image_dir=td)
    if raw_mira:                       # the series image placed WITHOUT slot_picture: no tag on it
        dk.picture(s2, str(td / "slide-02-mira.png"), 0.6, 0.8, 3.0, 3.0, fit="cover", alt="persona portrait")
    dk.text(s2, 4.0, 1.0, 8, 1.0, [[("Mira, 29, product designer", 24, dk.DEEP, True, False)]])
    if persona_label:
        dk.text(s2, 4.0, 2.2, 8, 0.6, [[("Illustrative persona", 14, dk.DEEP, False, False)]])
    if untagged_extra:
        p = dk.picture(s2, str(td / "slide-01-maker.png"), 9, 4, 2, 2, fit="cover", alt="extra")
        dk._compose_tag(p, gen="ghost")
    path = td / "deck.pptx"
    prs.save(str(path))
    return path


GATES = lambda td: {"design_plan": {"imagery": "series", "image_series": str(Path(td) / "series.json")}}  # noqa: E731

with tempfile.TemporaryDirectory() as td:
    rec = cis.recorded_series(GATES(td))
    check(rec and rec["imagery"] == "series", "recorded_series reads design_plan")
    check(cis.recorded_series({"design": {"imagery": "series", "image_series": "x"}})["plan"] == "x",
          "recorded_series reads the Codex design twin")
    check(cis.recorded_series({"design_plan": {"imagery": "selective"}}) is None, "selective = not a series deck")
    # clean: both slots placed, persona labelled, no names on the generic person
    p = build(td)
    f, facts = cis.check(str(p), rec, td)
    check(not codes(f, "block"), "a clean series deck has blocks: {}".format(f))
    check(any(c == "SERIES QC MISSING" for c in codes(f, "note")), "no series-qc.json is a NOTE")
    # the documented layout keeps the generated images in <deck>/assets/generated — the QC report
    # there must be FOUND, and before it exists the note must print a command that runs as printed
    gen = Path(td) / "assets" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    (gen / "image_prompt_manifest.json").write_text("[]", encoding="utf-8")
    nq = [w for (s_, c, w) in cis.check(str(p), rec, td)[0] if c == "SERIES QC MISSING"]
    check(nq and "--dir " + str(gen) in nq[0] and "<" not in nq[0],
          "the QC note must name the generated folder it found: {}".format(nq))
    (gen / "series-qc.json").write_text(json.dumps({"key": "maker", "slots": [], "outliers": [],
                                                    "acknowledged": {}}), encoding="utf-8")
    check("SERIES QC MISSING" not in codes(cis.check(str(p), rec, td)[0]),
          "a series-qc.json two folders down (assets/generated) must be found")
    (gen / "series-qc.json").write_text(json.dumps({"key": "maker", "slots": [], "outliers": ["mira"],
                                                    "acknowledged": {}}), encoding="utf-8")
    check("SERIES QC OUTLIER" in codes(cis.check(str(p), rec, td)[0], "note"), "an open outlier is a NOTE")
    import shutil  # noqa: E402
    shutil.rmtree(Path(td) / "assets")
    # GENERATED PERSON NAMED — name + role on a generic person
    p = build(td, name_on_maker=True)
    check("GENERATED PERSON NAMED" in codes(cis.check(str(p), rec, td)[0], "block"), "a named generic person must block")
    # ...team words too
    p = build(td, team_words=True)
    check("GENERATED PERSON NAMED" in codes(cis.check(str(p), rec, td)[0], "block"), "'Meet the team' over a generated person must block")
    # ...a Chinese name joined to a role, and an attributed quote
    for lines in (["张伟｜首席设计师"], ["“The wheel taught me patience.” — Ana"]):
        p = build(td, maker_lines=lines)
        check("GENERATED PERSON NAMED" in codes(cis.check(str(p), rec, td)[0], "block"),
              "{!r} beside a generated person must block".format(lines))
    # Review Focus 1: ordinary headings and role words that name NO ONE must not block
    for lines in (["Community Garden Program", "Design Thinking Workshop"],
                  ["Spring Planting Day", "Ask the research lead for a plot"],
                  ["城市菜园，社区负责人招募", "高效灌溉 · 节水"]):
        p = build(td, maker_lines=lines)
        f = cis.check(str(p), rec, td)[0]
        check("GENERATED PERSON NAMED" not in codes(f, "block"), "{!r} named no one but blocked: {}".format(lines, f))
    # the persona WITHOUT its label
    p = build(td, persona_label=False)
    check("GENERATED PERSON NAMED" in codes(cis.check(str(p), rec, td)[0], "block"), "an unlabelled persona must block")
    # The final review (2026-10-03) found the first patterns blocking ordinary copy beside a generated
    # person: any two Title Case words read as a name, a role word anywhere later on the line counted,
    # a surname-like first character (周 夏 金 方 高) started a "name", any dash after a quote was an
    # attribution. Each of these named no one — a false block stops delivery ("better a miss").
    for line in ("In Rotterdam, the project lead explains the plan",
                 "Last Spring, our garden lead planted beds along the wall",
                 "Community Gardens — Volunteer Lead Training",
                 "Open Studio, where volunteers lead the tour",
                 "Design Sprint - for every product designer",
                 "Case study: rooftop gardens in Rotterdam",
                 "The founders of the allotment movement, 1890s",
                 '"Grow food where people live" — City Plan 2030',
                 "周末，社区负责人招募", "夏日｜园艺老师带你种菜", "金秋，社区菜园负责人报名",
                 "方法 · 设计师工作坊", "“城市屋顶菜园计划”——每周六开放"):
        f = cis.check(str(build(td, maker_lines=[line])), rec, td)[0]
        check("GENERATED PERSON NAMED" not in codes(f, "block"), "{!r} named no one but blocked".format(line))
    # ...while a person NAMED beside a generated face still blocks, in both languages
    for line in ("Ana Ruiz | Lead Gardener", "Mira Chen — Senior Product Designer at Loom",
                 "李娜，社区园艺负责人", "“每天浇水半小时就够了。”——王芳", "“The wheel taught me patience.” — Ana, potter",
                 "Dr. Lena Vogt, Professor of Soil Science", "Lucía Gómez, Head of Design", "张伟——首席工程师"):
        f = cis.check(str(build(td, maker_lines=[line])), rec, td)[0]
        check("GENERATED PERSON NAMED" in codes(f, "block"), "{!r} names a person and must block".format(line))
    # UNPLANNED GENERATED IMAGE
    p = build(td, untagged_extra=True)
    check("UNPLANNED GENERATED IMAGE" in codes(cis.check(str(p), rec, td)[0], "block"), "a gen tag with no slot must block")
    # Review Focus 5: NO SLOT PLACED (the agent used dk.picture instead of slot_picture)
    p = build(td, place=())
    check("NO SLOT PLACED" in codes(cis.check(str(p), rec, td)[0], "block"), "a series with nothing placed must block")
    p = build(td, place=("maker",))
    check("SLOT NOT PLACED" in codes(cis.check(str(p), rec, td)[0], "note"), "one unplaced slot is a NOTE")
    # a series image placed with dk.picture carries no tag, so the people rule could not see it — the
    # gate recognises the file itself (picture() embeds the bytes unchanged) and blocks (final review)
    p = build(td, place=("maker",), raw_mira=True, persona_label=False)
    f = cis.check(str(p), rec, td)[0]
    check("UNTAGGED SERIES IMAGE" in codes(f, "block"), "a series image placed without slot_picture must block: {}".format(f))
    # a misspelled switch ("image-led") is not silently "not a series deck"
    odd = cis.recorded_series({"design_plan": {"imagery": "image-led", "image_series": "series.json"}})
    check(odd is not None and "UNKNOWN IMAGERY" in codes(cis.check(str(p), odd, td)[0], "block"),
          "imagery other than series/selective must block: {}".format(odd))
    # a plan that would crash the checks blocks instead of reading as NOT CHECKED
    (Path(td) / "series.json").write_text(json.dumps(dict(PLAN, slots=[dict(PLAN["slots"][0], frame="arch")])),
                                          encoding="utf-8")
    try:
        f = cis.check(str(p), rec, td)[0]
        check("SERIES PLAN INVALID" in codes(f, "block"), "a malformed plan must block: {}".format(f))
    except Exception as e:
        fails.append("the gate crashed on a malformed plan: {}: {}".format(type(e).__name__, e))
    (Path(td) / "series.json").write_text(json.dumps(PLAN), encoding="utf-8")
    # missing / invalid plan
    check("SERIES PLAN MISSING" in codes(cis.check(str(p), {"imagery": "series", "plan": None}, td)[0], "block"),
          "a series with no plan path must block")
    (Path(td) / "series.json").write_text(json.dumps({"slots": []}), encoding="utf-8")
    check("SERIES PLAN INVALID" in codes(cis.check(str(p), rec, td)[0], "block"), "an invalid plan must block")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_image_series_gate] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
