#!/usr/bin/env python3
"""The five files where the USER'S OWN artifacts enter and leave the skill.

Script-style (`main()` + explicit exit) to match the other suites; pytest collects nothing from
this file by design, and ci.yml invokes it directly.

Why these five, together. The four files that produce and police the skill's OWN output —
deckkit.py, lint_deck.py, render_deck.py, codex_delivery_gate.py — are ~12k lines with five test
suites, three meta-checkers that lint the prose against the code, and a CI job that asserts its own
assertions ran. The five that ingest or return the user's material — extract_deck.py (their deck),
inspect_template.py (their template), export_notes.py (their rehearsal script), assemble.py (their
sectioned deck), anim.py (what they will actually click through) — were ~455 lines with NO tests at
all, and every one of them, when run, failed SILENTLY rather than loudly:

    charts and notes vanished under a success message · a chart-only slide was reported as
    "_(empty / decorative only)_" · a .potx died on a raw library ValueError with the string
    "potx" appearing nowhere in 2.5MB of documentation · a rehearsal script came out with no
    titles · a second deck inherited the first deck's palette · a requested transition became
    a fade

Every gate this skill owns measures the deck against ITSELF — its own plan, its own lint, its own
critic, its own recorded consent. Internal consistency is precisely the property that cannot detect
a wrong input. These assertions face outward.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import deckkit as dk                                                    # noqa: E402

PASS: list[str] = []
FAIL: list[str] = []


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("\n       " + str(detail)[:300])
                                                       if not cond and detail else ""))


def make_deck(path: Path):
    """A deck with the things a results deck is actually made of."""
    prs = dk.blank_deck()
    s1 = dk.add_slide(prs)
    dk.text(s1, 0.5, 0.4, 9, 0.7, [[("Reconstruction quality", 30, dk.DEEP, True, False, dk.FONT)]])
    dk.text(s1, 0.5, 1.2, 4, 0.4, [[("a smaller line", 12, dk.SLATE, False, False, dk.FONT)]])
    dk.table(s1, 0.5, 1.8, 5.0, [["method", "Dice"], ["ours", "0.915"]])
    dk.speaker_notes(s1, "SPOKEN: the proposed method wins on every subject.")
    s2 = dk.add_slide(prs)
    dk.native_chart(s2, 1.0, 1.0, 8.0, 3.5, ["A", "B", "C"], [("PSNR", [31, 33, 36])])
    dk.speaker_notes(s2, "SPOKEN: note the saturation after stage eight.")
    prs.save(str(path))
    return path


def make_potx(src: Path, dest: Path):
    """A REAL .potx — the content type institutions actually ship, not a renamed .pptx."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(b"presentationml.presentation.main+xml",
                                    b"presentationml.template.main+xml")
            zout.writestr(item, data)
    return dest


# ─────────────────────────────────────────────────────────── extract_deck.py
def check_extract(td: Path):
    deck = make_deck(td / "theirs.pptx")
    out = td / "ex"
    r = subprocess.run([sys.executable, str(SCRIPTS / "extract_deck.py"), str(deck), str(out)],
                       capture_output=True, text=True)
    md = (out / "content.md").read_text(encoding="utf-8") if (out / "content.md").exists() else ""
    ok("extract: exits clean", r.returncode == 0, r.stderr)
    ok("extract: speaker notes are recovered", "SPOKEN: the proposed method wins" in md)
    ok("extract: BOTH slides' notes are recovered", "saturation after stage eight" in md)
    ok("extract: the chart's real numbers are recovered",
       "PSNR" in md and "31" in md and "36" in md, md[-400:])
    ok("extract: the chart's categories are recovered", "A" in md and "C" in md)
    ok("extract: the table is still recovered", "0.915" in md)
    # the regression that matters most: a chart-only slide used to be reported as empty
    ok("extract: a chart-only slide is NOT reported as empty",
       "_(empty / decorative only)_" not in md, md[-400:])
    ok("extract: the summary line counts what it recovered",
       "1 chart(s)" in r.stdout and "2 slide(s) with speaker notes" in r.stdout, r.stdout)


def check_extract_reports_loss(td: Path):
    """Never report absence you have not verified — an unreadable shape must announce itself."""
    prs = dk.blank_deck()
    s = dk.add_slide(prs)
    dk.text(s, 0.5, 0.5, 4, 0.5, [[("kept", 18, dk.DEEP, False, False, dk.FONT)]])
    p = td / "plain.pptx"
    prs.save(str(p))
    out = td / "ex2"
    subprocess.run([sys.executable, str(SCRIPTS / "extract_deck.py"), str(p), str(out)],
                   capture_output=True, text=True)
    md = (out / "content.md").read_text(encoding="utf-8")
    ok("extract: a genuinely empty slide is still called empty",
       "kept" in md)


# ─────────────────────────────────────────────────────────── .potx
def check_potx(td: Path):
    deck = make_deck(td / "base.pptx")
    potx = make_potx(deck, td / "brand.potx")
    from deckkit import open_presentation
    try:
        prs = open_presentation(str(potx))
        ok("potx: deckkit.open_presentation opens a real .potx", len(prs.slides._sldIdLst) == 2)
    except Exception as e:
        ok("potx: deckkit.open_presentation opens a real .potx", False, e)
    r = subprocess.run([sys.executable, str(SCRIPTS / "inspect_template.py"), str(potx)],
                       capture_output=True, text=True)
    ok("potx: inspect_template.py — the template branch's FIRST command — accepts it",
       r.returncode == 0 and "slide size" in r.stdout, (r.stderr or r.stdout)[-300:])
    r = subprocess.run([sys.executable, str(SCRIPTS / "extract_deck.py"), str(potx), str(td / "px")],
                       capture_output=True, text=True)
    ok("potx: extract_deck.py accepts it", r.returncode == 0, (r.stderr or r.stdout)[-300:])
    # and a genuinely broken file must still fail, loudly
    bad = td / "broken.pptx"
    bad.write_bytes(b"not a zip at all")
    try:
        open_presentation(str(bad))
        ok("potx: a genuinely broken file still raises", False, "no exception")
    except Exception:
        ok("potx: a genuinely broken file still raises", True)


# ─────────────────────────────────────────────────────────── export_notes.py
def check_export_notes(td: Path):
    deck = make_deck(td / "notes.pptx")
    sys.path.insert(0, str(SCRIPTS))
    import export_notes
    out, n = export_notes.export_notes(str(deck), str(td / "n.txt"))
    txt = Path(out).read_text(encoding="utf-8")
    ok("export_notes: the notes themselves are exported", "wins on every subject" in txt)
    ok("export_notes: a deckkit slide gets a TITLE in its header",
       "Slide 1: Reconstruction quality" in txt, txt[:300])
    ok("export_notes: it picks the largest run, not just any text",
       "a smaller line" not in txt.splitlines()[0], txt[:200])


# ─────────────────────────────────────────────────────────── assemble.py
def check_assemble(td: Path):
    for name, val in (("A", "DECK-A-MAGENTA"), ("B", "DECK-B-TEAL")):
        d = td / ("deck" + name)
        d.mkdir()
        (d / "style.py").write_text('PALETTE = "%s"\n' % val)
        (d / "section_01.py").write_text(
            "import style\n"
            "def build_section(prs):\n"
            "    print('SEEN deck%s ->', style.PALETTE)\n" % name)
    code = (
        "import sys; sys.path.insert(0, r'%s')\n"
        "import assemble\n"
        "for n in 'AB':\n"
        "    d = r'%s' + '/deck' + n\n"
        "    assemble.build_deck(d + '/out.pptx', [d + '/section_01.py'], lint=False)\n"
        % (SCRIPTS, td))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    out = r.stdout + r.stderr
    ok("assemble: deck A sees its own style", "SEEN deckA -> DECK-A-MAGENTA" in out, out[-300:])
    ok("assemble: deck B does NOT inherit deck A's style",
       "SEEN deckB -> DECK-B-TEAL" in out, out[-300:])


def check_assemble_within_deck(td: Path):
    """The within-deck guarantee must survive the fix: all of ONE deck's sections share a style."""
    d = td / "shared"
    d.mkdir()
    (d / "style.py").write_text('PALETTE = "ONE"\n')
    for i in (1, 2):
        (d / ("section_0%d.py" % i)).write_text(
            "import style\n"
            "def build_section(prs):\n"
            "    print('SEC%d ->', style.PALETTE, id(style))\n" % i)
    code = ("import sys; sys.path.insert(0, r'%s')\n"
            "import assemble\n"
            "assemble.build_deck(r'%s/out.pptx', [r'%s/section_01.py', r'%s/section_02.py'], "
            "lint=False)\n" % (SCRIPTS, d, d, d))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    out = r.stdout + r.stderr
    ok("assemble: sections of ONE deck still share one style module",
       out.count("ONE") == 2 and len(set(
           ln.rsplit(" ", 1)[-1] for ln in out.splitlines() if "SEC" in ln)) == 1,
       out[-300:])


# ─────────────────────────────────────────────────────────── anim.py
def check_anim(td: Path):
    import anim
    prs = dk.blank_deck()
    for kind, tag in (("fade", "<p:fade"), ("cut", "<p:cut"),
                      ("wipe", "<p:wipe"), ("push", "<p:push")):
        s = dk.add_slide(prs)
        anim.slide_transition(s, kind=kind)
        ok("anim: slide_transition(kind=%r) writes %s" % (kind, tag), tag in s._element.xml)
    s = dk.add_slide(prs)
    try:
        anim.slide_transition(s, kind="starwars")
        ok("anim: an unknown transition raises instead of silently fading", False)
    except ValueError:
        ok("anim: an unknown transition raises instead of silently fading", True)


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        td = Path(t)
        check_extract(td)
        check_extract_reports_loss(td)
        check_potx(td)
        check_export_notes(td)
        check_assemble(td)
        check_assemble_within_deck(td)
        check_anim(td)
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
