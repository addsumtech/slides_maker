#!/usr/bin/env python3
"""Preflight: verify the slide-maker toolchain. Run once on a new machine:

    python check_env.py            # Windows / anywhere
    bash scripts/check_env.sh      # mac / Linux (delegates here)

Reports what's installed and the exact command to fix anything missing.
Cross-platform: macOS, Linux, WSL, and native Windows (PowerShell / cmd).
"""
import os
import sys
import tempfile

# Reuse the one LibreOffice finder so check + render agree on what counts as "found".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_deck import find_soffice  # noqa: E402

# Copy-pasteable pip commands for THIS interpreter (handles python vs python3 vs py).
PIP = '"{}" -m pip install'.format(sys.executable)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = os.path.join(ROOT, "requirements.txt")
PIP_REQ = '{} -r "{}"'.format(PIP, REQ)


def ensure_mpl_config_dir():
    """Avoid noisy matplotlib warnings when the home cache dir is not writable."""
    if os.environ.get("MPLCONFIGDIR"):
        return
    default = os.path.join(os.path.expanduser("~"), ".matplotlib")
    if os.path.isdir(default) and os.access(default, os.W_OK):
        return
    path = os.path.join(tempfile.gettempdir(), "slide-maker-matplotlib")
    os.makedirs(path, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = path


def check_module(mod, label, fix_pkg, optional=False, note=""):
    try:
        if mod == "matplotlib":
            ensure_mpl_config_dir()
        m = __import__(mod)
        ver = getattr(m, "__version__", "")
        print("  [ok]  {} {}".format(label, ver).rstrip())
    except ImportError:
        tag = "[optional]" if optional else "[MISSING] "
        line = "  {} {:<12} ->  {} {}".format(tag, label, PIP, fix_pkg)
        if note:
            line += "   ({})".format(note)
        print(line)


def main():
    print("slide-maker environment check:")
    print("  install python deps: {}".format(PIP_REQ))
    check_module("pptx", "python-pptx", "python-pptx")
    check_module("fitz", "pymupdf", "pymupdf")
    check_module("PIL", "Pillow", "Pillow")
    check_module("matplotlib", "matplotlib", "matplotlib",
                 optional=True, note="only for equation_png")

    soffice = find_soffice()
    if soffice:
        print("  [ok]  LibreOffice ({})".format(soffice))
    else:
        print("  [MISSING]  LibreOffice  ->  "
              "macOS: brew install --cask libreoffice | "
              "Ubuntu: sudo apt install libreoffice | "
              "Windows: winget install TheDocumentFoundation.LibreOffice | "
              "else https://www.libreoffice.org/download")


if __name__ == "__main__":
    main()
