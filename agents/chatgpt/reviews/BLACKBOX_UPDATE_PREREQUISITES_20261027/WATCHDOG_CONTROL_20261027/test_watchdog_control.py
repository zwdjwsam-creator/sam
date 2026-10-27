import unittest
from pathlib import PureWindowsPath
from unittest.mock import patch
import subprocess
import base64
import watchdog_control as w

class PolicyChecks(unittest.TestCase):
    def action(self,name='watchdog_after_resume.ps1'):
        return {'Execute':r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                'Arguments':'-NoProfile -File "'+w.ARCH+'\\'+name+'"'}
    def test_exact_watcher_action(self):
        self.assertEqual(w.action_kind(self.action()),'WATCHER')
    def test_same_name_outside_archive_not_authorized(self):
        a=self.action();a['Arguments']=r'-File "C:\other\watchdog_after_resume.ps1"'
        self.assertIsNone(w.action_kind(a))
    def test_encoded_or_command_payload_not_authorized(self):
        for arg in ['-EncodedCommand AAA','-Command "echo -File '+w.ARCH+'\\watchdog_after_resume.ps1"']:
            a=self.action();a['Arguments']=arg;self.assertIsNone(w.action_kind(a))
    def test_unknown_or_mixed_actions_not_authorized(self):
        self.assertIsNone(w.task_kind({'Actions':[self.action(),{'Execute':'unrelated.exe','Arguments':''}]}))
        self.assertIsNone(w.task_kind({'TaskName':'watchdog','Actions':[]}))
    def test_direct_driver_task_disable_only_kind(self):
        a={'Execute':r'E:\BLACKBOX\.venv\Scripts\python.exe','Arguments':'-u "'+w.DRIVER+'"'}
        self.assertEqual(w.action_kind(a),'DRIVER')
        p={'Name':'python.exe','CommandLine':a['Arguments']}
        self.assertFalse(w.process_watcher(p))
    def test_only_powershell_exact_file_process_matches(self):
        self.assertTrue(w.process_watcher({'Name':'powershell.exe','CommandLine':'powershell.exe '+self.action()['Arguments']}))
        self.assertFalse(w.process_watcher({'Name':'python.exe','CommandLine':self.action()['Arguments']}))
    def test_readonly_desktop_and_host_guard(self):
        w.require_role('ZHANGWEI',False,'ZHANGWEI')
        w.require_role('SAM',True,'sam')
        with self.assertRaises(RuntimeError):w.require_role('ZHANGWEI',True,'ZHANGWEI')
        with self.assertRaises(RuntimeError):w.require_role('SAM',True,'ZHANGWEI')
    def test_identity_drift_detectable(self):
        a={'ProcessId':123,'CreationDate':'A','CommandLine':'same','ExecutablePath':'ps'}
        b={**a,'CreationDate':'B'}
        self.assertNotEqual(w.process_identity(a),w.process_identity(b))
        a={'TaskPath':'\\','TaskName':'x','Enabled':True,'Actions':[self.action()]}
        self.assertNotEqual(w.task_identity(a),w.task_identity({**a,'Enabled':False}))
    def test_output_redacts_raw_commands(self):
        d={'Tasks':[{'TaskName':'watchdog unknown','TaskPath':'\\','Actions':[]}],
           'Processes':[{'Name':'python.exe','CommandLine':'run_unattended_catchup secret-fixture'}]}
        import json
        result=json.dumps(w.candidates(d))
        self.assertNotIn('secret-fixture',result)
        self.assertFalse(w.candidates(d)['raw_command_lines_exported'])
    def test_native_command_no_shell_or_elevation(self):
        result=subprocess.CompletedProcess([],0,b'{}',b'')
        with patch.object(w.subprocess,'run',return_value=result) as run:
            self.assertEqual(w.ps('Get-Date'),'{}')
        args,kwargs=run.call_args
        self.assertNotIn('shell',kwargs);self.assertNotIn('text',kwargs)
        self.assertEqual(args[0][:3],['powershell.exe','-NoProfile','-NonInteractive'])
        script=base64.b64decode(args[0][-1]).decode('utf-16le')
        self.assertIn('Get-Date',script);self.assertNotIn('RunAs',script)

if __name__=='__main__':unittest.main()
