#!/usr/bin/env python3
"""A deck's PURPOSE declares content it is not finished without — checked against the built file.

`references/design-by-purpose.md` carries nine purpose recipes, and measured by grep NOTHING
consumed it: every per-purpose rule in that file was advisory by construction, so a build could
ignore it line by line and no gate would know. Four genres with the most rigid conventions were
missing from the list entirely — grant proposal, progress/guidance committee, journal club,
clinical case presentation — and three of those are among the most common decks an academic makes.

This is the same mechanism `check_surface.py` applies to SURFACES, generalised to genres, and for
the same measured reason: the shape of a genre is exactly what an author under time pressure drops.
A poster drops methods and limitations; a grant deck drops feasibility and risk; a committee deck
drops the ask and becomes a status update.

    MISSING SECTION   the purpose declares a section and nothing in the deck names it
    FIDELITY NOTE     the one fidelity rule this genre carries beyond never-invent (always printed,
                      never a finding — it is a rule for prose, which no scan can judge)

🔴 WHAT IT IS AND IS NOT. It asks whether the deck NAMES the thing, not whether it does it well. A
grant deck can name its risks in two words and pass; judging whether the mitigation is credible is
the critic's job and always will be. The cheap catch is the one worth having — a grant deck with no
feasibility section and a committee deck with no ask are not weak decks, they are decks missing a
section their audience is required to score.

🔴 NO BINDING, NO CLAIM. A deck whose recorded purpose matches no registry entry reports NOT
CHECKED and exits 2. Guessing a genre would be worse than checking nothing: applying a clinical
case's section list to a product pitch would fire four times and teach the author to ignore it.

    python3 scripts/check_purpose.py <deck.pptx> [--purpose "<recorded purpose>"] [--json]
    python3 scripts/check_purpose.py --selftest

Exit 0 clean · 1 findings · 2 could not run / nothing bound.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def deck_text(prs):
    """Every run of text in the deck, lowercased — including speaker notes.

    🔴 Notes count. A committee deck whose ask is spoken rather than printed has the section; this
    check asks whether the deck CARRIES it, not whether it is set in 28pt. Excluding notes would
    fire on exactly the decks that moved their sentences where this skill tells them to.
    """
    out = []
    for slide in prs.slides:
        for t in slide._element.iter(_A + "t"):
            if t.text:
                out.append(t.text)
        try:
            if slide.has_notes_slide:
                nt = slide.notes_slide.notes_text_frame.text
                if nt:
                    out.append(nt)
        except Exception:
            pass
    return " ".join(out).lower()


def recorded_purpose(gates):
    """The purpose string a record carries, across BOTH schemas — or ''.

    Looks at the shared `.deck-gates.json` (`interview.picks[axis=purpose]`, then `interview.goal`)
    and the Codex evidence shape (`design.purpose`, `purpose`). The two runtimes name this
    differently and always have; reading only one is how a floor quietly stops applying to half the
    decks (this repo has been through that three times — see check_gate_parity).
    """
    if not isinstance(gates, dict):
        return ""
    bits = []
    iv = gates.get("interview")
    if isinstance(iv, dict):
        for row in (iv.get("picks") or []):
            if isinstance(row, dict) and row.get("axis") in ("purpose", "angle"):
                bits.append(str(row.get("value") or ""))
        for k in ("goal", "purpose"):
            if iv.get(k):
                bits.append(str(iv[k]))
        # 🔴 `interview.record` is literally "the user's answers, or the auto-carved rationale" in
        # the Codex evidence schema, and on a SUPERVISED Codex run it is often the only place the
        # genre is written down at all: `delegated_picks` requires a `purpose` axis, but only on a
        # deck whose checkpoints were delivered as `auto`. Measured on the real scaffold: the Codex
        # schema has NO `design.purpose` and no `purpose` key anywhere, so without this the gate
        # would exist on that runtime and never be able to bind — the exact parity failure
        # check_gate_parity cannot see, because both paths DO call the checker.
        if iv.get("record"):
            bits.append(str(iv["record"]))
    dp = gates.get("design_plan") or gates.get("design")
    if isinstance(dp, dict):
        for k in ("purpose", "audience"):
            if dp.get(k):
                bits.append(str(dp[k]))
    for k in ("purpose", "deck_purpose"):
        if gates.get(k):
            bits.append(str(gates[k]))
    ab = (gates.get("content") or {}).get("audience_brief") if isinstance(
        gates.get("content"), dict) else None
    if isinstance(ab, dict):
        if ab.get("who"):
            bits.append(str(ab["who"]))
        # the DECISIONS name the genre when `who` does not: a grant deck's audience is "a review
        # panel", which says nothing, while its decisions say "fund it or not".
        for row in (ab.get("decisions") or []):
            if isinstance(row, dict) and row.get("decision"):
                bits.append(str(row["decision"]))
    return " ".join(b for b in bits if b)


def _names(term, blob):
    """Does `blob` NAME `term`? Word-START boundary for Latin, plain substring for CJK.

    🔴 Naive substring matching made three of these checks VACUOUS, which is worse than having no
    check at all — it passes every deck and teaches the reader that the gate is noise. Measured on
    a deck containing only "Our action plan for the project", "The benefit of this approach" and
    "This is a summary":

        clinical_case/investigations   satisfied by "ct"  inside a-CT-ion / proje-CT
        job_talk/fit                   satisfied by "fit" inside bene-FIT
        product_pitch                  reported NOTHING missing at all

    The boundary is on the START only, never the end, because several terms are deliberate
    PREFIXES — "feasib" must match feasibility and feasible, "demo" must match demonstration. A
    trailing boundary would silently break those, which is the same class of quiet failure.
    A term with no letters or digits at all (`%`) has no word boundary to anchor to and falls back
    to substring.
    """
    if any(ord(c) > 0x2E80 for c in term):
        return term in blob                       # CJK has no word boundaries
    if not any(c.isalnum() for c in term):
        return term in blob                       # e.g. "%" — nothing to anchor
    return re.search(r"(?<![a-z0-9])" + re.escape(term), blob) is not None


def check(pptx, purpose_text, *, extra_terms=None, waive=None):
    """(problems, facts). problems = [(code, message), ...]. Raises when nothing binds."""
    import purposes
    from pptx import Presentation

    p = purposes.match(purpose_text)
    if p is None:
        mode = purposes.not_a_genre(purpose_text)
        if mode:
            # a silent NOT CHECKED here would be a worse answer than a question: the reader HAS a
            # genre, they just recorded the room instead of the argument.
            raise RuntimeError(
                "the recorded purpose %r names a DELIVERY MODE, not a genre — %s"
                % ((purpose_text or "")[:60], mode))
        raise RuntimeError(
            "no registry purpose binds to the recorded purpose %r — nothing was checked. That is "
            "correct when the deck is a genre this registry does not carry (a product pitch, a "
            "teaching deck); guessing a genre would fire a whole section list at the wrong deck. "
            "`python3 scripts/purposes.py --list` shows what is registered."
            % (purpose_text or "<nothing recorded>")[:80])

    prs = Presentation(pptx)
    blob = deck_text(prs)
    more = {str(k).lower(): list(v) for k, v in (extra_terms or {}).items()}
    problems = []
    facts = {"purpose": p.name, "label": p.label, "fidelity": p.fidelity,
             "sections": [lbl for lbl, _t in p.required_sections], "missing": [],
             "slides": len(prs.slides._sldIdLst)}
    if waive:
        facts["waived"] = waive
        return [], facts
    for label, keys in p.required_sections:
        keys = tuple(keys) + tuple(more.get(label.lower(), ()))
        if not any(_names(str(k).lower(), blob) for k in keys):
            facts["missing"].append(label)
            problems.append((
                "MISSING SECTION",
                "nothing in this %s names %s (looked for: %s). This genre's audience is asked to "
                "judge against that section, so a deck without it is not a lean deck — it is a "
                "deck missing something the room needs. If it IS there under a word this list does "
                "not know (another language, a field's own term), add it to "
                "`design_plan.purpose_section_terms` rather than waiving the check."
                % (p.label, label, ", ".join(keys[:4]))))
    return problems, facts


def _selftest():
    import purposes
    bad = []
    # binding: both languages, and a genre OUTSIDE the registry must bind to nothing
    for text, want in (("PhD guidance committee meeting", "committee"),
                       ("年度考核进展汇报", "committee"),
                       ("ERC Starting Grant", "grant"),
                       ("journal club on a MICCAI paper", "journal_club"),
                       ("组会读论文", "journal_club"),
                       ("tumour board", "clinical_case"),
                       ("a product pitch to investors", "investor_pitch"),   # moved when that genre was registered
                       ("a sales pitch to a hospital", "product_pitch"),
                       ("an ethics committee submission", None),
                       ("", None)):
        got = purposes.match(text)
        name = got.name if got else None
        if name != want:
            bad.append("%r bound to %r, wanted %r" % (text, name, want))
    # every registered purpose must declare at least one section, or it checks nothing
    for p in purposes.PURPOSES:
        if not p.required_sections:
            bad.append("%s declares no required sections — it would always pass" % p.name)
        if not p.binds_on:
            bad.append("%s has no binding terms — it could never be reached" % p.name)
    # a term list of one English word is a check that fires on every Chinese deck
    for p in purposes.PURPOSES:
        for lbl, terms in p.required_sections:
            if not any(any(ord(ch) > 0x2E80 for ch in t) for t in terms):
                bad.append("%s/%s has no non-Latin synonym — it would fire on every CJK deck"
                           % (p.name, lbl))
    # both record schemas must be readable
    shared = {"interview": {"picks": [{"axis": "purpose", "value": "guidance committee"}]}}
    codex = {"design": {"purpose": "tumour board case presentation"}}
    if purposes.match(recorded_purpose(shared)) is None:
        bad.append("the shared .deck-gates.json shape was not read")
    if purposes.match(recorded_purpose(codex)) is None:
        bad.append("the Codex evidence shape was not read")
    # 🔴 THESE DOCS ARE HAND-COPIES OF THIS REGISTRY, AND HAND-COPIES DRIFT.
    # Both files list the genres and their sections in prose, because that is where each runtime's
    # agent LEARNS the genres exist — `design-by-purpose.md` on the shared path, `codex-runtime.md`
    # on the Codex one. A genre absent from the doc its runtime reads is one that run never uses.
    # Measured: writing that list out by hand got 1 of 12 wrong within minutes (it said "lab
    # meeting", the colloquial trigger, where every gate message says `research_meeting`), so an
    # agent grepping the doc for the name in its own error found nothing. Not a style check: it is
    # the doc-vs-code drift that makes a capability invisible to whichever runtime reads that file.
    COUNTS = {11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
              17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"}
    REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
    # (file, anchor, span) — an anchor bounds the check to the paragraph that makes the claim;
    # None means the whole file is the genre reference.
    DOCS = (("codex-runtime.md", "The deck's GENRE may declare required content", 2400),
            ("design-by-purpose.md", None, None))
    total = len(purposes.PURPOSES) + len(purposes.NOT_A_GENRE)
    for fname, anchor, span in DOCS:
        try:
            doc = open(os.path.join(REF, fname), encoding="utf-8").read()
            chunk = doc if anchor is None else doc[doc.index(anchor):doc.index(anchor) + span]
        except (OSError, ValueError) as exc:
            bad.append("could not read the genre reference in references/%s (%s) — that file is "
                       "where one runtime learns these genres exist" % (fname, exc))
            continue
        para = " ".join(chunk.lower().split())
        for p_ in purposes.PURPOSES:
            if p_.name.replace("_", " ") not in para:
                bad.append("references/%s never names %r — every gate message prints that exact "
                           "name, so an agent grepping its own error finds nothing" % (fname, p_.name))
            for lbl, _terms in p_.required_sections:
                if lbl.lower() not in para:
                    bad.append("references/%s omits section %r of %r — a doc that understates a "
                               "genre's content reads as complete, which is worse than omitting it"
                               % (fname, lbl, p_.name))
        for _key in purposes.NOT_A_GENRE:                 # the key is a TUPLE of trigger words
            medium = _key[0] if isinstance(_key, tuple) else _key
            if medium not in para:
                bad.append("references/%s never mentions %r as a DELIVERY MODE — that path would "
                           "look like it silently checks nothing there" % (fname, medium))
        word = COUNTS.get(total)
        if word is None:
            bad.append("the registry now holds %d entries, outside COUNTS in this selftest — extend "
                       "the map so each doc's stated count keeps being checked" % total)
        elif word not in para:
            bad.append("references/%s does not say %r where it states its coverage, but the registry "
                       "now holds %d entries — the stated count has gone stale" % (fname, word, total))

    for b in bad:
        print("  ✗", b)
    print("[purpose] selftest %s" % ("FAILED" if bad else "ok"))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", nargs="?")
    ap.add_argument("--purpose", default=None,
                    help="the recorded purpose; read from .deck-gates.json beside the deck if omitted")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--waive", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.pptx:
        ap.error("a deck path is required")
    text = a.purpose
    if text is None:
        from pathlib import Path
        rec = Path(a.pptx).resolve().parent / ".deck-gates.json"
        try:
            text = recorded_purpose(json.loads(rec.read_text()))
        except Exception as exc:
            # 🔴 "no purpose recorded" and "could not READ the record" are different claims and
            # this used to print the first for both. Measured: macOS withdrew read access to
            # ~/Downloads mid-session (a documented TCC behaviour), the read raised
            # PermissionError, and the gate reported a deck with a perfectly good purpose row as
            # having recorded nothing — sending the reader to fix a record that was already right.
            print("[purpose] NOT CHECKED — could not read %s (%s: %s). That is a different problem "
                  "from an unrecorded purpose: the record may be fine and unreadable from here."
                  % (rec, exc.__class__.__name__, exc))
            print("          Pass the purpose directly with --purpose '<…>' to check anyway.")
            return 2
    try:
        problems, facts = check(a.pptx, text, waive=a.waive)
    except Exception as exc:
        print("[purpose] NOT CHECKED — %s" % exc)
        print("          NOT the same as clean.")
        return 2
    if a.json:
        print(json.dumps({"problems": [{"code": c, "why": m} for c, m in problems],
                          "facts": facts}, indent=1, ensure_ascii=False))
    print("[purpose] bound to %r (%s)" % (facts["purpose"], facts["label"]))
    if facts.get("fidelity"):
        print("[purpose] FIDELITY NOTE — %s" % facts["fidelity"])
    for c, m in problems:
        print("[purpose] ✗ %s: %s" % (c, m))
    if not problems:
        print("[purpose] every declared section is named: %s" % ", ".join(facts["sections"]))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
