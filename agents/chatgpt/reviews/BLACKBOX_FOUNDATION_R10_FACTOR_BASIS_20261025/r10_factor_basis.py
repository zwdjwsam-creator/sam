"""Compare registered factor generations without changing either generation."""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
from r10_factor_reconcile import read_snapshot, inspect_partition, compare_shared
from r10_factor_input_contract import flatten_factor
from r10_factor_desktop_check import WORK, pinned_bytes, no_side_effects, FALSE_FLAGS


def basis_measure(clean, cache, clean_anchor, cache_anchor, anchor, tol=1e-12):
    """Measure scale and normalized-factor equality on actually shared keys only."""
    clean, cache = flatten_factor(clean), flatten_factor(cache)
    ca, ta = flatten_factor(clean_anchor), flatten_factor(cache_anchor)
    t = pd.Timestamp(anchor)
    if not ca.date.eq(t).all() or not ta.date.eq(t).all():
        raise ValueError('EXPLICIT_COMMON_ANCHOR_REQUIRED')
    anchors = ca[['code', 'factor']].merge(ta[['code', 'factor']], on='code',
                   suffixes=('_clean_T', '_cache_T'), validate='one_to_one')
    m = clean.merge(cache, on=['date', 'code'], validate='one_to_one',
                    suffixes=('_clean', '_cache'))
    ratio = m.factor_cache / m.factor_clean
    if not np.isfinite(ratio).all() or not ratio.gt(0).all():
        raise ValueError('NONFINITE_SCALE_RATIO')
    m['scale'] = ratio
    stats = m.groupby('code').agg(n=('scale', 'size'),
             scale_min=('scale', 'min'), scale_max=('scale', 'max')).reset_index()
    stats['relative_scale_span'] = stats.scale_max / stats.scale_min - 1
    stats['multiple_observations'] = stats.n.ge(2)
    stats['constant_scale_within_tolerance'] = stats.multiple_observations & stats.relative_scale_span.le(tol)
    joined = m.merge(anchors, on='code', validate='many_to_one', how='left')
    eligible = joined.date.le(t) & joined.factor_clean_T.notna() & joined.factor_cache_T.notna()
    z = joined.loc[eligible].copy()
    z['normalized_clean'] = z.factor_clean / z.factor_clean_T
    z['normalized_cache'] = z.factor_cache / z.factor_cache_T
    z['relative_normalized_error'] = (z.normalized_cache / z.normalized_clean - 1).abs()
    if not np.isfinite(z.relative_normalized_error).all():
        raise ValueError('NONFINITE_NORMALIZED_RATIO')
    errors = z.loc[z.relative_normalized_error.gt(tol)].sort_values(['date', 'code'])
    sample = errors[['date', 'code', 'relative_normalized_error']].head(12).copy()
    sample['date'] = sample.date.dt.strftime('%Y-%m-%d')
    return {'shared_keys': len(m), 'explicit_anchor': anchor, 'relative_tolerance': tol,
            'normalization_tested_keys': len(z),
            'shared_keys_after_anchor_not_tested': int(joined.date.gt(t).sum()),
            'shared_keys_at_or_before_anchor_without_common_anchor': int((joined.date.le(t) & ~eligible).sum()),
            'normalization_mismatched_keys': len(errors),
            'normalization_max_relative_error': float(z.relative_normalized_error.max()) if len(z) else None,
            'normalized_equality_on_tested_keys': bool(len(z) and errors.empty),
            'mismatch_sample': sample.to_dict('records'),
            'per_code_scales': stats.to_dict('records'),
            'coverage_or_pit_proven': False, 'revision_precedence_decided': False}


def merge_scale_summaries(summaries, tol=1e-12):
    """Cross-year constancy: a different annual scale must remain visible."""
    rows = [row for summary in summaries for row in summary]
    if not rows:
        return []
    s = pd.DataFrame(rows).groupby('code').agg(n=('n', 'sum'),
            scale_min=('scale_min', 'min'), scale_max=('scale_max', 'max')).reset_index()
    s['relative_scale_span'] = s.scale_max / s.scale_min - 1
    s['multiple_observations'] = s.n.ge(2)
    s['constant_scale_within_tolerance'] = s.multiple_observations & s.relative_scale_span.le(tol)
    return s.to_dict('records')


def run_preflight():
    entry = WORK / 'reviews/R10/operating_entry/blackbox_operate_r10.py'
    pinned_bytes(entry, '1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9')
    argv = [sys.executable, '-X', 'utf8', str(entry), 'describe', '--product', 'ADJUST_FACTOR_PIT_R1']
    env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    p = subprocess.run(argv, cwd=WORK, env=env, capture_output=True, timeout=60)
    captured = {'argv': argv, 'exit_code': p.returncode,
                'stdout_base64': base64.b64encode(p.stdout).decode(),
                'stderr_base64': base64.b64encode(p.stderr).decode()}
    if p.returncode:
        return False, captured
    receipt = json.loads(p.stdout.decode('utf-8-sig'))
    pf = receipt.get('real_preflight', {})
    return pf.get('ok') is True and pf.get('MUST_READ_PRECHECK') == 'PASS', {**captured, 'real_preflight': pf}


def desktop():
    if os.name != 'nt' or socket.gethostname().upper() != 'ZHANGWEI':
        raise ValueError('WRONG_EXECUTION_HOST')
    if Path(sys.executable).resolve() != (WORK / 'runtime/.venv/Scripts/python.exe').resolve():
        raise ValueError('WRONG_RUNTIME')
    here = Path(__file__).parent
    package = json.loads((here / 'PACKAGE.json').read_text(encoding='utf-8'))
    for f in package['files']:
        pinned_bytes(here / f['path'], f['sha256'])
    spec = json.loads((here / 'INPUTS.json').read_text(encoding='utf-8'))
    good, preflight = run_preflight()
    if not good:
        return {'status': 'STOP_REAL_PREFLIGHT', 'preflight': preflight, **FALSE_FLAGS}
    sys.addaudithook(no_side_effects)
    clean_root = Path(spec['clean_root']) / 'data'
    files = sorted(clean_root.rglob('*.parquet'))
    expected = {clean_root / f'year={y}' / f'part_{y}.parquet' for y in range(2014, 2027)}
    if len(files) != 13 or set(files) != expected:
        return {'status': 'STOP_R26_PARTITION_LAYOUT_UNBOUND', 'observed_paths': [str(p) for p in files[:30]],
                'preflight': preflight, **FALSE_FLAGS}
    cache_pins = {p['year']: p for p in spec['cache']}
    identities = []
    def read_pair(year):
        cpath = clean_root / f'year={year}' / f'part_{year}.parquet'
        cp = cache_pins[year]; tpath = Path(cp['path'])
        csha = spec['clean_2026']['sha256'] if year == 2026 else None
        cb, tb = read_snapshot(cpath, csha), read_snapshot(tpath, cp['sha256'])
        cs, cf = inspect_partition(cb, year); ts, tf = inspect_partition(tb, year)
        if cf is None or tf is None:
            raise ValueError('FACTOR_BOUNDARY_REJECTED_STOP_COMPARISON')
        for path, b in [(cpath, cb), (tpath, tb)]:
            digest = hashlib.sha256(b).hexdigest()
            identities.append((path, digest))
        return cf, tf, {'year': year, 'clean_path': str(cpath), 'cache_path': str(tpath),
            'clean_sha256': identities[-2][1], 'cache_sha256': identities[-1][1],
            'clean_identity': 'PRIOR_PIN_MATCH' if csha else 'NEW_MEASURED_NOT_ADMITTED',
            'cache_identity': 'PRIOR_PIN_MATCH', 'clean_rows': len(cf), 'cache_rows': len(tf),
            'clean_boundary': cs['boundary'], 'cache_boundary': ts['boundary']}
    cf, tf, tip_identity = read_pair(2026)
    anchor = spec['anchor_date']; tol = spec['relative_tolerance']; t = pd.Timestamp(anchor)
    ca, ta = cf.loc[cf.date.eq(t)], tf.loc[tf.date.eq(t)]
    # Keep only anchor vectors across iterations; no concatenated all-history panel.
    results = []; scales = []
    for year in range(2014, 2027):
        if year == 2026:
            c, f, identity = cf, tf, tip_identity
        else:
            c, f, identity = read_pair(year)
        tuples = compare_shared(c, f)
        basis = basis_measure(c, f, ca, ta, anchor, tol)
        scales.append(basis.pop('per_code_scales'))
        results.append({**identity, 'tuple_comparison': tuples, 'basis_comparison': basis})
        del c, f
    for path, wanted in identities:
        read_snapshot(path, wanted)
    return {'status': 'FACTOR_GENERATION_BASIS_MEASURED', 'preflight': preflight,
            'year_results': results, 'cross_year_scale_summary': merge_scale_summaries(scales, tol),
            'clean_total_rows': sum(x['clean_rows'] for x in results),
            'cache_total_rows': sum(x['cache_rows'] for x in results),
            'clean_only_keys': sum(x['tuple_comparison']['clean_only'] for x in results),
            'cache_only_keys': sum(x['tuple_comparison']['cache_only'] for x in results),
            'unequal_shared_values': sum(x['tuple_comparison']['unequal_values_on_shared_keys'] for x in results),
            'source_files_changed': False, 'supplier_calls': 0, 'all_layer_search_performed': False,
            'scope': 'TWO_REGISTERED_FACTOR_GENERATIONS_ONLY',
            'interpretation': 'Constant per-code scales can cancel in factor(d)/factor(T) on measured shared keys only; no supplier/PIT/coverage authority follows.',
            'B1_CLOSED': False, **FALSE_FLAGS}


if __name__ == '__main__':
    if sys.argv[1:] != ['--desktop-check']:
        raise SystemExit('ONLY --desktop-check IS SUPPORTED')
    try:
        result = desktop()
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        raise SystemExit(0 if result['status'] == 'FACTOR_GENERATION_BASIS_MEASURED' else 3)
    except Exception as e:
        print(json.dumps({'status': 'STOP', 'error_type': type(e).__name__,
                          'reason': str(e) if isinstance(e, (ValueError, PermissionError)) else 'FACTOR_GENERATION_COMPARISON_FAILED',
                          **FALSE_FLAGS}))
        raise SystemExit(3)
