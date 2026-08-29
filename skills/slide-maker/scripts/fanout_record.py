#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fanout_record.py — land what a fan-out produced on disk, so one dead agent costs one agent.

WHY THIS EXISTS
    The pipeline dispatches agents in parallel three times over: research (claim ledger), the
    critic panel (one review per lens), and section authoring. All three return into memory, and
    memory is where the coordinator's context lives — so a fan-out is atomic in the worst way: if
    one member dies, the round has a hole in it and the only repair is running the whole round
    again.

    Measured on one deck built with this skill:
      · research  — 22 agents, 1.08M tokens, 24.9 min. The claim ledger survived only because it
        was hand-copied into _record/ afterwards.
      · critic    — 2 lenses dispatched, the DESIGN lens died on a session limit. The content
        lens had already produced a full review (1 blocker, 7 majors, 6 minors) that was read out
        of the workflow result and never written down, so `validate_review.py --record` had
        nothing to register and the delivered deck shipped with an empty `.deck-gates.json`.
      · earlier   — a 19-agent stress round returned `surviving: 0`, which reads identically to
        "nothing was found". 31 findings were recovered by hand out of journal.jsonl.

    Every one of those is the same bug: a result that exists but is not a file.

WHAT IT IS NOT
    Not a channel between agents. The isolation is the design — a critic that knows the author's
    intent stops being independent, and two lenses that compare notes stop being two pieces of
    evidence. This never moves data sideways between agents; it only moves it DOWN, onto disk,
    where a later step or a rerun can pick it up.

USAGE
    fanout_record.py put   <deck-dir> --round critic-r1 --member design  --file review.json
    fanout_record.py put   <deck-dir> --round critic-r1 --member content --json '<inline>'
    fanout_record.py miss  <deck-dir> --round critic-r1 --member design  --why "session limit"
    fanout_record.py status <deck-dir> --round critic-r1 --expect content,design
    fanout_record.py list  <deck-dir>

    `status` exits 0 only when every expected member landed; 1 when any is missing or failed —
    so "the round is complete" is a check, not a memory.

EXIT CODES
    0 = ok / round complete · 1 = round incomplete · 2 = could not run
"""
import argparse
import hashlib
import json
import os
import sys
import time

DIRNAME = "_record/fanout"


def die(msg):
    print("fanout_record: " + msg, file=sys.stderr)
    sys.exit(2)


def _round_dir(deck_dir, rnd):
    if not os.path.isdir(deck_dir):
        die("%s is not a directory" % deck_dir)
    safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in rnd)
    if not safe:
        die("--round needs a name")
    d = os.path.join(deck_dir, DIRNAME, safe)
    os.makedirs(d, exist_ok=True)
    return d


def _digest(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def cmd_put(args):
    d = _round_dir(args.deck, args.round)
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                payload = fh.read()
        except OSError as exc:
            die("cannot read %s (%s)" % (args.file, exc))
    elif args.json:
        payload = args.json
    else:
        payload = sys.stdin.read()
    if not payload.strip():
        die("refusing to record an empty payload for %r — an empty result and a dead agent read "
            "the same, which is the confusion this tool exists to remove; use `miss` instead"
            % args.member)
    # Parse when it is JSON so a truncated agent return is caught HERE rather than three steps
    # later, but keep the raw text either way — a non-JSON return is still evidence.
    parsed, kind = None, "text"
    try:
        parsed, kind = json.loads(payload), "json"
    except ValueError:
        pass
    body = os.path.join(d, "%s.%s" % (args.member, "json" if kind == "json" else "txt"))
    with open(body, "w", encoding="utf-8") as fh:
        fh.write(payload if kind == "text" else json.dumps(parsed, ensure_ascii=False, indent=1))
    meta = {"member": args.member, "status": "ok", "kind": kind, "bytes": len(payload),
            "sha256": _digest(payload), "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "file": os.path.basename(body)}
    with open(os.path.join(d, "%s.meta.json" % args.member), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    print("recorded %s/%s -> %s (%d bytes, %s)" % (args.round, args.member, body,
                                                   len(payload), kind))
    return 0


def cmd_miss(args):
    """A member that did NOT produce a result. Recording the absence is the point: 'nobody
    found anything' and 'the agent died' are indistinguishable unless one of them is written
    down — a real 19-agent round once returned `surviving: 0` for the second reason."""
    d = _round_dir(args.deck, args.round)
    meta = {"member": args.member, "status": "failed", "why": args.why or "unspecified",
            "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(os.path.join(d, "%s.meta.json" % args.member), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    print("recorded %s/%s as FAILED: %s" % (args.round, args.member, meta["why"]))
    return 0


def _members(d):
    out = {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".meta.json"):
            continue
        try:
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                m = json.load(fh)
            out[m.get("member") or f[:-10]] = m
        except (OSError, ValueError):
            out[f[:-10]] = {"member": f[:-10], "status": "unreadable"}
    return out


def cmd_status(args):
    d = _round_dir(args.deck, args.round)
    have = _members(d)
    expect = [m.strip() for m in (args.expect or "").split(",") if m.strip()] or sorted(have)
    if not expect:
        print("round %s: nothing recorded yet" % args.round)
        return 1
    missing, failed = [], []
    print("round %s" % args.round)
    for m in expect:
        rec = have.get(m)
        if rec is None:
            print("  MISSING %s — never recorded" % m)
            missing.append(m)
        elif rec.get("status") != "ok":
            print("  FAILED  %s — %s" % (m, rec.get("why", rec.get("status"))))
            failed.append(m)
        else:
            print("  ok      %s (%s, %s bytes)" % (m, rec.get("kind"), rec.get("bytes")))
    if missing or failed:
        print("\nround INCOMPLETE — re-dispatch only: %s" % ", ".join(missing + failed))
        print("(the members above are the whole re-run; the ones marked ok are on disk and "
              "must not be dispatched again)")
        return 1
    print("\nround complete: %d of %d" % (len(expect), len(expect)))
    return 0


def cmd_list(args):
    base = os.path.join(args.deck, DIRNAME)
    if not os.path.isdir(base):
        print("no fan-out records under %s" % base)
        return 0
    for rnd in sorted(os.listdir(base)):
        have = _members(os.path.join(base, rnd))
        ok = sum(1 for m in have.values() if m.get("status") == "ok")
        print("%-24s %d recorded, %d ok" % (rnd, len(have), ok))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    for name in ("put", "miss", "status", "list"):
        p = sub.add_parser(name)
        p.add_argument("deck")
        if name != "list":
            p.add_argument("--round", required=True)
        if name in ("put", "miss"):
            p.add_argument("--member", required=True)
        if name == "put":
            p.add_argument("--file")
            p.add_argument("--json")
        if name == "miss":
            p.add_argument("--why")
        if name == "status":
            p.add_argument("--expect", help="comma-separated members this round owes")
    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 2
    return {"put": cmd_put, "miss": cmd_miss, "status": cmd_status, "list": cmd_list}[args.cmd](args)


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
