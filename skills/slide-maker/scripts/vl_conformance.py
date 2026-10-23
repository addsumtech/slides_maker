"""Build-time conformance checks of the visual-language contract, over any registered language (tests/test_vl_contract.py
runs them for all; scripts/check_vl_contract.py for the ones you name). Each returns a list of problems, empty = conforms.
Spec: docs/superpowers/specs/2026-10-15-visual-language-system-design.md §4.3."""
import contextlib
import io
import re
from pathlib import Path

import deckkit as dk
import visual_languages as vl
import vl_native as vn
from vl_contract import PAGES

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent     # the repo root holds the READMEs; an installed copy of the skill has none
_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uac00-\ud7af]")
# one token per Latin word, digit run (with its separators) and circled numeral; CJK is checked per character
_TOKEN = re.compile(r"[A-Za-z][A-Za-z'’\-]*|\d[\d.,%]*|[\u2460-\u2473]")
# what a page may number itself with (page / point / section / sheet / figure numbers): 1-2 digits, CJK numerals one
# to ten, circled one to twenty — any longer number must be the caller's (final review: digits were never examined)
_NUMERAL = re.compile(r"^(?:\d{1,2}|[一二三四五六七八九十]|[\u2460-\u2473])$")
_HONORIFIC = {"DR", "MR", "MRS", "MS", "MX", "MISS", "PROF", "SIR", "DAME", "REV", "HON"}

# the check's OWN words: every page is built from these, so anything else on the page was invented. Ordinary length
# (the long-copy corpus is test_native_generality's job); one Latin and one CJK pass.
COPY = {
    "en": dict(kicker="Annual review", title="Why every street needs a repair night",
               subtitle="What a year of evenings taught us", number="02",
               items=[("Share the tools", "One drawer feeds three tables"), ("Open the door", "No booking and no fee"),
                      ("Keep it close", "Ten minutes on foot")],
               quote="The visitor holds the screwdriver; the volunteer only guides.",
               attribution="Mara Jensen, volunteer lead", figure="1,250", label="repairs this year",
               note="Counted at the door.", line="Bring a neighbour.", body="Screwdrivers and a soldering iron on every bench.",
               caption="Photo: the hall on a Tuesday"),
    "zh": dict(kicker="年度回顾", title="为什么每条街都需要一个修理之夜", subtitle="一年的夜晚教会我们的事", number="02",
               items=[("共享工具", "一抽屉螺丝刀供三张桌子"), ("敞开大门", "不用预约也不收费"), ("就近步行", "步行十分钟可达")],
               quote="来访者握着螺丝刀，志愿者只在旁边指导。", attribution="志愿者手册", figure="98%",
               label="的物品当晚修好", note="按门口登记统计。", line="带上邻居。", body="每张桌上都有螺丝刀和电烙铁。",
               caption="摄于周二的大厅"),
}


def _pages(spec, T, pic):
    img = lambda page: dict(image=pic) if page in spec["image_pages"] else {}
    return [("cover", dict(kicker=T["kicker"], title=T["title"], subtitle=T["subtitle"], **img("cover"))),
            ("section", dict(number=T["number"], kicker=T["kicker"], title=T["title"], **img("section"))),
            ("image_text", dict(kicker=T["kicker"], title=T["title"], body=T["body"], caption=T["caption"], image=pic)),
            ("points", dict(kicker=T["kicker"], title=T["title"], items=T["items"], **img("points"))),
            ("quote", dict(quote=T["quote"], attribution=T["attribution"], **img("quote"))),
            ("data", dict(number=T["figure"], label=T["label"], note=T["note"], **img("data"))),
            ("closing", dict(title=T["title"], line=T["line"], **img("closing")))]


def painters_missing(name):
    """[why] when the language's ground or card painter is not written (or its module does not import), else []."""
    return [] if vl.ready(name) else [vl._UNREADY[name]]


def pages_missing(name, registry=None):
    reg = registry or vl.REGISTRY
    spec = reg[name]
    if spec["kind"] == "image-led":
        have = set(vl.LAYOUTS.get(name, {})) | {"points"}       # points: the shared image-led points page
        stubs = set()
    else:
        comp = vn.COMPOSERS.get(name, {})
        stubs = {p for p, fn in comp.items() if getattr(fn, "stub", False)}
        have = set(comp) - stubs
    return ["{}: page {!r} is still a stub — compose it in scripts/vl_langs/{}.py".format(name, p, name) if p in stubs
            else "{}: no composition for page {!r}".format(name, p) for p in PAGES if p not in have]


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _strings(v)


def _initials(texts):
    """What the kit may derive as avatar initials from the caller's own words: the first letters of 1-3 capitalised
    words before a comma, honorifics skipped (vl_native3.initials)."""
    out = set()
    for t in texts:
        words = [w for w in vl._words(t.split(",")[0]) if w[:1].isalpha()]   # as vl_native3.initials splits
        while words and words[0].rstrip(".").upper() in _HONORIFIC:
            words = words[1:]
        if 1 <= len(words) <= 3 and all(w[:1].isupper() for w in words):
            out.add("".join(w[0] for w in words[:2]).upper())
    return out


def allowed_tokens(name, caller_texts):
    """Upper-cased tokens (words, digit runs) and single CJK characters the caller gave, plus the language's declared
    derived words (and initials when it declares them)."""
    tok = set()
    for t in caller_texts:
        tok |= {w.upper() for w in _TOKEN.findall(t)}
        tok |= set(_CJK.findall(t))
    spec = vl.REGISTRY[name]
    for d in spec["derived"]:
        for words in d["words"].values():
            for w in words:
                tok |= {x.upper() for x in _TOKEN.findall(w)}
                tok |= set(_CJK.findall(w))
    if any(d["id"] == "initials" for d in spec["derived"]):
        tok |= _initials(caller_texts)
    return tok


def _page_tokens(slide):
    for sh in slide.shapes:
        if not sh.has_text_frame or str(getattr(sh, "name", "")).startswith(dk.A11Y_TITLE_TAG):
            continue                         # the screen readers' off-page title repeats a field
        t = sh.text_frame.text
        yield from _TOKEN.findall(t)
        yield from _CJK.findall(t)


def invented_words(name):
    """Build all seven pages on every ground from the check's own words (COPY: an English and a Chinese pass); any
    token on a page that is neither those words nor a declared derived word was invented. Inspected in memory."""
    spec = vl.REGISTRY[name]
    pic = vl.sample_picture("watercolour/rooftop-garden.jpg" if spec["samples"].get("kind") == "watercolour"
                            else "photo/hall-repair.jpg")
    probs = []
    for script, T in COPY.items():
        texts = list(_strings(T))
        tok = allowed_tokens(name, texts)
        for g in vl.VARIANTS[name]:
            prs = dk.blank_deck(10.0, 5.625)
            with contextlib.redirect_stdout(io.StringIO()):
                k = vl.use(name, prs, ground=g)
            for page, fields in _pages(spec, T, pic):
                s = k.new_slide()
                try:
                    getattr(k, page)(s, **fields)
                except NotImplementedError as e:          # a language still being authored: report, never a traceback
                    return ["{}: its pages cannot be built yet — {}".format(name, e)]
                except vl.VLTextOverflow:
                    continue                               # refused by name: not this check's business
                for t in _page_tokens(s):
                    u = t if _CJK.match(t) else t.upper()
                    if u not in tok and not _NUMERAL.match(t):
                        probs.append("{} {}/{} {}: {!r} is neither the caller's nor declared derived".format(
                            name, g, script, page, t))
    return sorted(set(probs))


def extras_not_refused(name):
    spec = vl.REGISTRY[name]
    probs = []
    for x, d in spec["extras"].items():
        if d["pages"] == "any":
            continue
        off = [p for p in PAGES if p not in d["pages"] and p != "image_text"][0]
        prs = dk.blank_deck(10.0, 5.625)
        with contextlib.redirect_stdout(io.StringIO()):
            k = vl.use(name, prs)
        fields = {"cover": dict(title="A title"), "section": dict(number="1", title="A section"),
                  "points": dict(title="Points", items=["One", "Two"]), "quote": dict(quote="A quote."),
                  "data": dict(number="3", label="a label"), "closing": dict(title="Thanks")}[off]
        try:
            getattr(k, off)(k.new_slide(), **fields, **{x: "value"})
            probs.append("{}: {}= on {} was accepted (it draws only on {})".format(name, x, off, d["pages"]))
        except NotImplementedError as e:
            probs.append("{}: {}= could not be tried on {} — {}".format(name, x, off, e))
        except (ValueError, TypeError) as e:
            if x not in str(e):
                probs.append("{}: {}= on {} was refused without naming it: {}".format(name, x, off, str(e)[:100]))
    return probs


def assets_missing(name):
    import json
    import sigs
    probs = []
    stems = [vl._sample_stem(name, g) for g in vl.VARIANTS[name]]
    # a package that ships no pictures (SkillHub accepts no image files) has no assets/: its samples live in the
    # source repository, where this check runs on them
    if vl.ASSETS.exists():
        man = json.loads((vl.ASSETS / "samples" / "manifest.json").read_text())
        for st in stems:
            if not (vl.ASSETS / "samples" / (st + ".jpg")).exists():
                probs.append("{}: no bundled sample {}.jpg".format(name, st))
            if st not in man:                   # the stem is a KEY ('tally' is a substring of 'tally-night')
                probs.append("{}: sample {} has no fingerprint in manifest.json".format(name, st))
    if not any(('"{}"'.format(name) in src) or ("'{}'".format(name) in src)
               for k, src in sigs.EXAMPLES.items() if k.startswith("vl_")):
        probs.append("{}: no sigs.py --example vl_* scaffold names it".format(name))
    ref = (SKILL / "references" / "visual-languages.md").read_text(encoding="utf-8")
    if "| `{}` |".format(name) not in ref:
        probs.append("{}: references/visual-languages.md has no table row for it".format(name))
    # the README gallery is a fixed showcase (2026-10-22): a language need not have a cell — the library page
    # (vl_library_export.py) shows every one — but the two READMEs show the same languages
    shown = {r: "samples/{}.jpg".format(name) in (REPO / r).read_text(encoding="utf-8")
             for r in ("README.md", "README_CN.md") if (REPO / r).is_file()}    # an installed copy has neither
    if len(set(shown.values())) > 1:
        has = [r for r, v in shown.items() if v][0]
        lacks = [r for r, v in shown.items() if not v][0]
        probs.append("{}: the {} gallery shows it and the {} gallery does not — show it in both or in neither "
                     "(the library page carries every language)".format(name, has, lacks))
    return probs


def suites_not_registry_driven():
    probs = []
    gen = (SKILL / "tests" / "test_native_generality.py").read_text(encoding="utf-8")
    if "for name in vl.LANGS" not in gen:
        probs.append("tests/test_native_generality.py no longer iterates vl.LANGS — a new language would skip the build matrix")
    aud = (SKILL / "tests" / "test_vl_audit_fixes.py").read_text(encoding="utf-8")
    if "vl.LANGS" not in aud:
        probs.append("tests/test_vl_audit_fixes.py no longer iterates vl.LANGS — a new language would skip the own-pages lint")
    return probs


# ── Phase 3 (spec §6.2): the recurring design defects, as checks a new language cannot slip past ──────────────────
def _built(name, ground, T, canvas=(13.333, 7.5)):
    """Every page of `name` on `ground` from the words T, in memory: [(page, slide)] (a refused page is skipped)."""
    spec = vl.REGISTRY[name]
    pic = vl.sample_picture("watercolour/rooftop-garden.jpg" if spec["samples"].get("kind") == "watercolour"
                            else "photo/hall-repair.jpg")
    prs = dk.blank_deck(*canvas)
    with contextlib.redirect_stdout(io.StringIO()):
        k = vl.use(name, prs, ground=ground)
    out = []
    for page, fields in _pages(spec, T, pic):
        s = k.new_slide()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                getattr(k, page)(s, **fields)
        except (vl.VLTextOverflow, NotImplementedError):
            continue
        out.append((page, s))
    return out, prs


def _lum(hexs):
    r, g, b = (int(hexs[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _solid_fill(sh):
    try:
        if sh.fill.type == 1:                       # MSO_FILL.SOLID
            return str(sh.fill.fore_color.rgb)
    except Exception:
        return None
    return None


def bright_slabs(name, area=0.08, lum=0.85):
    """On a DARK ground, a drawn fill brighter than `lum` covering more than `area` of the page reads as a light-mode
    leftover (cutpaper-night's white cards, interface-dark's white bezel — Phase 3 verification). Pictures are the
    caller's content; declared ornament (dk.decorative) is exempt."""
    probs = []
    for g, G in vl.REGISTRY[name]["grounds"].items():
        if not G["dark"]:
            continue
        built, prs = _built(name, g, COPY["en"])
        W, H = prs.slide_width / 914400.0, prs.slide_height / 914400.0
        for page, s in built:
            for sh in s.shapes:
                if sh.shape_type == 13:             # a picture
                    continue
                nm = str(sh.name)
                if nm.startswith("deckkit-decor") or "+decor" in nm.split(":", 1)[0]:
                    continue
                c = _solid_fill(sh)
                if not c or _lum(c) <= lum:
                    continue
                a = (sh.width / 914400.0) * (sh.height / 914400.0) / (W * H)
                if a > area:
                    probs.append("{} {} {}: a #{} fill covers {:.0%} of the page on a dark ground".format(
                        name, g, page, c, a))
    return sorted(set(probs))


def _ink_box(sh):
    bb = dk._bbox_in(sh)
    if bb is None:
        return None
    r = dk._ink_rect(sh, bb) if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip() else None
    return r[0] if r else None


def _standin_slack(sh):
    """One line of the text's largest size when any of its runs is set in a STAND-IN face, else 0: under substituted
    metrics the layout's line model and lint's can disagree by a line (broadsheet's column held one more line on CI's
    Linux faces than lint's ink box did, and its rule read 0.53in past the words — 2026-10-16)."""
    runs = [r for p in sh.text_frame.paragraphs for r in p.runs if r.text.strip()]
    if not any(r.font.name and dk._font_substituted(r.font.name) for r in runs):
        return 0.0
    return max((r.font.size.pt for r in runs if r.font.size), default=0.0) * dk._LINT_LINE_H / 72.0


def rules_past_content(name, run_on=0.4):
    """A vertical rule (a column line, a margin line, a list spine) ends within `run_on` of the lowest text it serves —
    the text beside it, in its band. Built with SHORT copy (two points) and long, on the first ground: broadsheet's
    and ink's column rules ran 2.2in under two-line columns (Phase 3 verification)."""
    probs = []
    g = list(vl.VARIANTS[name])[0]
    runs = [(tag + "-" + sc, dict(COPY[sc], items=COPY[sc]["items"][:2]) if tag == "short" else COPY[sc])
            for sc in ("en", "zh") for tag in ("short", "long")]          # CJK too: ink's vertical columns
    for tag, T in runs:
        built, prs = _built(name, g, T)
        PW, PH = prs.slide_width / 914400.0, prs.slide_height / 914400.0
        for page, s in built:
            if page not in ("points", "cover"):
                continue
            # the words a rule can serve: a grid letter or a folio (one or two glyphs) is furniture, not a column —
            # drafting's leader lines sit beside its border's zone letters (A, B, C)
            texts = [b for b in (_ink_box(sh) + (_standin_slack(sh),) if _ink_box(sh) else None for sh in s.shapes
                                 if getattr(sh, "has_text_frame", False) and len(sh.text_frame.text.strip()) > 2) if b]
            for sh in s.shapes:
                if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip():
                    continue
                try:                                 # a connector has zero width: read the raw extents
                    x, y, w, h = (v / 914400.0 for v in (sh.left, sh.top, sh.width, sh.height))
                except Exception:
                    continue
                if not (w <= 0.06 and h >= 1.5):     # a thin vertical line
                    continue
                # the page's own frame — a band at the page's edge running most of its height — serves no text: topo's
                # neatline sides read as "a rule at x=0.21 runs 2.05in past its text" (2026-10-22)
                if (x + w <= 0.06 * PW or x >= 0.94 * PW) and h >= 0.6 * PH:
                    continue
                beside = [t for t in texts if t[1] < y + h and t[1] + t[3] > y and abs((t[0] + t[2] / 2) - x) < 3.2]
                if not beside:
                    continue
                lowest = max(beside, key=lambda t: t[1] + t[3])
                low = lowest[1] + lowest[3]
                if y + h - low > run_on + lowest[4]:
                    probs.append("{} {} {} ({} copy): a rule at x={:.2f} runs {:.2f}in past its text".format(
                        name, g, page, tag, x, y + h - low))
    return sorted(set(probs))
