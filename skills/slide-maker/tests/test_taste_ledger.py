#!/usr/bin/env python3
"""The taste ledger: what this user has already taught, so the next deck does not relearn it.

The module's `--selftest` covers the entry and gate logic. This file covers the two properties that
decide whether the ledger helps or becomes noise: it must ask NOTHING of a fresh install, and an
entry must leave by being PROMOTED to a real gate rather than by being forgotten.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import taste_ledger as tl  # noqa: E402

# 🔴 HERMETIC: point the taste ledger at a path that does not exist. It is USER-LEVEL data,
# so a test that reads the real one passes or fails by whatever the developer happens to
# have taught the skill — the same "passes by luck" class as a hash-salted fixture.
os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/nonexistent/taste-ledger-for-tests.json"

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


r = subprocess.run([sys.executable, str(SCRIPTS / "taste_ledger.py"), "--selftest"],
                   capture_output=True, text=True)
check(r.returncode == 0, "taste_ledger.py --selftest failed:\n{}{}".format(r.stdout, r.stderr))

E = {"id": "icons-are-default", "quote": "为什么这个slide没有icon",
     "rule": "categorical content gets icons by default; a skip needs a category reason",
     "binds_at": "design", "learned_from": {"deck": "melbourne-first-trip", "date": "2026-09-03"},
     "retired_by": ""}

# ── 🔴 A FRESH INSTALL MUST BE ASKED NOTHING ─────────────────────────────────────────────────────
# The ledger is per-user data that ships empty. If an empty ledger demanded a field, every first
# deck on every machine would fail a gate over a file that does not exist yet.
check(not tl.faults(None, []), "an empty ledger demanded something of a design plan")
check(not tl.faults({"boldness": "bold"}, []), "an empty ledger demanded a field")
with tempfile.TemporaryDirectory() as td:
    check(tl.load(Path(td) / "nothing.json") == [],
          "a missing ledger file did not read as empty — a fresh install would crash the gate")

# ── 🔴 THE SELF-LIMITING PROPERTY ────────────────────────────────────────────────────────────────
# A ledger that only grows becomes noise, and noise is indistinguishable from having no ledger.
# An entry that earns a deterministic gate is retired and points at it.
retired = dict(E, retired_by="READ_PLAN_UNSEEN")
check(not tl.faults({}, [retired]),
      "a RETIRED entry still demanded attention — the ledger would grow without bound")
check(tl.active([retired]) == [],
      "active() returned a retired entry; it would be re-listed in every design prompt forever")
check(tl.faults({}, [E]), "a live entry was not required to be read")

# ── it checks that rules were CONSIDERED, never that they were obeyed ────────────────────────────
# A rule can be right to break. A gate that forbids deviation would be worse than the rules it
# enforces — this skill's own taste protocol says defaults are offers, not orders.
check(not tl.faults({"taste_applied": [{"id": E["id"], "applied": False,
                                        "why_not": "this deck has no categorical content at all"}]},
                    [E]),
      "a REASONED deviation was blocked — the ledger must not outrank judgement")
check(tl.faults({"taste_applied": [{"id": E["id"], "applied": False}]}, [E]),
      "an unreasoned skip passed — that is how a taught rule quietly stops binding")

# ── what keeps an entry from being vibes ─────────────────────────────────────────────────────────
for field, why in (("quote", "a rule with no quote is something the assistant decided and "
                             "attributed to the user"),
                   ("rule", "a complaint restated is not an instruction"),
                   ("binds_at", "a rule that binds at no pipeline step is a note")):
    check(tl.entry_faults(dict(E, **{field: ""})), "an entry with no `{}` passed — {}".format(
        field, why))
check(tl.entry_faults(dict(E, learned_from={})),
      "an entry with no origin deck passed — it could never be re-examined when taste changes")

# ── the data must not live in the repo: it is the user's own words ───────────────────────────────
default = tl.ledger_path()
check(ROOT not in default.parents and default != ROOT,
      "the ledger defaults to a path inside the skill repo; a user's verbatim feedback would be "
      "committed to a public git history")

# ── round-trip keeps non-ASCII intact ────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "l.json"
    tl.save([E], p)
    got = tl.load(p)
    check(len(got) == 1 and got[0]["quote"] == E["quote"],
          "the round-trip mangled the quote — a CJK quote must survive verbatim")
    check("\\u" not in p.read_text(encoding="utf-8"),
          "the ledger escaped non-ASCII; the file is meant to be human-readable")

# ── 🔴 THE CODEX SCHEMA CALLS IT `design`, NOT `design_plan` ─────────────────────────────────────
# This module's first version reached for `design_plan` on the Codex path, where that key has never
# existed — so the gate was permanently unsatisfiable there and no non-Claude agent could have
# delivered a deck with a non-empty ledger. Same drift as png/path, third occurrence. One owner now.
check(tl.design_of({"design_plan": {"taste_applied": []}}) == {"taste_applied": []},
      "design_of misses the shared spelling")
check(tl.design_of({"design": {"boldness": "bold"}}) == {"boldness": "bold"},
      "design_of misses the CODEX spelling — the taste gate would be unsatisfiable on that runtime")
for junk in (None, 7, "str", []):
    check(tl.design_of(junk) == {}, "design_of must return {{}} on a malformed record ({!r})".format(junk))
_E2 = dict(E)
check(not tl.faults(tl.design_of({"design": {"taste_applied": [{"id": E["id"], "applied": True}]}}),
                    [_E2]),
      "a Codex record that DID record taste_applied was still rejected")

# ── wired into every gate path, like every other shared contract ─────────────────────────────────
for name in ("render_deck.py", "deck_gates.py", "codex_delivery_gate.py"):
    src = (SCRIPTS / name).read_text(encoding="utf-8")
    check("taste_ledger" in src, "{} does not consult the taste ledger".format(name))
    check("taste_applied" not in src or "import taste_ledger" in src,
          "{} references the field without importing the contract".format(name))

# the registry override isolates the LEDGER too: a real run that set SLIDE_MAKER_REGISTRY to keep the
# user's profile out was still blocked by the two entries in ~/.slide-maker/taste-ledger.json
import os as _os
_saved = {k: _os.environ.get(k) for k in ("SLIDE_MAKER_TASTE_LEDGER", "SLIDE_MAKER_REGISTRY")}
_os.environ.pop("SLIDE_MAKER_TASTE_LEDGER", None)
_os.environ["SLIDE_MAKER_REGISTRY"] = "/tmp/some-isolated-registry"
check(str(tl.ledger_path()) == "/tmp/some-isolated-registry/taste-ledger.json",
      "with SLIDE_MAKER_REGISTRY set, the ledger lives in that registry (got {})".format(tl.ledger_path()))
_os.environ["SLIDE_MAKER_TASTE_LEDGER"] = "/tmp/explicit-ledger.json"
check(str(tl.ledger_path()) == "/tmp/explicit-ledger.json",
      "an explicit SLIDE_MAKER_TASTE_LEDGER still wins over the registry")
for _k, _v in _saved.items():
    if _v is None:
        _os.environ.pop(_k, None)
    else:
        _os.environ[_k] = _v

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_taste_ledger] {}".format("FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
