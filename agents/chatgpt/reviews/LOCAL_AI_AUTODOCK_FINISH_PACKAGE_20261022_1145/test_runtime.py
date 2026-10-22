import importlib.util
import json
import tempfile
import unittest
import subprocess
from pathlib import Path

spec=importlib.util.spec_from_file_location('runtime',Path(__file__).with_name('run_autodock_once.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class Adapter:
    def __init__(self, answers): self.answers=iter(answers);self.calls=[]
    def handle(self,event,mode):
        self.calls.append((event['direction'],mode,event['body']))
        answer=next(self.answers)
        if isinstance(answer,Exception): raise answer
        return {'status':answer}

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.json';r.initialize(self.path,'c0',{})
    def state(self):return json.loads(self.path.read_text())
    def test_baseline_and_no_event_do_not_call_adapter(self):
        p=Path(self.tmp.name)/'base.json';files={'agents/chatgpt/outbox/old.md':'a'}
        r.initialize(p,'c0',files);a=Adapter([])
        result=r.tick(p,lambda:('c1',files),a,True)
        self.assertEqual(a.calls,[]);self.assertEqual(result['new_objects'],0)
    def test_remote_event_and_batch_and_repeat(self):
        files={f'agents/chatgpt/outbox/{n}.md':n for n in ['a','b']};a=Adapter(['DELIVERED'])
        r.tick(self.path,lambda:('c1',files),a,True)
        r.tick(self.path,lambda:('c1',files),a,True)
        self.assertEqual(a.calls,[('GPT_TO_CURSOR','SUBMIT','HUB')])
        self.assertEqual(len(self.state()['queue'][0]['items']),2)
    def test_remote_failure_does_not_advance_seen_or_lose_queue(self):
        before=self.path.read_bytes()
        def failure():raise RuntimeError('fetch failed')
        with self.assertRaises(RuntimeError):r.tick(self.path,failure)
        self.assertEqual(before,self.path.read_bytes())
    def test_uncertain_and_queued_only_verify_never_resubmit(self):
        f={'agents/chatgpt/inbox/task/REPORT.md':'s'};a=Adapter(['QUEUED','UNCERTAIN','DELIVERED'])
        for _ in range(3):r.tick(self.path,lambda:('c1',f),a,True)
        self.assertEqual([x[1] for x in a.calls],['SUBMIT','VERIFY','VERIFY'])
    def test_exception_after_possible_click_does_not_resubmit(self):
        f={'agents/chatgpt/outbox/new.md':'s'};a=Adapter([RuntimeError('adapter failed'),'DEFERRED','DELIVERED'])
        for _ in range(3):r.tick(self.path,lambda:('c1',f),a,True)
        self.assertEqual([x[1] for x in a.calls],['SUBMIT','VERIFY','VERIFY'])
    def test_deferred_before_any_input_can_retry(self):
        f={'agents/chatgpt/outbox/new.md':'s'};a=Adapter(['DEFERRED','DELIVERED'])
        for _ in range(2):r.tick(self.path,lambda:('c1',f),a,True)
        self.assertEqual([x[1] for x in a.calls],['SUBMIT','SUBMIT'])
    def test_restart_with_sending_can_only_verify(self):
        f={'agents/chatgpt/outbox/new.md':'s'}
        r.tick(self.path,lambda:('c1',f))
        s=self.state();s['queue'][0]['status']='SENDING';r.save(self.path,s)
        a=Adapter(['DELIVERED']);r.tick(self.path,lambda:('c1',f),a,True)
        self.assertEqual(a.calls[0][1],'VERIFY')
    def test_direction_filters_preserve_repair_task_and_ignore_echo(self):
        self.assertTrue(r.actionable('agents/chatgpt/outbox/LOCAL_AI_AUTODOCK_FIX.md'))
        self.assertFalse(r.actionable('agents/chatgpt/inbox/LOCAL_AI_AUTODOCK_FIX/REPORT.md'))
        self.assertFalse(r.actionable('agents/chatgpt/reviews/ACK_receipt.md'))
        self.assertFalse(r.actionable('agents/chatgpt/inbox/task/source/helper.json'))
    def test_explicit_existing_remote_test_once(self):
        p='agents/chatgpt/inbox/LOCAL_AI_AUTODOCK/PILOT_unique.md';f={p:'s'};a=Adapter(['DELIVERED'])
        for _ in range(2):r.tick(self.path,lambda:('c1',f),a,True,p)
        self.assertEqual(len(a.calls),1)
        with self.assertRaises(RuntimeError):r.tick(self.path,lambda:('c1',{}),a,True,p)
    def test_deleted_then_readded_same_blob_not_notified_twice(self):
        f={'agents/chatgpt/outbox/new.md':'s'};a=Adapter(['DELIVERED'])
        for snapshot in (f,{},f):r.tick(self.path,lambda:('c1',snapshot),a,True)
        self.assertEqual(len(a.calls),1)
    def test_initialization_cannot_reset_existing_state(self):
        with self.assertRaises(RuntimeError):r.initialize(self.path,'c1',{})
    def test_git_fetch_reads_remote_metadata_without_checkout(self):
        base=Path(self.tmp.name);remote=base/'remote.git';work=base/'work'
        def git(*args):
            return subprocess.run(['git',*map(str,args)],capture_output=True,check=True).stdout.decode().strip()
        git('init','--bare','--initial-branch=main',remote)
        git('init','--initial-branch=main',work)
        git('-C',work,'config','user.name','Local Fixture')
        git('-C',work,'config','user.email','fixture@example.invalid')
        item=work/'agents/chatgpt/outbox/中文任务.md';item.parent.mkdir(parents=True);item.write_text('fixture')
        git('-C',work,'add','.');git('-C',work,'commit','-m','fixture')
        git('-C',work,'remote','add','origin',remote);git('-C',work,'push','origin','main')
        draft=work/'local-draft.txt';draft.write_text('preserve me')
        commit,files=r.git_snapshot(work)
        self.assertEqual(commit,git('-C',work,'rev-parse','HEAD'))
        self.assertIn('agents/chatgpt/outbox/中文任务.md',files)
        self.assertEqual(draft.read_text(),'preserve me')

if __name__=='__main__':unittest.main(verbosity=2)
