# Visual-language authoring kit and any-agent use — Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A sixteenth visual language can be started with one command and finished by following one guide and the checks' own messages, without breaking the fifteen; and an agent that is not Claude can build a visual-language deck from the docs and the scripts' printed output alone.

**Architecture:** New languages keep their code in `scripts/vl_langs/<name>.py` (auto-loaded, like `scripts/vl_specs/`), so adding one never edits a central file. Unfinished work is marked, not guessed at: a manifest field still holding a `FILL:` string and a page whose composition is still a stub are named by the contract check. A language card (`--describe`) is printed from the manifest. The shared-gate frictions that stopped docs-only runs are fixed where they live (`render_deck.py`, `check_register_pixels.py`, `sigs.py`).

**Tech Stack:** Python 3 scripts in `skills/slide-maker/scripts`, python-pptx, script-style tests (`tests/test_*.py` printing `N passed, 0 failed`), LibreOffice for renders.

**Spec:** `docs/superpowers/specs/2026-10-15-visual-language-system-design.md` §7 (Phase 4), §3.D (frictions), §8 (constraints).

## Global Constraints

- Never invent words, numbers or names on a page; derived words are declared.
- Commit locally; push, release or rsync the installed copy only when the user says so; after a push wait for the GitHub CI conclusion, then `rsync` to `~/.agents/skills/slide-maker` (dry run first).
- Before any push: the full local CI (`cisteps.py`, chunks under 10 minutes) and the Linux font simulation — `cisim.py` over the visual-language suites AND `scripts/smoke_deckkit.py`.
- Codex usage: the single limited run of Phase 4 only — the user runs the one command given to them.
- CHANGELOG English-only; SKILL.md changes keep `check_skill_lossless.py` green.
- Fixtures are self-built; the user's own decks are never used as test input.
- Ordinary decks (no visual language) draw byte-identically; the fifteen languages' bundled sample fingerprints do not move.
- Branch `vl-authoring-p4` from `main`; stage named paths only; identity dong845.

## Review Focus

1. **A half-made language** — a manifest with no code, or the generator's untouched output — must leave every other language and every ordinary deck working (`import visual_languages` must not raise); only that language is reported, by name and file. Test: Task 1, Task 3.
2. **Generator inputs** — an existing name, an invalid name (`Mosaic`, `my-lang`, `vl`), `--kind image-led`, and a non-ASCII display name in the written manifest: each refused loudly or written exactly. Test: Task 3.
3. **`--describe` examples run as printed** for all fifteen languages, including a language whose sample copy is Chinese. Test: Task 4.
4. **render/ ownership** — an old cache with no `deck` key, an explicit `out_dir`, and the same deck rendered twice must all still work; only a different deck into the same `render/` is refused. Test: Task 8.
5. **The repeat waiver** — `deliberate repeat:` with an empty reason is not a waiver, and the waiver never silences the declared-hue and palette checks. Test: Task 7.

---

### Task 1: Language code is discovered, and a missing painter breaks only its own language

**Files:**
- Create: `skills/slide-maker/scripts/vl_langs/__init__.py`
- Modify: `skills/slide-maker/scripts/vl_native.py` (end of file: load `vl_langs` after `vl_native2`/`vl_native3`)
- Modify: `skills/slide-maker/scripts/visual_languages.py:396-400` (painter lookup), `use()` (refuse an unready language)
- Modify: `skills/slide-maker/scripts/vl_contract.py` (`validate`: painter names must be `_ground_<name>` / `_card_<name>` strings)
- Modify: `skills/slide-maker/scripts/vl_conformance.py` (`painters_missing(name)`), `scripts/check_vl_contract.py` (report it)
- Test: `skills/slide-maker/tests/test_vl_authoring.py` (new, wired into `.github/workflows/ci.yml` like `test_vl_optimise`)

**Interfaces:**
- Produces: `vl_langs.load(directory=None) -> {name: module}` (directory or `$VL_LANGS_DIR` or the package folder; `_`-prefixed files skipped); `visual_languages.painter(name, role) -> callable | None` (`role` in `"ground"`, `"card"`: `globals()` first, then `vl_langs` module attribute of that name); `visual_languages.VLNotReady(Exception)`; `vl_conformance.painters_missing(name) -> [str]`.

- [ ] **Step 1: Write the failing test** — copy every manifest into a temp dir, add `mosaic.py` (tally's manifest renamed: `name`, `order` 16, painters `_ground_mosaic`/`_card_mosaic`, ground/accent shifted so distinctiveness passes), run a child process with `VL_SPECS_DIR` set:

```python
r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0,'scripts'); import visual_languages as vl; "
                    "import deckkit as dk; prs = dk.blank_deck(13.333, 7.5); k = vl.use('tally', prs); print('ok')"],
                   cwd=ROOT, env=dict(os.environ, VL_SPECS_DIR=str(d)), capture_output=True, text=True)
check(r.returncode == 0 and "ok" in r.stdout, "a 16th manifest with no code leaves tally working ({})".format(r.stderr[-200:]))
# …and mosaic itself is refused by name, naming the file to write
r2 = <same, with vl.use('mosaic', prs)> → check(r2.returncode != 0 and "vl_langs/mosaic.py" in r2.stderr)
# …and check_vl_contract names the missing painters instead of crashing
r3 = <python3 scripts/check_vl_contract.py mosaic> → check(r3.returncode == 1 and "_ground_mosaic" in r3.stdout)
```

- [ ] **Step 2: Run it** — `python3 tests/test_vl_authoring.py` — Expected: FAIL, `KeyError: '_ground_mosaic'` in the child's stderr.
- [ ] **Step 3: Implement** — `vl_langs/__init__.py` mirrors `vl_specs/__init__.py`'s loader (importlib per file, module name `vl_lang_<stem>`); `vl_native.py` ends with `import vl_langs; vl_langs.load()`; in `visual_languages.py` the registration loop becomes:

```python
def painter(name, role):
    fn = REGISTRY[name]["painters"][role]
    if fn in globals():
        return globals()[fn]
    import vl_langs
    mod = vl_langs.load().get(name)
    return getattr(mod, fn, None) if mod else None

for _n in LANGS:
    _g, _c = painter(_n, "ground"), painter(_n, "card")
    if _g is None or _c is None:
        _UNREADY[_n] = "{}: write {} and {} in scripts/vl_langs/{}.py (references/visual-language-authoring.md)".format(
            _n, REGISTRY[_n]["painters"]["ground"], REGISTRY[_n]["painters"]["card"], _n)
        continue
    rs.register(_n, ground=_g, card=_c, forbids=LANGS[_n]["forbids"], source=__file__)
```

and `use()` raises `VLNotReady(_UNREADY[name])` first thing for a language in `_UNREADY`. `painters_missing(name)` returns `[_UNREADY[name]]` or `[]`; `check_vl_contract` adds it before the build checks and skips them for that language.
- [ ] **Step 4: Run** — Expected: PASS; `test_vl_contract.py`, `test_visual_languages.py` unchanged.
- [ ] **Step 5: Commit** — `git add` the files above; `git commit -m "a new language's code lives in scripts/vl_langs/<name>.py; a manifest whose painters are not written yet is refused by name instead of breaking every language"`

### Task 2: Unfilled fields and stub pages are named

**Files:**
- Modify: `skills/slide-maker/scripts/vl_contract.py` (`FILL = "FILL:"`, `unfilled(spec) -> [str]` walked first in `validate`)
- Modify: `skills/slide-maker/scripts/vl_native.py` (`stub(lang, page)` registers a composition that raises `NotImplementedError` and carries `fn.stub = True`)
- Modify: `skills/slide-maker/scripts/vl_conformance.py:54-61` (`pages_missing` counts a stub as missing, naming `scripts/vl_langs/<name>.py`)
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

**Interfaces:**
- Consumes: Task 1's `vl_langs`.
- Produces: `vl_contract.FILL`, `vl_contract.unfilled(spec)`; `vl_native.stub(lang, page)`.

- [ ] **Step 1: Failing test**

```python
s = good_spec()          # the fixture of test_vl_contract, copied here
s["display"]["zh"] = "FILL: the language's Chinese name"
s["grounds"]["night"]["palette"]["accents"] = ["FILL: one accent that reads on the night ground"]
p = vc.validate(s)
check(any("display.zh" in x and "Chinese name" in x for x in p), "an unfilled display.zh is named by its path and hint")
check(any("grounds.night.palette.accents[0]" in x for x in p), "an unfilled nested list item is named by its path")
check(not any("must be" in x for x in p if "accents" in x), "an unfilled field is reported once, as unfilled, not as a bad hex")
vn.stub("tally_stubcheck", "cover")
check(vcf.pages_missing("tally_stubcheck", registry={"tally_stubcheck": {"kind": "drawn"}})[0].endswith(
      "cover: still a stub — compose it in scripts/vl_langs/tally_stubcheck.py"), "a stub page is a missing page")
```

- [ ] **Step 2: Run** — Expected: FAIL (`vc.unfilled` / `vn.stub` missing).
- [ ] **Step 3: Implement** — `unfilled` walks dicts/lists with a dotted path (`grounds.night.palette.accents[0]`) and returns `"{name}: {path} is not filled — {hint}"`; `validate` returns those first and only them when any exist (the type checks would otherwise misread a sentinel string as a bad value). `pages_missing` treats `getattr(fn, "stub", False)` as absent.
- [ ] **Step 4: Run** — Expected: PASS; `test_vl_contract.py` 215/0.
- [ ] **Step 5: Commit** — `"a FILL: field and a stub page are named by the contract check, with the file to edit"`

### Task 3: `new_visual_language.py` starts a language

**Files:**
- Create: `skills/slide-maker/scripts/new_visual_language.py`
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

**Interfaces:**
- Consumes: Tasks 1–2 (`vl_langs` folder, `FILL:`, `vn.stub`).
- Produces: CLI `new_visual_language.py <name> [--like <drawn language>] [--specs-dir D] [--langs-dir D]`; prints the two files written and `NEXT: python3 <abs>/check_vl_contract.py <name>`.

- [ ] **Step 1: Failing test** — in temp dirs (copies of the shipped manifests), run the generator for `mosaic --like tally`; then:
  - `check_vl_contract.py mosaic` (with `VL_SPECS_DIR`/`VL_LANGS_DIR`) exits 1, lists `FILL` paths for `display`, `rationale`, `offer`, every ground's `palette`, `look.fonts` display face, and seven `still a stub` pages — and no traceback;
  - `import visual_languages; vl.use("tally", …)` still works in that environment;
  - refusals (exit 2, message names the reason): an existing name (`tally`), `Mosaic`, `my-lang`, `vl` (a module stem), `--kind image-led` (image-led languages compose through `LAYOUTS` — the message names the guide section);
  - end to end: the test replaces every `FILL:` with a value (a distinct palette, names, topics) and, in the stub module, points each page at tally's composer; `check_vl_contract.py mosaic` then exits 0.
- [ ] **Step 2: Run** — Expected: FAIL (no such script).
- [ ] **Step 3: Implement** — the manifest is written from the `--like` language's SPEC (`pprint`ed, `ensure_ascii=False` for the Chinese strings) with `name`, `order` (max + 1), `painters`, and these replaced by `FILL:` hints: `display.en/zh`, `rationale`, `offer.en/zh`, every ground's `palette` colours and `label`/`label_zh`, `look.fonts.*.display`, `samples.copy`. The module holds a ground painter returning the content rect (a working default: `(0.6, 0.55, W - 1.2, H - 1.1)`), `_card_<name> = vl._card_for(name)`, and `vn.stub(name, page)` for the seven pages, each with a comment naming the guide section.
- [ ] **Step 4: Run** — Expected: PASS.
- [ ] **Step 5: Commit** — `"new_visual_language.py writes a language's manifest and composition stubs; every unfilled decision is named by check_vl_contract"`

### Task 4: `visual_languages.py --describe <name>`

**Files:**
- Modify: `skills/slide-maker/scripts/visual_languages.py` (`describe(name) -> str`, `--describe NAME` in `main`)
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

**Interfaces:**
- Produces: `visual_languages.describe(name) -> str` — sections `language`, `grounds`, `pages`, `extras`, `derived words`, `offered for`, `fonts`, and `example:` followed by a self-contained Python block (imports, canvas, `vl.use`, cover + points + closing from the manifest's own sample copy, `prs.save`).

- [ ] **Step 1: Failing test** — for every language: `describe(n)` contains each section header and every extra name; the block after `example:` is `exec`'d in a temp dir and saves a deck whose slide count is 3; an unknown name exits 2 naming the registered ones; an unready language (Task 1) prints its card with the `not ready:` line instead of an example.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — read only `REGISTRY[name]` (manifest data); the extras table prints `pages`, `remembered`, `takes`, `absent` per extra.
- [ ] **Step 4: Run** — Expected: PASS for all fifteen.
- [ ] **Step 5: Commit** — `"--describe prints a language's card and a runnable example from its manifest"`

### Task 5: `sigs.py` — character offsets (M1) and `--in` / `--ground` (M8)

**Files:**
- Modify: `skills/slide-maker/scripts/sigs.py` (`placed_example`, argument handling)
- Modify: `skills/slide-maker/SKILL.md` (one line naming `--in`/`--ground` where `--example` is taught)
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

- [ ] **Step 1: Failing test** — a scaffold whose first line holds Chinese text before the placed call is placed with its arguments intact (today: ast byte offsets cut it mid-token); `sigs.py --example timeline --ground night` (no `--in`) exits 2 saying `--ground goes with --in`; `sigs.py --example timeline --in nosuch` exits 2 naming the registered languages.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — convert `col_offset`/`end_col_offset` (UTF-8 byte offsets) with `len(line.encode()[:off].decode())` per line; validate `--in`/`--ground` before printing.
- [ ] **Step 4: Run** — Expected: PASS; `smoke_deckkit.py` 0 failures.
- [ ] **Step 5: Commit** — `"sigs.py places scaffolds by character offsets; --ground without --in and an unknown --in are refused when typed"`

### Task 6: A gate summary never contradicts a fault in its own section (friction 2)

**Files:**
- Modify: `skills/slide-maker/scripts/render_deck.py` (`gate_ok(line)`; the summary prints at the blind-read, taste-ledger, build-shape and audience-brief sections)
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

- [ ] **Step 1: Failing test** — a self-built 3-slide deck plus `deck_gates.py init`'s template record (placeholders untouched); `render_deck.py <deck> --gate-check`: assert the output does not contain `blind read: ` with `answer(s)` when it contains `blind_read`'s `is missing`, and not `taste ledger: … all accounted for` when a `taste` fault is printed.
- [ ] **Step 2: Run** — Expected: FAIL (`blind read: 59 answer(s)` beside `answers is missing`).
- [ ] **Step 3: Implement** — `gate_ok(line)` prints only when `_COLLECTED` holds no fault for `_SECTION`; the four summary prints call it.
- [ ] **Step 4: Run** — Expected: PASS; `test_lint_regressions.py` unchanged.
- [ ] **Step 5: Commit** — `"a gate's pass summary is printed only when its section recorded no fault (blind read counted the letters of a placeholder)"`

### Task 7: The repeat waiver the GROUND REPEAT message promises (friction 3)

**Files:**
- Modify: `skills/slide-maker/scripts/check_register_pixels.py` (`_repeat_waiver(design) -> str | None`; GROUND REPEAT and LAST DECK'S SCHEME honour it; their messages name the exact words)
- Modify: `skills/slide-maker/references/visual-languages.md` (a ground the user named: the palette line carries `deliberate repeat: the user named the <g> ground`)
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

- [ ] **Step 1: Failing test** — a fixture look history with two light rows and a light deck: no waiver → GROUND REPEAT; palette `"… — deliberate repeat: the user named the light ground"` → no GROUND REPEAT and `facts["repeat"]` holds the reason; `"deliberate repeat:"` with nothing after it → still GROUND REPEAT; with the waiver, a declared hue absent from the pixels is still `DECLARED HUES ABSENT`.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — `_repeat_waiver` matches `deliberate repeat:\s*(\S.{3,})` in `design_plan.palette`; the history checks are skipped with the reason recorded; the messages say: `add "deliberate repeat: <why>" to design_plan.palette`.
- [ ] **Step 4: Run** — Expected: PASS.
- [ ] **Step 5: Commit** — `"the GROUND REPEAT waiver its message names now exists: 'deliberate repeat: <why>' in the palette line, history checks only"`

### Task 8: One deck's render/ is not another's (friction 4)

**Files:**
- Modify: `skills/slide-maker/scripts/render_deck.py` (cache records `"deck": <file name>`; refuse a different deck into the same `out`; `--gate-check` faults renders made from another deck)
- Modify: `skills/slide-maker/references/visual-languages.md` (one deck per folder)
- Test: `skills/slide-maker/tests/test_vl_authoring.py`

- [ ] **Step 1: Failing test** — two 2-slide decks `a.pptx`, `b.pptx` in one folder: render `a`; render `b` → exit 1, message names `a.pptx` and prints `render_deck.py b.pptx <folder>/render-b`; `a`'s PNG hashes unchanged; render `a` again → works; render `b` into an explicit out dir → works; a cache with no `deck` key → `b` renders (old caches are not refused); `--gate-check b.pptx` while `render/` holds `a` → fault `render/ holds a.pptx's pages`.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — write `deck` into `.render-cache.json`; before rendering, read it: a different, still-existing file name in the default `render/` → refuse with the exact command; the gate check compares the same key.
- [ ] **Step 4: Run** — Expected: PASS.
- [ ] **Step 5: Commit** — `"a second deck in the same folder no longer overwrites the first one's render/, and the gates notice renders of another deck"`

### Task 9: The authoring guide, and the docs an agent reads

**Files:**
- Create: `skills/slide-maker/references/visual-language-authoring.md`
- Modify: `skills/slide-maker/references/visual-languages.md` (pointer; the gate count is the first pass — `deck_gates.py check` lists every shape problem at once; the canvas note: `formats.blank_deck("16:9")` is 10in, `sigs.py` scaffolds lay out on 13.333in)
- Modify: `skills/slide-maker/SKILL.md` (one pointer line where visual languages are taught)
- Modify: `skills/slide-maker/scripts/visual_languages.py` (`--gates` prints `ground: light (the default — pass --ground)` when `--ground` was not given)
- Test: `skills/slide-maker/tests/test_vl_authoring.py` (doc checks), `scripts/check_skill_lossless.py`

The guide's sections (spec §7): the contract field by field (from `vl_contract.validate`'s checks, one row each); the design rules learned so far (never invent; a route or arrow only when the caller says ordered; measure with headroom and set the measured lines; alternative layouts before refusing; declared overlaps; the derived-words list; floors 12/10pt and the attribution floor; designed contrast ground; distinctiveness; CJK rules — clause breaks, no spaces between CJK and Latin, Latin words never split; a widow is fixed by phrase → balanced measure → ≤15% shrink → chosen breaks); the steps from `new_visual_language.py` to shipped samples (contract → compositions → `check_vl_contract` → sheets for the user → `--sample --refresh-bundled` → `vl_docs --check` → CI); a review checklist.

- [ ] **Step 1: Failing test** — every `scripts/*.py` and `--flag` the guide names exists (flags found in the script's argparse); every `references/*.md` it links exists; SKILL.md and visual-languages.md link it; `--gates tally --deck <tmp>` without `--ground` prints `the default`.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Write the guide and the doc lines; print the default ground.**
- [ ] **Step 4: Run** — Expected: PASS; `check_skill_lossless.py` and `vl_docs.py --check` green.
- [ ] **Step 5: Commit** — `"references/visual-language-authoring.md: the contract, the rules learned, the steps to a shipped language; the docs say what the gates and canvases really do"`

### Task 10: CHANGELOG

- [ ] Add an `[Unreleased]` entry (English only) covering Phases 1–4: the contract and manifests, components wearing a language (skins, designed series, placement), the optimisation pass approved on sheets (ink's cinnabar and xuan), the authoring kit, the frictions fixed. Commit `"CHANGELOG: the visual-language system (unreleased)"`.

### Task 11: Acceptance — two docs-only runs, then the Codex command

- [ ] Run two Sonnet subagents with only `SKILL.md`, `references/visual-languages.md`, `references/visual-language-authoring.md` and the scripts' printed output (no source reading): (a) English, `broadsheet`, five pages incl. one general component placed with `sigs.py --example … --in broadsheet`; (b) Chinese, `chalkboard`, five pages. Each reports every place it was blocked or misled, with the command and output.
- [ ] Each confirmed friction: a failing test, the fix, the test green, a commit.
- [ ] Hand the user ONE Codex command (one language, about five pages, run only printed commands), with what to send back.

### Task 12: Verify and review

- [ ] Full local CI (`cisteps.py`, four chunks) and the Linux sim (`cisim.py` over the visual-language suites, `test_vl_authoring.py` and `scripts/smoke_deckkit.py`).
- [ ] One Sonnet whole-branch review; one RED→GREEN fix pass; rulings and deferred minors to the user.
- [ ] Finishing menu (merge locally / keep); push only on the user's word.
