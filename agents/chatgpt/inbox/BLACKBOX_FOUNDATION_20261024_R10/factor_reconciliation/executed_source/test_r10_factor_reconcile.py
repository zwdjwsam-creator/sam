"""Offline invariant checks using real in-memory Parquet files."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import r10_factor_reconcile as r


def frame(rows):
    x = pd.DataFrame(rows, columns=['date', 'code', 'factor'])
    x['date'] = pd.to_datetime(x.date)
    return x


def parquet(x):
    stream = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(x, preserve_index=False), stream)
    return stream.getvalue()


class Controls(unittest.TestCase):
    def test_shared_key_value_conservation(self):
        c = frame([('2026-08-14', '000001.XSHE', 1.)])
        out = r.compare_shared(c, c.iloc[::-1])
        self.assertEqual((out['shared'], out['unequal_values_on_shared_keys'], out['clean_only'], out['cache_only']), (1, 0, 0, 0))
        self.assertFalse(out['source_lineage_proven'])

    def test_value_change_is_not_hidden_by_equal_counts(self):
        c = frame([('2026-08-14', '000001.XSHE', .8)])
        t = frame([('2026-08-14', '000001.XSHE', 1.)])
        out = r.compare_shared(c, t)
        self.assertEqual(out['row_delta_cache_minus_clean'], 0)
        self.assertEqual(out['unequal_values_on_shared_keys'], 1)
        self.assertFalse(out['precedence_decided'])

    def test_equal_rows_with_replaced_symbol_exposed(self):
        c = frame([('2026-08-14', '000001.XSHE', 1.)])
        t = frame([('2026-08-14', '000002.XSHE', 1.)])
        out = r.compare_shared(c, t)
        self.assertEqual((out['clean_only'], out['cache_only'], out['shared']), (1, 1, 0))
        json.dumps(out, allow_nan=False)

    def test_cache_extension_does_not_claim_clean_loss(self):
        c = frame([('2026-08-14', '000001.XSHE', 1.)])
        t = frame([('2026-08-14', '000001.XSHE', 1.), ('2026-09-01', '000001.XSHE', 1.)])
        out = r.compare_shared(c, t)
        self.assertEqual((out['clean_only'], out['cache_only'], out['shared']), (0, 1, 1))

    def test_duplicate_merge_never_selects_winner(self):
        c = frame([('2026-08-14', '000001.XSHE', 1.)] * 2)
        with self.assertRaises(pd.errors.MergeError):
            r.compare_shared(c, c)

    def test_real_parquet_preserves_one_factor(self):
        x = frame([('2026-09-01', '000001.XSHE', 1.)])
        stats, out = r.inspect_partition(parquet(x), 2026)
        self.assertEqual(stats['boundary'], 'SHAPE_VALID_ONLY_NOT_ADMITTED')
        pd.testing.assert_frame_equal(out.reset_index(drop=True), x)

    def test_integer_axis_real_parquet_rejected(self):
        x = pd.DataFrame({'date': [0], 'code': ['000001.XSHE'], 'factor': [1.]})
        stats, out = r.inspect_partition(parquet(x), 2026)
        self.assertEqual(stats['reason'], 'NUMERIC_DATE_AXIS_FORBIDDEN')
        self.assertIsNone(out)

    def test_duplicate_parquet_preserves_physical_count(self):
        x = frame([('2026-09-01', '000001.XSHE', 1.)] * 2)
        stats, out = r.inspect_partition(parquet(x), 2026)
        self.assertEqual((stats['physical_rows'], stats['distinct_keys']), (2, 1))
        self.assertEqual(stats['boundary'], 'REJECTED')

    def test_wrong_year_cannot_certify_disjoint_keys(self):
        x = frame([('2025-09-01', '000001.XSHE', 1.)])
        with self.assertRaisesRegex(ValueError, 'CROSS_YEAR_PARTITION_KEYS'):
            r.inspect_partition(parquet(x), 2026)

    def test_nan_factor_not_silently_dropped(self):
        x = frame([('2026-09-01', '000001.XSHE', float('nan'))])
        stats, out = r.inspect_partition(parquet(x), 2026)
        self.assertEqual(stats['physical_rows'], 1)
        self.assertEqual(stats['boundary'], 'REJECTED')

    def test_parquet_row_cap(self):
        x = frame([('2026-09-01', '000001.XSHE', 1.)])
        with patch.object(r, 'MAX_ROWS', 0):
            with self.assertRaisesRegex(ValueError, 'ROW_CAP'):
                r.inspect_partition(parquet(x), 2026)

    def parts(self):
        return [{'year': y, 'physical_rows': 1, 'distinct_keys': 1,
                 'boundary': 'SHAPE_VALID_ONLY_NOT_ADMITTED'} for y in range(2014, 2027)]

    def test_count_match_never_closes_b1(self):
        out = r.reconcile_counts(self.parts(), {'n_rows': 13, 'n_rows_year_2026': 1})
        self.assertEqual(out['physical_minus_sidecar'], 0)
        self.assertFalse(out['B1_CLOSED'])
        self.assertFalse(out['source_absence_claim'])

    def test_83503_arithmetic_is_not_causal_proof(self):
        out = r.reconcile_counts(self.parts(), {'n_rows': 83516, 'n_rows_year_2026': 1})
        self.assertEqual(out['physical_minus_sidecar'], -83503)
        self.assertFalse(out['reproduces_prior_83503_delta'])
        self.assertEqual(out['count_mismatch_cause'], 'NOT_ESTABLISHED_BY_ARITHMETIC')

    def test_incomplete_years_block_aggregate_claim(self):
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE_FIXED_YEAR_SET'):
            r.reconcile_counts(self.parts()[:-1], {'n_rows': 12})

    def test_invalid_partition_has_no_global_unique_proof(self):
        p = self.parts(); p[-1]['boundary'] = 'REJECTED'
        out = r.reconcile_counts(p, {'n_rows': 13})
        self.assertIsNone(out['distinct_keys'])
        self.assertEqual(out['global_distinct_key_proof'], 'NOT_PROVEN')

    def test_changed_snapshot_pin_blocks_read(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'part.bin'; path.write_bytes(b'original')
            wanted = r.sha(path.read_bytes()); path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'EXISTING_PIN_CHANGED'):
                r.read_snapshot(path, wanted)

    def test_snapshot_byte_cap(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'part.bin'; path.write_bytes(b'too large')
            with patch.object(r, 'MAX_BYTES', 2):
                with self.assertRaisesRegex(ValueError, 'BYTE_CAP'):
                    r.read_snapshot(path)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
                      'scope': 'OFFLINE_PARQUET_AND_KEY_CONSERVATION',
                      'supplier_calls': 0, 'FOUNDATION_ACCEPTANCE': False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
