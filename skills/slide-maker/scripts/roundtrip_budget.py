#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure what a deck build actually COST in round-trips, and say so out loud.

Why this exists
---------------
SKILL.md's preamble states the governing equation — *"the cost of a deck is `round-trips x
context`, not the size of what you write"* — and Step 5 restates it at the two places it binds
(the render self-check's slide reads, the fix pass's edits). All three are prose. Prose with no
gate is advisory in practice: nothing reports a run that read fourteen PNGs in fourteen messages,
because the deck still builds, every lint still passes, and the critic still consents. The bill
arrives as wall-clock the user notices and cannot attribute.

So this script computes the number from the session transcript rather than asking anyone to
remember it, and the Step-6 hand-off `cost:` line carries the measured value. It is a REPORTER,
not a blocker: it never fails a build. A heuristic that halts a finished deck would be worse than
the problem, and the point is attribution, not enforcement.

What it measures
----------------
  round-trips     assistant turns that issued >=1 tool call. This is the term that multiplies by
                  context, so it is the headline number.
  batching ratio  tool calls / round-trip. 1.00 means every call went in its own message; the
                  skill's own measured build averaged exactly 1.00 and its first fifteen calls
                  were unrelated fact-gathering that could have been three.
  image batching  the largest number of image reads issued in a single message, against the deck's
                  slide count — the render self-check is meant to read them all at once.
  context         median tokens re-sent per turn. Multiply by round-trips for the real bill.

Usage
-----
  python3 scripts/roundtrip_budget.py                       # newest transcript touching cwd
  python3 scripts/roundtrip_budget.py --transcript X.jsonl  # an explicit one
  python3 scripts/roundtrip_budget.py --slides 14 --json    # machine-readable, for the cost: line

Exit status is 0 unless the transcript could not be read at all (2) — over-budget is reported in
the text, never in the exit code.
"""
import argparse
import glob
import json
import os
import sys

# Budgets are ORDERS OF MAGNITUDE, not targets to hit exactly. They come from the skill's own
# measurement (SKILL.md: a 12-page build = 122 calls at ~302k context) plus the transcript study
# that produced this script. A build inside them is not necessarily good; a build far outside them
# is reliably paying for round-trips it did not need.
BUDGET_ROUNDTRIPS_BASE = 60      # interview, planning, design, hand-off — largely slide-independent
BUDGET_ROUNDTRIPS_PER_SLIDE = 5  # build + render + the fix rounds
MIN_BATCH_RATIO = 1.25           # below this, independent calls are going out one at a time


def _iter_records(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def find_transcript(explicit=None):
    """Locate the session transcript. Claude Code stores one .jsonl per session under
    ~/.claude/projects/<slugified-cwd>/. We prefer the newest transcript whose slug matches the
    current directory, then fall back to the newest overall — a wrong guess produces a wrong
    number, so the chosen path is always printed."""
    if explicit:
        return explicit if os.path.exists(explicit) else None
    root = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(root):
        return None
    cwd_slug = os.getcwd().replace("/", "-")
    pools = [
        glob.glob(os.path.join(root, cwd_slug, "*.jsonl")),
        glob.glob(os.path.join(root, "*", "*.jsonl")),
    ]
    for pool in pools:
        if pool:
            return max(pool, key=os.path.getmtime)
    return None


def analyse(path):
    roundtrips = 0
    tool_calls = 0
    assistant_turns = 0
    out_tokens = 0
    contexts = []
    max_images_in_one_message = 0
    image_reads = 0
    unbatched_bash = 0
    chained_bash = 0
    for rec in _iter_records(path):
        if rec.get("type") != "assistant" or rec.get("isSidechain"):
            continue
        assistant_turns += 1
        msg = rec.get("message") or {}
        usage = msg.get("usage") or {}
        out_tokens += usage.get("output_tokens", 0) or 0
        ctx = ((usage.get("input_tokens", 0) or 0)
               + (usage.get("cache_read_input_tokens", 0) or 0)
               + (usage.get("cache_creation_input_tokens", 0) or 0))
        if ctx:
            contexts.append(ctx)
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        calls = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        if not calls:
            continue
        roundtrips += 1
        tool_calls += len(calls)
        imgs = 0
        for block in calls:
            inp = block.get("input") or {}
            name = block.get("name", "")
            if name == "Read":
                fp = str(inp.get("file_path", "")).lower()
                if fp.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                    imgs += 1
                    image_reads += 1
            elif name == "Bash":
                cmd = str(inp.get("command", ""))
                if "&&" in cmd:
                    chained_bash += 1
                else:
                    unbatched_bash += 1
        max_images_in_one_message = max(max_images_in_one_message, imgs)
    contexts.sort()
    return dict(
        transcript=path,
        assistant_turns=assistant_turns,
        roundtrips=roundtrips,
        tool_calls=tool_calls,
        batch_ratio=(tool_calls / roundtrips) if roundtrips else 0.0,
        output_tokens=out_tokens,
        median_context=contexts[len(contexts) // 2] if contexts else 0,
        image_reads=image_reads,
        max_images_in_one_message=max_images_in_one_message,
        bash_chained=chained_bash,
        bash_unchained=unbatched_bash,
    )


def report(st, slides):
    budget = BUDGET_ROUNDTRIPS_BASE + BUDGET_ROUNDTRIPS_PER_SLIDE * slides if slides else None
    bill = st["roundtrips"] * st["median_context"]
    lines = []
    lines.append("round-trip budget — measured from {}".format(os.path.basename(st["transcript"])))
    lines.append("  round-trips        {}{}".format(
        st["roundtrips"],
        "" if budget is None else "   (budget for {} slides: ~{})".format(slides, budget)))
    lines.append("  tool calls         {}".format(st["tool_calls"]))
    lines.append("  batching ratio     {:.2f} calls/round-trip".format(st["batch_ratio"]))
    lines.append("  median context     {:,} tok/turn".format(st["median_context"]))
    lines.append("  context re-sent    ~{:,} tok  (round-trips x median context)".format(bill))
    lines.append("  output tokens      {:,}".format(st["output_tokens"]))
    lines.append("  bash calls         {} chained / {} single".format(
        st["bash_chained"], st["bash_unchained"]))
    lines.append("  image reads        {} total, most in one message: {}".format(
        st["image_reads"], st["max_images_in_one_message"]))

    notes = []
    if budget and st["roundtrips"] > budget:
        notes.append(
            "OVER BUDGET: {} round-trips vs ~{} expected for a {}-slide deck. At {:,} tok of "
            "context each, the excess cost ~{:,} tokens.".format(
                st["roundtrips"], budget, slides, st["median_context"],
                (st["roundtrips"] - budget) * st["median_context"]))
    if st["batch_ratio"] and st["batch_ratio"] < MIN_BATCH_RATIO:
        notes.append(
            "LOW BATCHING: {:.2f} calls per round-trip. Independent calls are going out one at a "
            "time — see SKILL.md 'Issue independent calls together in ONE message'.".format(
                st["batch_ratio"]))
    if slides and st["image_reads"] >= slides and st["max_images_in_one_message"] < max(2, slides // 2):
        notes.append(
            "UNBATCHED SLIDE READS: {} image reads but never more than {} in one message. The "
            "render self-check is meant to read every slide PNG in ONE message.".format(
                st["image_reads"], st["max_images_in_one_message"]))
    if notes:
        lines.append("")
        for n in notes:
            lines.append("  [over] " + n)
    else:
        lines.append("")
        lines.append("  [ok] within budget")
    lines.append("")
    lines.append("  cost: line for the hand-off -> "
                 "cost: {} round-trips · ~{:,} tok context re-sent · {:,} tok generated".format(
                     st["roundtrips"], bill, st["output_tokens"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", help="session .jsonl (default: newest matching this cwd)")
    ap.add_argument("--slides", type=int, default=0, help="slide count, to size the budget")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    path = find_transcript(args.transcript)
    if not path:
        sys.stderr.write(
            "roundtrip_budget: no session transcript found. Pass --transcript <file.jsonl>.\n"
            "This is a reporter, not a gate — a build is not wrong because this could not run.\n")
        return 2
    st = analyse(path)
    if st["roundtrips"] == 0:
        sys.stderr.write("roundtrip_budget: {} has no tool-using assistant turns — wrong "
                         "transcript?\n".format(path))
        return 2
    if args.json:
        print(json.dumps(st, indent=2))
    else:
        print(report(st, args.slides))
    return 0


if __name__ == "__main__":
    sys.exit(main())
