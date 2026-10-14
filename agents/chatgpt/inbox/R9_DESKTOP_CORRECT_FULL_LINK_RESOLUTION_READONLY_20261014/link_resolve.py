# -*- coding: utf-8 -*-
"""Offline link resolution in the formal destination namespace.

This diagnostic does not modify the production reader or the frozen plan.
A migrated E:\\BLACKBOX_ENGINES path is already a destination. It is not mapped again.
"""
from __future__ import annotations

from pathlib import PureWindowsPath

FORMAL = (r"E:\BLACKBOX_ENGINES", r"E:\BLACKBOX")
RESOURCE_LIMIT = 4096


def _clean(path: str) -> str:
    return str(path).replace("/", "\\").rstrip("\\")


def _under_formal(path: str) -> bool:
    text = _clean(path)
    upper = text.upper()
    for root in FORMAL:
        base = root.upper()
        if upper == base or upper.startswith(base + "\\"):
            return True
    return False


def _join(base: str, suffix: str) -> str:
    base = _clean(base)
    suffix = str(suffix).replace("/", "\\").strip("\\")
    if not suffix:
        return base
    return base + "\\" + suffix


class Graph:
    def __init__(self):
        self.directories = set()
        self.junctions = {}
        self.files = set()

    def add_directory(self, path: str) -> None:
        self.directories.add(_clean(path).casefold())

    def add_file(self, path: str) -> None:
        self.files.add(_clean(path).casefold())

    def add_junction(self, path: str, target: str) -> None:
        self.junctions[_clean(path).casefold()] = _clean(target)

    def _node(self, path: str):
        key = _clean(path).casefold()
        if key in self.junctions:
            return "junction", self.junctions[key]
        if key in self.directories:
            return "directory", path
        if key in self.files:
            return "file", path
        return None, None

    def _deepest_junction_prefix(self, path: str):
        current = _clean(path)
        while True:
            parent = str(PureWindowsPath(current).parent)
            if parent == current or len(parent) <= 3:
                return None
            key = parent.casefold()
            if key in self.junctions and _clean(path).casefold().startswith(key + "\\"):
                suffix = _clean(path)[len(parent):].lstrip("\\")
                return self.junctions[key], suffix, parent
            current = parent

    def resolve(self, start: str) -> dict:
        current = _clean(start)
        seen = []
        seen_keys = set()
        replacements = []
        for step in range(RESOURCE_LIMIT):
            key = current.casefold()
            if key in seen_keys:
                return self._result("CYCLE", current, step, replacements, seen)
            seen_keys.add(key)
            seen.append(current)
            if not _under_formal(current):
                return self._result("SCOPE_ESCAPE", current, step, replacements, seen)
            node, payload = self._node(current)
            if node == "junction":
                replacements.append({"from": current, "to": payload, "reason": "exact_junction"})
                current = _clean(payload)
                continue
            if node == "directory":
                return self._result("CLOSED_DIRECTORY", current, step, replacements, seen)
            if node == "file":
                return self._result("TARGET_FILE", current, step, replacements, seen)
            found = self._deepest_junction_prefix(current)
            if found is not None:
                target, suffix, parent = found
                rewritten = _join(target, suffix)
                replacements.append({
                    "from": current,
                    "to": rewritten,
                    "junction": parent,
                    "reason": "parent_junction_suffix",
                })
                current = rewritten
                continue
            missing = self._first_missing_ancestor(current)
            return self._result("MISSING_TERMINAL", current, step, replacements, seen, missing)
        return self._result("UNRESOLVED_RESOURCE_LIMIT", current, RESOURCE_LIMIT, replacements, seen)

    def _known_container(self, path: str) -> bool:
        key = _clean(path).casefold()
        if key in self.directories or key in self.junctions:
            return True
        return _clean(path).upper() in (r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES")

    def _first_missing_ancestor(self, path: str) -> str:
        current = _clean(path)
        missing = current
        while True:
            parent = str(PureWindowsPath(current).parent)
            if parent == current or len(parent) <= 3:
                return missing
            if self._known_container(parent):
                return missing
            missing = parent
            current = parent

    def _result(self, klass: str, terminal: str, steps: int, replacements: list, seen: list, missing=None) -> dict:
        return {
            "class": klass,
            "terminal": terminal,
            "steps": steps,
            "replacements": replacements,
            "chain_length": len(replacements),
            "states": seen,
            "missing_ancestor": missing,
            "windows_follow": "NOT_RUN",
        }
