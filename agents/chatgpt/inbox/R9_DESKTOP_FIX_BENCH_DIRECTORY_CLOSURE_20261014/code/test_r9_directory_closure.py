# -*- coding: utf-8 -*-
"""Directory closure uses the generator's directory_chain, not a hand-written good list."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_acceptance
import r9_formal_chain as chain
import r9_formal_executor as ex
import r9_source_contract as source_contract
import r9_state
import r9_winio as winio

EMPTY = r"E:\BLACKBOX\empty_target"
JUMP = r"E:\BLACKBOX\jump"
FILE = r"E:\BLACKBOX\sub\a.txt"
BENCH_EMPTY = chain.BENCH_E + r"\empty_target"
BENCH_JUMP = chain.BENCH_E + r"\jump"
BENCH_FILE = chain.BENCH_E + r"\sub\a.txt"
SOURCE = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\sub\\a.txt"
PAYLOAD = b"closure-file"


def _source(path: Path):
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE paths(
          path TEXT PRIMARY KEY, is_dir INTEGER, is_reparse INTEGER, logical_size INTEGER,
          alloc_size INTEGER, volume_serial TEXT, file_id TEXT, nlinks INTEGER,
          reparse_target TEXT, source TEXT
        );
        CREATE TABLE links(
          path TEXT PRIMARY KEY, target TEXT, source TEXT, mapped_dest TEXT, status TEXT,
          map_id INTEGER, original_target TEXT, migrated_link_path TEXT, migrated_target TEXT,
          map_source TEXT, content_files INTEGER, delta_files INTEGER, reparse_tag INTEGER, tag_source TEXT
        );
        """
    )
    db.execute(
        "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
        (EMPTY, 1, 0, 0, 0, "2387166462", "d1", 1, None, "fixture"),
    )
    db.execute(
        "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
        (JUMP, 1, 1, 0, 0, "2387166462", "j1", 1, EMPTY, "fixture"),
    )
    db.execute(
        "INSERT INTO links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (JUMP, EMPTY, "fixture", EMPTY, "OK", None, EMPTY, None, None, "fixture", 0, 0, 0xA0000003, "fixture"),
    )
    db.commit()
    db.close()


def _subset(path: Path, include_target: bool):
    dirs = set(chain.directory_chain(BENCH_EMPTY, True))
    dirs.update(chain.directory_chain(BENCH_JUMP, False))
    dirs.update(chain.directory_chain(BENCH_FILE, False))
    if not include_target:
        dirs.discard(BENCH_EMPTY)
    db = sqlite3.connect(path)
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
        CREATE TABLE links(
          path TEXT PRIMARY KEY, target TEXT, source TEXT, mapped_dest TEXT, status TEXT,
          map_id INTEGER, original_target TEXT, migrated_link_path TEXT, migrated_target TEXT,
          map_source TEXT, content_files INTEGER, delta_files INTEGER, reparse_tag INTEGER, tag_source TEXT
        );
        CREATE INDEX ix_entity ON paths(is_dir, is_reparse, volume_serial, file_id);
        """
    )
    db.execute(
        "INSERT INTO entities VALUES (?,?,?,?,?,?,0,0)",
        ("2387166462", "11", 1, len(PAYLOAD), len(PAYLOAD), 1),
    )
    db.execute(
        "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
        (BENCH_FILE, 0, 0, len(PAYLOAD), 4096, "2387166462", "11", 1, None, "subset"),
    )
    for directory in dirs:
        if directory.casefold() == BENCH_JUMP.casefold():
            continue
        db.execute(
            "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
            (directory, 1, 0, 0, 0, None, None, 1, None, "subset_parent"),
        )
    db.execute(
        "INSERT INTO links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (BENCH_JUMP, BENCH_EMPTY, "subset", BENCH_EMPTY, "OK", None, BENCH_EMPTY, BENCH_JUMP, BENCH_EMPTY, "subset", 0, 0, 0xA0000003, "plan"),
    )
    db.commit()
    db.close()


def _contract(plan: Path, state: Path):
    digest = chain.sha256_file(plan)
    return {
        "phase": "FORMAL_COPY",
        "scope": "BENCH",
        "copy_authorized": True,
        "full_migration": False,
        "isolated_chain": True,
        "dest_roots": [chain.BENCH_E, chain.BENCH_D],
        "expected_volume_serial": "DEST",
        "expected_unique_id": "ISOLATED",
        "source_plan_sha": chain.FULL_PLAN_SHA,
        "plan_path": str(plan),
        "plan_sha": digest,
        "max_unique_bytes": len(PAYLOAD),
        "subset_unique_bytes": len(PAYLOAD),
        "state_path": str(state),
        "run": {
            "run_id": "closure-fixture",
            "plan_digest": digest,
            "inputs_digest": digest,
            "code_digest": source_contract.code_digest(),
            "dest_volume": "DEST",
            "dest_root": chain.BENCH_E,
            "acceptance_roots": [chain.BENCH_PARENT],
        },
    }


class DirectoryClosureTests(unittest.TestCase):
    def test_generator_keeps_empty_directory_and_rejects_a_removed_target(self):
        dirs = set(chain.directory_chain(BENCH_EMPTY, True))
        dirs.update(chain.directory_chain(BENCH_JUMP, False))
        self.assertIn(BENCH_EMPTY, dirs)
        self.assertNotIn(BENCH_JUMP, dirs)
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            src = td / "source.sqlite"
            _source(src)
            conn = sqlite3.connect(src)
            kind, _nxt = chain._target_kind(conn, EMPTY)
            self.assertEqual(kind, "ordinary")
            conn.close()
            good = td / "good.sqlite"
            bad = td / "bad.sqlite"
            _subset(good, True)
            _subset(bad, False)
            good_conn = sqlite3.connect(good)
            bad_conn = sqlite3.connect(bad)
            self.assertTrue(chain.audit_bench_links(good_conn)["ok"])
            self.assertFalse(chain.audit_bench_links(bad_conn)["ok"])
            good_conn.close()
            bad_conn.close()
            probe = {"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"}
            good_contract = _contract(good, td / "good.state")
            bad_contract = _contract(bad, td / "bad.state")
            self.assertIsNone(chain.inspect_plan(good, good_contract)["error"])
            self.assertEqual(chain.inspect_plan(bad, bad_contract)["error"], "LINK_CLOSURE")
            sc = winio.VirtualSyscalls(dest_volume="DEST")
            sc.files[SOURCE] = PAYLOAD
            sc.identities[SOURCE] = {
                "file_id": "11",
                "volume_serial": "2387166462",
                "mtime": "T1",
                "object_type": "file",
            }
            backend = winio.WindowsBackend(sc)
            path = td / "contract.json"
            path.write_text(json.dumps(good_contract), encoding="utf-8")
            self.assertEqual(ex.main(["execute", "--contract", str(path)], backend=backend, probe=probe), 0, chain.last_result)
            seen = backend.observe_destination(BENCH_EMPTY)
            self.assertEqual(seen["status"], "PRESENT")
            self.assertEqual(seen["object_type"], "directory")
            jumped = backend.observe_destination(BENCH_JUMP)
            self.assertEqual(jumped["reparse_target"], BENCH_EMPTY)
            state = td / "dangling.state"
            r9_state.open_state(state).close()
            report = r9_acceptance.full_acceptance(bad, state, backend, bad_contract["run"])
            self.assertFalse(report["full_acceptance"])
            self.assertIn("DANGLING_TARGET", report["reasons"])


if __name__ == "__main__":
    unittest.main()
