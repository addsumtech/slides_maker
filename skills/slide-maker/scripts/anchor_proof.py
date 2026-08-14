#!/usr/bin/env python3
"""The ANCHOR PROOF contract — three rendered pages before the other slides exist.

Step 4 has always opened with a signature proof: build the one slide the `signature move:` names,
render it, look at it, and only then author the rest. The ritual is sound and the reason it exists
is measured — you learn the move is wrong having built one slide instead of twenty. But ONE page
proves exactly one thing, the aesthetic risk, and two of the three ways a deck falls apart at the
render are invisible on it:

  · **the design does not FIT the content.** The look is approved on the deck's most spacious page;
    the page carrying nine content units and a caption is where it breaks. "好看但装不下内容".
  · **the chart and the design language are incompatible.** The palette, the type scale and the
    chrome were all chosen against type, and the first real data page is where they meet a
    native chart that obeys none of them.

Both surface at Step 5, after the whole deck is built, at which point the fix is a rebuild — the
exact economics the signature proof was invented to escape. So the proof carries THREE anchors:

    signature   the slide `signature move:` names — the aesthetic risk (unchanged)
    complex     the most content-dense page in the plan — does the design hold the load
    data        the most critical data/conclusion page — does the chart speak the same language

**Why not the cover, which is the obvious third.** The proposal this came from named cover / most
complex / most critical. The cover is already proven twice over: branch (c) renders four full
directions at the direction gate and branch (d) posts a rendered hero at its own 🔴 checkpoint.
Making it an anchor would spend a third of this gate re-proving the one page that already has two
gates, and leave the signature risk unproven. The anchors are chosen to cover what nothing else
covers.

COST. Effectively nothing, which is the point. Measured on an 18-slide deck, a `--slides` render is
~2.9s and a full render ~2.8s — both pay one ~2.5s LibreOffice start, so two extra pages are noise.
They go in the SAME build script and the SAME render call as the signature slide, so the round-trip
count does not move either. What you spend is the authoring of two more slides; what you buy is
finding out that the design cannot hold your densest page while three slides exist instead of twelve.

This module exists so the two gate paths cannot disagree about the contract. `render_deck.py
--gate-check` (the shared path, `.deck-gates.json`) and `codex_delivery_gate.py` (the Codex path,
`.codex-deck-evidence.json`) both enforce it, and they have already diverged once on this very
field — one spelled the file key `path` and the other `png`, so a bridged run wrote what its own
gate demanded and was rejected by the other. A rule written twice is a rule that drifts; both
import this.

File-level checks (existence, size, hash) deliberately stay in each gate: the Codex path binds each
PNG to a SHA-256 and to the final PPTX hash, the shared path checks existence and a size floor, and
flattening those into one function would weaken the stricter of the two.
"""
from __future__ import annotations

# The three jobs an anchor can hold. `signature` is mandatory — it is the original ritual, and the
# risk is the thing most likely to be quietly sanded away during the build.
ROLES = ("signature", "complex", "data")
LEGACY_ROLE = "signature"


def required_count(n_slides):
    """How many anchors this deck owes. Three, unless the deck is smaller than three.

    A 2-slide tiny-ask already skips the whole ritual (SKILL.md Step 4). This bound is for the
    decks in between — a 3-slide deck cannot name three DISTINCT anchors without one page holding
    two jobs, and demanding it would push authors toward relabelling one page rather than proving
    anything.
    """
    try:
        n = int(n_slides)
    except (TypeError, ValueError):
        n = 3
    return max(1, min(3, n))


def normalise(proof):
    """Accept the legacy single-anchor dict or the anchor list; return a list, or None.

    The legacy dict is accepted on PURPOSE rather than rejected on sight: evidence files written
    before this change are still readable, and the run fails on the COUNT rule below with a message
    that says what to add. Rejecting the shape instead would produce a parse error where an
    instruction belongs.
    """
    if isinstance(proof, dict):
        return [dict(proof, role=proof.get("role") or LEGACY_ROLE)]
    if isinstance(proof, list):
        return [p for p in proof if isinstance(p, dict)] if all(
            isinstance(p, dict) for p in proof) else None
    return None


def anchor_file(anchor):
    """The PNG path, under either spelling. See the module docstring for why both are accepted."""
    if not isinstance(anchor, dict):
        return None
    v = anchor.get("png") or anchor.get("path")
    return v if isinstance(v, str) and v.strip() else None


def faults(proof, *, n_slides, expected_slides=None, carved=False):
    """Everything wrong with an anchor-proof record, as human-readable lines. Empty list = clean.

    Does NOT touch the filesystem — each gate does its own file/hash checking at its own strictness.

    `carved` is the documented `boldness: conservative` + "deliberately restrained" escape. Both
    gates still let a carved deck omit the record ENTIRELY — that behaviour predates the anchors and
    breaking it would reject honest evidence files written before this change. What `carved` does
    here is narrower: a carved deck that DOES supply anchors is not required to include the
    `signature` one, because it declared it took no aesthetic risk and there is nothing to prove.

    The asymmetry is deliberate but not ideal, and saying so is the point: a conservative deck still
    has a densest page and still has charts, so the `complex` and `data` anchors would earn their
    keep there too. Requiring them would reject every conservative evidence file already on disk, so
    the carve stays whole-record for now. Anyone tightening it should tighten BOTH gate paths in the
    same change.
    """
    out = []
    anchors = normalise(proof)
    if anchors is None or not anchors:
        return ['`signature_proof` must be a list of anchor records, e.g. '
                '[{"role": "signature", "slide": 6, "png": "render/slide06.png"}, '
                '{"role": "complex", "slide": 9, "png": "render/slide09.png"}, '
                '{"role": "data", "slide": 11, "png": "render/slide11.png"}] — the rendered '
                'evidence that the signature move survived, that the design holds the deck\'s '
                'densest page, and that the charts speak the same visual language.']

    need = required_count(n_slides)
    for i, a in enumerate(anchors):
        where = "signature_proof[%d]" % i
        role = a.get("role")
        if role not in ROLES:
            out.append("%s: role is %r; must be one of %s" % (where, role, " | ".join(ROLES)))
        if not isinstance(a.get("slide"), int):
            out.append("%s: `slide` must be the integer slide number" % where)
        elif expected_slides is not None and a["slide"] not in expected_slides:
            out.append("%s: slide %s is not a final slide of this deck" % (where, a["slide"]))
        if not anchor_file(a):
            out.append('%s: needs the rendered PNG as "png" (or "path")' % where)

    roles = [a.get("role") for a in anchors if a.get("role") in ROLES]
    if len(set(roles)) != len(roles):
        out.append("two anchors claim the same role (%s) — the three anchors prove three different "
                   "failures, so one page cannot hold two of the jobs" % ", ".join(roles))
    if LEGACY_ROLE not in roles and not carved:
        out.append("no `signature` anchor — the aesthetic risk is the one thing most likely to be "
                   "sanded back to the safe catalogue during the build, and it is the anchor this "
                   "ritual started as")

    slides = [a.get("slide") for a in anchors if isinstance(a.get("slide"), int)]
    if len(set(slides)) != len(slides):
        out.append("two anchors point at the same slide (%s) — proving one page three times "
                   "proves one page" % ", ".join(str(s) for s in slides))

    if len(anchors) < need:
        out.append(
            "only %d anchor(s); this deck owes %d. ONE rendered page proves the aesthetic risk and "
            "nothing else: the design that looks right on it can still fail to hold the deck's "
            "densest page, and the charts can still speak a different visual language. Add "
            "%s — same build script, same render call, ~0s more machine time."
            % (len(anchors), need,
               " and ".join('a "%s" anchor' % r for r in ROLES
                            if r not in roles and not (carved and r == LEGACY_ROLE))
               or "the rest"))
    return out
