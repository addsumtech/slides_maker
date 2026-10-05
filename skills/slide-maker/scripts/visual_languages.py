#!/usr/bin/env python3
"""visual_languages — four complete image-led looks: editorial, soft, collage, storybook.

Picking one gives a whole deck: a palette with text-safe inks, a type voice from SYSTEM fonts chosen per
platform and per script, a surface, image treatments, and six page compositions (cover, section,
image_text, quote, data, closing) that lay out the caller's own words and images — never invented ones.

    k = visual_languages.use("collage", prs, fonts="both")    # faces on macOS AND Windows (default)
    s = k.new_slide()
    k.cover(s, title="Bring it broken", kicker="A repair café", image="hero")   # a P1 slot id or a path

fonts="both" uses only faces present on macOS and Windows, so the render matches what the viewer opens;
fonts="mac" unlocks Mac-only faces (Didot, Bradley Hand, …) and refuses one that is not installed. East-Asian
faces follow the SCRIPT of each run (Han, kana, Hangul) — a Chinese face has no Hangul. Windows faces are
from Microsoft's documented defaults and are UNVERIFIED here (no Windows renderer on the build machine).

Each language registers with register_surface (ground + card), so register_guard, check_register_pixels
and rs.card(slide, name, …) work for ordinary pages in the same look. Never imported by deckkit, presets,
register_surface or bespoke_kits: test_register_surface asserts the registry equals the presets before
its own imports.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import deckkit as dk  # noqa: E402
import register_surface as rs  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402

EA_FACES = dk.EA_FACES   # one table, in deckkit; the "win" faces: Microsoft's documented defaults — unverified here

LANGS = {
    "editorial": {
        "palette": {"ground": "F4EFE6", "ink": "1C1A17", "mute": "6B655C", "panel": "EAE3D6",
                    "accents": ["B23A28", "1F4E79"], "text_accents": ["9E2F20", "1F4E79"]},
        "fonts": {"both": {"display": "Georgia", "body": "Arial", "numeral": "Arial Black"},
                  "mac": {"display": "Didot", "body": "Helvetica Neue", "numeral": "Helvetica Neue"}},
        "ea": {"display": "serif", "body": "sans"}, "grain": 3, "frames": ["rect", "arch"],
        "forbids": ("confetti",), "cover": "full-bleed-type", "skeleton": "split"},
    "soft": {
        "palette": {"ground": "F7EFE6", "ink": "2E2A27", "mute": "6E625A", "panel": "F0E2D6",
                    "accents": ["E8A88F", "9DB8A0", "B9A6D3"], "text_accents": ["8E4430", "3F5E45", "5A4780"]},
        "fonts": {"both": {"display": "Trebuchet MS", "body": "Trebuchet MS", "numeral": "Trebuchet MS"},
                  "mac": {"display": "Arial Rounded MT Bold", "body": "Avenir Next", "numeral": "Arial Rounded MT Bold"}},
        "ea": {"display": "sans", "body": "sans"}, "grain": 0, "frames": ["arch", "ellipse", "blob"],
        "forbids": (), "cover": "split-vertical", "skeleton": "island"},
    "collage": {
        "palette": {"ground": "EFE6D2", "ink": "1E1B18", "mute": "5F574C", "panel": "FFFFFF",
                    "accents": ["F2C230", "E4572E", "2E86AB"], "text_accents": ["7A5A00", "A83A14", "1D5A75"]},
        "fonts": {"both": {"display": "Impact", "body": "Arial", "numeral": "Impact"},
                  "mac": {"display": "Impact", "body": "Avenir Next", "numeral": "Impact", "hand": "Bradley Hand"}},
        "ea": {"display": "sans", "body": "sans"}, "ea_heavy": True, "grain": 6, "frames": ["rect"],
        "forbids": (), "cover": "low-left", "skeleton": "band"},
    "storybook": {
        "palette": {"ground": "F6F1E3", "ink": "2F3A2A", "mute": "5E6352", "panel": "EFE7D2",
                    "accents": ["E2734B", "7FA35B", "F2C14E"], "text_accents": ["9A3F1E", "46612F", "7A5C0E"]},
        "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman"},
                  "mac": {"display": "Baskerville", "body": "Georgia", "numeral": "Times New Roman"}},
        "ea": {"display": "serif", "body": "serif"}, "grain": 5, "frames": ["feather"],
        "forbids": ("confetti",), "cover": "centred", "skeleton": "statement"},
    # ── NATIVE languages (P3): drawn, no pictures needed; compositions in vl_native.py ──
    "ink": {
        "palette": {"ground": "F1ECE1", "ink": "1D1C1A", "mute": "645C51", "panel": "E8E1D2",
                    "accents": ["B0362A"], "text_accents": ["A3322A"], "sun": "B0362A"},
        "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman"},
                  "mac": {"display": "Baskerville", "body": "Georgia", "numeral": "Times New Roman"}},
        "ea": {"display": "serif", "body": "serif"}, "grain": 4, "frames": ["feather"],
        "forbids": ("confetti",), "cover": "split-vertical", "skeleton": "rail"},
    "poster": {
        "palette": {"ground": "1F3BFF", "ink": "F3F0E8", "mute": "F3F0E8", "panel": "141414",
                    "accents": ["D7FF3B", "FF4B1F", "141414"], "text_accents": ["D7FF3B", "F3F0E8"]},
        "fonts": {"both": {"display": "Impact", "body": "Arial", "numeral": "Impact", "mono": "Courier New"},
                  "mac": {"display": "Impact", "body": "Helvetica Neue", "numeral": "Impact", "mono": "Courier New"}},
        "ea": {"display": "sans", "body": "sans"}, "ea_heavy": True, "grain": 0, "frames": ["rect"],
        "forbids": (), "cover": "full-bleed-type", "skeleton": "statement"},
    "cutpaper": {
        "palette": {"ground": "FBF2E3", "ink": "2A2733", "mute": "4A4656", "panel": "FFFFFF",
                    "accents": ["EE8A6B", "4E8FC7", "5B3F6E", "5AA38A"], "text_accents": ["A8442D", "2F6F62"],
                    "card_ink": "2A2733", "card_mute": "4A4656", "card_accent": "A8442D"},
        "fonts": {"both": {"display": "Trebuchet MS", "body": "Trebuchet MS", "numeral": "Trebuchet MS"},
                  "mac": {"display": "Avenir Next", "body": "Avenir Next", "numeral": "Avenir Next"}},
        "ea": {"display": "sans", "body": "sans"}, "grain": 3, "frames": ["rect"],
        "forbids": (), "cover": "low-left", "skeleton": "island"},
    "drafting": {
        "palette": {"ground": "F1EFE8", "ink": "1E3A5F", "mute": "3E5674", "panel": "F1EFE8",
                    "accents": ["E2552C"], "text_accents": ["B8401A"]},
        "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman", "mono": "Courier New"},
                  "mac": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman", "mono": "Courier New"}},
        "ea": {"display": "serif", "body": "sans"}, "grain": 0, "frames": ["rect"],
        "forbids": ("confetti",), "cover": "low-left", "skeleton": "split"},
}

# Each language's GROUNDS: its own light paper, and ONE contrast ground (user's decision, 2026-10-04). All four
# light grounds are cream paper, and the register-pixels gate holds a deck whose ground repeats the last decks'
# — after a run of cream decks it held every language. Every text ink passes 4.5:1 on its ground AND panel.
# The storybook contrast is a meadow-green PAPER, not a dark ground: its light watercolours would halo on dark.
VARIANTS = {
    "editorial": {
        "light": {"label": "paper", "label_zh": "纸面版", "grain": 3, "palette": LANGS["editorial"]["palette"]},
        "ink": {"label": "ink", "label_zh": "墨黑版", "grain": 3,
                "palette": {"ground": "1B1A17", "ink": "F3EEE5", "mute": "B8B0A3", "panel": "27251F",
                            "accents": ["D9553C", "5C8FC4"], "text_accents": ["EE7A62", "8DB4DD"]}}},
    "soft": {
        "light": {"label": "cream", "label_zh": "奶油版", "grain": 0, "palette": LANGS["soft"]["palette"]},
        "dusk": {"label": "dusk", "label_zh": "暮色版", "grain": 0,
                 "palette": {"ground": "2E2940", "ink": "F6EEE6", "mute": "CFC5D6", "panel": "3A3450",
                             "accents": ["E8A88F", "9DB8A0", "B9A6D3"], "text_accents": ["F2B49B", "A8CFB1", "CBB8EA"]}}},
    "collage": {
        "light": {"label": "kraft", "label_zh": "牛皮纸版", "grain": 6, "palette": LANGS["collage"]["palette"]},
        "slate": {"label": "slate", "label_zh": "深灰纸版", "grain": 6,
                  "palette": {"ground": "2B2A27", "ink": "F4EEE2", "mute": "C2B9AA", "panel": "3B3934",
                              "accents": ["F2C230", "E4572E", "2E86AB"], "text_accents": ["F2C230", "F08A64", "7CC3E3"]}}},
    "storybook": {
        "light": {"label": "paper", "label_zh": "纸面版", "grain": 5, "palette": LANGS["storybook"]["palette"]},
        "meadow": {"label": "meadow", "label_zh": "草地纸版", "grain": 5,
                   "palette": {"ground": "C3D1B5", "ink": "222E1F", "mute": "3F4B36", "panel": "D3DECA",
                               "accents": ["E2734B", "7FA35B", "F2C14E"], "text_accents": ["772C11", "314526", "584108"]}}},
    "ink": {
        "light": {"label": "xuan paper", "label_zh": "宣纸版", "grain": 4, "palette": LANGS["ink"]["palette"]},
        "night": {"label": "ink night", "label_zh": "墨夜版", "grain": 4,
                  "palette": {"ground": "1C1B19", "ink": "E9E2D2", "mute": "A99F8F", "panel": "262421",
                              "accents": ["B23A2C"], "text_accents": ["E07A63"], "sun": "E8DEC6"}}},
    "poster": {
        "light": {"label": "colour fields", "label_zh": "色场版", "grain": 0, "palette": LANGS["poster"]["palette"]},
        "paper": {"label": "paper", "label_zh": "白纸版", "grain": 0,
                  "palette": {"ground": "F3F0E8", "ink": "141414", "mute": "141414", "panel": "E4DFD3",
                              "accents": ["1F3BFF", "FF4B1F"], "text_accents": ["1F3BFF", "141414"]}}},
    "cutpaper": {
        "light": {"label": "day", "label_zh": "白天版", "grain": 3, "palette": LANGS["cutpaper"]["palette"]},
        "night": {"label": "paper night", "label_zh": "纸夜版", "grain": 3,
                  "palette": {"ground": "1D2742", "ink": "F2EEE4", "mute": "C6C9D6", "panel": "30406A",
                              "accents": ["EE8A6B", "4E8FC7", "5B3F6E", "467E7A"], "text_accents": ["F2A285", "A8D5C4"],
                              "card_ink": "2A2733", "card_mute": "4A4656", "card_accent": "A8442D"}}},
    "drafting": {
        "light": {"label": "vellum", "label_zh": "硫酸纸版", "grain": 0, "palette": LANGS["drafting"]["palette"]},
        "cyanotype": {"label": "cyanotype", "label_zh": "晒图蓝版", "grain": 0,
                      "palette": {"ground": "123254", "ink": "E4ECF5", "mute": "B7C5D6", "panel": "123254",
                                  "accents": ["F27D4E"], "text_accents": ["F59A72"]}}},
}
NATIVE = ("ink", "poster", "cutpaper", "drafting")          # drawn, no pictures needed (vl_native.py)
IMAGE_LED = ("editorial", "soft", "collage", "storybook")    # built around the caller's pictures
# words only the CALLER can give — never invented by the kit; absent means nothing is drawn
NATIVE_EXTRAS = {"ink": ("seal",), "poster": ("highlight",), "cutpaper": ("icons",), "drafting": ("project",)}
# the pages that DRAW each extra; on any other page it is refused, never silently dropped (non-Claude run, 2026-10-05)
EXTRA_PAGES = {"highlight": ("cover", "section", "quote", "closing"), "icons": ("points",)}
_ACTIVE = {}    # language -> the ground key use() set; rs.ground()/rs.card() (no kit) follow it
_PAL_OVERRIDE = {}   # language -> the palette of the CURRENT page, for a language whose palette changes per page (poster)


def _pal(name):
    return _PAL_OVERRIDE.get(name) or VARIANTS[name][_ACTIVE.get(name, "light")]["palette"]


def _rgb(h):
    h = _hex(h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _auto_ground(name, prs, taste=None):
    """(ground key, why) for use(ground="auto"): the language's light ground unless the look history's last three
    decks already sit on it (register-pixels' GROUND REPEAT distance), then its contrast ground. A printed board
    (a registered print format) stays light — print takes a light ground. No history: light."""
    try:
        import formats
        fmt = formats.match(prs.slide_width / 914400.0, prs.slide_height / 914400.0)
    except Exception:
        fmt = None
    if fmt is not None and getattr(fmt, "chrome", "") == "print":
        return "light", "a printed board ({}) takes a light ground".format(fmt.label)
    if taste is None:
        try:
            import registry
            t = registry.taste_file()
            taste = str(t) if t else None
        except Exception:
            taste = None
    if not taste:
        return "light", "no look history on this machine"
    import check_register_pixels as crp
    recent = [cols[0] for _d, cols in crp.look_history(taste)[-3:] if cols]
    if not recent:
        return "light", "the look history is empty"
    order = ["light"] + [k_ for k_ in VARIANTS[name] if k_ != "light"]
    dist = {k_: min(crp._dist(c, _rgb(VARIANTS[name][k_]["palette"]["ground"])) for c in recent) for k_ in order}
    for k_ in order:
        if dist[k_] > crp.SAME_LOOK:
            return k_, ("the last {} deck(s) sit on other grounds".format(len(recent)) if k_ == "light" else
                        "the last {} deck(s) already sit on the light ground (distance {:.0f} <= {:.0f})".format(
                            len(recent), dist["light"], crp.SAME_LOOK))
    best = max(order, key=lambda k_: dist[k_])
    return best, "every ground repeats a recent deck; {} is the furthest (distance {:.0f})".format(best, dist[best])


def _hex(c):
    return c.lstrip("#").upper()


def _lum(c):
    c = _hex(c)
    v = [int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


script_of = dk.script_of                  # one definition, in deckkit (its EA face choice reads it too)


def _platform(platform=None):
    return platform or ("mac" if sys.platform == "darwin" else "win")


class Kit:
    def __init__(self, name, prs, fonts, plan, image_dir, platform, ground="light"):
        self.name, self.prs, self.fonts, self.plan, self.image_dir = name, prs, fonts, plan, image_dir
        self.L, self.platform = LANGS[name], _platform(platform)
        self.ground = ground
        self.project, self.field = None, None            # drafting's title-block words; poster's current field
        self.P = dict(VARIANTS[name][ground]["palette"])  # a COPY of the ground's palette (poster swaps it per page)
        self.grain = VARIANTS[name][ground]["grain"]
        self._fonts = dict(self.L["fonts"]["both"])
        if fonts == "mac":
            self._fonts.update(self.L["fonts"]["mac"])

    def face(self, role):
        return self._fonts.get(role) or self._fonts["body"]

    def ea_face(self, role, text):
        scr = script_of(text)
        if scr is None:
            return None
        kind = self.L["ea"]["display" if role in ("display", "numeral") else "body"]
        return EA_FACES[scr][kind]["mac" if self.platform == "mac" else "win"]

    def color(self, key, i=0):
        p = self.P
        v = p[key][i] if isinstance(p[key], list) else p[key]
        return dk.RGBColor.from_string(_hex(v))

    def run(self, text, size, color=None, bold=False, role="body", italic=False):
        """One run in the language: its face for `role`, the script's East-Asian face, no CJK italics. A run that
        is mostly digits is set in a LINING face when the role's face has old-style figures (Georgia)."""
        cjk = dk._has_cjk(text)
        if cjk and role in ("display", "numeral") and self.L.get("ea_heavy"):
            bold = True                      # Impact/Arial Black have no CJK: the EA face carries the weight
        return (text, size, color or self.color("ink"), bold, italic and not cjk,   # Chinese has no italics
                dk.numeral_run_face(text, self.face(role)), self.ea_face(role, text))

    def runs(self, text, size, color=None, bold=False, role="body", italic=False):
        """The runs of one paragraph: run(), with every digit sequence inside an OLD-STYLE figure face (Georgia)
        split into a run in a lining face of the same register — "Repair café 2026" never bobs (final review,
        2026-10-04; lining figures always). Use it for any text that may contain digits."""
        r = self.run(text, size, color, bold, role, italic)
        if not any(c.isdigit() for c in text) or not dk.has_oldstyle_figures(r[5]):
            return [r]
        lining = dk.numeral_face(r[5])
        return [((part,) + r[1:5] + ((lining if part[0].isdigit() else r[5]),) + r[6:])
                for part in re.split(r"(\d(?:[\d,.:/%\u2013-]*\d)?%?)", text) if part]

    def new_slide(self):
        """A slide in the language: paints the language's ground (its grain, where it has one) and names the
        slide `vl.<language>` (the OOXML slide name, nothing drawn) — so an ordinary page built on it (agenda,
        chart) counts as IN the language for the delivery gate, which a plain dk.add_slide page does not."""
        s = dk.add_slide(self.prs)
        s._element.cSld.set("name", "vl." + self.name)
        if self.grain:
            import surfaces
            surfaces.grain_background(s, self.P["ground"], strength=self.grain)
        if self.name in NATIVE:                 # poster's colour field, drafting's drawing sheet
            import vl_native
            vl_native.paint_ground(self, s)
        return s


def use(name, prs, *, fonts="both", plan=None, image_dir=None, platform=None, ground="light"):
    """Start a deck in a curated VISUAL LANGUAGE ("editorial", "soft", "collage", "storybook"): sets the
    palette, fonts and ground, and returns a Kit whose page functions — cover, section, image_text, quote,
    data, closing — lay out your own words and images in that language. fonts="both" uses only faces on
    macOS AND Windows; fonts="mac" unlocks Mac-only faces. plan/image_dir let image= take P1 series slot
    ids. ground="light" (default), the language's contrast ground (VARIANTS[name]), or "auto": the light ground
    unless your last decks already sit on it (the look history) — then the contrast one; printed boards stay
    light. Record design_plan.visual_language = name and vl_ground (references/visual-languages.md)."""
    if name not in LANGS:
        raise KeyError("visual_languages.use(): unknown language {!r} — one of {}".format(name, sorted(LANGS)))
    if fonts not in ("both", "mac"):
        raise ValueError("visual_languages.use(): fonts must be 'both' (macOS + Windows faces) or 'mac', got {!r}".format(fonts))
    if ground == "auto":
        ground, why = _auto_ground(name, prs)
        import shlex as _shq
        print("[visual_languages] {}: ground {!r} ({}) — {}. Record it (DECK_DIR = the folder the deck is saved in, "
              "TOPIC = what it is for): python3 {} --gates {} --ground {} --deck DECK_DIR --for TOPIC".format(
                  name, ground, VARIANTS[name][ground]["label_zh"], why, _shq.quote(str(Path(__file__).resolve())),
                  name, ground))
    if ground not in VARIANTS[name]:
        raise ValueError("visual_languages.use(): ground must be 'auto' or one of {} for {}, got {!r}".format(
            sorted(VARIANTS[name]), name, ground))
    k = Kit(name, prs, fonts, plan, image_dir, platform, ground)
    _ACTIVE[name] = ground
    _PAL_OVERRIDE.clear()      # a new deck starts clean: no language keeps the last deck's per-page palette
    if fonts == "mac":
        missing = [f for f in set(k._fonts.values()) if dk._font_substituted(f)]
        if missing:
            raise ValueError("visual_languages.use(): fonts='mac' needs {} — not installed here; use fonts='both'".format(missing))
    p = k.P
    ta = p["text_accents"]
    dk.set_palette(deep=_hex(p["ink"]), slate=_hex(p["mute"]), mute=_hex(p["mute"]), tint=_hex(p["panel"]),
                   magenta=_hex(ta[0]), blue=_hex(ta[1 % len(ta)]), teal=_hex(ta[2 % len(ta)]),
                   accents=[_hex(a) for a in ta],
                   font=k.face("body"), display=k.face("display"),
                   eafont=EA_FACES["han"][k.L["ea"]["body"]][k.platform],
                   eadisplay=EA_FACES["han"][k.L["ea"]["display"]][k.platform])
    dk.set_ground(_hex(p["ground"]))
    dk.HANG_PUNCT = dk.deck_hangs_punct(prs)     # CJK line ends follow what THIS deck declares
    return k


def _ground_editorial(slide, role, index):
    W, H = rs._canvas(slide)
    rs._shape(slide, MSO_SHAPE.RECTANGLE, 0.5, H - 0.42, W - 1.0, 0.012, fill=dk.DEEP, texture=True)   # folio hairline
    return (0.5, 0.45, W - 1.0, H - 1.05)


def _soft_fill(index):
    """The soft language's blob colour for page `index` — its fill-only accents in turn (never text)."""
    acc = _pal("soft")["accents"]
    return dk.RGBColor.from_string(acc[index % len(acc)])


def _ground_soft(slide, role, index):
    W, H = rs._canvas(slide)
    if role in ("cover", "section"):
        rs._shape(slide, MSO_SHAPE.OVAL, W * 0.72, -H * 0.18, W * 0.42, W * 0.42, fill=_soft_fill(index), texture=True)
    return (0.5, 0.5, W * (0.62 if role in ("cover", "section") else 0.9), H - 1.0)


def _ground_collage(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.45, 0.45, W - 0.9, H - 0.9)


def _ground_storybook(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.55, 0.5, W - 1.1, H - 1.0)


def _ground_ink(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.6, 0.55, W - 1.2, H - 1.1)


def _ground_poster(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.55, 0.85, W - 1.1, H - 1.4)


def _ground_cutpaper(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.6, 0.6, W - 1.2, H - 1.2)


def _ground_drafting(slide, role, index):
    W, H = rs._canvas(slide)
    s = min(W, H) / 7.5
    return (0.9 * s, 0.78 * s, W - 1.8 * s, H - 2.6 * s)      # above the title block


def _card_for(name):
    """The language's card: its panel colour; soft is rounded, the others square."""
    def card(slide, x, y, w, h, label=None):
        p = _pal(name)                        # the ground use() set: a card on the ink ground is an ink card
        soft = name == "soft"
        body = dk.box(slide, x, y, w, h, fill=_hex(p["panel"]), line=None, round=soft, r=0.22 if soft else None)
        header = None
        if label:
            scr = script_of(label)            # a Korean label gets a Hangul face, not the deck's Han face
            ea = (EA_FACES[scr][LANGS[name]["ea"]["body"]][_platform()],) if scr else ()
            header = dk.text(slide, x + 0.16, y + 0.12, max(0.5, w - 0.32), 0.4,
                             [[(label, 12, dk.RGBColor.from_string(_hex(p["text_accents"][0])), True, False,
                                LANGS[name]["fonts"]["both"]["body"]) + ea]])
        return body, header
    card.__name__ = "_card_" + name
    return card


_card_editorial, _card_soft, _card_collage, _card_storybook = (_card_for(n) for n in ("editorial", "soft", "collage", "storybook"))
_card_ink, _card_poster, _card_cutpaper, _card_drafting = (_card_for(n) for n in ("ink", "poster", "cutpaper", "drafting"))


for _n in LANGS:
    rs.register(_n, ground=globals()["_ground_" + _n], card=globals()["_card_" + _n],
                forbids=LANGS[_n]["forbids"], source=__file__)


# ════════════════════════════════════════════════════════════════════════════════════════════════
# Page compositions — one engine, layouts as DATA.
#
# A page = an optional image (with the language's treatment) + a TEXT COLUMN in which the caller's
# fields are flowed top-down by MEASURED height (the same 1.2-em line model lint reads), shrunk toward
# each field's floor when they do not fit, and REFUSED (VLTextOverflow) when even the floors overflow —
# never truncated, never spilled. Long single words are sized by their real glyph width, because
# measure_text only breaks at spaces (display_type, 2026-10-03: "BRO / KEN").
# ════════════════════════════════════════════════════════════════════════════════════════════════

class VLTextOverflow(ValueError):
    """A page's text cannot fit its column even at the language's floor sizes."""


# field: (size_pt at a 7.5in short side, role, bold, colour key, italic, floor_pt)
TYPE = {
    "editorial": {"kicker": (14, "body", True, "accent", False, 10), "title": (54, "display", False, "ink", False, 28),
                  "subtitle": (18, "body", False, "ink", False, 12), "body": (17, "body", False, "ink", False, 11),
                  "mark": (110, "display", False, "accent", False, 40), "quote": (32, "display", False, "ink", True, 18),
                  "attribution": (14, "body", True, "accent", False, 10), "number": (150, "numeral", True, "accent", False, 44),
                  "label": (24, "display", False, "ink", False, 14), "note": (15, "body", False, "ink", False, 10),
                  "caption": (12, "body", False, "ink", False, 9), "line": (20, "body", False, "ink", False, 12)},
    "soft": {"kicker": (15, "body", True, "accent", False, 10), "title": (48, "display", True, "ink", False, 26),
             "subtitle": (18, "body", False, "ink", False, 12), "body": (17, "body", False, "ink", False, 11),
             "mark": (90, "display", True, "accent", False, 36), "quote": (30, "display", False, "ink", False, 17),
             "attribution": (14, "body", True, "accent", False, 10), "number": (120, "numeral", True, "ink", False, 40),
             "label": (24, "display", True, "ink", False, 14), "note": (15, "body", False, "ink", False, 10),
             "caption": (12, "body", False, "ink", False, 9), "line": (20, "body", False, "ink", False, 12)},
    "collage": {"kicker": (16, "body", True, "ink", False, 10), "title": (62, "display", False, "ink", False, 30),
                "subtitle": (18, "body", False, "ink", False, 12), "body": (17, "body", False, "ink", False, 11),
                "mark": (100, "display", False, "accent", False, 36), "quote": (30, "display", False, "ink", False, 17),
                "attribution": (15, "body", True, "ink", False, 10), "number": (170, "numeral", False, "accent", False, 48),
                "label": (26, "display", False, "ink", False, 14), "note": (15, "body", False, "ink", False, 10),
                "caption": (12, "body", False, "ink", False, 9), "line": (22, "body", True, "ink", False, 12)},
    "storybook": {"kicker": (15, "body", False, "accent", True, 10), "title": (50, "display", False, "ink", False, 26),
                  "subtitle": (18, "body", False, "ink", True, 12), "body": (17, "body", False, "ink", False, 11),
                  "mark": (110, "display", False, "accent", False, 40), "quote": (30, "display", False, "ink", True, 17),
                  "attribution": (14, "body", False, "accent", True, 10), "number": (150, "numeral", False, "accent", False, 44),
                  "label": (24, "display", False, "ink", False, 14), "note": (15, "body", False, "ink", False, 10),
                  "caption": (12, "body", False, "ink", True, 9), "line": (20, "body", False, "ink", True, 12)},
    "ink": {"kicker": (13, "body", False, "mute", False, 10), "title": (52, "display", False, "ink", False, 26),
            "subtitle": (19, "body", False, "mute", False, 12), "body": (17, "body", False, "ink", False, 11),
            "mark": (60, "display", False, "accent", False, 30), "quote": (44, "display", False, "ink", False, 22),
            "attribution": (15, "body", False, "mute", False, 10), "number": (230, "numeral", False, "ink", False, 40),
            "label": (34, "display", False, "ink", False, 16), "note": (16, "body", False, "mute", False, 10),
            "caption": (12, "body", False, "mute", False, 9), "line": (20, "body", False, "ink", False, 12),
            "item_head": (28, "display", False, "ink", False, 14), "item_line": (17, "body", False, "mute", False, 10)},
    "poster": {"kicker": (11, "mono", True, "ink", False, 9), "title": (150, "display", False, "ink", False, 44),
               "subtitle": (20, "body", True, "ink", False, 12), "body": (18, "body", False, "ink", False, 11),
               "mark": (300, "display", False, "accent", False, 120), "quote": (90, "display", False, "ink", False, 34),
               "attribution": (12, "mono", True, "accent", False, 10), "number": (380, "numeral", False, "ink", False, 110),
               "label": (70, "display", False, "ink", False, 26), "note": (19, "body", True, "ink", False, 12),
               "caption": (12, "body", False, "ink", False, 9), "line": (24, "body", True, "ink", False, 14),
               "item_head": (18, "body", True, "ink", False, 12), "item_line": (14, "body", False, "ink", False, 10)},
    "cutpaper": {"kicker": (14, "body", True, "accent", False, 10), "title": (60, "display", True, "ink", False, 28),
                 "subtitle": (20, "body", False, "mute", False, 12), "body": (18, "body", False, "ink", False, 11),
                 "mark": (90, "display", True, "accent", False, 40), "quote": (44, "display", True, "ink", False, 20),
                 "attribution": (13, "body", True, "accent", False, 10), "number": (200, "numeral", True, "ink", False, 36),
                 "label": (44, "display", True, "ink", False, 20), "note": (19, "body", False, "mute", False, 11),
                 "caption": (12, "body", False, "mute", False, 9), "line": (22, "body", False, "ink", False, 12),
                 "item_head": (28, "display", True, "ink", False, 14), "item_line": (17, "body", False, "mute", False, 10)},
    "drafting": {"kicker": (11, "mono", True, "accent", False, 9), "title": (54, "display", False, "ink", False, 26),
                  "subtitle": (16, "display", False, "mute", True, 11), "body": (16, "body", False, "ink", False, 10),
                  "mark": (60, "display", False, "accent", False, 30), "quote": (44, "display", False, "ink", True, 20),
                  "attribution": (11, "mono", True, "mute", False, 9), "number": (330, "numeral", False, "ink", False, 40),
                  "label": (46, "display", False, "ink", False, 20), "note": (16, "display", False, "mute", True, 10),
                  "caption": (10, "mono", True, "mute", False, 8), "line": (20, "display", False, "ink", True, 12),
                  "item_head": (11, "mono", True, "ink", False, 9), "item_line": (15, "display", False, "mute", False, 10)},
}

# page -> its fields in column order (the caller's keyword names)
PAGE_FIELDS = {"cover": ("kicker", "title", "subtitle"), "section": ("number", "kicker", "title"),
               "image_text": ("kicker", "title", "body", "caption"), "quote": ("mark", "quote", "attribution"),
               "data": ("number", "label", "note"), "closing": ("title", "line"),
               "points": ("kicker", "title", "items")}


def L_(image, treat, col, *, col_noimg=None, anchor="middle", align="l", frame="rect", square=False, deco=()):
    return {"image": image, "treat": treat, "col": col, "col_noimg": col_noimg or col, "anchor": anchor,
            "align": align, "frame": frame, "square": square, "deco": tuple(deco)}


LAYOUTS = {
    "editorial": {
        "cover": {"land": L_((0, 0, 1, 1), "bleed", None, col_noimg=(.08, .22, .70, .60), anchor="bottom", deco=["rule"]),
                  "port": L_((0, 0, 1, .56), "frame", (.08, .60, .84, .33), col_noimg=(.08, .25, .84, .50), anchor="top", deco=["rule"])},
        "section": {"land": L_((.56, 0, .44, 1), "frame", (.08, .16, .42, .70), col_noimg=(.08, .16, .72, .70), anchor="bottom", deco=["rule"]),
                    "port": L_((0, 0, 1, .40), "frame", (.08, .45, .84, .45), col_noimg=(.08, .22, .84, .60), anchor="bottom", deco=["rule"])},
        "image_text": {"land": L_((0, 0, .56, 1), "frame", (.62, .14, .32, .72)),
                       "port": L_((0, 0, 1, .48), "frame", (.08, .52, .84, .41), anchor="top")},
        "quote": {"land": L_((.68, .12, .24, .76), "frame", (.08, .12, .54, .76), col_noimg=(.12, .12, .76, .76), frame="arch"),
                  "port": L_((.30, .05, .40, .24), "frame", (.08, .33, .84, .58), col_noimg=(.08, .18, .84, .70), frame="arch")},
        "data": {"land": L_((.62, .10, .30, .80), "frame", (.08, .12, .48, .76), col_noimg=(.08, .12, .80, .76)),
                 "port": L_((0, 0, 1, .34), "frame", (.08, .40, .84, .52), col_noimg=(.08, .18, .84, .70))},
        "closing": {"land": L_((0, 0, 1, 1), "bleed", None, col_noimg=(.12, .30, .76, .40), align="c"),
                    "port": L_((0, 0, 1, .60), "frame", (.08, .64, .84, .28), col_noimg=(.08, .30, .84, .40), align="c")},
    },
    "soft": {
        "cover": {"land": L_((.58, .08, .34, .84), "frame", (.07, .16, .46, .68), frame="arch", deco=["blob"]),
                  "port": L_((.14, .04, .72, .50), "frame", (.08, .58, .84, .35), frame="arch", anchor="top", deco=["blob"])},
        "section": {"land": L_((.64, .18, .28, .64), "frame", (.08, .16, .50, .68), col_noimg=(.08, .16, .80, .68), frame="ellipse", square=True, deco=["circle"]),
                    "port": L_((.25, .05, .50, .30), "frame", (.08, .40, .84, .52), col_noimg=(.08, .22, .84, .62), frame="ellipse", square=True, deco=["circle"])},
        "image_text": {"land": L_((.05, .10, .44, .80), "frame", (.56, .16, .38, .68), frame="blob", deco=["card"]),
                       "port": L_((.08, .04, .84, .44), "frame", (.08, .52, .84, .42), frame="blob", anchor="top", deco=["card"])},
        "quote": {"land": L_((.70, .30, .20, .40), "frame", (.12, .16, .54, .68), col_noimg=(.14, .16, .72, .68), frame="ellipse", square=True, deco=["card"]),
                  "port": L_((.32, .04, .36, .20), "frame", (.08, .30, .84, .60), col_noimg=(.08, .18, .84, .70), frame="ellipse", square=True, deco=["card"])},
        "data": {"land": L_((.64, .10, .28, .80), "frame", (.08, .14, .50, .72), col_noimg=(.08, .14, .80, .72), frame="arch", deco=["circle"]),
                 "port": L_((.20, .04, .60, .34), "frame", (.08, .42, .84, .50), col_noimg=(.08, .20, .84, .68), frame="arch", deco=["circle"])},
        "closing": {"land": L_((.60, .14, .32, .72), "frame", (.08, .22, .48, .56), col_noimg=(.12, .30, .76, .40), frame="ellipse", square=True, align="l"),
                    "port": L_((.20, .05, .60, .40), "frame", (.08, .52, .84, .40), col_noimg=(.08, .30, .84, .40), frame="ellipse", square=True, align="c", anchor="top")},
    },
    "collage": {
        "cover": {"land": L_((.45, .06, .51, .88), "collage", (.05, .14, .37, .72), col_noimg=(.07, .18, .80, .64), deco=["scribble"]),
                  "port": L_((.06, .40, .88, .54), "collage", (.06, .05, .88, .32), col_noimg=(.06, .20, .88, .60), anchor="top", deco=["scribble"])},
        "section": {"land": L_((.66, .12, .28, .76), "print", (.07, .14, .55, .72), col_noimg=(.07, .14, .80, .72)),
                    "port": L_((.15, .04, .70, .34), "print", (.06, .42, .88, .50), col_noimg=(.06, .20, .88, .66))},
        "image_text": {"land": L_((.04, .07, .52, .86), "print", (.60, .14, .34, .72), deco=["scribble"]),
                       "port": L_((.06, .03, .88, .46), "print", (.06, .53, .88, .40), anchor="top", deco=["scribble"])},
        "quote": {"land": L_((.70, .16, .24, .68), "print", (.14, .18, .52, .62), col_noimg=(.16, .18, .68, .62), deco=["note"]),
                  "port": L_((.25, .03, .50, .26), "print", (.10, .36, .80, .52), col_noimg=(.10, .20, .80, .62), deco=["note"])},
        "data": {"land": L_((.62, .10, .32, .80), "print", (.07, .14, .50, .72), col_noimg=(.07, .14, .80, .72)),
                 "port": L_((.12, .03, .76, .34), "print", (.06, .42, .88, .50), col_noimg=(.06, .20, .88, .66))},
        "closing": {"land": L_((.50, .08, .45, .84), "collage", (.06, .20, .40, .60), col_noimg=(.10, .28, .80, .44), deco=["scribble"]),
                    "port": L_((.06, .42, .88, .52), "collage", (.06, .06, .88, .30), col_noimg=(.06, .28, .88, .44), anchor="top", deco=["scribble"])},
    },
    "storybook": {
        "cover": {"land": L_((.06, .03, .88, .64), "feather", (.12, .69, .76, .25), col_noimg=(.12, .24, .76, .52), anchor="top", align="c"),
                  "port": L_((.03, .03, .94, .52), "feather", (.08, .58, .84, .35), col_noimg=(.08, .24, .84, .52), anchor="top", align="c"),
                  # *_tall: a PORTRAIT illustration — contained in a wide frame it filled 27-50% of it (a sliver on
                  # the quote page, the user, 2026-10-04); picked by the picture's own aspect (_compose)
                  "land_tall": L_((.05, .05, .44, .90), "feather", (.53, .22, .40, .56), align="c"),
                  "port_tall": L_((.14, .03, .72, .58), "feather", (.08, .64, .84, .30), anchor="top", align="c")},
        "section": {"land": L_((.54, .08, .42, .84), "feather", (.08, .18, .44, .64), col_noimg=(.12, .18, .76, .64), align="l"),
                    "port": L_((.06, .04, .88, .38), "feather", (.08, .46, .84, .46), col_noimg=(.08, .22, .84, .60), align="c"),
                    "port_tall": L_((.20, .03, .60, .50), "feather", (.08, .56, .84, .38), align="c")},
        "image_text": {"land": L_((.03, .08, .53, .84), "feather", (.60, .16, .34, .68)),
                       "port": L_((.04, .03, .92, .46), "feather", (.08, .52, .84, .42), anchor="top"),
                       "port_tall": L_((.18, .03, .64, .48), "feather", (.08, .54, .84, .40), anchor="top")},
        "quote": {"land": L_((.34, .02, .32, .34), "feather", (.14, .38, .72, .50), col_noimg=(.14, .18, .72, .66), align="c"),
                  "port": L_((.30, .03, .40, .20), "feather", (.08, .27, .84, .64), col_noimg=(.08, .18, .84, .70), align="c"),
                  "land_tall": L_((.08, .08, .32, .84), "feather", (.44, .16, .48, .68), align="c"),
                  "port_tall": L_((.25, .03, .50, .36), "feather", (.08, .42, .84, .50), align="c")},
        "data": {"land": L_((.58, .08, .38, .84), "feather", (.08, .14, .48, .72), col_noimg=(.12, .14, .76, .72)),
                 "port": L_((.06, .03, .88, .36), "feather", (.08, .42, .84, .50), col_noimg=(.08, .20, .84, .66)),
                 "port_tall": L_((.20, .03, .60, .44), "feather", (.08, .50, .84, .44))},
        "closing": {"land": L_((.15, .03, .70, .62), "feather", (.12, .68, .76, .25), col_noimg=(.12, .30, .76, .40), anchor="top", align="c"),
                    "port": L_((.04, .03, .92, .52), "feather", (.08, .58, .84, .34), col_noimg=(.08, .30, .84, .40), anchor="top", align="c"),
                    "land_tall": L_((.05, .05, .44, .90), "feather", (.53, .22, .40, .56), align="c"),
                    "port_tall": L_((.16, .03, .68, .56), "feather", (.08, .62, .84, .32), anchor="top", align="c")},
    },
}

GAP = 0.10            # inches between flowed fields at a 7.5in short side
HEAD_GAP = 0.20       # after the page's display field: lint's HEADLINE_CROWDED asks >= 0.18in of INK, and ink
                      # sits inside the box, so a box gap of 0.20 (never scaled below it) clears it by construction
_INSET = 0.056        # text() insets 0.028in a side
_FOOT = 0.55          # keep text out of the reserved footer band


def _canvas(k):
    return k.prs.slide_width / 914400.0, k.prs.slide_height / 914400.0


def _unbreakable_overwide(k, field, text, size, w):
    """The first word the renderer cannot keep whole AND will not break sensibly: a Latin token (identifier,
    URL, compound) wider than the column. A Korean word that is too wide breaks between syllables and is
    measured that way; Chinese/Japanese break between characters. None when every such word fits."""
    import display_type as dt
    if dk._has_cjk(text) and not any(dk._is_hangul(ord(c)) for c in text):
        return None
    role, bold = TYPE[k.name][field][1], TYPE[k.name][field][2]
    for word in text.split():
        if dk._has_cjk(word):
            continue
        if (dt._glyph_width(word, size, k.face(role), bold) or 0) > w - _INSET:
            return word
    return None


def _outlinable(k, text):
    """A collage numeral is drawn as an outlined picture only when its face is installed here and draws every
    character; otherwise it is a text run (the EA face for CJK) — never tofu, never a refused page on a machine
    without Impact (Linux, 2026-10-04)."""
    import display_type as dt
    return k.name == "collage" and len(text) <= 6 and dt.covers(k.face("numeral"), text)


def _field_height(k, field, text, size, w):
    _sz, role, bold = size, TYPE[k.name][field][1], TYPE[k.name][field][2]
    if field == "number" and _outlinable(k, text):
        return size / 72.0 * 1.0                                   # an outlined picture, one line
    runs = [(text, bold)]
    # measure East-Asian text with the EA face it renders in: a Latin face's metrics made a Korean quote
    # one line where the render (and lint) set two, and it ran into its attribution
    face = k.ea_face(role, text) if dk._has_cjk(text) else k.face(role)
    # the larger of measure_text's count (what lint reads) and a break by the REAL glyphs of the style the
    # run renders in — an italic quote measured at upright widths rendered one line longer (2026-10-03)
    lines = max(dk._measure_lines(runs, size, max(0.2, w - _INSET), font=face), len(_break_lines(k, field, text, size, w)))
    lh = dk._LINT_LINE_H * (dk.CJK_LS if dk._has_cjk(text) else 1.0)
    return lines * size / 72.0 * lh + 0.06


def _widest_word_fits(k, field, text, size, w):
    import display_type as dt
    role, bold = TYPE[k.name][field][1], TYPE[k.name][field][2]
    korean = any(dk._is_hangul(ord(c)) for c in text)
    if dk._has_cjk(text) and not korean:
        return True                       # Chinese/Japanese break between characters; Korean words do not
    face = k.ea_face(role, text) if korean else k.face(role)
    return all((dt._glyph_width(word, size, face, bold) or 0) <= (w - _INSET) for word in text.split())


def _break_lines(k, field, text, size, w):
    """Greedy line breaks with the real glyph widths of the face the run renders in (words for Latin,
    characters for CJK) — an approximation of the renderer, good enough to see a widow. CJK line ends as
    LibreOffice sets them (deckkit _CJK_HANG / _CJK_CLOSE / _CJK_OPEN, probed): ONE closing mark hangs past
    the measure — in pure CJK text only, as measure_text; a closing bracket, or a second mark, takes the hung
    mark and the ideograph before it down; an opening bracket never ends a line."""
    import display_type as dt
    role, bold, italic = TYPE[k.name][field][1], TYPE[k.name][field][2], TYPE[k.name][field][4]
    cjk = dk._has_cjk(text)
    face = k.ea_face(role, text) if cjk else k.face(role)
    italic = italic and not cjk
    korean = any(dk._is_hangul(ord(c)) for c in text)     # wraps at spaces, like Latin (LibreOffice probe)
    units, joiner = (list(text), "") if cjk and not korean else (text.split(" "), " ")
    limit = w - _INSET
    may_hang = (dk.HANG_PUNCT and cjk and not korean and not any(c.isascii() and c.isalnum() for c in text)
                and limit >= 2 * size / 72.0)
    cjk = cjk and not korean                               # below: per-character CJK rules only

    def width(s_):
        return dt._glyph_width(s_, size, face, bold, italic) or 0
    # (separator, unit) pairs; a Korean word wider than the whole line goes in as syllables — the renderer
    # breaks it between them ("인공지능기반의 / 료영상재구성", final review 2026-10-04)
    toks = []
    for i_, u in enumerate(units):
        sep = joiner if i_ else ""
        if korean and len(u) > 1 and width(u) > limit:
            toks += [(sep if j_ == 0 else "", c_) for j_, c_ in enumerate(u)]
        else:
            toks.append((sep, u))
    lines, cur = [], ""
    for sep, u in toks:
        nxt = (cur + sep + u) if cur else u
        if not cur or width(nxt) <= limit:
            cur = nxt
        elif may_hang and u in dk._CJK_HANG and width(cur) <= limit:
            cur = nxt                                      # one closing mark hangs at the line end
        elif cjk and (u in dk._CJK_CLOSE or u in dk._CJK_HANG):
            hung = len(cur) - len(cur.rstrip(dk._CJK_HANG))
            take = hung + 1 if len(cur) > hung + 1 else hung
            if 0 < take < len(cur):
                lines.append(cur[:-take])
                cur = cur[-take:] + u                      # "一二三四五 / 六。」"
            else:
                cur = nxt                                  # nothing to carry: it overflows, as the renderer does
        elif cjk and len(cur) > 1 and cur[-1] in dk._CJK_OPEN:
            lines.append(cur[:-1])                         # "意度很高 / （详见附"
            cur = cur[-1] + u
        else:
            lines.append(cur)
            cur = u
    return lines + [cur]


def _widowed(k, field, text, size, w):
    """True when the last line is a lone short word (Latin) or one or two characters (CJK)."""
    ls = _break_lines(k, field, text, size, w)
    if len(ls) < 2:
        return False
    last = ls[-1].strip()
    korean = any(dk._is_hangul(ord(c)) for c in text)
    return len(last) <= 2 if dk._has_cjk(text) and not korean else len(last.split()) <= 1


_NO_WIDOW = ("title", "quote", "label", "line", "subtitle")
_CLAUSE_CJK = "，。、；：！？"
_CLAUSE_LATIN = ".,;:!?—–"
_CLOSE = "）」』》\"'”’)"


def _at_clause(line):
    t = line.rstrip().rstrip(_CLOSE)
    return bool(t) and t[-1] in _CLAUSE_CJK + _CLAUSE_LATIN


def _clause_cuts(text):
    """Offsets just after each clause mark INSIDE the text: a full-width mark anywhere, an ASCII mark or dash
    only before a space (so "3.5" and "e.g.x" never cut) — Korean uses ASCII marks between spaced words."""
    cuts, n = [], len(text)
    for i, ch in enumerate(text[:-1]):
        if ch in _CLAUSE_CJK or (ch in _CLAUSE_LATIN and text[i + 1] == " "):
            j = i + 1
            while j < n and text[j] in _CLOSE:
                j += 1
            if text[j:].strip():
                cuts.append(j)
    return sorted(set(cuts))


def _one_line(k, f, seg, size, w):
    """The segment sits on ONE line by both models (the glyph break and measure_text, which lint reads), with
    3% to spare for a renderer a little wider than either."""
    role, bold = TYPE[k.name][f][1], TYPE[k.name][f][2]
    face = k.ea_face(role, seg) if dk._has_cjk(seg) else k.face(role)
    ww = w * 0.97
    return (len(_break_lines(k, f, seg, size, ww)) == 1
            and dk._measure_lines([(seg, bold)], size, max(0.2, ww - _INSET), font=face) == 1)


def _phrase_lines(k, f, t, sz, w, min_size):
    """(size, lines) with every break after a clause mark — "带着坏东西来，/ 带着好东西走", "Bring it broken. /
    Take it home working." — clauses packed greedily, at the largest size from sz down to min_size, never more
    lines than the plain break at sz. None when the text already breaks at its clauses, has none, or a clause
    cannot sit on one line. Greedy WRAPPING cannot do this at any measure (it fills the first line), so the
    lines are set as explicit paragraphs."""
    cuts = _clause_cuts(t)
    if not cuts:
        return None
    base = _break_lines(k, f, t, sz, w)
    if len(base) < 2 or all(_at_clause(l_) for l_ in base[:-1]):
        return None
    steps, s = [], sz
    while s > min_size + 1e-6:
        steps.append(s)
        s *= 0.95
    for s in steps + [min_size]:                      # 5% steps, and the bound itself
        lines, start, last_ok = [], 0, None
        for b in cuts + [len(t)]:
            if _one_line(k, f, t[start:b].strip(), s, w):
                last_ok = b
                continue
            if last_ok is None:
                lines = None                         # a clause wider than the line at this size
                break
            lines.append(t[start:last_ok].strip())
            start, last_ok = last_ok, None
            if not _one_line(k, f, t[start:b].strip(), s, w):
                lines = None
                break
            last_ok = b
        if lines is not None:
            lines.append(t[start:].strip())
            if len(lines) <= len(base):
                return s, lines
    return None


def _balanced_width(k, f, t, sz, w):
    """A narrower measure at which the same text has no widow (text-wrap: balance), or None."""
    import display_type as dt
    n = len(_break_lines(k, f, t, sz, w))
    if n < 2:
        return None
    role, bold = TYPE[k.name][f][1], TYPE[k.name][f][2]
    face = k.ea_face(role, t) if dk._has_cjk(t) else k.face(role)
    full = dt._glyph_width(t, sz, face, bold) or 0
    wb = full / n + _INSET
    while wb < w:
        if len(_break_lines(k, f, t, sz, wb)) == n and not _widowed(k, f, t, sz, wb):
            return wb
        wb *= 1.04
    return None


def _flow(k, slide, page, col, items, *, anchor, align, underlay=None, start=None):
    """PLAN the fields of one page in its column by measured height; returns (rects, draw).

    Sizes start at the language's sizes (scaled to the canvas), shrink toward each field's floor until
    the column holds them, and refuse (VLTextOverflow) when even the floors overflow. A word wider than
    the column shrinks that field; a title ending in a lone word / one or two CJK characters shrinks a
    little, or — when that cannot fix it — is set in a narrower, BALANCED measure ("not for / you",
    "工具其实很 / 少", "先种下第 / 一株", 2026-10-03). Nothing is drawn until draw() is called, so a
    card can be sized to the text it backs."""
    from pptx.enum.text import PP_ALIGN
    x, y, w, h = col
    W, H = _canvas(k)
    h = min(h, H - _FOOT - y)
    s = min(W, H) / 7.5
    sizes, floors, widths = {}, {}, {}
    for f, _t in items:
        base, *_rest, floor = TYPE[k.name][f]
        sizes[f], floors[f], widths[f] = (start or {}).get(f, base * s), max(9.0, floor * s), w
    gap = GAP * s
    order = [f for f, _ in items]
    head = max(order, key=lambda f: TYPE[k.name][f][0])          # the display field, by design
    # both sides of it: when the title sits low on a cover, lint reads the kicker above it as the headline
    gaps = {f: (max(HEAD_GAP, 2 * GAP * s) if head in (f, nxt) else gap) for f, nxt in zip(order, order[1:])}
    gaps[order[-1]] = 0.0

    # field -> its explicit lines: the author's own line breaks ("Line one\nLine two"), or clause lines
    # (_phrase_lines). One paragraph per line; each measured on its own, as dk.text sets them.
    phrased = {f: [l_.strip() for l_ in t.split("\n") if l_.strip()] for f, t in items if "\n" in t}

    def fheight(f, t, sz, fw):
        if f in phrased:
            return sum(_field_height(k, f, l_, sz, fw) - 0.06 for l_ in phrased[f]) + 0.06
        return _field_height(k, f, t, sz, fw)

    def total():
        return sum(fheight(f, t, sizes[f], widths[f]) + gaps[f] for f, t in items)
    for f, t in items:
        while sizes[f] > floors[f] and not _widest_word_fits(k, f, t, sizes[f], w):
            sizes[f] = max(floors[f], sizes[f] * 0.94)
        bad = _unbreakable_overwide(k, f, t, sizes[f], w) if not (f == "number" and _outlinable(k, t)) else None
        if bad:                           # it would break mid-word and run into the next field (final review)
            raise VLTextOverflow("{}.{}(): the {}'s word {!r} is wider than the {:.2f}in column even at the floor size "
                                 "{:.0f}pt — shorten it, or break it with a space".format(k.name, page, f, bad, w, sizes[f]))
    guard = 0
    while total() > h and guard < 200:
        guard += 1
        shrinkable = [f for f in order if sizes[f] > floors[f] + 0.05]
        if not shrinkable:
            break
        big = max(shrinkable, key=lambda f: sizes[f] / floors[f])
        sizes[big] = max(floors[big], sizes[big] * 0.94)
    if total() > h + 0.02:
        worst = max(items, key=lambda it: _field_height(k, it[0], it[1], floors[it[0]], w))
        raise VLTextOverflow("{}.{}(): all fields together need {:.2f}in at their floor sizes but the column is "
                             "{:.2f}in — shorten the copy; the longest is the {} ({:.2f}in at {:.0f}pt)".format(
                                 k.name, page, total(), h, worst[0],
                                 _field_height(k, worst[0], worst[1], floors[worst[0]], w), floors[worst[0]]))
    for f, t in items:
        if f not in _NO_WIDOW or f in phrased:            # the author's own breaks are kept as given
            continue
        sz, tries = sizes[f], 0
        while _widowed(k, f, t, sz, w) and sz * 0.95 >= floors[f] and tries < 10:
            sz, tries = sz * 0.95, tries + 1
        # clause breaks first: down to 0.7x (a display line still), or to what the widow fix shrinks to anyway
        fit = _phrase_lines(k, f, t, sizes[f], w, max(floors[f], min(0.7 * sizes[f], sz)))
        if fit is not None:
            sizes[f], phrased[f] = fit
            continue
        if not _widowed(k, f, t, sz, w):
            sizes[f] = sz
            continue
        wb = _balanced_width(k, f, t, sizes[f], w)
        if wb is not None:
            widths[f] = wb
    if total() > h + 0.02:                 # balancing never adds lines; this is a guard, not a path
        widths = {f: w for f in widths}
    t_all = total()
    cy = y if anchor == "top" else (y + h - t_all if anchor == "bottom" else y + (h - t_all) / 2.0)
    rects, plan = {}, []
    for f, t in items:
        sz = round(sizes[f], 1)
        fw = widths[f]
        fx = x + (w - fw) / 2.0 if align == "c" else x
        fh = fheight(f, t, sz, fw)
        rects[f] = (fx, cy, fw, fh)
        plan.append((f, t, sz, (fx, cy, fw, fh)))
        cy += fh + gaps[f]

    def draw():
        al = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER}[align]
        for f, t, sz, (fx, fy, fw, fh) in plan:
            _base, role, bold, ckey, italic, _floor = TYPE[k.name][f]
            if underlay and f in underlay:
                _dx = underlay[f]((fx, fy, fw, fh), t, sz) or 0.0
                fx, fw = fx + _dx, fw - max(0.0, _dx)          # the figure moves to the shape's centre
            color = (k.color("text_accents") if ckey == "accent" else k.color("mute") if ckey == "mute" else k.color("ink"))
            if f == "number" and _outlinable(k, t):
                import display_type as dt
                dt.outlined(slide, fx, fy, fw, fh, t, color=_hex(k.P["text_accents"][0]), face=k.face("numeral"))
                continue
            if f in phrased:
                dk.text(slide, fx, fy, fw, fh, [k.runs(l_, sz, color, bold, role, italic) for l_ in phrased[f]],
                        align=al, space_after=0)
                continue
            if f == "kicker" and k.name == "collage":
                hl = _hex(k.P["accents"][0])         # highlighter: the text reads on the HIGHLIGHT, not the ground
                ink = max((k.P["ink"], LANGS[k.name]["palette"]["ink"]), key=lambda c: _contrast(c, hl))
                rr = [dk.mark(x, hl) for x in k.runs(t, sz, dk.RGBColor.from_string(_hex(ink)), bold, role, italic)]
            else:
                rr = k.runs(t, sz, color, bold, role, italic)
            dk.text(slide, fx, fy, fw, fh, [rr], align=al)
    return rects, draw


def _data_hero(k, slide, page, col, items, lay, underlay, orient):
    """A data page with no picture: the figure IS the page. It was the language's stack at its usual size in a column
    80% wide — the figure, label and note filled its top-left quarter (the user, looking at the gallery, 2026-10-04).
    Now the figure is set as tall as the column allows (and never wider than about half of it); on a landscape canvas
    the label and note sit beside it, centred on it, so the page reads across; on a portrait one they stack below.
    Fitting is still _flow's: a long number, a long label or CJK text shrinks toward the floors, never past them."""
    x, y, w, h = col
    fields = dict(items)
    num = fields.get("number")
    if not num:
        return _flow(k, slide, page, col, items, anchor=lay["anchor"], align=lay["align"], underlay=underlay)
    bold, face = TYPE[k.name]["number"][2], k.face("numeral")
    s = min(*_canvas(k)) / 7.5
    rest = [it for it in items if it[0] != "number"]
    side = orient == "land" and bool(rest)
    tall = (0.80 if side else 0.55) * h * 72.0 / 1.2            # a line of the figure at ~1.2 em
    adv = dk._natural_width_in([(num, bool(bold))], tall, face)
    room = (0.50 if side else 0.86) * w
    if adv > room:
        tall *= room / adv
    start = {"number": tall, "label": TYPE[k.name]["label"][0] * s * (1.9 if side else 1.45),
             "note": TYPE[k.name]["note"][0] * s * (1.35 if side else 1.2)}
    if not side:
        return _flow(k, slide, page, col, items, anchor="middle", align=lay["align"], underlay=underlay, start=start)
    line_h = tall / 72.0 * 1.2
    nw = dk._natural_width_in([(num, bool(bold))], tall, face) + (0.5 * line_h if "circle" in lay["deco"] else 0.0) \
        + 0.15 * line_h
    gutter = max(0.35, 0.06 * w)
    # the figure + caption GROUP is centred on the page (it hugged the left edge with half the page empty): the
    # caption column is as wide as its longest line wants (capped by what is left), the group shifts by the slack
    cw_room = max(1.0, w - nw - gutter)
    want = max(dk._natural_width_in([(t, False)], start.get(f, 12), k.face("display" if f == "label" else "body"))
               for f, t in rest) + 0.1
    cw = min(cw_room, max(want, 0.35 * cw_room))
    x0 = x + max(0.0, (w - (nw + gutter + cw)) / 2.0)
    r1, d1 = _flow(k, slide, page, (x0, y, nw, h), [("number", num)], anchor="middle", align="l",
                   underlay=underlay, start=start)
    r2, d2 = _flow(k, slide, page, (x0 + nw + gutter, y, cw, h), rest, anchor="middle", align="l", start=start)

    def draw():
        d1()
        d2()
    return dict(r1, **r2), draw


def _frac(rect, W, H):
    x, y, w, h = rect
    return (x * W, y * H, w * W, h * H)


def _resolve(k, image):
    """(path, alt, slot_id) for an image argument: a P1 slot id, or a file path."""
    import image_series as ims
    if isinstance(image, str) and k.plan and image in {s_.get("id") for s_ in k.plan.get("slots", [])}:
        sl = ims.slot(k.plan, image)
        base = Path(k.image_dir) / "slide-{:02d}-{}.png".format(sl["slide"], sl["id"])
        path = base.with_name(base.stem + ".cut.png") if sl.get("cutout") else base
        if not path.exists():
            raise FileNotFoundError("{}: no image for slot {!r} at {}".format(k.name, image, path))
        return str(path), sl["alt"], sl["id"]
    p = Path(str(image))
    if not p.is_file():
        hint = ""
        if not p.suffix and "/" not in str(image) and "\\" not in str(image):
            if k.plan:                                   # a plan is passed: the id is not one of its slots
                hint = " — {!r} is not a slot of the image-series plan (its slots: {})".format(
                    str(image), ", ".join(str(s_.get("id")) for s_ in k.plan.get("slots", [])) or "none")
            else:
                hint = (" — if {!r} is an image-series slot id, pass plan= and image_dir= to visual_languages.use() "
                        "so it resolves to that slot's image".format(str(image)))
        raise FileNotFoundError("{}: no image at {}{}".format(k.name, p, hint))
    return str(p), p.stem.replace("-", " ").replace("_", " "), None


def _place_image(k, slide, image, rect, lay, page, keep_clear=None):
    """Place the page's image with the language's treatment. Returns the text column for 'bleed', else None."""
    import image_fx
    x, y, w, h = rect
    treat, frame = lay["treat"], lay["frame"]
    if lay["square"]:
        side = min(w, h)
        x, y, w, h = x + (w - side) / 2.0, y + (h - side) / 2.0, side, side
    if treat == "collage" or treat == "print":
        import collage as cl
        imgs = image if isinstance(image, (list, tuple)) else [image]
        items = []
        for im in imgs[:4] if treat == "collage" else imgs[:1]:
            path, alt, slot_id = _resolve(k, im)
            items.append({"slot": slot_id, "plan": k.plan, "image_dir": k.image_dir} if slot_id else {"path": path, "alt": alt})
        cl.collage(slide, (x, y, w, h), items, seed=len(slide.shapes) + 7, keep_clear=keep_clear, max_tilt=5.0)
        return None
    first = image[0] if isinstance(image, (list, tuple)) else image
    path, alt, slot_id = _resolve(k, first)
    if treat == "bleed":
        n0 = len(slide.shapes)
        bx, by, bw, bh, _ink = dk.photo_backdrop(slide, path, alt=alt, panel="quiet", fill=_hex(k.P["panel"]))
        if slot_id:
            for sh in list(slide.shapes)[n0:]:
                if sh.shape_type == 13:
                    dk._compose_tag(sh, gen=slot_id)
        return (bx, by, bw, bh)
    if treat == "feather":
        pic = dk.picture(slide, _feathered(path, _paper_tint(k)), x, y, w, h, fit="contain", alt=alt)
    elif slot_id and not frame_is_custom(frame):
        import image_series as ims
        pic = ims.slot_picture(slide, k.plan, slot_id, x, y, w, h, image_dir=k.image_dir)
        return None
    else:
        pic = dk.picture(slide, path, x, y, w, h, fit="cover", shape=None if frame == "rect" else frame, alt=alt)
    if slot_id:
        dk._compose_tag(pic, gen=slot_id)
    return None


def _paper_tint(k):
    """Per-channel factors that move the language's light paper to the ground this deck is on, or None on the
    light ground. A watercolour is transparent: painted on green paper, its cream paper IS green — without this
    every illustration sat as a pale patch on the meadow ground (looked at, 2026-10-04)."""
    if k.ground == "light":
        return None
    a, b = _rgb(LANGS[k.name]["palette"]["ground"]), _rgb(k.P["ground"])
    return tuple(round(b[i] / float(max(1, a[i])), 4) for i in range(3))


def _feathered(path, tint=None):
    """A feathered copy in a CACHE folder — never beside the caller's image (it once landed in the
    skill's own assets/). Keyed by the source's path, size, mtime and tint, so an edited source is redone.
    `tint` (per-channel factors, _paper_tint) multiplies the picture onto a non-light paper first."""
    import hashlib
    import tempfile
    import image_fx
    st = Path(path).stat()
    key = hashlib.sha1("{}|{}|{}|{}".format(Path(path).resolve(), st.st_size, st.st_mtime_ns, tint).encode()).hexdigest()[:16]
    d = Path(tempfile.gettempdir()) / "slide-maker-feather"
    d.mkdir(parents=True, exist_ok=True)
    out = d / "feather-{}.png".format(key)
    if not out.exists():
        src = str(path)
        if tint:
            from PIL import Image
            im = Image.open(path).convert("RGBA")
            r, g, b, a = im.split()
            r, g, b = (ch.point(lambda v, f=f: min(255, int(round(v * f)))) for ch, f in zip((r, g, b), tint))
            src = str(d / "tinted-{}.png".format(key))
            Image.merge("RGBA", (r, g, b, a)).save(src)
        image_fx.feather(src, out=str(out))
    return str(out)


def _readable_under(fill, ink, ground, floor=3.0):
    """`fill` blended toward `ground` until `ink` reads on it at `floor`:1 (large text) — a decorative disc under
    a figure must not drown it: soft dusk's light "1" sat on the pale sage disc at 1.87:1 (2026-10-04)."""
    f, g = _rgb(fill), _rgb(ground)
    for i in range(11):
        t = i / 10.0
        hx = "{:02X}{:02X}{:02X}".format(*(int(round(f[j] * (1 - t) + g[j] * t)) for j in range(3)))
        if _contrast(ink, hx) >= floor:
            return hx
    return _hex(ground)


def frame_is_custom(frame):
    """A frame the plan's own slot frame may not match (the page asks for it explicitly)."""
    return frame not in (None, "rect")


def _oval(slide, x, y, w, h, color, why, pill=False):
    from pptx.util import Inches
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if pill else MSO_SHAPE.OVAL
    sh = dk._flat(slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h)))
    if pill:
        sh.adjustments[0] = 0.5                          # fully round ends: a pill one line high
    sh.fill.solid()
    sh.fill.fore_color.rgb = dk.RGBColor.from_string(_hex(color))
    sh.line.fill.background()
    dk.decorative(sh, why)
    return sh


_CLEAR = 0.12         # inches between a card/note behind the text and a print beside it (lint SLIVER_GAP < 0.10)


def _card_geom(lay, col):
    """(x, y, w, h, rotation) of the card or note drawn behind a text column, or None. One definition for the
    drawing and for the room a picture beside it must leave (a print 0.05in from the note, 2026-10-03)."""
    x, y, w, h = col
    if "note" in lay["deco"]:
        return (x - 0.22, y - 0.20, w + 0.44, h + 0.40, -1.5)
    if "card" in lay["deco"]:
        return (x - 0.18, y - 0.16, w + 0.36, h + 0.32, 0.0)
    return None


def _keep_clear(lay, col):
    """What a picture beside the column must stay out of: the column, or the painted card around it plus _CLEAR."""
    g = _card_geom(lay, col) if col else None
    if g is None:
        return col
    import rotgeom
    pts = rotgeom.corners(*g)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) - _CLEAR, min(ys) - _CLEAR, max(xs) - min(xs) + 2 * _CLEAR, max(ys) - min(ys) + 2 * _CLEAR)


def _deco_before(k, slide, page, lay, img_rect, col, index):
    """Decoration that sits UNDER the content (painted first)."""
    p = k.P
    if "blob" in lay["deco"] and img_rect and col is None:
        x, y, w, h = img_rect
        _oval(slide, x - w * 0.10, y + h * 0.18, w * 0.62, w * 0.62, p["accents"][index % len(p["accents"])],
              "a soft colour blob behind the picture; carries no information")
    if "card" in lay["deco"] and col and img_rect is None:
        cx, cy, cw, ch, _rot = _card_geom(lay, col)
        dk.box(slide, cx, cy, cw, ch, fill=_hex(p["panel"]), round=True, r=0.28)
    if "note" in lay["deco"] and col and img_rect is None:
        x, y, w, h = col
        cx, cy, cw, ch, rot = _card_geom(lay, col)
        card = dk.box(slide, cx, cy, cw, ch, fill=_hex(p["panel"]))    # the ground's own paper (white on kraft)
        card.rotation = rot
        import ornaments
        dk.decorative(ornaments.tape(slide, x + w * 0.38, y - 0.36, w * 0.24, 0.30, "EDE3C8", rotation=2.0,
                                     seed=index, holds=card),
                      "washi tape holding the note card; ornament, nothing rides on seeing it")
    # "circle" is drawn by _flow under the number itself (an underlay), never across the column


def _deco_after(k, slide, page, lay, rects):
    """Decoration that sits over the page edge of the content (painted last)."""
    import ornaments
    p = k.P
    if "rule" in lay["deco"] and rects:
        first = min(rects.values(), key=lambda r: r[1])
        x, y, w, _h = first
        dk.box(slide, x, max(0.15, y - 0.16), min(w, 1.6), 0.025, fill=_hex(p["text_accents"][0]))
    if "scribble" in lay["deco"] and "title" in rects:
        x, y, w, h = rects["title"]
        ornaments.squiggle(slide, x, y + h - 0.02, min(w * 0.6, 3.2), 0.12, _hex(p["text_accents"][1 % len(p["text_accents"])]),
                           waves=5, line_w=2.5)


def _compose(k, slide, page, fields, image):
    W, H = _canvas(k)
    orient = "land" if W >= H * 1.2 else "port"
    lay = LAYOUTS[k.name][page][orient]
    if lay["treat"] == "feather" and image is not None and not isinstance(image, (list, tuple)) \
            and LAYOUTS[k.name][page].get(orient + "_tall"):
        try:                                       # a portrait picture takes the frame drawn for one
            from PIL import Image as _PI
            _iw, _ih = _PI.open(_resolve(k, image)[0]).size
            if _iw / float(_ih) < 0.85:
                lay = LAYOUTS[k.name][page][orient + "_tall"]
        except Exception:
            pass                                   # an unresolvable image is refused where it is placed, as before
    n0 = len(slide.shapes)
    index = len(k.prs.slides)
    items = [(f, str(fields[f]).strip()) for f in PAGE_FIELDS[page]
             if fields.get(f) is not None and str(fields[f]).strip()]       # whitespace is no text
    if not items and image is None:
        raise ValueError("{}.{}(): nothing to place — every field is empty and there is no image (a blank page "
                         "is never what was meant; pass the words)".format(k.name, page))
    if page == "quote" and fields.get("quote"):
        items = [("mark", "“")] + [it for it in items if it[0] != "mark"]
    if page == "image_text" and image is None:
        raise ValueError("{}.image_text(): image= is required — the page IS a picture beside its text (for text "
                         "alone use section() or quote())".format(k.name))
    if isinstance(image, (list, tuple)):          # never silently drop a picture the caller passed
        cap = 4 if lay["treat"] == "collage" else 1
        if not image:
            raise ValueError("{}.{}(): image= is an empty list — pass a path or slot id, or None".format(k.name, page))
        if len(image) > cap:
            raise ValueError("{}.{}(): {} images given but this page places {} — {}".format(
                k.name, page, len(image), cap, "a collage takes 1 to 4" if cap == 4 else
                "pass one image (only the collage cover and closing take a list)"))
    if image is not None and lay["image"]:
        img_rect = _frac(lay["image"], W, H)
        col = _frac(lay["col"], W, H) if lay["col"] else None        # None: a bleed image measures its panel
    else:
        img_rect, col = None, _frac(lay["col_noimg"], W, H)
    if img_rect is not None and lay["treat"] != "bleed":
        _deco_before(k, slide, page, lay, img_rect, None, index)          # blobs under the picture
    if img_rect is not None:
        panel = _place_image(k, slide, image, img_rect, lay, page, keep_clear=_keep_clear(lay, col))
        if panel is not None:
            col = panel
    underlay = {}
    if "circle" in lay["deco"]:
        acc = k.P["accents"]

        def _disc(r, t, sz, _c=_readable_under(acc[1 % len(acc)], k.P["ink"], k.P["ground"])):
            # The shape HOLDS the number, centred on it: it was one line-height across from the box's left edge, so a
            # "1" sat left of centre and the "2" of "02" stood outside it (the user, 2026-10-04). One figure: a
            # circle; wider: a pill of the same height (the flow's line does not change). Returns how far to move
            # the number's box so its measured ink sits at the shape's centre.
            x, y, w, h = r
            bold = TYPE[k.name]["number"][2]
            adv = dk._natural_width_in([(str(t), bool(bold))], sz, k.face("numeral"))
            # a circle while the figure's ink is narrow enough to sit well inside it (<= 0.62 of its height — any single
            # figure in any face: DejaVu's "1" is 0.56, Trebuchet's 0.45); wider, a pill with a quarter-height margin
            # each side. A width-only rule made DejaVu's "1" a near-circle pill on Linux CI (2026-10-04).
            sw = h if adv <= 0.62 * h else adv + 0.5 * h
            if lay["align"] == "c":
                sx, dx = x + (w - sw) / 2.0, 0.0
            else:
                sx = x - h * 0.10
                dx = (sx + sw / 2.0) - (x + dk.TEXT_INSET_LR / 2.0 + adv / 2.0)
            _oval(slide, sx, y, sw, h, _c, "a soft colour disc behind the figure; carries no information",
                  pill=sw > h + 1e-6)
            return dx
        underlay["number"] = _disc
    if page == "data" and img_rect is None and items:
        rects, draw = _data_hero(k, slide, page, col, items, lay, underlay, orient)
    else:
        rects, draw = _flow(k, slide, page, col, items, anchor=lay["anchor"], align=lay["align"],
                            underlay=underlay) if items else ({}, None)
    if rects:
        xs = [r[0] for r in rects.values()] + [r[0] + r[2] for r in rects.values()]
        ys = [r[1] for r in rects.values()] + [r[1] + r[3] for r in rects.values()]
        hug = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        if lay["align"] == "c" or "card" in lay["deco"] or "note" in lay["deco"]:
            hug = (col[0], hug[1], col[2], hug[3])                    # cards span the column, hug the text
        _deco_before(k, slide, page, lay, None, hug, index)           # cards and notes behind the text
    if draw:
        draw()
    _deco_after(k, slide, page, lay, rects)
    for sh in list(slide.shapes)[n0:]:
        dk._compose_tag(sh, vl=k.name)
    return {"rects": rects, "image": img_rect, "free": None}


def _page(page):
    def fn(self, slide, *, image=None, **fields):
        extras = {e for e in NATIVE_EXTRAS.get(self.name, ()) if page in EXTRA_PAGES.get(e, (page,))}
        bad = set(fields) - set(PAGE_FIELDS[page]) - ({"line"} if page == "closing" else set()) - extras
        if bad:
            raise TypeError("{}.{}(): unknown field(s) {} — this page takes {}{}".format(
                self.name, page, sorted(bad), list(PAGE_FIELDS[page]) + ["image"],
                " and {}".format(sorted(extras)) if extras else ""))
        if self.name in NATIVE:
            import vl_native
            out = vl_native.compose(self, slide, page, fields, image)
        elif page == "points":
            raise ValueError("{}.points(): the points page belongs to the native languages ({}) — on {} build the "
                             "list on an ordinary page: s = k.new_slide(); x, y, w, h = rs.ground(s, {!r}, "
                             "role='content', index=n); then rs.card / dk.text".format(
                                 self.name, ", ".join(NATIVE), self.name, self.name))
        else:
            out = _compose(self, slide, page, fields, image)
        # the page's title for screen readers: the kicker is set above it, or the title sits low, so neither lint
        # reading (a TITLE placeholder, or large text in the top 28%) found it — READING ORDER held the hand-off
        ttl = (" ".join(str(fields.get(f) or "") for f in ("number", "label")) if page == "data"
               else fields.get("quote") if page == "quote" else fields.get("title"))
        if ttl and str(ttl).strip():
            dk.a11y_title(slide, str(ttl), ea=self.ea_face("display", str(ttl)))   # the kit's own face for its script
        return out
    fn.__name__ = page
    fn.__doc__ = ("Compose a {} page: keyword fields {} plus image= (a P1 slot id, a file path, or None; the collage "
                  "cover/closing take a list of up to 4). Returns {{'rects': {{field: (x, y, w, h)}}, ...}}; refuses "
                  "with VLTextOverflow when even the floor sizes overflow, ValueError when there is nothing to place. "
                  "The native languages also take the words only you can give: seal= (ink), highlight= (poster), "
                  "icons= (cutpaper points), project= (drafting) — never invented, nothing drawn without them."
                  .format(page, PAGE_FIELDS[page]))
    import inspect as _insp                      # a real signature, so sigs.py prints the fields by name
    _P = _insp.Parameter
    fn.__signature__ = _insp.Signature(
        [_P("self", _P.POSITIONAL_OR_KEYWORD), _P("slide", _P.POSITIONAL_OR_KEYWORD)]
        + [_P(f, _P.KEYWORD_ONLY, default=None) for f in PAGE_FIELDS[page] if not (page == "quote" and f == "mark")]
        + [_P("image", _P.KEYWORD_ONLY, default=None)])
    return fn


for _pg in PAGE_FIELDS:
    setattr(Kit, _pg, _page(_pg))


# ════════════════════════════════════════════════════════════════════════════════════════════════
# Bundled samples — the direction preview shows these ("style sample — not your content").
# ════════════════════════════════════════════════════════════════════════════════════════════════
ASSETS = HERE.parent / "assets" / "vl"
SAMPLE_IMAGES = {
    "photo": ["photo/hall-repair.jpg", "photo/tools-tray.jpg", "photo/bench-toaster.jpg", "photo/jacket-mend.jpg",
              "photo/table-mended.jpg", "photo/kettle-cutout.png"],
    "watercolour": ["watercolour/rooftop-garden.jpg", "watercolour/garden-tools.jpg", "watercolour/balcony-watering.jpg",
                    "watercolour/harvest-basket.jpg", "watercolour/seedling-cutout.png"],
}
_SAMPLE_COPY = {
    "photo": dict(kicker="A neighbourhood repair café", title="Bring it broken. Take it home working.",
                  it_title="Everything you need is on the table",
                  body="Screwdrivers, a soldering iron, thread and a multimeter, shared on every bench.",
                  quote="The visitor holds the screwdriver; the volunteer only guides.", attr="How every repair begins",
                  num="1", label="evening a month", note="Short enough to fit around work."),
    "watercolour": dict(kicker="A small city garden", title="A balcony can grow a season of vegetables",
                        it_title="You need very few tools", body="A trowel, a watering can, twine and a few packets of seed.",
                        quote="Half an hour of watering a day is enough.", attr="A balcony gardener",
                        num="1", label="pot is enough to begin", note="A window sill will do."),
}

# the native languages need no pictures: their samples are words only (still a STYLE sample, not your content)
_SAMPLE_COPY_NATIVE = {
    "ink": [("cover", dict(kicker="茶事 · 卷一", title="一盏茶的时间", subtitle="慢下来，看见日常", seal="茶事")),
            ("points", dict(title="三道工序", items=[("洗盏", "器净，心先静"), ("候汤", "水沸，如蟹眼"), ("分茶", "浅斟，留七分")], seal="序")),
            ("quote", dict(quote="茶有两种姿态，浮与沉", attribution="茶室题记", seal="记")),
            ("data", dict(number="3", label="泡，滋味最浓", note="头泡醒茶，三泡正好", seal="茶"))],
    "poster": [("cover", dict(kicker="A manifesto for neighbourhood rooms", title="Make the room smaller.", highlight="room")),
               ("points", dict(title="Three moves.", items=["Share the tools", "Open the door", "Keep it local"])),
               ("quote", dict(quote="A room is a promise you can walk into.", attribution="From the manifesto")),
               ("data", dict(number="01", label="Room on every street.", note="Close enough to walk to, small enough to share."))],
    "cutpaper": [("cover", dict(kicker="A paper-cut science story", title="How seeds travel")),
                 ("points", dict(title="Three ways a seed gets around",
                                 items=[("Wind", "Wings and parachutes drift far."), ("Water", "Some seeds float to a new shore."),
                                        ("Animals", "Hooks hitch a ride on fur.")],
                                 icons=["lucide:wind", "lucide:droplets", "lucide:paw-print"])),
                 ("quote", dict(quote="Every forest began as one small seed.", attribution="A paper-cut science story")),
                 ("data", dict(number="1", label="seed is all a forest needs", note="Small beginnings, slow growth."))],
    "drafting": [("cover", dict(kicker="Schematic 01 · a modular reading room", title="A room built layer by layer.",
                                 subtitle="Floor, walls and roof drawn as one frame, each layer free to move.")),
                  ("points", dict(title="Three layers, one frame", items=[("Floor", "One continuous plate."),
                                                                         ("Walls", "Panels that slide on a track."),
                                                                         ("Roof", "A single span, no columns.")])),
                  ("quote", dict(quote="“Draw the quiet first, then the walls.”", attribution="Design principle")),
                  ("data", dict(number="3", label="layers, one structure.", note="Each layer can be built, moved and reused on its own."))],
}


def _sample_stem(name, ground):
    return name if ground == "light" else "{}-{}".format(name, ground)


def build_sample(name, out_dir, *, W=13.333, H=7.5, ground="light"):
    """A four-page sample deck of `name` on `ground` — cover, image_text, quote, data from the bundled images; the
    native languages: cover, points, quote, data in words alone."""
    if name in NATIVE:
        prs = dk.blank_deck(W, H)
        k = use(name, prs, ground=ground)
        for page, fields in _SAMPLE_COPY_NATIVE[name]:
            getattr(k, page)(k.new_slide(), **fields)
        out = Path(out_dir) / "sample-{}.pptx".format(_sample_stem(name, ground))
        out.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(out))
        return out
    kind = "watercolour" if name == "storybook" else "photo"
    imgs = [str(ASSETS / x) for x in SAMPLE_IMAGES[kind]]
    T = _SAMPLE_COPY[kind]
    prs = dk.blank_deck(W, H)
    k = use(name, prs, ground=ground)
    k.cover(k.new_slide(), kicker=T["kicker"], title=T["title"], image=imgs[:3] if name == "collage" else imgs[0])
    k.image_text(k.new_slide(), kicker=T["kicker"], title=T["it_title"], body=T["body"], image=imgs[1])
    k.quote(k.new_slide(), quote=T["quote"], attribution=T["attr"], image=imgs[2])
    k.data(k.new_slide(), number=T["num"], label=T["label"], note=T["note"], image=imgs[3])
    out = Path(out_dir) / "sample-{}.pptx".format(_sample_stem(name, ground))
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


def sample_fingerprint(pptx):
    """sha256 of a sample deck's slide XML — what its JPG was rendered from. tests/test_visual_languages.py rebuilds
    every sample and compares, so a preview that no longer matches the code fails instead of misleading a pick."""
    import hashlib
    import zipfile
    h = hashlib.sha256()
    with zipfile.ZipFile(str(pptx)) as z:
        for n in sorted(n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)):
            h.update(z.read(n))
    return h.hexdigest()


def sample_sheet(render_dir, out_jpg, *, width=1400):
    """A 2x2 contact of a rendered sample's four pages (slide01..04.png) as one JPEG."""
    from PIL import Image
    pngs = [Path(render_dir) / "slide{:02d}.png".format(i) for i in range(1, 5)]
    missing = [p.name for p in pngs if not p.exists()]
    if missing:
        raise FileNotFoundError("sample_sheet(): {} not rendered in {} — run render_deck.py first".format(missing, render_dir))
    ims = [Image.open(p).convert("RGB") for p in pngs]
    cw = (width - 30) // 2
    ch = int(cw * ims[0].size[1] / ims[0].size[0])
    sheet = Image.new("RGB", (width, ch * 2 + 30), (255, 255, 255))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((cw, ch)), (10 + (i % 2) * (cw + 10), 10 + (i // 2) * (ch + 10)))
    sheet.save(out_jpg, quality=78, optimize=True)
    # record which deck this sheet shows (sample-<stem>.pptx beside the render dir, as --sample lays them out)
    stem = Path(out_jpg).stem
    deck = Path(render_dir).parent / ("sample-" + stem + ".pptx")
    if deck.exists():
        import json
        man = Path(out_jpg).parent / "manifest.json"
        rec = json.loads(man.read_text(encoding="utf-8")) if man.exists() else {}
        rec[stem] = sample_fingerprint(deck)
        man.write_text(json.dumps(dict(sorted(rec.items())), indent=1) + "\n", encoding="utf-8")
    return out_jpg


_DISPLAY_NAMES = {"editorial": "Editorial magazine", "soft": "Soft organic", "collage": "Collage scrapbook",
                  "storybook": "Watercolour storybook"}
_RATIONALE = {"editorial": "photo-led and quiet: big bleed photographs, a serif display voice, pull quotes",
              "soft": "photo-led and warm: arch and blob frames, pastel ground, rounded cards",
              "collage": "photo-led and loud: tilted taped prints, heavy headlines, highlighter and squiggles",
              "storybook": "illustration-led: a watercolour series melting into paper, serif type"}
_DISPLAY_NAMES.update({"ink": "Ink wash", "poster": "Type poster", "cutpaper": "Cut paper", "drafting": "Drafting sheet"})
_RATIONALE.update({"ink": "drawn, no pictures: misty ink ridges, vertical CJK, a carved seal, an ensō around the figure",
                   "poster": "drawn, no pictures: the headline is the picture, one saturated field per page",
                   "cutpaper": "drawn, no pictures: a layered paper diorama with soft paper shadows",
                   "drafting": "drawn, no pictures: a drawing sheet with grid, title block, dimensions and leaders"})


def direction(name, *, fonts="both", ground="light", W=13.333, H=7.5):
    """A direction for the direction gate (archetypes_html / directions_diversity): this language's tokens
    plus its bundled style SAMPLE (a data URI the preview shows, labelled "style sample — not your
    content"). `vl` marks it STYLED for the diversity check — it never counts as the topic-invented
    bespoke direction the gate also requires. ground= as use(): "light", the contrast ground, or "auto" (the
    look history decides) — the preview then shows the ground the deck will be built on. W, H: the deck's canvas in
    inches, which "auto" reads as use() does (a printed board stays light)."""
    import base64
    if name not in LANGS:
        raise KeyError("visual_languages.direction(): unknown language {!r} — one of {}".format(name, sorted(LANGS)))
    if ground == "auto":
        ground, _why = _auto_ground(name, dk.blank_deck(W, H))
    if ground not in VARIANTS[name]:
        raise ValueError("visual_languages.direction(): ground must be 'auto' or one of {} for {}".format(
            sorted(VARIANTS[name]), name))
    L = LANGS[name]
    p = VARIANTS[name][ground]["palette"]
    f = dict(L["fonts"]["both"])
    if fonts == "mac":
        f.update(L["fonts"]["mac"])
    sample = ASSETS / "samples" / "{}.jpg".format(_sample_stem(name, ground))
    if not sample.exists():
        raise FileNotFoundError("visual_languages.direction(): no bundled sample at {} — rebuild it: python3 "
                                "scripts/visual_languages.py --sample <dir>".format(sample))
    return {"name": _DISPLAY_NAMES[name] + ("" if ground == "light" else " · " + VARIANTS[name][ground]["label"]),
            "vl": name, "vl_ground": ground, "rationale": _RATIONALE[name],
            "bg": "#" + _hex(p["ground"]), "ink": "#" + _hex(p["ink"]), "accent": "#" + _hex(p["text_accents"][0]),
            "accents": ["#" + _hex(a) for a in p["text_accents"]],
            "font_display": f["display"], "font_body": f["body"], "cover": L["cover"], "skeleton": L["skeleton"],
            "sample": "data:image/jpeg;base64," + base64.b64encode(sample.read_bytes()).decode("ascii")}

def _print_gates(name, deck, topic, fonts, ground="light"):
    """The record a deck in `name` needs, as runnable commands — including the palette hexes the register-pixels
    gate reads, which a docs-only run had to GUESS (and the guess was held: DECLARED HUES ABSENT, 2026-10-04)."""
    import shlex
    if name not in LANGS:
        print("visual_languages: no language {!r} — one of {}".format(name, sorted(LANGS)), file=sys.stderr)
        return 2
    if ground == "auto":
        # resolve on the BUILT deck's canvas, as use() did — a default 16:9 recorded the contrast ground for an A4
        # board that use() built light (final review 2026-10-04); no single deck to read means no guess
        decks = sorted(q for q in Path(str(deck)).glob("*.pptx") if not q.name.startswith("~$"))
        if len(decks) != 1:
            print("visual_languages: --ground auto reads the canvas of the built deck, and {} has {} .pptx — pass the "
                  "ground use() printed when it built the deck (one of: {})".format(
                      deck, len(decks), ", ".join(VARIANTS[name])), file=sys.stderr)
            return 2
        from pptx import Presentation as _P
        ground, why = _auto_ground(name, _P(str(decks[0])))
        print("# ground 'auto' → {} ({}): {}".format(ground, VARIANTS[name][ground]["label_zh"], why))
    if ground not in VARIANTS[name]:
        print("visual_languages: {} has no ground {!r} — one of {} (or auto)".format(name, ground, sorted(VARIANTS[name])),
              file=sys.stderr)
        return 2
    p = VARIANTS[name][ground]["palette"]
    pal = "ground #{} ink #{} accents {}".format(p["ground"], p["ink"], " ".join("#" + h for h in p["text_accents"]))
    pick = "bespoke {}".format(name) + (" for {}".format(topic) if topic else "")
    d = shlex.quote(str(Path(str(deck)).resolve()))
    # the script's ABSOLUTE path: the commands run as printed from any folder (`python3 scripts/deck_gates.py` ran only
    # from the skill folder; a docs-only agent working in its deck folder path-prefixed every one, 2026-10-04)
    dg = shlex.quote(str(HERE / "deck_gates.py"))
    print("# record the {} language (shared runtime: <deck>/.deck-gates.json)".format(name))
    if not (Path(str(deck)) / ".deck-gates.json").exists():        # `set` refuses a record that was never made
        print("python3 {} init {}".format(dg, d))
    for key, val in (("visual_language", name), ("vl_fonts", fonts), ("vl_ground", ground), ("style_pick", pick),
                     ("look_source", "bespoke"), ("palette", pal)):
        print("python3 {} set {} design_plan.{} {}".format(dg, d, key, shlex.quote(val)))
    print("# Codex runtime: the same six values in .codex-deck-evidence.json as design.visual_language, "
          "design.vl_fonts, design.vl_ground, design.style_pick, design.look_source and design.palette")
    return 0


def main(argv=None):
    import argparse
    import shlex
    ap = argparse.ArgumentParser(description="visual languages: build the bundled samples")
    ap.add_argument("--sample", metavar="OUT_DIR", help="build sample-<name>.pptx for every language")
    ap.add_argument("--sample-sheet", nargs=2, metavar=("RENDER_DIR", "OUT_JPG"),
                    help="contact a rendered sample's four pages into one JPEG")
    ap.add_argument("--list", action="store_true", help="list the languages")
    ap.add_argument("--gates", metavar="NAME", help="print the exact record commands for a deck in this language")
    ap.add_argument("--deck", metavar="DECK_DIR", help="with --gates (required): the deck folder")
    ap.add_argument("--for", dest="topic", metavar="TOPIC", default=None, help="with --gates: what the deck is for")
    ap.add_argument("--fonts", choices=("both", "mac"), default="both", help="with --gates: the fonts= you passed to use()")
    ap.add_argument("--ground", default="light", help="with --gates: the ground the deck was built on (light, the "
                    "language's contrast ground, or auto)")
    a = ap.parse_args(argv)
    if a.gates:
        if not a.deck:                    # a printed placeholder path runs nowhere — refuse instead
            print("visual_languages: --gates needs --deck <the deck folder>, so every printed command runs as "
                  "printed", file=sys.stderr)
            return 2
        return _print_gates(a.gates, a.deck, a.topic, a.fonts, a.ground)
    if a.list or not (a.sample or a.sample_sheet):
        for n, L in LANGS.items():
            print("{:10s} fonts both: {}  mac: {}  grounds: {}".format(n, L["fonts"]["both"], L["fonts"]["mac"], ", ".join(
                "{} ({})".format(g, V["label_zh"]) for g, V in VARIANTS[n].items())))
        return 0
    if a.sample_sheet:
        print(sample_sheet(*a.sample_sheet))
        return 0
    for n in LANGS:
        for g in VARIANTS[n]:
            out = build_sample(n, a.sample, ground=g)
            rd = Path(a.sample) / ("render-" + _sample_stem(n, g))
            print("built", out)
            print("NEXT: python3 scripts/render_deck.py {} {}".format(shlex.quote(str(out)), shlex.quote(str(rd))))
            print("then: python3 scripts/visual_languages.py --sample-sheet {} {}".format(
                shlex.quote(str(rd)), shlex.quote(str(ASSETS / "samples" / (_sample_stem(n, g) + ".jpg")))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
