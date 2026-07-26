#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_repo_integrity.py — catch source files this repo silently does not contain.

The failure this exists for, verbatim: `.gitignore` hardened credential patterns with
`*_secret*`, which also matches `scripts/scan_secrets.py` — the credential SCANNER itself.
The file existed on the author's disk, ran clean locally, was documented in SECURITY.md and
invoked by three CI steps, and was never in a single commit. Every clone was missing it and
CI died on `can't open file ... scan_secrets.py`.

Nothing reported it, because every layer looked fine from where it stood: the script worked
locally, the docs described a real file, CI referenced a real path. Only the intersection was
wrong. Two mechanical checks close it:

  1. a file that EXISTS in a source directory but is IGNORED by git is almost always a mistake
     — real secrets do not live in scripts/ or skills/ with a .py extension
  2. every path a CI workflow invokes must be TRACKED, not merely present on the runner

    python3 scripts/check_repo_integrity.py            # exit 0 clean · 1 findings · 2 cannot run

Deliberate exceptions go in EXPECTED_IGNORED with a written reason, so each one is a decision
somebody made rather than a casualty.
"""
import os
import re
import subprocess
import sys

# Directories whose contents are SOURCE. An ignored file here is a bug, not a secret.
SOURCE_DIRS = ("scripts", "skills", ".github")
SOURCE_EXT = {".py", ".md", ".json", ".yml", ".yaml", ".sh", ".svg", ".css", ".js", ".txt", ".toml"}

# Files that are ignored here ON PURPOSE. Each needs a reason.
EXPECTED_IGNORED = {
    # "skills/foo/local_notes.md": "scratch notes, never shipped",
}


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, cwd=ROOT)


def ignored_source_files():
    """Files that exist under a source dir, look like source, and are ignored by git."""
    out = []
    for d in SOURCE_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in ("__pycache__", "node_modules", ".venv", "extracted")]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() not in SOURCE_EXT:
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                if rel in EXPECTED_IGNORED:
                    continue
                r = sh("git", "check-ignore", "-v", rel)
                if r.returncode == 0 and r.stdout.strip():
                    out.append((rel, r.stdout.strip().split("\t")[0]))
    return out


def untracked_ci_paths():
    """Every `python <path>` a workflow runs must be tracked, not just present on the runner."""
    out = []
    wf = os.path.join(ROOT, ".github", "workflows")
    if not os.path.isdir(wf):
        return out
    pat = re.compile(r"python3?\s+((?:scripts|skills|tests)[\w./-]+\.py)")
    for fn in sorted(os.listdir(wf)):
        if not fn.endswith((".yml", ".yaml")):
            continue
        text = open(os.path.join(wf, fn), encoding="utf-8", errors="ignore").read()
        for m in sorted(set(pat.findall(text))):
            # a workflow may set working-directory, so accept the path from repo root OR
            # from any directory that contains it
            cands = [m] + [os.path.join(d, m) for d in
                           ("skills/slide-maker", "skills/slide-maker/scripts")]
            if not any(sh("git", "ls-files", "--error-unmatch", c).returncode == 0 for c in cands):
                out.append((fn, m))
    return out


def main():
    global ROOT
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0:
        print("error: not a git repository", file=sys.stderr)
        return 2
    ROOT = r.stdout.strip()

    bad = []
    for rel, rule in ignored_source_files():
        bad.append("IGNORED SOURCE FILE  %s\n    matched by %s — it exists on your disk and is "
                   "NOT in the repo. Add a negation (!%s) or narrow the pattern; if it is "
                   "ignored on purpose, add it to EXPECTED_IGNORED with a reason."
                   % (rel, rule, rel))
    for wf, path in untracked_ci_paths():
        bad.append("UNTRACKED CI PATH    %s runs `%s`, which is not tracked by git — the step "
                   "cannot work on a fresh clone." % (wf, path))

    if bad:
        print("%d repo-integrity problem(s):\n" % len(bad))
        for b in bad:
            print("  " + b + "\n")
        return 1
    print("repo integrity ok — no ignored source files, every CI script path is tracked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
