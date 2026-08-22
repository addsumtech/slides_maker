#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The template/taste registry must resolve on runtimes nobody enumerated.

WHY. The registry root was prose, and every copy of that prose named exactly two hosts —
`~/.claude/slide-templates/` and `~/.codex/slide-templates/` — in `user-taste.md`,
`interview-protocol.md` (twice), `file-inventory.md`, `generated-template.md`,
`handoff-and-iteration.md` and `deckkit.content_slide`'s own docstring. On Kimi, Gemini,
Cursor, Coze or an API caller NEITHER exists, so Q1(a) ("one of your saved templates,
N registered") could not be offered and `taste.md` was never read or written.

Nothing reported it. That is the failure mode this suite is really about: no lint fires when a
registry silently has no root, the deck just comes back without the user's accumulated
preferences. So the assertions below are mostly about the SILENT cases —

  * an unknown runtime still gets a write target (the bug: it got none);
  * an existing Claude/Codex install keeps ITS root and its priority (the risk in the fix:
    quietly relocating a user's 11 saved templates would be worse than the bug);
  * a user with no footprint still reports zero templates and no taste.md, because
    `user-taste.md`'s empty-file rule turns on exactly that difference and a resolver that
    conjures an empty registry destroys it.

Every case runs against a FAKE home, never the developer's own registry.

Run:  python3 tests/test_registry_roots.py
"""
import os
import pathlib
import sys
import tempfile
from contextlib import contextmanager

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))

import registry  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


@contextmanager
def fake_home(*existing_roots, env=None, templates=(), taste=None):
    """Run the resolver against a throwaway HOME holding only the named roots."""
    with tempfile.TemporaryDirectory() as td:
        home = pathlib.Path(td)
        for rel in existing_roots:
            (home / rel).mkdir(parents=True, exist_ok=True)
        for rel, name in templates:
            d = home / rel / name
            d.mkdir(parents=True, exist_ok=True)
            (d / "profile.md").write_text("# profile\n", encoding="utf-8")
        if taste:
            rel, body = taste
            (home / rel).mkdir(parents=True, exist_ok=True)
            (home / rel / "taste.md").write_text(body, encoding="utf-8")
        old_home, old_env = os.environ.get("HOME"), os.environ.get(registry.ENV_OVERRIDE)
        os.environ["HOME"] = str(home)
        if env is None:
            os.environ.pop(registry.ENV_OVERRIDE, None)
        else:
            os.environ[registry.ENV_OVERRIDE] = str(home / env)
            (home / env).mkdir(parents=True, exist_ok=True)
        try:
            yield home
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home
            os.environ.pop(registry.ENV_OVERRIDE, None)
            if old_env is not None:
                os.environ[registry.ENV_OVERRIDE] = old_env


CLAUDE = ".claude/slide-templates"
CODEX = ".codex/slide-templates"
NEUTRAL = ".slide-maker/slide-templates"


def main():
    print("== the bug: a runtime that is neither Claude nor Codex ==")
    with fake_home() as home:
        check("no root exists, yet a write target is still resolved",
              registry.root_for_write()[1] == home / NEUTRAL, registry.root_for_write())
        check("...and it is named as the host-neutral one",
              registry.root_for_write()[0] == registry.NEUTRAL)
        check("nothing is CREATED by resolving — an empty registry conjured at read time is "
              "indistinguishable from a user who has one",
              not (home / NEUTRAL).exists())
        check("a user with no footprint has no taste.md", registry.taste_file() is None)
        check("...and zero templates, not a manufactured one", registry.list_templates() == [])

    print("\n== the risk in the fix: an existing install must not move ==")
    with fake_home(CLAUDE, templates=[(CLAUDE, "lkeb-lumc")]) as home:
        check("a Claude-only machine still writes to the Claude root",
              registry.root_for_write()[1] == home / CLAUDE, registry.root_for_write())
        check("...and finds its template there",
              [n for n, _ in registry.list_templates()] == ["lkeb-lumc"])
    with fake_home(CODEX, templates=[(CODEX, "nvidia-dark")]) as home:
        check("a Codex-only machine still writes to the Codex root",
              registry.root_for_write()[1] == home / CODEX, registry.root_for_write())
    with fake_home(CLAUDE, CODEX, NEUTRAL) as home:
        check("with all three present, Claude keeps priority (documented order, unchanged)",
              registry.root_for_write()[1] == home / CLAUDE, registry.root_for_write())

    print("\n== reads span every existing root, so one agent can see another's templates ==")
    with fake_home(CLAUDE, NEUTRAL,
                   templates=[(CLAUDE, "editorial-warm"), (NEUTRAL, "kimi-saved")]):
        names = sorted(n for n, _ in registry.list_templates())
        check("templates from both roots are offered at Q1(a)",
              names == ["editorial-warm", "kimi-saved"], names)
    with fake_home(CLAUDE, NEUTRAL,
                   templates=[(CLAUDE, "dup"), (NEUTRAL, "dup")]) as home:
        got = dict(registry.list_templates())
        check("a name clash resolves to the higher-priority root, once",
              list(got) == ["dup"] and got["dup"] == home / CLAUDE / "dup", got)

    print("\n== taste.md: found wherever it is, and EMPTY still means absent ==")
    with fake_home(NEUTRAL, taste=(NEUTRAL, "dials: bold\n")) as home:
        check("a taste.md under the host-neutral root is read",
              registry.taste_file() == home / NEUTRAL / "taste.md", registry.taste_file())
    with fake_home(CLAUDE, taste=(CLAUDE, "   \n\n")):
        check("an EMPTY taste.md is silently skipped, not returned as a profile",
              registry.taste_file() is None)
    with fake_home(CODEX, NEUTRAL,
                   taste=(NEUTRAL, "neutral\n")) as home:
        check("only the neutral root has one, so that is the one read",
              registry.taste_file() == home / NEUTRAL / "taste.md")

    print("\n== the explicit override wins over every host root ==")
    with fake_home(CLAUDE, CODEX, env="myreg") as home:
        check(f"${registry.ENV_OVERRIDE} outranks an existing Claude root",
              registry.root_for_write()[1] == home / "myreg", registry.root_for_write())
        check("...and is labelled as the override, not as a host",
              registry.root_for_write()[0] == "env")

    print("\n== degrades LOUDLY, never fatally, on a root it cannot read ==")
    # macOS TCC revokes access to home subdirectories mid-session (it does this to ~/Downloads
    # and ~/Desktop routinely). A PermissionError escaping the Step-0 interview would kill a
    # whole build over a directory the deck does not need — but reporting "no templates" for
    # a permission wall would be the silent lie this resolver exists to end.
    with fake_home(CLAUDE, templates=[(CLAUDE, "walled")]) as home:
        (home / CLAUDE).chmod(0o000)
        try:
            import io
            import contextlib
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                tpls = registry.list_templates()
                taste = registry.taste_file()
            check("an unreadable root does not crash list_templates", tpls == [], tpls)
            check("...nor taste_file", taste is None)
            check("...and it SAYS so on stderr, distinguishing absent from empty",
                  "cannot read" in err.getvalue() and "NOT the same as empty" in err.getvalue(),
                  err.getvalue()[:120])
        finally:
            (home / CLAUDE).chmod(0o755)

    print("\n== a root that exists but is a FILE is not a root ==")
    with fake_home() as home:
        (home / ".claude").mkdir(parents=True)
        (home / CLAUDE).write_text("not a directory", encoding="utf-8")
        check("a file where the root should be falls through to the neutral root",
              registry.root_for_write()[0] == registry.NEUTRAL, registry.root_for_write())

    print("\n== the override is anchored, not cwd-relative ==")
    # This skill changes directory constantly (build here, render there, lint elsewhere). A
    # relative override would make taste.md follow the cwd and scatter partial copies of the
    # user's profile across every deck folder they ever built in, each looking complete.
    with fake_home(CLAUDE) as home:
        (home / "rel").mkdir()
        os.environ[registry.ENV_OVERRIDE] = "rel"
        cwd = os.getcwd()
        try:
            os.chdir(home)
            root = registry.root_for_write()[1]
            check("a relative $SLIDE_MAKER_REGISTRY becomes an ABSOLUTE path",
                  root.is_absolute(), root)
            check("...anchored to HOME, the same anchor as every sibling root",
                  root == home / "rel", root)
            os.chdir(cwd)
            check("...and does not move when the working directory does",
                  registry.root_for_write()[1] == root, registry.root_for_write()[1])
        finally:
            os.chdir(cwd)
            os.environ.pop(registry.ENV_OVERRIDE, None)
    # An ABSOLUTE override must be passed through untouched — no symlink rewriting. macOS
    # resolves /var to /private/var, which would make this root print and compare differently
    # from the three that sit under HOME.
    with fake_home(CLAUDE, env="myreg") as home:
        got = registry.root_for_write()[1]
        check("an absolute override is used verbatim, not symlink-resolved",
              got == home / "myreg", got)

    print("\n== the docs point at the resolver, not at a hardcoded pair ==")
    # The prose is what an agent actually follows; a resolver nobody is told to run is the
    # same silent gap in a new place.
    for rel in ("references/user-taste.md", "references/interview-protocol.md",
                "references/file-inventory.md", "references/generated-template.md",
                "references/handoff-and-iteration.md"):
        body = (SKILL / rel).read_text(encoding="utf-8")
        check(f"{rel} names the host-neutral root",
              "slide-maker/slide-templates" in body)
    ip = (SKILL / "references/interview-protocol.md").read_text(encoding="utf-8")
    check("interview-protocol tells Q1 to RUN registry.py for the count",
          "registry.py" in ip)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
