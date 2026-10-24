"""Synthetic replies + hash-pinned isolated legacy AST functions. No original module import."""
import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import pandas as pd
from r10_factor_input_contract import FactorContractError
from r10_factor_response_gate import request_plan, assemble_responses

HERE = Path(__file__).parent
DAY = '2026-09-01'
CODES = ['000001.XSHE', '000002.XSHE']
FIXTURES = {
    'full_data_update_r14_run.py': 'a1ca66995ccecc15c08f982b1cc5568372d123c47a0fc16c93fdc7a653b01944',
    'aux_billboard_adjust_index_minute_r15.py': '767c73c7a5c17e017d4274c57071725e0a59c1eef39194e795edff8dce57a3cc'}

def frame(codes=CODES):
    return pd.DataFrame({'date': pd.to_datetime([DAY] * len(codes)), 'code': codes, 'factor': 1.0})

def reply(f, codes=CODES, i=0):
    return {'status': 'OK', 'batch_index': i, 'requested_codes': codes, 'frame': f}

class Sink:
    name = 'SYNTHETIC.parquet'
    def __truediv__(self, name): return self
    def mkdir(self, *a, **k): pass

def legacy(name, codes, response):
    b = (HERE/'CANDIDATE_BODIES'/name).read_bytes()
    if hashlib.sha256(b).hexdigest() != FIXTURES[name]:
        raise AssertionError('LEGACY_SOURCE_PIN_CHANGED')
    tree = ast.parse(b.decode('utf-8-sig'))
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'download_adjust_factor_day')
    module = ast.Module(body=[node], type_ignores=[])
    env = {'pd': pd, 'P1': Sink(), 'P6_ADJ': Sink(), 'ts': lambda: 'SYNTHETIC', 'log': lambda *a: None}
    exec(compile(module, '<PINNED_LEGACY_FUNCTION_ONLY>', 'exec'), env)
    class JQ:
        def get_all_securities(self, **kw): return pd.DataFrame(index=codes)
        def get_price(self, batch, **kw): return response(batch)
    captured = []
    with patch.object(pd.DataFrame, 'to_parquet', lambda self, *a, **k: captured.append(self.copy())):
        result = env['download_adjust_factor_day'](JQ(), DAY)
    return result, captured

class Gate(unittest.TestCase):
    def plan(self, **kw): return request_plan(CODES, DAY, fq_arg=kw.get('fq', 'pre'), batch_size=2)
    def run_gate(self, f, **kw): return assemble_responses(self.plan(), [reply(f)], required_fq='pre')
    def reject(self, f, reason):
        with self.assertRaisesRegex(FactorContractError, reason): self.run_gate(f)
    def test_valid_columns_and_factor_one(self):
        out, rec = self.run_gate(frame()); self.assertEqual(len(out), 2); self.assertTrue(out.factor.eq(1).all()); self.assertFalse(rec['historical_execution_proven'])
    def test_datetime_index_preserved(self):
        f=frame().set_index('date');f.index.name='time';out,_=self.run_gate(f);self.assertTrue(out.date.eq(DAY).all())
    def test_integer_axis_rejected(self):
        f=frame();f['date']=[0,1];self.reject(f,'NUMERIC_DATE_AXIS_FORBIDDEN')
    def test_range_index_not_request_day(self): self.reject(frame().drop(columns='date'),'REQUIRED_FACTOR_FIELDS_MISSING')
    def test_wrong_day(self):
        f=frame();f['date']=pd.Timestamp('2026-08-31');self.reject(f,'RESPONSE_DATE_OUTSIDE_REQUEST')
    def test_intraday(self):
        f=frame();f['date']+=pd.Timedelta(hours=1);self.reject(f,'INTRADAY_AXIS_IN_DAILY_PRODUCT')
    def test_missing_security(self): self.reject(frame().iloc[:1],'BATCH_SECURITY_COVERAGE_CONFLICT')
    def test_extra_security(self): self.reject(frame(CODES+['000004.XSHE']),'BATCH_SECURITY_COVERAGE_CONFLICT')
    def test_failed_batch(self):
        with self.assertRaisesRegex(FactorContractError,'BATCH_NOT_SUCCESSFUL'):
            assemble_responses(self.plan(),[{'status':'FAIL'}],required_fq='pre')
    def test_missing_batch(self):
        with self.assertRaisesRegex(FactorContractError,'BATCH_RESPONSE_COUNT_CONFLICT'):
            assemble_responses(self.plan(),[],required_fq='pre')
    def test_none_is_not_pre(self):
        with self.assertRaisesRegex(FactorContractError,'FQ_ARGUMENT_CONSUMER_CONFLICT'):
            assemble_responses(self.plan(fq=None),[reply(frame())],required_fq='pre')
    def test_none_keeps_its_own_semantics(self):
        _,r=assemble_responses(self.plan(fq=None),[reply(frame())],required_fq=None);self.assertIsNone(r['fq_argument'])
    def test_batch_binding(self):
        with self.assertRaisesRegex(FactorContractError,'BATCH_REQUEST_BINDING_CONFLICT'):
            assemble_responses(self.plan(),[reply(frame(),list(reversed(CODES)))],required_fq='pre')
    def test_duplicate_keys(self): self.reject(pd.concat([frame(),frame()]),'DUPLICATE_KEYS_REQUIRE_REVISION_CONTRACT')
    def test_conflicting_date_aliases(self):
        f=frame();f['time']=pd.Timestamp('2026-08-31');self.reject(f,'CONFLICTING_DATE_ALIASES')
    def test_invalid_factor(self):
        f=frame();f.loc[0,'factor']=0;self.reject(f,'INVALID_FACTOR_OBSERVATION')
    def test_legacy_integer_index_renamed_by_r14(self):
        def response(codes):
            return pd.DataFrame({'index':range(len(codes)), 'code':codes, 'factor':1.0})
        result,captured=legacy('full_data_update_r14_run.py',CODES,response)
        self.assertEqual(result['status'],'PASS');self.assertTrue(pd.api.types.is_integer_dtype(captured[0]['date']))
    def test_legacy_date_index_loss_both_bodies(self):
        for name in FIXTURES:
            with self.subTest(name=name):
                def response(codes):
                    f=frame(codes).set_index('date');f.index.name='time';return f
                result,captured=legacy(name,CODES,response)
                self.assertEqual(result['status'],'PASS');self.assertNotIn('date',captured[0])
    def test_legacy_partial_failure_pass_both_bodies(self):
        codes=[f'{i:06d}.XSHE' for i in range(1,202)]
        for name in FIXTURES:
            with self.subTest(name=name):
                def response(chunk):
                    if len(chunk)==1:raise RuntimeError('SYNTHETIC_BATCH_FAILURE')
                    return frame(chunk)
                result,captured=legacy(name,codes,response)
                self.assertEqual(result['status'],'PASS');self.assertEqual(result['rows'],200)
    def test_complete_multiple_batches(self):
        plan=request_plan(CODES,DAY,fq_arg='pre',batch_size=1)
        out,_=assemble_responses(plan,[reply(frame([c]),[c],i) for i,c in enumerate(CODES)],required_fq='pre');self.assertEqual(len(out),2)

if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Gate))
    print(json.dumps({'tests_run':result.testsRun,'passed':result.wasSuccessful(),
          'scope':'SYNTHETIC_RESPONSES_AND_PINNED_ISOLATED_LEGACY_AST_ONLY',
          'supplier_calls':0,'FOUNDATION_ACCEPTANCE':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
