# -*- coding: utf-8 -*-
"""Copy a sqlite state with the backup API. Refuses to open the real full_1400.sqlite."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

REAL_STATE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\state\full_1400.sqlite").resolve()


def _fingerprint(path: Path) -> str:
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT kind, phase, dest_path, logical_size, file_id, sha256 FROM stage ORDER BY kind, dest_path"
        ).fetchall()
        digest = hashlib.sha256()
        for row in rows:
            digest.update(repr(row).encode("utf-8"))
        counts = conn.execute("SELECT kind, phase, COUNT(*) FROM stage GROUP BY kind, phase ORDER BY 1, 2").fetchall()
        return digest.hexdigest(), counts, len(rows)
    finally:
        conn.close()


def migrate_copy(source: Path, dest: Path, new_run_id: str, new_code_digest: str) -> dict:
    source = source.resolve()
    dest = dest.resolve()
    if source == REAL_STATE or dest == REAL_STATE:
        raise RuntimeError("REFUSING_REAL_STATE")
    if dest.exists():
        raise RuntimeError("DEST_EXISTS")
    src = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(dest.as_posix())
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    before_fp, before_counts, before_n = _fingerprint(source)
    conn = sqlite3.connect(dest.as_posix())
    try:
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE run_bind SET run_id=?, code_digest=? WHERE run_id IS NOT NULL",
            (new_run_id, new_code_digest),
        )
        conn.commit()
    finally:
        conn.close()
    after_fp, after_counts, after_n = _fingerprint(dest)
    original_fp, _, _ = _fingerprint(source)
    if before_n != after_n or before_counts != after_counts or before_fp != after_fp:
        raise RuntimeError("STAGE_MISMATCH")
    if original_fp != before_fp:
        raise RuntimeError("ORIGINAL_CHANGED")
    return {"rows": after_n, "fingerprint": after_fp, "counts": after_counts}
