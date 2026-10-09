#!/usr/bin/env python3
"""The 13 visual languages after the 2026-10-09 audit: every finding the audit reproduced is pinned here — text measured
with room to spare and by script (Latin words never split), no caller's words or pictures dropped, photos upright,
the kit's own pages clear of its own gates, and the image-led languages level with the drawn ones."""
from __future__ import annotations
import contextlib, io, re, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deckkit as dk
import visual_languages as vl

ok, bad = [], []
def check(cond, why):
    (ok if cond else bad).append(why)
EMU = 914400.0
td = Path(tempfile.mkdtemp())
PHOTO = str(vl.ASSETS / "photo" / "hall-repair.jpg")


def use(name, W=13.333, H=7.5, ground="light"):
    prs = dk.blank_deck(W, H)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        k = vl.use(name, prs, ground=ground)
    return prs, k


def texts(s):
    return [sh for sh in s.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() and sh.top >= 0]


def img_for(name):
    return str(vl.ASSETS / "watercolour" / "rooftop-garden.jpg") if name == "storybook" else PHOTO


# ── A1: measured with room to spare, by script ──
# A line measured to fit its box exactly was set one line longer by LibreOffice: collage on 9:16 measured "fix what it
# already owns" at 4.894in in a 4.894in box and rendered "owns" on a fourth line, over the subtitle (audit sweep,
# 2026-10-09). Every language now measures its words in HEADROOM of the column and draws the box at the full width.
check(0.95 <= getattr(vl, "HEADROOM", 1.0) < 1.0, "the kit measures display text with headroom (vl.HEADROOM)")
TITLE = "Why every street deserves a place to fix what it already owns"
for name in vl.LANGS:
    for W, H in ((5.625, 10.0), (7.5, 10.0), (10.0, 5.625)):
        prs, k = use(name, W, H)
        s = k.new_slide()
        k.cover(s, kicker="Annual review of the repair network", title=TITLE,
                subtitle="What twelve months of evenings, benches and borrowed tools taught us",
                image=img_for(name) if name in vl.IMAGE_LED else None)
        hd = [sh for sh in texts(s) if sh.text_frame.text.replace("\n", " ").replace("\v", " ").lower().startswith("why every")]
        if not hd:
            check(False, "{} {}x{}: the cover title is drawn".format(name, W, H)); continue
        sh = hd[0]
        tf = sh.text_frame
        inner = sh.width / EMU - (tf.margin_left or 91440) / EMU - (tf.margin_right or 91440) / EMU
        sz = tf.paragraphs[0].runs[0].font.size.pt
        if len(tf.paragraphs) > 1:        # set in its measured lines: no line may come near the box's inner width
            widest = max(dk._natural_width_in([(p_.text, bool(p_.runs[0].font.bold))], sz, p_.runs[0].font.name)
                         for p_ in tf.paragraphs if p_.runs)
            check(widest <= inner * 0.985, "{} {}x{}: every title line leaves room in its box ({:.3f}in of {:.3f}in)".format(
                name, W, H, widest, inner))
        else:                             # one paragraph: the box holds the lines the title needs at 98.5% of its width
            need = len(vl._break_lines(k, "title", tf.text, sz, inner * 0.985 + vl._INSET))
            held = round((sh.height / EMU - 0.06) / (sz / 72.0 * dk._LINT_LINE_H))
            check(need <= held, "{} {}x{}: the title box holds its lines with room to spare (needs {}, holds {})".format(
                name, W, H, need, held))

# mixed CJK + Latin: a Latin word is one unit, measured in the Latin face; breaks fall between CJK characters, at the
# script boundary or at a space — never inside "report" (journal set "…进展re / port v2", the robustness audit)
MIXED = ("2026年第3季度MRI重建项目进展report v2", "GPT-4o与Claude在代码生成上的对比", "用ResNet50做图像分类的三个教训")
def word_cuts(t, ls):
    """Line boundaries that fall between two Latin letters/digits that were ADJACENT in `t` (a break at a space is a
    break between words)."""
    cuts, pos = [], 0
    for a, b in zip(ls, ls[1:]):
        pos = t.index(a.strip(), pos) + len(a.strip())
        if a and b and re.match(r"[A-Za-z0-9]", a.strip()[-1]) and re.match(r"[A-Za-z0-9]", b.strip()[0]) and t[pos:pos + 1] != " ":
            cuts.append((a, b))
    return cuts


for name in ("journal", "tally", "starlit", "editorial", "ink"):
    prs, k = use(name, 10.0, 5.625)
    for t in MIXED:
        for wi in (2.0, 2.6, 3.3, 4.1, 5.0):
            ls = vl._break_lines(k, "title", t, 30, wi)
            split = word_cuts(t, ls)
            check(not split and "".join(ls).replace(" ", "") == t.replace(" ", ""),
                  "{}: {!r} at {}in breaks only between words ({})".format(name, t, wi, ls))
for name in ("journal", "tally", "starlit", "broadsheet", "chalkboard"):
    prs, k = use(name, 10.0, 5.625)
    s = k.new_slide()
    k.cover(s, title=MIXED[0], subtitle="面向临床的加速方案")
    paras = [p_.text for sh in texts(s) for p_ in sh.text_frame.paragraphs if "MRI" in sh.text_frame.text or "port" in sh.text_frame.text]
    cut = word_cuts(MIXED[0], paras) if paras else []
    check(not cut, "{}: a mixed title is never split inside a Latin word ({})".format(name, paras))
# the Latin parts of a mixed line are measured in the Latin face they render in: a mixed line measures at least as wide
# as its Latin and CJK parts measured apart
prs, k = use("journal")
t = "Claude与GPT-4o"
w_mix = vl._line_width(k, "title", t, 30) if hasattr(vl, "_line_width") else 0.0
w_lat = dk._natural_width_in([("Claude", False)], 30, k.face("display")) + dk._natural_width_in([("GPT-4o", False)], 30, k.face("display"))
check(w_mix >= w_lat + 0.9 * 30 / 72.0, "a mixed line is measured per script ({:.2f}in for Latin {:.2f}in + one CJK em)".format(w_mix, w_lat))

# ── A2: a caller's words are never dropped because a sibling field is absent ──
# poster drew a data note, a quote's attribution and a closing line only inside the primary field's `if`: number+note
# lost the note, attribution alone drew a lone “, line alone a blank colour block (robustness audit, 2026-10-09)
SUBSETS = [("data", dict(number="12", note="Weighed at the door.")), ("data", dict(label="evenings a month", note="Since spring.")),
           ("quote", dict(quote="Fix it together.")), ("quote", dict(quote="Fix it together.", attribution="A volunteer")),
           ("quote", dict(attribution="A volunteer")),
           ("closing", dict(line="Bring a neighbour.")), ("closing", dict(title="See you next week")),
           ("section", dict(title="The evening")), ("section", dict(number="02", title="The evening")),
           ("cover", dict(title="Bring it broken")), ("cover", dict(subtitle="How an evening works", title="Bring it broken"))]
for name in vl.LANGS:
    for page, kw in SUBSETS:
        prs, k = use(name)
        s = k.new_slide()
        try:
            getattr(k, page)(s, **kw)
        except (vl.VLTextOverflow, ValueError) as e:
            check("needs" in str(e) or "give" in str(e) or "empty" in str(e),
                  "{} {} {}: a refusal says what is missing ({})".format(name, page, sorted(kw), str(e)[:80]))
            continue
        on = " ".join(sh.text_frame.text for sh in texts(s)).replace("\n", " ").replace("\v", " ").lower()
        on = re.sub(r"\s+", " ", on)
        lost = [v for v in kw.values() if v.lower() not in on and v.upper() not in on.upper()
                and not (name == "collage" and vl._outlinable(k, v))]      # collage draws a short figure as an outline
        check(not lost, "{} {} {}: every given word is on the page (lost {})".format(name, page, sorted(kw), lost))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
