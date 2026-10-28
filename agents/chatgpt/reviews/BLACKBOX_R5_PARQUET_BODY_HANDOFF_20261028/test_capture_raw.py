import unittest,tempfile,json,hashlib,zipfile
from pathlib import Path
from unittest.mock import patch
import capture_raw as c
class RawHandoff(unittest.TestCase):
 def row(self,root,body=b'PAR1examplePAR1',name='a.parquet',action='CAPTURE'):
  p=root/'raw/stock'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
  return {'root':'R5','relative_path':'raw/stock/'+name,'bytes':len(body),'sha256':c.sha(body),'action':action}
 def test_exact_bytes_zip_and_source_unchanged(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);row=self.row(r);p=r/row['relative_path'];before=p.stat();out=r/'out'
   self.assertEqual(c.capture([row],{'R5':r},out),0)
   with zipfile.ZipFile(out/'raw_part_001.zip') as z:self.assertEqual(z.read('R5/'+row['relative_path']),p.read_bytes())
   self.assertEqual(p.stat().st_mtime_ns,before.st_mtime_ns)
 def test_real_retained_parquet_bytes_not_reencoded(self):
  f=Path(__file__).with_name('retained_failed_fixture.json');import base64
  b=base64.b64decode(json.loads(f.read_bytes())['content_base64'])
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);row=self.row(r,b);self.assertEqual(c.capture([row],{'R5':r},r/'out'),0)
   with zipfile.ZipFile(r/'out/raw_part_001.zip') as z:self.assertEqual(z.read('R5/'+row['relative_path']),b)
 def test_hash_drift_failure_kept(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);row=self.row(r);row['sha256']='0'*64
   self.assertEqual(c.capture([row],{'R5':r},r/'out'),2);self.assertTrue((r/'out/FAILURE_PRESERVED.json').exists())
 def test_existing_output_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);out=r/'out';out.mkdir()
   with self.assertRaisesRegex(c.Blocked,'EXISTING_OUTPUT'):c.capture([],{'R5':r},out)
 def test_path_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(c.Blocked,'SOURCE_PATH'):c.read_source(Path(d),{'relative_path':'../x.parquet'})
 def test_duplicate_plan_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);row=self.row(r);self.assertEqual(c.capture([row,row],{'R5':r},r/'out'),2)
 def test_existing_hub_body_reference_not_zipped(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);row=self.row(r,action='REUSE_HUB_BODY');self.assertEqual(c.capture([row],{'R5':r},r/'out'),0)
   self.assertFalse(list((r/'out').glob('*.zip')))
 def test_part_boundary_and_crc(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);rows=[self.row(r,b'12345678',str(i)+'.parquet') for i in range(3)]
   with patch.object(c,'MAX_SOURCE_PART',10):self.assertEqual(c.capture(rows,{'R5':r},r/'out'),0)
   self.assertEqual(len(list((r/'out').glob('*.zip'))),3)
 def test_unknown_file_never_read(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);row=self.row(r);unknown=r/'secret.txt';unknown.write_bytes(b'not read')
   original=Path.read_bytes
   def read(p):
    if p==unknown:raise AssertionError('unknown read')
    return original(p)
   with patch.object(Path,'read_bytes',read):self.assertEqual(c.capture([row],{'R5':r},r/'out'),0)
 def test_payload_plan_identity(self):
  rows=json.loads(Path(__file__).with_name('RAW_TRANSFER_PLAN.json').read_bytes())['rows']
  self.assertEqual(len(rows),1504);self.assertEqual(sum(r['action']=='REUSE_HUB_BODY' for r in rows),2)
if __name__=='__main__':unittest.main()
