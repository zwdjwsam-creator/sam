# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import r9_bounded_pilot as pilot
import r9_runner as runner
import r9_winio as winio

SAMPLE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json")
CONTRACT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json")


class BoundedPilotTests(unittest.TestCase):
    def test_sample_limits_and_flat_destinations(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        pilot.validate_sample(sample)
        self.assertEqual(sample["entities"][0]["logical_size"], 6849)
        self.assertEqual(len(sample["entities"][0]["paths"]), 39)
        self.assertEqual(sample["entities"][1]["logical_size"], 2463)

    def test_public_execute_copies_two_and_second_run_does_not_rewrite(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        entities = pilot.entities_for_run(sample)
        files = {}
        identities = {}
        for entity in entities:
            files[entity["source_path"]] = b"x" * int(entity["logical_size"])
            identities[entity["source_path"]] = {
                "file_id": entity["file_id"],
                "volume_serial": entity["volume_serial"],
                "mtime": entity["mtime"],
            }
        sc = winio.VirtualSyscalls(files=files, identities=identities, dest_volume="D86AEE82")
        backend = winio.WindowsBackend(sc)
        import r9_source_contract as source
        authorized = {
            "pilot_write_authorized": True,
            "copy_authorized": False,
            "full_migration": False,
            "disk_unique_id": pilot.DISK_ID,
            "volume_serial_hex": pilot.VOLUME_HEX,
            "dest_root": pilot.DEST_ROOT,
            "plan_sha256": pilot.PLAN_SHA,
            "sample_sha256": pilot.sample_sha256(SAMPLE),
            "code_digest": source.code_digest(),
            "scope": "BOUNDED_PILOT_ONLY",
        }
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            contract = td / "contract.json"
            contract.write_text(json.dumps(authorized), encoding="utf-8")
            state = td / "state.sqlite"
            self.assertEqual(pilot.execute(SAMPLE, contract, backend=backend, live_probe=lambda: {"ok": True}, state_path=state), 0)
            rep = backend.observe_destination(entities[0]["dest_path"])
            alias = sample["entities"][0]["paths"][1]["dest_path"]
            self.assertEqual(backend.observe_destination(alias)["file_id"], rep["file_id"])
            self.assertEqual(rep["volume_serial"], "D86AEE82")
            writes = sc.write_calls
            again = pilot.execute(SAMPLE, contract, backend=backend, live_probe=lambda: {"ok": True}, state_path=state)
            self.assertEqual(again, 0)
            self.assertEqual(sc.write_calls, writes)

    def test_dry_run_and_unauthorized_execute_do_not_write(self):
        before = winio.Win32Syscalls.write_calls
        self.assertEqual(pilot.dry_run(SAMPLE, CONTRACT), 0)
        self.assertEqual(pilot.execute(SAMPLE, CONTRACT), 3)
        self.assertEqual(winio.Win32Syscalls.write_calls, before)

    def test_entry_refusals_happen_before_write(self):
        import r9_source_contract as source
        base = {
            "pilot_write_authorized": True,
            "copy_authorized": False,
            "full_migration": False,
            "disk_unique_id": pilot.DISK_ID,
            "volume_serial_hex": pilot.VOLUME_HEX,
            "dest_root": pilot.DEST_ROOT,
            "plan_sha256": pilot.PLAN_SHA,
            "sample_sha256": pilot.sample_sha256(SAMPLE),
            "code_digest": source.code_digest(),
        }
        sc = winio.VirtualSyscalls(dest_volume="D86AEE82")
        backend = winio.WindowsBackend(sc)
        cases = {
            "volume": {**base, "volume_serial_hex": "806508DF"},
            "disk": {**base, "disk_unique_id": "other"},
            "code": {**base, "code_digest": "stale"},
            "sample": {**base, "sample_sha256": "0" * 64},
        }
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            for name, payload in cases.items():
                path = td / f"{name}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                before = sc.write_calls
                self.assertEqual(pilot.execute(SAMPLE, path, backend=backend, live_probe=lambda: {"ok": True}, state_path=td / f"{name}.sqlite"), 3, name)
                self.assertEqual(sc.write_calls, before, name)
            good = td / "good.json"
            good.write_text(json.dumps(base), encoding="utf-8")
            before = sc.write_calls
            self.assertEqual(pilot.execute(SAMPLE, good, backend=backend, live_probe=lambda: {"ok": False, "reason": "REPARSE_ANCESTOR"}, state_path=td / "reparse.sqlite"), 3)
            self.assertEqual(sc.write_calls, before)
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        sample["entities"][0]["logical_size"] = 1
        with self.assertRaises(RuntimeError):
            pilot.validate_sample(sample)
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        sample["entities"][0]["paths"][0]["dest_path"] = r"E:\BLACKBOX\not-pilot"
        with self.assertRaises(RuntimeError):
            pilot.validate_sample(sample)


if __name__ == "__main__":
    unittest.main()
