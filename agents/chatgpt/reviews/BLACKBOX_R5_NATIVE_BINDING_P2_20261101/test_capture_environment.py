import unittest,tempfile,types,stat
from pathlib import Path
import capture_environment as c

class Tests(unittest.TestCase):
 def test_regular(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'abc');self.assertEqual(c.read_one(p),b'abc')
 def test_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'a');q=Path(d)/'q';q.symlink_to(p)
   with self.assertRaisesRegex(RuntimeError,'REPARSE'):c.read_one(q)
 def test_reparse_attribute(self):
  self.assertTrue(c.blocked_reparse(types.SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400)))
 def test_symlink_mode(self):
  self.assertTrue(c.blocked_reparse(types.SimpleNamespace(st_mode=stat.S_IFLNK,st_file_attributes=0)))
 def test_oversize(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'x'*(2*1024*1024+1))
   with self.assertRaises(RuntimeError):c.read_one(p)
 def test_write_readback_and_collision(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';c.write_exact(p,b'a');self.assertEqual(p.read_bytes(),b'a')
   with self.assertRaises(FileExistsError):c.write_exact(p,b'b')
 def test_once_outside_capture(self):
  with tempfile.TemporaryDirectory() as d:
   out=c.reserve(Path(d));out.rmdir()
   with self.assertRaises(FileExistsError):c.reserve(Path(d))
 def test_existing_capture(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'capture_001').mkdir()
   with self.assertRaisesRegex(RuntimeError,'CAPTURE_EXISTS'):c.reserve(Path(d))
 def test_versions(self):self.assertEqual(set(c.package_versions()),{'pandas','pyarrow','numpy'})
 def test_fixed_inputs(self):
  self.assertEqual(len(c.INPUTS),len(set(c.INPUTS)));self.assertEqual(len(c.POINTERS),4)
  self.assertFalse(any('secret' in x.lower() for x in c.INPUTS))
 def test_native_main_blocked_on_linux(self):
  with self.assertRaisesRegex(RuntimeError,'WRONG_HOST'):c.main()

if __name__=='__main__':unittest.main(verbosity=2)
