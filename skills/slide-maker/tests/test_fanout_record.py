#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A fan-out was atomic in the worst way: one dead agent cost the whole round.

The pipeline dispatches agents in parallel three times over — research, the critic panel, section
authoring — and all three returned into the coordinator's memory. Memory is not a file, so a
round with one dead member had a hole in it and the only repair was re-running everything,
including the members that had already succeeded.

Measured on one deck built with this skill:
  · research — 22 agents, 1.08M tokens, 24.9 min; the claim ledger survived only because it was
    hand-copied into _record/ afterwards.
  · critic   — 2 lenses dispatched, the DESIGN lens died on a session limit. The content lens had
    already produced a complete review (1 blocker, 7 majors, 6 minors) which was read out of the
    workflow result and never written down, so `validate_review.py --record` had nothing to
    register and the deck shipped with `.deck-gates.json` holding only `{"delivery": …}`.
  · earlier  — a 19-agent round returned `surviving: 0`, which reads exactly like "nothing was
    found"; 31 findings were recovered by hand out of journal.jsonl.

🔴 This is persistence, NOT a channel between agents. The isolation is the design: a critic that
knows the author's intent stops being independent, and two lenses that compare notes stop being
two pieces of evidence. Nothing here moves data sideways between agents — it moves results DOWN,
onto disk, where a rerun or a later step can pick them up.

The two load-bearing behaviours, both asserted below:
  · `status` EXITS 1 on an incomplete round and names only the members to re-dispatch. "The round
    is complete" becomes a check rather than something the coordinator remembers.
  · a dead member is recorded as `failed` WITH a reason, because "nobody found anything" and "the
    agent died" are indistinguishable unless one of them is written down — which is exactly how
    `surviving: 0` was misread once.

Run:  python3 tests/test_fanout_record.py
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
TOOL = SCRIPTS / "fanout_record.py"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name
          + (("  — " + str(detail)) if detail and not cond else ""))


def run(*args, stdin=None):
    r = subprocess.run([sys.executable, str(TOOL)] + [str(a) for a in args],
                       capture_output=True, text=True, input=stdin)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    print("fanout record")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="fan_"))
    try:
        deck = tmp / "deck"
        deck.mkdir()

        # ---- put: the result becomes a file ------------------------------------------------
        payload = json.dumps({"lens": "content", "verdict": "revise",
                              "findings": [{"slide": 10, "severity": "blocker"}]},
                             ensure_ascii=False)
        code, out = run("put", deck, "--round", "critic-r1", "--member", "content",
                        "--json", payload)
        check("put records a member and says where it landed", code == 0 and "recorded" in out, out)
        body = deck / "_record" / "fanout" / "critic-r1" / "content.json"
        check("...as a real file on disk", body.exists(), body)
        check("...with the payload intact",
              json.loads(body.read_text(encoding="utf-8"))["verdict"] == "revise")
        meta = json.loads((body.parent / "content.meta.json").read_text(encoding="utf-8"))
        check("...and a meta record carrying status + sha256",
              meta["status"] == "ok" and len(meta["sha256"]) == 64, meta)

        # a payload that is not JSON is still evidence
        code, out = run("put", deck, "--round", "critic-r1", "--member", "notes",
                        "--json", "a plain text return from an agent")
        check("a non-JSON return is recorded rather than rejected", code == 0, out)
        check("...as .txt, and flagged as text",
              (deck / "_record/fanout/critic-r1/notes.txt").exists()
              and json.loads((deck / "_record/fanout/critic-r1/notes.meta.json")
                             .read_text(encoding="utf-8"))["kind"] == "text")

        # ---- an EMPTY payload must not be recorded as a result ------------------------------
        code, out = run("put", deck, "--round", "critic-r1", "--member", "ghost", "--json", "   ")
        check("an empty payload is refused, not stored as a result", code == 2, out)
        check("...and the message points at `miss` instead", "miss" in out, out)

        # ---- miss: the absence is itself a record -------------------------------------------
        code, out = run("miss", deck, "--round", "critic-r1", "--member", "design",
                        "--why", "session limit")
        check("a dead member is recorded as failed", code == 0 and "FAILED" in out, out)
        m = json.loads((deck / "_record/fanout/critic-r1/design.meta.json")
                       .read_text(encoding="utf-8"))
        check("...with the reason kept, so 'died' cannot read as 'found nothing'",
              m["status"] == "failed" and m["why"] == "session limit", m)

        # ---- status: completeness is a CHECK, not a memory ----------------------------------
        code, out = run("status", deck, "--round", "critic-r1", "--expect", "content,design")
        check("an incomplete round EXITS 1", code == 1, code)
        check("...names only the member to re-dispatch",
              "re-dispatch only: design" in out, out)
        check("...and says the ok ones must not be dispatched again",
              "must not be dispatched again" in out, out)
        check("...while showing the one that landed as ok", "ok      content" in out, out)

        code, out = run("status", deck, "--round", "critic-r1", "--expect", "content")
        check("a round whose expected members all landed EXITS 0", code == 0, out)
        check("...and says so", "round complete" in out, out)

        code, out = run("status", deck, "--round", "critic-r1", "--expect", "content,design,extra")
        check("a member that was never dispatched at all is MISSING, not silently ok",
              code == 1 and "MISSING extra" in out, out)

        # a round nobody has written to is incomplete, never "clean"
        code, out = run("status", deck, "--round", "never-ran", "--expect", "a,b")
        check("an empty round exits 1 rather than reading as complete", code == 1, out)

        # ---- re-running a member overwrites cleanly (the whole point of a rerun) -------------
        code, _ = run("put", deck, "--round", "critic-r1", "--member", "design",
                      "--json", json.dumps({"lens": "design", "verdict": "consent"}))
        check("re-dispatching a failed member replaces its record", code == 0)
        code, out = run("status", deck, "--round", "critic-r1", "--expect", "content,design")
        check("...and the round then reports complete", code == 0 and "round complete" in out, out)

        # ---- put --file and stdin, the two shapes a caller actually has ----------------------
        f = tmp / "review.json"
        f.write_text(json.dumps({"lens": "arbiter", "ok": True}), encoding="utf-8")
        code, _ = run("put", deck, "--round", "critic-r2", "--member", "arbiter", "--file", str(f))
        check("put --file works", code == 0)
        code, _ = run("put", deck, "--round", "critic-r2", "--member", "piped",
                      stdin='{"from": "stdin"}')
        check("put from stdin works", code == 0)

        # ---- list: what rounds exist at all --------------------------------------------------
        code, out = run("list", deck)
        check("list shows every round with its counts",
              code == 0 and "critic-r1" in out and "critic-r2" in out, out)

        # ---- a bad deck dir must fail loudly, never silently succeed --------------------------
        code, out = run("status", tmp / "nope", "--round", "x")
        check("a missing deck directory exits 2 (could-not-run)", code == 2, out)

        # ---- a round name with path characters cannot escape the deck folder ------------------
        code, _ = run("put", deck, "--round", "../../etc", "--member", "x", "--json", "{}")
        escaped = (tmp / "etc").exists() or (tmp.parent / "etc").exists()
        check("a traversal-looking round name stays inside the deck folder", not escaped)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
