#!/usr/bin/env python3
"""Create image-generation prompt manifests for slide visual plates.

This helper does not call an image model. It turns a slide outline into a repeatable
prompt plan that an agent can feed to its image generation skill/tool, then save the
selected assets back into the deck folder.
"""
import argparse
import json
import os
import re
from pathlib import Path


HEADING_RE = re.compile(r"^\s{0,3}#{1,3}\s+(.+?)\s*$")
SLIDE_HEADING_RE = re.compile(r"^(?:slide|page)\s*(\d+)?\s*[:.-]\s*(.+)$", re.I)
NUMBERED_HEADING_RE = re.compile(r"^(\d+)\s*[:.-]\s*(.+)$")


def _clean(s):
    return re.sub(r"\s+", " ", s.strip())


def _sentence(s):
    s = _clean(s)
    return s if not s or s[-1] in ".!?" else s + "."


def parse_outline(text):
    """Return a list of {'title', 'notes'} parsed from markdown-ish slide headings.

    Any markdown heading (``#``/``##``/``###``) starts a new slide. A ``Slide N:`` or
    ``N:`` prefix is stripped from the title when present, but plain headings such as
    ``## Background`` are recognized too.
    """
    slides = []
    current = None
    for raw in text.splitlines():
        m = HEADING_RE.match(raw)
        if m:
            heading = m.group(1).strip()
            sm = SLIDE_HEADING_RE.match(heading) or NUMBERED_HEADING_RE.match(heading)
            title = _clean(sm.group(2)) if sm else _clean(heading)
            if current:
                slides.append(current)
            current = {"title": title or f"Slide {len(slides) + 1}", "notes": []}
        elif current:
            current["notes"].append(raw.rstrip())
    if current:
        slides.append(current)
    if slides:
        return [{"title": s["title"], "notes": _clean("\n".join(s["notes"]))} for s in slides]

    chunks = [c for c in re.split(r"\n\s*\n", text) if _clean(c)]
    return [{"title": f"Slide {i + 1}", "notes": _clean(c)} for i, c in enumerate(chunks)]


def parse_facts(text):
    """Parse a VISUAL FACTS file: `## <slide heading>` followed by `- <observed attribute>` lines.

    This is the written output of the research step (references/image-generation.md, "Visual
    research"): the model FETCHES real reference photos of the subject, LOOKS at them, and writes
    down what the thing actually looks like. Without it a prompt can only carry the subject's NAME,
    and a name is exactly what a generator will happily illustrate wrongly — the topicality gate in
    generate_images_codex.py counts subject nouns and cannot know that a 7T scanner has a bore and
    a cryostat, or that this campus tower is grey with red panels.

    Keys are matched case-insensitively, and by substring in either direction, so `## EWI tower`
    matches the slide `The EWI tower at night` without anyone maintaining exact strings."""
    facts, key = {}, None
    for raw in (text or "").splitlines():
        m = HEADING_RE.match(raw)
        if m:
            key = _clean(m.group(1))
            facts.setdefault(key, [])
            continue
        line = raw.strip()
        if key and line.startswith(("-", "*", "•")):
            v = _clean(line[1:])
            if v:
                facts[key].append(v)
    return {k: v for k, v in facts.items() if v}


def facts_for(slide, idx, facts):
    """Facts for this slide: by heading (either direction), else by 1-based index."""
    if not facts:
        return []
    title = (slide.get("title") or "").strip().lower()
    for k, v in facts.items():
        kl = k.strip().lower()
        if kl and (kl in title or title in kl):
            return v
    for k, v in facts.items():
        if k.strip().lower() in (str(idx), "slide %d" % idx):
            return v
    return []


def build_prompt(slide, idx, *, deck_size, style, calm_zone, facts=()):
    title = slide["title"]
    notes = slide.get("notes", "")
    calm = f" Leave a broad low-detail calm region for editable slide text: {calm_zone}." if calm_zone else ""
    style_line = f"Visual style: {style}." if style else "Visual style: polished presentation-grade editorial visual, cohesive and modern."
    # OBSERVED, not remembered. These lines were written by a model that looked at license-clear
    # reference photographs of the real subject — so they go in as binding attributes, ahead of the
    # style line, and they are the difference between "a robot arm" and THIS machine.
    fact_lines = ([f"Observed subject facts (from reference photographs — these BIND, honour every "
                   f"one): {'; '.join(facts)}."] if facts else [])
    return "\n".join([
        "Use case: productivity-visual",
        f"Asset type: text-free visual plate for a {deck_size} presentation slide",
        f"Primary request: create a visual that supports slide {idx}: {title}.",
        f"Slide context: {_sentence(notes or title)}",
        *fact_lines,
        style_line,
        f"Composition/framing: wide slide composition, designed to be cropped with fit='cover' or placed as a side panel.{calm}",
        "Content rules: no readable words, letters, numbers, formulas, UI labels, chart labels, logos, watermarks, or citations.",
        "Fidelity rules: do not invent source figures, data charts, medical/scientific evidence, product UI, or branded marks. If the slide needs those, use real source assets instead.",
        "Avoid: clutter behind future text, fake annotations, fake charts, tiny illegible details, stock-photo cliches, low-resolution texture.",
    ])


def main():
    ap = argparse.ArgumentParser(description="Create imagegen prompts for slide visual plates.")
    ap.add_argument("outline", help="Markdown outline listing ONLY the slides that earn a "
                    "generated plate (one heading per plate) — NOT the whole deck.")
    ap.add_argument("out_dir", help="Directory for image_prompt_manifest.json and image_prompts.md.")
    ap.add_argument("--count", type=int, default=None, help="Optional cap on the number of plates; "
                    "truncates the parsed list (does NOT pad). Pass only plate-worthy slides.")
    ap.add_argument("--deck-size", default="16:9", help="Deck aspect ratio or size label.")
    ap.add_argument("--style", default="", help="Shared art direction to carry across the plated slides.")
    ap.add_argument("--calm-zone", default="", help="Where generated plates should leave quiet space, e.g. left third.")
    ap.add_argument("--prefix", default="slide", help="Output filename prefix.")
    ap.add_argument("--facts", help="A VISUAL FACTS markdown file (`## <slide heading>` + `- <observed "
                    "attribute>` bullets), written after LOOKING at real reference photos of the "
                    "subject — see references/image-generation.md 'Visual research'. Without it a "
                    "prompt carries the subject's name and nothing about its actual appearance.")
    args = ap.parse_args()

    text = Path(args.outline).read_text(encoding="utf-8")
    slides = parse_outline(text)
    facts_map = parse_facts(Path(args.facts).read_text(encoding="utf-8")) if args.facts else {}
    # Cap the number of plates if asked, but never PAD: padding to a deck-length count would
    # invent a context-free plate per slide — the one-image-per-slide habit we want to avoid.
    # Feed an outline of only the plate-worthy slides instead.
    if args.count is not None:
        slides = slides[:args.count]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, slide in enumerate(slides, start=1):
        filename = f"{args.prefix}-{i:02d}.png"
        _f = facts_for(slide, i, facts_map)
        prompt = build_prompt(slide, i, deck_size=args.deck_size, style=args.style,
                              calm_zone=args.calm_zone, facts=_f)
        manifest.append({
            "slide": i,
            "title": slide["title"],
            "filename": filename,
            "path": os.path.join(str(out_dir), filename),
            "prompt": prompt,
        })

    (out_dir / "image_prompt_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md = ["# Image Generation Prompts", ""]
    for item in manifest:
        md.extend([
            f"## Slide {item['slide']}: {item['title']}",
            "",
            f"Expected file: `{item['filename']}`",
            "",
            "```text",
            item["prompt"],
            "```",
            "",
        ])
    (out_dir / "image_prompts.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {len(manifest)} prompts to {out_dir}")


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    main()
