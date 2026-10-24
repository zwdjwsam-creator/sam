"""Pure factor-input successor. No acquisition, publisher or implicit data repair."""
from __future__ import annotations

import re
import numpy as np
import pandas as pd


class FactorContractError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise FactorContractError(reason)


def daily_axis(values):
    s = pd.Series(values).reset_index(drop=True)
    require(len(s) > 0 and not s.isna().any(), 'EMPTY_OR_NULL_DATE_AXIS')
    require(not pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s),
            'NUMERIC_DATE_AXIS_FORBIDDEN')
    # Mixed/object numeric axes and numeric strings must not evade the dtype check.
    text = s.map(str)
    require(not text.str.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]+)?').any(),
            'NUMERIC_DATE_AXIS_FORBIDDEN')
    require(text.str.match(r'^\d{4}-\d{2}-\d{2}(?:$|[ T])').all(),
            'EXPLICIT_ISO_DATE_AXIS_REQUIRED')
    try:
        d = pd.to_datetime(s, errors='raise', format='mixed')
        require(pd.api.types.is_datetime64_any_dtype(d), 'MIXED_OR_UNSUPPORTED_TIME_AXIS')
        require(d.dt.tz is None, 'TIMEZONE_REQUIRES_SEPARATE_CONTRACT')
        require(d.eq(d.dt.normalize()).all(), 'INTRADAY_AXIS_IN_DAILY_PRODUCT')
    except FactorContractError:
        raise
    except Exception as exc:
        raise FactorContractError('INVALID_DATE_AXIS') from exc
    return d


def flatten_factor(frame):
    """Validate declared aliases; reject bad observations instead of dropping/filling."""
    require(isinstance(frame, pd.DataFrame) and not frame.empty, 'EMPTY_FACTOR_FRAME')
    out = frame.copy()
    require(out.columns.is_unique, 'DUPLICATE_COLUMN_NAMES')
    if not ({'date', 'time'} & set(out.columns)) or not ({'code', 'security'} & set(out.columns)):
        try:
            out = out.reset_index()
        except Exception as exc:
            raise FactorContractError('AMBIGUOUS_INDEX_COLUMNS') from exc
    require(out.columns.is_unique, 'DUPLICATE_COLUMN_NAMES')
    dates = [k for k in ('date', 'time') if k in out]
    codes = [k for k in ('code', 'security') if k in out]
    require(bool(dates) and bool(codes) and 'factor' in out, 'REQUIRED_FACTOR_FIELDS_MISSING')
    d = daily_axis(out[dates[0]])
    if len(dates) == 2:
        require(d.equals(daily_axis(out[dates[1]])), 'CONFLICTING_DATE_ALIASES')
    c = out[codes[0]].reset_index(drop=True)
    require(c.notna().all() and c.map(lambda x: isinstance(x, str)).all(), 'INVALID_FACTOR_CODE')
    require(c.str.fullmatch(r'\d{6}\.(?:XSHE|XSHG)').all(), 'CANONICAL_CODE_REQUIRED')
    if len(codes) == 2:
        require(c.equals(out[codes[1]].reset_index(drop=True)), 'CONFLICTING_CODE_ALIASES')
    f = out['factor'].reset_index(drop=True)
    require(pd.api.types.is_numeric_dtype(f) and not pd.api.types.is_bool_dtype(f), 'NON_NUMERIC_FACTOR')
    a = f.to_numpy(dtype=float, na_value=np.nan)
    require(np.isfinite(a).all() and (a > 0).all(), 'INVALID_FACTOR_OBSERVATION')
    result = pd.DataFrame({'date': d, 'code': c, 'factor': a})
    # Revision precedence is not encoded by file order, even for equal duplicates.
    require(not result.duplicated(['date', 'code']).any(), 'DUPLICATE_KEYS_REQUIRE_REVISION_CONTRACT')
    return result.sort_values(['code', 'date']).reset_index(drop=True)


def factor_request_spec(codes, start, end):
    """Build a non-executing request specification under the explicit fq contract."""
    require(isinstance(codes, list) and codes and len(set(codes)) == len(codes), 'INVALID_CODE_LIST')
    require(all(isinstance(c, str) and re.fullmatch(r'\d{6}\.(?:XSHE|XSHG)', c) for c in codes),
            'CANONICAL_CODE_REQUIRED')
    require(all(isinstance(x, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', x) for x in (start, end)),
            'EXPLICIT_DATE_RANGE_REQUIRED')
    days = daily_axis([start, end])
    require(days.iloc[0] <= days.iloc[1], 'REVERSED_DATE_RANGE')
    return {'security': codes.copy(), 'start_date': start, 'end_date': end,
            'frequency': 'daily', 'fields': ['factor'], 'fq': 'pre'}
