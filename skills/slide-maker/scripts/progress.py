#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""progress — the lines a run says to the USER at each stage, printed by the scripts themselves.

Measured on two real runs (2026-10-30, a 9-slide deck from the user's own files, one on the Claude path
and one on the docs-only Codex path): a full first render existed at minute 7.5–8.6, but the user first
saw a page at the very end, minute 34–41. The polishing between (self-check, fixes, review rounds) took
25–33 minutes the user could neither see nor steer. Prose asking the agent to "keep the user posted"
has no backstop and is skipped silently; a line printed by the command the agent just ran is read on
every host, Claude Code, Codex or any other agent that reads stdout.

So the commands that mark a stage print a block that starts with TELL THE USER, in the deck's language
(the interview's `language` answer), and this module keeps `<deck-dir>/.deck-progress.json` so each
stage is announced once — the early preview above all, which must come at the FIRST render and never
again. Nothing happens outside a real run: no `.deck-gates.json` in the folder, no line and no file
(so CI renders of the examples and the tests stay silent).

    python3 scripts/progress.py <deck-dir> <stage>      # announce a stage by hand (plan, fixes)
    python3 scripts/progress.py <deck-dir> --status     # what has been announced, and when

Stages: brief → plan → preview → fixes → review → done.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

STAGES = ("brief", "plan", "preview", "fixes", "review", "done")

# Minutes still to go after each stage, as measured (9-slide deck, two runs, 2026-10-30). Said as a
# range for a deck of that size, never as a promise; a longer deck is said to take longer.
_MEASURED_SLIDES = 9
_LEFT = {"brief": (30, 40), "plan": (28, 35), "preview": (25, 33), "fixes": (12, 20), "review": (5, 15)}

_TEXT = {
    "zh": {
        "head": "告诉用户（第 {k}/{n} 步）：",
        "brief": "需求已确认。下一步：规划内容和设计。",
        "plan": "内容和设计方案已定。下一步：生成第一版页面。",
        "preview": ("第一版已经生成，共 {slides} 页，先给你看全貌：{contact}\n"
                    "接下来我会逐页检查、修正，再请独立评审把关。你现在就可以提意见"
                    "（改哪页、哪里不对、风格要不要换），我会在接下来的修改里一并处理。"),
        "fixes": "正在逐页检查和修正。",
        "review": "修正完成，正在请独立评审逐页检查。",
        "done": "最终检查已全部通过，可以交付。",
        "eta": "按以往实测，{size}页左右的 deck 从这里到交付大约还要 {lo}–{hi} 分钟{more}。",
        "more": "；页数更多会更久",
        "size": "{n} ",
    },
    "en": {
        "head": "TELL THE USER (step {k}/{n}):",
        "brief": "Your brief is confirmed. Next: planning the content and the design.",
        "plan": "The content and design plan is set. Next: building the first version of the slides.",
        "preview": ("The first version is built, {slides} slides — here is the whole deck: {contact}\n"
                    "Next I check and fix every slide, then an independent reviewer checks it. You can "
                    "comment now (a slide to change, something wrong, a different look) and I will fold "
                    "it into the fixes that follow."),
        "fixes": "Checking and fixing every slide.",
        "review": "Fixes done; an independent reviewer is now checking every slide.",
        "done": "All final checks passed; the deck is ready to hand over.",
        "eta": "From past measured runs, a deck of about {size}slides takes roughly {lo}–{hi} more minutes "
               "from here{more}.",
        "more": "; more slides take longer",
        "size": "{n} ",
    },
}


def _lang(deck_dir):
    """The deck's language from the interview answer; English unless it reads as Chinese."""
    try:
        g = json.loads((Path(deck_dir) / ".deck-gates.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "en"
    iv = g.get("interview") if isinstance(g, dict) else None
    v = str((iv or {}).get("language") or "").strip().lower() if isinstance(iv, dict) else ""
    if v.startswith("zh") or "中" in v or "chinese" in v or "汉" in v:
        return "zh"
    return "en"


def _state_path(deck_dir):
    return Path(deck_dir) / ".deck-progress.json"


def _load(deck_dir):
    try:
        s = json.loads(_state_path(deck_dir).read_text(encoding="utf-8"))
        return s if isinstance(s, dict) else {}
    except (OSError, ValueError):
        return {}


def in_run(deck_dir):
    """A real skill run: the deck folder carries its gate record."""
    return bool(deck_dir) and (Path(deck_dir) / ".deck-gates.json").is_file()


def announce(deck_dir, stage, *, slides=None, contact=None, once=True, out=None):
    """Print the TELL THE USER block for `stage` and record it. Returns the text printed ("" when
    nothing was: not a run, an unknown stage, or a once-only stage already announced). Never raises:
    a progress line must not fail a render or a gate."""
    try:
        if stage not in STAGES or not in_run(deck_dir):
            return ""
        state = _load(deck_dir)
        seen = state.get("stages") if isinstance(state.get("stages"), dict) else {}
        if once and stage in seen:
            return ""
        t = _TEXT[_lang(deck_dir)]
        body = t[stage].format(slides=slides if slides is not None else "?",
                               contact=contact or "render/contact.png")
        lines = [t["head"].format(k=STAGES.index(stage) + 1, n=len(STAGES)), "  " + body.replace("\n", "\n  ")]
        if stage in _LEFT:
            lo, hi = _LEFT[stage]
            n = slides if isinstance(slides, int) and slides > 0 else None
            if n is None:
                n = state.get("slides") if isinstance(state.get("slides"), int) else None
            more = t["more"] if n and n > _MEASURED_SLIDES + 2 else ""
            lines.append("  " + t["eta"].format(size=t["size"].format(n=_MEASURED_SLIDES), lo=lo, hi=hi,
                                                  more=more))
        text = "\n".join(lines)
        print("\n" + text, file=out or sys.stdout)
        if stage == "preview":
            # Said to the AGENT, not the user: the review stage has a script hook only on hosts that
            # dispatch through dispatch_brief.py, so every other host is told here, at the one render
            # every path goes through.
            print("AGENT NEXT: say the block above to the user now, in your own words, with the image. "
                  "When the independent review starts, run:  python3 {} {} review".format(
                      os.path.abspath(__file__), os.path.abspath(deck_dir)), file=out or sys.stdout)
        seen[stage] = time.strftime("%Y-%m-%dT%H:%M:%S")
        state["stages"] = seen
        if isinstance(slides, int):
            state["slides"] = slides
        _state_path(deck_dir).write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n",
                                         encoding="utf-8")
        return text
    except Exception:                       # a progress line is never worth a failed command
        return ""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(__doc__.split("Stages:")[0].rstrip())
        return 2
    deck_dir, stage = argv
    if stage == "--status":
        s = _load(deck_dir)
        for k in STAGES:
            print("  {:<8} {}".format(k, (s.get("stages") or {}).get(k, "—")))
        return 0
    if stage not in STAGES:
        print("unknown stage {!r} — one of: {}".format(stage, ", ".join(STAGES)), file=sys.stderr)
        return 2
    if not in_run(deck_dir):
        print("{} has no .deck-gates.json — not a slide-maker run, nothing announced".format(deck_dir),
              file=sys.stderr)
        return 2
    return 0 if announce(deck_dir, stage, once=False) else 1


if __name__ == "__main__":
    sys.exit(main())
