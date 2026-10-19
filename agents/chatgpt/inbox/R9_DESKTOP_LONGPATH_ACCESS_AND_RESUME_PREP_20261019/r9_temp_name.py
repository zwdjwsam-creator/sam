# -*- coding: utf-8 -*-
"""Bounded destination temp names. Does not touch E:."""
from __future__ import annotations

import hashlib

SAFE_API_CHARS = 32760
PARTIAL_SUFFIX = ".partial"


def api_chars(path: str) -> int:
    if path.startswith("\\\\?\\"):
        return len(path)
    if path.startswith("\\\\"):
        return len(path) + 6
    return len(path) + 4


def temp_path(dest: str) -> str:
    parent, name = dest.rsplit("\\", 1)
    naive = dest + PARTIAL_SUFFIX
    if api_chars(naive) <= SAFE_API_CHARS and len(name) + len(PARTIAL_SUFFIX) <= 255:
        return naive
    token = hashlib.sha256(dest.encode("utf-8")).hexdigest()[:16]
    bounded = parent + "\\.r9" + token + ".partial"
    if api_chars(bounded) > SAFE_API_CHARS or len(bounded.rsplit("\\", 1)[1]) > 255:
        raise ValueError("TEMP_STILL_TOO_LONG")
    return bounded
