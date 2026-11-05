#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""progress — the lines a run says to the USER at each stage, printed by the scripts themselves.

Measured on two real runs (2026-10-30, a 9-slide deck from the user's own files, one on the Claude path
and one on the docs-only Codex path): a full first render existed at minute 7.5–8.6, but the user first
saw a page at the very end, minute 34–41. The polishing between (self-check, fixes, review rounds) took
25–33 minutes the user could neither see nor steer. Prose asking the agent to "keep the user posted"
has no backstop and is skipped silently; a line printed by the command the agent just ran is read on
every host, Claude Code, Codex or any other agent that reads stdout.

Measured again (2026-11-05, six real runs, two agents): the agents relayed the printed preview ZERO
times — they act on the `next:` line, pipe output through `tail`, and even a 🔴 checkpoint in SKILL.md
did not move them. So the preview does not depend on the agent: on a desktop session the first full
render OPENS the contact sheet on the user's screen (`show`), which reached the user at minute 5.3 and
15.8 instead of at hand-off. The stage lines stay, for hosts whose UI shows command output; the review
stage is announced by commands (dispatch_brief.py, validate_review.py), never left to an agent's timing.

So the commands that mark a stage print a block that starts with TELL THE USER, in the deck's language
(the interview's `language` answer), and this module keeps `<deck-dir>/.deck-progress.json` so each
stage is announced once — the early preview above all, which must come at the FIRST render and never
again. Nothing happens outside a real run: no gate record (`.deck-gates.json` or the Codex `.codex-deck-evidence.json`) in the folder, no line and no file
(so CI renders of the examples and the tests stay silent).

    python3 scripts/progress.py <deck-dir> <stage>      # announce a stage by hand (plan, fixes)
    python3 scripts/progress.py <deck-dir> --status     # what has been announced, and when

Stages: brief → plan → preview → fixes → review → done.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
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
        "review": "进入独立评审：评审逐页检查后，我按意见修正，再做最终检查。",
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
        "review": "In independent review: a reviewer checks every slide; I fix what it finds, then run the final checks.",
        "done": "All final checks passed; the deck is ready to hand over.",
        "eta": "From past measured runs, a deck of about {size}slides takes roughly {lo}–{hi} more minutes "
               "from here{more}.",
        "more": "; more slides take longer",
        "size": "{n} ",
    },
}


RECORDS = (".deck-gates.json", ".codex-deck-evidence.json")    # the shared and the Codex gate record


def _lang(deck_dir):
    """The deck's language from the interview answer (either record); English unless it reads as Chinese."""
    v = ""
    for name in RECORDS:
        try:
            g = json.loads((Path(deck_dir) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        iv = g.get("interview") if isinstance(g, dict) else None
        v = str((iv or {}).get("language") or "").strip().lower() if isinstance(iv, dict) else ""
        if v:
            break
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


def open_command(path, env=None, platform=None):
    """The command that shows `path` on the user's own screen, or None when there is no screen to show
    it on. Four real runs (2026-11-05, two agents) printed the early preview and relayed it to the user
    zero times, so the preview no longer depends on the agent: on a desktop session the contact sheet
    simply opens. Off: SLIDE_MAKER_NO_OPEN=1, a CI run, an SSH session, a Linux box with no display.
    SLIDE_MAKER_OPEN_CMD (a command, the path appended) replaces the platform opener."""
    env = os.environ if env is None else env
    platform = platform or sys.platform
    if env.get("SLIDE_MAKER_NO_OPEN") or env.get("CI") or env.get("SSH_CONNECTION") or env.get("SSH_TTY"):
        return None
    if env.get("SLIDE_MAKER_OPEN_CMD"):
        return shlex.split(env["SLIDE_MAKER_OPEN_CMD"]) + [str(path)]
    if platform == "darwin":
        return ["open", str(path)]
    if platform.startswith("win"):
        return ["cmd", "/c", "start", "", str(path)]
    if env.get("DISPLAY") or env.get("WAYLAND_DISPLAY"):
        return ["xdg-open", str(path)]
    return None


def show(path, out=None):
    """Open `path` for the user without waiting on the viewer; returns True when an opener started."""
    cmd = open_command(path)
    if not cmd or not os.path.exists(str(path)):
        return False
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                         start_new_session=True)
    except (OSError, ValueError):
        return False
    print("(opened {} on the user's screen; SLIDE_MAKER_NO_OPEN=1 turns this off)".format(path),
          file=out or sys.stdout)
    return True


def in_run(deck_dir):
    """A real skill run: the deck folder carries a gate record (shared or Codex)."""
    return bool(deck_dir) and any((Path(deck_dir) / n).is_file() for n in RECORDS)


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
        if stage == "preview" and contact:
            show(contact, out=out)
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
        print("{} has no gate record (.deck-gates.json or .codex-deck-evidence.json) — not a slide-maker run, nothing announced".format(deck_dir),
              file=sys.stderr)
        return 2
    return 0 if announce(deck_dir, stage, once=False) else 1


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a character, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
