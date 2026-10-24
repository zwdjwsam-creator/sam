import json
import unittest
import pandas as pd
from r10_factor_source_batches import validate_batch,merge_batches


class SourceBatchControls(unittest.TestCase):
    def setUp(self):
        self.frame=pd.DataFrame({'date':['2026-08-14'],'code':['000001.XSHE'],'factor':[1.]})
        self.meta={'year':2026,'batch':0,'fq':'pre','n_codes_requested':400,'rows':1,
                   'n_codes':1,'date_min':'2026-08-14','date_max':'2026-08-14'}

    def check(self,f=None,m=None):
        return validate_batch(self.frame if f is None else f,self.meta if m is None else m,2026,0,400)

    def test_valid_explicit_source(self):self.assertEqual(len(self.check()),1)
    def test_wrong_fq_rejected(self):
        with self.assertRaisesRegex(ValueError,'SIDECAR_IDENTITY'):self.check(m={**self.meta,'fq':'none'})
    def test_numeric_date_not_recovered_from_sidecar(self):
        with self.assertRaisesRegex(ValueError,'NUMERIC_DATE_AXIS'):self.check(self.frame.assign(date=0))
    def test_row_count_conflict(self):
        with self.assertRaisesRegex(ValueError,'ROW_COUNT'):self.check(m={**self.meta,'rows':2})
    def test_sidecar_date_conflict(self):
        with self.assertRaisesRegex(ValueError,'DATE_BOUND'):self.check(m={**self.meta,'date_max':'2026-08-13'})
    def test_outside_declared_source_end(self):
        with self.assertRaisesRegex(ValueError,'DATE_RANGE'):self.check(self.frame.assign(date='2026-08-17'))
    def test_duplicate_across_batches_is_not_last_file_wins(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_KEYS'):merge_batches([self.check(),self.check()])
    def test_empty_batch_can_be_measured_without_completeness_claim(self):
        out=self.check(self.frame.iloc[:0],{**self.meta,'rows':0,'n_codes':0,'date_min':None,'date_max':None})
        self.assertTrue(out.empty)


if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceBatchControls))
    print(json.dumps({'tests_run':result.testsRun,'passed':result.wasSuccessful(),
                     'scope':'SOURCE_BATCH_BOUNDARY_OFFLINE_ONLY','supplier_calls':0,'FOUNDATION_ACCEPTANCE':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
