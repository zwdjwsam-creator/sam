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

    def test_simulated_chain_copies_two_and_links_thirty_eight(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        mtimes = {entity["entity_key"]: "src-mtime" for entity in sample["entities"]}
        entities = pilot.entities_for_run(sample, mtimes)
        files = {}
        identities = {}
        for entity in entities:
            payload = b"x" * int(entity["logical_size"])
            files[entity["source_path"]] = payload
            identities[entity["source_path"]] = {
                "file_id": entity["file_id"],
                "volume_serial": entity["volume_serial"],
                "mtime": "src-mtime",
            }
        sc = winio.VirtualSyscalls(files=files, identities=identities)
        backend = winio.WindowsBackend(sc)
        contract = {
            "phase": "SIMULATED_CHAIN",
            "dest_binding": {"volume_serial": "DEST"},
            "directories": sample["directories"],
            "links": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "state.sqlite"
            result = runner.production_run(iter(entities), backend, contract, state)
            self.assertEqual(result["copied_count"], 2)
            self.assertEqual(result["linked_count"], 38)
            writes = sc.write_calls
            again = runner.production_run(iter(entities), backend, contract, state)
            self.assertEqual(sc.write_calls, writes)
            self.assertEqual(again["skipped_entities"], 2)
            self.assertEqual(again["skipped_links"], 38)

    def test_dry_run_and_unauthorized_execute_do_not_write(self):
        before = winio.Win32Syscalls.write_calls
        self.assertEqual(pilot.dry_run(SAMPLE, CONTRACT), 0)
        self.assertEqual(pilot.execute(SAMPLE, CONTRACT), 3)
        self.assertEqual(winio.Win32Syscalls.write_calls, before)

    def test_changed_sample_is_rejected(self):
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
