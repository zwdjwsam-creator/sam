"""Read one pinned factor partition and one pinned retained receipt."""
import base64
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
sys.dont_write_bytecode = True
import pandas as pd
import pyarrow.parquet as pq
from r10_factor_input_contract import flatten_factor, daily_axis, require
from r10_factor_desktop_check import WORK, CACHE, pinned_bytes, no_side_effects, FALSE_FLAGS

RECEIPT = Path(r'E:\BLACKBOX\任务\BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1\INCREMENTAL_RECEIPT.json')
RECEIPT_SHA = 'bbbec46fb07034506bdc74761e6e7d6de95edfb771d9b80314ff8eaa6f8b71ed'
CACHE_SHA = '3f44139e136a00f9eb1dca31bf9b668f3a2a8709519752ec69a8894c8c66a46d'


def compare_receipt(frame, receipt):
    f = flatten_factor(frame)
    require(receipt.get('selftest') is False and receipt.get('fq') == 'pre' and
            receipt.get('action') == 'FULL_HISTORY_REFRESHED_DIRTY_CODES', 'UNEXPECTED_RECEIPT_KIND')
    day = daily_axis([receipt['update_date']]).iloc[0]
    dirty = receipt['backward_dirty_codes']
    require(isinstance(dirty, list) and dirty and len(set(dirty)) == len(dirty), 'INVALID_DIRTY_LIST')
    # Reuse the code validator without inferring any observation or factor value.
    flatten_factor(pd.DataFrame({'date': [day] * len(dirty), 'code': dirty, 'factor': 1.0}))
    require(len(dirty) == receipt['backward_dirty_count'] == receipt['full_history_refreshed_count'],
            'RECEIPT_COUNT_CONFLICT')
    rows = f.loc[f.date.eq(day)].copy()
    observed, reported = set(rows.code), set(dirty)
    rows['date'] = rows.date.dt.strftime('%Y-%m-%d')
    return {'receipt_date': receipt['update_date'], 'receipt_release': receipt['resolver_release'],
            'observed_codes_on_receipt_date': sorted(observed), 'receipt_dirty_codes': sorted(reported),
            'sets_equal': observed == reported, 'observed_not_reported': sorted(observed - reported),
            'reported_not_observed': sorted(reported - observed),
            'observed_rows_on_receipt_date': rows.to_dict('records'),
            'interpretation': 'Set agreement is content consistency with the reported branch; not exact code execution, producer identity or complete market coverage proof.',
            'SOURCE_ABSENCE_CLAIM_ALLOWED': False, 'B1_CLOSED': False}


def desktop():
    require(os.name == 'nt' and socket.gethostname().upper() == 'ZHANGWEI', 'WRONG_EXECUTION_HOST')
    require(Path(sys.executable).resolve() == (WORK/'runtime/.venv/Scripts/python.exe').resolve(), 'WRONG_RUNTIME')
    here = Path(__file__).parent
    package = json.loads((here/'PACKAGE.json').read_text(encoding='utf-8'))
    for member in package['files']:
        b = pinned_bytes(here/member['path'], member['sha256'])
        require(len(b) == member['bytes'], 'PACKAGE_SIZE_CHANGED')
    entry = WORK/'reviews/R10/operating_entry/blackbox_operate_r10.py'
    pinned_bytes(entry, '1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9')
    argv = [sys.executable, '-X', 'utf8', str(entry), 'describe', '--product', 'ADJUST_FACTOR_PIT_R1']
    env = os.environ.copy(); env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run(argv, cwd=WORK, env=env, capture_output=True, timeout=60)
    capture = {'argv': argv, 'exit_code': p.returncode,
               'stdout_base64': base64.b64encode(p.stdout).decode(),
               'stderr_base64': base64.b64encode(p.stderr).decode()}
    require(p.returncode == 0, 'REAL_PREFLIGHT_COMMAND_FAILED')
    preflight = json.loads(p.stdout.decode('utf-8-sig')).get('real_preflight', {})
    require(preflight.get('ok') is True and preflight.get('MUST_READ_PRECHECK') == 'PASS', 'REAL_PREFLIGHT_NOT_PASS')
    sys.addaudithook(no_side_effects)
    rb, cb = pinned_bytes(RECEIPT, RECEIPT_SHA), pinned_bytes(CACHE, CACHE_SHA)
    pf = pq.ParquetFile(io.BytesIO(cb))
    require(pf.metadata.num_rows <= 2500000, 'INPUT_ROW_CAP')
    measured = compare_receipt(pf.read(columns=['date','code','factor']).to_pandas(), json.loads(rb.decode('utf-8-sig')))
    pinned_bytes(RECEIPT, RECEIPT_SHA); pinned_bytes(CACHE, CACHE_SHA)
    return {'status': 'PINNED_DIRTY_RECEIPT_CONTENT_MEASURED', 'preflight': capture,
            'real_preflight': preflight, 'measurement': measured, 'source_files_changed': False,
            'supplier_calls': 0, 'all_layer_search_performed': False, **FALSE_FLAGS}


if __name__ == '__main__':
    if sys.argv[1:] != ['--desktop-check']:
        raise SystemExit('ONLY --desktop-check IS SUPPORTED')
    try:
        result = desktop()
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    except Exception as exc:
        print(json.dumps({'status': 'STOP', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__, **FALSE_FLAGS}))
        raise SystemExit(3)
