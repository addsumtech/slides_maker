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
  waterfall   — running total built from signed steps (start → +/- deltas → end); no native pptx form
  distribution— SAMPLE data: box plot (n>=5) or mean+/-error (n=3-5) + every observation; the
                form to use whenever a value is a mean of measurements rather than a count
  marimekko   — two dimensions at once: column WIDTH = segment size, height = split within it
  radar       — a multivariate profile across 3-8 axes for <=3 series (limits enforced)

All emit a single highlight per the deck's one-accent discipline; pair each with a
``deckkit.takeaway_rail`` so the chart always carries its "so-what".

IBCS scenario notation (business/status/finance decks): the bar-family recipes — ``pareto`` and
``waterfall`` — take ``scenario=``, either ONE string for the whole chart or a per-bar sequence
(the classic bridge: actual months solid, forecast months hatched). The fill encodes the data
world: ``"actual"`` solid dark ink · ``"prior"`` solid light grey · ``"plan"`` hollow (white face,
dark edge) · ``"forecast"`` hatched ``//``. In ``waterfall`` the treatment keeps each bar's
semantic up/down/total colour as its ink (an FC variance bar = green/red hatch). Where a recipe
shows variance (``waterfall``, ``dumbbell``), ``favorable_color``/``unfavorable_color`` name the
green-favorable / red-unfavorable pair (flip them when *down* is good, e.g. cost) — and never rely
on the hue alone: the recipes pair it with a sign/label. ``scenario=None`` (the default) keeps the
pre-IBCS output unchanged. See references/data-viz.md → "IBCS notation".
"""
import os
import sys

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

# The active visual language's chart defaults, read from deckkit's THEME when a chart is drawn (never a copy that a
# state restore or a new deck could leave stale). Used ONLY when a chart's own palette= / dark= / font= is None, so an
# explicit argument always wins and an ordinary deck (no theme) draws as before.
def theme_defaults():
    dk = sys.modules.get("deckkit")
    th = getattr(dk, "THEME", None) if dk is not None else None
    if not th:
        return {}
    # charts index fixed slots (points, mean line, limits …): six series, padded APART when the language designs
    # fewer (deckkit.theme_series); the face keeps the language's register but never its old-style figures
    return {"palette": ["#" + c for c in dk.theme_series(max(6, len(th.get("series") or [])))],
            "dark": bool(th.get("dark", False)), "font": dk.numeral_face(dk.FONT),
            "ink": "#" + str(th["ink"]).lstrip("#"), "rule": "#" + str(th["rule"]).lstrip("#"),
            "mute": "#" + str(th["mute"]).lstrip("#")}


def _theme(palette, dark, font):
    d = theme_defaults()
    if palette is None and d.get("palette"):
        palette = list(d["palette"])
    if dark is None:
        dark = bool(d.get("dark", False))
    if font is None:
        font = d.get("font")
    return palette, dark, font


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
    d = theme_defaults()
    if d and d["dark"] == bool(dark):        # drawn for the language's own ground: its ink, rules and muted text
        ink, grid, muted = d["ink"], d["rule"], d["mute"]
    return plt, ink, grid, muted


def _save(fig, out, transparent=True):
    """Rasterise — and refuse to ship TOFU.

    matplotlib does not fail on a glyph the resolved font lacks: it draws a hollow box and emits a
    UserWarning nobody reads, so a chart caption or a CJK label can go out as ▯▯▯ with every gate
    green (a radar's own range note shipped "0 ▯ 3" this way). The warning is the only signal there
    is, so it is promoted to an error here, once, for every recipe — including labels the CALLER
    supplied, which is the case no amount of care inside these functions can cover.
    """
    import warnings
    import matplotlib.pyplot as plt
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.savefig(out, bbox_inches="tight", transparent=transparent, dpi=200)
    missing = sorted({str(w.message).split("Glyph ")[1].split(" ")[0]
                      for w in caught if "Glyph" in str(w.message)
                      and "missing from font" in str(w.message)})
    plt.close(fig)
    if missing:
        raise ValueError(
            f"designed_charts: the chart text uses {len(missing)} character(s) the resolved font "
            f"cannot draw (codepoint(s) {', '.join(missing)}), so they would render as tofu boxes. "
            f"Pass font='<a face that has them>' (for CJK, your deckkit.EAFONT), or write the label "
            f"with characters the deck's font actually carries. Arrows/symbols such as → ← ✓ are "
            f"the usual culprits: most text faces omit them even though the deck font looks fine.")
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



# IBCS scenario grammar: which data WORLD a bar shows is encoded in its FILL, so an
# actual-vs-plan-vs-forecast readout scans without a legend. (Docs: references/data-viz.md.)
IBCS_SCENARIOS = ("actual", "prior", "plan", "forecast")
_PRIOR_GREY = "#C2C6D2"                    # PY light grey — same neutral the slope recipe de-emphasizes with


def _scenario_fill(scenario, ink, dark):
    """Map an IBCS scenario name to bar-fill kwargs. ``ink`` is the solid colour the bar would
    otherwise carry (the chart ink for a plain bar family; the semantic up/down/total colour in a
    waterfall). ``scenario=None`` → solid ``ink``, edge-less — the pre-IBCS default, unchanged."""
    if scenario is None:
        return dict(color=ink, edgecolor="none")
    s = str(scenario).lower()
    hollow = "none" if dark else "white"    # hollow face: white on a light deck, transparent on dark
    if s == "actual":
        return dict(color=ink, edgecolor="none")
    if s == "prior":
        return dict(color=_PRIOR_GREY, edgecolor="none")
    if s == "plan":
        return dict(color=hollow, edgecolor=ink, linewidth=1.6)
    if s == "forecast":
        return dict(color=hollow, edgecolor=ink, linewidth=1.2, hatch="//")
    raise ValueError(f"unknown IBCS scenario {scenario!r} — use one of {IBCS_SCENARIOS}")


def _per_bar_scenarios(scenario, n, recipe):
    """Normalize ``scenario`` (None | str | sequence) to one entry per bar."""
    if isinstance(scenario, (list, tuple)):
        if len(scenario) != n:
            raise ValueError(f"{recipe}: a per-bar scenario list needs one entry per item "
                             f"({len(scenario)} given for {n} bars)")
        return list(scenario)
    return [scenario] * n


def donut_kpi(out, segments, center_value, center_label, *, palette=None, dark=None, font=None, figsize=(5.2, 4.0)):
    """Part-to-whole donut with a headline KPI in the hole. segments = [(label, value), ...]."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
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


def dumbbell(out, rows, *, palette=None, dark=None, font=None, highlight=None, a_label="before", b_label="after",
             favorable_color=None, unfavorable_color=None, figsize=(6.6, 4.0)):
    """Gap between two values per category. rows = [(label, value_a, value_b), ...].
    Variance semantics (IBCS): pass ``favorable_color``/``unfavorable_color`` to colour each row's
    connector + "after" dot by direction of change — favorable when value_b >= value_a (pass the
    colours swapped when *down* is good, e.g. cost). Passing either turns variance mode on (the
    other defaults to the standard green/red pair); both ``None`` (default) keeps the accent look."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D"]
    acc, acc2, neutral = pal[0], (pal[1] if len(pal) > 1 else pal[0]), "#9AA0AE"
    variance = favorable_color is not None or unfavorable_color is not None
    fav = favorable_color or "#1F9D55"; unf = unfavorable_color or "#D9463B"
    labels = [r[0] for r in rows]; A = [r[1] for r in rows]; B = [r[2] for r in rows]
    ys = list(range(len(rows)))[::-1]
    fig, ax = plt.subplots(figsize=figsize)
    for i, y in enumerate(ys):
        em = (highlight is None or i == highlight)
        if variance:   # "before" dot stays neutral (the reference); hue is paired with dot POSITION (left/right of
            #            the reference) per the never-hue-alone rule, and the end label restates the value
            vc = fav if B[i] >= A[i] else unf
            line_c, a_c, b_c, lbl_c = (vc if em else grid), neutral, (vc if em else neutral), vc
        else:
            line_c, a_c, b_c, lbl_c = (acc if em else grid), (acc2 if em else neutral), (acc if em else neutral), ink
        ax.plot([A[i], B[i]], [y, y], color=line_c, lw=3 if em else 2, zorder=1, solid_capstyle="round")
        ax.scatter([A[i]], [y], color=a_c, s=70, zorder=2)
        ax.scatter([B[i]], [y], color=b_c, s=70, zorder=2)
        if variance and B[i] < A[i]:   # declining row: label on the FREE side, not atop the reference dot
            ax.annotate(_numlabel(B[i]), (B[i], y), textcoords="offset points", xytext=(-8, 0),
                        ha="right", va="center", fontsize=9.5, color=lbl_c, fontweight="bold")
        else:
            ax.annotate(_numlabel(B[i]), (B[i], y), textcoords="offset points", xytext=(8, 0),
                        va="center", fontsize=9.5, color=lbl_c, fontweight="bold")
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=11, color=ink)
    ax.scatter([], [], color=(neutral if variance else acc2), s=70, label=a_label)
    ax.scatter([], [], color=(ink if variance else acc), s=70, label=b_label)
    ax.legend(loc="lower right", frameon=False, fontsize=10, labelcolor=ink)
    for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(muted); ax.tick_params(colors=muted)
    ax.xaxis.grid(True, color=grid, lw=0.7); ax.set_axisbelow(True)
    return _save(fig, out)


def distribution(out, groups, *, palette=None, dark=None, font=None, highlight=None,
                 kind="auto", err="sd", value_label="", show_n=True, jitter=True,
                 ref=None, ref_label="", figsize=(6.6, 4.0), seed=0):
    """SAMPLE DATA — the spread, not just the average. groups = [(label, [v, v, ...]), ...].

    Reach for this whenever a value is a **mean or median of measurements** (Dice per subject,
    latency per run, score per rater) rather than a count. A bar chart of such means is the single
    most-criticised figure in scientific publishing: the bar's weight implies the value fills the
    range from zero, hides n, hides the shape, and hides outliers -- Nature Methods, "Kick the bar
    chart habit" (2014) and PLOS Biology, "Beyond Bar and Line Graphs" (2015) both say to show the
    distribution instead. Counts still belong in a bar chart; sample measurements do not.

    `kind="auto"` applies that literature's own rule, so the choice is not left to memory:
      * min n >= 5  -> **box plot** (median, IQR box, Tukey 1.5xIQR whiskers, outliers as points)
      * 3 <= n < 5  -> **mean +/- error** (a box's quartiles are meaningless on four points)
      * n < 3       -> refuses. Two values have no distribution; show them with `deckkit.dot_strip`
                      or `deckkit.stat_row` and say n=2, rather than implying a shape.
    Force one with `kind="box"` / `"mean_error"`.

    `err` names the interval and is PRINTED on the figure ("sd" | "se" | "ci95"): an error bar whose
    measure is not stated cannot be read, and the same drawn height means three different things.
    `jitter=True` overlays EVERY observation, deterministically (`seed`), which is what makes n and
    any clustering visible; the caption line records the box/whisker definition for the same reason.
    `show_n` puts n under each group label. `ref`/`ref_label` draw a baseline (a prior SOTA, a
    clinical threshold). `highlight` = index of the one group in the accent, the rest neutral.
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    import numpy as np
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D"]
    neutral = "#9AA0AE"
    if not groups:
        raise ValueError("distribution(): no groups")
    labels, data = [], []
    for g in groups:
        lab, vals = g[0], [float(v) for v in g[1]]
        if not vals:
            raise ValueError(f"distribution(): group {lab!r} has no values")
        labels.append(lab)
        data.append(vals)
    nmin = min(len(v) for v in data)
    if kind == "auto":
        kind = "box" if nmin >= 5 else "mean_error"
    if kind == "mean_error" and nmin < 3:
        raise ValueError(
            f"distribution(): the smallest group has n={nmin}. Two values are not a distribution -- "
            f"an error bar or a box drawn over them asserts a spread the data cannot support. Show "
            f"the individual values (deckkit.dot_strip / stat_row) and state n instead.")
    if kind not in ("box", "mean_error"):
        raise ValueError(f"distribution(): kind={kind!r} is not 'auto' | 'box' | 'mean_error'")
    if err not in ("sd", "se", "ci95"):
        raise ValueError(f"distribution(): err={err!r} is not 'sd' | 'se' | 'ci95' -- the interval "
                         f"has to be named because the drawn height cannot say which it is")

    fig, ax = plt.subplots(figsize=figsize)
    xs = list(range(1, len(data) + 1))
    col = [(pal[0] if (highlight is None or i == highlight) else neutral) for i in range(len(data))]

    if kind == "box":
        bp = ax.boxplot(data, positions=xs, widths=0.52, whis=1.5, showfliers=not jitter,
                        patch_artist=True, medianprops=dict(color=ink, lw=1.6),
                        whiskerprops=dict(color=muted, lw=1.1),
                        capprops=dict(color=muted, lw=1.1),
                        flierprops=dict(marker="o", markersize=3.5, markerfacecolor=neutral,
                                        markeredgecolor="none"))
        for patch, c in zip(bp["boxes"], col):
            patch.set_facecolor(c)
            patch.set_alpha(0.22)
            patch.set_edgecolor(c)
            patch.set_linewidth(1.4)
        note = "box: median + IQR · whiskers 1.5×IQR"
        if jitter:
            note += " · every observation shown"
    else:
        rs = np.random.RandomState(seed)
        means = [float(np.mean(v)) for v in data]
        if err == "sd":
            bars = [float(np.std(v, ddof=1)) if len(v) > 1 else 0.0 for v in data]
            note = "error bars: ±1 SD"
        elif err == "se":
            bars = [float(np.std(v, ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0 for v in data]
            note = "error bars: ±1 SEM"
        else:
            from math import sqrt
            bars = []
            for v in data:
                if len(v) > 1:
                    se = float(np.std(v, ddof=1) / sqrt(len(v)))
                    bars.append(1.96 * se)      # normal approx; stated in the note, not implied
                else:
                    bars.append(0.0)
            note = "error bars: 95% CI (normal approx.)"
        for i, x in enumerate(xs):
            ax.errorbar([x], [means[i]], yerr=[bars[i]], fmt="o", ms=9, color=col[i],
                        ecolor=col[i], elinewidth=1.6, capsize=6, capthick=1.6, zorder=3)
        if jitter:
            note += " · every observation shown"

    if jitter:
        rs = np.random.RandomState(seed)
        # On a box, the cloud belongs INSIDE the box (that is what shows where the mass sits). On a
        # mean+/-error the summary is a single marker, so the cloud is offset beside it -- points
        # drawn through the error bar hide the very interval they are there to justify.
        off = 0.0 if kind == "box" else 0.19
        for i, x in enumerate(xs):
            xj = x + off + rs.uniform(-0.11, 0.11, size=len(data[i]))
            ax.scatter(xj, data[i], s=16, color=col[i], alpha=0.55, linewidths=0, zorder=4)

    if ref is not None:
        ax.axhline(ref, color=muted, lw=1.1, ls="--", zorder=1)
        if ref_label:
            # ABOVE its own line: sitting on it puts the dash through the glyphs, which is the
            # RULE THROUGH TEXT defect the deck lint fails a slide for.
            ax.annotate(ref_label, xy=(1.0, ref), xycoords=("axes fraction", "data"),
                        xytext=(-2, 3), textcoords="offset points", fontsize=9, color=muted,
                        ha="right", va="bottom", annotation_clip=False)

    ticks = [f"{lab}\nn={len(v)}" if show_n else lab for lab, v in zip(labels, data)]
    ax.set_xticks(xs)
    ax.set_xticklabels(ticks, fontsize=10.5, color=ink)
    ax.set_xlim(0.45, len(data) + 0.55)
    if value_label:
        ax.set_ylabel(value_label, fontsize=10.5, color=ink)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("bottom", "left"):
        ax.spines[sp].set_color(muted)
    ax.tick_params(colors=muted)
    ax.yaxis.grid(True, color=grid, lw=0.7)
    ax.set_axisbelow(True)
    # The definition line is not decoration: an unlabelled error bar or whisker is unreadable, and
    # a reader who cannot tell SD from SEM cannot judge the claim. Drawn, never left to a caption
    # someone may not write.
    ax.annotate(note, xy=(0.0, -0.16), xycoords="axes fraction", fontsize=8.5, color=muted,
                ha="left", va="top", annotation_clip=False)
    return _save(fig, out)


def marimekko(out, columns, categories, *, palette=None, dark=None, font=None, highlight=None,
              width_label="", gap=0.006, min_pct_label=6.0, show_width=True, figsize=(7.0, 4.2)):
    """TWO dimensions at once: column WIDTH = how big the segment is, HEIGHT = how it splits.

    `columns` = [(segment_label, size, [value_per_category, ...]), ...]; `categories` names the
    stack. Each column is normalised to 100% internally, so the values may be shares or raw counts.

    The form only works because **cell area = size x share = the absolute quantity**, which is the
    one thing a plain 100% stacked bar throws away: it shows every segment as equally important. So
    a mekko answers "who leads, and in a segment worth caring about" in one read -- the reason it is
    a strategy staple (market share by segment, share of wallet, portfolio mix).

    That also means the widths carry data and cannot be nudged for looks: they are laid out strictly
    proportional to `size`, and a non-positive size is refused rather than drawn thin. `gap` is a
    hairline separator taken out of each column's own width, not added between them, so the
    proportions survive it. `width_label` (e.g. "$B") annotates the size axis; `show_width` prints
    each segment's size under its label. `highlight` = index of the ONE category to keep in accent.
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D", "#D9463B", "#8A93A6"]
    neutral = "#C2C6D2"
    if not columns:
        raise ValueError("marimekko(): no columns")
    for lab, size, vals in columns:
        if size is None or size <= 0:
            raise ValueError(f"marimekko(): segment {lab!r} has size {size!r}; the column WIDTH "
                             f"encodes it, so a non-positive size has no width to draw")
        if len(vals) != len(categories):
            raise ValueError(f"marimekko(): segment {lab!r} has {len(vals)} values for "
                             f"{len(categories)} categories")
        if sum(vals) <= 0:
            raise ValueError(f"marimekko(): segment {lab!r} sums to {sum(vals)}; a column with no "
                             f"positive total cannot be split into shares")
        if any(v < 0 for v in vals):
            raise ValueError(f"marimekko(): segment {lab!r} has a negative value; a stacked share "
                             f"crosses zero and the height stops meaning the split")

    total = float(sum(c[1] for c in columns))
    fig, ax = plt.subplots(figsize=figsize)
    # A stacked form cannot take the roster's usual "grey out the rest": two categories flattened to
    # ONE grey give the legend two identical swatches and make their cells indistinguishable, which
    # destroys the mix the chart exists to show (native_chart documents the same trap for its stacked
    # kinds). So the de-emphasised categories keep a DISTINGUISHABLE neutral each -- still clearly
    # secondary to the accent, still readable against one another.
    _NEUTRAL_RAMP = ["#C9CDD6", "#A8AEBC", "#878FA1", "#6A7285", "#515869"]
    cols, k = [], 0
    for i in range(len(categories)):
        if highlight is None:
            cols.append(pal[i % len(pal)])
        elif i == highlight:
            cols.append(pal[0])
        else:
            cols.append(_NEUTRAL_RAMP[k % len(_NEUTRAL_RAMP)])
            k += 1
    x = 0.0
    for lab, size, vals in columns:
        w = size / total                                  # strictly proportional -- never tuned
        dw = max(w - gap, w * 0.55)                       # separator taken OUT of the column
        s = float(sum(vals))
        y = 0.0
        for ci, v in enumerate(vals):
            hh = v / s
            ax.add_patch(plt.Rectangle((x, y), dw, hh, facecolor=cols[ci], edgecolor="none"))
            if hh * 100 >= min_pct_label and dw > 0.05:
                em = highlight is None or ci == highlight
                # pick ink by the cell's own luminance, not by whether it is the accent: the
                # neutral ramp spans light to dark, so one fixed grey would fail at one end
                fc = cols[ci].lstrip("#")
                lum = (0.299 * int(fc[0:2], 16) + 0.587 * int(fc[2:4], 16)
                       + 0.114 * int(fc[4:6], 16)) / 255.0
                ax.text(x + dw / 2, y + hh / 2, f"{hh*100:.0f}%", ha="center", va="center",
                        fontsize=9, color=("#22262E" if lum > 0.62 else "white"),
                        fontweight="bold" if em else "normal")
            y += hh
        tick = f"{lab}\n{_numlabel(size)}{width_label}" if show_width else lab
        ax.text(x + dw / 2, -0.035, tick, ha="center", va="top", fontsize=10, color=ink)
        x += w
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0", "25", "50", "75", "100%"], fontsize=9.5, color=muted)
    ax.set_xticks([])
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(muted)
    ax.tick_params(colors=muted, length=0)
    for i, c in enumerate(categories):
        ax.add_patch(plt.Rectangle((0, 0), 0, 0, facecolor=cols[i], label=c))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=min(len(categories), 5),
              frameon=False, fontsize=10, labelcolor=ink, handlelength=1.0, handleheight=1.0)
    ax.annotate(f"column width = segment size{(' (' + width_label.strip() + ')') if width_label else ''}"
                f" · height = share within the segment",
                xy=(0.0, -0.155), xycoords="axes fraction", fontsize=8.5, color=muted,
                ha="left", va="top", annotation_clip=False)
    return _save(fig, out)


def radar(out, axes_labels, series, *, palette=None, dark=None, font=None, highlight=None,
          axis_range=None, value_fmt="{:g}", fill_alpha=0.13, figsize=(5.0, 4.6)):
    """A MULTIVARIATE PROFILE across 3-8 axes -- the SHAPE of a trade-off, for <=3 things.

    `axes_labels` names the spokes; `series` = [(name, [v per axis]), ...].

    Radar is the one form in this roster that misleads by construction, so the limits are enforced
    rather than advised:
      * **<=3 series.** Four overlaid polygons cannot be read apart, whatever the palette does.
      * **3-8 axes.** Two is a scatter; nine is a table.
      * **every spoke is anchored at zero** by default (`axis_range=(lo, hi)` shared, or a list of
        per-axis pairs). Per-axis min-max stretching is the usual radar cheat: it re-scales each
        spoke to the observed range and turns a 2% gap into half the radius.
    Note also that a polygon's AREA grows as the square of its values, so radar always overstates a
    lead -- and the spoke ORDER changes the shape while the data stays identical. Both are inherent;
    they are why this returns a profile-comparison picture and never a magnitude claim.

    **Prefer something else when you can:** for "which method wins on each metric", `small_multiples`
    or a per-metric `dot_strip`/`dumbbell` is read faster and cannot distort; for 4+ methods, they
    are the only honest option. Reach for radar when the SHAPE of a profile -- balanced vs spiky --
    is itself the message.
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    import numpy as np
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0", "#00A6A6", "#F2A03D"]
    neutral = "#9AA0AE"
    n = len(axes_labels)
    if not (3 <= n <= 8):
        raise ValueError(f"radar(): {n} axes. Below 3 there is no polygon (use a bar or a scatter); "
                         f"above 8 the spokes crowd and the labels collide -- use small_multiples or "
                         f"a per-metric dot_strip, which stay readable at any width")
    if not series:
        raise ValueError("radar(): no series")
    if len(series) > 3:
        raise ValueError(f"radar(): {len(series)} series. Four or more overlaid polygons cannot be "
                         f"told apart -- use small_multiples (one panel per series, shared axis) or "
                         f"a per-metric dumbbell/dot_strip instead")
    for nm, vals in series:
        if len(vals) != n:
            raise ValueError(f"radar(): series {nm!r} has {len(vals)} values for {n} axes")

    if axis_range is None:
        hi = [max(max(s[1][i] for s in series), 0.0) for i in range(n)]
        rng = [(0.0, (h if h > 0 else 1.0)) for h in hi]
        note = "each spoke: 0 to its own max"
    elif isinstance(axis_range[0], (list, tuple)):
        if len(axis_range) != n:
            raise ValueError(f"radar(): axis_range has {len(axis_range)} pairs for {n} axes")
        rng = [(float(a), float(b)) for a, b in axis_range]
        note = "per-axis ranges as given"
    else:
        rng = [(float(axis_range[0]), float(axis_range[1]))] * n
        note = f"all spokes: {value_fmt.format(rng[0][0])} to {value_fmt.format(rng[0][1])}"
    for i, (lo, hi_) in enumerate(rng):
        if hi_ <= lo:
            raise ValueError(f"radar(): axis {axes_labels[i]!r} has range ({lo}, {hi_})")
    # A polar axis does not clip out-of-range values, it MIRRORS them: r < 0 lands the point on the
    # opposite spoke, and r > 1 walks outside the ring. Either way the drawn shape stops matching
    # the data while looking perfectly plausible -- the exact failure this whole roster refuses.
    for nm, vals in series:
        for i, v in enumerate(vals):
            lo, hi_ = rng[i]
            if not (lo <= float(v) <= hi_):
                raise ValueError(
                    f"radar(): {nm!r} has {v} on axis {axes_labels[i]!r}, outside the declared "
                    f"range ({lo:g}, {hi_:g}). A polar plot mirrors a negative radius onto the "
                    f"opposite spoke and runs a too-large one off the ring, so this would draw a "
                    f"shape that is not the data. Widen axis_range, or drop the axis.")

    ang = [2 * np.pi * i / n for i in range(n)]
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    for si, (nm, vals) in enumerate(series):
        em = highlight is None or si == highlight
        c = pal[si % len(pal)] if em else neutral
        r = [(float(v) - rng[i][0]) / (rng[i][1] - rng[i][0]) for i, v in enumerate(vals)]
        ax.plot(ang + [ang[0]], r + [r[0]], color=c, lw=2.4 if em else 1.5,
                zorder=3 if em else 2, label=nm)
        ax.fill(ang + [ang[0]], r + [r[0]], color=c, alpha=fill_alpha if em else 0.06, zorder=1)
        ax.scatter(ang, r, color=c, s=26 if em else 16, zorder=4)
    ax.set_xticks(ang)
    ax.set_xticklabels(axes_labels, fontsize=10, color=ink)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels([])                      # the rings are a grid, not a second value claim
    ax.set_ylim(0, 1.06)
    ax.grid(color=grid, lw=0.8)
    ax.spines["polar"].set_color(grid)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=min(len(series), 3),
              frameon=False, fontsize=10, labelcolor=ink)
    ax.annotate(note, xy=(0.5, -0.17), xycoords="axes fraction", fontsize=8.5, color=muted,
                ha="center", va="top", annotation_clip=False)
    return _save(fig, out)


def slope(out, series, *, palette=None, dark=None, font=None, highlight=None, t0="", t1="", figsize=(5.4, 4.2)):
    """Rank/level change between TWO points in time. series = [(label, start, end), ...]."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
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


def dual_axis(out, x, left, right, *, left_label="", right_label="", palette=None, dark=None, font=None,
              left_fmt="{:g}", right_fmt="{:g}", figsize=(6.8, 4.0)):
    """Two trends on different scales — the classic 'A rises while B falls' tradeoff."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
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


def bubble_trend(out, points, *, palette=None, dark=None, font=None, trend=True, xlabel="", ylabel="", figsize=(6.6, 4.2)):
    """x vs y with a size dimension + an optional fair-value trend line. points = [(x,y,size,label)]."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
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


def pareto(out, items, *, palette=None, dark=None, font=None, figsize=(6.8, 4.0), scenario=None):
    """Ranked bars + cumulative % line — the 'vital few' that drive the total. items=[(label,value)].
    ``scenario`` (IBCS): "actual"/"prior"/"plan"/"forecast" for the whole chart, or a per-item
    sequence (kept aligned through the ranking sort) — bars then take the scenario fill (solid
    ink / light grey / hollow / hatched) instead of the accent. ``None`` = the accent as before."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#5B4BE0"]; acc = pal[0]
    scen = _per_bar_scenarios(scenario, len(items), "pareto")
    ranked = sorted(zip(items, scen), key=lambda t: t[0][1], reverse=True)
    items = [t[0] for t in ranked]; scen = [t[1] for t in ranked]
    labels = [i[0] for i in items]; vals = [i[1] for i in items]
    tot = sum(vals) or 1; cum = []; run = 0
    for v in vals:
        run += v; cum.append(100 * run / tot)
    xs = list(range(len(vals)))
    fig, ax = plt.subplots(figsize=figsize); ax2 = ax.twinx()
    if scenario is None:
        ax.bar(xs, vals, color=acc, width=0.62)
    else:
        for i in xs:
            ax.bar(i, vals[i], width=0.62, **_scenario_fill(scen[i], ink, dark))
    ax2.plot(xs, cum, color=muted, lw=2, marker="o", ms=5)
    ax2.set_ylim(0, 105)
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=10, color=ink, rotation=0)
    ax.tick_params(axis="y", colors=muted); ax2.tick_params(axis="y", colors=muted)
    for sp in ("top",): ax.spines[sp].set_visible(False); ax2.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(muted)
    return _save(fig, out)


def waterfall(out, items, *, palette=None, dark=None, font=None, total_label="Total", figsize=(6.8, 4.0),
              scenario=None, favorable_color="#1F9D55", unfavorable_color="#D9463B"):
    """Running total built from signed steps — the 'how did we get from A to B' bridge that
    python-pptx has NO native form for. ``items = [(label, delta), ...]`` where a ``delta`` of ``None``
    marks a SUBTOTAL/TOTAL bar (drawn from zero to the running cumulative). Each step bar FLOATS on the
    cumulative so far; rises, falls and totals are coloured DISTINCTLY (green ↑ / red ↓ / navy total —
    the documented categorical exception to one-accent), consecutive bars are joined by dashed connector
    steps, and every bar carries a direct value label. ``total_label`` names a total bar whose label is
    left blank. Transparent PNG saved to ``out``.
    ``favorable_color``/``unfavorable_color`` rename the ↑/↓ variance pair (defaults green/red — pass
    them swapped when a rise is BAD, e.g. a cost bridge); the +/− on every label keeps the sign
    readable without the hue. ``scenario`` (IBCS): "actual"/"prior"/"plan"/"forecast" for the whole
    chart, or a per-item sequence (e.g. a bridge whose last steps are forecast) — the treatment keeps
    each bar's semantic colour as its ink, so an FC variance bar renders as a green/red ``//`` hatch."""
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    if not items:
        raise ValueError("waterfall needs at least one item")
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#33415C", "#00A6A6", "#F2A03D"]
    up_c, down_c, total_c = favorable_color, unfavorable_color, pal[0]
    n = len(items)
    scen = _per_bar_scenarios(scenario, n, "waterfall")
    running = 0.0
    bases, heights, colors, is_total, deltas, cum_after, labels = [], [], [], [], [], [], []
    for (label, delta) in items:
        if delta is None:
            base, height, color, tot, val = 0.0, running, total_c, True, running
            labels.append(label if label else total_label)
        else:
            tot = False
            if delta >= 0:
                base, height, color = running, delta, up_c
            else:
                base, height, color = running + delta, -delta, down_c
            running += delta
            val = delta
            labels.append(label)
        bases.append(base); heights.append(height); colors.append(color)
        is_total.append(tot); deltas.append(val); cum_after.append(running)
    xs = list(range(n)); bw = 0.62
    tops = [bases[i] + heights[i] for i in xs]
    allmax, allmin = max(tops + bases), min(bases + tops)
    span = (allmax - allmin) or 1.0
    lblpad = 0.03 * span
    fig, ax = plt.subplots(figsize=figsize)
    for i in xs:
        ax.bar(i, heights[i], bottom=bases[i], width=bw, zorder=3, **_scenario_fill(scen[i], colors[i], dark))
    for i in range(n - 1):                              # dashed connector at the level between bars
        ax.plot([i + bw / 2, i + 1 - bw / 2], [cum_after[i], cum_after[i]],
                color=muted, lw=1.0, ls="--", zorder=2)
    for i in xs:
        if is_total[i]:
            ax.text(i, tops[i] + lblpad, _numlabel(deltas[i]), ha="center", va="bottom",
                    fontsize=10, color=ink, fontweight="bold")
        elif deltas[i] >= 0:
            ax.text(i, tops[i] + lblpad, "+" + _numlabel(deltas[i]), ha="center", va="bottom",
                    fontsize=9.5, color=up_c, fontweight="bold")
        else:
            ax.text(i, bases[i] - lblpad, "-" + _numlabel(abs(deltas[i])), ha="center", va="top",
                    fontsize=9.5, color=down_c, fontweight="bold")  # ASCII '-' (U+2212 tofus in CJK fonts;
            #                                          matches axes.unicode_minus=False on the tick labels)
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=10, color=ink)
    ax.set_ylim(min(0.0, allmin) - lblpad * 2, allmax + lblpad * 4)
    ax.axhline(0, color=grid, lw=1.0, zorder=1)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(muted); ax.tick_params(axis="x", colors=muted); ax.set_yticks([])
    return _save(fig, out)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# CLINICAL / EVIDENCE-SYNTHESIS forms.
#
# 🔴 WHY THESE EXIST. `design-by-topic.md` lists "Medicine / biotech / clinical" as a first-class
# domain and tells you which PRESET to dress it in — but every domain row in that table is an
# aesthetic row, and none of them changes the FORM vocabulary. Measured by grep across
# references/ + scripts/ + agents/ before this block: zero hits for kaplan-meier, forest plot,
# CONSORT, PRISMA, Bland-Altman, ROC. The recipes above are a BUSINESS-ANALYTICS vocabulary
# (waterfall, marimekko, pareto, radar) and `schematic-diagrams.md` is an UNDERGRADUATE-PHYSICS
# one (free-body, optics, circuits). So the skill knew how to STYLE a clinical deck and could not
# DRAW one, and the author's only option was a hand-rolled scatter — which is where the geometry
# rules below get broken silently.
#
# Each of these owns a rule that is wrong-by-default when hand-rolled:
#   forest_plot   ratios live on a LOG axis, or a CI that is symmetric in ratio terms is drawn
#                 lopsided and the eye reads a bias that is not in the data
#   km_curve      survival is a STEP function; drawing it as a line interpolates events that did
#                 not happen between observations
#   bland_altman  agreement is bias ± 1.96·SD of the DIFFERENCES — not a correlation, and not a
#                 regression of one method on the other
#   roc_curve     the chance diagonal and a square aspect are what make an AUC readable at a
#                 glance; stretched axes flatter every classifier
# ─────────────────────────────────────────────────────────────────────────────────────────────


def _as_floats(seq, what):
    try:
        return [float(v) for v in seq]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{what} must be a sequence of numbers — {exc}") from exc


def forest_plot(out, rows, *, null=1.0, log=None, summary=None, xlabel=None, xlim=None,
                palette=None, dark=None, font=None, figsize=(7.2, None),
                value_fmt="{:.2f}"):
    """A FOREST PLOT — one effect estimate with its confidence interval per row, on a shared axis
    against a null reference line. The general form for "the same comparison, measured several
    times": meta-analysis, subgroup effects, regression coefficients, A/B lifts per segment.

    ``rows = [(label, estimate, lo, hi[, weight]), ...]``. ``weight`` (optional) sizes the marker
    by AREA — the convention that makes a precise study visibly dominate an imprecise one.
    ``summary=(label, est, lo, hi)`` draws the pooled estimate as a DIAMOND, the shape that says
    "this is not another study".

    🔴 ``log`` defaults to ``null == 1``. A ratio (OR/RR/HR) is symmetric in LOG space — 0.5 and 2
    are the same effect in opposite directions — so on a linear axis the left CI is squashed and
    the right stretched, and the eye reads an asymmetry that is not in the data. Pass
    ``log=False`` deliberately for a difference scale (``null=0``). Non-positive bounds on a log
    axis RAISE rather than silently disappearing.
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    if not rows:
        raise ValueError("forest_plot needs at least one row")
    if log is None:
        log = abs(float(null) - 1.0) < 1e-9
    parsed = []
    for r in rows:
        if len(r) < 4:
            raise ValueError("each forest row is (label, estimate, lo, hi[, weight]); got %r" % (r,))
        label, est, lo, hi = r[0], float(r[1]), float(r[2]), float(r[3])
        wt = float(r[4]) if len(r) > 4 and r[4] is not None else None
        if not (lo <= est <= hi):
            raise ValueError(
                f"forest_plot: row {label!r} has estimate {est:g} outside its interval "
                f"[{lo:g}, {hi:g}] — a point estimate sits INSIDE its own CI, so one of the three "
                f"numbers is wrong or the columns are swapped")
        if log and min(lo, est, hi) <= 0:
            raise ValueError(
                f"forest_plot: row {label!r} has a non-positive bound on a LOG axis "
                f"({lo:g}, {est:g}, {hi:g}). Ratios cannot be <=0; if these are DIFFERENCES pass "
                f"null=0 (log defaults to False there).")
        parsed.append((str(label), est, lo, hi, wt))

    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#33415C", "#00A6A6", "#D9463B"]
    n = len(parsed) + (1 if summary else 0)
    fw, fh = figsize
    fig, ax = plt.subplots(figsize=(fw, fh if fh else max(2.0, 0.42 * n + 1.1)))

    ys = list(range(len(parsed)))[::-1]                      # first row at the TOP, as read
    wts = [w for (_l, _e, _lo, _hi, w) in parsed if w is not None]
    wmax = max(wts) if wts else None
    for y, (label, est, lo, hi, wt) in zip(ys, parsed):
        ax.plot([lo, hi], [y, y], color=ink, lw=1.3, solid_capstyle="butt", zorder=2)
        for b in (lo, hi):                                   # CI caps — the ends must be findable
            ax.plot([b, b], [y - 0.12, y + 0.12], color=ink, lw=1.3, zorder=2)
        size = 46.0 if wmax is None else 22.0 + 90.0 * (wt / wmax)   # AREA ∝ weight
        ax.scatter([est], [y], s=size, color=pal[0], zorder=3, marker="s")

    if summary:
        slabel, sest, slo, shi = summary[0], float(summary[1]), float(summary[2]), float(summary[3])
        if not (slo <= sest <= shi):
            raise ValueError("forest_plot: the summary estimate sits outside its own interval")
        y = -1
        ax.fill([slo, sest, shi, sest], [y, y + 0.22, y, y - 0.22],
                color=pal[1], zorder=3, lw=0)
        ys = ys + [y]
        parsed = parsed + [(str(slabel), sest, slo, shi, None)]

    ax.axvline(float(null), color=muted, lw=1.1, ls="--", zorder=1)
    if log:
        ax.set_xscale("log")
        # 🔴 PLAIN numbers, never scientific notation. matplotlib's default log formatter renders
        # 0.4 as "4x10^-1" and the null as "10^0"; a reader looking for the line at ONE has to
        # decode an exponent to find it. Ratios in this range are read as 0.5 / 1 / 2, so the
        # ticks are chosen from a human ladder and formatted literally.
        from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
        _lo = min(p[2] for p in parsed)
        _hi = max(p[3] for p in parsed)
        if summary:
            _lo, _hi = min(_lo, float(summary[2])), max(_hi, float(summary[3]))
        LADDER = [0.05, 0.1, 0.2, 0.25, 0.33, 0.5, 0.67, 0.8, 1, 1.25, 1.5, 2, 3, 4, 5, 10, 20]
        ticks = [t for t in LADDER if _lo * 0.92 <= t <= _hi * 1.08]
        if float(null) not in ticks and _lo * 0.92 <= float(null) <= _hi * 1.08:
            ticks = sorted(ticks + [float(null)])
        if len(ticks) >= 2:
            ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.xaxis.set_major_formatter(FuncFormatter(
            lambda v, _p: ("%g" % v) if v >= 0.01 else ("%.3f" % v)))
    if xlim:
        ax.set_xlim(*xlim)
    ax.set_yticks(ys)
    ax.set_yticklabels([p[0] for p in parsed], fontsize=9.5, color=ink)
    ax.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(grid)
    ax.tick_params(axis="x", colors=muted, labelsize=9)
    ax.tick_params(axis="y", length=0)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9.5, color=muted)

    # the numeric column — a forest plot is READ as numbers as often as it is scanned as a picture
    xr = ax.get_xlim()
    tx = xr[1] * (1.06 if log else 1.0) if log else xr[1] + 0.04 * (xr[1] - xr[0])
    for y, (label, est, lo, hi, _w) in zip(ys, parsed):
        txt = f"{value_fmt.format(est)} ({value_fmt.format(lo)}–{value_fmt.format(hi)})"
        ax.text(tx, y, txt, fontsize=9, color=ink, va="center", ha="left", clip_on=False)
    return _save(fig, out)


def _km_steps(times, events):
    """The Kaplan–Meier estimate as plottable steps: (ts, sv, censor_marks).

    S(t) = prod over event times t_i <= t of (1 - d_i / n_i), starting from (0, 1).

    🔴 The step runs to the LAST OBSERVATION, not the last event. Stopping at the last event — what
    this did — ended every curve whose final subject was censored in a bare vertical drop, left that
    subject's censor mark floating over empty axes, clipped the x-range at the last EVENT so the
    longest follow-up was cut off the plot, and drew NOTHING for a group with no events at all
    (one (0, 1) point is not a line) — the arm a small trial most wants to show. Found by LOOKING at
    the scaffold's render; the suite's ladder test re-implemented the estimator and compared that.
    """
    obs = sorted(zip(times, events))
    ts, sv, s, at_risk, cens, i = [0.0], [1.0], 1.0, len(obs), [], 0
    while i < len(obs):
        t = obs[i][0]
        d = sum(1 for (tt, ee) in obs[i:] if abs(tt - t) < 1e-12 and ee == 1)
        c = sum(1 for (tt, ee) in obs[i:] if abs(tt - t) < 1e-12 and ee == 0)
        if d:
            s *= (1.0 - d / at_risk)
            ts.append(t); sv.append(s)
        if c:
            cens.append((t, s))
        at_risk -= (d + c)
        i += d + c
    if obs and obs[-1][0] > ts[-1] + 1e-12:
        ts.append(obs[-1][0]); sv.append(s)       # carry the estimate to the last follow-up
    return ts, sv, cens


def km_curve(out, groups, *, xlabel="Time", ylabel="Survival probability", risk_table=True,
             palette=None, dark=None, font=None, figsize=(6.8, 4.4), censor_marks=True,
             percent=False, xlim=None):
    """A KAPLAN–MEIER survival curve — the step-down estimator, computed here from RAW data so the
    caller never has to hand-roll it.

    ``groups = [(label, times, events), ...]`` where ``events`` is 1 for an event and 0 for a
    censored observation, aligned with ``times``. (A precomputed curve is also accepted:
    ``(label, times, surv, "precomputed")``.)

    🔴 Survival is a STEP function, drawn ``steps-post``: the estimate only changes AT an observed
    event, and a straight line between two observations asserts deaths on days nobody was seen.
    Censored observations get a tick, which is what separates "we stopped watching" from "nothing
    happened", and the NUMBERS AT RISK table under the axis is the part reviewers ask for first —
    a curve whose right tail rests on two patients looks identical to one resting on two hundred.
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    if not groups:
        raise ValueError("km_curve needs at least one group")
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#33415C", "#00A6A6", "#D9463B", "#F2A03D", "#5B4BE0"]

    curves = []
    for gi, g in enumerate(groups):
        label = str(g[0])
        if len(g) > 3 and g[3] == "precomputed":
            ts, sv = _as_floats(g[1], "times"), _as_floats(g[2], "survival")
            if len(ts) != len(sv):
                raise ValueError(f"km_curve: {label!r} has {len(ts)} times and {len(sv)} survival "
                                 f"values — they must be aligned")
            if any(b > a + 1e-9 for a, b in zip(sv, sv[1:])):
                raise ValueError(f"km_curve: {label!r} has survival that INCREASES; a "
                                 f"Kaplan–Meier estimate is non-increasing by construction")
            if any(v < -1e-9 or v > 1 + 1e-9 for v in sv):
                raise ValueError(f"km_curve: {label!r} has survival outside [0, 1]")
            cens, n0 = [], None
            obs = list(zip(ts, [1] * len(ts)))
        else:
            ts, ev = _as_floats(g[1], "times"), [int(e) for e in g[2]]
            if len(ts) != len(ev):
                raise ValueError(f"km_curve: {label!r} has {len(ts)} times and {len(ev)} event "
                                 f"flags — they must be aligned")
            if not ts:
                raise ValueError(f"km_curve: {label!r} has no observations")
            if any(e not in (0, 1) for e in ev):
                raise ValueError(f"km_curve: {label!r} has an event flag that is not 0 or 1 — "
                                 f"1 means the event happened, 0 means censored")
            obs = sorted(zip(ts, ev))
            n0 = len(obs)
            ts, sv, cens = _km_steps(ts, ev)
        curves.append((label, ts, sv, cens, n0, obs))

    if risk_table:
        fig, (ax, axr) = plt.subplots(
            2, 1, figsize=figsize, sharex=True,
            gridspec_kw={"height_ratios": [1.0, 0.10 + 0.075 * len(curves)], "hspace": 0.12})
    else:
        fig, ax = plt.subplots(figsize=figsize)
        axr = None

    scale = 100.0 if percent else 1.0
    tmax = max(max(c[1]) for c in curves) or 1.0
    for gi, (label, ts, sv, cens, n0, obs) in enumerate(curves):
        col = pal[gi % len(pal)]
        ax.step(ts, [v * scale for v in sv], where="post", color=col, lw=1.9, label=label, zorder=3)
        if censor_marks and cens:
            ax.plot([t for t, _s in cens], [s * scale for _t, s in cens], linestyle="none",
                    marker="|", markersize=7, markeredgewidth=1.4, color=col, zorder=4)
    ax.set_ylim(0, 1.02 * scale)
    ax.set_xlim(*(xlim if xlim else (0, tmax * 1.02)))
    ax.set_ylabel(ylabel + (" (%)" if percent else ""), fontsize=10, color=ink)
    ax.grid(axis="y", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(grid)
    ax.tick_params(colors=muted, labelsize=9)
    if len(curves) > 1:
        leg = ax.legend(frameon=False, fontsize=9.5, loc="lower left")
        for t in leg.get_texts():
            t.set_color(ink)

    if axr is not None:
        ticks = ax.get_xticks()
        ticks = [t for t in ticks if ax.get_xlim()[0] <= t <= ax.get_xlim()[1]]
        axr.set_xlim(*ax.get_xlim())
        axr.set_ylim(-0.5, len(curves) - 0.5)
        axr.invert_yaxis()
        _widest = 1
        for (_l, _t, _s, _c, _n0, _obs) in curves:
            for t in ticks:
                if _n0 is not None:
                    _widest = max(_widest, len(str(sum(1 for (tt, _e) in _obs if tt >= t - 1e-12))))
        _lab_gap = 0.012 + 0.011 * _widest        # half the widest number, plus a real gap
        for gi, (label, ts, sv, cens, n0, obs) in enumerate(curves):
            for t in ticks:
                n_at = (sum(1 for (tt, _e) in obs if tt >= t - 1e-12)
                        if n0 is not None else None)
                axr.text(t, gi, "—" if n_at is None else str(n_at), ha="center", va="center",
                         fontsize=8.5, color=ink)
            # 🔴 The row label lives in the FIGURE's left margin, not just left of the axes. At a
            # small negative offset it lands on top of the first tick's number, because the first
            # tick of a survival curve sits at x=0 on the spine itself — rendered as "Control20".
            # The margin is reserved below from the longest label, so the column cannot collide.
            # The first tick sits ON the spine at x=0 and its number is CENTRED there, so it
            # extends LEFT of the axes by half its own width — "Surgery alone" + "10" rendered
            # joined at a small offset. Clear the widest number, not a guessed gap.
            axr.text(-_lab_gap, gi, label, ha="right", va="center", fontsize=8.5, color=muted,
                     transform=axr.get_yaxis_transform(), clip_on=False)
        axr.set_yticks([]); axr.set_xticks(ticks)
        axr.tick_params(axis="x", colors=muted, labelsize=9, length=0)
        for side in ("top", "right", "left"):
            axr.spines[side].set_visible(False)
        axr.spines["bottom"].set_visible(False)
        axr.set_title("Number at risk", fontsize=8.5, color=muted, loc="left", pad=4)
        axr.set_xlabel(xlabel, fontsize=10, color=ink)
        # reserve the label column from the longest label actually present, so the numbers start
        # clear of it on any group naming — a fixed margin is wrong the moment a label is long
        _lab_chars = max((len(str(c[0])) for c in curves), default=0)
        fig.subplots_adjust(left=min(0.40, 0.10 + 0.0135 * _lab_chars + _lab_gap))
    else:
        ax.set_xlabel(xlabel, fontsize=10, color=ink)
    return _save(fig, out)


def bland_altman(out, method_a, method_b, *, names=("A", "B"), xlabel=None, ylabel=None,
                 palette=None, dark=None, font=None, figsize=(6.4, 4.2), percent=False):
    """A BLAND–ALTMAN agreement plot — the difference between two measurement methods against
    their mean, with the bias and the 95% limits of agreement drawn and LABELLED.

    🔴 This is the right form for "do these two methods agree?", and a correlation or a regression
    of one on the other is the classic wrong answer: two methods can correlate almost perfectly
    and still disagree by a clinically fatal constant. The limits are ``bias ± 1.96·SD of the
    DIFFERENCES`` — they describe where 95% of individual disagreements fall, which is the number
    a reader has to judge against what the application can tolerate.

    ``percent=True`` plots the difference as a percentage of the mean — the right choice when the
    disagreement grows with magnitude (a funnel in the raw plot is the tell).
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    a, b = _as_floats(method_a, "method_a"), _as_floats(method_b, "method_b")
    if len(a) != len(b):
        raise ValueError(f"bland_altman: {len(a)} values for {names[0]!r} and {len(b)} for "
                         f"{names[1]!r} — an agreement plot pairs each subject with itself, so "
                         f"the two sequences must be the same length and in the same order")
    if len(a) < 3:
        raise ValueError("bland_altman needs at least 3 paired observations to estimate an SD")
    import math
    means = [(x + y) / 2.0 for x, y in zip(a, b)]
    if percent and any(abs(m) < 1e-12 for m in means):
        raise ValueError("bland_altman(percent=True) divides by the pair mean, and one pair means "
                         "zero — use the absolute scale for data that crosses zero")
    diffs = ([(x - y) / m * 100.0 for x, y, m in zip(a, b, means)] if percent
             else [x - y for x, y in zip(a, b)])
    n = len(diffs)
    bias = sum(diffs) / n
    sd = math.sqrt(sum((d - bias) ** 2 for d in diffs) / (n - 1))
    lo, hi = bias - 1.96 * sd, bias + 1.96 * sd

    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#33415C", "#D9463B", "#00A6A6"]
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(means, diffs, s=28, color=pal[0], alpha=0.75, zorder=3, edgecolors="none")
    span = (max(means) - min(means)) or 1.0
    xr = (min(means) - 0.06 * span, max(means) + 0.18 * span)
    for val, col, style, name in ((bias, pal[1], "-", "bias"),
                                  (hi, pal[2], "--", "+1.96 SD"),
                                  (lo, pal[2], "--", "−1.96 SD")):
        ax.axhline(val, color=col, lw=1.3, ls=style, zorder=2)
        ax.text(xr[1], val, f"  {name} {val:+.3g}", fontsize=8.5, color=col,
                va="center", ha="left", clip_on=False)
    ax.set_xlim(*xr)
    ax.set_xlabel(xlabel or f"Mean of {names[0]} and {names[1]}", fontsize=10, color=ink)
    ax.set_ylabel(ylabel or (f"Difference ({names[0]} − {names[1]})"
                             + (" %" if percent else "")), fontsize=10, color=ink)
    ax.grid(axis="y", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(grid)
    ax.tick_params(colors=muted, labelsize=9)
    if n < 10:
        # not fatal — small agreement studies are real — but the limits are wide and unstable,
        # and a reader cannot see n from the picture.
        ax.set_title(f"n = {n} — limits of agreement are unstable at this sample size",
                     fontsize=8.5, color=muted, loc="left", pad=6)
    return _save(fig, out)


def roc_curve(out, curves, *, palette=None, dark=None, font=None, figsize=(4.8, 4.8),
              chance_line=True, xlabel="False positive rate", ylabel="True positive rate"):
    """An ROC CURVE — one or more classifiers against the chance diagonal, on a SQUARE canvas.

    ``curves = [(label, y_true, y_score), ...]`` with ``y_true`` in {0, 1} — the ROC and its AUC
    are computed here. A precomputed curve is also accepted as
    ``(label, fpr, tpr, "precomputed"[, auc])``.

    🔴 The square aspect and the chance diagonal are the form, not decoration: on a stretched axis
    every classifier looks better than it is, and without the diagonal there is no visual anchor
    for "no better than guessing". AUC is printed in the legend because the curve alone does not
    let a reader rank two models that cross.
    """
    palette, dark, font = _theme(palette, dark, font)   # the active visual language, unless passed
    if not curves:
        raise ValueError("roc_curve needs at least one curve")
    plt, ink, grid, muted = _mpl(dark, font)
    pal = list(palette) if palette else ["#33415C", "#00A6A6", "#D9463B", "#F2A03D", "#5B4BE0"]
    fig, ax = plt.subplots(figsize=figsize)

    for ci, c in enumerate(curves):
        label = str(c[0])
        if len(c) > 3 and c[3] == "precomputed":
            fpr, tpr = _as_floats(c[1], "fpr"), _as_floats(c[2], "tpr")
            if len(fpr) != len(tpr):
                raise ValueError(f"roc_curve: {label!r} has {len(fpr)} fpr and {len(tpr)} tpr "
                                 f"points — they must be aligned")
            if any(v < -1e-9 or v > 1 + 1e-9 for v in fpr + tpr):
                raise ValueError(f"roc_curve: {label!r} has a rate outside [0, 1]")
            auc = float(c[4]) if len(c) > 4 and c[4] is not None else None
        else:
            y_true = [int(v) for v in c[1]]
            y_score = _as_floats(c[2], "y_score")
            if len(y_true) != len(y_score):
                raise ValueError(f"roc_curve: {label!r} has {len(y_true)} labels and "
                                 f"{len(y_score)} scores — they must be aligned")
            if any(v not in (0, 1) for v in y_true):
                raise ValueError(f"roc_curve: {label!r} has a label that is not 0 or 1 — ROC is "
                                 f"defined for a BINARY outcome")
            P, N = sum(y_true), len(y_true) - sum(y_true)
            if not P or not N:
                raise ValueError(f"roc_curve: {label!r} has only one class present (P={P}, N={N}) "
                                 f"— an ROC curve is undefined without both")
            order = sorted(range(len(y_score)), key=lambda i: -y_score[i])
            tp = fp = 0
            fpr, tpr = [0.0], [0.0]
            prev = None
            for i in order:
                if prev is not None and y_score[i] != prev:
                    fpr.append(fp / N); tpr.append(tp / P)
                if y_true[i] == 1:
                    tp += 1
                else:
                    fp += 1
                prev = y_score[i]
            fpr.append(fp / N); tpr.append(tp / P)
            auc = 0.0
            for (x0, y0), (x1, y1) in zip(zip(fpr, tpr), zip(fpr[1:], tpr[1:])):
                auc += (x1 - x0) * (y0 + y1) / 2.0
        name = label if auc is None else f"{label}  (AUC {auc:.3f})"
        ax.step(fpr, tpr, where="post", color=pal[ci % len(pal)], lw=1.9, label=name, zorder=3)

    if chance_line:
        ax.plot([0, 1], [0, 1], color=muted, lw=1.1, ls="--", zorder=1)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_aspect("equal", adjustable="box")          # a stretched ROC flatters every model
    ax.set_xlabel(xlabel, fontsize=10, color=ink)
    ax.set_ylabel(ylabel, fontsize=10, color=ink)
    ax.grid(color=grid, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(grid)
    ax.tick_params(colors=muted, labelsize=9)
    leg = ax.legend(frameon=False, fontsize=9, loc="lower right")
    for t in leg.get_texts():
        t.set_color(ink)
    return _save(fig, out)
