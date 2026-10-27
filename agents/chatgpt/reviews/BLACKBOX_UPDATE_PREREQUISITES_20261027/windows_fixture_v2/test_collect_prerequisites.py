import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import os
import subprocess

spec=importlib.util.spec_from_file_location("collector",Path(__file__).with_name("collect_prerequisites.py"))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class Checks(unittest.TestCase):
    def directory_link(self, link, target):
        """Use a real unprivileged junction on Windows; real symlink elsewhere."""
        if os.name == "nt":
            if any(c in str(link)+str(target) for c in '"%!'):
                raise RuntimeError("UNSAFE_FIXTURE_PATH")
            command = 'mklink /J "' + str(link) + '" "' + str(target) + '"'
            result = subprocess.run(["cmd.exe", "/d", "/c", command],
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError("JUNCTION_FIXTURE_CREATION_FAILED: " + result.stderr)
            self.assertTrue(c.reparse(link))
            self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)
        else:
            link.symlink_to(target, target_is_directory=True)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.root=self.base/"root";self.root.mkdir()
        self.out=self.base/"output"
        self.plan={"guard_paths":["guard.json"],"exact_paths":{"SAM":["x.py"],"ZHANGWEI":["x.py","commit.json"]},
                   "commit_relative_path":"commit.json","candidate_relative_root":"candidate"}
        (self.root/"guard.json").write_text('{"v":1}')
        (self.root/"x.py").write_bytes(b"def f():\r\n    return 7\r\n")
        (self.root/"\u4efb\u52a1").mkdir()
    def run_capture(self,role="ZHANGWEI",known=None):
        return c.collect(self.root,self.out,role,self.plan,known or {})
    def test_exact_bytes_source_preserved(self):
        before=(self.root/"x.py").read_bytes()
        r=self.run_capture(); rec=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertEqual((self.out/rec["captured_body"]).read_bytes(),before)
        self.assertEqual((self.root/"x.py").read_bytes(),before)
        self.assertEqual(r["guard_changes"],[])
        self.assertFalse(r["business_modules_imported"])
    def test_known_body_reused_without_duplicate(self):
        b=(self.root/"x.py").read_bytes();r=self.run_capture(known={c.digest(b):["pinned/original.py"]})
        x=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertEqual(x["status"],"REUSED_HUB_BODY");self.assertNotIn("captured_body",x)
    def test_missing_path_is_not_source_absence(self):
        r=self.run_capture()
        x=next(x for x in r["records"] if x["source_path"].endswith("commit.json"))
        self.assertEqual(x["status"],"NOT_FOUND_AT_EXACT_PATH")
        self.assertFalse(x["source_absence_claim_allowed"])
    def test_existing_output_refused(self):
        self.out.mkdir();(self.out/"preserve").write_text("keep")
        with self.assertRaises(FileExistsError):self.run_capture()
        self.assertEqual((self.out/"preserve").read_text(),"keep")
    def test_external_link_blocked(self):
        outside=self.base/"outside";outside.mkdir();(outside/"x.py").write_text("outside")
        self.directory_link(self.root/"view", outside)
        self.plan["exact_paths"]["ZHANGWEI"]=["view/x.py","commit.json"]
        r=self.run_capture();x=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertEqual(x["status"],"BLOCKED_OR_READ_ERROR")
        self.assertNotIn("sha256",x)
    def test_reference_not_producer_certificate(self):
        t=self.root/"\u4efb\u52a1"/"R45_test";t.mkdir()
        (t/"REPORT.md").write_text(c.NEEDLES[0])
        r=self.run_capture("SAM")
        hit=r["task_lookup"]["matches"][0]
        self.assertEqual(hit["evidence_role"],"REFERENCE_ONLY_NOT_PRODUCER_ATTESTATION")
        self.assertFalse(r["task_lookup"]["producer_execution_proven"])
    def test_unrelated_task_not_read(self):
        t=self.root/"\u4efb\u52a1"/"UNRELATED";t.mkdir()
        (t/"REPORT.md").write_text(c.NEEDLES[0])
        r=self.run_capture("SAM");self.assertEqual(r["task_lookup"]["matches"],[])
    def test_cycle_link_not_followed_and_disclosed(self):
        t=self.root/"\u4efb\u52a1"/"R45_test";t.mkdir()
        self.directory_link(t/"loop", t)
        r=self.run_capture("SAM")
        self.assertTrue(r["task_lookup"]["limits"])
        self.assertFalse(r["task_lookup"]["search_complete_within_declared_scope"])
    def test_file_budget_is_explicit_incomplete(self):
        t=self.root/"\u4efb\u52a1"/"R45_test";t.mkdir()
        (t/"one.json").write_text("{}");(t/"two.json").write_text("{}")
        with mock.patch.object(c,"MAX_SEARCH_FILES",1):r=self.run_capture("SAM")
        self.assertIn("FILE_LIMIT",r["task_lookup"]["limits"])
    def test_secret_pattern_blocks_before_digest_or_copy(self):
        (self.root/"x.py").write_text("ghp_"+"A"*36)
        r=self.run_capture();x=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertEqual(x["reason"],"SECRET_PATTERN_BLOCKED")
        self.assertNotIn("sha256",x);self.assertNotIn("captured_body",x)
    def test_dynamic_checkpoint_outside_candidate_blocked(self):
        p=self.root/"outside.json";p.write_text("{}")
        (self.root/"commit.json").write_text(json.dumps({"checkpoint_path":str(p)}))
        r=self.run_capture()
        self.assertTrue(any(x.get("status")=="BLOCKED_OUTSIDE_CANDIDATE" for x in r["records"]))
    def test_dynamic_bound_metadata_capture(self):
        d=self.root/"candidate"/"r";d.mkdir(parents=True)
        for name in ["RELEASE.json","SEAL.json","MANIFEST.json","CHECKPOINT.json"]:(d/name).write_text("{}")
        (self.root/"commit.json").write_text(json.dumps({"checkpoint_path":str(d/"CHECKPOINT.json"),"release_root":str(d)}))
        r=self.run_capture()
        self.assertTrue(any(x["source_path"]==str(d/"CHECKPOINT.json") for x in r["records"]))
    def test_guard_change_is_not_hidden(self):
        original=c.capture
        def altered(root,p,out,known,records):
            result=original(root,p,out,known,records)
            (root/"guard.json").write_text('{"v":2}')
            return result
        with mock.patch.object(c,"capture",altered):r=self.run_capture()
        self.assertEqual(len(r["guard_changes"]),1)
    def test_large_file_not_silently_truncated(self):
        with mock.patch.object(c,"MAX_FILE",5):r=self.run_capture()
        x=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertEqual(x["reason"],"SIZE_LIMIT")
    def test_credentials_never_read(self):
        d=self.root/"\u914d\u7f6e"/"secrets"/"\u5df2\u9a8c\u8bc1";d.mkdir(parents=True)
        p=d/"\u805a\u5bbd\u8d26\u53f7.txt";p.write_text("private")
        self.assertFalse(c.permitted(self.root,p))
        r=self.run_capture();self.assertFalse(r["credential_contents_read"])
        self.assertTrue(r["credential_locator_present_only"])
    def test_ast_read_does_not_execute_source(self):
        marker=self.base/"executed"
        (self.root/"x.py").write_text("raise RuntimeError('MUST_NOT_EXECUTE')")
        r=self.run_capture()
        x=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertTrue(x["source_parsed_only_not_executed"])
        self.assertFalse(marker.exists())
    def test_source_changed_during_read_is_preserved_as_failure(self):
        original=Path.read_bytes
        def changed(p):
            b=original(p)
            if p==self.root/"x.py":
                p.write_bytes(b+b"#changed\n")
            return b
        with mock.patch.object(Path,"read_bytes",changed):r=self.run_capture()
        x=next(x for x in r["records"] if x["source_path"].endswith("x.py"))
        self.assertEqual(x["reason"],"SOURCE_CHANGED_DURING_READ")
        self.assertNotIn("captured_body",x)

if __name__=="__main__":unittest.main()

