#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_ci_split.py — the CI workflow was split into parallel jobs; prove no step was lost or doubled.

One serial job of ~170 steps took 44 minutes. Splitting it is only safe if (a) every step still runs
EXACTLY once, and (b) no step depended on something another step left behind (a /tmp log, a generated
file) that now lives on a different runner. A split that drops a step looks identical to a split that
kept it: a skipped check and a passing check both print nothing.

    python3 scripts/check_ci_split.py                       # from the repo root; base = 27b4d6c (the last serial ci.yml)
    python3 scripts/check_ci_split.py --base <rev>          # compare against another revision
    python3 scripts/check_ci_split.py --base-file old.yml   # ... or a file on disk

Checks (exit 0 clean, 1 problems, 2 cannot run):
  1. the multiset of `run:` commands (and of `uses:` actions' own `with:`) outside the setup steps is
     IDENTICAL before and after — nothing dropped, nothing duplicated, nothing edited;
  2. the setup steps (apt install, pip install, checkout, setup-python) are the same commands in every
     job that has work to do, and every job has a timeout and the skill working directory;
  3. a temp path named by several steps is either kept inside one job (writer before reader) or written
     by each step that reads it — so a job boundary never separates a reader from its writer. (Static:
     it sees /tmp paths on the command line, not files a script writes into the working tree.)
"""
from __future__ import annotations

import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                       # cannot run must never look like clean
    print("check_ci_split: cannot run: PyYAML is not installed", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parent.parent
CI = REPO / ".github" / "workflows" / "ci.yml"
DEFAULT_BASE = "27b4d6c"

SETUP_RUN = re.compile(r"apt-get|pip install")
TMP = re.compile(r"/tmp/[\w./\-]+|\$\{?RUNNER_TEMP\}?[\w./\-]*")
WRITES = re.compile(r"(?:tee(?:\s+-a)?|>>?|--report|--out|-o)\s+(/tmp/[\w./\-]+)")


def jobs_of(doc):
    j = doc.get("jobs") or {}
    return {name: (job.get("steps") or []) for name, job in j.items()}, j


def is_setup(step):
    if "uses" in step:
        return True
    return bool(SETUP_RUN.search(step.get("run", "")))


def real_steps(steps):
    return [s for s in steps if not is_setup(s)]


def multiset(steps):
    return collections.Counter(
        (s.get("name", ""), s.get("run", "").strip(), s.get("working-directory", "")) for s in steps)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--base-file")
    a = ap.parse_args(argv)

    try:
        if a.base_file:
            old_text = Path(a.base_file).read_text(encoding="utf-8")
        else:
            old_text = subprocess.run(["git", "show", "%s:.github/workflows/ci.yml" % a.base],
                                      cwd=REPO, capture_output=True, text=True, check=True).stdout
        old_doc = yaml.safe_load(old_text)
        new_doc = yaml.safe_load(CI.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — cannot run must never look like clean
        print("check_ci_split: cannot run: %s" % e, file=sys.stderr)
        return 2

    old_jobs, _ = jobs_of(old_doc)
    new_jobs, new_raw = jobs_of(new_doc)
    problems = []

    old_steps = [s for st in old_jobs.values() for s in real_steps(st)]
    new_steps = [s for st in new_jobs.values() for s in real_steps(st)]
    if len(old_steps) < 100:
        problems.append("the base has only %d non-setup steps — wrong base revision?" % len(old_steps))
    mo, mn = multiset(old_steps), multiset(new_steps)
    for k in sorted((mo - mn).elements()):
        problems.append("LOST or EDITED step (in base, not in new): %s" % (k[0] or k[1][:60]))
    for k in sorted((mn - mo).elements()):
        problems.append("NEW or DUPLICATED step (in new, not in base): %s" % (k[0] or k[1][:60]))

    # setup consistency
    old_setup = [s.get("run", "").strip() for st in old_jobs.values() for s in st if "run" in s and is_setup(s)]
    for name, st in new_jobs.items():
        setup = [s.get("run", "").strip() for s in st if "run" in s and is_setup(s)]
        if setup != old_setup:
            problems.append("job %s: setup commands differ from the base's (%d vs %d)" % (name, len(setup), len(old_setup)))
        if not real_steps(st):
            problems.append("job %s has no work steps" % name)
        raw = new_raw[name]
        if "timeout-minutes" not in raw:
            problems.append("job %s has no timeout-minutes" % name)
        if (raw.get("defaults", {}).get("run", {}) or {}).get("working-directory") != "skills/slide-maker":
            problems.append("job %s lost defaults.run.working-directory" % name)
        uses = [s["uses"] for s in st if "uses" in s]
        if not any(u.startswith("actions/checkout") for u in uses):
            problems.append("job %s does not check out the repo" % name)

    # A temp path named by more than one step is a possible hand-off. Where it was shared in the base,
    # the new layout must either keep every sharer in ONE job, or each sharer must write it itself
    # before reading it (tee / > / --report), so a job boundary never separates a reader from its writer.
    where = collections.defaultdict(list)      # path -> [(job, index, step)]
    for name, st in new_jobs.items():
        for i, s in enumerate(st):
            for p in set(TMP.findall(s.get("run", ""))):
                where[p].append((name, i, s))
    for p, refs in sorted(where.items()):
        if len(refs) < 2:
            continue
        for name, i, s in refs:
            writes_itself = p in WRITES.findall(s.get("run", ""))
            others_same_job = [r for r in refs if r[0] == name and r[1] != i]
            if not writes_itself and not others_same_job:
                problems.append("job %s step %d (%s) reads %s, which another job's step also uses — a cross-job "
                                "dependency" % (name, i, s.get("name", "")[:50], p))
            if not writes_itself and others_same_job and not any(
                    r[1] < i and p in WRITES.findall(r[2].get("run", "")) for r in others_same_job):
                problems.append("job %s step %d (%s) reads %s before any step of the job wrote it"
                                % (name, i, s.get("name", "")[:50], p))

    n_new = len(new_steps)
    print("check_ci_split: base %d steps in %d job(s) -> %d work steps in %d job(s) (%s)"
          % (len(old_steps), len(old_jobs), n_new, len(new_jobs), ", ".join(new_jobs)))
    if problems:
        print("%d problem(s):" % len(problems))
        for p in problems:
            print("  " + p)
        return 1
    print("0 problem(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
