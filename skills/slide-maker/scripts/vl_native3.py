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
        # the button fill, not the state hue (5B8CFF on dark is too light for white); item_no is accent-keyed, so the
        # white goes to accent= — an ink= override alone left the glyph in accent blue on the blue disc
        dk.disc(slide, ncol[0] + pad, ny + (nh - dd) / 2.0, dd, fill=_hex(k.P["primary_fill"]))
        r1, d1 = flow(k, slide, "data", (ncol[0] + pad, ny + (nh - dd) / 2.0, dd, dd), [("item_no", "i")],
                      anchor="middle", align="c", ink="FFFFFF", accent="FFFFFF")
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


# ═══════════════════════════════════ wayfinding 导视线路 ═══════════════════════════════════
# The plain word for exit in each script: 出口 on Chinese and Japanese signs, 출구 on Korean ones ("1번 출구").
# "나가는 곳" was the planned Korean wording; a search (2026-10-10) found no source naming it the standard
# sign text, so the dictionary word stands.
LABELS3 = {"way_out": {"en": "Way out", "zh": "出口", "ja": "出口", "ko": "출구"}}


def ink_on(k, fill):
    """The page's ink or white on a coloured fill — whichever reads better (a yellow roundel takes the dark ink)."""
    return "FFFFFF" if vl._contrast("FFFFFF", fill) >= vl._contrast(k.P["ink"], fill) else k.P["ink"]


def line_colour(k, n):
    """A section's line colour from its number: 1 red, 2 blue, 3 green, 4 yellow, 5 purple, repeating."""
    try:
        i = max(1, int(str(n).strip())) - 1
    except ValueError:
        i = 0
    return k.P["lines"][i % len(k.P["lines"])]


def _line_code(k, f, page):
    """line=: the caller's 1-3 character line code, optionally (code, colour name). Remembered for the deck."""
    v = f.get("line") if f.get("line") is not None else k.memo.get("line")
    if f.get("line") is not None:
        k.memo = dict(k.memo, line=f.get("line"))
    if v is None:
        return None
    names = {"red": 0, "blue": 1, "green": 2, "yellow": 3, "purple": 4}
    code, colour = (v, None) if isinstance(v, str) else (tuple(v) + (None,))[:2] if isinstance(v, (list, tuple)) else (None, None)
    if not isinstance(code, str) or not 1 <= len(code.strip()) <= 3 or (colour is not None and colour not in names):
        raise ValueError("wayfinding.{}(): line= takes a 1-3 character line code, or (code, colour) with colour in {} — "
                         "got {!r}".format(page, sorted(names), v))
    return code.strip(), k.P["lines"][names[colour]] if colour else k.P["lines"][0]


def _roundel(k, slide, cx, cy, d, text, fill):
    W, H, s, o = ctx(k)
    sz = min(vl.TYPE["wayfinding"]["roundel"][0] * s * d / (0.5 * s), d * 72 * 0.5)
    return na.roundel(slide, cx, cy, d, text, fill=fill, ink=ink_on(k, fill), size=sz, face=k.face("display"),
                      ea_face=k.ea_face("display", text))


def ordinary_sign(slide):
    """rs.ground for wayfinding: a navy sign strip with the yellow edge across the top; the content rect below it."""
    import vl_native2 as v2
    k = v2.kit_for("wayfinding", slide)
    W, H, s, o = ctx(k)
    h = 0.34 * s
    dk.box(slide, 0, 0, W, h, fill=_hex(k.P["sign"]))
    e = dk.box(slide, 0, h, W, 0.05 * s, fill=_hex(k.P["edge"]))
    dk.decorative(e, "the sign strip's edge")
    return (0.07 * W, h + 0.35 * s, 0.86 * W, H - h - 0.8 * s)


@register("wayfinding", "cover", alts=2)
def _wf_cover(k, slide, f, image):
    """Two or three lines converge on an interchange; kicker + title as the destination; the subtitle on a sign."""
    W, H, s, o = ctx(k)
    lc = _line_code(k, f, "cover")
    lw = 0.16 * s
    if o == "land":
        ix, iy = (0.50 if alt() == 0 else 0.44) * W, 0.52 * H
        col = (ix + 0.75 * s, 0.18 * H, 0.94 * W - ix - 0.75 * s, 0.70 * H)
    else:
        ix, iy = 0.55 * W, 0.30 * H
        col = (0.07 * W, iy + 0.9 * s, 0.86 * W, H - iy - 0.9 * s - 0.5 * s)
    L = k.P["lines"]
    ya = iy - 0.23 * H if o == "land" else iy - 0.18 * H
    na.route(slide, [(0, ya), (ix - (iy - ya), ya), (ix, iy)], L[0], w=lw)
    na.route(slide, [(0, iy), (ix, iy)], L[1], w=lw)
    if o == "land":
        xc = ix - 0.6 * (H - iy)
        na.route(slide, [(xc, H), (xc, iy + (ix - xc)), (ix, iy)], L[2], w=lw)
    else:
        # on a portrait or square page the words sit UNDER the interchange, so the third line comes in from the top
        # edge and stays above it (from the bottom it ran through the kicker and the title — render review)
        xc = min(max(0.18 * W, ix - iy + 0.2 * s), ix - 0.3 * s)
        na.route(slide, [(xc, 0.0), (xc, max(0.0, iy - (ix - xc))), (ix, iy)], L[2], w=lw)
    for x_, y_ in ((0.12 * W, ya), (0.27 * W, ya), (0.12 * W, iy)):
        if x_ < ix - (iy - ya) - 0.3 * s:
            dk.decorative(na.station(slide, x_, y_, 0.26 * s, ring=k.P["casing"]), "a station on the network")
    na.interchange(slide, ix, iy, 1.0 * s, 0.7 * s, ring=k.P["casing"])
    sub = text_of(f, "subtitle")
    sh = 0.0
    if sub:
        sh = 0.95 * s
    r, ds = stack(k, slide, "cover", col[0], col[2], col[1], col[1] + col[3] - (sh + 0.4 * s if sub else 0.0),
                  [(fields(f, ("kicker",), capsed=("kicker",)), 0.12 * s), (fields(f, ("title",)), 0.0)], anchor="middle")
    _run_all(ds)
    rects = dict(r)
    if sub:
        foot = max((v[1] + v[3] for v in r.values()), default=col[1]) + 0.4 * s
        inner = na.sign_panel(slide, col[0], foot, col[2], sh, fill=k.P["sign"])
        tx = inner[0] + 0.2 * s
        if lc:
            d = 0.52 * s
            _roundel(k, slide, inner[0] + 0.15 * s + d / 2.0, inner[1] + inner[3] / 2.0, d, lc[0], lc[1])
            tx = inner[0] + 0.3 * s + d
        aw = 0.5 * s
        r2, d2 = flow(k, slide, "cover", (tx, inner[1], inner[0] + inner[2] - tx - aw - 0.35 * s, inner[3]),
                      [("subtitle", sub)], anchor="middle", ink=k.P["sign_ink"])
        d2()
        ar = dk.arrow(slide, inner[0] + inner[2] - aw - 0.2 * s, inner[1] + inner[3] / 2.0 - 0.18 * s, aw, 0.36 * s,
                      color=dk._as_rgb(_hex(k.P["sign_ink"])))
        dk.decorative(ar, "the sign's direction arrow")
        rects.update(r2)
    return rects


@register("wayfinding", "section", alts=2)
def _wf_section(k, slide, f, image):
    """A station-name sign across the page: the roundel (section number, or the line code), kicker, title, arrow."""
    W, H, s, o = ctx(k)
    num = text_of(f, "number")
    lc = _line_code(k, f, "section")
    band = (0, (0.28 if alt() == 0 else 0.20) * H, W, (0.44 if alt() == 0 else 0.60) * H)
    dk.box(slide, *band, fill=_hex(k.P["sign"]))
    e = dk.box(slide, 0, band[1], W, 0.08 * s, fill=_hex(k.P["edge"]))
    dk.decorative(e, "the sign's yellow edge")
    d = min(1.6 * s, band[3] * 0.62)
    x = 0.07 * W
    label = lc[0] if lc else num
    if label:
        fill = lc[1] if lc else line_colour(k, num)
        _roundel(k, slide, x + d / 2.0, band[1] + band[3] / 2.0, d, label, fill)
        x += d + 0.5 * s
    r, ds = stack(k, slide, "section", x, 0.93 * W - x - 1.0 * s, band[1] + 0.25 * s, band[1] + band[3] - 0.2 * s,
                  [(fields(f, ("kicker",), capsed=("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.0)], anchor="middle",
                  ink=k.P["sign_ink"], mute=k.P["sign_mute"])
    _run_all(ds)
    ar = dk.arrow(slide, 0.93 * W - 0.85 * s, band[1] + band[3] / 2.0 - 0.3 * s, 0.85 * s, 0.6 * s,
                  color=dk._as_rgb(_hex(k.P["sign_ink"])))
    dk.decorative(ar, "the sign's direction arrow")
    return r


@register("wayfinding", "image_text", alts=2)
def _wf_image_text(k, slide, f, image):
    """The picture as a station poster in a sign frame; kicker, title, body, caption beside it."""
    W, H, s, o = ctx(k)
    if o == "land":
        fr = (0.06 * W, 0.10 * H, (0.48 if alt() == 0 else 0.40) * W, 0.80 * H)
        cx0 = fr[0] + fr[2] + 0.55 * s
        col = (cx0, 0.14 * H, 0.94 * W - cx0, 0.72 * H)
    else:
        fr = (0.07 * W, 0.05 * H, 0.86 * W, (0.46 if alt() == 0 else 0.38) * H)
        cy0 = fr[1] + fr[3] + 0.4 * s
        col = (0.07 * W, cy0, 0.86 * W, H - 0.5 * s - cy0)
    inner = na.sign_panel(slide, *fr, fill=k.P["sign"])
    pad = 0.12 * s
    vl._place_image(k, slide, image, (inner[0] + pad, inner[1] + pad, inner[2] - 2 * pad, inner[3] - 2 * pad),
                    vl.L_((0, 0, 1, 1), "frame", None), "image_text")
    r, ds = stack(k, slide, "image_text", col[0], col[2], col[1], col[1] + col[3],
                  [(fields(f, ("kicker",), capsed=("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.2 * s),
                   (fields(f, ("body",)), 0.2 * s), (fields(f, ("caption",)), 0.0)], anchor="middle")
    _run_all(ds)
    return r


def _interchange_ix(f, n):
    v = f.get("interchange")
    if v is None:
        return set()
    if not f.get("ordered"):
        raise ValueError("wayfinding.points(): interchange= marks stops on a route, so it needs ordered=True — "
                         "unordered points are a directory sign with no route")
    if not isinstance(v, (list, tuple)) or not all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < n for i in v):
        raise ValueError("wayfinding.points(): interchange= takes point indexes 0..{} — got {!r}".format(n - 1, v))
    return set(v)


@register("wayfinding", "points", alts=2)
def _wf_points(k, slide, f, image):
    """ordered=True: a strip map (stations on one line, names alternating above and below; a vertical route on a
    portrait page). Otherwise a directory sign: one row per point with its numbered roundel — no route, no order."""
    W, H, s, o = ctx(k)
    pts = points_of(f.get("items"))
    n = len(pts)
    ordered = f.get("ordered")
    if ordered not in (None, True, False):
        raise ValueError("wayfinding.points(): ordered= takes True or False, got {!r}".format(ordered))
    ixs = _interchange_ix(f, n)
    x0, w0 = 0.07 * W, 0.86 * W
    colour = (_line_code(k, f, "points") or (None, k.P["lines"][1]))[1]
    if not ordered:
        a = alt()
        r, ds = stack(k, slide, "points", x0, w0, 0.06 * H, (0.30 if a == 0 else 0.40) * H,
                      [(fields(f, ("kicker",), capsed=("kicker",)), 0.1 * s), (fields(f, ("title",)), 0.0)], anchor="top")
        _run_all(ds)
        top = max((v[1] + v[3] for v in r.values()), default=0.07 * H) + (0.35 if a == 0 else 0.22) * s
        inner = na.sign_panel(slide, x0, top, w0, H - 0.35 * s - top, fill=k.P["sign"])
        d = (0.56 if a == 0 else 0.44) * s
        tx = inner[0] + 0.3 * s + d + 0.3 * s
        gap = (0.2 if a == 0 else 0.08) * s
        rowh = (inner[3] - 0.4 * s - gap * (n - 1)) / n
        specs = [((tx, inner[1] + 0.2 * s + i * (rowh + gap), inner[0] + inner[2] - tx - 1.0 * s, rowh),
                  [("item_head", h)] + ([("item_line", l)] if l else []), {"anchor": "middle", "ink": k.P["sign_ink"],
                                                                            "mute": k.P["sign_mute"]})
                 for i, (h, l) in enumerate(pts)]
        planned = plan_together(k, slide, "points", specs)
        rects = dict(r)
        for i, (rr, dd) in enumerate(planned):
            cy = inner[1] + 0.2 * s + i * (rowh + gap) + rowh / 2.0
            _roundel(k, slide, inner[0] + 0.35 * s + d / 2.0, cy, d, str(i + 1), k.P["lines"][i % len(k.P["lines"])])
            dd()
            ar = dk.arrow(slide, inner[0] + inner[2] - 0.75 * s, cy - 0.2 * s, 0.5 * s, 0.4 * s,
                          color=dk._as_rgb(_hex(k.P["sign_ink"])))
            dk.decorative(ar, "a direction arrow on the directory sign")
            if i < n - 1:
                hl = dk.box(slide, tx, cy + rowh / 2.0 + gap / 2.0, inner[0] + inner[2] - tx - 0.3 * s, 0.012,
                            fill=_hex(k.P["sign_mute"]))
                dk.decorative(hl, "a rule between directory rows")
            rects.update(rr)
        return rects
    # the strip map: the title on a sign band, the route under it
    r, ds = stack(k, slide, "points", x0 + 0.3 * s, w0 - 0.6 * s, 0.07 * H + 0.2 * s, 0.07 * H + 1.6 * s,
                  [(fields(f, ("title",)), 0.0)], anchor="top", ink=k.P["sign_ink"])
    tb = max(v[1] + v[3] for v in r.values()) + 0.2 * s
    na.sign_panel(slide, x0, 0.07 * H, w0, tb - 0.07 * H, fill=k.P["sign"])
    _run_all(ds)
    rects = dict(r)
    lw = 0.2 * s
    sd = 0.42 * s
    if o == "land":
        y = tb + (H - tb) * 0.50
        xs = [x0 + 0.5 * s + i * (w0 - 1.0 * s) / (n - 1) for i in range(n)]
        cw = min(2.8 * s, (w0 - 0.5 * s) / max(2, n) * 1.6)
        specs = []
        for i, (h, l) in enumerate(pts):
            up = i % 2 == 0
            ry = (tb + 0.3 * s) if up else (y + sd / 2.0 + 0.35 * s)
            rh = (y - sd / 2.0 - 0.35 * s - ry) if up else (H - 0.4 * s - ry)
            cx = min(max(xs[i] - 0.2 * s, x0), x0 + w0 - cw)
            specs.append(((cx, ry, cw, rh), [("item_head", h)] + ([("item_line", l)] if l else []),
                          {"anchor": "bottom" if up else "top"}))
        planned = plan_together(k, slide, "points", specs)
        na.route(slide, [(0.0, y), (W, y)], colour, w=lw)
        for i, x in enumerate(xs):
            if i in ixs:
                na.interchange(slide, x, y, 0.8 * s, 0.56 * s, ring=k.P["casing"])
            else:
                na.station(slide, x, y, sd, ring=k.P["casing"])
        for rr, dd in planned:
            dd()
            rects.update(rr)
        return rects
    x = x0 + 0.3 * s
    ys = [tb + 0.6 * s + i * (H - 0.8 * s - tb - 0.6 * s) / (n - 1) for i in range(n)]
    specs = [((x + 0.6 * s, yy - 0.5 * s, w0 - 0.9 * s, 1.0 * s), [("item_head", h)] + ([("item_line", l)] if l else []),
              {"anchor": "middle"}) for yy, (h, l) in zip(ys, pts)]
    planned = plan_together(k, slide, "points", specs)
    na.route(slide, [(x, tb + 0.2 * s), (x, H)], colour, w=lw)
    for i, yy in enumerate(ys):
        if i in ixs:
            na.interchange(slide, x, yy, 0.56 * s, 0.8 * s, ring=k.P["casing"])
        else:
            na.station(slide, x, yy, sd, ring=k.P["casing"])
    for rr, dd in planned:
        dd()
        rects.update(rr)
    return rects


@register("wayfinding", "quote", alts=2)
def _wf_quote(k, slide, f, image):
    """The quote on an enamel sign; the source under it."""
    W, H, s, o = ctx(k)
    a = text_of(f, "attribution")
    x = (0.08 if alt() == 0 else 0.05) * W
    w = W - 2 * x
    ah = 0.7 * s if a else 0.0
    pad = 0.55 * s
    r, d = flow(k, slide, "quote", (x + pad, 0.14 * H + pad, w - 2 * pad, H - 0.14 * H - 0.45 * s - ah - 2 * pad),
                fields(f, ("quote",)), anchor="middle", ink=k.P["sign_ink"])
    qt = min(v[1] for v in r.values())
    qb = max(v[1] + v[3] for v in r.values())
    na.sign_panel(slide, x, qt - pad, w, qb - qt + 2 * pad, fill=k.P["sign"])
    d()
    rects = dict(r)
    if a:
        r2, d2 = flow(k, slide, "quote", (x, qb + pad + 0.25 * s, w, ah), [("attribution", "— " + a)], anchor="top")
        d2()
        rects.update(r2)
    return rects


def _flow_right(k, slide, page, col, items, **kw):
    """flow() set flush RIGHT: the kit's measured flow knows left and centre, so the words are planned left in the
    full column and their paragraphs turned right when drawn (a board's values line up on their right edge)."""
    r, d = flow(k, slide, page, col, items, align="l", **kw)

    def go():
        n0 = len(slide.shapes)
        d()
        for sh in list(slide.shapes)[n0:]:
            if getattr(sh, "has_text_frame", False):
                for p_ in sh.text_frame.paragraphs:
                    p_.alignment = dk.PP_ALIGN.RIGHT
    return r, go


def _board_rows(f):
    v = f.get("board")
    if v is None:
        return []
    ok_ = isinstance(v, (list, tuple)) and 1 <= len(v) <= 4 and all(
        isinstance(t, (list, tuple)) and len(t) == 2 and all(isinstance(x, str) and x.strip() for x in t) for t in v)
    if not ok_:
        raise ValueError("wayfinding.data(): board= takes 1 to 4 (label, value) rows under the page's own row, got {!r}"
                         .format(v))
    return [(a.strip(), b.strip()) for a, b in v]


@register("wayfinding", "data", alts=2)
def _wf_data(k, slide, f, image):
    """A departure board: the page's label and number as the first, largest row; the caller's board= rows under it;
    the note beneath the board."""
    W, H, s, o = ctx(k)
    rows = _board_rows(f)
    num, lab, note = text_of(f, "number"), text_of(f, "label"), text_of(f, "note")
    x0, w0 = 0.06 * W, 0.88 * W
    nh = 0.9 * s if note else 0.0
    board = (x0, 0.10 * H, w0, H - 0.10 * H - 0.4 * s - nh)
    dk.box(slide, *board, fill=_hex(k.P["board"]), round=True, r=0.14 * s)
    pad = 0.45 * s
    rd = 0.5 * s
    inner = (board[0] + pad, board[1] + pad, board[2] - 2 * pad, board[3] - 2 * pad)
    head_h = inner[3] * (0.55 if rows else 1.0)
    rest_h = inner[3] - head_h
    rects = {}
    lx = inner[0] + rd + 0.4 * s
    if o == "land" and alt() == 0:
        _roundel(k, slide, inner[0] + rd / 2.0, inner[1] + head_h / 2.0, rd, "1", k.P["lines"][0])
        nw = inner[2] * 0.42
        r1, d1 = _flow_right(k, slide, "data", (inner[0] + inner[2] - nw, inner[1], nw, head_h),
                             [("number", num)] if num else [], anchor="middle", ink=k.P["led"])
        r2, d2 = flow(k, slide, "data", (lx, inner[1], inner[2] - nw - (lx - inner[0]) - 0.3 * s, head_h),
                      [("label", lab)] if lab else [], anchor="middle", ink=k.P["led"])
    else:
        # stacked: the label beside its roundel, the number under it across the board's whole width ('1,250,000' did
        # not fit beside a label on a square or A4 page — the generality corpus)
        lh = head_h * 0.38
        _roundel(k, slide, inner[0] + rd / 2.0, inner[1] + lh / 2.0, rd, "1", k.P["lines"][0])
        r2, d2 = flow(k, slide, "data", (lx, inner[1], inner[0] + inner[2] - lx, lh), [("label", lab)] if lab else [],
                      anchor="middle", ink=k.P["led"])
        r1, d1 = _flow_right(k, slide, "data", (inner[0], inner[1] + lh, inner[2], head_h - lh),
                             [("number", num)] if num else [], anchor="middle", ink=k.P["led"])
        nw = inner[2] * 0.42
    d1(); d2()
    rects.update(r1); rects.update(r2)
    if rows:
        rh = rest_h / len(rows)
        for i, (a, b) in enumerate(rows):
            ry = inner[1] + head_h + i * rh
            hl = dk.box(slide, inner[0], ry, inner[2], 0.01, fill=_hex(k.P["board_mute"]))
            dk.decorative(hl, "a rule between board rows")
            _roundel(k, slide, inner[0] + rd * 0.8 / 2.0, ry + rh / 2.0, rd * 0.8, str(i + 2),
                     k.P["lines"][(i + 1) % len(k.P["lines"])])
            ra, da = flow(k, slide, "data", (lx, ry, inner[2] * 0.55, rh), [("row", a)], anchor="middle", ink=k.P["led"])
            rb, db = _flow_right(k, slide, "data", (inner[0] + inner[2] - nw, ry, nw, rh), [("row", b)],
                                 anchor="middle", ink=k.P["led"])
            da(); db()
            rects.update(ra); rects.update(rb)
    if note:
        r3, d3 = flow(k, slide, "data", (x0, board[1] + board[3] + 0.25 * s, w0, nh - 0.1 * s), [("note", note)],
                      anchor="top")
        d3()
        rects.update(r3)
    return rects


@register("wayfinding", "closing", alts=2)
def _wf_closing(k, slide, f, image):
    """The way-out sign: the localised label, the title and line in white on green; the route ends at a terminus."""
    W, H, s, o = ctx(k)
    lab = LABELS3["way_out"][lang_of(text_of(f, "title"), text_of(f, "line"), k=k, f=f)]
    x, w = 0.07 * W, (0.66 if alt() == 0 else 0.86) * W if o == "land" else 0.86 * W
    top = 0.14 * H
    ry = (0.80 if o == "land" else 0.86) * H
    pad = 0.45 * s
    r, ds = stack(k, slide, "closing", x + pad, w - 2 * pad, top + pad, ry - 0.9 * s - pad,
                  [([("exit", caps(lab))], 0.15 * s), (fields(f, ("title",)), 0.2 * s), (fields(f, ("line",)), 0.0)],
                  anchor="top", ink=k.P["exit_ink"], mute=k.P["exit_ink"])
    foot = max(v[1] + v[3] for v in r.values()) + pad
    na.sign_panel(slide, x, top, w, foot - top, fill=k.P["exit"])
    _run_all(ds)
    tx = min(0.62 * W, x + w * 0.85)
    na.route(slide, [(0.0, ry), (tx, ry)], k.P["lines"][0], w=0.16 * s)
    for i in range(3):
        sx = 0.1 * W + i * (tx - 0.1 * W - 0.6 * s) / 3.0
        dk.decorative(na.station(slide, sx, ry, 0.28 * s, ring=k.P["casing"]), "a station before the terminus")
    na.interchange(slide, tx, ry, 0.9 * s, 0.7 * s, ring=k.P["casing"])
    return r


def caps(t):
    return t.upper() if t and not dk._has_cjk(t) and dk.script_of(t) is None else t
