#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""density_choice — whose decision a dense deck is. Imported by the density gate in render_deck.py.

🔴 WHY THIS EXISTS. Measured 2026-11-07/08: twelve real runs of the current skill shipped presented
decks at a median of 83–168 words a slide by writing `"density": {"waived": "<my reason>"}`, while the
older skill's runs sat at 54–66 and won a blind design comparison on 11 of 11 consistent pairs. Dense
pages force small type and leave no room for a hero page — exactly what the reviewers faulted. The
waiver was meant to record a USER who wants a read-alone deck; it had become the author's way past
the budget.

So a density waiver counts only when the recorded interview density is text-heavy AND the user chose
it. A picks row marked `delegated` is the author's preference, not the user's. Balanced (图文均衡 — the
default) and diagram-heavy decks get no free-text waiver: move the prose to the speaker notes or split
the slide. Too sparse is a design smell too, but only a note — a statement slide is meant to be bare.
"""
from __future__ import annotations

TEXT_HEAVY = ("text-heavy", "text heavy", "textheavy", "文字为主", "文字多", "文字密集", "重文字")
SPARSE_MEDIAN = 6       # words a slide; below this, across 4+ slides, the deck says almost nothing


def _density_pick(gates):
    iv = gates.get("interview") if isinstance(gates, dict) else None
    picks = (iv or {}).get("picks") if isinstance(iv, dict) else None
    for p in picks if isinstance(picks, list) else ():
        if isinstance(p, dict) and str(p.get("axis") or "").lower() == "density":
            return str(p.get("source") or "").strip().lower()
    return None


def waiver_allowed(gates: dict) -> tuple[bool, str]:
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


def sparse_note(median: float, total: int) -> str | None:
    """A note (never a block) when a deck of 4+ slides says almost nothing on its pages."""
    if total >= 4 and median < SPARSE_MEDIAN:
        return ("density: very sparse — median %s words a slide. Fine for statement slides; on content "
                "slides a short takeaway line beside the visual reads better than a label alone." % median)
    return None
