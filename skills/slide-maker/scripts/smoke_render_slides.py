#!/usr/bin/env python3
"""Regression for `render_deck.py --slides N[,M]` — the signature-move preview path.

The contract this locks down is CORRECTNESS, not speed:
  1. slideNN.png from a subset render is byte-identical to the same page from a full render
     (if this ever breaks, every preview silently shows the wrong slide);
  2. a --slides run NEVER leaves a render cache (a cache implies "all pages current", so the
     next --fast would report "no slide changed" over stale PNGs — the exact lie the
     incremental path exists to prevent);
  3. incoherent flag combinations fail at parse time with a non-zero exit, not after
     LibreOffice has run.

Run: python3 smoke_render_slides.py     (needs LibreOffice; skips cleanly without it)
"""
import hashlib
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.join(HERE, "render_deck.py")
FAILS = []


def ok(label, fn):
    try:
        fn()
        print("  ok   " + label)
    except AssertionError as e:
        FAILS.append(label)
        print("  FAIL " + label + " — " + str(e))
    except Exception as e:                                    # noqa: BLE001
        FAILS.append(label)
        print("  ERR  " + label + " — {}: {}".format(type(e).__name__, e))


def run(*args, cwd=None):
    # UTF-8 forced on the child: this output is machine-read, not displayed. Inheriting the
    # console code page makes these assertions fail under a legacy page — the child's
    # safe_stdio() replaces what it cannot encode, and the parser then cannot find it.
    p = subprocess.run([sys.executable, RENDER] + list(args), cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _fixture(d, n=5):
    sys.path.insert(0, HERE)
    import deckkit as dk
    prs = dk.blank_deck()
    for i in range(n):
        s = dk.add_slide(prs)
        dk.title_bar(s, "Slide number {}".format(i + 1))
        dk.big_numeral(s, 3.5, 2.0, str((i + 1) * 111))
    path = os.path.join(d, "t.pptx")
    prs.save(path)
    return path


def _sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    sys.path.insert(0, HERE)
    from render_deck import find_soffice
    if not find_soffice():
        print("smoke_render_slides: LibreOffice not found — skipped")
        return 0

    with tempfile.TemporaryDirectory() as d:
        pptx = _fixture(d)
        sub, full = os.path.join(d, "sub"), os.path.join(d, "full")

        def _subset_matches_full():
            rc, out = run(pptx, sub, "--slides", "3")
            assert rc == 0, "subset render failed: " + out[-400:]
            assert os.path.isfile(os.path.join(sub, "slide03.png")), "no slide03.png"
            assert not os.path.exists(os.path.join(sub, "slide01.png")), \
                "--slides 3 rendered pages it was not asked for"
            rc, out = run(pptx, full)
            assert rc == 0, "full render failed: " + out[-400:]
            assert _sha(os.path.join(sub, "slide03.png")) == _sha(os.path.join(full, "slide03.png")), \
                "subset slide03.png differs from the full render's — the preview would lie"
        ok("--slides 3 is byte-identical to the full render's page 3", _subset_matches_full)

        def _no_cache():
            assert not os.path.exists(os.path.join(sub, ".render-cache.json")), \
                "a --slides run left a cache; the next --fast would call stale PNGs current"
        ok("--slides leaves NO render cache", _no_cache)

        def _multi():
            out_d = os.path.join(d, "multi")
            rc, out = run(pptx, out_d, "--slides", "1,5")
            assert rc == 0, out[-300:]
            got = sorted(f for f in os.listdir(out_d) if f.startswith("slide"))
            assert got == ["slide01.png", "slide05.png"], "expected pages 1 and 5, got " + str(got)
        ok("--slides 1,5 renders exactly those pages", _multi)

        def _equals_form():
            out_d = os.path.join(d, "eq")
            rc, _ = run(pptx, out_d, "--slides=2")
            assert rc == 0 and os.path.isfile(os.path.join(out_d, "slide02.png")), "--slides=N form"
        ok("--slides=N form works", _equals_form)

        def _rejections():
            for args, needle in [
                (["--slides", "3", "--deliverables"], "full-deck render"),
                (["--slides", "3", "--fast"], "pass one"),
                (["--slides", "99"], "out of range"),
                (["--slides", "0"], "out of range"),
                (["--slides", "abc"], "1-indexed"),
                (["--slides"], "at least one"),
            ]:
                rc, out = run(pptx, os.path.join(d, "x"), *args)
                assert rc != 0, "{} should exit non-zero, got 0".format(" ".join(args))
                assert needle in out, "{} → wrong message: {}".format(" ".join(args), out[-200:])
        ok("incoherent flag combinations die at parse time", _rejections)

    print("smoke_render_slides: {} failure(s)".format(len(FAILS)))
    return 1 if FAILS else 0


try:                                            # console safety: a legacy code page must
    from _console import safe_stdio             # degrade a tick, never kill the report
    safe_stdio()
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
