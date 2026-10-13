# -*- coding: utf-8 -*-
"""Stream entities from the bound plan. Never fetchall the full table."""
from __future__ import annotations

import sqlite3
from pathlib import Path

PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
E_UNC = r"\\192.168.100.2\E_DRIVE\BLACKBOX"
D_UNC_BLOCKER = "D source share is not in the handoff contract; D_DRIVE was not guessed"


def connect(plan: Path = PLAN) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{plan.resolve().as_posix()}?mode=ro", uri=True)


def query_plan(plan: Path = PLAN) -> list:
    conn = connect(plan)
    try:
        return conn.execute(
            "EXPLAIN QUERY PLAN SELECT volume_serial, file_id, min_size, path_count FROM entities"
        ).fetchall()
    finally:
        conn.close()


def sample_entities(plan: Path = PLAN, limit: int = 3) -> list[dict]:
    conn = connect(plan)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT volume_serial, file_id, min_size, path_count, d_paths, delta_paths FROM entities LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


E_ROOT = "E:\\BLACKBOX"
E_UNC = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX"
D_DEST_ROOT = "E:\\BLACKBOX_ENGINES"


def map_inventory_path(path: str) -> dict:
    """Map a plan inventory path to source and destination. D share is not guessed."""
    text = str(path).replace("/", "\\")
    upper = text.upper()
    if upper == E_ROOT or upper.startswith(E_ROOT + "\\"):
        rel = text[len(E_ROOT):].lstrip("\\")
        source = E_UNC if not rel else E_UNC + "\\" + rel
        return {"source_path": source, "dest_path": text, "source_share": "KNOWN_E"}
    if upper.startswith("D:\\"):
        return {
            "source_path": text,
            "dest_path": D_DEST_ROOT + "\\" + text[3:],
            "source_share": "D_SHARE_NOT_IN_CONTRACT",
        }
    raise ValueError(f"UNMAPPED_PATH:{text}")


def read_executable(conn: sqlite3.Connection):
    """Stream entities using the published plan columns. No source_path column required."""
    path_cols = {row[1] for row in conn.execute("PRAGMA table_info(paths)")}
    if "path" not in path_cols:
        raise RuntimeError("PLAN_SCHEMA_MISSING_PATH")
    cols = {row[1] for row in conn.execute("PRAGMA table_info(entities)")}
    mtime_sql = "mtime" if "mtime" in cols else "NULL"
    cur = conn.execute(f"SELECT volume_serial, file_id, min_size, path_count, {mtime_sql} FROM entities")
    while True:
        rows = cur.fetchmany(100)
        if not rows:
            break
        for volume, file_id, size, path_count, mtime in rows:
            stored = conn.execute(
                "SELECT path FROM paths WHERE is_dir=0 AND is_reparse=0 AND volume_serial=? AND file_id=? ORDER BY path",
                (volume, file_id),
            )
            mapped = []
            for (inventory_path,) in stored:
                mapped.append(map_inventory_path(inventory_path))
            if not mapped:
                continue
            yield {
                "entity_key": f"{volume}|{file_id}",
                "volume_serial": volume,
                "file_id": file_id,
                "logical_size": size,
                "path_count": path_count,
                "mtime": mtime,
                "mtime_status": "FROM_PLAN" if mtime is not None else "ABSENT_IN_PLAN",
                "source_path": mapped[0]["source_path"],
                "dest_path": mapped[0]["dest_path"],
                "extra_dest_paths": [item["dest_path"] for item in mapped[1:]],
                "source_share": mapped[0]["source_share"],
            }


def iter_entities(plan: Path = PLAN, batch: int = 1000):
    """One sequential scan. Caller must not materialize the whole result."""
    conn = connect(plan)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT volume_serial, file_id, min_size, path_count FROM entities"
    )
    try:
        while True:
            rows = cur.fetchmany(batch)
            if not rows:
                break
            for row in rows:
                yield {
                    "entity_key": f"{row['volume_serial']}|{row['file_id']}",
                    "volume_serial": row["volume_serial"],
                    "file_id": row["file_id"],
                    "logical_size": row["min_size"],
                    "path_count": row["path_count"],
                    "source_unc_note": E_UNC if str(row["volume_serial"]) == "2387166462" else D_UNC_BLOCKER,
                }
    finally:
        conn.close()
