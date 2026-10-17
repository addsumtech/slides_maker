#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""On the direction page, no style motif covers a cover's title — in any preset, on any cover composition.

WHY. The glassmorphism preview drew its frosted panel at a fixed right:8% top:26%, which is exactly where
a `split-vertical` cover sets its title: the user was shown "The iPho[…] explaine[…]" under a blurred pane
and asked to pick a direction from it (iPhone 18 explainer, 2026-10-17). Nothing measured it, because the
preview is HTML and every gate in the skill reads a .pptx.

HOW. Each of the 18 presets is rendered on each of the four cover compositions in headless Chrome, and the
topmost element under the title's centre and four inset corners is asked for: it must be the title itself.
That is the reader's question — can I read the title — and it holds for every motif, present or future,
without knowing what any of them draws. Without Chrome the test says SKIP; it never passes silently.

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
window.addEventListener('load', function () {
  var out = [];
  document.querySelectorAll('.slide.cover').forEach(function (cov) {
    var t = cov.querySelector('.cover-ttl');
    if (!t) return;
    cov.scrollIntoView({block: 'center', behavior: 'instant'});        // elementFromPoint answers only inside the viewport
    var r = t.getBoundingClientRect();
    var name = cov.className;
    var c = cov.getBoundingClientRect();
    if (r.left < c.left - 1 || r.right > c.right + 1 || r.top < c.top - 1 || r.bottom > c.bottom + 1) {
      out.push(name + ' title outside its own slide');   // a cover that left its frame (memphis, 2026-10-17)
    }
    var pts = [[.5, .5], [.12, .25], [.88, .25], [.12, .75], [.88, .75]];
    pts.forEach(function (p) {
      var x = r.left + r.width * p[0], y = r.top + r.height * p[1];
      var el = document.elementFromPoint(x, y);
      if (!el || !el.closest('.cover-ttl')) {
        out.push(name + ' @' + p.join(',') + ' -> ' + (el ? (el.className || el.tagName) : 'nothing'));
      }
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
    r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=1400,4000", "--virtual-time-budget=1500", "--dump-dom",
                        html_path.as_uri()], capture_output=True, text=True, timeout=300)
    m = re.search(r'<pre id="probe-result">(.*?)</pre>', r.stdout, re.S)
    blocked = []
    if not m:
        bad.append("the probe did not run in Chrome ({})".format((r.stderr or "")[-160:]))
    else:
        found = json.loads(m.group(1).replace("&quot;", '"').replace("&gt;", ">").replace("&lt;", "<")
                           .replace("&amp;", "&"))
        n_cov = len(re.findall(r'class="slide cover cov-', html))
        if n_cov != len(dirs):
            bad.append("the page carries {} covers for {} directions".format(n_cov, len(dirs)))
        blocked = found
    if not bad:
        if blocked:
            bad.append("a motif covers the cover title at {} probe point(s): {}".format(len(blocked), blocked[:4]))
        else:
            ok.append("no motif covers the title on any of {} presets x {} cover compositions".format(
                len(ah._PRESET_COMPOSITION), len(ah._COVERS)))

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
