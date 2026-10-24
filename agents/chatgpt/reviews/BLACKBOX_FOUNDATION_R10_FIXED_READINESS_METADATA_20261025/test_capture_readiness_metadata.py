import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import capture_readiness_metadata as c

class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name) / 'input.json'
        self.out = Path(self.tmp.name) / 'output.json'
    def run_capture(self, raw):
        self.p.write_bytes(raw)
        return c.capture_one(self.p, self.out)
    def test_original_bytes(self):
        raw = b'\xef\xbb\xbf{\r\n "cursor": "2026-09-24"\r\n}\r\n'
        r = self.run_capture(raw)
        self.assertEqual(r['bytes'], len(raw)); self.assertEqual(self.out.read_bytes(), raw)
    def test_missing_is_not_source_absence(self):
        r = c.capture_one(self.p, self.out)
        self.assertIs(r['source_absence_claim_allowed'], False); self.assertFalse(self.out.exists())
    def test_duplicate_not_exported(self):
        r = self.run_capture(b'{"status":"FAIL","status":"PASS"}')
        self.assertEqual(r['status'], 'INVALID_OR_DUPLICATE_JSON_NOT_EXPORTED'); self.assertFalse(self.out.exists())
    def test_invalid_not_exported(self):
        r = self.run_capture(b'{bad')
        self.assertEqual(r['status'], 'INVALID_OR_DUPLICATE_JSON_NOT_EXPORTED')
    def test_secrets_never_hashed_or_exported(self):
        for raw in [b'{"detail":{"token":"example-sensitive-value"}}', b'{"log":"Authorization: Bearer abcdefghijklmnop"}']:
            r = self.run_capture(raw)
            self.assertEqual(r, {'status':'POTENTIAL_SECRET_NOT_EXPORTED'}); self.assertFalse(self.out.exists())
    def test_oversized_not_exported(self):
        with patch.object(c, 'LIMIT', 4):
            self.assertEqual(self.run_capture(b'{"x":1}')['status'], 'FILE_TYPE_OR_SIZE_REFUSED')
    def test_no_replay_overwrite(self):
        out = Path(self.tmp.name) / 'delivery'; out.mkdir()
        with patch.object(c, 'OUT', out), self.assertRaises(FileExistsError):
            c.main()
    def test_locator_not_followed(self):
        self.run_capture(b'{"credential_locator":"E:/BLACKBOX/config/secrets/account.txt"}')
        self.assertTrue(self.out.exists())

if __name__ == '__main__':
    r = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests_run':r.testsRun, 'passed':r.wasSuccessful(), 'scope':'FIXED_METADATA_CAPTURE_TEMPFILES_ONLY'}))
    raise SystemExit(0 if r.wasSuccessful() else 1)
