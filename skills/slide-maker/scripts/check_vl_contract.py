#!/usr/bin/env python3
"""Check visual languages against the contract: the manifest (scripts/vl_contract.py) and the build-time conformance
(scripts/vl_conformance.py). usage: check_vl_contract.py [name …]   (default: every registered language)

The manifests are loaded and validated FIRST, as plain data: a broken manifest is named here before anything imports
visual_languages (which reads every manifest at import and would die on it)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vl_contract as vc            # noqa: E402
import vl_specs                     # noqa: E402

# the contract's tests, which a packaged copy of the skill may leave out (the SkillHub package ships no tests/)
TESTS = Path(__file__).resolve().parent.parent / "tests"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="languages to check (default: all)")
    a = ap.parse_args(argv)
    try:
        specs = vl_specs.load(drafts=True)
    except ValueError as e:
        print("  FAIL " + str(e))
        print("[vl-contract] the manifests cannot be loaded — fix the file named above")
        return 1
    names = a.names or list(specs)
    unknown = [n for n in names if n not in specs]
    if unknown:
        print("unknown language(s) {} — registered: {}".format(unknown, ", ".join(specs)))
        return 2
    own = {n: vc.validate(specs[n]) for n in names}
    every_own = {p for s in specs.values() for p in vc.validate(s)}
    cross = [p for p in vc.validate_all(specs) if p not in every_own]
    # a cross problem names a language quoted ('ink') or as lang/ground (distinctiveness: "editorial/light and …")
    probs = [p for n in names for p in own[n]] + [p for p in cross if any(
        "'{}'".format(n) in p or any(w.split("/")[0] == n for w in p.split() if "/" in w) for n in names)]
    if probs:                              # the manifest itself is wrong: building pages from it would only crash
        for p in probs:
            print("  FAIL " + p)
        print("[vl-contract] {} language(s), {} manifest problem(s) — fix these first".format(len(names), len(probs)))
        return 1
    import vl_conformance as vcf           # imports visual_languages: only once every manifest is sound
    for n in names:
        unready = vcf.painters_missing(n)
        if unready:                        # nothing of it can be built yet: say what to write, check nothing else
            probs += unready
            continue
        missing = vcf.pages_missing(n)
        probs += missing + vcf.assets_missing(n)
        if missing:                        # the build checks need every page composed: say so, do not crash
            print("  skipped for {}: never-invent and extras checks (they build pages; compose all seven first)".format(n))
            continue
        probs += vcf.invented_words(n) + vcf.extras_not_refused(n) + vcf.bright_slabs(n) + vcf.rules_past_content(n)
    for p in probs:
        print("  FAIL " + p)
    print("[vl-contract] {} language(s), {} problem(s)".format(len(names), len(probs)))
    if not probs:                          # a NEXT line is a command that runs, so it names only a file that is here
        test = TESTS / "test_vl_contract.py"
        if test.is_file():
            print("NEXT: python3 {}".format(test))
        else:
            print("(this copy of the skill has no tests/: run tests/test_vl_contract.py on a checkout of the source "
                  "repository)")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
