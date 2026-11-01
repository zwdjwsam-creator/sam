import io,json,tempfile,unittest
from pathlib import Path
from datetime import date,datetime
from types import SimpleNamespace
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
import freeze_calendar as c
import launch_calendar as l
import package_guard as g

def body(vals,typ=pa.date32(),name='trade_date'):
 sink=io.BytesIO();pq.write_table(pa.table({name:pa.array(vals,type=typ)}),sink);return sink.getvalue()
class CalendarTests(unittest.TestCase):
 def test_date_sequence_exact(self):
  b=body([date(2014,1,2),date(2014,1,3)]);r=c.decode(b);self.assertEqual(r['trade_days'],['2014-01-02','2014-01-03']);self.assertEqual(r['physical_row_positions'],[0,1]);self.assertFalse(r['calendar_complete'])
 def test_timestamp_midnight(self):self.assertEqual(c.decode(body([datetime(2014,1,2)],pa.timestamp('ns')))['rows'],1)
 def test_iso_string(self):self.assertEqual(c.decode(body(['2014-01-02'],pa.string()))['first'],'2014-01-02')
 def test_ordinal_refused(self):
  with self.assertRaisesRegex(c.Stop,'DATE_TYPE_NOT_ORDINAL'):c.decode(body([0,1],pa.int64()))
 def test_date_alias_not_invented(self):
  with self.assertRaisesRegex(c.Stop,'EXACT_TRADE_DATE'):c.decode(body([date(2014,1,2)],name='date'))
 def test_null_refused(self):
  with self.assertRaisesRegex(c.Stop,'NULL_CALENDAR'):c.decode(body([None]))
 def test_duplicate_refused(self):
  with self.assertRaisesRegex(c.Stop,'DUPLICATE'):c.decode(body([date(2014,1,2)]*2))
 def test_no_sort_repair(self):
  with self.assertRaisesRegex(c.Stop,'UNORDERED'):c.decode(body([date(2014,1,3),date(2014,1,2)]))
 def test_intraday_refused(self):
  with self.assertRaisesRegex(c.Stop,'NON_MIDNIGHT'):c.decode(body([datetime(2014,1,2,12)],pa.timestamp('ns')))
 def test_empty_refused(self):
  with self.assertRaisesRegex(c.Stop,'EXACT_TRADE_DATE'):c.decode(body([]))
 def test_reparse_component_refused(self):
  with tempfile.TemporaryDirectory() as d,patch.object(Path,'lstat',return_value=SimpleNamespace(st_mode=0,st_file_attributes=0x400)):
   with self.assertRaisesRegex(c.Stop,'REPARSE'):c.safe(Path(d))
 def test_only_derived_files_written_and_source_unchanged(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);src=d/'original.parquet';b=body([date(2014,1,2)]);src.write_bytes(b);out=d/'out';out.mkdir();c.collect(src,out,c.sha(b)[:16]);self.assertEqual(src.read_bytes(),b);self.assertEqual({x.name for x in out.iterdir()},{'SOURCE_IDENTITY.json','TRADE_DAY_SEQUENCE.json','CAPTURE_RESULT.json'});self.assertTrue(json.loads((out/'CAPTURE_RESULT.json').read_bytes())['no_original_body_copy'])
 def test_changed_registered_prefix_stops_preserves_identity(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);src=d/'original.parquet';src.write_bytes(body([date(2014,1,2)]));out=d/'out';out.mkdir()
   with self.assertRaisesRegex(c.Stop,'REGISTERED_HASH_PREFIX'):c.collect(src,out,'0'*16)
   self.assertTrue((out/'SOURCE_IDENTITY.json').exists());self.assertFalse((out/'TRADE_DAY_SEQUENCE.json').exists())
 def test_source_change_during_read_stops(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);src=d/'original.parquet';b=body([date(2014,1,2)]);src.write_bytes(b);out=d/'out';out.mkdir();old=Path.read_bytes;n=[0]
   def changed(p):
    if p==src:
     n[0]+=1;return b if n[0]==1 else b+b'x'
    return old(p)
   with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(c.Stop,'SOURCE_CHANGED'):c.collect(src,out,c.sha(b)[:16])
   self.assertFalse((out/'CAPTURE_RESULT.json').exists())
 def test_outputs_never_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';c.write_new(p,b'old')
   with self.assertRaises(FileExistsError):c.write_new(p,b'new')
   self.assertEqual(p.read_bytes(),b'old')
 def test_directory_is_not_a_source(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);out=d/'out';out.mkdir()
   with self.assertRaisesRegex(c.Stop,'NOT_REGULAR'):c.collect(d,out,'0'*16)
 def test_draft_native_entry_locked(self):
  with patch.object(g,'validate',side_effect=c.Stop('REVIEW_ONLY_NOT_DISPATCHED')),self.assertRaisesRegex(c.Stop,'REVIEW_ONLY_NOT_DISPATCHED'):c.main()
 def test_draft_outer_entry_locked(self):
  with patch.object(g,'validate',side_effect=c.Stop('REVIEW_ONLY_NOT_DISPATCHED')),self.assertRaisesRegex(c.Stop,'REVIEW_ONLY_NOT_DISPATCHED'):l.main()
class ReceiptTests(unittest.TestCase):
 def test_empty_fixture_directory_not_miscounted_as_file(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);(out/'fixture_tmp').mkdir();(out/'empty.stdout.txt').write_bytes(b'');c.local_readback(out)
   r=json.loads((out/'LOCAL_READBACK.json').read_bytes());self.assertEqual(r['files'],[{'path':'empty.stdout.txt','bytes':0,'sha256':c.sha(b'')}])
class PackageTests(unittest.TestCase):
 def fixture(self,root):
  (root/'x.py').write_bytes(b'pass\n')
  m={'task_id':'BLACKBOX_HISTORICAL_CALENDAR_FREEZE_20261101','files':[{'path':'x.py','bytes':5,'sha256':c.sha(b'pass\n')}]}
  (root/'PACKAGE.json').write_bytes(c.packed(m))
 def test_package_valid(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);self.fixture(d);self.assertEqual(g.manifest_at(d),c.sha((d/'PACKAGE.json').read_bytes()))
 def test_package_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);self.fixture(d);(d/'x.py').write_bytes(b'evil\n')
   with self.assertRaisesRegex(c.Stop,'PACKAGE_MEMBER_CHANGED'):g.manifest_at(d)
 def test_package_extra_refused(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);self.fixture(d);(d/'extra').write_bytes(b'')
   with self.assertRaisesRegex(c.Stop,'PACKAGE_EXACT_SET'):g.manifest_at(d)
 def test_parent_member_refused(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);self.fixture(d);m=json.loads((d/'PACKAGE.json').read_bytes());m['files'][0]['path']='../x.py';(d/'PACKAGE.json').write_bytes(c.packed(m))
   with self.assertRaisesRegex(c.Stop,'PACKAGE_MEMBERS'):g.manifest_at(d)
 def test_production_host_guard_before_fixed_drive_access(self):
  with patch.object(g.socket,'gethostname',return_value='UNAUTHORIZED_HOST'),self.assertRaisesRegex(c.Stop,'HOST'):g.validate(False)
 def test_production_rule_pin_change(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);q=d/'rule';q.write_bytes(b'old');(d/'RULE_PINS.json').write_bytes(c.packed({'files':[{'path':str(q),'bytes':3,'sha256':c.sha(b'old')}]}))
   with patch.object(g,'PACKAGE',d):
    self.assertEqual(g.rules()[0]['sha256'],c.sha(b'old'));q.write_bytes(b'new')
    with self.assertRaisesRegex(c.Stop,'OPERATIONAL_PIN_CHANGED'):g.rules()
if __name__=='__main__':unittest.main(verbosity=2)

