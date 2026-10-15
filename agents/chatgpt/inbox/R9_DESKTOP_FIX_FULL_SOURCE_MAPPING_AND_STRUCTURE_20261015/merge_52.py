# -*- coding: utf-8 -*-
"""Merge SAM's 52 local metadata rows into a new candidate. Does not touch the 94e6 plan."""
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

SRC = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015\FINAL_CANDIDATE.sqlite")
DEST = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite")
META = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\LOCAL_52_METADATA.json")
PATCH = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015\sam_evidence\SOURCE_PLAN_PATCH.json")
PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
EXPECTED = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    patch = json.loads(PATCH.read_text(encoding="utf-8"))
    expected = {row["path"] for row in patch["added_51_metadata_candidates"]}
    expected.update(row["path"] for row in patch["mcp_and_real_changes"])
    got = {row["path"] for row in meta["rows"]}
    if got != expected or len(got) != 52 or meta["summary"]["ok"] != 52:
        raise SystemExit("PATH_SET")
    if DEST.exists():
        DEST.unlink()
    shutil.copy2(SRC, DEST)
    conn = sqlite3.connect(DEST)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS observed_metadata_52 (
          path TEXT PRIMARY KEY, item_class TEXT, volume_serial TEXT, file_id TEXT,
          size INTEGER, allocation_size INTEGER, mtime_ft TEXT, observed_at TEXT, source_bucket TEXT
        )
        """
    )
    ancestors = set()
    for row in meta["rows"]:
        for item in row.get("ancestor_checks") or []:
            if item.get("exists") and not item.get("is_drive_root"):
                ancestors.add(item["path"])
        current = conn.execute("SELECT is_dir, is_reparse, file_id FROM paths WHERE path=?", (row["path"],)).fetchone()
        is_dir = 1 if row["is_directory"] else 0
        if current is None:
            if is_dir:
                conn.execute(
                    "INSERT INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (row["path"], 1, 0, 0, row["allocation_size"], row["volume_serial"], row["file_id"], row["nlinks"], None, "post_baseline_directory"),
                )
            else:
                conn.execute(
                    "INSERT INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (row["path"], 0, 0, row["size"], row["allocation_size"], row["volume_serial"], row["file_id"], row["nlinks"], None, "post_baseline_file"),
                )
                known = conn.execute(
                    "SELECT path_count, min_size, max_size FROM entities WHERE volume_serial=? AND file_id=?",
                    (row["volume_serial"], row["file_id"]),
                ).fetchone()
                if known is None:
                    conn.execute(
                        "INSERT INTO entities(volume_serial, file_id, path_count, min_size, max_size, max_nlinks, d_paths, delta_paths) VALUES (?,?,?,?,?,?,?,?)",
                        (row["volume_serial"], row["file_id"], 1, row["size"], row["size"], row["nlinks"], 1 if row["path"].startswith("D:\\") else 0, 0),
                    )
                else:
                    conn.execute(
                        "UPDATE entities SET path_count=path_count+1, min_size=MIN(min_size, ?), max_size=MAX(max_size, ?) WHERE volume_serial=? AND file_id=?",
                        (row["size"], row["size"], row["volume_serial"], row["file_id"]),
                    )
        else:
            if int(current[0]) != is_dir:
                conn.close()
                raise SystemExit("TYPE_CONFLICT " + row["path"])
            conn.execute(
                "UPDATE paths SET logical_size=?, alloc_size=?, volume_serial=?, file_id=?, nlinks=? WHERE path=?",
                (0 if is_dir else row["size"], row["allocation_size"], row["volume_serial"], row["file_id"], row["nlinks"], row["path"]),
            )
            if not is_dir:
                conn.execute(
                    "UPDATE entities SET min_size=?, max_size=? WHERE volume_serial=? AND file_id=?",
                    (row["size"], row["size"], row["volume_serial"], row["file_id"]),
                )
        conn.execute(
            "INSERT OR REPLACE INTO observed_metadata_52 VALUES (?,?,?,?,?,?,?,?,?)",
            (row["path"], row["item_class"], row["volume_serial"], row["file_id"], row["size"], row["allocation_size"], row["mtime_ft"], row["observed_at"], row.get("source_bucket")),
        )
    added_ancestors = 0
    for path in sorted(ancestors):
        if path in got:
            continue
        if conn.execute("SELECT 1 FROM paths WHERE path=?", (path,)).fetchone():
            continue
        conn.execute(
            "INSERT INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (path, 1, 0, 0, None, None, None, None, None, "ancestor_exists_identity_not_in_handoff"),
        )
        added_ancestors += 1
    mismatch = conn.execute(
        """
        SELECT COUNT(*) FROM entities e
        WHERE e.path_count != (
          SELECT COUNT(*) FROM paths p
          WHERE p.is_dir=0 AND p.is_reparse=0 AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
        )
        """
    ).fetchone()[0]
    check = conn.execute("PRAGMA quick_check").fetchone()[0]
    conn.commit()
    conn.close()
    if mismatch or check != "ok":
        raise SystemExit(f"MERGE {mismatch} {check}")
    print("ancestors", added_ancestors)
    print("candidate", sha256_file(DEST), DEST.stat().st_size)
    print("plan", sha256_file(PLAN))
    if sha256_file(PLAN) != EXPECTED:
        raise SystemExit("PLAN")


if __name__ == "__main__":
    main()
