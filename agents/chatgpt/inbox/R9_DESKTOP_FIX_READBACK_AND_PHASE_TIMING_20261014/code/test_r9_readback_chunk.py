# -*- coding: utf-8 -*-
import hashlib
import unittest

import r9_winio as winio

CHUNK = 1024 * 1024


class Recording(winio.VirtualSyscalls):
    def __init__(self):
        super().__init__()
        self.read_requests = []

    def read(self, handle, n):
        self.read_requests.append((self.handles[handle]["path"], n))
        return super().read(handle, n)


def _entity(size, name="E:\\R9_FORMAL_PILOT_1G_20261014\\BLACKBOX\\a.bin"):
    return {
        "source_path": "SRC",
        "dest_path": name,
        "file_id": "11",
        "volume_serial": "2387166462",
        "logical_size": size,
        "mtime": "T1",
        "mtime_status": "FROM_PLAN",
    }


def _prepare(sc, payload):
    sc.files["SRC"] = payload
    sc.identities["SRC"] = {
        "file_id": "11",
        "volume_serial": "2387166462",
        "mtime": "T1",
        "object_type": "file",
        "allocation_size": 4096,
    }


class ReadbackChunkTests(unittest.TestCase):
    def test_readback_uses_mib_chunks_including_tail(self):
        payload = b"a" * CHUNK + b"tail-bytes"
        sc = Recording()
        _prepare(sc, payload)
        backend = winio.WindowsBackend(sc, chunk=CHUNK)
        self.assertEqual(backend.phase_stats["readback_calls"], "NOT_RUN")
        copied = backend.copy_entity(_entity(len(payload)))
        self.assertEqual(copied["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(copied["bytes"], len(payload))
        readback = [n for path, n in sc.read_requests if str(path).endswith(".partial")]
        self.assertEqual(readback, [CHUNK, len(payload) - CHUNK])
        self.assertEqual(backend.phase_stats["readback_calls"], 2)
        self.assertEqual(backend.phase_stats["readback_bytes"], len(payload))
        self.assertGreater(backend.phase_stats["flush_calls"], 0)
        self.assertNotEqual(backend.phase_stats["source_open_seconds"], "NOT_RUN")

    def test_short_failed_and_corrupt_readback_are_rejected(self):
        payload = b"b" * 3000

        class Short(Recording):
            def read(self, handle, n):
                if str(self.handles[handle]["path"]).endswith(".partial"):
                    return b""
                return super().read(handle, n)

        class Failed(Recording):
            def read(self, handle, n):
                if str(self.handles[handle]["path"]).endswith(".partial"):
                    raise OSError("read failed")
                return super().read(handle, n)

        class Corrupt(Recording):
            def read(self, handle, n):
                if str(self.handles[handle]["path"]).endswith(".partial"):
                    return b"\x00" * n
                return super().read(handle, n)

        for cls, error in ((Short, "DEST_SHORT"), (Failed, "read failed"), (Corrupt, "DEST_HASH")):
            sc = cls()
            _prepare(sc, payload)
            backend = winio.WindowsBackend(sc, chunk=CHUNK)
            with self.assertRaisesRegex(Exception, error):
                backend.copy_entity(_entity(len(payload)))
            self.assertIsInstance(backend.phase_stats["readback_calls"], int)


if __name__ == "__main__":
    unittest.main()
