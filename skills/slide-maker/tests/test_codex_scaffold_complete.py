#!/usr/bin/env python3
"""Every field the Codex gate REQUIRES must appear in the template that gate itself writes.

🔴 MEASURED. A Codex run filled `--init`'s scaffold end to end, supplied a real deck and a clean
lint, and was still BLOCKED by `interview.picks is missing` and `design.composition is missing` —
two of 43 errors, for fields that had never appeared in the template it was given. Both gates had
bound them on BOTH runtimes for a while; only the shared path's `deck_gates.py --init` showed
them, so the rule existed and the Codex agent had no way to discover it. That is this repo's
recorded lesson in a new place: a capability that does not reach the example scaffold has not been
added for the runtime that reads the scaffold.

This asserts the property rather than the two instances: fill the scaffold with plausible values,
run the real gate, and fail if any error names a field the scaffold never mentioned.
"""
from __future__ import annotations

import _hermetic  # noqa: F401,E402 — never read the user's own taste.md / taste ledger
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def keys_of(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield prefix + k
            yield from keys_of(v, prefix + k + ".")


with tempfile.TemporaryDirectory() as _td:
    td = Path(_td)
    tmpl = td / "ev.json"
    r = subprocess.run([sys.executable, str(SCRIPTS / "codex_delivery_gate.py"), "--init",
                        str(tmpl)], capture_output=True, text=True)
    check(r.returncode == 0 and tmpl.exists(),
          "codex_delivery_gate.py --init did not write a template: {}{}".format(r.stdout, r.stderr))

    if tmpl.exists():
        ev = json.loads(tmpl.read_text(encoding="utf-8"))
        scaffold_keys = set(keys_of(ev))

        # 🔴 the two that were measured missing — named, so a regression says which one
        for k in ("interview.picks", "design.composition"):
            check(k in scaffold_keys,
                  "`{}` is REQUIRED by this gate on an auto deck and is absent from the template "
                  "the gate itself writes — a Codex run filling the scaffold hits a wall it had no "
                  "way to see".format(k))

        # …and the general property: run the real gate over the filled scaffold and check that no
        # error names a dotted field the scaffold never mentions.
        import deckkit as dk                                           # noqa: E402
        dk.set_palette(font="Helvetica Neue")
        prs = dk.blank_deck(13.333, 7.5)
        for _ in range(3):
            s = dk.add_slide(prs)
            dk.text(s, 0.9, 0.6, 11.5, 0.9,
                    [[("A title that says something", 30,
                       dk.RGBColor.from_string("111111"), True, False)]])
        deck = td / "deck.pptx"
        prs.save(str(deck))
        ev["delivery"] = "presented"
        ev["deck"] = {"pptx": "deck.pptx",
                      "sha256": hashlib.sha256(deck.read_bytes()).hexdigest(),
                      "slide_count": 3}
        ev.setdefault("content", {})["checkpoint"] = {"mode": "auto", "record": "FYI"}
        (td / ".codex-deck-evidence.json").write_text(json.dumps(ev, ensure_ascii=False),
                                                      encoding="utf-8")
        (td / "lint.json").write_text('{"findings":[],"slides":3}', encoding="utf-8")
        (td / "comp.json").write_text('{"components":[]}', encoding="utf-8")
        (td / "build.py").write_text("# build\n", encoding="utf-8")
        g = subprocess.run([sys.executable, str(SCRIPTS / "codex_delivery_gate.py"),
                            "--evidence", str(td / ".codex-deck-evidence.json"),
                            "--lint", str(td / "lint.json"),
                            "--components", str(td / "comp.json"),
                            "--build-script", str(td / "build.py")],
                           capture_output=True, text=True, cwd=str(td))
        out = g.stdout + g.stderr
        check("BLOCKED" in out or "PASS" in out,
              "the gate did not run over the filled scaffold: {}".format(out[:300]))

        # dotted field names the gate complains about, e.g. `interview.picks` / `design.composition`
        named = set(re.findall(r"`([a-z_]+\.[a-z_]+(?:\.[a-z_]+)?)`", out))
        unknown = sorted(f for f in named
                         if f.split(".")[0] in ("interview", "design", "content")
                         and f not in scaffold_keys
                         # a LEAF the scaffold shows one level up is discoverable enough
                         and ".".join(f.split(".")[:2]) not in scaffold_keys)
        check(not unknown,
              "the gate demands field(s) the template never mentions, so a run that filled the "
              "scaffold cannot discover them: {}".format(unknown))

print("\n".join("FAIL " + f for f in fails) if fails else "", end="")
print("[test_codex_scaffold_complete] {}".format(
    "FAILED: {} problem(s)".format(len(fails)) if fails else "ok"))
sys.exit(1 if fails else 0)
