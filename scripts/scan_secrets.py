#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_secrets.py — credential scan that discriminates by SHAPE, not by prefix.

Why this exists: generic scanners match `sk-` as a prefix and flag this repository every time,
because the direction-gate preview page names its CSS classes after slide SKELETONS —
`sk-body`, `sk-split`, `sk-island`, `sk-band`, `sk-rail`, `sk-statement`. Those are four to nine
lowercase letters. A real OpenAI key is `sk-` followed by ~48 high-entropy characters. The two are
trivially separable by length and entropy, so a prefix match produces a report that costs a human
an afternoon to dismiss and teaches everyone to ignore the scanner — which is the expensive
failure, not the false positive itself.

So every rule here carries a minimum length AND a Shannon-entropy floor over the candidate's
variable part. A finding means the string is long enough and disordered enough to be a real
credential, not that it starts with the right letters.

    python3 scripts/scan_secrets.py              # working tree (tracked files only)
    python3 scripts/scan_secrets.py --history    # every blob in every commit, all branches
    python3 scripts/scan_secrets.py --selftest   # prove it catches real shapes and ignores ours

Exit 0 = clean · 1 = findings (never prints the matched secret, only its location and a masked
head) · 2 = could not run.

Findings are printed as `path:line  RULE  sk-abcd…<redacted, 51 chars, entropy 4.9>` — enough to
locate and revoke, never enough to leak. A scanner that echoes the credential it found has
published it into your CI logs.
"""
import argparse
import math
import os
import re
import subprocess
import sys

# name, regex (the variable part MUST be group 1), min length of group 1, min entropy of group 1
RULES = [
    ("openai",        re.compile(r"\bsk-(?:proj-)?([A-Za-z0-9_-]{20,})"),      32, 3.6),
    ("anthropic",     re.compile(r"\bsk-ant-(?:api\d\d-)?([A-Za-z0-9_-]{20,})"), 32, 3.6),
    ("github-pat",    re.compile(r"\bgh[pousr]_([A-Za-z0-9]{30,})"),           36, 3.6),
    ("github-fine",   re.compile(r"\bgithub_pat_([A-Za-z0-9_]{50,})"),         50, 3.6),
    ("aws-akid",      re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),                   20, 2.8),
    ("gcp",           re.compile(r"\b(AIza[0-9A-Za-z_-]{35})\b"),              39, 3.4),
    ("slack",         re.compile(r"\bxox[baprs]-([A-Za-z0-9-]{20,})"),         24, 3.2),
    ("private-key",   re.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----)"), 27, 0.0),
    ("generic-assign", re.compile(
        r"(?i)(?:api[_-]?key|secret|token|passwd|password)\s*[:=]\s*['\"]([A-Za-z0-9_\-/+=]{24,})['\"]"),
     24, 4.0),
]

# Literals that are placeholders by construction. Kept deliberately short: an allowlist is a hole,
# so it may only ever hold strings that could not be a credential.
BENIGN = re.compile(
    r"(?i)^(?:x{4,}|\.{3,}|<[^>]+>|\$\{?[A-Za-z_]+\}?|your[_-]?\w+|dummy\w*|example\w*|"
    r"replace[_-]?\w*|placeholder\w*|redacted\w*|test[_-]?\w*|fake\w*|changeme\w*)$")

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "extracted"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".pptx", ".docx", ".xlsx",
            ".zip", ".gz", ".woff", ".woff2", ".ttf", ".otf", ".ico", ".mp4", ".db"}


def entropy(s):
    """Shannon entropy in bits per character. A real key sits near 4.5-6; an English word near 3."""
    if not s:
        return 0.0
    n = len(s)
    return -sum((c / n) * math.log2(c / n)
                for c in {ch: s.count(ch) for ch in set(s)}.values())


def mask(raw, var):
    head = raw[:max(0, len(raw) - len(var)) + 4]
    return "%s…<redacted, %d chars, entropy %.1f>" % (head, len(var), entropy(var))


def scan_text(text, where, out):
    for lineno, line in enumerate(text.splitlines(), 1):
        if len(line) > 4000:            # minified asset — not where secrets hide, and it is noise
            continue
        for name, rx, min_len, min_ent in RULES:
            for m in rx.finditer(line):
                var = m.group(1)
                if len(var) < min_len or BENIGN.match(var) or entropy(var) < min_ent:
                    continue
                out.append((where, lineno, name, mask(m.group(0), var)))


def tracked_files(root):
    try:
        r = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return [os.path.join(root, p) for p in r.stdout.splitlines()]
    except Exception:
        pass
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        paths += [os.path.join(dirpath, f) for f in filenames]
    return paths


def scan_tree(root):
    out = []
    for p in tracked_files(root):
        if os.path.splitext(p)[1].lower() in SKIP_EXT or not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                scan_text(fh.read(), os.path.relpath(p, root), out)
        except Exception:
            continue
    return out


def scan_history(root):
    """Every blob reachable from every ref — a key deleted in a later commit is still leaked."""
    out = []
    r = subprocess.run(["git", "-C", root, "rev-list", "--all", "--objects"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("error: not a git repository", file=sys.stderr)
        sys.exit(2)
    blobs = []
    for ln in r.stdout.splitlines():
        parts = ln.split(" ", 1)
        if len(parts) == 2 and os.path.splitext(parts[1])[1].lower() not in SKIP_EXT:
            blobs.append((parts[0], parts[1]))
    print("scanning %d historical blobs…" % len(blobs), file=sys.stderr)
    for sha, path in blobs:
        c = subprocess.run(["git", "-C", root, "cat-file", "-p", sha],
                           capture_output=True)
        if c.returncode == 0:
            scan_text(c.stdout.decode("utf-8", "ignore"), "history:%s" % path, out)
    return out


def _selftest():
    """Prove BOTH directions: real shapes are caught, and this repo's own strings are not."""
    must_catch = [
        "sk-" + "aB3xK9mQ7pL2wR5tY8nJ4vH6cF1dG0zS" * 1 + "eXtRaPaDdInG12",
        "ghp_" + "aB3xK9mQ7pL2wR5tY8nJ4vH6cF1dG0zS9qWm",
        "AKIA" + "3XZQ7MNP2LRTYW5V",
        # Assembled at runtime, like the three above: a scanner whose own source contains a
        # matching literal reports itself forever. This was invisible until the file became
        # TRACKED — `tracked_files()` reads `git ls-files`, so while .gitignore was swallowing
        # this script it was never in its own scan. Fixing the tracking bug exposed this one.
        "-----BEGIN " + "RSA " + "PRIVATE KEY-----",
        "api" + '_key = "' + "aB3xK9mQ7pL2wR5tY8nJ4vH6cF1dG0zS" + '"',
    ]
    must_ignore = [
        '<div class="slide sk-statement">', '.sk-body{position:relative}',
        '"sk-" + spec["skeleton"]', 'sk-split .sp-l{width:58%}', 'sk-island .mini-fig{}',
        'export OPENAI_API_KEY="$(cat ~/.openai_key)"',
        'export OPENAI_API_KEY="sk-..."', 'api_key = "your_api_key_here"',
        'token: "REPLACE_ME_AT_RUNTIME_XXXXXXXXXX"', 'password = "xxxxxxxxxxxxxxxxxxxxxxxxxxx"',
    ]
    bad = []
    for s in must_catch:
        out = []
        scan_text(s, "t", out)
        if not out:
            bad.append("MISSED a real shape: %s…" % s[:14])
    for s in must_ignore:
        out = []
        scan_text(s, "t", out)
        if out:
            bad.append("FALSE POSITIVE on: %s" % s[:60])
    if bad:
        for b in bad:
            print("  ✗ " + b, file=sys.stderr)
        return 1
    print("selftest ok — %d real shapes caught, %d benign strings ignored "
          "(including this repo's sk-* CSS skeleton classes)" % (len(must_catch), len(must_ignore)))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--history", action="store_true",
                    help="scan every blob in every commit, not just the working tree")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    hits = scan_history(a.root) if a.history else scan_tree(a.root)
    if not hits:
        print("clean — no string matched a credential SHAPE (length + entropy), %s"
              % ("full history" if a.history else "working tree"))
        return 0
    print("%d possible credential(s) — locations only, values never printed:" % len(hits))
    for where, lineno, name, masked in hits:
        print("  %s:%s  %s  %s" % (where, lineno, name, masked))
    print("\nIf any is real: revoke it FIRST (it is in the history and cannot be un-published by "
          "a later commit), then rewrite history.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
