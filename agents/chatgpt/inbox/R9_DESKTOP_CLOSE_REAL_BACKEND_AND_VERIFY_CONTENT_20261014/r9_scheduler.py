# -*- coding: utf-8 -*-
"""Batch scheduler. Preparation gate returns before any backend call."""
from __future__ import annotations


class PreparationGate:
    def allows_write(self, contract: dict | None = None) -> bool:
        contract = contract or {}
        if contract.get("phase") != "WRITE_AUTHORIZED":
            return False
        if contract.get("format_confirmed") is not True:
            return False
        if not contract.get("dest_binding_id"):
            return False
        return True


def run_batch(entities, backend, gate: PreparationGate, contract: dict | None = None) -> dict:
    if not gate.allows_write(contract):
        return {"refused_before_write": True, "backend_calls": backend.calls}
    copied = 0
    linked = 0
    for entity in entities:
        backend.copy_entity(entity)
        copied += 1
        for extra in entity.get("extra_paths", ()):
            backend.hardlink(entity["representative"], extra, entity["volume_serial"])
            linked += 1
    return {"refused_before_write": False, "copied": copied, "linked": linked, "backend_calls": backend.calls}


class FakeBackend:
    def __init__(self):
        self.calls = 0
        self.copies = []
        self.links = []

    def copy_entity(self, entity):
        self.calls += 1
        self.copies.append(entity["entity_key"])

    def hardlink(self, source, dest, volume):
        self.calls += 1
        self.links.append((source, dest, volume))
