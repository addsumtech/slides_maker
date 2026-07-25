# Content plan spec — comprehension brief, claim ledger, and the web-verification bar (Step 1)

## Comprehension brief — the required fields and the claim-ledger columns

- The **one-sentence message** + the verbatim source sentence it derives from (+ where).
- The **contributions**, in their words, each with its source location.
- The **method essence** at talk-altitude (+ the one key equation), and where it appears.
- **One row per figure AND table:** `id | what it is FOR (the ONE comparison) | which exact
  element carries it (row/column/curve/panel) | what it emphasises | the WRONG reading to avoid`.
  A table exists to make one comparison obvious — foreground *that* (e.g. baseline vs +X), and
  name the carrying element (it drives which row the build highlights + the assertion title).
  A figure whose carrying element you cannot name is one you haven't understood.
- Any **nuance/limitation** the authors stress, quoted.
- A **claim ledger** (per `content-planner.md` §2): every number/date/name/citation/superlative/
  dated-event as a row with source + verbatim value + verified?(Y/N) + as-of date; an unverifiable
  claim is cut or marked open, never shipped.

## Web verification & no-source decks (incl. grounding to today)

- **No content:** draft an outline from your own expertise, then **ground *and verify*
  it** with the host's available web search/fetch tools (Codex: use `web.run`) — treat this as a **fact-check, not just framing**.
  List the deck's specific *falsifiable* claims (numbers, dates, names, citations, and
  every "first/largest/state-of-the-art" assertion) and confirm each against its **primary**
  source (the planner's PROVENANCE CONTRACT, `agents/content-planner.md` §2 — an aggregator
  or news rewrite is not confirmation) before it lands on a slide; fix or cut anything you
  can't verify, and never
  present an unverifiable claim as established fact. This matters because a no-source deck
  has **no paper to anchor it** — *you* are the only check on whether a confident-sounding
  statement is actually true, and an expert audience spots a wrong "fact" instantly (the
  failure mode here is being *wrong*, not just vague). **If the host exposes NO web tool** (no
  search/fetch available), do not present falsifiable claims as established: mark each such claim
  *open/unverified*, soften it to what you can defend, and **ask the user to confirm the numbers or
  supply a source** — never ship an unchecked "fact" just because you couldn't check it.
  - **Ground to *today* — the current day, not just the year — and re-verify on every build.**
    You know today's date; use it: run **recency-bounded** searches (this month / the last few
    weeks for fast-moving topics) and fold in material recent events. Re-check anything
    **time-bound** *every* build (including a regeneration) — never reuse cached research for it
    (cached is fine for *stable* facts): prices, counts, rankings, role-holders, versions,
    status; "current / latest / upcoming" claims; "first / largest / record" superlatives; and
    any **scheduled / dated event** (launch, release, ruling, earnings, election, deadline). For
    a dated event, check whether it has **already happened as of today** and write the correct
    status/tense — a "planned / upcoming" item whose date has passed is **completed**; a
    "leading / latest" thing may since have been superseded. Date the deck **"as of \<day month
    year\>"**; if the newest *full-year* metric is last year's, label it and add the current
    year-to-date figure rather than presenting old data as current.
  Carry the verified outline + source log into the **Content plan**, where the user
  approves it — a no-source deck is gated the same as any other: once at the CONTENT
  checkpoint (Step 1), then again at the DESIGN checkpoint (Step 2).

## Long-source mode — classify, map, triage, deep-read the load-bearing 20%

- **A long source (a book / very long PDF / large corpus / multi-volume set)** — one you can't read
  faithfully in a single pass — is NOT read front-to-back: a faked linear read either overflows or,
  worse, *fits* and goes shallow, then invents plausible-but-absent points. Run the planner's
  **Long-source mode** (`agents/content-planner.md` §1): (1) **classify size deterministically** —
  PDF/EPUB → `python scripts/extract_pdf.py map <src>` (CJK-correct load + token estimate); `.docx`/
  `.md`/Google-Doc/web → convert to PDF first or use a `wc`-style count (**never raw `wc -w` on CJK
  text — it undercounts ~6–30×; count CJK chars ÷ 2 + Latin words, or convert to PDF and let `map`
  do it**); a code repo → size the file
  tree; **multi-file → sum across files** (once the set is over-threshold, convert every non-PDF
  member `office`→PDF so pages/provenance exist uniformly) — recorded as the brief's `source size:`
  field; over
  ~40–50 pp (or a token estimate that won't fit one pass) FORCES the mode, (2) anchor on purpose FIRST,
  (3) **map the structure** — TOC/bookmarks + density; **no TOC? `extract_pdf.py headings <src>`**
  reconstructs a skeleton by font-size outlier (recorded in the plan), (4) read **only the chapters
  you'll build-around/summarise** into page-tagged notes (`extract_pdf.py text <src> <start> <end>`;
  fan out the *reading*, synthesise as one mind; `cut` chapters are dispositioned from the skeleton,
  unread), (5) **deep-read *verbatim* only the load-bearing ~20%**, tracing every slide-bound claim
  to a real page (`<file>:p.NNN`; a chapter note is corroboration, not a source), extracting figures
  **per page** from the plan's locators (never `autofig` the whole book). The plan then carries a
  **Source-coverage map** (every skeleton section → built-around / summarised / cut) so the SELECTION
  is explicit — on a book the biggest risk is building around the *wrong slice*, not misreading one
  figure. **Dispatch mechanics — the selection FYI must land BEFORE the deep-read, so an
  over-threshold source makes the planner dispatch TWO-PHASE:** phase 1 (steps 0–3) returns the
  `source size:` + skeleton + draft coverage map, the coordinator posts the selection FYI in chat
  (a stop normally, an FYI under the auto-waiver) and gets the slice confirmed/adjusted, THEN phase 2
  (steps 4–6) runs the verbatim deep-read on the confirmed slice — a one-shot dispatch has no user
  channel mid-run, so a single-phase dispatch silently converts the "early" FYI into a post-hoc one
  (the plan records `selection FYI: posted <when> · slice confirmed/adjusted`, which the checkpoint
  precondition checks). An inline-run planner just posts the FYI directly at the same point.
  A **scanned / image-only or DRM-locked** PDF yields no extractable text (`map`/`text` print
  a `⚠ NO extractable text` warning) — say so and ask for a text version, OCR, or the specific
  chapters, never hallucinate the contents.
