# -*- coding: utf-8 -*-
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_acceptance
import r9_plan_reader as reader
import r9_runner as runner
import r9_winio as winio
import test_r9_close as close

FT = "134363232000000000"
ISO_Z = "2026-10-13T00:00:00Z"
ISO_OFFSET = "2026-10-13T00:00:00+00:00"
ISO_PLUS8 = "2026-10-13T08:00:00+08:00"


def _fresh():
    raw = tempfile.mkdtemp()
    td = Path(raw)
    plan = td / "plan.sqlite"
    close._plan(plan)
    db = sqlite3.connect(plan)
    entities, contract = close._contract(plan, db)
    db.close()
    sc, backend = close._backend()
    state = td / "state.sqlite"
    result = runner.production_run(iter(entities), backend, contract, state)
    return td, plan, sc, backend, contract, state, result


class StrictAcceptanceTests(unittest.TestCase):
    def test_clean_acceptance_hashes_each_entity_once(self):
        td, plan, sc, backend, contract, state, result = _fresh()
        contract["accept"] = True
        contract["plan_path"] = str(plan)
        result = runner.production_run(iter([]), backend, contract, state)
        self.assertTrue(result["acceptance"]["full_acceptance"])
        self.assertEqual(result["acceptance"]["content_hash_calls"], 2)
        self.assertEqual(sc.hash_calls, 2)

    def test_missing_fields_orphan_and_substitutes_fail(self):
        td, plan, sc, backend, contract, state, _ = _fresh()
        run = contract["run"]

        def accept():
            return r9_acceptance.full_acceptance(plan, state, backend, run)

        for path in (r"E:\BLACKBOX\a.bin", r"E:\BLACKBOX\z-link.bin"):
            sc.identities[path]["file_id"] = None
            sc.identities[path]["volume_serial"] = None
        report = accept()
        self.assertFalse(report["full_acceptance"])
        self.assertIn("MISSING_FIELD", report["reasons"])
        for path in (r"E:\BLACKBOX\a.bin", r"E:\BLACKBOX\z-link.bin"):
            sc.identities[path]["file_id"] = backend.observe_destination(r"E:\BLACKBOX\realdir")["file_id"]

        td, plan, sc, backend, contract, state, _ = _fresh()
        run = contract["run"]
        sc.identities[r"E:\BLACKBOX\realdir"]["object_type"] = None
        report = r9_acceptance.full_acceptance(plan, state, backend, run)
        self.assertFalse(report["full_acceptance"])
        self.assertIn("MISSING_FIELD", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        run = contract["run"]
        sc.identities[r"E:\BLACKBOX\jump"]["reparse_target"] = None
        report = r9_acceptance.full_acceptance(plan, state, backend, run)
        self.assertFalse(report["full_acceptance"])
        self.assertIn("MISSING_FIELD", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        db = sqlite3.connect(plan)
        db.execute("INSERT INTO entities VALUES ('X','orphan',99,1,'t1')")
        db.commit()
        db.close()
        report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
        self.assertFalse(report["full_acceptance"])
        self.assertIn("PLAN_ORPHAN_ENTITY", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        original = sc.identities[r"E:\BLACKBOX\a.bin"]["file_id"]
        for path in (r"E:\BLACKBOX\a.bin", r"E:\BLACKBOX\z-link.bin"):
            sc.identities[path]["file_id"] = "swapped"
        report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
        self.assertFalse(report["full_acceptance"])
        self.assertIn("IDENTITY_MISMATCH", report["reasons"])
        self.assertNotEqual("swapped", original)

        td, plan, sc, backend, contract, state, _ = _fresh()
        for ident in sc.identities.values():
            if ident.get("volume_serial") == "DEST":
                ident["volume_serial"] = "OTHER"
        report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
        self.assertFalse(report["full_acceptance"])
        self.assertIn("DEST_VOLUME", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        report = r9_acceptance.full_acceptance(plan, state, backend, None)
        self.assertFalse(report["full_acceptance"])
        self.assertIn("RUN_BINDING_MISSING", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        sc.identities[r"E:\BLACKBOX\a.bin"]["allocation_size"] = None
        sc.identities[r"E:\BLACKBOX\z-link.bin"]["allocation_size"] = None
        report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
        self.assertFalse(report["full_acceptance"])
        self.assertIn("MISSING_FIELD", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        db = sqlite3.connect(plan)
        db.execute("UPDATE entities SET path_count=9 WHERE file_id='11' AND volume_serial='2387166462'")
        db.commit()
        db.close()
        report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
        self.assertFalse(report["full_acceptance"])
        self.assertIn("PATH_COUNT", report["reasons"])

        td, plan, sc, backend, contract, state, _ = _fresh()
        db = sqlite3.connect(state)
        db.execute("DELETE FROM stage WHERE parent_key='3187598165|11'")
        db.execute(
            """
            INSERT INTO stage(item_key, kind, phase, dest_path, sha256, file_id, volume_serial, object_type, link_target, logical_size, parent_key)
            VALUES ('entity:fake|1','entity','DONE',?, 'abc','fake','DEST','file',NULL,1,'fake|1')
            """,
            (r"E:\BLACKBOX_ENGINES\engine.bin",),
        )
        db.commit()
        db.close()
        report = r9_acceptance.full_acceptance(plan, state, backend, contract["run"])
        self.assertFalse(report["full_acceptance"])
        self.assertIn("EXTRA_DONE", report["reasons"])
        self.assertIn("MISSING_ENTITY", report["reasons"])


class MetadataAndWrapperTests(unittest.TestCase):
    def test_filetime_matches_iso_forms_and_drift_fails(self):
        for manifest in (ISO_Z, ISO_OFFSET, ISO_PLUS8):
            winio.assert_manifest_mtime(manifest, {"mtime_ft": FT})
        with self.assertRaises(RuntimeError):
            winio.assert_manifest_mtime("2026-10-13T00:00:01Z", {"mtime_ft": FT})
        with self.assertRaises(RuntimeError):
            winio.assert_manifest_mtime(ISO_Z, {})
        with self.assertRaises(RuntimeError):
            winio.mtime_evidence({})
        source = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\a.bin"
        sc = winio.VirtualSyscalls(
            files={source: b"hello"},
            identities={source: {"file_id": "11", "volume_serial": "2387166462", "mtime_ft": FT}},
        )
        entity = {
            "entity_key": "2387166462|11",
            "volume_serial": "2387166462",
            "file_id": "11",
            "logical_size": 5,
            "mtime": ISO_OFFSET,
            "mtime_status": "FROM_BASE_MTIME_UTC",
            "source_path": source,
            "dest_path": r"E:\BLACKBOX\a.bin",
            "extra_dest_paths": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            result = runner.production_run(
                iter([entity]),
                winio.WindowsBackend(sc),
                {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}},
                Path(raw) / "state.sqlite",
            )
        self.assertEqual(result["copied_count"], 1)

    def test_real_kernel_wrapper_records_native_arguments(self):
        class Native:
            def __init__(self):
                self.calls = []
                self.err = 0
                self.get_buffer = None

            def get_last_error(self):
                return self.err

            def CreateDirectoryW(self, path, security):
                self.calls.append(("CreateDirectoryW", path))
                return 1

            def GetFileAttributesW(self, path):
                return 0x10

            def CreateFileW(self, path, access, share, security, disposition, flags, template):
                self.calls.append(("CreateFileW", int(access), int(disposition), int(flags)))
                return 77

            def DeviceIoControl(self, handle, code, payload, in_len, outbuf, out_len, returned, overlapped):
                blob = bytes(payload) if payload else None
                self.calls.append(("DeviceIoControl", int(handle), int(code), blob))
                if outbuf is not None and self.get_buffer is not None:
                    raw = self.get_buffer
                    winio.common.ctypes.memmove(outbuf, raw, len(raw))
                    returned.value = len(raw)
                return 1

            def CloseHandle(self, handle):
                self.calls.append(("CloseHandle", int(handle)))
                return 1

            def CreateSymbolicLinkW(self, link, target, flags):
                self.calls.append(("CreateSymbolicLinkW", target, int(flags)))
                return 1

        native = Native()
        kernel = winio._RealKernel(native)
        self.assertTrue(kernel.create_junction(r"E:\BLACKBOX\jump", r"E:\BLACKBOX\realdir"))
        created = [item for item in native.calls if item[0] == "CreateFileW"][0]
        self.assertEqual(created[1], int(winio.common.GENERIC_WRITE))
        self.assertEqual(created[2], int(winio.common.OPEN_EXISTING))
        self.assertTrue(created[3] & winio.common.FILE_FLAG_OPEN_REPARSE_POINT)
        ioctl = [item for item in native.calls if item[0] == "DeviceIoControl"][0]
        self.assertEqual(ioctl[1], 77)
        self.assertEqual(ioctl[2], winio.FSCTL_SET_REPARSE_POINT)
        self.assertIn("E:\\BLACKBOX\\realdir".encode("utf-16le"), ioctl[3])
        self.assertIn(("CloseHandle", 77), native.calls)

        native.get_buffer = winio.symlink_buffer(r"rel\target", relative=True)
        parsed = kernel.read_reparse(77)
        self.assertEqual(parsed["kind"], "symlink")
        self.assertTrue(parsed["relative"])
        self.assertEqual(parsed["target"], r"rel\target")
        native.get_buffer = b"\x00\x00\x00\x00\x00\x00\x00\x00"
        with self.assertRaises(RuntimeError):
            kernel.read_reparse(77)
        self.assertTrue(kernel.create_directory_symlink(r"E:\BLACKBOX\s", r"rel\target", relative=True))
        self.assertEqual(native.calls[-1][0], "CreateSymbolicLinkW")
        self.assertEqual(native.calls[-1][2], winio.SYMBOLIC_LINK_FLAG_DIRECTORY)
        self.assertEqual(winio.classify_find_next(False, 18), "end")
        with self.assertRaises(OSError):
            winio.classify_find_next(False, 5)
        self.assertIsNotNone(winio.common.kernel32.DeviceIoControl.argtypes)
        self.assertIsNotNone(winio.common.kernel32.MoveFileW.argtypes)
        self.assertIsNotNone(winio.common.kernel32.CreateSymbolicLinkW.argtypes)
        self.assertIsNot(winio.common.kernel32.CreateFileW.restype, winio.common.ctypes.c_int)


if __name__ == "__main__":
    unittest.main()
