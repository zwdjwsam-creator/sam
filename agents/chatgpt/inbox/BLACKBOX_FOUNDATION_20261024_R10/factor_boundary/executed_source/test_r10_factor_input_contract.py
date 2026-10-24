"""Meaningful pure input-boundary controls; never supplier authentication."""
import json
import unittest
import numpy as np
import pandas as pd
from r10_factor_input_contract import flatten_factor, factor_request_spec, FactorContractError


class FactorInputControls(unittest.TestCase):
    def frame(self, dates=None, factors=None):
        return pd.DataFrame({'date': dates if dates is not None else ['2026-08-31', '2026-09-01'],
                             'code': ['000001.XSHE', '000001.XSHE'],
                             'factor': factors if factors is not None else [0.9, 1.0]})

    def reject(self, f, reason):
        with self.assertRaisesRegex(FactorContractError, reason):
            flatten_factor(f)

    def test_ordinal_reject_instead_of_1970(self):
        f = self.frame([0, 299])
        self.assertEqual(pd.to_datetime(f.date).iloc[1].year, 1970)
        self.reject(f, 'NUMERIC_DATE_AXIS')

    def test_numeric_strings_reject(self):
        self.reject(self.frame(['20260831', '20260901']), 'NUMERIC_DATE_AXIS')

    def test_mixed_object_ordinal_reject(self):
        self.reject(self.frame(['2026-08-31', 1]), 'NUMERIC_DATE_AXIS')

    def test_null_date_reject(self):
        self.reject(self.frame(['2026-08-31', None]), 'NULL_DATE_AXIS')

    def test_intraday_reject_no_normalization(self):
        self.reject(self.frame(['2026-08-31 12:00', '2026-09-01']), 'INTRADAY_AXIS')

    def test_timezone_reject(self):
        self.reject(self.frame(['2026-08-31T00:00:00+08:00', '2026-09-01T00:00:00+08:00']), 'TIMEZONE')

    def test_zero_negative_nan_inf_reject(self):
        for value in [0, -1, np.nan, np.inf]:
            with self.subTest(value=value):
                self.reject(self.frame(factors=[value, 1.0]), 'INVALID_FACTOR_OBSERVATION')

    def test_equal_and_conflicting_duplicates_reject(self):
        for factors in [[1.0, 1.0], [0.9, 1.0]]:
            self.reject(self.frame(['2026-08-31'] * 2, factors), 'DUPLICATE_KEYS')

    def test_alias_conflict_reject(self):
        f = self.frame(); f['time'] = ['2026-08-30', '2026-09-01']
        self.reject(f, 'CONFLICTING_DATE_ALIASES')

    def test_code_not_inferred(self):
        f = self.frame(); f['code'] = ['000001', '000001.XSHE']
        self.reject(f, 'CANONICAL_CODE')

    def test_valid_ones_are_observations_not_automatic_error(self):
        self.assertEqual(flatten_factor(self.frame(factors=[1.0, 1.0])).factor.tolist(), [1.0, 1.0])

    def test_valid_named_multiindex(self):
        f = self.frame().rename(columns={'date': 'time', 'code': 'security'}).set_index(['time', 'security'])
        self.assertEqual(len(flatten_factor(f)), 2)

    def test_explicit_pre_request_no_execution(self):
        s = factor_request_spec(['000001.XSHE'], '2026-01-01', '2026-09-24')
        self.assertEqual(s['fq'], 'pre'); self.assertEqual(s['fields'], ['factor'])
        self.assertEqual(s['frequency'], 'daily')

    def test_request_reversed_reject(self):
        with self.assertRaisesRegex(FactorContractError, 'REVERSED_DATE_RANGE'):
            factor_request_spec(['000001.XSHE'], '2026-09-24', '2026-01-01')

    def test_actual_parquet_numeric_axis_reject(self):
        import io
        import pyarrow as pa
        import pyarrow.parquet as pq
        from r10_factor_desktop_check import inspect
        sink = io.BytesIO()
        pq.write_table(pa.Table.from_pandas(self.frame([0, 299])), sink)
        result = inspect('RAW_0831', sink.getvalue())
        self.assertEqual(result['boundary'], 'REJECTED')
        self.assertEqual(result['reason'], 'NUMERIC_DATE_AXIS_FORBIDDEN')

    def test_actual_parquet_valid_shape_cannot_admit(self):
        import io
        import pyarrow as pa
        import pyarrow.parquet as pq
        from r10_factor_desktop_check import inspect
        sink = io.BytesIO()
        pq.write_table(pa.Table.from_pandas(self.frame(factors=[1.0, 1.0])), sink)
        result = inspect('CACHE_2026', sink.getvalue())
        self.assertEqual(result['boundary'], 'SHAPE_VALID_ONLY_NOT_ADMITTED')
        self.assertEqual(result['fq_provenance'], 'NOT_PROVEN_BY_VALUES_OR_SHAPE')
        self.assertEqual(len(result['target_observations']), 2)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FactorInputControls)
    result = unittest.TextTestRunner().run(suite)
    print(json.dumps({'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
                      'scope': 'PURE_OFFLINE_INPUT_BOUNDARY', 'supplier_calls': 0,
                      'FOUNDATION_ACCEPTANCE': False}))
    raise SystemExit(0 if result.wasSuccessful() else 2)
