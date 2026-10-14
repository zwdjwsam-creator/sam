# -*- coding: utf-8 -*-
"""Names-only directory enumeration must still reach full metadata and one hash per entity."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_acceptance
import r9_formal_chain as chain
import r9_runner
import r9_source_contract as source_contract
import r9_state
import r9_winio as winio

PARENT = chain.BENCH_PARENT
BLACKBOX = chain.BENCH_E
SUB = BLACKBOX + r"\sub"
FILE_A = SUB + r"\a.txt"
FILE_B = SUB + r"\b.txt"
EMPTY = BLACKBOX + r"\empty_target"
JUMP = BLACKBOX + r"\jump"
PAYLOAD = b"enum-ok"
TAG = 0xA0000003


class NamesOnly(winio.VirtualSyscalls):
    def list_nofollow(self, root):
        return [
            {"path": item["path"], "object_type": item["object_type"]}
            for item in super().list_nofollow(root)
        ]


def _plan(path: Path):
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
    db.execute("INSERT INTO entities VALUES ('2387166462','11',2,?,?,2,0,0)", (len(PAYLOAD), len(PAYLOAD)))
    for dest in (FILE_A, FILE_B):
        db.execute(
            "INSERT INTO paths VALUES (?,?,0,?,?, '2387166462','11',2,NULL,'t')",
            (dest, 0, len(PAYLOAD), 4096),
        )
    for directory in chain.directory_chain(SUB, True) + [EMPTY]:
        db.execute("INSERT OR IGNORE INTO paths VALUES (?,?,0,0,0,NULL,NULL,1,NULL,'t')", (directory, 1))
    db.execute(
        "INSERT INTO links VALUES (?,?, 't', ?, 'OK', NULL, ?, ?, ?, 't', 0, 0, ?, 't')",
        (JUMP, EMPTY, EMPTY, EMPTY, JUMP, EMPTY, TAG),
    )
    db.commit()
    db.close()


def _seed(state: Path, digest: str, sha: str, code: str):
    db = r9_state.open_state(state)
    db.execute(
        "INSERT INTO run_bind VALUES (?,?,?,?,?,?)",
        ("enum-test", digest, digest, code, "DEST", BLACKBOX),
    )
    db.execute(
        """
        INSERT INTO stage(item_key, kind, phase, dest_path, sha256, file_id, volume_serial, object_type, link_target, logical_size, parent_key)
        VALUES ('entity:2387166462|11','entity','DONE',?,?,?,?, 'file', NULL, ?, '2387166462|11')
        """,
        (FILE_A, sha, "D1", "DEST", len(PAYLOAD)),
    )
    db.commit()
    db.close()


def _store(payload=PAYLOAD):
    sc = NamesOnly(dest_volume="DEST")
    for directory in chain.directory_chain(SUB, True) + [EMPTY]:
        sc.ensure_directory(directory)
    for dest in (FILE_A, FILE_B):
        sc.files[dest] = payload
        sc.identities[dest] = {
            "file_id": "D1",
            "volume_serial": "DEST",
            "object_type": "file",
            "allocation_size": 4096,
        }
    sc.create_reparse(JUMP, EMPTY, "junction")
    return sc


def _run(path, state, sc, code):
    digest = chain.sha256_file(path)
    _seed(state, digest, hashlib.sha256(PAYLOAD).hexdigest(), code)
    run = {
        "run_id": "enum-test",
        "plan_digest": digest,
        "inputs_digest": digest,
        "code_digest": code,
        "dest_volume": "DEST",
        "dest_root": BLACKBOX,
        "acceptance_roots": [PARENT],
    }
    return r9_acceptance.full_acceptance(path, state, winio.WindowsBackend(sc), run)


class EnumAcceptanceTests(unittest.TestCase):
    def test_names_only_enumeration_hashes_each_entity_once(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            report = _run(plan, td / "state.sqlite", _store(), source_contract.code_digest())
            self.assertTrue(report["full_acceptance"], report["reasons"])
            self.assertEqual(report["content_hash_calls"], 1)
            self.assertEqual(report["content_bytes"], len(PAYLOAD))

    def test_names_only_rejects_bad_content_missing_tag_and_dangling_target(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            bad = _run(plan, td / "bad.sqlite", _store(b"nope-not-the-same"), source_contract.code_digest())
            self.assertFalse(bad["full_acceptance"])
            self.assertTrue({"IDENTITY_MISMATCH", "DEST_VOLUME", "MISSING_FIELD"} & set(bad["reasons"]))

        class NoTag(NamesOnly):
            def observe(self, path):
                seen = super().observe(path)
                if isinstance(seen, dict):
                    seen["reparse_tag"] = None
                return seen

        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            sc = NoTag(dest_volume="DEST")
            for directory in chain.directory_chain(SUB, True) + [EMPTY]:
                sc.ensure_directory(directory)
            for dest in (FILE_A, FILE_B):
                sc.files[dest] = PAYLOAD
                sc.identities[dest] = {"file_id": "D1", "volume_serial": "DEST", "object_type": "file", "allocation_size": 4096}
            sc.create_reparse(JUMP, EMPTY, "junction")
            report = _run(plan, td / "tag.sqlite", sc, source_contract.code_digest())
            self.assertFalse(report["full_acceptance"])
            self.assertIn("MISSING_FIELD", report["reasons"])

        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            sc = _store()
            del sc.files[EMPTY]
            del sc.identities[EMPTY]
            report = _run(plan, td / "dangle.sqlite", sc, source_contract.code_digest())
            self.assertFalse(report["full_acceptance"])
            self.assertTrue("DANGLING_TARGET" in report["reasons"] or "MISSING_OBJECT" in report["reasons"] or "OBSERVE_ERROR" in report["reasons"])

    def test_reverify_does_not_open_copy_and_keeps_historical_digest(self):
        with self.assertRaisesRegex(RuntimeError, "REVERIFY_IS_NOT_COPY"):
            r9_runner.production_run(iter(()), winio.WindowsBackend(winio.VirtualSyscalls()), {"readonly_reverify": True, "run": {"readonly_reverify": True}}, Path("C:/LAN_SHARE_REPORT/unused.sqlite"))
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            state = td / "state.sqlite"
            _plan(plan)
            old = "a" * 64
            digest = chain.sha256_file(plan)
            _seed(state, digest, hashlib.sha256(PAYLOAD).hexdigest(), old)
            contract = {
                "plan_path": str(plan),
                "state_path": str(state),
                "source_plan_path": str(plan),
                "plan_sha": digest,
                "source_plan_sha": digest,
                "run": {
                    "run_id": "enum-test",
                    "plan_digest": digest,
                    "inputs_digest": digest,
                    "code_digest": old,
                    "dest_volume": "DEST",
                    "dest_root": BLACKBOX,
                    "acceptance_roots": [PARENT],
                },
            }
            result = chain.readonly_reverify(contract, backend=winio.WindowsBackend(_store()))
            self.assertEqual(result["write_attempts"], 0)
            self.assertTrue(result["acceptance"]["full_acceptance"], result["acceptance"]["reasons"])
            self.assertEqual(result["copy_code_digest"], old)
            self.assertEqual(result["verifier_code_digest"], source_contract.code_digest())
            self.assertNotEqual(result["copy_code_digest"], result["verifier_code_digest"])
            self.assertFalse(result["full_plan_acceptance"])
            self.assertEqual(result["acceptance"]["content_hash_calls"], 1)


if __name__ == "__main__":
    unittest.main()
