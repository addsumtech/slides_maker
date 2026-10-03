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

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import deckkit as dk  # noqa: E402
import register_surface as rs  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402

EA_FACES = {
    "han": {"serif": {"mac": "Songti SC", "win": "SimSun"}, "sans": {"mac": "Hiragino Sans GB", "win": "Microsoft YaHei"}},
    "kana": {"serif": {"mac": "Hiragino Mincho ProN", "win": "Yu Mincho"}, "sans": {"mac": "Hiragino Sans", "win": "Yu Gothic"}},
    "hangul": {"serif": {"mac": "AppleMyungjo", "win": "Batang"}, "sans": {"mac": "Apple SD Gothic Neo", "win": "Malgun Gothic"}},
}   # the "win" faces: Microsoft's documented defaults — unverified here

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
        "ea": {"display": "sans", "body": "sans"}, "grain": 6, "frames": ["rect"],
        "forbids": (), "cover": "low-left", "skeleton": "band"},
    "storybook": {
        "palette": {"ground": "F6F1E3", "ink": "2F3A2A", "mute": "5E6352", "panel": "EFE7D2",
                    "accents": ["E2734B", "7FA35B", "F2C14E"], "text_accents": ["9A3F1E", "46612F", "7A5C0E"]},
        "fonts": {"both": {"display": "Georgia", "body": "Georgia", "numeral": "Times New Roman"},
                  "mac": {"display": "Baskerville", "body": "Georgia", "numeral": "Times New Roman"}},
        "ea": {"display": "serif", "body": "serif"}, "grain": 5, "frames": ["feather"],
        "forbids": ("confetti",), "cover": "centred", "skeleton": "statement"},
}


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


def script_of(text):
    t = text or ""
    if any("가" <= ch <= "힯" or "ᄀ" <= ch <= "ᇿ" for ch in t):
        return "hangul"
    if any("぀" <= ch <= "ヿ" for ch in t):
        return "kana"
    if any("一" <= ch <= "鿿" for ch in t):
        return "han"
    return None


def _platform(platform=None):
    return platform or ("mac" if sys.platform == "darwin" else "win")


class Kit:
    def __init__(self, name, prs, fonts, plan, image_dir, platform):
        self.name, self.prs, self.fonts, self.plan, self.image_dir = name, prs, fonts, plan, image_dir
        self.L, self.platform = LANGS[name], _platform(platform)
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
        p = self.L["palette"]
        v = p[key][i] if isinstance(p[key], list) else p[key]
        return dk.RGBColor.from_string(_hex(v))

    def run(self, text, size, color=None, bold=False, role="body", italic=False):
        return (text, size, color or self.color("ink"), bold, italic, self.face(role), self.ea_face(role, text))

    def new_slide(self):
        s = dk.add_slide(self.prs)
        if self.L["grain"]:
            import surfaces
            surfaces.grain_background(s, self.L["palette"]["ground"], strength=self.L["grain"])
        return s


def use(name, prs, *, fonts="both", plan=None, image_dir=None, platform=None):
    if name not in LANGS:
        raise KeyError("visual_languages.use(): unknown language {!r} — one of {}".format(name, sorted(LANGS)))
    if fonts not in ("both", "mac"):
        raise ValueError("visual_languages.use(): fonts must be 'both' (macOS + Windows faces) or 'mac', got {!r}".format(fonts))
    k = Kit(name, prs, fonts, plan, image_dir, platform)
    if fonts == "mac":
        missing = [f for f in set(k._fonts.values()) if dk._font_substituted(f)]
        if missing:
            raise ValueError("visual_languages.use(): fonts='mac' needs {} — not installed here; use fonts='both'".format(missing))
    p = k.L["palette"]
    ta = p["text_accents"]
    dk.set_palette(deep=_hex(p["ink"]), slate=_hex(p["mute"]), mute=_hex(p["mute"]), tint=_hex(p["panel"]),
                   magenta=_hex(ta[0]), blue=_hex(ta[1 % len(ta)]), teal=_hex(ta[2 % len(ta)]),
                   accents=[_hex(a) for a in ta],
                   font=k.face("body"), display=k.face("display"),
                   eafont=EA_FACES["han"][k.L["ea"]["body"]][k.platform],
                   eadisplay=EA_FACES["han"][k.L["ea"]["display"]][k.platform])
    dk.set_ground(_hex(p["ground"]))
    return k


def _ground_editorial(slide, role, index):
    W, H = rs._canvas(slide)
    rs._shape(slide, MSO_SHAPE.RECTANGLE, 0.5, H - 0.42, W - 1.0, 0.012, fill=dk.DEEP, texture=True)   # folio hairline
    return (0.5, 0.45, W - 1.0, H - 1.05)


def _soft_fill(index):
    """The soft language's blob colour for page `index` — its fill-only accents in turn (never text)."""
    acc = LANGS["soft"]["palette"]["accents"]
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


def _card_for(name):
    """The language's card: its panel colour; soft is rounded, the others square."""
    def card(slide, x, y, w, h, label=None):
        p = LANGS[name]["palette"]
        soft = name == "soft"
        body = dk.box(slide, x, y, w, h, fill=_hex(p["panel"]), line=None, round=soft, r=0.22 if soft else None)
        header = None
        if label:
            header = dk.text(slide, x + 0.16, y + 0.12, max(0.5, w - 0.32), 0.4,
                             [[(label, 12, dk.RGBColor.from_string(_hex(p["text_accents"][0])), True, False)]])
        return body, header
    card.__name__ = "_card_" + name
    return card


_card_editorial, _card_soft, _card_collage, _card_storybook = (_card_for(n) for n in ("editorial", "soft", "collage", "storybook"))


for _n in LANGS:
    rs.register(_n, ground=globals()["_ground_" + _n], card=globals()["_card_" + _n],
                forbids=LANGS[_n]["forbids"], source=__file__)
