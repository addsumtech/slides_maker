#!/usr/bin/env python3
"""registry — resolve the user's template + taste registry root, on ANY runtime.

WHAT LIVES THERE
----------------
`<root>/<template-name>/profile.md` — one folder per template the user has used before, and
`<root>/taste.md` — the portable cross-deck taste profile (schema in `references/user-taste.md`).
It is the USER's footprint, deliberately outside the skill folder so it survives reinstalls and
stays theirs to edit or delete line-by-line.

WHY THIS IS CODE AND NOT A SENTENCE IN FIVE FILES
--------------------------------------------------
It was a sentence in five files, and every one of them named exactly two roots:
`~/.claude/slide-templates/` and `~/.codex/slide-templates/` (`user-taste.md`,
`interview-protocol.md`, `file-inventory.md`, `generated-template.md`, and `deckkit`'s own
`content_slide` docstring). On Kimi, Gemini, Cursor, Coze or any other runtime NEITHER root
exists, so:

  * Q1(a) — "one of your saved templates (N registered)" — can never be offered, and the
    interview quietly drops a choice the protocol says MUST always be presented;
  * `taste.md` is never read and never written, so cross-deck taste does not exist there.

Nothing reports either. No lint fires, no gate fails, the deck simply comes back without the
user's accumulated preferences — the exact silent class this skill legislates against
everywhere else. A hardcoded pair cannot be extended by a runtime that did not exist when the
pair was written; a resolver can.

RESOLUTION
----------
READ scans every root that exists, in priority order, so a template saved under one agent is
findable from another — a user's own templates are theirs regardless of which runtime wrote
them, and `user-taste.md` already calls the profile "portable across hosts".
WRITE picks the first root that exists; if NONE does, it picks the host-neutral root, which is
the only one safe to create on a runtime whose home directory this skill does not own.

    $SLIDE_MAKER_REGISTRY        explicit override — always wins, read and write
    ~/.claude/slide-templates    Claude Code
    ~/.codex/slide-templates     Codex
    ~/.slide-maker/slide-templates   host-neutral — every other runtime, and the fallback
                                     that guarantees a write target always exists

The two established roots keep their priority, so nothing about an existing Claude/Codex
install changes: same root, same precedence, same files.

USAGE
    python3 scripts/registry.py              # report the resolved roots + what is registered
    from registry import roots_for_read, root_for_write, taste_file, list_templates
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Priority order. Host-neutral last so an existing Claude/Codex install is unaffected, but
# present ALWAYS so that "no root exists" is never a reachable state for a write.
_ROOTS = [
    ("claude", ".claude/slide-templates"),
    ("codex", ".codex/slide-templates"),
    ("neutral", ".slide-maker/slide-templates"),
]
NEUTRAL = "neutral"
ENV_OVERRIDE = "SLIDE_MAKER_REGISTRY"


def all_roots() -> list[tuple[str, Path]]:
    """Every candidate root, in priority order — existing or not."""
    out: list[tuple[str, Path]] = []
    override = os.environ.get(ENV_OVERRIDE, "").strip()
    home = Path.home()
    if override:
        # A relative override must be anchored, because this skill changes directory constantly
        # — it builds in a deck folder, renders in another, lints from a third. Left relative,
        # `taste.md` would follow the cwd and the user's profile would fan out into every deck
        # directory they ever built in, each copy looking like a complete registry.
        #
        # Anchor to HOME, NOT via .resolve(): resolve() is still cwd-relative for a relative
        # input (it only makes it absolute *now*), and on macOS it also rewrites /var -> /private/var
        # by following symlinks, so this root would print and compare differently from every
        # sibling root. HOME is where the other three live, so the anchor is consistent rather
        # than invented — and it is said out loud, because a config silently reinterpreted is
        # exactly the class of quiet wrongness this resolver replaced.
        env_path = Path(override).expanduser()
        if not env_path.is_absolute():
            env_path = home / env_path
            print(f"registry: ${ENV_OVERRIDE}={override!r} is a relative path, which cannot mean "
                  f"one fixed place in a tool that changes directory — anchoring it to your home "
                  f"as {env_path}. Set an absolute path to choose somewhere else.",
                  file=sys.stderr)
        out.append(("env", env_path))
    out.extend((name, home / rel) for name, rel in _ROOTS)
    return out


def _unreadable(path: Path, what: str, exc: OSError) -> None:
    """Say it out loud, on stderr, and carry on.

    An unreadable registry must not abort a build. macOS TCC can revoke access to a home
    subdirectory mid-session (it does this to ~/Downloads and ~/Desktop routinely), and a
    PermissionError raised out of the Step-0 interview would kill a deck over a directory the
    deck does not need. But it must not be SILENT either: "no templates registered" and
    "your templates are behind a permission wall" are different facts, and only one of them
    means the user genuinely has no footprint.
    """
    print(f"registry: cannot read {what} at {path} ({exc.__class__.__name__}) — "
          f"treating it as ABSENT for this run, which is NOT the same as empty. "
          f"Fix the permissions if you expected saved templates or a taste profile here.",
          file=sys.stderr)


def roots_for_read() -> list[tuple[str, Path]]:
    """Roots that actually exist, priority order. May be empty — a brand-new user has none,
    and that is a legitimate state: never manufacture a profile for someone with no footprint."""
    out = []
    for n, p in all_roots():
        try:
            if p.is_dir():
                out.append((n, p))
        except OSError as exc:                       # unreadable parent, dead symlink, long path
            _unreadable(p, "registry root", exc)
    return out


def root_for_write() -> tuple[str, Path]:
    """Where a NEW template or a first `taste.md` goes.

    The first existing root wins, so a user who already keeps templates under ~/.claude keeps
    using it. With no root anywhere, the host-neutral one is chosen — NOT created. Creation is
    the caller's job at the moment it has something real to write, because an empty registry
    conjured at read time is indistinguishable from a user who has one, and
    `references/user-taste.md`'s empty-file rule turns on exactly that difference.
    """
    existing = roots_for_read()
    if existing:
        return existing[0]
    for name, path in all_roots():
        if name == NEUTRAL:
            return name, path
    raise RuntimeError("no host-neutral registry root configured")  # unreachable by construction


def taste_file() -> Path | None:
    """The `taste.md` to READ, or None when the user has no footprint yet."""
    for _, root in roots_for_read():
        f = root / "taste.md"
        try:
            if f.is_file() and f.read_text(encoding="utf-8", errors="ignore").strip():
                return f
        except OSError as exc:
            _unreadable(f, "taste.md", exc)
    return None


def list_templates() -> list[tuple[str, Path]]:
    """Registered templates as (name, folder), de-duplicated by name across roots with the
    higher-priority root winning — so Q1(a) can state a real N on any runtime."""
    seen: dict[str, Path] = {}
    for _, root in roots_for_read():
        try:
            subs = sorted(p for p in root.iterdir() if p.is_dir())
        except OSError as exc:
            _unreadable(root, "registry root", exc)
            continue
        for sub in subs:
            try:
                registered = (sub / "profile.md").is_file()
            except OSError as exc:
                _unreadable(sub, "template folder", exc)
                continue
            if registered and sub.name not in seen:
                seen[sub.name] = sub
    return list(seen.items())


def main() -> int:
    print("slide-maker template/taste registry:")
    for name, path in all_roots():
        mark = "ok" if path.is_dir() else "--"
        note = "" if path.is_dir() else "  (not present)"
        print(f"  [{mark}]  {name:<8} {path}{note}")
    wname, wpath = root_for_write()
    print(f"\n  write target: {wpath}  ({wname})")
    t = taste_file()
    shown = str(t) if t else "none yet — a new user has no footprint, and that is not an error"
    print(f"  taste.md:     {shown}")
    tpls = list_templates()
    if tpls:
        print(f"  templates:    {len(tpls)} registered — " + ", ".join(n for n, _ in tpls))
    else:
        print("  templates:    0 registered — offer Q1(a) as 'none saved yet'")
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
