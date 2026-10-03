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
        "ea": {"display": "sans", "body": "sans"}, "ea_heavy": True, "grain": 6, "frames": ["rect"],
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
        cjk = dk._has_cjk(text)
        if cjk and role in ("display", "numeral") and self.L.get("ea_heavy"):
            bold = True                      # Impact/Arial Black have no CJK: the EA face carries the weight
        return (text, size, color or self.color("ink"), bold, italic and not cjk,   # Chinese has no italics
                self.face(role), self.ea_face(role, text))

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
}

# page -> its fields in column order (the caller's keyword names)
PAGE_FIELDS = {"cover": ("kicker", "title", "subtitle"), "section": ("number", "kicker", "title"),
               "image_text": ("kicker", "title", "body", "caption"), "quote": ("mark", "quote", "attribution"),
               "data": ("number", "label", "note"), "closing": ("title", "line")}


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
                  "port": L_((.03, .03, .94, .52), "feather", (.08, .58, .84, .35), col_noimg=(.08, .24, .84, .52), anchor="top", align="c")},
        "section": {"land": L_((.54, .08, .42, .84), "feather", (.08, .18, .44, .64), col_noimg=(.12, .18, .76, .64), align="l"),
                    "port": L_((.06, .04, .88, .38), "feather", (.08, .46, .84, .46), col_noimg=(.08, .22, .84, .60), align="c")},
        "image_text": {"land": L_((.03, .08, .53, .84), "feather", (.60, .16, .34, .68)),
                       "port": L_((.04, .03, .92, .46), "feather", (.08, .52, .84, .42), anchor="top")},
        "quote": {"land": L_((.34, .02, .32, .34), "feather", (.14, .38, .72, .50), col_noimg=(.14, .18, .72, .66), align="c"),
                  "port": L_((.30, .03, .40, .20), "feather", (.08, .27, .84, .64), col_noimg=(.08, .18, .84, .70), align="c")},
        "data": {"land": L_((.58, .08, .38, .84), "feather", (.08, .14, .48, .72), col_noimg=(.12, .14, .76, .72)),
                 "port": L_((.06, .03, .88, .36), "feather", (.08, .42, .84, .50), col_noimg=(.08, .20, .84, .66))},
        "closing": {"land": L_((.15, .03, .70, .62), "feather", (.12, .68, .76, .25), col_noimg=(.12, .30, .76, .40), anchor="top", align="c"),
                    "port": L_((.04, .03, .92, .52), "feather", (.08, .58, .84, .34), col_noimg=(.08, .30, .84, .40), anchor="top", align="c")},
    },
}

GAP = 0.10            # inches between flowed fields at a 7.5in short side
_INSET = 0.056        # text() insets 0.028in a side
_FOOT = 0.55          # keep text out of the reserved footer band


def _canvas(k):
    return k.prs.slide_width / 914400.0, k.prs.slide_height / 914400.0


def _field_height(k, field, text, size, w):
    _sz, role, bold = size, TYPE[k.name][field][1], TYPE[k.name][field][2]
    if field == "number" and k.name == "collage" and len(text) <= 6:
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
    if dk._has_cjk(text):
        return True
    face = k.face(role)
    return all((dt._glyph_width(word, size, face, bold) or 0) <= (w - _INSET) for word in text.split())


def _break_lines(k, field, text, size, w):
    """Greedy line breaks with the real glyph widths of the face the run renders in (words for Latin,
    characters for CJK) — an approximation of the renderer, good enough to see a widow."""
    import display_type as dt
    role, bold, italic = TYPE[k.name][field][1], TYPE[k.name][field][2], TYPE[k.name][field][4]
    cjk = dk._has_cjk(text)
    face = k.ea_face(role, text) if cjk else k.face(role)
    italic = italic and not cjk
    units, joiner = (list(text), "") if cjk else (text.split(" "), " ")
    lines, cur = [], ""
    for u in units:
        nxt = (cur + joiner + u) if cur else u
        if cur and u in _HANG:
            cur = nxt                    # closing CJK punctuation hangs at the line end (kinsoku)
        elif cur and (dt._glyph_width(nxt, size, face, bold, italic) or 0) > w - _INSET:
            lines.append(cur)
            cur = u
        else:
            cur = nxt
    return lines + [cur]


_HANG = "，。、；：！？）」』》"


def _widowed(k, field, text, size, w):
    """True when the last line is a lone short word (Latin) or one or two characters (CJK)."""
    ls = _break_lines(k, field, text, size, w)
    if len(ls) < 2:
        return False
    last = ls[-1].strip()
    return len(last) <= 2 if dk._has_cjk(text) else len(last.split()) <= 1


_NO_WIDOW = ("title", "quote", "label", "line", "subtitle")


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


def _flow(k, slide, page, col, items, *, anchor, align, underlay=None):
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
        sizes[f], floors[f], widths[f] = base * s, max(9.0, floor * s), w
    gap = GAP * s
    order = [f for f, _ in items]

    def total():
        return sum(_field_height(k, f, t, sizes[f], widths[f]) for f, t in items) + gap * (len(items) - 1)
    for f, t in items:
        while sizes[f] > floors[f] and not _widest_word_fits(k, f, t, sizes[f], w):
            sizes[f] = max(floors[f], sizes[f] * 0.94)
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
        raise VLTextOverflow("{}.{}(): the {} needs {:.2f}in at the floor size {:.0f}pt but the column is {:.2f}in "
                             "(all fields together: {:.2f}in) — shorten it".format(
                                 k.name, page, worst[0], _field_height(k, worst[0], worst[1], floors[worst[0]], w),
                                 floors[worst[0]], h, total()))
    for f, t in items:
        if f not in _NO_WIDOW:
            continue
        sz, tries = sizes[f], 0
        while _widowed(k, f, t, sz, w) and sz * 0.95 >= floors[f] and tries < 10:
            sz, tries = sz * 0.95, tries + 1
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
        fh = _field_height(k, f, t, sz, fw)
        rects[f] = (fx, cy, fw, fh)
        plan.append((f, t, sz, (fx, cy, fw, fh)))
        cy += fh + gap

    def draw():
        al = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER}[align]
        for f, t, sz, (fx, fy, fw, fh) in plan:
            _base, role, bold, ckey, italic, _floor = TYPE[k.name][f]
            if underlay and f in underlay:
                underlay[f]((fx, fy, fw, fh))
            color = k.color("text_accents") if ckey == "accent" else k.color("ink")
            if f == "number" and k.name == "collage" and len(t) <= 6:
                import display_type as dt
                dt.outlined(slide, fx, fy, fw, fh, t, color=_hex(k.L["palette"]["text_accents"][0]), face=k.face("numeral"))
                continue
            run = k.run(t, sz, color, bold, role, italic)
            if f == "kicker" and k.name == "collage":
                run = dk.mark(run, _hex(k.L["palette"]["accents"][0]))
            dk.text(slide, fx, fy, fw, fh, [[run]], align=al)
    return rects, draw


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
        raise FileNotFoundError("{}: no image at {}".format(k.name, p))
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
        bx, by, bw, bh, _ink = dk.photo_backdrop(slide, path, alt=alt, panel="quiet", fill=_hex(k.L["palette"]["panel"]))
        if slot_id:
            for sh in list(slide.shapes)[n0:]:
                if sh.shape_type == 13:
                    dk._compose_tag(sh, gen=slot_id)
        return (bx, by, bw, bh)
    if treat == "feather":
        pic = dk.picture(slide, _feathered(path), x, y, w, h, fit="contain", alt=alt)
    elif slot_id and not frame_is_custom(frame):
        import image_series as ims
        pic = ims.slot_picture(slide, k.plan, slot_id, x, y, w, h, image_dir=k.image_dir)
        return None
    else:
        pic = dk.picture(slide, path, x, y, w, h, fit="cover", shape=None if frame == "rect" else frame, alt=alt)
    if slot_id:
        dk._compose_tag(pic, gen=slot_id)
    return None


def _feathered(path):
    """A feathered copy in a CACHE folder — never beside the caller's image (it once landed in the
    skill's own assets/). Keyed by the source's path, size and mtime, so an edited source is redone."""
    import hashlib
    import tempfile
    import image_fx
    st = Path(path).stat()
    key = hashlib.sha1("{}|{}|{}".format(Path(path).resolve(), st.st_size, st.st_mtime_ns).encode()).hexdigest()[:16]
    d = Path(tempfile.gettempdir()) / "slide-maker-feather"
    d.mkdir(parents=True, exist_ok=True)
    out = d / "feather-{}.png".format(key)
    if not out.exists():
        image_fx.feather(str(path), out=str(out))
    return str(out)


def frame_is_custom(frame):
    """A frame the plan's own slot frame may not match (the page asks for it explicitly)."""
    return frame not in (None, "rect")


def _oval(slide, x, y, w, h, color, why):
    from pptx.util import Inches
    sh = dk._flat(slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h)))
    sh.fill.solid()
    sh.fill.fore_color.rgb = dk.RGBColor.from_string(_hex(color))
    sh.line.fill.background()
    dk.decorative(sh, why)
    return sh


def _deco_before(k, slide, page, lay, img_rect, col, index):
    """Decoration that sits UNDER the content (painted first)."""
    p = k.L["palette"]
    if "blob" in lay["deco"] and img_rect and col is None:
        x, y, w, h = img_rect
        _oval(slide, x - w * 0.10, y + h * 0.18, w * 0.62, w * 0.62, p["accents"][index % len(p["accents"])],
              "a soft colour blob behind the picture; carries no information")
    if "card" in lay["deco"] and col and img_rect is None:
        x, y, w, h = col
        dk.box(slide, x - 0.18, y - 0.16, w + 0.36, h + 0.32, fill=_hex(p["panel"]), round=True, r=0.28)
    if "note" in lay["deco"] and col and img_rect is None:
        x, y, w, h = col
        card = dk.box(slide, x - 0.22, y - 0.20, w + 0.44, h + 0.40, fill="FFFFFF")
        card.rotation = -1.5
        import ornaments
        ornaments.tape(slide, x + w * 0.38, y - 0.36, w * 0.24, 0.30, "EDE3C8", rotation=2.0, seed=index, holds=card)
    # "circle" is drawn by _flow under the number itself (an underlay), never across the column


def _deco_after(k, slide, page, lay, rects):
    """Decoration that sits over the page edge of the content (painted last)."""
    import ornaments
    p = k.L["palette"]
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
    n0 = len(slide.shapes)
    index = len(k.prs.slides)
    items = [(f, str(fields[f])) for f in PAGE_FIELDS[page] if fields.get(f) not in (None, "")]
    if page == "quote" and fields.get("quote"):
        items = [("mark", "“")] + [it for it in items if it[0] != "mark"]
    if image is not None and lay["image"]:
        img_rect = _frac(lay["image"], W, H)
        col = _frac(lay["col"], W, H) if lay["col"] else None        # None: a bleed image measures its panel
    else:
        img_rect, col = None, _frac(lay["col_noimg"], W, H)
    if img_rect is not None and lay["treat"] != "bleed":
        _deco_before(k, slide, page, lay, img_rect, None, index)          # blobs under the picture
    if img_rect is not None:
        panel = _place_image(k, slide, image, img_rect, lay, page, keep_clear=col)
        if panel is not None:
            col = panel
    underlay = {}
    if "circle" in lay["deco"]:
        acc = k.L["palette"]["accents"]

        def _disc(r, _c=acc[1 % len(acc)]):
            x, y, w, h = r
            _oval(slide, x - h * 0.10, y, h, h, _c, "a soft colour disc behind the figure; carries no information")
        underlay["number"] = _disc
    rects, draw = _flow(k, slide, page, col, items, anchor=lay["anchor"], align=lay["align"], underlay=underlay) if items else ({}, None)
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
        bad = set(fields) - set(PAGE_FIELDS[page]) - ({"line"} if page == "closing" else set())
        if bad:
            raise TypeError("{}.{}(): unknown field(s) {} — this page takes {}".format(self.name, page, sorted(bad),
                                                                                    list(PAGE_FIELDS[page]) + ["image"]))
        return _compose(self, slide, page, fields, image)
    fn.__name__ = page
    fn.__doc__ = "Compose a {} page: fields {} plus image= (a slot id, a path, or None).".format(page, PAGE_FIELDS[page])
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


def build_sample(name, out_dir, *, W=13.333, H=7.5):
    """A four-page sample deck of `name` (cover, image_text, quote, data) from the bundled images."""
    kind = "watercolour" if name == "storybook" else "photo"
    imgs = [str(ASSETS / x) for x in SAMPLE_IMAGES[kind]]
    T = _SAMPLE_COPY[kind]
    prs = dk.blank_deck(W, H)
    k = use(name, prs)
    k.cover(k.new_slide(), kicker=T["kicker"], title=T["title"], image=imgs[:3] if name == "collage" else imgs[0])
    k.image_text(k.new_slide(), kicker=T["kicker"], title=T["it_title"], body=T["body"], image=imgs[1])
    k.quote(k.new_slide(), quote=T["quote"], attribution=T["attr"], image=imgs[2])
    k.data(k.new_slide(), number=T["num"], label=T["label"], note=T["note"], image=imgs[3])
    out = Path(out_dir) / "sample-{}.pptx".format(name)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


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
    return out_jpg


_DISPLAY_NAMES = {"editorial": "Editorial magazine", "soft": "Soft organic", "collage": "Collage scrapbook",
                  "storybook": "Watercolour storybook"}
_RATIONALE = {"editorial": "photo-led and quiet: big bleed photographs, a serif display voice, pull quotes",
              "soft": "photo-led and warm: arch and blob frames, pastel ground, rounded cards",
              "collage": "photo-led and loud: tilted taped prints, heavy headlines, highlighter and squiggles",
              "storybook": "illustration-led: a watercolour series melting into paper, serif type"}


def direction(name, *, fonts="both"):
    """A direction for the direction gate (archetypes_html / directions_diversity): this language's tokens
    plus its bundled style SAMPLE (a data URI the preview shows, labelled "style sample — not your
    content"). `vl` marks it STYLED for the diversity check — it never counts as the topic-invented
    bespoke direction the gate also requires."""
    import base64
    if name not in LANGS:
        raise KeyError("visual_languages.direction(): unknown language {!r} — one of {}".format(name, sorted(LANGS)))
    L = LANGS[name]
    p = L["palette"]
    f = dict(L["fonts"]["both"])
    if fonts == "mac":
        f.update(L["fonts"]["mac"])
    sample = ASSETS / "samples" / "{}.jpg".format(name)
    if not sample.exists():
        raise FileNotFoundError("visual_languages.direction(): no bundled sample at {} — rebuild it: python3 "
                                "scripts/visual_languages.py --sample <dir>".format(sample))
    return {"name": _DISPLAY_NAMES[name], "vl": name, "rationale": _RATIONALE[name],
            "bg": "#" + _hex(p["ground"]), "ink": "#" + _hex(p["ink"]), "accent": "#" + _hex(p["text_accents"][0]),
            "accents": ["#" + _hex(a) for a in p["text_accents"]],
            "font_display": f["display"], "font_body": f["body"], "cover": L["cover"], "skeleton": L["skeleton"],
            "sample": "data:image/jpeg;base64," + base64.b64encode(sample.read_bytes()).decode("ascii")}

def main(argv=None):
    import argparse
    import shlex
    ap = argparse.ArgumentParser(description="visual languages: build the bundled samples")
    ap.add_argument("--sample", metavar="OUT_DIR", help="build sample-<name>.pptx for every language")
    ap.add_argument("--sample-sheet", nargs=2, metavar=("RENDER_DIR", "OUT_JPG"),
                    help="contact a rendered sample's four pages into one JPEG")
    ap.add_argument("--list", action="store_true", help="list the languages")
    a = ap.parse_args(argv)
    if a.list or not (a.sample or a.sample_sheet):
        for n, L in LANGS.items():
            print("{:10s} fonts both: {}  mac: {}".format(n, L["fonts"]["both"], L["fonts"]["mac"]))
        return 0
    if a.sample_sheet:
        print(sample_sheet(*a.sample_sheet))
        return 0
    for n in LANGS:
        out = build_sample(n, a.sample)
        rd = Path(a.sample) / ("render-" + n)
        print("built", out)
        print("NEXT: python3 scripts/render_deck.py {} {}".format(shlex.quote(str(out)), shlex.quote(str(rd))))
        print("then: python3 scripts/visual_languages.py --sample-sheet {} {}".format(
            shlex.quote(str(rd)), shlex.quote(str(ASSETS / "samples" / (n + ".jpg")))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
