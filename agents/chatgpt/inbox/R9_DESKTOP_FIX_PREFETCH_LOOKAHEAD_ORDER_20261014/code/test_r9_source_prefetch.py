# -*- coding: utf-8 -*-
import tempfile
import threading
import time
import unittest
from pathlib import Path

import r9_runner
import r9_winio as winio

PARENT = r"E:\R9_FORMAL_PREFETCH_BENCH_20261014\BLACKBOX"
PAYLOAD = b"prefetch-bytes"


def _entity(index, payload=PAYLOAD, extra=None):
    return {
        "entity_key": f"2387166462|{index}",
        "source_path": f"SRC\\{index}",
        "dest_path": PARENT + f"\\{index}",
        "file_id": str(index),
        "volume_serial": "2387166462",
        "logical_size": len(payload),
        "mtime": "T1",
        "mtime_status": "FROM_PLAN",
        "extra_dest_paths": list(extra or []),
    }


def _load(sc, indexes, payload=PAYLOAD):
    for index in indexes:
        path = f"SRC\\{index}"
        sc.files[path] = payload
        sc.identities[path] = {
            "file_id": str(index),
            "volume_serial": "2387166462",
            "mtime": "T1",
            "object_type": "file",
        }


def _contract(workers, fault=None):
    payload = {
        "phase": "SIMULATED_CHAIN",
        "dest_binding": {"volume_serial": "DEST"},
        "source_prefetch_workers": workers,
        "directories": [],
        "links": [],
        "accept": False,
    }
    if fault:
        payload["fault"] = fault
    return payload


class Tracking(winio.VirtualSyscalls):
    def __init__(self):
        super().__init__(dest_volume="DEST")
        self.opened = 0
        self.closed = 0
        self.live = 0
        self.peak = 0
        self.lock = threading.Lock()
        self.pulls = 0
        self.source_handles = set()

    def open_source(self, path):
        if str(path).endswith("\\0"):
            time.sleep(0.15)
            if self.pulls > 4:
                raise RuntimeError("LOOKAHEAD")
        handle = super().open_source(path)
        if str(path).endswith(".partial"):
            return handle
        with self.lock:
            self.source_handles.add(handle)
            self.opened += 1
            self.live += 1
            self.peak = max(self.peak, self.live)
        return handle

    def close(self, handle):
        with self.lock:
            tracked = handle in self.source_handles
            if tracked:
                self.source_handles.discard(handle)
                self.closed += 1
                self.live -= 1
        super().close(handle)


class PrefetchTests(unittest.TestCase):
    def test_out_of_order_completion_stays_in_plan_order_and_bounds_handles(self):
        sc = Tracking()
        _load(sc, range(6))
        pulls = {"n": 0}

        def generate():
            for index in range(6):
                pulls["n"] += 1
                sc.pulls = pulls["n"]
                yield _entity(index)

        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            result = r9_runner.production_run(generate(), backend, _contract(4), Path(raw) / "state.sqlite")
        self.assertEqual(result["copied_count"], 6)
        self.assertLessEqual(result["source_prefetch_handle_peak"], 4)
        self.assertLessEqual(sc.peak, 4)
        self.assertEqual(sc.opened, sc.closed)
        self.assertEqual(sc.live, 0)
        self.assertIn("not wall-clock", result["prefetch_timing_note"])
        for index in range(6):
            self.assertEqual(bytes(sc.files[PARENT + f"\\{index}"]), PAYLOAD)

    def test_identity_failure_does_not_replace_the_entity_or_leak(self):
        class Bad(Tracking):
            def identity(self, handle):
                ident = super().identity(handle)
                if str(self.handles[handle]["path"]).endswith("\\1"):
                    ident = dict(ident)
                    ident["file_id"] = "other"
                return ident

        sc = Bad()
        _load(sc, range(3))
        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(RuntimeError, "SOURCE_CHANGED"):
                r9_runner.production_run((_entity(i) for i in range(3)), backend, _contract(4), Path(raw) / "state.sqlite")
        self.assertEqual(bytes(sc.files[PARENT + r"\0"]), PAYLOAD)
        self.assertNotIn(PARENT + r"\2", sc.files)
        self.assertEqual(sc.opened, sc.closed)
        self.assertEqual(sc.live, 0)

    def test_interrupt_a_closes_prefetched_handles(self):
        sc = Tracking()
        _load(sc, range(3))
        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(RuntimeError, "INTERRUPT_A"):
                r9_runner.production_run((_entity(i) for i in range(3)), backend, _contract(4, fault="A"), Path(raw) / "state.sqlite")
        self.assertEqual(sc.opened, sc.closed)
        self.assertEqual(sc.live, 0)

    def test_serial_and_prefetch_match_and_rerun_does_not_rewrite(self):
        def once(workers):
            sc = winio.VirtualSyscalls(dest_volume="DEST")
            _load(sc, [0])
            entity = _entity(0, extra=[PARENT + r"\0-alias"])
            backend = winio.WindowsBackend(sc)
            with tempfile.TemporaryDirectory() as raw:
                state = Path(raw) / "state.sqlite"
                first = r9_runner.production_run([entity], backend, _contract(workers), state)
                writes = sc.write_calls
                second = r9_runner.production_run([_entity(0, extra=[PARENT + r"\0-alias"])], backend, _contract(workers), state)
            return first, second, writes, sc

        serial, serial_rerun, serial_writes, serial_sc = once(1)
        prefetch, prefetch_rerun, prefetch_writes, prefetch_sc = once(4)
        self.assertEqual(serial["copied_count"], 1)
        self.assertEqual(prefetch["copied_count"], 1)
        self.assertEqual(serial["linked_count"], 1)
        self.assertEqual(prefetch["linked_count"], 1)
        self.assertEqual(bytes(serial_sc.files[PARENT + r"\0"]), bytes(prefetch_sc.files[PARENT + r"\0"]))
        self.assertEqual(serial_rerun["copied_count"], 0)
        self.assertEqual(prefetch_rerun["copied_count"], 0)
        self.assertEqual(serial_rerun["skipped_entities"], 1)
        self.assertEqual(prefetch_rerun["skipped_entities"], 1)
        self.assertEqual(prefetch_sc.write_calls, prefetch_writes)

    def test_unauthorized_real_backend_does_not_open_source(self):
        backend = winio.WindowsBackend(winio.Win32Syscalls())
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "state.sqlite"
            result = r9_runner.production_run(iter([_entity(0)]), backend, {
                "phase": "FORMAL_COPY",
                "copy_authorized": False,
                "source_prefetch_workers": 4,
                "state_path": str(state),
                "directories": [],
                "links": [],
                "run": {"run_id": "unauthorized"},
            }, state)
        self.assertTrue(result["refused_before_write"])
        self.assertEqual(result["write_calls"], 0)
        self.assertEqual(backend.sc.write_calls, 0)
        self.assertEqual(result["phase_stats"]["source_open_calls"], "NOT_RUN")

    def test_invalid_worker_count_refuses_before_source_open(self):
        sc = Tracking()
        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            result = r9_runner.production_run(iter([_entity(0)]), backend, _contract(5), Path(raw) / "state.sqlite")
        self.assertEqual(result["reason"], "PREFETCH_WORKERS")
        self.assertEqual(sc.opened, 0)
        self.assertEqual(result["phase_stats"]["source_open_calls"], "NOT_RUN")


class OrderBackend(winio.VirtualSyscalls):
    def __init__(self):
        super().__init__(dest_volume="DEST")
        self.events = []

    def commit_no_replace(self, temp, dest):
        ok = super().commit_no_replace(temp, dest)
        self.events.append(("commit", dest))
        return ok

    def hardlink(self, dest_representative, alias_path):
        ok = super().hardlink(dest_representative, alias_path)
        self.events.append(("hardlink", alias_path))
        return ok


class PrefetchOrderTests(unittest.TestCase):
    def test_done_alias_is_not_linked_before_the_new_entity_is_copied(self):
        sc = OrderBackend()
        _load(sc, [0, 1])
        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "state.sqlite"
            r9_runner.production_run([_entity(1)], backend, _contract(1), state)
            sc.events.clear()
            later = _entity(1, extra=[PARENT + r"\1-alias"])
            r9_runner.production_run([_entity(0), later], backend, _contract(4), state)
        self.assertEqual(sc.events[0], ("commit", PARENT + r"\0"))
        self.assertEqual(sc.events[1], ("hardlink", PARENT + r"\1-alias"))

    def test_front_failure_does_not_touch_later_done_alias_or_intent(self):
        class Bad(Tracking):
            def identity(self, handle):
                ident = super().identity(handle)
                if str(self.handles[handle]["path"]).endswith("\\0"):
                    ident = dict(ident)
                    ident["file_id"] = "other"
                return ident

        sc = Bad()
        _load(sc, [0, 1, 2])
        backend = winio.WindowsBackend(sc)
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "state.sqlite"
            r9_runner.production_run([_entity(1)], backend, _contract(1), state)
            with self.assertRaisesRegex(RuntimeError, "INTERRUPT_A"):
                r9_runner.production_run([_entity(2)], backend, _contract(1, fault="A"), state)
            sc.opened = sc.closed = sc.live = sc.peak = 0
            with self.assertRaisesRegex(RuntimeError, "SOURCE_CHANGED"):
                r9_runner.production_run(
                    [_entity(0), _entity(1, extra=[PARENT + r"\1-alias"]), _entity(2)],
                    backend,
                    _contract(4),
                    state,
                )
            import sqlite3
            conn = sqlite3.connect(state)
            phase = conn.execute(
                "SELECT phase FROM stage WHERE item_key=?",
                ("entity:2387166462|2",),
            ).fetchone()[0]
            conn.close()
        self.assertNotIn(PARENT + r"\1-alias", sc.files)
        self.assertEqual(phase, "INTENT")
        self.assertEqual(sc.opened, sc.closed)
        self.assertEqual(sc.live, 0)

    def test_entity_phase_wall_includes_prefetch_wait(self):
        sc = Tracking()
        _load(sc, range(2))
        backend = winio.WindowsBackend(sc)
        contract = _contract(4)
        contract["collect_timing"] = True
        with tempfile.TemporaryDirectory() as raw:
            result = r9_runner.production_run((_entity(i) for i in range(2)), backend, contract, Path(raw) / "state.sqlite")
        self.assertGreaterEqual(result["entity_phase_wall_seconds"], 0.15)
        self.assertGreater(result["entity_phase_wall_seconds"], result["copy_seconds"])

    def test_fault_b_and_c_close_unconsumed_handles(self):
        for fault in ("B", "C"):
            sc = Tracking()
            _load(sc, range(3))
            backend = winio.WindowsBackend(sc)
            entities = [_entity(i, extra=[PARENT + f"\\{i}-a", PARENT + f"\\{i}-b"]) for i in range(3)]
            with tempfile.TemporaryDirectory() as raw:
                with self.assertRaisesRegex(RuntimeError, f"INTERRUPT_{fault}"):
                    r9_runner.production_run(entities, backend, _contract(4, fault=fault), Path(raw) / "state.sqlite")
            self.assertEqual(sc.opened, sc.closed)
            self.assertEqual(sc.live, 0)


if __name__ == "__main__":
    unittest.main()
