#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_plan_record — the art director's Design plan is a FILE the hand-off gate re-reads.

🔴 WHY THIS EXISTS. Measured 2026-11-07: in eight real runs of the current skill not one opened
`agents/slide-design.md`. The agents typed the `design_plan` fields into `.deck-gates.json`
themselves, and the gate — which required the fields — could not tell that from an art director's
work. Three of four runs of the older skill read the file, and the older skill won a blind design
comparison on three or four of four briefs. A required FIELD is satisfied by typing; a required
ARTIFACT in the shape slide-design.md's "Output — the Design plan" prescribes is not.

So the Design plan the art director returns is saved as a markdown file and recorded here:

    python3 scripts/design_plan_record.py <design-plan.md> --deck <deck-dir> --dispatched
    python3 scripts/design_plan_record.py <design-plan.md> --deck <deck-dir> \\
            --waived "<why no subagent could run>" --category no-dispatch-on-host

It checks the plan carries the Output sections (Design language · Deck rhythm · Per-slide design ·
Form ledger · Design self-verify — English or Chinese headings) and at least 15 of the 19 lettered
self-verify checks (a)–(s), then writes `design_plan.plan_file` = {path, sha256, dispatched} into
`.deck-gates.json`, keeping every other field. `render_deck.py --gate-check` re-reads the file: a
missing record, a plan edited after recording, or a self-authored plan without an allowed waiver
category blocks. `--dispatched` is a claim about what you did, like a critic review's provenance —
the gate can check the artifact, not the dispatch; on a host that can dispatch, dispatch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

GATES = ".deck-gates.json"
SECTIONS = (  # (name, accepted heading phrases, lower-cased)
    ("Design language", ("design language", "设计语言")),
    ("Deck rhythm", ("deck rhythm", "rhythm", "节奏")),
    ("Per-slide design", ("per-slide design", "per-slide", "逐页", "每页设计")),
    ("Form ledger", ("form ledger", "形式台账", "形式账本", "台账")),
    ("Design self-verify", ("self-verify", "自检")),
)
CHECK_LETTERS = "abcdefghijklmnopqrs"
# The ground plan — light/dark pacing, decided in the Deck rhythm. Measured 2026-11-08: the older skill's
# decks flipped 1–3 interior pages against the deck's ground (7 across four decks) and won a blind design
# comparison on every consistent pair; the newer decks flipped 0–1, because register kits paint the quiet
# ground on every content page, and reviewers named "dark and light pages alternate" as the difference.
SINGLE_GROUND = ("conservative", "visual-language", "template-locked", "tiny-deck")
FLIP_DELTA = 0.35       # luminance distance from the deck's median ground that reads as a flipped page
_GROUNDS_RE = re.compile(r"^\s*[-*]?\s*(?:\*\*)?(grounds|底色)(?:\*\*)?\s*[:：]\s*(.+)$", re.I | re.M)
# The hero page — one moment of type drama. Measured 2026-11-08 on the launch brief: the winning decks put
# their biggest type at 5.7–7.1x the deck's typical top size (the gallery decks 2.3–6.5x); the losing one at
# 1.6x — "tidy but quiet". A planned hero is checked on the built file: its largest type must reach HERO_RATIO
# times the median of every slide's largest type.
HERO_NONE = ("conservative", "template-locked", "tiny-deck", "image-led")
HERO_RATIO = 2.5
_HERO_RE = re.compile(r"^\s*[-*]?\s*(?:\*\*)?(hero|高潮页)(?:\*\*)?\s*[:：]\s*(.+)$", re.I | re.M)
MIN_CHECKS = 15
WAIVER_CATEGORIES = ("no-dispatch-on-host", "tiny-ask")


def parse_grounds(text: str):
    """The plan's `grounds:` line — {"flips": [slide numbers], "why"} or {"single": category, "why"},
    {"bad": raw} when it is neither, None when there is no such line."""
    m = _GROUNDS_RE.search(text or "")
    if not m:
        return None
    body = m.group(2).strip()
    parts = re.split(r"\s+[—–]\s+|\s+--?\s+", body, maxsplit=1)
    head, why = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    low = head.lower()
    if low.startswith(("flip", "翻转")):
        return {"flips": [int(n) for n in re.findall(r"\d+", head)], "why": why}
    if low.startswith(("single", "单一", "统一")):
        cat, _, reason = why.partition(":") if ":" in why else why.partition("：")
        return {"single": cat.strip().lower(), "why": reason.strip()}
    return {"bad": body}


def parse_hero(text: str):
    """The plan's `hero:` line — {"slide": n, "why"} or {"none": category, "why"}, {"bad": raw}, or None."""
    m = _HERO_RE.search(text or "")
    if not m:
        return None
    body = m.group(2).strip()
    parts = re.split(r"\s+[—–]\s+|\s+--?\s+", body, maxsplit=1)
    head, why = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    low = head.lower()
    if low.startswith(("none", "无")):
        cat, _, reason = why.partition(":") if ":" in why else why.partition("：")
        return {"none": cat.strip().lower(), "why": reason.strip()}
    n = re.findall(r"\d+", head)
    if n and (low.startswith(("slide", "第", "p")) or head.strip().isdigit()):
        return {"slide": int(n[0]), "why": why}
    return {"bad": body}


def _slide_tops(pptx_path):
    """The largest font size (pt) on each slide, groups included; 0 for a slide with no sized text."""
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from walk(sh.shapes)
            else:
                yield sh
    tops = []
    for slide in Presentation(pptx_path).slides:
        top = 0.0
        for sh in walk(slide.shapes):
            if not getattr(sh, "has_text_frame", False) or not sh.has_text_frame:
                continue
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    sz = r.font.size or p.font.size
                    if sz is not None and r.text.strip():
                        top = max(top, sz.pt)
        tops.append(top)
    return tops


def hero_faults(hero, pptx_path: str) -> list[str]:
    """[] when the planned hero page carries the deck's type drama; a named fault with a target size otherwise."""
    if not isinstance(hero, dict) or not hero.get("slide") or not pptx_path or not os.path.isfile(pptx_path):
        return []
    tops = _slide_tops(pptx_path)
    n = hero["slide"]
    if not 1 <= n <= len(tops):
        return ["the planned hero is slide %d, but the deck has %d slides" % (n, len(tops))]
    sized = sorted(t for t in tops if t > 0)
    if not sized:
        return []
    med = sized[len(sized) // 2]
    if tops[n - 1] < HERO_RATIO * med:
        return ["the hero page (slide %d) tops out at %.0f pt — %.1fx the deck's typical top size (%.0f pt). The "
                "peak needs its number or words at %.0f pt or more (%.1fx), so it reads as the moment the deck "
                "exists for" % (n, tops[n - 1], tops[n - 1] / med, med, HERO_RATIO * med, HERO_RATIO)]
    return []


def validate(text: str) -> list[str]:
    """Faults in a Design plan's shape; [] when it carries slide-design.md's Output sections."""
    if not text.strip():
        return ["the design plan file is empty"]
    heads = [l.strip().lstrip("#").strip().lower() for l in text.splitlines() if re.match(r"^\s*#{1,6}\s", l)]
    faults = []
    for name, phrases in SECTIONS:
        if not any(p in h for h in heads for p in phrases):
            faults.append("missing the `%s` section (agents/slide-design.md → \"Output — the Design plan\")" % name)
    g = parse_grounds(text)
    if g is None:
        faults.append("no `grounds:` line in the Deck rhythm — write `grounds: flips <slide>, <slide> — <why>` "
                      "(the interior beats that flip against the deck's ground, as a family) or `grounds: single "
                      "— <%s>: <why>`" % " | ".join(SINGLE_GROUND))
    elif "bad" in g:
        faults.append("the `grounds:` line must start with `flips` or `single`, not %r" % g["bad"][:60])
    elif "flips" in g and len(g["flips"]) < 2:
        faults.append("`grounds: flips` names %d page — flips come as a family (two or more interior beats); a "
                      "lone flip reads as an error, not rhythm" % len(g["flips"]))
    elif "single" in g and g["single"] not in SINGLE_GROUND:
        faults.append("`grounds: single` needs a category from: %s (got %r)"
                      % (", ".join(SINGLE_GROUND), g["single"]))
    h = parse_hero(text)
    if h is None:
        faults.append("no `hero:` line in the Deck rhythm — write `hero: slide <n> — <the number or words it "
                      "is built around>` or `hero: none — <%s>: <why>`" % " | ".join(HERO_NONE))
    elif "bad" in h:
        faults.append("the `hero:` line must be `slide <n>` or `none`, not %r" % h["bad"][:60])
    elif "none" in h and h["none"] not in HERO_NONE:
        faults.append("`hero: none` needs a category from: %s (got %r)" % (", ".join(HERO_NONE), h["none"]))
    found = set(re.findall(r"\(([a-s])\)", text))
    if len(found) < MIN_CHECKS:
        faults.append("carries %d of the 19 Design self-verify checks (a)–(s); the plan is not ready until "
                      "at least %d are answered" % (len(found), MIN_CHECKS))
    return faults


def ground_faults(grounds, render_dir: str) -> list[str]:
    """Planned flips the BUILT deck does not carry, read from the rendered pages; [] when they hold or when
    there is nothing to measure (no renders, or a single-ground plan)."""
    if not isinstance(grounds, dict) or not grounds.get("flips"):
        return []
    import glob
    files = sorted(glob.glob(os.path.join(render_dir or "", "slide[0-9]*.png")))
    if not files:
        return []
    from PIL import Image, ImageStat
    lum = [ImageStat.Stat(Image.open(f).convert("L").resize((96, 54))).mean[0] / 255 for f in files]
    med = sorted(lum)[len(lum) // 2]
    out = []
    for n in grounds["flips"]:
        if not 1 <= n <= len(lum):
            out.append("planned flip on slide %d, but the deck has %d slides" % (n, len(lum)))
        elif abs(lum[n - 1] - med) <= FLIP_DELTA:
            out.append("planned flip on slide %d is not built — its page reads on the deck's own ground "
                       "(luminance %.2f vs the deck's %.2f). Paint the flipped ground "
                       "(`dk.slide_background(slide, <deep colour>)`, ink re-chosen for it) or change the plan"
                       % (n, lum[n - 1], med))
    return out


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _resolve(path, deck_dir):
    return path if os.path.isabs(path) else os.path.join(deck_dir, path)


def gate_faults(design: dict, deck_dir: str) -> list[str]:
    """What the hand-off gate refuses about the recorded art-director plan; [] when it holds."""
    pf = design.get("plan_file") if isinstance(design, dict) else None
    if not isinstance(pf, dict) or not pf.get("path"):
        return ["no art-director plan on record. Dispatch agents/slide-design.md (`python3 scripts/"
                "dispatch_brief.py prompt --brief <brief> --role design`), save the Design plan it returns "
                "as a .md file, and record it: `python3 scripts/design_plan_record.py <design-plan.md> "
                "--deck %s --dispatched`" % (deck_dir or ".")]
    path = _resolve(pf["path"], deck_dir)
    if not os.path.isfile(path):
        return ["the recorded design plan %s does not exist — record the file the art director returned"
                % pf["path"]]
    faults = []
    if pf.get("sha256") != _sha(path):
        faults.append("the design plan %s changed after it was recorded — re-run design_plan_record.py on "
                      "the version the deck was built from" % pf["path"])
    with open(path, encoding="utf-8", errors="replace") as f:
        faults += validate(f.read())
    if pf.get("dispatched") is not True:
        if pf.get("waived_category") not in WAIVER_CATEGORIES or not str(pf.get("waived") or "").strip():
            faults.append("the design plan is SELF-AUTHORED (dispatched: false) with no allowed waiver — "
                          "dispatch the art director, or record why one could not run: --waived \"<why>\" "
                          "--category %s" % " | ".join(WAIVER_CATEGORIES))
    return faults


def record(plan_path, deck_dir, dispatched, waived=None, category=None) -> dict:
    if not os.path.isfile(plan_path):
        raise SystemExit("[design_plan_record] no such file: %s" % plan_path)
    with open(plan_path, encoding="utf-8", errors="replace") as f:
        faults = validate(f.read())
    if faults:
        raise SystemExit("[design_plan_record] %s is not a complete Design plan:\n  - %s"
                         % (plan_path, "\n  - ".join(faults)))
    if not dispatched and (category not in WAIVER_CATEGORIES or not (waived or "").strip()):
        raise SystemExit("[design_plan_record] a self-authored plan needs --waived \"<why>\" and --category "
                         "one of: %s" % ", ".join(WAIVER_CATEGORIES))
    gp = os.path.join(deck_dir, GATES)
    try:
        with open(gp, encoding="utf-8") as f:
            gates = json.load(f)
    except FileNotFoundError:
        gates = {}
    except ValueError as e:
        raise SystemExit("[design_plan_record] %s is not valid JSON: %s" % (gp, e))
    design = gates.get("design_plan")
    if not isinstance(design, dict):
        design = {}
    abs_plan, abs_deck = os.path.abspath(plan_path), os.path.abspath(deck_dir)
    rel = os.path.relpath(abs_plan, abs_deck) if abs_plan.startswith(abs_deck + os.sep) else abs_plan
    with open(plan_path, encoding="utf-8", errors="replace") as f:
        grounds = parse_grounds(f.read())
    with open(plan_path, encoding="utf-8", errors="replace") as f:
        hero = parse_hero(f.read())
    pf = {"path": rel, "sha256": _sha(plan_path), "dispatched": bool(dispatched), "grounds": grounds,
          "hero": hero}
    if not dispatched:
        pf.update(waived=waived, waived_category=category)
    design["plan_file"] = pf
    gates["design_plan"] = design
    with open(gp, "w", encoding="utf-8") as f:
        json.dump(gates, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return pf


# ── Density: whose decision a dense deck is (formerly density_choice.py) ─────────────────────────────
# density_choice — whose decision a dense deck is. Imported by the density gate in render_deck.py.
#
# 🔴 WHY THIS EXISTS. Measured 2026-11-07/08: twelve real runs of the current skill shipped presented
# decks at a median of 83–168 words a slide by writing `"density": {"waived": "<my reason>"}`, while the
# older skill's runs sat at 54–66 and won a blind design comparison on 11 of 11 consistent pairs. Dense
# pages force small type and leave no room for a hero page — exactly what the reviewers faulted. The
# waiver was meant to record a USER who wants a read-alone deck; it had become the author's way past
# the budget.
#
# So a density waiver counts only when the recorded interview density is text-heavy AND the user chose
# it. A picks row marked `delegated` is the author's preference, not the user's. Balanced (图文均衡 — the
# default) and diagram-heavy decks get no free-text waiver: move the prose to the speaker notes or split
# the slide. Too sparse is a design smell too, but only a note — a statement slide is meant to be bare.

TEXT_HEAVY = ("text-heavy", "text heavy", "textheavy", "文字为主", "文字多", "文字密集", "重文字")
SPARSE_MEDIAN = 6       # words a slide; below this, across 4+ slides, the deck says almost nothing


def _density_pick(gates):
    iv = gates.get("interview") if isinstance(gates, dict) else None
    picks = (iv or {}).get("picks") if isinstance(iv, dict) else None
    for p in picks if isinstance(picks, list) else ():
        if isinstance(p, dict) and str(p.get("axis") or "").lower() == "density":
            return str(p.get("source") or "").strip().lower()
    return None


def density_waiver_allowed(gates: dict) -> tuple[bool, str]:
    """(True, "") when a density waiver records the user's own text-heavy choice; else (False, why)."""
    iv = gates.get("interview") if isinstance(gates, dict) else None
    dens = str((iv or {}).get("density") or "").strip().lower() if isinstance(iv, dict) else ""
    if not any(k in dens for k in TEXT_HEAVY):
        return False, ("the recorded density is %r, not text-heavy — a waiver is for a user who asked for "
                       "a read-alone deck. Move the prose into the speaker notes or split the slide "
                       "(balanced / 图文均衡 is one short sentence per point beside a visual)."
                       % (dens or "unrecorded"))
    if _density_pick(gates) == "delegated":
        return False, ("text-heavy was a `delegated` pick — your preference, not the user's — so it cannot "
                       "waive the budget. Cut to the budget, or ask the user.")
    return True, ""


def density_sparse_note(median: float, total: int) -> str | None:
    """A note (never a block) when a deck of 4+ slides says almost nothing on its pages."""
    if total >= 4 and median < SPARSE_MEDIAN:
        return ("density: very sparse — median %s words a slide. Fine for statement slides; on content "
                "slides a short takeaway line beside the visual reads better than a label alone." % median)
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plan")
    ap.add_argument("--deck", required=True)
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument("--dispatched", action="store_true", help="the plan came from a dispatched art director")
    who.add_argument("--waived", help="why no art director could be dispatched")
    ap.add_argument("--category", choices=WAIVER_CATEGORIES)
    a = ap.parse_args(argv)
    try:
        pf = record(a.plan, a.deck, a.dispatched, a.waived, a.category)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    print("[design_plan_record] recorded %s (%s)" % (pf["path"], "dispatched" if pf["dispatched"]
                                                     else "SELF-AUTHORED — " + pf["waived_category"]))
    return 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a character, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
