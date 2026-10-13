# -*- coding: utf-8 -*-
"""Production runner. Preparation contracts never reach a write syscall."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from r9_winio import WindowsBackend, Win32Syscalls


def allows_write(contract: dict) -> bool:
    if contract.get("phase") != "SIMULATED_CHAIN":
        return False
    binding = contract.get("dest_binding")
    return isinstance(binding, dict) and bool(binding.get("volume_serial"))


def production_run(entities, backend: WindowsBackend, contract: dict, state_path: Path) -> dict:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state_path)
    db.execute("CREATE TABLE IF NOT EXISTS done(entity_key TEXT PRIMARY KEY, dest_path TEXT, sha256 TEXT, dest_file_id TEXT, dest_volume_serial TEXT)")
    db.commit()
    if not allows_write(contract):
        db.close()
        return {"refused_before_write": True, "write_calls": getattr(backend.sc, "write_calls", 0), "backend_calls": backend.calls}
    copied = []
    linked = []
    for entity in entities:
        existing = db.execute("SELECT dest_path, sha256, dest_file_id, dest_volume_serial FROM done WHERE entity_key=?", (entity["entity_key"],)).fetchone()
        if existing:
            record = {"dest_path": existing[0], "sha256": existing[1], "dest_file_id": existing[2], "dest_volume_serial": existing[3], "bytes": entity["logical_size"]}
        else:
            record = backend.copy_entity(entity)
            db.execute(
                "INSERT INTO done(entity_key, dest_path, sha256, dest_file_id, dest_volume_serial) VALUES (?,?,?,?,?)",
                (entity["entity_key"], record["dest_path"], record["sha256"], record["dest_file_id"], record["dest_volume_serial"]),
            )
            db.commit()
        copied.append(record)
        for alias in entity.get("extra_dest_paths", ()):
            link = backend.hardlink(record["dest_path"], alias)
            linked.append(link)
    db.close()
    return {"refused_before_write": False, "copied": copied, "linked": linked, "backend_calls": backend.calls}
