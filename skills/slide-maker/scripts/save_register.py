#!/usr/bin/env python3
"""Keep a bespoke register after the deck ships — the skill's design memory.

WHY. `references/bespoke-registers.md` holds FOUR invented registers. This user's own look history
holds at least NINE that were designed, shipped, and then lost: 改札 Signage · 验讫台 Inspection
Bench · Grootboek 分类账 · 配置行 Config-Row · Build Record · Section Drawing… Measured by grep,
no script anywhere writes a register or a look-history line: the mechanism was "remember to edit
the markdown by hand", which is not a mechanism. So the skill invents good registers and forgets
every one of them, and every deck starts its design from zero no matter how good the tooling gets.

The register is not re-described here — that is the other reason this never happened. Everything
needed is already in `.deck-gates.json`, written at the design checkpoint and verified at hand-off:
the pick, the palette, the motif's three generated things, the signature move. This reads that
record, adds what only the RENDER knows (the colours that actually reached the pixels), and appends
one entry.

It writes to the USER'S registry root, beside `taste.md` — never into the skill's own
`bespoke-registers.md`, which is a teaching library of worked examples, not a place for one user's
collection. `registry.py` resolves the root on any runtime, so a non-Claude host gets its own.

    python3 scripts/save_register.py <deck-dir>            # append (idempotent by name)
    python3 scripts/save_register.py <deck-dir> --dry-run   # print the entry, write nothing
    python3 scripts/save_register.py --list                 # what is already kept
    python3 scripts/save_register.py --selftest

Exit 0 written / already there / nothing to keep · 2 could not run.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

FILE = "registers.md"
HEADER = """# Bespoke registers — invented here, kept for the next deck

Written by `scripts/save_register.py` at hand-off. Each entry is a register that was designed for a
real subject and shipped; the skill's own `references/bespoke-registers.md` is the worked-example
library that teaches how to invent one, and this is what YOU have invented.

Read these at Step 2 the way you read the preset gallery: not to reuse a look wholesale — the
freshness rule still says never reuse the last deck's scheme — but because a register that already
solved "how do I make an argument about X visible" is the best starting point for the next X.
"""


def _norm(name):
    """A register's identity for the DUPLICATE test, not for display.

    The same register is named two ways in two records: `.deck-gates.json` carries the pick's
    English name (`bespoke Section Drawing for …`) while the look-history row carries the one the
    author typed for a human (`自创「Section Drawing 建筑剖面」`). Comparing the strings kept both,
    which is how a collection meant to be read becomes a list with the same thing in it twice.
    So identity is the name with case, spacing and punctuation removed, and one name containing
    the other counts as the same register — a suffix like 建筑剖面 or `— the ledger` is a gloss on
    the same invention, not a second one.
    """
    import unicodedata
    n = unicodedata.normalize("NFKC", str(name or "")).lower()
    return re.sub(r"[\s\-_·—:：、,，.。'\"「」“”()（）]+", "", n)


def _same(a, b):
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    return na == nb or na.startswith(nb) or nb.startswith(na)


def _bespoke_name(style_pick):
    """The register's NAME from a `bespoke <name> for <domain> - beat …` pick, or None.

    Only picks that are actually bespoke are kept: `check_style_applied.declared_preset` settles
    whether a look is preset-based, and a preset needs no keeping — it is already in the gallery.
    """
    s = str(style_pick or "").strip()
    if not s:
        return None
    m = re.match(r"^\s*(?:bespoke|self-?invented|自创)[\s:·-]*(.+?)\s+(?:for|register for|—|-|·)\s",
                 s, re.I)
    if m:
        name = m.group(1).strip(" \"'「」“”·-—")
        return name or None
    m = re.match(r"^\s*(?:bespoke|自创)[\s:·]*[「\"']?([^」\"'\n]{2,60})[」\"']?", s, re.I)
    if m:
        return m.group(1).strip(" \"'「」“”·-—") or None
    return None


def _colours(deck_dir):
    """The colours that actually reached the pixels — what only the render knows."""
    try:
        import check_register_pixels as crp
        _p, facts = crp.check(deck_dir)
        return list(facts.get("present") or []) or list(facts.get("declared") or [])
    except Exception:
        return []


def entry_for(deck_dir):
    """(name, markdown) for the deck's bespoke register, or (None, reason)."""
    deck_dir = Path(os.path.expanduser(deck_dir))
    gp = deck_dir / ".deck-gates.json"
    try:
        gates = json.loads(gp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, "could not read {}: {}".format(gp, exc)
    d = gates.get("design_plan") or {}
    pick = d.get("style_pick")

    # A preset-based look needs no keeping — it is already in the gallery.
    try:
        import check_style_applied as csa
        preset, conf = csa.declared_preset(pick, csa.preset_names(), d.get(csa.LOOK_SOURCE_KEY))
        if preset and conf == "sure":
            return None, ("this deck declares the preset {!r} — presets live in the gallery "
                          "already, and only INVENTED registers are worth keeping".format(preset))
    except Exception:
        pass

    name = _bespoke_name(pick)
    if not name:
        return None, ("`design_plan.style_pick` does not read as a bespoke register "
                      "({!r}) — nothing to keep".format(str(pick or "")[:70]))

    mg = d.get("motif_generates") or {}
    cols = _colours(deck_dir)
    deck = deck_dir.name
    lines = ["", "### `{}` — from: {}".format(name, _domain(pick) or deck)]
    if d.get("palette"):
        lines.append("- **Palette:** {}".format(d["palette"]))
    if cols:
        lines.append("- **Reached the pixels:** {}".format(" · ".join(cols)))
    if d.get("signature_move"):
        lines.append("- **Signature move:** {}".format(d["signature_move"]))
    gen = [f for f in (("background", mg.get("background")), ("markers", mg.get("markers")),
                       ("page", mg.get("page"))) if f[1]]
    if gen:
        lines.append("- **Generates:** " + " · ".join("{} = {}".format(k, v) for k, v in gen))
    if d.get("carried_by"):
        lines.append("- **Carried by:** slide(s) {}".format(
            ", ".join(str(x) for x in d["carried_by"])))
    lines.append("- **Shipped as:** `{}`".format(deck))
    return name, "\n".join(lines) + "\n"


def _domain(pick):
    m = re.search(r"\bfor\s+(?:a|an|the)?\s*([^-—·]{3,60})", str(pick or ""), re.I)
    return m.group(1).strip() if m else None


def from_history():
    """Recover registers already recorded in `taste.md`'s LOOK HISTORY.

    The collection would otherwise start empty while the evidence that it should not sat one file
    away: a look-history row names the register, its canvas and its signature motif, because
    `references/user-taste.md` has required exactly that for every delivered deck. Those rows are
    thinner than a gates-record entry — they carry no `motif_generates` breakdown — and they say so,
    so nobody mistakes a recovered stub for one written at hand-off.
    """
    import re as _re
    try:
        import registry
        t = registry.taste_file()
        text = t.read_text(encoding="utf-8") if t else ""
    except Exception:
        return []
    out = []
    for line in text.splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        deck, look, canvas = cells[1], cells[2], cells[3]
        m = _re.search(r"自创\s*[「\"']([^」\"']+)[」\"']|bespoke\s+[\"'“]([^\"'”]+)[\"'”]"
                       r"|generated\s+[\"'“]([^\"'”]+)[\"'”]", look)
        if not m:
            continue
        name = next(g for g in m.groups() if g)
        body = ["", "### `{}` — from: {}".format(name.strip(), deck),
                "- **Look:** {}".format(look),
                "- **Canvas:** {}".format(canvas),
                "- **Shipped as:** `{}`".format(deck),
                "- *(recovered from the look history — thinner than an entry written at hand-off, "
                "which also carries the motif's generated background/markers/page)*"]
        out.append((name.strip(), "\n".join(body) + "\n"))
    return out


def target():
    """The user's registry root file — never the skill's own example library."""
    try:
        import registry
        _kind, root = registry.root_for_write()
        return Path(root) / FILE
    except Exception:
        return Path.home() / ".slide-maker" / "slide-templates" / FILE


def save(deck_dir, dry_run=False):
    name, body = entry_for(deck_dir)
    if not name:
        return 0, body
    path = target()
    existing = ""
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            return 2, "cannot read {}: {}".format(path, exc)
    # Idempotent by NAME: re-running a hand-off, or shipping a revision of the same deck, must not
    # grow a second copy. A register that changed enough to deserve a new entry has a new name.
    for have in re.findall(r"^### `([^`]+)`", existing, re.M):
        if _same(have, name):
            return 0, "`{}` is already kept in {} (as `{}`)".format(name, path, have)
    if dry_run:
        return 0, body
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((existing or HEADER) + body, encoding="utf-8")
    except OSError as exc:
        return 2, "cannot write {}: {}".format(path, exc)
    return 0, "kept `{}` in {}".format(name, path)


def kept():
    """The register names already in the user's collection."""
    path = target()
    try:
        return re.findall(r"^### `([^`]+)`", path.read_text(encoding="utf-8"), re.M)
    except OSError:
        return []


def _selftest():
    import tempfile
    ok, bad = [], []
    tmp = Path(tempfile.mkdtemp(prefix="savereg-"))

    for pick, want in (
            ("bespoke Section Drawing for a toolchain domain - beat blueprint because x",
             "Section Drawing"),
            ("自创「改札 Signage」register(车站标识体系) + Hiragino", "改札 Signage"),
            ("bespoke \"Build Record\" for the skill's own build-log - beat swiss", "Build Record"),
            ("brutalist for engineering - beat blueprint", None),
            ("", None)):
        got = _bespoke_name(pick)
        (ok if got == want else bad).append(
            "name from {!r} -> {!r}".format(pick[:34], got) if got == want
            else "name from {!r} gave {!r}, wanted {!r}".format(pick[:34], got, want))

    def deck(name, pick, extra=None):
        d = tmp / name
        d.mkdir(exist_ok=True)
        g = {"design_plan": dict({"style_pick": pick, "palette": "ground #101010; accent #FF0000",
                                 "signature_move": "the thing that is the argument",
                                 "motif_generates": {"background": "a quiet rule",
                                                     "markers": "numbered ticks",
                                                     "page": "slide 5"},
                                 "carried_by": [5, 10]}, **(extra or {}))}
        (d / ".deck-gates.json").write_text(json.dumps(g), encoding="utf-8")
        return d

    n, body = entry_for(deck("a", "bespoke Section Drawing for a toolchain domain - beat blueprint"))
    (ok if n == "Section Drawing" and "Signature move" in body else bad).append(
        "a bespoke deck yields an entry carrying its motif, signature and palette"
        if n == "Section Drawing" else "entry: {} {}".format(n, body[:60]))
    (ok if "Generates" in body and "background" in body else bad).append(
        "...including what the motif GENERATES, which is what makes a register reusable"
        if "Generates" in body else "no generates")

    n, why = entry_for(deck("b", "brutalist for engineering - beat blueprint - anti-pick avoided: x"))
    (ok if n is None and "gallery" in why else bad).append(
        "a PRESET-based deck is not kept — it is in the gallery already"
        if n is None else "preset deck kept: {}".format(n))

    for a, b, want in (("Section Drawing", "Section Drawing 建筑剖面", True),
                       ("改札 Signage", "改札Signage", True),
                       ("配置行 Config-Row", "配置行 Config Row", True),
                       ("Build Record", "Grootboek 分类账", False)):
        got = _same(a, b)
        (ok if got == want else bad).append(
            "{!r} and {!r} are {}the same register".format(a, b, "" if want else "NOT ")
            if got == want else "{!r} vs {!r} gave {}".format(a, b, got))

    d = deck("dup", "bespoke Section Drawing for a toolchain domain - beat blueprint")
    import tempfile as _tf
    _root = Path(_tf.mkdtemp())
    _orig = globals()["target"]
    globals()["target"] = lambda: _root / FILE
    try:
        save(d)
        c1, m1 = save(d)
        (ok if "already kept" in m1 else bad).append(
            "saving the same deck twice does not grow a second entry" if "already kept" in m1
            else "duplicate: {}".format(m1))
        (_root / FILE).write_text((_root / FILE).read_text(encoding="utf-8")
                                  .replace("### `Section Drawing`",
                                           "### `Section Drawing 建筑剖面`"), encoding="utf-8")
        _c, m2 = save(d)
        (ok if "already kept" in m2 else bad).append(
            "...nor when the collection names it with a gloss — the gates record carries the "
            "English pick and the look history the human-typed name, and comparing strings kept "
            "both" if "already kept" in m2 else "gloss duplicate: {}".format(m2))
    finally:
        globals()["target"] = _orig

    n, why = entry_for(tmp / "nope")
    (ok if n is None and "could not read" in why else bad).append(
        "a deck with no gates record says so rather than raising"
        if n is None else "missing gates: {}".format(why))

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck_dir", nargs="?")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--from-history", action="store_true",
                    help="recover registers already named in taste.md's LOOK HISTORY")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.list:
        names = kept()
        print("{} kept in {}".format(len(names), target()))
        for n in names:
            print("  " + n)
        return 0
    if a.from_history:
        have = kept()
        rows = [(n, b) for n, b in from_history()
                if not any(_same(h, n) for h in have)]
        if not rows:
            print("nothing to recover — every register named in the look history is already kept")
            return 0
        path = target()
        if a.dry_run:
            print("".join(b for _n, b in rows))
            return 0
        try:
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((existing or HEADER) + "".join(b for _n, b in rows), encoding="utf-8")
        except OSError as exc:
            print("cannot write {}: {}".format(path, exc), file=sys.stderr)
            return 2
        print("recovered {} register(s) into {}:\n  {}".format(
            len(rows), path, "\n  ".join(n for n, _b in rows)))
        return 0
    if not a.deck_dir:
        ap.print_help()
        return 2
    code, msg = save(a.deck_dir, a.dry_run)
    print(msg)
    return code


try:
    from _console import safe_stdio
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
