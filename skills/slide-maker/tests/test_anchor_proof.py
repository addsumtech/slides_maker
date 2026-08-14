#!/usr/bin/env python3
"""The ANCHOR PROOF contract, and the anti-drift property that is its whole reason for existing.

Step 4's proof used to be ONE rendered page. It proved the aesthetic risk survived the build and
nothing else — so a design approved on the deck's most spacious page could still fail to hold its
densest one, and a palette and type scale chosen entirely against text could still meet their first
native chart at Step 5, where the fix is a rebuild. Three anchors, three different failures.

The second half of this file matters more than the first. The rule is enforced by TWO gate paths —
`render_deck.py --gate-check` (shared, `.deck-gates.json`) and `codex_delivery_gate.py` (Codex,
`.codex-deck-evidence.json`) — and they have already diverged once on this exact field: the file key
was spelled `path` in one and `png` in the other, so a bridged run wrote what its own gate demanded
and was rejected by the other for the key name alone. The fix was not to be more careful; it was to
make one module the only place the rule is written. The import tests below are what keep it that
way, because a re-implementation would look perfectly correct in review — it just would not be the
same rule six months later.
"""
import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import anchor_proof as ap                                      # noqa: E402

ok, bad = [], []


def want(cond, good, wrong):
    (ok if cond else bad).append(good if cond else wrong)


def A(role, slide, png="p.png", **kw):
    return dict({"role": role, "slide": slide, "png": png}, **kw)


THREE = [A("signature", 3), A("complex", 5, "c.png"), A("data", 7, "d.png")]
SL = {1, 2, 3, 4, 5, 6, 7, 8}

# ------------------------------------------------------------------ required_count
want(ap.required_count(12) == 3 and ap.required_count(3) == 3,
     "a deck of three slides or more owes three anchors",
     "required_count is wrong on normal decks: %r / %r" % (ap.required_count(12),
                                                           ap.required_count(3)))
want(ap.required_count(2) == 2 and ap.required_count(1) == 1,
     "a deck smaller than three owes only as many anchors as it has slides — demanding three "
     "distinct anchors from a 2-page deck would buy a relabelled page, not a proof",
     "small decks are asked for more anchors than they have slides")
want(ap.required_count(0) == 1 and ap.required_count(None) == 3,
     "a zero or unreadable slide count degrades to a floor rather than to zero — an unparseable "
     "deck must never mean 'no anchors required'",
     "a bad slide count switches the requirement off")

# ------------------------------------------------------------------ normalise / anchor_file
leg = ap.normalise({"slide": 3, "png": "p.png"})
want(leg is not None and len(leg) == 1 and leg[0]["role"] == "signature",
     "the LEGACY single-anchor dict parses as one `signature` anchor — evidence files written "
     "before this change stay readable and fail on the COUNT rule with an instruction, rather "
     "than dying with a parse error where guidance belongs",
     "the legacy dict shape no longer parses: %r" % (leg,))
want(ap.normalise("proof.png") is None and ap.normalise(None) is None,
     "a bare string or None is not an anchor record",
     "a non-record was accepted as an anchor list")
want(ap.normalise([A("signature", 1), "nope"]) is None,
     "a list with a non-dict entry is refused whole rather than silently dropping the entry — a "
     "silently dropped anchor is an anchor nobody rendered",
     "a malformed list entry was silently discarded")
want(ap.anchor_file({"png": "a.png"}) == "a.png"
     and ap.anchor_file({"path": "b.png"}) == "b.png",
     "both key spellings resolve — the exact divergence that once rejected valid bridged evidence",
     "the two documented key spellings do not both resolve")
want(ap.anchor_file({"png": "   "}) is None and ap.anchor_file({}) is None,
     "a blank or absent file key is None, not an empty path that fails later at open()",
     "a blank file key was accepted")

# ------------------------------------------------------------------ faults
want(ap.faults(THREE, n_slides=8, expected_slides=SL) == [],
     "a well-formed three-anchor set is clean",
     "a valid anchor set was faulted: %r" % ap.faults(THREE, n_slides=8, expected_slides=SL))

f = ap.faults({"slide": 3, "png": "p.png"}, n_slides=12, expected_slides=set(range(1, 13)))
want(any("owes 3" in x for x in f) and any('"complex"' in x and '"data"' in x for x in f),
     "the legacy single anchor on a real deck is refused, and the message NAMES the two missing "
     "anchors instead of printing a count",
     "the count fault does not name what is missing: %r" % f)

f = ap.faults([A("signature", 1), A("complex", 2), A("complex", 3)], n_slides=8, expected_slides=SL)
want(any("same role" in x for x in f),
     "two anchors claiming one role are refused — the three prove three different failures, so "
     "one page cannot hold two of the jobs",
     "duplicate roles passed: %r" % f)

f = ap.faults([A("signature", 3), A("complex", 3), A("data", 3)], n_slides=8, expected_slides=SL)
want(any("same slide" in x for x in f),
     "three anchors on one slide are refused — proving one page three times proves one page",
     "duplicate slides passed: %r" % f)

f = ap.faults([A("data", 1), A("complex", 2), A("data", 3)], n_slides=8, expected_slides=SL)
want(any("no `signature` anchor" in x for x in f),
     "a set with no signature anchor is refused — the risk is the thing most likely to have been "
     "sanded back to the safe catalogue during the build",
     "a signature-less anchor set passed: %r" % f)

f = ap.faults([A("signature", 3), A("complex", 5), A("data", 99)], n_slides=8, expected_slides=SL)
want(any("not a final slide" in x for x in f),
     "an anchor pointing outside the deck is refused",
     "an out-of-range anchor slide passed: %r" % f)

f = ap.faults([A("signature", 3), A("complex", 5), dict(A("data", 7), png=None, path=None)],
              n_slides=8, expected_slides=SL)
want(any("needs the rendered PNG" in x for x in f),
     "an anchor with no rendered file is refused — a promise is not a proof",
     "a file-less anchor passed: %r" % f)

f = ap.faults([A("signature", "three"), A("complex", 5), A("data", 7)],
              n_slides=8, expected_slides=SL)
want(any("must be the integer slide number" in x for x in f),
     "a non-integer slide number is refused by name",
     "a string slide number passed: %r" % f)

f = ap.faults([A("signature", 3), A("kicker", 5), A("data", 7)], n_slides=8, expected_slides=SL)
want(any("kicker" in x and "signature | complex | data" in x for x in f),
     "an invented role is refused AND the vocabulary is printed",
     "an invented role passed or the vocabulary was not shown: %r" % f)

# ------------------------------------------------------------------ the restraint carve
f = ap.faults([A("complex", 5), A("data", 7)], n_slides=8, expected_slides=SL, carved=True)
want(not any("no `signature` anchor" in x for x in f),
     "under the documented conservative/'deliberately restrained' carve a supplied set may omit "
     "the signature anchor — the deck declared it took no aesthetic risk, so there is none to prove",
     "the carve does not release the signature anchor: %r" % f)
want(not any('a "signature" anchor' in x for x in f),
     "…and the count message does not then ask for the anchor the carve just released",
     "the carved count message still demands a signature anchor: %r" % f)
f = ap.faults([A("complex", 5), A("data", 7)], n_slides=8, expected_slides=SL, carved=False)
want(any("no `signature` anchor" in x for x in f),
     "…and the release is genuinely conditional: without the carve the same set is refused",
     "the signature anchor is not required even off the carve")

# ------------------------------------------------------------------ THE ANTI-DRIFT PROPERTY
GATES = {"render_deck.py": SCRIPTS / "render_deck.py",
         "codex_delivery_gate.py": SCRIPTS / "codex_delivery_gate.py"}

for name, path in GATES.items():
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = any(
        (isinstance(n, ast.Import) and any(a.name == "anchor_proof" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "anchor_proof")
        for n in ast.walk(tree))
    want(imported,
         "%s imports the shared anchor_proof contract rather than restating it" % name,
         "%s does NOT import anchor_proof — the rule is written twice again, which is exactly how "
         "the two gate paths diverged on this field before" % name)

    src = path.read_text(encoding="utf-8")
    # The old local re-implementation, verbatim. Its return would be a silent fork of the contract.
    want('proof.get("png") or proof.get("path")' not in src,
         "%s no longer resolves the anchor file key itself — that two-spelling rule lives in one "
         "place now" % name,
         "%s re-implements the png/path resolution locally; when the shared module changes, this "
         "copy will not" % name)

# The recorded failure this guards: the shared gate's own JSON template drifted behind the fields it
# enforced (it listed six of eight), so copying the template verbatim produced a record that died on
# the gate that printed it.
rd = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
tmpl = [ln for ln in rd.splitlines() if '"signature_proof"' in ln and "'" in ln]
want(tmpl and all('"role"' in ln or "[{" in ln for ln in tmpl),
     "every printed `signature_proof` template in render_deck.py shows the ROLE-bearing list shape "
     "— a template that still shows the single-anchor dict teaches authors to write a record its "
     "own gate now rejects",
     "a printed template still shows the pre-anchor shape: %r" % tmpl)

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print("\n%d passed, %d failed" % (len(ok), len(bad)))
raise SystemExit(1 if bad else 0)
