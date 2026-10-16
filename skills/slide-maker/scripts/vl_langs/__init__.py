"""One module per visual language written AFTER the first fifteen: scripts/vl_langs/<name>.py holds its ground painter
(_ground_<name>), its card (_card_<name>) and its seven page compositions (@vl_native.register(name, page)) — so a
new language never edits a central file. `new_visual_language.py <name>` writes the first draft.

load() imports every module here once and returns {name: module}. It is re-entrant: a module is placed in sys.modules
BEFORE it runs, because it imports vl_native and visual_languages, which call load() while they import. VL_LANGS_DIR
points it at another folder (tests)."""
import importlib.util
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
ERRORS = {}        # name -> "<file>: <the exception>" for a module that failed to import (that language is not ready)


def load(directory=None):
    """{name: module} for every module that imports; a module that raises is left out and named in ERRORS — one
    half-written language must not take the other languages down with it."""
    d = Path(directory or os.environ.get("VL_LANGS_DIR") or _HERE)
    out = {}
    for f in sorted(d.glob("*.py")):
        if f.name.startswith("_"):
            continue
        key = "vl_lang_" + f.stem
        mod = sys.modules.get(key)
        if mod is None or getattr(mod, "__file__", None) != str(f):
            spec = importlib.util.spec_from_file_location(key, f)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[key] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                sys.modules.pop(key, None)
                ERRORS[f.stem] = "{}: {}: {}".format(f, type(e).__name__, e)
                continue
        ERRORS.pop(f.stem, None)
        out[f.stem] = mod
    return out
