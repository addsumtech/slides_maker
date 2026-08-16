#!/usr/bin/env python3
"""How long a WRITTEN REASON is, measured so the answer does not depend on the language.

WHY. This skill gates a dozen decisions on "a written reason that travels with the deck" — a
critic waiver, a form-reach exception, a density waiver, `--nudge-again`, `none_opt_in`. Every one
of those floors was `len(text) < N`, i.e. a count of CODEPOINTS, and that quietly made the bar
depend on the language the user writes in:

    "看过了，不用再审"                          8 codepoints → REJECTED by a floor of 12
    "the box is a fixed template slot"        32 codepoints → accepted by a floor of 20
    "这个盒子是模板固定槽位，只能改常数"          17 codepoints → REJECTED by a floor of 20

The Chinese strings there say MORE than the English one and were refused for saying it in fewer
characters. That is not a rounding error in a validator; on a Chinese deck it is a gate that
cannot be satisfied honestly, and the way out of a gate you cannot satisfy is to pad it with
words nobody means — which destroys the one property these reasons exist to have.

So width is measured the way the writing system actually works: an East-Asian **wide** or
**fullwidth** character counts as 2. That is the same `east_asian_width` rule terminals and
typography use, it is exactly a no-op for ASCII (every existing Latin floor keeps its behaviour,
byte for byte), and it makes the floors mean "roughly this much information" instead of "roughly
this much Latin".

ONE definition, imported — never three copies. Copied constants have drifted between this skill's
two gate paths three separate times, and a floor is exactly the kind of small number that gets
re-typed slightly differently and then disagrees for years.
"""
from __future__ import annotations

import unicodedata


def reason_width(text) -> int:
    """Latin-equivalent width of a written reason. Non-strings and blanks are 0, never an error.

    Wide (W) and fullwidth (F) characters — CJK ideographs, kana, hangul, fullwidth punctuation —
    count as 2; everything else counts as 1. Ambiguous-width characters (`A`) deliberately count
    as 1: they are Latin in a Latin context and widening them would let a string of accented
    letters or box-drawing characters clear a floor it should not.
    """
    if not isinstance(text, str):
        return 0
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
               for ch in text.strip())


if __name__ == "__main__":                      # a one-line sanity check, not a test suite
    for s in ("看过了，不用再审", "the box is a fixed template slot", "", None):
        print(reason_width(s), repr(s))
