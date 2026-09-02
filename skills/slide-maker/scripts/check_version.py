#!/usr/bin/env python3
"""check_version — tell the user a newer slide-maker exists. Never do anything else.

Prints ONE line when the installed skill is behind, and NOTHING when it is current.
It never pulls, never checks out, never writes into the skill, and never fails a build: every
error path exits 0 silently, because a version notice that can break someone's deck is worse
than no version notice at all.

WHAT IT *DOES* TOUCH — stated because "never writes" was too broad and a security review read
it as "no side effects at all". On a git checkout it runs `git fetch origin main -q`, which
makes a NETWORK request and updates remote-tracking refs inside `.git` (never the working tree,
never a branch you are on). On a copy install it makes ONE HTTPS request to GitHub for the
VERSION file. Both are rate-limited to once per CACHE_HOURS and both are disabled by
`SLIDE_MAKER_NO_VERSION_CHECK=1`. The git subcommands used are exactly: fetch, remote, rev-list,
rev-parse, status — no pull, merge, checkout, reset or clean anywhere in this file.

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
import hashlib
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
# 🔴 A VERSION STRING CANNOT ANSWER "am I running what main has". It only moves on a RELEASE, so
# every commit between releases is invisible to it — which is exactly the development case.
# Measured: a copy whose SKILL.md had been truncated to 2,000 bytes of 278,400 passed this check
# SILENTLY, because its VERSION still read 5.2.0. In one real session the installed copy was three
# commits behind, this said nothing, and a whole deck was built by a skill that did not contain
# rules the repo had already fixed and pushed. `SKILL.sha256` is committed beside the skill and
# says what main's tree hashes to, so a copy can compare its own content against it.
RAW_FINGERPRINT_URL = (f"https://raw.githubusercontent.com/{REPO}/main/"
                       "skills/slide-maker/SKILL.sha256")
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
    """One cache file PER INSTALL. A single shared file let a symlinked dev checkout and an
    npx copy on the same machine answer for each other — and the wrong one is the dangerous
    one, because the answer feeds a decision about overwriting files."""
    base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    key = hashlib.sha1(str(SKILL_ROOT).encode()).hexdigest()[:12]
    return Path(base) / "slide-maker" / f"version-check-{key}.json"


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
        # A real checkout whose remote is not ours — a fork, a vendored copy, someone's monorepo.
        # Returning None used to fall through to copy_shape(), which would then tell a git
        # working tree to run `npx skills add` and overwrite itself. Stay silent instead.
        return {"shape": "foreign-git", "behind": 0, "dirty": None, "ahead": 0}
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
    # `repo` so the caller can print a real path instead of a literal `<repo>` nobody defines.
    return {"shape": "git", "behind": int(n), "dirty": dirty,
            "ahead": int(ahead) if (ahead or "").isdigit() else 0,
            "repo": _git("rev-parse", "--show-toplevel")}


def copy_shape(local: str | None) -> dict | None:
    """An npx/copied install: compare the local VERSION against the one on GitHub.

    A Claude Code PLUGIN install is also a copy on disk, but its update path is the plugin
    system — telling it `npx skills add` would install a second, competing copy beside it."""
    shape = "plugin" if any("plugins" == part or "plugins" in part
                            for part in SKILL_ROOT.parts[:-2]) else "copy"

    # CONTENT FIRST, and usually the only request: if this tree hashes to what main hashes to,
    # the version necessarily matches too and there is nothing to say. A mismatch is the case
    # VERSION cannot see, so only then is it worth asking what the released version is.
    local_fp = remote_fp = None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from skill_fingerprint import fingerprint as _fp
        local_fp = _fp()
        req = urllib.request.Request(RAW_FINGERPRINT_URL,
                                     headers={"User-Agent": "slide-maker-version-check"})
        with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as r:
            remote_fp = r.read().decode("ascii", "replace").split()[0].strip()
    except Exception:
        local_fp = remote_fp = None      # any failure here falls back to the VERSION compare
    if local_fp and remote_fp and local_fp == remote_fp:
        return {"shape": shape, "local": local, "remote": local, "dirty": None, "behind": 0,
                "drift": None, "fingerprint": local_fp}

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
    version_behind = 1 if (lv is None or lv < rv) else 0
    # Same released version, different tree = work landed on main since the last release. That is
    # the state this check was blind to, and it is the state a developer is in most of the time.
    content_drift = bool(local_fp and remote_fp and local_fp != remote_fp)
    return {"shape": shape, "local": local, "remote": remote, "dirty": None,
            "behind": 1 if (version_behind or content_drift) else 0,
            "drift": "version" if version_behind else ("content" if content_drift else None),
            "fingerprint": local_fp}


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
        kind = "plugin install" if res.get("shape") == "plugin" else "copied install"
        return f" · local edits: unknown ({kind} has no baseline to diff against)"
    ahead = res.get("ahead") or 0
    if d:
        extra = f" and {ahead} unpushed commit{'s' if ahead != 1 else ''}" if ahead else ""
        return f" · 🔴 you have {d} uncommitted change{'s' if d != 1 else ''}{extra} here"
    # An `ahead` count on a CLEAN tree still means a plain pull is not the whole story.
    if ahead:
        return f" · working tree clean, but {ahead} unpushed commit{'s' if ahead != 1 else ''}"
    return " · working tree clean"


def notice(res: dict) -> str | None:
    if not res or not res.get("behind"):
        return None
    if res.get("shape") == "foreign-git":
        return None          # not our remote — we have no standing to tell it anything
    if res.get("shape") == "git":
        n = res["behind"]
        return (f"slide-maker is {n} commit{'s' if n != 1 else ''} behind "
                f"{REPO}@main{local_work(res)}")
    if res.get("drift") == "content":
        # Direction is genuinely unknowable from a hash, so the wording does not claim one — and
        # it names local edits, because on a copied install those are the other way to get here.
        return (f"slide-maker's installed copy DIFFERS from {REPO}@main at the same version "
                f"({res.get('local') or 'unknown'}) — it is not running what main has. Commits "
                f"land between releases, so VERSION cannot see this. (Local edits to the "
                f"installed copy look the same from here.)")
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
    # 🔴 Only the REMOTE fact is cacheable. `dirty`/`ahead`/`behind` are local git reads that
    # cost ~10ms and change whenever the user touches a file — caching them for 24h means the
    # update prompt can be told "working tree clean" about a tree edited an hour ago, which is
    # precisely the reading this feature exists to get right. Local state is recomputed every run.
    res = git_shape()
    if res is None:
        res = None if a.force else read_cache()
        if res is None:
            res = copy_shape(local)
            if res is not None:
                write_cache(res)

    if res is None and a.json:
        print(json.dumps({"shape": None, "local": local})); return 0
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
