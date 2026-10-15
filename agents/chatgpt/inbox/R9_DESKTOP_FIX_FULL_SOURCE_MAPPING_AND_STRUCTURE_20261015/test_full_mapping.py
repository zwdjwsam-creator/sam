# -*- coding: utf-8 -*-
import sqlite3
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


class Mapping(unittest.TestCase):
    def test_full_d_source_without_share_is_unbound(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "d.sqlite"
            fixtures._write(plan, [(r"D:\data\one.txt", 4)], [r"D:\data"], [])
            with self.assertRaises(RuntimeError):
                next(chain._entities(plan, plan.stat()))

    def test_full_d_source_uses_the_sam_unc(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "d.sqlite"
            fixtures._write(plan, [(r"D:\data\one.txt", 4)], [r"D:\data"], [])
            entity = next(chain._entities(plan, plan.stat(), SHARES))
            self.assertEqual(entity["source_path"], r"\\192.168.100.2\D_DRIVE\data\one.txt")
            self.assertEqual(entity["source_share"], "D_DRIVE")
            self.assertEqual(entity["dest_path"], r"E:\BLACKBOX_ENGINES\data\one.txt")

    def test_missing_share_contract_keeps_the_gate_closed(self):
        self.assertIsNone(chain.full_share_binding({"shares": {"d_unc_root": "D:\\", "e_unc_root": SHARES["e_unc_root"]}}))
        self.assertFalse(chain.formal_write_gate({
            "phase": "FORMAL_COPY",
            "scope": "FULL",
            "copy_authorized": True,
            "full_migration": True,
            "version_choice": "AS_IS_MIGRATE_MARKED",
            "isolated_chain": True,
            "plan_sha": "temp",
            "source_plan_sha": "temp",
            "dest_roots": [chain.FORMAL_E, chain.FORMAL_D],
            "expected_volume_serial": "DEST",
            "expected_unique_id": "ISOLATED",
            "max_unique_bytes": 4,
            "subset_unique_bytes": 4,
            "state_path": r"C:\LAN_SHARE_REPORT\state.sqlite",
            "dest_probe": {"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED"},
            "plan_audit": {"ok": True},
            "run": {"plan_digest": "temp", "inputs_digest": "temp", "code_digest": "x", "dest_volume": "DEST", "dest_root": chain.FORMAL_E},
        }, winio.WindowsBackend(winio.VirtualSyscalls())))

    def test_reproduced_structure_gaps_now_fail(self):
        cases = [
            ("EMPTY_DIRECTORY_MISSING_PARENT", [r"E:\BLACKBOX\missing\empty"], []),
            ("LINK_MISSING_PARENT", [r"E:\BLACKBOX\real"], [(r"E:\BLACKBOX\missing\link", r"E:\BLACKBOX\real")]),
            ("ORDINARY_DIRECTORY_LINK_COLLISION", [r"E:\BLACKBOX\a"], [(r"E:\BLACKBOX\a", r"E:\BLACKBOX\a")]),
        ]
        for name, dirs, links in cases:
            with tempfile.TemporaryDirectory() as folder:
                plan = Path(folder) / (name + ".sqlite")
                fixtures._write(plan, [(r"E:\BLACKBOX\one.txt", 4)], dirs, links)
                audit = chain.inspect_plan(plan, fixtures._contract(plan))
                self.assertFalse(audit["ok"], name)
                self.assertEqual(audit["error"], "LINK_CLOSURE")

    def test_link_inventory_parent_is_not_replaced_by_the_migrated_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            fixtures._write(
                plan,
                [(r"E:\BLACKBOX\one.txt", 4)],
                [r"E:\BLACKBOX"],
                [(r"E:\BLACKBOX\missing\link", r"E:\BLACKBOX")],
            )
            db = sqlite3.connect(plan)
            db.execute(
                "UPDATE links SET migrated_link_path=? WHERE path=?",
                (r"E:\BLACKBOX\link", r"E:\BLACKBOX\missing\link"),
            )
            db.commit()
            db.close()
            audit = chain.inspect_plan(plan, fixtures._contract(plan))
            self.assertFalse(audit["ok"])
            self.assertGreater(audit["closure"]["missing_parent"], 0)

    def test_isolated_full_open_source_uses_unc_for_e_and_d(self):
        payload = b"abcd"
        e_source = r"\\192.168.100.2\E_DRIVE\BLACKBOX\alias.txt"
        d_source = r"\\192.168.100.2\D_DRIVE\data\alias.txt"
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / "plan.sqlite"
            fixtures._write(
                plan,
                [],
                [r"D:\data", r"E:\BLACKBOX"],
                [],
            )
            # two paths per entity, written directly so the alias shares the file id
            import sqlite3
            db = sqlite3.connect(plan)
            for volume, file_id, paths in (
                ("2387166462", "e1", [r"E:\BLACKBOX\one.txt", r"E:\BLACKBOX\alias.txt"]),
                ("3187598165", "d1", [r"D:\data\one.txt", r"D:\data\alias.txt"]),
            ):
                db.execute("INSERT INTO entities VALUES (?,?,?,?,?,?,0,0)", (volume, file_id, 2, 4, 4, 2))
                for path in paths:
                    db.execute(
                        "INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (path, 0, 0, 4, 4096, volume, file_id, 2, None, "t"),
                    )
            db.commit()
            db.close()
            ident = {"volume_serial": "2387166462", "file_id": "e1", "mtime": "1", "nlinks": 1}
            ident_d = {"volume_serial": "3187598165", "file_id": "d1", "mtime": "1", "nlinks": 1}
            sc = winio.VirtualSyscalls(
                files={e_source: payload, d_source: payload},
                identities={e_source: ident, d_source: ident_d},
                dest_volume="DEST",
            )
            backend = winio.WindowsBackend(sc)
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
                    "run_id": "isolated-full-0800",
                    "plan_digest": contract["plan_sha"],
                    "inputs_digest": contract["plan_sha"],
                    "code_digest": source_contract.code_digest(),
                    "dest_volume": "DEST",
                    "dest_root": chain.FORMAL_E,
                },
            })
            result = chain.execute_contract(contract, "execute", backend=backend, probe={"ok": True, "volume_serial": "DEST", "unique_id": "ISOLATED", "filesystem": "NTFS"})
            opened = list(sc.opened_sources)
            self.assertIn(e_source, opened, result)
            self.assertIn(d_source, opened)
            self.assertFalse(any(str(path).upper().startswith("D:\\") for path in opened))
            self.assertTrue(any(str(path).startswith("E:\\BLACKBOX_ENGINES\\") for path in sc.files), list(sc.files))
            self.assertFalse(result.get("full_plan_acceptance"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
