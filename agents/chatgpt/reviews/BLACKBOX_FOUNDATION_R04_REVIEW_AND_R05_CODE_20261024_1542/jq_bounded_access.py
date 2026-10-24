"""GPT-owned R05 check: one JQ login, quota metadata and at most one daily bar.

Default is offline selftest. --live is authorized only by the R05 HUB contract.
Never prints SDK output, exception messages, credentials or retrieved row contents.
"""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib
import json
import os
import subprocess
import sys

ROOT = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
CREDENTIAL = Path(r'E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt')
RESULT = ROOT / 'reviews' / 'R05' / 'JQ_BOUNDED_ACCESS.json'


def parse_credential(text):
    lines = [line.strip() for line in text.lstrip('\ufeff').splitlines() if line.strip()]
    labels = {'账号': 'user', '用户名': 'user', 'username': 'user',
              '密码': 'password', 'password': 'password'}
    keyed = {}
    for line in lines:
        found = False
        for sep in (':', '：'):
            if sep in line:
                k, v = line.split(sep, 1)
                if k.strip().lower() in labels:
                    keyed[labels[k.strip().lower()]] = v.strip()
                    found = True
                    break
        if found:
            continue
    if set(keyed) == {'user', 'password'} and all(keyed.values()):
        return keyed['user'], keyed['password']
    if not keyed and len(lines) == 2:
        return lines[0], lines[1]
    raise ValueError('CREDENTIAL_FORMAT_UNSUPPORTED')


def run(jq, text):
    result = {'source_id': 'SRC_JQDATA_SDK', 'host': 'ZHANGWEI',
              'auth_invocations': 0, 'quota_invocations': 0, 'data_invocations': 0,
              'full_dataset_access_proven': False, 'stage': 'CREDENTIAL_PARSE'}
    try:
        user, password = parse_credential(text)
        result['stage'] = 'AUTH'
        result['auth_invocations'] = 1
        jq.auth(user, password)
        user = password = None
        result['stage'] = 'QUOTA'
        result['quota_invocations'] = 1
        q = jq.get_query_count()
        total, spare = q.get('total'), q.get('spare')
        if not isinstance(total, (int, float)) or not isinstance(spare, (int, float)):
            raise ValueError('QUOTA_SHAPE_UNSUPPORTED')
        result['quota'] = {'total': total, 'spare': spare}
        # Operational reserve, not a statement of supplier pricing or query cost.
        if spare < 1000:
            result.update(status='STOP_QUOTA_RESERVE', authentication='SUCCEEDED')
            return result
        result['stage'] = 'ONE_DAILY_BAR'
        result['data_invocations'] = 1
        frame = jq.get_price('000001.XSHE', start_date='2026-09-24', end_date='2026-09-24',
                             frequency='daily', fields=['open', 'high', 'low', 'close', 'volume', 'money'],
                             skip_paused=False, fq=None, panel=False)
        wanted = ['open', 'high', 'low', 'close', 'volume', 'money']
        if frame is None or not hasattr(frame, 'columns'):
            raise ValueError('RESPONSE_SHAPE_UNSUPPORTED')
        result['rows'] = len(frame)
        result['required_columns_present'] = all(c in frame.columns for c in wanted)
        result['all_required_values_nonnull'] = (all(c in frame.columns for c in wanted)
             and not bool(frame[wanted].isna().any().any()))
        result['status'] = ('BOUNDED_ACCESS_VERIFIED' if len(frame) == 1
             and result['required_columns_present'] and result['all_required_values_nonnull']
             else 'RESPONSE_NOT_VERIFIED')
        result['request'] = {'code': '000001.XSHE', 'date': '2026-09-24', 'fq': None, 'frequency': 'daily'}
        result['authentication'] = 'SUCCEEDED'
    except BaseException as exc:
        result['status'] = 'FAILED'
        result['error_type'] = type(exc).__name__
        # No str(exc), traceback, SDK output or secret-dependent hash is retained.
    return result


def selftest():
    import pandas as pd
    class Fake:
        def auth(self, u, p):
            assert (u, p) == ('fixture-user', 'fixture:password')
        def get_query_count(self):
            return {'total': 10000, 'spare': 2000}
        def get_price(self, *a, **kw):
            assert kw['fq'] is None and kw['start_date'] == kw['end_date']
            return pd.DataFrame([{f: 1.0 for f in kw['fields']}])
    assert parse_credential('fixture-user\nfixture:password') == ('fixture-user', 'fixture:password')
    assert parse_credential('账号: fixture-user\n密码: fixture:password') == ('fixture-user', 'fixture:password')
    assert run(Fake(), 'fixture-user\nfixture:password')['status'] == 'BOUNDED_ACCESS_VERIFIED'
    class Low(Fake):
        def get_query_count(self):
            return {'total': 10000, 'spare': 100}
    assert run(Low(), 'fixture-user\nfixture:password')['data_invocations'] == 0
    class Bad(Fake):
        def auth(self, *a):
            raise RuntimeError('DO_NOT_DISCLOSE_FIXTURE_SECRET')
    assert 'DO_NOT_DISCLOSE_FIXTURE_SECRET' not in json.dumps(run(Bad(), 'fixture-user\nfixture:password'))
    print(json.dumps({'status': 'PASS', 'scope': 'offline SDK double', 'checks': 5}))


def child():
    result = {'status': 'FAILED', 'stage': 'SDK_IMPORT', 'source_id': 'SRC_JQDATA_SDK'}
    with open(os.devnull, 'w') as sink, redirect_stdout(sink), redirect_stderr(sink):
        try:
            jq = importlib.import_module('jqdatasdk')
            text = CREDENTIAL.read_text(encoding='utf-8-sig')
            result = run(jq, text)
            text = None
        except BaseException as exc:
            result['error_type'] = type(exc).__name__
    result['observed_at'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    print(json.dumps(result))


def live():
    if RESULT.exists():
        raise SystemExit('RESULT_EXISTS_NO_REPEAT_AUTH')
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--child'],
                              cwd=ROOT, capture_output=True, timeout=45, text=True)
        result = json.loads(proc.stdout) if proc.returncode == 0 else {'status': 'CHILD_FAILED'}
    except subprocess.TimeoutExpired:
        result = {'status': 'TIMEOUT_NO_RETRY', 'timeout_seconds': 45}
    except BaseException as exc:
        result = {'status': 'FAILED', 'stage': 'RESULT_DECODE', 'error_type': type(exc).__name__}
    RESULT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result_path': str(RESULT), 'status': result.get('status')}))
    return 0 if result.get('status') == 'BOUNDED_ACCESS_VERIFIED' else 2


if __name__ == '__main__':
    if sys.argv[1:] == ['--child']:
        child()
    elif sys.argv[1:] == ['--live']:
        raise SystemExit(live())
    elif not sys.argv[1:] or sys.argv[1:] == ['--selftest']:
        selftest()
    else:
        raise SystemExit('UNSUPPORTED_COMMAND')
