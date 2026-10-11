# -*- coding: utf-8 -*-
"""Path normalization helpers for R2 repair."""
from __future__ import annotations


def normalize_win_path(p: str | None) -> str | None:
    if p is None:
        return None
    s = str(p).strip().replace("/", "\\")
    if not s:
        return s
    if s.startswith("\\\\?\\UNC\\"):
        s = "\\" + s[7:]  # \\server\share...
    elif s.startswith("\\\\?\\"):
        s = s[4:]
    # collapse duplicate backslashes except UNC prefix
    if s.startswith("\\\\"):
        body = s[2:]
        while "\\\\" in body:
            body = body.replace("\\\\", "\\")
        s = "\\\\" + body
    else:
        while "\\\\" in s:
            s = s.replace("\\\\", "\\")
    if len(s) >= 3 and s[1] == ":" and s[2] != "\\":
        s = s[:2] + "\\" + s[2:]
    return s


def path_under(path: str, root: str) -> bool:
    p = normalize_win_path(path)
    r = normalize_win_path(root)
    if not p or not r:
        return False
    pu, ru = p.rstrip("\\").upper(), r.rstrip("\\").upper()
    return pu == ru or pu.startswith(ru + "\\")
