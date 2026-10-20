# -*- coding: utf-8 -*-
"""Full-plan acceptance. Expected rows come from the bound plan, not a caller list."""
from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import r9_plan_reader as reader


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _open_disk() -> tuple[sqlite3.Connection, str]:
    handle, name = tempfile.mkstemp(prefix="r9acc_", suffix=".sqlite")
    os.close(handle)
    conn = sqlite3.connect(name)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    return conn, name


def full_acceptance(plan: Path, state_path: Path, backend, run: dict | None) -> dict:
    reasons = []
    plan_conn = reader.connect(plan)
    state = None
    reverify = isinstance(run, dict) and run.get("readonly_reverify") is True
    if reverify:
        state = sqlite3.connect(f"file:{Path(state_path).resolve().as_posix()}?mode=ro", uri=True)
    else:
        state = sqlite3.connect(state_path)
    mem, disk_name = _open_disk()
    try:
        mem.executescript(
            """
            CREATE TABLE expected(path TEXT PRIMARY KEY, object_type TEXT, entity_key TEXT, target TEXT, path_count INTEGER);
            CREATE TABLE observed(
                path TEXT PRIMARY KEY, object_type TEXT, file_id TEXT, volume_serial TEXT,
                sha256 TEXT, target TEXT, alloc INTEGER, logical_size INTEGER, reparse_tag INTEGER
            );
            CREATE TABLE queue(id INTEGER PRIMARY KEY, path TEXT);
            CREATE TABLE plan_entity(entity_key TEXT PRIMARY KEY, dest_path TEXT, path_count INTEGER, logical_size INTEGER);
            """
        )
        required = ("run_id", "plan_digest", "inputs_digest", "code_digest", "dest_volume", "dest_root")
        if not isinstance(run, dict) or any(_blank(run.get(key)) for key in required):
            reasons.append("RUN_BINDING_MISSING")
            dest_volume = None
        else:
            dest_volume = str(run["dest_volume"])
            try:
                computed = reader.plan_digest(plan_conn)
            except RuntimeError as exc:
                computed = None
                if "PLAN_NOT_FROZEN" in str(exc):
                    reasons.append("PLAN_NOT_FROZEN")
                else:
                    raise
            if computed is None or run.get("plan_digest") != computed:
                if "PLAN_NOT_FROZEN" not in reasons:
                    reasons.append("PLAN_DIGEST_MISMATCH")
            if run.get("inputs_digest") != computed:
                reasons.append("INPUT_DIGEST_MISMATCH")
            import r9_source_contract as source_contract
            if isinstance(run, dict) and run.get("readonly_reverify") is True:
                if run.get("code_digest") != run.get("copy_code_digest"):
                    reasons.append("COPY_CODE_BINDING")
            elif run.get("code_digest") != source_contract.code_digest():
                reasons.append("CODE_DIGEST_MISMATCH")
            row = state.execute(
                "SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind"
            ).fetchone()
            current = tuple(run.get(key) for key in required)
            if row is None or tuple(row) != current:
                reasons.append("RUN_BINDING_MISMATCH")
        for entity in reader.read_executable(plan_conn):
            if entity.get("orphan"):
                reasons.append("PLAN_ORPHAN_ENTITY")
                continue
            paths = [entity["dest_path"], *entity.get("extra_dest_paths", ())]
            if len(paths) != int(entity.get("path_count") or 0):
                reasons.append("PATH_COUNT")
            mem.execute(
                "INSERT INTO plan_entity(entity_key, dest_path, path_count, logical_size) VALUES (?,?,?,?)",
                (entity["entity_key"], entity["dest_path"], entity.get("path_count"), entity.get("logical_size")),
            )
            for dest in paths:
                existing = mem.execute("SELECT entity_key FROM expected WHERE path=?", (dest,)).fetchone()
                if existing:
                    reasons.append("DUPLICATE_DEST")
                    continue
                mem.execute(
                    "INSERT INTO expected(path, object_type, entity_key, target, path_count) VALUES (?,?,?,?,?)",
                    (dest, "file", entity["entity_key"], None, entity.get("path_count")),
                )
        directory_paths = [directory["dest_path"] for directory in reader.iter_directories(plan_conn)]
        declared_roots = []
        if isinstance(run, dict):
            declared_roots = [str(item) for item in (run.get("acceptance_roots") or ())]
        for root in (r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES"):
            if any(item.casefold() == root.casefold() for item in declared_roots):
                directory_paths.append(root)
        seen_dirs = set()
        for dest_path in directory_paths:
            key = dest_path.casefold()
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            existing = mem.execute("SELECT path FROM expected WHERE path=?", (dest_path,)).fetchone()
            if existing:
                reasons.append("DUPLICATE_DEST")
                continue
            mem.execute(
                "INSERT INTO expected(path, object_type, entity_key, target, path_count) VALUES (?,?,?,?,?)",
                (dest_path, "directory", None, None, None),
            )
        link_count = 0
        for link in reader.iter_links(plan_conn):
            link_count += 1
            if link.get("blocked") or not link.get("kind"):
                reasons.append(link.get("reason") or "LINK_TYPE_DEFICIT")
                continue
            existing = mem.execute("SELECT path FROM expected WHERE path=?", (link["link_path"],)).fetchone()
            if existing:
                reasons.append("DUPLICATE_DEST")
                continue
            mem.execute(
                "INSERT INTO expected(path, object_type, entity_key, target, path_count) VALUES (?,?,?,?,?)",
                (link["link_path"], link["kind"], None, link["target"], None),
            )
        orphan_count = plan_conn.execute(
            """
            SELECT COUNT(*) FROM entities e
            WHERE NOT EXISTS (
                SELECT 1 FROM paths p
                WHERE p.is_dir=0 AND p.is_reparse=0
                  AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
            )
            """
        ).fetchone()[0]
        if orphan_count:
            reasons.append("PLAN_ORPHAN_ENTITY")
        path_count_bad = plan_conn.execute(
            """
            SELECT COUNT(*) FROM entities e
            WHERE e.path_count != (
                SELECT COUNT(*) FROM paths p
                WHERE p.is_dir=0 AND p.is_reparse=0 AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
            )
            """
        ).fetchone()[0]
        if path_count_bad:
            reasons.append("PATH_COUNT")
        expected_entities = plan_conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        if expected_entities == 0:
            reasons.append("EMPTY_PLAN")
        mem.executescript(
            """
            CREATE INDEX ix_expected_entity ON expected(entity_key);
            CREATE INDEX ix_observed_identity ON observed(file_id, volume_serial);
            """
        )
        if isinstance(run, dict) and run.get("acceptance_roots"):
            accept_roots = tuple(str(item) for item in run["acceptance_roots"])
        else:
            accept_roots = (r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES")
        accept_root_set = set(accept_roots)
        for root in accept_roots:
            mem.execute("INSERT INTO queue(path) VALUES (?)", (root,))
        while True:
            item = mem.execute("SELECT id, path FROM queue ORDER BY id LIMIT 1").fetchone()
            if item is None:
                break
            mem.execute("DELETE FROM queue WHERE id=?", (item[0],))
            current = item[1]
            observed = backend.observe_destination(current) if current in accept_root_set else None
            children = []
            if observed and observed.get("status") == "PRESENT":
                children.append({"path": current, **observed})
            if observed is None or observed.get("object_type") == "directory" or observed.get("status") != "PRESENT":
                children.extend(backend.list_nofollow(current))
            for child in children:
                enumerated = child["path"]
                if mem.execute("SELECT 1 FROM observed WHERE path=?", (enumerated,)).fetchone():
                    continue
                meta = backend.observe_destination(enumerated)
                if not isinstance(meta, dict) or meta.get("status") == "ERROR":
                    reasons.append("OBSERVE_ERROR")
                    continue
                if meta.get("status") != "PRESENT":
                    reasons.append("OBSERVE_ERROR")
                    continue
                mem.execute(
                    """
                    INSERT INTO observed(path, object_type, file_id, volume_serial, sha256, target, alloc, logical_size, reparse_tag)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        enumerated,
                        meta.get("object_type"),
                        None if meta.get("file_id") is None else str(meta.get("file_id")),
                        None if meta.get("volume_serial") is None else str(meta.get("volume_serial")),
                        None,
                        meta.get("reparse_target"),
                        meta.get("allocation_size"),
                        meta.get("logical_size"),
                        meta.get("reparse_tag"),
                    ),
                )
                if meta.get("object_type") == "directory":
                    mem.execute("INSERT INTO queue(path) VALUES (?)", (enumerated,))
        hash_calls_before = int(getattr(backend.sc, "hash_calls", 0))
        for path, file_id, volume in mem.execute(
            """
            SELECT MIN(path), file_id, volume_serial FROM observed
            WHERE object_type='file' AND file_id IS NOT NULL AND file_id!='' AND volume_serial IS NOT NULL AND volume_serial!=''
            GROUP BY file_id, volume_serial
            """
        ):
            digest = backend.content_sha(path)
            mem.execute(
                "UPDATE observed SET sha256=? WHERE file_id=? AND volume_serial=?",
                (digest, file_id, volume),
            )
        hash_calls = int(getattr(backend.sc, "hash_calls", 0)) - hash_calls_before
        missing_field = mem.execute(
            """
            SELECT COUNT(*) FROM expected e
            JOIN observed o ON o.path=e.path
            WHERE o.object_type IS NULL OR o.object_type=''
               OR (e.object_type='file' AND (
                    o.file_id IS NULL OR o.file_id='' OR o.volume_serial IS NULL OR o.volume_serial=''
                    OR o.sha256 IS NULL OR o.sha256='' OR o.alloc IS NULL OR o.logical_size IS NULL
                    OR o.object_type!='file'))
               OR (e.object_type='directory' AND (
                    o.object_type!='directory'
                    OR o.file_id IS NULL OR o.file_id=''
                    OR o.volume_serial IS NULL OR o.volume_serial=''))
               OR (e.object_type IN ('junction','symlink') AND (
                    o.object_type IS NULL OR o.object_type!=e.object_type
                    OR o.target IS NULL OR o.target=''
                    OR o.file_id IS NULL OR o.file_id=''
                    OR o.volume_serial IS NULL OR o.volume_serial=''
                    OR o.reparse_tag IS NULL))
            """
        ).fetchone()[0]
        if missing_field:
            reasons.append("MISSING_FIELD")
        if dest_volume is not None:
            bad_volume = mem.execute(
                """
                SELECT COUNT(*) FROM expected e
                JOIN observed o ON o.path=e.path
                WHERE o.volume_serial IS NULL OR o.volume_serial='' OR o.volume_serial!=?
                """,
                (dest_volume,),
            ).fetchone()[0]
            if bad_volume:
                reasons.append("DEST_VOLUME")
        missing = mem.execute("SELECT COUNT(*) FROM expected e LEFT JOIN observed o ON o.path=e.path WHERE o.path IS NULL").fetchone()[0]
        extra = mem.execute("SELECT COUNT(*) FROM observed o LEFT JOIN expected e ON e.path=o.path WHERE e.path IS NULL").fetchone()[0]
        if missing:
            reasons.append("MISSING_OBJECT")
        if extra:
            reasons.append("EXTRA_OBJECT")
        bad_target = mem.execute(
            """
            SELECT COUNT(*) FROM expected e
            JOIN observed o ON o.path=e.path
            WHERE e.target IS NOT NULL AND (o.target IS NULL OR o.target!=e.target)
            """
        ).fetchone()[0]
        if bad_target:
            reasons.append("BAD_LINK_TARGET")
        dangling = 0
        for link in reader.iter_links(plan_conn):
            if link.get("blocked") or not link.get("kind"):
                continue
            target = link["target"]
            expected = mem.execute("SELECT object_type FROM expected WHERE path=?", (target,)).fetchone()
            observed = mem.execute("SELECT object_type FROM observed WHERE path=?", (target,)).fetchone()
            if observed is None:
                seen = backend.observe_destination(target)
                if isinstance(seen, dict) and seen.get("status") == "PRESENT":
                    observed = (seen.get("object_type"),)
            if expected is None or observed is None or expected[0] != observed[0]:
                dangling += 1
            tag_row = mem.execute("SELECT reparse_tag FROM observed WHERE path=?", (link["link_path"],)).fetchone()
            if link.get("reparse_tag") not in (None, "") and tag_row and tag_row[0] not in (None, "") and int(tag_row[0]) != int(link["reparse_tag"]):
                reasons.append("BAD_REPARSE_TAG")
        if dangling:
            reasons.append("DANGLING_TARGET")
        merged = mem.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT o.file_id, o.volume_serial
                FROM expected e JOIN observed o ON o.path=e.path
                WHERE e.object_type='file' AND o.file_id IS NOT NULL AND o.file_id!=''
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
                FROM expected e JOIN observed o ON o.path=e.path
                WHERE e.object_type='file' AND o.file_id IS NOT NULL AND o.file_id!=''
                GROUP BY e.entity_key
                HAVING COUNT(DISTINCT o.file_id || '|' || COALESCE(o.volume_serial,'')) > 1
            )
            """
        ).fetchone()[0]
        if split:
            reasons.append("ALIAS_SPLIT")
        state.close()
        state = None
        mem.execute("ATTACH DATABASE ? AS st", (str(state_path),))
        if mem.execute(
            """
            SELECT COUNT(*) FROM plan_entity p
            WHERE NOT EXISTS (
                SELECT 1 FROM st.stage s
                WHERE s.item_key = 'entity:' || p.entity_key
                  AND s.kind='entity'
                  AND s.phase='DONE'
                  AND s.parent_key=p.entity_key
            )
            """
        ).fetchone()[0]:
            reasons.append("MISSING_ENTITY")
        if mem.execute(
            """
            SELECT COUNT(*) FROM st.stage s
            WHERE s.kind='entity' AND s.phase='DONE'
              AND NOT EXISTS (SELECT 1 FROM plan_entity p WHERE p.entity_key=s.parent_key)
            """
        ).fetchone()[0]:
            reasons.append("EXTRA_DONE")
        stage_rows = mem.execute(
            """
            SELECT s.parent_key, s.dest_path, s.sha256, s.file_id, s.volume_serial, s.logical_size
            FROM st.stage s
            JOIN plan_entity p ON p.entity_key=s.parent_key
            WHERE s.kind='entity' AND s.phase='DONE'
            """
        )
        identity_bad = 0
        checked = 0
        for parent, dest, digest, file_id, volume, size in stage_rows:
            checked += 1
            observed = mem.execute(
                "SELECT sha256, file_id, volume_serial, logical_size, object_type FROM observed WHERE path=?",
                (dest,),
            ).fetchone()
            if observed is None or any(_blank(part) for part in observed[:4]) or observed[4] != "file":
                identity_bad += 1
                continue
            if observed[0] != digest or observed[1] != file_id or observed[2] != volume or observed[3] != size:
                identity_bad += 1
            if dest_volume is not None and observed[2] != dest_volume:
                identity_bad += 1
        if identity_bad:
            reasons.append("IDENTITY_MISMATCH")
        content = mem.execute(
            """
            SELECT COALESCE(SUM(logical_size),0) FROM (
                SELECT MAX(logical_size) AS logical_size FROM observed
                WHERE object_type='file' AND file_id IS NOT NULL AND file_id!=''
                GROUP BY file_id, volume_serial
            )
            """
        ).fetchone()[0]
        allocation = mem.execute(
            """
            SELECT COALESCE(SUM(alloc),0) FROM (
                SELECT MAX(alloc) AS alloc FROM observed
                WHERE object_type='file' AND file_id IS NOT NULL AND file_id!='' AND alloc IS NOT NULL
                GROUP BY file_id, volume_serial
            )
            """
        ).fetchone()[0]
        verifier_digest = None
        copy_binding = None
        if reverify:
            import r9_source_contract as source_contract
            verifier_digest = source_contract.code_digest()
            copy_binding = run.get("copy_code_digest") if isinstance(run, dict) else None
        unique = []
        seen = set()
        for reason in reasons:
            if reason not in seen:
                seen.add(reason)
                unique.append(reason)
        done_entities = checked
        return {
            "full_acceptance": not unique,
            "reasons": unique[:20],
            "expected_entities": expected_entities,
            "checked_entities": done_entities,
            "expected_dirs": mem.execute("SELECT COUNT(*) FROM expected WHERE object_type='directory'").fetchone()[0],
            "expected_links": link_count,
            "expected_file_paths": mem.execute("SELECT COUNT(*) FROM expected WHERE object_type='file'").fetchone()[0],
            "missing": missing,
            "extra": extra,
            "content_bytes": int(content or 0),
            "allocation_bytes": int(allocation or 0),
            "allocation_equals_content_not_required": True,
            "content_hash_calls": hash_calls,
            "acceptance_store": "disk-sqlite",
            "verifier_code_digest": verifier_digest,
            "copy_code_digest": copy_binding,
            "readonly_reverify": reverify,
        }
    finally:
        mem.close()
        if state is not None:
            state.close()
        plan_conn.close()
        try:
            os.remove(disk_name)
        except OSError:
            pass
