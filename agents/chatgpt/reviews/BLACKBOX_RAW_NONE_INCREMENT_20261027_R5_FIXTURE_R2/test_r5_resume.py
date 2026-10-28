import base64
import json
import tempfile
import unittest
from datetime import date,datetime,timedelta
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import acquire_daily as a
import acquire_r5 as r
import precheck_r5 as p
import sys
import types

D=date(2026,10,27)

def fixture():
    meta=json.loads(Path(__file__).with_name('failed_batch_fixture.json').read_bytes())
    b=base64.b64decode(meta['content_base64']);assert a.digest(b)==r.FAILED_SHA
    return b

def failed_frame():
    import io
    return pd.read_parquet(io.BytesIO(fixture()))

def candidate():
    x=failed_frame();return x.loc[x['code'].eq('600621.XSHG')].iloc[0].copy()

class QuarantineTests(unittest.TestCase):
    def test_original_failed_body_exact_79_1_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'original.parquet';path.write_bytes(fixture());before=path.read_bytes()
            x=pd.read_parquet(path);dec=r.classify(x,x['code'].tolist(),D,'stock')
            self.assertEqual(len(dec['admitted_positions']),79);self.assertEqual(dec['quarantined_positions'],[7])
            self.assertEqual(path.read_bytes(),before)
            q=r.Quarantine();q.add(x,[7],{'sha256':r.FAILED_SHA},D)
            self.assertEqual(q.rows[0]['source_values']['paused'],0)
            self.assertIsNone(q.rows[0]['source_values']['open']);self.assertEqual(q.rows[0]['label'],r.LABEL)
    def test_four_numeric_pairs_only(self):
        for ratio in ['0.05','0.10','0.20','0.30']:
            x=candidate();pc=Decimal(str(x['pre_close']))
            x['high_limit']=float((pc*(1+Decimal(ratio))).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
            x['low_limit']=float((pc*(1-Decimal(ratio))).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
            self.assertTrue(r.is_quarantine_candidate(x))
    def test_volume_nonzero_hard_stop(self):
        x=failed_frame();x.loc[7,'volume']=1
        with self.assertRaisesRegex(a.Blocked,'LIVE_BAR_NULL'):r.classify(x,x['code'].tolist(),D,'stock')
    def test_money_nonzero_hard_stop(self):
        x=candidate();x['money']=1;self.assertFalse(r.is_quarantine_candidate(x))
    def test_close_null_hard_stop(self):
        x=candidate();x['close']=float('nan');self.assertFalse(r.is_quarantine_candidate(x))
    def test_close_not_preclose(self):
        x=candidate();x['close']+=1;self.assertFalse(r.is_quarantine_candidate(x))
    def test_avg_not_close(self):
        x=candidate();x['avg']+=1;self.assertFalse(r.is_quarantine_candidate(x))
    def test_unmatched_limits(self):
        x=candidate();x['high_limit']+=.01;self.assertFalse(r.is_quarantine_candidate(x))
    def test_paused_null(self):
        x=candidate();x['paused']=float('nan');self.assertFalse(r.is_quarantine_candidate(x))
    def test_factor_null(self):
        x=candidate();x['factor']=float('nan');self.assertFalse(r.is_quarantine_candidate(x))
    def test_only_open_null(self):
        x=candidate();x['high']=x['close'];self.assertFalse(r.is_quarantine_candidate(x))
    def test_etf_hard_stop_preserved(self):
        x=failed_frame()
        with self.assertRaisesRegex(a.Blocked,'LIVE_BAR_NULL'):r.classify(x,x['code'].tolist(),D,'etf')
    def test_index_hard_stop_preserved(self):
        x=failed_frame().iloc[[7]].copy();x['code']=['000001.XSHG']
        with self.assertRaisesRegex(a.Blocked,'LIVE_BAR_NULL'):r.classify(x,['000001.XSHG'],D,'index')
    def test_duplicate_cannot_be_quarantined(self):
        x=failed_frame();x=pd.concat([x,x.iloc[[7]]])
        with self.assertRaisesRegex(a.Blocked,'DUPLICATE'):r.classify(x,x['code'].tolist(),D,'stock')
    def test_nonfinite_cannot_be_quarantined(self):
        x=failed_frame();x.loc[7,'factor']=float('inf')
        with self.assertRaisesRegex(a.Blocked,'NONFINITE'):r.classify(x,x['code'].tolist(),D,'stock')
    def test_day_cap_fourth_stops(self):
        x=failed_frame();q=r.Quarantine();q.add(x,[7],{},D);q.add(x,[7],{},D);q.add(x,[7],{},D)
        with self.assertRaisesRegex(a.Blocked,'QUARANTINE_CAP'):q.add(x,[7],{},D)
        self.assertEqual(len(q.rows),3)
    def test_total_cap_eleventh_stops(self):
        x=failed_frame();q=r.Quarantine()
        for n in range(10):q.add(x,[7],{},D+timedelta(days=n))
        with self.assertRaisesRegex(a.Blocked,'QUARANTINE_CAP'):q.add(x,[7],{},D+timedelta(days=10))
    def test_invalid_two_rows_not_old_readmission(self):
        x=failed_frame();x.iloc[8,2:]=x.iloc[7,2:]
        with self.assertRaisesRegex(a.Blocked,'FAILED_79_1'):r.readmit_failed(x,x['code'].tolist())
    def test_wrong_old_candidate_security_refused(self):
        x=failed_frame();x.loc[7,'code']='600622.XSHE'
        with self.assertRaisesRegex(a.Blocked,'FAILED_WRONG_ISOLATE'):r.readmit_failed(x,x['code'].tolist())

class ReuseAndCoverage(unittest.TestCase):
    def test_failed_hash_corruption_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'body';f.write_bytes(fixture()+b'x')
            # This fixture tests byte identity, not the host's E: read permission.
            # Replace only that permission seam for this exact temporary file;
            # the unchanged Windows guard is exercised separately below.
            with patch.object(a,'require_allowed_read') as policy:
                with self.assertRaisesRegex(a.Blocked,'IDENTITY_DRIFT'):r.read_exact(f,{'bytes':15489,'sha256':r.FAILED_SHA})
                policy.assert_called_once_with(f.resolve(strict=True))
    def test_exact_raw_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'body';f.write_bytes(fixture());s=f.stat()
            with patch.object(a,'require_allowed_read') as policy:
                self.assertEqual(r.read_exact(f,{'bytes':15489,'sha256':r.FAILED_SHA}),fixture())
                policy.assert_called_once_with(f.resolve(strict=True))
            self.assertEqual(f.stat().st_mtime_ns,s.st_mtime_ns)
    def test_remaining_1784_batches(self):
        u=[f'{n:06d}.XSHG' for n in range(5224)];left=r.validate_remaining(u,u[:3440])
        self.assertEqual(len(left),1784);self.assertEqual(len([left[n:n+80] for n in range(0,len(left),80)]),23)
        self.assertEqual(len(left[-24:]),24)
    def test_wrong_fetched_count_refused(self):
        u=[f'{n:06d}.XSHG' for n in range(5224)]
        with self.assertRaisesRegex(a.Blocked,'FETCHED_KEY_SET'):r.validate_remaining(u,u[:3439])
    def test_fetched_duplicate_refused(self):
        u=[f'{n:06d}.XSHG' for n in range(5224)]
        with self.assertRaisesRegex(a.Blocked,'FETCHED_KEY_SET'):r.validate_remaining(u,u[:3439]+[u[0]])
    def test_quarantine_not_hidden_missing(self):
        d=r.reconcile(['a','b','c'],['a'],['b']);self.assertEqual(d['unacquired_codes'],['c'])
        self.assertEqual(d['quarantined'],1);self.assertEqual(d['PAGINATION_COMPLETE'],'NO')
    def test_quarantine_not_double_counted(self):
        with self.assertRaisesRegex(a.Blocked,'OVERLAP'):r.reconcile(['a'],['a'],['a'])
    def test_cross_batch_duplicate_hard_stop(self):
        with self.assertRaisesRegex(a.Blocked,'DUPLICATE_BOUNDARY'):r.reconcile(['a','b'],['a','a'],[])
    def test_unrequested_not_source_absence(self):
        d=r.reconcile(['a'],[],[]);self.assertFalse(d['source_absence_claim']);self.assertEqual(d['unacquired_codes'],['a'])
    def test_raw_values_and_dtype_preserved_end_to_end(self):
        x=failed_frame();x['code']=x['code'].astype(object)
        with tempfile.TemporaryDirectory() as d:
            q=r.Quarantine();entry,good,bad=r.save_batch(x,x['code'].tolist(),D,'stock',3360,Path(d),1,q)
            self.assertEqual((len(good),len(bad)),(79,1));self.assertEqual(entry['source_rows'],80)
            stored=pd.read_parquet(entry['source']['path']);a.verify_parquet_roundtrip(x,stored)
            self.assertEqual(x['paused'].tolist(),stored['paused'].tolist());self.assertEqual(len(q.rows),1)
    def test_unapproved_batch_preserved_on_failure(self):
        x=failed_frame();x.loc[7,'volume']=4
        with tempfile.TemporaryDirectory() as d:
            q=r.Quarantine()
            with self.assertRaisesRegex(a.Blocked,'LIVE_BAR_NULL'):r.save_batch(x,x['code'].tolist(),D,'stock',3360,Path(d),1,q)
            self.assertEqual(len(list(Path(d).rglob('*.parquet'))),1);self.assertEqual(len(q.rows),0)
    def test_exact_source_receipt_hash_binding(self):
        bindings=json.loads(Path(__file__).with_name('R4_BINDINGS.json').read_bytes())
        self.assertEqual(len(bindings['raw']),1098);self.assertEqual(len(bindings['metadata']),3363)
        self.assertEqual(bindings['raw'][r.FAILED_REL],{'bytes':15489,'sha256':r.FAILED_SHA})

class WindowsReadPolicy(unittest.TestCase):
    @staticmethod
    def native_guard():
        # Execute the real production function's code with an explicit Windows
        # OS-name proxy. Do not mutate global os.name (which changes pathlib).
        return types.FunctionType(a.require_allowed_read.__code__,
            dict(a.require_allowed_read.__globals__,os=types.SimpleNamespace(name='nt')))
    def test_real_windows_guard_fixed_roots_and_sibling_boundary(self):
        guard=self.native_guard()
        for value in [r'E:\BLACKBOX\STAGING\fixture',r'E:\BLACKBOX_ENGINES\fixture',r'\\?\E:\BLACKBOX\STAGING\fixture']:
            guard(value)
        for value in [r'C:\Users\Admin\AppData\Local\Temp\fixture',r'E:\BLACKBOX_EVIL\fixture',r'F:\BLACKBOX\fixture']:
            with self.assertRaisesRegex(a.Blocked,'EXTERNAL_LINK_TARGET'):guard(value)
    def test_real_windows_guard_refuses_external_temp_before_read_admission(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'body';f.write_bytes(fixture());before=f.stat().st_mtime_ns
            with patch.object(a,'require_allowed_read',self.native_guard()):
                with self.assertRaisesRegex(a.Blocked,'EXTERNAL_LINK_TARGET'):
                    r.read_exact(f,{'bytes':15489,'sha256':r.FAILED_SHA})
            self.assertEqual(f.stat().st_mtime_ns,before)
    def test_external_path_not_hidden_by_corrupt_hash(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'body';f.write_bytes(fixture()+b'x')
            with patch.object(a,'require_allowed_read',self.native_guard()):
                with self.assertRaisesRegex(a.Blocked,'EXTERNAL_LINK_TARGET'):
                    r.read_exact(f,{'bytes':15489,'sha256':r.FAILED_SHA})

class FakeJQ:
    def __init__(self):self.spare=200000000;self.calls=[]
    def get_query_count(self):return {'spare':self.spare}
    def get_price(self,**args):self.calls.append(args);self.spare-=len(args['security']);return 'response'

class QuotaAndGates(unittest.TestCase):
    def test_new_budget_and_inherited_quota(self):
        with tempfile.TemporaryDirectory() as d:
            j=FakeJQ();s=r.Supplier(j,Path(d));ans,n=s.call('get_price',r.price_args(['600621.XSHG'],D))
            self.assertEqual(n,1);self.assertEqual(sum(s.deltas),1);self.assertEqual(s.inherited,175858)
    def test_projected_cap_before_call(self):
        with tempfile.TemporaryDirectory() as d:
            j=FakeJQ();s=r.Supplier(j,Path(d));s.quota();j.spare-=149950
            with self.assertRaisesRegex(a.Blocked,'RESERVE_STOP'):s.call('get_price',r.price_args(['000001.XSHG']*80,D))
            self.assertEqual(j.calls,[])
    def test_universe_stock_refetch_denied(self):
        with tempfile.TemporaryDirectory() as d:
            j=FakeJQ();s=r.Supplier(j,Path(d))
            with self.assertRaisesRegex(a.Blocked,'UNIVERSE_ENDPOINT_SCOPE'):s.call('get_all_securities',{'types':['stock'],'date':str(D)})
            self.assertEqual(j.calls,[])
    def test_nonzero_preflight_not_substituted_by_tests(self):
        with self.assertRaisesRegex(a.Blocked,'PREFLIGHT'):p.verify_preflight_stdout(b'MUST_READ_PRECHECK = FAIL\n')
    def test_skipped_suite_not_pass(self):
        with self.assertRaisesRegex(a.Blocked,'TEST'):p.verify_tests(b'Ran 100 tests in 1s\nOK (skipped=1)\n',100)
    def test_wrong_test_count_blocks(self):
        with self.assertRaisesRegex(a.Blocked,'COUNT'):p.verify_tests(b'Ran 99 tests in 1s\nOK\n',100)
    def test_failure_before_sdk_or_E_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(r'E:\BLACKBOX');out=root/'STAGING'/r.OUTPUT_NAME
            with patch.object(r.platform,'system',return_value='Windows'),patch.object(r.platform,'node',return_value='ZHANGWEI'),\
                 patch.object(r,'ensure_gate',side_effect=a.Blocked('GATE_MISSING')),\
                 patch.object(Path,'exists',return_value=False),patch.object(Path,'mkdir') as mkdir:
                with self.assertRaisesRegex(a.Blocked,'GATE_MISSING'):r.run(root,out)
                mkdir.assert_not_called()
    def test_rule_drift_blocks_before_preflight(self):
        pins=json.loads(Path(__file__).with_name('RULE_PINS.json').read_bytes())
        self.assertEqual(len(pins['files']),10)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for rel in pins['files']:
                path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'changed')
            with self.assertRaisesRegex(a.Blocked,'RULE_IDENTITY_DRIFT'):p.rule_binding(root)
    def test_no_future_target_expansion(self):
        self.assertEqual(a.UPPER,date(2026,10,27));self.assertEqual(r.INHERITED,175858);self.assertEqual(r.NEW_CAP,150000)

class WholeContinuation(unittest.TestCase):
    def run_model(self,mode):
        from contextlib import ExitStack
        from copy import deepcopy
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name);out=root/'STAGING'/r.OUTPUT_NAME
        days=['2026-09-28','2026-09-29','2026-09-30','2026-10-08','2026-10-09','2026-10-12','2026-10-13',
              '2026-10-14','2026-10-15','2026-10-16','2026-10-19','2026-10-20','2026-10-21','2026-10-22',
              '2026-10-23','2026-10-26','2026-10-27']
        full=[f'{n:06d}.XSHG' for n in range(5223)]+['600621.XSHG'];remaining=full[3440:5223]+['600621.XSHG']
        # Existing 600621 must be excluded from supplier requests: move it into the retained set.
        remaining=full[3440:5224];remaining.remove('600621.XSHG');remaining.insert(0,full[3439])
        old_admitted={d:list(full) for d in days};old_admitted[days[-1]]=full[:3439]
        isolated={d:[] for d in days};isolated[days[-1]]=['600621.XSHG']
        old={'admission':[],'days':days,'admitted':old_admitted,'isolated':isolated,'expected_by_day':{d:full for d in days},
             'remaining':remaining,'last_universe':full,'source_root':'MODEL','references':[]}
        class SDK:
            __version__='1.9.8'
            def __init__(self):self.spare=200000000;self.log=[]
            def get_price(self,security,start_date,end_date,frequency,fields,skip_paused=False,fill_paused=True,fq=None,panel=False):
                self.log.append(('price',start_date,list(security)));self.spare-=len(security)
                if mode=='supplier_error':raise RuntimeError('unlogged supplier error')
                x=pd.DataFrame({'time':[pd.Timestamp(start_date)]*len(security),'code':pd.Series(security,dtype=object)})
                for f in fields:x[f]=[1.0]*len(security)
                x['paused']=0.0
                if mode=='etf_null' and security==['510001.XSHG','510002.XSHG']:x.loc[0,'open']=float('nan')
                return x
            def get_all_securities(self,types,date):
                assert types==['etf'];self.log.append(('universe',date));self.spare-=2
                return pd.DataFrame({'start_date':[D-timedelta(days=1000)]*2,'end_date':[D+timedelta(days=1000)]*2},
                                    index=['510001.XSHG','510002.XSHG'])
            def get_query_count(self):return {'spare':self.spare}
            def set_params(self,**args):assert args['request_attempt_count']==1
        sdk=SDK();module=types.ModuleType('jqdatasdk')
        for name in ['get_price','get_all_securities','get_query_count','set_params']:setattr(module,name,getattr(sdk,name))
        module.__version__='1.9.8'
        def reuse_model(root_arg,reuse_arg,q):
            x=failed_frame();q.add(x,[7],{'sha256':r.FAILED_SHA},D);return deepcopy(old)
        with ExitStack() as stack:
            stack.enter_context(patch.object(r,'check_location'))
            stack.enter_context(patch.object(r,'ensure_gate',return_value={'model':True}))
            stack.enter_context(patch.object(a,'pinned',return_value={}))
            stack.enter_context(patch.object(a,'reuse_inputs',return_value={'model_reuse':True}))
            stack.enter_context(patch.object(r,'reuse_r4',side_effect=reuse_model))
            stack.enter_context(patch.object(a,'login'))
            stack.enter_context(patch.dict(sys.modules,{'jqdatasdk':module}))
            code=r.run(root,out)
        result=json.loads((out/'RESULT_R5.json').read_bytes());return code,result,sdk,out
    def test_actual_entry_resumes_only_unrequested_codes_and_no_refetch(self):
        code,result,sdk,out=self.run_model('ok');self.assertEqual(code,0)
        prices=[x for x in sdk.log if x[0]=='price'];universes=[x for x in sdk.log if x[0]=='universe']
        self.assertEqual(len(universes),17);self.assertEqual(len(prices),23+17+17)
        stock=prices[:23];self.assertEqual(sum(len(x[2]) for x in stock),1784)
        self.assertNotIn('600621.XSHG',{c for x in stock for c in x[2]})
        self.assertTrue(all(x[1]=='2026-10-27' for x in stock));self.assertEqual(result['quarantined_rows'],1)
        self.assertEqual(result['quota_spent'],1784+17*4+17*7)
        self.assertEqual(result['quota_spent'],result['receipt_quota_sum'])
        cells=json.loads((out/'COVERAGE_R5.json').read_bytes())['cells'];self.assertEqual(len(cells),51)
        self.assertTrue(all(x['status']=='ACQUIRED' for x in cells));self.assertEqual(result['baseline_after'],'UNCHANGED')
    def test_supplier_failure_is_not_retried_and_receipts_survive(self):
        code,result,sdk,out=self.run_model('supplier_error');self.assertEqual(code,2)
        self.assertEqual(len(sdk.log),1);self.assertEqual(result['supplier_calls'],1)
        self.assertEqual(result['quota_spent'],80);self.assertEqual(result['failure_final_quota_measurement'],'MEASURED')
        self.assertTrue((out/'QUARANTINE_R5.json').exists());self.assertTrue((out/'ADMISSION_R5.json').exists())
        cells=json.loads((out/'COVERAGE_R5.json').read_bytes())['cells']
        self.assertEqual(sum(x['status']=='NOT_ATTEMPTED' for x in cells),34)
    def test_etf_failure_stops_before_index_and_preserves_raw(self):
        code,result,sdk,out=self.run_model('etf_null');self.assertEqual(code,2)
        self.assertEqual(result['reason'],'LIVE_BAR_NULL');self.assertEqual(len(sdk.log),25)
        self.assertEqual(result['quarantined_rows'],1)
        self.assertEqual(len(list((out/'raw/etf').glob('*.parquet'))),1)
        cells=json.loads((out/'COVERAGE_R5.json').read_bytes())['cells']
        self.assertTrue(all(x['status']=='NOT_ATTEMPTED' for x in cells if x['product']=='index'))

class GateEvidence(unittest.TestCase):
    def check(self,mutate=None):
        with tempfile.TemporaryDirectory() as d:
            control=Path(d);root=Path(r'E:\BLACKBOX')
            count=json.loads(Path(__file__).with_name('PACKAGE.json').read_bytes())['expected_tests']
            stdout=('MUST_READ_PRECHECK = PASS\nTASK_CLASS = ACQUISITION\nKERNEL_STATUS = VERIFIED\n'
              'AUTHORITY_READY = YES\nTASK_EXECUTION = ALLOWED\nTASK_EXECUTION_FORBIDDEN = FALSE\n'+
              'status = VERIFIED\n'*3).encode()
            stderr=f'Ran {count} tests in 0.5s\nOK\n'.encode();gate={'task_id':r.TASK,'package_sha256':'model',
              'rule_bindings':[],'ack_sha256':a.digest(b'ACK'),'finished_at':a.now().isoformat(),'expected_tests':count}
            (control/'ACK_R5.json').write_bytes(b'ACK')
            for phase in ['preflight','tests']:
                run={'actual_os_exit':0}
                for channel in ['stdout','stderr']:
                    b=stdout if (phase,channel)==('preflight','stdout') else stderr if (phase,channel)==('tests','stderr') else b''
                    name=f'{phase.upper()}_{channel.upper()}_R5.txt';(control/name).write_bytes(b)
                    run[channel]={'name':name,'bytes':len(b),'sha256':a.digest(b)}
                gate[phase]=run
            gate['preflight']['argv']=[str(root/'.venv/Scripts/python.exe'),'-X','utf8',
               str(root/'脚本/blackbox_must_read_preflight_r1.py'),'--task-class','ACQUISITION']
            gate['tests']['argv']=[str(root/'.venv/Scripts/python.exe'),'-X','utf8','-m','unittest','-v',
                'test_acquire_daily','test_r3_code_and_reuse','test_r4_empty_slots','test_r5_resume']
            if mutate:mutate(gate,control)
            (control/'GATE_R5.json').write_text(json.dumps(gate))
            with patch.object(p,'verify_package',return_value='model'),patch.object(p,'rule_binding',return_value=[]):
                return p.validate_gate(control)
    def test_raw_two_gate_evidence_accepted(self):self.assertEqual(self.check()['actual_preflight_exit'],0)
    def test_claimed_pass_with_actual_exit_one_refused(self):
        def change(g,c):g['preflight']['actual_os_exit']=1
        with self.assertRaisesRegex(a.Blocked,'GATE_EXIT'):self.check(change)
    def test_raw_stream_drift_refused(self):
        def change(g,c):(c/'PREFLIGHT_STDOUT_R5.txt').write_bytes(b'PASS')
        with self.assertRaisesRegex(a.Blocked,'STREAM_DRIFT'):self.check(change)
    def test_wrong_command_refused(self):
        def change(g,c):g['preflight']['argv'].append('--acceptance')
        with self.assertRaisesRegex(a.Blocked,'PREFLIGHT_COMMAND'):self.check(change)
    def test_weakened_test_count_refused(self):
        def change(g,c):g['expected_tests']=1
        with self.assertRaisesRegex(a.Blocked,'TEST_REQUIREMENT_CHANGED'):self.check(change)

if __name__=='__main__':unittest.main()
