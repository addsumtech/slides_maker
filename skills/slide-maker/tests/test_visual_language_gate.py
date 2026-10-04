#!/usr/bin/env python3
"""The visual-language gate, read from the file on both runtimes: a recorded language must be APPLIED (cover + half the pages carry its tag, its display face is used) and its prohibitions hold; unknown names and unreadable decks block."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


import json
import deckkit as dk, visual_languages as vl, check_visual_language as cvl
from PIL import Image
check(cvl.recorded_language({"design_plan": {"visual_language": "collage", "vl_fonts": "both"}}) == {"name": "collage", "fonts": "both", "ground": None}, "shared record")
check(cvl.recorded_language({"design": {"visual_language": "soft"}})["name"] == "soft", "Codex record")
check(cvl.recorded_language({"design_plan": {"visual_language": None}}) is None, "unset")
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    img = td / "p.png"
    im = Image.new("RGB", (600, 400))
    im.putdata([(150 + (x * 7 + y * 3) % 90, 110 + (x * 3) % 80, 70 + (y * 5) % 60) for y in range(400) for x in range(600)])
    im.save(img)
    def deck(kit_pages, plain_pages, name="collage"):
        prs = dk.blank_deck(13.333, 7.5)
        k = vl.use(name, prs)
        for i in range(kit_pages):
            s = k.new_slide()
            (k.cover if i == 0 else k.image_text)(s, **({"title": "Repair night", "image": str(img)} if i == 0 else
                                                        {"title": "Tools", "body": "Shared tools on every bench.", "image": str(img)}))
        for _ in range(plain_pages):                 # PLAIN: not even the kit's new_slide()
            s = dk.add_slide(prs)
            dk.text(s, 0.8, 0.8, 8, 1, [[("Agenda", 28, dk.DEEP, True, False)]])
        p = td / "d{}{}.pptx".format(kit_pages, plain_pages)
        prs.save(str(p))
        return p
    rec = {"name": "collage", "fonts": "both"}
    f, facts = cvl.check(str(deck(3, 1)), rec)
    check(not [x for x in f if x[0] == "block"], "3 kit pages of 4 pass: {}".format(f))
    f, _ = cvl.check(str(deck(2, 2)), rec)
    check(not [x for x in f if x[0] == "block"], "Review Focus 5: half the pages + cover pass: {}".format(f))
    f, _ = cvl.check(str(deck(1, 3)), rec)
    check(any(c == "LANGUAGE NOT APPLIED" for _s, c, _w in f), "1 of 4 blocks")
    f, _ = cvl.check(str(deck(0, 3)), rec)
    check(any(c == "LANGUAGE NOT APPLIED" for _s, c, _w in f), "recorded but never used blocks")
    f, _ = cvl.check(str(deck(3, 1)), {"name": "nope", "fonts": "both"})
    check(any(c == "UNKNOWN VISUAL LANGUAGE" for _s, c, _w in f), "unknown name blocks")

    # a crash on a recorded deck is a block, never NOT CHECKED
    f, _ = cvl.check(str(td / "missing.pptx"), rec)
    check(any(s_ == "block" for s_, _c, _w in f), "an unreadable deck recorded as a language blocks")
    # editorial forbids confetti: two big decorative primitives on one page violate it
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use("editorial", prs)
    s = k.new_slide()
    k.cover(s, title="Repair night", image=str(img))
    s2 = k.new_slide()
    k.section(s2, number="02", title="How it works")
    dk.box(s2, 7.0, 1.0, 2.5, 2.5, fill="B23A28")
    dk.box(s2, 10.0, 3.5, 2.5, 2.5, fill="1F4E79")
    p = td / "confetti.pptx"
    prs.save(str(p))
    f, _ = cvl.check(str(p), {"name": "editorial", "fonts": "both"})
    check(any(c == "FORBIDDEN BY LANGUAGE" for _s, c, _w in f), "editorial's confetti prohibition is enforced: {}".format(f))

    # ordinary pages started with k.new_slide() (agenda, charts) are IN the language: a chart-heavy deck built
    # exactly as the reference says must pass; padding with plain slides still blocks (Task 13 run, 2026-10-04)
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use("collage", prs)
    k.cover(k.new_slide(), title="Repair night", image=str(img))
    k.data(k.new_slide(), number="1", label="evening a month")
    for _ in range(8):
        s_ = k.new_slide()
        dk.text(s_, 0.8, 0.8, 8, 1, [[k.run("Agenda", 28)]])
    p = td / "chart_heavy.pptx"
    prs.save(str(p))
    f, facts = cvl.check(str(p), {"name": "collage", "fonts": "both"})
    check(not [x for x in f if x[0] == "block"], "a deck of kit pages + ordinary k.new_slide() pages passes: {} {}".format(f, facts))
    prs = dk.blank_deck(13.333, 7.5)
    k = vl.use("collage", prs)
    k.cover(k.new_slide(), title="Repair night", image=str(img))
    for _ in range(8):
        s_ = dk.add_slide(prs)
        dk.text(s_, 0.8, 0.8, 8, 1, [[("Agenda", 28, dk.DEEP, True, False)]])
    p = td / "plain_padded.pptx"
    prs.save(str(p))
    f, _ = cvl.check(str(p), {"name": "collage", "fonts": "both"})
    check(any(c == "LANGUAGE NOT APPLIED" for _s, c, _w in f), "a cover + plain slides still blocks: {}".format(f))

    # a recorded curated language is a KIT that ships with the skill — the register notes on both runtimes
    # must say so, not call it an INVENTED register and advise scaffolding a kit and saving it (real-deck
    # gate-check, 2026-10-03: the record this reference prescribes drew both wrong notes)
    import contextlib, io
    import render_deck as rd, codex_delivery_gate as cdg
    rec_dir = td / "vl-deck"
    rec_dir.mkdir()
    vp = rec_dir / "deck.pptx"
    deck(3, 1, name="editorial").rename(vp)
    plan = {"visual_language": "editorial", "vl_fonts": "both", "look_source": "bespoke",
            "style_pick": "bespoke editorial for a neighbourhood repair café"}
    (rec_dir / ".deck-gates.json").write_text(json.dumps({"design_plan": plan}), encoding="utf-8")
    for label, call in (("render_deck kit note", lambda: rd._register_kit_note(str(vp), {"design_plan": plan})),
                        ("render_deck keep note", lambda: rd._register_keep_note(str(vp), {"design_plan": plan})),
                        ("codex kit note", lambda: cdg.note_register_kit({"design": plan}, vp, None)),
                        ("codex keep note", lambda: cdg.note_register_kept({"design": plan}, vp))):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            call()
        out = buf.getvalue()
        check("INVENTED" not in out and "keep it" not in out and "--new" not in out,
              "{} misreads a curated language as invented: {!r}".format(label, out[:160]))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rd._register_kit_note(str(vp), {"design_plan": plan})
        cdg.note_register_kit({"design": plan}, vp, None)
    check(buf.getvalue().count("curated visual language") == 2, "both kit notes name the curated language: {!r}".format(buf.getvalue()))
    # control: an invented register with no language recorded still hears both notes
    inv = dict(plan, visual_language=None, style_pick="bespoke workshop-ledger for a repair café")
    (rec_dir / ".deck-gates.json").write_text(json.dumps({"design_plan": inv}), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rd._register_kit_note(str(vp), {"design_plan": inv})
        rd._register_keep_note(str(vp), {"design_plan": inv})
    check("INVENTED" in buf.getvalue() and "keep it" in buf.getvalue(), "an invented register still gets both notes: {!r}".format(buf.getvalue()[:200]))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_visual_language_gate] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
