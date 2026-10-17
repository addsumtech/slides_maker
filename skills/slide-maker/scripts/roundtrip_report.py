#!/usr/bin/env python3
"""How many round-trips a build actually cost, measured from a session transcript.

🔴 THIS MUST NEVER BECOME A GATE, and the reason is the whole point of the file.

A deck's wall-clock cost is round-trips, not computation: measured on a delivered 12-page build,
the deterministic pipeline was 9.1 seconds and the build took 88 minutes. So the number below is
worth knowing. But the cheapest way to make it smaller is to LOOK AT LESS — skip a render read,
skip a verification, apply a fix without confirming it landed. Put it in the delivery gate and it
becomes a target that is satisfied by exactly the behaviour every other gate here exists to
prevent. Goodhart, in a codebase whose whole history is gates being met rather than achieved.

So it is a DEVELOPER tool, run after the fact, to find out where a build's turns went and whether
a change to the skill moved them. It is not part of the deck pipeline, nothing reads its output,
and `references/maintenance-boundaries.md` carries the contract that it stays that way.

USAGE
    python3 scripts/roundtrip_report.py <transcript.jsonl> [--from "<text>"] [--to "<text>"]

`--from` / `--to` are substrings of the user messages that bracket the build (default: the whole
transcript). Prints the turn count, the batching ratio, the tool mix, and the commands that were
issued more than once — the four things that have actually explained a slow build.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import sys
from pathlib import Path

NOISE = ("<system-reminder>", "<task-notification>", "(Re-invocation", "Base directory",
         "<command-name>", "<local-command")


def _rows(path):
    for line in Path(path).open(encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        ts = d.get("timestamp")
        if not ts:
            continue
        m = d.get("message") or {}
        c = m.get("content")
        text, tools, is_tool_result = "", [], False
        if isinstance(c, str):
            text = c
        elif isinstance(c, list):
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    text += b.get("text", "")
                elif b.get("type") == "tool_use":
                    tools.append((b.get("name"), b.get("input") or {}))
                elif b.get("type") == "tool_result":
                    is_tool_result = True
        kind = d.get("type")
        if kind == "user" and is_tool_result:
            kind = "tool"
        yield dt.datetime.fromisoformat(ts.replace("Z", "+00:00")), kind, text, tools


def _real_user(kind, text):
    return kind == "user" and text.strip() and not text.lstrip().startswith(NOISE)


def main(argv):
    argv = list(argv)
    src = next((a for a in argv if not a.startswith("-")), None)
    if not src:
        print(__doc__.split("USAGE")[1].strip())
        return 2

    def opt(name):
        for i, a in enumerate(argv):
            if a == name and i + 1 < len(argv):
                return argv[i + 1]
            if a.startswith(name + "="):
                return a.split("=", 1)[1]
        return None

    rows = list(_rows(src))
    if not rows:
        print("roundtrip_report: no timestamped entries in that transcript")
        return 1
    f_mark, t_mark = opt("--from"), opt("--to")
    start = rows[0][0]
    end = rows[-1][0]
    # A marker that matches nothing must NOT silently widen the window to the whole transcript.
    # Measured: a typo'd --from reported a 9,492-minute "build" with 1,836 minutes of assistant
    # work, in the same layout as a real answer. A wrong number delivered confidently is worse
    # than an error, and this tool exists to inform a judgement about where time goes.
    for mark, name in ((f_mark, "--from"), (t_mark, "--to")):
        if mark and not any(_real_user(k, x) and mark in x for _t, k, x, _tl in rows):
            print(f"roundtrip_report: {name} {mark!r} matches no user message in that transcript. "
                  f"Not falling back to the whole file — the window would be meaningless.")
            return 2
    if f_mark:
        start = next(t for t, k, x, _ in rows if _real_user(k, x) and f_mark in x)
    if t_mark:
        end = next(t for t, k, x, _ in rows if _real_user(k, x) and t_mark in x)
    if end < start:
        print("roundtrip_report: --to occurs BEFORE --from in this transcript; the window would "
              "be negative. Check the two markers.")
        return 2
    win = [r for r in rows if start <= r[0] <= end]

    asst = [r for r in win if r[1] == "assistant"]
    with_tools = [r for r in asst if r[3]]
    ntools = sum(len(r[3]) for r in asst)
    waits = 0.0
    for i in range(1, len(win)):
        pt, pk = win[i - 1][0], win[i - 1][1]
        t, k, x = win[i][0], win[i][1], win[i][2]
        if _real_user(k, x) and pk != "user":
            waits += (t - pt).total_seconds()
    span = (end - start).total_seconds()

    print(f"window            {start:%H:%M} → {end:%H:%M}   ({span / 60:.1f} min)")
    print(f"waiting on user   {waits / 60:.1f} min")
    print(f"assistant working {(span - waits) / 60:.1f} min")
    print(f"turns             {len(asst)}   ({len(asst) - len(with_tools)} with no tool call)")
    print(f"tool calls        {ntools}")
    if with_tools:
        ratio = ntools / len(with_tools)
        note = "  ← 1.00 means nothing was batched" if ratio < 1.05 else ""
        print(f"batching          {ratio:.2f} tools per message{note}")
        dist = collections.Counter(len(r[3]) for r in with_tools)
        print(f"                  per-message: {dict(sorted(dist.items()))}")
    if span - waits > 0 and asst:
        print(f"per turn          {(span - waits) / len(asst):.0f} s")

    mix = collections.Counter(n for r in asst for n, _ in r[3])
    if mix:
        print("\ntool mix          " + " · ".join(f"{k} {v}" for k, v in mix.most_common(8)))

    cmds = collections.Counter()
    for r in asst:
        for n, inp in r[3]:
            key = None
            if n == "Bash":
                key = "Bash: " + str(inp.get("command", ""))[:64].replace("\n", " ")
            elif n in ("Read", "Edit", "Write"):
                key = f"{n}: " + str(inp.get("file_path", "")).split("/")[-1]
            if key:
                cmds[key] += 1
    rep = [(k, v) for k, v in cmds.most_common(8) if v > 1]
    if rep:
        print(f"\nrepeated calls    ({len(cmds)} distinct)")
        for k, v in rep:
            print(f"   x{v:<3} {k}")
    print("\nThis is a developer measurement. It is deliberately not a gate: the cheapest way to "
          "\nmake these numbers smaller is to look at less, which is the failure every other "
          "\ncheck in this skill exists to prevent.")
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
