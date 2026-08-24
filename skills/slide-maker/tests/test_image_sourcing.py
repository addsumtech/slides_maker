#!/usr/bin/env python3
"""The sourced-photo pipeline: the code, and its agreement with the prose that teaches it.

The three scripts carry their own `--selftest` (behaviour, offline). This suite holds the
CROSS-FILE contracts that no single script can check about itself, because each of them is a place
where the skill has already drifted once:

  * the evidence-token grammar the GATE accepts must be the grammar the REFERENCE teaches — a
    checker that quietly speaks a different dialect rejects correct plans and, worse, accepts
    malformed ones (`check_reference_code.py` exists for the same class of drift);
  * both runtimes must require the same field. `render_deck.py` and `codex_delivery_gate.py`
    disagreeing about what an honest plan looks like has cost this repo before — one side spelled
    a key `path` and the other `png`, so a bridged run wrote the field its own gate demanded and
    the other rejected it;
  * the query ladder must actually widen. It exists because a six-word subject phrase returns
    ZERO on Commons (measured live), and a ladder that does not narrow toward distinctive terms
    would silently restore the false `none found` it was written to prevent.
"""
import ast
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

ok, bad = [], []


def check(cond, good, why=""):
    (ok if cond else bad).append(good if cond else "{}{}".format(good, why and " — " + why))


# ── the three scripts' own self-tests must pass (they are the behaviour suite) ────────────────
for script in ("fetch_images.py", "image_qc.py", "check_image_provenance.py"):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), "--selftest"],
                       capture_output=True, text=True)
    tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
    check(p.returncode == 0 and re.match(r"\d+ passed, 0 failed", tail[0]),
          "{} --selftest is green ({})".format(script, tail[0]),
          (p.stdout or "")[-400:])

import check_image_provenance as cip                                        # noqa: E402
import fetch_images as fi                                                   # noqa: E402

# ── 1. the gate's grammar IS the reference's grammar ──────────────────────────────────────────
REF = (SKILL / "references" / "image-generation.md").read_text(encoding="utf-8")
block = REF.split("Evidence token (the gate")[1] if "Evidence token (the gate" in REF else ""
check(bool(block), "references/image-generation.md still owns the evidence-token block",
      "the block moved or was renamed; this suite can no longer verify the grammar")

if block:
    # Each rung is taught as `- `token` — explanation`; take the leading code span of each.
    taught = re.findall(r"^\s*-\s+`([^`]+)`", block[:4000], re.M)
    taught = [t for t in taught if len(t) > 8]
    check(len(taught) >= 5,
          "{} token forms are taught in the reference".format(len(taught)),
          "found {}".format(taught))
    for t in taught:
        # The reference writes placeholders in <angle brackets>; fill them so the FORM can parse.
        sample = (t.replace("<origin>", "Wikimedia Commons").replace("<license>", "CC BY-SA 4.0")
                   .replace("<tool>", "codex").replace("<…>", "x"))
        sample = re.sub(r"<[^>]*>", "Commons, Openverse", sample)
        kind, _m = cip.parse_token(sample)
        check(kind is not None,
              "the gate parses the taught form {!r}".format(t[:52]),
              "the reference teaches a token the gate would reject as BAD TOKEN")

# A form the reference does NOT sanction must still be refused — a parser that accepts everything
# is not a gate.
check(cip.parse_token("slide 4 | campus | photo.jpg")[0] is None,
      "a bare filename is still refused (the parser did not go permissive)")
check(cip.parse_token("slide 4 | from the internet")[0] is None,
      "an unsanctioned phrase is refused")

# ── 2. both runtimes require the field ────────────────────────────────────────────────────────
rd = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
m = re.search(r"DESIGN_FIELDS = \((.*?)\)", rd, re.S)
fields = set(re.findall(r'"([a-z_]+)"', m.group(1))) if m else set()
check("image_sources" in fields,
      "render_deck.py requires design_plan.image_sources",
      "DESIGN_FIELDS = {}".format(sorted(fields)))
check("motif_generates" in fields and "style_pick" in fields,
      "...alongside the fields it shipped with (the tuple was extended, not replaced)")

cdg = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")
check("design.image_sources missing" in cdg,
      "codex_delivery_gate.py requires the same field, with its own message")
check('"image_sources": [' in cdg,
      "...and the CODEX SCAFFOLD carries it",
      "a capability that is not in the example scaffold is a capability that does not get produced")
check("check_image_provenance" in cdg and "check_image_provenance" in rd,
      "both gate paths call the SAME checker rather than re-implementing the contract")

# ── 3. the query ladder widens, and does not crash on non-space-delimited scripts ──────────────
lad = fi._query_ladder("Delft University of Technology aerial campus")
check(lad[0] == "Delft University of Technology aerial campus",
      "the ladder asks the EXACT subject phrase first (a widened query is a fallback, never the "
      "first move)")
check(len(lad) >= 3, "...then widens: {} rungs".format(len(lad)), str(lad))
check(all(len(lad[i + 1].split()) <= len(lad[i].split()) for i in range(len(lad) - 1)),
      "...monotonically — every rung is as broad or broader than the last", str(lad))
check("of" not in lad[-1].split() and "the" not in lad[-1].split(),
      "...and stop words are gone from the widest rung", str(lad))
check(len(set(x.lower() for x in lad)) == len(lad), "no rung is issued twice")

cjk = fi._query_ladder("阿姆斯特丹运河")
check(cjk == ["阿姆斯特丹运河"],
      "a Chinese subject tokenises as one term and the ladder collapses to it — correct, not a "
      "crash (this skill builds decks in any language)", str(cjk))
check(fi._query_ladder("") == [] and fi._query_ladder(None) == [],
      "an empty subject yields no queries rather than searching for nothing")

# ── 4. licence handling: the parts a credit line is built from ────────────────────────────────
check(fi._license_key("CC BY-SA 4.0") == "by-sa" and fi._license_key("CC0") == "cc0"
      and fi._license_key("Public Domain") == "pdm",
      "licence labels normalise to the keys --licenses speaks")
check(fi._license_key("All rights reserved") == "" and fi._license_key("") == "",
      "an unrecognised licence maps to NOTHING and is rejected upstream — never guessed free")
check(fi._attrib_required("by") and fi._attrib_required("by-sa")
      and not fi._attrib_required("cc0") and not fi._attrib_required("pdm"),
      "attribution obligation follows the licence family")
credit = fi._credit_line({"title": "Campus", "author": "X Photographer", "license": "CC BY-SA 4.0",
                          "page_url": "https://commons.example/File:Campus.jpg"})
check("X Photographer" in credit and "CC BY-SA 4.0" in credit and "commons.example" in credit,
      "a built credit line carries author + licence + source URL")

# ── 5. the ledger describes the file ON DISK, and names it once ───────────────────────────────
import tempfile                                                             # noqa: E402
import urllib.error                                                         # noqa: E402

_PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000004000000040802000000269309290000"
                     "001449444154789c63e41291638001260624809b03000ca800445e3a74ee00000000"
                     "49454e44ae426082")                       # a real 4x4 PNG


def _fake(url, timeout=20, binary=False):
    if binary:
        return _PNG
    if "commons" in url:
        return {"query": {"pages": {"1": {
            "title": "File:Campus Aerial.jpg",
            "imageinfo": [{"descriptionurl": "https://commons.example/File:Campus_Aerial.jpg",
                           "url": "https://u/Campus_Aerial.jpg",
                           "thumburl": "https://u/2400px-Campus_Aerial.jpg",
                           "width": 6000, "height": 4000,
                           "extmetadata": {"LicenseShortName": {"value": "CC0"},
                                           "Artist": {"value": "Anon"}}}]}}}}
    return {"results": []}


_real, fi._TRANSPORT = fi._TRANSPORT, _fake
try:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="imgsrc-"))
    got, _ = fi.fetch("campus aerial", tmp, subject="campus", slide=4)
    e = got[0]
    check(not e["file"].lower().endswith((".jpg.jpg", ".jpeg.jpeg", ".png.png")),
          "the filename does not double its extension when the source title already carries one",
          e["file"])
    check((e["width"], e["height"]) == (4, 4) and (e["orig_width"], e["orig_height"]) == (6000, 4000),
          "the ledger records the DOWNLOADED file's size, keeping the upload's size separately — "
          "a 6000px number must not vouch for the deck-sized file that actually landed",
          "{}x{} / orig {}x{}".format(e["width"], e["height"], e["orig_width"], e["orig_height"]))
    check(e["license"] == "CC0" and e["attribution_required"] is False,
          "a CC0 file carries no attribution obligation")
    check(fi.token_for(e).startswith("sourced — Wikimedia Commons (CC0"),
          "the emitted token is the sourced form the gate parses", fi.token_for(e))
    check(cip.parse_token(fi.token_for(e))[0] == "sourced",
          "...and the GATE agrees — emitter and parser cannot drift apart silently")
    check(fi.none_found_token(("commons", "openverse")).startswith("searched (Commons, Openverse)"),
          "the not-found rung NAMES the origins tried, as the reference requires")
    check(cip.parse_token(fi.none_found_token(("commons", "openverse")))[0] == "searched",
          "...and that rung parses too")
finally:
    fi._TRANSPORT = _real


# ── 6. grounding a GENERATED plate: observed facts, and governed reference conditioning ────────
import image_prompts as ip                                                  # noqa: E402
import generate_images_codex as gic                                         # noqa: E402

facts = ip.parse_facts("""
## The EWI tower
- grey concrete slab, roughly 20 storeys, red accent panels
- flat campus parkland, young birches, red-brick paths
## 2
- a wide bore, a patient table, a shielded control window
""")
check(len(facts) == 2, "a visual-facts file parses into per-slide bullet lists", str(facts))
slide = {"title": "The EWI tower on the TU Delft campus", "notes": ""}
check(len(ip.facts_for(slide, 1, facts)) == 2,
      "facts match a slide whose heading CONTAINS the fact key — nobody maintains exact strings")
check(len(ip.facts_for({"title": "The scanner", "notes": ""}, 2, facts)) == 1,
      "...and fall back to the slide INDEX when no heading matches")
check(ip.facts_for({"title": "Nothing here", "notes": ""}, 9, facts) == [],
      "an unmatched slide gets NO facts rather than another slide's")

prompt = ip.build_prompt(slide, 1, deck_size="16:9", style="editorial", calm_zone="left third",
                         facts=ip.facts_for(slide, 1, facts))
check("red accent panels" in prompt and "BIND" in prompt,
      "observed facts reach the prompt, marked as binding — the topicality gate counts nouns and "
      "cannot know what the thing looks like")
check("Observed subject facts" not in ip.build_prompt(slide, 1, deck_size="16:9", style="",
                                                      calm_zone=""),
      "...and a deck with no research is unchanged (the flag is additive)")

refdir = pathlib.Path(tempfile.mkdtemp(prefix="refs-"))
for n in ("slide-01-tower.jpg", "slide-01-park.jpg", "slide-02-other.jpg", "_ref-slide-01-x.jpg"):
    (refdir / n).write_bytes(_PNG)
r1 = gic.refs_for({"filename": "slide-01.png"}, refdir)
check([f.name for f in r1] == ["slide-01-park.jpg", "slide-01-tower.jpg"],
      "references are matched to a plate by its slide-NN stem", str([f.name for f in r1]))
check(gic.refs_for({"filename": "slide-07.png"}, refdir) == [],
      "an unmatched plate gets NO reference — a shared pool would steer a robot-arm plate with a "
      "campus photo, and a wrong reference looks like grounding")
check(all(not f.name.startswith("_ref-") for f in r1),
      "already-staged inputs are not re-adopted as references")

check(set(gic.REF_INTENTS) == {"generic-concrete", "stylized-illustration", "fallback-rung"},
      "the three sanctioned uses of a reference are enumerated", str(sorted(gic.REF_INTENTS)))
check("not look photographic" in gic._render_clause("stylized-illustration").lower()
      and "not look photographic" in gic._render_clause("fallback-rung").lower(),
      "the non-photographic RENDER MODE rides on the intents whose point is not being mistaken "
      "for a photograph")
check(gic._render_clause("generic-concrete") == "",
      "...and not on generic-concrete, where there is no real referent to fake")
check(gic._render_clause(None) == "", "no reference, no render-mode override")

_probe = subprocess.run([sys.executable, str(SCRIPTS / "generate_images_codex.py"),
                         str(SCRIPTS / "does-not-matter.json"), "--ref-dir", str(refdir),
                         "--dry-run"], capture_output=True, text=True)
check(_probe.returncode != 0 and "--ref-intent" in (_probe.stderr or ""),
      "--ref-dir without --ref-intent is a HARD STOP, not a default — the permissive reading of "
      "this flag produces a convincing fake photograph of a real building (measured)")


# ── 7. set-level checks: coherence, and not QC-ing our own outputs ─────────────────────────────
import image_qc as iq                                                       # noqa: E402
from PIL import Image                                                       # noqa: E402

setdir = pathlib.Path(tempfile.mkdtemp(prefix="qcset-"))
import random as _rnd                                                       # noqa: E402
_r = _rnd.Random(3)
colour = Image.new("RGB", (1600, 1000))
colour.putdata([(_r.randrange(120, 256), _r.randrange(0, 90), _r.randrange(0, 90))
                for _ in range(1600 * 1000)])
colour.save(setdir / "a-colour.png")
colour.convert("L").convert("RGB").save(setdir / "b-mono.png")
colour.rotate(180).save(setdir / "c-colour.png")
(setdir / "_contact_sheet.png").write_bytes((setdir / "a-colour.png").read_bytes())

recs = iq.inspect_dir(setdir)
flags = {r["file"]: {f[0] for f in r["flags"]} for r in recs}
check("MIXED TREATMENT" in flags.get("b-mono.png", set()),
      "MIXED TREATMENT catches the monochrome photo in a colour set — a set-level fault no "
      "per-file check can see, and the one a human spots the instant they open the contact sheet",
      str(flags))
check(not any("MIXED TREATMENT" in flags.get(f, set()) for f in ("a-colour.png", "c-colour.png")),
      "...and does not accuse the colour photos of it")
check("_contact_sheet.png" not in flags,
      "the pipeline's OWN outputs (leading underscore: the contact sheet, staged _ref- files) are "
      "not QC'd as candidates — the sheet used to report LETTERBOX on its own margins and to count "
      "itself in the set-level passes", str(sorted(flags)))


# ── 8. non-Latin subjects: the paths that were quietly Latin-only ──────────────────────────────
check(fi._safe_name("北京大学校园") == "北京大学校园"
      and fi._safe_name("東京タワー") == "東京タワー",
      "a CJK subject keeps its name in the filename — the ASCII-only sanitiser collapsed every "
      "Chinese and Japanese subject to the bare fallback, so an asset folder lost the one thing "
      "a filename is for", fi._safe_name("北京大学校园"))
check(fi._safe_name("Delft University of Technology.jpg").endswith(".jpg")
      and " " not in fi._safe_name("a b c"),
      "...while separators and shell-hostile punctuation are still replaced")
check(fi._safe_name("///") == "photo", "an all-punctuation title still falls back")

check(cip._weight("张伟") == 4 and cip._weight("John") == 4 and cip._weight("ab") == 2,
      "credit matching weighs CJK glyphs double — a two-character Chinese personal name carries "
      "as much signal as a four-letter Latin one, and a plain len() gate reported MISSING CREDIT "
      "on a correctly credited Chinese deck (measured)")

_cjk_led = {"entries": [{"file": "a.jpg", "license": "CC BY 4.0", "author": "张伟", "title": "校园",
                         "attribution_required": True, "status": "placed"}],
            "searches": [{"outcome": "found"}]}
_g = {"design_plan": {"image_sources": ["slide 1 | sourced — Wikimedia Commons (CC BY 4.0)"]}}
_real_dt = cip._deck_text
cip._deck_text = lambda pth: ("来源：校园照片 由 张伟 提供（cc by 4.0）" if pth == "CJK_OK"
                              else "完全无关的内容")
try:
    check(not [c for c, _ in cip.check(".", gates=_g, ledger=_cjk_led, pptx="CJK_OK")],
          "a Chinese credit line ON THE SLIDE clears the attribution check")
    check("MISSING CREDIT" in {c for c, _ in cip.check(".", gates=_g, ledger=_cjk_led, pptx="CJK_NO")},
          "...and its absence still fails — the fix widened the alphabet, it did not soften the rule")
finally:
    cip._deck_text = _real_dt

check(fi._query_ladder("北京大学 campus photo of the main gate")[0]
      == "北京大学 campus photo of the main gate"
      and len(fi._query_ladder("北京大学 campus photo of the main gate")) >= 3,
      "a MIXED CJK/Latin subject still widens through the ladder")

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print("\n{} passed, {} failed".format(len(ok), len(bad)))
raise SystemExit(1 if bad else 0)
