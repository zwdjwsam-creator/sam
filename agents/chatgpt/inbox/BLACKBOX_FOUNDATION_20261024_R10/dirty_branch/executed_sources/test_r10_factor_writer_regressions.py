"""Regression fixtures; never import or execute the supplier-facing writer."""
import ast
import hashlib
import json
from pathlib import Path
import unittest
import pandas as pd
from r10_factor_candidate_merge import candidate_merge

WRITER_SHA = '1df97ec81882243716cece03afb786638a05028642f97309cf71a3bcea3456f0'


def f(rows):
    return pd.DataFrame(rows, columns=['date', 'code', 'factor'])


class WriterRegressionControls(unittest.TestCase):
    def setUp(self):
        self.a, self.b = '000001.XSHE', '000002.XSHE'
        self.old = f([('2026-09-01', self.a, 1.0)])
        self.add = f([('2026-09-01', self.b, 1.0)])
        self.expected = pd.concat([self.old, self.add], ignore_index=True)[['date', 'code']]

    def run_merge(self, old=None, new=None, expected=None, dirty=()):
        return candidate_merge(self.old if old is None else old,
            self.add if new is None else new,
            self.expected if expected is None else expected, '2026-09-01', dirty)

    def test_original_date_only_shortcut_reproduced_from_pinned_ast(self):
        path = Path(__file__).with_name('source_incremental_backward_refresh_r1.py')
        data = path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), WRITER_SHA)
        tree = ast.parse(data.decode('utf-8-sig'))
        node = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'have_ud' for t in n.targets))
        cache = self.old.copy(); cache['date'] = pd.to_datetime(cache.date)
        result = eval(compile(ast.Expression(node), '<pinned-have_ud>', 'eval'),
                      {'__builtins__': {}, 'set': set, 'cache': cache,
                       'ud': pd.Timestamp('2026-09-01')})
        self.assertTrue(result)
        self.assertNotIn(self.b, set(cache.code))

    def test_partial_day_gets_remaining_security(self):
        out, receipt = self.run_merge()
        self.assertEqual(set(out.code), {self.a, self.b})
        self.assertFalse(receipt['provenance_proven'])

    def test_unserved_expected_key_blocks(self):
        with self.assertRaisesRegex(ValueError, 'REQUEST_KEYS_NOT_SERVED'):
            self.run_merge(new=self.old)

    def test_dirty_full_history_truncation_blocks(self):
        old = f([('2026-08-31', self.a, .8), ('2026-09-01', self.a, 1.)])
        with self.assertRaisesRegex(ValueError, 'DIRTY_HISTORY_KEY_REGRESSION'):
            self.run_merge(old, self.old, old[['date', 'code']], [self.a])

    def test_full_dirty_replacement_preserves_keys(self):
        old = f([('2026-08-31', self.a, .8), ('2026-09-01', self.a, 1.)])
        new = old.assign(factor=[.4, .5])
        out, _ = self.run_merge(old, new, old[['date', 'code']], [self.a])
        self.assertEqual(out.factor.tolist(), [.4, .5])

    def test_revision_before_parent_tip_blocks_mixed_basis(self):
        old = f([('2026-09-01', self.a, 1.), ('2026-09-02', self.a, 1.)])
        with self.assertRaisesRegex(ValueError, 'REVISION_END_BEFORE_PARENT_TIP'):
            self.run_merge(old, self.old.assign(factor=.5), self.old[['date','code']], [self.a])

    def test_unapproved_value_conflict_blocks(self):
        with self.assertRaisesRegex(ValueError, 'VALUE_CONFLICT'):
            self.run_merge(new=self.old.assign(factor=.5), expected=self.old[['date','code']])

    def test_no_last_file_wins(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_KEYS'):
            self.run_merge(new=pd.concat([self.add, self.add]))

    def test_replay_is_idempotent(self):
        out, _ = self.run_merge()
        replay, _ = self.run_merge(old=out)
        pd.testing.assert_frame_equal(out, replay)

    def test_numeric_axis_rejected(self):
        with self.assertRaisesRegex(ValueError, 'NUMERIC_DATE_AXIS'):
            self.run_merge(new=self.add.assign(date=0))

    def test_future_input_rejected(self):
        with self.assertRaisesRegex(ValueError, 'INCOMING_AFTER_ASOF'):
            self.run_merge(new=self.add.assign(date='2026-09-02'))

    def test_no_generated_calendar_grid(self):
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_EXPECTED_KEYS'):
            self.run_merge(expected=pd.DataFrame())

    def test_legitimate_one_and_flags(self):
        out, r = self.run_merge()
        self.assertTrue(out.factor.eq(1.).all())
        self.assertFalse(r['publication_authorized'])
        self.assertFalse(r['FOUNDATION_ACCEPTANCE'])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(WriterRegressionControls))
    print(json.dumps({'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
                     'scope': 'PINNED_AST_AND_OFFLINE_MERGE_ONLY',
                     'supplier_calls': 0, 'FOUNDATION_ACCEPTANCE': False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
