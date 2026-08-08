"""The parallel render paths must be INVISIBLE in the output.

Two optimizations sit under `render_deck.py` — chunked parallel rasterization and the
pooled LibreOffice profile. Both are pure speed: every PNG they produce must be the same
bytes the old serial, throwaway-profile path produced, or the critic and the render-time
lint are looking at something the deck did not actually say.

That is the whole contract, and it is not something prose can hold. So the suite renders
the SAME deck down every path and compares sha256 — parallel vs serial, pooled profile vs
throwaway — rather than asserting that the code "looks right".

Two traps are encoded here because both were hit while writing the feature:

  * **Thumbnails are order-dependent.** `thumb_first`/`thumb_last` hash differently when
    rendered from a fresh document than when rendered after that page's 2x pass — MuPDF
    scales a cached decode in one case and does a scaled decode in the other. A first cut
    that rasterized in workers but made thumbnails in the parent changed two PNGs while
    every slide matched. `test_thumbnails_match` is that bug.
  * **A sub-threshold deck must take the serial path** and still produce both thumbnails.

Run:  python3 tests/test_render_parallel.py
"""
import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  — " + detail) if detail and not cond else ""))


def _require_deps():
    try:
        import fitz  # noqa: F401
        import pptx  # noqa: F401
    except ImportError as e:
        print("SKIPPED — missing dependency ({}). Install requirements.txt.".format(e))
        sys.exit(0)
    from render_deck import find_soffice
    if not find_soffice():
        print("SKIPPED — LibreOffice not found; this suite renders for real.")
        sys.exit(0)


def _heavy_image(path, w=900, h=560):
    """A deterministic photo-like image — noisy enough that it does NOT compress away.

    The fixture needs weight, not prettiness: the worker pool is now gated on PDF bytes per page,
    so a flat fill would keep the deck under the threshold and quietly send every "parallel" render
    down the serial path — which is how a byte-identity suite passes while comparing serial to
    serial. Deterministic so the deck (and therefore every hash below) is reproducible.
    """
    from PIL import Image
    im = Image.new("RGB", (w, h))
    px = im.load()
    v = 12345
    for y in range(h):
        for x in range(w):
            v = (1103515245 * v + 12345) & 0x7FFFFFFF        # LCG: same bytes on every machine
            px[x, y] = (v >> 16 & 0xFF, (v >> 8 & 0xFF) ^ (x & 0xFF), (v & 0xFF) ^ (y & 0xFF))
    im.save(path, "JPEG", quality=92)
    return path


def build_deck(path, n, heavy=False):
    """`heavy=True` puts a full-bleed photo on every slide, which is what crosses the weight gate."""
    import deckkit as dk
    prs = dk.blank_deck()
    img = _heavy_image(os.path.join(os.path.dirname(path), "probe.jpg")) if heavy else None
    for i in range(n):
        s = dk.add_slide(prs)
        if heavy:
            dk.picture(s, img, 0.0, 0.0, 10.0, 5.625, fit="cover")
        dk.title_bar(s, "Parallel render probe {}".format(i + 1), kicker="TEST")
        dk.bullet(s, 0.8, 1.6, 8.4, [("Alpha", "a line of supporting detail that wraps once"),
                                     ("Beta", "a second line of comparable length here")])
        dk.footer(s, tag="test", page=i + 1)
    prs.save(path)
    return path


def to_pdf(pptx, outdir):
    """Convert once, so the weight gate can be asked the same question the renderer asks it."""
    import render_deck as _rd
    os.makedirs(outdir, exist_ok=True)
    subprocess.run([_rd.find_soffice(), "--headless", "--convert-to", "pdf",
                    "--outdir", outdir, str(pptx)], capture_output=True, text=True)
    return os.path.join(outdir, os.path.splitext(os.path.basename(str(pptx)))[0] + ".pdf")


def render(pptx, out, env_extra=None):
    env = dict(os.environ, SLIDE_MAKER_SKIP_GATES="1")
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, str(SCRIPTS / "render_deck.py"), str(pptx), str(out)],
                       capture_output=True, text=True, env=env)
    return r


def hashes(d):
    out = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".png"):
            out[f] = hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest()
    return out


def main():
    _require_deps()
    tmp = tempfile.mkdtemp(prefix="render_parallel_")
    print("Parallel-render equivalence")

    from render_deck import _raster_workers, RASTER_MIN_PAGES, RASTER_MIN_BYTES_PER_PAGE

    # --- the worker-count policy, without rendering anything -----------------------------
    check("sub-threshold deck renders serially",
          _raster_workers(RASTER_MIN_PAGES - 1) == 1)
    check("at-threshold deck may go parallel (or serial on a 1-core box)",
          _raster_workers(RASTER_MIN_PAGES) >= 1)
    check("SLIDE_MAKER_RENDER_WORKERS=1 forces serial",
          _forced(1) == 1)
    check("a garbage SLIDE_MAKER_RENDER_WORKERS does not raise",
          isinstance(_forced("banana"), int))

    # --- the WEIGHT gate: page count alone was the wrong question ------------------------
    # A worker pool saves decode work, and decode cost tracks page weight. On text decks the pool
    # cost ~70ms in process starts to save ~60ms of rasterizing — measured +2.1% wall clock, an
    # optimization that ran and made the render slower.
    _light = os.path.join(tmp, "light.pdf")
    with open(_light, "wb") as fh:
        fh.write(b"x" * (RASTER_MIN_BYTES_PER_PAGE * 20 // 2))       # 10 KB/page over 20 pages
    check("a LIGHT pdf renders serially however many pages it has",
          _raster_workers(20, _light) == 1)
    _heavy = os.path.join(tmp, "heavy.pdf")
    with open(_heavy, "wb") as fh:
        fh.write(b"x" * (RASTER_MIN_BYTES_PER_PAGE * 20 * 4))        # 80 KB/page
    check("a HEAVY pdf still fans out", _raster_workers(20, _heavy) >= 2)
    check("the weight gate never overrides an explicit worker count",
          _forced(1, _heavy) == 1)
    check("an unreadable pdf size does not raise and does not force serial",
          _raster_workers(20, os.path.join(tmp, "does-not-exist.pdf")) >= 2)
    check("omitting the pdf keeps the old page-count-only answer",
          _raster_workers(20) >= 2)

    # --- the real thing: same deck, both paths -------------------------------------------
    # HEAVY on purpose. With a text fixture the weight gate sends the "parallel" run down the
    # serial path and every hash below compares serial to serial — a suite that passes by
    # measuring nothing. The assertion after the conversion is what keeps that honest.
    big = build_deck(os.path.join(tmp, "big.pptx"), max(12, RASTER_MIN_PAGES + 4), heavy=True)
    _big_pdf = to_pdf(big, os.path.join(tmp, "pdfdir"))
    _pages = max(12, RASTER_MIN_PAGES + 4)
    check("the equivalence fixture actually TAKES the parallel path",
          os.path.isfile(_big_pdf) and _raster_workers(_pages, _big_pdf) >= 2,
          "pdf={} bytes/page={}".format(
              _big_pdf,
              round(os.path.getsize(_big_pdf) / _pages) if os.path.isfile(_big_pdf) else "n/a"))
    par_dir, ser_dir = os.path.join(tmp, "par"), os.path.join(tmp, "ser")
    rp = render(big, par_dir)
    rs = render(big, ser_dir, {"SLIDE_MAKER_RENDER_WORKERS": "1"})
    check("parallel render exits 0", rp.returncode == 0, rp.stderr[-300:])
    check("serial render exits 0", rs.returncode == 0, rs.stderr[-300:])

    hp, hs = hashes(par_dir), hashes(ser_dir)
    check("both paths produce the same file set", set(hp) == set(hs),
          "parallel={} serial={}".format(sorted(hp), sorted(hs)))
    slides_same = all(hp.get(k) == hs.get(k) for k in hs if k.startswith("slide"))
    check("every slide PNG is byte-identical across paths", slides_same)
    thumbs = [k for k in hs if k.startswith("thumb_")]
    check("both thumbnails were produced", len(thumbs) == 2, str(thumbs))
    check("test_thumbnails_match — thumbnails byte-identical across paths",
          all(hp.get(k) == hs.get(k) for k in thumbs))

    # --- a deck below the threshold still gets its thumbnails ----------------------------
    small = build_deck(os.path.join(tmp, "small.pptx"), 3)
    sm_dir = os.path.join(tmp, "small_out")
    r = render(small, sm_dir)
    check("small deck renders", r.returncode == 0, r.stderr[-300:])
    got = set(hashes(sm_dir))
    check("small deck still emits both thumbnails",
          {"thumb_first.png", "thumb_last.png"} <= got, str(sorted(got)))

    # --- the LibreOffice profile pool ----------------------------------------------------
    # The pool replaced a throwaway profile that existed for two reasons. Both are asserted
    # here, because a pool that quietly breaks either is worse than no pool: a fan-out render
    # that produces no PDF is the exact failure the throwaway was protecting against.
    np_dir = os.path.join(tmp, "nopool")
    r = render(big, np_dir, {"SLIDE_MAKER_NO_PROFILE_POOL": "1"})
    check("SLIDE_MAKER_NO_PROFILE_POOL=1 still renders", r.returncode == 0, r.stderr[-300:])
    check("opting out of the pool changes no bytes",
          hashes(np_dir) == hs, "pool-free output differs from serial output")

    procs = [subprocess.Popen([sys.executable, str(SCRIPTS / "render_deck.py"), str(big),
                               os.path.join(tmp, "cc{}".format(i))],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=dict(os.environ, SLIDE_MAKER_SKIP_GATES="1"))
             for i in range(3)]
    for p in procs:
        p.communicate()
    check("3 concurrent renders all exit 0", all(p.returncode == 0 for p in procs),
          str([p.returncode for p in procs]))
    check("3 concurrent renders all match the serial output",
          all(hashes(os.path.join(tmp, "cc{}".format(i))) == hs for i in range(3)))

    check("a full pool falls back to a throwaway profile instead of failing",
          _renders_with_pool_exhausted(big, os.path.join(tmp, "exhausted")))

    print("\n{} passed, {} failed".format(len(PASS), len(FAIL)))
    return 1 if FAIL else 0


def _renders_with_pool_exhausted(pptx, out):
    """Hold every pool slot, then render. Must still succeed via the throwaway fallback."""
    try:
        import fcntl
    except ImportError:
        return True                       # Windows never uses the pool at all
    from render_deck import _profile_pool_dir, PROFILE_POOL_SLOTS
    root = _profile_pool_dir()
    os.makedirs(root, exist_ok=True)
    held = []
    try:
        for i in range(PROFILE_POOL_SLOTS):
            fh = open(os.path.join(root, "slot{:02d}.lock".format(i)), "a+")
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            held.append(fh)
        r = render(pptx, out)
        return r.returncode == 0 and any(f.startswith("slide") for f in hashes(out))
    except OSError:
        return True                       # could not take every slot; nothing to assert
    finally:
        for fh in held:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                fh.close()
            except Exception:
                pass


def _forced(val, pdf=None):
    from render_deck import _raster_workers
    old = os.environ.get("SLIDE_MAKER_RENDER_WORKERS")
    os.environ["SLIDE_MAKER_RENDER_WORKERS"] = str(val)
    try:
        return _raster_workers(32, pdf)
    finally:
        if old is None:
            os.environ.pop("SLIDE_MAKER_RENDER_WORKERS", None)
        else:
            os.environ["SLIDE_MAKER_RENDER_WORKERS"] = old


if __name__ == "__main__":
    sys.exit(main())
