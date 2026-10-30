"""Imported FIRST by every test: a test run never reads the user's own taste profile or taste ledger.

The gates read two per-user files when they exist — the registry's `taste.md` (the register-pixels
freshness check, in both runtimes) and the taste ledger (`taste_ledger.py`). A test that runs a gate
on a developer's machine therefore read that person's private files, and its outcome depended on
them: green in CI (no such files), red or green locally depending on what the person had taught the
skill. Nine suites had each patched the ledger half by hand and one the registry half; this does
both, for every suite, before anything else is imported.

Both point at a fresh, empty temp folder. A test that needs a registry or a ledger of its own sets
the variable AFTER this import, as before. `scripts/check_tests_wired.py` refuses a test file that
does not import this module.
"""
import os
import tempfile

_ROOT = tempfile.mkdtemp(prefix="slide-maker-hermetic-")
os.environ["SLIDE_MAKER_REGISTRY"] = os.path.join(_ROOT, "registry")
os.makedirs(os.environ["SLIDE_MAKER_REGISTRY"], exist_ok=True)
os.environ["SLIDE_MAKER_TASTE_LEDGER"] = os.path.join(_ROOT, "taste-ledger.json")
