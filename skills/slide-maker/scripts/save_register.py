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


_ANNOT = "-—–:：(（[【,，、/|"          # separators that introduce a GLOSS, not a new word
_CJK = "\u2e80-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af"


def _norm(name):
    """A register's identity for the DUPLICATE test, not for display — TOKENS plus how each began.

    The same register is named two ways in two records: `.deck-gates.json` carries the pick's
    English name (`bespoke Section Drawing for …`) while the look-history row carries the one the
    author typed for a human (`自创「Section Drawing 建筑剖面」`). Comparing the strings kept both,
    which is how a collection meant to be read becomes a list with the same thing in it twice.

    Returns [(token, introduced_by_an_annotation_separator), …]. Case, spacing and punctuation fold
    away; a Latin<->CJK transition counts as a token boundary, because `改札 Signage` gets typed
    both with and without the space.
    """
    import unicodedata
    n = unicodedata.normalize("NFKC", str(name or "")).lower()
    n = re.sub(r"[\u300c\u300d\u2018\u2019\u201c\u201d\'\"]+", "", n)
    n = re.sub(r"(?<=[" + _CJK + r"])(?=[0-9a-z])", " ", n)
    n = re.sub(r"(?<=[0-9a-z])(?=[" + _CJK + r"])", " ", n)
    out, annot = [], False
    for piece in re.split(r"([" + re.escape(_ANNOT) + r"\s.。;；)）\]】]+)", n):
        if not piece:
            continue
        if re.fullmatch(r"[" + re.escape(_ANNOT) + r"\s.。;；)）\]】]+", piece):
            annot = annot or any(c in _ANNOT for c in piece)
            continue
        out.append((piece, annot))
        annot = False
    return out


def _script(tok):
    return "cjk" if re.search("[" + _CJK + "]", tok) else "latin"


def _same(a, b):
    """Same register? Equal tokens, or one is the other plus a GLOSS.

    Plain containment was wrong in a way that costs exactly what this file protects: `Grid` and
    `Gridiron`, `Ledger` and `Ledger Line` came out identical, and the loser vanishes silently
    under "already kept". A gloss announces itself — it is in the other script (`Section Drawing
    建筑剖面`) or it arrives after an annotation separator (`Section Drawing — the ledger`). A bare
    Latin word after a Latin name is a DIFFERENT name, and the tie is broken toward keeping two
    entries: a visible duplicate is something the reader can merge, a dropped register is gone.
    """
    ta, tb = _norm(a), _norm(b)
    if not ta or not tb:
        return False
    if [t for t, _ in ta] == [t for t, _ in tb]:
        return True
    short, long_ = (ta, tb) if len(ta) < len(tb) else (tb, ta)
    if [t for t, _ in long_[:len(short)]] != [t for t, _ in short]:
        return False
    extra_tok, extra_annot = long_[len(short)]
    return bool(extra_annot or _script(extra_tok) != _script(short[-1][0]))


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
    if not isinstance(gates, dict):
        return None, "{} is not a gates record (found {})".format(gp, type(gates).__name__)
    d = gates.get("design_plan")
    if not isinstance(d, dict):
        # A hand-edited or half-written record must REPORT, never raise: the same AttributeError
        # class once took down a whole 16-section gate run, and a hand-off is the worst moment to
        # meet a traceback from a library-bookkeeping helper.
        return None, ("{}'s `design_plan` is {}, not an object — nothing to read a register "
                      "from".format(gp, type(d).__name__))
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

    mg = d.get("motif_generates")
    mg = mg if isinstance(mg, dict) else {}
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
    if isinstance(d.get("carried_by"), (list, tuple)) and d["carried_by"]:
        lines.append("- **Carried by:** slide(s) {}".format(
            ", ".join(str(x) for x in d["carried_by"])))
    lines.append("- **Shipped as:** `{}`".format(deck))
    return name, "\n".join(lines) + "\n"


def _domain(pick):
    m = re.search(r"\bfor\s+(?:a|an|the)?\s*([^-—·]{3,60})", str(pick or ""), re.I)
    return m.group(1).strip() if m else None


def _history_name(look):
    """The register NAME inside a look-history cell, or None.

    Quoted first — an author who typed the name in 「」 or "" means exactly that span. Then the
    UNQUOTED forms, because a row reading `bespoke Section Drawing register` is the same fact typed
    without quotes, and dropping it silently is the loss this whole file exists to stop, arriving
    as a clean "nothing to recover". A capture that begins with the NOUN (`bespoke register
    invented for the archive`) names nothing — a stub called "register invented for the archive"
    would be worse than the missing row, so that goes back to the caller as unreadable.
    """
    m = re.search(r"自创\s*[「\"'“]([^」\"'”]+)[」\"'”]|bespoke\s+[\"'“]([^\"'”]+)[\"'”]"
                  r"|generated\s+[\"'“]([^\"'”]+)[\"'”]", str(look or ""))
    if not m:
        m = re.search(r"(?:bespoke|self-invented|自创)\s+([^,;(（]{2,48}?)"
                      r"\s*(?:register|look|scheme|风格|$|[,;(（])", str(look or ""), re.I)
    if not m:
        return None
    name = next((g for g in m.groups() if g), "").strip()
    if not name or re.match(r"(?:register|look|scheme|风格)\b", name, re.I):
        return None
    return name


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
    out, unread = [], []
    for line in text.splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        deck, look, canvas = cells[1], cells[2], cells[3]
        name = _history_name(look)
        if not name:
            if _re.search(r"bespoke|自创|self-invented", look, _re.I):
                unread.append((deck, look))
            continue
        body = ["", "### `{}` — from: {}".format(name.strip(), deck),
                "- **Look:** {}".format(look),
                "- **Canvas:** {}".format(canvas),
                "- **Shipped as:** `{}`".format(deck),
                "- *(recovered from the look history — thinner than an entry written at hand-off, "
                "which also carries the motif's generated background/markers/page)*"]
        out.append((name.strip(), "\n".join(body) + "\n"))
    for deck, look in unread:
        print("  ! {}: this row names a bespoke look but no register NAME could be read from it — "
              "add it by hand if it is worth keeping:\n      {}".format(deck, look[:110]),
              file=sys.stderr)
    return out


def target():
    """Where a NEW entry goes — the user's registry root, never the skill's example library."""
    try:
        import registry
        _kind, root = registry.root_for_write()
        return Path(root) / FILE
    except Exception:
        return Path.home() / ".slide-maker" / "slide-templates" / FILE


def sources():
    """Every `registers.md` to READ — one per existing registry root, priority order.

    `registry.taste_file()` scans all roots and `list_templates()` de-duplicates across them, for
    the same reason: the same person runs Claude Code on one deck and a Codex host on the next, and
    the roots are `~/.claude/…` and `~/.codex/…`. Reading only the WRITE root would have shown an
    empty collection to the runtime that did not create it, and then written a second copy of a
    register that was already kept — a split collection is the failure this file exists to prevent,
    arriving by a different door. New entries still go to ONE root; reading spans them all.
    """
    out = []
    try:
        import registry
        for _kind, root in registry.roots_for_read():
            f = Path(root) / FILE
            if f.is_file():
                out.append(f)
    except Exception:
        pass
    t = target()
    if t.is_file() and t not in out:
        out.append(t)
    return out


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
    for src in sources():
        try:
            text = src.read_text(encoding="utf-8")
        except OSError as exc:
            # An unreadable collection is not an empty one. macOS TCC revokes access to home
            # subdirectories mid-session, and skipping the duplicate test in silence is how the
            # user ends up with two copies of one register and no idea why.
            print("  ! cannot read {} ({}) — the duplicate test could not consult it, which is "
                  "NOT the same as it being empty".format(src, exc.__class__.__name__),
                  file=sys.stderr)
            continue
        for have in re.findall(r"^### `([^`]+)`", text, re.M):
            if _same(have, name):
                return 0, "`{}` is already kept in {} (as `{}`)".format(name, src, have)
    if dry_run:
        return 0, body
    # Rewriting the file in place would truncate it first, and this file is the user's design
    # memory: an interrupt between truncate and write costs the whole collection to add one entry.
    # Temp-then-replace makes the worst case a stray temp file.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".new")
        tmp.write_text((existing or HEADER) + body, encoding="utf-8")
        os.replace(str(tmp), str(path))
    except OSError as exc:
        return 2, "cannot write {}: {}".format(path, exc)
    return 0, "kept `{}` in {}".format(name, path)


def kept():
    """Every register name in the user's collection, across all registry roots."""
    names = []
    for src in sources():
        try:
            for n in re.findall(r"^### `([^`]+)`", src.read_text(encoding="utf-8"), re.M):
                if not any(_same(n, m) for m in names):
                    names.append(n)
        except OSError as exc:
            print("  ! cannot read {} ({}) — listed as absent, which is not the same as "
                  "empty".format(src, exc.__class__.__name__), file=sys.stderr)
            continue
    return names


def is_kept(name):
    """Identity, not string equality — the caller printing a reminder must agree with `save()`."""
    return any(_same(name, have) for have in kept())


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

    for a, b in (("Grid", "Gridiron"), ("Rail", "Railyard"), ("Ledger", "Ledger Line"),
                 ("Bench", "Benchmark")):
        (ok if not _same(a, b) else bad).append(
            "{!r} and {!r} stay two registers — a name that merely STARTS with another is not a "
            "gloss on it, and merging them loses one silently under \"already kept\"".format(a, b)
            if not _same(a, b) else "{!r} and {!r} were merged".format(a, b))

    for shape, why in (({"design_plan": ["a"]}, "a list"), ({"design_plan": "x"}, "a string"),
                       ({"design_plan": {"style_pick": "bespoke X for y - beat z",
                                         "motif_generates": ["nope"],
                                         "carried_by": "5, 10"}}, "wrong-typed subfields")):
        dd = tmp / ("shape" + why.replace(" ", ""))
        dd.mkdir(exist_ok=True)
        (dd / ".deck-gates.json").write_text(json.dumps(shape), encoding="utf-8")
        try:
            entry_for(dd)
            ok.append("a gates record whose design_plan is {} reports instead of raising".format(why))
        except Exception as exc:
            bad.append("design_plan as {} raised {}: {}".format(why, type(exc).__name__, exc))

    for look, want in (("bespoke Section Drawing register", "Section Drawing"),
                       ("self-invented Ledger Line look for the ledger", "Ledger Line"),
                       ("bespoke register invented for the archive", None),
                       ("brutalist preset, tuned", None)):
        got = _history_name(look)
        (ok if got == want else bad).append(
            "look-history row {!r} -> {!r}".format(look[:38], got) if got == want
            else "row {!r} gave {!r}, wanted {!r}".format(look[:38], got, want))

    d = deck("dup", "bespoke Section Drawing for a toolchain domain - beat blueprint")
    import tempfile as _tf
    _root = Path(_tf.mkdtemp())
    # BOTH seams, not just the write one: `sources()` reads every real registry root, so a
    # selftest that patched only `target` would consult the developer's own collection — and
    # `Section Drawing` is IN it. That test passes on CI (no collection) and fails on the machine
    # of anyone who has used the tool, which is the wrong way round.
    _orig, _orig_src = globals()["target"], globals()["sources"]
    globals()["target"] = lambda: _root / FILE
    globals()["sources"] = lambda: [_root / FILE] if (_root / FILE).is_file() else []
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
        globals()["target"], globals()["sources"] = _orig, _orig_src

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
        srcs = sources()
        print("{} kept in {}".format(len(names), " + ".join(str(x) for x in srcs) or target()))
        if len(srcs) > 1:
            print("  (two registry roots on this machine — new entries go to {})".format(target()))
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
