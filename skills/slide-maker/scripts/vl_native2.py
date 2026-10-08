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
    dk._compose_tag(tb, flag="+initial")       # lint measures the first line apart (deckkit._ink_rect)
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


# ═══════════════════════════════════ broadsheet 报纸头版 ═══════════════════════════════════
def bs_strip(k, slide, f, big=False):
    """The masthead strip every page carries: the paper's name (masthead=, else the cover's kicker, else none), a
    heavy rule, the caller's edition= at the left and the page number at the right, a hairline. Never invents a name,
    a date or an issue number. Draws at once and returns the y under it."""
    W, H, s, o = ctx(k)
    name = memo(k, f, "masthead", fallback=k.memo.get("_cover_kicker"))
    edition = memo(k, f, "edition")
    y = 0.04 * H
    draws = []
    if name:
        nh = (0.80 if big else 0.52) * s
        r, d = flow(k, slide, "masthead", (0.05 * W, y, 0.90 * W, nh), [("masthead", name)], anchor="middle", align="c",
                    start={"masthead": (44 if big else 26) * s})
        draws.append(d)
        y = max(y + nh, max(v[1] + v[3] for v in r.values())) + 0.04 * s
    rule_y, meta_y = y, y + 0.10 * s
    draws.append(lambda: na.seg(slide, 0.05 * W, rule_y, 0.95 * W, rule_y, k.P["ink"], w=2.5))
    if edition:
        r, d = flow(k, slide, "edition", (0.05 * W, meta_y, 0.62 * W, 0.30 * s), [("edition", caps(edition))])
        draws.append(d)
    pg = caps(label("page", name, edition, text_of(f, "title"), text_of(f, "quote"), k.memo.get("_title")).format(page_no(slide)))
    sz = vl.TYPE[k.name]["edition"][0] * s
    draws.append(lambda: dk.text(slide, 0.70 * W, meta_y, 0.25 * W, 0.30 * s,
                                 [k.runs(pg, sz, k.color("mute"), True, "meta")], align=dk.PP_ALIGN.RIGHT))
    hair = meta_y + 0.34 * s
    draws.append(lambda: na.seg(slide, 0.05 * W, hair, 0.95 * W, hair, k.P["ink"], w=0.6))
    _run_all(draws)
    return hair + 0.10 * s


def _with_initial(k, slide, draw, words):
    """Run a planned draw, then open the body it set on a raised initial (planned with room for it: max_extra)."""
    def go():
        n0 = len(slide.shapes)
        draw()
        tb = last_shape(slide, n0, words)
        if tb is not None:
            raise_initial(tb, face=k.face("display"))
    return go


@register("broadsheet", "cover", alts=2)
def _bs_cover(k, slide, f, image):
    """A front page: the headline across the page, a rule, the standfirst; the caller's inside= lines in a sidebar
    (under the standfirst in portrait). With no masthead= the cover's kicker names the paper and is not repeated."""
    W, H, s, o = ctx(k)
    kick, title = text_of(f, "kicker"), text_of(f, "title")
    as_name = bool(kick) and not text_of(f, "masthead") and not k.memo.get("masthead")
    if title:
        k.memo = dict(k.memo, _title=title)
    if as_name:
        k.memo = dict(k.memo, _cover_kicker=kick)
    top = bs_strip(k, slide, f, big=True) + 0.12 * s
    lines = inside_lines(f.get("inside"))
    head = ([("kicker", caps(kick))] if kick and not as_name else []) + ([("title", title)] if title else [])
    hh = ((0.50 if o == "land" else 0.36) if alt() == 0 else (0.62 if o == "land" else 0.48)) * H
    r, d = flow(k, slide, "cover", (0.05 * W, top, 0.90 * W, hh), head, anchor="top")
    rects, draws = dict(r), [d]
    yr = max((v[1] + v[3] for v in r.values()), default=top) + 0.16 * s
    art = [lambda: na.seg(slide, 0.05 * W, yr, 0.95 * W, yr, k.P["ink"], w=0.75)]
    side = bool(lines) and o == "land"
    sub, sb, foot = text_of(f, "subtitle"), yr, H - 0.6
    if sub:
        r, d = flow(k, slide, "cover", (0.05 * W, yr + 0.16 * s, (0.62 if side else 0.90) * W, foot - yr - 0.16 * s),
                    [("subtitle", sub)], anchor="top")
        rects.update(r); draws.append(d)
        sb = max(v[1] + v[3] for v in r.values())
    if lines:
        if side:
            ix, iy, iw = 0.71 * W, yr + 0.16 * s, 0.24 * W
            art.append(lambda: na.seg(slide, 0.685 * W, yr + 0.16 * s, 0.685 * W, foot, k.P["ink"], w=0.5))
        else:
            ix, iy, iw = 0.05 * W, sb + 0.3 * s, 0.90 * W
        r, d = flow(k, slide, "cover", (ix, iy, iw, foot - iy),
                    [("inside_h", caps(label("inside", *lines))), ("inside", "\n".join(lines))], anchor="top")
        draws.append(d)
    _run_all(art + draws)
    return rects


@register("broadsheet", "section", alts=2)
def _bs_section(k, slide, f, image):
    """A section front: the number in a black tab on a heavy rule, the section's title as its headline."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    num = text_of(f, "number")
    rects, art, draws = {}, [], []
    y = top + (0.6 if alt() == 0 else 0.3) * s
    if num:
        th = 0.95 * s
        tw = min(0.6 * W, max(1.1 * s, na.chip_width(num, 44 * s, k.face("numeral")) + 0.2 * s))
        r, d = flow(k, slide, "section", (0.05 * W + 0.1 * s, y, tw - 0.2 * s, th), [("number", num)], anchor="middle",
                    align="c", ink=k.P["ground"], accent=k.P["ground"], start={"number": 44 * s})
        rects.update(r); draws.append(d)
        art.append(lambda y=y: dk.box(slide, 0.05 * W, y, tw, th, fill=k.P["ink"]))
        y += th
    art.append(lambda y=y: na.seg(slide, 0.05 * W, y, 0.95 * W, y, k.P["ink"], w=3.0))
    r, d = flow(k, slide, "section", (0.05 * W, y + 0.3 * s, 0.90 * W, H - 0.6 - y - 0.3 * s),
                fields(f, ("kicker", "title"), ("kicker",)), anchor="top")
    rects.update(r); draws.append(d)
    _run_all(art + draws)
    return rects


@register("broadsheet", "image_text", alts=2)
def _bs_image_text(k, slide, f, image):
    """A news photograph with its caption under a hairline; the story's headline and body beside it (under it in
    portrait)."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f) + 0.25 * s
    bottom = H - 0.6
    cap = text_of(f, "caption")
    rects, draws, art = {}, [], []
    if o == "land":
        img_x, img_w = 0.05 * W, (0.58 if alt() == 0 else 0.50) * W
        cx0 = img_x + img_w + 0.35 * s
        col = (cx0, top, 0.95 * W - cx0, bottom - top)
        img_y1 = bottom
        if cap:
            cr_, cd = flow(k, slide, "image_text", (img_x, bottom - 0.9 * s, img_w, 0.9 * s), [("caption", cap)], anchor="bottom")
            img_y1 = cr_["caption"][1] - 0.22 * s
    else:
        img_x, img_w = 0.05 * W, 0.90 * W
        img_y1 = top + (0.42 if alt() == 0 else 0.34) * H
        if cap:
            cr_, cd = flow(k, slide, "image_text", (img_x, img_y1 + 0.22 * s, img_w, 0.6 * s), [("caption", cap)], anchor="top")
        cy0 = (max(v[1] + v[3] for v in cr_.values()) if cap else img_y1) + 0.3 * s
        col = (0.05 * W, cy0, 0.90 * W, bottom - cy0)
    if cap:
        rects.update(cr_); draws.append(cd)
        hy = cr_["caption"][1] - 0.11 * s
        art.append(lambda: na.seg(slide, img_x, hy, img_x + img_w, hy, k.P["ink"], w=0.5))
    r, d = flow(k, slide, "image_text", col, fields(f, ("kicker", "title", "body"), ("kicker",)), anchor="top",
                start={"title": 40 * s})
    rects.update(r); draws.append(d)
    vl._place_image(k, slide, image, (img_x, top, img_w, img_y1 - top), vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    _run_all(art + draws)
    return rects


@register("broadsheet", "quote", alts=2)
def _bs_quote(k, slide, f, image):
    """A pull quote between a heavy rule and a hairline, the quote mark hung in the margin, the source under it."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    x0, x1 = (0.12 * W, 0.88 * W) if (o == "land" and alt() == 0) else (0.06 * W, 0.94 * W)
    mw = 0.9 * s
    q, a = text_of(f, "quote"), text_of(f, "attribution")
    rects, draws = {}, []
    qy0, qy1 = top + 0.85 * s, H - 1.4 * s
    if q:
        r, d = flow(k, slide, "quote", (x0 + mw, qy0, x1 - x0 - mw, qy1 - qy0), [("quote", q)], anchor="middle")
        rects.update(r); draws.append(d)
        qt, qb = r["quote"][1], r["quote"][1] + r["quote"][3]
        _m, dm = flow(k, slide, "quote", (x0, qt - 0.12 * s, mw, 1.2 * s), [("mark", "“")], start={"mark": 80 * s})
        draws.append(dm)
    else:
        qt = qb = (qy0 + qy1) / 2.0
    art = [lambda: na.seg(slide, x0, qt - 0.3 * s, x1, qt - 0.3 * s, k.P["ink"], w=3.0),
           lambda: na.seg(slide, x0, qb + 0.25 * s, x1, qb + 0.25 * s, k.P["ink"], w=0.6)]
    if a:
        r, d = flow(k, slide, "quote", (x0 + mw, qb + 0.40 * s, x1 - x0 - mw, 0.8 * s), [("attribution", caps(a))])
        rects.update(r); draws.append(d)
    _run_all(art + draws)
    return rects


@register("broadsheet", "data", alts=2)
def _bs_data(k, slide, f, image):
    """By the numbers: the figure, a short rule, its label and note, in a boxed panel under a solid band — a header
    with no words, because the kit has none to give it."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    bw = ((0.42 if o == "land" else 0.80) if alt() == 0 else 0.86) * W
    bx, band, pad = (W - bw) / 2.0, 0.30 * s, 0.30 * s
    y_in, avail = top + 0.3 * s, (H - 0.6) - (top + 0.3 * s)
    items = fields(f, ("number", "label", "note"))

    def plan(y):
        return flow(k, slide, "data", (bx + pad, y + band + pad, bw - 2 * pad, avail - band - 2 * pad), items,
                    anchor="top", align="c")
    r, _unused = plan(y_in)
    bh = band + 2 * pad + (max(v[1] + v[3] for v in r.values()) - (y_in + band + pad)) + 0.1 * s
    by = y_in + max(0.0, (avail - bh) / 2.0)
    r, d = plan(by)
    art = [lambda: dk.box(slide, bx, by, bw, bh, fill=None, line=dk._as_rgb(k.P["ink"]), line_w=1.25),
           lambda: dk.decorative(dk.box(slide, bx, by, bw, band, fill=k.P["ink"]), "the header band of a numbers box")]
    if "number" in r and "label" in r:
        yl = (r["number"][1] + r["number"][3] + r["label"][1]) / 2.0
        art.append(lambda: na.seg(slide, W / 2 - 0.15 * bw, yl, W / 2 + 0.15 * bw, yl, k.P["ink"], w=0.6))
    _run_all(art + [d])
    return r


@register("broadsheet", "closing", alts=2)
def _bs_closing(k, slide, f, image):
    """The last story's end: its headline, its line, and the ■ end-of-article mark after the last words."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    t, ln = text_of(f, "title"), text_of(f, "line")
    items = [("title", t if ln or not t else t + " ■")] if t else []
    if ln:
        items.append(("line", ln + " ■"))
    col = (0.05 * W, top + 0.3 * s, (0.70 if o == "land" and alt() == 0 else 0.90) * W, H - 0.6 - top - 0.3 * s)
    r, d = flow(k, slide, "closing", col, items, anchor="middle")
    d()
    end_mark(list(slide.shapes)[-1], k.P["text_accents"][0])
    return r


@register("broadsheet", "points", alts=2)
def _bs_points(k, slide, f, image):
    """Newspaper columns: each point a column — the caller's tag over its head over its body, rules between; a Latin
    body opens on a raised initial when its column has room for the taller first line (and the one line the initial's
    width may push down); where it has not, the body is set plain — the words never move for an ornament. Portrait
    stacks the columns as rows; long copy gives the title more room."""
    W, H, s, o = ctx(k)
    top = bs_strip(k, slide, f)
    pts = points_of(f.get("items"))
    n = len(pts)
    tags = tags_of(f, n, "broadsheet")
    r, d = flow(k, slide, "points", (0.05 * W, top + 0.05 * s, 0.90 * W, (0.20 if alt() == 0 else 0.34) * H),
                fields(f, ("kicker", "title"), ("kicker",)),
                start={"title": 42 * s})                  # an inside page's head; the 80pt headline is the cover's
    rects, draws, art = dict(r), [d], []
    ctop = max((v[1] + v[3] for v in r.values()), default=top) + 0.30 * s
    bottom = H - 0.6
    gap = 0.30 * s
    if o == "land":                                   # columns across the page
        cw = (0.90 * W - (n - 1) * gap) / n
        boxes = [(0.05 * W + i * (cw + gap), ctop, cw, bottom - ctop) for i in range(n)]
        rules = [(b[0] - gap / 2, ctop, b[0] - gap / 2, bottom) for b in boxes[1:]]
    elif alt() == 1 and n >= 3:                       # a square or portrait page with long copy: two columns of rows
        cw, rows = (0.90 * W - gap) / 2, -(-n // 2)
        rh = (bottom - ctop - (rows - 1) * 0.15 * s) / rows
        boxes = [(0.05 * W + (i % 2) * (cw + gap), ctop + (i // 2) * (rh + 0.15 * s), cw, rh) for i in range(n)]
        rules = [(0.05 * W + cw + gap / 2, ctop, 0.05 * W + cw + gap / 2, bottom)] + \
                [(0.05 * W, ctop + r_ * (rh + 0.15 * s) - 0.08 * s, 0.95 * W, ctop + r_ * (rh + 0.15 * s) - 0.08 * s)
                 for r_ in range(1, rows)]
    else:                                             # portrait: the columns stacked as rows
        slot = (bottom - ctop) / n
        boxes = [(0.05 * W, ctop + i * slot, 0.90 * W, slot - 0.15 * s) for i in range(n)]
        rules = [(0.05 * W, b[1] - 0.08 * s, 0.95 * W, b[1] - 0.08 * s) for b in boxes[1:]]
    for x0, y0, x1, y1 in rules:
        art.append(lambda x0=x0, y0=y0, x1=x1, y1=y1: na.seg(slide, x0, y0, x1, y1, k.P["ink"], w=0.5))
    for i, ((hd, ln), (x, y, w, h)) in enumerate(zip(pts, boxes)):
        items = ([("tag", caps(tags[i]))] if tags else []) + [("item_head", hd)] + ([("item_line", ln)] if ln else [])
        tr, td_ = flow(k, slide, "points", (x, y, w, h), items, anchor="top")
        initial = bool(ln) and ln[0].isalpha() and not dk._has_cjk(ln[0]) and "item_line" in tr
        if initial:                       # room in the column for the taller first line and the one line its width
            bx, by, bw, bh = tr["item_line"]  # may push down (lint measures a declared initial so: deckkit._ink_rect)
            pitch = td_.sizes["item_line"] * dk._LINT_LINE_H / 72.0
            initial = by + bh + 1.3 * pitch + pitch + 0.05 <= y + h
        draws.append(_with_initial(k, slide, td_, ln) if initial else td_)
    _run_all(art + draws)
    return rects
