# -*- coding: utf-8 -*-
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_formal_chain as chain
import r9_plan_reader as reader
import r9_runner
import r9_source_contract as source_contract
import r9_winio as winio

PAYLOAD = b"phase-timing-bytes"
PARENT = chain.RECHECK_PARENT
BLACKBOX = chain.RECHECK_E
FILE = BLACKBOX + r"\a.bin"
SOURCE = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\a.bin"


def _entity(size=len(PAYLOAD)):
    return {
        "source_path": "SRC",
        "dest_path": FILE,
        "file_id": "11",
        "volume_serial": "2387166462",
        "logical_size": size,
        "mtime": "T1",
        "mtime_status": "FROM_PLAN",
    }


def _prepare(sc, payload=PAYLOAD):
    sc.files["SRC"] = payload
    sc.identities["SRC"] = {
        "file_id": "11",
        "volume_serial": "2387166462",
        "mtime": "T1",
        "object_type": "file",
        "allocation_size": 4096,
    }


class PhaseTimingTests(unittest.TestCase):
    def test_failed_open_identity_and_flush_leave_later_phases_unentered(self):
        class OpenFails(winio.VirtualSyscalls):
            def open_source(self, path):
                raise OSError("open failed")

        backend = winio.WindowsBackend(OpenFails())
        with self.assertRaisesRegex(OSError, "open failed"):
            backend.copy_entity(_entity())
        self.assertEqual(backend.phase_stats["source_open_calls"], 1)
        self.assertIsInstance(backend.phase_stats["source_open_seconds"], float)
        for name in ("source_identity_calls", "stream_read_calls", "flush_calls", "readback_open_calls", "readback_calls", "commit_no_replace_calls"):
            self.assertEqual(backend.phase_stats[name], "NOT_RUN", name)

        sc = winio.VirtualSyscalls()
        _prepare(sc)
        sc.identities["SRC"]["file_id"] = "other"
        backend = winio.WindowsBackend(sc)
        with self.assertRaisesRegex(RuntimeError, "SOURCE_CHANGED"):
            backend.copy_entity(_entity())
        self.assertEqual(backend.phase_stats["source_open_calls"], 1)
        self.assertEqual(backend.phase_stats["source_identity_calls"], 1)
        self.assertEqual(backend.phase_stats["flush_calls"], "NOT_RUN")
        self.assertEqual(backend.phase_stats["readback_calls"], "NOT_RUN")
        self.assertEqual(backend.phase_stats["readback_open_calls"], "NOT_RUN")

        class FlushFails(winio.VirtualSyscalls):
            def flush(self, handle):
                raise OSError("flush failed")

        sc = FlushFails()
        _prepare(sc)
        backend = winio.WindowsBackend(sc)
        with self.assertRaisesRegex(OSError, "flush failed"):
            backend.copy_entity(_entity())
        self.assertEqual(backend.phase_stats["source_open_calls"], 1)
        self.assertEqual(backend.phase_stats["flush_calls"], 1)
        self.assertIsInstance(backend.phase_stats["flush_seconds"], float)
        self.assertEqual(backend.phase_stats["readback_open_calls"], "NOT_RUN")
        self.assertEqual(backend.phase_stats["readback_calls"], "NOT_RUN")
        self.assertEqual(backend.phase_stats["commit_no_replace_calls"], "NOT_RUN")

    def test_one_entity_separates_source_open_from_local_readback_open(self):
        sc = winio.VirtualSyscalls()
        _prepare(sc)
        backend = winio.WindowsBackend(sc)
        copied = backend.copy_entity(_entity())
        self.assertEqual(copied["bytes"], len(PAYLOAD))
        self.assertEqual(backend.phase_stats["source_open_calls"], 1)
        self.assertEqual(backend.phase_stats["readback_open_calls"], 1)
        self.assertIsInstance(backend.phase_stats["stream_read_seconds"], float)
        self.assertIsInstance(backend.phase_stats["stream_write_seconds"], float)
        self.assertEqual(backend.phase_stats["commit_no_replace_calls"], 1)
        self.assertIsInstance(backend.phase_stats["commit_no_replace_seconds"], float)
        self.assertGreater(backend.phase_stats["stream_read_bytes"], 0)

    def test_runner_commit_time_starts_only_when_a_commit_happens(self):
        sc = winio.VirtualSyscalls(dest_volume="DEST")
        sc.files[SOURCE] = PAYLOAD
        sc.identities[SOURCE] = {
            "file_id": "11",
            "volume_serial": "2387166462",
            "mtime": "T1",
            "object_type": "file",
        }
        backend = winio.WindowsBackend(sc)
        self.assertEqual(backend._state_commit_calls, "NOT_RUN")
        self.assertEqual(backend._state_commit_seconds, "NOT_RUN")
        with tempfile.TemporaryDirectory() as raw:
            result = r9_runner.production_run([
                {
                    "entity_key": "2387166462|11",
                    "source_path": SOURCE,
                    "dest_path": FILE,
                    "file_id": "11",
                    "volume_serial": "2387166462",
                    "logical_size": len(PAYLOAD),
                    "mtime": "T1",
                    "mtime_status": "FROM_PLAN",
                    "extra_dest_paths": [],
                }
            ], backend, {
                "phase": "SIMULATED_CHAIN",
                "dest_binding": {"volume_serial": "DEST"},
                "directories": [],
                "links": [],
                "accept": False,
            }, Path(raw) / "state.sqlite")
        self.assertGreaterEqual(result["state_commit_calls"], 1)
        self.assertIsInstance(result["state_commit_seconds"], float)
        self.assertEqual(result["phase_stats"]["source_open_calls"], 1)
        self.assertEqual(result["copied_count"], 1)

    def test_recheck_root_is_exact_and_formal_failure_keeps_stats(self):
        sample = PARENT + r"\BLACKBOX\数据\a"
        mapped = reader.map_inventory_path(sample)
        self.assertEqual(mapped["dest_path"], sample)
        self.assertTrue(mapped["source_path"].startswith("\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\"))
        engines = PARENT + r"\BLACKBOX_ENGINES\JQ\a"
        mapped = reader.map_inventory_path(engines)
        self.assertEqual(mapped["dest_path"], engines)
        self.assertTrue(mapped["source_path"].startswith("\\\\192.168.100.2\\D_DRIVE\\JQ\\"))
        self.assertTrue(reader.dest_allowed(sample))
        self.assertFalse(reader.dest_allowed(r"E:\OTHER_ROOT\a"))
        self.assertIsNone(chain.bench_layout((r"E:\OTHER_ROOT\BLACKBOX", r"E:\OTHER_ROOT\BLACKBOX_ENGINES")))
        self.assertEqual(chain.bench_layout((chain.BENCH_E, chain.BENCH_D))[0], chain.BENCH_PARENT)
        self.assertEqual(chain.bench_layout((BLACKBOX, chain.RECHECK_D))[0], PARENT)

        class FlushFails(winio.VirtualSyscalls):
            def flush(self, handle):
                raise OSError("flush failed")

        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
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
            for directory in (PARENT, BLACKBOX):
                db.execute(
                    "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (directory, 1, 0, 0, 0, None, None, 1, None, "test"),
                )
            db.execute(
                "INSERT INTO entities VALUES (?,?,?,?,?,?,0,0)",
                ("2387166462", "11", 1, len(PAYLOAD), len(PAYLOAD), 1),
            )
            db.execute(
                "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                (FILE, 0, 0, len(PAYLOAD), 4096, "2387166462", "11", 1, None, "test"),
            )
            db.commit()
            db.close()
            digest = chain.sha256_file(plan)
            state = td / "state.sqlite"
            contract = {
                "phase": "FORMAL_COPY",
                "scope": "BENCH",
                "copy_authorized": True,
                "full_migration": False,
                "isolated_chain": True,
                "dest_roots": [BLACKBOX, chain.RECHECK_D],
                "expected_volume_serial": "DEST",
                "expected_unique_id": "ISOLATED",
                "source_plan_sha": chain.FULL_PLAN_SHA,
                "plan_path": str(plan),
                "plan_sha": digest,
                "max_unique_bytes": len(PAYLOAD),
                "subset_unique_bytes": len(PAYLOAD),
                "state_path": str(state),
                "run": {
                    "run_id": "phase-timing",
                    "plan_digest": digest,
                    "inputs_digest": digest,
                    "code_digest": source_contract.code_digest(),
                    "dest_volume": "DEST",
                    "dest_root": BLACKBOX,
                },
            }
            sc = FlushFails(dest_volume="DEST")
            sc.files[SOURCE] = PAYLOAD
            sc.identities[SOURCE] = {
                "file_id": "11",
                "volume_serial": "2387166462",
                "mtime": "T1",
                "object_type": "file",
            }
            backend = winio.WindowsBackend(sc)
            probe = {"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"}
            result = chain.execute_contract(contract, "execute", backend=backend, probe=probe)
        self.assertEqual(result["exit_code"], 4)
        self.assertIn("flush failed", result["error"])
        self.assertNotEqual(result["exit_code"], 0)
        self.assertEqual(result["phase_stats"]["flush_calls"], 1)
        self.assertEqual(result["phase_stats"]["source_open_calls"], 1)
        self.assertEqual(result["phase_stats"]["readback_calls"], "NOT_RUN")
        self.assertIn("copy_seconds", result["timing_note"])
        self.assertFalse(result["full_plan_acceptance"])


if __name__ == "__main__":
    unittest.main()
