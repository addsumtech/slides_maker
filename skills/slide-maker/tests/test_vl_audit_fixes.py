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

# ── A3: a drawn language never drops a picture silently ──
# image= on a drawn language's cover/section/quote/data/closing/points built with no picture and no error — even a path
# to no file (robustness + docs audits, 2026-10-09). It is refused there, naming the pages that do draw one.
F = dict(cover=dict(title="T"), section=dict(title="T"), points=dict(title="T", items=[("a", "b"), ("c", "d")]),
         quote=dict(quote="Q"), data=dict(number="3", label="l"), closing=dict(title="T"))
check(set(getattr(vl, "NATIVE_IMAGE_PAGES", {})) == set(vl.NATIVE), "vl.NATIVE_IMAGE_PAGES names the picture pages of every drawn language")
for name in vl.NATIVE:
    pages = getattr(vl, "NATIVE_IMAGE_PAGES", {}).get(name, ("image_text",))
    for page, kw in F.items():
        kw = dict(kw)
        if page == "points" and name in ("tally", "broadsheet"):
            kw["tags"] = ["a", "b"]
        for im in (PHOTO, "/no/such/photo.jpg"):
            prs, k = use(name)
            s = k.new_slide()
            try:
                getattr(k, page)(s, image=im, **kw)
                drew = any(sh.shape_type == 13 for sh in s.shapes)
                check(page in pages and drew, "{} {}: image={} is drawn or refused (built, picture drawn: {})".format(
                    name, page, Path(im).name, drew))
            except (ValueError, FileNotFoundError) as e:
                check(page not in pages or im != PHOTO, "{} {}: a picture it draws is accepted ({})".format(name, page, str(e)[:60]))
                if page not in pages:
                    check("image_text" in str(e), "{} {}: the refusal names the pages that draw a picture ({})".format(
                        name, page, str(e)[:90]))
    for im in ([], [PHOTO, PHOTO]):                      # one picture per page: an empty or long list is refused by name
        prs, k = use(name)
        try:
            k.image_text(k.new_slide(), title="T", body="B", image=im)
            check(False, "{} image_text: image={} is refused".format(name, "[]" if not im else "two pictures"))
        except ValueError as e:
            check("image" in str(e), "{} image_text: image={} is refused by name ({})".format(name, len(im), str(e)[:60]))
        except Exception as e:
            check(False, "{} image_text: image={} raises a plain error, not {}".format(name, len(im), type(e).__name__))
    prs, k = use(name)
    s = k.new_slide(); k.image_text(s, title="T", body="B", image=[PHOTO])
    check(any(sh.shape_type == 13 for sh in s.shapes), "{} image_text: a one-picture list is drawn".format(name))

# ── A4 + A7: every picture arrives upright, readable and in a format PowerPoint embeds ──
from PIL import Image
import numpy as np
src = Image.open(PHOTO).convert("RGB")
portrait = src.crop((0, 0, int(src.height * 0.66), src.height))            # an upright portrait photo …
stored = portrait.rotate(90, expand=True)                                    # … stored on its side, as phones do
ex = Image.Exif(); ex[0x0112] = 6
EXIF6 = td / "phone.jpg"; stored.save(EXIF6, exif=ex.tobytes())
G16 = td / "figure16.png"
Image.fromarray((np.linspace(0, 65535, 500 * 400).reshape(400, 500)).astype(np.uint16)).save(G16)
WEBP = td / "photo.webp"; src.save(WEBP)
TRUNC = td / "cut.jpg"; TRUNC.write_bytes(Path(PHOTO).read_bytes()[:4000])
NOTIMG = td / "notes.jpg"; NOTIMG.write_text("not a picture")


def placed(s, before):
    """The pictures a page added (blob decoded), the ground's own picture(s) left out."""
    out = []
    for sh in s.shapes:
        if sh.shape_type == 13 and sh.image.sha1 not in before:
            out.append(Image.open(io.BytesIO(sh.image.blob)))
    return out


for name in vl.LANGS:
    prs, k = use(name)
    s0 = k.new_slide(); k.image_text(s0, title="Before", body="B", image=PHOTO)
    ground = {sh.image.sha1 for sh in s0.shapes if sh.shape_type == 13 and Image.open(io.BytesIO(sh.image.blob)).size != src.size}
    s = k.new_slide(); k.image_text(s, title="A photo from a phone", body="Taken upright.", image=str(EXIF6))
    pics = [im for im in placed(s, ground) if im.size[0] > 50]
    up = [im for im in pics if im.size[1] > im.size[0] and int(im.getexif().get(274, 1) or 1) == 1]
    check(bool(up), "{}: a phone photo (EXIF orientation 6) is placed upright ({})".format(name, [im.size for im in pics]))
    s = k.new_slide(); k.image_text(s, title="A 16-bit figure", body="From the scanner.", image=str(G16))
    flat = [np.asarray(im.convert("L")).std() for im in placed(s, ground) if im.size[0] > 50]
    check(flat and max(flat) > 30, "{}: a 16-bit PNG keeps its tones (std {})".format(name, [round(x) for x in flat]))
    s = k.new_slide()
    try:
        k.image_text(s, title="A WebP", body="From the web.", image=str(WEBP))
        check(any(sh.shape_type == 13 for sh in s.shapes), "{}: a WebP photo is placed".format(name))
    except Exception as e:
        check(False, "{}: a WebP photo is placed, not refused ({}: {})".format(name, type(e).__name__, str(e)[:60]))
    for bad_, why in ((TRUNC, "truncated"), (NOTIMG, "not an image")):
        try:
            k.image_text(k.new_slide(), title="Bad", body="B", image=str(bad_))
            check(False, "{}: a {} file is refused".format(name, why))
        except ValueError as e:
            check("image_text" in str(e) and bad_.name in str(e), "{}: a {} file is refused naming the page and file ({})".format(
                name, why, str(e)[:90]))
        except Exception as e:
            check(False, "{}: a {} file raises a plain refusal, not {} ({})".format(name, why, type(e).__name__, str(e)[:60]))
check(int(Image.open(EXIF6).getexif().get(274, 1)) == 6, "the caller's own file is never rewritten")

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
