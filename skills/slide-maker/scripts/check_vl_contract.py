#!/usr/bin/env python3
"""Check visual languages against the contract: the manifest (scripts/vl_contract.py) and the build-time conformance
(scripts/vl_conformance.py). usage: check_vl_contract.py [name …]   (default: every registered language)"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vl_contract as vc            # noqa: E402
import vl_conformance as vcf        # noqa: E402
import visual_languages as vl       # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="languages to check (default: all)")
    a = ap.parse_args(argv)
    names = a.names or list(vl.REGISTRY)
    unknown = [n for n in names if n not in vl.REGISTRY]
    if unknown:
        print("unknown language(s) {} — registered: {}".format(unknown, ", ".join(vl.REGISTRY)))
        return 2
    probs = [p for p in vc.validate_all(vl.REGISTRY) if any(n in p for n in names)]
    for n in names:
        missing = vcf.pages_missing(n)
        probs += missing + vcf.assets_missing(n)
        if missing:                            # the build checks need every page composed: say so, do not crash
            print("  skipped for {}: never-invent and extras checks (they build pages; compose all seven first)".format(n))
            continue
        probs += vcf.invented_words(n) + vcf.extras_not_refused(n)
    for p in probs:
        print("  FAIL " + p)
    print("[vl-contract] {} language(s), {} problem(s)".format(len(names), len(probs)))
    if not probs:
        print("NEXT: python3 {}/tests/test_vl_contract.py".format(Path(__file__).resolve().parent.parent))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
