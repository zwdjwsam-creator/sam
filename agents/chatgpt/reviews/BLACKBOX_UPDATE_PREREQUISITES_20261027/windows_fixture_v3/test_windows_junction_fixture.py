import subprocess
import unittest
from pathlib import Path
from unittest import mock
import windows_junction_fixture as helper


class JunctionInvocationChecks(unittest.TestCase):
    def test_separate_argv_unicode_spaces_and_raw_capture(self):
        link = Path("C:/temporary 夹具/任务/loop")
        target = Path("C:/temporary 夹具/任务")
        result = subprocess.CompletedProcess([], 0, b"created", b"")
        with mock.patch.object(helper.subprocess, "run", return_value=result) as run:
            self.assertIs(helper.create_directory_junction(link, target), result)
        args, kwargs = run.call_args
        self.assertEqual(args, (["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],))
        self.assertEqual(kwargs, {"capture_output": True, "stdin": subprocess.DEVNULL, "timeout": 15})
        self.assertNotIn("text", kwargs)
        self.assertNotIn("encoding", kwargs)
        self.assertNotIn("shell", kwargs)

    def test_nonzero_gbk_bytes_are_lossless(self):
        diagnostic = "文件名、目录名或卷标语法不正确。".encode("gbk")
        result = subprocess.CompletedProcess([], 1, b"", diagnostic)
        with mock.patch.object(helper.subprocess, "run", return_value=result):
            with self.assertRaises(RuntimeError) as raised:
                helper.create_directory_junction("C:/link", "C:/target")
        message = str(raised.exception)
        self.assertIn("exit=1", message)
        self.assertIn("stderr_hex=" + diagnostic.hex(), message)

    def test_missing_streams_do_not_mask_exit(self):
        result = subprocess.CompletedProcess([], 2, None, None)
        with mock.patch.object(helper.subprocess, "run", return_value=result):
            with self.assertRaises(RuntimeError) as raised:
                helper.create_directory_junction("C:/link", "C:/target")
        self.assertIn("exit=2", str(raised.exception))
        self.assertIn("stderr_present=False", str(raised.exception))

    def test_shell_metacharacters_block_before_process(self):
        with mock.patch.object(helper.subprocess, "run") as run:
            for char in '"%!&|<>^\r\n':
                with self.subTest(char=repr(char)):
                    with self.assertRaisesRegex(RuntimeError, "UNSAFE_FIXTURE_PATH"):
                        helper.create_directory_junction("C:/link" + char, "C:/target")
            run.assert_not_called()

    def test_timeout_propagates_as_failure_with_raw_output(self):
        failure = subprocess.TimeoutExpired(["cmd.exe"], 15, output=b"partial", stderr=b"error")
        with mock.patch.object(helper.subprocess, "run", side_effect=failure):
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                helper.create_directory_junction("C:/link", "C:/target")
        self.assertIs(raised.exception, failure)
        self.assertEqual(raised.exception.output, b"partial")

    def test_invalid_utf8_error_bytes_are_not_decoded(self):
        diagnostic = b"\xff\x81\xfe"
        result = subprocess.CompletedProcess([], 1, b"\x80", diagnostic)
        with mock.patch.object(helper.subprocess, "run", return_value=result):
            with self.assertRaises(RuntimeError) as raised:
                helper.create_directory_junction("C:/link", "C:/target")
        self.assertIn("stdout_hex=80", str(raised.exception))
        self.assertIn("stderr_hex=ff81fe", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
