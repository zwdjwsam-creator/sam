# -*- coding: utf-8 -*-
import unittest
import r9_copy_body as body


ROOTS = (r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES")


class CopyBodyTests(unittest.TestCase):
    def _chunks(self, parts):
        data = list(parts)
        def read():
            if not data:
                return b""
            return data.pop(0)
        return read

    def test_write_rejects_escape_ads_and_nul(self):
        sha = __import__("hashlib").sha256(b"ab").hexdigest()
        with self.assertRaises(body.LinkRejected):
            body.write_entity_bytes(self._chunks([b"ab"]), lambda: "id", r"E:\BLACKBOX\..\x", 2, "id", sha, ROOTS, lambda *_: None, lambda *_: None)
        with self.assertRaises(body.LinkRejected):
            body.assert_dest_allowed(r"E:\BLACKBOX\a.txt:evil", ROOTS)
        with self.assertRaises(body.LinkRejected):
            body.assert_dest_allowed(r"E:\BLACKBOX\NUL", ROOTS)

    def test_write_streams_and_returns_hash(self):
        payload = b"xyz"
        sha = __import__("hashlib").sha256(payload).hexdigest()
        seen = []
        out = body.write_entity_bytes(
            self._chunks([b"x", b"yz"]),
            lambda: "id1",
            r"E:\BLACKBOX\a.bin",
            3,
            "id1",
            sha,
            ROOTS,
            lambda chunk: seen.append(chunk),
            lambda temp, dest: seen.append(("commit", temp, dest)),
        )
        self.assertEqual(out["sha256"], sha)
        self.assertEqual(seen[0], b"x")
        self.assertEqual(seen[1], b"yz")
        self.assertNotIn(payload, seen)

    def test_batch_and_hardlink_groups(self):
        planned = {"path": "a", "sha256": "aa", "file_id": "src", "volume_serial": "sv", "logical_size": 1, "alloc_size": 2, "object_type": "file"}
        observed = dict(planned, dest_file_id="d1", dest_volume_serial="dv")
        batch = body.accept_batch([planned], lambda row: observed)
        self.assertTrue(batch["ok"])
        missing = body.accept_batch([planned], lambda row: {"logical_size": 1, "alloc_size": 2})
        self.assertFalse(missing["ok"])
        good = body.hardlink_groups_ok([
            [{"dest_file_id": "1", "dest_volume_serial": "v"}],
            [{"dest_file_id": "2", "dest_volume_serial": "v"}],
        ])
        self.assertTrue(good["ok"])
        bad = body.hardlink_groups_ok([
            [{"dest_file_id": "1", "dest_volume_serial": "v"}],
            [{"dest_file_id": "1", "dest_volume_serial": "v"}],
        ])
        self.assertFalse(bad["ok"])

    def test_accept_rejects_missing_fields(self):
        result = body.accept_on_disk({"logical_size": 0, "alloc_size": 0}, {"logical_size": 0, "alloc_size": 0})
        self.assertFalse(result["ok"])
        self.assertTrue(any(item.startswith("MISSING_") for item in result["reasons"]))

    def test_hardlink_same_volume_only(self):
        with self.assertRaises(body.LinkRejected):
            body.create_local_hardlink(lambda *_: None, r"E:\BLACKBOX\a", r"E:\BLACKBOX\b", "v1", "v2", ROOTS)
        seen = []
        body.create_local_hardlink(lambda s, d: seen.append((s, d)), r"E:\BLACKBOX\a", r"E:\BLACKBOX\b", "v1", "v1", ROOTS)
        self.assertEqual(seen, [(r"E:\BLACKBOX\a", r"E:\BLACKBOX\b")])

    def test_reparse_refuses_source_drive_and_unc(self):
        with self.assertRaises(body.LinkRejected):
            body.rebuild_reparse(lambda *_: None, r"E:\BLACKBOX_ENGINES\a", r"D:\OLD", ROOTS)
        with self.assertRaises(body.LinkRejected):
            body.rebuild_reparse(lambda *_: None, r"E:\BLACKBOX_ENGINES\a", r"\\192.168.100.2\E_DRIVE\BLACKBOX\a", ROOTS)
        seen = []
        body.rebuild_reparse(lambda link, target: seen.append((link, target)), r"E:\BLACKBOX_ENGINES\a", r"E:\BLACKBOX\data", ROOTS)
        self.assertEqual(seen[0][1], r"E:\BLACKBOX\data")

    def test_accept_splits_failures(self):
        planned = {"sha256": "aa", "file_id": "1", "volume_serial": "9", "logical_size": 3, "alloc_size": 4, "object_type": "file", "dest_file_id": "8", "dest_volume_serial": "7"}
        bad = dict(planned, sha256="zz", logical_size=9)
        result = body.accept_on_disk(planned, bad)
        self.assertFalse(result["ok"])
        self.assertIn("CONTENT_SHA", result["reasons"])
        self.assertIn("SIZE", result["reasons"])
        self.assertTrue(body.accept_on_disk(planned, dict(planned))["ok"])


if __name__ == "__main__":
    unittest.main()
