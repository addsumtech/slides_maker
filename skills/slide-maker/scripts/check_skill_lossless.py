#!/usr/bin/env python3
"""Guard a SKILL.md slimming refactor: prove it LAYERED content instead of DELETING it.

A big SKILL.md should shrink by moving prose into `references/*.md` that load on demand.
The failure mode is that "split into references" quietly becomes "rewrite and condense":
the file gets smaller, the PR says "zero information loss", and operational rules are gone.
That regression is invisible in review — the diff is thousands of lines and every removed
line *looks* like it landed somewhere.

So make it mechanical. Every substantive line of the baseline SKILL.md must still be findable,
verbatim, somewhere in the skill tree. Moving a line between files is fine. Reflowing a
paragraph is fine. Changing what it says is not — that shows up here as a missing line, and
has to be justified in the allowlist rather than slipping through.

    # against the merge base, in CI
    python3 scripts/check_skill_lossless.py --baseline main:skills/slide-maker/SKILL.md

    # against a file on disk
    python3 scripts/check_skill_lossless.py --baseline /tmp/SKILL.md.orig

    # show every line that went missing, not just the first 40
    python3 scripts/check_skill_lossless.py --baseline main:... --report missing.md

Exit 0 = every baseline line accounted for. Exit 1 = content was lost; the report names it.

Matching is deliberately forgiving about FORM and strict about SUBSTANCE. Text is NFKC-folded,
em/en dashes and smart quotes are unified, punctuation drops out, case is ignored, and the whole
corpus is joined into one string before matching — so a line may be re-wrapped, re-indented,
moved to another file, or have its bullet marker changed and still pass. What it may not do is
lose a word.

Deliberate deletions are legitimate (a genuinely redundant sentence, a rule superseded by a lint
check). Record them in the allowlist with a reason and they stop failing the build:

    python3 scripts/check_skill_lossless.py --baseline main:... --write-allow allow.json

Allowlist entries key on a hash of the normalized line, so editing the line invalidates its
waiver and it comes back for review. That is the point: a waiver covers one specific sentence
someone actually looked at, not a moving target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# Lines shorter than this after normalization are structural noise — bare list markers, `---`
# rules, lone code-fence lines, one-word headings. They carry no rule that can be lost, and
# checking them produces false failures every time a heading is renamed.
DEFAULT_MIN_CHARS = 25

CORPUS_SUFFIXES = (".md",)
CORPUS_DIRS = (".", "references", "agents")

_DASHES = dict.fromkeys(map(ord, "—–‒―−"), "-")
_QUOTES = {0x2019: "'", 0x2018: "'", 0x201C: '"', 0x201D: '"', ord("`"): "'"}

# Keep alphanumerics and CJK/kana/hangul; everything else (markdown syntax, punctuation, emoji,
# box-drawing) becomes a separator. Dropping CJK would blind the check on the Chinese passages
# this skill carries, and those are exactly where a careless refactor churns wording.
_DROP = re.compile(
    r"[^0-9a-z"
    r"぀-ヿ"      # kana
    r"㐀-䶿"      # CJK ext A
    r"一-鿿"      # CJK unified
    r"가-힯"      # hangul
    r"豈-﫿"      # CJK compatibility ideographs
    r"]+"
)


def normalize(text: str) -> str:
    """Fold away formatting so only word content is compared."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_DASHES).translate(_QUOTES)
    text = text.lower()
    text = _DROP.sub(" ", text)
    return " ".join(text.split())


def line_key(normalized: str) -> str:
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def read_baseline(spec: str, repo: Path) -> str:
    """Accept either `gitref:path/in/repo` or a filesystem path."""
    if ":" in spec and not Path(spec).exists():
        ref, _, path = spec.partition(":")
        out = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=repo, capture_output=True, text=True,
        )
        if out.returncode != 0:
            sys.exit(f"cannot read baseline {spec!r}: {out.stderr.strip()}")
        return out.stdout
    p = Path(spec)
    if not p.exists():
        sys.exit(f"baseline not found: {spec}")
    return p.read_text(encoding="utf-8")


def build_corpus(skill_dir: Path) -> tuple[str, list[Path]]:
    """Everything a skill trigger can eventually reach: SKILL.md + references + agents."""
    files: list[Path] = []
    for sub in CORPUS_DIRS:
        d = skill_dir / sub if sub != "." else skill_dir
        if not d.is_dir():
            continue
        files.extend(sorted(f for f in d.iterdir() if f.suffix in CORPUS_SUFFIXES))
    joined = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in files)
    return normalize(joined), files


def locate(needle: str, skill_dir: Path) -> list[str]:
    """Which files contain this normalized line — for the 'moved to' column."""
    hits = []
    for sub in CORPUS_DIRS:
        d = skill_dir / sub if sub != "." else skill_dir
        if not d.is_dir():
            continue
        for f in sorted(x for x in d.iterdir() if x.suffix in CORPUS_SUFFIXES):
            if needle in normalize(f.read_text(encoding="utf-8", errors="replace")):
                hits.append(str(f.relative_to(skill_dir)))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify a SKILL.md refactor moved content instead of deleting it.",
    )
    ap.add_argument("--baseline", required=True,
                    help="`gitref:path` (e.g. main:skills/slide-maker/SKILL.md) or a file path")
    ap.add_argument("--skill-dir", default=None,
                    help="skill root holding SKILL.md, references/, agents/ (default: this script's parent)")
    ap.add_argument("--repo", default=None,
                    help="git repo to resolve a `gitref:path` baseline against (default: the repo containing this script)")
    ap.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS,
                    help=f"ignore baseline lines shorter than this once normalized (default {DEFAULT_MIN_CHARS})")
    ap.add_argument("--allow", default=None,
                    help="JSON allowlist of deliberately-removed lines")
    ap.add_argument("--write-allow", default=None,
                    help="write every currently-missing line to this JSON file as a waiver stub, then exit 0")
    ap.add_argument("--report", default=None, help="write the full missing-line report to this path")
    ap.add_argument("--quiet", action="store_true", help="print only the verdict line")
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir) if args.skill_dir else Path(__file__).resolve().parent.parent
    skill_dir = skill_dir.resolve()

    # Resolve the git ref against the repo this script lives in, not against --skill-dir: the
    # common comparison is a checked-out baseline versus a tree exported somewhere else entirely.
    def find_repo(start: Path) -> Path | None:
        p = start.resolve()
        while True:
            if (p / ".git").exists():
                return p
            if p == p.parent:
                return None
            p = p.parent

    repo = Path(args.repo).resolve() if args.repo else (
        find_repo(Path(__file__).resolve().parent) or find_repo(skill_dir) or skill_dir
    )

    baseline = read_baseline(args.baseline, repo)
    corpus, files = build_corpus(skill_dir)

    allow: dict[str, str] = {}
    if args.allow and Path(args.allow).exists():
        allow = json.load(open(args.allow, encoding="utf-8")).get("waived", {})

    checked = 0
    missing: list[tuple[int, str, str]] = []   # (lineno, raw, normalized)
    waived = 0
    for n, raw in enumerate(baseline.split("\n"), 1):
        norm = normalize(raw)
        if len(norm) < args.min_chars:
            continue
        checked += 1
        if norm in corpus:
            continue
        if line_key(norm) in allow:
            waived += 1
            continue
        missing.append((n, raw.strip(), norm))

    if args.write_allow:
        # MERGE, never overwrite. The natural thing to type is --write-allow <the live allowlist>,
        # and this used to build a fresh dict and write it: every hand-written REASON accumulated
        # over the skill's history vanished, silently, exit 0. A tool whose whole job is proving
        # content was not deleted must not be the thing that deletes it. Existing reasons win —
        # a stub never overwrites a justification someone already wrote.
        out_path = Path(args.write_allow)
        existing = {}
        comment = ("Each entry waives one baseline line that no longer exists anywhere in the "
                   "skill tree. Replace every REASON with why losing this line is safe. Editing "
                   "the line's wording changes its hash and revokes the waiver.")
        if out_path.exists():
            try:
                prior = json.loads(out_path.read_text(encoding="utf-8"))
                existing = dict(prior.get("waived") or {})
                comment = prior.get("_comment") or comment
            except Exception as e:
                sys.exit(f"{out_path} exists but is not readable JSON ({e}) — "
                         "refusing to overwrite it")
        added = {line_key(nrm): f"REASON REQUIRED (baseline line {n}): {raw[:120]}"
                 for n, raw, nrm in missing if line_key(nrm) not in existing}
        merged = dict(existing)
        merged.update(added)
        out_path.write_text(
            json.dumps({"_comment": comment, "waived": merged}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"added {len(added)} waiver stub(s) to {out_path} "
              f"({len(existing)} existing kept) — fill in every REASON")
        return 0

    pct = 100.0 * len(missing) / checked if checked else 0.0
    verdict = "LOSSLESS" if not missing else "CONTENT LOST"
    summary = (f"{verdict}: {checked - len(missing)}/{checked} baseline lines accounted for "
               f"across {len(files)} files ({pct:.1f}% missing"
               + (f", {waived} waived)" if waived else ")"))

    if not args.quiet and missing:
        print(f"\n{len(missing)} baseline line(s) exist nowhere in the skill tree:\n")
        for n, raw, _ in missing[:40]:
            print(f"  baseline:{n}: {raw[:150]}")
        if len(missing) > 40:
            print(f"  … and {len(missing) - 40} more"
                  + (f" (full list: {args.report})" if args.report else " (use --report to see all)"))
        print("\nMoving these into a references/*.md file fixes it. If a line is genuinely meant to go,")
        print("record it with --write-allow and write down why.\n")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(f"# Lost content report\n\n{summary}\n\nBaseline: `{args.baseline}`\n\n")
            for n, raw, nrm in missing:
                fh.write(f"- **baseline:{n}** `{line_key(nrm)}`\n  > {raw}\n")

    print(summary)
    return 1 if missing else 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
