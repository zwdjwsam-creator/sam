# -*- coding: utf-8 -*-
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_acceptance
import r9_formal_executor
import r9_plan_reader as reader
import r9_runner as runner
import r9_state
import r9_winio as winio


def _plan(path: Path, with_mtime: bool = True) -> None:
    db = sqlite3.connect(path)
    mtime_col = ", mtime TEXT" if with_mtime else ""
    mtime_val = ",'t1'" if with_mtime else ""
    db.executescript(
        f"""
        CREATE TABLE entities(volume_serial TEXT, file_id TEXT, min_size INTEGER, path_count INTEGER{mtime_col});
        CREATE TABLE paths(path TEXT, is_dir INTEGER, is_reparse INTEGER, volume_serial TEXT, file_id TEXT);
        CREATE TABLE links(path TEXT, target TEXT, migrated_link_path TEXT, migrated_target TEXT, status TEXT, reparse_tag INTEGER);
        INSERT INTO paths VALUES ('E:\\BLACKBOX',1,0,'','');
        INSERT INTO paths VALUES ('E:\\BLACKBOX\\realdir',1,0,'','');
        INSERT INTO entities VALUES ('2387166462','11',5,2{mtime_val});
        INSERT INTO paths VALUES ('E:\\BLACKBOX\\a.bin',0,0,'2387166462','11');
        INSERT INTO paths VALUES ('E:\\BLACKBOX\\z-link.bin',0,0,'2387166462','11');
        INSERT INTO entities VALUES ('3187598165','11',5,1{mtime_val});
        INSERT INTO paths VALUES ('D:\\engine.bin',0,0,'3187598165','11');
        INSERT INTO links VALUES ('E:\\BLACKBOX\\jump','E:\\BLACKBOX\\realdir',NULL,NULL,'MAPPED_E_BLACKBOX',2684354563);
        """
    )
    db.commit()
    db.close()


def _backend():
    source = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\a.bin"
    payload = b"hello"
    sc = winio.VirtualSyscalls(
        files={source: payload, r"D:\engine.bin": payload},
        identities={
            source: {"file_id": "11", "volume_serial": "2387166462", "mtime": "t1"},
            r"D:\engine.bin": {"file_id": "11", "volume_serial": "3187598165", "mtime": "t1"},
        },
    )
    return sc, winio.WindowsBackend(sc)


def _contract(plan: Path, db: sqlite3.Connection, fault=None, accept=False, run_id="run-1"):
    entities = list(reader.read_executable(db))
    directories = list(reader.iter_directories(db))
    links = list(reader.iter_links(db))
    contract = {
        "phase": "SIMULATED_CHAIN",
        "dest_binding": {"volume_serial": "DEST"},
        "directories": directories,
        "links": links,
        "run": {
            "run_id": run_id,
            "plan_digest": reader.plan_digest(db),
            "inputs_digest": reader.plan_digest(db),
            "code_digest": __import__("r9_source_contract").code_digest(),
            "dest_volume": "DEST",
            "dest_root": r"E:\BLACKBOX",
        },
    }
    if fault:
        contract["fault"] = fault
    if accept:
        contract["accept"] = True
        contract["plan_path"] = str(plan)
    return entities, contract


class CloseTests(unittest.TestCase):
    def test_simulated_plan_reparse_and_full_acceptance(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            db = sqlite3.connect(plan)
            entities, contract = _contract(plan, db, accept=True)
            db.close()
            sc, backend = _backend()
            result = runner.production_run(iter(entities), backend, contract, td / "state.sqlite")
            self.assertTrue(result["acceptance"]["full_acceptance"])
            self.assertEqual(result["reparse_count"], 1)
            self.assertGreater(result["directory_count"], 0)
            jump = backend.observe_destination(r"E:\BLACKBOX\jump")
            self.assertEqual(jump["object_type"], "junction")
            self.assertEqual(jump["reparse_target"], r"E:\BLACKBOX\realdir")
            self.assertEqual(backend.list_nofollow(r"E:\BLACKBOX\jump"), [])
            child = r"E:\BLACKBOX\realdir\child.bin"
            sc.files[child] = b"child"
            sc.identities[child] = {"file_id": "child", "volume_serial": "DEST", "object_type": "file", "allocation_size": 4096}
            self.assertEqual(backend.list_nofollow(r"E:\BLACKBOX\jump"), [])
            self.assertEqual(len(backend.list_nofollow(r"E:\BLACKBOX\realdir")), 1)
            one = backend.observe_destination(r"E:\BLACKBOX\a.bin")
            two = backend.observe_destination(r"E:\BLACKBOX_ENGINES\engine.bin")
            self.assertEqual(one["sha256"], two["sha256"])
            self.assertNotEqual(one["file_id"], two["file_id"])
            self.assertNotEqual(result["acceptance"]["allocation_bytes"], result["acceptance"]["content_bytes"])
            writes = sc.write_calls
            db2 = sqlite3.connect(plan)
            entities2, contract2 = _contract(plan, db2)
            db2.close()
            again = runner.production_run(iter(entities2), backend, contract2, td / "state.sqlite")
            self.assertEqual(sc.write_calls, writes)
            self.assertEqual(again["skipped_entities"], 2)
            self.assertEqual(again["skipped_reparse"], 1)
            sc.identities[r"E:\BLACKBOX\jump"]["reparse_target"] = r"E:\BLACKBOX\other"
            with self.assertRaisesRegex(RuntimeError, "REPARSE_MISMATCH"):
                runner.production_run(iter(entities2), backend, contract2, td / "state.sqlite")

    def test_interrupt_points_and_tamper(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            db = sqlite3.connect(plan)
            entities, contract = _contract(plan, db, fault="A")
            db.close()
            first = dict(entities[0])
            first["extra_dest_paths"] = []
            sc, backend = _backend()
            contract["directories"] = []
            contract["links"] = []
            with self.assertRaisesRegex(RuntimeError, "INTERRUPT_A"):
                runner.production_run(iter([first]), backend, contract, td / "a.sqlite")
            self.assertEqual(backend.observe_destination(first["dest_path"])["status"], "PRESENT")
            writes = sc.write_calls
            contract.pop("fault")
            resumed = runner.production_run(iter([first]), backend, contract, td / "a.sqlite")
            self.assertEqual(resumed["resumed_entities"], 1)
            self.assertEqual(resumed["copied_count"], 0)
            self.assertEqual(sc.write_calls, writes)
            sc.files[first["dest_path"]] = b"tampered"
            sc.identities[first["dest_path"]]["file_id"] = "evil"
            with self.assertRaisesRegex(RuntimeError, "RESUME_DEST_MISMATCH"):
                runner.production_run(iter([first]), backend, contract, td / "a.sqlite")

            sc, backend = _backend()
            db = sqlite3.connect(plan)
            entities, contract = _contract(plan, db, fault="B")
            db.close()
            contract["directories"] = []
            contract["links"] = []
            entities[0]["extra_dest_paths"] = list(entities[0]["extra_dest_paths"]) + [r"E:\BLACKBOX\z-link2.bin"]
            with self.assertRaisesRegex(RuntimeError, "INTERRUPT_B"):
                runner.production_run(iter([entities[0]]), backend, contract, td / "b.sqlite")
            mid = sc.write_calls
            contract.pop("fault")
            resumed = runner.production_run(iter([entities[0]]), backend, contract, td / "b.sqlite")
            self.assertEqual(resumed["linked_count"], 1)
            self.assertEqual(resumed["skipped_entities"], 1)
            self.assertEqual(sc.write_calls, mid + 1)
            alias = entities[0]["extra_dest_paths"][0]
            sc.identities[alias]["volume_serial"] = "OTHER"
            with self.assertRaisesRegex(RuntimeError, "RESUME_ALIAS_MISMATCH"):
                runner.production_run(iter([entities[0]]), backend, contract, td / "b.sqlite")

            sc, backend = _backend()
            db = sqlite3.connect(plan)
            entities, contract = _contract(plan, db, fault="C")
            db.close()
            contract["directories"] = []
            contract["links"] = []
            with self.assertRaisesRegex(RuntimeError, "INTERRUPT_C"):
                runner.production_run(iter([entities[0]]), backend, contract, td / "c.sqlite")
            writes = sc.write_calls
            self.assertEqual(backend.observe_destination(entities[0]["extra_dest_paths"][0])["status"], "PRESENT")
            contract.pop("fault")
            resumed = runner.production_run(iter([entities[0]]), backend, contract, td / "c.sqlite")
            self.assertEqual(resumed["resumed_links"], 1)
            self.assertEqual(sc.write_calls, writes)

            sc, backend = _backend()
            db = sqlite3.connect(plan)
            entities, contract = _contract(plan, db, fault="C_REPARSE")
            db.close()
            contract["directories"] = [r"E:\BLACKBOX", r"E:\BLACKBOX\realdir"]
            with self.assertRaisesRegex(RuntimeError, "INTERRUPT_C"):
                runner.production_run(iter(entities), backend, contract, td / "cr.sqlite")
            writes = sc.write_calls
            contract.pop("fault")
            resumed = runner.production_run(iter(entities), backend, contract, td / "cr.sqlite")
            self.assertEqual(resumed["resumed_reparse"], 1)
            self.assertEqual(sc.write_calls, writes)

    def test_rejections_do_not_write(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan, with_mtime=False)
            db = sqlite3.connect(plan)
            entity = next(reader.read_executable(db))
            db.close()
            self.assertEqual(entity["mtime_status"], "ABSENT_IN_PLAN")
            sc, backend = _backend()
            with self.assertRaisesRegex(RuntimeError, "MTIME_DEFICIT"):
                runner.production_run(iter([entity]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}}, td / "m.sqlite")
            self.assertEqual(sc.write_calls, 0)
            base = sqlite3.connect(td / "base.sqlite")
            base.execute("CREATE TABLE entries(path TEXT, mtime_utc TEXT)")
            base.execute("INSERT INTO entries VALUES ('E:\\BLACKBOX\\a.bin','from-base')")
            base.commit()
            db = sqlite3.connect(plan)
            filled = next(reader.read_executable(db, {"base": base}))
            db.close()
            base.close()
            self.assertEqual(filled["mtime"], "from-base")
            self.assertEqual(filled["mtime_status"], "FROM_BASE_MTIME_UTC")

            sc, backend = _backend()
            sc.files[r"E:\BLACKBOX\a.bin"] = b"already"
            sc.identities[r"E:\BLACKBOX\a.bin"] = {"file_id": "x", "volume_serial": "DEST", "object_type": "file", "mtime": "t"}
            db = sqlite3.connect(plan)
            # mtime column absent; give the entity an explicit mtime so the unknown-target check is reached
            entity = next(reader.read_executable(db))
            db.close()
            entity["mtime"] = "t1"
            entity["mtime_status"] = "FROM_PLAN"
            with self.assertRaisesRegex(RuntimeError, "UNKNOWN_TARGET_EXISTS"):
                runner.production_run(iter([entity]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}}, td / "u.sqlite")

            sc, backend = _backend()
            sc.files[r"E:\BLACKBOX"] = b"file"
            sc.identities[r"E:\BLACKBOX"] = {"file_id": "f", "volume_serial": "DEST", "object_type": "file"}
            with self.assertRaisesRegex(RuntimeError, "TYPE_CONFLICT"):
                runner.production_run(iter([]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}, "directories": [r"E:\BLACKBOX"]}, td / "t.sqlite")

            sc, backend = _backend()
            sc.files[r"E:\BLACKBOX"] = b""
            sc.identities[r"E:\BLACKBOX"] = {"file_id": "j", "volume_serial": "DEST", "object_type": "junction", "reparse_target": r"E:\BLACKBOX\realdir"}
            db = sqlite3.connect(plan)
            entity = next(reader.read_executable(db))
            db.close()
            entity["mtime"] = "t1"
            entity["mtime_status"] = "FROM_PLAN"
            with self.assertRaisesRegex(RuntimeError, "REPARSE_ANCESTOR"):
                runner.production_run(iter([entity]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}}, td / "anc.sqlite")

            bad = {"link_path": r"E:\BLACKBOX\jump", "target": r"\\192.168.100.2\E_DRIVE\BLACKBOX\realdir", "kind": "junction", "blocked": True}
            sc, backend = _backend()
            before = sc.write_calls
            with self.assertRaisesRegex(RuntimeError, "BAD_LINK_TARGET"):
                runner.production_run(iter([]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}, "links": [bad]}, td / "bad.sqlite")
            self.assertEqual(sc.write_calls, before)
            cycle = [
                {"link_path": r"E:\BLACKBOX\a", "target": r"E:\BLACKBOX\b", "kind": "junction", "blocked": False},
                {"link_path": r"E:\BLACKBOX\b", "target": r"E:\BLACKBOX\a", "kind": "junction", "blocked": False},
            ]
            with self.assertRaisesRegex(RuntimeError, "REPARSE_CYCLE"):
                reader.order_links(cycle)

            blocked = runner.production_run(iter([]), winio.WindowsBackend(), {"phase": "PREPARATION_ONLY"}, td / "prep.sqlite")
            self.assertTrue(blocked["refused_before_write"])
            self.assertEqual(winio.Win32Syscalls.write_calls, 0)
            blocked = runner.production_run(iter([]), winio.WindowsBackend(), {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}}, td / "simreal.sqlite")
            self.assertTrue(blocked["refused_before_write"])
            self.assertEqual(winio.Win32Syscalls.write_calls, 0)

    def test_partial_empty_and_wrong_run(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            plan = td / "plan.sqlite"
            _plan(plan)
            r9_state.open_state(td / "empty.sqlite").close()
            empty = r9_acceptance.full_acceptance(plan, td / "empty.sqlite", _backend()[1], None)
            self.assertFalse(empty["full_acceptance"])
            db = sqlite3.connect(plan)
            entities, contract = _contract(plan, db)
            db.close()
            sc, backend = _backend()
            contract["directories"] = []
            contract["links"] = []
            runner.production_run(iter(entities[:1]), backend, contract, td / "part.sqlite")
            partial = r9_acceptance.full_acceptance(plan, td / "part.sqlite", backend, contract["run"])
            self.assertFalse(partial["full_acceptance"])
            self.assertLess(partial["checked_entities"], partial["expected_entities"])
            wrong = dict(contract["run"])
            wrong["code_digest"] = "other"
            with self.assertRaisesRegex(RuntimeError, "RUN_BINDING_MISMATCH"):
                runner.production_run(iter(entities[:1]), backend, {**contract, "run": wrong}, td / "part.sqlite")

    def test_winapi_fake_kernel_fields(self):
        class Api:
            def __init__(self, mode):
                self.mode = mode
            def GetFileAttributesW(self, path):
                if self.mode == "missing":
                    return 0xFFFFFFFF
                if self.mode == "denied":
                    return 0xFFFFFFFF
                if self.mode == "junction":
                    return 0x400 | 0x10
                return 0x80
            def last_error(self):
                return 2 if self.mode == "missing" else 5 if self.mode == "denied" else 0
            def CreateFileW(self, path, flags):
                return 7
            def close(self, handle):
                return None
            def GetFileInformationByHandle(self, handle):
                return {"file_id": 99, "volume_serial": 7, "size": 4, "mtime": "mt", "nlinks": 1}
            def GetFileInformationByHandleEx(self, handle):
                return {"allocation_size": 4096}
            def hash_handle(self, handle, size):
                return hashlib.sha256(b"data").hexdigest()
            def read_reparse(self, handle):
                return {"target": r"E:\BLACKBOX\real", "kind": "junction"}

        missing = winio.observe_via_winapi(Api("missing"), r"E:\BLACKBOX\nope")
        self.assertEqual(missing["status"], "MISSING")
        denied = winio.observe_via_winapi(Api("denied"), r"E:\BLACKBOX\nope")
        self.assertEqual(denied, {"status": "ERROR", "winerror": 5})
        present = winio.observe_via_winapi(Api("file"), r"E:\BLACKBOX\a.bin")
        self.assertEqual(present["file_id"], "99")
        self.assertEqual(present["allocation_size"], 4096)
        self.assertEqual(present["object_type"], "file")
        self.assertIsNone(present["sha256"])
        hashed = winio.observe_via_winapi(Api("file"), r"E:\BLACKBOX\a.bin", include_hash=True)
        self.assertEqual(hashed["sha256"], hashlib.sha256(b"data").hexdigest())
        junction = winio.observe_via_winapi(Api("junction"), r"E:\BLACKBOX\jump")
        self.assertEqual(junction["object_type"], "junction")
        self.assertEqual(junction["reparse_target"], r"E:\BLACKBOX\real")
        payload = winio.mount_point_buffer(r"E:\BLACKBOX\realdir")
        self.assertEqual(int.from_bytes(payload[0:4], "little"), winio.IO_REPARSE_TAG_MOUNT_POINT)
        self.assertIn("E:\\BLACKBOX\\realdir".encode("utf-16le"), payload)

        class Recorder:
            def __init__(self):
                self.payload = None
                self.symlink = None
            def CreateFileW(self, path, flags):
                return 1
            def close(self, handle):
                return None
            def DeviceIoControl(self, handle, code, blob):
                self.payload = (code, blob)
                return True
            def CreateSymbolicLinkW(self, link, target, flags):
                self.symlink = (link, target, flags)
                return True
            def list_directory_nofollow(self, root):
                return [
                    {"path": root + r"\jump", "object_type": "junction"},
                    {"path": root + r"\realdir", "object_type": "directory"},
                ]

        rec = Recorder()
        self.assertTrue(winio.apply_reparse(rec, r"E:\BLACKBOX\jump", r"E:\BLACKBOX\realdir", "junction"))
        self.assertEqual(rec.payload[0], winio.FSCTL_SET_REPARSE_POINT)
        self.assertTrue(winio.apply_reparse(rec, r"E:\BLACKBOX\s", r"E:\BLACKBOX\t", "symlink"))
        self.assertEqual(rec.symlink[1], r"E:\BLACKBOX\t")
        listed = winio.enumerate_nofollow(rec, r"E:\BLACKBOX")
        self.assertEqual([item["object_type"] for item in listed], ["junction", "directory"])
        self.assertTrue(any("DeviceIoControl" in text or "create_reparse" in text for text in dir(winio.Win32Syscalls)))

    def test_source_mtime_is_checked_after_the_copy_read(self):
        class Flip(winio.VirtualSyscalls):
            def identity(self, handle):
                meta = super().identity(handle)
                self.seen = getattr(self, "seen", 0) + 1
                if self.seen >= 2:
                    meta = dict(meta)
                    meta["mtime"] = "changed"
                return meta

        source = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\a.bin"
        sc = Flip(files={source: b"hello"}, identities={source: {"file_id": "11", "volume_serial": "2387166462", "mtime": "t1"}})
        backend = winio.WindowsBackend(sc)
        entity = {
            "entity_key": "2387166462|11",
            "volume_serial": "2387166462",
            "file_id": "11",
            "logical_size": 5,
            "mtime": "t1",
            "mtime_status": "FROM_PLAN",
            "source_path": source,
            "dest_path": r"E:\BLACKBOX\a.bin",
            "extra_dest_paths": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(RuntimeError, "SOURCE_CHANGED_DURING_COPY"):
                runner.production_run(iter([entity]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}}, Path(raw) / "state.sqlite")

    def test_accept_simulated_cli_does_not_touch_disk(self):
        self.assertEqual(r9_formal_executor.main(["accept-simulated"]), 3)


if __name__ == "__main__":
    unittest.main()
