# -*- coding: utf-8 -*-
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_acceptance
import r9_formal_chain as chain
import r9_state
import r9_formal_executor as ex
import r9_plan_reader as reader
import r9_runner
import r9_source_contract as source_contract
import r9_winio as winio

PARENT = chain.BENCH_PARENT
BLACKBOX = chain.BENCH_E
SUB = BLACKBOX + r"\sub"
FILE_A = SUB + r"\a.txt"
FILE_B = SUB + r"\b.txt"
SOURCE = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\sub\\a.txt"
PAYLOAD = b"hello-formal-chain"


class MetaOnly(winio.VirtualSyscalls):
    def observe(self, path):
        seen = super().observe(path)
        if isinstance(seen, dict):
            seen["sha256"] = None
        return seen


class OrderBackend(winio.WindowsBackend):
    def __init__(self, sc):
        super().__init__(sc)
        self.made = []

    def ensure_directory(self, path):
        self.made.append(str(path))
        return super().ensure_directory(path)


def _plan(path: Path, rows):
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
        CREATE INDEX ix_entity ON paths(is_dir, is_reparse, volume_serial, file_id);
        """
    )
    for row in rows:
        kind = row[0]
        if kind == "dir":
            db.execute(
                "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                (row[1], 1, 0, 0, 0, None, None, 1, None, "test"),
            )
        elif kind == "entity":
            _volume, file_id, size, paths = row[1], row[2], row[3], row[4]
            db.execute(
                "INSERT INTO entities VALUES (?,?,?,?,?,?,0,0)",
                (_volume, file_id, len(paths), size, size, len(paths)),
            )
            for dest in paths:
                db.execute(
                    "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (dest, 0, 0, size, 4096, _volume, file_id, len(paths), None, "test"),
                )
    db.commit()
    db.close()


def _contract(plan: Path, state: Path, **overrides):
    digest = chain.sha256_file(plan)
    total = 0
    db = sqlite3.connect(plan)
    total = int(db.execute("SELECT COALESCE(SUM(min_size),0) FROM entities").fetchone()[0])
    db.close()
    payload = {
        "phase": "FORMAL_COPY",
        "scope": "BENCH",
        "copy_authorized": True,
        "full_migration": False,
        "isolated_chain": True,
        "dest_roots": [BLACKBOX, chain.BENCH_D],
        "expected_volume_serial": "DEST",
        "expected_unique_id": "ISOLATED",
        "source_plan_sha": chain.FULL_PLAN_SHA,
        "plan_path": str(plan),
        "plan_sha": digest,
        "max_unique_bytes": total,
        "subset_unique_bytes": total,
        "state_path": str(state),
        "run": {
            "run_id": "formal-chain-test",
            "plan_digest": digest,
            "inputs_digest": digest,
            "code_digest": source_contract.code_digest(),
            "dest_volume": "DEST",
            "dest_root": BLACKBOX,
            "acceptance_roots": [PARENT],
        },
    }
    payload.update(overrides)
    return payload


def _backend():
    sc = MetaOnly(dest_volume="DEST")
    sc.files[SOURCE] = PAYLOAD
    sc.identities[SOURCE] = {
        "file_id": "11",
        "volume_serial": "2387166462",
        "mtime": "T1",
        "object_type": "file",
    }
    return OrderBackend(sc)


class FormalChainTests(unittest.TestCase):
    def test_metadata_observe_does_not_hash_aliases_and_rerun_accepts(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            state = td / "state.sqlite"
            _plan(plan, [
                ("dir", PARENT),
                ("dir", BLACKBOX),
                ("dir", SUB),
                ("entity", "2387166462", "11", len(PAYLOAD), [FILE_A, FILE_B]),
            ])
            contract = _contract(plan, state)
            probe = {"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"}
            backend = _backend()
            path = td / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            self.assertEqual(ex.main(["dry-run", "--contract", str(path)], backend=backend, probe=probe), 0)
            self.assertEqual(backend.sc.write_calls, 0)
            self.assertFalse(state.exists())
            self.assertFalse(chain.last_result["would_write"])
            self.assertTrue(chain.last_result["gate_open"])
            self.assertEqual(ex.main(["execute", "--contract", str(path)], backend=backend, probe=probe), 0, chain.last_result)
            result = chain.last_result
            self.assertEqual(result["copied_count"], 1)
            self.assertEqual(result["linked_count"], 1)
            self.assertEqual(result["acceptance"]["content_hash_calls"], 1)
            self.assertEqual(backend.sc.hash_calls, 1)
            self.assertFalse(result["full_plan_acceptance"])
            self.assertLess(backend.made.index(PARENT), backend.made.index(BLACKBOX))
            self.assertLess(backend.made.index(BLACKBOX), backend.made.index(SUB))
            self.assertEqual(ex.main(["execute", "--contract", str(path)], backend=backend, probe=probe), 0, chain.last_result)
            self.assertEqual(chain.last_result["copied_count"], 0)
            self.assertEqual(chain.last_result["linked_count"], 0)
            self.assertTrue(chain.last_result["acceptance"]["full_acceptance"])
            self.assertEqual(backend.sc.hash_calls, 3)

    def test_refusals_do_not_write_and_partial_or_empty_acceptance_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            state = td / "state.sqlite"
            _plan(plan, [
                ("dir", PARENT),
                ("dir", BLACKBOX),
                ("dir", SUB),
                ("entity", "2387166462", "11", len(PAYLOAD), [FILE_A, FILE_B]),
            ])
            probe = {"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"}
            backend = _backend()
            denied = _contract(plan, state, copy_authorized=False)
            denied_path = td / "denied.json"
            denied_path.write_text(json.dumps(denied), encoding="utf-8")
            self.assertEqual(ex.main(["execute", "--contract", str(denied_path)], backend=backend, probe=probe), 3)
            self.assertEqual(backend.sc.write_calls, 0)
            self.assertTrue(chain.last_result["refused_before_write"])
            self.assertIn("backend_calls", chain.last_result)

            wrong = _contract(plan, td / "wrong.sqlite")
            wrong_probe = dict(probe, unique_id="OTHER")
            wrong_path = td / "wrong.json"
            wrong_path.write_text(json.dumps(wrong), encoding="utf-8")
            fresh = _backend()
            self.assertEqual(ex.main(["execute", "--contract", str(wrong_path)], backend=fresh, probe=wrong_probe), 3)
            self.assertEqual(fresh.sc.write_calls, 0)

            bad = _contract(plan, td / "bad.sqlite")
            bad["plan_sha"] = "0" * 64
            bad["run"]["plan_digest"] = "0" * 64
            bad["run"]["inputs_digest"] = "0" * 64
            bad_path = td / "bad.json"
            bad_path.write_text(json.dumps(bad), encoding="utf-8")
            fresh = _backend()
            self.assertEqual(ex.main(["execute", "--contract", str(bad_path)], backend=fresh, probe=probe), 3)
            self.assertEqual(fresh.sc.write_calls, 0)
            self.assertEqual(chain.last_result["reason"], "PLAN_DIGEST_MISMATCH")

            huge = td / "huge.sqlite"
            _plan(huge, [("dir", PARENT), ("entity", "2387166462", "11", chain.BUDGET + 1, [FILE_A])])
            huge_state = td / "huge.sqlite.state"
            huge_contract = _contract(huge, huge_state)
            huge_path = td / "huge.json"
            huge_path.write_text(json.dumps(huge_contract), encoding="utf-8")
            fresh = _backend()
            self.assertEqual(ex.main(["execute", "--contract", str(huge_path)], backend=fresh, probe=probe), 3)
            self.assertEqual(fresh.sc.write_calls, 0)
            self.assertEqual(chain.last_result["reason"], "BUDGET")

            outside = td / "out.sqlite"
            _plan(outside, [("dir", PARENT), ("entity", "2387166462", "11", len(PAYLOAD), [r"C:\nope\a.txt"])])
            outside_contract = _contract(outside, td / "out.state")
            outside_path = td / "out.json"
            outside_path.write_text(json.dumps(outside_contract), encoding="utf-8")
            fresh = _backend()
            self.assertEqual(ex.main(["execute", "--contract", str(outside_path)], backend=fresh, probe=probe), 3)
            self.assertEqual(fresh.sc.write_calls, 0)
            self.assertEqual(chain.last_result["reason"], "SCOPE_ESCAPE")

            empty = td / "empty.sqlite"
            _plan(empty, [])
            empty_run = {
                "run_id": "empty",
                "plan_digest": chain.sha256_file(empty),
                "inputs_digest": chain.sha256_file(empty),
                "code_digest": source_contract.code_digest(),
                "dest_volume": "DEST",
                "dest_root": BLACKBOX,
            }
            empty_state = td / "empty.state"
            r9_state.open_state(empty_state).close()
            report = r9_acceptance.full_acceptance(empty, empty_state, _backend(), empty_run)
            self.assertFalse(report["full_acceptance"])
            self.assertIn("EMPTY_PLAN", report["reasons"])

            both = td / "both.sqlite"
            other = SUB + r"\c.txt"
            _plan(both, [
                ("dir", PARENT),
                ("dir", BLACKBOX),
                ("dir", SUB),
                ("entity", "2387166462", "11", len(PAYLOAD), [FILE_A]),
                ("entity", "2387166462", "12", len(PAYLOAD), [other]),
            ])
            partial_state = td / "partial.sqlite"
            partial = _contract(both, partial_state)
            partial["plan_audit"] = {"ok": True}
            partial["dest_probe"] = probe
            sc = MetaOnly(dest_volume="DEST")
            for source, file_id in (
                (SOURCE, "11"),
                ("\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\sub\\c.txt", "12"),
            ):
                sc.files[source] = PAYLOAD
                sc.identities[source] = {
                    "file_id": file_id,
                    "volume_serial": "2387166462",
                    "mtime": "T1",
                    "object_type": "file",
                }
            backend = winio.WindowsBackend(sc)
            conn = reader.connect(both)
            try:
                entities = list(reader.read_executable(conn))
            finally:
                conn.close()
            ran = r9_runner.production_run(iter(entities[:1]), backend, {
                **partial,
                "directories": [PARENT, BLACKBOX, SUB],
                "links": [],
                "accept": True,
                "plan_path": str(both),
            }, partial_state)
            self.assertFalse(ran["acceptance"]["full_acceptance"])
            self.assertTrue(ran["acceptance"]["expected_entities"] > ran["acceptance"]["checked_entities"])

    def test_simulated_chain_is_not_a_real_backend_and_full_scope_needs_frozen_plan(self):
        win = winio.WindowsBackend(winio.Win32Syscalls())
        self.assertFalse(r9_runner.allows_write(
            {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "3630886530"}},
            win,
        ))
        self.assertEqual(win.sc.write_calls, 0)
        virtual = winio.WindowsBackend(winio.VirtualSyscalls())
        self.assertFalse(chain.formal_write_gate({
            "phase": "FORMAL_COPY",
            "scope": "FULL",
            "copy_authorized": True,
            "full_migration": True,
            "isolated_chain": True,
            "dest_roots": [chain.FORMAL_E, chain.FORMAL_D],
            "expected_volume_serial": "DEST",
            "expected_unique_id": "ISOLATED",
            "source_plan_sha": chain.FULL_PLAN_SHA,
            "plan_sha": "abc",
            "max_unique_bytes": 1,
            "subset_unique_bytes": 1,
            "state_path": r"C:\LAN_SHARE_REPORT\state.sqlite",
            "dest_probe": {"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED"},
            "plan_audit": {"ok": True},
            "run": {
                "plan_digest": "abc",
                "inputs_digest": "abc",
                "code_digest": "code",
                "dest_volume": "DEST",
                "dest_root": chain.FORMAL_E,
            },
        }, virtual))
        sample = r"E:\R9_FORMAL_PILOT_1G_20261014\BLACKBOX\数据\a"
        mapped = reader.map_inventory_path(sample)
        self.assertEqual(mapped["dest_path"], sample)
        self.assertTrue(mapped["source_path"].startswith("\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\"))
        deng = r"E:\R9_FORMAL_PILOT_1G_20261014\BLACKBOX_ENGINES\JQ\a"
        mapped = reader.map_inventory_path(deng)
        self.assertEqual(mapped["dest_path"], deng)
        self.assertTrue(mapped["source_path"].startswith("\\\\192.168.100.2\\D_DRIVE\\JQ\\"))
        self.assertFalse(mapped["dest_path"].startswith("\\\\"))
        self.assertEqual(chain.classify_failure("SOURCE_CHANGED", 4), ("PHASE_STOP", 4))
        self.assertEqual(chain.classify_failure("PLAN_DIGEST_MISMATCH", 0), ("REFUSED_BEFORE_WRITE", 3))
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "x"
            path.write_bytes(b"abc")
            snap = path.stat()
            path.write_bytes(b"abcd")
            with self.assertRaisesRegex(RuntimeError, "PLAN_CHANGED"):
                chain.assert_plan_stable(path, snap)


if __name__ == "__main__":
    unittest.main()
