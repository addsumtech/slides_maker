#!/usr/bin/env python3
"""vl_native — page compositions of the NATIVE visual languages (ink, poster, cutpaper, drafting).

Imported by visual_languages only for those languages; the image-led four never load it. Each page PLANS its text
first (measured: the kit's _flow for horizontal text, vcol for vertical CJK, display for poster-scale type —
shrinking to each field's floor and refusing with VLTextOverflow past it), then draws its native art with that
text kept clear, then sets the text — so art never sits over words and z-order is art below type.
Nothing here invents a word: seal/highlight/project/icons come from the caller or are not drawn.
"""
from __future__ import annotations

import copy

import deckkit as dk
import native_art as na
import visual_languages as vl

COMPOSERS = {}     # language -> {page: fn(k, slide, fields, image) -> rects}
GROUNDS = {}       # language -> fn(k, slide): what every page of the language carries (new_slide)


def register(lang, page):
    def deco(fn):
        COMPOSERS.setdefault(lang, {})[page] = fn
        return fn
    return deco


def ctx(k):
    W, H = vl._canvas(k)
    return W, H, min(W, H) / 7.5, ("land" if W >= H * 1.2 else "port")


def text_of(fields, name):
    v = fields.get(name)
    return str(v).strip() if v is not None and str(v).strip() else None


def points_of(items):
    """2-4 points: strings, (head, line) pairs or {"head", "line"} dicts -> [(head, line or None)]."""
    if not isinstance(items, (list, tuple)) or not 2 <= len(items) <= 4:
        raise ValueError("points(): items= takes 2 to 4 points, got {!r}".format(items))
    out = []
    for it in items:
        if isinstance(it, dict):
            head, line = it.get("head"), it.get("line")
        elif isinstance(it, (list, tuple)):
            head, line = (list(it) + [None, None])[:2]
        else:
            head, line = it, None
        head = str(head or "").strip()
        if not head:
            raise ValueError("points(): every point needs its words — an empty one in {!r}".format(items))
        out.append((head, str(line).strip() if line is not None and str(line).strip() else None))
    return out


def _cjk(ch):
    o = ord(ch)
    return 0x3000 <= o <= 0x30FF or 0x3400 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or ch in "·—…"


def is_vertical(text):
    """Vertical only for CJK (Han/kana) with no Latin letters or digits — those would lie on their side."""
    t = "".join(ch for ch in (text or "") if not ch.isspace())
    if not t or any(ch.isascii() and ch.isalnum() for ch in t):
        return False
    return dk.script_of(t) in ("han", "kana") and all(_cjk(ch) for ch in t)


def _kit_on(k, ink=None, accent=None, mute=None):
    if not (ink or accent or mute):
        return k
    kk = copy.copy(k)
    kk.P = dict(k.P)
    if ink:
        kk.P["ink"] = ink
    if mute:
        kk.P["mute"] = mute
    if accent:
        kk.P["text_accents"] = [accent] + list(k.P["text_accents"][1:])
    return kk


def flow(k, slide, page, col, items, *, anchor="top", align="l", ink=None, accent=None, mute=None, start=None):
    """PLAN horizontal text with the kit's measured flow; returns (rects, draw). ink/accent/mute override the
    colours for text that sits on a card or panel instead of the ground."""
    if not items:
        return {}, (lambda: None)
    kk = _kit_on(k, ink, accent, mute)
    return vl._flow(kk, slide, page, col, items, anchor=anchor, align=align, start=start)


def _color(k, ckey):
    return k.color("text_accents") if ckey == "accent" else k.color("mute") if ckey == "mute" else k.color("ink")


def vcol(k, slide, right, top, h_max, text, field, *, color=None, spacing=0.12, max_cols=2):
    """PLAN CJK `text` set vertically, right edge at `right`: starts at the field's size, shrinks toward its floor,
    refuses past `max_cols` columns at the floor. Returns ((x, y, w, h), size, draw)."""
    base, role, bold, ckey, _italic, floor = vl.TYPE[k.name][field]
    s = ctx(k)[2]
    sz, fl = base * s, max(9.0, floor * s)
    n = len(text)
    while True:
        adv = sz * (1.0 + spacing) / 72.0
        per = max(1, int((h_max - 0.08) // adv))
        cols = -(-n // per)
        if cols <= max_cols or sz <= fl + 1e-6:
            break
        sz = max(fl, sz * 0.92)
    if cols > max_cols:
        raise vl.VLTextOverflow("{}: the {} {!r} needs {} vertical columns even at {:.0f}pt — shorten it".format(
            k.name, field, text[:24], cols, sz))
    w = cols * sz * 1.28 / 72.0 + 0.06
    h = min(h_max, -(-n // cols) * adv + 0.12)
    x = right - w
    col = color or _color(k, ckey)

    def draw():
        tb = dk.text(slide, x, top, w, h, [k.runs(text, sz, col, bold, role)], space_after=0)
        for p in tb.text_frame.paragraphs:
            for r in p.runs:
                r._r.get_or_add_rPr().set("spc", str(int(round(sz * spacing * 100))))
        na.vertical(tb)
    return (x, top, w, h), sz, draw


def display(k, slide, rect, text, field, *, highlight=None, caps=True, ink=None, hl=None, hl_ink=None,
            align="l", anchor="t"):
    """PLAN poster-scale type in `rect`: measured, shrinking to the field's floor, refused past it; Latin set in
    capitals; `highlight` (words of the caller's own text) set on a highlighter. Returns (rect, size, draw)."""
    base, role, bold, ckey, _italic, floor = vl.TYPE[k.name][field]
    s = ctx(k)[2]
    t = text.upper() if caps and not dk._has_cjk(text) else text
    if highlight is not None:
        hi = str(highlight).strip()
        if not hi or hi.upper() not in t.upper():
            raise ValueError("{}: highlight= must be words of the {} itself, got {!r}".format(k.name, field, highlight))
    x, y, w, h = rect
    face = k.ea_face(role, t) or k.face(role)
    sz, fl = base * s, max(9.0, floor * s)
    while True:
        need = dk.measure_text([(t, bool(bold))], w, sz, font=face, line_spacing=0.86)
        if need <= h or sz <= fl + 1e-6:
            break
        sz = max(fl, sz * 0.93)
    if need > h + 1e-6:
        raise vl.VLTextOverflow("{}: the {} {!r} does not fit {:.2f}x{:.2f}in even at {:.0f}pt — shorten it".format(
            k.name, field, text[:24], w, h, sz))
    ty = y if anchor == "t" else (y + h - need if anchor == "b" else y + (h - need) / 2.0)
    col = dk.RGBColor.from_string(ink) if ink else _color(k, ckey)

    def draw():
        runs = []
        if highlight:
            i = t.upper().index(str(highlight).strip().upper())
            j = i + len(str(highlight).strip())
            for part, marked in ((t[:i], False), (t[i:j], True), (t[j:], False)):
                if not part:
                    continue
                if marked:
                    runs += [dk.mark(r, hl) for r in k.runs(part, sz, dk.RGBColor.from_string(hl_ink), bold, role)]
                else:
                    runs += k.runs(part, sz, col, bold, role)
        else:
            runs = k.runs(t, sz, col, bold, role)
        al = {"l": dk.PP_ALIGN.LEFT, "c": dk.PP_ALIGN.CENTER, "r": dk.PP_ALIGN.RIGHT}[align]
        dk.text(slide, x, ty, w, need, [runs], align=al, space_after=0, line_spacing=0.86)
    return (x, ty, w, need), sz, draw


def place_image(k, slide, image, rect, page, treat="frame"):
    """The caller's picture in `rect` with the kit's own placement (feather for ink, a frame for the others)."""
    return vl._place_image(k, slide, image, rect, vl.L_((0, 0, 1, 1), treat, None), page)


def compose(k, slide, page, fields, image):
    fns = COMPOSERS.get(k.name, {})
    if page not in fns:
        raise NotImplementedError("{}.{}(): no composition is registered for this page".format(k.name, page))
    if page == "image_text" and image is None:
        raise ValueError("{}.image_text(): image= is required — for text alone use section(), quote() or points()"
                         .format(k.name))
    if not any(text_of(fields, f) for f in vl.PAGE_FIELDS[page] if f != "items") and not fields.get("items") \
            and image is None:
        raise ValueError("{}.{}(): nothing to place — pass the words".format(k.name, page))
    n0 = len(slide.shapes)
    rects = fns[page](k, slide, fields, image) or {}
    for sh in list(slide.shapes)[n0:]:
        dk._compose_tag(sh, vl=k.name)
    return {"rects": rects, "image": None, "free": None}


def paint_ground(k, slide):
    fn = GROUNDS.get(k.name)
    if fn:
        n0 = len(slide.shapes)
        fn(k, slide)
        for sh in list(slide.shapes)[n0:]:
            dk._compose_tag(sh, vl=k.name)
