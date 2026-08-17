#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A WEB-RESEARCHED deck (source_mode == "web") must ship on three floors — 全面 COMPREHENSIVE,
充实 SUBSTANTIAL, 准确 ACCURATE (content-planner.md §2(e)). The Codex delivery gate carries them as
structured fields so the machine checks what the shared content checkpoint states:

  - content.coverage   — the domain enumerated + swept (全面)
  - content.lifecycle  — every featured product/version/entity checked live-vs-discontinued today
  - content.provenance — the checked/confirmed/fixed/cut digest (准确)
  - claim_ledger[*].confidence — HIGH/MED/LOW so LOW/UNVERIFIED facts are visibly cut

Closes the measured gap: a no-source deck shipped thin and headlined two discontinued products
(Sora, Agent Builder) because none of the three floors was recorded or checked anywhere.

🔴 The load-bearing half is what it must stay SILENT on: a 'provided'-source deck traces to its
material and a 'none' stub has no web to sweep — neither should be forced to carry these fields.

Run:  python3 tests/test_web_research_floors.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import codex_delivery_gate as g                                       # noqa: E402

PASS, FAIL = [], []


def ok(c, m):
    (PASS if c else FAIL).append(m)


def content_errors(content):
    """Run check_content over a minimal evidence and return only the web-floor errors (interview /
    arc / slide errors from the stub are irrelevant here and filtered out)."""
    errors = []
    g.check_content({"content": content}, pathlib.Path("."), {1, 2, 3, 4}, errors)
    return errors


LEDGER_OK = [{"claim": "a real checkable claim", "source": "https://example.com/primary",
              "verified": True, "confidence": "HIGH"}]
LEDGER_NO_CONF = [{"claim": "a real checkable claim", "source": "https://example.com/primary",
                   "verified": True}]

FLOORS = {
    "coverage": "the areas enumerated, covered, and cut with reasons",
    "lifecycle": "every product checked live vs discontinued as of today",
    "provenance": {"summary": "checked 16 · confirmed 12 · fixed 5 · cut 4"},
}


def web(**overrides):
    c = {"source_mode": "web",
         "sources": [{"kind": "web", "locator": "https://example.com/source"}],
         "claim_ledger": list(LEDGER_OK)}
    c.update(FLOORS)
    c.update(overrides)
    return c


# ── a complete web deck passes the web-floor checks ──────────────────────────
errs = content_errors(web())
ok(not any("content.coverage" in e for e in errs), "complete web deck: coverage accepted")
ok(not any("content.lifecycle" in e for e in errs), "complete web deck: lifecycle accepted")
ok(not any("content.provenance" in e for e in errs), "complete web deck: provenance accepted")
ok(not any("confidence must be" in e for e in errs), "complete web deck: HIGH confidence accepted")

# ── each missing floor is flagged ────────────────────────────────────────────
ok(any("content.coverage" in e for e in content_errors(web(coverage=None))),
   "missing coverage (全面) is flagged")
ok(any("content.lifecycle" in e for e in content_errors(web(lifecycle=None))),
   "missing lifecycle sweep is flagged")
ok(any("content.provenance" in e for e in content_errors(web(provenance=None))),
   "missing provenance digest (准确) is flagged")
ok(any("content.provenance.summary" in e for e in content_errors(web(provenance={}))),
   "provenance present but empty summary is flagged")
ok(any("confidence must be" in e for e in content_errors(web(claim_ledger=LEDGER_NO_CONF))),
   "a ledger row with no confidence tier is flagged")
ok(any("confidence must be" in e for e in content_errors(
        web(claim_ledger=[{"claim": "x y z claim", "source": "s", "verified": True, "confidence": "maybe"}]))),
   "an invalid confidence value is flagged")

# ── the floors DO NOT apply to a provided-source or none-stub deck ───────────
prov = {"source_mode": "provided",
        "sources": [{"kind": "provided", "path": "README.md", "sha256": "0" * 64}],
        "claim_ledger": LEDGER_NO_CONF}
perrs = content_errors(prov)
ok(not any("content.coverage" in e for e in perrs), "provided deck: coverage NOT required")
ok(not any("content.lifecycle" in e for e in perrs), "provided deck: lifecycle NOT required")
ok(not any("confidence must be" in e for e in perrs), "provided deck: confidence NOT required")

none = {"source_mode": "none", "sources": [], "claim_ledger": []}
nerrs = content_errors(none)
ok(not any("content.coverage" in e for e in nerrs), "none-stub deck: coverage NOT required")
ok(not any("content.lifecycle" in e for e in nerrs), "none-stub deck: lifecycle NOT required")

# ── report ────────────────────────────────────────────────────────────────────
print("\n".join("  ok  " + m for m in PASS))
if FAIL:
    print("\n".join("  XX  " + m for m in FAIL))
print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
