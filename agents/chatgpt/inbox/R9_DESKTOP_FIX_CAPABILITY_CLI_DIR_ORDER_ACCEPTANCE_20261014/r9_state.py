# -*- coding: utf-8 -*-
"""Small SQLite run state. Handles are closed by the caller."""
from __future__ import annotations

import sqlite3
from pathlib import Path


def open_state(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS run_bind(
            run_id TEXT PRIMARY KEY,
            plan_digest TEXT,
            inputs_digest TEXT,
            code_digest TEXT,
            dest_volume TEXT,
            dest_root TEXT
        );
        CREATE TABLE IF NOT EXISTS stage(
            item_key TEXT PRIMARY KEY,
            kind TEXT,
            phase TEXT,
            dest_path TEXT,
            sha256 TEXT,
            file_id TEXT,
            volume_serial TEXT,
            object_type TEXT,
            link_target TEXT,
            logical_size INTEGER,
            parent_key TEXT
        );
        """
    )
    db.commit()
    return db


def bind_run(db: sqlite3.Connection, run: dict | None, required: bool = False) -> None:
    if not run:
        if required:
            raise RuntimeError("RUN_BINDING_MISSING")
        return
    required_keys = ("run_id", "plan_digest", "inputs_digest", "code_digest", "dest_volume", "dest_root")
    if any(run.get(key) in (None, "") for key in required_keys):
        raise RuntimeError("RUN_BINDING_MISSING")
    current = tuple(run[key] for key in required_keys)
    row = db.execute(
        "SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind"
    ).fetchone()
    if row is None:
        db.execute("INSERT INTO run_bind VALUES (?,?,?,?,?,?)", current)
        db.commit()
        return
    if tuple(row) != current:
        raise RuntimeError("RUN_BINDING_MISMATCH")


def get_stage(db: sqlite3.Connection, item_key: str) -> dict | None:
    row = db.execute(
        """
        SELECT phase, dest_path, sha256, file_id, volume_serial, object_type, link_target, logical_size, parent_key, kind
        FROM stage WHERE item_key=?
        """,
        (item_key,),
    ).fetchone()
    if row is None:
        return None
    names = ["phase", "dest_path", "sha256", "file_id", "volume_serial", "object_type", "link_target", "logical_size", "parent_key", "kind"]
    return dict(zip(names, row))


def put_stage(db: sqlite3.Connection, item_key: str, **fields) -> None:
    current = get_stage(db, item_key) or {}
    current.update(fields)
    db.execute("DELETE FROM stage WHERE item_key=?", (item_key,))
    db.execute(
        """
        INSERT INTO stage(item_key, kind, phase, dest_path, sha256, file_id, volume_serial, object_type, link_target, logical_size, parent_key)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            item_key,
            current.get("kind"),
            current.get("phase"),
            current.get("dest_path"),
            current.get("sha256"),
            current.get("file_id"),
            current.get("volume_serial"),
            current.get("object_type"),
            current.get("link_target"),
            current.get("logical_size"),
            current.get("parent_key"),
        ),
    )


def destination_matches(observed: dict, stage: dict) -> bool:
    if observed.get("status") != "PRESENT":
        return False
    if stage.get("sha256") and observed.get("sha256") != stage["sha256"]:
        return False
    if stage.get("file_id") and observed.get("file_id") != stage["file_id"]:
        return False
    if stage.get("volume_serial") and observed.get("volume_serial") != stage["volume_serial"]:
        return False
    if stage.get("object_type") and observed.get("object_type") != stage["object_type"]:
        return False
    if stage.get("link_target") and observed.get("reparse_target") != stage["link_target"]:
        return False
    if stage.get("logical_size") is not None and observed.get("logical_size") != stage["logical_size"]:
        return False
    return True
