# -*- coding: utf-8 -*-
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_capability_pilot as cap
import r9_pilot_common_r9fix as common
import r9_source_contract as source
import r9_winio as winio
from test_r9_bounded_pilot import RecordingStore

SAMPLE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json")


class JunctionKernel:
    def __init__(self):
        self.dirs = []
        self.opens = []
        self.controls = []
        self.buffers = {}

    def _key(self, path: str) -> str:
        text = str(path)
        if text.startswith("\\\\?\\UNC\\"):
            return "\\\\" + text[8:]
        if text.startswith("\\\\?\\"):
            return text[4:]
        return text

    def CreateDirectoryW(self, path, security):
        self.dirs.append(path)
        return True

    def CreateFileW(self, path, *args):
        if len(args) == 1:
            self.opens.append((path, None, None, int(args[0])))
        else:
            access, _share, _sec, disp, flags, _template = args
            self.opens.append((path, int(access), int(disp), int(flags)))
        return 7

    def CloseHandle(self, handle):
        return True

    def close(self, handle):
        return None

    def get_last_error(self):
        return 2

    def last_error(self):
        return 2

    def GetFileAttributesW(self, path):
        if self._key(path) in self.buffers:
            return common.FILE_ATTRIBUTE_REPARSE_POINT | common.FILE_ATTRIBUTE_DIRECTORY
        return 0xFFFFFFFF

    def GetFileInformationByHandle(self, handle):
        return {"file_id": 50, "volume_serial": cap.VOLUME_DWORD, "size": 0, "mtime": "1", "nlinks": 1}

    def GetFileInformationByHandleEx(self, handle):
        return {"allocation_size": 0}

    def read_reparse(self, handle):
        return winio.parse_reparse_buffer(self.buffers[self._key(self.opens[-1][0])])

    def DeviceIoControl(self, handle, code, payload, in_len, outbuf, out_len, returned, overlapped):
        data = bytes(payload) if payload else b""
        self.controls.append((int(code), data))
        if data:
            self.buffers[self._key(self.opens[-1][0])] = data
        return True


class Probe:
    def __init__(self, serial=cap.VOLUME_DWORD, disk=cap.DISK_ID, junction=False, unknown=False):
        self.serial = serial
        self.disk = disk
        self.filesystem = "NTFS"
        self.junction = junction
        self.unknown = unknown

    def observe_nofollow(self, path):
        if self.unknown:
            return {"status": "ERROR", "winerror": 5}
        if self.junction:
            return {"status": "PRESENT", "object_type": "junction", "reparse_target": r"E:\other"}
        return {"status": "MISSING"}


def _contract(sample_path: Path, authorized=True):
    scenarios = {}
    for name in cap.SCENARIOS:
        scenarios[name] = {
            "dest_root": cap.root_for(name),
            "run_id": "R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014_1242_" + name,
            "state_path": r"C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\state\\" + name + ".sqlite",
        }
    return {
        "pilot_write_authorized": authorized,
        "copy_authorized": False,
        "full_migration": False,
        "scope": "CAPABILITY_PILOT_ONLY",
        "disk_unique_id": cap.DISK_ID,
        "volume_serial_hex": cap.VOLUME_HEX,
        "plan_sha256": cap.PLAN_SHA,
        "sample_sha256": cap.sample_sha256(sample_path),
        "code_digest": source.code_digest(),
        "scenarios": scenarios,
    }


def _backend(sample):
    plan = cap.scenario_plan(sample, "NORMAL")
    store = RecordingStore()
    for entity in plan["entities"]:
        store.add_source(entity["source_path"], b"x" * int(entity["logical_size"]), entity["file_id"], entity["volume_serial"], "7001")
    kernel = JunctionKernel()
    return plan, store, kernel, winio.WindowsBackend(winio.Win32Syscalls(api=store, kernel=kernel))


class CapabilityPilotTests(unittest.TestCase):
    def test_junction_creation_uses_real_win32_sequence_and_extended_path(self):
        kernel = JunctionKernel()
        long_path = "E:\\" + ("dir\\" * 70) + "link"
        self.assertGreater(len(long_path), 260)
        self.assertTrue(winio._RealKernel(kernel).create_junction(long_path, r"E:\R9_CAPABILITY_PILOT_20261014\NORMAL\e\target"))
        self.assertTrue(kernel.dirs[0].startswith("\\\\?\\"))
        access, disp, flags = kernel.opens[-1][1:]
        self.assertEqual(access, int(common.GENERIC_WRITE))
        self.assertEqual(disp, int(common.OPEN_EXISTING))
        self.assertTrue(flags & int(common.FILE_FLAG_OPEN_REPARSE_POINT))
        self.assertEqual(kernel.controls[-1][0], winio.FSCTL_SET_REPARSE_POINT)
        parsed = winio.observe_via_winapi(kernel, kernel.dirs[0])
        self.assertEqual(parsed["object_type"], "junction")
        self.assertEqual(parsed["reparse_target"], r"E:\R9_CAPABILITY_PILOT_20261014\NORMAL\e\target")

    def test_normal_scenario_copies_links_and_rerun_does_not_rewrite(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        cap.validate_sample(sample)
        plan, store, kernel, backend = _backend(sample)
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            contract = td / "contract.json"
            contract.write_text(json.dumps(_contract(SAMPLE)), encoding="utf-8")
            state = td / "normal.sqlite"
            self.assertEqual(cap.execute(SAMPLE, contract, "NORMAL", backend=backend, os_api=Probe(), state_path=state), 0)
            self.assertEqual(len(kernel.controls), 2)
            self.assertEqual(backend.observe_destination(plan["links"][0]["link_path"])["object_type"], "junction")
            self.assertEqual(backend.observe_destination(plan["links"][0]["link_path"])["reparse_target"], plan["links"][0]["target"])
            writes = store.source_opens
            controls = len(kernel.controls)
            self.assertEqual(cap.execute(SAMPLE, contract, "NORMAL", backend=backend, os_api=Probe(), state_path=state), 0)
            self.assertEqual(len(kernel.controls), controls)
            self.assertGreater(writes, 0)

    def test_interrupt_a_persists_identity_before_resume(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        plan, _store, _kernel, backend = _backend(sample)
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            contract = td / "contract.json"
            contract.write_text(json.dumps(_contract(SAMPLE)), encoding="utf-8")
            state = td / "a.sqlite"
            self.assertEqual(cap.execute(SAMPLE, contract, "A", backend=backend, os_api=Probe(), state_path=state, fault="A"), 3)
            db = sqlite3.connect(state)
            row = db.execute(
                "SELECT phase, file_id, volume_serial, sha256 FROM stage WHERE item_key=?",
                ("entity:" + plan["entities"][0]["entity_key"],),
            ).fetchone()
            db.close()
            self.assertEqual(row[0], "INTENT")
            self.assertTrue(row[1] and row[2] and row[3])
            self.assertEqual(cap.execute(SAMPLE, contract, "A", backend=backend, os_api=Probe(), state_path=state), 0)
            db = sqlite3.connect(state)
            done = db.execute(
                "SELECT phase FROM stage WHERE item_key=?",
                ("entity:" + plan["entities"][0]["entity_key"],),
            ).fetchone()
            db.close()
            self.assertEqual(done[0], "DONE")

    def test_b_and_c_resume_only_missing_alias_work(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        for fault, scenario in (("B", "B"), ("C", "C")):
            plan = cap.scenario_plan(sample, scenario)
            alias_keys = ["alias:" + path for path in plan["entities"][2]["extra_dest_paths"]]
            _plan, _store, kernel, backend = _backend(sample)
            with tempfile.TemporaryDirectory() as raw:
                td = Path(raw)
                contract = td / "contract.json"
                contract.write_text(json.dumps(_contract(SAMPLE)), encoding="utf-8")
                state = td / "state.sqlite"
                self.assertEqual(cap.execute(SAMPLE, contract, scenario, backend=backend, os_api=Probe(), state_path=state, fault=fault), 3, fault)
                db = sqlite3.connect(state)
                phases = [db.execute("SELECT phase FROM stage WHERE item_key=?", (key,)).fetchone() for key in alias_keys]
                db.close()
                self.assertEqual(phases[0][0], "DONE" if fault == "B" else "INTENT", fault)
                self.assertIsNone(phases[1], fault)
                self.assertEqual(cap.execute(SAMPLE, contract, scenario, backend=backend, os_api=Probe(), state_path=state), 0, fault)
                db = sqlite3.connect(state)
                done = [db.execute("SELECT phase FROM stage WHERE item_key=?", (key,)).fetchone()[0] for key in alias_keys]
                db.close()
                self.assertEqual(done, ["DONE", "DONE"], fault)
                self.assertEqual(len(kernel.controls), 2, fault)

    def test_refusals_and_false_contract_do_not_write(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        _plan, store, kernel, backend = _backend(sample)
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            good = td / "good.json"
            good.write_text(json.dumps(_contract(SAMPLE)), encoding="utf-8")
            blocked = td / "blocked.json"
            blocked.write_text(json.dumps(_contract(SAMPLE, authorized=False)), encoding="utf-8")
            before = winio.Win32Syscalls.write_calls
            self.assertEqual(cap.dry_run(SAMPLE, blocked, "NORMAL"), 0)
            self.assertEqual(cap.execute(SAMPLE, blocked, "NORMAL", backend=backend, os_api=Probe(), state_path=td / "no.sqlite"), 3)
            self.assertEqual(cap.execute(SAMPLE, good, "NORMAL", backend=backend, os_api=Probe(disk="eui.OTHER"), state_path=td / "disk.sqlite"), 3)
            self.assertEqual(cap.execute(SAMPLE, good, "NORMAL", backend=backend, os_api=Probe(disk=None), state_path=td / "unknown.sqlite"), 3)
            self.assertEqual(cap.execute(SAMPLE, good, "NORMAL", backend=backend, os_api=Probe(junction=True), state_path=td / "re.sqlite"), 3)
            self.assertEqual(kernel.controls, [])
            self.assertEqual(winio.Win32Syscalls.write_calls, before)
            self.assertFalse(Path(cap.root_for("NORMAL")).exists())

    def test_bad_link_target_is_rejected(self):
        import r9_plan_reader as reader
        with self.assertRaisesRegex(RuntimeError, "BAD_LINK_TARGET"):
            reader.order_links([{
                "link_path": r"E:\R9_CAPABILITY_PILOT_20261014\NORMAL\e_manifest",
                "target": r"\\192.168.100.2\E_DRIVE\BLACKBOX\data",
                "kind": "junction",
                "blocked": False,
            }])


if __name__ == "__main__":
    unittest.main()
