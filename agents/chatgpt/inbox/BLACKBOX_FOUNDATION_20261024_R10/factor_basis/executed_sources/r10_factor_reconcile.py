"""Read-only, one-product row/key reconciliation. Never grants data admission."""
from __future__ import annotations
import hashlib
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
from r10_factor_input_contract import flatten_factor, FactorContractError
from r10_factor_desktop_check import WORK, CACHE, pinned_bytes, no_side_effects, FALSE_FLAGS

PRODUCT = Path(r'E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439\ADJUST_FACTOR_PIT_R1')
CLEAN = Path(r'E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R26_ADJFACTOR_PIT_ASOF_20260814_20260816_044000\standard\fundamentals\adjust_factor\data\year=2026\part_2026.parquet')
CLEAN_SHA = 'e20315ba98c6766159a3ccf1972a838b9cbc936149b8fa0bd968f9c1c55443a4'
CACHE_SHA = '3f44139e136a00f9eb1dca31bf9b668f3a2a8709519752ec69a8894c8c66a46d'
COVERAGE_SHA = 'b613442e42abfb34e46ce391e533f806653439ed92855cca54a347c9fcca7b46'
MAX_BYTES = 128 * 1024 * 1024
MAX_ROWS = 2500000
YEARS = set(range(2014, 2027))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_snapshot(path, expected=None):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('FACTOR_PARTITION_BYTE_CAP')
    with path.open('rb') as f:
        b = f.read(MAX_BYTES + 1)
    if len(b) > MAX_BYTES:
        raise ValueError('FACTOR_PARTITION_BYTE_CAP')
    if expected is not None and sha(b) != expected:
        raise ValueError('EXISTING_PIN_CHANGED')
    return b


def inspect_partition(b, year):
    """Measure exact date/code/factor tuples. Do not deduplicate or manufacture dates."""
    pf = pq.ParquetFile(io.BytesIO(b))
    if pf.metadata.num_rows > MAX_ROWS:
        raise ValueError('FACTOR_PARTITION_ROW_CAP')
    names = pf.schema_arrow.names
    if not {'date', 'code', 'factor'} <= set(names):
        raise ValueError('FACTOR_SCHEMA_UNBOUND')
    raw = pf.read(columns=['date', 'code', 'factor']).to_pandas()
    physical_rows = len(raw)
    if physical_rows == 0:
        raise ValueError('EMPTY_EXPECTED_PARTITION')
    try:
        out = flatten_factor(raw)
    except FactorContractError as e:
        return {'physical_rows': physical_rows, 'schema': names, 'year': year,
                'boundary': 'REJECTED', 'reason': str(e),
                'distinct_keys': int(raw[['date', 'code']].drop_duplicates().shape[0]),
                'date_counts': None}, None
    if not out.date.dt.year.eq(year).all():
        raise ValueError('CROSS_YEAR_PARTITION_KEYS')
    counts = out.groupby('date').size()
    return {'physical_rows': physical_rows, 'distinct_keys': len(out), 'schema': names,
            'year': year, 'boundary': 'SHAPE_VALID_ONLY_NOT_ADMITTED',
            'date_min': out.date.min().date().isoformat(),
            'date_max': out.date.max().date().isoformat(),
            'codes': int(out.code.nunique()),
            'date_counts': {d.date().isoformat(): int(n) for d, n in counts.items()}}, out


def compare_shared(clean, cache):
    """Equality is descriptive: unequal bases are not adjudicated as corruption."""
    m = clean.merge(cache, on=['date', 'code'], how='outer', validate='one_to_one',
                    suffixes=('_clean', '_cache'), indicator=True)
    both = m['_merge'].eq('both')
    unequal = both & m.factor_clean.ne(m.factor_cache)
    def sample(mask):
        x = m.loc[mask, ['date', 'code', 'factor_clean', 'factor_cache']].sort_values(['date', 'code']).head(12).copy()
        x['date'] = x.date.dt.strftime('%Y-%m-%d')
        # Object conversion before replacing NaN avoids JSON NaN values.
        return x.astype(object).where(x.notna(), None).to_dict('records')
    daily = []
    for day, g in m.groupby('date', sort=True):
        shared = g['_merge'].eq('both')
        daily.append({'date': day.date().isoformat(),
                      'clean_only': int(g['_merge'].eq('left_only').sum()),
                      'cache_only': int(g['_merge'].eq('right_only').sum()),
                      'shared': int(shared.sum()),
                      'unequal_values_on_shared_keys': int((shared & g.factor_clean.ne(g.factor_cache)).sum())})
    return {'clean_rows': len(clean), 'cache_rows': len(cache),
            'clean_only': int(m['_merge'].eq('left_only').sum()),
            'cache_only': int(m['_merge'].eq('right_only').sum()),
            'shared': int(both.sum()), 'unequal_values_on_shared_keys': int(unequal.sum()),
            'row_delta_cache_minus_clean': len(cache) - len(clean),
            'by_date': daily, 'clean_only_sample': sample(m['_merge'].eq('left_only')),
            'cache_only_sample': sample(m['_merge'].eq('right_only')),
            'unequal_sample': sample(unequal),
            'precedence_decided': False, 'source_lineage_proven': False,
            'warning': 'A tuple match is not supplier/PIT provenance; unequal factors may have different anchors.'}


def reconcile_counts(parts, sidecar):
    if len(parts) != 13 or {p['year'] for p in parts} != YEARS:
        raise ValueError('INCOMPLETE_FIXED_YEAR_SET')
    physical = sum(p['physical_rows'] for p in parts)
    valid = all(p['boundary'] == 'SHAPE_VALID_ONLY_NOT_ADMITTED' for p in parts)
    tip = next(p['physical_rows'] for p in parts if p['year'] == 2026)
    declared = sidecar.get('n_rows')
    if type(declared) is not int or declared < 0:
        raise ValueError('SIDECAR_ROW_COUNT_UNBOUND')
    return {'partition_files': 13, 'physical_rows': physical,
            'distinct_keys': sum(p['distinct_keys'] for p in parts) if valid else None,
            'global_distinct_key_proof': 'UNIQUE_WITHIN_DISJOINT_YEAR_PARTITIONS' if valid else 'NOT_PROVEN',
            'sidecar_declared_rows': declared, 'physical_minus_sidecar': physical - declared,
            'reproduces_prior_83503_delta': physical - declared == 83503,
            'measured_2026_rows': tip, 'sidecar_2026_rows': sidecar.get('n_rows_year_2026'),
            'measured_2014_2025_rows': physical - tip,
            'sidecar_total_minus_declared_2026': declared - sidecar['n_rows_year_2026']
                if type(sidecar.get('n_rows_year_2026')) is int else None,
            'per_year_sidecar_baselines': 'NOT_AVAILABLE_IN_THIS_SIDECAR',
            'count_mismatch_cause': 'NOT_ESTABLISHED_BY_ARITHMETIC',
            'source_absence_claim': False, 'B1_CLOSED': False}


def desktop():
    if os.name != 'nt' or socket.gethostname().upper() != 'ZHANGWEI':
        raise ValueError('WRONG_EXECUTION_HOST')
    if Path(sys.executable).resolve() != (WORK / 'runtime/.venv/Scripts/python.exe').resolve():
        raise ValueError('WRONG_RUNTIME')
    here = Path(__file__).parent
    for n, wanted in [('r10_factor_input_contract.py', 'e30acaddecf03e0abd4360f60a74bae53525373e55feb51cf76d409beebe67c5'),
                       ('r10_factor_desktop_check.py', '76693d0834086e22b2afa62c70c4973b8271e14242ccae5c7f2a3f269d3cfed0')]:
        pinned_bytes(here / n, wanted)
    entry = WORK / 'reviews/R10/operating_entry/blackbox_operate_r10.py'
    pinned_bytes(entry, '1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9')
    argv = [sys.executable, '-X', 'utf8', str(entry), 'describe', '--product', 'ADJUST_FACTOR_PIT_R1']
    env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    p = subprocess.run(argv, cwd=WORK, env=env, capture_output=True, timeout=60)
    if p.returncode:
        return {'status': 'STOP_REAL_PREFLIGHT_ENTRY', 'exit_code': p.returncode,
                'preflight_stdout_base64': base64.b64encode(p.stdout).decode('ascii'),
                'preflight_stderr_base64': base64.b64encode(p.stderr).decode('ascii'),
                **FALSE_FLAGS}
    receipt = json.loads(p.stdout.decode('utf-8-sig'))
    preflight = receipt.get('real_preflight', {})
    if preflight.get('ok') is not True or preflight.get('MUST_READ_PRECHECK') != 'PASS':
        raise ValueError('REAL_PREFLIGHT_NOT_PASS')
    sys.addaudithook(no_side_effects)
    side_path = PRODUCT / 'COVERAGE.json'
    side_bytes = read_snapshot(side_path, COVERAGE_SHA)
    sidecar = json.loads(side_bytes.decode('utf-8-sig'))
    # One registered product only. No search outside its data directory.
    files = sorted((PRODUCT / 'data').rglob('*.parquet'))
    expected = {PRODUCT / 'data' / f'year={y}' / f'part_{y}.parquet' for y in YEARS}
    if len(files) != 13 or set(files) != expected:
        return {'status': 'STOP_PARTITION_LAYOUT_UNBOUND', 'observed_paths': [str(f) for f in files[:30]],
                'scope': str(PRODUCT / 'data'), **FALSE_FLAGS}
    parts = []; identities = []; cache2026 = None
    for path in files:
        year = int(path.parent.name.split('=')[1])
        wanted = CACHE_SHA if year == 2026 else None
        b = read_snapshot(path, wanted)
        stats, frame = inspect_partition(b, year)
        if read_snapshot(path, sha(b)) != b:
            raise ValueError('INPUT_CHANGED')
        identities.append((path, sha(b)))
        parts.append({**stats, 'path': str(path), 'sha256': sha(b), 'bytes': len(b),
                      'identity_status': 'PRIOR_PIN_MATCH' if wanted else 'NEW_MEASURED_IDENTITY_NOT_ADMITTED'})
        if year == 2026:
            cache2026 = frame
        del frame
    cb = read_snapshot(CLEAN, CLEAN_SHA)
    cs, clean2026 = inspect_partition(cb, 2026)
    identities += [(CLEAN, CLEAN_SHA), (side_path, COVERAGE_SHA)]
    shared = compare_shared(clean2026, cache2026) if clean2026 is not None and cache2026 is not None else {'status': 'NOT_COMPARABLE_BOUNDARY_REJECTION'}
    for path, wanted in identities:
        read_snapshot(path, wanted)
    return {'status': 'FIXED_FACTOR_RECONCILIATION_MEASURED', 'real_preflight': preflight,
            'preflight_argv': argv, 'preflight_stdout_sha256': sha(p.stdout),
            'preflight_stderr_sha256': sha(p.stderr), 'partitions': parts,
            'counts': reconcile_counts(parts, sidecar),
            'clean2026': {**cs, 'path': str(CLEAN), 'sha256': CLEAN_SHA, 'bytes': len(cb)},
            'clean_vs_cache_2026': shared, 'coverage_sidecar': sidecar,
            'coverage_sidecar_sha256': COVERAGE_SHA, 'source_files_changed': False,
            'supplier_calls': 0, 'all_layer_search_performed': False,
            'remaining': ['EXACT_WRITER_AND_TRANSFORM_RECEIPTS', 'HISTORICAL_FQ_PIT_PROVENANCE',
                          'ALL_LAYER_FACTOR_SOURCE_RESOLUTION', 'OTHER_SIX_INTEGRATION_GROUPS'],
            **FALSE_FLAGS}


if __name__ == '__main__':
    if sys.argv[1:] != ['--desktop-check']:
        raise SystemExit('ONLY --desktop-check IS SUPPORTED')
    try:
        result = desktop()
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        raise SystemExit(0 if result['status'] == 'FIXED_FACTOR_RECONCILIATION_MEASURED' else 3)
    except Exception as exc:
        print(json.dumps({'status': 'STOP', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, (ValueError, PermissionError)) else 'FIXED_RECONCILIATION_FAILED',
                          **FALSE_FLAGS}, ensure_ascii=True))
        raise SystemExit(3)
