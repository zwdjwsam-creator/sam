# -*- coding: utf-8 -*-
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path, PureWindowsPath

import r9_bounded_pilot as pilot
import r9_runner as runner
import r9_source_contract as source
import r9_winio as winio

SAMPLE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json")
CONTRACT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json")


class RecordingStore:
    """Stand-in OS file data. Win32Syscalls methods perform the copy and the content hash."""

    def __init__(self):
        self.files = {}
        self.identities = {}
        self.handles = {}
        self.next_id = 1
        self.source_opens = 0

    def add_source(self, path, data, file_id, volume, mtime_ft):
        self.files[path] = bytearray(data)
        self.identities[path] = {
            "file_id": str(file_id),
            "volume_serial": str(volume),
            "mtime_ft": str(mtime_ft),
            "object_type": "file",
            "allocation_size": 4096,
        }

    def open_source(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        self.source_opens += 1
        hid = self.next_id
        self.next_id += 1
        self.handles[hid] = {"path": path, "pos": 0}
        return hid

    def identity(self, handle):
        path = self.handles[handle]["path"]
        meta = dict(self.identities[path])
        meta["size"] = len(self.files[path])
        return meta

    def read(self, handle, n):
        slot = self.handles[handle]
        data = self.files[slot["path"]]
        piece = bytes(data[slot["pos"]: slot["pos"] + n])
        slot["pos"] += len(piece)
        return piece

    def close(self, handle):
        self.handles.pop(handle, None)

    def create_temp(self, path):
        if self.source_opens < 2:
            raise RuntimeError("SOURCE_NOT_OBSERVED")
        if path in self.files:
            raise FileExistsError(path)
        self.files[path] = bytearray()
        hid = self.next_id
        self.next_id += 1
        self.handles[hid] = {"path": path, "pos": 0}
        return hid

    def write(self, handle, data):
        self.files[self.handles[handle]["path"]].extend(data)
        return len(data)

    def flush(self, handle):
        return True

    def commit_no_replace(self, temp, dest):
        if dest in self.files:
            return False
        data = bytes(self.files.pop(temp))
        self.identities.pop(temp, None)
        self.files[dest] = bytearray(data)
        self.identities[dest] = {
            "file_id": f"fid-{self.next_id}",
            "volume_serial": str(pilot.VOLUME_DWORD),
            "mtime_ft": "committed",
            "object_type": "file",
            "allocation_size": ((len(data) + 4095) // 4096) * 4096,
        }
        self.next_id += 1
        return True

    def hardlink(self, dest, alias):
        if alias in self.files or dest not in self.files:
            return False
        self.files[alias] = self.files[dest]
        self.identities[alias] = dict(self.identities[dest])
        return True

    def observe(self, path):
        if path not in self.files:
            return {"status": "MISSING"}
        data = bytes(self.files[path])
        ident = self.identities.get(path, {})
        kind = ident.get("object_type", "file")
        return {
            "status": "PRESENT",
            "path": path,
            "logical_size": 0 if kind != "file" else len(data),
            "sha256": hashlib.sha256(data).hexdigest() if kind == "file" else None,
            "object_type": kind,
            "file_id": ident.get("file_id"),
            "volume_serial": ident.get("volume_serial"),
            "allocation_size": ident.get("allocation_size", 0),
            "reparse_target": ident.get("reparse_target"),
            "mtime": ident.get("mtime_ft"),
        }

    def ensure_directory(self, path):
        parent = str(PureWindowsPath(str(path)).parent)
        if len(parent) > 3 and parent not in self.files:
            raise RuntimeError("PARENT_MISSING")
        current = self.identities.get(path)
        if current:
            if current.get("object_type") != "directory":
                raise RuntimeError("TYPE_CONFLICT")
            return
        self.files[path] = bytearray()
        self.identities[path] = {
            "file_id": f"dir-{self.next_id}",
            "volume_serial": str(pilot.VOLUME_DWORD),
            "object_type": "directory",
            "allocation_size": 0,
        }
        self.next_id += 1

    def create_reparse(self, link_path, target, kind="junction"):
        return False

    def list_nofollow(self, root):
        prefix = str(root).rstrip("\\") + "\\"
        found = []
        for path, ident in self.identities.items():
            text = str(path)
            if not text.startswith(prefix):
                continue
            rest = text[len(prefix):]
            if "\\" in rest:
                continue
            found.append({"path": text, "object_type": ident.get("object_type", "file")})
        return found


class ProbeOs:
    def __init__(self, serial=pilot.VOLUME_DWORD, filesystem="NTFS", disk=pilot.DISK_ID, reparse=(), unknown=()):
        self.serial = serial
        self.filesystem = filesystem
        self.disk = disk
        self.reparse = {pilot.canonical_path(item).casefold() for item in reparse}
        self.unknown = {pilot.canonical_path(item).casefold() for item in unknown}

    def volume_information(self, root):
        if self.serial is None:
            return None
        return {"serial": self.serial, "filesystem": self.filesystem}

    def disk_unique_id(self, letter):
        return self.disk

    def observe_nofollow(self, path):
        key = pilot.canonical_path(path).casefold()
        if key in self.unknown:
            return {"status": "ERROR", "winerror": 5}
        if key in self.reparse:
            return {"status": "PRESENT", "object_type": "junction", "reparse_target": r"D:\other"}
        if key == "e:\\":
            return {"status": "PRESENT", "object_type": "directory", "allocation_size": 0, "file_id": "vol", "volume_serial": str(pilot.VOLUME_DWORD)}
        return {"status": "MISSING"}


def _run(run_id="pilot-1147"):
    return {
        "run_id": run_id,
        "plan_digest": pilot.PLAN_SHA,
        "inputs_digest": pilot.sample_sha256(SAMPLE),
        "code_digest": source.code_digest(),
        "dest_volume": str(pilot.VOLUME_DWORD),
        "dest_root": pilot.DEST_ROOT,
    }


def _authorized(run_id="pilot-1147"):
    return {
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
        "run": _run(run_id),
    }


def _backend_for_sample():
    sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
    entities = pilot.entities_for_run(sample)
    store = RecordingStore()
    for index, entity in enumerate(entities):
        store.add_source(
            entity["source_path"],
            b"x" * int(entity["logical_size"]),
            entity["file_id"],
            entity["volume_serial"],
            "9001" if index == 0 else "9002",
        )
    backend = winio.WindowsBackend(winio.Win32Syscalls(api=store))
    return sample, entities, store, backend


class BoundedPilotTests(unittest.TestCase):
    def test_sample_limits_and_flat_destinations(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        pilot.validate_sample(sample)
        self.assertEqual(sample["entities"][0]["logical_size"], 6849)
        self.assertEqual(len(sample["entities"][0]["paths"]), 39)
        self.assertEqual(sample["entities"][1]["logical_size"], 2463)
        built = pilot.entities_for_run(sample)
        self.assertTrue(all(item["mtime_status"] == "PRIOR_OBSERVATION" for item in built))
        self.assertNotEqual(source.code_digest(), json.loads(CONTRACT.read_bytes().decode("utf-8"))["code_digest"])

    def test_public_execute_uses_win32_chain_and_second_run_does_not_write(self):
        sample, entities, store, backend = _backend_for_sample()
        self.assertFalse(hasattr(backend.sc, "dest_volume"))
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            contract = td / "contract.json"
            contract.write_text(json.dumps(_authorized()), encoding="utf-8")
            state = td / "state.sqlite"
            before = backend.sc.recorded_writes
            real_before = winio.Win32Syscalls.write_calls
            self.assertEqual(pilot.execute(SAMPLE, contract, backend=backend, os_api=ProbeOs(), state_path=state), 0)
            self.assertGreater(backend.sc.recorded_writes, before)
            self.assertEqual(winio.Win32Syscalls.write_calls, real_before)
            self.assertEqual(backend.sc.hash_calls, 2)
            rep = backend.observe_destination(entities[0]["dest_path"])
            alias = sample["entities"][0]["paths"][1]["dest_path"]
            self.assertEqual(backend.observe_destination(alias)["file_id"], rep["file_id"])
            self.assertEqual(rep["volume_serial"], str(pilot.VOLUME_DWORD))
            self.assertNotEqual(rep["file_id"], backend.observe_destination(entities[1]["dest_path"])["file_id"])
            writes = backend.sc.recorded_writes
            hashes = backend.sc.hash_calls
            self.assertEqual(pilot.execute(SAMPLE, contract, backend=backend, os_api=ProbeOs(), state_path=state), 0)
            self.assertEqual(backend.sc.recorded_writes, writes)
            self.assertEqual(winio.Win32Syscalls.write_calls, real_before)
            self.assertEqual(backend.sc.hash_calls, hashes + 4)

    def test_probe_data_refuses_before_write(self):
        _sample, _entities, _store, backend = _backend_for_sample()
        cases = {
            "disk": ProbeOs(disk="eui.OTHER"),
            "volume": ProbeOs(serial=0x806508DF),
            "unknown_disk": ProbeOs(disk=None),
            "reparse": ProbeOs(reparse=[pilot.DEST_ROOT]),
            "unknown_reparse": ProbeOs(unknown=["E:\\"]),
        }
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            contract = td / "contract.json"
            contract.write_text(json.dumps(_authorized()), encoding="utf-8")
            for name, probe in cases.items():
                before = backend.sc.recorded_writes
                real_before = winio.Win32Syscalls.write_calls
                self.assertEqual(
                    pilot.execute(SAMPLE, contract, backend=backend, os_api=probe, state_path=td / f"{name}.sqlite"),
                    3,
                    name,
                )
                self.assertEqual(backend.sc.recorded_writes, before, name)
                self.assertEqual(winio.Win32Syscalls.write_calls, real_before, name)

    def test_contract_and_run_refusals_before_write(self):
        _sample, _entities, _store, backend = _backend_for_sample()
        base = _authorized()
        cases = {
            "volume": {**base, "volume_serial_hex": "806508DF"},
            "disk": {**base, "disk_unique_id": "other"},
            "code": {**base, "code_digest": "stale"},
            "sample": {**base, "sample_sha256": "0" * 64},
            "missing_run": {key: value for key, value in base.items() if key != "run"},
        }
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            for name, payload in cases.items():
                path = td / f"{name}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                before = backend.sc.recorded_writes
                real_before = winio.Win32Syscalls.write_calls
                self.assertEqual(pilot.execute(SAMPLE, path, backend=backend, os_api=ProbeOs(), state_path=td / f"{name}.sqlite"), 3, name)
                self.assertEqual(backend.sc.recorded_writes, before, name)
                self.assertEqual(winio.Win32Syscalls.write_calls, real_before, name)
            old = td / "old.json"
            old.write_text(json.dumps(_authorized("pilot-old")), encoding="utf-8")
            state = td / "old.sqlite"
            self.assertEqual(pilot.execute(SAMPLE, old, backend=backend, os_api=ProbeOs(), state_path=state), 0)
            changed = td / "changed.json"
            changed.write_text(json.dumps(_authorized("pilot-new")), encoding="utf-8")
            before = backend.sc.recorded_writes
            real_before = winio.Win32Syscalls.write_calls
            self.assertEqual(pilot.execute(SAMPLE, changed, backend=backend, os_api=ProbeOs(), state_path=state), 3)
            self.assertEqual(backend.sc.recorded_writes, before)
            self.assertEqual(winio.Win32Syscalls.write_calls, real_before)

    def test_acceptance_rejects_bad_content_size_directory_alias_and_identity(self):
        sample, entities, store, backend = _backend_for_sample()
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            contract = td / "contract.json"
            contract.write_text(json.dumps(_authorized()), encoding="utf-8")
            state = td / "state.sqlite"
            self.assertEqual(pilot.execute(SAMPLE, contract, backend=backend, os_api=ProbeOs(), state_path=state), 0)
            run = _run()
            db = sqlite3.connect(state)
            db.execute("UPDATE stage SET sha256=? WHERE item_key=?", ("wrong-content-hash", "entity:" + entities[0]["entity_key"]))
            db.commit()
            db.close()
            bad_hash = pilot.accept_pilot(sample, backend, state, run)
            self.assertFalse(bad_hash["full_acceptance"])
            self.assertIn("CONTENT_HASH", bad_hash["reasons"])
            self.assertNotIn("SIZE_MISMATCH", bad_hash["reasons"])
            db = sqlite3.connect(state)
            db.execute("UPDATE stage SET logical_size=1 WHERE kind='entity'")
            db.commit()
            db.close()
            bad_size = pilot.accept_pilot(sample, backend, state, run)
            self.assertFalse(bad_size["full_acceptance"])
            self.assertIn("SIZE_MISMATCH", bad_size["reasons"])
            db = sqlite3.connect(state)
            db.execute("UPDATE stage SET logical_size=?, sha256=? WHERE item_key=?", (entities[0]["logical_size"], hashlib.sha256(b"x" * int(entities[0]["logical_size"])).hexdigest(), "entity:" + entities[0]["entity_key"]))
            db.execute("UPDATE stage SET logical_size=?, sha256=? WHERE item_key=?", (entities[1]["logical_size"], hashlib.sha256(b"x" * int(entities[1]["logical_size"])).hexdigest(), "entity:" + entities[1]["entity_key"]))
            db.commit()
            db.close()
            self.assertTrue(pilot.accept_pilot(sample, backend, state, run)["full_acceptance"])
            del store.files[pilot.DEST_ROOT + "\\e"]
            del store.identities[pilot.DEST_ROOT + "\\e"]
            self.assertFalse(pilot.accept_pilot(sample, backend, state, run)["full_acceptance"])
            store.ensure_directory(pilot.DEST_ROOT + "\\e")
            alias = sample["entities"][0]["paths"][1]["dest_path"]
            store.identities[alias]["file_id"] = "split"
            self.assertIn("ALIAS_SPLIT", pilot.accept_pilot(sample, backend, state, run)["reasons"])
            store.identities[alias]["file_id"] = store.identities[entities[0]["dest_path"]]["file_id"]
            for entity in entities:
                for dest in [entity["dest_path"], *entity["extra_dest_paths"]]:
                    store.identities[dest]["file_id"] = "same-id"
            db = sqlite3.connect(state)
            db.execute("UPDATE stage SET file_id=? WHERE kind='entity'", ("same-id",))
            db.commit()
            db.close()
            self.assertIn("ENTITY_MERGE", pilot.accept_pilot(sample, backend, state, run)["reasons"])
            self.assertFalse(pilot.accept_pilot(sample, backend, state, None)["full_acceptance"])

    def test_win32_content_sha_reads_injected_bytes(self):
        store = RecordingStore()
        store.files[r"C:\temp\a.bin"] = bytearray(b"abc")
        store.identities[r"C:\temp\a.bin"] = {"file_id": "1", "volume_serial": "1", "mtime_ft": "1", "object_type": "file"}
        sc = winio.Win32Syscalls(api=store)
        before = winio.Win32Syscalls.write_calls
        self.assertEqual(sc.content_sha(r"C:\temp\a.bin"), hashlib.sha256(b"abc").hexdigest())
        self.assertEqual(sc.hash_calls, 1)
        self.assertEqual(winio.Win32Syscalls.write_calls, before)
        self.assertFalse(hasattr(sc, "dest_volume"))

    def test_partial_win32_contract_cannot_write(self):
        backend = winio.WindowsBackend(winio.Win32Syscalls())
        contract = {
            "phase": "PILOT_REAL_IO",
            "pilot_write_authorized": True,
            "scope": "BOUNDED_PILOT_ONLY",
            "dest_root": pilot.DEST_ROOT,
            "volume_serial_hex": pilot.VOLUME_HEX,
        }
        self.assertFalse(runner.allows_write(contract, backend))
        with tempfile.TemporaryDirectory() as raw:
            before = winio.Win32Syscalls.write_calls
            result = runner.production_run(iter(()), backend, contract, Path(raw) / "state.sqlite")
            self.assertTrue(result["refused_before_write"])
            self.assertEqual(winio.Win32Syscalls.write_calls, before)

    def test_dry_run_and_unauthorized_execute_do_not_write(self):
        before = winio.Win32Syscalls.write_calls
        self.assertEqual(pilot.dry_run(SAMPLE, CONTRACT), 0)
        self.assertEqual(pilot.execute(SAMPLE, CONTRACT), 3)
        self.assertEqual(winio.Win32Syscalls.write_calls, before)

    def test_path_shapes_are_rejected(self):
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        sample["entities"][0]["logical_size"] = 1
        with self.assertRaises(RuntimeError):
            pilot.validate_sample(sample)
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        sample["entities"][0]["paths"][0]["dest_path"] = r"E:\BLACKBOX\not-pilot"
        with self.assertRaises(RuntimeError):
            pilot.validate_sample(sample)
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        sample["entities"][0]["paths"][0]["dest_path"] = pilot.DEST_ROOT + r"\e\..\e\p00"
        with self.assertRaises(RuntimeError):
            pilot.validate_sample(sample)
        sample = json.loads(SAMPLE.read_bytes().decode("utf-8"))
        sample["entities"][0]["paths"][0]["dest_path"] = pilot.DEST_ROOT + r"\e\p00:stream"
        with self.assertRaises(RuntimeError):
            pilot.validate_sample(sample)


if __name__ == "__main__":
    unittest.main()
