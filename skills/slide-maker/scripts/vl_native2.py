#!/usr/bin/env python3
"""vl_native2 — page compositions of the second set of NATIVE visual languages: starlit (星夜), broadsheet (报纸头版),
journal (学术期刊), tally (数据账本) and chalkboard (黑板报).

Same contract as vl_native, which imports this module from its foot (so any importer of vl_native gets these): each
page PLANS its text by measurement, draws its art clear of that text, then sets the text. Nothing here invents a word:
masthead / edition / inside / tags / running / authors / abstract / margin / total / doodle / ordered come from the
caller or nothing is drawn. Page numbers, figure numbers, the ■ end mark and the structural labels (Abstract, Inside,
Figure, Page, Note — in the page's own script) are derived, never typed in.
"""
from __future__ import annotations

import copy
import math
import re
from pathlib import Path

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import GROUNDS, _run_all, alt, ctx, display, fit_circle, flow, points_of, register, text_of  # noqa: F401

# Japanese and Korean entries are confirmed against a native-reading source in Task 6, not written from memory.
LABELS = {
    "abstract": {"en": "Abstract", "zh": "摘要", "ja": "要旨", "ko": "초록"},
    "inside": {"en": "Inside", "zh": "本期", "ja": "今号", "ko": "이번 호"},
    "figure": {"en": "Figure {}", "zh": "图 {}", "ja": "図 {}", "ko": "그림 {}"},
    "page": {"en": "Page {}", "zh": "第 {} 版", "ja": "{} 面", "ko": "{}면"},
    "note": {"en": "Note", "zh": "注", "ja": "注", "ko": "주"},
}


def lang_of(*texts):
    """The language a structural label is set in: the script of the page's own words (Hangul, kana, Han), else en."""
    scr = dk.script_of("".join(t for t in texts if t))
    return {"han": "zh", "kana": "ja", "hangul": "ko"}.get(scr, "en")


def label(kind, *texts):
    return LABELS[kind][lang_of(*texts)]


def caps(t):
    """Latin set in capitals (kickers, meta lines); CJK has no case and is left as written."""
    return t.upper() if t and not dk._has_cjk(t) else t


def fields(f, names, capsed=()):
    """[(field, words)] for the fields of `names` the caller gave, in order; those in `capsed` set in capitals."""
    return [(n, caps(text_of(f, n)) if n in capsed else text_of(f, n)) for n in names if text_of(f, n)]


def stack(k, slide, page, x, w, y0, y1, groups, *, anchor="middle", align="l", **flow_kw):
    """Plan GROUPS of fields one under another — groups = [(items, gap_after_in), …], an empty group skipped — inside
    [y0, y1], the whole stack anchored top or middle. Two passes: measured at the top, then placed. The gaps give an
    underline or a rule its own room (flow's own gaps are for type). Returns (rects, draws)."""
    groups = [(items, gap) for items, gap in groups if items]

    def plan(top):
        rects, draws, y = {}, [], top
        for i, (items, gap) in enumerate(groups):
            r, d = flow(k, slide, page, (x, y, w, y1 - y), items, anchor="top", align=align, **flow_kw)
            rects.update(r)
            draws.append(d)
            y = max((v[1] + v[3] for v in r.values()), default=y) + (gap if i < len(groups) - 1 else 0.0)
        return rects, draws, y
    rects, draws, foot = plan(y0)
    if anchor == "middle" and groups:
        rects, draws, foot = plan(y0 + max(0.0, (y1 - foot) / 2.0))
    return rects, draws


def meet(a, b, pad=0.0):
    return a[0] < b[0] + b[2] + pad and b[0] < a[0] + a[2] + pad and a[1] < b[1] + b[3] + pad and b[1] < a[1] + a[3] + pad


def memo(k, f, name, fallback=None):
    """The caller's words for an extra that holds for the whole deck (masthead=, edition=, running=). Given on this
    page, they are remembered by REASSIGNING k.memo — compose() restores k.__dict__ shallowly when a layout fails, so
    an in-place update would survive the failed attempt. Else the remembered words, else `fallback`."""
    v = text_of(f, name)
    if v:
        k.memo = dict(k.memo, **{name: v})
    return k.memo.get(name) or fallback


def page_no(slide):
    prs = slide.part.package.presentation_part.presentation
    return [s.slide_id for s in prs.slides].index(slide.slide_id) + 1


def tags_of(f, n, lang):
    """tags=: one short label per point, from the caller. Absent → None (no tags drawn)."""
    v = f.get("tags")
    if v is None:
        return None
    if not isinstance(v, (list, tuple)) or len(v) != n or not all(str(t or "").strip() for t in v):
        raise ValueError("{}.points(): tags= takes one non-empty label per point ({} points), got {!r}".format(lang, n, v))
    return [str(t).strip() for t in v]


def inside_lines(v):
    """inside=: 1 to 4 short lines for a broadsheet cover's 'Inside' sidebar. Absent → None."""
    if v is None:
        return None
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= 4 or not all(str(t or "").strip() for t in v):
        raise ValueError("broadsheet.cover(): inside= takes 1 to 4 non-empty lines, got {!r}".format(v))
    return [str(t).strip() for t in v]


def max_extra(size_pt, s, factor=2.3):
    """The most height (in) a raised initial can add to a body field whose base size is `size_pt` at scale `s`."""
    return (factor - 1.0) * size_pt * s * 1.2 / 72.0


def raise_initial(tb, factor=2.3, face=None):
    """Enlarge the first letter of `tb`'s first paragraph IN its line — a raised initial. pptx has no drop cap, and a
    two-box fake re-wraps differently in PowerPoint, Keynote and LibreOffice (the look-dev's "W" ran into its own
    word). Latin letters only; returns the height (in) the taller first line adds, which the box grows by."""
    from pptx.text.text import _Run
    from pptx.util import Emu, Pt
    p = tb.text_frame.paragraphs[0]
    if not p.runs:
        return 0.0
    r0 = p.runs[0]
    t = r0.text
    if not t or not t[0].isalpha() or dk._has_cjk(t[0]) or len(t) < 2:
        return 0.0
    size = r0.font.size.pt
    el = copy.deepcopy(r0._r)
    r0._r.addprevious(el)
    first = _Run(el, p)
    first.text, r0.text = t[0], t[1:]
    first.font.size, first.font.bold = Pt(size * factor), True
    if face:
        first.font.name = face
    added = (factor - 1.0) * size * 1.2 / 72.0
    tb.height = Emu(int(tb.height + added * 914400))
    return added


def end_mark(tb, color, face="Arial"):
    """Set the end-of-article ■ (planned into the words as " ■", so the measured height holds it) in its own
    run, in the accent. Returns whether a mark was found."""
    from pptx.text.text import _Run
    p = tb.text_frame.paragraphs[-1]
    if not p.runs or not p.runs[-1].text.endswith("■"):
        return False
    r = p.runs[-1]
    r.text = r.text[:-1]
    el = copy.deepcopy(r._r)
    r._r.addnext(el)
    m = _Run(el, p)
    m.text = "■"
    m.font.color.rgb = dk.RGBColor.from_string(color)
    m.font.name = face
    return True


def kit_for(name, slide):
    """A kit for an ORDINARY page: rs.ground() receives only the slide, so the ground use() set and the deck's
    remembered extras (vl._MEMO) are read back here."""
    prs = slide.part.package.presentation_part.presentation
    k = vl.Kit(name, prs, "both", None, None, None, vl._ACTIVE.get(name, "light"))
    k.memo = dict(vl._MEMO.get(name, {}))
    return k


def last_shape(slide, n0, text):
    """The text box drawn after the first n0 shapes whose words are `text` (to finish a raised initial or end mark)."""
    for sh in list(slide.shapes)[n0:][::-1]:
        if getattr(sh, "has_text_frame", False) and sh.text_frame.text.replace("\n", "").startswith(text[:12]):
            return sh
    return None


# ═══════════════════════════════════ starlit 星夜 ═══════════════════════════════════
def _st_sky(k, slide, keep, seed):
    na.starfield_png(slide, base=k.P["ground"], ink=k.P["ink"], glow=k.P["glow"], seed=seed, keep_clear=list(keep))


def _st_ground(k, slide):
    _st_sky(k, slide, (), seed=len(k.prs.slides))       # an ordinary page: the sky; its words are not known yet


GROUNDS["starlit"] = _st_ground


def _st_rule(k, slide, rects, a, b):
    """A short gold rule in the gap between field `a` and field `b` (stack() leaves that gap)."""
    if a not in rects or b not in rects:
        return lambda: None
    W, H, s, o = ctx(k)
    y = (rects[a][1] + rects[a][3] + rects[b][1]) / 2.0
    return lambda: na.seg(slide, W / 2 - 0.55 * s, y, W / 2 + 0.55 * s, y, k.P["text_accents"][0], w=1.0)


def _st_moon(k, slide, clear):
    """The crescent at the first corner clear of the words — top right, top left, bottom right; none when no corner
    is clear (it is the sky's, not the page's)."""
    W, H, s, o = ctx(k)
    d = 0.9 * s
    for cx, cy in ((0.86 * W, 0.16 * H), (0.14 * W, 0.16 * H), (0.86 * W, 0.80 * H)):
        r = (cx - 0.5 * d, cy - 0.6 * d, 1.21 * d, 1.1 * d)
        if not any(meet(r, c, 0.2 * s) for c in clear):
            na.crescent(slide, cx, cy, d, k.P["text_accents"][0], k.P["ground"])
            return


@register("starlit", "cover", alts=2)
def _st_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = (0.12 * W, 0.76 * W) if o == "land" else (0.08 * W, 0.84 * W)
    y0, y1 = (0.20 * H, 0.80 * H) if alt() == 0 else (0.07 * H, 0.92 * H)
    r, ds = stack(k, slide, "cover", x, w, y0, y1,
                  [(fields(f, ("kicker", "title"), ("kicker",)), 0.40 * s), (fields(f, ("subtitle",)), 0.0)], align="c")
    _st_sky(k, slide, r.values(), seed=1)
    _st_moon(k, slide, list(r.values()))
    _run_all([_st_rule(k, slide, r, "title", "subtitle")] + ds)
    return r


@register("starlit", "section", alts=2)
def _st_section(k, slide, f, image):
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    cx, cy = 0.5 * W, (0.32 if o == "land" else 0.26) * H
    d0 = fit_circle(k, cx, cy, (min(0.46 * H, 0.40 * W) if o == "land" else 0.62 * W) * (1.0 if alt() == 0 else 0.72))
    rects, draws = {}, []
    if num:
        r, d = flow(k, slide, "section", (cx - d0 * 0.42, cy - d0 * 0.3, d0 * 0.84, d0 * 0.6), [("number", num)],
                    anchor="middle", align="c", start={"number": 96 * s})
        rects.update(r); draws.append(d)
    top = cy + d0 / 2 + 0.1 * s if num else 0.12 * H
    r, d = flow(k, slide, "section", (0.10 * W, top, 0.80 * W, 0.92 * H - top),
                fields(f, ("kicker", "title"), ("kicker",)), anchor="top" if num else "middle", align="c")
    rects.update(r); draws.append(d)
    _st_sky(k, slide, rects.values(), seed=2)
    if num:
        na.radial_glow(slide, cx, cy, d0, k.P["glow"])
    _run_all(draws)
    return rects


@register("starlit", "image_text", alts=2)
def _st_image_text(k, slide, f, image):
    """The caller's picture in a round window with a gold rim, the words beside it (under it in portrait)."""
    W, H, s, o = ctx(k)
    if o == "land":
        d = min(0.70 * H, 0.40 * W) * (1.0 if alt() == 0 else 0.8)
        cx, cy = 0.07 * W + 0.09 * s + d / 2, 0.5 * H
        x0 = cx + d / 2 + 0.6 * s
        col = (x0, 0.10 * H, 0.93 * W - x0, 0.80 * H)
    else:
        d = min(0.80 * W, 0.40 * H) * (1.0 if alt() == 0 else 0.75)
        cx, cy = 0.5 * W, 0.06 * H + 0.09 * s + d / 2
        y0 = cy + d / 2 + 0.4 * s
        col = (0.08 * W, y0, 0.84 * W, 0.92 * H - y0)
    r, dr = flow(k, slide, "image_text", col, fields(f, ("kicker", "title", "body", "caption"), ("kicker",)),
                 anchor="middle" if o == "land" else "top")
    rim = d + 0.18 * s
    _st_sky(k, slide, list(r.values()) + [(cx - rim / 2, cy - rim / 2, rim, rim)], seed=3)
    vl._place_image(k, slide, image, (cx - d / 2, cy - d / 2, d, d),
                    vl.L_((0, 0, 1, 1), "frame", None, frame="ellipse"), "image_text")
    na.ring(slide, cx, cy, rim, k.P["text_accents"][0], w=1.25)
    dr()
    return r


@register("starlit", "quote", alts=2)
def _st_quote(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = (0.20 * W, 0.60 * W) if (o == "land" and alt() == 0) else (0.08 * W, 0.84 * W)
    r, ds = stack(k, slide, "quote", x, w, 0.10 * H, 0.90 * H,
                  [([("mark", "“")] + fields(f, ("quote",)), 0.40 * s), (fields(f, ("attribution",), ("attribution",)), 0.0)],
                  align="c")
    _st_sky(k, slide, r.values(), seed=4)
    _run_all([_st_rule(k, slide, r, "quote", "attribution")] + ds)
    return r


@register("starlit", "data", alts=2)
def _st_data(k, slide, f, image):
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    cx, cy = 0.5 * W, (0.36 if o == "land" else 0.28) * H
    d0 = fit_circle(k, cx, cy, (min(0.60 * H, 0.46 * W) if o == "land" else 0.80 * W) * (1.0 if alt() == 0 else 0.75))
    rects, draws = {}, []
    if num:
        r, d = flow(k, slide, "data", (0.06 * W, cy - d0 * 0.32, 0.88 * W, d0 * 0.64), [("number", num)],
                    anchor="middle", align="c")
        rects.update(r); draws.append(d)
    top = cy + d0 / 2 + 0.05 * s if num else 0.30 * H
    r, d = flow(k, slide, "data", (0.10 * W, top, 0.80 * W, 0.90 * H - top), fields(f, ("label", "note")),
                anchor="top", align="c")
    rects.update(r); draws.append(d)
    _st_sky(k, slide, rects.values(), seed=5)
    if num:
        na.radial_glow(slide, cx, cy, d0, k.P["glow"])
    na.horizon_glow(slide, 0.86 * H, k.P["glow"], k.P["text_accents"][0])
    _run_all(draws)
    return rects


@register("starlit", "closing", alts=2)
def _st_closing(k, slide, f, image):
    W, H, s, o = ctx(k)
    x, w = (0.12 * W, 0.76 * W) if alt() == 0 else (0.07 * W, 0.86 * W)
    r, ds = stack(k, slide, "closing", x, w, (0.22 if alt() == 0 else 0.08) * H, 0.80 * H,
                  [(fields(f, ("title",)), 0.40 * s), (fields(f, ("line",)), 0.0)], align="c")
    _st_sky(k, slide, r.values(), seed=6)
    _st_moon(k, slide, list(r.values()))
    na.horizon_glow(slide, 0.86 * H, k.P["glow"], k.P["text_accents"][0])
    _run_all([_st_rule(k, slide, r, "title", "line")] + ds)
    return r


@register("starlit", "points", alts=2)
def _st_points(k, slide, f, image):
    """A constellation: one star per point, joined in order by one gold line. Across a landscape page the stars step
    high, low, high with their words under them; in portrait (and for long copy) they climb a zig-zag at the left
    with their words beside them. The line never reaches the words: from a high star it drops 0.75s over a whole
    column span, so at the column's edge it is still above y + 0.375s, and the words start at y + 0.42s."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    hh = ((0.20 if o == "land" else 0.16) if alt() == 0 else 0.32) * H      # long copy: the title gets more room
    r, d = flow(k, slide, "points", (0.07 * W, 0.07 * H, 0.86 * W, hh), fields(f, ("kicker", "title"), ("kicker",)))
    rects, draws, clear = dict(r), [d], list(r.values())
    top = max((v[1] + v[3] for v in r.values()), default=0.07 * H) + 0.3 * s
    bottom = H - 0.6

    def layout(t0):
        stars, cols = [], []
        if o == "land" and alt() == 0:
            span = 0.86 * W / n
            for i in range(n):
                x, y = 0.07 * W + span * (i + 0.5), t0 + (0.45 if i % 2 == 0 else 1.20) * s
                stars.append((x, y))
                cols.append((x - span / 2 + 0.12 * s, y + 0.42 * s, span - 0.24 * s, 0.92 * H - (y + 0.42 * s)))
            align = "c"
        else:
            slot = (0.92 * H - t0) / n
            lx = 0.30 * W
            for i in range(n):
                y = t0 + slot * (i + 0.5)
                stars.append(((0.13 if i % 2 == 0 else 0.22) * W, y))
                cols.append((lx, y - min(0.30 * s, slot / 2), 0.92 * W - lx, slot - 0.06 * s))
            align = "l"
        planned = [flow(k, slide, "points", col, [(x_, t) for x_, t in (("item_head", hd), ("item_line", ln)) if t],
                        anchor="top", align=align) for (hd, ln), col in zip(pts, cols)]
        return stars, planned
    stars, planned = layout(top)
    if o == "land" and alt() == 0:          # the constellation and its words sit in the middle of the room under the title
        foot = max(v[1] + v[3] for tr, _d in planned for v in tr.values())
        shift = max(0.0, (bottom - foot) / 2.0)
        if shift > 0.05:
            stars, planned = layout(top + shift)
    for tr, td_ in planned:
        clear += list(tr.values())
        draws.append(td_)
    _st_sky(k, slide, clear + [(x - 0.35 * s, y - 0.35 * s, 0.7 * s, 0.7 * s) for x, y in stars], seed=7)
    for a, b in zip(stars, stars[1:]):
        na.seg(slide, a[0], a[1], b[0], b[1], k.P["text_accents"][0], w=0.9, alpha=0.55)
    for x, y in stars:
        na.radial_glow(slide, x, y, 1.0 * s, k.P["glow"])
        dk.decorative(na.disc(slide, x, y, 0.16 * s, k.P["glow"]), "a star of the constellation; its words sit beside it")
    _run_all(draws)
    return rects
