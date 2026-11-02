"""Native-safe C: fixtures only. No E: data, supplier, network or admission."""
from pathlib import Path
from datetime import datetime
import copy, io, json, math, os, tempfile, unittest
import observe as o
import guard as g


def raw(rows=1,code='002270.XSHE',day='2026-10-15',**changes):
    values={f:([1.]*rows) for f in o.FIELDS[2:]}
    values.update(open=[17.87]*rows,high_limit=[19.82]*rows,low_limit=[16.22]*rows,
                  volume=[14076869.]*rows,money=[254286654.36]*rows,paused=[0.]*rows)
    values.update(time=[datetime.fromisoformat(day)]*rows,code=[code]*rows,__index_level_0__=list(range(rows)))
    values.update(changes)
    t=o.pa.Table.from_pydict(values,schema=o.SCHEMA)
    b=io.BytesIO();o.pq.write_table(t,b);return b.getvalue()

def universe(day='2026-10-15',code='002270.XSHE',start='1990-01-01'):
    return dict(request=1,date=day,codes=[code],lifecycle={code:dict(start_date=start+' 00:00:00',end_date='2200-01-01 00:00:00')})

def prereg():
    return dict(dates=['2026-09-29','2026-10-15','2026-10-26'],exchanges=['XSHG','XSHE'],fields=['money','volume'],
      candidate_multipliers_applied_to_raw_sum_after_explicit_official_unit_normalization=[1,100,1000,10000])

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_readonly_identity_and_bytes(self):
        p=self.root/'x';p.write_bytes(b'abc');before=p.stat().st_mtime_ns
        b,m=o.read_source(p);self.assertEqual(b,b'abc');self.assertEqual(m['sha256'],o.sha(b));self.assertEqual(before,p.stat().st_mtime_ns)
    def test_resource_cap(self):
        p=self.root/'large'
        with p.open('wb') as f:f.truncate(o.MAX_FILE+1)
        with self.assertRaises(o.Blocked):o.read_source(p)
    def test_nonregular_rejected(self):
        with self.assertRaises(o.Blocked):o.read_source(self.root)
    def test_missing_exact_path(self):
        with self.assertRaises(FileNotFoundError):o.read_source(self.root/'absent')
    def test_package_good_and_tamper(self):
        p=self.root/'a.py';p.write_bytes(b'pass\n');m=dict(task_id=o.TASK,files=[dict(path='a.py',bytes=5,sha256=o.sha(p.read_bytes()))])
        (self.root/'PACKAGE.json').write_bytes(o.packed(m));self.assertEqual(g.package_sha(self.root),o.sha(o.packed(m)))
        p.write_bytes(b'fail\n')
        with self.assertRaises(o.Blocked):g.package_sha(self.root)
    def test_package_traversal(self):
        (self.root/'PACKAGE.json').write_bytes(o.packed(dict(task_id=o.TASK,files=[dict(path='../bad',bytes=0,sha256=o.sha(b''))])))
        with self.assertRaises(o.Blocked):g.package_sha(self.root)
    def test_output_exclusive_no_overwrite(self):
        w=o.Output(self.root);w.json('x.json',{});
        with self.assertRaises(FileExistsError):w.json('x.json',{})
    def test_audit_write_outside_capture(self):
        check=g.audit_checker([self.root])
        with self.assertRaises(o.Safety):check('open',(str(self.root.parent/'forbidden'),'w',os.O_WRONLY))
    def test_audit_scoped_write_allowed(self):
        g.audit_checker([self.root])('open',(str(self.root/'ok'),'w',os.O_WRONLY))
    def test_audit_network_forbidden(self):
        with self.assertRaises(o.Safety):g.audit_checker([self.root])('socket.connect',())
    def test_audit_unreviewed_subprocess(self):
        with self.assertRaises(o.Safety):g.audit_checker([self.root])('subprocess.Popen',('x',['x'],None,None))
    def test_audit_source_enumeration(self):
        with self.assertRaises(o.Safety):g.audit_checker([self.root])('os.scandir',('E:\\BLACKBOX\\STAGING',))
    def test_audit_rename_forbidden(self):
        with self.assertRaises(o.Safety):g.audit_checker([self.root])('os.rename',('a','b'))
    def test_ack_blob_binding(self):
        import hashlib
        b=b'ack';r=dict(ack_bytes=3,ack_sha256=o.sha(b),ack_blob_sha=hashlib.sha1(b'blob 3\0'+b).hexdigest(),git_commit='a'*40)
        g.check_ack_upload(b,r)
        r['ack_blob_sha']='0'*40
        with self.assertRaises(o.Blocked):g.check_ack_upload(b,r)


class DataTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def profile(self,changes=None):
        d=raw(**(changes or {}));ref=dict(source_id='S',expected_bytes=len(d),expected_sha256=o.sha(d),expected_physical_rows=1,indexed_session='2026-10-15',quarantined_positions=[],sample=True)
        p=o.Profile(o.Output(self.root),['2026-10-15'],set(),prereg(),{'2026-10-15':universe()});return p,ref,d
    def test_exact_sample(self):
        p,r,_=self.profile();d=raw(rows=80);r.update(expected_bytes=len(d),expected_sha256=o.sha(d),expected_physical_rows=80)
        p.add(r,d);p.out.close();self.assertEqual(p.sample['physical_row'],68);self.assertEqual(p.rows,80)
    def test_hash_mismatch_before_decode(self):
        p,r,d=self.profile();r['expected_sha256']='0'*64
        with self.assertRaises(o.Blocked):p.add(r,d)
    def test_schema_not_alias(self):
        p,r,d=self.profile();t=o.pa.table({'date':[datetime(2026,10,15)],'code':['002270.XSHE']});b=io.BytesIO();o.pq.write_table(t,b);d=b.getvalue();r.update(expected_bytes=len(d),expected_sha256=o.sha(d))
        with self.assertRaises(o.Blocked):p.add(r,d)
    def test_null_price_flagged_retained(self):
        p,r,d=self.profile({'open':[None]});p.add(r,d);p.out.close();self.assertEqual(p.anomalies['open:NULL'],1);self.assertEqual(p.rows,1)
    def test_nan_and_infinity(self):
        self.assertIn('money:NON_FINITE',o.flags(dict(paused=0.,open=1.,high_limit=float('inf'),low_limit=1.,volume=0.,money=float('nan'))))
    def test_status_outside_binary(self):
        self.assertIn('STATUS_OUTSIDE_0_1',o.flags(dict(paused=2.,open=2.,high_limit=3.,low_limit=1.,volume=1.,money=2.)))
    def test_reversed_limits(self):
        self.assertIn('UPPER_NOT_ABOVE_LOWER',o.flags(dict(paused=0.,open=2.,high_limit=1.,low_limit=3.,volume=1.,money=2.)))
    def test_paused_open_not_used_to_admit(self):
        self.assertNotIn('UNPAUSED_OPEN_OUTSIDE_OBSERVED_BOUNDS',o.flags(dict(paused=1.,open=99.,high_limit=3.,low_limit=1.,volume=0.,money=0.)))
    def test_signed_zero_encoding(self):
        self.assertNotEqual(o.float_value(0.)['ieee754'],o.float_value(-0.)['ieee754'])
    def test_no_large_value_cutoff(self):
        self.assertEqual(o.float_value(1e200)['state'],'FINITE')
    def test_duplicate_rows_not_suppressed(self):
        p,r,d=self.profile();p.add(r,d);r=dict(r,source_id='T');p.add(r,d);p.out.close();self.assertEqual(p.rows,2);self.assertEqual(len(next(iter(p.keys.values()))),2)
    def test_physical_positions_not_pandas_index(self):
        p,r,d=self.profile({'__index_level_0__':[8]})
        with self.assertRaises(o.Blocked):p.add(r,d)
    def test_nonmidnight_is_retained_flag(self):
        p,r,d=self.profile({'time':[datetime(2026,10,15,9)]});p.add(r,d);p.out.close();self.assertEqual(p.anomalies['NULL_NONMIDNIGHT_OR_CELL_TIME_MISMATCH'],1)
    def test_quarantined_row_still_observed(self):
        p,r,d=self.profile();r['quarantined_positions']=[0];p.add(r,d);p.out.close();self.assertEqual(p.quarantine,1)
    def test_compact_row_has_exact_bits_and_lineage(self):
        import struct
        p,r,d=self.profile();p.add(r,d);p.out.close()
        row=json.loads((self.root/'ROWS_2026-10-15.jsonl').read_bytes())
        self.assertEqual(row[:3],['S',0,'002270.XSHE']);self.assertEqual(row[4][1],struct.pack('>d',17.87).hex())


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.days=['2026-09-28','2026-09-29','2026-09-30','2026-10-08','2026-10-09','2026-10-12'];self.u=universe('2026-10-09',start='2026-09-28')
    def test_ipo_fifth_included(self):self.assertEqual(o.classify('002270.XSHE','2026-10-09',self.u,self.days,set())['label'],'NO_LIMIT_CANDIDATE')
    def test_sixth_candidate_only(self):self.assertEqual(o.classify('002270.XSHE','2026-10-12',dict(self.u,date='2026-10-12'),self.days,set())['label'],'LIMITED_CANDIDATE_PENDING_EXCEPTIONS')
    def test_no_master_never_default_limited(self):self.assertEqual(o.classify('002270.XSHE','2026-10-09',None,self.days,set())['reason'],'UNKNOWN_MASTER')
    def test_explicit_exception(self):self.assertEqual(o.classify('002270.XSHE','2026-10-12',dict(self.u,date='2026-10-12'),self.days,{('002270.XSHE','2026-10-12')})['label'],'NO_LIMIT_CANDIDATE')
    def test_cdr_hold(self):self.assertEqual(o.classify('689009.XSHG','2026-10-09',None,self.days,set())['label'],'EXCLUDED_UNSUPPORTED_OR_CDR')
    def test_302132_single_exception(self):self.assertEqual(o.board('302132.XSHE'),('CHINEXT_SINGLE_EXCEPTION','0.20'));self.assertEqual(o.board('302133.XSHE'),('UNSUPPORTED',None))
    def test_unknown_listing_calendar(self):
        u=universe('2026-10-09',start='2026-09-27');self.assertEqual(o.classify('002270.XSHE','2026-10-09',u,self.days,set())['label'],'UNKNOWN')
    def test_universe_duplicate_keys(self):
        with self.assertRaises(o.Blocked):o.universe(b'{"date":1,"date":2}','2026-10-15')
    def test_universe_validity(self):
        with self.assertRaises(o.Blocked):o.universe(o.packed(universe(start='2027-01-01')),'2026-10-15')
    def test_st_unknown_no_fabrication(self):self.assertEqual(o.classify('002270.XSHE','2026-10-09',self.u,self.days,set())['st_status'],'UNKNOWN_NOT_CAPTURED')
    def test_wrong_snapshot_day(self):self.assertEqual(o.classify('002270.XSHE','2026-10-12',self.u,self.days,set())['reason'],'UNKNOWN_MASTER')
    def test_unordered_calendar(self):self.assertEqual(o.classify('002270.XSHE','2026-10-09',self.u,list(reversed(self.days)),set())['reason'],'UNKNOWN_CALENDAR')


class ScaleTests(unittest.TestCase):
    def setUp(self):
        self.p=prereg();self.local={d+'|'+ex:dict(money='1',volume='1',comparison_blockers=[]) for d in self.p['dates'] for ex in self.p['exchanges']}
        self.official=dict(scope_compatible_and_complete=True,cells={k:dict(money='1',volume='1',scope_bound=True) for k in self.local})
    def test_unique_base_scale(self):self.assertEqual(o.compare_scales(self.local,self.official,self.p)['multipliers'],dict(money=1,volume=1))
    def test_unbound_reference(self):self.assertEqual(o.compare_scales(self.local,{},self.p)['status'],'UNRESOLVED')
    def test_missing_one_date(self):del self.official['cells']['2026-10-26|XSHE'];self.assertEqual(o.compare_scales(self.local,self.official,self.p)['status'],'UNRESOLVED')
    def test_zero_official(self):self.official['cells']['2026-10-26|XSHE']['money']='0';self.assertEqual(o.compare_scales(self.local,self.official,self.p)['status'],'UNRESOLVED')
    def test_scope_blocker(self):self.local['2026-10-26|XSHE']['comparison_blockers']=['DUPLICATE'];self.assertEqual(o.compare_scales(self.local,self.official,self.p)['status'],'UNRESOLVED')
    def test_adjacent_10x_condition_is_strict(self):
        for c in self.official['cells'].values():c.update(money='101',volume='101')
        self.assertEqual(o.compare_scales(self.local,self.official,self.p)['status'],'UNRESOLVED')
    def test_scale_is_not_unit_certificate(self):self.assertFalse(o.compare_scales(self.local,self.official,self.p)['unit_admitted'])


class CaptureFailureTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def cat(self):
        d=raw();r=dict(source_id='S',kind='STOCK',path=str(self.root/'source'),expected_bytes=len(d),expected_sha256=o.sha(d),expected_physical_rows=1,indexed_session='2026-10-15',quarantined_positions=[],sample=False)
        return dict(historical=[],universes=[],stock=[r],review_sessions=['2026-10-15'],no_limit_exceptions=[],preregistration=prereg(),official_reference={},data_sessions=['2026-10-15']),d
    def reader(self,d):return d,dict(bytes=len(d),sha256=o.sha(d),metadata=dict(size=len(d),dev=1,ino=1,mtime_ns=1))
    def test_drift_returns_three_and_retains_after(self):
        c,d=self.cat();calls=[]
        def reader(path):calls.append(path);return self.reader(d if len(calls)==1 else d+b'changed')
        rc=o.collect(c,self.root,reader);self.assertEqual(rc,3)
        self.assertFalse(json.loads((self.root/'SOURCE_AFTER.json').read_bytes())['files'][0]['equal_before'])
    def test_missing_path_is_bounded_not_absence(self):
        c,d=self.cat()
        def reader(path):raise FileNotFoundError(path)
        self.assertEqual(o.collect(c,self.root,reader),2)
        self.assertEqual(json.loads((self.root/'OBSERVATION_RESULT.json').read_bytes())['source_absence_claims'],0)
    def test_mismatch_preserves_two_snapshots(self):
        c,d=self.cat();c['stock'][0]['expected_sha256']='0'*64
        self.assertEqual(o.collect(c,self.root,lambda path:self.reader(d)),2)
        self.assertTrue((self.root/'SOURCE_BEFORE.json').is_file());self.assertTrue((self.root/'SOURCE_AFTER.json').is_file())


if __name__=='__main__':
    if os.name=='nt':g.audit([g.CONTROL])
    unittest.main(verbosity=2)
