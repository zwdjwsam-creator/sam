import importlib.util, json, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("capture_registered_layer_metadata_r1.py")
SPEC = importlib.util.spec_from_file_location("capture_metadata", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class CaptureTests(unittest.TestCase):
    def test_literal_date_hit_only(self):
        got = MOD.summarize_json({"datasets":[{"dataset_id":"X","layers":{"RAW":{"max":"2026-11-11"}}}]})
        self.assertEqual(got["product_ids"],["X"])
        self.assertEqual([x["date"] for x in got["candidate_session_literal_hits"]],["2026-11-11"])
        self.assertIn("no row-level",got["interpretation_limit"].lower())

    def test_csv_rows_are_preserved(self):
        got=MOD.summarize_csv(b"domain,clean_action\nprice_fq_factor,jqdata_native_load\n")
        self.assertEqual(got["row_count"],1)
        self.assertEqual(got["rows"][0]["domain"],"price_fq_factor")

    def test_capture_bytes_and_readback(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); src=r/"a.json"; src.write_text('{"dataset_id":"X"}',encoding="utf-8")
            code,m=MOD.capture([{"id":"a","path":str(src),"basis":"fixture","format":"json"}],r/"pkg",r/"pkg"/"delivery")
            row=m["inputs"][0]
            self.assertEqual(code,0); self.assertEqual(row["status"],"CAPTURED")
            self.assertEqual(row["sha256"],row["readback_sha256"])
            self.assertEqual(src.read_text(encoding="utf-8"),'{"dataset_id":"X"}')

    def test_missing_exact_path(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); code,m=MOD.capture([{"id":"x","path":str(r/"missing.json"),"basis":"fixture","format":"json"}],r/"pkg",r/"pkg"/"delivery")
            self.assertEqual(code,2); self.assertEqual(m["inputs"][0]["status"],"NOT_FOUND_AT_EXACT_PATH")

    def test_existing_delivery_stops(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); d=r/"pkg"/"delivery"; d.mkdir(parents=True); f=d/"keep"; f.write_text("x")
            code,_=MOD.capture([],r/"pkg",d)
            self.assertEqual(code,4); self.assertEqual(f.read_text(),"x")

    def test_file_size_cap(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); src=r/"large.json"; src.write_bytes(b"x"*20)
            code,m=MOD.capture([{"id":"x","path":str(src),"basis":"fixture","format":"json"}],r/"pkg",r/"pkg"/"delivery",max_file=10)
            self.assertEqual(code,2); self.assertEqual(m["inputs"][0]["status"],"SIZE_CAP_EXCEEDED")

    def test_total_size_cap(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); a=r/"a"; b=r/"b"; a.write_bytes(b"{}"); b.write_bytes(b"{}")
            specs=[{"id":"a","path":str(a),"basis":"fixture","format":"json"},{"id":"b","path":str(b),"basis":"fixture","format":"json"}]
            code,m=MOD.capture(specs,r/"pkg",r/"pkg"/"delivery",max_total=2)
            self.assertEqual(code,2); self.assertEqual(m["inputs"][0]["status"],"CAPTURED")
            self.assertEqual(m["inputs"][1]["status"],"TOTAL_SIZE_CAP_EXCEEDED")

    def test_invalid_json_retained(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); src=r/"bad.json"; src.write_bytes(b"{bad")
            code,m=MOD.capture([{"id":"bad","path":str(src),"basis":"fixture","format":"json"}],r/"pkg",r/"pkg"/"delivery")
            self.assertEqual(code,2); self.assertEqual(m["inputs"][0]["parse_status"],"PARSE_FAILED")
            self.assertEqual((r/"pkg"/"delivery"/"capture_001"/"bad.json").read_bytes(),b"{bad")

    def test_allowlist_fixed_unique(self):
        ids=[x["id"] for x in MOD.INPUTS]; paths=[x["path"] for x in MOD.INPUTS]
        self.assertEqual(len(ids),11); self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len(paths),len(set(paths)))

    def test_no_recursive_or_network_apis(self):
        source=SCRIPT.read_text(encoding="utf-8")
        for token in [".rglob(",".glob(","os.walk(","os.scandir(","os.listdir(","urllib","requests","socket","jqdatasdk","subprocess"]:
            self.assertNotIn(token,source)

    def test_historical_pointer_change_is_not_failure_but_immutable_change_is(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); a=r/"a.json"; b=r/"b.csv"; a.write_text("{}",encoding="utf-8"); b.write_text("domain,x\nA,B\n",encoding="utf-8")
            specs=[
                {"id":"historical","path":str(a),"basis":"fixture","format":"json","expected_sha256":"0"*64,"sha_policy":"HISTORICAL_BASELINE_ONLY"},
                {"id":"immutable","path":str(b),"basis":"fixture","format":"csv","expected_sha256":"0"*64,"sha_policy":"IMMUTABLE_PIN"},
            ]
            code,m=MOD.capture(specs,r/"pkg",r/"pkg"/"delivery")
            self.assertEqual(code,2)
            self.assertEqual(m["inputs"][0]["pin_status"],"CHANGED_SINCE_HISTORICAL_BASELINE")
            self.assertEqual(m["inputs"][1]["pin_status"],"MISMATCH")

    def test_second_run_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); src=r/"a"; src.write_text("{}",encoding="utf-8")
            args=([{"id":"a","path":str(src),"basis":"fixture","format":"json"}],r/"pkg",r/"pkg"/"delivery")
            first,_=MOD.capture(*args); second,result=MOD.capture(*args)
            self.assertEqual(first,0); self.assertEqual(second,4)
            self.assertEqual(result["status"],"STOP_EXISTING_ONCE_OR_DELIVERY_ROOT")

if __name__ == "__main__": unittest.main()
