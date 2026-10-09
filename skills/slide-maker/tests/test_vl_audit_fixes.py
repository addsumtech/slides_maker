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

# ── A5: a deck built from a language's own pages passes that language's own prohibitions ──
# starlit's data page drew two oversized primitives (the glow behind the figure, the horizon) and its own CONFETTI guard
# blocked every landscape starlit deck at hand-off (docs audit, 2026-10-09) — its declared atmosphere is not a hero shape
import check_visual_language as cvl
FULL = [("cover", dict(kicker="Annual review", title="Every street needs a night for fixing things", subtitle="How it works")),
        ("section", dict(number="02", title="The evening")),
        ("image_text", dict(title="Tools on every bench", body="Volunteers sit beside you.", caption="The hall")),
        ("points", dict(title="How it works", items=[("Bring it", "Anything that switches on."), ("Fix it", "Your hands do the work.")])),
        ("quote", dict(quote="The visitor holds the screwdriver.", attribution="A volunteer")),
        ("data", dict(number="12", label="evenings this year", note="Counted at the door.")),
        ("closing", dict(title="See you next week", line="Bring a neighbour."))]
EXTRA_FOR = {"tally": {"points": {"tags": ["A", "B"]}}, "broadsheet": {"points": {"tags": ["A", "B"]}}}
for name in vl.LANGS:
    for W, H in ((13.333, 7.5), (7.5, 10.0)):
        for ground in vl.VARIANTS[name]:
            prs, k = use(name, W, H, ground)
            for page, kw in FULL:
                if page == "points" and name in vl.IMAGE_LED and not hasattr(k, "_has_points"):
                    pass
                kw = dict(kw, **EXTRA_FOR.get(name, {}).get(page, {}))
                if page == "image_text":
                    kw["image"] = img_for(name)
                try:
                    getattr(k, page)(k.new_slide(), **kw)
                except ValueError:
                    pass                                   # (image-led points: C1)
            path = td / "own_{}_{}_{}.pptx".format(name, ground, int(W))
            prs.save(str(path))
            with contextlib.redirect_stdout(io.StringIO()):
                found, _f = cvl.check(str(path), {"name": name, "fonts": "both", "ground": ground})
            forb = [x for x in found if "FORBIDDEN" in str(x) or "forbids" in str(x)]
            check(not forb, "{} {} {}x{}: a deck of its own pages passes its own prohibitions ({})".format(
                name, ground, W, H, [str(x)[:90] for x in forb[:1]]))

# ── A6: a picture stays visible on a dark ground ──
# ink's night ground multiplied the picture by the dark/light paper ratio (~0.13) and the photo all but vanished (both
# audits, 2026-10-09); the paper tint is for moving a watercolour's paper to a LIGHT or mid ground (storybook meadow)
src_mean = np.asarray(Image.open(PHOTO).convert("L")).mean()
for name in ("ink", "storybook"):
    for ground in vl.VARIANTS[name]:
        prs, k = use(name, ground=ground)
        s = k.new_slide(); k.image_text(s, title="A photo", body="B", image=PHOTO)
        pics = [Image.open(io.BytesIO(sh.image.blob)).convert("RGBA") for sh in s.shapes if sh.shape_type == 13]
        pics = [im for im in pics if im.size[0] > 200]
        if not pics:
            check(False, "{} {}: the photo is placed".format(name, ground)); continue
        a = np.asarray(pics[0]).astype(float)
        core = a[a.shape[0] // 4: 3 * a.shape[0] // 4, a.shape[1] // 4: 3 * a.shape[1] // 4]
        lum = (0.299 * core[..., 0] + 0.587 * core[..., 1] + 0.114 * core[..., 2]).mean()
        check(lum >= 0.55 * src_mean, "{} {}: the photo keeps its light ({:.0f} of the source's {:.0f})".format(name, ground, lum, src_mean))

# ── B4: the palette --gates prints is one the register-pixels gate can find on the pages ──
# it declared the TEXT accents (a kicker's red, a hairline's gold): broadsheet, soft dusk, ink night and cutpaper night
# failed DECLARED HUES ABSENT on the bundled samples themselves (docs audit, 2026-10-09). The hues a language really
# paints are measured on its rendered sample pages (assets/vl/samples/hues.json, written by --sample-sheet).
import json as _json
import check_register_pixels as crp
HF = vl.ASSETS / "samples" / "hues.json"
hues = _json.loads(HF.read_text(encoding="utf-8")) if HF.exists() else {}
for name in vl.LANGS:
    for g in vl.VARIANTS[name]:
        stem = vl._sample_stem(name, g)
        P = vl.VARIANTS[name][g]["palette"]
        mine = {c.upper() for c in list(P["accents"]) + list(P["text_accents"]) + [P["ground"], P["ink"]]}
        rec = hues.get(stem)
        check(isinstance(rec, list) and all(h.lstrip("#").upper() in mine for h in rec),
              "{}: its painted hues are recorded from its sample pages, each one of its palette ({})".format(stem, rec))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            vl._print_gates(name, str(td / "gates_{}".format(stem)), "a topic", "both", ground=g)
        line = [l_ for l_ in buf.getvalue().splitlines() if "design_plan.palette" in l_]
        got = {h.upper() for h in re.findall(r"#([0-9A-Fa-f]{6})", line[0])} if line else set()
        want = {P["ground"].upper(), P["ink"].upper()} | {h.lstrip("#").upper() for h in (rec or [])}
        check(got == want, "{}: --gates declares the ground, the ink and the hues it paints ({} vs {})".format(stem, sorted(got), sorted(want)))

# ── B1: the screen readers' title, parked off the page, is not text in a platform's safe zone ──
# every visual-language page on 小红书 3:4 / 9:16 failed SAFE ZONE "text sits -1.00in from the top" — the a11y title
# (non-Claude agent run, 2026-10-09)
import check_surface as csf
for name in vl.LANGS:
    for fmtname, (W, H) in (("red", (7.5, 10.0)), ("story", (5.625, 10.0))):
        prs, k = use(name, W, H)
        k.cover(k.new_slide(), kicker="A repair café", title="Bring it broken, take it home working", subtitle="How it works",
                image=img_for(name) if name in vl.IMAGE_LED else None)
        k.closing(k.new_slide(), title="See you next week", line="Bring a neighbour.",
                  image=img_for(name) if name in vl.IMAGE_LED else None)
        path = td / "safe_{}_{}.pptx".format(name, fmtname)
        prs.save(str(path))
        with contextlib.redirect_stdout(io.StringIO()):
            res = csf.check(str(path), fmtname)
        found = res[0] if isinstance(res, tuple) else res
        off = [x for x in found if x[0] == "SAFE ZONE" and "-1.00in" in x[1]]
        check(not off, "{} {}: the off-page a11y title is not SAFE ZONE text ({})".format(name, fmtname, [x[1][:60] for x in off[:1]]))

# ── B2: a deck of a language's own pages is clean under the delivery lint (lint_deck) ──
# the kit's own furniture failed it: soft's blob behind the photo, ink's sun over a ridge, cutpaper's cards tucked into
# the hills, chalkboard's doodle (OVERLAP), ink's figure inside its ensō (INVISIBLE TEXT: the ring's bounding box read as
# the figure's backing) — an agent told "fix every finding" could not (both audits, 2026-10-09)
import lint_deck as _ld
DX = {"tally": {"points": {"tags": ["A", "B", "C"]}, "data": {"total": "20"}}, "broadsheet": {"points": {"tags": ["A", "B", "C"]}},
      "chalkboard": {"cover": {"doodle": "lucide:wrench"}, "closing": {"doodle": "lucide:wrench"}, "points": {"ordered": True}},
      "ink": {"cover": {"seal": "修"}}}
for name in vl.LANGS:
    for W, H in ((13.333, 7.5), (7.5, 10.0)):
        for ground in vl.VARIANTS[name]:
            prs, k = use(name, W, H, ground)
            for page, kw in FULL:
                if page == "points" and name in vl.IMAGE_LED and not getattr(vl, "IMAGE_LED_POINTS", False):
                    continue
                kw = dict(kw, **DX.get(name, {}).get(page, {}))
                if page in ("points",) and name in ("tally", "broadsheet"):
                    kw["items"] = kw["items"][:3] + [("Take it home", "Or put it on the list.")][:max(0, len(kw["tags"]) - len(kw["items"]))]
                if page == "image_text" or (name in vl.IMAGE_LED and page in ("cover", "closing")):
                    kw["image"] = img_for(name)
                getattr(k, page)(k.new_slide(), **kw)
            path = td / "lint_{}_{}_{}.pptx".format(name, ground, int(W))
            prs.save(str(path))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                hard = _ld.lint(str(path), static_ok=True)
            why = [l_.strip()[:110] for l_ in buf.getvalue().splitlines()
                   if re.match(r"\s+slide \d+: [A-Z]", l_) and "[warn]" not in l_ and "[stats]" not in l_]
            check(hard == 0, "{} {} {}x{}: a deck of its own pages has no hard lint finding ({})".format(name, ground, W, H, why[:2]))

# ── B3: a near-uniform texture ground is a solid ground for contrast ──
# tally's grid, chalkboard's slate, collage's grain, the drafting grid and the night sky are pictures painted as the
# slide background; lint called their colour unknowable and estimated it from the render, where the glyphs' own
# antialiasing scored white-on-navy at 2.8:1 — a TEXT-ON-IMAGE warning on every page (audits, 2026-10-09). The picture
# is measured instead: 99%+ of its pixels sit on one colour, which is the backing (a photo stays unknowable).
from pptx import Presentation as _Prs
for name, ground in (("tally", "night"), ("chalkboard", "light"), ("collage", "slate"), ("drafting", "cyanotype"), ("starlit", "light")):
    prs, k = use(name, ground=ground)
    k.cover(k.new_slide(), title="A title on the ground", subtitle="And a line")
    path = td / "bg_{}.pptx".format(name)
    prs.save(str(path))
    p2 = _Prs(str(path))
    rec = _ld._slide_bg_box(p2.slides[0], 13.333, 7.5)
    want = vl.VARIANTS[name][ground]["palette"]["ground"].upper()
    got = (rec or {}).get("fill")
    check(rec is not None and not rec.get("unk") and bool(got) and _ld._contrast(got, want) < 1.15,
          "{} {}: its texture ground reads as the solid {} (got {})".format(name, ground, want, got))
prs = dk.blank_deck(13.333, 7.5)
s = dk.add_slide(prs)
import native_art as _na
_part, _rid = s.part.get_or_add_image_part(PHOTO)
_na._bg(s, '<a:blipFill><a:blip r:embed="{}"/><a:stretch><a:fillRect/></a:stretch></a:blipFill>'.format(_rid))
path = td / "bg_photo.pptx"; prs.save(str(path))
rec = _ld._slide_bg_box(_Prs(str(path)).slides[0], 13.333, 7.5)
check(rec is not None and rec.get("unk") and not rec.get("fill"), "a photo background stays unknowable ({})".format(rec and rec.get("fill")))

# ── a printed board takes a language's LIGHTEST ground: poster's default is a saturated blue, its paper ground is light
# (it said poster "has none" — docs agent, 2026-10-09); starlit and chalkboard are dark on both and say so
for name in vl.LANGS:
    prs = dk.blank_deck(8.27, 11.69)
    g, why = vl._auto_ground(name, prs)
    lums = {k_: vl._lum(vl.VARIANTS[name][k_]["palette"]["ground"]) for k_ in vl.VARIANTS[name]}
    best = max(lums, key=lums.get)
    check(g == best, "{}: a printed board takes its lightest ground ({} picked, {} is lightest)".format(name, g, best))
    if lums[best] < 0.2:
        check("dark" in why, "{}: a printed board says the page prints dark ({})".format(name, why[:80]))

for line in ok:
    print("  ok   " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
sys.exit(1 if bad else 0)
