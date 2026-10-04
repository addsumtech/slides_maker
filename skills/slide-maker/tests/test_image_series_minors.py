#!/usr/bin/env python3
"""Image-series follow-ups: a negated label is not a label, a slot placed twice or on another slide is said, a stale series-qc.json is said, prompts() writes absolute paths, a contact-sheet failure is printed, an explicit --size is honoured and moderation goes to generations only, chroma_cutout has an example."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)



import io, json, os, time, contextlib, argparse
import deckkit as dk, image_series as ims, check_image_series as cis
from PIL import Image
PLAN = {"art_direction": "warm editorial craft photography, soft window daylight, shallow depth",
        "palette": ["F2E8D8", "D9A13B", "C2462E", "1A1A1A"], "render": "photo",
        "slots": [{"id": "maker", "slide": 1, "frame": {"shape": "rect", "w": 4.0, "h": 5.0},
                   "subject": "a ceramic maker at a wheel in a sunlit studio", "kind": "generic-person",
                   "cutout": False, "alt": "a maker at a wheel", "referent": "generic-concrete",
                   "meaning": "the hands-on work the program funds; a person, not a product, opens the deck"},
                  {"id": "mira", "slide": 2, "frame": {"shape": "rect", "w": 3.0, "h": 3.0},
                   "subject": "a young designer with a notebook in a bright workshop", "kind": "persona",
                   "persona_label": "Illustrative persona", "cutout": False, "alt": "persona portrait",
                   "referent": "generic-concrete",
                   "meaning": "the persona this service is designed around; her needs drive every later slide"}]}


def build(td, lines2=("Illustrative persona",), placements=(("maker", 1), ("mira", 2))):
    td = Path(td)
    for s in PLAN["slots"]:
        im = Image.new("RGB", (300, 360))
        im.putdata([(200 + x % 40, 150 + y % 30, 90) for y in range(360) for x in range(300)])
        im.save(td / "slide-{:02d}-{}.png".format(s["slide"], s["id"]))
    (td / "series.json").write_text(json.dumps(PLAN), encoding="utf-8")
    prs = dk.blank_deck(13.333, 7.5)
    slides = [dk.add_slide(prs), dk.add_slide(prs)]
    for sid, n in placements:
        ims.slot_picture(slides[n - 1], PLAN, sid, 0.6, 0.8, 3.0, 3.0, image_dir=td)
    for i, line in enumerate(lines2):
        dk.text(slides[1], 4.0, 1.0 + 0.6 * i, 8, 0.6, [[(line, 14, dk.DEEP, False, False)]])
    p = td / "deck.pptx"
    prs.save(str(p))
    return p


def found(td, p):
    f, _ = cis.check(str(p), {"imagery": "series", "plan": str(Path(td) / "series.json")}, td)
    return {c: (s, w) for s, c, w in f}


# a NEGATED label is not a label: "non-fictional" / "非虚构" contain "fictional" / "虚构"
for neg in ("A non-fictional account of the studio", "这是一个非虚构的故事"):
    td = Path(tempfile.mkdtemp())
    p = build(td, lines2=(neg,))
    check("GENERATED PERSON NAMED" in found(td, p), "a persona beside {!r} still has no fictional label".format(neg))
td = Path(tempfile.mkdtemp())
p = build(td)
check("GENERATED PERSON NAMED" not in found(td, p), "a real 'Illustrative persona' label still counts")
# a slot placed twice, or on another slide than its plan says, is said (it was silently overwritten)
td = Path(tempfile.mkdtemp())
p = build(td, placements=(("maker", 1), ("mira", 2), ("maker", 2)))
f = found(td, p)
check("SLOT PLACED TWICE" in f and "1" in f["SLOT PLACED TWICE"][1] and "2" in f["SLOT PLACED TWICE"][1], "a slot placed on two slides is reported: {}".format(sorted(f)))
td = Path(tempfile.mkdtemp())
p = build(td, placements=(("maker", 2), ("mira", 2)))
f = found(td, p)
check("SLOT ON ANOTHER SLIDE" in f, "a slot placed on another slide than planned is reported: {}".format(sorted(f)))
# series-qc.json older than an image it judged is stale
td = Path(tempfile.mkdtemp())
p = build(td)
ims.qc(PLAN, td, plan_path=str(td / "series.json"))
time.sleep(0.05)
os.utime(td / "slide-01-maker.png", None)
f = found(td, p)
check("SERIES QC STALE" in f and "slide-01-maker" in f["SERIES QC STALE"][1], "an image regenerated after qc makes the report stale: {}".format(sorted(f)))
# prompts(): a relative out_dir still writes ABSOLUTE item paths (a generator run from another folder found nothing)
cwd = os.getcwd()
try:
    os.chdir(tempfile.mkdtemp())
    items = ims.prompts(PLAN, "gen")
    check(all(Path(it["path"]).is_absolute() for it in items), "prompts() writes absolute paths: {}".format(items[0]["path"]))
finally:
    os.chdir(cwd)
# qc(): a contact-sheet failure is SAID, not swallowed
import image_qc
_cs = image_qc.contact_sheet
image_qc.contact_sheet = lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
err = io.StringIO()
try:
    with contextlib.redirect_stderr(err):
        ims.qc(PLAN, td, plan_path=str(td / "series.json"))
finally:
    image_qc.contact_sheet = _cs
check("contact" in err.getvalue().lower() and "disk full" in err.getvalue(), "a contact-sheet failure is printed: {!r}".format(err.getvalue()[:200]))
# generate_images_openai: an explicit --size is honoured; moderation is not sent to /images/edits (the SDK's edit() has
# no such parameter — only generate() does)
import generate_images_openai as gio
item = {"aspect": 0.66, "prompt": "x", "filename": "a.png"}
check(gio._size_for(item, None) != "1024x1024" and gio._size_for(item, "1024x1024") == "1024x1024",
      "explicit --size wins; without it the item's aspect picks: {} / {}".format(gio._size_for(item, None), gio._size_for(item, "1024x1024")))
sent = []
gio._request_image, _ri = (lambda key, payload, **kw: sent.append(payload) or {}), gio._request_image
gio._write_response_image, _wr = (lambda result, out: None), gio._write_response_image
try:
    base = dict(model="gpt-image-1", size=None, quality="high", output_format="png", background=None, moderation="low", timeout=5, retries=0)
    gio._generate_item(item, Path(tempfile.mkdtemp()) / "a.png", argparse.Namespace(style_ref=None, **base), "k")
    gio._generate_item(item, Path(tempfile.mkdtemp()) / "a.png", argparse.Namespace(style_ref=str(td / "slide-01-maker.png"), **base), "k")
finally:
    gio._request_image, gio._write_response_image = _ri, _wr
check(sent and sent[0].get("moderation") == "low" and "moderation" not in sent[1], "moderation goes to generations only: {}".format([sorted(s_) for s_ in sent]))
# chroma_cutout has a runnable --example, and the series reference says where series.json may live
import sigs
check("chroma_cutout" in sigs.EXAMPLES, "chroma_cutout has a runnable --example")
ref = (ROOT / "references" / "image-generation.md").read_text(encoding="utf-8")
check("absolute" in ref and "relative to the deck" in ref, "the reference says series.json is absolute or relative to the deck folder")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_image_series_minors] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
