#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""On the direction page, no style motif covers a cover's title — in any preset, on any cover composition.

WHY. The glassmorphism preview drew its frosted panel at a fixed right:8% top:26%, which is exactly where
a `split-vertical` cover sets its title: the user was shown "The iPho[…] explaine[…]" under a blurred pane
and asked to pick a direction from it (iPhone 18 explainer, 2026-10-17). Nothing measured it, because the
preview is HTML and every gate in the skill reads a .pptx.

HOW. Each of the 18 presets is rendered on each of the four cover compositions in headless Chrome, at a wide and
a narrow window, and every SOLID motif (not a full-slide texture, not a blurred glow, visibly opaque, with a fill,
border or glyphs) is measured against the INK box of every word on the cover — title, subtitle, tag. A first
version asked only which element sat on top of the title; once the words were lifted above every motif that
question always answered "the title", while a near-white card under a light title still erased it (review of
005842f). A rotated thin line is walked along its stroke, not its axis-aligned box. Without Chrome the test says
SKIP, and CI turns a SKIP into a failure.

Run: python3 tests/test_direction_cover_legibility.py
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import archetypes_html as ah  # noqa: E402
from icons import _find_chrome  # noqa: E402

PROBE = """
<script>
// A SOLID motif: not a full-slide texture (grid, frame), not blurred (a glow), visibly opaque (the product of its
// own and its ancestors' opacity), and drawn with a fill, a border or glyphs. Its box must not cross the INK box of
// any of the cover's words (title, subtitle, tag) — "topmost element" is not "readable": a near-white card UNDER a
// light title passes every hit-test and wipes the title out (dark_tech, review of 005842f).
var ALLOW = ['dna-gl', 'dna-ghost'];   // synthwave's horizon grid, swiss's 6%-white ghost numeral: texture by design
function solid(el, cov) {
  var cs = getComputedStyle(el), r = el.getBoundingClientRect(), c = cov.getBoundingClientRect();
  if (r.width * r.height > 0.5 * c.width * c.height) return false;
  var op = 1, e = el; while (e && e !== cov) { op *= parseFloat(getComputedStyle(e).opacity); e = e.parentElement; }
  if (op < 0.35 || (cs.filter || '').indexOf('blur') >= 0) return false;
  var m = cs.backgroundColor.match(/rgba?\\(([^)]+)\\)/), a = 1;
  if (m) { var p = m[1].split(','); a = p.length > 3 ? parseFloat(p[3]) : 1; }
  var bw = Math.max(parseFloat(cs.borderTopWidth) || 0, parseFloat(cs.borderBottomWidth) || 0,
                    parseFloat(cs.borderLeftWidth) || 0, parseFloat(cs.borderRightWidth) || 0);
  var glyphs = (el.textContent || '').trim().length > 0 && el.children.length === 0;
  return a >= 0.35 || glyphs || bw >= 1.2;
}
window.addEventListener('load', function () {
  var out = [];
  document.querySelectorAll('.slide.cover').forEach(function (cov) {
    var name = cov.className.replace('slide cover ', '');
    var t = cov.querySelector('.cover-ttl'), c = cov.getBoundingClientRect();
    if (t) {
      var r = t.getBoundingClientRect();
      if (r.left < c.left - 1 || r.right > c.right + 1 || r.top < c.top - 1 || r.bottom > c.bottom + 1)
        out.push(name + ': title outside its own slide');      // memphis, 2026-10-17
    }
    var words = [].slice.call(cov.querySelectorAll('.cover-ttl,.cover-sub,.cover-tag'));
    cov.querySelectorAll('*').forEach(function (el) {
      if (el.closest('.cover-body') || el.closest('.cover-tag') || el.classList.contains('accentbar')
          || el.classList.contains('cover-panel') || ALLOW.indexOf((el.className || '').split(' ')[0]) >= 0) return;
      if (!solid(el, cov)) return;
      var r = el.getBoundingClientRect();
      // a ROTATED THIN LINE (midcentury's rays) is not its bounding box: client rects are axis-aligned, so a
      // diagonal stroke's box covers a whole quadrant. Walk the stroke itself — corner to corner of its box,
      // the diagonal its angle picks — and test points along it.
      var mt = (getComputedStyle(el).transform || 'none').match(/matrix\\(([^)]+)\\)/);
      var thin = Math.min(el.offsetWidth, el.offsetHeight) <= 4;
      words.forEach(function (w) {
        var rg = document.createRange(); rg.selectNodeContents(w); var ink = rg.getBoundingClientRect();
        if (thin && mt) {
          var v = mt[1].split(',').map(parseFloat), down = (v[1] >= 0) === (v[0] >= 0);
          var x0 = down ? r.left : r.right, x1 = down ? r.right : r.left, n = 0;
          for (var i = 0; i <= 40; i++) {
            var px = x0 + (x1 - x0) * i / 40, py = r.top + (r.bottom - r.top) * i / 40;
            if (px >= ink.left && px <= ink.right && py >= ink.top && py <= ink.bottom) n++;
          }
          if (n > 0) out.push(name + ': ' + el.className + ' crosses ' + w.className + ' (' + n + ' points)');
          return;
        }
        var ix = Math.max(0, Math.min(r.right, ink.right) - Math.max(r.left, ink.left));
        var iy = Math.max(0, Math.min(r.bottom, ink.bottom) - Math.max(r.top, ink.top));
        if (ix * iy > 4) out.push(name + ': ' + el.className + ' crosses ' + w.className + ' (' + Math.round(ix * iy) + 'px2)');
      });
    });
  });
  var pre = document.createElement('pre'); pre.id = 'probe-result';
  pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
});
</script>
"""

ok, bad, skipped = [], [], []
chrome = _find_chrome()
if not chrome:
    skipped.append("no Chrome/Chromium on this machine — the cover-title probe needs a browser")
else:
    tmp = Path(tempfile.mkdtemp(prefix="dir-cover-"))
    dirs = []                                   # every preset on every cover composition, ONE page, ONE browser run
    for name in sorted(ah._PRESET_COMPOSITION):
        base = ah.preset_directions([name])[0]
        for comp in ah._COVERS:
            d = dict(base)
            d["cover"] = comp
            d["name"] = "{} / {}".format(name, comp)
            dirs.append(d)
    html_path = tmp / "all.html"
    ah.build_directions_html(dirs, str(html_path), deck_title="The iPhone 18 family, explained")
    html = html_path.read_text(encoding="utf-8").replace("</body>", PROBE + "</body>")
    html_path.write_text(html, encoding="utf-8")
    blocked = []
    n_cov = len(re.findall(r'class="slide cover cov-', html))
    if n_cov != len(dirs):
        bad.append("the page carries {} covers for {} directions".format(n_cov, len(dirs)))
    for width in (1400, 760):                   # a wide window, and one narrow enough to stack the grid
        r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--window-size={},4000".format(width), "--virtual-time-budget=1500", "--dump-dom",
                            html_path.as_uri()], capture_output=True, text=True, timeout=300)
        m = re.search(r'<pre id="probe-result">(.*?)</pre>', r.stdout, re.S)
        if not m:
            bad.append("the probe did not run in Chrome at {}px ({})".format(width, (r.stderr or "")[-160:]))
            continue
        found = json.loads(m.group(1).replace("&quot;", '"').replace("&gt;", ">").replace("&lt;", "<")
                           .replace("&amp;", "&"))
        blocked += ["{}px {}".format(width, f) for f in found]
    if not bad:
        if blocked:
            bad.append("{} motif/word crossing(s) on the covers: {}".format(len(blocked), blocked[:4]))
        else:
            ok.append("no solid motif crosses a cover's words on {} presets x {} compositions, at 1400px and 760px"
                      .format(len(ah._PRESET_COMPOSITION), len(ah._COVERS)))

for line in ok:
    print("  ok   " + line)
for line in skipped:
    print("  SKIP " + line)
for line in bad:
    print("  FAIL " + line)
print("\n{} passed, {} failed".format(len(ok), len(bad)))
if bad:
    print("[test_direction_cover_legibility] FAILED: {} problem(s)".format(len(bad)))
    sys.exit(1)
print("[test_direction_cover_legibility] ok")
