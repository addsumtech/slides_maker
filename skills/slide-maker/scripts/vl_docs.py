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
import vl_contract as ct         # noqa: E402  plain data too: the component tiers and the skin vocabulary

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
    REPO / "README.md": {"count-all", "count-image-cap", "count-drawn", "gallery-more", "vl-badge", "vl-gallery"},
    REPO / "README_CN.md": {"count-all-zh", "count-image-zh", "count-drawn-zh", "gallery-more-zh", "vl-badge-zh",
                            "vl-gallery-zh"},
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


_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _en(n):
    """A count in words: digits in the middle of prose that spells its other counts read as a slip ("four image-led
    and 26 drawn", 2026-10-22). Past ninety-nine, digits."""
    if n < len(_EN):
        return _EN[n]
    if n < 100:
        return _TENS[n // 10] + ("-" + _EN[n % 10] if n % 10 else "")
    return str(n)


_CELL = re.compile(r"samples/([a-z0-9_]+)\.jpg")       # a gallery cell's sample (a second ground's link has a '-')


def gallery(reg):
    """The languages the README's gallery shows, or None without a repo README (an installed copy). The gallery is
    generated from SHOWCASE (vl-gallery); the library section shows every language, and the README says how many
    more there are (gallery-more)."""
    p = REPO / "README.md"
    if not p.is_file():
        return None
    return {n for n in _CELL.findall(p.read_text(encoding="utf-8")) if n in reg}


def _more(reg):
    n = len([s for s in SHOWCASE if s in reg])
    return n, len(reg) - n


LIBRARY = "https://slides.addsum.top/#languages"        # the library is a section of the home page (2026-10-23)
LIBRARY_ZH = "https://slides.addsum.top/cn/#languages"
# the README gallery (2026-10-23): twelve looks the user asked for, three to a row like the template gallery above it,
# chosen for range of look and use; a new language gets no cell, the library section shows every one
SHOWCASE = ("editorial", "poster", "ink", "comic", "vinyl", "stainedglass", "wayfinding", "chalkboard", "recipe",
            "circuit", "storybook", "scoreboard")
_CARRIES = {"photos": ("with your photos", "配你的照片"), "illustrations": ("with an illustration series", "配一组插画")}


def _gallery(reg, zh):
    """The README gallery's table: each cell is a language's sample sheet and its name, what it suits (a picture
    language: what it carries), and a link; the picture and the link open that language in the library section."""
    missing = [n for n in SHOWCASE if n not in reg]
    if missing:
        raise ValueError("vl_docs.SHOWCASE names no registered language: {}".format(missing))
    site, more = ("https://slides.addsum.top/cn/#vl-", "在模版库查看全部页面") if zh else \
        ("https://slides.addsum.top/#vl-", "See every page in the library")
    rows = []
    for i in range(0, len(SHOWCASE), 3):
        cells = []
        for n in SHOWCASE[i:i + 3]:
            s = reg[n]
            pics = s["offer"].get("pictures")
            use = _CARRIES[pics][1 if zh else 0] if pics else ("、" if zh else ", ").join(s["offer"]["zh" if zh else "en"][:3])
            name = "{}（{}）".format(s["display"]["zh"], n) if zh else "{} ({})".format(s["display"]["en"], n)
            cells.append(
                '    <td align="center" width="33%">\n'
                '      <a href="{u}{n}"><img src="skills/slide-maker/assets/vl/samples/{n}.jpg" alt="{alt}"></a><br/>\n'
                '      <sub><strong>{name}</strong><br/>{use}<br/>\n'
                '      <a href="{u}{n}">{more}</a></sub>\n'
                '    </td>'.format(u=site, n=n, name=name, use=use, more=more,
                                   alt="{} 设计语言示例页".format(n) if zh else "{} visual language sample pages".format(n)))
        rows.append("  <tr>\n" + "\n".join(cells) + "\n  </tr>")
    return "\n<table>\n" + "\n".join(rows) + "\n</table>\n"


def _badge(n, label, alt, url=LIBRARY):
    """The README's badge beside ClawHub: the library's language count, linked to the library section."""
    from urllib.parse import quote
    return '<a href="{}"><img alt="{}: {}" src="https://img.shields.io/badge/{}-{}-c2410c"></a>'.format(
        url, alt, n, quote(label), n)


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
        "gallery-more": lambda: (lambda g, n: "" if n <= 0 else
                                 "The gallery above shows {} of them; {} more are only in the library. ".format(
                                     _en(g), _en(n)))(*_more(reg)),
        "gallery-more-zh": lambda: (lambda g, n: "" if n <= 0 else
                                    "上面只展示了其中{}套，另外{}套只在模版库里。".format(_zh(g), _zh(n)))(*_more(reg)),
        "vl-badge": lambda: _badge(len(reg), "visual_languages", "Visual languages"),
        "vl-badge-zh": lambda: _badge(len(reg), "视觉语言模版库", "视觉语言模版库", LIBRARY_ZH),
        "vl-gallery": lambda: _gallery(reg, zh=False), "vl-gallery-zh": lambda: _gallery(reg, zh=True),
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
              "offer-arrow", "offer-paren", "offer-zh", "tier-one-list", "tier-two-table", "skin-table", "gallery-more",
              "gallery-more-zh", "vl-badge", "vl-badge-zh", "vl-gallery", "vl-gallery-zh"):
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
