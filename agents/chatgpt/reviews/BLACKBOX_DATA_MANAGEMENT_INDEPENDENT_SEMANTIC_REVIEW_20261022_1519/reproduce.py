"""Exercise only copied publish_atomic/wjson AST nodes in a temporary lab.

Production matrix is stubbed PASS to reach publication. No business modules,
production directories, APIs, or Windows processes are imported or executed.
"""
import ast
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

def load_function(filename, name, namespace):
    tree = ast.parse((HERE / filename).read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(module, filename, 'exec'), namespace)
    return namespace[name]

def scenario(fail_on):
    with tempfile.TemporaryDirectory(prefix='hub-publish-review-') as td:
        lab = Path(td)
        paths = {k: lab / (k + '.json') for k in ('CACHE_PTR', 'CLEAN_PTR', 'FACTS', 'LEDGER')}
        old = {k: {'generation': 'OLD'} for k in paths if k != 'LEDGER'}
        for k, value in old.items():
            paths[k].write_text(json.dumps(value), encoding='utf-8')
        writer_ns = {'Path': Path, 'Any': Any, 'os': os, 'json': json}
        real_writer = load_function('common.py', 'wjson', writer_ns)
        writes = []
        def writer(path, obj):
            key = next(k for k, p in paths.items() if p == path)
            writes.append(key)
            if key == fail_on:
                raise OSError('LAB_INJECTED_WRITE_FAILURE')
            return real_writer(path, obj)
        namespace = dict(paths, Path=Path, shutil=shutil, json=json, wjson=writer,
            run_production_matrix=lambda facts, target: {
                'CURRENT_PUBLISH': 'ALLOWED', 'OPERATIONAL_READINESS': 'PASS'},
            now_cn=lambda: 'LAB', refresh_scope_from_live=lambda: None)
        publish = load_function('gate.py', 'publish_atomic', namespace)
        error = None
        try:
            result = publish(cache_pointer={'cache_release_id': 'NEW'}, cache_root=lab,
                facts={'SYSTEM_GENERATION_ID': 'NEW'}, target='2026-09-24',
                cleaning_pointer={'generation': 'NEW'}, dry_run=False)
        except OSError as exc:
            result = None
            error = str(exc)
        after = {k: json.loads(paths[k].read_text()) for k in old}
        if fail_on is None:
            assert result['published'] is True
            assert after['CLEAN_PTR']['generation'] == 'NEW'
            assert after['CACHE_PTR']['cache_release_id'] == 'NEW'
            assert after['FACTS']['SYSTEM_GENERATION_ID'] == 'NEW'
        elif fail_on == 'CACHE_PTR':
            assert error and after['CLEAN_PTR']['generation'] == 'NEW'
            assert after['CACHE_PTR'] == old['CACHE_PTR'] and after['FACTS'] == old['FACTS']
        elif fail_on == 'FACTS':
            assert error and after['CLEAN_PTR']['generation'] == 'NEW'
            assert after['CACHE_PTR']['cache_release_id'] == 'NEW'
            assert after['FACTS'] == old['FACTS']
        return {'fail_on': fail_on, 'writes_attempted': writes, 'after': after,
                'exception': error, 'published_result': result,
                'backups_present': {k: paths[k].with_suffix('.json.bak_before_atomic_publish').exists()
                                    for k in ('CACHE_PTR', 'CLEAN_PTR')}}

report = {'tests_passed': 3, 'production_executed': False,
    'matrix_stub': 'PASS only; matrix validity NOT tested',
    'platform': 'Linux scratch, Python stdlib; Windows process interruption NOT tested',
    'conclusion': 'Sequential per-file atomic replacements permit mixed generations after write failure; backups are present but not restored by publish_atomic.',
    'scenarios': [scenario(None), scenario('CACHE_PTR'), scenario('FACTS')]}
(HERE / 'RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
