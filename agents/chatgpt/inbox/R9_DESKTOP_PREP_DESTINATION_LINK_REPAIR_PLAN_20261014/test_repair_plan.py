# -*- coding: utf-8 -*-
import sqlite3
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_DESTINATION_LINK_REPAIR_PLAN_20261014")
import r9_plan_reader as reader
import r9_runner
import r9_winio as winio
from build_candidate import BROKEN, GOOD, role


class RepairDecisionTests(unittest.TestCase):
    def test_historical_long_chain_shortens_and_dynamic_head_stays(self):
        action, _basis = role(r"E:\BLACKBOX\releases\R1_ASOF_20260814\data", 12)
        self.assertEqual(action, "HISTORICAL_SHORTEN")
        action, _basis = role(r"E:\BLACKBOX\releases\CURRENT", 12)
        self.assertEqual(action, "DYNAMIC_KEEP")
        action, _basis = role(r"E:\BLACKBOX\releases\R1_ASOF_20260814\data", 1)
        self.assertEqual(action, "ALREADY_DIRECT")
        self.assertLess(GOOD, BROKEN)

    def test_reader_keeps_the_good_file_as_source_representative(self):
        with tempfile.TemporaryDirectory() as raw:
            plan = Path(raw) / "plan.sqlite"
            db = sqlite3.connect(plan)
            db.executescript(
                """
                CREATE TABLE entities(
                  volume_serial TEXT, file_id TEXT, path_count INTEGER, min_size INTEGER,
                  max_size INTEGER, max_nlinks INTEGER, d_paths INTEGER, delta_paths INTEGER
                );
                CREATE TABLE paths(
                  path TEXT PRIMARY KEY, is_dir INTEGER, is_reparse INTEGER, logical_size INTEGER,
                  alloc_size INTEGER, volume_serial TEXT, file_id TEXT, nlinks INTEGER,
                  reparse_target TEXT, source TEXT
                );
                """
            )
            db.execute("INSERT INTO entities VALUES (?,?,?,?,?,?,0,0)", ("2387166462", "77", 2, 9, 9, 2))
            for path, source in ((GOOD, "plan"), (BROKEN, "dest_repair_alias")):
                db.execute(
                    "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (path, 0, 0, 9, 4096, "2387166462", "77", 2, None, source),
                )
            db.commit()
            db.close()
            conn = reader.connect(plan)
            try:
                entities = [item for item in reader.read_executable(conn) if item["file_id"] == "77"]
            finally:
                conn.close()
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]["inventory_path"], GOOD)
        self.assertIn(BROKEN, entities[0]["extra_dest_paths"])
        self.assertNotEqual(entities[0]["inventory_path"], BROKEN)

    def test_virtual_copy_aliases_the_existing_file_once(self):
        payload = b"pointer-bytes"
        source = r"\\192.168.100.2\E_DRIVE\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ADJFACTOR_PIT_ASOF_20260814_20260816_034243\CURRENT_POINTER_COPY.json"
        sc = winio.VirtualSyscalls(dest_volume="DEST")
        sc.files[source] = payload
        sc.identities[source] = {"file_id": "77", "volume_serial": "2387166462", "mtime": "T1", "object_type": "file"}
        entity = {
            "entity_key": "2387166462|77",
            "source_path": source,
            "dest_path": GOOD,
            "file_id": "77",
            "volume_serial": "2387166462",
            "logical_size": len(payload),
            "mtime": "T1",
            "mtime_status": "FROM_PLAN",
            "extra_dest_paths": [BROKEN],
        }
        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "state.sqlite"
            contract = {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}, "directories": [], "links": [], "accept": False}
            first = r9_runner.production_run([entity], backend, contract, state)
            writes = sc.write_calls
            second = r9_runner.production_run([entity], backend, contract, state)
        self.assertEqual(first["copied_count"], 1)
        self.assertEqual(first["linked_count"], 1)
        self.assertEqual(bytes(sc.files[GOOD]), payload)
        self.assertEqual(bytes(sc.files[BROKEN]), payload)
        self.assertEqual(second["copied_count"], 0)
        self.assertEqual(second["linked_count"], 0)
        self.assertEqual(sc.write_calls, writes)


if __name__ == "__main__":
    unittest.main()
