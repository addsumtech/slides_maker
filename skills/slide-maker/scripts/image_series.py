#!/usr/bin/env python3
"""image_series — an ART-DIRECTED IMAGE SERIES for an image-led deck (`imagery: series`).

Studied 2026-10-03: the 33 image-led decks of skillry.dev carry a series-consistent image on nearly
every page; this skill could give a few slides a plate, each prompted alone, and no image held another's
look. The series is planned first (`series.json`), checked here, prompted as one series, generated
key-first with the key as a STYLE reference, cut out on a chroma key where the design wants a sticker,
QC'd against the key, and placed by slot with a provenance tag the gates read from the file.

    python3 scripts/image_series.py check series.json
    python3 scripts/image_series.py prompts series.json <out_dir>
    python3 scripts/image_series.py qc series.json --dir <generated_dir>

The plan is the contract — every slot says what its image MEANS on its slide (a slot with nothing to
say does not exist); a real, specific subject is never generated (REFERENT RULE); people follow the
user's rule: generic people yes, a fictional persona only with a visible label, real people never.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deckkit import PIC_SHAPES  # noqa: E402
from written_reason import reason_width  # noqa: E402

KINDS = ("scene", "object", "generic-person", "persona", "illustration")
NOT_GENERATABLE = ("team-member", "customer", "testimonial", "real-person")
REFERENTS = ("generic-concrete", "stylized", "real-specific")
RENDERS = ("photo", "illustration")
FRAME_SHAPES = ("rect",) + tuple(PIC_SHAPES)
CHROMA_MIN_DE = 30.0   # a palette colour closer than this to the key colour would be keyed away with it
SLOT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
CHROMAS = ("00B140", "FF00FF")
# subjects whose OWN colour is the key's: keyed, they lose themselves (measured: green leaves on green)
KEY_COLOURED = {
    "00B140": re.compile(r"\b(green|leaf|leaves|leafy|plants?|seedlings?|sprouts?|herbs?|basil|mint|lettuce|"
                         r"cucumbers?|grass|moss|ferns?|cact(?:us|i)|succulents?|lime|spinach|kale|broccoli|"
                         r"peas?)\b|绿|叶|幼苗|嫩芽|草|植物|生菜|黄瓜|青菜|菠菜|苔|仙人掌|多肉|薄荷|豆角", re.I),
    "FF00FF": re.compile(r"\b(pink|magenta|purple|violet|fuchsia|orchids?|beet(?:root)?s?|lavender|plum)\b"
                         r"|粉色|粉红|紫|玫红|洋红|薰衣草|甜菜", re.I),
}
DEFAULT_CHROMA = "00B140"
HEX6 = re.compile(r"^[0-9A-Fa-f]{6}$")
FLOOR_MEANING, FLOOR_ART, FLOOR_SUBJECT = 24, 24, 12
# A subject that NAMES people is a person slot whatever kind it was given: measured 2026-10-03, a
# "scene" for "volunteers' hands repairing a lamp" came back as four people, and the people gate only
# reads person kinds. Bare 人 is not a word here (人工, 人行道); the CJK list is people words.
PEOPLE = re.compile(
    r"\b(people|persons?|man(?![-‐])|men|woman|women|child(?:ren)?|boys?|girls?|volunteers?|visitors?|"
    r"neighbou?rs?|workers?|farmers?|students?|teachers?|famil(?:y|ies)|crowds?|couples?|customers?|"
    r"patients?|doctors?|nurses?|chefs?|artisans?|potters?|gardeners?|grand(?:mother|father|parents?)s?|"
    r"elderly|adults?|teen(?:ager)?s?)((?:'|’)s|s(?:'|’))?\b"
    r"|人们|行人|路人|老人|孩子|儿童|小孩|志愿者|邻居|农民|学生|老师|家人|一家人|居民|顾客|(?<!手)工人|"
    r"妈妈|爸爸|奶奶|爷爷|女孩|男孩|女士|先生|手艺人|园丁|陶艺师|师傅|游客|观众|人群", re.I)
# a possessive names a person only when their body follows ("a potter's hands"); "a potter's wheel",
# "a chef's knife" are objects (final review, 2026-10-03). Words that are mostly objects — maker, face,
# baby, kid, portrait, 用户 — are not in the list at all.
_BODY = re.compile(r"\s+(?:[\w-]+\s+)?(hands?|fingers?|arms?|face|faces|eyes|smile|feet|shoulders?|back)\b", re.I)


def _names_people(subject):
    for m in PEOPLE.finditer(subject or ""):
        if m.lastindex and m.group(2) and not _BODY.match(subject[m.end():]):
            continue
        return m.group(0)
    return None


def _q(x):
    """A path as ONE shell word, so a printed command runs as printed in "My Deck 菜园/" too."""
    return shlex.quote(str(x))


def load(path):
    path = Path(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError("image_series: cannot read the plan {} — {}".format(path.name, e)) from None


def _lab(hex6):
    """sRGB hex -> CIE L*a*b* (D65)."""
    r, g, b = (int(hex6[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    x = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
    y = (0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])
    z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
    f = [t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116 for t in (x, y, z)]
    return (116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2]))


def _de(a, b):
    return math.dist(_lab(a), _lab(b))


def key_id(plan):
    return plan.get("key") or (plan.get("slots") or [{}])[0].get("id")


def slot(plan, slot_id):
    for s in plan.get("slots") or []:
        if s.get("id") == slot_id:
            return s
    raise KeyError("image_series: no slot {!r} — the plan has {}".format(
        slot_id, [s.get("id") for s in plan.get("slots") or []]))


def check(plan):
    """Problems with a series plan, each naming the slot and the fix; [] when valid."""
    out = []
    if not isinstance(plan, dict):
        return ["the plan must be a JSON object"]
    if reason_width(plan.get("art_direction")) < FLOOR_ART:
        out.append("art_direction: one line that a stranger could paint from (>= {} wide; CJK counts 2)"
                   .format(FLOOR_ART))
    pal = plan.get("palette")
    if not (isinstance(pal, list) and 2 <= len(pal) <= 8 and all(isinstance(p, str) and HEX6.match(p.lstrip("#")) for p in pal)):
        out.append("palette: 2-8 'RRGGBB' hex colours, got {!r}".format(pal))
        pal = []
    render = plan.get("render")
    if render not in RENDERS:
        out.append("render: one of {} (it goes verbatim into every prompt), got {!r}".format(RENDERS, render))
    chroma = str(plan.get("chroma") or DEFAULT_CHROMA).lstrip("#").upper()
    if chroma not in CHROMAS:
        out.append("chroma: one of {} (the cut-out key colour), got {!r}".format(CHROMAS, chroma))
    else:
        near = [p for p in pal if _de(p.lstrip("#"), chroma) < CHROMA_MIN_DE]
        if near:
            other = [c for c in CHROMAS if c != chroma][0]
            out.append("chroma {}: too close to palette colour(s) {} — the key would eat the subject; set "
                       "\"chroma\": \"{}\"".format(chroma, near, other))
    slots = plan.get("slots")
    if not isinstance(slots, list) or not slots:
        out.append("slots: at least one slot")
        return out
    seen = set()
    for i, s in enumerate(slots):
        sid = s.get("id") if isinstance(s, dict) else None
        tag = "slot {!r}".format(sid if sid else i)
        if not isinstance(s, dict):
            out.append(tag + ": must be an object")
            continue
        if not (isinstance(sid, str) and SLOT_ID.match(sid)):
            out.append(tag + ": id must match [a-z0-9-] (1-40 chars), e.g. 'hero' or 's03-kettle'")
        elif sid in seen:
            out.append(tag + ": duplicate id")
        else:
            seen.add(sid)
        sl_ = s.get("slide")
        if not (isinstance(sl_, int) and not isinstance(sl_, bool) and sl_ >= 1):
            out.append(tag + ": slide must be the deck slide number (>= 1)")
        fr = s.get("frame")
        if not isinstance(fr, dict):
            out.append(tag + ": frame must be an object {\"shape\": …, \"w\": …, \"h\": …}")
            fr = {}
        if fr.get("shape") not in FRAME_SHAPES:
            out.append(tag + ": frame.shape must be one of {}".format(FRAME_SHAPES))
        if not all(isinstance(fr.get(k), (int, float)) and fr.get(k) > 0 for k in ("w", "h")):
            out.append(tag + ": frame needs w and h > 0 (inches, the box it will fill)")
        kind = s.get("kind")
        if kind in NOT_GENERATABLE:
            out.append(tag + ": kind {!r} is not generatable — team members, customers, testimonials and "
                       "real people get a REAL photo (the user's own, or fetch_images.py) or no portrait"
                       .format(kind))
        elif kind not in KINDS:
            out.append(tag + ": kind must be one of {}".format(KINDS))
        if kind in KINDS and kind not in ("generic-person", "persona"):
            who = _names_people(str(s.get("subject") or ""))
            if who:
                out.append(tag + ": the subject names people ({!r}) — if no person is meant, rephrase the subject; "
                           "if one is, set kind 'generic-person' (or 'persona' with its label), so the people "
                           "rule is checked on its slide".format(who))
        if kind == "persona" and not (isinstance(s.get("persona_label"), str) and s["persona_label"].strip()):
            out.append(tag + ": a persona needs persona_label — the visible 'fictional' label set on its slide")
        if reason_width(s.get("subject")) < FLOOR_SUBJECT:
            out.append(tag + ": subject must say what is in the picture (>= {} wide)".format(FLOOR_SUBJECT))
        else:
            import generate_images_codex as _gic
            if len(_gic.subject_terms(str(s.get("subject")))) < _gic.SERIES_MIN_SUBJECT_TERMS:
                out.append(tag + ": the subject names no THING a stranger could picture (only style/mood "
                           "words: {!r}) — say what is in the picture".format(s.get("subject")))
        if reason_width(s.get("meaning")) < FLOOR_MEANING:
            out.append(tag + ": meaning — what this image SAYS on its slide (>= {} wide). A slot with "
                       "nothing to say does not exist".format(FLOOR_MEANING))
        if not (isinstance(s.get("alt"), str) and s["alt"].strip()):
            out.append(tag + ": alt text is required (what a screen reader says)")
        ref = s.get("referent")
        if ref == "real-specific":
            out.append(tag + ": a real, specific subject is never generated (REFERENT RULE) — use a real "
                       "photo, or declare referent 'stylized' with render 'illustration'")
        elif ref not in REFERENTS:
            out.append(tag + ": referent must be one of {}".format(REFERENTS))
        elif ref == "stylized" and render != "illustration":
            out.append(tag + ": a stylized referent needs render 'illustration' — a photographic fake of a "
                       "real subject is the fidelity bug the REFERENT RULE exists for")
        if s.get("cutout") is True and chroma in CHROMAS:
            hit = KEY_COLOURED[chroma].search(str(s.get("subject") or ""))
            if hit:
                other = [c for c in CHROMAS if c != chroma][0]
                out.append(tag + ": a cut-out of {!r} on the {} key would lose the subject's own colour — set "
                           "\"chroma\": \"{}\"".format(hit.group(0), chroma, other))
        if not isinstance(s.get("cutout", False), bool):
            out.append(tag + ": cutout must be true or false")
        fo = s.get("focus")
        if fo is not None and not (isinstance(fo, (list, tuple)) and len(fo) == 2
                                   and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in fo)):
            out.append(tag + ": focus must be [fx, fy] within 0..1")
    k = plan.get("key")
    if k is not None and not (isinstance(k, str) and k in seen):
        out.append("key: {!r} is not a slot id".format(k))
    else:
        kid = key_id(plan)
        ks = next((x for x in slots if isinstance(x, dict) and x.get("id") == kid), {})
        if ks.get("cutout"):
            out.append("key: {!r} is a cut-out — the series' look is READ from the key image, so it must be a "
                       "graded picture; set \"key\" to a scene slot".format(kid))
    return out


RENDER_CLAUSE = {
    "photo": "Render: a natural photograph — real light, real materials, believable depth of field.",
    "illustration": ("Render: a hand-made illustration, NOT a photograph — visible drawn or painted marks, "
                     "flat or textured planes; it must not look photographic."),
}


def _aspect_words(w, h):
    r = w / float(h)
    if r >= 1.6:
        return "a wide landscape composition ({:.2f}:1)".format(r)
    if r <= 0.65:
        return "a tall portrait composition (1:{:.2f})".format(1 / r)
    return "a near-square composition ({:.2f}:1)".format(r)


def _stop(text):
    """End a sentence in its own script's full stop: a Chinese subject gets 。, a Latin one gets '.'."""
    t = str(text).rstrip().rstrip("。.")
    return t + ("。" if t and "\u3000" <= t[-1] <= "\u9fff" else ".")


def build_prompt(plan, s):
    pal = ", ".join("#" + p.lstrip("#").upper() for p in plan.get("palette") or [])
    chroma = "#" + str(plan.get("chroma") or DEFAULT_CHROMA).lstrip("#").upper()
    fr = s["frame"]
    lines = [
        "Use case: one image of an art-directed SERIES for a presentation deck — every image in the "
        "series must read as made by the same hand.",
        "Subject: {}".format(_stop(s["subject"])),
        "Art direction (shared by the whole series): {}".format(_stop(plan["art_direction"])),
        "Palette: {} — stay within it.".format(pal),
        RENDER_CLAUSE[plan["render"]],
        "Composition: {}; the subject centred with generous margin so the {} frame's crop keeps it "
        "whole.".format(_aspect_words(fr["w"], fr["h"]), fr["shape"]),
    ]
    cz = s.get("calm_zone")
    if cz and cz != "none":
        lines.append("Leave a calm, low-detail area at {} for text set over the image.".format(cz))
    if s.get("cutout"):
        lines.append("Background: isolated on a perfectly flat, uniform {} background — no shadow, gradient "
                     "or texture on the background; the whole subject inside the frame with margin on every "
                     "side; no {} anywhere in the subject.".format(chroma, chroma))
    if s.get("kind") in ("generic-person", "persona"):
        lines.append("People: ordinary, non-identifiable people — not a portrait of any real or famous person.")
    lines.append("Content rules: no text, letters, numbers, signage, logos or watermarks anywhere in the image.")
    return "\n".join(lines)


def prompts(plan, out_dir, plan_path=None):
    out_dir = Path(out_dir).resolve()          # absolute: a generator run from another folder must find them
    out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for s in plan["slots"]:
        fn = "slide-{:02d}-{}.png".format(s["slide"], s["id"])
        items.append({"id": s["id"], "slide": s["slide"], "filename": fn, "orientation": "auto",
                      "subject": s["subject"],
                      **({"series_plan": str(Path(plan_path).resolve())} if plan_path else {}),
                      "aspect": round(s["frame"]["w"] / float(s["frame"]["h"]), 3),
                      "path": str(out_dir / fn), "prompt": build_prompt(plan, s)})
    (out_dir / "image_prompt_manifest.json").write_text(
        json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return items


# Calibrated on REAL series (2026-10-03, metered gpt-image, key image as style reference): a warm photo
# series measured colour distance 2.1-12.9 and hue 0.07-0.19 from its key, a watercolour series 6.0-7.0
# and 0.07-0.10, and a planted cold-neon picture of the same subject 44.0 and 0.86. Both thresholds sit
# in that gap; a synthetic pair would have flattered them.
DE_MAX = 25.0      # mean-colour distance (CIE76) from the key beyond which an image is OFF-SERIES
HIST_MAX = 0.6     # hue-histogram distance (L1/2) beyond which an image is OFF-SERIES
LOW_SAT = 0.08     # mean saturation below which a picture's hue histogram is noise
# ASPECT compares the image with what a generator CAN make for the frame — between 2:3 and 16:9 (the
# metered path's sizes; the Codex tool steers by prompt within about the same range) — on a log scale,
# so 1:1-vs-3:2 and 3:2-vs-1:1 are the same distance. A 1:4 arch used to be told "regenerate" forever.
GEN_ASPECT = (2 / 3.0, 16 / 9.0)
ASPECT_TOL = 1.35  # image aspect / reachable aspect (or its inverse) beyond which the crop loses too much


def image_stats(path, *, exclude=None):
    """Mean Lab, saturation, luminance spread and a saturation-weighted hue histogram. `exclude` (an
    'RRGGBB' key colour) drops the pixels near it — a cut-out slot is generated on the key, and its
    background must not be what the series is compared on."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    size = im.size
    im.thumbnail((128, 128))
    px = list(im.getdata())
    if exclude:
        kc = tuple(int(exclude[i:i + 2], 16) for i in (0, 2, 4))
        keep = [p for p in px if math.dist(p, kc) > 60]
        if len(keep) >= max(16, len(px) // 50):
            px = keep
            im = Image.new("RGB", (len(px), 1))
            im.putdata(px)
    n = float(len(px))
    mean = tuple(sum(p[i] for p in px) / n for i in range(3))
    lab = _lab("{:02X}{:02X}{:02X}".format(*(int(round(c)) for c in mean)))
    hsv = list(im.convert("HSV").getdata())
    sat = sum(p[1] for p in hsv) / (255.0 * n)
    lum = [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px]
    mu = sum(lum) / n
    lum_std = (sum((v - mu) ** 2 for v in lum) / n) ** 0.5
    hist = [0.0] * 12
    for h_, s_, v_ in hsv:
        hist[h_ * 12 // 256] += s_ / 255.0
    tot = sum(hist) or 1.0
    return {"lab": lab, "sat": sat, "lum_std": lum_std, "hue_hist": [v / tot for v in hist],
            "size": size}


def _hist_d(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / 2.0


def cutout(plan, gen_dir):
    """Key every cut-out slot's image off the PLAN's chroma colour -> {slot id: .cut.png path or the
    refusal}. A slot generated on any other ground is refused, never keyed: keying cream paper also
    removes the subject's cream highlights."""
    import image_fx
    key = str(plan.get("chroma") or DEFAULT_CHROMA).lstrip("#").upper()
    res = {}
    for s in plan["slots"]:
        if not s.get("cutout"):
            continue
        f = Path(gen_dir) / "slide-{:02d}-{}.png".format(s["slide"], s["id"])
        if not f.exists():
            res[s["id"]] = "MISSING: no image at {} — generate it".format(f.name)
            continue
        try:
            res[s["id"]] = image_fx.chroma_cutout(str(f), key=key)
        except ValueError as e:
            res[s["id"]] = "REFUSED: {}".format(e)
    return res


def qc(plan, gen_dir, *, de_max=None, hist_max=None, plan_path=None):
    """Compare every slot's image with the KEY image; flag MISSING / OFF-SERIES / ASPECT / CUTOUT and the
    per-file image_qc flags. Writes series-qc.json beside the images and returns the report."""
    import image_qc
    de_max = DE_MAX if de_max is None else de_max
    hist_max = HIST_MAX if hist_max is None else hist_max
    gen_dir = Path(gen_dir)
    kid = key_id(plan)
    # an acknowledgement ("kept on purpose: <why>") survives every re-run — qc used to rewrite it to {}
    ack = {}
    try:
        old = json.loads((gen_dir / "series-qc.json").read_text(encoding="utf-8")).get("acknowledged") or {}
        ack = {k: v for k, v in old.items() if isinstance(k, str) and isinstance(v, str)}
    except (OSError, ValueError, AttributeError):
        pass
    files = {s["id"]: gen_dir / "slide-{:02d}-{}.png".format(s["slide"], s["id"]) for s in plan["slots"]}
    chroma = str(plan.get("chroma") or DEFAULT_CHROMA).lstrip("#").upper()
    key_stats = (image_stats(files[kid], exclude=chroma if slot(plan, kid).get("cutout") else None)
                 if files[kid].exists() else None)
    rows, outliers, recs = [], [], []
    for s in plan["slots"]:
        f, flags, row = files[s["id"]], [], {"id": s["id"], "file": str(files[s["id"]])}
        if not f.exists():
            flags.append("MISSING: no image at {} — generate it".format(f.name))
        else:
            st = image_stats(f, exclude=chroma if s.get("cutout") else None)
            w, h = st["size"]
            fa = s["frame"]["w"] / float(s["frame"]["h"])
            reach = min(max(fa, GEN_ASPECT[0]), GEN_ASPECT[1])
            if abs(math.log((w / float(h)) / reach)) > math.log(ASPECT_TOL):
                flags.append("ASPECT: {}x{} ({:.2f}:1) is far from the {:.2f}:1 frame (a generator reaches {:.2f}:1 "
                             "for it) — regenerate this slot".format(w, h, w / float(h), fa, reach))
            # a cut-out is an isolated OBJECT: its colour is the object's, not the series' grade, so it
            # is not colour-compared (measured: a cream kettle read 30.3 from a warm hall scene)
            if key_stats is not None and s["id"] != kid and not s.get("cutout"):
                de = math.dist(st["lab"], key_stats["lab"])
                # hue is NOISE when both pictures are near-grey (a black-and-white series): a hair of warm
                # tint against a hair of cool tint read 1.00 — the colour distance still catches a real outlier
                hd = (0.0 if max(st["sat"], key_stats["sat"]) < LOW_SAT
                      else _hist_d(st["hue_hist"], key_stats["hue_hist"]))
                row.update(delta_e=round(de, 1), hist=round(hd, 2))
                if de > de_max or hd > hist_max:
                    flags.append("OFF-SERIES: colour distance {:.1f} (max {}) / hue {:.2f} (max {}) from the key "
                                 "— regenerate with --style-ref <key>".format(de, de_max, hd, hist_max))
            if s.get("cutout"):
                cut = f.with_name(f.stem + ".cut.png")
                if not cut.exists():
                    flags.append("CUTOUT: no {} — run: python3 scripts/image_series.py cutout {} "
                                 "--dir {}".format(cut.name, _q(plan_path or "<series.json>"), _q(gen_dir)))
                elif cut.stat().st_mtime < f.stat().st_mtime:
                    flags.append("CUTOUT: {} is older than {} (regenerated after it was cut out) — run: python3 "
                                 "scripts/image_series.py cutout {} --dir {}".format(
                                     cut.name, f.name, _q(plan_path or "<series.json>"), _q(gen_dir)))
            rec = image_qc.inspect(str(f))
            # a cut-out's flat key IS uniform bands, and an illustration's paper margin is its medium —
            # neither is a padded export (measured: LETTERBOX on 4 of 5 watercolours); on the sheet too
            if s.get("cutout") or plan.get("render") == "illustration":
                rec["flags"] = [fl for fl in rec.get("flags", []) if fl[0] != "LETTERBOX"]
            recs.append(rec)
            flags += ["{}: {}".format(c, m) for c, m in rec.get("flags", [])]
        row["flags"] = flags
        if flags and reason_width(ack.get(s["id"])) >= FLOOR_SUBJECT:
            row["acknowledged"] = ack[s["id"]]
        if flags and s["id"] != kid and any(x.startswith("OFF-SERIES") for x in flags):
            outliers.append(s["id"])
        rows.append(row)
    rep = {"key": kid, "slots": rows, "outliers": outliers, "acknowledged": ack}
    (gen_dir / "series-qc.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if recs:
        try:
            image_qc.contact_sheet(recs, str(gen_dir / "_series_contact.png"))
        except Exception as exc:                 # said, not swallowed: the sheet is how the series is looked at
            print("image_series qc: the contact sheet could not be written ({}: {}) — the report above still "
                  "stands; look at the images one by one".format(type(exc).__name__, exc), file=sys.stderr)
    return rep

def slot_picture(slide, plan, slot_id, x, y, w, h, *, image_dir, sticker=False):
    """Place a series slot's image into (x, y, w, h) with the PLAN's frame, focus and alt text, and tag it
    `+gen.<slot>` — the gates read the tag from the saved file. A cut-out slot places its keyed PNG;
    `sticker=True` places that cut-out with a die-cut border (image_fx.sticker_outline), still tagged."""
    import deckkit as dk
    s = slot(plan, slot_id)
    base = Path(image_dir) / "slide-{:02d}-{}.png".format(s["slide"], s["id"])
    path = base.with_name(base.stem + ".cut.png") if s.get("cutout") else base
    if sticker and not s.get("cutout"):
        raise ValueError("slot_picture(): sticker=True needs a cut-out slot — {!r} has \"cutout\": false".format(slot_id))
    if not path.exists():
        raise FileNotFoundError("slot_picture(): no image at {} — make it: python3 scripts/generate_images_codex.py "
                                "<manifest> --only {}{}".format(
                                    path, s["id"], "  then: python3 scripts/image_series.py cutout <series.json> "
                                    "--dir {}".format(_q(image_dir)) if s.get("cutout") else ""))
    if s.get("cutout") and base.exists() and base.stat().st_mtime > path.stat().st_mtime:
        raise ValueError("slot_picture(): {} is OLDER than {} — the slot was regenerated after it was cut out; "
                         "run: python3 scripts/image_series.py cutout <series.json> --dir {}".format(
                             path.name, base.name, _q(image_dir)))
    if sticker:
        import image_fx
        path = Path(image_fx.sticker_outline(str(path)))
    if s.get("cutout"):
        pic = dk.picture(slide, str(path), x, y, w, h, fit="contain", alt=s["alt"])
    else:
        shape = None if s["frame"]["shape"] == "rect" else s["frame"]["shape"]
        pic = dk.picture(slide, str(path), x, y, w, h, fit="cover", shape=shape,
                         focus=tuple(s.get("focus") or (0.5, 0.5)), alt=s["alt"])
    dk._compose_tag(pic, gen=s["id"])
    return pic


def _print_problems(probs):
    for p in probs:
        print("  - " + p)
    print("image_series: {} problem(s) — fix the plan, then re-run".format(len(probs)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate series.json")
    c.add_argument("plan")
    p = sub.add_parser("prompts", help="write image_prompt_manifest.json for generate_images_codex.py")
    p.add_argument("plan")
    p.add_argument("out_dir")
    c2 = sub.add_parser("cutout", help="key every cut-out slot off the plan's chroma colour")
    c2.add_argument("plan")
    c2.add_argument("--dir", required=True, help="the folder the generator wrote the images into")
    q = sub.add_parser("qc", help="compare every generated image with the key image")
    q.add_argument("plan")
    q.add_argument("--dir", required=True, help="the folder the generator wrote the images into")
    a = ap.parse_args(argv)
    try:
        plan = load(a.plan)
    except ValueError as e:
        print(e)
        return 2
    probs = check(plan)
    if probs:
        _print_problems(probs)
        return 1
    if a.cmd == "check":
        print("image_series: {} slot(s), key {!r} — plan OK".format(len(plan["slots"]), key_id(plan)))
        print("NEXT: python3 scripts/image_series.py prompts {} {}".format(
            _q(a.plan), _q(Path(a.plan).resolve().parent / "assets" / "generated")))
        return 0
    if a.cmd == "cutout":
        res = cutout(plan, a.dir)
        bad_ = {k: v for k, v in res.items() if not str(v).endswith(".cut.png")}
        for k, v in res.items():
            print("  [{}] {}".format(k, v))
        if not res:
            print("image_series cutout: the plan has no cut-out slot")
        if not bad_:
            print("NEXT: python3 scripts/image_series.py qc {} --dir {}".format(_q(a.plan), _q(a.dir)))
        return 1 if bad_ else 0
    if a.cmd == "qc":
        rep = qc(plan, a.dir, plan_path=a.plan)
        qpath = Path(a.dir) / "series-qc.json"
        man = Path(a.dir) / "image_prompt_manifest.json"
        kid = rep["key"]
        key_img = Path(a.dir) / "slide-{:02d}-{}.png".format(slot(plan, kid)["slide"], kid)
        open_ = []
        for r in rep["slots"]:
            for f in r["flags"]:
                print("  [{}] {}".format(r["id"], f))
            if r["flags"] and r.get("acknowledged"):
                print("  [{}] acknowledged: {}".format(r["id"], r["acknowledged"]))
            elif r["flags"]:
                open_.append(r)
        for r in open_:
            if any(not f.startswith("CUTOUT") for f in r["flags"]):
                if r["id"] == kid:
                    print("  fix [{}] (the KEY — every other slot follows it): python3 scripts/generate_images_codex.py "
                          "{} --overwrite --only {}".format(r["id"], _q(man), _q(r["id"])))
                else:
                    print("  fix [{}]: python3 scripts/generate_images_codex.py {} --overwrite --only {} --style-ref {}"
                          .format(r["id"], _q(man), _q(r["id"]), _q(key_img)))
        print("image_series qc: {} slot(s), {} flagged ({} open), outliers {} — wrote {}".format(
            len(rep["slots"]), sum(1 for r in rep["slots"] if r["flags"]), len(open_), rep["outliers"] or "none", qpath))
        if open_:
            print("  To keep a flagged slot ON PURPOSE (the flag is the style itself), record why in {} -> "
                  "\"acknowledged\": {{\"<id>\": \"<the reason>\"}} and rerun qc.".format(qpath))
            print("NEXT: fix or acknowledge the slot(s) above, then rerun: python3 scripts/image_series.py qc {} --dir {}"
                  .format(_q(a.plan), _q(a.dir)))
            return 1
        print("NEXT: place each slot with image_series.slot_picture(slide, plan, slot_id, x, y, w, h, image_dir=...) "
              "and look at the contact sheet {}".format(Path(a.dir) / "_series_contact.png"))
        return 0
    items = prompts(plan, a.out_dir, plan_path=a.plan)
    man = Path(a.out_dir) / "image_prompt_manifest.json"
    print("image_series: wrote {} prompt(s) to {}".format(len(items), man))
    print("NEXT (the key image first, then LOOK at it): python3 scripts/generate_images_codex.py {} --only {}"
          .format(_q(man), _q(key_id(plan))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
