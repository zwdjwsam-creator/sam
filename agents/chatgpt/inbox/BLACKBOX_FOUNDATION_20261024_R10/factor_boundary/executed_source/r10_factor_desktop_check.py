"""Fixed, read-only desktop factor-boundary check. Never runs the old compiler."""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pandas as pd
import pyarrow.parquet as pq
from r10_factor_input_contract import flatten_factor, FactorContractError

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
RAW = Path(r'E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor')
CACHE = Path(r'E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439\ADJUST_FACTOR_PIT_R1\data\year=2026\part_2026.parquet')
FILES = [
    ('RAW_0831', RAW / 'adjust_factor_stock__incremental_20260831__20260831_163108.parquet',
     'e8f16f6dda011907c598ae3a7b91b752d3a16f6135dd1b4f8773894aba142fec'),
    ('RAW_0901', RAW / 'adjust_factor_stock__incremental_20260901__20260901_171005.parquet',
     'fb127145b83a2b43fc392b4e9a0ff42ec7236c2a73527de781cc149be8ccc289'),
    ('RAW_0924', RAW / 'adjust_factor_stock__incremental_20260924__20260925_030214.parquet',
     '59ca656ea171c198f4dbf238c3d39b69481b02ae563c6a8421934b3fddc7cac6'),
    ('CACHE_2026', CACHE, '3f44139e136a00f9eb1dca31bf9b668f3a2a8709519752ec69a8894c8c66a46d'),
]
CAP = 256 * 1024 * 1024
FALSE_FLAGS = {'FOUNDATION_ACCEPTANCE': False, 'FORMAL_ENGINE_ADMISSION': False,
               'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
               'ORDER_ALLOWED': False, 'SOURCE_ABSENCE_CLAIM_ALLOWED': False}


def digest_bytes(b):
    return hashlib.sha256(b).hexdigest()


def pinned_bytes(path, wanted):
    if path.stat().st_size > CAP:
        raise ValueError('FIXED_INPUT_SIZE_CAP')
    with path.open('rb') as f:
        b = f.read(CAP + 1)
    if len(b) > CAP or digest_bytes(b) != wanted:
        raise ValueError('FIXED_INPUT_PIN_CHANGED')
    return b


def inspect(role, b):
    pf = pq.ParquetFile(io.BytesIO(b))
    if pf.metadata.num_rows > 2500000:
        raise ValueError('FIXED_INPUT_ROW_CAP')
    fields = ['date', 'code', 'factor']
    if not set(fields) <= set(pf.schema_arrow.names):
        raise ValueError('FIXED_FACTOR_SCHEMA_NOT_PRESENT')
    frame = pf.read(columns=fields).to_pandas()
    report = {'role': role, 'rows': len(frame), 'date_dtype': str(frame.date.dtype),
              'field_selection': fields, 'fq_provenance': 'NOT_PROVEN_BY_VALUES_OR_SHAPE'}
    try:
        validated = flatten_factor(frame)
    except FactorContractError as exc:
        return {**report, 'boundary': 'REJECTED', 'reason': str(exc), 'source_absent': 'NOT_CLAIMED'}
    counts = validated.groupby('date').size()
    report.update(boundary='SHAPE_VALID_ONLY_NOT_ADMITTED',
                  date_min=str(validated.date.min().date()), date_max=str(validated.date.max().date()),
                  distinct_codes=int(validated.code.nunique()),
                  factor_min=float(validated.factor.min()), factor_max=float(validated.factor.max()),
                  all_factor_one=bool(validated.factor.eq(1).all()),
                  duplicate_keys=0,
                  date_counts={str(k.date()): int(v) for k, v in counts.items()})
    if role == 'CACHE_2026':
        wanted_codes = ['000001.XSHE', '002223.XSHE', '301237.XSHE', '600351.XSHG', '600989.XSHG']
        wanted_dates = ['2026-08-31', '2026-09-01']
        selected = validated[validated.code.isin(wanted_codes) & validated.date.isin(pd.to_datetime(wanted_dates))].copy()
        selected['date'] = selected.date.dt.strftime('%Y-%m-%d')
        report['target_observations'] = selected.to_dict('records')
        report['density_scope'] = 'OBSERVED_FACTOR_KEYS_ONLY; NOT_A_UNIVERSE_COMPLETENESS_CERTIFICATE'
    return report


def no_side_effects(event, args):
    if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'subprocess.Popen',
                 'os.system', 'os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.truncate',
                 'os.link', 'os.symlink', 'os.utime', 'os.chmod'):
        raise PermissionError('FACTOR_CHECK_SIDE_EFFECT_FORBIDDEN')
    if event == 'open':
        path, mode, flags = args
        if (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (flags or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise PermissionError('FACTOR_CHECK_WRITE_FORBIDDEN')
        if isinstance(path, (str, bytes)):
            p = os.fsdecode(path).replace('\\', '/').lower()
            if '/secrets/' in p or p.endswith('/.env'):
                raise PermissionError('FACTOR_CHECK_SECRET_READ_FORBIDDEN')


def desktop():
    if os.name != 'nt' or socket.gethostname().upper() != 'ZHANGWEI':
        raise ValueError('WRONG_EXECUTION_HOST')
    if Path(sys.executable).resolve() != (WORK / 'runtime/.venv/Scripts/python.exe').resolve():
        raise ValueError('WRONG_RUNTIME')
    entry = WORK / 'reviews/R10/operating_entry/blackbox_operate_r10.py'
    pinned_bytes(entry, '1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9')
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    args = [sys.executable, '-X', 'utf8', str(entry), 'describe', '--product', 'ADJUST_FACTOR_PIT_R1']
    p = subprocess.run(args, cwd=WORK, env=env, capture_output=True, timeout=60)
    if p.returncode != 0:
        return {'status': 'STOP_REAL_PREFLIGHT_ENTRY', 'exit_code': p.returncode,
                'preflight_stdout_base64': __import__('base64').b64encode(p.stdout).decode('ascii'),
                'preflight_stderr_base64': __import__('base64').b64encode(p.stderr).decode('ascii'), **FALSE_FLAGS}
    receipt = json.loads(p.stdout.decode('utf-8-sig'))
    preflight = receipt.get('real_preflight', {})
    if preflight.get('ok') is not True or preflight.get('MUST_READ_PRECHECK') != 'PASS':
        raise ValueError('REAL_PREFLIGHT_NOT_PASS')
    sys.addaudithook(no_side_effects)
    results = []
    for role, path, wanted in FILES:
        b = pinned_bytes(path, wanted)
        result = inspect(role, b)
        pinned_bytes(path, wanted)
        results.append({**result, 'path': str(path), 'sha256': wanted, 'bytes': len(b)})
    return {'status': 'FIXED_FACTOR_BOUNDARY_CHECK_COMPLETE', 'results': results,
            'real_preflight': preflight, 'preflight_stdout_sha256': digest_bytes(p.stdout),
            'preflight_stderr_sha256': digest_bytes(p.stderr), 'preflight_argv': args,
            'source_files_changed': False, 'supplier_calls': 0,
            'rule': 'Reject numeric axes; never infer dates from file names; shape validity is not factor provenance.',
            'remaining': ['83503_ROW_RECONCILIATION', 'SOURCE_TO_CACHE_LINEAGE', 'HISTORICAL_FQ_AND_PIT_PROVENANCE'],
            **FALSE_FLAGS}


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    if sys.argv[1:] != ['--desktop-check']:
        raise SystemExit('ONLY --desktop-check IS SUPPORTED')
    try:
        result = desktop()
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        raise SystemExit(0 if result['status'] == 'FIXED_FACTOR_BOUNDARY_CHECK_COMPLETE' else 3)
    except Exception as exc:
        print(json.dumps({'status': 'STOP', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, (ValueError, PermissionError)) else 'FIXED_INPUT_CHECK_FAILED',
                          **FALSE_FLAGS}, ensure_ascii=True))
        raise SystemExit(3)
