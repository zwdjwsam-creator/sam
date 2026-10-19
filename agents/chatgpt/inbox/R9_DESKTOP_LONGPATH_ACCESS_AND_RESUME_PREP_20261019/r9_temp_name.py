# -*- coding: utf-8 -*-
"""UTF-16 aware temporary names. 32700 is an engineering margin, not a Windows guarantee."""
from __future__ import annotations

import hashlib

ENGINEERING_MARGIN_UTF16 = 32700
PARTIAL_SUFFIX = ".partial"


def utf16_units(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def api_utf16(path: str) -> int:
    if path.startswith("\\\\?\\"):
        extended = path
    elif path.startswith("\\\\"):
        extended = "\\\\?\\UNC\\" + path[2:]
    else:
        extended = "\\\\?\\" + path
    return utf16_units(extended)


def temp_path(dest: str) -> str:
    parent, name = dest.rsplit("\\", 1)
    naive = dest + PARTIAL_SUFFIX
    naive_name_units = utf16_units(name + PARTIAL_SUFFIX)
    if api_utf16(naive) <= ENGINEERING_MARGIN_UTF16 and naive_name_units <= 255:
        return naive
    token = hashlib.sha256(dest.encode("utf-8")).hexdigest()[:16]
    bounded_name = ".r9" + token + ".partial"
    bounded = parent + "\\" + bounded_name
    if api_utf16(bounded) > ENGINEERING_MARGIN_UTF16 or utf16_units(bounded_name) > 255:
        raise ValueError("TEMP_STILL_TOO_LONG")
    return bounded
