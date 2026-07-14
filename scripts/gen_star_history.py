#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the README star-history chart (classic star-history.com look, self-hosted).

Fetches every stargazer's `starred_at` via the GitHub API and plots cumulative stars
over time as light + dark PNGs under docs/assets/. Run by .github/workflows/star-history.yml
on a daily schedule so the chart stays current without any third-party image service.
"""
import os, json, urllib.request, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

REPO = os.environ.get("STAR_REPO", "addsumtech/slides_maker")
LABEL = os.environ.get("STAR_LABEL", "addsumtech/slide-maker")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "assets")
RED = "#E1416B"   # classic star-history line colour


def fetch_starred_at():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    out, page = [], 1
    while True:
        url = f"https://api.github.com/repos/{REPO}/stargazers?per_page=100&page={page}"
        headers = {"Accept": "application/vnd.github.star+json",
                   "User-Agent": "star-history-gen"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        if not data:
            break
        out += [x["starred_at"] for x in data if x.get("starred_at")]
        if len(data) < 100:
            break
        page += 1
        if page > 500:        # safety cap (~50k stars)
            break
    return sorted(dt.datetime.fromisoformat(s.replace("Z", "+00:00")) for s in out)


def draw(ts, dark, path):
    if not ts:
        return
    xs = [ts[0] - dt.timedelta(minutes=20)] + ts
    ys = list(range(0, len(ts) + 1))
    bg = "#0d1117" if dark else "#ffffff"
    fg = "#c9d1d9" if dark else "#1a1a1a"
    axc = "#30363d" if dark else "#333333"
    grid = "#21262d" if dark else "#eeeeee"
    span_days = (ts[-1] - ts[0]).total_seconds() / 86400
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    ax.plot(xs, ys, color=RED, linewidth=2.4, solid_capstyle="round", solid_joinstyle="round")
    ax.set_title("Star history", color=fg, fontsize=15, fontweight="bold", pad=16)
    ax.set_xlabel("Date", color=fg, fontsize=11, style="italic")
    ax.set_ylabel("GitHub Stars", color=fg, fontsize=11)
    leg = ax.legend([Line2D([0], [0], marker='s', color='w', markerfacecolor=RED,
                            markersize=9, linestyle='')], [LABEL], loc="upper left",
                    frameon=True, fontsize=10.5, handletextpad=0.4, borderpad=0.7)
    leg.get_frame().set_edgecolor(axc); leg.get_frame().set_facecolor(bg); leg.get_frame().set_linewidth(1)
    for txt in leg.get_texts():
        txt.set_color(fg)
    ax.set_ylim(0, max(ys) * 1.12)
    ax.set_xlim(xs[0], xs[-1] + dt.timedelta(minutes=max(40, span_days * 20)))
    # adapt date format to the span so labels don't all read the same day
    if span_days <= 3:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d %H:%M"))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y" if span_days > 120 else "%b %d"))
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(axc); ax.spines[s].set_linewidth(1.1)
    ax.tick_params(colors=fg, labelsize=9.5); ax.grid(True, color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    plt.tight_layout()
    fig.savefig(path, facecolor=bg, bbox_inches="tight")
    plt.close()
    print("wrote", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    ts = fetch_starred_at()
    print(f"{REPO}: {len(ts)} stars")
    draw(ts, False, os.path.join(OUT, "star_history.png"))
    draw(ts, True, os.path.join(OUT, "star_history_dark.png"))


if __name__ == "__main__":
    main()
