#!/usr/bin/env python3
"""The bespoke-register library, as BUILDABLE kits instead of prose.

`references/bespoke-registers.md` holds four registers invented from a subject's own world and
proved on real decks — `current`, `transit-signage`, `ledger`, `k-space`. They were written as
five-field descriptions (subject world · motif+meaning · legible-at-first · generates-triple · build
note), which is the right way to TEACH one and no way at all to BUILD one: a library of four worked
examples contained zero lines of runnable code, so every deck that reached for one re-derived it by
hand and got a different subset of the contracts right.

These are the same four, registered through `register_surface.register()`. That means they arrive
with everything a preset's kit has: `ground()` returns the content rect it leaves, loud marks may
not be painted into it, the furniture scales to any canvas, secondary ink resolves from the ground,
and each states what it REFUSES so `check_register_guard` can hold it to that.

They are STARTING POINTS, not answers. Every one of them was invented for a specific subject, and
the library entry says what family it fits — "any subject that accumulates across a divide", "any
subject that is a set of distinct paths", "any subject about a balance that fails or holds", "any
subject about partial measurement". Adapt the register to the subject in front of you (swap the
electric bus for the subject's own conduit); do not paste it because it renders.

    import bespoke_kits                       # registering is the import's whole job
    band = register_surface.ground(slide, "ledger", role="content", index=n)

To invent a NEW one: `python3 scripts/register_surface.py --new "<name>"` scaffolds a kit with
every contract already wired, and `scripts/save_register.py` keeps it after the deck ships.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deckkit as dk                                                          # noqa: E402
import register_surface as rs                                                 # noqa: E402
from register_surface import (MSO_SHAPE, _blend, _canvas, _hrule, _mute,      # noqa: E402
                              _note, _shape, _text, _h, _pick, color_band)


def _hues(n):
    """`n` DISTINCT hues for a register whose motif NEEDS them — never one colour n times.

    Rendered on a `swiss` palette (whose accents are a single red), `current`'s two-colour crossing
    came out one colour and `transit-signage`'s three routes came out one route: the motif's whole
    meaning is the difference between them, so collapsing to the base palette's accent count does
    not degrade the look, it deletes the idea. `deckkit.palette()` exists to return a thought-through
    categorical set, and falls back to its own well-separated accents when the register has fewer.
    """
    seen, out = set(), []
    for c in list(dk.palette(n, accents=getattr(dk, "ACCENTS", None))) + list(dk.palette(n)):
        key = tuple(dk._as_rgb(c))
        if key not in seen:
            seen.add(key)
            out.append(c)
        if len(out) == n:
            break
    # If the base palette simply does not HAVE n hues (swiss ships one red), derive the rest by
    # rotating the seed's hue rather than repeating a colour. A repeated colour is the same failure
    # as a missing one: two routes drawn in one hue are one route as far as a reader is concerned.
    import colorsys
    seed = dk._as_rgb(out[0] if out else dk.MAGENTA)
    h0, l0, s0 = colorsys.rgb_to_hls(seed[0] / 255, seed[1] / 255, seed[2] / 255)
    step, k = 1.0 / max(2, n), 1
    while len(out) < n:
        h = (h0 + step * k) % 1.0
        r, g, b = colorsys.hls_to_rgb(h, min(0.55, max(0.3, l0)), max(0.45, s0))
        cand = dk.RGBColor(int(r * 255), int(g * 255), int(b * 255))
        if all(sum(abs(a - c) for a, c in zip(dk._as_rgb(cand), dk._as_rgb(o))) > 90 for o in out):
            out.append(cand)
        k += 1
        if k > 24:                              # cannot happen with a sane palette; never spin
            raise RuntimeError("cannot derive {} distinct hues from {}".format(n, seed))
    return out


# --------------------------------------------------------------------------------------- current

def _current(slide, role, index):
    """A live electric BUS crossing from one colour register to another at a node.

    MEANS the crossing from a present state to a future one; the taps are the sub-points feeding
    each side. The kit paints the conduit and the junction and NOT the end labels — those name the
    two states, which are this deck's content, and a kit that guessed them would be inventing.
    """
    W, H = _canvas(slide)
    loud = role in ("cover", "section")
    # The bus sits LOW on a loud page: at 0.45H it left 1.4in above it, which is a strip, not a
    # page. The crossing still reads — a conduit near the foot with the taps hanging under it.
    bus_y = H * 0.66 if loud else 0.62
    thick = 0.09 if loud else 0.045
    node_x = W * (0.52 if loud else 0.34)
    before, after = _hues(2)
    # the bus: one colour up to the junction, the other after it — the crossing IS the motif
    _shape(slide, MSO_SHAPE.RECTANGLE, 0, bus_y, node_x, thick, fill=before, texture=not loud)
    _shape(slide, MSO_SHAPE.RECTANGLE, node_x, bus_y, W - node_x, thick, fill=after,
           texture=not loud)
    r = 0.2 if loud else 0.1
    _shape(slide, MSO_SHAPE.OVAL, node_x - r, bus_y + thick / 2 - r, 2 * r, 2 * r,
           fill=dk.GROUND, line=dk.INK if hasattr(dk, "INK") else dk.DEEP, line_w=1.6)
    if loud:
        _note(0, bus_y - 0.12, W, thick + 0.34 + 0.11 + 0.24)
        for i in range(4):                       # tap-off traces, the sub-points feeding each side
            tx = W * (0.16 + 0.21 * i)
            col = before if tx < node_x else after
            _shape(slide, MSO_SHAPE.RECTANGLE, tx, bus_y + thick, 0.022, 0.34, fill=col)
            _shape(slide, MSO_SHAPE.OVAL, tx - 0.055, bus_y + thick + 0.34, 0.11, 0.11, fill=col)
        return (0.7, 0.85, W - 1.4, bus_y - 0.28 - 0.85)
    return (0.7, bus_y + thick + 0.55, W - 1.4, H - (bus_y + thick + 0.55) - 0.6)


def _card_current(slide, x, y, w, h, label=None):
    """A tap-off block: the panel hangs from a short trace, so a card reads as fed BY the bus."""
    k = rs._K[0]
    body = dk.box(slide, x, y, w, h, fill=_blend(dk.GROUND, dk.TINT, 0.5),
                  line=_blend(dk.GROUND, dk.TEAL, 0.45), line_w=0.9, round=True, r=0.06 * k)
    # the trace hangs DOWN to the bus, which is below the band: drawn upward it pointed at nothing.
    _shape(slide, MSO_SHAPE.RECTANGLE, (x + w / 2) / k, (y + h) / k, 0.022, 0.2, fill=_hues(2)[1])
    return body, None


# ------------------------------------------------------------------------------- transit-signage

def _transit(slide, role, index):
    """Transit-map grammar: line COLOUR is a route, a numbered ROUNDEL is a step, a bar is a stop.

    The roundel carries the page's own index and nothing else — a route NAME belongs to the legend,
    which is content.
    """
    W, H = _canvas(slide)
    routes = _hues(3)
    loud = role in ("cover", "section")
    base = H - 0.52
    for i, col in enumerate(routes):             # the route field, quiet, along the foot
        y = base - i * 0.13
        _shape(slide, MSO_SHAPE.RECTANGLE, 0.5 + i * 0.25, y, W - 1.0 - i * 0.5, 0.055,
               fill=col, texture=not loud)
    stop = routes[_h(index, 3) % len(routes)]
    _shape(slide, MSO_SHAPE.RECTANGLE, W - 0.62, base - 0.3, 0.05, 0.42, fill=stop)  # buffer stop
    rr = 0.24
    _note(0.42, 0.26, 2 * rr + 0.1, 2 * rr + 0.1)
    _shape(slide, MSO_SHAPE.OVAL, 0.46, 0.28, 2 * rr, 2 * rr, fill=None, line=stop, line_w=3.0)
    _text(slide, 0.46, 0.34, 2 * rr, 0.3,
          [[("{:02d}".format(index + 1), 12, stop, True, False)]], align=dk.PP_ALIGN.CENTER)
    return (1.15, 0.3, W - 1.85, base - 0.5 - 0.3)


def _card_transit(slide, x, y, w, h, label=None):
    """A station panel: one route bar down its left edge, the way a map colours a line."""
    k = rs._K[0]
    body = dk.box(slide, x, y, w, h, fill=_blend(dk.GROUND, dk.TINT, 0.55),
                  line=_blend(dk.GROUND, dk.DEEP, 0.2), line_w=0.7, round=True, r=0.05 * k)
    _shape(slide, MSO_SHAPE.RECTANGLE, x / k, y / k, 0.07, h / k, fill=_hues(3)[0])
    return body, None


# ---------------------------------------------------------------------------------------- ledger

def _ledger(slide, role, index):
    """A ruled account page whose balance rule either closes or BREAKS.

    The kit rules the page and draws the balance rule at the foot; whether it closes is the deck's
    argument, so `card()` gives a ruled column rather than a box, and the STRIKE is the author's.
    """
    W, H = _canvas(slide)
    pitch, top = 0.28, 1.0
    y = top
    while y < H - 0.75:                          # the ruled field — a texture type sits on
        _hrule(slide, 0.6, y, W - 1.2, _blend(dk.GROUND, dk.DEEP, 0.12))
        y += pitch
    for f in (0.62, 0.81):                       # the debit / credit column rules
        cx = 0.6 + (W - 1.2) * f
        c = dk._flat(slide.shapes.add_connector(
            1, rs.Inches(cx * rs._K[0]), rs.Inches(top * rs._K[0]),
            rs.Inches(cx * rs._K[0]), rs.Inches((H - 0.75) * rs._K[0])))
        c.line.color.rgb = dk._as_rgb(_blend(dk.GROUND, dk.DEEP, 0.3))
        c.line.width = rs.Pt(0.7 * rs._K[0])
        c.shadow.inherit = False
    _hrule(slide, 0.6, H - 0.62, W - 1.2, dk.MAGENTA, weight=0.02)      # the balance rule
    _text(slide, 0.6, 0.42, W - 1.2, 0.26,
          [[("FOLIO {:02d}".format(index + 1), 9.5, _mute(), True, False)]])
    return (0.7, top + 0.05, W - 1.4, (H - 0.75) - top - 0.05)


def _card_ledger(slide, x, y, w, h, label=None):
    """No box — a ledger entry is a RULE and a measure. Boxing it would make it a card deck again."""
    k = rs._K[0]
    _hrule(slide, x, y, w, _blend(dk.GROUND, dk.DEEP, 0.45), weight=0.014 * k)
    _hrule(slide, x, y + h, w, _blend(dk.GROUND, dk.DEEP, 0.25), weight=0.01 * k)
    return None, None


# --------------------------------------------------------------------------------------- k-space

def _kspace(slide, role, index):
    """A grid of sampled vs skipped points: what was MEASURED against what was inferred.

    Density follows the k-space lineage — the centre rows are acquired, the outer ones fall away —
    so the mark carries the idea rather than illustrating it. Deterministic by index, never random.
    """
    W, H = _canvas(slide)
    loud = role in ("cover", "section")
    cols, rows = (22, 9) if loud else (16, 4)
    cw = (W - 1.2) / cols
    ch = 0.13
    d = min(cw, ch) * 0.62                       # a sampling POINT is round; cw>>ch made lozenges
    y0 = (H * 0.52) if loud else (H - 0.78)
    if loud:
        _note(0.6, y0 - 0.06, W - 1.2, rows * ch + 0.12)
    for r in range(rows):
        for c in range(cols):
            centre = abs(r - (rows - 1) / 2.0) / max(1.0, (rows - 1) / 2.0)
            acquired = centre < 0.4 or (_h(index, r * 31 + c) % 100) < int(70 * (1 - centre))
            x = 0.6 + c * cw
            yy = y0 + r * ch
            if acquired:
                _shape(slide, MSO_SHAPE.OVAL, x, yy, d, d, fill=dk.MAGENTA, texture=not loud)
            else:
                _shape(slide, MSO_SHAPE.OVAL, x, yy, d, d, fill=None,
                       line=_blend(dk.GROUND, dk.DEEP, 0.35), line_w=0.6, texture=not loud)
    if loud:
        return (0.7, 0.85, W - 1.4, (y0 - 0.32) - 0.85)
    return (0.7, 0.85, W - 1.4, (y0 - 0.3) - 0.85)


def _card_kspace(slide, x, y, w, h, label=None):
    """A panel with a sampling strip along its head — the card states its own coverage."""
    k = rs._K[0]
    body = dk.box(slide, x, y, w, h, fill=_blend(dk.GROUND, dk.TINT, 0.45),
                  line=_blend(dk.GROUND, dk.DEEP, 0.25), line_w=0.7)
    n = 9
    for i in range(n):
        filled = i % 3 != 2
        cx = (x + 0.1 + i * (w - 0.2) / n) / k
        _shape(slide, MSO_SHAPE.OVAL, cx, (y + 0.09) / k, 0.07, 0.07,
               fill=dk.MAGENTA if filled else None,
               line=None if filled else _blend(dk.GROUND, dk.DEEP, 0.35), line_w=0.6)
    return body, None


KITS = {
    "current": (_current, _card_current, ("gradient",)),
    "transit-signage": (_transit, _card_transit, ()),
    "ledger": (_ledger, _card_ledger, ("rounded", "gradient")),
    "k-space": (_kspace, _card_kspace, ("gradient",)),
}

for _name, (_g, _c, _forbids) in KITS.items():
    rs.register(_name, ground=_g, card=_c, forbids=_forbids, source=__file__)


def sample(out_path, base="swiss"):
    """One page per bespoke kit, same content — the difference IS the register."""
    import warnings
    import presets
    prs = None
    for i, name in enumerate(sorted(KITS)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            presets.apply(base)
        if prs is None:
            prs = dk.blank_deck()
        s = dk.add_slide(prs)
        role = "cover" if i % 2 == 0 else "content"
        bx, by, bw, bh = rs.ground(s, name, role=role, index=i)
        dk.text(s, bx, by, bw, 0.6,
                [[(name.upper() + "  " + role, 24, dk.DEEP, True, False)]])
        cw = (bw - 0.6) / 3.0
        for c in range(3):
            cx = bx + c * (cw + 0.3)
            rs.card(s, name, cx, by + 0.85, cw, max(0.5, bh - 1.05), label="CARD")
            if bh - 1.05 > 0.7:
                dk.text(s, cx + 0.16, by + 1.05, cw - 0.32, max(0.3, bh - 1.45),
                        [[("the same three cards on every page", 11, dk.DEEP, False, False)]])
    prs.save(str(out_path))
    return out_path


def _selftest():
    import tempfile
    import warnings
    import presets
    import check_register_guard as guard
    ok, bad = [], []
    tmp = Path(tempfile.mkdtemp(prefix="bespoke-"))
    snap = {k: getattr(dk, k) for k in dir(dk) if k.isupper()}
    try:
        for name in sorted(KITS):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                presets.apply("swiss")
            prs = dk.blank_deck()
            for i, role in enumerate(("cover", "content", "section")):
                s = dk.add_slide(prs)
                bx, by, bw, bh = rs.ground(s, name, role=role, index=i)
                if bw < 3.5 or bh < 1.4:
                    bad.append("{}/{}: band {:.1f}x{:.1f} is not a page".format(name, role, bw, bh))
                cw, ch = min(3.0, bw / 2), max(0.6, bh - 0.6)
                rs.card(s, name, bx, by + 0.5, cw, ch, label="L")
                dk.text(s, bx + 0.2, by + 0.7, max(0.5, cw - 0.4), max(0.3, ch - 0.4),
                        [[("content", 12, dk.DEEP, False, False)]])
            p = tmp / "{}.pptx".format(name.replace("-", "_"))
            prs.save(str(p))
            declared = rs.forbids(name)
            if declared:
                viol, _f = guard.check(p, register=name)
                ok.append("`{}` obeys the prohibitions it declares ({})".format(
                    name, " · ".join(declared))) if not viol else bad.append(
                    "{} violates its own: {}".format(name, [c for c, _m in viol]))
            else:
                ok.append("`{}` declares no prohibitions, and says so rather than pretending".format(name))
    finally:
        for k, v in snap.items():
            setattr(dk, k, v)

    ok.append("all {} library registers are registered kits, not prose".format(len(KITS))) \
        if all(rs.has(n) and rs.is_bespoke(n) for n in KITS) else bad.append("not all registered")
    for line in ok:
        print("  ok   " + line)
    for line in bad:
        print("  FAIL " + line)
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    import argparse
    from _console import safe_stdio
    safe_stdio()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sample", metavar="OUT.pptx")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.sample:
        print("wrote", sample(a.sample))
        return 0
    for n in sorted(KITS):
        print("  {:18s} forbids: {}".format(n, " · ".join(rs.forbids(n)) or "—"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
