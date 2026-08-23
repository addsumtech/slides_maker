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
| **Installs Python packages** into the active interpreter (`python-pptx`, `pymupdf`, `Pillow`, `matplotlib`) | `check_env.py --ensure`, Step 0.0b | A missing library otherwise surfaces at the RENDER, the slowest step in the pipeline, after all the authoring is spent | `SLIDE_MAKER_NO_ENV_CHECK=1` |
| **Runs LibreOffice** (`soffice`) to convert pptx → PDF → PNG | `render_deck.py`, `ingest.py` | There is no pure-Python pptx renderer; the visual self-check and the critic loop both need real pixels | don't run the render steps; `SOFFICE` re-points it |
| **Runs headless Chrome/Edge** | `icons.py`, only when neither cairosvg nor `rsvg-convert` is present | SVG → PNG for icons | install cairosvg or librsvg and it is never used |
| **Runs `codex exec`** | `generate_images_codex.py` | The no-API-key image path for the generate-a-template branch | don't use that branch, or use `generate_images_openai.py` |
| **Probes for a command** (`command -v codex`) | interview Q1(d) | So the interview does not offer an image-tool branch that would dead-end at generation time | — (a probe, no execution) |
| **Network: fetches icon SVGs** | `icons.py` | The icon families are fetched once and cached | pre-populate or clear `SLIDE_MAKER_CACHE`; warm builds are offline |
| **Network: one version check** | `check_version.py` — `git fetch origin main` on a checkout, one HTTPS GET on a copy install | Tells you a newer version exists. It never pulls, merges, checks out or writes the working tree | `SLIDE_MAKER_NO_VERSION_CHECK=1` |
| **Network: web search** | Step 1 research, through the HOST's tool | Fact-checking a no-source deck. The skill never opens sockets itself for this — the host's search tool does, under the host's own permissions | give the deck source material, or say no research |
| **Reads a Codex session rollout** | `generate_images_codex.py` fallback | The hosted image tool returns base64 inside the session transcript; that is the only place the bytes exist | see *Session data*, below |
| **Reads/writes a cross-deck taste profile** | `taste.md` at the registry root (`registry.py`) | Remembers preferences across decks so the interview stops re-asking | it is a plain file you own — delete it, or never let a Step-6 close write one. Missing/empty is silently skipped |
| **Writes files** | the deck folder you chose, plus the registry root and the platform icon cache | The deliverables | — |
| **Deletes files** | its own `tempfile.mkdtemp()` work dirs, its own icon-cache entries, its own probe file; `install_skill.py --replace` on an install directory | Cleanup | `--replace` is opt-in and refuses a symlink, a wrongly-named directory, or one with no `SKILL.md` in it |

## Session data

`generate_images_codex.py` reads `~/.codex/sessions/**/rollout-*.jsonl` because the hosted
image-generation tool returns its PNG as base64 **inside the session transcript** — there is no
other copy. That is a genuine privacy surface and it is scoped three ways: an explicit session
pointer from the environment wins (`CODEX_SESSION_ID` / `CODEX_ROLLOUT_PATH` / `CODEX_THREAD_ID`);
otherwise the newest rollout must be under 30 minutes old to be plausibly this run's; and the file
actually opened is **named on stderr**, so reading a transcript is never silent. Only the
`image_generation_call` payload is extracted; no other field is read and nothing from the file is
echoed. Avoid the path entirely by handing the script an image, or by using the API variant.

## Executing Python that is not this skill's

A deck's `style.py` and a section module ARE Python, by design — that is what makes a visual
identity programmable — and they are loaded with `importlib`
(`archetypes.py`, `assemble.py`, `slide_index.py`, `palette_audit.py --from-style`). **Loading a
style file executes it.** That is fine for a file this skill or you just wrote, and it is *not*
fine for a style file from an untrusted source. Treat a third-party `style.py` exactly as you
would treat any Python you are about to run: read it first.

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
