import json
import unittest
from r10_factor_dirty_receipt_check import compare_receipt
from test_r10_factor_writer_regressions import WriterRegressionControls, f
from test_r10_factor_refresh_assembly import DirtyBranchControls


class ReceiptSetControls(unittest.TestCase):
    def setUp(self):
        self.receipt = {'selftest': False, 'fq':'pre', 'action':'FULL_HISTORY_REFRESHED_DIRTY_CODES',
                        'update_date':'2026-09-01', 'backward_dirty_codes':['000001.XSHE'],
                        'backward_dirty_count':1, 'full_history_refreshed_count':1,
                        'resolver_release':'FIXTURE_ONLY'}

    def test_equal_set_is_not_execution_proof(self):
        out = compare_receipt(f([('2026-09-01','000001.XSHE',1.)]), self.receipt)
        self.assertTrue(out['sets_equal']); self.assertFalse(out['B1_CLOSED'])

    def test_different_set_is_reported(self):
        out = compare_receipt(f([('2026-09-01','000002.XSHE',1.)]), self.receipt)
        self.assertFalse(out['sets_equal']); self.assertEqual(out['reported_not_observed'], ['000001.XSHE'])

    def test_receipt_count_conflict_blocks(self):
        with self.assertRaisesRegex(ValueError, 'RECEIPT_COUNT_CONFLICT'):
            compare_receipt(f([('2026-09-01','000001.XSHE',1.)]), {**self.receipt,'full_history_refreshed_count':2})


if __name__ == '__main__':
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c)
                              for c in [WriterRegressionControls,DirtyBranchControls,ReceiptSetControls])
    result = unittest.TextTestRunner().run(suite)
    print(json.dumps({'tests_run':result.testsRun,'passed':result.wasSuccessful(),
                     'scope':'PINNED_AST_ASSEMBLY_AND_RECEIPT_SET_OFFLINE_ONLY',
                     'supplier_calls':0,'FOUNDATION_ACCEPTANCE':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
