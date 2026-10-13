# -*- coding: utf-8 -*-
"""Production runner. Preparation contracts never reach a write syscall."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from r9_winio import WindowsBackend, Win32Syscalls


def allows_write(contract: dict, backend=None) -> bool:
    if contract.get("phase") != "SIMULATED_CHAIN":
        return False
    binding = contract.get("dest_binding")
    if not isinstance(binding, dict) or not binding.get("volume_serial"):
        return False
    if backend is None:
        return False
    from r9_winio import VirtualSyscalls
    return isinstance(getattr(backend, "sc", None), VirtualSyscalls)


def production_run(entities, backend: WindowsBackend, contract: dict, state_path: Path) -> dict:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state_path)
    db.execute("CREATE TABLE IF NOT EXISTS done(entity_key TEXT PRIMARY KEY, dest_path TEXT, sha256 TEXT, dest_file_id TEXT, dest_volume_serial TEXT)")
    db.commit()
    if not allows_write(contract, backend):
        db.close()
        return {"refused_before_write": True, "write_calls": getattr(backend.sc, "write_calls", 0), "backend_calls": backend.calls}
    for directory in contract.get("directories", ()):
        backend.ensure_directory(directory)
    copied = []
    linked = []
    for entity in entities:
        existing = db.execute("SELECT dest_path, sha256, dest_file_id, dest_volume_serial FROM done WHERE entity_key=?", (entity["entity_key"],)).fetchone()
        observed = backend.observe_destination(entity["dest_path"])
        if existing:
            if observed.get("status") != "PRESENT" or observed.get("sha256") != existing[1] or observed.get("file_id") != existing[2] or observed.get("volume_serial") != existing[3]:
                db.close()
                raise RuntimeError("RESUME_DEST_MISMATCH")
            record = {"dest_path": existing[0], "sha256": existing[1], "dest_file_id": existing[2], "dest_volume_serial": existing[3], "bytes": entity["logical_size"]}
        elif observed.get("status") == "PRESENT":
            db.close()
            raise RuntimeError("UNKNOWN_TARGET_EXISTS")
        else:
            record = backend.copy_entity(entity)
            db.execute(
                "INSERT INTO done(entity_key, dest_path, sha256, dest_file_id, dest_volume_serial) VALUES (?,?,?,?,?)",
                (entity["entity_key"], record["dest_path"], record["sha256"], record["dest_file_id"], record["dest_volume_serial"]),
            )
            db.commit()
        copied.append(record)
        for alias in entity.get("extra_dest_paths", ()):
            seen = backend.observe_destination(alias)
            if seen.get("status") == "PRESENT":
                if seen.get("file_id") != record["dest_file_id"] or seen.get("volume_serial") != record["dest_volume_serial"]:
                    db.close()
                    raise RuntimeError("RESUME_ALIAS_MISMATCH")
                linked.append({"dest_path": alias, "skipped": True, "dest_file_id": seen.get("file_id"), "dest_volume_serial": seen.get("volume_serial")})
                continue
            link = backend.hardlink(record["dest_path"], alias)
            linked.append(link)
    db.close()
    return {"refused_before_write": False, "copied": copied, "linked": linked, "backend_calls": backend.calls}
