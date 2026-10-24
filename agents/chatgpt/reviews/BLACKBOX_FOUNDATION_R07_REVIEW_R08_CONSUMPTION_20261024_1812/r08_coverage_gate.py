"""Candidate successor controls. No filesystem writes, network, or absence approval.

Presence is measured at the declared key and field grain, never just max(date).
This module is not a replacement installed at the historical HAND script path.
"""
import pandas as pd
import numpy as np

MISSING_ENUM = (
    'SOURCE_MISSING','RAW_COMPLETE_CLEANING_MISSING','CLEANING_COMPLETE_CACHE_MISSING',
    'CACHE_COVERAGE_REGRESSION','CACHE_PRODUCT_UNAVAILABLE','READER_LOAD_MISSING',
    'READER_DATE_SLICE_MISSING','FILTER_EMPTY','UNIVERSE_EMPTY','PIT_ASOF_EMPTY',
    'SOURCE_LIMITATION','REQUEST_OUTSIDE_PRODUCT_COVERAGE','AMBIGUOUS_DATASET','UNKNOWN_STOP')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def normalize_dates(series):
    # Integer row ordinals are not nanosecond timestamps or session dates.
    require(not pd.api.types.is_numeric_dtype(series), 'NUMERIC_DATE_AXIS_REJECTED')
    value = pd.to_datetime(series, errors='raise')
    require(value.notna().all(), 'NULL_DATE_AXIS')
    require(value.dt.tz is None, 'TIMEZONE_CONVERSION_REQUIRES_EXPLICIT_CONTRACT')
    require(value.eq(value.dt.normalize()).all(), 'INTRADAY_AXIS_NOT_DAILY')
    return value


def keys(frame, grain):
    require(bool(grain) and set(grain) <= set(frame.columns), 'GRAIN_COLUMNS_MISSING')
    data = frame[list(grain)].copy()
    require(not data.isna().any().any(), 'NULL_KEY')
    if 'date' in grain:
        data['date'] = normalize_dates(data['date'])
    require(not data.duplicated().any(), 'DUPLICATE_KEYS')
    return pd.MultiIndex.from_frame(data)


def compare(before, after, grain=('date','code'), fields=('close',)):
    """Loss of a symbol on an existing date is a regression too."""
    a, b = keys(before, grain), keys(after, grain)
    lost = a.difference(b)
    losses = {}
    for field in fields:
        require(field in before and field in after, 'FIELD_NOT_BOUND:' + field)
        old_ok = before[field].notna().to_numpy()
        new_ok = after[field].notna().to_numpy()
        if pd.api.types.is_numeric_dtype(before[field]):
            old_ok &= np.isfinite(before[field].to_numpy(dtype=float, na_value=np.nan))
        if pd.api.types.is_numeric_dtype(after[field]):
            new_ok &= np.isfinite(after[field].to_numpy(dtype=float, na_value=np.nan))
        losses[field] = len(a[old_ok].difference(b[new_ok]))
    passed = len(lost) == 0 and not any(losses.values())
    return {'coverage_non_regression_pass': passed, 'grain': list(grain),
            'parent_keys': len(a), 'candidate_keys': len(b), 'lost_keys': len(lost),
            'lost_field_observation_keys': losses,
            'lost_key_examples': [list(map(str, v)) for v in list(lost[:10])],
            # No aggregate of two products certifies all critical products.
            'PUBLISH_ALLOWED': False, 'CURRENT_SWITCH_ALLOWED': False,
            'scope': 'EXACT_INPUT_FRAMES_ONLY_NOT_GLOBAL_COVERAGE_OR_ENGINE_ADMISSION'}


def diagnose_observed_layers(layer_frames, expected_keys, grain=('date','code')):
    """Bounded positive evidence only. Zero source-absence claims are authorized.

    expected_keys must come from a reviewed scope, not be guessed from a cache.
    A layer with keys but null close is not a serving observation for this request.
    """
    expected = keys(expected_keys, grain)
    require(len(expected) > 0, 'EMPTY_EXPECTED_SCOPE')
    evidence = {}
    for layer in ('RAW','CLEAN','CACHE','READER'):
        f = layer_frames.get(layer)
        if f is None:
            evidence[layer] = {'scope_complete': False, 'observed_request_keys': 0}
            continue
        axis = keys(f, grain)
        require('close' in f, 'OBSERVATION_FIELD_NOT_BOUND')
        good = f['close'].notna().to_numpy()
        good &= np.isfinite(f['close'].to_numpy(dtype=float, na_value=np.nan))
        count = len(expected.intersection(axis[good]))
        evidence[layer] = {'scope_complete': count == len(expected), 'observed_request_keys': count}
    root, status = 'UNKNOWN_STOP', 'UNRESOLVED'
    if evidence['RAW']['scope_complete']:
        if not evidence['CLEAN']['scope_complete']:
            root = 'RAW_COMPLETE_CLEANING_MISSING'
        elif not evidence['CACHE']['scope_complete']:
            root = 'CLEANING_COMPLETE_CACHE_MISSING'
        elif not evidence['READER']['scope_complete']:
            root = 'READER_LOAD_MISSING'
        else:
            root, status = None, 'AVAILABLE_FOR_EXACT_REQUEST'
    return {'root_cause': root, 'diagnosis_status': status, 'allowed_root_causes': list(MISSING_ENUM),
            'expected_keys': len(expected), 'layers': evidence,
            'SOURCE_ABSENCE_CLAIM_ALLOWED': False, 'DOWNLOAD_REQUIRED': False,
            'global_authority_ready': False,
            'scope': 'BOUNDED_POSITIVE_EVIDENCE_NOT_LEGACY_ABSENCE_GATE_REPLACEMENT'}


def require_union_members(members, required):
    require(set(members) == set(required), 'VIEW_MEMBERSHIP_CHANGED')
    for name in required:
        require(members[name] is not None and not members[name].empty, 'CACHE_PRODUCT_UNAVAILABLE:' + name)
    return True
