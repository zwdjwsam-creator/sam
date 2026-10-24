"""Exercise exact engine API functions with explicit injection, without package startup.

This is a function-path harness, NOT full engine/module initialization or MASTER admission.
Creates a helper-only API candidate copy when --output-api is supplied; never edits input.
"""
import argparse
import ast
from datetime import date as Date, datetime, time as Time, timedelta
import hashlib
import importlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import pandas as pd

API_SHA = '49c49697504202fb24a73241d14f0025729a08d03ff12a67a7f694e325383dee'
NAMES = {'_normalize_provider_name', '_bind_sdk_fallback', '_sdk_fallback_targets',
         'set_data_provider', '_ensure_auth', '_maybe_disable_cache_for_live',
         '_is_live_mode', '_disable_cache_for_provider', '_get_setting',
         '_call_provider_get_price', '_call_provider_get_price_with_security_fallback',
         '_candidate_security_keys', '_is_security_lookup_error', '_raise_if_not_implemented',
         '_build_empty_price_frame', 'get_price'}


def candidate_text(s):
    tree = ast.parse(s)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_raise_if_not_implemented')
    replacement = '''def _raise_if_not_implemented(error: Exception) -> None:
    if isinstance(error, NotImplementedError) or getattr(error, "bb_admission_error", False):
        raise error
'''
    lines = s.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1]) + replacement + ''.join(lines[node.end_lineno:])


def load_functions(text, dp):
    ns = dict(globals())
    def factory_forbidden(*a, **kw):
        raise AssertionError('REMOTE_FACTORY_FORBIDDEN_IN_FUNCTION_HARNESS')
    ns.update(DataProvider=dp, _provider=None, _current_context=None,
              _provider_cache={}, _provider_auth_attempted={}, _auth_attempted=False,
              _security_info_cache={}, _cache_forced_off_warned=False,
              _create_provider=factory_forbidden,
              get_settings=lambda: SimpleNamespace(options={}),
              log=SimpleNamespace(error=lambda *a, **k: None, warning=lambda *a, **k: None,
                                  debug=lambda *a, **k: None))
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    if {n.name for n in nodes} != NAMES:
        raise ValueError('API_FUNCTION_SET_MISMATCH')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-engine-api-functions>', 'exec'), ns)
    return ns


class AdmissionError(Exception):
    bb_admission_error = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('api_path')
    ap.add_argument('--adapter')
    ap.add_argument('--output-api')
    args = ap.parse_args()
    text = Path(args.api_path).read_text(encoding='utf-8-sig').replace('\r\n', '\n').rstrip('\n')+'\n'
    if hashlib.sha256(text.encode()).hexdigest() != API_SHA:
        raise SystemExit('API_SOURCE_HASH_MISMATCH')
    changed = candidate_text(text)
    ast.parse(changed)
    if args.output_api:
        out = Path(args.output_api)
        if out.exists():
            raise SystemExit('API_CANDIDATE_DESTINATION_EXISTS')
        out.write_text(changed, encoding='utf-8')
    class Base:
        pass
    class Dummy(Base):
        name = 'blackbox_local_fixture'
        _sdk_fallback = None
        reject = False
        def auth(self):
            pass
        def get_price(self, **kw):
            if self.reject:
                raise AdmissionError('REQUIRED_FIELD_MISSING')
            return pd.DataFrame({'close': [1.]}, index=pd.to_datetime(['2026-06-01']))
    p = Dummy()
    old = load_functions(text, Base)
    old['set_data_provider'](p)
    p.reject = True
    swallowed = old['get_price']('000001.XSHE', '2026-06-01', '2026-06-01', fields=['close'], fq='none')
    assert swallowed.empty
    fixed = load_functions(changed, Base)
    fixed['set_data_provider'](p)
    try:
        fixed['get_price']('000001.XSHE', '2026-06-01', '2026-06-01', fields=['close'], fq='none')
    except AdmissionError:
        pass
    else:
        raise AssertionError('ADMISSION_ERROR_SWALLOWED')
    p.reject = False
    assert len(fixed['get_price']('000001.XSHE', '2026-06-01', '2026-06-01', fields=['close'], fq='none')) == 1
    result = {'status': 'PASS', 'scope': 'exact API function-path harness with controlled settings/logging; no package startup',
              'old_admission_error': 'EMPTY_FRAME', 'patched_admission_error': 'PROPAGATED',
              'success_control': 'FRAME', 'factory_calls': 0, 'engine_core_started': False,
              'MASTER_ADMISSION': 'NOT_IMPLEMENTED_BY_THIS_HARNESS'}
    if args.adapter:
        mod = importlib.import_module(args.adapter)
        api = load_functions(changed, mod.DataProvider)
        adapter = mod.EngineLocalValueProvider()
        api['set_data_provider'](adapter)
        try:
            frame = api['get_price']('000001.XSHE', '2026-06-01', '2026-06-03',
                                      fq='none', fill_paused=False)
            result['real_diagnostic_call'] = {'result': 'FRAME', 'rows': len(frame), 'status': frame.attrs.get('bb_status')}
        except Exception as exc:
            if not getattr(exc, 'bb_admission_error', False):
                raise
            result['real_diagnostic_call'] = {'result': 'CONTRACT_REJECT', 'reason': getattr(exc, 'reason', None)}
        try:
            api['get_price']('000001.XSHE', '2026-06-01', '2026-06-03', fq='pre', fill_paused=False)
        except Exception as exc:
            assert getattr(exc, 'bb_admission_error', False)
            result['real_adjustment_rejection'] = getattr(exc, 'reason', None)
        else:
            raise AssertionError('UNSUPPORTED_FQ_NOT_REJECTED')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
