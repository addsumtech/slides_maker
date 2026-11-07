# Setup and version — the detail behind Step 0.0 / 0.0b

Read this when `check_version.py` reports an update or `DIFFERS … at the same version`, and when `check_env.py --ensure` exits non-zero. Moved verbatim from SKILL.md (2026-11-07) so the main file can be read in full; both scripts print what they found, so skipping this file is never silent.


## When check_version reports an update

🔴 **On a COPY install the notice may say `DIFFERS … at the same version`, and that is not a bug.**
`--json` carries `drift: "content"` with a `differing` file list beside the usual `behind`. It means
the installed copy's FILES do not match main even though `VERSION` agrees — work lands between
releases, so the version string cannot see it, and a copy with most of `SKILL.md` missing used to
pass silently. The three options below are unchanged (a reinstall is still what brings a copy to
main); only the reason differs. Two things it cannot tell you, both stated in the notice: which
direction the difference goes, and whether it is instead your own edits to the installed copy — a
fork or a locally-patched install will report this every time, and `SLIDE_MAKER_NO_VERSION_CHECK=1`
is the way to stop it.

**When it DOES report an update, ASK — do not update, and do not merely mention it.** Run
`check_version.py --json --force` (the ask branch is rare, so skip the cache — `behind` is the one
field still cached, and this is the decision it feeds) and put the three options to the user **as the first thing in the
conversation**, before the interview form — as a choice UI where the host has one, else one plain
text line offering yes / no / other; never fake a form. **Spell out what each answer DOES — never
offer a bare yes / no / other.** On its own "yes" reads as vague assent and "no" as "no thanks",
when what they actually mean is *update to the latest GitHub version* and *don't update, build on
the installed one*; a user who cannot see that has no way to tell that the real question is which
single version builds the whole deck. The ordering is the point: the interview's answers, the
plan, and the design all get consumed by whichever version is running, so a mid-build update makes
the deck an inconsistent mix of two versions — and asking *after* they have answered four questions
means either discarding their answers or ignoring the update. Ask once, at the top, then build.

*(Per-deck AUTO WAIVER: do **not** stop. Default to **no — build on the installed version**, and say
so in the first FYI. Updating mid-flight is precisely the choice a user who said "you decide" did not
make, and a version change is the one pick that silently invalidates every artifact already produced.)*
- **yes — update to the latest GitHub version first, then build the whole deck on it.** DO IT
  YOURSELF — the user answered the question, not "give me instructions". `check_version.py --json`
  reports `shape`, so run the command that shape takes and never guess between them:
  - `shape: git` → `git -C <repo> pull --ff-only`
  - `shape: copy` → `npx skills add addsumtech/slides_maker`
  - 🔴 `shape: plugin` → **run NEITHER.** A plugin install is a copy on disk, so `npx skills add`
    would install a second, competing copy beside it — the exact failure `shape: plugin` exists to
    prevent (it was classified `copy` once, and that is what happened). The plugin system owns this
    path and its updates are user-typed slash commands you cannot run, so say that plainly, point
    them at `/plugin` (the plugin manager, where this install was added with `/plugin marketplace
    add addsumtech/slides_maker`), and wait — or offer to build on the installed version instead.
    Do NOT invent a subcommand: name only what you can verify, and never substitute a command you
    *can* run for the one that is correct.
  - `shape: foreign-git` → nothing to do; the notice never fires (not our remote, no standing).

  🔴 **Re-read SKILL.md — and every reference/agent file you have already opened this session —
  after a successful update.** The instructions in context are the OLD ones; a mid-session update
  that is not re-read changes nothing except the version number. Where the two disagree, the file
  on disk wins.
- **no — don't update; build on the installed version.** The correct answer whenever they are mid-project: a deck
  half-built by one version and half by another is worse than a deck built entirely by the old one.
- **other — they have local changes.** Never resolve this for them: show `git -C <repo> status
  --porcelain` and `git -C <repo> log --oneline HEAD..origin/main`, i.e. *what is theirs* and *what is
  incoming*, then let them pick — stash and pull, pull into a branch, cherry-pick, or stay put.
  **Never `git checkout .`, never `--force`, never `--replace` over an install you did not verify is
  clean.** 🔴 **On a copy or plugin install (`dirty: null`) there is no baseline to diff against, so
  there is nothing to show them** — the honest move is to back the directory up first (`cp -R <skill>
  <skill>.bak`), then update, then let them compare. Never present "no local changes" as the finding
  when the shape cannot know it.

🔴 **`--json` reports `dirty` in three states and they are NOT interchangeable:** a number (a git
checkout with that many uncommitted changes — a pull is not a safe default), `0` (clean — updating
costs them nothing), and `null` (a *copied* install, which has no baseline to diff against, so local
edits are genuinely **unknowable**). Report `null` as unknown. Saying "you have no local changes"
when you cannot know is the claim that licenses overwriting someone's work — and on the copy path,
`npx skills add` overwrites the directory outright.


## The toolchain check in full

🔴 **The moment the version is settled and BEFORE the interview, run
`python3 scripts/check_env.py --ensure` on a deck-BUILD ask.** It is the same silent-when-warm shape
as the version check: it imports the required pip deps (`python-pptx`, `pymupdf`, `Pillow`,
`matplotlib`, `numpy`), and if any are missing it **installs them into this interpreter** (pip, then
`--user` on an externally-managed env) — one fast install now instead of an `ImportError` at the step
that needs them. **Why here and not "when a render errors":** on a fresh machine the missing library
does not surface until the step that imports it, and the most expensive one is the **RENDER (Step 5),
the gate the critic loop waits on** — a missing LibreOffice or PyMuPDF there costs a diagnosis
round-trip and a re-run at the priciest moment in the pipeline. Catching it at Step 0 turns that into
one up-front install, which is the whole point (less wall-clock, fewer tokens). Cost on a warm machine
is ~0.1s and it prints nothing; opt out with `SLIDE_MAKER_NO_ENV_CHECK=1`.

**Act on the exit code — it distinguishes what you CAN auto-fix from what you cannot:**
- **`0`** — everything required is present (or was just installed) and LibreOffice is found. If it
  installed something it says so in one line; otherwise say nothing and go to the interview.
- **`3`** — pip deps are ready but **LibreOffice is MISSING**. It cannot be pip-installed (a system
  app needing a package manager / GUI download), so the script prints the one install command per OS
  and does not run it. **Surface that command to the user now** — LibreOffice is what Step 5's render
  needs, so a deck built without noticing will die at the render, after all the authoring is spent.
- **`1`** — a required pip dep could not be installed (a hard externally-managed block). The script
  prints the manual command; surface it, and do not add `--break-system-packages` on the user's behalf
  — overriding the OS package manager is their call.

This is a BUILD-ask step: a pure critique/audit/question run does not need the render toolchain, so
skip it there (the version check still runs — it is not gated on build). One shared `check_env.py`
owns both the `--ensure` auto-fix and the human-readable report, so "what is required" never drifts.
