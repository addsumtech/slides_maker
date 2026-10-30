#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brand_kit — the user's brand files -> one reviewed brand spec -> the deck's palette and faces ->
a check of the BUILT deck for off-brand colours, faces and the logo rule.

A company / lab / product deck should come out on-brand without anyone hand-building a .potx. The
user hands over what they have — a logo (SVG/PNG/JPG), a brand-guide PDF, an old on-brand
.pptx/.potx, or just hex codes and font names — and this turns it into ONE brand.json that a person
reviewed, uses it for the deck's palette and faces, and checks the built deck before hand-off.

    python3 scripts/brand_kit.py extract logo.svg guide.pdf old.pptx [--hex #0B5FFF …] [--font "Inter" …] --out <deck-dir>/brand.json
    python3 scripts/brand_kit.py review  <brand.json> [--auto]
    python3 scripts/brand_kit.py confirm <brand.json> --primary #RRGGBB [--accent …] [--secondary …] [--neutral …]
                                         [--heading-font …] [--body-font …] [--cjk-font …] [--mono-font …] [--lang zh-Hans]
    python3 scripts/brand_kit.py style   <brand.json> [--ground light|dark] [--out <deck-dir>/brand_style.py]
    python3 scripts/brand_kit.py check   <deck.pptx> --brand <brand.json> [--multi-entity] [--json]
    python3 scripts/brand_kit.py save <brand.json> --name N  ·  list  ·  use N <deck-dir>
    python3 scripts/brand_kit.py --selftest

Every successful command prints a `NEXT:` line naming the exact next command; every failure names the
cause and the fix. Local only: no network, no metered API.

🔴 NEVER INVENT. Every value in brand.json comes from a file the user supplied or a value the user
typed, and records its `source`. A Pantone or CMYK reference with no hex beside it is listed as
UNDECIDED, never converted from memory; a brand with no named face is checked on colour alone and
says so. The only DERIVED values are shades a contrast floor forces (a primary too light to read as
text gets a darker twin of the SAME hue), and they record what they were derived from.

🔴 A DRAFT CANNOT BE USED. `style` and `check` refuse anything `confirm` has not signed, and a
brand.json whose roles were edited after `confirm` is refused too (`confirmed.digest`): the roles a
person reviewed are the only roles that bind.

WHAT `check` ALLOWS. A colour is on-brand when it is a brand colour, a TINT or SHADE of one (its mix
with white, black or a declared neutral — how every deckkit tint is made), or a declared neutral;
plus, unless `--strict-neutrals` was given at confirm, any achromatic grey. Distance is CIEDE2000 to
the nearest point on those mixing ramps, against TOLERANCE_DE (calibrated — see the constant).
Pictures are ignored (a photograph carries every hue); text, fills, lines, slide backgrounds, table
cells and native chart series are read. ANTI-GOAL: a check that flags every chart tint so people
learn to waive it — which is why tints are allowed by construction rather than listed.

GATE. `.deck-gates.json` / `.codex-deck-evidence.json` section `brand`:
    {"file": "brand.json"}                         (path relative to the deck folder), or
    {"waived": "<why>", "waived_category": "co-branded | user-approved-deviation | third-party-material"}
No section -> no brand gate; a deck without a brand is unaffected.

Exit 0 clean · 1 findings / refused · 2 could not run (unreadable input).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SELF = "python3 " + shlex.quote(str(HERE / "brand_kit.py"))
SCHEMA = "slide-maker/brand@1"
ASSETS = "brand-assets"

# 🔴 CALIBRATED on four invented brands (blue / green+CJK / saffron on a dark ground / a low-chroma
# graphite), each built from `style` output with real deckkit components — tests/test_brand_kit.py
# keeps two of them as the regression. CIEDE2000 to the nearest point on the tint/shade ramps:
#   on-brand colours in the built decks ........ max 0.49 (integer rounding of deckkit's mixes)
#   a JPEG q75 round-trip of a brand colour ..... max 0.70
#   +-3 RGB drift (an eyedropper, colour mgmt) .. p99 2.13 / 2.76 / 2.31 / 4.09 per brand
#   the deliberately off-brand variants ......... min 8.7 (a jade series on the green brand;
#     violet / raspberry text and fills 17.8-28.6)
#   a 10-degree hue rotation of primary/accent .. min 3.76 / 5.54 on mid-chroma hues, but 0.87 for
#     the saturated blue (gamut clipping pulls it back) and 1.93 for the low-chroma graphite
# 3.0 clears every on-brand use with ~6x headroom and catches every deliberate variant; what it
# lets through is what a person reads as the SAME colour (a clipped azure beside a brand blue,
# deckkit's own SLATE beside a graphite brand at 1.8). Lower and eyedropper drift starts failing
# real decks; higher and deckkit's stock MUTE/DEEP/GOLD (3.8 / 4.5 / 5.1 from the blue brand) would pass.
TOLERANCE_DE = 3.0
# Lab chroma at or below which a colour is a grey (no hue to be off-brand WITH). Pure greys measure
# 0; deckkit's own blue-grey SLATE/MUTE measure 9.2, so they are NOT swept in by this.
ACHROMATIC_C = 4.0
LOGO_MATCH = 14.0              # mean abs diff (0-255) of 24x24 premultiplied thumbnails
WAIVER_CATEGORIES = ("co-branded", "user-approved-deviation", "third-party-material")
MIN_WAIVER = 24
ROLES = ("primary", "accent", "secondary", "neutral")
LANGS = {"zh-Hans": "han", "zh-Hant": "han", "ja": "kana", "ko": "hangul"}
# a sample of what each script's deck will actually set — the commonest characters, so a face that
# lacks them fails here rather than as tofu on a slide
_GLYPHS = {
    "zh-Hans": "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处府研完",
    "zh-Hant": "的一是在不了有和人這中大為上個國我以要他時來用們生到作地於出就分對成會可主發年動同工也能下過子說產種面而方後多定行學法所民得經十三之進著等部度家電力裡如水化高自二理起小物現實加量都兩體制機當使點從業本去把性好應開它合還因由其些然前外天政四日那社義事平形相全表間樣與關各重新線內數正心反你明看原又麼利比或但質氣第向道命此變條只沒結解問意建月公無系軍很情者最立代想已通並提直題黨程展五果料象員革位入常文總次品式活設及管特件長求老頭基資邊流路級少圖山統接知較將組見計別她手角期根論運農指幾九區強放決西被幹做必戰先回則任取據處府研完",
    "ja": "のにはをたがでてとしれさあるいうかなこもすつよりらまやわんアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン日本語人年大中出会社国時事自分行見上下前後新学生先",
    "ko": "이가은는을를의에서와과도로으로하다있습니다그리고한국어사람시간오늘내일우리모두위해대한것수년월일중요새로운회사제품고객",
}


# ════════════════════════════════════════════════════════════════════════ colour maths

def norm_hex(v):
    """'#0b5fff' / '0B5FFF' / '#abc' -> '#0B5FFF'; None when it is not a hex colour."""
    s = str(v or "").strip().lstrip("#")
    if re.fullmatch(r"[0-9A-Fa-f]{3}", s):
        s = "".join(c * 2 for c in s)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        return None
    return "#" + s.upper()


def rgb_of(h):
    h = norm_hex(h)
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def hex_of(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(rgb):
    r, g, b = (_lin(v) for v in rgb)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = (0.2126729 * r + 0.7151522 * g + 0.0721750 * b)
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def chroma(rgb):
    _l, a, b = lab(rgb)
    return math.hypot(a, b)


def de2000(lab1, labs):
    """CIEDE2000 from one Lab colour to an (N,3) array of them. numpy, vectorised."""
    import numpy as np
    L1, a1, b1 = lab1
    L2, a2, b2 = labs[:, 0], labs[:, 1], labs[:, 2]
    C1 = math.hypot(a1, b1)
    C2 = np.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2 - L1
    dCp = C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(C1p * C2p == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    hs = h1p + h2p
    hbp = np.where(C1p * C2p == 0, hs,
                   np.where(np.abs(h1p - h2p) <= 180, hs / 2,
                            np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dtheta = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dtheta)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                   + Rt * (dCp / Sc) * (dHp / Sh))


def de(h1, h2):
    import numpy as np
    return float(de2000(lab(rgb_of(h1)), np.array([lab(rgb_of(h2))]))[0])


def contrast(h1, h2):
    sys.path.insert(0, str(HERE))
    import palette_audit as pa                # the skill's one WCAG ratio
    return pa.ratio(norm_hex(h1)[1:], norm_hex(h2)[1:])


def mix(h1, h2, t):
    """h1 mixed toward h2 by t in sRGB — the way deckkit.tint / _blend make every tint."""
    a, b = rgb_of(h1), rgb_of(h2)
    return hex_of(tuple(x + (y - x) * t for x, y in zip(a, b)))


# ════════════════════════════════════════════════════════════════════════ small io helpers

class Unreadable(Exception):
    """An input file cannot be read — exit 2 with the file named."""


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _now():
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def load_brand(path):
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Unreadable("{} does not exist — run `{} extract <files…> --out {}` first."
                         .format(p, _SELF, p))
    except (OSError, ValueError) as exc:
        raise Unreadable("{} is not readable JSON ({}). Re-run extract, or fix the file."
                         .format(p, exc))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise Unreadable("{} is not a brand kit (no `schema: {}`) — make one with `{} extract`."
                         .format(p, SCHEMA, _SELF))
    return data


def save_brand(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _rel(path, base):
    try:
        return str(Path(path).resolve().relative_to(Path(base).resolve()))
    except ValueError:
        return str(Path(path).resolve())


# ════════════════════════════════════════════════════════════════════════ extractors

def _pixels(im):
    """A PIL image's pixels as a list — `get_flattened_data` where Pillow has it (getdata is going)."""
    f = getattr(im, "get_flattened_data", None)
    return list(f() if f else im.getdata())


def _clusters(pixels, min_share=0.04):
    """[(hex, share)] for a list of RGB tuples: binned, averaged, merged under dE 8, small dropped."""
    if not pixels:
        return []
    bins = {}
    for p in pixels:
        k = (p[0] >> 4, p[1] >> 4, p[2] >> 4)
        e = bins.setdefault(k, [0, 0, 0, 0])
        e[0] += p[0]
        e[1] += p[1]
        e[2] += p[2]
        e[3] += 1
    raw = sorted(((tuple(v[i] / v[3] for i in range(3)), v[3]) for v in bins.values()),
                 key=lambda t: -t[1])
    merged = []                                   # [[rgb_sum(3), n, lab]]
    for rgb, n in raw:
        L = lab(rgb)
        for m in merged:
            if de(hex_of(m[0]), hex_of(rgb)) < 8:
                tot = m[1] + n
                m[0] = tuple((m[0][i] * m[1] + rgb[i] * n) / tot for i in range(3))
                m[1] = tot
                break
        else:
            merged.append([rgb, n, L])
    total = float(len(pixels))
    out = [(hex_of(m[0]), m[1] / total) for m in merged if m[1] / total >= min_share]
    return sorted(out, key=lambda t: -t[1])


def _raster_marks(img):
    """(marks [(hex, share)], plate_hex | None) from a PIL image: transparent or plate pixels out."""
    im = img.convert("RGBA")
    im.thumbnail((256, 256))
    px = _pixels(im)
    if any(a < 250 for *_c, a in px):
        fg = [(r, g, b) for r, g, b, a in px if a >= 128]
        return _clusters(fg), None
    w, h = im.size
    border = [px[i] for i in range(w)] + [px[(h - 1) * w + i] for i in range(w)] + \
             [px[j * w] for j in range(h)] + [px[j * w + w - 1] for j in range(h)]
    counts = {}
    for r, g, b, _a in border:
        k = (r >> 3, g >> 3, b >> 3)
        counts[k] = counts.get(k, 0) + 1
    k, n = max(counts.items(), key=lambda t: t[1])
    if n < 0.6 * len(border):                    # no single plate colour: the whole image is the mark
        return _clusters([(r, g, b) for r, g, b, _a in px]), None
    plate = hex_of(tuple(sum(p[i] for p in border if (p[0] >> 3, p[1] >> 3, p[2] >> 3) == k) / n
                         for i in range(3)))
    pl = lab(rgb_of(plate))
    import numpy as np
    arr = np.array([lab((r, g, b)) for r, g, b, _a in px])
    far = np.sqrt(((arr - np.array(pl)) ** 2).sum(axis=1)) > 12
    fg = [px[i][:3] for i in range(len(px)) if far[i]]
    return _clusters(fg), plate


def _ground_of(marks, plate=None):
    """light | dark | both | neither — where the mark reads at >= 3:1 (WCAG non-text) for >= 60% of
    its weight. A logo on its own opaque plate reads where the plate does."""
    if plate is not None:
        return "light" if contrast(plate, "#000000") > contrast(plate, "#FFFFFF") else "dark"
    tot = sum(s for _h, s in marks) or 1.0
    light = sum(s for h, s in marks if contrast(h, "#FFFFFF") >= 3.0) / tot >= 0.6
    dark = sum(s for h, s in marks if contrast(h, "#111111") >= 3.0) / tot >= 0.6
    return "both" if light and dark else "light" if light else "dark" if dark else "neither"


_CSS_COL = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b|rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)")


def _css_colour(v):
    v = (v or "").strip()
    m = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", v)
    if m:
        return hex_of(tuple(int(g) for g in m.groups()))
    return norm_hex(v) if v.startswith("#") else None


def from_svg(path, assets):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8", "replace")
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.I):
        raise Unreadable("{} declares a DOCTYPE/ENTITY — refused (entity expansion). Export the "
                         "logo again without one, or pass its colours with --hex.".format(path))
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Unreadable("{} is not a readable SVG ({}).".format(path, exc))
    declared, unparsed = {}, set()
    for el in root.iter():
        vals = []
        for attr in ("fill", "stroke", "stop-color"):
            if el.get(attr):
                vals.append((attr, el.get(attr)))
        for decl in (el.get("style") or "").split(";"):
            if ":" in decl:
                k, v = decl.split(":", 1)
                if k.strip() in ("fill", "stroke", "stop-color"):
                    vals.append((k.strip(), v))
        if el.tag.endswith("style") and el.text:
            vals += [("css", m.group(0)) for m in _CSS_COL.finditer(el.text)]
        for kind, v in vals:
            v = v.strip()
            if v.lower() in ("none", "transparent", "currentcolor", "inherit") or v.startswith("url("):
                continue
            h = _css_colour(v)
            if h:
                declared.setdefault(h, set()).add(kind)
            else:
                unparsed.add(v)
    # the RENDER: weight for the declared colours, and the only truth when none are declared
    import fitz
    try:
        doc = fitz.open(stream=raw, filetype="svg")
        page = doc[0]
        zoom = 600.0 / max(page.rect.width, 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    except Exception as exc:
        raise Unreadable("{} could not be rendered ({}).".format(path, exc))
    assets.mkdir(parents=True, exist_ok=True)
    raster = assets / (Path(path).stem + ".png")
    pix.save(str(raster))
    from PIL import Image
    marks, _plate = _raster_marks(Image.open(raster))
    notes = []
    colours = []
    if declared:
        import numpy as np
        mark_labs = [(h, s, lab(rgb_of(h))) for h, s in marks]
        for h, kinds in declared.items():
            w = sum(s for mh, s, ml in mark_labs if de(mh, h) < 6)
            colours.append({"hex": h, "source": "{} ({})".format(Path(path).name, "/".join(sorted(kinds))),
                            "weight": round(w, 3), "kind": "logo"})
    else:
        notes.append("{} declares no fill/stroke colours — read its RENDERED colours instead "
                     "(an unfilled SVG shape renders black, per the SVG spec).".format(Path(path).name))
        colours = [{"hex": h, "source": "{} (rendered)".format(Path(path).name), "weight": round(s, 3),
                    "kind": "logo"} for h, s in marks]
    undecided = ["{}: colour value {!r} is not a hex/rgb() — pass it with --hex if it is a brand "
                 "colour".format(Path(path).name, v) for v in sorted(unparsed)]
    logo = {"file": None, "raster": None, "ground": _ground_of(marks), "marks": marks}
    return colours, logo, raster, notes, undecided


def from_raster(path):
    from PIL import Image, UnidentifiedImageError
    try:
        img = Image.open(path)
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise Unreadable("{} is not a readable image ({}).".format(path, exc.__class__.__name__))
    marks, plate = _raster_marks(img)
    colours = [{"hex": h, "source": "{} (pixels)".format(Path(path).name), "weight": round(s, 3),
                "kind": "logo"} for h, s in marks]
    logo = {"file": None, "raster": None, "ground": _ground_of(marks, plate), "marks": marks}
    if plate:
        logo["plate"] = plate
    return colours, logo


_HEX_TXT = re.compile(r"(?<![0-9A-Za-z&])#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Za-z])")
_HEX_LBL = re.compile(r"\bHEX\b\s*[:#]?\s*([0-9A-Fa-f]{6})\b", re.I)
_RGB_TXT = [re.compile(r"\bRGB\b\s*[:(]?\s*(\d{1,3})\s*[,/ ]\s*(\d{1,3})\s*[,/ ]\s*(\d{1,3})", re.I),
            re.compile(r"\bR\s*[:=]?\s*(\d{1,3})\s+G\s*[:=]?\s*(\d{1,3})\s+B\s*[:=]?\s*(\d{1,3})\b")]
_PRINT_ONLY = re.compile(r"\b(pantone|pms|cmyk|ral)\b", re.I)
_ROLE_WORDS = (("primary", ("primary", "main colour", "main color", "主色", "主要")),
               ("accent", ("accent", "highlight", "强调", "辅助", "点缀")),
               ("secondary", ("secondary", "supporting", "次要", "第二")),
               ("neutral", ("neutral", "background", "text colour", "text color", "grey", "gray",
                            "black", "white", "ink", "paper", "中性", "背景", "灰", "墨", "纸")))
_FONT_KW = re.compile(r"typeface|type face|font|字体|字型|書体|서체", re.I)
_FONT_ROLE = (("heading", re.compile(r"heading|headline|display|title|标题|見出し|제목", re.I)),
              ("body", re.compile(r"\bbody|paragraph|\btext\b|copy|正文|本文|본문", re.I)),
              ("cjk", re.compile(r"chinese|japanese|korean|cjk|中文|日本語|한국어|汉字|漢字", re.I)),
              ("mono", re.compile(r"\bcode\b|mono", re.I)))
_FONT_AFTER = re.compile(r"(?:typeface|font|字体|字型)s?\s*(?:[:：]|is|=)\s*"
                         r"([A-Z一-鿿][\w一-鿿 .\-]{1,40}?)"
                         r"(?=\s+(?:for|is|in|on|at|with|—|–)\b|[,.;()（]|\s*$)", re.I)


def _role_from(text):
    t = text.lower()
    for role, words in _ROLE_WORDS:
        if any(w in t for w in words):
            return role
    return None


def _installed_families():
    try:
        from matplotlib import font_manager as fm
        return sorted({f.name for f in fm.fontManager.ttflist}, key=len, reverse=True)
    except Exception:
        return []


def _family_of(basefont):
    """'ABCDEF+Inter-SemiBold' -> 'Inter' (PDF subset prefix and style suffix off)."""
    name = re.sub(r"^[A-Z]{6}\+", "", basefont or "")
    name = re.split(r"[-,]", name)[0]
    name = re.sub(r"(MT|PS|Std|Pro)$", "", name)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).strip()


_BASE14 = {"Helvetica", "Times", "Courier", "Symbol", "Zapf Dingbats", "Helv", "Ti Ro", "Cour",
           "Times Roman", "Times New Roman"}


def from_pdf(path):
    import fitz
    try:
        doc = fitz.open(path)
    except Exception as exc:
        raise Unreadable("{} is not a readable PDF ({}).".format(path, exc.__class__.__name__))
    name = Path(path).name
    colours, fonts, undecided = [], [], []
    families = None
    for pno, page in enumerate(doc, 1):
        for line in page.get_text("text").splitlines():
            found = []
            for m in _HEX_TXT.finditer(line):
                found.append(norm_hex(m.group(1)))
            for m in _HEX_LBL.finditer(line):
                found.append(norm_hex(m.group(1)))
            for rx in _RGB_TXT:
                for m in rx.finditer(line):
                    vals = [int(g) for g in m.groups()]
                    if all(0 <= v <= 255 for v in vals):
                        found.append(hex_of(vals))
            label = re.sub(r"\s+", " ", _HEX_TXT.sub("", _HEX_LBL.sub("", line))).strip()
            for h in dict.fromkeys(found):
                colours.append({"hex": h, "source": "{} p{} text".format(name, pno),
                                "label": label[:60], "role_guess": _role_from(line),
                                "weight": 1.0, "kind": "guide"})
            if not found and _PRINT_ONLY.search(line):
                undecided.append("{} p{}: {!r} — a print reference with no hex/RGB beside it; ask "
                                 "for the hex (never convert it from memory)".format(name, pno,
                                                                                      line.strip()))
            if _FONT_KW.search(line):
                if families is None:
                    families = _installed_families()
                face = None
                low = line.lower()
                for fam in families:
                    if len(fam) > 2 and re.search(r"(?<![\w])" + re.escape(fam.lower()) + r"(?![\w])", low):
                        face = fam
                        break
                if face is None:
                    m = _FONT_AFTER.search(line)
                    face = m.group(1).strip() if m else None
                if face:
                    role = next((r for r, rx in _FONT_ROLE if rx.search(line)), None)
                    fonts.append({"name": face, "source": "{} p{} text".format(name, pno),
                                  "role_guess": role})
        try:
            for f in page.get_fonts(full=True):
                ext, basefont = f[1], f[3]
                fam = _family_of(basefont)
                if ext and ext != "n/a" and fam and fam not in _BASE14:
                    fonts.append({"name": fam, "source": "{} p{} (embedded)".format(name, pno),
                                  "role_guess": None})
        except Exception:
            pass
    return colours, fonts, undecided


_THEME_SLOTS = ("accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
                "dk1", "lt1", "dk2", "lt2")


def from_pptx(path):
    sys.path.insert(0, str(HERE))
    try:
        import deckkit
        prs = deckkit.open_presentation(str(path))
    except Exception as exc:
        raise Unreadable("{} is not a readable .pptx/.potx ({}: {}).".format(
            path, exc.__class__.__name__, exc))
    import lint_deck
    import check_fonts_resolve as cfr
    name = Path(path).name
    colours, fonts = [], []
    master = prs.slide_masters[0]
    resolve = lint_deck._theme_resolver(master)       # the skill's own theme reader
    usage = {}
    for slide in prs.slides:
        for el in slide._element.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr"):
            v = norm_hex(el.get("val"))
            if v:
                usage[v] = usage.get(v, 0) + 1
    for slot in _THEME_SLOTS:
        h = norm_hex(resolve(slot))
        if not h:
            continue
        guess = ("primary" if slot == "accent1" else "accent" if slot == "accent2"
                 else "neutral" if slot[:2] in ("dk", "lt") else None)
        colours.append({"hex": h, "source": "{} theme {}".format(name, slot), "role_guess": guess,
                        "weight": 1.0 + usage.get(h, 0), "kind": "theme"})
    themed = {c["hex"] for c in colours}
    for h, n in sorted(usage.items(), key=lambda t: -t[1])[:8]:
        if h not in themed and n >= 3:
            colours.append({"hex": h, "source": "{} slides (used {}x)".format(name, n),
                            "weight": float(n), "kind": "theme"})
    th = cfr._theme_of(master)                       # the skill's own theme-font reader
    for (scheme, slot), face in th.items():
        if slot == "latin":
            fonts.append({"name": face, "source": "{} theme {}Font".format(name, scheme),
                          "role_guess": "heading" if scheme == "major" else "body"})
        elif slot == "ea" or slot in ("script:Hans", "script:Hant", "script:Jpan", "script:Hang"):
            fonts.append({"name": face, "source": "{} theme {}Font {}".format(name, scheme, slot),
                          "role_guess": "cjk"})
    return colours, fonts


# ════════════════════════════════════════════════════════════════════════ extract

_SOURCE_RANK = {"user": 0, "guide": 1, "theme": 2, "logo": 3}


def _merge_colours(cols):
    """Colours within dE 2.5 are ONE colour: keep the most authoritative hex, join the sources."""
    out = []
    for c in sorted(cols, key=lambda c: (_SOURCE_RANK.get(c.get("kind"), 9), -c.get("weight", 0))):
        for o in out:
            if de(o["hex"], c["hex"]) < 2.5:
                o["sources"].append(c["source"])
                o["weight"] = round(o["weight"] + c.get("weight", 0), 3)
                o["role_guess"] = o.get("role_guess") or c.get("role_guess")
                if c.get("label") and not o.get("label"):
                    o["label"] = c["label"]
                break
        else:
            out.append({"hex": c["hex"], "sources": [c["source"]], "weight": c.get("weight", 0),
                        "role_guess": c.get("role_guess"), "label": c.get("label")})
    for o in out:
        o["source"] = "; ".join(dict.fromkeys(o.pop("sources")))
    return out


def _guess_roles(cols):
    """Fill role guesses nobody's label gave: the heaviest chromatic colour is the primary."""
    chromatic = sorted((c for c in cols if chroma(rgb_of(c["hex"])) > 12),
                       key=lambda c: -c["weight"])
    if not any(c.get("role_guess") == "primary" for c in cols) and chromatic:
        chromatic[0]["role_guess"] = "primary"
    for c in cols:
        if not c.get("role_guess"):
            L = lab(rgb_of(c["hex"]))[0]
            # a near-black or near-white is a ground/ink even with a tint in it (#1F1235 "Night")
            c["role_guess"] = ("neutral" if chroma(rgb_of(c["hex"])) <= 12 or L < 20 or L > 95
                               else "accent")
    return cols


def _font_guesses(fonts):
    out = {"heading": None, "body": None, "cjk": None, "mono": None}
    for f in fonts:                                  # labelled roles first
        r = f.get("role_guess")
        if r in out and out[r] is None:
            out[r] = {"name": f["name"], "source": f["source"]}
    unlabelled = [f for f in fonts if not f.get("role_guess")]
    for f in unlabelled:
        try:
            sys.path.insert(0, str(HERE))
            import deckkit
            is_cjk = deckkit._face_covers(f["name"], "中文") is True
        except Exception:
            is_cjk = False
        slot = "cjk" if is_cjk and out["cjk"] is None else (
            "heading" if out["heading"] is None else "body" if out["body"] is None else None)
        if slot:
            out[slot] = {"name": f["name"], "source": f["source"]}
    return out


def cmd_extract(a):
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    assets = out.parent / ASSETS
    cols, fonts, logos, notes, undecided, sources = [], [], [], [], [], []
    for f in a.files:
        p = Path(f)
        if not p.is_file():
            raise Unreadable("{} does not exist or is not a file.".format(p))
        ext = p.suffix.lower()
        sources.append({"file": str(p.resolve()), "sha256": _sha(p)})
        if ext == ".svg":
            c, logo, raster, n, u = from_svg(p, assets)
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, assets / p.name)
            logo["file"] = _rel(assets / p.name, out.parent)
            logo["raster"] = _rel(raster, out.parent)
            cols += c
            logos.append(logo)
            notes += n
            undecided += u
        elif ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            c, logo = from_raster(p)
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, assets / p.name)
            logo["file"] = logo["raster"] = _rel(assets / p.name, out.parent)
            cols += c
            logos.append(logo)
        elif ext == ".pdf":
            c, fo, u = from_pdf(p)
            if not c:
                notes.append("{}: no hex/RGB codes in its text.".format(p.name))
            cols += c
            fonts += fo
            undecided += u
        elif ext in (".pptx", ".potx"):
            c, fo = from_pptx(p)
            cols += c
            fonts += fo
        else:
            raise Unreadable("{}: unsupported file type {!r}. Supported: .svg .png .jpg .pdf .pptx "
                             ".potx — or pass values with --hex / --font.".format(p, ext))
    for v in a.hex or []:
        h = norm_hex(v)
        if not h:
            print("brand_kit: --hex {!r} is not a #RRGGBB colour.".format(v), file=sys.stderr)
            return 1
        cols.append({"hex": h, "source": "user (--hex)", "weight": 1.0, "kind": "user"})
    for v in a.font or []:
        role, _, name = v.partition("=") if "=" in v else (None, "", v)
        role = (role or "").strip().lower() or None
        if role and role not in ("heading", "body", "cjk", "mono"):
            print("brand_kit: --font {!r}: the role before '=' must be heading|body|cjk|mono."
                  .format(v), file=sys.stderr)
            return 1
        fonts.insert(0, {"name": name.strip(), "source": "user (--font)", "role_guess": role})
    if not cols and not fonts:
        print("brand_kit: nothing to build a brand from. {}".format(" ".join(notes)), file=sys.stderr)
        print("  The files you gave carry no hex/RGB codes, no theme and no logo. Pass the colours "
              "the user typed with --hex #RRGGBB (and faces with --font \"Name\"), or add a logo "
              "or an on-brand .pptx.", file=sys.stderr)
        return 1
    merged = _guess_roles(_merge_colours(cols))
    fg = _font_guesses(fonts)
    if not fg["heading"] and fg["body"]:
        fg["heading"] = dict(fg["body"], source=fg["body"]["source"] + " (same as body)")
    if not fg["body"] and fg["heading"]:
        fg["body"] = dict(fg["heading"], source=fg["heading"]["source"] + " (same as heading)")
    for lg in logos:
        lg["marks"] = [{"hex": h, "share": round(s, 3)} for h, s in lg["marks"]]
    data = {"schema": SCHEMA, "name": a.name, "status": "draft", "created": _now(),
            "sources": sources,
            "colors": [dict(c, role=None) for c in merged],
            "fonts": dict(fg, candidates=[{"name": f["name"], "source": f["source"],
                                           "role_guess": f.get("role_guess")} for f in fonts]),
            "logos": logos, "undecided": undecided, "notes": notes}
    save_brand(out, data)
    print("brand kit DRAFT written: {}".format(out))
    print("  {} colour(s), {} face candidate(s), {} logo(s) from {} file(s){}".format(
        len(merged), len(fonts), len(logos), len(a.files),
        " + typed values" if (a.hex or a.font) else ""))
    for n in notes:
        print("  note: " + n)
    for u in undecided:
        print("  UNDECIDED: " + u)
    for role in ("heading", "body", "cjk"):
        if not fg[role]:
            print("  could not decide a {} face from these files — confirm takes --{}-font "
                  "if the user names one{}.".format(role, role, " (a CJK deck only)" if role == "cjk" else ""))
    print("NEXT: {} review {}".format(_SELF, shlex.quote(str(out))))
    return 0


# ════════════════════════════════════════════════════════════════════════ review

def _fmt_font(f):
    if not f:
        return "—"
    s = f["name"]
    if f.get("fallback"):
        s += " (not installed -> {})".format(f["fallback"])
    return "{}  [{}]".format(s, f.get("source", "?"))


def _confirm_cmd(path, b):
    parts = [_SELF, "confirm", shlex.quote(str(path))]
    for c in b["colors"]:
        r = c.get("role") or c.get("role_guess")
        if r in ROLES:
            parts += ["--" + r, shlex.quote(c["hex"])]   # '#' unquoted starts a shell COMMENT
    for role in ("heading", "body", "cjk", "mono"):
        f = b["fonts"].get(role)
        if f and f.get("name"):
            parts += ["--{}-font".format(role), shlex.quote(f["name"])]
    return " ".join(parts)


def cmd_review(a):
    b = load_brand(a.brand)
    print("Brand kit{} — {} ({})".format(" " + b["name"] if b.get("name") else "", a.brand,
                                          b["status"].upper()))
    print("  {:<3} {:<8} {:<10} {:>6}  {}".format("#", "hex", "role" if b["status"] == "confirmed"
                                                 else "guess", "weight", "source · label"))
    for i, c in enumerate(b["colors"], 1):
        r = c.get("role") or c.get("role_guess") or "?"
        print("  {:<3} {:<8} {:<10} {:>6}  {}{}".format(i, c["hex"], r, c.get("weight", ""),
                                                      c["source"], (" · " + c["label"]) if c.get("label") else ""))
    for role in ("heading", "body", "cjk", "mono"):
        print("  {:<8} {}".format(role, _fmt_font(b["fonts"].get(role))))
    for lg in b.get("logos", []):
        print("  logo     {} -> place {}  reads on: {}{}".format(
            lg["file"], lg["raster"], lg["ground"],
            "  (on its own {} plate)".format(lg["plate"]) if lg.get("plate") else ""))
    for u in b.get("undecided", []):
        print("  UNDECIDED: " + u)
    cmd = _confirm_cmd(a.brand, b)
    if b["status"] == "confirmed":
        print("Already CONFIRMED (the roles above are the reviewed ones). To change them, run "
              "confirm again: " + cmd)
        print("NEXT: {} style {}".format(_SELF, shlex.quote(str(a.brand))))
        return 0
    if a.auto:
        prim = next((c for c in b["colors"] if (c.get("role") or c.get("role_guess")) == "primary"), None)
        alt = next((c for c in b["colors"] if c is not prim and chroma(rgb_of(c["hex"])) > 12), None)
        files = ", ".join(Path(s["file"]).name for s in b.get("sources", [])) or "typed values"
        row = {"axis": "template", "source": "from-material",
               "value": "brand kit from {}: primary {}".format(files, prim["hex"] if prim else "—"),
               "basis": "the user supplied {}; primary {} is {}".format(
                   files, prim["hex"] if prim else "—",
                   ("labelled " + repr(prim["label"])) if prim and prim.get("label") else
                   "the heaviest hue in " + (prim["source"] if prim else "nothing")),
               "alternative": ("{} as primary instead — it carries less weight in the files ({} vs "
                               "{})".format(alt["hex"], alt.get("weight"), prim.get("weight"))
                               if alt and prim else
                               "a stock preset instead of the brand — lost because the user "
                               "supplied brand files")}
        print("AUTO MODE — record this delegated pick in interview.picks (it says who chose the "
              "roles), then confirm the guesses:")
        print(json.dumps(row, ensure_ascii=False))
        print("NEXT: " + cmd)
    else:
        print("Show this table to the user and ask which colour is primary / accent / neutral and "
              "which faces to use; drop anything they reject. Then run confirm with THEIR answer "
              "(pre-filled here with the guesses):")
        print("NEXT: " + cmd)
    return 0


# ════════════════════════════════════════════════════════════════════════ confirm

def _plat():
    return "mac" if sys.platform == "darwin" else ("win" if sys.platform.startswith("win") else "linux")


def _font_status(name, lang=None):
    """{installed, covers?, fallback?, why?} for one face. Asks deckkit; never guesses."""
    sys.path.insert(0, str(HERE))
    import deckkit as dk
    st = {"installed": not dk._font_substituted(name)}
    if lang:
        st["covers"] = dk._face_covers(name, _GLYPHS[lang]) if st["installed"] else None
    return st


def _cjk_fallback(lang, serif=False):
    sys.path.insert(0, str(HERE))
    import deckkit as dk
    scr = LANGS[lang]
    cands = ([dk.EA_LINUX[scr]] if _plat() == "linux" else
             [dk.EA_FACES[scr]["serif" if serif else "sans"][_plat()],
              dk.EA_FACES[scr]["sans" if serif else "serif"][_plat()]])
    cands += [dk.EA_LINUX[scr]]
    for c in dict.fromkeys(cands):
        if not dk._font_substituted(c) and dk._face_covers(c, _GLYPHS[lang]):
            return c
    return None


def _latin_fallback(slot):
    sys.path.insert(0, str(HERE))
    import deckkit as dk
    key = "darwin" if sys.platform == "darwin" else "win32" if sys.platform.startswith("win") else "linux"
    face = dk._PLATFORM_FONTS[key]["MONO" if slot == "mono" else "FONT"]
    if not dk._font_substituted(face):
        return face
    # 🔴 the platform default is not guaranteed either — DejaVu Sans does not resolve on this repo's
    # own Ubuntu CI. Ask the font machinery for ANY face that resolves rather than failing a brand
    # whose only problem is a missing default.
    import check_fonts_resolve as cfr
    return cfr.an_installed_face()


def digest(b):
    """What a person reviewed: roles, faces, logos, policy. An edit after confirm changes it."""
    core = {"colors": sorted((c["hex"], c.get("role")) for c in b["colors"] if c.get("role")),
            "fonts": {k: (v or {}).get("name") for k, v in b["fonts"].items() if k != "candidates"},
            "fallbacks": {k: (v or {}).get("fallback") for k, v in b["fonts"].items()
                          if k != "candidates"},
            "logos": [(lg.get("raster"), lg.get("ground")) for lg in b.get("logos", [])],
            "policy": (b.get("confirmed") or {}).get("neutral_policy"),
            "lang": (b.get("confirmed") or {}).get("lang")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def cmd_confirm(a):
    b = load_brand(a.brand)
    if not a.primary:
        print("brand_kit confirm: --primary #RRGGBB is required — the one colour the deck is "
              "recognisably the brand's. Run `{} review {}` to see the candidates.".format(
                  _SELF, a.brand), file=sys.stderr)
        return 1
    if a.lang and a.lang not in LANGS:
        print("brand_kit confirm: --lang must be one of {} (or omit it for a Latin-only deck)."
              .format(", ".join(LANGS)), file=sys.stderr)
        return 1
    want = [("primary", a.primary)] + [("accent", h) for h in a.accent or []] + \
           [("secondary", h) for h in a.secondary or []] + [("neutral", h) for h in a.neutral or []]
    by_hex = {c["hex"]: c for c in b["colors"]}
    kept = []
    for role, v in want:
        h = norm_hex(v)
        if not h:
            print("brand_kit confirm: {} {!r} is not a #RRGGBB colour.".format(role, v), file=sys.stderr)
            return 1
        c = by_hex.get(h)
        if c is None:                               # typed at confirm: the user's value, said so
            c = {"hex": h, "source": "user (confirm --{})".format(role), "weight": 1.0,
                 "role_guess": None}
            print("  {} {} is not in the draft — recorded as a USER value (source: confirm).".format(role, h))
        c = dict(c, role=role)
        if any(k["hex"] == h for k in kept):
            print("brand_kit confirm: {} is given two roles — pick one.".format(h), file=sys.stderr)
            return 1
        kept.append(c)
    dropped = [c["hex"] for c in b["colors"] if c["hex"] not in {k["hex"] for k in kept}]
    b["colors"] = kept
    # faces
    fonts = b["fonts"]
    for role in ("heading", "body", "cjk", "mono"):
        v = getattr(a, role + "_font")
        if v:
            fonts[role] = {"name": v, "source": "user (confirm --{}-font)".format(role)
                           if not (fonts.get(role) and fonts[role].get("name") == v)
                           else fonts[role]["source"]}
    if fonts.get("body") and not fonts.get("heading"):
        fonts["heading"] = dict(fonts["body"], source=fonts["body"]["source"] + " (same as body)")
    if fonts.get("heading") and not fonts.get("body"):
        fonts["body"] = dict(fonts["heading"], source=fonts["heading"]["source"] + " (same as heading)")
    problems = []
    for role in ("heading", "body", "mono"):
        f = fonts.get(role)
        if not f:
            continue
        f.update(_font_status(f["name"]))
        f.pop("fallback", None)
        if not f["installed"]:
            fb = _latin_fallback(role)
            if not fb:
                problems.append("{} face {!r} is not installed and no platform fallback is either — "
                                "install it, or confirm with --{}-font <an installed face>."
                                .format(role, f["name"], role))
            else:
                f["fallback"] = fb
                f["why"] = "not installed on this machine — the deck draws in {}".format(fb)
    if a.lang:
        f = fonts.get("cjk")
        if f:
            f.update(_font_status(f["name"], a.lang))
            f.pop("fallback", None)
        if not f or not f.get("installed") or f.get("covers") is False:
            serif = bool(f and re.search(r"song|ming|serif|kai|mincho|myungjo", f["name"], re.I))
            fb = _cjk_fallback(a.lang, serif)
            if not fb:
                problems.append("no installed face covers {} text — install one (Noto Sans CJK on "
                                "Linux; the system CJK faces on macOS/Windows) and re-run confirm."
                                .format(a.lang))
            else:
                if not f:
                    f = fonts["cjk"] = {"name": None, "source": "brand names no CJK face"}
                f["fallback"] = fb
                f["why"] = ("brand names no CJK face" if not f.get("name") else
                            "not installed here" if not f.get("installed") else
                            "lacks glyphs for {} text".format(a.lang))
    if problems:
        for p in problems:
            print("brand_kit confirm: " + p, file=sys.stderr)
        return 1
    if (fonts.get("cjk") or {}).get("name") and not a.lang:
        print("  NOTE: a CJK face ({}) is set but --lang is not — its glyphs are NOT checked, and "
              "`check` will refuse CJK text until you re-run confirm with --lang zh-Hans|zh-Hant|ja|ko."
              .format(fonts["cjk"]["name"]))
    # grounds, ink and contrast pairs
    policy = "declared" if a.strict_neutrals else "achromatic"
    neutrals = [c["hex"] for c in kept if c["role"] == "neutral"]
    # The brand's OWN neutrals ground the deck first (its paper, its night); white / black only
    # when it declares none light / dark enough and the achromatic policy allows them.
    lt = [h for h in neutrals if contrast(h, "#000000") >= 10]
    dk_ = [h for h in neutrals if contrast(h, "#FFFFFF") >= 10]
    light = (max(lt, key=lambda h: contrast(h, "#000000")) if lt else
             "#FFFFFF" if policy == "achromatic" else None)
    dark = (min(dk_, key=lambda h: contrast(h, "#000000")) if dk_ else
            "#000000" if policy == "achromatic" else None)
    pairs, twins = [], {}
    for c in kept:
        for gname, g in (("light", light), ("dark", dark)):
            if not g or g == c["hex"]:
                continue
            r = contrast(c["hex"], g)
            pairs.append({"fg": c["hex"], "bg": g, "ground": gname, "ratio": round(r, 2),
                          "use": "body text" if r >= 4.5 else "large text / marks" if r >= 3 else "fill only"})
            if gname == "light" and c["role"] in ("primary", "accent", "secondary") and r < 4.5:
                sys.path.insert(0, str(HERE))
                import palette_audit as pa
                t = pa.darken_to(c["hex"][1:], g[1:], 4.5)
                if t:
                    twins[c["hex"]] = {"hex": "#" + t, "source": "derived: shade of {} to 4.5:1 on {}"
                                       .format(c["hex"], g)}
    ink = None
    if light:
        cands = [c["hex"] for c in kept if contrast(c["hex"], light) >= 7]
        if cands:
            ink = {"hex": min(cands, key=lambda h: contrast(h, "#000000")), "source": "brand colour"}
        else:
            sys.path.insert(0, str(HERE))
            import palette_audit as pa
            t = pa.darken_to(a.primary.lstrip("#").upper()[-6:], light[1:], 7.0)
            if t:
                ink = {"hex": "#" + t, "source": "derived: shade of the primary to 7:1 on {}".format(light)}
    b["confirmed"] = {"at": _now(), "neutral_policy": policy, "lang": a.lang,
                      "ground_light": light, "ground_dark": dark, "ink": ink,
                      "text_twins": twins, "pairs": pairs, "dropped": dropped}
    b["status"] = "confirmed"
    b["confirmed"]["digest"] = digest(b)
    save_brand(a.brand, b)
    print("brand kit CONFIRMED: {}".format(a.brand))
    for c in kept:
        print("  {:<9} {}  [{}]".format(c["role"], c["hex"], c["source"]))
    for role in ("heading", "body", "cjk", "mono"):
        f = fonts.get(role)
        if f:
            print("  {:<9} {}".format(role, _fmt_font(f)))
            if f.get("fallback"):
                print("            ^ FALLBACK {} — {}".format(f["fallback"], f.get("why")))
    if not fonts.get("body"):
        print("  no face is part of this brand — check will test colour only, and say so")
    print("  grounds: light {} · dark {} · ink {}".format(light or "—", dark or "—",
                                                       (ink or {}).get("hex", "—")))
    for c in kept:
        if c["role"] == "neutral":
            continue
        row = ["{} on {} {}:1 ({})".format(gname, p["bg"], p["ratio"], p["use"])
               for gname in ("light", "dark") for p in pairs
               if p["fg"] == c["hex"] and p["ground"] == gname]
        tw = twins.get(c["hex"])
        print("  {} {}{}".format(c["hex"], " · ".join(row),
                                 "  -> as TEXT on light uses the shade {}".format(tw["hex"]) if tw else ""))
    if dropped:
        print("  dropped (not named at confirm): " + ", ".join(dropped))
    print("  neutrals: " + ("declared only (--strict-neutrals)" if policy == "declared" else
                            "declared + any achromatic grey"))
    print("NEXT: {} style {}".format(_SELF, shlex.quote(str(a.brand))))
    return 0


def _require_confirmed(b, path):
    if b.get("status") != "confirmed":
        raise Refused("{} is a DRAFT — a person has not confirmed its roles. Run `{} review {}` "
                      "and then `confirm`.".format(path, _SELF, path))
    if (b.get("confirmed") or {}).get("digest") != digest(b):
        raise Refused("{} was edited after confirm — its roles/faces are no longer what was "
                      "reviewed. Re-run `{} confirm {} --primary …` to sign the edit.".format(
                          path, _SELF, path))


class Refused(Exception):
    """Exit 1 with the reason (a draft, an edited kit, a bad name)."""


# ════════════════════════════════════════════════════════════════════════ style

def effective_fonts(b):
    """{slot: face the deck should SET} — the brand face when installed, else its fallback."""
    out = {}
    for role in ("heading", "body", "cjk", "mono"):
        f = b["fonts"].get(role) or {}
        out[role] = f.get("fallback") or f.get("name") or None
    return out


def allowed_fonts(b):
    s = set()
    for role in ("heading", "body", "cjk", "mono"):
        f = b["fonts"].get(role) or {}
        for k in ("name", "fallback"):
            if f.get(k):
                s.add(f[k].lower())
    return s


def allowed_fonts_cased(b):
    out = []
    for role in ("heading", "body", "cjk", "mono"):
        f = b["fonts"].get(role) or {}
        for k in ("name", "fallback"):
            if f.get(k) and f[k] not in out:
                out.append(f[k])
    return out


def cmd_style(a):
    b = load_brand(a.brand)
    _require_confirmed(b, a.brand)
    cf = b["confirmed"]
    base = Path(a.brand).resolve().parent
    out = Path(a.out) if a.out else base / "brand_style.py"
    cols = {r: [c["hex"] for c in b["colors"] if c["role"] == r] for r in ROLES}
    prim = cols["primary"][0]
    if a.ground == "dark":
        g = cf.get("ground_dark") or (prim if contrast(prim, "#FFFFFF") >= 10 else None)
        if not g:
            print("brand_kit style: no dark brand colour to ground on — confirm a dark --neutral, "
                  "or use --ground light.", file=sys.stderr)
            return 1
        ink = cf.get("ground_light") or "#FFFFFF"
    else:
        g = cf.get("ground_light")
        if not g:
            print("brand_kit style: no light ground — confirm a light --neutral (or drop "
                  "--strict-neutrals so white is allowed), or use --ground dark.", file=sys.stderr)
            return 1
        ink = (cf.get("ink") or {}).get("hex")
        if not ink:
            print("brand_kit style: no brand colour reads as body text on {}. Confirm a dark "
                  "--neutral.".format(g), file=sys.stderr)
            return 1
    accents = cols["primary"] + cols["accent"] + cols["secondary"]
    twins = cf.get("text_twins") or {}
    acc_text = twins.get(prim, {}).get("hex", prim) if a.ground != "dark" else prim
    grey = mix(ink, g, 0.22)
    mute = mix(ink, g, 0.42)
    t = 0.42
    while contrast(mute, g) < 4.5 and t > 0:
        t = round(t - 0.04, 2)
        mute = mix(ink, g, max(t, 0))
    line = mix(ink, g, 0.82)
    tint = mix(prim, g, 0.90)
    fonts = effective_fonts(b)
    body = fonts["body"]
    logo = None
    for lg in b.get("logos", []):
        ok = lg["ground"] in ("both", "dark" if a.ground == "dark" else "light")
        if ok and lg.get("raster"):
            logo = lg
            break
    if logo:
        rel_logo = os.path.relpath(base / logo["raster"], out.parent)
    lines = [
        '"""brand_style.py — GENERATED by brand_kit.py style from {} (confirmed {}).'.format(
            Path(a.brand).name, cf.get("at")),
        "",
        "Do not hand-edit the colours: change the brand with `brand_kit.py confirm` and re-run",
        "`brand_kit.py style`. Same shape as presets.preset() (bg/ink/muted/accents/font/display/mono/",
        "ea/ea_display) and the style.py names (INK/ACCENT/GREY/MUTE/LINE/WHITE/FONT).",
        "",
        "    import brand_style as bs",
        "    B = bs.apply()              # palette + faces + ground, like presets.apply()",
        '"""',
        "import sys",
        "sys.path.insert(0, {!r})".format(str(HERE)),
        "import deckkit",
        "from pptx.dml.color import RGBColor",
        "",
        "",
        "def C(h):",
        "    return RGBColor.from_string(h.lstrip('#'))",
        "",
        "",
        "BRAND_FILE = {!r}".format(str(Path(a.brand).resolve())),
        "LANG = {!r}".format(cf.get("lang")),
        "GROUND = C({!r})        # {} ground".format(g, a.ground),
        "INK = C({!r})           # titles / strong text  [{}]".format(
            ink, (cf.get("ink") or {}).get("source", "brand ground") if a.ground != "dark" else "light ground"),
        "ACCENT = C({!r})        # primary — fills, marks".format(prim),
        "ACCENT_TEXT = C({!r})   # primary as TEXT (>= 4.5:1 on the ground)".format(acc_text),
        "ACCENTS = [{}]".format(", ".join("C({!r})".format(h) for h in accents)),
        "NEUTRALS = [{}]".format(", ".join("C({!r})".format(h) for h in cols["neutral"])),
        "GREY = C({!r})          # body — a tint of INK toward the ground".format(grey),
        "MUTE = C({!r})          # captions / footer (>= 4.5:1)".format(mute),
        "LINE = C({!r})          # hairlines".format(line),
        "TINT = C({!r})          # pale panel — a tint of the primary".format(tint),
        "WHITE = C({!r})         # the light ground (style.py's WHITE)".format(
            cf.get("ground_light") or "#FFFFFF"),
        "FONT = {!r}".format(body),
        "DISPLAY = {!r}".format(fonts["heading"] or body),
        "MONO = {!r}".format(fonts["mono"]),
        "EAFONT = {!r}".format(fonts["cjk"]),
        "EADISPLAY = {!r}".format(fonts["cjk"]),
        "BRAND = {",
        "    'name': {!r},".format(b.get("name")),
        "    'bg': GROUND, 'ink': INK, 'muted': MUTE, 'accents': ACCENTS,",
        "    'font': FONT, 'display': DISPLAY, 'mono': MONO, 'ea': EAFONT, 'ea_display': EADISPLAY,",
        "    # absolute at import, so a build run from any folder finds it",
        "    'logo': {}, 'logo_ground': {!r},".format(
            "str(__import__('pathlib').Path(__file__).resolve().parent / {!r})".format(rel_logo)
            if logo else None, logo["ground"] if logo else None),
        "}",
        "",
        "",
        "def apply():",
        "    \"\"\"Re-theme deckkit to the brand (colour defaults of every component, faces, ground).\"\"\"",
        "    acc = list(ACCENTS)",
        "    kw = dict(deep=INK, slate=GREY, mute=MUTE, accents=acc, magenta=acc[1 % len(acc)],",
        "              blue=acc[0], teal=acc[2 % len(acc)], tint=TINT)",
        "    if FONT: kw['font'] = FONT",
        "    if DISPLAY: kw['display'] = DISPLAY",
        "    if MONO: kw['mono'] = MONO",
        "    if EAFONT: kw.update(eafont=EAFONT, eadisplay=EADISPLAY)",
        "    deckkit.set_palette(**kw)",
        "    _extra = {'LIGHT': TINT, 'GOLD': acc[1 % len(acc)], 'STEEL': GREY, 'VIOLET': acc[2 % len(acc)],",
        "              'GREEN': acc[0]}",
        "    _remap = {}",
        "    for name, new in _extra.items():          # defaults set_palette does not own",
        "        old = getattr(deckkit, name, None)",
        "        if old is not None:",
        "            _remap[id(old)] = new",
        "            setattr(deckkit, name, new)",
        "    import types",
        "    for obj in list(vars(deckkit).values()):",
        "        if isinstance(obj, types.FunctionType):",
        "            if obj.__kwdefaults__:",
        "                for k, v in list(obj.__kwdefaults__.items()):",
        "                    if id(v) in _remap:",
        "                        obj.__kwdefaults__[k] = _remap[id(v)]",
        "            if obj.__defaults__:",
        "                obj.__defaults__ = tuple(_remap.get(id(v), v) for v in obj.__defaults__)",
        "    deckkit.set_ground(None if {!r} == '#FFFFFF' else GROUND)".format(g),
        "    return BRAND",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print("brand style written: {}".format(out))
    print("  ground {} · ink {} · accents {} · faces {} / {}{}".format(
        g, ink, " ".join(accents), fonts["heading"] or "—", body or "—",
        " / " + fonts["cjk"] if fonts["cjk"] else ""))
    if logo:
        print("  logo for this ground: {} ({})".format(rel_logo, logo["ground"]))
    elif b.get("logos"):
        print("  NOTE: no logo reads on a {} ground ({}); place one on a contrasting plate.".format(
            a.ground, ", ".join("{}: {}".format(lg["file"], lg["ground"]) for lg in b["logos"])))
    print("  In the build script, beside the deck:  import brand_style as bs;  B = bs.apply()  "
          "— then draw with bs.INK / bs.ACCENT / bs.ACCENTS / bs.GREY / bs.MUTE and place B['logo'].")
    print("NEXT: build the deck, then  {} check <deck.pptx> --brand {}".format(
        _SELF, shlex.quote(str(a.brand))))
    return 0


# ════════════════════════════════════════════════════════════════════════ check

_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


# A ▲/▼ delta's green/red is a FUNCTIONAL signal every reader decodes, not a brand choice. Allowed
# only on delta-shaped text, only in deckkit's own good/bad colours (read from deckkit, not copied),
# and counted in the report. Measured: scorecard(delta="+12%") put #15803D on every fixture deck —
# 25.8 dE from a blue brand — so without this every on-brand deck with a KPI tile failed.
_DELTA_TEXT = re.compile(r"^\s*[▲▼△▽↑↓+\-−]\s*\d")


def _status_colours():
    sys.path.insert(0, str(HERE))
    try:
        import deckkit as dk
        return {norm_hex(str(getattr(dk, n))) for n in ("_GOOD", "_BAD", "_GOOD_D", "_BAD_D")
                if getattr(dk, n, None) is not None}
    except Exception:
        return set()


class Palette:
    """Is this hex on-brand? Brand colours, their mixes with white/black/neutrals, and the policy."""

    def __init__(self, b, tol=TOLERANCE_DE):
        import numpy as np
        self.tol = tol
        cf = b.get("confirmed") or {}
        self.achromatic = cf.get("neutral_policy", "achromatic") == "achromatic"
        cols = [c["hex"] for c in b["colors"]]
        cols += [t["hex"] for t in (cf.get("text_twins") or {}).values()]
        if (cf.get("ink") or {}).get("hex"):
            cols.append(cf["ink"]["hex"])
        neutrals = [c["hex"] for c in b["colors"] if c["role"] == "neutral"]
        anchors = ["#FFFFFF", "#000000"] + neutrals
        pts = []
        for c in dict.fromkeys(cols):
            for an in anchors:
                for i in range(51):
                    pts.append(lab(rgb_of(mix(c, an, i / 50.0))))
        self.labs = np.array(pts)
        self.cache = {}

    def distance(self, h):
        if h not in self.cache:
            self.cache[h] = float(de2000(lab(rgb_of(h)), self.labs).min())
        return self.cache[h]

    def ok(self, h):
        if self.achromatic and chroma(rgb_of(h)) <= ACHROMATIC_C:
            return True
        return self.distance(h) <= self.tol


def _colour_of(el, resolve):
    """hex | 'UNRESOLVED' | None for a fill-ish element (solidFill / gs / …)."""
    srgb = el.find(_A + "srgbClr")
    if srgb is not None and srgb.get("val"):
        return norm_hex(srgb.get("val"))
    sch = el.find(_A + "schemeClr")
    if sch is not None:
        if len(sch):                                    # a transformed theme colour
            return "UNRESOLVED"
        v = resolve(sch.get("val")) if resolve else None
        return norm_hex(v) if v else "UNRESOLVED"
    sysc = el.find(_A + "sysClr")
    if sysc is not None and sysc.get("lastClr"):
        return norm_hex(sysc.get("lastClr"))
    return None


def _spPr_uses(spPr, resolve, kind_fill="fill"):
    out = []
    if spPr is None:
        return out
    for child in spPr:
        if child.tag == _A + "solidFill":
            out.append((kind_fill, _colour_of(child, resolve)))
        elif child.tag == _A + "gradFill":
            for gs in child.iter(_A + "gs"):
                out.append((kind_fill + " (gradient stop)", _colour_of(gs, resolve)))
        elif child.tag == _A + "ln":
            sf = child.find(_A + "solidFill")
            if sf is not None:
                out.append(("line", _colour_of(sf, resolve)))
    return [(k, v) for k, v in out if v]


def _shape_name(el):
    for tag in (_P + "nvSpPr", _P + "nvCxnSpPr", _P + "nvGrpSpPr", _P + "nvGraphicFramePr", _P + "nvPicPr"):
        nv = el.find(tag)
        if nv is not None:
            c = nv.find(_P + "cNvPr")
            if c is not None:
                return c.get("name") or "?"
    return "?"


def _text_uses(txBody, resolve):
    out = []
    if txBody is None:
        return out
    for r in txBody.iter(_A + "r"):
        t = r.find(_A + "t")
        txt = (t.text or "") if t is not None else ""
        if not txt.strip():
            continue
        rPr = r.find(_A + "rPr")
        sf = rPr.find(_A + "solidFill") if rPr is not None else None
        if sf is not None:
            v = _colour_of(sf, resolve)
            if v:
                out.append(("text", v, txt.strip()[:40]))
    return out


def _walk(el, slide, resolve, uses, chart_parts, depth=0):
    for sh in el:
        tag = sh.tag
        if tag == _P + "pic":
            continue                                    # a picture carries every hue: ignored
        name = _shape_name(sh)
        if tag == _P + "grpSp":
            for k, v in _spPr_uses(sh.find(_P + "grpSpPr"), resolve):
                uses.append((name, k, v, ""))
            _walk(sh, slide, resolve, uses, chart_parts, depth + 1)
        elif tag in (_P + "sp", _P + "cxnSp"):
            for k, v in _spPr_uses(sh.find(_P + "spPr"), resolve):
                uses.append((name, k, v, ""))
            for k, v, t in _text_uses(sh.find(_P + "txBody"), resolve):
                uses.append((name, k, v, t))
        elif tag == _P + "graphicFrame":
            for tc in sh.iter(_A + "tc"):
                tcPr = tc.find(_A + "tcPr")
                if tcPr is not None:
                    for child in tcPr:
                        if child.tag == _A + "solidFill":
                            v = _colour_of(child, resolve)
                            if v:
                                uses.append((name, "table cell fill", v, ""))
                        elif child.tag in (_A + "lnL", _A + "lnR", _A + "lnT", _A + "lnB"):
                            sf = child.find(_A + "solidFill")
                            v = _colour_of(sf, resolve) if sf is not None else None
                            if v:
                                uses.append((name, "table border", v, ""))
                for k, v, t in _text_uses(tc.find(_A + "txBody"), resolve):
                    uses.append((name, "table text", v, t))
            ch = sh.find(".//" + _C + "chart")
            if ch is not None:
                rid = ch.get(_R + "id")
                part = chart_parts.get(rid)
                if part is not None:
                    _chart_uses(part, name, resolve, uses)


def _chart_uses(part, name, resolve, uses):
    from lxml import etree
    root = etree.fromstring(part.blob)
    for ser in root.iter(_C + "ser"):
        sp = ser.find(_C + "spPr")
        for k, v in _spPr_uses(sp, resolve, "chart series"):
            uses.append((name, k if k != "line" else "chart series line", v, ""))
        for dpt in ser.findall(_C + "dPt"):
            for k, v in _spPr_uses(dpt.find(_C + "spPr"), resolve, "chart data point"):
                uses.append((name, k, v, ""))
    # Axis text, gridlines and the plot frame are chart CHROME, not data: the design doc scopes the
    # chart check to SERIES. Measured: native_chart's own axis ink (#222A37) is 8.7 dE off a green
    # brand's ink ramp — flagging it would fail every on-brand deck that has a chart.


def _slide_bg(slide, resolve):
    bg = slide._element.find(_P + "cSld/" + _P + "bg/" + _P + "bgPr")
    if bg is None:
        return None
    sf = bg.find(_A + "solidFill")
    return _colour_of(sf, resolve) if sf is not None else None


def _thumb(img):
    from PIL import Image
    im = img.convert("RGBA").resize((24, 24), Image.BILINEAR)
    bgc = Image.new("RGBA", im.size, (128, 128, 128, 255))
    return _pixels(Image.alpha_composite(bgc, im).convert("RGB")), img.size


def _same_image(t1, t2):
    (p1, s1), (p2, s2) = t1, t2
    if abs(s1[0] / max(s1[1], 1) - s2[0] / max(s2[1], 1)) > 0.06 * (s1[0] / max(s1[1], 1)):
        return False
    d = sum(abs(a - b) for x, y in zip(p1, p2) for a, b in zip(x, y)) / (len(p1) * 3.0)
    return d <= LOGO_MATCH


def check_deck(pptx, b, base, multi_entity=False):
    """(findings, facts). findings = [{code, slide, shape, kind, value, why, sev}]."""
    sys.path.insert(0, str(HERE))
    import io
    from PIL import Image
    from pptx import Presentation
    import lint_deck
    import check_fonts_resolve as cfr
    try:
        prs = Presentation(str(pptx))
    except Exception as exc:
        raise Unreadable("{} is not a readable .pptx ({}).".format(pptx, exc.__class__.__name__))
    pal = Palette(b)
    allowed = allowed_fonts(b)
    # 🔴 deckkit sets DIGITS in a lining face when the brand face has old-style figures (the skill's
    # lining-figures rule). Measured: a Georgia brand's scorecard value "1,240" came back in Times
    # New Roman. That substitution is the skill's own deliberate rule, so it is allowed — on runs
    # with no letters at all, and only the face numeral_face() picks for a brand face.
    try:
        import deckkit as _dk
        numeral = {str(_dk.numeral_face(f)).lower() for f in allowed_fonts_cased(b)} - allowed
    except Exception:
        numeral = set()
    status = _status_colours()
    findings, facts = [], {"slides": len(prs.slides), "colour_uses": 0, "unresolved": 0,
                           "status_uses": 0, "numeral_runs": 0,
                           "fonts_checked": bool(allowed), "logo": "not checked"}
    seen = set()
    # logos
    logo_thumbs = []
    for lg in b.get("logos", []):
        rp = Path(base) / (lg.get("raster") or "")
        if rp.is_file():
            try:
                logo_thumbs.append((lg, _thumb(Image.open(rp))))
            except Exception:
                pass
    placed = []
    ea_ord = cfr._ea_ranges()
    themes = {}
    cjk_runs = 0
    for sno, slide in enumerate(prs.slides, 1):
        master = slide.slide_layout.slide_master
        key = str(master.part.partname)
        if key not in themes:
            themes[key] = (lint_deck._theme_resolver(master), cfr._theme_of(master))
        resolve, theme = themes[key]
        uses = []
        bgc = _slide_bg(slide, resolve)
        if bgc:
            uses.append(("(slide background)", "background", bgc, ""))
        chart_parts = {rid: rel.target_part for rid, rel in slide.part.rels.items()
                       if rel.reltype.endswith("/chart")}
        _walk(slide._element.find(_P + "cSld/" + _P + "spTree"), slide, resolve, uses, chart_parts)
        for name, kind, val, txt in uses:
            facts["colour_uses"] += 1
            if val == "UNRESOLVED":
                facts["unresolved"] += 1
                continue
            if pal.ok(val):
                continue
            if kind == "text" and val in status and _DELTA_TEXT.match(txt or ""):
                facts["status_uses"] += 1
                continue
            k = (sno, name, kind, val)
            if k in seen:
                continue
            seen.add(k)
            findings.append({"code": "COLOUR OFF BRAND", "sev": "block", "slide": sno, "shape": name,
                             "kind": kind, "value": val,
                             "why": "slide {} '{}': {} {}{} is not a brand colour or a tint/shade of "
                                    "one (nearest dE {:.1f} > {})".format(
                                        sno, name, kind, val, (" «" + txt + "»") if txt else "",
                                        pal.distance(val), pal.tol)})
        # faces
        for run in slide._element.iter(_A + "r", _A + "fld"):
            t = run.find(_A + "t")
            text = t.text if t is not None and t.text else ""
            if not text.strip():
                continue
            counts = cfr._by_slot(text, ea_ord)
            cjk_runs += 1 if counts["ea"] else 0
            if not allowed:
                continue
            rPr, chain, scheme = cfr._defaults_chain(run)
            script = cfr._script_of(rPr)
            for slot in ("latin", "ea"):
                if not counts[slot] or (slot == "latin" and not text.strip(" 　")):
                    continue
                if slot == "latin" and not re.search(r"[A-Za-z0-9]", text):
                    continue                              # punctuation-only latin is not a face choice
                face, how = cfr._face_for(chain, slot, scheme, theme, script)
                if face is None or face.lower() in allowed:
                    continue
                if face.lower() in numeral and not re.search(r"[^\W\d_]", text):
                    facts["numeral_runs"] += 1          # lining digits beside an old-style face
                    continue
                shape = run
                while shape is not None and shape.tag not in (_P + "sp", _P + "graphicFrame", _P + "cxnSp"):
                    shape = shape.getparent()
                name = _shape_name(shape) if shape is not None else "?"
                k = (sno, name, "font", face)
                if k in seen:
                    continue
                seen.add(k)
                findings.append({"code": "FONT OFF BRAND", "sev": "block", "slide": sno, "shape": name,
                                 "kind": "{} face{}".format(slot, " (via theme)" if how == "theme" else ""),
                                 "value": face,
                                 "why": "slide {} '{}': «{}» is set in {!r}, not a brand face ({})".format(
                                     sno, name, text.strip()[:40], face,
                                     ", ".join(sorted(allowed)))})
        # logo placements
        if logo_thumbs:
            for shp in slide.shapes:
                if shp.shape_type is None or "PICTURE" not in str(shp.shape_type):
                    continue
                try:
                    th = _thumb(Image.open(io.BytesIO(shp.image.blob)))
                except Exception:
                    continue
                for lg, lt in logo_thumbs:
                    if _same_image(th, lt):
                        placed.append((sno, shp, lg))
                        break
    if cjk_runs and allowed and not (b["fonts"].get("cjk") or {}).get("name") and \
            not (b["fonts"].get("cjk") or {}).get("fallback"):
        findings.append({"code": "NO CJK FACE", "sev": "block", "slide": None, "shape": None,
                         "kind": "font", "value": None,
                         "why": "{} run(s) carry CJK text and the brand records no CJK face — re-run "
                                "`{} confirm … --lang zh-Hans|zh-Hant|ja|ko` so one is chosen and checked."
                                .format(cjk_runs, _SELF)})
    elif cjk_runs and allowed and not (b.get("confirmed") or {}).get("lang"):
        findings.append({"code": "CJK UNCHECKED", "sev": "block", "slide": None, "shape": None,
                         "kind": "font", "value": None,
                         "why": "{} run(s) carry CJK text, but the brand was confirmed without --lang, so "
                                "its CJK face was never checked for the glyphs — re-run `{} confirm … "
                                "--lang zh-Hans|zh-Hant|ja|ko`.".format(cjk_runs, _SELF)})
    # the logo rule
    if multi_entity:
        facts["logo"] = "NOT CHECKED — a multi-entity deck (co-branded / partner logos)"
    elif not b.get("logos"):
        facts["logo"] = "NOT CHECKED — the brand records no logo"
    elif not logo_thumbs:
        facts["logo"] = "NOT CHECKED — the brand's logo raster is missing beside brand.json"
        findings.append({"code": "LOGO FILE MISSING", "sev": "block", "slide": None, "shape": None,
                         "kind": "logo", "value": None,
                         "why": "brand.json names logo(s) whose raster is not beside it: {} — re-run "
                                "`{} use` or extract again.".format(
                                    ", ".join(lg.get("raster") or "?" for lg in b["logos"]), _SELF)})
    elif not placed:
        findings.append({"code": "LOGO MISSING", "sev": "block", "slide": None, "shape": None,
                         "kind": "logo", "value": None,
                         "why": "a single-entity deck carries the brand's logo nowhere (looked for {}). "
                                "Place it (cover at least) with dk.picture(…, B['logo']), or check with "
                                "--multi-entity if this deck is co-branded.".format(
                                    ", ".join(lg["raster"] for lg in b["logos"] if lg.get("raster")))})
    else:
        facts["logo"] = "placed on slide(s) {}".format(sorted({s for s, _p, _l in placed}))
        for sno, shp, lg in placed:
            g = _ground_under(prs.slides[sno - 1], shp, themes)
            marks = lg.get("marks") or []
            if lg.get("plate") or not marks or g is None:
                continue
            tot = sum(m["share"] for m in marks) or 1.0
            share = sum(m["share"] for m in marks if contrast(m["hex"], g) >= 3.0) / tot
            if share < 0.6:
                findings.append({"code": "LOGO GROUND", "sev": "block", "slide": sno,
                                 "shape": shp.name, "kind": "logo", "value": g,
                                 "why": "slide {} '{}': the logo sits on {} where only {:.0%} of its "
                                        "mark clears 3:1 — use the variant for this ground, or a "
                                        "contrasting plate.".format(sno, shp.name, g, share)})
    return findings, facts


def _ground_under(slide, pic, themes):
    """The colour behind a picture: the last filled shape before it that covers its centre, else
    the slide background, else white (no background declared). None when unknowable (a picture)."""
    cx, cy = pic.left + pic.width / 2, pic.top + pic.height / 2
    master = slide.slide_layout.slide_master
    resolve = themes[str(master.part.partname)][0]
    ground = _slide_bg(slide, resolve) or "#FFFFFF"
    for shp in slide.shapes:
        if shp.shape_id == pic.shape_id:
            break
        try:
            if not (shp.left <= cx <= shp.left + shp.width and shp.top <= cy <= shp.top + shp.height):
                continue
        except TypeError:
            continue
        if shp.shape_type is not None and "PICTURE" in str(shp.shape_type):
            ground = None
            continue
        sp = shp._element.find(_P + "spPr")
        uses = [v for k, v in _spPr_uses(sp, resolve) if k.startswith("fill")]
        if uses and uses[0] != "UNRESOLVED":
            ground = uses[0]
    return ground


def cmd_check(a):
    b = load_brand(a.brand)
    _require_confirmed(b, a.brand)
    base = Path(a.brand).resolve().parent
    findings, facts = check_deck(a.deck, b, base, multi_entity=a.multi_entity)
    if a.json:
        print(json.dumps({"findings": findings, "facts": facts}, ensure_ascii=False, indent=1))
        return 1 if findings else 0
    print("[brand] {} slide(s), {} colour use(s) read{} · faces {} · logo {}".format(
        facts["slides"], facts["colour_uses"],
        " ({} theme colour(s) with transforms NOT CHECKED)".format(facts["unresolved"])
        if facts["unresolved"] else "",
        "checked" if facts["fonts_checked"] else "NOT CHECKED (the brand names no face)",
        facts["logo"]))
    for f in findings:
        print("  {}: {}".format(f["code"], f["why"]))
    if findings:
        print("{} finding(s). Fix each in the build script (draw with brand_style's colours/faces), "
              "rebuild, and re-run:".format(len(findings)))
        print("NEXT: {} check {} --brand {}".format(_SELF, shlex.quote(str(a.deck)),
                                                     shlex.quote(str(a.brand))))
        return 1
    print("[brand] on-brand: every colour is a brand colour, a tint/shade of one, or a neutral{}{}."
          .format(" · {} ▲/▼ delta(s) in deckkit's good/bad colours".format(facts["status_uses"])
                  if facts["status_uses"] else "",
                  " · {} digit run(s) in the lining face beside an old-style brand face".format(
                      facts["numeral_runs"]) if facts["numeral_runs"] else ""))
    deck_dir = Path(a.deck).resolve().parent
    rel = _rel(a.brand, deck_dir)
    obj = json.dumps({"file": rel})
    dg = "python3 " + shlex.quote(str(HERE / "deck_gates.py"))
    setc = "{} set {} brand {}".format(dg, shlex.quote(str(deck_dir)), shlex.quote(obj))
    if (deck_dir / ".deck-gates.json").is_file():
        print("NEXT: " + setc)
    else:                                       # `set` needs the record to exist first
        print("NEXT: {} init {}".format(dg, shlex.quote(str(deck_dir))))
        print("THEN: " + setc)
    print("  (Codex runtime: put  \"brand\": {}  in .codex-deck-evidence.json instead.)".format(obj))
    print("THEN: python3 {} {} --gate-check".format(
        shlex.quote(str(HERE / "render_deck.py")), shlex.quote(str(a.deck))))
    print("  (Codex runtime: the delivery gate as references/codex-runtime.md 'Evidence record and "
          "gate' runs it — codex_delivery_gate.py --lint … --components … --build-script … "
          "--evidence .codex-deck-evidence.json)")
    return 0


# ════════════════════════════════════════════════════════════════════════ save / list / use

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _brand_roots():
    sys.path.insert(0, str(HERE))
    import registry
    return registry


def cmd_save(a):
    if not _NAME.match(a.name or "") or ".." in a.name:
        raise Refused("kit name {!r} must be letters, digits, '.', '_' or '-' (no paths).".format(a.name))
    b = load_brand(a.brand)
    _require_confirmed(b, a.brand)
    reg = _brand_roots()
    if os.environ.get(reg.ENV_OVERRIDE, "").strip():
        root = reg.all_roots()[0][1]                # the override WINS for writes (registry.py's
    else:                                           # contract), even before it exists — never
        _rn, root = reg.root_for_write()            # silently the user's real registry instead
    dest = root / "brands" / a.name
    dest.mkdir(parents=True, exist_ok=True)
    src_base = Path(a.brand).resolve().parent
    if (src_base / ASSETS).is_dir():
        shutil.copytree(src_base / ASSETS, dest / ASSETS, dirs_exist_ok=True)
    b["name"] = b.get("name") or a.name
    b["confirmed"]["digest"] = digest(b)
    save_brand(dest / "brand.json", b)
    print("brand kit saved: {}".format(dest / "brand.json"))
    print("NEXT: for the next deck of this brand —  {} use {} <deck-dir>".format(_SELF, a.name))
    return 0


def _kits():
    reg = _brand_roots()
    seen = {}
    for _n, root in reg.roots_for_read():
        d = root / "brands"
        try:
            subs = sorted(p for p in d.iterdir() if (p / "brand.json").is_file()) if d.is_dir() else []
        except OSError:
            subs = []
        for p in subs:
            seen.setdefault(p.name, p)
    return seen


def cmd_list(a):
    kits = _kits()
    if not kits:
        print("no saved brand kits yet (they live under <registry>/brands/, beside the templates).")
        print("NEXT: {} extract <logo/guide/pptx…> --out <deck-dir>/brand.json".format(_SELF))
        return 0
    for name, p in kits.items():
        try:
            b = load_brand(p / "brand.json")
            prim = next((c["hex"] for c in b["colors"] if c.get("role") == "primary"), "—")
            print("  {:<20} primary {}  {}  ({})".format(name, prim, b.get("status"), p))
        except Unreadable as exc:
            print("  {:<20} UNREADABLE — {}".format(name, exc))
    print("NEXT: {} use <name> <deck-dir>".format(_SELF))
    return 0


def cmd_use(a):
    kits = _kits()
    if a.name not in kits:
        raise Refused("no saved brand kit named {!r} (saved: {}). `{} list` shows them.".format(
            a.name, ", ".join(kits) or "none", _SELF))
    src = kits[a.name]
    deck = Path(a.deck_dir)
    deck.mkdir(parents=True, exist_ok=True)
    tgt = deck / "brand.json"
    if tgt.exists() and not a.force:
        raise Refused("{} already exists — pass --force to replace it with kit {!r}.".format(tgt, a.name))
    if (src / ASSETS).is_dir():
        shutil.copytree(src / ASSETS, deck / ASSETS, dirs_exist_ok=True)
    shutil.copy2(src / "brand.json", tgt)
    b = load_brand(tgt)
    _require_confirmed(b, tgt)
    print("brand kit {!r} copied into {}".format(a.name, deck))
    print("NEXT: {} style {}".format(_SELF, shlex.quote(str(tgt))))
    return 0


# ════════════════════════════════════════════════════════════════════════ the gate contract

def recorded_brand(record):
    """The `brand` section of either runtime's record, or None (no section -> no brand gate)."""
    if not isinstance(record, dict):
        return None
    sec = record.get("brand")
    if sec is None and isinstance(record.get("design"), dict):
        sec = record["design"].get("brand")
    return sec if sec not in (None, {}, "") else None


def section_faults(sec):
    """Shape problems of a recorded `brand` section. [] = well-shaped."""
    if not isinstance(sec, dict):
        return ["`brand` must be an object — {\"file\": \"brand.json\"} or a categorised waiver."]
    if sec.get("waived") is not None:
        out = []
        if str(sec.get("waived_category") or "") not in WAIVER_CATEGORIES:
            out.append("`brand.waived` needs a `waived_category`: " + " | ".join(WAIVER_CATEGORIES))
        if len(str(sec.get("waived") or "").strip()) < MIN_WAIVER:
            out.append("`brand.waived` needs a written reason (which slides, whose palette, who "
                       "approved) — a bare word is a label, not a decision.")
        return out
    f = sec.get("file")
    if not isinstance(f, str) or not f.strip() or (f.strip().startswith("<") and f.strip().endswith(">")):
        return ["`brand.file` must name the confirmed brand.json (relative to the deck folder), "
                "got {!r}.".format(f)]
    return []


def gate(pptx, record, root=None):
    """(findings [(sev, code, why)], facts, waived_reason) for a recorded brand section."""
    sec = recorded_brand(record)
    if sec is None:
        return [], {"applies": False}, None
    faults = section_faults(sec)
    if faults:
        return [("block", "BRAND RECORD", f) for f in faults], {"applies": True}, None
    waived = sec.get("waived")
    if waived:
        return [], {"applies": True, "waived": waived}, waived
    root = Path(root or Path(pptx).resolve().parent)
    p = Path(sec["file"])
    p = p if p.is_absolute() else root / p
    try:
        b = load_brand(p)
        _require_confirmed(b, p)
    except (Unreadable, Refused) as exc:
        return [("block", "BRAND FILE", str(exc))], {"applies": True}, None
    findings, facts = check_deck(pptx, b, p.resolve().parent,
                                 multi_entity=str(sec.get("entity") or "single") == "multi")
    facts["applies"] = True
    facts["file"] = str(p)
    return [("block", f["code"], f["why"]) for f in findings], facts, None


# ════════════════════════════════════════════════════════════════════════ selftest / main

def _selftest():
    bad = []
    if norm_hex("#abc") != "#AABBCC" or norm_hex("0b5fff") != "#0B5FFF" or norm_hex("xyz"):
        bad.append("norm_hex")
    # CIEDE2000 reference pair (Sharma et al. 2005, pair 1): 2.0425
    import numpy as np
    d = float(de2000((50.0, 2.6772, -79.7751), np.array([[50.0, 0.0, -82.7485]]))[0])
    if abs(d - 2.0425) > 1e-3:
        bad.append("CIEDE2000 pair 1 = {:.4f}, want 2.0425".format(d))
    b = {"colors": [{"hex": "#0B5FFF", "role": "primary"}, {"hex": "#F2F5F9", "role": "neutral"}],
         "confirmed": {"neutral_policy": "achromatic"}}
    pal = Palette(b)
    if not pal.ok(mix("#0B5FFF", "#FFFFFF", 0.88)):
        bad.append("a deckkit-style 12% tint of the primary must be on-brand")
    if not pal.ok(mix("#0B5FFF", "#000000", 0.4)):
        bad.append("a shade of the primary must be on-brand")
    if pal.ok("#7B2CBF") or pal.ok("#E01E5A"):
        bad.append("violet / raspberry must be off-brand for a blue brand")
    if not pal.ok("#777777"):
        bad.append("a pure grey is allowed under the achromatic policy")
    if section_faults({"file": "brand.json"}) or not section_faults({"waived": "x"}):
        bad.append("section_faults")
    if recorded_brand({"brand": None}) is not None:
        bad.append("an empty section must mean no gate")
    print("[brand_kit selftest] {}".format("FAILED: " + "; ".join(bad) if bad else "ok"))
    return 1 if bad else 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        return _selftest()
    ap = argparse.ArgumentParser(prog="brand_kit.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("extract", help="read logo/guide/pptx files into a DRAFT brand.json")
    p.add_argument("files", nargs="*")
    p.add_argument("--hex", nargs="+", action="extend", help="colours the user typed")
    p.add_argument("--font", nargs="+", action="extend", help='"Name" or role=Name (heading|body|cjk|mono)')
    p.add_argument("--out", required=True)
    p.add_argument("--name")
    p = sub.add_parser("review", help="print the draft as a table to show the user")
    p.add_argument("brand")
    p.add_argument("--auto", action="store_true", help="auto mode: print the delegated-pick row")
    p = sub.add_parser("confirm", help="set roles, check faces and contrast, sign the kit")
    p.add_argument("brand")
    p.add_argument("--primary")
    for r in ("accent", "secondary", "neutral"):
        p.add_argument("--" + r, action="append")
    for r in ("heading", "body", "cjk", "mono"):
        p.add_argument("--{}-font".format(r), dest=r + "_font")
    p.add_argument("--lang", help="the deck's CJK language: zh-Hans | zh-Hant | ja | ko")
    p.add_argument("--strict-neutrals", action="store_true",
                   help="allow only the declared neutrals, not every achromatic grey")
    p = sub.add_parser("style", help="write brand_style.py for the build script")
    p.add_argument("brand")
    p.add_argument("--ground", choices=("light", "dark"), default="light")
    p.add_argument("--out")
    p = sub.add_parser("check", help="off-brand colours, faces and the logo rule in a built deck")
    p.add_argument("deck")
    p.add_argument("--brand", required=True)
    p.add_argument("--multi-entity", action="store_true", help="co-branded: skip the logo rule")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("save", help="keep a confirmed kit in the registry for the next deck")
    p.add_argument("brand")
    p.add_argument("--name", required=True)
    sub.add_parser("list", help="saved kits")
    p = sub.add_parser("use", help="copy a saved kit into a deck folder")
    p.add_argument("name")
    p.add_argument("deck_dir")
    p.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        print("NEXT: {} extract <logo/guide/pptx…> --out <deck-dir>/brand.json".format(_SELF))
        return 1
    try:
        return {"extract": cmd_extract, "review": cmd_review, "confirm": cmd_confirm,
                "style": cmd_style, "check": cmd_check, "save": cmd_save, "list": cmd_list,
                "use": cmd_use}[a.cmd](a)
    except Unreadable as exc:
        print("brand_kit: CANNOT READ — {}".format(exc), file=sys.stderr)
        return 2
    except Refused as exc:
        print("brand_kit: REFUSED — {}".format(exc), file=sys.stderr)
        return 1


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
