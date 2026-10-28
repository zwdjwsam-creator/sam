import json, tempfile, unittest, types
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import acquire_daily as a

class EmptySlotContract(unittest.TestCase):
    def setup_layout(self,root):
        policy=a.load_slot_policy(root);records=[]
        for parent in {p.parent for p in policy}:
            parent.mkdir(parents=True,exist_ok=True)
            raw=parent/'registered.parquet';pd.DataFrame({'x':[1]}).to_parquet(raw)
            records.append({'path':str(raw),'status':'NON_PRICE_SCHEMA','columns':['x']})
        for p in policy:p.mkdir()
        return policy,[{'records':records}]
    def test_all_five_exact_empty_slots_recorded(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);r=a.check_registered_freshness(docs,root)
            self.assertEqual(len(r['slots']),5);self.assertFalse(r['source_absence_claim'])
            self.assertEqual(sum(x['classification']=='DECLARED_EMPTY_SLOT' for x in r['slots']),4)
            self.assertEqual(sum(x['classification']=='REVIEWED_EMPTY_LAYOUT_SLOT' for x in r['slots']),1)
            for x in r['slots']:
                self.assertEqual(x['entries_including_hidden'],0);self.assertFalse(x['historical_creator_proven'])
            self.assertTrue(all(not list(p.iterdir()) for p in policy))
    def test_declared_slot_hidden_file_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root)
            p=next(p for p in policy if p.name=='fund_nav');(p/'.hidden').write_bytes(b'kept')
            with self.assertRaisesRegex(a.Blocked,'BECAME_NONEMPTY'):a.check_registered_freshness(docs,root)
            self.assertEqual((p/'.hidden').read_bytes(),b'kept')
    def test_declared_slot_new_parquet_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root)
            p=next(p for p in policy if p.name=='fund_share');pd.DataFrame({'x':[1]}).to_parquet(p/'new.parquet')
            with self.assertRaisesRegex(a.Blocked,'BECAME_NONEMPTY'):a.check_registered_freshness(docs,root)
    def test_declared_slot_nested_empty_child_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);(next(iter(policy))/'nested').mkdir()
            with self.assertRaisesRegex(a.Blocked,'BECAME_NONEMPTY'):a.check_registered_freshness(docs,root)
    def test_unknown_empty_directory_still_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);(next(iter(policy)).parent/'not_registered').mkdir()
            with self.assertRaisesRegex(a.Blocked,'DIRECTORY_SET_UNPROVEN'):a.check_registered_freshness(docs,root)
    def test_same_basename_different_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);policy=a.load_slot_policy(root);p=root/'elsewhere/fund_nav';p.mkdir(parents=True)
            with self.assertRaisesRegex(a.Blocked,'DIRECTORY_SET_UNPROVEN'):a.check_reviewed_empty_slot(p,policy)
    def test_reviewed_layout_slot_not_declared_as_source(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);p=next(p for p in policy if p.name=='none_adj')
            r=a.check_reviewed_empty_slot(p,policy)
            self.assertEqual(r['classification'],'REVIEWED_EMPTY_LAYOUT_SLOT')
            self.assertIsNone(r['declaration_evidence']['lines'])
    def test_junction_reparse_attribute_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);policy,docs=self.setup_layout(root);p=next(iter(policy));s=p.lstat()
            fake=types.SimpleNamespace(st_file_attributes=0x400,st_mode=s.st_mode)
            with patch.object(Path,'lstat',return_value=fake),self.assertRaisesRegex(a.Blocked,'REPARSE_UNPROVEN'):
                a.check_reviewed_empty_slot(p,policy)
    def test_symlink_flag_blocks_without_following(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);policy,docs=self.setup_layout(root);p=next(iter(policy))
            with patch.object(Path,'is_symlink',return_value=True),self.assertRaisesRegex(a.Blocked,'REPARSE_UNPROVEN'):
                a.check_reviewed_empty_slot(p,policy)
    def test_read_permission_failure_preserved(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);p=next(iter(policy))
            with patch.object(a.os,'scandir',side_effect=PermissionError('fixture')),self.assertRaises(PermissionError):
                a.check_reviewed_empty_slot(p,policy)
    def test_mtime_drift_during_empty_check_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);p=next(iter(policy));original=a.os.scandir
            def mutate(path):
                import os
                s=path.stat();os.utime(path,ns=(s.st_atime_ns,s.st_mtime_ns+1000000000));return original(path)
            with patch.object(a.os,'scandir',side_effect=mutate),self.assertRaisesRegex(a.Blocked,'CHANGED_DURING_CHECK'):
                a.check_reviewed_empty_slot(p,policy)
    def test_new_unhandled_format_still_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'require_allowed_read'):
            root=Path(d);policy,docs=self.setup_layout(root);(next(iter(policy)).parent/'new.csv').write_text('x')
            with self.assertRaisesRegex(a.Blocked,'NEW_FORMAT_UNPROVEN'):a.check_registered_freshness(docs,root)
    def test_slot_report_has_no_absence_or_date_allowance(self):
        policy=json.loads(Path(a.__file__).with_name('EMPTY_SLOT_POLICY.json').read_text())
        self.assertTrue(policy['date_is_not_an_allow_rule']);self.assertFalse(policy['source_absence_claim'])
        self.assertEqual(policy['nonempty_reviewed_slot_action'],'BLOCK')
    def test_policy_path_traversal_rejected(self):
        p=json.loads(Path(a.__file__).with_name('EMPTY_SLOT_POLICY.json').read_text());p['slots'][0]['relative_path']='../outside'
        with patch.object(Path,'read_text',return_value=json.dumps(p)),self.assertRaisesRegex(a.Blocked,'SLOT_POLICY_PATH'):
            a.load_slot_policy(Path('root'))

if __name__=='__main__':unittest.main()
