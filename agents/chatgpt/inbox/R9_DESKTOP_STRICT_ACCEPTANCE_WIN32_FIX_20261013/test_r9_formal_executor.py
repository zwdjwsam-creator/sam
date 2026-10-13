# -*- coding: utf-8 -*-
import sqlite3
import tempfile
import unittest
from pathlib import Path

import r9_formal_executor as ex


def _base(path: Path):
    c = sqlite3.connect(path)
    c.executescript(
        """
        create table meta(key text primary key, value text);
        create table entries(
          path text primary key, is_dir integer, logical_size integer,
          alloc_size integer, volume_serial text, file_id text, reparse_tag integer
        );
        insert into meta values('source_volume_serial','2387166462');
        insert into entries values('E:\\BLACKBOX\\a.txt',0,10,16,'2387166462','11',0);
        insert into entries values('E:\\BLACKBOX\\dir',1,0,0,'11708076955747828990','22',0);
        insert into entries values('E:\\BLACKBOX\\link',0,0,0,'2387166462','33',0xA0000003);
        """
    )
    c.commit()
    c.close()


def _delta(path: Path, extra_path="E:\\BLACKBOX\\new.bin"):
    c = sqlite3.connect(path)
    c.executescript(
        f"""
        create table files(path text primary key, volume_serial text, file_id text, size integer);
        insert into files values('E:\\BLACKBOX\\a.txt','11708076955747828990','99',10);
        insert into files values('{extra_path}','11708076955747828990','100',5);
        """
    )
    c.commit()
    c.close()


class ExecutorTests(unittest.TestCase):
    def test_copy_refused_when_not_authorized(self):
        self.assertEqual(ex.refuse_copy(False), 3)

    def test_historical_serial_is_not_post_format_auth(self):
        self.assertFalse(ex.post_format_copy_allowed(ex.HISTORICAL_DEST_SERIAL, True))
        self.assertFalse(ex.post_format_copy_allowed("DEADBEEF", False))

    def test_original_d_sha_cannot_validate_repaired_db(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "d.sqlite"
            p.write_bytes(b"not-the-real-db")
            result = ex.validate_sha(p, ex.ORIGINAL_D_SHA_NOT_REPAIRED, "d_repaired")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "CONTRACT_BINDS_REPAIRED_DB_TO_ORIGINAL_SHA")

    def test_sha_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.bin"
            p.write_bytes(b"abc")
            result = ex.validate_sha(p, "0" * 64, "e_delta")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "SHA_MISMATCH")

    def test_invalid_identity_not_comparable(self):
        self.assertFalse(ex.identity_comparable("None", "1", "1", "1"))
        self.assertFalse(ex.identity_comparable("0", "5", "0", "5"))
        self.assertFalse(ex.identity_comparable(None, "5", "1", "5"))

    def test_delta_overlays_same_path_and_dirs_excluded_from_content(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            base, delta, plan = td / "base.sqlite", td / "delta.sqlite", td / "plan.sqlite"
            _base(base)
            _delta(delta)
            result = ex.plan_from_inputs(base, delta, None, plan)
            self.assertEqual(result["status"], "PARTIAL")
            self.assertFalse(result["copy_ready"])
            self.assertEqual(result["stats"]["e_content_bytes"], 10)
            self.assertEqual(result["stats"]["e_dir_paths"], 1)
            self.assertEqual(result["stats"]["delta_paths_already_in_base"], 1)
            codes = {c for c, _ in result["deficits"]}
            self.assertIn("D_REPAIRED_MISSING", codes)
            self.assertIn("IDENTITY_FORM_DIFFERS", codes)

    def test_missing_inputs_not_ready(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "plan.sqlite"
            result = ex.plan_from_inputs(None, None, None, plan)
            self.assertEqual(result["status"], "PARTIAL")
            self.assertFalse(result["copy_ready"])


class AdapterTests(unittest.TestCase):
    def test_wrong_sha_rejected(self):
        import r9_adapter as adapter
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.bin"
            p.write_bytes(b"abc")
            row = adapter.check_binding(p, "0" * 64, 3, "e_delta")
            self.assertFalse(row["ok"])
            self.assertEqual(row["reason"], "SHA_OR_SIZE_MISMATCH")

    def test_null_identity_blocks_plan(self):
        import r9_adapter as adapter
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            base, delta, ddb, plan = td / "b.sqlite", td / "dlt.sqlite", td / "d.sqlite", td / "plan.sqlite"
            b = sqlite3.connect(base)
            b.executescript(
                """
                create table entries(
                  path text primary key, is_dir integer, logical_size integer, alloc_size integer,
                  volume_serial text, file_id text, nlinks integer, reparse_tag integer, reparse_target text
                );
                insert into entries values('E:\\BLACKBOX\\a.txt',0,1,1,'2387166462','None',1,0,null);
                """
            )
            b.commit(); b.close()
            dlt = sqlite3.connect(delta)
            dlt.executescript("create table files(path text primary key, volume_serial_dword integer, file_id text, size integer, allocation_size integer, nlinks integer);")
            dlt.commit(); dlt.close()
            d = sqlite3.connect(ddb)
            d.executescript("create table nodes(path text primary key, is_dir integer, is_reparse integer, logical_size integer, volume_serial text, file_id text, nlinks integer);")
            d.commit(); d.close()
            code, result = adapter.build_plan(base, delta, ddb, plan)
            self.assertEqual(code, 2)
            self.assertFalse(result["plan_ready"])

    def test_copy_refused_even_if_flags_passed(self):
        import r9_adapter as adapter
        self.assertEqual(adapter.copy_entry_refused(True, True), 3)

    def test_fixture_delta_covers_and_d_merges(self):
        import r9_adapter as adapter
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            base, delta, ddb, plan = td / "b.sqlite", td / "dlt.sqlite", td / "d.sqlite", td / "plan.sqlite"
            b = sqlite3.connect(base)
            b.executescript(
                """
                create table meta(key text, value text);
                create table entries(
                  path text primary key, is_dir integer, logical_size integer, alloc_size integer,
                  volume_serial text, file_id text, nlinks integer, reparse_tag integer, reparse_target text
                );
                insert into entries values('E:\\BLACKBOX\\a.txt',0,15,15,'2387166462','11',2,0,null);
                insert into entries values('E:\\BLACKBOX\\a-link.txt',0,15,15,'2387166462','11',2,0,null);
                insert into entries values('E:\\BLACKBOX\\dir',1,0,0,'999','22',1,0,null);
                """
            )
            b.commit(); b.close()
            dlt = sqlite3.connect(delta)
            dlt.executescript(
                """
                create table files(
                  path text primary key, volume_serial_dword integer, file_id text, size integer,
                  allocation_size integer, nlinks integer
                );
                insert into files values('E:\\BLACKBOX\\a.txt',2387166462,'11',15,15,2);
                """
            )
            dlt.commit(); dlt.close()
            d = sqlite3.connect(ddb)
            d.executescript(
                """
                create table nodes(
                  path text primary key, is_dir integer, is_reparse integer, logical_size integer,
                  volume_serial text, file_id text, nlinks integer
                );
                insert into nodes values('D:\\JQ\\f.txt',0,0,7,'3187598165','77',1);
                insert into nodes values('D:\\JQ',1,0,0,'3187598165','88',1);
                """
            )
            d.commit(); d.close()
            code, result = adapter.build_plan(base, delta, ddb, plan)
            self.assertEqual(code, 0, result)
            self.assertTrue(result["plan_ready"])
            self.assertEqual(result["stats"]["d_file_paths"], 1)
            self.assertEqual(result["stats"]["delta_paths_already_in_base"], 1)
            self.assertEqual(result["stats"]["entity_count"], 2)
            self.assertEqual(result["stats"]["unique_content_bytes"], 22)
            self.assertEqual(result["stats"]["dir_paths"], 2)


if __name__ == "__main__":
    unittest.main()
