#!/usr/bin/env python3
"""archetypes_html — build the DIRECTION GATE preview as ONE self-contained HTML page.

This is the HTML counterpart to `archetypes.py` (which renders the same archetype slides
as a real .pptx). For the direction gate (references/collaborative-mode.md) you show the
user 2–3 *differentiated* style directions and let them pick. This script renders all of
them into a **single HTML file** — one link the user opens in a browser to review every
direction side-by-side and choose the one they like — instead of rendering local .pptx
samples + PNGs.

Why HTML here: it's fast (no LibreOffice round-trip), and the whole comparison is ONE
shareable file:// link. The trade-off is a fidelity gap to the real .pptx — so the gate's
job is *taste/direction only*, and the SAME design tokens that drive this HTML must seed
the chosen direction's `style.py`. After the user picks, render ONE real slide in the
chosen style (deckkit / render_deck) to confirm before the full build. (See
collaborative-mode.md "HTML preview link".)

PICKING: each direction has a **"Pick this one"** button; clicking it highlights that
direction and copies a short paste-back line to the clipboard — `I pick direction B —
Keynote` (or, from the "D — describe your own" textarea, `I pick D (my own): <text>`). The
page can't message the session, so the user pastes that line back into chat. Parse it to get
the choice; on a "D" line, synthesize a new direction token-set from their text and
regenerate this page.

The 4 archetype slides per direction mirror archetypes.py exactly — cover, bullets+callout,
diagram pipeline, data/figure — so the HTML comparison is apples-to-apples with what ships.

USAGE
  python archetypes_html.py directions.json out.html ["Deck Title"]

`directions.json` is a list of 2–3 direction objects. Each object (only `name` required;
sensible defaults fill the rest):
  {
    "name": "Editorial",
    "rationale": "serif, airy, gravitas",
    "bg":    "#FCFAF5",   "ink":  "#1A1A1A",  "grey": "#444444",
    "mute":  "#8A8A8A",   "line": "#E2DCCF",  "light": "#F3EEE2",
    "accent": "#B0451F",  "accents": ["#B0451F", "#2C6B76", "#6E7E3A", "#A66436"],
    "font_display": "Georgia, 'Times New Roman', serif",
    "font_body":    "'Helvetica Neue', Arial, sans-serif",
    "density": "minimal"
  }

KEEP FONTS PORTABLE — pick families present on macOS+Windows (Georgia, Arial/Helvetica,
'Times New Roman', Consolas, Verdana, 'Trebuchet MS'). The deck's real `style.py` should use
the same families (per references/font-guidance.md), so the preview and the .pptx agree and
the page renders the same offline (no webfont dependency).
"""
import html
import json
import os
import sys

_DEFAULTS = {
    "rationale": "",
    "bg": "#FFFFFF", "ink": "#1A1A1A", "grey": "#444444",
    "mute": "#8C8C8C", "line": "#E2E2E2", "light": "#F4F4F4",
    "accent": "#B0451F",
    "accents": None,
    "font_display": "Georgia, 'Times New Roman', serif",
    "font_body": "'Helvetica Neue', Arial, sans-serif",
    "density": "minimal",
    # COMPOSITION — the axis this preview could not express before. Two directions can share a
    # palette family and still read as different decks if the ink lands somewhere else; the
    # converse (different hues, identical layout) is the "three colourways of one idea" failure.
    "cover": "centred",         # centred | low-left | split-vertical | full-bleed-type
    "skeleton": "statement",    # statement | split | island | band | rail
}

_COVERS = ("centred", "low-left", "split-vertical", "full-bleed-type")
_SKELETONS = ("statement", "split", "island", "band", "rail")


def _norm(d):
    s = dict(_DEFAULTS)
    s.update({k: v for k, v in d.items() if v is not None})
    if not s.get("accents"):
        s["accents"] = [s["accent"]]
    s["name"] = d.get("name", "Direction")
    # An unknown value must not silently fall back to the default — that would make the gate
    # claim a composition it did not render. Fail loudly instead.
    if s["cover"] not in _COVERS:
        raise ValueError("direction {!r}: cover must be one of {}".format(s["name"], _COVERS))
    if s["skeleton"] not in _SKELETONS:
        raise ValueError("direction {!r}: skeleton must be one of {}".format(s["name"], _SKELETONS))
    return s


def _esc(t):
    return html.escape(str(t))


def _is_dark(hexc):
    s = str(hexc).lstrip("#")
    try:
        r, g, b = (int(s[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return False
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.45


# ── the 4 archetype slides, as HTML (mirrors scripts/archetypes.py) ──────────────────────

def _title_bar(S, title, kicker):
    k = (f'<div class="kicker" style="color:{S["accent"]}">{_esc(kicker)}</div>'
         if kicker else "")
    return (f'<div class="tbar">{k}'
            f'<div class="ttl" style="color:{S["ink"]}">{_esc(title)}</div>'
            f'<div class="rule" style="background:{S["accent"]}"></div></div>')


def _footer(S, page, tag=""):
    t = f'<span>{_esc(tag)}</span>' if tag else "<span></span>"
    return (f'<div class="ftr" style="color:{S["mute"]};border-color:{S["line"]}">'
            f'{t}<span>{page}</span></div>')


def _slide_cover(S):
    name = S["name"]
    # Faithful cover: a DARK deck gets a dark cover (its bg + light ink title); a LIGHT deck gets
    # a bold inverted cover (ink panel + light title). Avoids the inverted/low-contrast preview bug.
    if _is_dark(S["bg"]):
        cbg, tt, tag = S["bg"], S["ink"], S["mute"]
    else:
        cbg, tt, tag = S["ink"], "#ffffff", "rgba(255,255,255,.55)"
    comp = S["cover"]
    # The accent bar is a LEFT-EDGE device; on a split cover it becomes the divider, and on a
    # full-bleed-type cover it goes away entirely (the type IS the composition there).
    bar = "" if comp == "full-bleed-type" else (
        f'<div class="accentbar" style="background:{S["accent"]}"></div>')
    panel = (f'<div class="cover-panel" style="background:{S["accent"]}"></div>'
             if comp == "split-vertical" else "")
    return f'''<div class="slide cover cov-{comp}" style="background:{cbg}">
      {bar}{panel}
      <div class="cover-body">
        <div class="cover-ttl" style="color:{tt}">Deck Title</div>
        <div class="cover-sub" style="color:{S['accent']}">a one-line subtitle in this direction</div>
      </div>
      <div class="cover-tag" style="color:{tag}">Direction: {_esc(name)}</div>
    </div>'''


def _bullet_row(S, lead, body):
    return (f'<li><span class="mk" style="background:{S["accent"]}"></span>'
            f'<span class="bl-lead" style="color:{S["ink"]}">{_esc(lead)}</span>'
            f'<span class="bl-body" style="color:{S["grey"]}">{_esc(body)}</span></li>')


def _callout(S, label, body):
    return (f'<div class="callout" style="background:{S["accent"]}">'
            f'<span class="co-label">{_esc(label)}</span>'
            f'<span class="co-body">{_esc(body)}</span></div>')


def _slide_bullets(S):
    """The CONTENT archetype — rendered per the direction's skeleton, faithfully to the canonical
    vocabulary (design-intelligence-addendum §skeleton), so the user picks a composition the deck
    will actually build, not a padding variation of one layout."""
    sk = S["skeleton"]
    tb = _title_bar(S, "How content slides read", "archetype")
    bl3 = "".join([
        _bullet_row(S, "Terse points", "a few words each"),
        _bullet_row(S, "Emphasis", "where it matters"),
        _bullet_row(S, "Consistent", "spacing and rhythm"),
    ])
    co = _callout(S, "TAKEAWAY", "One idea per slide, carried by the layout.")
    fig = (f'<div class="mini-fig" style="background:{S["light"]};border-color:{S["line"]};'
           f'color:{S["mute"]}">[ visual ]</div>')

    if sk == "statement":
        # one oversized sentence, centred, NOTHING else — no bullets, no callout
        body = (f'<div class="st-kick" style="color:{S["accent"]}">ARCHETYPE</div>'
                f'<div class="st-line" style="color:{S["ink"]}">One idea, stated at full size.</div>'
                f'<div class="st-sub" style="color:{S["mute"]}">nothing else on the page</div>')
        return f'''<div class="slide sk-statement" style="background:{S['bg']}">
      <div class="sk-body">{body}</div>
      {_footer(S, 2, "direction preview")}
    </div>'''

    if sk == "split":
        # two vertical fields, text <-> visual
        body = (f'<div class="sp-l">{tb}<ul class="bullets">{bl3}</ul></div>'
                f'<div class="sp-r">{fig}</div>')
        return f'''<div class="slide sk-split" style="background:{S['bg']}">
      <div class="sk-body">{body}</div>
      {co}{_footer(S, 2, "direction preview")}
    </div>'''

    if sk == "island":
        # one figure dominating the middle, annotations ORBITING it
        body = (f'{tb}<div class="is-wrap">{fig}'
                f'<div class="is-note is-a" style="color:{S["ink"]};border-color:{S["accent"]};background:{S["bg"]}">annotation</div>'
                f'<div class="is-note is-b" style="color:{S["ink"]};border-color:{S["accent"]};background:{S["bg"]}">orbits the figure</div>'
                f'</div>')
        return f'''<div class="slide sk-island" style="background:{S['bg']}">
      <div class="sk-body">{body}</div>
      {_footer(S, 2, "direction preview")}
    </div>'''

    if sk == "band":
        # a full-width horizontal axis with content hanging off it
        chips = "".join(
            f'<div class="bd-item"><span class="bd-dot" style="background:{S["accent"]}"></span>'
            f'<span class="bd-t" style="color:{S["ink"]}">{t}</span></div>'
            for t in ("first beat", "second beat", "third beat"))
        body = (f'{tb}<div class="bd-axis" style="background:{S["line"]}"></div>'
                f'<div class="bd-row">{chips}</div>')
        return f'''<div class="slide sk-band" style="background:{S['bg']}">
      <div class="sk-body">{body}</div>
      {co}{_footer(S, 2, "direction preview")}
    </div>'''

    # rail — a NARROW SIDE RAIL (stat stack) + a wide main field
    rail = (f'<div class="rl-rail" style="border-color:{S["line"]}">'
            f'<div class="rl-stat" style="color:{S["accent"]}">42%</div>'
            f'<div class="rl-cap" style="color:{S["mute"]}">context stat</div>'
            f'<div class="rl-stat" style="color:{S["accent"]}">3&times;</div>'
            f'<div class="rl-cap" style="color:{S["mute"]}">stacked in the rail</div></div>')
    body = f'{rail}<div class="rl-main">{tb}<ul class="bullets">{bl3}</ul></div>'
    return f'''<div class="slide sk-rail" style="background:{S['bg']}">
      <div class="sk-body">{body}</div>
      {co}{_footer(S, 2, "direction preview")}
    </div>'''


def _slide_diagram(S):
    stages = ["Input", "Process", "Model", "Output"]
    acc = S["accents"]
    chips = []
    for i, nm in enumerate(stages):
        c = acc[i % len(acc)]
        chips.append(
            f'<div class="chip" style="background:{c}">'
            f'<div class="chip-t">{_esc(nm)}</div><div class="chip-s">one line</div></div>')
        if i < len(stages) - 1:
            chips.append(f'<div class="arrow" style="color:{S["accent"]}">&rarr;</div>')
    return f'''<div class="slide" style="background:{S['bg']}">
      {_title_bar(S, "How a diagram reads", "archetype")}
      <div class="pipe">{"".join(chips)}</div>
      {_footer(S, 3, "direction preview")}
    </div>'''


def _slide_data(S):
    legend = (f'<div class="lg-h" style="color:{S["accent"]}">LEGEND</div>'
              + _bullet_simple(S, "Series A", "baseline")
              + _bullet_simple(S, "Series B", "proposed"))
    return f'''<div class="slide" style="background:{S['bg']}">
      {_title_bar(S, "How a results slide reads", "archetype")}
      <div class="data-row">
        <div class="figbox" style="background:{S['light']};border-color:{S['line']};color:{S['mute']}">
          [ your figure / chart, shown whole ]
        </div>
        <div class="data-side">
          <div class="legend">{legend}</div>
          {_callout(S, "WHAT TO NOTICE", "The one comparison the figure makes.")}
        </div>
      </div>
      {_footer(S, 4, "direction preview")}
    </div>'''


def _bullet_simple(S, lead, body):
    return (f'<div class="lg-row"><span class="mk-sm" style="background:{S["accent"]}"></span>'
            f'<span style="color:{S["ink"]};font-weight:600">{_esc(lead)}</span> '
            f'<span style="color:{S["grey"]}">{_esc(body)}</span></div>')


def _swatches(S):
    cols = [S["ink"], S["accent"]] + [c for c in S["accents"] if c != S["accent"]]
    seen, out = set(), []
    for c in cols:
        if c.lower() in seen:
            continue
        seen.add(c.lower())
        out.append(f'<span class="sw" style="background:{c}" title="{_esc(c)}"></span>')
    return "".join(out)


def _direction_block(S, idx):
    letter = chr(ord("A") + idx)
    name = S["name"]
    rat = f' — <span class="rat">{_esc(S["rationale"])}</span>' if S["rationale"] else ""
    fonts = (f'<span class="fmeta">display: {_esc(S["font_display"].split(",")[0])} · '
             f'body: {_esc(S["font_body"].split(",")[0])} · {_esc(S["density"])}</span>')
    slides = (_slide_cover(S) + _slide_bullets(S) + _slide_diagram(S) + _slide_data(S))
    # Per-direction font scoping via a wrapper class + inline custom props.
    return f'''<section class="dir" id="dir-{letter}" style="--fd:{S['font_display']};--fb:{S['font_body']}">
      <div class="dir-head">
        <div class="dir-name"><span class="badge" style="background:{S['accent']}">{letter}</span>
          {_esc(name)}{rat}</div>
        <div class="dir-meta"><span class="swatches">{_swatches(S)}</span>{fonts}</div>
      </div>
      <div class="grid">{slides}</div>
      <div class="dir-foot">
        <button class="pick-btn" style="--ac:{S['accent']}"
          data-letter="{letter}" data-name="{_esc(name)}"
          onclick="pick('{letter}', this.dataset.name)">&#10003; Pick this one &mdash; {letter}</button>
      </div>
    </section>'''


_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
  background:#1b1d21;color:#e8e8ea;padding:28px 20px 60px;line-height:1.4}
.page-head{max-width:1180px;margin:0 auto 26px;padding:0 6px}
.page-head h1{font-size:22px;font-weight:700;letter-spacing:-.01em}
.page-head p{color:#a9acb2;font-size:13.5px;margin-top:7px;max-width:760px}
.page-head .pick{color:#ffd479;font-weight:600}
.dir{max-width:1180px;margin:0 auto 34px;background:#212429;border:1px solid #2e3238;
  border-radius:14px;padding:18px 18px 22px}
.dir-head{display:flex;justify-content:space-between;align-items:baseline;gap:16px;
  flex-wrap:wrap;margin-bottom:14px;padding:0 2px}
.dir-name{font-size:17px;font-weight:700;display:flex;align-items:center;gap:9px}
.dir-name .rat{font-weight:400;color:#a9acb2;font-size:14px}
.badge{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;
  border-radius:6px;color:#fff;font-size:13px;font-weight:700}
.dir-meta{display:flex;align-items:center;gap:12px;color:#9a9da3;font-size:12px}
.swatches{display:inline-flex;gap:5px}
.sw{width:15px;height:15px;border-radius:4px;display:inline-block;border:1px solid rgba(255,255,255,.14)}
.fmeta{font-size:11.5px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}

/* a slide card — fixed 16:9, internal sizes tuned to that box */
.slide{position:relative;aspect-ratio:16/9;border-radius:8px;overflow:hidden;
  box-shadow:0 1px 0 rgba(0,0,0,.4),0 6px 22px rgba(0,0,0,.28);
  padding:22px 26px;font-family:var(--fb)}
.tbar{margin-bottom:10px}
.kicker{font-size:10px;letter-spacing:.16em;text-transform:uppercase;font-weight:700}
.ttl{font-family:var(--fd);font-size:21px;font-weight:700;line-height:1.12;margin-top:3px}
.rule{width:46px;height:3px;border-radius:2px;margin-top:8px}
.bullets{list-style:none;margin-top:14px}
.bullets li{display:flex;align-items:baseline;gap:9px;margin-bottom:11px;font-size:14px}
.mk{width:8px;height:8px;border-radius:2px;flex:0 0 auto;transform:translateY(1px)}
.bl-lead{font-weight:700}
.callout{position:absolute;left:26px;right:26px;bottom:22px;border-radius:6px;
  padding:9px 13px;display:flex;align-items:baseline;gap:10px}
.co-label{color:#fff;font-size:10px;letter-spacing:.12em;font-weight:800;text-transform:uppercase;
  flex:0 0 auto;opacity:.92}
.co-body{color:#fff;font-size:13px;font-weight:500}
.cover{display:flex;flex-direction:column;justify-content:center}
.accentbar{position:absolute;left:0;top:0;bottom:0;width:10px}
.cover-body{padding-left:8px}
.cover-ttl{font-family:var(--fd);font-size:32px;font-weight:800;letter-spacing:-.01em}
.cover-sub{font-size:15px;margin-top:9px}
.cover-tag{position:absolute;left:26px;bottom:20px;font-size:11px;letter-spacing:.04em}
.pipe{display:flex;align-items:center;gap:7px;margin-top:24px}
.chip{flex:1;border-radius:7px;padding:13px 10px;color:#fff;min-width:0}
.chip-t{font-weight:700;font-size:14px}
.chip-s{font-size:11px;opacity:.85;margin-top:3px}
.arrow{font-size:18px;font-weight:700;flex:0 0 auto}
.data-row{display:flex;gap:16px;margin-top:14px;height:calc(100% - 74px)}
.figbox{flex:0 0 56%;border:1.5px solid;border-radius:6px;display:flex;align-items:center;
  justify-content:center;font-size:12px;font-style:italic}
.data-side{flex:1;display:flex;flex-direction:column;justify-content:space-between}
.lg-h{font-size:10px;letter-spacing:.12em;font-weight:800;text-transform:uppercase;margin-bottom:8px}
.lg-row{font-size:12.5px;margin-bottom:6px;display:flex;align-items:baseline;gap:7px}
.mk-sm{width:7px;height:7px;border-radius:2px;display:inline-block;flex:0 0 auto;transform:translateY(1px)}
.data-side .callout{position:static;margin-top:10px}
.ftr{position:absolute;left:26px;right:26px;bottom:8px;display:flex;justify-content:space-between;
  font-size:9px;border-top:1px solid;padding-top:4px;letter-spacing:.04em}
.cover .ftr{display:none}

/* ── COMPOSITION variants — the axis the direction gate now diverges on.
   Each must move the INK, not merely restyle it: a viewer comparing two directions should see
   a different shape with the page squinted, before reading a word. */
.cov-centred{justify-content:center}
.cov-low-left{justify-content:flex-end;padding-bottom:34px}
.cov-low-left .cover-ttl{font-size:30px}
.cov-split-vertical{justify-content:center;padding-left:46%}
.cov-split-vertical .cover-panel{position:absolute;left:0;top:0;bottom:0;width:40%;opacity:.92}
.cov-split-vertical .accentbar{display:none}
.cov-split-vertical .cover-ttl{font-size:26px}
/* the tag is bottom-LEFT by default, which on a split cover lands ON the accent panel at
   whatever contrast the pair happens to give. Move it beside the title instead. */
.cov-split-vertical .cover-tag{left:46%}
.cov-full-bleed-type{justify-content:center;padding-left:0;padding-right:0}
.cov-full-bleed-type .cover-body{padding-left:0;text-align:center}
.cov-full-bleed-type .cover-ttl{font-size:44px;letter-spacing:-.03em;line-height:.98}
.cov-full-bleed-type .cover-sub{margin-top:14px}
.cov-full-bleed-type .cover-tag{left:0;right:0;text-align:center}

/* z-index is INERT on a static element, so a bare z-index did NOT lift the body above the
   absolutely-positioned band: the band painted over the title, and only looked survivable because
   its tint is translucent. The body is positioned below (once the callout was moved out of it). */
/* .callout/.ftr are SIBLINGS of .sk-body (never descendants — a positioned ancestor would steal
   their slide-bottom anchoring; that bug shipped once). Each skeleton below implements its
   CANONICAL meaning from design-intelligence-addendum §skeleton, so the preview teaches the same
   vocabulary the deck will build. */
.sk-body{position:relative;z-index:2}
.callout,.ftr{z-index:3}
.mini-fig{display:flex;align-items:center;justify-content:center;border:1px dashed;
  border-radius:8px;font-size:11px;font-style:italic;min-height:96px;height:100%}

/* statement — one oversized sentence, centred, nothing else */
.sk-statement .sk-body{display:flex;flex-direction:column;justify-content:center;height:100%;
  text-align:center;padding:0 7%}
.st-kick{font-size:10px;letter-spacing:.14em;font-weight:700;margin-bottom:12px}
.st-line{font-family:var(--fd);font-size:27px;font-weight:800;line-height:1.15;
  letter-spacing:-.01em}
.st-sub{font-size:12px;margin-top:12px}

/* split — two vertical fields, text <-> visual */
.sk-split .sk-body{display:flex;gap:16px;height:100%}
.sk-split .sp-l{width:58%}
.sk-split .sp-r{width:42%;display:flex;align-items:stretch;padding:6px 0 44px}
.sk-split .sp-r .mini-fig{flex:1;width:100%}   /* main-axis size — without it the fig shrinks to a
                                                  sliver and the gate misrepresents the split */
.sk-split .bullets li{font-size:13px}

/* island — one figure dominating the middle, annotations orbiting */
.sk-island .is-wrap{position:relative;margin:4px 12% 0}
.sk-island .mini-fig{min-height:118px}
.is-note{position:absolute;font-size:10.5px;padding:3px 8px;border:1px solid;border-radius:99px}
.is-a{top:-6px;left:-9%}
.is-b{bottom:8px;right:-10%}

/* band — a full-width horizontal axis with content hanging off it */
.sk-band .bd-axis{height:2px;margin:26px 0 0;border-radius:2px}
.sk-band .bd-row{display:flex;justify-content:space-between;padding:0 4%;margin-top:-5px}
.bd-item{display:flex;flex-direction:column;align-items:center;gap:7px;width:30%}
.bd-dot{width:9px;height:9px;border-radius:99px}
.bd-t{font-size:12px;font-weight:600;text-align:center}

/* rail — a narrow side rail (stat stack) + a wide main field */
.sk-rail .sk-body{display:flex;gap:14px;height:100%}
.rl-rail{width:24%;border-right:1px solid;border-radius:8px 0 0 8px;padding:14px 12px 44px;
  background:rgba(127,127,127,.13)}   /* a tint of the deck's OWN ground — a fixed light fill on a
                                         dark direction shipped twice before this rule stuck */
.rl-stat{font-size:24px;font-weight:800;line-height:1}
.rl-cap{font-size:10px;margin:4px 0 14px}
.rl-main{width:76%;padding-right:4px}
.sk-rail .bullets li{font-size:13px}

/* pick buttons + selection */
.dir-foot{margin-top:14px;display:flex;justify-content:flex-end}
.pick-btn{appearance:none;border:1.5px solid var(--ac);background:transparent;color:#e8e8ea;
  font:600 13.5px/1 inherit;padding:10px 18px;border-radius:8px;cursor:pointer;
  display:inline-flex;align-items:center;gap:7px;transition:background .12s,color .12s}
.pick-btn:hover{background:var(--ac);color:#fff}
.dir.selected{outline:2.5px solid #ffd479;outline-offset:3px}
.dir.selected .pick-btn{background:var(--ac);color:#fff;border-color:var(--ac)}
.dir.selected .pick-btn::after{content:" ✓ selected";font-weight:700;opacity:.95}

/* describe-your-own (D) */
.dsec{max-width:1180px;margin:0 auto 34px;background:#212429;border:1px dashed #3a3f46;
  border-radius:14px;padding:18px}
.dsec h2{font-size:16px;font-weight:700;margin-bottom:6px}
.dsec p{color:#a9acb2;font-size:13px;margin-bottom:11px}
.dsec textarea{width:100%;min-height:74px;background:#1a1d22;color:#e8e8ea;border:1px solid #343a42;
  border-radius:8px;padding:11px 13px;font:14px/1.45 inherit;resize:vertical}
.dsec .ownbtn{margin-top:11px;appearance:none;border:1.5px solid #ffd479;background:transparent;
  color:#ffd479;font:600 13.5px/1 inherit;padding:10px 18px;border-radius:8px;cursor:pointer}
.dsec .ownbtn:hover{background:#ffd479;color:#1b1d21}

/* confirmation bar */
.cbar{position:fixed;left:0;right:0;bottom:0;background:#15171b;border-top:1px solid #2e3238;
  box-shadow:0 -6px 26px rgba(0,0,0,.4);padding:13px 22px;display:none;z-index:50}
.cbar.show{display:block}
.cbar-in{max-width:1180px;margin:0 auto;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.cbar .lab{font-weight:700;color:#9ae6b4;font-size:13.5px;flex:0 0 auto}
.cbar input{flex:1;min-width:240px;background:#0f1115;color:#e8e8ea;border:1px solid #343a42;
  border-radius:7px;padding:9px 12px;font:13px/1 ui-monospace,SFMono-Regular,Menlo,monospace}
.cbar .copy{appearance:none;border:none;background:#3b82f6;color:#fff;font:600 13px/1 inherit;
  padding:10px 16px;border-radius:7px;cursor:pointer;flex:0 0 auto}
.cbar .copy:hover{background:#2f6fd6}
.cbar .hint{flex-basis:100%;color:#8c949e;font-size:11.5px;margin-top:2px}
"""


def build_directions_html(directions, out_path, deck_title="Your Deck"):
    """Render 2–3 directions into ONE self-contained HTML file. Returns out_path."""
    styles = [_norm(d) for d in directions]
    letters = ", ".join(chr(ord("A") + i) for i in range(len(styles)))
    blocks = "\n".join(_direction_block(S, i) for i, S in enumerate(styles))
    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Choose a direction — {_esc(deck_title)}</title>
<style>{_CSS}</style></head>
<body>
  <div class="page-head">
    <h1>Choose a direction — {_esc(deck_title)}</h1>
    <p>Each direction below shows the <strong>same four slide types</strong> (cover, content,
    diagram, results) so the comparison is apples-to-apples — only the <em>style</em> differs.
    Review {letters}, then hit <strong>“Pick this one”</strong>
    (<span class="pick">or describe your own — “D”</span> at the bottom). Your pick is copied to
    the clipboard as a short line — <strong>paste it back to Claude</strong>. These are taste
    previews; once you pick, Claude renders one real slide in that style to confirm before
    building the full deck.</p>
  </div>
  {blocks}
  <div class="dsec">
    <h2>D — describe your own</h2>
    <p>None quite right? Type the look you have in mind — a reference deck/site, a brand, a mood,
    a colour, a constraint ("like our website", "warmer", "a serif on dark", "B's palette with A's
    serif"). Claude will build it and bring it back.</p>
    <textarea id="ownText" placeholder="e.g. darker than B, a warm serif headline, one teal accent…"></textarea>
    <button class="ownbtn" onclick="pickOwn()">Use my own description &rarr;</button>
  </div>
  <div class="cbar" id="cbar">
    <div class="cbar-in">
      <span class="lab" id="cbarLab">Copied!</span>
      <input id="cbarText" readonly onclick="this.select()">
      <button class="copy" onclick="copyAgain()">Copy</button>
      <span class="hint">Paste this line back into your chat with Claude. (If copy didn't work,
        click the box to select it, then ⌘/Ctrl-C.)</span>
    </div>
  </div>
  <script>
  function show(msg, text){{
    document.getElementById('cbarLab').textContent = msg;
    document.getElementById('cbarText').value = text;
    document.getElementById('cbar').classList.add('show');
    copyText(text);
  }}
  function copyText(text){{
    try {{ navigator.clipboard.writeText(text); }} catch(e) {{
      var b=document.getElementById('cbarText'); b.focus(); b.select();
      try {{ document.execCommand('copy'); }} catch(e2) {{}}
    }}
  }}
  function copyAgain(){{ copyText(document.getElementById('cbarText').value); }}
  function pick(letter, name){{
    document.querySelectorAll('.dir').forEach(function(d){{ d.classList.remove('selected'); }});
    var el = document.getElementById('dir-' + letter);
    if (el) el.classList.add('selected');
    show('Copied — paste to Claude:', 'I pick direction ' + letter + ' — ' + name);
  }}
  function pickOwn(){{
    var t = (document.getElementById('ownText').value || '').trim();
    if (!t) {{ document.getElementById('ownText').focus(); return; }}
    document.querySelectorAll('.dir').forEach(function(d){{ d.classList.remove('selected'); }});
    show('Copied — paste to Claude:', 'I pick D (my own): ' + t);
  }}
  </script>
</body></html>'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python archetypes_html.py directions.json out.html [\"Deck Title\"]")
        raise SystemExit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        dirs = json.load(f)
    if isinstance(dirs, dict):
        dirs = dirs.get("directions", [dirs])
    title = sys.argv[3] if len(sys.argv) > 3 else "Your Deck"
    out = build_directions_html(dirs, os.path.abspath(sys.argv[2]), title)
    print("wrote", out)
    print("open this link in a browser:  file://" + out)
