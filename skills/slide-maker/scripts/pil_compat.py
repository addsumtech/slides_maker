#!/usr/bin/env python3
"""Pillow version shims, so one call works on every Pillow the skill allows (requirements: Pillow>=10).

`pixels(im)` — an image's pixel values, flattened (what `Image.getdata()` returned). Pillow 12+ warns that getdata() is deprecated
and Pillow 14 removes it (2027-10-15); its replacement `get_flattened_data()` exists only from Pillow 12, so this
uses whichever the installed Pillow has. tests/test_pillow_compat.py names any getdata() call added elsewhere.
"""


def pixels(im):
    """The pixel values of `im`, flattened row by row — one tuple (or int, for single-band modes) per pixel."""
    flat = getattr(im, "get_flattened_data", None)
    return flat() if flat is not None else im.getdata()
