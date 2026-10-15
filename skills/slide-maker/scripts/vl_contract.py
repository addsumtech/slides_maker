"""The visual-language contract: what every language's manifest (scripts/vl_specs/<name>.py) declares, checked.

validate(spec) -> [problem, …] (empty = valid); validate_all({name: spec}) adds the rules across languages (one extra
name means one thing; unique names and orders). Pure: imports nothing from the skill, so the manifests, the tests and
a new language's author can all run it. Spec: docs/superpowers/specs/2026-10-15-visual-language-system-design.md §4."""
import re

PAGES = ("cover", "section", "image_text", "points", "quote", "data", "closing")
KINDS = ("image-led", "drawn")
# the type roles every page and component may ask for; a language may add private ones (item_no is private: six drawn
# languages number their points in their own furniture)
CORE_TYPE = ("kicker", "title", "subtitle", "body", "quote", "attribution", "number", "label", "note", "caption",
             "line", "item_head", "item_line")
ROLE_KEYS = ("card", "card_ink", "rule", "on_accent", "series", "highlight")
TOP_KEYS = ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters", "skin")
_HEX = re.compile(r"^[0-9A-Fa-f]{6}$")
SERIES_MIN = 4          # spec §4.1 ruling: four designed colours per ground (Phase 2b, approved on its sheet 2026-10-15)
SERIES_DE = 20.0        # two series colours closer than this (CIE76) read as one


def _rgb(h):
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    r, g, b = (_lin(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _lab(h):
    r, g, b = (_lin(c) for c in _rgb(h))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = [t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116 for t in (x, y, z)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def delta_e(a, b):
    return sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5


def is_dark(palette):
    """A ground is dark when its text ink is lighter than it — the meaning a component needs to pick its ink."""
    return luminance(palette["ink"]) > luminance(palette["ground"])


def _hexes(where, d, keys, probs):
    for k in keys:
        v = d.get(k)
        vals = v if isinstance(v, list) else [v]
        if k == "series" and not isinstance(v, list):
            probs.append("{}: series must be a list of colours, got {!r}".format(where, v))
            return False
        if not vals or any(not isinstance(x, str) or not _HEX.match(x) for x in vals):
            probs.append("{}: {} must be 6-digit hex colour(s), got {!r}".format(where, k, v))
            return False
    return True


def validate(spec):
    probs = []
    name = spec.get("name", "?")
    for k in TOP_KEYS:
        if k not in spec:
            probs.append("{}: the manifest has no {!r}".format(name, k))
    if probs:
        return probs
    # every nested value is type-checked before it is read: a half-filled skeleton must get named problems, never a
    # traceback (final review)
    for k, typ in (("display", dict), ("offer", dict), ("look", dict), ("grounds", dict), ("type", dict),
                   ("image_pages", tuple), ("extras", dict), ("derived", list), ("samples", dict), ("painters", dict)):
        if not isinstance(spec[k], typ):
            probs.append("{}: {} must be a {}, got {!r}".format(name, k, typ.__name__, type(spec[k]).__name__))
    if probs:
        return probs
    if not isinstance(name, str) or not re.match(r"^[a-z][a-z0-9_]*$", name):
        probs.append("{!r}: name must be lowercase letters, digits or _".format(name))
    if not isinstance(spec["order"], int):
        probs.append("{}: order must be an int".format(name))
    if spec["kind"] not in KINDS:
        probs.append("{}: kind must be one of {}, got {!r}".format(name, KINDS, spec["kind"]))
    if not all(isinstance(spec["display"].get(s), str) and spec["display"][s].strip() for s in ("en", "zh")):
        probs.append("{}: display needs non-empty 'en' and 'zh'".format(name))
    if not isinstance(spec["rationale"], str) or len(spec["rationale"]) < 12:
        probs.append("{}: rationale must say in a line what the language is".format(name))
    off = spec["offer"]
    if spec["kind"] == "drawn":
        if not all(isinstance(off.get(s), list) and len(off[s]) >= 2 and all(isinstance(t, str) and t for t in off[s])
                   for s in ("en", "zh")):
            probs.append("{}: offer needs at least two topics in 'en' and in 'zh'".format(name))
    elif off.get("pictures") not in ("photos", "illustrations"):
        probs.append("{}: an image-led language's offer names its pictures: 'photos' or 'illustrations'".format(name))
    look = spec["look"]
    missing_look = [k for k in ("palette", "fonts", "ea", "grain", "frames", "forbids", "cover", "skeleton") if k not in look]
    if missing_look:
        probs.append("{}: look has no {}".format(name, missing_look))
    gr = spec["grounds"]
    if not all(isinstance(gd, dict) for gd in gr.values()):
        probs.append("{}: every ground must be a dict, got {}".format(
            name, {g: type(gd).__name__ for g, gd in gr.items() if not isinstance(gd, dict)}))
        return probs
    if isinstance(gr.get("light"), dict) and "palette" in look and look["palette"] != gr["light"].get("palette"):
        probs.append("{}: look.palette differs from grounds.light.palette — the light ground has ONE palette".format(name))
    if "light" not in gr or len(gr) < 2:
        probs.append("{}: grounds need 'light' (the default key callers pass) and a contrast ground".format(name))
    for g, gd in gr.items():
        where = "{}/{}".format(name, g)
        pal, roles = gd.get("palette"), gd.get("roles", {})
        if not isinstance(pal, dict) or not isinstance(roles, dict):
            probs.append("{}: palette and roles must be dicts".format(where))
            continue
        if not _hexes(where, pal, ("ground", "ink", "mute", "panel", "accents", "text_accents"), probs):
            continue
        if not isinstance(gd.get("dark"), bool):
            probs.append("{}: dark must be True or False".format(where))
        elif gd["dark"] != is_dark(pal):
            probs.append("{}: dark={} but its ink is {} than its ground".format(
                where, gd["dark"], "lighter" if is_dark(pal) else "darker"))
        missing = [k for k in ROLE_KEYS if k not in roles]
        if missing:
            probs.append("{}: roles missing {}".format(where, missing))
            continue
        if not _hexes(where, roles, ROLE_KEYS, probs):
            continue
        for a, b, floor, what in ((pal["ink"], pal["ground"], 4.5, "ink on ground"),
                                  (pal["mute"], pal["ground"], 4.5, "mute on ground"),
                                  (roles["card_ink"], roles["card"], 4.5, "card_ink on card"),
                                  (roles["on_accent"], pal["accents"][0], 3.0, "on_accent on accents[0]")):
            c = contrast(a, b)
            if c < floor:
                probs.append("{}: {} is {:.2f}:1 (floor {}:1) — {} on {}".format(where, what, c, floor, a, b))
        ser = roles["series"]
        if not isinstance(ser, list):
            probs.append("{}: series must be a list of colours".format(where))
            continue
        if len(ser) < SERIES_MIN:
            probs.append("{}: series needs at least {} colour(s)".format(where, SERIES_MIN))
        for c in ser:
            for surf, sname in ((pal["ground"], "ground"), (roles["card"], "card")):
                if contrast(c, surf) < 3.0:
                    probs.append("{}: series colour {} is {:.2f}:1 on the {} (floor 3:1)".format(
                        where, c, contrast(c, surf), sname))
        for i, a in enumerate(ser):
            for b in ser[i + 1:]:
                if delta_e(a, b) < SERIES_DE:
                    probs.append("{}: series colours {} and {} are too close to distinguish (ΔE {:.1f} < {})".format(
                        where, a, b, delta_e(a, b), SERIES_DE))
    t = spec["type"]
    for r in CORE_TYPE:
        if r not in t:
            probs.append("{}: type has no core role {!r}".format(name, r))
    for r, v in t.items():
        if not (isinstance(v, tuple) and len(v) == 6 and isinstance(v[0], (int, float)) and isinstance(v[5], (int, float))
                and v[5] <= v[0]):
            probs.append("{}: type role {!r} must be (size, role, bold, colour, italic, floor<=size), got {!r}".format(
                name, r, v))
    import component_tiers as _ct
    sk = spec.get("skin")
    if not isinstance(sk, dict) or set(sk) != set(_ct.SKIN_VOCAB):
        probs.append("{}: skin must name one value per role {} (got {!r})".format(name, sorted(_ct.SKIN_VOCAB), sk))
    else:
        for role, v in sk.items():
            if v not in _ct.SKIN_VOCAB[role]:
                probs.append("{}: skin {} {!r} is not in the vocabulary {} — pick one, or add the value to "
                             "component_tiers.SKIN_VOCAB and implement it in deckkit".format(
                                 name, role, v, list(_ct.SKIN_VOCAB[role])))
    for p in spec["image_pages"]:
        if p not in PAGES:
            probs.append("{}: image page {!r} is not one of {}".format(name, p, PAGES))
    for x, d in spec["extras"].items():
        if not isinstance(d, dict):
            probs.append("{}: extra {!r} must be a dict of pages/remembered/takes/absent, got {!r}".format(name, x, d))
            continue
        pages = d.get("pages")
        if pages != "any" and (not isinstance(pages, tuple) or any(p not in PAGES for p in pages)):
            probs.append("{}: extra {!r} pages must be 'any' or a tuple of {}, got {!r}".format(name, x, PAGES, pages))
        if not isinstance(d.get("remembered"), bool):
            probs.append("{}: extra {!r} must say remembered=True/False".format(name, x))
        for k in ("takes", "absent"):
            if not isinstance(d.get(k), str) or not d[k].strip():
                probs.append("{}: extra {!r} must say what it {}".format(name, x, k))
    for d in spec["derived"]:
        if not (isinstance(d, dict) and isinstance(d.get("id"), str) and isinstance(d.get("what"), str)
                and isinstance(d.get("words"), dict)):
            probs.append("{}: each derived entry is {{'id', 'what', 'words': {{script: [word, …]}}}}, got {!r}".format(
                name, d))
    sm = spec["samples"]
    if spec["kind"] == "drawn" and not (isinstance(sm.get("copy"), list) and sm["copy"]):
        probs.append("{}: a drawn language's samples need 'copy': [(page, fields), …]".format(name))
    if spec["kind"] == "image-led" and sm.get("kind") not in ("photo", "watercolour"):
        probs.append("{}: an image-led language's samples name 'kind': 'photo' or 'watercolour'".format(name))
    for k in ("ground", "card"):
        if not isinstance(spec["painters"].get(k), str):
            probs.append("{}: painters needs the name of its {} function".format(name, k))
    return probs


def validate_all(specs):
    probs = []
    for n, s in specs.items():
        probs += validate(s)
        if s.get("name") != n:
            probs.append("{}: the manifest says name={!r}".format(n, s.get("name")))
    orders = {}
    for n, s in specs.items():
        orders.setdefault(s.get("order"), []).append(n)
    probs += ["order {} is used by {}".format(o, ns) for o, ns in orders.items() if len(ns) > 1]
    meaning = {}
    for n, s in specs.items():
        for x, d in s.get("extras", {}).items():
            if not isinstance(d, dict):
                continue
            pg = d.get("pages")
            key = (tuple(pg) if isinstance(pg, list) else pg, d.get("remembered"))
            meaning.setdefault(x, {}).setdefault(key, []).append(n)
    for x, m in meaning.items():
        if len(m) > 1:
            probs.append("extra {!r} means different things: {}".format(
                x, "; ".join("{} in {}".format(k, ns) for k, ns in m.items())))
    return probs
