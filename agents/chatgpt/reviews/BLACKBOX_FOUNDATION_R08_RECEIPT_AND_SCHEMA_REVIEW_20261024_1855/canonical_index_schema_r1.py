"""Pure canonical-index schema adapter for a future contracted Cleaning successor.

Does not open files, write releases, set PIT/known_at, merge revisions, or authorize
research/engine RAW fallback. Caller must pin and enumerate registered shards.
"""
import numpy as np
import pandas as pd


def normalize_canonical_index(source):
    required={'canonical_code','trade_date','open','high','low','close','pre_close',
              'volume','amount','price_variant','return_variant','source_fq'}
    missing=required-set(source.columns)
    if missing:
        raise ValueError('CANONICAL_COLUMNS_MISSING:'+','.join(sorted(missing)))
    if {'code','date','money'} & set(source.columns):
        raise ValueError('AMBIGUOUS_TARGET_COLUMN_ALREADY_PRESENT')
    if pd.api.types.is_numeric_dtype(source['trade_date']):
        raise ValueError('ORDINAL_NOT_A_TRADE_DATE')
    dates=pd.to_datetime(source['trade_date'],errors='raise')
    if dates.isna().any() or dates.dt.tz is not None or not dates.eq(dates.dt.normalize()).all():
        raise ValueError('UNSUPPORTED_TRADE_DATE_AXIS')
    codes=source['canonical_code']
    if codes.isna().any() or not codes.map(lambda x:isinstance(x,str) and bool(x.strip())).all():
        raise ValueError('INVALID_CANONICAL_CODE')
    for field,value in [('price_variant','PRICE_INDEX'),('return_variant','PRICE'),('source_fq','NOT_APPLICABLE')]:
        if not source[field].eq(value).all():
            raise ValueError('UNSUPPORTED_PRICE_SEMANTICS:'+field)
    result=source.rename(columns={'canonical_code':'code','trade_date':'date','amount':'money'}).copy()
    result['date']=dates
    if result.duplicated(['date','code']).any():
        raise ValueError('DUPLICATE_CANONICAL_KEYS_REQUIRES_REVISION_CONTRACT')
    for field in ['open','high','low','close','pre_close','volume','money']:
        # Fail rather than coerce strings/errors to silently missing observations.
        if not pd.api.types.is_numeric_dtype(result[field]):
            raise ValueError('NONNUMERIC_PRICE_FIELD:'+field)
        vals=result[field].dropna().to_numpy(dtype=float)
        if not np.isfinite(vals).all():
            raise ValueError('NONFINITE_PRICE_FIELD:'+field)
    # Preserve null pre-inception rows and all provenance columns, without any fill.
    return result
