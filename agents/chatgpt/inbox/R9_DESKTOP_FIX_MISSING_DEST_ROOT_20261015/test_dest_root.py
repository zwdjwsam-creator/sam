# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_ASIS_FINAL_CANDIDATE_20261015")
import r9_formal_chain as chain
import r9_source_contract as source_contract
import r9_winio as winio
import test_full_closure as fixtures

SHARES = {"d_unc_root": r"\\192.168.100.2\D_DRIVE", "e_unc_root": r"\\192.168.100.2\E_DRIVE\BLACKBOX"}


class ParentRequired(winio.VirtualSyscalls):
    def ensure_directory(self, path):
        text = str(path).replace("/", "\\").rstrip("\\")
        parent = text.rsplit("\\", 1)[0]
        if "\\" in parent and parent not in self.files:
            raise OSError(None, f"CreateDirectoryW failed path={text} winerror=3", None, 3)
        ident = self.identities.get(text, {})
        if text in self.files and ident.get("object_type") not in (None, "directory"):
            raise RuntimeError("TYPE_CONFLICT")
        return super().ensure_directory(text)


class DestRoot(unittest.TestCase):
    def test_full_directory_sequence_includes_both_roots(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            fixtures._write(plan, [(r"D:\data\one.txt", 4)], [r"E:\BLACKBOX", r"D:\data"], [])
            paths = [item["dest_path"] for item in chain._directories(plan, "FULL")]
            self.assertEqual(paths[:3], [r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES", r"E:\BLACKBOX_ENGINES\data"])
            audit = chain.inspect_plan(plan, fixtures._contract(plan))
            self.assertTrue(audit["ok"], audit)

    def test_missing_non_root_parent_is_still_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            fixtures._write(plan, [(r"E:\BLACKBOX\one.txt", 4)], [r"E:\BLACKBOX\missing\empty"], [])
            audit = chain.inspect_plan(plan, fixtures._contract(plan))
            self.assertFalse(audit["ok"])
            self.assertEqual(audit["error"], "LINK_CLOSURE")

    def test_parent_required_full_execute_creates_both_roots(self):
        source = r"\\192.168.100.2\D_DRIVE\data\one.txt"
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            fixtures._write(plan, [(r"D:\data\one.txt", 4)], [r"E:\BLACKBOX", r"D:\data"], [])
            sc = ParentRequired(
                files={source: b"abcd"},
                identities={source: {"volume_serial": "2387166462", "file_id": r"D:\data\one.txt", "mtime": "1", "nlinks": 1}},
                dest_volume="DEST",
            )
            contract = fixtures._contract(plan)
            contract.update({
                "phase": "FORMAL_COPY",
                "plan_path": str(plan),
                "copy_authorized": True,
                "full_migration": True,
                "version_choice": "AS_IS_MIGRATE_MARKED",
                "isolated_chain": True,
                "shares": SHARES,
                "source_plan_sha": contract["plan_sha"],
                "dest_roots": [chain.FORMAL_E, chain.FORMAL_D],
                "expected_volume_serial": "DEST",
                "expected_unique_id": "ISOLATED",
                "state_path": str(Path(folder) / "state.sqlite"),
                "run": {
                    "run_id": "isolated-root-1400",
                    "plan_digest": contract["plan_sha"],
                    "inputs_digest": contract["plan_sha"],
                    "code_digest": source_contract.code_digest(),
                    "dest_volume": "DEST",
                    "dest_root": chain.FORMAL_E,
                },
            })
            backend = winio.WindowsBackend(sc)
            first = chain.execute_contract(contract, "execute", backend=backend, probe={"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"})
            self.assertTrue(first.get("acceptance", {}).get("full_acceptance"), first)
            self.assertIn(r"E:\BLACKBOX", sc.files)
            self.assertIn(r"E:\BLACKBOX_ENGINES", sc.files)
            self.assertIn(source, sc.opened_sources)
            self.assertFalse(any(str(path).upper().startswith("D:\\") for path in sc.opened_sources))
            second = chain.execute_contract(contract, "execute", backend=backend, probe={"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"})
            self.assertTrue(second.get("acceptance", {}).get("full_acceptance"), second)
            self.assertEqual(second.get("copied_count"), 0)

    def test_existing_directory_root_is_idempotent_and_file_root_is_refused(self):
        sc = ParentRequired(dest_volume="DEST")
        sc.ensure_directory(r"E:\BLACKBOX")
        sc.ensure_directory(r"E:\BLACKBOX")
        self.assertEqual(sc.identities[r"E:\BLACKBOX"]["object_type"], "directory")
        blocked = ParentRequired(
            files={r"E:\BLACKBOX_ENGINES": b"x"},
            identities={r"E:\BLACKBOX_ENGINES": {"object_type": "file", "volume_serial": "DEST", "file_id": "f"}},
            dest_volume="DEST",
        )
        with self.assertRaises(RuntimeError):
            blocked.ensure_directory(r"E:\BLACKBOX_ENGINES")


if __name__ == "__main__":
    unittest.main(verbosity=1)
