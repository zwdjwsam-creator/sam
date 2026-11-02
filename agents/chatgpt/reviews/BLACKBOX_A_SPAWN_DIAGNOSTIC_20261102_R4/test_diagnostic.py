"""GPT-only telemetry regressions. No native source data or policy relaxation."""
from pathlib import Path
import sys,unittest,subprocess
import guard as g
import observe as o
from diagnostic_probe import recorder,differences,runtime_identity

class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.argv=[sys.executable,'-B','-X','utf8','-c',"print('READ_ONLY_STARTUP_PROBE_OK')"]
        self.cmd=subprocess.list2cmdline(self.argv);self.rows=[]
        self.check=g.audit_checker([Path.cwd()],processes=(tuple(self.argv),),spawn_observer=recorder(self.rows))
    def popen(self,cmd=None):self.check('subprocess.Popen',(None,self.cmd if cmd is None else cmd,None,None))
    def low(self,cmd=None):self.check('_winapi.CreateProcess',(None,self.cmd if cmd is None else cmd,None))
    def test_approved_pair_retains_both_literals_and_pending(self):
        self.popen();self.low();a,b=self.rows
        self.assertEqual([a['decision'],b['decision']],['APPROVED','APPROVED'])
        self.assertEqual(a['command_literal'],self.cmd);self.assertEqual(a['reviewed_vectors'],[self.argv])
        self.assertEqual(a['pending_after'],b['pending_before']);self.assertIsNone(b['pending_after'])
    def test_different_low_command_is_measured_and_still_blocked(self):
        self.popen();different=self.cmd+' extra'
        with self.assertRaises(o.Safety):self.low(different)
        r=self.rows[-1];self.assertEqual(r['command_literal'],different)
        self.assertEqual(r['rejection_reason'],'COMMAND_LINE_NOT_REVIEWED')
        self.assertEqual(r['pending_before'][0],self.cmd);self.assertIsNone(r['pending_after'])
        self.assertEqual(r['exact_differences'][0]['first_different_index'],len(self.cmd))
    def test_base_interpreter_hypothesis_does_not_gain_permission(self):
        self.popen();different=self.cmd.replace(sys.executable,'UNREVIEWED_BASE_PYTHON',1)
        with self.assertRaises(o.Safety):self.low(different)
        self.assertEqual(self.rows[-1]['decision'],'REJECTED')
    def test_early_popen_rejection_is_recorded(self):
        with self.assertRaises(o.Safety):self.popen(self.cmd+' extra')
        self.assertEqual(len(self.rows),1);self.assertIsNone(self.rows[0]['pending_before'])
        self.assertEqual(self.rows[0]['decision'],'REJECTED')
    def test_no_env_contents_in_diagnostic(self):
        with self.assertRaises(o.Safety):self.check('subprocess.Popen',(None,self.cmd,None,{'FIXTURE_PRIVATE':'DO_NOT_COLLECT'}))
        self.assertTrue(self.rows[-1]['explicit_environment'])
        self.assertNotIn('DO_NOT_COLLECT',str(self.rows));self.assertNotIn('FIXTURE_PRIVATE',str(self.rows))
    def test_unicode_and_invisible_difference_codepoints(self):
        r=differences('abc\u200b',['abc'])[0]
        self.assertFalse(r['equal']);self.assertEqual(r['first_different_index'],3)
        self.assertIn(0x200b,r['actual_codepoints'])
    def test_unpaired_low_event_records_rejection(self):
        with self.assertRaises(o.Safety):self.low()
        self.assertEqual(self.rows[-1]['rejection_reason'],'CREATEPROCESS_WITHOUT_MATCHING_POPEN')
    def test_runtime_identity_is_metadata_only(self):
        r=runtime_identity()
        self.assertFalse(r['environment_values_collected']);self.assertFalse(r['runtime_source_bodies_read'])
        self.assertEqual(r['executable'],sys.executable)

if __name__=='__main__':unittest.main(verbosity=2)
