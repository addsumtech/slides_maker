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
DEFAULT_CHROMA = "00B140"
HEX6 = re.compile(r"^[0-9A-Fa-f]{6}$")
FLOOR_MEANING, FLOOR_ART, FLOOR_SUBJECT = 24, 24, 12


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
        seen.add(sid)
        if not (isinstance(s.get("slide"), int) and s["slide"] >= 1):
            out.append(tag + ": slide must be the deck slide number (>= 1)")
        fr = s.get("frame") or {}
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
        if kind == "persona" and not (isinstance(s.get("persona_label"), str) and s["persona_label"].strip()):
            out.append(tag + ": a persona needs persona_label — the visible 'fictional' label set on its slide")
        if reason_width(s.get("subject")) < FLOOR_SUBJECT:
            out.append(tag + ": subject must say what is in the picture (>= {} wide)".format(FLOOR_SUBJECT))
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
        if not isinstance(s.get("cutout", False), bool):
            out.append(tag + ": cutout must be true or false")
        fo = s.get("focus")
        if fo is not None and not (isinstance(fo, (list, tuple)) and len(fo) == 2
                                   and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in fo)):
            out.append(tag + ": focus must be [fx, fy] within 0..1")
    k = plan.get("key")
    if k is not None and k not in seen:
        out.append("key: {!r} is not a slot id".format(k))
    return out
