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


D_UNC_ROOT = "\\\\192.168.100.2\\D_DRIVE"


def map_inventory_path(path: str, shares: dict | None = None) -> dict:
    """Map a plan inventory path. D UNC is used only when the share contract is bound."""
    text = str(path).replace("/", "\\")
    upper = text.upper()
    if upper == E_ROOT or upper.startswith(E_ROOT + "\\"):
        rel = text[len(E_ROOT):].lstrip("\\")
        source = E_UNC if not rel else E_UNC + "\\" + rel
        return {"source_path": source, "dest_path": text, "source_share": "E_DRIVE"}
    if upper.startswith("D:\\"):
        dest = D_DEST_ROOT + "\\" + text[3:]
        if shares and shares.get("d_unc_root"):
            root = str(shares["d_unc_root"]).rstrip("\\")
            return {"source_path": root + "\\" + text[3:], "dest_path": dest, "source_share": "D_DRIVE"}
        return {"source_path": text, "dest_path": dest, "source_share": "D_SHARE_NOT_IN_CONTRACT"}
    raise ValueError(f"UNMAPPED_PATH:{text}")


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


_SCHEMA_CACHE: dict = {}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    key = (id(conn), table)
    if key not in _SCHEMA_CACHE:
        if table not in _table_names(conn):
            _SCHEMA_CACHE[key] = set()
        else:
            _SCHEMA_CACHE[key] = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    return _SCHEMA_CACHE[key]


MOUNT_POINT_TAG = 0xA0000003
SYMLINK_TAG = 0xA000000C


def kind_from_reparse_tag(tag) -> str | None:
    if tag is None or str(tag).strip() == "":
        return None
    try:
        value = int(tag)
    except (TypeError, ValueError):
        return None
    if value == MOUNT_POINT_TAG:
        return "junction"
    if value == SYMLINK_TAG:
        return "symlink"
    return None


def plan_database_path(conn: sqlite3.Connection) -> Path:
    for _seq, name, file in conn.execute("PRAGMA database_list"):
        if name == "main" and file:
            return Path(file)
    raise RuntimeError("PLAN_PATH_UNBOUND")


def plan_freeze_status(path: Path) -> dict:
    """A plan is frozen only when no unmerged WAL or hot journal is present."""
    wal = Path(str(path) + "-wal")
    journal = Path(str(path) + "-journal")
    wal_bytes = wal.stat().st_size if wal.exists() else 0
    journal_bytes = journal.stat().st_size if journal.exists() else 0
    frozen = wal_bytes == 0 and journal_bytes == 0
    return {"frozen": frozen, "wal_bytes": wal_bytes, "journal_bytes": journal_bytes, "reason": None if frozen else "PLAN_NOT_FROZEN"}


def plan_digest(conn: sqlite3.Connection) -> str:
    """SHA256 of a frozen plan file. Does not checkpoint and does not ignore a live WAL."""
    import hashlib
    path = plan_database_path(conn)
    status = plan_freeze_status(path)
    if not status["frozen"]:
        raise RuntimeError("PLAN_NOT_FROZEN")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def lookup_mtime(inventory_path: str, bindings: dict | None) -> tuple:
    """Read mtime from bound input schemas. Missing evidence is a deficit, not a skip."""
    if not bindings:
        return None, "ABSENT_IN_PLAN"
    lookups = (
        ("delta", "files", ("mtime_utc", "mtime_ft")),
        ("base", "entries", ("mtime_utc", "mtime_ft")),
        ("d", "nodes", ("mtime_iso", "mtime_ft")),
    )
    for name, table, columns in lookups:
        conn = bindings.get(name)
        if conn is None or table not in _table_names(conn):
            continue
        present = _columns(conn, table)
        for column in columns:
            if column not in present or "path" not in present:
                continue
            row = conn.execute(f"SELECT {column} FROM {table} WHERE path=?", (inventory_path,)).fetchone()
            if row and row[0]:
                return row[0], f"FROM_{name.upper()}_{column.upper()}"
    return None, "MTIME_DEFICIT"


def read_executable(conn: sqlite3.Connection, bindings: dict | None = None, shares: dict | None = None):
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
            inventory_paths = []
            for (inventory_path,) in stored:
                mapped.append(map_inventory_path(inventory_path, shares))
                inventory_paths.append(inventory_path)
            if not mapped:
                yield {
                    "entity_key": f"{volume}|{file_id}",
                    "volume_serial": volume,
                    "file_id": file_id,
                    "logical_size": size,
                    "path_count": path_count,
                    "mtime": None,
                    "mtime_status": "PLAN_ORPHAN_ENTITY",
                    "orphan": True,
                    "source_path": None,
                    "dest_path": None,
                    "extra_dest_paths": [],
                    "source_share": None,
                }
                continue
            status = "FROM_PLAN" if mtime is not None else "ABSENT_IN_PLAN"
            if mtime is None:
                mtime, status = lookup_mtime(inventory_paths[0], bindings)
            yield {
                "entity_key": f"{volume}|{file_id}",
                "volume_serial": volume,
                "file_id": file_id,
                "logical_size": size,
                "path_count": path_count,
                "mtime": mtime,
                "mtime_status": status,
                "inventory_path": inventory_paths[0],
                "source_path": mapped[0]["source_path"],
                "dest_path": mapped[0]["dest_path"],
                "extra_dest_paths": [item["dest_path"] for item in mapped[1:]],
                "source_share": mapped[0]["source_share"],
            }


def dest_allowed(path: str) -> bool:
    text = str(path).replace("/", "\\").rstrip("\\")
    if text.startswith("\\\\") or text.upper().startswith("D:\\"):
        return False
    upper = text.upper()
    for root in ("E:\\BLACKBOX", "E:\\BLACKBOX_ENGINES"):
        if upper == root or upper.startswith(root + "\\"):
            return True
    return False


def iter_directories(conn: sqlite3.Connection):
    if "paths" not in _table_names(conn):
        return
    cur = conn.execute("SELECT path FROM paths WHERE is_dir=1 AND is_reparse=0")
    while True:
        rows = cur.fetchmany(200)
        if not rows:
            break
        for (inventory_path,) in rows:
            mapped = map_inventory_path(inventory_path)
            yield {"inventory_path": inventory_path, "dest_path": mapped["dest_path"], "source_share": mapped["source_share"]}


def iter_links(conn: sqlite3.Connection, bindings: dict | None = None):
    """Migrated link path and target. Kind comes from a reparse tag, never a guessed junction."""
    if "links" not in _table_names(conn):
        return
    columns = _columns(conn, "links")
    tag_sql = "reparse_tag" if "reparse_tag" in columns else "NULL"
    cur = conn.execute(f"SELECT path, target, migrated_link_path, migrated_target, status, {tag_sql} FROM links")
    while True:
        rows = cur.fetchmany(200)
        if not rows:
            break
        for path, target, migrated_link, migrated_target, status, tag in rows:
            try:
                link_path = migrated_link or map_inventory_path(path)["dest_path"]
                link_target = migrated_target or map_inventory_path(target)["dest_path"]
                blocked = not (dest_allowed(link_path) and dest_allowed(link_target))
                reason = None if not blocked else "BAD_LINK_TARGET"
            except ValueError:
                link_path = migrated_link or path
                link_target = migrated_target or target
                blocked = True
                reason = "BAD_LINK_TARGET"
            if tag is None and bindings:
                tag = _lookup_reparse_tag(path, bindings)
            kind = kind_from_reparse_tag(tag)
            if kind is None:
                blocked = True
                reason = reason or "LINK_TYPE_DEFICIT"
            yield {
                "link_path": link_path,
                "target": link_target,
                "kind": kind,
                "reparse_tag": tag,
                "status": status,
                "blocked": blocked,
                "reason": reason,
            }


def _lookup_reparse_tag(inventory_path: str, bindings: dict):
    for name, table, column in (("base", "entries", "reparse_tag"), ("d", "nodes", "object_class")):
        conn = bindings.get(name)
        if conn is None or column not in _columns(conn, table):
            continue
        row = conn.execute(f"SELECT {column} FROM {table} WHERE path=?", (inventory_path,)).fetchone()
        if row and row[0] not in (None, "", 0):
            return row[0]
    return None


def order_links(links) -> list[dict]:
    items = []
    for item in links:
        if item.get("blocked") or not item.get("kind") or not dest_allowed(item["link_path"]) or not dest_allowed(item["target"]):
            raise RuntimeError(item.get("reason") or "BAD_LINK_TARGET")
        items.append(item)
    by = {}
    for item in items:
        key = item["link_path"].casefold()
        if key in by:
            raise RuntimeError("LINK_PATH_CONFLICT")
        by[key] = item
    edges = [(item["link_path"], item["target"]) for item in items]
    from r9_adapter import walk_reparse
    for item in items:
        if walk_reparse(item["link_path"], edges):
            raise RuntimeError("REPARSE_CYCLE")
    ordered = []
    pending = list(items)
    while pending:
        ready = []
        rest = []
        done = {item["link_path"].casefold() for item in ordered}
        for item in pending:
            target = item["target"].rstrip("\\").casefold()
            blocked = False
            for key in by:
                if key in done or key == item["link_path"].casefold():
                    continue
                if target == key or target.startswith(key + "\\"):
                    blocked = True
                    break
            if blocked:
                rest.append(item)
            else:
                ready.append(item)
        if not ready:
            raise RuntimeError("REPARSE_CYCLE")
        ordered.extend(ready)
        pending = rest
    return ordered


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
