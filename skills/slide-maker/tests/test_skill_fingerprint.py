#!/usr/bin/env python3
"""A COPIED install must be able to tell it is not running what main has.

The comparison is git BLOB SHAs fetched from GitHub's trees API — nothing is generated into the
repo, so there is no artifact to keep fresh and none to go stale. It is deliberately ONE-
DIRECTIONAL (does everything I HAVE match main?), because an installer chooses what to copy:
`npx skills add` lands ~55 files where the tree has ~193, and demanding an exact set would report
"differs" on every correct install forever.

🔴 THE MEASURED DEFECT. `check_version.py` on a copy install compared `VERSION` against the one on
GitHub. `VERSION` only moves on a RELEASE, so every commit between releases — the development case,
which is most of the time — was invisible. Tested directly before this file existed: a copy whose
`SKILL.md` had been truncated to 2,000 bytes of 278,400 (99.3% of the skill gone) passed
`check_version.py --force` SILENTLY with exit 0, because its VERSION still read `5.2.0`. The real
cost, in one session: the installed copy was three commits behind, the check said nothing, and a
deck was built by a skill that did not contain rules the repo had already fixed and pushed.

A version string cannot answer "am I on main". A content fingerprint can, without hooking an
installer we do not own.
"""
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
warnings.simplefilter("ignore")

import skill_fingerprint as sf              # noqa: E402
import check_version as cv                  # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


# ---------------------------------------------------------------- blob SHAs, not a tree hash
import subprocess as _sp                                                          # noqa: E402

repo_file = ROOT / "VERSION"
git_sha = _sp.run(["git", "hash-object", str(repo_file)], capture_output=True, text=True,
                  cwd=str(ROOT)).stdout.strip()
check(git_sha and sf.blob_sha(repo_file) == git_sha,
      "🔴 `blob_sha` equals what `git hash-object` produces — the whole approach rests on it, "
      "because it lets a copy with no git compute the same identity GitHub already stores")

tmp = Path(tempfile.mkdtemp(prefix="fp-"))
tree = tmp / "skill"
(tree / "scripts").mkdir(parents=True)
(tree / "SKILL.md").write_text("rule one\n", encoding="utf-8")
(tree / "scripts" / "a.py").write_text("print(1)\n", encoding="utf-8")
(tree / "scripts" / "__pycache__").mkdir()
(tree / "scripts" / "__pycache__" / "a.cpython-313.pyc").write_bytes(b"\x00")
(tree / ".DS_Store").write_bytes(b"\x00")

blobs = sf.local_blobs(tree)
check(set(blobs) == {"SKILL.md", "scripts/a.py"},
      "🔴 caches and OS turds are pruned — they differ between two identical installs, so "
      "comparing them would report a difference that is not one (got {})".format(sorted(blobs)))

before = dict(blobs)
(tree / "SKILL.md").write_text("rule one\nrule two\n", encoding="utf-8")
check(sf.local_blobs(tree)["SKILL.md"] != before["SKILL.md"],
      "a CONTENT change moves that file's sha — the case VERSION is blind to, since a commit "
      "between releases leaves the version string untouched")


# ----------------------------------------------- the comparison is SUBSET-aware, on purpose
real_remote = sf.remote_blobs
sf.remote_blobs = lambda: dict(before, **{"only/on/main.md": "0" * 40})
matches, differing = sf.compare(tree)
sf.remote_blobs = real_remote
check(matches is False and differing == ["SKILL.md"],
      "🔴 a file whose content differs is reported")
check("only/on/main.md" not in differing,
      "🔴 ...and a file main has that this copy does NOT is IGNORED — `npx skills add` lands ~55 "
      "files where the tree has ~193, so demanding an exact set would report 'differs' on every "
      "correct install forever")

sf.remote_blobs = lambda: dict(sf.local_blobs(tree))
matches, differing = sf.compare(tree)
sf.remote_blobs = real_remote
check(matches is True and differing == [],
      "...and a copy whose every file matches main is reported current")

sf.remote_blobs = lambda: None
matches, differing = sf.compare(tree)
sf.remote_blobs = real_remote
check(matches is None,
      "🔴 unavailable is NOT 'current' — offline/rate-limited/truncated returns None, and every "
      "caller says nothing, so this can never be the reason a deck did not get built")

# ------------------------------------- copy_shape: CONTENT first, VERSION only when it differs
class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


real_open = cv.urllib.request.urlopen
real_compare = sf.compare


def _version_server(body, calls):
    def _open(req, timeout=None):
        calls.append(req.full_url if hasattr(req, "full_url") else str(req))
        if body is None:
            raise OSError("simulated network failure")
        return _Resp(body.encode())
    return _open


calls = []
sf.compare = lambda *a, **k: (True, [])
cv.urllib.request.urlopen = _version_server("5.2.0", calls)
res = cv.copy_shape("5.2.0")
sf.compare, cv.urllib.request.urlopen = real_compare, real_open
check(res and res.get("behind") == 0 and res.get("drift") is None,
      "a copy whose every file matches main is reported CURRENT")
check(not calls,
      "🔴 ...without fetching VERSION at all — if the CONTENT agrees the version necessarily does, "
      "so the common case costs one API call and no second request ({} extra)".format(len(calls)))

calls = []
sf.compare = lambda *a, **k: (False, ["scripts/deckkit.py", "SKILL.md", "a.md", "b.md"])
cv.urllib.request.urlopen = _version_server("5.2.0", calls)
res = cv.copy_shape("5.2.0")
sf.compare, cv.urllib.request.urlopen = real_compare, real_open
check(res and res.get("behind") == 1 and res.get("drift") == "content",
      "🔴 a copy at the SAME released version but different content is reported BEHIND — the exact "
      "state that used to pass silently, and the one a developer is in between releases")
msg = cv.notice(res) or ""
check("DIFFERS" in msg and "VERSION cannot see this" in msg,
      "...and the notice says what happened rather than 'a new version is available', which would "
      "be false: the version is identical")
check("scripts/deckkit.py" in msg and "and 1 more" in msg,
      "...and it NAMES the files, capped — a bare 'differs' leaves the reader no way to judge "
      "whether it matters ({})".format(msg[-90:]))
check("Local edits" in msg,
      "...and names local edits as the other way to reach this state, because a hash cannot tell "
      "direction and claiming one would be a guess")

calls = []
sf.compare = lambda *a, **k: (None, [])
cv.urllib.request.urlopen = _version_server("5.3.0", calls)
res = cv.copy_shape("5.2.0")
sf.compare, cv.urllib.request.urlopen = real_compare, real_open
check(res and res.get("behind") == 1 and res.get("drift") == "version",
      "🔴 when the content comparison is UNAVAILABLE the check falls back to the old VERSION "
      "compare rather than going quiet — a new capability must not remove the one that worked")

calls = []
sf.compare = lambda *a, **k: (None, [])
cv.urllib.request.urlopen = _version_server(None, calls)
res = cv.copy_shape("5.2.0")
sf.compare, cv.urllib.request.urlopen = real_compare, real_open
check(res is None,
      "...and with BOTH unavailable it returns None — offline stays silent by design, so this can "
      "never be the reason a deck did not get built")

check(not (ROOT / "SKILL.sha256").exists(),
      "🔴 and NOTHING is generated into the repo: no committed artifact means none to regenerate "
      "on every commit, none to conflict on every merge, and none to silently go stale")

shutil.rmtree(tmp, ignore_errors=True)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
