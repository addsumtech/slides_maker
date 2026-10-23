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

# Component tiers (was component_tiers.py). Which general components wear a visual language, and how far (spec §5.5) — plain data, no deckkit import, so docs
# and gates read it without building anything.
#
# TIER1: every general component is held to every ground of every language (theme colours, readable, placed).
# TIER2_SKIN: the components that also draw their containers, rules, markers and numerals in the language's SKIN, and
# which of those roles each one draws. SKIN_VOCAB: the values a manifest may pick per role (spec §5.3); a value is
# implemented once in deckkit and reused by every language that picks it. A new language picks from here and adds a
# value only when none fits.
TIER1 = ("agenda bento consort_flow distribution dot_strip dumbbell_board eval_matrix forest_plot funnel gantt "
         "heat_matrix iso_bars iso_prism iso_stack km_curve leaderboard marimekko meter_bar native_chart org_tree "
         "position_map pyramid radar roc_curve sankey scorecard segmented_bar small_multiples stat_row step_list table "
         "tier_stack timeline unit_grid venn waterfall bland_altman source_note").split()
TIER1 = tuple(TIER1)

TIER2_SKIN = {
    "bento": ("card",),                     # through dk.skin_card — bento returns the rects, the caller draws them
    "step_list": ("marker", "rule", "number"),
    "timeline": ("rule", "marker", "number"),
    "agenda": ("rule", "number"),
    "stat_row": ("rule", "number"),
    "org_tree": ("card", "rule"),
    "tier_stack": ("card", "rule"),
    "funnel": ("card", "rule"),
    "pyramid": ("card", "rule"),
    "venn": ("rule",),
    "meter_bar": ("rule", "number"),
    "gantt": ("rule", "number"),
    "table": ("rule", "number"),
    "native_chart": ("rule", "number"),
    "heat_matrix": ("number",),
}

SKIN_VOCAB = {
    "card": ("filled", "outlined", "hairline", "window", "sign", "chalk", "paper"),
    "rule": ("solid", "hairline", "dashed", "chalk"),
    "marker": ("disc-number", "dot", "roundel", "circled", "badge"),
    "number": ("body", "display", "mono"),
}
SKIN_DEFAULT = {"card": "filled", "rule": "solid", "marker": "disc-number", "number": "body"}
TOP_KEYS = ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters", "skin")
_HEX = re.compile(r"^[0-9A-Fa-f]{6}$")
SERIES_MIN = 4          # spec §4.1 ruling: four designed colours per ground (Phase 2b, approved on its sheet 2026-10-15)
SERIES_DE = 20.0        # two series colours closer than this (CIE76) read as one
TYPE_FLOOR_CORE, TYPE_FLOOR_PRIVATE = 12, 10      # the smallest tier on a 13.333in page (spec §6.2)
# the core role whose FLOOR must hold the smallest tier too: a long quote shrank its credit to 10.3pt. Not kicker or
# caption — the lowest floor of all a language's roles is the floor its components keep (THEME["floor"]), and
# raising theirs moved drafting's and chalkboard's components and refused cutpaper's 1:1 long copy (2026-10-16)
SMALL_TIER = ("attribution",)
# two languages whose grounds are this close (ΔE ground + ΔE first accent, +10 for a different display face) are one
# look in two names (spec §6.2 distinctiveness; editorial/light and ink/light measured 4.2 — Phase 3, 2026-10-15)
DISTINCT_MIN = 15.0
# a pair the user chose to keep alike, with the reason (spec §6 Task 7) — {(lang/ground, lang/ground): reason}
DISTINCT_WAIVERS = {}


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


FILL = "FILL:"     # new_visual_language.py writes every decision it cannot make as "FILL: <what to decide>"


def unfilled(spec):
    """["<name>: <dotted.path> is not filled — <hint>"] for every string still starting with FILL: (look.palette is
    the light ground's palette, so it is read once, under grounds.light)."""
    name = spec.get("name", "?") if isinstance(spec, dict) else "?"
    out = []

    def walk(v, path):
        if path == "look.palette":
            return
        if isinstance(v, str) and v.strip().startswith(FILL):
            out.append("{}: {} is not filled — {}".format(name, path, v.strip()[len(FILL):].strip() or "decide it"))
        elif isinstance(v, dict):
            for k, x in v.items():
                walk(x, "{}.{}".format(path, k) if path else str(k))
        elif isinstance(v, (list, tuple)):
            for i, x in enumerate(v):
                walk(x, "{}[{}]".format(path, i))
    walk(spec, "")
    return out


def validate(spec):
    probs = []
    name = spec.get("name", "?")
    for k in TOP_KEYS:
        if k not in spec:
            probs.append("{}: the manifest has no {!r}".format(name, k))
    if probs:
        return probs
    # a draft from new_visual_language.py: name what is still to decide, and only that — the checks below would read
    # a "FILL: …" string as a bad colour or a bad face and bury the one message that says what to do
    probs = unfilled(spec)
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
    # the visitor-facing line the library page shows (vl_library_export.py); not a TOP_KEY: vl_specs.load refuses a
    # manifest missing one, and a field only the exporter reads must not brick every importer
    b = spec.get("blurb")
    if not (isinstance(b, dict) and isinstance(b.get("en"), str) and len(b["en"].strip()) >= 40
            and isinstance(b.get("zh"), str) and len(b["zh"].strip()) >= 12):
        probs.append("{}: blurb needs 'en' (40+ characters) and 'zh' (12+) — one or two plain sentences a visitor "
                     "reads on the library page".format(name))
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
    # the direction preview draws look.cover / look.skeleton and refuses any other value: eleven languages shipped
    # "split" (not a cover) and comic "grid" (not a skeleton), so choosing them in the direction gate raised (2026-10-23)
    import archetypes_html as _ah                    # standard library only: the contract stays light
    if "cover" in look and look["cover"] not in _ah._COVERS:
        probs.append("{}: look.cover {!r} is not a cover the direction preview draws — one of {}".format(
            name, look["cover"], _ah._COVERS))
    if "skeleton" in look and look["skeleton"] not in _ah._SKELETONS:
        probs.append("{}: look.skeleton {!r} is not a skeleton the direction preview draws — one of {}".format(
            name, look["skeleton"], _ah._SKELETONS))
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
    sk = spec.get("skin")
    if not isinstance(sk, dict) or set(sk) != set(SKIN_VOCAB):
        probs.append("{}: skin must name one value per role {} (got {!r})".format(name, sorted(SKIN_VOCAB), sk))
    else:
        for role, v in sk.items():
            if v not in SKIN_VOCAB[role]:
                probs.append("{}: skin {} {!r} is not in the vocabulary {} — pick one, or add the value to "
                             "vl_contract.SKIN_VOCAB and implement it in deckkit".format(
                                 name, role, v, list(SKIN_VOCAB[role])))
    # the smallest tier (spec §6.2, calibrated 2026-10-15 on the fifteen languages): a core role is read by the
    # audience — >= 12pt; a language's private furniture (running heads, tags, editions) >= 10pt
    for r, v in t.items():
        if isinstance(v, tuple) and len(v) == 6 and isinstance(v[0], (int, float)):
            need = TYPE_FLOOR_CORE if r in CORE_TYPE else TYPE_FLOOR_PRIVATE
            if v[0] < need:
                probs.append("{}: type role {!r} is {}pt — the smallest tier is {}pt for {} roles".format(
                    name, r, v[0], need, "core" if r in CORE_TYPE else "private"))
            # …and holds when a page SHRINKS: the small roles' floors too (a 60-word quote's attribution fell to
            # 10.3pt in drafting — final review, 2026-10-16)
            elif r in SMALL_TIER and v[5] < TYPE_FLOOR_CORE:
                probs.append("{}: type role {!r} may shrink to {}pt — its floor (the last number) must be >= {}pt, "
                             "the smallest tier".format(name, r, v[5], TYPE_FLOOR_CORE))
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
        elif spec["painters"][k] != "_{}_{}".format(k, name):
            # the one spelling every reader and new_visual_language.py use: a free name could quietly point at
            # another language's painter, and the language would draw that language's furniture
            probs.append("{}: painters.{} must be '_{}_{}' (got {!r})".format(name, k, k, name, spec["painters"][k]))
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
    # a draft (FILL: still in it) is named by validate() above; the cross-language checks read its colours and extras,
    # which are not decided yet — "FILL: …" read as a hex crashed the whole check (2026-10-16)
    specs = {n: s for n, s in specs.items() if not unfilled(s)}
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
    probs += distinct_pairs(specs)
    return probs


def distinctiveness(a, b):
    """How far apart two grounds look: ΔE of the grounds + ΔE of the first accents, +10 when the display faces differ."""
    (sa, ga), (sb, gb) = a, b
    pa, pb = sa["grounds"][ga]["palette"], sb["grounds"][gb]["palette"]
    fa = sa["look"]["fonts"]["both"]["display"]
    fb = sb["look"]["fonts"]["both"]["display"]
    return delta_e(pa["ground"], pb["ground"]) + delta_e(pa["accents"][0], pb["accents"][0]) + (0.0 if fa == fb else 10.0)


def distinct_pairs(specs):
    rows = [(n, g, s) for n, s in specs.items() if isinstance(s.get("grounds"), dict) for g in s["grounds"]]
    probs = []
    for i, (na, ga, sa) in enumerate(rows):
        for nb, gb, sb in rows[i + 1:]:
            if na == nb:
                continue
            try:
                d = distinctiveness((sa, ga), (sb, gb))
            except (KeyError, TypeError, IndexError):
                continue                               # a malformed manifest is reported by validate()
            key = tuple(sorted(("{}/{}".format(na, ga), "{}/{}".format(nb, gb))))
            if d < DISTINCT_MIN and key not in DISTINCT_WAIVERS:
                probs.append("{} and {} look alike (distance {:.1f} < {}): change one's ground, accent or display face, "
                             "or record the choice in DISTINCT_WAIVERS".format(key[0], key[1], d, DISTINCT_MIN))
    return probs
