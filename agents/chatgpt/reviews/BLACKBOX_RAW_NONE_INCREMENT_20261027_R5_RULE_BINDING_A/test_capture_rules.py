import unittest,tempfile,json,base64,hashlib
from pathlib import Path
from unittest.mock import patch
import capture_rules as c
class CaptureTests(unittest.TestCase):
 def test_all_exact_originals_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)/'root';out=Path(d)/'out';before={}
   for n in c.PATHS:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'BOM\r\n original\x00\xff');before[n]=p.read_bytes()
   self.assertEqual(c.capture(root,out),0);x=json.loads((out/'RULE_BODIES.json').read_text())
   for r in x['records']:self.assertEqual(base64.b64decode(r['content']),before[r['relative_path']]);self.assertEqual((root/r['relative_path']).read_bytes(),before[r['relative_path']])
 def test_missing_preserves_partial_exit2(self):
  with tempfile.TemporaryDirectory()as d:
   self.assertEqual(c.capture(Path(d)/'none',Path(d)/'out'),2);self.assertEqual(len(json.loads((Path(d)/'out/RULE_BODIES.json').read_text())['records']),6)
 def test_existing_output_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaisesRegex(RuntimeError,'NO_REPLAY'):c.capture(Path(d),Path(d))
 def test_cap_blocks_no_extra_read(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)/'r';p=root/c.PATHS[0];p.parent.mkdir(parents=True);p.write_bytes(b'xx')
   with patch.object(c,'CAP',1):self.assertEqual(c.capture(root,Path(d)/'out'),2)
 def test_unknown_files_never_read(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)/'r';root.mkdir();p=root/'credentials';p.write_bytes(b'untouched');self.assertEqual(c.capture(root,Path(d)/'out'),2);self.assertEqual(p.read_bytes(),b'untouched')
if __name__=='__main__':unittest.main()
