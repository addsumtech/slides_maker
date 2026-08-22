#!/usr/bin/env python3
"""Install slide-maker into every terminal-agent skill directory on this machine.

Run from anywhere:
    python3 scripts/install_skill.py --target all

This copies the current skill folder into:
    ~/.codex/skills/slide-maker     (Codex)
    ~/.claude/skills/slide-maker    (Claude Code)
    ~/.agents/skills/slide-maker    (the host-neutral root `npx skills add` installs into —
                                     Coze CLI and other non-Claude agents read it)

WHY `agents` IS IN THIS LIST
----------------------------
It was not, and the copy there went a whole major version stale in the dark. Measured on one
machine: `~/.agents/skills/slide-maker` sat at 4.9.0 while codex/claude/repo were all at 5.0.0 —
missing `design-by-topic.md`, `bespoke-registers.md` and `written_reason.py`, i.e. the entire
5.0.0 topic-adapted look selection, with `style_pick` appearing ZERO times in its SKILL.md while
the current `render_deck.py --gate-check` requires that field.

`check_version.py` was not broken — run inside the stale copy it correctly printed
"5.0.0 is available (installed: 4.9.0)". The notice went out and nothing could act on it,
because `--target` only accepted {codex, claude, both} and `both` meant the two that were
already current. **A refresh path that cannot reach an install target is the same as no notice
at all**, which is why the target list lives here rather than in a README sentence.

`all` installs into every root whose HOST directory already exists, so it never litters
`~/.agents` onto a machine that does not use that channel; naming a target explicitly always
creates it. Skipped roots are printed with the reason — a silent skip is how this drifted.

NOTE for the `agents` root: `npx skills add` keeps its own `~/.agents/.skill-lock.json` with a
`skillFolderHash`. Copying files under it does not update that hash, so `npx skills` may report
the folder as locally modified until you re-run `npx skills add addsumtech/slides_maker`. The
files on disk — which is what the agent actually reads — are correct either way.
"""
import argparse
import fnmatch
import os
import shutil
from pathlib import Path


SKILL_NAME = "slide-maker"
# The root that is correct for a runtime we cannot identify — and therefore the fallback when
# NO host directory exists yet. Kept as a name, not a literal, so the two places that mean
# "the host-neutral one" cannot drift apart.
HOST_NEUTRAL = "agents"
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDE_FILES = {
    ".DS_Store",
}
EXCLUDE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.tmp",
]


def source_root():
    return Path(__file__).resolve().parents[1]


def target_roots():
    home = Path.home()
    return {
        "codex": home / ".codex" / "skills" / SKILL_NAME,
        "claude": home / ".claude" / "skills" / SKILL_NAME,
        # The host-neutral root. `npx skills add` installs here, and non-Claude agents
        # (Coze CLI and friends) read it. Left out of this map once; see the module docstring.
        "agents": home / ".agents" / "skills" / SKILL_NAME,
    }


def host_dir(name):
    """The runtime's OWN directory — the thing whose existence means 'this host is in use'.

    `all` keys off this rather than off the installed skill, so a machine that uses a runtime
    but has never installed this skill still gets it, and a machine that does not use the
    runtime does not grow an empty tree for it.
    """
    return target_roots()[name].parent.parent


def should_skip(path):
    name = path.name
    if path.is_dir() and name in EXCLUDE_DIRS:
        return True
    if path.is_file() and name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_PATTERNS)


def iter_files(src):
    for root, dirs, files in os.walk(src):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_skip(root_path / d)]
        for filename in files:
            path = root_path / filename
            if not should_skip(path):
                yield path


def copy_skill(src, dest, *, dry_run=False, replace=False):
    if src.resolve() == dest.resolve():
        # A symlinked install (the usual dev setup for ~/.codex) resolves to the source itself.
        # Nothing is copied and nothing needs to be: it is always current by construction.
        # Returning None rather than a file count keeps the caller from reporting "installed N
        # files" for a copy that did not happen — the drift this script exists to surface is the
        # one thing its own output must not fake.
        print(f"skip {dest}: symlink/alias to the source — already current by construction")
        return None
    # List source files BEFORE any rmtree, so a misconfigured path can never wipe
    # the source out from under us.
    files = list(iter_files(src))
    if replace and dest.exists():
        if dry_run:
            print(f"would remove existing {dest}")
        else:
            shutil.rmtree(dest)
    if dry_run:
        print(f"would copy {len(files)} files -> {dest}")
        return len(files)

    dest.mkdir(parents=True, exist_ok=True)
    for path in files:
        rel = path.relative_to(src)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
    return len(files)


def validate_install(dest):
    required = [
        "SKILL.md",
        "scripts/deckkit.py",
        "scripts/check_env.py",
        "references/design-principles.md",
    ]
    missing = [rel for rel in required if not (dest / rel).exists()]
    if missing:
        return False, missing
    return True, []


def main():
    ap = argparse.ArgumentParser(description="Install slide-maker for terminal agent runtimes.")
    ap.add_argument(
        "--target",
        choices=["codex", "claude", "agents", "all", "both"],
        default="all",
        help="Which skill directory to install into. 'all' (default) covers every runtime "
             "whose host directory exists. 'both' is the old name for codex+claude and is "
             "kept working, but it is what let the 'agents' root go stale — it now installs "
             "everywhere and says so.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Show what would be copied.")
    ap.add_argument(
        "--replace",
        action="store_true",
        help="Remove the existing installed skill directory before copying.",
    )
    args = ap.parse_args()

    src = source_root()
    if not (src / "SKILL.md").exists():
        raise SystemExit(f"could not find SKILL.md at {src}")

    roots = target_roots()
    if args.target in ("all", "both"):
        if args.target == "both":
            print("note: --target both now means ALL runtimes (codex · claude · agents). "
                  "The two-runtime meaning is what let the host-neutral root go a major "
                  "version stale; use --target all, or name one runtime.")
        # Capability, not a hardcoded pair: install where the host actually lives.
        selected = [n for n in roots if host_dir(n).exists()]
        for name in roots:
            if name not in selected:
                print(f"{name}: skipped — {host_dir(name)} does not exist on this machine "
                      f"(run --target {name} to install there anyway)")
        if not selected:
            # A FRESH machine — no ~/.codex, no ~/.claude, no ~/.agents — is the case this
            # installer most exists for, so refusing there was worse than the littering it
            # avoided. Fall back to the host-neutral root: it is the one directory that is
            # correct to create for a runtime we cannot identify, and it is the same choice
            # `registry.py` makes for the template root under the same "nothing exists yet"
            # condition. Announced, never silent — creating a directory in someone's home is
            # a thing they should be told about.
            selected = [HOST_NEUTRAL]
            print(f"{HOST_NEUTRAL}: no runtime directory exists yet — installing into the "
                  f"host-neutral root {host_dir(HOST_NEUTRAL)}, which any terminal agent "
                  f"reading ~/.agents/skills/ will find.")
    else:
        selected = [args.target]
    for name in selected:
        dest = roots[name]
        n = copy_skill(src, dest, dry_run=args.dry_run, replace=args.replace)
        if args.dry_run:
            continue
        ok, missing = validate_install(dest)
        status = "ok" if ok else f"missing: {', '.join(missing)}"
        # Print the version that landed. Drift between roots is the failure this script exists
        # to prevent, and a number beside each destination is what makes it visible in one look.
        ver = (dest / "VERSION").read_text().strip() if (dest / "VERSION").exists() else "?"
        what = "already current" if n is None else f"installed {n} files"
        print(f"{name}: {what} (v{ver}) -> {dest} ({status})")

    if not args.dry_run:
        print("")
        print("Try it in your terminal agent:")
        print('  Use $slide-maker to create one slide about <topic>.')
        print("")
        print("Optional toolchain check:")
        for name in selected:
            print(f"  python3 {roots[name] / 'scripts' / 'check_env.py'}")


if __name__ == "__main__":
    main()
