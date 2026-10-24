"""Integration controls for the actual candidate gates. Synthetic in-memory data only."""
import json
import unittest
from unittest.mock import patch
import pandas as pd
from r10_factor_response_gate import request_plan
from r10_factor_candidate_pipeline import candidate_pipeline

DAY='2026-09-01'
A,B='000001.XSHE','000002.XSHE'
EXPECTED_STAGES=['REQUEST_RESPONSES_VALIDATED','OVERLAP_BOUNDARY_VALIDATED',
    'DIRTY_DAY_BOUNDARY_VALIDATED','HISTORY_PRESERVING_MERGE_PASSED','PUBLICATION_NOT_AUTHORIZED']

def f(rows):
    df=pd.DataFrame(rows,columns=['date','code','factor']);df['date']=pd.to_datetime(df['date']);return df

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.old=f([('2026-08-31',A,1.),('2026-08-31',B,1.)])
        self.day=f([(DAY,A,1.),(DAY,B,1.)])
        self.plan=request_plan([A,B],DAY,fq_arg='pre',batch_size=2)
        self.expected=pd.concat([self.old,self.day])[['date','code']].reset_index(drop=True)
    def run_pipe(self,day=None,prior=None,refresh=None,dirty=(),expected=None,plan=None):
        return candidate_pipeline(self.old,self.plan if plan is None else plan,
            [{'status':'OK','batch_index':0,'requested_codes':[A,B],
              'frame':self.day if day is None else day}],
            pd.DataFrame(columns=['date','code','factor']) if prior is None else prior,
            refresh,self.expected if expected is None else expected,required_fq='pre',dirty_codes=dirty)
    def test_clean_branch_actual_order(self):
        out,r=self.run_pipe();self.assertEqual(len(out),4);self.assertEqual(r['stages'],EXPECTED_STAGES)
        self.assertFalse(r['publication_authorized']);self.assertFalse(r['production_integrated'])
    def test_dirty_branch_keeps_non_dirty_new_day(self):
        day=f([(DAY,A,.5),(DAY,B,1.)]);rev=f([('2026-08-31',A,.5),(DAY,A,.5)])
        out,r=self.run_pipe(day=day,refresh=rev,dirty=[A]);self.assertEqual(len(out),4)
        self.assertEqual(set(out.loc[out.date.eq(DAY),'code']),{A,B});self.assertEqual(r['stages'],EXPECTED_STAGES)
        self.assertEqual(out.loc[(out.code==A)&(out.date==pd.Timestamp('2026-08-31')),'factor'].iloc[0],.5)
    def test_bad_date_stops_before_merge(self):
        bad=self.day.copy();bad['date']=[0,1]
        with patch('r10_factor_candidate_pipeline.assemble_candidate') as downstream:
            with self.assertRaisesRegex(ValueError,'NUMERIC_DATE_AXIS_FORBIDDEN'):self.run_pipe(day=bad)
            downstream.assert_not_called()
    def test_missing_security_stops_before_merge(self):
        with patch('r10_factor_candidate_pipeline.assemble_candidate') as downstream:
            with self.assertRaisesRegex(ValueError,'BATCH_SECURITY_COVERAGE_CONFLICT'):self.run_pipe(day=self.day.iloc[:1])
            downstream.assert_not_called()
    def test_fq_mismatch_stops_before_merge(self):
        plan=request_plan([A,B],DAY,fq_arg=None,batch_size=2)
        with patch('r10_factor_candidate_pipeline.assemble_candidate') as downstream:
            with self.assertRaisesRegex(ValueError,'FQ_ARGUMENT_CONSUMER_CONFLICT'):self.run_pipe(plan=plan)
            downstream.assert_not_called()
    def test_overlap_cannot_override_same_day(self):
        with self.assertRaisesRegex(ValueError,'OVERLAP_MUST_PRECEDE_REQUEST_DAY'):self.run_pipe(prior=self.day)
    def test_dirty_history_regression_blocked_by_real_merge(self):
        with self.assertRaisesRegex(ValueError,'DIRTY_HISTORY_KEY_REGRESSION'):self.run_pipe(refresh=self.day[self.day.code==A],dirty=[A])
    def test_dirty_day_value_conflict_stops_before_merge(self):
        rev=f([('2026-08-31',A,.5),(DAY,A,.5)])
        with patch('r10_factor_candidate_pipeline.assemble_candidate') as downstream:
            with self.assertRaisesRegex(ValueError,'DIRTY_REQUEST_DAY_VALUES_CONFLICT'):self.run_pipe(refresh=rev,dirty=[A])
            downstream.assert_not_called()
    def test_expected_keys_checked_in_actual_merge(self):
        expected=pd.concat([self.expected,pd.DataFrame({'date':[pd.Timestamp(DAY)],'code':['000004.XSHE']})])
        with self.assertRaisesRegex(ValueError,'REQUEST_KEYS_NOT_SERVED'):self.run_pipe(expected=expected)
    def test_dirty_future_rejected(self):
        rev=f([('2026-08-31',A,1.),(DAY,A,1.),('2026-09-02',A,1.)])
        with self.assertRaisesRegex(ValueError,'REFRESH_AFTER_ASOF'):self.run_pipe(refresh=rev,dirty=[A])
    def test_no_synthetic_pass_upgrades_authority(self):
        _,r=self.run_pipe()
        for k in ['FOUNDATION_ACCEPTANCE','FORMAL_ENGINE_ADMISSION','NEW_DATA_ACQUISITION_AUTHORIZED',
                  'CURRENT_SWITCH_ALLOWED','ORDER_ALLOWED','historical_input_authority_proven']:
            self.assertIs(r[k],False)

if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Pipeline))
    print(json.dumps({'tests_run':result.testsRun,'passed':result.wasSuccessful(),
        'scope':'CONNECTED_CANDIDATE_GATES_SYNTHETIC_ONLY','supplier_calls':0,'FOUNDATION_ACCEPTANCE':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
