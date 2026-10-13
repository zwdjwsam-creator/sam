# -*- coding: utf-8 -*-
import unittest
import r9_scheduler as sched
import r9_winio as winio


class SchedulerTests(unittest.TestCase):
    def test_preparation_gate_calls_backend_zero_times(self):
        backend = sched.FakeBackend()
        entities = iter([{"entity_key": "a", "representative": r"E:\BLACKBOX\a", "volume_serial": "1", "extra_paths": [r"E:\BLACKBOX\b"]}])
        result = sched.run_batch(entities, backend, sched.PreparationGate(), {"phase": "PREPARATION_ONLY", "copy_authorized": True, "format_done": True})
        self.assertTrue(result["refused_before_write"])
        self.assertEqual(backend.calls, 0)

    def test_two_bools_do_not_open_the_gate(self):
        gate = sched.PreparationGate()
        self.assertFalse(gate.allows_write({"copy_authorized": True, "format_done": True}))

    def test_same_content_different_volume_copies_twice(self):
        backend = sched.FakeBackend()
        entities = [
            {"entity_key": "v1|1", "representative": r"E:\BLACKBOX\a", "volume_serial": "v1", "extra_paths": []},
            {"entity_key": "v2|1", "representative": r"E:\BLACKBOX_ENGINES\a", "volume_serial": "v2", "extra_paths": []},
        ]
        contract = {"phase": "WRITE_AUTHORIZED", "format_confirmed": True, "dest_binding_id": "future"}
        result = sched.run_batch(iter(entities), backend, sched.PreparationGate(), contract)
        self.assertEqual(result["copied"], 2)
        self.assertEqual(backend.copies, ["v1|1", "v2|1"])

    def test_one_entity_many_paths_copies_once(self):
        backend = sched.FakeBackend()
        entities = [{"entity_key": "v|9", "representative": r"E:\BLACKBOX\a", "volume_serial": "v", "extra_paths": [r"E:\BLACKBOX\b", r"E:\BLACKBOX\c"]}]
        contract = {"phase": "WRITE_AUTHORIZED", "format_confirmed": True, "dest_binding_id": "future"}
        sched.run_batch(iter(entities), backend, sched.PreparationGate(), contract)
        self.assertEqual(backend.copies, ["v|9"])
        self.assertEqual(len(backend.links), 2)

    def test_ancestor_remainder_cycle(self):
        import r9_adapter as adapter
        edges = [(r"E:\A", r"E:\B"), (r"E:\B\child", r"E:\A\child")]
        self.assertTrue(adapter.walk_reparse(r"E:\B\child", edges))
        self.assertFalse(adapter.walk_reparse(r"E:\ONLY", [(r"E:\ONLY", r"E:\OTHER")]))

    def test_chain_reader_runner_backend(self):
        import sqlite3, tempfile, hashlib
        from pathlib import Path
        import r9_winio as winio
        import r9_runner as runner
        payload = b"hello-entity"
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            db = sqlite3.connect(td / "plan.sqlite")
            db.executescript(
                """
                CREATE TABLE entities(volume_serial TEXT, file_id TEXT, min_size INTEGER, path_count INTEGER, mtime TEXT);
                CREATE TABLE paths(path TEXT, is_dir INTEGER, is_reparse INTEGER, volume_serial TEXT, file_id TEXT);
                INSERT INTO entities VALUES ('2387166462','11',12,2,'t1');
                INSERT INTO paths VALUES ('E:\\BLACKBOX\\a.bin',0,0,'2387166462','11');
                INSERT INTO paths VALUES ('E:\\BLACKBOX\\z-link.bin',0,0,'2387166462','11');
                """
            )
            db.commit()
            import r9_plan_reader as reader
            entity = next(reader.read_executable(db))
            db.close()
            sc = winio.VirtualSyscalls(
                files={entity["source_path"]: payload},
                identities={entity["source_path"]: {"file_id": "11", "volume_serial": "2387166462", "mtime": "t1"}},
            )
            self.assertTrue(entity["source_path"].startswith("\\\\192.168.100.2\\"))
            self.assertEqual(entity["dest_path"], r"E:\BLACKBOX\a.bin")
            backend = winio.WindowsBackend(sc)
            result = runner.production_run(
                iter([entity]),
                backend,
                {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}},
                td / "state.sqlite",
            )
            self.assertFalse(result["refused_before_write"])
            self.assertEqual(result["copied"][0]["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(result["copied"][0]["bytes"], 12)
            self.assertNotEqual(result["copied"][0]["dest_file_id"], "11")
            self.assertEqual(result["linked"][0]["dest_path"], r"E:\BLACKBOX\z-link.bin")
            self.assertEqual(result["linked"][0]["dest_file_id"], result["copied"][0]["dest_file_id"])
            self.assertEqual(backend.observe_destination(r"E:\BLACKBOX\z-link.bin")["status"], "PRESENT")
            self.assertEqual(backend.observe_destination(r"E:\BLACKBOX\missing.bin")["status"], "MISSING")
            writes = sc.write_calls
            again = runner.production_run(iter([entity]), backend, {"phase": "SIMULATED_CHAIN", "dest_binding": {"volume_serial": "DEST"}}, td / "state.sqlite")
            self.assertEqual(sc.write_calls, writes)
            self.assertTrue(again["linked"][0].get("skipped"))
            blocked = runner.production_run(iter([entity]), winio.WindowsBackend(), {"phase": "PREPARATION_ONLY", "copy_authorized": True, "format_done": True}, td / "state2.sqlite")
            self.assertTrue(blocked["refused_before_write"])
            self.assertEqual(winio.Win32Syscalls.write_calls, 0)

    def test_windows_declarations_are_present_without_io(self):
        info = winio.declarations_ready()
        self.assertTrue(info["ready"])
        self.assertEqual(info["pilot_common_sha256"], winio.PILOT_COMMON_SHA256)


if __name__ == "__main__":
    unittest.main()
