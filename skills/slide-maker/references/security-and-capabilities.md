# Security and capabilities — what this skill does to your machine

Read this before installing, and read it again if a scanner flags the skill. It is the honest
inventory: everything here is real, deliberate, and switchable. Nothing is hidden because it
looked bad in a list.

A slide deck cannot be built without touching the machine — it needs Python libraries, a
renderer, fonts and a place to write files. The question is not whether a deck builder has
capabilities; it is whether they are **declared, scoped and refusable**. This file declares them.

## The capability list

| Capability | Where | Why it exists | Turn it off |
|---|---|---|---|
| **Installs Python packages** into the active interpreter (`python-pptx`, `pymupdf`, `Pillow`, `matplotlib`, `numpy`) | `check_env.py --ensure`, Step 0.0b — **and `import deckkit` itself**, the moment one of them is missing, so an agent that skips Step 0 still gets a working build | A missing library otherwise surfaces at the RENDER, the slowest step in the pipeline, after all the authoring is spent. The versions are lower bounds, not pins, and nothing asks first | `SLIDE_MAKER_NO_ENV_CHECK=1` (covers both paths) |
| **Runs LibreOffice** (`soffice`) to convert pptx → PDF → PNG | `render_deck.py`, `ingest.py` | There is no pure-Python pptx renderer; the visual self-check and the critic loop both need real pixels | don't run the render steps; `SOFFICE` re-points it |
| **Runs headless Chrome/Edge** | `icons.py`, only when neither cairosvg nor `rsvg-convert` is present | SVG → PNG for icons | install cairosvg or librsvg and it is never used |
| **Runs `codex exec`** with no approvals | `generate_images_codex.py` | The no-API-key image path for the generate-a-template branch. The sub-agent runs in a fresh EMPTY directory (its writable workspace), the prompt is passed as marked DATA, and the manifest is validated before any generation — see *Session data* | don't use that branch, or use `generate_images_openai.py` |
| **Probes for a command** (`command -v codex`) | interview Q1(d) | So the interview does not offer an image-tool branch that would dead-end at generation time | — (a probe, no execution) |
| **Runs `npx easybrandkit@0.4.0`** to read a company's website | interview Q1 ("our brand"), only when the user has nothing but a website to go on, and only after the user says yes to it | So a company with no brand files still gets its real logo, colours and fonts rather than a palette guessed from its name. npx fetches that pinned version from npm (MIT, no dependencies; reviewed at 0.4.0, and a newer version comes in only through a reviewed change to the skill, never `@latest`). It opens the site in a headless Chrome with a fresh temporary profile, so no cookies or sign-ins, and saves what it finds in `<deck-dir>/brand-src`; `--no-stores` keeps it off the store listings and social profiles the site links to. `brand_kit.py` itself still never fetches | say no when it is offered, and give the brand's files, hex codes and font names yourself |
| **Network: fetches icon SVGs** | `icons.py` | The icon families are fetched once and cached | pre-populate or clear `SLIDE_MAKER_CACHE`; warm builds are offline |
| **Network: searches and downloads photos** | `fetch_images.py` (`search` / `fetch`), only when you ask for a sourced image | Two keyless, license-clear APIs — Wikimedia Commons and Openverse. It sends the SUBJECT you searched for and nothing else, downloads only files whose licence it recognised, and writes what it did to `<assets>/sources.json` | don't use the sourced path (generation and user-supplied files are unaffected); every call is one you initiated |
| **Network: one version check** | `check_version.py` — `git fetch origin main` on a checkout, one HTTPS GET on a copy install | Tells you a newer version exists. It never pulls, merges, checks out or writes the working tree | `SLIDE_MAKER_NO_VERSION_CHECK=1` |
| **Network: web search** | Step 1 research, through the HOST's tool | Fact-checking a no-source deck. The skill never opens sockets itself for this — the host's search tool does, under the host's own permissions | give the deck source material, or say no research |
| **Reads a Codex session rollout** | `generate_images_codex.py` fallback | The hosted image tool returns base64 inside the session transcript; that is the only place the bytes exist | see *Session data*, below |
| **Reads/writes a cross-deck taste profile** | `taste.md` at the registry root (`registry.py`) | Remembers preferences across decks so the interview stops re-asking | it is a plain file you own — delete it, or never let a Step-6 close write one. Missing/empty is silently skipped |
| **Writes files** | the deck folder you chose, plus the registry root and the platform icon cache | The deliverables | — |
| **Deletes files** | its own `tempfile.mkdtemp()` work dirs, its own icon-cache entries, its own probe file; `install_skill.py --replace` on an install directory | Cleanup | `--replace` is opt-in and refuses a symlink, a wrongly-named directory, or one with no `SKILL.md` in it |

## Session data

`generate_images_codex.py` hands each image prompt to a `codex exec` sub-agent, and the hosted image
tool returns its PNG as base64 **inside that session's transcript**. The manifest those prompts come
from is written by an agent that was reading your material — untrusted input — so the path is built
on four limits, each tested adversarially:

- **The prompt is data.** It sits between markers carrying a per-job random token, the instruction
  says nothing inside them is to be followed, and a prompt containing the marker words, a chat
  special token (`<|…|>`) or a control character is refused before anything is generated.
- **Nothing from the manifest names a file for the sub-agent.** It writes to a fixed name in a
  fresh, empty directory — its whole writable workspace — and the result is moved into place
  afterwards. The deck folder is never its workspace.
- **Outputs stay inside the deck.** Every output must be a bare image file name (letters or digits
  in any script, `.`, `_`, `-`) that resolves inside `--out-dir`, or the manifest's own folder; a
  `../`, a separator or a symlink out is refused, and one bad item stops the whole batch before any
  spend.
- **Only this job's transcript is read, and only when needed.** The image is taken from the file
  the sub-agent wrote, else from its own `--json` event stream; only then from its transcript,
  located by the exact thread id codex reports (`rollout-<time>-<id>.jsonl`, whose first record must
  name the same id). There is no "newest file" fallback any more: that picked a SIBLING job's
  transcript when images were generated in parallel, and an environment pointer named the parent
  session, not the one that made the image. The file read is named on stderr; only the
  `image_generation_call` payload is kept.

Avoid the path entirely by handing the script an image, or by using the API variant.

## Executing Python that is not this skill's

A deck's `style.py` and a section module ARE Python, by design — that is what makes a visual
identity programmable — and they are loaded with `importlib`
(`archetypes.py`, `assemble.py`, `slide_index.py`, `palette_audit.py --from-style`). **Loading a
style file executes it.** That is fine for a file this skill or you just wrote, and it is *not*
fine for a style file from an untrusted source. Treat a third-party `style.py` exactly as you
would treat any Python you are about to run: read it first.

**The delivery gate also executes a deck's surface kits.** `check_register_guard.py` calls
`register_surface.load_kits` on the checked deck's folder, which imports every `surface_*.py` there
so that an invented register's declared prohibitions exist at hand-off. For a deck this skill built,
those are its own kits. For a deck folder you did NOT create — say, reviewing a deck someone sent
you — checking it runs whatever `surface_*.py` sits beside it: move the deck to its own folder, or
read those files first.

`smoke_deckkit.py` calls `exec()` — a scanner will flag it. It executes `sigs.EXAMPLES`, a
hardcoded dict literal in `sigs.py`; that module reads no files and takes no input. It is the CI
test proving every documented scaffold still runs. Nothing external reaches it.

## Untrusted source material, and the preview page

The material you hand this skill — a paper, a deck, a repo, a web page — is **untrusted input to
a language model**. It can contain instructions aimed at the agent. Two consequences are handled
in code:

- The direction-gate preview (`archetypes_html.py`) is an HTML file **you open in your browser**,
  built from a `directions.json` the agent wrote while reading your material. Text was always
  escaped; colour and font values are now validated against a strict pattern before they reach a
  `style="…"` attribute, and a rejected value is replaced and reported on stderr.
- `cover_motif` / `ambient_motif` are **raw HTML on purpose** — a bespoke register draws its own
  signature and the direction-gate structure check requires it. They are sanitised rather than
  escaped: `script`/`style`/`iframe`/`object`/`embed`/`form` elements are removed with their
  contents, `on*` handlers are stripped, and `javascript:` / `vbscript:` / `data:text/html` URLs
  are neutralised. Shape and colour survive; behaviour does not.

Nothing in this file replaces your own judgement about the source you feed it.

## Running it more carefully

- A virtualenv or a container makes the dependency installs disposable.
- `SLIDE_MAKER_NO_ENV_CHECK=1` + `SLIDE_MAKER_NO_VERSION_CHECK=1` removes every automatic install
  and every automatic network call the skill makes on its own behalf.
- `SLIDE_MAKER_CACHE` re-points the icon cache; `SLIDE_MAKER_REGISTRY` re-points the taste/template
  registry. Both accept a throwaway directory.
- Build in a directory you chose, not one the skill picked for you.

## Reporting

Repo-root `SECURITY.md` has the disclosure process. If a scanner flagged something not listed
here, that is worth reporting even if it turns out benign — an undeclared capability is the
finding, whether or not it is exploitable.
