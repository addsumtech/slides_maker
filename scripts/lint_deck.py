#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_deck.py — deterministic LAYOUT lint for a built .pptx: catches the overlaps a visual
critic can miss (a callout tucked a few px under a panel/image, a block hanging off the slide,
content colliding with the footer).

    python scripts/lint_deck.py deck.pptx

Run it right after building, BEFORE/with the critic loop — it's a cheap, deterministic safety net
for the "no block/text/image overlap" rule, not a replacement for the visual critic (which judges
crop, balance, legibility, fidelity). Exits non-zero if it finds anything.

Checks (tuned for low false-positives):
  1. OVERFLOW   — a shape extends beyond the slide edge.
  2. OVERLAP    — two SOLID shapes (filled auto-shape / picture / table / freeform) partially
                  overlap with NEITHER contained in the other. Intentional layering — text on a
                  card, an image inside its frame, a header band on a card, a full-bleed
                  background — is *containment* and is NOT flagged; only "two separate blocks
                  collide" partial overlaps are.
  3. FOOTER     — a solid block overlaps a footer / page-number text box at the bottom.
"""
import sys
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

EMU = 914400.0
TOL = 0.05        # inches — ignore hairline/touching overlaps
CONTAIN = 0.90    # A is "inside" B when >=90% of A's area lies within B
SOLID = {MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.TABLE, MSO_SHAPE_TYPE.FREEFORM}


def _boxes(slide, sw, sh):
    out = []
    for s in slide.shapes:
        try:
            l, t, w, h = s.left / EMU, s.top / EMU, s.width / EMU, s.height / EMU
        except (TypeError, AttributeError):
            continue
        if not w or not h or w <= 0 or h <= 0:
            continue
        full = s.text_frame.text.strip() if s.has_text_frame else ""
        txt = full.replace("\n", " ")[:26]
        paras, size = [], 0.0
        if s.has_text_frame:
            size = max((r.font.size.pt for p in s.text_frame.paragraphs for r in p.runs if r.font.size),
                       default=12.0)
            for p in s.text_frame.paragraphs:
                pr = [(r.text, (r.font.size.pt if r.font.size else size)) for r in p.runs]
                if pr:
                    paras.append(pr)
        out.append({"l": l, "t": t, "w": w, "h": h, "r": l + w, "b": t + h,
                    "st": str(s.shape_type).split()[0], "txt": txt, "full": full, "size": size or 12.0,
                    "paras": paras, "solid": s.shape_type in SOLID,
                    "text": bool(s.has_text_frame and txt),
                    "bg": (w * h) >= 0.95 * (sw * sh)})
    return out


def _est_lines(paras, width_in):
    """CJK-aware estimate of total wrapped line count across paragraphs, using each RUN's own font
    size (so a mixed-size 'small label + big value' stat line counts as one line, not two). CJK glyph
    ≈ 1 em, Latin ≈ 0.52 em."""
    if width_in <= 0 or not paras:
        return 1
    total = 0
    for pr in paras:
        lines, w = 1, 0.0
        for text, size_pt in pr:
            em = max(0.01, size_pt / 72.0)
            for ch in text:
                if ch == "\n":
                    lines += 1; w = 0.0; continue
                cw = em * (1.0 if ord(ch) > 0x2E80 else 0.52)
                if w + cw > width_in and w > 0:
                    lines += 1; w = cw
                else:
                    w += cw
        total += lines
    return total or 1


def _inter(a, b):
    return (max(0.0, min(a["r"], b["r"]) - max(a["l"], b["l"])),
            max(0.0, min(a["b"], b["b"]) - max(a["t"], b["t"])))


def _frac_inside(a, b):
    ix, iy = _inter(a, b)
    return (ix * iy) / (a["w"] * a["h"] + 1e-9)


def lint(path):
    prs = Presentation(path)
    sw, sh = prs.slide_width / EMU, prs.slide_height / EMU
    total = 0
    for si, slide in enumerate(prs.slides):
        bx = _boxes(slide, sw, sh)
        finds = []
        # 1) overflow
        for s in bx:
            if s["bg"]:
                continue
            ov = []
            if s["l"] < -TOL: ov.append("left")
            if s["t"] < -TOL: ov.append("top")
            if s["r"] > sw + TOL: ov.append(f"right+{round(s['r']-sw,2)}")
            if s["b"] > sh + TOL: ov.append(f"bottom+{round(s['b']-sh,2)}")
            if ov:
                finds.append(f"OVERFLOW [{','.join(ov)}] {s['st']} '{s['txt']}'")
        # 2) solid vs solid partial overlap (neither contained)
        sol = [s for s in bx if s["solid"] and not s["bg"]]
        for i in range(len(sol)):
            for j in range(i + 1, len(sol)):
                a, b = sol[i], sol[j]
                ix, iy = _inter(a, b)
                if ix > TOL and iy > TOL and _frac_inside(a, b) < CONTAIN and _frac_inside(b, a) < CONTAIN:
                    finds.append(f"OVERLAP {round(ix,2)}x{round(iy,2)}in  {a['st']}'{a['txt']}' x {b['st']}'{b['txt']}'")
        # 3) footer collision: a solid block over a bottom text label
        footers = [s for s in bx if s["text"] and s["t"] > sh - 0.6 and not s["bg"]]
        for f in footers:
            for s in sol:
                ix, iy = _inter(s, f)
                if ix > TOL and iy > TOL and _frac_inside(f, s) < CONTAIN:
                    finds.append(f"FOOTER collision  {s['st']}'{s['txt']}' over footer '{f['txt']}'")
        # 4) editability: a slide that is ~one whole-page image with no native text/objects
        bigpic = next((s for s in bx if s["st"] == "PICTURE" and s["w"] * s["h"] >= 0.85 * sw * sh), None)
        if bigpic is not None:
            others = [s for s in bx if s is not bigpic and not s["bg"] and (s["text"] or s["w"] * s["h"] > 0.5)]
            if not others:
                finds.append("EDITABILITY: slide is ~one whole-page image with no native text/objects "
                             "(build content as native shapes; images are plates/figures, not the whole slide)")
        # 5) orphan / blank slide
        if not [s for s in bx if not s["bg"] and (s["text"] or s["solid"])]:
            finds.append("EMPTY/ORPHAN slide: no native content (blank or background only)")
        # 6) text overflowing the filled CARD it sits on (text taller than its container)
        cards = [s for s in bx if s["solid"] and not s["bg"] and not s["text"] and s["h"] > 0.35]
        for t in [s for s in bx if s["text"]]:
            host = None
            for c in cards:
                if c["l"] - 0.12 <= t["l"] and t["r"] <= c["r"] + 0.12 and c["t"] - 0.12 <= t["t"] <= c["b"] - 0.05:
                    if host is None or c["b"] < host["b"]:
                        host = c
            if host:
                nlines = _est_lines(t["paras"], t["w"])
                lh = 1.4 if any(ord(ch) > 0x2E80 for ch in t["full"]) else 1.25   # CJK lines run taller
                est_bottom = t["t"] + 0.06 + nlines * (t["size"] / 72.0) * lh      # + top inset
                if est_bottom > host["b"] + 0.05:
                    finds.append(f"TEXT OVERFLOWS its card: '{t['txt']}' (~{nlines} lines) runs past the "
                                 f"card bottom ({round(host['b'],2)}in) — size the card to the text "
                                 f"(measure-then-place) or shorten the text")
        # 7) uneven card heights in a row (sibling cards must share ONE height)
        cset = [s for s in bx if s["solid"] and not s["bg"] and not s["text"] and s["h"] > 0.5 and s["w"] < 0.6 * sw]
        bycol = {}                                  # dedupe layered shapes per (top,left): keep the tallest (the card, not its header band)
        for c in cset:
            key = (round(c["t"] * 10), round(c["l"] * 10))
            if key not in bycol or c["h"] > bycol[key]["h"]:
                bycol[key] = c
        rows = {}
        for c in bycol.values():
            rows.setdefault(round(c["t"] * 10), []).append(c)
        for _top, row in rows.items():
            if len(row) >= 2 and (max(r["w"] for r in row) - min(r["w"] for r in row)) < 0.4:  # a row of similar-width siblings
                hs = [r["h"] for r in row]
                if max(hs) - min(hs) > 0.12:
                    finds.append(f"UNEVEN CARD HEIGHTS: a row of {len(row)} cards has heights "
                                 f"{sorted(round(h,2) for h in hs)} — sibling cards in a row must share ONE "
                                 f"height (size the row to the tallest card's content)")
        for m in finds:
            print(f"  slide {si+1}: {m}")
        total += len(finds)
    print(f"\n{path}: {total} layout finding(s)" + ("" if total else "  ✓ clean"))
    return total


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python lint_deck.py <deck.pptx>"); sys.exit(2)
    sys.exit(1 if lint(sys.argv[1]) > 0 else 0)
