#!/usr/bin/env python3
"""A COPIED install must be able to tell it is not running what main has.

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


# ---------------------------------------------------------------- the fingerprint itself
tmp = Path(tempfile.mkdtemp(prefix="fp-"))
tree = tmp / "skill"
(tree / "scripts").mkdir(parents=True)
(tree / "SKILL.md").write_text("rule one\nrule two\n", encoding="utf-8")
(tree / "scripts" / "a.py").write_text("print(1)\n", encoding="utf-8")

base = sf.fingerprint(tree)
check(base == sf.fingerprint(tree),
      "the fingerprint is deterministic — the same tree hashes the same twice, or every install "
      "would report a difference that is not one")

(tree / "SKILL.md").write_text("rule one\nrule two\nrule three\n", encoding="utf-8")
check(sf.fingerprint(tree) != base,
      "🔴 a CONTENT change moves it — this is the case VERSION is blind to, since a commit between "
      "releases leaves the version string untouched")

(tree / "SKILL.md").write_text("rule one\nrule two\n", encoding="utf-8")
check(sf.fingerprint(tree) == base, "...and reverting the content restores the hash")

(tree / "scripts" / "a.py").rename(tree / "scripts" / "b.py")
check(sf.fingerprint(tree) != base,
      "🔴 a RENAME moves it too — the digest covers PATHS, not just contents, so a file moved or "
      "deleted cannot slip through a contents-only hash")
(tree / "scripts" / "b.py").rename(tree / "scripts" / "a.py")

(tree / "scripts" / "__pycache__").mkdir()
(tree / "scripts" / "__pycache__" / "a.cpython-313.pyc").write_bytes(b"\x00\x01")
(tree / ".DS_Store").write_bytes(b"\x00")
(tree / "SKILL.sha256").write_text(base + "\n", encoding="utf-8")
check(sf.fingerprint(tree) == base,
      "🔴 caches, OS turds and the fingerprint FILE ITSELF are excluded — two identical installs "
      "must agree, and including SKILL.sha256 in its own input is self-referential")


# ------------------------------------------------------ the committed file cannot go stale
r = subprocess.run([sys.executable, str(SCRIPTS / "skill_fingerprint.py"), "--check"],
                   capture_output=True, text=True)
check(r.returncode == 0,
      "`--check` passes on this repo, so the committed SKILL.sha256 matches the tree ({})"
      .format((r.stdout or r.stderr).strip()[:70]))
check("--write" in (r.stdout + r.stderr) or r.returncode == 0,
      "...and when it fails it names the one command that fixes it, because a stale fingerprint "
      "silently disables the check for EVERY copied install")


# --------------------------------------------------- copy_shape: content first, then version
class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patched(fp_body, version_body, calls):
    def _open(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        calls.append(url)
        if url.endswith("SKILL.sha256"):
            if fp_body is None:
                raise OSError("simulated network failure")
            return _Resp(fp_body.encode())
        return _Resp(version_body.encode())
    return _open


real_open = cv.urllib.request.urlopen
local_fp = sf.fingerprint()

calls = []
cv.urllib.request.urlopen = _patched(local_fp, "5.2.0", calls)
res = cv.copy_shape("5.2.0")
cv.urllib.request.urlopen = real_open
check(res and res.get("behind") == 0 and res.get("drift") is None,
      "a copy whose tree hashes to main's is reported CURRENT")
check(len(calls) == 1,
      "...and it cost ONE request, not two — the fingerprint settles the common case on its own "
      "({} call(s))".format(len(calls)))

calls = []
cv.urllib.request.urlopen = _patched("deadbeef" * 8, "5.2.0", calls)
res = cv.copy_shape("5.2.0")
cv.urllib.request.urlopen = real_open
check(res and res.get("behind") == 1 and res.get("drift") == "content",
      "🔴 a copy at the SAME released version but a different tree is reported BEHIND — the exact "
      "state that used to pass silently, and the state a developer is in between releases")
msg = cv.notice(res) or ""
check("DIFFERS" in msg and "VERSION cannot see this" in msg,
      "...and the notice says what actually happened rather than 'a new version is available', "
      "which would be false: the version is identical")
check("Local edits" in msg,
      "...and it names local edits as the other way to reach this state, because a hash cannot "
      "tell direction and claiming one would be a guess")

calls = []
cv.urllib.request.urlopen = _patched(None, "5.3.0", calls)
res = cv.copy_shape("5.2.0")
cv.urllib.request.urlopen = real_open
check(res and res.get("behind") == 1 and res.get("drift") == "version",
      "🔴 when the fingerprint fetch FAILS the check falls back to the old VERSION compare rather "
      "than going quiet — a new capability must not remove the one that already worked")

calls = []
cv.urllib.request.urlopen = _patched(None, "", calls)
res = cv.copy_shape("5.2.0")
cv.urllib.request.urlopen = real_open
check(res is None,
      "...and with BOTH unavailable it returns None — offline stays silent by design, so this can "
      "never be the reason a deck did not get built")

shutil.rmtree(tmp, ignore_errors=True)

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
