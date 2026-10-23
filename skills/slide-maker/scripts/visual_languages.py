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
from pptx.enum.text import MSO_ANCHOR  # noqa: E402

EA_FACES = dk.EA_FACES   # one table, in deckkit; the "win" faces: Microsoft's documented defaults — unverified here

import copy as _copy
import vl_specs as _vl_specs
# Every language is ONE manifest, scripts/vl_specs/<name>.py, checked by scripts/vl_contract.py; the tables below are
# built from them and keep their old names for every importer. Each language's GROUNDS: its own light paper, and ONE
# contrast ground (user's decision, 2026-10-04). All four light grounds are cream paper, and the register-pixels gate
# holds a deck whose ground repeats the last decks' — after a run of cream decks it held every language. Every text ink
# passes 4.5:1 on its ground AND panel (the contract checks it). The storybook contrast is a meadow-green PAPER, not a
# dark ground: its light watercolours would halo on dark.
REGISTRY = _vl_specs.load()
# the tables are COPIES (code that edits a table must not rewrite a manifest in memory), and a language's light palette
# is ONE object shared by LANGS and VARIANTS, as before the manifests (final review)
LANGS = {n: _copy.deepcopy(s["look"]) for n, s in REGISTRY.items()}
VARIANTS = {n: {g: {k: (LANGS[n]["palette"] if (k == "palette" and g == "light") else _copy.deepcopy(v))
                    for k, v in gd.items() if k not in ("dark", "roles")} for g, gd in s["grounds"].items()}
            for n, s in REGISTRY.items()}
NATIVE = tuple(n for n, s in REGISTRY.items() if s["kind"] == "drawn")          # drawn, no pictures needed (vl_native.py)
# the pages on which a drawn language draws the caller's picture; image= anywhere else is refused, naming these — it
# was dropped without a word, even a path to no file (robustness + docs audits, 2026-10-09)
NATIVE_IMAGE_PAGES = {n: REGISTRY[n]["image_pages"] for n in NATIVE}
IMAGE_LED = tuple(n for n, s in REGISTRY.items() if s["kind"] == "image-led")    # built around the caller's pictures
# words only the CALLER can give — never invented by the kit; absent means nothing is drawn
NATIVE_EXTRAS = {n: tuple(REGISTRY[n]["extras"]) for n in NATIVE if REGISTRY[n]["extras"]}
# the pages that DRAW each extra; on any other page it is refused, never silently dropped (non-Claude run, 2026-10-05)
EXTRA_PAGES = {x: d["pages"] for s in REGISTRY.values() for x, d in s["extras"].items() if d["pages"] != "any"}
_ACTIVE = {}    # language -> the ground key use() set; rs.ground()/rs.card() (no kit) follow it
_PAL_OVERRIDE = {}   # language -> the palette of the CURRENT page, for a language whose palette changes per page (poster)
_MEMO = {}   # language -> the last composed page's remembered extras, for ordinary pages (rs.ground has no kit)


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
        # the LIGHTEST ground, whichever key it has: poster's default is a saturated blue and its paper ground is light
        # (it was reported as having none, 2026-10-09)
        best = max(VARIANTS[name], key=lambda k_: _lum(VARIANTS[name][k_]["palette"]["ground"]))
        if _lum(VARIANTS[name][best]["palette"]["ground"]) < 0.2:      # dark on both: keep the designed default
            return "light", ("a printed board ({}) takes a light ground, and {} has none — both its grounds are dark "
                             "and print as a dark page; for print, pick a language with a light ground".format(fmt.label, name))
        return best, "a printed board ({}) takes {}'s lightest ground".format(fmt.label, name)
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
        self.memo = {}        # P4: the deck's remembered extras (masthead, edition, running) — REASSIGN, never mutate
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
        2026-10-04; lining figures always). Use it for any text that may contain digits. The cut is
        display_type.figure_runs, the one every measure of the flow uses (_drawn_width)."""
        import display_type as dt
        r = self.run(text, size, color, bold, role, italic)
        lat, figures = _run_faces(self.face(role), text)
        return [(part,) + r[1:5] + (face,) + r[6:] for part, face in dt.figure_runs(text, lat, figures)]

    def new_slide(self):
        """A slide in the language: paints the language's ground (its grain, where it has one) and names the
        slide `vl.<language>` (the OOXML slide name, nothing drawn) — so an ordinary page built on it (agenda,
        chart) counts as IN the language for the delivery gate, which a plain dk.add_slide page does not."""
        s = dk.add_slide(self.prs)
        s._element.cSld.set("name", "vl." + self.name)
        if self.grain:
            rs.grain_background(s, self.P["ground"], strength=self.grain)
        if self.name in NATIVE:                 # poster's colour field, drafting's drawing sheet
            import vl_native
            vl_native.paint_ground(self, s)
        return s


def use(name, prs, *, fonts="both", plan=None, image_dir=None, platform=None, ground="light"):
    """Start a deck in a curated VISUAL LANGUAGE — image-led "editorial", "soft", "collage", "storybook"; drawn (no
    pictures needed) "ink", "poster", "cutpaper", "drafting", "starlit", "broadsheet", "journal", "tally",
    "chalkboard": sets the palette, fonts and ground, and returns a Kit whose page functions — cover, section,
    image_text, points, quote, data and closing — lay out your own words and images in that
    language. fonts="both" uses only faces on
    macOS AND Windows; fonts="mac" unlocks Mac-only faces. plan/image_dir let image= take P1 series slot
    ids. ground="light" (default), the language's contrast ground (VARIANTS[name]), or "auto": the light ground
    unless your last decks already sit on it (the look history) — then the contrast one; printed boards stay
    light. Record design_plan.visual_language = name and vl_ground (references/visual-languages.md)."""
    if name in _vl_specs.DRAFTS:
        raise VLNotReady("visual_languages.use(): {} is a draft — decide every FILL: in scripts/vl_specs/{} "
                         "(python3 scripts/check_vl_contract.py {} names each one)".format(name, _vl_specs.DRAFTS[name], name))
    if name not in LANGS:
        raise KeyError("visual_languages.use(): unknown language {!r} — one of {}".format(name, sorted(LANGS)))
    if not ready(name):
        raise VLNotReady("visual_languages.use(): " + _UNREADY[name])
    if fonts not in ("both", "mac"):
        raise ValueError("visual_languages.use(): fonts must be 'both' (macOS + Windows faces) or 'mac', got {!r}".format(fonts))
    if ground == "auto":
        ground, why = _auto_ground(name, prs)
        import shlex as _shq
        # a TEMPLATE, not a command: `--deck DECK_DIR` ran verbatim and recorded into ./DECK_DIR (audit 2026-10-09);
        # an unquoted <…> cannot run as-is (the shell reads `<` as a redirect), so it must be filled in first
        print("[visual_languages] {}: ground {!r} ({}) — {}. Record it — replace both <…> first: python3 {} --gates "
              "{} --ground {} --deck <the deck folder> --for <what the deck is for, in quotes>".format(
                  name, ground, VARIANTS[name][ground]["label_zh"], why, _shq.quote(str(Path(__file__).resolve())),
                  name, ground))
    if ground not in VARIANTS[name]:
        raise ValueError("visual_languages.use(): ground must be 'auto' or one of {} for {}, got {!r}".format(
            sorted(VARIANTS[name]), name, ground))
    k = Kit(name, prs, fonts, plan, image_dir, platform, ground)
    _ACTIVE[name] = ground
    _PAL_OVERRIDE.clear()      # a new deck starts clean: no language keeps the last deck's per-page palette
    _MEMO.clear()              # ...nor the last deck's remembered masthead / running head
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
    r = REGISTRY[name]["grounds"][ground]["roles"]
    dk.set_theme({"ground": p["ground"], "ink": p["ink"], "mute": p["mute"], "card": r["card"], "card_ink": r["card_ink"],
                  "rule": r["rule"], "axis": p["mute"], "track": r["rule"], "on_accent": r["on_accent"],
                  "highlight": r["highlight"], "series": list(r["series"]),
                  "dark": REGISTRY[name]["grounds"][ground]["dark"],
                  "skin": dict(REGISTRY[name]["skin"]),
                  "floor": min(t[5] for t in REGISTRY[name]["type"].values() if isinstance(t, tuple))})
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


def _ground_starlit(slide, role, index):
    """An ordinary starlit page: the sky, kept clear of the content rect it returns (painted in REAL inches —
    register_surface scales the reference canvas by _K)."""
    import native_art as na
    W, H = rs._canvas(slide)
    K = rs._K[0]
    rect = (0.6, 0.55, W - 1.2, H - 1.1)
    p = _pal("starlit")
    na.starfield_png(slide, base=p["ground"], ink=p["ink"], glow=p["glow"], seed=int(index),
                     keep_clear=[tuple(v * K for v in rect)])
    return rect


def _ground_broadsheet(slide, role, index):
    """An ordinary broadsheet page: the masthead strip (the deck's remembered masthead and edition, this page's
    number), and the content rect under it — in REFERENCE inches."""
    import vl_native2 as v2
    K = rs._K[0]
    W, H = rs._canvas(slide)
    y = v2.bs_strip(v2.kit_for("broadsheet", slide), slide, {}) / K
    return (0.05 * W, y + 0.15, 0.90 * W, H - y - 0.75)


def _ground_journal(slide, role, index):
    """An ordinary journal page: the running head (the deck's remembered words, this page's number) and the
    content rect under it — in REFERENCE inches."""
    import vl_native2 as v2
    K = rs._K[0]
    W, H = rs._canvas(slide)
    y = v2.jn_running(v2.kit_for("journal", slide), slide, {}) / K
    return (0.07 * W, y + 0.1, 0.86 * W, H - y - 0.7)


def _ground_tally(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.55, 0.55, W - 1.1, H - 1.1)          # the grid is the page's background (new_slide paints it)


def _ground_chalkboard(slide, role, index):
    W, H = rs._canvas(slide)
    return (0.7, 0.6, W - 1.4, H - 1.3)             # inside the wooden frame new_slide drew


def _ground_interface(slide, role, index):
    """An ordinary page in the interface language is a window: the content rect is inside it, below its bar."""
    import vl_native3
    return _as_reference(vl_native3.ordinary_window(slide))


def _ground_wayfinding(slide, role, index):
    """An ordinary page carries the sign strip; the content rect starts below it."""
    import vl_native3
    return _as_reference(vl_native3.ordinary_sign(slide))


def _as_reference(rect):
    """vl_native3 lays an ordinary page out in REAL inches (its kit's ctx); rs.ground multiplies a painter's rect by
    the canvas scale (painters compose in reference inches), so a real-inch rect came back 1.33x on 16:9 — wider than
    the page (found by the 2026-10-15 placement matrix)."""
    k = rs._K[0]
    return tuple(v / k for v in rect)

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
_card_starlit = _card_for("starlit")
_card_broadsheet = _card_for("broadsheet")
_card_journal = _card_for("journal")
_card_tally = _card_for("tally")
_card_chalkboard = _card_for("chalkboard")
_card_interface = _card_for("interface")
_card_wayfinding = _card_for("wayfinding")


class VLNotReady(KeyError):
    """A language whose manifest is registered but whose code is not written yet (or does not import)."""


def _has_module(name):
    """Does scripts/vl_langs/<name>.py (or $VL_LANGS_DIR's) exist? Read without importing it."""
    import os
    return (Path(os.environ.get("VL_LANGS_DIR") or HERE / "vl_langs") / (name + ".py")).is_file()


def painter(name, role):
    """The language's `role` painter ("ground" or "card"), by the name in its manifest: from its own
    scripts/vl_langs/<name>.py when it has one (a language named "for" would otherwise get this module's _card_for),
    else a function of this module. None when neither defines it."""
    fn = REGISTRY[name]["painters"][role]
    if _has_module(name):
        import vl_langs
        mod = vl_langs.load().get(name)
        return getattr(mod, fn, None) if mod is not None else None
    return globals().get(fn)


_UNREADY = {}      # name -> why the language cannot be used yet (use() refuses it; check_vl_contract names it)
_PENDING = []      # languages whose painters live in scripts/vl_langs/: registered at this module's foot (below)


def _register(n):
    _g, _c = painter(n, "ground"), painter(n, "card")
    if _g is None or _c is None:
        import vl_langs as _vll
        if n in _vll.ERRORS:
            _UNREADY[n] = "{}: scripts/vl_langs/{}.py does not import — {}".format(n, n, _vll.ERRORS[n])
        else:
            _UNREADY[n] = ("{}: its code is not written yet — write {} and {} in scripts/vl_langs/{}.py "
                           "(references/visual-language-authoring.md; new_visual_language.py writes a first draft)"
                           .format(n, REGISTRY[n]["painters"]["ground"], REGISTRY[n]["painters"]["card"], n))
        return False
    _UNREADY.pop(n, None)
    rs.register(n, ground=_g, card=_c, forbids=LANGS[n]["forbids"], source=__file__)
    return True


_LAZY = set()      # languages with a scripts/vl_langs/ module not imported yet — it loads on first use (ready())


def _lazy_painter(n, role):
    """A stand-in for a module language's painter until its module is imported: registering the real one at import
    time loaded every module, and through them vl_native and native_art, into decks that use only an image-led
    language (spec §6 — measured when the first four module languages landed, 2026-10-22)."""
    def paint(*a, **kw):
        if not ready(n):
            raise VLNotReady(_UNREADY[n])
        return painter(n, role)(*a, **kw)
    paint.__name__ = REGISTRY[n]["painters"][role]
    return paint


def ready(name):
    """Is the language usable now? A module language is imported here, on first use. A language found unready while
    its module was half-imported (vl_native imported BEFORE this module: the module's own import of vl_native
    failed) is tried once more — by then it loads."""
    if name in _LAZY:
        _LAZY.discard(name)
        return _register(name)
    return name not in _UNREADY or _register(name)


for _n in LANGS:
    if not _has_module(_n) and all(REGISTRY[_n]["painters"][r] in globals() for r in ("ground", "card")):
        _register(_n)
    else:                  # its module imports vl_native, which reads this module's later names (HEADROOM, …):
        _PENDING.append(_n)    # loading it here, half-way down, failed as a circular import (2026-10-16)


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


class VLImageError(ValueError):
    """A picture the page was given cannot be used (unreadable, truncated, not an image); the page names itself."""


# field: (size_pt at a 7.5in short side, role, bold, colour key, italic, floor_pt)
TYPE = {n: _copy.deepcopy(s["type"]) for n, s in REGISTRY.items()}

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
        # *_wide / *_tall: the slot follows the picture's shape — a 16:9 watercolour in the 5.07x6.3in square-ish slot filled
        # 10.9% of the page, a portrait one 19.7% (the group-A verification, 2026-10-15); picked by _compose
        "data": {"land": L_((.58, .08, .38, .84), "feather", (.08, .14, .48, .72), col_noimg=(.12, .14, .76, .72)),
                 "port": L_((.06, .03, .88, .36), "feather", (.08, .42, .84, .50), col_noimg=(.08, .20, .84, .66)),
                 "land_wide": L_((.44, .10, .54, .80), "feather", (.06, .14, .34, .72), col_noimg=(.12, .14, .76, .72)),
                 "land_tall": L_((.54, .06, .42, .88), "feather", (.07, .14, .42, .72), col_noimg=(.12, .14, .76, .72)),
                 "port_wide": L_((.04, .03, .92, .41), "feather", (.08, .47, .84, .45), col_noimg=(.08, .20, .84, .66)),
                 "port_tall": L_((.14, .03, .72, .56), "feather", (.08, .62, .84, .32))},
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


HEADROOM = 0.97      # every language MEASURES its words in 97% of a column and draws the box at the full width: a line
# measured to fit exactly was set one line longer by LibreOffice — collage on 9:16 measured "fix what it already owns"
# at 4.894in in a 4.894in box and rendered "owns" on a fourth line, over the subtitle (audit sweep, 2026-10-09)
WORD_HEADROOM = 0.99  # a field that is ONE word, still too wide for HEADROOM at its floor, may take the whole column with
# this much of it to spare: one word has no line breaks to jitter, and LibreOffice keeps it whole once the box holds its
# advance width (+0.1% held, -0.1% broke it: 8 face/size pairs, 2026-10-22); Pillow's unkerned advances read wider
_LATIN_RUN = re.compile(r"[^\s]+")


_BREAKABLE = re.compile(r"[^\S\u00a0\u2007\u202f]+")   # whitespace a line may break at: NOT the no-break kinds


def _words(text):
    """The words a line may break between. str.split() also splits at a NO-BREAK SPACE (U+00A0, U+2007, U+202F), so a
    caller's "iPhone<NBSP>18" came back as two words and the widow balancer set "iPhone / 18, explained" — then joined
    the lines with an ordinary space, so the glue was gone too (iPhone 18 explainer, 2026-10-17)."""
    return [w_ for w_ in _BREAKABLE.split(text) if w_]


def _tokens(text):
    """(separator, unit) pairs a line may break between. A Latin word — letters, digits and their own punctuation, a
    run of non-CJK characters — is ONE unit, even inside Chinese ("…进展report v2" never breaks "re / port", the
    robustness audit 2026-10-09); a Chinese or Japanese character is one unit; a space is a separator. Korean breaks
    at spaces only, like Latin."""
    if any(dk._is_hangul(ord(c)) for c in text) or not dk._has_cjk(text):
        return [(" " if i_ else "", u) for i_, u in enumerate(text.split(" "))]
    out, cur, sep = [], "", ""
    for ch in text:
        if ch == " ":
            if cur:
                out.append((sep, cur)); cur = ""
            sep = " "
        elif dk._has_cjk(ch):
            if cur:
                out.append((sep, cur)); cur, sep = "", ""
            out.append((sep, ch)); sep = ""
        else:
            cur += ch
    if cur:
        out.append((sep, cur))
    return out


_RUN_FACES = {}


def _run_faces(face, text):
    """(latin, figures): the Latin face Kit.run sets a run of `text` in when its role's face is `face` — a run that is
    mostly figures in a lining face entirely (dk.numeral_run_face) — and the lining face Kit.runs cuts its figure
    sequences out into, when that face has old-style figures (None: they stay in `latin`). Memoised: the flow asks for
    the same lines again and again while it shrinks."""
    if not any(c.isdigit() for c in text):
        return face, None                                  # no figure: numeral_run_face keeps the face
    key = (face, text)
    got = _RUN_FACES.get(key)
    if got is None:
        lat = dk.numeral_run_face(text, face)
        got = (lat, dk.numeral_face(lat) if dk.has_oldstyle_figures(lat) else None)
        if len(_RUN_FACES) > 200000:
            _RUN_FACES.clear()
        _RUN_FACES[key] = got
    return got


def _decisions(face, text, whole):
    """The distinct (latin, figures) readings of `text` — on its own and as part of `whole` (see _drawn_width)."""
    own = _run_faces(face, text)
    if whole is None or whole == text:
        return (own,)
    other = _run_faces(face, whole)
    return (own,) if other == own else (own, other)


def _drawn_width(k, role, text, size, bold, italic=False, whole=None, floor=True):
    """The width (in) of Latin `text` as Kit.runs DRAWS it in `role` — each part in its own face, the figures of an
    old-style face in the lining face that sets them (display_type.figure_runs) — and never narrower than the run's own
    face reads it whole. Measured in the role's face only, Didot's "214" read 1.29in where Times New Roman drew 1.54in,
    in a 1.457in box: LibreOffice set "21 / 4" (stainedglass, 2026-10-22). The floor is what the lints read: each
    measures a paragraph in ONE face (deckkit its first run's, lint_deck the face of most of its characters), so a run
    split around its figures reads in its own face there — Georgia's figures, wider than they are drawn, keep their
    width; a run set in the lining face entirely ("3,400") reads in that face everywhere. `whole`: the field `text` is
    a line or word of — whether a run is set in the lining face entirely is decided on the run (mostly figures), and
    the field is drawn either whole or as its measured lines, so the wider of the two readings is taken. floor=False:
    the drawn width alone — where LibreOffice decides by what it draws (_break_lines: does the space overflow?)."""
    import display_type as dt
    best = 0.0
    for lat, figures in _decisions(k.face(role), text, whole):
        best = max(best, dt.figures_width(text, size, lat, bold, italic, figures))
        if figures and floor:
            best = max(best, dt.figures_width(text, size, lat, bold, italic))
    return best


def _drawn_advance(k, role, text, size, bold):
    """deckkit's advance width (dk._natural_width_in, what its lint reads) of `text` as Kit.runs draws it in `role`:
    each part in its own face, and never under the run's own face's reading (see _drawn_width)."""
    import display_type as dt
    lat, figures = _run_faces(k.face(role), text)
    drawn = sum(dk._natural_width_in([(p_, bool(bold))], size, f_) for p_, f_ in dt.figure_runs(text, lat, figures))
    return max(drawn, dk._natural_width_in([(text, bool(bold))], size, lat)) if figures else drawn


def _line_width(k, field, text, size, italic=None, whole=None):
    """The width (in) one line of `text` takes — the widest of three models, because a line has to fit them all: as it
    RENDERS (display_type.line_width: each script run in its own face, a space taking the script before it, and
    LibreOffice's autospace at every change between CJK and Latin — without it "用 GPT-5 做 3 件事" read 3.67in and
    rendered 4.04, its last character alone on a second line, calendar 2026-10-22); as the delivery lint reads it (one
    em per CJK character, the rest in the Latin face — on a machine without the East-Asian face its stand-in has no CJK
    glyphs and measured ~0.6em, the Linux font simulation 2026-10-09); and as deckkit's lint reads it (the whole run in
    the East-Asian face). A chalkboard title split by the render width alone was read by lint as one line more, under
    its own chalk underline (2026-10-09). `italic`: the style the run renders in, the field's own when None — a run
    that carries any CJK is set upright (Kit.run), so a caller measuring a Latin PART of one passes italic=False.
    Latin text and the Latin runs of a CJK line are measured in the faces Kit.runs DRAWS them in (figures of an
    old-style face in a lining one, _drawn_width); `whole`: the field `text` is a line of (see _drawn_width)."""
    import display_type as dt
    role, bold = TYPE[k.name][field][1], _weight(k, field, text)
    italic = TYPE[k.name][field][4] if italic is None else italic
    if not dk._has_cjk(text):
        return _drawn_width(k, role, text, size, bold, italic, whole)
    ea = k.ea_face(role, text) or k.face(role)
    lat = k.face(role)
    return max(_render_width(k, role, text, size, ea, bold, whole), dt.em_width(text, size, lat, bold),
               dk._natural_width_in([(text, bool(bold))], size, ea))


def _render_width(k, role, text, size, ea, bold, whole=None, floor=True):
    """display_type.line_width — one line as LibreOffice sets it, script by script — in the faces Kit.runs draws `text`
    in for `role` (see _drawn_width for `whole` and for the floor: the run's own face's reading), the East-Asian runs in
    `ea`."""
    import display_type as dt
    best = 0.0
    for lat, figures in _decisions(k.face(role), text, whole):
        best = max(best, dt.line_width(text, size, lat, ea, bold, figures=figures))
        if figures and floor:
            best = max(best, dt.line_width(text, size, lat, ea, bold))
    return best


def _unbreakable_overwide(k, field, text, size, w):
    """The first word the renderer cannot keep whole AND will not break sensibly: a Latin token (identifier,
    URL, compound) wider than the column. A Korean word that is too wide breaks between syllables and is
    measured that way; Chinese/Japanese break between characters. None when every such word fits."""
    role, bold = TYPE[k.name][field][1], _weight(k, field, text)
    italic = TYPE[k.name][field][4] and not dk._has_cjk(text)          # a run that carries CJK is set upright
    if dk._has_cjk(text) and not any(dk._is_hangul(ord(c)) for c in text):
        words = [u for _sep, u in _tokens(text) if not dk._has_cjk(u)]   # the Latin words inside Chinese/Japanese
    else:
        words = [w_ for w_ in _words(text) if not dk._has_cjk(w_)]
    for word in words:
        if _drawn_width(k, role, word, size, bold, italic, text) > w - _INSET:     # in the faces it is drawn in
            return word
    return None


def _outlinable(k, text):
    """A collage numeral is drawn as an outlined picture only when its face is installed here and draws every
    character; otherwise it is a text run (the EA face for CJK) — never tofu, never a refused page on a machine
    without Impact (Linux, 2026-10-04)."""
    import display_type as dt
    return k.name == "collage" and len(text) <= 6 and dt.covers(k.face("numeral"), text)


def _weight(k, field, text):
    """The weight a field's run RENDERS in, which every measure must use: Kit.run sets CJK display type bold where
    the Latin face has no CJK (ea_heavy: collage, poster, tally), and bold is wider — measured at the table's
    light weight, "用 GPT-5 做 3 件事" planned one line and the lint (and the render) set two (2026-10-09)."""
    role, bold = TYPE[k.name][field][1], TYPE[k.name][field][2]
    return bool(bold) or (dk._has_cjk(text) and role in ("display", "numeral") and bool(k.L.get("ea_heavy")))


def _field_height(k, field, text, size, w):
    _sz, role, bold = size, TYPE[k.name][field][1], _weight(k, field, text)
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
    """Every word of `text` fits the measure `w` — a Latin word (and a figure) measured in the faces and the style
    Kit.runs draws it in (_drawn_width; italic where the field is, upright inside CJK — Georgia Italic's "Everything"
    is 4% wider than its upright), a Korean word in its Korean face; Chinese and Japanese break between characters,
    so only the Latin words among them count."""
    import display_type as dt
    role, bold = TYPE[k.name][field][1], _weight(k, field, text)
    korean = any(dk._is_hangul(ord(c)) for c in text)
    if dk._has_cjk(text) and not korean:
        return all(_drawn_width(k, role, u, size, bold, whole=text) <= (w - _INSET)     # …but not inside a
                   for _sep, u in _tokens(text) if not dk._has_cjk(u))                  # Latin word among them
    if korean:
        face = k.ea_face(role, text)
        return all((dt._glyph_width(word, size, face, bold) or 0) <= (w - _INSET) for word in _words(text))
    italic = TYPE[k.name][field][4]
    return all(_drawn_width(k, role, word, size, bold, italic, text) <= (w - _INSET) for word in _words(text))


# CJK line ends as LibreOffice sets them (hangingPunct="1"). Measured on renders — 2,558 boxes for the delivery lint
# (lint_deck._HANG_MARKS, 2026-10-22; this model sets all 2,444 horizontal ones as rendered) and 2,256 more for this line
# model (2026-10-23: Songti SC, Hiragino Sans GB and Hiragino Sans with Arial, Times New Roman and Georgia, 20/36pt, each
# box as wide as puts one mark, or the space before it, at the line end; lines read back from the PDF):
#   * ONE of these marks hangs past a full line — the half-width ones too, after an ideograph ("螺丝刀握在,") — in every
#     measure down to one ideograph ("螺。"), but never after Latin text ("握在 / A。", "螺丝刀握 / GPT，在来访" — a space
#     after a word is Latin too), never a second one;
_HANG_MARKS = frozenset(dk._CJK_HANG + ",.;:!?")
#   * none of these starts a line — the break moves back to the last place it may fall, taking the WHOLE word or
#     character before it down ("螺丝刀握 / WikiGPT-5，在来访", "螺丝刀握 / 在”来访者"; the curly quotes too) …
_NO_LINE_START = _HANG_MARKS | frozenset(dk._CJK_CLOSE + "〗｝］”’～々)]}")
#   * … and none of these ends one: an opening quote or bracket goes down with what it opens, even with a space after it
#     ("螺丝刀握 / (在来访)", "螺丝刀握在来访 / “者手里”", "螺丝刀握 / （在来访者" from "握（ 在") — "(" as well as "（「";
_NO_LINE_END = frozenset(dk._CJK_OPEN + "〖｛［“‘([{")
#   * a SPACE: when the space itself is what overflows, the line breaks there, whatever follows ("螺丝刀握 / ，在来访",
#     "螺丝刀握在（ / 握在来"); when it fits, a mark after it hangs where it may ("螺丝刀握 ，"), a closing bracket after an
#     ideograph and a space starts the next line ("螺丝刀握 / 」在来访"), and after a Latin word and a space the word
#     goes down with the mark ("螺丝刀握 / GPT，在来访");
#   * with nowhere on the line to move the break back to, it falls at the measure ("螺丝刀握 / 「Claude / 」在来访").
# A Latin word inside CJK is one unit (_tokens) — LibreOffice also breaks one after "-" or "/" before a letter ("Wiki- /
# GPT，", "A/ / B，"), which this model does not: it moves the whole word down.


def _latin_end(line):
    """True when `line` does not end in East-Asian text — a Latin letter or digit, or anything else of the Latin script
    ("87%", "v2)"), a weak mark taking the script before it (display_type.script_runs): no mark hangs after it. Rendered:
    "握在 / A。", "来访 / 5。"; after an ideograph one hangs even when the line starts in Latin ("AB螺丝刀，")."""
    import display_type as dt
    runs = dt.script_runs(line)
    return not runs or runs[-1][1] != "a"


def _may_break(before, sep, unit):
    """True when LibreOffice may break between the text `before` and `unit` (with `sep`, "" or " ", between them) INSIDE
    a line — not where the space itself overflows (see _NO_LINE_END and the rules above it)."""
    if before[-1:] in _NO_LINE_END:
        return False
    return unit[0] not in _NO_LINE_START or (sep == " " and not _latin_end(before))


def _break_lines(k, field, text, size, w):
    """Greedy line breaks with the real glyph widths of the faces the run is DRAWN in (words for Latin, characters
    for CJK; the figures of an old-style face in their lining face, _drawn_width) — an approximation of the renderer,
    good enough to see a widow. Chinese and Japanese line ends follow LibreOffice (_HANG_MARKS, _NO_LINE_START,
    _NO_LINE_END, _may_break, measured on renders): one closing mark hangs past a full line, a mark that may not start
    a line takes the word or character before it down, an opening one never ends a line, a space that overflows is a
    break. Korean and Latin wrap at spaces."""
    import display_type as dt
    role, bold, italic = TYPE[k.name][field][1], _weight(k, field, text), TYPE[k.name][field][4]
    cjk = dk._has_cjk(text)
    face = k.ea_face(role, text) if cjk else k.face(role)
    italic = italic and not cjk
    korean = any(dk._is_hangul(ord(c)) for c in text)     # wraps at spaces, like Latin (LibreOffice probe)
    pairs = _tokens(text)                                  # CJK characters and whole Latin words (see _tokens)
    limit = w - _INSET
    may_hang = dk.HANG_PUNCT                               # in every measure, down to one ideograph ("螺。", rendered
    #                                                        12-48pt, lint_deck's probe 2026-10-22)
    cjk = cjk and not korean                               # below: per-character CJK rules only

    def width(s_):
        if korean:       # Hangul in its face, Latin words in theirs, the autospace between (display_type.line_width) —
            return max(_render_width(k, role, s_, size, face, bold, text),           # or, when wider, the whole
                       dt._glyph_width(s_, size, face, bold) or 0)                    # line in the Korean face
        # a part of a CJK run is measured upright, as the whole run renders: measured in the field's italic, the Latin
        # half of "v2 2026 道具" read 6% narrow in Didot Italic and was planned on one line (corpus diff, 2026-10-22)
        return (_line_width(k, field, s_, size, italic=False, whole=text) if cjk else
                _drawn_width(k, role, s_, size, bold, italic, text)) or 0

    def drawn(s_):       # the width LibreOffice itself sets — no lint's reading: it decides WHICH rule applies
        if dk._has_cjk(s_):
            return _render_width(k, role, s_, size, face, bold, text, floor=False)
        return _drawn_width(k, role, s_, size, bold, False, text, floor=False)
    # (separator, unit) pairs; a Korean word wider than the whole line goes in as syllables — the renderer
    # breaks it between them ("인공지능기반의 / 료영상재구성", final review 2026-10-04)
    toks = []
    for sep, u in pairs:
        if korean and len(u) > 1 and width(u) > limit:
            toks += [(sep if j_ == 0 else "", c_) for j_, c_ in enumerate(u)]
        else:
            toks.append((sep, u))
    if not cjk:
        lines, cur = [], ""
        for sep, u in toks:
            nxt = (cur + sep + u) if cur else u
            if not cur or width(nxt) <= limit:
                cur = nxt
            else:
                lines.append(cur)
                cur = u
        return lines + [cur]

    def joined(us):                                        # a line's units: its first one without the space before it
        return "".join((s_ if i_ else "") + u_ for i_, (s_, u_, _h) in enumerate(us))
    lines, cur = [], []                                    # cur: the line's [separator, unit, hung past the measure?]
    for i, (sep, u) in enumerate(toks):
        if not cur:
            cur = [[sep, u, False]]
            continue
        line = joined(cur)
        if width(line + sep + u) <= limit:
            cur.append([sep, u, False])
            continue
        if sep and drawn(line + sep) > limit:              # the space itself overflows: the line breaks there
            lines.append(line)
            cur = [[sep, u, False]]
            continue
        after = toks[i + 1] if i + 1 < len(toks) else None
        if (may_hang and u in _HANG_MARKS and not cur[-1][2] and not _latin_end(line)
                and not (after and after[0] == "" and after[1][0] in _NO_LINE_START)):
            cur.append([sep, u, True])                     # one mark hangs past a full line
            continue
        if not _may_break(line, sep, u):
            seq = cur + [[sep, u, False]]
            j = len(cur)                                   # the break goes before seq[j] — moved back past every unit
            while j > 0 and not _may_break(joined(seq[:j]), seq[j][0], seq[j][1]):
                j -= 1                                     # that may not start a line or follows one that may not end one
            if j == 0:                                     # nowhere on the line to move it: it breaks at the measure,
                j = len(cur)                               # taking down only what hangs past it
                while j > 1 and cur[j - 1][2]:
                    j -= 1
            lines.append(joined(cur[:j]))
            cur = [[s_, u_, False] for s_, u_, _h in seq[j:]]
            continue
        lines.append(line)
        cur = [[sep, u, False]]
    return lines + [joined(cur)]


def _set_lines(k, field, text, size, w):
    """The lines a wrapping DISPLAY field (title, subtitle, quote, label, line) is set in — its measured breaks at width
    `w` — or None: one line, a field that is not display type, or Chinese/Japanese/Korean whose East-Asian face is a
    stand-in here (a Linux box without SimSun: lines imposed from stand-in metrics read as overflow to the lint)."""
    if field not in _NO_WIDOW:
        return None
    if dk._has_cjk(text):
        role = TYPE[k.name][field][1]
        if dk._font_substituted(k.ea_face(role, text) or k.face(role)):
            return None
    ls = _break_lines(k, field, text, size, w)
    if len(ls) < 2 or "".join(ls).replace(" ", "") != text.replace(" ", ""):
        return None
    # every imposed line must sit on ONE line by the measure lint reads too — else the renderer wraps it again and
    # the field grows a line its box never had (a grown Korean quote at 42.7pt, Phase 3, 2026-10-15); the field then
    # wraps naturally, inside the height measured by the larger of the two models
    return ls if _lines_hold(k, field, text, ls, size, w) else None


def _lines_hold(k, field, text, ls, size, w):
    """True when every line in `ls` sits on ONE line by the measure lint reads too, at width `w` — the condition for
    imposing them as paragraphs (shared by _set_lines and vl_native2's stack: a Korean quote imposed there without it
    ran off the canvas, final review 2026-10-16)."""
    role = TYPE[k.name][field][1] if field in TYPE[k.name] else "body"
    bold = _weight(k, field, text) if field in TYPE[k.name] else False
    face = k.ea_face(role, text) if dk._has_cjk(text) else k.face(role)
    return not any(dk._measure_lines([(l_, bold)], size, max(0.2, w - _INSET), font=face) > 1 for l_ in ls)


def _widowed(k, field, text, size, w):
    """True when the last line is a lone short word (Latin) or one or two characters (CJK)."""
    ls = _break_lines(k, field, text, size, w)
    if len(ls) < 2:
        return False
    last = ls[-1].strip()
    korean = any(dk._is_hangul(ord(c)) for c in text)
    return len(last) <= 2 if dk._has_cjk(text) and not korean else len(_words(last)) <= 1


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
    role, bold = TYPE[k.name][f][1], _weight(k, f, seg)
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
    # a phrase per line is worth at most 15% of the size: past that the title WRAPS at full size instead (the comma
    # title "take it home working" shrank a 54pt cover to 37.8pt to keep its phrase whole — Phase 3, 2026-10-15)
    min_size = max(min_size, 0.85 * sz)
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
    role, bold = TYPE[k.name][f][1], _weight(k, f, t)
    face = k.ea_face(role, t) if dk._has_cjk(t) else k.face(role)
    full = (dt._glyph_width(t, sz, face, bold) or 0) if dk._has_cjk(t) else _drawn_width(k, role, t, sz, bold)
    wb = full / n + _INSET
    while wb < w:
        # the lint's line model must hold the same lines too: collage's 4.23in measure was four lines by the glyphs and
        # five by the measure lint reads, the height guard threw it away, and the widow came back (sheet review 2026-10-16)
        # …and it holds the widest word: a greedy break lets an over-wide word overflow its line, so the count still
        # matched while LibreOffice broke "Everythin / g" in a 3.12in measure (the herbarium review, 2026-10-22)
        if (len(_break_lines(k, f, t, sz, wb)) == n and not _widowed(k, f, t, sz, wb)
                and _widest_word_fits(k, f, t, sz, wb)
                and dk._measure_lines([(t, bold)], sz, max(0.2, wb - _INSET), font=face) <= n):
            return wb
        wb *= 1.04
    return None


def _even_lines(k, f, t, sz, w):
    """The same number of lines as the plain break, ending on two words or more, every line on one line by both
    models, the lines as even as they go — or None. A narrower measure cannot do this when the line that must take
    the lone word is already the widest ("a repair / night" in collage's narrow column, sheet review 2026-10-16), so
    the breaks are chosen, not wrapped, and set as explicit paragraphs. Space-separated words only (Latin, Korean);
    a Chinese or Japanese widow is balanced by the narrower measure."""
    import display_type as dt
    words = _words(t)
    korean = any(dk._is_hangul(ord(c)) for c in t)
    if (dk._has_cjk(t) and not korean) or len(words) < 3 or len(words) > 24:
        return None
    n = len(_break_lines(k, f, t, sz, w))
    if n < 2 or n > len(words) - 1:
        return None
    role, bold = TYPE[k.name][f][1], _weight(k, f, t)
    face = k.ea_face(role, t) if dk._has_cjk(t) else k.face(role)
    seg, fits = {}, {}

    def fit(i, j):
        if (i, j) not in fits:
            s = " ".join(words[i:j])
            fits[(i, j)] = _one_line(k, f, s, sz, w)
            seg[(i, j)] = (dt._glyph_width(s, sz, face, bold) or 0) if korean else _drawn_width(k, role, s, sz, bold, whole=t)
        return fits[(i, j)]
    best = {}                                          # (start, lines left) -> (cost, breaks)

    def solve(i, left):
        if (i, left) in best:
            return best[(i, left)]
        out = None
        if left == 1:
            if len(words) - i >= 2 and fit(i, len(words)):
                out = (0.0, [len(words)])
        else:
            for j in range(i + 1, len(words) - 1):    # leave the last line at least two words
                if not fit(i, j):
                    break
                rest = solve(j, left - 1)
                if rest is not None:
                    c = (w - seg[(i, j)]) ** 2 + rest[0]
                    if out is None or c < out[0]:
                        out = (c, [j] + rest[1])
        best[(i, left)] = out
        return out
    got = solve(0, n)
    if got is None:
        return None
    lines, start = [], 0
    for j in got[1]:
        lines.append(" ".join(words[start:j]))
        start = j
    return lines


# A quote STARTS this much larger than the language's quote size and shrinks to its column like every field: a
# three-word quote was set at the same 30pt as a paragraph, covering 0.3% of its page (Phase 3 verification, 2026-10-15).
QUOTE_GROW = 1.5


TUCK_MARK = ("soft",)     # the languages whose quote mark sits on a card (a void in it shows): it is tucked to the quote
MARK_PAD = 0.07           # in: between the tucked mark's ink and the line box of the quote under it
_MARK_INK = {}


def _mark_ink_bottom(k):
    """Where the opening quote mark's ink ends, in ems from the top of its box: the glyph drawn in the language's mark
    face (PIL) plus 0.10em for what a renderer adds above the glyph (its box inset and line leading — measured in
    LibreOffice: the soft mark's ink ended 0.60em down, PIL said 0.52em)."""
    face, bold = k.face(TYPE[k.name]["mark"][1]), bool(TYPE[k.name]["mark"][2])
    if (face, bold) not in _MARK_INK:
        try:
            from PIL import Image, ImageDraw
            f = dk._pil_font(face, 90, bold)
            px = 90 * dk._MEAS_PREC
            im = Image.new("L", (int(px * 2), int(px * 2)), 0)
            ImageDraw.Draw(im).text((int(px * 0.1), 0), "\u201c", font=f, fill=255)
            bb = im.getbbox()
            _MARK_INK[(face, bold)] = (bb[3] / float(px)) if bb else 0.52
        except Exception:
            _MARK_INK[(face, bold)] = 0.52
    return _MARK_INK[(face, bold)] + 0.10


def _mark_tuck(k, size, box_h):
    """The gap after a tucked mark: negative — the next field starts MARK_PAD under the mark's ink."""
    return min(0.0, _mark_ink_bottom(k) * size / 72.0 + MARK_PAD - box_h)


def _flow(k, slide, page, col, items, *, anchor, align, underlay=None, start=None):
    """PLAN the fields of one page in its column by measured height; returns (rects, draw).

    Sizes start at the language's sizes (scaled to the canvas), shrink toward each field's floor until
    the column holds them, and refuse (VLTextOverflow) when even the floors overflow. A word wider than
    the column shrinks that field; a title ending in a lone word / one or two CJK characters shrinks a
    little, or — when that cannot fix it — is set in a narrower, BALANCED measure ("not for / you",
    "工具其实很 / 少", "先种下第 / 一株", 2026-10-03). Nothing is drawn until draw() is called, so a
    card can be sized to the text it backs."""
    from pptx.enum.text import PP_ALIGN
    import math as _math
    x, y, w_col, h = col
    W, H = _canvas(k)
    h = min(h, H - _FOOT - y)
    s = min(W, H) / 7.5
    w = w_col * HEADROOM                   # MEASURED in HEADROOM of the column; every box is DRAWN dw wider (see HEADROOM)
    dw = w_col - w
    sizes, floors, widths = {}, {}, {}
    for f, _t in items:
        base, *_rest, floor = TYPE[k.name][f]
        grow = QUOTE_GROW if f == "quote" else 1.0
        sizes[f], floors[f], widths[f] = (start or {}).get(f, base * s * grow), max(9.0, floor * s), w
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

    tucks = k.name in TUCK_MARK and "mark" in order[:-1]

    def gap_of(f, size, box_h, tucked=False):
        # a quote mark on a card is TUCKED to the quote: the next field starts where the mark's ink ends, not under its
        # whole line box (0.8in of blank at 90pt); the mark's box then runs under the quote's first line. Only where the
        # block is PLACED: the sizes are decided on the untucked heights as before — a tucked page that kept more of the
        # quote's size set a long quote one size past what the lint's line model holds in its box
        return _mark_tuck(k, size, box_h) if tucked and tucks and f == "mark" else gaps[f]

    def total(tucked=False):
        return sum(fheight(f, t, sizes[f], widths[f]) + gap_of(f, sizes[f], fheight(f, t, sizes[f], widths[f]), tucked)
                   for f, t in items)
    whole = set()        # one-word fields held to the WHOLE column at their floor: measured and drawn at w_col
    for f, t in items:
        # ONE word is held to the same measure as every line — HEADROOM of the column, where _field_height counts its
        # lines. Held to the full column, "1,250" filled 3.75in of a 3.754in inner width and LibreOffice set "1,25 / 0"
        # (it keeps a word whole only once the box holds its whole advance width: -0.1% broke it, +0.1% did not,
        # measured 2026-10-22), and a word between the two widths was planned a line taller than it is drawn — the
        # figure sat at the top of a box twice its height (periodic, calendar).
        while sizes[f] > floors[f] and not _widest_word_fits(k, f, t, sizes[f], w):
            sizes[f] = max(floors[f], sizes[f] * 0.94)
        if f == "number" and _outlinable(k, t):
            continue                                     # drawn as a picture of its own size
        # …except a field that IS one word and still misses the measure at its floor ("1,250,000" at 56pt in herbarium's
        # 2.60in column): it is a single line with no line breaks to protect, so it takes the whole column, keeping
        # WORD_HEADROOM of it to spare, and is measured there too — one line, in a box exactly the column wide
        if (not _widest_word_fits(k, f, t, sizes[f], w) and len(_words(t)) == 1 and not dk._has_cjk(t)
                and _widest_word_fits(k, f, t, sizes[f], w_col * WORD_HEADROOM)):
            whole.add(f)
            widths[f] = w_col
            continue
        bad = _unbreakable_overwide(k, f, t, sizes[f], w)
        if bad:                           # it would break mid-word and run into the next field (final review)
            raise VLTextOverflow("{}.{}(): the {}'s word {!r} is wider than the {:.2f}in measure of the {:.2f}in column "
                                 "even at the floor size {:.0f}pt — shorten it, or break it with a space".format(
                                     k.name, page, f, bad, w, w_col, sizes[f]))
    # copy that cannot fit even at the floor sizes is refused at once, with the same numbers — the shrink loop below
    # measured an overlong title up to 200 times first (a refusal took ~20s a page, the audit's test, 2026-10-09)
    _start = dict(sizes)
    sizes.update({f_: min(sizes[f_], floors[f_]) for f_ in sizes})   # the smallest the loop can reach: a field that
    _at_floor = total()                                                # STARTS under its floor (cutpaper's disc
    sizes.update(_start)                                               # numbers) is never grown to it
    if _at_floor > h + 0.02:
        worst = max(items, key=lambda it: _field_height(k, it[0], it[1], floors[it[0]], w))
        raise VLTextOverflow("{}.{}(): all fields together need {:.2f}in at their floor sizes but the column is "
                             "{:.2f}in — shorten the copy; the longest is the {} ({:.2f}in at {:.0f}pt)".format(
                                 k.name, page, _at_floor, h, worst[0],
                                 _field_height(k, worst[0], worst[1], floors[worst[0]], w), floors[worst[0]]))
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
        # the SIZE is kept first (Phase 3, 2026-10-15: a widow fix that shrank before it balanced took covers 30% under
        # their size): clause breaks within 15% of the size, then a balanced (narrower) measure at full size, and only
        # then a smaller size — never below 85% of it; a lone last word at 85% is kept rather than a third smaller title
        fit = _phrase_lines(k, f, t, sizes[f], w, max(floors[f], 0.85 * sizes[f]))
        if fit is not None:
            sizes[f], phrased[f] = fit
            continue
        if not _widowed(k, f, t, sizes[f], w):
            continue
        wb = _balanced_width(k, f, t, sizes[f], w)
        if wb is not None:
            widths[f] = wb
            continue
        sz, tries, steps = sizes[f], 0, [sizes[f]]
        while _widowed(k, f, t, sz, w) and sz * 0.95 >= max(floors[f], 0.85 * sizes[f]) and tries < 10:
            sz, tries = sz * 0.95, tries + 1
            steps.append(sz)
        if _widowed(k, f, t, sz, w):
            # the last resort, largest size first: breaks CHOSEN at the same line count (collage's "a repair / night" —
            # the widest line had to take the word, and 15% smaller still left it alone; sheet review 2026-10-16). Not
            # before the shrink: editorial's 3 even lines at 90% read better than 4 ragged ones at full size
            for s_ in steps:
                ev = _even_lines(k, f, t, s_, w)
                if ev is not None:
                    sz, phrased[f] = s_, ev
                    break
        sizes[f] = sz
    if total() > h + 0.02:                 # balancing never adds lines; this is a guard, not a path
        widths = {f: (w_col if f in whole else w) for f in widths}
    t_all = total(True)
    cy = y if anchor == "top" else (y + h - t_all if anchor == "bottom" else y + (h - t_all) / 2.0)
    rects, plan = {}, []
    for f, t in items:
        sz = _math.floor(sizes[f] * 10 + 1e-9) / 10.0   # rounded DOWN: 32.58pt (one line) drawn at 32.6 set two lines
        fw = widths[f]                                   # the measure …
        fh = fheight(f, t, sz, fw)
        fw = fw + (0.0 if f in whole else dw)            # … and the box, drawn with the headroom (a whole-column word:
        #                                                  the column itself)
        fx = x + (w_col - fw) / 2.0 if align == "c" else (x + w_col - fw if align == "r" else x)
        rects[f] = (fx, cy, fw, fh)
        plan.append((f, t, sz, (fx, cy, fw, fh)))
        cy += fh + gap_of(f, sz, fh, True)

    def draw():
        al = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        for f, t, sz, (fx, fy, fw, fh) in plan:
            _base, role, bold, ckey, italic, _floor = TYPE[k.name][f]
            al_f = al
            if underlay and f in underlay:
                _dx = underlay[f]((fx, fy, fw, fh), t, sz) or 0.0
                _box = getattr(underlay[f], "box", None)
                if getattr(underlay[f], "ink", None) and _box:
                    # a figure in the ground's own ink sits ON the shape: its text box IS the shape, centred — the lint
                    # reads what is behind a text box by how much of the box a shape covers, and a box wider than the
                    # disc is read as sitting on the ground (dark ink on a dark ground: INVISIBLE TEXT)
                    fx, fw, al_f, fy = _box[0], _box[1], PP_ALIGN.CENTER, fy - _box[2]
                else:
                    fx, fw = fx + _dx, fw - max(0.0, _dx)      # the figure moves to the shape's centre
            color = (k.color("text_accents") if ckey == "accent" else k.color("mute") if ckey == "mute" else k.color("ink"))
            if f == "number" and getattr(underlay and underlay.get("number"), "ink", None):
                color = dk.RGBColor.from_string(_hex(underlay["number"].ink))     # the figure on its disc: the ink the disc asks for
            if f == "number" and _outlinable(k, t):
                import display_type as dt
                dt.outlined(slide, fx, fy, fw, fh, t, color=_hex(k.P["text_accents"][0]), face=k.face("numeral"))
                continue
            if f in phrased:
                dk.text(slide, fx, fy, fw, fh, [k.runs(l_, sz, color, bold, role, italic) for l_ in phrased[f]],
                        align=al, space_after=0)
                continue
            lines = _set_lines(k, f, t, sz, fw - (0.0 if f in whole else dw))
            if lines:                      # a wrapping display field is SET in its measured lines: drawn dw wider than it
                dk.text(slide, fx, fy, fw, fh, [k.runs(l_, sz, color, bold, role, italic) for l_ in lines],   # was measured,
                        align=al, space_after=0)    # the renderer re-wrapped "…more than ever / before" (final review)
                continue
            if f == "kicker" and k.name == "collage":
                hl = _hex(k.P["accents"][0])         # highlighter: the text reads on the HIGHLIGHT, not the ground
                ink = max((k.P["ink"], LANGS[k.name]["palette"]["ink"]), key=lambda c: _contrast(c, hl))
                rr = [dk.mark(x, hl) for x in k.runs(t, sz, dk.RGBColor.from_string(_hex(ink)), bold, role, italic)]
            else:
                rr = k.runs(t, sz, color, bold, role, italic)
            tb = dk.text(slide, fx, fy, fw, fh, [rr], align=al_f)
            if tucks and f == "mark":
                # the quote is TUCKED under the mark's box on purpose (its glyph's measured ink ends MARK_PAD above the
                # first line); lint reads the mark's whole line box as ink, and a long quote's smaller mark crossed its
                # 22% share (90 words, final review 2026-10-16) though the rendered glyphs never touch
                dk.overlap_intent(tb, "the quote mark is tucked over the quote's first line box; its glyph ink ends "
                                      "above the line (_mark_tuck)")
    draw.sizes = {f: sz for f, _t, sz, _r in plan}      # what each field was planned at (P4 sizes its art by it)
    draw.headroom = dw                                   # how much wider each box is drawn than its words were measured
    draw.exact = {f: sizes[f] for f, _t in items}       # …before the 0.1pt rounding: a size decided at 32.58pt (one
    # line) was drawn at 32.6 (two, "一盏茶的时 / 间"); vl_native2 draws at the exact size rounded DOWN
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
    bold = TYPE[k.name]["number"][2]
    s = min(*_canvas(k)) / 7.5
    rest = [it for it in items if it[0] != "number"]
    side = orient == "land" and bool(rest)
    tall = (0.80 if side else 0.55) * h * 72.0 / 1.2            # a line of the figure at ~1.2 em
    adv = _drawn_advance(k, "numeral", num, tall, bold)            # in the faces it is drawn in (lining figures)
    room = (0.50 if side else 0.86) * w
    if adv > room:
        tall *= room / adv
    start = {"number": tall, "label": TYPE[k.name]["label"][0] * s * (1.9 if side else 1.45),
             "note": TYPE[k.name]["note"][0] * s * (1.35 if side else 1.2)}
    if not side:
        return _flow(k, slide, page, col, items, anchor="middle", align=lay["align"], underlay=underlay, start=start)
    line_h = tall / 72.0 * 1.2
    nw = _drawn_advance(k, "numeral", num, tall, bold) + (0.5 * line_h if "circle" in lay["deco"] else 0.0) \
        + 0.15 * line_h
    gutter = max(0.35, 0.06 * w)
    # the figure + caption GROUP is centred on the page (it hugged the left edge with half the page empty): the
    # caption column is as wide as its longest line wants (capped by what is left), the group shifts by the slack
    cw_room = max(1.0, w - nw - gutter)
    want = max(_drawn_advance(k, "display" if f == "label" else "body", t, start.get(f, 12), False)
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
        return _usable(path), sl["alt"], sl["id"]
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
    return _usable(p), p.stem.replace("-", " ").replace("_", " "), None


_EMBEDS = ("JPEG", "PNG", "GIF", "BMP", "TIFF")     # what python-pptx embeds


def _usable(p):
    """The path of `p` as every language can place it — the caller's own file is never rewritten. A picture that only
    LOOKS right in a viewer is made right in a copy (robustness audit, 2026-10-09): a phone photo's EXIF orientation is
    baked into its pixels (pptx ignores the flag — the photo landed on its side in all 13 languages); a 16-bit PNG is
    scaled to 8 bits (the feather step clipped it to a white plate); WebP and other formats pptx cannot embed are
    re-saved as PNG. A file that cannot be decoded at all — truncated, or not an image — is refused by name."""
    import hashlib, tempfile
    from PIL import Image, ImageOps
    try:
        im = Image.open(p)
        im.load()
    except Exception as e:
        why = "it is cut short" if "truncated" in str(e).lower() else "it is not a picture this machine can read"
        raise VLImageError("the image {} cannot be used: {} ({}) — re-export it as a JPEG or PNG".format(
            Path(p).name, why, type(e).__name__))
    fmt = (im.format or "").upper()
    try:
        orient = int(im.getexif().get(274, 1) or 1)
    except Exception:
        orient = 1
    deep = im.mode in ("I;16", "I;16B", "I;16L", "I;16N", "I", "F")
    if fmt in _EMBEDS and orient in (0, 1) and not deep:
        return str(p)
    st = Path(p).stat()
    key = hashlib.sha1("{}|{}|{}".format(Path(p).resolve(), st.st_size, st.st_mtime_ns).encode()).hexdigest()[:20]
    # a photo stays a JPEG (a phone JPEG re-saved as PNG grew 1.2MB -> 7.5MB, final review 2026-10-09); PNG for alpha,
    # deep or palette pictures
    as_jpeg = fmt in ("JPEG", "MPO") and not deep and "A" not in im.mode
    out = Path(tempfile.gettempdir()) / "slide-maker-images" / (key + (".jpg" if as_jpeg else ".png"))
    if not _cached_ok(out):
        out.parent.mkdir(parents=True, exist_ok=True)
        if orient not in (0, 1):
            im = ImageOps.exif_transpose(im)
        if deep:
            import numpy as _np
            a = _np.asarray(im, dtype=_np.float64)
            top = 65535.0 if im.mode.startswith("I;16") or (im.mode == "I" and a.max() > 255) else (a.max() or 1.0)
            im = Image.fromarray(_np.clip(a / top * 255.0, 0, 255).astype(_np.uint8), "L")
        elif as_jpeg:
            im = im.convert("RGB")
        elif im.mode not in ("RGB", "RGBA", "L", "LA", "P"):
            im = im.convert("RGBA" if "A" in im.mode else "RGB")
        _atomic_save(im, out, **({"format": "JPEG", "quality": 92} if as_jpeg else {"format": "PNG"}))
    return str(out)


def _cached_ok(path):
    """A cache file that exists AND decodes: a build killed mid-write left a truncated copy under a stable key, and every
    later build embedded it as a black rectangle (final review, 2026-10-09)."""
    try:
        from PIL import Image
        if not Path(path).exists():
            return False
        with Image.open(path) as im:
            im.load()
        return True
    except Exception:
        return False


def _atomic_save(im, path, **kw):
    """Save a PIL image to `path` through a temporary name and an atomic rename, so a reader never sees half a file."""
    import os
    import tempfile
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=path.suffix)
    os.close(fd)
    try:
        im.save(tmp, **kw)
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _place_image(k, slide, image, rect, lay, page, keep_clear=None):
    """Place the page's image with the language's treatment. Returns the text column for 'bleed', else None."""
    import image_fx
    x, y, w, h = rect
    treat, frame = lay["treat"], lay["frame"]
    if lay["square"]:
        side = min(w, h)
        x, y, w, h = x + (w - side) / 2.0, y + (h - side) / 2.0, side, side
    if treat == "collage" or treat == "print":
        imgs = image if isinstance(image, (list, tuple)) else [image]
        items = []
        for im in imgs[:4] if treat == "collage" else imgs[:1]:
            path, alt, slot_id = _resolve(k, im)
            items.append({"slot": slot_id, "plan": k.plan, "image_dir": k.image_dir} if slot_id else {"path": path, "alt": alt})
        pp = _paper(k)
        collage(slide, (x, y, w, h), items, seed=len(slide.shapes) + 7, keep_clear=keep_clear, max_tilt=5.0,
                   **({"paper": pp[0], "tape_color": pp[1]} if pp else {}))
        return None
    first = image[0] if isinstance(image, (list, tuple)) else image
    path, alt, slot_id = _resolve(k, first)
    if treat == "bleed":
        n0 = len(slide.shapes)
        bx, by, bw, bh, _ink = dk.photo_backdrop(slide, path, alt=alt, panel="quiet", fill=_hex(k.P["panel"]))
        _crop_to_visible(slide, n0, path)
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


BLEED_FOCUS = (0.5, 0.10)    # which part of a picture the cover crop keeps: centred across, near the top down


def _crop_to_visible(slide, n0, path, focus=BLEED_FOCUS):
    """photo_backdrop() cover-fits its picture to the WHOLE page and then lays an opaque panel over one side of it, so
    the crop was made for a window the viewer never sees: a 853x1280 portrait kept 37% of its height in the 7.2in
    strip left of the panel, centred, and the heads sat on the top edge (the group-A verification, 2026-10-15). The
    picture is re-fitted, in place, to the part the panel leaves visible — cover-fitted to THAT rect, biased to the
    top — and meets the panel on its edge, to the EMU (a picture under the panel by any width is an OVERLAP finding;
    one apart by any is a sliver). Needs the panel to be the opaque box right after the picture; anything else leaves
    the page as photo_backdrop drew it."""
    shapes = list(slide.shapes)[n0:]
    pic = next((sh for sh in shapes if sh.shape_type == 13), None)
    panel = next((sh for sh in shapes[shapes.index(pic) + 1:] if sh.shape_type == 1), None) if pic is not None else None
    if pic is None or panel is None:
        return
    prs = slide.part.package.presentation_part.presentation
    W, H = prs.slide_width, prs.slide_height                       # EMU throughout
    pl, pt_, pw, ph = panel.left, panel.top, panel.width, panel.height
    if pw < 0.9 * W:                                               # a side band: the picture is the rest of the width
        vx, vy, vw, vh = (pl + pw, 0, W - (pl + pw), H) if pl < 9144 else (0, 0, pl, H)
    else:                                                          # a band across: the picture is the rest of the height
        vx, vy, vw, vh = (0, pt_ + ph, W, H - (pt_ + ph)) if pt_ < 9144 else (0, 0, W, pt_)
    if vw < 457200 or vh < 457200:                                 # under half an inch: not a picture area
        return
    from PIL import Image
    with Image.open(path) as im:
        iw, ih = im.size
    fx, fy = focus
    pic.left, pic.top, pic.width, pic.height = int(vx), int(vy), int(vw), int(vh)
    pic.crop_left = pic.crop_right = pic.crop_top = pic.crop_bottom = 0.0
    ar_i, ar_f = iw / float(ih), vw / float(vh)
    if ar_i > ar_f:
        c = 1.0 - ar_f / ar_i
        pic.crop_left, pic.crop_right = c * fx, c * (1.0 - fx)
    elif ar_i < ar_f:
        c = 1.0 - ar_i / ar_f
        pic.crop_top, pic.crop_bottom = c * fy, c * (1.0 - fy)


def _paper_tint(k):
    """Per-channel factors that move the language's light paper to the ground this deck is on, or None on the
    light ground. A watercolour is transparent: painted on green paper, its cream paper IS green — without this
    every illustration sat as a pale patch on the meadow ground (looked at, 2026-10-04)."""
    if k.ground == "light":
        return None
    if _lum(k.P["ground"]) < 0.2:          # a DARK ground: multiplying by dark/light (~0.13 on ink's night) all but
        return None                        # erased the picture (audits, 2026-10-09) — it is feathered onto the dark as is
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
    if not _cached_ok(out):
        import os
        src = str(path)
        if tint:
            from PIL import Image
            im = Image.open(path).convert("RGBA")
            r, g, b, a = im.split()
            r, g, b = (ch.point(lambda v, f=f: min(255, int(round(v * f)))) for ch, f in zip((r, g, b), tint))
            src = str(d / "tinted-{}.png".format(key))
            _atomic_save(Image.merge("RGBA", (r, g, b, a)), src, format="PNG")
        tmp = str(out) + ".{}.tmp.png".format(os.getpid())             # written whole, then renamed (see _cached_ok)
        image_fx.feather(src, out=tmp)
        os.replace(tmp, str(out))
    return str(out)


# A language's PAPER on a dark ground — the border of a print and the card of a note: (paper, the washi tape that holds it).
# Collage's white prints and its ground-coloured notes were the brightest and the darkest things on slate; both are cream
# paper with the LIGHT ground's inks on it. Kraft has no entry: its paper is its panel, white, as always.
PAPER_ON_DARK = {"collage": ("E8DFC9", "CDBE95")}


def _paper(k):
    """(paper, tape) for the paper things on this deck's ground, or None when they are the ground's panel and EDE3C8."""
    return PAPER_ON_DARK.get(k.name) if REGISTRY[k.name]["grounds"][k.ground]["dark"] else None


def _paper_kit(k):
    """The kit to set words ON this ground's paper: the language's light-ground inks when its paper is cream on a dark
    ground, else the kit itself."""
    if not _paper(k):
        return k
    import copy
    kk = copy.copy(k)
    light = LANGS[k.name]["palette"]
    kk.P = dict(k.P, ink=light["ink"], mute=light["mute"], text_accents=list(light["text_accents"]))
    return kk


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


def _disc_colors(P, fill):
    """(disc fill, the figure's ink or None for the language's own ink) for a figure on a decorative disc. The disc keeps
    its true colour when the ground's page ink or the ground itself reads on it at 4.5:1 — soft dusk's sage disc
    9DB8A0 takes the ground's dark 2E2940 (6.5:1). It was blended toward the ground until the OFF-WHITE ink reached 3:1
    (7C8D83, a muddy grey-green, the figure at 3.05:1), and that blend is now only the last resort."""
    best = max((P["ink"], P["ground"]), key=lambda c: _contrast(c, fill))
    if _contrast(best, fill) >= 4.5:
        return _hex(fill), (None if best == P["ink"] else _hex(best))
    return _readable_under(fill, P["ink"], P["ground"]), None


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
        blob = _oval(slide, x - w * 0.10, y + h * 0.18, w * 0.62, w * 0.62, p["accents"][index % len(p["accents"])],
                     "a soft colour blob behind the picture; carries no information")
        dk.overlap_intent(blob, "a soft colour blob tucked behind the picture's frame: the overlap is the composition")
    if "card" in lay["deco"] and col and img_rect is None:
        cx, cy, cw, ch, _rot = _card_geom(lay, col)
        dk.box(slide, cx, cy, cw, ch, fill=_hex(p["panel"]), round=True, r=0.28)
    if "note" in lay["deco"] and col and img_rect is None:
        x, y, w, h = col
        cx, cy, cw, ch, rot = _card_geom(lay, col)
        pp = _paper(k)
        card = dk.box(slide, cx, cy, cw, ch, fill=pp[0] if pp else _hex(p["panel"]))    # the ground's own paper (white on kraft)
        card.rotation = rot
        import ornaments
        dk.decorative(ornaments.tape(slide, x + w * 0.38, y - 0.36, w * 0.24, 0.30, pp[1] if pp else "EDE3C8", rotation=2.0,
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


def _yield_to_words(lay, f):
    """The layout with its picture shrunk to `f` of its size along the line it shares with the text column — the
    column takes the room — or None when the two are not side by side or stacked (a bleed, an overlap)."""
    I, C = lay.get("image"), lay.get("col")
    if not I or not C or lay["treat"] == "bleed":
        return None
    ix, iy, iw, ih = I
    cx, cy, cw, ch = C
    if cx + cw <= ix + 0.01:                       # words left of the picture
        I2, C2 = (ix + iw * (1 - f), iy, iw * f, ih), (cx, cy, cw + iw * (1 - f), ch)
    elif cx >= ix + iw - 0.01:                     # words right of it
        I2, C2 = (ix, iy, iw * f, ih), (cx - iw * (1 - f), cy, cw + iw * (1 - f), ch)
    elif cy >= iy + ih - 0.01:                     # words under it
        I2, C2 = (ix, iy, iw, ih * f), (cx, cy - ih * (1 - f), cw, ch + ih * (1 - f))
    elif cy + ch <= iy + 0.01:                     # words over it
        I2, C2 = (ix, iy + ih * (1 - f), iw, ih * f), (cx, cy, cw, ch + ih * (1 - f))
    else:
        return None
    return dict(lay, image=I2, col=C2)


def _compose(k, slide, page, fields, image):
    """Compose an image-led page; when its words do not fit beside the picture, the picture gives up room (80%, then
    65% of its size) before the page refuses — a storybook cover refused an ordinary 14-word title on the 10in 16:9,
    and every image-led cover a 30-character Chinese one on the square (the long-copy corpus, 2026-10-09)."""
    import vl_native
    W, H = _canvas(k)
    orient = "land" if W >= H * 1.2 else "port"
    lay = LAYOUTS[k.name][page][orient]
    if lay["treat"] == "feather" and image is not None and not isinstance(image, (list, tuple)) \
            and (LAYOUTS[k.name][page].get(orient + "_tall") or LAYOUTS[k.name][page].get(orient + "_wide")):
        try:                                       # a portrait picture takes the frame drawn for one, a 16:9 one its wide frame
            from PIL import Image as _PI
            _iw, _ih = _PI.open(_resolve(k, image)[0]).size
            _ar = _iw / float(_ih)
            _key = "_tall" if _ar < 0.85 else "_wide" if _ar > 1.4 else None
            if _key and LAYOUTS[k.name][page].get(orient + _key):
                lay = LAYOUTS[k.name][page][orient + _key]
        except Exception:
            pass                                   # an unresolvable image is refused where it is placed, as before
    variants = [lay] + ([v for v in (_yield_to_words(lay, 0.8), _yield_to_words(lay, 0.65)) if v]
                        if image is not None else [])
    n0, state, last = len(slide.shapes), dict(k.__dict__), None
    for v in variants:
        try:
            return _compose_one(k, slide, page, fields, image, v)
        except VLTextOverflow as e:
            last = e
            vl_native._unbuild(slide, n0)
            k.__dict__.clear(); k.__dict__.update(state)
    raise last


def _compose_one(k, slide, page, fields, image, lay):
    W, H = _canvas(k)
    orient = "land" if W >= H * 1.2 else "port"
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
        _fill, _ink = _disc_colors(k.P, acc[1 % len(acc)])

        def _disc(r, t, sz, _c=_fill):
            # The shape HOLDS the number, centred on it: it was one line-height across from the box's left edge, so a
            # "1" sat left of centre and the "2" of "02" stood outside it (the user, 2026-10-04). One figure: a
            # circle; wider: a pill of the same height (the flow's line does not change). Returns how far to move
            # the number's box so its measured ink sits at the shape's centre.
            x, y, w, h = r
            bold = TYPE[k.name]["number"][2]
            adv = _drawn_advance(k, "numeral", str(t), sz, bold)          # as drawn: lining figures (Kit.runs)
            # a circle while the figure's ink is narrow enough to sit well inside it (<= 0.62 of its height — any single
            # figure in any face: DejaVu's "1" is 0.56, Trebuchet's 0.45); wider, a pill with a quarter-height margin
            # each side. A width-only rule made DejaVu's "1" a near-circle pill on Linux CI (2026-10-04).
            sw = h if adv <= 0.62 * h else adv + 0.5 * h
            if lay["align"] == "c":
                sx, dx = x + (w - sw) / 2.0, 0.0
            else:
                sx = x - h * 0.10
                dx = (sx + sw / 2.0) - (x + dk.TEXT_INSET_LR / 2.0 + adv / 2.0)
            g = dy = 0.0
            if _ink:
                # a figure in the ground's own ink sits ON its disc, and the lint reads it against the disc only when
                # the disc HOLDS the text box with the padding it asks of a card (0.10in under the text's rendered
                # extent: its 0.04in top inset + one line at 1.25) — the disc grows to give it, never off the page, and
                # the text box rises by what the page's edge leaves short (a figure as wide as the page: ~1% of the disc)
                need = 0.04 + 1.25 * sz / 72.0 + 0.10
                cw_ = _canvas(k)[0]
                g = max(0.0, min(need - h, sx - 0.05, cw_ - 0.05 - (sx + sw)))
                dy = max(0.0, need - (h + g))
            _oval(slide, sx - g, y - g, sw + 2 * g, h + 2 * g, _c, "a soft colour disc behind the figure; carries no information",
                  pill=sw > h + 1e-6)
            _disc.box = (sx - g, sw + 2 * g, dy)
            return dx
        _disc.ink = _ink
        underlay["number"] = _disc
    if page == "data" and img_rect is None and items:
        rects, draw = _data_hero(k, slide, page, col, items, lay, underlay, orient)
    else:
        # the words of a note are set on its paper: on a dark ground that is cream, with the light ground's inks
        rects, draw = _flow(_paper_kit(k) if "note" in lay["deco"] else k, slide, page, col, items, anchor=lay["anchor"],
                            align=lay["align"], underlay=underlay) if items else ({}, None)
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


def _place_credit(k, slide, n0, credit):
    """The caller's picture credit, set ON the picture this page placed, in its bottom-right corner: a chip of the
    language's ground carrying the words in its ink, at the caption size and never under 12pt, kept clear of the
    footer band. Only image_text had a caption; a CC BY photo on any other page had no lawful place for its credit
    (iPhone 18 explainer, 2026-10-17). The words are measured by the model the lint reads — a Chinese credit in its
    East-Asian face, one em per character (a Latin-face measure gave its chip two thirds of its width) — and a credit
    that needs more than three lines, or a third of its picture's height, is refused: shorten it, never spread it over
    the page."""
    import display_type as dt
    pics = [sh for sh in list(slide.shapes)[n0:] if sh.shape_type == 13]
    if not pics:
        raise ValueError("{}: credit= credits the page's picture, and the page placed none".format(k.name))
    big = max(sh.width * sh.height for sh in pics)
    pic = [sh for sh in pics if sh.width * sh.height >= 0.5 * big][-1]     # the topmost of the large ones (collage)
    W, H = k.prs.slide_width / 914400.0, k.prs.slide_height / 914400.0
    left, top = max(0.0, pic.left / 914400.0), max(0.0, pic.top / 914400.0)
    right = min(W, (pic.left + pic.width) / 914400.0)
    bottom = min(H - 0.62 * H / 7.5, (pic.top + pic.height) / 914400.0)       # never into the footer band
    size = max(12.0, float(TYPE[k.name].get("caption", (12,))[0]) * min(W, H) / 7.5)
    cjk = dk._has_cjk(credit)
    face = k.face("body")
    mface = k.ea_face("body", credit) if cjk else face
    inset, pad = 0.12, 0.08

    def _w(t):
        # …and, when wider, as it is DRAWN: Kit.runs sets the figures of an old-style body face in a lining one
        if not cjk:
            return max(dt._glyph_width(t, size, face, False) or len(t) * size * 0.55 / 72.0,
                       _drawn_width(k, "body", t, size, False))
        # the lints' one em a CJK character, or — when wider — as LibreOffice sets it, with the autospace at every
        # change between Chinese and Latin ("摄影：张三，CC BY 4.0 授权" has four, an em between them)
        return max(dt.em_width(t, size, face, False), dt.line_width(t, size, face, mface, False),
                   _render_width(k, "body", t, size, mface, False))
    import lint_deck as _ld

    def _box_h(w_):
        # The box holds the lines by BOTH readings: as LibreOffice sets them (1.2 em a line x the paragraph's spacing —
        # a CJK paragraph 1.12, so 1.344 em; measured 2026-10-22, the same in every face tried) and as the delivery lint
        # reads them (its own line count, 1.4 em a CJK line, 1.25 a Latin one — lint_deck._txt_h, asked, not copied).
        # The chip measured 1.3 em a CJK line, under both: a two-line Chinese credit at 14pt was "cramped against the
        # card bottom" of its own chip (chalkboard, 10x7.5), and the text box was shorter than the lines it rendered.
        return max(dk.measure_text([(credit, False)], w_, size, font=mface, line_h_factor=dk._LINT_LINE_H),
                   _ld._txt_h({"paras": [[(credit, size)]], "w": w_, "font": face, "bold": False, "size": size,
                               "full": credit}))
    room = max(0.6, right - left - 2 * inset - 2 * pad)
    tb_w = min(room, _w(credit) * 1.10 + dk.TEXT_INSET_LR + 0.06)          # headroom: the lint's estimate must agree
    h_text = dk.measure_text([(credit, False)], tb_w, size, font=mface)
    one = dk.measure_text([("x", False)], 10.0, size, font=mface)
    if h_text > 3.05 * one or _box_h(tb_w) + 0.2 > 0.35 * (bottom - top):
        raise ValueError("{}: credit= {!r} needs more than three lines, or a third of its picture ({:.1f}in wide) — shorten it, "
                         "e.g. 'Photo: <name>, <licence>', and put the full source on a sources page"
                         .format(k.name, credit[:40] + ("…" if len(credit) > 40 else ""), right - left))
    if h_text > 1.5 * one:                               # wrapped: the narrowest box that keeps the line count
        lo_, hi_ = tb_w * 0.45, tb_w                      # balances the lines, so the last never holds one glyph
        for _ in range(14):
            mid = (lo_ + hi_) / 2
            if dk.measure_text([(credit, False)], mid, size, font=mface) <= h_text + 1e-6:
                hi_ = mid
            else:
                lo_ = mid
        tb_w = min(tb_w, hi_ * 1.03 + 0.02)
    # a chip that hugs the line it renders is a LABEL (0.04in above and below); one tall enough to read as a card (over
    # 0.35in, where the lint starts to ask a card's 0.09in padding) holds its words by both readings and is padded as
    # a card — a one-line 15.4pt Chinese credit on A4 was 0.37in tall with 0.04in under its words
    h_text = dk.measure_text([(credit, False)], tb_w, size, font=mface, line_h_factor=dk._LINT_LINE_H)
    vpad = 0.04
    if h_text + 2 * vpad > 0.35:
        h_text, vpad = _box_h(tb_w), 0.10
    cw, ch = tb_w + 2 * pad, h_text + 2 * vpad
    x, y = right - inset - cw, max(top + inset, bottom - inset - ch)
    chip = dk.box(slide, x, y, cw, ch, fill=k.P["ground"])
    dk.overlap_intent(chip, "the picture credit is set on the picture it credits")
    tb = dk.text(slide, x + pad, y + vpad, tb_w, h_text,
                 [k.runs(credit, size, dk.RGBColor.from_string(k.P["ink"]), False, role="body")],
                 anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    dk.overlap_intent(tb, "the picture credit is set on the picture it credits")
    return (x, y, cw, ch)


def _page(page):
    def fn(self, slide, *, image=None, credit=None, **fields):
        # words are words: a list was str()'d onto the slide as "['Bring it', 'broken']" and a float as
        # 0.30000000000000004 (robustness audit, 2026-10-09) — a whole number is shown as written, anything else refused
        fields = dict(fields)
        for f_, v in list(fields.items()):
            if f_ not in PAGE_FIELDS[page] or f_ == "items" or v is None or isinstance(v, str):
                continue
            if f_ == "number" and isinstance(v, int) and not isinstance(v, bool):
                fields[f_] = str(v)
                continue
            raise ValueError("{}.{}(): {}= takes text, got {} {!r} — pass the words exactly as they should read{}".format(
                self.name, page, f_, type(v).__name__, v,
                " (a number as written, e.g. '0.3' or '98.6%')" if isinstance(v, float) else ""))
        extras = {e for e in NATIVE_EXTRAS.get(self.name, ()) if page in EXTRA_PAGES.get(e, (page,))}
        bad = set(fields) - set(PAGE_FIELDS[page]) - ({"line"} if page == "closing" else set()) - extras
        if bad:
            elsewhere = ["{}= is drawn on {}".format(e, ", ".join(EXTRA_PAGES[e])) for e in sorted(bad)
                         if e in NATIVE_EXTRAS.get(self.name, ()) and e in EXTRA_PAGES]
            raise TypeError("{}.{}(): unknown field(s) {} — this page takes {}{}{}".format(
                self.name, page, sorted(bad), list(PAGE_FIELDS[page]) + ["image"],
                " and {}".format(sorted(extras)) if extras else "",
                " ({})".format("; ".join(elsewhere)) if elsewhere else ""))
        if credit is not None:
            if not isinstance(credit, str) or not credit.strip():
                raise ValueError("{}.{}(): credit= takes the credit line as text, e.g. 'Photo: A. Name, CC BY 4.0'"
                                 .format(self.name, page))
            if image is None:
                raise ValueError("{}.{}(): credit= credits the page's picture, and this page has none — pass image= "
                                 "too, or set the credit on the page that carries the picture".format(self.name, page))
        n0_credit = len(slide.shapes)
        if self.name in NATIVE:
            import vl_native
            if image is not None:
                pics = NATIVE_IMAGE_PAGES[self.name]
                if page not in pics:
                    raise ValueError("{}.{}(): this page draws no picture — {} draws the caller's picture on {}; pass "
                                     "image= there, or leave it out".format(self.name, page, self.name, " and ".join(pics)))
                if isinstance(image, (list, tuple)):
                    if len(image) != 1:
                        raise ValueError("{}.{}(): image= takes ONE picture (a file path or a slot id), got a list of "
                                         "{}".format(self.name, page, len(image)))
                    image = image[0]
            try:
                out = vl_native.compose(self, slide, page, fields, image)
            except VLImageError as e:
                raise VLImageError("{}.{}(): {}".format(self.name, page, e)) from None
        else:
            import vl_native
            n0, state = len(slide.shapes), dict(self.__dict__)
            try:
                out = (_points_led(self, slide, fields, image) if page == "points"
                       else _compose(self, slide, page, fields, image))
            except Exception as e:
                # a refused page leaves its slide as it found it: collage left its furniture and storybook its picture,
                # and a retry with shorter copy on the same slide drew them twice (audit sweep, 2026-10-09)
                vl_native._unbuild(slide, n0)
                self.__dict__.clear(); self.__dict__.update(state)
                if isinstance(e, VLImageError):
                    raise VLImageError("{}.{}(): {}".format(self.name, page, e)) from None
                raise
        if credit is not None:
            out.setdefault("rects", {})["credit"] = _place_credit(self, slide, n0_credit, credit.strip())
        # the page's title for screen readers: the kicker is set above it, or the title sits low, so neither lint
        # reading (a TITLE placeholder, or large text in the top 28%) found it — READING ORDER held the hand-off
        ttl = (" ".join(str(fields.get(f) or "") for f in ("number", "label")) if page == "data"
               else fields.get("quote") if page == "quote" else fields.get("title"))
        if ttl and str(ttl).strip():
            dk.a11y_title(slide, str(ttl), ea=self.ea_face("display", str(ttl)))   # the kit's own face for its script
        return out
    fn.__name__ = page
    fn.__doc__ = ("Compose a {} page: keyword fields {} plus image= (a P1 slot id, a file path, or None; the collage "
                  "cover/closing take a list of up to 4) and credit= (the picture's credit line, set on the picture "
                  "at the caption size). Returns {{'rects': {{field: (x, y, w, h)}}, ...}}; refuses "
                  "with VLTextOverflow when even the floor sizes overflow, ValueError when there is nothing to place. "
                  "The native languages also take the words only you can give: seal= (ink), highlight= (poster), "
                  "icons= (cutpaper points), project= (drafting); masthead=, edition=, inside= (cover), tags= (points) "
                  "(broadsheet); running=, authors= and abstract= (cover), margin= (points) (journal); tags= (points), "
                  "total= (data) (tally); doodle= (cover, closing), ordered= (points) (chalkboard) — never invented, "
                  "nothing drawn without them; on a page that does not draw one it is refused, naming the pages that do."
                  .format(page, PAGE_FIELDS[page]))
    import inspect as _insp                      # a real signature, so sigs.py prints the fields by name
    _P = _insp.Parameter
    fn.__signature__ = _insp.Signature(
        [_P("self", _P.POSITIONAL_OR_KEYWORD), _P("slide", _P.POSITIONAL_OR_KEYWORD)]
        + [_P(f, _P.KEYWORD_ONLY, default=None) for f in PAGE_FIELDS[page] if not (page == "quote" and f == "mark")]
        + [_P("image", _P.KEYWORD_ONLY, default=None), _P("credit", _P.KEYWORD_ONLY, default=None),
           _P("extras", _P.VAR_KEYWORD)])
    return fn


for _pg in PAGE_FIELDS:
    setattr(Kit, _pg, _page(_pg))

# the points page of the image-led languages (audit, 2026-10-09): a number, a head and a line per point, in each
# language's own voice — sizes scale with the canvas like every other field
for _n, (_no, _hd, _ln) in {
        "editorial": ((26, "numeral", True, "accent", False, 16), (22, "display", False, "ink", False, 13), (15, "body", False, "ink", False, 10)),
        "soft": ((24, "numeral", False, "accent", False, 15), (20, "display", False, "ink", False, 13), (15, "body", False, "ink", False, 10)),
        "collage": ((26, "numeral", True, "accent", False, 16), (22, "display", True, "ink", False, 13), (15, "body", False, "ink", False, 10)),
        "storybook": ((24, "numeral", False, "accent", False, 15), (21, "display", False, "ink", False, 13), (15, "body", False, "ink", False, 10)),
}.items():
    TYPE[_n].setdefault("item_no", _no)
    TYPE[_n].setdefault("item_head", _hd)
    TYPE[_n].setdefault("item_line", _ln)


NUMBER_SLACK = 1.10      # a point's number box holds its digits with at least this much to spare


def _number_gutter(k, labels, size, floor):
    """The width (in) of the gutter that holds a points page's item numbers: the widest of `labels` at `size` in the
    language's numeral face, by BOTH widths the kit uses (the glyph widths the flow measures, the font's advance the
    lint reads), plus NUMBER_SLACK and the text box's own insets — never under `floor`. A fixed 0.62in gutter held
    editorial's "01" (Arial Black 30.5pt, 0.5651in in LibreOffice) in an inner width of 0.5644in, and the renderer set
    "0" over "1" (the group-A verification, 2026-10-15). Measured in the faces Kit.runs draws them in: Didot's "01"
    is set in Times New Roman (lining figures)."""
    bold = bool(TYPE[k.name]["item_no"][2])
    need = max(max(_drawn_advance(k, "numeral", t, size, bold), _drawn_width(k, "numeral", t, size, bold))
               for t in labels)                                  # in the faces Kit.runs draws them in
    # + 2 EMU: a pptx stores whole EMU and python-pptx truncates, so a box sized to exactly 1.10x came back 1.0999x
    # wherever the slack term beats the floor (CI's Linux faces, GitHub run 38892848519)
    return max(floor, NUMBER_SLACK * need + dk.TEXT_INSET_LR + 2.0 / 914400)


def _points_led(k, slide, fields, image):
    """The points page of an image-led language: kicker and title, then 2-4 points — a number, a head and a line —
    in the language's own furniture (editorial: a hairline over each; soft: a rounded panel; collage: a taped note;
    storybook: a painted dot), with the caller's picture beside them (landscape) or above them (portrait) when given.
    Points sit in a row, else a 2x2 grid, else a stack — the first layout their words fit — at one size per field."""
    import vl_native as vn
    import vl_native2 as v2
    import ornaments
    W, H = _canvas(k)
    s = min(W, H) / 7.5
    land = W >= H * 1.05
    pts = vn.points_of(fields.get("items"))
    n = len(pts)
    P = k.P
    m = (0.07 if land else 0.08) * W
    top, bottom = 0.08 * H, H - max(0.55 * s, 0.07 * H)
    def attempt(frac, hfrac):
        img_rect = None
        if image is not None:
            lay = dict(LAYOUTS[k.name]["image_text"]["land" if land else "port"], deco=())
            if land:
                img_rect = (m, top, frac * W, bottom - top)
                x0, w0 = m + frac * W + 0.04 * W, W - (m + (frac + 0.04) * W) - m
            else:
                img_rect = (m, top, W - 2 * m, frac * H)
                x0, w0 = m, W - 2 * m
            head_top = top if land else top + frac * H + 0.3 * s
        else:
            x0, w0, head_top = m, W - 2 * m, top
        head = v2.fields(fields, ("kicker", "title"), ())
        hh = hfrac * H
        hr, hd = v2.flow(k, slide, "points", (x0, head_top, w0, hh), head, anchor="top") if head else ({}, (lambda: None))
        y0 = (max(v[1] + v[3] for v in hr.values()) if hr else head_top) + 0.35 * s
        area = (x0, y0, w0, bottom - y0)
        pad = 0.0 if k.name in ("editorial", "storybook") else 0.20 * s
        gap = 0.28 * s

        lift = 0.16 * s if k.name == "editorial" else 0.0            # editorial's hairline sits above the number
        big = {f_: TYPE[k.name][f_][0] * s * 1.25 for f_ in ("item_no", "item_head", "item_line")}   # room to read from the back

        def cells(cols, y, ch):
            rows = -(-n // cols)
            cw = (area[2] - gap * (cols - 1)) / cols
            return [(area[0] + (i % cols) * (cw + gap), y + (i // cols) * (ch + gap), cw, ch) for i in range(n)]

        def plan_at(grid, inline=False, tight=False):
            """[(rects, draw)] per point. inline: the number in a gutter beside the head instead of a line above it — one
            line less per point, which four two-line points on a square page needed (the long-copy corpus)."""
            specs, nums = [], []
            pd = pad * (0.6 if tight else 1.0)           # last resort: a narrower margin inside each note or panel
            for i, ((hd_, ln_), c) in enumerate(zip(pts, grid)):
                inner = (c[0] + pd, c[1] + pd + lift, c[2] - 2 * pd, c[3] - 2 * pd - lift)
                no = [] if k.name == "storybook" else [("item_no", "{:02d}".format(i + 1))]
                if inline and no:
                    gw = _number_gutter(k, ["{:02d}".format(j + 1) for j in range(n)], big["item_no"], 0.62 * s)
                    nums.append(((inner[0], inner[1], gw, inner[3]), no, dict(anchor="top", start=dict(big))))
                    inner, no = (inner[0] + gw, inner[1], inner[2] - gw, inner[3]), []
                its = no + [("item_head", hd_)] + ([("item_line", ln_)] if ln_ else [])
                if k.name == "storybook":
                    inner = (inner[0] + 0.42 * s, inner[1], inner[2] - 0.42 * s, inner[3])
                specs.append((inner, its, dict(anchor="top", start=dict(big))))
            words = v2.plan_together(_paper_kit(k), slide, "points", specs)         # the words sit on the notes' paper
            if not nums:
                return words
            out = []
            for (nr, nd), (wr, wd) in zip(v2.plan_together(_paper_kit(k), slide, "points", nums), words):
                def both(nd=nd, wd=wd):
                    nd(); wd()
                both.sizes = getattr(wd, "sizes", {})
                out.append((dict(nr, **wr), both))
            return out
        orders = ([n, 2, 1] if land and image is None else [1, 2]) if n > 2 else ([2, 1] if land and image is None else [1, 2])
        last, fits = None, []
        tries = ([(c_, False, False) for c_ in dict.fromkeys(orders)] + [(c_, True, False) for c_ in dict.fromkeys(orders)]
                 + ([(c_, True, True) for c_ in dict.fromkeys(orders)] if pad else []))
        for rank, (cols, inline, tight) in enumerate(tries):
            if tight and fits:
                break                                    # the narrower margin is only a last resort
            if fits and fits[-1][0] >= big["item_head"] - 0.05:
                break                                    # a layout already sets the points at full size: none can beat it
            rows = -(-n // cols)
            grid = cells(cols, area[1], (area[3] - gap * (rows - 1)) / rows)
            try:
                planned = plan_at(grid, inline, tight)
            except VLTextOverflow as e:
                last = e
                continue
            # each cell as tall as the tallest point's words; the block sits a little above the middle of the room
            need = max(max(v[1] + v[3] for v in r.values()) - c[1] for (r, _d), c in zip(planned, grid)) + pad
            block = rows * need + (rows - 1) * gap
            grid = cells(cols, area[1] + max(0.0, area[3] - block) * 0.4, need)
            try:
                planned = plan_at(grid, inline, tight)
            except VLTextOverflow as e:
                last = e
                continue
            fits.append((planned[0][1].sizes.get("item_head", 0.0), rank, grid, planned))
        if not fits:
            raise last or VLTextOverflow("{}.points(): the points do not fit".format(k.name))
        # the layout that sets the points LARGEST (four points stacked on a portrait page were set at the floor while a
        # 2x2 grid held them at full size); within 5%, the preferred order (row, grid, stack) decides
        top_ = max(f_[0] for f_ in fits)
        _z, _rank, grid, planned = min((f_ for f_ in fits if f_[0] >= 0.95 * top_), key=lambda f_: f_[1])
        return img_rect, (lay if image is not None else None), hr, hd, grid, planned

    # the caller's picture is never dropped for room: on a portrait page it gives up height first (28% → 21% → 15%),
    # a landscape one width (36% → 30%) — three points beside a photo on 3:4 were refused at the first size (2026-10-09)
    last_, done = None, None
    for frac in ((0.36, 0.30) if land else (0.28, 0.21, 0.15)) if image is not None else (None,):
        for hfrac in ((0.30, 0.40) if land else (0.24, 0.34)):     # a long title gets more room (as the drawn ones)
            try:
                done = attempt(frac, hfrac)
                break
            except VLTextOverflow as e:
                last_ = e
        if done:
            break
    if not done:
        raise last_
    img_rect, lay, hr, hd, grid, planned = done
    art = []
    if img_rect is not None:
        _place_image(k, slide, image, img_rect, lay, "points")
    hd()
    rects = dict(hr)
    for i, ((r, d), c) in enumerate(zip(planned, grid)):
        x, y, w, h = c
        if k.name == "soft":
            dk.decorative(dk.box(slide, x, y, w, h, fill=_hex(P["panel"]), round=True, r=0.22),
                          "a soft panel behind one point")
        elif k.name == "collage":
            # the language's own note paper for this ground (white on kraft, cream on slate, with the light ground's inks):
            # a hard-coded white note put slate's yellow numbers on white at 1.68:1 (the lint, 2026-10-09)
            pp = _paper(k)
            dk.decorative(dk.box(slide, x, y, w, h, fill=pp[0] if pp else _hex(P["panel"])), "a paper note holding one point")
            tp = ornaments.tape(slide, x + w * 0.38, y - 0.14 * s, w * 0.24, 0.26 * s, pp[1] if pp else "EDE3C8", rotation=2.0)
            dk.decorative(tp, "washi tape holding the note; ornament")
            dk.overlap_intent(tp, "washi tape across the note's top edge holds it to the page: the overlap is the tape")
        elif k.name == "editorial":
            dk.decorative(dk.box(slide, x, y, w, max(0.012, 0.012 * s), fill=_hex(P["ink"])), "a hairline over one point")
        elif k.name == "storybook":
            dd = 0.24 * s
            # ONE colour — the accent ink, which reads on either ground (>= 3:1). The dots cycled the three FILL accents
            # (orange, green, yellow; the fourth repeating the first): the order meant nothing, and the yellow was 1.05:1
            # on meadow (the group-A verification, 2026-10-15)
            dk.decorative(dk.box(slide, x, y + 0.08 * s, dd, dd, fill=_hex(P["text_accents"][0]), round=True, r=dd / 2),
                          "a painted dot marking one point")
        d()
        for f_, v in r.items():
            rects["{}_{}".format(f_, i + 1)] = v
    return {"rects": rects, "image": img_rect, "free": None}


# ════════════════════════════════════════════════════════════════════════════════════════════════
# collage (was collage.py) — usr/bin/env python3
# ════════════════════════════════════════════════════════════════════════════════════════════════
import random as _random  # noqa: E402
import rotgeom  # noqa: E402

MAX_COVER = 0.25      # the most of the smaller print another print may cover
GROW = 1.12           # a print is ~12% larger than its cell, so neighbours overlap a little
MIN_SIDE = 0.9        # inches — below this a print is a thumbnail, not a print


def _cells(region, n):
    """Cells for n prints. Wide-ish regions: a row of 2, or 2 over 1 centred, or 2x2. Tall regions:
    a column of 2, or a zig-zag of 3 rows (left, right, left), or 2x2."""
    x, y, w, h = region
    tall = h > w * 1.25
    if n == 1:
        return [region]
    if n == 2:
        return ([(x, y, w, h / 2.0), (x, y + h / 2.0, w, h / 2.0)] if tall else
                [(x, y, w / 2.0, h), (x + w / 2.0, y, w / 2.0, h)])
    if n == 3:
        if tall:
            cw, ch = w * 0.72, h / 3.0
            return [(x, y, cw, ch), (x + w - cw, y + ch, cw, ch), (x, y + 2 * ch, cw, ch)]
        cw, ch = w / 2.0, h / 2.0
        return [(x, y, cw, ch), (x + cw, y, cw, ch), (x + (w - cw) / 2.0, y + ch, cw, ch)]
    cw, ch = w / 2.0, h / 2.0
    return [(x + c * cw, y + r * ch, cw, ch) for r in range(2) for c in range(2)]


def _geometry(region, n, rnd, keep_clear, max_tilt):
    cells = _cells(region, n)
    rots = [round(rnd.uniform(-max_tilt, max_tilt), 1) for _ in range(n)]
    scale = GROW
    for _attempt in range(12):
        boxes = []
        for (cx, cy, cw, ch) in cells:
            pw, ph = min(cw * scale, region[2]), min(ch * scale, region[3])
            px = min(max(cx + (cw - pw) / 2.0, region[0]), region[0] + region[2] - pw)
            py = min(max(cy + (ch - ph) / 2.0, region[1]), region[1] + region[3] - ph)
            boxes.append((px, py, pw, ph))
        if min(min(b[2], b[3]) for b in boxes) < MIN_SIDE:
            raise ValueError("collage(): region {} is too small for {} prints (a print side < {}in)"
                             .format(tuple(round(v, 2) for v in region), n, MIN_SIDE))
        polys = [rotgeom.corners(*b, r) for b, r in zip(boxes, rots)]
        clear_ok = keep_clear is None or all(
            rotgeom.overlap(p, rotgeom.rect_poly(*keep_clear))[0] < 1e-6 for p in polys)
        cover_ok = all(rotgeom.overlap(polys[a], polys[b])[0]
                       <= MAX_COVER * min(rotgeom.area(polys[a]), rotgeom.area(polys[b])) + 1e-9
                       for a in range(n) for b in range(a + 1, n))
        if clear_ok and cover_ok:
            return boxes, rots
        scale *= 0.94                                   # shrink toward the cells' centres and retry
    raise ValueError("collage(): cannot place {} prints in {} without covering a print by more than {:.0%} or "
                     "entering keep_clear {} — enlarge the region or use fewer images"
                     .format(n, tuple(round(v, 2) for v in region), MAX_COVER, keep_clear))


def collage(slide, region, items, *, seed=0, keep_clear=None, tape=True, border=0.07, max_tilt=6.0,
            paper="FFFFFF", tape_color="EDE3C8"):
    """Place 1-4 images as prints in `region` (x, y, w, h). Each item is a path, or a dict with "path"
    and "alt", or a dict with "slot", "plan" and "image_dir" (placed through image_series.slot_picture,
    so the image-series tag is kept). `paper` is the print's border colour and `tape_color` the washi strip
    that holds it (white and EDE3C8 unless a dark page asks for a cream print). Returns the picture shapes."""
    import ornaments
    if not (1 <= len(items) <= 4):
        raise ValueError("collage(): 1-4 items, got {}".format(len(items)))
    rnd = _random.Random(seed)
    boxes, rots = _geometry(region, len(items), rnd, keep_clear, max_tilt)
    out = []
    for i, (it, (px, py, pw, ph), rot) in enumerate(zip(items, boxes, rots)):
        it = {"path": it} if isinstance(it, str) else dict(it)
        frame = dk.box(slide, px, py, pw, ph, fill=paper)
        frame.rotation = rot
        dk.overlap_intent(frame, "a print's white border under its own photo")
        b = border * min(pw, ph)
        if it.get("slot"):
            import image_series as ims
            pic = ims.slot_picture(slide, it["plan"], it["slot"], px + b, py + b, pw - 2 * b, ph - 2 * b,
                                   image_dir=it["image_dir"])
        else:
            pic = dk.picture(slide, it["path"], px + b, py + b, pw - 2 * b, ph - 2 * b, fit="cover",
                             alt=it.get("alt") or "photograph")
        pic.rotation = rot
        dk.overlap_intent(pic, "a collage print overlapping its neighbour by design")
        if tape and i % 2 == 0:                     # a strip across the print's top edge, held by the print
            tw, th = pw * 0.34, min(0.32, ph * 0.16)
            t_ = ornaments.tape(slide, px + (pw - tw) / 2.0, py - th * 0.45, tw, th, tape_color,
                                rotation=rot - 3.0, seed=seed + i, holds=frame)
            # a pale washi strip on the white border is 1.28:1 — NON-TEXT CONTRAST, which holds the hand-off;
            # it carries nothing, so say so (the print it holds is the content)
            dk.decorative(t_, "washi tape holding a print; ornament, nothing rides on seeing it")
        out.append(pic)
    return out


# ════════════════════════════════════════════════════════════════════════════════════════════════
# Bundled samples — the direction preview shows these ("style sample — not your content").
# ════════════════════════════════════════════════════════════════════════════════════════════════
ASSETS = HERE.parent / "assets" / "vl"
# a package with no pictures (SkillHub accepts no image files) previews a language from the library's copy of the
# same sample; the direction preview lays it over the palette cover, which shows if it cannot load (offline)
SAMPLE_SITE = "https://slides.addsum.top/languages/media/{name}/sample-{ground}.jpg"


def sample_picture(rel):
    """A picture bundled with the skill (`photo/hall-repair.jpg`, `figure/…`, `watercolour/…`, relative to assets/vl)
    for the sample decks and the runnable examples — it stands for YOUR picture. A package that ships no pictures
    (SkillHub accepts no image files) has no assets/: a plain stand-in of the same kind is drawn once into the temp
    folder instead (no words on it; a cutout stays transparent), so every example still runs as printed."""
    p = ASSETS / rel
    if p.exists():
        return str(p)
    import tempfile
    out = Path(tempfile.gettempdir()) / "slide-maker-sample-pictures" / rel
    if not out.exists():
        from PIL import Image, ImageDraw
        out.parent.mkdir(parents=True, exist_ok=True)
        kind = rel.split("/", 1)[0]
        if out.suffix.lower() == ".png":                 # a cutout: a soft subject on transparency
            im = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
            dr = ImageDraw.Draw(im)
            dr.ellipse((150, 120, 650, 700), fill=(176, 150, 120, 255))
            dr.ellipse((260, 230, 540, 510), fill=(206, 186, 158, 255))
        elif kind == "figure":                            # a figure: a few curves on white
            im = Image.new("RGB", (1200, 900), (255, 255, 255))
            dr = ImageDraw.Draw(im)
            dr.line([(120, 780), (1100, 780)], fill=(90, 90, 90), width=4)
            dr.line([(120, 780), (120, 100)], fill=(90, 90, 90), width=4)
            for i, col in enumerate(((40, 90, 160), (190, 90, 40))):
                pts = [(120 + x, 760 - int((x / 980.0) ** (1.6 + i) * 600)) for x in range(0, 981, 20)]
                dr.line(pts, fill=col, width=6)
        else:                                             # a photograph or a watercolour: a quiet gradient
            top, bot = ((214, 196, 170), (120, 104, 88)) if kind == "photo" else ((232, 226, 206), (178, 196, 160))
            im = Image.new("RGB", (1200, 800))
            dr = ImageDraw.Draw(im)
            for y in range(800):
                t = y / 799.0
                dr.line([(0, y), (1199, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))
            dr.ellipse((700, 260, 1000, 560), fill=tuple(max(0, c - 30) for c in bot))
        tmp = out.with_name(out.stem + ".part" + out.suffix)
        im.save(str(tmp))
        tmp.replace(out)                                  # atomic: a parallel run never reads half a file
    return str(out)


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
def _resolved_copy(pages):
    """A manifest's sample copy with each picture path resolved under assets/vl (a manifest stores it relative: an
    absolute path baked in by the migration broke every other checkout — final review)."""
    out = []
    for page, fields in pages:
        f = dict(fields)
        if isinstance(f.get("image"), str) and not Path(f["image"]).is_absolute():
            f["image"] = sample_picture(f["image"])
        out.append((page, f))
    return out


_SAMPLE_COPY_NATIVE = {n: _resolved_copy(REGISTRY[n]["samples"]["copy"]) for n in NATIVE}


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
    imgs = [sample_picture(x) for x in SAMPLE_IMAGES[kind]]
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
    _record_hues(render_dir, Path(out_jpg).parent, stem)
    return out_jpg


def _record_hues(render_dir, folder, stem):
    """Measure which of the language's chromatic colours its rendered sample pages really PAINT (as the register-pixels
    gate measures: the largest share on any one page) into <folder>/hues.json. --gates declares exactly these — the text
    accents it declared before (a kicker's red, a hairline's gold) never reached the gate's floor, and broadsheet,
    soft dusk, ink night and cutpaper night failed DECLARED HUES ABSENT on their own samples (docs audit, 2026-10-09)."""
    import json
    import check_register_pixels as crp
    hit = [(n_, g_) for n_ in LANGS for g_ in VARIANTS[n_] if _sample_stem(n_, g_) == stem]
    if not hit:
        return None
    P = VARIANTS[hit[0][0]][hit[0][1]]["palette"]
    cands = [c.upper() for c in dict.fromkeys(list(P["accents"]) + list(P["text_accents"])) if crp._chromatic(_rgb(c))]
    pngs = sorted(str(q) for q in Path(render_dir).glob("slide*.png"))
    seen = crp.presence(pngs, [_rgb(c) for c in cands]) if pngs else {}
    got = ["#" + c for c in cands if seen.get(_rgb(c), 0) >= crp.PRESENT]
    hf = Path(folder) / "hues.json"
    rec = json.loads(hf.read_text(encoding="utf-8")) if hf.exists() else {}
    rec[stem] = got
    hf.write_text(json.dumps(dict(sorted(rec.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return got


def painted_hues(name, ground):
    """The hues `name` paints on `ground`, as measured on its sample pages (hues.json), or None when not recorded."""
    import json
    hf = ASSETS / "samples" / "hues.json"
    try:
        return json.loads(hf.read_text(encoding="utf-8")).get(_sample_stem(name, ground))
    except Exception:
        return None


_DISPLAY_NAMES = {n: s["display"]["en"] for n, s in REGISTRY.items()}
_RATIONALE = {n: s["rationale"] for n, s in REGISTRY.items()}


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
    if sample.exists():
        sample_src = "data:image/jpeg;base64," + base64.b64encode(sample.read_bytes()).decode("ascii")
    elif not ASSETS.exists():          # a package with no pictures (SkillHub): the library's copy of the same sample
        sample_src = SAMPLE_SITE.format(name=name, ground=ground)
    else:
        raise FileNotFoundError("visual_languages.direction(): no bundled sample at {} — rebuild it: python3 "
                                "scripts/visual_languages.py --sample <dir>".format(sample))
    return {"name": _DISPLAY_NAMES[name] + ("" if ground == "light" else " · " + VARIANTS[name][ground]["label"]),
            "vl": name, "vl_ground": ground, "rationale": _RATIONALE[name],
            "bg": "#" + _hex(p["ground"]), "ink": "#" + _hex(p["ink"]), "accent": "#" + _hex(p["text_accents"][0]),
            "accents": ["#" + _hex(a) for a in p["text_accents"]],
            "font_display": f["display"], "font_body": f["body"], "cover": L["cover"], "skeleton": L["skeleton"],
            "sample": sample_src}

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
    hues = painted_hues(name, ground)
    if hues is None:                       # not measured here: the fill accents, never the text ones (see _record_hues)
        hues = ["#" + h for h in p["accents"]]
    pal = "ground #{} ink #{}".format(p["ground"], p["ink"]) + (
        " accents {}".format(" ".join(hues)) if hues else
        " — a neutral register: its accent colour is a type colour, too small to carry a page")
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


_CARD_PAGES = ("cover", "section", "image_text", "points", "quote", "data", "closing")


def _example_lines(name):
    """The language's sample deck as code that runs as printed, from any folder (the bundled sample's own calls)."""
    code = ["import sys", "sys.path.insert(0, {!r})".format(str(HERE)), "import deckkit as dk, visual_languages as vl",
            "prs = dk.blank_deck(13.333, 7.5)", "k = vl.use({!r}, prs)".format(name)]
    if name in NATIVE:
        code += ["k.{}(k.new_slide(), **{!r})".format(page, fields) for page, fields in _SAMPLE_COPY_NATIVE[name]]
    else:
        kind = "watercolour" if name == "storybook" else "photo"
        imgs = [sample_picture(x) for x in SAMPLE_IMAGES[kind]]
        T = _SAMPLE_COPY[kind]
        code += ["k.cover(k.new_slide(), kicker={!r}, title={!r}, image={!r})".format(
                     T["kicker"], T["title"], imgs[:3] if name == "collage" else imgs[0]),
                 "k.image_text(k.new_slide(), kicker={!r}, title={!r}, body={!r}, image={!r})".format(
                     T["kicker"], T["it_title"], T["body"], imgs[1]),
                 "k.quote(k.new_slide(), quote={!r}, attribution={!r}, image={!r})".format(T["quote"], T["attr"], imgs[2]),
                 "k.data(k.new_slide(), number={!r}, label={!r}, note={!r}, image={!r})".format(
                     T["num"], T["label"], T["note"], imgs[3])]
    out = name + "-example.pptx"
    code += ["prs.save({!r})".format(out),
             "print({!r})".format("saved {} — NEXT: python3 {} {}".format(out, HERE / "render_deck.py", out))]
    return code


def describe(name):
    """A language's card, printed from its manifest alone: what it is, its grounds, its pages, the extras it takes
    (which pages, whether the deck remembers them, what to pass, what an absent one means), the words it derives, the
    topics it is offered for, its faces — and its sample deck as code that runs as printed."""
    chk = HERE / "check_vl_contract.py"
    if name in _vl_specs.DRAFTS:
        return ("{n}: a draft — its manifest (scripts/vl_specs/{f}) still holds FILL: decisions, so it is not offered "
                "or usable yet.\nNEXT: python3 {c} {n}   (names each decision still to make)\n").format(
                    n=name, f=_vl_specs.DRAFTS[name], c=chk)
    sp = REGISTRY[name]
    out = ["{} — {} / {}  ({})".format(name, sp["display"]["en"], sp["display"]["zh"], sp["kind"]), sp["rationale"],
           "grounds:"]
    out += ["  {:<10} {} / {} — a {} ground".format(g, gd["label"], gd["label_zh"], "dark" if gd["dark"] else "light")
            for g, gd in sp["grounds"].items()]
    out.append("pages: " + ", ".join(_CARD_PAGES) + (
        "   (a picture on: {})".format(", ".join(sp["image_pages"])) if sp["image_pages"] else ""))
    out.append("extras:" + ("" if sp["extras"] else " none"))
    for x, d in sp["extras"].items():
        out.append("  {}= on {}{} — takes {}; without it: {}".format(
            x, "every page" if d["pages"] == "any" else ", ".join(d["pages"]),
            ", remembered for the deck" if d["remembered"] else "", d["takes"], d["absent"]))
    out.append("derived words:" + ("" if sp["derived"] else " none — every word on a page is the caller's"))
    for dv in sp["derived"]:
        words = "; ".join("{}: {}".format(l, " ".join(w)) for l, w in dv["words"].items()) or "no words — a mark"
        out.append("  {} — {} ({})".format(dv["id"], dv["what"], words))
    off = sp["offer"]
    out.append("offered for: " + ("; ".join("{}: {}".format(l, ", ".join(off[l])) for l in ("en", "zh") if l in off)
                                  if "en" in off else "decks with {}".format(off.get("pictures"))))
    fo = sp["look"]["fonts"]
    out.append("fonts: both {}  mac {}".format(fo.get("both"), fo.get("mac")))
    if not ready(name):
        out.append("not ready: " + _UNREADY[name])
        return "\n".join(out) + "\n"
    out.append("example (runs as printed from any folder; saves {}-example.pptx there):".format(name))
    out += _example_lines(name)
    return "\n".join(out) + "\n"


def main(argv=None):
    import argparse
    import shlex
    ap = argparse.ArgumentParser(description="visual languages: build the bundled samples")
    ap.add_argument("--sample", metavar="OUT_DIR", help="build sample-<name>.pptx for every language")
    ap.add_argument("--refresh-bundled", action="store_true", help="maintainers, with --sample: the printed then: "
                    "lines overwrite the BUNDLED previews in assets/vl/samples (and their manifest.json)")
    ap.add_argument("--sample-sheet", nargs=2, metavar=("RENDER_DIR", "OUT_JPG"),
                    help="contact a rendered sample's four pages into one JPEG")
    ap.add_argument("--list", action="store_true", help="list the languages")
    ap.add_argument("--describe", metavar="NAME", help="print a language's card and an example that runs as printed")
    ap.add_argument("--gates", metavar="NAME", help="print the exact record commands for a deck in this language")
    ap.add_argument("--deck", metavar="DECK_DIR", help="with --gates (required): the deck folder")
    ap.add_argument("--for", dest="topic", metavar="TOPIC", default=None, help="with --gates: what the deck is for")
    ap.add_argument("--fonts", choices=("both", "mac"), default="both", help="with --gates: the fonts= you passed to use()")
    ap.add_argument("--ground", default=None, help="with --gates: the ground the deck was built on (light — the default "
                    "— the language's contrast ground, or auto)")
    a = ap.parse_args(argv)
    if a.describe:
        if a.describe not in REGISTRY and a.describe not in _vl_specs.DRAFTS:
            print("visual_languages: --describe {!r}: no such language — one of {}".format(
                a.describe, ", ".join(list(REGISTRY) + list(_vl_specs.DRAFTS))), file=sys.stderr)
            return 2
        print(describe(a.describe), end="")
        return 0
    if a.gates:
        if not a.deck:                    # a printed placeholder path runs nowhere — refuse instead
            print("visual_languages: --gates needs --deck <the deck folder>, so every printed command runs as "
                  "printed", file=sys.stderr)
            return 2
        if a.deck.strip() in ("DECK_DIR", "<deck>") or "<" in a.deck or ">" in a.deck:   # a template, run verbatim
            print("visual_languages: --deck {!r} is a placeholder — pass the folder the deck is saved in".format(a.deck),
                  file=sys.stderr)
            return 2
        if a.gates in REGISTRY:
            other = [g for g in REGISTRY[a.gates]["grounds"] if g != "light"]
            if a.ground is None:              # it was recorded silently (docs-only run, 2026-10-16)
                print("# ground: light — the default; for the contrast ground pass --ground {}".format(
                    " / --ground ".join(other)))
            elif a.ground in REGISTRY[a.gates]["grounds"]:
                print("# ground: {g} — if the USER named it and GROUND REPEAT holds the deck, append ' — deliberate "
                      "repeat: the user named the {g} ground' to design_plan.palette (the waiver that check names)".format(
                          g=a.ground))
        return _print_gates(a.gates, a.deck, a.topic, a.fonts, a.ground or "light")
    if a.refresh_bundled and not a.sample:
        print("visual_languages: --refresh-bundled goes with --sample <OUT_DIR>", file=sys.stderr)
        return 2
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
            rd = Path(a.sample).resolve() / ("render-" + _sample_stem(n, g))
            # absolute script paths (they ran only from the skill folder), and the sheet lands in OUT_DIR: a then:
            # line run verbatim used to overwrite the bundled preview (audit 2026-10-09) — that is --refresh-bundled
            sheet = (ASSETS / "samples" if a.refresh_bundled else Path(a.sample).resolve()) / (_sample_stem(n, g) + ".jpg")
            print("built", out)
            print("NEXT: python3 {} {} {}".format(shlex.quote(str(HERE / "render_deck.py")), shlex.quote(str(Path(out).resolve())),
                                                  shlex.quote(str(rd))))
            print("then: python3 {} --sample-sheet {} {}".format(shlex.quote(str(HERE / "visual_languages.py")),
                                                                 shlex.quote(str(rd)), shlex.quote(str(sheet))))
    return 0


# the languages written after the fifteen, now that every name above exists. A module language is registered with
# stand-in painters and imported on first use (ready()), so a deck that never picks one never imports vl_native.
for _n in _PENDING:
    if _has_module(_n):
        _LAZY.add(_n)
        rs.register(_n, ground=_lazy_painter(_n, "ground"), card=_lazy_painter(_n, "card"),
                    forbids=LANGS[_n]["forbids"], source=__file__)
    else:
        _register(_n)


if __name__ == "__main__":
    sys.exit(main())
