# Efficiency and iteration — the measurements behind Step 0's efficiency rules

The rules themselves are stated in SKILL.md ("Work efficiently"); this file keeps the measured cost model, the full `deck_cycle.py` behaviour and the canon-probe notes. Moved verbatim from SKILL.md (2026-11-07).


## Round-trips and context

- **Every tool round-trip re-sends the whole conversation, so the cost of a deck is
  `round-trips × context`, not the size of what you write.** Measured on one 12-page build: 122
  calls, 37M tokens, of which **98.5% was context re-sent** and 0.6% was actual output; context ran
  ~302k per call by mid-build. Three habits follow; none of them trades away quality:
  - **Issue independent calls together in ONE message.** That same build averaged *1.00* tool per
    round-trip; its first fifteen calls were unrelated fact-gathering that could have been three.
    Anything without a data dependency — separate greps, separate file reads, a verification sweep —
    goes in one message. A dependency chain (build → render → lint → look) obviously cannot.


## Repairs and the canon probe

  - **Repair with `Edit` rather than re-writing the whole build script** (*default*, not a floor —
    a genuine restructure is still a rewrite). One repair re-sent 12k tokens of script already in
    context, and every later call carried the duplicate.
  - **The canon is cited here in prose and MEASURED in `scripts/canon_probe.py` — know which is
    which.** Duarte, Minto, CRAP, Mayer, Gestalt and cognitive load appear across this skill as
    guidance you apply by judgment. Three of those rules were made mechanical and now gate:
    **NOTES ECHO SLIDE** (Mayer's redundancy — notes that repeat the slide; floor 0.75, real decks
    top out at 0.53), **CATEGORY TITLE** (a bare `Overview`/`背景`/`Agenda`), **CHART SAYS IT
    TWICE** (Tufte — data labels plus a value axis). Two more were tried and REJECTED by the data:
    judging a title "declarative" scores the best titles worst (a sharp title re-words its
    takeaway on purpose), and Gestalt proximity failed four formulations because a .pptx records
    coordinates and no notion of which shapes belong together. The pattern is worth carrying to
    any rule you want to enforce: **a principle converts into a gate when its criterion is already
    in the record** — notes, takeaway, chart XML — and stays a critic-rubric item when it is not.


## deck_cycle.py in full

  - **Iterate with `deck_cycle.py`, so one fix costs one round-trip.**
    `python3 scripts/deck_cycle.py build_<deck>.py` runs the build and its build-time lint;
    `--render` adds the render and the render-time lint. Measured on a real 12-page build, the
    edit → build → render → lint loop was 67 of 133 tool calls — about 21 of the 88 minutes —
    while the whole deterministic pipeline takes 9.1 seconds. The steps are not slow; asking for
    them one at a time is. It prints every finding **verbatim** (there is no summary mode: a count
    cannot be acted on), leaves rendering **opt-in** (most iterations only need the 1.8s geometry
    pass, and forcing a 5.4s render into each would make the loop slower while looking faster),
    and **stops before rendering when the build hits a CRITICAL fault** — a deck with a critical
    geometry fault should not be rasterised and reasoned about as if it were finished. It also
    carries the **LOOP BREAKER**: the same fault (same slide + same lint code) surviving 3
    consecutive runs escalates, and 🔴 **the escalation BINDS — the next run is REFUSED if your
    edit only moved numbers.** "Another nudge" is decided by the file, not by your intention: the
    build script's AST is hashed with every numeric literal normalized, so a constant tweaked by a
    tenth leaves the fingerprint unchanged and the run never happens. Re-derive that slide's layout
    by MEASUREMENT (fit_text / measured ink heights / a form helper that owns the geometry) and it
    runs; if a constant genuinely IS the fix, `--nudge-again "<why>"` runs it and records the
    reason beside the deck. Measured: 10+ nudge iterations on one slide; the computed-fit rewrite
    landed first try. It replaces nothing: `render_deck.py` and `lint_deck.py` behave as before.
    After every build that completed it also **snapshots the deck** into `<deck-dir>/.versions/`
    (`scripts/deck_versions.py`; unchanged content makes no new version) — Step 6 shows the user the diff.


## render_deck --fast in full

**Iterating on a deck you already rendered? Add `--fast`.** `render_deck … --fast` fingerprints
every slide (its XML + rels + the bytes of the media it references, mixed with a deck-global digest
covering the theme/master/layouts/canvas size) against the previous run, then re-renders **only the
slides that changed** — it subsets the pptx to those slides, converts that, and overwrites just their
PNGs. Measured on an 18-slide deck: a full render is ~2.8s, a one-slide change **~2.3s**, and a run
where nothing changed **0.07s**. 🔴 **The no-op round is the big win, not the one-slide round** — a
no-op never starts LibreOffice, while any real render pays one ~2.5s start that dwarfs the page work,
so a one-slide round saves about a fifth. Never skip a re-render on the belief that rendering is
expensive; it is a couple of seconds. Output is byte-identical to a full render (verified), so the
critic and the render-time lint see exactly what they would have seen anyway. It falls back to a full
render — and says why — whenever the mapping could be wrong: slide count changed, every slide changed,
no cache, or the deck contains **auto slide-number fields** or **hidden slides** (LibreOffice drops
hidden slides from the PDF, so page N stops being slide N — a full render now warns loudly and
refuses to cache when the page count and slide count disagree). **Use it for the actor-critic fix rounds
and for post-delivery tweaks** ("change slide 7 to a chart"); use a plain full render for the first
render of a deck and whenever you pass `--deliverables`.
