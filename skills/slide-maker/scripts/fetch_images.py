#!/usr/bin/env python3
"""Search and download LICENSE-CLEAR photographs, and keep a provenance ledger of what happened.

`references/image-generation.md` owns the REFERENT RULE: a real-and-specific subject (a named
place, a real product, a real person) gets a REAL sourced photo, and generating one that CLAIMS
photographic reality of it is a fidelity bug. That whole pipeline — search Commons/Openverse,
verify the subject, record the license, treat to the palette, write an evidence token — existed
only as prose, executed by hand, every run. Two consequences, both silent:

  * the API calls were re-derived per deck (query shape, license filtering, which field carries
    the attribution string), which is the same "arithmetic nobody should re-derive per deck"
    argument `deckkit.register_mark` was written from; and
  * the `searched (Commons, Openverse), none found -> generated, flagged illustrative` rung was
    UNFALSIFIABLE. Nothing recorded that a search ran, what it asked for, or what came back — so
    "I looked and there was nothing" and "I did not look" produced identical decks, and the
    cheaper one is the one a tired run picks.

This script makes the search a recorded event. Every query lands in `sources.json` next to the
assets with its result count and outcome, every adopted file lands with its license, author,
attribution string and sha256 — so `check_image_provenance.py` can hold the plan's evidence
tokens against something real instead of against a claim.

**It never decides that a photo is GOOD.** Subject-correctness and the aesthetic bar
(construction cranes, ugly snapshots, watermarks) are eyes-and-judgment gates that stay with the
model — `image_qc.py` measures what a program can measure and prints a contact sheet precisely so
that looking is cheap. A file this script downloads is a CANDIDATE, not an approved plate.

**Network failure is NOT "none found".** A blocked host, a proxy, an offline box: every one of
them makes the sources return nothing, and treating that as "no photo exists" launders a
connectivity problem into a licence to generate fake photography. Unreachable sources exit 2 with
a distinct message and never write a `none found` outcome.

    python3 scripts/fetch_images.py search "Delft University of Technology campus"
    python3 scripts/fetch_images.py fetch "Delft University aerial" \\
        --out ~/Downloads/<deck>/assets/sourced --subject "TU Delft campus" --slide 4 --limit 3
    python3 scripts/fetch_images.py ledger ~/Downloads/<deck>/assets/sourced --tokens
    python3 scripts/fetch_images.py ledger ~/Downloads/<deck>/assets/sourced --credits
    python3 scripts/fetch_images.py --selftest        # offline: parsing, filters, both outcomes

Exit 0 clean · 1 nothing usable found (a recorded `none found`) · 2 could not run / unreachable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

# A polite, identifying UA is a Wikimedia API REQUIREMENT, not manners: anonymous default-UA
# traffic is rate-limited and can be blocked outright, which would surface here as "none found".
UA = ("slide-maker/1.0 (https://github.com/addsumtech/slides_maker; skill asset sourcing) "
      "python-urllib")

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"

LEDGER_NAME = "sources.json"
LEDGER_VERSION = 1

# Licenses a deck may carry without further questions. NC (non-commercial) and ND (no-derivatives)
# are excluded BY DEFAULT and deliberately: a deck is routinely shown at work, and treating a photo
# to the deck palette (`image_fx.duotone`) is a derivative work. Both are opt-in via --licenses
# because a genuinely non-commercial deck may use NC, and that is the user's call to make with the
# facts in front of them, not a default to inherit silently.
DEFAULT_LICENSES = ("cc0", "pdm", "by", "by-sa")
_ALL_LICENSES = ("cc0", "pdm", "by", "by-sa", "by-nc", "by-nc-sa", "by-nd", "by-nc-nd")

# Attribution obligations by license family. CC0/PDM ask for none; every BY variant does.
_NO_ATTRIB = ("cc0", "pdm")


# --------------------------------------------------------------------------- transport

class Unreachable(RuntimeError):
    """No source could be contacted. Distinct from 'contacted, nothing matched'."""


def _cache_dir():
    """Same cache contract as `icons.py` — one place, overridable, platform-correct. Kept local
    rather than imported so a change to the icon cache cannot silently move image candidates."""
    env = os.environ.get("SLIDE_MAKER_CACHE")
    if env:
        base = env
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches/slide-maker")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "slide-maker")
    else:
        base = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
                            "slide-maker")
    d = os.path.join(base, "sourced")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = os.path.join(tempfile.gettempdir(), "slide-maker-sourced")
        os.makedirs(d, exist_ok=True)
    return d


def _get(url, *, timeout=20, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else json.loads(data.decode("utf-8", "replace"))


# The transport is a module-level seam so `--selftest` can run the whole pipeline — parsing,
# license filtering, ranking, both outcomes — with ZERO network. A self-test that needs the
# internet is a self-test that gets skipped on the day it matters.
_TRANSPORT = _get


def _fetch_json(url, *, timeout=20):
    return _TRANSPORT(url, timeout=timeout)


# --------------------------------------------------------------------------- normalisation

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _plain(s):
    """Commons `extmetadata` values are HTML fragments (`<a href=…>Ymblanter</a>`). A credits line
    with markup in it is a defect that reaches the rendered slide, so strip at the boundary."""
    if not s:
        return ""
    s = _TAG.sub(" ", str(s))
    s = (s.replace("&amp;", "&").replace("&quot;", '"').replace("&#039;", "'")
          .replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " "))
    return _WS.sub(" ", s).strip()


# Words that carry no search signal. Dropping them is the FIRST rung of the relaxation ladder.
_STOP = {"a", "an", "the", "of", "in", "on", "at", "and", "or", "for", "with", "from", "by",
         "photo", "photos", "photograph", "photography", "image", "images", "picture", "view",
         "shot", "close-up", "closeup"}


def _query_ladder(q, max_terms=3):
    """Progressively broader queries, most specific FIRST.

    Measured, live, on the first real run of this script: Commons' search is AND over terms, so
    `Delft University of Technology aerial campus` returned ZERO files while `Delft University`
    returned plenty. A single-shot query therefore manufactures the exact defect this whole file
    exists to prevent — a `searched, none found` rung that is false, and a licence to generate
    fake photography of a place that is photographed thousands of times over.

    The ladder is RECORDED (`queries_tried` in the ledger), because "we asked six ways and found
    nothing" and "we asked once, badly" are different claims and only one of them justifies the
    fallback rung. Non-space-delimited scripts (Chinese, Japanese) tokenise as one term, so the
    ladder collapses to the original query — correct, not a crash."""
    q = (q or "").strip()
    if not q:
        return []
    words = re.findall(r"[^\s,;:/()\[\]]+", q)
    core = [w for w in words if w.lower().strip(".,'\"") not in _STOP]
    out = [q]
    if core and len(core) != len(words):
        out.append(" ".join(core))
    if len(core) > max_terms:
        # Keep the DISTINCTIVE terms: proper nouns (capitalised) first, then the longest, since a
        # long common word ("reconstruction") discriminates better than a short one ("new").
        rank = sorted(range(len(core)), key=lambda i: (0 if core[i][:1].isupper() else 1,
                                                       -len(core[i]), i))
        for n in (max_terms, 2):
            if n < len(core):
                keep = sorted(rank[:n])
                out.append(" ".join(core[i] for i in keep))
    seen, ladder = set(), []
    for c in out:
        c = c.strip()
        if c and c.lower() not in seen:
            seen.add(c.lower())
            ladder.append(c)
    return ladder


def _license_key(short):
    """Map a licence label onto the short keys used by --licenses.

    Returns "" for anything unrecognised, and the caller REJECTS on "" rather than assuming free
    use — an unknown licence string is exactly the case where guessing is expensive."""
    s = (short or "").strip().lower()
    if not s:
        return ""
    if "public domain" in s or s in ("pdm", "public-domain") or s.startswith("pd-"):
        return "pdm"
    if "cc0" in s:
        return "cc0"
    m = re.search(r"cc[ -]?by([ -]nc)?([ -]sa|[ -]nd)?", s)
    if m:
        key = "by"
        if m.group(1):
            key += "-nc"
        if m.group(2):
            key += "-sa" if "sa" in m.group(2) else "-nd"
        return key
    if s.startswith("by"):                       # Openverse already speaks this dialect
        k = s.replace("_", "-")
        return k if k in _ALL_LICENSES else ""
    return ""


def _pretty_license(key, version=""):
    if key == "cc0":
        return "CC0"
    if key == "pdm":
        return "Public Domain"
    label = "CC " + key.upper().replace("-", "-")
    return (label + " " + version).strip()


def _attrib_required(key):
    return key not in _NO_ATTRIB


def _credit_line(entry):
    """One human-readable credit. Used by `--credits` for `deckkit.sources_page` / `source_note`."""
    if entry.get("attribution"):
        return entry["attribution"]
    bits = [entry.get("title") or entry.get("subject") or "photo"]
    if entry.get("author"):
        bits.append("by " + entry["author"])
    bits.append("(" + entry.get("license", "?") + ")")
    if entry.get("page_url"):
        bits.append("— " + entry["page_url"])
    return " ".join(bits)


# --------------------------------------------------------------------------- sources

def _commons(query, *, limit, width, timeout, attempts=None):
    """Walks the relaxation ladder and stops at the first rung that answers. Each returned
    candidate carries the rung it was found on, so a widened query is visible, never implied."""
    for rung in _query_ladder(query):
        if attempts is not None:
            attempts.append("Commons: " + rung)
        got = _commons_once(rung, limit=limit, width=width, timeout=timeout)
        if got:
            for g in got:
                g["found_via"] = rung
            return got
    return []


def _commons_once(query, *, limit, width, timeout):
    url = (COMMONS_API + "?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search",
        # `filetype:bitmap` keeps SVG diagrams and PDFs out of a PHOTO search; namespace 6 is File:.
        "gsrsearch": "filetype:bitmap " + query,
        "gsrnamespace": "6", "gsrlimit": str(max(1, min(50, limit * 3))),
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": str(width),
    }))
    data = _fetch_json(url, timeout=timeout)
    pages = ((data or {}).get("query") or {}).get("pages") or {}
    out = []
    for p in pages.values():
        infos = p.get("imageinfo") or []
        if not infos:
            continue
        ii = infos[0]
        em = ii.get("extmetadata") or {}

        def _em(k):
            return _plain((em.get(k) or {}).get("value"))

        short = _em("LicenseShortName")
        key = _license_key(short or _em("License"))
        restrictions = _em("Restrictions")
        out.append({
            "source": "Wikimedia Commons",
            "title": _plain(p.get("title", "")).replace("File:", "").strip(),
            "description": _em("ImageDescription")[:400],
            "author": _em("Artist"),
            "license_key": key,
            # Commons' own short name already carries the VERSION ("CC BY-SA 4.0"), which the
            # generic formatter cannot reconstruct — a credit line that drops the version is
            # a subtly wrong licence statement, so prefer the source's own string.
            "license": short if key and short else (_pretty_license(key) if key else "unknown"),
            "license_url": _em("LicenseUrl"),
            "attribution": "",                      # Commons has no ready-made string; built below
            "page_url": ii.get("descriptionurl", ""),
            "file_url": ii.get("thumburl") or ii.get("url", ""),
            "original_url": ii.get("url", ""),
            "width": int(ii.get("width") or 0),
            "height": int(ii.get("height") or 0),
            # A Commons file may be free of COPYRIGHT and still restricted for other reasons
            # (trademark, personality rights). That is not a licence question and cannot be
            # auto-resolved, so it is carried forward and shown, never silently dropped.
            "restrictions": "" if restrictions.lower() in ("", "none") else restrictions,
            "categories": _em("Categories")[:300],
        })
    for e in out:
        if not e["attribution"] and e["license_key"] and _attrib_required(e["license_key"]):
            e["attribution"] = '"{}" by {} ({}) — {}'.format(
                e["title"] or "photo", e["author"] or "unknown author", e["license"], e["page_url"])
    return out


def _openverse(query, *, limit, licenses, timeout, attempts=None):
    for rung in _query_ladder(query):
        if attempts is not None:
            attempts.append("Openverse: " + rung)
        got = _openverse_once(rung, limit=limit, licenses=licenses, timeout=timeout)
        if got:
            for g in got:
                g["found_via"] = rung
            return got
    return []


def _openverse_once(query, *, limit, licenses, timeout):
    url = (OPENVERSE_API + "?" + urllib.parse.urlencode({
        "q": query,
        "page_size": str(max(1, min(20, limit * 3))),
        "license": ",".join(licenses),
        "mature": "false",
    }))
    data = _fetch_json(url, timeout=timeout)
    out = []
    for r in (data or {}).get("results") or []:
        key = _license_key(r.get("license") or "")
        out.append({
            "source": "Openverse/" + (r.get("provider") or r.get("source") or "?"),
            "title": _plain(r.get("title", "")),
            "description": "",
            "author": _plain(r.get("creator", "")),
            "license_key": key,
            "license": _pretty_license(key, r.get("license_version", "")) if key else "unknown",
            "license_url": r.get("license_url", ""),
            "attribution": _plain(r.get("attribution", "")),
            "page_url": r.get("foreign_landing_url", ""),
            "file_url": r.get("url", ""),
            "original_url": r.get("url", ""),
            "width": int(r.get("width") or 0),
            "height": int(r.get("height") or 0),
            "restrictions": "",
            "categories": ", ".join((r.get("tags") or [])[:6]) if isinstance(r.get("tags"), list)
                          and r.get("tags") and isinstance(r["tags"][0], str) else "",
        })
    return out


_SOURCES = {"commons": _commons, "openverse": _openverse}
_SOURCE_LABEL = {"commons": "Commons", "openverse": "Openverse"}


def search(query, *, sources=("commons", "openverse"), limit=8, licenses=DEFAULT_LICENSES,
           min_px=1200, width=2400, timeout=20, attempts=None):
    """Return (candidates, errors). Raises Unreachable when EVERY source failed to answer.

    `attempts` (a list, optional) collects every query rung actually ISSUED, so the ledger can
    record what was asked rather than what was intended."""
    cands, errors = [], []
    for name in sources:
        fn = _SOURCES.get(name)
        if fn is None:
            errors.append((name, "unknown source"))
            continue
        try:
            if name == "commons":
                got = fn(query, limit=limit, width=width, timeout=timeout, attempts=attempts)
            else:
                got = fn(query, limit=limit, licenses=licenses, timeout=timeout, attempts=attempts)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
            errors.append((name, "{}: {}".format(type(exc).__name__, exc)))
            continue
        cands.extend(got)
    if errors and len(errors) == len(sources):
        raise Unreachable("; ".join("{} -> {}".format(n, e) for n, e in errors))

    kept = []
    for c in cands:
        if c["license_key"] not in licenses:
            continue                                   # includes unknown ("") — reject, never guess
        # The long edge is what a full-bleed plate consumes. A 900x600 photo is fine for a thumb
        # and unusable at 13.3in wide, and finding that out at render time costs a whole round.
        if max(c["width"], c["height"]) < min_px:
            continue
        kept.append(c)

    seen, uniq = set(), []
    for c in kept:
        k = c["file_url"] or (c["source"], c["title"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    uniq.sort(key=lambda c: (-(c["width"] * c["height"]), c["title"]))
    return uniq[:limit], errors


# --------------------------------------------------------------------------- ledger

def _ledger_path(out_dir):
    return Path(out_dir) / LEDGER_NAME


def load_ledger(out_dir):
    p = _ledger_path(out_dir)
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            d.setdefault("entries", [])
            d.setdefault("searches", [])
            return d
        except (ValueError, OSError) as exc:
            raise SystemExit("cannot read {}: {}".format(p, exc))
    return {"version": LEDGER_VERSION, "entries": [], "searches": []}


def save_ledger(out_dir, led):
    p = _ledger_path(out_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(led, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def record_search(led, query, sources, n_results, outcome, note="", attempts=None):
    led.setdefault("searches", []).append({
        "query": query,
        # What was ASKED, rung by rung. A `none found` rung is only as honest as the queries
        # behind it, and this is the only place that record can live.
        "queries_tried": list(attempts or []),
        "sources": [_SOURCE_LABEL.get(s, s) for s in sources],
        "n_results": n_results,
        "outcome": outcome,                    # found | none found | unreachable
        "note": note,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    return led


def token_for(entry):
    """The evidence token for a plan row. THE grammar lives in `references/image-generation.md`;
    this emits the `sourced —` form so a hand-typed token cannot drift from the ledger."""
    return "sourced — {} ({})".format(entry.get("source", "?"), entry.get("license", "?"))


def none_found_token(sources, *, reason="none"):
    named = ", ".join(_SOURCE_LABEL.get(s, s) for s in sources)
    tail = ("none found → generated, flagged illustrative" if reason == "none"
            else "found but low-quality → generated, flagged illustrative")
    return "searched ({}), {}".format(named, tail)


def _download(url, dest, *, timeout=60):
    data = _TRANSPORT(url, timeout=timeout, binary=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _safe_name(s, fallback="photo"):
    """Filesystem-safe, and NOT Latin-only.

    The first version stripped everything outside `[A-Za-z0-9._-]`, so every Chinese or Japanese
    subject collapsed to the bare fallback: 北京大学校园 and 東京タワー both became `photo`, and a
    deck's asset folder lost the one thing that makes a filename useful. ``\\w`` with the unicode flag
    keeps letters in any script and still drops the separators and shell-hostile punctuation that
    actually matter. Every modern filesystem this skill runs on stores those names fine."""
    s = re.sub(r"[^\w.-]+", "-", (s or "").strip(), flags=re.UNICODE).strip("-.")
    return (s or fallback)[:60]


def fetch(query, out_dir, *, subject="", slide=None, sources=("commons", "openverse"), limit=3,
          licenses=DEFAULT_LICENSES, min_px=1200, width=2400, timeout=20, prefix=""):
    """Search, download the top `limit` candidates, and write/extend the ledger.

    Downloads CANDIDATES on purpose. The skill requires a human/model LOOK before a photo is
    placed (watermarks, cranes, wrong preparation), and you cannot look at a URL."""
    out = Path(out_dir)
    led = load_ledger(out)
    attempts = []
    try:
        cands, errors = search(query, sources=sources, limit=limit, licenses=licenses,
                               min_px=min_px, width=width, timeout=timeout, attempts=attempts)
    except Unreachable as exc:
        record_search(led, query, sources, 0, "unreachable", str(exc)[:300], attempts=attempts)
        save_ledger(out, led)
        raise

    if not cands:
        record_search(led, query, sources, 0, "none found",
                      "; ".join("{} -> {}".format(n, e) for n, e in errors), attempts=attempts)
        save_ledger(out, led)
        return [], errors

    written = []
    for i, c in enumerate(cands, 1):
        stem = prefix or ("slide-%02d" % slide if slide else "src")
        ext = os.path.splitext(urllib.parse.urlparse(c["file_url"]).path)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"):
            ext = ".jpg"
        base = re.sub(r"\.(jpe?g|png|webp|tiff?|bmp|gif)$", "", (c["title"] or subject), flags=re.I)
        name = "{}-{}-{}{}".format(stem, i, _safe_name(base), ext)
        dest = out / name
        try:
            sha = _download(c["file_url"], dest, timeout=max(timeout, 60))
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            errors.append((c["source"], "download failed: {}".format(exc)))
            continue
        entry = dict(c)
        # The ledger must describe the file ON DISK. The API's width/height belong to the ORIGINAL
        # upload, and what lands here is the deck-sized thumb — recording the original would let a
        # 6000px number vouch for a 1200px file, which is precisely the claim image_qc.py exists
        # to test.
        entry["orig_width"], entry["orig_height"] = c["width"], c["height"]
        try:
            from PIL import Image
            with Image.open(dest) as _im:
                entry["width"], entry["height"] = _im.size
        except Exception as exc:
            # LOUDLY unknown, never the upload's numbers. Leaving 6000x4000 on a file that is
            # actually 1200px wide is the precise shape of a claim that vouches for something it
            # never measured — and it would silence image_qc.py's TOO SMALL by looking large.
            entry["width"] = entry["height"] = None
            entry["size_probe"] = "failed: {}: {}".format(type(exc).__name__, exc)
        entry.update({
            "file": name, "path": str(dest), "sha256": sha, "bytes": dest.stat().st_size,
            "subject": subject or query, "slide": slide, "query": query,
            "attribution_required": _attrib_required(c["license_key"]),
            "status": "candidate",
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        entry["token"] = token_for(entry)
        entry["credit"] = _credit_line(entry)
        led["entries"] = [e for e in led["entries"] if e.get("file") != name] + [entry]
        written.append(entry)

    record_search(led, query, sources, len(cands), "found" if written else "none found",
                  "; ".join("{} -> {}".format(n, e) for n, e in errors), attempts=attempts)
    save_ledger(out, led)
    return written, errors


def adopt(out_dir, files, *, slide=None, note=""):
    """Promote candidate(s) to `placed` — the state that means a model LOOKED and chose this file."""
    led = load_ledger(out_dir)
    names = {os.path.basename(f) for f in files}
    hit = 0
    for e in led["entries"]:
        if e.get("file") in names:
            e["status"] = "placed"
            if slide is not None:
                e["slide"] = slide
            if note:
                e["note"] = note
            hit += 1
    save_ledger(out_dir, led)
    return hit


# --------------------------------------------------------------------------- CLI

def _print_candidates(cands, query=""):
    for i, c in enumerate(cands, 1):
        print("  [{}] {}x{}  {}  {}".format(i, c["width"], c["height"], c["license"], c["source"]))
        print("      {}".format(c["title"][:90]))
        if c.get("restrictions"):
            print("      ⚠ non-copyright restriction: {}".format(c["restrictions"]))
        if c.get("found_via") and c["found_via"].lower() != (query or "").lower():
            print("      found via widened query: {!r}".format(c["found_via"]))
        if c.get("description"):
            print("      desc: {}".format(c["description"][:110]))
        print("      {}".format(c["page_url"] or c["file_url"]))


def _cmd_search(a):
    attempts = []
    try:
        cands, errors = search(a.query, sources=a.sources, limit=a.limit, licenses=a.licenses,
                               min_px=a.min_px, width=a.width, timeout=a.timeout, attempts=attempts)
    except Unreachable as exc:
        print("NETWORK UNREACHABLE — every source failed to answer. This is NOT 'none found': do "
              "not record a `searched, none found` rung and do not generate a photographic plate "
              "on the strength of it.\n  {}".format(exc), file=sys.stderr)
        return 2
    for n, e in errors:
        print("  [warn] {} unavailable: {}".format(n, e), file=sys.stderr)
    if not cands:
        print("no license-clear candidate ≥{}px in {}.".format(a.min_px, ", ".join(a.sources)))
        print("queries tried: " + " | ".join(attempts))
        print("evidence token: " + none_found_token(a.sources))
        return 1
    print("{} candidate(s) — LOOK at the file before you place it (image_qc.py --contact-sheet):"
          .format(len(cands)))
    _print_candidates(cands, a.query)
    if a.json:
        Path(a.json).write_text(json.dumps(cands, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote " + a.json)
    return 0


def _cmd_fetch(a):
    try:
        got, errors = fetch(a.query, a.out, subject=a.subject, slide=a.slide, sources=a.sources,
                            limit=a.limit, licenses=a.licenses, min_px=a.min_px, width=a.width,
                            timeout=a.timeout, prefix=a.prefix)
    except Unreachable as exc:
        print("NETWORK UNREACHABLE — every source failed to answer; recorded as `unreachable`, "
              "NOT as `none found`.\n  {}".format(exc), file=sys.stderr)
        return 2
    for n, e in errors:
        print("  [warn] {}: {}".format(n, e), file=sys.stderr)
    if not got:
        print("no license-clear candidate ≥{}px. Recorded the search.".format(a.min_px))
        print("evidence token: " + none_found_token(a.sources))
        return 1
    print("downloaded {} candidate(s) to {}".format(len(got), a.out))
    for e in got:
        print("  {}  {}x{}  {}".format(e["file"], e["width"], e["height"], e["token"]))
    print("\nNEXT — these are CANDIDATES, not plates:")
    print("  1. python3 scripts/image_qc.py {} --contact-sheet".format(a.out))
    print("  2. VIEW the sheet: reject watermarks, cranes/scaffolding, ugly or wrong-subject shots")
    print("  3. python3 scripts/fetch_images.py adopt {} <chosen-file>".format(a.out))
    return 0


def _cmd_adopt(a):
    n = adopt(a.out, a.files, slide=a.slide, note=a.note)
    print("marked {} file(s) placed in {}".format(n, _ledger_path(a.out)))
    return 0 if n else 1


def _cmd_ledger(a):
    led = load_ledger(a.out)
    entries = [e for e in led["entries"] if (not a.placed_only or e.get("status") == "placed")]
    if a.tokens:
        for e in entries:
            print("slide {}: {} — {}".format(e.get("slide") or "?", e.get("file"), e["token"]))
        for s in led["searches"]:
            if s["outcome"] == "none found":
                print("query {!r}: searched ({}), none found".format(s["query"],
                                                                     ", ".join(s["sources"])))
            elif s["outcome"] == "unreachable":
                print("query {!r}: UNREACHABLE — not a 'none found' rung".format(s["query"]))
        return 0
    if a.credits:
        need = [e for e in entries if e.get("attribution_required")]
        if not need:
            print("(no attribution-required image in the ledger)")
            return 0
        for e in need:
            print(_credit_line(e))
        return 0
    print(json.dumps(led, indent=2, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- selftest

_FAKE_COMMONS = {"query": {"pages": {"1": {
    "title": "File:Test Campus Aerial.jpg",
    "imageinfo": [{
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Test_Campus_Aerial.jpg",
        "url": "https://upload.wikimedia.org/x/Test_Campus_Aerial.jpg",
        "thumburl": "https://upload.wikimedia.org/thumb/x/2400px-Test_Campus_Aerial.jpg",
        "width": 4000, "height": 2500,
        "extmetadata": {
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
            "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
            "Artist": {"value": '<a href="//commons.wikimedia.org/wiki/User:X">X Photographer</a>'},
            "ImageDescription": {"value": "Aerial view of the campus"},
            "AttributionRequired": {"value": "true"},
            "Restrictions": {"value": "None"},
        }}]},
    "2": {                                        # non-free label -> must be dropped, not guessed
    "title": "File:Unknown Terms.jpg",
    "imageinfo": [{"descriptionurl": "u", "url": "u", "thumburl": "u", "width": 3000,
                   "height": 2000, "extmetadata": {"LicenseShortName": {"value": "All rights reserved"}}}]},
    "3": {                                        # too small -> must be dropped
    "title": "File:Tiny.jpg",
    "imageinfo": [{"descriptionurl": "t", "url": "t", "thumburl": "t", "width": 400,
                   "height": 300, "extmetadata": {"LicenseShortName": {"value": "CC0"}}}]},
}}}

_FAKE_OPENVERSE = {"results": [{
    "title": "Mobile scanner", "license": "by-nc", "license_version": "2.0",
    "creator": "Someone", "url": "https://example.org/a.jpg",
    "foreign_landing_url": "https://example.org/a", "width": 3000, "height": 2000,
    "attribution": '"Mobile scanner" by Someone is licensed under CC BY-NC 2.0.',
    "provider": "flickr", "tags": [{"name": "x"}],
}]}


def _selftest():
    global _TRANSPORT
    ok, bad = [], []

    def fake(url, timeout=20, binary=False):
        if binary:
            return b"\x89PNG\r\n\x1a\n" + b"0" * 64
        if "commons.wikimedia.org" in url:
            return _FAKE_COMMONS
        if "openverse" in url:
            return _FAKE_OPENVERSE
        raise urllib.error.URLError("unexpected host")

    _TRANSPORT = fake
    try:
        cands, errors = search("campus", sources=("commons", "openverse"))
        names = [c["title"] for c in cands]
        if names == ["Test Campus Aerial.jpg"]:
            ok.append("license + size filters kept exactly the free, large file (unknown terms "
                      "REJECTED rather than assumed free; 400px dropped; BY-NC excluded by default)")
        else:
            bad.append("filter kept the wrong set: {}".format(names))

        c = cands[0]
        if c["author"] == "X Photographer" and "<a" not in c["author"]:
            ok.append("Commons HTML in `Artist` is stripped before it can reach a credits line")
        else:
            bad.append("author not de-marked-up: {!r}".format(c["author"]))
        if c["license"] == "CC BY-SA 4.0" or c["license_key"] == "by-sa":
            ok.append("licence normalised to a short key + printable label")
        else:
            bad.append("licence mapping wrong: {} / {}".format(c["license_key"], c["license"]))
        if c["attribution"] and "X Photographer" in c["attribution"]:
            ok.append("an attribution-required file arrives WITH a built credit string")
        else:
            bad.append("no attribution string built for a BY-SA file")

        cands_nc, _ = search("campus", sources=("openverse",), licenses=("by-nc",), min_px=1000)
        if cands_nc and cands_nc[0]["license_key"] == "by-nc":
            ok.append("--licenses opens NC deliberately (the user's call, never the default)")
        else:
            bad.append("explicit NC opt-in did not return the NC file")

        tmp = Path(tempfile.mkdtemp(prefix="fetchimg-"))
        got, _ = fetch("campus", tmp, subject="campus", slide=4)
        led = load_ledger(tmp)
        if got and led["entries"][0]["sha256"] and led["entries"][0]["status"] == "candidate":
            ok.append("a downloaded file lands in the ledger hashed and marked CANDIDATE — "
                      "downloading is not choosing")
        else:
            bad.append("ledger entry wrong: {}".format(led["entries"][:1]))
        if led["searches"] and led["searches"][0]["outcome"] == "found":
            ok.append("the search itself is recorded, with its query and result count")
        else:
            bad.append("search not recorded")
        if adopt(tmp, [got[0]["file"]], slide=4) == 1 and \
                load_ledger(tmp)["entries"][0]["status"] == "placed":
            ok.append("adopt promotes candidate -> placed (the 'a model looked' state)")
        else:
            bad.append("adopt did not promote")

        def empty(url, timeout=20, binary=False):
            if binary:
                return b""
            return {"query": {"pages": {}}} if "commons" in url else {"results": []}

        _TRANSPORT = empty
        tmp2 = Path(tempfile.mkdtemp(prefix="fetchimg-none-"))
        got2, _ = fetch("nothing at all", tmp2)
        led2 = load_ledger(tmp2)
        if not got2 and led2["searches"][0]["outcome"] == "none found":
            ok.append("a genuine empty result records `none found` — the rung becomes checkable")
        else:
            bad.append("empty result not recorded as none found")

        def dead(url, timeout=20, binary=False):
            raise urllib.error.URLError("connection refused")

        _TRANSPORT = dead
        tmp3 = Path(tempfile.mkdtemp(prefix="fetchimg-dead-"))
        try:
            fetch("anything", tmp3)
            bad.append("an unreachable network did NOT raise — it would read as 'none found'")
        except Unreachable:
            led3 = load_ledger(tmp3)
            if led3["searches"][0]["outcome"] == "unreachable":
                ok.append("unreachable is a DISTINCT recorded outcome from `none found` — a "
                          "blocked host can never launder itself into a licence to fake a photo")
            else:
                bad.append("unreachable recorded as {}".format(led3["searches"][0]["outcome"]))
    finally:
        _TRANSPORT = _get

    print("\n".join("  ok   " + x for x in ok))
    if bad:
        print("\n".join("  FAIL " + x for x in bad))
    print("\n{} passed, {} failed".format(len(ok), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="Run the offline self-test (no network) and exit.")
    sub = ap.add_subparsers(dest="cmd")

    def common(p, *, need_query=True):
        if need_query:
            p.add_argument("query", help="What to search for — the SUBJECT, in words a caption "
                                         "would use ('Delft University aerial', not 'nice campus').")
        p.add_argument("--sources", default="commons,openverse",
                       type=lambda s: tuple(x.strip() for x in s.split(",") if x.strip()),
                       help="commons,openverse (default both).")
        p.add_argument("--limit", type=int, default=3, help="Candidates to keep (default 3).")
        p.add_argument("--licenses", default=",".join(DEFAULT_LICENSES),
                       type=lambda s: tuple(x.strip().lower() for x in s.split(",") if x.strip()),
                       help="Allowed licence keys. Default {} — NC/ND are OFF because a work deck "
                            "is commercial use and palette treatment is a derivative."
                            .format(",".join(DEFAULT_LICENSES)))
        p.add_argument("--min-px", type=int, default=1200,
                       help="Reject anything whose LONG edge is under this (default 1200).")
        p.add_argument("--width", type=int, default=2400,
                       help="Requested Commons thumb width (default 2400) — deck-sized, not the "
                            "60MB original.")
        p.add_argument("--timeout", type=int, default=20)

    p = sub.add_parser("search", help="Search only; print candidates. Downloads nothing.")
    common(p)
    p.add_argument("--json", help="Also write the candidate list to this path.")
    p.set_defaults(fn=_cmd_search)

    p = sub.add_parser("fetch", help="Search AND download candidates into --out, updating the ledger.")
    common(p)
    p.add_argument("--out", required=True, help="Asset directory (holds sources.json).")
    p.add_argument("--subject", default="", help="The subject as the plan states it.")
    p.add_argument("--slide", type=int, help="Deck slide number this is planned for.")
    p.add_argument("--prefix", default="", help="Filename stem (default slide-NN / src).")
    p.set_defaults(fn=_cmd_fetch)

    p = sub.add_parser("adopt", help="Mark chosen candidate(s) as placed, after LOOKING at them.")
    p.add_argument("out")
    p.add_argument("files", nargs="+")
    p.add_argument("--slide", type=int)
    p.add_argument("--note", default="")
    p.set_defaults(fn=_cmd_adopt)

    p = sub.add_parser("ledger", help="Print the provenance ledger, its evidence tokens, or credits.")
    p.add_argument("out")
    p.add_argument("--tokens", action="store_true", help="Print plan evidence tokens.")
    p.add_argument("--credits", action="store_true", help="Print the attribution lines to render.")
    p.add_argument("--placed-only", action="store_true")
    p.set_defaults(fn=_cmd_ledger)

    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not getattr(a, "fn", None):
        ap.print_help()
        return 2
    return a.fn(a)


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
