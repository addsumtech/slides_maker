"""One manifest per visual language: scripts/vl_specs/<name>.py defines SPEC (the contract: scripts/vl_contract.py).

load() returns {name: SPEC} ordered by SPEC["order"]. A new language is a new file here — nothing else to register.
A manifest that would brick the skill or shadow another language is refused HERE, naming its file: a missing top-level
key (every importer reads it), a name that is not the file's stem (a copied manifest that kept the old name silently
replaced that language — final review), two files with one name. VL_SPECS_DIR points it at another folder (tests)."""
import importlib.util
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DRAFTS = {}        # name -> file of a manifest still holding "FILL:" decisions (new_visual_language.py's draft)


def _is_draft(o):
    if isinstance(o, str):
        return o.lstrip().startswith("FILL:")
    if isinstance(o, dict):
        return any(_is_draft(v) for v in o.values())
    if isinstance(o, (list, tuple)):
        return any(_is_draft(v) for v in o)
    return False
TOP_KEYS = ("name", "order", "kind", "display", "rationale", "offer", "look", "grounds", "type", "image_pages",
            "extras", "derived", "samples", "painters", "skin")      # = vl_contract.TOP_KEYS (kept here: this file imports nothing)


def load(directory=None, drafts=False):
    """{name: SPEC}. A DRAFT — a manifest still holding a "FILL:" decision — is left out unless drafts=True (only the
    contract check and new_visual_language.py read drafts): every other importer reads colours, faces and copy from
    a manifest, and one undecided field would break the whole skill. Left-out drafts are named in DRAFTS."""
    d = Path(directory or os.environ.get("VL_SPECS_DIR") or _HERE)
    specs, files = [], {}
    DRAFTS.clear()
    for f in sorted(d.glob("*.py")):
        if f.name.startswith("_"):
            continue
        mod_spec = importlib.util.spec_from_file_location("vl_spec_" + f.stem, f)
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)
        spec = getattr(mod, "SPEC", None)
        if not isinstance(spec, dict):
            raise ValueError("{}: defines no SPEC dict".format(f))
        missing = [k for k in TOP_KEYS if k not in spec]
        if missing:
            raise ValueError("{}: the manifest has no {} — every importer reads these".format(f.name, missing))
        if spec["name"] != f.stem:
            raise ValueError("{}: name={!r} must equal the file's stem {!r} (a copied manifest keeps the old name and "
                             "silently replaces that language)".format(f.name, spec["name"], f.stem))
        if spec["name"] in files:
            raise ValueError("{} and {}: both declare name={!r}".format(files[spec["name"]], f.name, spec["name"]))
        files[spec["name"]] = f.name
        if not drafts and _is_draft(spec):
            DRAFTS[spec["name"]] = f.name
            continue
        specs.append(spec)
    specs.sort(key=lambda s: s["order"])
    return {s["name"]: s for s in specs}
