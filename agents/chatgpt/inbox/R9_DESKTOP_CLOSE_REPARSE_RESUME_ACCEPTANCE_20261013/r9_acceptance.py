# -*- coding: utf-8 -*-
"""Full-plan acceptance. Expected counts come from the bound plan, not a caller list."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import r9_plan_reader as reader
import r9_state


def _add(mem: sqlite3.Connection, sql: str, row: tuple) -> None:
    mem.execute(sql, row)


def full_acceptance(plan: Path, state_path: Path, backend, run: dict | None) -> dict:
    reasons = []
    plan_conn = reader.connect(plan)
    state = sqlite3.connect(state_path)
    mem = sqlite3.connect(":memory:")
    try:
        mem.execute("CREATE TABLE expected(path TEXT PRIMARY KEY, object_type TEXT, entity_key TEXT, target TEXT)")
        mem.execute(
            "CREATE TABLE observed(path TEXT PRIMARY KEY, object_type TEXT, file_id TEXT, volume_serial TEXT, sha256 TEXT, target TEXT, alloc INTEGER, logical_size INTEGER, entity_key TEXT)"
        )
        if run:
            row = state.execute(
                "SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind"
            ).fetchone()
            current = (run.get("run_id"), run.get("plan_digest"), run.get("inputs_digest"), run.get("code_digest"), run.get("dest_volume"), run.get("dest_root"))
            if row is None or tuple(row) != current:
                reasons.append("RUN_BINDING_MISMATCH")
        file_rows = 0
        for entity in reader.read_executable(plan_conn):
            paths = [entity["dest_path"], *entity.get("extra_dest_paths", ())]
            for index, dest in enumerate(paths):
                _add(
                    mem,
                    "INSERT OR REPLACE INTO expected(path, object_type, entity_key, target) VALUES (?,?,?,?)",
                    (dest, "file", entity["entity_key"], None),
                )
                file_rows += 1
        for directory in reader.iter_directories(plan_conn):
            _add(mem, "INSERT OR REPLACE INTO expected(path, object_type, entity_key, target) VALUES (?,?,?,?)", (directory["dest_path"], "directory", None, None))
        link_count = 0
        for link in reader.iter_links(plan_conn):
            link_count += 1
            if link.get("blocked"):
                reasons.append("BAD_LINK_TARGET")
                continue
            _add(
                mem,
                "INSERT OR REPLACE INTO expected(path, object_type, entity_key, target) VALUES (?,?,?,?)",
                (link["link_path"], link["kind"], None, link["target"]),
            )
        expected_entities = plan_conn.execute(
            """
            SELECT COUNT(*) FROM entities e
            WHERE EXISTS (
                SELECT 1 FROM paths p
                WHERE p.is_dir=0 AND p.is_reparse=0 AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
            )
            """
        ).fetchone()[0]
        expected_dirs = mem.execute("SELECT COUNT(*) FROM expected WHERE object_type='directory'").fetchone()[0]
        done_entities = state.execute("SELECT COUNT(*) FROM stage WHERE kind='entity' AND phase='DONE'").fetchone()[0]
        if expected_entities == 0 or done_entities != expected_entities:
            reasons.append("ENTITY_COUNT")
        unfinished = state.execute("SELECT COUNT(*) FROM stage WHERE phase!='DONE'").fetchone()[0]
        if unfinished:
            reasons.append("UNFINISHED")
        roots = [r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES"]
        for root in roots:
            seen_root = backend.observe_destination(root)
            if seen_root.get("status") != "PRESENT":
                continue
            _add(
                mem,
                "INSERT OR REPLACE INTO observed(path, object_type, file_id, volume_serial, sha256, target, alloc, logical_size, entity_key) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    root,
                    seen_root.get("object_type"),
                    seen_root.get("file_id"),
                    seen_root.get("volume_serial"),
                    seen_root.get("sha256"),
                    seen_root.get("reparse_target"),
                    seen_root.get("allocation_size") or 0,
                    seen_root.get("logical_size"),
                    None,
                ),
            )
        stack = list(roots)
        seen = set()
        while stack:
            current = stack.pop()
            for child in backend.list_nofollow(current):
                path = child["path"]
                if path in seen:
                    continue
                seen.add(path)
                _add(
                    mem,
                    "INSERT OR REPLACE INTO observed(path, object_type, file_id, volume_serial, sha256, target, alloc, logical_size, entity_key) VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        path,
                        child.get("object_type"),
                        child.get("file_id"),
                        child.get("volume_serial"),
                        child.get("sha256"),
                        child.get("reparse_target"),
                        child.get("allocation_size") or 0,
                        child.get("logical_size"),
                        None,
                    ),
                )
                if child.get("object_type") == "directory":
                    stack.append(path)
        missing = mem.execute("SELECT COUNT(*) FROM expected e LEFT JOIN observed o ON o.path=e.path WHERE o.path IS NULL").fetchone()[0]
        extra = mem.execute("SELECT COUNT(*) FROM observed o LEFT JOIN expected e ON e.path=o.path WHERE e.path IS NULL").fetchone()[0]
        if missing:
            reasons.append("MISSING_OBJECT")
        if extra:
            reasons.append("EXTRA_OBJECT")
        typed = mem.execute(
            """
            SELECT COUNT(*) FROM expected e
            JOIN observed o ON o.path=e.path
            WHERE o.object_type!=e.object_type
            """
        ).fetchone()[0]
        if typed:
            reasons.append("TYPE_MISMATCH")
        bad_target = mem.execute(
            """
            SELECT COUNT(*) FROM expected e
            JOIN observed o ON o.path=e.path
            WHERE e.target IS NOT NULL AND o.target!=e.target
            """
        ).fetchone()[0]
        if bad_target:
            reasons.append("BAD_LINK_TARGET")
        merged = mem.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT o.file_id, o.volume_serial
                FROM expected e
                JOIN observed o ON o.path=e.path
                WHERE e.object_type='file' AND o.file_id IS NOT NULL
                GROUP BY o.file_id, o.volume_serial
                HAVING COUNT(DISTINCT e.entity_key) > 1
            )
            """
        ).fetchone()[0]
        if merged:
            reasons.append("ENTITY_MERGE")
        split = mem.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT e.entity_key
                FROM expected e
                JOIN observed o ON o.path=e.path
                WHERE e.object_type='file'
                GROUP BY e.entity_key
                HAVING COUNT(DISTINCT o.file_id || '|' || o.volume_serial) > 1
            )
            """
        ).fetchone()[0]
        if split:
            reasons.append("ALIAS_SPLIT")
        hash_bad = 0
        for dest, digest in state.execute(
            "SELECT dest_path, sha256 FROM stage WHERE kind='entity' AND phase='DONE'"
        ):
            observed = mem.execute("SELECT sha256 FROM observed WHERE path=?", (dest,)).fetchone()
            if observed is None or observed[0] != digest:
                hash_bad += 1
        if hash_bad:
            reasons.append("HASH_MISMATCH")
        content = mem.execute(
            """
            SELECT COALESCE(SUM(logical_size), 0) FROM (
                SELECT MAX(logical_size) AS logical_size
                FROM observed WHERE object_type='file' AND file_id IS NOT NULL
                GROUP BY file_id, volume_serial
            )
            """
        ).fetchone()[0]
        allocation = mem.execute(
            """
            SELECT COALESCE(SUM(alloc), 0) FROM (
                SELECT MAX(alloc) AS alloc
                FROM observed WHERE object_type='file' AND file_id IS NOT NULL
                GROUP BY file_id, volume_serial
            )
            """
        ).fetchone()[0]
        full = not reasons
        return {
            "full_acceptance": full,
            "reasons": reasons[:20],
            "expected_entities": expected_entities,
            "checked_entities": done_entities,
            "expected_dirs": expected_dirs,
            "expected_links": link_count,
            "expected_file_paths": file_rows,
            "missing": missing,
            "extra": extra,
            "content_bytes": int(content or 0),
            "allocation_bytes": int(allocation or 0),
            "allocation_equals_content_not_required": True,
        }
    finally:
        mem.close()
        state.close()
        plan_conn.close()
