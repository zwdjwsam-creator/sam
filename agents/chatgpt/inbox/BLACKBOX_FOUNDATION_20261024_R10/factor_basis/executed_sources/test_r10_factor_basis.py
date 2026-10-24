import io
import json
import unittest
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from r10_factor_basis import basis_measure, merge_scale_summaries


def frame(rows):
    f = pd.DataFrame(rows, columns=['date', 'code', 'factor'])
    f['date'] = pd.to_datetime(f.date)
    f['factor'] = f.factor.astype(float)
    return f


class BasisControls(unittest.TestCase):
    def setUp(self):
        self.c = frame([('2026-01-05', '000001.XSHE', .8), ('2026-08-14', '000001.XSHE', 1.)])
        self.t = frame([('2026-01-05', '000001.XSHE', .4), ('2026-08-14', '000001.XSHE', .5)])

    def run_basis(self, c=None, t=None, ca=None, ta=None):
        c = self.c if c is None else c; t = self.t if t is None else t
        ca = c[c.date.eq('2026-08-14')] if ca is None else ca
        ta = t[t.date.eq('2026-08-14')] if ta is None else ta
        return basis_measure(c, t, ca, ta, '2026-08-14')

    def test_different_values_same_normalized_results(self):
        out = self.run_basis()
        self.assertTrue(out['normalized_equality_on_tested_keys'])
        self.assertEqual(out['normalization_tested_keys'], 2)
        self.assertTrue(out['per_code_scales'][0]['constant_scale_within_tolerance'])
        self.assertFalse(out['coverage_or_pit_proven'])

    def test_time_varying_scale_changes_normalized_result(self):
        t = self.t.copy(); t.loc[0, 'factor'] = .3
        out = self.run_basis(t=t)
        self.assertEqual(out['normalization_mismatched_keys'], 1)
        self.assertFalse(out['normalized_equality_on_tested_keys'])
        self.assertFalse(out['per_code_scales'][0]['constant_scale_within_tolerance'])

    def test_independent_scales_per_security(self):
        c = pd.concat([self.c, self.c.assign(code='000002.XSHE')], ignore_index=True)
        t = pd.concat([self.t, self.c.assign(code='000002.XSHE', factor=lambda x:x.factor * .9)], ignore_index=True)
        out = self.run_basis(c, t)
        self.assertTrue(out['normalized_equality_on_tested_keys'])
        self.assertEqual(len(out['per_code_scales']), 2)

    def test_missing_anchor_is_unverified(self):
        extra = frame([('2026-01-05', '000002.XSHE', .7)])
        c = pd.concat([self.c, extra]); t = pd.concat([self.t, extra])
        out = self.run_basis(c, t)
        self.assertEqual(out['shared_keys_at_or_before_anchor_without_common_anchor'], 1)
        self.assertEqual(out['normalization_tested_keys'], 2)

    def test_after_anchor_does_not_extend_certificate(self):
        extra = frame([('2026-09-01', '000001.XSHE', .7)])
        out = self.run_basis(pd.concat([self.c, extra]), pd.concat([self.t, extra]))
        self.assertEqual(out['shared_keys_after_anchor_not_tested'], 1)
        self.assertEqual(out['normalization_tested_keys'], 2)
        self.assertFalse(out['coverage_or_pit_proven'])

    def test_wrong_anchor_date_blocked(self):
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_COMMON_ANCHOR_REQUIRED'):
            self.run_basis(ca=self.c.iloc[:1])

    def test_duplicate_key_never_picks_winner(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_KEYS'):
            self.run_basis(c=pd.concat([self.c, self.c.iloc[:1]]))

    def test_missing_key_is_not_normalization_proof(self):
        out = self.run_basis(t=self.t.iloc[1:])
        self.assertEqual(out['shared_keys'], 1)
        self.assertFalse(out['per_code_scales'][0]['multiple_observations'])
        self.assertFalse(out['coverage_or_pit_proven'])

    def test_cross_year_change_not_hidden(self):
        a = self.run_basis()['per_code_scales']
        b = self.run_basis(t=self.c)['per_code_scales']
        combined = merge_scale_summaries([a, b])
        self.assertFalse(combined[0]['constant_scale_within_tolerance'])
        self.assertEqual(combined[0]['n'], 4)

    def test_same_cross_year_scale(self):
        a = self.run_basis()['per_code_scales']
        combined = merge_scale_summaries([a, a])
        self.assertTrue(combined[0]['constant_scale_within_tolerance'])

    def test_real_parquet_round_trip(self):
        stream = io.BytesIO(); pq.write_table(pa.Table.from_pandas(self.c, preserve_index=False), stream)
        c = pq.read_table(io.BytesIO(stream.getvalue())).to_pandas()
        self.assertTrue(self.run_basis(c=c)['normalized_equality_on_tested_keys'])

    def test_valid_all_one_values(self):
        c = self.c.assign(factor=1.)
        out = self.run_basis(c, c)
        self.assertTrue(out['normalized_equality_on_tested_keys'])
        self.assertFalse(out['coverage_or_pit_proven'])
        json.dumps(out, allow_nan=False)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(BasisControls))
    print(json.dumps({'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
                     'scope': 'FACTOR_RATIO_INVARIANCE_OFFLINE_ONLY', 'supplier_calls': 0,
                     'FOUNDATION_ACCEPTANCE': False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
