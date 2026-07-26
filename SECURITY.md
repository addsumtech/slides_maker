# Security

## Reporting

Open a private security advisory on
[GitHub](https://github.com/addsumtech/slides_maker/security/advisories/new), or a normal issue if
the finding is not sensitive. There is no bug bounty.

## Known false positive: `sk-*` is a CSS class prefix in this repository

**If a scanner reported a hardcoded OpenAI API key here, it is almost certainly this.** You can
confirm it in about ten seconds; please do that before filing.

The direction-gate preview page names its CSS classes after slide **skeletons**:

```
sk-body   sk-statement   sk-split   sk-island   sk-band   sk-rail
```

They live in `skills/slide-maker/scripts/archetypes_html.py` and are asserted by
`skills/slide-maker/scripts/smoke_directions.py`. `sk-` is short for *skeleton*.

A scanner that matches the literal prefix `sk-` flags every one of them. A real OpenAI key is `sk-`
followed by roughly 48 high-entropy characters; these are followed by four to nine lowercase
letters. **The two are separable by length and entropy**, which is what `scripts/scan_secrets.py`
does instead of prefix matching:

```bash
python3 scripts/scan_secrets.py --selftest   # proves it catches real shapes AND ignores ours
python3 scripts/scan_secrets.py              # working tree
python3 scripts/scan_secrets.py --history    # every blob in every commit, all branches
```

All three run in CI on every push and pull request. The self-test runs *first*: if a rule ever
stops catching a real credential shape, the build fails rather than reporting clean.

The reason this file exists is not the false positive itself — it is that a report which is always
wrong teaches everyone to ignore the scanner, and then the one true positive is ignored too.

## How credentials are handled

- **Nothing is ever hardcoded.** `scripts/generate_images_openai.py` reads the key from an
  environment variable (`--api-key-env`, default `OPENAI_API_KEY`) and exits with an error if it is
  unset. No `.env`, key or credential file is tracked; `.gitignore` covers the usual shapes so that
  staying out of version control is a mechanism rather than a habit.
- **The documented pattern reads from a local file**, never a literal:
  `export OPENAI_API_KEY="$(cat ~/.openai_key)"`. Docs deliberately avoid writing any literal after
  the `=`, because a scanner cannot tell a placeholder from a credential — and neither can a reader
  skimming a diff.
- **A present key is not consent.** The OpenAI image path is metered, and the skill's BILLING GATE
  (`skills/slide-maker/references/image-generation.md`) requires the user's explicit go-ahead before
  the first paid call, even when a key is already exported. The free paths (native imagegen, Codex)
  need no key at all.

### Audit performed 2026-07-26

Prompted by a third-party multi-engine report of a possible hardcoded `sk-` key:

| check | result |
|---|---|
| working tree, real key shape (`sk-` + ≥20 chars, entropy floor) | 0 |
| **full git history**, all refs, 1,645 blobs | 0 |
| Anthropic · GitHub PAT · AWS · GCP · Slack · private-key blocks | 0 in tree, 0 in history |
| tracked `.env` / `*.pem` / `*.key` / credential files | none |
| key read path | `os.environ.get(...)`, no literal anywhere |

**No credential exposure, and nothing to revoke.** Every `sk-` hit was a CSS class name. The same
conclusion was reached manually for v3.9.0; it is now a CI check so the next report can be
dismissed by running one command instead of repeating the investigation.

## What this skill does on your machine

It writes decks and assets under `~/Downloads/<deck-name>/`, runs LibreOffice to render slides, and
— only after the billing gate — may call an image API. It does not phone home, and it does not read
credentials other than the image-provider key you explicitly export.
