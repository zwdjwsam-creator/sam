import ast
import hashlib
import json
from pathlib import Path
import unittest
import pandas as pd
from r10_factor_refresh_assembly import assemble_candidate
from test_r10_factor_writer_regressions import WriterRegressionControls, f, WRITER_SHA


class DirtyBranchControls(unittest.TestCase):
    def setUp(self):
        self.a, self.b = '000001.XSHE', '000002.XSHE'
        self.old = f([('2026-08-31', self.a, 1.), ('2026-08-31', self.b, 1.)])
        self.live = f([('2026-08-31', self.a, .5), ('2026-08-31', self.b, 1.),
                       ('2026-09-01', self.a, .5), ('2026-09-01', self.b, 1.)])
        self.revised = self.live.loc[self.live.code.eq(self.a)]
        self.expected = self.live[['date', 'code']]

    def test_exact_old_dirty_merge_ignores_non_dirty_new_day(self):
        b = Path(__file__).with_name('source_incremental_backward_refresh_r1.py').read_bytes()
        self.assertEqual(hashlib.sha256(b).hexdigest(), WRITER_SHA)
        main = next(n for n in ast.parse(b.decode('utf-8-sig')).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'main')
        branch = next(n for n in main.body if isinstance(n, ast.If)
                      and isinstance(n.test, ast.Name) and n.test.id == 'dirty')
        # Execute only the three original in-memory assignments; skip fetch/publish.
        safe = [n for n in branch.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id in {'keep', 'new_df'} for t in n.targets)]
        self.assertEqual(len(safe), 3)
        scope = {'pd': pd, 'cache': self.old.copy(), 'dirty': [self.a],
                 'refreshed': self.revised.copy(), 'set': set}
        exec(compile(ast.Module(body=safe, type_ignores=[]), '<pinned-dirty-merge>', 'exec'),
             {'__builtins__': {}}, scope)
        out = scope['new_df']
        self.assertEqual(set(out.loc[out.date.eq('2026-09-01'), 'code']), {self.a})
        self.assertEqual(set(self.live.loc[self.live.date.eq('2026-09-01'), 'code']), {self.a,self.b})

    def test_combined_branch_keeps_non_dirty_new_day(self):
        out, receipt = assemble_candidate(self.old, self.live, self.revised,
                         self.expected, '2026-09-01', [self.a])
        self.assertEqual(len(out), 4)
        self.assertEqual(set(out.loc[out.date.eq('2026-09-01'), 'code']), {self.a,self.b})
        self.assertFalse(receipt['publication_authorized'])

    def test_source_without_non_dirty_row_is_not_filled(self):
        with self.assertRaisesRegex(ValueError, 'REQUEST_KEYS_NOT_SERVED'):
            assemble_candidate(self.old, self.revised, self.revised,
                               self.expected, '2026-09-01', [self.a])

    def test_revised_code_set_mismatch_blocks(self):
        with self.assertRaisesRegex(ValueError, 'REFRESH_CODE_SET'):
            assemble_candidate(self.old, self.live, self.live,
                               self.expected, '2026-09-01', [self.a])


if __name__ == '__main__':
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(WriterRegressionControls),
                              unittest.defaultTestLoader.loadTestsFromTestCase(DirtyBranchControls)])
    result = unittest.TextTestRunner().run(suite)
    print(json.dumps({'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
                     'scope': 'PINNED_OLD_BRANCH_AST_AND_OFFLINE_ASSEMBLY',
                     'supplier_calls': 0, 'FOUNDATION_ACCEPTANCE': False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
