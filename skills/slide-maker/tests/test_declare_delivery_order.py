#!/usr/bin/env python3
"""`declare_delivery` hashes the file on disk, so calling it before the save is a silent trap.

🔴 MEASURED, on a real 12-page build. The docstring said "call it beside the save"; `beside` reads
as either side, and called BEFORE `prs.save(...)` it records no hash at all on a first build and
the PREVIOUS build's hash on every rebuild. Every later `--gate-check` then reported

    🔴 EDITED SINCE BUILD: … Somebody saved over it — Reconcile first: scripts/extract_deck.py

on a file nobody had touched, and the message named the ONE cause it could not know while staying
silent about the mechanical one that was actually true. That is a round-trip and a wrong diagnosis
for any agent that writes the call in the order the docstring allowed.

Three things are pinned here: the call FAILS LOUDLY when the deck does not exist yet, a correct
build records a hash that MATCHES, and the mismatch message DIAGNOSES the ordering from the build
script instead of blaming a person.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk      # noqa: E402
import render_deck as rd  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def _deck(td: Path, name="t.pptx"):
    prs = dk.blank_deck(13.333, 7.5)
    s = dk.add_slide(prs)
    dk.text(s, 1, 1, 8, 1, [[("hello", 40, dk.DEEP, True, False)]])
    return prs, td / name


# ── 🔴 CALLED TOO EARLY: loud, not silent ───────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    prs, out = _deck(td)
    try:
        dk.declare_delivery(str(out), "presented", builds="static")
        fails.append("declare_delivery accepted a deck that does not exist yet — it wrote a record "
                     "with no hash, which is the whole trap: every later gate-check reports "
                     "EDITED SINCE BUILD on a file nobody touched")
    except FileNotFoundError as exc:
        check("AFTER prs.save" in str(exc),
              "it raised, but the message does not say WHICH order is right: {}".format(exc))
    check(not (td / ".deck-gates.json").exists(),
          "a record was written anyway — the raise must happen before anything is recorded")

# ── the CORRECT order records a hash that matches ───────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    prs, out = _deck(td)
    prs.save(str(out))
    dk.declare_delivery(str(out), "presented", builds="static")
    rec = json.loads((td / ".deck-gates.json").read_text(encoding="utf-8"))
    real = hashlib.sha256(out.read_bytes()).hexdigest()
    check(rec.get("deck_sha256") == real,
          "the correct order still does not record the deck's real hash: {!r} vs {!r}"
          .format(str(rec.get("deck_sha256"))[:16], real[:16]))

# ── 🔴 THE MESSAGE DIAGNOSES, it does not blame ─────────────────────────────────────────────────
BAD = '''import deckkit as dk
OUT = "t.pptx"
prs = dk.blank_deck(13.333, 7.5)
dk.declare_delivery(str(OUT), "presented")
prs.save(str(OUT))
'''
GOOD = '''import deckkit as dk
OUT = "t.pptx"
prs = dk.blank_deck(13.333, 7.5)
prs.save(str(OUT))
dk.declare_delivery(str(OUT), "presented")
'''
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    prs, out = _deck(td, "t.pptx")
    prs.save(str(out))
    (td / "build_t.py").write_text(BAD, encoding="utf-8")
    hint = rd._sha_mismatch_hint(str(out), {})
    check("BEFORE `prs.save" in hint and "NOT an edit" in hint,
          "a build script with the calls in the WRONG order was not diagnosed; the reader is sent "
          "to reconcile edits nobody made: {!r}".format(hint[:160]))
    check("extract_deck" not in hint,
          "the wrong-order case still points at the reconcile path, which cannot help here")

    (td / "build_t.py").write_text(GOOD, encoding="utf-8")
    hint2 = rd._sha_mismatch_hint(str(out), {})
    check("Somebody saved over it" in hint2,
          "with the calls in the RIGHT order a mismatch IS a real edit and must say so: {!r}"
          .format(hint2[:160]))
    check("declare_delivery` AFTER" in hint2 or "AFTER\n" in hint2 or "AFTER `prs.save" in hint2,
          "even the real-edit message should name the other cause — it is the cheaper one to "
          "check and the reader cannot tell them apart: {!r}".format(hint2[:200]))

    # unreadable build script: neither cause may be asserted as fact
    (td / "build_t.py").unlink()
    hint3 = rd._sha_mismatch_hint(str(out), {})
    check(isinstance(hint3, str) and hint3.strip(),
          "with no build script to read, the hint vanished instead of degrading")

# ── the docstring no longer allows the wrong reading ────────────────────────────────────────────
doc = dk.declare_delivery.__doc__ or ""
check("AFTER" in doc, "the docstring stopped saying AFTER the save — `beside` reads as either "
                      "side, and that ambiguity is what shipped the bug")
check("beside the save" not in doc, "the ambiguous wording is back")

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_declare_delivery_order] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
