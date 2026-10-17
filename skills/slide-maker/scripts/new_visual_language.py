#!/usr/bin/env python3
"""Start a new visual language: write its manifest (scripts/vl_specs/<name>.py) and its code
(scripts/vl_langs/<name>.py), then let the contract check name everything still to do.

usage: new_visual_language.py <name> [--like <drawn language>] [--specs-dir D] [--langs-dir D]

The manifest is drafted from the --like language (default tally): its type scale, skin, grain and ground keys are a
starting point; every decision that makes the language ITSELF — its names, what it is for, its colours on each
ground, its display face, its sample words — is written as "FILL: <what to decide>", and check_vl_contract.py names
each one until it is decided. Its extras and derived words start empty (they belong to the language they came from).
The module holds a working ground painter, the language's card and one stub per page; check_vl_contract.py names each
stub until it is composed. Nothing else in the skill is edited, and the fifteen languages keep working throughout.
references/visual-language-authoring.md walks through every step."""
import argparse
import copy
import pprint
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vl_specs  # noqa: E402

PAGES = ("cover", "section", "image_text", "points", "quote", "data", "closing")
FILL = "FILL: "


def _fill_values(v, hint):
    """A colour (or a list of colours) replaced by FILL hints, keeping its shape."""
    if isinstance(v, list):
        return [FILL + "{} #{}".format(hint, i + 1) for i in range(len(v))]
    if isinstance(v, str):
        return FILL + hint
    return v


def draft(like, name, order):
    s = copy.deepcopy(like)
    s["name"], s["order"] = name, order
    s["display"] = {"en": FILL + "the language's name in English (one or two words)",
                    "zh": FILL + "它的中文名（两到四个字）"}
    s["rationale"] = FILL + "one line: what the language looks like and which decks it fits"
    s["blurb"] = {"en": FILL + "one or two plain sentences for visitors: what it looks like, what it suits (40+ characters)",
                  "zh": FILL + "给访客看的一两句话：长什么样、适合什么（12 字以上）"}
    s["offer"] = {"en": [FILL + "a topic it fits", FILL + "another topic it fits"],
                  "zh": [FILL + "适合的主题", FILL + "另一个适合的主题"]}
    for g, gd in s["grounds"].items():
        which = "default" if g == "light" else "contrast"
        gd["label"] = FILL + "the {} ground's name in English".format(which)
        gd["label_zh"] = FILL + "{}底色的中文名".format("默认" if g == "light" else "对比")
        gd["palette"] = {k: _fill_values(v, "{} ground: {}".format(g, k)) for k, v in gd["palette"].items()}
        gd["roles"] = {k: _fill_values(v, "{} ground: {}".format(g, k)) for k, v in gd["roles"].items()}
    for plat, faces in s["look"]["fonts"].items():
        faces["display"] = FILL + ("the display face, installed on macOS AND Windows" if plat == "both"
                                   else "the display face on macOS")
    s["samples"] = dict(s["samples"], copy=FILL + "the sample deck's words: [(page, fields), …], one of each page, "
                                                 "on a topic the language is offered for")
    s["extras"], s["derived"] = {}, []
    s["painters"] = {"ground": "_ground_" + name, "card": "_card_" + name}
    return s


def manifest_text(spec):
    body = pprint.pformat(spec, width=118, sort_dicts=False)
    return ('"""{n} — a visual language (a draft by new_visual_language.py). Every "FILL: …" is a decision to make;\n'
            'python3 scripts/check_vl_contract.py {n} names each one until it is made. The contract, field by field:\n'
            'references/visual-language-authoring.md."""\n'
            "SPEC = {b}\n"
            "# the light ground's palette IS the look's palette — one object, so a colour is decided once\n"
            "SPEC['look']['palette'] = SPEC['grounds']['light']['palette']\n").format(n=spec["name"], b=body)


def module_text(name):
    return '''"""{n} — the language's code: its ground painter, its card and its seven pages (a draft by
new_visual_language.py). Compose each page — replace its stub with a function decorated
@vn.register("{n}", "<page>") — then run:  python3 scripts/check_vl_contract.py {n}
references/visual-language-authoring.md walks through every step (what a page must and must not do)."""
import visual_languages as vl
import vl_native as vn

PAGES = {pages!r}


def _ground_{n}(slide, role, index):
    """An ordinary page in the language (a chart, an agenda): draw what every page carries and return the content
    rect in REFERENCE inches (the canvas's short side is 7.5)."""
    W, H = vl.rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


_card_{n} = vl._card_for("{n}")

for _page in PAGES:                    # a stub raises, and check_vl_contract.py names it until it is composed
    vn.stub("{n}", _page)
'''.format(n=name, pages=PAGES)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="new_visual_language", description=__doc__.split("\n")[0])
    ap.add_argument("name", help="lowercase letters, digits or _, starting with a letter")
    ap.add_argument("--like", default="tally", help="the drawn language to start from (default: tally)")
    ap.add_argument("--specs-dir", default=str(HERE / "vl_specs"), help=argparse.SUPPRESS)
    ap.add_argument("--langs-dir", default=str(HERE / "vl_langs"), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    def refuse(msg):
        print("new_visual_language: " + msg, file=sys.stderr)
        return 2
    if not re.match(r"^[a-z][a-z0-9_]*$", a.name):
        return refuse("{!r}: a name is lowercase letters, digits or _, starting with a letter".format(a.name))
    sd, ld = Path(a.specs_dir), Path(a.langs_dir)
    specs = vl_specs.load(sd, drafts=True)
    if a.name in specs or (sd / (a.name + ".py")).exists() or (ld / (a.name + ".py")).exists():
        return refuse("{!r} already exists — pick another name".format(a.name))
    vl_src = (HERE / "visual_languages.py").read_text(encoding="utf-8")
    if re.search(r"\b_(ground|card)_{}\b".format(re.escape(a.name)), vl_src):
        return refuse("{!r}: its painters (_ground_{n} / _card_{n}) would collide with names visual_languages.py "
                      "already defines — pick another name".format(a.name, n=a.name))
    if a.like not in specs:
        return refuse("--like {!r}: no such language — one of {}".format(a.like, ", ".join(specs)))
    if specs[a.like]["kind"] != "drawn":
        return refuse("--like {!r} is image-led: image-led languages compose through visual_languages.LAYOUTS, not "
                      "page modules — start from a drawn language (e.g. --like tally); "
                      "references/visual-language-authoring.md".format(a.like))
    spec = draft(specs[a.like], a.name, max(s["order"] for s in specs.values()) + 1)
    ld.mkdir(parents=True, exist_ok=True)
    (sd / (a.name + ".py")).write_text(manifest_text(spec), encoding="utf-8")
    (ld / (a.name + ".py")).write_text(module_text(a.name), encoding="utf-8")
    print("wrote {} — the manifest: every FILL: is a decision to make".format(sd / (a.name + ".py")))
    print("wrote {} — its ground painter, its card and seven page stubs".format(ld / (a.name + ".py")))
    env = []
    if sd.resolve() != (HERE / "vl_specs").resolve():
        env.append("VL_SPECS_DIR=" + shlex.quote(str(sd.resolve())))
    if ld.resolve() != (HERE / "vl_langs").resolve():
        env.append("VL_LANGS_DIR=" + shlex.quote(str(ld.resolve())))
    print("NEXT: {}python3 {} {}".format(" ".join(env) + " " if env else "",
                                         shlex.quote(str(HERE / "check_vl_contract.py")), a.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
