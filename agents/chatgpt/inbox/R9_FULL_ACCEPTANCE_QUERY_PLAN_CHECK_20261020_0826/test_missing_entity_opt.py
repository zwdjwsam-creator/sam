# -*- coding: utf-8 -*-
"""Synthetic semantic and plan/timing tests for MISSING_ENTITY lookup.

Does not touch production state or the running executor modules.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

OUT = Path(r"C:\LAN_SHARE_REPORT\R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826")

OLD = """
SELECT COUNT(*) FROM plan_entity p
WHERE NOT EXISTS (
    SELECT 1 FROM stage s WHERE s.kind='entity' AND s.phase='DONE' AND s.parent_key=p.entity_key
)
"""

NEW = """
SELECT COUNT(*) FROM plan_entity p
WHERE NOT EXISTS (
    SELECT 1 FROM stage s
    WHERE s.item_key = 'entity:' || p.entity_key
      AND s.kind='entity' AND s.phase='DONE' AND s.parent_key=p.entity_key
)
"""


def build(n_plan: int, n_stage: int, mode: str) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.executescript(
        """
        CREATE TABLE plan_entity(entity_key TEXT PRIMARY KEY, dest_path TEXT, path_count INTEGER, logical_size INTEGER);
        CREATE TABLE stage(
            item_key TEXT PRIMARY KEY, kind TEXT, phase TEXT, dest_path TEXT, sha256 TEXT,
            file_id TEXT, volume_serial TEXT, object_type TEXT, link_target TEXT,
            logical_size INTEGER, parent_key TEXT
        );
        """
    )
    for i in range(n_plan):
        key = f"vol|{i}"
        db.execute("INSERT INTO plan_entity VALUES (?,?,?,?)", (key, f"C:\\\\d\\\\{i}", 1, 1))
        if mode == "complete":
            db.execute(
                "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"entity:{key}", "entity", "DONE", f"C:\\\\d\\\\{i}", "a" * 64, str(i), "1", "file", None, 1, key),
            )
        elif mode == "missing_one" and i != 0:
            db.execute(
                "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"entity:{key}", "entity", "DONE", f"C:\\\\d\\\\{i}", "a" * 64, str(i), "1", "file", None, 1, key),
            )
        elif mode == "wrong_phase" and i == 0:
            db.execute(
                "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"entity:{key}", "entity", "INTENT", f"C:\\\\d\\\\{i}", "a" * 64, str(i), "1", "file", None, 1, key),
            )
            for j in range(1, n_plan):
                k2 = f"vol|{j}"
                db.execute(
                    "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (f"entity:{k2}", "entity", "DONE", f"C:\\\\d\\\\{j}", "a" * 64, str(j), "1", "file", None, 1, k2),
                )
            break
        elif mode == "wrong_parent":
            # item_key looks normal but parent_key does not match entity_key
            bad_parent = f"other|{i}"
            db.execute(
                "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"entity:{key}", "entity", "DONE", f"C:\\\\d\\\\{i}", "a" * 64, str(i), "1", "file", None, 1, bad_parent),
            )
        elif mode == "malformed_item_key":
            # parent_key matches but item_key is not entity:entity_key
            db.execute(
                "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"alias:{key}", "entity", "DONE", f"C:\\\\d\\\\{i}", "a" * 64, str(i), "1", "file", None, 1, key),
            )
        elif mode == "extra_done":
            db.execute(
                "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"entity:{key}", "entity", "DONE", f"C:\\\\d\\\\{i}", "a" * 64, str(i), "1", "file", None, 1, key),
            )
    if mode == "extra_done":
        db.execute(
            "INSERT INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("entity:orphan|9", "entity", "DONE", "C:\\\\o", "b" * 64, "9", "1", "file", None, 1, "orphan|9"),
        )
    # pad stage with unrelated rows for scale tests
    for j in range(n_stage):
        db.execute(
            "INSERT OR IGNORE INTO stage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (f"alias:pad|{j}", "alias", "DONE", f"C:\\\\a\\\\{j}", None, None, None, "file", None, 0, f"vol|{j % max(n_plan,1)}"),
        )
    db.commit()
    return db


def missing_count(db: sqlite3.Connection, sql: str) -> int:
    return int(db.execute(sql).fetchone()[0])


def plan_text(db: sqlite3.Connection, sql: str) -> str:
    return " | ".join(str(r[-1]) if len(r) > 3 else " ".join(str(x) for x in r) for r in db.execute("EXPLAIN QUERY PLAN " + sql))


def main() -> None:
    results = []
    # semantic cases
    cases = [
        ("complete", 20, 0, 0, 0),
        ("missing_one", 20, 0, 1, 1),
        ("wrong_phase", 20, 0, 1, 1),
        ("wrong_parent", 20, 0, 20, 20),
        ("malformed_item_key", 20, 0, 0, 20),  # old parent_key-only would accept; new must reject
        ("extra_done", 20, 0, 0, 0),  # MISSING_ENTITY count only; extra is separate check
    ]
    for mode, n_plan, n_stage, expect_old, expect_new in cases:
        db = build(n_plan, n_stage, mode)
        old_c = missing_count(db, OLD)
        new_c = missing_count(db, NEW)
        ok = old_c == expect_old and new_c == expect_new
        # malformed: new must be stricter (reject) than old if old accepted
        if mode == "malformed_item_key":
            ok = old_c == 0 and new_c == 20
        results.append({
            "case": mode,
            "old_count": old_c,
            "new_count": new_c,
            "expect_old": expect_old,
            "expect_new": expect_new,
            "ok": ok,
            "note": "malformed_item_key: new refuses parent_key-only DONE without matching item_key" if mode == "malformed_item_key" else None,
        })
        db.close()

    # scale plans/timings
    scales = []
    for n_plan, n_stage in ((100, 1000), (1000, 10000), (5000, 50000)):
        db = build(n_plan, n_stage, "complete")
        old_plan = plan_text(db, OLD)
        new_plan = plan_text(db, NEW)
        t0 = time.perf_counter()
        old_c = missing_count(db, OLD)
        t1 = time.perf_counter()
        new_c = missing_count(db, NEW)
        t2 = time.perf_counter()
        scales.append({
            "n_plan": n_plan,
            "n_stage": n_stage + n_plan,
            "old_count": old_c,
            "new_count": new_c,
            "old_seconds": t1 - t0,
            "new_seconds": t2 - t1,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "old_has_scan_s": "SCAN s" in old_plan or "SCAN TABLE stage" in old_plan,
            "new_has_search": "SEARCH" in new_plan and "item_key" in new_plan,
            "counts_match": old_c == new_c == 0,
        })
        db.close()

    payload = {
        "semantic": results,
        "scale": scales,
        "semantic_ok": all(r["ok"] for r in results),
        "scale_ok": all(s["counts_match"] and s["new_has_search"] for s in scales),
    }
    (OUT / "SYNTHETIC_TEST.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SEMANTIC_OK" if payload["semantic_ok"] else "SEMANTIC_FAIL", "SCALE_OK" if payload["scale_ok"] else "SCALE_FAIL")
    for s in scales:
        print(s["n_plan"], "old", round(s["old_seconds"], 4), "new", round(s["new_seconds"], 4), "scan", s["old_has_scan_s"], "search", s["new_has_search"])


if __name__ == "__main__":
    main()
