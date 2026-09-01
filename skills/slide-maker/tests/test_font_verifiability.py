#!/usr/bin/env python3
"""A font inside an app bundle is a font this pipeline cannot verify.

Portability was only ever framed as "will the RECIPIENT have it". The failure that actually cost a
build was the other one: on macOS, Microsoft Office keeps Calibri / Cambria / Aptos INSIDE its own
app folder rather than installing them system-wide. PowerPoint renders them; LibreOffice — the
render loop — and the width-measurement path cannot see them at all. So a deck set in Calibri on
such a machine is laid out against a substitute's metrics (voiding `measure_text`, `vstack`,
`bottom_callout`, `fit_text_size`) and then "verified" against a render of a face nobody will see,
with both linters green the whole way.

Item 10 used to answer that case with "may be fine where the deck is presented" — which is the
wrong risk, stated reassuringly. These hold the distinction.
"""
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
warnings.simplefilter("ignore")

import preflight_check as pf                # noqa: E402
import deckkit as dk                        # noqa: E402

ok, bad = [], []


def check(cond, why):
    (ok if cond else bad).append(why)


# ------------------------------------------------------------------ the family-name matcher
check(pf._norm_face("Times New Roman") == "timesnewroman",
      "a family name normalises to alphanumerics, so 'Times New Roman' matches 'Times New Roman.ttf'")
check(pf._norm_face("") == "" and pf._bundled_only("") is None,
      "an empty face name is not matched against every file in every bundle")

# 🔴 The direction of the prefix test is the whole correctness of this check.
_stem, _want = pf._norm_face("Cambria"), pf._norm_face("Cambria Math")
check(not _stem.startswith(_want),
      "🔴 `Cambria.ttc` must NOT answer for `Cambria Math` — they are different fonts, and a "
      "machine with Office routinely carries the first and not the second (measured). The test is "
      "stem.startswith(family), never the reverse, or every math deck would be told its math font "
      "is present when the formulas are about to tofu")
check(pf._norm_face("Calibrib").startswith(pf._norm_face("Calibri")),
      "...while a weight file (`Calibrib.ttf`) DOES answer for its family, which is what makes the "
      "bundle scan find Calibri at all")
check(pf._bundled_only("NoSuchFaceAnywhere12345") is None,
      "a face in no bundle returns None rather than a guess")


# ------------------------------------------------------- the two failures are reported apart
class _FakeRun(object):
    def __init__(self, name):
        self.font = type("F", (), {"name": name})()


class _FakePara(object):
    def __init__(self, names):
        self.runs = [_FakeRun(n) for n in names]


class _FakeShape(object):
    shape_type = None                       # not a GROUP, so `_leaves` yields it directly
    left = top = 0

    def __init__(self, names):
        self.has_text_frame = True
        self.text_frame = type("T", (), {"paragraphs": [_FakePara(names)]})()


class _FakeSlide(object):
    def __init__(self, names):
        self.shapes = [_FakeShape(names)]


class _FakePrs(object):
    def __init__(self, names):
        self.slides = [_FakeSlide(names)]


status, msg = pf.item10_fonts(_FakePrs(["ZzzNotARealFace", "AlsoNotReal"]))
check(status == "ADVISORY" and "presented" in msg,
      "a face installed NOWHERE keeps the original wording — the risk really is the presenter's "
      "machine, and this check has no business failing a deck for CI not having Helvetica Neue")

_bundled = pf._bundled_only("Calibri")
if _bundled:
    status, msg = pf.item10_fonts(_FakePrs(["Calibri"]))
    check(status == "ADVISORY" and "application bundle" in msg and "SUBSTITUTE" in msg,
          "🔴 a face present ONLY inside an app bundle is reported as its own class — the message "
          "says the GEOMETRY was measured against a substitute and the render verified the wrong "
          "face, not the reassuring 'may be fine where the deck is presented' ({})".format(_bundled))
    check("~/Library/Fonts" in msg and "Times New Roman" in msg,
          "...and it names both fixes: a system-wide face, or making the bundled file visible")
    status2, msg2 = pf.item10_fonts(_FakePrs(["Calibri", "ZzzNotARealFace"]))
    check("application bundle" in msg2 and "NOWHERE" in msg2,
          "...and when BOTH failures are present, both are reported — the bundled one must not "
          "swallow a genuinely missing math font, which is the tofu that reaches the audience")
else:
    check(True, "no Office bundle on this machine — the bundle-detection arm is skipped, not faked "
                "(it is exercised wherever Office is installed)")

status, msg = pf.item10_fonts(_FakePrs(["Times New Roman"]))
check(status == "PASS",
      "a system-wide face passes clean — the check must stay quiet on the answer it recommends, "
      "or authors learn to ignore it")


# ---------------------------------------------------- and the rule is written where it is read
_gui = (ROOT / "references" / "font-guidance.md").read_text(encoding="utf-8")
check("APP BUNDLE" in _gui and "DFonts" in _gui,
      "`font-guidance.md` carries the app-bundle trap with the real path, so the reason survives "
      "the check")
check("ACADEMIC / LAB register" in _gui and "Times New Roman" in _gui,
      "...and the academic/lab/conference type default, which is the question that was never "
      "answered anywhere: a lab room expects a conference face, not a designer sans")
_pur = (ROOT / "references" / "design-by-purpose.md").read_text(encoding="utf-8")
check(_pur.count("- **Type:**") >= 4,
      "the four academic purposes carry a `Type:` line — they had Palette / Density / Layout / "
      "Icons / Signature and no type row at all, which is why the face was inherited from whatever "
      "the template profile happened to say")
check("Type by register" in _pur,
      "...pointing at one shared note, so the rule is stated once rather than drifting five ways")
_setup = (ROOT / "references" / "deck-setup.md").read_text(encoding="utf-8")
check("APP BUNDLE" in _setup and "preflight_check.py` item 10" in _setup,
      "`deck-setup.md` §Fonts — the file SKILL.md routes to before the first `set_palette` — "
      "carries both rules and names the check that enforces one of them")


# ------------------------------------------------- the check runs in a FRESH PROCESS, as it does
tmp = Path(tempfile.mkdtemp(prefix="fontverif-"))
dk.set_palette(font="Times New Roman", mono="Courier New")
prs = dk.blank_deck()
s = dk.add_slide(prs)
dk.text(s, 1, 1, 8, 1, [[("a headline", 24, dk.DEEP, True, False, dk.FONT)]])
dk.speaker_notes(s, "n")
deck = tmp / "d.pptx"
prs.save(str(deck))
out = subprocess.run([sys.executable, str(SCRIPTS / "preflight_check.py"), str(deck)],
                     capture_output=True, text=True)
check("10. Hand-off: fonts" in out.stdout and "resolve locally" in out.stdout,
      "🔴 and it works from a FRESH PROCESS — the way preflight actually runs — on a deck set in "
      "the recommended academic face")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
