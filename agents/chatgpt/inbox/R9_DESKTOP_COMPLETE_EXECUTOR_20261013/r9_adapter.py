# -*- coding: utf-8 -*-
"""Real input validation and merged read-only plan for R9.

copy is not executed. This module does not write to E: or create links.
"""
from __future__ import annotations

import hashlib
import json
import socket
import sqlite3
from pathlib import Path

E_BASE_SHA = "a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572"
E_BASE_BYTES = 9376645120
DELTA_SHA = "aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c"
DELTA_BYTES = 86016
D_SHA = "4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795"
D_BYTES = 48635904
ORIGINAL_D_SHA = "787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39"
OLD_REPAIRED_SNAPSHOT_SHA = "e3e0f653114782067fcc1df1d5e6d9a6c0f2d2f992f6c93649dae5831b3977a7"
HISTORICAL_DEST_SERIAL = "806508DF"
DISK_UNIQUE_HINT = "eui.E8238FA6BF530001001B448B42E694AE"
INVALID = {"", "none", "null", "0"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)


def _bad_id(value) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in INVALID


def check_binding(path: Path, expected_sha: str, expected_bytes: int, role: str) -> dict:
    if not path.exists():
        return {"role": role, "ok": False, "reason": "MISSING", "path": str(path)}
    size = path.stat().st_size
    actual = sha256_file(path)
    reason = "OK"
    ok = actual.lower() == expected_sha.lower() and size == expected_bytes
    if not ok:
        reason = "SHA_OR_SIZE_MISMATCH"
    if role == "d_repaired" and actual.lower() in {ORIGINAL_D_SHA, OLD_REPAIRED_SNAPSHOT_SHA}:
        ok = False
        reason = "REJECT_OLD_D_SHA"
    if role == "d_repaired" and expected_sha.lower() in {ORIGINAL_D_SHA, OLD_REPAIRED_SNAPSHOT_SHA}:
        ok = False
        reason = "CONTRACT_USES_OLD_D_SHA"
    integrity = None
    if path.suffix == ".sqlite" and ok:
        integrity = _ro(path).execute("pragma integrity_check").fetchone()[0]
        if integrity != "ok":
            ok = False
            reason = "INTEGRITY_FAIL"
    return {
        "role": role,
        "path": str(path),
        "bytes": size,
        "sha256": actual,
        "ok": ok,
        "reason": reason,
        "integrity": integrity,
    }


def validate_inputs(e_base: Path, e_delta: Path, d_sqlite: Path) -> tuple[int, list[dict]]:
    rows = [
        check_binding(e_base, E_BASE_SHA, E_BASE_BYTES, "e_base"),
        check_binding(e_delta, DELTA_SHA, DELTA_BYTES, "e_delta"),
        check_binding(d_sqlite, D_SHA, D_BYTES, "d_repaired"),
    ]
    # schema spot checks
    if rows[1]["ok"]:
        cols = [r[1] for r in _ro(e_delta).execute("pragma table_info(files)")]
        if "volume_serial_dword" not in cols or "file_id" not in cols:
            rows.append({"role": "e_delta_schema", "ok": False, "reason": "MISSING_CANONICAL_IDENTITY"})
    if rows[2]["ok"]:
        cols = [r[1] for r in _ro(d_sqlite).execute("pragma table_info(nodes)")]
        for need in ("path", "is_dir", "is_reparse", "logical_size", "volume_serial", "file_id"):
            if need not in cols:
                rows.append({"role": "d_schema", "ok": False, "reason": f"MISSING_{need}"})
    code = 0 if all(r["ok"] for r in rows) else 2
    return code, rows


def _init(out: Path) -> sqlite3.Connection:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    conn = sqlite3.connect(out)
    conn.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE paths (
          path TEXT PRIMARY KEY,
          is_dir INTEGER NOT NULL,
          is_reparse INTEGER NOT NULL,
          logical_size INTEGER,
          alloc_size INTEGER,
          volume_serial TEXT,
          file_id TEXT,
          nlinks INTEGER,
          reparse_target TEXT,
          source TEXT NOT NULL
        );
        CREATE TABLE deficits(id INTEGER PRIMARY KEY, code TEXT, detail TEXT);
        CREATE TABLE stats(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE links(path TEXT PRIMARY KEY, target TEXT, source TEXT, mapped_dest TEXT, status TEXT);
        """
    )
    return conn


def _map_target(target: str) -> tuple[str, str]:
    if target is None or str(target).strip() == "":
        return "", "UNRESOLVED"
    text = str(target).replace("/", "\\")
    if ".." in text.split("\\"):
        return "", "ESCAPE"
    if len(text) >= 3 and text[1] == ":" and text[2] == "\\":
        if text.upper().startswith("E:\\BLACKBOX\\") or text.upper() == "E:\\BLACKBOX":
            return text, "MAPPED_E_BLACKBOX"
        if text.upper().startswith("D:\\"):
            rest = text[3:]
            return "E:\\BLACKBOX_ENGINES\\" + rest, "MAPPED_D_ROOT"
        return "", "OUTSIDE_ROOT"
    return "", "NOT_ABSOLUTE"


def build_plan(e_base: Path, e_delta: Path, d_sqlite: Path, out: Path) -> tuple[int, dict]:
    conn = _init(out)
    conn.execute("ATTACH DATABASE ? AS base", (str(e_base),))
    conn.execute("ATTACH DATABASE ? AS delta", (str(e_delta),))
    conn.execute("ATTACH DATABASE ? AS dsrc", (str(d_sqlite),))
    conn.execute("BEGIN")
    conn.execute(
        """
        INSERT INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source)
        SELECT path, is_dir,
               CASE WHEN reparse_tag IS NOT NULL AND reparse_tag != 0 THEN 1 ELSE 0 END,
               logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, 'base'
        FROM base.entries
        """
    )
    conn.execute("DELETE FROM paths WHERE path IN (SELECT path FROM delta.files)")
    conn.execute(
        """
        INSERT INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source)
        SELECT path, 0, 0, size, allocation_size, CAST(volume_serial_dword AS TEXT), file_id, nlinks, NULL, 'delta'
        FROM delta.files
        """
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source)
        SELECT path, is_dir, is_reparse, logical_size, NULL, volume_serial, file_id, nlinks, NULL, 'd'
        FROM dsrc.nodes
        """
    )
    conn.execute("COMMIT")
    conn.execute("CREATE INDEX ix_entity ON paths(is_dir, is_reparse, volume_serial, file_id)")

    overlay = conn.execute(
        "SELECT COUNT(*) FROM delta.files d JOIN base.entries b ON b.path=d.path"
    ).fetchone()[0]

    # entity stats: normal files only
    conn.execute(
        """
        CREATE TABLE entities AS
        SELECT volume_serial, file_id,
               COUNT(*) AS path_count,
               MIN(logical_size) AS min_size,
               MAX(logical_size) AS max_size,
               MAX(nlinks) AS max_nlinks,
               SUM(CASE WHEN source='d' THEN 1 ELSE 0 END) AS d_paths,
               SUM(CASE WHEN source='delta' THEN 1 ELSE 0 END) AS delta_paths
        FROM paths
        WHERE is_dir=0 AND is_reparse=0
        GROUP BY volume_serial, file_id
        """
    )
    bad_id = conn.execute(
        """
        SELECT COUNT(*) FROM paths
        WHERE is_dir=0 AND is_reparse=0
          AND (volume_serial IS NULL OR file_id IS NULL OR lower(file_id) IN ('','none','null','0')
               OR lower(volume_serial) IN ('','none','null','0'))
        """
    ).fetchone()[0]
    size_conflict = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE min_size IS NOT NULL AND max_size IS NOT NULL AND min_size != max_size"
    ).fetchone()[0]
    if bad_id:
        conn.execute("INSERT INTO deficits(code,detail) VALUES('NULL_IDENTITY',?)", (str(bad_id),))
    if size_conflict:
        conn.execute("INSERT INTO deficits(code,detail) VALUES('ENTITY_SIZE_CONFLICT',?)", (str(size_conflict),))

    # links
    for path, target, source in conn.execute(
        "SELECT path, reparse_target, source FROM paths WHERE is_reparse=1"
    ):
        mapped, status = _map_target(target)
        conn.execute(
            "INSERT OR REPLACE INTO links(path,target,source,mapped_dest,status) VALUES(?,?,?,?,?)",
            (path, target, source, mapped, status),
        )
    bad_links = conn.execute(
        "SELECT status, COUNT(*) FROM links WHERE status != 'MAPPED_E_BLACKBOX' AND status != 'MAPPED_D_ROOT' GROUP BY status"
    ).fetchall()
    for status, count in bad_links:
        conn.execute("INSERT INTO deficits(code,detail) VALUES(?,?)", (f"LINK_{status}", str(count)))

    d_files = conn.execute("SELECT COUNT(*) FROM paths WHERE source='d' AND is_dir=0 AND is_reparse=0").fetchone()[0]
    d_dirs = conn.execute("SELECT COUNT(*) FROM paths WHERE source='d' AND is_dir=1 AND is_reparse=0").fetchone()[0]
    d_reparse = conn.execute("SELECT COUNT(*) FROM paths WHERE source='d' AND is_reparse=1").fetchone()[0]
    if d_files == 0:
        conn.execute("INSERT INTO deficits(code,detail) VALUES('D_NOT_MERGED','0')")

    file_paths = conn.execute("SELECT COUNT(*) FROM paths WHERE is_dir=0 AND is_reparse=0").fetchone()[0]
    dir_paths = conn.execute("SELECT COUNT(*) FROM paths WHERE is_dir=1 AND is_reparse=0").fetchone()[0]
    logical = conn.execute(
        "SELECT COALESCE(SUM(logical_size),0) FROM paths WHERE is_dir=0 AND is_reparse=0"
    ).fetchone()[0]
    unique_bytes = conn.execute(
        "SELECT COALESCE(SUM(min_size),0) FROM entities WHERE min_size=max_size"
    ).fetchone()[0]
    entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    d_entities = conn.execute("SELECT COUNT(*) FROM entities WHERE d_paths>0 AND delta_paths=0").fetchone()[0]
    delta_entities = conn.execute("SELECT COUNT(*) FROM entities WHERE delta_paths>0").fetchone()[0]
    link_count = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]

    stats = {
        "file_paths": int(file_paths),
        "dir_paths": int(dir_paths),
        "entity_count": int(entity_count),
        "unique_content_bytes": int(unique_bytes),
        "logical_path_bytes": int(logical),
        "links": int(link_count),
        "d_file_paths": int(d_files),
        "d_dirs": int(d_dirs),
        "d_reparse": int(d_reparse),
        "d_entities": int(d_entities),
        "delta_entities": int(delta_entities),
        "delta_paths_already_in_base": int(overlay),
        "null_identity_files": int(bad_id),
        "entity_size_conflicts": int(size_conflict),
    }
    for key, value in stats.items():
        conn.execute("INSERT INTO stats(key,value) VALUES(?,?)", (key, str(value)))

    deficit_n = conn.execute("SELECT COUNT(*) FROM deficits").fetchone()[0]
    plan_ready = deficit_n == 0 and file_paths > 0 and d_files > 0
    conn.execute("INSERT INTO stats(key,value) VALUES('plan_ready',?)", ("true" if plan_ready else "false",))
    conn.commit()
    conn.close()
    return (0 if plan_ready else 2), {"plan_ready": plan_ready, "stats": stats, "plan": str(out)}


def preflight(e_base: Path, e_delta: Path, d_sqlite: Path) -> dict:
    code, rows = validate_inputs(e_base, e_delta, d_sqlite)
    unc = r"\\192.168.100.2\E_DRIVE\BLACKBOX"
    unc_ok = False
    unc_error = ""
    try:
        unc_ok = Path(unc).exists()
        if not unc_ok:
            unc_error = "PATH_NOT_FOUND"
    except OSError as exc:
        unc_error = str(exc)
    report = {
        "hostname": socket.gethostname(),
        "hostname_ok": socket.gethostname().upper() == "ZHANGWEI",
        "input_bindings_ok": code == 0,
        "bindings": rows,
        "dest_historical_serial": HISTORICAL_DEST_SERIAL,
        "historical_serial_is_post_format_auth": False,
        "format_done": False,
        "copy_authorized": False,
        "disk_unique_id_expected_hint": DISK_UNIQUE_HINT,
        "source_unc": unc,
        "source_unc_readable": unc_ok,
        "SOURCE_LIVE_PREFLIGHT_PENDING": not unc_ok,
        "source_unc_error": unc_error,
        "existing_e_sample_allowed": True,
    }
    return report


def copy_entry_refused(copy_authorized: bool, format_done: bool) -> int:
    """This task never performs copy, even if the flag is passed on the CLI."""
    print(
        "COPY_REFUSED"
        f" copy_authorized={str(copy_authorized).lower()}"
        f" format_done={str(format_done).lower()}"
        " task_allows_copy=false"
        " historical_serial_is_not_authorization=true"
    )
    return 3
