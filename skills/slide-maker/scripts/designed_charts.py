#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""designed_charts — a small ROSTER of "designed plot" recipes beyond default bars/lines.

Great data decks don't reach for the same bar chart every time; they pick the chart TYPE that
fits the argument, theme it to the deck, and highlight the ONE thing that matters. These recipes
do that: each renders a clean, themed PNG you place with ``deckkit.picture(..., fit="contain")``,
takes a ``palette`` (list of hex strings — pass your style's ACCENTS) and an optional
``highlight`` index (that series in the accent, the rest dropped to a neutral grey), and supports
``dark=True`` to match a dark deck. Transparent background by default so it sits on any slide.

For a **CJK (Chinese/Japanese/Korean) deck**, pass ``font="<an installed CJK face>"`` (e.g. your
``deckkit.EAFONT``) so category/axis/series labels render real glyphs instead of tofu — matplotlib
uses its first resolvable font for all text, so the CJK face must lead. (Latin/numbers still render
fine in a CJK face.) If no CJK font is installed, keep chart text Latin/numeric and label the
categories with ``deckkit.text()`` around the chart — the same fallback as ``equation_png``.

Pick by argument (see references/data-viz.md):
  donut_kpi   — part-to-whole + one headline number in the hole
  dumbbell    — before→after / gap between two values per category
  slope       — rank/level change between exactly two points in time
  dual_axis   — two trends on different scales (e.g. success ↑ vs cost ↓)
  bubble_trend— x vs y with a third (size) dimension + a fair-value trend line
  pareto      — ranked bars + cumulative % (the "vital few")

All emit a single highlight per the deck's one-accent discipline; pair each with a
``deckkit.takeaway_rail`` so the chart always carries its "so-what".
"""
import os

# CJK-capable font candidates, broad across OSes/name-variants (PingFang SC/HK/TC, Heiti SC/TC, …),
# so chart labels in any language render a real glyph instead of tofu (□). matplotlib only USES a font
# it can resolve, and the same family is named differently per machine — so we detect what's actually
# installed (below) rather than trusting one name. "Arial Unicode MS" is a broad universal fallback.
_CJK_CANDIDATES = [
    "PingFang SC", "PingFang HK", "PingFang TC", "Hiragino Sans GB", "Hiragino Sans",
    "Heiti SC", "Heiti TC", "STHeiti", "Microsoft YaHei", "SimHei",
    "Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK KR", "Source Han Sans SC",
    "Songti SC", "STSong", "Noto Serif CJK SC", "Apple SD Gothic Neo", "Nanum Gothic",
    "Arial Unicode MS", "Sarasa Gothic SC", "WenQuanYi Zen Hei",
]
_cjk_cache = None

def _available_cjk():
    global _cjk_cache
    if _cjk_cache is None:
        from matplotlib import font_manager
        avail = {f.name for f in font_manager.fontManager.ttflist}
        _cjk_cache = [n for n in _CJK_CANDIDATES if n in avail]   # only fonts matplotlib can actually use
    return _cjk_cache


def _mpl(dark, font=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # Latin face(s) first, then whatever CJK fonts are actually installed → labels in any language
    # resolve. If no CJK font is installed, charts can't render CJK (label around them in deckkit
    # text() instead — see references/data-viz.md), the same limit as equation_png.
    stack = ([font] if font else []) + ["Helvetica Neue", "Arial"] + _available_cjk() + ["DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = stack
    plt.rcParams["axes.unicode_minus"] = False    # render a real minus glyph
    ink = "#E8ECF5" if dark else "#1A1A22"
    grid = "#2A3050" if dark else "#E7E9F0"
    muted = "#8A93A6" if dark else "#9AA0AE"
    return plt, ink, grid, muted


def _save(fig, out, transparent=True):
    fig.savefig(out, bbox_inches="tight", transparent=transparent, dpi=200)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return out


def _palette(palette, n, highlight, neutral):
    """Return n colors: the highlighted index keeps its hue, the rest fall to `neutral`."""
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D", "#E0529C", "#1B7A3D"]
    cols = [pal[i % len(pal)] for i in range(n)]
    if highlight is not None:
        cols = [pal[highlight % len(pal)] if i == highlight else neutral for i in range(n)]
    return cols


def _numlabel(v):
    """Format a value for a data label: numeric → compact, a pre-formatted string → as-is (so a
    string value labels gracefully instead of crashing on the :g format spec)."""
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return str(v)


def donut_kpi(out, segments, center_value, center_label, *, palette=None, dark=False, font=None, figsize=(5.2, 4.0)):
    """Part-to-whole donut with a headline KPI in the hole. segments = [(label, value), ...]."""
    if not segments:
        raise ValueError("donut_kpi needs at least one segment")
    plt, ink, grid, muted = _mpl(dark, font)
    labels = [s[0] for s in segments]; vals = [s[1] for s in segments]
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D", "#E0529C", "#1B7A3D"]
    cols = [pal[i % len(pal)] for i in range(len(vals))]
    if sum(v for v in vals) <= 0:           # zero-total → even placeholder ring (no NaN crash)
        vals = [1] * len(vals) if vals else [1]
    fig, ax = plt.subplots(figsize=figsize)
    ax.pie(vals, colors=cols, startangle=90, counterclock=False,
           wedgeprops=dict(width=0.34, edgecolor="none"))
    ax.text(0, 0.12, center_value, ha="center", va="center", fontsize=30, fontweight="bold", color=ink)
    ax.text(0, -0.22, center_label, ha="center", va="center", fontsize=11, color=muted)
    ax.legend(labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False,
              fontsize=10, labelcolor=ink)
    ax.set(aspect="equal")
    return _save(fig, out)


def dumbbell(out, rows, *, palette=None, dark=False, font=None, highlight=None, a_label="before", b_label="after", figsize=(6.6, 4.0)):
    """Gap between two values per category. rows = [(label, value_a, value_b), ...]."""
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D"]
    acc, acc2, neutral = pal[0], (pal[1] if len(pal) > 1 else pal[0]), "#9AA0AE"
    labels = [r[0] for r in rows]; A = [r[1] for r in rows]; B = [r[2] for r in rows]
    ys = list(range(len(rows)))[::-1]
    fig, ax = plt.subplots(figsize=figsize)
    for i, y in enumerate(ys):
        em = (highlight is None or i == highlight)
        ax.plot([A[i], B[i]], [y, y], color=(acc if em else grid), lw=3 if em else 2, zorder=1, solid_capstyle="round")
        ax.scatter([A[i]], [y], color=neutral if not em else acc2, s=70, zorder=2)
        ax.scatter([B[i]], [y], color=neutral if not em else acc, s=70, zorder=2)
        ax.annotate(_numlabel(B[i]), (B[i], y), textcoords="offset points", xytext=(8, 0),
                    va="center", fontsize=9.5, color=ink, fontweight="bold")
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=11, color=ink)
    ax.scatter([], [], color=acc2, s=70, label=a_label); ax.scatter([], [], color=acc, s=70, label=b_label)
    ax.legend(loc="lower right", frameon=False, fontsize=10, labelcolor=ink)
    for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(muted); ax.tick_params(colors=muted)
    ax.xaxis.grid(True, color=grid, lw=0.7); ax.set_axisbelow(True)
    return _save(fig, out)


def slope(out, series, *, palette=None, dark=False, font=None, highlight=None, t0="", t1="", figsize=(5.4, 4.2)):
    """Rank/level change between TWO points in time. series = [(label, start, end), ...]."""
    plt, ink, grid, muted = _mpl(dark, font)
    cols = _palette(palette, len(series), highlight, "#C2C6D2")
    fig, ax = plt.subplots(figsize=figsize)
    for i, (lab, a, b) in enumerate(series):
        em = (highlight is None or i == highlight)
        ax.plot([0, 1], [a, b], color=cols[i], lw=3 if em else 1.8, marker="o", ms=7, zorder=2 if em else 1)
        ax.text(-0.04, a, f"{lab}  {_numlabel(a)}", ha="right", va="center", fontsize=10, color=ink if em else muted,
                fontweight="bold" if em else "normal")
        ax.text(1.04, b, _numlabel(b), ha="left", va="center", fontsize=10, color=ink if em else muted,
                fontweight="bold" if em else "normal")
    ax.set_xlim(-0.5, 1.5); ax.set_xticks([0, 1]); ax.set_xticklabels([t0, t1], fontsize=11, color=ink)
    for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(muted); ax.set_yticks([]); ax.tick_params(colors=muted)
    return _save(fig, out)


def dual_axis(out, x, left, right, *, left_label="", right_label="", palette=None, dark=False, font=None,
              left_fmt="{:g}", right_fmt="{:g}", figsize=(6.8, 4.0)):
    """Two trends on different scales — the classic 'A rises while B falls' tradeoff."""
    if not x or not left or not right:
        raise ValueError("dual_axis needs non-empty x, left, right")
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#1F9D55", "#E0529C"]
    c1 = pal[0]; c2 = pal[1] if len(pal) > 1 else "#E0529C"   # single-colour palette → contrasting 2nd hue
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2 = ax1.twinx()
    ax1.plot(x, left, color=c1, lw=3, marker="o", ms=5, zorder=3)
    ax1.fill_between(x, left, min(left), color=c1, alpha=0.10)
    ax2.plot(x, right, color=c2, lw=3, marker="o", ms=5, zorder=3)
    ax1.set_ylabel(left_label, color=c1, fontsize=11); ax2.set_ylabel(right_label, color=c2, fontsize=11)
    ax1.annotate(left_fmt.format(left[-1]), (x[-1], left[-1]), textcoords="offset points", xytext=(6, 6),
                 color=c1, fontsize=10, fontweight="bold")
    ax2.annotate(right_fmt.format(right[-1]), (x[-1], right[-1]), textcoords="offset points", xytext=(6, -12),
                 color=c2, fontsize=10, fontweight="bold")
    for ax, c in ((ax1, c1), (ax2, c2)):
        ax.tick_params(axis="y", colors=c); ax.tick_params(axis="x", colors=muted)
    for sp in ("top",): ax1.spines[sp].set_visible(False); ax2.spines[sp].set_visible(False)
    ax1.spines["bottom"].set_color(muted); ax1.xaxis.grid(True, color=grid, lw=0.7); ax1.set_axisbelow(True)
    return _save(fig, out)


def bubble_trend(out, points, *, palette=None, dark=False, font=None, trend=True, xlabel="", ylabel="", figsize=(6.6, 4.2)):
    """x vs y with a size dimension + an optional fair-value trend line. points = [(x,y,size,label)]."""
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0"]
    acc = pal[0]
    xs = [p[0] for p in points]; ys = [p[1] for p in points]; ss = [p[2] for p in points]
    smax = max(ss) or 1
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(xs, ys, s=[120 + 1400 * (v / smax) for v in ss], color=acc, alpha=0.55, edgecolor=acc, lw=1.2, zorder=2)
    for p in points:
        if len(p) > 3 and p[3]:
            ax.annotate(p[3], (p[0], p[1]), textcoords="offset points", xytext=(0, 10), ha="center",
                        fontsize=9.5, color=ink)
    if trend and len(points) >= 2:
        import numpy as np
        m, b = np.polyfit(xs, ys, 1)
        xr = [min(xs), max(xs)]
        ax.plot(xr, [m * v + b for v in xr], color=muted, lw=1.6, ls="--", zorder=1)
    ax.set_xlabel(xlabel, color=ink, fontsize=11); ax.set_ylabel(ylabel, color=ink, fontsize=11)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(muted)
    ax.tick_params(colors=muted); ax.grid(True, color=grid, lw=0.6); ax.set_axisbelow(True)
    return _save(fig, out)


def pareto(out, items, *, palette=None, dark=False, font=None, figsize=(6.8, 4.0)):
    """Ranked bars + cumulative % line — the 'vital few' that drive the total. items=[(label,value)]."""
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0"]; acc = pal[0]
    items = sorted(items, key=lambda t: t[1], reverse=True)
    labels = [i[0] for i in items]; vals = [i[1] for i in items]
    tot = sum(vals) or 1; cum = []; run = 0
    for v in vals:
        run += v; cum.append(100 * run / tot)
    xs = list(range(len(vals)))
    fig, ax = plt.subplots(figsize=figsize); ax2 = ax.twinx()
    ax.bar(xs, vals, color=acc, width=0.62)
    ax2.plot(xs, cum, color=muted, lw=2, marker="o", ms=5)
    ax2.set_ylim(0, 105)
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=10, color=ink, rotation=0)
    ax.tick_params(axis="y", colors=muted); ax2.tick_params(axis="y", colors=muted)
    for sp in ("top",): ax.spines[sp].set_visible(False); ax2.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(muted)
    return _save(fig, out)
