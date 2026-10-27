"""Read exactly one already downloaded price batch; no pandas/SDK/business import."""
import base64,hashlib,json,os,platform,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SOURCE=Path(r'E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R4\raw\stock\2026-10-27_03360_R4.parquet')
OUT=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R4_FAILED_BAR_BODY_20261027\capture_001')
EXPECTED='fb1a0ccb4918e6035d7e6a3695d6fbac6cbf9818c3ea2ca01bcf7928b2e8b2c7'
def read_bound(path,expected,size):
    before=path.lstat()
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)() or getattr(before,'st_file_attributes',0)&0x400:raise RuntimeError('SOURCE_LINK_UNPROVEN')
    if before.st_size!=size or size>2*1024*1024:raise RuntimeError('SOURCE_LENGTH_DRIFT')
    with path.open('rb') as f:b=f.read(size+1)
    after=path.lstat()
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise RuntimeError('SOURCE_STAT_DRIFT')
    if len(b)!=size or hashlib.sha256(b).hexdigest()!=expected:raise RuntimeError('SOURCE_HASH_DRIFT')
    return b

def capture(path,out,expected,size):
    if out.exists():raise RuntimeError('EXISTING_OUTPUT_NO_REPLAY')
    b=read_bound(path,expected,size)
    envelope={'schema':'BLACKBOX_EXACT_RAW_BODY_R1','source_path':str(path),'bytes':len(b),'sha256':expected,'encoding':'base64','content':base64.b64encode(b).decode('ascii'),'source_modified':False,'supplier_calls':0,'business_modules_imported':False,'order_allowed':False}
    if base64.b64decode(envelope['content'],validate=True)!=b:raise RuntimeError('ENCODING_MISMATCH')
    out.mkdir(parents=True,exist_ok=False)
    with (out/'RAW_BODY.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(envelope,f,ensure_ascii=False,indent=2);f.write('\n')
    stored=json.loads((out/'RAW_BODY.json').read_text(encoding='utf-8'))
    if base64.b64decode(stored['content'],validate=True)!=b:raise RuntimeError('LOCAL_READBACK_MISMATCH')
    return {'status':'EXACT_RAW_BODY_CAPTURED_NOT_PRICE_ACCEPTANCE','bytes':size,'sha256':expected,'supplier_calls':0,'order_allowed':False}

class Controls(unittest.TestCase):
    def test_exact_body_and_readonly_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'PAR1\x00\xff');h=hashlib.sha256(p.read_bytes()).hexdigest();out=Path(d)/'out';s=p.stat();r=capture(p,out,h,6)
            self.assertEqual(base64.b64decode(json.loads((out/'RAW_BODY.json').read_text())['content']),p.read_bytes());self.assertEqual(s.st_mtime_ns,p.stat().st_mtime_ns);self.assertEqual(r['supplier_calls'],0)
    def test_hash_mismatch_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'x');out=Path(d)/'out'
            with self.assertRaisesRegex(RuntimeError,'HASH_DRIFT'):capture(p,out,'0'*64,1)
            self.assertFalse(out.exists())
    def test_length_mismatch_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'x');out=Path(d)/'out'
            with self.assertRaisesRegex(RuntimeError,'LENGTH_DRIFT'):capture(p,out,'0'*64,2)
            self.assertFalse(out.exists())
    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'x');out=Path(d)/'out';out.mkdir();(out/'kept').write_bytes(b'kept')
            with self.assertRaisesRegex(RuntimeError,'NO_REPLAY'):capture(p,out,'0'*64,1)
            self.assertEqual((out/'kept').read_bytes(),b'kept')
    def test_link_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'x')
            with patch.object(Path,'is_symlink',return_value=True),self.assertRaisesRegex(RuntimeError,'LINK_UNPROVEN'):read_bound(p,'0'*64,1)

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--self-test']:unittest.main(argv=[sys.argv[0]],verbosity=2)
    else:
        if sys.argv[1:]:raise RuntimeError('ARGUMENTS_NOT_ALLOWED')
        if platform.system()!='Windows' or platform.node().upper()!='ZHANGWEI':raise RuntimeError('WRONG_HOST')
        if SOURCE.resolve(strict=True)!=SOURCE:raise RuntimeError('SOURCE_PHYSICAL_PATH_UNPROVEN')
        print(json.dumps(capture(SOURCE,OUT,EXPECTED,15489)))
