#!/usr/bin/env python3
"""The docs' visual-language lists, counts and offer guidance, generated from the registry (scripts/vl_specs/).

A doc carries a block as <!-- vl:NAME -->text<!-- /vl -->; `--write` regenerates every block, `--check` (CI) fails on any
block that differs. A hand-written count once drifted ("the nine DRAWN languages" after two more were added); now it
cannot. usage: vl_docs.py --write | --check"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vl_specs                      # noqa: E402  plain-data manifests: no deckkit import, so gates can use it

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent
DOCS = [SKILL / "SKILL.md", SKILL / "references" / "visual-languages.md", SKILL / "references" / "interview-protocol.md",
        SKILL / "references" / "codex-runtime.md", REPO / "README.md", REPO / "README_CN.md"]
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


def render(block):
    reg = vl_specs.load()
    drawn = [s for s in reg.values() if s["kind"] == "drawn"]
    image = [s for s in reg.values() if s["kind"] == "image-led"]
    if block == "count-all":
        return _EN[len(reg)]
    if block == "count-drawn":
        return _EN[len(drawn)]
    if block == "count-image":
        return _EN[len(image)]
    if block == "count-all-zh":
        return _zh(len(reg))
    if block == "count-drawn-zh":
        return _zh(len(drawn))
    if block == "list-drawn":
        return " · ".join("`{}`".format(s["name"]) for s in drawn)
    if block == "offer-arrow":
        return "; ".join("{} → `{}`".format(", ".join(s["offer"]["en"]), s["name"]) for s in drawn) + "."
    if block == "offer-paren":
        parts = ["`{}` ({})".format(s["name"], ", ".join(s["offer"]["en"])) for s in drawn]
        return ", ".join(parts[:-1]) + " or " + parts[-1]
    if block == "offer-zh":
        return "；".join("{} → {}".format("、".join(s["offer"]["zh"]), s["display"]["zh"]) for s in drawn) + "。"
    raise KeyError("unknown vl docs block {!r}".format(block))


def _rewrite(text):
    return _BLOCK.sub(lambda m: "<!-- vl:{} -->{}<!-- /vl -->".format(m.group(1), render(m.group(1))), text)


def write():
    changed = []
    for p in DOCS:
        t = p.read_text(encoding="utf-8")
        n = _rewrite(t)
        if n != t:
            p.write_text(n, encoding="utf-8")
            changed.append(str(p))
    return changed


def check():
    probs = []
    for p in DOCS:
        for m in _BLOCK.finditer(p.read_text(encoding="utf-8")):
            want = render(m.group(1))
            if m.group(2) != want:
                probs.append("{}: block vl:{} reads {!r}, the registry says {!r}".format(
                    p.relative_to(REPO), m.group(1), m.group(2)[:60], want[:60]))
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        for c in write():
            print("wrote", c)
        return 0
    probs = check()
    for p in probs:
        print("  FAIL " + p)
    print("[vl-docs] {} problem(s)".format(len(probs)) + ("" if not probs else " — run: python3 {} --write".format(
        Path(__file__).resolve())))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
