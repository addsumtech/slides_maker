#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Citations for an academic deck: read from the .bib, never retyped — and never invented.

WHY THIS EXISTS. A defense, a journal club, a lab meeting and a grant talk all cite, and every
citation on those slides was, until now, a string somebody typed onto a slide by hand. Measured
across this skill before this file: `sources_page` renders a list of STRINGS and `source_note`
renders a provenance line of STRINGS; nothing read a bibliography, nothing linked an in-text marker
to a reference list, and nothing could tell a correct year from a remembered one. Retyping is
exactly where a year drifts by one and an author gets dropped — and on a slide, a misattributed
result is a claim about a real person's work.

So the bibliography is the source of truth: `parse_bibtex` reads it, `in_text` and
`format_reference` derive the marker and the line from the SAME entry, and
`scripts/check_citations.py` checks the built deck against it. Nothing here accepts a hand-typed
reference, because a hand-typed reference is the failure this file exists for.

🔴 IT REFUSES RATHER THAN FILLING IN. An entry with no author, no title or no year is not formatted
with `n.d.` or `Anon.` — it raises, naming the key and the field. Under this skill's never-invent
floor, a plausible-looking citation is worse than a missing one: a reader cannot tell it from a real
one, and neither can the author six months later.

The two styles are SLIDE reference lines — enough for a reader to identify the work and find it —
not a journal's copy-edited style. A deck is not a manuscript; if a venue demands exact APA/IEEE
punctuation, the manuscript is where that belongs.

    python3 scripts/citations.py refs.bib                    # what parsed, and what is incomplete
    python3 scripts/citations.py refs.bib --style author-year --keys smith2020,jones2019
    python3 scripts/citations.py --selftest

Exit 0 clean · 1 entries this module refuses to format · 2 could not run.
"""
from __future__ import annotations

import argparse
import re
import sys

STYLES = ("numeric", "author-year")
REQUIRED = ("author", "title", "year")          # the three a reader needs to FIND the work
VENUE_FIELDS = ("journal", "booktitle", "publisher", "school", "institution", "howpublished")

# Enough LaTeX to render the names that actually appear in a bibliography. The FALLBACK is the
# general part: an accent this table does not know still yields the base letter, never `\v{s}`.
_ACCENTS = {
    ('"', "a"): "ä", ('"', "o"): "ö", ('"', "u"): "ü", ('"', "e"): "ë", ('"', "i"): "ï",
    ("'", "a"): "á", ("'", "e"): "é", ("'", "i"): "í", ("'", "o"): "ó", ("'", "u"): "ú",
    ("'", "c"): "ć", ("'", "n"): "ń", ("'", "s"): "ś", ("'", "z"): "ź",
    ("`", "a"): "à", ("`", "e"): "è", ("`", "i"): "ì", ("`", "o"): "ò", ("`", "u"): "ù",
    ("^", "a"): "â", ("^", "e"): "ê", ("^", "i"): "î", ("^", "o"): "ô", ("^", "u"): "û",
    ("~", "a"): "ã", ("~", "n"): "ñ", ("~", "o"): "õ",
    ("c", "c"): "ç", ("c", "s"): "ş", ("v", "s"): "š", ("v", "c"): "č", ("v", "z"): "ž",
    ("r", "a"): "å", ("H", "o"): "ő", ("=", "a"): "ā", ("=", "e"): "ē", ("=", "o"): "ō",
    (".", "z"): "ż", ("u", "a"): "ă", ("k", "a"): "ą", ("k", "e"): "ę", ("l", "l"): "ł",
}
_LIGATURES = {r"\ss": "ß", r"\ae": "æ", r"\AE": "Æ", r"\oe": "œ", r"\OE": "Œ",
              r"\o": "ø", r"\O": "Ø", r"\aa": "å", r"\AA": "Å", r"\l": "ł", r"\L": "Ł",
              r"\&": "&", r"\%": "%", r"\$": "$", r"\_": "_", r"\#": "#",
              "--": "\u2013", "---": "\u2014", r"\textendash": "\u2013"}


class Incomplete(ValueError):
    """An entry this module will not format, because formatting it would mean inventing a field."""


def _deaccent(s):
    """LaTeX escapes -> the characters they stand for; an UNKNOWN accent keeps its base letter."""
    # The DOTLESS letters first: an accent over an i is written `{\'\i}` in a real bibliography
    # (the dot would collide with the accent), and leaving `\i` in place strips the whole name to
    # `Krejč\'`. Bounded by a lookahead so `\it` and friends are not mangled into text.
    s = re.sub(r"\\([ij])(?![a-zA-Z])", r"\1", s)
    for src, dst in sorted(_LIGATURES.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(src, dst)
    # \"{o} · \"o · \c{c} · \v{s}
    s = re.sub(r"\\(.)\{(\w)\}", lambda m: _ACCENTS.get((m.group(1), m.group(2)), m.group(2)), s)
    s = re.sub(r"\\(.)(\w)", lambda m: _ACCENTS.get((m.group(1), m.group(2)), m.group(0)[1:]), s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)                       # any command left over
    return s


def _clean(value):
    """A field value as it should READ: braces stripped, LaTeX resolved, whitespace collapsed."""
    v = _deaccent(value)
    v = v.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", v).strip()


def parse_bibtex(text):
    """{key: {"type": …, "author": …, …}} — brace-matched, so nested braces do not truncate a title.

    A regex over `field = {value}` breaks on the first title containing braces (`{DNA} methylation`),
    which is common enough that it would fail on real bibliographies while passing a test file.
    """
    out, i, n = {}, 0, len(text)
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.match(r"@([A-Za-z]+)\s*[{(]", text[at:])
        if not m:
            i = at + 1
            continue
        kind = m.group(1).lower()
        body_start = at + m.end()
        opener = text[body_start - 1]
        closer = "}" if opener == "{" else ")"
        depth, j = 1, body_start
        while j < n and depth:                                  # brace-match the whole entry
            if text[j] == opener:
                depth += 1
            elif text[j] == closer:
                depth -= 1
            j += 1
        body, i = text[body_start:j - 1], j
        if kind in ("comment", "preamble", "string"):
            continue
        key, _, rest = body.partition(",")
        key = key.strip()
        if not key:
            continue
        if key not in out:                        # BibTeX keeps the FIRST and warns; so do we
            out[key] = dict(_fields(rest), type=kind, key=key)
    return out


def duplicate_keys(text):
    """Keys defined more than once. BibTeX keeps the first and warns; a silent second definition
    means a citation resolves to a paper the author did not mean, which no later check can see."""
    seen, dup = set(), []
    for m in re.finditer(r"@([A-Za-z]+)\s*[{(]\s*([^,\s{}()]+)\s*,", text):
        if m.group(1).lower() in ("comment", "preamble", "string"):
            continue
        k = m.group(2)
        (dup.append(k) if k in seen else seen.add(k))
    return sorted(set(dup))


def _fields(body):
    """`a = {x}, b = "y", c = 1 # {z}` -> {"a": "x", "b": "y", "c": "1z"} — brace-aware."""
    fields, i, n = {}, 0, len(body)
    while i < n:
        m = re.compile(r"\s*([A-Za-z][\w-]*)\s*=\s*").match(body, i)
        if not m:
            break
        name, i, parts = m.group(1).lower(), m.end(), []
        while i < n:
            if body[i] == "{":
                depth, start = 1, i + 1
                i += 1
                while i < n and depth:
                    depth += {"{": 1, "}": -1}.get(body[i], 0)
                    i += 1
                parts.append(body[start:i - 1])
            elif body[i] == '"':
                start, i = i + 1, i + 1
                while i < n and body[i] != '"':
                    i += 2 if body[i] == "\\" else 1
                parts.append(body[start:i])
                i += 1
            else:
                m2 = re.compile(r"[^,#]*").match(body, i)
                parts.append(m2.group(0).strip())
                i = m2.end()
            m3 = re.compile(r"\s*#\s*").match(body, i)          # string concatenation
            if not m3:
                break
            i = m3.end()
        joined = "".join(parts)
        fields[name] = _clean(joined)
        if name in ("author", "editor"):
            # 🔴 The braces are DATA in a name field: `{{World Health Organization}}` is BibTeX's
            # way of saying "this is one atomic name, do not read the last word as a surname".
            # _clean strips them for display, so the raw form is kept beside it — without this,
            # the WHO cites as "W. H. Organization".
            fields[name + "_raw"] = re.sub(r"\s+", " ", _deaccent(joined)).strip()
        m4 = re.compile(r"\s*,\s*").match(body, i)
        if not m4:
            break
        i = m4.end()
    return fields


_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "2nd", "3rd"}


def _split_and(field):
    """Split a BibTeX name list on ` and ` — but never inside braces, where the word is part of an
    atomic name (`{Institute for Science and Technology}` is ONE author, not two)."""
    out, depth, cur = [], 0, []
    i, n = 0, len(field)
    while i < n:
        ch = field[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if depth == 0 and field[i:i + 5].lower() == " and " :
            out.append("".join(cur))
            cur, i = [], i + 5
            continue
        cur.append(ch)
        i += 1
    out.append("".join(cur))
    return [a.strip() for a in out if a.strip()]


def authors(entry):
    """['Berg, Anna', …] as written — split on BibTeX's ` and `, never on a comma or inside braces.

    A trailing `and others` is BibTeX's own "et al." and is NOT a person: left in, it prints an
    author literally named "others", which is what every hand-rolled parser does.
    """
    field = entry.get("author_raw") or entry.get("author") or entry.get("editor_raw") \
        or entry.get("editor") or ""
    names = _split_and(field)
    if names and names[-1].strip().lower().rstrip(".") == "others":
        names = names[:-1]
    return names


def more_authors(entry):
    """True when the entry ended in `and others` — the author list is deliberately truncated."""
    field = entry.get("author_raw") or entry.get("author") or entry.get("editor_raw") \
        or entry.get("editor") or ""
    names = _split_and(field)
    return bool(names) and names[-1].strip().lower().rstrip(".") == "others"


def _atomic(one):
    """A brace-wrapped name is ONE unit — `{World Health Organization}`, `{van Gogh Museum}`."""
    one = one.strip()
    return one[1:-1].strip() if one.startswith("{") and one.endswith("}") else None


def _parts(one):
    """(family, given) for any of BibTeX's three spellings, suffixes discarded.

        First von Last          Anna van der Berg
        von Last, First         van der Berg, Anna
        von Last, Jr, First     King, Jr., Martin Luther     <- the 3-part form, and the reason
                                                                'M. L. King Jr.' is not 'J. King'
    """
    atomic = _atomic(one)
    if atomic is not None:
        return atomic, ""
    chunks = [c.strip() for c in one.split(",")]
    if len(chunks) >= 3:
        return chunks[0], chunks[2]                     # family, Jr dropped, given
    if len(chunks) == 2:
        return chunks[0], chunks[1]
    toks = [t for t in one.split() if t.lower().rstrip(",") not in _SUFFIXES]
    if not toks:
        return "", ""
    for k, t in enumerate(toks[:-1]):
        if t[:1].islower():                             # the von particle starts the family name
            return " ".join(toks[k:]), " ".join(toks[:k])
    return toks[-1], " ".join(toks[:-1])


def surname(one):
    """The FAMILY name, with its particles: 'van der Berg, A.' and 'Anna van der Berg' both work,
    an atomic `{…}` name is returned whole, and a `Jr.`/`III` suffix is never mistaken for one.

    The braces are read BEFORE they are dropped: they decide whether the name is atomic, and only
    then stop being text. (`M{\"u}ller` keeps its brace through `author_raw` and must not keep it
    on the slide.)
    """
    fam, _given = _parts(one.strip())
    return re.sub(r"[{}]", "", fam).strip()


def initials(one):
    """'Anna van der Berg' -> 'A.'; a surname-only or ATOMIC name yields ''. Never a guessed name."""
    _fam, given = _parts(one.strip())
    given = re.sub(r"[{}]", "", given)
    return " ".join("%s." % g[0].upper()
                    for g in given.replace(".", " ").split()
                    if g[:1].isalpha() and g.lower().rstrip(".") not in _SUFFIXES)


def year(entry):
    m = re.search(r"\b(1[5-9]\d\d|20\d\d|21\d\d)\b", str(entry.get("year") or entry.get("date") or ""))
    return m.group(1) if m else ""


def missing(entry):
    """Which of the three findability fields this entry does not have."""
    return [f for f in REQUIRED if not (entry.get(f) or "").strip()
            or (f == "year" and not year(entry))]


def _require(entry):
    gone = missing(entry)
    if gone:
        raise Incomplete(
            "%r has no %s. This module will not print `n.d.`/`Anon.` in its place: under the "
            "never-invent floor a plausible-looking citation is worse than a missing one, because "
            "nobody downstream can tell it from a real one. Fill the field in the .bib (the "
            "publisher's page or the DOI record has it) or drop the citation."
            % (entry.get("key", "?"), " or no ".join(gone)))


def _cjk_particle(s):
    """Does this string start with a CJK glyph (Han, kana, or CJK punctuation)?"""
    if not s:
        return False
    o = ord(s[0])
    return 0x2E80 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFF65


def suffixes(entries):
    """['', 'a', 'b', …] — the letter each entry needs so its author-year marker is UNIQUE.

    🔴 Two papers by the same first author in the same year produce the SAME marker, and until this
    existed both were `(Smith, 2020)`: ambiguous on the slide, and indistinguishable to the gate,
    so an uncited second paper read as cited. The a/b/c suffix is the ordinary convention, not an
    invention — it is assigned in CITED order, which is the order the reference list is built in.
    """
    keyed = [(_norm_key(e), i) for i, e in enumerate(entries)]
    counts = {}
    for k, _i in keyed:
        counts[k] = counts.get(k, 0) + 1
    out, seen = [""] * len(entries), {}
    for k, i in keyed:
        if counts[k] > 1 and k != ("", ""):
            n = seen.get(k, 0)
            out[i] = chr(ord("a") + n) if n < 26 else "%d" % (n + 1)
            seen[k] = n + 1
    return out


def _norm_key(entry):
    names = authors(entry)
    return ((surname(names[0]).lower() if names else ""), year(entry))


def _join(*parts):
    """Join name parts with the separator their SCRIPT takes: 'Müller et al.' but 'Müller等'.

    Chinese does not space a particle against the name it follows, so a hardcoded " %s " put a gap
    into 「(Müller 等, 2019)」 that no Chinese reader would write. The rule is the character, not a
    language setting: a particle that STARTS with a CJK glyph gets no space on either side.
    """
    out = ""
    for part in parts:
        part = str(part)
        if not part:
            continue
        if not out:
            out = part
        elif _cjk_particle(part) or _cjk_particle(out[-1]):
            out += part
        else:
            out += " " + part
    return out


def in_text(entry, style="numeric", n=None, *, etal="et al.", amp="&", suffix=""):
    """The marker that goes ON the slide: `[3]`, or `(van der Berg et al., 2020)`.

    `etal`/`amp` are parameters because a Chinese-language deck writes 等 and 与, and a hardcoded
    'et al.' would put English into an otherwise Chinese sentence.
    """
    if style == "numeric":
        if not isinstance(n, int) or n < 1:
            raise ValueError("numeric style needs the entry's 1-based position, got %r" % (n,))
        return "[%d]" % n
    if style != "author-year":
        raise ValueError("unknown citation style %r — %s" % (style, " / ".join(STYLES)))
    _require(entry)
    names = [surname(a) for a in authors(entry)]
    more = more_authors(entry)
    who = (_join(names[0], etal) if more or len(names) > 2 else
           _join(names[0], amp, names[1]) if len(names) == 2 else
           names[0])
    return "(%s, %s%s)" % (who, year(entry), suffix)


def format_reference(entry, style="numeric", n=None, *, etal="et al.", amp="&", suffix=""):
    """One reference-list line, derived from the entry — never from memory.

    `suffix` is the author-year disambiguator from `suffixes()`; it belongs on the line as well as
    on the marker, or the reader cannot tell which `(Smith, 2020a)` is which.
    """
    _require(entry)
    names = authors(entry)
    more = more_authors(entry)
    title = _clean(entry.get("title", ""))
    # GB/T 7714: a CJK "et al." (等) is for CJK-language works; a Latin-script work keeps "et al."
    # A 等 inside a Latin line also switched the whole run to East-Asian line breaking in a render
    # ("K onno", "ozon e" — test build, 2026-11-27).
    if etal != "et al." and not re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", " ".join(names) + title):
        etal = "et al."
    yr = year(entry)
    venue = next((_clean(entry[f]) for f in VENUE_FIELDS if entry.get(f)), "")
    if not venue and entry.get("eprint"):
        venue = "arXiv:%s" % _clean(entry["eprint"])
    doi = _clean(entry.get("doi", ""))
    if style == "numeric":
        if not isinstance(n, int) or n < 1:
            raise ValueError("numeric style needs the entry's 1-based position, got %r" % (n,))
        who = ", ".join((("%s %s" % (initials(a), surname(a))).strip()) for a in names[:6])
        if len(names) > 6 or more:
            who = _join(who + ",", etal)
        bits = ["[%d] %s," % (n, who), '"%s"' % title if title.endswith(("?", "!")) else '"%s,"' % title]
        if venue:
            bits.append("%s," % venue)
        bits.append("%s." % yr)
        if doi:
            bits.append("doi:%s" % doi)
        return " ".join(bits)
    if style != "author-year":
        raise ValueError("unknown citation style %r — %s" % (style, " / ".join(STYLES)))
    parts = [("%s, %s" % (surname(a), initials(a))).strip(", ") for a in names[:6]]
    if len(names) > 6 or more:
        who = _join(", ".join(parts) + ",", etal)
    elif len(parts) > 1:
        who = _join(", ".join(parts[:-1]), amp, parts[-1])
    else:
        who = parts[0]
    line = "%s (%s%s). %s%s" % (who, yr, suffix, title, "" if title.endswith((".", "?", "!")) else ".")
    if venue:
        line += " %s." % venue
    if doi:
        line += " https://doi.org/%s" % doi
    return line


def doi_url(entry):
    """The clickable target for this entry, or None. `link()` accepts it; a bare DOI is not a URL."""
    doi = _clean(entry.get("doi", ""))
    if doi:
        return "https://doi.org/" + doi.replace("https://doi.org/", "")
    url = _clean(entry.get("url", ""))
    return url if url.lower().startswith(("http://", "https://")) else None


def reference_page(slide, entries, *, style="numeric", title="References", cols=1, x=0.7, y=1.4,
                   accent=None, ink=None, chrome=None, size=9, link_dois=True, etal="et al.",
                   link_style="ink", w=None):
    """Render the reference list, FORMATTED FROM THE ENTRIES, with每 DOI clickable.

    `entries` is the ordered list of parsed entries (numeric markers are their 1-based positions).
    Built on the same mono/accent chrome as `deckkit.sources_page`, which takes plain strings; this
    takes bibliography entries, so the line on the slide cannot drift from the .bib.

    🔴 `link_style="ink"` (the default) sets the DECK's hyperlink colour to `ink` and drops the
    underline, because a renderer paints a linked run in the theme's hyperlink colour whatever fill
    the run itself carries. Measured on a rendered page: the two entries that happened to have a DOI
    came out in bright underlined blue and the third in the deck's navy — one list, two typographies,
    decided by whether a field existed in the .bib. `link_style="theme"` leaves the theme alone.
    """
    import deckkit as dk
    accent = dk.MAGENTA if accent is None else accent
    ink = dk.DEEP if ink is None else ink
    if link_dois and link_style == "ink":
        dk.set_link_color(slide, ink)
    sfx0 = suffixes(entries) if style == "author-year" else [""] * len(entries)
    lines0 = [format_reference(e, style, i + 1, etal=etal, suffix=sfx0[i]) for i, e in enumerate(entries)]
    # a Chinese list in the mono chrome mixes faces mid-line (Consolas has no CJK glyphs) and measures
    # with the wrong metrics, so its rows overlapped in a test build (2026-11-27): CJK uses the body face
    chrome = chrome or (dk.FONT if any(dk._has_cjk(t) for t in lines0 + [title, etal]) else dk.MONO)
    sw, _sh = dk._slide_size(slide)
    # the heading follows `y` (it was pinned at 0.6 whatever `y` said); the default y=1.4 places it as before
    dk.part_eyebrow(slide, x, y - 0.8, title, color=accent, font=chrome, size=13)
    dk.box(slide, x, y - 0.38, 1.2, 0.05, fill=accent)
    w = ((w if w is not None else sw - 2 * x) - 0.4 * (cols - 1)) / cols
    per = (len(entries) + cols - 1) // cols
    sfx = suffixes(entries) if style == "author-year" else [""] * len(entries)
    # 🔴 Only the NUMERIC style has a marker to hang in a gutter. Author-year's marker IS the
    # opening of the line ("Smith, J. (2020a). ..."), and setting it in a second column repeats it
    # -- measured on a render: "(Smith & van der Berg, 2020a)" wrapped inside a 0.5in gutter sized
    # for "[1]" and piled through the three rows below it. Both lints passed; only the picture
    # showed it.
    gut = 0.55 if style == "numeric" else 0.0
    for ci in range(cols):
        cx, cy = x + ci * (w + 0.4), y
        for i in range(ci * per, min((ci + 1) * per, len(entries))):
            e = entries[i]
            line = format_reference(e, style, i + 1, etal=etal, suffix=sfx[i])
            mark = in_text(e, style, i + 1, etal=etal, suffix=sfx[i]) if gut else ""
            body = line[len(mark):].strip() if mark and line.startswith(mark) else line
            # measured with the same model and line spacing the text is placed with (and the build lint
            # reads): a hand-rolled `lines × size × 1.25` disagreed with both and rows overlapped (2026-11-27)
            h = max(0.3, dk.measure_text([(body, False)], w - gut, size, font=chrome, line_spacing=1.15))
            if mark:
                # The gutter must HOLD its marker. This is the invariant the author-year pile
                # broke, so it is asserted rather than trusted: a marker that needs more lines
                # than the row has stacks through the rows below it, and both lints pass.
                mlines = dk.measure_lines([(mark, True)], size, gut - 0.05, font=chrome)
                if mlines * size / 72.0 * 1.25 > h + 1e-6:
                    raise ValueError(
                        "reference_page(): the marker %r needs %d line(s) in a %.2fin gutter while "
                        "its entry occupies %.2fin — it would stack through the rows below. A "
                        "marker column only suits the numeric style; author-year opens its own "
                        "line with the author and year." % (mark, mlines, gut - 0.05, h))
                dk.text(slide, cx, cy, gut - 0.05, h,
                        [[(mark, size, accent, True, False, chrome)]],
                        space_after=0, line_spacing=1.15)
            shape = dk.text(slide, cx + gut, cy, w - gut, h,
                            [[(body, size, ink, False, False, chrome)]],
                            space_after=0, line_spacing=1.15)
            url = doi_url(e) if link_dois else None
            if url:
                run = shape.text_frame.paragraphs[0].runs[0]
                dk.link(run, url)
                if link_style == "ink":
                    run.font.underline = False     # the DOI text is the affordance, not a rule
                    run.font.color.rgb = dk._as_rgb(ink)
            cy += h + 0.1
    return cy


def _selftest():
    bad = []
    bib = r"""
    @article{berg2020, author = {van der Berg, Anna and Smith, C. J.},
      title = {Deep {MRI} reconstruction}, journal = {Nature Methods}, year = {2020},
      doi = {10.1038/s41592-020-0772-5}}
    @inproceedings{muller2019, author = {M{\"u}ller, Hans and Lee, Ji-woo and Rossi, P.},
      title = {Sampling}, booktitle = {MICCAI}, year = 2019}
    @misc{nobody, title = {An orphan}}
    """
    db = parse_bibtex(bib)
    if sorted(db) != ["berg2020", "muller2019", "nobody"]:
        bad.append("three entries did not parse: %r" % sorted(db))
    if db.get("berg2020", {}).get("title") != "Deep MRI reconstruction":
        bad.append("a title with nested braces truncated: %r" % db.get("berg2020", {}).get("title"))
    if db.get("muller2019", {}).get("author", "").split(" and ")[0] != "Müller, Hans":
        bad.append("a LaTeX umlaut did not resolve: %r" % db.get("muller2019", {}).get("author"))
    if surname("van der Berg, Anna") != "van der Berg" or surname("Anna van der Berg") != "van der Berg":
        bad.append("a particled surname is wrong in one of the two spellings")
    if in_text(db["berg2020"], "author-year") != "(van der Berg & Smith, 2020)":
        bad.append("two-author marker: %r" % in_text(db["berg2020"], "author-year"))
    if in_text(db["muller2019"], "author-year") != "(Müller et al., 2019)":
        bad.append("three-author marker: %r" % in_text(db["muller2019"], "author-year"))
    if missing(db["nobody"]) != ["author", "year"]:
        bad.append("the incomplete entry's missing fields: %r" % missing(db["nobody"]))
    try:
        format_reference(db["nobody"], "numeric", 1)
        bad.append("an entry with no author/year was FORMATTED instead of refused")
    except Incomplete:
        pass
    for b in bad:
        print("  ✗", b)
    print("[citations] selftest %s" % ("FAILED" if bad else "ok"))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib", nargs="?", help="a .bib file")
    ap.add_argument("--style", default="numeric", choices=STYLES)
    ap.add_argument("--keys", help="comma-separated citation keys, in the order they are cited")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.bib:
        ap.error("a .bib file is required")
    try:
        db = parse_bibtex(open(a.bib, encoding="utf-8").read())
    except Exception as exc:
        print("[citations] could not read %s: %s" % (a.bib, exc))
        return 2
    keys = [k.strip() for k in a.keys.split(",")] if a.keys else sorted(db)
    unknown = [k for k in keys if k not in db]
    incomplete = []
    print("[citations] %d entry(ies) in %s; %d requested" % (len(db), a.bib, len(keys)))
    for i, k in enumerate(keys, 1):
        if k not in db:
            print("  ✗ %s — no such entry in this bibliography" % k)
            continue
        try:
            mark = in_text(db[k], a.style, i)
            line = format_reference(db[k], a.style, i)
            print("  %-22s %s" % (mark, line[len(mark):].strip() if line.startswith(mark) else line))
        except Incomplete as exc:
            incomplete.append(k)
            print("  ✗ %s" % exc)
    return 1 if (unknown or incomplete) else 0


if __name__ == "__main__":
    raise SystemExit(main())
