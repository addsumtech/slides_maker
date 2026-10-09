#!/usr/bin/env python3
"""vl_native3 — page compositions of the P5 native visual languages: interface (产品界面) and wayfinding (导视线路).

Same contract as vl_native2, which this module builds on: each page PLANS its text by measurement, draws its art
clear of that text, then sets the text. Nothing here invents a word: crumb / status / actions / toggles / tags /
total (interface) and line / ordered / interchange / board (wayfinding) come from the caller or nothing is drawn.
Page numbers, avatar initials, the device frame, a section's line colour and the way-out label are derived.
"""
from __future__ import annotations

import deckkit as dk
import native_art as na
import visual_languages as vl
from vl_native import _run_all, alt, ctx, points_of, register, text_of
import vl_native2 as _v2

# vl_native2 imports vl_native, whose foot imports this module: when vl_native2 is imported FIRST it is only partly
# built at that moment, so its names are looked up at call time, never copied at import (a P4 test that imported
# vl_native2 directly failed with "cannot import name 'chip_size'").
def chip_size(*a, **kw): return _v2.chip_size(*a, **kw)          # noqa: E704
def fields(*a, **kw): return _v2.fields(*a, **kw)                # noqa: E704
def flow(*a, **kw): return _v2.flow(*a, **kw)                    # noqa: E704
def lang_of(*a, **kw): return _v2.lang_of(*a, **kw)              # noqa: E704
def meet(*a, **kw): return _v2.meet(*a, **kw)                    # noqa: E704
def memo(*a, **kw): return _v2.memo(*a, **kw)                    # noqa: E704
def plan_together(*a, **kw): return _v2.plan_together(*a, **kw)  # noqa: E704
def share_of(*a, **kw): return _v2.share_of(*a, **kw)            # noqa: E704
def stack(*a, **kw): return _v2.stack(*a, **kw)                  # noqa: E704
def tags_of(*a, **kw): return _v2.tags_of(*a, **kw)              # noqa: E704

STATES = ("primary", "on", "pending", "error")


def _hex(v):
    return vl._hex(v)


# ═══════════════════════════════════ interface 产品界面 ═══════════════════════════════════
def ui_state(v, page, name):
    """An extra given as text or (text, state): -> (text, state), state one of STATES, default 'primary'."""
    if isinstance(v, (list, tuple)) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], str):
        t, st = v[0].strip(), v[1].strip()
        if st not in STATES:
            raise ValueError("interface.{}(): {}= state must be one of {} — got {!r}".format(page, name, list(STATES), st))
        if t:
            return t, st
    elif isinstance(v, str) and v.strip():
        return v.strip(), "primary"
    raise ValueError("interface.{}(): {}= takes words, or (words, state) with state in {} — got {!r}"
                     .format(page, name, list(STATES), v))


def initials(attribution):
    """Avatar initials from an attribution that is a NAME: before any comma, 1-3 words each starting with a capital
    letter ("Maya Kowalski, Operations lead" -> MK). Anything else — a phrase ("How every repair begins"), CJK, empty —
    gets no avatar: a circle of letters claims a person (render review, 2026-10-10: "HE" from a sentence)."""
    t = (attribution or "").split(",")[0].strip()
    if not t or dk._has_cjk(t):
        return None
    words = t.split()
    if not 1 <= len(words) <= 3 or not all(w[:1].isalpha() and w[:1].isupper() for w in words):
        return None
    return "".join(w[0] for w in words[:2])


def device_for(path):
    """'phone' for a picture taller than wide, else 'browser' — derived from the picture, never chosen."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    return "phone" if h > w * 1.05 else "browser"


def fit_device(kind, box, ar):
    """The largest device frame inside `box` whose SCREEN has the picture's aspect `ar`, centred: the insets mirror
    native_art.ui_device (browser: 0.06 sides, a bar of min(0.36, 0.09 h) and 0.06 below; phone: m = max(0.06, 0.045 w)
    at the sides, 1.6 m top and bottom). Solved by a few fixed-point steps — the insets depend on the frame's size."""
    bx, by, bw, bh = box
    if kind == "browser":
        fw = bw
        fh = (fw - 0.12) / ar + 0.42
        for _ in range(4):
            fh = (fw - 0.12) / ar + min(0.36, 0.09 * fh) + 0.06
        if fh > bh:
            fh = bh
            fw = (fh - min(0.36, 0.09 * fh) - 0.06) * ar + 0.12
    else:
        fh = bh
        fw = (fh - 0.192) * ar + 0.12
        for _ in range(4):
            m = max(0.06, 0.045 * fw)
            fw = (fh - 3.2 * m) * ar + 2 * m
        if fw > bw:
            fw = bw
            m = max(0.06, 0.045 * fw)
            fh = (fw - 2 * m) / ar + 3.2 * m
    return (bx + (bw - fw) / 2.0, by + (bh - fh) / 2.0, fw, fh)


def _actions(f, page):
    v = f.get("actions")
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= 2 or not all(isinstance(a, str) and a.strip() for a in v):
        raise ValueError("interface.{}(): actions= takes 1 or 2 button labels (primary, secondary), got {!r}".format(page, v))
    return [a.strip() for a in v]


def _toggles(f):
    v = f.get("toggles")
    if v is None:
        return []
    ok_ = isinstance(v, (list, tuple)) and 1 <= len(v) <= 4 and all(
        isinstance(t, (list, tuple)) and len(t) == 2 and isinstance(t[0], str) and t[0].strip() and isinstance(t[1], bool)
        for t in v)
    if not ok_:
        raise ValueError("interface.cover(): toggles= takes 1 to 4 (label, True/False) rows, got {!r}".format(v))
    return [(t[0].strip(), t[1]) for t in v]


def dot_chip_width(k, text, sz):
    """A status chip's width: its words (chip_width, which carries 1.2 em of padding), the dot and a gap."""
    W, H, s, o = ctx(k)
    return na.chip_width(text, sz, k.face("body")) + 0.09 * s + 0.35 * sz / 72.0


def dot_chip(k, slide, x, y, text, sz, state):
    """A pill holding a state dot and the caller's words BESIDE it (a plain chip centred its words over the dot —
    "Ŀive", render review 2026-10-10). Returns (x, y, w, h)."""
    W, H, s, o = ctx(k)
    em = sz / 72.0
    w, h, d = dot_chip_width(k, text, sz), em * 1.9, 0.09 * s
    dk.box(slide, x, y, w, h, fill=_hex(k.P["soft"]), line=dk._as_rgb(_hex(k.P["line"])), line_w=0.75, round=True,
           r=h / 2.0)
    dd = dk.disc(slide, x + 0.6 * em, y + (h - d) / 2.0, d, fill=_hex(k.P["states"][state]))
    dk.decorative(dd, "the state is named in the chip's words")
    tx = x + 0.6 * em + d
    tb = dk.text(slide, tx, y, w - (tx - x), h, [k.runs(text, sz, k.color("ink"), True)], align=dk.PP_ALIGN.CENTER,
                 anchor=dk.MSO_ANCHOR.MIDDLE, space_after=0)
    tb.text_frame.word_wrap = False
    dk.overlap_intent(tb, "the label sits on its own chip")
    return (x, y, w, h)


def _bar_h(k):
    return 0.62 * ctx(k)[2]


def _top_bar(k, slide, win, f, page):
    """The window's bar: the crumb (remembered) left, the status chip (remembered) right. The crumb is one line at
    its size or its floor, else refused. Draws at once."""
    W, H, s, o = ctx(k)
    x, y, w, _h = win
    bh = _bar_h(k)
    crumb = memo(k, f, "crumb")
    st = f.get("status") if f.get("status") is not None else k.memo.get("status")
    if f.get("status") is not None:
        k.memo = dict(k.memo, status=f.get("status"))
    right = x + w - 0.32 * s
    if st is not None:
        t, state = ui_state(st, page, "status")
        sz = chip_size(k, t, 0.45 * w, "status")
        if sz is None:
            raise vl.VLTextOverflow("interface.{}(): status={!r} does not fit the window's bar".format(page, t))
        cw = dot_chip_width(k, t, sz)
        ch = sz / 72.0 * 1.9
        cx = right - cw
        cy = y + (bh - ch) / 2.0
        dot_chip(k, slide, cx, cy, t, sz, state)
        right = cx - 0.2 * s
    if crumb:
        cw = right - (x + 0.32 * s)
        sz = chip_size(k, crumb, cw, "crumb")
        if sz is None:
            raise vl.VLTextOverflow("interface.{}(): crumb={!r} does not fit the window's bar on one line"
                                    .format(page, crumb))
        tb = dk.text(slide, x + 0.32 * s, y, cw, bh, [k.runs(crumb, sz, k.color("mute"))], anchor=dk.MSO_ANCHOR.MIDDLE,
                     space_after=0)
        tb.text_frame.word_wrap = False


def _window(k, slide, rect, f, page, *, bar=True):
    """Draw a window with its bar; returns the content rect inside it (padded)."""
    W, H, s, o = ctx(k)
    inner = na.ui_window(slide, *rect, fill=k.P["panel"], line=k.P["line"], drop=k.P["drop"], r=0.22 * s,
                         bar=_bar_h(k) if bar else None)
    if bar:
        _top_bar(k, slide, rect, f, page)
    p = 0.42 * s
    return (inner[0] + p, inner[1] + 0.3 * s, inner[2] - 2 * p, inner[3] - 0.3 * s - p)


def ordinary_window(slide):
    """rs.ground for interface: the page is one window (with the deck's remembered crumb and status)."""
    import vl_native2 as v2
    k = v2.kit_for("interface", slide)
    W, H, s, o = ctx(k)
    return _window(k, slide, (0.06 * W, 0.08 * H, 0.88 * W, 0.84 * H), {}, "ordinary")


def _buttons(k, slide, x, y, acts, max_w):
    """The caller's actions as buttons from (x, y): primary filled, secondary outlined; a pointer on the primary.
    Returns the row's height; refuses a row that cannot fit max_w."""
    W, H, s, o = ctx(k)
    if not acts:
        return 0.0
    sz = vl.TYPE["interface"]["action"][0] * s
    widths = [na.ui_button_width(a, sz, k.face("body")) for a in acts]
    while sum(widths) + 0.2 * s * (len(acts) - 1) > max_w and sz > vl.TYPE["interface"]["action"][5] * s:
        sz *= 0.92
        widths = [na.ui_button_width(a, sz, k.face("body")) for a in acts]
    if sum(widths) + 0.2 * s * (len(acts) - 1) > max_w:
        raise vl.VLTextOverflow("interface: actions={!r} do not fit one row".format(acts))
    h = sz / 72.0 * 2.6
    cx = x
    for i, a in enumerate(acts):
        if i == 0:
            fill, ink = k.P["primary_fill"], ("FFFFFF" if vl._contrast("FFFFFF", k.P["primary_fill"]) >= 4.5 else k.P["ink"])
            b = na.ui_button(slide, cx, y, a, size=sz, fill=fill, ink=ink, face=k.face("body"),
                             ea_face=k.ea_face("body", a), h=h)
            na.ui_cursor(slide, b[0] + b[2] * 0.90, b[1] + b[3] * 0.74, fill=k.P["ink"], edge=k.P["panel"], size=0.34 * s)
        else:
            b = na.ui_button(slide, cx, y, a, size=sz, fill=k.P["panel"], ink=k.P["ink"], face=k.face("body"),
                             ea_face=k.ea_face("body", a), line=k.P["off_line"], h=h)
        cx = b[0] + b[2] + 0.2 * s
    return h


@register("interface", "cover", alts=2)
def _ui_cover(k, slide, f, image):
    W, H, s, o = ctx(k)
    acts, tog = _actions(f, "cover"), _toggles(f)
    side = bool(tog) and o == "land"
    if o == "land":
        win = (0.06 * W, (0.15 if alt() == 0 else 0.08) * H, (0.60 if side else 0.88) * W, (0.74 if alt() == 0 else 0.84) * H)
    else:
        win = (0.07 * W, 0.06 * H, 0.86 * W, (0.56 if tog else 0.84) * H)
    col = _window(k, slide, win, f, "cover")
    bh = (vl.TYPE["interface"]["action"][0] * s / 72.0 * 2.6 + 0.35 * s) if acts else 0.0
    r, ds = stack(k, slide, "cover", col[0], col[2], col[1], col[1] + col[3] - bh,
                  [(fields(f, ("kicker",)), 0.12 * s), (fields(f, ("title",)), 0.25 * s), (fields(f, ("subtitle",)), 0.0)],
                  anchor="middle")
    _run_all(ds)
    if acts:
        foot = max(v[1] + v[3] for v in r.values()) if r else col[1]
        _buttons(k, slide, col[0], foot + 0.35 * s, acts, col[2])
    if tog:
        if side:
            px, py, pw = 0.69 * W, win[1], 0.25 * W
        else:
            px, py, pw = 0.07 * W, win[1] + win[3] + 0.25 * s, 0.86 * W
        rows = [(lab, on) for lab, on in tog]
        tw, th = 0.62 * s, 0.34 * s
        specs = [((0, 0, pw - 0.84 * s - tw - 0.2 * s, 10.0), [("toggle", lab)], {}) for lab, _on in rows]
        planned = plan_together(k, slide, "cover", specs)
        hs = [max(v[3] for v in rr.values()) for rr, _d in planned]
        ph = sum(max(hh, th) for hh in hs) + 0.42 * s * len(rows) + 0.42 * s
        if py + ph > H - 0.3 * s:
            raise vl.VLTextOverflow("interface.cover(): toggles= need more room than the page has")
        na.ui_window(slide, px, py, pw, ph, fill=k.P["panel"], line=k.P["line"], drop=k.P["drop"], r=0.22 * s)
        yy = py + 0.42 * s
        for (lab, on), hh in zip(rows, hs):
            rowh = max(hh, th)
            rr, d = flow(k, slide, "cover", (px + 0.42 * s, yy + (rowh - hh) / 2.0, pw - 0.84 * s - tw - 0.2 * s, hh),
                         [("toggle", lab)], start={"toggle": min(getattr(dd, "sizes", {}).get("toggle", 99) for _r2, dd in planned)})
            d()
            na.ui_toggle(slide, px + pw - 0.42 * s - tw, yy + (rowh - th) / 2.0, on, on_fill=k.P["states"]["primary"],
                         off_line=k.P["off_line"], w=tw, h=th)
            yy += rowh + 0.42 * s
    return r


@register("interface", "section", alts=2)
def _ui_section(k, slide, f, image):
    """A tab: the section number in a rounded badge, kicker and title beside it, the active-tab bar under the title."""
    W, H, s, o = ctx(k)
    top = (0.26 if alt() == 0 else 0.14) * H
    beside = o == "land" or alt() == 1
    win = (0.06 * W, top, 0.88 * W, H - 2 * top) if o == "land" else \
        (0.07 * W, (0.12 if alt() == 0 else 0.08) * H, 0.86 * W, (0.76 if alt() == 0 else 0.84) * H)
    col = _window(k, slide, win, f, "section")
    num = text_of(f, "number")
    x = col[0]
    if num:
        bs = min(1.6 * s, col[3] * 0.8) if o == "land" else (1.6 * s if alt() == 0 else 0.9 * s)
        by = col[1] + (col[3] - bs) / 2.0 if beside else col[1]
        dk.box(slide, x, by, bs, bs, fill=_hex(k.P["primary_fill"]), round=True, r=0.22 * s)
        r0, d0 = flow(k, slide, "section", (x, by, bs, bs), [("number", num)], anchor="middle", align="c",
                      ink="FFFFFF", start={"number": 72 * s})
        d0()
        if beside:
            x = x + bs + (0.5 if o == "land" else 0.3) * s
            col = (x, col[1], col[0] + col[2] - x, col[3])
        else:
            col = (col[0], by + bs + 0.4 * s, col[2], col[1] + col[3] - by - bs - 0.4 * s)
    r, ds = stack(k, slide, "section", col[0], col[2], col[1], col[1] + col[3] - 0.3 * s,
                  [(fields(f, ("kicker",)), 0.12 * s), (fields(f, ("title",)), 0.0)], anchor="middle")
    _run_all(ds)
    if "title" in r:
        t = r["title"]
        dk.box(slide, t[0], t[1] + t[3] + 0.14 * s, min(t[2], 2.4 * s), 0.07 * s, fill=_hex(k.P["primary_fill"]),
               round=True, r=0.035 * s)
    return r


@register("interface", "image_text", alts=2)
def _ui_image_text(k, slide, f, image):
    """The caller's picture in a device frame chosen by its aspect; kicker, title, body, caption beside it."""
    W, H, s, o = ctx(k)
    path, _alt, _slot = vl._resolve(k, image if not isinstance(image, (list, tuple)) else image[0])
    kind = device_for(path)
    from PIL import Image
    with Image.open(path) as im:
        ar = im.size[0] / float(im.size[1])
    if o == "land":
        box = (0.06 * W, 0.10 * H, (0.48 if alt() == 0 else 0.40) * W, 0.80 * H)
        cx0 = box[0] + box[2] + 0.55 * s
        col = (cx0, 0.14 * H, 0.94 * W - cx0, 0.72 * H)
    else:
        box = (0.07 * W, 0.05 * H, 0.86 * W, (0.48 if alt() == 0 else 0.40) * H)
        cy0 = box[1] + box[3] + 0.4 * s
        col = (0.07 * W, cy0, 0.86 * W, H - 0.5 * s - cy0)
    fx, fy, fw, fh = fit_device(kind, box, ar)
    if kind == "phone":
        scr = na.ui_device(slide, fx, fy, fw, fh, "phone", frame=k.P["ink"], screen=k.P["panel"])
    else:
        scr = na.ui_device(slide, fx, fy, fw, fh, "browser", frame=k.P["panel"], screen=k.P["line"])
    vl._place_image(k, slide, image, scr, vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    r, ds = stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                  [(fields(f, ("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.2 * s),
                   (fields(f, ("body",)), 0.2 * s), (fields(f, ("caption",)), 0.0)], anchor="middle")
    _run_all(ds)
    return r


@register("interface", "points", alts=3)
def _ui_points(k, slide, f, image):
    """A settings list: title above a window; one row per point — numbered badge, head + line, the caller's tag chip.
    Long copy on a small canvas falls back to a window without its bar and tighter rows (alt 1), then — on a landscape
    page — two columns of rows (alt 2); the generality corpus refused four long points on a 10in canvas otherwise."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    raw = f.get("tags")
    if raw is not None and (not isinstance(raw, (list, tuple)) or len(raw) != n):
        raise ValueError("interface.points(): tags= takes one label per point ({} points), got {!r}".format(n, raw))
    tags = [ui_state(t, "points", "tags") for t in raw] if raw is not None else None
    a = alt()
    x0, w0 = 0.06 * W, 0.88 * W
    r, ds = stack(k, slide, "points", x0, w0, 0.06 * H, (0.30 if a == 0 else 0.40) * H,
                  [(fields(f, ("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.0)], anchor="top")
    _run_all(ds)
    top = max((v[1] + v[3] for v in r.values()), default=0.06 * H) + (0.3 if a == 0 else 0.2) * s
    col = _window(k, slide, (x0, top, w0, H - 0.3 * s - top), f, "points", bar=(a == 0))
    if a > 0:
        col = (col[0] - 0.1 * s, col[1] - 0.1 * s, col[2] + 0.2 * s, col[3] + 0.15 * s)
    ncols = 2 if (a == 2 and o == "land" and n >= 3) else 1
    per = -(-n // ncols)
    cgap = 0.5 * s
    cw = (col[2] - cgap * (ncols - 1)) / ncols
    badge = (0.62 if a == 0 else 0.5) * s
    tagsz, tagw = None, 0.0
    if tags:
        szs = [chip_size(k, t, 0.34 * cw, "tag") for t, _st in tags]
        if any(z is None for z in szs):
            raise vl.VLTextOverflow("interface.points(): a tag does not fit its chip — tags={!r}".format([t for t, _ in tags]))
        tagsz = min(szs)
        tagw = max(dot_chip_width(k, t, tagsz) for t, _st in tags) + 0.25 * s
    gap = (0.34 if a == 0 else 0.18) * s
    rowh = (col[3] - gap * (per - 1)) / per
    cells = []
    for i in range(n):
        c, rw = divmod(i, per)
        cx = col[0] + c * (cw + cgap)
        cells.append((cx, col[1] + rw * (rowh + gap)))
    specs = [((cx + badge + 0.25 * s, ry, cw - badge - 0.25 * s - tagw, rowh),
              [("item_head", h)] + ([("item_line", l)] if l else []), {"anchor": "middle"})
             for (cx, ry), (h, l) in zip(cells, pts)]
    planned = plan_together(k, slide, "points", specs)
    rects = dict(r)
    for i, ((rr, d), (cx, ry)) in enumerate(zip(planned, cells)):
        cy = ry + rowh / 2.0
        dk.box(slide, cx, cy - badge / 2.0, badge, badge, fill=_hex(k.P["soft"]), line=dk._as_rgb(_hex(k.P["line"])),
               round=True, r=0.16 * s)
        r2, d2 = flow(k, slide, "points", (cx, cy - badge / 2.0, badge, badge), [("item_no", str(i + 1))],
                      anchor="middle", align="c")
        d2()
        d()
        if tags:
            t, st = tags[i]
            tw_, th_ = dot_chip_width(k, t, tagsz), tagsz / 72.0 * 1.9
            dot_chip(k, slide, cx + cw - tw_, cy - th_ / 2.0, t, tagsz, st)
        if (i % per) < per - 1 and i < n - 1:
            hl = dk.box(slide, cx, ry + rowh + gap / 2.0, cw, 0.012, fill=_hex(k.P["line"]))
            dk.decorative(hl, "a hairline between settings rows")
        rects.update(rr)
    return rects


@register("interface", "quote", alts=2)
def _ui_quote(k, slide, f, image):
    """A chat message: the avatar's initials (from a Latin attribution), the quote in a bubble, the source under it."""
    W, H, s, o = ctx(k)
    a = text_of(f, "attribution")
    ini = initials(a)
    av = 1.0 * s
    x = (0.10 if alt() == 0 else 0.06) * W
    bx = x + (av + 0.35 * s if ini else 0.0)
    bw = (0.90 * W if o == "land" else 0.93 * W) - bx
    ah = 0.7 * s if a else 0.0
    bub = (bx, 0.16 * H, bw, H - 0.16 * H - 0.45 * s - ah - 0.3 * s)
    pad = 0.5 * s
    r, d = flow(k, slide, "quote", (bub[0] + pad, bub[1] + pad, bub[2] - 2 * pad, bub[3] - 2 * pad), fields(f, ("quote",)),
                anchor="middle")
    qt = min(v[1] for v in r.values())
    qb = max(v[1] + v[3] for v in r.values())
    bub = (bub[0], qt - pad, bub[2], qb - qt + 2 * pad)
    na.ui_bubble(slide, *bub, fill=k.P["panel"], line=k.P["line"], r=0.32 * s)
    if ini:
        dk.disc(slide, x, bub[1], av, fill=_hex(k.P["states"]["primary"]))
        r0, d0 = flow(k, slide, "quote", (x, bub[1], av, av), [("initials", ini)], anchor="middle", align="c", ink="FFFFFF")
        d0()
    d()
    rects = dict(r)
    if a:
        r2, d2 = flow(k, slide, "quote", (bub[0] + pad, bub[1] + bub[3] + 0.25 * s, bub[2] - 2 * pad, ah),
                      [("attribution", a)], anchor="top")
        d2()
        rects.update(r2)
    return rects


@register("interface", "data", alts=2)
def _ui_data(k, slide, f, image):
    """A dashboard card: label, the number, a progress bar when total= is given (tally's rules); the note as a notice
    BESIDE the card on a landscape page (under it on a portrait one), sized to its words."""
    W, H, s, o = ctx(k)
    num, total = text_of(f, "number"), text_of(f, "total")
    frac = share_of("interface", num, total)
    note = text_of(f, "note")
    if o == "land":
        card = (0.06 * W, 0.12 * H, (0.56 if note else 0.88) * W if alt() == 0 else (0.50 if note else 0.88) * W, 0.76 * H)
        ncol = (card[0] + card[2] + 0.45 * s, None, 0.94 * W - card[0] - card[2] - 0.45 * s, None)
    else:
        card = (0.07 * W, 0.07 * H, 0.86 * W, (0.52 if alt() == 0 else 0.46) * H)
        ncol = (0.07 * W, card[1] + card[3] + 0.4 * s, 0.86 * W, None)
    col = _window(k, slide, card, f, "data", bar=False)
    barh = 0.45 * s if frac is not None else 0.0
    r, ds = stack(k, slide, "data", col[0], col[2], col[1], col[1] + col[3] - barh,
                  [(fields(f, ("label",)), 0.15 * s), ([("number", num)] if num else [], 0.0)], anchor="middle")
    _run_all(ds)
    if frac is not None:
        foot = max(v[1] + v[3] for v in r.values())
        na.share_bar(slide, col[0], foot + 0.25 * s, col[2], frac, track=k.P["line"], fill=k.P["states"]["primary"],
                     h=0.16 * s)
    rects = dict(r)
    if note:
        dd, pad = 0.42 * s, 0.32 * s
        tx = ncol[0] + pad + dd + 0.25 * s
        tw = ncol[0] + ncol[2] - pad - tx
        room = (H - 0.4 * s - ncol[1]) if o != "land" else card[3]
        r2, d2 = flow(k, slide, "data", (tx, 0, tw, room - 2 * pad), [("note", note)], anchor="top")
        nh = max(v[3] for v in r2.values()) + 2 * pad
        ny = card[1] + (card[3] - nh) / 2.0 if o == "land" else ncol[1]
        r2, d2 = flow(k, slide, "data", (tx, ny + pad, tw, nh - 2 * pad), [("note", note)], anchor="middle")
        na.ui_window(slide, ncol[0], ny, ncol[2], nh, fill=k.P["panel"], line=k.P["line"], drop=k.P["drop"], r=0.22 * s)
        dk.disc(slide, ncol[0] + pad, ny + (nh - dd) / 2.0, dd, fill=_hex(k.P["states"]["primary"]))
        r1, d1 = flow(k, slide, "data", (ncol[0] + pad, ny + (nh - dd) / 2.0, dd, dd), [("item_no", "i")],
                      anchor="middle", align="c", ink="FFFFFF")
        d1()
        d2()
        rects.update(r2)
    return rects


@register("interface", "closing", alts=2)
def _ui_closing(k, slide, f, image):
    """A dialog: title and line in a centred window, the caller's actions as its buttons."""
    W, H, s, o = ctx(k)
    acts = _actions(f, "closing")
    ww = (0.62 if alt() == 0 else 0.80) * W if o == "land" else 0.86 * W
    wh = (0.62 if o == "land" else 0.50) * H
    win = ((W - ww) / 2.0, (H - wh) / 2.0, ww, wh)
    col = _window(k, slide, win, f, "closing", bar=False)
    bh = (vl.TYPE["interface"]["action"][0] * s / 72.0 * 2.6 + 0.4 * s) if acts else 0.0
    r, ds = stack(k, slide, "closing", col[0], col[2], col[1], col[1] + col[3] - bh,
                  [(fields(f, ("title",)), 0.25 * s), (fields(f, ("line",)), 0.0)], anchor="middle")
    _run_all(ds)
    if acts:
        foot = max(v[1] + v[3] for v in r.values())
        _buttons(k, slide, col[0], foot + 0.4 * s, acts, col[2])
    return r
