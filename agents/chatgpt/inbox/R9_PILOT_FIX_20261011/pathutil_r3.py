# -*- coding: utf-8 -*-
"""Hardened path helpers — absolute only; reject traversal / relative / drive-relative."""
from __future__ import annotations


def normalize_win_path(p: str | None) -> str | None:
    if p is None:
        return None
    s = str(p).strip().replace("/", "\\")
    if not s:
        return s
    if s.startswith("\\\\?\\UNC\\"):
        s = "\\" + s[7:]
    elif s.startswith("\\\\?\\"):
        s = s[4:]
    elif s.startswith("\\??\\"):
        s = s[4:]
    if s.startswith("\\\\"):
        body = s[2:]
        while "\\\\" in body:
            body = body.replace("\\\\", "\\")
        s = "\\\\" + body
    else:
        while "\\\\" in s:
            s = s.replace("\\\\", "\\")
    # Drive-relative (E:foo) must stay non-absolute; do not inject '\'.
    return s


def is_absolute_win_path(p: str | None) -> bool:
    s = normalize_win_path(p)
    if not s:
        return False
    if s.startswith("\\\\"):
        return True
    return len(s) >= 3 and s[1] == ":" and s[2] == "\\"


def has_traversal(p: str | None) -> bool:
    s = normalize_win_path(p)
    if not s:
        return False
    parts = s.split("\\")
    return any(part == ".." for part in parts)


def path_under(path: str, root: str) -> bool:
    """Strict containment: both must be absolute; reject .. / relative / drive-relative."""
    if not is_absolute_win_path(path) or not is_absolute_win_path(root):
        return False
    if has_traversal(path) or has_traversal(root):
        return False
    p = normalize_win_path(path)
    r = normalize_win_path(root)
    assert p and r
    pu, ru = p.rstrip("\\").upper(), r.rstrip("\\").upper()
    return pu == ru or pu.startswith(ru + "\\")


def require_absolute(path: str, label: str = "path") -> str:
    n = normalize_win_path(path)
    if not is_absolute_win_path(n):
        raise ValueError(f"{label}_NOT_ABSOLUTE:{path!r}")
    if has_traversal(n):
        raise ValueError(f"{label}_TRAVERSAL:{path!r}")
    return n  # type: ignore[return-value]
