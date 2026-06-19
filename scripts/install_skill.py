#!/usr/bin/env python3
"""Install slide-maker into Codex and/or Claude Code skill directories.

Run from anywhere:
    python scripts/install_skill.py --target both

This copies the current skill folder into:
    ~/.codex/skills/slide-maker
    ~/.claude/skills/slide-maker
"""
import argparse
import fnmatch
import os
import shutil
from pathlib import Path


SKILL_NAME = "slide-maker"
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
    }


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
    if replace and dest.exists():
        if dry_run:
            print(f"would remove existing {dest}")
        else:
            shutil.rmtree(dest)
    files = list(iter_files(src))
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
        choices=["codex", "claude", "both"],
        default="both",
        help="Which skill directory to install into.",
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
    selected = ["codex", "claude"] if args.target == "both" else [args.target]
    for name in selected:
        dest = roots[name]
        n = copy_skill(src, dest, dry_run=args.dry_run, replace=args.replace)
        if args.dry_run:
            continue
        ok, missing = validate_install(dest)
        status = "ok" if ok else f"missing: {', '.join(missing)}"
        print(f"{name}: installed {n} files -> {dest} ({status})")

    if not args.dry_run:
        print("")
        print("Try it in your terminal agent:")
        print('  Use $slide-maker to create one slide about <topic>.')
        print("")
        print("Optional toolchain check:")
        for name in selected:
            print(f"  python {roots[name] / 'scripts' / 'check_env.py'}")


if __name__ == "__main__":
    main()
