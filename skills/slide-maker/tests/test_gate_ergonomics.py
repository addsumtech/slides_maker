#!/usr/bin/env python3
"""Six defects found by RUNNING the skill end to end on a real deck, not by reading it.

The build that produced them: a 15-slide presented deck, direction gate, bespoke register,
sourced + generated imagery. Everything here is a measurement from that run.

  * **six consecutive `--gate-check` round-trips**, each naming exactly ONE `design_plan` field —
    `boldness` in the wrong dial format, `signature_proof`, `material_probe`, `concept` in the
    wrong shape, `type_scale.body` under the floor, `form_reach`. The section-abort is a
    deliberate, tested contract ("its later checks read values the earlier one validated") and it
    stays; what was missing is somewhere to learn the SHAPES before spending a round-trip on each.
    `deck_gates.py` is that: five of those six are now one pass.
  * **`directions_diversity.py` is a real detector nothing required anyone to run.** On that
    build's first direction set it reports `TOO SIMILAR Brutalist vs Swiss (palette 37.9)` — which
    the author caught by eye — AND `NO BESPOKE DIRECTION`, which the author did not catch at all:
    the "bespoke" candidate carried colours and a skeleton but no `cover_motif`, so the user chose
    from three presets and a colourway. The arc competition is re-scored at hand-off; the design
    competition was a sentence somebody typed.
  * **`presets.apply("terminal")` set Consolas, which macOS does not have** — every measurement in
    a fixed-width register computed in a proportional substitute. `_font_substituted` was one call
    away.
  * **`RULE_THROUGH_TEXT` had no declaration**, so a STRIKE-THROUGH — a rule crossing its own text,
    which is what the mark means — could not be built. Its two siblings both have one.
  * **the builds choice was carried by memory**: the user opted out of appear-builds and `--static`
    still had to be retyped on every lint run or `NO BUILDS` fired on a deck that is static by
    their decision.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

ok, bad = [], []


def check(cond, good, why=""):
    (ok if cond else bad).append(good if cond else "{}{}".format(
        good, (" — " + ("; ".join(map(str, why)) if isinstance(why, list) else str(why)))
        if why else ""))


# ── deck_gates.py: the shapes, before the round-trip ──────────────────────────────────────────
p = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "--selftest"],
                   capture_output=True, text=True)
tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
check(p.returncode == 0 and tail[0].endswith("0 failed"),
      "deck_gates.py --selftest is green ({})".format(tail[0]), (p.stdout or "")[-300:])

import deck_gates                                                            # noqa: E402

filled = deck_gates.template(2)
d = filled["design_plan"]
d.update({"boldness": "bold",
          "concept": {"chosen": "a red line that gets crossed",
                      "rejected": [{"concept": "a deepfake face", "why_lost": "spectacle"},
                                   {"concept": "a magnifier", "why_lost": "the stock verify image"}]},
          "signature_move": "the best plate is filed on the wrong side of the deck's own line",
          "carried_by": [4, 6], "form_ledger": "seam 2 · editorial 3", "icon_family": "tabler",
          "palette": "FILL/TEXT split", "style_pick": "terminal · beat swiss · anti-pick: neon",
          "build_shape": "solo — one argument", "image_sources": ["slide 3 | x | generated — codex"],
          "motif_generates": {"background": "a rail", "markers": "+/x/?", "page": "slide 13"},
          "material_probe": {"png": "render/slide04.png", "safe_version": "two captioned pictures"},
          "signature_proof": [{"role": r, "slide": i + 4, "png": "render/x.png"}
                              for i, r in enumerate(("signature", "complex", "data"))],
          "checkpoint": {"mode": "approved", "record": "posted"}})
# `[]` is the legitimate "swept the source, nothing it marks as open" value — the gate blocks the
# missing KEY, never the count.
filled["content"]["open_ledger"] = []
filled["content"]["audience_brief"] = {
    "who": "the two editors deciding whether to run this investigation",
    "decisions": [{"decision": "run it or hold it", "needs": "which claim is the weakest link"},
                  {"decision": "how much legal review", "needs": "which lines name a person"},
                  {"decision": "what the headline claims", "needs": "the one fact that survives"}]}
filled["critic"] = {"waived": "user declined", "waived_category": "user-waived"}
filled["render_selfcheck"] = {"slides": [{"n": 1, "verdict": "ok"}, {"n": 2, "verdict": "ok"}]}
check(deck_gates.check(filled) == [], "a filled record is shape-clean", deck_gates.check(filled))

broken = json.loads(json.dumps(filled))
broken["design_plan"]["boldness"] = "bold - derived from purpose"      # the real first failure
broken["design_plan"]["concept"] = "a red line"                        # the real fourth
broken["design_plan"].pop("material_probe")                            # the real third
broken["design_plan"].pop("signature_proof")                           # the real second
broken["design_plan"]["type_scale"]["body"] = 13                       # the real fifth
probs = deck_gates.check(broken)
hit = {k: any(k in m for m in probs)
       for k in ("boldness", "concept", "material_probe", "signature_proof", "type_scale.body")}
check(all(hit.values()) and len(probs) >= 5,
      "the five shape faults that cost five separate --gate-check runs are reported in ONE pass",
      "{} / {}".format(hit, probs))
check(any("not a dial" in m and "boldness_derivation" in m for m in probs),
      "...and the dial message says WHERE the reason goes, which is what made it a typo trap")

fresh = deck_gates.template(3)
check(deck_gates.check(fresh) != [],
      "a FRESH template fails its own check — an unfilled skeleton cannot pass as a filled one")

# ── the direction competition is re-scored, not read ──────────────────────────────────────────
import directions_diversity                                                  # noqa: E402

lookalike = [
    {"name": "Brutalist", "bg": "#FFFFFF", "ink": "#111111", "accent": "#C8102E",
     "cover": "full-bleed-type", "skeleton": "statement",
     "cover_motif": "<div/>", "ambient_motif": "<div/>"},
    {"name": "Swiss", "bg": "#FFFFFF", "ink": "#111111", "accent": "#E2231A",
     "cover": "low-left", "skeleton": "statement",
     "cover_motif": "<div/>", "ambient_motif": "<div/>"},
]
r = directions_diversity.check(lookalike)
check(bool(r["flagged"]),
      "the detector still calls two white/red presets skins of one idea — the pair a human caught "
      "by eye on a real build", r)
plain = [{"name": "A", "bg": "#FFFFFF", "ink": "#111111", "accent": "#C8102E"},
         {"name": "B", "bg": "#0E1A2B", "ink": "#ECE6D8", "accent": "#C5A253"}]
check(directions_diversity.check(plain)["no_bespoke"],
      "...and a set with no invented register is reported as having none — the finding the same "
      "build shipped without noticing, because nothing ran this")

rd = (SCRIPTS / "render_deck.py").read_text(encoding="utf-8")
check("_direction_gate" in rd and "directions_diversity" in rd,
      "the hand-off gate now RE-SCORES the directions, the way it re-scores the arc")
check("direction_gate" in rd and "n/a" in rd,
      "...with the named-carve escape a locked/mimic/tiny-ask deck needs")
cdg = (SCRIPTS / "codex_delivery_gate.py").read_text(encoding="utf-8")
check("direction_gate" in cdg and "directions_diversity" in cdg,
      "and the CODEX path re-scores it too — the two gates drifting on a duplicated field has cost "
      "this repo twice already")
check('"direction_gate": {"candidates"' in cdg,
      "...and the codex SCAFFOLD carries it, so the field gets produced rather than discovered")
crt = (SKILL / "references" / "codex-runtime.md").read_text(encoding="utf-8")
check("direction_gate" in crt,
      "the CODEX RUNBOOK documents the field its own gate now BLOCKS on — the same defect this "
      "repo shipped once already: a gate taught to refuse something the runbook never mentions "
      "gives a non-Claude run a hard failure with no instruction anywhere")
check("deck_gates.py" in crt and "declare_delivery" in crt and "builds=" in crt,
      "...and the runbook carries the shape emitter and the builds record too")
check(".codex-deck-evidence.json" in (SCRIPTS / "deck_gates.py").read_text(encoding="utf-8"),
      "deck_gates.py says WHICH record it writes, so a Codex agent does not mistake it for the "
      "evidence file its own gate reads")

# ── a preset may not set a face this machine does not have ────────────────────────────────────
import warnings                                                              # noqa: E402
import presets                                                               # noqa: E402
import deckkit as dk                                                         # noqa: E402

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    presets.apply("terminal")
    msgs = [str(x.message) for x in w]
if dk._font_substituted("Consolas"):
    check(any("not installed" in m.lower() or "NOT installed" in m for m in msgs),
          "presets.apply warns when its declared face is absent — a fixed-width register measured "
          "in a proportional substitute is the worst case of a silent fallback", msgs)
    check(len([m for m in msgs if "Consolas" in m]) == 1,
          "...once per FACE, not once per slot (font/display/mono are the same face here)", msgs)
else:
    ok.append("Consolas IS installed here, so the terminal-preset case cannot be exercised "
              "(reported, not skipped silently)")

# ── a strike-through is a rule crossing its own text, and may now say so ──────────────────────
def _strike(declared):
    prs = dk.blank_deck(10.0, 5.625)
    s = dk.add_slide(prs)
    dk.text(s, 0.85, 1.0, 4.6, 0.34,
            [[("six fingers", 17, dk.MUTE, False, False, "Helvetica Neue")]], space_after=0)
    rule = dk.box(s, 0.85, 1.155, 1.3, 0.018, fill=dk.MUTE)
    if declared:
        dk.overlap_intent(rule, "a strike-through IS a rule crossing its own text")
    return [f[2] for f in dk.lint_layout(prs, verbose=False) if f[1] == "CRITICAL"]


check("RULE_THROUGH_TEXT" in _strike(False),
      "an UNdeclared rule through text is still CRITICAL — the hand-picked-y defect it was written "
      "for is untouched")
check(_strike(True) == [],
      "...and a declared one saves, so a strike-through is buildable at all", _strike(True))

# ── the builds choice is recorded, not retyped ────────────────────────────────────────────────
tmp = pathlib.Path(tempfile.mkdtemp(prefix="builds-"))
prs = dk.blank_deck(10.0, 5.625)
dk.add_slide(prs)
out = tmp / "d.pptx"
prs.save(str(out))
dk.declare_delivery(str(out), "presented", builds="static")
rec = json.loads((tmp / ".deck-gates.json").read_text(encoding="utf-8"))
check(rec.get("builds") == "static" and rec.get("delivery") == "presented",
      "declare_delivery records the BUILDS choice beside the delivery mode", rec)
raised = False
try:
    dk.declare_delivery(str(out), "presented", builds="maybe")
except ValueError:
    raised = True
check(raised, "...and refuses a value that is neither 'static' nor 'builds'")
ld = (SCRIPTS / "lint_deck.py").read_text(encoding="utf-8")
check('_blob.get("builds")' in ld,
      "lint_deck reads it, so NO BUILDS stands down on a deck that is static BY THE USER'S CHOICE")


# ── the console a non-Claude agent may actually be running on ─────────────────────────────────
# SKILL.md tells native-Windows users to call these entry points directly, and the toolchain
# writes ✓ · → · • · 🔴 into every report. On a legacy code page (the cmd/PowerShell default on
# Python 3.11-3.14) encoding those RAISES, and the tool dies mid-report: measured, `lint_deck.py`
# and `render_deck.py --gate-check` both exited 1 with a traceback after printing part of their
# output, which reads as a broken deck when the deck was fine and the CONSOLE could not print a
# tick. This is pre-existing and repo-wide — not a property of any one script — so it is pinned
# here for every CLI an agent actually runs.
import os                                                                    # noqa: E402

CONSOLE_CLIS = [
    ["lint_deck.py", "--help"], ["render_deck.py", "--help"],
    ["deck_gates.py", "--selftest"], ["check_image_provenance.py", "--selftest"],
    ["fetch_images.py", "--selftest"], ["image_qc.py", "--selftest"],
    ["arc_divergence.py", "--template"], ["component_audit.py"],
    ["preflight_check.py", "--help"], ["validate_review.py", "--schema", "critic"],
    ["check_design_contracts.py"], ["sigs.py", "--list"],
]
env = dict(os.environ, PYTHONIOENCODING="cp1252")
crashed = []
for cmd in CONSOLE_CLIS:
    # errors="replace" on OUR side too: the child is writing cp1252 bytes on purpose, and a
    # test that cannot read them would fail for its own reason rather than the tool's.
    r = subprocess.run([sys.executable, str(SCRIPTS / cmd[0])] + cmd[1:],
                       capture_output=True, text=True, errors="replace", env=env)
    if "UnicodeEncodeError" in (r.stderr or ""):
        crashed.append(cmd[0])
check(not crashed,
      "every CLI an agent runs survives a cp1252 console — the report degrades a tick to '?' and "
      "still finishes, instead of dying half-printed", crashed)

r = subprocess.run([sys.executable, str(SCRIPTS / "deck_gates.py"), "--selftest"],
                   capture_output=True, text=True, errors="replace", env=env)
check(r.returncode == 0 and "passed" in (r.stdout or ""),
      "...and still reports its real verdict there, not a mangled fragment", (r.stdout or "")[-160:])

check((SCRIPTS / "_console.py").exists(),
      "the safety lives in ONE place (_console.safe_stdio) rather than being re-typed per script")

# ── the same tooling on a Chinese deck ────────────────────────────────────────────────────────
import directions_diversity as _dd                                           # noqa: E402

cjk_dirs = [{"name": "验讫台", "bg": "#F2F5F6", "ink": "#1C1A17", "accent": "#C42E1C",
             "cover": "low-left", "skeleton": "rail",
             "cover_motif": "<div/>", "ambient_motif": "<div/>"},
            {"name": "夜间数据简报", "bg": "#101A24", "ink": "#ECE6D8", "accent": "#C5A253",
             "cover": "centred", "skeleton": "statement",
             "cover_motif": "<div/>", "ambient_motif": "<div/>"}]
_r = _dd.check(cjk_dirs)
check(not _r["flagged"] and len(_r["bespoke"]) == 2,
      "two CJK-named bespoke registers score as distinct and as bespoke — this skill builds decks "
      "in any language, and a checker that only understands Latin names is a checker for half of "
      "them", _r)

cjk = json.loads(json.dumps(filled))
cjk["design_plan"]["concept"] = {"chosen": "一条被跨越的红线",
                                 "rejected": [{"concept": "深伪人脸", "why_lost": "把话题变成奇观"},
                                              {"concept": "放大镜", "why_lost": "库存图"}]}
cjk["design_plan"]["signature_move"] = "最好的那张图被钉在自己红线的错误一侧"
cjk["critic"] = {"waived": "用户在看过成品后选择直接交", "waived_category": "user-waived"}
check(deck_gates.check(cjk) == [],
      "an all-Chinese record is shape-clean — the checker reads STRUCTURE, not English",
      deck_gates.check(cjk))

print("\n".join("  ok   " + x for x in ok))
if bad:
    print("\n".join("  FAIL " + x for x in bad))
print("\n{} passed, {} failed".format(len(ok), len(bad)))
raise SystemExit(1 if bad else 0)
