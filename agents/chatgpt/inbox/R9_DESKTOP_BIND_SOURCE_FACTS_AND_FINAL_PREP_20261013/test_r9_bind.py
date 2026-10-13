# -*- coding: utf-8 -*-
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_acceptance
import r9_plan_reader as reader
import r9_source_contract as source
import test_r9_close as close


class BindTests(unittest.TestCase):
    def test_same_count_content_change_rejects_old_binding(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            close._plan(plan)
            db = sqlite3.connect(plan)
            entities, contract = close._contract(plan, db)
            before = contract["run"]["plan_digest"]
            db.close()
            sc, backend = close._backend()
            state = td / "state.sqlite"
            import r9_runner as runner
            runner.production_run(iter(entities), backend, contract, state)
            db = sqlite3.connect(plan)
            db.execute("UPDATE entities SET mtime='changed-expected-time'")
            db.commit()
            after = reader.plan_digest(db)
            db.close()
            self.assertNotEqual(before, after)
            report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
            self.assertFalse(report["full_acceptance"])
            self.assertIn("PLAN_DIGEST_MISMATCH", report["reasons"])

    def test_bound_d_unc_and_overlay_rules(self):
        shares = source.share_contract(json.loads(Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\input_v2\SOURCE_SHARE_FACTS.json").read_bytes()))
        mapped = reader.map_inventory_path(r"D:\CURSOR_TASK_ARCHIVE\engine.bin", shares)
        self.assertEqual(mapped["source_path"], r"\\192.168.100.2\D_DRIVE\CURSOR_TASK_ARCHIVE\engine.bin")
        self.assertEqual(mapped["source_share"], "D_DRIVE")
        self.assertTrue(mapped["dest_path"].startswith("E:\\BLACKBOX_ENGINES\\"))
        unbound = reader.map_inventory_path(r"D:\CURSOR_TASK_ARCHIVE\engine.bin")
        self.assertEqual(unbound["source_share"], "D_SHARE_NOT_IN_CONTRACT")
        payload = json.loads(Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\input_v2\D_REPARSE_TYPE_OVERLAY.json").read_bytes())
        rows = source.validate_overlay(payload)
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(row["reparse_tag"] == 0xA0000003 for row in rows))
        broken = json.loads(json.dumps(payload))
        broken["records"][0]["map_id"] = broken["records"][1]["map_id"]
        with self.assertRaises(RuntimeError):
            source.validate_overlay(broken)
        missing = json.loads(json.dumps(payload))
        missing["records"][0]["reparse_tag"] = 1
        with self.assertRaises(RuntimeError):
            source.validate_overlay(missing)

    def test_orphan_query_uses_entity_index(self):
        with tempfile.TemporaryDirectory() as raw:
            db = sqlite3.connect(Path(raw) / "plan.sqlite")
            db.execute("CREATE TABLE entities(volume_serial TEXT, file_id TEXT, path_count INTEGER)")
            db.execute("CREATE TABLE paths(path TEXT, is_dir INTEGER, is_reparse INTEGER, volume_serial TEXT, file_id TEXT)")
            db.execute("CREATE INDEX ix_entity ON paths(is_dir, is_reparse, volume_serial, file_id)")
            sql = """
                SELECT COUNT(*) FROM entities e
                WHERE NOT EXISTS (
                    SELECT 1 FROM paths p
                    WHERE p.is_dir=0 AND p.is_reparse=0
                      AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
                )
            """
            plan = " ".join(str(part) for row in db.execute("EXPLAIN QUERY PLAN " + sql) for part in row)
            db.close()
            self.assertIn("ix_entity", plan)


if __name__ == "__main__":
    unittest.main()
