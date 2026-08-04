#!/usr/bin/env python3
"""check_version — tell the user a newer slide-maker exists. Never do anything else.

Prints ONE line when the installed skill is behind, and NOTHING when it is current.
It never pulls, never writes into the skill, and never fails a build: every error path
exits 0 silently, because a version notice that can break someone's deck is worse than
no version notice at all.

TWO INSTALL SHAPES, and they need different questions asked
-----------------------------------------------------------
  git checkout / symlink   a .git exists above the skill  -> ask git how many commits behind
  npx skills add (a COPY)  no .git, no CHANGELOG           -> ask GitHub for the VERSION file

The second shape is why `skills/slide-maker/VERSION` exists. CHANGELOG.md lives at the
REPO ROOT, which `npx skills add` does not copy — so a copy install used to have literally
nothing on disk saying which version it was. The marker has to live inside the installed
directory or this check cannot exist for the majority of users.

COST
----
One network call at most once per CACHE_HOURS. Every other invocation reads a small JSON
cache and returns in ~5ms. That is what makes it safe to call on every run.

OPT OUT
-------
    export SLIDE_MAKER_NO_VERSION_CHECK=1

USAGE
    python3 scripts/check_version.py           # silent unless behind
    python3 scripts/check_version.py --verbose # always print what it found (troubleshooting)
    python3 scripts/check_version.py --force   # ignore the cache
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "addsumtech/slides_maker"
RAW_VERSION_URL = f"https://raw.githubusercontent.com/{REPO}/main/skills/slide-maker/VERSION"
CACHE_HOURS = 24
NET_TIMEOUT = 6          # seconds; a slow network must not make a deck slow to start
GIT_TIMEOUT = 8

SKILL_ROOT = Path(__file__).resolve().parent.parent


# ── local version ──────────────────────────────────────────────────────────────────────

def local_version() -> str | None:
    """The installed version, from the VERSION file that ships INSIDE the skill."""
    f = SKILL_ROOT / "VERSION"
    if f.is_file():
        v = f.read_text(encoding="utf-8", errors="replace").strip()
        if v:
            return v
    # A git checkout made before VERSION existed can still answer from the repo CHANGELOG.
    ch = SKILL_ROOT.parent.parent / "CHANGELOG.md"
    if ch.is_file():
        m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", ch.read_text(encoding="utf-8",
                                                                 errors="replace"), re.M)
        if m:
            return m.group(1)
    return None


def _semver(v: str) -> tuple[int, ...] | None:
    m = re.match(r"^\s*v?(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(g) for g in m.groups()) if m else None


# ── cache ──────────────────────────────────────────────────────────────────────────────

def cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(base) / "slide-maker" / "version-check.json"


def read_cache() -> dict | None:
    try:
        d = json.loads(cache_path().read_text(encoding="utf-8"))
        if time.time() - float(d.get("at", 0)) < CACHE_HOURS * 3600:
            return d
    except Exception:
        pass
    return None


def write_cache(d: dict) -> None:
    try:
        p = cache_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        d = dict(d, at=time.time())
        p.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass          # a cache we cannot write is a slower check, never a failed one


# ── the two shapes ─────────────────────────────────────────────────────────────────────

def _git(*args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(SKILL_ROOT), *args],
                           capture_output=True, text=True, timeout=GIT_TIMEOUT)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        # subprocess.run's own timeout= is used deliberately: macOS has no `timeout` binary,
        # so shelling out to one would fail on the single most common platform.
        return None


def git_shape() -> dict | None:
    """A git checkout (including the symlink-into-a-repo install).

    Reports commits behind AND whether the working tree carries local work, because those are
    two different situations for the user: "you are behind" invites a pull, while "you are
    behind AND you have edited this" must never invite one silently. The second number is the
    only fact the update prompt's third option can stand on."""
    if _git("rev-parse", "--git-dir") is None:
        return None
    remotes = _git("remote", "-v") or ""
    if "slides_maker" not in remotes:
        return None          # someone else's repo happens to contain the skill — not ours to judge
    branch = "origin/main"
    if _git("fetch", "origin", "main", "-q") is None:
        # offline, or no permission to fetch. Fall back to whatever ref we already have.
        pass
    n = _git("rev-list", "--count", f"HEAD..{branch}")
    if n is None or not n.isdigit():
        return None
    porcelain = _git("status", "--porcelain") or ""
    dirty = len([l for l in porcelain.splitlines() if l.strip()])
    ahead = _git("rev-list", "--count", f"{branch}..HEAD")
    return {"shape": "git", "behind": int(n), "dirty": dirty,
            "ahead": int(ahead) if (ahead or "").isdigit() else 0}


def copy_shape(local: str | None) -> dict | None:
    """An npx/copied install: compare the local VERSION against the one on GitHub."""
    try:
        req = urllib.request.Request(RAW_VERSION_URL,
                                     headers={"User-Agent": "slide-maker-version-check"})
        with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as r:
            remote = r.read().decode("utf-8", "replace").strip()
    except Exception:
        return None          # offline, rate-limited, DNS down — all silent by design
    lv, rv = _semver(local or ""), _semver(remote)
    if not rv:
        return None
    # `dirty: None` is deliberate and is NOT the same as 0. A copied install has no baseline to
    # diff against, so whether the user edited it is genuinely unknowable here — and the update
    # prompt must say "I cannot tell" rather than "you have no local changes", which would be a
    # claim that quietly licenses overwriting someone's work.
    return {"shape": "copy", "local": local, "remote": remote, "dirty": None,
            "behind": 1 if (lv is None or lv < rv) else 0}


# ── report ─────────────────────────────────────────────────────────────────────────────

def local_work(res: dict) -> str:
    """The clause that decides whether an update is a one-liner or a conversation.

    Three distinct states, and collapsing any two of them loses the thing that matters:
      dirty > 0   the user has edited this checkout — a pull is NOT a safe default
      dirty == 0  clean; updating costs them nothing
      dirty None  a copied install; genuinely unknowable, and saying "clean" would be a lie
    """
    d = res.get("dirty")
    if d is None:
        return " · local edits: unknown (copied install has no baseline to diff against)"
    if d:
        ahead = res.get("ahead") or 0
        extra = f" + {ahead} unpushed commit{'s' if ahead != 1 else ''}" if ahead else ""
        return f" · 🔴 you have {d} uncommitted change{'s' if d != 1 else ''}{extra} here"
    return " · working tree clean"


def notice(res: dict) -> str | None:
    if not res or not res.get("behind"):
        return None
    if res.get("shape") == "git":
        n = res["behind"]
        return (f"slide-maker is {n} commit{'s' if n != 1 else ''} behind "
                f"{REPO}@main{local_work(res)}")
    return (f"slide-maker {res.get('remote')} is available "
            f"(installed: {res.get('local') or 'unknown'}){local_work(res)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Tell the user if a newer slide-maker exists.")
    ap.add_argument("--verbose", action="store_true", help="print the result even when current")
    ap.add_argument("--force", action="store_true", help="ignore the cache")
    ap.add_argument("--json", action="store_true",
                    help="emit the raw result so a caller can build the update prompt")
    a = ap.parse_args()

    if os.environ.get("SLIDE_MAKER_NO_VERSION_CHECK"):
        if a.verbose:
            print("version check: disabled via SLIDE_MAKER_NO_VERSION_CHECK")
        return 0

    local = local_version()
    res = None if a.force else read_cache()
    if res is None:
        res = git_shape() or copy_shape(local)
        if res is not None:
            write_cache(res)

    if res is None:
        if a.verbose:
            print(f"version check: could not determine (installed: {local or 'unknown'}) — "
                  "offline, or no VERSION marker")
        return 0

    if a.json:
        print(json.dumps(res)); return 0
    line = notice(res)
    if line:
        print(line)
    elif a.verbose:
        print(f"version check: up to date (installed: {local or 'unknown'}, "
              f"shape: {res.get('shape')})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # 🔴 The whole point: this script may never be the reason a deck did not get built.
        sys.exit(0)
