#!/usr/bin/env python3
"""The docs' visual-language lists, counts and offer guidance, generated from the registry (scripts/vl_specs/).

A doc carries a block as <!-- vl:NAME -->text<!-- /vl -->; `--write` regenerates every block, `--check` (CI) fails on a
block that differs, a block a doc must carry but does not (REQUIRED), an unknown block name, or markers that do not
pair. A hand-written count once drifted ("the nine DRAWN languages" after two more were added); now it cannot.
`--write` refuses a doc whose markers do not pair: it once paired an open marker with a far close and replaced the
prose between (final review). usage: vl_docs.py --write | --check"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vl_specs                      # noqa: E402  plain-data manifests: no deckkit import, so gates can use it
import component_tiers as ct         # noqa: E402  plain data too: the component tiers and the skin vocabulary

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent
REF = SKILL / "references"
# every doc, and the blocks it must carry (a doc that lost one by hand-editing is caught, not silently stale)
REQUIRED = {
    SKILL / "SKILL.md": {"count-drawn", "list-drawn", "list-image"},
    REF / "visual-languages.md": {"count-all", "count-image", "count-drawn", "offer-arrow", "tier-one-list", "tier-two-table",
                                  "skin-table"},
    REF / "interview-protocol.md": {"count-all", "count-image", "count-drawn", "list-image-comma", "offer-paren"},
    REF / "codex-runtime.md": {"list-drawn"},
    REF / "file-inventory.md": {"count-all", "count-image", "count-drawn", "list-image-plain", "list-drawn-plain"},
    REPO / "README.md": {"count-all", "count-image-cap", "count-drawn", "offer-arrow"},
    REPO / "README_CN.md": {"count-all-zh", "count-image-zh", "count-drawn-zh", "offer-zh"},
}
DOCS = list(REQUIRED)
_MARK = re.compile(r"<!-- vl:([a-z\-]+) -->|<!-- /vl -->")
_BLOCK = re.compile(r"<!-- vl:([a-z\-]+) -->(.*?)<!-- /vl -->", re.S)
_EN = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
       "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
_ZH = "零一二三四五六七八九十"


def _zh(n):
    if n <= 10:
        return _ZH[n]
    if n < 20:
        return "十" + _ZH[n - 10]
    return _ZH[n // 10] + "十" + (_ZH[n % 10] if n % 10 else "")


def _en(n):
    return _EN[n] if n < len(_EN) else str(n)


def _render(block, reg):
    drawn = [s for s in reg.values() if s["kind"] == "drawn"]
    image = [s for s in reg.values() if s["kind"] == "image-led"]
    names = lambda ss, fmt, sep: sep.join(fmt.format(s["name"]) for s in ss)
    table = {
        "count-all": lambda: _en(len(reg)), "count-drawn": lambda: _en(len(drawn)), "count-image": lambda: _en(len(image)),
        "count-image-cap": lambda: _en(len(image)).capitalize(),
        "count-all-zh": lambda: _zh(len(reg)), "count-drawn-zh": lambda: _zh(len(drawn)),
        "count-image-zh": lambda: _zh(len(image)),
        "list-drawn": lambda: names(drawn, "`{}`", " · "), "list-image": lambda: names(image, "`{}`", " · "),
        "list-image-comma": lambda: names(image, "`{}`", ", "),
        "list-drawn-plain": lambda: names(drawn, "{}", ", "), "list-image-plain": lambda: names(image, "{}", ", "),
        "offer-arrow": lambda: "; ".join("{} → `{}`".format(", ".join(s["offer"]["en"]), s["name"]) for s in drawn) + ".",
        "offer-paren": lambda: (lambda parts: parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " or " + parts[-1])(
            ["`{}` ({})".format(s["name"], ", ".join(s["offer"]["en"])) for s in drawn]),
        "offer-zh": lambda: "；".join("{} → {}".format("、".join(s["offer"]["zh"]), s["display"]["zh"]) for s in drawn) + "。",
        "tier-one-list": lambda: " · ".join("`{}`".format(n) for n in ct.TIER1),
        "tier-two-table": lambda: "\n" + "\n".join(["| component | draws in the skin |", "|---|---|"] +
                                         ["| `{}` | {} |".format(n, ", ".join(r)) for n, r in ct.TIER2_SKIN.items()]) + "\n",
        "skin-table": lambda: "\n" + "\n".join(["| language | card | rule | marker | number |", "|---|---|---|---|---|"] +
                                        ["| `{}` | {} | {} | {} | {} |".format(s["name"], *(s["skin"][r] for r in
                                         ("card", "rule", "marker", "number"))) for s in reg.values()]) + "\n",
    }
    if block not in table:
        raise KeyError(block)
    return table[block]()


def render(block):
    return _render(block, vl_specs.load())


def _structure(path, text):
    """Problems with the markers themselves: they must alternate open, close, open, close … with known names."""
    probs, open_ = [], None
    for m in _MARK.finditer(text):
        if m.group(1):                                   # an open marker
            if open_ is not None:
                probs.append("{}: unbalanced vl markers — vl:{} opens before vl:{} closes".format(path, m.group(1), open_))
                return probs
            open_ = m.group(1)
        else:
            if open_ is None:
                probs.append("{}: unbalanced vl markers — a /vl closes nothing".format(path))
                return probs
            open_ = None
    if open_ is not None:
        probs.append("{}: unbalanced vl markers — vl:{} is never closed".format(path, open_))
    return probs


def _rel(p):
    try:
        return str(Path(p).relative_to(REPO))
    except ValueError:
        return str(p)


def check(docs=None):
    reg = vl_specs.load()
    probs = []
    for p, required in (docs or REQUIRED).items():
        p = Path(p)
        if not p.is_file():                              # an installed copy of the skill has no repo README
            continue
        text = p.read_text(encoding="utf-8")
        st = _structure(_rel(p), text)
        if st:
            probs += st
            continue
        seen = set()
        for m in _BLOCK.finditer(text):
            seen.add(m.group(1))
            try:
                want = _render(m.group(1), reg)
            except KeyError:
                probs.append("{}: unknown block vl:{}".format(_rel(p), m.group(1)))
                continue
            if m.group(2) != want:
                probs.append("{}: block vl:{} reads {!r}, the registry says {!r}".format(
                    _rel(p), m.group(1), m.group(2)[:60], want[:60]))
        for b in sorted(set(required) - seen):
            probs.append("{}: required block vl:{} is missing".format(_rel(p), b))
    return probs


def write(docs=None):
    """Regenerate every block; a doc with unpaired markers or an unknown block is refused and left untouched."""
    reg = vl_specs.load()
    out = []
    for p in (docs or REQUIRED):
        p = Path(p)
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        st = _structure(_rel(p), text)
        unknown = [m.group(1) for m in _BLOCK.finditer(text) if m.group(1) not in _known(reg)]
        if st or unknown:
            out.append("refused {}: {}".format(_rel(p), "; ".join(st) or "unknown block(s) {}".format(unknown)))
            continue
        new = _BLOCK.sub(lambda m: "<!-- vl:{} -->{}<!-- /vl -->".format(m.group(1), _render(m.group(1), reg)), text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            out.append("wrote {}".format(_rel(p)))
    return out


def _known(reg):
    known = set()
    for b in ("count-all", "count-drawn", "count-image", "count-image-cap", "count-all-zh", "count-drawn-zh",
              "count-image-zh", "list-drawn", "list-image", "list-image-comma", "list-drawn-plain", "list-image-plain",
              "offer-arrow", "offer-paren", "offer-zh", "tier-one-list", "tier-two-table", "skin-table"):
        known.add(b)
    return known


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        res = write()
        for r in res:
            print(r)
        return 1 if any(r.startswith("refused") for r in res) else 0
    probs = check()
    for p in probs:
        print("  FAIL " + p)
    print("[vl-docs] {} problem(s)".format(len(probs)) + ("" if not probs else " — run: python3 {} --write".format(
        Path(__file__).resolve())))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
