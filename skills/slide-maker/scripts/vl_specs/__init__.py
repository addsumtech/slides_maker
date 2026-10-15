"""One manifest per visual language: scripts/vl_specs/<name>.py defines SPEC (the contract: scripts/vl_contract.py).

load() returns {name: SPEC} ordered by SPEC["order"]. A new language is a new file here — nothing else to register."""
import importlib
import pkgutil
from pathlib import Path


def load():
    specs = []
    for m in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
        if m.name.startswith("_"):
            continue
        specs.append(importlib.import_module("vl_specs." + m.name).SPEC)
    specs.sort(key=lambda s: s["order"])
    return {s["name"]: s for s in specs}
