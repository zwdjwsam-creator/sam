# -*- coding: utf-8 -*-
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_formal_chain as chain
import r9_source_contract as source_contract


def _write(path: Path, files, dirs, links, reparses=()):
    db = sqlite3.connect(path)
    db.execute(
        """
        CREATE TABLE paths (
          path TEXT PRIMARY KEY, is_dir INTEGER, is_reparse INTEGER, logical_size INTEGER,
          alloc_size INTEGER, volume_serial TEXT, file_id TEXT, nlinks INTEGER,
          reparse_target TEXT, source TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE entities (
          volume_serial TEXT, file_id TEXT, path_count INTEGER, min_size INTEGER, max_size INTEGER,
          max_nlinks INTEGER, d_paths INTEGER, delta_paths INTEGER
        )
        """
    )
    db.execute(
        """
        CREATE TABLE links (
          path TEXT PRIMARY KEY, target TEXT, source TEXT, mapped_dest TEXT, status TEXT,
          map_id INTEGER, original_target TEXT, migrated_link_path TEXT, migrated_target TEXT,
          map_source TEXT, content_files INTEGER, delta_files INTEGER, reparse_tag INTEGER, tag_source TEXT
        )
        """
    )
    for item in dirs:
        db.execute("INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)", (item, 1, 0, 0, 0, "1", "1", 1, None, "t"))
    for item in reparses:
        db.execute("INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)", (item, 1, 1, 0, 0, "1", "9", 1, None, "t"))
    for item, size in files:
        db.execute("INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)", (item, 0, 0, size, 4096, "2387166462", item, 1, None, "t"))
        db.execute("INSERT INTO entities VALUES (?,?,?,?,?,?,0,0)", ("2387166462", item, 1, size, size, 1))
    for link, target in links:
        db.execute(
            "INSERT INTO links(path, target, migrated_target) VALUES (?,?,?)",
            (link, target, target),
        )
    db.commit()
    db.close()


def _contract(plan: Path):
    digest = chain.sha256_file(plan)
    db = sqlite3.connect(plan)
    total = int(db.execute("SELECT COALESCE(SUM(min_size),0) FROM entities").fetchone()[0])
    db.close()
    return {
        "scope": "FULL",
        "plan_sha": digest,
        "max_unique_bytes": total,
        "subset_unique_bytes": total,
        "run": {
            "plan_digest": digest,
            "inputs_digest": digest,
            "code_digest": source_contract.code_digest(),
        },
    }


class FullClosure(unittest.TestCase):
    def test_missing_terminal_is_not_ok(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            _write(plan, [(r"E:\BLACKBOX\a.txt", 4)], [], [(r"E:\BLACKBOX\link", r"E:\BLACKBOX\NONEXISTENT")])
            audit = chain.inspect_plan(plan, _contract(plan))
            self.assertFalse(audit["ok"])
            self.assertEqual(audit["error"], "LINK_CLOSURE")
            self.assertGreater(audit["closure"]["missing_terminal"], 0)

    def test_cycle_is_not_ok(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            _write(
                plan,
                [(r"E:\BLACKBOX\a.txt", 4)],
                [],
                [(r"E:\BLACKBOX\a", r"E:\BLACKBOX\b"), (r"E:\BLACKBOX\b", r"E:\BLACKBOX\a")],
            )
            audit = chain.inspect_plan(plan, _contract(plan))
            self.assertFalse(audit["ok"])
            self.assertGreater(audit["closure"]["cycles"], 0)

    def test_missing_parent_is_not_ok(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            _write(plan, [(r"E:\BLACKBOX\missing\a.txt", 4)], [], [])
            audit = chain.inspect_plan(plan, _contract(plan))
            self.assertFalse(audit["ok"])
            self.assertGreater(audit["closure"]["missing_parent"], 0)

    def test_file_under_reparse_is_not_ok(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            _write(plan, [(r"E:\BLACKBOX\link\a.txt", 4)], [], [], reparses=[r"E:\BLACKBOX\link"])
            audit = chain.inspect_plan(plan, _contract(plan))
            self.assertFalse(audit["ok"])
            self.assertGreater(audit["closure"]["under_reparse"], 0)

    def test_engines_mapping_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            _write(
                plan,
                [(r"E:\BLACKBOX\a.txt", 4)],
                [r"D:\foo"],
                [(r"D:\link", r"E:\BLACKBOX_ENGINES\foo")],
            )
            audit = chain.inspect_plan(plan, _contract(plan))
            self.assertTrue(audit["ok"], audit)
            self.assertEqual(audit["closure"]["engines_mapped"], 1)

    def test_as_is_without_copy_stays_closed(self):
        self.assertFalse(chain.formal_write_gate({
            "phase": "FORMAL_COPY",
            "scope": "FULL",
            "copy_authorized": False,
            "full_migration": False,
            "version_choice": "AS_IS_MIGRATE_MARKED",
            "plan_sha": chain.CANDIDATE_PLAN_SHA,
            "source_plan_sha": chain.CANDIDATE_PLAN_SHA,
            "dest_roots": [chain.FORMAL_E, chain.FORMAL_D],
            "expected_volume_serial": chain.EXPECTED_VOLUME,
            "expected_unique_id": chain.EXPECTED_DISK,
            "max_unique_bytes": 1,
            "subset_unique_bytes": 1,
            "state_path": r"C:\LAN_SHARE_REPORT\state.sqlite",
            "dest_probe": {"ok": True, "volume_serial": chain.EXPECTED_VOLUME, "unique_id": chain.EXPECTED_DISK, "filesystem": "NTFS"},
            "plan_audit": {"ok": True},
            "run": {"plan_digest": chain.CANDIDATE_PLAN_SHA, "inputs_digest": chain.CANDIDATE_PLAN_SHA, "code_digest": "x", "dest_volume": chain.EXPECTED_VOLUME, "dest_root": chain.FORMAL_E},
        }, None))


if __name__ == "__main__":
    unittest.main(verbosity=1)
