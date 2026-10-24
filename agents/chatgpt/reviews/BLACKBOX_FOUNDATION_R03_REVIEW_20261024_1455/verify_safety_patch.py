"""Independent method tests, using AST extraction and synthetic rows only.

No Windows path, engine package, real parquet, account or network access.
Usage: python verify_safety_patch.py ORIGINAL_R3_DIRECTORY PATCHED_DIRECTORY
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
from datetime import date, datetime, time as dtime, timedelta, timezone
from typing import Any, Dict, List, Optional
import sys
import pandas as pd


class Reject(Exception):
    def __init__(self, reason, detail=None):
        self.reason = reason


class Reasons:
    OK = 'OK'
    PARTIAL = 'PARTIAL'
    REJECTED = 'REJECTED'
    COVERAGE_INCOMPLETE = 'COVERAGE_INCOMPLETE'
    KNOWABLE_TIME_UNPROVEN = 'KNOWABLE_TIME_UNPROVEN'
    SOURCE_FILE_UNREADABLE = 'SOURCE_FILE_UNREADABLE'
    FILE_BUDGET_EXCEEDED = 'FILE_BUDGET_EXCEEDED'


def method(path, cls, name, ns):
    tree = ast.parse(Path(path).read_text())
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    node = next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), ns)
    return ns[name]


def gate(path, env, **kwargs):
    ns = {'Reason': Reasons, 'ProviderReject': Reject, 'Dict': Dict, 'Any': Any}
    fn = method(path / 'engine_adapter.py', 'EngineLocalValueProvider', '_envelope_or_raise', ns)
    obj = SimpleNamespace(strict_partial=False)
    try:
        fn(obj, env, **kwargs)
        return 'RETURNED'
    except Reject as exc:
        return exc.reason


def events(path, budget=False):
    def parse_dt(v):
        if v is None:
            return None
        d = datetime.fromisoformat(str(v))
        return {'date': str(v)[:10], 'aware': d.replace(tzinfo=timezone(timedelta(hours=8)))}
    rows = pd.DataFrame([
        {'code': '000001.XSHE', 'a_xr_date': '2026-01-05', 'implementation_pub_date': '2026-01-02'},
        {'code': '000001.XSHE', 'a_xr_date': '2026-01-06', 'implementation_pub_date': '2026-01-20'},
    ])
    pq = ModuleType('pyarrow.parquet')
    pq.read_table = lambda p: SimpleNamespace(to_pandas=lambda: rows.copy())
    pa = ModuleType('pyarrow')
    pa.parquet = pq
    idx = SimpleNamespace(build_index=lambda *a: {}, select=lambda *a, **kw: {
        'selected': 1, 'files': [SimpleNamespace(path='synthetic')],
        'budget_skipped': ['not-read'] if budget else [], 'version_superseded': []})
    ns = dict(Reason=Reasons, file_index=idx, parse_dt=parse_dt, pd=pd,
              Any=Any, Dict=Dict, List=List, Optional=Optional)
    fn = method(path / 'provider.py', 'LocalValueProvider', 'get_split_dividend', ns)
    obj = SimpleNamespace(layer='CLEAN', _layer_root=lambda _: 'synthetic')
    with patch.dict(sys.modules, {'pyarrow': pa, 'pyarrow.parquet': pq}):
        return fn(obj, '000001.XSHE', '2026-01-01', '2026-01-31', asof='2026-01-10')


def main():
    old, new = map(Path, sys.argv[1:])
    before = events(old)
    after = events(new)
    partial = {'status': 'PARTIAL', 'incomplete_reasons': ['SOURCE_FILE_UNREADABLE']}
    assert gate(old, partial) == 'RETURNED'
    assert gate(new, partial, allow_partial=True) != 'RETURNED'
    assert before['row_count'] == 2 and after['row_count'] == 1
    assert after['withheld_future_announcement'] == 1
    assert gate(new, {'status': 'OK', 'field_admission': {'factor': {'admitted': False}}}) != 'RETURNED'
    assert gate(new, {'status': 'OK', 'coverage': {'proven': False}}) != 'RETURNED'
    assert gate(new, {'status': 'OK', 'file_accounting': {'budget_skipped': ['x']}}) != 'RETURNED'
    assert gate(new, {'status': 'OK', 'incomplete_reasons': []}) == 'RETURNED'
    assert Reasons.FILE_BUDGET_EXCEEDED in events(new, budget=True)['incomplete_reasons']
    for fn, reason in [('get_index_stocks', 'ENGINE_INDEX_CONTRACT_PENDING'),
                       ('get_split_dividend', 'ENGINE_EVENT_CONTRACT_PENDING')]:
        ns = dict(ProviderReject=Reject, Dict=Dict, List=List, Any=Any, Optional=Optional)
        run = method(new / 'engine_adapter.py', 'EngineLocalValueProvider', fn, ns)
        try:
            run(SimpleNamespace(), '000001.XSHE')
        except Reject as exc:
            assert exc.reason == reason
        else:
            raise AssertionError('contract-pending engine method returned')
    print(json.dumps({'status': 'PASS', 'scope': 'AST-extracted methods; synthetic frames; no engine import',
        'original_partial': 'RETURNED', 'patched_partial': 'REJECTED',
        'original_future_announced_rows': before['row_count'], 'patched_rows': after['row_count'],
        'checks': ['partial guard', 'future announcement', 'unadmitted requested field',
                   'unproven coverage', 'file budget', 'complete envelope control',
                   'event budget reason', 'index quarantine', 'event quarantine']}))


if __name__ == '__main__':
    main()
