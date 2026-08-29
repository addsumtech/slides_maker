#!/usr/bin/env python3
"""The register a deck declares must reach its PIXELS — and must not be the last deck's.

SKILL.md states two rules that survive no matter what: **never ship deckkit's default blue, and
never reuse the last deck's scheme.** Both were prose. What existed instead:

  * `check_style_applied.py` verifies the CALL — `presets.apply("brutalist")` appearing in the
    build script. A deck that calls it and then hand-sets the tokens back to stock passes, and a
    **bespoke** register (no preset call at all) is skipped by definition. Measured: the deck built
    in this repo's own session set its whole register by hand, and nothing verified it landed.
  * The sameness lint measures monotony WITHIN one deck; SKILL.md says so itself — "no gate checks
    that a built deck EXPRESSES its register".
  * Freshness against past decks lived in one prose line of `taste.md`, with nothing scoring it.

The sibling skill already learned the lesson this file applies: its null-DNA gate hashes real
renders because "that is a claim about real CSS in a real browser, so it is checked by hashing real
renders — not by asserting that a variable is present." A palette is the same kind of claim.

So this reads the RENDERED PNGs and asks three questions a source-level check cannot:

  STOCK REGISTER SHIPPED   deckkit's own identity colours dominate the pages while the palette the
                           plan declares is nowhere on them — the "default blue" rule, measured.
  DECLARED PALETTE ABSENT  the plan names colours the render does not contain (a bespoke register
                           that never reached the build, or a palette rewritten after the fact).
  LAST DECK'S SCHEME       the ground value and the accents match a deck already in `taste.md`'s
                           LOOK HISTORY — the freshness rule, measured across decks instead of
                           asserted in a sentence.

    python3 scripts/check_register_pixels.py <deck-dir> [--renders DIR] [--taste PATH]
    python3 scripts/check_register_pixels.py --selftest

🔴 It judges COLOUR IDENTITY only. It cannot see composition, type, geometry or motif, so a deck
can pass here and still be a stock layout in fresh paint — the critic's distinctiveness axis and
the sameness gate own that half. Exit 0 clean · 1 findings · 2 could not run.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

HEX = re.compile(r"#([0-9a-fA-F]{6})\b")

# deckkit's own identity, from scripts/deckkit.py. A deck wearing these while its plan declares
# something else is the exact failure the "never ship the default blue" rule names. Only the three
# CHROMATIC tokens are listed: deckkit's TINT is a near-white wash, and near-white matches almost
# any light ground — measured, #EAF3FA covered 11.8% of a page in a deck that contains no deckkit
# colour at all. A discriminator that fires on every pale deck is not a discriminator.
STOCK = {"DEEP": (0x00, 0x3C, 0x66), "BLUE": (0x00, 0x7C, 0xC2), "MAGENTA": (0xE3, 0x00, 0x4F)}

# How close two colours have to be to count as "the same colour" to a viewer. Redmean is a cheap
# perceptual approximation — good enough to tell one register from another, and honest about not
# being a calibrated deltaE.
NEAR = 30.0               # "this exact colour is on the page"
SAME_LOOK = 36.0          # "this is the same look as that other deck"
PRESENT = 0.0015          # see presence(): measured to sit between blend noise and real ink
MIN_AREA = 0.004          # a colour under 0.4% of the page is a speck, not part of the GROUND
TOP_N = 8                 # colours considered "the page's field"
CHROMA = 40               # max-min channel spread that separates a colour from a grey


def _dist(a, b):
    """Redmean colour distance — cheap, perceptual enough, no dependency."""
    rm = (a[0] + b[0]) / 2.0
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return ((2 + rm / 256.0) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256.0) * db * db) ** 0.5


def _near(a, b, tol=NEAR):
    return _dist(a, b) <= tol


def _chromatic(rgb):
    return max(rgb) - min(rgb) >= CHROMA


def _band(rgb):
    """dark / mid / light — the coarse value a viewer registers before any hue."""
    v = sum(rgb) / 3.0
    return "dark" if v < 90 else ("light" if v > 200 else "mid")


def _hexes(text):
    out = []
    for m in HEX.finditer(str(text or "")):
        h = m.group(1)
        rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        if rgb not in out:
            out.append(rgb)
    return out


def _hx(rgb):
    return "#%02X%02X%02X" % tuple(rgb)


def _load(png, side=900):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    im.thumbnail((side, side))
    return im


def page_field(png):
    """[(rgb, area_fraction), …] for one render, most area first — what FILLS the page.

    Quantized on purpose: the field is about grounds and blocks, and antialiasing would otherwise
    split one ground into a hundred near-identical entries.
    """
    from PIL import Image
    im = _load(png, 220)
    q = im.quantize(colors=24, method=Image.MEDIANCUT).convert("RGB")
    total = q.size[0] * q.size[1]
    counts = {}
    for count, rgb in q.getcolors(maxcolors=1 << 16) or []:
        counts[rgb] = counts.get(rgb, 0) + count
    return sorted(((rgb, c / float(total)) for rgb, c in counts.items()), key=lambda t: -t[1])


def readable(pngs):
    """(good, bad) — a render this cannot open is REPORTED, never allowed to abort the check.

    Both callers of this module wrap it in try/except so a broken checker can never fail a render.
    That protection turns any raised exception into "NOT CHECKED" for the WHOLE deck, so a single
    truncated PNG among fifteen good ones would silently switch the colour gate off. Degrade
    loudly: check what can be read, and name what cannot.
    """
    good, bad = [], []
    for png in pngs:
        try:
            _load(png, 32).convert("RGB")
            good.append(png)
        except Exception as exc:
            bad.append((png, "{}: {}".format(exc.__class__.__name__, exc)))
    return good, bad


def presence(pngs, colours):
    """{colour: largest share of any ONE page within NEAR of it}.

    Deliberately NOT quantized and NOT area-ranked. A register's accent usually lives in TYPE:
    measured on a real 15-page deck, its signature green covered 0.65% of its best page and its ink
    1.4% — both far below any "dominant colour" cut, and both unmistakably the deck's identity to a
    viewer. Ranking by area answers "what is this page mostly made of", which is a different
    question from "did the declared register reach the pixels". Colours genuinely absent from that
    same deck measured 0.0000%, so the two populations do not overlap.

    PRESENT is set from the same measurements. Two colours can also meet ACCIDENTALLY: where a
    white ground abuts a pale panel, antialiasing produces every blend between them, and a cream
    that is in neither one scored 0.093% of a page that way. The smallest colour a real deck
    deliberately used — an amber reserved for one status — scored 0.41%. The threshold sits
    between them. It is a floor, not a truth: a hue placed once, on one small mark, can fall under
    it and be reported absent. That is why the finding names the missing colours and points at the
    waiver instead of just failing.
    """
    if not colours:
        return {}
    try:
        import numpy as np
    except ImportError:
        np = None
    best = {c: 0.0 for c in colours}
    for png in pngs:
        im = _load(png)
        if np is not None:
            a = np.asarray(im, dtype=np.float64).reshape(-1, 3)
            n = float(len(a))
            for c in colours:
                rm = (a[:, 0] + c[0]) / 2.0
                dr, dg, db = a[:, 0] - c[0], a[:, 1] - c[1], a[:, 2] - c[2]
                d2 = (2 + rm / 256.0) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256.0) * db * db
                frac = float((d2 <= NEAR * NEAR).sum()) / n
                if frac > best[c]:
                    best[c] = frac
        else:                                   # no numpy: loop distinct colours, not pixels
            hist = im.getcolors(maxcolors=1 << 24) or []
            n = float(im.size[0] * im.size[1])
            for c in colours:
                frac = sum(k for k, rgb in hist if _near(rgb, c)) / n
                if frac > best[c]:
                    best[c] = frac
    return best


def deck_field(pngs):
    """The colours that FILL this deck's pages, by mean area across them."""
    acc = {}
    for p in pngs:
        for rgb, frac in page_field(p):
            if frac < MIN_AREA:
                continue
            hit = next((k for k in acc if _near(k, rgb, 18.0)), None)
            acc[hit or rgb] = acc.get(hit or rgb, 0.0) + frac
    field = sorted(acc.items(), key=lambda t: -t[1])[:TOP_N]
    return [(rgb, f / max(1, len(pngs))) for rgb, f in field]


def look_history(taste_path):
    """Past decks as (deck, [rgb…]) from taste.md's LOOK HISTORY table, newest last."""
    try:
        text = Path(taste_path).read_text(encoding="utf-8")
    except OSError:
        return []
    if "LOOK HISTORY" not in text:
        return []
    tail = text.split("LOOK HISTORY", 1)[1]
    rows = []
    for line in tail.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower().startswith(("date", "---")) or set(cells[0]) <= set("-: "):
            continue
        cols = _hexes(" ".join(cells))
        if cols:
            rows.append((cells[1] if len(cells) > 1 else "?", cols))
    return rows


def printed_surface(deck_dir, design):
    """The registered Format for this deck if it is PRINTED AT ACTUAL SIZE, else None.

    Freshness is a rule about a RUN of decks; ink on paper is a rule about one board, and the
    second one wins where they meet. Recovered from the built .pptx beside the renders, or from a
    declared `format`, because a render is just pixels and cannot say how it will be reproduced.
    """
    try:
        import formats
    except Exception:
        return None
    name = (design or {}).get("format")
    if name:
        try:
            fmt = formats.get(name)
            return fmt if fmt.chrome == "print" else None
        except KeyError:
            return None
    try:
        from pptx import Presentation
    except ImportError:
        return None
    for deck in sorted(Path(deck_dir).glob("*.pptx")):
        try:
            prs = Presentation(str(deck))
            fmt = formats.match(prs.slide_width / 914400.0, prs.slide_height / 914400.0)
        except Exception:
            continue
        if fmt is not None and fmt.chrome == "print":
            return fmt
    return None


def check(deck_dir, renders=None, taste=None, recent=3, design=None):
    """Return (problems, facts). Empty problems means clean.

    `design` lets a caller hand in the plan dict it already has — the codex path keeps it in
    `.codex-deck-evidence.json` under `design`, the shared path in `.deck-gates.json` under
    `design_plan`. Both paths then run THIS code over the same pixels rather than growing two
    opinions about the same deck.
    """
    deck_dir = Path(os.path.expanduser(deck_dir))
    renders = renders or str(deck_dir / "render")
    problems, facts = [], {}

    if design is None:
        gates = {}
        gp = deck_dir / ".deck-gates.json"
        if gp.exists():
            try:
                gates = json.loads(gp.read_text(encoding="utf-8"))
            except (ValueError, OSError) as exc:
                # OSError as well as ValueError, and REPORTED rather than raised. Both callers
                # wrap this module in try/except, so anything that escapes here becomes a silent
                # "NOT CHECKED" for the whole deck. Measured: on macOS, a deck under ~/Downloads
                # became unreadable mid-session (TCC), and `read_text` raised PermissionError —
                # not a ValueError — straight past this handler.
                return [("UNREADABLE GATES",
                         "{}: {}. The plan could not be read, so nothing here was checked — that "
                         "is not the same as clean. On macOS this is usually the privacy layer "
                         "over ~/Downloads or ~/Desktop; move the deck elsewhere or grant access."
                         .format(gp, exc))], facts
        design = gates.get("design_plan") or {}
    if design.get("waived") or design.get("register_pixels_waived"):
        facts["waived"] = True
        return [], facts

    declared = _hexes(design.get("palette")) + [c for c in _hexes(design.get("style_pick"))
                                                if c not in _hexes(design.get("palette"))]
    pngs = sorted(glob.glob(os.path.join(renders, "slide*.png")))
    pngs, unreadable = readable(pngs)
    facts["pages"] = len(pngs)
    if unreadable:
        problems.append(("UNREADABLE RENDER",
                         "{} render(s) could not be opened and were left out of the measurement: "
                         "{}. Re-render before trusting the rest of this report — a colour check "
                         "over a partial deck is a partial answer, not a clean one."
                         .format(len(unreadable),
                                 "; ".join("{} ({})".format(os.path.basename(f), e)
                                           for f, e in unreadable[:3]))))
    if not pngs:
        return [("NO RENDERS", "no slide*.png under {} — this check reads PIXELS, and there are "
                               "none to read. Render first (`scripts/render_deck.sh <deck>`)."
                               .format(renders))], facts

    field = deck_field(pngs)
    seen = presence(pngs, declared + list(STOCK.values()))
    facts["field"] = [_hx(rgb) for rgb, _ in field[:6]]
    facts["declared"] = [_hx(c) for c in declared]
    facts["present"] = [_hx(c) for c in declared if seen.get(c, 0) >= PRESENT]
    if not declared:
        # Not a failure: `palette` is prose and may legitimately carry no hex (a locked corporate
        # template, a mimic of a supplied deck). Say so rather than inventing a verdict — silence
        # here would read as a pass.
        facts["note"] = ("design_plan.palette names no hex colour, so the declared-vs-rendered "
                         "half could not run; only the stock-register and freshness checks did")

    hit = [c for c in declared if seen.get(c, 0) >= PRESENT]
    stock_hits = [n for n, rgb in STOCK.items() if seen.get(rgb, 0) >= PRESENT]
    # A register is carried by its HUES. Greys, near-blacks and near-whites are shared by half the
    # world's decks and match each other across a blend, so they cannot answer "did this register
    # arrive" — measured, a cream ground scored as "present" on a deck rendered in deckkit's own
    # white-and-blue purely through antialiasing at a panel edge.
    want_hue = [c for c in declared if _chromatic(c)]
    got_hue = [c for c in want_hue if seen.get(c, 0) >= PRESENT]
    facts["hues"] = [_hx(c) for c in want_hue]

    # ── 1. the "never ship deckkit's default blue" rule, measured ────────────────────────────
    stock_shipped = (len(stock_hits) >= 2 and want_hue
                     and len(got_hue) < max(1, (len(want_hue) + 1) // 2))
    if stock_shipped:
        problems.append(("STOCK REGISTER SHIPPED",
                         "the pages are wearing deckkit's own identity ({}) while the hues the plan "
                         "declares ({}) are mostly absent from them — {} of {} reached a pixel. That "
                         "is the default-blue rule: a register was chosen on paper and the build "
                         "shipped the stock one. `presets.apply()` sets palette AND geometry AND "
                         "ground together; setting tokens by hand afterwards, or calling it after "
                         "the slides are already laid down, puts the stock ones back."
                         .format(", ".join(sorted(stock_hits)),
                                 ", ".join(_hx(c) for c in want_hue) or "none",
                                 len(got_hue), len(want_hue))))

    # A ground and an ink are shared by half the world's decks; the HUES are what make a register
    # that register. If the plan declares hues and not one of them reached a pixel, the colour
    # identity did not arrive — regardless of how the count-based rule below happens to land. The
    # count rule cannot see this on its own: a two-colour plan whose ground still matches scores
    # 1 of 2 and clears "fewer than half", which is how a deck rendered entirely in GREYSCALE
    # passed an earlier version of this check.
    if want_hue and not got_hue and not stock_shipped:
        problems.append(("DECLARED HUES ABSENT",
                         "not one of the declared hues ({}) reached a pixel. A ground and an ink "
                         "are shared by half the world's decks — the hue is the register. Either it "
                         "was never applied, or it is used so sparingly (a hairline, one small mark) "
                         "that it does not read as this deck's colour. If the restraint is "
                         "deliberate, record it in the palette line or set "
                         "design_plan.register_pixels_waived."
                         .format(", ".join(_hx(c) for c in want_hue))))

    # ── 2. the declared palette must actually be on the pages ────────────────────────────────
    if declared and not stock_shipped and len(hit) < max(1, (len(declared) + 1) // 2):
        missing = [_hx(c) for c in declared if seen.get(c, 0) < PRESENT]
        problems.append(("DECLARED PALETTE ABSENT",
                         "{} of {} declared colour(s) reached the rendered pages; missing: {}. A "
                         "palette that reaches no pixel is a sentence in the plan, not a register — "
                         "either the build never applied it, or the plan was written to describe a "
                         "deck that was built some other way. (A colour held for a state this deck "
                         "never shows is a fine reason: say so in the palette line, or set "
                         "design_plan.register_pixels_waived.)"
                         .format(len(hit), len(declared), ", ".join(missing) or "-")))

    # ── 3. the "never reuse the last deck's scheme" rule, measured ACROSS decks ──────────────
    #
    # What the look history actually records, measured on this repo's real registry: 8 of 10 rows
    # carry exactly ONE hex — the canvas value — because the accents are written as prose
    # ("teal=you, amber=leverage"). A freshness check that demanded two matching hexes could
    # therefore never fire on real data, which is the worst failure mode available to a gate: it
    # would report "fresh" forever. So the ground is checked against what IS recorded, and the
    # accent half runs only for rows that name accents.
    #
    # And the ground is where the repetition actually is: seven of those eight canvases were pale
    # warm/cool near-whites. That is a house style nobody asked for.
    # 🔴 …and where a board is PRINTED, this rule yields. Measured consequence, on this repo's own
    # work: GROUND REPEAT fired on an A0 poster whose canvas matched a recent deck's, the advice
    # said "move the VALUE (dark for a light run)", and the board was rebuilt DARK — which for a
    # printed poster is the wrong direction on every count print shops name: it burns ink, dries
    # slowly and streaks, several university shops surcharge it, and light hairlines are lost
    # because print resolution does not match the screen the deck was designed on. A freshness rule
    # that cannot tell a board from a projector will keep giving that advice. So on a printed
    # surface the repeat is still REPORTED — a house style is still a house style — but the fix is
    # named in the terms that surface allows (paper warmth, accent hue, type register), and a dark
    # ground becomes a finding of its own rather than the remedy.
    printed = printed_surface(deck_dir, design)
    if printed is not None:
        facts["printed"] = printed.label

    hist = look_history(taste) if taste else []
    facts["history"] = len(hist)
    ground = field[0][0] if field else None

    # Scoped to LARGE-FORMAT boards, which is what the evidence is actually about. The ink,
    # drying, streaking and surcharge advice comes from academic-poster and wide-format print
    # guidance; an A4 sheet is 97 sq in against an A0's 1550, so the same solid ground is about a
    # sixteenth of the ink and no shop surcharges it. Extending a poster finding to a handout would
    # be reasoning past the source — and a dark A4 leave-behind, programme or menu is a legitimate
    # design. Below the threshold it is reported instead. (A1 is 775 sq in and A2 386, so 300 keeps
    # every board in and every document out.)
    LARGE_FORMAT = 300.0
    large = printed is not None and printed.w_in * printed.h_in >= LARGE_FORMAT
    if printed is not None and ground is not None and _band(ground) == "dark" and not large:
        facts["dark_note"] = (
            "canvas {} is dark on a printed {} — the ink/drying argument still applies, but the "
            "poster evidence behind the finding is about large-format boards ({:.0f} sq in here vs "
            "1550 for A0), so this is a note rather than a hold."
            .format(_hx(ground), printed.label, printed.w_in * printed.h_in))
    if large and ground is not None and _band(ground) == "dark":
        problems.append(("DARK GROUND ON A PRINTED BOARD",
                         "this {} has a dark canvas ({}). On a screen that is a legitimate "
                         "register; on paper it is the one choice print shops uniformly advise "
                         "against — it burns ink, dries slowly and streaks, several university "
                         "shops surcharge it, and light hairlines thin out because print "
                         "resolution does not match the screen this was designed on. Use a paper "
                         "ground and keep the dark for panels and figures, or record the choice "
                         "with design_plan.register_pixels_waived if the board is being produced "
                         "some other way (a fabric banner, a screen)."
                         .format(printed.label, _hx(ground))))

    if hist and ground:
        recent_rows = hist[-recent:]
        for deck, cols in recent_rows:
            if _near(cols[0], ground, SAME_LOOK):
                # On a PRINTED board a light ground is not a choice, it is the medium: the same
                # print advice that forbids a dark canvas leaves only pale stocks, and every pale
                # stock is within tolerance of every other. Blocking here would demand something
                # the surface cannot give — so the repeat is REPORTED and the freshness load moves
                # to the accent and the type, which is where a board can actually vary. A *dark*
                # ground repeat on a printed board is impossible by definition, since the rule
                # above already fires on it.
                if printed is not None and _band(ground) == "light":
                    facts["ground_note"] = (
                        "canvas {} is close to {!r}'s {} — on a printed board that is the medium, "
                        "not a house style (print wants a light stock), so it is reported rather "
                        "than held. Carry the freshness in the ACCENT and the type register."
                        .format(_hx(ground), deck, _hx(cols[0])))
                    break
                problems.append(("GROUND REPEAT",
                                 "this deck's canvas ({}) is the same value as {!r}'s ({}) — one of "
                                 "the last {} decks. The ground is the first thing seen and the "
                                 "least varied thing in the history; repeating it is how a run of "
                                 "decks acquires a house style the user never chose. {}"
                                 .format(_hx(ground), deck, _hx(cols[0]), len(recent_rows),
                                         "Vary the PAPER (a warmer or cooler stock) and the accent "
                                         "hue — not the value: a printed board wants a light "
                                         "ground, so freshness here has to come from hue and type "
                                         "rather than from going dark."
                                         if printed is not None else
                                         "Move the VALUE (dark for a light run, or a different "
                                         "paper), or record the repeat as deliberate in the "
                                         "palette line.")))
                break
        band = _band(ground)
        same_band = [d for d, c in hist[-8:] if _band(c[0]) == band]
        facts["band"] = "{} ground; {} of the last {} decks were {}".format(
            band, len(same_band), len(hist[-8:]), band)

        mine = [rgb for rgb, _ in field[:6]] + got_hue
        for deck, cols in recent_rows:
            if len(cols) < 2:
                continue                      # accents not recorded for that deck — cannot judge
            shared = [c for c in cols if any(_near(c, m, SAME_LOOK) for m in mine)]
            if len(shared) >= 2 and any(_chromatic(c) for c in shared):
                problems.append(("LAST DECK'S SCHEME",
                                 "{} of this deck's colours also identify {!r} in the look history "
                                 "({}), at least one of them a real hue rather than a shared black "
                                 "or white. Vary the accent as well as the ground, or record the "
                                 "repeat as deliberate."
                                 .format(len(shared), deck, ", ".join(_hx(c) for c in shared))))
                break
    return problems, facts


# --------------------------------------------------------------------------- selftest

def _selftest():
    import tempfile
    from PIL import Image
    ok, bad = [], []
    tmp = Path(tempfile.mkdtemp(prefix="regpix-"))

    def deck(name, ground, accents, declared_hexes, taste_rows=None):
        d = tmp / name
        (d / "render").mkdir(parents=True, exist_ok=True)
        for i in range(3):
            im = Image.new("RGB", (480, 270), ground)
            px = im.load()
            for j, a in enumerate(accents):
                for y in range(20 + j * 40, 36 + j * 40):   # a headline's worth of ink,
                    for x in range(20, 260):                # not a colour field
                        px[x, y] = a
            im.save(d / "render" / ("slide%02d.png" % (i + 1)))
        (d / ".deck-gates.json").write_text(json.dumps(
            {"design_plan": {"palette": " / ".join("#%02X%02X%02X" % c for c in declared_hexes)}}),
            encoding="utf-8")
        tp = None
        if taste_rows is not None:
            tp = d / "taste.md"
            rows = "\n".join("| 2026-01-0%d | %s | x | %s | y |" % (i + 1, nm, " ".join(
                "#%02X%02X%02X" % c for c in cols)) for i, (nm, cols) in enumerate(taste_rows))
            tp.write_text("## LOOK HISTORY\n| date | deck | look | canvas | motif |\n|---|---|---|---|---|\n"
                          + rows + "\n", encoding="utf-8")
        return d, (str(tp) if tp else None)

    # a deck whose declared register really is on the pages
    d, _ = deck("honest", (0x0A, 0x0F, 0x0A), [(0x33, 0xFF, 0x66), (0xFF, 0x5A, 0x5A)],
                [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66), (0xFF, 0x5A, 0x5A)])
    probs, facts = check(d)
    (ok if not probs else bad).append(
        "a deck whose declared colours ARE on its pages passes" if not probs
        else "honest deck flagged: {}".format(probs))

    # declared brutalist red, built in deckkit stock
    d, _ = deck("stock", (0xFF, 0xFF, 0xFF), [(0x00, 0x7C, 0xC2), (0x00, 0x3C, 0x66),
                                              (0xE3, 0x00, 0x4F)],
                [(0xC8, 0x10, 0x2E), (0x11, 0x11, 0x11)])
    codes = {c for c, _ in check(d)[0]}
    (ok if "STOCK REGISTER SHIPPED" in codes else bad).append(
        "a deck declaring one register and wearing deckkit's stock one is caught — the "
        "'never ship the default blue' rule, measured in pixels rather than asserted"
        if "STOCK REGISTER SHIPPED" in codes else "stock deck not caught: {}".format(codes))

    # a bespoke register that never reached the build (declared colours absent, no stock either)
    d, _ = deck("absent", (0x20, 0x20, 0x20), [(0x80, 0x80, 0x80)],
                [(0xC4, 0x2E, 0x1C), (0x2F, 0x5D, 0x50), (0xF2, 0xED, 0xE3)])
    codes = {c for c, _ in check(d)[0]}
    (ok if "DECLARED PALETTE ABSENT" in codes else bad).append(
        "a BESPOKE register that never reached the build is caught — the case "
        "check_style_applied.py skips by definition, because there is no preset call to find"
        if "DECLARED PALETTE ABSENT" in codes else "absent palette not caught: {}".format(codes))

    # the same scheme as a deck already in the look history
    scheme = [(0x0E, 0x1A, 0x2B), (0xC5, 0xA2, 0x53)]
    d, tp = deck("repeat", scheme[0], [scheme[1]], scheme,
                 taste_rows=[("older-deck", scheme)])
    codes = {c for c, _ in check(d, taste=tp)[0]}
    (ok if "LAST DECK'S SCHEME" in codes else bad).append(
        "a deck wearing a previous deck's scheme is caught ACROSS decks — freshness was a prose "
        "line in taste.md with nothing scoring it"
        if "LAST DECK'S SCHEME" in codes else "repeat not caught: {}".format(codes))

    d, tp = deck("fresh", (0xF2, 0xED, 0xE3), [(0xC4, 0x2E, 0x1C)],
                 [(0xF2, 0xED, 0xE3), (0xC4, 0x2E, 0x1C)],
                 taste_rows=[("older-deck", [(0x0E, 0x1A, 0x2B), (0xC5, 0xA2, 0x53)])])
    codes = {c for c, _ in check(d, taste=tp)[0]}
    (ok if "LAST DECK'S SCHEME" not in codes else bad).append(
        "...and a genuinely different scheme is NOT flagged (a check that always fires is noise)"
        if "LAST DECK'S SCHEME" not in codes else "fresh deck wrongly flagged")

    # the shape the REAL registry has: rows recording only the canvas value
    d, tp = deck("groundrepeat", (0xF3, 0xF2, 0xED), [(0xC4, 0x2E, 0x1C)],
                 [(0xF3, 0xF2, 0xED), (0xC4, 0x2E, 0x1C)],
                 taste_rows=[("deepseek-harness", [(0xF3, 0xF2, 0xED)])])
    codes = {c for c, _ in check(d, taste=tp)[0]}
    (ok if "GROUND REPEAT" in codes else bad).append(
        "a repeated CANVAS VALUE is caught from a one-hex history row — the real registry records "
        "only the canvas, so a check needing two hexes could never fire on real data"
        if "GROUND REPEAT" in codes else "ground repeat not caught: {}".format(codes))

    d, tp = deck("groundfresh", (0x0A, 0x0F, 0x0A), [(0x33, 0xFF, 0x66)],
                 [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)],
                 taste_rows=[("deepseek-harness", [(0xF3, 0xF2, 0xED)])])
    probs, facts = check(d, taste=tp)
    got = {c for c, _ in probs}
    (ok if "GROUND REPEAT" not in got and facts.get("band") else bad).append(
        "...a different value band is not flagged, and the run REPORTS the band streak "
        "({}) so a drift toward one house ground is visible before it becomes a rule"
        .format(facts.get("band")) if "GROUND REPEAT" not in got and facts.get("band")
        else "ground freshness misjudged: {} {}".format(got, facts.get("band")))

    # A deck rendered in GREYSCALE while its plan declares a hue. The count rule cannot see this:
    # a two-colour plan whose near-black ground still matches scores 1 of 2 and clears "fewer than
    # half", which is how an earlier version passed exactly this deck.
    from PIL import Image as _Im
    d, _ = deck("greyscale", (0x0A, 0x0F, 0x0A), [(0x33, 0xFF, 0x66)],
                [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)])
    for f in (d / "render").glob("*.png"):
        _Im.open(f).convert("L").save(f)
    got = {c for c, _ in check(d)[0]}
    (ok if "DECLARED HUES ABSENT" in got else bad).append(
        "a deck rendered in greyscale under a plan declaring a hue is caught — the hue IS the "
        "register; a ground and an ink are shared by half the world's decks"
        if "DECLARED HUES ABSENT" in got else "greyscale not caught: {}".format(got))

    # One unreadable PNG must be REPORTED, not allowed to abort the run: both callers wrap this
    # module in try/except, so anything raised becomes "NOT CHECKED" for the whole deck.
    d, _ = deck("corrupt", (0x0A, 0x0F, 0x0A), [(0x33, 0xFF, 0x66)],
                [(0x0A, 0x0F, 0x0A), (0x33, 0xFF, 0x66)])
    (d / "render" / "slide02.png").write_bytes(b"not a png")
    probs, facts = check(d)
    hit = "UNREADABLE RENDER" in {c for c, _ in probs} and facts.get("pages") == 2
    (ok if hit else bad).append(
        "a corrupt render is reported and the readable pages are still measured" if hit
        else "corrupt render mishandled: {} pages={}".format(probs, facts.get("pages")))

    d, _ = deck("norender", (0, 0, 0), [], [(1, 1, 1)])
    for f in (d / "render").glob("*.png"):
        f.unlink()
    codes = {c for c, _ in check(d)[0]}
    (ok if "NO RENDERS" in codes else bad).append(
        "with no renders it says so — a pixel check with no pixels must never report clean"
        if "NO RENDERS" in codes else "missing renders reported as {}".format(codes))

    d, _ = deck("noplan", (0x11, 0x22, 0x33), [(0x44, 0x55, 0x66)], [])
    probs, facts = check(d)
    (ok if "note" in facts else bad).append(
        "a palette with no hex (a locked template, a mimic) is REPORTED as not-checked rather "
        "than passed silently" if "note" in facts else "no-hex palette silently passed")

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck_dir", nargs="?")
    ap.add_argument("--renders", help="render directory (default <deck-dir>/render)")
    ap.add_argument("--taste", help="taste.md to score freshness against (registry.py prints the root)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.deck_dir:
        ap.print_help()
        return 2
    try:
        __import__("PIL")
    except ImportError:
        print("cannot run: Pillow is required (pip install -r requirements.txt)", file=sys.stderr)
        return 2
    probs, facts = check(a.deck_dir, a.renders, a.taste)
    if facts.get("waived"):
        print("design_plan records a written waiver for this check — not run.")
        return 0
    if facts.get("band"):
        print("look history: {} deck(s) — {}".format(facts.get("history", 0), facts["band"]))
    for note in ("ground_note", "dark_note"):
        if facts.get(note):
            print("  [--] " + facts[note])
    print("pages {} | field: {} | declared: {} | reached the pixels: {} | history: {}".format(
        facts.get("pages", 0),
        ", ".join(facts.get("field", [])) or "-",
        ", ".join(facts.get("declared", [])) or "none",
        ", ".join(facts.get("present", [])) or "none",
        facts.get("history", 0)))
    if facts.get("note"):
        print("  [--] " + facts["note"])
    if not probs:
        print("the register reached the pixels, and it is not a previous deck's.")
        return 0
    print("\n{} finding(s):\n".format(len(probs)))
    for code, msg in probs:
        print("  {}: {}\n".format(code, msg))
    return 1


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
