#!/usr/bin/env python3
"""assemble — robustly combine independently-authored SECTIONS into one deck.

The naive way to parallelize a big deck is to build N separate .pptx files and merge
them. Don't: python-pptx has no clean slide-copy API, so merging means deep-copying
XML, relationships, and embedded images across packages — fragile and bug-prone.

This is the robust alternative. Each section is a *module* exposing `build_section(prs)`
that APPENDS its slides to a shared Presentation. We build ONE base deck and run every
section into it, in order. Result: a single file, no XML merge, and — because every
section imports the SAME `style` module (palette, font, chrome, layout constants) —
zero cross-section drift. That's what protects coherence while sections are authored
in parallel by different subagents.

Workflow this supports (see references/large-deck-orchestration.md):
  style.py              # single source of truth (palette/FONT/helpers) — one owner
  section_01_intro.py   # def build_section(prs): ...   (imports style)
  section_02_method.py  # def build_section(prs): ...   (imports style)
  ...
  -> orchestrator runs build_deck(out, [section_01..., section_02...], template=...)
  -> then the critic panel reviews the ASSEMBLED deck.

Each section subagent can self-check while authoring by rendering JUST its section
(`preview_section`), then returns its finalized module for assembly.

CONTRACT (don't break it): all sections AND the single `style.py` live in ONE directory,
and every section does `import style`. Python caches the first `import style` in
sys.modules, so giving sections *separate* style.py files in different dirs would silently
make them all use the first one — exactly the drift this tool prevents. One shared
style.py is the design; keep it that way.
"""
import importlib.util
import os
import sys

# make deckkit importable whether or not the caller already added scripts/ to path
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _load(path):
    """Import a section module from a file path (unique module name per file)."""
    path = os.path.abspath(path)
    name = "section_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # ensure the section's own dir is importable (so `import style` resolves)
    sec_dir = os.path.dirname(path)
    if sec_dir not in sys.path:
        sys.path.insert(0, sec_dir)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build_section"):
        raise AttributeError(f"{path} defines no build_section(prs)")
    return mod


def _base(template=None, width_in=10.0, height_in=10.0 * 9 / 16):
    from deckkit import blank_deck, open_template
    return open_template(template) if template else blank_deck(width_in, height_in)


def build_deck(out_path, section_paths, *, template=None,
               width_in=10.0, height_in=10.0 * 9 / 16):
    """Assemble the final deck: run every section module, in order, into one deck.

    out_path: where to save the .pptx.
    section_paths: ordered list of module files, each defining build_section(prs).
    template: optional .pptx to build on (else a blank 16:9 deck).
    Returns the final slide count."""
    prs = _base(template, width_in, height_in)
    for path in section_paths:
        _load(path).build_section(prs)
    prs.save(out_path)
    return len(prs.slides._sldIdLst)


def preview_section(section_path, out_path, *, template=None,
                    width_in=10.0, height_in=10.0 * 9 / 16):
    """Render JUST one section to its own deck, so its authoring subagent can render +
    self-critique it in isolation before it's assembled. Same base/style as the final
    deck, so what you see is what you'll get after assembly."""
    prs = _base(template, width_in, height_in)
    _load(section_path).build_section(prs)
    prs.save(out_path)
    return out_path


if __name__ == "__main__":
    # tiny CLI: assemble.py OUT.pptx section_a.py section_b.py ...
    if len(sys.argv) < 3:
        print("usage: python assemble.py OUT.pptx section_1.py [section_2.py ...]")
        raise SystemExit(2)
    out, sections = sys.argv[1], sys.argv[2:]
    n = build_deck(out, sections)
    print(f"assembled {len(sections)} sections -> {out} ({n} slides)")
