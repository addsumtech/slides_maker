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
